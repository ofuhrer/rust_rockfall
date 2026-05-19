#!/usr/bin/env python3
"""Preview AOI scenario cost, output pressure, and execution suitability.

The helper stays in the pre-execution boundary. It consumes reviewed candidate
packages, expands their frozen source-zone / block-family contracts, and
projects output pressure with measured envelope helpers. It does not run
simulations, authorize scale-up, or submit anything to Balfrin.
"""

from __future__ import annotations

import argparse
import json
import tempfile
import sys
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except ImportError as exc:  # pragma: no cover - environment setup.
    raise SystemExit(
        "PyYAML is required. Run this script with `PYENV_VERSION=system uv run python ...`; "
        "CI may use `requirements-tools.txt`"
    ) from exc

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import generate_candidate_source_zone_scenarios as FREEZER
from scripts import estimate_swiss_wide_execution_envelope as ENVELOPE
from scripts import summarize_bounded_validation_output_profile as OUTPUT_BUDGET
from scripts.lib import output_profile_policy as OUTPUT_PROFILE_POLICY


SCHEMA_VERSION = "aoi_scenario_preview_v1"
DEFAULT_REVIEW_PACKAGE = ROOT / "tests/fixtures/aoi_scenario_preview/tiny_review_package.yaml"
DEFAULT_TRAJECTORY_COUNT = None
DEFAULT_OUTPUT_ROOT = Path("/tmp/rust_rockfall/aoi_scenario_preview")
DEFAULT_OUTPUT_PROFILE_CONTROLS = {
    "conditional_curve_export": "summary-only",
    "grid_csv_export": "none",
    "no_plots": True,
    "explicit_debug_override": False,
}
DEFAULT_BLOCK_FAMILY_TEMPLATE_ID = "policy_block_family_v1"
DEFAULT_SCENARIO_FAMILY_TEMPLATE_ID = "policy_block_family_v1"
LOCAL_TARGET = "local_smoke"
BALFRIN_TARGET = "balfrin_postproc"
BLOCKED_TARGET = "blocked"
BLOCKED_MISSING_REVIEWED_CANDIDATES = "blocked_missing_reviewed_candidates"
BLOCKED_UNKNOWN_TRAJECTORY_BUDGET = "blocked_unknown_trajectory_budget"
BLOCKED_UNSUPPORTED_PROFILE = "blocked_unsupported_profile"
BLOCKED_OUTPUT_BUDGET_EXCEEDED = "blocked_output_budget_exceeded"


