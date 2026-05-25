#!/usr/bin/env python3
"""Summarize local sensitivity for the most fragile extreme hazard layers.

The helper is read-only. It compares existing same-scale hazard manifests for
max kinetic energy and max jump height only. It does not run ensembles, tune
parameters, or upgrade conditional diagnostics into physical, annual-frequency,
operational, risk, or scale-up claims.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import compare_hazard_map_convergence as convergence


SCHEMA_VERSION = "extreme_layer_sensitivity_smoke_v1"
DEFAULT_GATE_MANIFEST = ROOT / "hazard/results/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_manifest.json"
DEFAULT_TARGET_MANIFEST = ROOT / "hazard/results/tschamut_public_pilot/target_gate_v1/validation_tschamut_public_target_gate_v1_manifest.json"
EXTREME_LAYERS = ("max_kinetic_energy", "max_jump_height")
EXTREME_SUPPORT_LAYERS = {
    "max_kinetic_energy": "max_kinetic_energy_sample_count",
    "max_jump_height": "max_jump_height_sample_count",
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gate-manifest", type=Path, default=DEFAULT_GATE_MANIFEST)
    parser.add_argument("--target-manifest", type=Path, default=DEFAULT_TARGET_MANIFEST)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    args = parser.parse_args(argv)

    report = build_report(gate_manifest=args.gate_manifest, target_manifest=args.target_manifest)
    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text_report(report))
    return 0 if report["smoke_status"] == "measured" else 2


def build_report(*, gate_manifest: Path = DEFAULT_GATE_MANIFEST, target_manifest: Path = DEFAULT_TARGET_MANIFEST) -> dict[str, Any]:
    try:
        gate = convergence.resolve_manifest(gate_manifest)
        target = convergence.resolve_manifest(target_manifest)
        gate_layers = convergence.cellwise_layer_index(gate)
        target_layers = convergence.cellwise_layer_index(target)
    except convergence.HazardMapConvergenceInputError as exc:
        return blocked_report(
            status=exc.status,
            gate_manifest=gate_manifest,
            target_manifest=target_manifest,
            reason=str(exc),
            requested_path=exc.requested_path,
        )
    except convergence.HazardMapConvergenceDiagnosticError as exc:
        return blocked_report(
            status=convergence.BLOCKED_INVALID_INPUTS,
            gate_manifest=gate_manifest,
            target_manifest=target_manifest,
            reason=str(exc),
            requested_path=target_manifest,
        )

    missing_layers = [
        {
            "layer_key": layer_key,
            "gate_present": layer_key in gate_layers,
            "target_present": layer_key in target_layers,
            "presence_status": layer_presence_status(layer_key, gate_layers, target_layers),
        }
        for layer_key in EXTREME_LAYERS
        if layer_key not in gate_layers or layer_key not in target_layers
    ]
    if missing_layers:
        return {
            **base_report(gate_manifest=gate_manifest, target_manifest=target_manifest),
            "smoke_status": "blocked_missing_extreme_layers",
            "missing_layers": missing_layers,
            "layer_summaries": [
                missing_layer_summary(item) for item in missing_layers
            ],
            "overall_metrics": empty_overall_metrics(),
            "next_measurement": "Restore both extreme layers in the gate and target manifests before measuring sensitivity.",
        }

    layer_summaries = []
    for layer_key in EXTREME_LAYERS:
        comparison = convergence.compare_cellwise_layer(gate_layers[layer_key], target_layers[layer_key])
        support_layer_key = EXTREME_SUPPORT_LAYERS[layer_key]
        layer_summaries.append(
            summarize_layer(
                comparison,
                sample_support_delta=summarize_sample_support_delta(
                    layer_key=layer_key,
                    support_layer_key=support_layer_key,
                    gate_layer=gate_layers.get(support_layer_key),
                    target_layer=target_layers.get(support_layer_key),
                ),
            )
        )

    return {
        **base_report(gate_manifest=gate_manifest, target_manifest=target_manifest),
        "smoke_status": "measured",
        "missing_layers": [],
        "layer_summaries": layer_summaries,
        "overall_metrics": summarize_overall(layer_summaries),
        "next_measurement": "Use this smoke to target the next local sensitivity check at support/nodata and maximum-reduction behavior.",
    }


def base_report(*, gate_manifest: Path, target_manifest: Path) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "gate_manifest": str(gate_manifest),
        "target_manifest": str(target_manifest),
        "selected_layers": list(EXTREME_LAYERS),
        "claim_boundaries": {
            "annual_frequency_claims_allowed": False,
            "operational_claims_allowed": False,
            "physical_probability_claims_allowed": False,
            "risk_exposure_vulnerability_claims_allowed": False,
            "scale_up_authorized": False,
            "balfrin_required": False,
            "new_ensemble_execution": False,
            "tuning_performed": False,
        },
    }


def blocked_report(
    *,
    status: str,
    gate_manifest: Path,
    target_manifest: Path,
    reason: str,
    requested_path: Path,
) -> dict[str, Any]:
    return {
        **base_report(gate_manifest=gate_manifest, target_manifest=target_manifest),
        "smoke_status": status,
        "missing_layers": [],
        "layer_summaries": [],
        "overall_metrics": empty_overall_metrics(),
        "blocked_reason": reason,
        "requested_path": str(requested_path),
        "next_measurement": "Restore the requested local artifact before measuring extreme-layer sensitivity.",
    }


def layer_presence_status(layer_key: str, gate_layers: dict[str, Any], target_layers: dict[str, Any]) -> str:
    gate_present = layer_key in gate_layers
    target_present = layer_key in target_layers
    if gate_present and target_present:
        return "present_on_both"
    if gate_present:
        return "missing_from_target"
    if target_present:
        return "missing_from_gate"
    return "missing_from_both"


def missing_layer_summary(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "layer_key": item["layer_key"],
        "presence_status": item["presence_status"],
        "support_delta": {},
        "sample_support_delta": {},
        "summary_delta": {},
        "sensitivity_class": "blocked_missing_layer",
        "interpretation": "Sensitivity cannot be measured until the layer is present in both manifests.",
    }


def summarize_layer(comparison: dict[str, Any], *, sample_support_delta: dict[str, Any]) -> dict[str, Any]:
    value_metrics = comparison["value_metrics"]
    nonzero_metrics = comparison["nonzero_metrics"]
    missing_metrics = comparison["missing_cell_metrics"]
    reference_nonzero = int(nonzero_metrics["reference_nonzero_cell_count"])
    compare_nonzero = int(nonzero_metrics["compare_nonzero_cell_count"])
    reference_missing = int(missing_metrics["reference_missing_cell_count"])
    compare_missing = int(missing_metrics["compare_missing_cell_count"])
    nodata_mismatch = int(missing_metrics["nodata_mismatch_count"])

    return {
        "layer_key": comparison["layer_key"],
        "presence_status": "present_on_both",
        "support_delta": {
            "gate_nonzero_cell_count": reference_nonzero,
            "target_nonzero_cell_count": compare_nonzero,
            "nonzero_cell_count_delta": compare_nonzero - reference_nonzero,
            "nonzero_jaccard": float(nonzero_metrics["nonzero_jaccard"]),
            "gate_missing_cell_count": reference_missing,
            "target_missing_cell_count": compare_missing,
            "missing_cell_count_delta": compare_missing - reference_missing,
            "nodata_mismatch_count": nodata_mismatch,
        },
        "summary_delta": {
            "compared_cell_count": int(value_metrics["compared_cell_count"]),
            "linf_abs_diff": float(value_metrics["linf_abs_diff"]),
            "l1_abs_diff": float(value_metrics["l1_abs_diff"]),
            "rmse": float(value_metrics["rmse"]),
        },
        "sample_support_delta": sample_support_delta,
        "sensitivity_class": classify_sensitivity(
            layer_key=comparison["layer_key"],
            nodata_mismatch_count=nodata_mismatch,
            sample_support_mismatch_count=int(sample_support_delta.get("sample_support_mismatch_count", 0) or 0),
            linf_abs_diff=float(value_metrics["linf_abs_diff"]),
            nonzero_jaccard=float(nonzero_metrics["nonzero_jaccard"]),
        ),
        "interpretation": interpret_layer(
            comparison["layer_key"],
            nodata_mismatch,
            int(sample_support_delta.get("sample_support_mismatch_count", 0) or 0),
        ),
    }


def summarize_sample_support_delta(
    *,
    layer_key: str,
    support_layer_key: str,
    gate_layer: convergence.CellwiseLayer | None,
    target_layer: convergence.CellwiseLayer | None,
) -> dict[str, Any]:
    if gate_layer is None or target_layer is None:
        return {
            "support_metadata_status": "missing",
            "support_layer_key": support_layer_key,
            "gate_support_present": gate_layer is not None,
            "target_support_present": target_layer is not None,
            "sample_support_mismatch_count": 0,
            "support_count_linf_abs_diff": 0.0,
        }
    support_comparison = convergence.compare_cellwise_layer(gate_layer, target_layer)
    return {
        "support_metadata_status": "measured",
        "support_layer_key": support_layer_key,
        "gate_support_present": True,
        "target_support_present": True,
        "gate_supported_cell_count": int(support_comparison["nonzero_metrics"]["reference_nonzero_cell_count"]),
        "target_supported_cell_count": int(support_comparison["nonzero_metrics"]["compare_nonzero_cell_count"]),
        "shared_supported_cell_count": int(support_comparison["nonzero_metrics"]["nonzero_overlap_count"]),
        "support_jaccard": float(support_comparison["nonzero_metrics"]["nonzero_jaccard"]),
        "sample_support_mismatch_count": int(support_comparison["nonzero_metrics"]["nonzero_union_count"])
        - int(support_comparison["nonzero_metrics"]["nonzero_overlap_count"]),
        "support_count_linf_abs_diff": float(support_comparison["value_metrics"]["linf_abs_diff"]),
        "support_count_l1_abs_diff": float(support_comparison["value_metrics"]["l1_abs_diff"]),
        "interpretation": (
            f"{layer_key} support metadata distinguishes cells with finite sample support from unsupported cells."
        ),
    }


def classify_sensitivity(
    *,
    layer_key: str,
    nodata_mismatch_count: int,
    sample_support_mismatch_count: int,
    linf_abs_diff: float,
    nonzero_jaccard: float,
) -> str:
    if (nodata_mismatch_count > 0 or sample_support_mismatch_count > 0) and layer_key == "max_jump_height":
        return "support_nodata_sensitive_extreme_layer"
    if linf_abs_diff > 0.0 and layer_key == "max_kinetic_energy":
        return "magnitude_sensitive_extreme_layer"
    if nonzero_jaccard < 1.0:
        return "support_sensitive_extreme_layer"
    return "measured_no_detected_delta"


def interpret_layer(layer_key: str, nodata_mismatch_count: int, sample_support_mismatch_count: int) -> str:
    if layer_key == "max_kinetic_energy":
        return "Cellwise maximum energy remains a high-priority local sensitivity surface."
    if nodata_mismatch_count > 0 or sample_support_mismatch_count > 0:
        return "Maximum jump height remains tied to support/nodata and sample-count behavior in the local manifests."
    return "Maximum jump height is measured here as a local extreme-layer sensitivity surface."


def summarize_overall(layer_summaries: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "measured_layer_count": len(layer_summaries),
        "blocked_layer_count": 0,
        "max_linf_abs_diff": max((row["summary_delta"]["linf_abs_diff"] for row in layer_summaries), default=0.0),
        "max_rmse": max((row["summary_delta"]["rmse"] for row in layer_summaries), default=0.0),
        "total_l1_abs_diff": sum(row["summary_delta"]["l1_abs_diff"] for row in layer_summaries),
        "total_nodata_mismatch_count": sum(row["support_delta"]["nodata_mismatch_count"] for row in layer_summaries),
        "total_sample_support_mismatch_count": sum(
            int(row["sample_support_delta"].get("sample_support_mismatch_count", 0) or 0)
            for row in layer_summaries
        ),
        "minimum_nonzero_jaccard": min((row["support_delta"]["nonzero_jaccard"] for row in layer_summaries), default=1.0),
    }


def empty_overall_metrics() -> dict[str, Any]:
    return {
        "measured_layer_count": 0,
        "blocked_layer_count": len(EXTREME_LAYERS),
        "max_linf_abs_diff": 0.0,
        "max_rmse": 0.0,
        "total_l1_abs_diff": 0.0,
        "total_nodata_mismatch_count": 0,
        "total_sample_support_mismatch_count": 0,
        "minimum_nonzero_jaccard": 1.0,
    }


def render_text_report(report: dict[str, Any]) -> str:
    lines = [
        f"schema_version: {report['schema_version']}",
        f"smoke_status: {report['smoke_status']}",
        f"gate_manifest: {report['gate_manifest']}",
        f"target_manifest: {report['target_manifest']}",
        "claim_boundaries:",
    ]
    for key, value in report["claim_boundaries"].items():
        lines.append(f"  {key}: {value}")
    if report.get("blocked_reason"):
        lines.append(f"blocked_reason: {report['blocked_reason']}")
    if report.get("missing_layers"):
        lines.append("missing_layers:")
        for item in report["missing_layers"]:
            lines.append(f"  - {item['layer_key']}: {item['presence_status']}")
    lines.append("layer_summaries:")
    for row in report["layer_summaries"]:
        lines.append(f"  - {row['layer_key']}: {row['sensitivity_class']} ({row['presence_status']})")
        if row["summary_delta"]:
            lines.append(
                "    "
                f"linf={row['summary_delta']['linf_abs_diff']:.6g} "
                f"l1={row['summary_delta']['l1_abs_diff']:.6g} "
                f"rmse={row['summary_delta']['rmse']:.6g} "
                f"nonzero_jaccard={row['support_delta']['nonzero_jaccard']:.6g} "
                f"nodata_mismatch={row['support_delta']['nodata_mismatch_count']} "
                f"sample_support_mismatch={row['sample_support_delta'].get('sample_support_mismatch_count', 0)}"
            )
    lines.append(f"next_measurement: {report['next_measurement']}")
    return "\n".join(lines)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
