#!/usr/bin/env python3
"""Create validation-ready derived files from downloaded public datasets.

This script never overwrites raw data. Dataset-specific scientific conversions are
added incrementally as schemas are stabilized; the current implementation provides
safe archive inventories and regenerates the small synthetic fixture.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import statistics
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TSCHAMUT_VALIDATION_RUN_LIMIT = 10


def write_synthetic_fixture() -> None:
    for out in (
        ROOT / "data" / "processed" / "synthetic_plane_basic",
        ROOT / "validation" / "data" / "processed" / "synthetic_plane_basic",
    ):
        out.mkdir(parents=True, exist_ok=True)
        write_csv(
            out / "observed_deposition.csv",
            ["trajectory_id", "experiment_id", "x_m", "y_m", "z_m"],
            [["synthetic_plane_001", "synthetic_plane_basic", "0.2", "0.0", "0.5"]],
        )
        write_csv(
            out / "release_points.csv",
            ["trajectory_id", "experiment_id", "x_m", "y_m", "z_m", "vx_mps", "vy_mps", "vz_mps"],
            [["synthetic_plane_001", "synthetic_plane_basic", "0.0", "0.0", "0.5", "1.0", "0.0", "0.0"]],
        )
        write_csv(
            out / "block_metadata.csv",
            ["block_id", "mass_kg", "radius_m", "shape_class"],
            [["synthetic_sphere_001", "10.0", "0.5", "sphere"]],
        )


def write_csv(path: Path, header: list[str], rows: list[list[str]]) -> None:
    with path.open("w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(header)
        writer.writerows(rows)


def inventory_archives(dataset_id: str) -> None:
    raw_dir = ROOT / "data" / "raw" / dataset_id
    processed_dir = ROOT / "data" / "processed" / dataset_id
    validation_id = "tschamut" if dataset_id == "tschamut2014" else dataset_id
    validation_processed_dir = ROOT / "validation" / "data" / "processed" / validation_id
    processed_dir.mkdir(parents=True, exist_ok=True)
    validation_processed_dir.mkdir(parents=True, exist_ok=True)
    records = []
    for archive in sorted(raw_dir.glob("*.zip")):
        with zipfile.ZipFile(archive) as zf:
            for info in zf.infolist():
                records.append(
                    {
                        "archive": str(archive.relative_to(ROOT)),
                        "member": info.filename,
                        "compressed_size": info.compress_size,
                        "size": info.file_size,
                    }
                )
    if records:
        inventory = json.dumps(records, indent=2)
        (processed_dir / "archive_inventory.json").write_text(inventory)
        (validation_processed_dir / "archive_inventory.json").write_text(inventory)
        print(f"wrote {processed_dir / 'archive_inventory.json'}")
        print(f"wrote {validation_processed_dir / 'archive_inventory.json'}")
    else:
        print(f"no ZIP archives found under {raw_dir}")


def preprocess_tschamut2014() -> None:
    raw_dir = ROOT / "data" / "raw" / "tschamut2014"
    overview_archive = raw_dir / "overviewalltests.zip"
    lps_archive = raw_dir / "trajectoriesfromlps.zip"
    if not overview_archive.exists() or not lps_archive.exists():
        raise SystemExit(
            "missing Tschamut raw archives; run "
            "`python3 scripts/download_datasets.py --dataset tschamut2014 "
            "--resource overview_tests --resource lps_trajectories` first"
        )

    overview = read_tschamut_overview(overview_archive)
    trajectories = read_tschamut_lps_trajectories(lps_archive)
    plane = fit_plane_from_points(
        [
            (sample["x_m"], sample["y_m"], sample["ground_z_m"])
            for samples in trajectories.values()
            for sample in samples
        ]
    )

    processed_dir = ROOT / "data" / "processed" / "tschamut2014"
    validation_dir = ROOT / "validation" / "data" / "processed" / "tschamut"
    processed_dir.mkdir(parents=True, exist_ok=True)
    validation_dir.mkdir(parents=True, exist_ok=True)

    full_release_rows, full_deposition_rows, block_rows = tschamut_rows(
        trajectories, overview, plane
    )
    validation_ids = [row[0] for row in full_release_rows[:TSCHAMUT_VALIDATION_RUN_LIMIT]]
    validation_release_rows = [row for row in full_release_rows if row[0] in validation_ids]
    validation_deposition_rows = [row for row in full_deposition_rows if row[0] in validation_ids]

    release_header = [
        "trajectory_id",
        "experiment_id",
        "x_m",
        "y_m",
        "z_m",
        "ground_z_m",
        "vx_mps",
        "vy_mps",
        "vz_mps",
        "block_id",
        "mass_kg",
        "radius_m",
        "source",
    ]
    deposition_header = [
        "trajectory_id",
        "experiment_id",
        "x_m",
        "y_m",
        "z_m",
        "ground_z_m",
        "release_x_m",
        "release_y_m",
        "release_z_m",
        "observed_runout_m",
        "block_id",
        "mass_kg",
        "radius_m",
        "source",
    ]
    block_header = ["block_id", "name", "mass_kg", "radius_m", "size_x_m", "size_y_m", "size_z_m"]

    write_csv(processed_dir / "release_points.csv", release_header, full_release_rows)
    write_csv(processed_dir / "observed_deposition.csv", deposition_header, full_deposition_rows)
    write_csv(processed_dir / "block_metadata.csv", block_header, block_rows)
    write_tschamut_terrain(processed_dir / "terrain.asc", trajectories, plane)
    write_tschamut_metadata(
        processed_dir / "metadata.json",
        plane,
        len(full_release_rows),
        len(validation_release_rows),
    )

    write_csv(validation_dir / "release_points.csv", release_header, validation_release_rows)
    write_csv(validation_dir / "observed_deposition.csv", deposition_header, validation_deposition_rows)
    write_csv(validation_dir / "block_metadata.csv", block_header, block_rows)
    write_tschamut_terrain(validation_dir / "terrain.asc", trajectories, plane)
    write_tschamut_metadata(
        validation_dir / "metadata.json",
        plane,
        len(full_release_rows),
        len(validation_release_rows),
    )
    print(f"wrote Tschamut processed data to {processed_dir}")
    print(f"wrote Tschamut validation subset to {validation_dir}")


def read_tschamut_overview(path: Path) -> dict[str, dict[str, float | str]]:
    with zipfile.ZipFile(path) as archive:
        text = archive.read("OverviewAllTests.txt").decode("utf-8-sig", errors="replace")
    rows = list(csv.reader(text.splitlines(), delimiter="\t"))
    records: dict[str, dict[str, float | str]] = {}
    for row in rows[6:]:
        if len(row) < 25:
            continue
        try:
            test_no = int(row[0])
            mass_kg = float(row[6])
            sizes_m = [float(row[index]) / 100.0 for index in (7, 8, 9)]
        except ValueError:
            continue
        radius_m = 0.5 * statistics.fmean(sizes_m)
        records[f"v{test_no:03}"] = {
            "test_no": test_no,
            "block_id": str(row[4]).strip() or f"block_{test_no}",
            "block_name": str(row[5]).strip() or "unknown",
            "mass_kg": mass_kg,
            "radius_m": radius_m,
            "size_x_m": sizes_m[0],
            "size_y_m": sizes_m[1],
            "size_z_m": sizes_m[2],
        }
    return records


def read_tschamut_lps_trajectories(path: Path) -> dict[str, list[dict[str, float]]]:
    with zipfile.ZipFile(path) as archive:
        text = archive.read("all_LPS_splined.txt").decode("utf-8-sig", errors="replace")
    trajectories: dict[str, list[dict[str, float]]] = {}
    current: str | None = None
    for row in csv.reader(text.splitlines(), delimiter="\t"):
        if not row:
            continue
        match = re.match(r"v(\d+)_LPS_splined\.txt", row[0].strip())
        if match:
            current = f"v{int(match.group(1)):03}"
            trajectories[current] = []
            continue
        if current is None or len(row) < 20 or not row[1].strip():
            continue
        try:
            trajectories[current].append(
                {
                    "time_s": float(row[1]),
                    "x_m": float(row[6]),
                    "y_m": float(row[7]),
                    "ground_z_m": float(row[8]) - 1600.0,
                    "vx_mps": float(row[15]),
                    "vy_mps": float(row[16]),
                    "vz_mps": float(row[17]),
                }
            )
        except ValueError:
            continue
    return {key: value for key, value in trajectories.items() if value}


def tschamut_rows(
    trajectories: dict[str, list[dict[str, float]]],
    overview: dict[str, dict[str, float | str]],
    plane: tuple[float, float, float],
) -> tuple[list[list[str]], list[list[str]], list[list[str]]]:
    release_rows: list[list[str]] = []
    deposition_rows: list[list[str]] = []
    blocks: dict[str, list[str]] = {}
    for trajectory_id in sorted(trajectories):
        if trajectory_id not in overview:
            continue
        samples = trajectories[trajectory_id]
        first = samples[0]
        last = samples[-1]
        meta = overview[trajectory_id]
        block_id = str(meta["block_id"])
        radius_m = float(meta["radius_m"])
        mass_kg = float(meta["mass_kg"])
        release_ground = plane_height(plane, first["x_m"], first["y_m"])
        deposition_ground = plane_height(plane, last["x_m"], last["y_m"])
        release_z = release_ground + radius_m
        deposition_z = deposition_ground + radius_m
        observed_runout = math.hypot(last["x_m"] - first["x_m"], last["y_m"] - first["y_m"])
        release_rows.append(
            [
                trajectory_id,
                "tschamut2014",
                f"{first['x_m']:.6f}",
                f"{first['y_m']:.6f}",
                f"{release_z:.6f}",
                f"{release_ground:.6f}",
                f"{first['vx_mps']:.6f}",
                f"{first['vy_mps']:.6f}",
                f"{first['vz_mps']:.6f}",
                block_id,
                f"{mass_kg:.6f}",
                f"{radius_m:.6f}",
                "EnviDat tschamut2014 all_LPS_splined first sample; z projected to proxy terrain plus radius",
            ]
        )
        deposition_rows.append(
            [
                trajectory_id,
                "tschamut2014",
                f"{last['x_m']:.6f}",
                f"{last['y_m']:.6f}",
                f"{deposition_z:.6f}",
                f"{deposition_ground:.6f}",
                f"{first['x_m']:.6f}",
                f"{first['y_m']:.6f}",
                f"{release_z:.6f}",
                f"{observed_runout:.6f}",
                block_id,
                f"{mass_kg:.6f}",
                f"{radius_m:.6f}",
                "EnviDat tschamut2014 all_LPS_splined last sample; z projected to proxy terrain plus radius",
            ]
        )
        blocks.setdefault(
            block_id,
            [
                block_id,
                str(meta["block_name"]),
                f"{mass_kg:.6f}",
                f"{radius_m:.6f}",
                f"{float(meta['size_x_m']):.6f}",
                f"{float(meta['size_y_m']):.6f}",
                f"{float(meta['size_z_m']):.6f}",
            ],
        )
    return release_rows, deposition_rows, list(blocks.values())


def fit_plane_from_points(points: list[tuple[float, float, float]]) -> tuple[float, float, float]:
    n = len(points)
    sx = sum(point[0] for point in points)
    sy = sum(point[1] for point in points)
    sz = sum(point[2] for point in points)
    sxx = sum(point[0] * point[0] for point in points)
    syy = sum(point[1] * point[1] for point in points)
    sxy = sum(point[0] * point[1] for point in points)
    sxz = sum(point[0] * point[2] for point in points)
    syz = sum(point[1] * point[2] for point in points)
    matrix = [[sxx, sxy, sx], [sxy, syy, sy], [sx, sy, float(n)]]
    rhs = [sxz, syz, sz]
    return solve_3x3(matrix, rhs)


def solve_3x3(matrix: list[list[float]], rhs: list[float]) -> tuple[float, float, float]:
    a = [row[:] + [rhs[index]] for index, row in enumerate(matrix)]
    for col in range(3):
        pivot = max(range(col, 3), key=lambda row: abs(a[row][col]))
        if abs(a[pivot][col]) < 1.0e-12:
            raise SystemExit("singular plane-fit matrix for Tschamut preprocessing")
        a[col], a[pivot] = a[pivot], a[col]
        scale = a[col][col]
        for item in range(col, 4):
            a[col][item] /= scale
        for row in range(3):
            if row == col:
                continue
            factor = a[row][col]
            for item in range(col, 4):
                a[row][item] -= factor * a[col][item]
    return (a[0][3], a[1][3], a[2][3])


def plane_height(plane: tuple[float, float, float], x_m: float, y_m: float) -> float:
    ax, ay, c = plane
    return ax * x_m + ay * y_m + c


def write_tschamut_terrain(
    path: Path,
    trajectories: dict[str, list[dict[str, float]]],
    plane: tuple[float, float, float],
) -> None:
    xs = [sample["x_m"] for samples in trajectories.values() for sample in samples]
    ys = [sample["y_m"] for samples in trajectories.values() for sample in samples]
    cellsize = 5.0
    pad = 30.0
    xll = math.floor((min(xs) - pad) / cellsize) * cellsize
    yll = math.floor((min(ys) - pad) / cellsize) * cellsize
    xmax = math.ceil((max(xs) + pad) / cellsize) * cellsize
    ymax = math.ceil((max(ys) + pad) / cellsize) * cellsize
    ncols = int(round((xmax - xll) / cellsize)) + 1
    nrows = int(round((ymax - yll) / cellsize)) + 1
    lines = [
        f"ncols {ncols}",
        f"nrows {nrows}",
        f"xllcorner {xll:.6f}",
        f"yllcorner {yll:.6f}",
        f"cellsize {cellsize:.6f}",
        "NODATA_value -9999",
    ]
    for row_from_top in range(nrows):
        row_from_bottom = nrows - 1 - row_from_top
        y = yll + row_from_bottom * cellsize
        values = [
            f"{plane_height(plane, xll + col * cellsize, y):.6f}"
            for col in range(ncols)
        ]
        lines.append(" ".join(values))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_tschamut_metadata(
    path: Path,
    plane: tuple[float, float, float],
    source_run_count: int,
    validation_run_count: int,
) -> None:
    ax, ay, c = plane
    metadata = {
        "dataset_id": "tschamut2014",
        "doi": "https://doi.org/10.16904/envidat.34",
        "license": "ODbL with Database Contents License (DbCL)",
        "source_files": ["OverviewAllTests.txt", "all_LPS_splined.txt"],
        "coordinate_system": (
            "Tschamut LPS local horizontal coordinates; elevations are EnviDat LPS "
            "terrain heights shifted by -1600 m for consistency with overview data."
        ),
        "terrain_proxy": {
            "type": "least_squares_plane_sampled_as_esri_ascii_grid",
            "equation": "z_m = slope_x * x_m + slope_y * y_m + intercept_m",
            "slope_x": ax,
            "slope_y": ay,
            "intercept_m": c,
            "note": (
                "This is a transparent v0 proxy terrain fitted to public LPS terrain "
                "points. It is not an official field DEM and must not be interpreted "
                "as calibrated terrain reconstruction."
            ),
        },
        "source_run_count": source_run_count,
        "validation_subset_run_count": validation_run_count,
    }
    path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", required=True, help="dataset id or synthetic_plane_basic")
    args = parser.parse_args()

    if args.dataset == "synthetic_plane_basic":
        write_synthetic_fixture()
        print("wrote synthetic fixture")
    elif args.dataset == "tschamut2014":
        preprocess_tschamut2014()
    else:
        inventory_archives(args.dataset)

    return 0


if __name__ == "__main__":
    sys.exit(main())
