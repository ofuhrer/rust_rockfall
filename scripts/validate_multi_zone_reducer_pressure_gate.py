#!/usr/bin/env python3
"""Validate a fixture-backed multi-zone reducer pressure regression gate.

The gate stays local and fail-closed. It materializes deterministic scratch
fixtures, compares the measured reducer manifest bytes, output-family file
counts, output-family bytes, sidecar counts, reducer wall time, and merge-order
determinism against fixture-backed warning and blocked thresholds, and never
relies on live Balfrin artifacts.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import summarize_multi_zone_reducer_pressure as reducer_pressure  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "multi_zone_reducer_pressure_gate_v1"
REPORT_BASENAME = "multi_zone_reducer_pressure_gate_v1"
DEFAULT_ARTIFACT_DIR = Path("/tmp/rust_rockfall/multi_zone_reducer_pressure_gate_v1")
DEFAULT_TARGET_ROOT = DEFAULT_ARTIFACT_DIR / "target_fixture_root"
DEFAULT_TARGET_RELEASE_ZONE_COUNT = 8
DEFAULT_TARGET_REDUCER_CHUNK_COUNT = 2
DEFAULT_TARGET_REDUCER_WORKERS = 2
DEFAULT_WARNING_RELEASE_ZONE_COUNT = 9
DEFAULT_WARNING_REDUCER_CHUNK_COUNT = 3
DEFAULT_WARNING_REDUCER_WORKERS = 2
DEFAULT_BLOCKED_RELEASE_ZONE_COUNT = 11
DEFAULT_BLOCKED_REDUCER_CHUNK_COUNT = 4
DEFAULT_BLOCKED_REDUCER_WORKERS = 2
DEFAULT_OUTPUT_FAMILY_MIX = reducer_pressure.DEFAULT_OUTPUT_FAMILY_MIX


class MultiZoneReducerPressureGateError(ValueError):
    """User-facing pressure-gate validation error."""


@dataclass(frozen=True)
class FixtureProfile:
    profile_name: str
    root: Path
    release_zone_count: int
    reducer_chunk_count: int
    reducer_worker_count: int
    output_family_mix: tuple[str, ...]
    report: dict[str, Any]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe-root", type=Path, default=None, help="Existing scratch probe root to validate.")
    parser.add_argument(
        "--materialize-root",
        type=Path,
        default=None,
        help="Create the deterministic target fixture root at this path before validating it.",
    )
    parser.add_argument("--release-zone-count", type=int, default=DEFAULT_TARGET_RELEASE_ZONE_COUNT)
    parser.add_argument("--reducer-chunk-count", type=int, default=DEFAULT_TARGET_REDUCER_CHUNK_COUNT)
    parser.add_argument("--reducer-workers", type=int, default=DEFAULT_TARGET_REDUCER_WORKERS)
    parser.add_argument(
        "--output-family-mix",
        default=None,
        help="Comma-separated output families to materialize for the target and threshold fixtures.",
    )
    parser.add_argument("--warning-release-zone-count", type=int, default=DEFAULT_WARNING_RELEASE_ZONE_COUNT)
    parser.add_argument("--warning-reducer-chunk-count", type=int, default=DEFAULT_WARNING_REDUCER_CHUNK_COUNT)
    parser.add_argument("--warning-reducer-workers", type=int, default=DEFAULT_WARNING_REDUCER_WORKERS)
    parser.add_argument("--blocked-release-zone-count", type=int, default=DEFAULT_BLOCKED_RELEASE_ZONE_COUNT)
    parser.add_argument("--blocked-reducer-chunk-count", type=int, default=DEFAULT_BLOCKED_REDUCER_CHUNK_COUNT)
    parser.add_argument("--blocked-reducer-workers", type=int, default=DEFAULT_BLOCKED_REDUCER_WORKERS)
    parser.add_argument("--format", choices=("json", "text"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    parser.add_argument("--text-output", type=Path, default=None)
    parser.add_argument("--artifact-dir", type=Path, default=None)
    return parser.parse_args(argv)


def _load_json(path: Path | None) -> dict[str, Any] | None:
    if path is None or not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else None


def _ensure_positive_int(value: int, label: str) -> int:
    if value <= 1:
        raise MultiZoneReducerPressureGateError(f"{label} must be greater than 1")
    return value


def _ensure_positive_count(value: int, label: str) -> int:
    if value <= 0:
        raise MultiZoneReducerPressureGateError(f"{label} must be greater than 0")
    return value


def _compare_numeric_metric(*, measured: int | float, warning_limit: int | float, blocked_limit: int | float) -> str:
    if measured > blocked_limit:
        return "blocked"
    if measured > warning_limit:
        return "warning"
    return "ready"


def _worse_status(left: str, right: str) -> str:
    order = {"ready": 0, "warning": 1, "blocked": 2}
    return left if order.get(left, 0) >= order.get(right, 0) else right


def _profile_measurements(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "release_zone_count": report.get("release_zone_count"),
        "reducer_chunk_count": report.get("reducer_chunk_count"),
        "reducer_worker_count": report.get("reducer_worker_count"),
        "output_family_mix": report.get("output_family_mix", []),
        "manifest_size_bytes": report.get("manifest_size_bytes"),
        "output_file_count": report.get("output_file_count"),
        "output_byte_count": report.get("output_byte_count"),
        "reducer_manifest_bytes": report.get("reducer_manifest_bytes"),
        "reducer_manifest_file_count": report.get("reducer_manifest_file_count"),
        "sidecar_file_count": report.get("sidecar_file_count"),
        "sidecar_byte_count": report.get("sidecar_byte_count"),
        "reducer_wall_time_seconds": report.get("reducer_wall_time_seconds"),
        "merge_order": report.get("merge_order"),
        "merge_order_independent": report.get("merge_order_independent"),
        "merge_order_deterministic": report.get("merge_order_deterministic"),
        "output_family_file_counts": dict(report.get("output_family_file_counts") or {}),
        "output_family_bytes": dict(report.get("output_family_bytes") or {}),
        "sidecar_family_file_counts": dict(report.get("sidecar_family_file_counts") or {}),
        "sidecar_family_bytes": dict(report.get("sidecar_family_bytes") or {}),
        "primary_output_family_file_counts": dict(report.get("primary_output_family_file_counts") or {}),
        "primary_output_family_bytes": dict(report.get("primary_output_family_bytes") or {}),
    }


def _materialize_profile(
    *,
    tmpdir: Path,
    profile_name: str,
    release_zone_count: int,
    reducer_chunk_count: int,
    reducer_worker_count: int,
    output_family_mix: tuple[str, ...],
) -> FixtureProfile:
    root = tmpdir / profile_name
    reducer_pressure.materialize_probe_root(
        root,
        release_zone_count=release_zone_count,
        reducer_worker_count=reducer_worker_count,
        reducer_chunk_count=reducer_chunk_count,
        output_family_mix=output_family_mix,
    )
    report = reducer_pressure.build_report(root)
    return FixtureProfile(
        profile_name=profile_name,
        root=root,
        release_zone_count=release_zone_count,
        reducer_chunk_count=reducer_chunk_count,
        reducer_worker_count=reducer_worker_count,
        output_family_mix=output_family_mix,
        report=report,
    )


def _build_threshold_profile(
    *,
    tmpdir: Path,
    profile_name: str,
    release_zone_count: int,
    reducer_chunk_count: int,
    reducer_worker_count: int,
    output_family_mix: tuple[str, ...],
) -> FixtureProfile:
    return _materialize_profile(
        tmpdir=tmpdir,
        profile_name=profile_name,
        release_zone_count=release_zone_count,
        reducer_chunk_count=reducer_chunk_count,
        reducer_worker_count=reducer_worker_count,
        output_family_mix=output_family_mix,
    )


def _build_family_checks(
    *,
    measured: dict[str, int],
    warning: dict[str, int],
    blocked: dict[str, int],
    value_kind: str,
) -> list[dict[str, Any]]:
    families = sorted(set(measured) | set(warning) | set(blocked))
    checks: list[dict[str, Any]] = []
    for family in families:
        measured_value = int(measured.get(family, 0))
        warning_value = int(warning.get(family, 0))
        blocked_value = int(blocked.get(family, 0))
        status = _compare_numeric_metric(
            measured=measured_value,
            warning_limit=warning_value,
            blocked_limit=blocked_value,
        )
        checks.append(
            {
                "kind": family,
                "value_kind": value_kind,
                "measured": measured_value,
                "warning_threshold": warning_value,
                "blocked_threshold": blocked_value,
                "status": status,
                "threshold_provenance": "fixture_backed",
            }
        )
    return checks


def build_report(
    evidence_override: dict[str, Any] | None = None,
    *,
    probe_root: Path | None = None,
    materialize_root: Path | None = None,
    release_zone_count: int = DEFAULT_TARGET_RELEASE_ZONE_COUNT,
    reducer_chunk_count: int = DEFAULT_TARGET_REDUCER_CHUNK_COUNT,
    reducer_workers: int = DEFAULT_TARGET_REDUCER_WORKERS,
    output_family_mix: tuple[str, ...] | str | None = None,
    manifest_mode: str = "full",
    warning_release_zone_count: int = DEFAULT_WARNING_RELEASE_ZONE_COUNT,
    warning_reducer_chunk_count: int = DEFAULT_WARNING_REDUCER_CHUNK_COUNT,
    warning_reducer_workers: int = DEFAULT_WARNING_REDUCER_WORKERS,
    blocked_release_zone_count: int = DEFAULT_BLOCKED_RELEASE_ZONE_COUNT,
    blocked_reducer_chunk_count: int = DEFAULT_BLOCKED_REDUCER_CHUNK_COUNT,
    blocked_reducer_workers: int = DEFAULT_BLOCKED_REDUCER_WORKERS,
) -> dict[str, Any]:
    if evidence_override is not None and isinstance(evidence_override.get("pressure_gate_report"), dict):
        return dict(evidence_override["pressure_gate_report"])

    output_family_mix = reducer_pressure.normalize_output_family_mix(output_family_mix)
    release_zone_count = _ensure_positive_int(release_zone_count, "release_zone_count")
    reducer_chunk_count = _ensure_positive_count(reducer_chunk_count, "reducer_chunk_count")
    reducer_workers = _ensure_positive_count(reducer_workers, "reducer_workers")
    warning_release_zone_count = _ensure_positive_int(warning_release_zone_count, "warning_release_zone_count")
    warning_reducer_chunk_count = _ensure_positive_count(warning_reducer_chunk_count, "warning_reducer_chunk_count")
    warning_reducer_workers = _ensure_positive_count(warning_reducer_workers, "warning_reducer_workers")
    blocked_release_zone_count = _ensure_positive_int(blocked_release_zone_count, "blocked_release_zone_count")
    blocked_reducer_chunk_count = _ensure_positive_count(blocked_reducer_chunk_count, "blocked_reducer_chunk_count")
    blocked_reducer_workers = _ensure_positive_count(blocked_reducer_workers, "blocked_reducer_workers")
    if warning_release_zone_count >= blocked_release_zone_count:
        raise MultiZoneReducerPressureGateError("warning_release_zone_count must be less than blocked_release_zone_count")
    if warning_reducer_chunk_count >= blocked_reducer_chunk_count:
        raise MultiZoneReducerPressureGateError("warning_reducer_chunk_count must be less than blocked_reducer_chunk_count")

    if materialize_root is not None:
        target_root = materialize_root
        reducer_pressure.materialize_probe_root(
            target_root,
            release_zone_count=release_zone_count,
            reducer_worker_count=reducer_workers,
            reducer_chunk_count=reducer_chunk_count,
            output_family_mix=output_family_mix,
            manifest_mode=manifest_mode,
        )
    elif probe_root is not None:
        target_root = probe_root
    else:
        target_root = DEFAULT_TARGET_ROOT
        reducer_pressure.materialize_probe_root(
            target_root,
            release_zone_count=release_zone_count,
            reducer_worker_count=reducer_workers,
            reducer_chunk_count=reducer_chunk_count,
            output_family_mix=output_family_mix,
            manifest_mode=manifest_mode,
        )

    with tempfile.TemporaryDirectory() as tmpdir:
        temp_root = Path(tmpdir)
        warning_profile = _build_threshold_profile(
            tmpdir=temp_root,
            profile_name="warning_fixture",
            release_zone_count=warning_release_zone_count,
            reducer_chunk_count=warning_reducer_chunk_count,
            reducer_worker_count=warning_reducer_workers,
            output_family_mix=output_family_mix,
        )
        blocked_profile = _build_threshold_profile(
            tmpdir=temp_root,
            profile_name="blocked_fixture",
            release_zone_count=blocked_release_zone_count,
            reducer_chunk_count=blocked_reducer_chunk_count,
            reducer_worker_count=blocked_reducer_workers,
            output_family_mix=output_family_mix,
        )

    target_report = reducer_pressure.build_report(target_root)
    target_profile = _profile_measurements(target_report)
    warning_profile_measurements = _profile_measurements(warning_profile.report)
    blocked_profile_measurements = _profile_measurements(blocked_profile.report)

    budget_checks: list[dict[str, Any]] = []
    numeric_metrics = (
        "manifest_size_bytes",
        "output_file_count",
        "output_byte_count",
        "reducer_manifest_bytes",
        "reducer_manifest_file_count",
        "sidecar_file_count",
        "sidecar_byte_count",
        "reducer_wall_time_seconds",
    )
    for metric in numeric_metrics:
        measured_value = target_profile[metric]
        warning_value = warning_profile_measurements[metric]
        blocked_value = blocked_profile_measurements[metric]
        status = _compare_numeric_metric(
            measured=measured_value,
            warning_limit=warning_value,
            blocked_limit=blocked_value,
        )
        budget_checks.append(
            {
                "metric": metric,
                "measured": measured_value,
                "warning_threshold": warning_value,
                "blocked_threshold": blocked_value,
                "status": status,
                "threshold_provenance": "fixture_backed",
            }
        )

    family_count_checks = _build_family_checks(
        measured=target_profile["output_family_file_counts"],
        warning=warning_profile_measurements["output_family_file_counts"],
        blocked=blocked_profile_measurements["output_family_file_counts"],
        value_kind="file_count",
    )
    family_byte_checks = _build_family_checks(
        measured=target_profile["output_family_bytes"],
        warning=warning_profile_measurements["output_family_bytes"],
        blocked=blocked_profile_measurements["output_family_bytes"],
        value_kind="bytes",
    )

    merge_order_ok = bool(target_profile["merge_order_deterministic"])
    merge_order_status = "ready" if merge_order_ok else "blocked"
    merge_order_check = {
        "metric": "merge_order_determinism",
        "measured": target_profile["merge_order"],
        "merge_order_independent": target_profile["merge_order_independent"],
        "merge_order_deterministic": target_profile["merge_order_deterministic"],
        "expected_merge_order": "sorted_chunk_id",
        "expected_merge_order_independent": True,
        "status": merge_order_status,
        "threshold_provenance": "fixture_backed",
    }
    budget_checks.append(merge_order_check)

    aggregate_status = "ready"
    for check in budget_checks:
        aggregate_status = _worse_status(aggregate_status, check["status"])
    for check in family_count_checks + family_byte_checks:
        aggregate_status = _worse_status(aggregate_status, check["status"])

    if aggregate_status == "blocked":
        gate_status = "blocked_fixture_backed"
    elif aggregate_status == "warning":
        gate_status = "fixture_backed_warning"
    else:
        gate_status = "fixture_backed_ready"

    thresholds = {
        "status": "fixture_backed",
        "warning": {
            "release_zone_count": warning_profile.release_zone_count,
            "reducer_chunk_count": warning_profile.reducer_chunk_count,
            "reducer_worker_count": warning_profile.reducer_worker_count,
            "output_family_mix": list(warning_profile.output_family_mix),
            "measurements": warning_profile_measurements,
        },
        "blocked": {
            "release_zone_count": blocked_profile.release_zone_count,
            "reducer_chunk_count": blocked_profile.reducer_chunk_count,
            "reducer_worker_count": blocked_profile.reducer_worker_count,
            "output_family_mix": list(blocked_profile.output_family_mix),
            "measurements": blocked_profile_measurements,
        },
    }

    blocked_reasons = [check["metric"] for check in budget_checks if check["status"] == "blocked"]
    blocked_reasons.extend(
        f"{check['kind']}:{check['value_kind']}" for check in family_count_checks + family_byte_checks if check["status"] == "blocked"
    )
    warning_reasons = [check["metric"] for check in budget_checks if check["status"] == "warning"]
    warning_reasons.extend(
        f"{check['kind']}:{check['value_kind']}" for check in family_count_checks + family_byte_checks if check["status"] == "warning"
    )
    if merge_order_check["status"] == "blocked":
        blocked_reasons.append("merge_order_determinism")

    report = {
        "schema_version": SCHEMA_VERSION,
        "gate_status": gate_status,
        "threshold_provenance": "fixture_backed",
        "target_root": str(target_root),
        "target_profile": target_profile,
        "validation_output_inventory": target_report.get("validation_output_inventory", {}),
        "thresholds": thresholds,
        "budget_checks": budget_checks,
        "family_count_checks": family_count_checks,
        "family_byte_checks": family_byte_checks,
        "merge_order_check": merge_order_check,
        "warning_reasons": warning_reasons,
        "blocked_reasons": blocked_reasons,
        "claim_boundaries": {
            "operational_claims_allowed": False,
            "annual_frequency_claims_allowed": False,
            "physical_probability_claims_allowed": False,
            "risk_exposure_vulnerability_claims_allowed": False,
            "scale_up_authorized": False,
            "distributed_execution_authorized": False,
        },
        "summary": summarize_report(gate_status, target_profile, warning_reasons, blocked_reasons),
        "measurement_command": (
            "PYENV_VERSION=system uv run python scripts/validate_multi_zone_reducer_pressure_gate.py "
            f"--materialize-root {target_root} --output-family-mix {','.join(output_family_mix)} --format json"
        ),
    }
    return report


def summarize_report(
    gate_status: str,
    target_profile: dict[str, Any],
    warning_reasons: list[str],
    blocked_reasons: list[str],
) -> str:
    if gate_status == "blocked_fixture_backed":
        return (
            "Fixture-backed multi-zone reducer pressure gate is blocked: "
            f"{len(blocked_reasons)} blocked checks, {len(warning_reasons)} warning checks, "
            f"{target_profile.get('release_zone_count')} release zones, "
            f"{target_profile.get('output_file_count')} output files, "
            f"{target_profile.get('sidecar_file_count')} sidecar files."
        )
    if gate_status == "fixture_backed_warning":
        return (
            "Fixture-backed multi-zone reducer pressure gate is warning: "
            f"{len(warning_reasons)} warning checks, "
            f"{target_profile.get('release_zone_count')} release zones, "
            f"{target_profile.get('output_file_count')} output files, "
            f"{target_profile.get('sidecar_file_count')} sidecar files."
        )
    return (
        "Fixture-backed multi-zone reducer pressure gate is ready: "
        f"{target_profile.get('release_zone_count')} release zones, "
        f"{target_profile.get('output_file_count')} output files, "
        f"{target_profile.get('sidecar_file_count')} sidecar files, "
        f"deterministic merge order preserved."
    )


def render_text_report(report: dict[str, Any]) -> str:
    lines = [
        "Multi-Zone Reducer Pressure Gate",
        f"schema_version: {report.get('schema_version', 'unknown')}",
        f"gate_status: {report.get('gate_status', 'unknown')}",
        f"threshold_provenance: {report.get('threshold_provenance', 'unknown')}",
        f"target_root: {report.get('target_root', 'unknown')}",
        f"summary: {report.get('summary', '')}",
        "",
        "target_profile:",
    ]
    target_profile = report.get("target_profile", {})
    for key in (
        "release_zone_count",
        "reducer_chunk_count",
        "reducer_worker_count",
        "output_family_mix",
        "manifest_size_bytes",
        "output_file_count",
        "output_byte_count",
        "reducer_manifest_bytes",
        "reducer_manifest_file_count",
        "sidecar_file_count",
        "sidecar_byte_count",
        "reducer_wall_time_seconds",
        "merge_order",
        "merge_order_independent",
        "merge_order_deterministic",
    ):
        lines.append(f"  - {key}: {target_profile.get(key)}")
    lines.append("budget_checks:")
    for check in report.get("budget_checks", []):
        lines.append(
            f"  - {check.get('metric')}: status={check.get('status')} measured={check.get('measured')} "
            f"warning={check.get('warning_threshold')} blocked={check.get('blocked_threshold')}"
        )
    lines.append("family_count_checks:")
    for check in report.get("family_count_checks", []):
        lines.append(
            f"  - {check.get('kind')}: status={check.get('status')} measured={check.get('measured')} "
            f"warning={check.get('warning_threshold')} blocked={check.get('blocked_threshold')}"
        )
    lines.append("family_byte_checks:")
    for check in report.get("family_byte_checks", []):
        lines.append(
            f"  - {check.get('kind')}: status={check.get('status')} measured={check.get('measured')} "
            f"warning={check.get('warning_threshold')} blocked={check.get('blocked_threshold')}"
        )
    lines.append("merge_order_check:")
    merge_order_check = report.get("merge_order_check", {})
    for key in (
        "metric",
        "measured",
        "expected_merge_order",
        "expected_merge_order_independent",
        "merge_order_independent",
        "merge_order_deterministic",
        "status",
    ):
        lines.append(f"  - {key}: {merge_order_check.get(key)}")
    if report.get("warning_reasons"):
        lines.append("warning_reasons:")
        for reason in report.get("warning_reasons", []):
            lines.append(f"  - {reason}")
    if report.get("blocked_reasons"):
        lines.append("blocked_reasons:")
        for reason in report.get("blocked_reasons", []):
            lines.append(f"  - {reason}")
    return "\n".join(lines)


def materialize_artifacts(
    report: dict[str, Any],
    *,
    json_output: Path | None = None,
    text_output: Path | None = None,
    artifact_dir: Path | None = None,
) -> None:
    if artifact_dir is not None:
        artifact_dir.mkdir(parents=True, exist_ok=True)
        json_output = json_output or (artifact_dir / f"{REPORT_BASENAME}.json")
        text_output = text_output or (artifact_dir / f"{REPORT_BASENAME}.txt")
    if json_output is not None:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if text_output is not None:
        text_output.parent.mkdir(parents=True, exist_ok=True)
        text_output.write_text(render_text_report(report), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        report = build_report(
            probe_root=args.probe_root,
            materialize_root=args.materialize_root,
            release_zone_count=args.release_zone_count,
            reducer_chunk_count=args.reducer_chunk_count,
            reducer_workers=args.reducer_workers,
            output_family_mix=args.output_family_mix,
            warning_release_zone_count=args.warning_release_zone_count,
            warning_reducer_chunk_count=args.warning_reducer_chunk_count,
            warning_reducer_workers=args.warning_reducer_workers,
            blocked_release_zone_count=args.blocked_release_zone_count,
            blocked_reducer_chunk_count=args.blocked_reducer_chunk_count,
            blocked_reducer_workers=args.blocked_reducer_workers,
        )
    except (OSError, ValueError) as exc:
        print(f"multi-zone reducer pressure gate error: {exc}", file=sys.stderr)
        return 2

    materialize_artifacts(report, json_output=args.json_output, text_output=args.text_output, artifact_dir=args.artifact_dir)

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text_report(report))
    return 0 if report["gate_status"] == "fixture_backed_ready" else 2


if __name__ == "__main__":
    raise SystemExit(main())
