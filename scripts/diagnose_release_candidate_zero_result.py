#!/usr/bin/env python3
"""Diagnose why a terrain release-zone candidate sweep produced no candidates.

This helper is intentionally diagnostic only. It reuses the deterministic
terrain-candidate planner, decomposes the current screenable terrain into slope
bands, footprint exclusions, and bounded sensitivity variants, and names the
first upstream blocker. It does not tune thresholds, accept release zones, or
authorize scenario generation.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SITE_ROOT = ROOT / "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input"
DEFAULT_TERRAIN_CROP = DEFAULT_SITE_ROOT / "terrain.asc"
DEFAULT_TERRAIN_METADATA = DEFAULT_SITE_ROOT / "terrain_metadata.yaml"
DEFAULT_SOURCE_ZONE_METADATA = DEFAULT_SITE_ROOT / "source_zone_metadata.yaml"
SCHEMA_VERSION = "release_candidate_zero_result_diagnostic_v1"


class ReleaseCandidateZeroResultDiagnosticError(ValueError):
    """User-facing diagnostic error."""


def _load_module(module_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load helper module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


PLANNER = _load_module("release_candidate_planner_for_zero_diagnostic", ROOT / "scripts/plan_terrain_release_zone_candidates.py")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--terrain-crop", type=Path, default=DEFAULT_TERRAIN_CROP)
    parser.add_argument("--terrain-metadata", type=Path, default=DEFAULT_TERRAIN_METADATA)
    parser.add_argument("--source-zone-metadata", type=Path, default=DEFAULT_SOURCE_ZONE_METADATA)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    args = parser.parse_args(argv)

    try:
        report = build_report(
            repo_root=args.repo_root,
            terrain_crop_path=args.terrain_crop,
            terrain_metadata_path=args.terrain_metadata,
            source_zone_metadata_path=args.source_zone_metadata,
        )
    except ReleaseCandidateZeroResultDiagnosticError as exc:
        print(f"release candidate zero-result diagnostic error: {exc}", file=sys.stderr)
        return 2

    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps(report, indent=2, sort_keys=True) if args.format == "json" else render_text_report(report))
    return 0 if report["diagnostic_status"] in {"candidates_present", "zero_candidates_diagnosed"} else 2


def build_report(
    *,
    repo_root: Path = ROOT,
    terrain_crop_path: Path = DEFAULT_TERRAIN_CROP,
    terrain_metadata_path: Path = DEFAULT_TERRAIN_METADATA,
    source_zone_metadata_path: Path = DEFAULT_SOURCE_ZONE_METADATA,
) -> dict[str, Any]:
    repo_root = repo_root.resolve(strict=False)
    terrain_crop_path = resolve_path(repo_root, terrain_crop_path)
    terrain_metadata_path = resolve_path(repo_root, terrain_metadata_path)
    source_zone_metadata_path = resolve_path(repo_root, source_zone_metadata_path)
    missing_inputs = [
        display_path(path, repo_root)
        for path in (terrain_crop_path, terrain_metadata_path, source_zone_metadata_path)
        if not path.exists()
    ]
    if missing_inputs:
        return blocked_report(repo_root, terrain_crop_path, terrain_metadata_path, source_zone_metadata_path, missing_inputs)

    planner_report = PLANNER.build_report(
        repo_root=repo_root,
        terrain_crop_path=terrain_crop_path,
        terrain_metadata_path=terrain_metadata_path,
        source_zone_metadata_path=source_zone_metadata_path,
    )
    if planner_report.get("candidate_metrics_status") != "ready":
        return blocked_report(
            repo_root,
            terrain_crop_path,
            terrain_metadata_path,
            source_zone_metadata_path,
            list(planner_report.get("blocked_missing_inputs", [])),
            planner_report=planner_report,
        )

    terrain = PLANNER.read_esri_ascii_grid(terrain_crop_path)
    source_zone_metadata = PLANNER.load_yaml(source_zone_metadata_path)
    terrain_metadata = PLANNER.load_yaml(terrain_metadata_path)
    screening = PLANNER.build_screening_criteria(terrain_metadata, source_zone_metadata)
    terrain_preprocessing = PLANNER.build_terrain_preprocessing_report(
        repo_root=repo_root,
        terrain_crop_path=terrain_crop_path,
        terrain_metadata_path=terrain_metadata_path,
        terrain_catalog_path=terrain_crop_path.parent / "aoi_tile_catalog.yaml"
        if (terrain_crop_path.parent / "aoi_tile_catalog.yaml").exists()
        else None,
    )
    screening.update(PLANNER.build_screening_criteria_from_terrain_package(terrain_preprocessing))
    candidate_mask, terrain_masks = PLANNER.compute_candidate_masks(terrain, source_zone_metadata, screening)

    candidate_count = int(candidate_mask.sum())
    first_blocker = classify_first_blocker(terrain_masks, screening, candidate_count)
    sensitivity = planner_report.get("candidate_sensitivity_report", {})
    variant_counts = [
        {
            "variant_id": row.get("variant_id"),
            "candidate_cell_count": row.get("candidate_cell_count"),
            "candidate_area_m2": row.get("candidate_area_m2"),
            "candidate_slope_min_deg": row.get("candidate_slope_min_deg"),
            "candidate_slope_max_deg": row.get("candidate_slope_max_deg"),
        }
        for row in sensitivity.get("variant_summaries", [])
        if isinstance(row, dict)
    ]
    max_variant_count = max([int(row.get("candidate_cell_count") or 0) for row in variant_counts], default=0)

    return {
        "schema_version": SCHEMA_VERSION,
        "diagnostic_status": "candidates_present" if candidate_count > 0 else "zero_candidates_diagnosed",
        "repo_root": str(repo_root),
        "input_paths": {
            "terrain_crop": display_path(terrain_crop_path, repo_root),
            "terrain_metadata": display_path(terrain_metadata_path, repo_root),
            "source_zone_metadata": display_path(source_zone_metadata_path, repo_root),
        },
        "candidate_metrics_status": planner_report.get("candidate_metrics_status"),
        "candidate_cell_count": candidate_count,
        "candidate_area_m2": candidate_count * (terrain["cellsize"] ** 2),
        "screening_criteria": {
            "slope_algorithm": screening.get("slope_algorithm"),
            "candidate_slope_min_deg": screening.get("candidate_slope_min_deg"),
            "candidate_slope_max_deg": screening.get("candidate_slope_max_deg"),
            "exclude_frozen_release_zone_footprint": screening.get("exclude_frozen_release_zone_footprint"),
            "frozen_release_zone_footprint_buffer_cells": screening.get("frozen_release_zone_footprint_buffer_cells", 0),
        },
        "terrain_screening_decomposition": build_screening_decomposition(terrain, terrain_masks, screening),
        "slope_distribution": build_slope_distribution(terrain_masks),
        "slope_band_counts": build_slope_band_counts(terrain_masks, terrain),
        "excluded_area_summary": planner_report.get("excluded_area_summary", []),
        "frozen_source_zone_footprint": planner_report.get("frozen_source_zone_footprint", {}),
        "candidate_sensitivity_summary": {
            "sensitivity_status": sensitivity.get("sensitivity_status"),
            "variant_count": sensitivity.get("variant_count"),
            "baseline_candidate_cell_count": sensitivity.get("baseline_candidate_cell_count"),
            "union_candidate_cell_count": sensitivity.get("union_candidate_cell_count"),
            "max_variant_candidate_cell_count": max_variant_count,
            "variant_counts": variant_counts,
        },
        "first_blocker": first_blocker,
        "unblock_guidance": build_unblock_guidance(first_blocker, max_variant_count),
        "claim_boundaries": {
            "diagnostic_only": True,
            "threshold_tuning_performed": False,
            "validated_release_zone_evidence": False,
            "scenario_generation_authorized": False,
            "hazard_execution_authorized": False,
            "scale_up_authorized": False,
            "operational_claims_allowed": False,
            "notes": [
                "diagnostic counts explain the current zero-candidate result only",
                "changing thresholds requires a separate review task and must not be represented as validation",
                "no candidate rows or scenario rows are invented by this helper",
            ],
        },
    }


def blocked_report(
    repo_root: Path,
    terrain_crop_path: Path,
    terrain_metadata_path: Path,
    source_zone_metadata_path: Path,
    missing_inputs: list[str],
    *,
    planner_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "diagnostic_status": "blocked_missing_inputs",
        "repo_root": str(repo_root),
        "input_paths": {
            "terrain_crop": display_path(terrain_crop_path, repo_root),
            "terrain_metadata": display_path(terrain_metadata_path, repo_root),
            "source_zone_metadata": display_path(source_zone_metadata_path, repo_root),
        },
        "missing_inputs": missing_inputs,
        "planner_status": (planner_report or {}).get("candidate_metrics_status"),
        "first_blocker": {
            "blocker_id": "missing_inputs",
            "status": "blocked_missing_inputs",
            "reason": "required candidate-diagnostic inputs are missing",
            "missing_inputs": missing_inputs,
        },
        "claim_boundaries": {
            "diagnostic_only": True,
            "threshold_tuning_performed": False,
            "validated_release_zone_evidence": False,
            "scenario_generation_authorized": False,
            "hazard_execution_authorized": False,
            "scale_up_authorized": False,
            "operational_claims_allowed": False,
        },
    }


def build_screening_decomposition(terrain: dict[str, Any], terrain_masks: dict[str, np.ndarray], screening: dict[str, Any]) -> dict[str, Any]:
    cell_area = terrain["cellsize"] ** 2
    screenable = int(terrain_masks["screenable_mask"].sum())
    valid_interior = int(terrain_masks["valid_interior_mask"].sum())
    footprint = int(terrain_masks["footprint_mask"].sum())
    low = int(terrain_masks["low_slope_mask"].sum())
    high = int(terrain_masks["high_slope_mask"].sum())
    candidate = int(terrain_masks["candidate_mask"].sum())
    return {
        "valid_cell_count": int(terrain["valid_mask"].sum()),
        "valid_interior_cell_count": valid_interior,
        "screenable_cell_count": screenable,
        "screenable_area_m2": screenable * cell_area,
        "frozen_footprint_cell_count": footprint,
        "frozen_footprint_area_m2": footprint * cell_area,
        "slope_below_candidate_band_cell_count": low,
        "slope_above_candidate_band_cell_count": high,
        "candidate_band_cell_count": candidate,
        "candidate_slope_min_deg": screening.get("candidate_slope_min_deg"),
        "candidate_slope_max_deg": screening.get("candidate_slope_max_deg"),
        "screenable_fraction_of_valid_interior_cells": fraction(screenable, valid_interior),
        "candidate_fraction_of_screenable_cells": fraction(candidate, screenable),
    }


def build_slope_distribution(terrain_masks: dict[str, np.ndarray]) -> dict[str, float | int | None]:
    slope_values = terrain_masks["slope_deg"][terrain_masks["screenable_mask"]]
    slope_values = slope_values[np.isfinite(slope_values)]
    if slope_values.size == 0:
        return {"status": "no_screenable_slope_values", "count": 0}
    quantiles = {
        f"p{int(q * 100):02d}_deg": float(np.quantile(slope_values, q))
        for q in (0.0, 0.1, 0.25, 0.5, 0.75, 0.9, 0.95, 0.99, 1.0)
    }
    return {
        "status": "ready",
        "count": int(slope_values.size),
        "mean_deg": float(np.mean(slope_values)),
        "median_deg": float(np.median(slope_values)),
        **quantiles,
    }


def build_slope_band_counts(terrain_masks: dict[str, np.ndarray], terrain: dict[str, Any]) -> list[dict[str, Any]]:
    slope = terrain_masks["slope_deg"]
    screenable = terrain_masks["screenable_mask"] & np.isfinite(slope)
    cell_area = terrain["cellsize"] ** 2
    bands = [(0, 10), (10, 20), (20, 25), (25, 30), (30, 35), (35, 45), (45, 55), (55, 65), (65, 90)]
    rows: list[dict[str, Any]] = []
    denominator = int(screenable.sum())
    for lower, upper in bands:
        mask = screenable & (slope >= lower) & (slope < upper if upper < 90 else slope <= upper)
        count = int(mask.sum())
        rows.append(
            {
                "band_id": f"{lower}_{upper}_deg",
                "slope_min_deg": lower,
                "slope_max_deg": upper,
                "screenable_cell_count": count,
                "area_m2": count * cell_area,
                "fraction_of_screenable_cells": fraction(count, denominator),
            }
        )
    return rows


def classify_first_blocker(terrain_masks: dict[str, np.ndarray], screening: dict[str, Any], candidate_count: int) -> dict[str, Any]:
    if candidate_count > 0:
        return {
            "blocker_id": "none",
            "status": "candidates_present",
            "reason": "the selected inputs produce at least one candidate cell",
        }
    screenable = int(terrain_masks["screenable_mask"].sum())
    if screenable == 0:
        return {
            "blocker_id": "no_screenable_cells",
            "status": "blocked_empty_candidate_set",
            "reason": "no valid interior cells remain after nodata, incomplete-neighborhood, and frozen-footprint exclusions",
        }
    slope_values = terrain_masks["slope_deg"][terrain_masks["screenable_mask"]]
    slope_values = slope_values[np.isfinite(slope_values)]
    if slope_values.size == 0:
        return {
            "blocker_id": "no_screenable_slope_values",
            "status": "blocked_empty_candidate_set",
            "reason": "screenable cells exist but no finite slope values were computed",
        }
    min_slope = float(screening.get("candidate_slope_min_deg", PLANNER.MIN_CANDIDATE_SLOPE_DEG))
    max_slope = float(screening.get("candidate_slope_max_deg", PLANNER.MAX_CANDIDATE_SLOPE_DEG))
    slope_max = float(np.max(slope_values))
    slope_min = float(np.min(slope_values))
    if slope_max < min_slope:
        return {
            "blocker_id": "all_screenable_slopes_below_candidate_band",
            "status": "blocked_empty_candidate_set",
            "reason": f"all screenable slopes are below the candidate band minimum of {min_slope} degrees",
            "screenable_slope_max_deg": slope_max,
            "candidate_slope_min_deg": min_slope,
        }
    if slope_min > max_slope:
        return {
            "blocker_id": "all_screenable_slopes_above_candidate_band",
            "status": "blocked_empty_candidate_set",
            "reason": f"all screenable slopes are above the candidate band maximum of {max_slope} degrees",
            "screenable_slope_min_deg": slope_min,
            "candidate_slope_max_deg": max_slope,
        }
    return {
        "blocker_id": "candidate_band_absent_after_combined_masks",
        "status": "blocked_empty_candidate_set",
        "reason": "screenable slopes straddle the candidate band, but no cell satisfies all deterministic masks simultaneously",
        "screenable_slope_min_deg": slope_min,
        "screenable_slope_max_deg": slope_max,
        "candidate_slope_min_deg": min_slope,
        "candidate_slope_max_deg": max_slope,
    }


def build_unblock_guidance(first_blocker: dict[str, Any], max_variant_count: int) -> dict[str, Any]:
    blocker_id = first_blocker.get("blocker_id")
    if blocker_id == "all_screenable_slopes_below_candidate_band":
        action = "inspect whether the management AOI crop is too flat/small for the current deterministic slope band before considering a separate heuristic-review task"
    elif blocker_id == "all_screenable_slopes_above_candidate_band":
        action = "inspect whether the current upper slope cap excludes the whole AOI before considering a separate heuristic-review task"
    elif blocker_id == "no_screenable_cells":
        action = "inspect AOI extent, nodata, and frozen-footprint overlap before scenario-generation work"
    elif max_variant_count == 0:
        action = "do not continue scenario generation or Balfrin execution until a non-empty candidate package exists"
    else:
        action = "inspect sensitivity variants with non-empty candidates before any review or freeze step"
    return {
        "recommended_next_action": action,
        "scenario_generation_should_remain_blocked": first_blocker.get("status") == "blocked_empty_candidate_set",
        "balfrin_multi_zone_run_should_remain_blocked": first_blocker.get("status") == "blocked_empty_candidate_set",
        "max_variant_candidate_cell_count": max_variant_count,
    }


def render_text_report(report: dict[str, Any]) -> str:
    blocker = report.get("first_blocker", {})
    decomposition = report.get("terrain_screening_decomposition", {})
    sensitivity = report.get("candidate_sensitivity_summary", {})
    lines = [
        "Release Candidate Zero-Result Diagnostic",
        f"diagnostic_status: `{report.get('diagnostic_status')}`",
        f"candidate_cell_count: `{report.get('candidate_cell_count', 0)}`",
        f"first_blocker: `{blocker.get('blocker_id')}`",
        f"first_blocker_reason: {blocker.get('reason')}",
        "",
        "terrain_screening_decomposition:",
        f"- screenable_cell_count: `{decomposition.get('screenable_cell_count')}`",
        f"- slope_below_candidate_band_cell_count: `{decomposition.get('slope_below_candidate_band_cell_count')}`",
        f"- slope_above_candidate_band_cell_count: `{decomposition.get('slope_above_candidate_band_cell_count')}`",
        f"- candidate_band_cell_count: `{decomposition.get('candidate_band_cell_count')}`",
        "",
        "sensitivity:",
        f"- baseline_candidate_cell_count: `{sensitivity.get('baseline_candidate_cell_count')}`",
        f"- union_candidate_cell_count: `{sensitivity.get('union_candidate_cell_count')}`",
        f"- max_variant_candidate_cell_count: `{sensitivity.get('max_variant_candidate_cell_count')}`",
        "",
        f"recommended_next_action: {report.get('unblock_guidance', {}).get('recommended_next_action')}",
    ]
    return "\n".join(lines)


def resolve_path(repo_root: Path, path: Path) -> Path:
    if path.is_absolute():
        return path.resolve(strict=False)
    return (repo_root / path).resolve(strict=False)


def display_path(path: Path, repo_root: Path) -> str:
    try:
        return str(path.resolve(strict=False).relative_to(repo_root.resolve(strict=False)))
    except ValueError:
        return str(path.resolve(strict=False))


def fraction(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return float(numerator) / float(denominator)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
