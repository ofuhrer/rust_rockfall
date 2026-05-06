#!/usr/bin/env python3
"""Prepare a public Tschamut benchmark reproduction package.

The generated package is intentionally written under ignored result/raw-data
directories. It combines the public EnviDat Tschamut 2014 observations with a
public swissALTI3D 2 m tile and creates runnable validation cases for the
current simulator. The default transform fits a 2D translation between public
LPS terrain-height samples and the public CH1903 slope scan, then projects the
result to LV95. The public OverviewAllTests tachymeter offset and the original
bounding-box alignment remain available for comparison and registration
uncertainty checks.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import urllib.request
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import yaml  # type: ignore
from PIL import Image
from pyproj import Transformer


ROOT = Path(__file__).resolve().parents[1]
TSCHAMUT_SCAN_URL = (
    "https://www.envidat.ch/dataset/6a7664a6-77a9-49c9-9498-4b63c018fa09/"
    "resource/8cf275ca-06d0-47cf-b67f-48780b019ae6/download/geosciences-08-00088-s001.zip"
)
TSCHAMUT_SCAN_SHA256 = "c6fb965374c61b9e4909fe1a14330fed2b1593e7276299af6ec933aa64e991b5"
TSCHAMUT_LPS_URL = (
    "https://www.envidat.ch/dataset/6a7664a6-77a9-49c9-9498-4b63c018fa09/"
    "resource/b6dc0f14-5b86-4353-a2a6-ef06c0ddf0ad/download/trajectoriesfromlps.zip"
)
TSCHAMUT_LPS_SHA256 = "63619cbe5bb4ff9f869bbf665e5e79218e189affeb55d08b3f024046f17c98b8"
SWISSALTI_TILE_ID = "2696-1167"
SWISSALTI_TILE_URL = (
    "https://data.geo.admin.ch/ch.swisstopo.swissalti3d/"
    "swissalti3d_2019_2696-1167/swissalti3d_2019_2696-1167_2_2056_5728.tif"
)
SWISSALTI_TILE_SHA256 = "e1fe4119d3fec60f1f6fcb3f15698af23c96c92a2a0b9d8f34c89b109a88becf"
DEFAULT_OUTPUT_ROOT = ROOT / "validation" / "results" / "tschamut_public_benchmark"
NODATA = -9999.0


@dataclass(frozen=True)
class LpsToLv95Transform:
    lv03_e_offset_m: float
    lv03_n_offset_m: float
    vertical_offset_m: float
    method: str
    transformer: Transformer

    def lv03_xy(self, x_m: float, y_m: float) -> tuple[float, float]:
        return x_m + self.lv03_e_offset_m, y_m + self.lv03_n_offset_m

    def xy(self, x_m: float, y_m: float) -> tuple[float, float]:
        e_lv03, n_lv03 = self.lv03_xy(x_m, y_m)
        x_lv95, y_lv95 = self.transformer.transform(e_lv03, n_lv03)
        return float(x_lv95), float(y_lv95)

    def z(self, z_local_m: float) -> float:
        return z_local_m + self.vertical_offset_m


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--run-limit", type=int, default=10, help="number of public LPS runs to include")
    parser.add_argument(
        "--run-ids",
        help="comma-separated trajectory IDs to include instead of the first --run-limit processed rows",
    )
    parser.add_argument(
        "--block-id",
        help="select the first --run-limit public LPS runs for one Tschamut block ID",
    )
    parser.add_argument(
        "--block-shape-metadata",
        type=Path,
        help=(
            "optional passive shape_metadata_v1 sidecar; accepted only when all selected runs "
            "share one block ID"
        ),
    )
    parser.add_argument("--ensemble-size", type=int, default=6)
    parser.add_argument("--seed", type=int, default=34014)
    parser.add_argument("--padding-m", type=float, default=250.0)
    parser.add_argument(
        "--transform-method",
        choices=("scan_surface_fit_v1", "bbox_align_v1", "overview_offset_v1"),
        default="scan_surface_fit_v1",
        help="coordinate transform from public LPS local coordinates to Swiss projected coordinates",
    )
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    output_root = args.output_root if args.output_root.is_absolute() else ROOT / args.output_root
    input_dir = output_root / "input"
    case_dir = output_root / "cases"
    results_dir = output_root / "validation"
    input_dir.mkdir(parents=True, exist_ok=True)
    case_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    scan_zip = ROOT / "data" / "raw" / "tschamut2014" / "geosciences-08-00088-s001.zip"
    lps_zip = ROOT / "data" / "raw" / "tschamut2014" / "trajectoriesfromlps.zip"
    swissalti_tif = ROOT / "data" / "raw" / "swisstopo" / "swissalti3d_2019_2696-1167_2_2056_5728.tif"
    ensure_download(scan_zip, TSCHAMUT_SCAN_URL, TSCHAMUT_SCAN_SHA256)
    ensure_download(lps_zip, TSCHAMUT_LPS_URL, TSCHAMUT_LPS_SHA256)
    ensure_download(swissalti_tif, SWISSALTI_TILE_URL, SWISSALTI_TILE_SHA256)

    release_rows_all = read_csv(ROOT / "data" / "processed" / "tschamut2014" / "release_points.csv")
    deposition_rows_all = read_csv(ROOT / "data" / "processed" / "tschamut2014" / "observed_deposition.csv")
    release_rows, deposition_rows, selection = select_observation_rows(
        release_rows_all,
        deposition_rows_all,
        args.run_limit,
        args.run_ids,
        args.block_id,
    )
    if not release_rows or not deposition_rows:
        raise SystemExit("processed Tschamut release/deposition rows are missing")
    shape_metadata_path = resolve_shape_metadata_path(args.block_shape_metadata, release_rows)

    transform = derive_lps_to_lv95_transform(scan_zip, args.transform_method)
    transformed_releases = transform_release_rows(release_rows, transform)
    transformed_depositions = transform_deposition_rows(deposition_rows, transform)

    release_csv = input_dir / "release_points_lv95.csv"
    deposition_csv = input_dir / "observed_deposition_lv95.csv"
    write_csv(release_csv, transformed_releases)
    write_csv(deposition_csv, transformed_depositions)

    dem_path = input_dir / "tschamut_public_swissalti3d_crop.asc"
    terrain_metadata_path = input_dir / "tschamut_public_swissalti3d_metadata.yaml"
    release_zone_path = input_dir / "tschamut_public_release_zone.yaml"
    crop = write_swissalti_crop(
        swissalti_tif,
        dem_path,
        [*transformed_releases, *transformed_depositions],
        padding_m=args.padding_m,
    )
    terrain_sha = sha256_file(dem_path)
    write_terrain_metadata(
        terrain_metadata_path,
        crop,
        dem_path,
        terrain_sha,
        swissalti_tif,
        transform,
        args.padding_m,
    )
    qa = registration_quality(scan_zip, transform)
    write_registration_qa(input_dir / "registration_qa.json", qa, transform)
    write_registration_overlay_svg(input_dir / "registration_lps_scan_overlay.svg", scan_zip, transform)
    write_release_zone_metadata(release_zone_path, transformed_releases, crop, args.seed, len(transformed_releases))
    write_release_deposition_overlay_svg(
        input_dir / "release_deposition_crop_overlay.svg",
        transformed_releases,
        transformed_depositions,
        crop,
    )

    baseline = build_case(
        "baseline",
        "translational_v0",
        dem_path,
        terrain_metadata_path,
        release_csv,
        deposition_csv,
        results_dir,
        args.seed,
        args.ensemble_size,
        transformed_releases[0],
        shape_metadata_path,
    )
    rotational = build_case(
        "rotational",
        "sphere_rotational_v1",
        dem_path,
        terrain_metadata_path,
        release_csv,
        deposition_csv,
        results_dir,
        args.seed,
        args.ensemble_size,
        transformed_releases[0],
        shape_metadata_path,
    )
    write_yaml(case_dir / "tschamut_public_benchmark_baseline.yaml", baseline)
    write_yaml(case_dir / "tschamut_public_benchmark_rotational.yaml", rotational)

    manifest = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "output_root": str(output_root.relative_to(ROOT)),
        "run_limit": args.run_limit,
        "selection": selection,
        "selected_run_summary": summarize_selected_runs(release_rows),
        "selected_block_id": single_selected_block_id(release_rows),
        "block_shape_metadata": (
            str(shape_metadata_path.relative_to(ROOT)) if shape_metadata_path is not None else None
        ),
        "case_files": [
            str((case_dir / "tschamut_public_benchmark_baseline.yaml").relative_to(ROOT)),
            str((case_dir / "tschamut_public_benchmark_rotational.yaml").relative_to(ROOT)),
        ],
        "terrain_crop": str(dem_path.relative_to(ROOT)),
        "terrain_metadata": str(terrain_metadata_path.relative_to(ROOT)),
        "release_zone_metadata": str(release_zone_path.relative_to(ROOT)),
        "release_points_csv": str(release_csv.relative_to(ROOT)),
        "observed_deposition_csv": str(deposition_csv.relative_to(ROOT)),
        "swissalti3d_tile_url": SWISSALTI_TILE_URL,
        "swissalti3d_tile_sha256": sha256_file(swissalti_tif),
        "tschamut_scan_url": TSCHAMUT_SCAN_URL,
        "tschamut_scan_sha256": sha256_file(scan_zip),
        "tschamut_lps_url": TSCHAMUT_LPS_URL,
        "tschamut_lps_sha256": sha256_file(lps_zip),
        "transform": {
            "method": transform.method,
            "lv03_e_offset_m": transform.lv03_e_offset_m,
            "lv03_n_offset_m": transform.lv03_n_offset_m,
            "vertical_offset_m": transform.vertical_offset_m,
            "registration_quality": qa,
        },
    }
    (output_root / "preparation_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(f"wrote public Tschamut benchmark package to {output_root}")
    return 0


def ensure_download(path: Path, url: str, expected_sha256: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        print(f"download {url}")
        urllib.request.urlretrieve(url, path)
    actual = sha256_file(path)
    if actual != expected_sha256:
        raise SystemExit(f"checksum mismatch for {path}: expected {expected_sha256}, got {actual}")


def derive_lps_to_lv95_transform(scan_zip: Path, method: str) -> LpsToLv95Transform:
    transformer = Transformer.from_crs(21781, 2056, always_xy=True)
    if method == "scan_surface_fit_v1":
        e_offset, n_offset = fit_lps_to_scan_surface_offsets(scan_zip)
        return LpsToLv95Transform(
            lv03_e_offset_m=e_offset,
            lv03_n_offset_m=n_offset,
            vertical_offset_m=1600.0,
            method="scan_surface_fit_v1",
            transformer=transformer,
        )
    if method == "overview_offset_v1":
        # Public OverviewAllTests.txt header: "Tachymeter (Local coordinates minus 696608/167635/1600)".
        # This applies to the overview tachymeter coordinates, not necessarily to the LPS-splined rows.
        return LpsToLv95Transform(
            lv03_e_offset_m=696608.0,
            lv03_n_offset_m=167635.0,
            vertical_offset_m=1600.0,
            method="overview_offset_v1",
            transformer=transformer,
        )
    if method == "bbox_align_v1":
        scan_points = read_tschamut_scan_points(scan_zip)
        lps_points = read_lps_xy_points(ROOT / "data" / "raw" / "tschamut2014" / "trajectoriesfromlps.zip")
        e_offset = min(e for e, _, _ in scan_points) - min(x for x, _, _ in lps_points)
        n_offset = min(n for _, n, _ in scan_points) - min(y for _, y, _ in lps_points)
        return LpsToLv95Transform(
            lv03_e_offset_m=e_offset,
            lv03_n_offset_m=n_offset,
            vertical_offset_m=1600.0,
            method="bbox_align_v1",
            transformer=transformer,
        )
    raise SystemExit(f"unsupported transform method: {method}")


def fit_lps_to_scan_surface_offsets(scan_zip: Path) -> tuple[float, float]:
    try:
        from scipy.spatial import cKDTree  # type: ignore
    except ImportError as exc:
        raise SystemExit("scan_surface_fit_v1 requires scipy.spatial.cKDTree") from exc

    scan_points = read_tschamut_scan_points(scan_zip)
    lps_points = read_lps_xy_points(ROOT / "data" / "raw" / "tschamut2014" / "trajectoriesfromlps.zip")
    scan_xy = np.asarray([(e, n) for e, n, _ in scan_points], dtype=float)
    scan_z = np.asarray([z for _, _, z in scan_points], dtype=float)
    lps_xy_full = np.asarray([(x, y) for x, y, _ in lps_points], dtype=float)
    lps_z_full = np.asarray([z for _, _, z in lps_points], dtype=float)
    stride = max(1, len(lps_points) // 2500)
    lps_xy = lps_xy_full[::stride]
    lps_z = lps_z_full[::stride]
    tree = cKDTree(scan_xy)
    bbox = derive_lps_to_lv95_transform(scan_zip, "bbox_align_v1")
    center = np.asarray([bbox.lv03_e_offset_m, bbox.lv03_n_offset_m], dtype=float)

    def score(offset: np.ndarray) -> float:
        _, indices = tree.query(lps_xy + offset, k=1)
        residual = lps_z - scan_z[indices]
        return float(np.sqrt(np.mean(residual**2)))

    for step_m, span_m in ((10.0, 80.0), (2.0, 20.0), (0.5, 5.0), (0.1, 1.0)):
        best_offset = center
        best_score = score(center)
        for e_offset in np.arange(center[0] - span_m, center[0] + span_m + 1e-9, step_m):
            for n_offset in np.arange(center[1] - span_m, center[1] + span_m + 1e-9, step_m):
                candidate = np.asarray([e_offset, n_offset], dtype=float)
                candidate_score = score(candidate)
                if candidate_score < best_score:
                    best_score = candidate_score
                    best_offset = candidate
        center = best_offset
    return float(center[0]), float(center[1])


def read_tschamut_scan_points(scan_zip: Path) -> list[tuple[float, float, float]]:
    points: list[tuple[float, float, float]] = []
    with zipfile.ZipFile(scan_zip) as archive:
        with archive.open("SupplData_VolkweinEtAl2018/DEM_Tschamut.xyz") as file:
            next(file)
            for line in file:
                parts = line.decode("utf-8", errors="replace").split()
                if len(parts) >= 3:
                    points.append((float(parts[0]), float(parts[1]), float(parts[2])))
    if not points:
        raise SystemExit(f"no slope scan points found in {scan_zip}")
    return points


def read_lps_xy_points(lps_zip: Path) -> list[tuple[float, float, float]]:
    points: list[tuple[float, float, float]] = []
    with zipfile.ZipFile(lps_zip) as archive:
        text = archive.read("all_LPS_splined.txt").decode("utf-8-sig", errors="replace")
    for row in csv.reader(text.splitlines(), delimiter="\t"):
        if len(row) < 9 or not row[1].strip():
            continue
        try:
            points.append((float(row[6]), float(row[7]), float(row[8])))
        except ValueError:
            continue
    if not points:
        raise SystemExit(f"no LPS trajectory points found in {lps_zip}")
    return points


def registration_quality(scan_zip: Path, active_transform: LpsToLv95Transform) -> dict[str, Any]:
    scan_points = read_tschamut_scan_points(scan_zip)
    lps_points = read_lps_xy_points(ROOT / "data" / "raw" / "tschamut2014" / "trajectoriesfromlps.zip")
    methods = {active_transform.method: active_transform}
    for method in ("scan_surface_fit_v1", "overview_offset_v1", "bbox_align_v1"):
        if method not in methods:
            methods[method] = derive_lps_to_lv95_transform(scan_zip, method)
    comparison: dict[str, Any] = {}
    for name, transform in methods.items():
        comparison[name] = nearest_scan_metrics(scan_points, lps_points, transform)
    return {
        "active_method": active_transform.method,
        "scan_point_count": len(scan_points),
        "lps_point_count": len(lps_points),
        "comparison": comparison,
        "interpretation": (
            "Nearest-neighbour residuals compare transformed LPS trajectory samples against "
            "the public CH1903 slope scan. They are a registration QA diagnostic, not a "
            "survey-control adjustment."
        ),
    }


def nearest_scan_metrics(
    scan_points: list[tuple[float, float, float]],
    lps_points: list[tuple[float, float, float]],
    transform: LpsToLv95Transform,
) -> dict[str, float | int | str]:
    try:
        from scipy.spatial import cKDTree  # type: ignore
    except ImportError as exc:
        raise SystemExit("registration QA requires scipy.spatial.cKDTree") from exc

    scan_xy = np.asarray([(e, n) for e, n, _ in scan_points], dtype=float)
    scan_z = np.asarray([z for _, _, z in scan_points], dtype=float)
    lps_xy = np.asarray([transform.lv03_xy(x, y) for x, y, _ in lps_points], dtype=float)
    lps_z = np.asarray([z for _, _, z in lps_points], dtype=float)
    tree = cKDTree(scan_xy)
    horizontal_distance_m, indices = tree.query(lps_xy, k=1)
    vertical_residual_m = lps_z - scan_z[indices]
    abs_vertical_m = np.abs(vertical_residual_m)
    return {
        "method": transform.method,
        "sample_count": int(len(lps_points)),
        "nearest_horizontal_mean_m": float(np.mean(horizontal_distance_m)),
        "nearest_horizontal_p50_m": float(np.percentile(horizontal_distance_m, 50)),
        "nearest_horizontal_p95_m": float(np.percentile(horizontal_distance_m, 95)),
        "nearest_horizontal_max_m": float(np.max(horizontal_distance_m)),
        "vertical_residual_mean_m": float(np.mean(vertical_residual_m)),
        "vertical_residual_median_m": float(np.median(vertical_residual_m)),
        "vertical_residual_rmse_m": float(np.sqrt(np.mean(vertical_residual_m**2))),
        "vertical_residual_abs_p95_m": float(np.percentile(abs_vertical_m, 95)),
    }


def write_registration_qa(path: Path, qa: dict[str, Any], transform: LpsToLv95Transform) -> None:
    payload = {
        "schema_version": "tschamut_registration_qa_v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "active_transform": {
            "method": transform.method,
            "lv03_e_offset_m": transform.lv03_e_offset_m,
            "lv03_n_offset_m": transform.lv03_n_offset_m,
            "vertical_offset_m": transform.vertical_offset_m,
        },
        "quality": qa,
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def write_registration_overlay_svg(path: Path, scan_zip: Path, transform: LpsToLv95Transform) -> None:
    scan_points = read_tschamut_scan_points(scan_zip)
    lps_points = read_lps_xy_points(ROOT / "data" / "raw" / "tschamut2014" / "trajectoriesfromlps.zip")
    scan_stride = max(1, len(scan_points) // 2500)
    lps_stride = max(1, len(lps_points) // 2500)
    scan_lv95 = [transform.transformer.transform(e, n) for e, n, _ in scan_points[::scan_stride]]
    lps_lv95 = [transform.xy(x, y) for x, y, _ in lps_points[::lps_stride]]
    write_point_overlay_svg(
        path,
        title=f"Tschamut registration QA ({transform.method})",
        layers=[
            ("public slope scan sample", scan_lv95, "#707070", 1.2),
            ("transformed LPS sample", lps_lv95, "#d62728", 1.5),
        ],
    )


def write_release_deposition_overlay_svg(
    path: Path,
    releases: list[dict[str, str]],
    depositions: list[dict[str, str]],
    crop: CropInfo,
) -> None:
    release_points = [(float(row["x_m"]), float(row["y_m"])) for row in releases]
    deposition_points = [(float(row["x_m"]), float(row["y_m"])) for row in depositions]
    crop_outline = [
        (crop.xmin, crop.ymin),
        (crop.xmax, crop.ymin),
        (crop.xmax, crop.ymax),
        (crop.xmin, crop.ymax),
        (crop.xmin, crop.ymin),
    ]
    write_point_overlay_svg(
        path,
        title="Tschamut public benchmark release/deposition crop QA",
        layers=[
            ("swissALTI3D crop outline", crop_outline, "#444444", 1.0),
            ("release points", release_points, "#1f77b4", 4.0),
            ("observed deposition points", deposition_points, "#2ca02c", 4.0),
        ],
        polyline_layer_names={"swissALTI3D crop outline"},
    )


def write_point_overlay_svg(
    path: Path,
    *,
    title: str,
    layers: list[tuple[str, list[tuple[float, float]], str, float]],
    polyline_layer_names: set[str] | None = None,
) -> None:
    polyline_layer_names = polyline_layer_names or set()
    all_points = [point for _, points, _, _ in layers for point in points]
    if not all_points:
        return
    width = 900
    height = 700
    margin = 40
    xmin = min(x for x, _ in all_points)
    xmax = max(x for x, _ in all_points)
    ymin = min(y for _, y in all_points)
    ymax = max(y for _, y in all_points)
    span_x = max(xmax - xmin, 1.0)
    span_y = max(ymax - ymin, 1.0)

    def project(point: tuple[float, float]) -> tuple[float, float]:
        x, y = point
        px = margin + (x - xmin) / span_x * (width - 2 * margin)
        py = height - margin - (y - ymin) / span_y * (height - 2 * margin)
        return px, py

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<style>text{font-family:Arial,sans-serif;font-size:13px}.title{font-size:18px;font-weight:bold}</style>",
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="white"/>',
        f'<text class="title" x="{margin}" y="24">{title}</text>',
        f'<text x="{margin}" y="{height - 12}">Extent: x {xmin:.1f}-{xmax:.1f}, y {ymin:.1f}-{ymax:.1f} m EPSG:2056</text>',
    ]
    legend_y = 48
    for name, points, color, radius in layers:
        lines.append(f'<circle cx="{margin}" cy="{legend_y - 4}" r="5" fill="{color}" opacity="0.8"/>')
        lines.append(f'<text x="{margin + 14}" y="{legend_y}">{name}</text>')
        legend_y += 18
        projected = [project(point) for point in points]
        if name in polyline_layer_names:
            coords = " ".join(f"{x:.2f},{y:.2f}" for x, y in projected)
            lines.append(f'<polyline points="{coords}" fill="none" stroke="{color}" stroke-width="2"/>')
        else:
            for x, y in projected:
                lines.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{radius:.1f}" fill="{color}" opacity="0.55"/>')
    lines.append("</svg>")
    path.write_text("\n".join(lines) + "\n")


def transform_release_rows(rows: list[dict[str, str]], transform: LpsToLv95Transform) -> list[dict[str, str]]:
    transformed = []
    for row in rows:
        x, y = transform.xy(float(row["x_m"]), float(row["y_m"]))
        out = dict(row)
        out["x_m"] = f"{x:.6f}"
        out["y_m"] = f"{y:.6f}"
        out["ground_z_m"] = f"{transform.z(float(row['ground_z_m'])):.6f}"
        out["z_m"] = f"{transform.z(float(row['z_m'])):.6f}"
        out["source"] = f"{row['source']}; transformed to EPSG:2056 by public benchmark {transform.method}"
        transformed.append(out)
    return transformed


def transform_deposition_rows(rows: list[dict[str, str]], transform: LpsToLv95Transform) -> list[dict[str, str]]:
    transformed = []
    for row in rows:
        x, y = transform.xy(float(row["x_m"]), float(row["y_m"]))
        rx, ry = transform.xy(float(row["release_x_m"]), float(row["release_y_m"]))
        out = dict(row)
        out["x_m"] = f"{x:.6f}"
        out["y_m"] = f"{y:.6f}"
        out["release_x_m"] = f"{rx:.6f}"
        out["release_y_m"] = f"{ry:.6f}"
        out["ground_z_m"] = f"{transform.z(float(row['ground_z_m'])):.6f}"
        out["z_m"] = f"{transform.z(float(row['z_m'])):.6f}"
        out["release_z_m"] = f"{transform.z(float(row['release_z_m'])):.6f}"
        out["source"] = f"{row['source']}; transformed to EPSG:2056 by public benchmark {transform.method}"
        transformed.append(out)
    return transformed


@dataclass(frozen=True)
class CropInfo:
    xmin: float
    ymin: float
    xmax: float
    ymax: float
    ncols: int
    nrows: int
    cell_size: float


def write_swissalti_crop(
    tile_path: Path,
    output_path: Path,
    rows: Iterable[dict[str, str]],
    *,
    padding_m: float,
) -> CropInfo:
    points = [(float(row["x_m"]), float(row["y_m"])) for row in rows]
    xmin_req = min(x for x, _ in points) - padding_m
    xmax_req = max(x for x, _ in points) + padding_m
    ymin_req = min(y for _, y in points) - padding_m
    ymax_req = max(y for _, y in points) + padding_m

    image = Image.open(tile_path)
    arr = np.asarray(image, dtype=float)
    tie = image.tag_v2.get(33922)
    scale = image.tag_v2.get(33550)
    if tie is None or scale is None:
        raise SystemExit(f"missing GeoTIFF tiepoint/pixel scale tags in {tile_path}")
    origin_x = float(tie[3])
    origin_y = float(tie[4])
    cell = float(scale[0])
    tile_nrows, tile_ncols = arr.shape
    tile_xmax = origin_x + tile_ncols * cell
    tile_ymin = origin_y - tile_nrows * cell

    col0 = max(0, int(math.floor((xmin_req - origin_x) / cell)))
    col1 = min(tile_ncols, int(math.ceil((xmax_req - origin_x) / cell)))
    row0 = max(0, int(math.floor((origin_y - ymax_req) / cell)))
    row1 = min(tile_nrows, int(math.ceil((origin_y - ymin_req) / cell)))
    if col0 >= col1 or row0 >= row1:
        raise SystemExit("requested Tschamut public benchmark crop lies outside the swissALTI3D tile")

    crop = arr[row0:row1, col0:col1]
    xll = origin_x + col0 * cell
    ymax = origin_y - row0 * cell
    yll = origin_y - row1 * cell
    nrows, ncols = crop.shape
    if xll < origin_x or xll + ncols * cell > tile_xmax or yll < tile_ymin or ymax > origin_y:
        raise SystemExit("internal crop bounds error")

    lines = [
        f"ncols {ncols}",
        f"nrows {nrows}",
        f"xllcorner {xll:.6f}",
        f"yllcorner {yll:.6f}",
        f"cellsize {cell:.6f}",
        f"NODATA_value {NODATA:g}",
    ]
    for row in crop:
        lines.append(" ".join(f"{float(value):.6f}" for value in row))
    output_path.write_text("\n".join(lines) + "\n")
    return CropInfo(xmin=xll, ymin=yll, xmax=xll + ncols * cell, ymax=ymax, ncols=ncols, nrows=nrows, cell_size=cell)


def write_terrain_metadata(
    path: Path,
    crop: CropInfo,
    dem_path: Path,
    dem_sha256: str,
    tile_path: Path,
    transform: LpsToLv95Transform,
    padding_m: float,
) -> None:
    metadata = {
        "schema_version": 1,
        "tile_id": f"tschamut_public_benchmark_{SWISSALTI_TILE_ID}",
        "source_dataset": "swisstopo_swissalti3d",
        "source_product": "swissALTI3D 2 m COG",
        "source_url": SWISSALTI_TILE_URL,
        "source_filename": str(tile_path.relative_to(ROOT)),
        "source_file_present": True,
        "download_status": "downloaded_public_open_data_to_ignored_raw_cache",
        "license": "swisstopo open data terms; cite swisstopo and preserve provenance",
        "coordinate_reference_system": {
            "epsg": 2056,
            "horizontal_name": "CH1903+ / LV95",
            "vertical_datum": "LN02",
            "coordinate_unit": "m",
            "height_unit": "m",
        },
        "raster": {
            "format": "ESRI ASCII GRID",
            "resolution_m": crop.cell_size,
            "width_px": crop.ncols,
            "height_px": crop.nrows,
            "nodata": NODATA,
        },
        "extent_lv95_m": {
            "xmin": crop.xmin,
            "ymin": crop.ymin,
            "xmax": crop.xmax,
            "ymax": crop.ymax,
        },
        "preprocessing": {
            "status": "public_benchmark_crop_generated",
            "crop_extent_lv95_m": {
                "xmin": crop.xmin,
                "ymin": crop.ymin,
                "xmax": crop.xmax,
                "ymax": crop.ymax,
            },
            "resampling_method": "none; integer-window crop from 2 m source COG",
            "raw_sha256": sha256_file(tile_path),
            "processed_sha256": dem_sha256,
            "tool": "scripts/prepare_tschamut_public_benchmark.py",
            "processed_utc": datetime.now(timezone.utc).isoformat(),
        },
        "provenance": {
            "intended_use": "public_tschamut_benchmark_reproduction",
            "notes": [
                "Release/deposition observations are EnviDat Tschamut 2014 LPS-derived rows transformed to LV95.",
                f"LPS to Swiss coordinates use {transform.method} against public Tschamut metadata/slope scan.",
                f"Transform offsets: E={transform.lv03_e_offset_m:.6f}, N={transform.lv03_n_offset_m:.6f}, Z={transform.vertical_offset_m:.6f}; padding={padding_m:.1f} m.",
                "No model parameters are tuned by this preprocessing step.",
            ],
        },
    }
    write_yaml(path, metadata)


def write_release_zone_metadata(
    path: Path,
    releases: list[dict[str, str]],
    crop: CropInfo,
    seed: int,
    run_limit: int,
) -> None:
    xs = [float(row["x_m"]) for row in releases]
    ys = [float(row["y_m"]) for row in releases]
    pad = 5.0
    polygon = [
        [max(crop.xmin, min(xs) - pad), max(crop.ymin, min(ys) - pad)],
        [min(crop.xmax, max(xs) + pad), max(crop.ymin, min(ys) - pad)],
        [min(crop.xmax, max(xs) + pad), min(crop.ymax, max(ys) + pad)],
        [max(crop.xmin, min(xs) - pad), min(crop.ymax, max(ys) + pad)],
    ]
    metadata = {
        "schema_version": 1,
        "source_zone_id": "tschamut_public_lps_release_bbox",
        "coordinate_reference_system": {
            "epsg": 2056,
            "horizontal_name": "CH1903+ / LV95",
            "vertical_datum": "LN02",
            "coordinate_unit": "m",
            "height_unit": "m",
        },
        "geometry": {"type": "Polygon", "coordinates": polygon},
        "sampling": {
            "mode": "deterministic_grid",
            "release_count": run_limit,
            "seed": seed,
        },
        "provenance": {
            "source": "Bounding polygon around transformed public Tschamut LPS release rows.",
            "license": "Derived from EnviDat Tschamut 2014 ODbL/DbCL rows.",
            "notes": [
                "This metadata is for source-area provenance and visual QA; validation cases use observed release_points_csv directly.",
                "No release-zone sampling is used for the benchmark validation metrics.",
            ],
        },
    }
    write_yaml(path, metadata)


def build_case(
    suffix: str,
    contact_model: str,
    dem_path: Path,
    terrain_metadata_path: Path,
    release_csv: Path,
    deposition_csv: Path,
    results_dir: Path,
    seed: int,
    ensemble_size: int,
    first_release: dict[str, str],
    shape_metadata_path: Path | None,
) -> dict[str, Any]:
    case_id = f"validation_tschamut_public_benchmark_{suffix}"
    case = {
        "case_id": case_id,
        "title": f"Tschamut public benchmark reproduction ({suffix})",
        "level": 5,
        "description": (
            "Public-data Tschamut benchmark reproduction using EnviDat observations transformed to LV95 "
            "and a swissALTI3D 2 m public terrain crop. No parameters are tuned."
        ),
        "terrain": {
            "type": "ascii_dem_clamped",
            "path": str(dem_path.relative_to(ROOT)),
            "metadata_path": str(terrain_metadata_path.relative_to(ROOT)),
        },
        "block": {
            "mass": float(first_release["mass_kg"]),
            "radius": float(first_release["radius_m"]),
        },
        "release": {
            "position": [
                float(first_release["x_m"]),
                float(first_release["y_m"]),
                float(first_release["z_m"]),
            ],
            "velocity": [
                float(first_release["vx_mps"]),
                float(first_release["vy_mps"]),
                float(first_release["vz_mps"]),
            ],
        },
        "parameters": {
            "gravity": 9.81,
            "normal_restitution": 0.25,
            "tangential_restitution": 0.85,
            "friction_coefficient": 0.45,
            "contact_model": contact_model,
            "roughness_model": "stochastic_contact_v1",
            "roughness_std_normal": 0.08,
            "roughness_std_tangent": 0.06,
            "roughness_std_angle": 0.08,
        },
        "simulation": {"dt": 0.02, "t_max": 18.0, "max_steps": 900, "stop_velocity": 0.1},
        "random": {"seed": seed, "ensemble_size": ensemble_size},
        "hazard_layers": {
            "statistics": {
                "kinetic_energy_exceedance_j": [1000.0, 10000.0],
                "jump_height_exceedance_m": [0.5, 2.0],
                "velocity_exceedance_mps": [5.0, 10.0],
            }
        },
        "validation_scope": {
            "type": "public-benchmark-reproduction",
            "note": "Scientific diagnostic only; no tuning, operational validity, or proprietary-model equivalence claim.",
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
            "tolerances": {},
        },
        "outputs": {
            "diagnostics_json": str((results_dir / f"{case_id}_metrics.json").relative_to(ROOT)),
            "manifest_json": str((results_dir / f"{case_id}_manifest.json").relative_to(ROOT)),
            "ensemble_deposition_csv": str((results_dir / f"{case_id}_deposition.csv").relative_to(ROOT)),
            "ensemble_trajectories_dir": str((results_dir / f"{case_id}_trajectories").relative_to(ROOT)),
            "ensemble_impact_events_dir": str((results_dir / f"{case_id}_impacts").relative_to(ROOT)),
            "trajectory_metadata_csv": str((results_dir / f"{case_id}_trajectory_metadata.csv").relative_to(ROOT)),
        },
        "references": {
            "dataset": "tschamut2014",
            "literature": [
                "Volkwein, A., Gerber, W. (2018). Repetitive trajectory testing in Tschamut 2014. EnviDat. https://doi.org/10.16904/envidat.34.",
                "Volkwein et al. (2018). Repetitive Rockfall Trajectory Testing. Geosciences 8(3), 88. https://doi.org/10.3390/geosciences8030088.",
                "swisstopo swissALTI3D public terrain data, LV95/LN02, 2 m COG tile.",
            ],
            "notes": [
                "Uses scan_surface_fit_v1 coordinate preprocessing by default; bbox_align_v1 and overview_offset_v1 remain fallback/comparison modes.",
                "No restitution, friction, roughness, scarring, or contact-model parameters are tuned to these results.",
            ],
        },
    }
    if shape_metadata_path is not None:
        case["block_shape"] = {"metadata_path": str(shape_metadata_path.relative_to(ROOT))}
    return case


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as file:
        return [dict(row) for row in csv.DictReader(file)]


def select_observation_rows(
    release_rows: list[dict[str, str]],
    deposition_rows: list[dict[str, str]],
    run_limit: int,
    run_ids_arg: str | None,
    block_id: str | None,
) -> tuple[list[dict[str, str]], list[dict[str, str]], dict[str, Any]]:
    releases_by_id = {row["trajectory_id"]: row for row in release_rows}
    depositions_by_id = {row["trajectory_id"]: row for row in deposition_rows}
    shared_rows = [row for row in release_rows if row["trajectory_id"] in depositions_by_id]
    if block_id:
        shared_rows = [row for row in shared_rows if row.get("block_id") == block_id]
        if not shared_rows:
            raise SystemExit(f"--block-id {block_id} selected no complete public LPS runs")
    shared_ids = [row["trajectory_id"] for row in shared_rows]
    if run_ids_arg:
        selected_ids = [item.strip() for item in run_ids_arg.split(",") if item.strip()]
        if not selected_ids:
            raise SystemExit("--run-ids was provided but no trajectory IDs were parsed")
        missing = [run_id for run_id in selected_ids if run_id not in releases_by_id or run_id not in depositions_by_id]
        if missing:
            raise SystemExit(f"--run-ids contains unknown or incomplete trajectory IDs: {', '.join(missing)}")
        if block_id:
            mismatched = [run_id for run_id in selected_ids if releases_by_id[run_id].get("block_id") != block_id]
            if mismatched:
                raise SystemExit(
                    f"--run-ids contains IDs outside --block-id {block_id}: {', '.join(mismatched)}"
                )
        mode = "explicit_run_ids"
    else:
        if run_limit <= 0:
            raise SystemExit("--run-limit must be positive")
        selected_ids = shared_ids[:run_limit]
        mode = "first_n_processed_runs_for_block" if block_id else "first_n_processed_runs"
    return (
        [releases_by_id[run_id] for run_id in selected_ids],
        [depositions_by_id[run_id] for run_id in selected_ids],
        {
            "mode": mode,
            "available_shared_run_count": len(shared_ids),
            "selected_run_count": len(selected_ids),
            "selected_trajectory_ids": selected_ids,
            "selected_block_id": block_id,
        },
    )


def single_selected_block_id(rows: list[dict[str, str]]) -> str | None:
    block_ids = {row.get("block_id") for row in rows if row.get("block_id")}
    if len(block_ids) == 1:
        return next(iter(block_ids))
    return None


def resolve_shape_metadata_path(path: Path | None, release_rows: list[dict[str, str]]) -> Path | None:
    if path is None:
        return None
    if single_selected_block_id(release_rows) is None:
        raise SystemExit(
            "--block-shape-metadata requires all selected runs to share one block_id; "
            "use --block-id or explicit single-block --run-ids"
        )
    resolved = path if path.is_absolute() else ROOT / path
    if not resolved.exists():
        raise SystemExit(f"--block-shape-metadata does not exist: {resolved}")
    return resolved


def summarize_selected_runs(rows: list[dict[str, str]]) -> dict[str, Any]:
    masses = [float(row["mass_kg"]) for row in rows if row.get("mass_kg")]
    radii = [float(row["radius_m"]) for row in rows if row.get("radius_m")]
    block_counts: dict[str, int] = {}
    for row in rows:
        block_id = row.get("block_id", "unknown")
        block_counts[block_id] = block_counts.get(block_id, 0) + 1
    summary: dict[str, Any] = {
        "trajectory_count": len(rows),
        "block_id_counts": dict(sorted(block_counts.items())),
    }
    if masses:
        summary["mass_kg"] = {
            "min": min(masses),
            "max": max(masses),
            "mean": sum(masses) / len(masses),
        }
    if radii:
        summary["radius_m"] = {
            "min": min(radii),
            "max": max(radii),
            "mean": sum(radii) / len(radii),
        }
    return summary


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_yaml(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(value, sort_keys=False))


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
