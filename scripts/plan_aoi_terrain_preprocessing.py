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
import sys
from pathlib import Path
from typing import Any

import numpy as np

try:
    import yaml  # type: ignore
except ImportError as exc:  # pragma: no cover - environment setup.
    raise SystemExit("PyYAML is required; install with `python3 -m pip install PyYAML`") from exc


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "aoi_terrain_preprocessing_dry_run_v1"
DEFAULT_SITE_CONFIG = ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml"


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
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    args = parser.parse_args(argv)

    report = build_report(
        repo_root=args.repo_root,
        site_config=args.site_config,
        terrain_crop_path=args.terrain_crop,
        terrain_metadata_path=args.terrain_metadata,
        aoi_tile_catalog_path=args.aoi_tile_catalog,
        output_root=args.output_root,
    )

    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    output = json.dumps(report, indent=2, sort_keys=True) if args.format == "json" else render_text_report(report)
    print(output)
    return 0 if report["terrain_preprocessing_status"] == "ready" else 2


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
        return blocked_report(
            repo_root=repo_root,
            candidate_site_id=candidate_site_id,
            candidate_site_name=candidate_site_name,
            site_extent=site_extent,
            paths=paths,
            missing_inputs=missing_inputs,
        )

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
        terrain_metadata=terrain_metadata,
        source_tile_plan=source_tile_plan,
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
        "scale_up_authorized": False,
        "operational_claims_allowed": False,
    }

    if output_root is not None:
        output_root = resolve_path(output_root, base=repo_root)
        output_root.mkdir(parents=True, exist_ok=True)
        manifest_path = output_root / "terrain_preprocessing_manifest.json"
        report["terrain_preprocessing_manifest_path"] = display_path(manifest_path, repo_root)
        manifest_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    else:
        report["terrain_preprocessing_manifest_path"] = None

    return report


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
    return {
        "schema_version": SCHEMA_VERSION,
        "terrain_preprocessing_status": "blocked_missing_inputs",
        "candidate_site_id": candidate_site_id,
        "candidate_site_name": candidate_site_name if candidate_site_name != "unspecified" else "placeholder_second_site",
        "site_extent": site_extent if site_extent else "placeholder_extent_missing",
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
            "manifest_path": str(paths["output_root"] / "terrain_preprocessing_manifest.json"),
        },
        "terrain_summary": {},
        "source_tiles": [],
        "blocked_missing_inputs": missing_inputs,
        "missing_tile_ids": [],
        "metadata_mismatches": [],
        "output_roots": output_roots,
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


def build_package(
    *,
    repo_root: Path,
    candidate_site_id: str,
    candidate_site_name: str,
    paths: dict[str, Path | None],
    terrain: dict[str, Any],
    terrain_summary: dict[str, Any],
    terrain_metadata: dict[str, Any],
    source_tile_plan: dict[str, Any],
    metadata_mismatches: list[str],
    preprocessing_status: str,
) -> dict[str, Any]:
    output_root = paths["output_root"] or paths["processed_input_root"]
    output_roots = {
        "raw_swisstopo_cache_root": str(paths["raw_swisstopo_cache_root"]),
        "processed_input_root": str(paths["processed_input_root"]),
        "output_root": str(output_root),
    }
    output_paths = {
        "terrain_crop_path": display_path(paths["terrain_crop"], repo_root) if paths["terrain_crop"] is not None else None,
        "terrain_metadata_path": display_path(paths["terrain_metadata"], repo_root)
        if paths["terrain_metadata"] is not None
        else None,
        "aoi_tile_catalog_path": display_path(paths["aoi_tile_catalog"], repo_root)
        if paths["aoi_tile_catalog"] is not None
        else None,
        "terrain_preprocessing_manifest_path": str(output_root / "terrain_preprocessing_manifest.json"),
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
        "output_paths": output_paths,
        "metadata_mismatches": metadata_mismatches,
        "processing_steps": [
            "inspect staged terrain crop header",
            "read terrain metadata sidecar",
            "match AOI crop extent to AOI tile catalog",
            "record deterministic output roots and paths",
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
