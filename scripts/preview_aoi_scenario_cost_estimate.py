#!/usr/bin/env python3
"""Preview AOI scenario cost, output pressure, and execution suitability.

The helper stays in the pre-execution boundary. It consumes reviewed candidate
packages, expands their frozen source-zone / block-family contracts, and
projects output pressure with measured envelope helpers. It does not run
simulations, authorize scale-up, or submit anything to Balfrin.

It also exposes a bounded AOI cost-projection ladder for 2, 4, 8, 12, 50,
and 100-zone shapes so the companion report can separate measured, scratch-
local, projection-only, and no-go evidence without inventing new execution.
"""

from __future__ import annotations

import argparse
import json
import math
import tempfile
import sys
from functools import lru_cache
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
from scripts import estimate_large_scale_execution as LARGE_SCALE
from scripts import summarize_balfrin_scale_readiness_matrix as BALFRIN_SCALE
from scripts import summarize_bounded_validation_output_profile as OUTPUT_BUDGET
from scripts.lib import output_profile_policy as OUTPUT_PROFILE_POLICY


SCHEMA_VERSION = "aoi_scenario_preview_v1"
SELECTED_ZONE_SCHEMA_VERSION = "aoi_selected_zone_scenario_preview_v1"
COST_PROJECTION_SCHEMA_VERSION = "aoi_scenario_cost_projection_v1"
DEFAULT_REVIEW_PACKAGE = ROOT / "tests/fixtures/aoi_scenario_preview/tiny_review_package.yaml"
DEFAULT_TRAJECTORY_COUNT = None
DEFAULT_OUTPUT_ROOT = Path("/tmp/rust_rockfall/aoi_scenario_preview")
DEFAULT_SELECTED_ZONE_OUTPUT_ROOT = DEFAULT_OUTPUT_ROOT / "selected_zone_counts"
DEFAULT_SELECTED_ZONE_COUNTS = (2, 4, 8, 12)
DEFAULT_PROJECTION_ZONE_COUNTS = (2, 4, 8, 12, 50, 100)
DEFAULT_PLANNING_ZONE_COUNTS = (10, 50, 100)
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
PLANNED_PLAUSIBLE = "plausible"
PLANNED_BLOCKED = "blocked"
PLANNED_OUT_OF_REACH = "out_of_reach"


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
    parser.add_argument(
        "--selected-zone-counts",
        default="",
        help="Comma-separated selected-zone counts to preview from a single reviewed package. "
        "When set, the helper generates scratch-root scenario tables for each count.",
    )
    parser.add_argument(
        "--projection-zone-counts",
        default="",
        help="Comma-separated AOI zone counts to project with measured runtime, storage, and reducer pressure. "
        "When set, the helper emits the companion cost-projection report.",
    )
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_SELECTED_ZONE_OUTPUT_ROOT)
    args = parser.parse_args(argv)

    review_packages = args.review_package or [DEFAULT_REVIEW_PACKAGE]
    selected_zone_counts = parse_selected_zone_counts(args.selected_zone_counts) if args.selected_zone_counts else None
    projection_zone_counts = (
        parse_selected_zone_counts(args.projection_zone_counts) if args.projection_zone_counts else None
    )
    if selected_zone_counts is not None and projection_zone_counts is not None:
        print(
            "aoi scenario preview error: selected-zone and projection-zone modes are mutually exclusive",
            file=sys.stderr,
        )
        return 2

    try:
        output_profile_policy = OUTPUT_PROFILE_POLICY.classify_output_profile_policy(
            conditional_curve_export=args.conditional_curve_export,
            grid_csv_export=args.grid_csv_export,
            no_plots=args.no_plots,
            explicit_debug_override=args.explicit_debug_override,
            label="aoi_scenario_preview",
        )
        if projection_zone_counts is not None:
            report = build_aoi_cost_projection_report(
                review_package_paths=review_packages,
                trajectory_count=args.trajectory_count,
                projection_zone_counts=projection_zone_counts,
                output_profile_policy=output_profile_policy,
                output_root=args.output_root,
            )
        else:
            report = build_report(
                review_package_paths=review_packages,
                trajectory_count=args.trajectory_count,
                selected_zone_counts=selected_zone_counts,
                output_profile_policy=output_profile_policy,
                output_root=args.output_root,
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
    status = report.get("preview_status", report.get("projection_status", ""))
    return 0 if status == "ready" else 2


def build_report(
    *,
    review_package_paths: list[Path] | tuple[Path, ...],
    trajectory_count: int | None = DEFAULT_TRAJECTORY_COUNT,
    selected_zone_counts: list[int] | tuple[int, ...] | None = None,
    output_profile_policy: dict[str, Any] | None = None,
    output_root: Path | None = None,
) -> dict[str, Any]:
    if selected_zone_counts is not None:
        if len(review_package_paths) != 1:
            raise AoiScenarioPreviewError("selected-zone counts mode requires exactly one reviewed package")
        return build_selected_zone_pressure_report(
            review_package_path=review_package_paths[0],
            selected_zone_counts=selected_zone_counts,
            trajectory_count=trajectory_count,
            output_profile_policy=output_profile_policy,
            output_root=output_root,
        )

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
        "cardinality_pressure_summary": summary["cardinality_pressure_summary"],
        "rows": rows,
        "projected_files": projected_totals,
        "projected_bytes": projected_bytes,
        "estimated_runtime_seconds": projected_runtime_seconds,
        "budget_summary": budget_summary,
        "execution_target": target,
        "output_budget_assessment": build_output_budget_assessment(target),
    }
    return report


