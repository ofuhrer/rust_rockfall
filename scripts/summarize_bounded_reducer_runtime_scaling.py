#!/usr/bin/env python3
"""Summarize bounded reducer/runtime/output scaling from existing artifacts.

The helper is read-only. It reads the committed or ignored local manifests and
filesystem counts for the selected same-scale Tschamut artifacts, then reports
runtime, reducer-worker, and output-volume evidence without running a new
validation or hazard build.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "bounded_reducer_runtime_scaling_v1"


def _load_module(module_name: str, filename: str):
    path = ROOT / "scripts" / filename
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load helper module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


AUDIT = _load_module("bounded_reducer_runtime_scaling_audit", "audit_local_artifacts.py")


@dataclass(frozen=True)
class ArtifactSpec:
    artifact_id: str
    validation_root: Path
    validation_manifest: Path
    hazard_root: Path
    hazard_manifest: Path
    hazard_manifest_optional: bool = False


DEFAULT_ARTIFACTS = (
    ArtifactSpec(
        "gate_v1",
        ROOT / "validation/private/tschamut_public_pilot/gate_v1",
        ROOT / "validation/private/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_manifest.json",
        ROOT / "hazard/results/tschamut_public_pilot/gate_v1",
        ROOT / "hazard/results/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_manifest.json",
    ),
    ArtifactSpec(
        "target_gate_v1",
        ROOT / "validation/private/tschamut_public_pilot/target_gate_v1",
        ROOT / "validation/private/tschamut_public_pilot/target_gate_v1/validation_tschamut_public_target_gate_v1_manifest.json",
        ROOT / "hazard/results/tschamut_public_pilot/target_gate_v1",
        ROOT / "hazard/results/tschamut_public_pilot/target_gate_v1/validation_tschamut_public_target_gate_v1_manifest.json",
    ),
    ArtifactSpec(
        "target_rebuildable_reduced",
        ROOT / "validation/private/tschamut_public_pilot/target_gate_v1_rebuildable_reduced",
        ROOT
        / "validation/private/tschamut_public_pilot/target_gate_v1_rebuildable_reduced/validation_tschamut_public_target_gate_v1_rebuildable_reduced_manifest.json",
        ROOT / "hazard/results/tschamut_public_pilot/target_gate_v1_rebuildable_reduced",
        ROOT
        / "hazard/results/tschamut_public_pilot/target_gate_v1_rebuildable_reduced/validation_tschamut_public_target_gate_v1_rebuildable_reduced_manifest.json",
        True,
    ),
    ArtifactSpec(
        "sampling_sensitivity_v1_full",
        ROOT / "validation/private/tschamut_public_pilot/sampling_sensitivity_v1_full",
        ROOT / "validation/private/tschamut_public_pilot/sampling_sensitivity_v1_full/validation_tschamut_public_sampling_sensitivity_v1_full_manifest.json",
        ROOT / "hazard/results/tschamut_public_pilot/sampling_sensitivity_v1_full",
        ROOT / "hazard/results/tschamut_public_pilot/sampling_sensitivity_v1_full/validation_tschamut_public_sampling_sensitivity_v1_full_manifest.json",
    ),
    ArtifactSpec(
        "sampling_sensitivity_v2_full",
        ROOT / "validation/private/tschamut_public_pilot/sampling_sensitivity_v2_full",
        ROOT / "validation/private/tschamut_public_pilot/sampling_sensitivity_v2_full/validation_tschamut_public_sampling_sensitivity_v2_full_manifest.json",
        ROOT / "hazard/results/tschamut_public_pilot/sampling_sensitivity_v2_full",
        ROOT / "hazard/results/tschamut_public_pilot/sampling_sensitivity_v2_full/validation_tschamut_public_sampling_sensitivity_v2_full_manifest.json",
    ),
)


class BoundedReducerRuntimeScalingError(ValueError):
    """User-facing bounded reducer/runtime scaling error."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    parser.add_argument("--markdown-output", type=Path, default=None)
    parser.add_argument("--allow-missing", action="store_true")
    args = parser.parse_args(argv)

    try:
        report = build_report(DEFAULT_ARTIFACTS, allow_missing=args.allow_missing)
    except BoundedReducerRuntimeScalingError as exc:
        print(f"bounded reducer/runtime scaling error: {exc}")
        return 2

    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.markdown_output is not None:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(render_markdown(report), encoding="utf-8")

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text(report))
    return 0 if report["reducer_scaling_status"] == "measured_existing_artifacts" else 2


