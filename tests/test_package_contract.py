from __future__ import annotations

import importlib.util
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
SKILL_ROOT = ROOT / "skills" / "audit-venue-submission"
SCRIPTS = SKILL_ROOT / "scripts"


def load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / filename)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


INTEGRITY = load("package_integrity", "package_integrity.py")


class PackageContractTests(unittest.TestCase):
    def test_release_identity_license_and_citation_are_synchronized(self) -> None:
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        package_version = json.loads(
            (SKILL_ROOT / "references" / "package-version.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(version, "0.2.0")
        self.assertEqual(package_version["skill_name"], "audit-venue-submission")
        self.assertEqual(package_version["version"], version)
        root_citation = (ROOT / "CITATION.cff").read_bytes()
        self.assertEqual(
            root_citation,
            (SKILL_ROOT / "CITATION.cff").read_bytes(),
        )
        self.assertIn(f'version: "{version}"'.encode(), root_citation)
        self.assertEqual(
            (ROOT / "LICENSE").read_bytes(),
            (SKILL_ROOT / "LICENSE").read_bytes(),
        )

    def test_package_manifest_verifies_and_detects_ordinary_drift(self) -> None:
        digest = INTEGRITY.verify_manifest(SKILL_ROOT)
        self.assertRegex(digest, r"^[0-9a-f]{64}$")
        with tempfile.TemporaryDirectory() as directory:
            copied = Path(directory) / "skill"
            shutil.copytree(SKILL_ROOT, copied)
            INTEGRITY.verify_manifest(copied)
            guide = copied / "references" / "general-guide.md"
            guide.write_text(
                guide.read_text(encoding="utf-8") + "\nchanged\n",
                encoding="utf-8",
            )
            with self.assertRaises(INTEGRITY.IntegrityError):
                INTEGRITY.verify_manifest(copied)

    def test_manifest_tolerates_only_github_frontmatter_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            copied = Path(directory) / "skill"
            shutil.copytree(SKILL_ROOT, copied)
            skill = copied / "SKILL.md"
            text = skill.read_text(encoding="utf-8")
            marker = "\n---\n"
            frontmatter, body = text.split(marker, 1)
            injected = (
                frontmatter
                + "\nmetadata:\n"
                + "  github-path: skills/audit-venue-submission\n"
                + "  github-ref: refs/tags/v0.2.0\n"
                + "  github-repo: "
                + "https://github.com/Ian-Tseng/audit-venue-submission\n"
                + "  github-tree-sha: "
                + ("a" * 40)
                + marker
                + body
            )
            skill.write_text(injected, encoding="utf-8")
            INTEGRITY.verify_manifest(copied)
            skill.write_text(
                injected.replace(
                    "license: MIT", "license: Proprietary", 1
                ),
                encoding="utf-8",
            )
            with self.assertRaises(INTEGRITY.IntegrityError):
                INTEGRITY.verify_manifest(copied)

    def test_manifest_excludes_caches_and_package_text_is_clean(self) -> None:
        paths = [path for path in SKILL_ROOT.rglob("*") if path.is_file()]
        manifest = json.loads(
            (
                SKILL_ROOT / "references" / "package-manifest.json"
            ).read_text(encoding="utf-8")
        )
        self.assertFalse(
            [
                entry["path"]
                for entry in manifest["files"]
                if "__pycache__" in Path(entry["path"]).parts
                or Path(entry["path"]).suffix.lower() in {".pyc", ".pyo"}
            ]
        )
        for path in paths:
            if path.suffix.lower() not in {
                ".cff",
                ".json",
                ".md",
                ".py",
                ".yaml",
            } and path.name != "LICENSE":
                continue
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("\ufffd", text, str(path))
            self.assertFalse(
                any(0xE000 <= ord(char) <= 0xF8FF for char in text),
                str(path),
            )

    def test_skill_links_and_first_party_source_log_are_current(self) -> None:
        skill_text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        for target in re.findall(r"\[[^]]+\]\(([^)]+)\)", skill_text):
            if "://" not in target:
                self.assertTrue((SKILL_ROOT / target).is_file(), target)
        guide = (
            SKILL_ROOT / "references" / "general-guide.md"
        ).read_text(encoding="utf-8")
        self.assertIn("2026-08-20 (Asia/Taipei)", guide)
        for url in (
            "https://www.nature.com/nature-portfolio/for-authors/write",
            "https://www.nature.com/nature/for-authors/initial-submission",
            "https://neurips.cc/Conferences/2026/CallForPapers",
            "https://neurips.cc/public/guides/PaperChecklist",
            "https://aaai.org/conference/aaai/aaai-26/reproducibility-checklist/",
        ):
            self.assertIn(url, guide)

    def test_every_packaged_cli_has_working_help(self) -> None:
        for filename in (
            "audit_submission.py",
            "audit_terminology.py",
            "audit_docx_text_parts.py",
            "package_integrity.py",
            "submission_intake.py",
            "update_policy.py",
            "skill_outcome.py",
        ):
            completed = subprocess.run(
                [sys.executable, str(SCRIPTS / filename), "--help"],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn("usage:", completed.stdout.lower())


if __name__ == "__main__":
    unittest.main()
