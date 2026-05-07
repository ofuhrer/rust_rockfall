#!/usr/bin/env python3
"""Build first-pass probabilistic rockfall hazard-map layers from CSV outputs.

This is a post-processing/reporting utility. It consumes existing trajectory,
deposition, and optional impact-event CSV files and does not call or modify the
simulation kernel.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import math
import struct
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


ROOT = Path(__file__).resolve().parents[1]
NODATA = -9999.0
SIGNIFICANT_IMPACT_MIN_NORMAL_SPEED_MPS = 0.05
INPUT_ARTIFACT_COLLECTION_MEMBER_LIMIT = 32


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
class HazardProbabilityFilters:
    source_zone_ids: tuple[str, ...] = ()
    scenario_ids: tuple[str, ...] = ()
    block_mass_kg_min: float | None = None
    block_mass_kg_max: float | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "source_zone_ids": list(self.source_zone_ids),
            "scenario_ids": list(self.scenario_ids),
            "block_mass_kg_min": self.block_mass_kg_min,
            "block_mass_kg_max": self.block_mass_kg_max,
        }


@dataclass(frozen=True)
class HazardProbabilityConfig:
    probability_model: str
    metadata_path: Path
    weight_column: str
    normalization_convention: str
    filters: HazardProbabilityFilters

    @property
    def enabled(self) -> bool:
        return True

    def as_dict(self) -> dict[str, Any]:
        return {
            "probability_model": self.probability_model,
            "metadata_path": str(self.metadata_path),
            "weight_column": self.weight_column,
            "normalization_convention": self.normalization_convention,
            "filters": self.filters.as_dict(),
        }


@dataclass(frozen=True)
class TrajectoryWeight:
    trajectory_id: str
    weight: float
    source_zone_id: str | None
    scenario_id: str | None
    block_mass_kg: float | None


@dataclass(frozen=True)
class HazardProbabilityState:
    config: HazardProbabilityConfig
    weights: dict[str, TrajectoryWeight]
    total_input_weight: float
    total_filtered_weight: float

    def weight_for_trajectory(self, trajectory_id: str) -> float:
        try:
            return self.weights[trajectory_id].weight
        except KeyError as exc:
            raise SystemExit(
                f"trajectory id {trajectory_id!r} is missing from {self.config.metadata_path}"
            ) from exc

    def as_manifest(self, generated_layer_names: list[str]) -> dict[str, Any]:
        return {
            **self.config.as_dict(),
            "total_input_weight": self.total_input_weight,
            "total_filtered_weight": self.total_filtered_weight,
            "generated_weighted_layer_names": generated_layer_names,
        }


@dataclass(frozen=True)
class ScenarioMetadataRow:
    scenario_id: str
    source_zone_id: str
    sampling_weight: float
    release_probability: float | None
    scenario_probability: float | None
    annual_frequency_per_year: float | None
    time_horizon_years: float | None


@dataclass(frozen=True)
class HazardMapPackageConfig:
    map_product_id: str
    probability_mode: str
    normalization_scope: str
    source_zone_metadata_path: Path
    scenario_table_path: Path | None = None
    map_package_manifest_json: Path | None = None
    validation_context: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()


@dataclass(frozen=True)
class HazardMapPackageState:
    config: HazardMapPackageConfig
    source_zone_id: str
    scenario_rows: tuple[ScenarioMetadataRow, ...]
    annual_frequency_fields_present: bool = False

    @property
    def scenario_ids(self) -> list[str]:
        return [row.scenario_id for row in self.scenario_rows]


@dataclass(frozen=True)
class RasterExportConfig:
    geotiff: bool = False
    cog: bool = False
    compression: str = "none"

    @property
    def enabled(self) -> bool:
        return self.geotiff

    def as_metadata(self) -> dict[str, Any]:
        formats = ["csv_grid", "esri_ascii_grid"]
        if self.geotiff:
            formats.append("geotiff")
        return {
            "geotiff": self.geotiff,
            "cog": self.cog,
            "compression": self.compression if self.geotiff else None,
            "formats": formats,
        }


@dataclass(frozen=True)
class InputStats:
    trajectory_count: int = 0
    trajectory_sample_count: int = 0
    deposition_point_count: int = 0
    impact_event_count: int = 0
    significant_impact_count: int = 0


@dataclass
class BoundsDiscoveryStats:
    trajectory_files_scanned: int = 0
    deposition_files_scanned: int = 0
    impact_csv_files_scanned: int = 0
    impact_parquet_tables_scanned: int = 0
    trajectory_rows_scanned: int = 0
    deposition_rows_scanned: int = 0
    impact_csv_rows_scanned: int = 0
    impact_parquet_rows_scanned: int = 0

    @property
    def total_rows_scanned(self) -> int:
        return (
            self.trajectory_rows_scanned
            + self.deposition_rows_scanned
            + self.impact_csv_rows_scanned
            + self.impact_parquet_rows_scanned
        )


@dataclass(frozen=True)
class TrajectorySample:
    x_m: float | None
    y_m: float | None
    z_m: float | None
    kinetic_j: float | None
    speed_mps: float | None


@dataclass(frozen=True)
class TrajectorySampleBatch:
    path: Path
    trajectory_id: str | None
    samples: tuple[TrajectorySample, ...]


@dataclass(frozen=True)
class DepositionPoint:
    x_m: float | None
    y_m: float | None
    properties: dict[str, float | str]


@dataclass(frozen=True)
class DepositionPointBatch:
    points: tuple[DepositionPoint, ...]


@dataclass(frozen=True)
class ImpactEventBatch:
    source_path: Path
    event_count: int
    significant_event_count: int
    significant_points: tuple[tuple[float, float], ...]


@dataclass(frozen=True)
class HazardAccumulationTimings:
    bounds_discovery_seconds: float = 0.0
    deposition_accumulation_seconds: float = 0.0
    trajectory_accumulation_seconds: float = 0.0
    impact_accumulation_seconds: float = 0.0
    normalization_seconds: float = 0.0


@dataclass
class GridBounds:
    xs: list[float]
    ys: list[float]

    @staticmethod
    def empty() -> "GridBounds":
        return GridBounds(xs=[], ys=[])

    def add_row(self, row: dict[str, float | str | bool]) -> None:
        x = row.get("x_m")
        y = row.get("y_m")
        if isinstance(x, float) and isinstance(y, float) and math.isfinite(x) and math.isfinite(y):
            self.add_xy(x, y)

    def add_xy(self, x: float, y: float) -> None:
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
        probability: HazardProbabilityState | None = None,
    ) -> None:
        self.grid = grid
        self.terrain = terrain
        self.block_radius_m = block_radius_m
        self.statistics = statistics
        self.probability = probability
        self.reach = zeros(grid)
        self.weighted_reach = zeros(grid) if probability else None
        self.max_ke = nodata_grid(grid)
        self.max_jump = nodata_grid(grid)
        self.kinetic_exceedance = {
            threshold: zeros(grid) for threshold in statistics.kinetic_energy_exceedance_j
        }
        self.weighted_kinetic_exceedance = (
            {threshold: zeros(grid) for threshold in statistics.kinetic_energy_exceedance_j}
            if probability
            else {}
        )
        self.jump_exceedance = {
            threshold: zeros(grid) for threshold in statistics.jump_height_exceedance_m
        }
        self.weighted_jump_exceedance = (
            {threshold: zeros(grid) for threshold in statistics.jump_height_exceedance_m}
            if probability
            else {}
        )
        self.velocity_exceedance = {
            threshold: zeros(grid) for threshold in statistics.velocity_exceedance_mps
        }
        self.weighted_velocity_exceedance = (
            {threshold: zeros(grid) for threshold in statistics.velocity_exceedance_mps}
            if probability
            else {}
        )
        self.deposition = zeros(grid)
        self.impact_density = zeros(grid)
        self.deposition_points: list[DepositionPoint] = []
        self.trajectory_count = 0
        self.trajectory_sample_count = 0
        self.deposition_point_count = 0
        self.impact_event_count = 0
        self.significant_impact_count = 0
        self.warnings: list[str] = []
        self.terrain_warning_emitted = False

    def accumulate_trajectory(self, batch: TrajectorySampleBatch) -> None:
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
        for sample in batch.samples:
            self.trajectory_sample_count += 1
            cell = sample_cell_from_xy(self.grid, sample.x_m, sample.y_m)
            if cell is None:
                continue
            row, col = cell
            self.accumulate_trajectory_occupancy(cell, occupied)
            self.accumulate_trajectory_maxima_and_exceedances(
                sample,
                row,
                col,
                cell,
                kinetic_exceeded,
                jump_exceeded,
                velocity_exceeded,
            )
        self.commit_trajectory_sets(occupied, kinetic_exceeded, jump_exceeded, velocity_exceeded)
        if self.probability is not None:
            if batch.trajectory_id is None:
                raise SystemExit(f"trajectory file {batch.path} contains no samples and cannot be weighted")
            self.commit_weighted_trajectory_sets(
                batch.trajectory_id,
                occupied,
                kinetic_exceeded,
                jump_exceeded,
                velocity_exceeded,
            )

    def accumulate_trajectory_occupancy(
        self,
        cell: tuple[int, int],
        occupied: set[tuple[int, int]],
    ) -> None:
        occupied.add(cell)

    def accumulate_trajectory_maxima_and_exceedances(
        self,
        sample: TrajectorySample,
        row: int,
        col: int,
        cell: tuple[int, int],
        kinetic_exceeded: dict[float, set[tuple[int, int]]],
        jump_exceeded: dict[float, set[tuple[int, int]]],
        velocity_exceeded: dict[float, set[tuple[int, int]]],
    ) -> None:
        kinetic = sample.kinetic_j
        if kinetic is not None:
            self.max_ke[row][col] = max(self.max_ke[row][col], kinetic) if self.max_ke[row][col] != NODATA else kinetic
            for threshold in kinetic_exceeded:
                if kinetic >= threshold:
                    kinetic_exceeded[threshold].add(cell)
        speed = sample.speed_mps
        if speed is not None:
            for threshold in velocity_exceeded:
                if speed >= threshold:
                    velocity_exceeded[threshold].add(cell)
        jump = self.sample_jump_height(sample)
        if jump is None and not self.terrain_warning_emitted:
            self.warnings.append("maximum jump height omitted where terrain could not be evaluated")
            self.terrain_warning_emitted = True
        elif jump is not None:
            self.max_jump[row][col] = max(self.max_jump[row][col], jump) if self.max_jump[row][col] != NODATA else jump
            for threshold in jump_exceeded:
                if jump >= threshold:
                    jump_exceeded[threshold].add(cell)

    def sample_jump_height(self, sample: TrajectorySample) -> float | None:
        x = sample.x_m
        y = sample.y_m
        z = sample.z_m
        if x is None or y is None or z is None:
            return None
        ground = self.terrain.height(x, y)
        if ground is None:
            return None
        return max(0.0, z - ground - self.block_radius_m)

    def commit_trajectory_sets(
        self,
        occupied: set[tuple[int, int]],
        kinetic_exceeded: dict[float, set[tuple[int, int]]],
        jump_exceeded: dict[float, set[tuple[int, int]]],
        velocity_exceeded: dict[float, set[tuple[int, int]]],
    ) -> None:
        for row, col in occupied:
            self.reach[row][col] += 1.0
        increment_exceedance_grids(self.kinetic_exceedance, kinetic_exceeded)
        increment_exceedance_grids(self.jump_exceedance, jump_exceeded)
        increment_exceedance_grids(self.velocity_exceedance, velocity_exceeded)

    def commit_weighted_trajectory_sets(
        self,
        trajectory_id: str,
        occupied: set[tuple[int, int]],
        kinetic_exceeded: dict[float, set[tuple[int, int]]],
        jump_exceeded: dict[float, set[tuple[int, int]]],
        velocity_exceeded: dict[float, set[tuple[int, int]]],
    ) -> None:
        weight = self.probability.weight_for_trajectory(trajectory_id) if self.probability else 0.0
        if self.weighted_reach is not None:
            for row, col in occupied:
                self.weighted_reach[row][col] += weight
        increment_weighted_exceedance_grids(
            self.weighted_kinetic_exceedance,
            kinetic_exceeded,
            weight,
        )
        increment_weighted_exceedance_grids(
            self.weighted_jump_exceedance,
            jump_exceeded,
            weight,
        )
        increment_weighted_exceedance_grids(
            self.weighted_velocity_exceedance,
            velocity_exceeded,
            weight,
        )

    def accumulate_deposition(self, batch: DepositionPointBatch) -> None:
        for point in batch.points:
            self.deposition_point_count += 1
            self.deposition_points.append(point)
            cell = sample_cell_from_xy(self.grid, point.x_m, point.y_m)
            if cell is not None:
                self.deposition[cell[0]][cell[1]] += 1.0

    def accumulate_impacts(self, batch: ImpactEventBatch) -> None:
        self.impact_event_count += batch.event_count
        self.significant_impact_count += batch.significant_event_count
        for x, y in batch.significant_points:
            cell = self.grid.cell(x, y)
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
            if self.probability is not None:
                denominator = self.probability.total_filtered_weight
                if denominator <= 0.0:
                    raise SystemExit("filtered total sampling weight must be positive")
                if self.weighted_reach is not None:
                    scale_grid(self.weighted_reach, 1.0 / denominator)
                    layers.append(
                        RasterLayer(
                            "weighted_reach_probability",
                            "Weighted reach probability",
                            "sampling-weighted fraction of filtered trajectories",
                            self.weighted_reach,
                            note=(
                                "Sampling-weighted conditional reach probability using "
                                "trajectory_metadata_table_v1 and normalization conditioned on filters."
                            ),
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
            for threshold, values in self.weighted_kinetic_exceedance.items():
                scale_grid(values, 1.0 / self.probability.total_filtered_weight)
                layers.append(
                    RasterLayer(
                        exceedance_layer_key("weighted_kinetic_energy_exceedance", threshold, "j"),
                        f"Weighted kinetic energy exceedance >= {threshold:g} J",
                        "sampling-weighted fraction of filtered trajectories",
                        values,
                        note=(
                            "Sampling-weighted trajectory-level exceedance probability: a cell is counted once per "
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
            for threshold, values in self.weighted_jump_exceedance.items():
                scale_grid(values, 1.0 / self.probability.total_filtered_weight)
                layers.append(
                    RasterLayer(
                        exceedance_layer_key("weighted_jump_height_exceedance", threshold, "m"),
                        f"Weighted jump height exceedance >= {threshold:g} m",
                        "sampling-weighted fraction of filtered trajectories",
                        values,
                        note=(
                            "Sampling-weighted trajectory-level exceedance probability: a cell is counted once per "
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
            for threshold, values in self.weighted_velocity_exceedance.items():
                scale_grid(values, 1.0 / self.probability.total_filtered_weight)
                layers.append(
                    RasterLayer(
                        exceedance_layer_key("weighted_velocity_exceedance", threshold, "mps"),
                        f"Weighted velocity exceedance >= {threshold:g} m/s",
                        "sampling-weighted fraction of filtered trajectories",
                        values,
                        note=(
                            "Sampling-weighted trajectory-level exceedance probability: a cell is counted once per "
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
            warnings.append("no impact-event input supplied; significant impact density layer was not created")

        return layers, warnings


def main_with_args(argv: list[str] | None = None) -> int:
    total_started = time.perf_counter()
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
    parser.add_argument(
        "--impact-events-parquet",
        action="append",
        type=Path,
        default=[],
        help="batched impact-events Parquet table; may be repeated",
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
    parser.add_argument("--map-product-id", help="optional Phase 1 map product id for hazard-map package metadata")
    parser.add_argument(
        "--probability-mode",
        choices=[
            "unweighted_diagnostic",
            "sampling_weighted_conditional",
            "physical_probability",
            "annual_frequency",
        ],
        help="optional external probability-mode label for map-package metadata",
    )
    parser.add_argument(
        "--normalization-scope",
        choices=[
            "conditioned_on_filter",
            "conditioned_on_scenario",
            "absolute_probability_mass",
            "annual_frequency_sum",
        ],
        help="optional denominator convention for map-package metadata",
    )
    parser.add_argument(
        "--source-zone-metadata-path",
        type=Path,
        help="source_zone_metadata_v1 YAML sidecar for Phase 1 map-package validation",
    )
    parser.add_argument(
        "--scenario-table-path",
        type=Path,
        help="scenario_table_v1 CSV sidecar for Phase 1 map-package validation",
    )
    parser.add_argument(
        "--map-package-manifest-json",
        type=Path,
        help="optional output path for map_package_manifest_v1; defaults next to the hazard manifest",
    )
    parser.add_argument(
        "--export-geotiff",
        action="store_true",
        help="opt-in GIS GeoTIFF export for each hazard raster layer",
    )
    parser.add_argument(
        "--export-cog",
        action="store_true",
        help="reserved for future Cloud-Optimized GeoTIFF export; currently fails rather than writing non-COG TIFFs",
    )
    parser.add_argument("--no-plots", action="store_true", help="write core hazard outputs only; skip PNG and HTML report rendering")
    args = parser.parse_args(argv)

    case = load_yaml(args.case) if args.case else {}
    if args.case:
        case["_path"] = str(args.case)
    case_id = str(case.get("case_id") or args.prefix or "hazard_layers")
    prefix = args.prefix or case_id
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    trajectory_paths = resolve_trajectory_paths(case, args.trajectory, args.ensemble_trajectories_dir)
    deposition_path = args.deposition or first_case_output_path(case, "ensemble_deposition_csv")
    explicit_csv_impact_inputs = bool(args.impact_events or args.ensemble_impact_events_dir)
    explicit_parquet_impact_inputs = bool(args.impact_events_parquet)
    impact_event_parquet_paths = resolve_impact_event_parquet_paths(
        case,
        args.impact_events_parquet,
        suppress_case_defaults=explicit_csv_impact_inputs,
    )
    impact_event_paths = resolve_impact_event_paths(
        case,
        args.impact_events,
        args.ensemble_impact_events_dir,
        suppress_case_defaults=explicit_parquet_impact_inputs
        or (bool(impact_event_parquet_paths) and not explicit_csv_impact_inputs),
    )
    diagnostics_path = args.diagnostics or first_case_output_path(case, "diagnostics_json")

    input_warnings: list[str] = []
    diagnostics = read_json(diagnostics_path) if diagnostics_path and diagnostics_path.exists() else {}
    if diagnostics_path:
        diagnostics["_path"] = str(diagnostics_path)
    probability_config = parse_hazard_probability(case)
    map_package_config = parse_hazard_map_package(case, args)
    raster_export_config = parse_raster_export_config(case, args)

    explicit_grid = parse_explicit_grid(args)
    if explicit_grid:
        grid, grid_source = explicit_grid, "explicit"
        bounds_discovery_seconds = 0.0
        bounds_stats = BoundsDiscoveryStats()
    else:
        bounds_started = time.perf_counter()
        bounds, bounds_stats = discover_bounds(
            trajectory_paths,
            deposition_path,
            impact_event_paths,
            impact_event_parquet_paths,
            args.cell_size,
            input_warnings,
        )
        bounds_discovery_seconds = time.perf_counter() - bounds_started
        grid, grid_source = bounds.to_grid(args.cell_size), "auto"
    terrain = TerrainSampler.from_case(case)
    block_radius_m = float((case.get("block") or {}).get("radius", 0.0) or 0.0)
    statistic_config = parse_hazard_statistics(case, args)
    probability_state = load_hazard_probability_state(
        probability_config,
        trajectory_paths,
        deposition_path,
        impact_event_paths,
        impact_event_parquet_paths,
    )
    map_package_state = load_hazard_map_package_state(map_package_config, probability_state)

    accumulation_started = time.perf_counter()
    accumulator = HazardAccumulator(grid, terrain, block_radius_m, statistic_config, probability_state)
    deposition_started = time.perf_counter()
    accumulator.accumulate_deposition(read_deposition_batch(deposition_path, input_warnings))
    deposition_accumulation_seconds = time.perf_counter() - deposition_started
    trajectory_started = time.perf_counter()
    for trajectory_path in trajectory_paths:
        batch = read_trajectory_sample_batch(trajectory_path, input_warnings)
        if batch is not None:
            accumulator.accumulate_trajectory(batch)
    trajectory_accumulation_seconds = time.perf_counter() - trajectory_started
    impact_started = time.perf_counter()
    for batch in read_impact_event_csv_batches(impact_event_paths, input_warnings):
        accumulator.accumulate_impacts(batch)
    for batch in read_impact_event_parquet_batches(impact_event_parquet_paths, input_warnings):
        accumulator.accumulate_impacts(batch)
    impact_accumulation_seconds = time.perf_counter() - impact_started
    stats = accumulator.stats()
    if not stats.trajectory_count and not stats.deposition_point_count and not stats.impact_event_count:
        raise SystemExit("no trajectory, deposition, or impact-event inputs found")

    normalization_started = time.perf_counter()
    layers, warnings = accumulator.layers()
    warnings = input_warnings + warnings + validate_layers(layers)
    normalization_seconds = time.perf_counter() - normalization_started
    accumulation_seconds = time.perf_counter() - accumulation_started

    core_write_started = time.perf_counter()
    metadata = build_metadata(
        case,
        diagnostics,
        grid,
        grid_source,
        layers,
        warnings,
        stats,
        statistic_config,
        probability_state,
        map_package_state,
        raster_export_config,
    )
    write_core_hazard_outputs(
        output_dir,
        prefix,
        grid,
        layers,
        accumulator.deposition_points,
        metadata,
        case,
        raster_export_config,
    )
    manifest_metadata = dict(metadata)
    manifest_metadata["_trajectory_paths"] = [str(path) for path in trajectory_paths]
    manifest_metadata["_deposition_path"] = str(deposition_path) if deposition_path else None
    manifest_metadata["_impact_event_paths"] = [str(path) for path in impact_event_paths]
    manifest_metadata["_impact_event_parquet_paths"] = [str(path) for path in impact_event_parquet_paths]
    core_output_write_seconds = time.perf_counter() - core_write_started

    plot_paths: dict[str, str] = {}
    plot_render_seconds = 0.0
    plots_enabled = not args.no_plots
    if plots_enabled:
        plot_started = time.perf_counter()
        plot_paths = render_png_layers(output_dir, prefix, grid, layers)
        write_html_report(output_dir / "index.html", case, metadata, layers, plot_paths, prefix)
        plot_render_seconds = time.perf_counter() - plot_started
    manifest = build_hazard_manifest(
        case,
        diagnostics,
        manifest_metadata,
        output_dir,
        prefix,
        grid,
        grid_source,
        layers,
        plot_paths,
        warnings,
        statistic_config,
        probability_state,
        map_package_state,
        raster_export_config,
        total_wall_seconds=time.perf_counter() - total_started,
        accumulation_seconds=accumulation_seconds,
        core_output_write_seconds=core_output_write_seconds,
        plot_render_seconds=plot_render_seconds,
        plots_enabled=plots_enabled,
        input_file_counts={
            "trajectory_files_scanned": sum(1 for path in trajectory_paths if path.exists()),
            "deposition_files_scanned": 1 if deposition_path is not None and deposition_path.exists() else 0,
            "impact_csv_files_scanned": sum(1 for path in impact_event_paths if path.exists()),
            "impact_parquet_tables_scanned": sum(1 for path in impact_event_parquet_paths if path.exists()),
        },
        bounds_stats=bounds_stats,
        timings=HazardAccumulationTimings(
            bounds_discovery_seconds=bounds_discovery_seconds,
            deposition_accumulation_seconds=deposition_accumulation_seconds,
            trajectory_accumulation_seconds=trajectory_accumulation_seconds,
            impact_accumulation_seconds=impact_accumulation_seconds,
            normalization_seconds=normalization_seconds,
        ),
    )
    hazard_manifest_path = output_dir / f"{prefix}_manifest.json"
    write_text(hazard_manifest_path, json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    if map_package_state is not None:
        package_path = map_package_output_path(map_package_state, output_dir, prefix)
        write_map_package_manifest(
            package_path,
            map_package_state,
            hazard_manifest_path,
            manifest["layer_semantics"],
            geotiff_raster_outputs(manifest["outputs"]),
        )
        manifest["outputs"].append(output_manifest_entry(package_path, "map_package_manifest", "json"))
        manifest["performance"]["output_file_count"] = sum(
            int(output["file_count"]) for output in manifest["outputs"]
        )
        manifest["performance"]["output_bytes"] = sum(int(output["total_bytes"]) for output in manifest["outputs"])
        write_text(hazard_manifest_path, json.dumps(manifest, indent=2, sort_keys=True) + "\n")

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
    *,
    suppress_case_defaults: bool = False,
) -> list[Path]:
    paths = [explicit_impact_events] if explicit_impact_events else []
    dirs = list(explicit_dirs)
    if not paths and not dirs and not suppress_case_defaults:
        dirs = case_output_paths(case, "ensemble_impact_events_dir")
    for directory in dirs:
        paths.extend(csv_files_in_dir(directory))
    if not paths:
        single = first_case_output_path(case, "impact_events_csv")
        if single:
            paths.append(single)
    return paths


def resolve_impact_event_parquet_paths(
    case: dict[str, Any],
    explicit_paths: list[Path],
    *,
    suppress_case_defaults: bool = False,
) -> list[Path]:
    paths = list(explicit_paths)
    if not paths and not suppress_case_defaults:
        paths = case_output_paths(case, "ensemble_impact_events_parquet")
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


def parse_raster_export_config(case: dict[str, Any], args: argparse.Namespace) -> RasterExportConfig:
    raw = case.get("hazard_exports") or case.get("raster_exports") or {}
    if raw and not isinstance(raw, dict):
        raise SystemExit("hazard_exports must be a mapping")
    geotiff = bool(raw.get("geotiff", False)) or bool(args.export_geotiff) or bool(args.export_cog)
    cog = bool(raw.get("cog", False)) or bool(args.export_cog)
    if cog:
        raise SystemExit(
            "COG export is not implemented in Phase 2A without a verified COG writer; use --export-geotiff"
        )
    compression = str(raw.get("geotiff_compression") or raw.get("compression") or "none")
    if compression not in {"none", "uncompressed"}:
        raise SystemExit(
            "Phase 2A GeoTIFF export uses an uncompressed stdlib writer; compressed/COG export is deferred"
        )
    compression = "none"
    return RasterExportConfig(geotiff=geotiff, cog=False, compression=compression)


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


def parse_hazard_probability(case: dict[str, Any]) -> HazardProbabilityConfig | None:
    raw = case.get("hazard_probability")
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise SystemExit("hazard_probability must be a mapping")
    probability_model = str(raw.get("probability_model") or "")
    if probability_model != "sampling_weighted":
        raise SystemExit("hazard_probability.probability_model must be sampling_weighted")
    normalization = str(raw.get("normalization_convention") or "")
    if normalization != "conditioned_on_filter":
        raise SystemExit("hazard_probability.normalization_convention must be conditioned_on_filter")
    weight_column = str(raw.get("weight_column") or "")
    if weight_column != "sampling_weight":
        raise SystemExit("hazard_probability.weight_column must be sampling_weight")
    metadata_path = raw.get("metadata_path")
    if not metadata_path:
        raise SystemExit("hazard_probability.metadata_path is required")
    filters = raw.get("filters") or {}
    if not isinstance(filters, dict):
        raise SystemExit("hazard_probability.filters must be a mapping")
    block_mass_min = optional_float(filters.get("block_mass_kg_min"), "block_mass_kg_min")
    block_mass_max = optional_float(filters.get("block_mass_kg_max"), "block_mass_kg_max")
    if block_mass_min is not None and block_mass_max is not None and block_mass_min > block_mass_max:
        raise SystemExit("hazard_probability.filters.block_mass_kg_min cannot exceed block_mass_kg_max")
    return HazardProbabilityConfig(
        probability_model=probability_model,
        metadata_path=ROOT / str(metadata_path),
        weight_column=weight_column,
        normalization_convention=normalization,
        filters=HazardProbabilityFilters(
            source_zone_ids=tuple(str(value) for value in list_from_any(filters.get("source_zone_ids"))),
            scenario_ids=tuple(str(value) for value in list_from_any(filters.get("scenario_ids"))),
            block_mass_kg_min=block_mass_min,
            block_mass_kg_max=block_mass_max,
        ),
    )


def parse_hazard_map_package(case: dict[str, Any], args: argparse.Namespace) -> HazardMapPackageConfig | None:
    raw = case.get("hazard_map_package") or case.get("map_package") or {}
    if raw and not isinstance(raw, dict):
        raise SystemExit("hazard_map_package must be a mapping")
    values = {
        "map_product_id": args.map_product_id or raw.get("map_product_id"),
        "probability_mode": args.probability_mode or raw.get("probability_mode"),
        "normalization_scope": args.normalization_scope or raw.get("normalization_scope"),
        "source_zone_metadata_path": args.source_zone_metadata_path or raw.get("source_zone_metadata_path"),
        "scenario_table_path": args.scenario_table_path or raw.get("scenario_table_path"),
        "map_package_manifest_json": args.map_package_manifest_json or raw.get("map_package_manifest_json"),
    }
    if not raw and not any(value is not None for value in values.values()):
        return None
    missing = [
        field
        for field in (
            "map_product_id",
            "probability_mode",
            "normalization_scope",
            "source_zone_metadata_path",
        )
        if not values[field]
    ]
    if missing:
        raise SystemExit(f"hazard_map_package missing required fields: {', '.join(missing)}")
    probability_mode = str(values["probability_mode"])
    if probability_mode not in {
        "unweighted_diagnostic",
        "sampling_weighted_conditional",
        "physical_probability",
        "annual_frequency",
    }:
        raise SystemExit("hazard_map_package.probability_mode is not a supported Phase 1 label")
    normalization_scope = str(values["normalization_scope"])
    if normalization_scope not in {
        "conditioned_on_filter",
        "conditioned_on_scenario",
        "absolute_probability_mass",
        "annual_frequency_sum",
    }:
        raise SystemExit("hazard_map_package.normalization_scope is not a supported Phase 1 label")
    return HazardMapPackageConfig(
        map_product_id=stable_required_id(str(values["map_product_id"]), "hazard_map_package.map_product_id"),
        probability_mode=probability_mode,
        normalization_scope=normalization_scope,
        source_zone_metadata_path=ROOT / str(values["source_zone_metadata_path"]),
        scenario_table_path=ROOT / str(values["scenario_table_path"]) if values["scenario_table_path"] else None,
        map_package_manifest_json=ROOT / str(values["map_package_manifest_json"])
        if values["map_package_manifest_json"]
        else None,
        validation_context=tuple(str(value) for value in list_from_any(raw.get("validation_context"))),
        limitations=tuple(str(value) for value in list_from_any(raw.get("limitations"))),
    )


def load_hazard_map_package_state(
    config: HazardMapPackageConfig | None,
    probability: HazardProbabilityState | None,
) -> HazardMapPackageState | None:
    if config is None:
        return None
    if not config.source_zone_metadata_path.exists():
        raise SystemExit(f"source_zone_metadata_v1 file does not exist: {config.source_zone_metadata_path}")
    source_zone = load_yaml(config.source_zone_metadata_path)
    if source_zone.get("schema_version") != "source_zone_metadata_v1":
        raise SystemExit("source_zone_metadata_path must point to source_zone_metadata_v1")
    source_zone_id = stable_required_id(str(source_zone.get("source_zone_id") or ""), "source_zone_id")
    annual_frequency_fields_present = source_zone.get("annual_release_frequency_per_year") not in (None, "")
    if config.probability_mode == "annual_frequency":
        raise SystemExit(
            "annual_frequency is schema-visible but unsupported in Phase 1; Level 3 temporal/source-frequency semantics are required"
        )
    if config.probability_mode == "physical_probability":
        raise SystemExit("physical_probability map products are schema-visible but not generated by the Phase 1 hazard builder")
    if config.probability_mode == "unweighted_diagnostic":
        if config.normalization_scope in {"absolute_probability_mass", "annual_frequency_sum"}:
            raise SystemExit("unweighted_diagnostic map packages cannot use physical or annual normalization scopes")
        if probability is not None:
            raise SystemExit(
                "hazard_probability is configured; use probability_mode sampling_weighted_conditional for weighted outputs"
            )
    if config.probability_mode == "sampling_weighted_conditional":
        if config.normalization_scope not in {"conditioned_on_filter", "conditioned_on_scenario"}:
            raise SystemExit(
                "sampling_weighted_conditional requires conditioned_on_filter or conditioned_on_scenario"
            )
        if probability is None:
            raise SystemExit(
                "sampling_weighted_conditional map packages require hazard_probability sampling_weighted metadata"
            )
        if config.scenario_table_path is None:
            raise SystemExit("sampling_weighted_conditional map packages require scenario_table_path")
    scenario_rows = load_scenario_table(config.scenario_table_path) if config.scenario_table_path else ()
    if config.probability_mode == "sampling_weighted_conditional" and not scenario_rows:
        raise SystemExit("sampling_weighted_conditional map packages require scenario_table_v1 rows")
    for row in scenario_rows:
        if row.source_zone_id != source_zone_id:
            raise SystemExit(
                f"scenario_table source_zone_id {row.source_zone_id!r} does not match source metadata {source_zone_id!r}"
            )
        annual_frequency_fields_present = annual_frequency_fields_present or row.annual_frequency_per_year is not None or row.time_horizon_years is not None
        if row.release_probability is not None or row.scenario_probability is not None:
            raise SystemExit("physical probability columns are not active in Phase 1 hazard map-package writing")
    if annual_frequency_fields_present:
        raise SystemExit(
            "annual-frequency fields are present but unsupported in Phase 1; Level 3 temporal/source-frequency semantics are required"
        )
    if probability is not None:
        scenario_ids = {row.scenario_id for row in scenario_rows}
        for record in probability.weights.values():
            if record.source_zone_id != source_zone_id:
                raise SystemExit(
                    f"trajectory metadata source_zone_id {record.source_zone_id!r} does not match source metadata {source_zone_id!r}"
                )
            if scenario_ids and record.scenario_id not in scenario_ids:
                raise SystemExit(
                    f"trajectory metadata scenario_id {record.scenario_id!r} is not present in scenario_table_v1"
                )
    return HazardMapPackageState(
        config=config,
        source_zone_id=source_zone_id,
        scenario_rows=scenario_rows,
        annual_frequency_fields_present=False,
    )


def load_scenario_table(path: Path | None) -> tuple[ScenarioMetadataRow, ...]:
    if path is None:
        return ()
    if not path.exists():
        raise SystemExit(f"scenario_table_v1 file does not exist: {path}")
    rows: list[ScenarioMetadataRow] = []
    with path.open(newline="") as file:
        reader = csv.DictReader(file)
        required = {
            "scenario_id",
            "source_zone_id",
            "release_sampling_policy",
            "model_configuration_id",
            "terrain_material_assumption_id",
            "sampling_weight",
        }
        missing = sorted(required.difference(reader.fieldnames or ()))
        if missing:
            raise SystemExit(f"scenario_table_v1 is missing required columns: {', '.join(missing)}")
        for index, row in enumerate(reader):
            weight = parse_required_float(row.get("sampling_weight"), "sampling_weight")
            if weight < 0.0:
                raise SystemExit(f"scenario_table_v1 row {index} has negative sampling_weight")
            rows.append(
                ScenarioMetadataRow(
                    scenario_id=stable_required_id(str(row.get("scenario_id") or ""), "scenario_id"),
                    source_zone_id=stable_required_id(str(row.get("source_zone_id") or ""), "source_zone_id"),
                    sampling_weight=weight,
                    release_probability=parse_optional_float_text(row.get("release_probability"), "release_probability"),
                    scenario_probability=parse_optional_float_text(row.get("scenario_probability"), "scenario_probability"),
                    annual_frequency_per_year=parse_optional_float_text(
                        row.get("annual_frequency_per_year"),
                        "annual_frequency_per_year",
                    ),
                    time_horizon_years=parse_optional_float_text(row.get("time_horizon_years"), "time_horizon_years"),
                )
            )
    if not rows:
        raise SystemExit("scenario_table_v1 must not be empty")
    return tuple(rows)


def stable_required_id(value: str, field: str) -> str:
    value = value.strip()
    if not value:
        raise SystemExit(f"{field} must be set")
    allowed = set("_-.:/")
    if not all(ch.isascii() and (ch.isalnum() or ch in allowed) for ch in value):
        raise SystemExit(f"{field} must be a stable ASCII id")
    return value


def load_hazard_probability_state(
    config: HazardProbabilityConfig | None,
    trajectory_paths: list[Path],
    deposition_path: Path | None,
    impact_event_paths: list[Path],
    impact_event_parquet_paths: list[Path],
) -> HazardProbabilityState | None:
    if config is None:
        return None
    if not config.metadata_path.exists():
        raise SystemExit(f"hazard_probability metadata file does not exist: {config.metadata_path}")
    all_rows: dict[str, TrajectoryWeight] = {}
    total_input_weight = 0.0
    total_filtered_weight = 0.0
    with config.metadata_path.open(newline="") as file:
        reader = csv.DictReader(file)
        if not reader.fieldnames or "trajectory_id" not in reader.fieldnames:
            raise SystemExit("trajectory metadata must contain trajectory_id")
        if config.weight_column not in reader.fieldnames:
            raise SystemExit(f"trajectory metadata must contain {config.weight_column}")
        for row in reader:
            trajectory_id = str(row.get("trajectory_id") or "").strip()
            if not trajectory_id:
                raise SystemExit("trajectory metadata contains an empty trajectory_id")
            if trajectory_id in all_rows:
                raise SystemExit(f"trajectory metadata contains duplicate trajectory_id: {trajectory_id}")
            weight = parse_required_float(row.get(config.weight_column), config.weight_column)
            if weight < 0.0:
                raise SystemExit(f"sampling weights must be non-negative: {trajectory_id}")
            record = TrajectoryWeight(
                trajectory_id=trajectory_id,
                weight=weight,
                source_zone_id=blank_to_none(row.get("source_zone_id")),
                scenario_id=blank_to_none(row.get("scenario_id")),
                block_mass_kg=parse_optional_float_text(row.get("block_mass_kg"), "block_mass_kg"),
            )
            all_rows[trajectory_id] = record
            total_input_weight += weight

    filtered = {
        trajectory_id: record
        for trajectory_id, record in all_rows.items()
        if metadata_record_matches_filters(record, config.filters)
    }
    total_filtered_weight = math.fsum(record.weight for record in filtered.values())
    if total_filtered_weight <= 0.0:
        raise SystemExit("filtered total sampling weight must be positive")

    for path in trajectory_paths:
        trajectory_id = trajectory_id_from_path_or_file(path)
        if trajectory_id not in all_rows:
            raise SystemExit(f"trajectory id {trajectory_id!r} is missing from {config.metadata_path}")
        if trajectory_id not in filtered:
            raise SystemExit(
                f"trajectory id {trajectory_id!r} is excluded by hazard_probability filters; "
                "supply matching trajectory inputs or adjust filters"
            )

    for trajectory_id in trajectory_ids_from_hazard_side_inputs(
        deposition_path,
        impact_event_paths,
        impact_event_parquet_paths,
    ):
        if trajectory_id not in all_rows:
            raise SystemExit(f"trajectory id {trajectory_id!r} is missing from {config.metadata_path}")

    return HazardProbabilityState(
        config=config,
        weights=filtered,
        total_input_weight=total_input_weight,
        total_filtered_weight=total_filtered_weight,
    )


def metadata_record_matches_filters(record: TrajectoryWeight, filters: HazardProbabilityFilters) -> bool:
    if filters.source_zone_ids and record.source_zone_id not in filters.source_zone_ids:
        return False
    if filters.scenario_ids and record.scenario_id not in filters.scenario_ids:
        return False
    if filters.block_mass_kg_min is not None:
        if record.block_mass_kg is None or record.block_mass_kg < filters.block_mass_kg_min:
            return False
    if filters.block_mass_kg_max is not None:
        if record.block_mass_kg is None or record.block_mass_kg > filters.block_mass_kg_max:
            return False
    return True


def list_from_any(value: Any) -> list[Any]:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def optional_float(value: Any, name: str) -> float | None:
    if value is None:
        return None
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise SystemExit(f"hazard_probability.filters.{name} must be numeric") from exc
    if not math.isfinite(result):
        raise SystemExit(f"hazard_probability.filters.{name} must be finite")
    return result


def parse_required_float(value: Any, name: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise SystemExit(f"{name} must be numeric") from exc
    if not math.isfinite(result):
        raise SystemExit(f"{name} must be finite")
    return result


def parse_optional_float_text(value: Any, name: str) -> float | None:
    if value is None or value == "":
        return None
    return parse_required_float(value, name)


def blank_to_none(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def discover_bounds(
    trajectory_paths: list[Path],
    deposition_path: Path | None,
    impact_event_paths: list[Path],
    impact_event_parquet_paths: list[Path],
    cell_size: float,
    warnings: list[str],
) -> tuple[GridBounds, BoundsDiscoveryStats]:
    if cell_size <= 0.0:
        raise SystemExit("--cell-size must be positive")
    bounds = GridBounds.empty()
    stats = BoundsDiscoveryStats()
    for path in trajectory_paths:
        if path.exists():
            stats.trajectory_files_scanned += 1
            for row in iter_numeric_csv(path, f"trajectory:{path}", warnings, emit_warnings=False):
                stats.trajectory_rows_scanned += 1
                bounds.add_row(row)
    if deposition_path and deposition_path.exists():
        stats.deposition_files_scanned += 1
        for row in iter_numeric_csv(deposition_path, f"deposition:{deposition_path}", warnings, emit_warnings=False):
            stats.deposition_rows_scanned += 1
            bounds.add_row(row)
    for path in impact_event_paths:
        if path.exists():
            stats.impact_csv_files_scanned += 1
            for row in iter_numeric_csv(path, f"impact_events:{path}", warnings, emit_warnings=False):
                stats.impact_csv_rows_scanned += 1
                bounds.add_row(row)
    for path in impact_event_parquet_paths:
        if path.exists():
            stats.impact_parquet_tables_scanned += 1
            stats.impact_parquet_rows_scanned += add_parquet_xy_bounds(
                bounds,
                path,
                warnings,
                emit_warnings=False,
            )
    return bounds, stats


def read_trajectory_sample_batch(path: Path, warnings: list[str]) -> TrajectorySampleBatch | None:
    if not path.exists():
        return None
    samples: list[TrajectorySample] = []
    trajectory_id: str | None = None
    for row in iter_numeric_csv(path, f"trajectory:{path}", warnings):
        if trajectory_id is None:
            trajectory_id = trajectory_id_from_sample_or_path(row, path)
        samples.append(
            TrajectorySample(
                x_m=numeric(row.get("x_m")),
                y_m=numeric(row.get("y_m")),
                z_m=numeric(row.get("z_m")),
                kinetic_j=numeric(row.get("kinetic_j")),
                speed_mps=numeric(row.get("speed_mps")),
            )
        )
    return TrajectorySampleBatch(path=path, trajectory_id=trajectory_id, samples=tuple(samples))


def read_deposition_batch(path: Path | None, warnings: list[str]) -> DepositionPointBatch:
    if path is None or not path.exists():
        return DepositionPointBatch(points=())
    return DepositionPointBatch(
        points=tuple(
            deposition_point_from_row(row)
            for row in iter_numeric_csv(path, f"deposition:{path}", warnings)
        )
    )


def deposition_point_from_row(row: dict[str, float | str]) -> DepositionPoint:
    return DepositionPoint(
        x_m=numeric(row.get("x_m")),
        y_m=numeric(row.get("y_m")),
        properties={key: value for key, value in row.items() if key not in {"x_m", "y_m"}},
    )


def read_impact_event_csv_batches(paths: list[Path], warnings: list[str]) -> Iterator[ImpactEventBatch]:
    for path in paths:
        if not path.exists():
            continue
        event_count = 0
        significant_event_count = 0
        significant_points: list[tuple[float, float]] = []
        for event in iter_numeric_csv(path, f"impact_events:{path}", warnings):
            event_count += 1
            if (numeric(event.get("incoming_normal_speed_mps")) or 0.0) < SIGNIFICANT_IMPACT_MIN_NORMAL_SPEED_MPS:
                continue
            significant_event_count += 1
            x = numeric(event.get("x_m"))
            y = numeric(event.get("y_m"))
            if x is not None and y is not None:
                significant_points.append((x, y))
        yield ImpactEventBatch(
            source_path=path,
            event_count=event_count,
            significant_event_count=significant_event_count,
            significant_points=tuple(significant_points),
        )


def read_impact_event_parquet_batches(paths: list[Path], warnings: list[str]) -> Iterator[ImpactEventBatch]:
    for path in paths:
        if not path.exists():
            continue
        yield from iter_impact_event_parquet_batches(path, warnings)


def iter_numeric_csv(
    path: Path | None,
    label: str,
    warnings: list[str],
    *,
    emit_warnings: bool = True,
) -> Iterator[dict[str, float | str]]:
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


def add_parquet_xy_bounds(
    bounds: GridBounds,
    path: Path,
    warnings: list[str],
    *,
    emit_warnings: bool = True,
) -> int:
    try:
        import pyarrow.parquet as pq  # type: ignore
    except ImportError as exc:
        raise SystemExit("pyarrow is required for impact-event Parquet inputs") from exc
    parquet_file = pq.ParquetFile(path)
    require_parquet_columns(parquet_file, path, ("x_m", "y_m"))
    dropped = 0
    row_count = 0
    for batch in parquet_file.iter_batches(columns=["x_m", "y_m"], batch_size=65_536):
        xs = batch.column(0).to_pylist()
        ys = batch.column(1).to_pylist()
        for x_value, y_value in zip(xs, ys):
            row_count += 1
            x = finite_float(x_value)
            y = finite_float(y_value)
            if x is None or y is None:
                dropped += 1
                continue
            bounds.add_xy(x, y)
    if emit_warnings and dropped:
        warnings.append(f"dropped {dropped} non-finite coordinate rows from impact_events_parquet:{path}")
    return row_count


def iter_impact_event_parquet_batches(path: Path, warnings: list[str]) -> Iterator[ImpactEventBatch]:
    try:
        import pyarrow.parquet as pq  # type: ignore
    except ImportError as exc:
        raise SystemExit("pyarrow is required for impact-event Parquet inputs") from exc
    parquet_file = pq.ParquetFile(path)
    names = set(parquet_file.schema_arrow.names)
    require_parquet_columns(parquet_file, path, ("x_m", "y_m"))
    use_significant_flag = "significant_impact" in names
    if use_significant_flag:
        columns = ["x_m", "y_m", "significant_impact"]
    else:
        require_parquet_columns(parquet_file, path, ("incoming_normal_speed_mps",))
        columns = ["x_m", "y_m", "incoming_normal_speed_mps"]

    dropped = 0
    for batch in parquet_file.iter_batches(columns=columns, batch_size=65_536):
        xs = batch.column(0).to_pylist()
        ys = batch.column(1).to_pylist()
        significance_values = batch.column(2).to_pylist()
        impact_event_count = 0
        significant_impact_count = 0
        significant_points: list[tuple[float, float]] = []
        for x_value, y_value, significance_value in zip(xs, ys, significance_values):
            impact_event_count += 1
            if use_significant_flag:
                is_significant = bool(significance_value) if significance_value is not None else False
            else:
                normal_speed = finite_float(significance_value) or 0.0
                is_significant = normal_speed >= SIGNIFICANT_IMPACT_MIN_NORMAL_SPEED_MPS
            if not is_significant:
                continue
            significant_impact_count += 1
            x = finite_float(x_value)
            y = finite_float(y_value)
            if x is None or y is None:
                dropped += 1
                continue
            significant_points.append((x, y))
        yield ImpactEventBatch(
            source_path=path,
            event_count=impact_event_count,
            significant_event_count=significant_impact_count,
            significant_points=tuple(significant_points),
        )
    if dropped:
        warnings.append(f"dropped {dropped} non-finite significant impact rows from impact_events_parquet:{path}")


def require_parquet_columns(parquet_file: Any, path: Path, columns: tuple[str, ...]) -> None:
    names = set(parquet_file.schema_arrow.names)
    missing = [column for column in columns if column not in names]
    if missing:
        raise SystemExit(f"impact-event Parquet table {path} is missing required columns: {', '.join(missing)}")


def finite_float(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def sample_cell_from_xy(grid: GridSpec, x: float | None, y: float | None) -> tuple[int, int] | None:
    if x is None or y is None:
        return None
    return grid.cell(x, y)


def numeric(value: float | str | bool | None) -> float | None:
    return value if isinstance(value, float) and math.isfinite(value) else None


def safe_rate_or_none(count: int, seconds: float) -> float | None:
    return count / seconds if count > 0 and seconds > 0.0 else None


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


def increment_weighted_exceedance_grids(
    grids: dict[float, list[list[float]]],
    exceeded: dict[float, set[tuple[int, int]]],
    weight: float,
) -> None:
    for threshold, cells in exceeded.items():
        grid = grids[threshold]
        for row, col in cells:
            grid[row][col] += weight


def exceedance_layer_key(prefix: str, threshold: float, suffix: str) -> str:
    threshold_text = f"{threshold:g}".replace("-", "neg_").replace(".", "p")
    return f"{prefix}_{threshold_text}{suffix}"


def trajectory_id_from_sample_or_path(sample: dict[str, float | str], path: Path) -> str:
    value = sample.get("trajectory_id")
    if isinstance(value, str) and value:
        return value
    return path.stem


def trajectory_id_from_path_or_file(path: Path) -> str:
    if path.exists():
        with path.open(newline="") as file:
            reader = csv.DictReader(file)
            try:
                row = next(reader)
            except StopIteration:
                return path.stem
            value = row.get("trajectory_id")
            if value:
                return str(value)
    return path.stem


def trajectory_ids_from_hazard_side_inputs(
    deposition_path: Path | None,
    impact_event_paths: list[Path],
    impact_event_parquet_paths: list[Path],
) -> set[str]:
    ids: set[str] = set()
    if deposition_path is not None:
        ids.update(trajectory_ids_from_csv_if_available(deposition_path))
    for path in impact_event_paths:
        ids.update(trajectory_ids_from_csv_if_available(path))
    for path in impact_event_parquet_paths:
        ids.update(trajectory_ids_from_parquet_if_available(path))
    return ids


def trajectory_ids_from_csv_if_available(path: Path) -> set[str]:
    if not path.exists():
        return set()
    with path.open(newline="") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames and "trajectory_id" in reader.fieldnames:
            return {str(row["trajectory_id"]).strip() for row in reader if str(row.get("trajectory_id") or "").strip()}
    if path.stem.startswith("trajectory_"):
        return {path.stem}
    return set()


def trajectory_ids_from_parquet_if_available(path: Path) -> set[str]:
    if not path.exists():
        return set()
    try:
        import pyarrow.parquet as pq  # type: ignore
    except ImportError as exc:
        raise SystemExit("pyarrow is required for impact-event Parquet inputs") from exc
    parquet_file = pq.ParquetFile(path)
    if "trajectory_id" not in parquet_file.schema_arrow.names:
        raise SystemExit(f"impact-event Parquet table must contain trajectory_id: {path}")
    ids: set[str] = set()
    for batch in parquet_file.iter_batches(columns=["trajectory_id"], batch_size=65_536):
        for row in batch.to_pylist():
            value = str(row.get("trajectory_id") or "").strip()
            if value:
                ids.add(value)
    return ids


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
                curvature_x=float(
                    parameters.get("ax", parameters.get("curvature_x", parameters.get("a", 0.0))) or 0.0
                ),
                curvature_y=float(
                    parameters.get("ay", parameters.get("curvature_y", parameters.get("b", 0.0))) or 0.0
                ),
                x0=float(parameters.get("x0_m", 0.0) or 0.0),
                y0=float(parameters.get("y0_m", 0.0) or 0.0),
            )
        if terrain_type in {"step", "step_terrain"}:
            return StepTerrain(
                z_low=float(parameters.get("low_z_m", parameters.get("z_low_m", 0.0)) or 0.0),
                z_high=float(
                    parameters.get("high_z_m", parameters.get("z_high_m", parameters.get("height_m", 0.0)))
                    or 0.0
                ),
                x_step=float(parameters.get("step_x_m", parameters.get("x_step_m", 0.0)) or 0.0),
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
        return self.z_high if x < self.x_step else self.z_low


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


def write_geotiff_layers(
    output_dir: Path,
    prefix: str,
    grid: GridSpec,
    layers: list[RasterLayer],
    case: dict[str, Any],
    export_config: RasterExportConfig,
) -> None:
    if not export_config.geotiff:
        return
    spatial_reference = geotiff_spatial_reference(case, grid)
    for layer in layers:
        write_geotiff_grid(
            output_dir / f"{prefix}_{layer.key}.tif",
            grid,
            layer,
            spatial_reference,
            export_config,
        )


def write_geotiff_grid(
    path: Path,
    grid: GridSpec,
    layer: RasterLayer,
    spatial_reference: dict[str, Any],
    export_config: RasterExportConfig,
) -> None:
    _ = export_config
    path.parent.mkdir(parents=True, exist_ok=True)
    pixels = [float(ascii_value(value)) for row in layer.values for value in row]
    pixel_bytes = b"".join(struct.pack("<d", value) for value in pixels)
    data_offset = 8
    ifd_offset = data_offset + len(pixel_bytes)
    entries: list[tuple[int, int, int, bytes]] = [
        (256, 4, 1, struct.pack("<I", grid.ncols)),  # ImageWidth
        (257, 4, 1, struct.pack("<I", grid.nrows)),  # ImageLength
        (258, 3, 1, struct.pack("<H", 64)),  # BitsPerSample
        (259, 3, 1, struct.pack("<H", 1)),  # Compression = none
        (262, 3, 1, struct.pack("<H", 1)),  # BlackIsZero
        (273, 4, 1, struct.pack("<I", data_offset)),  # StripOffsets
        (277, 3, 1, struct.pack("<H", 1)),  # SamplesPerPixel
        (278, 4, 1, struct.pack("<I", grid.nrows)),  # RowsPerStrip
        (279, 4, 1, struct.pack("<I", len(pixel_bytes))),  # StripByteCounts
        (284, 3, 1, struct.pack("<H", 1)),  # PlanarConfiguration
        (339, 3, 1, struct.pack("<H", 3)),  # SampleFormat = IEEE floating point
        (33550, 12, 3, struct.pack("<ddd", float(grid.cell_size), float(grid.cell_size), 0.0)),
        (33922, 12, 6, struct.pack("<dddddd", 0.0, 0.0, 0.0, float(grid.xmin), float(grid.ymax), 0.0)),
        (42113, 2, len(str(NODATA)) + 1, str(NODATA).encode("ascii") + b"\0"),
    ]
    geokeys = geokey_directory(spatial_reference.get("epsg"))
    if geokeys:
        entries.append((34735, 3, len(geokeys), struct.pack("<" + "H" * len(geokeys), *geokeys)))
    ifd_bytes = build_tiff_ifd(entries, ifd_offset)
    path.write_bytes(b"II" + struct.pack("<HI", 42, ifd_offset) + pixel_bytes + ifd_bytes)


def build_tiff_ifd(entries: list[tuple[int, int, int, bytes]], ifd_offset: int) -> bytes:
    entries = sorted(entries, key=lambda item: item[0])
    inline_size = 2 + 12 * len(entries) + 4
    extra = bytearray()
    directory = bytearray(struct.pack("<H", len(entries)))
    for tag, field_type, count, value_bytes in entries:
        if len(value_bytes) <= 4:
            value_or_offset = value_bytes.ljust(4, b"\0")
        else:
            if len(extra) % 2:
                extra.extend(b"\0")
            value_offset = ifd_offset + inline_size + len(extra)
            value_or_offset = struct.pack("<I", value_offset)
            extra.extend(value_bytes)
        directory.extend(struct.pack("<HHI", tag, field_type, count))
        directory.extend(value_or_offset)
    directory.extend(struct.pack("<I", 0))
    directory.extend(extra)
    return bytes(directory)


def geokey_directory(epsg: Any) -> tuple[int, ...] | None:
    try:
        epsg_code = int(epsg)
    except (TypeError, ValueError):
        return None
    if epsg_code <= 0:
        return None
    if epsg_code == 4326:
        entries = [
            (1024, 0, 1, 2),  # GTModelTypeGeoKey = geographic
            (1025, 0, 1, 1),  # GTRasterTypeGeoKey = PixelIsArea
            (2048, 0, 1, epsg_code),  # GeographicTypeGeoKey
        ]
    else:
        entries = [
            (1024, 0, 1, 1),  # GTModelTypeGeoKey = projected
            (1025, 0, 1, 1),  # GTRasterTypeGeoKey = PixelIsArea
            (3072, 0, 1, epsg_code),  # ProjectedCSTypeGeoKey
            (3076, 0, 1, 9001),  # ProjLinearUnitsGeoKey = metre
        ]
    flattened: list[int] = [1, 1, 0, len(entries)]
    for entry in entries:
        flattened.extend(entry)
    return tuple(flattened)


def geotiff_spatial_reference(case: dict[str, Any], grid: GridSpec) -> dict[str, Any]:
    terrain = hazard_terrain_manifest(case, [])
    return {
        "crs": terrain.get("crs"),
        "epsg": terrain.get("epsg"),
        "vertical_datum": terrain.get("vertical_datum"),
        "nodata": NODATA,
        "affine_transform": geotiff_affine_transform(grid),
    }


def geotiff_affine_transform(grid: GridSpec) -> list[float]:
    return [grid.cell_size, 0.0, grid.xmin, 0.0, -grid.cell_size, grid.ymax]


def write_deposition_geojson(path: Path, depositions: list[DepositionPoint]) -> None:
    features = []
    for point in depositions:
        x = point.x_m
        y = point.y_m
        if x is None or y is None:
            continue
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [x, y]},
                "properties": point.properties,
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
    probability: HazardProbabilityState | None,
    map_package: HazardMapPackageState | None,
    raster_exports: RasterExportConfig,
) -> dict[str, Any]:
    weighted_layer_names = [
        layer.key for layer in layers if layer.key.startswith("weighted_")
    ]
    layer_semantics = build_layer_semantics(layers, probability, map_package)
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
        "hazard_probability": probability.as_manifest(weighted_layer_names) if probability else None,
        "hazard_map_package": hazard_map_package_manifest_section(map_package, probability) if map_package else None,
        "raster_exports": raster_exports.as_metadata(),
        "layer_semantics": layer_semantics,
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


def hazard_map_package_manifest_section(
    map_package: HazardMapPackageState | None,
    probability: HazardProbabilityState | None,
) -> dict[str, Any] | None:
    if map_package is None:
        return None
    scenario_weights = [row.sampling_weight for row in map_package.scenario_rows]
    return {
        "schema_version": "map_package_manifest_v1",
        "map_product_id": map_package.config.map_product_id,
        "probability_mode": map_package.config.probability_mode,
        "normalization_scope": map_package.config.normalization_scope,
        "source_zone_id": map_package.source_zone_id,
        "source_zone_metadata_path": str(map_package.config.source_zone_metadata_path),
        "scenario_table_path": str(map_package.config.scenario_table_path)
        if map_package.config.scenario_table_path
        else None,
        "scenario_ids": map_package.scenario_ids,
        "total_sampling_weight": math.fsum(scenario_weights) if scenario_weights else None,
        "total_filtered_weight": probability.total_filtered_weight if probability else None,
        "annual_frequency_fields_present": False,
        "operational_status": "research_diagnostic",
    }


def build_layer_semantics(
    layers: list[RasterLayer],
    probability: HazardProbabilityState | None,
    map_package: HazardMapPackageState | None,
) -> list[dict[str, Any]]:
    conditioning = []
    if map_package is not None:
        conditioning.append(f"source_zone_id={map_package.source_zone_id}")
        conditioning.extend(f"scenario_id={scenario_id}" for scenario_id in map_package.scenario_ids)
    semantics = []
    for layer in layers:
        weighted = layer.key.startswith("weighted_")
        semantics.append(
            {
                "layer_name": layer.key,
                "units": layer_semantic_units(layer, map_package),
                "numerator": layer_semantic_numerator(layer.key, weighted),
                "denominator": layer_semantic_denominator(layer.key, weighted, probability, map_package),
                "conditioned_on": conditioning,
                "weighted": weighted,
                "is_annualized": False,
                "annualized": False,
            }
        )
    return semantics


def layer_semantic_units(layer: RasterLayer, map_package: HazardMapPackageState | None) -> str:
    if map_package is not None and (
        "probability" in layer.key or "exceedance" in layer.key or layer.key.endswith("_density")
    ):
        return "dimensionless"
    return layer.units


def layer_semantic_numerator(layer_key: str, weighted: bool) -> str:
    if layer_key == "reach_probability" or layer_key == "weighted_reach_probability":
        return "trajectories reaching cell"
    if "exceedance" in layer_key:
        return "trajectories exceeding threshold in cell"
    if layer_key == "deposition_density":
        return "deposition points in cell"
    if layer_key == "significant_impact_density":
        return "significant impact events in cell"
    if layer_key.startswith("max_"):
        return "maximum sampled value in cell"
    return "cell value"


def layer_semantic_denominator(
    layer_key: str,
    weighted: bool,
    probability: HazardProbabilityState | None,
    map_package: HazardMapPackageState | None,
) -> str | None:
    if weighted and probability is not None:
        return f"filtered sampling_weight sum ({probability.total_filtered_weight:g})"
    if layer_key == "reach_probability" or "exceedance" in layer_key:
        if map_package is not None:
            return "trajectory count conditioned on source/scenario metadata"
        return "supplied trajectory count"
    if layer_key == "deposition_density":
        return "deposition point count"
    if layer_key == "significant_impact_density":
        return "significant impact event count"
    return None


def write_core_hazard_outputs(
    output_dir: Path,
    prefix: str,
    grid: GridSpec,
    layers: list[RasterLayer],
    deposition_points: list[DepositionPoint],
    metadata: dict[str, Any],
    case: dict[str, Any],
    raster_exports: RasterExportConfig,
) -> None:
    write_layers(output_dir, prefix, grid, layers)
    write_geotiff_layers(output_dir, prefix, grid, layers, case, raster_exports)
    write_deposition_geojson(output_dir / f"{prefix}_deposition_points.geojson", deposition_points)
    write_text(output_dir / f"{prefix}_metadata.json", json.dumps(metadata, indent=2, sort_keys=True) + "\n")


def map_package_output_path(
    map_package: HazardMapPackageState,
    output_dir: Path,
    prefix: str,
) -> Path:
    return map_package.config.map_package_manifest_json or output_dir / f"{prefix}_map_package_manifest.json"


def write_map_package_manifest(
    path: Path,
    map_package: HazardMapPackageState,
    hazard_manifest_path: Path,
    layer_semantics: list[dict[str, Any]],
    raster_outputs: list[dict[str, Any]],
) -> None:
    limitations = list(map_package.config.limitations) or [
        "Research diagnostic; not operational hazard validation.",
        "No annual frequency model is implemented in Phase 1.",
        "Physical occurrence probabilities, exposure, vulnerability, and risk are out of scope.",
    ]
    manifest = {
        "schema_version": "map_package_manifest_v1",
        "map_product_id": map_package.config.map_product_id,
        "map_product_version": "map_package_v1",
        "probability_mode": map_package.config.probability_mode,
        "normalization_scope": map_package.config.normalization_scope,
        "source_zone_id": map_package.source_zone_id,
        "source_zone_metadata_path": str(map_package.config.source_zone_metadata_path),
        "scenario_table_path": str(map_package.config.scenario_table_path)
        if map_package.config.scenario_table_path
        else None,
        "hazard_manifest_paths": [str(hazard_manifest_path)],
        "raster_outputs": raster_outputs,
        "layer_semantics": [
            {
                "layer_name": semantic["layer_name"],
                "units": semantic["units"],
                "conditioned_on": semantic["conditioned_on"],
                "is_annualized": False,
                "numerator": semantic["numerator"],
                "denominator": semantic["denominator"],
                "weighted": semantic["weighted"],
            }
            for semantic in layer_semantics
        ],
        "validation_context": list(map_package.config.validation_context),
        "limitations": limitations,
        "operational_status": "research_diagnostic",
    }
    write_text(path, json.dumps(manifest, indent=2, sort_keys=True) + "\n")


def build_hazard_manifest(
    case: dict[str, Any],
    diagnostics: dict[str, Any],
    metadata: dict[str, Any],
    output_dir: Path,
    prefix: str,
    grid: GridSpec,
    grid_source: str,
    layers: list[RasterLayer],
    plot_paths: dict[str, str],
    warnings: list[str],
    statistic_config: HazardStatisticConfig,
    probability: HazardProbabilityState | None,
    map_package: HazardMapPackageState | None,
    raster_exports: RasterExportConfig,
    *,
    total_wall_seconds: float,
    accumulation_seconds: float,
    core_output_write_seconds: float,
    plot_render_seconds: float,
    plots_enabled: bool,
    input_file_counts: dict[str, int],
    bounds_stats: BoundsDiscoveryStats,
    timings: HazardAccumulationTimings,
) -> dict[str, Any]:
    outputs: list[dict[str, Any]] = []
    for layer in layers:
        outputs.append(output_manifest_entry(output_dir / f"{prefix}_{layer.key}.csv", "hazard_layer", "csv_grid"))
        outputs.append(output_manifest_entry(output_dir / f"{prefix}_{layer.key}.asc", "hazard_layer", "esri_ascii_grid"))
        if raster_exports.geotiff:
            outputs.append(geotiff_output_manifest_entry(output_dir / f"{prefix}_{layer.key}.tif", layer, grid, case))
    outputs.append(output_manifest_entry(output_dir / f"{prefix}_deposition_points.geojson", "deposition_points", "geojson"))
    outputs.append(output_manifest_entry(output_dir / f"{prefix}_metadata.json", "hazard_metadata", "json"))
    if plots_enabled:
        outputs.append(output_manifest_entry(output_dir / "index.html", "hazard_report", "html"))
    for layer_key, filename in sorted(plot_paths.items()):
        outputs.append(output_manifest_entry(output_dir / filename, f"{layer_key}_plot", "png"))

    terrain = case.get("terrain") or {}
    random = case.get("random") or {}
    output_file_count = sum(int(output["file_count"]) for output in outputs)
    output_bytes = sum(int(output["total_bytes"]) for output in outputs)
    inputs = metadata.get("inputs", {})
    accumulation_seconds = max(0.0, accumulation_seconds)
    core_output_write_seconds = max(0.0, core_output_write_seconds)
    plot_render_seconds = max(0.0, plot_render_seconds)
    output_write_seconds = core_output_write_seconds + plot_render_seconds
    trajectory_sample_rows = int(inputs.get("trajectory_sample_count", 0) or 0)
    deposition_rows = int(inputs.get("deposition_point_count", 0) or 0)
    impact_rows = int(inputs.get("impact_event_count", 0) or 0)
    total_hazard_input_rows = trajectory_sample_rows + deposition_rows + impact_rows
    layer_semantics = metadata.get("layer_semantics", [])
    return {
        "schema_version": "run_manifest_v1",
        "created_unix_s": int(datetime.now(timezone.utc).timestamp()),
        "case_id": metadata.get("case_id"),
        "model_version": metadata.get("model_version"),
        "git_hash": diagnostics.get("git_hash"),
        "config_fingerprint": None,
        "completion_status": "completed",
        "execution_status": "completed",
        "scientific_status": "not_evaluated",
        "seed_policy": {
            "global_seed": random.get("seed"),
            "ensemble_size": random.get("ensemble_size", 1),
            "derivation": "hazard post-processing consumes existing simulation outputs; seed derivation is inherited from the source run",
        },
        "terrain": hazard_terrain_manifest(case, warnings),
        "outputs": outputs,
        "performance": {
            "total_wall_seconds": max(0.0, total_wall_seconds),
            "terrain_load_seconds": 0.0,
            "release_generation_seconds": 0.0,
            "simulation_seconds": 0.0,
            "output_write_seconds": output_write_seconds,
            "hazard_layer_seconds": accumulation_seconds,
            "accumulation_seconds": accumulation_seconds,
            "core_output_write_seconds": core_output_write_seconds,
            "plot_render_seconds": plot_render_seconds,
            "plots_enabled": plots_enabled,
            "bounds_discovery_seconds": max(0.0, timings.bounds_discovery_seconds),
            "deposition_accumulation_seconds": max(0.0, timings.deposition_accumulation_seconds),
            "trajectory_accumulation_seconds": max(0.0, timings.trajectory_accumulation_seconds),
            "impact_accumulation_seconds": max(0.0, timings.impact_accumulation_seconds),
            "normalization_seconds": max(0.0, timings.normalization_seconds),
            "trajectory_count": int(inputs.get("trajectory_count", 0) or 0),
            "impact_event_count": int(inputs.get("impact_event_count", 0) or 0),
            "trajectory_sample_rows_read": trajectory_sample_rows,
            "deposition_rows_read": deposition_rows,
            "impact_event_rows_read": impact_rows,
            "total_hazard_input_rows_read": total_hazard_input_rows,
            **input_file_counts,
            "bounds_trajectory_files_scanned": bounds_stats.trajectory_files_scanned,
            "bounds_deposition_files_scanned": bounds_stats.deposition_files_scanned,
            "bounds_impact_csv_files_scanned": bounds_stats.impact_csv_files_scanned,
            "bounds_impact_parquet_tables_scanned": bounds_stats.impact_parquet_tables_scanned,
            "bounds_input_rows_scanned": bounds_stats.total_rows_scanned,
            "trajectory_rows_per_second": safe_rate_or_none(
                trajectory_sample_rows,
                timings.trajectory_accumulation_seconds,
            ),
            "deposition_rows_per_second": safe_rate_or_none(
                deposition_rows,
                timings.deposition_accumulation_seconds,
            ),
            "impact_rows_per_second": safe_rate_or_none(
                impact_rows,
                timings.impact_accumulation_seconds,
            ),
            "hazard_input_rows_per_second": safe_rate_or_none(
                total_hazard_input_rows,
                accumulation_seconds,
            ),
            "output_file_count": output_file_count,
            "output_bytes": output_bytes,
        },
        "warnings": warnings,
        "grid": dict(metadata.get("grid", {}), source=grid_source),
        "raster_exports": metadata.get("raster_exports", {}),
        "inputs": metadata.get("inputs", {}),
        "input_artifacts": input_artifact_identities(
            case=case,
            diagnostics_path=diagnostics.get("_path"),
            trajectory_paths=metadata.get("_trajectory_paths", []),
            deposition_path=metadata.get("_deposition_path"),
            impact_event_paths=metadata.get("_impact_event_paths", []),
            impact_event_parquet_paths=metadata.get("_impact_event_parquet_paths", []),
        ),
        "hazard_statistics": {
            "configured": statistic_config.as_dict(),
            "generated_layer_names": [layer.key for layer in layers if "exceedance" in layer.key],
        },
        "hazard_probability": (
            probability.as_manifest([layer.key for layer in layers if layer.key.startswith("weighted_")])
            if probability
            else None
        ),
        "hazard_map_package": hazard_map_package_manifest_section(map_package, probability) if map_package else None,
        "layer_semantics": layer_semantics,
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


def hazard_terrain_manifest(case: dict[str, Any], warnings: list[str]) -> dict[str, Any]:
    terrain = case.get("terrain") or {}
    parameters = terrain.get("parameters") or {}
    manifest: dict[str, Any] = {
        "terrain_type": terrain.get("type"),
        "path": terrain.get("path"),
        "metadata_path": terrain.get("metadata_path"),
        "crs": None,
        "epsg": None,
        "vertical_datum": None,
        "resolution_m": parameters.get("cell_size_m") or parameters.get("cellsize"),
        "extent": None,
        "nodata": None,
        "source_dataset": None,
        "source_product": None,
        "source_filename": None,
        "license": None,
        "processed_sha256": None,
    }
    metadata_path_text = terrain.get("metadata_path")
    if not metadata_path_text:
        return manifest

    metadata_path = ROOT / str(metadata_path_text)
    if not metadata_path.exists():
        warnings.append(f"terrain metadata file not found for hazard manifest: {metadata_path_text}")
        return manifest

    try:
        metadata = load_yaml(metadata_path)
    except Exception as exc:  # pragma: no cover - defensive provenance path
        warnings.append(f"terrain metadata could not be read for hazard manifest: {metadata_path_text}: {exc}")
        return manifest

    crs = metadata.get("coordinate_reference_system") or {}
    raster = metadata.get("raster") or {}
    preprocessing = metadata.get("preprocessing") or {}
    manifest.update(
        {
            "crs": crs.get("horizontal_name"),
            "epsg": crs.get("epsg"),
            "vertical_datum": crs.get("vertical_datum"),
            "resolution_m": raster.get("resolution_m") or manifest["resolution_m"],
            "extent": metadata.get("extent_lv95_m") or preprocessing.get("crop_extent_lv95_m"),
            "nodata": raster.get("nodata"),
            "source_dataset": metadata.get("source_dataset"),
            "source_product": metadata.get("source_product"),
            "source_filename": metadata.get("source_filename"),
            "license": metadata.get("license"),
            "processed_sha256": preprocessing.get("processed_sha256"),
        }
    )
    return manifest


def output_manifest_entry(path: Path, kind: str, format_name: str) -> dict[str, Any]:
    return {
        "kind": kind,
        "format": format_name,
        "path": str(path),
        "file_count": 1,
        "total_bytes": path.stat().st_size if path.exists() else 0,
        "sha256": sha256_file(path) if path.exists() and path.is_file() else None,
        "row_count": None,
        "skipped_empty_files": None,
    }


def geotiff_output_manifest_entry(path: Path, layer: RasterLayer, grid: GridSpec, case: dict[str, Any]) -> dict[str, Any]:
    entry = output_manifest_entry(path, "hazard_layer", "geotiff")
    spatial_reference = geotiff_spatial_reference(case, grid)
    entry.update(
        {
            "layer_name": layer.key,
            "export_format": "GeoTIFF",
            "compression": "none",
            "cloud_optimized": False,
            "cog": False,
            "raster": {
                "crs": spatial_reference.get("crs"),
                "epsg": spatial_reference.get("epsg"),
                "vertical_datum": spatial_reference.get("vertical_datum"),
                "affine_transform": spatial_reference["affine_transform"],
                "nodata": NODATA,
                "ncols": grid.ncols,
                "nrows": grid.nrows,
                "cell_size_m": grid.cell_size,
                "extent": {
                    "xmin_m": grid.xmin,
                    "ymin_m": grid.ymin,
                    "xmax_m": grid.xmax,
                    "ymax_m": grid.ymax,
                },
                "cloud_optimized": False,
                "cog": False,
                "compression": "none",
            },
            "probability_semantics": {
                "weighted": layer.key.startswith("weighted_"),
                "annualized": False,
                "is_annualized": False,
            },
        }
    )
    return entry


def geotiff_raster_outputs(outputs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    raster_outputs = []
    for output in outputs:
        if output.get("format") != "geotiff":
            continue
        raster_outputs.append(
            {
                "layer_name": output.get("layer_name"),
                "format": output.get("format"),
                "path": output.get("path"),
                "sha256": output.get("sha256"),
                "total_bytes": output.get("total_bytes"),
                "cloud_optimized": bool((output.get("raster") or {}).get("cloud_optimized", False)),
                "annualized": False,
                "is_annualized": False,
            }
        )
    return raster_outputs


def input_artifact_identities(
    *,
    case: dict[str, Any],
    diagnostics_path: str | None,
    trajectory_paths: list[str],
    deposition_path: str | None,
    impact_event_paths: list[str],
    impact_event_parquet_paths: list[str],
) -> list[dict[str, Any]]:
    artifacts: list[dict[str, Any]] = []
    if case.get("_path"):
        artifacts.append(input_artifact_entry(Path(case["_path"]), "case", "yaml"))
    if diagnostics_path:
        artifacts.append(input_artifact_entry(Path(diagnostics_path), "diagnostics", "json"))
    artifacts.append(input_artifact_collection(trajectory_paths, "trajectory_samples", "csv_collection"))
    if deposition_path:
        artifacts.append(input_artifact_entry(Path(deposition_path), "deposition_points", "csv"))
    artifacts.append(input_artifact_collection(impact_event_paths, "impact_events", "csv_collection"))
    artifacts.append(input_artifact_collection(impact_event_parquet_paths, "impact_events", "parquet_collection"))
    return [artifact for artifact in artifacts if artifact["file_count"] > 0]


def input_artifact_entry(path: Path, kind: str, format_name: str) -> dict[str, Any]:
    if not path.exists() or not path.is_file():
        return {
            "kind": kind,
            "format": format_name,
            "path": str(path),
            "file_count": 0,
            "total_bytes": 0,
            "sha256": None,
        }
    return {
        "kind": kind,
        "format": format_name,
        "path": str(path),
        "file_count": 1,
        "total_bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def input_artifact_collection(paths: list[str], kind: str, format_name: str) -> dict[str, Any]:
    existing = [Path(path) for path in paths if Path(path).exists() and Path(path).is_file()]
    digest = hashlib.sha256()
    total_bytes = 0
    members: list[dict[str, Any]] = []
    for path in sorted(existing, key=lambda item: str(item)):
        file_hash = sha256_file(path)
        size = path.stat().st_size
        total_bytes += size
        members.append(
            {
                "path": str(path),
                "total_bytes": size,
                "sha256": file_hash,
            }
        )
        digest.update(str(path).encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(size).encode("ascii"))
        digest.update(b"\0")
        digest.update(file_hash.encode("ascii"))
        digest.update(b"\n")
    return {
        "kind": kind,
        "format": format_name,
        "file_count": len(existing),
        "total_bytes": total_bytes,
        "sha256": digest.hexdigest() if existing else None,
        "path_hash_policy": "sha256 over sorted member path, byte size, and file sha256",
        "members": members
        if len(members) <= INPUT_ARTIFACT_COLLECTION_MEMBER_LIMIT
        else members[:INPUT_ARTIFACT_COLLECTION_MEMBER_LIMIT],
        "members_truncated": len(members) > INPUT_ARTIFACT_COLLECTION_MEMBER_LIMIT,
    }


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def layer_source(layer_key: str) -> str:
    if layer_key in {
        "reach_probability",
        "weighted_reach_probability",
        "max_kinetic_energy",
        "max_jump_height",
    } or "exceedance" in layer_key:
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
        if layer.key in {
            "reach_probability",
            "weighted_reach_probability",
            "deposition_density",
            "significant_impact_density",
        } or "exceedance" in layer.key:
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
    geotiff_enabled = bool((metadata.get("raster_exports") or {}).get("geotiff"))
    for layer in layers:
        summary = next(
            (entry.get("summary", {}) for entry in metadata.get("layers", []) if entry.get("key") == layer.key),
            {},
        )
        files = (
            f"<a href=\"{prefix}_{layer.key}.csv\">CSV grid</a> | "
            f"<a href=\"{prefix}_{layer.key}.asc\">ASCII grid</a>"
        )
        if geotiff_enabled:
            files += f" | <a href=\"{prefix}_{layer.key}.tif\">GeoTIFF</a>"
        rows.append(
            "<tr>"
            f"<td>{html.escape(layer.title)}</td>"
            f"<td>{html.escape(layer.units)}</td>"
            f"<td>{files}</td>"
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
