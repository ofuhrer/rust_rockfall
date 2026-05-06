#!/usr/bin/env python3
"""Prepare a lightweight public Chant Sura benchmark manifest.

This script records the checked-in Chant Sura trajectory/contact fixtures as a
standard public benchmark package. It does not download the large EnviDat raw
archives and it does not generate tuned validation cases.
"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_ROOT = ROOT / "validation" / "results" / "public_benchmarks" / "chant_sura"
PROCESSED_DIR = ROOT / "data" / "processed" / "chant_sura_2020"
VALIDATION_PROCESSED_DIR = ROOT / "validation" / "data" / "processed" / "chant_sura_2020"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument(
        "--allow-missing",
        action="store_true",
        help="write a metadata-only manifest even if checked-in fixtures are missing",
    )
    args = parser.parse_args()

    output_root = resolve_path(args.output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    required_files = [
        PROCESSED_DIR / "release_points.csv",
        PROCESSED_DIR / "observed_trajectories.csv",
        PROCESSED_DIR / "terrain_rf16_contact.asc",
        PROCESSED_DIR / "release_points_contact_extended.csv",
        PROCESSED_DIR / "observed_trajectories_contact_extended.csv",
        PROCESSED_DIR / "observed_contact_events_extended.csv",
        PROCESSED_DIR / "metadata_contact_split.json",
        VALIDATION_PROCESSED_DIR / "release_points_contact_heldout.csv",
        VALIDATION_PROCESSED_DIR / "observed_trajectories_contact_heldout.csv",
        VALIDATION_PROCESSED_DIR / "observed_contact_events_heldout.csv",
    ]
    missing = [path for path in required_files if not path.exists()]
    if missing and not args.allow_missing:
        formatted = "\n".join(f"  - {path.relative_to(ROOT)}" for path in missing)
        raise SystemExit(f"missing Chant Sura processed fixtures:\n{formatted}")

    manifest = {
        "schema_version": "public_benchmark_preparation_manifest_v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "benchmark_id": "chant_sura",
        "dataset_id": "chant_sura_2020",
        "status": "fixture_backed_manifest",
        "public_source": {
            "title": "Induced Rockfall Dataset #2 (Chant Sura Experimental Campaign), Flüelapass, Grisons, Switzerland",
            "doi": "https://doi.org/10.16904/envidat.174",
            "source_url": "https://www.envidat.ch/metadata/induced-rockfall-dataset-chant-sura",
            "license": "WSL Data Policy",
        },
        "scientific_role": [
            "trajectory/contact validation",
            "impact timing and rebound proxy validation",
            "energy and jump-height evolution diagnostics",
        ],
        "processed_inputs": [file_summary(path) for path in required_files],
        "fixture_counts": {
            "first_flight_release_rows": csv_row_count(PROCESSED_DIR / "release_points.csv"),
            "first_flight_trajectory_rows": csv_row_count(PROCESSED_DIR / "observed_trajectories.csv"),
            "extended_release_rows": csv_row_count(PROCESSED_DIR / "release_points_contact_extended.csv"),
            "extended_trajectory_rows": csv_row_count(PROCESSED_DIR / "observed_trajectories_contact_extended.csv"),
            "extended_contact_event_rows": csv_row_count(PROCESSED_DIR / "observed_contact_events_extended.csv"),
            "heldout_release_rows": csv_row_count(VALIDATION_PROCESSED_DIR / "release_points_contact_heldout.csv"),
            "heldout_trajectory_rows": csv_row_count(VALIDATION_PROCESSED_DIR / "observed_trajectories_contact_heldout.csv"),
            "heldout_contact_event_rows": csv_row_count(VALIDATION_PROCESSED_DIR / "observed_contact_events_heldout.csv"),
        },
        "validation_cases": [
            "validation/cases/chant_sura_trajectory_subset.yaml",
            "validation/cases/chant_sura_contact.yaml",
            "validation/cases/chant_sura_contact_extended.yaml",
            "validation/cases/chant_sura_contact_heldout.yaml",
        ],
        "qa_checks": [
            "processed fixture files exist",
            "model-selection and held-out trajectory IDs are disjoint",
            "large raw EnviDat archives are not committed",
        ],
        "limitations": [
            "Small RF16 contact fixtures do not validate full runout or deposition.",
            "Segment boundaries are contact/rebound proxies, not exact impact observations.",
            "EOTA shape data remain passive metadata under current spherical dynamics.",
        ],
    }
    split_path = PROCESSED_DIR / "metadata_contact_split.json"
    if split_path.exists():
        manifest["contact_split"] = json.loads(split_path.read_text())

    manifest_path = output_root / "preparation_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(f"wrote Chant Sura benchmark manifest to {manifest_path}")
    return 0


def resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def csv_row_count(path: Path) -> int | None:
    if not path.exists():
        return None
    with path.open(newline="") as file:
        reader = csv.reader(file)
        return max(0, sum(1 for _ in reader) - 1)


def file_summary(path: Path) -> dict[str, Any]:
    exists = path.exists()
    return {
        "path": str(path.relative_to(ROOT)),
        "exists": exists,
        "bytes": path.stat().st_size if exists else None,
        "tracked_fixture": exists and is_tracked(path),
    }


def is_tracked(path: Path) -> bool:
    import subprocess

    result = subprocess.run(
        ["git", "ls-files", "--error-unmatch", str(path.relative_to(ROOT))],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0


if __name__ == "__main__":
    raise SystemExit(main())
