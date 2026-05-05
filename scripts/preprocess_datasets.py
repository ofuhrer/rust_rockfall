#!/usr/bin/env python3
"""Create validation-ready derived files from downloaded public datasets.

This script never overwrites raw data. Dataset-specific scientific conversions are
added incrementally as schemas are stabilized; the current implementation provides
safe archive inventories and regenerates the small synthetic fixture.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def write_synthetic_fixture() -> None:
    for out in (
        ROOT / "data" / "processed" / "synthetic_plane_basic",
        ROOT / "validation" / "data" / "processed" / "synthetic_plane_basic",
    ):
        out.mkdir(parents=True, exist_ok=True)
        write_csv(
            out / "observed_deposition.csv",
            ["trajectory_id", "experiment_id", "x_m", "y_m", "z_m"],
            [["synthetic_plane_001", "synthetic_plane_basic", "0.2", "0.0", "0.5"]],
        )
        write_csv(
            out / "release_points.csv",
            ["trajectory_id", "experiment_id", "x_m", "y_m", "z_m", "vx_mps", "vy_mps", "vz_mps"],
            [["synthetic_plane_001", "synthetic_plane_basic", "0.0", "0.0", "0.5", "1.0", "0.0", "0.0"]],
        )
        write_csv(
            out / "block_metadata.csv",
            ["block_id", "mass_kg", "radius_m", "shape_class"],
            [["synthetic_sphere_001", "10.0", "0.5", "sphere"]],
        )


def write_csv(path: Path, header: list[str], rows: list[list[str]]) -> None:
    with path.open("w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(header)
        writer.writerows(rows)


def inventory_archives(dataset_id: str) -> None:
    raw_dir = ROOT / "data" / "raw" / dataset_id
    processed_dir = ROOT / "data" / "processed" / dataset_id
    validation_id = "tschamut" if dataset_id == "tschamut2014" else dataset_id
    validation_processed_dir = ROOT / "validation" / "data" / "processed" / validation_id
    processed_dir.mkdir(parents=True, exist_ok=True)
    validation_processed_dir.mkdir(parents=True, exist_ok=True)
    records = []
    for archive in sorted(raw_dir.glob("*.zip")):
        with zipfile.ZipFile(archive) as zf:
            for info in zf.infolist():
                records.append(
                    {
                        "archive": str(archive.relative_to(ROOT)),
                        "member": info.filename,
                        "compressed_size": info.compress_size,
                        "size": info.file_size,
                    }
                )
    if records:
        inventory = json.dumps(records, indent=2)
        (processed_dir / "archive_inventory.json").write_text(inventory)
        (validation_processed_dir / "archive_inventory.json").write_text(inventory)
        print(f"wrote {processed_dir / 'archive_inventory.json'}")
        print(f"wrote {validation_processed_dir / 'archive_inventory.json'}")
    else:
        print(f"no ZIP archives found under {raw_dir}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", required=True, help="dataset id or synthetic_plane_basic")
    args = parser.parse_args()

    if args.dataset == "synthetic_plane_basic":
        write_synthetic_fixture()
        print("wrote synthetic fixture")
    else:
        inventory_archives(args.dataset)

    return 0


if __name__ == "__main__":
    sys.exit(main())
