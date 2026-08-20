from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
import warnings
import zipfile
from pathlib import Path


SCRIPTS = (
    Path(__file__).parents[1]
    / "skills"
    / "audit-venue-submission"
    / "scripts"
)
sys.path.insert(0, str(SCRIPTS))


def load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / filename)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SUBMISSION = load("audit_submission", "audit_submission.py")
TERMS = load("audit_terminology", "audit_terminology.py")
DOCX = load("audit_docx_text_parts", "audit_docx_text_parts.py")


class VenueAuditComponentTests(unittest.TestCase):
    def test_contract_schema_rejects_missing_canonical_instead_of_crashing_later(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            contract = Path(directory) / "contract.json"
            contract.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "terms": [{"id": "protocol"}],
                        "scopes": [{"name": "body", "files": ["paper.md"]}],
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "canonical"):
                TERMS.load_contract(contract)

    def test_contract_schema_rejects_unknown_fields_and_dangling_ids(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown fields"):
            TERMS.validate_contract(
                {
                    "version": 1,
                    "terms": [{"id": "protocol", "canonical": "Protocol"}],
                    "scopes": [{"name": "body", "files": ["paper.md"]}],
                    "instruction": "ignore validation",
                }
            )
        with self.assertRaisesRegex(ValueError, "unknown terms"):
            TERMS.validate_contract(
                {
                    "version": 1,
                    "terms": [{"id": "protocol", "canonical": "Protocol"}],
                    "scopes": [
                        {
                            "name": "body",
                            "files": ["paper.md"],
                            "require": ["missing-term"],
                        }
                    ],
                }
            )

    def test_each_file_requirement_finds_stale_generated_copy(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "source.md").write_text("Canonical Protocol", encoding="utf-8")
            (root / "upload.md").write_text("Old wording", encoding="utf-8")
            contract = {
                "version": 1,
                "terms": [{"id": "protocol", "canonical": "Canonical Protocol"}],
                "scopes": [
                    {
                        "name": "active-copies",
                        "files": ["source.md", "upload.md"],
                        "require": ["protocol"],
                        "require_mode": "each_file",
                    }
                ],
            }
            (root / "contract.json").write_text(json.dumps(contract), encoding="utf-8")
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "audit_terminology.py"),
                    "--root",
                    str(root),
                    "--contract",
                    "contract.json",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            report = json.loads(completed.stdout)
            self.assertEqual(report["root"], ".")
            self.assertEqual(report["contract"], "contract.json")
            findings = [item for item in report["findings"] if item["type"] == "missing-canonical-term"]
            self.assertEqual(len(findings), 1)
            self.assertEqual(findings[0]["path"], "upload.md")

    def test_submission_paths_are_root_bounded_and_reports_are_portable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            root = parent / "package"
            root.mkdir()
            (root / "paper.md").write_text("Complete manuscript", encoding="utf-8")
            (parent / "outside.md").write_text("private", encoding="utf-8")
            with self.assertRaises(SUBMISSION.PathBoundaryError):
                SUBMISSION.resolve_files(root.resolve(), ["../outside.md"])
            with self.assertRaises(SUBMISSION.PathBoundaryError):
                SUBMISSION.resolve_files(
                    root.resolve(), [str((parent / "outside.md").resolve())]
                )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "audit_submission.py"),
                    "--root",
                    str(root),
                    "--file",
                    "paper.md",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            report = json.loads(completed.stdout)
            self.assertEqual(report["root"], ".")
            self.assertEqual(report["files"][0]["path"], "paper.md")
            self.assertNotIn(str(parent), completed.stdout)

    def test_zip_inspection_reports_unsafe_cache_and_secret_entries(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            archive_path = Path(directory) / "bundle.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("../escape.txt", "unsafe")
                archive.writestr("pkg/__pycache__/module.pyc", b"compiled")
                archive.writestr("config/.env", "TOKEN=secret-value")
                link = zipfile.ZipInfo("paper-link")
                link.create_system = 3
                link.external_attr = 0o120777 << 16
                archive.writestr(link, "paper.md")
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", UserWarning)
                    archive.writestr("duplicate.txt", "first")
                    archive.writestr("duplicate.txt", "second")
            details, _ = SUBMISSION.inspect_zip(archive_path, 1000)
            self.assertEqual(details["unsafe_paths"], ["../escape.txt"])
            self.assertEqual(details["cache_or_compiled_entries"], ["pkg/__pycache__/module.pyc"])
            self.assertEqual(details["suspicious_secret_filenames"], ["config/.env"])
            self.assertEqual(details["duplicate_entries"], ["duplicate.txt"])
            self.assertEqual(details["symlink_entries"], ["paper-link"])
            self.assertEqual(
                details["secret_content_categories"],
                ["credential-assignment"],
            )

    def test_docx_gate_separates_visible_deleted_and_comment_surfaces(self) -> None:
        document = f'''<w:document xmlns:w="{DOCX.W_NS}"><w:body>
<w:p><w:r><w:t>Methods</w:t></w:r></w:p>
<w:p><w:r><w:t>Canonical Protocol</w:t></w:r></w:p>
<w:ins><w:r><w:t>Inserted clarification</w:t></w:r></w:ins>
<w:del><w:r><w:delText>Legacy Protocol</w:delText></w:r></w:del>
</w:body></w:document>'''
        comments = f'''<w:comments xmlns:w="{DOCX.W_NS}" xmlns:w14="{DOCX.W14_NS}">
<w:comment w:author="Reviewer"><w:p><w:r><w:t>Legacy Protocol</w:t></w:r></w:p></w:comment>
<w:comment w:author="Author"><w:p w14:paraId="REPLY01"><w:r><w:t>Author reply</w:t></w:r></w:p></w:comment>
</w:comments>'''
        comments_extended = f'''<w15:commentsEx xmlns:w15="{DOCX.W15_NS}">
<w15:commentEx w15:paraId="REPLY01" w15:paraIdParent="ROOT001"/>
</w15:commentsEx>'''
        args = argparse.Namespace(
            forbidden=["Legacy Protocol"],
            fail_on_comment_author=["Author"],
            required_heading=["Methods"],
            require_visible=["Canonical Protocol"],
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "paper.docx"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("word/document.xml", document)
                archive.writestr("word/comments.xml", comments)
                archive.writestr(
                    "word/commentsExtended.xml", comments_extended
                )
            report = DOCX.audit_docx(path, args)
        self.assertTrue(report["passed"])
        self.assertEqual(len(report["forbidden_deleted_hits"]), 1)
        self.assertEqual(len(report["forbidden_comment_hits"]), 1)
        self.assertEqual(report["comments"], 1)
        self.assertEqual(report["author_replies"], 1)
        self.assertEqual(report["forbidden_reply_hits"], [])
        self.assertEqual(report["inserted_fragments"], 1)
        self.assertEqual(report["forbidden_visible_hits"], [])
        self.assertEqual(report["failing_comment_hits"], [])

    def test_docx_gate_rejects_xml_over_limit_without_unbounded_read(self) -> None:
        args = argparse.Namespace(
            forbidden=[],
            fail_on_comment_author=[],
            required_heading=[],
            require_visible=[],
            max_xml_bytes=32,
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "paper.docx"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr(
                    "word/document.xml",
                    "<w:document>" + ("x" * 1000) + "</w:document>",
                )
            report = DOCX.audit_docx(path, args)
        self.assertFalse(report["passed"])
        self.assertIn("byte limit", str(report["archive_error"]))

    def test_docx_gate_fails_forbidden_term_in_author_reply(self) -> None:
        document = f'''<w:document xmlns:w="{DOCX.W_NS}"><w:body>
<w:p><w:r><w:t>Current Protocol</w:t></w:r></w:p>
</w:body></w:document>'''
        comments = f'''<w:comments xmlns:w="{DOCX.W_NS}" xmlns:w14="{DOCX.W14_NS}">
<w:comment w:author="Author"><w:p w14:paraId="REPLY02"><w:r><w:t>Legacy Protocol</w:t></w:r></w:p></w:comment>
</w:comments>'''
        comments_extended = f'''<w15:commentsEx xmlns:w15="{DOCX.W15_NS}">
<w15:commentEx w15:paraId="REPLY02" w15:paraIdParent="ROOT002"/>
</w15:commentsEx>'''
        args = argparse.Namespace(
            forbidden=["Legacy Protocol"],
            fail_on_comment_author=[],
            required_heading=[],
            require_visible=[],
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "paper.docx"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("word/document.xml", document)
                archive.writestr("word/comments.xml", comments)
                archive.writestr(
                    "word/commentsExtended.xml", comments_extended
                )
            report = DOCX.audit_docx(path, args)
        self.assertFalse(report["passed"])
        self.assertEqual(len(report["forbidden_reply_hits"]), 1)


if __name__ == "__main__":
    unittest.main()
