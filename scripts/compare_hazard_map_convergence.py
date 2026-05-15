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
    comparisons = [
        compare_manifests(reference, candidate)
        for candidate in resolved[1:]
    ]
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

    return {
        "reference_run": manifest_identity(reference),
        "compare_run": manifest_identity(candidate),
        "compatibility": compatibility,
        "metrics": metrics,
        "layer_comparisons": layer_comparisons,
        "conditional_curve_comparison": curve_comparison,
        "output_checksum_comparison": output_comparison,
    }


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
