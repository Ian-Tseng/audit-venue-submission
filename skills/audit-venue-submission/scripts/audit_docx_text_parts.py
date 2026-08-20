from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import unicodedata
import zipfile
from xml.etree import ElementTree as ET

from path_contract import (
    PathBoundaryError,
    portable_path,
    resolve_input_specs,
    resolve_output,
    resolve_root,
)

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
M_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"
W14_NS = "http://schemas.microsoft.com/office/word/2010/wordml"
W15_NS = "http://schemas.microsoft.com/office/word/2012/wordml"
W = f"{{{W_NS}}}"
M = f"{{{M_NS}}}"
W14 = f"{{{W14_NS}}}"
W15 = f"{{{W15_NS}}}"
VISIBLE_PART = re.compile(
    r"^word/(?:document|header\d+|footer\d+|footnotes|endnotes)\.xml$"
)
MAX_ARCHIVE_ENTRIES = 10_000
DEFAULT_MAX_XML_BYTES = 50_000_000


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\u00ad", "").replace("\u00a0", " ")
    return " ".join(text.split())


def node_text(node: ET.Element, include_deleted: bool = False) -> str:
    if node.tag == f"{W}del" and not include_deleted:
        return ""
    if node.tag in {f"{W}t", f"{W}delText", f"{M}t"}:
        return node.text or ""
    if node.tag == f"{W}tab":
        return "\t"
    if node.tag in {f"{W}br", f"{W}cr"}:
        return "\n"
    return "".join(node_text(child, include_deleted) for child in node)


def paragraphs(root: ET.Element, include_deleted: bool = False) -> list[str]:
    result: list[str] = []
    for paragraph in root.iter(f"{W}p"):
        text = normalize(node_text(paragraph, include_deleted))
        if text:
            result.append(text)
    return result


