#!/usr/bin/env python3
"""Summarize local scaling evidence for the Tschamut conditional pilot.

The summary is intentionally manifest-driven: it reads ignored local run
outputs when they exist, records file/row/byte counts and reducer metadata, and
does not execute simulations or build hazard products.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


DEFAULT_VALIDATION_MANIFEST = Path(
    "validation/private/tschamut_public_pilot/gate_v1/"
    "validation_tschamut_public_conditional_gate_v1_manifest.json"
)
DEFAULT_HAZARD_MANIFEST = Path(
    "hazard/results/tschamut_public_pilot/gate_v1/"
    "validation_tschamut_public_conditional_gate_v1_manifest.json"
)
DEFAULT_GIS_MANIFEST = Path(
    "hazard/results/tschamut_public_pilot/gate_v1/"
    "tschamut_public_conditional_gate_v1_pilot_gis_package_manifest.json"
)


class ScalingSummaryError(ValueError):
    """User-facing scaling summary error."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validation-manifest", type=Path, default=DEFAULT_VALIDATION_MANIFEST)
    parser.add_argument("--hazard-manifest", type=Path, default=DEFAULT_HAZARD_MANIFEST)
    parser.add_argument("--gis-package-manifest", type=Path, default=DEFAULT_GIS_MANIFEST)
    parser.add_argument("--validation-time-file", type=Path)
    parser.add_argument("--hazard-time-file", type=Path)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument(
        "--allow-missing",
        action="store_true",
        help="write a blocked_missing_outputs summary instead of failing when ignored outputs are absent",
    )
    args = parser.parse_args(argv)

    try:
        summary = build_summary(
            args.validation_manifest,
            args.hazard_manifest,
            args.gis_package_manifest,
            validation_time_file=args.validation_time_file,
            hazard_time_file=args.hazard_time_file,
            exclude_paths=[path for path in (args.output_json, args.output_md) if path is not None],
            allow_missing=args.allow_missing,
        )
    except ScalingSummaryError as exc:
        print(f"pilot scaling summary error: {exc}", file=sys.stderr)
        return 2

    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.output_md:
        args.output_md.parent.mkdir(parents=True, exist_ok=True)
        args.output_md.write_text(render_markdown(summary), encoding="utf-8")
    if not args.output_json and not args.output_md:
        print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


def build_summary(
    validation_manifest_path: Path,
    hazard_manifest_path: Path,
    gis_package_manifest_path: Path,
    *,
    validation_time_file: Path | None = None,
    hazard_time_file: Path | None = None,
    exclude_paths: list[Path] | None = None,
    allow_missing: bool = False,
) -> dict[str, Any]:
    required = [validation_manifest_path, hazard_manifest_path]
    missing = [str(path) for path in required if not path.exists()]
    if missing and not allow_missing:
        joined = "\n  - ".join(missing)
        raise ScalingSummaryError(
            "required ignored pilot output manifests are missing; rerun the public "
            "Tschamut gate workflow or pass --allow-missing for a blocked summary:\n"
            f"  - {joined}"
        )
    if missing:
        return {
            "schema_version": "pilot_scaling_summary_v1",
            "pilot_id": "tschamut_public_pilot",
            "run_id": "tschamut_public_conditional_gate_v1",
            "measurement_status": "blocked_missing_outputs",
            "missing_required_manifests": missing,
            "claim_boundary": claim_boundary(),
            "decision": {
                "status": "blocked",
                "next_action": "reproduce the ignored local Tschamut gate outputs before scaling decisions",
            },
        }

    validation_manifest = read_json(validation_manifest_path)
    hazard_manifest = read_json(hazard_manifest_path)
    gis_manifest = read_json(gis_package_manifest_path) if gis_package_manifest_path.exists() else None

    validation_stage = summarize_validation(validation_manifest, validation_manifest_path, validation_time_file)
    hazard_stage = summarize_hazard(hazard_manifest, hazard_manifest_path, hazard_time_file)
    gis_stage = summarize_gis(gis_manifest, gis_package_manifest_path)
    totals = summarize_filesystem_totals(
        [validation_manifest_path.parent, hazard_manifest_path.parent],
        exclude_paths=exclude_paths or [],
    )
    decision = decide_bottleneck(validation_stage, hazard_stage)

    return {
        "schema_version": "pilot_scaling_summary_v1",
        "pilot_id": "tschamut_public_pilot",
        "run_id": "tschamut_public_conditional_gate_v1",
        "measurement_status": "completed_local_manifest_measurement",
        "source_manifests": {
            "validation_manifest": str(validation_manifest_path),
            "hazard_manifest": str(hazard_manifest_path),
            "gis_package_manifest": str(gis_package_manifest_path) if gis_manifest else None,
        },
        "validation_stage": validation_stage,
        "hazard_stage": hazard_stage,
        "gis_package_stage": gis_stage,
        "local_filesystem_totals": totals,
        "claim_boundary": claim_boundary(),
        "decision": decision,
        "limitations": [
            "Metrics are from local ignored pilot outputs and may differ by machine.",
            "Memory peak is reported only when optional /usr/bin/time sidecar files are supplied.",
            "The summary does not change physics, defaults, source zones, block scenarios, or hazard semantics.",
        ],
    }


