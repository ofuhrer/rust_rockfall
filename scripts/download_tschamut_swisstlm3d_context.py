#!/usr/bin/env python3
"""Download or stage swissTLM3D context for the Tschamut public pilot.

The matching swissTLM3D archive is large, so the script is explicit about
download intent. By default it only writes/updates the metadata sidecar used by
the context inspector. Pass --accept-large-download to fetch the archive into
the ignored raw cache, then stage a symlink or copy under the processed context
cache.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import shutil
import sys
import urllib.request
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
SOURCE_URL = (
    "https://data.geo.admin.ch/ch.swisstopo.swisstlm3d/"
    "swisstlm3d_2021-04/swisstlm3d_2021-04_2056_5728.shp.zip"
)
RAW_FILENAME = "swisstlm3d_2021-04_2056_5728.shp.zip"
DEFAULT_RAW_DIR = ROOT / "data/raw/swisstopo/swisstlm3d"
DEFAULT_CONTEXT_DIR = ROOT / "data/processed/swisstopo/tschamut_public_pilot/context/swisstlm3d"
DEFAULT_SCOPE_RECORD = ROOT / "validation/pilot_runs/tschamut_public_obstacle_scope_v1.yaml"
DEFAULT_PILOT_MANIFEST = ROOT / "data/processed/swisstopo/tschamut_public_pilot_manifest.yaml"
LARGE_DOWNLOAD_BYTES = 1_000_000_000


class SwissTlmDownloadError(RuntimeError):
    """User-facing swissTLM3D staging error."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-url", default=SOURCE_URL)
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR)
    parser.add_argument("--context-dir", type=Path, default=DEFAULT_CONTEXT_DIR)
    parser.add_argument("--scope-record", type=Path, default=DEFAULT_SCOPE_RECORD)
    parser.add_argument("--pilot-manifest", type=Path, default=DEFAULT_PILOT_MANIFEST)
    parser.add_argument(
        "--accept-large-download",
        action="store_true",
        help="actually download the large swissTLM3D archive when it is not already present",
    )
    parser.add_argument("--force", action="store_true", help="replace an existing raw archive")
    parser.add_argument(
        "--copy",
        action="store_true",
        help="copy the raw archive into the processed context directory instead of creating a symlink",
    )
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv)

    try:
        report = stage_swisstlm3d_context(
            source_url=args.source_url,
            raw_dir=resolve_path(args.raw_dir),
            context_dir=resolve_path(args.context_dir),
            scope_record=resolve_path(args.scope_record),
            pilot_manifest=resolve_path(args.pilot_manifest),
            accept_large_download=args.accept_large_download,
            force=args.force,
            copy=args.copy,
        )
    except SwissTlmDownloadError as exc:
        print(f"swissTLM3D context download error: {exc}", file=sys.stderr)
        return 2

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text(report))
    return 0 if report["status"] in {"downloaded", "staged_existing", "metadata_only"} else 2


def stage_swisstlm3d_context(
    *,
    source_url: str,
    raw_dir: Path,
    context_dir: Path,
    scope_record: Path,
    pilot_manifest: Path,
    accept_large_download: bool,
    force: bool,
    copy: bool,
) -> dict[str, Any]:
    raw_path = raw_dir / RAW_FILENAME
    context_path = context_dir / RAW_FILENAME
    metadata_path = context_dir / "metadata.json"
    source_head = head_source(source_url)
    content_length = source_head.get("content_length_bytes")
    selected_extent = load_selected_extent(scope_record=scope_record, pilot_manifest=pilot_manifest)

    raw_dir.mkdir(parents=True, exist_ok=True)
    context_dir.mkdir(parents=True, exist_ok=True)

    downloaded = False
    if force and raw_path.exists():
        raw_path.unlink()
    if not raw_path.exists():
        if not accept_large_download:
            metadata = build_metadata(
                source_url=source_url,
                raw_path=raw_path,
                context_path=context_path,
                selected_extent=selected_extent,
                source_head=source_head,
                raw_asset_downloaded=False,
                staged_asset_present=False,
                review_classification="unresolved",
                inspection_rationale=(
                    "Metadata-only unresolved state: pass --accept-large-download to fetch the "
                    "large swissTLM3D archive, then rerun the context inspector."
                ),
            )
            write_json(metadata_path, metadata)
            return {
                "status": "metadata_only",
                "source_url": source_url,
                "raw_path": str(raw_path),
                "context_path": str(context_path),
                "metadata_path": str(metadata_path),
                "content_length_bytes": content_length,
                "download_required": True,
                "accept_large_download_required": bool(content_length and content_length >= LARGE_DOWNLOAD_BYTES),
                "metadata": metadata,
            }
        download(source_url, raw_path, expected_bytes=content_length)
        downloaded = True

    staged = stage_context_asset(raw_path=raw_path, context_path=context_path, copy=copy)
    raw_sha256 = sha256_file(raw_path)
    metadata = build_metadata(
        source_url=source_url,
        raw_path=raw_path,
        context_path=context_path,
        selected_extent=selected_extent,
        source_head=source_head,
        raw_asset_downloaded=True,
        staged_asset_present=True,
        review_classification="limiting",
        inspection_rationale=(
            "Real swissTLM3D archive is staged for roads, hydrography, constructed "
            "features, and barrier/protection context. It remains limiting until "
            "feature classes are clipped or queried for the selected corridor."
        ),
        raw_sha256=raw_sha256,
        staged_method=staged,
    )
    write_json(metadata_path, metadata)
    return {
        "status": "downloaded" if downloaded else "staged_existing",
        "source_url": source_url,
        "raw_path": str(raw_path),
        "context_path": str(context_path),
        "metadata_path": str(metadata_path),
        "content_length_bytes": content_length,
        "raw_size_bytes": raw_path.stat().st_size,
        "raw_sha256": raw_sha256,
        "staged_method": staged,
        "metadata": metadata,
    }


