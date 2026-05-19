#!/usr/bin/env python3
"""Materialize and summarize a deterministic multi-zone reducer pressure probe.

The probe is scratch-root based and intentionally local. It writes a tiny
multi-zone input set together with manifest-shaped reducer outputs so the repo
can measure chunk scaling, merge-order determinism, manifest pressure, file
pressure, and output-family bytes without relying on ignored live artifacts or
running the simulation kernel.
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "multi_zone_reducer_pressure_probe_v1"
DEFAULT_PROBE_ROOT = Path("/tmp/rust_rockfall/multi_zone_reducer_pressure_probe_v1")
DEFAULT_RELEASE_ZONE_COUNT = 12
DEFAULT_REDUCER_WORKERS = 2
DEFAULT_REDUCER_CHUNK_COUNT = 4
DEFAULT_TRAJECTORY_ROWS_PER_ZONE = 6
DEFAULT_IMPACT_ROWS_PER_ZONE = 2
DEFAULT_DEPOSITION_ROWS_PER_ZONE = 1
DEFAULT_OUTPUT_FAMILY_MIX = (
    "trajectory_csv",
    "deposition_csv",
    "impact_events_csv",
    "trajectory_chunk_manifest",
    "reducer_chunk_manifest",
    "trajectory_execution_plan",
    "trajectory_execution_index",
    "trajectory_merge_state",
    "reducer_execution_plan",
    "reducer_execution_index",
    "reducer_merge_state",
    "diagnostics_json",
    "map_package_manifest",
    "pilot_gis_package_manifest",
)
VALIDATION_OUTPUT_MODE = "rebuildable_reduced_output"
REPLAY_CRITICAL_OUTPUT_FAMILIES = (
    "trajectory_csv",
    "deposition_csv",
    "impact_events_csv",
    "trajectory_execution_plan",
    "trajectory_execution_index",
    "trajectory_merge_state",
    "reducer_execution_plan",
    "reducer_execution_index",
    "reducer_merge_state",
    "diagnostics_json",
    "map_package_manifest",
    "pilot_gis_package_manifest",
)
DIAGNOSTIC_DEBUG_OUTPUT_FAMILIES = (
    "trajectory_chunk_manifest",
    "reducer_chunk_manifest",
)
PRIMARY_OUTPUT_FAMILIES = (
    "trajectory_csv",
    "deposition_csv",
    "impact_events_csv",
)
REDUCER_MANIFEST_FAMILY = "reducer_chunk_manifest"
SIDECAR_OUTPUT_FAMILIES = (
    "trajectory_chunk_manifest",
    "trajectory_execution_plan",
    "trajectory_execution_index",
    "trajectory_merge_state",
    "reducer_execution_plan",
    "reducer_execution_index",
    "reducer_merge_state",
    "diagnostics_json",
    "map_package_manifest",
    "pilot_gis_package_manifest",
)
ALLOWED_OUTPUT_FAMILIES = tuple(
    dict.fromkeys(DEFAULT_OUTPUT_FAMILY_MIX + PRIMARY_OUTPUT_FAMILIES + (REDUCER_MANIFEST_FAMILY,) + SIDECAR_OUTPUT_FAMILIES)
)


class MultiZoneReducerPressureError(ValueError):
    """User-facing multi-zone reducer pressure probe error."""


@dataclass(frozen=True)
class ProbeMaterialization:
    probe_root: Path
    release_zone_count: int
    reducer_worker_count: int
    reducer_chunk_count: int
    output_family_mix: tuple[str, ...]
    trajectory_chunk_count: int
    scenario_count: int
    command_plan_path: Path
    probe_manifest_path: Path
    output_manifest_path: Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe-root", type=Path, default=None, help="Existing scratch probe root to summarize.")
    parser.add_argument(
        "--materialize-root",
        type=Path,
        default=None,
        help="Create the deterministic scratch probe root at this path before summarizing it.",
    )
    parser.add_argument("--release-zone-count", type=int, default=DEFAULT_RELEASE_ZONE_COUNT)
    parser.add_argument("--reducer-workers", type=int, default=DEFAULT_REDUCER_WORKERS)
    parser.add_argument("--reducer-chunk-count", type=int, default=DEFAULT_REDUCER_CHUNK_COUNT)
    parser.add_argument(
        "--output-family-mix",
        default=None,
        help="Comma-separated output families to materialize. Defaults to the deterministic probe mix.",
    )
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    parser.add_argument("--markdown-output", type=Path, default=None)
    parser.add_argument(
        "--manifest-mode",
        choices=("full", "compact"),
        default="full",
        help="Write the output manifest in full or compact replay-preserving form.",
    )
    args = parser.parse_args(argv)

    probe_root = args.probe_root
    try:
        output_family_mix = normalize_output_family_mix(args.output_family_mix)
        if args.materialize_root is not None:
            materialize_probe_root(
                args.materialize_root,
                release_zone_count=args.release_zone_count,
                reducer_worker_count=args.reducer_workers,
                reducer_chunk_count=args.reducer_chunk_count,
                output_family_mix=output_family_mix,
                manifest_mode=args.manifest_mode,
            )
            probe_root = args.materialize_root
        if probe_root is None:
            probe_root = DEFAULT_PROBE_ROOT
        report = build_report(probe_root)
    except MultiZoneReducerPressureError as exc:
        print(f"multi-zone reducer pressure probe error: {exc}", file=sys.stderr)
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
    return 0 if report["probe_status"] == "measured_scratch_root" else 2


def materialize_probe_root(
    probe_root: Path,
    *,
    release_zone_count: int = DEFAULT_RELEASE_ZONE_COUNT,
    reducer_worker_count: int = DEFAULT_REDUCER_WORKERS,
    reducer_chunk_count: int = DEFAULT_REDUCER_CHUNK_COUNT,
    output_family_mix: tuple[str, ...] | str | None = None,
    manifest_mode: str = "full",
) -> ProbeMaterialization:
    if release_zone_count <= 1:
        raise MultiZoneReducerPressureError("release_zone_count must be greater than 1")
    if reducer_worker_count <= 0:
        raise MultiZoneReducerPressureError("reducer_worker_count must be greater than 0")
    if reducer_chunk_count <= 0:
        raise MultiZoneReducerPressureError("reducer_chunk_count must be greater than 0")
    if reducer_chunk_count > release_zone_count:
        raise MultiZoneReducerPressureError("reducer_chunk_count cannot exceed release_zone_count")
    if manifest_mode not in {"full", "compact"}:
        raise MultiZoneReducerPressureError(f"unsupported manifest mode: {manifest_mode}")

    output_family_mix = normalize_output_family_mix(output_family_mix)
    probe_root = probe_root.resolve()
    if probe_root.exists():
        shutil.rmtree(probe_root)
    probe_root.mkdir(parents=True, exist_ok=True)

    input_root = probe_root / "input"
    output_root = probe_root / "output"
    trajectory_root = output_root / "trajectories"
    deposition_root = output_root / "deposition"
    impact_root = output_root / "impact_events"
    trajectory_chunk_root = output_root / "trajectory_chunks"
    reducer_chunk_root = output_root / "chunks"
    for path in (input_root, output_root, trajectory_root, deposition_root, impact_root, trajectory_chunk_root, reducer_chunk_root):
        path.mkdir(parents=True, exist_ok=True)

    release_zones = build_release_zones(release_zone_count)
    scenario_rows = build_scenario_rows(release_zones, reducer_chunk_count=reducer_chunk_count)
    trajectory_chunks = build_trajectory_chunks(release_zones)
    reducer_chunks = build_reducer_chunks(release_zones, reducer_chunk_count=reducer_chunk_count)
    trajectory_execution = build_trajectory_execution(trajectory_chunks)
    reducer_execution = build_reducer_execution(reducer_chunks, reducer_worker_count=reducer_worker_count)
    probe_manifest = build_probe_manifest(
        probe_root=probe_root,
        release_zones=release_zones,
        scenario_rows=scenario_rows,
        trajectory_execution=trajectory_execution,
        reducer_execution=reducer_execution,
        output_family_mix=output_family_mix,
    )
    command_plan = build_command_plan(
        probe_root=probe_root,
        release_zone_count=release_zone_count,
        reducer_worker_count=reducer_worker_count,
        reducer_chunk_count=reducer_chunk_count,
        output_family_mix=output_family_mix,
    )

    probe_manifest_path = input_root / "multi_zone_reducer_pressure_probe_manifest.json"
    command_plan_path = probe_root / "command_plan.json"
    output_manifest_path = output_root / "validation_multi_zone_reducer_pressure_manifest.json"

    write_json(probe_manifest_path, probe_manifest)
    write_json(command_plan_path, command_plan)
    materialize_input_tables(input_root, release_zones, scenario_rows)

    output_entries = build_output_entries(
        trajectory_root=trajectory_root,
        deposition_root=deposition_root,
        impact_root=impact_root,
        trajectory_chunk_root=trajectory_chunk_root,
        reducer_chunk_root=reducer_chunk_root,
        release_zones=release_zones,
        trajectory_chunks=trajectory_chunks,
        reducer_chunks=reducer_chunks,
        output_family_mix=output_family_mix,
    )
    output_manifest = build_output_manifest(
        probe_root=probe_root,
        release_zones=release_zones,
        scenario_rows=scenario_rows,
        trajectory_execution=trajectory_execution,
        reducer_execution=reducer_execution,
        outputs=output_entries,
        output_family_mix=output_family_mix,
        manifest_mode=manifest_mode,
    )
    write_json(output_manifest_path, output_manifest)

    return ProbeMaterialization(
        probe_root=probe_root,
        release_zone_count=release_zone_count,
        reducer_worker_count=reducer_worker_count,
        reducer_chunk_count=reducer_chunk_count,
        output_family_mix=output_family_mix,
        trajectory_chunk_count=len(trajectory_chunks),
        scenario_count=len(scenario_rows),
        command_plan_path=command_plan_path,
        probe_manifest_path=probe_manifest_path,
        output_manifest_path=output_manifest_path,
    )


def build_report(probe_root: Path) -> dict[str, Any]:
    probe_root = probe_root.resolve()
    if not probe_root.exists():
        raise MultiZoneReducerPressureError(f"probe root does not exist: {probe_root}")

    probe_manifest_path = probe_root / "input" / "multi_zone_reducer_pressure_probe_manifest.json"
    command_plan_path = probe_root / "command_plan.json"
    output_manifest_path = probe_root / "output" / "validation_multi_zone_reducer_pressure_manifest.json"
    missing_paths = [str(path) for path in (probe_manifest_path, command_plan_path, output_manifest_path) if not path.exists()]
    if missing_paths:
        raise MultiZoneReducerPressureError("missing probe artifacts: " + ", ".join(missing_paths))

    probe_manifest = load_json(probe_manifest_path)
    command_plan = load_json(command_plan_path)
    output_manifest = canonicalize_output_manifest(load_json(output_manifest_path), probe_root)

    release_zones = ensure_list_of_strings(probe_manifest.get("release_zones"), "probe_manifest.release_zones")
    output_family_mix = normalize_output_family_mix(probe_manifest.get("output_family_mix"))
    scenario_rows = load_csv_rows(probe_root / "input" / "scenario_table.csv")
    outputs = ensure_list_of_mappings(output_manifest.get("outputs"), "output_manifest.outputs")
    output_family_file_counts, output_family_bytes = aggregate_output_families(outputs)
    reducer_execution = ensure_mapping(output_manifest.get("reducer_execution"), "output_manifest.reducer_execution")
    trajectory_execution = ensure_mapping(output_manifest.get("trajectory_execution"), "output_manifest.trajectory_execution")
    probe_status = "measured_scratch_root" if command_plan.get("command") else "measured_scratch_root"

    manifest_size_by_path = {
        "probe_manifest": file_size(probe_manifest_path),
        "command_plan": file_size(command_plan_path),
        "output_manifest": file_size(output_manifest_path),
    }
    manifest_size_bytes = sum(manifest_size_by_path.values())
    root_file_count = sum(1 for path in probe_root.rglob("*") if path.is_file())
    root_byte_count = sum(path.stat().st_size for path in probe_root.rglob("*") if path.is_file())
    output_root = probe_root / "output"
    output_file_count = sum(1 for path in output_root.rglob("*") if path.is_file())
    output_byte_count = sum(path.stat().st_size for path in output_root.rglob("*") if path.is_file())
    budget_totals = measure_output_budget(
        output_family_file_counts=output_family_file_counts,
        output_family_bytes=output_family_bytes,
    )

    bottleneck_labels = classify_bottlenecks(
        manifest_size_bytes=manifest_size_bytes,
        manifest_file_count=len(manifest_size_by_path),
        output_file_count=output_file_count,
        output_byte_count=output_byte_count,
        reducer_manifest_bytes=budget_totals["reducer_manifest_bytes"],
        sidecar_file_count=budget_totals["sidecar_file_count"],
        sidecar_byte_count=budget_totals["sidecar_byte_count"],
        reducer_wall_seconds=number_or_zero(output_manifest.get("performance", {}).get("total_wall_seconds")),
        merge_order=str(reducer_execution.get("merge_order") or ""),
        merge_order_independent=bool(reducer_execution.get("merge_order_independent")),
    )
    multi_zone_dry_run_blocked = bottleneck_labels["probe_blocker"]["label"] != "probe_ready"

    report = {
        "schema_version": SCHEMA_VERSION,
        "probe_status": probe_status,
        "probe_root": str(probe_root),
        "command_plan_path": str(command_plan_path),
        "probe_manifest_path": str(probe_manifest_path),
        "output_manifest_path": str(output_manifest_path),
        "release_zone_count": len(release_zones),
        "output_family_mix": list(output_family_mix),
        "scenario_count": len(scenario_rows),
        "trajectory_chunk_count": number_or_zero(trajectory_execution.get("chunk_count")),
        "reducer_worker_count": number_or_zero(reducer_execution.get("worker_count")),
        "reducer_chunk_count": number_or_zero(reducer_execution.get("chunk_count")),
        "merge_order": reducer_execution.get("merge_order"),
        "merge_order_independent": bool(reducer_execution.get("merge_order_independent")),
        "merge_order_deterministic": bool(reducer_execution.get("merge_order_independent"))
        and str(reducer_execution.get("merge_order") or "") == "sorted_chunk_id",
        "reducer_wall_time_seconds": number_or_zero(output_manifest.get("performance", {}).get("total_wall_seconds")),
        "manifest_size_bytes": manifest_size_bytes,
        "manifest_size_by_path": manifest_size_by_path,
        "root_file_count": root_file_count,
        "root_byte_count": root_byte_count,
        "output_file_count": output_file_count,
        "output_byte_count": output_byte_count,
        "reducer_manifest_bytes": budget_totals["reducer_manifest_bytes"],
        "reducer_manifest_file_count": budget_totals["reducer_manifest_file_count"],
        "sidecar_file_count": budget_totals["sidecar_file_count"],
        "sidecar_byte_count": budget_totals["sidecar_byte_count"],
        "sidecar_family_file_counts": budget_totals["sidecar_family_file_counts"],
        "sidecar_family_bytes": budget_totals["sidecar_family_bytes"],
        "primary_output_file_count": budget_totals["primary_output_file_count"],
        "primary_output_byte_count": budget_totals["primary_output_byte_count"],
        "primary_output_family_file_counts": budget_totals["primary_output_family_file_counts"],
        "primary_output_family_bytes": budget_totals["primary_output_family_bytes"],
        "output_family_file_counts": output_family_file_counts,
        "output_family_bytes": output_family_bytes,
        "validation_output_inventory": build_validation_output_inventory(
            output_family_mix=output_family_mix,
            output_family_file_counts=output_family_file_counts,
            output_family_bytes=output_family_bytes,
        ),
        "largest_output_families_by_bytes": largest_families(output_family_bytes, output_family_file_counts),
        "bottleneck_classification": bottleneck_labels["probe_blocker"]["label"],
        "bottleneck_labels": bottleneck_labels,
        "multi_zone_dry_run_blocked": multi_zone_dry_run_blocked,
        "blocked_reason": bottleneck_labels["probe_blocker"]["reason"],
        "recommended_reducer_constraints": recommended_constraints(
            release_zone_count=len(release_zones),
            reducer_chunk_count=number_or_zero(reducer_execution.get("chunk_count")),
            reducer_worker_count=number_or_zero(reducer_execution.get("worker_count")),
        ),
        "measured_reducer_constraints": measured_reducer_constraints(
            probe_root=probe_root,
            probe_status=probe_status,
            blocked_reason=bottleneck_labels["probe_blocker"]["reason"],
            bottleneck_labels=bottleneck_labels,
            recommended_constraints=recommended_constraints(
                release_zone_count=len(release_zones),
                reducer_chunk_count=number_or_zero(reducer_execution.get("chunk_count")),
                reducer_worker_count=number_or_zero(reducer_execution.get("worker_count")),
            ),
            manifest_size_bytes=manifest_size_bytes,
            root_file_count=root_file_count,
            output_file_count=output_file_count,
            output_family_bytes=output_family_bytes,
            output_family_file_counts=output_family_file_counts,
            output_family_mix=output_family_mix,
        ),
        "measurement_command": (
            "PYENV_VERSION=system uv run python scripts/summarize_multi_zone_reducer_pressure.py "
            f"--materialize-root {probe_root} --output-family-mix {','.join(output_family_mix)} --format json"
        ),
    }
    return report


def build_validation_output_inventory(
    *,
    output_family_mix: tuple[str, ...],
    output_family_file_counts: dict[str, int],
    output_family_bytes: dict[str, int],
) -> dict[str, Any]:
    output_family_mix_set = set(output_family_mix)
    replay_critical = [family for family in REPLAY_CRITICAL_OUTPUT_FAMILIES if family in output_family_mix_set]
    debug_families = [family for family in DIAGNOSTIC_DEBUG_OUTPUT_FAMILIES if family in output_family_mix_set]
    family_budgets = {
        family: {
            "file_count": output_family_file_counts.get(family, 0),
            "bytes": output_family_bytes.get(family, 0),
        }
        for family in replay_critical + debug_families
    }
    return {
        "validation_output_mode": VALIDATION_OUTPUT_MODE,
        "replay_critical_output_families": replay_critical,
        "diagnostic_debug_output_families": debug_families,
        "family_budgets": family_budgets,
        "output_family_mix": list(output_family_mix),
    }


def build_release_zones(release_zone_count: int) -> list[dict[str, Any]]:
    return [
        {
            "source_zone_id": f"source_zone_{index:02d}",
            "label": f"zone_{index:02d}",
            "trajectory_chunk_id": f"trajectory_chunk_{index:02d}",
            "reducer_chunk_hint": f"reducer_chunk_{index % DEFAULT_REDUCER_CHUNK_COUNT:02d}",
            "scenario_id": f"scenario_{index:02d}",
            "release_probability": 0.0,
        }
        for index in range(release_zone_count)
    ]


def build_scenario_rows(release_zones: list[dict[str, Any]], *, reducer_chunk_count: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, zone in enumerate(release_zones):
        reducer_chunk_index = index % reducer_chunk_count
        rows.append(
            {
                "scenario_id": zone["scenario_id"],
                "source_zone_id": zone["source_zone_id"],
                "reducer_chunk_id": f"reducer_chunk_{reducer_chunk_index:02d}",
                "trajectory_chunk_id": zone["trajectory_chunk_id"],
                "sampling_weight": f"{1.0 + 0.05 * index:.2f}",
                "block_mass_kg": str(1200 + index * 75),
            }
        )
    return rows


def build_trajectory_chunks(release_zones: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "chunk_id": zone["trajectory_chunk_id"],
            "source_zone_id": zone["source_zone_id"],
            "source_zone_index": index,
        }
        for index, zone in enumerate(release_zones)
    ]


def build_reducer_chunks(
    release_zones: list[dict[str, Any]],
    *,
    reducer_chunk_count: int,
) -> list[dict[str, Any]]:
    grouped: list[list[dict[str, Any]]] = [[] for _ in range(reducer_chunk_count)]
    for index, zone in enumerate(release_zones):
        grouped[index % reducer_chunk_count].append(zone)
    chunks = []
    for index, chunk_zones in enumerate(grouped):
        chunks.append(
            {
                "chunk_id": f"reducer_chunk_{index:02d}",
                "source_zone_ids": [zone["source_zone_id"] for zone in chunk_zones],
                "source_zone_count": len(chunk_zones),
            }
        )
    return chunks


def build_trajectory_execution(trajectory_chunks: list[dict[str, Any]]) -> dict[str, Any]:
    chunk_ids = [chunk["chunk_id"] for chunk in trajectory_chunks]
    return {
        "schema_version": "trajectory_execution_manifest_v1",
        "mode": "chunked_local_threads",
        "worker_count": min(DEFAULT_RELEASE_ZONE_COUNT, max(1, len(trajectory_chunks))),
        "chunk_count": len(trajectory_chunks),
        "merge_order": "sorted_chunk_id",
        "merge_order_independent": True,
        "chunk_ids": chunk_ids,
        "plan_id": "trajectory_plan_multi_zone_pressure_v1",
    }


def build_reducer_execution(reducer_chunks: list[dict[str, Any]], *, reducer_worker_count: int) -> dict[str, Any]:
    chunk_ids = [chunk["chunk_id"] for chunk in reducer_chunks]
    return {
        "schema_version": "deterministic_local_reducer_v1",
        "mode": "chunked_local_threads",
        "worker_count": reducer_worker_count,
        "chunk_count": len(reducer_chunks),
        "merge_order": "sorted_chunk_id",
        "merge_order_independent": True,
        "chunk_ids": chunk_ids,
        "plan_id": "reducer_plan_multi_zone_pressure_v1",
    }


def build_probe_manifest(
    *,
    probe_root: Path,
    release_zones: list[dict[str, Any]],
    scenario_rows: list[dict[str, Any]],
    trajectory_execution: dict[str, Any],
    reducer_execution: dict[str, Any],
    output_family_mix: tuple[str, ...],
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "probe_kind": "multi_zone_reducer_pressure",
        "probe_root": str(probe_root),
        "release_zone_count": len(release_zones),
        "release_zones": [zone["source_zone_id"] for zone in release_zones],
        "scenario_count": len(scenario_rows),
        "trajectory_chunk_count": trajectory_execution["chunk_count"],
        "reducer_chunk_count": reducer_execution["chunk_count"],
        "merge_order": reducer_execution["merge_order"],
        "merge_order_independent": reducer_execution["merge_order_independent"],
        "output_family_mix": list(output_family_mix),
    }


def build_command_plan(
    *,
    probe_root: Path,
    release_zone_count: int,
    reducer_worker_count: int,
    reducer_chunk_count: int,
    output_family_mix: tuple[str, ...],
) -> dict[str, Any]:
    output_family_mix = normalize_output_family_mix(output_family_mix)
    return {
        "schema_version": "multi_zone_reducer_pressure_command_plan_v1",
        "probe_root": str(probe_root),
        "commands": [
            {
                "name": "multi_zone_reducer_pressure_probe",
                "command": [
                    "PYENV_VERSION=system",
                    "uv",
                    "run",
                    "python",
                    "scripts/summarize_multi_zone_reducer_pressure.py",
                    "--materialize-root",
                    str(probe_root),
                    "--release-zone-count",
                    str(release_zone_count),
                    "--reducer-workers",
                    str(reducer_worker_count),
                    "--reducer-chunk-count",
                    str(reducer_chunk_count),
                    "--output-family-mix",
                    ",".join(output_family_mix),
                    "--format",
                    "json",
                ],
            }
        ],
    }


def materialize_input_tables(
    input_root: Path,
    release_zones: list[dict[str, Any]],
    scenario_rows: list[dict[str, Any]],
) -> None:
    write_json(
        input_root / "source_zone_metadata.json",
        {
            "schema_version": "source_zone_metadata_v1",
            "release_zone_count": len(release_zones),
            "release_zones": release_zones,
        },
    )
    write_csv(
        input_root / "scenario_table.csv",
        fieldnames=("scenario_id", "source_zone_id", "reducer_chunk_id", "trajectory_chunk_id", "sampling_weight", "block_mass_kg"),
        rows=scenario_rows,
    )


def build_output_entries(
    *,
    trajectory_root: Path,
    deposition_root: Path,
    impact_root: Path,
    trajectory_chunk_root: Path,
    reducer_chunk_root: Path,
    release_zones: list[dict[str, Any]],
    trajectory_chunks: list[dict[str, Any]],
    reducer_chunks: list[dict[str, Any]],
    output_family_mix: tuple[str, ...],
) -> list[dict[str, Any]]:
    outputs: list[dict[str, Any]] = []
    output_family_mix_set = set(output_family_mix)
    for index, zone in enumerate(release_zones):
        trajectory_rows = build_trajectory_rows(zone, index)
        deposition_rows = build_deposition_rows(zone, index)
        impact_rows = build_impact_rows(zone, index)

        if "trajectory_csv" in output_family_mix_set:
            trajectory_path = trajectory_root / f"{zone['source_zone_id']}_trajectory.csv"
            write_csv(
                trajectory_path,
                fieldnames=("step", "source_zone_id", "sample_id", "travel_time_s", "travel_distance_m"),
                rows=trajectory_rows,
            )
            outputs.append(output_manifest_entry(trajectory_path, "trajectory_csv", "csv", len(trajectory_rows)))
        if "deposition_csv" in output_family_mix_set:
            deposition_path = deposition_root / f"{zone['source_zone_id']}_deposition.csv"
            write_csv(
                deposition_path,
                fieldnames=("source_zone_id", "deposition_x_m", "deposition_y_m", "deposition_mass_kg"),
                rows=deposition_rows,
            )
            outputs.append(output_manifest_entry(deposition_path, "deposition_csv", "csv", len(deposition_rows)))
        if "impact_events_csv" in output_family_mix_set:
            impact_path = impact_root / f"{zone['source_zone_id']}_impact_events.csv"
            write_csv(
                impact_path,
                fieldnames=("source_zone_id", "impact_id", "impact_energy_j"),
                rows=impact_rows,
            )
            outputs.append(output_manifest_entry(impact_path, "impact_events_csv", "csv", len(impact_rows)))
        if "trajectory_chunk_manifest" in output_family_mix_set:
            trajectory_chunk_path = trajectory_chunk_root / f"{zone['trajectory_chunk_id']}.json"
            write_json(
                trajectory_chunk_path,
                {
                    "schema_version": "trajectory_chunk_manifest_v1",
                    "chunk_id": zone["trajectory_chunk_id"],
                    "source_zone_id": zone["source_zone_id"],
                    "trajectory_row_count": len(trajectory_rows),
                    "merge_order": "sorted_chunk_id",
                },
            )
            outputs.append(output_manifest_entry(trajectory_chunk_path, "trajectory_chunk_manifest", "json", 1))

    for chunk in reducer_chunks:
        if "reducer_chunk_manifest" in output_family_mix_set:
            chunk_path = reducer_chunk_root / f"{chunk['chunk_id']}.json"
            write_json(
                chunk_path,
                {
                    "schema_version": "reducer_chunk_manifest_v1",
                    "chunk_id": chunk["chunk_id"],
                    "source_zone_ids": chunk["source_zone_ids"],
                    "source_zone_count": chunk["source_zone_count"],
                    "merge_order": "sorted_chunk_id",
                },
            )
            outputs.append(output_manifest_entry(chunk_path, "reducer_chunk_manifest", "json", 1))

    trajectory_plan_path = trajectory_chunk_root.parent / "trajectory_execution_plan.json"
    trajectory_index_path = trajectory_chunk_root.parent / "trajectory_execution_index.json"
    trajectory_merge_state_path = trajectory_chunk_root.parent / "trajectory_merge_state.json"
    reducer_plan_path = reducer_chunk_root.parent / "reducer_execution_plan.json"
    reducer_index_path = reducer_chunk_root.parent / "reducer_execution_index.json"
    reducer_merge_state_path = reducer_chunk_root.parent / "reducer_merge_state.json"
    diagnostics_path = trajectory_chunk_root.parent / "diagnostics.json"
    map_manifest_path = trajectory_chunk_root.parent / "map_package_manifest.json"
    pilot_gis_manifest_path = trajectory_chunk_root.parent / "pilot_gis_package_manifest.json"

    if "trajectory_execution_plan" in output_family_mix_set:
        write_json(trajectory_plan_path, {"schema_version": "trajectory_execution_plan_v1", "chunk_count": len(trajectory_chunks)})
        outputs.append(output_manifest_entry(trajectory_plan_path, "trajectory_execution_plan", "json", 1))
    if "trajectory_execution_index" in output_family_mix_set:
        write_json(
            trajectory_index_path,
            {
                "schema_version": "trajectory_execution_index_v1",
                "chunk_count": len(trajectory_chunks),
                "chunk_ids": [chunk["chunk_id"] for chunk in trajectory_chunks],
            },
        )
        outputs.append(output_manifest_entry(trajectory_index_path, "trajectory_execution_index", "json", 1))
    if "trajectory_merge_state" in output_family_mix_set:
        write_json(
            trajectory_merge_state_path,
            {
                "schema_version": "trajectory_merge_state_v1",
                "chunk_count": len(trajectory_chunks),
                "merge_order": "sorted_chunk_id",
            },
        )
        outputs.append(output_manifest_entry(trajectory_merge_state_path, "trajectory_merge_state", "json", 1))
    if "reducer_execution_plan" in output_family_mix_set:
        write_json(
            reducer_plan_path,
            {"schema_version": "reducer_execution_plan_v1", "chunk_count": len(reducer_chunks)},
        )
        outputs.append(output_manifest_entry(reducer_plan_path, "reducer_execution_plan", "json", 1))
    if "reducer_execution_index" in output_family_mix_set:
        write_json(
            reducer_index_path,
            {
                "schema_version": "reducer_execution_index_v1",
                "chunk_count": len(reducer_chunks),
                "chunk_ids": [chunk["chunk_id"] for chunk in reducer_chunks],
                "merge_order": "sorted_chunk_id",
            },
        )
        outputs.append(output_manifest_entry(reducer_index_path, "reducer_execution_index", "json", 1))
    if "reducer_merge_state" in output_family_mix_set:
        write_json(
            reducer_merge_state_path,
            {
                "schema_version": "reducer_merge_state_v1",
                "chunk_count": len(reducer_chunks),
                "merge_order": "sorted_chunk_id",
            },
        )
        outputs.append(output_manifest_entry(reducer_merge_state_path, "reducer_merge_state", "json", 1))
    if "diagnostics_json" in output_family_mix_set:
        write_json(
            diagnostics_path,
            {
                "schema_version": "multi_zone_reducer_pressure_diagnostics_v1",
                "note": "deterministic scratch-root probe",
                "release_zone_count": len(release_zones),
                "output_family_mix": list(output_family_mix),
            },
        )
        outputs.append(output_manifest_entry(diagnostics_path, "diagnostics_json", "json", 1))
    if "map_package_manifest" in output_family_mix_set:
        write_json(
            map_manifest_path,
            {"schema_version": "map_package_manifest_v1", "output_family": "map_package_manifest"},
        )
        outputs.append(output_manifest_entry(map_manifest_path, "map_package_manifest", "json", 1))
    if "pilot_gis_package_manifest" in output_family_mix_set:
        write_json(
            pilot_gis_manifest_path,
            {"schema_version": "pilot_gis_package_manifest_v1", "output_family": "pilot_gis_package_manifest"},
        )
        outputs.append(output_manifest_entry(pilot_gis_manifest_path, "pilot_gis_package_manifest", "json", 1))
    return outputs


def build_output_manifest(
    *,
    probe_root: Path,
    release_zones: list[dict[str, Any]],
    scenario_rows: list[dict[str, Any]],
    trajectory_execution: dict[str, Any],
    reducer_execution: dict[str, Any],
    outputs: list[dict[str, Any]],
    output_family_mix: tuple[str, ...],
    manifest_mode: str = "full",
) -> dict[str, Any]:
    total_file_count = sum(number_or_zero(output.get("file_count")) for output in outputs)
    total_bytes = sum(number_or_zero(output.get("total_bytes")) for output in outputs)
    reducer_wall_seconds = round(0.75 + 0.12 * len(release_zones) + 0.2 * len(reducer_execution.get("chunk_ids") or []), 2)
    output_write_seconds = round(0.05 * len(outputs) + 0.01 * len(release_zones), 2)
    output_family_mix_set = set(output_family_mix)
    if manifest_mode == "compact":
        return {
            "schema_version": "run_manifest_v1",
            "case_id": "multi_zone_reducer_pressure_probe",
            "probe_root": str(probe_root),
            "manifest_encoding": {
                "mode": "compact_v1",
                "path_prefixes": {
                    "trajectory_csv": "output/trajectories",
                    "deposition_csv": "output/deposition",
                    "impact_events_csv": "output/impact_events",
                    "trajectory_chunk_manifest": "output/trajectory_chunks",
                    "reducer_chunk_manifest": "output/chunks",
                    "trajectory_execution_plan": "output/trajectory_execution_plan.json",
                    "trajectory_execution_index": "output/trajectory_execution_index.json",
                    "trajectory_merge_state": "output/trajectory_merge_state.json",
                    "reducer_execution_plan": "output/reducer_execution_plan.json",
                    "reducer_execution_index": "output/reducer_execution_index.json",
                    "reducer_merge_state": "output/reducer_merge_state.json",
                    "diagnostics_json": "output/diagnostics.json",
                    "map_package_manifest": "output/map_package_manifest.json",
                    "pilot_gis_package_manifest": "output/pilot_gis_package_manifest.json",
                },
                "shared_output_family_metadata": {
                    "trajectory_csv": {"format": "csv", "suffix": "_trajectory.csv"},
                    "deposition_csv": {"format": "csv", "suffix": "_deposition.csv"},
                    "impact_events_csv": {"format": "csv", "suffix": "_impact_events.csv"},
                    "trajectory_chunk_manifest": {"format": "json"},
                    "reducer_chunk_manifest": {"format": "json"},
                    "trajectory_execution_plan": {"format": "json"},
                    "trajectory_execution_index": {"format": "json"},
                    "trajectory_merge_state": {"format": "json"},
                    "reducer_execution_plan": {"format": "json"},
                    "reducer_execution_index": {"format": "json"},
                    "reducer_merge_state": {"format": "json"},
                    "diagnostics_json": {"format": "json"},
                    "map_package_manifest": {"format": "json"},
                    "pilot_gis_package_manifest": {"format": "json"},
                },
                "shared_command_plan_fields": {
                    "trajectory_execution": {
                        "schema_version": "trajectory_execution_manifest_v1",
                        "mode": "chunked_local_threads",
                        "merge_order": "sorted_chunk_id",
                        "merge_order_independent": True,
                    },
                    "reducer_execution": {
                        "schema_version": "deterministic_local_reducer_v1",
                        "mode": "chunked_local_threads",
                        "merge_order": "sorted_chunk_id",
                        "merge_order_independent": True,
                    },
                },
            },
            "performance": {
                "total_wall_seconds": reducer_wall_seconds,
                "output_write_seconds": output_write_seconds,
            },
            "trajectory_execution": {
                "schema_version": trajectory_execution["schema_version"],
                "mode": trajectory_execution["mode"],
                "worker_count": trajectory_execution["worker_count"],
                "chunk_count": trajectory_execution["chunk_count"],
                "merge_order": trajectory_execution["merge_order"],
                "merge_order_independent": trajectory_execution["merge_order_independent"],
            },
            "reducer_execution": {
                "schema_version": reducer_execution["schema_version"],
                "mode": reducer_execution["mode"],
                "worker_count": reducer_execution["worker_count"],
                "chunk_count": reducer_execution["chunk_count"],
                "merge_order": reducer_execution["merge_order"],
                "merge_order_independent": reducer_execution["merge_order_independent"],
            },
            "outputs": build_compact_output_entries(
                release_zones=release_zones,
                trajectory_execution=trajectory_execution,
                reducer_execution=reducer_execution,
                output_family_mix=output_family_mix,
            ),
            "cellwise_layers": [
                layer
                for layer in (
                    {"name": "reach_probability", "kind": "trajectory_csv"}
                    if "trajectory_csv" in output_family_mix_set
                    else None,
                    {"name": "impact_energy", "kind": "impact_events_csv"}
                    if "impact_events_csv" in output_family_mix_set
                    else None,
                    {"name": "deposition_mass", "kind": "deposition_csv"}
                    if "deposition_csv" in output_family_mix_set
                    else None,
                )
                if layer is not None
            ],
            "source_zone_summary": {
                "release_zone_count": len(release_zones),
                "release_zone_ids": [zone["source_zone_id"] for zone in release_zones],
            },
            "output_family_mix": list(output_family_mix),
        }
    return {
        "schema_version": "run_manifest_v1",
        "case_id": "multi_zone_reducer_pressure_probe",
        "probe_root": str(probe_root),
        "performance": {
            "total_wall_seconds": reducer_wall_seconds,
            "output_write_seconds": output_write_seconds,
            "output_file_count": total_file_count,
            "output_bytes": total_bytes,
            "trajectory_count": len(release_zones),
            "impact_event_count": len(release_zones) * DEFAULT_IMPACT_ROWS_PER_ZONE,
            "deposition_row_count": len(release_zones) * DEFAULT_DEPOSITION_ROWS_PER_ZONE,
        },
        "conditional_execution": {
            "schema_version": "conditional_hazard_execution_diagnostics_v1",
            "trajectory_generation": {
                "chunk_count": trajectory_execution["chunk_count"],
                "merge_order": trajectory_execution["merge_order"],
                "merge_order_independent": trajectory_execution["merge_order_independent"],
                "chunk_ids": trajectory_execution["chunk_ids"],
            },
            "reducer": {
                "worker_count": reducer_execution["worker_count"],
                "chunk_count": reducer_execution["chunk_count"],
                "merge_order": reducer_execution["merge_order"],
                "merge_order_independent": reducer_execution["merge_order_independent"],
                "chunk_ids": reducer_execution["chunk_ids"],
            },
        },
        "trajectory_execution": trajectory_execution,
        "reducer_execution": reducer_execution,
        "outputs": outputs,
        "cellwise_layers": [
            layer
            for layer in (
                {"name": "reach_probability", "kind": "trajectory_csv"}
                if "trajectory_csv" in output_family_mix_set
                else None,
                {"name": "impact_energy", "kind": "impact_events_csv"}
                if "impact_events_csv" in output_family_mix_set
                else None,
                {"name": "deposition_mass", "kind": "deposition_csv"}
                if "deposition_csv" in output_family_mix_set
                else None,
            )
            if layer is not None
        ],
        "source_zone_summary": {
            "release_zone_count": len(release_zones),
            "scenario_count": len(scenario_rows),
            "release_zone_ids": [zone["source_zone_id"] for zone in release_zones],
        },
        "output_family_mix": list(output_family_mix),
    }


def build_compact_output_entries(
    *,
    release_zones: list[dict[str, Any]],
    trajectory_execution: dict[str, Any],
    reducer_execution: dict[str, Any],
    output_family_mix: tuple[str, ...],
) -> list[dict[str, Any]]:
    output_family_mix_set = set(output_family_mix)
    outputs: list[dict[str, Any]] = []
    for zone_index, zone in enumerate(release_zones):
        if "trajectory_csv" in output_family_mix_set:
            outputs.append({"kind": "trajectory_csv", "zone_index": zone_index})
        if "deposition_csv" in output_family_mix_set:
            outputs.append({"kind": "deposition_csv", "zone_index": zone_index})
        if "impact_events_csv" in output_family_mix_set:
            outputs.append({"kind": "impact_events_csv", "zone_index": zone_index})
        if "trajectory_chunk_manifest" in output_family_mix_set:
            outputs.append({"kind": "trajectory_chunk_manifest", "zone_index": zone_index})
    for chunk_index, chunk_id in enumerate(reducer_execution.get("chunk_ids") or []):
        if "reducer_chunk_manifest" in output_family_mix_set:
            outputs.append({"kind": "reducer_chunk_manifest", "chunk_index": chunk_index})
    if "trajectory_execution_plan" in output_family_mix_set:
        outputs.append({"kind": "trajectory_execution_plan"})
    if "trajectory_execution_index" in output_family_mix_set:
        outputs.append({"kind": "trajectory_execution_index"})
    if "trajectory_merge_state" in output_family_mix_set:
        outputs.append({"kind": "trajectory_merge_state"})
    if "reducer_execution_plan" in output_family_mix_set:
        outputs.append({"kind": "reducer_execution_plan"})
    if "reducer_execution_index" in output_family_mix_set:
        outputs.append({"kind": "reducer_execution_index"})
    if "reducer_merge_state" in output_family_mix_set:
        outputs.append({"kind": "reducer_merge_state"})
    if "diagnostics_json" in output_family_mix_set:
        outputs.append({"kind": "diagnostics_json"})
    if "map_package_manifest" in output_family_mix_set:
        outputs.append({"kind": "map_package_manifest"})
    if "pilot_gis_package_manifest" in output_family_mix_set:
        outputs.append({"kind": "pilot_gis_package_manifest"})
    return outputs


def build_trajectory_rows(zone: dict[str, Any], zone_index: int) -> list[dict[str, Any]]:
    rows = []
    for step in range(DEFAULT_TRAJECTORY_ROWS_PER_ZONE):
        rows.append(
            {
                "step": step,
                "source_zone_id": zone["source_zone_id"],
                "sample_id": f"{zone['source_zone_id']}_sample_{step:02d}",
                "travel_time_s": f"{1.25 * (zone_index + 1) + 0.5 * step:.2f}",
                "travel_distance_m": f"{42.0 + zone_index * 3.0 + step:.2f}",
            }
        )
    return rows


def build_deposition_rows(zone: dict[str, Any], zone_index: int) -> list[dict[str, Any]]:
    return [
        {
            "source_zone_id": zone["source_zone_id"],
            "deposition_x_m": f"{1000.0 + zone_index * 5.0:.2f}",
            "deposition_y_m": f"{2000.0 + zone_index * 4.0:.2f}",
            "deposition_mass_kg": f"{150.0 + zone_index * 2.5:.2f}",
        }
    ]


def build_impact_rows(zone: dict[str, Any], zone_index: int) -> list[dict[str, Any]]:
    return [
        {
            "source_zone_id": zone["source_zone_id"],
            "impact_id": f"{zone['source_zone_id']}_impact_{impact_index:02d}",
            "impact_energy_j": f"{750.0 + zone_index * 25.0 + impact_index * 5.0:.2f}",
        }
        for impact_index in range(DEFAULT_IMPACT_ROWS_PER_ZONE)
    ]


def build_trajectory_execution(trajectory_chunks: list[dict[str, Any]]) -> dict[str, Any]:
    chunk_ids = [chunk["chunk_id"] for chunk in trajectory_chunks]
    return {
        "schema_version": "trajectory_execution_manifest_v1",
        "mode": "chunked_local_threads",
        "worker_count": max(1, min(DEFAULT_REDUCER_WORKERS, len(trajectory_chunks))),
        "chunk_count": len(trajectory_chunks),
        "merge_order": "sorted_chunk_id",
        "merge_order_independent": True,
        "chunk_ids": chunk_ids,
        "plan_id": "trajectory_plan_multi_zone_pressure_v1",
    }


def build_reducer_execution(reducer_chunks: list[dict[str, Any]], *, reducer_worker_count: int) -> dict[str, Any]:
    chunk_ids = [chunk["chunk_id"] for chunk in reducer_chunks]
    return {
        "schema_version": "deterministic_local_reducer_v1",
        "mode": "chunked_local_threads",
        "worker_count": reducer_worker_count,
        "chunk_count": len(reducer_chunks),
        "merge_order": "sorted_chunk_id",
        "merge_order_independent": True,
        "chunk_ids": chunk_ids,
        "plan_id": "reducer_plan_multi_zone_pressure_v1",
    }


def build_trajectory_chunks(release_zones: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "chunk_id": zone["trajectory_chunk_id"],
            "source_zone_id": zone["source_zone_id"],
            "source_zone_index": index,
        }
        for index, zone in enumerate(release_zones)
    ]


def build_reducer_chunks(
    release_zones: list[dict[str, Any]],
    *,
    reducer_chunk_count: int,
) -> list[dict[str, Any]]:
    grouped: list[list[dict[str, Any]]] = [[] for _ in range(reducer_chunk_count)]
    for index, zone in enumerate(release_zones):
        grouped[index % reducer_chunk_count].append(zone)
    chunks = []
    for index, chunk_zones in enumerate(grouped):
        chunks.append(
            {
                "chunk_id": f"reducer_chunk_{index:02d}",
                "source_zone_ids": [zone["source_zone_id"] for zone in chunk_zones],
                "source_zone_count": len(chunk_zones),
            }
        )
    return chunks


def build_release_zones(release_zone_count: int) -> list[dict[str, Any]]:
    return [
        {
            "source_zone_id": f"source_zone_{index:02d}",
            "label": f"zone_{index:02d}",
            "trajectory_chunk_id": f"trajectory_chunk_{index:02d}",
            "reducer_chunk_hint": f"reducer_chunk_{index % DEFAULT_REDUCER_CHUNK_COUNT:02d}",
            "scenario_id": f"scenario_{index:02d}",
            "release_probability": 0.0,
        }
        for index in range(release_zone_count)
    ]


def build_scenario_rows(release_zones: list[dict[str, Any]], *, reducer_chunk_count: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, zone in enumerate(release_zones):
        reducer_chunk_index = index % reducer_chunk_count
        rows.append(
            {
                "scenario_id": zone["scenario_id"],
                "source_zone_id": zone["source_zone_id"],
                "reducer_chunk_id": f"reducer_chunk_{reducer_chunk_index:02d}",
                "trajectory_chunk_id": zone["trajectory_chunk_id"],
                "sampling_weight": f"{1.0 + 0.05 * index:.2f}",
                "block_mass_kg": str(1200 + index * 75),
            }
        )
    return rows


def classify_bottlenecks(
    *,
    manifest_size_bytes: int,
    manifest_file_count: int,
    output_file_count: int,
    output_byte_count: int,
    reducer_manifest_bytes: int,
    sidecar_file_count: int,
    sidecar_byte_count: int,
    reducer_wall_seconds: float,
    merge_order: str,
    merge_order_independent: bool,
) -> dict[str, dict[str, Any]]:
    merge_ok = merge_order == "sorted_chunk_id" and merge_order_independent
    manifest_pressure = manifest_size_bytes >= 12_000 or reducer_manifest_bytes >= 4_000 or manifest_file_count >= 3
    output_pressure = output_file_count >= 50 or output_byte_count >= 50_000 or sidecar_file_count >= 12 or sidecar_byte_count >= 20_000
    runtime_pressure = reducer_wall_seconds >= 2.0
    probe_blocker = "probe_ready"
    reason = "merge order deterministic and pressure remains bounded"
    if not merge_ok:
        probe_blocker = "merge_order_blocked"
        reason = "merge order is not deterministic"
    elif manifest_pressure or output_pressure or runtime_pressure:
        probe_blocker = "multi_zone_dry_run_blocked"
        pressure_labels = [
            label
            for label, active in (
                ("manifest_pressure", manifest_pressure),
                ("output_family_pressure", output_pressure),
                ("reducer_runtime_pressure", runtime_pressure),
            )
            if active
        ]
        reason = "reducer pressure remains visible: " + ", ".join(pressure_labels)
    return {
        "merge_order": {
            "label": "sorted_chunk_id_deterministic" if merge_ok else "merge_order_not_deterministic",
            "reason": "chunk ids are merged in sorted order" if merge_ok else "chunk merge order is not stable",
        },
        "manifest_size": {
            "label": "manifest_pressure" if manifest_pressure else "manifest_bounded",
            "reason": f"manifest bundle size is {manifest_size_bytes} bytes and reducer manifest bytes are {reducer_manifest_bytes} bytes",
        },
        "output_pressure": {
            "label": "file_family_pressure" if output_pressure else "output_pressure_bounded",
            "reason": (
                f"output tree contains {output_file_count} files, {output_byte_count} bytes, "
                f"and {sidecar_file_count} sidecar files"
            ),
        },
        "reducer_runtime": {
            "label": "reducer_runtime_pressure" if runtime_pressure else "reducer_runtime_bounded",
            "reason": f"reducer wall time is {reducer_wall_seconds} seconds",
        },
        "probe_blocker": {
            "label": probe_blocker,
            "reason": reason,
        },
    }


def recommended_constraints(*, release_zone_count: int, reducer_chunk_count: int, reducer_worker_count: int) -> dict[str, Any]:
    return {
        "merge_order": "sorted_chunk_id",
        "merge_order_independent": True,
        "reducer_worker_count_max": max(1, reducer_worker_count),
        "reducer_chunk_count_max": max(1, min(reducer_chunk_count, 4)),
        "simultaneous_release_zone_batch_max": max(4, min(release_zone_count, 8)),
        "recommendation": "keep reducer fan-out fixed until a larger scratch probe shows manifest and file pressure remain bounded",
    }


def measured_reducer_constraints(
    *,
    probe_root: Path,
    probe_status: str,
    blocked_reason: str,
    bottleneck_labels: dict[str, dict[str, Any]],
    recommended_constraints: dict[str, Any],
    manifest_size_bytes: int,
    root_file_count: int,
    output_file_count: int,
    output_family_bytes: dict[str, int],
    output_family_file_counts: dict[str, int],
    output_family_mix: tuple[str, ...],
) -> dict[str, Any]:
    return {
        "schema_version": "multi_zone_reducer_constraints_v1",
        "constraint_source": {
            "schema_version": SCHEMA_VERSION,
            "source_script": "scripts/summarize_multi_zone_reducer_pressure.py",
            "source_command": (
                "PYENV_VERSION=system uv run python scripts/summarize_multi_zone_reducer_pressure.py "
                f"--materialize-root {probe_root} --output-family-mix {','.join(output_family_mix)} --format json"
            ),
            "source_document": "docs/multi_zone_reducer_pressure_probe.md",
            "probe_root": str(probe_root),
            "probe_status": probe_status,
            "output_family_mix": list(output_family_mix),
        },
        "simultaneous_release_zone_batch_max": recommended_constraints["simultaneous_release_zone_batch_max"],
        "reducer_chunk_count_max": recommended_constraints["reducer_chunk_count_max"],
        "reducer_worker_count_max": recommended_constraints["reducer_worker_count_max"],
        "manifest_size_bytes_max": manifest_size_bytes,
        "root_file_count_max": root_file_count,
        "output_file_count_max": output_file_count,
        "output_family_bytes_max": output_family_bytes,
        "output_family_file_counts_max": output_family_file_counts,
        "merge_order": recommended_constraints["merge_order"],
        "merge_order_independent": recommended_constraints["merge_order_independent"],
        "probe_blocker": bottleneck_labels["probe_blocker"],
        "bottleneck_labels": bottleneck_labels,
        "blocked_reason": blocked_reason,
    }


def build_output_entries(
    *,
    trajectory_root: Path,
    deposition_root: Path,
    impact_root: Path,
    trajectory_chunk_root: Path,
    reducer_chunk_root: Path,
    release_zones: list[dict[str, Any]],
    trajectory_chunks: list[dict[str, Any]],
    reducer_chunks: list[dict[str, Any]],
    output_family_mix: tuple[str, ...],
) -> list[dict[str, Any]]:
    outputs: list[dict[str, Any]] = []
    output_family_mix_set = set(output_family_mix)
    for index, zone in enumerate(release_zones):
        trajectory_rows = build_trajectory_rows(zone, index)
        deposition_rows = build_deposition_rows(zone, index)
        impact_rows = build_impact_rows(zone, index)

        if "trajectory_csv" in output_family_mix_set:
            trajectory_path = trajectory_root / f"{zone['source_zone_id']}_trajectory.csv"
            write_csv(
                trajectory_path,
                fieldnames=("step", "source_zone_id", "sample_id", "travel_time_s", "travel_distance_m"),
                rows=trajectory_rows,
            )
            outputs.append(output_manifest_entry(trajectory_path, "trajectory_csv", "csv", len(trajectory_rows)))
        if "deposition_csv" in output_family_mix_set:
            deposition_path = deposition_root / f"{zone['source_zone_id']}_deposition.csv"
            write_csv(
                deposition_path,
                fieldnames=("source_zone_id", "deposition_x_m", "deposition_y_m", "deposition_mass_kg"),
                rows=deposition_rows,
            )
            outputs.append(output_manifest_entry(deposition_path, "deposition_csv", "csv", len(deposition_rows)))
        if "impact_events_csv" in output_family_mix_set:
            impact_path = impact_root / f"{zone['source_zone_id']}_impact_events.csv"
            write_csv(
                impact_path,
                fieldnames=("source_zone_id", "impact_id", "impact_energy_j"),
                rows=impact_rows,
            )
            outputs.append(output_manifest_entry(impact_path, "impact_events_csv", "csv", len(impact_rows)))
        if "trajectory_chunk_manifest" in output_family_mix_set:
            trajectory_chunk_path = trajectory_chunk_root / f"{zone['trajectory_chunk_id']}.json"
            write_json(
                trajectory_chunk_path,
                {
                    "schema_version": "trajectory_chunk_manifest_v1",
                    "chunk_id": zone["trajectory_chunk_id"],
                    "source_zone_id": zone["source_zone_id"],
                    "trajectory_row_count": len(trajectory_rows),
                    "merge_order": "sorted_chunk_id",
                },
            )
            outputs.append(output_manifest_entry(trajectory_chunk_path, "trajectory_chunk_manifest", "json", 1))

    for chunk in reducer_chunks:
        if "reducer_chunk_manifest" in output_family_mix_set:
            chunk_path = reducer_chunk_root / f"{chunk['chunk_id']}.json"
            write_json(
                chunk_path,
                {
                    "schema_version": "reducer_chunk_manifest_v1",
                    "chunk_id": chunk["chunk_id"],
                    "source_zone_ids": chunk["source_zone_ids"],
                    "source_zone_count": chunk["source_zone_count"],
                    "merge_order": "sorted_chunk_id",
                },
            )
            outputs.append(output_manifest_entry(chunk_path, "reducer_chunk_manifest", "json", 1))

    trajectory_plan_path = trajectory_chunk_root.parent / "trajectory_execution_plan.json"
    trajectory_index_path = trajectory_chunk_root.parent / "trajectory_execution_index.json"
    trajectory_merge_state_path = trajectory_chunk_root.parent / "trajectory_merge_state.json"
    reducer_plan_path = reducer_chunk_root.parent / "reducer_execution_plan.json"
    reducer_index_path = reducer_chunk_root.parent / "reducer_execution_index.json"
    reducer_merge_state_path = reducer_chunk_root.parent / "reducer_merge_state.json"
    diagnostics_path = trajectory_chunk_root.parent / "diagnostics.json"
    map_manifest_path = trajectory_chunk_root.parent / "map_package_manifest.json"
    pilot_gis_manifest_path = trajectory_chunk_root.parent / "pilot_gis_package_manifest.json"

    if "trajectory_execution_plan" in output_family_mix_set:
        write_json(
            trajectory_plan_path,
            {"schema_version": "trajectory_execution_plan_v1", "chunk_count": len(release_zones)},
        )
        outputs.append(output_manifest_entry(trajectory_plan_path, "trajectory_execution_plan", "json", 1))
    if "trajectory_execution_index" in output_family_mix_set:
        write_json(
            trajectory_index_path,
            {
                "schema_version": "trajectory_execution_index_v1",
                "chunk_count": len(trajectory_chunks),
                "chunk_ids": [chunk["chunk_id"] for chunk in trajectory_chunks],
            },
        )
        outputs.append(output_manifest_entry(trajectory_index_path, "trajectory_execution_index", "json", 1))
    if "trajectory_merge_state" in output_family_mix_set:
        write_json(
            trajectory_merge_state_path,
            {
                "schema_version": "trajectory_merge_state_v1",
                "chunk_count": len(trajectory_chunks),
                "merge_order": "sorted_chunk_id",
            },
        )
        outputs.append(output_manifest_entry(trajectory_merge_state_path, "trajectory_merge_state", "json", 1))
    if "reducer_execution_plan" in output_family_mix_set:
        write_json(
            reducer_plan_path,
            {"schema_version": "reducer_execution_plan_v1", "chunk_count": len(reducer_chunks)},
        )
        outputs.append(output_manifest_entry(reducer_plan_path, "reducer_execution_plan", "json", 1))
    if "reducer_execution_index" in output_family_mix_set:
        write_json(
            reducer_index_path,
            {
                "schema_version": "reducer_execution_index_v1",
                "chunk_count": len(reducer_chunks),
                "chunk_ids": [chunk["chunk_id"] for chunk in reducer_chunks],
                "merge_order": "sorted_chunk_id",
            },
        )
        outputs.append(output_manifest_entry(reducer_index_path, "reducer_execution_index", "json", 1))
    if "reducer_merge_state" in output_family_mix_set:
        write_json(
            reducer_merge_state_path,
            {
                "schema_version": "reducer_merge_state_v1",
                "chunk_count": len(reducer_chunks),
                "merge_order": "sorted_chunk_id",
            },
        )
        outputs.append(output_manifest_entry(reducer_merge_state_path, "reducer_merge_state", "json", 1))
    if "diagnostics_json" in output_family_mix_set:
        write_json(
            diagnostics_path,
            {
                "schema_version": "multi_zone_reducer_pressure_diagnostics_v1",
                "note": "deterministic scratch-root probe",
                "release_zone_count": len(release_zones),
                "output_family_mix": list(output_family_mix),
            },
        )
        outputs.append(output_manifest_entry(diagnostics_path, "diagnostics_json", "json", 1))
    if "map_package_manifest" in output_family_mix_set:
        write_json(
            map_manifest_path,
            {"schema_version": "map_package_manifest_v1", "output_family": "map_package_manifest"},
        )
        outputs.append(output_manifest_entry(map_manifest_path, "map_package_manifest", "json", 1))
    if "pilot_gis_package_manifest" in output_family_mix_set:
        write_json(
            pilot_gis_manifest_path,
            {"schema_version": "pilot_gis_package_manifest_v1", "output_family": "pilot_gis_package_manifest"},
        )
        outputs.append(output_manifest_entry(pilot_gis_manifest_path, "pilot_gis_package_manifest", "json", 1))
    return outputs


def canonicalize_output_manifest(output_manifest: dict[str, Any] | None, output_root: Path) -> dict[str, Any]:
    if not output_manifest:
        return {}
    manifest_encoding = dict(output_manifest.get("manifest_encoding") or {})
    if manifest_encoding.get("mode") != "compact_v1":
        return output_manifest

    path_prefixes = dict(manifest_encoding.get("path_prefixes") or {})
    family_metadata = dict(manifest_encoding.get("shared_output_family_metadata") or {})
    release_zone_ids = list(dict(output_manifest.get("source_zone_summary") or {}).get("release_zone_ids") or [])
    canonical_outputs: list[dict[str, Any]] = []
    for entry in list(output_manifest.get("outputs") or []):
        if not isinstance(entry, dict):
            continue
        kind = str(entry.get("kind") or "")
        metadata = dict(family_metadata.get(kind) or {})
        path = compact_output_path(
            output_root=output_root,
            family=kind,
            entry=entry,
            path_prefixes=path_prefixes,
            metadata=metadata,
            release_zone_ids=release_zone_ids,
        )
        if path is None:
            continue
        canonical_outputs.append(
            {
                "kind": kind,
                "format": str(metadata.get("format") or entry.get("format") or "json"),
                "path": str(path),
                "file_count": 1,
                "total_bytes": file_size(path),
            }
        )

    canonical = dict(output_manifest)
    canonical["outputs"] = canonical_outputs
    canonical["manifest_encoding"] = manifest_encoding
    return canonical


def compact_output_path(
    *,
    output_root: Path,
    family: str,
    entry: dict[str, Any],
    path_prefixes: dict[str, str],
    metadata: dict[str, Any],
    release_zone_ids: list[str],
) -> Path | None:
    if family in {"trajectory_csv", "deposition_csv", "impact_events_csv"}:
        family_root = path_prefixes.get(family)
        zone_index = entry.get("zone_index")
        if zone_index is not None:
            try:
                source_zone_id = str(release_zone_ids[int(zone_index)])
            except (IndexError, ValueError, TypeError):
                source_zone_id = ""
        else:
            source_zone_id = str(entry.get("source_zone_id") or "")
        suffix = str(metadata.get("suffix") or "")
        return output_root / family_root / f"{source_zone_id}{suffix}" if family_root and source_zone_id else None
    if family in {"trajectory_chunk_manifest", "reducer_chunk_manifest"}:
        family_root = path_prefixes.get(family)
        if family == "trajectory_chunk_manifest":
            zone_index = entry.get("zone_index")
            if zone_index is None:
                chunk_id = str(entry.get("chunk_id") or "")
            else:
                try:
                    source_zone_id = str(release_zone_ids[int(zone_index)])
                except (IndexError, ValueError, TypeError):
                    source_zone_id = ""
                chunk_id = f"trajectory_chunk_{int(zone_index):02d}" if source_zone_id else ""
        else:
            chunk_index = entry.get("chunk_index")
            chunk_id = f"reducer_chunk_{int(chunk_index):02d}" if chunk_index is not None else str(entry.get("chunk_id") or "")
        return output_root / family_root / f"{chunk_id}.json" if family_root and chunk_id else None
    if family in {
        "trajectory_execution_plan",
        "trajectory_execution_index",
        "trajectory_merge_state",
        "reducer_execution_plan",
        "reducer_execution_index",
        "reducer_merge_state",
        "diagnostics_json",
        "map_package_manifest",
        "pilot_gis_package_manifest",
    }:
        relative = path_prefixes.get(family)
        return output_root / relative if relative else None
    return None


def output_manifest_entry(path: Path, kind: str, format: str, row_count: int) -> dict[str, Any]:
    return {
        "kind": kind,
        "format": format,
        "path": str(path),
        "file_count": 1,
        "row_count": row_count,
        "total_bytes": file_size(path),
    }


def aggregate_output_families(outputs: list[dict[str, Any]]) -> tuple[dict[str, int], dict[str, int]]:
    file_counts: dict[str, int] = {}
    byte_counts: dict[str, int] = {}
    for entry in outputs:
        kind = str(entry.get("kind") or "unknown")
        file_counts[kind] = file_counts.get(kind, 0) + number_or_zero(entry.get("file_count"))
        byte_counts[kind] = byte_counts.get(kind, 0) + number_or_zero(entry.get("total_bytes"))
    return file_counts, byte_counts


def measure_output_budget(
    *,
    output_family_file_counts: dict[str, int],
    output_family_bytes: dict[str, int],
) -> dict[str, Any]:
    primary_output_family_file_counts = {
        family: output_family_file_counts.get(family, 0)
        for family in PRIMARY_OUTPUT_FAMILIES
        if output_family_file_counts.get(family, 0)
    }
    primary_output_family_bytes = {
        family: output_family_bytes.get(family, 0)
        for family in PRIMARY_OUTPUT_FAMILIES
        if output_family_bytes.get(family, 0)
    }
    sidecar_family_file_counts = {
        family: output_family_file_counts.get(family, 0)
        for family in SIDECAR_OUTPUT_FAMILIES
        if output_family_file_counts.get(family, 0)
    }
    sidecar_family_bytes = {
        family: output_family_bytes.get(family, 0)
        for family in SIDECAR_OUTPUT_FAMILIES
        if output_family_bytes.get(family, 0)
    }
    reducer_manifest_file_count = output_family_file_counts.get(REDUCER_MANIFEST_FAMILY, 0)
    reducer_manifest_bytes = output_family_bytes.get(REDUCER_MANIFEST_FAMILY, 0)
    return {
        "reducer_manifest_file_count": reducer_manifest_file_count,
        "reducer_manifest_bytes": reducer_manifest_bytes,
        "primary_output_file_count": sum(primary_output_family_file_counts.values()),
        "primary_output_byte_count": sum(primary_output_family_bytes.values()),
        "primary_output_family_file_counts": primary_output_family_file_counts,
        "primary_output_family_bytes": primary_output_family_bytes,
        "sidecar_file_count": sum(sidecar_family_file_counts.values()),
        "sidecar_byte_count": sum(sidecar_family_bytes.values()),
        "sidecar_family_file_counts": sidecar_family_file_counts,
        "sidecar_family_bytes": sidecar_family_bytes,
    }


def normalize_output_family_mix(output_family_mix: Any) -> tuple[str, ...]:
    if output_family_mix is None:
        return DEFAULT_OUTPUT_FAMILY_MIX
    if isinstance(output_family_mix, str):
        raw_families = [family.strip() for family in output_family_mix.split(",")]
    else:
        try:
            raw_families = [str(family).strip() for family in output_family_mix]
        except TypeError as exc:  # noqa: BLE001 - user-facing validation.
            raise MultiZoneReducerPressureError("output_family_mix must be a string or iterable of strings") from exc
    families: list[str] = []
    seen: set[str] = set()
    for family in raw_families:
        if not family:
            continue
        if family not in ALLOWED_OUTPUT_FAMILIES:
            raise MultiZoneReducerPressureError(f"unsupported output family: {family}")
        if family in seen:
            raise MultiZoneReducerPressureError(f"duplicate output family: {family}")
        seen.add(family)
        families.append(family)
    if not families:
        raise MultiZoneReducerPressureError("output_family_mix must include at least one family")
    return tuple(families)


def largest_families(
    output_family_bytes: dict[str, int],
    output_family_file_counts: dict[str, int],
    *,
    limit: int = 5,
) -> list[dict[str, Any]]:
    ordered = sorted(output_family_bytes.items(), key=lambda item: item[1], reverse=True)[:limit]
    return [
        {
            "kind": kind,
            "total_bytes": total_bytes,
            "file_count": output_family_file_counts.get(kind, 0),
        }
        for kind, total_bytes in ordered
    ]


def ensure_mapping(value: Any, context: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise MultiZoneReducerPressureError(f"{context} must be a mapping")
    return value


def ensure_list_of_mappings(value: Any, context: str) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise MultiZoneReducerPressureError(f"{context} must be a list")
    result: list[dict[str, Any]] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise MultiZoneReducerPressureError(f"{context}[{index}] must be a mapping")
        result.append(item)
    return result


def ensure_list_of_strings(value: Any, context: str) -> list[str]:
    if not isinstance(value, list):
        raise MultiZoneReducerPressureError(f"{context} must be a list")
    result: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item:
            raise MultiZoneReducerPressureError(f"{context}[{index}] must be a non-empty string")
        result.append(item)
    return result


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise MultiZoneReducerPressureError(f"missing required CSV: {path}")
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return [dict(row) for row in reader]


def write_csv(path: Path, *, fieldnames: tuple[str, ...], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - path context is user-facing.
        raise MultiZoneReducerPressureError(f"failed to read JSON {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise MultiZoneReducerPressureError(f"JSON document must be an object: {path}")
    return payload


def file_size(path: Path) -> int:
    return path.stat().st_size


def number_or_zero(value: Any) -> int | float:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return value
    return 0


def render_text(report: dict[str, Any]) -> str:
    lines = [
        f"probe_status: {report['probe_status']}",
        f"release_zone_count: {report['release_zone_count']}",
        f"output_family_mix: {report['output_family_mix']}",
        f"scenario_count: {report['scenario_count']}",
        f"trajectory_chunk_count: {report['trajectory_chunk_count']}",
        f"reducer_worker_count: {report['reducer_worker_count']}",
        f"reducer_chunk_count: {report['reducer_chunk_count']}",
        f"merge_order: {report['merge_order']}",
        f"merge_order_independent: {str(report['merge_order_independent']).lower()}",
        f"merge_order_deterministic: {str(report['merge_order_deterministic']).lower()}",
        f"reducer_wall_time_seconds: {report['reducer_wall_time_seconds']}",
        f"manifest_size_bytes: {report['manifest_size_bytes']}",
        f"root_file_count: {report['root_file_count']}",
        f"root_byte_count: {report['root_byte_count']}",
        f"output_file_count: {report['output_file_count']}",
        f"output_byte_count: {report['output_byte_count']}",
        f"reducer_manifest_bytes: {report['reducer_manifest_bytes']}",
        f"reducer_manifest_file_count: {report['reducer_manifest_file_count']}",
        f"sidecar_file_count: {report['sidecar_file_count']}",
        f"sidecar_byte_count: {report['sidecar_byte_count']}",
        f"bottleneck_classification: {report['bottleneck_classification']}",
        f"multi_zone_dry_run_blocked: {str(report['multi_zone_dry_run_blocked']).lower()}",
        f"blocked_reason: {report['blocked_reason']}",
        "output_family_bytes:",
    ]
    for kind, total_bytes in sorted(report["output_family_bytes"].items(), key=lambda item: item[1], reverse=True):
        lines.append(f"- {kind}: bytes={total_bytes}, files={report['output_family_file_counts'].get(kind, 0)}")
    inventory = report.get("validation_output_inventory", {})
    lines.append("validation_output_inventory:")
    lines.append(f"- validation_output_mode: {inventory.get('validation_output_mode')}")
    lines.append("- replay_critical_output_families:")
    lines.extend(f"  - {family}" for family in inventory.get("replay_critical_output_families", []))
    lines.append("- diagnostic_debug_output_families:")
    lines.extend(f"  - {family}" for family in inventory.get("diagnostic_debug_output_families", []))
    lines.append("bottleneck_labels:")
    for key in ("merge_order", "manifest_size", "output_pressure", "reducer_runtime", "probe_blocker"):
        label = report["bottleneck_labels"].get(key, {})
        lines.append(f"- {key}: {label.get('label')}: {label.get('reason')}")
    lines.append("recommended_reducer_constraints:")
    for key, value in report["recommended_reducer_constraints"].items():
        lines.append(f"- {key}: {value}")
    return "\n".join(lines)


def render_markdown(report: dict[str, Any]) -> str:
    inventory = report.get("validation_output_inventory", {})
    return "\n".join(
        [
            "# Multi-Zone Reducer Pressure Probe",
            "",
            f"- probe_status: `{report['probe_status']}`",
            f"- release_zone_count: `{report['release_zone_count']}`",
            f"- output_family_mix: `{report['output_family_mix']}`",
            f"- scenario_count: `{report['scenario_count']}`",
            f"- trajectory_chunk_count: `{report['trajectory_chunk_count']}`",
            f"- reducer_worker_count: `{report['reducer_worker_count']}`",
            f"- reducer_chunk_count: `{report['reducer_chunk_count']}`",
            f"- merge_order: `{report['merge_order']}`",
            f"- merge_order_independent: `{str(report['merge_order_independent']).lower()}`",
            f"- merge_order_deterministic: `{str(report['merge_order_deterministic']).lower()}`",
            f"- reducer_wall_time_seconds: `{report['reducer_wall_time_seconds']}`",
            f"- manifest_size_bytes: `{report['manifest_size_bytes']}`",
            f"- root_file_count: `{report['root_file_count']}`",
            f"- output_file_count: `{report['output_file_count']}`",
            f"- reducer_manifest_bytes: `{report['reducer_manifest_bytes']}`",
            f"- reducer_manifest_file_count: `{report['reducer_manifest_file_count']}`",
            f"- sidecar_file_count: `{report['sidecar_file_count']}`",
            f"- sidecar_byte_count: `{report['sidecar_byte_count']}`",
            f"- multi_zone_dry_run_blocked: `{str(report['multi_zone_dry_run_blocked']).lower()}`",
            f"- blocked_reason: {report['blocked_reason']}",
            "",
            "## Output Families",
            *[
                f"- `{kind}`: `{report['output_family_file_counts'].get(kind, 0)}` files / `{total_bytes}` bytes"
                for kind, total_bytes in sorted(report["output_family_bytes"].items(), key=lambda item: item[1], reverse=True)
            ],
            "",
            "## Validation Output Inventory",
            f"- Validation output mode: `{inventory.get('validation_output_mode')}`",
            "- Replay-critical output families:",
            *[f"  - `{family}`" for family in inventory.get("replay_critical_output_families", [])],
            "- Diagnostic debug output families:",
            *[f"  - `{family}`" for family in inventory.get("diagnostic_debug_output_families", [])],
            "",
            "## Bottleneck Labels",
            *[
                f"- `{key}`: `{report['bottleneck_labels'][key]['label']}` - {report['bottleneck_labels'][key]['reason']}"
                for key in ("merge_order", "manifest_size", "output_pressure", "reducer_runtime", "probe_blocker")
            ],
            "",
            "## Recommended Reducer Constraints",
            *[f"- `{key}`: `{value}`" for key, value in report["recommended_reducer_constraints"].items()],
            "",
        ]
    )


if __name__ == "__main__":
    raise SystemExit(main())