def build_aoi_cost_projection_report(
    *,
    review_package_paths: list[Path] | tuple[Path, ...],
    trajectory_count: int | None = DEFAULT_TRAJECTORY_COUNT,
    projection_zone_counts: list[int] | tuple[int, ...] | None = None,
    output_profile_policy: dict[str, Any] | None = None,
    output_root: Path | None = None,
) -> dict[str, Any]:
    profile_policy = output_profile_policy or default_output_profile_policy()
    if profile_policy.get("classification") == OUTPUT_PROFILE_POLICY.BLOCKED_UNSCALABLE_DEFAULT:
        return blocked_projection_report(
            review_package_paths=review_package_paths,
            projection_zone_counts=projection_zone_counts or DEFAULT_PROJECTION_ZONE_COUNTS,
            blocked_reason="unsupported output profile requires an explicit override",
            blocking_label=BLOCKED_UNSUPPORTED_PROFILE,
            output_profile_policy=profile_policy,
        )

    if not review_package_paths:
        return blocked_projection_report(
            review_package_paths=[],
            projection_zone_counts=projection_zone_counts or DEFAULT_PROJECTION_ZONE_COUNTS,
            blocked_reason="no reviewed candidate package was supplied",
            blocking_label=BLOCKED_MISSING_REVIEWED_CANDIDATES,
            output_profile_policy=profile_policy,
        )
    if len(review_package_paths) != 1:
        raise AoiScenarioPreviewError("AOI cost projection mode requires exactly one reviewed package")

    package_path = Path(review_package_paths[0])
    if not package_path.exists():
        return blocked_projection_report(
            review_package_paths=[package_path],
            projection_zone_counts=projection_zone_counts or DEFAULT_PROJECTION_ZONE_COUNTS,
            blocked_reason=f"missing reviewed candidate package: {display_path(package_path)}",
            blocking_label=BLOCKED_MISSING_REVIEWED_CANDIDATES,
            output_profile_policy=profile_policy,
        )

    review_package = load_review_package(package_path)
    reviewed_candidates = list((review_package.get("review_application") or {}).get("accepted_candidate_ids") or [])
    if review_package.get("review_package_status") != "review_applied" or not reviewed_candidates:
        return blocked_projection_report(
            review_package_paths=[package_path],
            projection_zone_counts=projection_zone_counts or DEFAULT_PROJECTION_ZONE_COUNTS,
            blocked_reason="missing reviewed candidates in reviewed package",
            blocking_label=BLOCKED_MISSING_REVIEWED_CANDIDATES,
            output_profile_policy=profile_policy,
        )

    preview_count = trajectory_count if trajectory_count is not None else infer_trajectory_count(package_path)
    if preview_count is None or preview_count <= 0:
        return blocked_projection_report(
            review_package_paths=[package_path],
            projection_zone_counts=projection_zone_counts or DEFAULT_PROJECTION_ZONE_COUNTS,
            blocked_reason="trajectory budget is missing or invalid",
            blocking_label=BLOCKED_UNKNOWN_TRAJECTORY_BUDGET,
            output_profile_policy=profile_policy,
        )

    requested_counts = parse_selected_zone_counts(projection_zone_counts or DEFAULT_PROJECTION_ZONE_COUNTS)
    if not requested_counts:
        return blocked_projection_report(
            review_package_paths=[package_path],
            projection_zone_counts=requested_counts,
            blocked_reason="no projection-zone counts were supplied",
            blocking_label=BLOCKED_MISSING_REVIEWED_CANDIDATES,
            output_profile_policy=profile_policy,
        )

    reference_report = build_projection_reference_report(
        review_package_path=package_path,
        trajectory_count=preview_count,
    )
    classification_surface = load_balfrin_scale_classification_surface()
    projection_rows = build_aoi_cost_projection_rows(
        projection_zone_counts=requested_counts,
        trajectory_count=preview_count,
        reference_report=reference_report,
    )
    summary = summarize_aoi_cost_projection_rows(projection_rows)
    classification_summary = {
        **summary,
        "measured_tiers": list(classification_surface.get("measured_tiers", [])),
        "scratch_local_tiers": list(classification_surface.get("scratch_local_tiers", [])),
        "projection_only_tiers": list(classification_surface.get("projection_only_tiers", [])),
        "no_go_tiers": list(classification_surface.get("no_go_tiers", [])),
    }
    largest_report = projection_rows[-1]
    return {
        "schema_version": COST_PROJECTION_SCHEMA_VERSION,
        "preview_mode": "aoi_cost_projection_counts",
        "projection_status": "ready",
        "blocked_reason": "",
        "read_only": True,
        "scale_up_authorized": False,
        "operational_claims_allowed": False,
        "review_package_count": 1,
        "review_package_path": display_path(package_path),
        "reviewed_candidate_pool_count": reference_report["reviewed_candidate_pool_count"],
        "trajectory_count": preview_count,
        "projection_zone_counts": requested_counts,
        "projection_zone_count_reports": projection_rows,
        "largest_projection_zone_count": largest_report["projection_zone_count"],
        "largest_projection_zone_report": largest_report,
        "output_profile_policy": profile_policy,
        "output_profile_choice": profile_policy.get("classification", "unknown"),
        "blocking_labels": [],
        "classification_surface": classification_surface,
        "projection_classification_summary": classification_summary,
        "planning_case_pressure_thresholds": build_planning_case_pressure_thresholds(
            projection_rows=build_aoi_cost_projection_rows(
                projection_zone_counts=DEFAULT_PLANNING_ZONE_COUNTS,
                trajectory_count=preview_count,
                reference_report=reference_report,
            )
        ),
        "measurement_basis": reference_report["measurement_basis"],
        "reference_block_family_count": reference_report["block_family_count"],
        "reference_block_family_ids": reference_report["block_family_ids"],
        "source_zone_count": largest_report["projection_zone_count"],
        "scenario_family_count": largest_report["scenario_cardinality"]["scenario_family_count"],
        "scenario_cardinality": largest_report["scenario_cardinality"],
        "execution_cardinality": largest_report["execution_cardinality"],
        "projected_files": largest_report["projected_files"],
        "projected_bytes": largest_report["projected_bytes"],
        "estimated_runtime_seconds": largest_report["estimated_runtime_seconds"],
        "budget_summary": OUTPUT_BUDGET.build_summary(),
        "execution_target": largest_report["execution_target"],
        "output_budget_assessment": largest_report["output_budget_assessment"],
        "projection_assumptions": [
            "The reviewed package is a reference for scenario-table family structure only; no synthetic candidate pool is invented beyond the supplied counts.",
            "Trajectory count stays fixed at the reviewed package budget unless the caller overrides it.",
            "Runtime, storage, and file bands come from measured coefficients; they are not new Balfrin execution measurements.",
            "Reducer pressure is summarized from the measured single-job envelope helper and the current scaling frontier labels.",
        ],
        "projection_uncertainty": {
            "runtime_seconds": largest_report["uncertainty_band"]["runtime_seconds"],
            "storage_bytes": largest_report["uncertainty_band"]["storage_bytes"],
            "file_count": largest_report["uncertainty_band"]["file_count"],
            "memory_peak_mb": largest_report["uncertainty_band"]["memory_peak_mb"],
            "notes": [
                "The low/nominal/high bands are inherited from measured coefficients and are projection-only for every requested zone count.",
                "No additional field or Balfrin postproc measurement is claimed for the 50-zone or 100-zone rows.",
            ],
        },
    }


