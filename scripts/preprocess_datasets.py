#!/usr/bin/env python3
"""Create validation-ready derived files from downloaded public datasets.

This script never overwrites raw data. Dataset-specific scientific conversions are
added incrementally as schemas are stabilized; the current implementation provides
safe archive inventories and regenerates the small synthetic fixture.
"""

from __future__ import annotations

import argparse
import csv
import heapq
import json
import math
import re
import shutil
import statistics
import subprocess
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TSCHAMUT_VALIDATION_RUN_LIMIT = 10
CHANT_SURA_TRAJECTORY_IDS = ["RF16W200r1", "RF16W800r1", "RF18W200r1"]


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
    residual_samples = terrain_residual_samples(trajectories, plane)

    processed_dir = ROOT / "data" / "processed" / "tschamut2014"
    validation_dir = ROOT / "validation" / "data" / "processed" / "tschamut"
    processed_dir.mkdir(parents=True, exist_ok=True)
    validation_dir.mkdir(parents=True, exist_ok=True)

    full_release_rows, full_deposition_rows, block_rows = tschamut_rows(
        trajectories, overview, plane, residual_samples
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
    terrain_settings = write_tschamut_terrain(
        processed_dir / "terrain.asc", trajectories, plane, residual_samples
    )
    write_tschamut_metadata(
        processed_dir / "metadata.json",
        plane,
        terrain_settings,
        len(full_release_rows),
        len(validation_release_rows),
    )

    write_csv(validation_dir / "release_points.csv", release_header, validation_release_rows)
    write_csv(validation_dir / "observed_deposition.csv", deposition_header, validation_deposition_rows)
    write_csv(validation_dir / "block_metadata.csv", block_header, block_rows)
    write_tschamut_terrain(validation_dir / "terrain.asc", trajectories, plane, residual_samples)
    write_tschamut_metadata(
        validation_dir / "metadata.json",
        plane,
        terrain_settings,
        len(full_release_rows),
        len(validation_release_rows),
    )
    print(f"wrote Tschamut processed data to {processed_dir}")
    print(f"wrote Tschamut validation subset to {validation_dir}")


def preprocess_chant_sura_2020() -> None:
    raw_dir = ROOT / "data" / "raw" / "chant_sura_2020"
    output_archive = raw_dir / "output.7z"
    eota_archive = raw_dir / "eota.7z"
    if not output_archive.exists():
        raise SystemExit(
            "missing Chant Sura output archive; run "
            "`python3 scripts/download_datasets.py --dataset chant_sura_2020 "
            "--resource output_archive` first"
        )
    if shutil.which("bsdtar") is None:
        raise SystemExit("Chant Sura preprocessing requires bsdtar/libarchive for .7z extraction")

    trajectory_rows: list[list[str]] = []
    release_rows: list[list[str]] = []
    block_rows_by_id: dict[str, list[str]] = {}
    for trajectory_id in CHANT_SURA_TRAJECTORY_IDS:
        member = f"Output/txt/{trajectory_id}.txt"
        text = extract_archive_member(output_archive, member)
        segment = first_monotonic_chant_sura_segment(text)
        if not segment:
            raise SystemExit(f"no trajectory samples parsed from {member}")
        first = segment[0]
        mass_kg = infer_mass_kg(first)
        radius_m = equivalent_sphere_radius_m(mass_kg)
        block_id = chant_sura_block_id(trajectory_id)
        release_rows.append(
            [
                trajectory_id,
                "chant_sura_2020_first_flight_subset",
                fmt(first["x"]),
                fmt(first["y"]),
                fmt(first["z"]),
                fmt(first["v_x"]),
                fmt(first["v_y"]),
                fmt(first["v_z"]),
                fmt(mass_kg),
                fmt(radius_m),
            ]
        )
        block_rows_by_id.setdefault(
            block_id,
            [
                block_id,
                fmt(mass_kg),
                fmt(radius_m),
                "equivalent_sphere_from_mass",
                "radius inferred with density 2670 kg/m3; original EOTA shape data are not used by the current sphere model",
            ],
        )
        for sample in segment:
            trajectory_rows.append(
                [
                    trajectory_id,
                    "chant_sura_2020_first_flight_subset",
                    fmt(sample["time"]),
                    fmt(sample["x"]),
                    fmt(sample["y"]),
                    fmt(sample["z"]),
                    fmt(sample["v_x"]),
                    fmt(sample["v_y"]),
                    fmt(sample["v_z"]),
                    fmt(sample["v"]),
                    fmt(sample["Ekin"]),
                    fmt(sample["Erot"]),
                    fmt(sample["Etot"]),
                    fmt(sample.get("omega_x", 0.0)),
                    fmt(sample.get("omega_y", 0.0)),
                    fmt(sample.get("omega_z", 0.0)),
                ]
            )

    shape_rows = chant_sura_shape_rows(eota_archive) if eota_archive.exists() else []

    for out in (
        ROOT / "data" / "processed" / "chant_sura_2020",
        ROOT / "validation" / "data" / "processed" / "chant_sura_2020",
    ):
        out.mkdir(parents=True, exist_ok=True)
        write_csv(
            out / "release_points.csv",
            [
                "trajectory_id",
                "experiment_id",
                "x_m",
                "y_m",
                "z_m",
                "vx_mps",
                "vy_mps",
                "vz_mps",
                "mass_kg",
                "radius_m",
            ],
            release_rows,
        )
        write_csv(
            out / "observed_trajectories.csv",
            [
                "trajectory_id",
                "experiment_id",
                "time_s",
                "x_m",
                "y_m",
                "z_m",
                "vx_mps",
                "vy_mps",
                "vz_mps",
                "speed_mps",
                "kinetic_j",
                "rotational_j",
                "total_energy_j",
                "omega_x_radps",
                "omega_y_radps",
                "omega_z_radps",
            ],
            trajectory_rows,
        )
        write_csv(
            out / "block_metadata.csv",
            ["block_id", "mass_kg", "radius_m", "shape_class", "notes"],
            list(block_rows_by_id.values()),
        )
        if shape_rows:
            write_csv(
                out / "rock_shapes.csv",
                ["shape_file", "point_count", "min_x_m", "max_x_m", "min_y_m", "max_y_m", "min_z_m", "max_z_m", "role"],
                shape_rows,
            )
        write_chant_sura_metadata(out / "metadata.json", len(CHANT_SURA_TRAJECTORY_IDS), len(trajectory_rows), bool(shape_rows))
    print("wrote Chant Sura validation subset to data/processed/chant_sura_2020 and validation/data/processed/chant_sura_2020")


def extract_archive_member(archive: Path, member: str) -> str:
    result = subprocess.run(
        ["bsdtar", "-xOf", str(archive), member],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise SystemExit(f"failed to extract {member} from {archive}: {result.stderr.strip()}")
    return result.stdout


def first_monotonic_chant_sura_segment(text: str) -> list[dict[str, float]]:
    rows = csv.DictReader(text.splitlines())
    segment: list[dict[str, float]] = []
    previous_time = -math.inf
    for row in rows:
        try:
            parsed = {key: float(value) for key, value in row.items() if key is not None and value not in {None, ""}}
        except ValueError:
            continue
        time_s = parsed.get("time")
        if time_s is None:
            continue
        if segment and time_s < previous_time:
            break
        segment.append(parsed)
        previous_time = time_s
    return segment


def infer_mass_kg(sample: dict[str, float]) -> float:
    speed = sample["v"]
    if speed <= 0.0:
        raise SystemExit("cannot infer mass from non-positive speed")
    return 2.0 * sample["Ekin"] / (speed * speed)


def equivalent_sphere_radius_m(mass_kg: float, density_kgpm3: float = 2670.0) -> float:
    volume_m3 = mass_kg / density_kgpm3
    return (3.0 * volume_m3 / (4.0 * math.pi)) ** (1.0 / 3.0)


def chant_sura_block_id(trajectory_id: str) -> str:
    match = re.search(r"W(\d+)", trajectory_id)
    return f"W{match.group(1)}" if match else "unknown"


def chant_sura_shape_rows(eota_archive: Path) -> list[list[str]]:
    rows: list[list[str]] = []
    listing = subprocess.run(
        ["bsdtar", "-tf", str(eota_archive)],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if listing.returncode != 0:
        return rows
    for member in listing.stdout.splitlines():
        if not member.endswith(".pts"):
            continue
        text = extract_archive_member(eota_archive, member)
        points = []
        for line in text.splitlines():
            parts = line.split()
            if len(parts) < 3:
                continue
            try:
                points.append((float(parts[0]), float(parts[1]), float(parts[2])))
            except ValueError:
                continue
        if not points:
            continue
        xs, ys, zs = zip(*points)
        rows.append(
            [
                member,
                str(len(points)),
                fmt(min(xs)),
                fmt(max(xs)),
                fmt(min(ys)),
                fmt(max(ys)),
                fmt(min(zs)),
                fmt(max(zs)),
                "public EOTA shape geometry; documented for future non-spherical model development",
            ]
        )
    return rows


def write_chant_sura_metadata(
    path: Path,
    trajectory_count: int,
    sample_count: int,
    includes_shape_summary: bool,
) -> None:
    metadata = {
        "dataset_id": "chant_sura_2020",
        "doi": "https://doi.org/10.16904/envidat.174",
        "license": "WSL Data Policy",
        "source_files": [
            "Output/txt/RF16W200r1.txt",
            "Output/txt/RF16W800r1.txt",
            "Output/txt/RF18W200r1.txt",
        ],
        "coordinate_system": "LV95 / Swiss projected coordinates inferred from EnviDat output trajectory magnitudes; no CRS transformation is applied.",
        "subset": "first monotonic time segment from three reconstructed trajectory files",
        "trajectory_count": trajectory_count,
        "trajectory_sample_count": sample_count,
        "includes_shape_summary": includes_shape_summary,
        "available_but_not_committed": {
            "dem": "Input.7z contains site input data but is large and remains optional/raw-only.",
            "full_output_archive": "Output.7z contains reconstructed trajectory text files for the campaign.",
            "experimental_runs": "ExperimentalRuns.7z is large and not required for the minimal validation subset.",
        },
        "assumptions": [
            "Mass is inferred from published Ekin and speed columns per trajectory sample.",
            "Sphere radius is an equivalent-volume proxy using density 2670 kg/m3; original shapes are not used by the current sphere model.",
            "Only the first monotonic time segment is used because the public text files concatenate jump segments with local time resets.",
            "This subset is intended for trajectory-shape, energy-evolution, and proxy jump-height checks, not deposition validation.",
        ],
    }
    path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def fmt(value: float) -> str:
    return f"{value:.12g}"


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
    residual_samples: list[tuple[float, float, float]],
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
        release_ground = terrain_height(plane, residual_samples, first["x_m"], first["y_m"])
        deposition_ground = terrain_height(plane, residual_samples, last["x_m"], last["y_m"])
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
                "EnviDat tschamut2014 all_LPS_splined first sample; z projected to IDW residual terrain plus radius",
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
                "EnviDat tschamut2014 all_LPS_splined last sample; z projected to IDW residual terrain plus radius",
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


def terrain_residual_samples(
    trajectories: dict[str, list[dict[str, float]]],
    plane: tuple[float, float, float],
) -> list[tuple[float, float, float]]:
    return [
        (
            sample["x_m"],
            sample["y_m"],
            sample["ground_z_m"] - plane_height(plane, sample["x_m"], sample["y_m"]),
        )
        for samples in trajectories.values()
        for sample in samples
    ]


def idw_residual(
    residual_samples: list[tuple[float, float, float]],
    x_m: float,
    y_m: float,
    k_nearest: int = 24,
    power: float = 2.0,
) -> float:
    nearest = heapq.nsmallest(
        k_nearest,
        (
            ((x_m - sx) * (x_m - sx) + (y_m - sy) * (y_m - sy), residual)
            for sx, sy, residual in residual_samples
        ),
        key=lambda item: item[0],
    )
    if not nearest:
        return 0.0
    if nearest[0][0] < 1.0e-12:
        return nearest[0][1]
    weighted_sum = 0.0
    weight_total = 0.0
    for distance2, residual in nearest:
        weight = 1.0 / (math.pow(distance2, 0.5 * power) + 1.0e-12)
        weighted_sum += weight * residual
        weight_total += weight
    return weighted_sum / weight_total


def terrain_height(
    plane: tuple[float, float, float],
    residual_samples: list[tuple[float, float, float]],
    x_m: float,
    y_m: float,
) -> float:
    return plane_height(plane, x_m, y_m) + idw_residual(residual_samples, x_m, y_m)


def write_tschamut_terrain(
    path: Path,
    trajectories: dict[str, list[dict[str, float]]],
    plane: tuple[float, float, float],
    residual_samples: list[tuple[float, float, float]],
) -> dict[str, float | int | str]:
    xs = [sample["x_m"] for samples in trajectories.values() for sample in samples]
    ys = [sample["y_m"] for samples in trajectories.values() for sample in samples]
    cellsize = 5.0
    pad = 45.0
    k_nearest = 24
    power = 2.0
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
            f"{terrain_height(plane, residual_samples, xll + col * cellsize, y):.6f}"
            for col in range(ncols)
        ]
        lines.append(" ".join(values))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {
        "type": "idw_residual_dem_from_lps",
        "cellsize_m": cellsize,
        "padding_m": pad,
        "k_nearest": k_nearest,
        "idw_power": power,
        "xllcorner_m": xll,
        "yllcorner_m": yll,
        "ncols": ncols,
        "nrows": nrows,
    }


def write_tschamut_metadata(
    path: Path,
    plane: tuple[float, float, float],
    terrain_settings: dict[str, float | int | str],
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
            **terrain_settings,
            "trend_equation": "z_trend_m = slope_x * x_m + slope_y * y_m + intercept_m",
            "height_equation": "z_m = z_trend_m + IDW_residual_from_public_LPS_ground_points",
            "slope_x": ax,
            "slope_y": ay,
            "intercept_m": c,
            "note": (
                "This is a transparent terrain proxy built from public LPS ground "
                "points by adding inverse-distance-weighted residuals to a fitted "
                "trend plane. It is not an official field DEM and must not be "
                "interpreted as calibrated terrain reconstruction."
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
    elif args.dataset == "chant_sura_2020":
        preprocess_chant_sura_2020()
    else:
        inventory_archives(args.dataset)

    return 0


if __name__ == "__main__":
    sys.exit(main())
