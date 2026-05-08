#!/usr/bin/env python3
"""Dry-runnable DEM and terrain-representation sensitivity fixture.

The script derives deterministic terrain variants from a small ESRI ASCII DEM
and writes comparison diagnostics plus a report template into a user-provided
output directory. It does not run the simulator or tune contact parameters.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


SCHEMA_VERSION = "dem_terrain_sensitivity_summary_v1"
DEFAULT_SOURCE_DEM = Path("validation/data/processed/swisstopo_pilot/swissalti3d_pilot_crop.asc")
NO_TUNING_WARNING = (
    "Do not tune restitution, friction, roughness, scarring, terrain-class, "
    "release-condition, or other contact parameters to compensate for DEM or "
    "terrain-representation effects."
)


class DemSensitivityError(ValueError):
    """Raised when the dry-run fixture inputs are invalid."""


@dataclass(frozen=True)
class AsciiDem:
    ncols: int
    nrows: int
    xllcorner: float
    yllcorner: float
    cellsize: float
    nodata_value: float
    values: list[list[float]]

    @property
    def header(self) -> dict[str, float | int]:
        return {
            "ncols": self.ncols,
            "nrows": self.nrows,
            "xllcorner": self.xllcorner,
            "yllcorner": self.yllcorner,
            "cellsize": self.cellsize,
            "NODATA_value": self.nodata_value,
        }

    def is_nodata(self, value: float) -> bool:
        if math.isnan(self.nodata_value):
            return math.isnan(value)
        return value == self.nodata_value


def read_ascii_dem(path: Path) -> AsciiDem:
    with path.open("r", encoding="utf-8") as handle:
        header_lines = [handle.readline() for _ in range(6)]
        rows = [line.strip() for line in handle if line.strip()]

    header: dict[str, float] = {}
    for line in header_lines:
        parts = line.split()
        if len(parts) != 2:
            raise DemSensitivityError(f"invalid ESRI ASCII header line in {path}: {line.strip()}")
        header[parts[0].lower()] = float(parts[1])

    required = {"ncols", "nrows", "xllcorner", "yllcorner", "cellsize", "nodata_value"}
    missing = required.difference(header)
    if missing:
        raise DemSensitivityError(f"DEM header is missing {sorted(missing)}: {path}")

    ncols = int(header["ncols"])
    nrows = int(header["nrows"])
    values = [[float(item) for item in row.split()] for row in rows]
    if len(values) != nrows:
        raise DemSensitivityError(f"DEM has {len(values)} rows, expected {nrows}: {path}")
    for row_index, row in enumerate(values):
        if len(row) != ncols:
            raise DemSensitivityError(
                f"DEM row {row_index} has {len(row)} columns, expected {ncols}: {path}"
            )

    return AsciiDem(
        ncols=ncols,
        nrows=nrows,
        xllcorner=header["xllcorner"],
        yllcorner=header["yllcorner"],
        cellsize=header["cellsize"],
        nodata_value=header["nodata_value"],
        values=values,
    )


def write_ascii_dem(path: Path, dem: AsciiDem, values: list[list[float]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        handle.write(f"ncols {dem.ncols}\n")
        handle.write(f"nrows {dem.nrows}\n")
        handle.write(f"xllcorner {format_number(dem.xllcorner)}\n")
        handle.write(f"yllcorner {format_number(dem.yllcorner)}\n")
        handle.write(f"cellsize {format_number(dem.cellsize)}\n")
        handle.write(f"NODATA_value {format_number(dem.nodata_value)}\n")
        for row in values:
            handle.write(" ".join(format_number(value) for value in row))
            handle.write("\n")


def format_number(value: float) -> str:
    if float(value).is_integer():
        return str(int(value))
    return f"{value:.6f}".rstrip("0").rstrip(".")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def smooth_3x3_mean(dem: AsciiDem) -> list[list[float]]:
    smoothed: list[list[float]] = []
    for row_index, row in enumerate(dem.values):
        smoothed_row: list[float] = []
        for col_index, value in enumerate(row):
            if dem.is_nodata(value):
                smoothed_row.append(dem.nodata_value)
                continue
            neighbours = list(valid_neighbour_values(dem, row_index, col_index, radius=1))
            smoothed_row.append(sum(neighbours) / len(neighbours))
        smoothed.append(smoothed_row)
    return smoothed


def coarsen_2x2_mean_reexpand(dem: AsciiDem) -> list[list[float]]:
    reexpanded = [[dem.nodata_value for _ in range(dem.ncols)] for _ in range(dem.nrows)]
    for row_start in range(0, dem.nrows, 2):
        for col_start in range(0, dem.ncols, 2):
            cells: list[float] = []
            for row_index in range(row_start, min(row_start + 2, dem.nrows)):
                for col_index in range(col_start, min(col_start + 2, dem.ncols)):
                    value = dem.values[row_index][col_index]
                    if not dem.is_nodata(value):
                        cells.append(value)
            block_value = sum(cells) / len(cells) if cells else dem.nodata_value
            for row_index in range(row_start, min(row_start + 2, dem.nrows)):
                for col_index in range(col_start, min(col_start + 2, dem.ncols)):
                    source_value = dem.values[row_index][col_index]
                    reexpanded[row_index][col_index] = (
                        dem.nodata_value if dem.is_nodata(source_value) else block_value
                    )
    return reexpanded


def valid_neighbour_values(
    dem: AsciiDem, row_index: int, col_index: int, radius: int
) -> Iterable[float]:
    for neighbour_row in range(max(0, row_index - radius), min(dem.nrows, row_index + radius + 1)):
        for neighbour_col in range(
            max(0, col_index - radius), min(dem.ncols, col_index + radius + 1)
        ):
            value = dem.values[neighbour_row][neighbour_col]
            if not dem.is_nodata(value) and math.isfinite(value):
                yield value


def slope_proxy_grid(dem: AsciiDem, values: list[list[float]]) -> list[list[float | None]]:
    slopes: list[list[float | None]] = []
    for row_index, row in enumerate(values):
        slope_row: list[float | None] = []
        for col_index, value in enumerate(row):
            if dem.is_nodata(value) or not math.isfinite(value):
                slope_row.append(None)
                continue
            max_delta = 0.0
            has_neighbour = False
            for neighbour_row in range(max(0, row_index - 1), min(dem.nrows, row_index + 2)):
                for neighbour_col in range(max(0, col_index - 1), min(dem.ncols, col_index + 2)):
                    if neighbour_row == row_index and neighbour_col == col_index:
                        continue
                    neighbour = values[neighbour_row][neighbour_col]
                    if dem.is_nodata(neighbour) or not math.isfinite(neighbour):
                        continue
                    distance_cells = math.hypot(neighbour_row - row_index, neighbour_col - col_index)
                    if distance_cells == 0.0:
                        continue
                    max_delta = max(max_delta, abs(neighbour - value) / (distance_cells * dem.cellsize))
                    has_neighbour = True
            slope_row.append(max_delta if has_neighbour else None)
        slopes.append(slope_row)
    return slopes


def compare_to_baseline(
    dem: AsciiDem, baseline: list[list[float]], variant: list[list[float]]
) -> dict[str, float | int]:
    compared = 0
    nodata_mismatch = 0
    sum_delta = 0.0
    sum_abs_delta = 0.0
    sum_sq_delta = 0.0
    max_abs_delta = 0.0

    baseline_slope = slope_proxy_grid(dem, baseline)
    variant_slope = slope_proxy_grid(dem, variant)
    slope_compared = 0
    slope_sum_abs_delta = 0.0
    slope_sum_sq_delta = 0.0
    slope_max_abs_delta = 0.0

    for row_index in range(dem.nrows):
        for col_index in range(dem.ncols):
            base = baseline[row_index][col_index]
            other = variant[row_index][col_index]
            base_nodata = dem.is_nodata(base)
            other_nodata = dem.is_nodata(other)
            if base_nodata != other_nodata:
                nodata_mismatch += 1
                continue
            if base_nodata or not math.isfinite(base) or not math.isfinite(other):
                continue
            delta = other - base
            compared += 1
            sum_delta += delta
            sum_abs_delta += abs(delta)
            sum_sq_delta += delta * delta
            max_abs_delta = max(max_abs_delta, abs(delta))

            base_slope = baseline_slope[row_index][col_index]
            other_slope = variant_slope[row_index][col_index]
            if base_slope is not None and other_slope is not None:
                slope_delta = other_slope - base_slope
                slope_compared += 1
                slope_sum_abs_delta += abs(slope_delta)
                slope_sum_sq_delta += slope_delta * slope_delta
                slope_max_abs_delta = max(slope_max_abs_delta, abs(slope_delta))

    return {
        "compared_cell_count": compared,
        "nodata_mismatch_count": nodata_mismatch,
        "mean_elevation_delta_m": sum_delta / compared if compared else 0.0,
        "mean_abs_elevation_delta_m": sum_abs_delta / compared if compared else 0.0,
        "max_abs_elevation_delta_m": max_abs_delta,
        "rmse_elevation_delta_m": math.sqrt(sum_sq_delta / compared) if compared else 0.0,
        "slope_proxy_compared_cell_count": slope_compared,
        "mean_abs_slope_proxy_delta": (
            slope_sum_abs_delta / slope_compared if slope_compared else 0.0
        ),
        "max_abs_slope_proxy_delta": slope_max_abs_delta,
        "rmse_slope_proxy_delta": (
            math.sqrt(slope_sum_sq_delta / slope_compared) if slope_compared else 0.0
        ),
    }


def build_summary(source_dem: Path, output_dir: Path) -> dict[str, object]:
    dem = read_ascii_dem(source_dem)
    output_dir.mkdir(parents=True, exist_ok=True)
    variants_dir = output_dir / "terrain_variants"
    variants_dir.mkdir(parents=True, exist_ok=True)

    variants = [
        {
            "id": "baseline",
            "description": "Byte-preserved copy of the source DEM.",
            "method": "copy",
            "values": dem.values,
        },
        {
            "id": "smooth_3x3_mean",
            "description": "3x3 mean smoothing with nodata excluded and source nodata preserved.",
            "method": "3x3_mean_valid_cells",
            "values": smooth_3x3_mean(dem),
        },
        {
            "id": "coarsen_2x2_mean_reexpanded",
            "description": "2x2 valid-cell mean aggregation reexpanded to the source grid.",
            "method": "2x2_mean_valid_cells_reexpanded_to_source_grid",
            "values": coarsen_2x2_mean_reexpand(dem),
        },
    ]

    variant_metadata: list[dict[str, object]] = []
    baseline_values = dem.values
    pairwise_metrics: list[dict[str, object]] = []
    for variant in variants:
        variant_id = str(variant["id"])
        output_path = variants_dir / f"{variant_id}.asc"
        if variant_id == "baseline":
            shutil.copyfile(source_dem, output_path)
        else:
            write_ascii_dem(output_path, dem, variant["values"])  # type: ignore[arg-type]
        variant_metadata.append(
            {
                "id": variant_id,
                "path": str(output_path),
                "sha256": sha256_file(output_path),
                "description": variant["description"],
                "method": variant["method"],
                "same_grid_as_source": True,
                "nodata_policy": "source nodata cells preserved; nodata excluded from local means",
            }
        )
        if variant_id != "baseline":
            pairwise_metrics.append(
                {
                    "baseline_variant": "baseline",
                    "comparison_variant": variant_id,
                    "metrics": compare_to_baseline(
                        dem, baseline_values, variant["values"]  # type: ignore[arg-type]
                    ),
                }
            )

    summary: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "source_dem": {
            "path": str(source_dem),
            "sha256": sha256_file(source_dem),
            "format": "ESRI ASCII grid",
            "header": dem.header,
        },
        "terrain_variants": variant_metadata,
        "invariants": {
            "simulation_physics_changed": False,
            "simulation_defaults_changed": False,
            "validation_baselines_changed": False,
            "hazard_semantics_changed": False,
            "contact_parameter_tuning_allowed": False,
            "note": NO_TUNING_WARNING,
        },
        "pairwise_baseline_comparisons": pairwise_metrics,
        "diagnostic_scope": (
            "Terrain preprocessing and map-difference metrics only; no simulator "
            "execution, calibration, operational validation, annual-frequency, or risk claim."
        ),
    }
    summary_path = output_dir / "dem_terrain_sensitivity_summary.json"
    with summary_path.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, sort_keys=True)
        handle.write("\n")

    report_path = output_dir / "dem_terrain_sensitivity_report.md"
    report_path.write_text(render_report(summary, summary_path, report_path), encoding="utf-8")
    return summary


def render_report(summary: dict[str, object], summary_path: Path, report_path: Path) -> str:
    source = summary["source_dem"]  # type: ignore[index]
    variants = summary["terrain_variants"]  # type: ignore[index]
    comparisons = summary["pairwise_baseline_comparisons"]  # type: ignore[index]
    lines = [
        "# DEM Terrain Sensitivity Report",
        "",
        "Status: dry-runnable fixture report. This report compares terrain representations only.",
        "",
        f"> {NO_TUNING_WARNING}",
        "",
        "## Terrain Representation Inventory",
        "",
        "| Variant | Method | Same grid | Nodata policy | Output |",
        "| --- | --- | --- | --- | --- |",
    ]
    for variant in variants:  # type: ignore[assignment]
        lines.append(
            "| {id} | {method} | {same_grid_as_source} | {nodata_policy} | `{path}` |".format(
                **variant
            )
        )

    lines.extend(
        [
            "",
            "## Invariant Configuration",
            "",
            "| Invariant | Value |",
            "| --- | --- |",
            "| Simulation physics changed | false |",
            "| Simulation defaults changed | false |",
            "| Validation baselines changed | false |",
            "| Hazard semantics changed | false |",
            "| Contact-parameter tuning allowed | false |",
            "",
            "## Command Log",
            "",
            "| Item | Value |",
            "| --- | --- |",
            f"| Source DEM | `{source['path']}` |",  # type: ignore[index]
            f"| Summary JSON | `{summary_path}` |",
            f"| Report | `{report_path}` |",
            "",
            "## Metric Comparison",
            "",
            "| Comparison | Cells | Mean delta m | Mean abs delta m | Max abs delta m | RMSE delta m | Mean abs slope-proxy delta | Nodata mismatches |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for comparison in comparisons:  # type: ignore[assignment]
        metrics = comparison["metrics"]
        lines.append(
            "| {baseline_variant} vs {comparison_variant} | {compared_cell_count} | {mean_elevation_delta_m:.6f} | {mean_abs_elevation_delta_m:.6f} | {max_abs_elevation_delta_m:.6f} | {rmse_elevation_delta_m:.6f} | {mean_abs_slope_proxy_delta:.6f} | {nodata_mismatch_count} |".format(
                baseline_variant=comparison["baseline_variant"],
                comparison_variant=comparison["comparison_variant"],
                **metrics,
            )
        )

    lines.extend(
        [
            "",
            "## Gate Table",
            "",
            "| Gate | Status | Required note |",
            "| --- | --- | --- |",
            "| Deterministic terrain variants | pass | Variants are derived by fixed local mean operations. |",
            "| Same-grid comparison | pass | All outputs preserve source extent, cell size, dimensions, and nodata value. |",
            "| Metric diagnostics | pass | Elevation, slope-proxy, and nodata-mismatch metrics are written to JSON. |",
            "| Variant invariants | pass | No simulator physics, defaults, validation baselines, or hazard semantics changed. |",
            "| Interpretation boundary | pass | Terrain sensitivity only; no operational validation, annual-frequency, or risk claim. |",
            "",
            "## Limitations",
            "",
            "- This dry run does not execute trajectories or hazard-layer reducers.",
            "- The default fixture is tiny and deterministic; it tests workflow mechanics, not Swiss terrain representativeness.",
            "- Slope proxy is a local map-difference diagnostic, not the simulator normal calculation.",
            "- swisstopo-style terrain inputs are operational geodata context, not validation evidence by themselves.",
            "",
            "## No-Tuning Warning",
            "",
            NO_TUNING_WARNING,
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate deterministic DEM terrain-sensitivity variants and diagnostics."
    )
    parser.add_argument(
        "--source-dem",
        type=Path,
        default=DEFAULT_SOURCE_DEM,
        help=f"ESRI ASCII DEM fixture or user-supplied DEM crop (default: {DEFAULT_SOURCE_DEM})",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory for generated variants, summary JSON, and report Markdown.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.source_dem.exists():
        raise SystemExit(f"source DEM does not exist: {args.source_dem}")
    summary = build_summary(args.source_dem, args.output_dir)
    print(args.output_dir / "dem_terrain_sensitivity_summary.json")
    print(args.output_dir / "dem_terrain_sensitivity_report.md")
    print(summary["invariants"]["note"])  # type: ignore[index]
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