def build_planning_case_pressure_thresholds(*, projection_rows: list[dict[str, Any]]) -> dict[str, Any]:
    planning_thresholds = []
    for row in projection_rows:
        planning_thresholds.append(
            {
                "planning_zone_count": row["projection_zone_count"],
                "scenario_cardinality": row["scenario_cardinality"],
                "projected_files": row["projected_files"],
                "projected_bytes": row["projected_bytes"],
                "estimated_runtime_seconds": row["estimated_runtime_seconds"],
                "reducer_pressure": row["reducer_pressure"],
                "blocking_labels": list(row["no_go_labels"]),
                "blocked_reason": row["blocked_reason"],
                "projection_status": row["projection_status"],
                "suitability_classification": row["suitability_classification"],
            }
        )
    return {
        "schema_version": "aoi_planning_case_pressure_thresholds_v1",
        "planning_zone_counts": list(DEFAULT_PLANNING_ZONE_COUNTS),
        "planning_case_thresholds": planning_thresholds,
        "largest_planning_case": planning_thresholds[-1] if planning_thresholds else {},
    }


def build_projection_reference_report(*, review_package_path: Path, trajectory_count: int) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(dir="/tmp", prefix="aoi_cost_projection_reference_") as tmpdir:
        output_root = Path(tmpdir)
        freezer_report = FREEZER.build_freezer_report(
            review_package_path=review_package_path,
            accepted_candidate_ids=None,
            output_root=output_root,
            trajectory_count=trajectory_count,
            seed=FREEZER.DEFAULT_FREEZER_SEED,
        )

    classification_surface = load_balfrin_scale_classification_surface()
    return {
        "reviewed_candidate_pool_count": int(freezer_report.get("accepted_candidate_count") or 0),
        "block_family_count": len(freezer_report.get("block_family_ids", []) or []),
        "block_family_ids": list(freezer_report.get("block_family_ids", []) or []),
        "measurement_basis": {
            "measured_tiers": list(classification_surface.get("measured_tiers", [])),
            "scratch_local_tiers": list(classification_surface.get("scratch_local_tiers", [])),
            "projection_only_tiers": list(classification_surface.get("projection_only_tiers", [])),
            "no_go_tiers": list(classification_surface.get("no_go_tiers", [])),
            "summary": classification_surface.get("summary", ""),
            "evidence_label_definitions": dict(classification_surface.get("evidence_label_definitions", {})),
        },
    }


