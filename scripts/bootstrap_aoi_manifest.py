#!/usr/bin/env python3
"""Bootstrap a deterministic AOI manifest package from bounds or GeoJSON.

The bootstrap helper is metadata-only. It turns a user-supplied LV95 bounds
rectangle or polygon GeoJSON file into a compact AOI manifest package under a
caller-provided ignored root. The package is designed to be consumed by the
existing second-site preflight and planning helpers without manual fixture
editing.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except ImportError as exc:  # pragma: no cover - environment setup.
    raise SystemExit("PyYAML is required. Run this script with `PYENV_VERSION=system uv run python ...`; CI may use `requirements-tools.txt`") from exc


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = 1
MANIFEST_TYPE = "aoi_manifest_bootstrap_v1"
SUPPORTED_CRS = "EPSG:2056"
SUPPORTED_VERTICAL_DATUM = "LN02"
DEFAULT_SITE_NAME = "Bootstrap AOI"
DEFAULT_PRODUCT_POLICY_STATUS = "template_not_run"
DEFAULT_PRODUCT_POLICY_OPERATIONAL_STATUS = "research_diagnostic"
DEFAULT_SOURCE_SCENARIO_POLICY_SCHEMA = "source_zone_block_scenario_policy_v1"


def _load_preflight_module():
    path = ROOT / "scripts" / "check_second_site_public_geodata_preflight.py"
    spec = importlib.util.spec_from_file_location("bootstrap_aoi_manifest_preflight", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load preflight helper from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


PREFLIGHT = _load_preflight_module()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--site-id", type=str, required=True)
    parser.add_argument("--site-name", type=str, default=None)
    parser.add_argument("--crs", type=str, default=SUPPORTED_CRS)
    parser.add_argument("--vertical-datum", type=str, default=SUPPORTED_VERTICAL_DATUM)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--bounds", nargs=4, type=float, metavar=("XMIN", "YMIN", "XMAX", "YMAX"))
    group.add_argument("--aoi-geojson", type=Path)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    args = parser.parse_args(argv)

    try:
        report = build_report(
            output_root=args.output_root,
            site_id=args.site_id,
            site_name=args.site_name,
            crs=args.crs,
            vertical_datum=args.vertical_datum,
            bounds=args.bounds,
            aoi_geojson=args.aoi_geojson,
        )
    except BootstrapError as exc:
        print(f"bootstrap error: {exc}", file=sys.stderr)
        return 2

    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    output = json.dumps(report, indent=2, sort_keys=True) if args.format == "json" else render_text_report(report)
    print(output)
    return 0 if report["bootstrap_status"] == "ready" else 2


def build_report(
    *,
    output_root: Path,
    site_id: str,
    site_name: str | None,
    crs: str,
    vertical_datum: str,
    bounds: list[float] | None = None,
    aoi_geojson: Path | None = None,
) -> dict[str, Any]:
    output_root = resolve_output_root(output_root)
    validate_output_root(output_root)
    validate_site_id(site_id)
    validate_crs(crs)
    validate_vertical_datum(vertical_datum)

    if bounds is not None:
        geometry = geometry_from_bounds(bounds)
        source_kind = "bounds"
        source_reference = "user-supplied bounds"
    elif aoi_geojson is not None:
        geometry = geometry_from_geojson(aoi_geojson)
        source_kind = "geojson"
        source_reference = str(aoi_geojson)
    else:  # pragma: no cover - argparse prevents this.
        raise BootstrapError("either bounds or a GeoJSON polygon is required")

    site_name = (site_name or default_site_name(site_id)).strip()
    extent = geometry_extent(geometry["coordinates"])
    geometry_hash = hash_payload(
        {
            "candidate_site_id": site_id,
            "candidate_site_name": site_name,
            "crs": crs,
            "vertical_datum": vertical_datum,
            "geometry": geometry,
            "site_extent": extent,
        }
    )
    manifest_id = f"aoi_bootstrap_{geometry_hash[:16]}"
    site_root = output_root
    input_root = site_root / "input"
    context_root = site_root / "context"
    validation_root = site_root / "validation" / "private" / site_id
    hazard_root = site_root / "hazard" / "results" / site_id
    policy_root = site_root / "validation" / "policies"
    raw_root = site_root / "data" / "raw" / "swisstopo" / site_id
    processed_root = site_root / "data" / "processed" / "swisstopo" / site_id

    paths = {
        "site_config": site_root / "aoi_manifest.yaml",
        "aoi_tile_catalog": input_root / "aoi_tile_catalog.yaml",
        "acquisition_manifest": input_root / "public_geodata_acquisition.yaml",
        "source_scenario_policy": policy_root / f"{site_id}_source_scenario_policy_v1.yaml",
    }

    bootstrap_package = {
        "schema_version": SCHEMA_VERSION,
        "manifest_type": MANIFEST_TYPE,
        "manifest_id": manifest_id,
        "candidate_site_id": site_id,
        "candidate_site_name": site_name,
        "bootstrap_status": "ready",
        "path_layout": "site_root_relative",
        "selection_rationale": "Bootstrap AOI manifest from user-supplied bounds or GeoJSON.",
        "input_source": {
            "source_kind": source_kind,
            "source_reference": source_reference,
            "crs": crs,
            "vertical_datum": vertical_datum,
        },
        "site_extent": {
            "crs": crs,
            "xmin": extent["xmin"],
            "ymin": extent["ymin"],
            "xmax": extent["xmax"],
            "ymax": extent["ymax"],
        },
        "aoi_geometry": {
            "geometry_type": "polygon",
            "coordinates": geometry["coordinates"],
            "geometry_hash": geometry_hash,
        },
        "local_layout": {
            "raw_root": "data/raw/swisstopo/" + site_id,
            "processed_root": "data/processed/swisstopo/" + site_id,
            "private_validation_root": "validation/private/" + site_id,
            "hazard_results_root": "hazard/results/" + site_id,
            "raw_files_committed": False,
            "processed_large_files_committed": False,
        },
        "expected_processed_input_root": "input",
        "expected_processed_context_root": "context",
        "expected_terrain_crop_path": "input/terrain.asc",
        "expected_aoi_tile_catalog_path": "input/aoi_tile_catalog.yaml",
        "expected_terrain_metadata_path": "input/terrain_metadata.yaml",
        "expected_source_zone_metadata_path": "input/source_zone_metadata.yaml",
        "expected_scenario_table_path": "input/scenario_table.csv",
        "expected_source_scenario_policy_path": "validation/policies/" + f"{site_id}_source_scenario_policy_v1.yaml",
        "expected_validation_private_root": "validation/private/" + site_id,
        "expected_hazard_results_root": "hazard/results/" + site_id,
        "acquisition_manifest_path": "input/public_geodata_acquisition.yaml",
        "source_zone_scenario_contract": source_zone_scenario_contract(site_id),
        "product_policy": product_policy(),
        "claim_boundary": product_policy()["claim_boundary"],
        "bootstrap_artifacts": {
            "site_config_path": "aoi_manifest.yaml",
            "aoi_tile_catalog_path": "input/aoi_tile_catalog.yaml",
            "acquisition_manifest_path": "input/public_geodata_acquisition.yaml",
            "source_scenario_policy_path": "validation/policies/" + f"{site_id}_source_scenario_policy_v1.yaml",
        },
    }

    ensure_bootstrap_layout(site_root, paths)
    write_yaml(paths["site_config"], bootstrap_package)
    write_aoi_tile_catalog(paths["aoi_tile_catalog"], site_id=site_id, site_name=site_name, extent=extent)
    write_acquisition_manifest(paths["acquisition_manifest"], site_id=site_id, site_name=site_name, extent=extent)
    write_source_scenario_policy(paths["source_scenario_policy"], site_id=site_id, site_name=site_name, extent=extent, geometry_hash=geometry_hash)

    report = {
        "schema_version": SCHEMA_VERSION,
        "manifest_type": MANIFEST_TYPE,
        "manifest_id": manifest_id,
        "bootstrap_status": "ready",
        "candidate_site_id": site_id,
        "candidate_site_name": site_name,
        "site_extent": bootstrap_package["site_extent"],
        "output_root": str(site_root),
        "site_config_path": str(paths["site_config"]),
        "aoi_tile_catalog_path": str(paths["aoi_tile_catalog"]),
        "acquisition_manifest_path": str(paths["acquisition_manifest"]),
        "source_scenario_policy_path": str(paths["source_scenario_policy"]),
        "local_layout": bootstrap_package["local_layout"],
        "product_policy": bootstrap_package["product_policy"],
        "claim_boundary": bootstrap_package["claim_boundary"],
        "input_source": bootstrap_package["input_source"],
        "aoi_geometry": bootstrap_package["aoi_geometry"],
        "validation_notes": [
            "CRS validated as EPSG:2056",
            "vertical datum validated as LN02",
            "output-root layout validated under the caller-provided ignored root",
            "generated files remain metadata-only and contain no swisstopo downloads",
        ],
        "downstream_helpers": {
            "second_site_preflight": str(paths["site_config"]),
            "aoi_acquisition_planner": str(paths["site_config"]),
        },
    }
    return report


def ensure_bootstrap_layout(site_root: Path, paths: dict[str, Path]) -> None:
    for path in (
        site_root,
        paths["site_config"].parent,
        paths["aoi_tile_catalog"].parent,
        paths["acquisition_manifest"].parent,
        paths["source_scenario_policy"].parent,
        site_root / "input",
        site_root / "context",
        site_root / "validation" / "private",
        site_root / "validation" / "policies",
        site_root / "hazard" / "results",
        site_root / "data" / "processed" / "swisstopo",
        site_root / "data" / "raw" / "swisstopo",
    ):
        path.mkdir(parents=True, exist_ok=True)


def write_aoi_tile_catalog(path: Path, *, site_id: str, site_name: str, extent: dict[str, float]) -> None:
    tile_ids = tile_catalog_ids_for_extent(extent)
    records = []
    for tile_id in tile_ids:
        records.append(
            {
                "tile_id": tile_id,
                "product_id": "swissalti3d_2m",
                "source_product": "swissALTI3D 2 m",
                "product_version": "2019",
                "product_date": "2019",
                "crs": SUPPORTED_CRS,
                "resolution_m": 2.0,
                "expected_staging_root": f"data/raw/swisstopo/{site_id}",
                "expected_staged_path": f"data/raw/swisstopo/{site_id}/swissalti3d_2019_{tile_id}_2_2056_5728.tif",
                "source_filename": f"swissalti3d_2019_{tile_id}_2_2056_5728.tif",
                "source_url": (
                    "https://data.geo.admin.ch/ch.swisstopo.swissalti3d/"
                    f"swissalti3d_2019_{tile_id}/swissalti3d_2019_{tile_id}_2_2056_5728.tif"
                ),
                "license": "swisstopo open data terms; verify current terms before download or redistribution",
                "site_name": site_name,
            }
        )

    catalog = {
        "schema_version": 1,
        "catalog_type": "aoi_tile_catalog_v1",
        "catalog_id": f"{site_id}_aoi_tile_catalog_v1",
        "candidate_site_id": site_id,
        "candidate_site_name": site_name,
        "catalog_product_id": "swissalti3d_2m",
        "coordinate_reference_system": {
            "epsg": 2056,
            "horizontal_name": "CH1903+ / LV95",
            "vertical_datum": "LN02",
            "coordinate_unit": "m",
            "height_unit": "m",
        },
        "terrain_tiles": records,
    }
    write_yaml(path, catalog)


def write_acquisition_manifest(path: Path, *, site_id: str, site_name: str, extent: dict[str, float]) -> None:
    processed_input_root = "input"
    processed_context_root = "context"
    acquisition = {
        "schema_version": 1,
        "manifest_type": "second_site_public_geodata_acquisition_v1",
        "candidate_site_id": site_id,
        "candidate_site_name": site_name,
        "selection_rationale": "Bootstrap AOI manifest from caller-supplied bounds or GeoJSON.",
        "crs": SUPPORTED_CRS,
        "vertical_datum": SUPPORTED_VERTICAL_DATUM,
        "site_extent": extent,
        "expected_processed_input_root": processed_input_root,
        "expected_processed_context_root": processed_context_root,
        "expected_validation_private_root": f"validation/private/{site_id}",
        "expected_hazard_results_root": f"hazard/results/{site_id}",
        "expected_products": [
            {
                "category": "terrain_crop",
                "product": "swissALTI3D",
                "status": "missing",
                "required": True,
                "expected_staged_path": f"{processed_input_root}/terrain.asc",
                "source_reference": "docs/swisstopo_data_strategy.md",
                "notes": "Terrain crop and metadata remain intentionally unstaged by the bootstrap helper.",
            },
            {
                "category": "terrain_metadata",
                "product": "swissALTI3D terrain metadata",
                "status": "missing",
                "required": True,
                "expected_staged_path": f"{processed_input_root}/terrain_metadata.yaml",
                "source_reference": "docs/public_real_site_geodata_preparation.md",
                "notes": "Terrain metadata is reserved for the later preprocessing helper.",
            },
            {
                "category": "aoi_tile_catalog",
                "product": "AOI tile catalog for deterministic swisstopo discovery",
                "status": "ready",
                "required": True,
                "expected_staged_path": f"{processed_input_root}/aoi_tile_catalog.yaml",
                "source_reference": "scripts/bootstrap_aoi_manifest.py",
                "notes": "Bootstrap helper writes the tile catalog deterministically from the AOI extent.",
            },
            {
                "category": "source_scenario_policy",
                "product": "source-scenario policy record",
                "status": "ready",
                "required": True,
                "expected_staged_path": f"validation/policies/{site_id}_source_scenario_policy_v1.yaml",
                "source_reference": "scripts/bootstrap_aoi_manifest.py",
                "notes": "Bootstrap helper writes a template source-scenario policy contract.",
            },
            {
                "category": "swissimage_context",
                "product": "SWISSIMAGE",
                "status": "missing",
                "required": True,
                "expected_staged_path": f"{processed_context_root}/swissimage",
                "source_reference": "docs/swisstopo_data_strategy.md",
                "notes": "Public context remains deferred until a later staging step.",
            },
            {
                "category": "swisstlm3d_context",
                "product": "swissTLM3D",
                "status": "missing",
                "required": True,
                "expected_staged_path": f"{processed_context_root}/swisstlm3d",
                "source_reference": "docs/swisstopo_data_strategy.md",
                "notes": "Public context remains deferred until a later staging step.",
            },
            {
                "category": "swisstlm3d_metadata",
                "product": "swissTLM3D metadata",
                "status": "missing",
                "required": True,
                "expected_staged_path": f"{processed_context_root}/swisstlm3d/metadata.json",
                "source_reference": "docs/public_real_site_geodata_preparation.md",
                "notes": "Metadata sidecar is intentionally not synthesized by the bootstrap helper.",
            },
            {
                "category": "swisssurface3d_context",
                "product": "swissSURFACE3D",
                "status": "missing",
                "required": True,
                "expected_staged_path": f"{processed_context_root}/swisssurface3d",
                "source_reference": "docs/swisstopo_data_strategy.md",
                "notes": "Deferred until a later public-context staging step.",
            },
            {
                "category": "swisssurface3d_raster_context",
                "product": "swissSURFACE3D Raster",
                "status": "missing",
                "required": True,
                "expected_staged_path": f"{processed_context_root}/swisssurface3d_raster",
                "source_reference": "docs/swisstopo_data_strategy.md",
                "notes": "Deferred until a later public-context staging step.",
            },
            {
                "category": "swissbuildings3d_context",
                "product": "swissBUILDINGS3D",
                "status": "missing",
                "required": True,
                "expected_staged_path": f"{processed_context_root}/swissbuildings3d",
                "source_reference": "docs/swisstopo_data_strategy.md",
                "notes": "Deferred until a later public-context staging step.",
            },
        ],
        "expected_ignored_output_roots": [
            f"validation/private/{site_id}",
            f"hazard/results/{site_id}",
        ],
        "command_templates": [
            {
                "id": "preflight_review",
                "command": (
                    "PYENV_VERSION=system uv run python scripts/check_second_site_public_geodata_preflight.py "
                    f"--site-config {repo_relative(Path('aoi_manifest.yaml'))} --format json"
                ),
                "expected_outputs": ["JSON portability preflight"],
            },
            {
                "id": "aoi_planner_review",
                "command": (
                    "PYENV_VERSION=system uv run python scripts/plan_swisstopo_aoi_acquisition.py "
                    f"--site-config {repo_relative(Path('aoi_manifest.yaml'))} --format json"
                ),
                "expected_outputs": ["JSON AOI acquisition plan"],
            },
        ],
    }
    write_yaml(path, acquisition)


def write_source_scenario_policy(path: Path, *, site_id: str, site_name: str, extent: dict[str, float], geometry_hash: str) -> None:
    center_x = round((extent["xmin"] + extent["xmax"]) / 2.0, 3)
    center_y = round((extent["ymin"] + extent["ymax"]) / 2.0, 3)
    policy = {
        "schema_version": DEFAULT_SOURCE_SCENARIO_POLICY_SCHEMA,
        "policy_id": f"{site_id}_source_scenario_policy_v1",
        "pilot_id": site_id,
        "policy_status": DEFAULT_PRODUCT_POLICY_STATUS,
        "operational_status": DEFAULT_PRODUCT_POLICY_OPERATIONAL_STATUS,
        "source_zone_policy": {
            "evidence_level": "level0_synthetic_fixture",
            "allowed_geometry_type": "polygon",
            "coordinate_reference_system": {
                "epsg": 2056,
                "vertical_datum": SUPPORTED_VERTICAL_DATUM,
            },
            "derivation_inputs": {
                "required": ["swisstopo_swissalti3d"],
            },
            "derivation_criteria": {
                "status": "not_defined",
            },
            "release_sampling": {
                "mode": "deterministic_grid",
                "seed_policy": "bootstrap_aoi_manifest_geometry_hash",
                "seed": int(geometry_hash[:8], 16),
                "release_cell_id_prefix": f"{site_id}_release_cell_",
                "requested_release_cell_count": 1,
                "release_cells": [
                    {
                        "release_cell_id": f"{site_id}_release_cell_001",
                        "center_lv95_m": [center_x, center_y],
                        "sampling_weight": 1.0,
                    }
                ],
            },
        },
        "block_scenario_policy": {
            "active_shape_physics_supported": False,
            "sampling_weight_semantics": "conditional_sampling_only",
            "scenarios": [],
        },
        "claim_boundary": product_policy()["claim_boundary"],
        "provenance": {
            "intended_use": "bootstrap_aoi_manifest_template",
            "site_name": site_name,
            "geometry_hash": geometry_hash,
            "notes": [
                "Template policy for AOI bootstrap only.",
                "No annual-frequency, physical-probability, risk, or operational claims are authorized.",
            ],
        },
    }
    write_yaml(path, policy)


def product_policy() -> dict[str, Any]:
    return {
        "policy_id": "aoi_manifest_product_policy_v1",
        "policy_status": DEFAULT_PRODUCT_POLICY_STATUS,
        "operational_status": DEFAULT_PRODUCT_POLICY_OPERATIONAL_STATUS,
        "current_allowed_products": [
            "unweighted_diagnostic",
            "sampling_weighted_conditional",
            "conditional_intensity_exceedance",
        ],
        "future_products": [
            "physical_probability",
            "annual_intensity_frequency",
        ],
        "unsupported_current_claims": [
            "annual_frequency",
            "return_period",
            "physical_probability",
            "risk_map",
            "operational_hazard_map",
            "validated_hazard_map",
        ],
        "notes": [
            "AOI bootstrap output is a research-diagnostic manifest, not a validation result.",
            "Current outputs remain conditional and must not be read as validation evidence.",
        ],
        "claim_boundary": {
            "current_allowed_products": [
                "unweighted_diagnostic",
                "sampling_weighted_conditional",
                "conditional_intensity_exceedance",
            ],
            "future_products": [
                "physical_probability",
                "annual_intensity_frequency",
            ],
            "unsupported_current_claims": [
                "annual_frequency",
                "return_period",
                "physical_probability",
                "risk_map",
                "operational_hazard_map",
                "validated_hazard_map",
            ],
            "notes": [
                "AOI bootstrap output is not validation evidence by itself.",
                "Current outputs remain conditional and are not physical probabilities.",
            ],
        },
    }


def source_zone_scenario_contract(site_id: str) -> dict[str, Any]:
    return {
        "source_zone_id_pattern": f"{site_id}_*",
        "source_zone_geometry": "LV95 polygon",
        "release_point_table": "one row per release point",
        "block_scenario_table": "CSV table with one row per block / scenario record",
        "scenario_probability_semantics": "normalized within a block family; no annual frequency claim",
    }


def geometry_from_bounds(bounds: list[float]) -> dict[str, Any]:
    if len(bounds) != 4:
        raise BootstrapError("bounds require xmin ymin xmax ymax")
    xmin, ymin, xmax, ymax = bounds
    validate_extent_values(xmin, ymin, xmax, ymax)
    coordinates = [
        [xmin, ymin],
        [xmax, ymin],
        [xmax, ymax],
        [xmin, ymax],
        [xmin, ymin],
    ]
    return {"geometry_type": "polygon", "coordinates": coordinates}


def geometry_from_geojson(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise BootstrapError(f"missing GeoJSON file: {path}")
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - path context matters.
        raise BootstrapError(f"failed to read GeoJSON polygon {path}: {exc}") from exc

    geometry = extract_geojson_geometry(raw)
    if geometry is None:
        raise BootstrapError(f"GeoJSON must contain a polygon geometry: {path}")
    coordinates = normalize_polygon_coordinates(geometry)
    if len(coordinates) < 4:
        raise BootstrapError("polygon must contain at least three vertices")
    return {"geometry_type": "polygon", "coordinates": coordinates}


def extract_geojson_geometry(node: Any) -> dict[str, Any] | None:
    if not isinstance(node, dict):
        return None
    if node.get("type") == "FeatureCollection":
        features = node.get("features")
        if isinstance(features, list):
            for feature in features:
                geometry = extract_geojson_geometry(feature)
                if geometry is not None:
                    return geometry
        return None
    if node.get("type") == "Feature":
        return extract_geojson_geometry(node.get("geometry"))
    if node.get("type") in {"Polygon", "MultiPolygon"}:
        return node
    return None


def normalize_polygon_coordinates(geometry: dict[str, Any]) -> list[list[float]]:
    if geometry.get("type") != "Polygon":
        raise BootstrapError("only polygon GeoJSON geometries are supported")
    rings = geometry.get("coordinates")
    if not isinstance(rings, list) or not rings:
        raise BootstrapError("polygon coordinates must contain an outer ring")
    outer_ring = rings[0]
    if not isinstance(outer_ring, list) or len(outer_ring) < 4:
        raise BootstrapError("polygon outer ring must contain at least four coordinates")
    coordinates: list[list[float]] = []
    for index, raw_vertex in enumerate(outer_ring):
        if not isinstance(raw_vertex, (list, tuple)) or len(raw_vertex) < 2:
            raise BootstrapError(f"polygon vertex {index} must contain x and y")
        x = float(raw_vertex[0])
        y = float(raw_vertex[1])
        validate_finite(x, f"polygon vertex {index} x")
        validate_finite(y, f"polygon vertex {index} y")
        coordinates.append([x, y])
    if coordinates[0] != coordinates[-1]:
        coordinates.append(list(coordinates[0]))
    if len(coordinates) < 4:
        raise BootstrapError("polygon outer ring must contain at least three vertices")
    return coordinates


def geometry_extent(coordinates: list[list[float]]) -> dict[str, float]:
    xs = [vertex[0] for vertex in coordinates]
    ys = [vertex[1] for vertex in coordinates]
    xmin = min(xs)
    ymin = min(ys)
    xmax = max(xs)
    ymax = max(ys)
    validate_extent_values(xmin, ymin, xmax, ymax)
    return {"xmin": xmin, "ymin": ymin, "xmax": xmax, "ymax": ymax}


def validate_extent_values(xmin: float, ymin: float, xmax: float, ymax: float) -> None:
    for value, label in ((xmin, "xmin"), (ymin, "ymin"), (xmax, "xmax"), (ymax, "ymax")):
        validate_finite(value, label)
    if xmax <= xmin:
        raise BootstrapError("xmax must be greater than xmin")
    if ymax <= ymin:
        raise BootstrapError("ymax must be greater than ymin")


def tile_catalog_ids_for_extent(extent: dict[str, float]) -> list[str]:
    min_east = tile_grid_floor(extent["xmin"])
    max_east = tile_grid_floor(extent["xmax"] - 1e-9)
    min_north = tile_grid_floor(extent["ymin"])
    max_north = tile_grid_floor(extent["ymax"] - 1e-9)
    return [
        f"{east // 1000}-{north // 1000}"
        for east in range(min_east, max_east + 1, 1000)
        for north in range(min_north, max_north + 1, 1000)
    ]


def tile_grid_floor(value: float) -> int:
    return int(value // 1000) * 1000


def hash_payload(payload: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")).hexdigest()


def validate_site_id(site_id: str) -> None:
    if not site_id or not site_id.strip():
        raise BootstrapError("site-id must be a non-empty string")
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-")
    if any(character not in allowed for character in site_id):
        raise BootstrapError("site-id may contain only letters, numbers, underscores, and hyphens")


def validate_crs(crs: str) -> None:
    if crs != SUPPORTED_CRS:
        raise BootstrapError(f"CRS must be {SUPPORTED_CRS}")


def validate_vertical_datum(vertical_datum: str) -> None:
    if vertical_datum != SUPPORTED_VERTICAL_DATUM:
        raise BootstrapError(f"vertical datum must be {SUPPORTED_VERTICAL_DATUM}")


def validate_output_root(output_root: Path) -> None:
    resolved = output_root.resolve(strict=False)
    tracked_roots = [ROOT / "docs", ROOT / "scripts", ROOT / "src", ROOT / "tests", ROOT / "validation" / "policies"]
    if resolved == ROOT or any(resolved.is_relative_to(root) for root in tracked_roots):
        raise BootstrapError(f"output-root must stay under an ignored scratch or repo-generated root: {output_root}")


def resolve_output_root(output_root: Path) -> Path:
    return output_root if output_root.is_absolute() else ROOT / output_root


def repo_relative(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def write_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def default_site_name(site_id: str) -> str:
    return site_id.replace("_", " ").replace("-", " ").title()


def validate_finite(value: float, label: str) -> None:
    if not isinstance(value, (int, float)):
        raise BootstrapError(f"{label} must be numeric")
    if not (value == value and value not in (float("inf"), float("-inf"))):
        raise BootstrapError(f"{label} must be finite")


class BootstrapError(ValueError):
    """User-facing AOI bootstrap validation error."""


def render_text_report(report: dict[str, Any]) -> str:
    lines = [
        f"schema_version: {report['schema_version']}",
        f"manifest_type: {report['manifest_type']}",
        f"manifest_id: {report['manifest_id']}",
        f"bootstrap_status: {report['bootstrap_status']}",
        f"candidate_site_id: {report['candidate_site_id']}",
        f"candidate_site_name: {report['candidate_site_name']}",
        f"site_config_path: {report['site_config_path']}",
        f"aoi_tile_catalog_path: {report['aoi_tile_catalog_path']}",
        f"acquisition_manifest_path: {report['acquisition_manifest_path']}",
        f"source_scenario_policy_path: {report['source_scenario_policy_path']}",
        "site_extent:",
    ]
    extent = report["site_extent"]
    for key in ("crs", "xmin", "ymin", "xmax", "ymax"):
        lines.append(f"  {key}: {extent[key]}")
    lines.append("product_policy:")
    for key in ("policy_status", "operational_status"):
        lines.append(f"  {key}: {report['product_policy'][key]}")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
