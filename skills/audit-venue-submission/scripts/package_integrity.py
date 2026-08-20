#!/usr/bin/env python3
"""Build or verify the installed skill package manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import stat
import sys
from pathlib import Path
from typing import Iterator


SKILL_NAME = "audit-venue-submission"
MANIFEST_RELATIVE_PATH = "references/package-manifest.json"
GITHUB_METADATA_PATTERN = re.compile(r"^github-[a-z0-9-]+$")
IGNORED_PARTS = {"__pycache__"}
IGNORED_NAMES = {".DS_Store", "Thumbs.db"}
TEXT_NAMES = {"LICENSE"}
TEXT_SUFFIXES = {".cff", ".json", ".md", ".py", ".yaml", ".yml"}


class IntegrityError(ValueError):
    pass


def normalized_skill_bytes(skill_path: Path) -> bytes:
    try:
        text = skill_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise IntegrityError("SKILL.md is not readable UTF-8") from exc
    keep_ending = text.endswith(("\n", "\r"))
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise IntegrityError("SKILL.md frontmatter is missing")
    try:
        frontmatter_end = next(
            index
            for index, line in enumerate(lines[1:], 1)
            if line.strip() == "---"
        )
    except StopIteration as exc:
        raise IntegrityError("SKILL.md frontmatter is not closed") from exc

    frontmatter = lines[1:frontmatter_end]
    blocks: list[tuple[str | None, list[str]]] = []
    index = 0
    while index < len(frontmatter):
        line = frontmatter[index]
        if not line.strip():
            index += 1
            continue
        if line[:1].isspace():
            raise IntegrityError("SKILL.md frontmatter contains an orphaned value")
        key_match = re.match(r"^([A-Za-z0-9_-]+)\s*:", line)
        key = key_match.group(1) if key_match else None
        block = [line]
        index += 1
        while index < len(frontmatter):
            child = frontmatter[index]
            if child.strip() and not child[:1].isspace():
                break
            block.append(child)
            index += 1

        if key == "metadata":
            filtered: list[str] = []
            for child in block[1:]:
                child_match = re.match(r"^\s+([A-Za-z0-9-]+):", child)
                if (
                    child_match
                    and GITHUB_METADATA_PATTERN.fullmatch(child_match.group(1))
                ):
                    continue
                filtered.append(child)
            block = [line, *filtered]
            if not any(item.strip() for item in filtered):
                continue
        elif key and GITHUB_METADATA_PATTERN.fullmatch(key):
            continue
        blocks.append((key, block))

    priority = {"name": 0, "description": 1}
    ordered = sorted(
        enumerate(blocks),
        key=lambda item: (priority.get(item[1][0] or "", 2), item[0]),
    )
    normalized = [line for _, (_, block) in ordered for line in block]
    while normalized and not normalized[-1].strip():
        normalized.pop()
    body = lines[frontmatter_end + 1 :]
    while body and not body[0].strip():
        body.pop(0)
    rebuilt = ["---", *normalized, "---"]
    if body:
        rebuilt.extend(["", *body])
    result = "\n".join(rebuilt)
    if keep_ending:
        result += "\n"
    return result.encode("utf-8")


def _is_link_like(path: Path) -> bool:
    try:
        attributes = getattr(path.lstat(), "st_file_attributes", 0)
    except OSError:
        return False
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    return path.is_symlink() or bool(reparse_flag and attributes & reparse_flag)


def _reject_links(skill_root: Path) -> None:
    for candidate in skill_root.resolve().rglob("*"):
        if _is_link_like(candidate):
            raise IntegrityError(
                "package contains a symbolic link or reparse point"
            )


def _iter_files(skill_root: Path) -> Iterator[tuple[str, Path]]:
    root = skill_root.resolve()
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
        if not path.is_file() or path.is_symlink():
            continue
        relative_path = path.relative_to(root)
        relative = relative_path.as_posix()
        if relative == MANIFEST_RELATIVE_PATH:
            continue
        if any(part in IGNORED_PARTS for part in relative_path.parts):
            continue
        if path.name in IGNORED_NAMES or path.suffix.lower() in {".pyc", ".pyo"}:
            continue
        yield relative, path


def canonical_bytes(relative: str, path: Path) -> bytes:
    if relative == "SKILL.md":
        return normalized_skill_bytes(path)
    if path.name in TEXT_NAMES or path.suffix.lower() in TEXT_SUFFIXES:
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise IntegrityError(f"{relative} is not readable UTF-8") from exc
        return ("\n".join(text.splitlines()) + ("\n" if text else "")).encode(
            "utf-8"
        )
    return path.read_bytes()


def file_digest(relative: str, path: Path) -> str:
    return hashlib.sha256(canonical_bytes(relative, path)).hexdigest()


def build_manifest(skill_root: Path) -> dict[str, object]:
    _reject_links(skill_root)
    return {
        "schema_version": 1,
        "skill_name": SKILL_NAME,
        "algorithm": "sha256",
        "skill_normalization": "canonical-frontmatter-v1-without-github-metadata",
        "files": [
            {"path": relative, "sha256": file_digest(relative, path)}
            for relative, path in _iter_files(skill_root)
        ],
    }


def manifest_digest(manifest: dict[str, object]) -> str:
    payload = json.dumps(
        manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def verify_manifest(skill_root: Path) -> str:
    _reject_links(skill_root)
    manifest_path = skill_root / MANIFEST_RELATIVE_PATH
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise IntegrityError("package manifest is missing or invalid JSON") from exc
    expected = build_manifest(skill_root)
    if manifest != expected:
        raise IntegrityError("package files do not match package manifest")
    return manifest_digest(manifest)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skill-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    build = subparsers.add_parser("build")
    build.add_argument("--write", action="store_true")
    subparsers.add_parser("verify")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    skill_root = args.skill_root.resolve()
    try:
        if args.command == "build":
            manifest = build_manifest(skill_root)
            rendered = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
            if args.write:
                path = skill_root / MANIFEST_RELATIVE_PATH
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(rendered, encoding="utf-8", newline="\n")
            print(
                json.dumps(
                    {
                        "status": "MANIFEST_WRITTEN"
                        if args.write
                        else "MANIFEST_BUILT",
                        "digest_sha256": manifest_digest(manifest),
                        "files": len(manifest["files"]),
                    },
                    sort_keys=True,
                )
            )
            return 0
        digest = verify_manifest(skill_root)
        print(
            json.dumps(
                {"status": "PACKAGE_VERIFIED", "digest_sha256": digest},
                sort_keys=True,
            )
        )
        return 0
    except IntegrityError as exc:
        print(
            json.dumps(
                {"status": "PACKAGE_INVALID", "message": str(exc)},
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
