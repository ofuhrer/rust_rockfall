#!/usr/bin/env python3
"""Validate and record locally staged public swisstopo inputs against a cache manifest.

This helper is a local staging front door. It does not download public
geodata, infer missing tiles, or authorize any operational workflow. Instead,
it reads the cache-manifest template, validates the locally supplied staged
paths and metadata sidecars, records deterministic checksums and provenance
fields, and rewrites the manifest in place.
"""

from __future__ import annotations

import argparse
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
PREFLIGHT_SCRIPT = ROOT / "scripts" / "check_second_site_public_geodata_preflight.py"
STAGED_PRODUCT_CATEGORIES = {
    "terrain_crop",
    "swissimage_context",
    "swisstlm3d_context",
    "swisssurface3d_context",
    "swisssurface3d_raster_context",
    "swissbuildings3d_context",
    "barrier_inventory",
}


def _load_preflight_module():
    spec = importlib.util.spec_from_file_location("public_geodata_cache_stage_preflight", PREFLIGHT_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load preflight helper from {PREFLIGHT_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


PREFLIGHT = _load_preflight_module()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-manifest", type=Path, required=True)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    args = parser.parse_args(argv)

    report = stage_public_geodata_cache(args.cache_manifest)

    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    output = json.dumps(report, indent=2, sort_keys=True) if args.format == "json" else render_text_report(report)
    print(output)
    return 0 if report["staging_status"] == "verified" else 2


def stage_public_geodata_cache(cache_manifest_path: Path) -> dict[str, Any]:
    if not cache_manifest_path.exists():
        raise SystemExit(f"missing cache manifest: {cache_manifest_path}")
    manifest = PREFLIGHT.load_site_config(cache_manifest_path)
    if not isinstance(manifest, dict):
        manifest = {}
    products = manifest.get("products") or []
    staged_products: list[dict[str, Any]] = []
    overall_status = "verified"
    for record in products:
        if not isinstance(record, dict):
            continue
        staged_product = stage_public_geodata_cache_product(record, cache_manifest_path.parent)
        staged_products.append(staged_product)
        status = PREFLIGHT.text_value(staged_product.get("staging_status")) or "missing"
        if status == "optional_missing":
            continue
        if status == "unsupported_product":
            overall_status = status
            continue
        if status == "missing" and overall_status == "verified":
            overall_status = status
        elif status == "checksum_mismatch" and overall_status == "verified":
            overall_status = status
        elif status == "metadata_mismatch" and overall_status == "verified":
            overall_status = status

    staged_count = sum(1 for entry in staged_products if entry.get("staging_status") == "verified")
    optional_missing_count = sum(1 for entry in staged_products if entry.get("staging_status") == "optional_missing")
    missing_count = sum(1 for entry in staged_products if entry.get("staging_status") == "missing")
    checksum_mismatch_count = sum(1 for entry in staged_products if entry.get("staging_status") == "checksum_mismatch")
    metadata_mismatch_count = sum(1 for entry in staged_products if entry.get("staging_status") == "metadata_mismatch")
    unsupported_count = sum(1 for entry in staged_products if entry.get("staging_status") == "unsupported_product")

    staged_manifest = {
        **manifest,
        "schema_version": manifest.get("schema_version") or PREFLIGHT.PUBLIC_GEODATA_CACHE_TEMPLATE_SCHEMA_VERSION,
        "staging_status": overall_status,
        "cache_manifest_path": str(cache_manifest_path),
        "staged_product_count": staged_count,
        "optional_missing_product_count": optional_missing_count,
        "missing_product_count": missing_count,
        "checksum_mismatch_product_count": checksum_mismatch_count,
        "metadata_mismatch_product_count": metadata_mismatch_count,
        "unsupported_product_count": unsupported_count,
        "products": staged_products,
    }
    cache_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    cache_manifest_path.write_text(yaml.safe_dump(staged_manifest, sort_keys=False), encoding="utf-8")

    return {
        "schema_version": "swiss_public_geodata_cache_staging_report_v1",
        "staging_status": overall_status,
        "cache_manifest_path": str(cache_manifest_path),
        "product_count": len(staged_products),
        "staged_product_count": staged_count,
        "optional_missing_product_count": optional_missing_count,
        "missing_product_count": missing_count,
        "checksum_mismatch_product_count": checksum_mismatch_count,
        "metadata_mismatch_product_count": metadata_mismatch_count,
        "unsupported_product_count": unsupported_count,
        "products": staged_products,
        "claim_boundaries": PREFLIGHT.claim_boundaries(),
    }


def stage_public_geodata_cache_product(record: dict[str, Any], manifest_base: Path) -> dict[str, Any]:
    category = PREFLIGHT.text_value(record.get("category")) or PREFLIGHT.text_value(record.get("product_id")) or PREFLIGHT.text_value(record.get("source_product_id"))
    required = bool(record.get("required", True))
    if not category or category not in STAGED_PRODUCT_CATEGORIES:
        return {
            **record,
            "required": required,
            "staging_status": "unsupported_product",
            "verification_status": "unsupported_product",
            "observed_checksum_sha256": "",
            "observed_metadata_mismatches": [],
        }

    staged_path = PREFLIGHT.resolve_repo_path(
        record.get("staged_path") or record.get("expected_staged_path"),
        base=manifest_base,
    )
    metadata_path = PREFLIGHT.resolve_repo_path(
        record.get("metadata_path") or record.get("expected_metadata_path"),
        base=manifest_base,
    )
    expected_checksum = PREFLIGHT.text_value(record.get("checksum_sha256")) or PREFLIGHT.text_value(record.get("processed_checksum"))
    observed_checksum = (
        PREFLIGHT.sha256_path(staged_path, exclude_paths={metadata_path} if staged_path.is_dir() else None)
        if staged_path.exists()
        else ""
    )
    actual_metadata = PREFLIGHT.load_site_config(metadata_path) if metadata_path.is_file() else {}
    if not isinstance(actual_metadata, dict):
        actual_metadata = {}

    missing_paths = [name for name, path in (("staged_path", staged_path), ("metadata_path", metadata_path)) if not path.exists()]
    if metadata_path.exists() and not metadata_path.is_file():
        missing_paths.append("metadata_path")
    if missing_paths:
        status = "missing" if required else "optional_missing"
        return {
            **record,
            "required": required,
            "staging_status": status,
            "verification_status": status,
            "staged_path": str(staged_path),
            "metadata_path": str(metadata_path),
            "observed_checksum_sha256": observed_checksum,
            "observed_metadata_mismatches": [],
            "missing_paths": missing_paths,
        }

    metadata_mismatches = compare_metadata(record, actual_metadata)
    checksum_match = not expected_checksum or observed_checksum == expected_checksum
    if not checksum_match:
        status = "checksum_mismatch"
    elif metadata_mismatches:
        status = "metadata_mismatch"
    else:
        status = "verified"

    normalized_record = {
        **record,
        "required": required,
        "staging_status": status,
        "verification_status": status,
        "staged_path": str(staged_path),
        "metadata_path": str(metadata_path),
        "checksum_sha256": expected_checksum or observed_checksum,
        "observed_checksum_sha256": observed_checksum,
        "observed_metadata_mismatches": metadata_mismatches,
    }
    if status == "verified":
        normalized_record["raw_checksum"] = observed_checksum
        normalized_record["processed_checksum"] = observed_checksum
        normalized_record["preprocessing_command_and_timestamp"] = (
            PREFLIGHT.text_value(record.get("preprocessing_command_and_timestamp"))
            or f"PYENV_VERSION=system uv run python scripts/stage_public_geodata_cache.py --cache-manifest {cache_manifest_path_for_record(record, manifest_base)}"
        )
    return normalized_record


def compare_metadata(record: dict[str, Any], metadata: dict[str, Any]) -> list[str]:
    mismatches: list[str] = []
    expected_source_product_id = PREFLIGHT.text_value(record.get("source_product_id"))
    expected_source_product_name = PREFLIGHT.text_value(record.get("source_product_name"))
    expected_source_url = PREFLIGHT.text_value(record.get("source_url_or_download_record")) or PREFLIGHT.text_value(record.get("source_url"))
    expected_product_version = PREFLIGHT.text_value(record.get("product_version_or_date")) or PREFLIGHT.text_value(record.get("product_version"))
    expected_tile_id = PREFLIGHT.text_value(record.get("tile_id_or_delivery_identifier")) or PREFLIGHT.text_value(record.get("tile_id"))
    expected_crs = PREFLIGHT.text_value(record.get("crs"))
    expected_resolution = PREFLIGHT.normalize_resolution_m(record.get("resolution_m"))
    expected_crop_extent = record.get("crop_extent_lv95_m") if isinstance(record.get("crop_extent_lv95_m"), dict) else {}
    expected_license = PREFLIGHT.text_value(record.get("license_or_terms_reference")) or PREFLIGHT.text_value(record.get("license_note"))
    expected_raw_checksum = PREFLIGHT.text_value(record.get("raw_checksum"))
    expected_processed_checksum = PREFLIGHT.text_value(record.get("processed_checksum"))
    expected_preprocessing = PREFLIGHT.text_value(record.get("preprocessing_command_and_timestamp"))

    if expected_source_product_id and PREFLIGHT.text_value(metadata.get("source_product_id")) != expected_source_product_id:
        mismatches.append("source_product_id")
    if expected_source_product_name and PREFLIGHT.text_value(metadata.get("source_product_name")) != expected_source_product_name:
        mismatches.append("source_product_name")
    if expected_source_url and PREFLIGHT.text_value(metadata.get("source_url_or_download_record")) != expected_source_url and PREFLIGHT.text_value(metadata.get("source_url")) != expected_source_url:
        mismatches.append("source_url_or_download_record")
    if expected_product_version and PREFLIGHT.text_value(metadata.get("product_version_or_date")) != expected_product_version and PREFLIGHT.text_value(metadata.get("product_version")) != expected_product_version:
        mismatches.append("product_version_or_date")
    if expected_tile_id and PREFLIGHT.text_value(metadata.get("tile_id_or_delivery_identifier")) != expected_tile_id and PREFLIGHT.text_value(metadata.get("tile_id")) != expected_tile_id:
        mismatches.append("tile_id_or_delivery_identifier")
    if expected_crs and PREFLIGHT.text_value(metadata.get("crs")) != expected_crs:
        mismatches.append("crs")
    if expected_resolution is not None and PREFLIGHT.normalize_resolution_m(metadata.get("resolution_m")) != expected_resolution:
        mismatches.append("resolution_m")
    if expected_crop_extent and metadata.get("crop_extent_lv95_m") != expected_crop_extent:
        mismatches.append("crop_extent_lv95_m")
    if expected_license and PREFLIGHT.text_value(metadata.get("license_or_terms_reference")) != expected_license and PREFLIGHT.text_value(metadata.get("license_note")) != expected_license:
        mismatches.append("license_or_terms_reference")
    if expected_raw_checksum and PREFLIGHT.text_value(metadata.get("raw_checksum")) != expected_raw_checksum:
        mismatches.append("raw_checksum")
    if expected_processed_checksum and PREFLIGHT.text_value(metadata.get("processed_checksum")) != expected_processed_checksum:
        mismatches.append("processed_checksum")
    if expected_preprocessing and PREFLIGHT.text_value(metadata.get("preprocessing_command_and_timestamp")) != expected_preprocessing:
        mismatches.append("preprocessing_command_and_timestamp")
    return mismatches


def cache_manifest_path_for_record(record: dict[str, Any], manifest_base: Path) -> str:
    return str(manifest_base / "public_geodata_cache_manifest.yaml")


def render_text_report(report: dict[str, Any]) -> str:
    lines = [
        f"schema_version: {report['schema_version']}",
        f"staging_status: {report['staging_status']}",
        f"cache_manifest_path: {report['cache_manifest_path']}",
        f"product_count: {report['product_count']}",
        f"staged_product_count: {report['staged_product_count']}",
        f"optional_missing_product_count: {report['optional_missing_product_count']}",
        f"missing_product_count: {report['missing_product_count']}",
        f"checksum_mismatch_product_count: {report['checksum_mismatch_product_count']}",
        f"metadata_mismatch_product_count: {report['metadata_mismatch_product_count']}",
        f"unsupported_product_count: {report['unsupported_product_count']}",
        "products:",
    ]
    for product in report["products"]:
        lines.append(
            f"- {product.get('category') or product.get('product_id')}: "
            f"staging_status={product.get('staging_status')}, "
            f"checksum_match={product.get('staging_status') == 'verified'}, "
            f"missing_paths={', '.join(product.get('missing_paths') or []) or 'none'}, "
            f"metadata_mismatches={', '.join(product.get('observed_metadata_mismatches') or []) or 'none'}"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
