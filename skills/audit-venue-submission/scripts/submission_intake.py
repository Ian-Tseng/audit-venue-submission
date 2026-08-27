#!/usr/bin/env python3
"""Validate confidential audit intake and select non-scoring reporting-guideline candidates."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import stat
import sys
from datetime import date
from pathlib import Path
from typing import Any


MAX_BYTES = 128 * 1024
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
IDENTIFIER = re.compile(r"^[a-z][a-z0-9-]{0,63}$")
ROOT_KEYS = {"schema_version", "authorization", "submission", "guideline_coverage"}
AUTH_KEYS = {
    "authorized_to_process",
    "confidentiality_policy_checked",
    "venue_ai_policy_checked",
    "ai_assistance_permitted",
    "external_services_allowed",
    "human_accountable",
    "retention_decision",
    "conflicts_status",
}
SUBMISSION_KEYS = {
    "venue",
    "year",
    "track",
    "article_type",
    "review_stage",
    "study_design",
    "official_sources_checked_at",
}
COVERAGE_KEYS = {"guideline_id", "applicability", "evidence_locator", "human_verified"}
EQUATOR = "https://www.equator-network.org/reporting-guidelines"
GUIDELINES: dict[str, list[dict[str, str]]] = {
    "randomized_trial": [{"id": "consort", "name": "CONSORT", "official_url": f"{EQUATOR}/consort/"}],
    "observational_study": [{"id": "strobe", "name": "STROBE", "official_url": f"{EQUATOR}/strobe/"}],
    "systematic_review": [{"id": "prisma", "name": "PRISMA", "official_url": f"{EQUATOR}/prisma/"}],
    "trial_protocol": [{"id": "spirit", "name": "SPIRIT", "official_url": f"{EQUATOR}/spirit-2013-statement-defining-standard-protocol-items-for-clinical-trials/"}],
    "systematic_review_protocol": [{"id": "prisma-p", "name": "PRISMA-P", "official_url": f"{EQUATOR}/prisma-protocols/"}],
    "diagnostic_accuracy": [{"id": "stard", "name": "STARD", "official_url": f"{EQUATOR}/stard/"}],
    "prediction_model": [{"id": "tripod", "name": "TRIPOD", "official_url": f"{EQUATOR}/tripod-statement/"}],
    "case_report": [{"id": "care", "name": "CARE", "official_url": f"{EQUATOR}/care-guidelines-for-case-reports/"}],
    "qualitative_study": [
        {"id": "srqr", "name": "SRQR", "official_url": f"{EQUATOR}/srqr/"},
        {"id": "coreq", "name": "COREQ", "official_url": f"{EQUATOR}/coreq/"},
    ],
    "animal_preclinical": [{"id": "arrive", "name": "ARRIVE", "official_url": f"{EQUATOR}/arrive-guidelines/"}],
    "quality_improvement": [{"id": "squire", "name": "SQUIRE", "official_url": f"{EQUATOR}/squire/"}],
    "economic_evaluation": [{"id": "cheers", "name": "CHEERS", "official_url": f"{EQUATOR}/cheers/"}],
}


class IntakeError(ValueError):
    pass


def _exact_keys(value: dict[str, Any], expected: set[str], scope: str) -> None:
    actual = set(value)
    if actual != expected:
        raise IntakeError(f"{scope} keys differ; missing={sorted(expected - actual)}; unknown={sorted(actual - expected)}")


def _string(value: Any, scope: str) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > 300:
        raise IntakeError(f"{scope} must be a non-empty string of at most 300 characters")
    return value.strip()


def _identifier(value: Any, scope: str) -> str:
    text = _string(value, scope)
    if not IDENTIFIER.fullmatch(text):
        raise IntakeError(f"{scope} must be a lowercase stable identifier")
    return text


def _checked_date(value: Any, scope: str) -> str:
    text = _string(value, scope)
    if not DATE.fullmatch(text):
        raise IntakeError(f"{scope} must be YYYY-MM-DD")
    try:
        checked = date.fromisoformat(text)
    except ValueError as exc:
        raise IntakeError(f"{scope} must be a valid calendar date") from exc
    if checked > date.today():
        raise IntakeError(f"{scope} must not be in the future")
    return text


def _digest(value: dict[str, Any]) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def select_guidelines(study_design: str) -> dict[str, Any]:
    if not isinstance(study_design, str) or study_design not in GUIDELINES:
        raise IntakeError(f"unsupported study design: {study_design}")
    return {
        "schema_version": 1,
        "status": "CANDIDATE_ONLY",
        "study_design": study_design,
        "guidelines": GUIDELINES[study_design],
        "registry": "EQUATOR Network",
        "registry_url": "https://www.equator-network.org/reporting-guidelines/",
        "registry_checked_at": "2026-08-27",
        "compliance_scored": False,
        "requires_current_official_confirmation": True,
        "next_action": "Confirm the current guideline, extensions, venue mandate, and exact checklist with first-party sources.",
    }


def validate_intake(intake: Any) -> dict[str, Any]:
    if not isinstance(intake, dict):
        raise IntakeError("intake must be an object")
    _exact_keys(intake, ROOT_KEYS, "intake")
    if intake["schema_version"] != 1:
        raise IntakeError("schema_version must equal 1")
    authorization = intake["authorization"]
    if not isinstance(authorization, dict):
        raise IntakeError("authorization must be an object")
    _exact_keys(authorization, AUTH_KEYS, "authorization")
    bool_fields = (
        "authorized_to_process",
        "confidentiality_policy_checked",
        "venue_ai_policy_checked",
        "ai_assistance_permitted",
        "external_services_allowed",
        "human_accountable",
    )
    for field in bool_fields:
        if type(authorization[field]) is not bool:
            raise IntakeError(f"authorization.{field} must be boolean")
    if not isinstance(authorization["retention_decision"], str) or authorization["retention_decision"] not in {"ephemeral", "project_controlled", "owner_defined"}:
        raise IntakeError("authorization.retention_decision is unsupported")
    if not isinstance(authorization["conflicts_status"], str) or authorization["conflicts_status"] not in {"none", "resolved", "unresolved"}:
        raise IntakeError("authorization.conflicts_status is unsupported")

    findings: list[dict[str, str]] = []
    gates = (
        ("authorized_to_process", True, "PROCESSING_NOT_AUTHORIZED"),
        ("confidentiality_policy_checked", True, "CONFIDENTIALITY_POLICY_UNCHECKED"),
        ("venue_ai_policy_checked", True, "VENUE_AI_POLICY_UNCHECKED"),
        ("ai_assistance_permitted", True, "AI_ASSISTANCE_NOT_PERMITTED"),
        ("external_services_allowed", False, "EXTERNAL_PROCESSING_NOT_ALLOWED"),
        ("human_accountable", True, "HUMAN_ACCOUNTABILITY_MISSING"),
    )
    for field, expected, code in gates:
        if authorization[field] is not expected:
            findings.append({"code": code, "scope": "authorization", "item_id": "authorization"})
    if authorization["conflicts_status"] == "unresolved":
        findings.append({"code": "CONFLICTS_UNRESOLVED", "scope": "authorization", "item_id": "authorization"})

    submission = intake["submission"]
    if not isinstance(submission, dict):
        raise IntakeError("submission must be an object")
    _exact_keys(submission, SUBMISSION_KEYS, "submission")
    for field in SUBMISSION_KEYS - {"official_sources_checked_at"}:
        _string(submission[field], f"submission.{field}")
    if not isinstance(submission["study_design"], str) or submission["study_design"] not in GUIDELINES:
        raise IntakeError("submission.study_design is unsupported")
    _checked_date(submission["official_sources_checked_at"], "submission.official_sources_checked_at")

    coverage = intake["guideline_coverage"]
    if not isinstance(coverage, list) or len(coverage) > 64:
        raise IntakeError("guideline_coverage must be a list of at most 64 items")
    counts = {"applicable": 0, "not_applicable": 0, "pending": 0}
    covered: set[str] = set()
    for item in coverage:
        if not isinstance(item, dict):
            raise IntakeError("each guideline coverage item must be an object")
        _exact_keys(item, COVERAGE_KEYS, "guideline coverage")
        guideline_id = _identifier(item["guideline_id"], "guideline_id")
        if guideline_id in covered:
            raise IntakeError(f"duplicate guideline coverage: {guideline_id}")
        covered.add(guideline_id)
        applicability = item["applicability"]
        if not isinstance(applicability, str) or applicability not in counts:
            raise IntakeError(f"unsupported applicability for {guideline_id}")
        counts[applicability] += 1
        _string(item["evidence_locator"], f"{guideline_id}.evidence_locator")
        if type(item["human_verified"]) is not bool:
            raise IntakeError(f"{guideline_id}.human_verified must be boolean")
        if applicability == "pending" or not item["human_verified"]:
            findings.append({"code": "GUIDELINE_COVERAGE_PENDING", "scope": "guideline", "item_id": guideline_id})

    candidates = [item["id"] for item in GUIDELINES[submission["study_design"]]]
    for guideline_id in candidates:
        if guideline_id not in covered:
            findings.append({"code": "CANDIDATE_GUIDELINE_UNASSESSED", "scope": "guideline", "item_id": guideline_id})

    blocked = any(item["scope"] == "authorization" for item in findings)
    return {
        "schema_version": 1,
        "status": "BLOCKED" if blocked else ("PARTIAL" if findings else "PASS"),
        "intake_digest_sha256": _digest(intake),
        "candidate_guidelines": candidates,
        "coverage": counts,
        "findings": findings,
        "content_echoed": False,
        "external_processing": "not_performed",
        "compliance_scored": False,
    }


def _is_link_like(path: Path) -> bool:
    attributes = getattr(path.lstat(), "st_file_attributes", 0)
    reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    return path.is_symlink() or bool(reparse and attributes & reparse)


def load_intake(path: Path) -> dict[str, Any]:
    if _is_link_like(path):
        raise IntakeError("intake path must not be a symlink or reparse point")
    info = path.stat()
    if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_BYTES:
        raise IntakeError("intake must be a regular file no larger than 128 KiB")
    try:
        value = json.loads(path.read_bytes().decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise IntakeError("intake is not readable UTF-8 JSON") from exc
    if not isinstance(value, dict):
        raise IntakeError("intake must be an object")
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate")
    validate.add_argument("--intake", type=Path, required=True)
    guidelines = commands.add_parser("guidelines")
    guidelines.add_argument("--study-design", choices=sorted(GUIDELINES), required=True)
    args = parser.parse_args(argv)
    try:
        output = select_guidelines(args.study_design) if args.command == "guidelines" else validate_intake(load_intake(args.intake))
    except (IntakeError, OSError) as exc:
        print(json.dumps({"status": "INVALID", "message": str(exc)}, sort_keys=True), file=sys.stderr)
        return 2
    print(json.dumps(output, ensure_ascii=False, sort_keys=True))
    return 0 if output["status"] in {"PASS", "PARTIAL", "CANDIDATE_ONLY"} else 3


if __name__ == "__main__":
    raise SystemExit(main())
