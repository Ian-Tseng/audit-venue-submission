#!/usr/bin/env python3
"""Audit canonical terminology across manuscript, display, and artifact scopes."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from audit_submission import inspect_docx, inspect_pdf, inspect_zip
from path_contract import (
    PathBoundaryError,
    portable_path,
    resolve_input,
    resolve_input_specs,
    resolve_output,
    resolve_root,
)
from terminology_contract import validate_contract


TEXT_SUFFIXES = {
    ".bib", ".csv", ".htm", ".html", ".json", ".md", ".py", ".rst",
    ".svg", ".tex", ".tsv", ".txt", ".xml", ".yaml", ".yml",
}


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def contains(text: str, phrase: str, case_sensitive: bool = False) -> bool:
    haystack = normalize(text)
    needle = normalize(phrase)
    if not case_sensitive:
        haystack = haystack.casefold()
        needle = needle.casefold()
    return needle in haystack


def read_surface(path: Path, max_text_bytes: int) -> tuple[str, str | None]:
    suffix = path.suffix.lower()
    try:
        if suffix == ".docx":
            _, text = inspect_docx(path)
            return text, None
        if suffix == ".pdf":
            details, text = inspect_pdf(path)
            return text, details.get("inspection_error")
        if suffix == ".zip":
            details, text = inspect_zip(path, max_text_bytes)
            return text, details.get("inspection_error")
        if suffix in TEXT_SUFFIXES:
            if path.stat().st_size > max_text_bytes:
                return "", f"file exceeds max_text_bytes ({path.stat().st_size})"
            return path.read_text(encoding="utf-8", errors="replace"), None
        return "", f"unsupported text surface: {suffix or '<none>'}"
    except Exception as exc:  # keep the full audit report available
        return "", f"{type(exc).__name__}: {exc}"


def resolve_specs(root: Path, specs: list[str]) -> tuple[list[Path], list[str]]:
    return resolve_input_specs(root, specs)


def slice_surface(text: str, start: str | None, end: str | None) -> tuple[str, list[str]]:
    errors: list[str] = []
    selected = text
    if start:
        position = selected.find(start)
        if position < 0:
            errors.append(f"start marker not found: {start}")
        else:
            selected = selected[position + len(start):]
    if end:
        position = selected.find(end)
        if position < 0:
            errors.append(f"end marker not found: {end}")
        else:
            selected = selected[:position]
    return selected, errors


def line_hits(
    path: str, text: str, phrase: str, case_sensitive: bool
) -> list[dict[str, Any]]:
    flags = 0 if case_sensitive else re.I
    pattern = re.compile(re.escape(phrase), flags)
    hits: list[dict[str, Any]] = []
    for number, line in enumerate(text.splitlines(), start=1):
        if pattern.search(line):
            hits.append({"path": path, "line": number, "text": line.strip()[:300]})
    return hits


def load_contract(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    return validate_contract(data)


def main() -> int:
    # Keep machine-readable reports portable on Windows consoles whose legacy
    # code page cannot represent mathematical or non-Latin manuscript text.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, help="Root used to resolve contract file specifications")
    parser.add_argument("--contract", required=True, help="Version-1 JSON terminology contract")
    parser.add_argument("--output", help="Optional JSON report path")
    parser.add_argument("--max-text-bytes", type=int, default=20_000_000)
    args = parser.parse_args()

    try:
        root = resolve_root(args.root)
        contract_path = resolve_input(root, args.contract, "contract")
    except PathBoundaryError as exc:
        print(f"Invalid root or terminology contract: {exc}", file=sys.stderr)
        return 2

    try:
        contract = load_contract(contract_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Invalid terminology contract: {exc}", file=sys.stderr)
        return 2

    terms = {item["id"]: item for item in contract["terms"]}
    findings: list[dict[str, Any]] = []
    scope_reports: list[dict[str, Any]] = []

    for scope in contract["scopes"]:
        name = scope.get("name", "unnamed-scope")
        try:
            files, missing_specs = resolve_specs(
                root, scope.get("files", [])
            )
        except PathBoundaryError as exc:
            print(
                f"Invalid file specification in scope {name}: {exc}",
                file=sys.stderr,
            )
            return 2
        scope_report: dict[str, Any] = {
            "name": name,
            "files": [portable_path(root, path) for path in files],
            "missing_specs": missing_specs,
            "required_terms": scope.get("require", []),
            "require_mode": scope.get("require_mode", "scope"),
        }
        for spec in missing_specs:
            findings.append({"type": "missing-file", "scope": name, "value": spec})

        surfaces: list[tuple[Path, str]] = []
        for path in files:
            display_path = portable_path(root, path)
            text, error = read_surface(path, args.max_text_bytes)
            if error:
                findings.append(
                    {
                        "type": "surface-error",
                        "scope": name,
                        "path": display_path,
                        "value": error,
                    }
                )
                continue
            selected, marker_errors = slice_surface(text, scope.get("start"), scope.get("end"))
            for error in marker_errors:
                findings.append(
                    {
                        "type": "marker-error",
                        "scope": name,
                        "path": display_path,
                        "value": error,
                    }
                )
            surfaces.append((path, selected))

        combined = "\n".join(text for _, text in surfaces)
        require_mode = scope.get("require_mode", "scope")
        for term_id in scope.get("require", []):
            term = terms.get(term_id)
            if term is None:
                findings.append({"type": "unknown-term-id", "scope": name, "value": term_id})
                continue
            targets = surfaces if require_mode == "each_file" else [(None, combined)]
            for target_path, target_text in targets:
                if contains(target_text, term["canonical"], term.get("case_sensitive", False)):
                    continue
                finding = {
                    "type": "missing-canonical-term",
                    "scope": name,
                    "term_id": term_id,
                    "value": term["canonical"],
                }
                if target_path is not None:
                    finding["path"] = portable_path(root, target_path)
                findings.append(finding)

        allowed = {normalize(value).casefold() for value in scope.get("allowed_variants", [])}
        scan_ids = scope.get("scan_terms", list(terms))
        for term_id in scan_ids:
            term = terms.get(term_id)
            if term is None:
                findings.append({"type": "unknown-term-id", "scope": name, "value": term_id})
                continue
            case_sensitive = term.get("case_sensitive", False)
            for variant in term.get("forbidden_variants", []):
                if normalize(variant).casefold() in allowed:
                    continue
                for path, selected in surfaces:
                    if contains(selected, variant, case_sensitive):
                        findings.append({
                            "type": "forbidden-variant",
                            "scope": name,
                            "term_id": term_id,
                            "value": variant,
                            "hits": line_hits(
                                portable_path(root, path),
                                selected,
                                variant,
                                case_sensitive,
                            ),
                        })

        for acronym in contract.get("acronyms", []):
            if name not in acronym.get("scopes", []):
                continue
            short = acronym["short"]
            long = acronym["long"]
            folded = normalize(combined).casefold()
            short_pos = folded.find(normalize(short).casefold())
            long_pos = folded.find(normalize(long).casefold())
            if short_pos >= 0 and (long_pos < 0 or long_pos > short_pos):
                findings.append({
                    "type": "acronym-before-definition",
                    "scope": name,
                    "value": f"{short} -> {long}",
                })

        scope_reports.append(scope_report)

    report = {
        "root": ".",
        "contract": portable_path(root, contract_path),
        "terms": len(terms),
        "scopes": scope_reports,
        "findings": findings,
        "passed": not findings,
        "notes": [
            "Image-only figures require a textual label source or transcript plus visual inspection.",
            "A terminology contract should preserve scientifically meaningful distinctions rather than ban every synonym.",
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
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
