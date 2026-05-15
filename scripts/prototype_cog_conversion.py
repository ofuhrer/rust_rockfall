#!/usr/bin/env python3
"""Prototype a bounded GeoTIFF-to-COG conversion on an explicit scratch path.

This helper is read-only with respect to committed artifact roots. It accepts an
input GeoTIFF, writes the converted output only to an explicit destination
(`--output`) or a `/tmp` default, and verifies the result with `gdalinfo`.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def build_translate_command(input_path: Path, output_path: Path) -> list[str]:
    return [
        "gdal_translate",
        "-of",
        "COG",
        "-co",
        "BLOCKSIZE=256",
        "-co",
        "COMPRESS=ZSTD",
        str(input_path),
        str(output_path),
    ]


def build_gdalinfo_command(path: Path) -> list[str]:
    return ["gdalinfo", "-json", str(path)]


def inspect_gdalinfo(path: Path) -> dict[str, Any] | None:
    if shutil.which("gdalinfo") is None:
        return None
    try:
        completed = subprocess.run(
            build_gdalinfo_command(path),
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        return {
            "status": "verification_failed",
            "error": (exc.stderr or exc.stdout or str(exc)).strip(),
        }
    data = json.loads(completed.stdout)
    band = data.get("bands", [{}])[0]
    image_structure = data.get("metadata", {}).get("IMAGE_STRUCTURE", {})
    return {
        "status": "ok",
        "driver": data.get("driverShortName"),
        "size": data.get("size"),
        "geo_transform": data.get("geoTransform"),
        "block_size": band.get("block"),
        "nodata": band.get("noDataValue"),
        "overview_count": len(band.get("overviews", [])),
        "image_structure": image_structure,
        "sample_raster_tiled": bool(
            band.get("block")
            and isinstance(data.get("size"), list)
            and len(data["size"]) == 2
            and band["block"][0] < data["size"][0]
            and band["block"][1] < data["size"][1]
        ),
        "sample_raster_overviews": len(band.get("overviews", [])) > 0,
        "sample_raster_cog_layout": image_structure.get("LAYOUT") == "COG",
    }


def convert_to_cog(
    input_path: Path,
    output_path: Path,
    *,
    overwrite: bool = False,
) -> dict[str, Any]:
    if not input_path.exists():
        return {
            "status": "blocked_missing_inputs",
            "input_path": str(input_path),
            "output_path": str(output_path),
            "command": build_translate_command(input_path, output_path),
            "verification": None,
            "error": f"missing input raster: {input_path}",
        }
    if output_path.exists() and not overwrite:
        return {
            "status": "blocked_missing_inputs",
            "input_path": str(input_path),
            "output_path": str(output_path),
            "command": build_translate_command(input_path, output_path),
            "verification": None,
            "error": f"output exists and overwrite is disabled: {output_path}",
        }
    if shutil.which("gdal_translate") is None or shutil.which("gdalinfo") is None:
        return {
            "status": "blocked_missing_gdal",
            "input_path": str(input_path),
            "output_path": str(output_path),
            "command": build_translate_command(input_path, output_path),
            "verification": None,
            "error": "gdal_translate/gdalinfo not available on PATH",
        }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    command = build_translate_command(input_path, output_path)
    try:
        completed = subprocess.run(command, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as exc:
        return {
            "status": "conversion_failed",
            "input_path": str(input_path),
            "output_path": str(output_path),
            "command": command,
            "stdout": exc.stdout,
            "stderr": exc.stderr,
            "verification": None,
            "error": (exc.stderr or exc.stdout or str(exc)).strip(),
        }

    verification = inspect_gdalinfo(output_path)
    if verification is None:
        return {
            "status": "blocked_missing_gdal",
            "input_path": str(input_path),
            "output_path": str(output_path),
            "command": command,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "verification": None,
            "error": "gdalinfo unavailable after conversion",
        }
    if verification.get("status") != "ok":
        return {
            "status": verification.get("status", "verification_failed"),
            "input_path": str(input_path),
            "output_path": str(output_path),
            "command": command,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "verification": verification,
            "error": verification.get("error", "verification failed"),
        }

    status = "cog_conversion_sample_ready" if verification["sample_raster_tiled"] and verification["sample_raster_overviews"] and verification["sample_raster_cog_layout"] else "verification_failed"
    return {
        "status": status,
        "input_path": str(input_path),
        "output_path": str(output_path),
        "command": command,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "verification": verification,
        "output_exists": output_path.exists(),
        "output_bytes": output_path.stat().st_size if output_path.exists() else 0,
        "blockers": []
        if status == "cog_conversion_sample_ready"
        else [
            blocker
            for blocker, ok in (
                ("sample_raster_not_tiled", verification.get("sample_raster_tiled")),
                ("sample_raster_no_overviews", verification.get("sample_raster_overviews")),
                ("sample_raster_not_cog_layout", verification.get("sample_raster_cog_layout")),
            )
            if not ok
        ],
    }


def default_output_path(input_path: Path) -> Path:
    return Path("/tmp") / f"{input_path.stem}_cog_poc.tif"


def render_text(report: dict[str, Any]) -> str:
    lines = [
        f"status\t{report['status']}",
        f"input_path\t{report['input_path']}",
        f"output_path\t{report['output_path']}",
        f"command\t{' '.join(report['command'])}",
        f"output_exists\t{report.get('output_exists', False)}",
        f"output_bytes\t{report.get('output_bytes', 0)}",
    ]
    verification = report.get("verification") or {}
    if verification:
        lines.append(f"verification\t{verification}")
    if report.get("blockers"):
        lines.append(f"blockers\t{report['blockers']}")
    return "\n".join(lines) + "\n"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="input GeoTIFF to convert")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="explicit COG output path; defaults to /tmp/<input-stem>_cog_poc.tif",
    )
    parser.add_argument("--overwrite", action="store_true", help="overwrite existing output path if present")
    parser.add_argument("--format", choices=("json", "text"), default="json")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    output_path = args.output or default_output_path(args.input)
    report = convert_to_cog(args.input, output_path, overwrite=args.overwrite)
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text(report))
    return 0 if report["status"] == "cog_conversion_sample_ready" else 2 if report["status"].startswith("blocked_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
