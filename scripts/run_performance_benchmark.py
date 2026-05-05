#!/usr/bin/env python3
"""Run an opt-in synthetic scale benchmark for execution and I/O profiling.

The benchmark creates synthetic terrain/release-zone fixtures under an ignored
results directory, generates validation cases for a small matrix of output
modes, runs them through the existing CLI, optionally builds hazard layers, and
summarizes run_manifest_v1 performance metadata.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except ImportError as exc:  # pragma: no cover - environment issue.
    raise SystemExit("PyYAML is required; install with `python3 -m pip install PyYAML`") from exc


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_ROOT = ROOT / "validation" / "results" / "performance_synthetic_scale"
DEFAULT_COUNTS = (50, 100, 200)
CONTACT_MODELS = ("translational_v0", "sphere_rotational_v1")
OUTPUT_MODES = (
    ("summary_only", False, False),
    ("trajectories", True, False),
    ("impacts", False, True),
    ("trajectories_impacts", True, True),
)


@dataclass(frozen=True)
class BenchmarkRun:
    run_id: str
    release_count: int
    contact_model: str
    mode_name: str
    write_trajectories: bool
    write_impacts: bool
    case_path: Path
    manifest_path: Path
    diagnostics_path: Path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run opt-in synthetic performance benchmarks and summarize manifest timings."
    )
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--counts", type=int, nargs="+", default=list(DEFAULT_COUNTS))
    parser.add_argument("--terrain-size", type=int, default=80, help="synthetic DEM width/height in cells")
    parser.add_argument("--cell-size", type=float, default=2.0, help="synthetic DEM cell size in metres")
    parser.add_argument("--dt", type=float, default=0.02)
    parser.add_argument("--t-max", type=float, default=5.0)
    parser.add_argument("--seed", type=int, default=97031)
    parser.add_argument("--skip-hazard", action="store_true", help="skip hazard-layer post-processing")
    parser.add_argument(
        "--hazard-plots",
        choices=("both", "with-plots", "no-plots"),
        default="both",
        help="which hazard-layer plotting modes to run when trajectory output is enabled",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="create synthetic inputs and cases but do not execute cargo or hazard-layer commands",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        runs = prepare_benchmark_inputs(
            output_root=args.output_root,
            counts=args.counts,
            terrain_size=args.terrain_size,
            cell_size=args.cell_size,
            dt=args.dt,
            t_max=args.t_max,
            seed=args.seed,
        )
        if args.dry_run:
            print(f"prepared {len(runs)} benchmark cases under {args.output_root}")
            return 0
        rows = run_benchmark_matrix(
            runs,
            output_root=args.output_root,
            skip_hazard=args.skip_hazard,
            hazard_plots=args.hazard_plots,
        )
        write_summary_reports(args.output_root, rows)
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"benchmark error: {exc}", file=sys.stderr)
        return 2
    return 0


def prepare_benchmark_inputs(
    *,
    output_root: Path,
    counts: list[int],
    terrain_size: int,
    cell_size: float,
    dt: float,
    t_max: float,
    seed: int,
) -> list[BenchmarkRun]:
    validate_positive_counts(counts)
    if terrain_size < 16:
        raise ValueError("--terrain-size must be at least 16 cells")
    if cell_size <= 0.0:
        raise ValueError("--cell-size must be positive")
    if dt <= 0.0 or t_max <= 0.0:
        raise ValueError("--dt and --t-max must be positive")

    inputs_dir = output_root / "inputs"
    cases_dir = output_root / "cases"
    results_dir = output_root / "validation"
    inputs_dir.mkdir(parents=True, exist_ok=True)
    cases_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    dem_path = inputs_dir / "synthetic_scale_dem.asc"
    terrain_metadata_path = inputs_dir / "synthetic_scale_terrain_metadata.yaml"
    write_synthetic_dem(dem_path, terrain_size=terrain_size, cell_size=cell_size)
    write_terrain_metadata(
        terrain_metadata_path,
        dem_path=dem_path,
        terrain_size=terrain_size,
        cell_size=cell_size,
    )

    runs: list[BenchmarkRun] = []
    for count in counts:
        release_zone_path = inputs_dir / f"release_zone_{count}.yaml"
        write_release_zone_metadata(
            release_zone_path,
            count=count,
            terrain_size=terrain_size,
            cell_size=cell_size,
            seed=seed + count,
        )
        for contact_model in CONTACT_MODELS:
            for mode_name, write_trajectories, write_impacts in OUTPUT_MODES:
                run_id = run_identifier(count, contact_model, mode_name)
                case_path = cases_dir / f"{run_id}.yaml"
                diagnostics_path = results_dir / f"{run_id}_metrics.json"
                manifest_path = results_dir / f"{run_id}_manifest.json"
                case = build_validation_case(
                    run_id=run_id,
                    release_count=count,
                    terrain_path=dem_path,
                    terrain_metadata_path=terrain_metadata_path,
                    release_zone_path=release_zone_path,
                    results_dir=results_dir,
                    diagnostics_path=diagnostics_path,
                    manifest_path=manifest_path,
                    contact_model=contact_model,
                    write_trajectories=write_trajectories,
                    write_impacts=write_impacts,
                    dt=dt,
                    t_max=t_max,
                    seed=seed,
                )
                case_path.write_text(yaml.safe_dump(case, sort_keys=False), encoding="utf-8")
                runs.append(
                    BenchmarkRun(
                        run_id=run_id,
                        release_count=count,
                        contact_model=contact_model,
                        mode_name=mode_name,
                        write_trajectories=write_trajectories,
                        write_impacts=write_impacts,
                        case_path=case_path,
                        manifest_path=manifest_path,
                        diagnostics_path=diagnostics_path,
                    )
                )
    return runs


def run_benchmark_matrix(
    runs: list[BenchmarkRun],
    *,
    output_root: Path,
    skip_hazard: bool,
    hazard_plots: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for run in runs:
        subprocess.run(
            ["cargo", "run", "--quiet", "--", "validate", "--case", str(run.case_path)],
            cwd=ROOT,
            check=True,
        )
        rows.append(row_from_manifest(run=run, stage="validation", manifest_path=run.manifest_path))
        if not skip_hazard and run.write_trajectories:
            if hazard_plots in ("both", "with-plots"):
                rows.append(run_hazard_stage(run, output_root=output_root, no_plots=False))
            if hazard_plots in ("both", "no-plots"):
                rows.append(run_hazard_stage(run, output_root=output_root, no_plots=True))
    return rows


def run_hazard_stage(run: BenchmarkRun, *, output_root: Path, no_plots: bool) -> dict[str, Any]:
    suffix = "hazard_no_plots" if no_plots else "hazard_with_plots"
    output_dir = output_root / "hazard" / run.run_id / suffix
    command = [
        "python3",
        "scripts/build_hazard_layers.py",
        "--case",
        str(run.case_path),
        "--output-dir",
        str(output_dir),
        "--cell-size",
        "2.0",
    ]
    if no_plots:
        command.append("--no-plots")
    subprocess.run(command, cwd=ROOT, check=True)
    manifest_path = output_dir / f"{run.run_id}_manifest.json"
    return row_from_manifest(run=run, stage=suffix, manifest_path=manifest_path)


def row_from_manifest(run: BenchmarkRun, *, stage: str, manifest_path: Path) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    performance = manifest.get("performance") or {}
    simulation_seconds = float(performance.get("simulation_seconds") or 0.0)
    total_seconds = float(performance.get("total_wall_seconds") or 0.0)
    trajectory_count = int(performance.get("trajectory_count") or 0)
    impact_count = int(performance.get("impact_event_count") or 0)
    throughput_denominator = simulation_seconds if simulation_seconds > 0.0 else total_seconds
    return {
        "run_id": run.run_id,
        "stage": stage,
        "release_count": run.release_count,
        "contact_model": run.contact_model,
        "trajectory_output": run.write_trajectories,
        "impact_output": run.write_impacts,
        "total_wall_seconds": total_seconds,
        "terrain_load_seconds": float(performance.get("terrain_load_seconds") or 0.0),
        "release_generation_seconds": float(performance.get("release_generation_seconds") or 0.0),
        "simulation_seconds": simulation_seconds,
        "output_write_seconds": float(performance.get("output_write_seconds") or 0.0),
        "hazard_layer_seconds": none_to_empty(performance.get("hazard_layer_seconds")),
        "accumulation_seconds": none_to_empty(performance.get("accumulation_seconds")),
        "core_output_write_seconds": none_to_empty(performance.get("core_output_write_seconds")),
        "plot_render_seconds": none_to_empty(performance.get("plot_render_seconds")),
        "plots_enabled": none_to_empty(performance.get("plots_enabled")),
        "trajectory_count": trajectory_count,
        "impact_event_count": impact_count,
        "output_file_count": int(performance.get("output_file_count") or 0),
        "output_bytes": int(performance.get("output_bytes") or 0),
        "trajectories_per_second": safe_rate(trajectory_count, throughput_denominator),
        "impacts_per_second": safe_rate(impact_count, throughput_denominator),
        "manifest_path": str(manifest_path),
    }


def write_summary_reports(output_root: Path, rows: list[dict[str, Any]]) -> None:
    output_root.mkdir(parents=True, exist_ok=True)
    csv_path = output_root / "summary.csv"
    markdown_path = output_root / "summary.md"
    fieldnames = [
        "run_id",
        "stage",
        "release_count",
        "contact_model",
        "trajectory_output",
        "impact_output",
        "total_wall_seconds",
        "terrain_load_seconds",
        "release_generation_seconds",
        "simulation_seconds",
        "output_write_seconds",
        "hazard_layer_seconds",
        "accumulation_seconds",
        "core_output_write_seconds",
        "plot_render_seconds",
        "plots_enabled",
        "trajectory_count",
        "impact_event_count",
        "output_file_count",
        "output_bytes",
        "trajectories_per_second",
        "impacts_per_second",
        "manifest_path",
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    lines = [
        "# Synthetic Scale Performance Benchmark Summary",
        "",
        "Generated by `scripts/run_performance_benchmark.py` from run_manifest_v1 timing metadata.",
        "",
        markdown_table(rows, fieldnames[:-1]),
        "",
        "Generated outputs under this directory are ignored artifacts and should not be committed.",
        "",
    ]
    markdown_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote benchmark summary to {csv_path} and {markdown_path}")


def markdown_table(rows: list[dict[str, Any]], fields: list[str]) -> str:
    if not rows:
        return "_No benchmark rows were collected._"
    header = "| " + " | ".join(fields) + " |"
    separator = "| " + " | ".join("---" for _ in fields) + " |"
    body = ["| " + " | ".join(format_cell(row.get(field)) for field in fields) + " |" for row in rows]
    return "\n".join([header, separator, *body])


def format_cell(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value)


def write_synthetic_dem(path: Path, *, terrain_size: int, cell_size: float) -> None:
    xll = 2_601_000.0
    yll = 1_201_000.0
    values: list[list[float]] = []
    for row in range(terrain_size):
        y = yll + (terrain_size - row - 0.5) * cell_size
        row_values = []
        for col in range(terrain_size):
            x = xll + (col + 0.5) * cell_size
            downslope = 1300.0 - 0.20 * (x - xll)
            cross_slope = 0.015 * (y - yll)
            roughness = 0.35 * math.sin((x - xll) / 14.0) * math.cos((y - yll) / 18.0)
            row_values.append(downslope + cross_slope + roughness)
        values.append(row_values)
    lines = [
        f"ncols {terrain_size}",
        f"nrows {terrain_size}",
        f"xllcorner {xll}",
        f"yllcorner {yll}",
        f"cellsize {cell_size}",
        "NODATA_value -9999",
        *(" ".join(f"{value:.3f}" for value in row) for row in values),
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_terrain_metadata(path: Path, *, dem_path: Path, terrain_size: int, cell_size: float) -> None:
    xll = 2_601_000.0
    yll = 1_201_000.0
    metadata = {
        "schema_version": 1,
        "tile_id": "performance_synthetic_scale_dem",
        "source_dataset": "swisstopo_swissalti3d",
        "source_product": "synthetic_swissalti3d_style_dem",
        "source_url": None,
        "source_filename": dem_path.name,
        "source_file_present": True,
        "download_status": "generated_local_benchmark_fixture",
        "license": "synthetic fixture generated locally; not external geodata",
        "coordinate_reference_system": {
            "epsg": 2056,
            "horizontal_name": "CH1903+ / LV95 style synthetic coordinates",
            "vertical_datum": "LN02",
            "coordinate_unit": "m",
            "height_unit": "m",
        },
        "raster": {
            "format": "ESRI ASCII GRID",
            "resolution_m": cell_size,
            "width_px": terrain_size,
            "height_px": terrain_size,
            "nodata": -9999.0,
        },
        "extent_lv95_m": {
            "xmin": xll,
            "ymin": yll,
            "xmax": xll + terrain_size * cell_size,
            "ymax": yll + terrain_size * cell_size,
        },
        "preprocessing": {
            "status": "generated_for_performance_benchmark",
            "crop_extent_lv95_m": {
                "xmin": xll,
                "ymin": yll,
                "xmax": xll + terrain_size * cell_size,
                "ymax": yll + terrain_size * cell_size,
            },
            "resampling_method": "none",
            "raw_sha256": None,
            "processed_sha256": None,
            "tool": "scripts/run_performance_benchmark.py",
            "processed_utc": None,
        },
        "provenance": {
            "intended_use": "synthetic_scale_performance_benchmark",
            "notes": [
                "Synthetic DEM generated locally to stress execution and output paths.",
                "Not real Swiss terrain and not suitable for scientific validation.",
            ],
        },
    }
    path.write_text(yaml.safe_dump(metadata, sort_keys=False), encoding="utf-8")


def write_release_zone_metadata(
    path: Path,
    *,
    count: int,
    terrain_size: int,
    cell_size: float,
    seed: int,
) -> None:
    xll = 2_601_000.0
    yll = 1_201_000.0
    xmin = xll + 4.0 * cell_size
    xmax = xll + min(24.0, terrain_size * 0.35) * cell_size
    ymin = yll + terrain_size * cell_size * 0.35
    ymax = yll + terrain_size * cell_size * 0.75
    metadata = {
        "schema_version": 1,
        "zone_id": f"performance_synthetic_release_zone_{count}",
        "title": f"Synthetic performance benchmark source area ({count} releases)",
        "source_dataset": "synthetic_performance_release_zone",
        "source_url": None,
        "license": "synthetic fixture generated locally; not external geodata",
        "coordinate_reference_system": {
            "epsg": 2056,
            "horizontal_name": "CH1903+ / LV95 style synthetic coordinates",
            "vertical_datum": "LN02",
            "coordinate_unit": "m",
            "height_unit": "m",
        },
        "geometry": {
            "type": "polygon",
            "coordinates": [
                [xmin, ymin],
                [xmax, ymin],
                [xmax, ymax],
                [xmin, ymax],
            ],
        },
        "sampling": {
            "mode": "deterministic_grid",
            "count": count,
            "seed": seed,
            "initial_velocity_mps": [3.0, 0.15, 0.0],
            "z_offset_m": 0.20,
            "point_id_prefix": f"perf_{count}",
        },
        "provenance": {
            "intended_use": "synthetic_scale_performance_benchmark",
            "notes": [
                "Generated release-zone fixture for opt-in performance measurement.",
                "No scientific validation or operational interpretation is implied.",
            ],
        },
    }
    path.write_text(yaml.safe_dump(metadata, sort_keys=False), encoding="utf-8")


def build_validation_case(
    *,
    run_id: str,
    release_count: int,
    terrain_path: Path,
    terrain_metadata_path: Path,
    release_zone_path: Path,
    results_dir: Path,
    diagnostics_path: Path,
    manifest_path: Path,
    contact_model: str,
    write_trajectories: bool,
    write_impacts: bool,
    dt: float,
    t_max: float,
    seed: int,
) -> dict[str, Any]:
    outputs: dict[str, Any] = {
        "diagnostics_json": str(diagnostics_path),
        "manifest_json": str(manifest_path),
        "ensemble_deposition_csv": str(results_dir / f"{run_id}_deposition.csv"),
    }
    if write_trajectories:
        outputs["ensemble_trajectories_dir"] = str(results_dir / f"{run_id}_trajectories")
    if write_impacts:
        outputs["ensemble_impact_events_dir"] = str(results_dir / f"{run_id}_impacts")

    return {
        "case_id": run_id,
        "title": f"Synthetic scale benchmark {run_id}",
        "level": 4,
        "description": (
            "Opt-in synthetic performance benchmark case generated by "
            "scripts/run_performance_benchmark.py. It stresses execution and I/O only."
        ),
        "terrain": {
            "type": "ascii_dem_clamped",
            "path": str(terrain_path),
            "metadata_path": str(terrain_metadata_path),
        },
        "block": {"mass": 20.0, "radius": 0.25},
        "release": {"position": [2_601_002.0, 1_201_002.0, 1300.5], "velocity": [3.0, 0.15, 0.0]},
        "release_zone": {
            "metadata_path": str(release_zone_path),
            "generated_release_points_csv": str(results_dir / f"{run_id}_release_points.csv"),
        },
        "parameters": {
            "gravity": 9.81,
            "normal_restitution": 0.28,
            "tangential_restitution": 0.80,
            "friction_coefficient": 0.42,
            "contact_model": contact_model,
        },
        "simulation": {
            "dt": dt,
            "t_max": t_max,
            "max_steps": int(math.ceil(t_max / dt)),
            "stop_velocity": 0.05,
        },
        "random": {"seed": seed, "ensemble_size": 1},
        "hazard_layers": {
            "statistics": {
                "kinetic_energy_exceedance_j": [25.0, 100.0],
                "jump_height_exceedance_m": [0.10, 0.50],
                "velocity_exceedance_mps": [1.0, 3.0],
            }
        },
        "expected": {
            "metrics": [
                "release_zone_point_count",
                "release_zone_extent_area_m2",
                "release_zone_mean_runout_m",
                "release_zone_max_runout_m",
            ],
            "values": {"release_zone_point_count": float(release_count)},
            "minimums": {"release_zone_extent_area_m2": 1.0},
            "maximums": {"release_zone_mean_runout_m": 200.0, "release_zone_max_runout_m": 250.0},
        },
        "outputs": outputs,
        "references": {
            "dataset": "synthetic_performance_fixture",
            "notes": [
                "Generated locally and excluded from normal validation.",
                "Used only to measure runtime, file count, and output volume.",
            ],
        },
    }


def run_identifier(release_count: int, contact_model: str, mode_name: str) -> str:
    contact = "rotational" if contact_model == "sphere_rotational_v1" else "baseline"
    return f"synthetic_scale_n{release_count}_{contact}_{mode_name}"


def validate_positive_counts(counts: list[int]) -> None:
    if not counts:
        raise ValueError("at least one release count is required")
    for count in counts:
        if count <= 0:
            raise ValueError("release counts must be positive")


def none_to_empty(value: Any) -> Any:
    return "" if value is None else value


def safe_rate(count: int, seconds: float) -> float:
    return count / seconds if seconds > 0.0 else 0.0


if __name__ == "__main__":
    raise SystemExit(main())
