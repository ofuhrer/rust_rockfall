#!/usr/bin/env python3
"""Prepare a metadata-only Mel de la Niva public benchmark manifest.

The Zenodo dataset is large. This scaffold records the public archives and
local ignored cache paths, but it does not download or preprocess data by
default.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_ROOT = ROOT / "validation" / "results" / "public_benchmarks" / "mel_de_la_niva"
RAW_DIR = ROOT / "data" / "raw" / "mel_de_la_niva_2015"

ARCHIVES = [
    {
        "id": "trajectories",
        "filename": "3d_trajectories_epsg21781_lv03.zip",
        "size_bytes": 166000,
        "md5": "dba538e90510c30eaa8cf9fcbdadad99",
        "role": "reconstructed 3D trajectories in EPSG:21781 / LV03",
    },
    {
        "id": "blocks_3d_shapes",
        "filename": "blocks_3d_shapes.zip",
        "size_bytes": 9100000,
        "md5": "b291875db502a8478a8e6fbecdd08d75",
        "role": "block shape geometry",
    },
    {
        "id": "gis_shapes",
        "filename": "gis_shapes_epsg21781_lv03.zip",
        "size_bytes": 10100000,
        "md5": "b88775690c74aff171f341a3681df4f8",
        "role": "rockfall path segments and deposited-block GIS shapes",
    },
    {
        "id": "sfm_rasters",
        "filename": "sfm_rasters_epsg21781_lv03.zip",
        "size_bytes": 74100000,
        "md5": "a17874b6c82d8739e2eda21455780515",
        "role": "SfM digital surface model and orthophoto rasters",
    },
    {
        "id": "simulation_benchmark",
        "filename": "rockfall_simulation_benchmark.zip",
        "size_bytes": 516300000,
        "md5": "2faf71e9c40a7c31ed8987d931db1791",
        "role": "public simulation benchmark resources for comparison context",
    },
    {
        "id": "videos",
        "filename": "videos_BEG_SA_and_Valais_canton.zip",
        "size_bytes": 488300000,
        "md5": "7fc42e2e2cb4a685ceb3af668656752e",
        "role": "event videos, optional for reconstruction QA",
    },
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument(
        "--require-raw",
        action="store_true",
        help="fail if expected Zenodo archives are not present under data/raw",
    )
    args = parser.parse_args()

    output_root = args.output_root if args.output_root.is_absolute() else ROOT / args.output_root
    output_root.mkdir(parents=True, exist_ok=True)

    archive_status = [archive_summary(item) for item in ARCHIVES]
    missing_required = [item for item in archive_status if not item["exists"]]
    if args.require_raw and missing_required:
        formatted = "\n".join(f"  - {item['path']}" for item in missing_required)
        raise SystemExit(f"missing Mel de la Niva raw archives:\n{formatted}")

    manifest = {
        "schema_version": "public_benchmark_preparation_manifest_v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "benchmark_id": "mel_de_la_niva",
        "dataset_id": "mel_de_la_niva_2015",
        "status": "metadata_only_until_raw_archives_are_downloaded",
        "selected_ids": [],
        "excluded_ids_with_reasons": [],
        "public_source": {
            "title": "Highly energetic rockfalls: Dataset of the 2015 event from the Mel de la Niva, Switzerland",
            "doi": "https://doi.org/10.5281/zenodo.7257979",
            "source_url": "https://zenodo.org/records/7257979",
            "license": "Creative Commons Attribution 4.0 International",
        },
        "scientific_role": [
            "external high-energy/generalization benchmark",
            "trajectory-path and impact-path validation after smaller benchmarks are stable",
            "future block-shape and terrain-interaction stress test",
        ],
        "coordinate_system": "Public archive names indicate EPSG:21781 / LV03 for trajectories, GIS shapes, and SfM rasters.",
        "generated_cases": [],
        "command_provenance": {
            "script": "scripts/prepare_mel_de_la_niva_benchmark.py",
            "require_raw": args.require_raw,
        },
        "provenance": {
            "dataset": "Mel de la Niva 2015 metadata-only benchmark scaffold",
            "doi": "https://doi.org/10.5281/zenodo.7257979",
            "license": "Creative Commons Attribution 4.0 International",
        },
        "raw_cache_policy": {
            "raw_dir": str(RAW_DIR.relative_to(ROOT)),
            "ignored_by_git": True,
            "download_large_archives_by_default": False,
        },
        "archives": archive_status,
        "required_before_runnable_cases": [
            "download selected public Zenodo archives into data/raw/mel_de_la_niva_2015",
            "define CRS strategy: remain in LV03 or transform consistently to LV95/EPSG:2056",
            "derive terrain crop and release/deposition/reference files with checksums",
            "record excluded trajectories or blocks with reproducible reasons",
        ],
        "limitations": [
            "No runnable validation case is generated by this metadata-only scaffold.",
            "The event scale differs from small-block field experiments and must not be used for hidden tuning.",
            "The current simulator lacks dynamic non-spherical shape/contact physics.",
        ],
    }
    manifest_path = output_root / "preparation_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(f"wrote Mel de la Niva benchmark manifest to {manifest_path}")
    return 0


def archive_summary(item: dict[str, Any]) -> dict[str, Any]:
    path = RAW_DIR / item["filename"]
    summary = dict(item)
    summary.update(
        {
            "path": str(path.relative_to(ROOT)),
            "exists": path.exists(),
            "bytes_on_disk": path.stat().st_size if path.exists() else None,
            "download_url": f"https://zenodo.org/records/7257979/files/{item['filename']}?download=1",
        }
    )
    return summary


if __name__ == "__main__":
    raise SystemExit(main())
