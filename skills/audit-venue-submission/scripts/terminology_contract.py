"""Schema validation for version-1 scholarly terminology contracts."""

from __future__ import annotations

from typing import Any


def _string_list(value: Any, path: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise ValueError(f"{path} must be an array of non-empty strings")
    return value


def _exact_keys(
    value: dict[str, Any],
    allowed: set[str],
    required: set[str],
    path: str,
) -> None:
    unknown = set(value) - allowed
    missing = required - set(value)
    if unknown:
        raise ValueError(f"{path} has unknown fields: {sorted(unknown)}")
    if missing:
        raise ValueError(f"{path} is missing fields: {sorted(missing)}")


def validate_contract(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ValueError("terminology contract root must be an object")
    _exact_keys(
        data,
        {"version", "terms", "scopes", "acronyms"},
        {"version", "terms", "scopes"},
        "contract",
    )
    if data.get("version") != 1:
        raise ValueError("terminology contract must use version 1")
    terms = data.get("terms")
    scopes = data.get("scopes")
    if (
        not isinstance(terms, list)
        or not terms
        or not isinstance(scopes, list)
        or not scopes
    ):
        raise ValueError("terminology contract requires terms[] and scopes[]")

    term_ids: list[str] = []
    for index, term in enumerate(terms):
        path = f"terms[{index}]"
        if not isinstance(term, dict):
            raise ValueError(f"{path} must be an object")
        _exact_keys(
            term,
            {"id", "canonical", "forbidden_variants", "case_sensitive"},
            {"id", "canonical"},
            path,
        )
        term_id = term.get("id")
        canonical = term.get("canonical")
        if not isinstance(term_id, str) or not term_id:
            raise ValueError(f"{path}.id must be a non-empty string")
        if not isinstance(canonical, str) or not canonical:
            raise ValueError(f"{path}.canonical must be a non-empty string")
        _string_list(term.get("forbidden_variants", []), f"{path}.forbidden_variants")
        if "case_sensitive" in term and not isinstance(term["case_sensitive"], bool):
            raise ValueError(f"{path}.case_sensitive must be boolean")
        term_ids.append(term_id)
    if len(term_ids) != len(set(term_ids)):
        raise ValueError("every terminology term needs a unique id")

    scope_names: list[str] = []
    for index, scope in enumerate(scopes):
        path = f"scopes[{index}]"
        if not isinstance(scope, dict):
            raise ValueError(f"{path} must be an object")
        _exact_keys(
            scope,
            {
                "name",
                "files",
                "require",
                "scan_terms",
                "allowed_variants",
                "require_mode",
                "start",
                "end",
            },
            {"name", "files"},
            path,
        )
        name = scope.get("name")
        if not isinstance(name, str) or not name:
            raise ValueError(f"{path}.name must be a non-empty string")
        _string_list(scope.get("files"), f"{path}.files")
        for field in ("require", "scan_terms", "allowed_variants"):
            if field in scope:
                _string_list(scope[field], f"{path}.{field}")
        for field in ("require", "scan_terms"):
            unknown_ids = set(scope.get(field, [])) - set(term_ids)
            if unknown_ids:
                raise ValueError(
                    f"{path}.{field} references unknown terms: "
                    f"{sorted(unknown_ids)}"
                )
        for field in ("start", "end"):
            if field in scope and (
                not isinstance(scope[field], str) or not scope[field]
            ):
                raise ValueError(f"{path}.{field} must be a non-empty string")
        if scope.get("require_mode", "scope") not in {"scope", "each_file"}:
            raise ValueError(f"{path}.require_mode must be 'scope' or 'each_file'")
        scope_names.append(name)
    if len(scope_names) != len(set(scope_names)):
        raise ValueError("every terminology scope needs a unique name")

    acronyms = data.get("acronyms", [])
    if not isinstance(acronyms, list):
        raise ValueError("acronyms must be an array")
    for index, acronym in enumerate(acronyms):
        path = f"acronyms[{index}]"
        if not isinstance(acronym, dict):
            raise ValueError(f"{path} must be an object")
        _exact_keys(
            acronym,
            {"short", "long", "scopes"},
            {"short", "long"},
            path,
        )
        for field in ("short", "long"):
            if not isinstance(acronym.get(field), str) or not acronym[field]:
                raise ValueError(f"{path}.{field} must be a non-empty string")
        acronym_scopes = _string_list(
            acronym.get("scopes", []), f"{path}.scopes"
        )
        unknown_scopes = set(acronym_scopes) - set(scope_names)
        if unknown_scopes:
            raise ValueError(
                f"{path}.scopes references unknown scopes: "
                f"{sorted(unknown_scopes)}"
            )
    return data
