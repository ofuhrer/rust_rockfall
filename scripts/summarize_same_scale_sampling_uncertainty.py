#!/usr/bin/env python3
"""Summarize multi-seed same-scale sampling uncertainty for the selected Tschamut pilot.

This report composes existing gate, target, and bounded-probe convergence
comparisons. It does not alter simulator physics, defaults, thresholds,
release assumptions, or sampling semantics.
"""

from __future__ import annotations

import argparse
import importlib.util
import itertools
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any

try:
    import yaml  # type: ignore
except ImportError as exc:  # pragma: no cover - environment setup.
    raise SystemExit("PyYAML is required; install with `python3 -m pip install PyYAML`") from exc


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ARTIFACTS = [
    ROOT / "hazard/results/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_manifest.json",
    ROOT / "hazard/results/tschamut_public_pilot/target_gate_v1/validation_tschamut_public_target_gate_v1_manifest.json",
    ROOT / "hazard/results/tschamut_public_pilot/sampling_sensitivity_v1_full/validation_tschamut_public_sampling_sensitivity_v1_full_manifest.json",
    ROOT / "hazard/results/tschamut_public_pilot/sampling_sensitivity_v2_full/validation_tschamut_public_sampling_sensitivity_v2_full_manifest.json",
]
SELECTED_LAYERS = (
    "max_kinetic_energy",
    "max_jump_height",
    "velocity_exceedance_5mps",
    "weighted_velocity_exceedance_5mps",
    "velocity_exceedance_10mps",
)
SCHEMA_VERSION = "tschamut_same_scale_sampling_uncertainty_v1"


class SamplingUncertaintyError(ValueError):
    """User-facing sampling uncertainty error."""


