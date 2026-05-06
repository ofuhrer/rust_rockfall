#!/usr/bin/env python3
"""Prepare a Mel de la Niva public benchmark manifest or runnable package.

The Zenodo dataset is large. By default this script records the public archives
and local ignored cache paths. With ``--make-runnable`` it uses the public
trajectory, GIS, and SfM DSM archives already present under ``data/raw`` to
generate a small no-tuning distribution-level validation package under ignored
``validation/results``.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import shutil
import struct
import subprocess
import tempfile
import urllib.request
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml  # type: ignore


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_ROOT = ROOT / "validation" / "results" / "public_benchmarks" / "mel_de_la_niva"
RAW_DIR = ROOT / "data" / "raw" / "mel_de_la_niva_2015"
DENSITY_KGPM3 = 2670.0
NODATA = -9999.0
RUNNABLE_ARCHIVE_IDS = ("trajectories", "gis_shapes", "sfm_rasters")
DEPOSITION_MATCH_THRESHOLD_M = None
DEPOSITION_MATCH_POLICY = (
    "nearest_neighbor_between_las_endpoint_and_2015_deposited_block_points; "
    "no hard threshold in first smoke package"
)

ARCHIVES = [
    {
        "id": "trajectories",
        "filename": "3d_trajectories_epsg21781_lv03.zip",
        "size_bytes": 166000,
        "md5": "dba538e90510c30eaa8cf9fcbdadad99",
        "role": "reconstructed 3D trajectories in EPSG:21781 / LV03",
    },
    {
        "id": "blocks_3d_shapes",
        "filename": "blocks_3d_shapes.zip",
        "size_bytes": 9100000,
        "md5": "b291875db502a8478a8e6fbecdd08d75",
        "role": "block shape geometry",
    },
    {
        "id": "gis_shapes",
        "filename": "gis_shapes_epsg21781_lv03.zip",
        "size_bytes": 10100000,
        "md5": "b88775690c74aff171f341a3681df4f8",
        "role": "rockfall path segments and deposited-block GIS shapes",
    },
    {
        "id": "sfm_rasters",
        "filename": "sfm_rasters_epsg21781_lv03.zip",
        "size_bytes": 74100000,
        "md5": "a17874b6c82d8739e2eda21455780515",
        "role": "SfM digital surface model and orthophoto rasters",
    },
    {
        "id": "simulation_benchmark",
        "filename": "rockfall_simulation_benchmark.zip",
        "size_bytes": 516300000,
        "md5": "2faf71e9c40a7c31ed8987d931db1791",
        "role": "public simulation benchmark resources for comparison context",
    },
    {
        "id": "videos",
        "filename": "videos_BEG_SA_and_Valais_canton.zip",
        "size_bytes": 488300000,
        "md5": "7fc42e2e2cb4a685ceb3af668656752e",
        "role": "event videos, optional for reconstruction QA",
    },
]


@dataclass(frozen=True)
class LasTrajectorySummary:
    trajectory_id: str
    first_xyz: tuple[float, float, float]
    last_xyz: tuple[float, float, float]
    point_count: int
    bounds: tuple[float, float, float, float]


@dataclass(frozen=True)
class DepositionPoint:
    x_m: float
    y_m: float
    year: int
    size_text: str
    dimensions_m: list[float]


@dataclass(frozen=True)
class MatchedDeposition:
    trajectory: LasTrajectorySummary
    deposition: DepositionPoint
    match_distance_m: float


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument(
        "--require-raw",
        action="store_true",
        help="fail if expected Zenodo archives are not present under data/raw",
    )
    parser.add_argument(
        "--download-runnable-archives",
        action="store_true",
        help="download the public trajectory, GIS-shape, and SfM DSM archives needed by --make-runnable",
    )
    parser.add_argument(
        "--make-runnable",
        action="store_true",
        help="generate a small runnable no-tuning validation package from locally cached public archives",
    )
    parser.add_argument("--initial-speed-mps", type=float, default=1.0)
    parser.add_argument("--terrain-resolution-m", type=float, default=5.0)
    parser.add_argument("--padding-m", type=float, default=100.0)
    args = parser.parse_args()

    output_root = args.output_root if args.output_root.is_absolute() else ROOT / args.output_root
    output_root.mkdir(parents=True, exist_ok=True)

    if args.download_runnable_archives:
        download_archives(RUNNABLE_ARCHIVE_IDS)

    archive_status = [archive_summary(item) for item in ARCHIVES]
    missing_required = [item for item in archive_status if not item["exists"]]
    if args.require_raw and missing_required:
        formatted = "\n".join(f"  - {item['path']}" for item in missing_required)
        raise SystemExit(f"missing Mel de la Niva raw archives:\n{formatted}")

    runnable_package = None
    if args.make_runnable:
        archive_errors = runnable_archive_errors(archive_status)
        if archive_errors:
            formatted = "\n".join(f"  - {error}" for error in archive_errors)
            raise SystemExit(
                "invalid Mel de la Niva archives required for --make-runnable:\n"
                f"{formatted}\nRun with --download-runnable-archives or place verified public archives manually."
            )
        runnable_package = prepare_runnable_package(
            output_root,
            initial_speed_mps=args.initial_speed_mps,
            terrain_resolution_m=args.terrain_resolution_m,
            padding_m=args.padding_m,
        )

    manifest = {
        "schema_version": "public_benchmark_preparation_manifest_v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "benchmark_id": "mel_de_la_niva",
        "dataset_id": "mel_de_la_niva_2015",
        "status": "runnable_no_tuning_package" if runnable_package else "metadata_only_until_raw_archives_are_downloaded",
        "selected_ids": runnable_package["selected_ids"] if runnable_package else [],
        "excluded_ids_with_reasons": [],
        "public_source": {
            "title": "Highly energetic rockfalls: Dataset of the 2015 event from the Mel de la Niva, Switzerland",
            "doi": "https://doi.org/10.5281/zenodo.7257979",
            "source_url": "https://zenodo.org/records/7257979",
            "license": "Creative Commons Attribution 4.0 International",
        },
        "scientific_role": [
            "external high-energy/generalization benchmark",
            "trajectory-path and impact-path validation after smaller benchmarks are stable",
            "future block-shape and terrain-interaction stress test",
        ],
        "coordinate_system": "Public archive names indicate EPSG:21781 / LV03 for trajectories, GIS shapes, and SfM rasters.",
        "generated_cases": runnable_package["generated_cases"] if runnable_package else [],
        "command_provenance": {
            "script": "scripts/prepare_mel_de_la_niva_benchmark.py",
            "require_raw": args.require_raw,
            "download_runnable_archives": args.download_runnable_archives,
            "make_runnable": args.make_runnable,
            "initial_speed_mps": args.initial_speed_mps,
            "terrain_resolution_m": args.terrain_resolution_m,
            "padding_m": args.padding_m,
        },
        "provenance": {
            "dataset": "Mel de la Niva 2015 public benchmark scaffold",
            "doi": "https://doi.org/10.5281/zenodo.7257979",
            "license": "Creative Commons Attribution 4.0 International",
        },
        "raw_cache_policy": {
            "raw_dir": str(RAW_DIR.relative_to(ROOT)),
            "ignored_by_git": True,
            "download_large_archives_by_default": False,
        },
        "archives": archive_status,
        "runnable_package": runnable_package,
        "required_before_runnable_cases": [
            "download selected public Zenodo archives into data/raw/mel_de_la_niva_2015",
            "define CRS strategy: remain in LV03 or transform consistently to LV95/EPSG:2056",
            "derive terrain crop and release/deposition/reference files with checksums",
            "record excluded trajectories or blocks with reproducible reasons",
        ],
        "limitations": [
            (
                "Runnable case is a path-endpoint/deposition smoke benchmark, not a calibrated high-energy field validation."
                if runnable_package
                else "No runnable validation case is generated by this metadata-only scaffold."
            ),
            (
                "Runnable deposition matching records nearest-neighbor distances and applies no hard threshold; "
                "matches require QA review before scientific interpretation."
                if runnable_package
                else "No deposition matching is performed by this metadata-only scaffold."
            ),
            "The event scale differs from small-block field experiments and must not be used for hidden tuning.",
            "The current simulator lacks dynamic non-spherical shape/contact physics.",
            "LAS trajectory archives do not provide time in point format 0; the runnable case uses path endpoints and a documented non-calibrated initial-speed policy.",
        ],
    }
    manifest_path = output_root / "preparation_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(f"wrote Mel de la Niva benchmark manifest to {manifest_path}")
    return 0


def archive_summary(item: dict[str, Any]) -> dict[str, Any]:
    path = RAW_DIR / item["filename"]
    summary = dict(item)
    md5 = md5_file(path) if path.exists() else None
    summary.update(
        {
            "path": str(path.relative_to(ROOT)),
            "exists": path.exists(),
            "bytes_on_disk": path.stat().st_size if path.exists() else None,
            "md5_on_disk": md5,
            "checksum_matches": md5 == item["md5"] if md5 else None,
            "download_url": f"https://zenodo.org/records/7257979/files/{item['filename']}?download=1",
        }
    )
    return summary


def runnable_archive_errors(archive_status: list[dict[str, Any]]) -> list[str]:
    by_id = {item["id"]: item for item in archive_status}
    errors: list[str] = []
    for archive_id in RUNNABLE_ARCHIVE_IDS:
        item = by_id.get(archive_id)
        if item is None:
            errors.append(f"missing archive status for required runnable archive {archive_id}")
            continue
        if not item.get("exists"):
            errors.append(f"missing required runnable archive: {item.get('path', archive_id)}")
            continue
        if item.get("checksum_matches") is not True:
            errors.append(
                "checksum mismatch for required runnable archive "
                f"{item.get('path', archive_id)}: expected {item.get('md5')}, got {item.get('md5_on_disk')}"
            )
    return errors


def download_archives(ids: tuple[str, ...]) -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    by_id = {item["id"]: item for item in ARCHIVES}
    for archive_id in ids:
        item = by_id[archive_id]
        path = RAW_DIR / item["filename"]
        if not path.exists():
            url = f"https://zenodo.org/records/7257979/files/{item['filename']}?download=1"
            print(f"download {url}")
            urllib.request.urlretrieve(url, path)
        actual = md5_file(path)
        if actual != item["md5"]:
            raise SystemExit(f"checksum mismatch for {path}: expected {item['md5']}, got {actual}")


def prepare_runnable_package(
    output_root: Path,
    *,
    initial_speed_mps: float,
    terrain_resolution_m: float,
    padding_m: float,
) -> dict[str, Any]:
    if initial_speed_mps <= 0.0 or not math.isfinite(initial_speed_mps):
        raise SystemExit("--initial-speed-mps must be positive and finite")
    if terrain_resolution_m <= 0.0 or not math.isfinite(terrain_resolution_m):
        raise SystemExit("--terrain-resolution-m must be positive and finite")

    input_dir = output_root / "input"
    case_dir = output_root / "cases"
    validation_dir = output_root / "validation"
    input_dir.mkdir(parents=True, exist_ok=True)
    case_dir.mkdir(parents=True, exist_ok=True)
    validation_dir.mkdir(parents=True, exist_ok=True)

    trajectories = read_mel_las_trajectories(RAW_DIR / "3d_trajectories_epsg21781_lv03.zip")
    depositions = read_2015_deposition_points(RAW_DIR / "gis_shapes_epsg21781_lv03.zip")
    if len(depositions) < len(trajectories):
        raise SystemExit("not enough 2015 deposited-block points to match Mel de la Niva trajectories")
    matched = match_trajectory_depositions(trajectories, depositions)

    terrain_path = input_dir / "mel_de_la_niva_dsm_crop.asc"
    crop = write_dsm_crop(
        RAW_DIR / "sfm_rasters_epsg21781_lv03.zip",
        terrain_path,
        trajectories,
        depositions,
        resolution_m=terrain_resolution_m,
        padding_m=padding_m,
    )
    terrain_metadata_path = input_dir / "mel_de_la_niva_terrain_metadata.yaml"
    write_terrain_metadata(terrain_metadata_path, terrain_path, crop, terrain_resolution_m)

    release_rows, deposition_rows = build_release_and_deposition_rows(
        matched,
        initial_speed_mps=initial_speed_mps,
    )
    release_csv = input_dir / "release_points_lv03.csv"
    deposition_csv = input_dir / "observed_deposition_lv03.csv"
    write_csv(release_csv, release_rows)
    write_csv(deposition_csv, deposition_rows)

    baseline_case = build_case(
        "mel_de_la_niva_baseline",
        "translational_v0",
        terrain_path,
        release_csv,
        deposition_csv,
        validation_dir,
        release_rows[0],
    )
    rotational_case = build_case(
        "mel_de_la_niva_rotational",
        "sphere_rotational_v1",
        terrain_path,
        release_csv,
        deposition_csv,
        validation_dir,
        release_rows[0],
    )
    baseline_path = case_dir / "mel_de_la_niva_baseline.yaml"
    rotational_path = case_dir / "mel_de_la_niva_rotational.yaml"
    write_yaml(baseline_path, baseline_case)
    write_yaml(rotational_path, rotational_case)

    return {
        "schema_version": "mel_de_la_niva_runnable_package_v1",
        "status": "generated",
        "selected_ids": [trajectory.trajectory_id for trajectory in trajectories],
        "selected_run_count": len(trajectories),
        "generated_cases": [
            str(baseline_path.relative_to(ROOT)),
            str(rotational_path.relative_to(ROOT)),
        ],
        "input_files": {
            "terrain_ascii": str(terrain_path.relative_to(ROOT)),
            "terrain_metadata": str(terrain_metadata_path.relative_to(ROOT)),
            "release_points_csv": str(release_csv.relative_to(ROOT)),
            "observed_deposition_csv": str(deposition_csv.relative_to(ROOT)),
        },
        "terrain_crop": crop,
        "crs": "EPSG:21781 / CH1903 LV03 retained from public archive names",
        "selection_policy": "both public LAS trajectories, matched to nearest 2015 deposited-block points",
        "deposition_match_policy": deposition_match_policy_summary(matched),
        "initial_velocity_policy": (
            f"path-direction unit vector scaled to {initial_speed_mps:g} m/s because LAS point format 0 "
            "does not carry observation timestamps"
        ),
        "active_block_policy": (
            "sphere radius from reported deposited-block maximum dimension / 2; mass from an assumed "
            f"rock density of {DENSITY_KGPM3:g} kg/m3; no calibration and no measured block density claim"
        ),
        "limitations": [
            "Nearest-neighbor deposition matches are recorded with distances and no hard acceptance threshold.",
            "Observed runout is horizontal release-to-matched-deposited-block endpoint displacement.",
            f"The {DENSITY_KGPM3:g} kg/m3 density is an assumption for smoke-package mass estimates, not measured truth.",
        ],
    }


def read_mel_las_trajectories(path: Path) -> list[LasTrajectorySummary]:
    with zipfile.ZipFile(path) as archive:
        summaries = [
            read_las_summary(archive.read("3d_trajectories_epsg21781_lv03/traj_bl1.las"), "mel_de_la_niva_bl1"),
            read_las_summary(archive.read("3d_trajectories_epsg21781_lv03/traj_bl2.las"), "mel_de_la_niva_bl2"),
        ]
    return summaries


def read_las_summary(data: bytes, trajectory_id: str) -> LasTrajectorySummary:
    if data[:4] != b"LASF":
        raise SystemExit(f"{trajectory_id} is not an uncompressed LAS file")
    offset = struct.unpack_from("<I", data, 96)[0]
    point_format = data[104]
    record_len = struct.unpack_from("<H", data, 105)[0]
    point_count = struct.unpack_from("<I", data, 107)[0]
    if point_format != 0:
        raise SystemExit(f"{trajectory_id} uses unsupported LAS point format {point_format}")
    scale = struct.unpack_from("<ddd", data, 131)
    offsets = struct.unpack_from("<ddd", data, 155)
    points: list[tuple[float, float, float]] = []
    for index in range(point_count):
        base = offset + index * record_len
        ix, iy, iz = struct.unpack_from("<iii", data, base)
        points.append(
            (
                ix * scale[0] + offsets[0],
                iy * scale[1] + offsets[1],
                iz * scale[2] + offsets[2],
            )
        )
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    return LasTrajectorySummary(
        trajectory_id=trajectory_id,
        first_xyz=points[0],
        last_xyz=points[-1],
        point_count=len(points),
        bounds=(min(xs), min(ys), max(xs), max(ys)),
    )


def read_2015_deposition_points(path: Path) -> list[DepositionPoint]:
    try:
        import shapefile  # type: ignore
    except ImportError as exc:
        raise SystemExit("pyshp is required to read Mel de la Niva GIS shapefiles") from exc

    with tempfile.TemporaryDirectory() as temp_dir:
        with zipfile.ZipFile(path) as archive:
            archive.extractall(temp_dir)
        reader = shapefile.Reader(str(Path(temp_dir) / "gis_shapes_epsg21781_lv03/deposited_bl.shp"))
        depositions: list[DepositionPoint] = []
        for record in reader.shapeRecords():
            attrs = record.record.as_dict()
            year = int(attrs.get("year"))
            if year != 2015:
                continue
            point = record.shape.points[0]
            size_text = str(attrs.get("size", ""))
            depositions.append(
                DepositionPoint(
                    x_m=float(point[0]),
                    y_m=float(point[1]),
                    year=year,
                    size_text=size_text,
                    dimensions_m=parse_size_dimensions(size_text),
                )
            )
    return depositions


def parse_size_dimensions(value: str) -> list[float]:
    stripped = value.strip().strip("[]")
    dimensions = [float(part.strip()) for part in stripped.split(";") if part.strip()]
    if not dimensions:
        raise SystemExit(f"could not parse deposited-block size {value!r}")
    return dimensions


def match_trajectory_depositions(
    trajectories: list[LasTrajectorySummary],
    depositions: list[DepositionPoint],
) -> list[MatchedDeposition]:
    remaining = list(depositions)
    matched: list[MatchedDeposition] = []
    for trajectory in trajectories:
        lx, ly, _ = trajectory.last_xyz
        deposition = min(remaining, key=lambda item: math.hypot(item.x_m - lx, item.y_m - ly))
        remaining.remove(deposition)
        matched.append(
            MatchedDeposition(
                trajectory=trajectory,
                deposition=deposition,
                match_distance_m=math.hypot(deposition.x_m - lx, deposition.y_m - ly),
            )
        )
    return matched


def deposition_match_policy_summary(matched: list[MatchedDeposition]) -> dict[str, Any]:
    return {
        "method": DEPOSITION_MATCH_POLICY,
        "threshold_m": DEPOSITION_MATCH_THRESHOLD_M,
        "threshold_policy": (
            "No hard threshold is applied in this first runnable smoke package. "
            "Match distances are QA diagnostics and these matches must not be treated as strong validation evidence "
            "without scientific review."
        ),
        "selected_match_count": len(matched),
        "matches": [
            {
                "trajectory_id": item.trajectory.trajectory_id,
                "deposition_year": item.deposition.year,
                "deposition_size_text": item.deposition.size_text,
                "match_distance_m": round(item.match_distance_m, 6),
                "observed_runout_definition": "horizontal_release_to_matched_2015_deposited_block_point_m",
                "observed_runout_m": round(
                    math.hypot(
                        item.deposition.x_m - item.trajectory.first_xyz[0],
                        item.deposition.y_m - item.trajectory.first_xyz[1],
                    ),
                    6,
                ),
            }
            for item in matched
        ],
    }


def write_dsm_crop(
    archive_path: Path,
    output_path: Path,
    trajectories: list[LasTrajectorySummary],
    depositions: list[DepositionPoint],
    *,
    resolution_m: float,
    padding_m: float,
) -> dict[str, Any]:
    xs = [x for trajectory in trajectories for x in (trajectory.first_xyz[0], trajectory.last_xyz[0])]
    ys = [y for trajectory in trajectories for y in (trajectory.first_xyz[1], trajectory.last_xyz[1])]
    xs.extend(deposition.x_m for deposition in depositions)
    ys.extend(deposition.y_m for deposition in depositions)
    xmin = math.floor((min(xs) - padding_m) / resolution_m) * resolution_m
    xmax = math.ceil((max(xs) + padding_m) / resolution_m) * resolution_m
    ymin = math.floor((min(ys) - padding_m) / resolution_m) * resolution_m
    ymax = math.ceil((max(ys) + padding_m) / resolution_m) * resolution_m
    source = (
        f"/vsizip/{archive_path.resolve()}/"
        "sfm_rasters_epsg21781_lv03/dsm_lv1903_50cm.tif"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "gdal_translate",
        "-q",
        "-of",
        "AAIGrid",
        "-r",
        "bilinear",
        "-tr",
        str(resolution_m),
        str(resolution_m),
        "-a_nodata",
        str(NODATA),
        "-projwin",
        str(xmin),
        str(ymax),
        str(xmax),
        str(ymin),
        source,
        str(output_path),
    ]
    if shutil.which("gdal_translate") is None:
        raise SystemExit("gdal_translate is required to generate the Mel de la Niva terrain crop")
    subprocess.run(command, check=True)
    return {
        "xmin": xmin,
        "ymin": ymin,
        "xmax": xmax,
        "ymax": ymax,
        "resolution_m": resolution_m,
        "source_archive": str(archive_path.relative_to(ROOT)),
        "processed_sha256": sha256_file(output_path),
    }


def write_terrain_metadata(path: Path, terrain_path: Path, crop: dict[str, Any], resolution_m: float) -> None:
    write_yaml(
        path,
        {
            "schema_version": 1,
            "source_dataset": "mel_de_la_niva_2015",
            "source_product": "SfM DSM dsm_lv1903_50cm.tif",
            "coordinate_reference_system": {
                "epsg": 21781,
                "horizontal_name": "CH1903 / LV03",
                "vertical_datum": "not separately specified by this package",
                "coordinate_unit": "m",
                "height_unit": "m",
            },
            "raster": {
                "format": "ESRI ASCII GRID",
                "resolution_m": resolution_m,
                "nodata": NODATA,
            },
            "extent_lv03_m": {key: crop[key] for key in ("xmin", "ymin", "xmax", "ymax")},
            "preprocessing": {
                "tool": "scripts/prepare_mel_de_la_niva_benchmark.py",
                "source_archive": crop["source_archive"],
                "processed_ascii": str(terrain_path.relative_to(ROOT)),
                "processed_sha256": crop["processed_sha256"],
                "resampling_method": "gdal_translate bilinear crop from 0.5 m public SfM DSM",
            },
            "limitations": [
                "LV03 is retained for this first runnable benchmark package.",
                "Vertical datum is inherited from the public SfM DSM archive and not independently adjusted.",
            ],
        },
    )


def build_release_and_deposition_rows(
    matched: list[MatchedDeposition],
    *,
    initial_speed_mps: float,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    release_rows: list[dict[str, Any]] = []
    deposition_rows: list[dict[str, Any]] = []
    for item in matched:
        trajectory = item.trajectory
        deposition = item.deposition
        radius = max(deposition.dimensions_m) / 2.0
        mass = (4.0 / 3.0) * math.pi * radius**3 * DENSITY_KGPM3
        vx, vy, vz = initial_velocity_from_path(trajectory, initial_speed_mps)
        release_rows.append(
            {
                "trajectory_id": trajectory.trajectory_id,
                "experiment_id": "mel_de_la_niva_2015_first_runnable",
                "x_m": f"{trajectory.first_xyz[0]:.6f}",
                "y_m": f"{trajectory.first_xyz[1]:.6f}",
                "z_m": f"{trajectory.first_xyz[2]:.6f}",
                "ground_z_m": f"{trajectory.first_xyz[2] - radius:.6f}",
                "vx_mps": f"{vx:.6f}",
                "vy_mps": f"{vy:.6f}",
                "vz_mps": f"{vz:.6f}",
                "block_id": trajectory.trajectory_id.rsplit("_", 1)[-1],
                "mass_kg": f"{mass:.6f}",
                "radius_m": f"{radius:.6f}",
                "density_assumption_kgpm3": f"{DENSITY_KGPM3:.6f}",
                "source": (
                    "public LAS trajectory first point; initial speed policy documented in manifest; "
                    "mass uses assumed rock density, not a measured block density"
                ),
            }
        )
        runout = math.hypot(deposition.x_m - trajectory.first_xyz[0], deposition.y_m - trajectory.first_xyz[1])
        deposition_rows.append(
            {
                "trajectory_id": trajectory.trajectory_id,
                "experiment_id": "mel_de_la_niva_2015_first_runnable",
                "x_m": f"{deposition.x_m:.6f}",
                "y_m": f"{deposition.y_m:.6f}",
                "z_m": f"{trajectory.last_xyz[2]:.6f}",
                "ground_z_m": f"{trajectory.last_xyz[2] - radius:.6f}",
                "release_x_m": f"{trajectory.first_xyz[0]:.6f}",
                "release_y_m": f"{trajectory.first_xyz[1]:.6f}",
                "release_z_m": f"{trajectory.first_xyz[2]:.6f}",
                "observed_runout_m": f"{runout:.6f}",
                "observed_runout_definition": "horizontal_release_to_matched_2015_deposited_block_point_m",
                "deposition_match_distance_m": f"{item.match_distance_m:.6f}",
                "deposition_match_threshold_m": "",
                "deposition_match_policy": DEPOSITION_MATCH_POLICY,
                "block_id": trajectory.trajectory_id.rsplit("_", 1)[-1],
                "mass_kg": f"{mass:.6f}",
                "radius_m": f"{radius:.6f}",
                "density_assumption_kgpm3": f"{DENSITY_KGPM3:.6f}",
                "source": (
                    f"nearest public 2015 deposited_bl point {deposition.size_text}; "
                    "z inherited from LAS trajectory endpoint for runnable smoke comparison; "
                    "nearest-neighbor match distance recorded for QA"
                ),
            }
        )
    return release_rows, deposition_rows


def initial_velocity_from_path(
    trajectory: LasTrajectorySummary,
    initial_speed_mps: float,
) -> tuple[float, float, float]:
    dx = trajectory.last_xyz[0] - trajectory.first_xyz[0]
    dy = trajectory.last_xyz[1] - trajectory.first_xyz[1]
    dz = trajectory.last_xyz[2] - trajectory.first_xyz[2]
    norm = math.sqrt(dx * dx + dy * dy + dz * dz)
    if norm == 0.0:
        return (0.0, 0.0, 0.0)
    return (dx / norm * initial_speed_mps, dy / norm * initial_speed_mps, dz / norm * initial_speed_mps)


def build_case(
    suffix: str,
    contact_model: str,
    terrain_path: Path,
    release_csv: Path,
    deposition_csv: Path,
    validation_dir: Path,
    first_release_row: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": "benchmark_case_v1",
        "case_id": f"validation_{suffix}",
        "title": f"Mel de la Niva first runnable {contact_model} benchmark",
        "level": 5,
        "description": (
            "First runnable public Mel de la Niva path-endpoint/deposition smoke benchmark. "
            "It preserves no-tuning discipline and is not a calibrated field-realism claim."
        ),
        "terrain": {
            "type": "ascii_dem_clamped",
            "path": str(terrain_path.relative_to(ROOT)),
        },
        "block": {
            "mass": float(first_release_row["mass_kg"]),
            "radius": float(first_release_row["radius_m"]),
        },
        "release": {
            "position": [
                float(first_release_row["x_m"]),
                float(first_release_row["y_m"]),
                float(first_release_row["z_m"]),
            ],
            "velocity": [
                float(first_release_row["vx_mps"]),
                float(first_release_row["vy_mps"]),
                float(first_release_row["vz_mps"]),
            ],
        },
        "parameters": {
            "gravity": 9.81,
            "normal_restitution": 0.25,
            "tangential_restitution": 0.85,
            "friction_coefficient": 0.45,
            "contact_model": contact_model,
        },
        "simulation": {"dt": 0.02, "t_max": 60.0, "max_steps": 3000, "stop_velocity": 0.05},
        "random": {"seed": None, "ensemble_size": 1},
        "validation_scope": {
            "type": "distribution-level-path-endpoint-smoke",
            "note": (
                "Compares generated deposition against public trajectory endpoint/deposited-block references. "
                "LAS point format lacks time, so this is a runnable workflow benchmark, not trajectory-dynamics validation."
            ),
        },
        "observations": {
            "release_points_csv": str(release_csv.relative_to(ROOT)),
            "deposition_points_csv": str(deposition_csv.relative_to(ROOT)),
        },
        "expected": {
            "metrics": [
                "validation_release_count",
                "validation_simulated_trajectory_count",
                "observed_mean_runout_m",
                "simulated_mean_runout_m",
                "runout_distance_error_m",
                "deposition_centroid_error_m",
                "deposition_cloud_mean_nearest_error_m",
                "lateral_spread_error_m",
                "deposition_cloud_overlap_fraction",
            ],
            "values": {"validation_release_count": 2.0, "validation_simulated_trajectory_count": 2.0},
        },
        "outputs": {
            "diagnostics_json": str((validation_dir / f"validation_{suffix}_metrics.json").relative_to(ROOT)),
            "trajectory_csv": str((validation_dir / f"validation_{suffix}_trajectory.csv").relative_to(ROOT)),
            "ensemble_deposition_csv": str(
                (validation_dir / f"validation_{suffix}_ensemble_deposition.csv").relative_to(ROOT)
            ),
        },
        "references": {
            "dataset": "mel_de_la_niva_2015",
            "literature": [
                "Noel, F. et al. (2022). Highly energetic rockfalls: Dataset of the 2015 event from the Mel de la Niva, Switzerland. Zenodo. https://doi.org/10.5281/zenodo.7257979"
            ],
            "notes": [
                "No parameters are calibrated or tuned to this benchmark.",
                "LV03/EPSG:21781 coordinates are retained from public archive names.",
                "Active block radius/mass are documented approximations from public deposited-block size strings and density assumption.",
            ],
        },
        "report": {
            "verifies": [
                "Public archive ingestion, terrain crop generation, release/deposition CSV construction, and deterministic validation execution.",
            ],
            "does_not_verify": [
                "Timed trajectory dynamics, operational hazard skill, calibrated high-energy runout, or shape-dependent contact physics.",
            ],
        },
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise SystemExit(f"cannot write empty CSV {path}")
    with path.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_yaml(path: Path, data: dict[str, Any]) -> None:
    path.write_text(yaml.safe_dump(data, sort_keys=False))


def md5_file(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
