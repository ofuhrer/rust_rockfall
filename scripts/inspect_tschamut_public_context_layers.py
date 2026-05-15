#!/usr/bin/env python3
"""Inspect public Tschamut context layers or emit an acquisition checklist.

The inspector is a share-safe diagnostic. It summarizes local context evidence
when present, or reports an explicit blocked state and exact cache/check
paths when context products are absent. It does not download geodata, change
physics, or turn missing data into an inference that obstacles are absent.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import shutil
import sys
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "tschamut_public_context_layers_inspection_v1"
BLOCKED = "blocked_pending_local_evidence"
BLOCKED_REVIEW_STATUS = "blocked_missing_context_layers"
SUPPORTED_CLASSIFICATIONS = {
    "acceptable",
    "limiting",
    "invalidating",
    "unresolved",
}
EXPECTED_LAYER_PATHS = {
    "forest_or_canopy": "swisssurface3d_raster",
    "buildings_or_structures": "swissbuildings3d",
    "roads_or_transport": "swisstlm3d",
    "barriers_or_protection": "swisstlm3d",
    "water_or_channel": "swisstlm3d",
    "orthophoto_visual_context": "swissimage",
}
SWISSTLM3D_CONTEXT_DIR_NAME = "swisstlm3d"
SWISSTLM3D_ARCHIVE_MEMBER_ROOT = "2021_SWISSTLM3D_SHP_CHLV95_LN02"
SWISSTLM3D_CORRIDOR_QUERY_SPEC = {
    "roads_or_transport": [
        {
            "layer_name": "swissTLM3D_TLM_STRASSE",
            "member_path": "TLM_STRASSEN/swissTLM3D_TLM_STRASSE.shp",
        },
        {
            "layer_name": "swissTLM3D_TLM_STRASSENINFO",
            "member_path": "TLM_STRASSEN/swissTLM3D_TLM_STRASSENINFO.shp",
        },
    ],
    "barriers_or_protection": [
        {
            "layer_name": "swissTLM3D_TLM_MAUER",
            "member_path": "TLM_BAUTEN/swissTLM3D_TLM_MAUER.shp",
        },
        {
            "layer_name": "swissTLM3D_TLM_VERBAUUNG",
            "member_path": "TLM_BAUTEN/swissTLM3D_TLM_VERBAUUNG.shp",
        },
        {
            "layer_name": "swissTLM3D_TLM_STAUBAUTE",
            "member_path": "TLM_BAUTEN/swissTLM3D_TLM_STAUBAUTE.shp",
        },
    ],
    "water_or_channel": [
        {
            "layer_name": "swissTLM3D_TLM_FLIESSGEWAESSER",
            "member_path": "TLM_GEWAESSER/swissTLM3D_TLM_FLIESSGEWAESSER.shp",
        },
        {
            "layer_name": "swissTLM3D_TLM_STEHENDES_GEWAESSER",
            "member_path": "TLM_GEWAESSER/swissTLM3D_TLM_STEHENDES_GEWAESSER.shp",
        },
    ],
    "constructed_feature_relevance": [
        {
            "layer_name": "swissTLM3D_TLM_GEBAEUDE_FOOTPRINT",
            "member_path": "TLM_BAUTEN/swissTLM3D_TLM_GEBAEUDE_FOOTPRINT.shp",
        },
        {
            "layer_name": "swissTLM3D_TLM_VERKEHRSBAUTE_LIN",
            "member_path": "TLM_BAUTEN/swissTLM3D_TLM_VERKEHRSBAUTE_LIN.shp",
        },
        {
            "layer_name": "swissTLM3D_TLM_VERKEHRSBAUTE_PLY",
            "member_path": "TLM_BAUTEN/swissTLM3D_TLM_VERKEHRSBAUTE_PLY.shp",
        },
        {
            "layer_name": "swissTLM3D_TLM_VERSORGUNGS_BAUTE_LIN",
            "member_path": "TLM_BAUTEN/swissTLM3D_TLM_VERSORGUNGS_BAUTE_LIN.shp",
        },
        {
            "layer_name": "swissTLM3D_TLM_VERSORGUNGS_BAUTE_PKT",
            "member_path": "TLM_BAUTEN/swissTLM3D_TLM_VERSORGUNGS_BAUTE_PKT.shp",
        },
    ],
}


class ContextLayerInspectionError(ValueError):
    """User-facing context layer inspection error."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--scope-record",
        type=Path,
        default=ROOT / "validation/pilot_runs/tschamut_public_obstacle_scope_v1.yaml",
    )
    parser.add_argument(
        "--datasets-registry",
        type=Path,
        default=ROOT / "data/datasets.yaml",
    )
    parser.add_argument(
        "--context-root",
        type=Path,
        default=ROOT / "data/processed/swisstopo/tschamut_public_pilot/context",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
    )
    args = parser.parse_args(argv)

    try:
        report = inspect_context_layers(
            scope_record_path=args.scope_record,
            datasets_registry_path=args.datasets_registry,
            context_root=args.context_root,
        )
    except ContextLayerInspectionError as exc:
        print(f"context layer inspection error: {exc}", file=sys.stderr)
        return 2

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text_report(report))
    return 0 if report["status"] == "acceptable" else 2