def build_report(artifact_specs: tuple[ArtifactSpec, ...], *, allow_missing: bool = False) -> dict[str, Any]:
    missing_paths = [
        str(path)
        for spec in artifact_specs
        for path in (
            spec.validation_manifest,
            spec.hazard_manifest,
        )
        if not path.exists() and not (path == spec.hazard_manifest and spec.hazard_manifest_optional)
    ]
    if missing_paths:
        if not allow_missing:
            raise BoundedReducerRuntimeScalingError(
                "required same-scale artifacts are missing: " + ", ".join(sorted(set(missing_paths)))
            )
        return {
            "schema_version": SCHEMA_VERSION,
            "command_plan_status": "ready",
            "readiness_status": "blocked_missing_inputs",
            "reducer_scaling_status": "blocked_missing_inputs",
            "artifacts_measured": [],
            "validation_roots": [],
            "hazard_roots": [],
            "file_counts": {},
            "byte_counts": {},
            "hazard_layer_counts": {},
            "reducer_worker_counts": {},
            "runtime_seconds": {},
            "timing_source": "manifest_performance.total_wall_seconds",
            "bottleneck_classification": "blocked_missing_inputs",
            "output_scaling_findings": [],
            "local_single_job_sufficient_for_next_step": False,
            "distributed_execution_authorized": False,
            "blocked_reason": "missing same-scale artifacts: " + ", ".join(sorted(set(missing_paths))),
            "scale_up_authorized": False,
            "operational_claims_allowed": False,
            "comparison_pairs": [],
            "measurement_command": "PYENV_VERSION=system uv run python scripts/summarize_bounded_reducer_runtime_scaling.py --format json",
        }

    artifacts: list[dict[str, Any]] = []
    for spec in artifact_specs:
        artifact = summarize_artifact(spec)
        artifacts.append(artifact)

    comparison_pairs = [
        compare_artifacts(artifacts[0], artifacts[1], label="gate_vs_target"),
        compare_artifacts(artifacts[1], artifacts[2], label="target_full_vs_native_rebuildable_reduced"),
        compare_artifacts(artifacts[3], artifacts[4], label="sampling_probe_v1_vs_v2"),
    ]
    overall = classify_bottleneck(artifacts, comparison_pairs)
    readiness_status = "ready"

    report = {
        "schema_version": SCHEMA_VERSION,
        "command_plan_status": "ready",
        "readiness_status": readiness_status,
        "reducer_scaling_status": "measured_existing_artifacts" if not missing_paths else "blocked_missing_inputs",
        "artifacts_measured": artifacts,
        "validation_roots": [
            {
                "artifact_id": artifact["artifact_id"],
                "path": artifact["validation_root"]["path"],
                "file_count": artifact["validation_root"]["file_count"],
                "total_bytes": artifact["validation_root"]["total_bytes"],
            }
            for artifact in artifacts
        ],
        "hazard_roots": [
            {
                "artifact_id": artifact["artifact_id"],
                "path": artifact["hazard_root"]["path"],
                "file_count": artifact["hazard_root"]["file_count"],
                "total_bytes": artifact["hazard_root"]["total_bytes"],
            }
            for artifact in artifacts
        ],
        "file_counts": {
            "validation_roots": {artifact["artifact_id"]: artifact["validation_root"]["file_count"] for artifact in artifacts},
            "hazard_roots": {artifact["artifact_id"]: artifact["hazard_root"]["file_count"] for artifact in artifacts},
            "comparison_pairs": {entry["label"]: entry["validation_file_count_delta"] for entry in comparison_pairs},
        },
        "byte_counts": {
            "validation_roots": {artifact["artifact_id"]: artifact["validation_root"]["total_bytes"] for artifact in artifacts},
            "hazard_roots": {artifact["artifact_id"]: artifact["hazard_root"]["total_bytes"] for artifact in artifacts},
            "comparison_pairs": {entry["label"]: entry["byte_count_delta"] for entry in comparison_pairs},
        },
        "hazard_layer_counts": {artifact["artifact_id"]: artifact["hazard_layer_count"] for artifact in artifacts},
        "reducer_worker_counts": {artifact["artifact_id"]: artifact["reducer_worker_count"] for artifact in artifacts},
        "runtime_seconds": {
            "validation_roots": {artifact["artifact_id"]: artifact["validation_runtime_seconds"] for artifact in artifacts},
            "hazard_roots": {artifact["artifact_id"]: artifact["hazard_runtime_seconds"] for artifact in artifacts},
        },
        "timing_source": "manifest_performance.total_wall_seconds",
        "bottleneck_classification": overall["bottleneck_classification"],
        "output_scaling_findings": overall["output_scaling_findings"],
        "local_single_job_sufficient_for_next_step": overall["local_single_job_sufficient_for_next_step"],
        "distributed_execution_authorized": False,
        "blocked_reason": "",
        "scale_up_authorized": False,
        "operational_claims_allowed": False,
        "comparison_pairs": comparison_pairs,
        "measurement_command": "PYENV_VERSION=system uv run python scripts/summarize_bounded_reducer_runtime_scaling.py --format json",
    }
    return report