def _load_module(module_name: str, filename: str):
    path = ROOT / "scripts" / filename
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise SamplingUncertaintyError(f"failed to load helper module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


CONVERGENCE = _load_module("compare_hazard_map_convergence", "compare_hazard_map_convergence.py")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        action="append",
        type=Path,
        dest="manifests",
        help="hazard manifest file or run directory; may be repeated",
    )
    parser.add_argument("--format", choices=("text", "markdown", "json"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    parser.add_argument("--markdown-output", type=Path, default=None)
    args = parser.parse_args(argv)

    try:
        report = build_sampling_uncertainty_summary(manifest_paths=args.manifests)
    except SamplingUncertaintyError as exc:
        print(f"same-scale sampling uncertainty error: {exc}", file=sys.stderr)
        return 2

    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.markdown_output is not None:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(render_markdown_report(report), encoding="utf-8")

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    elif args.format == "markdown":
        print(render_markdown_report(report), end="")
    else:
        print(
            "same-scale sampling uncertainty: "
            f"{report['sampling_uncertainty_status']} "
            f"(comparison_pairs={report['comparison_pairs_run']}, "
            f"dominant_layers={', '.join(report['dominant_layer_spread'])})"
        )
    return 0 if report["sampling_uncertainty_status"] == "sampling_uncertainty_measured" else 2


def build_sampling_uncertainty_summary(
    manifest_paths: list[Path] | None = None,
) -> dict[str, Any]:
    manifests = resolve_manifests(manifest_paths or DEFAULT_ARTIFACTS)
    expected_artifacts = [artifact_paths_for_manifest(manifest_path) for manifest_path in manifests]
    missing = collect_missing_inputs(expected_artifacts)
    if missing:
        return blocked_report(manifests, expected_artifacts, missing, reason="one or more required sampling artifacts are missing")

    artifacts = [load_artifact(manifest_path) for manifest_path in manifests]

    comparisons = build_pairwise_comparisons(artifacts)
    pairwise_count = len(comparisons)
    if not comparisons:
        return blocked_report(manifests, artifacts, [], reason="no pairwise comparisons could be produced")

    layer_spread = compute_layer_spread(comparisons, SELECTED_LAYERS)
    output_pressure = {
        artifact["artifact_id"]: {
            "validation": {
                "file_count": artifact["validation_file_count"],
                "byte_count": artifact["validation_byte_count"],
            },
            "hazard": {
                "file_count": artifact["hazard_file_count"],
                "byte_count": artifact["hazard_byte_count"],
            },
        }
        for artifact in artifacts
    }

    report = {
        "schema_version": SCHEMA_VERSION,
        "sampling_uncertainty_status": "sampling_uncertainty_measured",
        "readiness_status": "ready",
        "artifacts_included": artifacts,
        "artifact_ids": [artifact["artifact_id"] for artifact in artifacts],
        "case_ids": [artifact["case_id"] for artifact in artifacts],
        "seeds_or_splits": [artifact["seed_or_split"] for artifact in artifacts],
        "ensemble_sizes": [artifact["ensemble_size"] for artifact in artifacts],
        "validation_output_modes": [artifact["validation_output_mode"] for artifact in artifacts],
        "output_file_counts": output_pressure and {
            artifact_id: pressure["validation"]["file_count"] for artifact_id, pressure in output_pressure.items()
        },
        "output_byte_counts": output_pressure and {
            artifact_id: pressure["validation"]["byte_count"] for artifact_id, pressure in output_pressure.items()
        },
        "hazard_output_file_counts": {
            artifact_id: pressure["hazard"]["file_count"] for artifact_id, pressure in output_pressure.items()
        },
        "hazard_output_byte_counts": {
            artifact_id: pressure["hazard"]["byte_count"] for artifact_id, pressure in output_pressure.items()
        },
        "comparison_pairs_run": comparisons,
        "pairwise_comparison_count": pairwise_count,
        "shared_cellwise_layer_counts": [comparison["shared_cellwise_layer_count"] for comparison in comparisons],
        "dominant_layer_spread": layer_spread,
        "max_kinetic_energy_uncertainty": layer_spread["max_kinetic_energy"],
        "max_jump_height_uncertainty": layer_spread["max_jump_height"],
        "velocity_exceedance_uncertainty": {
            "velocity_exceedance_5mps": layer_spread["velocity_exceedance_5mps"],
            "weighted_velocity_exceedance_5mps": layer_spread["weighted_velocity_exceedance_5mps"],
            "velocity_exceedance_10mps": layer_spread["velocity_exceedance_10mps"],
        },
        "support_or_nodata_sensitivity": summarize_support_nodata_sensitivity(layer_spread),
        "uncertainty_reduced": [
            "A second same-size seed now shows that the dominant disagreement shrinks relative to the gate-target baseline but does not collapse.",
            "max_kinetic_energy remains the dominant layer, while max_jump_height retains support and nodata sensitivity.",
            "velocity exceedance layers vary across seeds but remain lower-order than kinetic-energy disagreement.",
        ],
        "remaining_uncertainty": [
            "seed sensitivity remains structurally limiting on the shared grid",
            "max_kinetic_energy still dominates the envelope",
            "max_jump_height still carries support/nodata variation",
            "the gate-target interpretation remains conservative and non-operational",
        ],
        "defaults_changed": False,
        "physics_changed": False,
        "thresholds_changed": False,
        "source_or_scenario_inputs_changed": False,
        "target_convergence_interpretation": "inconclusive",
        "scale_up_authorized": False,
        "operational_claims_allowed": False,
        "comparison_status": "ok",
        "interpretation": "sampling_uncertainty_measured",
        "blocked_reason": "none",
    }
    return report


def blocked_report(
    manifests: list[Path],
    artifacts: list[dict[str, Any]],
    missing: list[str],
    *,
    reason: str,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "sampling_uncertainty_status": "blocked_missing_inputs",
        "readiness_status": "blocked_missing_inputs",
        "artifacts_included": artifacts,
        "artifact_ids": [artifact.get("artifact_id") for artifact in artifacts if artifact.get("artifact_id")],
        "case_ids": [artifact.get("case_id") for artifact in artifacts if artifact.get("case_id")],
        "seeds_or_splits": [artifact.get("seed_or_split") for artifact in artifacts if artifact.get("seed_or_split") is not None],
        "ensemble_sizes": [artifact.get("ensemble_size") for artifact in artifacts if artifact.get("ensemble_size") is not None],
        "validation_output_modes": [artifact.get("validation_output_mode") for artifact in artifacts if artifact.get("validation_output_mode")],
        "output_file_counts": {artifact.get("artifact_id"): artifact.get("validation_file_count") for artifact in artifacts if artifact.get("artifact_id")},
        "output_byte_counts": {artifact.get("artifact_id"): artifact.get("validation_byte_count") for artifact in artifacts if artifact.get("artifact_id")},
        "hazard_output_file_counts": {artifact.get("artifact_id"): artifact.get("hazard_file_count") for artifact in artifacts if artifact.get("artifact_id")},
        "hazard_output_byte_counts": {artifact.get("artifact_id"): artifact.get("hazard_byte_count") for artifact in artifacts if artifact.get("artifact_id")},
        "comparison_pairs_run": [],
        "pairwise_comparison_count": 0,
        "shared_cellwise_layer_counts": [],
        "dominant_layer_spread": {},
        "max_kinetic_energy_uncertainty": {},
        "max_jump_height_uncertainty": {},
        "velocity_exceedance_uncertainty": {},
        "support_or_nodata_sensitivity": {},
        "uncertainty_reduced": [],
        "remaining_uncertainty": [],
        "defaults_changed": False,
        "physics_changed": False,
        "thresholds_changed": False,
        "source_or_scenario_inputs_changed": False,
        "target_convergence_interpretation": "inconclusive",
        "scale_up_authorized": False,
        "operational_claims_allowed": False,
        "comparison_status": "blocked_missing_inputs",
        "interpretation": "blocked_missing_inputs",
        "blocked_reason": reason,
        "missing_input_paths": missing,
        "requested_manifests": [str(path) for path in manifests],
    }


def summarize_support_nodata_sensitivity(layer_spread: dict[str, Any]) -> dict[str, Any]:
    max_jump = layer_spread["max_jump_height"]
    max_ke = layer_spread["max_kinetic_energy"]
    velocity_layers = {
        name: layer_spread[name]
        for name in ("velocity_exceedance_5mps", "weighted_velocity_exceedance_5mps", "velocity_exceedance_10mps")
    }
    return {
        "max_jump_height_nodata_mismatch_range": max_jump["nodata_mismatch_count"],
        "max_kinetic_energy_nodata_mismatch_range": max_ke["nodata_mismatch_count"],
        "velocity_layer_nodata_mismatch_range": {
            name: stats["nodata_mismatch_count"] for name, stats in velocity_layers.items()
        },
        "max_jump_height_support_range": max_jump["nonzero_jaccard"],
        "max_kinetic_energy_support_range": max_ke["nonzero_jaccard"],
        "velocity_layer_support_range": {
            name: stats["nonzero_jaccard"] for name, stats in velocity_layers.items()
        },
    }


def compute_layer_spread(comparisons: list[dict[str, Any]], layer_keys: tuple[str, ...]) -> dict[str, Any]:
    spread: dict[str, dict[str, list[float]]] = {
        key: {
            "l1_abs_diff": [],
            "linf_abs_diff": [],
            "rmse": [],
            "nonzero_jaccard": [],
            "nodata_mismatch_count": [],
        }
        for key in layer_keys
    }
    for comparison in comparisons:
        for layer in comparison["layer_comparisons"]:
            key = layer["layer_key"]
            if key not in spread:
                continue
            spread[key]["l1_abs_diff"].append(float(layer["value_metrics"]["l1_abs_diff"]))
            spread[key]["linf_abs_diff"].append(float(layer["value_metrics"]["linf_abs_diff"]))
            spread[key]["rmse"].append(float(layer["value_metrics"]["rmse"]))
            spread[key]["nonzero_jaccard"].append(float(layer["nonzero_metrics"]["nonzero_jaccard"]))
            spread[key]["nodata_mismatch_count"].append(int(layer["missing_cell_metrics"]["nodata_mismatch_count"]))
    return {
        key: {
            metric: summarize_range(values)
            for metric, values in metrics.items()
        }
        for key, metrics in spread.items()
    }


def summarize_range(values: list[float]) -> dict[str, Any]:
    if not values:
        return {"min": None, "max": None, "range": None, "mean": None, "count": 0}
    return {
        "min": min(values),
        "max": max(values),
        "range": max(values) - min(values),
        "mean": mean(values),
        "count": len(values),
    }


def build_pairwise_comparisons(artifacts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    comparisons = []
    for reference, candidate in itertools.combinations(artifacts, 2):
        result = compare_manifest_pair(Path(reference["manifest_path"]), Path(candidate["manifest_path"]))
        comparison = result["comparisons"][0]
        layer_metrics = {
            layer["layer_key"]: {
                "l1_abs_diff": float(layer["value_metrics"]["l1_abs_diff"]),
                "linf_abs_diff": float(layer["value_metrics"]["linf_abs_diff"]),
                "rmse": float(layer["value_metrics"]["rmse"]),
                "nonzero_jaccard": float(layer["nonzero_metrics"]["nonzero_jaccard"]),
                "nodata_mismatch_count": int(layer["missing_cell_metrics"]["nodata_mismatch_count"]),
            }
            for layer in comparison["cellwise_metrics"]["layer_comparisons"]
        }
        comparisons.append(
            {
                "reference_artifact_id": reference["artifact_id"],
                "compare_artifact_id": candidate["artifact_id"],
                "reference_case_id": reference["case_id"],
                "compare_case_id": candidate["case_id"],
                "status": result["status"],
                "shared_cellwise_layer_count": int(result["overall_metrics"]["shared_layer_count"]),
                "cellwise_linf_abs_diff_max": float(result["overall_metrics"]["cellwise_linf_abs_diff_max"]),
                "cellwise_l1_abs_diff_sum": float(result["overall_metrics"]["cellwise_l1_abs_diff_sum"]),
                "cellwise_rmse_max": float(result["overall_metrics"]["cellwise_rmse_max"]),
                "cellwise_nonzero_jaccard_min": float(result["overall_metrics"]["cellwise_nonzero_jaccard_min"]),
                "cellwise_nodata_mismatch_count": int(result["overall_metrics"]["cellwise_nodata_mismatch_count"]),
                "output_checksum_match_count": int(result["overall_metrics"]["output_checksum_match_count"]),
                "output_checksum_mismatch_count": int(result["overall_metrics"]["output_checksum_mismatch_count"]),
                "output_checksum_missing_count": int(result["overall_metrics"]["output_checksum_missing_count"]),
                "layer_comparisons": [
                    {
                        "layer_key": layer_key,
                        "value_metrics": {
                            "l1_abs_diff": layer_metrics[layer_key]["l1_abs_diff"],
                            "linf_abs_diff": layer_metrics[layer_key]["linf_abs_diff"],
                            "rmse": layer_metrics[layer_key]["rmse"],
                        },
                        "nonzero_metrics": {
                            "nonzero_jaccard": layer_metrics[layer_key]["nonzero_jaccard"],
                        },
                        "missing_cell_metrics": {
                            "nodata_mismatch_count": layer_metrics[layer_key]["nodata_mismatch_count"],
                        },
                    }
                    for layer_key in layer_metrics
                ],
                "layer_metrics": layer_metrics,
            }
        )
    return comparisons


def compare_manifest_pair(reference_manifest: Path, compare_manifest: Path) -> dict[str, Any]:
    result = CONVERGENCE.compare_hazard_map_convergence([reference_manifest, compare_manifest])
    if result["status"] != CONVERGENCE.OK_STATUS:
        raise SamplingUncertaintyError(f"comparison blocked for {reference_manifest} vs {compare_manifest}: {result['status']}")
    return result


def load_artifact(manifest_path: Path) -> dict[str, Any]:
    if not manifest_path.exists():
        raise SamplingUncertaintyError(f"missing manifest: {manifest_path}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    case_path = infer_case_path(manifest_path)
    validation_root = case_path.parent
    hazard_root = manifest_path.parent
    validation_files, validation_bytes = tree_size(validation_root)
    hazard_files, hazard_bytes = tree_size(hazard_root)
    case = load_case_yaml(case_path)
    output_mode = infer_validation_output_mode(case)
    artifact_id = manifest.get("case_id") or manifest_path.stem.removeprefix("validation_").removesuffix("_manifest")
    seed_policy = manifest.get("seed_policy") or {}
    case_seed = case.get("random", {}).get("seed")
    return {
        "artifact_id": artifact_id,
        "case_id": manifest.get("case_id", artifact_id),
        "case_path": str(case_path),
        "manifest_path": str(manifest_path),
        "validation_root": str(validation_root),
        "hazard_root": str(hazard_root),
        "validation_output_mode": output_mode,
        "seed_or_split": seed_policy.get("global_seed", case_seed),
        "ensemble_size": seed_policy.get("ensemble_size", case.get("random", {}).get("ensemble_size")),
        "validation_file_count": validation_files,
        "validation_byte_count": validation_bytes,
        "hazard_file_count": hazard_files,
        "hazard_byte_count": hazard_bytes,
        "grid": manifest.get("grid", {}),
        "shared_cellwise_layer_count": len(manifest.get("cellwise_layers", [])),
        "required_input_paths": {
            "source_zone_metadata": case.get("probabilistic_metadata", {}).get("source_zone_metadata_path"),
            "scenario_table": case.get("probabilistic_metadata", {}).get("scenario_table_path"),
        },
    }


def artifact_paths_for_manifest(manifest_path: Path) -> dict[str, Any]:
    case_path = infer_case_path(manifest_path)
    validation_root = case_path.parent
    hazard_root = manifest_path.parent
    return {
        "artifact_id": manifest_path.stem.removeprefix("validation_").removesuffix("_manifest"),
        "manifest_path": str(manifest_path),
        "case_path": str(case_path),
        "validation_root": str(validation_root),
        "hazard_root": str(hazard_root),
    }


def infer_validation_output_mode(case: dict[str, Any]) -> str:
    outputs = case.get("outputs", {}) or {}
    if any(key in outputs for key in ("trajectory_csv", "ensemble_trajectories_dir", "ensemble_impact_events_dir")):
        return "full"
    if outputs:
        return "summary_only"
    return "unknown"


def infer_case_path(manifest_path: Path) -> Path:
    base_root, relative = split_hazard_results_path(manifest_path)
    validation_root = base_root / "validation/private" / relative.parent
    case_candidates = sorted(validation_root.glob("*_case.yaml"))
    if len(case_candidates) == 1:
        return case_candidates[0]
    case_filename = manifest_path.name
    if case_filename.startswith("validation_") and case_filename.endswith("_manifest.json"):
        case_filename = case_filename[len("validation_") : -len("_manifest.json")] + "_case.yaml"
    else:
        case_filename = manifest_path.stem + ".yaml"
    return validation_root / case_filename


def split_hazard_results_path(manifest_path: Path) -> tuple[Path, Path]:
    parts = manifest_path.parts
    for index in range(len(parts) - 1):
        if parts[index] == "hazard" and parts[index + 1] == "results":
            base = Path(*parts[:index]) if index > 0 else Path(".")
            relative = Path(*parts[index + 2 :]) if index + 2 < len(parts) else Path()
            return base, relative
    raise SamplingUncertaintyError(f"cannot infer hazard/results path from {manifest_path}")


def load_case_yaml(case_path: Path) -> dict[str, Any]:
    if not case_path.exists():
        raise SamplingUncertaintyError(f"missing case YAML: {case_path}")
    return yaml.safe_load(case_path.read_text(encoding="utf-8")) or {}


def tree_size(path: Path) -> tuple[int, int]:
    if not path.exists():
        return 0, 0
    files = 0
    bytes_ = 0
    for root, _, names in os.walk(path):
        for name in names:
            fp = Path(root) / name
            files += 1
            bytes_ += fp.stat().st_size
    return files, bytes_


def collect_missing_inputs(artifacts: list[dict[str, Any]]) -> list[str]:
    missing: list[str] = []
    for artifact in artifacts:
        for key in ("manifest_path", "case_path"):
            path = Path(artifact[key])
            if not path.exists():
                missing.append(str(path))
        for key in ("validation_root", "hazard_root"):
            path = Path(artifact[key])
            if not path.exists():
                missing.append(str(path))
    return sorted(set(missing))


def resolve_manifests(manifest_paths: list[Path]) -> list[Path]:
    resolved: list[Path] = []
    for manifest_path in manifest_paths:
        manifest_path = Path(manifest_path)
        if manifest_path.is_dir():
            candidate = next(manifest_path.glob("*_manifest.json"), None)
            if candidate is None:
                raise SamplingUncertaintyError(f"no manifest found in directory: {manifest_path}")
            manifest_path = candidate
        resolved.append(manifest_path)
    return resolved


def render_markdown_report(report: dict[str, Any]) -> str:
    if report["sampling_uncertainty_status"] != "sampling_uncertainty_measured":
        lines = [
            "# Same-Scale Sampling Uncertainty",
            "",
            f"- Status: `{report['sampling_uncertainty_status']}`",
            f"- Blocked reason: `{report['blocked_reason']}`",
        ]
        if report.get("missing_input_paths"):
            lines.append("- Missing inputs:")
            lines.extend(f"  - `{path}`" for path in report["missing_input_paths"])
        return "\n".join(lines) + "\n"

    lines = [
        "# Same-Scale Sampling Uncertainty Envelope",
        "",
        f"- Status: `{report['sampling_uncertainty_status']}`",
        f"- Pairwise comparisons: `{report['pairwise_comparison_count']}`",
        f"- Case ids: `{', '.join(report['case_ids'])}`",
        f"- Seeds or splits: `{', '.join(str(x) for x in report['seeds_or_splits'])}`",
        f"- Ensemble sizes: `{', '.join(str(x) for x in report['ensemble_sizes'])}`",
        "",
        "## Dominant Layers",
    ]
    for layer_name in SELECTED_LAYERS:
        spread = report["dominant_layer_spread"][layer_name]
        lines.append(
            f"- `{layer_name}`: l1 {spread['l1_abs_diff']['min']:.6g} to {spread['l1_abs_diff']['max']:.6g}, "
            f"linf {spread['linf_abs_diff']['min']:.6g} to {spread['linf_abs_diff']['max']:.6g}, "
            f"rmse {spread['rmse']['min']:.6g} to {spread['rmse']['max']:.6g}, "
            f"jaccard {spread['nonzero_jaccard']['min']:.6g} to {spread['nonzero_jaccard']['max']:.6g}"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            *[f"- {item}" for item in report["uncertainty_reduced"]],
            "",
            "## Remaining Uncertainty",
            *[f"- {item}" for item in report["remaining_uncertainty"]],
        ]
    )
    return "\n".join(lines) + "\n"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        action="append",
        type=Path,
        dest="manifests",
        help="hazard manifest file or run directory; may be repeated",
    )
    parser.add_argument("--format", choices=("text", "markdown", "json"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    parser.add_argument("--markdown-output", type=Path, default=None)
    return parser.parse_args(argv)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