def build_aoi_cost_projection_rows(
    *,
    projection_zone_counts: list[int] | tuple[int, ...],
    trajectory_count: int,
    reference_report: dict[str, Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    coefficients = ENVELOPE.load_measured_coefficients()
    block_family_count = max(1, int(reference_report.get("block_family_count") or 0))
    for zone_count in projection_zone_counts:
        large_scale_estimate = LARGE_SCALE.estimate(
            LARGE_SCALE.EstimateInputs(
                release_zone_count=zone_count,
                ensemble_size=1,
                trajectory_count=trajectory_count,
                grid_rows=LARGE_SCALE.ANCHOR["grid_rows"],
                grid_cols=LARGE_SCALE.ANCHOR["grid_cols"],
                trajectory_workers=2,
                reducer_workers=2,
                trajectory_chunks=None,
                reducer_chunks=None,
                threshold_count=2,
                profile="scalable_conditional",
                export_geotiff=True,
            )
        )
        evidence_label = classify_projection_evidence(zone_count)
        suitability = classify_projection_suitability(zone_count)
        total_units = zone_count * trajectory_count
        job_count = max(1, math.ceil(total_units / coefficients.measured_units_per_job))
        no_go_labels = []
        if zone_count > coefficients.measured_release_zone_count:
            no_go_labels.append("release_zone_count_exceeds_measured_support")
        if job_count > 1:
            no_go_labels.append("per_aoi_job_count_exceeds_measured_single_job_support")
        projection_status = "measured_within_support" if not no_go_labels else "no_go_extrapolated_beyond_measured_evidence"
        blocked_reason = "none" if not no_go_labels else "extrapolation beyond measured evidence: " + ", ".join(no_go_labels)
        runtime_seconds = ENVELOPE.build_scalar_band(
            total_units,
            coefficients.runtime_seconds_per_unit_low,
            coefficients.runtime_seconds_per_unit_nominal,
            coefficients.runtime_seconds_per_unit_high,
            precision=3,
        )
        projected_files = ENVELOPE.build_integer_band(
            total_units,
            coefficients.file_count_per_unit_low,
            coefficients.file_count_per_unit_nominal,
            coefficients.file_count_per_unit_high,
        )
        projected_bytes = ENVELOPE.build_integer_band(
            total_units,
            coefficients.storage_bytes_per_unit_low,
            coefficients.storage_bytes_per_unit_nominal,
            coefficients.storage_bytes_per_unit_high,
        )
        memory_peak_mb = ENVELOPE.build_absolute_band(
            coefficients.memory_peak_mb_low,
            coefficients.memory_peak_mb_nominal,
            coefficients.memory_peak_mb_high,
            precision=3,
        )
        scenario_cardinality = build_scenario_cardinality(
            source_zone_count=zone_count,
            scenario_family_count=block_family_count,
            row_count=zone_count * block_family_count,
        )
        rows.append(
            {
                "projection_zone_count": zone_count,
                "evidence_label": evidence_label,
                "suitability_classification": suitability,
                "projection_status": projection_status,
                "measurement_status": "measured_existing_artifacts",
                "scenario_cardinality": scenario_cardinality,
                "execution_cardinality": {
                    "aoi_count": 1,
                    "release_zone_count": zone_count,
                    "trajectory_count": trajectory_count,
                    "total_units": total_units,
                },
                "job_count": job_count,
                "jobs_per_aoi": job_count,
                "runtime_seconds": runtime_seconds,
                "storage_bytes": projected_bytes,
                "file_count": projected_files,
                "memory_peak_mb": memory_peak_mb,
                "no_go_labels": no_go_labels,
                "blocked_reason": blocked_reason,
                "planning_labels": {
                    "no_go": "no_go_extrapolated_beyond_measured_evidence" if no_go_labels else "no_go_not_triggered",
                    "defer": "defer_scale_up_authorized_false",
                    "allowed_next_probe": "allowed_next_probe_measured_existing_artifacts",
                },
                "reducer_pressure": {
                    "job_count": job_count,
                    "jobs_per_aoi": job_count,
                    "trajectory_chunks": large_scale_estimate.trajectory_chunks,
                    "reducer_chunks": large_scale_estimate.reducer_chunks,
                    "nominal_output_file_count": large_scale_estimate.total_output_file_count,
                    "nominal_output_bytes": large_scale_estimate.output_bytes,
                    "chunk_counts": large_scale_estimate.chunk_counts,
                },
                "uncertainty_band": {
                    "runtime_seconds": runtime_seconds,
                    "storage_bytes": projected_bytes,
                    "file_count": projected_files,
                    "memory_peak_mb": memory_peak_mb,
                },
                "output_budget_assessment": {
                    "local": {"status": suitability},
                    "balfrin": {"status": projection_status},
                    "budget_exceeded": bool(no_go_labels),
                },
                "execution_target": {
                    "target": suitability,
                    "target_status": suitability,
                    "blocked_reason": blocked_reason,
                },
                "projected_files": projected_files,
                "projected_bytes": projected_bytes,
                "estimated_runtime_seconds": runtime_seconds,
            }
        )
    return rows


def summarize_aoi_cost_projection_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_label: dict[str, list[int]] = {
        "measured": [],
        "scratch_local": [],
        "projection_only": [],
        "no_go": [],
    }
    by_suitability: dict[str, list[int]] = {
        PLANNED_PLAUSIBLE: [],
        PLANNED_BLOCKED: [],
        PLANNED_OUT_OF_REACH: [],
    }
    for row in rows:
        zone_count = int(row.get("projection_zone_count") or 0)
        label = str(row.get("evidence_label") or "")
        if label in by_label:
            by_label[label].append(zone_count)
        suitability = str(row.get("suitability_classification") or "")
        if suitability in by_suitability:
            by_suitability[suitability].append(zone_count)
    return {
        "measured": by_label["measured"],
        "scratch_local": by_label["scratch_local"],
        "projection_only": by_label["projection_only"],
        "no_go": by_label["no_go"],
        "plausible": by_suitability[PLANNED_PLAUSIBLE],
        "blocked": by_suitability[PLANNED_BLOCKED],
        "out_of_reach": by_suitability[PLANNED_OUT_OF_REACH],
    }


def classify_projection_evidence(zone_count: int) -> str:
    if zone_count <= 12:
        return "scratch_local"
    if zone_count <= 50:
        return "projection_only"
    return "no_go"


def classify_projection_suitability(zone_count: int) -> str:
    if zone_count <= 4:
        return PLANNED_PLAUSIBLE
    if zone_count <= 50:
        return PLANNED_BLOCKED
    return PLANNED_OUT_OF_REACH


@lru_cache(maxsize=1)
def load_balfrin_scale_classification_surface() -> dict[str, Any]:
    report = BALFRIN_SCALE.build_report()
    return {
        "measured_tiers": list(report.get("measured_tiers", [])),
        "scratch_local_tiers": list(report.get("scratch_local_tiers", [])),
        "projection_only_tiers": list(report.get("projection_only_tiers", [])),
        "no_go_tiers": list(report.get("no_go_tiers", [])),
        "summary": str(report.get("summary") or ""),
        "next_recommended_scaling_task": str(report.get("next_recommended_scaling_task") or ""),
        "evidence_label_definitions": dict(report.get("evidence_label_definitions") or {}),
    }


def blocked_projection_report(
    *,
    review_package_paths: list[Path],
    projection_zone_counts: list[int] | tuple[int, ...],
    blocked_reason: str,
    blocking_label: str,
    output_profile_policy: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": COST_PROJECTION_SCHEMA_VERSION,
        "preview_mode": "aoi_cost_projection_counts",
        "projection_status": blocking_label,
        "blocked_reason": blocked_reason,
        "read_only": True,
        "scale_up_authorized": False,
        "operational_claims_allowed": False,
        "review_package_count": len(review_package_paths),
        "review_package_path": display_path(Path(review_package_paths[0])) if review_package_paths else "",
        "reviewed_candidate_pool_count": 0,
        "trajectory_count": None,
        "projection_zone_counts": list(projection_zone_counts),
        "projection_zone_count_reports": [],
        "largest_projection_zone_count": 0,
        "largest_projection_zone_report": {},
        "output_profile_policy": output_profile_policy,
        "output_profile_choice": output_profile_policy.get("classification", "unknown"),
        "blocking_labels": [blocking_label],
        "classification_surface": load_balfrin_scale_classification_surface(),
        "projection_classification_summary": {
            "measured": [],
            "scratch_local": [],
            "projection_only": [],
            "no_go": [],
            "plausible": [],
            "blocked": [],
            "out_of_reach": [],
        },
        "measurement_basis": {},
        "reference_block_family_count": 0,
        "reference_block_family_ids": [],
        "source_zone_count": 0,
        "scenario_family_count": 0,
        "scenario_cardinality": {
            "source_zone_count": 0,
            "scenario_family_count": 0,
            "row_count": 0,
        },
        "execution_cardinality": {
            "aoi_count": 0,
            "release_zone_count": 0,
            "trajectory_count": 0,
            "total_units": 0,
        },
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
        "projection_assumptions": [
            "No synthetic candidate pool is invented beyond the supplied zone counts.",
            "Runtime, storage, and file bands are projection-only and are inherited from measured coefficients.",
            "Reducer pressure is summarized from the current measured single-job envelope helper.",
        ],
        "projection_uncertainty": {
            "runtime_seconds": {"low": None, "nominal": None, "high": None},
            "storage_bytes": {"low": None, "nominal": None, "high": None},
            "file_count": {"low": None, "nominal": None, "high": None},
            "memory_peak_mb": {"low": None, "nominal": None, "high": None},
            "notes": [
                "The projection could not be completed because a required reviewed candidate package or trajectory budget was missing.",
            ],
        },
    }


def build_projection_reference_report(*, review_package_path: Path, trajectory_count: int) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(dir="/tmp", prefix="aoi_cost_projection_reference_") as tmpdir:
        output_root = Path(tmpdir)
        freezer_report = FREEZER.build_freezer_report(
            review_package_path=review_package_path,
            accepted_candidate_ids=None,
            output_root=output_root,
            trajectory_count=trajectory_count,
            seed=FREEZER.DEFAULT_FREEZER_SEED,
        )

    classification_surface = load_balfrin_scale_classification_surface()
    return {
        "reviewed_candidate_pool_count": int(freezer_report.get("accepted_candidate_count") or 0),
        "block_family_count": len(freezer_report.get("block_family_ids", []) or []),
        "block_family_ids": list(freezer_report.get("block_family_ids", []) or []),
        "measurement_basis": {
            "measured_tiers": list(classification_surface.get("measured_tiers", [])),
            "scratch_local_tiers": list(classification_surface.get("scratch_local_tiers", [])),
            "projection_only_tiers": list(classification_surface.get("projection_only_tiers", [])),
            "no_go_tiers": list(classification_surface.get("no_go_tiers", [])),
            "summary": classification_surface.get("summary", ""),
            "next_recommended_scaling_task": classification_surface.get("next_recommended_scaling_task", ""),
            "evidence_label_definitions": dict(classification_surface.get("evidence_label_definitions", {})),
        },
    }


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
                    "expected_trajectory_count": row_units,
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
    block_family_ids = sorted({row.get("block_family_id", "") for row in rows if row.get("block_family_id")})
    scenario_family_ids = sorted({row.get("scenario_family_id", "") for row in rows if row.get("scenario_family_id")})
    source_zone_count = len(source_zone_ids)
    block_family_count = len(block_family_ids)
    scenario_family_count = len(scenario_family_ids)
    scenario_cardinality = build_scenario_cardinality(
        source_zone_count=source_zone_count,
        scenario_family_count=scenario_family_count,
        row_count=len(rows),
    )
    blocking_labels: list[str] = []
    cardinality_pressure_summary = build_cardinality_pressure_summary(
        scenario_count=len(rows),
        expected_trajectory_count=sum(int(row.get("expected_trajectory_count") or 0) for row in rows),
        trajectory_count=max((int(row.get("trajectory_count") or 0) for row in rows), default=0),
        source_zone_count=source_zone_count,
        block_family_count=block_family_count,
        scenario_family_count=scenario_family_count,
        reviewed_candidate_count=sum(int(row.get("reviewed_candidate_count") or 0) for row in rows),
    )
    return {
        "source_zone_count": source_zone_count,
        "scenario_family_count": scenario_family_count,
        "scenario_cardinality": scenario_cardinality,
        "cardinality_pressure_summary": cardinality_pressure_summary,
        "blocking_labels": blocking_labels,
    }


def build_cardinality_pressure_summary(
    *,
    scenario_count: int,
    expected_trajectory_count: int,
    trajectory_count: int,
    source_zone_count: int,
    block_family_count: int,
    scenario_family_count: int,
    reviewed_candidate_count: int,
) -> dict[str, Any]:
    factors = {
        "source_zone_count": int(source_zone_count),
        "block_family_count": int(block_family_count),
        "scenario_family_count": int(scenario_family_count),
        "reviewed_candidate_count": int(reviewed_candidate_count),
        "trajectory_count": int(trajectory_count),
    }
    if source_zone_count > 1:
        first_driver = "source_zone_count"
    elif block_family_count > 1:
        first_driver = "block_family_count"
    elif scenario_family_count > 1:
        first_driver = "scenario_family_count"
    elif reviewed_candidate_count > 1:
        first_driver = "reviewed_candidate_count"
    elif trajectory_count > 1:
        first_driver = "trajectory_count"
    else:
        first_driver = "single_scenario_baseline"
    return {
        "summary_status": "ready",
        "scenario_count": int(scenario_count),
        "expected_trajectory_count": int(expected_trajectory_count),
        "trajectory_count_per_candidate": int(trajectory_count),
        "cardinality_factors": factors,
        "first_cardinality_growth_driver": first_driver,
        "recommended_pressure_response": recommended_cardinality_pressure_response(first_driver),
        "claim_boundary": "local pre-execution estimate only; no simulation, scale-up authorization, or scientific claim upgrade",
    }


def recommended_cardinality_pressure_response(first_driver: str) -> str:
    responses = {
        "source_zone_count": "review whether multiple source zones are all needed before expanding execution",
        "scenario_family_count": "inspect block/scenario family policy before adding more candidates",
        "block_family_count": "inspect block/scenario family policy before adding more candidates",
        "reviewed_candidate_count": "reduce or stratify reviewed candidates before larger execution planning",
        "trajectory_count": "keep trajectory budget explicit before execution planning",
        "single_scenario_baseline": "use as the local baseline before adding more source zones or scenario families",
    }
    return responses.get(first_driver, responses["single_scenario_baseline"])


def build_scenario_cardinality(
    *,
    source_zone_count: int,
    scenario_family_count: int,
    row_count: int,
) -> dict[str, int]:
    return {
        "source_zone_count": int(source_zone_count),
        "scenario_family_count": int(scenario_family_count),
        "row_count": int(row_count),
    }


def summarize_scenario_table_rows(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    scenario_family_counts: dict[str, int] = {}
    release_zone_counts: dict[str, int] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        block_family_id = str(row.get("block_family_id") or "")
        release_zone_id = str(row.get("candidate_release_zone_id") or row.get("source_zone_id") or "")
        if block_family_id:
            scenario_family_counts[block_family_id] = scenario_family_counts.get(block_family_id, 0) + 1
        if release_zone_id:
            release_zone_counts[release_zone_id] = release_zone_counts.get(release_zone_id, 0) + 1
    return {
        "scenario_family_cardinality": [
            {"scenario_family_id": family_id, "row_count": count}
            for family_id, count in sorted(scenario_family_counts.items())
        ],
        "release_zone_cardinality": [
            {"release_zone_id": release_zone_id, "row_count": count}
            for release_zone_id, count in sorted(release_zone_counts.items())
        ],
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


def build_output_pressure_labels(execution_target: dict[str, Any]) -> dict[str, Any]:
    return {
        "target": execution_target["target"],
        "target_status": execution_target["target_status"],
        "local": execution_target["local_assessment"]["status"],
        "balfrin": execution_target["balfrin_assessment"]["status"],
        "budget_exceeded": execution_target["target_status"] == BLOCKED_TARGET,
    }


def build_output_budget_assessment(execution_target: dict[str, Any]) -> dict[str, Any]:
    return {
        "local": execution_target["local_assessment"],
        "balfrin": execution_target["balfrin_assessment"],
        "budget_exceeded": execution_target["target_status"] == BLOCKED_TARGET,
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
        "conditional_weight_summary": {
            "conditional_weight_total": 0.0,
            "conditional_weight_semantics": "conditional_sampling_only",
            "block_family_count": 0,
            "block_family_ids": [],
        },
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


def build_selected_zone_pressure_report(
    *,
    review_package_path: Path,
    selected_zone_counts: list[int] | tuple[int, ...],
    trajectory_count: int | None = DEFAULT_TRAJECTORY_COUNT,
    output_profile_policy: dict[str, Any] | None = None,
    output_root: Path | None = None,
) -> dict[str, Any]:
    profile_policy = output_profile_policy or default_output_profile_policy()
    if profile_policy.get("classification") == OUTPUT_PROFILE_POLICY.BLOCKED_UNSCALABLE_DEFAULT:
        return blocked_selected_zone_report(
            review_package_path=review_package_path,
            selected_zone_counts=selected_zone_counts,
            blocked_reason="unsupported output profile requires an explicit override",
            blocking_label=BLOCKED_UNSUPPORTED_PROFILE,
            output_profile_policy=profile_policy,
        )

    package_path = Path(review_package_path)
    if not package_path.exists():
        return blocked_selected_zone_report(
            review_package_path=package_path,
            selected_zone_counts=selected_zone_counts,
            blocked_reason=f"missing reviewed candidate package: {display_path(package_path)}",
            blocking_label=BLOCKED_MISSING_REVIEWED_CANDIDATES,
            output_profile_policy=profile_policy,
        )

    review_package = load_review_package(package_path)
    reviewed_candidates = list((review_package.get("review_application") or {}).get("accepted_candidate_ids") or [])
    if review_package.get("review_package_status") != "review_applied" or not reviewed_candidates:
        return blocked_selected_zone_report(
            review_package_path=package_path,
            selected_zone_counts=selected_zone_counts,
            blocked_reason="missing reviewed candidates in reviewed package",
            blocking_label=BLOCKED_MISSING_REVIEWED_CANDIDATES,
            output_profile_policy=profile_policy,
        )

    requested_counts = parse_selected_zone_counts(selected_zone_counts)
    if not requested_counts:
        return blocked_selected_zone_report(
            review_package_path=package_path,
            selected_zone_counts=requested_counts,
            blocked_reason="no selected-zone counts were supplied",
            blocking_label=BLOCKED_MISSING_REVIEWED_CANDIDATES,
            output_profile_policy=profile_policy,
        )

    preview_count = trajectory_count if trajectory_count is not None else infer_trajectory_count(package_path)
    if preview_count is None or preview_count <= 0:
        return blocked_selected_zone_report(
            review_package_path=package_path,
            selected_zone_counts=requested_counts,
            blocked_reason="trajectory budget is missing or invalid",
            blocking_label=BLOCKED_UNKNOWN_TRAJECTORY_BUDGET,
            output_profile_policy=profile_policy,
        )

    missing_counts = [count for count in requested_counts if count > len(reviewed_candidates)]
    if missing_counts:
        return blocked_selected_zone_report(
            review_package_path=package_path,
            selected_zone_counts=requested_counts,
            blocked_reason=(
                "selected-zone count exceeds reviewed candidate pool: "
                + ", ".join(str(count) for count in missing_counts)
            ),
            blocking_label=BLOCKED_MISSING_REVIEWED_CANDIDATES,
            output_profile_policy=profile_policy,
        )

    selected_reports: list[dict[str, Any]] = []
    base_output_root = Path(output_root) if output_root is not None else DEFAULT_SELECTED_ZONE_OUTPUT_ROOT
    for count in requested_counts:
        selected_ids = reviewed_candidates[:count]
        try:
            freezer_report = FREEZER.build_freezer_report(
                review_package_path=package_path,
                accepted_candidate_ids=selected_ids,
                output_root=base_output_root / f"selected_{count:02d}",
                trajectory_count=preview_count,
                seed=FREEZER.DEFAULT_FREEZER_SEED + count,
            )
        except FREEZER.CandidateSourceZoneFreezerError as exc:
            return blocked_selected_zone_report(
                review_package_path=package_path,
                selected_zone_counts=requested_counts,
                blocked_reason=f"missing reviewed candidates: {exc}",
                blocking_label=BLOCKED_MISSING_REVIEWED_CANDIDATES,
                output_profile_policy=profile_policy,
            )

        block_family_count = len(freezer_report.get("block_family_ids", []))
        row_units = max(1, freezer_report["accepted_candidate_count"]) * preview_count * max(1, block_family_count)
        pressure = estimate_output_pressure(row_units)
        output_paths = {
            name: Path(path)
            for name, path in freezer_report.get("output_paths", {}).items()
        }
        csv_path = output_paths.get("scenario_table")
        manifest_path = output_paths.get("manifest")
        if csv_path is None or manifest_path is None:
            return blocked_selected_zone_report(
                review_package_path=package_path,
                selected_zone_counts=requested_counts,
                blocked_reason="selected-zone scratch outputs are incomplete",
                blocking_label=BLOCKED_MISSING_REVIEWED_CANDIDATES,
                output_profile_policy=profile_policy,
            )
        csv_bytes = csv_path.stat().st_size
        manifest_bytes = manifest_path.stat().st_size
        total_bytes = 0
        for output_path in output_paths.values():
            total_bytes += output_path.stat().st_size
        conditional_weight_summary = {
            "conditional_weight_total": freezer_report.get("conditional_weight_total", 0.0),
            "conditional_weight_semantics": freezer_report.get("conditional_weight_semantics", "conditional_sampling_only"),
            "block_family_count": block_family_count,
            "block_family_ids": list(freezer_report.get("block_family_ids", [])),
        }
        execution_target = recommend_execution_target(
            profile_policy=profile_policy,
            projected_files=pressure["projected_files"],
            projected_bytes=pressure["projected_bytes"],
            budget_summary=OUTPUT_BUDGET.build_summary(),
        )
        selected_reports.append(
            {
                "selected_zone_count": count,
                "selected_candidate_ids": selected_ids,
                "reviewed_candidate_pool_count": len(reviewed_candidates),
                "trajectory_count": preview_count,
                "expected_trajectory_count": freezer_report["scenario_row_count"] * preview_count,
                "seed": freezer_report["seed"],
                "seed_policy": freezer_report["seed_policy"],
                "block_family_count": block_family_count,
                "block_family_ids": list(freezer_report.get("block_family_ids", [])),
                "conditional_weight_summary": conditional_weight_summary,
                "candidate_release_zone_record_count": freezer_report["accepted_candidate_count"],
                "scenario_cardinality": build_scenario_cardinality(
                    source_zone_count=freezer_report["accepted_candidate_count"],
                    scenario_family_count=block_family_count,
                    row_count=freezer_report["scenario_row_count"],
                ),
                "scenario_row_count": freezer_report["scenario_row_count"],
                "storage_measurements": {
                    "csv_bytes": csv_bytes,
                    "manifest_bytes": manifest_bytes,
                    "total_bytes": total_bytes,
                },
                "manifest_bytes": manifest_bytes,
                "csv_bytes": csv_bytes,
                "total_bytes": total_bytes,
                "projected_files": pressure["projected_files"],
                "projected_bytes": pressure["projected_bytes"],
                "estimated_runtime_seconds": pressure["estimated_runtime_seconds"],
                "output_root": display_path(base_output_root / f"selected_{count:02d}"),
                "output_paths": freezer_report["output_paths"],
                "expected_output_file_count": len(freezer_report["output_paths"]),
                "execution_target": execution_target,
                "output_budget_assessment": build_output_budget_assessment(execution_target),
            }
        )

    largest_report = selected_reports[-1]
    cardinality_pressure_summary = build_cardinality_pressure_summary(
        scenario_count=largest_report["scenario_row_count"],
        expected_trajectory_count=largest_report["expected_trajectory_count"],
        trajectory_count=preview_count,
        source_zone_count=largest_report["scenario_cardinality"]["source_zone_count"],
        block_family_count=largest_report["block_family_count"],
        scenario_family_count=largest_report["scenario_cardinality"]["scenario_family_count"],
        reviewed_candidate_count=largest_report["selected_zone_count"],
    )
    return {
        "schema_version": SELECTED_ZONE_SCHEMA_VERSION,
        "preview_mode": "selected_zone_counts",
        "preview_status": "ready",
        "blocked_reason": "",
        "read_only": True,
        "scale_up_authorized": False,
        "operational_claims_allowed": False,
        "review_package_count": 1,
        "review_package_path": display_path(package_path),
        "reviewed_candidate_pool_count": len(reviewed_candidates),
        "trajectory_count": preview_count,
        "selected_zone_counts": requested_counts,
        "selected_zone_count_reports": selected_reports,
        "largest_selected_zone_count": largest_report["selected_zone_count"],
        "largest_selected_zone_report": largest_report,
        "output_profile_policy": profile_policy,
        "output_profile_choice": profile_policy.get("classification", "unknown"),
        "blocking_labels": [],
        "conditional_weight_summary": largest_report["conditional_weight_summary"],
        "source_zone_count": largest_report["scenario_cardinality"]["source_zone_count"],
        "scenario_family_count": largest_report["scenario_cardinality"]["scenario_family_count"],
        "scenario_cardinality": largest_report["scenario_cardinality"],
        "cardinality_pressure_summary": cardinality_pressure_summary,
        "rows": [],
        "projected_files": largest_report["projected_files"],
        "projected_bytes": largest_report["projected_bytes"],
        "estimated_runtime_seconds": largest_report["estimated_runtime_seconds"],
        "budget_summary": OUTPUT_BUDGET.build_summary(),
        "execution_target": largest_report["execution_target"],
        "output_budget_assessment": largest_report["output_budget_assessment"],
    }


def blocked_selected_zone_report(
    *,
    review_package_path: Path,
    selected_zone_counts: list[int] | tuple[int, ...],
    blocked_reason: str,
    blocking_label: str,
    output_profile_policy: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": SELECTED_ZONE_SCHEMA_VERSION,
        "preview_mode": "selected_zone_counts",
        "preview_status": blocking_label,
        "blocked_reason": blocked_reason,
        "read_only": True,
        "scale_up_authorized": False,
        "operational_claims_allowed": False,
        "review_package_count": 1,
        "review_package_path": display_path(Path(review_package_path)),
        "reviewed_candidate_pool_count": 0,
        "trajectory_count": None,
        "selected_zone_counts": list(selected_zone_counts),
        "selected_zone_count_reports": [],
        "largest_selected_zone_count": 0,
        "largest_selected_zone_report": {},
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
    if report.get("preview_mode") == "selected_zone_counts":
        lines = [
            "AOI Selected-Zone Scenario Preview",
            "",
            f"- schema_version: `{report['schema_version']}`",
            f"- preview_status: `{report['preview_status']}`",
            f"- blocked_reason: `{report['blocked_reason']}`",
            f"- output_profile_choice: `{report['output_profile_choice']}`",
            f"- review_package_count: `{report['review_package_count']}`",
            f"- reviewed_candidate_pool_count: `{report['reviewed_candidate_pool_count']}`",
            f"- trajectory_count: `{report['trajectory_count']}`",
            f"- selected_zone_counts: `{report['selected_zone_counts']}`",
            f"- cardinality_pressure_summary: `{report.get('cardinality_pressure_summary', {})}`",
            "",
            "Selected Zone Counts",
        ]
        for row in report.get("selected_zone_count_reports", []):
            lines.append(f"- selected_zone_count: `{row.get('selected_zone_count', '')}`")
            lines.append(f"  selected_candidate_ids: `{row.get('selected_candidate_ids', [])}`")
            lines.append(f"  block_family_ids: `{row.get('block_family_ids', [])}`")
            lines.append(f"  conditional_weight_summary: `{row.get('conditional_weight_summary', {})}`")
            lines.append(f"  scenario_cardinality: `{row.get('scenario_cardinality', {})}`")
            lines.append(f"  seed_policy: `{row.get('seed_policy', '')}`")
            lines.append(f"  seed: `{row.get('seed', '')}`")
            lines.append(f"  csv_bytes: `{row.get('csv_bytes', '')}`")
            lines.append(f"  manifest_bytes: `{row.get('manifest_bytes', '')}`")
            lines.append(f"  total_bytes: `{row.get('total_bytes', '')}`")
            lines.append(f"  output_root: `{row.get('output_root', '')}`")
            lines.append(f"  projected_files: `{row.get('projected_files', {})}`")
            lines.append(f"  projected_bytes: `{row.get('projected_bytes', {})}`")
            lines.append(f"  estimated_runtime_seconds: `{row.get('estimated_runtime_seconds', {})}`")
        lines.extend(
            [
                "",
                "Largest Selected Zone Count",
                f"- selected_zone_count: `{report['largest_selected_zone_count']}`",
                f"- conditional_weight_summary: `{report.get('conditional_weight_summary', {})}`",
                f"- execution_target: `{report['execution_target'].get('target', '')}`",
                f"- projected_files: `{report['projected_files']}`",
                f"- projected_bytes: `{report['projected_bytes']}`",
                f"- estimated_runtime_seconds: `{report['estimated_runtime_seconds']}`",
            ]
        )
        return "\n".join(lines)

    if report.get("preview_mode") == "aoi_cost_projection_counts":
        lines = [
            "AOI Cost Projection Preview",
            "",
            f"- schema_version: `{report['schema_version']}`",
            f"- projection_status: `{report['projection_status']}`",
            f"- blocked_reason: `{report['blocked_reason']}`",
            f"- output_profile_choice: `{report['output_profile_choice']}`",
            f"- review_package_count: `{report['review_package_count']}`",
            f"- reviewed_candidate_pool_count: `{report['reviewed_candidate_pool_count']}`",
            f"- trajectory_count: `{report['trajectory_count']}`",
            f"- projection_zone_counts: `{report['projection_zone_counts']}`",
            f"- measured_tiers: `{report['classification_surface'].get('measured_tiers', [])}`",
            f"- scratch_local_tiers: `{report['classification_surface'].get('scratch_local_tiers', [])}`",
            f"- projection_only_tiers: `{report['classification_surface'].get('projection_only_tiers', [])}`",
            f"- no_go_tiers: `{report['classification_surface'].get('no_go_tiers', [])}`",
            "",
            "Projection Zone Counts",
        ]
        for row in report.get("projection_zone_count_reports", []):
            lines.append(f"- projection_zone_count: `{row.get('projection_zone_count', '')}`")
            lines.append(f"  evidence_label: `{row.get('evidence_label', '')}`")
            lines.append(f"  suitability_classification: `{row.get('suitability_classification', '')}`")
            lines.append(f"  projection_status: `{row.get('projection_status', '')}`")
            lines.append(f"  scenario_cardinality: `{row.get('scenario_cardinality', {})}`")
            lines.append(f"  execution_cardinality: `{row.get('execution_cardinality', {})}`")
            lines.append(f"  reducer_pressure: `{row.get('reducer_pressure', {})}`")
            lines.append(f"  runtime_seconds: `{row.get('runtime_seconds', {})}`")
            lines.append(f"  storage_bytes: `{row.get('storage_bytes', {})}`")
            lines.append(f"  file_count: `{row.get('file_count', {})}`")
            lines.append(f"  no_go_labels: `{row.get('no_go_labels', [])}`")
            lines.append(f"  blocked_reason: `{row.get('blocked_reason', '')}`")
        lines.extend(
            [
                "",
                "Projection Summary",
                f"- largest_projection_zone_count: `{report['largest_projection_zone_count']}`",
                f"- projected_files: `{report['projected_files']}`",
                f"- projected_bytes: `{report['projected_bytes']}`",
                f"- estimated_runtime_seconds: `{report['estimated_runtime_seconds']}`",
                f"- projection_classification_summary: `{report['projection_classification_summary']}`",
                "",
                "Projection Assumptions",
            ]
        )
        for assumption in report.get("projection_assumptions", []):
            lines.append(f"- {assumption}")
        lines.extend(
            [
                "",
                "Projection Uncertainty",
                f"- runtime_seconds: `{report['projection_uncertainty'].get('runtime_seconds', {})}`",
                f"- storage_bytes: `{report['projection_uncertainty'].get('storage_bytes', {})}`",
                f"- file_count: `{report['projection_uncertainty'].get('file_count', {})}`",
                f"- memory_peak_mb: `{report['projection_uncertainty'].get('memory_peak_mb', {})}`",
            ]
        )
        return "\n".join(lines)

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
        f"- cardinality_pressure_summary: `{report.get('cardinality_pressure_summary', {})}`",
        "",
        "Scenario Preview Rows",
    ]
    for row in report.get("rows", []):
        lines.append(f"- source_zone_id: `{row.get('source_zone_id', '')}`")
        lines.append(f"  block_family_id: `{row.get('block_family_id', '')}`")
        lines.append(f"  scenario_family_id: `{row.get('scenario_family_id', '')}`")
        lines.append(f"  trajectory_count: `{row.get('trajectory_count', '')}`")
        lines.append(f"  expected_trajectory_count: `{row.get('expected_trajectory_count', '')}`")
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


def parse_selected_zone_counts(value: str | list[int] | tuple[int, ...]) -> list[int]:
    if isinstance(value, (list, tuple)):
        counts = [int(item) for item in value if int(item) > 0]
    else:
        counts = [int(item.strip()) for item in value.split(",") if item.strip()]
    unique_counts: list[int] = []
    seen: set[int] = set()
    for count in counts:
        if count <= 0 or count in seen:
            continue
        seen.add(count)
        unique_counts.append(count)
    return sorted(unique_counts)


def display_path(path: Path) -> str:
    resolved = path.resolve(strict=False)
    try:
        return str(resolved.relative_to(ROOT))
    except ValueError:
        return str(resolved)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
