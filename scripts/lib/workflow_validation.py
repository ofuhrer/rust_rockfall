from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

import yaml


CONTROL_CHARS_RE = re.compile(r"[\x00-\x1f\x7f]")
SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")
DEFAULT_CLAIM_BOUNDARY_FIELDS = (
    "annual_frequency_supported",
    "physical_probability_supported",
    "return_period_supported",
    "operational_hazard_map_supported",
    "risk_or_exposure_supported",
)
DEFAULT_MISLEADING_ALLOW_MARKERS = (
    "unsupported",
    "not_",
    "not ",
    "no ",
    "no_",
    "without",
    "defer",
    "future",
    "out of scope",
)
DEFAULT_MISLEADING_PATTERNS = (
    re.compile(r"\breturn[- ]?period\b", re.IGNORECASE),
    re.compile(r"\brisk[- ]?map\b", re.IGNORECASE),
    re.compile(r"\boperational(?:ly)?\s+(?:approved|validated|ready|hazard)\b", re.IGNORECASE),
)
DEFAULT_SKIP_KEYS = frozenset({"claim_boundary", "claim_boundaries", "does_not_verify", "does_not_support"})


def read_yaml(
    path: Path,
    error_cls: type[Exception],
    *,
    read_message: str = "failed to read YAML",
    object_message: str = "YAML document must be an object",
) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - user-facing path context matters.
        prefix = f"{read_message} " if read_message else "failed to read "
        raise error_cls(f"{prefix}{path}: {exc}") from exc
    if not isinstance(data, dict):
        raise error_cls(f"{object_message}: {path}")
    return data


def read_json(
    path: Path,
    error_cls: type[Exception],
    *,
    read_message: str = "failed to read JSON",
    object_message: str = "JSON document must be an object",
) -> dict[str, Any]:
    import json

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - user-facing path context matters.
        prefix = f"{read_message} " if read_message else "failed to read "
        raise error_cls(f"{prefix}{path}: {exc}") from exc
    if not isinstance(data, dict):
        raise error_cls(f"{object_message}: {path}")
    return data