def phrase_hits(
    items: list[dict[str, object]], phrases: list[str]
) -> list[dict[str, object]]:
    hits: list[dict[str, object]] = []
    normalized = [(phrase, normalize(phrase).casefold()) for phrase in phrases]
    for item in items:
        folded = str(item["text"]).casefold()
        for original, phrase in normalized:
            if phrase and phrase in folded:
                hits.append({**item, "phrase": original})
    return hits


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def audit_docx(
    path: Path,
    args: argparse.Namespace,
    display_path: str | None = None,
) -> dict[str, object]:
    visible: list[dict[str, object]] = []
    comments: list[dict[str, object]] = []
    replies: list[dict[str, object]] = []
    deleted: list[dict[str, object]] = []
    inserted: list[dict[str, object]] = []
    archive_error: str | None = None
    corrupt_member: str | None = None

    try:
        with zipfile.ZipFile(path) as archive:
            infos = archive.infolist()
            if len(infos) > MAX_ARCHIVE_ENTRIES:
                raise ValueError("archive entry limit exceeded")
            selected = [
                info
                for info in infos
                if VISIBLE_PART.match(info.filename)
                or info.filename
                in {"word/comments.xml", "word/commentsExtended.xml"}
            ]
            max_xml_bytes = getattr(
                args, "max_xml_bytes", DEFAULT_MAX_XML_BYTES
            )
            if sum(info.file_size for info in selected) > max_xml_bytes:
                raise ValueError("DOCX XML byte limit exceeded")
            raw_by_name: dict[str, bytes] = {}
            for info in selected:
                try:
                    raw_by_name[info.filename] = archive.read(info)
                except zipfile.BadZipFile:
                    corrupt_member = info.filename
                    raise
            reply_paragraph_ids: set[str] = set()
            extended = raw_by_name.get("word/commentsExtended.xml")
            if extended is not None:
                extended_root = ET.fromstring(extended)
                for item in extended_root.iter(f"{W15}commentEx"):
                    para_id = item.attrib.get(f"{W15}paraId")
                    parent_id = item.attrib.get(f"{W15}paraIdParent")
                    if para_id and parent_id:
                        reply_paragraph_ids.add(para_id)

            for member, raw in raw_by_name.items():
                if member == "word/commentsExtended.xml":
                    continue
                root = ET.fromstring(raw)
                if member == "word/comments.xml":
                    for comment in root.iter(f"{W}comment"):
                        author = comment.attrib.get(f"{W}author", "")
                        for index, paragraph in enumerate(
                            comment.iter(f"{W}p")
                        ):
                            text = normalize(node_text(paragraph))
                            if not text:
                                continue
                            para_id = paragraph.attrib.get(f"{W14}paraId", "")
                            target = (
                                replies
                                if para_id in reply_paragraph_ids
                                else comments
                            )
                            target.append(
                                {
                                    "part": member,
                                    "index": index,
                                    "author": author,
                                    "text": text,
                                }
                            )
                    continue
                for index, text in enumerate(paragraphs(root)):
                    visible.append(
                        {"part": member, "index": index, "text": text}
                    )
                for insertion in root.iter(f"{W}ins"):
                    text = normalize(node_text(insertion))
                    if text:
                        inserted.append({"part": member, "text": text})
                for deletion in root.iter(f"{W}del"):
                    text = normalize(
                        node_text(deletion, include_deleted=True)
                    )
                    if text:
                        deleted.append({"part": member, "text": text})
    except (
        ET.ParseError,
        OSError,
        RuntimeError,
        ValueError,
        zipfile.BadZipFile,
    ) as exc:
        archive_error = f"{type(exc).__name__}: {exc}"

    visible_text = "\n".join(str(item["text"]) for item in visible)
    visible_paragraphs = {str(item["text"]) for item in visible}
    forbidden_visible = phrase_hits(visible, args.forbidden)
    forbidden_comments = phrase_hits(comments, args.forbidden)
    forbidden_replies = phrase_hits(replies, args.forbidden)
    forbidden_deleted = phrase_hits(deleted, args.forbidden)
    forbidden_inserted = phrase_hits(inserted, args.forbidden)
    failed_comment_authors = {
        author.casefold() for author in args.fail_on_comment_author
    }
    failing_comment_hits = [
        item
        for item in [*forbidden_comments, *forbidden_replies]
        if str(item.get("author", "")).casefold() in failed_comment_authors
    ]
    missing_headings = [
        heading
        for heading in args.required_heading
        if normalize(heading) not in visible_paragraphs
    ]
    folded_visible = normalize(visible_text).casefold()
    missing_visible = [
        phrase
        for phrase in args.require_visible
        if normalize(phrase).casefold() not in folded_visible
    ]
    passed = not (
        archive_error
        or corrupt_member
        or forbidden_visible
        or forbidden_replies
        or failing_comment_hits
        or missing_headings
        or missing_visible
    )
    return {
        "path": display_path or path.name,
        "bytes": path.stat().st_size,
        "sha256": file_sha256(path),
        "visible_text_sha256": hashlib.sha256(
            visible_text.encode("utf-8")
        ).hexdigest(),
        "visible_paragraphs": len(visible),
        "comments": len(comments),
        "author_replies": len(replies),
        "inserted_fragments": len(inserted),
        "deleted_fragments": len(deleted),
        "archive_error": archive_error,
        "corrupt_member": corrupt_member,
        "forbidden_visible_hits": forbidden_visible,
        "forbidden_comment_hits": forbidden_comments,
        "forbidden_reply_hits": forbidden_replies,
        "forbidden_deleted_hits": forbidden_deleted,
        "forbidden_inserted_hits": forbidden_inserted,
        "failing_comment_hits": failing_comment_hits,
        "missing_required_headings": missing_headings,
        "missing_required_visible_phrases": missing_visible,
        "passed": passed,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run-aware DOCX word/paragraph audit across visible and review parts."
    )
    parser.add_argument("--root", default=".")
    parser.add_argument("--docx", action="append", required=True)
    parser.add_argument("--forbidden", action="append", default=[])
    parser.add_argument("--required-heading", action="append", default=[])
    parser.add_argument("--require-visible", action="append", default=[])
    parser.add_argument("--fail-on-comment-author", action="append", default=[])
    parser.add_argument("--output")
    parser.add_argument(
        "--max-xml-bytes",
        type=int,
        default=DEFAULT_MAX_XML_BYTES,
    )
    args = parser.parse_args()

    try:
        root = resolve_root(args.root)
        paths, missing = resolve_input_specs(root, args.docx)
    except PathBoundaryError as exc:
        print(f"Invalid DOCX input: {exc}")
        return 2
    if missing:
        print(
            json.dumps(
                {"status": "MISSING_DOCX", "missing_specs": missing},
                sort_keys=True,
            )
        )
        return 2
    if any(path.suffix.lower() != ".docx" for path in paths):
        print("Every --docx input must have a .docx suffix")
        return 2
    reports = [
        audit_docx(path, args, portable_path(root, path)) for path in paths
    ]
    result = {
        "files": reports,
        "passed": all(report["passed"] for report in reports),
    }
    rendered = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        try:
            output = resolve_output(root, args.output)
        except PathBoundaryError as exc:
            print(f"Invalid output: {exc}")
            return 2
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
