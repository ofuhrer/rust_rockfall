#!/usr/bin/env python3
"""Build first-pass probabilistic rockfall hazard-map layers from CSV outputs.

This is a post-processing/reporting utility. It consumes existing trajectory,
deposition, and optional impact-event CSV files and does not call or modify the
simulation kernel.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
NODATA = -9999.0
SIGNIFICANT_IMPACT_MIN_NORMAL_SPEED_MPS = 0.05


@dataclass(frozen=True)
class GridSpec:
    xmin: float
    ymin: float
    ncols: int
    nrows: int
    cell_size: float

    @property
    def xmax(self) -> float:
        return self.xmin + self.ncols * self.cell_size

    @property
    def ymax(self) -> float:
        return self.ymin + self.nrows * self.cell_size

    def cell(self, x: float, y: float) -> tuple[int, int] | None:
        col = int(math.floor((x - self.xmin) / self.cell_size))
        row_from_bottom = int(math.floor((y - self.ymin) / self.cell_size))
        if col < 0 or col >= self.ncols or row_from_bottom < 0 or row_from_bottom >= self.nrows:
            return None
        row = self.nrows - 1 - row_from_bottom
        return row, col

    def center(self, row: int, col: int) -> tuple[float, float]:
        x = self.xmin + (col + 0.5) * self.cell_size
        row_from_bottom = self.nrows - 1 - row
        y = self.ymin + (row_from_bottom + 0.5) * self.cell_size
        return x, y


@dataclass
class RasterLayer:
    key: str
    title: str
    units: str
    values: list[list[float]]
    nodata: bool = False
    note: str = ""


@dataclass(frozen=True)
class HazardStatisticConfig:
    kinetic_energy_exceedance_j: tuple[float, ...] = ()
    jump_height_exceedance_m: tuple[float, ...] = ()
    velocity_exceedance_mps: tuple[float, ...] = ()

    @property
    def enabled(self) -> bool:
        return bool(
            self.kinetic_energy_exceedance_j
            or self.jump_height_exceedance_m
            or self.velocity_exceedance_mps
        )

    def as_dict(self) -> dict[str, list[float]]:
        return {
            "kinetic_energy_exceedance_j": list(self.kinetic_energy_exceedance_j),
            "jump_height_exceedance_m": list(self.jump_height_exceedance_m),
            "velocity_exceedance_mps": list(self.velocity_exceedance_mps),
        }


@dataclass(frozen=True)
class InputStats:
    trajectory_count: int = 0
    trajectory_sample_count: int = 0
    deposition_point_count: int = 0
    impact_event_count: int = 0
    significant_impact_count: int = 0


@dataclass
class GridBounds:
    xs: list[float]
    ys: list[float]

    @staticmethod
    def empty() -> "GridBounds":
        return GridBounds(xs=[], ys=[])

    def add_row(self, row: dict[str, float | str]) -> None:
        x = row.get("x_m")
        y = row.get("y_m")
        if isinstance(x, float) and isinstance(y, float) and math.isfinite(x) and math.isfinite(y):
            self.xs.append(x)
            self.ys.append(y)

    def to_grid(self, cell_size: float) -> GridSpec:
        if cell_size <= 0.0:
            raise SystemExit("--cell-size must be positive")
        if not self.xs or not self.ys:
            raise SystemExit("input files contain no x_m/y_m coordinates")

        pad = cell_size
        xmin = math.floor((min(self.xs) - pad) / cell_size) * cell_size
        ymin = math.floor((min(self.ys) - pad) / cell_size) * cell_size
        xmax = math.ceil((max(self.xs) + pad) / cell_size) * cell_size
        ymax = math.ceil((max(self.ys) + pad) / cell_size) * cell_size
        ncols = max(1, int(round((xmax - xmin) / cell_size)))
        nrows = max(1, int(round((ymax - ymin) / cell_size)))
        return GridSpec(xmin=xmin, ymin=ymin, ncols=ncols, nrows=nrows, cell_size=cell_size)


class HazardAccumulator:
    def __init__(
        self,
        grid: GridSpec,
        terrain: "TerrainSampler",
        block_radius_m: float,
        statistics: HazardStatisticConfig,
    ) -> None:
        self.grid = grid
        self.terrain = terrain
        self.block_radius_m = block_radius_m
        self.statistics = statistics
        self.reach = zeros(grid)
        self.max_ke = nodata_grid(grid)
        self.max_jump = nodata_grid(grid)
        self.kinetic_exceedance = {
            threshold: zeros(grid) for threshold in statistics.kinetic_energy_exceedance_j
        }
        self.jump_exceedance = {
            threshold: zeros(grid) for threshold in statistics.jump_height_exceedance_m
        }
        self.velocity_exceedance = {
            threshold: zeros(grid) for threshold in statistics.velocity_exceedance_mps
        }
        self.deposition = zeros(grid)
        self.impact_density = zeros(grid)
        self.deposition_points: list[dict[str, float | str]] = []
        self.trajectory_count = 0
        self.trajectory_sample_count = 0
        self.deposition_point_count = 0
        self.impact_event_count = 0
        self.significant_impact_count = 0
        self.warnings: list[str] = []
        self.terrain_warning_emitted = False

    def accumulate_trajectory(self, path: Path, warnings: list[str]) -> None:
        if not path.exists():
            return
        self.trajectory_count += 1
        occupied: set[tuple[int, int]] = set()
        kinetic_exceeded: dict[float, set[tuple[int, int]]] = {
            threshold: set() for threshold in self.kinetic_exceedance
        }
        jump_exceeded: dict[float, set[tuple[int, int]]] = {
            threshold: set() for threshold in self.jump_exceedance
        }
        velocity_exceeded: dict[float, set[tuple[int, int]]] = {
            threshold: set() for threshold in self.velocity_exceedance
        }
        for sample in iter_numeric_csv(path, f"trajectory:{path}", warnings):
            self.trajectory_sample_count += 1
            cell = sample_cell(self.grid, sample)
            if cell is None:
                continue
            row, col = cell
            occupied.add(cell)
            kinetic = numeric(sample.get("kinetic_j"))
            if kinetic is not None:
                self.max_ke[row][col] = max(self.max_ke[row][col], kinetic) if self.max_ke[row][col] != NODATA else kinetic
                for threshold in kinetic_exceeded:
                    if kinetic >= threshold:
                        kinetic_exceeded[threshold].add(cell)
            speed = numeric(sample.get("speed_mps"))
            if speed is not None:
                for threshold in velocity_exceeded:
                    if speed >= threshold:
                        velocity_exceeded[threshold].add(cell)
            jump = jump_height(sample, self.terrain, self.block_radius_m)
            if jump is None and not self.terrain_warning_emitted:
                self.warnings.append("maximum jump height omitted where terrain could not be evaluated")
                self.terrain_warning_emitted = True
            elif jump is not None:
                self.max_jump[row][col] = max(self.max_jump[row][col], jump) if self.max_jump[row][col] != NODATA else jump
                for threshold in jump_exceeded:
                    if jump >= threshold:
                        jump_exceeded[threshold].add(cell)
        for row, col in occupied:
            self.reach[row][col] += 1.0
        increment_exceedance_grids(self.kinetic_exceedance, kinetic_exceeded)
        increment_exceedance_grids(self.jump_exceedance, jump_exceeded)
        increment_exceedance_grids(self.velocity_exceedance, velocity_exceeded)

    def accumulate_deposition(self, path: Path | None, warnings: list[str]) -> None:
        if path is None or not path.exists():
            return
        for point in iter_numeric_csv(path, f"deposition:{path}", warnings):
            self.deposition_point_count += 1
            self.deposition_points.append(point)
            cell = sample_cell(self.grid, point)
            if cell is not None:
                self.deposition[cell[0]][cell[1]] += 1.0

    def accumulate_impacts(self, paths: list[Path], warnings: list[str]) -> None:
        for path in paths:
            if not path.exists():
                continue
            for event in iter_numeric_csv(path, f"impact_events:{path}", warnings):
                self.impact_event_count += 1
                if (numeric(event.get("incoming_normal_speed_mps")) or 0.0) < SIGNIFICANT_IMPACT_MIN_NORMAL_SPEED_MPS:
                    continue
                self.significant_impact_count += 1
                cell = sample_cell(self.grid, event)
                if cell is not None:
                    self.impact_density[cell[0]][cell[1]] += 1.0

    def stats(self) -> InputStats:
        return InputStats(
            trajectory_count=self.trajectory_count,
            trajectory_sample_count=self.trajectory_sample_count,
            deposition_point_count=self.deposition_point_count,
            impact_event_count=self.impact_event_count,
            significant_impact_count=self.significant_impact_count,
        )

    def layers(self) -> tuple[list[RasterLayer], list[str]]:
        warnings = list(self.warnings)
        layers: list[RasterLayer] = []
        if self.trajectory_count:
            scale_grid(self.reach, 1.0 / self.trajectory_count)
            layers.append(
                RasterLayer(
                    "reach_probability",
                    "Reach probability",
                    "fraction of supplied trajectories",
                    self.reach,
                    note="Cells touched by each supplied trajectory, normalized by the number of trajectory CSVs.",
                )
            )
            layers.append(RasterLayer("max_kinetic_energy", "Maximum kinetic energy", "J", self.max_ke, nodata=True))
            layers.append(
                RasterLayer(
                    "max_jump_height",
                    "Maximum jump height",
                    "m above terrain plus block radius",
                    self.max_jump,
                    nodata=True,
                )
            )
            for threshold, values in self.kinetic_exceedance.items():
                scale_grid(values, 1.0 / self.trajectory_count)
                layers.append(
                    RasterLayer(
                        exceedance_layer_key("kinetic_energy_exceedance", threshold, "j"),
                        f"Kinetic energy exceedance >= {threshold:g} J",
                        "fraction of supplied trajectories",
                        values,
                        note=(
                            "Trajectory-level exceedance probability: a cell is counted once per "
                            f"trajectory if kinetic_j >= {threshold:g} J in that cell."
                        ),
                    )
                )
            for threshold, values in self.jump_exceedance.items():
                scale_grid(values, 1.0 / self.trajectory_count)
                layers.append(
                    RasterLayer(
                        exceedance_layer_key("jump_height_exceedance", threshold, "m"),
                        f"Jump height exceedance >= {threshold:g} m",
                        "fraction of supplied trajectories",
                        values,
                        note=(
                            "Trajectory-level exceedance probability: a cell is counted once per "
                            f"trajectory if jump height >= {threshold:g} m in that cell."
                        ),
                    )
                )
            for threshold, values in self.velocity_exceedance.items():
                scale_grid(values, 1.0 / self.trajectory_count)
                layers.append(
                    RasterLayer(
                        exceedance_layer_key("velocity_exceedance", threshold, "mps"),
                        f"Velocity exceedance >= {threshold:g} m/s",
                        "fraction of supplied trajectories",
                        values,
                        note=(
                            "Trajectory-level exceedance probability: a cell is counted once per "
                            f"trajectory if speed_mps >= {threshold:g} m/s in that cell."
                        ),
                    )
                )
        else:
            warnings.append("no trajectory CSVs supplied; reach, energy, and jump-height layers were not created")

        if self.deposition_point_count:
            scale_grid(self.deposition, 1.0 / self.deposition_point_count)
            layers.append(
                RasterLayer(
                    "deposition_density",
                    "Deposition density",
                    "fraction of deposition points",
                    self.deposition,
                    note="Final-position density from ensemble deposition CSV.",
                )
            )
        else:
            warnings.append("no ensemble deposition CSV supplied; deposition density layer was not created")

        if self.impact_event_count:
            if self.significant_impact_count:
                scale_grid(self.impact_density, 1.0 / self.significant_impact_count)
            layers.append(
                RasterLayer(
                    "significant_impact_density",
                    "Significant impact density",
                    "fraction of significant impact events",
                    self.impact_density,
                    note=f"Significant impacts use incoming_normal_speed_mps >= {SIGNIFICANT_IMPACT_MIN_NORMAL_SPEED_MPS:g} m/s.",
                )
            )
        else:
            warnings.append("no impact-event CSV supplied; significant impact density layer was not created")

        return layers, warnings


def main_with_args(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", type=Path, help="verification or validation YAML case")
    parser.add_argument("--trajectory", action="append", type=Path, default=[], help="trajectory CSV; may be repeated")
    parser.add_argument(
        "--ensemble-trajectories-dir",
        action="append",
        type=Path,
        default=[],
        help="directory containing one trajectory CSV per ensemble member; may be repeated",
    )
    parser.add_argument("--deposition", type=Path, help="ensemble deposition CSV")
    parser.add_argument("--impact-events", type=Path, help="impact event CSV")
    parser.add_argument(
        "--ensemble-impact-events-dir",
        action="append",
        type=Path,
        default=[],
        help="directory containing one impact-event CSV per ensemble member; may be repeated",
    )
    parser.add_argument("--diagnostics", type=Path, help="JSON diagnostics report")
    parser.add_argument("--output-dir", type=Path, required=True, help="directory for hazard layers and report")
    parser.add_argument("--cell-size", type=float, default=5.0, help="raster cell size in metres")
    parser.add_argument("--grid-xmin", type=float, help="explicit output grid minimum x coordinate")
    parser.add_argument("--grid-ymin", type=float, help="explicit output grid minimum y coordinate")
    parser.add_argument("--grid-ncols", type=int, help="explicit output grid column count")
    parser.add_argument("--grid-nrows", type=int, help="explicit output grid row count")
    parser.add_argument("--grid-cell-size", type=float, help="explicit output grid cell size in metres")
    parser.add_argument("--prefix", help="output filename prefix; defaults to case_id or hazard_layers")
    parser.add_argument(
        "--kinetic-energy-exceedance-j",
        action="append",
        type=float,
        default=[],
        help="add trajectory-level kinetic-energy exceedance probability layer for this threshold in J; may be repeated",
    )
    parser.add_argument(
        "--jump-height-exceedance-m",
        action="append",
        type=float,
        default=[],
        help="add trajectory-level jump-height exceedance probability layer for this threshold in m; may be repeated",
    )
    parser.add_argument(
        "--velocity-exceedance-mps",
        action="append",
        type=float,
        default=[],
        help="add trajectory-level velocity exceedance probability layer for this threshold in m/s; may be repeated",
    )
    parser.add_argument("--no-plots", action="store_true", help="skip PNG rendering")
    args = parser.parse_args(argv)

    case = load_yaml(args.case) if args.case else {}
    case_id = str(case.get("case_id") or args.prefix or "hazard_layers")
    prefix = args.prefix or case_id
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    trajectory_paths = resolve_trajectory_paths(case, args.trajectory, args.ensemble_trajectories_dir)
    deposition_path = args.deposition or first_case_output_path(case, "ensemble_deposition_csv")
    impact_event_paths = resolve_impact_event_paths(case, args.impact_events, args.ensemble_impact_events_dir)
    diagnostics_path = args.diagnostics or first_case_output_path(case, "diagnostics_json")

    input_warnings: list[str] = []
    diagnostics = read_json(diagnostics_path) if diagnostics_path and diagnostics_path.exists() else {}

    explicit_grid = parse_explicit_grid(args)
    if explicit_grid:
        grid, grid_source = explicit_grid, "explicit"
    else:
        bounds = discover_bounds(trajectory_paths, deposition_path, impact_event_paths, args.cell_size, input_warnings)
        grid, grid_source = bounds.to_grid(args.cell_size), "auto"
    terrain = TerrainSampler.from_case(case)
    block_radius_m = float((case.get("block") or {}).get("radius", 0.0) or 0.0)
    statistic_config = parse_hazard_statistics(case, args)

    accumulator = HazardAccumulator(grid, terrain, block_radius_m, statistic_config)
    accumulator.accumulate_deposition(deposition_path, input_warnings)
    for trajectory_path in trajectory_paths:
        accumulator.accumulate_trajectory(trajectory_path, input_warnings)
    accumulator.accumulate_impacts(impact_event_paths, input_warnings)
    stats = accumulator.stats()
    if not stats.trajectory_count and not stats.deposition_point_count and not stats.impact_event_count:
        raise SystemExit("no trajectory, deposition, or impact-event inputs found")

    layers, warnings = accumulator.layers()
    warnings = input_warnings + warnings + validate_layers(layers)
    write_layers(output_dir, prefix, grid, layers)
    write_deposition_geojson(output_dir / f"{prefix}_deposition_points.geojson", accumulator.deposition_points)

    metadata_path = output_dir / f"{prefix}_metadata.json"
    metadata = build_metadata(case, diagnostics, grid, grid_source, layers, warnings, stats, statistic_config)
    write_text(metadata_path, json.dumps(metadata, indent=2, sort_keys=True) + "\n")

    plot_paths: dict[str, str] = {}
    if not args.no_plots:
        plot_paths = render_png_layers(output_dir, prefix, grid, layers)
    write_html_report(output_dir / "index.html", case, metadata, layers, plot_paths, prefix)
    manifest = build_hazard_manifest(
        case,
        diagnostics,
        metadata,
        output_dir,
        prefix,
        grid_source,
        layers,
        plot_paths,
        warnings,
        statistic_config,
    )
    write_text(output_dir / f"{prefix}_manifest.json", json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    print(f"wrote hazard layers to {output_dir}")
    return 0


def load_yaml(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    try:
        import yaml  # type: ignore
    except ImportError as exc:
        raise SystemExit("PyYAML is required for --case") from exc
    with path.open() as file:
        return yaml.safe_load(file) or {}


def read_json(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    with path.open() as file:
        return json.load(file)


def case_output_paths(case: dict[str, Any], key: str) -> list[Path]:
    value = (case.get("outputs") or {}).get(key)
    if value is None:
        return []
    values = value if isinstance(value, list) else [value]
    return [ROOT / str(path) for path in values]


def resolve_trajectory_paths(
    case: dict[str, Any],
    explicit_trajectories: list[Path],
    explicit_dirs: list[Path],
) -> list[Path]:
    paths = list(explicit_trajectories)
    dirs = list(explicit_dirs)
    if not paths and not dirs:
        dirs = case_output_paths(case, "ensemble_trajectories_dir")
    for directory in dirs:
        paths.extend(csv_files_in_dir(directory))
    if not paths:
        paths = case_output_paths(case, "trajectory_csv")
    return paths


def resolve_impact_event_paths(
    case: dict[str, Any],
    explicit_impact_events: Path | None,
    explicit_dirs: list[Path],
) -> list[Path]:
    paths = [explicit_impact_events] if explicit_impact_events else []
    dirs = list(explicit_dirs)
    if not paths and not dirs:
        dirs = case_output_paths(case, "ensemble_impact_events_dir")
    for directory in dirs:
        paths.extend(csv_files_in_dir(directory))
    if not paths:
        single = first_case_output_path(case, "impact_events_csv")
        if single:
            paths.append(single)
    return paths


def csv_files_in_dir(directory: Path) -> list[Path]:
    if not directory.exists() or not directory.is_dir():
        return []
    return sorted(path for path in directory.glob("*.csv") if path.is_file())


def first_case_output_path(case: dict[str, Any], key: str) -> Path | None:
    paths = case_output_paths(case, key)
    return paths[0] if paths else None


def parse_explicit_grid(args: argparse.Namespace) -> GridSpec | None:
    values = [args.grid_xmin, args.grid_ymin, args.grid_ncols, args.grid_nrows, args.grid_cell_size]
    provided = [value is not None for value in values]
    if any(provided) and not all(provided):
        raise SystemExit(
            "--grid-xmin, --grid-ymin, --grid-ncols, --grid-nrows, and --grid-cell-size must be provided together"
        )
    if not any(provided):
        return None
    if args.grid_ncols <= 0 or args.grid_nrows <= 0:
        raise SystemExit("--grid-ncols and --grid-nrows must be positive")
    if args.grid_cell_size <= 0.0:
        raise SystemExit("--grid-cell-size must be positive")
    return GridSpec(
        xmin=float(args.grid_xmin),
        ymin=float(args.grid_ymin),
        ncols=int(args.grid_ncols),
        nrows=int(args.grid_nrows),
        cell_size=float(args.grid_cell_size),
    )


def parse_hazard_statistics(case: dict[str, Any], args: argparse.Namespace) -> HazardStatisticConfig:
    configured = case.get("hazard_layers") or {}
    statistics = configured.get("statistics") or configured
    return HazardStatisticConfig(
        kinetic_energy_exceedance_j=validated_thresholds(
            list_from_config(statistics.get("kinetic_energy_exceedance_j"))
            + list(args.kinetic_energy_exceedance_j),
            "kinetic_energy_exceedance_j",
        ),
        jump_height_exceedance_m=validated_thresholds(
            list_from_config(statistics.get("jump_height_exceedance_m"))
            + list(args.jump_height_exceedance_m),
            "jump_height_exceedance_m",
        ),
        velocity_exceedance_mps=validated_thresholds(
            list_from_config(statistics.get("velocity_exceedance_mps"))
            + list(args.velocity_exceedance_mps),
            "velocity_exceedance_mps",
        ),
    )


def list_from_config(value: Any) -> list[float]:
    if value is None:
        return []
    values = value if isinstance(value, list) else [value]
    return [float(item) for item in values]


def validated_thresholds(values: list[float], name: str) -> tuple[float, ...]:
    unique = sorted(set(values))
    for value in unique:
        if not math.isfinite(value) or value < 0.0:
            raise SystemExit(f"{name} thresholds must be finite and nonnegative")
    return tuple(unique)


def discover_bounds(
    trajectory_paths: list[Path],
    deposition_path: Path | None,
    impact_event_paths: list[Path],
    cell_size: float,
    warnings: list[str],
) -> GridBounds:
    if cell_size <= 0.0:
        raise SystemExit("--cell-size must be positive")
    bounds = GridBounds.empty()
    for path in trajectory_paths:
        if path.exists():
            for row in iter_numeric_csv(path, f"trajectory:{path}", warnings, emit_warnings=False):
                bounds.add_row(row)
    if deposition_path and deposition_path.exists():
        for row in iter_numeric_csv(deposition_path, f"deposition:{deposition_path}", warnings, emit_warnings=False):
            bounds.add_row(row)
    for path in impact_event_paths:
        if path.exists():
            for row in iter_numeric_csv(path, f"impact_events:{path}", warnings, emit_warnings=False):
                bounds.add_row(row)
    return bounds


def iter_numeric_csv(
    path: Path | None,
    label: str,
    warnings: list[str],
    *,
    emit_warnings: bool = True,
) -> Any:
    if path is None:
        return
    dropped = 0
    with path.open(newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            parsed: dict[str, float | str] = {}
            row_bad = False
            for key, value in row.items():
                if value is None or value == "":
                    continue
                try:
                    parsed_value: float | str = float(value)
                except ValueError:
                    parsed_value = value
                if isinstance(parsed_value, float) and not math.isfinite(parsed_value):
                    row_bad = True
                    continue
                parsed[key] = parsed_value
            if row_bad and ("x_m" in row or "y_m" in row):
                dropped += 1
                continue
            yield parsed
    if emit_warnings and dropped:
        warnings.append(f"dropped {dropped} non-finite coordinate rows from {label}")


def sample_cell(grid: GridSpec, sample: dict[str, float | str]) -> tuple[int, int] | None:
    x = numeric(sample.get("x_m"))
    y = numeric(sample.get("y_m"))
    if x is None or y is None:
        return None
    return grid.cell(x, y)


def numeric(value: float | str | None) -> float | None:
    return value if isinstance(value, float) and math.isfinite(value) else None


def zeros(grid: GridSpec) -> list[list[float]]:
    return [[0.0 for _ in range(grid.ncols)] for _ in range(grid.nrows)]


def nodata_grid(grid: GridSpec) -> list[list[float]]:
    return [[NODATA for _ in range(grid.ncols)] for _ in range(grid.nrows)]


def scale_grid(values: list[list[float]], factor: float) -> None:
    for row_index, row in enumerate(values):
        for col_index, value in enumerate(row):
            if value != NODATA:
                values[row_index][col_index] = value * factor


def increment_exceedance_grids(
    grids: dict[float, list[list[float]]],
    exceeded: dict[float, set[tuple[int, int]]],
) -> None:
    for threshold, cells in exceeded.items():
        grid = grids[threshold]
        for row, col in cells:
            grid[row][col] += 1.0


def exceedance_layer_key(prefix: str, threshold: float, suffix: str) -> str:
    threshold_text = f"{threshold:g}".replace("-", "neg_").replace(".", "p")
    return f"{prefix}_{threshold_text}{suffix}"


def jump_height(sample: dict[str, float | str], terrain: "TerrainSampler", radius_m: float) -> float | None:
    x = numeric(sample.get("x_m"))
    y = numeric(sample.get("y_m"))
    z = numeric(sample.get("z_m"))
    if x is None or y is None or z is None:
        return None
    ground = terrain.height(x, y)
    if ground is None:
        return None
    return max(0.0, z - ground - radius_m)


class TerrainSampler:
    def height(self, x: float, y: float) -> float | None:
        raise NotImplementedError

    @staticmethod
    def from_case(case: dict[str, Any]) -> "TerrainSampler":
        terrain = case.get("terrain") or {}
        terrain_type = terrain.get("type")
        parameters = terrain.get("parameters") or {}
        if terrain_type in {"plane", "inclined_plane"}:
            return PlaneTerrain(
                z0=float(parameters.get("z0_m", parameters.get("base_z_m", 0.0)) or 0.0),
                slope_x=float(parameters.get("slope_x", 0.0) or 0.0),
                slope_y=float(parameters.get("slope_y", 0.0) or 0.0),
            )
        if terrain_type == "paraboloid":
            return ParaboloidTerrain(
                z0=float(parameters.get("z0_m", 0.0) or 0.0),
                curvature_x=float(parameters.get("curvature_x", parameters.get("a", 0.0)) or 0.0),
                curvature_y=float(parameters.get("curvature_y", parameters.get("b", 0.0)) or 0.0),
                x0=float(parameters.get("x0_m", 0.0) or 0.0),
                y0=float(parameters.get("y0_m", 0.0) or 0.0),
            )
        if terrain_type in {"step", "step_terrain"}:
            return StepTerrain(
                z_low=float(parameters.get("z_low_m", 0.0) or 0.0),
                z_high=float(parameters.get("z_high_m", parameters.get("height_m", 0.0)) or 0.0),
                x_step=float(parameters.get("x_step_m", 0.0) or 0.0),
            )
        if terrain_type in {"ascii_dem", "esri_ascii_grid", "ascii_dem_clamped", "esri_ascii_grid_clamped"}:
            path_text = terrain.get("path")
            if path_text:
                return AsciiDemTerrain.from_path(ROOT / str(path_text), clamped="clamped" in str(terrain_type))
        return UnknownTerrain()


@dataclass(frozen=True)
class PlaneTerrain(TerrainSampler):
    z0: float
    slope_x: float
    slope_y: float

    def height(self, x: float, y: float) -> float:
        return self.z0 + self.slope_x * x + self.slope_y * y


@dataclass(frozen=True)
class ParaboloidTerrain(TerrainSampler):
    z0: float
    curvature_x: float
    curvature_y: float
    x0: float
    y0: float

    def height(self, x: float, y: float) -> float:
        dx = x - self.x0
        dy = y - self.y0
        return self.z0 + self.curvature_x * dx * dx + self.curvature_y * dy * dy


@dataclass(frozen=True)
class StepTerrain(TerrainSampler):
    z_low: float
    z_high: float
    x_step: float

    def height(self, x: float, y: float) -> float:
        _ = y
        return self.z_low if x < self.x_step else self.z_high


class UnknownTerrain(TerrainSampler):
    def height(self, x: float, y: float) -> None:
        _ = (x, y)
        return None


@dataclass(frozen=True)
class AsciiDemTerrain(TerrainSampler):
    ncols: int
    nrows: int
    xll: float
    yll: float
    cell_size: float
    nodata: float
    values: list[list[float]]
    clamped: bool

    @staticmethod
    def from_path(path: Path, clamped: bool) -> "AsciiDemTerrain":
        with path.open() as file:
            header = {}
            for _ in range(6):
                key, value = file.readline().split()[:2]
                header[key.lower()] = float(value)
            values = [[float(value) for value in line.split()] for line in file if line.strip()]
        return AsciiDemTerrain(
            ncols=int(header["ncols"]),
            nrows=int(header["nrows"]),
            xll=header.get("xllcorner", header.get("xllcenter", 0.0)),
            yll=header.get("yllcorner", header.get("yllcenter", 0.0)),
            cell_size=header["cellsize"],
            nodata=header.get("nodata_value", NODATA),
            values=values,
            clamped=clamped,
        )

    def height(self, x: float, y: float) -> float | None:
        col = (x - self.xll) / self.cell_size
        row_from_bottom = (y - self.yll) / self.cell_size
        if self.clamped:
            col = min(max(col, 0.0), self.ncols - 1.0)
            row_from_bottom = min(max(row_from_bottom, 0.0), self.nrows - 1.0)
        elif col < 0.0 or col > self.ncols - 1 or row_from_bottom < 0.0 or row_from_bottom > self.nrows - 1:
            return None
        c0 = int(math.floor(col))
        r0b = int(math.floor(row_from_bottom))
        c1 = min(c0 + 1, self.ncols - 1)
        r1b = min(r0b + 1, self.nrows - 1)
        tx = col - c0
        ty = row_from_bottom - r0b
        r0 = self.nrows - 1 - r0b
        r1 = self.nrows - 1 - r1b
        z00 = self.values[r0][c0]
        z10 = self.values[r0][c1]
        z01 = self.values[r1][c0]
        z11 = self.values[r1][c1]
        if any(value == self.nodata for value in (z00, z10, z01, z11)):
            return None
        return (1 - tx) * (1 - ty) * z00 + tx * (1 - ty) * z10 + (1 - tx) * ty * z01 + tx * ty * z11


def write_layers(output_dir: Path, prefix: str, grid: GridSpec, layers: list[RasterLayer]) -> None:
    for layer in layers:
        write_grid_csv(output_dir / f"{prefix}_{layer.key}.csv", grid, layer)
        write_ascii_grid(output_dir / f"{prefix}_{layer.key}.asc", grid, layer)


def write_grid_csv(path: Path, grid: GridSpec, layer: RasterLayer) -> None:
    with path.open("w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["row", "col", "x_center_m", "y_center_m", layer.key])
        for row in range(grid.nrows):
            for col in range(grid.ncols):
                x, y = grid.center(row, col)
                value = layer.values[row][col]
                writer.writerow([row, col, f"{x:.6f}", f"{y:.6f}", f"{value:.12g}"])


def write_ascii_grid(path: Path, grid: GridSpec, layer: RasterLayer) -> None:
    lines = [
        f"ncols {grid.ncols}",
        f"nrows {grid.nrows}",
        f"xllcorner {grid.xmin:.12g}",
        f"yllcorner {grid.ymin:.12g}",
        f"cellsize {grid.cell_size:.12g}",
        f"NODATA_value {NODATA:.12g}",
    ]
    for row in layer.values:
        lines.append(" ".join(f"{ascii_value(value):.12g}" for value in row))
    write_text(path, "\n".join(lines) + "\n")


def ascii_value(value: float) -> float:
    return value if math.isfinite(value) else NODATA


def write_deposition_geojson(path: Path, depositions: list[dict[str, float | str]]) -> None:
    features = []
    for point in depositions:
        x = numeric(point.get("x_m"))
        y = numeric(point.get("y_m"))
        if x is None or y is None:
            continue
        properties = {key: value for key, value in point.items() if key not in {"x_m", "y_m"}}
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [x, y]},
                "properties": properties,
            }
        )
    write_text(path, json.dumps({"type": "FeatureCollection", "features": features}, indent=2) + "\n")


def build_metadata(
    case: dict[str, Any],
    diagnostics: dict[str, Any],
    grid: GridSpec,
    grid_source: str,
    layers: list[RasterLayer],
    warnings: list[str],
    stats: InputStats,
    statistic_config: HazardStatisticConfig,
) -> dict[str, Any]:
    return {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "case_id": case.get("case_id"),
        "case_title": case.get("title"),
        "model_version": diagnostics.get("model_version"),
        "hazard_only": True,
        "risk_modeling_included": False,
        "grid": {
            "xmin_m": grid.xmin,
            "ymin_m": grid.ymin,
            "ncols": grid.ncols,
            "nrows": grid.nrows,
            "cell_size_m": grid.cell_size,
            "source": grid_source,
        },
        "inputs": {
            "trajectory_count": stats.trajectory_count,
            "trajectory_sample_count": stats.trajectory_sample_count,
            "deposition_point_count": stats.deposition_point_count,
            "impact_event_count": stats.impact_event_count,
            "significant_impact_count": stats.significant_impact_count,
        },
        "hazard_statistics": statistic_config.as_dict(),
        "layers": [
            {
                "key": layer.key,
                "title": layer.title,
                "units": layer.units,
                "note": layer.note,
                "summary": summarize_layer(layer),
            }
            for layer in layers
        ],
        "warnings": warnings,
        "limitations": [
            "Hazard layers are diagnostic research outputs, not operational hazard or risk maps.",
            "Reach, kinetic-energy, and jump-height layers are computed only from supplied trajectory CSVs.",
            "Use outputs.ensemble_trajectories_dir or repeated --trajectory inputs for scientifically meaningful ensemble reach, energy, and jump-height layers.",
            "Exceedance layers are trajectory-level exceedance probabilities, not return-period or risk layers.",
            "Risk mapping requires exposure and vulnerability data and is outside this workflow.",
        ],
    }


def build_hazard_manifest(
    case: dict[str, Any],
    diagnostics: dict[str, Any],
    metadata: dict[str, Any],
    output_dir: Path,
    prefix: str,
    grid_source: str,
    layers: list[RasterLayer],
    plot_paths: dict[str, str],
    warnings: list[str],
    statistic_config: HazardStatisticConfig,
) -> dict[str, Any]:
    outputs: list[dict[str, Any]] = []
    for layer in layers:
        outputs.append(output_manifest_entry(output_dir / f"{prefix}_{layer.key}.csv", "hazard_layer", "csv_grid"))
        outputs.append(output_manifest_entry(output_dir / f"{prefix}_{layer.key}.asc", "hazard_layer", "esri_ascii_grid"))
    outputs.append(output_manifest_entry(output_dir / f"{prefix}_deposition_points.geojson", "deposition_points", "geojson"))
    outputs.append(output_manifest_entry(output_dir / f"{prefix}_metadata.json", "hazard_metadata", "json"))
    outputs.append(output_manifest_entry(output_dir / "index.html", "hazard_report", "html"))
    for layer_key, filename in sorted(plot_paths.items()):
        outputs.append(output_manifest_entry(output_dir / filename, f"{layer_key}_plot", "png"))

    terrain = case.get("terrain") or {}
    random = case.get("random") or {}
    parameters = terrain.get("parameters") or {}
    return {
        "schema_version": "run_manifest_v1",
        "created_unix_s": int(datetime.now(timezone.utc).timestamp()),
        "case_id": metadata.get("case_id"),
        "model_version": metadata.get("model_version"),
        "git_hash": diagnostics.get("git_hash"),
        "config_fingerprint": None,
        "completion_status": "completed",
        "seed_policy": {
            "global_seed": random.get("seed"),
            "ensemble_size": random.get("ensemble_size", 1),
            "derivation": "hazard post-processing consumes existing simulation outputs; seed derivation is inherited from the source run",
        },
        "terrain": {
            "terrain_type": terrain.get("type"),
            "path": terrain.get("path"),
            "crs": None,
            "vertical_datum": None,
            "resolution_m": parameters.get("cell_size_m") or parameters.get("cellsize"),
        },
        "outputs": outputs,
        "warnings": warnings,
        "grid": dict(metadata.get("grid", {}), source=grid_source),
        "inputs": metadata.get("inputs", {}),
        "hazard_statistics": {
            "configured": statistic_config.as_dict(),
            "generated_layer_names": [layer.key for layer in layers if "exceedance" in layer.key],
        },
        "layers": [
            {
                "key": layer.key,
                "source": layer_source(layer.key),
                "units": layer.units,
                "summary": summarize_layer(layer),
            }
            for layer in layers
        ],
    }


def output_manifest_entry(path: Path, kind: str, format_name: str) -> dict[str, Any]:
    return {
        "kind": kind,
        "format": format_name,
        "path": str(path),
        "file_count": 1,
        "total_bytes": path.stat().st_size if path.exists() else 0,
        "row_count": None,
        "skipped_empty_files": None,
    }


def layer_source(layer_key: str) -> str:
    if layer_key in {"reach_probability", "max_kinetic_energy", "max_jump_height"} or "exceedance" in layer_key:
        return "trajectory_csv"
    if layer_key == "deposition_density":
        return "ensemble_deposition_csv"
    if layer_key == "significant_impact_density":
        return "impact_event_csv"
    return "unknown"


def summarize_layer(layer: RasterLayer) -> dict[str, float | int | None]:
    values = [
        value
        for row in layer.values
        for value in row
        if math.isfinite(value) and (not layer.nodata or value != NODATA)
    ]
    if not values:
        return {
            "valid_cell_count": 0,
            "minimum": None,
            "maximum": None,
            "sum": 0.0,
            "nonzero_cell_count": 0,
        }
    return {
        "valid_cell_count": len(values),
        "minimum": min(values),
        "maximum": max(values),
        "sum": math.fsum(values),
        "nonzero_cell_count": sum(1 for value in values if value != 0.0),
    }


def validate_layers(layers: list[RasterLayer]) -> list[str]:
    warnings: list[str] = []
    for layer in layers:
        summary = summarize_layer(layer)
        if summary["valid_cell_count"] == 0:
            warnings.append(f"{layer.key} has no valid cells")
        if layer.key in {"reach_probability", "deposition_density", "significant_impact_density"} or "exceedance" in layer.key:
            maximum = summary["maximum"]
            minimum = summary["minimum"]
            if isinstance(maximum, float) and maximum > 1.0 + 1e-12:
                warnings.append(f"{layer.key} has values greater than 1.0")
            if isinstance(minimum, float) and minimum < -1e-12:
                warnings.append(f"{layer.key} has negative values")
    return warnings


def render_png_layers(output_dir: Path, prefix: str, grid: GridSpec, layers: list[RasterLayer]) -> dict[str, str]:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt  # type: ignore
    except ImportError:
        return {}

    plot_paths: dict[str, str] = {}
    extent = [grid.xmin, grid.xmax, grid.ymin, grid.ymax]
    for layer in layers:
        fig, ax = plt.subplots(figsize=(8.0, 6.5), constrained_layout=True)
        data = [[math.nan if value == NODATA else value for value in row] for row in layer.values]
        image = ax.imshow(data, extent=extent, origin="upper", interpolation="nearest")
        ax.set_title(layer.title)
        ax.set_xlabel("x [m]")
        ax.set_ylabel("y [m]")
        colorbar = fig.colorbar(image, ax=ax)
        colorbar.set_label(layer.units)
        path = output_dir / f"{prefix}_{layer.key}.png"
        fig.savefig(path, dpi=150)
        plt.close(fig)
        plot_paths[layer.key] = path.name
    return plot_paths


def write_html_report(
    path: Path,
    case: dict[str, Any],
    metadata: dict[str, Any],
    layers: list[RasterLayer],
    plot_paths: dict[str, str],
    prefix: str,
) -> None:
    title = str(case.get("title") or metadata.get("case_id") or "Hazard Layers")
    rows = []
    for layer in layers:
        summary = next(
            (entry.get("summary", {}) for entry in metadata.get("layers", []) if entry.get("key") == layer.key),
            {},
        )
        rows.append(
            "<tr>"
            f"<td>{html.escape(layer.title)}</td>"
            f"<td>{html.escape(layer.units)}</td>"
            f"<td><a href=\"{prefix}_{layer.key}.csv\">CSV grid</a> | "
            f"<a href=\"{prefix}_{layer.key}.asc\">ASCII grid</a></td>"
            f"<td>{html.escape(layer.note)}</td>"
            f"<td>{html.escape(format_summary(summary))}</td>"
            "</tr>"
        )
    plots = []
    for layer in layers:
        plot = plot_paths.get(layer.key)
        if plot:
            plots.append(
                f"<figure><img src=\"{html.escape(plot)}\" alt=\"{html.escape(layer.title)}\">"
                f"<figcaption>{html.escape(layer.title)} ({html.escape(layer.units)}). {html.escape(layer.note)}</figcaption></figure>"
            )
    warnings = "".join(f"<li>{html.escape(warning)}</li>" for warning in metadata.get("warnings", []))
    limitations = "".join(f"<li>{html.escape(item)}</li>" for item in metadata.get("limitations", []))
    content = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{html.escape(title)} Hazard Layers</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 2rem; line-height: 1.45; color: #172033; }}
    h1, h2 {{ line-height: 1.15; }}
    .badge {{ display: inline-block; padding: 0.15rem 0.45rem; border-radius: 0.35rem; background: #e8f0fe; color: #174ea6; font-size: 0.86rem; }}
    table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
    th, td {{ border: 1px solid #d8dee9; padding: 0.5rem; text-align: left; vertical-align: top; }}
    th {{ background: #f5f7fb; }}
    img {{ max-width: 920px; width: 100%; border: 1px solid #d8dee9; }}
    figure {{ margin: 1.5rem 0; }}
    figcaption {{ color: #4b5563; font-size: 0.92rem; margin-top: 0.35rem; }}
    code {{ background: #f5f7fb; padding: 0.1rem 0.25rem; }}
  </style>
</head>
<body>
  <h1>{html.escape(title)} Hazard Layers</h1>
  <p><span class="badge">research hazard layer</span> <span class="badge">not operational risk</span></p>
  <p>This report converts existing rockfall simulation outputs into first-pass spatial hazard layers. It does not add physics, does not include exposure or vulnerability, and must not be interpreted as an operational Swiss hazard or risk map.</p>
  <h2>How to Read Hazard Layers</h2>
  <p>Probability and density layers are normalized diagnostic rasters. A value near 1 means all supplied samples for that layer occupied the cell; a value near 0 means few or none did. Maximum-energy and maximum-jump-height layers record the largest sampled value in each cell, not an expected value or design value. Exceedance layers count each trajectory at most once per cell and threshold.</p>
  <ul>
    <li><strong>Reach probability</strong>: cells touched by supplied trajectory CSVs. With <code>outputs.ensemble_trajectories_dir</code> it represents the full written ensemble; with one representative trajectory it is only a 0/1 path mask.</li>
    <li><strong>Deposition density</strong>: final-position density from ensemble deposition points.</li>
    <li><strong>Maximum kinetic energy</strong>: largest kinetic energy sampled in each cell from supplied trajectories.</li>
    <li><strong>Maximum jump height</strong>: largest sampled height above terrain plus block radius where terrain metadata can be evaluated.</li>
    <li><strong>Exceedance probability</strong>: fraction of supplied trajectories that exceeded a configured kinetic-energy, jump-height, or velocity threshold in each cell.</li>
    <li><strong>Significant impact density</strong>: normalized locations of impact events above the configured normal-speed threshold.</li>
  </ul>
  <h2>Inputs</h2>
  <ul>
    <li>Case: <code>{html.escape(str(metadata.get("case_id") or "unspecified"))}</code></li>
    <li>Model version: <code>{html.escape(str(metadata.get("model_version") or "unknown"))}</code></li>
    <li>Trajectory CSV count: {metadata["inputs"]["trajectory_count"]}</li>
    <li>Trajectory samples: {metadata["inputs"]["trajectory_sample_count"]}</li>
    <li>Deposition points: {metadata["inputs"]["deposition_point_count"]}</li>
    <li>Impact events: {metadata["inputs"]["impact_event_count"]}</li>
    <li>Cell size: {metadata["grid"]["cell_size_m"]} m</li>
  </ul>
  <h2>Layer Exports</h2>
  <table>
    <thead><tr><th>Layer</th><th>Units</th><th>Files</th><th>Interpretation</th><th>Summary</th></tr></thead>
    <tbody>{''.join(rows)}</tbody>
  </table>
  <p>Deposition points are also exported as <a href="{prefix}_deposition_points.geojson">GeoJSON</a>. Run metadata are in <a href="{prefix}_metadata.json">JSON</a>.</p>
  <h2>Plots</h2>
  {''.join(plots) if plots else '<p>PNG plots were not generated for this run.</p>'}
  <h2>Warnings</h2>
  <ul>{warnings or '<li>No warnings.</li>'}</ul>
  <h2>Known Limitations</h2>
  <ul>{limitations}</ul>
</body>
</html>
"""
    write_text(path, content)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def format_summary(summary: dict[str, Any]) -> str:
    valid = summary.get("valid_cell_count", 0)
    nonzero = summary.get("nonzero_cell_count", 0)
    minimum = summary.get("minimum")
    maximum = summary.get("maximum")
    total = summary.get("sum")
    if valid == 0:
        return "no valid cells"
    return f"valid={valid}, nonzero={nonzero}, min={format_number(minimum)}, max={format_number(maximum)}, sum={format_number(total)}"


def format_number(value: Any) -> str:
    if isinstance(value, (int, float)):
        return f"{value:.6g}"
    return "n/a"


if __name__ == "__main__":
    raise SystemExit(main_with_args())
