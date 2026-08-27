from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "audit-venue-submission" / "scripts" / "submission_intake.py"


def load_module():
    spec = importlib.util.spec_from_file_location("submission_intake", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def valid_intake() -> dict:
    return {
        "schema_version": 1,
        "authorization": {
            "authorized_to_process": True,
            "confidentiality_policy_checked": True,
            "venue_ai_policy_checked": True,
            "ai_assistance_permitted": True,
            "external_services_allowed": False,
            "human_accountable": True,
            "retention_decision": "project_controlled",
            "conflicts_status": "none",
        },
        "submission": {
            "venue": "venue-a",
            "year": "2027",
            "track": "main",
            "article_type": "research",
            "review_stage": "initial",
            "study_design": "randomized_trial",
            "official_sources_checked_at": "2026-08-27",
        },
        "guideline_coverage": [{
            "guideline_id": "consort",
            "applicability": "applicable",
            "evidence_locator": "check-table:consort",
            "human_verified": True,
        }],
    }


class SubmissionIntakeTests(unittest.TestCase):
    def test_confidential_intake_passes_without_echoing_submission_content(self) -> None:
        module = load_module()
        report = module.validate_intake(valid_intake())
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["candidate_guidelines"], ["consort"])
        self.assertEqual(report["coverage"], {"applicable": 1, "not_applicable": 0, "pending": 0})
        rendered = json.dumps(report)
        self.assertNotIn("venue-a", rendered)
        self.assertNotIn("check-table:consort", rendered)
        self.assertEqual(report["external_processing"], "not_performed")

    def test_intake_blocks_when_external_processing_or_ai_use_is_not_authorized(self) -> None:
        module = load_module()
        intake = valid_intake()
        intake["authorization"]["external_services_allowed"] = True
        intake["authorization"]["ai_assistance_permitted"] = False
        report = module.validate_intake(intake)
        self.assertEqual(report["status"], "BLOCKED")
        self.assertEqual([item["code"] for item in report["findings"]], [
            "AI_ASSISTANCE_NOT_PERMITTED",
            "EXTERNAL_PROCESSING_NOT_ALLOWED",
        ])

    def test_guideline_selection_is_non_scoring_and_requires_current_confirmation(self) -> None:
        module = load_module()
        result = module.select_guidelines("prediction_model")
        self.assertEqual(result["status"], "CANDIDATE_ONLY")
        self.assertEqual(result["guidelines"][0]["id"], "tripod")
        self.assertTrue(result["guidelines"][0]["official_url"].startswith("https://www.equator-network.org/"))
        self.assertFalse(result["compliance_scored"])
        self.assertTrue(result["requires_current_official_confirmation"])

    def test_cli_selects_guidelines_without_reading_a_manuscript(self) -> None:
        result = subprocess.run(
            [sys.executable, "-X", "utf8", str(SCRIPT), "guidelines", "--study-design", "systematic_review"],
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual([item["id"] for item in payload["guidelines"]], ["prisma"])
        self.assertEqual(payload["status"], "CANDIDATE_ONLY")

    def test_all_authorization_and_conflict_gates_block(self) -> None:
        module = load_module()
        cases = (
            ("authorized_to_process", False, "PROCESSING_NOT_AUTHORIZED"),
            ("confidentiality_policy_checked", False, "CONFIDENTIALITY_POLICY_UNCHECKED"),
            ("venue_ai_policy_checked", False, "VENUE_AI_POLICY_UNCHECKED"),
            ("ai_assistance_permitted", False, "AI_ASSISTANCE_NOT_PERMITTED"),
            ("external_services_allowed", True, "EXTERNAL_PROCESSING_NOT_ALLOWED"),
            ("human_accountable", False, "HUMAN_ACCOUNTABILITY_MISSING"),
            ("conflicts_status", "unresolved", "CONFLICTS_UNRESOLVED"),
        )
        for field, value, code in cases:
            with self.subTest(field=field):
                intake = valid_intake()
                intake["authorization"][field] = value
                report = module.validate_intake(intake)
                self.assertEqual(report["status"], "BLOCKED")
                self.assertIn(code, [item["code"] for item in report["findings"]])

    def test_partial_coverage_states_are_identifier_only(self) -> None:
        module = load_module()
        for name, mutate, expected_code in (
            ("pending", lambda value: value["guideline_coverage"][0].update({"applicability": "pending"}), "GUIDELINE_COVERAGE_PENDING"),
            ("unverified", lambda value: value["guideline_coverage"][0].update({"human_verified": False}), "GUIDELINE_COVERAGE_PENDING"),
            ("missing", lambda value: value.update({"guideline_coverage": []}), "CANDIDATE_GUIDELINE_UNASSESSED"),
        ):
            with self.subTest(name=name):
                intake = valid_intake()
                mutate(intake)
                report = module.validate_intake(intake)
                self.assertEqual(report["status"], "PARTIAL")
                self.assertIn(expected_code, [item["code"] for item in report["findings"]])
                self.assertNotIn("check-table:consort", json.dumps(report))

    def test_malformed_values_fail_closed_without_type_errors(self) -> None:
        module = load_module()
        cases = (
            lambda value: value["authorization"].update({"retention_decision": []}),
            lambda value: value["authorization"].update({"conflicts_status": {}}),
            lambda value: value["submission"].update({"study_design": []}),
            lambda value: value["submission"].update({"official_sources_checked_at": "2026-99-99"}),
            lambda value: value["submission"].update({"official_sources_checked_at": "9999-12-31"}),
            lambda value: value["guideline_coverage"][0].update({"guideline_id": "Not stable"}),
            lambda value: value["guideline_coverage"][0].update({"applicability": []}),
            lambda value: value["guideline_coverage"].append(dict(value["guideline_coverage"][0])),
        )
        for mutate in cases:
            with self.subTest(case=repr(mutate)):
                intake = valid_intake()
                mutate(intake)
                with self.assertRaises(module.IntakeError):
                    module.validate_intake(intake)

    def test_selector_covers_multi_guideline_and_unsupported_designs(self) -> None:
        module = load_module()
        result = module.select_guidelines("qualitative_study")
        self.assertEqual([item["id"] for item in result["guidelines"]], ["srqr", "coreq"])
        for value in ("unknown", []):
            with self.subTest(value=value):
                with self.assertRaises(module.IntakeError):
                    module.select_guidelines(value)

    def test_cli_validate_pass_partial_blocked_and_invalid_outcomes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cases = []
            cases.append(("pass", valid_intake(), 0, "PASS"))
            partial = valid_intake()
            partial["guideline_coverage"] = []
            cases.append(("partial", partial, 0, "PARTIAL"))
            blocked = valid_intake()
            blocked["authorization"]["authorized_to_process"] = False
            cases.append(("blocked", blocked, 3, "BLOCKED"))
            invalid = valid_intake()
            invalid["submission"]["official_sources_checked_at"] = "not-a-date"
            cases.append(("invalid", invalid, 2, "INVALID"))
            for name, intake, returncode, status in cases:
                with self.subTest(name=name):
                    path = root / f"{name}.json"
                    path.write_text(json.dumps(intake), encoding="utf-8")
                    result = subprocess.run(
                        [sys.executable, "-X", "utf8", str(SCRIPT), "validate", "--intake", str(path)],
                        cwd=ROOT,
                        text=True,
                        encoding="utf-8",
                        capture_output=True,
                        check=False,
                    )
                    self.assertEqual(result.returncode, returncode, result.stderr)
                    stream = result.stdout if returncode in {0, 3} else result.stderr
                    self.assertEqual(json.loads(stream)["status"], status)

    def test_file_boundary_rejects_links_malformed_and_oversized_inputs(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            malformed = root / "malformed.json"
            malformed.write_bytes(b"{")
            invalid_utf8 = root / "invalid-utf8.json"
            invalid_utf8.write_bytes(b"\xff")
            oversized = root / "oversized.json"
            oversized.write_bytes(b"x" * (module.MAX_BYTES + 1))
            for path in (malformed, invalid_utf8, oversized, root):
                with self.subTest(path=path.name):
                    with self.assertRaises(module.IntakeError):
                        module.load_intake(path)

    def test_file_boundary_rejects_an_actual_symlink_before_target_stat(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "target.json"
            target.write_text(json.dumps(valid_intake()), encoding="utf-8")
            linked = root / "linked.json"
            try:
                linked.symlink_to(target)
            except OSError as exc:
                self.skipTest(f"symlink creation unavailable: {exc}")
            self.assertTrue(module._is_link_like(linked))
            original_stat = Path.stat

            def reject_follow(path: Path, *args, **kwargs):
                if kwargs.get("follow_symlinks") is False:
                    return original_stat(path, *args, **kwargs)
                raise AssertionError("target followed")

            with mock.patch.object(Path, "stat", reject_follow):
                with self.assertRaises(module.IntakeError):
                    module.load_intake(linked)

    def test_link_detector_recognizes_windows_reparse_attribute(self) -> None:
        module = load_module()
        reparse = getattr(module.stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
        candidate = Path("reparse-intake.json")
        with mock.patch.object(Path, "lstat", return_value=SimpleNamespace(st_file_attributes=reparse)), mock.patch.object(Path, "is_symlink", return_value=False):
            self.assertTrue(module._is_link_like(candidate))

    def test_skill_routes_confidential_gate_before_audit_work(self) -> None:
        skill = (ROOT / "skills" / "audit-venue-submission" / "SKILL.md").read_text(encoding="utf-8")
        gate = skill.index("## Confirm confidential intake before reading unpublished content")
        audit = skill.index("## Refresh official sources on every refinement")
        self.assertLess(gate, audit)
        self.assertIn("submission_intake.py", skill[gate:audit])
        self.assertIn("never scores reporting compliance", skill[gate:audit])


if __name__ == "__main__":
    unittest.main()
