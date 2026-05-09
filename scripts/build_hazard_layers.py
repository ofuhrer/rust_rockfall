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
import os
import html
import json
import math
import socket
import struct
import time
from io import TextIOBase
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


ROOT = Path(__file__).resolve().parents[1]
NODATA = -9999.0
SIGNIFICANT_IMPACT_MIN_NORMAL_SPEED_MPS = 0.05
INPUT_ARTIFACT_COLLECTION_MEMBER_LIMIT = 32
CHUNK_MANIFEST_SCHEMA_VERSION = "hazard_reducer_chunk_manifest_v1"
CHUNK_EXECUTION_MANIFEST_SCHEMA_VERSION = "chunk_execution_manifest_v1"
CHUNK_EXECUTION_PLAN_SCHEMA_VERSION = "execution_plan_v1"
CHUNK_PARTIAL_STATE_SCHEMA_VERSION = "reducer_chunk_state_v1"
CHUNK_EXECUTION_INDEX_SCHEMA_VERSION = "reducer_execution_index_v1"
CHUNK_MERGE_STATE_SCHEMA_VERSION = "reducer_merge_state_v1"
CHUNK_REDUCTION_MAX_ATTEMPTS = 3
CHUNK_CLAIM_TTL_SECONDS = 60 * 60


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
class ConditionalCurveRow:
    row: int
    col: int
    x_center_m: float
    y_center_m: float
    intensity_measure: str
    threshold: float
    threshold_units: str
    layer_name: str
    probability_mode: str
    normalization_scope: str
    numerator: float
    denominator: float
    conditional_fraction: float
    standard_error: float | None
    weighted: bool
    annualized: bool = False


@dataclass(frozen=True)
class ConditionalCurveExportConfig:
    mode: str = "full"

    @property
    def write_table(self) -> bool:
        return self.mode == "full"

    def as_metadata(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "csv_table_written": self.write_table,
            "annualized": False,
        }


