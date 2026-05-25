#!/usr/bin/env python3
"""Summarize the closure-gap deltas for the Tschamut conditional pilot.

This helper is read-only. It composes the canonical diagnostic interpretation
with the spatial decomposition and measured output/runtime/product evidence to
show which measured fields keep the pilot inconclusive, how the closure-limiting
layers differ from the deferrable layer, and why the current evidence is closer
to deferred than to no-go.
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import math
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
SCHEMA_VERSION = "tschamut_closure_gap_deltas_v1"
DEFAULT_CANDIDATE_LOCAL_COMPARISON_RECORD = (
    ROOT / "validation/pilot_runs/tschamut_candidate_adjacent_prau_mulins_local_comparison_v1.yaml"
)


def _load_module(module_name: str, filename: str):
    path = ROOT / "scripts" / filename
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ClosureGapDeltasError(f"unable to load helper module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


DIAGNOSTIC = _load_module(
    "tschamut_closure_gap_diagnostic_interpretation",
    "summarize_tschamut_conditional_diagnostic_interpretation.py",
)


class ClosureGapDeltasError(ValueError):
    """User-facing closure-gap delta error."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("json", "text"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    parser.add_argument(
        "--evidence-json",
        type=Path,
        default=None,
        help="optional override JSON file for tests or alternate evidence snapshots",
    )
    args = parser.parse_args(argv)

    try:
        report = build_report(load_evidence_override(args.evidence_json))
    except ClosureGapDeltasError as exc:
        print(f"tschamut closure-gap delta summary error: {exc}", file=sys.stderr)
        return 2

    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text_report(report))
    return 0 if report["closure_gap_status"] != "blocked_missing_inputs" else 2


