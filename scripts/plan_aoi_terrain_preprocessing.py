#!/usr/bin/env python3
"""Plan deterministic AOI terrain preprocessing from staged tiles.

This helper is dry-run and fixture-backed. It inspects a staged terrain crop,
terrain metadata sidecar, and AOI tile catalog, then records the crop extent,
resolution, CRS, nodata, source tiles, and output roots needed by downstream
release-zone and case planning. It does not download public data or crop tiles.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import shutil
import sys
from pathlib import Path
from typing import Any

import numpy as np

try:
    import yaml  # type: ignore
except ImportError as exc:  # pragma: no cover - environment setup.
    raise SystemExit("PyYAML is required. Run this script with `PYENV_VERSION=system uv run python ...`; CI may use `requirements-tools.txt`") from exc


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "aoi_terrain_preprocessing_dry_run_v1"
PREPARED_INPUT_SCHEMA_VERSION = "aoi_prepared_input_builder_v1"
DEFAULT_SITE_CONFIG = ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml"
DEFAULT_PREPARED_INPUT_ROOT = ROOT / "data/processed/swisstopo/unspecified_second_site/prepared_input"
CONTEXT_MASK_ROLE_BY_CATEGORY = {
    "swissimage_context": {
        "mask_role": "visual_qa_context_mask",
        "mask_targets": ["orthophoto_visual_context"],
    },
    "swisstlm3d_context": {
        "mask_role": "transport_and_hydrography_context_mask",
        "mask_targets": ["roads_or_transport", "water_or_channel", "barriers_or_protection"],
    },
    "swisstlm3d_metadata": {
        "mask_role": "archive_metadata_provenance",
        "mask_targets": ["context_archive_provenance"],
    },
    "swisssurface3d_context": {
        "mask_role": "surface_context_mask",
        "mask_targets": ["surface_context"],
    },
    "swisssurface3d_raster_context": {
        "mask_role": "forest_or_canopy_context_mask",
        "mask_targets": ["forest_or_canopy"],
    },
    "swissbuildings3d_context": {
        "mask_role": "buildings_or_structures_context_mask",
        "mask_targets": ["buildings_or_structures"],
    },
    "barrier_inventory": {
        "mask_role": "optional_barrier_context_mask",
        "mask_targets": ["barriers_or_protection"],
    },
}


def _load_preflight_module():
    path = ROOT / "scripts" / "check_second_site_public_geodata_preflight.py"
    spec = importlib.util.spec_from_file_location("aoi_terrain_preprocessing_preflight", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load preflight helper from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


PREFLIGHT = _load_preflight_module()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--site-config", type=Path, default=DEFAULT_SITE_CONFIG)
    parser.add_argument("--terrain-crop", type=Path, default=None)
    parser.add_argument("--terrain-metadata", type=Path, default=None)
    parser.add_argument("--aoi-tile-catalog", type=Path, default=None)
    parser.add_argument("--output-root", type=Path, default=None)
    parser.add_argument("--prepared-input-root", type=Path, default=None)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    args = parser.parse_args(argv)

    if args.prepared_input_root is not None:
        report = build_prepared_input_report(
            repo_root=args.repo_root,
            site_config=args.site_config,
            terrain_crop_path=args.terrain_crop,
            terrain_metadata_path=args.terrain_metadata,
            aoi_tile_catalog_path=args.aoi_tile_catalog,
            prepared_input_root=args.prepared_input_root,
        )
        report_status = report["prepared_input_status"]
    else:
        report = build_report(
            repo_root=args.repo_root,
            site_config=args.site_config,
            terrain_crop_path=args.terrain_crop,
            terrain_metadata_path=args.terrain_metadata,
            aoi_tile_catalog_path=args.aoi_tile_catalog,
            output_root=args.output_root,
        )
        report_status = report["terrain_preprocessing_status"]

    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if args.format == "json":
        output = json.dumps(report, indent=2, sort_keys=True)
    elif args.prepared_input_root is not None:
        output = render_prepared_input_report(report)
    else:
        output = render_text_report(report)
    print(output)
    return 0 if report_status == "ready" else 2


def build_report(
    *,
    repo_root: Path | None = None,
    site_config: Path | None = None,
    terrain_crop_path: Path | None = None,
    terrain_metadata_path: Path | None = None,
    aoi_tile_catalog_path: Path | None = None,
    output_root: Path | None = None,
) -> dict[str, Any]:
    repo_root = repo_root or ROOT
    original_root = PREFLIGHT.ROOT
    try:
        PREFLIGHT.ROOT = repo_root
        config = PREFLIGHT.load_site_config(site_config) if site_config is not None and site_config.exists() else {}
        candidate_site_id = PREFLIGHT.text_value(config.get("candidate_site_id")) or "unspecified_second_site"
        candidate_site_id = candidate_site_id.strip()
        candidate_site_name = PREFLIGHT.text_value(config.get("candidate_site_name")) or "unspecified"
        site_extent = config.get("site_extent") if isinstance(config.get("site_extent"), dict) else {}

        paths = build_paths(
            candidate_site_id=candidate_site_id,
            config=config,
            repo_root=repo_root,
            terrain_crop_path=terrain_crop_path,
            terrain_metadata_path=terrain_metadata_path,
            aoi_tile_catalog_path=aoi_tile_catalog_path,
            output_root=output_root,
        )

        required_inputs = [paths["terrain_crop"], paths["terrain_metadata"]]
        missing_inputs = [display_path(path, repo_root) for path in required_inputs if not path.exists()]
        if paths["aoi_tile_catalog"] is not None and not paths["aoi_tile_catalog"].exists():
            missing_inputs.append(display_path(paths["aoi_tile_catalog"], repo_root))
        if missing_inputs:
            report = blocked_report(
                repo_root=repo_root,
                candidate_site_id=candidate_site_id,
                candidate_site_name=candidate_site_name,
                site_extent=site_extent,
                paths=paths,
                missing_inputs=missing_inputs,
            )
            if output_root is not None:
                output_root = resolve_path(output_root, base=repo_root)
                output_root.mkdir(parents=True, exist_ok=True)
                manifest_path = output_root / "terrain_preprocessing_manifest.json"
                report["terrain_preprocessing_manifest_path"] = display_path(manifest_path, repo_root)
                manifest_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            return report

        terrain = read_esri_ascii_grid(paths["terrain_crop"])
        terrain_metadata = PREFLIGHT.load_site_config(paths["terrain_metadata"])
        terrain_metadata = terrain_metadata if isinstance(terrain_metadata, dict) else {}
        aoi_tile_catalog = (
            PREFLIGHT.load_aoi_tile_catalog(paths["aoi_tile_catalog"])
            if paths["aoi_tile_catalog"] is not None and paths["aoi_tile_catalog"].exists()
            else {}
        )

        terrain_summary = build_terrain_summary(terrain)
        terrain_extent_for_tiles = dict(terrain_summary["extent_lv95_m"])
        terrain_extent_for_tiles["crs"] = "EPSG:2056"
        source_tile_plan = build_source_tile_plan(terrain_extent_for_tiles, aoi_tile_catalog, repo_root)
        metadata_mismatches = compare_metadata(terrain_summary, terrain_metadata, source_tile_plan["source_tile_ids"])
        terrain_audit = build_terrain_audit_summary(terrain_summary, terrain_metadata, source_tile_plan)
        terrain_derivative_inventory = build_terrain_derivative_inventory(terrain)
        terrain_nodata_summary = build_terrain_nodata_summary(terrain)
        terrain_provenance = build_terrain_provenance_summary(
            terrain_metadata=terrain_metadata,
            terrain_summary=terrain_summary,
            source_tile_plan=source_tile_plan,
            metadata_mismatches=metadata_mismatches,
        )
        if source_tile_plan["missing_tile_ids"]:
            preprocessing_status = "blocked_missing_tile"
        elif metadata_mismatches:
            preprocessing_status = "metadata_mismatch"
        else:
            preprocessing_status = "ready"

        package = build_package(
            repo_root=repo_root,
            candidate_site_id=candidate_site_id,
            candidate_site_name=candidate_site_name,
            paths=paths,
            terrain=terrain,
            terrain_summary=terrain_summary,
            terrain_audit=terrain_audit,
            terrain_nodata_summary=terrain_nodata_summary,
            terrain_derivative_inventory=terrain_derivative_inventory,
            terrain_metadata=terrain_metadata,
            source_tile_plan=source_tile_plan,
            terrain_provenance=terrain_provenance,
            metadata_mismatches=metadata_mismatches,
            preprocessing_status=preprocessing_status,
        )
        blocked_reason = ""
        if preprocessing_status == "blocked_missing_tile":
            blocked_reason = "missing AOI tile catalog coverage for tile ids: " + ", ".join(source_tile_plan["missing_tile_ids"])
        elif preprocessing_status == "metadata_mismatch":
            blocked_reason = "terrain metadata does not match staged crop: " + ", ".join(metadata_mismatches)

        report = {
            "schema_version": SCHEMA_VERSION,
            "terrain_preprocessing_status": preprocessing_status,
            "preprocessing_gate_classification": (
                "blocked_missing_terrain"
                if preprocessing_status in {"blocked_missing_inputs", "blocked_missing_tile"}
                else "metadata_mismatch"
                if preprocessing_status == "metadata_mismatch"
                else terrain_provenance["classification"]
            ),
            "candidate_site_id": candidate_site_id,
            "candidate_site_name": candidate_site_name if candidate_site_name != "unspecified" else "placeholder_second_site",
            "site_extent": site_extent if site_extent else "placeholder_extent_missing",
            "terrain_inputs": {
                "terrain_crop_path": display_path(paths["terrain_crop"], repo_root),
                "terrain_metadata_path": display_path(paths["terrain_metadata"], repo_root),
                "aoi_tile_catalog_path": display_path(paths["aoi_tile_catalog"], repo_root)
                if paths["aoi_tile_catalog"] is not None
                else None,
                "terrain_crop_sha256": PREFLIGHT.sha256_file(paths["terrain_crop"]),
                "terrain_metadata_sha256": PREFLIGHT.sha256_file(paths["terrain_metadata"]),
                "terrain_download_status": terrain_metadata.get("download_status"),
                "terrain_license": terrain_metadata.get("license"),
                "terrain_preprocessing_package": package,
            },
            "terrain_preprocessing_package": package,
            "terrain_summary": terrain_summary,
            "source_tiles": package["source_tiles"],
            "blocked_missing_inputs": missing_inputs,
            "missing_tile_ids": source_tile_plan["missing_tile_ids"],
            "metadata_mismatches": metadata_mismatches,
            "terrain_provenance": terrain_provenance,
            "terrain_audit": terrain_audit,
            "terrain_nodata_summary": terrain_nodata_summary,
            "terrain_derivative_inventory": terrain_derivative_inventory,
            "qa_blockers": list(terrain_provenance.get("qa_blockers") or missing_inputs),
            "output_roots": package["output_roots"],
            "blocked_reason": blocked_reason,
            "claim_boundaries": {
                **PREFLIGHT.claim_boundaries(),
                "downloads_authorized": False,
                "download_retry_authorized": False,
                "tile_staging_authorized": False,
                "notes": [
                    "AOI terrain preprocessing is dry-run or fixture-backed only",
                    "source tiles and crop metadata are recorded for downstream planning only",
                    "no public-data download or operational release-zone claim is authorized",
                ],
            },
            "ignored_output_roots": package["ignored_output_roots"],
            "scale_up_authorized": False,
            "operational_claims_allowed": False,
        }

        if output_root is not None and preprocessing_status == "ready":
            output_root = resolve_path(output_root, base=repo_root)
            materialize_terrain_output_root(
                output_root=output_root,
                terrain=terrain,
                terrain_metadata=terrain_metadata,
                aoi_tile_catalog=aoi_tile_catalog,
                terrain_audit=terrain_audit,
                terrain_nodata_summary=terrain_nodata_summary,
                terrain_derivative_inventory=terrain_derivative_inventory,
                report=report,
                repo_root=repo_root,
                preprocessing_status=preprocessing_status,
            )
            manifest_path = output_root / "terrain_preprocessing_manifest.json"
            report["terrain_preprocessing_manifest_path"] = display_path(manifest_path, repo_root)
            manifest_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        elif output_root is not None:
            output_root = resolve_path(output_root, base=repo_root)
            output_root.mkdir(parents=True, exist_ok=True)
            manifest_path = output_root / "terrain_preprocessing_manifest.json"
            report["terrain_preprocessing_manifest_path"] = display_path(manifest_path, repo_root)
            manifest_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        else:
            report["terrain_preprocessing_manifest_path"] = None

        return report
    finally:
        PREFLIGHT.ROOT = original_root


def build_prepared_input_report(
    *,
    repo_root: Path | None = None,
    site_config: Path | None = None,
    terrain_crop_path: Path | None = None,
    terrain_metadata_path: Path | None = None,
    aoi_tile_catalog_path: Path | None = None,
    prepared_input_root: Path | None = None,
) -> dict[str, Any]:
    repo_root = repo_root or ROOT
    original_root = PREFLIGHT.ROOT
    try:
        PREFLIGHT.ROOT = repo_root
        config = PREFLIGHT.load_site_config(site_config) if site_config is not None and site_config.exists() else {}
        candidate_site_id = PREFLIGHT.text_value(config.get("candidate_site_id")) or "unspecified_second_site"
        candidate_site_id = candidate_site_id.strip()
        candidate_site_name = PREFLIGHT.text_value(config.get("candidate_site_name")) or "unspecified"
        prepared_input_root = resolve_path(
            prepared_input_root or (repo_root / "data/processed/swisstopo" / candidate_site_id / "prepared_input"),
            base=repo_root,
        )
        terrain_output_root = prepared_input_root / "input"
        qa_root = prepared_input_root / "qa"

        paths = build_paths(
            candidate_site_id=candidate_site_id,
            config=config,
            repo_root=repo_root,
            terrain_crop_path=terrain_crop_path,
            terrain_metadata_path=terrain_metadata_path,
            aoi_tile_catalog_path=aoi_tile_catalog_path,
            output_root=terrain_output_root,
        )
        base_report = build_report(
            repo_root=repo_root,
            site_config=site_config,
            terrain_crop_path=terrain_crop_path,
            terrain_metadata_path=terrain_metadata_path,
            aoi_tile_catalog_path=aoi_tile_catalog_path,
            output_root=terrain_output_root,
        )

        terrain_status = base_report["terrain_preprocessing_status"]
        context_summary = build_context_availability_summary(
            repo_root=repo_root,
            site_config=site_config,
            config=config,
            paths=paths,
        )
        terrain_provenance = dict(base_report.get("terrain_provenance") or {})
        context_provenance = summarize_context_provenance(context_summary)
        context_preprocessing_report = build_context_preprocessing_report(
            context_summary=context_summary,
            terrain_summary=base_report.get("terrain_summary") if isinstance(base_report.get("terrain_summary"), dict) else {},
            terrain_audit=base_report.get("terrain_audit") if isinstance(base_report.get("terrain_audit"), dict) else {},
            terrain_provenance=terrain_provenance,
        )
        if terrain_status in {"blocked_missing_inputs", "blocked_missing_tile"}:
            prepared_status = "blocked_missing_terrain"
        elif terrain_status == "metadata_mismatch":
            prepared_status = "blocked_metadata_mismatch"
        else:
            prepared_status = "ready" if context_summary["missing_context_count"] == 0 else "partial_context"

        terrain_qa_summary = build_terrain_qa_summary(
            paths.get("terrain_crop"),
            base_report,
            prepared_status,
            terrain_derivative_inventory=base_report.get("terrain_derivative_inventory")
            if isinstance(base_report.get("terrain_derivative_inventory"), dict)
            else None,
            terrain_nodata_summary=base_report.get("terrain_nodata_summary")
            if isinstance(base_report.get("terrain_nodata_summary"), dict)
            else None,
            terrain_audit=base_report.get("terrain_audit") if isinstance(base_report.get("terrain_audit"), dict) else None,
        )
        preprocessing_gate_classification = classify_prepared_input_gate(
            terrain_status=terrain_status,
            terrain_provenance=terrain_provenance,
            context_summary=context_summary,
        )
        if prepared_status in {"ready", "partial_context"}:
            materialize_prepared_input_root(
                prepared_input_root=prepared_input_root,
                terrain_output_root=terrain_output_root,
                qa_root=qa_root,
                paths=paths,
                terrain_qa_summary=terrain_qa_summary,
                context_summary=context_summary,
                context_preprocessing_report=context_preprocessing_report,
                repo_root=repo_root,
            )
        report = {
            "schema_version": PREPARED_INPUT_SCHEMA_VERSION,
            "prepared_input_status": prepared_status,
            "candidate_site_id": candidate_site_id,
            "candidate_site_name": candidate_site_name if candidate_site_name != "unspecified" else "placeholder_second_site",
            "site_extent": base_report.get("site_extent", "placeholder_extent_missing"),
            "prepared_input_root": str(prepared_input_root),
            "prepared_input_manifest_path": str(prepared_input_root / "prepared_input_manifest.json"),
            "prepared_input_written": prepared_status in {"ready", "partial_context"},
            "terrain_preprocessing_status": terrain_status,
            "preprocessing_gate_classification": preprocessing_gate_classification,
            "terrain_preprocessing": base_report,
            "terrain_provenance": terrain_provenance,
            "terrain_qa_summary": terrain_qa_summary,
            "terrain_qa_summary_path": str(qa_root / "terrain_qa_summary.json"),
            "context_availability_summary": context_summary,
            "context_provenance": context_provenance,
            "context_availability_summary_path": str(qa_root / "context_availability_summary.json"),
            "context_preprocessing_report": context_preprocessing_report,
            "context_preprocessing_report_path": str(qa_root / "context_preprocessing_summary.json"),
            "output_roots": {
                "prepared_input_root": str(prepared_input_root),
                "terrain_output_root": str(terrain_output_root),
                "qa_root": str(qa_root),
            },
            "claim_boundaries": {
                **PREFLIGHT.claim_boundaries(),
                "downloads_authorized": False,
                "download_retry_authorized": False,
                "tile_staging_authorized": False,
                "notes": [
                    "prepared-input builder mode is deterministic and fixture-backed only",
                    "terrain and QA summaries are preparation evidence only",
                    "context availability does not imply hazard validation or operational readiness",
                ],
            },
            "scale_up_authorized": False,
            "operational_claims_allowed": False,
        }
        write_prepared_input_manifest(report, prepared_input_root)
        return report
    finally:
        PREFLIGHT.ROOT = original_root


def build_context_availability_summary(
    *,
    repo_root: Path,
    site_config: Path | None,
    config: dict[str, Any],
    paths: dict[str, Path | None],
) -> dict[str, Any]:
    acquisition_manifest_path = PREFLIGHT.resolve_repo_path(
        config.get("acquisition_manifest_path"),
        (site_config.parent if site_config is not None else repo_root / "tests/fixtures/second_site_public_geodata_preflight")
        / "chant_sura_fluelapass_public_geodata_acquisition.yaml",
        base=repo_root,
    )
    acquisition_manifest = PREFLIGHT.load_site_config(acquisition_manifest_path) if acquisition_manifest_path.exists() else {}
    expected_products = acquisition_manifest.get("expected_products") if isinstance(acquisition_manifest.get("expected_products"), list) else []
    required_categories = list(PREFLIGHT.PUBLIC_CONTEXT_ACQUISITION_PLAN_CATEGORIES) + ["swisstlm3d_metadata"]
    entries: list[dict[str, Any]] = []
    missing_categories: list[str] = []

    if not expected_products:
        for category in required_categories:
            entries.append(
                {
                    "category": category,
                    "product": "",
                    "required": True,
                    "expected_staged_path": "",
                    "metadata_path": None,
                    "staged_asset_present": False,
                    "metadata_present": False,
                    "review_classification": None,
                    "source_product": None,
                    "source_tile_ids": [],
                    "coordinate_reference_system": {},
                    "context_readiness_status": "missing",
                    "context_provenance_classification": "missing",
                    "context_qa_blockers": ["missing_staged_context"],
                }
            )
        missing_categories = required_categories.copy()
        return {
            "schema_version": PREPARED_INPUT_SCHEMA_VERSION,
            "context_readiness_status": "partial_context",
            "context_provenance_classification": "missing",
            "expected_context_count": len(entries),
            "ready_context_count": 0,
            "missing_context_count": len(missing_categories),
            "real_staged_context_count": 0,
            "fixture_backed_context_count": 0,
            "metadata_mismatch_context_count": 0,
            "ready_context_categories": [],
            "missing_context_categories": missing_categories,
            "context_entries": entries,
            "optional_context_entries": [],
            "context_qa_blockers": ["missing_staged_context"],
            "processed_context_root": str(paths["processed_context_root"]) if paths.get("processed_context_root") is not None else None,
            "acquisition_manifest_path": str(acquisition_manifest_path),
        }

    context_warnings: list[str] = []

    for category in required_categories:
        manifest_entry = next(
            (
                entry
                for entry in expected_products
                if isinstance(entry, dict) and PREFLIGHT.text_value(entry.get("category")) == category
            ),
            {},
        )
        expected_path_text = PREFLIGHT.text_value(manifest_entry.get("expected_staged_path"))
        if not expected_path_text and category == "swisstlm3d_metadata":
            expected_path_text = str((paths["processed_context_root"] / "swisstlm3d" / "metadata.json") if paths["processed_context_root"] is not None else repo_root / "data/processed/swisstopo/unknown/context/swisstlm3d/metadata.json")
        if not expected_path_text:
            continue
        expected_path = PREFLIGHT.resolve_repo_path(expected_path_text, base=repo_root)
        metadata_path = resolve_context_metadata_path(expected_path, category)
        staged_asset_present = expected_path.exists()
        metadata_present = metadata_path is not None and metadata_path.exists()
        metadata = PREFLIGHT.load_site_config(metadata_path) if metadata_present and metadata_path is not None else {}
        ready = staged_asset_present
        crs = metadata.get("coordinate_reference_system") if isinstance(metadata.get("coordinate_reference_system"), dict) else {}
        blockers = []
        if not staged_asset_present:
            blockers.append("missing_staged_asset")
        if metadata_present and PREFLIGHT.text_value(crs.get("epsg")) not in {"2056", "EPSG:2056"}:
            blockers.append("crs")
        if metadata_present and PREFLIGHT.text_value(crs.get("vertical_datum")) not in {"LN02", "LN02 / CH1903+"}:
            blockers.append("vertical_datum")
        provenance_classification = classify_context_provenance(metadata, ready=ready)
        if blockers and ready:
            provenance_classification = "metadata_mismatch"
        if not ready:
            missing_categories.append(category)
        if not metadata_present:
            context_warnings.append(f"missing metadata sidecar for context category {category}")
        entries.append(
            {
                "category": category,
                "product": PREFLIGHT.text_value(manifest_entry.get("product")),
                "required": bool(manifest_entry.get("required", True)),
                "expected_staged_path": str(expected_path),
                "metadata_path": str(metadata_path) if metadata_path is not None else None,
                "staged_asset_present": staged_asset_present,
                "metadata_present": metadata_present,
                "review_classification": PREFLIGHT.text_value(metadata.get("review_classification")),
                "source_product": PREFLIGHT.text_value(metadata.get("source_product")),
                "source_tile_ids": metadata.get("source_tile_ids") if isinstance(metadata.get("source_tile_ids"), list) else [],
                "coordinate_reference_system": crs,
                "context_readiness_status": "ready" if ready else "missing",
                "context_provenance_classification": provenance_classification,
                "context_qa_blockers": blockers,
            }
        )

    optional_entries = [
        {
            "category": PREFLIGHT.text_value(entry.get("category")),
            "product": PREFLIGHT.text_value(entry.get("product")),
            "expected_staged_path": PREFLIGHT.text_value(entry.get("expected_staged_path")),
            "required": bool(entry.get("required")),
            "status": "optional",
        }
        for entry in expected_products
        if isinstance(entry, dict)
        and PREFLIGHT.text_value(entry.get("category")) not in required_categories
        and PREFLIGHT.text_value(entry.get("category"))
    ]

    optional_missing_categories: list[str] = []
    for entry in expected_products:
        if not isinstance(entry, dict):
            continue
        category = PREFLIGHT.text_value(entry.get("category"))
        if not category or category in required_categories:
            continue
        expected_path_text = PREFLIGHT.text_value(entry.get("expected_staged_path"))
        if not expected_path_text:
            continue
        expected_path = PREFLIGHT.resolve_repo_path(expected_path_text, base=repo_root)
        if not expected_path.exists():
            optional_missing_categories.append(category)
    context_warnings = dedupe_text(
        [
            *([f"missing required context category {category}" for category in missing_categories] if missing_categories else []),
            *([f"missing optional context category {category}" for category in optional_missing_categories] if optional_missing_categories else []),
            *context_warnings,
        ]
    )

    return {
        "schema_version": PREPARED_INPUT_SCHEMA_VERSION,
        "context_readiness_status": "ready" if not missing_categories else "partial_context",
        "context_provenance_classification": summarize_context_entry_provenance(entries),
        "expected_context_count": len(entries),
        "ready_context_count": len([entry for entry in entries if entry["context_readiness_status"] == "ready"]),
        "missing_context_count": len(missing_categories),
        "real_staged_context_count": len([entry for entry in entries if entry["context_provenance_classification"] == "real_staged"]),
        "fixture_backed_context_count": len([entry for entry in entries if entry["context_provenance_classification"] == "fixture_backed"]),
        "metadata_mismatch_context_count": len([entry for entry in entries if entry["context_provenance_classification"] == "metadata_mismatch"]),
        "ready_context_categories": [entry["category"] for entry in entries if entry["context_readiness_status"] == "ready"],
        "missing_context_categories": missing_categories,
        "optional_missing_context_categories": optional_missing_categories,
        "optional_missing_context_count": len(optional_missing_categories),
        "context_entries": entries,
        "optional_context_entries": optional_entries,
        "context_warnings": context_warnings,
        "context_warning_count": len(context_warnings),
        "context_qa_blockers": [
            blocker
            for entry in entries
            for blocker in entry.get("context_qa_blockers", [])
        ],
        "processed_context_root": str(paths["processed_context_root"]) if paths.get("processed_context_root") is not None else None,
        "acquisition_manifest_path": str(acquisition_manifest_path),
    }


def resolve_context_metadata_path(expected_path: Path, category: str) -> Path | None:
    if expected_path.suffix:
        return expected_path
    metadata_json = expected_path / "metadata.json"
    if metadata_json.exists():
        return metadata_json
    metadata_yaml = expected_path / "metadata.yaml"
    if metadata_yaml.exists():
        return metadata_yaml
    if category == "swisstlm3d_metadata":
        return expected_path / "metadata.json"
    return metadata_json


def build_terrain_qa_summary(
    terrain_path: Path | None,
    base_report: dict[str, Any],
    prepared_status: str,
    *,
    terrain_derivative_inventory: dict[str, Any] | None = None,
    terrain_nodata_summary: dict[str, Any] | None = None,
    terrain_audit: dict[str, Any] | None = None,
) -> dict[str, Any]:
    terrain_summary = base_report.get("terrain_summary") if isinstance(base_report.get("terrain_summary"), dict) else {}
    terrain_provenance = base_report.get("terrain_provenance") if isinstance(base_report.get("terrain_provenance"), dict) else {}
    qa_blockers = list(terrain_provenance.get("qa_blockers") or base_report.get("metadata_mismatches") or [])
    if not terrain_summary:
        return {
            "schema_version": PREPARED_INPUT_SCHEMA_VERSION,
            "qa_status": prepared_status,
            "terrain_present": False,
            "terrain_provenance_classification": PREFLIGHT.text_value(terrain_provenance.get("classification")) or "missing",
            "qa_blockers": qa_blockers or ["missing_terrain"],
            "summary_status": "blocked_missing_terrain",
            "terrain_cell_count": 0,
            "valid_cell_count": 0,
            "nodata_cell_count": 0,
            "slope_kernel": "horn_3x3",
            "aspect_convention": "clockwise_from_north",
            "hillshade_parameters_deg": {"azimuth": 315.0, "altitude": 45.0},
            "terrain_audit": terrain_audit or {},
            "terrain_nodata_summary": terrain_nodata_summary or {
                "cell_count": 0,
                "valid_cell_count": 0,
                "nodata_cell_count": 0,
                "nodata_fraction": 0.0,
            },
            "terrain_derivative_inventory": terrain_derivative_inventory or build_empty_terrain_derivative_inventory(),
            "slope_stats_deg": {},
            "aspect_stats_deg": {},
            "hillshade_stats": {},
            "roughness_stats_m": {},
        }

    if terrain_path is None or not terrain_path.exists():
        return {
            "schema_version": PREPARED_INPUT_SCHEMA_VERSION,
            "qa_status": prepared_status,
            "terrain_present": False,
            "terrain_provenance_classification": PREFLIGHT.text_value(terrain_provenance.get("classification")) or "missing",
            "qa_blockers": qa_blockers or ["missing_terrain"],
            "summary_status": "blocked_missing_terrain",
            "terrain_cell_count": int(terrain_summary.get("cell_count", 0)),
            "valid_cell_count": 0,
            "nodata_cell_count": int(terrain_summary.get("cell_count", 0)),
            "slope_kernel": "horn_3x3",
            "aspect_convention": "clockwise_from_north",
            "hillshade_parameters_deg": {"azimuth": 315.0, "altitude": 45.0},
            "terrain_audit": terrain_audit or {},
            "terrain_nodata_summary": terrain_nodata_summary or {
                "cell_count": int(terrain_summary.get("cell_count", 0)),
                "valid_cell_count": 0,
                "nodata_cell_count": int(terrain_summary.get("cell_count", 0)),
                "nodata_fraction": 1.0 if int(terrain_summary.get("cell_count", 0)) else 0.0,
            },
            "terrain_derivative_inventory": terrain_derivative_inventory or build_empty_terrain_derivative_inventory(int(terrain_summary.get("cell_count", 0))),
            "slope_stats_deg": {},
            "aspect_stats_deg": {},
            "hillshade_stats": {},
            "roughness_stats_m": {},
        }

    terrain = read_esri_ascii_grid(terrain_path)
    terrain_derivative_inventory = terrain_derivative_inventory or build_terrain_derivative_inventory(terrain)
    terrain_nodata_summary = terrain_nodata_summary or build_terrain_nodata_summary(terrain)
    terrain_audit = terrain_audit or {}
    valid_mask = np.isfinite(terrain["values"]) & (terrain["values"] != terrain["nodata"])
    valid_values = terrain["values"][valid_mask]
    slope_stats_deg = terrain_derivative_inventory.get("slope", {}).get("stats", {}) if isinstance(terrain_derivative_inventory.get("slope"), dict) else {}
    aspect_stats_deg = terrain_derivative_inventory.get("aspect", {}).get("stats", {}) if isinstance(terrain_derivative_inventory.get("aspect"), dict) else {}
    hillshade_stats = terrain_derivative_inventory.get("hillshade", {}).get("stats", {}) if isinstance(terrain_derivative_inventory.get("hillshade"), dict) else {}
    roughness_stats_m = terrain_derivative_inventory.get("roughness", {}).get("stats", {}) if isinstance(terrain_derivative_inventory.get("roughness"), dict) else {}
    return {
        "schema_version": PREPARED_INPUT_SCHEMA_VERSION,
        "qa_status": prepared_status,
        "terrain_present": True,
        "terrain_provenance_classification": PREFLIGHT.text_value(terrain_provenance.get("classification")) or "fixture_backed",
        "qa_blockers": qa_blockers,
        "summary_status": "ready" if prepared_status == "ready" else prepared_status,
        "terrain_cell_count": int(terrain_summary.get("cell_count", terrain["values"].size)),
        "valid_cell_count": int(valid_values.size),
        "nodata_cell_count": int(terrain["values"].size - valid_values.size),
        "terrain_extent_lv95_m": terrain_summary.get("extent_lv95_m", {}),
        "resolution_m": terrain_summary.get("resolution_m"),
        "slope_kernel": "horn_3x3",
        "aspect_convention": "clockwise_from_north",
        "hillshade_parameters_deg": {"azimuth": 315.0, "altitude": 45.0},
        "terrain_audit": terrain_audit,
        "terrain_nodata_summary": terrain_nodata_summary,
        "terrain_derivative_inventory": terrain_derivative_inventory,
        "slope_stats_deg": slope_stats_deg,
        "aspect_stats_deg": aspect_stats_deg,
        "hillshade_stats": hillshade_stats,
        "roughness_stats_m": roughness_stats_m,
    }


def compute_terrain_derivative_grids(terrain: dict[str, Any]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    values = terrain["values"].astype(float)
    nodata = float(terrain["nodata"])
    cellsize = float(terrain["cellsize"])
    nrows, ncols = values.shape
    slope = np.full((nrows, ncols), np.nan, dtype=float)
    aspect = np.full((nrows, ncols), np.nan, dtype=float)
    hillshade = np.full((nrows, ncols), np.nan, dtype=float)
    zenith_rad = math.radians(45.0)
    azimuth_rad = math.radians(315.0)

    for row in range(1, nrows - 1):
        for col in range(1, ncols - 1):
            window = values[row - 1 : row + 2, col - 1 : col + 2]
            if not np.all(np.isfinite(window)) or np.any(window == nodata):
                continue
            dzdx = (
                (window[0, 2] + 2.0 * window[1, 2] + window[2, 2])
                - (window[0, 0] + 2.0 * window[1, 0] + window[2, 0])
            ) / (8.0 * cellsize)
            dzdy = (
                (window[2, 0] + 2.0 * window[2, 1] + window[2, 2])
                - (window[0, 0] + 2.0 * window[0, 1] + window[0, 2])
            ) / (8.0 * cellsize)
            slope_rad = math.atan(math.hypot(dzdx, dzdy))
            aspect_rad = math.atan2(dzdy, -dzdx)
            if aspect_rad < 0.0:
                aspect_rad += 2.0 * math.pi
            slope[row, col] = math.degrees(slope_rad)
            aspect[row, col] = math.degrees(aspect_rad)
            hillshade_raw = (
                math.cos(zenith_rad) * math.cos(slope_rad)
                + math.sin(zenith_rad) * math.sin(slope_rad) * math.cos(azimuth_rad - aspect_rad)
            )
            hillshade[row, col] = max(0.0, min(255.0, 255.0 * hillshade_raw))

    return slope, aspect, hillshade


def compute_terrain_roughness_grid(terrain: dict[str, Any]) -> np.ndarray:
    values = terrain["values"].astype(float)
    nodata = float(terrain["nodata"])
    nrows, ncols = values.shape
    roughness = np.full((nrows, ncols), np.nan, dtype=float)

    for row in range(1, nrows - 1):
        for col in range(1, ncols - 1):
            window = values[row - 1 : row + 2, col - 1 : col + 2]
            if not np.all(np.isfinite(window)) or np.any(window == nodata):
                continue
            roughness[row, col] = float(np.std(window, ddof=0))

    return roughness


def build_terrain_derivative_inventory(terrain: dict[str, Any]) -> dict[str, Any]:
    slope_deg, aspect_deg, hillshade = compute_terrain_derivative_grids(terrain)
    roughness_m = compute_terrain_roughness_grid(terrain)
    valid_mask = np.isfinite(terrain["values"]) & (terrain["values"] != terrain["nodata"])
    total_cell_count = int(terrain["values"].size)
    valid_cell_count = int(valid_mask.sum())
    return {
        "terrain_cell_count": total_cell_count,
        "valid_cell_count": valid_cell_count,
        "nodata_cell_count": int(total_cell_count - valid_cell_count),
        "slope": {
            "kernel": "horn_3x3",
            "units": "degrees",
            "stats": summarize_numeric_grid(slope_deg),
        },
        "aspect": {
            "kernel": "horn_3x3",
            "units": "degrees_clockwise_from_north",
            "stats": summarize_aspect_grid(aspect_deg),
        },
        "hillshade": {
            "kernel": "horn_3x3",
            "units": "0_to_255",
            "stats": summarize_numeric_grid(hillshade),
        },
        "roughness": {
            "kernel": "local_stddev_3x3",
            "units": "metres",
            "stats": summarize_numeric_grid(roughness_m),
        },
    }


def build_terrain_nodata_summary(terrain: dict[str, Any]) -> dict[str, Any]:
    values = terrain["values"]
    valid_mask = np.isfinite(values) & (values != terrain["nodata"])
    valid_cell_count = int(valid_mask.sum())
    total_cell_count = int(values.size)
    nodata_cell_count = int(total_cell_count - valid_cell_count)
    return {
        "cell_count": total_cell_count,
        "valid_cell_count": valid_cell_count,
        "nodata_cell_count": nodata_cell_count,
        "nodata_fraction": float(nodata_cell_count / total_cell_count) if total_cell_count else 0.0,
    }


def build_terrain_audit_summary(
    terrain_summary: dict[str, Any],
    terrain_metadata: dict[str, Any],
    source_tile_plan: dict[str, Any],
) -> dict[str, Any]:
    raster = terrain_metadata.get("raster") if isinstance(terrain_metadata.get("raster"), dict) else {}
    preprocessing = terrain_metadata.get("preprocessing") if isinstance(terrain_metadata.get("preprocessing"), dict) else {}
    return {
        "observed_extent_lv95_m": terrain_summary.get("extent_lv95_m", {}),
        "observed_resolution_m": terrain_summary.get("resolution_m"),
        "metadata_extent_lv95_m": terrain_metadata.get("extent_lv95_m") if isinstance(terrain_metadata.get("extent_lv95_m"), dict) else {},
        "metadata_resolution_m": raster.get("resolution_m"),
        "metadata_nodata": raster.get("nodata"),
        "extent_match": terrain_summary.get("extent_lv95_m", {}) == (terrain_metadata.get("extent_lv95_m") if isinstance(terrain_metadata.get("extent_lv95_m"), dict) else {}),
        "resolution_match": PREFLIGHT.normalize_resolution_m(raster.get("resolution_m")) == PREFLIGHT.normalize_resolution_m(terrain_summary.get("resolution_m")),
        "nodata_match": PREFLIGHT.normalize_resolution_m(raster.get("nodata")) == PREFLIGHT.normalize_resolution_m(terrain_summary.get("nodata")),
        "source_tile_ids": list(source_tile_plan.get("source_tile_ids") or []),
        "source_tile_count": len(source_tile_plan.get("source_tiles") or []),
        "missing_tile_ids": list(source_tile_plan.get("missing_tile_ids") or []),
        "crop_extent_lv95_m": preprocessing.get("crop_extent_lv95_m") if isinstance(preprocessing.get("crop_extent_lv95_m"), dict) else {},
    }


def build_empty_terrain_derivative_inventory(cell_count: int = 0) -> dict[str, Any]:
    return {
        "terrain_cell_count": cell_count,
        "valid_cell_count": 0,
        "nodata_cell_count": cell_count,
        "slope": {"kernel": "horn_3x3", "units": "degrees", "stats": {}},
        "aspect": {"kernel": "horn_3x3", "units": "degrees_clockwise_from_north", "stats": {}},
        "hillshade": {"kernel": "horn_3x3", "units": "0_to_255", "stats": {}},
        "roughness": {"kernel": "local_stddev_3x3", "units": "metres", "stats": {}},
    }


def materialize_terrain_output_root(
    *,
    output_root: Path,
    terrain: dict[str, Any],
    terrain_metadata: dict[str, Any],
    aoi_tile_catalog: dict[str, Any],
    terrain_audit: dict[str, Any],
    terrain_nodata_summary: dict[str, Any],
    terrain_derivative_inventory: dict[str, Any],
    report: dict[str, Any],
    repo_root: Path,
    preprocessing_status: str,
) -> None:
    output_root.mkdir(parents=True, exist_ok=True)
    terrain_output_path = output_root / "terrain.asc"
    terrain_metadata_path = output_root / "terrain_metadata.yaml"
    aoi_tile_catalog_path = output_root / "aoi_tile_catalog.yaml"

    if report["terrain_inputs"]["terrain_crop_path"] is not None:
        source_terrain_path = resolve_path(Path(report["terrain_inputs"]["terrain_crop_path"]), base=repo_root)
        if source_terrain_path.resolve() != terrain_output_path.resolve():
            shutil.copy2(source_terrain_path, terrain_output_path)
    if report["terrain_inputs"]["terrain_metadata_path"] is not None:
        source_metadata_path = resolve_path(Path(report["terrain_inputs"]["terrain_metadata_path"]), base=repo_root)
        if source_metadata_path.resolve() != terrain_metadata_path.resolve():
            if source_metadata_path.suffix.lower() in {".yaml", ".yml"}:
                shutil.copy2(source_metadata_path, terrain_metadata_path)
            else:
                terrain_metadata_path.write_text(json.dumps(terrain_metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    else:
        terrain_metadata_path.write_text(json.dumps(terrain_metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if aoi_tile_catalog:
        aoi_tile_catalog_path.write_text(yaml.safe_dump(aoi_tile_catalog, sort_keys=False), encoding="utf-8")

    (output_root / "terrain_qa_summary.json").write_text(
        json.dumps(
            {
                "terrain_audit": terrain_audit,
                "terrain_nodata_summary": terrain_nodata_summary,
                "terrain_derivative_inventory": terrain_derivative_inventory,
                "preprocessing_status": preprocessing_status,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (output_root / "terrain_derivative_inventory.json").write_text(
        json.dumps(terrain_derivative_inventory, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_root / "terrain_nodata_summary.json").write_text(
        json.dumps(terrain_nodata_summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def summarize_numeric_grid(grid: np.ndarray) -> dict[str, float | int | None]:
    finite = grid[np.isfinite(grid)]
    if finite.size == 0:
        return {
            "count": 0,
            "min": None,
            "max": None,
            "mean": None,
            "median": None,
        }
    return {
        "count": int(finite.size),
        "min": float(np.min(finite)),
        "max": float(np.max(finite)),
        "mean": float(np.mean(finite)),
        "median": float(np.median(finite)),
    }


def summarize_aspect_grid(grid: np.ndarray) -> dict[str, float | int | None]:
    finite = grid[np.isfinite(grid)]
    if finite.size == 0:
        return {
            "count": 0,
            "min": None,
            "max": None,
            "mean": None,
            "median": None,
        }
    radians = np.deg2rad(finite)
    mean_angle = math.degrees(math.atan2(np.mean(np.sin(radians)), np.mean(np.cos(radians))))
    if mean_angle < 0.0:
        mean_angle += 360.0
    return {
        "count": int(finite.size),
        "min": float(np.min(finite)),
        "max": float(np.max(finite)),
        "mean": float(mean_angle),
        "median": float(np.median(finite)),
    }


def materialize_prepared_input_root(
    *,
    prepared_input_root: Path,
    terrain_output_root: Path,
    qa_root: Path,
    paths: dict[str, Path | None],
    terrain_qa_summary: dict[str, Any],
    context_summary: dict[str, Any],
    context_preprocessing_report: dict[str, Any],
    repo_root: Path,
) -> None:
    prepared_input_root.mkdir(parents=True, exist_ok=True)
    terrain_output_root.mkdir(parents=True, exist_ok=True)
    qa_root.mkdir(parents=True, exist_ok=True)

    if paths.get("terrain_crop") is not None:
        shutil.copy2(paths["terrain_crop"], terrain_output_root / "terrain.asc")
    if paths.get("terrain_metadata") is not None:
        shutil.copy2(paths["terrain_metadata"], terrain_output_root / "terrain_metadata.yaml")
    if paths.get("aoi_tile_catalog") is not None and paths["aoi_tile_catalog"].exists():
        shutil.copy2(paths["aoi_tile_catalog"], terrain_output_root / "aoi_tile_catalog.yaml")

    (qa_root / "terrain_qa_summary.json").write_text(json.dumps(terrain_qa_summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (qa_root / "context_availability_summary.json").write_text(
        json.dumps(context_summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (qa_root / "context_preprocessing_summary.json").write_text(
        json.dumps(context_preprocessing_report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_prepared_input_manifest(report: dict[str, Any], prepared_input_root: Path) -> None:
    prepared_input_root.mkdir(parents=True, exist_ok=True)
    manifest_path = prepared_input_root / "prepared_input_manifest.json"
    manifest_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def render_prepared_input_report(report: dict[str, Any]) -> str:
    lines = [
        f"schema_version: {report['schema_version']}",
        f"prepared_input_status: {report['prepared_input_status']}",
        f"preprocessing_gate_classification: {report.get('preprocessing_gate_classification', '')}",
        f"candidate_site_id: {report['candidate_site_id']}",
        f"candidate_site_name: {report['candidate_site_name']}",
        f"prepared_input_root: {report['prepared_input_root']}",
        "",
        "terrain_provenance:",
    ]
    for key, value in report.get("terrain_provenance", {}).items():
        if key == "qa_blockers" and isinstance(value, list):
            lines.append("- qa_blockers:")
            lines.extend(f"  - {item}" for item in value)
        elif key == "provenance_notes" and isinstance(value, list):
            lines.append("- provenance_notes:")
            lines.extend(f"  - {item}" for item in value)
        else:
            lines.append(f"- {key}: {value}")
    lines.extend(
        [
            "",
            "context_provenance:",
        ]
    )
    for key, value in report.get("context_provenance", {}).items():
        if key == "qa_blockers" and isinstance(value, list):
            lines.append("- qa_blockers:")
            lines.extend(f"  - {item}" for item in value)
        else:
            lines.append(f"- {key}: {value}")
    lines.extend(
        [
            "",
            "terrain_qa_summary:",
        ]
    )
    for key, value in report["terrain_qa_summary"].items():
        lines.append(f"- {key}: {value}")
    lines.append("")
    lines.append("context_availability_summary:")
    for key, value in report["context_availability_summary"].items():
        if key == "context_entries":
            lines.append("- context_entries:")
            for entry in value:
                lines.append(f"  - {entry['category']}: {entry['context_readiness_status']} / {entry.get('context_provenance_classification', '')}")
                blockers = entry.get("context_qa_blockers") or []
                if blockers:
                    lines.append(f"    - blockers: {', '.join(blockers)}")
        elif key == "optional_context_entries":
            lines.append("- optional_context_entries:")
            for entry in value:
                lines.append(f"  - {entry['category']}: {entry['status']}")
        else:
            lines.append(f"- {key}: {value}")
    lines.append("")
    lines.append("context_preprocessing_report:")
    for key, value in report.get("context_preprocessing_report", {}).items():
        if key == "context_mask_inventory" and isinstance(value, list):
            lines.append("- context_mask_inventory:")
            for entry in value:
                lines.append(
                    f"  - {entry.get('category', '')}: {entry.get('status', '')} / {entry.get('mask_role', '')}"
                )
                targets = entry.get("mask_targets") or []
                if targets:
                    lines.append(f"    - mask_targets: {', '.join(targets)}")
                provenance = entry.get("mask_provenance") or {}
                if provenance:
                    lines.append(
                        f"    - provenance: {provenance.get('context_provenance_classification', '')} / "
                        f"{provenance.get('review_classification', '')}"
                    )
        elif key == "mask_provenance" and isinstance(value, dict):
            lines.append("- mask_provenance:")
            for nested_key, nested_value in value.items():
                lines.append(f"  - {nested_key}: {nested_value}")
        elif key == "context_warnings" and isinstance(value, list):
            lines.append("- context_warnings:")
            lines.extend(f"  - {item}" for item in value)
        else:
            lines.append(f"- {key}: {value}")
    return "\n".join(lines)


def build_paths(
    *,
    candidate_site_id: str,
    config: dict[str, Any],
    repo_root: Path,
    terrain_crop_path: Path | None,
    terrain_metadata_path: Path | None,
    aoi_tile_catalog_path: Path | None,
    output_root: Path | None,
) -> dict[str, Path | None]:
    processed_input_root = PREFLIGHT.resolve_repo_path(
        config.get("expected_processed_input_root"),
        repo_root / "data/processed/swisstopo" / candidate_site_id / "input",
        base=repo_root,
    )
    processed_context_root = PREFLIGHT.resolve_repo_path(
        config.get("expected_processed_context_root"),
        repo_root / "data/processed/swisstopo" / candidate_site_id / "context",
        base=repo_root,
    )
    derived = {
        "terrain_crop": processed_input_root / "terrain.asc",
        "terrain_metadata": processed_input_root / "terrain_metadata.yaml",
        "aoi_tile_catalog": processed_input_root / "aoi_tile_catalog.yaml",
    }

    return {
        "terrain_crop": PREFLIGHT.resolve_repo_path(
            terrain_crop_path,
            derived["terrain_crop"],
            base=repo_root,
        )
        if terrain_crop_path is not None
        else derived["terrain_crop"],
        "terrain_metadata": PREFLIGHT.resolve_repo_path(
            terrain_metadata_path,
            derived["terrain_metadata"],
            base=repo_root,
        )
        if terrain_metadata_path is not None
        else derived["terrain_metadata"],
        "aoi_tile_catalog": PREFLIGHT.resolve_repo_path(
            aoi_tile_catalog_path,
            derived["aoi_tile_catalog"],
            base=repo_root,
        )
        if aoi_tile_catalog_path is not None
        else derived["aoi_tile_catalog"],
        "processed_input_root": processed_input_root,
        "processed_context_root": processed_context_root,
        "output_root": resolve_path(output_root, base=repo_root) if output_root is not None else processed_input_root,
        "raw_swisstopo_cache_root": repo_root / "data/raw/swisstopo" / candidate_site_id,
    }


def blocked_report(
    *,
    repo_root: Path,
    candidate_site_id: str,
    candidate_site_name: str,
    site_extent: dict[str, Any],
    paths: dict[str, Path | None],
    missing_inputs: list[str],
) -> dict[str, Any]:
    output_roots = {
        "raw_swisstopo_cache_root": str(paths["raw_swisstopo_cache_root"]),
        "processed_input_root": str(paths["processed_input_root"]),
        "output_root": str(paths["output_root"]),
    }
    ignored_output_roots = [
        str(repo_root / "data/raw/swisstopo" / candidate_site_id),
        str(repo_root / "data/processed/swisstopo" / candidate_site_id),
        str(repo_root / "validation/private" / candidate_site_id),
        str(repo_root / "hazard/results" / candidate_site_id),
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "terrain_preprocessing_status": "blocked_missing_inputs",
        "preprocessing_gate_classification": "blocked_missing_terrain",
        "candidate_site_id": candidate_site_id,
        "candidate_site_name": candidate_site_name if candidate_site_name != "unspecified" else "placeholder_second_site",
        "site_extent": site_extent if site_extent else "placeholder_extent_missing",
        "blocked_reason": "missing staged terrain inputs: " + ", ".join(missing_inputs),
        "terrain_inputs": {
            "terrain_crop_path": display_path(paths["terrain_crop"], repo_root) if paths["terrain_crop"] is not None else None,
            "terrain_metadata_path": display_path(paths["terrain_metadata"], repo_root)
            if paths["terrain_metadata"] is not None
            else None,
            "aoi_tile_catalog_path": display_path(paths["aoi_tile_catalog"], repo_root)
            if paths["aoi_tile_catalog"] is not None
            else None,
            "terrain_preprocessing_package": {
                "preprocessing_status": "blocked_missing_inputs",
                "source_tile_ids": [],
                "source_tiles": [],
                "output_roots": output_roots,
                "terrain_provenance": {
                    "classification": "missing",
                    "qa_blockers": missing_inputs,
                },
                "qa_blockers": missing_inputs,
            },
        },
        "terrain_preprocessing_package": {
            "preprocessing_status": "blocked_missing_inputs",
            "crop_extent_lv95_m": {},
            "resolution_m": None,
            "crs_epsg": None,
            "nodata": None,
            "source_tile_ids": [],
            "source_tiles": [],
            "output_roots": output_roots,
            "output_paths": {},
            "source_tile_count": 0,
            "terrain_provenance": {
                "classification": "missing",
                "qa_blockers": missing_inputs,
            },
            "qa_blockers": missing_inputs,
            "ignored_output_roots": ignored_output_roots,
            "manifest_path": str(paths["output_root"] / "terrain_preprocessing_manifest.json"),
        },
        "terrain_summary": {},
        "source_tiles": [],
        "blocked_missing_inputs": missing_inputs,
        "missing_tile_ids": [],
        "metadata_mismatches": [],
        "terrain_audit": {
            "observed_extent_lv95_m": {},
            "observed_resolution_m": None,
            "metadata_extent_lv95_m": {},
            "metadata_resolution_m": None,
            "metadata_nodata": None,
            "extent_match": False,
            "resolution_match": False,
            "nodata_match": False,
            "source_tile_ids": [],
            "source_tile_count": 0,
            "missing_tile_ids": [],
            "crop_extent_lv95_m": {},
        },
        "terrain_nodata_summary": {
            "cell_count": 0,
            "valid_cell_count": 0,
            "nodata_cell_count": 0,
            "nodata_fraction": 0.0,
        },
        "terrain_derivative_inventory": build_empty_terrain_derivative_inventory(),
        "terrain_provenance": {
            "classification": "missing",
            "qa_blockers": missing_inputs,
        },
        "qa_blockers": missing_inputs,
        "output_roots": output_roots,
        "ignored_output_roots": ignored_output_roots,
        "claim_boundaries": {
            **PREFLIGHT.claim_boundaries(),
            "downloads_authorized": False,
            "download_retry_authorized": False,
            "tile_staging_authorized": False,
            "notes": [
                "AOI terrain preprocessing is dry-run or fixture-backed only",
                "source tiles and crop metadata are recorded for downstream planning only",
                "no public-data download or operational release-zone claim is authorized",
            ],
        },
        "scale_up_authorized": False,
        "operational_claims_allowed": False,
        "terrain_preprocessing_manifest_path": None,
    }


def build_terrain_summary(terrain: dict[str, Any]) -> dict[str, Any]:
    values = terrain["values"]
    return {
        "cell_count": int(values.size),
        "ncols": terrain["ncols"],
        "nrows": terrain["nrows"],
        "resolution_m": terrain["cellsize"],
        "nodata": terrain["nodata"],
        "extent_lv95_m": {
            "xmin": terrain["xllcorner"],
            "ymin": terrain["yllcorner"],
            "xmax": terrain["xllcorner"] + terrain["ncols"] * terrain["cellsize"],
            "ymax": terrain["yllcorner"] + terrain["nrows"] * terrain["cellsize"],
        },
    }


def build_source_tile_plan(
    crop_extent_lv95_m: dict[str, float],
    aoi_tile_catalog: dict[str, Any],
    repo_root: Path,
) -> dict[str, Any]:
    wanted_tile_ids = PREFLIGHT.tile_catalog_ids_for_extent(crop_extent_lv95_m)
    tile_records = PREFLIGHT.catalog_tile_records(aoi_tile_catalog)
    tile_record_by_id = {entry.get("tile_id"): entry for entry in tile_records if entry.get("tile_id")}
    missing_tile_ids = [tile_id for tile_id in wanted_tile_ids if tile_id not in tile_record_by_id]
    source_tiles = [
        build_source_tile_record(tile_record_by_id[tile_id], repo_root)
        for tile_id in wanted_tile_ids
        if tile_id in tile_record_by_id
    ]
    return {
        "source_tile_ids": wanted_tile_ids,
        "source_tiles": source_tiles,
        "missing_tile_ids": missing_tile_ids,
        "tile_candidate_count": len(wanted_tile_ids),
    }


def build_source_tile_record(record: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    return {
        "tile_id": PREFLIGHT.text_value(record.get("tile_id")),
        "source_product": PREFLIGHT.text_value(record.get("source_product")),
        "source_filename": PREFLIGHT.text_value(record.get("source_filename")),
        "source_url": PREFLIGHT.text_value(record.get("source_url")),
        "product_version": PREFLIGHT.text_value(record.get("product_version")),
        "product_date": PREFLIGHT.text_value(record.get("product_date")),
        "license": PREFLIGHT.text_value(record.get("license")),
        "extent_lv95_m": record.get("extent_lv95_m") if isinstance(record.get("extent_lv95_m"), dict) else {},
        "expected_staging_root": PREFLIGHT.text_value(record.get("expected_staging_root")) or str(
            repo_root / "data/raw/swisstopo"
        ),
    }


def compare_metadata(
    terrain_summary: dict[str, Any],
    terrain_metadata: dict[str, Any],
    source_tile_ids: list[str],
) -> list[str]:
    mismatches: list[str] = []
    crs = terrain_metadata.get("coordinate_reference_system") if isinstance(terrain_metadata.get("coordinate_reference_system"), dict) else {}
    raster = terrain_metadata.get("raster") if isinstance(terrain_metadata.get("raster"), dict) else {}
    preprocessing = terrain_metadata.get("preprocessing") if isinstance(terrain_metadata.get("preprocessing"), dict) else {}
    extent = terrain_metadata.get("extent_lv95_m") if isinstance(terrain_metadata.get("extent_lv95_m"), dict) else {}

    if PREFLIGHT.text_value(crs.get("epsg")) not in {"2056", "EPSG:2056"}:
        mismatches.append("crs")
    if PREFLIGHT.normalize_resolution_m(raster.get("resolution_m")) != PREFLIGHT.normalize_resolution_m(terrain_summary["resolution_m"]):
        mismatches.append("resolution_m")
    if PREFLIGHT.normalize_resolution_m(raster.get("nodata")) != PREFLIGHT.normalize_resolution_m(terrain_summary["nodata"]):
        mismatches.append("nodata")
    if extent != terrain_summary["extent_lv95_m"]:
        mismatches.append("extent_lv95_m")
    crop_extent = preprocessing.get("crop_extent_lv95_m") if isinstance(preprocessing.get("crop_extent_lv95_m"), dict) else {}
    if crop_extent and crop_extent != terrain_summary["extent_lv95_m"]:
        mismatches.append("preprocessing.crop_extent_lv95_m")
    metadata_source_tiles = preprocessing.get("source_tile_ids") if isinstance(preprocessing.get("source_tile_ids"), list) else []
    if metadata_source_tiles and sorted(PREFLIGHT.text_value(tile_id) for tile_id in metadata_source_tiles) != sorted(source_tile_ids):
        mismatches.append("preprocessing.source_tile_ids")
    return mismatches


def build_terrain_provenance_summary(
    *,
    terrain_metadata: dict[str, Any],
    terrain_summary: dict[str, Any],
    source_tile_plan: dict[str, Any],
    metadata_mismatches: list[str],
) -> dict[str, Any]:
    crs = terrain_metadata.get("coordinate_reference_system") if isinstance(terrain_metadata.get("coordinate_reference_system"), dict) else {}
    preprocessing = terrain_metadata.get("preprocessing") if isinstance(terrain_metadata.get("preprocessing"), dict) else {}
    provenance = terrain_metadata.get("provenance") if isinstance(terrain_metadata.get("provenance"), dict) else {}
    return {
        "classification": classify_terrain_provenance(terrain_metadata=terrain_metadata, metadata_mismatches=metadata_mismatches),
        "source_dataset": PREFLIGHT.text_value(terrain_metadata.get("source_dataset")),
        "source_product": PREFLIGHT.text_value(terrain_metadata.get("source_product")),
        "source_url": PREFLIGHT.text_value(terrain_metadata.get("source_url")),
        "source_filename": PREFLIGHT.text_value(terrain_metadata.get("source_filename")),
        "download_status": PREFLIGHT.text_value(terrain_metadata.get("download_status")),
        "source_file_present": bool(terrain_metadata.get("source_file_present")),
        "license": PREFLIGHT.text_value(terrain_metadata.get("license")),
        "preprocessing_status": PREFLIGHT.text_value(preprocessing.get("status")),
        "resampling_method": PREFLIGHT.text_value(preprocessing.get("resampling_method")),
        "source_tile_ids": list(source_tile_plan.get("source_tile_ids") or []),
        "source_tile_count": len(source_tile_plan.get("source_tiles") or []),
        "crs_epsg": PREFLIGHT.normalize_resolution_m(crs.get("epsg")) if crs else None,
        "vertical_datum": PREFLIGHT.text_value(crs.get("vertical_datum")),
        "extent_lv95_m": terrain_summary["extent_lv95_m"],
        "resolution_m": terrain_summary["resolution_m"],
        "nodata": terrain_summary["nodata"],
        "qa_blockers": list(metadata_mismatches),
        "intended_use": PREFLIGHT.text_value(provenance.get("intended_use")),
        "provenance_notes": provenance.get("notes") if isinstance(provenance.get("notes"), list) else [],
    }


def classify_terrain_provenance(*, terrain_metadata: dict[str, Any], metadata_mismatches: list[str]) -> str:
    if metadata_mismatches:
        return "metadata_mismatch"
    source_dataset = PREFLIGHT.text_value(terrain_metadata.get("source_dataset")).lower()
    source_product = PREFLIGHT.text_value(terrain_metadata.get("source_product")).lower()
    download_status = PREFLIGHT.text_value(terrain_metadata.get("download_status")).lower()
    preprocessing_status = PREFLIGHT.text_value(
        (terrain_metadata.get("preprocessing") or {}).get("status") if isinstance(terrain_metadata.get("preprocessing"), dict) else ""
    ).lower()
    license_text = PREFLIGHT.text_value(terrain_metadata.get("license")).lower()
    synthetic_markers = ("synthetic" in source_dataset) or ("synthetic" in source_product) or ("fixture" in download_status) or ("synthetic" in preprocessing_status) or ("synthetic" in license_text)
    if synthetic_markers:
        return "fixture_backed"
    if source_dataset == "swisstopo_swissalti3d" or source_product == "swissalti3d" or download_status in {"staged_real_input", "downloaded", "staged"} or preprocessing_status in {"staged_real_input", "downloaded", "staged"}:
        return "real_staged"
    return "fixture_backed"


def classify_context_provenance(metadata: dict[str, Any], *, ready: bool) -> str:
    if not ready:
        return "missing"
    if not metadata:
        return "fixture_backed"
    crs = metadata.get("coordinate_reference_system") if isinstance(metadata.get("coordinate_reference_system"), dict) else {}
    if not crs:
        return "fixture_backed"
    if PREFLIGHT.text_value(crs.get("epsg")) not in {"2056", "EPSG:2056"}:
        return "metadata_mismatch"
    if PREFLIGHT.text_value(crs.get("vertical_datum")) not in {"LN02", "LN02 / CH1903+"}:
        return "metadata_mismatch"
    review_classification = PREFLIGHT.text_value(metadata.get("review_classification")).lower()
    inspection_rationale = PREFLIGHT.text_value(metadata.get("inspection_rationale")).lower()
    if "synthetic" in inspection_rationale or review_classification in {"unresolved", "limiting"}:
        return "fixture_backed"
    if review_classification in {"acceptable", "ready"}:
        return "real_staged"
    return "fixture_backed"


def summarize_context_entry_provenance(entries: list[dict[str, Any]]) -> str:
    classifications = [PREFLIGHT.text_value(entry.get("context_provenance_classification")) for entry in entries]
    if not classifications:
        return "missing"
    if any(classification == "metadata_mismatch" for classification in classifications):
        return "metadata_mismatch"
    if any(classification == "missing" for classification in classifications):
        return "missing"
    if all(classification == "real_staged" for classification in classifications):
        return "real_staged"
    if all(classification == "fixture_backed" for classification in classifications):
        return "fixture_backed"
    if "real_staged" in classifications and "fixture_backed" in classifications:
        return "mixed_real_fixture"
    return "fixture_backed"


def summarize_context_provenance(context_summary: dict[str, Any]) -> dict[str, Any]:
    entries = context_summary.get("context_entries") if isinstance(context_summary.get("context_entries"), list) else []
    classifications = [PREFLIGHT.text_value(entry.get("context_provenance_classification")) for entry in entries if isinstance(entry, dict)]
    return {
        "classification": summarize_context_entry_provenance(entries if isinstance(entries, list) else []),
        "real_staged_context_count": len([classification for classification in classifications if classification == "real_staged"]),
        "fixture_backed_context_count": len([classification for classification in classifications if classification == "fixture_backed"]),
        "missing_context_count": len([classification for classification in classifications if classification == "missing"]),
        "metadata_mismatch_context_count": len([classification for classification in classifications if classification == "metadata_mismatch"]),
        "qa_blockers": list(context_summary.get("context_qa_blockers") or []),
    }


def build_context_preprocessing_report(
    *,
    context_summary: dict[str, Any],
    terrain_summary: dict[str, Any],
    terrain_audit: dict[str, Any],
    terrain_provenance: dict[str, Any],
) -> dict[str, Any]:
    entries = [entry for entry in context_summary.get("context_entries", []) if isinstance(entry, dict)]
    mask_rows: list[dict[str, Any]] = []
    context_warnings = list(context_summary.get("context_warnings") or [])
    missing_required_categories = list(context_summary.get("missing_context_categories") or [])
    missing_optional_categories = list(context_summary.get("optional_missing_context_categories") or [])

    for entry in entries:
        category = PREFLIGHT.text_value(entry.get("category"))
        role = CONTEXT_MASK_ROLE_BY_CATEGORY.get(category, {})
        required = bool(entry.get("required"))
        ready = entry.get("context_readiness_status") == "ready"
        status = "ready" if ready else "blocked_missing_context" if required else "warning_optional_context_missing"
        if not ready and not required and category:
            warning = f"missing optional context category {category}"
            if warning not in context_warnings:
                context_warnings.append(warning)
        mask_rows.append(
            {
                "category": category,
                "product": PREFLIGHT.text_value(entry.get("product")),
                "required": required,
                "status": status,
                "mask_role": role.get("mask_role", "context_mask"),
                "mask_targets": list(role.get("mask_targets", [])),
                "context_readiness_status": entry.get("context_readiness_status"),
                "context_provenance_classification": entry.get("context_provenance_classification"),
                "expected_staged_path": entry.get("expected_staged_path"),
                "metadata_path": entry.get("metadata_path"),
                "staged_asset_present": bool(entry.get("staged_asset_present")),
                "metadata_present": bool(entry.get("metadata_present")),
                "source_product": entry.get("source_product"),
                "source_tile_ids": list(entry.get("source_tile_ids") or []),
                "coordinate_reference_system": entry.get("coordinate_reference_system") or {},
                "context_qa_blockers": list(entry.get("context_qa_blockers") or []),
                "mask_provenance": {
                    "source_product": PREFLIGHT.text_value(entry.get("product")),
                    "source_tile_ids": list(entry.get("source_tile_ids") or []),
                    "review_classification": PREFLIGHT.text_value(entry.get("review_classification")),
                    "context_provenance_classification": PREFLIGHT.text_value(entry.get("context_provenance_classification")),
                    "expected_staged_path": entry.get("expected_staged_path"),
                    "metadata_path": entry.get("metadata_path"),
                },
            }
        )

    if context_summary.get("metadata_mismatch_context_count", 0):
        preprocessing_status = "blocked_context_metadata_mismatch"
        blocked_reason = "staged context metadata does not match the required CRS or vertical datum contract"
    elif missing_required_categories:
        preprocessing_status = "blocked_missing_context"
        blocked_reason = "missing required context categories: " + ", ".join(missing_required_categories)
    elif missing_optional_categories:
        preprocessing_status = "ready_with_optional_warnings"
        blocked_reason = ""
    else:
        preprocessing_status = "ready"
        blocked_reason = ""

    terrain_alignment = {
        "terrain_extent_lv95_m": terrain_summary.get("extent_lv95_m", {}),
        "terrain_resolution_m": terrain_summary.get("resolution_m"),
        "terrain_nodata": terrain_summary.get("nodata"),
        "terrain_source_tile_ids": list(terrain_audit.get("source_tile_ids") or []),
        "terrain_source_tile_count": terrain_audit.get("source_tile_count", 0),
        "terrain_crop_extent_lv95_m": terrain_audit.get("crop_extent_lv95_m", {}),
        "terrain_provenance_classification": PREFLIGHT.text_value(terrain_provenance.get("classification")),
    }

    return {
        "schema_version": PREPARED_INPUT_SCHEMA_VERSION,
        "context_preprocessing_status": preprocessing_status,
        "blocked_reason": blocked_reason,
        "context_warning_count": len(context_warnings),
        "context_warnings": context_warnings,
        "missing_required_context_categories": missing_required_categories,
        "missing_optional_context_categories": missing_optional_categories,
        "context_mask_count": len(mask_rows),
        "context_mask_inventory": mask_rows,
        "mask_provenance": {
            "terrain_alignment": terrain_alignment,
            "processed_context_root": context_summary.get("processed_context_root"),
            "acquisition_manifest_path": context_summary.get("acquisition_manifest_path"),
            "context_provenance_classification": context_summary.get("context_provenance_classification"),
            "ready_context_categories": list(context_summary.get("ready_context_categories") or []),
            "mask_consumer_targets": [
                "release_zone_screening",
                "gis_package_preparation",
            ],
            "mask_inventory_state": "aligned" if preprocessing_status == "ready" else "deferred_or_blocked",
        },
    }


def dedupe_text(items: list[str]) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for item in items:
        if not item or item in seen:
            continue
        seen.add(item)
        ordered.append(item)
    return ordered


def classify_prepared_input_gate(
    *,
    terrain_status: str,
    terrain_provenance: dict[str, Any],
    context_summary: dict[str, Any],
) -> str:
    if terrain_status in {"blocked_missing_inputs", "blocked_missing_tile"}:
        return "blocked_missing_terrain"
    if terrain_status == "metadata_mismatch":
        return "blocked_metadata_mismatch"
    if context_summary.get("missing_context_count", 0):
        return "blocked_missing_context"
    if terrain_provenance.get("classification") == "metadata_mismatch" or context_summary.get("context_provenance_classification") == "metadata_mismatch":
        return "blocked_metadata_mismatch"
    context_classification = PREFLIGHT.text_value(context_summary.get("context_provenance_classification"))
    terrain_classification = PREFLIGHT.text_value(terrain_provenance.get("classification"))
    if terrain_classification == "real_staged" and context_classification == "real_staged":
        return "real_staged"
    if terrain_classification == "fixture_backed" or context_classification in {"fixture_backed", "mixed_real_fixture"}:
        return "fixture_backed"
    if terrain_classification == "real_staged":
        return "real_staged"
    return "fixture_backed"


def build_package(
    *,
    repo_root: Path,
    candidate_site_id: str,
    candidate_site_name: str,
    paths: dict[str, Path | None],
    terrain: dict[str, Any],
    terrain_summary: dict[str, Any],
    terrain_audit: dict[str, Any],
    terrain_nodata_summary: dict[str, Any],
    terrain_derivative_inventory: dict[str, Any],
    terrain_metadata: dict[str, Any],
    source_tile_plan: dict[str, Any],
    terrain_provenance: dict[str, Any],
    metadata_mismatches: list[str],
    preprocessing_status: str,
) -> dict[str, Any]:
    output_root = paths["output_root"] or paths["processed_input_root"]
    output_roots = {
        "raw_swisstopo_cache_root": str(paths["raw_swisstopo_cache_root"]),
        "processed_input_root": str(paths["processed_input_root"]),
        "output_root": str(output_root),
    }
    ignored_output_roots = [
        str(repo_root / "data/raw/swisstopo" / candidate_site_id),
        str(repo_root / "data/processed/swisstopo" / candidate_site_id),
        str(repo_root / "validation/private" / candidate_site_id),
        str(repo_root / "hazard/results" / candidate_site_id),
    ]
    output_paths = {
        "terrain_crop_path": display_path(paths["terrain_crop"], repo_root) if paths["terrain_crop"] is not None else None,
        "terrain_metadata_path": display_path(paths["terrain_metadata"], repo_root)
        if paths["terrain_metadata"] is not None
        else None,
        "aoi_tile_catalog_path": display_path(paths["aoi_tile_catalog"], repo_root)
        if paths["aoi_tile_catalog"] is not None
        else None,
        "terrain_preprocessing_manifest_path": str(output_root / "terrain_preprocessing_manifest.json"),
        "terrain_derivative_inventory_path": str(output_root / "terrain_derivative_inventory.json"),
        "terrain_nodata_summary_path": str(output_root / "terrain_nodata_summary.json"),
    }
    crs = terrain_metadata.get("coordinate_reference_system") if isinstance(terrain_metadata.get("coordinate_reference_system"), dict) else {}
    return {
        "schema_version": SCHEMA_VERSION,
        "preprocessing_status": preprocessing_status,
        "candidate_site_id": candidate_site_id,
        "candidate_site_name": candidate_site_name if candidate_site_name != "unspecified" else "placeholder_second_site",
        "crop_extent_lv95_m": terrain_summary["extent_lv95_m"],
        "resolution_m": terrain_summary["resolution_m"],
        "crs_epsg": PREFLIGHT.normalize_resolution_m(crs.get("epsg")) if crs else None,
        "nodata": float(terrain_summary["nodata"]),
        "source_tile_ids": source_tile_plan["source_tile_ids"],
        "source_tile_count": len(source_tile_plan["source_tiles"]),
        "source_tiles": source_tile_plan["source_tiles"],
        "output_roots": output_roots,
        "ignored_output_roots": ignored_output_roots,
        "output_paths": output_paths,
        "metadata_mismatches": metadata_mismatches,
        "terrain_provenance": terrain_provenance,
        "terrain_audit": terrain_audit,
        "terrain_nodata_summary": terrain_nodata_summary,
        "terrain_derivative_inventory": terrain_derivative_inventory,
        "qa_blockers": list(metadata_mismatches),
        "processing_steps": [
            "inspect staged terrain crop header",
            "read terrain metadata sidecar",
            "match AOI crop extent to AOI tile catalog",
            "compute slope and roughness derivative inventory",
            "record deterministic output roots and paths",
            "materialize normalized DEM package in the ignored output root",
        ],
        "terrain_crop_sha256": PREFLIGHT.sha256_file(paths["terrain_crop"]) if paths["terrain_crop"] is not None else None,
        "terrain_metadata_sha256": PREFLIGHT.sha256_file(paths["terrain_metadata"]) if paths["terrain_metadata"] is not None else None,
    }


def read_esri_ascii_grid(path: Path) -> dict[str, Any]:
    header = read_esri_ascii_header(path)
    values = np.loadtxt(path, skiprows=6, dtype=float)
    if values.ndim == 1:
        values = values.reshape(1, -1)
    if values.shape != (header["nrows"], header["ncols"]):
        raise ValueError(f"terrain grid shape mismatch in {path}: expected {(header['nrows'], header['ncols'])}, got {values.shape}")
    return {
        **header,
        "values": values,
    }


def read_esri_ascii_header(path: Path) -> dict[str, Any]:
    header: dict[str, Any] = {}
    with path.open("r", encoding="utf-8") as handle:
        for _ in range(6):
            line = handle.readline()
            if not line:
                break
            parts = line.split()
            if len(parts) < 2:
                continue
            key = parts[0].lower()
            value = parts[1]
            if key in {"ncols", "nrows"}:
                header[key] = int(float(value))
            elif key == "nodata_value":
                header["nodata"] = float(value)
            else:
                header[key] = float(value)
    required = {"ncols", "nrows", "xllcorner", "yllcorner", "cellsize", "nodata"}
    missing = sorted(required.difference(header))
    if missing:
        raise ValueError(f"terrain grid header missing fields {missing}: {path}")
    return header


def resolve_path(path: Path | None, *, base: Path = ROOT) -> Path:
    if path is None:
        return base
    return path if path.is_absolute() else base / path


def display_path(path: Path, repo_root: Path) -> str:
    path = Path(path)
    try:
        return str(path.relative_to(repo_root))
    except ValueError:
        return str(path)


def render_text_report(report: dict[str, Any]) -> str:
    lines = [
        f"schema_version: {report['schema_version']}",
        f"terrain_preprocessing_status: {report['terrain_preprocessing_status']}",
        f"preprocessing_gate_classification: {report.get('preprocessing_gate_classification', '')}",
        f"candidate_site_id: {report['candidate_site_id']}",
        f"candidate_site_name: {report['candidate_site_name']}",
        "",
        "terrain_inputs:",
    ]
    for key, value in report["terrain_inputs"].items():
        if isinstance(value, dict):
            lines.append(f"- {key}:")
            for subkey, subvalue in value.items():
                if isinstance(subvalue, list):
                    lines.append(f"  - {subkey}:")
                    for item in subvalue:
                        if isinstance(item, dict):
                            lines.append("    -")
                            for field, field_value in item.items():
                                lines.append(f"      - {field}: {field_value}")
                        else:
                            lines.append(f"    - {item}")
                else:
                    lines.append(f"  - {subkey}: {subvalue}")
        else:
            lines.append(f"- {key}: {value}")
    lines.extend(
        [
            "",
            "terrain_preprocessing_package:",
        ]
    )
    for key, value in report["terrain_preprocessing_package"].items():
        if isinstance(value, list):
            lines.append(f"- {key}:")
            for item in value:
                if isinstance(item, dict):
                    lines.append("  -")
                    for field, field_value in item.items():
                        lines.append(f"    - {field}: {field_value}")
                else:
                    lines.append(f"  - {item}")
        elif isinstance(value, dict):
            lines.append(f"- {key}:")
            for subkey, subvalue in value.items():
                lines.append(f"  - {subkey}: {subvalue}")
        else:
            lines.append(f"- {key}: {value}")
    lines.append("")
    lines.append("metadata_mismatches:")
    lines.extend(f"- {item}" for item in report["metadata_mismatches"] or ["none"])
    lines.append("")
    lines.append("missing_tile_ids:")
    lines.extend(f"- {item}" for item in report["missing_tile_ids"] or ["none"])
    lines.append("")
    lines.append("blocked_missing_inputs:")
    lines.extend(f"- {item}" for item in report["blocked_missing_inputs"] or ["none"])
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
