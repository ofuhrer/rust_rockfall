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

    return {
        "schema_version": SCHEMA_VERSION,
        "pilot_id": scope["pilot_id"],
        "run_id": scope["run_id"],
        "scope_record_path": str(scope_record_path),
        "context_root": str(context_root),
        "classification": overall_classification,
        "context_review_status": target_review["local_context_review_status"],
        "status": overall_classification,
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
        "current_effect": "Local context review remains blocked when no reviewed processed cache is staged in the checkout.",
        "layer_classification_summary": summarize_spatial_relevance(layer_reports),
        "operational_claims_allowed": False,
    }


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
        f"context review status: {report['context_review_status']}",
        f"scope record: {report['scope_record_path']}",
        f"context root: {report['context_root']}",
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