def inspect_context_layers(
    *,
    scope_record_path: Path,
    datasets_registry_path: Path,
    context_root: Path,
) -> dict[str, Any]:
    scope = read_yaml(scope_record_path)
    registry = load_dataset_registry(datasets_registry_path)
    validate_scope_shape(scope)

    selected_extent_or_corridor = build_selected_extent_or_corridor(scope)
    target_review = scope["target_scale_review"]
    evidence = scope["evidence"]
    context_inventory = {item["category"]: item for item in scope["context_inventory"]}
    missing_artifact_paths = list(target_review.get("missing_context_artifact_paths", []))
    reviewed_artifacts = list(target_review.get("reviewed_context_artifact_paths", []))

    layer_reports: list[dict[str, Any]] = []
    for category, slug in EXPECTED_LAYER_PATHS.items():
        item = context_inventory[category]
        expected_path = context_root / slug
        dataset_id = item["dataset_id"]
        dataset = registry.get(dataset_id, {})
        layer_report = inspect_layer(
            category=category,
            dataset_id=dataset_id,
            expected_path=expected_path,
            dataset=dataset,
        )
        layer_reports.append(layer_report)

    adjacent_context_products = [
        summarize_registry_dataset(registry[dataset_id], checked_path=None)
        for dataset_id in ("swisstopo_geocover",)
        if dataset_id in registry
    ]

    overall_classification = determine_overall_classification(layer_reports)
    available_layers = [layer for layer in layer_reports if layer["path_exists"]]
    missing_layers = [layer for layer in layer_reports if not layer["path_exists"]]
    source_products = build_source_products(layer_reports, registry)
    local_cache_paths = build_local_cache_paths(context_root, layer_reports, registry)
    checksums = build_checksum_summary(layer_reports)
    crs_or_spatial_reference = build_crs_summary(layer_reports)
    spatial_relevance_status = determine_spatial_relevance_status(context_root, layer_reports)
    local_context_review_status = determine_local_context_review_status(spatial_relevance_status)
    swisstlm3d_corridor_relevance = inspect_swisstlm3d_corridor_relevance(
        context_root=context_root,
        selected_extent_or_corridor=selected_extent_or_corridor,
        registry=registry,
    )
    blocked_reason = build_blocked_reason(
        context_root=context_root,
        layer_reports=layer_reports,
        spatial_relevance_status=spatial_relevance_status,
    )
    spatial_relevance_indicators = build_spatial_relevance_indicators(
        selected_extent_or_corridor=selected_extent_or_corridor,
        layer_reports=layer_reports,
        context_root=context_root,
    )
    spatial_relevance_indicators["swisstlm3d_archive_status"] = swisstlm3d_corridor_relevance["archive_status"]
    spatial_relevance_indicators["swisstlm3d_queried_layers_count"] = len(swisstlm3d_corridor_relevance["queried_layers"])
    spatial_relevance_indicators["swisstlm3d_intersecting_feature_counts"] = swisstlm3d_corridor_relevance[
        "intersecting_feature_counts"
    ]

    return {
        "schema_version": SCHEMA_VERSION,
        "pilot_id": scope["pilot_id"],
        "run_id": scope["run_id"],
        "scope_record_path": str(scope_record_path),
        "context_root": str(context_root),
        "selected_extent_or_corridor": selected_extent_or_corridor,
        "classification": overall_classification,
        "context_review_status": local_context_review_status,
        "spatial_relevance_status": spatial_relevance_status,
        "swisstlm3d_archive_status": swisstlm3d_corridor_relevance["archive_status"],
        "swisstlm3d_archive_blocked_reason": swisstlm3d_corridor_relevance["blocked_reason"],
        "blocked_reason": blocked_reason,
        "status": overall_classification,
        "final_classification": overall_classification,
        "target_scale_context_review_status": target_review["local_context_review_status"],
        "context_root_present": context_root.exists(),
        "context_layer_count": len(layer_reports),
        "reviewed_context_count": sum(1 for layer in layer_reports if layer["classification"] != "unresolved"),
        "blocked_context_layer_count": sum(1 for layer in layer_reports if not layer["path_exists"]),
        "blocked_missing_context_layers": not any(layer["path_exists"] for layer in layer_reports),
        "layers_expected": layer_reports,
        "layers_available": available_layers,
        "layers_missing": missing_layers,
        "source_products": source_products,
        "local_cache_paths": local_cache_paths,
        "checksums": checksums,
        "crs_or_spatial_reference": crs_or_spatial_reference,
        "spatial_relevance_indicators": spatial_relevance_indicators,
        "queried_layers": swisstlm3d_corridor_relevance["queried_layers"],
        "feature_counts": swisstlm3d_corridor_relevance["feature_counts"],
        "intersecting_feature_counts": swisstlm3d_corridor_relevance["intersecting_feature_counts"],
        "nearest_feature_distances_m": swisstlm3d_corridor_relevance["nearest_feature_distances_m"],
        "roads_or_transport_relevance": swisstlm3d_corridor_relevance["roads_or_transport_relevance"],
        "barriers_or_protection_relevance": swisstlm3d_corridor_relevance["barriers_or_protection_relevance"],
        "water_or_channel_relevance": swisstlm3d_corridor_relevance["water_or_channel_relevance"],
        "constructed_feature_relevance": swisstlm3d_corridor_relevance["constructed_feature_relevance"],
        "interpretation_impact": build_interpretation_impact(scope, layer_reports),
        "operational_claims_allowed": False,
        "expected_context_layers": layer_reports,
        "adjacent_context_products": adjacent_context_products,
        "acquisition_checklist": build_acquisition_checklist(layer_reports, registry, context_root),
        "spatial_relevance_summary": summarize_spatial_relevance(layer_reports),
        "target_scale_review": {
            "status": target_review["local_context_review_status"],
            "reviewed_context_artifact_paths": reviewed_artifacts,
            "missing_context_artifact_paths": missing_artifact_paths,
        },
        "evidence": {
            "reviewed_documents": evidence.get("reviewed_documents", []),
            "required_future_context_downloads": evidence.get("required_future_context_downloads", []),
            "local_artifact_probe": evidence.get("local_artifact_probe", {}),
        },
    }