def load_evidence_override(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    if not path.exists():
        raise ClosureGapDeltasError(f"evidence override file is missing: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ClosureGapDeltasError("evidence override must be a JSON object")
    return data


def build_report(evidence_override: dict[str, Any] | None = None) -> dict[str, Any]:
    if evidence_override and evidence_override.get("missing_inputs"):
        missing_inputs = [str(item) for item in evidence_override.get("missing_inputs", [])]
        return blocked_report(missing_inputs, reason="required evidence inputs are missing")

    diagnostic_report = gather_diagnostic_report(evidence_override)
    if diagnostic_report.get("interpretation_status") == "blocked_missing_inputs":
        missing_inputs = [str(item) for item in diagnostic_report.get("missing_inputs", [])]
        return blocked_report(missing_inputs, reason="required evidence inputs are missing")

    closure_report = dict((diagnostic_report.get("current_evidence") or {}).get("closure") or {})
    spatial = dict(closure_report.get("spatial_uncertainty_interpretation") or {})
    layer_roles = spatial.get("layer_roles") or {}

    closure_limiting_layers = summarize_layers(
        layer_roles,
        wanted_roles={"closure_limiting"},
        reference_layer_key="velocity_exceedance_5mps",
    )
    deferrable_layers = summarize_layers(
        layer_roles,
        wanted_roles={"deferrable"},
        reference_layer_key="velocity_exceedance_5mps",
    )

    scientific_blocker_deltas = build_scientific_blocker_deltas(layer_roles)
    workflow_product_blocker_deltas = build_workflow_product_blocker_deltas(diagnostic_report)
    claim_boundaries = summarize_claim_boundaries(diagnostic_report)

    accepted_diagnostic_gap = summarize_accepted_gap(diagnostic_report, closure_limiting_layers, workflow_product_blocker_deltas)
    deferred_gap = summarize_deferred_gap(diagnostic_report, closure_limiting_layers, deferrable_layers)
    no_go_gap = summarize_no_go_gap(diagnostic_report, closure_limiting_layers, workflow_product_blocker_deltas)
    candidate_runout_failure_diagnostic = summarize_candidate_runout_failure(evidence_override)
    candidate_geometry_ablation = summarize_candidate_geometry_ablation(evidence_override)

    current_closure_status = diagnostic_report.get("closure_status", "unknown")
    current_interpretation_status = diagnostic_report.get("interpretation_status", "unknown")
    gap_status = "measured_gaps_remain"
    if current_closure_status == "blocked_missing_inputs" or current_interpretation_status == "blocked_missing_inputs":
        gap_status = "blocked_missing_inputs"

    return {
        "schema_version": SCHEMA_VERSION,
        "closure_gap_status": gap_status,
        "current_closure_status": current_closure_status,
        "current_interpretation_status": current_interpretation_status,
        "same_scale_readiness_status": diagnostic_report.get("same_scale_readiness_status", "unknown"),
        "closure_limiting_layers": closure_limiting_layers,
        "deferrable_layers": deferrable_layers,
        "scientific_blocker_deltas": scientific_blocker_deltas,
        "workflow_product_blocker_deltas": workflow_product_blocker_deltas,
        "accepted_diagnostic_gap": accepted_diagnostic_gap,
        "deferred_gap": deferred_gap,
        "no_go_gap": no_go_gap,
        "candidate_runout_failure_diagnostic": candidate_runout_failure_diagnostic,
        "candidate_geometry_ablation": candidate_geometry_ablation,
        "claim_boundaries": claim_boundaries,
        "current_evidence": {
            "closure": closure_report,
            "spatial_uncertainty": spatial,
            "output_profile_status": diagnostic_report.get("output_profile_status", {}),
            "gis_cog_status": diagnostic_report.get("gis_cog_status", {}),
            "runtime_scaling_status": diagnostic_report.get("runtime_scaling_status", {}),
            "portability_status": diagnostic_report.get("portability_status", {}),
            "physical_credibility_status": diagnostic_report.get("physical_credibility_status", "unknown"),
            "candidate_runout_failure": candidate_runout_failure_diagnostic,
            "candidate_geometry_ablation": candidate_geometry_ablation,
        },
        "scale_up_authorized": False,
        "operational_claims_allowed": False,
        "annual_frequency_claims_allowed": False,
        "risk_exposure_vulnerability_claims_allowed": False,
        "distributed_execution_authorized": False,
        "physical_probability_claims_allowed": False,
        "blocked_reason": "none",
    }


def gather_diagnostic_report(evidence_override: dict[str, Any] | None = None) -> dict[str, Any]:
    if evidence_override and isinstance(evidence_override.get("diagnostic_report"), dict):
        return dict(evidence_override["diagnostic_report"])
    return DIAGNOSTIC.build_report()


def summarize_layers(
    layer_roles: dict[str, Any],
    *,
    wanted_roles: set[str],
    reference_layer_key: str,
) -> list[dict[str, Any]]:
    reference = layer_roles.get(reference_layer_key, {})
    summaries = []
    for layer_key, layer in layer_roles.items():
        if layer.get("closure_role") not in wanted_roles:
            continue
        summaries.append(
            build_layer_summary(layer_key, layer, reference_layer_key, reference)
        )
    summaries.sort(key=lambda item: (item["closure_role"], item["layer_key"]))
    return summaries


def build_layer_summary(
    layer_key: str,
    layer: dict[str, Any],
    reference_layer_key: str,
    reference: dict[str, Any],
) -> dict[str, Any]:
    bbox = layer.get("high_uncertainty_bbox") or {}
    bbox_cell_area = bbox_cell_count(bbox)
    compactness = layer.get("high_uncertainty_cell_count", 0) / bbox_cell_area if bbox_cell_area else 0.0
    summary = {
        "layer_key": layer_key,
        "closure_role": layer.get("closure_role"),
        "stability_zone_class": layer.get("stability_zone_class"),
        "stability_zone_dominant_category": layer.get("stability_zone_dominant_category"),
        "stability_zone_dominant_high_uncertainty_category": layer.get("stability_zone_dominant_high_uncertainty_category"),
        "stability_zone_closure_role_impact": layer.get("stability_zone_closure_role_impact"),
        "disagreement_decomposition_class": layer.get("disagreement_decomposition_class"),
        "uncertainty_concentration_class": layer.get("uncertainty_concentration_class"),
        "high_uncertainty_cell_count": layer.get("high_uncertainty_cell_count"),
        "high_uncertainty_cell_fraction": layer.get("high_uncertainty_cell_fraction"),
        "high_uncertainty_support_nodata_fraction": layer.get("high_uncertainty_support_nodata_fraction"),
        "high_uncertainty_shared_support_magnitude_fraction": layer.get("high_uncertainty_shared_support_magnitude_fraction"),
        "support_only_disagreement_count": layer.get("support_only_disagreement_count"),
        "nodata_disagreement_count": layer.get("nodata_disagreement_count"),
        "magnitude_only_disagreement_count": layer.get("magnitude_only_disagreement_count"),
        "shared_valid_cell_count": layer.get("shared_valid_cell_count"),
        "analysis_cell_count": layer.get("analysis_cell_count"),
        "high_uncertainty_bbox": layer.get("high_uncertainty_bbox"),
        "high_uncertainty_bbox_cell_area": bbox_cell_area,
        "high_uncertainty_bbox_compactness": compactness,
        "shared_support_magnitude_range_summary": layer.get("disagreement_decomposition", {}).get(
            "shared_support_magnitude_range_summary",
            {},
        ),
        "reference_layer_key": reference_layer_key,
    }
    if reference:
        ref_bbox = reference.get("high_uncertainty_bbox") or {}
        ref_bbox_cell_area = bbox_cell_count(ref_bbox)
        summary["reference"] = {
            "layer_key": reference_layer_key,
            "closure_role": reference.get("closure_role"),
            "disagreement_decomposition_class": reference.get("disagreement_decomposition_class"),
            "high_uncertainty_cell_count": reference.get("high_uncertainty_cell_count"),
            "high_uncertainty_cell_fraction": reference.get("high_uncertainty_cell_fraction"),
            "high_uncertainty_support_nodata_fraction": reference.get("high_uncertainty_support_nodata_fraction"),
            "high_uncertainty_shared_support_magnitude_fraction": reference.get("high_uncertainty_shared_support_magnitude_fraction"),
            "high_uncertainty_bbox_cell_area": ref_bbox_cell_area,
            "high_uncertainty_bbox_compactness": (
                reference.get("high_uncertainty_cell_count", 0) / ref_bbox_cell_area if ref_bbox_cell_area else 0.0
            ),
            "stability_zone_class": reference.get("stability_zone_class"),
            "stability_zone_dominant_category": reference.get("stability_zone_dominant_category"),
        }
    return summary


def build_scientific_blocker_deltas(layer_roles: dict[str, Any]) -> list[dict[str, Any]]:
    reference_key = "velocity_exceedance_5mps"
    reference = layer_roles.get(reference_key, {})
    deltas: list[dict[str, Any]] = []
    for layer_key in ("max_kinetic_energy", "max_jump_height"):
        layer = layer_roles.get(layer_key, {})
        if not layer:
            continue
        deltas.append(
            {
                "layer_key": layer_key,
                "reference_layer_key": reference_key,
                "layer_closure_role": layer.get("closure_role"),
                "reference_closure_role": reference.get("closure_role"),
                "layer_disagreement_decomposition_class": layer.get("disagreement_decomposition_class"),
                "reference_disagreement_decomposition_class": reference.get("disagreement_decomposition_class"),
                "support_nodata_fraction_delta": float(layer.get("high_uncertainty_support_nodata_fraction", 0.0))
                - float(reference.get("high_uncertainty_support_nodata_fraction", 0.0)),
                "shared_support_magnitude_fraction_delta": float(layer.get("high_uncertainty_shared_support_magnitude_fraction", 0.0))
                - float(reference.get("high_uncertainty_shared_support_magnitude_fraction", 0.0)),
                "high_uncertainty_cell_count_delta": int(layer.get("high_uncertainty_cell_count", 0))
                - int(reference.get("high_uncertainty_cell_count", 0)),
                "high_uncertainty_cell_fraction_delta": float(layer.get("high_uncertainty_cell_fraction", 0.0))
                - float(reference.get("high_uncertainty_cell_fraction", 0.0)),
                "high_uncertainty_bbox_compactness_delta": float(layer.get("high_uncertainty_bbox_compactness", 0.0))
                - float(reference.get("high_uncertainty_bbox_compactness", 0.0)),
                "support_only_disagreement_count_delta": int(layer.get("support_only_disagreement_count", 0))
                - int(reference.get("support_only_disagreement_count", 0)),
                "nodata_disagreement_count_delta": int(layer.get("nodata_disagreement_count", 0))
                - int(reference.get("nodata_disagreement_count", 0)),
                "magnitude_only_disagreement_count_delta": int(layer.get("magnitude_only_disagreement_count", 0))
                - int(reference.get("magnitude_only_disagreement_count", 0)),
                "shared_support_magnitude_range_mean_delta": float(
                    layer.get("shared_support_magnitude_range_summary", {}).get("mean_range", 0.0)
                )
                - float(reference.get("shared_support_magnitude_range_summary", {}).get("mean_range", 0.0)),
            }
        )
    return deltas


def build_workflow_product_blocker_deltas(diagnostic_report: dict[str, Any]) -> list[dict[str, Any]]:
    output_profile = diagnostic_report.get("output_profile_status") or {}
    gis_cog = diagnostic_report.get("gis_cog_status") or {}
    portability = diagnostic_report.get("portability_status") or {}
    runtime = diagnostic_report.get("runtime_scaling_status") or {}
    return [
        {
            "blocker_key": "summary_only_not_rebuildable",
            "current_status": output_profile.get("target_summary_only"),
            "blocker_state": output_profile.get("validation_output_blocker_status") or output_profile.get("target_summary_only"),
            "delta_to_rebuildable_reduced": output_profile.get("target_rebuildable_reduced"),
            "local_rebuild_proof_status": (output_profile.get("same_scale_rebuild_evidence") or {}).get(
                "proof_status",
                "not_run",
            ),
            "blocker_narrowing_status": (output_profile.get("summary_only_blocker_narrowing") or {}).get(
                "summary_only_blocker_narrowing_status",
                "not_reduced_without_local_rebuild_proof",
            ),
            "evidence": (
                "trajectory CSV artifacts are absent from the legacy summary-only path; "
                "local rebuild proof narrows the blocker when the native rebuildable-reduced path executes"
            ),
        },
        {
            "blocker_key": "standard_gis_roots_cog_blocked",
            "current_status": gis_cog.get("standard_package_status"),
            "blocker_state": gis_cog.get("standard_package_status"),
            "delta_to_cog_ready": "ignored gate_v1_cog_poc audits as ready",
            "evidence": "standard raster roots remain strip-organized and lack overviews",
        },
        {
            "blocker_key": "public_context_inputs_deferred",
            "current_status": portability.get("portability_preflight_status"),
            "blocker_state": portability.get("portability_preflight_status"),
            "delta_to_public_context_ready": portability.get("missing_input_categories", []),
            "evidence": "Chant Sura / Flüelapass public-context inputs remain intentionally deferred",
        },
        {
            "blocker_key": "runtime_scaling_sufficient",
            "current_status": runtime.get("reducer_scaling_status"),
            "blocker_state": "satisfied",
            "delta_to_distributed_execution": runtime.get("distributed_execution_authorized"),
            "evidence": "local single-job execution remains sufficient for the next step",
        },
    ]


def summarize_claim_boundaries(diagnostic_report: dict[str, Any]) -> dict[str, Any]:
    claim_boundaries = dict(diagnostic_report.get("claim_boundaries") or {})
    claim_boundaries.setdefault("physical_probability_claims_allowed", False)
    claim_boundaries.setdefault("distributed_execution_authorized", False)
    claim_boundaries.setdefault("scale_up_authorized", False)
    claim_boundaries.setdefault("operational_claims_allowed", False)
    claim_boundaries.setdefault("annual_frequency_claims_allowed", False)
    claim_boundaries.setdefault("risk_exposure_vulnerability_claims_allowed", False)
    return claim_boundaries


def summarize_accepted_gap(
    diagnostic_report: dict[str, Any],
    closure_limiting_layers: list[dict[str, Any]],
    workflow_product_blocker_deltas: list[dict[str, Any]],
) -> dict[str, Any]:
    blockers = list(diagnostic_report.get("dominant_scientific_blockers", []))
    blockers.extend(
        item["blocker_key"]
        for item in workflow_product_blocker_deltas
        if item["blocker_key"] in {"summary_only_not_rebuildable", "standard_gis_roots_cog_blocked", "public_context_inputs_deferred"}
    )
    return {
        "status": "not_met",
        "current_classification": diagnostic_report.get("interpretation_status"),
        "blocking_scientific_fields": blockers,
        "blocking_layers": [item["layer_key"] for item in closure_limiting_layers],
        "required_state": "accepted_diagnostic",
        "note": "accepted diagnostic remains unsupported because closure is inconclusive and the dominant layers stay closure-limiting.",
    }


def summarize_deferred_gap(
    diagnostic_report: dict[str, Any],
    closure_limiting_layers: list[dict[str, Any]],
    deferrable_layers: list[dict[str, Any]],
) -> dict[str, Any]:
    reference_layers = [item["layer_key"] for item in deferrable_layers]
    return {
        "status": "closer_to_deferred_than_no_go",
        "current_classification": diagnostic_report.get("interpretation_status"),
        "supporting_layers": reference_layers,
        "residual_closure_limiting_layers": [item["layer_key"] for item in closure_limiting_layers],
        "note": "the evidence is localized and bounded, and the deferrable velocity layer demonstrates the gap is not diffuse enough to justify no-go.",
    }


def summarize_no_go_gap(
    diagnostic_report: dict[str, Any],
    closure_limiting_layers: list[dict[str, Any]],
    workflow_product_blocker_deltas: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "status": "not_supported_by_current_evidence",
        "current_classification": diagnostic_report.get("interpretation_status"),
        "would_require": [
            "persistent diffuse spatial disagreement rather than localized high-uncertainty cells",
            "support/nodata dominance that cannot be localized into measured closure-gap deltas",
            "workflow/product blockers that are not bounded by the current reduced-output and COG proof paths",
        ],
        "blocking_layers": [item["layer_key"] for item in closure_limiting_layers],
        "blocking_workflow_products": [item["blocker_key"] for item in workflow_product_blocker_deltas if item["blocker_key"] != "runtime_scaling_sufficient"],
        "note": "current evidence is bounded and measured, so the report stays conservative and closer to deferred than to no-go.",
    }


def summarize_candidate_runout_failure(evidence_override: dict[str, Any] | None = None) -> dict[str, Any]:
    if evidence_override and isinstance(evidence_override.get("candidate_runout_failure_diagnostic"), dict):
        return dict(evidence_override["candidate_runout_failure_diagnostic"])

    record_path = DEFAULT_CANDIDATE_LOCAL_COMPARISON_RECORD
    if evidence_override and evidence_override.get("candidate_local_comparison_record"):
        record_path = resolve_repo_path(Path(str(evidence_override["candidate_local_comparison_record"])))

    if not record_path.exists():
        return {
            "diagnostic_status": "blocked_missing_inputs",
            "blocked_reason": f"candidate local comparison record is missing: {display_path(record_path)}",
            "missing_inputs": [display_path(record_path)],
            "dominant_failure_mode": "unknown",
            "smallest_next_scientific_action": "restore or rerun the local candidate comparison before diagnosing failure mode",
        }

    record = load_yaml(record_path)
    inputs = dict(record.get("inputs") or {})
    candidate_smoke = dict(record.get("candidate_local_smoke") or {})
    prior_baselines = dict(record.get("prior_baselines") or {})
    local_baseline = dict(prior_baselines.get("observed_release_local_baseline") or {})
    required_paths = {
        "reviewed_release_rows": resolve_repo_path(Path(str(inputs.get("reviewed_release_rows") or ""))),
        "generated_release_points": ROOT / "validation/results/tb484_candidate_local_comparison/generated_release_points.csv",
        "simulated_deposition": ROOT / "validation/results/tb484_candidate_local_comparison/ensemble_deposition.csv",
        "observed_deposition": resolve_repo_path(Path(str(inputs.get("observed_deposition") or ""))),
    }
    missing = [display_path(path) for path in required_paths.values() if not path.exists()]
    if missing:
        return {
            "diagnostic_status": "blocked_missing_inputs",
            "blocked_reason": "candidate runout diagnostic needs local comparison scratch outputs",
            "missing_inputs": missing,
            "dominant_failure_mode": "unknown",
            "smallest_next_scientific_action": "rerun the TB-484 local comparison scratch case before diagnosing failure mode",
            "record_path": display_path(record_path),
        }

    generated_release_rows = read_csv_rows(required_paths["generated_release_points"])
    reviewed_release_rows = read_csv_rows(required_paths["reviewed_release_rows"])
    simulated_deposition_rows = read_csv_rows(required_paths["simulated_deposition"])
    observed_deposition_rows = read_csv_rows(required_paths["observed_deposition"])
    candidate_release_centroid = centroid_xy(generated_release_rows)
    reviewed_release_centroid = centroid_xy(reviewed_release_rows)
    simulated_deposition_centroid = centroid_xy(simulated_deposition_rows)
    observed_deposition_centroid = centroid_xy(observed_deposition_rows)
    observed_release_centroid = centroid_xy(
        observed_deposition_rows,
        x_key="release_x_m",
        y_key="release_y_m",
    )

    observed_mean_runout = float(candidate_smoke.get("observed_mean_runout_m") or 0.0)
    simulated_mean_runout = float(candidate_smoke.get("simulated_mean_runout_m") or 0.0)
    local_baseline_runout_error = float(local_baseline.get("runout_distance_error_m") or 0.0)
    candidate_runout_error = float(candidate_smoke.get("runout_distance_error_m") or 0.0)
    source_displacement = distance_xy(candidate_release_centroid, observed_release_centroid)
    local_stopping_distance = distance_xy(candidate_release_centroid, simulated_deposition_centroid)
    observed_transport_distance = distance_xy(observed_release_centroid, observed_deposition_centroid)
    centroid_error = distance_xy(simulated_deposition_centroid, observed_deposition_centroid)
    runout_ratio = simulated_mean_runout / observed_mean_runout if observed_mean_runout else 0.0
    source_displacement_fraction = source_displacement / observed_mean_runout if observed_mean_runout else 0.0
    local_stopping_fraction = local_stopping_distance / observed_mean_runout if observed_mean_runout else 0.0

    dominant_failure_mode = classify_candidate_failure_mode(
        runout_ratio=runout_ratio,
        source_displacement_fraction=source_displacement_fraction,
        centroid_error=centroid_error,
        source_displacement=source_displacement,
    )
    return {
        "diagnostic_status": "ready",
        "record_path": display_path(record_path),
        "dominant_failure_mode": dominant_failure_mode,
        "smallest_next_scientific_action": next_candidate_failure_action(dominant_failure_mode),
        "interpretation": (
            "the reviewed adjacent candidate is spatially displaced from the observed release cloud and the local "
            "simulation stops almost immediately, so the failed comparison should not be treated as a physics "
            "calibration target without first revisiting source interpretation"
        ),
        "candidate_vs_observed_geometry": {
            "candidate_release_centroid_xy": candidate_release_centroid,
            "reviewed_release_centroid_xy": reviewed_release_centroid,
            "observed_release_centroid_xy": observed_release_centroid,
            "observed_deposition_centroid_xy": observed_deposition_centroid,
            "simulated_deposition_centroid_xy": simulated_deposition_centroid,
            "candidate_release_to_observed_release_centroid_m": round(source_displacement, 6),
            "candidate_release_to_observed_deposition_centroid_m": round(
                distance_xy(candidate_release_centroid, observed_deposition_centroid),
                6,
            ),
            "simulated_deposition_to_observed_deposition_centroid_m": round(centroid_error, 6),
            "candidate_local_stopping_distance_m": round(local_stopping_distance, 6),
            "observed_release_to_observed_deposition_centroid_m": round(observed_transport_distance, 6),
        },
        "runout_diagnostics": {
            "observed_mean_runout_m": observed_mean_runout,
            "simulated_mean_runout_m": simulated_mean_runout,
            "simulated_to_observed_runout_ratio": round(runout_ratio, 6),
            "source_displacement_fraction_of_observed_runout": round(source_displacement_fraction, 6),
            "local_stopping_fraction_of_observed_runout": round(local_stopping_fraction, 6),
            "runout_distance_error_m": candidate_runout_error,
            "runout_error_delta_vs_observed_release_local_baseline_m": round(
                candidate_runout_error - local_baseline_runout_error,
                6,
            ),
            "deposition_cloud_overlap_fraction": float(candidate_smoke.get("deposition_cloud_overlap_fraction") or 0.0),
        },
        "evidence_counts": {
            "generated_release_point_count": len(generated_release_rows),
            "reviewed_release_row_count": len(reviewed_release_rows),
            "simulated_deposition_point_count": len(simulated_deposition_rows),
            "observed_deposition_point_count": len(observed_deposition_rows),
        },
        "claim_boundaries": {
            "diagnostic_only": True,
            "candidate_acceptance_upgrade": False,
            "parameter_tuning_authorized": False,
            "operational_claims_allowed": False,
            "physical_probability_claims_allowed": False,
        },
    }


def summarize_candidate_geometry_ablation(evidence_override: dict[str, Any] | None = None) -> dict[str, Any]:
    if evidence_override and isinstance(evidence_override.get("candidate_geometry_ablation"), dict):
        return dict(evidence_override["candidate_geometry_ablation"])

    record_path = DEFAULT_CANDIDATE_LOCAL_COMPARISON_RECORD
    if evidence_override and evidence_override.get("candidate_local_comparison_record"):
        record_path = resolve_repo_path(Path(str(evidence_override["candidate_local_comparison_record"])))

    if not record_path.exists():
        return blocked_candidate_geometry_ablation(
            f"candidate local comparison record is missing: {display_path(record_path)}",
            [display_path(record_path)],
        )

    record = load_yaml(record_path)
    candidate_smoke = dict(record.get("candidate_local_smoke") or {})
    prior_baselines = dict(record.get("prior_baselines") or {})
    source_aligned = dict(prior_baselines.get("observed_release_local_baseline") or {})
    missing_fields = required_ablation_fields(candidate_smoke, source_aligned)
    if missing_fields:
        return blocked_candidate_geometry_ablation(
            "candidate/source-aligned comparison metrics are incomplete",
            missing_fields,
        )

    candidate_variant = build_ablation_variant("candidate_aligned_reviewed_source", candidate_smoke)
    source_variant = build_ablation_variant("source_aligned_observed_release_baseline", source_aligned)
    deltas = {
        "runout_distance_error_delta_candidate_minus_source_aligned_m": round(
            candidate_variant["runout_distance_error_m"] - source_variant["runout_distance_error_m"],
            6,
        ),
        "deposition_centroid_error_delta_candidate_minus_source_aligned_m": round(
            candidate_variant["deposition_centroid_error_m"] - source_variant["deposition_centroid_error_m"],
            6,
        ),
        "deposition_overlap_delta_candidate_minus_source_aligned": round(
            candidate_variant["deposition_cloud_overlap_fraction"] - source_variant["deposition_cloud_overlap_fraction"],
            6,
        ),
        "simulated_to_observed_runout_ratio_delta_candidate_minus_source_aligned": round(
            candidate_variant["simulated_to_observed_runout_ratio"] - source_variant["simulated_to_observed_runout_ratio"],
            6,
        ),
        "endpoint_cloud_mean_nearest_error_delta_candidate_minus_source_aligned_m": round(
            candidate_variant["endpoint_cloud_shape"]["mean_nearest_error_m"]
            - source_variant["endpoint_cloud_shape"]["mean_nearest_error_m"],
            6,
        ),
        "endpoint_lateral_spread_error_delta_candidate_minus_source_aligned_m": round(
            candidate_variant["endpoint_cloud_shape"]["lateral_spread_error_m"]
            - source_variant["endpoint_cloud_shape"]["lateral_spread_error_m"],
            6,
        ),
        "endpoint_shape_error_delta_candidate_minus_source_aligned_m": round(
            candidate_variant["endpoint_cloud_shape"]["shape_error_m"]
            - source_variant["endpoint_cloud_shape"]["shape_error_m"],
            6,
        ),
    }
    dominant_effect = classify_candidate_geometry_ablation(candidate_variant, source_variant, deltas)
    endpoint_shape_interpretation = classify_endpoint_shape_delta(candidate_variant, source_variant, deltas)
    return {
        "ablation_status": "fixture_replay_ready",
        "record_path": display_path(record_path),
        "dominant_effect": dominant_effect,
        "endpoint_shape_interpretation": endpoint_shape_interpretation,
        "source_aligned_variant": source_variant,
        "candidate_aligned_variant": candidate_variant,
        "deltas": deltas,
        "smallest_next_scientific_action": next_candidate_geometry_ablation_action(dominant_effect),
        "interpretation": (
            "the fixture replay compares the candidate-aligned local smoke with the observed-release local "
            "baseline as the source-aligned variant; this separates geometry placement from a full physics "
            "or parameter-tuning experiment"
        ),
        "claim_boundaries": {
            "fixture_replay_only": True,
            "candidate_acceptance_upgrade": False,
            "parameter_tuning_authorized": False,
            "operational_claims_allowed": False,
            "physical_probability_claims_allowed": False,
        },
    }


def blocked_candidate_geometry_ablation(reason: str, missing_inputs: list[str]) -> dict[str, Any]:
    return {
        "ablation_status": "blocked_missing_inputs",
        "blocked_reason": reason,
        "missing_inputs": missing_inputs,
        "dominant_effect": "unknown",
        "smallest_next_scientific_action": "restore the local comparison record or rerun the candidate/local baseline pair",
        "claim_boundaries": {
            "fixture_replay_only": True,
            "candidate_acceptance_upgrade": False,
            "parameter_tuning_authorized": False,
            "operational_claims_allowed": False,
            "physical_probability_claims_allowed": False,
        },
    }


def required_ablation_fields(candidate: dict[str, Any], source_aligned: dict[str, Any]) -> list[str]:
    required = (
        "observed_mean_runout_m",
        "simulated_mean_runout_m",
        "runout_distance_error_m",
        "deposition_centroid_error_m",
        "deposition_cloud_overlap_fraction",
    )
    missing: list[str] = []
    for label, metrics in (
        ("candidate_local_smoke", candidate),
        ("prior_baselines.observed_release_local_baseline", source_aligned),
    ):
        for field in required:
            if metrics.get(field) is None:
                missing.append(f"{label}.{field}")
    return missing


def build_ablation_variant(label: str, metrics: dict[str, Any]) -> dict[str, Any]:
    observed_runout = float(metrics.get("observed_mean_runout_m") or 0.0)
    simulated_runout = float(metrics.get("simulated_mean_runout_m") or 0.0)
    return {
        "variant_id": label,
        "observed_mean_runout_m": observed_runout,
        "simulated_mean_runout_m": simulated_runout,
        "simulated_to_observed_runout_ratio": round(simulated_runout / observed_runout, 6) if observed_runout else 0.0,
        "runout_distance_error_m": float(metrics.get("runout_distance_error_m") or 0.0),
        "deposition_centroid_error_m": float(metrics.get("deposition_centroid_error_m") or 0.0),
        "deposition_cloud_overlap_fraction": float(metrics.get("deposition_cloud_overlap_fraction") or 0.0),
        "endpoint_cloud_shape": endpoint_cloud_shape_from_metrics(metrics),
    }


def endpoint_cloud_shape_from_metrics(metrics: dict[str, Any]) -> dict[str, float]:
    mean_nearest = float(metrics.get("deposition_cloud_mean_nearest_error_m") or 0.0)
    lateral_spread = float(metrics.get("lateral_spread_error_m") or 0.0)
    centroid_error = float(metrics.get("deposition_centroid_error_m") or 0.0)
    shape_error = mean_nearest + abs(lateral_spread)
    return {
        "mean_nearest_error_m": mean_nearest,
        "lateral_spread_error_m": lateral_spread,
        "shape_error_m": round(shape_error, 6),
        "shape_to_centroid_error_ratio": round(shape_error / centroid_error, 6) if centroid_error else 0.0,
    }


def endpoint_cloud_metrics(
    simulated_rows: list[dict[str, Any]],
    observed_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    simulated_points = valid_xy_points(simulated_rows)
    observed_points = valid_xy_points(observed_rows)
    if not simulated_points or not observed_points:
        return {
            "metric_status": "blocked_missing_points",
            "simulated_point_count": len(simulated_points),
            "observed_point_count": len(observed_points),
        }
    simulated_spread = point_cloud_spread(simulated_points)
    observed_spread = point_cloud_spread(observed_points)
    nearest = nearest_neighbor_distances(simulated_points, observed_points)
    return {
        "metric_status": "ready",
        "simulated_point_count": len(simulated_points),
        "observed_point_count": len(observed_points),
        "mean_nearest_error_m": round(sum(nearest) / len(nearest), 6),
        "p95_nearest_error_m": round(percentile(nearest, 0.95), 6),
        "simulated_radial_spread_rms_m": round(simulated_spread["radial_spread_rms_m"], 6),
        "observed_radial_spread_rms_m": round(observed_spread["radial_spread_rms_m"], 6),
        "radial_spread_error_m": round(abs(simulated_spread["radial_spread_rms_m"] - observed_spread["radial_spread_rms_m"]), 6),
        "simulated_orientation_deg": round(simulated_spread["orientation_deg"], 6),
        "observed_orientation_deg": round(observed_spread["orientation_deg"], 6),
        "orientation_difference_deg": round(
            orientation_difference_deg(simulated_spread["orientation_deg"], observed_spread["orientation_deg"]),
            6,
        ),
    }


def valid_xy_points(rows: list[dict[str, Any]]) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    for row in rows:
        xy = row_xy(row)
        if xy is not None:
            points.append(xy)
    return points


def nearest_neighbor_distances(
    simulated_points: list[tuple[float, float]],
    observed_points: list[tuple[float, float]],
) -> list[float]:
    return [
        min(math.hypot(x - obs_x, y - obs_y) for obs_x, obs_y in observed_points)
        for x, y in simulated_points
    ]


def point_cloud_spread(points: list[tuple[float, float]]) -> dict[str, float]:
    centroid_x = sum(x for x, _ in points) / len(points)
    centroid_y = sum(y for _, y in points) / len(points)
    centered = [(x - centroid_x, y - centroid_y) for x, y in points]
    radial_spread_rms = math.sqrt(sum(x * x + y * y for x, y in centered) / len(centered))
    if len(points) < 2:
        return {"radial_spread_rms_m": radial_spread_rms, "orientation_deg": 0.0}
    xx = sum(x * x for x, _ in centered) / len(centered)
    yy = sum(y * y for _, y in centered) / len(centered)
    xy = sum(x * y for x, y in centered) / len(centered)
    orientation = 0.5 * math.degrees(math.atan2(2.0 * xy, xx - yy))
    if orientation < 0.0:
        orientation += 180.0
    return {"radial_spread_rms_m": radial_spread_rms, "orientation_deg": orientation}


def percentile(values: list[float], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, math.ceil(fraction * len(ordered)) - 1))
    return ordered[index]


def orientation_difference_deg(left: float, right: float) -> float:
    raw = abs(left - right) % 180.0
    return min(raw, 180.0 - raw)


def classify_endpoint_shape_delta(
    candidate_variant: dict[str, Any],
    source_variant: dict[str, Any],
    deltas: dict[str, float],
) -> str:
    centroid_delta = deltas["deposition_centroid_error_delta_candidate_minus_source_aligned_m"]
    shape_delta = deltas["endpoint_shape_error_delta_candidate_minus_source_aligned_m"]
    spread_delta = deltas["endpoint_lateral_spread_error_delta_candidate_minus_source_aligned_m"]
    overlap_delta = deltas["deposition_overlap_delta_candidate_minus_source_aligned"]
    candidate_shape = candidate_variant["endpoint_cloud_shape"]
    source_shape = source_variant["endpoint_cloud_shape"]
    if centroid_delta > 50.0 and shape_delta > 50.0 and overlap_delta < -0.1:
        return "centroid_and_endpoint_shape_degrade_together"
    if centroid_delta < -20.0 and shape_delta > 20.0:
        return "centroid_improves_but_endpoint_shape_degrades"
    if centroid_delta > 20.0 and shape_delta <= 0.0:
        return "centroid_degrades_without_endpoint_shape_degradation"
    if abs(spread_delta) > 20.0 and candidate_shape["shape_error_m"] > source_shape["shape_error_m"]:
        return "spread_failure_dominates_endpoint_shape"
    return "endpoint_shape_delta_inconclusive"


def classify_candidate_geometry_ablation(
    candidate_variant: dict[str, Any],
    source_variant: dict[str, Any],
    deltas: dict[str, float],
) -> str:
    source_geometry_improves = (
        deltas["deposition_centroid_error_delta_candidate_minus_source_aligned_m"] >= 100.0
        and deltas["runout_distance_error_delta_candidate_minus_source_aligned_m"] >= 30.0
        and deltas["deposition_overlap_delta_candidate_minus_source_aligned"] <= -0.25
    )
    candidate_early_stops = candidate_variant["simulated_to_observed_runout_ratio"] < 0.25
    source_early_stops = source_variant["simulated_to_observed_runout_ratio"] < 0.25
    if source_geometry_improves and candidate_early_stops and not source_early_stops:
        return "source_offset_dominates_with_candidate_local_stopping_signal"
    if source_geometry_improves:
        return "source_offset_dominates"
    if candidate_early_stops and source_early_stops:
        return "terrain_contact_stopping_dominates"
    if candidate_early_stops:
        return "candidate_local_stopping_signal_without_source_offset_dominance"
    return "inconclusive_geometry_ablation"


def next_candidate_geometry_ablation_action(dominant_effect: str) -> str:
    if dominant_effect == "source_offset_dominates_with_candidate_local_stopping_signal":
        return "test a source-aligned reviewed candidate before any physics tuning; preserve candidate local-stopping diagnostics as secondary evidence"
    if dominant_effect == "source_offset_dominates":
        return "prioritize source interpretation and reviewed candidate placement before contact or parameter changes"
    if dominant_effect == "terrain_contact_stopping_dominates":
        return "inspect terrain/contact stopping behavior on matched source geometry before evaluating new candidate polygons"
    return "rerun a paired candidate/source-aligned local comparison with the same output metrics"


def classify_candidate_failure_mode(
    *,
    runout_ratio: float,
    source_displacement_fraction: float,
    centroid_error: float,
    source_displacement: float,
) -> str:
    early_stop = runout_ratio < 0.25
    source_displaced = source_displacement_fraction > 0.75 or source_displacement > 75.0
    if source_displaced and early_stop:
        return "source_placement_displaced_with_local_early_stopping"
    if source_displaced:
        return "source_placement_displaced"
    if early_stop:
        return "local_early_stopping_or_excess_dissipation"
    if centroid_error > 50.0:
        return "deposition_centroid_displaced"
    return "inconclusive_candidate_failure_mode"


def next_candidate_failure_action(dominant_failure_mode: str) -> str:
    if dominant_failure_mode == "source_placement_displaced_with_local_early_stopping":
        return "compare an alternate reviewed candidate and inspect candidate-source placement before any physics tuning"
    if dominant_failure_mode == "source_placement_displaced":
        return "review candidate-source placement against observed release geometry before reusing the candidate for validation"
    if dominant_failure_mode == "local_early_stopping_or_excess_dissipation":
        return "inspect contact/terrain stopping behavior on the same candidate after source geometry is confirmed"
    return "add a second local candidate comparison to separate source and physics failure modes"


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def centroid_xy(rows: list[dict[str, Any]], *, x_key: str = "x_m", y_key: str = "y_m") -> dict[str, float]:
    xs: list[float] = []
    ys: list[float] = []
    for row in rows:
        xy = row_xy(row, x_key=x_key, y_key=y_key)
        if xy is None:
            continue
        x, y = xy
        xs.append(x)
        ys.append(y)
    if not xs or not ys:
        return {"x_m": 0.0, "y_m": 0.0}
    return {
        "x_m": round(sum(xs) / len(xs), 6),
        "y_m": round(sum(ys) / len(ys), 6),
    }


def row_xy(row: dict[str, Any], *, x_key: str = "x_m", y_key: str = "y_m") -> tuple[float, float] | None:
    try:
        x = float(row.get(x_key) or "")
        y = float(row.get(y_key) or "")
    except (TypeError, ValueError):
        center = row.get("release_cell_center_lv95_m")
        if not center:
            return None
        try:
            values = json.loads(str(center))
            x = float(values[0])
            y = float(values[1])
        except (TypeError, ValueError, json.JSONDecodeError, IndexError):
            return None
    if not math.isfinite(x) or not math.isfinite(y):
        return None
    return x, y


def distance_xy(left: dict[str, float], right: dict[str, float]) -> float:
    return math.hypot(
        float(left.get("x_m", 0.0)) - float(right.get("x_m", 0.0)),
        float(left.get("y_m", 0.0)) - float(right.get("y_m", 0.0)),
    )


def resolve_repo_path(path: Path) -> Path:
    if path.is_absolute():
        return path
    return ROOT / path


def display_path(path: Path) -> str:
    resolved = path.resolve(strict=False)
    try:
        return str(resolved.relative_to(ROOT))
    except ValueError:
        return str(resolved)


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def bbox_cell_count(bbox: dict[str, Any]) -> int:
    if not bbox:
        return 0
    row_min = bbox.get("row_min")
    row_max = bbox.get("row_max")
    col_min = bbox.get("col_min")
    col_max = bbox.get("col_max")
    if None in {row_min, row_max, col_min, col_max}:
        return 0
    try:
        return max(0, int(row_max) - int(row_min) + 1) * max(0, int(col_max) - int(col_min) + 1)
    except (TypeError, ValueError):
        return 0


def blocked_report(missing_inputs: list[str], *, reason: str) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "closure_gap_status": "blocked_missing_inputs",
        "current_closure_status": "blocked_missing_inputs",
        "current_interpretation_status": "blocked_missing_inputs",
        "same_scale_readiness_status": "blocked_missing_inputs",
        "closure_limiting_layers": [],
        "deferrable_layers": [],
        "scientific_blocker_deltas": [],
        "workflow_product_blocker_deltas": [],
        "accepted_diagnostic_gap": {"status": "blocked_missing_inputs", "missing_inputs": missing_inputs},
        "deferred_gap": {"status": "blocked_missing_inputs", "missing_inputs": missing_inputs},
        "no_go_gap": {"status": "blocked_missing_inputs", "missing_inputs": missing_inputs},
        "candidate_runout_failure_diagnostic": {
            "diagnostic_status": "blocked_missing_inputs",
            "missing_inputs": missing_inputs,
            "dominant_failure_mode": "unknown",
            "smallest_next_scientific_action": "restore required evidence inputs before diagnosing candidate runout failure",
        },
        "candidate_geometry_ablation": blocked_candidate_geometry_ablation(
            "required evidence inputs are missing",
            missing_inputs,
        ),
        "claim_boundaries": {
            "scale_up_authorized": False,
            "operational_claims_allowed": False,
            "annual_frequency_claims_allowed": False,
            "risk_exposure_vulnerability_claims_allowed": False,
            "distributed_execution_authorized": False,
            "physical_probability_claims_allowed": False,
        },
        "current_evidence": {},
        "scale_up_authorized": False,
        "operational_claims_allowed": False,
        "annual_frequency_claims_allowed": False,
        "risk_exposure_vulnerability_claims_allowed": False,
        "distributed_execution_authorized": False,
        "physical_probability_claims_allowed": False,
        "blocked_reason": reason + ": " + ", ".join(missing_inputs),
        "missing_inputs": missing_inputs,
    }


def render_text_report(report: dict[str, Any]) -> str:
    lines = [
        f"closure_gap_status: {report['closure_gap_status']}",
        f"current_closure_status: {report['current_closure_status']}",
        f"current_interpretation_status: {report['current_interpretation_status']}",
        "closure_limiting_layers:",
    ]
    for item in report.get("closure_limiting_layers", []):
        lines.append(
            "  - "
            + item["layer_key"]
            + f" | role={item['closure_role']}"
            + f" | stability={item.get('stability_zone_class')}"
            + f" | class={item['disagreement_decomposition_class']}"
            + f" | support/nodata={item['high_uncertainty_support_nodata_fraction']:.6g}"
            + f" | shared-support magnitude={item['high_uncertainty_shared_support_magnitude_fraction']:.6g}"
        )
    lines.append("deferrable_layers:")
    for item in report.get("deferrable_layers", []):
        lines.append(
            "  - "
            + item["layer_key"]
            + f" | role={item['closure_role']}"
            + f" | stability={item.get('stability_zone_class')}"
            + f" | class={item['disagreement_decomposition_class']}"
            + f" | support/nodata={item['high_uncertainty_support_nodata_fraction']:.6g}"
            + f" | shared-support magnitude={item['high_uncertainty_shared_support_magnitude_fraction']:.6g}"
        )
    lines.append("scientific_blocker_deltas:")
    for item in report.get("scientific_blocker_deltas", []):
        lines.append(
            f"  - {item['layer_key']} vs {item['reference_layer_key']}"
            + f" | role={item['layer_closure_role']}->{item['reference_closure_role']}"
            + f" | support/nodata_delta={item['support_nodata_fraction_delta']:.6g}"
            + f" | shared-support_delta={item['shared_support_magnitude_fraction_delta']:.6g}"
            + f" | compactness_delta={item['high_uncertainty_bbox_compactness_delta']:.6g}"
        )
    lines.append("workflow_product_blocker_deltas:")
    for item in report.get("workflow_product_blocker_deltas", []):
        lines.append(
            f"  - {item['blocker_key']}"
            + f" | current={item['current_status']}"
            + f" | blocker_state={item['blocker_state']}"
            + f" | evidence={item['evidence']}"
        )
    lines.append(f"accepted_diagnostic_gap: {json.dumps(report['accepted_diagnostic_gap'], sort_keys=True)}")
    lines.append(f"deferred_gap: {json.dumps(report['deferred_gap'], sort_keys=True)}")
    lines.append(f"no_go_gap: {json.dumps(report['no_go_gap'], sort_keys=True)}")
    candidate = report.get("candidate_runout_failure_diagnostic", {})
    runout = candidate.get("runout_diagnostics") or {}
    geometry = candidate.get("candidate_vs_observed_geometry") or {}
    lines.append("candidate_runout_failure_diagnostic:")
    lines.append(
        "  - "
        + f"status={candidate.get('diagnostic_status', 'unknown')}"
        + f" | dominant_failure_mode={candidate.get('dominant_failure_mode', 'unknown')}"
        + f" | runout_ratio={runout.get('simulated_to_observed_runout_ratio', 'unknown')}"
        + " | release_offset_m="
        + str(geometry.get("candidate_release_to_observed_release_centroid_m", "unknown"))
        + f" | next_action={candidate.get('smallest_next_scientific_action', 'unknown')}"
    )
    ablation = report.get("candidate_geometry_ablation", {})
    ablation_deltas = ablation.get("deltas") or {}
    lines.append("candidate_geometry_ablation:")
    lines.append(
        "  - "
        + f"status={ablation.get('ablation_status', 'unknown')}"
        + f" | dominant_effect={ablation.get('dominant_effect', 'unknown')}"
        + f" | endpoint_shape={ablation.get('endpoint_shape_interpretation', 'unknown')}"
        + " | centroid_delta_m="
        + str(ablation_deltas.get("deposition_centroid_error_delta_candidate_minus_source_aligned_m", "unknown"))
        + " | shape_delta_m="
        + str(ablation_deltas.get("endpoint_shape_error_delta_candidate_minus_source_aligned_m", "unknown"))
        + " | runout_error_delta_m="
        + str(ablation_deltas.get("runout_distance_error_delta_candidate_minus_source_aligned_m", "unknown"))
        + f" | next_action={ablation.get('smallest_next_scientific_action', 'unknown')}"
    )
    lines.append(f"claim_boundaries: {json.dumps(report['claim_boundaries'], sort_keys=True)}")
    lines.append(f"scale_up_authorized: {str(report['scale_up_authorized']).lower()}")
    lines.append(f"operational_claims_allowed: {str(report['operational_claims_allowed']).lower()}")
    lines.append(f"annual_frequency_claims_allowed: {str(report['annual_frequency_claims_allowed']).lower()}")
    lines.append(
        f"risk_exposure_vulnerability_claims_allowed: {str(report['risk_exposure_vulnerability_claims_allowed']).lower()}"
    )
    lines.append(f"distributed_execution_authorized: {str(report['distributed_execution_authorized']).lower()}")
    lines.append(f"physical_probability_claims_allowed: {str(report['physical_probability_claims_allowed']).lower()}")
    return "\n".join(lines)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
