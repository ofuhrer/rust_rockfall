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
from unittest.mock import patch

from scripts.hazard_output_manifests import output_manifest_entry
from scripts.hazard_output_writers import sha256_file, write_text
from scripts import generate_aoi_map_qa_review as qa_review
from scripts.lib.workflow_validation import (
    build_blocked_report,
    build_release_zone_provenance_intake,
    resolve_optional_repo_path,
)
from scripts.prototype_cog_conversion import convert_to_cog
from scripts import summarize_observed_runout_deposition_intake_contract as observed_intake_helper

try:
    import yaml  # type: ignore
except ImportError as exc:  # pragma: no cover - environment setup.
    raise SystemExit("PyYAML is required. Run this script with `PYENV_VERSION=system uv run python ...`; CI may use `requirements-tools.txt`") from exc


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "aoi_hazard_map_package_v1"
EVIDENCE_OVERLAY_HOOK_SCHEMA_VERSION = "aoi_observed_evidence_overlay_hook_v1"
DIAGNOSTIC_HAZARD_OUTPUT_ROLE = "diagnostic_hazard_outputs"
OBSERVED_EVIDENCE_OVERLAY_ROLE = "observed_evidence_overlays"
CALIBRATION_INPUT_ROLE = "calibration_inputs"
HOLDOUT_EVIDENCE_ROLE = "holdout_evidence"
DEFERRED_SOURCE_FREQUENCY_ROLE = "deferred_source_frequency_records"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-root", required=True, type=Path, help="existing AOI hazard output root")
    parser.add_argument("--output-root", required=True, type=Path, help="destination package root")
    parser.add_argument(
        "--evidence-root",
        type=Path,
        default=None,
        help="optional staged observed-evidence root containing accepted benchmark or field-supported provenance",
    )
    parser.add_argument("--overwrite", action="store_true", help="replace an existing output root")
    parser.add_argument("--format", choices=("json", "text"), default="json")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report = package_aoi_hazard_map(
        args.input_root,
        args.output_root,
        overwrite=args.overwrite,
        evidence_root=args.evidence_root,
    )
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text(report))
    status = report.get("status", "")
    return 0 if status == "map_package_ready" else 2 if status.startswith("blocked_") else 1


def package_aoi_hazard_map(
    input_root: Path,
    output_root: Path,
    *,
    overwrite: bool = False,
    evidence_root: Path | None = None,
) -> dict[str, Any]:
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
    source_zone_metadata_path = resolve_optional_repo_path(ROOT, map_manifest.get("source_zone_metadata_path"))
    scenario_table_path = resolve_optional_repo_path(ROOT, map_manifest.get("scenario_table_path"))
    hazard_manifest_paths = [
        resolved_path
        for path in list(map_manifest.get("hazard_manifest_paths") or [])
        if (resolved_path := resolve_optional_repo_path(ROOT, path)) is not None
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
    required_paths.extend(
        resolved_path
        for output in raster_outputs
        if (resolved_path := resolve_optional_repo_path(ROOT, output.get("path"))) is not None
    )
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
    evidence_hook = package_observed_evidence_overlays(output_root, evidence_root)
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
        "diagnostic_hazard_outputs": diagnostic_hazard_outputs_section(raster_package["inventory"]),
        "observed_evidence_overlay_hook": evidence_hook,
        "observed_evidence_overlays": observed_evidence_overlays_section(evidence_hook),
        "calibration_inputs": non_operational_artifact_section(
            CALIBRATION_INPUT_ROLE,
            "not_included",
            "Calibration inputs are intentionally excluded from AOI map packages.",
        ),
        "holdout_evidence": non_operational_artifact_section(
            HOLDOUT_EVIDENCE_ROLE,
            "not_included",
            "Holdout evidence is intentionally excluded from AOI map packages.",
        ),
        "deferred_source_frequency_records": non_operational_artifact_section(
            DEFERRED_SOURCE_FREQUENCY_ROLE,
            "deferred",
            "Source-frequency records remain deferred and are not included here.",
        ),
        "vector_overlays": [source_zone_overlay, scenario_overlay, *evidence_hook["observed_evidence_overlays"]],
        "inventory": [
            *raster_package["inventory"],
            source_zone_overlay,
            scenario_overlay,
            *evidence_hook["observed_evidence_overlays"],
        ],
        "layer_inventory_status": layer_inventory["status"],
        "missing_layer_names": layer_inventory["missing_layer_names"],
        "extra_layer_names": layer_inventory["extra_layer_names"],
        "claim_boundary": claim_boundary(map_manifest, pilot_manifest),
        "limitations": list(map_manifest.get("limitations", [])),
        "cog_blockers": raster_package["cog_blockers"],
        "missing_hazard_outputs": raster_package["missing_hazard_outputs"],
        "review_surface_paths": {},
        "package_file_count": 0,
        "package_byte_count": 0,
        "package_manifest_sha256": None,
        "summary_sha256": None,
    }
    write_summary(summary_path, report)
    report["summary_sha256"] = sha256_file(summary_path)
    write_package_manifest(package_manifest_path, report)
    report["package_manifest_sha256"] = sha256_file(package_manifest_path)
    review_report = qa_review.build_review_surface(input_root=output_root, output_root=output_root)
    report["review_surface_status"] = review_report.get("status")
    report["review_surface_paths"] = review_report.get("review_surface_paths") or {}
    file_count, byte_count = count_files_and_bytes(output_root)
    report["package_file_count"] = file_count
    report["package_byte_count"] = byte_count
    write_summary(summary_path, report)
    report["summary_sha256"] = sha256_file(summary_path)
    write_package_manifest(package_manifest_path, report)
    report["package_manifest_sha256"] = sha256_file(package_manifest_path)
    return report


