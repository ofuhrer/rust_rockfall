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
    args = parser.parse_args(argv)

    try:
        report = build_gis_cog_readiness_report(
            artifact_roots=args.artifact_roots,
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
    raster_metadata_provider: Callable[[Path], dict[str, Any] | None] | None = None,
) -> dict[str, Any]:
    roots = [Path(root) for root in (artifact_roots or DEFAULT_ARTIFACT_ROOTS)]
    provider = raster_metadata_provider or inspect_raster_metadata
    artifacts = [audit_artifact_root(root, provider) for root in roots]

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

    report = {
        "schema_version": SCHEMA_VERSION,
        "gis_cog_readiness_status": gis_status,
        "readiness_status": gis_status,
        "artifacts_audited": len(artifacts),
        "artifact_roots": [str(artifact["artifact_root"]) for artifact in artifacts],
        "hazard_manifest_paths": {artifact["artifact_id"]: artifact["hazard_manifest_path"] for artifact in artifacts},
        "map_package_manifest_paths": {artifact["artifact_id"]: artifact["map_package_manifest_path"] for artifact in artifacts},
        "pilot_gis_package_manifest_paths": {
            artifact["artifact_id"]: artifact["pilot_gis_package_manifest_path"] for artifact in artifacts
        },
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


def audit_artifact_root(
    root: Path,
    raster_metadata_provider: Callable[[Path], dict[str, Any] | None],
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

    cog_readiness_indicators = summarize_cog_readiness(map_manifest, pilot_manifest, sample_raster, sample_metadata)
    blockers = list(
        summarize_blockers(
            [str(map_manifest_missing)] if map_manifest_missing else [],
            [str(pilot_manifest_missing)] if pilot_manifest_missing else [],
            missing_raster_outputs,
            cog_readiness_indicators,
        )
    )
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

    return {
        "manifest_cloud_optimized": cloud_optimized == [True],
        "manifest_geotiff_declared": geotiff_required and geotiff_declared == ["geotiff"],
        "sample_raster_exists": sample_raster_exists,
        "sample_raster_driver": sample_raster_driver,
        "sample_raster_epsg": sample_raster_epsg,
        "sample_raster_tiled": tiled,
        "sample_raster_overviews": overviews_present,
        "sample_raster_compressed": sample_raster_compressed,
        "sample_raster_cog_layout": sample_raster_cog_layout,
        "sample_raster_block_size": sample_metadata.get("block_size") if sample_metadata else None,
        "sample_raster_geo_transform": sample_metadata.get("geo_transform") if sample_metadata else None,
        "visual_qa_status": pilot_manifest.get("visual_qa", {}).get("status"),
        "gdalinfo_available": sample_metadata is not None,
    }


def inspect_raster_metadata(path: Path) -> dict[str, Any] | None:
    if path is None or not path.exists():
        return None
    try:
        completed = subprocess.run(
            ["gdalinfo", "-json", str(path)],
            capture_output=True,
            text=True,
            check=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    data = json.loads(completed.stdout)
    band = data.get("bands", [{}])[0]
    metadata = data.get("metadata", {})
    image_structure = metadata.get("IMAGE_STRUCTURE", {})
    wkt = data.get("coordinateSystem", {}).get("wkt", "")
    return {
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
    return "\n".join(lines) + "\n"


if __name__ == "__main__":  # pragma: no cover - CLI entry point.
    raise SystemExit(main())
