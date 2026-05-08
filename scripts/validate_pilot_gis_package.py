#!/usr/bin/env python3
"""Validate a diagnostic pilot GIS/QGIS package manifest.

This validator checks package metadata and optional local artifact presence for
the current `pilot_gis_package_manifest_v1` contract. It does not open QGIS,
certify COG conformance, or approve operational hazard products.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_UNSUPPORTED_LABELS = {
    "physical_probability",
    "annual_intensity_frequency",
    "return_period",
    "risk_map",
    "operational_hazard_map",
}
VISUAL_QA_STATUSES = {"pass", "no-go", "inconclusive", "not-run"}


class PackageValidationError(ValueError):
    """User-facing pilot package validation error."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument(
        "--require-real-site",
        action="store_true",
        help="require Swiss real-site CRS/datum/grid metadata: EPSG:2056, LN02, nodata, explicit grid",
    )
    parser.add_argument(
        "--require-existing-files",
        action="store_true",
        help="verify referenced local output files exist and match recorded SHA-256 and byte counts",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="summary output format",
    )
    args = parser.parse_args(argv)
    try:
        summary = validate_package(
            args.manifest,
            require_real_site=args.require_real_site,
            require_existing_files=args.require_existing_files,
        )
    except PackageValidationError as exc:
        print(f"pilot GIS package validation error: {exc}", file=sys.stderr)
        return 2
    if args.format == "json":
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(
            "pilot GIS package manifest is valid: "
            f"{args.manifest} "
            f"({summary['geotiff_count']} GeoTIFFs, "
            f"{summary['csv_parity_count']} CSV parity grids, "
            f"{summary['ascii_parity_count']} ASCII parity grids)"
        )
    return 0


def validate_package(
    manifest_path: Path,
    *,
    require_real_site: bool = False,
    require_existing_files: bool = False,
) -> dict[str, Any]:
    manifest = read_json(manifest_path)
    require(
        manifest.get("schema_version") == "pilot_gis_package_manifest_v1",
        "schema_version must be pilot_gis_package_manifest_v1",
    )
    require(
        manifest.get("operational_status") == "research_diagnostic",
        "operational_status must remain research_diagnostic",
    )

    grid = require_mapping(manifest.get("grid"), "grid")
    validate_grid(grid, require_real_site=require_real_site)
    validate_contract(require_mapping(manifest.get("raster_contract"), "raster_contract"))
    validate_claim_boundary(require_mapping(manifest.get("probability_claim_boundary"), "probability_claim_boundary"))
    validate_visual_qa(require_mapping(manifest.get("visual_qa"), "visual_qa"))
    terrain = validate_terrain(require_mapping(manifest.get("terrain"), "terrain"), require_real_site=require_real_site)

    raster_outputs = require_list(manifest.get("raster_outputs"), "raster_outputs")
    parity_outputs = require_list(manifest.get("parity_outputs"), "parity_outputs")
    manifest_outputs = require_list(manifest.get("manifest_outputs"), "manifest_outputs")
    hazard_manifest_paths = require_list(manifest.get("hazard_manifest_paths"), "hazard_manifest_paths")
    require(hazard_manifest_paths, "hazard_manifest_paths must not be empty")

    geotiffs = validate_geotiff_outputs(raster_outputs, require_existing_files=require_existing_files)
    csv_parity, ascii_parity = validate_parity_outputs(
        parity_outputs,
        geotiffs,
        require_existing_files=require_existing_files,
    )
    validate_manifest_outputs(manifest_outputs, require_existing_files=require_existing_files)

    hazard_manifest = read_json(resolve_path(str(hazard_manifest_paths[0])))
    validate_hazard_manifest_spatial_metadata(hazard_manifest, grid, terrain, require_real_site=require_real_site)
    source_context_status = validate_source_context(manifest, manifest_outputs, require_existing_files=require_existing_files)

    return {
        "schema_version": manifest["schema_version"],
        "case_id": manifest.get("case_id"),
        "grid": grid,
        "terrain_epsg": terrain.get("epsg"),
        "terrain_vertical_datum": terrain.get("vertical_datum"),
        "geotiff_count": len(geotiffs),
        "csv_parity_count": len(csv_parity),
        "ascii_parity_count": len(ascii_parity),
        "visual_qa_status": manifest["visual_qa"]["status"],
        "source_context_status": source_context_status,
        "operational_status": manifest["operational_status"],
    }


