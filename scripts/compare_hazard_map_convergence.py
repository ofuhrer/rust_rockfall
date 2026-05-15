#!/usr/bin/env python3
"""Compare hazard-map manifests or summaries and report convergence indicators.

This is a post-processing diagnostic for conditional hazard-map products. It
compares manifest summaries and output checksums where available. It does not
change simulator physics, model defaults, or claim annual/physical/risk/
operational semantics.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = "hazard_map_convergence_diagnostic_v1"
BLOCKED_MISSING_INPUTS = "blocked_missing_inputs"
BLOCKED_INVALID_INPUTS = "blocked_invalid_inputs"
OK_STATUS = "ok"
LAYER_SUMMARY_FIELDS = ("valid_cell_count", "minimum", "maximum", "sum", "nonzero_cell_count")
ROOT = Path(__file__).resolve().parents[1]


class HazardMapConvergenceDiagnosticError(ValueError):
    """User-facing hazard-map convergence diagnostic error."""


class HazardMapConvergenceInputError(HazardMapConvergenceDiagnosticError):
    """Raised when a requested input cannot be loaded or interpreted."""

    def __init__(self, status: str, message: str, *, requested_path: Path) -> None:
        super().__init__(message)
        self.status = status
        self.requested_path = requested_path


@dataclass(frozen=True)
class ResolvedManifest:
    requested_path: Path
    manifest_path: Path
    manifest: dict[str, Any]
    manifest_sha256: str


@dataclass(frozen=True)
class CellwiseLayer:
    layer_key: str
    grid_path: Path
    nodata_value: float | None
    thresholds: tuple[float, ...]
    grid: list[list[float | None]]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "inputs",
        nargs="+",
        type=Path,
        help="hazard-map manifest files or run directories to compare",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="output format",
    )
    args = parser.parse_args(argv)

    try:
        result = compare_hazard_map_convergence(args.inputs)
    except HazardMapConvergenceDiagnosticError as exc:
        print(f"hazard-map convergence diagnostic error: {exc}", file=sys.stderr)
        return 2

    if args.format == "json":
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(render_text_report(result))

    return 0 if result["status"] == OK_STATUS else 2


def compare_hazard_map_convergence(input_paths: Iterable[Path]) -> dict[str, Any]:
    requested_paths = [Path(path) for path in input_paths]
    if len(requested_paths) < 2:
        raise HazardMapConvergenceDiagnosticError("provide at least two inputs")

    resolved: list[ResolvedManifest] = []
    missing_inputs: list[dict[str, Any]] = []
    invalid_inputs: list[dict[str, Any]] = []

    for requested_path in requested_paths:
        try:
            resolved.append(resolve_manifest(requested_path))
        except HazardMapConvergenceInputError as exc:
            item = {
                "requested_path": str(exc.requested_path),
                "status": exc.status,
                "reason": str(exc),
            }
            if exc.status == BLOCKED_MISSING_INPUTS:
                missing_inputs.append(item)
            else:
                invalid_inputs.append(item)

    if missing_inputs or invalid_inputs:
        status = BLOCKED_MISSING_INPUTS if missing_inputs else BLOCKED_INVALID_INPUTS
        return {
            "schema_version": SCHEMA_VERSION,
            "status": status,
            "requested_input_count": len(requested_paths),
            "available_input_count": len(resolved),
            "reference_run": manifest_identity(resolved[0]) if resolved else None,
            "comparisons": [],
            "overall_metrics": {
                "comparison_count": 0,
                "shared_layer_count": 0,
                "layer_summary_max_abs_diff": 0.0,
                "layer_summary_sum_abs_diff": 0.0,
                "output_checksum_match_count": 0,
                "output_checksum_mismatch_count": 0,
                "output_checksum_missing_count": 0,
            },
            "missing_inputs": missing_inputs,
            "invalid_inputs": invalid_inputs,
        }

    reference = resolved[0]
    comparisons = []
    for candidate in resolved[1:]:
        try:
            comparisons.append(compare_manifests(reference, candidate))
        except HazardMapConvergenceInputError as exc:
            item = {
                "requested_path": str(exc.requested_path),
                "status": exc.status,
                "reason": str(exc),
            }
            if exc.status == BLOCKED_MISSING_INPUTS:
                missing_inputs.append(item)
            else:
                invalid_inputs.append(item)
        except HazardMapConvergenceDiagnosticError as exc:
            invalid_inputs.append(
                {
                    "requested_path": str(candidate.requested_path),
                    "status": BLOCKED_INVALID_INPUTS,
                    "reason": str(exc),
                }
            )

    if missing_inputs or invalid_inputs:
        status = BLOCKED_MISSING_INPUTS if missing_inputs else BLOCKED_INVALID_INPUTS
        return {
            "schema_version": SCHEMA_VERSION,
            "status": status,
            "requested_input_count": len(requested_paths),
            "available_input_count": len(resolved),
            "reference_run": manifest_identity(resolved[0]) if resolved else None,
            "comparisons": comparisons,
            "overall_metrics": {
                "comparison_count": len(comparisons),
                "shared_layer_count": sum(int(item["metrics"]["shared_layer_count"]) for item in comparisons),
                "layer_summary_max_abs_diff": max(
                    [float(item["metrics"]["layer_summary_max_abs_diff"]) for item in comparisons],
                    default=0.0,
                ),
                "layer_summary_sum_abs_diff": sum(
                    float(item["metrics"]["layer_summary_sum_abs_diff"]) for item in comparisons
                ),
                "output_checksum_match_count": sum(
                    int(item["metrics"]["output_checksum_match_count"]) for item in comparisons
                ),
                "output_checksum_mismatch_count": sum(
                    int(item["metrics"]["output_checksum_mismatch_count"]) for item in comparisons
                ),
                "output_checksum_missing_count": sum(
                    int(item["metrics"]["output_checksum_missing_count"]) for item in comparisons
                ),
                **aggregate_cellwise_metrics(comparisons),
            },
            "missing_inputs": missing_inputs,
            "invalid_inputs": invalid_inputs,
        }
    overall_metrics = aggregate_metrics(comparisons)
    return {
        "schema_version": SCHEMA_VERSION,
        "status": OK_STATUS,
        "requested_input_count": len(requested_paths),
        "available_input_count": len(resolved),
        "reference_run": manifest_identity(reference),
        "comparisons": comparisons,
        "overall_metrics": overall_metrics,
        "missing_inputs": [],
        "invalid_inputs": [],
    }


def render_text_report(result: dict[str, Any]) -> str:
    lines = [
        f"hazard-map convergence diagnostic: {result['status']}",
        f"requested inputs: {result['requested_input_count']}",
        f"available inputs: {result['available_input_count']}",
    ]
    reference = result.get("reference_run")
    if reference:
        lines.append(f"reference: {reference['manifest_path']}")
    if result.get("status") == OK_STATUS:
        for comparison in result.get("comparisons", []):
            metrics = comparison["metrics"]
            lines.append(
                f"- {comparison['compare_run']['manifest_path']}: "
                f"shared_layers={metrics['shared_layer_count']}, "
                f"layer_max_abs_diff={metrics['layer_summary_max_abs_diff']:.6g}, "
                f"checksum_mismatches={metrics['output_checksum_mismatch_count']}"
            )
            cellwise = comparison.get("cellwise_metrics")
            if cellwise:
                lines.append("  cell-wise layers:")
                for layer in cellwise.get("layer_comparisons", []):
                    value_metrics = layer["value_metrics"]
                    missing_metrics = layer["missing_cell_metrics"]
                    lines.append(
                        "  - "
                        f"{layer['layer_key']}: "
                        f"linf={value_metrics['linf_abs_diff']:.6g}, "
                        f"l1={value_metrics['l1_abs_diff']:.6g}, "
                        f"rmse={value_metrics['rmse']:.6g}, "
                        f"jaccard={layer['nonzero_metrics']['nonzero_jaccard']:.6g}, "
                        f"nodata_mismatch={missing_metrics['nodata_mismatch_count']}"
                    )
    else:
        missing = result.get("missing_inputs", [])
        invalid = result.get("invalid_inputs", [])
        if missing:
            lines.append("missing inputs:")
            lines.extend(f"- {item['requested_path']}: {item['reason']}" for item in missing)
        if invalid:
            lines.append("invalid inputs:")
            lines.extend(f"- {item['requested_path']}: {item['reason']}" for item in invalid)
    return "\n".join(lines)


def compare_manifests(reference: ResolvedManifest, candidate: ResolvedManifest) -> dict[str, Any]:
    reference_layers = layer_summary_index(reference.manifest)
    candidate_layers = layer_summary_index(candidate.manifest)
    shared_layer_keys = sorted(set(reference_layers) & set(candidate_layers))
    reference_only_layer_keys = sorted(set(reference_layers) - set(candidate_layers))
    candidate_only_layer_keys = sorted(set(candidate_layers) - set(reference_layers))

    layer_comparisons = [
        compare_layer_summary(layer_key, reference_layers[layer_key], candidate_layers[layer_key])
        for layer_key in shared_layer_keys
    ]
    layer_max_abs_diffs = [entry["max_abs_diff"] for entry in layer_comparisons]
    layer_sum_abs_diffs = [entry["sum_abs_diff"] for entry in layer_comparisons]

    curve_comparison = compare_curve_summaries(
        reference.manifest.get("conditional_intensity_exceedance_curves"),
        candidate.manifest.get("conditional_intensity_exceedance_curves"),
    )
    output_comparison = compare_output_signatures(
        reference.manifest.get("outputs") or [],
        candidate.manifest.get("outputs") or [],
    )
    cellwise_comparison = compare_cellwise_layers(reference, candidate)

    compatibility = compare_compatibility(reference.manifest, candidate.manifest)

    metrics = {
        "shared_layer_count": len(shared_layer_keys),
        "reference_only_layer_count": len(reference_only_layer_keys),
        "compare_only_layer_count": len(candidate_only_layer_keys),
        "layer_summary_max_abs_diff": max(layer_max_abs_diffs, default=0.0),
        "layer_summary_sum_abs_diff": sum(layer_sum_abs_diffs),
        "layer_summary_mean_abs_diff": (
            sum(layer_sum_abs_diffs) / len(layer_sum_abs_diffs) if layer_sum_abs_diffs else 0.0
        ),
        "conditional_curve_row_count_abs_diff": abs(
            curve_comparison["reference_row_count"] - curve_comparison["compare_row_count"]
        ),
        "conditional_curve_measure_symdiff_count": len(curve_comparison["intensity_measure_symdiff"]),
        "conditional_curve_probability_mode_symdiff_count": len(
            curve_comparison["probability_mode_symdiff"]
        ),
        "output_file_count_abs_diff": abs(
            output_comparison["reference_output_count"] - output_comparison["compare_output_count"]
        ),
        "output_total_bytes_abs_diff": abs(
            output_comparison["reference_total_bytes"] - output_comparison["compare_total_bytes"]
        ),
        "output_checksum_match_count": output_comparison["match_count"],
        "output_checksum_mismatch_count": output_comparison["mismatch_count"],
        "output_checksum_missing_count": output_comparison["missing_count"],
        "manifest_checksum_match": reference.manifest_sha256 == candidate.manifest_sha256,
    }
    if cellwise_comparison is not None:
        metrics.update(cellwise_comparison["overall_metrics"])

    result = {
        "reference_run": manifest_identity(reference),
        "compare_run": manifest_identity(candidate),
        "compatibility": compatibility,
        "metrics": metrics,
        "layer_comparisons": layer_comparisons,
        "conditional_curve_comparison": curve_comparison,
        "output_checksum_comparison": output_comparison,
    }
    if cellwise_comparison is not None:
        result["cellwise_metrics"] = cellwise_comparison
    return result


def aggregate_metrics(comparisons: list[dict[str, Any]]) -> dict[str, Any]:
    if not comparisons:
        return {
            "comparison_count": 0,
            "shared_layer_count": 0,
            "layer_summary_max_abs_diff": 0.0,
            "layer_summary_sum_abs_diff": 0.0,
            "output_checksum_match_count": 0,
            "output_checksum_mismatch_count": 0,
            "output_checksum_missing_count": 0,
        }
    return {
        "comparison_count": len(comparisons),
        "shared_layer_count": sum(int(item["metrics"]["shared_layer_count"]) for item in comparisons),
        "layer_summary_max_abs_diff": max(float(item["metrics"]["layer_summary_max_abs_diff"]) for item in comparisons),
        "layer_summary_sum_abs_diff": sum(float(item["metrics"]["layer_summary_sum_abs_diff"]) for item in comparisons),
        "output_checksum_match_count": sum(
            int(item["metrics"]["output_checksum_match_count"]) for item in comparisons
        ),
        "output_checksum_mismatch_count": sum(
            int(item["metrics"]["output_checksum_mismatch_count"]) for item in comparisons
        ),
        "output_checksum_missing_count": sum(
            int(item["metrics"]["output_checksum_missing_count"]) for item in comparisons
        ),
        **aggregate_cellwise_metrics(comparisons),
    }


def aggregate_cellwise_metrics(comparisons: list[dict[str, Any]]) -> dict[str, Any]:
    cellwise_comparisons = [item.get("cellwise_metrics") for item in comparisons if item.get("cellwise_metrics")]
    if not cellwise_comparisons:
        return {}

    layer_counts = [int(item["layer_count"]) for item in cellwise_comparisons]
    linf_values = [float(layer["value_metrics"]["linf_abs_diff"]) for item in cellwise_comparisons for layer in item["layer_comparisons"]]
    l1_values = [float(layer["value_metrics"]["l1_abs_diff"]) for item in cellwise_comparisons for layer in item["layer_comparisons"]]
    rmse_values = [float(layer["value_metrics"]["rmse"]) for item in cellwise_comparisons for layer in item["layer_comparisons"]]
    jaccard_values = [
        float(layer["nonzero_metrics"]["nonzero_jaccard"]) for item in cellwise_comparisons for layer in item["layer_comparisons"]
    ]
    threshold_disagreement_total = sum(
        int(entry["disagreement_cell_count"])
        for item in cellwise_comparisons
        for layer in item["layer_comparisons"]
        for entry in layer["threshold_exceedance_disagreement"]
    )
    nodata_mismatch_total = sum(
        int(layer["missing_cell_metrics"]["nodata_mismatch_count"])
        for item in cellwise_comparisons
        for layer in item["layer_comparisons"]
    )
    shape_mismatch_total = sum(
        1
        for item in cellwise_comparisons
        for layer in item["layer_comparisons"]
        if not layer["grid_shape"]["shape_match"]
    )
    return {
        "cellwise_layer_count": sum(layer_counts),
        "cellwise_shared_layer_count": sum(int(item["shared_layer_count"]) for item in cellwise_comparisons),
        "cellwise_reference_only_layer_count": sum(int(item["reference_only_layer_count"]) for item in cellwise_comparisons),
        "cellwise_compare_only_layer_count": sum(int(item["compare_only_layer_count"]) for item in cellwise_comparisons),
        "cellwise_layer_shape_mismatch_count": shape_mismatch_total,
        "cellwise_linf_abs_diff_max": max(linf_values, default=0.0),
        "cellwise_l1_abs_diff_sum": sum(l1_values),
        "cellwise_rmse_max": max(rmse_values, default=0.0),
        "cellwise_nonzero_jaccard_min": min(jaccard_values, default=1.0),
        "cellwise_threshold_disagreement_count": threshold_disagreement_total,
        "cellwise_nodata_mismatch_count": nodata_mismatch_total,
    }


def compare_compatibility(reference: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    reference_grid = reference.get("grid") or {}
    candidate_grid = candidate.get("grid") or {}
    reference_map_package = reference.get("hazard_map_package") or {}
    candidate_map_package = candidate.get("hazard_map_package") or {}

    fields = {
        "grid_match": normalized_mapping(reference_grid) == normalized_mapping(candidate_grid),
        "case_id_match": reference.get("case_id") == candidate.get("case_id"),
        "map_product_id_match": semantic_field(reference_map_package, "map_product_id")
        == semantic_field(candidate_map_package, "map_product_id"),
        "probability_mode_match": semantic_field(reference_map_package, "probability_mode")
        == semantic_field(candidate_map_package, "probability_mode"),
        "normalization_scope_match": semantic_field(reference_map_package, "normalization_scope")
        == semantic_field(candidate_map_package, "normalization_scope"),
    }
    return {
        **fields,
        "mismatch_count": sum(1 for value in fields.values() if value is False),
    }


def compare_layer_summary(layer_key: str, reference: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    summary_diffs: dict[str, Any] = {}
    abs_diffs: list[float] = []
    for field in LAYER_SUMMARY_FIELDS:
        reference_value = reference.get(field)
        candidate_value = candidate.get(field)
        abs_diff = numeric_abs_diff(reference_value, candidate_value)
        summary_diffs[field] = {
            "reference": reference_value,
            "compare": candidate_value,
            "abs_diff": abs_diff,
        }
        if abs_diff is not None:
            abs_diffs.append(abs_diff)
    return {
        "layer_key": layer_key,
        "summary_diffs": summary_diffs,
        "max_abs_diff": max(abs_diffs, default=0.0),
        "sum_abs_diff": sum(abs_diffs),
    }


def compare_curve_summaries(reference: Any, candidate: Any) -> dict[str, Any]:
    reference_summary = reference if isinstance(reference, dict) else {}
    candidate_summary = candidate if isinstance(candidate, dict) else {}
    reference_measures = set(reference_summary.get("intensity_measures") or [])
    candidate_measures = set(candidate_summary.get("intensity_measures") or [])
    reference_modes = set(reference_summary.get("probability_modes") or [])
    candidate_modes = set(candidate_summary.get("probability_modes") or [])
    return {
        "reference_row_count": int(reference_summary.get("row_count") or 0),
        "compare_row_count": int(candidate_summary.get("row_count") or 0),
        "reference_mode": reference_summary.get("mode"),
        "compare_mode": candidate_summary.get("mode"),
        "reference_csv_table_written": bool(reference_summary.get("csv_table_written", False)),
        "compare_csv_table_written": bool(candidate_summary.get("csv_table_written", False)),
        "reference_annualized": bool(reference_summary.get("annualized", False)),
        "compare_annualized": bool(candidate_summary.get("annualized", False)),
        "intensity_measure_symdiff": sorted(reference_measures.symmetric_difference(candidate_measures)),
        "probability_mode_symdiff": sorted(reference_modes.symmetric_difference(candidate_modes)),
    }


def compare_output_signatures(reference_outputs: list[dict[str, Any]], candidate_outputs: list[dict[str, Any]]) -> dict[str, Any]:
    reference_map = {output_signature(output): output for output in reference_outputs}
    candidate_map = {output_signature(output): output for output in candidate_outputs}
    shared_keys = sorted(set(reference_map) & set(candidate_map))
    reference_only_keys = sorted(set(reference_map) - set(candidate_map))
    candidate_only_keys = sorted(set(candidate_map) - set(reference_map))

    output_comparisons = []
    match_count = 0
    mismatch_count = 0
    for key in shared_keys:
        reference = reference_map[key]
        candidate = candidate_map[key]
        same_checksum = reference.get("sha256") == candidate.get("sha256")
        if same_checksum:
            match_count += 1
        else:
            mismatch_count += 1
        output_comparisons.append(
            {
                "signature": key,
                "reference_path": reference.get("path"),
                "compare_path": candidate.get("path"),
                "reference_sha256": reference.get("sha256"),
                "compare_sha256": candidate.get("sha256"),
                "sha256_match": same_checksum,
                "reference_total_bytes": int(reference.get("total_bytes") or 0),
                "compare_total_bytes": int(candidate.get("total_bytes") or 0),
            }
        )

    return {
        "reference_output_count": len(reference_outputs),
        "compare_output_count": len(candidate_outputs),
        "reference_total_bytes": sum(int(output.get("total_bytes") or 0) for output in reference_outputs),
        "compare_total_bytes": sum(int(output.get("total_bytes") or 0) for output in candidate_outputs),
        "shared_output_count": len(shared_keys),
        "reference_only_output_count": len(reference_only_keys),
        "compare_only_output_count": len(candidate_only_keys),
        "match_count": match_count,
        "mismatch_count": mismatch_count,
        "missing_count": len(reference_only_keys) + len(candidate_only_keys),
        "shared_outputs": output_comparisons,
    }


def compare_cellwise_layers(reference: ResolvedManifest, candidate: ResolvedManifest) -> dict[str, Any] | None:
    reference_layers = cellwise_layer_index(reference)
    candidate_layers = cellwise_layer_index(candidate)
    if not reference_layers and not candidate_layers:
        return None
    if not reference_layers or not candidate_layers:
        raise HazardMapConvergenceInputError(
            BLOCKED_INVALID_INPUTS,
            "cell-wise layer grids must be provided on both inputs when comparing raster-like fixtures",
            requested_path=candidate.requested_path,
        )

    shared_layer_keys = sorted(set(reference_layers) & set(candidate_layers))
    reference_only_layer_keys = sorted(set(reference_layers) - set(candidate_layers))
    candidate_only_layer_keys = sorted(set(candidate_layers) - set(reference_layers))
    if reference_only_layer_keys or candidate_only_layer_keys:
        raise HazardMapConvergenceInputError(
            BLOCKED_INVALID_INPUTS,
            "cell-wise layer keys must match on both inputs",
            requested_path=candidate.requested_path,
        )

    layer_comparisons = [
        compare_cellwise_layer(reference_layers[layer_key], candidate_layers[layer_key])
        for layer_key in shared_layer_keys
    ]
    overall_metrics = aggregate_cellwise_layer_metrics(layer_comparisons)
    return {
        "layer_count": len(shared_layer_keys),
        "shared_layer_count": len(shared_layer_keys),
        "reference_only_layer_count": len(reference_only_layer_keys),
        "compare_only_layer_count": len(candidate_only_layer_keys),
        "layer_comparisons": layer_comparisons,
        "overall_metrics": overall_metrics,
    }


def compare_cellwise_layer(reference: CellwiseLayer, candidate: CellwiseLayer) -> dict[str, Any]:
    reference_rows = len(reference.grid)
    candidate_rows = len(candidate.grid)
    reference_cols = len(reference.grid[0]) if reference.grid else 0
    candidate_cols = len(candidate.grid[0]) if candidate.grid else 0
    if reference_rows != candidate_rows or reference_cols != candidate_cols:
        raise HazardMapConvergenceInputError(
            BLOCKED_INVALID_INPUTS,
            f"cell-wise grid shape mismatch for {reference.layer_key}: "
            f"reference={reference_rows}x{reference_cols}, compare={candidate_rows}x{candidate_cols}",
            requested_path=candidate.grid_path,
        )

    linf_abs_diff = 0.0
    l1_abs_diff = 0.0
    squared_diff_sum = 0.0
    compared_cell_count = 0
    reference_nonzero_count = 0
    compare_nonzero_count = 0
    nonzero_overlap_count = 0
    nonzero_union_count = 0
    reference_missing_cell_count = 0
    compare_missing_cell_count = 0
    nodata_mismatch_count = 0

    thresholds = sorted(set(reference.thresholds) | set(candidate.thresholds))
    threshold_metrics = {
        threshold: {
            "reference_exceedance_cell_count": 0,
            "compare_exceedance_cell_count": 0,
            "intersection_cell_count": 0,
            "disagreement_cell_count": 0,
        }
        for threshold in thresholds
    }

    for row_index in range(reference_rows):
        for col_index in range(reference_cols):
            reference_value = reference.grid[row_index][col_index]
            candidate_value = candidate.grid[row_index][col_index]
            reference_missing = reference_value is None
            candidate_missing = candidate_value is None

            if reference_missing:
                reference_missing_cell_count += 1
            if candidate_missing:
                compare_missing_cell_count += 1
            if reference_missing != candidate_missing:
                nodata_mismatch_count += 1
                continue
            if reference_missing and candidate_missing:
                continue

            compared_cell_count += 1
            abs_diff = abs(float(candidate_value) - float(reference_value))
            linf_abs_diff = max(linf_abs_diff, abs_diff)
            l1_abs_diff += abs_diff
            squared_diff_sum += abs_diff * abs_diff

            reference_nonzero = float(reference_value) != 0.0
            candidate_nonzero = float(candidate_value) != 0.0
            if reference_nonzero:
                reference_nonzero_count += 1
            if candidate_nonzero:
                compare_nonzero_count += 1
            if reference_nonzero or candidate_nonzero:
                nonzero_union_count += 1
            if reference_nonzero and candidate_nonzero:
                nonzero_overlap_count += 1

            for threshold, bucket in threshold_metrics.items():
                reference_exceeds = float(reference_value) >= threshold
                candidate_exceeds = float(candidate_value) >= threshold
                if reference_exceeds:
                    bucket["reference_exceedance_cell_count"] += 1
                if candidate_exceeds:
                    bucket["compare_exceedance_cell_count"] += 1
                if reference_exceeds and candidate_exceeds:
                    bucket["intersection_cell_count"] += 1
                if reference_exceeds != candidate_exceeds:
                    bucket["disagreement_cell_count"] += 1

    rmse = math.sqrt(squared_diff_sum / compared_cell_count) if compared_cell_count else 0.0
    nonzero_jaccard = 1.0 if nonzero_union_count == 0 else nonzero_overlap_count / nonzero_union_count
    threshold_disagreement_metrics = []
    for threshold in thresholds:
        bucket = threshold_metrics[threshold]
        reference_exceedance = bucket["reference_exceedance_cell_count"]
        compare_exceedance = bucket["compare_exceedance_cell_count"]
        intersection = bucket["intersection_cell_count"]
        union = reference_exceedance + compare_exceedance - intersection
        threshold_disagreement_metrics.append(
            {
                "threshold": threshold,
                "reference_exceedance_cell_count": reference_exceedance,
                "compare_exceedance_cell_count": compare_exceedance,
                "disagreement_cell_count": bucket["disagreement_cell_count"],
                "exceedance_jaccard": 1.0 if union == 0 else intersection / union,
            }
        )

    layer_name = reference.layer_key
    return {
        "layer_key": layer_name,
        "layer_name": layer_name,
        "grid_shape": {
            "reference_nrows": reference_rows,
            "reference_ncols": reference_cols,
            "compare_nrows": candidate_rows,
            "compare_ncols": candidate_cols,
            "shape_match": reference_rows == candidate_rows and reference_cols == candidate_cols,
        },
        "linf_abs_diff": linf_abs_diff,
        "l1_abs_diff": l1_abs_diff,
        "rmse": rmse,
        "compared_cell_count": compared_cell_count,
        "value_metrics": {
            "linf_abs_diff": linf_abs_diff,
            "l1_abs_diff": l1_abs_diff,
            "rmse": rmse,
            "compared_cell_count": compared_cell_count,
        },
        "reference_nonzero_cell_count": reference_nonzero_count,
        "compare_nonzero_cell_count": compare_nonzero_count,
        "nonzero_overlap_count": nonzero_overlap_count,
        "nonzero_union_count": nonzero_union_count,
        "nonzero_jaccard": nonzero_jaccard,
        "nonzero_metrics": {
            "reference_nonzero_cell_count": reference_nonzero_count,
            "compare_nonzero_cell_count": compare_nonzero_count,
            "nonzero_overlap_count": nonzero_overlap_count,
            "nonzero_union_count": nonzero_union_count,
            "nonzero_jaccard": nonzero_jaccard,
        },
        "threshold_exceedance_disagreement_count": sum(
            int(entry["disagreement_cell_count"]) for entry in threshold_disagreement_metrics
        ),
        "threshold_exceedance_disagreement": threshold_disagreement_metrics,
        "reference_missing_cell_count": reference_missing_cell_count,
        "compare_missing_cell_count": compare_missing_cell_count,
        "nodata_mismatch_count": nodata_mismatch_count,
        "missing_cell_metrics": {
            "reference_missing_cell_count": reference_missing_cell_count,
            "compare_missing_cell_count": compare_missing_cell_count,
            "nodata_mismatch_count": nodata_mismatch_count,
        },
    }


def aggregate_cellwise_layer_metrics(layer_comparisons: list[dict[str, Any]]) -> dict[str, Any]:
    if not layer_comparisons:
        return {
            "cellwise_layer_count": 0,
            "cellwise_shared_layer_count": 0,
            "cellwise_reference_only_layer_count": 0,
            "cellwise_compare_only_layer_count": 0,
            "cellwise_layer_shape_mismatch_count": 0,
            "cellwise_linf_abs_diff_max": 0.0,
            "cellwise_l1_abs_diff_sum": 0.0,
            "cellwise_rmse_max": 0.0,
            "cellwise_nonzero_jaccard_min": 1.0,
            "cellwise_threshold_disagreement_count": 0,
            "cellwise_nodata_mismatch_count": 0,
        }

    linf_values = []
    l1_values = []
    rmse_values = []
    jaccard_values = []
    threshold_disagreement_total = 0
    nodata_mismatch_total = 0
    shape_mismatch_count = 0
    for comparison in layer_comparisons:
        value_metrics = comparison["value_metrics"]
        nonzero_metrics = comparison["nonzero_metrics"]
        missing_metrics = comparison["missing_cell_metrics"]
        grid_shape = comparison["grid_shape"]
        linf_values.append(float(value_metrics["linf_abs_diff"]))
        l1_values.append(float(value_metrics["l1_abs_diff"]))
        rmse_values.append(float(value_metrics["rmse"]))
        jaccard_values.append(float(nonzero_metrics["nonzero_jaccard"]))
        threshold_disagreement_total += sum(
            int(entry["disagreement_cell_count"]) for entry in comparison["threshold_exceedance_disagreement"]
        )
        nodata_mismatch_total += int(missing_metrics["nodata_mismatch_count"])
        if not grid_shape["shape_match"]:
            shape_mismatch_count += 1

    return {
        "cellwise_layer_count": len(layer_comparisons),
        "cellwise_shared_layer_count": len(layer_comparisons),
        "cellwise_reference_only_layer_count": 0,
        "cellwise_compare_only_layer_count": 0,
        "cellwise_layer_shape_mismatch_count": shape_mismatch_count,
        "cellwise_linf_abs_diff_max": max(linf_values, default=0.0),
        "cellwise_l1_abs_diff_sum": sum(l1_values),
        "cellwise_rmse_max": max(rmse_values, default=0.0),
        "cellwise_nonzero_jaccard_min": min(jaccard_values, default=1.0),
        "cellwise_threshold_disagreement_count": threshold_disagreement_total,
        "cellwise_nodata_mismatch_count": nodata_mismatch_total,
    }


def cellwise_layer_index(resolved: ResolvedManifest) -> dict[str, CellwiseLayer]:
    layer_entries = resolved.manifest.get("cellwise_layers")
    if not layer_entries:
        layer_entries = infer_cellwise_layers_from_outputs(resolved)
    if not layer_entries:
        return {}
    if not isinstance(layer_entries, list):
        raise HazardMapConvergenceInputError(
            BLOCKED_INVALID_INPUTS,
            "cellwise_layers must be a list of layer definitions",
            requested_path=resolved.requested_path,
        )

    index: dict[str, CellwiseLayer] = {}
    for entry in layer_entries:
        if not isinstance(entry, dict):
            continue
        layer_key = entry.get("key") or entry.get("layer_name")
        grid_path_value = entry.get("grid_path") or entry.get("path")
        if not isinstance(layer_key, str) or not layer_key:
            raise HazardMapConvergenceInputError(
                BLOCKED_INVALID_INPUTS,
                f"cellwise layer entry is missing a valid key: {resolved.manifest_path}",
                requested_path=resolved.requested_path,
            )
        if not isinstance(grid_path_value, str) or not grid_path_value:
            raise HazardMapConvergenceInputError(
                BLOCKED_INVALID_INPUTS,
                f"cellwise layer {layer_key} is missing grid_path",
                requested_path=resolved.requested_path,
            )
        grid_path = resolve_artifact_path(grid_path_value, resolved.manifest_path.parent)
        if not grid_path.exists():
            raise HazardMapConvergenceInputError(
                BLOCKED_MISSING_INPUTS,
                f"cellwise grid file does not exist: {grid_path}",
                requested_path=grid_path,
            )
        thresholds_value = entry.get("thresholds") or entry.get("threshold_values") or []
        if isinstance(thresholds_value, (int, float)):
            thresholds = (float(thresholds_value),)
        elif isinstance(thresholds_value, list):
            thresholds = tuple(float(value) for value in thresholds_value)
        else:
            raise HazardMapConvergenceInputError(
                BLOCKED_INVALID_INPUTS,
                f"cellwise layer {layer_key} thresholds must be a number or list of numbers",
                requested_path=resolved.requested_path,
            )
        if not thresholds:
            thresholds = infer_thresholds_from_layer_key(layer_key)
        grid, nodata_value = load_cell_grid(grid_path)
        index[layer_key] = CellwiseLayer(
            layer_key=layer_key,
            grid_path=grid_path,
            nodata_value=nodata_value,
            thresholds=thresholds,
            grid=grid,
        )

    if not index:
        raise HazardMapConvergenceInputError(
            BLOCKED_INVALID_INPUTS,
            f"cellwise_layers did not yield any usable layer definitions: {resolved.manifest_path}",
            requested_path=resolved.requested_path,
        )
    return index


def infer_cellwise_layers_from_outputs(resolved: ResolvedManifest) -> list[dict[str, Any]]:
    outputs = resolved.manifest.get("outputs")
    if not isinstance(outputs, list):
        return []
    cellwise_layers: list[dict[str, Any]] = []
    for output in outputs:
        if not isinstance(output, dict):
            continue
        if output.get("kind") != "hazard_layer":
            continue
        if output.get("format") != "esri_ascii_grid":
            continue
        layer_name = output.get("layer_name")
        path_value = output.get("path")
        if not isinstance(layer_name, str) or not layer_name:
            continue
        if not isinstance(path_value, str) or not path_value:
            continue
        grid_path = resolve_artifact_path(path_value, resolved.manifest_path.parent)
        if not grid_path.exists():
            continue
        cellwise_layers.append(
            {
                "key": layer_name,
                "grid_path": path_value,
                "thresholds": list(infer_thresholds_from_layer_key(layer_name)),
                "source": "outputs",
            }
        )
    return cellwise_layers


def resolve_artifact_path(path_value: str, manifest_dir: Path) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path
    repo_relative = (ROOT / path).resolve()
    if repo_relative.exists():
        return repo_relative
    return (manifest_dir / path).resolve()


def infer_thresholds_from_layer_key(layer_key: str) -> tuple[float, ...]:
    parsed = parse_exceedance_layer_key(layer_key)
    if parsed is None:
        return ()
    return (parsed[1],)


def parse_exceedance_layer_key(layer_key: str) -> tuple[str, float, str, bool] | None:
    if layer_key.endswith("_standard_error"):
        return None
    specs = (
        ("weighted_kinetic_energy_exceedance_", "kinetic_energy", "J", "j", True),
        ("kinetic_energy_exceedance_", "kinetic_energy", "J", "j", False),
        ("weighted_jump_height_exceedance_", "jump_height", "m", "m", True),
        ("jump_height_exceedance_", "jump_height", "m", "m", False),
        ("weighted_velocity_exceedance_", "velocity", "m/s", "mps", True),
        ("velocity_exceedance_", "velocity", "m/s", "mps", False),
    )
    for prefix, measure, units, suffix, weighted in specs:
        if layer_key.startswith(prefix) and layer_key.endswith(suffix):
            raw = layer_key[len(prefix) : -len(suffix)]
            threshold_text = raw.replace("neg_", "-").replace("p", ".")
            try:
                threshold = float(threshold_text)
            except ValueError:
                return None
            return measure, threshold, units, weighted
    return None


def load_cell_grid(path: Path) -> tuple[list[list[float | None]], float | None]:
    suffix = path.suffix.lower()
    if suffix in {".json"}:
        return load_json_cell_grid(path)
    return load_ascii_cell_grid(path)


def load_json_cell_grid(path: Path) -> tuple[list[list[float | None]], float | None]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HazardMapConvergenceInputError(
            BLOCKED_INVALID_INPUTS,
            f"invalid JSON cell grid in {path}: {exc}",
            requested_path=path,
        ) from exc
    if not isinstance(document, dict):
        raise HazardMapConvergenceInputError(
            BLOCKED_INVALID_INPUTS,
            f"cell grid JSON must be an object: {path}",
            requested_path=path,
        )
    rows_value = document.get("cells") or document.get("values")
    if not isinstance(rows_value, list) or not rows_value:
        raise HazardMapConvergenceInputError(
            BLOCKED_INVALID_INPUTS,
            f"cell grid JSON must contain a non-empty cells or values list: {path}",
            requested_path=path,
        )
    nodata_value = document.get("nodata_value")
    rows: list[list[float | None]] = []
    expected_width: int | None = None
    for row_index, row in enumerate(rows_value):
        if not isinstance(row, list):
            raise HazardMapConvergenceInputError(
                BLOCKED_INVALID_INPUTS,
                f"cell grid JSON row {row_index} must be a list: {path}",
                requested_path=path,
            )
        if expected_width is None:
            expected_width = len(row)
        elif len(row) != expected_width:
            raise HazardMapConvergenceInputError(
                BLOCKED_INVALID_INPUTS,
                f"cell grid JSON rows must have the same length: {path}",
                requested_path=path,
            )
        try:
            rows.append([normalize_grid_value(value, nodata_value) for value in row])
        except ValueError as exc:
            raise HazardMapConvergenceInputError(
                BLOCKED_INVALID_INPUTS,
                f"cell grid JSON contains a non-numeric value: {path}",
                requested_path=path,
            ) from exc
    return rows, float(nodata_value) if isinstance(nodata_value, (int, float)) else None


def load_ascii_cell_grid(path: Path) -> tuple[list[list[float | None]], float | None]:
    try:
        lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    except OSError as exc:
        raise HazardMapConvergenceInputError(
            BLOCKED_MISSING_INPUTS,
            f"cell grid file does not exist or cannot be read: {path}",
            requested_path=path,
        ) from exc
    if len(lines) < 6:
        raise HazardMapConvergenceInputError(
            BLOCKED_INVALID_INPUTS,
            f"ASCII grid is too short to contain a header: {path}",
            requested_path=path,
        )

    header: dict[str, str] = {}
    data_start_index = 0
    for index, line in enumerate(lines[:6]):
        parts = line.split()
        if len(parts) < 2:
            raise HazardMapConvergenceInputError(
                BLOCKED_INVALID_INPUTS,
                f"ASCII grid header line is malformed: {path}",
                requested_path=path,
            )
        header[parts[0].lower()] = parts[1]
        data_start_index = index + 1

    try:
        ncols = int(header["ncols"])
        nrows = int(header["nrows"])
    except KeyError as exc:
        raise HazardMapConvergenceInputError(
            BLOCKED_INVALID_INPUTS,
            f"ASCII grid header missing ncols or nrows: {path}",
            requested_path=path,
        ) from exc
    except ValueError as exc:
        raise HazardMapConvergenceInputError(
            BLOCKED_INVALID_INPUTS,
            f"ASCII grid ncols or nrows is not an integer: {path}",
            requested_path=path,
        ) from exc

    nodata_value: float | None = None
    if "nodata_value" in header:
        try:
            nodata_value = float(header["nodata_value"])
        except ValueError as exc:
            raise HazardMapConvergenceInputError(
                BLOCKED_INVALID_INPUTS,
                f"ASCII grid nodata_value is not numeric: {path}",
                requested_path=path,
            ) from exc

    data_lines = lines[data_start_index:]
    if len(data_lines) != nrows:
        raise HazardMapConvergenceInputError(
            BLOCKED_INVALID_INPUTS,
            f"ASCII grid row count does not match header for {path}",
            requested_path=path,
        )

    grid: list[list[float | None]] = []
    for row_index, line in enumerate(data_lines):
        values = line.split()
        if len(values) != ncols:
            raise HazardMapConvergenceInputError(
                BLOCKED_INVALID_INPUTS,
                f"ASCII grid column count mismatch on row {row_index} for {path}",
                requested_path=path,
            )
        try:
            grid.append([normalize_grid_value(value, nodata_value) for value in values])
        except ValueError as exc:
            raise HazardMapConvergenceInputError(
                BLOCKED_INVALID_INPUTS,
                f"ASCII grid contains a non-numeric value: {path}",
                requested_path=path,
            ) from exc
    return grid, nodata_value


def normalize_grid_value(value: Any, nodata_value: float | None) -> float | None:
    if value is None:
        return None
    if isinstance(value, str):
        lowered = value.lower()
        if lowered == "nan":
            return None
        try:
            numeric = float(value)
        except ValueError as exc:
            raise ValueError(f"grid cell value is not numeric: {value!r}") from exc
    elif isinstance(value, (int, float)) and not isinstance(value, bool):
        numeric = float(value)
    else:
        raise ValueError(f"grid cell value is not numeric: {value!r}")
    if nodata_value is not None and numeric == nodata_value:
        return None
    return numeric


def layer_summary_index(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    layers = manifest.get("layers")
    if not isinstance(layers, list):
        raise HazardMapConvergenceDiagnosticError("manifest is missing a layers list")
    index: dict[str, dict[str, Any]] = {}
    for entry in layers:
        if not isinstance(entry, dict):
            continue
        layer_key = entry.get("key")
        summary = entry.get("summary")
        if isinstance(layer_key, str) and isinstance(summary, dict):
            index[layer_key] = summary
    if not index:
        raise HazardMapConvergenceDiagnosticError("manifest layers do not include summary records")
    return index


def resolve_manifest(requested_path: Path) -> ResolvedManifest:
    if not requested_path.exists():
        raise HazardMapConvergenceInputError(
            BLOCKED_MISSING_INPUTS,
            f"input path does not exist: {requested_path}",
            requested_path=requested_path,
        )

    if requested_path.is_file():
        manifest = load_manifest_document(requested_path)
        return ResolvedManifest(
            requested_path=requested_path,
            manifest_path=requested_path,
            manifest=manifest,
            manifest_sha256=sha256_file(requested_path),
        )

    if requested_path.is_dir():
        candidate_paths = sorted(
            candidate
            for candidate in requested_path.rglob("*.json")
            if "manifest" in candidate.name.lower()
        )
        for candidate_path in candidate_paths:
            try:
                manifest = load_manifest_document(candidate_path)
            except HazardMapConvergenceDiagnosticError:
                continue
            return ResolvedManifest(
                requested_path=requested_path,
                manifest_path=candidate_path,
                manifest=manifest,
                manifest_sha256=sha256_file(candidate_path),
            )
        raise HazardMapConvergenceInputError(
            BLOCKED_MISSING_INPUTS,
            f"no hazard manifest JSON found under {requested_path}",
            requested_path=requested_path,
        )

    raise HazardMapConvergenceInputError(
        BLOCKED_MISSING_INPUTS,
        f"input path is neither file nor directory: {requested_path}",
        requested_path=requested_path,
    )


def load_manifest_document(path: Path) -> dict[str, Any]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise HazardMapConvergenceInputError(
            BLOCKED_MISSING_INPUTS,
            f"input file does not exist: {path}",
            requested_path=path,
        ) from exc
    except json.JSONDecodeError as exc:
        raise HazardMapConvergenceInputError(
            BLOCKED_INVALID_INPUTS,
            f"invalid JSON in {path}: {exc}",
            requested_path=path,
        ) from exc

    if not isinstance(document, dict):
        raise HazardMapConvergenceInputError(
            BLOCKED_INVALID_INPUTS,
            f"manifest document must be a JSON object: {path}",
            requested_path=path,
        )
    if "layers" not in document or "outputs" not in document:
        raise HazardMapConvergenceInputError(
            BLOCKED_INVALID_INPUTS,
            f"manifest document is missing required layers or outputs fields: {path}",
            requested_path=path,
        )
    return document


def manifest_identity(resolved: ResolvedManifest) -> dict[str, Any]:
    manifest = resolved.manifest
    return {
        "requested_path": str(resolved.requested_path),
        "manifest_path": str(resolved.manifest_path),
        "manifest_sha256": resolved.manifest_sha256,
        "schema_version": manifest.get("schema_version"),
        "case_id": manifest.get("case_id"),
    }


def output_signature(output: dict[str, Any]) -> str:
    kind = str(output.get("kind") or "unknown")
    format_name = str(output.get("format") or "unknown")
    layer_name = str(output.get("layer_name") or "")
    path = Path(str(output.get("path") or "")).name
    return "|".join((kind, format_name, layer_name or path))


def semantic_field(mapping: dict[str, Any], field: str) -> Any:
    value = mapping.get(field)
    if value is None:
        return None
    return value


def normalized_mapping(mapping: dict[str, Any]) -> dict[str, Any]:
    return {key: mapping[key] for key in sorted(mapping)}


def numeric_abs_diff(reference: Any, candidate: Any) -> float | None:
    if isinstance(reference, (int, float)) and isinstance(candidate, (int, float)):
        return abs(float(candidate) - float(reference))
    return None


def sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
