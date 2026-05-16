#!/usr/bin/env python3
"""Audit GIS and COG package readiness for existing same-scale Tschamut outputs.

This helper is read-only. It inspects existing hazard manifests, map-package
manifests, pilot-GIS package manifests, and a bounded sample of raster metadata
for the selected same-scale artifact roots. It does not regenerate outputs,
perform manual QGIS QA, or change scientific settings.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import shutil
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ARTIFACT_ROOTS = [
    ROOT / "hazard/results/tschamut_public_pilot/gate_v1",
    ROOT / "hazard/results/tschamut_public_pilot/target_gate_v1",
    ROOT / "hazard/results/tschamut_public_pilot/sampling_sensitivity_v1_full",
    ROOT / "hazard/results/tschamut_public_pilot/sampling_sensitivity_v2_full",
]
SCHEMA_VERSION = "tschamut_gis_cog_package_readiness_v1"

REQUIRED_MAP_PACKAGE_FIELDS = (
    "schema_version",
    "map_product_id",
    "map_product_version",
    "probability_mode",
    "normalization_scope",
    "source_zone_id",
    "source_zone_metadata_path",
    "scenario_table_path",
    "hazard_manifest_paths",
    "raster_outputs",
    "layer_semantics",
    "limitations",
    "operational_status",
)
REQUIRED_PILOT_GIS_FIELDS = (
    "schema_version",
    "package_version",
    "case_id",
    "grid",
    "terrain",
    "terrain_metadata",
    "hazard_manifest_paths",
    "raster_outputs",
    "manifest_outputs",
    "parity_outputs",
    "conditional_intensity_exceedance_curve_outputs",
    "visual_qa",
    "raster_contract",
    "probability_claim_boundary",
    "limitations",
    "operational_status",
)


class GisCogReadinessError(ValueError):
    """User-facing audit error."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--artifact-root",
        action="append",
        type=Path,
        dest="artifact_roots",
        help="same-scale hazard output root to audit; may be repeated",
    )
    parser.add_argument("--format", choices=("json", "text"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    parser.add_argument(
        "--converted-sample",
        type=Path,
        default=None,
        help="optional scratch COG sample to verify alongside the package audit",
    )
    parser.add_argument(
        "--converted-package-root",
        action="append",
        type=Path,
        dest="converted_package_roots",
        help="optional ignored package root to audit as a COG-ready proof; may be repeated",
    )
    args = parser.parse_args(argv)

    try:
        report = build_gis_cog_readiness_report(
            artifact_roots=args.artifact_roots,
            converted_sample_path=args.converted_sample,
            converted_package_roots=args.converted_package_roots,
            raster_metadata_provider=inspect_raster_metadata,
        )
    except GisCogReadinessError as exc:
        print(f"GIS/COG readiness audit error: {exc}", file=sys.stderr)
        return 2

    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text_report(report))
    return 0 if report["gis_cog_readiness_status"] in {"gis_package_ready", "gis_package_ready_cog_blocked"} else 2


def build_gis_cog_readiness_report(
    artifact_roots: list[Path] | None = None,
    *,
    converted_sample_path: Path | None = None,
    converted_package_roots: list[Path] | None = None,
    raster_metadata_provider: Callable[[Path], dict[str, Any] | None] | None = None,
) -> dict[str, Any]:
    roots = [Path(root) for root in (artifact_roots or DEFAULT_ARTIFACT_ROOTS)]
    converted_roots = [Path(root) for root in (converted_package_roots or [])]
    provider = raster_metadata_provider or inspect_raster_metadata
    artifacts = [audit_artifact_root(root, provider) for root in roots]
    converted_sample = audit_converted_sample(converted_sample_path, provider)
    converted_packages = [audit_artifact_root(root, provider, verify_all_geotiffs=True) for root in converted_roots]
    artifacts_by_id = {artifact["artifact_id"]: artifact for artifact in artifacts}
    converted_packages = [
        compare_layer_inventory(artifacts_by_id.get(package["artifact_id"]), package) for package in converted_packages
    ]
    converted_packages = [normalize_converted_package_status(package) for package in converted_packages]

    missing_any = any(
        artifact["manifest_completeness"]["map_package_manifest_missing_fields"]
        or artifact["manifest_completeness"]["pilot_gis_package_manifest_missing_fields"]
        or artifact["manifest_completeness"]["missing_raster_outputs"]
        for artifact in artifacts
    )
    missing_gdal = any(artifact["cog_readiness_indicators"]["gdalinfo_available"] is False for artifact in artifacts)
    cog_blocked = any(artifact["blockers"] for artifact in artifacts)

    if missing_any:
        gis_status = "blocked_missing_inputs"
    elif missing_gdal:
        gis_status = "metadata_only"
    elif cog_blocked:
        gis_status = "gis_package_ready_cog_blocked"
    else:
        gis_status = "gis_package_ready"

    converted_summary = summarize_converted_package_readiness(converted_packages)
    report = {
        "schema_version": SCHEMA_VERSION,
        "gis_cog_readiness_status": gis_status,
        "readiness_status": gis_status,
        "standard_package_readiness_status": summarize_standard_package_readiness(artifacts),
        "standard_package_layer_counts": {artifact["artifact_id"]: artifact["raster_layer_count"] for artifact in artifacts},
        "standard_package_status": {artifact["artifact_id"]: artifact["cog_package_status"] for artifact in artifacts},
        "converted_sample_status": converted_sample["status"],
        "converted_sample_path": converted_sample["path"],
        "converted_sample": converted_sample,
        "artifacts_audited": len(artifacts),
        "artifact_roots": [str(artifact["artifact_root"]) for artifact in artifacts],
        "converted_package_roots": [str(artifact["artifact_root"]) for artifact in converted_packages],
        "hazard_manifest_paths": {artifact["artifact_id"]: artifact["hazard_manifest_path"] for artifact in artifacts},
        "map_package_manifest_paths": {artifact["artifact_id"]: artifact["map_package_manifest_path"] for artifact in artifacts},
        "pilot_gis_package_manifest_paths": {
            artifact["artifact_id"]: artifact["pilot_gis_package_manifest_path"] for artifact in artifacts
        },
        "converted_package_status": {
            artifact["artifact_id"]: artifact["cog_package_status"] for artifact in converted_packages
        },
        "converted_package_readiness_status": converted_summary["converted_package_readiness_status"],
        "any_converted_package_ready": converted_summary["any_converted_package_ready"],
        "converted_package_layer_inventory_status": summarize_converted_package_layer_inventory(converted_packages),
        "converted_package_scope_boundaries": {
            artifact["artifact_id"]: artifact["cog_scope"] for artifact in converted_packages
        },
        "converted_package_layer_counts": {
            artifact["artifact_id"]: artifact["converted_layer_count"] for artifact in converted_packages
        },
        "converted_package_scope_deltas": {
            artifact["artifact_id"]: artifact["scope_delta"] for artifact in converted_packages
        },
        "converted_packages": converted_packages,
        "raster_layer_count": {artifact["artifact_id"]: artifact["raster_layer_count"] for artifact in artifacts},
        "crs_or_epsg": {artifact["artifact_id"]: artifact["crs_or_epsg"] for artifact in artifacts},
        "grid_dimensions": {artifact["artifact_id"]: artifact["grid_dimensions"] for artifact in artifacts},
        "transform_or_cell_size": {artifact["artifact_id"]: artifact["transform_or_cell_size"] for artifact in artifacts},
        "nodata_values": {artifact["artifact_id"]: artifact["nodata_values"] for artifact in artifacts},
        "geotiff_presence": {artifact["artifact_id"]: artifact["geotiff_presence"] for artifact in artifacts},
        "cog_readiness_indicators": {artifact["artifact_id"]: artifact["cog_readiness_indicators"] for artifact in artifacts},
        "manifest_completeness": {artifact["artifact_id"]: artifact["manifest_completeness"] for artifact in artifacts},
        "missing_package_fields": {artifact["artifact_id"]: artifact["missing_package_fields"] for artifact in artifacts},
        "blockers": {artifact["artifact_id"]: artifact["blockers"] for artifact in artifacts},
        "qgis_manual_qa_status": summarize_qgis_status(artifacts),
        "scientific_acceptance_status": "inconclusive",
        "scale_up_authorized": False,
        "operational_claims_allowed": False,
        "artifacts": artifacts,
    }
    return report


def audit_converted_sample(
    sample_path: Path | None,
    raster_metadata_provider: Callable[[Path], dict[str, Any] | None],
) -> dict[str, Any]:
    if sample_path is None:
        return {
            "status": "not_provided",
            "path": None,
            "exists": False,
            "metadata": None,
            "blockers": [],
        }
    sample_path = Path(sample_path)
    if not sample_path.exists():
        return {
            "status": "blocked_missing_inputs",
            "path": str(sample_path),
            "exists": False,
            "metadata": None,
            "blockers": [f"missing_input:{sample_path}"],
        }
    metadata = raster_metadata_provider(sample_path)
    if metadata is None:
        return {
            "status": "missing_gdal",
            "path": str(sample_path),
            "exists": True,
            "metadata": None,
            "blockers": ["gdalinfo_unavailable_or_failed"],
        }
    if metadata.get("status") == "verification_failed":
        return {
            "status": "verification_failed",
            "path": str(sample_path),
            "exists": True,
            "metadata": metadata,
            "blockers": [metadata.get("error") or "verification_failed"],
        }
    if metadata.get("status") != "ok":
        return {
            "status": metadata.get("status") or "unknown",
            "path": str(sample_path),
            "exists": True,
            "metadata": metadata,
            "blockers": [metadata.get("error") or "unknown"],
        }
    sample_raster_cog_layout = metadata.get("sample_raster_cog_layout")
    if sample_raster_cog_layout is None:
        sample_raster_cog_layout = metadata.get("image_structure", {}).get("LAYOUT") == "COG"
    sample_raster_tiled = metadata.get("sample_raster_tiled")
    if sample_raster_tiled is None:
        sample_raster_tiled = bool(
            metadata.get("block_size")
            and isinstance(metadata.get("size"), list)
            and len(metadata["size"]) == 2
            and metadata["block_size"][0] < metadata["size"][0]
            and metadata["block_size"][1] < metadata["size"][1]
        )
    sample_raster_overviews = metadata.get("sample_raster_overviews")
    if sample_raster_overviews is None:
        sample_raster_overviews = metadata.get("overview_count", 0) > 0
    enriched_metadata = {
        **metadata,
        "sample_raster_cog_layout": bool(sample_raster_cog_layout),
        "sample_raster_tiled": bool(sample_raster_tiled),
        "sample_raster_overviews": bool(sample_raster_overviews),
    }
    if sample_raster_cog_layout and sample_raster_tiled and sample_raster_overviews:
        status = "cog_conversion_sample_ready"
        blockers: list[str] = []
    else:
        status = "verification_failed"
        blockers = []
        if not sample_raster_tiled:
            blockers.append("sample_raster_not_tiled")
        if not sample_raster_overviews:
            blockers.append("sample_raster_no_overviews")
        if not sample_raster_cog_layout:
            blockers.append("sample_raster_not_cog_layout")
    return {
        "status": status,
        "path": str(sample_path),
        "exists": True,
        "metadata": enriched_metadata,
        "blockers": blockers,
    }


def summarize_converted_package_readiness(converted_packages: list[dict[str, Any]]) -> dict[str, Any]:
    if not converted_packages:
        return {
            "converted_package_readiness_status": "not_provided",
            "any_converted_package_ready": False,
        }
    statuses = [package.get("cog_package_status") for package in converted_packages]
    any_ready = any(status in {"cog_package_ready", "cog_package_ready_with_scope_delta"} for status in statuses)
    if any(status == "blocked_missing_inputs" for status in statuses):
        readiness_status = "blocked_missing_inputs"
    elif any(status == "metadata_only" for status in statuses):
        readiness_status = "metadata_only"
    elif all(status == "cog_package_ready" for status in statuses):
        readiness_status = "cog_package_ready"
    elif all(status in {"cog_package_ready", "cog_package_ready_with_scope_delta"} for status in statuses):
        readiness_status = "cog_package_ready_with_scope_delta"
    elif any(status in {"cog_package_ready", "cog_package_ready_with_scope_delta", "cog_package_poc_ready"} for status in statuses):
        readiness_status = "cog_package_poc_ready"
    else:
        readiness_status = "cog_package_poc_ready"
    return {
        "converted_package_readiness_status": readiness_status,
        "any_converted_package_ready": any_ready,
    }


def summarize_converted_package_layer_inventory(converted_packages: list[dict[str, Any]]) -> str:
    if not converted_packages:
        return "not_provided"
    statuses = {package.get("layer_inventory_status") for package in converted_packages}
    if statuses == {"parity_match"}:
        return "parity_match"
    if statuses == {"scope_reduced"}:
        return "scope_reduced"
    if statuses == {"scope_extended"}:
        return "scope_extended"
    if statuses == {"no_standard_reference"}:
        return "no_standard_reference"
    if "inventory_mismatch" in statuses:
        return "inventory_mismatch"
    if "scope_reduced" in statuses and "scope_extended" not in statuses and "inventory_mismatch" not in statuses:
        return "scope_reduced"
    if "scope_extended" in statuses and "scope_reduced" not in statuses and "inventory_mismatch" not in statuses:
        return "scope_extended"
    return "mixed"


def compare_layer_inventory(
    standard_artifact: dict[str, Any] | None,
    converted_artifact: dict[str, Any],
) -> dict[str, Any]:
    converted_layer_names = list(converted_artifact.get("layer_names", []))
    converted_layer_semantics = list(converted_artifact.get("layer_semantics", []))
    converted_layer_semantics_by_name = {
        str(entry.get("layer_name")): entry
        for entry in converted_layer_semantics
        if isinstance(entry, dict) and entry.get("layer_name")
    }
    if standard_artifact is None:
        return {
            **converted_artifact,
            "layer_inventory_status": "no_standard_reference",
            "standard_layer_count": None,
            "converted_layer_count": len(converted_layer_names),
            "missing_layer_count": 0,
            "missing_layer_names": [],
            "missing_layer_semantics": [],
            "extra_layer_count": 0,
            "extra_layer_names": [],
            "extra_layer_semantics": [],
            "cog_scope": {
                "status": "no_standard_reference",
                "reference_layer_count": None,
                "reference_layer_names": [],
                "exported_layer_count": len(converted_layer_names),
                "exported_layer_names": converted_layer_names,
                "omitted_layer_count": 0,
                "omitted_layer_names": [],
                "extra_layer_count": 0,
                "extra_layer_names": [],
            },
            "scope_delta": {
                "status": "no_standard_reference",
                "missing_layer_count": 0,
                "missing_layer_names": [],
                "extra_layer_count": 0,
                "extra_layer_names": [],
            },
            "inventory_note": "no standard-root reference was available for comparison",
        }

    standard_layer_names = list(standard_artifact.get("layer_names", []))
    standard_layer_semantics = {
        str(entry.get("layer_name")): entry
        for entry in standard_artifact.get("layer_semantics", [])
        if isinstance(entry, dict) and entry.get("layer_name")
    }
    missing_layer_names = [layer_name for layer_name in standard_layer_names if layer_name not in converted_layer_names]
    extra_layer_names = [layer_name for layer_name in converted_layer_names if layer_name not in standard_layer_names]
    if missing_layer_names and extra_layer_names:
        layer_inventory_status = "inventory_mismatch"
        inventory_note = "converted package is missing standard layers and also declares extra layers"
    elif missing_layer_names:
        layer_inventory_status = "scope_reduced"
        inventory_note = "converted package omits standard layers that were not exported in the COG root"
    elif extra_layer_names:
        layer_inventory_status = "scope_extended"
        inventory_note = "converted package declares layers that are not present in the standard root"
    else:
        layer_inventory_status = "parity_match"
        inventory_note = "converted package mirrors the standard root layer inventory"
    if not missing_layer_names and not extra_layer_names:
        cog_scope_status = "full_scope"
    elif missing_layer_names and not extra_layer_names:
        cog_scope_status = "bounded_scope"
    elif extra_layer_names and not missing_layer_names:
        cog_scope_status = "expanded_scope"
    else:
        cog_scope_status = "inventory_mismatch"
    return {
        **converted_artifact,
        "layer_inventory_status": layer_inventory_status,
        "standard_layer_count": len(standard_layer_names),
        "converted_layer_count": len(converted_layer_names),
        "missing_layer_count": len(missing_layer_names),
        "missing_layer_names": missing_layer_names,
        "missing_layer_semantics": [standard_layer_semantics[layer_name] for layer_name in missing_layer_names if layer_name in standard_layer_semantics],
        "extra_layer_count": len(extra_layer_names),
        "extra_layer_names": extra_layer_names,
        "extra_layer_semantics": [converted_layer_semantics_by_name[layer_name] for layer_name in extra_layer_names if layer_name in converted_layer_semantics_by_name],
        "cog_scope": {
            "status": cog_scope_status,
            "reference_layer_count": len(standard_layer_names),
            "reference_layer_names": standard_layer_names,
            "exported_layer_count": len(converted_layer_names),
            "exported_layer_names": converted_layer_names,
            "omitted_layer_count": len(missing_layer_names),
            "omitted_layer_names": missing_layer_names,
            "extra_layer_count": len(extra_layer_names),
            "extra_layer_names": extra_layer_names,
        },
        "scope_delta": {
            "status": "parity_match" if not missing_layer_names and not extra_layer_names else "scope_delta",
            "missing_layer_count": len(missing_layer_names),
            "missing_layer_names": missing_layer_names,
            "extra_layer_count": len(extra_layer_names),
            "extra_layer_names": extra_layer_names,
        },
        "inventory_note": inventory_note,
    }


def normalize_converted_package_status(package: dict[str, Any]) -> dict[str, Any]:
    status = package.get("cog_package_status")
    if status == "cog_package_ready" and package.get("layer_inventory_status") != "parity_match":
        package = dict(package)
        package["cog_package_status"] = "cog_package_ready_with_scope_delta"
    return package


def summarize_standard_package_readiness(artifacts: list[dict[str, Any]]) -> str:
    if not artifacts:
        return "not_provided"
    statuses = [artifact.get("cog_package_status") for artifact in artifacts]
    if any(status == "blocked_missing_inputs" for status in statuses):
        return "blocked_missing_inputs"
    if any(status == "metadata_only" for status in statuses):
        return "metadata_only"
    if all(status == "gis_package_ready" for status in statuses):
        return "gis_package_ready"
    if any(status == "gis_package_ready_cog_blocked" for status in statuses):
        return "gis_package_ready_cog_blocked"
    return "mixed"


def audit_artifact_root(
    root: Path,
    raster_metadata_provider: Callable[[Path], dict[str, Any] | None],
    *,
    verify_all_geotiffs: bool = False,
) -> dict[str, Any]:
    map_manifest_path, map_manifest_missing = discover_single_manifest(root, "*map_package_manifest*.json")
    pilot_manifest_path, pilot_manifest_missing = discover_single_manifest(root, "*pilot_gis_package_manifest*.json")
    map_manifest = load_json(map_manifest_path) if map_manifest_path and map_manifest_path.exists() else {}
    pilot_manifest = load_json(pilot_manifest_path) if pilot_manifest_path and pilot_manifest_path.exists() else {}

    missing_map_fields = missing_fields(map_manifest, REQUIRED_MAP_PACKAGE_FIELDS) if map_manifest else list(REQUIRED_MAP_PACKAGE_FIELDS)
    missing_pilot_fields = missing_fields(pilot_manifest, REQUIRED_PILOT_GIS_FIELDS) if pilot_manifest else list(REQUIRED_PILOT_GIS_FIELDS)

    raster_outputs = list(map_manifest.get("raster_outputs", [])) if map_manifest else []
    missing_raster_outputs = [
        str(resolve_relative_path(root, output.get("path")))
        for output in raster_outputs
        if output.get("path") and not resolve_relative_path(root, output.get("path")).exists()
    ]
    sample_raster = sample_raster_path(root, raster_outputs, pilot_manifest) if (map_manifest and pilot_manifest) else None
    sample_metadata = raster_metadata_provider(sample_raster) if sample_raster is not None else None
    geotiff_checks = audit_declared_geotiffs(root, raster_outputs, raster_metadata_provider) if verify_all_geotiffs else []

    cog_readiness_indicators = summarize_cog_readiness(map_manifest, pilot_manifest, sample_raster, sample_metadata)
    cog_readiness_indicators["declared_geotiff_checks"] = geotiff_checks
    cog_readiness_indicators["declared_geotiff_count"] = sum(1 for output in raster_outputs if output.get("format") == "geotiff")
    if verify_all_geotiffs:
        cog_readiness_indicators["all_declared_geotiffs_cog_ready"] = bool(
            geotiff_checks
            and all(
                check["status"] == "ok"
                and check["sample_raster_cog_layout"]
                and check["sample_raster_tiled"]
                and check["sample_raster_overviews"]
                for check in geotiff_checks
            )
        )
    else:
        cog_readiness_indicators["all_declared_geotiffs_cog_ready"] = (
            cog_readiness_indicators["sample_raster_cog_layout"]
            and cog_readiness_indicators["sample_raster_tiled"]
            and cog_readiness_indicators["sample_raster_overviews"]
        )
    blockers = list(
        summarize_blockers(
            [str(map_manifest_missing)] if map_manifest_missing else [],
            [str(pilot_manifest_missing)] if pilot_manifest_missing else [],
            missing_raster_outputs,
            cog_readiness_indicators,
        )
    )
    if verify_all_geotiffs:
        blockers.extend(declared_geotiff_blockers(geotiff_checks))
    manifest_completeness = {
        "map_package_manifest_complete": bool(map_manifest) and not missing_map_fields,
        "pilot_gis_package_manifest_complete": bool(pilot_manifest) and not missing_pilot_fields,
        "map_package_manifest_missing_fields": missing_map_fields,
        "pilot_gis_package_manifest_missing_fields": missing_pilot_fields,
        "missing_raster_outputs": missing_raster_outputs,
    }

    grid = pilot_manifest.get("grid", {}) if pilot_manifest else {}
    terrain = pilot_manifest.get("terrain", {}) if pilot_manifest else {}
    artifact_id = artifact_id_from_map_manifest(map_manifest, pilot_manifest, root)
    return {
        "artifact_id": artifact_id,
        "artifact_root": str(root),
        "layer_names": [str(output.get("layer_name")) for output in raster_outputs if output.get("layer_name")],
        "layer_semantics": list(map_manifest.get("layer_semantics", [])) if map_manifest else [],
        "cog_package_status": determine_package_status(
            blockers=blockers,
            missing_any=bool(missing_map_fields or missing_pilot_fields or missing_raster_outputs),
            gdal_missing=not cog_readiness_indicators.get("gdalinfo_available", False),
            verify_all_geotiffs=verify_all_geotiffs,
            all_declared_geotiffs_cog_ready=cog_readiness_indicators.get("all_declared_geotiffs_cog_ready", False),
        ),
        "hazard_manifest_path": str(resolve_relative_path(root, first_item(map_manifest.get("hazard_manifest_paths")))) if map_manifest else None,
        "map_package_manifest_path": str(map_manifest_path) if map_manifest_path else None,
        "pilot_gis_package_manifest_path": str(pilot_manifest_path) if pilot_manifest_path else None,
        "raster_layer_count": len(raster_outputs),
        "crs_or_epsg": {
            "terrain_crs": terrain.get("crs"),
            "terrain_epsg": terrain.get("epsg"),
            "sample_raster_epsg": sample_metadata.get("epsg") if sample_metadata else None,
        },
        "grid_dimensions": {
            "ncols": grid.get("ncols"),
            "nrows": grid.get("nrows"),
        },
        "transform_or_cell_size": {
            "cell_size_m": grid.get("cell_size_m"),
            "geo_transform": sample_metadata.get("geo_transform") if sample_metadata else None,
            "block_size": sample_metadata.get("block_size") if sample_metadata else None,
        },
        "nodata_values": {
            "terrain_nodata": terrain.get("nodata"),
            "sample_raster_nodata": sample_metadata.get("nodata") if sample_metadata else None,
        },
        "geotiff_presence": {
            "declared_geotiff_count": sum(1 for output in raster_outputs if output.get("format") == "geotiff"),
            "declared_total_raster_count": len(raster_outputs),
            "all_declared_geotiffs_present": not missing_raster_outputs,
        },
        "cog_readiness_indicators": cog_readiness_indicators,
        "manifest_completeness": manifest_completeness,
        "missing_package_fields": {
            "map_package_manifest": missing_map_fields,
            "pilot_gis_package_manifest": missing_pilot_fields,
        },
        "blockers": blockers,
    }


def audit_declared_geotiffs(
    root: Path,
    raster_outputs: list[dict[str, Any]],
    raster_metadata_provider: Callable[[Path], dict[str, Any] | None],
) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    for output in raster_outputs:
        if output.get("format") != "geotiff":
            continue
        candidate = resolve_relative_path(root, output.get("path"))
        metadata = raster_metadata_provider(candidate) if candidate.exists() else {"status": "missing_inputs"}
        if metadata is None:
            metadata = {"status": "missing_gdal"}
        sample_raster_cog_layout = metadata.get("sample_raster_cog_layout")
        if sample_raster_cog_layout is None:
            sample_raster_cog_layout = metadata.get("image_structure", {}).get("LAYOUT") == "COG"
        sample_raster_tiled = metadata.get("sample_raster_tiled")
        if sample_raster_tiled is None:
            sample_raster_tiled = bool(
                metadata.get("block_size")
                and isinstance(metadata.get("size"), list)
                and len(metadata["size"]) == 2
                and metadata["block_size"][0] < metadata["size"][0]
                and metadata["block_size"][1] < metadata["size"][1]
            )
        sample_raster_overviews = metadata.get("sample_raster_overviews")
        if sample_raster_overviews is None:
            sample_raster_overviews = metadata.get("overview_count", 0) > 0
        check = {
            "layer_name": output.get("layer_name"),
            "path": str(candidate),
            "status": metadata.get("status") if metadata else "missing_inputs",
            "sample_raster_tiled": bool(sample_raster_tiled),
            "sample_raster_overviews": bool(sample_raster_overviews),
            "sample_raster_cog_layout": bool(sample_raster_cog_layout),
        }
        checks.append(check)
    return checks


def declared_geotiff_blockers(geotiff_checks: list[dict[str, Any]]) -> list[str]:
    blockers: list[str] = []
    for check in geotiff_checks:
        if check.get("status") != "ok":
            blockers.append(f"declared_geotiff_unverified:{check.get('layer_name')}")
            continue
        if not check.get("sample_raster_tiled"):
            blockers.append(f"declared_geotiff_not_tiled:{check.get('layer_name')}")
        if not check.get("sample_raster_overviews"):
            blockers.append(f"declared_geotiff_no_overviews:{check.get('layer_name')}")
        if not check.get("sample_raster_cog_layout"):
            blockers.append(f"declared_geotiff_not_cog_layout:{check.get('layer_name')}")
    return blockers


def determine_package_status(
    *,
    blockers: list[str],
    missing_any: bool,
    gdal_missing: bool,
    verify_all_geotiffs: bool,
    all_declared_geotiffs_cog_ready: bool,
) -> str:
    if missing_any:
        return "blocked_missing_inputs"
    if gdal_missing:
        return "metadata_only"
    if verify_all_geotiffs:
        return "cog_package_ready" if all_declared_geotiffs_cog_ready and not blockers else "cog_package_poc_ready"
    return "gis_package_ready" if not blockers else "gis_package_ready_cog_blocked"


def summarize_qgis_status(artifacts: list[dict[str, Any]]) -> str:
    statuses = [artifact.get("cog_readiness_indicators", {}).get("visual_qa_status") for artifact in artifacts]
    if any(status == "not-run" for status in statuses):
        return "not_run"
    if any(status == "not-required" for status in statuses):
        return "not_required"
    return "not_run"


def summarize_blockers(
    missing_map_fields: list[str],
    missing_pilot_fields: list[str],
    missing_raster_outputs: list[str],
    cog_readiness_indicators: dict[str, Any],
) -> list[str]:
    blockers: list[str] = []
    if missing_map_fields:
        blockers.append(f"map_package_manifest_missing_fields:{','.join(missing_map_fields)}")
    if missing_pilot_fields:
        blockers.append(f"pilot_gis_package_manifest_missing_fields:{','.join(missing_pilot_fields)}")
    if missing_raster_outputs:
        blockers.append(f"missing_raster_outputs:{len(missing_raster_outputs)}")
    if not cog_readiness_indicators.get("manifest_cloud_optimized", False):
        blockers.append("manifest_cloud_optimized_false")
    if not cog_readiness_indicators.get("sample_raster_tiled", False):
        blockers.append("sample_raster_not_tiled")
    if not cog_readiness_indicators.get("sample_raster_overviews", False):
        blockers.append("sample_raster_no_overviews")
    return blockers


def summarize_cog_readiness(
    map_manifest: dict[str, Any],
    pilot_manifest: dict[str, Any],
    sample_raster: Path | None,
    sample_metadata: dict[str, Any] | None,
) -> dict[str, Any]:
    raster_outputs = list(map_manifest.get("raster_outputs", []))
    cloud_optimized = sorted({bool(output.get("cloud_optimized")) for output in raster_outputs})
    geotiff_required = bool(pilot_manifest.get("raster_contract", {}).get("geotiff_required", False))
    geotiff_declared = sorted({output.get("format") for output in raster_outputs})
    overviews_present = bool(sample_metadata and sample_metadata.get("overview_count", 0) > 0)
    tiled = bool(
        sample_metadata
        and sample_metadata.get("block_size") not in (None, [])
        and isinstance(sample_metadata.get("size"), list)
        and len(sample_metadata["size"]) == 2
        and sample_metadata["block_size"][0] < sample_metadata["size"][0]
        and sample_metadata["block_size"][1] < sample_metadata["size"][1]
    )
    sample_raster_exists = bool(sample_raster and sample_raster.exists())
    sample_raster_driver = sample_metadata.get("driver") if sample_metadata else None
    sample_raster_epsg = sample_metadata.get("epsg") if sample_metadata else None
    sample_raster_layout = sample_metadata.get("image_structure", {}) if sample_metadata else {}
    sample_raster_compressed = bool(sample_raster_layout.get("COMPRESSION"))
    sample_raster_cog_layout = sample_raster_layout.get("LAYOUT") == "COG"

    sample_status = sample_metadata.get("status") if sample_metadata else None
    return {
        "manifest_cloud_optimized": cloud_optimized == [True],
        "manifest_geotiff_declared": geotiff_required and geotiff_declared == ["geotiff"],
        "sample_raster_exists": sample_raster_exists,
        "sample_raster_driver": sample_metadata.get("driver") if sample_metadata else None,
        "sample_raster_epsg": sample_metadata.get("epsg") if sample_metadata else None,
        "sample_raster_tiled": tiled if sample_status == "ok" else False,
        "sample_raster_overviews": overviews_present if sample_status == "ok" else False,
        "sample_raster_compressed": sample_raster_compressed if sample_status == "ok" else False,
        "sample_raster_cog_layout": sample_raster_cog_layout if sample_status == "ok" else False,
        "sample_raster_block_size": sample_metadata.get("block_size") if sample_metadata else None,
        "sample_raster_geo_transform": sample_metadata.get("geo_transform") if sample_metadata else None,
        "visual_qa_status": pilot_manifest.get("visual_qa", {}).get("status"),
        "gdalinfo_available": sample_status == "ok",
        "sample_raster_status": sample_status or "unknown",
    }


def inspect_raster_metadata(path: Path) -> dict[str, Any] | None:
    if path is None or not path.exists():
        return {"status": "missing_inputs"}
    if shutil.which("gdalinfo") is None:
        return {"status": "missing_gdal", "error": "gdalinfo_not_available"}
    try:
        completed = subprocess.run(
            ["gdalinfo", "-json", str(path)],
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        return {"status": "verification_failed", "error": (exc.stderr or exc.stdout or str(exc)).strip()}
    data = json.loads(completed.stdout)
    band = data.get("bands", [{}])[0]
    metadata = data.get("metadata", {})
    image_structure = metadata.get("IMAGE_STRUCTURE", {})
    wkt = data.get("coordinateSystem", {}).get("wkt", "")
    return {
        "status": "ok",
        "driver": data.get("driverShortName"),
        "size": data.get("size"),
        "epsg": extract_epsg(wkt),
        "geo_transform": data.get("geoTransform"),
        "block_size": band.get("block"),
        "nodata": band.get("noDataValue"),
        "overview_count": len(band.get("overviews", [])),
        "image_structure": image_structure,
    }


def extract_epsg(wkt: str) -> int | None:
    match = re.search(r'AUTHORITY\\[\"EPSG\",\"(\\d+)\"\\]', wkt)
    return int(match.group(1)) if match else None


def discover_single_manifest(root: Path, pattern: str) -> tuple[Path | None, str | None]:
    matches = sorted(root.glob(pattern))
    if not matches:
        return None, f"{root}/{pattern}"
    if len(matches) > 1:
        raise GisCogReadinessError(f"multiple manifests matching {pattern!r} under {root}: {matches}")
    return matches[0], None


def sample_raster_path(
    root: Path,
    raster_outputs: list[dict[str, Any]],
    pilot_manifest: dict[str, Any],
) -> Path | None:
    for output in raster_outputs:
        if output.get("format") == "geotiff":
            candidate = resolve_relative_path(root, output.get("path"))
            if candidate.exists():
                return candidate
    terrain_path = pilot_manifest.get("terrain", {}).get("path")
    if terrain_path:
        candidate = resolve_relative_path(root, terrain_path)
        if candidate.exists():
            return candidate
    return None


def resolve_relative_path(root: Path, maybe_path: str | None) -> Path:
    if maybe_path is None:
        return root
    path = Path(maybe_path)
    return path if path.is_absolute() else ROOT / path


def first_item(values: Any) -> str | None:
    if isinstance(values, list) and values:
        item = values[0]
        return str(item) if item is not None else None
    return None


def load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise GisCogReadinessError(f"failed to read {path}: {exc}") from exc


def missing_fields(data: dict[str, Any], required_fields: tuple[str, ...]) -> list[str]:
    return [field for field in required_fields if field not in data]


def artifact_id_from_map_manifest(map_manifest: dict[str, Any], pilot_manifest: dict[str, Any], root: Path) -> str:
    case_id = pilot_manifest.get("case_id")
    if case_id:
        return str(case_id)
    product_id = map_manifest.get("map_product_id")
    if product_id:
        return str(product_id)
    return root.name


def render_text_report(report: dict[str, Any]) -> str:
    lines = [
        f"GIS/COG readiness: {report['gis_cog_readiness_status']}",
        f"Standard package readiness: {report.get('standard_package_readiness_status')}",
        f"Converted sample: {report['converted_sample_status']}",
        f"Converted package readiness: {report.get('converted_package_readiness_status')}",
        f"Converted package layer inventory: {report.get('converted_package_layer_inventory_status')}",
        f"Any converted package ready: {str(report.get('any_converted_package_ready', False)).lower()}",
        f"Artifacts audited: {report['artifacts_audited']}",
        f"QGIS manual QA: {report['qgis_manual_qa_status']}",
        f"Scientific acceptance: {report['scientific_acceptance_status']}",
    ]
    for artifact in report["artifacts"]:
        lines.append("")
        lines.append(f"- {artifact['artifact_id']}")
        lines.append(f"  root: {artifact['artifact_root']}")
        lines.append(f"  manifest completeness: {artifact['manifest_completeness']}")
        lines.append(f"  CRS/EPSG: {artifact['crs_or_epsg']}")
        lines.append(f"  grid: {artifact['grid_dimensions']}")
        lines.append(f"  transform/cell: {artifact['transform_or_cell_size']}")
        lines.append(f"  nodata: {artifact['nodata_values']}")
        lines.append(f"  geotiff presence: {artifact['geotiff_presence']}")
        lines.append(f"  cog indicators: {artifact['cog_readiness_indicators']}")
        lines.append(f"  blockers: {artifact['blockers']}")
        lines.append(f"  layer count: {artifact['raster_layer_count']}")
    if report.get("converted_packages"):
        for package in report["converted_packages"]:
            lines.append("")
            lines.append(f"* converted {package['artifact_id']}")
            lines.append(f"  root: {package['artifact_root']}")
            lines.append(f"  status: {package['cog_package_status']}")
            lines.append(f"  layer inventory: {package.get('layer_inventory_status')}")
            lines.append(f"  cog scope: {package.get('cog_scope')}")
            lines.append(
                f"  standard/converted layer counts: {package.get('standard_layer_count')}/{package.get('converted_layer_count')}"
            )
            lines.append(f"  scope delta: {package.get('scope_delta')}")
            lines.append(f"  inventory note: {package.get('inventory_note')}")
            lines.append(f"  manifest completeness: {package['manifest_completeness']}")
            lines.append(f"  geotiff presence: {package['geotiff_presence']}")
            lines.append(f"  cog indicators: {package['cog_readiness_indicators']}")
            if package.get("missing_layer_names"):
                lines.append(f"  omitted layers: {', '.join(package['missing_layer_names'])}")
                if package.get("missing_layer_semantics"):
                    lines.append(
                        "  omitted layer semantics: "
                        + "; ".join(
                            f"{entry.get('layer_name')}: {entry.get('numerator')} / {entry.get('denominator')}"
                            for entry in package["missing_layer_semantics"]
                        )
                    )
            if package.get("extra_layer_names"):
                lines.append(f"  extra layers: {', '.join(package['extra_layer_names'])}")
            lines.append(f"  blockers: {package['blockers']}")
    if report.get("converted_sample"):
        lines.append("")
        lines.append(f"converted sample path: {report['converted_sample'].get('path')}")
        lines.append(f"converted sample blockers: {report['converted_sample'].get('blockers')}")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":  # pragma: no cover - CLI entry point.
    raise SystemExit(main())