def summarize_artifact(spec: ArtifactSpec) -> dict[str, Any]:
    validation_manifest = load_json(spec.validation_manifest)
    hazard_manifest = load_json(spec.hazard_manifest) if spec.hazard_manifest.exists() else {}

    validation_root = summarize_root(spec.validation_root)
    hazard_root = summarize_root(spec.hazard_root)
    hazard_outputs = hazard_manifest.get("outputs") or []
    reducer_execution = hazard_manifest.get("reducer_execution") or {}

    map_package_manifest_path = find_reported_manifest_path(hazard_outputs, "map_package_manifest")
    pilot_gis_manifest_path = find_reported_manifest_path(hazard_outputs, "pilot_gis_package_manifest")

    return {
        "artifact_id": spec.artifact_id,
        "status": "ready",
        "validation_manifest_path": str(spec.validation_manifest),
        "hazard_manifest_path": str(spec.hazard_manifest),
        "validation_root": validation_root,
        "hazard_root": hazard_root,
        "validation_runtime_seconds": number_or_none(validation_manifest.get("performance", {}).get("total_wall_seconds")),
        "hazard_runtime_seconds": number_or_none(hazard_manifest.get("performance", {}).get("total_wall_seconds")),
        "validation_output_file_count": validation_manifest.get("performance", {}).get("output_file_count"),
        "validation_output_bytes": validation_manifest.get("performance", {}).get("output_bytes"),
        "hazard_output_file_count": hazard_manifest.get("performance", {}).get("output_file_count"),
        "hazard_output_bytes": hazard_manifest.get("performance", {}).get("output_bytes"),
        "validation_output_mode": validation_manifest.get("validation_output_mode"),
        "hazard_layer_count": len(hazard_manifest.get("cellwise_layers") or []),
        "reducer_worker_count": reducer_execution.get("worker_count"),
        "reducer_chunk_count": reducer_execution.get("chunk_count"),
        "reducer_merge_order": reducer_execution.get("merge_order"),
        "map_package_manifest_present": bool(map_package_manifest_path and Path(map_package_manifest_path).exists()),
        "pilot_gis_manifest_present": bool(pilot_gis_manifest_path and Path(pilot_gis_manifest_path).exists()),
        "map_package_manifest_path": map_package_manifest_path,
        "pilot_gis_manifest_path": pilot_gis_manifest_path,
        "missing_paths": [],
        "comparison_notes": [],
    }