def validate_scope_shape(scope: dict[str, Any]) -> None:
    if scope.get("schema_version") != "pilot_obstacle_scope_v1":
        raise ContextLayerInspectionError("scope record must use pilot_obstacle_scope_v1")
    if "context_inventory" not in scope or "target_scale_review" not in scope:
        raise ContextLayerInspectionError("scope record is missing required context inspection fields")


def inspect_layer(
    *,
    category: str,
    dataset_id: str,
    expected_path: Path,
    dataset: dict[str, Any],
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "category": category,
        "dataset_id": dataset_id,
        "expected_path": str(expected_path),
        "path_exists": expected_path.exists(),
        "classification": "unresolved",
        "rationale": "no local context evidence found",
        "file_count": 0,
        "total_bytes": 0,
        "combined_sha256": None,
        "files": [],
        "metadata_path": None,
        "metadata": {},
        "source_product": dataset.get("name"),
        "source_url": dataset.get("source_url"),
        "raw_cache_path": dataset.get("local_path"),
        "processed_cache_path": dataset.get("processed_path"),
    }
    if not expected_path.exists():
        result["rationale"] = f"expected context directory is absent: {expected_path}"
        return result

    files = sorted(
        [path for path in expected_path.rglob("*") if path.is_file()],
        key=lambda path: str(path),
    )
    result["file_count"] = len(files)
    result["total_bytes"] = sum(path.stat().st_size for path in files)
    result["files"] = [
        {
            "path": str(path),
            "size_bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
        for path in files
    ]
    result["combined_sha256"] = sha256_text("\n".join(entry["sha256"] for entry in result["files"]))

    metadata_path = find_metadata_path(files)
    if metadata_path is not None:
        result["metadata_path"] = str(metadata_path)
        metadata = read_metadata(metadata_path)
        result["metadata"] = extract_metadata_summary(metadata)
        classification = metadata.get("review_classification") or metadata.get("classification")
        if classification in SUPPORTED_CLASSIFICATIONS:
            result["classification"] = str(classification)
            result["rationale"] = metadata.get(
                "inspection_rationale",
                metadata.get("spatial_relevance", "classification supplied by local metadata"),
            )
        else:
            result["rationale"] = "context files are present but no explicit review classification was supplied"
    else:
        result["rationale"] = "context directory is present but no metadata sidecar was found"

    return result


def inspect_swisstlm3d_corridor_relevance(
    *,
    context_root: Path,
    selected_extent_or_corridor: dict[str, Any],
    registry: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    archive_context_root = context_root / SWISSTLM3D_CONTEXT_DIR_NAME
    metadata_path = archive_context_root / "metadata.json"
    archive_summary: dict[str, Any] = {
        "archive_status": BLOCKED,
        "blocked_reason": None,
        "metadata_path": str(metadata_path),
        "archive_path": None,
        "archive_sha256": None,
        "archive_size_bytes": None,
        "coordinate_reference_system": None,
        "source_product": "swissTLM3D",
        "source_url": registry.get("swisstopo_swisstlm3d", {}).get("source_url"),
        "queried_layers": [],
        "feature_counts": {},
        "intersecting_feature_counts": {},
        "nearest_feature_distances_m": {},
        "roads_or_transport_relevance": {
            "classification": "unresolved",
            "queried_layers": [],
            "feature_count": 0,
            "intersecting_feature_count": 0,
            "nearest_feature_distance_m": None,
        },
        "barriers_or_protection_relevance": {
            "classification": "unresolved",
            "queried_layers": [],
            "feature_count": 0,
            "intersecting_feature_count": 0,
            "nearest_feature_distance_m": None,
        },
        "water_or_channel_relevance": {
            "classification": "unresolved",
            "queried_layers": [],
            "feature_count": 0,
            "intersecting_feature_count": 0,
            "nearest_feature_distance_m": None,
        },
        "constructed_feature_relevance": {
            "classification": "unresolved",
            "queried_layers": [],
            "feature_count": 0,
            "intersecting_feature_count": 0,
            "nearest_feature_distance_m": None,
        },
    }
    if not metadata_path.exists():
        archive_summary["blocked_reason"] = f"staged swissTLM3D metadata is absent at {metadata_path}"
        return archive_summary

    metadata = read_metadata(metadata_path)
    try:
        archive_path = resolve_archive_path(metadata, root=ROOT)
    except ContextLayerInspectionError as exc:
        archive_summary["blocked_reason"] = str(exc)
        return archive_summary
    archive_summary["archive_path"] = str(archive_path)
    archive_summary["archive_sha256"] = metadata.get("local_asset_sha256") or metadata.get("raw_asset_sha256")
    archive_summary["archive_size_bytes"] = metadata.get("local_asset_bytes") or metadata.get("raw_asset_head_content_length_bytes")
    archive_summary["coordinate_reference_system"] = metadata.get("coordinate_reference_system")
    if not archive_path.exists():
        archive_summary["blocked_reason"] = f"staged swissTLM3D archive is absent at {archive_path}"
        return archive_summary

    bbox = selected_extent_or_corridor.get("extent_lv95_m") or {}
    required_bbox_keys = ("xmin", "ymin", "xmax", "ymax")
    if any(key not in bbox for key in required_bbox_keys):
        archive_summary["blocked_reason"] = "selected extent/corridor is missing LV95 bounds"
        return archive_summary

    ogrinfo = shutil.which("ogrinfo")
    if ogrinfo is None:
        archive_summary["blocked_reason"] = "ogrinfo is unavailable in the current environment"
        return archive_summary

    layer_results: list[dict[str, Any]] = []
    for category, specs in SWISSTLM3D_CORRIDOR_QUERY_SPEC.items():
        category_layer_results: list[dict[str, Any]] = []
        for spec in specs:
            layer_result = query_swisstlm3d_layer_count(
                ogrinfo=ogrinfo,
                archive_path=archive_path,
                layer_name=spec["layer_name"],
                member_path=spec["member_path"],
                bbox=bbox,
                category=category,
            )
            if layer_result.get("status") != "ok":
                archive_summary["blocked_reason"] = layer_result.get("blocked_reason") or "failed to query swissTLM3D archive"
                return archive_summary
            category_layer_results.append(layer_result)
            layer_results.append(layer_result)

        total_count = sum(item["intersecting_feature_count"] for item in category_layer_results)
        category_nearest = 0.0 if total_count > 0 else None
        classification = "limiting" if total_count > 0 else "unresolved"
        archive_summary[category + "_relevance"] = {
            "classification": classification,
            "queried_layers": [
                {
                    "layer_name": item["layer_name"],
                    "member_path": item["member_path"],
                    "intersecting_feature_count": item["intersecting_feature_count"],
                    "nearest_feature_distance_m": item["nearest_feature_distance_m"],
                }
                for item in category_layer_results
            ],
            "feature_count": total_count,
            "intersecting_feature_count": total_count,
            "nearest_feature_distance_m": category_nearest,
        }
        archive_summary["feature_counts"][category] = {
            "by_layer": {
                item["layer_name"]: item["intersecting_feature_count"] for item in category_layer_results
            },
            "total_intersecting_feature_count": total_count,
        }
        archive_summary["intersecting_feature_counts"][category] = total_count
        archive_summary["nearest_feature_distances_m"][category] = category_nearest

    archive_summary["queried_layers"] = layer_results
    archive_summary["archive_status"] = "measured_corridor_relevance"
    return archive_summary


def resolve_archive_path(metadata: dict[str, Any], *, root: Path) -> Path:
    for key in ("local_asset_path", "raw_asset_path"):
        value = metadata.get(key)
        if isinstance(value, str) and value:
            path = Path(value)
            return path if path.is_absolute() else root / path
    raise ContextLayerInspectionError("swissTLM3D metadata is missing an archive path")


def query_swisstlm3d_layer_count(
    *,
    ogrinfo: str,
    archive_path: Path,
    layer_name: str,
    member_path: str,
    bbox: dict[str, Any],
    category: str,
) -> dict[str, Any]:
    datasource_path = f"/vsizip/{archive_path}/{SWISSTLM3D_ARCHIVE_MEMBER_ROOT}/{member_path}"
    return query_vector_layer_count(
        ogrinfo=ogrinfo,
        datasource_path=datasource_path,
        layer_name=layer_name,
        bbox=bbox,
        category=category,
        member_path=member_path,
    )


def query_vector_layer_count(
    *,
    ogrinfo: str,
    datasource_path: str,
    layer_name: str,
    bbox: dict[str, Any],
    category: str,
    member_path: str | None = None,
) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            [
                ogrinfo,
                "-ro",
                "-q",
                "-geom=NO",
                "-al",
                "-spat",
                str(bbox["xmin"]),
                str(bbox["ymin"]),
                str(bbox["xmax"]),
                str(bbox["ymax"]),
                datasource_path,
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=180,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "status": "blocked",
            "blocked_reason": f"swissTLM3D query timed out for {layer_name}: {exc}",
            "category": category,
            "layer_name": layer_name,
            "member_path": member_path,
            "datasource_path": datasource_path,
        }
    except subprocess.CalledProcessError as exc:
        return {
            "status": "blocked",
            "blocked_reason": f"swissTLM3D query failed for {layer_name}: {exc.stderr or exc.stdout or exc}",
            "category": category,
            "layer_name": layer_name,
            "member_path": member_path,
            "datasource_path": datasource_path,
        }
    intersecting_feature_count = completed.stdout.count("OGRFeature(")
    return {
        "status": "ok",
        "category": category,
        "layer_name": layer_name,
        "member_path": member_path,
        "datasource_path": datasource_path,
        "intersecting_feature_count": intersecting_feature_count,
        "nearest_feature_distance_m": 0.0 if intersecting_feature_count > 0 else None,
    }


def determine_overall_classification(layer_reports: list[dict[str, Any]]) -> str:
    if any(not layer["path_exists"] for layer in layer_reports):
        return BLOCKED
    classifications = [layer["classification"] for layer in layer_reports]
    if "invalidating" in classifications:
        return "invalidating"
    if "limiting" in classifications:
        return "limiting"
    if all(classification == "acceptable" for classification in classifications):
        return "acceptable"
    return "unresolved"


def build_acquisition_checklist(
    layer_reports: list[dict[str, Any]],
    registry: dict[str, dict[str, Any]],
    context_root: Path,
) -> list[dict[str, Any]]:
    checklist = []
    for layer in layer_reports:
        if layer["path_exists"]:
            continue
        dataset = registry.get(layer["dataset_id"], {})
        checklist.append(
            {
                "category": layer["category"],
                "dataset_id": layer["dataset_id"],
                "source_product": dataset.get("name"),
                "source_url": dataset.get("source_url"),
                "raw_cache_path": dataset.get("local_path"),
                "processed_cache_path": str(Path(layer["expected_path"])),
                "staging_commands": [
                    f"mkdir -p {dataset.get('local_path')}",
                    f"mkdir -p {layer['expected_path']}",
                ],
                "verification_commands": [
                    "UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/validate_pilot_obstacle_scope.py validation/pilot_runs/tschamut_public_obstacle_scope_v1.yaml",
                    "UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/inspect_tschamut_public_context_layers.py --format json",
                ],
            }
        )
    if any(not layer["path_exists"] for layer in layer_reports):
        checklist.append(
            {
                "category": "adjacent_context",
                "dataset_id": "swisstopo_geocover",
                "source_product": "GeoCover geological 2D models",
                "source_url": registry.get("swisstopo_geocover", {}).get("source_url"),
                "raw_cache_path": registry.get("swisstopo_geocover", {}).get("local_path"),
                "processed_cache_path": str(context_root / "geocover"),
                "note": "adjacent geology/material context is optional for obstacle omission review but useful for future release-zone interpretation",
            }
        )
    return checklist


def build_source_products(
    layer_reports: list[dict[str, Any]],
    registry: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    products: dict[tuple[str | None, str | None], dict[str, Any]] = {}
    for layer in layer_reports:
        dataset = registry.get(layer["dataset_id"], {})
        key = (dataset.get("id"), dataset.get("name"))
        product = products.setdefault(
            key,
            {
                "dataset_id": dataset.get("id", layer["dataset_id"]),
                "source_product": dataset.get("name"),
                "source_url": dataset.get("source_url"),
                "raw_cache_path": dataset.get("local_path"),
                "processed_cache_path": str(Path(layer["expected_path"])),
                "layer_categories": [],
            },
        )
        product["layer_categories"].append(layer["category"])
    return sorted(products.values(), key=lambda item: (str(item["source_product"]), str(item["dataset_id"])))


def build_local_cache_paths(
    context_root: Path,
    layer_reports: list[dict[str, Any]],
    registry: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    raw_cache_paths = sorted(
        {
            str(registry.get(layer["dataset_id"], {}).get("local_path"))
            for layer in layer_reports
            if registry.get(layer["dataset_id"], {}).get("local_path")
        }
    )
    processed_cache_paths = sorted({str(Path(layer["expected_path"])) for layer in layer_reports})
    return {
        "context_root": str(context_root),
        "context_root_present": context_root.exists(),
        "raw_cache_paths": raw_cache_paths,
        "processed_cache_paths": processed_cache_paths,
        "available_layer_paths": sorted({layer["expected_path"] for layer in layer_reports if layer["path_exists"]}),
        "missing_layer_paths": sorted({layer["expected_path"] for layer in layer_reports if not layer["path_exists"]}),
    }


def build_checksum_summary(layer_reports: list[dict[str, Any]]) -> dict[str, Any]:
    available_layers = [layer for layer in layer_reports if layer["path_exists"]]
    return {
        "available_layers": [
            {
                "category": layer["category"],
                "dataset_id": layer["dataset_id"],
                "metadata_path": layer["metadata_path"],
                "combined_sha256": layer["combined_sha256"],
                "file_count": layer["file_count"],
                "total_bytes": layer["total_bytes"],
                "file_sha256s": [entry["sha256"] for entry in layer["files"]],
            }
            for layer in available_layers
        ],
        "available_files": [
            {
                "category": layer["category"],
                "path": entry["path"],
                "size_bytes": entry["size_bytes"],
                "sha256": entry["sha256"],
            }
            for layer in available_layers
            for entry in layer["files"]
        ],
    }


def build_crs_summary(layer_reports: list[dict[str, Any]]) -> list[dict[str, Any]]:
    crs_summary: list[dict[str, Any]] = []
    for layer in layer_reports:
        metadata = layer.get("metadata") or {}
        crs = metadata.get("coordinate_reference_system")
        if isinstance(crs, dict):
            crs_summary.append(
                {
                    "category": layer["category"],
                    "dataset_id": layer["dataset_id"],
                    "metadata_path": layer["metadata_path"],
                    "coordinate_reference_system": crs,
                }
            )
    return crs_summary


def build_interpretation_impact(scope: dict[str, Any], layer_reports: list[dict[str, Any]]) -> dict[str, Any]:
    omission = scope.get("omission_interpretation", {})
    return {
        "summary": omission.get("summary"),
        "required_before_interpretation": omission.get("required_before_interpretation"),
        "current_effect": (
            "Local context review remains conditional; the staged swissTLM3D archive now "
            "provides corridor-level counts for roads, water, and barrier/protection features, "
            "but that remains interpretation evidence rather than obstacle physics."
        ),
        "layer_classification_summary": summarize_spatial_relevance(layer_reports),
        "operational_claims_allowed": False,
    }


def build_selected_extent_or_corridor(scope: dict[str, Any]) -> dict[str, Any]:
    selected_domain = scope.get("selected_domain") or {}
    if not selected_domain:
        pilot_manifest_path = ROOT / "data/processed/swisstopo/tschamut_public_pilot_manifest.yaml"
        if pilot_manifest_path.exists():
            pilot_manifest = read_yaml(pilot_manifest_path)
            selected_domain = pilot_manifest.get("selected_domain") or {}
    extent = selected_domain.get("extent_lv95_m") or {}
    crs = selected_domain.get("coordinate_reference_system") or {}
    return {
        "name": selected_domain.get("name"),
        "purpose": selected_domain.get("purpose"),
        "selection_status": selected_domain.get("selection_status"),
        "extent_lv95_m": extent,
        "coordinate_reference_system": crs,
        "source_zone_status": selected_domain.get("source_zone_status"),
        "forest_obstacle_relevance_status": selected_domain.get("forest_obstacle_relevance_status"),
    }


def determine_spatial_relevance_status(context_root: Path, layer_reports: list[dict[str, Any]]) -> str:
    if not context_root.exists():
        return BLOCKED
    if any(not layer["path_exists"] for layer in layer_reports):
        return "blocked_missing_context_layers"
    fixture_root = ROOT / "tests/fixtures/tschamut_context_layers/available"
    if context_root.resolve() == fixture_root.resolve():
        return "fixture_reviewed_context"
    return "reviewed_local_context"


def determine_local_context_review_status(spatial_relevance_status: str) -> str:
    if spatial_relevance_status == BLOCKED:
        return BLOCKED_REVIEW_STATUS
    return spatial_relevance_status


def build_blocked_reason(
    *,
    context_root: Path,
    layer_reports: list[dict[str, Any]],
    spatial_relevance_status: str,
) -> str | None:
    if spatial_relevance_status not in {BLOCKED, "blocked_missing_context_layers"}:
        return None
    if not context_root.exists():
        return f"real processed Tschamut context crops are absent from {context_root}"
    missing_categories = [layer["category"] for layer in layer_reports if not layer["path_exists"]]
    if missing_categories:
        return (
            "processed context crops are incomplete for categories: "
            + ", ".join(missing_categories)
        )
    return "context review remains blocked pending local evidence"


def build_spatial_relevance_indicators(
    *,
    selected_extent_or_corridor: dict[str, Any],
    layer_reports: list[dict[str, Any]],
    context_root: Path,
) -> dict[str, Any]:
    summary = summarize_spatial_relevance(layer_reports)
    available_layers = [layer for layer in layer_reports if layer["path_exists"]]
    selected_epsg = (selected_extent_or_corridor.get("coordinate_reference_system") or {}).get("epsg")
    reviewed_epsg_values = sorted(
        {
            epsg
            for layer in available_layers
            for epsg in [
                (layer.get("metadata") or {}).get("coordinate_reference_system", {}).get("epsg")
                if isinstance((layer.get("metadata") or {}).get("coordinate_reference_system"), dict)
                else None
            ]
            if isinstance(epsg, int)
        }
    )
    crs_match = bool(available_layers) and all(
        (layer.get("metadata") or {}).get("coordinate_reference_system", {}).get("epsg") == selected_epsg
        for layer in available_layers
        if isinstance((layer.get("metadata") or {}).get("coordinate_reference_system"), dict)
    )
    return {
        "context_root_present": context_root.exists(),
        "selected_extent_or_corridor": selected_extent_or_corridor,
        "available_layer_count": len(available_layers),
        "missing_layer_count": sum(1 for layer in layer_reports if not layer["path_exists"]),
        "reviewed_layer_count": sum(1 for layer in layer_reports if layer["classification"] != "unresolved"),
        "classification_summary": summary,
        "reviewed_categories": [layer["category"] for layer in available_layers],
        "missing_categories": [layer["category"] for layer in layer_reports if not layer["path_exists"]],
        "relevant_product_categories": {
            "forest_or_canopy": "swisssurface3d_raster",
            "buildings_or_structures": "swissbuildings3d",
            "roads_or_transport": "swisstlm3d",
            "barriers_or_protection": "swisstlm3d",
            "water_or_channel": "swisstlm3d",
            "orthophoto_visual_context": "swissimage",
        },
        "per_layer_metadata_indicators": build_per_layer_metadata_indicators(available_layers),
        "surface_minus_bare_earth": build_surface_minus_bare_earth_summary(available_layers),
        "spatial_extent_alignment": {
            "selected_epsg": selected_epsg,
            "reviewed_epsg_values": reviewed_epsg_values,
            "all_reviewed_layers_share_selected_epsg": crs_match,
        },
    }


def build_per_layer_metadata_indicators(layer_reports: list[dict[str, Any]]) -> list[dict[str, Any]]:
    indicators: list[dict[str, Any]] = []
    for layer in layer_reports:
        metadata = layer.get("metadata") or {}
        indicators.append(
            {
                "category": layer["category"],
                "classification": layer["classification"],
                "source_product": metadata.get("source_product") or layer.get("source_product"),
                "source_tile_ids": metadata.get("source_tile_ids"),
                "spatial_relevance": metadata.get("spatial_relevance"),
                "local_asset_path": metadata.get("local_asset_path"),
                "local_asset_bytes": metadata.get("local_asset_bytes"),
                "raw_asset_downloaded": metadata.get("raw_asset_downloaded"),
                "raw_asset_head_content_length_bytes": metadata.get("raw_asset_head_content_length_bytes"),
                "spatial_relevance_indicators": metadata.get("spatial_relevance_indicators"),
            }
        )
    return indicators


def build_surface_minus_bare_earth_summary(layer_reports: list[dict[str, Any]]) -> dict[str, Any] | None:
    for layer in layer_reports:
        metadata = layer.get("metadata") or {}
        indicators = metadata.get("spatial_relevance_indicators")
        if layer["category"] == "forest_or_canopy" and isinstance(indicators, dict):
            return indicators
    return None


def summarize_spatial_relevance(layer_reports: list[dict[str, Any]]) -> dict[str, Any]:
    summary = {
        "acceptable": [],
        "limiting": [],
        "invalidating": [],
        "unresolved": [],
    }
    for layer in layer_reports:
        summary[layer["classification"]].append(layer["category"])
    return summary


def summarize_registry_dataset(dataset: dict[str, Any], checked_path: Path | None) -> dict[str, Any]:
    summary = {
        "dataset_id": dataset.get("id"),
        "source_product": dataset.get("name"),
        "source_url": dataset.get("source_url"),
        "local_path": dataset.get("local_path"),
        "processed_path": dataset.get("processed_path"),
        "checked_path": str(checked_path) if checked_path is not None else None,
    }
    if checked_path is not None and checked_path.exists():
        summary["path_exists"] = True
    return summary


def load_dataset_registry(path: Path) -> dict[str, dict[str, Any]]:
    registry = read_yaml(path)
    datasets = registry.get("datasets")
    if not isinstance(datasets, list):
        raise ContextLayerInspectionError("dataset registry must contain a datasets list")
    return {
        str(dataset.get("id")): dataset
        for dataset in datasets
        if isinstance(dataset, dict) and dataset.get("id")
    }


def read_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - path context matters.
        raise ContextLayerInspectionError(f"failed to read YAML {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ContextLayerInspectionError(f"YAML document must be a mapping: {path}")
    return data


def read_metadata(path: Path) -> dict[str, Any]:
    if path.suffix.lower() == ".json":
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001 - path context matters.
            raise ContextLayerInspectionError(f"failed to read JSON metadata {path}: {exc}") from exc
    else:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ContextLayerInspectionError(f"metadata must be a mapping: {path}")
    return data


def extract_metadata_summary(metadata: dict[str, Any]) -> dict[str, Any]:
    interesting_keys = (
        "review_classification",
        "classification",
        "inspection_rationale",
        "spatial_relevance",
        "source_product",
        "source_url",
        "source_tile_ids",
        "coordinate_reference_system",
        "vertical_datum",
        "source_tile_id",
        "source_filename",
        "license",
        "processed_sha256",
        "raw_sha256",
        "local_asset_path",
        "local_asset_bytes",
        "local_asset_sha256",
        "raw_asset_downloaded",
        "raw_asset_head_content_length_bytes",
        "selected_extent_lv95_m",
        "spatial_relevance_indicators",
    )
    summary = {key: metadata.get(key) for key in interesting_keys if key in metadata}
    return summary


def find_metadata_path(files: list[Path]) -> Path | None:
    for path in files:
        if path.name.lower().endswith((".json", ".yaml", ".yml")) and "metadata" in path.name.lower():
            return path
    for path in files:
        if path.name.lower().endswith((".json", ".yaml", ".yml")):
            return path
    return None


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def render_text_report(report: dict[str, Any]) -> str:
    lines = [
        f"context inspection status: {report['classification']}",
        f"final classification: {report.get('final_classification')}",
        f"context review status: {report['context_review_status']}",
        f"spatial relevance status: {report['spatial_relevance_status']}",
        f"swisstlm3d archive status: {report.get('swisstlm3d_archive_status')}",
        f"blocked reason: {report['blocked_reason']}",
        f"scope record: {report['scope_record_path']}",
        f"context root: {report['context_root']}",
        f"selected extent/corridor: {report['selected_extent_or_corridor']['name']}",
        f"target-scale context review: {report['target_scale_context_review_status']}",
        f"context layers inspected: {report['context_layer_count']}",
        f"blocked missing layers: {report['blocked_context_layer_count']}",
        f"operational claims allowed: {report['operational_claims_allowed']}",
    ]
    for layer in report["layers_expected"]:
        lines.append(
            f"- {layer['category']} [{layer['classification']}]: {layer['expected_path']} "
            f"(files={layer['file_count']}, bytes={layer['total_bytes']})"
        )
        lines.append(f"  rationale: {layer['rationale']}")
    if report["source_products"]:
        lines.append("source products:")
        for product in report["source_products"]:
            lines.append(f"- {product['source_product']}: {product['processed_cache_path']}")
    indicators = report.get("spatial_relevance_indicators") or {}
    if indicators:
        lines.append("spatial relevance indicators:")
        lines.append(
            f"- available={indicators.get('available_layer_count', 0)}, "
            f"missing={indicators.get('missing_layer_count', 0)}, "
            f"crs_match={indicators.get('spatial_extent_alignment', {}).get('all_reviewed_layers_share_selected_epsg', False)}, "
            f"swisstlm3d_archive_status={indicators.get('swisstlm3d_archive_status')}"
        )
    queried_layers = report.get("queried_layers") or []
    if queried_layers:
        lines.append("swisstlm3d corridor query:")
        for item in queried_layers:
            lines.append(
                f"- {item['category']}::{item['layer_name']}: "
                f"intersections={item['intersecting_feature_count']}, "
                f"nearest_m={item['nearest_feature_distance_m']}"
            )
    archive_blocked_reason = report.get("swisstlm3d_archive_blocked_reason")
    if archive_blocked_reason:
        lines.append(f"swisstlm3d blocked reason: {archive_blocked_reason}")
    if report["acquisition_checklist"]:
        lines.append("acquisition checklist:")
        for item in report["acquisition_checklist"]:
            lines.append(f"- {item['dataset_id']}: {item['processed_cache_path']}")
            if "source_url" in item and item["source_url"]:
                lines.append(f"  source: {item['source_url']}")
            if item.get("staging_commands"):
                lines.append(f"  staging: {item['staging_commands'][0]}")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
