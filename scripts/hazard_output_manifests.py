"""Small manifest helpers shared by hazard-output builders."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from scripts.hazard_output_writers import sha256_file


def output_manifest_entry(
    path: Path,
    kind: str,
    format_name: str,
    *,
    output_file_metadata: dict[Path, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    metadata = output_file_metadata.get(path) if output_file_metadata else None
    total_bytes = metadata.get("total_bytes") if metadata is not None else None
    sha256 = metadata.get("sha256") if metadata is not None else None
    if total_bytes is None:
        total_bytes = path.stat().st_size if path.exists() else 0
    if sha256 is None and path.exists() and path.is_file():
        sha256 = sha256_file(path)
    return {
        "kind": kind,
        "format": format_name,
        "path": str(path),
        "file_count": 1,
        "total_bytes": total_bytes,
        "sha256": sha256,
        "row_count": None,
        "skipped_empty_files": None,
    }


def compact_output_manifest_entry(output: dict[str, Any]) -> dict[str, Any]:
    return {
        "kind": output.get("kind"),
        "format": output.get("format"),
        "path": output.get("path"),
        "sha256": output.get("sha256"),
        "total_bytes": output.get("total_bytes"),
        "layer_name": output.get("layer_name"),
    }


def geotiff_raster_outputs(outputs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    raster_outputs = []
    for output in outputs:
        if output.get("format") != "geotiff":
            continue
        raster_outputs.append(
            {
                "layer_name": output.get("layer_name"),
                "format": output.get("format"),
                "path": output.get("path"),
                "sha256": output.get("sha256"),
                "total_bytes": output.get("total_bytes"),
                "cloud_optimized": bool((output.get("raster") or {}).get("cloud_optimized", False)),
                "annualized": False,
                "is_annualized": False,
            }
        )
    return raster_outputs