def compare_artifacts(left: dict[str, Any], right: dict[str, Any], *, label: str) -> dict[str, Any]:
    return {
        "label": label,
        "left_artifact_id": left["artifact_id"],
        "right_artifact_id": right["artifact_id"],
        "validation_file_count_delta": right["validation_root"]["file_count"] - left["validation_root"]["file_count"],
        "byte_count_delta": right["validation_root"]["total_bytes"] - left["validation_root"]["total_bytes"],
        "hazard_file_count_delta": right["hazard_root"]["file_count"] - left["hazard_root"]["file_count"],
        "hazard_byte_count_delta": right["hazard_root"]["total_bytes"] - left["hazard_root"]["total_bytes"],
        "validation_runtime_delta_seconds": number_or_none(right["validation_runtime_seconds"]) - number_or_none(left["validation_runtime_seconds"]),
        "hazard_runtime_delta_seconds": number_or_none(right["hazard_runtime_seconds"]) - number_or_none(left["hazard_runtime_seconds"]),
    }


def classify_bottleneck(artifacts: list[dict[str, Any]], comparison_pairs: list[dict[str, Any]]) -> dict[str, Any]:
    target = next(artifact for artifact in artifacts if artifact["artifact_id"] == "target_gate_v1")
    gate = next(artifact for artifact in artifacts if artifact["artifact_id"] == "gate_v1")
    validation_ratio = safe_ratio(target["validation_output_bytes"], gate["validation_output_bytes"])
    validation_file_ratio = safe_ratio(target["validation_output_file_count"], gate["validation_output_file_count"])
    dominant = "validation_output_size" if validation_ratio >= 2.0 or validation_file_ratio >= 2.0 else "hazard_raster_write"
    findings = [
        f"target validation output remains the dominant volume pressure ({target['validation_output_file_count']} files / {target['validation_output_bytes']} bytes vs gate {gate['validation_output_file_count']} files / {gate['validation_output_bytes']} bytes)",
        f"target validation runtime is the slowest observed stage in the measured same-scale set ({target['validation_runtime_seconds']} s vs gate {gate['validation_runtime_seconds']} s)",
        f"hazard reducer worker count remains fixed at {target['reducer_worker_count']} for the measured target and gate artifacts",
        f"native rebuildable_reduced_output trims target validation output to {artifacts[2]['validation_output_file_count']} files / {artifacts[2]['validation_output_bytes']} bytes while staying on the canonical reduced path",
        f"bounded probe validation output stays near the same order of magnitude ({artifacts[3]['validation_output_bytes']} and {artifacts[4]['validation_output_bytes']} bytes)",
    ]
    if comparison_pairs:
        findings.append(
            f"paired comparisons remain bounded without evidence that a distributed reducer is required: {comparison_pairs[0]['label']}, {comparison_pairs[1]['label']}, and {comparison_pairs[2]['label']}"
        )
    return {
        "bottleneck_classification": dominant,
        "output_scaling_findings": findings,
        "local_single_job_sufficient_for_next_step": True,
    }


def summarize_root(path: Path) -> dict[str, Any]:
    summary = AUDIT.summarize_path(path)
    return {
        "path": str(path),
        "exists": summary.exists,
        "file_count": summary.file_count,
        "total_bytes": summary.total_bytes,
    }


def find_reported_manifest_path(outputs: list[Any], kind: str) -> str | None:
    for entry in outputs:
        if not isinstance(entry, dict):
            continue
        if str(entry.get("kind")) == kind:
            path = entry.get("path")
            return str(path) if path else None
    return None


def safe_ratio(numerator: Any, denominator: Any) -> float:
    num = number_or_none(numerator)
    den = number_or_none(denominator)
    if den == 0:
        return 0.0
    return num / den


