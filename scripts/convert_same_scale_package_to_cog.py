#!/usr/bin/env python3
"""Convert one ignored same-scale GIS package root into a COG-ready proof.

This helper is intentionally read-only with respect to the source package root.
It copies the selected package into an ignored output root, converts the declared
GeoTIFF rasters to COG layout with GDAL, rewrites output-manifest paths to the
new root, and verifies the converted package with the GIS/COG audit helper.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.prototype_cog_conversion import convert_to_cog


DEFAULT_INPUT_ROOT = ROOT / "hazard/results/tschamut_public_pilot/gate_v1"
DEFAULT_OUTPUT_ROOT = ROOT / "hazard/results/tschamut_public_pilot/gate_v1_cog_poc"


class PackageConversionError(ValueError):
    pass


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-root", type=Path, default=DEFAULT_INPUT_ROOT, help="source same-scale GIS package root")
    parser.add_argument(
        "--output-root",
        type=Path,
        default=DEFAULT_OUTPUT_ROOT,
        help="ignored output root for the converted package",
    )
    parser.add_argument("--overwrite", action="store_true", help="replace an existing output root")
    parser.add_argument("--format", choices=("json", "text"), default="json")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        report = convert_same_scale_package_to_cog(args.input_root, args.output_root, overwrite=args.overwrite)
    except PackageConversionError as exc:
        print(f"package conversion error: {exc}", file=sys.stderr)
        return 2
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text(report))
    status = report.get("status", "")
    return 0 if status == "cog_package_ready" else 2 if status.startswith("blocked_") else 1


def convert_same_scale_package_to_cog(input_root: Path, output_root: Path, *, overwrite: bool = False) -> dict[str, Any]:
    input_root = Path(input_root)
    output_root = Path(output_root)
    input_root_rel = repo_relative(input_root)
    output_root_rel = repo_relative(output_root)
    if not input_root.exists():
        return {
            "status": "blocked_missing_inputs",
            "input_root": str(input_root),
            "output_root": str(output_root),
            "error": f"missing input package root: {input_root}",
            "converted_rasters": [],
            "package_file_count": 0,
            "package_byte_count": 0,
            "copied_files": 0,
        }
    if output_root.exists():
        if not overwrite:
            return {
                "status": "blocked_missing_inputs",
                "input_root": str(input_root),
                "output_root": str(output_root),
                "error": f"output root exists and overwrite is disabled: {output_root}",
                "converted_rasters": [],
                "package_file_count": 0,
                "package_byte_count": 0,
                "copied_files": 0,
            }
        shutil.rmtree(output_root)
    if shutil.which("gdal_translate") is None or shutil.which("gdalinfo") is None:
        return {
            "status": "blocked_missing_gdal",
            "input_root": str(input_root),
            "output_root": str(output_root),
            "error": "gdal_translate/gdalinfo not available on PATH",
            "converted_rasters": [],
            "package_file_count": 0,
            "package_byte_count": 0,
            "copied_files": 0,
        }

    shutil.copytree(input_root, output_root)
    map_manifest_path = discover_single_manifest(output_root, "*map_package_manifest*.json")
    pilot_manifest_path = discover_single_manifest(output_root, "*pilot_gis_package_manifest*.json")
    if map_manifest_path is None or pilot_manifest_path is None:
        shutil.rmtree(output_root, ignore_errors=True)
        return {
            "status": "blocked_missing_inputs",
            "input_root": str(input_root),
            "output_root": str(output_root),
            "error": "missing package manifests in source root copy",
            "converted_rasters": [],
            "package_file_count": 0,
            "package_byte_count": 0,
            "copied_files": 0,
        }

    map_manifest = load_json(map_manifest_path)
    pilot_manifest = load_json(pilot_manifest_path)

    converted_rasters: list[dict[str, Any]] = []
    for raster in map_manifest.get("raster_outputs", []):
        if raster.get("format") != "geotiff":
            continue
        source_path = resolve_repo_path(str(raster.get("path")))
        if source_path is None or not source_path.exists():
            shutil.rmtree(output_root, ignore_errors=True)
            return {
                "status": "blocked_missing_inputs",
                "input_root": str(input_root),
                "output_root": str(output_root),
                "error": f"missing source raster: {raster.get('path')}",
                "converted_rasters": converted_rasters,
                "package_file_count": 0,
                "package_byte_count": 0,
                "copied_files": 0,
            }
        output_path = rewrite_repo_path(str(raster["path"]), input_root_rel, output_root_rel)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.unlink(missing_ok=True)
        converted = convert_to_cog(source_path, output_path, overwrite=True)
        if converted.get("status") != "cog_conversion_sample_ready":
            shutil.rmtree(output_root, ignore_errors=True)
            return {
                "status": "conversion_failed",
                "input_root": str(input_root),
                "output_root": str(output_root),
                "error": f"failed converting {raster.get('path')}: {converted.get('error')}",
                "converted_rasters": converted_rasters,
                "package_file_count": 0,
                "package_byte_count": 0,
                "copied_files": 0,
                "conversion": converted,
            }
        converted_rasters.append(
            {
                "layer_name": raster.get("layer_name"),
                "source_path": str(source_path),
                "output_path": str(output_path),
                "sha256": sha256_file(output_path),
                "total_bytes": output_path.stat().st_size,
                "gdal_status": converted.get("status"),
            }
        )
        raster["cloud_optimized"] = True
        raster["sha256"] = converted_rasters[-1]["sha256"]
        raster["total_bytes"] = converted_rasters[-1]["total_bytes"]
        raster["path"] = str(output_path)

    rewritten_hazard_manifest_paths = [
        str(rewrite_repo_path(path, input_root_rel, output_root_rel))
        for path in map_manifest.get("hazard_manifest_paths", [])
    ]
    map_manifest["hazard_manifest_paths"] = rewritten_hazard_manifest_paths
    pilot_manifest["hazard_manifest_paths"] = list(rewritten_hazard_manifest_paths)
    pilot_manifest.setdefault("visual_qa", {})["status"] = "not-run"
    pilot_manifest["visual_qa"]["accepted_for_operational_use"] = False
    pilot_manifest["raster_contract"]["cloud_optimized"] = True
    pilot_manifest.setdefault("limitations", list(pilot_manifest.get("limitations", [])))
    map_manifest.setdefault("limitations", list(map_manifest.get("limitations", [])))

    map_manifest["cloud_optimized"] = True
    map_manifest["conversion_provenance"] = {
        "input_root": str(input_root),
        "output_root": str(output_root),
        "helper": Path(__file__).name,
        "conversion_mode": "package_copy_and_cog_translate",
    }
    pilot_manifest["conversion_provenance"] = {
        "input_root": str(input_root),
        "output_root": str(output_root),
        "helper": Path(__file__).name,
        "conversion_mode": "package_copy_and_cog_translate",
    }

    dump_json(map_manifest_path, map_manifest)
    dump_json(pilot_manifest_path, pilot_manifest)

    file_count, byte_count = count_files_and_bytes(output_root)
    all_rasters_ready = all_rasters_cog_ready(output_root, map_manifest, pilot_manifest)
    status = "cog_package_ready" if all_rasters_ready else "cog_package_poc_ready"
    return {
        "status": status,
        "input_root": str(input_root),
        "output_root": str(output_root),
        "map_manifest_path": str(map_manifest_path),
        "pilot_manifest_path": str(pilot_manifest_path),
        "converted_rasters": converted_rasters,
        "package_file_count": file_count,
        "package_byte_count": byte_count,
        "copied_files": file_count,
        "ignored_output_root": str(output_root),
        "gdal_translate_options": ["-of", "COG", "-co", "BLOCKSIZE=256", "-co", "COMPRESS=ZSTD"],
        "all_declared_geotiffs_cog_ready": all_rasters_ready,
}


def all_rasters_cog_ready(output_root: Path, map_manifest: dict[str, Any], pilot_manifest: dict[str, Any]) -> bool:
    for raster in map_manifest.get("raster_outputs", []):
        if raster.get("format") != "geotiff":
            continue
        path = resolve_repo_path(str(raster.get("path")))
        if path is None or not path.exists():
            return False
        metadata = inspect_gdal(path)
        if metadata.get("status") != "ok":
            return False
        if not (metadata.get("sample_raster_tiled") and metadata.get("sample_raster_overviews") and metadata.get("sample_raster_cog_layout")):
            return False
        if raster.get("cloud_optimized") is not True:
            return False
    return pilot_manifest.get("raster_contract", {}).get("cloud_optimized") is True


def inspect_gdal(path: Path) -> dict[str, Any]:
    from scripts.prototype_cog_conversion import inspect_gdalinfo

    metadata = inspect_gdalinfo(path)
    return metadata or {"status": "missing_gdal"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def count_files_and_bytes(root: Path) -> tuple[int, int]:
    files = [path for path in root.rglob("*") if path.is_file()]
    return len(files), sum(path.stat().st_size for path in files)


def discover_single_manifest(root: Path, pattern: str) -> Path | None:
    matches = sorted(root.glob(pattern))
    if not matches:
        return None
    if len(matches) > 1:
        raise PackageConversionError(f"multiple manifests matching {pattern!r} under {root}: {matches}")
    return matches[0]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def repo_relative(path: Path) -> Path:
    resolved = path.resolve()
    try:
        return resolved.relative_to(ROOT)
    except ValueError:
        return path


def rewrite_repo_path(raw_path: str, input_root: Path, output_root: Path) -> Path:
    return Path(raw_path.replace(str(input_root), str(output_root)))


def resolve_repo_path(raw_path: str | None) -> Path | None:
    if raw_path is None:
        return None
    path = Path(raw_path)
    return path if path.is_absolute() else ROOT / path


def render_text(report: dict[str, Any]) -> str:
    lines = [
        f"status\t{report['status']}",
        f"input_root\t{report['input_root']}",
        f"output_root\t{report['output_root']}",
        f"package_file_count\t{report.get('package_file_count', 0)}",
        f"package_byte_count\t{report.get('package_byte_count', 0)}",
        f"all_declared_geotiffs_cog_ready\t{report.get('all_declared_geotiffs_cog_ready', False)}",
        f"gdal_translate_options\t{' '.join(report.get('gdal_translate_options', []))}",
    ]
    if report.get("converted_rasters"):
        lines.append(f"converted_rasters\t{len(report['converted_rasters'])}")
    if report.get("error"):
        lines.append(f"error\t{report['error']}")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
