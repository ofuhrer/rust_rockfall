#!/usr/bin/env python3
"""Generate deterministic terrain-driven release-zone candidate metrics.

This helper stays read-only unless an explicit output root is requested. It
uses the committed Tschamut public pilot terrain crop, terrain metadata, and
frozen source-zone metadata to report a fixed heuristic screening over the
Balfrin/Tschamut AOI and can emit deterministic GIS-readable candidate masks
and polygon bundles for dry-run workflows. It does not emit a validated
release zone, tune thresholds, download public data, or authorize any ensemble
work.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np

try:
    import yaml  # type: ignore
except ImportError as exc:  # pragma: no cover - environment setup.
    raise SystemExit("PyYAML is required; install with `python3 -m pip install PyYAML`") from exc


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "terrain_release_zone_candidate_metrics_v1"
PRODUCT_SCHEMA_VERSION = "terrain_release_zone_candidate_products_v1"
DEFAULT_TERRAIN_CROP = ROOT / "data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_swissalti3d_crop.asc"
DEFAULT_TERRAIN_METADATA = ROOT / "data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_swissalti3d_metadata.yaml"
DEFAULT_SOURCE_ZONE_METADATA = ROOT / "data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_source_zone_metadata_v1.yaml"
DEFAULT_OUTPUT_MODE = "both"

MIN_CANDIDATE_SLOPE_DEG = 30.0
MAX_CANDIDATE_SLOPE_DEG = 55.0
NODATA_SENTINEL = -9999.0


class TerrainReleaseZoneCandidateMetricsError(ValueError):
    """User-facing dry-run helper error."""


def _load_module(module_name: str, filename: str):
    path = ROOT / "scripts" / filename
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load helper module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


TERRAIN_PREPROCESSING = _load_module("aoi_terrain_preprocessing_planner", "plan_aoi_terrain_preprocessing.py")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--terrain-crop", type=Path, default=None)
    parser.add_argument("--terrain-metadata", type=Path, default=None)
    parser.add_argument("--source-zone-metadata", type=Path, default=None)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    parser.add_argument("--output-root", type=Path, default=None, help="optional GIS-readable candidate product output root")
    parser.add_argument(
        "--output-mode",
        choices=("mask", "polygon", "both"),
        default=DEFAULT_OUTPUT_MODE,
        help="candidate product type to emit when --output-root is set",
    )
    args = parser.parse_args(argv)

    try:
        report = build_report(
            repo_root=args.repo_root,
            terrain_crop_path=args.terrain_crop,
            terrain_metadata_path=args.terrain_metadata,
            source_zone_metadata_path=args.source_zone_metadata,
            output_root=args.output_root,
            output_mode=args.output_mode,
        )
    except TerrainReleaseZoneCandidateMetricsError as exc:
        print(f"terrain release-zone candidate metrics error: {exc}", file=sys.stderr)
        return 2

    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    output = json.dumps(report, indent=2, sort_keys=True) if args.format == "json" else render_text_report(report)
    print(output)
    return 0 if report["candidate_metrics_status"] == "ready" else 2


def build_report(
    *,
    repo_root: Path | None = None,
    terrain_crop_path: Path | None = None,
    terrain_metadata_path: Path | None = None,
    source_zone_metadata_path: Path | None = None,
    output_root: Path | None = None,
    output_mode: str = DEFAULT_OUTPUT_MODE,
) -> dict[str, Any]:
    repo_root = repo_root or ROOT
    terrain_crop_path = terrain_crop_path or default_repo_path(repo_root, DEFAULT_TERRAIN_CROP)
    terrain_metadata_path = terrain_metadata_path or default_repo_path(repo_root, DEFAULT_TERRAIN_METADATA)
    source_zone_metadata_path = source_zone_metadata_path or default_repo_path(repo_root, DEFAULT_SOURCE_ZONE_METADATA)
    terrain_crop_path = resolve_path(repo_root, terrain_crop_path)
    terrain_metadata_path = resolve_path(repo_root, terrain_metadata_path)
    source_zone_metadata_path = resolve_path(repo_root, source_zone_metadata_path)
    terrain_catalog_path = terrain_crop_path.parent / "aoi_tile_catalog.yaml"

    required_inputs = [
        terrain_crop_path,
        terrain_metadata_path,
        source_zone_metadata_path,
    ]
    missing_inputs = [display_path(path, repo_root) for path in required_inputs if not path.exists()]
    if missing_inputs:
        return blocked_report(repo_root=repo_root, missing_inputs=missing_inputs)

    terrain = read_esri_ascii_grid(terrain_crop_path)
    terrain_metadata = load_yaml(terrain_metadata_path)
    source_zone_metadata = load_yaml(source_zone_metadata_path)
    terrain_preprocessing = build_terrain_preprocessing_report(
        repo_root=repo_root,
        terrain_crop_path=terrain_crop_path,
        terrain_metadata_path=terrain_metadata_path,
        terrain_catalog_path=terrain_catalog_path if terrain_catalog_path.exists() else None,
    )
    if terrain_preprocessing["terrain_preprocessing_status"] not in {"ready", "not_available"}:
        return blocked_report(
            repo_root=repo_root,
            missing_inputs=missing_inputs,
            terrain_preprocessing=terrain_preprocessing,
            blocked_status=terrain_preprocessing["terrain_preprocessing_status"],
        )

    screening = build_screening_criteria(terrain_metadata, source_zone_metadata)
    screening.update(build_screening_criteria_from_terrain_package(terrain_preprocessing))
    candidate_mask, terrain_masks = compute_candidate_masks(terrain, source_zone_metadata, screening)
    terrain_summary = build_terrain_summary(terrain)
    candidate_summary = build_candidate_summary(terrain, candidate_mask, terrain_masks, screening)
    excluded_area_summary = build_excluded_area_summary(terrain_masks, terrain, screening)
    frozen_footprint_summary = build_frozen_footprint_summary(terrain, source_zone_metadata, terrain_masks)
    candidate_footprint_comparison = build_candidate_footprint_comparison(terrain, terrain_masks)
    provenance = build_provenance(terrain_crop_path, terrain_metadata_path, source_zone_metadata_path, terrain_metadata, source_zone_metadata)

    report = {
        "schema_version": SCHEMA_VERSION,
        "candidate_metrics_status": "ready",
        "candidate_release_zone_set_status": "not_emitted",
        "candidate_release_zone_interpretation": "heuristic_workflow_input_only",
        "candidate_site_id": "tschamut_public_pilot",
        "candidate_site_name": "Balfrin / Tschamut AOI",
        "candidate_selection_rationale": (
            "The committed Tschamut public pilot terrain and frozen source-zone metadata are the "
            "reproducible Balfrin/Tschamut AOI inputs available in-repo."
        ),
        "repo_root": str(repo_root),
        "site_extent": terrain_metadata.get("extent_lv95_m", {}),
        "screening_criteria": screening,
        "terrain_inputs": {
            "terrain_crop_path": display_path(terrain_crop_path, repo_root),
            "terrain_metadata_path": display_path(terrain_metadata_path, repo_root),
            "terrain_crop_sha256": sha256_file(terrain_crop_path),
            "terrain_metadata_sha256": sha256_file(terrain_metadata_path),
            "terrain_download_status": terrain_metadata.get("download_status"),
            "terrain_license": terrain_metadata.get("license"),
            "terrain_preprocessing_status": terrain_preprocessing["terrain_preprocessing_status"],
            "terrain_preprocessing_manifest_path": terrain_preprocessing.get("terrain_preprocessing_manifest_path"),
            "terrain_preprocessing_package": terrain_preprocessing["terrain_preprocessing_package"],
        },
        "terrain_preprocessing": terrain_preprocessing,
        "source_zone_inputs": build_source_zone_inputs(source_zone_metadata_path, source_zone_metadata, repo_root),
        "terrain_summary": terrain_summary,
        "candidate_summary": candidate_summary,
        "excluded_area_summary": excluded_area_summary,
        "frozen_source_zone_footprint": frozen_footprint_summary,
        "candidate_footprint_comparison": candidate_footprint_comparison,
        "provenance": provenance,
        "claim_boundaries": {
            "heuristic_workflow_input_only": True,
            "validated_release_zone_evidence": False,
            "field_validation_claims_allowed": False,
            "physical_release_probability_claims_allowed": False,
            "scale_up_authorized": False,
            "operational_claims_allowed": False,
            "notes": [
                "candidate cells are heuristic workflow inputs, not validated release zones",
                "slope screening is fixed and deterministic",
                "no annual-frequency, risk, exposure, or vulnerability claim is authorized here",
            ],
        },
        "blocked_missing_inputs": [],
        "blocked_reason": "",
        "scale_up_authorized": False,
        "operational_claims_allowed": False,
        "candidate_release_zone_products": {
            "output_status": "not_emitted",
            "output_mode": output_mode,
            "output_root": display_path(Path(output_root), repo_root) if output_root is not None else None,
        },
    }
    if output_root is not None:
        candidate_products = emit_candidate_products(
            report=report,
            terrain=terrain,
            terrain_masks=terrain_masks,
            source_zone_metadata=source_zone_metadata,
            repo_root=repo_root,
            output_root=output_root,
            output_mode=output_mode,
        )
        report["candidate_release_zone_set_status"] = "emitted"
        report["candidate_release_zone_products"] = candidate_products
    return report


def blocked_report(
    *,
    repo_root: Path,
    missing_inputs: list[str],
    terrain_preprocessing: dict[str, Any] | None = None,
    blocked_status: str = "blocked_missing_inputs",
) -> dict[str, Any]:
    terrain_preprocessing = terrain_preprocessing or {
        "terrain_preprocessing_status": "not_available",
        "terrain_preprocessing_manifest_path": None,
        "terrain_preprocessing_package": {
            "preprocessing_status": "not_available",
            "source_tile_ids": [],
            "source_tiles": [],
            "output_roots": {
                "raw_swisstopo_cache_root": str(repo_root / "data/raw/swisstopo/tschamut_public_pilot"),
                "processed_input_root": str(default_repo_path(repo_root, DEFAULT_TERRAIN_CROP).parent),
                "output_root": str(default_repo_path(repo_root, DEFAULT_TERRAIN_CROP).parent),
            },
        },
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "candidate_metrics_status": blocked_status,
        "candidate_release_zone_set_status": "not_emitted",
        "candidate_release_zone_interpretation": "not_claimed",
        "candidate_site_id": "tschamut_public_pilot",
        "candidate_site_name": "Balfrin / Tschamut AOI",
        "candidate_selection_rationale": (
            "The committed Tschamut public pilot terrain and frozen source-zone metadata are the "
            "reproducible Balfrin/Tschamut AOI inputs available in-repo."
        ),
        "repo_root": str(repo_root),
        "site_extent": {},
        "screening_criteria": screening_criteria_stub(),
        "terrain_inputs": {
            "terrain_crop_path": display_path(default_repo_path(repo_root, DEFAULT_TERRAIN_CROP), repo_root),
            "terrain_metadata_path": display_path(default_repo_path(repo_root, DEFAULT_TERRAIN_METADATA), repo_root),
            "terrain_preprocessing_status": terrain_preprocessing["terrain_preprocessing_status"],
            "terrain_preprocessing_manifest_path": terrain_preprocessing.get("terrain_preprocessing_manifest_path"),
            "terrain_preprocessing_package": terrain_preprocessing["terrain_preprocessing_package"],
        },
        "source_zone_inputs": {
            "source_zone_metadata_path": display_path(
                default_repo_path(repo_root, DEFAULT_SOURCE_ZONE_METADATA), repo_root
            ),
        },
        "terrain_preprocessing": terrain_preprocessing,
        "terrain_summary": {},
        "candidate_summary": {},
        "excluded_area_summary": [],
        "frozen_source_zone_footprint": {},
        "candidate_footprint_comparison": {
            "comparison_status": "blocked_missing_inputs",
            "candidate_excludes_frozen_footprint": False,
        },
        "provenance": {},
        "claim_boundaries": {
            "heuristic_workflow_input_only": True,
            "validated_release_zone_evidence": False,
            "field_validation_claims_allowed": False,
            "physical_release_probability_claims_allowed": False,
            "scale_up_authorized": False,
            "operational_claims_allowed": False,
            "notes": [
                "candidate cells are heuristic workflow inputs, not validated release zones",
                "slope screening is fixed and deterministic",
                "no annual-frequency, risk, exposure, or vulnerability claim is authorized here",
            ],
        },
        "blocked_missing_inputs": missing_inputs,
        "blocked_reason": (
            terrain_preprocessing.get("blocked_reason")
            if terrain_preprocessing["terrain_preprocessing_status"] not in {"not_available", "ready"}
            else "required public inputs are missing: " + ", ".join(missing_inputs)
        ),
        "scale_up_authorized": False,
        "operational_claims_allowed": False,
        "candidate_release_zone_products": {
            "output_status": "not_emitted",
            "output_mode": DEFAULT_OUTPUT_MODE,
            "output_root": None,
        },
    }


def screening_criteria_stub() -> dict[str, Any]:
    return {
        "slope_algorithm": "horn_3x3_cell_center_deg",
        "minimum_finite_neighborhood": "3x3",
        "candidate_slope_min_deg": MIN_CANDIDATE_SLOPE_DEG,
        "candidate_slope_max_deg": MAX_CANDIDATE_SLOPE_DEG,
        "exclude_nodata": True,
        "exclude_incomplete_neighborhood": True,
        "exclude_frozen_release_zone_footprint": True,
        "frozen_release_zone_footprint_mask": "cell_center_in_polygon",
    }


def build_screening_criteria(terrain_metadata: dict[str, Any], source_zone_metadata: dict[str, Any]) -> dict[str, Any]:
    criteria = screening_criteria_stub()
    criteria.update(
        {
            "terrain_crs_epsg": terrain_metadata.get("coordinate_reference_system", {}).get("epsg"),
            "terrain_vertical_datum": terrain_metadata.get("coordinate_reference_system", {}).get("vertical_datum"),
            "source_zone_id": source_zone_metadata.get("source_zone_id"),
        }
    )
    return criteria


def build_screening_criteria_from_terrain_package(terrain_preprocessing: dict[str, Any]) -> dict[str, Any]:
    if terrain_preprocessing.get("terrain_preprocessing_status") == "not_available":
        return {}
    package = terrain_preprocessing.get("terrain_preprocessing_package") or {}
    if not isinstance(package, dict):
        return {}
    return {
        "terrain_crop_extent_lv95_m": package.get("crop_extent_lv95_m", {}),
        "terrain_resolution_m": package.get("resolution_m"),
        "terrain_crs_epsg": package.get("crs_epsg"),
        "terrain_nodata": package.get("nodata"),
        "terrain_source_tile_ids": package.get("source_tile_ids", []),
    }


def build_terrain_preprocessing_report(
    *,
    repo_root: Path,
    terrain_crop_path: Path,
    terrain_metadata_path: Path,
    terrain_catalog_path: Path | None,
) -> dict[str, Any]:
    if terrain_catalog_path is None:
        return {
            "terrain_preprocessing_status": "not_available",
            "terrain_preprocessing_manifest_path": None,
            "terrain_preprocessing_package": {
                "preprocessing_status": "not_available",
                "crop_extent_lv95_m": {},
                "resolution_m": None,
                "crs_epsg": None,
                "nodata": None,
                "source_tile_ids": [],
                "source_tiles": [],
                "output_roots": {
                    "raw_swisstopo_cache_root": str(repo_root / "data/raw/swisstopo/tschamut_public_pilot"),
                    "processed_input_root": str(terrain_crop_path.parent),
                    "output_root": str(terrain_crop_path.parent),
                },
                "output_paths": {},
                "source_tile_count": 0,
                "manifest_path": None,
            },
            "blocked_reason": "AOI tile catalog is not staged next to the terrain crop",
        }

    return TERRAIN_PREPROCESSING.build_report(
        repo_root=repo_root,
        terrain_crop_path=terrain_crop_path,
        terrain_metadata_path=terrain_metadata_path,
        aoi_tile_catalog_path=terrain_catalog_path,
    )


def build_terrain_summary(terrain: dict[str, Any]) -> dict[str, Any]:
    values = terrain["values"]
    valid_mask = terrain["valid_mask"]
    cell_count = int(values.size)
    valid_cell_count = int(valid_mask.sum())
    cell_area_m2 = terrain["cellsize"] ** 2
    return {
        "cell_count": cell_count,
        "valid_cell_count": valid_cell_count,
        "invalid_cell_count": cell_count - valid_cell_count,
        "cell_area_m2": cell_area_m2,
        "total_area_m2": cell_count * cell_area_m2,
        "valid_area_m2": valid_cell_count * cell_area_m2,
        "elevation_min_m": float(np.nanmin(np.where(valid_mask, values, np.nan))),
        "elevation_max_m": float(np.nanmax(np.where(valid_mask, values, np.nan))),
        "elevation_mean_m": float(np.nanmean(np.where(valid_mask, values, np.nan))),
        "resolution_m": terrain["cellsize"],
        "ncols": terrain["ncols"],
        "nrows": terrain["nrows"],
        "extent_lv95_m": {
            "xmin": terrain["xllcorner"],
            "ymin": terrain["yllcorner"],
            "xmax": terrain["xllcorner"] + terrain["ncols"] * terrain["cellsize"],
            "ymax": terrain["yllcorner"] + terrain["nrows"] * terrain["cellsize"],
        },
    }


def build_source_zone_inputs(
    source_zone_metadata_path: Path,
    source_zone_metadata: dict[str, Any],
    repo_root: Path,
) -> dict[str, Any]:
    vertices = extract_polygon_vertices(source_zone_metadata)
    return {
        "source_zone_metadata_path": display_path(source_zone_metadata_path, repo_root),
        "source_zone_metadata_sha256": sha256_file(source_zone_metadata_path),
        "source_zone_id": source_zone_metadata.get("source_zone_id"),
        "crs_epsg": source_zone_metadata.get("crs_epsg"),
        "vertical_datum": source_zone_metadata.get("vertical_datum"),
        "release_sampling_policy": source_zone_metadata.get("release_sampling_policy", {}),
        "provenance": source_zone_metadata.get("provenance", {}),
        "footprint": {
            "polygon_area_m2_exact": polygon_area(vertices),
            "vertex_count": len(vertices),
            "vertices": vertices,
        },
    }


def build_candidate_summary(
    terrain: dict[str, Any],
    candidate_mask: np.ndarray,
    terrain_masks: dict[str, np.ndarray],
    screening: dict[str, Any],
) -> dict[str, Any]:
    slope_deg = terrain_masks["slope_deg"]
    candidate_values = slope_deg[candidate_mask]
    cell_area_m2 = terrain["cellsize"] ** 2
    candidate_count = int(candidate_mask.sum())
    screenable_count = int(terrain_masks["screenable_mask"].sum())
    valid_interior_count = int(terrain_masks["valid_interior_mask"].sum())
    return {
        "candidate_cell_count": candidate_count,
        "candidate_area_m2": candidate_count * cell_area_m2,
        "candidate_fraction_of_screenable_cells": fraction(candidate_count, screenable_count),
        "candidate_fraction_of_valid_interior_cells": fraction(candidate_count, valid_interior_count),
        "candidate_slope_min_deg": float(np.min(candidate_values)) if candidate_count else None,
        "candidate_slope_max_deg": float(np.max(candidate_values)) if candidate_count else None,
        "candidate_slope_mean_deg": float(np.mean(candidate_values)) if candidate_count else None,
        "candidate_slope_median_deg": float(np.median(candidate_values)) if candidate_count else None,
        "candidate_slope_p95_deg": float(np.quantile(candidate_values, 0.95)) if candidate_count else None,
        "screenable_cell_count": screenable_count,
        "screenable_area_m2": screenable_count * cell_area_m2,
        "screenable_fraction_of_valid_cells": fraction(screenable_count, int(terrain["valid_mask"].sum())),
        "screening_summary": {
            "candidate_slope_min_deg": screening["candidate_slope_min_deg"],
            "candidate_slope_max_deg": screening["candidate_slope_max_deg"],
            "slope_algorithm": screening["slope_algorithm"],
        },
    }


def build_frozen_footprint_summary(
    terrain: dict[str, Any],
    source_zone_metadata: dict[str, Any],
    terrain_masks: dict[str, np.ndarray],
) -> dict[str, Any]:
    vertices = extract_polygon_vertices(source_zone_metadata)
    mask = terrain_masks["footprint_mask"]
    cell_area_m2 = terrain["cellsize"] ** 2
    return {
        "source_zone_id": source_zone_metadata.get("source_zone_id"),
        "geometry_type": source_zone_metadata.get("geometry", {}).get("type", "polygon"),
        "vertex_count": len(vertices),
        "vertex_coordinates": [[x, y] for x, y in vertices],
        "polygon_area_m2_exact": polygon_area(vertices),
        "masked_cell_count_on_terrain_grid": int(mask.sum()),
        "masked_area_m2_on_terrain_grid": int(mask.sum()) * cell_area_m2,
        "bbox_lv95_m": polygon_bbox(vertices),
    }


def build_candidate_footprint_comparison(
    terrain: dict[str, Any],
    terrain_masks: dict[str, np.ndarray],
) -> dict[str, Any]:
    candidate_mask = terrain_masks["candidate_mask"]
    footprint_mask = terrain_masks["footprint_mask"]
    intersection_mask = candidate_mask & footprint_mask
    cell_area_m2 = terrain["cellsize"] ** 2
    candidate_count = int(candidate_mask.sum())
    footprint_count = int(footprint_mask.sum())
    intersection_count = int(intersection_mask.sum())
    return {
        "comparison_status": "ready",
        "comparison_mode": "candidate_mask_vs_frozen_source_zone_footprint_mask",
        "candidate_excludes_frozen_footprint": intersection_count == 0,
        "candidate_cell_count": candidate_count,
        "frozen_footprint_cell_count": footprint_count,
        "candidate_and_frozen_footprint_intersection_cell_count": intersection_count,
        "candidate_and_frozen_footprint_intersection_area_m2": intersection_count * cell_area_m2,
        "candidate_overlap_fraction_of_candidate_cells": fraction(intersection_count, candidate_count),
        "candidate_overlap_fraction_of_frozen_footprint_cells": fraction(intersection_count, footprint_count),
    }


def build_excluded_area_summary(
    terrain_masks: dict[str, np.ndarray],
    terrain: dict[str, Any],
    screening: dict[str, Any],
) -> list[dict[str, Any]]:
    cell_area_m2 = terrain["cellsize"] ** 2
    slope = terrain_masks["slope_deg"]
    low_mask = terrain_masks["low_slope_mask"]
    high_mask = terrain_masks["high_slope_mask"]
    return [
        {
            "category": "nodata_or_invalid",
            "cell_count": int(terrain_masks["nodata_mask"].sum()),
            "area_m2": int(terrain_masks["nodata_mask"].sum()) * cell_area_m2,
            "reason": "cells with nodata or non-finite terrain values",
        },
        {
            "category": "incomplete_neighborhood",
            "cell_count": int(terrain_masks["incomplete_neighborhood_mask"].sum()),
            "area_m2": int(terrain_masks["incomplete_neighborhood_mask"].sum()) * cell_area_m2,
            "reason": "border cells without a full 3x3 slope kernel",
        },
        {
            "category": "frozen_release_zone_footprint",
            "cell_count": int(terrain_masks["footprint_mask"].sum()),
            "area_m2": int(terrain_masks["footprint_mask"].sum()) * cell_area_m2,
            "reason": "cells inside the committed frozen source-zone footprint are excluded from candidate screening",
        },
        {
            "category": "slope_below_candidate_band",
            "cell_count": int(low_mask.sum()),
            "area_m2": int(low_mask.sum()) * cell_area_m2,
            "reason": f"slope below {screening['candidate_slope_min_deg']} degrees",
        },
        {
            "category": "slope_above_candidate_band",
            "cell_count": int(high_mask.sum()),
            "area_m2": int(high_mask.sum()) * cell_area_m2,
            "reason": f"slope above {screening['candidate_slope_max_deg']} degrees",
        },
        {
            "category": "candidate_band",
            "cell_count": int(terrain_masks["candidate_mask"].sum()),
            "area_m2": int(terrain_masks["candidate_mask"].sum()) * cell_area_m2,
            "reason": (
                f"slope within [{screening['candidate_slope_min_deg']}, {screening['candidate_slope_max_deg']}] degrees "
                "and outside the frozen release-zone footprint"
            ),
        },
    ]


def compute_candidate_masks(
    terrain: dict[str, Any],
    source_zone_metadata: dict[str, Any],
    screening: dict[str, Any],
) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    values = terrain["values"]
    valid_mask = terrain["valid_mask"]
    nrows, ncols = values.shape

    slope_deg = np.full_like(values, np.nan, dtype=float)
    valid_interior_mask = np.zeros_like(valid_mask, dtype=bool)
    nodata_mask = ~valid_mask
    incomplete_neighborhood_mask = np.ones_like(valid_mask, dtype=bool)
    incomplete_neighborhood_mask[1:-1, 1:-1] = False
    footprint_mask = point_in_polygon_mask(terrain, extract_polygon_vertices(source_zone_metadata))

    for row in range(1, nrows - 1):
        for col in range(1, ncols - 1):
            neighborhood = values[row - 1 : row + 2, col - 1 : col + 2]
            if not np.isfinite(neighborhood).all():
                continue
            valid_interior_mask[row, col] = True
            dzdx = (
                (neighborhood[0, 2] + 2.0 * neighborhood[1, 2] + neighborhood[2, 2])
                - (neighborhood[0, 0] + 2.0 * neighborhood[1, 0] + neighborhood[2, 0])
            ) / (8.0 * terrain["cellsize"])
            dzdy = (
                (neighborhood[2, 0] + 2.0 * neighborhood[2, 1] + neighborhood[2, 2])
                - (neighborhood[0, 0] + 2.0 * neighborhood[0, 1] + neighborhood[0, 2])
            ) / (8.0 * terrain["cellsize"])
            slope_deg[row, col] = math.degrees(math.atan(math.hypot(dzdx, dzdy)))

    screenable_mask = valid_interior_mask & ~footprint_mask
    candidate_mask = screenable_mask & (slope_deg >= MIN_CANDIDATE_SLOPE_DEG) & (slope_deg <= MAX_CANDIDATE_SLOPE_DEG)
    low_slope_mask = screenable_mask & np.isfinite(slope_deg) & (slope_deg < MIN_CANDIDATE_SLOPE_DEG)
    high_slope_mask = screenable_mask & np.isfinite(slope_deg) & (slope_deg > MAX_CANDIDATE_SLOPE_DEG)

    terrain_masks = {
        "slope_deg": slope_deg,
        "valid_interior_mask": valid_interior_mask,
        "nodata_mask": nodata_mask,
        "incomplete_neighborhood_mask": incomplete_neighborhood_mask,
        "footprint_mask": footprint_mask,
        "screenable_mask": screenable_mask,
        "candidate_mask": candidate_mask,
        "low_slope_mask": low_slope_mask,
        "high_slope_mask": high_slope_mask,
    }
    return candidate_mask, terrain_masks


def emit_candidate_products(
    *,
    report: dict[str, Any],
    terrain: dict[str, Any],
    terrain_masks: dict[str, np.ndarray],
    source_zone_metadata: dict[str, Any],
    repo_root: Path,
    output_root: Path,
    output_mode: str,
) -> dict[str, Any]:
    output_root = Path(output_root)
    output_root.mkdir(parents=True, exist_ok=True)
    source_zone_id = source_zone_metadata.get("source_zone_id") or report["candidate_site_id"]
    components = connected_candidate_components(terrain_masks["candidate_mask"])
    width = max(3, len(str(max(0, len(components) - 1))))
    component_features = [
        build_candidate_component_feature(
            terrain=terrain,
            terrain_masks=terrain_masks,
            source_zone_metadata=source_zone_metadata,
            component=cells,
            index=index,
            width=width,
            source_zone_id=str(source_zone_id),
            candidate_site_id=report["candidate_site_id"],
            source_inputs=[
                report["terrain_inputs"]["terrain_crop_path"],
                report["terrain_inputs"]["terrain_metadata_path"],
                report["source_zone_inputs"]["source_zone_metadata_path"],
            ],
        )
        for index, cells in enumerate(components)
    ]

    manifest_path = output_root / f"{report['candidate_site_id']}_release_zone_candidates_manifest.json"
    product_bundle: dict[str, Any] = {
        "schema_version": PRODUCT_SCHEMA_VERSION,
        "output_status": "emitted",
        "output_mode": output_mode,
        "candidate_site_id": report["candidate_site_id"],
        "candidate_site_name": report["candidate_site_name"],
        "candidate_release_zone_set_status": "emitted",
        "source_zone_id": source_zone_id,
        "output_root": str(output_root),
        "outputs": {},
        "candidate_footprint_comparison": report["candidate_footprint_comparison"],
        "frozen_source_zone_footprint": report["frozen_source_zone_footprint"],
        "candidate_summary": report["candidate_summary"],
        "provenance": report["provenance"],
    }

    if output_mode in {"polygon", "both"}:
        polygon_path = output_root / f"{report['candidate_site_id']}_release_zone_candidates.geojson"
        polygon_payload = {
            "schema_version": PRODUCT_SCHEMA_VERSION,
            "type": "FeatureCollection",
            "candidate_generation_label": "heuristic_candidate_generation_only",
            "candidate_site_id": report["candidate_site_id"],
            "candidate_site_name": report["candidate_site_name"],
            "source_zone_id": source_zone_id,
            "features": component_features,
        }
        polygon_path.write_text(json.dumps(polygon_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        product_bundle["outputs"]["polygon"] = display_path(polygon_path, repo_root)
        product_bundle["polygon_feature_count"] = len(component_features)
        product_bundle["polygon_path"] = display_path(polygon_path, repo_root)

    if output_mode in {"mask", "both"}:
        mask_path = output_root / f"{report['candidate_site_id']}_release_zone_candidates_mask.asc"
        write_candidate_mask_ascii_grid(mask_path, terrain, terrain_masks["candidate_mask"])
        product_bundle["outputs"]["mask"] = display_path(mask_path, repo_root)
        product_bundle["mask_path"] = display_path(mask_path, repo_root)

    product_bundle["manifest_path"] = display_path(manifest_path, repo_root)
    product_bundle["candidate_release_zone_ids"] = [feature["properties"]["candidate_release_zone_id"] for feature in component_features]
    product_bundle["component_count"] = len(component_features)
    product_bundle["candidate_cell_count"] = int(terrain_masks["candidate_mask"].sum())
    product_bundle["candidate_excludes_frozen_footprint"] = report["candidate_footprint_comparison"]["candidate_excludes_frozen_footprint"]
    product_bundle["source_inputs"] = [
        report["terrain_inputs"]["terrain_crop_path"],
        report["terrain_inputs"]["terrain_metadata_path"],
        report["source_zone_inputs"]["source_zone_metadata_path"],
    ]
    manifest_path.write_text(json.dumps(product_bundle, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    product_bundle["outputs"]["manifest"] = display_path(manifest_path, repo_root)
    return product_bundle


def connected_candidate_components(candidate_mask: np.ndarray) -> list[list[tuple[int, int]]]:
    nrows, ncols = candidate_mask.shape
    visited = np.zeros_like(candidate_mask, dtype=bool)
    components: list[list[tuple[int, int]]] = []
    for row in range(nrows):
        for col in range(ncols):
            if not candidate_mask[row, col] or visited[row, col]:
                continue
            component = flood_fill_component(candidate_mask, visited, row, col)
            component.sort()
            components.append(component)
    components.sort(key=component_sort_key)
    return components


def flood_fill_component(
    candidate_mask: np.ndarray,
    visited: np.ndarray,
    start_row: int,
    start_col: int,
) -> list[tuple[int, int]]:
    stack = [(start_row, start_col)]
    visited[start_row, start_col] = True
    cells: list[tuple[int, int]] = []
    nrows, ncols = candidate_mask.shape
    while stack:
        row, col = stack.pop()
        cells.append((row, col))
        for next_row, next_col in (
            (row - 1, col),
            (row, col - 1),
            (row, col + 1),
            (row + 1, col),
        ):
            if next_row < 0 or next_row >= nrows or next_col < 0 or next_col >= ncols:
                continue
            if visited[next_row, next_col] or not candidate_mask[next_row, next_col]:
                continue
            visited[next_row, next_col] = True
            stack.append((next_row, next_col))
    return cells


def component_sort_key(component: list[tuple[int, int]]) -> tuple[int, int, int, int, int]:
    rows = [row for row, _ in component]
    cols = [col for _, col in component]
    return (min(rows), min(cols), max(rows), max(cols), len(component))


def build_candidate_component_feature(
    *,
    terrain: dict[str, Any],
    terrain_masks: dict[str, np.ndarray],
    source_zone_metadata: dict[str, Any],
    component: list[tuple[int, int]],
    index: int,
    width: int,
    source_zone_id: str,
    candidate_site_id: str,
    source_inputs: list[str],
) -> dict[str, Any]:
    component_mask = np.zeros_like(terrain_masks["candidate_mask"], dtype=bool)
    for row, col in component:
        component_mask[row, col] = True
    slope_deg = terrain_masks["slope_deg"][component_mask]
    cell_area_m2 = terrain["cellsize"] ** 2
    properties = {
        "candidate_release_zone_id": report_candidate_id(source_zone_id, index, width),
        "candidate_generation_label": "heuristic_candidate_generation_only",
        "candidate_site_id": candidate_site_id,
        "source_zone_id": source_zone_id,
        "source_inputs": source_inputs,
        "provenance_ref": "terrain_and_source_zone_inputs",
        "component_index": index,
        "component_cell_count": len(component),
        "component_area_m2": len(component) * cell_area_m2,
        "component_slope_min_deg": float(np.min(slope_deg)) if len(slope_deg) else None,
        "component_slope_max_deg": float(np.max(slope_deg)) if len(slope_deg) else None,
        "component_slope_mean_deg": float(np.mean(slope_deg)) if len(slope_deg) else None,
        "component_slope_median_deg": float(np.median(slope_deg)) if len(slope_deg) else None,
        "comparison_to_frozen_footprint_cell_count": int((component_mask & terrain_masks["footprint_mask"]).sum()),
        "comparison_to_frozen_footprint_excludes_source_zone": bool(not (component_mask & terrain_masks["footprint_mask"]).any()),
    }
    geometry = component_multipolygon_geometry(component, terrain)
    bbox = component_bbox(component, terrain)
    properties["component_bbox_lv95_m"] = bbox
    properties["source_zone_footprint_area_m2_exact"] = polygon_area(extract_polygon_vertices(source_zone_metadata))
    return {
        "type": "Feature",
        "id": properties["candidate_release_zone_id"],
        "geometry": geometry,
        "properties": properties,
    }


def report_candidate_id(source_zone_id: str, index: int, width: int) -> str:
    return f"{source_zone_id}_candidate_{index:0{width}d}"


def component_multipolygon_geometry(component: list[tuple[int, int]], terrain: dict[str, Any]) -> dict[str, Any]:
    coordinates = []
    for row, col in component:
        coordinates.append([cell_polygon_coordinates(row, col, terrain)])
    return {"type": "MultiPolygon", "coordinates": coordinates}


def cell_polygon_coordinates(row: int, col: int, terrain: dict[str, Any]) -> list[list[float]]:
    x0 = terrain["xllcorner"] + col * terrain["cellsize"]
    x1 = x0 + terrain["cellsize"]
    y0 = terrain["yllcorner"] + (terrain["nrows"] - row - 1) * terrain["cellsize"]
    y1 = y0 + terrain["cellsize"]
    return [
        [x0, y0],
        [x1, y0],
        [x1, y1],
        [x0, y1],
        [x0, y0],
    ]


def component_bbox(component: list[tuple[int, int]], terrain: dict[str, Any]) -> dict[str, float]:
    rows = [row for row, _ in component]
    cols = [col for _, col in component]
    xmin = terrain["xllcorner"] + min(cols) * terrain["cellsize"]
    xmax = terrain["xllcorner"] + (max(cols) + 1) * terrain["cellsize"]
    ymin = terrain["yllcorner"] + (terrain["nrows"] - max(rows) - 1) * terrain["cellsize"]
    ymax = terrain["yllcorner"] + (terrain["nrows"] - min(rows)) * terrain["cellsize"]
    return {
        "crs": "EPSG:2056",
        "xmin": xmin,
        "ymin": ymin,
        "xmax": xmax,
        "ymax": ymax,
    }


def polygon_bbox(vertices: list[tuple[float, float]]) -> dict[str, float]:
    if not vertices:
        return {"crs": "EPSG:2056", "xmin": 0.0, "ymin": 0.0, "xmax": 0.0, "ymax": 0.0}
    xs = [vertex[0] for vertex in vertices]
    ys = [vertex[1] for vertex in vertices]
    return {
        "crs": "EPSG:2056",
        "xmin": min(xs),
        "ymin": min(ys),
        "xmax": max(xs),
        "ymax": max(ys),
    }


def write_candidate_mask_ascii_grid(mask_path: Path, terrain: dict[str, Any], candidate_mask: np.ndarray) -> None:
    lines = [
        f"ncols {terrain['ncols']}",
        f"nrows {terrain['nrows']}",
        f"xllcorner {format_number(terrain['xllcorner'])}",
        f"yllcorner {format_number(terrain['yllcorner'])}",
        f"cellsize {format_number(terrain['cellsize'])}",
        f"NODATA_value {format_number(terrain['nodata_value'])}",
    ]
    values = np.where(candidate_mask, 1.0, terrain["nodata_value"])
    for row in values:
        lines.append(" ".join(format_number(float(value)) for value in row))
    mask_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def format_number(value: float) -> str:
    if float(value).is_integer():
        return str(int(value))
    return f"{value:g}"


def point_in_polygon_mask(terrain: dict[str, Any], vertices: list[tuple[float, float]]) -> np.ndarray:
    mask = np.zeros((terrain["nrows"], terrain["ncols"]), dtype=bool)
    if not vertices:
        return mask
    for row in range(terrain["nrows"]):
        y = terrain["yllcorner"] + (terrain["nrows"] - row - 0.5) * terrain["cellsize"]
        for col in range(terrain["ncols"]):
            x = terrain["xllcorner"] + (col + 0.5) * terrain["cellsize"]
            mask[row, col] = point_in_polygon(x, y, vertices)
    return mask


def point_in_polygon(x: float, y: float, vertices: list[tuple[float, float]]) -> bool:
    inside = False
    j = len(vertices) - 1
    for i, (xi, yi) in enumerate(vertices):
        xj, yj = vertices[j]
        intersects = ((yi > y) != (yj > y)) and (
            x < ((xj - xi) * (y - yi)) / ((yj - yi) if (yj - yi) != 0 else 1e-12) + xi
        )
        if intersects:
            inside = not inside
        j = i
    return inside


def extract_polygon_vertices(source_zone_metadata: dict[str, Any]) -> list[tuple[float, float]]:
    geometry = source_zone_metadata.get("geometry", {})
    raw_vertices = None
    if isinstance(geometry, dict):
        raw_vertices = geometry.get("vertices") or geometry.get("coordinates")
    if not isinstance(raw_vertices, list):
        return []
    vertices: list[tuple[float, float]] = []
    for entry in raw_vertices:
        if not isinstance(entry, (list, tuple)) or len(entry) < 2:
            continue
        vertices.append((float(entry[0]), float(entry[1])))
    if vertices and vertices[0] == vertices[-1]:
        vertices.pop()
    return vertices


def polygon_area(vertices: list[tuple[float, float]]) -> float:
    if len(vertices) < 3:
        return 0.0
    area = 0.0
    for idx, (x0, y0) in enumerate(vertices):
        x1, y1 = vertices[(idx + 1) % len(vertices)]
        area += x0 * y1 - x1 * y0
    return abs(area) / 2.0


def build_provenance(
    terrain_crop_path: Path,
    terrain_metadata_path: Path,
    source_zone_metadata_path: Path,
    terrain_metadata: dict[str, Any],
    source_zone_metadata: dict[str, Any],
) -> dict[str, Any]:
    return {
        "terrain_source": {
            "source_dataset": terrain_metadata.get("source_dataset"),
            "source_product": terrain_metadata.get("source_product"),
            "source_url": terrain_metadata.get("source_url"),
            "source_filename": terrain_metadata.get("source_filename"),
            "source_file_present": terrain_metadata.get("source_file_present"),
            "download_status": terrain_metadata.get("download_status"),
            "license": terrain_metadata.get("license"),
            "processed_utc": terrain_metadata.get("preprocessing", {}).get("processed_utc"),
            "raw_sha256": terrain_metadata.get("preprocessing", {}).get("raw_sha256"),
            "processed_sha256": terrain_metadata.get("preprocessing", {}).get("processed_sha256"),
            "tool": terrain_metadata.get("preprocessing", {}).get("tool"),
            "crop_extent_lv95_m": terrain_metadata.get("preprocessing", {}).get("crop_extent_lv95_m"),
            "terrain_crop_sha256": sha256_file(terrain_crop_path),
            "terrain_metadata_sha256": sha256_file(terrain_metadata_path),
        },
        "source_zone_source": {
            "source_zone_id": source_zone_metadata.get("source_zone_id"),
            "license": source_zone_metadata.get("provenance", {}).get("license"),
            "source": source_zone_metadata.get("provenance", {}).get("source"),
            "notes": source_zone_metadata.get("provenance", {}).get("notes", []),
            "source_zone_metadata_sha256": sha256_file(source_zone_metadata_path),
        },
        "heuristic_notes": [
            "cell-center inclusion against the frozen source-zone polygon is deterministic",
            "the 3x3 Horn slope kernel is fixed and does not fit outcomes",
            "candidate cells are workflow inputs only and are not validated release zones",
        ],
    }


def read_esri_ascii_grid(path: Path) -> dict[str, Any]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if len(lines) < 6:
        raise TerrainReleaseZoneCandidateMetricsError(f"ESRI ASCII grid is too short: {path}")

    header: dict[str, float] = {}
    for line in lines[:6]:
        key, value = line.split(maxsplit=1)
        header[key.lower()] = float(value)

    ncols = int(header["ncols"])
    nrows = int(header["nrows"])
    cellsize = float(header["cellsize"])
    nodata = float(header.get("nodata_value", NODATA_SENTINEL))
    data = np.loadtxt(lines[6:], dtype=float)
    if data.shape != (nrows, ncols):
        raise TerrainReleaseZoneCandidateMetricsError(
            f"terrain grid shape mismatch for {path}: expected {(nrows, ncols)}, got {data.shape}"
        )
    valid_mask = np.isfinite(data) & (data != nodata)
    data = np.where(valid_mask, data, np.nan)
    return {
        "values": data,
        "valid_mask": valid_mask,
        "ncols": ncols,
        "nrows": nrows,
        "xllcorner": float(header.get("xllcorner", 0.0)),
        "yllcorner": float(header.get("yllcorner", 0.0)),
        "cellsize": cellsize,
        "nodata_value": nodata,
    }


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - file context matters.
        raise TerrainReleaseZoneCandidateMetricsError(f"failed to read YAML {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise TerrainReleaseZoneCandidateMetricsError(f"expected YAML mapping in {path}")
    return data


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def display_path(path: Path, repo_root: Path) -> str:
    try:
        return str(path.relative_to(repo_root))
    except ValueError:
        return str(path)


def resolve_path(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else (repo_root / path).resolve()


def default_repo_path(repo_root: Path, path: Path) -> Path:
    try:
        rel = path.relative_to(ROOT)
    except ValueError:
        return path
    return (repo_root / rel).resolve()


def fraction(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return numerator / denominator


def render_text_report(report: dict[str, Any]) -> str:
    lines = [
        f"schema_version: {report['schema_version']}",
        f"candidate_metrics_status: {report['candidate_metrics_status']}",
        f"candidate_release_zone_set_status: {report['candidate_release_zone_set_status']}",
        f"candidate_release_zone_interpretation: {report['candidate_release_zone_interpretation']}",
        f"candidate_site_id: {report['candidate_site_id']}",
        f"candidate_site_name: {report['candidate_site_name']}",
        f"candidate_selection_rationale: {report['candidate_selection_rationale']}",
        "",
        "terrain_preprocessing:",
    ]
    lines.extend(render_mapping(report.get("terrain_preprocessing") or {}))
    lines.append("")
    lines.append("screening_criteria:")
    lines.extend(f"- {key}: {value}" for key, value in report["screening_criteria"].items())
    lines.append("")
    lines.append("terrain_summary:")
    lines.extend(render_mapping(report["terrain_summary"]))
    lines.append("")
    lines.append("candidate_summary:")
    lines.extend(render_mapping(report["candidate_summary"]))
    lines.append("")
    lines.append("frozen_source_zone_footprint:")
    lines.extend(render_mapping(report["frozen_source_zone_footprint"]))
    lines.append("")
    lines.append("candidate_footprint_comparison:")
    lines.extend(render_mapping(report["candidate_footprint_comparison"]))
    lines.append("")
    lines.append("excluded_area_summary:")
    for row in report["excluded_area_summary"]:
        lines.append(
            f"- {row['category']}: cell_count={row['cell_count']}, area_m2={row['area_m2']}, reason={row['reason']}"
        )
    lines.append("")
    lines.append("source_zone_inputs:")
    lines.extend(render_mapping(report["source_zone_inputs"]))
    lines.append("")
    lines.append("terrain_inputs:")
    lines.extend(render_mapping(report["terrain_inputs"]))
    lines.append("")
    lines.append("provenance:")
    lines.extend(render_mapping(report["provenance"]))
    lines.append("")
    lines.append("candidate_release_zone_products:")
    lines.extend(render_mapping(report["candidate_release_zone_products"]))
    lines.append("")
    lines.append("claim_boundaries:")
    lines.extend(render_mapping(report["claim_boundaries"]))
    lines.append("")
    lines.append(f"blocked_reason: {report['blocked_reason']}")
    return "\n".join(lines)


def render_mapping(mapping: dict[str, Any], indent: str = "") -> list[str]:
    lines: list[str] = []
    for key, value in mapping.items():
        if isinstance(value, dict):
            lines.append(f"{indent}- {key}:")
            lines.extend(render_mapping(value, indent=f"{indent}  "))
        elif isinstance(value, list):
            lines.append(f"{indent}- {key}:")
            for item in value:
                if isinstance(item, dict):
                    lines.append(f"{indent}  -")
                    lines.extend(render_mapping(item, indent=f"{indent}    "))
                else:
                    lines.append(f"{indent}  - {item}")
        else:
            lines.append(f"{indent}- {key}: {value}")
    return lines


if __name__ == "__main__":
    raise SystemExit(main())
