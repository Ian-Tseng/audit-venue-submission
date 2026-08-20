#!/usr/bin/env python3
"""Collect deterministic preflight evidence for selected submission artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

from path_contract import (
    PathBoundaryError,
    portable_path,
    resolve_input_specs,
    resolve_output,
    resolve_root,
)

TEXT_SUFFIXES = {
    ".bib", ".csv", ".htm", ".html", ".json", ".md", ".rst",
    ".tex", ".tsv", ".txt", ".xml", ".yaml", ".yml",
}
MAX_ARCHIVE_ENTRIES = 10_000
DEFAULT_MAX_DOCX_XML_BYTES = 50_000_000
SECRET_CONTENT_PATTERNS = {
    "github-token": re.compile(r"\b(?:ghp_|github_pat_)[A-Za-z0-9_]{20,}"),
    "aws-access-key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "private-key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "credential-assignment": re.compile(
        r"\b(?:api[_-]?key|password|secret|token)\s*[:=]\s*[^\s]{8,}",
        re.I,
    ),
}
SECRET_FILENAME_PATTERN = re.compile(
    r"(^|/)(\.env|id_rsa|credentials?|secrets?)(\.|/|$)",
    re.I,
)
PLACEHOLDER_PATTERNS = {
    "TODO": re.compile(r"\bTODO\b", re.I),
    "TBD": re.compile(r"\bTBD\b", re.I),
    "FIXME": re.compile(r"\bFIXME\b", re.I),
    "placeholder-field": re.compile(
        r"\[(?:details|path|value|name|email|affiliation|date|hash)\]", re.I
    ),
    "not-yet-provided": re.compile(r"\bnot yet provided\b", re.I),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def xml_text(data: bytes) -> str:
    try:
        root = ET.fromstring(data)
    except ET.ParseError:
        return data.decode("utf-8", errors="replace")
    return " ".join(text.strip() for text in root.itertext() if text.strip())


def inspect_docx(
    path: Path, max_xml_bytes: int = DEFAULT_MAX_DOCX_XML_BYTES
) -> tuple[dict[str, Any], str]:
    result: dict[str, Any] = {"kind": "docx"}
    chunks: list[str] = []
    try:
        with zipfile.ZipFile(path) as archive:
            infos = archive.infolist()
            if len(infos) > MAX_ARCHIVE_ENTRIES:
                result["inspection_error"] = "archive entry limit exceeded"
                return result, ""
            selected = [
                info
                for info in infos
                if (
                    info.filename.startswith("word/")
                    and info.filename.endswith(".xml")
                )
                or info.filename == "docProps/core.xml"
            ]
            total_xml_bytes = sum(info.file_size for info in selected)
            if total_xml_bytes > max_xml_bytes:
                result["inspection_error"] = "DOCX XML byte limit exceeded"
                return result, ""
            raw_by_name: dict[str, bytes] = {}
            for info in sorted(selected, key=lambda item: item.filename):
                raw = archive.read(info)
                raw_by_name[info.filename] = raw
                text = xml_text(raw)
                if info.filename.startswith("word/"):
                    chunks.append(text)
                elif info.filename == "docProps/core.xml":
                    result["core_properties_text"] = text
                    chunks.append(text)
            if "word/document.xml" in raw_by_name:
                raw = raw_by_name["word/document.xml"]
                try:
                    root = ET.fromstring(raw)
                    ns = {
                        "w": (
                            "http://schemas.openxmlformats.org/"
                            "wordprocessingml/2006/main"
                        )
                    }
                    sizes = []
                    for node in root.findall(".//w:sectPr/w:pgSz", ns):
                        width = node.get(f"{{{ns['w']}}}w")
                        height = node.get(f"{{{ns['w']}}}h")
                        if width and height:
                            sizes.append(
                                {
                                    "width_mm": round(
                                        int(width) * 25.4 / 1440, 2
                                    ),
                                    "height_mm": round(
                                        int(height) * 25.4 / 1440, 2
                                    ),
                                }
                            )
                    result["page_sizes"] = sizes
                except (ET.ParseError, ValueError):
                    result["page_sizes"] = []
    except (OSError, RuntimeError, zipfile.BadZipFile) as exc:
        result["inspection_error"] = f"{type(exc).__name__}: {exc}"
        return result, ""
    return result, "\n".join(chunks)


def inspect_pdf(path: Path) -> tuple[dict[str, Any], str]:
    result: dict[str, Any] = {"kind": "pdf"}
    try:
        from pypdf import PdfReader  # type: ignore
    except ImportError:
        result["inspection_error"] = "pypdf is not installed"
        return result, ""
    try:
        reader = PdfReader(str(path))
        result["encrypted"] = bool(reader.is_encrypted)
        if reader.is_encrypted:
            return result, ""
        result["pages"] = len(reader.pages)
        result["metadata"] = {str(k): str(v) for k, v in (reader.metadata or {}).items()}
        sizes = []
        chunks = []
        for page in reader.pages:
            width = float(page.mediabox.width) * 25.4 / 72
            height = float(page.mediabox.height) * 25.4 / 72
            size = {"width_mm": round(width, 2), "height_mm": round(height, 2)}
            if size not in sizes:
                sizes.append(size)
            chunks.append(page.extract_text() or "")
        result["page_sizes"] = sizes
        return result, "\n".join(chunks)
    except Exception as exc:  # keep preflight running across corrupt files
        result["inspection_error"] = f"{type(exc).__name__}: {exc}"
        return result, ""


def unsafe_zip_name(name: str) -> bool:
    normalized = name.replace("\\", "/")
    parts = [part for part in normalized.split("/") if part]
    return (
        normalized.startswith("/")
        or bool(re.match(r"^[A-Za-z]:", normalized))
        or ".." in parts
    )


def zip_member_is_symlink(info: zipfile.ZipInfo) -> bool:
    unix_mode = (info.external_attr >> 16) & 0o170000
    return unix_mode == 0o120000


def inspect_zip(path: Path, max_text_bytes: int) -> tuple[dict[str, Any], str]:
    result: dict[str, Any] = {"kind": "zip"}
    scan_text: list[str] = []
    try:
        with zipfile.ZipFile(path) as archive:
            infos = archive.infolist()
            names = [info.filename for info in infos]
            if len(infos) > MAX_ARCHIVE_ENTRIES:
                result["inspection_error"] = "archive entry limit exceeded"
                return result, ""
            scan_text.extend(names)
            result["entries"] = len(names)
            result["file_entries"] = sum(not info.is_dir() for info in infos)
            result["directory_entries"] = sum(info.is_dir() for info in infos)
            counts: dict[str, int] = {}
            for name in names:
                counts[name] = counts.get(name, 0) + 1
            result["duplicate_entries"] = sorted(
                name for name, count in counts.items() if count > 1
            )
            result["symlink_entries"] = [
                info.filename for info in infos if zip_member_is_symlink(info)
            ]
            result["unsafe_paths"] = [name for name in names if unsafe_zip_name(name)]
            result["cache_or_compiled_entries"] = [
                name for name in names
                if "__pycache__" in name.replace("\\", "/").split("/")
                or name.lower().endswith((".pyc", ".pyo"))
            ]
            result["suspicious_secret_filenames"] = [
                name for name in names
                if SECRET_FILENAME_PATTERN.search(name)
            ]
            text_entries = 0
            text_bytes = 0
            oversized_text_entries: list[str] = []
            secret_categories: set[str] = set()
            for info in infos:
                if info.is_dir() or (
                    Path(info.filename).suffix.lower() not in TEXT_SUFFIXES
                    and not SECRET_FILENAME_PATTERN.search(info.filename)
                ):
                    continue
                if (
                    info.file_size > max_text_bytes
                    or text_bytes + info.file_size > max_text_bytes
                ):
                    oversized_text_entries.append(info.filename)
                    continue
                raw = archive.read(info)
                decoded = raw.decode("utf-8", errors="replace")
                scan_text.append(decoded)
                for label, pattern in SECRET_CONTENT_PATTERNS.items():
                    if pattern.search(decoded):
                        secret_categories.add(label)
                text_entries += 1
                text_bytes += len(raw)
            result["text_entries_scanned"] = text_entries
            result["text_bytes_scanned"] = text_bytes
            result["oversized_text_entries"] = oversized_text_entries
            result["secret_content_categories"] = sorted(secret_categories)
    except (OSError, zipfile.BadZipFile) as exc:
        result["inspection_error"] = f"{type(exc).__name__}: {exc}"
    return result, "\n".join(scan_text)


def read_text(path: Path, max_bytes: int) -> str:
    if path.stat().st_size > max_bytes:
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def scan_terms(text: str, terms: list[str]) -> list[str]:
    lowered = text.casefold()
    return [term for term in terms if term.casefold() in lowered]


def resolve_files(root: Path, specs: list[str]) -> tuple[list[Path], list[str]]:
    return resolve_input_specs(root, specs)


def inspect_file(path: Path, root: Path, args: argparse.Namespace) -> dict[str, Any]:
    record: dict[str, Any] = {
        "path": portable_path(root, path),
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
    }
    suffix = path.suffix.lower()
    text = ""
    if suffix == ".pdf":
        details, text = inspect_pdf(path)
    elif suffix == ".docx":
        details, text = inspect_docx(path, args.max_docx_xml_bytes)
    elif suffix == ".zip":
        details, text = inspect_zip(path, args.max_text_bytes)
    elif suffix in TEXT_SUFFIXES:
        details = {"kind": "text"}
        text = read_text(path, args.max_text_bytes)
    else:
        details = {"kind": "binary-or-unsupported"}
    record.update(details)
    scan_surface = f"{path.name}\n{text}\n{json.dumps(details, ensure_ascii=False)}"
    record["identity_hits"] = scan_terms(scan_surface, args.identity)
    record["stale_term_hits"] = scan_terms(scan_surface, args.stale_term)
    record["placeholder_hits"] = [
        label for label, pattern in PLACEHOLDER_PATTERNS.items() if pattern.search(text)
    ]
    return record


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, help="Submission package root")
    parser.add_argument("--file", action="append", default=[], help="Relative file or glob; repeat")
    parser.add_argument("--identity", action="append", default=[], help="Identity term; repeat")
    parser.add_argument("--stale-term", action="append", default=[], help="Old venue/internal term; repeat")
    parser.add_argument("--output", help="Optional JSON report path")
    parser.add_argument("--max-text-bytes", type=int, default=10_000_000)
    parser.add_argument(
        "--max-docx-xml-bytes",
        type=int,
        default=DEFAULT_MAX_DOCX_XML_BYTES,
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        root = resolve_root(args.root)
    except PathBoundaryError as exc:
        print(f"Invalid root: {exc}", file=sys.stderr)
        return 2
    if not args.file:
        print("At least one --file is required; audit only selected active artifacts.", file=sys.stderr)
        return 2
    try:
        files, missing = resolve_files(root, args.file)
    except PathBoundaryError as exc:
        print(f"Invalid selected file: {exc}", file=sys.stderr)
        return 2
    report = {
        "root": ".",
        "selected_files": len(files),
        "missing_specs": missing,
        "files": [inspect_file(path, root, args) for path in files],
        "notes": [
            "This report does not verify current venue rules or replace page-by-page visual inspection.",
            "A term hit requires contextual review; archived or intentional wording may be harmless.",
        ],
    }
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        try:
            output = resolve_output(root, args.output)
        except PathBoundaryError as exc:
            print(f"Invalid output: {exc}", file=sys.stderr)
            return 2
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