def read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - path context is user-facing.
        raise PackageValidationError(f"failed to read JSON {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise PackageValidationError(f"JSON document must be an object: {path}")
    return data


def validate_grid(grid: dict[str, Any], *, require_real_site: bool) -> None:
    for key in ("xmin_m", "ymin_m", "cell_size_m"):
        value = require_number(grid.get(key), f"grid.{key}")
        require(math.isfinite(value), f"grid.{key} must be finite")
    for key in ("ncols", "nrows"):
        require_int(grid.get(key), f"grid.{key}", minimum=1)
    require(grid["cell_size_m"] > 0.0, "grid.cell_size_m must be positive")
    if require_real_site:
        require(grid.get("source") == "explicit", "real-site packages must use an explicit DEM-derived grid")


def validate_contract(contract: dict[str, Any]) -> None:
    require(contract.get("geotiff_required") is True, "raster_contract.geotiff_required must be true")
    require(
        contract.get("csv_ascii_parity_required") is True,
        "raster_contract.csv_ascii_parity_required must be true",
    )
    require(contract.get("cloud_optimized") is False, "current diagnostic package must not claim COG status")
    require(contract.get("qgis_project_included") is False, "current diagnostic package must not claim QGIS project packaging")
    require(contract.get("geopackage_included") is False, "current diagnostic package must not claim GeoPackage packaging")


def validate_claim_boundary(boundary: dict[str, Any]) -> None:
    require(boundary.get("annualized") is False, "probability_claim_boundary.annualized must be false")
    unsupported = set(require_list(boundary.get("future_unsupported_product_labels"), "future_unsupported_product_labels"))
    missing = REQUIRED_UNSUPPORTED_LABELS - unsupported
    require(not missing, f"probability_claim_boundary omits unsupported labels: {sorted(missing)}")
    allowed = set(require_list(boundary.get("current_allowed_product_labels"), "current_allowed_product_labels"))
    require("conditional_intensity_exceedance" in allowed, "current_allowed_product_labels must include conditional_intensity_exceedance")


def validate_visual_qa(visual: dict[str, Any]) -> None:
    status = require_text(visual.get("status"), "visual_qa.status")
    require(status in VISUAL_QA_STATUSES, f"visual_qa.status must be one of {sorted(VISUAL_QA_STATUSES)}")
    require_text(visual.get("note"), "visual_qa.note")
    require(visual.get("accepted_for_operational_use") is False, "visual_qa.accepted_for_operational_use must be false")
    require(
        visual.get("acceptance_scope") == "local diagnostic GIS/QGIS review only",
        "visual_qa.acceptance_scope must remain local diagnostic GIS/QGIS review only",
    )
    require_list(visual.get("reviewed_artifacts"), "visual_qa.reviewed_artifacts")


def validate_terrain(terrain: dict[str, Any], *, require_real_site: bool) -> dict[str, Any]:
    require_text(terrain.get("metadata_path"), "terrain.metadata_path")
    require_number(terrain.get("resolution_m"), "terrain.resolution_m")
    require_number(terrain.get("nodata"), "terrain.nodata")
    require_mapping(terrain.get("extent"), "terrain.extent")
    if require_real_site:
        require(terrain.get("epsg") == 2056, "real-site terrain.epsg must be 2056")
        require(terrain.get("vertical_datum") == "LN02", "real-site terrain.vertical_datum must be LN02")
        require(terrain.get("source_dataset") == "swisstopo_swissalti3d", "real-site terrain source must be swissALTI3D")
    return terrain


def validate_geotiff_outputs(outputs: list[Any], *, require_existing_files: bool) -> dict[str, dict[str, Any]]:
    geotiffs: dict[str, dict[str, Any]] = {}
    for index, raw in enumerate(outputs):
        output = require_mapping(raw, f"raster_outputs[{index}]")
        require(output.get("format") == "geotiff", f"raster_outputs[{index}].format must be geotiff")
        layer = require_text(output.get("layer_name"), f"raster_outputs[{index}].layer_name")
        require(layer not in geotiffs, f"duplicate GeoTIFF layer_name: {layer}")
        require(output.get("cloud_optimized") is False, f"GeoTIFF {layer} must not claim COG status")
        require(output.get("annualized") is False, f"GeoTIFF {layer} must not be annualized")
        require(output.get("is_annualized") is False, f"GeoTIFF {layer} must not be annualized")
        validate_artifact(output, f"raster_outputs[{index}]", require_existing_files=require_existing_files)
        geotiffs[layer] = output
    require(geotiffs, "raster_outputs must include at least one GeoTIFF")
    return geotiffs


def validate_parity_outputs(
    outputs: list[Any],
    geotiffs: dict[str, dict[str, Any]],
    *,
    require_existing_files: bool,
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    csv_by_layer: dict[str, dict[str, Any]] = {}
    ascii_by_layer: dict[str, dict[str, Any]] = {}
    geotiff_stems = {Path(str(output["path"])).stem: layer for layer, output in geotiffs.items()}
    for index, raw in enumerate(outputs):
        output = require_mapping(raw, f"parity_outputs[{index}]")
        fmt = require_text(output.get("format"), f"parity_outputs[{index}].format")
        require(fmt in {"csv_grid", "esri_ascii_grid"}, f"unsupported parity output format: {fmt}")
        validate_artifact(output, f"parity_outputs[{index}]", require_existing_files=require_existing_files)
        stem = Path(str(output["path"])).stem
        layer = geotiff_stems.get(stem)
        require(layer is not None, f"parity output has no matching GeoTIFF stem: {output['path']}")
        if fmt == "csv_grid":
            csv_by_layer[layer] = output
        else:
            ascii_by_layer[layer] = output
    missing_csv = sorted(set(geotiffs) - set(csv_by_layer))
    missing_ascii = sorted(set(geotiffs) - set(ascii_by_layer))
    require(not missing_csv, f"missing CSV parity outputs for GeoTIFF layers: {missing_csv}")
    require(not missing_ascii, f"missing ESRI ASCII parity outputs for GeoTIFF layers: {missing_ascii}")
    return csv_by_layer, ascii_by_layer


def validate_manifest_outputs(outputs: list[Any], *, require_existing_files: bool) -> None:
    kinds = set()
    for index, raw in enumerate(outputs):
        output = require_mapping(raw, f"manifest_outputs[{index}]")
        kinds.add(require_text(output.get("kind"), f"manifest_outputs[{index}].kind"))
        validate_artifact(output, f"manifest_outputs[{index}]", require_existing_files=require_existing_files)
    require("hazard_metadata" in kinds, "manifest_outputs must include hazard_metadata")
    require("map_package_manifest" in kinds, "manifest_outputs must include map_package_manifest")


def validate_hazard_manifest_spatial_metadata(
    hazard_manifest: dict[str, Any],
    grid: dict[str, Any],
    terrain: dict[str, Any],
    *,
    require_real_site: bool,
) -> None:
    outputs = require_list(hazard_manifest.get("outputs"), "hazard_manifest.outputs")
    geotiff_entries = [
        require_mapping(output, "hazard_manifest.outputs[]")
        for output in outputs
        if isinstance(output, dict) and output.get("format") == "geotiff"
    ]
    require(geotiff_entries, "hazard manifest must include GeoTIFF outputs")
    for entry in geotiff_entries:
        layer = require_text(entry.get("layer_name"), "hazard geotiff layer_name")
        raster = require_mapping(entry.get("raster"), f"hazard geotiff {layer}.raster")
        require(raster.get("ncols") == grid["ncols"], f"{layer} ncols must match package grid")
        require(raster.get("nrows") == grid["nrows"], f"{layer} nrows must match package grid")
        require(raster.get("cell_size_m") == grid["cell_size_m"], f"{layer} cell size must match package grid")
        require(raster.get("nodata") == terrain["nodata"], f"{layer} nodata must match terrain metadata")
        require(raster.get("cloud_optimized") is False, f"{layer} must not claim COG status")
        require(raster.get("cog") is False, f"{layer} must not claim COG status")
        affine = require_list(raster.get("affine_transform"), f"{layer}.affine_transform")
        expected_affine = [
            grid["cell_size_m"],
            0.0,
            grid["xmin_m"],
            0.0,
            -grid["cell_size_m"],
            grid["ymin_m"] + grid["nrows"] * grid["cell_size_m"],
        ]
        require(len(affine) == len(expected_affine), f"{layer}.affine_transform must have six values")
        for actual, expected in zip(affine, expected_affine, strict=True):
            require_number(actual, f"{layer}.affine_transform[]")
            require(abs(float(actual) - float(expected)) <= 1.0e-9, f"{layer}.affine_transform must match package grid")
        if require_real_site:
            require(raster.get("epsg") == 2056, f"{layer} EPSG must be 2056")
            require(raster.get("vertical_datum") == "LN02", f"{layer} vertical datum must be LN02")


def validate_source_context(
    manifest: dict[str, Any],
    manifest_outputs: list[Any],
    *,
    require_existing_files: bool,
) -> str:
    context = require_list(manifest.get("source_zone_context"), "source_zone_context")
    if context:
        for index, raw in enumerate(context):
            validate_artifact(require_mapping(raw, f"source_zone_context[{index}]"), f"source_zone_context[{index}]", require_existing_files=require_existing_files)
        return "source_zone_context_artifacts"

    map_manifest_paths = [
        require_mapping(output, "manifest_outputs[]").get("path")
        for output in manifest_outputs
        if isinstance(output, dict) and output.get("kind") == "map_package_manifest"
    ]
    require(map_manifest_paths, "missing map_package_manifest for source-zone context fallback")
    map_manifest = read_json(resolve_path(str(map_manifest_paths[0])))
    require_text(map_manifest.get("source_zone_id"), "map_package_manifest.source_zone_id")
    require_text(map_manifest.get("source_zone_metadata_path"), "map_package_manifest.source_zone_metadata_path")
    require(
        map_manifest.get("probability_mode") == "sampling_weighted_conditional",
        "map_package_manifest.probability_mode must be sampling_weighted_conditional",
    )
    require(map_manifest.get("operational_status") == "research_diagnostic", "map_package_manifest must remain research_diagnostic")
    return "map_package_source_zone_metadata"


def validate_artifact(entry: dict[str, Any], field: str, *, require_existing_files: bool) -> None:
    path_text = require_text(entry.get("path"), f"{field}.path")
    sha = require_text(entry.get("sha256"), f"{field}.sha256")
    require(len(sha) == 64 and all(ch in "0123456789abcdef" for ch in sha), f"{field}.sha256 must be lowercase SHA-256 hex")
    total_bytes = require_int(entry.get("total_bytes"), f"{field}.total_bytes", minimum=1)
    if not require_existing_files:
        return
    path = resolve_path(path_text)
    require(path.exists(), f"{field}.path does not exist: {path}")
    data = path.read_bytes()
    require(len(data) == total_bytes, f"{field}.total_bytes does not match file size: {path}")
    require(hashlib.sha256(data).hexdigest() == sha, f"{field}.sha256 does not match file content: {path}")


def resolve_path(path_text: str) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    return ROOT / path


def require(condition: bool, message: str) -> None:
    if not condition:
        raise PackageValidationError(message)


def require_mapping(value: Any, field: str) -> dict[str, Any]:
    require(isinstance(value, dict), f"{field} must be an object")
    return value


def require_list(value: Any, field: str) -> list[Any]:
    require(isinstance(value, list), f"{field} must be a list")
    return value


def require_text(value: Any, field: str) -> str:
    require(isinstance(value, str) and value.strip(), f"{field} must be a nonempty string")
    return value


def require_number(value: Any, field: str) -> float:
    require(isinstance(value, (int, float)) and not isinstance(value, bool), f"{field} must be a number")
    return float(value)


def require_int(value: Any, field: str, *, minimum: int) -> int:
    require(isinstance(value, int) and not isinstance(value, bool), f"{field} must be an integer")
    require(value >= minimum, f"{field} must be >= {minimum}")
    return value


if __name__ == "__main__":
    raise SystemExit(main())
