#!/usr/bin/env python3
"""Restage a larger management-AOI terrain/source-footprint bundle from local raw data.

This helper uses the already-downloaded swissALTI3D raw tile to produce a
deterministic larger terrain crop and copies the frozen source-zone metadata
into an ignored output root. It is a staging command, not a simulation,
threshold-tuning step, or operational claim.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except ImportError as exc:  # pragma: no cover - environment setup.
    raise SystemExit("PyYAML is required. Run this script with `PYENV_VERSION=system uv run python ...`; CI may use `requirements-tools.txt`") from exc


ROOT = Path(__file__).resolve().parents[1]
DIAGNOSTIC_SCRIPT = ROOT / "scripts" / "diagnose_release_candidate_zero_result.py"
DEFAULT_OUTPUT_ROOT = Path("/tmp/rust_rockfall/tb388_management_aoi_restaged")
DEFAULT_RAW_TERRAIN = ROOT / "data/raw/swisstopo/chant_sura_fluelapass_portability_example_v1/swissalti3d_2019_2793-1180_2_2056_5728.tif"
DEFAULT_SOURCE_ZONE_METADATA = ROOT / "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/source_zone_metadata.yaml"
DEFAULT_AOI_TILE_CATALOG = ROOT / "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/aoi_tile_catalog.yaml"
DEFAULT_TERRAIN_METADATA_TEMPLATE = ROOT / "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/terrain_metadata.yaml"
SCHEMA_VERSION = "management_aoi_terrain_restage_v1"


def _load_diagnostic_module():
    spec = importlib.util.spec_from_file_location("management_aoi_zero_result_diagnostic", DIAGNOSTIC_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load diagnostic helper from {DIAGNOSTIC_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


DIAGNOSTIC = _load_diagnostic_module()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--raw-terrain", type=Path, default=DEFAULT_RAW_TERRAIN)
    parser.add_argument("--source-zone-metadata", type=Path, default=DEFAULT_SOURCE_ZONE_METADATA)
    parser.add_argument("--aoi-tile-catalog", type=Path, default=DEFAULT_AOI_TILE_CATALOG)
    parser.add_argument("--terrain-metadata-template", type=Path, default=DEFAULT_TERRAIN_METADATA_TEMPLATE)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    args = parser.parse_args(argv)

    try:
        report = stage_management_aoi_restaged_inputs(
            repo_root=args.repo_root,
            output_root=args.output_root,
            raw_terrain_path=args.raw_terrain,
            source_zone_metadata_path=args.source_zone_metadata,
            aoi_tile_catalog_path=args.aoi_tile_catalog,
            terrain_metadata_template_path=args.terrain_metadata_template,
        )
    except RuntimeError as exc:
        print(f"management AOI restage error: {exc}", file=sys.stderr)
        return 2

    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps(report, indent=2, sort_keys=True) if args.format == "json" else render_text_report(report))
    return 0 if report["restage_status"] == "ready" else 2


def stage_management_aoi_restaged_inputs(
    *,
    repo_root: Path,
    output_root: Path,
    raw_terrain_path: Path,
    source_zone_metadata_path: Path,
    aoi_tile_catalog_path: Path | None = None,
    terrain_metadata_template_path: Path | None = None,
) -> dict[str, Any]:
    repo_root = repo_root.resolve(strict=False)
    raw_terrain_path = resolve_path(repo_root, raw_terrain_path)
    source_zone_metadata_path = resolve_path(repo_root, source_zone_metadata_path)
    output_root = resolve_path(repo_root, output_root)
    aoi_tile_catalog_path = resolve_path(repo_root, aoi_tile_catalog_path) if aoi_tile_catalog_path is not None else None
    terrain_metadata_template_path = (
        resolve_path(repo_root, terrain_metadata_template_path) if terrain_metadata_template_path is not None else None
    )

    missing_inputs = [
        display_path(path, repo_root)
        for path in (raw_terrain_path, source_zone_metadata_path)
        if not path.exists()
    ]
    if aoi_tile_catalog_path is not None and not aoi_tile_catalog_path.exists():
        missing_inputs.append(display_path(aoi_tile_catalog_path, repo_root))
    if terrain_metadata_template_path is not None and not terrain_metadata_template_path.exists():
        missing_inputs.append(display_path(terrain_metadata_template_path, repo_root))
    if missing_inputs:
        raise RuntimeError("missing required restage inputs: " + ", ".join(missing_inputs))

    output_input_root = output_root / "input"
    output_input_root.mkdir(parents=True, exist_ok=True)

    extent = derive_raw_dataset_extent(raw_terrain_path)
    terrain_output_path = output_input_root / "terrain.asc"
    terrain_metadata_path = output_input_root / "terrain_metadata.yaml"
    source_zone_output_path = output_input_root / "source_zone_metadata.yaml"

    gdal_translate_command = [
        "gdal_translate",
        "-of",
        "AAIGrid",
        "-projwin",
        f"{extent['xmin']}",
        f"{extent['ymax']}",
        f"{extent['xmax']}",
        f"{extent['ymin']}",
        str(raw_terrain_path),
        str(terrain_output_path),
    ]
    run_gdal_translate(gdal_translate_command)

    shutil.copy2(source_zone_metadata_path, source_zone_output_path)
    if aoi_tile_catalog_path is not None:
        shutil.copy2(aoi_tile_catalog_path, output_input_root / "aoi_tile_catalog.yaml")

    terrain_metadata = build_restaged_terrain_metadata(
        template_path=terrain_metadata_template_path,
        terrain_output_path=terrain_output_path,
        raw_terrain_path=raw_terrain_path,
        extent=extent,
        gdal_translate_command=gdal_translate_command,
    )
    terrain_metadata_path.write_text(yaml.safe_dump(terrain_metadata, sort_keys=False), encoding="utf-8")

    diagnostic_report = DIAGNOSTIC.build_report(
        repo_root=repo_root,
        terrain_crop_path=terrain_output_path,
        terrain_metadata_path=terrain_metadata_path,
        source_zone_metadata_path=source_zone_output_path,
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "restage_status": "ready",
        "repo_root": str(repo_root),
        "output_root": str(output_root),
        "terrain_crop_path": display_path(terrain_output_path, repo_root),
        "terrain_metadata_path": display_path(terrain_metadata_path, repo_root),
        "source_zone_metadata_path": display_path(source_zone_output_path, repo_root),
        "aoi_tile_catalog_path": display_path(output_input_root / "aoi_tile_catalog.yaml", repo_root)
        if (output_input_root / "aoi_tile_catalog.yaml").exists()
        else None,
        "restaging_command": "PYENV_VERSION=system uv run python scripts/stage_management_aoi_restaged_terrain.py "
        f"--output-root {output_root}",
        "gdal_translate_command": " ".join(gdal_translate_command),
        "restaged_terrain_extent_lv95_m": extent,
        "restaged_terrain_metadata": {
            "checksum_sha256": DIAGNOSTIC.PLANNER.sha256_file(terrain_output_path),
            "raw_checksum_sha256": DIAGNOSTIC.PLANNER.sha256_file(raw_terrain_path),
            "terrain_cell_count": int(extent["cell_count"]),
        },
        "diagnostic": diagnostic_report,
        "first_blocker": diagnostic_report.get("first_blocker", {}),
        "terrain_screening_decomposition": diagnostic_report.get("terrain_screening_decomposition", {}),
        "claim_boundaries": {
            "restaging_only": True,
            "diagnostic_only": diagnostic_report.get("claim_boundaries", {}).get("diagnostic_only", False),
            "threshold_tuning_performed": False,
            "validated_release_zone_evidence": False,
            "scenario_generation_authorized": False,
            "hazard_execution_authorized": False,
            "scale_up_authorized": False,
            "operational_claims_allowed": False,
        },
    }


def run_gdal_translate(command: list[str]) -> None:
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
    except FileNotFoundError as exc:  # pragma: no cover - environment setup.
        raise RuntimeError("gdal_translate is required to restage the management AOI terrain") from exc
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.strip() if exc.stderr else ""
        raise RuntimeError(f"gdal_translate failed: {stderr or exc}") from exc


def derive_raw_dataset_extent(raw_terrain_path: Path) -> dict[str, float | int]:
    try:
        result = subprocess.run(
            ["gdalinfo", "-json", str(raw_terrain_path)],
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:  # pragma: no cover - environment setup.
        raise RuntimeError("gdalinfo is required to inspect the raw management AOI tile") from exc
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.strip() if exc.stderr else ""
        raise RuntimeError(f"gdalinfo failed: {stderr or exc}") from exc

    payload = json.loads(result.stdout)
    size = payload.get("size") or []
    transform = payload.get("geoTransform") or []
    if len(size) != 2 or len(transform) != 6:
        raise RuntimeError(f"unable to derive raw dataset extent from {raw_terrain_path}")

    width = int(size[0])
    height = int(size[1])
    origin_x = float(transform[0])
    pixel_width = float(transform[1])
    origin_y = float(transform[3])
    pixel_height = float(transform[5])
    xmax = origin_x + width * pixel_width
    ymin = origin_y + height * pixel_height
    if pixel_width <= 0 or pixel_height >= 0:
        raise RuntimeError(f"unexpected geotransform for {raw_terrain_path}")
    return {
        "xmin": origin_x,
        "ymin": ymin,
        "xmax": xmax,
        "ymax": origin_y,
        "width_px": width,
        "height_px": height,
        "cellsize_m": abs(pixel_width),
        "cell_count": width * height,
    }


def build_restaged_terrain_metadata(
    *,
    template_path: Path | None,
    terrain_output_path: Path,
    raw_terrain_path: Path,
    extent: dict[str, float | int],
    gdal_translate_command: list[str],
) -> dict[str, Any]:
    template = yaml.safe_load(template_path.read_text(encoding="utf-8")) if template_path is not None else {}
    template = template if isinstance(template, dict) else {}
    checksum = DIAGNOSTIC.PLANNER.sha256_file(terrain_output_path)
    raw_checksum = DIAGNOSTIC.PLANNER.sha256_file(raw_terrain_path)
    crop_extent = {
        "xmin": float(extent["xmin"]),
        "ymin": float(extent["ymin"]),
        "xmax": float(extent["xmax"]),
        "ymax": float(extent["ymax"]),
    }
    width_px = int(extent["width_px"])
    height_px = int(extent["height_px"])
    cellsize_m = float(extent["cellsize_m"])
    metadata = {
        **template,
        "checksum_sha256": checksum,
        "raw_checksum": raw_checksum,
        "processed_checksum": checksum,
        "crs": "EPSG:2056",
        "resolution_m": cellsize_m,
        "crop_extent_lv95_m": crop_extent,
        "extent_lv95_m": crop_extent,
        "raster": {
            **(template.get("raster") or {}),
            "format": "ESRI ASCII GRID",
            "resolution_m": cellsize_m,
            "width_px": width_px,
            "height_px": height_px,
            "nodata": -9999.0,
        },
        "preprocessing_command_and_timestamp": " ".join(gdal_translate_command),
        "staged_path": str(terrain_output_path),
        "metadata_path": str(terrain_output_path.parent / "terrain_metadata.yaml"),
        "provenance_classification": "real_staged",
        "coordinate_reference_system": {
            "epsg": 2056,
            "horizontal_crs": "LV95",
            "vertical_datum": "LN02",
        },
        "preprocessing": {
            "crop_extent_lv95_m": crop_extent,
            "command": " ".join(gdal_translate_command),
        },
    }
    return metadata


def render_text_report(report: dict[str, Any]) -> str:
    diagnostic = report.get("diagnostic", {}) or {}
    first_blocker = diagnostic.get("first_blocker", {}) or {}
    decomposition = diagnostic.get("terrain_screening_decomposition", {}) or {}
    lines = [
        "Management AOI Terrain Restage",
        f"restage_status: `{report.get('restage_status')}`",
        f"terrain_crop_path: {report.get('terrain_crop_path')}",
        f"source_zone_metadata_path: {report.get('source_zone_metadata_path')}",
        f"screenable_cell_count: `{decomposition.get('screenable_cell_count')}`",
        f"candidate_cell_count: `{diagnostic.get('candidate_cell_count')}`",
        f"first_blocker: `{first_blocker.get('blocker_id')}`",
        f"diagnostic_status: `{diagnostic.get('diagnostic_status')}`",
        f"restaging_command: {report.get('restaging_command')}",
        f"gdal_translate_command: {report.get('gdal_translate_command')}",
    ]
    return "\n".join(lines)


def resolve_path(repo_root: Path, path: Path) -> Path:
    if path.is_absolute():
        return path.resolve(strict=False)
    return (repo_root / path).resolve(strict=False)


def display_path(path: Path, repo_root: Path) -> str:
    try:
        return str(path.resolve(strict=False).relative_to(repo_root.resolve(strict=False)))
    except ValueError:
        return str(path.resolve(strict=False))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
