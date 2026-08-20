"""Root-bounded path resolution shared by venue-audit collectors."""

from __future__ import annotations

from pathlib import Path


GLOB_CHARS = "*?["


class PathBoundaryError(ValueError):
    """Raised when an input or output escapes the declared audit root."""


def resolve_root(value: str | Path) -> Path:
    root = Path(value).resolve()
    if not root.is_dir():
        raise PathBoundaryError("declared root is not a directory")
    return root


def _validate_spec(spec: str, label: str) -> Path:
    if not isinstance(spec, str) or not spec or "\x00" in spec:
        raise PathBoundaryError(f"{label} must be a non-empty relative path")
    candidate = Path(spec)
    if candidate.is_absolute() or candidate.drive:
        raise PathBoundaryError(f"{label} must be relative to the declared root")
    return candidate


def _require_inside(root: Path, candidate: Path, label: str) -> Path:
    resolved = candidate.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise PathBoundaryError(f"{label} escapes the declared root") from exc
    return resolved


def portable_path(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def resolve_input_specs(
    root: Path, specs: list[str]
) -> tuple[list[Path], list[str]]:
    found: dict[str, Path] = {}
    missing: list[str] = []
    for spec in specs:
        relative = _validate_spec(spec, "input")
        if any(char in spec for char in GLOB_CHARS):
            try:
                matches = [
                    path for path in root.glob(spec) if path.is_file()
                ]
            except (OSError, ValueError) as exc:
                raise PathBoundaryError("input glob is invalid") from exc
        else:
            candidate = root / relative
            matches = [candidate] if candidate.is_file() else []
        if not matches:
            missing.append(spec)
            continue
        for match in matches:
            resolved = _require_inside(root, match, "input")
            if not resolved.is_file():
                continue
            found[portable_path(root, resolved)] = resolved
    return [found[key] for key in sorted(found)], missing


def resolve_input(root: Path, spec: str, label: str = "input") -> Path:
    relative = _validate_spec(spec, label)
    resolved = _require_inside(root, root / relative, label)
    if not resolved.is_file():
        raise PathBoundaryError(f"{label} does not exist")
    return resolved


def resolve_output(root: Path, spec: str, label: str = "output") -> Path:
    relative = _validate_spec(spec, label)
    resolved = _require_inside(root, root / relative, label)
    if resolved == root:
        raise PathBoundaryError(f"{label} must name a file beneath the root")
    return resolved