def package_rasters(output_root: Path, raster_outputs: list[dict[str, Any]]) -> dict[str, Any]:
    inventory: list[dict[str, Any]] = []
    cog_blockers: list[str] = []
    missing_hazard_outputs: list[str] = []
    for raster in raster_outputs:
        layer_name = str(raster.get("layer_name") or "")
        source_path = resolve_optional_repo_path(ROOT, raster.get("path"))
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


def package_observed_evidence_overlays(output_root: Path, evidence_root: Path | None) -> dict[str, Any]:
    diagnostic_hazard_outputs = diagnostic_hazard_outputs_section([])
    calibration_inputs = non_operational_artifact_section(
        CALIBRATION_INPUT_ROLE,
        "not_included",
        "Calibration inputs are not packaged with AOI map outputs.",
    )
    holdout_evidence = non_operational_artifact_section(
        HOLDOUT_EVIDENCE_ROLE,
        "not_included",
        "Holdout evidence is intentionally kept separate from AOI map outputs.",
    )
    deferred_source_frequency_records = non_operational_artifact_section(
        DEFERRED_SOURCE_FREQUENCY_ROLE,
        "deferred",
        "Source-frequency records are deferred and excluded from AOI map outputs.",
    )

    observed_overlay_result = classify_observed_evidence_overlay(output_root, evidence_root)
    release_zone_overlay_result = classify_release_zone_provenance_overlay(output_root, evidence_root)
    observed_evidence_overlays = [
        overlay
        for overlay in (
            observed_overlay_result.get("overlay"),
            release_zone_overlay_result.get("overlay"),
        )
        if overlay is not None
    ]
    hook_status = derive_overlay_hook_status(
        [
            str(observed_overlay_result["status"]),
            str(release_zone_overlay_result["status"]),
        ]
    )
    if observed_evidence_overlays and hook_status.startswith("blocked_"):
        hook_status = "ready"

    return {
        "schema_version": EVIDENCE_OVERLAY_HOOK_SCHEMA_VERSION,
        "hook_status": hook_status,
        "evidence_root": str(evidence_root) if evidence_root is not None else None,
        "observed_runout_deposition_overlay_status": observed_overlay_result["status"],
        "observed_runout_deposition_overlay_blockers": observed_overlay_result["blockers"],
        "release_zone_provenance_overlay_status": release_zone_overlay_result["status"],
        "release_zone_provenance_overlay_blockers": release_zone_overlay_result["blockers"],
        "observed_evidence_overlays": observed_evidence_overlays,
        "diagnostic_hazard_outputs": diagnostic_hazard_outputs,
        "calibration_inputs": calibration_inputs,
        "holdout_evidence": holdout_evidence,
        "deferred_source_frequency_records": deferred_source_frequency_records,
    }


