"""Shared output-family accounting helpers for local pressure reports."""

from __future__ import annotations

from pathlib import Path


def classify_storage_path_family(path: str | Path) -> str:
    """Classify an output path into the storage-pressure family vocabulary."""
    path = Path(path)
    name = path.name.lower()
    suffix = path.suffix.lower()
    if "scenario_table" in name:
        return "scenario_table"
    if "release" in name or "source_zone_metadata" in name or "source_scenario_policy" in name:
        return "release_plan"
    if "trajectory_metadata" in name:
        return "trajectory_metadata"
    if "trajectory" in name:
        return "trajectory"
    if "deposition" in name:
        return "deposition"
    if "impact" in name:
        return "impact_events"
    if "metrics" in name or "scaling_summary" in name or "diagnostic" in name:
        return "diagnostics"
    if "manifest" in name:
        return "manifest"
    if suffix in {".tif", ".tiff", ".asc", ".geojson", ".gpkg", ".qml", ".sld"}:
        return "gis"
    if "chunk" in name:
        return "chunk_metadata"
    return suffix.lstrip(".") or "other"
