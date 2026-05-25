"""Small manifest helpers shared by hazard-output builders."""

from __future__ import annotations

import json
import math
import time
from pathlib import Path
from typing import Any

from scripts.hazard_output_writers import sha256_file
from scripts.hazard_output_writers import write_file_text


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


def execution_sidecar_manifest_entries(
    *,
    execution_plan_path: Path,
    execution_index_path: Path,
    merge_state_path: Path,
    chunk_manifest_paths: list[Path] | tuple[Path, ...],
    kind_prefix: str,
    output_file_metadata: dict[Path, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    entries = [
        output_manifest_entry(
            execution_plan_path,
            f"{kind_prefix}_execution_plan",
            "json",
            output_file_metadata=output_file_metadata,
        ),
        output_manifest_entry(
            execution_index_path,
            f"{kind_prefix}_execution_index",
            "json",
            output_file_metadata=output_file_metadata,
        ),
        output_manifest_entry(
            merge_state_path,
            f"{kind_prefix}_merge_state",
            "json",
            output_file_metadata=output_file_metadata,
        ),
    ]
    entries.extend(
        output_manifest_entry(
            chunk_manifest_path,
            f"{kind_prefix}_chunk_manifest",
            "json",
            output_file_metadata=output_file_metadata,
        )
        for chunk_manifest_path in chunk_manifest_paths
    )
    return entries


def hazard_map_package_manifest_section(
    map_package: Any,
    probability: Any,
) -> dict[str, Any] | None:
    if map_package is None:
        return None
    scenario_rows = getattr(map_package, "scenario_rows", ())
    scenario_weights = [getattr(row, "sampling_weight", 0.0) for row in scenario_rows]
    config = map_package.config
    return {
        "schema_version": "map_package_manifest_v1",
        "map_product_id": config.map_product_id,
        "probability_mode": config.probability_mode,
        "normalization_scope": config.normalization_scope,
        "source_zone_id": map_package.source_zone_id,
        "source_zone_metadata_path": str(config.source_zone_metadata_path),
        "scenario_table_path": str(config.scenario_table_path) if config.scenario_table_path else None,
        "scenario_ids": list(getattr(map_package, "scenario_ids", ())),
        "total_sampling_weight": math.fsum(scenario_weights) if scenario_weights else None,
        "total_filtered_weight": probability.total_filtered_weight if probability else None,
        "annual_frequency_fields_present": False,
        "operational_status": "research_diagnostic",
    }


def map_package_output_path(map_package: Any, output_dir: Path, prefix: str) -> Path:
    return map_package.config.map_package_manifest_json or output_dir / f"{prefix}_map_package_manifest.json"


def write_map_package_manifest(
    path: Path,
    map_package: Any,
    hazard_manifest_path: Path,
    layer_semantics: list[dict[str, Any]],
    raster_outputs: list[dict[str, Any]],
    output_file_metadata: dict[Path, dict[str, Any]],
    output_write_kind_seconds: dict[str, float],
    output_write_kind_bytes: dict[str, int],
) -> float:
    limitations = list(map_package.config.limitations) or [
        "Research diagnostic; not operational hazard validation.",
        "No annual frequency model is implemented in Phase 1.",
        "Physical occurrence probabilities, exposure, vulnerability, and risk are out of scope.",
    ]
    manifest = {
        "schema_version": "map_package_manifest_v1",
        "map_product_id": map_package.config.map_product_id,
        "map_product_version": "map_package_v1",
        "probability_mode": map_package.config.probability_mode,
        "normalization_scope": map_package.config.normalization_scope,
        "source_zone_id": map_package.source_zone_id,
        "source_zone_metadata_path": str(map_package.config.source_zone_metadata_path),
        "scenario_table_path": str(map_package.config.scenario_table_path)
        if map_package.config.scenario_table_path
        else None,
        "hazard_manifest_paths": [str(hazard_manifest_path)],
        "raster_outputs": raster_outputs,
        "layer_semantics": [
            {
                "layer_name": semantic["layer_name"],
                "units": semantic["units"],
                "conditioned_on": semantic["conditioned_on"],
                "is_annualized": False,
                "numerator": semantic["numerator"],
                "denominator": semantic["denominator"],
                "weighted": semantic["weighted"],
            }
            for semantic in layer_semantics
        ],
        "validation_context": list(map_package.config.validation_context),
        "limitations": limitations,
        "operational_status": "research_diagnostic",
    }
    serialization_started = time.perf_counter()
    text = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    serialization_seconds = time.perf_counter() - serialization_started
    write_file_text(
        path,
        text,
        "json",
        output_file_metadata,
        output_write_kind_seconds,
        output_write_kind_bytes,
        elapsed_seconds=0.0,
    )
    return serialization_seconds
