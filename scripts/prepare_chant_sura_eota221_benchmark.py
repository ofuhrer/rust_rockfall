#!/usr/bin/env python3
"""Prepare a lightweight Chant Sura EOTA221 shape benchmark manifest.

This is a passive shape-metadata scaffold. It records public EOTA shape
metadata already processed into small fixtures, but it does not change dynamics
or generate active shape-contact cases.
"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_ROOT = ROOT / "validation" / "results" / "public_benchmarks" / "chant_sura_eota221"
ROCK_SHAPES_CSV = ROOT / "data" / "processed" / "chant_sura_2020" / "rock_shapes.csv"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument(
        "--allow-missing",
        action="store_true",
        help="write a metadata-only manifest even if rock_shapes.csv is missing",
    )
    args = parser.parse_args()

    output_root = args.output_root if args.output_root.is_absolute() else ROOT / args.output_root
    output_root.mkdir(parents=True, exist_ok=True)

    if not ROCK_SHAPES_CSV.exists() and not args.allow_missing:
        raise SystemExit(f"missing EOTA shape summary fixture: {ROCK_SHAPES_CSV.relative_to(ROOT)}")

    shape_rows = read_shape_rows(ROCK_SHAPES_CSV)
    eota221_rows = [
        row for row in shape_rows if "221" in row.get("shape_file", "") or "221" in row.get("shape_class", "")
    ]
    manifest = {
        "schema_version": "public_benchmark_preparation_manifest_v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "benchmark_id": "chant_sura_eota221",
        "dataset_id": "chant_sura_2020",
        "status": "passive_shape_metadata_manifest",
        "public_source": {
            "title": "Induced Rockfall Dataset #2 (Chant Sura Experimental Campaign), EOTA shape resource",
            "doi": "https://doi.org/10.16904/envidat.174",
            "source_url": "https://www.envidat.ch/metadata/induced-rockfall-dataset-chant-sura",
            "license": "WSL Data Policy",
        },
        "scientific_role": [
            "passive EOTA221 shape/orientation metadata",
            "future shape-contact validation readiness",
            "orientation-sensitive diagnostic planning",
        ],
        "processed_inputs": [file_summary(ROCK_SHAPES_CSV)],
        "shape_summary": {
            "all_shape_rows": shape_rows,
            "eota221_rows": eota221_rows,
            "eota221_row_count": len(eota221_rows),
        },
        "qa_checks": [
            "EOTA221 rows are explicitly separated from EOTA111 rows",
            "shape metadata is passive and must not alter current spherical dynamics",
        ],
        "limitations": [
            "No active non-spherical contact model is implemented.",
            "No shape-dependent restitution, friction, rolling, tumbling, or stopping rule is implemented.",
            "This benchmark is not a contact-model skill claim until active shape physics exists.",
        ],
    }
    manifest_path = output_root / "preparation_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(f"wrote Chant Sura EOTA221 benchmark manifest to {manifest_path}")
    return 0


def read_shape_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="") as file:
        return list(csv.DictReader(file))


def file_summary(path: Path) -> dict[str, Any]:
    exists = path.exists()
    return {
        "path": str(path.relative_to(ROOT)),
        "exists": exists,
        "bytes": path.stat().st_size if exists else None,
    }


if __name__ == "__main__":
    raise SystemExit(main())