def summarize_validation(manifest: dict[str, Any], manifest_path: Path, time_file: Path | None) -> dict[str, Any]:
    performance = require_mapping(manifest.get("performance"), "validation.performance")
    outputs = require_list(manifest.get("outputs"), "validation.outputs")
    terrain = require_mapping(manifest.get("terrain"), "validation.terrain")
    return {
        "manifest_path": str(manifest_path),
        "schema_version": manifest.get("schema_version"),
        "case_id": manifest.get("case_id"),
        "terrain": {
            "epsg": terrain.get("epsg"),
            "vertical_datum": terrain.get("vertical_datum"),
            "cell_size_m": terrain.get("cell_size_m") or terrain.get("resolution_m"),
        },
        "performance": select_keys(
            performance,
            [
                "total_wall_seconds",
                "terrain_load_seconds",
                "release_generation_seconds",
                "simulation_seconds",
                "hazard_layer_seconds",
                "output_write_seconds",
                "trajectory_count",
                "impact_event_count",
                "output_file_count",
                "output_bytes",
            ],
        ),
        "external_time": parse_time_file(time_file),
        "outputs": summarize_outputs(outputs),
    }


def summarize_hazard(manifest: dict[str, Any], manifest_path: Path, time_file: Path | None) -> dict[str, Any]:
    performance = require_mapping(manifest.get("performance"), "hazard.performance")
    outputs = require_list(manifest.get("outputs"), "hazard.outputs")
    reducer = manifest.get("reducer_execution")
    if reducer is not None:
        reducer = require_mapping(reducer, "hazard.reducer_execution")
    return {
        "manifest_path": str(manifest_path),
        "schema_version": manifest.get("schema_version"),
        "case_id": manifest.get("case_id"),
        "performance": select_keys(
            performance,
            [
                "total_wall_seconds",
                "accumulation_seconds",
                "trajectory_accumulation_seconds",
                "impact_accumulation_seconds",
                "normalization_seconds",
                "output_write_seconds",
                "core_output_write_seconds",
                "total_hazard_input_rows_read",
                "trajectory_sample_rows_read",
                "impact_event_rows_read",
                "deposition_rows_read",
                "trajectory_files_scanned",
                "impact_csv_files_scanned",
                "output_file_count",
                "output_bytes",
                "hazard_input_rows_per_second",
                "trajectory_rows_per_second",
                "impact_rows_per_second",
            ],
        ),
        "external_time": parse_time_file(time_file),
        "outputs": summarize_outputs(outputs),
        "reducer_execution": summarize_reducer(reducer),
        "raster_exports": manifest.get("raster_exports"),
    }


def summarize_gis(manifest: dict[str, Any] | None, manifest_path: Path) -> dict[str, Any]:
    if manifest is None:
        return {"manifest_path": str(manifest_path), "status": "not_present"}
    return {
        "manifest_path": str(manifest_path),
        "status": "present",
        "schema_version": manifest.get("schema_version"),
        "operational_status": manifest.get("operational_status"),
        "geotiff_count": len(require_list(manifest.get("raster_outputs"), "gis.raster_outputs")),
        "csv_parity_count": len(
            [entry for entry in require_list(manifest.get("parity_outputs"), "gis.parity_outputs") if entry.get("format") == "csv_grid"]
        ),
        "ascii_parity_count": len(
            [
                entry
                for entry in require_list(manifest.get("parity_outputs"), "gis.parity_outputs")
                if entry.get("format") == "esri_ascii_grid"
            ]
        ),
        "visual_qa_status": require_mapping(manifest.get("visual_qa"), "gis.visual_qa").get("status"),
    }


def summarize_outputs(outputs: list[Any]) -> dict[str, Any]:
    entries = [require_mapping(output, "output") for output in outputs]
    total_files = sum_int(entries, "file_count")
    total_rows = sum_int(entries, "row_count")
    total_bytes = sum_int(entries, "total_bytes")
    largest = sorted(
        [
            {
                "kind": entry.get("kind"),
                "format": entry.get("format"),
                "path": entry.get("path"),
                "file_count": entry.get("file_count"),
                "row_count": entry.get("row_count"),
                "total_bytes": entry.get("total_bytes"),
            }
            for entry in entries
            if isinstance(entry.get("total_bytes"), int)
        ],
        key=lambda entry: entry["total_bytes"],
        reverse=True,
    )[:5]
    by_kind: dict[str, dict[str, int]] = {}
    for entry in entries:
        kind = str(entry.get("kind", "unknown"))
        bucket = by_kind.setdefault(kind, {"file_count": 0, "row_count": 0, "total_bytes": 0})
        for key in ("file_count", "row_count", "total_bytes"):
            value = entry.get(key)
            if isinstance(value, int):
                bucket[key] += value
    return {
        "entry_count": len(entries),
        "total_file_count": total_files,
        "total_row_count": total_rows,
        "total_bytes": total_bytes,
        "by_kind": by_kind,
        "largest_outputs": largest,
    }


