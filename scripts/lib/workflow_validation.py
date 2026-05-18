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
RELEASE_CANDIDATE_OVERCLAIM_PATTERNS = (
    re.compile(r"\boccurrence probability\b", re.IGNORECASE),
    re.compile(r"\bphysical probability\b", re.IGNORECASE),
    re.compile(r"\bannual frequency\b", re.IGNORECASE),
    re.compile(r"\breturn[- ]?period\b", re.IGNORECASE),
    re.compile(r"\brisk\b", re.IGNORECASE),
)
RELEASE_CANDIDATE_PROVENANCE_STATES = (
    "workflow_generated",
    "field_supported",
    "mixed_provenance",
    "blocked_missing_provenance",
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


def classify_release_candidate_provenance_state(
    *,
    workflow_generated: bool,
    field_supported: bool,
    blocked_missing_provenance: bool = False,
) -> str:
    if blocked_missing_provenance or (not workflow_generated and not field_supported):
        return "blocked_missing_provenance"
    if workflow_generated and field_supported:
        return "mixed_provenance"
    if field_supported:
        return "field_supported"
    return "workflow_generated"


def build_release_zone_provenance_intake(
    provenance: Mapping[str, Any] | None = None,
    *,
    workflow_generated: bool | None = None,
    field_supported: bool | None = None,
    blocked_missing_provenance: bool | None = None,
    provenance_note: str | None = None,
    provenance_source: str | None = None,
) -> dict[str, Any]:
    raw_provenance = provenance if isinstance(provenance, dict) else {}
    if workflow_generated is None and "workflow_generated" in raw_provenance:
        workflow_generated = bool(raw_provenance.get("workflow_generated"))
    if field_supported is None and "field_supported" in raw_provenance:
        field_supported = bool(raw_provenance.get("field_supported"))
    if blocked_missing_provenance is None and "blocked_missing_provenance" in raw_provenance:
        blocked_missing_provenance = bool(raw_provenance.get("blocked_missing_provenance"))
    provenance_state = raw_provenance.get("release_zone_provenance_state") or raw_provenance.get("release_candidate_provenance_state") or raw_provenance.get("provenance_state")
    if provenance_state is not None:
        provenance_state = str(provenance_state).strip()
        if provenance_state not in RELEASE_CANDIDATE_PROVENANCE_STATES:
            raise ValueError(
                f"release_zone_provenance_state must be one of {sorted(RELEASE_CANDIDATE_PROVENANCE_STATES)}"
            )
        workflow_generated = provenance_state in {"workflow_generated", "mixed_provenance"}
        field_supported = provenance_state in {"field_supported", "mixed_provenance"}
        blocked_missing_provenance = provenance_state == "blocked_missing_provenance"

    if workflow_generated is None and field_supported is None and blocked_missing_provenance is None:
        if raw_provenance:
            workflow_generated = True
            field_supported = False
            blocked_missing_provenance = False
        else:
            workflow_generated = False
            field_supported = False
            blocked_missing_provenance = True

    workflow_generated = bool(workflow_generated)
    field_supported = bool(field_supported)
    blocked_missing_provenance = bool(blocked_missing_provenance)

    normalized_state = classify_release_candidate_provenance_state(
        workflow_generated=workflow_generated,
        field_supported=field_supported,
        blocked_missing_provenance=blocked_missing_provenance,
    )
    notes = raw_provenance.get("notes")
    if provenance_note is None:
        if isinstance(notes, list):
            provenance_note = "; ".join(str(item).strip() for item in notes if str(item).strip())
        else:
            provenance_note = str(raw_provenance.get("source") or "").strip()

    return {
        "release_zone_provenance_state": normalized_state,
        "release_candidate_provenance_state": normalized_state,
        "workflow_generated": workflow_generated,
        "field_supported": field_supported,
        "blocked_missing_provenance": blocked_missing_provenance,
        "provenance_note": str(provenance_note or "").strip(),
        "provenance_source": str(provenance_source or raw_provenance.get("source") or "").strip(),
    }


def build_release_candidate_physical_meaning_firewall(
    records: Sequence[Mapping[str, Any]],
    *,
    label_prefix: str = "release_candidate_physical_meaning_firewall",
) -> dict[str, Any]:
    profile: list[dict[str, Any]] = []
    counts = {state: 0 for state in RELEASE_CANDIDATE_PROVENANCE_STATES}
    for index, record in enumerate(records):
        intake = build_release_zone_provenance_intake(
            record.get("release_zone_provenance_intake"),
            workflow_generated=record.get("workflow_generated"),
            field_supported=record.get("field_supported"),
            blocked_missing_provenance=record.get("blocked_missing_provenance"),
            provenance_note=str(record.get("provenance_note") or "").strip(),
            provenance_source=str(record.get("release_zone_provenance_source") or "").strip(),
        )
        workflow_generated = bool(intake["workflow_generated"])
        field_supported = bool(intake["field_supported"])
        blocked_missing_provenance = bool(intake["blocked_missing_provenance"])
        provenance_state = str(intake["release_zone_provenance_state"])
        counts[provenance_state] += 1
        profile.append(
            {
                "row_index": index,
                "candidate_release_zone_record_id": str(record.get("candidate_release_zone_record_id") or "").strip(),
                "candidate_release_zone_record_kind": str(record.get("candidate_release_zone_record_kind") or "").strip(),
                "workflow_generated": workflow_generated,
                "field_supported": field_supported,
                "blocked_missing_provenance": blocked_missing_provenance,
                "provenance_state": provenance_state,
                "provenance_note": str(intake["provenance_note"]),
                "release_zone_provenance_state": str(intake["release_zone_provenance_state"]),
            }
        )

    if counts["blocked_missing_provenance"]:
        aggregate_state = "blocked_missing_provenance"
    elif counts["mixed_provenance"]:
        aggregate_state = "mixed_provenance"
    elif counts["field_supported"]:
        aggregate_state = "field_supported"
    elif counts["workflow_generated"]:
        aggregate_state = "workflow_generated"
    else:
        aggregate_state = "blocked_missing_provenance"

    firewall = {
        "firewall_status": aggregate_state,
        "release_candidate_provenance_state": aggregate_state,
        "release_candidate_provenance_state_counts": counts,
        "release_candidate_provenance_profile": profile,
        "sampling_weight_semantics": "conditional_sampling_only",
        "sampling_weight_boundary": "not occurrence probability, physical probability, annual frequency, return period, or risk",
        "sampling_weight_not_occurrence_probability": True,
        "sampling_weight_not_physical_probability": True,
        "sampling_weight_not_annual_frequency": True,
        "sampling_weight_not_return_period": True,
        "sampling_weight_not_risk": True,
        "physical_probability_claims_allowed": False,
        "annual_frequency_claims_allowed": False,
        "return_period_claims_allowed": False,
        "risk_claims_allowed": False,
    }
    return firewall


def validate_release_candidate_physical_meaning_firewall(
    firewall: Mapping[str, Any],
    *,
    error_cls: type[Exception],
    label_prefix: str = "release_candidate_physical_meaning_firewall",
) -> None:
    require_mapping(firewall, label_prefix, error_cls)
    require(
        firewall.get("release_candidate_provenance_state") in RELEASE_CANDIDATE_PROVENANCE_STATES,
        f"{label_prefix}.release_candidate_provenance_state must be one of {sorted(RELEASE_CANDIDATE_PROVENANCE_STATES)}",
        error_cls,
    )
    require_false_fields(
        firewall,
        (
            "physical_probability_claims_allowed",
            "annual_frequency_claims_allowed",
            "return_period_claims_allowed",
            "risk_claims_allowed",
        ),
        error_cls,
        label_prefix=label_prefix,
    )
    counts = require_mapping(firewall.get("release_candidate_provenance_state_counts"), f"{label_prefix}.release_candidate_provenance_state_counts", error_cls)
    for state in RELEASE_CANDIDATE_PROVENANCE_STATES:
        require(
            counts.get(state) is not None,
            f"{label_prefix}.release_candidate_provenance_state_counts must include {state}",
            error_cls,
        )
        require(
            isinstance(counts.get(state), int) and counts.get(state) >= 0,
            f"{label_prefix}.release_candidate_provenance_state_counts.{state} must be a nonnegative integer",
            error_cls,
        )
    profile = require_list(firewall.get("release_candidate_provenance_profile"), f"{label_prefix}.release_candidate_provenance_profile", error_cls)
    for index, raw in enumerate(profile):
        entry = require_mapping(raw, f"{label_prefix}.release_candidate_provenance_profile[{index}]", error_cls)
        require(
            entry.get("provenance_state") in RELEASE_CANDIDATE_PROVENANCE_STATES,
            f"{label_prefix}.release_candidate_provenance_profile[{index}].provenance_state must be one of {sorted(RELEASE_CANDIDATE_PROVENANCE_STATES)}",
            error_cls,
        )
        require(
            entry.get("workflow_generated") is not None,
            f"{label_prefix}.release_candidate_provenance_profile[{index}].workflow_generated must be present",
            error_cls,
        )
        require(
            entry.get("field_supported") is not None,
            f"{label_prefix}.release_candidate_provenance_profile[{index}].field_supported must be present",
            error_cls,
        )
    scan_text_for_misleading_claims(
        firewall,
        require_fn=lambda condition, message: require(condition, message, error_cls),
        patterns=RELEASE_CANDIDATE_OVERCLAIM_PATTERNS,
        path=label_prefix,
    )


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