@dataclass(frozen=True)
class HazardStatisticConfig:
    kinetic_energy_exceedance_j: tuple[float, ...] = ()
    jump_height_exceedance_m: tuple[float, ...] = ()
    velocity_exceedance_mps: tuple[float, ...] = ()
    probability_standard_error: bool = False

    @property
    def enabled(self) -> bool:
        return bool(
            self.kinetic_energy_exceedance_j
            or self.jump_height_exceedance_m
            or self.velocity_exceedance_mps
            or self.probability_standard_error
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "kinetic_energy_exceedance_j": list(self.kinetic_energy_exceedance_j),
            "jump_height_exceedance_m": list(self.jump_height_exceedance_m),
            "velocity_exceedance_mps": list(self.velocity_exceedance_mps),
            "probability_standard_error": self.probability_standard_error,
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
    grid_csv_export: str = "full"

    @property
    def enabled(self) -> bool:
        return self.geotiff

    def as_metadata(self) -> dict[str, Any]:
        formats = ["esri_ascii_grid"]
        if self.grid_csv_export == "full":
            formats.insert(0, "csv_grid")
        if self.geotiff:
            formats.append("geotiff")
        return {
            "geotiff": self.geotiff,
            "cog": self.cog,
            "compression": self.compression if self.geotiff else None,
            "grid_csv_export": self.grid_csv_export,
            "formats": formats,
        }


@dataclass(frozen=True)
class PilotGisPackageConfig:
    package_manifest_json: Path | None = None
    visual_qa_status: str = "not-run"
    visual_qa_note: str = "Manual GIS/QGIS inspection has not been run for this generated package."
    reviewed_artifacts: tuple[str, ...] = ()
    source_zone_context_paths: tuple[Path, ...] = ()


@dataclass(frozen=True)
class InputStats:
    trajectory_count: int = 0
    trajectory_sample_count: int = 0
    deposition_point_count: int = 0
    impact_event_count: int = 0
    significant_impact_count: int = 0


@dataclass(frozen=True)
class ReducerChunk:
    chunk_id: str
    index: int
    trajectory_start: int
    trajectory_end_exclusive: int
    trajectory_paths: tuple[Path, ...]
    deposition_path: Path | None
    impact_csv_start: int
    impact_csv_end_exclusive: int
    impact_event_paths: tuple[Path, ...]
    impact_parquet_start: int
    impact_parquet_end_exclusive: int
    impact_event_parquet_paths: tuple[Path, ...]


@dataclass(frozen=True)
class ReducerChunkResult:
    chunk: ReducerChunk
    accumulator: "HazardAccumulator"
    warnings: tuple[str, ...]
    partial_state_path: Path | None
    manifest: dict[str, Any]


def chunk_manifest_path(output_dir: Path, chunk_id: str) -> Path:
    return output_dir / f"{chunk_id}_manifest.json"


def chunk_partial_state_path(chunk_id: str, output_dir: Path) -> Path:
    return output_dir / f"{chunk_id}_state.json"


def execution_index_path(output_dir: Path, prefix: str) -> Path:
    return output_dir / f"{prefix}_reducer_execution_index_v1.json"


def merge_state_path(output_dir: Path, prefix: str) -> Path:
    return output_dir / f"{prefix}_reducer_merge_state_v1.json"


def chunk_ownership_state(state: str, owner_id: str | None = None) -> dict[str, Any]:
    return {
        "state": state,
        "owner_id": owner_id,
        "claimed_at_unix_s": None,
        "lease_expires_unix_s": None,
        "released_at_unix_s": None,
        "release_reason": None,
        "updated_unix_s": int(time.time()),
    }


def claim_chunk(record: dict[str, Any], owner_id: str | None, now_unix_s: int, lease_seconds: int) -> dict[str, Any]:
    ownership = chunk_ownership_state("claimed", owner_id)
    ownership["claimed_at_unix_s"] = now_unix_s
    ownership["lease_expires_unix_s"] = now_unix_s + max(1, lease_seconds)
    record["ownership"] = ownership
    return ownership


def release_chunk(
    record: dict[str, Any],
    owner_id: str | None,
    now_unix_s: int,
    *,
    completion_status: str,
    execution_status: str,
    reason: str,
    attempt_count: int,
    retry_count: int,
) -> None:
    ownership = chunk_ownership_state("released", owner_id)
    current_ownership = record.get("ownership") or {}
    ownership["claimed_at_unix_s"] = int(current_ownership.get("claimed_at_unix_s") or now_unix_s)
    ownership["lease_expires_unix_s"] = int(current_ownership.get("lease_expires_unix_s") or now_unix_s)
    ownership["released_at_unix_s"] = now_unix_s
    ownership["release_reason"] = reason
    ownership["updated_unix_s"] = now_unix_s
    record["ownership"] = ownership
    record["attempt_count"] = attempt_count
    record["retry_count"] = retry_count
    record["execution_status"] = execution_status
    record["completion_status"] = completion_status


def mark_chunk_stale_release(record: dict[str, Any], now_unix_s: int) -> None:
    current_ownership = record.get("ownership") or {}
    ownership = chunk_ownership_state("stale", current_ownership.get("owner_id"))
    ownership["claimed_at_unix_s"] = current_ownership.get("claimed_at_unix_s")
    ownership["lease_expires_unix_s"] = current_ownership.get("lease_expires_unix_s")
    ownership["released_at_unix_s"] = now_unix_s
    ownership["release_reason"] = "stale_claim"
    ownership["updated_unix_s"] = now_unix_s
    record["ownership"] = ownership


def chunk_input_signature(chunk: ReducerChunk) -> str:
    payload = json.dumps(
        {
            "trajectory_start": chunk.trajectory_start,
            "trajectory_end_exclusive": chunk.trajectory_end_exclusive,
            "impact_csv_start": chunk.impact_csv_start,
            "impact_csv_end_exclusive": chunk.impact_csv_end_exclusive,
            "impact_parquet_start": chunk.impact_parquet_start,
            "impact_parquet_end_exclusive": chunk.impact_parquet_end_exclusive,
            "trajectory_files": [str(path) for path in chunk.trajectory_paths],
            "impact_csv_files": [str(path) for path in chunk.impact_event_paths],
            "impact_parquet_files": [str(path) for path in chunk.impact_event_parquet_paths],
            "deposition_path": str(chunk.deposition_path) if chunk.deposition_path is not None else None,
        },
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def is_stale_claim(record: dict[str, Any], now_unix_s: int) -> bool:
    ownership = record.get("ownership")
    if not isinstance(ownership, dict):
        return False
    claimed_at = ownership.get("claimed_at_unix_s")
    lease_expires = ownership.get("lease_expires_unix_s")
    if not isinstance(claimed_at, int) or not isinstance(lease_expires, int):
        return False
    if lease_expires < now_unix_s:
        return True
    return False


def is_claim_active_for_other_owner(
    record: dict[str, Any],
    owner_id: str | None,
    now_unix_s: int,
) -> bool:
    ownership = record.get("ownership")
    if not isinstance(ownership, dict):
        return False
    owner = ownership.get("owner_id")
    state = ownership.get("state")
    if owner == owner_id:
        return False
    if state != "claimed":
        return False
    if is_stale_claim(record, now_unix_s):
        return False
    return True


def chunk_has_valid_reusable_state(
    chunk: ReducerChunk,
    record: dict[str, Any],
) -> bool:
    if record.get("completion_status") != "completed":
        return False
    if not isinstance(record.get("input_signature"), str):
        return False
    expected_signature = record["input_signature"]
    if expected_signature != chunk_input_signature(chunk):
        return False
    state_path = Path(str(record.get("partial_state_path"))) if record.get("partial_state_path") else None
    if state_path is None or not state_path.exists():
        return False
    try:
        state = read_json(state_path)
    except (OSError, json.JSONDecodeError, ValueError):
        return False
    return (
        isinstance(state, dict)
        and state.get("schema_version") == CHUNK_PARTIAL_STATE_SCHEMA_VERSION
        and state.get("chunk_id") == chunk.chunk_id
        and state.get("input_signature") == expected_signature
    )


def stable_owner_id(prefix: str | None) -> str:
    base = prefix or "reducer"
    return f"{socket.gethostname()}:{os.getpid()}:{base}"


def execution_plan_path(output_dir: Path, prefix: str) -> Path:
    return output_dir / f"{prefix}_execution_plan_v1.json"


def file_fingerprint(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "path": str(path),
            "status": "missing",
            "size_bytes": None,
            "sha256": None,
        }
    return {
        "path": str(path),
        "status": "present",
        "size_bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def _chunk_id_range_start(index: int, total_chunks: int, total_items: int) -> int:
    return index * total_items // total_chunks


def _chunk_id_range_end(index: int, total_chunks: int, total_items: int) -> int:
    return (index + 1) * total_items // total_chunks


def chunk_partition_ranges(total_items: int, partition_count: int) -> list[tuple[int, int]]:
    return [
        (_chunk_id_range_start(index, partition_count, total_items), _chunk_id_range_end(index, partition_count, total_items))
        for index in range(partition_count)
    ]


def build_chunk_execution_plan(
    prefix: str,
    chunks: list[ReducerChunk],
    reducer_workers: int,
    output_dir: Path,
    *,
    owner_id: str | None = None,
    scheduler_index: int = 0,
    scheduler_count: int = 1,
    max_chunk_attempts: int = CHUNK_REDUCTION_MAX_ATTEMPTS,
    lease_seconds: int = CHUNK_CLAIM_TTL_SECONDS,
) -> dict[str, Any]:
    chunk_records: list[dict[str, Any]] = []
    chunk_owner = owner_id or stable_owner_id(prefix)
    for chunk in chunks:
        signature = chunk_input_signature(chunk)
        chunk_records.append(
            {
                "chunk_id": chunk.chunk_id,
                "chunk_index": chunk.index,
                "trajectory_file_index_start": chunk.trajectory_start,
                "trajectory_file_index_end_exclusive": chunk.trajectory_end_exclusive,
                "impact_csv_file_index_start": chunk.impact_csv_start,
                "impact_csv_file_index_end_exclusive": chunk.impact_csv_end_exclusive,
                "impact_parquet_file_index_start": chunk.impact_parquet_start,
                "impact_parquet_file_index_end_exclusive": chunk.impact_parquet_end_exclusive,
                "deposition_file_count": 1 if chunk.deposition_path is not None else 0,
                "execution_status": "planned",
                "completion_status": "not_started",
                "input_signature": signature,
                "attempt_count": 0,
                "retry_count": 0,
                "completion_reason": None,
                "manifest_path": str(chunk_manifest_path(output_dir / "chunks", chunk.chunk_id)),
                "partial_state_path": str(chunk_partial_state_path(chunk.chunk_id, output_dir / "chunks")),
                "partial_state_schema_version": CHUNK_PARTIAL_STATE_SCHEMA_VERSION,
                "ownership": chunk_ownership_state("unclaimed", None),
                "input_artifacts": [
                    file_fingerprint(path)
                    for path in (
                        *chunk.trajectory_paths,
                        *chunk.impact_event_paths,
                        *chunk.impact_event_parquet_paths,
                    )
                    if path
                ]
                + ([file_fingerprint(chunk.deposition_path)] if chunk.deposition_path is not None else []),
            }
        )
    plan_id_source = json.dumps(
        {
            "prefix": prefix,
            "reducer_workers": reducer_workers,
            "chunk_ids": [chunk.chunk_id for chunk in chunks],
            "chunking_signature": [
                {
                    "trajectory_start": chunk.trajectory_start,
                    "trajectory_end_exclusive": chunk.trajectory_end_exclusive,
                    "impact_csv_start": chunk.impact_csv_start,
                    "impact_csv_end_exclusive": chunk.impact_csv_end_exclusive,
                    "impact_parquet_start": chunk.impact_parquet_start,
                    "impact_parquet_end_exclusive": chunk.impact_parquet_end_exclusive,
                }
                for chunk in chunks
            ],
            "artifact_inventory": [
                input_artifact["sha256"]
                for chunk_record in chunk_records
                for input_artifact in chunk_record["input_artifacts"]
            ],
        },
        sort_keys=True,
    ).encode("utf-8")
    digest = hashlib.sha256(plan_id_source).hexdigest()[:24]
    plan_id = f"{prefix}__execution_plan__{digest}"
    return {
        "schema_version": CHUNK_EXECUTION_PLAN_SCHEMA_VERSION,
        "plan_id": plan_id,
        "plan_status": "planned",
        "created_unix_s": int(datetime.now(timezone.utc).timestamp()),
        "reducer_mode": "chunked_local_threads",
        "merge_order": "sorted_chunk_id",
        "merge_group_id": digest,
        "reducer_workers": reducer_workers,
        "chunk_count": len(chunks),
        "owner_id": chunk_owner,
        "scheduler_index": scheduler_index,
        "scheduler_count": scheduler_count,
        "max_chunk_attempts": max_chunk_attempts,
        "claim_ttl_seconds": lease_seconds,
        "chunk_id_policy": "stable_prefix_sorted_chunk_index",
        "chunk_manifests": chunk_records,
        "output_manifest_path": str(execution_plan_path(output_dir, prefix)),
        "output_artifacts": {
            "schema_version": CHUNK_EXECUTION_PLAN_SCHEMA_VERSION,
            "path": str(execution_plan_path(output_dir, prefix)),
        },
    }


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
    trajectory_id: str | None
    properties: dict[str, float | str]


@dataclass(frozen=True)
class DepositionPointBatch:
    points: tuple[DepositionPoint, ...]


@dataclass(frozen=True)
class SignificantImpactPoint:
    x_m: float
    y_m: float
    trajectory_id: str | None


@dataclass(frozen=True)
class ImpactEventBatch:
    source_path: Path
    event_count: int
    significant_event_count: int
    significant_points: tuple[SignificantImpactPoint, ...]


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
        self.weighted_deposition = zeros(grid) if probability else None
        self.impact_density = zeros(grid)
        self.weighted_impact_density = zeros(grid) if probability else None
        self.weighted_significant_impact_weight = 0.0
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
                if self.weighted_deposition is not None:
                    if not point.trajectory_id:
                        raise SystemExit(
                            "sampling-weighted deposition density requires trajectory_id in deposition CSV"
                        )
                    if point.trajectory_id in self.probability.weights:
                        self.weighted_deposition[cell[0]][cell[1]] += self.probability.weight_for_trajectory(
                            point.trajectory_id
                        )

    def accumulate_impacts(self, batch: ImpactEventBatch) -> None:
        self.impact_event_count += batch.event_count
        self.significant_impact_count += batch.significant_event_count
        for point in batch.significant_points:
            if self.weighted_impact_density is not None:
                if not point.trajectory_id:
                    raise SystemExit(
                        "sampling-weighted significant impact density requires trajectory_id in impact-event input"
                    )
                if point.trajectory_id in self.probability.weights:
                    self.weighted_significant_impact_weight += self.probability.weight_for_trajectory(
                        point.trajectory_id
                    )
            cell = self.grid.cell(point.x_m, point.y_m)
            if cell is not None:
                self.impact_density[cell[0]][cell[1]] += 1.0
                if (
                    self.weighted_impact_density is not None
                    and point.trajectory_id
                    and point.trajectory_id in self.probability.weights
                ):
                    self.weighted_impact_density[cell[0]][cell[1]] += self.probability.weight_for_trajectory(
                        point.trajectory_id
                    )

    def merge(self, other: "HazardAccumulator") -> None:
        add_grid_into(self.reach, other.reach)
        merge_max_grid_into(self.max_ke, other.max_ke)
        merge_max_grid_into(self.max_jump, other.max_jump)
        add_threshold_grids_into(self.kinetic_exceedance, other.kinetic_exceedance)
        add_threshold_grids_into(self.jump_exceedance, other.jump_exceedance)
        add_threshold_grids_into(self.velocity_exceedance, other.velocity_exceedance)
        add_grid_into(self.deposition, other.deposition)
        add_grid_into(self.impact_density, other.impact_density)
        if self.weighted_reach is not None and other.weighted_reach is not None:
            add_grid_into(self.weighted_reach, other.weighted_reach)
        add_threshold_grids_into(self.weighted_kinetic_exceedance, other.weighted_kinetic_exceedance)
        add_threshold_grids_into(self.weighted_jump_exceedance, other.weighted_jump_exceedance)
        add_threshold_grids_into(self.weighted_velocity_exceedance, other.weighted_velocity_exceedance)
        if self.weighted_deposition is not None and other.weighted_deposition is not None:
            add_grid_into(self.weighted_deposition, other.weighted_deposition)
        if self.weighted_impact_density is not None and other.weighted_impact_density is not None:
            add_grid_into(self.weighted_impact_density, other.weighted_impact_density)
        self.weighted_significant_impact_weight += other.weighted_significant_impact_weight
        self.deposition_points.extend(other.deposition_points)
        self.trajectory_count += other.trajectory_count
        self.trajectory_sample_count += other.trajectory_sample_count
        self.deposition_point_count += other.deposition_point_count
        self.impact_event_count += other.impact_event_count
        self.significant_impact_count += other.significant_impact_count
        self.warnings.extend(other.warnings)
        self.terrain_warning_emitted = self.terrain_warning_emitted or other.terrain_warning_emitted

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
            reach_standard_error = (
                binomial_standard_error_grid(self.reach, self.trajectory_count)
                if self.statistics.probability_standard_error
                else None
            )
            reach = scaled_grid(self.reach, 1.0 / self.trajectory_count)
            layers.append(
                RasterLayer(
                    "reach_probability",
                    "Reach probability",
                    "fraction of supplied trajectories",
                    reach,
                    note="Cells touched by each supplied trajectory, normalized by the number of trajectory CSVs.",
                )
            )
            if reach_standard_error is not None:
                layers.append(
                    RasterLayer(
                        "reach_probability_standard_error",
                        "Reach probability standard error",
                        "standard error of trajectory fraction",
                        reach_standard_error,
                        note=(
                            "Binomial standard error sqrt(p(1-p)/n) for unweighted trajectory-level "
                            "reach probability, using supplied trajectory count n."
                        ),
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
                    weighted_reach = scaled_grid(self.weighted_reach, 1.0 / denominator)
                    layers.append(
                        RasterLayer(
                            "weighted_reach_probability",
                            "Weighted reach probability",
                            "sampling-weighted fraction of filtered trajectories",
                            weighted_reach,
                            note=(
                                "Sampling-weighted conditional reach probability using "
                                "trajectory_metadata_table_v1 and normalization conditioned on filters."
                            ),
                        )
                    )
            for threshold, values in self.kinetic_exceedance.items():
                standard_error = (
                    binomial_standard_error_grid(values, self.trajectory_count)
                    if self.statistics.probability_standard_error
                    else None
                )
                scaled_values = scaled_grid(values, 1.0 / self.trajectory_count)
                layer_key = exceedance_layer_key("kinetic_energy_exceedance", threshold, "j")
                layers.append(
                    RasterLayer(
                        layer_key,
                        f"Kinetic energy exceedance >= {threshold:g} J",
                        "fraction of supplied trajectories",
                        scaled_values,
                        note=(
                            "Trajectory-level exceedance probability: a cell is counted once per "
                            f"trajectory if kinetic_j >= {threshold:g} J in that cell."
                        ),
                    )
                )
                if standard_error is not None:
                    layers.append(
                        RasterLayer(
                            f"{layer_key}_standard_error",
                            f"Kinetic energy exceedance >= {threshold:g} J standard error",
                            "standard error of trajectory fraction",
                            standard_error,
                            note=(
                                "Binomial standard error sqrt(p(1-p)/n) for the unweighted "
                                "trajectory-level exceedance probability."
                            ),
                    )
                )
            for threshold, values in self.weighted_kinetic_exceedance.items():
                scaled_values = scaled_grid(values, 1.0 / self.probability.total_filtered_weight)
                layers.append(
                    RasterLayer(
                        exceedance_layer_key("weighted_kinetic_energy_exceedance", threshold, "j"),
                        f"Weighted kinetic energy exceedance >= {threshold:g} J",
                        "sampling-weighted fraction of filtered trajectories",
                        scaled_values,
                        note=(
                            "Sampling-weighted trajectory-level exceedance probability: a cell is counted once per "
                            f"trajectory if kinetic_j >= {threshold:g} J in that cell."
                        ),
                    )
                )
            for threshold, values in self.jump_exceedance.items():
                standard_error = (
                    binomial_standard_error_grid(values, self.trajectory_count)
                    if self.statistics.probability_standard_error
                    else None
                )
                scaled_values = scaled_grid(values, 1.0 / self.trajectory_count)
                layer_key = exceedance_layer_key("jump_height_exceedance", threshold, "m")
                layers.append(
                    RasterLayer(
                        layer_key,
                        f"Jump height exceedance >= {threshold:g} m",
                        "fraction of supplied trajectories",
                        scaled_values,
                        note=(
                            "Trajectory-level exceedance probability: a cell is counted once per "
                            f"trajectory if jump height >= {threshold:g} m in that cell."
                        ),
                    )
                )
                if standard_error is not None:
                    layers.append(
                        RasterLayer(
                            f"{layer_key}_standard_error",
                            f"Jump height exceedance >= {threshold:g} m standard error",
                            "standard error of trajectory fraction",
                            standard_error,
                            note=(
                                "Binomial standard error sqrt(p(1-p)/n) for the unweighted "
                                "trajectory-level exceedance probability."
                            ),
                    )
                )
            for threshold, values in self.weighted_jump_exceedance.items():
                scaled_values = scaled_grid(values, 1.0 / self.probability.total_filtered_weight)
                layers.append(
                    RasterLayer(
                        exceedance_layer_key("weighted_jump_height_exceedance", threshold, "m"),
                        f"Weighted jump height exceedance >= {threshold:g} m",
                        "sampling-weighted fraction of filtered trajectories",
                        scaled_values,
                        note=(
                            "Sampling-weighted trajectory-level exceedance probability: a cell is counted once per "
                            f"trajectory if jump height >= {threshold:g} m in that cell."
                        ),
                    )
                )
            for threshold, values in self.velocity_exceedance.items():
                standard_error = (
                    binomial_standard_error_grid(values, self.trajectory_count)
                    if self.statistics.probability_standard_error
                    else None
                )
                scaled_values = scaled_grid(values, 1.0 / self.trajectory_count)
                layer_key = exceedance_layer_key("velocity_exceedance", threshold, "mps")
                layers.append(
                    RasterLayer(
                        layer_key,
                        f"Velocity exceedance >= {threshold:g} m/s",
                        "fraction of supplied trajectories",
                        scaled_values,
                        note=(
                            "Trajectory-level exceedance probability: a cell is counted once per "
                            f"trajectory if speed_mps >= {threshold:g} m/s in that cell."
                        ),
                    )
                )
                if standard_error is not None:
                    layers.append(
                        RasterLayer(
                            f"{layer_key}_standard_error",
                            f"Velocity exceedance >= {threshold:g} m/s standard error",
                            "standard error of trajectory fraction",
                            standard_error,
                            note=(
                                "Binomial standard error sqrt(p(1-p)/n) for the unweighted "
                                "trajectory-level exceedance probability."
                            ),
                    )
                )
            for threshold, values in self.weighted_velocity_exceedance.items():
                scaled_values = scaled_grid(values, 1.0 / self.probability.total_filtered_weight)
                layers.append(
                    RasterLayer(
                        exceedance_layer_key("weighted_velocity_exceedance", threshold, "mps"),
                        f"Weighted velocity exceedance >= {threshold:g} m/s",
                        "sampling-weighted fraction of filtered trajectories",
                        scaled_values,
                        note=(
                            "Sampling-weighted trajectory-level exceedance probability: a cell is counted once per "
                            f"trajectory if speed_mps >= {threshold:g} m/s in that cell."
                        ),
                    )
                )
        else:
            warnings.append("no trajectory CSVs supplied; reach, energy, and jump-height layers were not created")

        if self.deposition_point_count:
            deposition = scaled_grid(self.deposition, 1.0 / self.deposition_point_count)
            layers.append(
                RasterLayer(
                    "deposition_density",
                    "Deposition density",
                    "fraction of deposition points",
                    deposition,
                    note="Final-position density from ensemble deposition CSV.",
                )
            )
            if self.weighted_deposition is not None:
                denominator = self.probability.total_filtered_weight
                if denominator <= 0.0:
                    raise SystemExit("filtered total sampling weight must be positive")
                weighted_deposition = scaled_grid(self.weighted_deposition, 1.0 / denominator)
                layers.append(
                    RasterLayer(
                        "weighted_deposition_density",
                        "Weighted deposition density",
                        "sampling-weighted fraction of filtered trajectories",
                        weighted_deposition,
                        note=(
                            "Sampling-weighted conditional final-position density using "
                            "trajectory_metadata_table_v1 and normalization conditioned on filters."
                        ),
                    )
                )
        else:
            warnings.append("no ensemble deposition CSV supplied; deposition density layer was not created")

        if self.impact_event_count:
            if self.significant_impact_count:
                impact_density = scaled_grid(self.impact_density, 1.0 / self.significant_impact_count)
            else:
                impact_density = copy_grid(self.impact_density)
            layers.append(
                RasterLayer(
                    "significant_impact_density",
                    "Significant impact density",
                    "fraction of significant impact events",
                    impact_density,
                    note=f"Significant impacts use incoming_normal_speed_mps >= {SIGNIFICANT_IMPACT_MIN_NORMAL_SPEED_MPS:g} m/s.",
                )
            )
            if self.weighted_impact_density is not None:
                if self.weighted_significant_impact_weight > 0.0:
                    weighted_impact_density = scaled_grid(
                        self.weighted_impact_density,
                        1.0 / self.weighted_significant_impact_weight,
                    )
                    layers.append(
                        RasterLayer(
                            "weighted_significant_impact_density",
                            "Weighted significant impact density",
                            "sampling-weighted fraction of significant impact events",
                            weighted_impact_density,
                            note=(
                                "Sampling-weighted significant-impact event density using trajectory_id and "
                                "normalization by the filtered significant-impact event weight sum."
                            ),
                        )
                    )
                elif self.significant_impact_count:
                    warnings.append(
                        "weighted significant impact density was not created because filters left no significant impact events"
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
    parser.add_argument(
        "--probability-standard-error",
        action="store_true",
        help=(
            "add binomial standard-error rasters for unweighted trajectory-level "
            "reach and exceedance probability layers"
        ),
    )
    parser.add_argument(
        "--conditional-curve-export",
        choices=["full", "summary-only"],
        help=(
            "conditional intensity-exceedance curve export mode; full writes the "
            "per-cell CSV table, summary-only records metadata without writing "
            "the large curve table"
        ),
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
        "--grid-csv-export",
        choices=["full", "none"],
        default=None,
        help="control hazard CSV-grid output volume; full writes csv_grid files, none suppresses them",
    )
    parser.add_argument(
        "--export-cog",
        action="store_true",
        help="reserved for future Cloud-Optimized GeoTIFF export; currently fails rather than writing non-COG TIFFs",
    )
    parser.add_argument(
        "--pilot-gis-package",
        action="store_true",
        help="write a diagnostic pilot GIS package manifest for GeoTIFF/QGIS review artifacts",
    )
    parser.add_argument(
        "--pilot-gis-package-manifest-json",
        type=Path,
        help="optional output path for pilot_gis_package_manifest_v1; defaults next to the hazard manifest",
    )
    parser.add_argument(
        "--pilot-gis-qa-status",
        choices=["pass", "no-go", "inconclusive", "not-run"],
        help="manual GIS/QGIS visual QA status recorded in the pilot package manifest",
    )
    parser.add_argument(
        "--pilot-gis-qa-note",
        help="manual GIS/QGIS visual QA note recorded in the pilot package manifest",
    )
    parser.add_argument(
        "--reducer-workers",
        type=int,
        default=1,
        help=(
            "opt-in deterministic local chunk reducer worker count; values above 1 "
            "partition input files and merge partial reducers by chunk id"
        ),
    )
    parser.add_argument(
        "--scheduler-index",
        type=int,
        default=0,
        help=(
            "deterministic scheduler partition index for cross-process chunk execution; "
            "defaults to 0 when scheduler-count is 1"
        ),
    )
    parser.add_argument(
        "--scheduler-count",
        type=int,
        default=1,
        help="deterministic scheduler partition count for cross-process chunk execution",
    )
    parser.add_argument(
        "--chunk-owner-id",
        type=str,
        default=None,
        help="optional deterministic owner label for chunk claim/release tracking",
    )
    parser.add_argument(
        "--chunk-claim-ttl-seconds",
        type=int,
        default=CHUNK_CLAIM_TTL_SECONDS,
        help="claim time-to-live window in seconds before a chunk claim becomes stale",
    )
    parser.add_argument(
        "--max-chunk-attempts",
        type=int,
        default=CHUNK_REDUCTION_MAX_ATTEMPTS,
        help="deterministic maximum claim-aware retry attempts per chunk",
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
    conditional_curve_export = parse_conditional_curve_export(case, args)
    pilot_gis_package_config = parse_pilot_gis_package(case, args, raster_export_config)

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
    (
        accumulator,
        reducer_warnings,
        reducer_execution,
        chunk_manifest_paths,
        reducer_timings,
    ) = run_reducer_accumulation(
        output_dir,
        prefix,
        grid,
        terrain,
        block_radius_m,
        statistic_config,
        probability_state,
        trajectory_paths,
        deposition_path,
        impact_event_paths,
        impact_event_parquet_paths,
        args.reducer_workers,
        owner_id=args.chunk_owner_id,
        scheduler_index=args.scheduler_index,
        scheduler_count=args.scheduler_count,
        max_chunk_attempts=args.max_chunk_attempts,
        lease_seconds=args.chunk_claim_ttl_seconds,
    )
    input_warnings.extend(reducer_warnings)
    deposition_accumulation_seconds = reducer_timings.deposition_accumulation_seconds
    trajectory_accumulation_seconds = reducer_timings.trajectory_accumulation_seconds
    impact_accumulation_seconds = reducer_timings.impact_accumulation_seconds
    stats = accumulator.stats()
    if not stats.trajectory_count and not stats.deposition_point_count and not stats.impact_event_count:
        raise SystemExit("no trajectory, deposition, or impact-event inputs found")

    normalization_started = time.perf_counter()
    layers, warnings = accumulator.layers()
    warnings = input_warnings + warnings + validate_layers(layers)
    normalization_seconds = time.perf_counter() - normalization_started
    accumulation_seconds = time.perf_counter() - accumulation_started

    output_file_metadata: dict[Path, dict[str, Any]] = {}
    output_write_kind_seconds: dict[str, float] = {
        "csv_grid": 0.0,
        "esri_ascii_grid": 0.0,
        "geotiff": 0.0,
        "csv_table": 0.0,
        "geojson": 0.0,
        "json": 0.0,
        "png": 0.0,
        "html": 0.0,
    }
    output_write_kind_bytes: dict[str, int] = {
        "csv_grid": 0,
        "esri_ascii_grid": 0,
        "geotiff": 0,
        "csv_table": 0,
        "geojson": 0,
        "json": 0,
        "png": 0,
        "html": 0,
    }
    core_write_started = time.perf_counter()
    json_serialization_seconds = 0.0
    conditional_curve_rows = build_conditional_intensity_exceedance_curves(
        grid,
        layers,
        stats,
        probability_state,
        map_package_state,
    )
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
        conditional_curve_export,
        conditional_curve_rows,
    )
    core_output_json_serialization_seconds = write_core_hazard_outputs(
        output_dir,
        prefix,
        grid,
        layers,
        accumulator.deposition_points,
        metadata,
        case,
        raster_export_config,
        conditional_curve_export,
        conditional_curve_rows,
        output_file_metadata,
        output_write_kind_seconds,
        output_write_kind_bytes,
    )
    json_serialization_seconds += core_output_json_serialization_seconds
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
        plot_paths = render_png_layers(
            output_dir,
            prefix,
            grid,
            layers,
            output_file_metadata,
            output_write_kind_seconds,
            output_write_kind_bytes,
        )
        write_html_report(
            output_dir / "index.html",
            case,
            metadata,
            layers,
            plot_paths,
            prefix,
            output_file_metadata,
            output_write_kind_seconds,
            output_write_kind_bytes,
        )
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
        conditional_curve_export,
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
        output_file_metadata=output_file_metadata,
    )
    manifest["performance"]["output_write_kind_seconds"] = {
        kind: seconds
        for kind, seconds in output_write_kind_seconds.items()
        if seconds > 0.0 or output_write_kind_bytes.get(kind, 0) > 0
    }
    manifest["performance"]["output_write_kind_bytes"] = {
        kind: bytes_count
        for kind, bytes_count in output_write_kind_bytes.items()
        if bytes_count > 0 or kind == "json"
    }
    manifest["performance"]["json_serialization_seconds"] = json_serialization_seconds
    manifest["performance"]["output_file_count"] = sum(
        int(output["file_count"]) for output in manifest["outputs"]
    )
    manifest["performance"]["output_bytes"] = sum(
        int(output["total_bytes"]) for output in manifest["outputs"]
    )
    hazard_manifest_path = output_dir / f"{prefix}_manifest.json"
    if reducer_execution is not None:
        manifest["reducer_execution"] = reducer_execution
        reducer_index_path = execution_index_path(output_dir, prefix)
        reducer_merge_state = merge_state_path(output_dir, prefix)
        manifest["outputs"].append(
            output_manifest_entry(
                execution_plan_path(output_dir, prefix),
                "reducer_execution_plan",
                "json",
                output_file_metadata=output_file_metadata,
            )
        )
        manifest["outputs"].append(
            output_manifest_entry(
                reducer_index_path,
                "reducer_execution_index",
                "json",
                output_file_metadata=output_file_metadata,
            )
        )
        manifest["outputs"].append(
            output_manifest_entry(
                reducer_merge_state,
                "reducer_merge_state",
                "json",
                output_file_metadata=output_file_metadata,
            )
        )
        for chunk_manifest_path in chunk_manifest_paths:
            manifest["outputs"].append(
                output_manifest_entry(
                    chunk_manifest_path,
                    "reducer_chunk_manifest",
                    "json",
                    output_file_metadata=output_file_metadata,
                )
            )
        manifest["performance"]["output_file_count"] = sum(
            int(output["file_count"]) for output in manifest["outputs"]
        )
        manifest["performance"]["output_bytes"] = sum(int(output["total_bytes"]) for output in manifest["outputs"])
    update_conditional_execution_manifest(
        manifest,
        grid,
        conditional_curve_export,
        reducer_execution,
        raster_export_config,
    )
    if map_package_state is not None:
        package_path = map_package_output_path(map_package_state, output_dir, prefix)
        json_serialization_seconds += write_map_package_manifest(
            package_path,
            map_package_state,
            hazard_manifest_path,
            manifest["layer_semantics"],
            geotiff_raster_outputs(manifest["outputs"]),
            output_file_metadata,
            output_write_kind_seconds,
            output_write_kind_bytes,
        )
        manifest["performance"]["json_serialization_seconds"] = json_serialization_seconds
        manifest["outputs"].append(
            output_manifest_entry(
                package_path,
                "map_package_manifest",
                "json",
                output_file_metadata=output_file_metadata,
            )
        )
    if pilot_gis_package_config is not None:
        package_path = pilot_gis_package_output_path(pilot_gis_package_config, output_dir, prefix)
        json_serialization_seconds += write_pilot_gis_package_manifest(
            package_path,
            pilot_gis_package_config,
            hazard_manifest_path,
            manifest,
            output_file_metadata,
            output_write_kind_seconds,
            output_write_kind_bytes,
        )
        manifest["performance"]["json_serialization_seconds"] = json_serialization_seconds
        manifest["outputs"].append(
            output_manifest_entry(
                package_path,
                "pilot_gis_package_manifest",
                "json",
                output_file_metadata=output_file_metadata,
            )
        )
    manifest["performance"]["output_file_count"] = sum(
        int(output["file_count"]) for output in manifest["outputs"]
    )
    manifest["performance"]["output_bytes"] = sum(int(output["total_bytes"]) for output in manifest["outputs"])
    update_conditional_execution_manifest(
        manifest,
        grid,
        conditional_curve_export,
        reducer_execution,
        raster_export_config,
    )
    manifest["performance"]["manifest_write_seconds"] = 0.0
    manifest_start = time.perf_counter()
    write_file_text(
        hazard_manifest_path,
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        "json",
        output_file_metadata,
        output_write_kind_seconds,
        output_write_kind_bytes,
        elapsed_seconds=0.0,
    )
    manifest["performance"]["manifest_write_seconds"] = time.perf_counter() - manifest_start

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
    grid_csv_export = str(args.grid_csv_export or raw.get("grid_csv_export") or "full")
    if grid_csv_export not in {"full", "none"}:
        raise SystemExit("hazard_exports.grid_csv_export must be full or none")
    return RasterExportConfig(
        geotiff=geotiff,
        cog=False,
        compression=compression,
        grid_csv_export=grid_csv_export,
    )


def parse_conditional_curve_export(
    case: dict[str, Any],
    args: argparse.Namespace,
) -> ConditionalCurveExportConfig:
    raw = case.get("conditional_curve_export") or case.get("hazard_output_volume") or {}
    if not isinstance(raw, dict):
        raise SystemExit("conditional_curve_export must be a mapping")
    mode = args.conditional_curve_export or raw.get("conditional_curve_export") or raw.get("mode") or "full"
    if mode not in {"full", "summary-only"}:
        raise SystemExit("conditional_curve_export.mode must be full or summary-only")
    return ConditionalCurveExportConfig(mode=str(mode))


def parse_pilot_gis_package(
    case: dict[str, Any],
    args: argparse.Namespace,
    raster_exports: RasterExportConfig,
) -> PilotGisPackageConfig | None:
    raw = case.get("pilot_gis_package") or {}
    if raw and not isinstance(raw, dict):
        raise SystemExit("pilot_gis_package must be a mapping")
    enabled = bool(args.pilot_gis_package) or bool(raw.get("enabled", False))
    values = {
        "package_manifest_json": args.pilot_gis_package_manifest_json or raw.get("package_manifest_json"),
        "visual_qa_status": args.pilot_gis_qa_status or raw.get("visual_qa_status") or "not-run",
        "visual_qa_note": args.pilot_gis_qa_note
        or raw.get("visual_qa_note")
        or "Manual GIS/QGIS inspection has not been run for this generated package.",
    }
    source_zone_paths = tuple(ROOT / str(path) for path in list_from_any(raw.get("source_zone_context_paths")))
    reviewed_artifacts = tuple(str(value) for value in list_from_any(raw.get("reviewed_artifacts")))
    if not enabled and not any(value is not None for value in values.values()) and not source_zone_paths and not reviewed_artifacts:
        return None
    if not enabled:
        enabled = bool(values["package_manifest_json"] or source_zone_paths or reviewed_artifacts)
    if not enabled:
        return None
    if not raster_exports.geotiff:
        raise SystemExit("pilot_gis_package requires GeoTIFF export; use --export-geotiff or hazard_exports.geotiff: true")
    visual_qa_status = str(values["visual_qa_status"])
    if visual_qa_status not in {"pass", "no-go", "inconclusive", "not-run"}:
        raise SystemExit("pilot_gis_package.visual_qa_status must be pass, no-go, inconclusive, or not-run")
    missing_context = [path for path in source_zone_paths if not path.exists()]
    if missing_context:
        raise SystemExit(
            "pilot_gis_package.source_zone_context_paths entries do not exist: "
            + ", ".join(str(path) for path in missing_context)
        )
    return PilotGisPackageConfig(
        package_manifest_json=ROOT / str(values["package_manifest_json"])
        if values["package_manifest_json"]
        else None,
        visual_qa_status=visual_qa_status,
        visual_qa_note=str(values["visual_qa_note"]),
        reviewed_artifacts=reviewed_artifacts,
        source_zone_context_paths=source_zone_paths,
    )


def build_reducer_execution_index_manifest(
    plan: dict[str, Any],
    chunk_records: list[dict[str, Any]],
    *,
    completed_chunk_count: int,
    failed_chunk_count: int,
    rerun_count: int,
    scheduled_chunk_count: int | None = None,
) -> dict[str, Any]:
    scheduled_count = scheduled_chunk_count if scheduled_chunk_count is not None else len(chunk_records)
    return {
        "schema_version": CHUNK_EXECUTION_INDEX_SCHEMA_VERSION,
        "plan_id": plan.get("plan_id"),
        "plan_path": str(plan.get("output_manifest_path") or ""),
        "plan_status": plan.get("plan_status"),
        "owner_id": plan.get("owner_id"),
        "scheduler_index": plan.get("scheduler_index"),
        "scheduler_count": plan.get("scheduler_count"),
        "merge_group_id": plan.get("merge_group_id"),
        "chunk_count": len(chunk_records),
        "scheduled_chunk_count": scheduled_count,
        "completed_chunk_count": completed_chunk_count,
        "failed_chunk_count": failed_chunk_count,
        "rerun_count": rerun_count,
        "merge_order": "sorted_chunk_id",
        "chunk_records": [
            {
                "chunk_id": record.get("chunk_id"),
                "chunk_manifest_path": record.get("manifest_path"),
                "chunk_index": record.get("chunk_index"),
                "status": record.get("status"),
                "completion_state": record.get("completion_state"),
                "execution_status": record.get("execution_status"),
                "completion_status": record.get("completion_status"),
                "completion_reason": record.get("completion_reason"),
                "failure_reason": record.get("failure_reason"),
                "ownership": record.get("ownership"),
                "timings": record.get("timings", {}),
                "row_count": record.get("row_count"),
                "rows_written": record.get("rows_written"),
                "output_bytes": record.get("output_bytes"),
                "execution_attempt": record.get("execution_attempt"),
                "retry_count": record.get("retry_count"),
                "attempt_count": record.get("attempt_count"),
                "merge_group_id": record.get("merge_group_id"),
                "input_file_counts": record.get("input_file_counts") if isinstance(record.get("input_file_counts"), dict) else None,
            }
            for record in chunk_records
        ],
    }


def build_reducer_merge_state_manifest(
    plan: dict[str, Any],
    chunk_records: list[dict[str, Any]],
) -> dict[str, Any]:
    complete_records = [record for record in chunk_records if record.get("completion_status") == "completed"]
    return {
        "schema_version": CHUNK_MERGE_STATE_SCHEMA_VERSION,
        "plan_id": plan.get("plan_id"),
        "plan_path": str(plan.get("output_manifest_path") or ""),
        "merge_group_id": plan.get("merge_group_id"),
        "merge_status": "ready" if len(complete_records) == len(chunk_records) else "incomplete",
        "status": "ready" if len(complete_records) == len(chunk_records) else "incomplete",
        "completion_state": "ready" if len(complete_records) == len(chunk_records) else "incomplete",
        "merge_order": "sorted_chunk_id",
        "merge_index": [
            {
                "chunk_id": record.get("chunk_id"),
                "chunk_manifest_path": record.get("manifest_path"),
                "partial_state_path": record.get("partial_state_path"),
                "partial_state_schema_version": record.get("partial_state_schema_version"),
                "completion_status": record.get("completion_status"),
                "completion_state": record.get("completion_state"),
                "status": record.get("status"),
                "row_count": record.get("row_count"),
                "rows_written": record.get("rows_written"),
                "output_bytes": record.get("output_bytes"),
            }
            for record in chunk_records
        ],
    }


def build_chunk_execution_manifest(
    chunk: ReducerChunk,
    accumulator: "HazardAccumulator",
    execution_plan_path: Path,
    *,
    plan_id: str | None,
    attempt_count: int,
    retry_count: int,
    execution_status: str,
    completion_status: str,
    completion_reason: str | None,
    output_bytes: int | None,
    merge_group_id: str | None = None,
    deposition_accumulation_seconds: float,
    trajectory_accumulation_seconds: float,
    impact_accumulation_seconds: float,
    partial_state_path: Path | None,
    ownership: dict[str, Any] | None = None,
) -> dict[str, Any]:
    stats = accumulator.stats()
    manifest = {
        "schema_version": CHUNK_MANIFEST_SCHEMA_VERSION,
        "chunk_id": chunk.chunk_id,
        "execution_state_schema_version": CHUNK_EXECUTION_MANIFEST_SCHEMA_VERSION,
        "status": (
            "completed"
            if completion_status == "completed"
            else "failed" if completion_status == "failed" else completion_status
        ),
        "completion_state": completion_status,
        "execution_plan": {
            "schema_version": CHUNK_EXECUTION_PLAN_SCHEMA_VERSION,
            "chunk_id": chunk.chunk_id,
            "chunk_index": chunk.index,
            "plan_id": plan_id,
            "plan_path": str(execution_plan_path),
            "plan_reference": None,
        },
        "execution_status": execution_status,
        "completion_status": completion_status,
        "completion_reason": completion_reason,
        "failure_reason": completion_reason if completion_status == "failed" else None,
        "execution_attempt": max(0, int(attempt_count)),
        "scientific_status": "not_evaluated",
        "merge_group_id": merge_group_id,
        "retry_count": max(0, int(retry_count)),
        "attempt_count": max(0, int(attempt_count)),
        "worker_partition_index": chunk.index,
        "ownership": ownership if isinstance(ownership, dict) else None,
        "input_file_indices": {
            "trajectory_file_index_start": chunk.trajectory_start,
            "trajectory_file_index_end_exclusive": chunk.trajectory_end_exclusive,
            "impact_csv_file_index_start": chunk.impact_csv_start,
            "impact_csv_file_index_end_exclusive": chunk.impact_csv_end_exclusive,
            "impact_parquet_file_index_start": chunk.impact_parquet_start,
            "impact_parquet_file_index_end_exclusive": chunk.impact_parquet_end_exclusive,
        },
        "input_file_counts": {
            "trajectory_files": len(chunk.trajectory_paths),
            "deposition_files": 1 if chunk.deposition_path is not None else 0,
            "impact_csv_files": len(chunk.impact_event_paths),
            "impact_parquet_tables": len(chunk.impact_event_parquet_paths),
        },
        "input_rows": {
            "trajectory_sample_rows": stats.trajectory_sample_count,
            "deposition_rows": stats.deposition_point_count,
            "impact_event_rows": stats.impact_event_count,
            "significant_impact_rows": stats.significant_impact_count,
        },
        "row_count": (
            stats.trajectory_sample_count
            + stats.deposition_point_count
            + stats.impact_event_count
            + stats.significant_impact_count
        ),
        "rows_written": (
            stats.trajectory_count
            + stats.deposition_point_count
            + stats.impact_event_count
            + stats.significant_impact_count
        ),
        "reducer_counts": {
            "trajectory_count": stats.trajectory_count,
            "deposition_point_count": stats.deposition_point_count,
            "impact_event_count": stats.impact_event_count,
            "significant_impact_count": stats.significant_impact_count,
        },
        "timings": {
            "deposition_accumulation_seconds": max(0.0, deposition_accumulation_seconds),
            "trajectory_accumulation_seconds": max(0.0, trajectory_accumulation_seconds),
            "impact_accumulation_seconds": max(0.0, impact_accumulation_seconds),
        },
        "output_bytes": max(0, int(output_bytes or 0)),
        "input_artifacts": reducer_chunk_input_artifacts(chunk),
        "reducer_contract": reducer_contract_manifest(),
        "limitations": [
            "Local in-memory partial reducer state; no distributed scheduler is involved.",
            "Research diagnostic; not operational hazard-map evidence.",
        ],
    }
    if completion_status == "completed" and partial_state_path is not None:
        manifest["partial_state_path"] = str(partial_state_path)
        manifest["partial_state_schema_version"] = CHUNK_PARTIAL_STATE_SCHEMA_VERSION
    return manifest


def run_reducer_accumulation(
    output_dir: Path,
    prefix: str,
    grid: GridSpec,
    terrain: "TerrainSampler",
    block_radius_m: float,
    statistics: HazardStatisticConfig,
    probability: HazardProbabilityState | None,
    trajectory_paths: list[Path],
    deposition_path: Path | None,
    impact_event_paths: list[Path],
    impact_event_parquet_paths: list[Path],
    worker_count: int,
    *,
    owner_id: str | None = None,
    scheduler_index: int = 0,
    scheduler_count: int = 1,
    max_chunk_attempts: int = CHUNK_REDUCTION_MAX_ATTEMPTS,
    lease_seconds: int = CHUNK_CLAIM_TTL_SECONDS,
) -> tuple[HazardAccumulator, list[str], dict[str, Any] | None, list[Path], HazardAccumulationTimings]:
    if worker_count < 1:
        raise SystemExit("--reducer-workers must be at least 1")
    if worker_count == 1:
        return run_serial_reducer_accumulation(
            grid,
            terrain,
            block_radius_m,
            statistics,
            probability,
            trajectory_paths,
            deposition_path,
            impact_event_paths,
            impact_event_parquet_paths,
        )

    if scheduler_count < 1:
        raise SystemExit("--scheduler-count must be at least 1")
    if scheduler_index < 0 or scheduler_index >= scheduler_count:
        raise SystemExit("--scheduler-index must be in [0, --scheduler-count)")
    if lease_seconds < 1:
        raise SystemExit("--chunk-claim-ttl-seconds must be at least 1")
    if max_chunk_attempts < 1:
        raise SystemExit("--max-chunk-attempts must be at least 1")

    chunks = build_reducer_chunks(
        prefix,
        worker_count,
        trajectory_paths,
        deposition_path,
        impact_event_paths,
        impact_event_parquet_paths,
    )
    chunk_dir = output_dir / "chunks"
    chunk_dir.mkdir(parents=True, exist_ok=True)
    execution_plan = execution_plan_path(output_dir, prefix)
    execution_index = execution_index_path(output_dir, prefix)
    merge_state_output_path = merge_state_path(output_dir, prefix)
    now_unix_s = int(datetime.now(timezone.utc).timestamp())
    chunk_plan = build_chunk_execution_plan(
        prefix,
        chunks,
        worker_count,
        output_dir,
        owner_id=owner_id,
        scheduler_index=scheduler_index,
        scheduler_count=scheduler_count,
        max_chunk_attempts=max_chunk_attempts,
        lease_seconds=lease_seconds,
    )
    chunk_records_by_id = {
        chunk_record.get("chunk_id"): chunk_record
        for chunk_record in chunk_plan.get("chunk_manifests", [])
        if isinstance(chunk_record, dict) and isinstance(chunk_record.get("chunk_id"), str)
    }
    run_owner_id = owner_id or str(chunk_plan.get("owner_id") or stable_owner_id(prefix))
    scheduled_chunks = [
        chunk
        for chunk in chunks
        if scheduler_count <= 1 or chunk.index % scheduler_count == scheduler_index
    ]
    scheduled_chunk_ids = {chunk.chunk_id for chunk in scheduled_chunks}
    chunk_plan["scheduled_chunk_count"] = len(scheduled_chunks)
    chunk_plan["scheduled_chunk_ids"] = sorted(scheduled_chunk_ids)
    chunk_plan["input_file_count"] = {
        "trajectory_files": len(trajectory_paths),
        "impact_csv_files": len(impact_event_paths),
        "impact_parquet_tables": len(impact_event_parquet_paths),
        "deposition_files": 1 if deposition_path is not None else 0,
    }

    previous_plan = {}
    if execution_plan.exists():
        try:
            previous_plan = read_json(execution_plan)
        except (OSError, json.JSONDecodeError, ValueError):
            previous_plan = {}
    if (
        isinstance(previous_plan, dict)
        and previous_plan.get("schema_version") == CHUNK_EXECUTION_PLAN_SCHEMA_VERSION
        and previous_plan.get("chunk_count") == chunk_plan.get("chunk_count")
        and sorted((record.get("chunk_id") for record in previous_plan.get("chunk_manifests", [])))
        == sorted((record.get("chunk_id") for record in chunk_plan.get("chunk_manifests", [])))
    ):
        chunk_plan["previous_plan_id"] = previous_plan.get("plan_id")
        previous_records_by_id = {
            record.get("chunk_id"): record
            for record in previous_plan.get("chunk_manifests", [])
            if isinstance(record, dict) and isinstance(record.get("chunk_id"), str)
        }
        for chunk_id, chunk_record in chunk_records_by_id.items():
            previous_record = previous_records_by_id.get(chunk_id)
            if not isinstance(previous_record, dict):
                continue
            if previous_record.get("input_signature") != chunk_record.get("input_signature"):
                continue
            for field in (
                "status",
                "completion_state",
                "attempt_count",
                "retry_count",
                "completion_status",
                "execution_attempt",
                "row_count",
                "rows_written",
                "output_bytes",
                "failure_reason",
                "merge_group_id",
                "completion_reason",
                "execution_status",
                "manifest_path",
                "timings",
                "input_rows",
                "input_file_indices",
                "reducer_counts",
                "input_file_counts",
                "ownership",
                "partial_state_path",
                "partial_state_schema_version",
            ):
                if field in previous_record:
                    chunk_record[field] = previous_record[field]
            if is_stale_claim(previous_record, now_unix_s):
                mark_chunk_stale_release(chunk_record, now_unix_s)

    def record_for_chunk(chunk_id: str) -> dict[str, Any]:
        return chunk_records_by_id.get(chunk_id, {})

    def build_no_execution_result(chunk: ReducerChunk, record: dict[str, Any]) -> ReducerChunkResult:
        state_path = record.get("partial_state_path")
        if not state_path:
            raise SystemExit(f"chunk {chunk.chunk_id} has no partial state path in plan")
        accumulator = load_chunk_accumulator_state(
            Path(state_path),
            chunk,
            grid,
            terrain,
            block_radius_m,
            statistics,
            probability,
        )
        attempt_count = max(0, int(record.get("attempt_count") or 0))
        retry_count = max(0, int(record.get("retry_count") or 0))
        manifest = build_chunk_execution_manifest(
            chunk,
            accumulator,
            execution_plan,
            plan_id=chunk_plan.get("plan_id"),
            attempt_count=attempt_count,
            retry_count=retry_count,
            execution_status="completed",
            completion_status="completed",
            completion_reason=None,
            output_bytes=chunk_partial_state_path(chunk.chunk_id, chunk_dir).stat().st_size
            if Path(chunk_partial_state_path(chunk.chunk_id, chunk_dir)).exists()
            else 0,
            merge_group_id=chunk_plan.get("merge_group_id"),
            deposition_accumulation_seconds=0.0,
            trajectory_accumulation_seconds=0.0,
            impact_accumulation_seconds=0.0,
            partial_state_path=chunk_partial_state_path(chunk.chunk_id, chunk_dir),
            ownership=record.get("ownership"),
        )
        return ReducerChunkResult(
            chunk=chunk,
            accumulator=accumulator,
            warnings=tuple(accumulator.warnings),
            partial_state_path=chunk_partial_state_path(chunk.chunk_id, chunk_dir),
            manifest=manifest,
        )

    scheduled_results: list[ReducerChunkResult] = []
    scheduled_run_specs: list[tuple[ReducerChunk, int, int]] = []
    failed_chunks: list[str] = []
    ineligible_chunks: list[str] = []
    run_retries = 0
    scheduled_chunk_records = [
        chunk_records_by_id[chunk_id]
        for chunk_id in scheduled_chunk_ids
        if chunk_id in chunk_records_by_id
    ]

    for chunk in chunks:
        record = record_for_chunk(chunk.chunk_id)
        if not record:
            continue
        if chunk.chunk_id not in scheduled_chunk_ids:
            record["execution_status"] = "not_scheduled"
            continue

        if is_claim_active_for_other_owner(record, run_owner_id, now_unix_s):
            release_chunk(
                record,
                run_owner_id,
                now_unix_s,
                completion_status="not_started",
                execution_status="skipped",
                reason="claimed_by_other_owner",
                attempt_count=max(0, int(record.get("attempt_count") or 0)),
                retry_count=max(0, int(record.get("retry_count") or 0)),
            )
            ineligible_chunks.append(chunk.chunk_id)
            continue

        if is_stale_claim(record, now_unix_s):
            mark_chunk_stale_release(record, now_unix_s)

        if chunk_has_valid_reusable_state(chunk, record):
            scheduled_results.append(build_no_execution_result(chunk, record))
            continue

        if str(record.get("completion_status") or "not_started") == "completed":
            record["completion_status"] = "not_started"
            record["execution_status"] = "planned"

        retry_count = max(0, int(record.get("retry_count") or 0))
        attempt_count = max(0, int(record.get("attempt_count") or 0))
        if retry_count >= max_chunk_attempts:
            release_chunk(
                record,
                run_owner_id,
                now_unix_s,
                completion_status="failed",
                execution_status="failed",
                reason="max_chunk_attempts_exceeded",
                attempt_count=max(1, attempt_count),
                retry_count=retry_count,
            )
            failed_chunks.append(chunk.chunk_id)
            continue

        claim_chunk(record, run_owner_id, now_unix_s, lease_seconds)
        scheduled_run_specs.append((chunk, attempt_count, retry_count))

    if scheduled_run_specs:
        def run_spec(spec: tuple[ReducerChunk, int, int]) -> ReducerChunkResult:
            chunk, attempt_count, retry_count = spec
            return run_reducer_chunk(
                chunk,
                grid,
                terrain,
                block_radius_m,
                statistics,
                probability,
                attempt_count=attempt_count,
                retry_count=retry_count,
                execution_plan_path=execution_plan,
                plan_id=chunk_plan.get("plan_id"),
                partial_state_path=chunk_partial_state_path(chunk.chunk_id, chunk_dir),
                merge_group_id=chunk_plan.get("merge_group_id"),
            )

        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            run_results = list(executor.map(run_spec, scheduled_run_specs))
        scheduled_results.extend(run_results)
        run_retries += len(run_results)

    scheduled_results.sort(key=lambda result: result.chunk.chunk_id)
    accumulator = HazardAccumulator(grid, terrain, block_radius_m, statistics, probability)
    warnings: list[str] = []
    chunk_manifest_paths: list[Path] = []
    total_deposition_seconds = 0.0
    total_trajectory_seconds = 0.0
    total_impact_seconds = 0.0
    for result in scheduled_results:
        manifest = result.manifest
        chunk_id = result.chunk.chunk_id
        record = record_for_chunk(chunk_id)
        completion_status = str(manifest.get("completion_status") or "unknown")
        execution_status = str(manifest.get("execution_status") or "unknown")
        if completion_status == "completed":
            accumulator.merge(result.accumulator)
        else:
            failed_chunks.append(chunk_id)
        warnings.extend(result.warnings)
        if execution_status in {"completed", "failed"} and isinstance(manifest.get("timings"), dict):
            total_deposition_seconds += float(manifest["timings"]["deposition_accumulation_seconds"])
            total_trajectory_seconds += float(manifest["timings"]["trajectory_accumulation_seconds"])
            total_impact_seconds += float(manifest["timings"]["impact_accumulation_seconds"])

        for key in (
            "execution_status",
            "completion_status",
            "status",
            "completion_state",
            "completion_reason",
            "failure_reason",
            "execution_attempt",
            "row_count",
            "rows_written",
            "output_bytes",
            "merge_group_id",
            "timings",
            "attempt_count",
            "retry_count",
            "ownership",
            "input_rows",
            "reducer_counts",
            "input_file_counts",
            "input_file_indices",
        ):
            if key in manifest:
                record[key] = manifest[key]

        manifest_path = Path(str(record.get("manifest_path") or chunk_manifest_path(chunk_dir, chunk_id)))
        write_text(manifest_path, json.dumps(manifest, indent=2, sort_keys=True) + "\n")
        chunk_manifest_paths.append(manifest_path)
        record["manifest_path"] = str(manifest_path)
        release_reason = (
            "completed"
            if completion_status == "completed"
            else (
                "failed"
                if completion_status == "failed"
                else str(manifest.get("completion_reason") or "not_completed")
            )
        )
        release_chunk(
            record,
            run_owner_id,
            int(datetime.now(timezone.utc).timestamp()),
            completion_status=completion_status,
            execution_status=execution_status,
            reason=release_reason,
            attempt_count=int(manifest.get("attempt_count") or 0),
            retry_count=int(manifest.get("retry_count") or 0),
        )

    if scheduler_count == 1 and not all(
        str(record.get("completion_status") or "") == "completed"
        for record in scheduled_chunk_records
    ):
        failed_chunks.extend(chunk for chunk in ineligible_chunks if chunk not in failed_chunks)

    chunk_plan["completed_chunk_count"] = len(
        [record for record in chunk_records_by_id.values() if record.get("completion_status") == "completed"]
    )
    chunk_plan["failed_chunk_count"] = len(
        [record for record in chunk_records_by_id.values() if record.get("completion_status") == "failed"]
    )
    chunk_plan["chunk_ids_completed"] = [
        record.get("chunk_id")
        for record in chunk_records_by_id.values()
        if record.get("completion_status") == "completed"
    ]
    chunk_plan["chunk_ids_failed"] = [
        record.get("chunk_id")
        for record in chunk_records_by_id.values()
        if record.get("completion_status") == "failed"
    ]
    if ineligible_chunks:
        chunk_plan["ineligible_chunk_ids"] = sorted(ineligible_chunks)

    all_scheduled_completed = all(
        str(record.get("completion_status") or "") == "completed"
        for record in scheduled_chunk_records
    )
    chunk_plan["plan_status"] = "completed" if all_scheduled_completed else "running"

    if any(str(record.get("completion_status") or "") == "failed" for record in scheduled_chunk_records):
        chunk_plan["plan_status"] = "failed"

    if failed_chunks:
        chunk_plan["plan_status"] = "failed"

    chunk_plan["updated_unix_s"] = int(datetime.now(timezone.utc).timestamp())
    execution_index_manifest = build_reducer_execution_index_manifest(
        chunk_plan,
        list(chunk_records_by_id.values()),
        completed_chunk_count=chunk_plan["completed_chunk_count"],
        failed_chunk_count=chunk_plan["failed_chunk_count"],
        rerun_count=run_retries,
        scheduled_chunk_count=len(scheduled_chunk_ids),
    )
    merge_state = build_reducer_merge_state_manifest(chunk_plan, list(chunk_records_by_id.values()))
    write_text(execution_index, json.dumps(execution_index_manifest, indent=2, sort_keys=True) + "\n")
    write_text(merge_state_output_path, json.dumps(merge_state, indent=2, sort_keys=True) + "\n")
    write_text(execution_plan, json.dumps(chunk_plan, indent=2, sort_keys=True) + "\n")

    if failed_chunks:
        raise SystemExit(
            "chunk reducer execution failed for one or more chunks: "
            + ", ".join(sorted(set(failed_chunks)))
        )

    reducer_execution = {
        "schema_version": "deterministic_local_reducer_v1",
        "mode": "chunked_local_threads",
        "worker_count": worker_count,
        "chunk_count": len(chunks),
        "plan_id": chunk_plan.get("plan_id"),
        "execution_plan_path": str(execution_plan),
        "execution_index_path": str(execution_index),
        "merge_state_path": str(merge_state_output_path),
        "merge_group_id": chunk_plan.get("merge_group_id"),
        "retry_policy": "deterministic_chunk_retry_count_by_manifest",
        "rerun_count": run_retries,
        "failed_chunk_count": len([id for id in failed_chunks if id in scheduled_chunk_ids]),
        "completed_chunk_count": chunk_plan["completed_chunk_count"],
        "scheduled_chunk_count": len(scheduled_chunk_ids),
        "chunk_ids": sorted(result.chunk.chunk_id for result in scheduled_results),
        "plan_status": chunk_plan.get("plan_status"),
        "owner_id": chunk_plan.get("owner_id"),
        "scheduler_index": scheduler_index,
        "scheduler_count": scheduler_count,
        "max_chunk_attempts": max_chunk_attempts,
        "merge_order": "sorted_chunk_id",
        "merge_order_independent": True,
        "partial_state_storage": "chunk_state_json",
        "full_trajectory_output_default": False,
        "reducer_contract": reducer_contract_manifest(),
    }

    timings = HazardAccumulationTimings(
        bounds_discovery_seconds=0.0,
        deposition_accumulation_seconds=total_deposition_seconds,
        trajectory_accumulation_seconds=total_trajectory_seconds,
        impact_accumulation_seconds=total_impact_seconds,
        normalization_seconds=0.0,
    )
    return accumulator, warnings, reducer_execution, chunk_manifest_paths, timings

def run_serial_reducer_accumulation(
    grid: GridSpec,
    terrain: "TerrainSampler",
    block_radius_m: float,
    statistics: HazardStatisticConfig,
    probability: HazardProbabilityState | None,
    trajectory_paths: list[Path],
    deposition_path: Path | None,
    impact_event_paths: list[Path],
    impact_event_parquet_paths: list[Path],
) -> tuple[HazardAccumulator, list[str], None, list[Path], HazardAccumulationTimings]:
    warnings: list[str] = []
    accumulator = HazardAccumulator(grid, terrain, block_radius_m, statistics, probability)
    deposition_started = time.perf_counter()
    accumulator.accumulate_deposition(read_deposition_batch(deposition_path, warnings))
    deposition_accumulation_seconds = time.perf_counter() - deposition_started
    trajectory_started = time.perf_counter()
    for trajectory_path in trajectory_paths:
        batch = read_trajectory_sample_batch(trajectory_path, warnings)
        if batch is not None:
            accumulator.accumulate_trajectory(batch)
    trajectory_accumulation_seconds = time.perf_counter() - trajectory_started
    impact_started = time.perf_counter()
    for batch in read_impact_event_csv_batches(impact_event_paths, warnings):
        accumulator.accumulate_impacts(batch)
    for batch in read_impact_event_parquet_batches(impact_event_parquet_paths, warnings):
        accumulator.accumulate_impacts(batch)
    impact_accumulation_seconds = time.perf_counter() - impact_started
    timings = HazardAccumulationTimings(
        bounds_discovery_seconds=0.0,
        deposition_accumulation_seconds=deposition_accumulation_seconds,
        trajectory_accumulation_seconds=trajectory_accumulation_seconds,
        impact_accumulation_seconds=impact_accumulation_seconds,
        normalization_seconds=0.0,
    )
    return accumulator, warnings, None, [], timings


def build_reducer_chunks(
    prefix: str,
    worker_count: int,
    trajectory_paths: list[Path],
    deposition_path: Path | None,
    impact_event_paths: list[Path],
    impact_event_parquet_paths: list[Path],
) -> list[ReducerChunk]:
    chunks: list[ReducerChunk] = []
    trajectory_partitions = contiguous_partitions(trajectory_paths, worker_count)
    impact_partitions = contiguous_partitions(impact_event_paths, worker_count)
    parquet_partitions = contiguous_partitions(impact_event_parquet_paths, worker_count)
    trajectory_ranges = chunk_partition_ranges(len(trajectory_paths), worker_count)
    impact_ranges = chunk_partition_ranges(len(impact_event_paths), worker_count)
    parquet_ranges = chunk_partition_ranges(len(impact_event_parquet_paths), worker_count)
    for index in range(worker_count):
        trajectory_start, trajectory_end_exclusive = trajectory_ranges[index]
        impact_start, impact_end_exclusive = impact_ranges[index]
        parquet_start, parquet_end_exclusive = parquet_ranges[index]
        chunks.append(
            ReducerChunk(
                chunk_id=f"{stable_required_id(prefix, 'prefix')}__chunk_{index:04d}",
                index=index,
                trajectory_start=trajectory_start,
                trajectory_end_exclusive=trajectory_end_exclusive,
                trajectory_paths=tuple(trajectory_partitions[index]),
                deposition_path=deposition_path if index == 0 else None,
                impact_csv_start=impact_start,
                impact_csv_end_exclusive=impact_end_exclusive,
                impact_event_paths=tuple(impact_partitions[index]),
                impact_parquet_start=parquet_start,
                impact_parquet_end_exclusive=parquet_end_exclusive,
                impact_event_parquet_paths=tuple(parquet_partitions[index]),
            )
        )
    return chunks


def contiguous_partitions(paths: list[Path], partition_count: int) -> list[list[Path]]:
    partitions: list[list[Path]] = []
    total = len(paths)
    for index in range(partition_count):
        start = index * total // partition_count
        end = (index + 1) * total // partition_count
        partitions.append(paths[start:end])
    return partitions


def run_reducer_chunk(
    chunk: ReducerChunk,
    grid: GridSpec,
    terrain: "TerrainSampler",
    block_radius_m: float,
    statistics: HazardStatisticConfig,
    probability: HazardProbabilityState | None,
    attempt_count: int,
    retry_count: int,
    execution_plan_path: Path,
    plan_id: str | None,
    partial_state_path: Path,
    merge_group_id: str | None = None,
) -> ReducerChunkResult:
    warnings: list[str] = []
    accumulator = HazardAccumulator(grid, terrain, block_radius_m, statistics, probability)
    execution_status = "completed"
    completion_status = "completed"
    completion_reason = None
    deposition_seconds = 0.0
    trajectory_seconds = 0.0
    impact_seconds = 0.0
    prior_attempt_count = max(0, int(attempt_count))
    prior_retry_count = max(0, int(retry_count))
    deposition_started = time.perf_counter()
    trajectory_started = time.perf_counter()
    impact_started = time.perf_counter()
    try:
        accumulator.accumulate_deposition(read_deposition_batch(chunk.deposition_path, warnings))
        deposition_seconds = time.perf_counter() - deposition_started
        trajectory_started = time.perf_counter()
        for trajectory_path in chunk.trajectory_paths:
            batch = read_trajectory_sample_batch(trajectory_path, warnings)
            if batch is not None:
                accumulator.accumulate_trajectory(batch)
        trajectory_seconds = time.perf_counter() - trajectory_started
        impact_started = time.perf_counter()
        for batch in read_impact_event_csv_batches(list(chunk.impact_event_paths), warnings):
            accumulator.accumulate_impacts(batch)
        for batch in read_impact_event_parquet_batches(list(chunk.impact_event_parquet_paths), warnings):
            accumulator.accumulate_impacts(batch)
        impact_seconds = time.perf_counter() - impact_started
        completion_status = "completed"
    except Exception as exc:  # noqa: BLE001 - chunk-level failure is surfaced by chunk manifest and rerun contract.
        execution_status = "failed"
        completion_status = "failed"
        completion_reason = str(exc)
        warnings.append(completion_reason)

    manifest = build_chunk_execution_manifest(
        chunk,
        accumulator,
        execution_plan_path,
        plan_id=plan_id,
        attempt_count=prior_attempt_count + 1,
        retry_count=prior_retry_count + (1 if completion_status == "failed" else 0),
        execution_status=execution_status,
        completion_status=completion_status,
        completion_reason=completion_reason,
        output_bytes=0,
        merge_group_id=merge_group_id,
        deposition_accumulation_seconds=deposition_seconds,
        trajectory_accumulation_seconds=trajectory_seconds,
        impact_accumulation_seconds=impact_seconds,
        partial_state_path=partial_state_path if completion_status == "completed" else None,
    )
    if completion_status == "completed":
        partial_state_payload = serialize_chunk_accumulator_state(accumulator, chunk)
        write_text(partial_state_path, json.dumps(partial_state_payload, indent=2, sort_keys=True) + "\n")
        manifest["partial_state_path"] = str(partial_state_path)
        manifest["partial_state_schema_version"] = CHUNK_PARTIAL_STATE_SCHEMA_VERSION
        manifest["output_bytes"] = partial_state_path.stat().st_size

    return ReducerChunkResult(
        chunk=chunk,
        accumulator=accumulator,
        warnings=tuple(warnings),
        partial_state_path=partial_state_path,
        manifest=manifest,
    )


def reducer_chunk_input_artifacts(chunk: ReducerChunk) -> list[dict[str, Any]]:
    artifacts = [
        input_artifact_collection([str(path) for path in chunk.trajectory_paths], "trajectory_samples", "csv_collection"),
        input_artifact_collection([str(path) for path in chunk.impact_event_paths], "impact_events", "csv_collection"),
        input_artifact_collection(
            [str(path) for path in chunk.impact_event_parquet_paths],
            "impact_events",
            "parquet_collection",
        ),
    ]
    if chunk.deposition_path is not None:
        artifacts.append(input_artifact_entry(chunk.deposition_path, "deposition_points", "csv"))
    return [artifact for artifact in artifacts if artifact["file_count"] > 0]


def reducer_contract_manifest() -> dict[str, Any]:
    return {
        "reach_counts": "cellwise integer counts add across chunks",
        "threshold_exceedance_counts": "cellwise integer or sampling-weighted counts add across chunks",
        "max_kinetic_energy": "cellwise maximum across chunks",
        "max_jump_height": "cellwise maximum across chunks",
        "deposition_density_counts": "cellwise deposition counts add across chunks",
        "significant_impact_counts": "cellwise significant-impact counts add across chunks",
        "merge_order": "deterministic after sorting chunk_id",
    }


def serialize_grid(grid: list[list[float]]) -> list[list[float]]:
    return [list(row) for row in grid]


def deserialize_grid(raw: Any) -> list[list[float]]:
    if not isinstance(raw, list):
        raise ValueError("serialized grid must be a list of rows")
    values: list[list[float]] = []
    for row in raw:
        if not isinstance(row, list):
            raise ValueError("serialized grid row must be a list")
        values.append([float(value) for value in row])
    return values


def serialize_threshold_grids(threshold_grids: dict[float, list[list[float]]]) -> dict[str, list[list[float]]]:
    return {str(threshold): serialize_grid(grid) for threshold, grid in threshold_grids.items()}


def deserialize_threshold_grids(raw: Any) -> dict[float, list[list[float]]]:
    if not isinstance(raw, dict):
        raise ValueError("serialized threshold grids must be a dict")
    threshold_grids: dict[float, list[list[float]]] = {}
    for threshold_text, rows in raw.items():
        threshold = float(threshold_text)
        threshold_grids[threshold] = deserialize_grid(rows)
    return threshold_grids


def serialize_chunk_accumulator_state(accumulator: "HazardAccumulator", chunk: ReducerChunk) -> dict[str, Any]:
    return {
        "schema_version": CHUNK_PARTIAL_STATE_SCHEMA_VERSION,
        "chunk_id": chunk.chunk_id,
        "input_signature": chunk_input_signature(chunk),
        "execution_state_schema_version": CHUNK_EXECUTION_MANIFEST_SCHEMA_VERSION,
        "trajectory_count": accumulator.trajectory_count,
        "trajectory_sample_count": accumulator.trajectory_sample_count,
        "deposition_point_count": accumulator.deposition_point_count,
        "impact_event_count": accumulator.impact_event_count,
        "significant_impact_count": accumulator.significant_impact_count,
        "warnings": list(accumulator.warnings),
        "inputs": {
            "trajectory_count": accumulator.trajectory_count,
            "deposition_point_count": accumulator.deposition_point_count,
            "impact_event_count": accumulator.impact_event_count,
            "significant_impact_count": accumulator.significant_impact_count,
        },
        "grids": {
            "reach": serialize_grid(accumulator.reach),
            "max_ke": serialize_grid(accumulator.max_ke),
            "max_jump": serialize_grid(accumulator.max_jump),
            "kinetic_exceedance": serialize_threshold_grids(accumulator.kinetic_exceedance),
            "weighted_kinetic_exceedance": serialize_threshold_grids(accumulator.weighted_kinetic_exceedance),
            "jump_exceedance": serialize_threshold_grids(accumulator.jump_exceedance),
            "weighted_jump_exceedance": serialize_threshold_grids(accumulator.weighted_jump_exceedance),
            "velocity_exceedance": serialize_threshold_grids(accumulator.velocity_exceedance),
            "weighted_velocity_exceedance": serialize_threshold_grids(accumulator.weighted_velocity_exceedance),
            "deposition": serialize_grid(accumulator.deposition),
            "weighted_deposition": serialize_grid(accumulator.weighted_deposition)
            if accumulator.weighted_deposition is not None
            else None,
            "impact_density": serialize_grid(accumulator.impact_density),
            "weighted_impact_density": serialize_grid(accumulator.weighted_impact_density)
            if accumulator.weighted_impact_density is not None
            else None,
        },
        "weighted_significant_impact_weight": accumulator.weighted_significant_impact_weight,
        "deposition_points": [
            {
                "x_m": point.x_m,
                "y_m": point.y_m,
                "trajectory_id": point.trajectory_id,
                "properties": dict(point.properties),
            }
            for point in accumulator.deposition_points
        ],
    }


def load_chunk_accumulator_state(
    path: Path,
    chunk: ReducerChunk,
    grid: GridSpec,
    terrain: "TerrainSampler",
    block_radius_m: float,
    statistics: HazardStatisticConfig,
    probability: HazardProbabilityState | None,
) -> HazardAccumulator:
    payload = read_json(path)
    if not isinstance(payload, dict) or payload.get("schema_version") != CHUNK_PARTIAL_STATE_SCHEMA_VERSION:
        raise SystemExit(f"invalid partial chunk state at {path}")
    if payload.get("chunk_id") != chunk.chunk_id or payload.get("input_signature") != chunk_input_signature(chunk):
        raise SystemExit(f"partial chunk state at {path} does not match chunk {chunk.chunk_id}")
    accumulator = HazardAccumulator(grid, terrain, block_radius_m, statistics, probability)
    grids = payload.get("grids")
    if not isinstance(grids, dict):
        raise SystemExit(f"partial chunk state {path} missing grids")
    accumulator.reach = deserialize_grid(grids.get("reach"))
    accumulator.max_ke = deserialize_grid(grids.get("max_ke"))
    accumulator.max_jump = deserialize_grid(grids.get("max_jump"))
    accumulator.deposition = deserialize_grid(grids.get("deposition"))
    accumulator.impact_density = deserialize_grid(grids.get("impact_density"))
    accumulator.kinetic_exceedance = deserialize_threshold_grids(grids.get("kinetic_exceedance"))
    accumulator.jump_exceedance = deserialize_threshold_grids(grids.get("jump_exceedance"))
    accumulator.velocity_exceedance = deserialize_threshold_grids(grids.get("velocity_exceedance"))
    accumulator.weighted_kinetic_exceedance = deserialize_threshold_grids(grids.get("weighted_kinetic_exceedance"))
    accumulator.weighted_jump_exceedance = deserialize_threshold_grids(grids.get("weighted_jump_exceedance"))
    accumulator.weighted_velocity_exceedance = deserialize_threshold_grids(grids.get("weighted_velocity_exceedance"))
    weighted_deposition = grids.get("weighted_deposition")
    weighted_impact_density = grids.get("weighted_impact_density")
    if weighted_deposition is None:
        accumulator.weighted_deposition = None
    else:
        accumulator.weighted_deposition = deserialize_grid(weighted_deposition)
    if weighted_impact_density is None:
        accumulator.weighted_impact_density = None
    else:
        accumulator.weighted_impact_density = deserialize_grid(weighted_impact_density)
    accumulator.trajectory_count = int(payload.get("trajectory_count", 0))
    accumulator.trajectory_sample_count = int(payload.get("trajectory_sample_count", 0))
    accumulator.deposition_point_count = int(payload.get("deposition_point_count", 0))
    accumulator.impact_event_count = int(payload.get("impact_event_count", 0))
    accumulator.significant_impact_count = int(payload.get("significant_impact_count", 0))
    accumulator.weighted_significant_impact_weight = float(payload.get("weighted_significant_impact_weight", 0.0))
    points_raw = payload.get("deposition_points", [])
    accumulator.deposition_points = [
        DepositionPoint(
            x_m=point.get("x_m"),
            y_m=point.get("y_m"),
            trajectory_id=point.get("trajectory_id"),
            properties=dict(point.get("properties", {})),
        )
        for point in points_raw
        if isinstance(point, dict)
    ]
    warnings_raw = payload.get("warnings", [])
    accumulator.warnings = [str(item) for item in warnings_raw] if isinstance(warnings_raw, list) else []
    return accumulator


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
        probability_standard_error=bool(
            args.probability_standard_error or statistics.get("probability_standard_error") is True
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
        row_trajectory_id = trajectory_id_from_sample_or_path(row, path)
        if trajectory_id is None:
            trajectory_id = row_trajectory_id
        elif row_trajectory_id != trajectory_id:
            raise SystemExit(
                f"trajectory CSV {path} contains multiple trajectory_id values; "
                "current hazard-layer accumulation expects one trajectory per CSV"
            )
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
    raw_trajectory_id = str(row.get("trajectory_id") or "").strip()
    return DepositionPoint(
        x_m=numeric(row.get("x_m")),
        y_m=numeric(row.get("y_m")),
        trajectory_id=raw_trajectory_id or None,
        properties={key: value for key, value in row.items() if key not in {"x_m", "y_m"}},
    )


def read_impact_event_csv_batches(paths: list[Path], warnings: list[str]) -> Iterator[ImpactEventBatch]:
    for path in paths:
        if not path.exists():
            continue
        event_count = 0
        significant_event_count = 0
        significant_points: list[SignificantImpactPoint] = []
        for event in iter_numeric_csv(path, f"impact_events:{path}", warnings):
            event_count += 1
            if (numeric(event.get("incoming_normal_speed_mps")) or 0.0) < SIGNIFICANT_IMPACT_MIN_NORMAL_SPEED_MPS:
                continue
            significant_event_count += 1
            x = numeric(event.get("x_m"))
            y = numeric(event.get("y_m"))
            if x is not None and y is not None:
                significant_points.append(
                    SignificantImpactPoint(
                        x_m=x,
                        y_m=y,
                        trajectory_id=trajectory_id_from_impact_event_or_path(event, path),
                    )
                )
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
    include_trajectory_id = "trajectory_id" in names
    if include_trajectory_id:
        columns.append("trajectory_id")

    dropped = 0
    for batch in parquet_file.iter_batches(columns=columns, batch_size=65_536):
        xs = batch.column(0).to_pylist()
        ys = batch.column(1).to_pylist()
        significance_values = batch.column(2).to_pylist()
        trajectory_ids = batch.column(3).to_pylist() if include_trajectory_id else [None] * len(xs)
        impact_event_count = 0
        significant_impact_count = 0
        significant_points: list[SignificantImpactPoint] = []
        for x_value, y_value, significance_value, trajectory_id_value in zip(
            xs,
            ys,
            significance_values,
            trajectory_ids,
        ):
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
            trajectory_id = str(trajectory_id_value or "").strip() if include_trajectory_id else None
            significant_points.append(SignificantImpactPoint(x_m=x, y_m=y, trajectory_id=trajectory_id or None))
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


def copy_grid(values: list[list[float]]) -> list[list[float]]:
    return [list(row) for row in values]


def scaled_grid(values: list[list[float]], factor: float) -> list[list[float]]:
    result = copy_grid(values)
    scale_grid(result, factor)
    return result


def add_grid_into(target: list[list[float]], source: list[list[float]]) -> None:
    for row_index, row in enumerate(source):
        for col_index, value in enumerate(row):
            target[row_index][col_index] += value


def merge_max_grid_into(target: list[list[float]], source: list[list[float]]) -> None:
    for row_index, row in enumerate(source):
        for col_index, value in enumerate(row):
            if value == NODATA:
                continue
            if target[row_index][col_index] == NODATA or value > target[row_index][col_index]:
                target[row_index][col_index] = value


def add_threshold_grids_into(
    target: dict[float, list[list[float]]],
    source: dict[float, list[list[float]]],
) -> None:
    for threshold, source_grid in source.items():
        add_grid_into(target[threshold], source_grid)


def binomial_standard_error_grid(counts: list[list[float]], trajectory_count: int) -> list[list[float]]:
    if trajectory_count <= 0:
        raise SystemExit("trajectory count must be positive for probability standard-error layers")
    result: list[list[float]] = []
    denominator = float(trajectory_count)
    for row in counts:
        result_row: list[float] = []
        for count in row:
            p = count / denominator
            variance = max(0.0, p * (1.0 - p) / denominator)
            result_row.append(math.sqrt(variance))
        result.append(result_row)
    return result


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


def trajectory_id_from_impact_event_or_path(event: dict[str, float | str], path: Path) -> str | None:
    value = event.get("trajectory_id")
    if isinstance(value, str) and value.strip():
        return value.strip()
    if path.stem.startswith("trajectory_"):
        return path.stem
    return None


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


class _OutputByteTracker:
    def __init__(self, wrapped: TextIOBase, digest: hashlib._Hash) -> None:
        self._wrapped = wrapped
        self._digest = digest
        self.bytes_written = 0

    def write(self, text: str) -> int:
        if text:
            encoded = text.encode("utf-8")
            self._digest.update(encoded)
            self.bytes_written += len(encoded)
        return self._wrapped.write(text)

    def flush(self) -> None:
        self._wrapped.flush()


def _register_written_output(
    path: Path,
    kind: str,
    output_file_metadata: dict[Path, dict[str, Any]],
    output_write_kind_seconds: dict[str, float],
    output_write_kind_bytes: dict[str, int],
    *,
    elapsed_seconds: float,
    total_bytes: int,
    sha256_hex: str | None,
) -> None:
    output_write_kind_seconds[kind] = output_write_kind_seconds.get(kind, 0.0) + elapsed_seconds
    output_write_kind_bytes[kind] = output_write_kind_bytes.get(kind, 0) + total_bytes
    output_file_metadata[path] = {
        "total_bytes": total_bytes,
        "sha256": sha256_hex,
    }


def _safe_sha256_hex(data: bytes) -> str:
    digest = hashlib.sha256()
    digest.update(data)
    return digest.hexdigest()


def write_layers(
    output_dir: Path,
    prefix: str,
    grid: GridSpec,
    layers: list[RasterLayer],
    raster_export_config: RasterExportConfig,
    output_file_metadata: dict[Path, dict[str, Any]],
    output_write_kind_seconds: dict[str, float],
    output_write_kind_bytes: dict[str, int],
) -> None:
    for layer in layers:
        if raster_export_config.grid_csv_export == "full":
            write_grid_csv(
                output_dir / f"{prefix}_{layer.key}.csv",
                grid,
                layer,
                output_file_metadata=output_file_metadata,
                output_write_kind_seconds=output_write_kind_seconds,
                output_write_kind_bytes=output_write_kind_bytes,
            )
        write_ascii_grid(
            output_dir / f"{prefix}_{layer.key}.asc",
            grid,
            layer,
            output_file_metadata=output_file_metadata,
            output_write_kind_seconds=output_write_kind_seconds,
            output_write_kind_bytes=output_write_kind_bytes,
        )


def write_grid_csv(
    path: Path,
    grid: GridSpec,
    layer: RasterLayer,
    output_file_metadata: dict[Path, dict[str, Any]],
    output_write_kind_seconds: dict[str, float],
    output_write_kind_bytes: dict[str, int],
) -> None:
    started = time.perf_counter()
    digest = hashlib.sha256()
    with path.open("w", newline="") as file:
        tracked_file = _OutputByteTracker(file, digest)
        writer = csv.writer(tracked_file)
        writer.writerow(["row", "col", "x_center_m", "y_center_m", layer.key])
        for row in range(grid.nrows):
            for col in range(grid.ncols):
                x, y = grid.center(row, col)
                value = layer.values[row][col]
                writer.writerow([row, col, f"{x:.6f}", f"{y:.6f}", f"{value:.12g}"])
        tracked_file.flush()
    _register_written_output(
        path,
        "csv_grid",
        output_file_metadata,
        output_write_kind_seconds,
        output_write_kind_bytes,
        elapsed_seconds=time.perf_counter() - started,
        total_bytes=tracked_file.bytes_written,
        sha256_hex=digest.hexdigest(),
    )


def write_ascii_grid(
    path: Path,
    grid: GridSpec,
    layer: RasterLayer,
    output_file_metadata: dict[Path, dict[str, Any]],
    output_write_kind_seconds: dict[str, float],
    output_write_kind_bytes: dict[str, int],
) -> None:
    started = time.perf_counter()
    digest = hashlib.sha256()
    lines = [
        f"ncols {grid.ncols}",
        f"nrows {grid.nrows}",
        f"xllcorner {grid.xmin:.12g}",
        f"yllcorner {grid.ymin:.12g}",
        f"cellsize {grid.cell_size:.12g}",
        f"NODATA_value {NODATA:.12g}",
    ]
    with path.open("w", newline="") as file:
        tracked_file = _OutputByteTracker(file, digest)
        for line in lines:
            tracked_file.write(line + "\n")
        for row in layer.values:
            tracked_file.write(" ".join(f"{ascii_value(value):.12g}" for value in row) + "\n")
        tracked_file.flush()
    _register_written_output(
        path,
        "esri_ascii_grid",
        output_file_metadata,
        output_write_kind_seconds,
        output_write_kind_bytes,
        elapsed_seconds=time.perf_counter() - started,
        total_bytes=tracked_file.bytes_written,
        sha256_hex=digest.hexdigest(),
    )


def ascii_value(value: float) -> float:
    return value if math.isfinite(value) else NODATA


def write_geotiff_layers(
    output_dir: Path,
    prefix: str,
    grid: GridSpec,
    layers: list[RasterLayer],
    case: dict[str, Any],
    export_config: RasterExportConfig,
    output_file_metadata: dict[Path, dict[str, Any]],
    output_write_kind_seconds: dict[str, float],
    output_write_kind_bytes: dict[str, int],
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
            output_file_metadata=output_file_metadata,
            output_write_kind_seconds=output_write_kind_seconds,
            output_write_kind_bytes=output_write_kind_bytes,
        )


def write_geotiff_grid(
    path: Path,
    grid: GridSpec,
    layer: RasterLayer,
    spatial_reference: dict[str, Any],
    export_config: RasterExportConfig,
    output_file_metadata: dict[Path, dict[str, Any]],
    output_write_kind_seconds: dict[str, float],
    output_write_kind_bytes: dict[str, int],
) -> None:
    _ = export_config
    started = time.perf_counter()
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
    _register_written_output(
        path,
        "geotiff",
        output_file_metadata,
        output_write_kind_seconds,
        output_write_kind_bytes,
        elapsed_seconds=time.perf_counter() - started,
        total_bytes=path.stat().st_size if path.exists() else len(
            b"II" + struct.pack("<HI", 42, ifd_offset) + pixel_bytes + ifd_bytes
        ),
        sha256_hex=_safe_sha256_hex(b"II" + struct.pack("<HI", 42, ifd_offset) + pixel_bytes + ifd_bytes),
    )


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


def write_deposition_geojson(
    path: Path,
    depositions: list[DepositionPoint],
    output_file_metadata: dict[Path, dict[str, Any]],
    output_write_kind_seconds: dict[str, float],
    output_write_kind_bytes: dict[str, int],
) -> float:
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
    serialization_started = time.perf_counter()
    text = json.dumps({"type": "FeatureCollection", "features": features}, indent=2, sort_keys=True) + "\n"
    serialization_seconds = time.perf_counter() - serialization_started
    write_file_text(
        path,
        text,
        "geojson",
        output_file_metadata,
        output_write_kind_seconds,
        output_write_kind_bytes,
        elapsed_seconds=0.0,
    )
    return serialization_seconds




def build_conditional_intensity_exceedance_curves(
    grid: GridSpec,
    layers: list[RasterLayer],
    stats: InputStats,
    probability: HazardProbabilityState | None,
    map_package: HazardMapPackageState | None,
) -> list[ConditionalCurveRow]:
    standard_errors = {
        layer.key.removesuffix("_standard_error"): layer
        for layer in layers
        if layer.key.endswith("_standard_error") and "exceedance" in layer.key
    }
    rows: list[ConditionalCurveRow] = []
    for layer in layers:
        parsed = parse_exceedance_layer_key(layer.key)
        if parsed is None:
            continue
        intensity_measure, threshold, threshold_units, weighted = parsed
        if weighted:
            denominator = probability.total_filtered_weight if probability else 0.0
            probability_mode = "sampling_weighted_conditional"
            normalization_scope = (
                map_package.config.normalization_scope
                if map_package is not None
                else "conditioned_on_filter"
            )
        else:
            denominator = float(stats.trajectory_count)
            probability_mode = "unweighted_diagnostic"
            normalization_scope = "supplied_trajectory_count"
        if denominator <= 0.0:
            continue
        standard_error_layer = standard_errors.get(layer.key)
        for row in range(grid.nrows):
            for col in range(grid.ncols):
                value = layer.values[row][col]
                if not math.isfinite(value) or value == NODATA:
                    continue
                x, y = grid.center(row, col)
                standard_error = (
                    standard_error_layer.values[row][col]
                    if standard_error_layer is not None
                    else None
                )
                rows.append(
                    ConditionalCurveRow(
                        row=row,
                        col=col,
                        x_center_m=x,
                        y_center_m=y,
                        intensity_measure=intensity_measure,
                        threshold=threshold,
                        threshold_units=threshold_units,
                        layer_name=layer.key,
                        probability_mode=probability_mode,
                        normalization_scope=normalization_scope,
                        numerator=value * denominator,
                        denominator=denominator,
                        conditional_fraction=value,
                        standard_error=standard_error,
                        weighted=weighted,
                    )
                )
    return rows


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


def write_conditional_intensity_exceedance_curves(
    path: Path,
    rows: list[ConditionalCurveRow],
    output_file_metadata: dict[Path, dict[str, Any]],
    output_write_kind_seconds: dict[str, float],
    output_write_kind_bytes: dict[str, int],
) -> None:
    started = time.perf_counter()
    with path.open("w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                "row",
                "col",
                "x_center_m",
                "y_center_m",
                "intensity_measure",
                "threshold",
                "threshold_units",
                "layer_name",
                "probability_mode",
                "normalization_scope",
                "numerator",
                "denominator",
                "conditional_fraction",
                "standard_error",
                "weighted",
                "annualized",
            ]
        )
        for row in rows:
            writer.writerow(
                [
                    row.row,
                    row.col,
                    f"{row.x_center_m:.6f}",
                    f"{row.y_center_m:.6f}",
                    row.intensity_measure,
                    f"{row.threshold:.12g}",
                    row.threshold_units,
                    row.layer_name,
                    row.probability_mode,
                    row.normalization_scope,
                    f"{row.numerator:.12g}",
                    f"{row.denominator:.12g}",
                    f"{row.conditional_fraction:.12g}",
                    "" if row.standard_error is None else f"{row.standard_error:.12g}",
                    str(row.weighted).lower(),
                    str(row.annualized).lower(),
                ]
            )
    _register_written_output(
        path,
        "csv_table",
        output_file_metadata,
        output_write_kind_seconds,
        output_write_kind_bytes,
        elapsed_seconds=time.perf_counter() - started,
        total_bytes=path.stat().st_size,
        sha256_hex=sha256_file(path),
    )


def summarize_conditional_curve_rows(
    rows: list[ConditionalCurveRow],
    export_config: ConditionalCurveExportConfig,
) -> dict[str, Any]:
    if not rows:
        return {"enabled": False, "row_count": 0, **export_config.as_metadata()}
    return {
        "enabled": True,
        "schema_version": "conditional_intensity_exceedance_curves_v1",
        "row_count": len(rows),
        "intensity_measures": sorted({row.intensity_measure for row in rows}),
        "probability_modes": sorted({row.probability_mode for row in rows}),
        **export_config.as_metadata(),
    }


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
    conditional_curve_export: ConditionalCurveExportConfig,
    conditional_curve_rows: list[ConditionalCurveRow],
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
        "conditional_intensity_exceedance_curves": summarize_conditional_curve_rows(
            conditional_curve_rows,
            conditional_curve_export,
        ),
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
    if layer_key.endswith("_standard_error"):
        return "estimated standard error of trajectory-level probability"
    if layer_key == "reach_probability" or layer_key == "weighted_reach_probability":
        return "trajectories reaching cell"
    if "exceedance" in layer_key:
        return "trajectories exceeding threshold in cell"
    if layer_key == "deposition_density" or layer_key == "weighted_deposition_density":
        return "deposition points in cell"
    if layer_key == "significant_impact_density" or layer_key == "weighted_significant_impact_density":
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
    if layer_key.endswith("_standard_error"):
        return "supplied trajectory count"
    if layer_key == "weighted_significant_impact_density":
        return "filtered significant impact event sampling_weight sum"
    if weighted and probability is not None:
        return f"filtered sampling_weight sum ({probability.total_filtered_weight:g})"
    if layer_key == "reach_probability" or "exceedance" in layer_key:
        if map_package is not None:
            return "trajectory count conditioned on source/scenario metadata"
        return "supplied trajectory count"
    if layer_key == "deposition_density":
        return "deposition point count"
    if layer_key == "significant_impact_density" or layer_key == "weighted_significant_impact_density":
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
    conditional_curve_export: ConditionalCurveExportConfig,
    conditional_curve_rows: list[ConditionalCurveRow],
    output_file_metadata: dict[Path, dict[str, Any]],
    output_write_kind_seconds: dict[str, float],
    output_write_kind_bytes: dict[str, int],
) -> float:
    write_layers(
        output_dir,
        prefix,
        grid,
        layers,
        raster_exports,
        output_file_metadata=output_file_metadata,
        output_write_kind_seconds=output_write_kind_seconds,
        output_write_kind_bytes=output_write_kind_bytes,
    )
    write_geotiff_layers(
        output_dir,
        prefix,
        grid,
        layers,
        case,
        raster_exports,
        output_file_metadata=output_file_metadata,
        output_write_kind_seconds=output_write_kind_seconds,
        output_write_kind_bytes=output_write_kind_bytes,
    )
    json_serialization_seconds = 0.0
    if conditional_curve_rows and conditional_curve_export.write_table:
        write_conditional_intensity_exceedance_curves(
            output_dir / f"{prefix}_conditional_intensity_exceedance_curves.csv",
            conditional_curve_rows,
            output_file_metadata=output_file_metadata,
            output_write_kind_seconds=output_write_kind_seconds,
            output_write_kind_bytes=output_write_kind_bytes,
        )
    json_serialization_seconds += write_deposition_geojson(
        output_dir / f"{prefix}_deposition_points.geojson",
        deposition_points,
        output_file_metadata=output_file_metadata,
        output_write_kind_seconds=output_write_kind_seconds,
        output_write_kind_bytes=output_write_kind_bytes,
    )
    serialization_started = time.perf_counter()
    text = json.dumps(metadata, indent=2, sort_keys=True) + "\n"
    json_serialization_seconds += time.perf_counter() - serialization_started
    write_file_text(
        output_dir / f"{prefix}_metadata.json",
        text,
        "json",
        output_file_metadata,
        output_write_kind_seconds,
        output_write_kind_bytes,
        elapsed_seconds=0.0,
    )
    return json_serialization_seconds


def map_package_output_path(
    map_package: HazardMapPackageState,
    output_dir: Path,
    prefix: str,
) -> Path:
    return map_package.config.map_package_manifest_json or output_dir / f"{prefix}_map_package_manifest.json"


def pilot_gis_package_output_path(
    package: PilotGisPackageConfig,
    output_dir: Path,
    prefix: str,
) -> Path:
    return package.package_manifest_json or output_dir / f"{prefix}_pilot_gis_package_manifest.json"


def write_map_package_manifest(
    path: Path,
    map_package: HazardMapPackageState,
    hazard_manifest_path: Path,
    layer_semantics: list[dict[str, Any]],
    raster_outputs: list[dict[str, Any]],
    output_file_metadata: dict[Path, dict[str, Any]],
    output_write_kind_seconds: dict[str, float],
    output_write_kind_bytes: dict[str, int],
) -> float:
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
    serialization_started = time.perf_counter()
    text = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    serialization_seconds = time.perf_counter() - serialization_started
    write_file_text(
        path,
        text,
        "json",
        output_file_metadata,
        output_write_kind_seconds,
        output_write_kind_bytes,
        elapsed_seconds=0.0,
    )
    return serialization_seconds


def write_pilot_gis_package_manifest(
    path: Path,
    package: PilotGisPackageConfig,
    hazard_manifest_path: Path,
    hazard_manifest: dict[str, Any],
    output_file_metadata: dict[Path, dict[str, Any]],
    output_write_kind_seconds: dict[str, float],
    output_write_kind_bytes: dict[str, int],
) -> float:
    outputs = hazard_manifest.get("outputs", [])
    geotiff_outputs = geotiff_raster_outputs(outputs)
    parity_outputs = [
        compact_output_manifest_entry(output)
        for output in outputs
        if output.get("format") in {"csv_grid", "esri_ascii_grid"}
    ]
    manifest_outputs = [
        compact_output_manifest_entry(output)
        for output in outputs
        if output.get("kind") in {"hazard_metadata", "map_package_manifest"}
    ]
    curve_outputs = [
        compact_output_manifest_entry(output)
        for output in outputs
        if output.get("kind") == "conditional_intensity_exceedance_curves"
    ]
    source_zone_context = [
        input_artifact_entry(path, "source_zone_context", path.suffix.lstrip(".") or "unknown")
        for path in package.source_zone_context_paths
    ]
    terrain = hazard_manifest.get("terrain") or {}
    terrain_metadata_path = terrain.get("metadata_path")
    terrain_metadata = (
        input_artifact_entry(ROOT / str(terrain_metadata_path), "terrain_metadata", "yaml")
        if terrain_metadata_path
        else None
    )
    review_status = {
        "status": package.visual_qa_status,
        "note": package.visual_qa_note,
        "reviewed_artifacts": list(package.reviewed_artifacts),
        "acceptance_scope": "local diagnostic GIS/QGIS review only",
        "accepted_for_operational_use": False,
    }
    manifest = {
        "schema_version": "pilot_gis_package_manifest_v1",
        "package_version": "pilot_gis_package_v1",
        "case_id": hazard_manifest.get("case_id"),
        "operational_status": "research_diagnostic",
        "hazard_manifest_paths": [str(hazard_manifest_path)],
        "raster_outputs": geotiff_outputs,
        "parity_outputs": parity_outputs,
        "manifest_outputs": manifest_outputs,
        "conditional_intensity_exceedance_curve_outputs": curve_outputs,
        "source_zone_context": source_zone_context,
        "terrain_metadata": terrain_metadata,
        "grid": hazard_manifest.get("grid"),
        "terrain": terrain,
        "raster_contract": {
            "geotiff_required": True,
            "cloud_optimized": False,
            "qgis_project_included": False,
            "geopackage_included": False,
            "csv_ascii_parity_required": True,
        },
        "probability_claim_boundary": {
            "annualized": False,
            "current_allowed_product_labels": [
                "unweighted_diagnostic",
                "sampling_weighted_conditional",
                "conditional_intensity_exceedance",
            ],
            "future_unsupported_product_labels": [
                "physical_probability",
                "annual_intensity_frequency",
                "return_period",
                "risk_map",
                "operational_hazard_map",
            ],
        },
        "visual_qa": review_status,
        "limitations": [
            "Local diagnostic review package only; not an operational hazard map.",
            "GeoTIFF rasters are uncompressed review rasters, not verified Cloud-Optimized GeoTIFFs.",
            "Current probability layers are conditional diagnostics, not annual frequencies or return-period products.",
            "Exposure, vulnerability, consequences, expected loss, and risk modelling are out of scope.",
        ],
    }
    serialization_started = time.perf_counter()
    text = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    serialization_seconds = time.perf_counter() - serialization_started
    write_file_text(
        path,
        text,
        "json",
        output_file_metadata,
        output_write_kind_seconds,
        output_write_kind_bytes,
        elapsed_seconds=0.0,
    )
    return serialization_seconds


def compact_output_manifest_entry(output: dict[str, Any]) -> dict[str, Any]:
    return {
        "kind": output.get("kind"),
        "format": output.get("format"),
        "path": output.get("path"),
        "sha256": output.get("sha256"),
        "total_bytes": output.get("total_bytes"),
        "layer_name": output.get("layer_name"),
    }


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
    conditional_curve_export: ConditionalCurveExportConfig,
    *,
    total_wall_seconds: float,
    accumulation_seconds: float,
    core_output_write_seconds: float,
    plot_render_seconds: float,
    plots_enabled: bool,
    input_file_counts: dict[str, int],
    bounds_stats: BoundsDiscoveryStats,
    timings: HazardAccumulationTimings,
    output_file_metadata: dict[Path, dict[str, Any]],
) -> dict[str, Any]:
    outputs: list[dict[str, Any]] = []
    for layer in layers:
        if raster_exports.grid_csv_export == "full":
            outputs.append(
                output_manifest_entry(
                    output_dir / f"{prefix}_{layer.key}.csv",
                    "hazard_layer",
                    "csv_grid",
                    output_file_metadata=output_file_metadata,
                )
            )
        outputs.append(
            output_manifest_entry(
                output_dir / f"{prefix}_{layer.key}.asc",
                "hazard_layer",
                "esri_ascii_grid",
                output_file_metadata=output_file_metadata,
            )
        )
        if raster_exports.geotiff:
            outputs.append(
                geotiff_output_manifest_entry(
                    output_dir / f"{prefix}_{layer.key}.tif",
                    layer,
                    grid,
                    case,
                    output_file_metadata=output_file_metadata,
                )
            )
    curves = metadata.get("conditional_intensity_exceedance_curves") or {}
    if curves.get("enabled") and conditional_curve_export.write_table:
        outputs.append(
            output_manifest_entry(
                output_dir / f"{prefix}_conditional_intensity_exceedance_curves.csv",
                "conditional_intensity_exceedance_curves",
                "csv_table",
                output_file_metadata=output_file_metadata,
            )
        )
    outputs.append(
        output_manifest_entry(
            output_dir / f"{prefix}_deposition_points.geojson",
            "deposition_points",
            "geojson",
            output_file_metadata=output_file_metadata,
        )
    )
    outputs.append(
        output_manifest_entry(
            output_dir / f"{prefix}_metadata.json",
            "hazard_metadata",
            "json",
            output_file_metadata=output_file_metadata,
        )
    )
    if plots_enabled:
        outputs.append(
            output_manifest_entry(
                output_dir / "index.html",
                "hazard_report",
                "html",
                output_file_metadata=output_file_metadata,
            )
        )
    for layer_key, filename in sorted(plot_paths.items()):
        outputs.append(
            output_manifest_entry(
                output_dir / filename,
                f"{layer_key}_plot",
                "png",
                output_file_metadata=output_file_metadata,
            )
        )

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
            "generated_layer_names": [
                layer.key for layer in layers if "exceedance" in layer.key or layer.key.endswith("_standard_error")
            ],
        },
        "hazard_probability": (
            probability.as_manifest([layer.key for layer in layers if layer.key.startswith("weighted_")])
            if probability
            else None
        ),
        "hazard_map_package": hazard_map_package_manifest_section(map_package, probability) if map_package else None,
        "conditional_intensity_exceedance_curves": metadata.get("conditional_intensity_exceedance_curves", {}),
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


def update_conditional_execution_manifest(
    manifest: dict[str, Any],
    grid: GridSpec,
    conditional_curve_export: ConditionalCurveExportConfig,
    reducer_execution: dict[str, Any] | None,
    raster_export_config: RasterExportConfig,
) -> None:
    curves = manifest.get("conditional_intensity_exceedance_curves") or {}
    performance = manifest.get("performance") or {}
    outputs = manifest.get("outputs") or []
    if reducer_execution is None:
        reducer = {
            "mode": "serial",
            "worker_count": 1,
            "chunk_count": 1,
            "chunk_manifest_count": 0,
            "merge_order": "single_serial_accumulator",
            "merge_order_independent": True,
            "chunk_ids": [],
        }
    else:
        reducer = {
            "mode": reducer_execution.get("mode"),
            "worker_count": reducer_execution.get("worker_count"),
            "chunk_count": reducer_execution.get("chunk_count"),
            "chunk_manifest_count": sum(1 for output in outputs if output.get("kind") == "reducer_chunk_manifest"),
            "merge_order": reducer_execution.get("merge_order"),
            "merge_order_independent": reducer_execution.get("merge_order_independent"),
            "chunk_ids": list(reducer_execution.get("chunk_ids") or []),
        }
    manifest["conditional_execution"] = {
        "schema_version": "conditional_hazard_execution_diagnostics_v1",
        "product_modes": [
            "unweighted_diagnostic",
            "sampling_weighted_conditional",
            "conditional_intensity_exceedance",
        ],
        "annualized": False,
        "physical_probability": False,
        "risk_or_exposure": False,
        "grid_cell_count": grid.ncols * grid.nrows,
        "conditional_curve_export": {
            "mode": conditional_curve_export.mode,
            "csv_table_written": conditional_curve_export.write_table,
            "row_count": int(curves.get("row_count", 0) or 0),
            "table_suppressed_for_output_budget": bool(
                curves.get("enabled") and not conditional_curve_export.write_table
            ),
        },
        "raster_exports": {
            "grid_csv_export": raster_export_config.grid_csv_export,
            "grid_csv_written": raster_export_config.grid_csv_export == "full",
            "geotiff": raster_export_config.geotiff,
        },
        "reducer": reducer,
        "output_budget": {
            "output_file_count": int(performance.get("output_file_count", 0) or 0),
            "output_bytes": int(performance.get("output_bytes", 0) or 0),
            "summary_only_curve_export_required_for_scale_up": True,
            "generated_outputs_should_remain_ignored": True,
        },
        "convergence_diagnostics": {
            "probability_standard_error_layers_present": any(
                output.get("path", "").endswith("_standard_error.csv") for output in outputs
            ),
            "requires_trajectory_count_sensitivity_before_scale_up": True,
            "requires_worker_count_reducer_parity_before_scale_up": True,
        },
        "limitations": [
            "Conditional research diagnostics only.",
            "No annual frequency, physical probability, return-period, risk, or operational semantics are included.",
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


def output_manifest_entry(
    path: Path,
    kind: str,
    format_name: str,
    *,
    output_file_metadata: dict[Path, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    metadata = output_file_metadata.get(path) if output_file_metadata else None
    total_bytes = metadata.get("total_bytes") if metadata is not None else None
    sha256 = metadata.get("sha256") if metadata is not None else None
    if total_bytes is None:
        total_bytes = path.stat().st_size if path.exists() else 0
    if sha256 is None and path.exists() and path.is_file():
        sha256 = sha256_file(path)
    return {
        "kind": kind,
        "format": format_name,
        "path": str(path),
        "file_count": 1,
        "total_bytes": total_bytes,
        "sha256": sha256,
        "row_count": None,
        "skipped_empty_files": None,
    }


def geotiff_output_manifest_entry(
    path: Path,
    layer: RasterLayer,
    grid: GridSpec,
    case: dict[str, Any],
    *,
    output_file_metadata: dict[Path, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    entry = output_manifest_entry(path, "hazard_layer", "geotiff", output_file_metadata=output_file_metadata)
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
        "reach_probability_standard_error",
        "max_kinetic_energy",
        "max_jump_height",
    } or "exceedance" in layer_key:
        return "trajectory_csv"
    if layer_key in {"deposition_density", "weighted_deposition_density"}:
        return "ensemble_deposition_csv"
    if layer_key == "significant_impact_density" or layer_key == "weighted_significant_impact_density":
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
            "weighted_deposition_density",
            "significant_impact_density",
            "weighted_significant_impact_density",
        } or "exceedance" in layer.key:
            maximum = summary["maximum"]
            minimum = summary["minimum"]
            if isinstance(maximum, float) and maximum > 1.0 + 1e-12:
                warnings.append(f"{layer.key} has values greater than 1.0")
            if isinstance(minimum, float) and minimum < -1e-12:
                warnings.append(f"{layer.key} has negative values")
    return warnings


def render_png_layers(
    output_dir: Path,
    prefix: str,
    grid: GridSpec,
    layers: list[RasterLayer],
    output_file_metadata: dict[Path, dict[str, Any]],
    output_write_kind_seconds: dict[str, float],
    output_write_kind_bytes: dict[str, int],
) -> dict[str, str]:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt  # type: ignore
    except ImportError:
        return {}

    plot_paths: dict[str, str] = {}
    extent = [grid.xmin, grid.xmax, grid.ymin, grid.ymax]
    for layer in layers:
        started = time.perf_counter()
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
        _register_written_output(
            path,
            "png",
            output_file_metadata,
            output_write_kind_seconds,
            output_write_kind_bytes,
            elapsed_seconds=time.perf_counter() - started,
            total_bytes=path.stat().st_size,
            sha256_hex=sha256_file(path),
        )
        plot_paths[layer.key] = path.name
    return plot_paths


def write_html_report(
    path: Path,
    case: dict[str, Any],
    metadata: dict[str, Any],
    layers: list[RasterLayer],
    plot_paths: dict[str, str],
    prefix: str,
    output_file_metadata: dict[Path, dict[str, Any]],
    output_write_kind_seconds: dict[str, float],
    output_write_kind_bytes: dict[str, int],
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
    <li><strong>Deposition density</strong>: final-position density from ensemble deposition points. Weighted deposition density is normalized by filtered sampling weight when <code>hazard_probability</code> is configured.</li>
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
    write_file_text(
        path,
        content,
        "html",
        output_file_metadata,
        output_write_kind_seconds,
        output_write_kind_bytes,
        elapsed_seconds=0.0,
    )


def write_file_text(
    path: Path,
    text: str,
    kind: str,
    output_file_metadata: dict[Path, dict[str, Any]],
    output_write_kind_seconds: dict[str, float],
    output_write_kind_bytes: dict[str, int],
    *,
    elapsed_seconds: float,
) -> None:
    started = time.perf_counter()
    data = text.encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    _register_written_output(
        path,
        kind,
        output_file_metadata,
        output_write_kind_seconds,
        output_write_kind_bytes,
        elapsed_seconds=elapsed_seconds + (time.perf_counter() - started),
        total_bytes=len(data),
        sha256_hex=_safe_sha256_hex(data),
    )


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