def classify_observed_evidence_overlay(output_root: Path, evidence_root: Path | None) -> dict[str, Any]:
    if evidence_root is None:
        return blocked_overlay_result("blocked_missing_evidence", ["evidence_root_missing"])

    observed_root = evidence_root / "observed_runout_deposition_benchmark"
    manifest_path = observed_root / "manifest.json"
    geometry_path = observed_root / "observed_runout_deposition.geojson"
    if not observed_root.exists() or not manifest_path.exists() or not geometry_path.exists():
        missing: list[str] = []
        if not evidence_root.exists():
            missing.append(str(evidence_root))
        if not observed_root.exists():
            missing.append(str(observed_root))
        if not manifest_path.exists():
            missing.append(str(manifest_path))
        if not geometry_path.exists():
            missing.append(str(geometry_path))
        return blocked_overlay_result("blocked_missing_evidence", missing)

    with patch.object(observed_intake_helper, "EXPECTED_BENCHMARK_ROOT", observed_root), patch.object(
        observed_intake_helper,
        "EXPECTED_BENCHMARK_MANIFEST",
        manifest_path,
    ), patch.object(
        observed_intake_helper,
        "EXPECTED_BENCHMARK_GEOMETRY",
        geometry_path,
    ), patch.object(
        observed_intake_helper,
        "EXPECTED_BENCHMARK_INPUTS",
        (
            manifest_path,
            geometry_path,
        ),
    ):
        report = observed_intake_helper.build_report()

    status = str(report.get("observed_runout_deposition_intake_status") or "blocked_schema_gap")
    blockers = list(report.get("missing_inputs") or [])
    if isinstance(report.get("real_input_intake_report"), dict):
        blockers = list(report["real_input_intake_report"].get("blocking_reasons") or blockers)
    if status == "ready":
        overlay_path = output_root / "overlays" / "observed_runout_deposition.geojson"
        write_observed_runout_deposition_overlay(overlay_path, manifest_path, geometry_path)
        overlay = output_manifest_entry(overlay_path, "observed_evidence_overlay", "geojson")
        overlay.update(
            {
                "overlay_role": "observed_runout_deposition",
                "evidence_category": "observed_evidence_overlay",
                "acceptance_status": "accepted",
                "source_manifest_path": str(manifest_path),
                "source_geometry_path": str(geometry_path),
                "real_input_intake_status": status,
                "claim_boundary": "observed evidence only; no calibration, physical probability, annual frequency, risk, or operational claim",
            }
        )
        return {"status": "ready", "blockers": [], "overlay": overlay}
    if status == "blocked_fixture_only_inputs":
        return blocked_overlay_result(status, blockers)
    if status == "blocked_missing_inputs":
        return blocked_overlay_result("blocked_missing_evidence", blockers)
    return blocked_overlay_result("blocked_schema_gap", blockers)


def classify_release_zone_provenance_overlay(output_root: Path, evidence_root: Path | None) -> dict[str, Any]:
    if evidence_root is None:
        return blocked_overlay_result("blocked_missing_evidence", ["evidence_root_missing"])

    record_path = next(
        (
            evidence_root / candidate
            for candidate in (
                "release_zone_provenance.yaml",
                "release_zone_provenance.yml",
                "release_zone_provenance.json",
            )
            if (evidence_root / candidate).exists()
        ),
        None,
    )
    if record_path is None or not record_path.exists():
        return blocked_overlay_result("blocked_missing_evidence", [str(evidence_root / "release_zone_provenance.*")])

    record = load_structured_record(record_path)
    if not isinstance(record, dict):
        return blocked_overlay_result("blocked_schema_gap", [str(record_path)])

    intake = build_release_zone_provenance_intake(record)
    geometry = record.get("geometry") or record.get("geometry_value")
    if not isinstance(geometry, dict):
        return blocked_overlay_result("blocked_schema_gap", [f"{record_path}:geometry"])

    provenance_state = str(intake.get("release_zone_provenance_state") or "")
    review_decision = str(intake.get("review_decision") or "")
    if provenance_state == "field_supported" and review_decision == "accepted":
        overlay_path = output_root / "overlays" / "release_zone_provenance.geojson"
        write_release_zone_provenance_overlay(overlay_path, record, geometry)
        overlay = output_manifest_entry(overlay_path, "observed_evidence_overlay", "geojson")
        overlay.update(
            {
                "overlay_role": "release_zone_provenance",
                "evidence_category": "observed_evidence_overlay",
                "acceptance_status": "accepted",
                "source_record_path": str(record_path),
                "release_zone_provenance_state": provenance_state,
                "review_decision": review_decision,
                "claim_boundary": "field-supported provenance only; no calibration, physical probability, annual frequency, risk, or operational claim",
            }
        )
        return {"status": "ready", "blockers": [], "overlay": overlay}
    if provenance_state == "blocked_missing_provenance":
        return blocked_overlay_result("blocked_missing_evidence", [str(record_path)])
    if provenance_state == "workflow_generated":
        return blocked_overlay_result("blocked_fixture_only_inputs", [str(record_path)])
    return blocked_overlay_result("blocked_schema_gap", [str(record_path)])


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
    entry = output_manifest_entry(path, "vector_overlay", "geojson")
    entry.update(
        {
            "overlay_role": "source_zone_release_geometry",
            "evidence_category": "diagnostic_workflow_overlay",
            "claim_boundary": "workflow provenance overlay only; not calibration, holdout, or frequency evidence",
        }
    )
    return entry


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
    entry = output_manifest_entry(path, "vector_overlay", "geojson")
    entry.update(
        {
            "overlay_role": "scenario_table",
            "evidence_category": "diagnostic_workflow_overlay",
            "claim_boundary": "conditional scenario overlay only; not frequency evidence",
        }
    )
    return entry


