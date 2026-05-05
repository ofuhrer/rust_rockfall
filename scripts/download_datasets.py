#!/usr/bin/env python3
"""Download public dataset resources listed in data/datasets.yaml.

The script intentionally downloads only requested public resources. It preserves
original filenames under data/raw/<dataset_id>/ and writes a manifest with source
URL, download timestamp, size, and SHA-256 checksum.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data" / "datasets.yaml"


def load_yaml(path: Path) -> dict:
    try:
        import yaml  # type: ignore
    except ImportError as exc:
        raise SystemExit(
            "PyYAML is required for dataset downloads. Install with `python3 -m pip install PyYAML`."
        ) from exc
    return yaml.safe_load(path.read_text())


def registry_index(registry: dict) -> dict[str, dict]:
    return {dataset["id"]: dataset for dataset in registry.get("datasets", [])}


def resource_index(dataset: dict) -> dict[str, dict]:
    return {resource["id"]: resource for resource in dataset.get("resources", [])}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download(url: str, destination: Path, overwrite: bool) -> None:
    if destination.exists() and not overwrite:
        print(f"skip existing {destination}")
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    print(f"download {url}")
    with urllib.request.urlopen(url, timeout=120) as response, destination.open("wb") as out:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            out.write(chunk)


def write_manifest(dataset: dict, resource: dict, destination: Path) -> None:
    manifest_path = destination.parent / "download_manifest.jsonl"
    record = {
        "dataset_id": dataset["id"],
        "dataset_name": dataset["name"],
        "resource_id": resource["id"],
        "resource_name": resource["name"],
        "source_url": resource["url"],
        "doi": dataset.get("doi"),
        "license": dataset.get("license"),
        "downloaded_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "local_file": str(destination.relative_to(ROOT)),
        "size_bytes": destination.stat().st_size,
        "sha256": sha256_file(destination),
    }
    with manifest_path.open("a") as file:
        file.write(json.dumps(record, sort_keys=True) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", required=True, help="dataset id from data/datasets.yaml")
    parser.add_argument(
        "--resource",
        action="append",
        help="resource id to download; may be repeated. Defaults to all resources for the dataset.",
    )
    parser.add_argument("--overwrite", action="store_true", help="overwrite existing raw files")
    args = parser.parse_args()

    registry = load_yaml(REGISTRY)
    datasets = registry_index(registry)
    if args.dataset not in datasets:
        raise SystemExit(f"unknown dataset id {args.dataset!r}")
    dataset = datasets[args.dataset]
    resources = resource_index(dataset)
    selected_ids = args.resource or list(resources)
    if not selected_ids:
        print(f"dataset {args.dataset} has no downloadable resources")
        return 0

    for resource_id in selected_ids:
        if resource_id not in resources:
            raise SystemExit(f"unknown resource id {resource_id!r} for dataset {args.dataset!r}")
        resource = resources[resource_id]
        raw_file = resource.get("raw_file") or Path(resource["url"]).name
        destination = ROOT / dataset["local_path"] / raw_file
        download(resource["url"], destination, args.overwrite)
        write_manifest(dataset, resource, destination)

    return 0


if __name__ == "__main__":
    sys.exit(main())