def summarize_reducer(reducer: dict[str, Any] | None) -> dict[str, Any]:
    if reducer is None:
        return {"status": "not_recorded"}
    return {
        "status": "recorded",
        "schema_version": reducer.get("schema_version"),
        "mode": reducer.get("mode"),
        "worker_count": reducer.get("worker_count"),
        "chunk_count": reducer.get("chunk_count"),
        "merge_order": reducer.get("merge_order"),
        "merge_order_independent": reducer.get("merge_order_independent"),
        "partial_state_storage": reducer.get("partial_state_storage"),
        "full_trajectory_output_default": reducer.get("full_trajectory_output_default"),
    }


def summarize_filesystem_totals(roots: list[Path], *, exclude_paths: list[Path]) -> dict[str, Any]:
    excluded = {path.resolve() for path in exclude_paths}
    root_summaries = []
    total_files = 0
    total_bytes = 0
    for root in roots:
        files = [
            path
            for path in root.rglob("*")
            if path.is_file() and path.resolve() not in excluded
        ] if root.exists() else []
        bytes_for_root = sum(path.stat().st_size for path in files)
        root_summaries.append({"path": str(root), "file_count": len(files), "total_bytes": bytes_for_root})
        total_files += len(files)
        total_bytes += bytes_for_root
    return {"roots": root_summaries, "total_file_count": total_files, "total_bytes": total_bytes}


def decide_bottleneck(validation_stage: dict[str, Any], hazard_stage: dict[str, Any]) -> dict[str, Any]:
    validation_perf = validation_stage["performance"]
    hazard_perf = hazard_stage["performance"]
    hazard_outputs = hazard_stage["outputs"]
    largest = hazard_outputs["largest_outputs"][0] if hazard_outputs["largest_outputs"] else {}

    hazard_write = number_or_zero(hazard_perf.get("output_write_seconds"))
    hazard_accum = number_or_zero(hazard_perf.get("accumulation_seconds"))
    validation_write = number_or_zero(validation_perf.get("output_write_seconds"))
    validation_sim = number_or_zero(validation_perf.get("simulation_seconds"))
    largest_kind = str(largest.get("kind", "unknown"))

    if hazard_write > hazard_accum and "conditional" in largest_kind:
        bottleneck = "hazard_conditional_curve_output_volume"
        next_action = (
            "optimize or gate conditional-curve table and raster output modes before increasing ensemble size"
        )
    elif hazard_write > max(validation_write, validation_sim):
        bottleneck = "hazard_output_writing"
        next_action = "profile hazard output serialization before orchestration work"
    elif validation_sim > hazard_write:
        bottleneck = "trajectory_simulation_runtime"
        next_action = "measure trajectory kernel and event-output costs before increasing ensemble size"
    else:
        bottleneck = "mixed_local_workflow_cost"
        next_action = "repeat with external time sidecars and a larger frozen ensemble before optimization"

    return {
        "status": "no_default_change_recommended",
        "primary_bottleneck": bottleneck,
        "largest_hazard_output_kind": largest_kind,
        "largest_hazard_output_bytes": largest.get("total_bytes"),
        "next_action": next_action,
        "not_recommended_now": [
            "MPI",
            "GPU",
            "SLURM orchestration",
            "annual or physical probability semantics",
            "ensemble-size increase without convergence and output-budget checks",
        ],
    }