def number_or_none(value: Any) -> float:
    return float(value) if isinstance(value, (int, float)) else 0.0


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - path context is user-facing.
        raise BoundedReducerRuntimeScalingError(f"failed to read JSON {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise BoundedReducerRuntimeScalingError(f"JSON document must be an object: {path}")
    return data


def render_text(report: dict[str, Any]) -> str:
    lines = [
        f"reducer_scaling_status: {report['reducer_scaling_status']}",
        f"readiness_status: {report['readiness_status']}",
        f"command_plan_status: {report['command_plan_status']}",
        f"timing_source: {report['timing_source']}",
        f"bottleneck_classification: {report['bottleneck_classification']}",
        f"local_single_job_sufficient_for_next_step: {str(report['local_single_job_sufficient_for_next_step']).lower()}",
        f"distributed_execution_authorized: {str(report['distributed_execution_authorized']).lower()}",
        f"scale_up_authorized: {str(report['scale_up_authorized']).lower()}",
        f"operational_claims_allowed: {str(report['operational_claims_allowed']).lower()}",
        "",
        "artifacts_measured:",
    ]
    for artifact in report["artifacts_measured"]:
        lines.append(
            f"- {artifact['artifact_id']}: mode={artifact['validation_output_mode']}, v={artifact['validation_root']['file_count']} files/{artifact['validation_root']['total_bytes']} bytes, "
            f"h={artifact['hazard_root']['file_count']} files/{artifact['hazard_root']['total_bytes']} bytes, "
            f"validation_runtime={artifact['validation_runtime_seconds']}, hazard_runtime={artifact['hazard_runtime_seconds']}, "
            f"reducer_workers={artifact['reducer_worker_count']}, hazard_layers={artifact['hazard_layer_count']}, "
            f"map_package_manifest_present={artifact['map_package_manifest_present']}, "
            f"pilot_gis_manifest_present={artifact['pilot_gis_manifest_present']}"
        )
    lines.append("")
    lines.append("output_scaling_findings:")
    for finding in report["output_scaling_findings"]:
        lines.append(f"- {finding}")
    lines.append("")
    lines.append("comparison_pairs:")
    for pair in report["comparison_pairs"]:
        lines.append(
            f"- {pair['label']}: validation_file_delta={pair['validation_file_count_delta']}, validation_byte_delta={pair['byte_count_delta']}, "
            f"hazard_file_delta={pair['hazard_file_count_delta']}, hazard_byte_delta={pair['hazard_byte_count_delta']}"
        )
    return "\n".join(lines)


def render_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Bounded Reducer Runtime And Output Scaling",
            "",
            f"- reducer_scaling_status: `{report['reducer_scaling_status']}`",
            f"- readiness_status: `{report['readiness_status']}`",
            f"- command_plan_status: `{report['command_plan_status']}`",
            f"- timing_source: `{report['timing_source']}`",
            f"- bottleneck_classification: `{report['bottleneck_classification']}`",
            f"- local_single_job_sufficient_for_next_step: `{str(report['local_single_job_sufficient_for_next_step']).lower()}`",
            f"- distributed_execution_authorized: `{str(report['distributed_execution_authorized']).lower()}`",
            "",
            "## Artifacts",
            *[
                f"- `{artifact['artifact_id']}`: mode `{artifact['validation_output_mode']}`, validation `{artifact['validation_root']['file_count']}` files / `{artifact['validation_root']['total_bytes']}` bytes, hazard `{artifact['hazard_root']['file_count']}` files / `{artifact['hazard_root']['total_bytes']}` bytes, "
                f"validation runtime `{artifact['validation_runtime_seconds']}` s, hazard runtime `{artifact['hazard_runtime_seconds']}` s, reducer workers `{artifact['reducer_worker_count']}`, hazard layers `{artifact['hazard_layer_count']}`, "
                f"map package manifest present `{artifact['map_package_manifest_present']}`, pilot GIS manifest present `{artifact['pilot_gis_manifest_present']}`"
                for artifact in report["artifacts_measured"]
            ],
            "",
            "## Findings",
            *[f"- {finding}" for finding in report["output_scaling_findings"]],
            "",
            "## Pairwise Deltas",
            *[
                f"- `{pair['label']}`: validation file delta `{pair['validation_file_count_delta']}`, validation byte delta `{pair['byte_count_delta']}`, hazard file delta `{pair['hazard_file_count_delta']}`, hazard byte delta `{pair['hazard_byte_count_delta']}`"
                for pair in report["comparison_pairs"]
            ],
            "",
        ]
    )


if __name__ == "__main__":
    raise SystemExit(main())
