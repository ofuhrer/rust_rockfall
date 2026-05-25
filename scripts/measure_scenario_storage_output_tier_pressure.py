#!/usr/bin/env python3
"""Measure scenario storage and output-tier pressure for expansion planning.

This helper is read-only except for scratch scenario-table materialization
under /tmp. It measures existing fixture and current real-AOI candidate
bundles, compares minimal, rebuildable-reduced, GIS, and research-full output
tiers, and recommends the smallest tier suitable for Balfrin demonstration
replay. It does not run ensembles, delete outputs, submit jobs, or authorize
scale-up.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import generate_candidate_source_zone_scenarios as SCENARIO_FREEZER  # noqa: E402
from scripts import summarize_management_aoi_scenario_pressure as MANAGEMENT_PRESSURE  # noqa: E402
from scripts.lib.output_family_accounting import classify_storage_path_family  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "scenario_storage_output_tier_pressure_v1"
DEFAULT_FIXTURE_REVIEW_PACKAGE = ROOT / "tests/fixtures/aoi_scenario_preview/tiny_review_package.yaml"
DEFAULT_FIXTURE_RUN_ROOT = ROOT / "tests/fixtures/balfrin_probe_metrics_contract/complete_run_root"
DEFAULT_REAL_CANDIDATE_METRICS = (
    ROOT / "validation/private/source_zone_review/tschamut_expanded_source_zone_candidate_report.json"
)
DEFAULT_REAL_CANDIDATE_REVIEW = (
    ROOT / "validation/private/source_zone_review/tschamut_adjacent_prau_mulins_candidate_v1_review_manifest.json"
)
DEFAULT_POLICY = ROOT / "validation/policies/tschamut_public_source_scenario_policy_v1.yaml"
DEFAULT_REDUCED_ROOT = ROOT / "validation/private/tschamut_public_pilot/target_gate_v1_rebuildable_reduced"
DEFAULT_FULL_VALIDATION_ROOT = ROOT / "validation/private/tschamut_public_pilot/target_gate_v1"
DEFAULT_GIS_ROOT = ROOT / "hazard/results/tschamut_public_pilot/target_gate_v1"
DEFAULT_FIXTURE_TRAJECTORY_COUNT = 6
DEFAULT_EXPANDED_CANDIDATE_REPEAT_COUNTS = (1, 3, 8)
MEASURED_REGIONAL_SPLIT = {
    "task_id": "TB-448",
    "job_id": "4350232",
    "run_root": "/scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_multi_release_zone_v1",
    "validation_output_file_count": 130,
    "validation_output_bytes": 34_565_323,
    "hazard_output_file_count": 53,
    "hazard_output_bytes": 55_837_701,
    "conditional_curve_rows": 729_600,
    "collector_wall_seconds": 6.738646155004972,
    "collector_peak_memory_mb": 172.921875,
}
COMPACT_BATCH_CAP_REGRESSION_LIMITS = {
    "max_candidate_repeat_count": 3,
    "max_candidate_release_zone_record_count": 30,
    "max_scenario_row_count": 300,
    "max_output_file_count": 4,
    "max_manifest_bytes": 211_277,
    "max_total_bytes": 595_867,
}

REBUILD_REQUIRED_FAMILIES = (
    "trajectory",
    "deposition",
    "impact_events",
    "diagnostics",
    "trajectory_metadata",
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture-review-package", type=Path, default=DEFAULT_FIXTURE_REVIEW_PACKAGE)
    parser.add_argument("--fixture-run-root", type=Path, default=DEFAULT_FIXTURE_RUN_ROOT)
    parser.add_argument("--candidate-metrics-manifest", type=Path, default=DEFAULT_REAL_CANDIDATE_METRICS)
    parser.add_argument("--candidate-review-manifest", type=Path, default=DEFAULT_REAL_CANDIDATE_REVIEW)
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("--rebuildable-reduced-root", type=Path, default=DEFAULT_REDUCED_ROOT)
    parser.add_argument("--full-validation-root", type=Path, default=DEFAULT_FULL_VALIDATION_ROOT)
    parser.add_argument("--gis-root", type=Path, default=DEFAULT_GIS_ROOT)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    return parser.parse_args(argv)


def build_report(
    *,
    fixture_review_package: Path = DEFAULT_FIXTURE_REVIEW_PACKAGE,
    fixture_run_root: Path = DEFAULT_FIXTURE_RUN_ROOT,
    candidate_metrics_manifest: Path = DEFAULT_REAL_CANDIDATE_METRICS,
    candidate_review_manifest: Path = DEFAULT_REAL_CANDIDATE_REVIEW,
    policy_path: Path = DEFAULT_POLICY,
    release_points_path: Path = SCENARIO_FREEZER.DEFAULT_RELEASE_POINTS,
    candidate_repeat_counts: tuple[int, ...] = DEFAULT_EXPANDED_CANDIDATE_REPEAT_COUNTS,
    rebuildable_reduced_root: Path = DEFAULT_REDUCED_ROOT,
    full_validation_root: Path = DEFAULT_FULL_VALIDATION_ROOT,
    gis_root: Path = DEFAULT_GIS_ROOT,
) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(dir="/tmp", prefix="scenario_tier_pressure_") as tmp:
        scratch = Path(tmp)
        fixture_scenario = build_fixture_scenario_measurement(
            review_package_path=fixture_review_package,
            output_root=scratch / "fixture_scenario_table",
        )
        real_candidate = build_real_candidate_measurement(
            candidate_metrics_manifest=candidate_metrics_manifest,
            candidate_review_manifest=candidate_review_manifest,
            policy_path=policy_path,
            scratch_root=scratch / "real_aoi",
        )
        expanded_candidate_sets = build_expanded_candidate_set_measurements(
            policy_path=policy_path,
            release_points_path=release_points_path,
            candidate_repeat_counts=candidate_repeat_counts,
            scratch_root=scratch / "expanded_candidate_sets",
        )

    output_families = {
        "fixture_run_root": measure_root(
            fixture_run_root,
            label="fixture_run_root",
            evidence_label="fixture_backed",
        ),
        "rebuildable_reduced": measure_root(
            rebuildable_reduced_root,
            label="rebuildable_reduced",
            evidence_label=evidence_label_for_path(rebuildable_reduced_root),
        ),
        "full_validation": measure_root(
            full_validation_root,
            label="full_validation",
            evidence_label=evidence_label_for_path(full_validation_root),
        ),
        "gis": measure_root(
            gis_root,
            label="gis",
            evidence_label=evidence_label_for_path(gis_root),
        ),
    }
    tier_comparison = build_tier_comparison(
        fixture_scenario=fixture_scenario,
        real_candidate=real_candidate,
        output_families=output_families,
    )
    recommendation = recommend_balfrin_replay_tier(tier_comparison)
    batching_rule = recommend_candidate_batching_rule(expanded_candidate_sets)
    next_bottleneck = determine_next_bottleneck(real_candidate=real_candidate, tier_comparison=tier_comparison)
    storage_output_tier_bands = [
        {
            "tier_id": row["tier_id"],
            "tier_role": row["tier_role"],
            "file_count": row["file_count"],
            "total_bytes": row["total_bytes"],
            "replay_suitability": row["replay_suitability"],
        }
        for row in tier_comparison
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "measurement_status": "ready",
        "read_only": True,
        "scratch_outputs_committed": False,
        "scale_up_authorized": False,
        "operational_claims_allowed": False,
        "fixture_measurement": fixture_scenario,
        "real_aoi_candidate_measurement": real_candidate,
        "expanded_candidate_set_measurements": expanded_candidate_sets,
        "next_balfrin_package_batching_rule": batching_rule,
        "compact_batch_cap_regression_guard": build_compact_batch_cap_regression_guard(batching_rule),
        "output_family_measurements": output_families,
        "tier_comparison": tier_comparison,
        "storage_output_tier_bands": storage_output_tier_bands,
        "measured_regional_split_comparison": build_measured_regional_split_comparison(
            storage_output_tier_bands=storage_output_tier_bands,
            batching_rule=batching_rule,
        ),
        "balfrin_demonstration_replay_recommendation": recommendation,
        "next_scale_bottleneck": next_bottleneck,
        "claim_boundaries": claim_boundaries(),
    }


def build_measured_regional_split_comparison(
    *,
    storage_output_tier_bands: list[dict[str, Any]],
    batching_rule: dict[str, Any],
) -> dict[str, Any]:
    tiers = {str(row.get("tier_id")): row for row in storage_output_tier_bands}
    rebuildable = tiers.get("rebuildable_reduced", {})
    gis = tiers.get("gis", {})
    measured_validation_files = int(MEASURED_REGIONAL_SPLIT["validation_output_file_count"])
    measured_validation_bytes = int(MEASURED_REGIONAL_SPLIT["validation_output_bytes"])
    measured_hazard_files = int(MEASURED_REGIONAL_SPLIT["hazard_output_file_count"])
    measured_hazard_bytes = int(MEASURED_REGIONAL_SPLIT["hazard_output_bytes"])
    return {
        "schema_version": "measured_regional_split_scenario_output_comparison_v1",
        "measurement_status": "measured_existing_balfrin_artifacts",
        "task_id": MEASURED_REGIONAL_SPLIT["task_id"],
        "job_id": MEASURED_REGIONAL_SPLIT["job_id"],
        "run_root": MEASURED_REGIONAL_SPLIT["run_root"],
        "validation_output_file_count": measured_validation_files,
        "validation_output_bytes": measured_validation_bytes,
        "hazard_output_file_count": measured_hazard_files,
        "hazard_output_bytes": measured_hazard_bytes,
        "conditional_curve_rows": MEASURED_REGIONAL_SPLIT["conditional_curve_rows"],
        "collector_wall_seconds": MEASURED_REGIONAL_SPLIT["collector_wall_seconds"],
        "collector_peak_memory_mb": MEASURED_REGIONAL_SPLIT["collector_peak_memory_mb"],
        "vs_rebuildable_reduced_tier": {
            "file_count_delta": measured_validation_files - int(rebuildable.get("file_count") or 0),
            "byte_delta": measured_validation_bytes - int(rebuildable.get("total_bytes") or 0),
            "classification": "measured_larger_than_rebuildable_reduced",
        },
        "vs_gis_tier": {
            "file_count_delta": measured_hazard_files - int(gis.get("file_count") or 0),
            "byte_delta": measured_hazard_bytes - int(gis.get("total_bytes") or 0),
            "classification": "measured_within_current_gis_package_band"
            if measured_hazard_files <= int(gis.get("file_count") or 0)
            and measured_hazard_bytes <= int(gis.get("total_bytes") or 0)
            else "measured_exceeds_current_gis_package_band",
        },
        "batching_rule_alignment": {
            "recommended_cap_candidate_repeat_count": batching_rule.get("recommended_cap_candidate_repeat_count"),
            "recommended_cap_scenario_row_count": batching_rule.get("recommended_cap_scenario_row_count"),
            "classification": "measured_run_should_reuse_compact_batch_cap_before_larger_probe",
        },
        "next_measured_run_candidate": "bounded_reduced_output_regional_split_retry_after_cog_and_reducer_review",
        "summary": (
            "The measured regional split output is larger than the rebuildable-reduced replay tier but remains within "
            "the current GIS package byte/file band, so the next measured run should keep the compact scenario batch cap "
            "and focus on reduced-output plus GIS/COG and reducer review before any larger probe."
        ),
    }


def build_fixture_scenario_measurement(*, review_package_path: Path, output_root: Path) -> dict[str, Any]:
    if not review_package_path.exists():
        return blocked_measurement(
            label="fixture_scenario_table",
            path=review_package_path,
            blocked_reason="fixture review package is missing",
            evidence_label="fixture_backed",
        )
    report = SCENARIO_FREEZER.build_freezer_report(
        review_package_path=review_package_path,
        accepted_candidate_ids=None,
        output_root=output_root,
        trajectory_count=DEFAULT_FIXTURE_TRAJECTORY_COUNT,
        seed=SCENARIO_FREEZER.DEFAULT_FREEZER_SEED,
        retain_row_payloads=False,
    )
    bundle = measure_root(output_root, label="fixture_scenario_table", evidence_label="fixture_backed")
    manifest_path = Path(str(report["output_paths"]["manifest"]))
    manifest = load_json(manifest_path) if manifest_path.exists() else {}
    return {
        "measurement_status": "ready",
        "evidence_label": "fixture_backed",
        "review_package_path": display_path(review_package_path),
        "trajectory_count": DEFAULT_FIXTURE_TRAJECTORY_COUNT,
        "scenario_row_count": int(report.get("scenario_row_count") or 0),
        "accepted_candidate_count": int(report.get("accepted_candidate_count") or 0),
        "block_family_count": len(report.get("block_family_ids", []) or []),
        "scenario_table_csv_bytes": safe_path_bytes(Path(str(report["output_paths"]["scenario_table"]))),
        "scenario_manifest_bytes": safe_path_bytes(manifest_path),
        "manifest_compaction": dict(report.get("manifest_compaction") or {}),
        "row_payload_materialization": dict(report.get("row_payload_materialization") or {}),
        "scenario_bundle": bundle,
        "scenario_family_cardinality": list(manifest.get("block_family_cardinality") or []),
    }


def build_real_candidate_measurement(
    *,
    candidate_metrics_manifest: Path,
    candidate_review_manifest: Path,
    policy_path: Path,
    scratch_root: Path,
) -> dict[str, Any]:
    if not candidate_metrics_manifest.exists() or not candidate_review_manifest.exists() or not policy_path.exists():
        missing = [
            display_path(path)
            for path in (candidate_metrics_manifest, candidate_review_manifest, policy_path)
            if not path.exists()
        ]
        return {
            "measurement_status": "blocked_missing_inputs",
            "evidence_label": "measured_existing_artifacts",
            "missing_inputs": missing,
            "scenario_row_count": 0,
            "scenario_table_total_bytes": 0,
            "candidate_bundle": measure_root(candidate_metrics_manifest.parent, label="real_candidate_bundle"),
        }
    candidate_metrics = load_json(candidate_metrics_manifest)
    candidate_review = load_json(candidate_review_manifest)
    generated = MANAGEMENT_PRESSURE.build_generated_scenario_table_report(
        candidate_review_manifest_path=candidate_review_manifest,
        policy_path=policy_path,
        output_root=scratch_root / "management_pressure",
        scenario_output_root=scratch_root / "scenario_table",
    )
    scenario_generation = dict(generated.get("scenario_table_generation") or {})
    scenario_rows = [row for row in scenario_generation.get("scenario_table_rows", []) if isinstance(row, dict)]
    if scenario_rows:
        cardinality = MANAGEMENT_PRESSURE.AOI_PREVIEW.summarize_scenario_table_rows(scenario_rows)
    else:
        cardinality = {
            "scenario_family_cardinality": list(
                scenario_generation.get("scenario_family_cardinality")
                or scenario_generation.get("scenario_family_template_cardinality")
                or []
            ),
            "release_zone_cardinality": list(
                scenario_generation.get("release_zone_cardinality")
                or scenario_generation.get("source_zone_family_cardinality")
                or []
            ),
        }
    review_summary = dict(candidate_review.get("review_summary") or {})
    candidate_summary = dict(candidate_metrics.get("candidate_summary") or {})
    status = "ready" if generated.get("scenario_table_status") == "ready" else str(generated.get("scenario_table_status") or "unknown")
    return {
        "measurement_status": status,
        "evidence_label": "measured_existing_artifacts",
        "candidate_metrics_manifest_path": display_path(candidate_metrics_manifest),
        "candidate_review_manifest_path": display_path(candidate_review_manifest),
        "policy_path": display_path(policy_path),
        "candidate_count": int(candidate_summary.get("candidate_cell_count") or review_summary.get("candidate_count") or 0),
        "candidate_review_count": int(review_summary.get("candidate_count") or 0),
        "scenario_row_count": int(scenario_generation.get("scenario_row_count") or 0),
        "scenario_table_file_count": int(scenario_generation.get("file_count") or 0),
        "scenario_table_csv_bytes": int(scenario_generation.get("csv_bytes") or 0),
        "scenario_manifest_bytes": int(scenario_generation.get("manifest_bytes") or 0),
        "manifest_compaction": dict(scenario_generation.get("manifest_compaction") or {}),
        "row_payload_materialization": dict(scenario_generation.get("row_payload_materialization") or {}),
        "scenario_table_total_bytes": int(scenario_generation.get("total_bytes") or 0),
        "release_plan_root": scenario_generation.get("review_application_output_root", ""),
        "scenario_table_output_root": scenario_generation.get("scenario_table_output_root", ""),
        "candidate_bundle": measure_root(candidate_metrics_manifest.parent, label="real_candidate_bundle"),
        "scenario_family_cardinality": cardinality["scenario_family_cardinality"],
        "release_zone_cardinality": cardinality["release_zone_cardinality"],
        "blocked_reason": generated.get("blocked_reason", ""),
    }


def build_expanded_candidate_set_measurements(
    *,
    policy_path: Path,
    release_points_path: Path,
    candidate_repeat_counts: tuple[int, ...],
    scratch_root: Path,
) -> list[dict[str, Any]]:
    if not policy_path.exists() or not release_points_path.exists():
        missing = [
            display_path(path)
            for path in (policy_path, release_points_path)
            if not path.exists()
        ]
        return [
            {
                "measurement_status": "blocked_missing_inputs",
                "blocked_reason": "missing required scenario-expansion inputs",
                "missing_inputs": missing,
                "candidate_repeat_count": repeat_count,
                "candidate_release_zone_record_count": 0,
                "scenario_row_count": 0,
                "csv_bytes": 0,
                "manifest_bytes": 0,
                "total_bytes": 0,
                "scenario_family_template_cardinality": [],
                "source_zone_family_cardinality": [],
                "block_family_cardinality": [],
                "shape_family_cardinality": [],
                "first_scaling_bottleneck": {
                    "name": "unavailable",
                    "reason": "required scenario-expansion inputs are missing",
                },
                "tb_183_planning_input": {
                    "status": "blocked_missing_inputs",
                    "reason": "required scenario-expansion inputs are missing",
                    "candidate_release_zone_record_count": 0,
                    "scenario_row_count": 0,
                    "block_family_count": 0,
                    "scenario_family_template_count": 0,
                    "ready_for_tb_183": False,
                },
            }
            for repeat_count in candidate_repeat_counts
        ]

    measurements: list[dict[str, Any]] = []
    for repeat_count in candidate_repeat_counts:
        if repeat_count < 1:
            raise ValueError("candidate-repeat-counts must contain positive integers")
        generated = SCENARIO_FREEZER.build_report(
            policy_path=policy_path,
            release_points_path=release_points_path,
            output_root=scratch_root / f"candidate_repeat_{repeat_count:02d}",
            candidate_repeat_count=repeat_count,
        )
        manifest = dict(generated.get("scenario_table_manifest") or {})
        storage = dict(generated.get("storage_measurements") or {})
        measurements.append(
            {
                "measurement_status": generated.get("stress_test_status", "unknown"),
                "blocked_reason": generated.get("blocked_reason"),
                "candidate_repeat_count": repeat_count,
                "candidate_release_zone_record_count": int(generated.get("candidate_release_zone_record_count") or 0),
                "scenario_row_count": int(generated.get("scenario_row_count") or 0),
                "csv_bytes": int(storage.get("csv_bytes") or 0),
                "manifest_bytes": int(storage.get("manifest_bytes") or 0),
                "total_bytes": int(storage.get("total_bytes") or 0),
                "output_file_count": len(generated.get("output_paths") or {}),
                "scenario_family_template_cardinality": list(manifest.get("scenario_family_template_cardinality") or []),
                "source_zone_family_cardinality": list(manifest.get("source_zone_family_cardinality") or []),
                "block_family_cardinality": list(manifest.get("block_family_cardinality") or []),
                "shape_family_cardinality": list(manifest.get("shape_family_cardinality") or []),
                "first_scaling_bottleneck": dict(generated.get("first_scaling_bottleneck") or {}),
                "tb_183_planning_input": dict(generated.get("tb_183_planning_input") or {}),
            }
        )
    return measurements


def recommend_candidate_batching_rule(candidate_measurements: list[dict[str, Any]]) -> dict[str, Any]:
    ready_measurements = [
        measurement
        for measurement in candidate_measurements
        if measurement.get("measurement_status") == "ready"
    ]
    if not ready_measurements:
        return {
            "recommended_batching_status": "blocked_missing_inputs",
            "batching_key": "candidate_repeat_count",
            "recommended_cap_candidate_repeat_count": 0,
            "recommended_cap_candidate_release_zone_record_count": 0,
            "recommended_cap_scenario_row_count": 0,
            "reason": "scenario-expansion measurements are unavailable",
        }

    ordered = sorted(ready_measurements, key=lambda measurement: int(measurement.get("candidate_repeat_count") or 0))
    cap_measurement = max(
        (measurement for measurement in ordered if int(measurement.get("candidate_repeat_count") or 0) <= 3),
        key=lambda measurement: int(measurement.get("candidate_repeat_count") or 0),
        default=ordered[0],
    )
    return {
        "recommended_batching_status": "ready",
        "batching_key": "candidate_repeat_count",
        "recommended_cap_candidate_repeat_count": int(cap_measurement.get("candidate_repeat_count") or 0),
        "recommended_cap_candidate_release_zone_record_count": int(cap_measurement.get("candidate_release_zone_record_count") or 0),
        "recommended_cap_scenario_row_count": int(cap_measurement.get("scenario_row_count") or 0),
        "cap_summary": (
            f"{int(cap_measurement.get('candidate_repeat_count') or 0)}-repeat / "
            f"{int(cap_measurement.get('candidate_release_zone_record_count') or 0)}-candidate / "
            f"{int(cap_measurement.get('scenario_row_count') or 0)}-row cap"
        ),
        "cap_measurement": {
            "candidate_repeat_count": int(cap_measurement.get("candidate_repeat_count") or 0),
            "candidate_release_zone_record_count": int(cap_measurement.get("candidate_release_zone_record_count") or 0),
            "scenario_row_count": int(cap_measurement.get("scenario_row_count") or 0),
            "csv_bytes": int(cap_measurement.get("csv_bytes") or 0),
            "manifest_bytes": int(cap_measurement.get("manifest_bytes") or 0),
            "total_bytes": int(cap_measurement.get("total_bytes") or 0),
            "output_file_count": int(cap_measurement.get("output_file_count") or 0),
        },
        "reason": (
            "batch at the largest measured candidate-repeat level at or below 3; "
            "the 8-repeat step grows to 800 rows and roughly 1.2 MB of manifest bytes, "
            "so larger candidate pools should be split into 3-repeat / 30-candidate chunks"
        ),
    }


def build_compact_batch_cap_regression_guard(batching_rule: dict[str, Any]) -> dict[str, Any]:
    limits = dict(COMPACT_BATCH_CAP_REGRESSION_LIMITS)
    cap = dict(batching_rule.get("cap_measurement") or {})
    checks = [
        {
            "metric": "candidate_repeat_count",
            "value": int(cap.get("candidate_repeat_count") or 0),
            "max_allowed": limits["max_candidate_repeat_count"],
        },
        {
            "metric": "candidate_release_zone_record_count",
            "value": int(cap.get("candidate_release_zone_record_count") or 0),
            "max_allowed": limits["max_candidate_release_zone_record_count"],
        },
        {
            "metric": "scenario_row_count",
            "value": int(cap.get("scenario_row_count") or 0),
            "max_allowed": limits["max_scenario_row_count"],
        },
        {
            "metric": "output_file_count",
            "value": int(cap.get("output_file_count") or 0),
            "max_allowed": limits["max_output_file_count"],
        },
        {
            "metric": "manifest_bytes",
            "value": int(cap.get("manifest_bytes") or 0),
            "max_allowed": limits["max_manifest_bytes"],
        },
        {
            "metric": "total_bytes",
            "value": int(cap.get("total_bytes") or 0),
            "max_allowed": limits["max_total_bytes"],
        },
    ]
    exceeded = [check for check in checks if check["value"] > check["max_allowed"]]
    return {
        "schema_version": "compact_batch_cap_regression_guard_v1",
        "guard_status": "pass" if not exceeded else "fail",
        "limits": limits,
        "checks": checks,
        "exceeded_limits": exceeded,
        "explicit_update_required": bool(exceeded),
        "guard_scope": "fixture-backed compact candidate batch cap only; no live execution or scale-up authorization",
    }


def measure_root(path: Path, *, label: str, evidence_label: str | None = None) -> dict[str, Any]:
    root = Path(path)
    if not root.exists():
        return {
            "label": label,
            "root": display_path(root),
            "measurement_status": "blocked_missing_root",
            "evidence_label": evidence_label or evidence_label_for_path(root),
            "file_count": 0,
            "total_bytes": 0,
            "manifest_bytes": 0,
            "family_counts": {},
            "family_bytes": {},
            "csv_row_counts": {},
        }
    files = sorted(file for file in root.rglob("*") if file.is_file())
    family_counts: dict[str, int] = {}
    family_bytes: dict[str, int] = {}
    csv_row_counts: dict[str, int] = {}
    for file in files:
        family = classify_file_family(file)
        size = file.stat().st_size
        family_counts[family] = family_counts.get(family, 0) + 1
        family_bytes[family] = family_bytes.get(family, 0) + size
        if file.suffix.lower() == ".csv":
            csv_row_counts[display_path(file)] = count_csv_data_rows(file)
    return {
        "label": label,
        "root": display_path(root),
        "measurement_status": "ready",
        "evidence_label": evidence_label or evidence_label_for_path(root),
        "file_count": len(files),
        "total_bytes": sum(file.stat().st_size for file in files),
        "manifest_bytes": sum(file.stat().st_size for file in files if "manifest" in file.name),
        "family_counts": dict(sorted(family_counts.items())),
        "family_bytes": dict(sorted(family_bytes.items())),
        "csv_row_counts": csv_row_counts,
    }


def build_tier_comparison(
    *,
    fixture_scenario: dict[str, Any],
    real_candidate: dict[str, Any],
    output_families: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    minimal_bytes = int(real_candidate.get("scenario_table_total_bytes") or 0)
    if minimal_bytes <= 0:
        minimal_bytes = int(((fixture_scenario.get("scenario_bundle") or {}).get("total_bytes")) or 0)
    minimal_files = int(real_candidate.get("scenario_table_file_count") or 0)
    if minimal_files <= 0:
        minimal_files = int(((fixture_scenario.get("scenario_bundle") or {}).get("file_count")) or 0)
    reduced = output_families["rebuildable_reduced"]
    gis = output_families["gis"]
    full = output_families["full_validation"]
    return [
        {
            "tier_id": "minimal",
            "tier_role": "scenario table plus release-plan manifest only",
            "measurement_status": "ready" if minimal_files > 0 else "blocked_no_scenario_table",
            "file_count": minimal_files,
            "total_bytes": minimal_bytes,
            "required_for_balfrin_replay": False,
            "replay_suitability": "insufficient_missing_trajectory_outputs",
            "omitted_families": list(REBUILD_REQUIRED_FAMILIES),
        },
        {
            "tier_id": "rebuildable_reduced",
            "tier_role": "smallest builder-facing validation outputs needed to replay or rebuild hazard layers",
            "measurement_status": reduced["measurement_status"],
            "file_count": reduced["file_count"],
            "total_bytes": reduced["total_bytes"],
            "required_for_balfrin_replay": True,
            "replay_suitability": classify_rebuildable_reduced(reduced),
            "family_counts": reduced["family_counts"],
        },
        {
            "tier_id": "gis",
            "tier_role": "map package, rasters, vectors, and GIS manifests for QGIS review",
            "measurement_status": gis["measurement_status"],
            "file_count": gis["file_count"],
            "total_bytes": gis["total_bytes"],
            "required_for_balfrin_replay": False,
            "replay_suitability": "sufficient_for_review_not_minimal_replay"
            if gis["measurement_status"] == "ready"
            else "blocked_missing_gis_root",
            "family_counts": gis["family_counts"],
        },
        {
            "tier_id": "research_full",
            "tier_role": "full validation output with full trajectory/history products where present",
            "measurement_status": full["measurement_status"],
            "file_count": full["file_count"],
            "total_bytes": full["total_bytes"],
            "required_for_balfrin_replay": False,
            "replay_suitability": "sufficient_but_not_smallest"
            if full["measurement_status"] == "ready"
            else "blocked_missing_full_root",
            "family_counts": full["family_counts"],
        },
    ]


def recommend_balfrin_replay_tier(tier_comparison: list[dict[str, Any]]) -> dict[str, Any]:
    by_id = {row["tier_id"]: row for row in tier_comparison}
    reduced = by_id["rebuildable_reduced"]
    if reduced["replay_suitability"] == "sufficient":
        return {
            "recommended_tier": "rebuildable_reduced",
            "recommendation_status": "ready",
            "reason": "minimal omits trajectory outputs; rebuildable_reduced is the smallest measured tier preserving builder-facing replay inputs",
            "required_followup": "keep GIS and research-full outputs optional unless QGIS review or trajectory research inspection is requested",
        }
    return {
        "recommended_tier": "research_full",
        "recommendation_status": "fallback_required",
        "reason": "rebuildable_reduced is not complete in the measured roots, so full validation output is the smallest available replay fallback",
        "required_followup": "restore the missing rebuildable-reduced output families before using it as the Balfrin replay tier",
    }


def determine_next_bottleneck(*, real_candidate: dict[str, Any], tier_comparison: list[dict[str, Any]]) -> dict[str, Any]:
    if real_candidate.get("measurement_status") != "ready":
        return {
            "bottleneck_id": "real_aoi_candidate_scenario_generation",
            "status": real_candidate.get("measurement_status", "unknown"),
            "summary": real_candidate.get("blocked_reason") or "current real-AOI candidate scenario table is not ready",
        }
    largest = max(tier_comparison, key=lambda row: int(row.get("total_bytes") or 0))
    return {
        "bottleneck_id": "gis_and_research_full_output_growth",
        "status": "measured_existing_artifacts",
        "summary": (
            f"scenario table pressure is measured at {real_candidate.get('scenario_row_count')} rows; "
            f"the largest measured tier is {largest['tier_id']} with {largest['file_count']} files and "
            f"{largest['total_bytes']} bytes, so GIS/research-full output growth is the next storage bottleneck."
        ),
    }


def classify_rebuildable_reduced(measurement: dict[str, Any]) -> str:
    if measurement.get("measurement_status") != "ready":
        return "blocked_missing_reduced_root"
    family_counts = dict(measurement.get("family_counts") or {})
    missing = [family for family in REBUILD_REQUIRED_FAMILIES if family_counts.get(family, 0) <= 0]
    return "sufficient" if not missing else "insufficient_missing_" + "_".join(missing)


def classify_file_family(path: Path) -> str:
    return classify_storage_path_family(path)


def count_csv_data_rows(path: Path) -> int:
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            return max(0, sum(1 for _ in csv.reader(handle)) - 1)
    except UnicodeDecodeError:
        return 0


def blocked_measurement(*, label: str, path: Path, blocked_reason: str, evidence_label: str) -> dict[str, Any]:
    return {
        "measurement_status": "blocked_missing_inputs",
        "label": label,
        "path": display_path(path),
        "blocked_reason": blocked_reason,
        "evidence_label": evidence_label,
        "scenario_row_count": 0,
    }


def evidence_label_for_path(path: Path) -> str:
    try:
        parts = path.resolve(strict=False).relative_to(ROOT).parts
    except ValueError:
        return "scratch_local"
    if len(parts) >= 2 and parts[0] == "tests" and parts[1] == "fixtures":
        return "fixture_backed"
    return "measured_existing_artifacts"


def safe_path_bytes(path: Path) -> int:
    return path.stat().st_size if path.exists() else 0


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def display_path(path: Path) -> str:
    resolved = path.resolve(strict=False)
    try:
        return str(resolved.relative_to(ROOT))
    except ValueError:
        return str(resolved)


def claim_boundaries() -> dict[str, bool]:
    return {
        "operational_claims_allowed": False,
        "physical_probability_claims_allowed": False,
        "annual_frequency_claims_allowed": False,
        "risk_exposure_vulnerability_claims_allowed": False,
        "scale_up_authorized": False,
        "distributed_execution_authorized": False,
    }


def render_text_report(report: dict[str, Any]) -> str:
    recommendation = report["balfrin_demonstration_replay_recommendation"]
    bottleneck = report["next_scale_bottleneck"]
    batching_rule = report["next_balfrin_package_batching_rule"]
    lines = [
        "Scenario Storage And Output-Tier Pressure",
        f"schema_version: {report['schema_version']}",
        f"measurement_status: {report['measurement_status']}",
        f"fixture_scenario_rows: {report['fixture_measurement'].get('scenario_row_count', 0)}",
        f"real_aoi_scenario_rows: {report['real_aoi_candidate_measurement'].get('scenario_row_count', 0)}",
        "expanded_candidate_measurements:",
    ]
    for measurement in report.get("expanded_candidate_set_measurements", []):
        lines.append(
            f"  - repeat={measurement['candidate_repeat_count']} candidates={measurement['candidate_release_zone_record_count']} "
            f"rows={measurement['scenario_row_count']} csv_bytes={measurement['csv_bytes']} "
            f"manifest_bytes={measurement['manifest_bytes']} total_bytes={measurement['total_bytes']}"
        )
    lines.extend([
        "next_balfrin_package_batching_rule:",
        f"  status: {batching_rule['recommended_batching_status']}",
        f"  key: {batching_rule['batching_key']}",
        f"  cap_summary: {batching_rule['cap_summary']}",
        f"  cap_repeat_count: {batching_rule['recommended_cap_candidate_repeat_count']}",
        f"  cap_candidate_records: {batching_rule['recommended_cap_candidate_release_zone_record_count']}",
        f"  cap_scenario_rows: {batching_rule['recommended_cap_scenario_row_count']}",
        f"  reason: {batching_rule['reason']}",
        "storage_output_tier_bands:",
    ])
    for tier in report["storage_output_tier_bands"]:
        lines.append(
            f"  - {tier['tier_id']}: files={tier['file_count']} bytes={tier['total_bytes']} "
            f"replay={tier['replay_suitability']}"
        )
    lines.append("tier_comparison:")
    for tier in report["tier_comparison"]:
        lines.append(
            f"  - {tier['tier_id']}: status={tier['measurement_status']} files={tier['file_count']} "
            f"bytes={tier['total_bytes']} replay={tier['replay_suitability']}"
        )
    regional = report["measured_regional_split_comparison"]
    lines.extend(
        [
            "recommendation:",
            f"  tier: {recommendation['recommended_tier']}",
            f"  status: {recommendation['recommendation_status']}",
            f"  reason: {recommendation['reason']}",
            "measured_regional_split_comparison:",
            f"  measurement_status: {regional['measurement_status']}",
            f"  job_id: {regional['job_id']}",
            f"  vs_gis_tier: {regional['vs_gis_tier']['classification']}",
            f"  next_measured_run_candidate: {regional['next_measured_run_candidate']}",
            "next_scale_bottleneck:",
            f"  id: {bottleneck['bottleneck_id']}",
            f"  status: {bottleneck['status']}",
            f"  summary: {bottleneck['summary']}",
            "claim_boundaries:",
        ]
    )
    for key, value in report["claim_boundaries"].items():
        lines.append(f"  {key}: {value}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        report = build_report(
            fixture_review_package=args.fixture_review_package,
            fixture_run_root=args.fixture_run_root,
            candidate_metrics_manifest=args.candidate_metrics_manifest,
            candidate_review_manifest=args.candidate_review_manifest,
            policy_path=args.policy,
            rebuildable_reduced_root=args.rebuildable_reduced_root,
            full_validation_root=args.full_validation_root,
            gis_root=args.gis_root,
        )
    except (OSError, ValueError) as exc:
        print(f"scenario storage pressure error: {exc}", file=sys.stderr)
        return 2

    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text_report(report))
    return 0 if report["measurement_status"] == "ready" else 2


if __name__ == "__main__":
    raise SystemExit(main())