def resolve_repo_path(root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


def require_paths_exist(
    paths: Mapping[str, str | Path],
    error_cls: type[Exception],
    *,
    root: Path | None = None,
    label_prefix: str = "required_path",
) -> dict[str, Path]:
    resolved: dict[str, Path] = {}
    for name, raw_path in paths.items():
        path = resolve_repo_path(root, raw_path) if root is not None else Path(raw_path)
        require(path.exists(), f"{label_prefix}.{name} does not exist: {path}", error_cls)
        resolved[name] = path
    return resolved


def missing_repo_paths(paths: Mapping[str, str | Path], *, root: Path | None = None) -> list[str]:
    missing: list[str] = []
    for raw_path in paths.values():
        path = resolve_repo_path(root, raw_path) if root is not None else Path(raw_path)
        if not path.exists():
            missing.append(str(path))
    return missing


def require_checksum_fields(
    record: Mapping[str, Any],
    fields: Sequence[str],
    error_cls: type[Exception],
    *,
    label_prefix: str = "artifact_checksums",
    allow_none: bool = False,
) -> dict[str, str | None]:
    validated: dict[str, str | None] = {}
    for field in fields:
        value = record.get(field)
        if value is None:
            require(allow_none, f"{label_prefix}.{field} must be a lowercase SHA-256 hex digest", error_cls)
            validated[field] = None
            continue
        checksum = require_text(value, f"{label_prefix}.{field}", error_cls)
        require_sha256_hex(checksum, f"{label_prefix}.{field}", error_cls)
        validated[field] = checksum
    return validated


def build_blocked_report(
    *,
    schema_version: str,
    status_key: str,
    missing_inputs: Sequence[str],
    blocked_reason: str,
    blocked_status: str = "blocked_missing_inputs",
    extra_fields: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    report = {
        "schema_version": schema_version,
        status_key: blocked_status,
        "blocked_reason": blocked_reason,
        "missing_inputs": sorted({str(item).strip() for item in missing_inputs if str(item).strip()}),
    }
    if extra_fields:
        report.update(extra_fields)
    return report


def normalize_text(value: Any) -> str:
    text = str(value).strip().replace("\\", "/")
    return CONTROL_CHARS_RE.sub("", text)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require(condition: bool, message: str, error_cls: type[Exception]) -> None:
    if not condition:
        raise error_cls(message)


def require_mapping(value: Any, field: str, error_cls: type[Exception]) -> dict[str, Any]:
    require(isinstance(value, dict), f"{field} must be an object", error_cls)
    return value


def require_list(value: Any, field: str, error_cls: type[Exception]) -> list[Any]:
    require(isinstance(value, list), f"{field} must be a list", error_cls)
    return value


def require_text(value: Any, field: str, error_cls: type[Exception]) -> str:
    require(isinstance(value, str) and value.strip(), f"{field} must be a nonempty string", error_cls)
    return value


def require_number(value: Any, field: str, error_cls: type[Exception]) -> float:
    require(isinstance(value, (int, float)), f"{field} must be numeric", error_cls)
    return float(value)


def require_positive_number(value: Any, field: str, error_cls: type[Exception]) -> float:
    number = require_number(value, field, error_cls)
    require(number > 0.0, f"{field} must be positive", error_cls)
    return number


def require_int(value: Any, field: str, error_cls: type[Exception], *, minimum: int) -> int:
    require(isinstance(value, int), f"{field} must be an integer", error_cls)
    require(value >= minimum, f"{field} must be at least {minimum}", error_cls)
    return value


def require_positive_int(value: Any, field: str, error_cls: type[Exception]) -> int:
    return require_int(value, field, error_cls, minimum=1)


def require_sha256_hex(value: str, field: str, error_cls: type[Exception]) -> None:
    require(SHA256_HEX_RE.fullmatch(value) is not None, f"{field} must be a lowercase SHA-256 hex digest", error_cls)


def require_false_fields(
    record: Mapping[str, Any],
    fields: Sequence[str],
    error_cls: type[Exception],
    *,
    label_prefix: str = "claim_boundary",
) -> None:
    for field in fields:
        require(record.get(field) is False, f"{label_prefix}.{field} must be false", error_cls)


def scan_text_for_misleading_claims(
    value: Any,
    *,
    require_fn: Callable[[bool, str], None],
    patterns: Iterable[re.Pattern[str]] = DEFAULT_MISLEADING_PATTERNS,
    path: str = "record",
    skip_keys: Iterable[str] = DEFAULT_SKIP_KEYS,
    allow_markers: Iterable[str] = DEFAULT_MISLEADING_ALLOW_MARKERS,
) -> None:
    skip = set(skip_keys)
    if isinstance(value, dict):
        for key, child in value.items():
            if key in skip:
                continue
            scan_text_for_misleading_claims(
                child,
                require_fn=require_fn,
                patterns=patterns,
                path=f"{path}.{key}",
                skip_keys=skip,
                allow_markers=allow_markers,
            )
    elif isinstance(value, list):
        for index, child in enumerate(value):
            scan_text_for_misleading_claims(
                child,
                require_fn=require_fn,
                patterns=patterns,
                path=f"{path}[{index}]",
                skip_keys=skip,
                allow_markers=allow_markers,
            )
    elif isinstance(value, str):
        lower = value.lower()
        if any(marker in lower for marker in allow_markers):
            return
        for pattern in patterns:
            require_fn(pattern.search(value) is None, f"{path} contains misleading current-product claim: {value!r}")


def render_status_message(
    subject: str,
    path: Path | str,
    summary: Mapping[str, Any],
    status_key: str,
    *,
    extra_fields: Sequence[tuple[str, str]] = (),
) -> str:
    pieces = [str(summary[status_key])]
    pieces.extend(f"{label}={summary[key]}" for key, label in extra_fields)
    suffix = f" ({', '.join(pieces)})" if pieces else ""
    return f"{subject} is valid: {path}{suffix}"
