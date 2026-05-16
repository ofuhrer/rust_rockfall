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
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "tschamut_closure_gap_deltas_v1"


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
        "claim_boundaries": claim_boundaries,
        "current_evidence": {
            "closure": closure_report,
            "spatial_uncertainty": spatial,
            "output_profile_status": diagnostic_report.get("output_profile_status", {}),
            "gis_cog_status": diagnostic_report.get("gis_cog_status", {}),
            "runtime_scaling_status": diagnostic_report.get("runtime_scaling_status", {}),
            "portability_status": diagnostic_report.get("portability_status", {}),
            "physical_credibility_status": diagnostic_report.get("physical_credibility_status", "unknown"),
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
            "evidence": "trajectory CSV artifacts are absent from the summary-only path",
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