def write_release_zone_provenance_overlay(path: Path, record: dict[str, Any], geometry: dict[str, Any]) -> None:
    coordinates = geometry_coordinates(geometry)
    payload = {
        "schema_version": "aoi_release_zone_provenance_overlay_v1",
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Polygon", "coordinates": [coordinates]},
                "properties": {
                    "source_id": record.get("source_id"),
                    "source_origin_description": record.get("source_origin_description"),
                    "source_reference_frame": record.get("source_reference_frame"),
                    "source_geometry_reference": record.get("source_geometry_reference"),
                    "provenance_uri": record.get("provenance_uri"),
                    "release_zone_provenance_state": record.get("release_zone_provenance_state"),
                    "review_decision": record.get("review_decision"),
                },
            }
        ],
    }
    write_json(path, payload)


def write_observed_runout_deposition_overlay(path: Path, manifest_path: Path, geometry_path: Path) -> None:
    manifest = load_json(manifest_path)
    provenance = manifest.get("provenance") if isinstance(manifest.get("provenance"), dict) else {}
    license_info = manifest.get("license") if isinstance(manifest.get("license"), dict) else {}
    geometry_record = load_json(geometry_path)
    geometry = extract_geojson_geometry(geometry_record)
    feature = {
        "type": "Feature",
        "geometry": geometry,
        "properties": {
            "source_manifest_path": str(manifest_path),
            "source_geometry_path": str(geometry_path),
            "overlay_role": "observed_runout_deposition",
            "acceptance_status": "accepted",
            "source_name": provenance.get("source_name"),
            "source_id": provenance.get("source_id"),
            "source_origin_description": provenance.get("source_origin_description"),
            "provenance_uri": provenance.get("provenance_uri"),
            "license_status": license_info.get("status"),
        },
    }
    payload = {
        "schema_version": "aoi_observed_runout_deposition_overlay_v1",
        "type": "FeatureCollection",
        "features": [feature],
    }
    write_json(path, payload)


def geometry_coordinates(geometry: dict[str, Any]) -> list[list[float]]:
    vertices = geometry.get("coordinates")
    if isinstance(vertices, list) and vertices:
        first = vertices[0]
        if isinstance(first, list) and first and isinstance(first[0], list):
            ring = first
        else:
            ring = vertices
        coordinates = [[float(x), float(y)] for x, y in ring]
        if coordinates and coordinates[0] != coordinates[-1]:
            coordinates.append(coordinates[0])
        return coordinates
    vertices = geometry.get("vertices")
    if isinstance(vertices, list) and len(vertices) >= 3:
        coordinates = [[float(x), float(y)] for x, y in vertices]
        if coordinates[0] != coordinates[-1]:
            coordinates.append(coordinates[0])
        return coordinates
    raise SystemExit("release-zone provenance geometry must define polygon coordinates")


def extract_geojson_geometry(record: dict[str, Any]) -> dict[str, Any]:
    if record.get("type") == "FeatureCollection":
        features = record.get("features")
        if isinstance(features, list) and features:
            first = features[0]
            if isinstance(first, dict) and isinstance(first.get("geometry"), dict):
                return first["geometry"]
    if record.get("type") == "Feature" and isinstance(record.get("geometry"), dict):
        return record["geometry"]
    if isinstance(record.get("geometry"), dict):
        return record["geometry"]
    if record.get("type") in {"LineString", "Polygon", "MultiLineString", "MultiPolygon"}:
        return record
    raise SystemExit("observed evidence geometry must be valid GeoJSON")