def head_source(url: str) -> dict[str, Any]:
    request = urllib.request.Request(url, method="HEAD")
    with urllib.request.urlopen(request, timeout=120) as response:
        content_length = response.headers.get("Content-Length")
        return {
            "content_length_bytes": int(content_length) if content_length else None,
            "content_type": response.headers.get("Content-Type"),
            "last_modified": response.headers.get("Last-Modified"),
            "etag": response.headers.get("ETag"),
        }


def download(url: str, destination: Path, *, expected_bytes: int | None) -> None:
    temp_path = destination.with_suffix(destination.suffix + ".part")
    print(f"download {url}", file=sys.stderr)
    with urllib.request.urlopen(url, timeout=120) as response, temp_path.open("wb") as out:
        while True:
            chunk = response.read(8 * 1024 * 1024)
            if not chunk:
                break
            out.write(chunk)
    actual_bytes = temp_path.stat().st_size
    if expected_bytes is not None and actual_bytes != expected_bytes:
        temp_path.unlink(missing_ok=True)
        raise SwissTlmDownloadError(
            f"downloaded byte count {actual_bytes} does not match expected {expected_bytes}"
        )
    temp_path.replace(destination)


def stage_context_asset(*, raw_path: Path, context_path: Path, copy: bool) -> str:
    context_path.parent.mkdir(parents=True, exist_ok=True)
    if context_path.exists() or context_path.is_symlink():
        context_path.unlink()
    if copy:
        shutil.copy2(raw_path, context_path)
        return "copy"
    relative_target = Path("../../../../../raw/swisstopo/swisstlm3d") / raw_path.name
    context_path.symlink_to(relative_target)
    return "symlink"


def build_metadata(
    *,
    source_url: str,
    raw_path: Path,
    context_path: Path,
    selected_extent: dict[str, Any],
    source_head: dict[str, Any],
    raw_asset_downloaded: bool,
    staged_asset_present: bool,
    review_classification: str,
    inspection_rationale: str,
    raw_sha256: str | None = None,
    staged_method: str | None = None,
) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "source_product": "swissTLM3D",
        "source_url": source_url,
        "source_tile_ids": ["2021-04"],
        "coordinate_reference_system": {
            "epsg": 2056,
            "horizontal_name": "CH1903+ / LV95",
            "vertical_datum": "LN02",
        },
        "selected_extent_lv95_m": selected_extent.get("extent_lv95_m", {}),
        "raw_asset_path": rel_or_abs(raw_path),
        "local_asset_path": rel_or_abs(context_path),
        "raw_asset_downloaded": raw_asset_downloaded,
        "staged_asset_present": staged_asset_present,
        "raw_asset_head_content_length_bytes": source_head.get("content_length_bytes"),
        "raw_asset_content_type": source_head.get("content_type"),
        "raw_asset_last_modified": source_head.get("last_modified"),
        "raw_asset_etag": source_head.get("etag"),
        "review_classification": review_classification,
        "inspection_rationale": inspection_rationale,
        "spatial_relevance": (
            "Roads, hydrography, constructed features, and protection/barrier context "
            "are expected to be relevant categories for the selected corridor. The "
            "archive must still be clipped or queried before obstacle omission can be accepted."
        ),
        "operational_claims_allowed": False,
        "downloaded_utc": dt.datetime.now(dt.timezone.utc).isoformat() if raw_asset_downloaded else None,
    }
    if raw_sha256 is not None:
        metadata["raw_asset_sha256"] = raw_sha256
        metadata["local_asset_sha256"] = raw_sha256
        metadata["local_asset_bytes"] = raw_path.stat().st_size
    if staged_method is not None:
        metadata["staged_method"] = staged_method
    return metadata


def load_selected_extent(*, scope_record: Path, pilot_manifest: Path) -> dict[str, Any]:
    if pilot_manifest.exists():
        manifest = yaml.safe_load(pilot_manifest.read_text(encoding="utf-8"))
        if isinstance(manifest, dict) and isinstance(manifest.get("selected_domain"), dict):
            return manifest["selected_domain"]
    if scope_record.exists():
        scope = yaml.safe_load(scope_record.read_text(encoding="utf-8"))
        if isinstance(scope, dict) and isinstance(scope.get("selected_domain"), dict):
            return scope["selected_domain"]
    return {}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def render_text(report: dict[str, Any]) -> str:
    lines = [
        f"status: {report['status']}",
        f"source_url: {report['source_url']}",
        f"raw_path: {report['raw_path']}",
        f"context_path: {report['context_path']}",
        f"metadata_path: {report['metadata_path']}",
        f"content_length_bytes: {report.get('content_length_bytes')}",
    ]
    if report["status"] == "metadata_only":
        lines.append("download skipped: rerun with --accept-large-download to fetch the archive")
    else:
        lines.append(f"raw_size_bytes: {report.get('raw_size_bytes')}")
        lines.append(f"raw_sha256: {report.get('raw_sha256')}")
        lines.append(f"staged_method: {report.get('staged_method')}")
    lines.append("")
    lines.append("After download/staging, run:")
    lines.append("UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/inspect_tschamut_public_context_layers.py --format json")
    return "\n".join(lines)


def resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def rel_or_abs(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


if __name__ == "__main__":
    sys.exit(main())
