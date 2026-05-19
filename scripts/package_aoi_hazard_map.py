#!/usr/bin/env python3
"""Package AOI hazard outputs into a compact review bundle.

This helper is a packaging front door only. It consumes an existing hazard
output root, keeps the underlying hazard values unchanged, converts declared
GeoTIFF layers to COG where conversion is available, emits compact vector
overlays for the source-zone release geometry and scenario table, and writes a
manifest plus text summary with explicit claim boundaries.
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import sys
from pathlib import Path
from typing import Any

from scripts.hazard_output_manifests import output_manifest_entry
from scripts.hazard_output_writers import sha256_file, write_text
from scripts.prototype_cog_conversion import convert_to_cog


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "aoi_hazard_map_package_v1"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-root", required=True, type=Path, help="existing AOI hazard output root")
    parser.add_argument("--output-root", required=True, type=Path, help="destination package root")
    parser.add_argument("--overwrite", action="store_true", help="replace an existing output root")
    parser.add_argument("--format", choices=("json", "text"), default="json")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report = package_aoi_hazard_map(args.input_root, args.output_root, overwrite=args.overwrite)
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text(report))
    status = report.get("status", "")
    return 0 if status == "map_package_ready" else 2 if status.startswith("blocked_") else 1


def package_aoi_hazard_map(input_root: Path, output_root: Path, *, overwrite: bool = False) -> dict[str, Any]:
    input_root = Path(input_root)
    output_root = Path(output_root)
    map_manifest_path, map_manifest_missing = discover_single_manifest(input_root, "*map_package_manifest*.json")
    pilot_manifest_path, pilot_manifest_missing = discover_single_manifest(input_root, "*pilot_gis_package_manifest*.json")
    if not input_root.exists():
        return blocked_missing_hazard_outputs(
            input_root,
            output_root,
            [str(input_root)],
            "input hazard root does not exist",
        )
    if map_manifest_path is None or pilot_manifest_path is None:
        missing_paths = [path for path in (map_manifest_missing, pilot_manifest_missing) if path]
        return blocked_missing_hazard_outputs(
            input_root,
            output_root,
            missing_paths,
            "missing required hazard package manifests",
        )

    map_manifest = load_json(map_manifest_path)
    pilot_manifest = load_json(pilot_manifest_path)
    source_zone_metadata_path = resolve_repo_path(map_manifest.get("source_zone_metadata_path"))
    scenario_table_path = resolve_repo_path(map_manifest.get("scenario_table_path"))
    hazard_manifest_paths = [
        resolve_repo_path(path)
        for path in list(map_manifest.get("hazard_manifest_paths") or [])
        if path is not None
    ]
    if source_zone_metadata_path is None or scenario_table_path is None or not hazard_manifest_paths:
        missing_refs = []
        if source_zone_metadata_path is None:
            missing_refs.append("source_zone_metadata_path")
        if scenario_table_path is None:
            missing_refs.append("scenario_table_path")
        if not hazard_manifest_paths:
            missing_refs.append("hazard_manifest_paths")
        return blocked_missing_hazard_outputs(
            input_root,
            output_root,
            missing_refs,
            "missing required provenance or hazard manifest references",
        )
    raster_outputs = [output for output in map_manifest.get("raster_outputs", []) if output.get("format") == "geotiff"]
    required_paths = [source_zone_metadata_path, scenario_table_path, *hazard_manifest_paths]
    required_paths.extend(resolve_repo_path(output.get("path")) for output in raster_outputs if output.get("path"))
    missing_required_paths = [str(path) for path in required_paths if path is not None and not path.exists()]
    if missing_required_paths:
        return blocked_missing_hazard_outputs(
            input_root,
            output_root,
            missing_required_paths,
            "missing source hazard outputs",
        )
    if output_root.exists():
        if not overwrite:
            return blocked_missing_hazard_outputs(
                input_root,
                output_root,
                [str(output_root)],
                "output root exists and overwrite is disabled",
            )
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    raster_package = package_rasters(output_root, raster_outputs)
    source_zone_overlay = write_release_zone_overlay(
        output_root / "overlays" / "release_zone.geojson",
        source_zone_metadata_path,
    )
    scenario_overlay = write_scenario_overlay(
        output_root / "overlays" / "scenario_table.geojson",
        source_zone_metadata_path,
        scenario_table_path,
    )
    package_manifest_path = output_root / "aoi_hazard_map_package_manifest.json"
    summary_path = output_root / "aoi_hazard_map_package_summary.txt"
    layer_inventory = summarize_layer_inventory(
        [str(output.get("layer_name")) for output in raster_outputs if output.get("layer_name")],
        [str(entry.get("layer_name")) for entry in raster_package["inventory"] if entry.get("layer_name")],
    )
    report = {
        "schema_version": SCHEMA_VERSION,
        "status": raster_package["status"],
        "input_root": str(input_root),
        "output_root": str(output_root),
        "map_product_id": map_manifest.get("map_product_id"),
        "map_product_version": map_manifest.get("map_product_version"),
        "probability_mode": map_manifest.get("probability_mode"),
        "normalization_scope": map_manifest.get("normalization_scope"),
        "source_zone_id": map_manifest.get("source_zone_id"),
        "source_zone_metadata_path": str(source_zone_metadata_path),
        "scenario_table_path": str(scenario_table_path),
        "hazard_manifest_paths": [str(path) for path in hazard_manifest_paths],
        "package_manifest_path": str(package_manifest_path),
        "summary_path": str(summary_path),
        "raster_outputs": raster_package["inventory"],
        "vector_overlays": [source_zone_overlay, scenario_overlay],
        "inventory": [
            *raster_package["inventory"],
            source_zone_overlay,
            scenario_overlay,
        ],
        "layer_inventory_status": layer_inventory["status"],
        "missing_layer_names": layer_inventory["missing_layer_names"],
        "extra_layer_names": layer_inventory["extra_layer_names"],
        "claim_boundary": claim_boundary(map_manifest, pilot_manifest),
        "limitations": list(map_manifest.get("limitations", [])),
        "cog_blockers": raster_package["cog_blockers"],
        "missing_hazard_outputs": raster_package["missing_hazard_outputs"],
        "package_file_count": 0,
        "package_byte_count": 0,
        "package_manifest_sha256": None,
        "summary_sha256": None,
    }
    write_summary(summary_path, report)
    report["summary_sha256"] = sha256_file(summary_path)
    write_package_manifest(package_manifest_path, report)
    report["package_manifest_sha256"] = sha256_file(package_manifest_path)
    file_count, byte_count = count_files_and_bytes(output_root)
    report["package_file_count"] = file_count
    report["package_byte_count"] = byte_count
    return report


def package_rasters(output_root: Path, raster_outputs: list[dict[str, Any]]) -> dict[str, Any]:
    inventory: list[dict[str, Any]] = []
    cog_blockers: list[str] = []
    missing_hazard_outputs: list[str] = []
    for raster in raster_outputs:
        layer_name = str(raster.get("layer_name") or "")
        source_path = resolve_repo_path(raster.get("path"))
        if not layer_name or source_path is None or not source_path.exists():
            if source_path is not None:
                missing_hazard_outputs.append(str(source_path))
            continue
        output_path = output_root / "rasters" / f"{layer_name}.tif"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        conversion = convert_to_cog(source_path, output_path, overwrite=True)
        if conversion.get("status") != "cog_conversion_sample_ready":
            cog_blockers.append(f"{layer_name}:{conversion.get('status')}")
            output_path.unlink(missing_ok=True)
            shutil.copy2(source_path, output_path)
            cloud_optimized = False
            conversion_status = conversion.get("status")
        else:
            cloud_optimized = True
            conversion_status = conversion.get("status")
        entry = output_manifest_entry(output_path, "hazard_layer", "geotiff")
        entry.update(
            {
                "layer_name": layer_name,
                "source_path": str(source_path),
                "cloud_optimized": cloud_optimized,
                "conversion_status": conversion_status,
            }
        )
        inventory.append(entry)
    status = "map_package_ready" if not cog_blockers else "cog_blocked"
    return {
        "status": status,
        "inventory": inventory,
        "cog_blockers": cog_blockers,
        "missing_hazard_outputs": missing_hazard_outputs,
    }


def write_release_zone_overlay(path: Path, source_zone_metadata_path: Path) -> dict[str, Any]:
    source_zone_metadata = load_yaml(source_zone_metadata_path)
    geometry = source_zone_metadata.get("geometry") or {}
    coordinates = polygon_coordinates(geometry)
    feature = {
        "type": "Feature",
        "geometry": {"type": "Polygon", "coordinates": [coordinates]},
        "properties": {
            "source_zone_id": source_zone_metadata.get("source_zone_id"),
            "crs_epsg": source_zone_metadata.get("crs_epsg"),
            "vertical_datum": source_zone_metadata.get("vertical_datum"),
            "release_sampling_mode": (source_zone_metadata.get("release_sampling_policy") or {}).get("mode"),
            "release_count": (source_zone_metadata.get("release_sampling_policy") or {}).get("release_count"),
        },
    }
    payload = {
        "schema_version": "aoi_release_zone_overlay_v1",
        "type": "FeatureCollection",
        "features": [feature],
    }
    write_json(path, payload)
    return output_manifest_entry(path, "vector_overlay", "geojson")


def write_scenario_overlay(path: Path, source_zone_metadata_path: Path, scenario_table_path: Path | None) -> dict[str, Any]:
    source_zone_metadata = load_yaml(source_zone_metadata_path)
    geometry = source_zone_metadata.get("geometry") or {}
    coordinates = polygon_coordinates(geometry)
    features = []
    if scenario_table_path is not None:
        with scenario_table_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                features.append(
                    {
                        "type": "Feature",
                        "geometry": {"type": "Polygon", "coordinates": [coordinates]},
                        "properties": {
                            "scenario_id": row.get("scenario_id"),
                            "source_zone_id": row.get("source_zone_id"),
                            "block_scenario_id": row.get("block_scenario_id"),
                            "block_shape_class": row.get("block_shape_class"),
                            "block_mass_kg": parse_float(row.get("block_mass_kg")),
                            "block_radius_m": parse_float(row.get("block_radius_m")),
                            "sampling_weight": parse_float(row.get("sampling_weight")),
                        },
                    }
                )
    payload = {
        "schema_version": "aoi_scenario_overlay_v1",
        "type": "FeatureCollection",
        "features": features,
    }
    write_json(path, payload)
    return output_manifest_entry(path, "vector_overlay", "geojson")


def claim_boundary(map_manifest: dict[str, Any], pilot_manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "operational_status": map_manifest.get("operational_status") or pilot_manifest.get("operational_status"),
        "annualized": False,
        "physical_probability": False,
        "risk_or_exposure": False,
        "accepted_for_operational_use": False,
        "current_allowed_product_labels": [
            "unweighted_diagnostic",
            "sampling_weighted_conditional",
            "conditional_intensity_exceedance",
        ],
        "deferred_or_unsupported_labels": [
            "physical_probability",
            "annual_intensity_frequency",
            "return_period",
            "risk_map",
            "operational_hazard_map",
        ],
    }


def summarize_layer_inventory(source_layer_names: list[str], packaged_layer_names: list[str]) -> dict[str, Any]:
    missing_layer_names = [layer_name for layer_name in source_layer_names if layer_name not in packaged_layer_names]
    extra_layer_names = [layer_name for layer_name in packaged_layer_names if layer_name not in source_layer_names]
    if missing_layer_names and extra_layer_names:
        status = "inventory_mismatch"
    elif missing_layer_names:
        status = "scope_reduced"
    elif extra_layer_names:
        status = "scope_extended"
    else:
        status = "parity_match"
    return {
        "status": status,
        "missing_layer_names": missing_layer_names,
        "extra_layer_names": extra_layer_names,
    }


def write_package_manifest(path: Path, report: dict[str, Any]) -> None:
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "package_status": report["status"],
        "input_root": report["input_root"],
        "output_root": report["output_root"],
        "map_product_id": report["map_product_id"],
        "map_product_version": report["map_product_version"],
        "probability_mode": report["probability_mode"],
        "normalization_scope": report["normalization_scope"],
        "source_zone_id": report["source_zone_id"],
        "source_zone_metadata_path": report["source_zone_metadata_path"],
        "scenario_table_path": report["scenario_table_path"],
        "hazard_manifest_paths": report["hazard_manifest_paths"],
        "layer_inventory": report["inventory"],
        "raster_outputs": report["raster_outputs"],
        "vector_overlays": report["vector_overlays"],
        "layer_inventory_status": report["layer_inventory_status"],
        "missing_layer_names": report["missing_layer_names"],
        "extra_layer_names": report["extra_layer_names"],
        "claim_boundary": report["claim_boundary"],
        "limitations": report["limitations"],
        "cog_blockers": report["cog_blockers"],
        "missing_hazard_outputs": report["missing_hazard_outputs"],
        "package_manifest_path": report["package_manifest_path"],
        "summary_path": report["summary_path"],
        "summary_sha256": report["summary_sha256"],
    }
    write_json(path, manifest)


def write_summary(path: Path, report: dict[str, Any]) -> None:
    lines = [
        f"status\t{report['status']}",
        f"input_root\t{report['input_root']}",
        f"output_root\t{report['output_root']}",
        f"map_product_id\t{report['map_product_id']}",
        f"probability_mode\t{report['probability_mode']}",
        f"normalization_scope\t{report['normalization_scope']}",
        f"layer_inventory_status\t{report['layer_inventory_status']}",
        f"package_file_count\t{report['package_file_count']}",
        f"package_byte_count\t{report['package_byte_count']}",
        f"raster_count\t{len(report['raster_outputs'])}",
        f"vector_overlay_count\t{len(report['vector_overlays'])}",
        f"cog_blockers\t{report['cog_blockers']}",
        f"missing_hazard_outputs\t{report['missing_hazard_outputs']}",
        f"claim_boundary\t{report['claim_boundary']}",
    ]
    write_text(path, "\n".join(lines) + "\n")


def blocked_missing_hazard_outputs(
    input_root: Path,
    output_root: Path,
    missing_paths: list[str],
    error: str,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "blocked_missing_hazard_outputs",
        "input_root": str(input_root),
        "output_root": str(output_root),
        "missing_hazard_outputs": missing_paths,
        "error": error,
    }


def polygon_coordinates(geometry: dict[str, Any]) -> list[list[float]]:
    vertices = geometry.get("vertices")
    if not isinstance(vertices, list) or len(vertices) < 3:
        raise SystemExit("source zone geometry must define at least three vertices")
    coordinates = [[float(x), float(y)] for x, y in vertices]
    if coordinates[0] != coordinates[-1]:
        coordinates.append(coordinates[0])
    return coordinates


def parse_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def discover_single_manifest(root: Path, pattern: str) -> tuple[Path | None, str | None]:
    matches = sorted(root.glob(pattern))
    if not matches:
        return None, f"{root}/{pattern}"
    if len(matches) > 1:
        raise SystemExit(f"multiple manifests matching {pattern!r} under {root}: {matches}")
    return matches[0], None


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_yaml(path: Path) -> dict[str, Any]:
    import yaml  # type: ignore

    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit(f"expected mapping in YAML file: {path}")
    return data


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def resolve_repo_path(raw_path: Any) -> Path | None:
    if raw_path in (None, ""):
        return None
    path = Path(str(raw_path))
    return path if path.is_absolute() else ROOT / path


def count_files_and_bytes(root: Path) -> tuple[int, int]:
    files = [path for path in root.rglob("*") if path.is_file()]
    return len(files), sum(path.stat().st_size for path in files)


def render_text(report: dict[str, Any]) -> str:
    lines = [
        f"status\t{report['status']}",
        f"input_root\t{report['input_root']}",
        f"output_root\t{report['output_root']}",
        f"package_file_count\t{report.get('package_file_count', 0)}",
        f"package_byte_count\t{report.get('package_byte_count', 0)}",
        f"layer_inventory_status\t{report.get('layer_inventory_status')}",
        f"cog_blockers\t{report.get('cog_blockers', [])}",
        f"missing_hazard_outputs\t{report.get('missing_hazard_outputs', [])}",
    ]
    if report.get("error"):
        lines.append(f"error\t{report['error']}")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