def parse_time_file(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {"status": "not_supplied", "elapsed_seconds": None, "max_rss_kb": None}
    if not path.exists():
        return {"status": "missing", "path": str(path), "elapsed_seconds": None, "max_rss_kb": None}
    values: dict[str, Any] = {"status": "recorded", "path": str(path)}
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key == "elapsed_seconds":
            values[key] = float(value)
        elif key == "max_rss_kb":
            values[key] = int(value)
    values.setdefault("elapsed_seconds", None)
    values.setdefault("max_rss_kb", None)
    return values


def render_markdown(summary: dict[str, Any]) -> str:
    if summary["measurement_status"] == "blocked_missing_outputs":
        missing = "\n".join(f"- `{path}`" for path in summary["missing_required_manifests"])
        return (
            "# Tschamut Public Pilot Scaling Review\n\n"
            "Status: blocked because required ignored local outputs are absent.\n\n"
            f"Missing manifests:\n\n{missing}\n"
        )

    validation = summary["validation_stage"]
    hazard = summary["hazard_stage"]
    totals = summary["local_filesystem_totals"]
    decision = summary["decision"]
    return "\n".join(
        [
            "# Tschamut Public Pilot Scaling Review",
            "",
            "Status: local manifest-based scaling and output-volume evidence.",
            "This is a research diagnostic performance note, not validation evidence,",
            "not an operational hazard-map claim, and not an annual or physical",
            "probability product.",
            "",
            "## Commands",
            "",
            "```bash",
            "UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/summarize_pilot_scaling.py \\",
            "  --output-json hazard/results/tschamut_public_pilot/gate_v1/tschamut_public_conditional_gate_v1_scaling_summary.json \\",
            "  --output-md docs/tschamut_public_pilot_scaling_review.md",
            "```",
            "",
            "## Observed Local Metrics",
            "",
            "| Stage | Wall seconds | Output write seconds | Rows read/written | Files | Bytes |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
            stage_row("validation", validation),
            stage_row("hazard", hazard),
            "",
            "Local ignored output tree totals:",
            "",
            f"- Files: `{totals['total_file_count']}`",
            f"- Bytes: `{totals['total_bytes']}`",
            "",
            "External `/usr/bin/time` sidecars:",
            "",
            f"- Validation: `{validation['external_time']['status']}`",
            f"- Hazard: `{hazard['external_time']['status']}`",
            "",
            "## Reducer Evidence",
            "",
            f"- Mode: `{hazard['reducer_execution'].get('mode')}`",
            f"- Worker count: `{hazard['reducer_execution'].get('worker_count')}`",
            f"- Chunk count: `{hazard['reducer_execution'].get('chunk_count')}`",
            f"- Merge order: `{hazard['reducer_execution'].get('merge_order')}`",
            f"- Merge-order independent: `{hazard['reducer_execution'].get('merge_order_independent')}`",
            "",
            "## Bottleneck Decision",
            "",
            f"- Status: `{decision['status']}`",
            f"- Primary bottleneck: `{decision['primary_bottleneck']}`",
            f"- Largest hazard output kind: `{decision['largest_hazard_output_kind']}`",
            f"- Largest hazard output bytes: `{decision['largest_hazard_output_bytes']}`",
            f"- Next action: {decision['next_action']}.",
            "",
            "Do not add MPI, GPU, SLURM orchestration, annual frequency, physical",
            "probability, or ensemble-size increases from this evidence alone.",
            "",
            "## Claim Boundary",
            "",
            "Current products remain conditional intensity-exceedance and",
            "sampling-weighted conditional diagnostics. The scaling summary does not",
            "introduce exposure, vulnerability, consequence, expected loss, return",
            "period, annual frequency, physical probability, or operational map",
            "semantics.",
            "",
        ]
    )


def stage_row(name: str, stage: dict[str, Any]) -> str:
    perf = stage["performance"]
    outputs = stage["outputs"]
    rows = perf.get("total_hazard_input_rows_read") or outputs.get("total_row_count")
    return (
        f"| {name} | {format_number(perf.get('total_wall_seconds'))} | "
        f"{format_number(perf.get('output_write_seconds'))} | "
        f"{format_number(rows)} | {format_number(outputs.get('total_file_count'))} | "
        f"{format_number(outputs.get('total_bytes'))} |"
    )


def read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - path context is user-facing.
        raise ScalingSummaryError(f"failed to read JSON {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ScalingSummaryError(f"JSON document must be an object: {path}")
    return data


def require_mapping(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ScalingSummaryError(f"{name} must be an object")
    return value


def require_list(value: Any, name: str) -> list[Any]:
    if not isinstance(value, list):
        raise ScalingSummaryError(f"{name} must be a list")
    return value


def select_keys(mapping: dict[str, Any], keys: list[str]) -> dict[str, Any]:
    return {key: mapping.get(key) for key in keys if key in mapping}


def sum_int(entries: list[dict[str, Any]], key: str) -> int:
    return sum(value for value in (entry.get(key) for entry in entries) if isinstance(value, int))


def number_or_zero(value: Any) -> float:
    return float(value) if isinstance(value, (int, float)) else 0.0


def format_number(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def claim_boundary() -> dict[str, Any]:
    return {
        "operational_status": "research_diagnostic",
        "current_allowed_product_labels": [
            "conditional_intensity_exceedance",
            "sampling_weighted_conditional",
            "unweighted_diagnostic",
        ],
        "unsupported_product_labels": [
            "annual_intensity_frequency",
            "physical_probability",
            "return_period",
            "risk_map",
            "operational_hazard_map",
        ],
    }


if __name__ == "__main__":
    raise SystemExit(main())