class AoiScenarioPreviewError(ValueError):
    """User-facing AOI scenario preview error."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--review-package",
        type=Path,
        action="append",
        default=None,
        help="Reviewed candidate package to include in the preview. Repeat for multi-zone previews.",
    )
    parser.add_argument(
        "--trajectory-count",
        type=int,
        default=DEFAULT_TRAJECTORY_COUNT,
        help="Trajectory budget to preview. When omitted, the helper falls back to reviewed-package metadata.",
    )
    parser.add_argument(
        "--conditional-curve-export",
        default=DEFAULT_OUTPUT_PROFILE_CONTROLS["conditional_curve_export"],
        help="Hazard output control used to classify the output profile.",
    )
    parser.add_argument(
        "--grid-csv-export",
        default=DEFAULT_OUTPUT_PROFILE_CONTROLS["grid_csv_export"],
        help="Hazard output control used to classify the output profile.",
    )
    parser.add_argument("--no-plots", action="store_true", default=DEFAULT_OUTPUT_PROFILE_CONTROLS["no_plots"])
    parser.add_argument(
        "--explicit-debug-override",
        action="store_true",
        default=DEFAULT_OUTPUT_PROFILE_CONTROLS["explicit_debug_override"],
        help="Allow an explicit heavy-debug output-profile override.",
    )
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    args = parser.parse_args(argv)

    review_packages = args.review_package or [DEFAULT_REVIEW_PACKAGE]

    try:
        report = build_report(
            review_package_paths=review_packages,
            trajectory_count=args.trajectory_count,
            output_profile_policy=OUTPUT_PROFILE_POLICY.classify_output_profile_policy(
                conditional_curve_export=args.conditional_curve_export,
                grid_csv_export=args.grid_csv_export,
                no_plots=args.no_plots,
                explicit_debug_override=args.explicit_debug_override,
                label="aoi_scenario_preview",
            ),
        )
    except AoiScenarioPreviewError as exc:
        print(f"aoi scenario preview error: {exc}", file=sys.stderr)
        return 2

    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text_report(report))
    return 0 if report["preview_status"] == "ready" else 2


def build_report(
    *,
    review_package_paths: list[Path] | tuple[Path, ...],
    trajectory_count: int | None = DEFAULT_TRAJECTORY_COUNT,
    output_profile_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not review_package_paths:
        return blocked_report(
            review_package_paths=[],
            blocked_reason="no reviewed candidate packages were supplied",
            blocking_label=BLOCKED_MISSING_REVIEWED_CANDIDATES,
            output_profile_policy=output_profile_policy or default_output_profile_policy(),
        )

    profile_policy = output_profile_policy or default_output_profile_policy()
    blocking_label = None
    if profile_policy.get("classification") == OUTPUT_PROFILE_POLICY.BLOCKED_UNSCALABLE_DEFAULT:
        blocking_label = BLOCKED_UNSUPPORTED_PROFILE

    package_reports: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(dir="/tmp", prefix="aoi_scenario_preview_") as tmpdir:
        output_root = Path(tmpdir)
        for index, review_package_path in enumerate(review_package_paths, start=1):
            package_path = Path(review_package_path)
            if not package_path.exists():
                return blocked_report(
                    review_package_paths=[package_path],
                    blocked_reason=f"missing reviewed candidate package: {display_path(package_path)}",
                    blocking_label=BLOCKED_MISSING_REVIEWED_CANDIDATES,
                    output_profile_policy=profile_policy,
                )
            review_package = load_review_package(package_path)
            reviewed_candidates = list((review_package.get("review_application") or {}).get("accepted_candidate_ids") or [])
            if review_package.get("review_package_status") != "review_applied" or not reviewed_candidates:
                return blocked_report(
                    review_package_paths=[package_path],
                    blocked_reason="missing reviewed candidates in reviewed package",
                    blocking_label=BLOCKED_MISSING_REVIEWED_CANDIDATES,
                    output_profile_policy=profile_policy,
                )
            preview_count = trajectory_count if trajectory_count is not None else infer_trajectory_count(package_path)
            if preview_count is None or preview_count <= 0:
                return blocked_report(
                    review_package_paths=[package_path],
                    blocked_reason="trajectory budget is missing or invalid",
                    blocking_label=BLOCKED_UNKNOWN_TRAJECTORY_BUDGET,
                    output_profile_policy=profile_policy,
                )
            try:
                review_report = FREEZER.build_freezer_report(
                    review_package_path=package_path,
                    accepted_candidate_ids=None,
                    output_root=output_root / f"review_{index:02d}",
                    trajectory_count=preview_count,
                    seed=34014 + index,
                )
            except FREEZER.CandidateSourceZoneFreezerError as exc:
                return blocked_report(
                    review_package_paths=[package_path],
                    blocked_reason=f"missing reviewed candidates: {exc}",
                    blocking_label=BLOCKED_MISSING_REVIEWED_CANDIDATES,
                    output_profile_policy=profile_policy,
                )
            package_reports.append(review_report)

    if trajectory_count is None:
        inferred = {
            int(report["source_zone_metadata"].get("trajectory_count_target"))
            for report in package_reports
            if isinstance(report.get("source_zone_metadata", {}).get("trajectory_count_target"), int)
        }
        if not inferred or any(value in (None, "") for value in inferred) or len(inferred) > 1:
            return blocked_report(
                review_package_paths=[Path(report["review_package_path"]) for report in package_reports],
                blocked_reason="trajectory budget is missing or invalid",
                blocking_label=BLOCKED_UNKNOWN_TRAJECTORY_BUDGET,
                output_profile_policy=profile_policy,
            )
        trajectory_count = int(next(iter(inferred)))

    rows = build_preview_rows(package_reports, trajectory_count=trajectory_count, output_profile_policy=profile_policy)
    summary = summarize_preview_rows(rows)
    projected_totals = aggregate_bands(row["projected_files"] for row in rows)
    projected_bytes = aggregate_bands(row["projected_bytes"] for row in rows)
    projected_runtime_seconds = aggregate_float_bands(row["estimated_runtime_seconds"] for row in rows)
    budget_summary = OUTPUT_BUDGET.build_summary()
    target = recommend_execution_target(
        profile_policy=profile_policy,
        projected_files=projected_totals,
        projected_bytes=projected_bytes,
        budget_summary=budget_summary,
    )
    blocking_labels = list(summary["blocking_labels"])
    if target["target_status"] == BLOCKED_TARGET and BLOCKED_OUTPUT_BUDGET_EXCEEDED not in blocking_labels:
        blocking_labels.append(BLOCKED_OUTPUT_BUDGET_EXCEEDED)
    if blocking_label and blocking_label not in blocking_labels:
        blocking_labels.insert(0, blocking_label)

    for row in rows:
        row["recommended_execution_target"] = target["target"]
        row["labels"] = list(blocking_labels)

    preview_status = "ready"
    blocked_reason = ""
    if blocking_labels:
        preview_status = blocking_labels[0]
        blocked_reason = target["blocked_reason"] or ", ".join(blocking_labels)

    report = {
        "schema_version": SCHEMA_VERSION,
        "preview_status": preview_status,
        "blocked_reason": blocked_reason,
        "read_only": True,
        "scale_up_authorized": False,
        "operational_claims_allowed": False,
        "review_package_count": len(package_reports),
        "trajectory_count": trajectory_count,
        "output_profile_policy": profile_policy,
        "output_profile_choice": profile_policy.get("classification", "unknown"),
        "blocking_labels": blocking_labels,
        "source_zone_count": summary["source_zone_count"],
        "scenario_family_count": summary["scenario_family_count"],
        "scenario_cardinality": summary["scenario_cardinality"],
        "rows": rows,
        "projected_files": projected_totals,
        "projected_bytes": projected_bytes,
        "estimated_runtime_seconds": projected_runtime_seconds,
        "budget_summary": budget_summary,
        "execution_target": target,
        "output_budget_assessment": {
            "local": target["local_assessment"],
            "balfrin": target["balfrin_assessment"],
            "budget_exceeded": target["target_status"] == BLOCKED_TARGET,
        },
    }
    return report


def build_preview_rows(
    package_reports: list[dict[str, Any]],
    *,
    trajectory_count: int,
    output_profile_policy: dict[str, Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    output_profile_choice = output_profile_policy.get("classification", "unknown")
    for package_report in package_reports:
        source_zone_metadata = package_report.get("source_zone_metadata", {}) or {}
        block_family_ids = list(package_report.get("block_family_ids", []) or [])
        if not block_family_ids:
            block_family_ids = [DEFAULT_BLOCK_FAMILY_TEMPLATE_ID]
        accepted_candidate_count = int(package_report.get("accepted_candidate_count") or source_zone_metadata.get("accepted_candidate_count") or 0)
        scenario_family_id = build_scenario_family_id(package_report)
        for block_family_id in block_family_ids:
            row_units = max(1, accepted_candidate_count) * trajectory_count
            estimated = estimate_output_pressure(row_units)
            rows.append(
                {
                    "source_zone_id": package_report.get("source_zone_id", ""),
                    "block_family_id": block_family_id,
                    "scenario_family_id": scenario_family_id,
                    "scenario_family_template_id": DEFAULT_SCENARIO_FAMILY_TEMPLATE_ID,
                    "trajectory_count": trajectory_count,
                    "output_profile_choice": output_profile_choice,
                    "projected_files": estimated["projected_files"],
                    "projected_bytes": estimated["projected_bytes"],
                    "estimated_runtime_seconds": estimated["estimated_runtime_seconds"],
                    "reviewed_candidate_count": accepted_candidate_count,
                    "recommended_execution_target": "",
                    "labels": [],
                }
            )
    return rows


def summarize_preview_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    source_zone_ids = sorted({row.get("source_zone_id", "") for row in rows if row.get("source_zone_id")})
    scenario_family_ids = sorted({row.get("scenario_family_id", "") for row in rows if row.get("scenario_family_id")})
    source_zone_count = len(source_zone_ids)
    scenario_family_count = len(scenario_family_ids)
    scenario_cardinality = {
        "source_zone_count": source_zone_count,
        "scenario_family_count": scenario_family_count,
        "row_count": len(rows),
    }
    blocking_labels: list[str] = []
    return {
        "source_zone_count": source_zone_count,
        "scenario_family_count": scenario_family_count,
        "scenario_cardinality": scenario_cardinality,
        "blocking_labels": blocking_labels,
    }


def recommend_execution_target(
    *,
    profile_policy: dict[str, Any],
    projected_files: dict[str, int],
    projected_bytes: dict[str, int],
    budget_summary: dict[str, Any],
) -> dict[str, Any]:
    current_pressure = budget_summary.get("current_pressure", {}) or {}
    output_budget_gate = budget_summary.get("output_budget_gate", {}) or {}
    validation_output_budget = output_budget_gate.get("validation_output_budget", {}) or {}
    hazard_output_budget = output_budget_gate.get("hazard_output_budget", {}) or {}
    local_file_ceiling = int(current_pressure.get("file_count_ceiling") or 0)
    local_byte_ceiling = int(current_pressure.get("byte_ceiling") or 0)
    balfrin_file_ceiling = min(
        int(validation_output_budget.get("file_count") or 0) or 0,
        int(hazard_output_budget.get("file_count") or 0) or 0,
    )
    balfrin_byte_ceiling = min(
        int(validation_output_budget.get("bytes") or 0) or 0,
        int(hazard_output_budget.get("bytes") or 0) or 0,
    )
    nominal_files = int(projected_files.get("nominal") or 0)
    nominal_bytes = int(projected_bytes.get("nominal") or 0)

    local_safe = nominal_files <= local_file_ceiling and nominal_bytes <= local_byte_ceiling
    balfrin_safe = nominal_files <= balfrin_file_ceiling and nominal_bytes <= balfrin_byte_ceiling

    if profile_policy.get("classification") == OUTPUT_PROFILE_POLICY.BLOCKED_UNSCALABLE_DEFAULT:
        return {
            "target_status": BLOCKED_TARGET,
            "target": BLOCKED_TARGET,
            "blocked_reason": "unsupported output profile requires an explicit override",
            "local_assessment": {
                "status": "blocked_unsupported_profile",
                "file_ceiling": local_file_ceiling,
                "byte_ceiling": local_byte_ceiling,
                "projected_files": projected_files,
                "projected_bytes": projected_bytes,
            },
            "balfrin_assessment": {
                "status": "blocked_unsupported_profile",
                "file_ceiling": balfrin_file_ceiling,
                "byte_ceiling": balfrin_byte_ceiling,
                "projected_files": projected_files,
                "projected_bytes": projected_bytes,
            },
        }

    if local_safe:
        return {
            "target_status": LOCAL_TARGET,
            "target": LOCAL_TARGET,
            "blocked_reason": "",
            "local_assessment": {
                "status": "safe",
                "file_ceiling": local_file_ceiling,
                "byte_ceiling": local_byte_ceiling,
                "projected_files": projected_files,
                "projected_bytes": projected_bytes,
            },
            "balfrin_assessment": {
                "status": "not_required",
                "file_ceiling": balfrin_file_ceiling,
                "byte_ceiling": balfrin_byte_ceiling,
                "projected_files": projected_files,
                "projected_bytes": projected_bytes,
            },
        }

    if balfrin_safe:
        return {
            "target_status": BALFRIN_TARGET,
            "target": BALFRIN_TARGET,
            "blocked_reason": "",
            "local_assessment": {
                "status": "output_pressure_exceeds_local_smoke",
                "file_ceiling": local_file_ceiling,
                "byte_ceiling": local_byte_ceiling,
                "projected_files": projected_files,
                "projected_bytes": projected_bytes,
            },
            "balfrin_assessment": {
                "status": "safe",
                "file_ceiling": balfrin_file_ceiling,
                "byte_ceiling": balfrin_byte_ceiling,
                "projected_files": projected_files,
                "projected_bytes": projected_bytes,
            },
        }

    return {
        "target_status": BLOCKED_TARGET,
        "target": BLOCKED_TARGET,
        "blocked_reason": "projected files or bytes exceed the preview budget ceiling",
        "local_assessment": {
            "status": "output_budget_exceeded",
            "file_ceiling": local_file_ceiling,
            "byte_ceiling": local_byte_ceiling,
            "projected_files": projected_files,
            "projected_bytes": projected_bytes,
        },
        "balfrin_assessment": {
            "status": "output_budget_exceeded",
            "file_ceiling": balfrin_file_ceiling,
            "byte_ceiling": balfrin_byte_ceiling,
            "projected_files": projected_files,
            "projected_bytes": projected_bytes,
        },
    }


def estimate_output_pressure(row_units: int) -> dict[str, dict[str, int] | dict[str, float]]:
    coefficients = ENVELOPE.load_measured_coefficients()
    runtime_seconds = ENVELOPE.build_scalar_band(
        row_units,
        coefficients.runtime_seconds_per_unit_low,
        coefficients.runtime_seconds_per_unit_nominal,
        coefficients.runtime_seconds_per_unit_high,
        precision=3,
    )
    projected_files = ENVELOPE.build_integer_band(
        row_units,
        coefficients.file_count_per_unit_low,
        coefficients.file_count_per_unit_nominal,
        coefficients.file_count_per_unit_high,
    )
    projected_bytes = ENVELOPE.build_integer_band(
        row_units,
        coefficients.storage_bytes_per_unit_low,
        coefficients.storage_bytes_per_unit_nominal,
        coefficients.storage_bytes_per_unit_high,
    )
    if row_units > 0:
        for key in ("low", "nominal", "high"):
            if runtime_seconds[key] <= 0:
                runtime_seconds[key] = 0.001
    return {
        "estimated_runtime_seconds": runtime_seconds,
        "projected_files": projected_files,
        "projected_bytes": projected_bytes,
    }


def aggregate_bands(bands: list[dict[str, Any]] | Any) -> dict[str, int]:
    total = {"low": 0, "nominal": 0, "high": 0}
    for band in bands:
        if not isinstance(band, dict):
            continue
        for key in total:
            total[key] += int(band.get(key) or 0)
    return total


def aggregate_float_bands(bands: list[dict[str, Any]] | Any) -> dict[str, float]:
    total = {"low": 0.0, "nominal": 0.0, "high": 0.0}
    for band in bands:
        if not isinstance(band, dict):
            continue
        for key in total:
            total[key] += float(band.get(key) or 0.0)
    return total


def build_scenario_family_id(package_report: dict[str, Any]) -> str:
    source_zone_id = str(package_report.get("source_zone_id") or "source_zone")
    policy_id = str(package_report.get("policy", {}).get("policy_id") or "policy")
    return f"{source_zone_id}__{policy_id}__{DEFAULT_SCENARIO_FAMILY_TEMPLATE_ID}"


def infer_trajectory_count(review_package_path: Path) -> int | None:
    review_package = load_review_package(review_package_path)
    for key in ("trajectory_count_target", "trajectory_count"):
        value = review_package.get(key)
        if isinstance(value, int) and value > 0:
            return value
        if isinstance(review_package.get("review_application"), dict):
            nested = review_package["review_application"].get(key)
            if isinstance(nested, int) and nested > 0:
                return nested
    return None


def load_review_package(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def default_output_profile_policy() -> dict[str, Any]:
    return OUTPUT_PROFILE_POLICY.classify_output_profile_policy(
        conditional_curve_export=DEFAULT_OUTPUT_PROFILE_CONTROLS["conditional_curve_export"],
        grid_csv_export=DEFAULT_OUTPUT_PROFILE_CONTROLS["grid_csv_export"],
        no_plots=DEFAULT_OUTPUT_PROFILE_CONTROLS["no_plots"],
        explicit_debug_override=DEFAULT_OUTPUT_PROFILE_CONTROLS["explicit_debug_override"],
        label="aoi_scenario_preview",
    )


def blocked_report(
    *,
    review_package_paths: list[Path],
    blocked_reason: str,
    blocking_label: str,
    output_profile_policy: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "preview_status": blocking_label,
        "blocked_reason": blocked_reason,
        "read_only": True,
        "scale_up_authorized": False,
        "operational_claims_allowed": False,
        "review_package_count": len(review_package_paths),
        "trajectory_count": None,
        "output_profile_policy": output_profile_policy,
        "output_profile_choice": output_profile_policy.get("classification", "unknown"),
        "blocking_labels": [blocking_label],
        "source_zone_count": 0,
        "scenario_family_count": 0,
        "scenario_cardinality": {
            "source_zone_count": 0,
            "scenario_family_count": 0,
            "row_count": 0,
        },
        "rows": [],
        "projected_files": {"low": 0, "nominal": 0, "high": 0},
        "projected_bytes": {"low": 0, "nominal": 0, "high": 0},
        "estimated_runtime_seconds": {"low": 0.0, "nominal": 0.0, "high": 0.0},
        "budget_summary": OUTPUT_BUDGET.build_summary(),
        "execution_target": {
            "target_status": BLOCKED_TARGET,
            "target": BLOCKED_TARGET,
            "blocked_reason": blocked_reason,
            "local_assessment": {"status": blocking_label},
            "balfrin_assessment": {"status": blocking_label},
        },
        "output_budget_assessment": {
            "local": {"status": blocking_label},
            "balfrin": {"status": blocking_label},
            "budget_exceeded": True,
        },
    }


def render_text_report(report: dict[str, Any]) -> str:
    lines = [
        "AOI Scenario Preview",
        "",
        f"- schema_version: `{report['schema_version']}`",
        f"- preview_status: `{report['preview_status']}`",
        f"- blocked_reason: `{report['blocked_reason']}`",
        f"- output_profile_choice: `{report['output_profile_choice']}`",
        f"- review_package_count: `{report['review_package_count']}`",
        f"- trajectory_count: `{report['trajectory_count']}`",
        f"- source_zone_count: `{report['source_zone_count']}`",
        f"- scenario_family_count: `{report['scenario_family_count']}`",
        "",
        "Scenario Preview Rows",
    ]
    for row in report.get("rows", []):
        lines.append(f"- source_zone_id: `{row.get('source_zone_id', '')}`")
        lines.append(f"  block_family_id: `{row.get('block_family_id', '')}`")
        lines.append(f"  scenario_family_id: `{row.get('scenario_family_id', '')}`")
        lines.append(f"  trajectory_count: `{row.get('trajectory_count', '')}`")
        lines.append(f"  output_profile_choice: `{row.get('output_profile_choice', '')}`")
        lines.append(f"  projected_files: `{row.get('projected_files', {})}`")
        lines.append(f"  projected_bytes: `{row.get('projected_bytes', {})}`")
        lines.append(f"  estimated_runtime_seconds: `{row.get('estimated_runtime_seconds', {})}`")
        lines.append(f"  recommended_execution_target: `{row.get('recommended_execution_target', '')}`")
    lines.extend(
        [
            "",
            "Execution Target",
            f"- target_status: `{report['execution_target'].get('target_status', '')}`",
            f"- target: `{report['execution_target'].get('target', '')}`",
            f"- blocked_reason: `{report['execution_target'].get('blocked_reason', '')}`",
            "",
            "Projected Pressure",
            f"- projected_files: `{report['projected_files']}`",
            f"- projected_bytes: `{report['projected_bytes']}`",
            f"- estimated_runtime_seconds: `{report['estimated_runtime_seconds']}`",
        ]
    )
    return "\n".join(lines)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