def load_structured_record(path: Path) -> dict[str, Any]:
    if path.suffix.lower() in {".yaml", ".yml"}:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    else:
        data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def derive_overlay_hook_status(statuses: list[str]) -> str:
    if any(status == "ready" for status in statuses):
        return "ready"
    if any(status == "blocked_fixture_only_inputs" for status in statuses):
        return "blocked_fixture_only_inputs"
    if any(status == "blocked_schema_gap" for status in statuses):
        return "blocked_schema_gap"
    return "blocked_missing_evidence"


def blocked_overlay_result(status: str, blockers: list[str]) -> dict[str, Any]:
    return {
        "status": status,
        "blockers": blockers,
        "overlay": None,
    }


def non_operational_artifact_section(role: str, status: str, note: str) -> dict[str, Any]:
    return {
        "schema_version": EVIDENCE_OVERLAY_HOOK_SCHEMA_VERSION,
        "role": role,
        "status": status,
        "claim_boundary": note,
        "items": [],
    }


def diagnostic_hazard_outputs_section(raster_inventory: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema_version": EVIDENCE_OVERLAY_HOOK_SCHEMA_VERSION,
        "role": DIAGNOSTIC_HAZARD_OUTPUT_ROLE,
        "status": "present",
        "claim_boundary": "diagnostic hazard outputs only; not calibration, holdout, or frequency evidence",
        "items": list(raster_inventory),
    }


def observed_evidence_overlays_section(evidence_hook: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": EVIDENCE_OVERLAY_HOOK_SCHEMA_VERSION,
        "role": OBSERVED_EVIDENCE_OVERLAY_ROLE,
        "status": evidence_hook["hook_status"],
        "claim_boundary": "observed evidence overlays are optional and do not imply calibration, physical probability, annual frequency, risk, or operational readiness",
        "items": list(evidence_hook["observed_evidence_overlays"]),
        "blockers": {
            "observed_runout_deposition": list(evidence_hook["observed_runout_deposition_overlay_blockers"]),
            "release_zone_provenance": list(evidence_hook["release_zone_provenance_overlay_blockers"]),
        },
    }


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
        "diagnostic_hazard_outputs": report["diagnostic_hazard_outputs"],
        "observed_evidence_overlay_hook": report["observed_evidence_overlay_hook"],
        "observed_evidence_overlays": report["observed_evidence_overlays"],
        "calibration_inputs": report["calibration_inputs"],
        "holdout_evidence": report["holdout_evidence"],
        "deferred_source_frequency_records": report["deferred_source_frequency_records"],
        "layer_inventory_status": report["layer_inventory_status"],
        "missing_layer_names": report["missing_layer_names"],
        "extra_layer_names": report["extra_layer_names"],
        "claim_boundary": report["claim_boundary"],
        "limitations": report["limitations"],
        "cog_blockers": report["cog_blockers"],
        "missing_hazard_outputs": report["missing_hazard_outputs"],
        "review_surface_status": report.get("review_surface_status"),
        "review_surface_paths": report.get("review_surface_paths", {}),
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
        f"observed_evidence_overlay_hook_status\t{report['observed_evidence_overlay_hook']['hook_status']}",
        f"observed_runout_deposition_overlay_status\t{report['observed_evidence_overlay_hook']['observed_runout_deposition_overlay_status']}",
        f"release_zone_provenance_overlay_status\t{report['observed_evidence_overlay_hook']['release_zone_provenance_overlay_status']}",
        f"observed_evidence_overlay_count\t{len(report['observed_evidence_overlays']['items'])}",
        f"review_entrypoint\t{report.get('review_surface_paths', {}).get('entrypoint')}",
        f"review_surface_status\t{report.get('review_surface_status')}",
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
    return build_blocked_report(
        schema_version=SCHEMA_VERSION,
        status_key="status",
        missing_inputs=missing_paths,
        blocked_reason=error,
        blocked_status="blocked_missing_hazard_outputs",
        extra_fields={
            "input_root": str(input_root),
            "output_root": str(output_root),
            "missing_hazard_outputs": missing_paths,
            "error": error,
        },
    )


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
        f"observed_evidence_overlay_hook_status\t{report.get('observed_evidence_overlay_hook', {}).get('hook_status')}",
        f"cog_blockers\t{report.get('cog_blockers', [])}",
        f"missing_hazard_outputs\t{report.get('missing_hazard_outputs', [])}",
    ]
    if report.get("error"):
        lines.append(f"error\t{report['error']}")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
