#!/usr/bin/env python3
"""Generate deterministic terrain-driven release-zone candidate metrics.

This helper stays read-only unless an explicit output root is requested. It
uses the committed Tschamut public pilot terrain crop, terrain metadata, and
frozen source-zone metadata to report a fixed heuristic screening over the
Balfrin/Tschamut AOI and can emit deterministic GIS-readable candidate masks
and polygon bundles for dry-run workflows. It can also apply deterministic
review decisions to an emitted review package and validate the edited review
state. It does not emit a validated release zone, tune thresholds, download
public data, or authorize any ensemble work.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
import sys
from itertools import combinations
from pathlib import Path
from typing import Any

import numpy as np

try:
    import yaml  # type: ignore
except ImportError as exc:  # pragma: no cover - environment setup.
    raise SystemExit("PyYAML is required. Run this script with `PYENV_VERSION=system uv run python ...`; CI may use `requirements-tools.txt`") from exc


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "terrain_release_zone_candidate_metrics_v1"
PRODUCT_SCHEMA_VERSION = "terrain_release_zone_candidate_products_v1"
REVIEW_PACKAGE_SCHEMA_VERSION = "terrain_release_zone_candidate_review_package_v1"
REVIEW_APPLICATION_SCHEMA_VERSION = "terrain_release_zone_candidate_review_application_v1"
DEFAULT_TERRAIN_CROP = ROOT / "data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_swissalti3d_crop.asc"
DEFAULT_TERRAIN_METADATA = ROOT / "data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_swissalti3d_metadata.yaml"
DEFAULT_SOURCE_ZONE_METADATA = ROOT / "data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_source_zone_metadata_v1.yaml"
DEFAULT_OUTPUT_MODE = "both"
REVIEW_DECISION_OPTIONS = ("accepted", "rejected", "needs_field_review")
PROVENANCE_LABELS = (
    "workflow_generated",
    "field_supported",
    "mixed_provenance",
    "blocked_missing_provenance",
)

MIN_CANDIDATE_SLOPE_DEG = 30.0
MAX_CANDIDATE_SLOPE_DEG = 55.0
HEURISTIC_SENSITIVITY_THRESHOLD_DELTA_DEG = 2.0
HEURISTIC_SENSITIVITY_FOOTPRINT_BUFFER_CELLS = 1
NODATA_SENTINEL = -9999.0


class TerrainReleaseZoneCandidateMetricsError(ValueError):
    """User-facing dry-run helper error."""


def _load_module(module_name: str, filename: str):
    path = ROOT / "scripts" / filename
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load helper module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


TERRAIN_PREPROCESSING = _load_module("aoi_terrain_preprocessing_planner", "plan_aoi_terrain_preprocessing.py")
WORKFLOW_VALIDATION = _load_module("release_zone_workflow_validation", "lib/workflow_validation.py")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("plan", "review-apply"), default="plan")
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--terrain-crop", type=Path, default=None)
    parser.add_argument("--terrain-metadata", type=Path, default=None)
    parser.add_argument("--source-zone-metadata", type=Path, default=None)
    parser.add_argument("--review-package", type=Path, default=None, help="candidate review package to edit")
    parser.add_argument(
        "--candidate-review-decision",
        action="append",
        default=[],
        help="candidate_release_zone_id=review_decision pair; repeat for each edited candidate",
    )
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    parser.add_argument("--output-root", type=Path, default=None, help="optional GIS-readable candidate product output root")
    parser.add_argument(
        "--output-mode",
        choices=("mask", "polygon", "both"),
        default=DEFAULT_OUTPUT_MODE,
        help="candidate product type to emit when --output-root is set",
    )
    args = parser.parse_args(argv)

    try:
        if args.mode == "review-apply":
            report = build_review_apply_report(
                repo_root=args.repo_root,
                review_package_path=args.review_package,
                candidate_review_decisions=parse_candidate_review_decisions(args.candidate_review_decision),
                output_root=args.output_root,
            )
        else:
            report = build_report(
                repo_root=args.repo_root,
                terrain_crop_path=args.terrain_crop,
                terrain_metadata_path=args.terrain_metadata,
                source_zone_metadata_path=args.source_zone_metadata,
                output_root=args.output_root,
                output_mode=args.output_mode,
            )
    except TerrainReleaseZoneCandidateMetricsError as exc:
        print(f"terrain release-zone candidate metrics error: {exc}", file=sys.stderr)
        return 2

    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if args.format == "json":
        output = json.dumps(report, indent=2, sort_keys=True)
    elif args.mode == "review-apply":
        output = render_review_apply_text_report(report)
    else:
        output = render_text_report(report)
    print(output)
    return 0 if report["candidate_metrics_status"] == "ready" else 2


def parse_candidate_review_decisions(values: list[str]) -> dict[str, str]:
    decisions: dict[str, str] = {}
    for entry in values:
        if "=" not in entry:
            raise TerrainReleaseZoneCandidateMetricsError(
                "candidate-review-decision must be provided as candidate_release_zone_id=review_decision"
            )
        candidate_id, decision = entry.split("=", 1)
        candidate_id = candidate_id.strip()
        decision = decision.strip()
        if not candidate_id or not decision:
            raise TerrainReleaseZoneCandidateMetricsError(
                "candidate-review-decision must include a nonempty candidate_release_zone_id and review_decision"
            )
        if candidate_id in decisions:
            raise TerrainReleaseZoneCandidateMetricsError(f"duplicate candidate-review-decision for {candidate_id}")
        decisions[candidate_id] = decision
    return decisions


def build_report(
    *,
    repo_root: Path | None = None,
    terrain_crop_path: Path | None = None,
    terrain_metadata_path: Path | None = None,
    source_zone_metadata_path: Path | None = None,
    output_root: Path | None = None,
    output_mode: str = DEFAULT_OUTPUT_MODE,
) -> dict[str, Any]:
    repo_root = repo_root or ROOT
    terrain_crop_path = terrain_crop_path or default_repo_path(repo_root, DEFAULT_TERRAIN_CROP)
    terrain_metadata_path = terrain_metadata_path or default_repo_path(repo_root, DEFAULT_TERRAIN_METADATA)
    source_zone_metadata_path = source_zone_metadata_path or default_repo_path(repo_root, DEFAULT_SOURCE_ZONE_METADATA)
    terrain_crop_path = resolve_path(repo_root, terrain_crop_path)
    terrain_metadata_path = resolve_path(repo_root, terrain_metadata_path)
    source_zone_metadata_path = resolve_path(repo_root, source_zone_metadata_path)
    terrain_catalog_path = terrain_crop_path.parent / "aoi_tile_catalog.yaml"

    required_inputs = [
        terrain_crop_path,
        terrain_metadata_path,
        source_zone_metadata_path,
    ]
    missing_inputs = [display_path(path, repo_root) for path in required_inputs if not path.exists()]
    if missing_inputs:
        return blocked_report(repo_root=repo_root, missing_inputs=missing_inputs)

    terrain = read_esri_ascii_grid(terrain_crop_path)
    terrain_metadata = load_yaml(terrain_metadata_path)
    source_zone_metadata = load_yaml(source_zone_metadata_path)
    terrain_preprocessing = build_terrain_preprocessing_report(
        repo_root=repo_root,
        terrain_crop_path=terrain_crop_path,
        terrain_metadata_path=terrain_metadata_path,
        terrain_catalog_path=terrain_catalog_path if terrain_catalog_path.exists() else None,
    )
    if terrain_preprocessing["terrain_preprocessing_status"] not in {"ready", "not_available"}:
        return blocked_report(
            repo_root=repo_root,
            missing_inputs=missing_inputs,
            terrain_preprocessing=terrain_preprocessing,
            blocked_status=terrain_preprocessing["terrain_preprocessing_status"],
        )

    screening = build_screening_criteria(terrain_metadata, source_zone_metadata)
    screening.update(build_screening_criteria_from_terrain_package(terrain_preprocessing))
    candidate_mask, terrain_masks = compute_candidate_masks(terrain, source_zone_metadata, screening)
    terrain_summary = build_terrain_summary(terrain)
    candidate_summary = build_candidate_summary(terrain, candidate_mask, terrain_masks, screening)
    candidate_sensitivity_report = build_candidate_sensitivity_report(
        terrain=terrain,
        source_zone_metadata=source_zone_metadata,
        screening=screening,
        baseline_candidate_mask=candidate_mask,
        baseline_terrain_masks=terrain_masks,
    )
    excluded_area_summary = build_excluded_area_summary(terrain_masks, terrain, screening)
    frozen_footprint_summary = build_frozen_footprint_summary(terrain, source_zone_metadata, terrain_masks)
    candidate_footprint_comparison = build_candidate_footprint_comparison(terrain, terrain_masks)
    provenance = build_provenance(terrain_crop_path, terrain_metadata_path, source_zone_metadata_path, terrain_metadata, source_zone_metadata)
    candidate_review_package = candidate_review_package_stub(repo_root=repo_root)

    report = {
        "schema_version": SCHEMA_VERSION,
        "candidate_metrics_status": "ready",
        "candidate_release_zone_set_status": "not_emitted",
        "candidate_release_zone_interpretation": "heuristic_workflow_input_only",
        "candidate_site_id": "tschamut_public_pilot",
        "candidate_site_name": "Balfrin / Tschamut AOI",
        "candidate_selection_rationale": (
            "The committed Tschamut public pilot terrain and frozen source-zone metadata are the "
            "reproducible Balfrin/Tschamut AOI inputs available in-repo."
        ),
        "repo_root": str(repo_root),
        "site_extent": terrain_metadata.get("extent_lv95_m", {}),
        "screening_criteria": screening,
        "terrain_inputs": {
            "terrain_crop_path": display_path(terrain_crop_path, repo_root),
            "terrain_metadata_path": display_path(terrain_metadata_path, repo_root),
            "terrain_crop_sha256": sha256_file(terrain_crop_path),
            "terrain_metadata_sha256": sha256_file(terrain_metadata_path),
            "terrain_download_status": terrain_metadata.get("download_status"),
            "terrain_license": terrain_metadata.get("license"),
            "terrain_preprocessing_status": terrain_preprocessing["terrain_preprocessing_status"],
            "terrain_preprocessing_manifest_path": terrain_preprocessing.get("terrain_preprocessing_manifest_path"),
            "terrain_preprocessing_package": terrain_preprocessing["terrain_preprocessing_package"],
        },
        "terrain_preprocessing": terrain_preprocessing,
        "source_zone_inputs": build_source_zone_inputs(source_zone_metadata_path, source_zone_metadata, repo_root),
        "terrain_summary": terrain_summary,
        "candidate_summary": candidate_summary,
        "candidate_sensitivity_report": candidate_sensitivity_report,
        "excluded_area_summary": excluded_area_summary,
        "frozen_source_zone_footprint": frozen_footprint_summary,
        "candidate_footprint_comparison": candidate_footprint_comparison,
        "provenance": provenance,
        "claim_boundaries": {
            "heuristic_workflow_input_only": True,
            "validated_release_zone_evidence": False,
            "field_validation_claims_allowed": False,
            "physical_release_probability_claims_allowed": False,
            "scale_up_authorized": False,
            "operational_claims_allowed": False,
            "notes": [
                "candidate cells are heuristic workflow inputs, not validated release zones",
                "bounded threshold and preprocessing perturbations only characterize heuristic stability",
                "stable regions are agreement regions across bounded heuristic settings, not validated release zones",
                "unstable regions are heuristic-sensitive regions, not invalidated release zones",
                "slope screening is fixed and deterministic",
                "no annual-frequency, risk, exposure, or vulnerability claim is authorized here",
            ],
        },
        "blocked_missing_inputs": [],
        "blocked_reason": "",
        "scale_up_authorized": False,
        "operational_claims_allowed": False,
        "candidate_review_package": candidate_review_package,
        "candidate_release_zone_products": {
            "output_status": "not_emitted",
            "output_mode": output_mode,
            "output_root": display_path(Path(output_root), repo_root) if output_root is not None else None,
        },
    }
    if output_root is not None:
        candidate_products, candidate_review_package = emit_candidate_products(
            report=report,
            terrain=terrain,
            terrain_masks=terrain_masks,
            source_zone_metadata=source_zone_metadata,
            repo_root=repo_root,
            output_root=output_root,
            output_mode=output_mode,
        )
        report["candidate_release_zone_set_status"] = "emitted"
        report["candidate_release_zone_products"] = candidate_products
        report["candidate_review_package"] = candidate_review_package
    return report


def build_review_apply_report(
    *,
    repo_root: Path | None = None,
    review_package_path: Path | None = None,
    candidate_review_decisions: dict[str, str] | None = None,
    output_root: Path | None = None,
) -> dict[str, Any]:
    repo_root = repo_root or ROOT
    if review_package_path is None:
        raise TerrainReleaseZoneCandidateMetricsError("review-package is required in review-apply mode")

    review_package_path = review_package_path.resolve(strict=False)
    if not review_package_path.exists():
        raise TerrainReleaseZoneCandidateMetricsError(f"missing review package: {display_path(review_package_path, repo_root)}")

    output_root = output_root or review_package_path.parent
    output_root = output_root if output_root.is_absolute() else (repo_root / output_root)
    if not is_allowed_output_root(output_root):
        raise TerrainReleaseZoneCandidateMetricsError(
            f"output-root must stay under /tmp or an ignored repo root: {output_root}"
        )

    review_package = load_yaml_or_json(review_package_path)
    report = apply_review_decisions_to_package(
        review_package_path=review_package_path,
        review_package=review_package,
        candidate_review_decisions=candidate_review_decisions or {},
        repo_root=repo_root,
        output_root=output_root,
    )

    review_package_status = text_value(report.get("review_package_status"))
    review_application_status = text_value(report.get("review_application_status"))
    if review_package_status != "review_applied" or review_application_status != "validated":
        raise TerrainReleaseZoneCandidateMetricsError("review package did not validate after applying review decisions")

    write_review_applied_outputs(report)
    return report


def apply_review_decisions_to_package(
    *,
    review_package_path: Path,
    review_package: dict[str, Any],
    candidate_review_decisions: dict[str, str],
    repo_root: Path,
    output_root: Path,
) -> dict[str, Any]:
    review_rows = review_package.get("candidate_review_rows", [])
    if not isinstance(review_rows, list):
        raise TerrainReleaseZoneCandidateMetricsError("candidate_review_rows must be a list")

    review_rows_by_id: dict[str, dict[str, Any]] = {}
    review_order: list[str] = []
    for index, row in enumerate(review_rows, start=1):
        if not isinstance(row, dict):
            raise TerrainReleaseZoneCandidateMetricsError(f"candidate_review_rows[{index}] must be an object")
        candidate_id = text_value(row.get("candidate_release_zone_id"))
        if not candidate_id:
            raise TerrainReleaseZoneCandidateMetricsError(f"candidate_review_rows[{index}] must define candidate_release_zone_id")
        if candidate_id in review_rows_by_id:
            raise TerrainReleaseZoneCandidateMetricsError(f"duplicate candidate_release_zone_id in review package: {candidate_id}")
        provenance_label = text_value(row.get("provenance_label"))
        if provenance_label not in PROVENANCE_LABELS:
            raise TerrainReleaseZoneCandidateMetricsError(
                f"candidate_review_rows[{index}].provenance_label must be one of {list(PROVENANCE_LABELS)}"
            )
        review_rows_by_id[candidate_id] = dict(row)
        review_order.append(candidate_id)

    unknown_decision_ids = sorted(set(candidate_review_decisions) - set(review_rows_by_id))
    if unknown_decision_ids:
        raise TerrainReleaseZoneCandidateMetricsError(
            "unknown candidate ids in review decisions: " + ", ".join(unknown_decision_ids)
        )

    applied_rows: list[dict[str, Any]] = []
    accepted_ids: list[str] = []
    rejected_ids: list[str] = []
    needs_field_review_ids: list[str] = []
    unreviewed_accepted_ids: list[str] = []
    mixed_provenance_overclaim_ids: list[str] = []
    accepted_missing_validation_ids: list[str] = []

    for candidate_id in review_order:
        row = dict(review_rows_by_id[candidate_id])
        original_decision = text_value(row.get("review_decision")) or "needs_field_review"
        decision = candidate_review_decisions.get(candidate_id, original_decision)
        if decision not in REVIEW_DECISION_OPTIONS:
            raise TerrainReleaseZoneCandidateMetricsError(
                f"candidate_review_rows decision for {candidate_id} must be one of {list(REVIEW_DECISION_OPTIONS)}"
            )

        explicit_review = candidate_id in candidate_review_decisions
        provenance_label = text_value(row.get("provenance_label"))
        if provenance_label not in PROVENANCE_LABELS:
            raise TerrainReleaseZoneCandidateMetricsError(
                f"candidate_review_rows provenance_label for {candidate_id} must be one of {list(PROVENANCE_LABELS)}"
            )

        accepted = decision == "accepted"
        rejected = decision == "rejected"
        needs_field_review = decision == "needs_field_review"

        if accepted:
            accepted_ids.append(candidate_id)
            if not explicit_review and original_decision == "accepted":
                unreviewed_accepted_ids.append(candidate_id)
            if provenance_label == "blocked_missing_provenance":
                accepted_missing_validation_ids.append(candidate_id)
        else:
            if provenance_label in {"field_supported", "mixed_provenance"}:
                mixed_provenance_overclaim_ids.append(candidate_id)
            if decision == "rejected":
                rejected_ids.append(candidate_id)
            else:
                needs_field_review_ids.append(candidate_id)

        row.update(
            {
                "review_decision": decision,
                "accepted": accepted,
                "rejected": rejected,
                "needs_field_review": needs_field_review,
                "review_application_source": "explicit" if explicit_review else "retained",
                "review_validation_status": "validated" if accepted else "not_accepted",
            }
        )
        applied_rows.append(row)

    if unreviewed_accepted_ids:
        raise TerrainReleaseZoneCandidateMetricsError(
            "unreviewed accepted candidates must be explicitly reviewed: " + ", ".join(unreviewed_accepted_ids)
        )
    if mixed_provenance_overclaim_ids:
        raise TerrainReleaseZoneCandidateMetricsError(
            "mixed-provenance overclaims are not allowed for non-accepted candidates: "
            + ", ".join(mixed_provenance_overclaim_ids)
        )
    if accepted_missing_validation_ids:
        raise TerrainReleaseZoneCandidateMetricsError(
            "accepted candidates cannot use blocked_missing_provenance provenance: "
            + ", ".join(accepted_missing_validation_ids)
        )
    if not accepted_ids:
        raise TerrainReleaseZoneCandidateMetricsError("reviewed package must contain at least one accepted candidate")

    accepted_rows = [row for row in applied_rows if text_value(row.get("review_decision")) == "accepted"]
    review_summary = build_candidate_review_summary(applied_rows)
    review_summary.update(
        {
            "accepted_candidate_count": len(accepted_ids),
            "rejected_candidate_count": len(rejected_ids),
            "needs_field_review_candidate_count": len(needs_field_review_ids),
        }
    )

    review_application = {
        "schema_version": REVIEW_APPLICATION_SCHEMA_VERSION,
        "review_package_path": display_path(review_package_path, repo_root),
        "output_root": display_path(output_root, repo_root),
        "validation_status": "validated",
        "validation_checks": {
            "unknown_candidate_ids": [],
            "unreviewed_accepted_candidate_ids": [],
            "mixed_provenance_overclaim_candidate_ids": [],
            "accepted_missing_validation_candidate_ids": [],
            "accepted_candidate_count": len(accepted_ids),
            "reviewed_candidate_count": len(candidate_review_decisions),
            "allowed_provenance_labels": list(PROVENANCE_LABELS),
        },
        "reviewed_candidate_ids": review_order,
        "explicit_reviewed_candidate_ids": list(candidate_review_decisions),
        "accepted_candidate_ids": accepted_ids,
        "rejected_candidate_ids": rejected_ids,
        "needs_field_review_candidate_ids": needs_field_review_ids,
    }

    review_package_status = "review_applied"
    reviewed_package = {
        **review_package,
        "schema_version": REVIEW_PACKAGE_SCHEMA_VERSION,
        "review_package_status": review_package_status,
        "review_application_status": "validated",
        "candidate_metrics_status": "ready",
        "candidate_release_zone_set_status": "review_applied",
        "candidate_release_zone_interpretation": "review_application_only",
        "review_application": review_application,
        "review_summary": review_summary,
        "candidate_review_rows": applied_rows,
        "accepted_candidate_ids": accepted_ids,
        "rejected_candidate_ids": rejected_ids,
        "needs_field_review_candidate_ids": needs_field_review_ids,
        "outputs": build_review_output_paths(review_package, review_package_path, repo_root, output_root),
        "review_source_outputs": review_package.get("outputs", {}),
        "output_root": display_path(output_root, repo_root),
    }
    reviewed_package["candidate_release_zone_ids"] = [text_value(row.get("candidate_release_zone_id")) for row in applied_rows]
    reviewed_package["review_decision_options"] = list(REVIEW_DECISION_OPTIONS)
    reviewed_package["editable_acceptance_fields"] = ["review_decision", "accepted", "rejected", "needs_field_review"]
    reviewed_package["provenance_label_legend"] = provenance_label_legend()
    reviewed_package["claim_boundaries"] = review_package.get("claim_boundaries", {})
    reviewed_package["candidate_sensitivity_summary"] = review_package.get("candidate_sensitivity_summary", {})
    reviewed_package["candidate_footprint_comparison"] = review_package.get("candidate_footprint_comparison", {})
    reviewed_package["frozen_source_zone_footprint"] = review_package.get("frozen_source_zone_footprint", {})
    reviewed_package["review_application"]["validated_candidate_count"] = len(accepted_rows)
    return reviewed_package


def build_review_output_paths(
    review_package: dict[str, Any],
    review_package_path: Path,
    repo_root: Path,
    output_root: Path,
) -> dict[str, str | None]:
    candidate_site_id = text_value(review_package.get("candidate_site_id")) or text_value(review_package_path.stem)
    polygon_path = output_root / f"{candidate_site_id}_release_zone_candidate_review.geojson"
    csv_path = output_root / f"{candidate_site_id}_release_zone_candidate_review.csv"
    mask_path = output_root / f"{candidate_site_id}_release_zone_candidate_review_mask.asc"
    manifest_path = output_root / f"{candidate_site_id}_release_zone_candidate_review_manifest.json"
    return {
        "polygon": str(polygon_path.resolve(strict=False)),
        "mask": str(mask_path.resolve(strict=False)),
        "csv": str(csv_path.resolve(strict=False)),
        "manifest": str(manifest_path.resolve(strict=False)),
    }


def write_review_applied_outputs(review_package: dict[str, Any]) -> None:
    output_paths = review_package.get("outputs", {}) or {}
    source_outputs = review_package.get("review_source_outputs", {}) or {}
    polygon_path = repo_path(output_paths.get("polygon"))
    csv_path = repo_path(output_paths.get("csv"))
    mask_path = repo_path(output_paths.get("mask"))
    manifest_path = repo_path(output_paths.get("manifest"))

    polygon_path.parent.mkdir(parents=True, exist_ok=True)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    mask_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    polygon_path.write_text(
        json.dumps(build_review_applied_geojson(review_package), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_candidate_review_csv(csv_path, review_package["candidate_review_rows"])
    write_candidate_mask_copy(mask_path, review_package, source_outputs)
    manifest_path.write_text(json.dumps(review_package, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_review_applied_geojson(review_package: dict[str, Any]) -> dict[str, Any]:
    source_outputs = review_package.get("review_source_outputs", {}) or {}
    polygon_path = source_outputs.get("polygon")
    geojson: dict[str, Any] = {
        "schema_version": REVIEW_PACKAGE_SCHEMA_VERSION,
        "type": "FeatureCollection",
        "candidate_site_id": review_package.get("candidate_site_id"),
        "candidate_site_name": review_package.get("candidate_site_name"),
        "source_zone_id": review_package.get("source_zone_id"),
        "candidate_generation_label": "heuristic_candidate_generation_only",
        "review_package_status": review_package.get("review_package_status"),
        "review_application_status": review_package.get("review_application_status"),
        "review_decision_options": list(REVIEW_DECISION_OPTIONS),
        "provenance_label_legend": provenance_label_legend(),
        "features": [],
    }
    if isinstance(polygon_path, str) and polygon_path.strip():
        polygon_file = package_path(review_package, polygon_path)
        if polygon_file.exists():
            payload = load_yaml_or_json(polygon_file)
            raw_features = payload.get("features", [])
            if isinstance(raw_features, list):
                features: list[dict[str, Any]] = []
                rows_by_id = {
                    text_value(row.get("candidate_release_zone_id")): row
                    for row in review_package.get("candidate_review_rows", [])
                    if isinstance(row, dict)
                }
                for feature in raw_features:
                    if not isinstance(feature, dict):
                        continue
                    feature_id = text_value((feature.get("properties") or {}).get("candidate_release_zone_id"))
                    row = rows_by_id.get(feature_id, {})
                    new_feature = dict(feature)
                    new_feature["properties"] = {
                        **(feature.get("properties") or {}),
                        "review_decision": row.get("review_decision"),
                        "accepted": row.get("accepted"),
                        "rejected": row.get("rejected"),
                        "needs_field_review": row.get("needs_field_review"),
                        "review_application_source": row.get("review_application_source"),
                        "review_validation_status": row.get("review_validation_status"),
                        "provenance_label": row.get("provenance_label"),
                    }
                    features.append(new_feature)
                geojson["features"] = features
    return geojson


def write_candidate_mask_copy(mask_path: Path, review_package: dict[str, Any], source_outputs: dict[str, Any]) -> None:
    output_mask = source_outputs.get("mask")
    if not isinstance(output_mask, str) or not output_mask.strip():
        mask_path.write_text("", encoding="utf-8")
        return
    source_mask = package_path(review_package, output_mask)
    if source_mask.exists():
        mask_path.write_text(source_mask.read_text(encoding="utf-8"), encoding="utf-8")
        return
    mask_path.write_text("", encoding="utf-8")


def blocked_report(
    *,
    repo_root: Path,
    missing_inputs: list[str],
    terrain_preprocessing: dict[str, Any] | None = None,
    blocked_status: str = "blocked_missing_inputs",
) -> dict[str, Any]:
    terrain_preprocessing = terrain_preprocessing or {
        "terrain_preprocessing_status": "not_available",
        "terrain_preprocessing_manifest_path": None,
        "terrain_preprocessing_package": {
            "preprocessing_status": "not_available",
            "source_tile_ids": [],
            "source_tiles": [],
            "output_roots": {
                "raw_swisstopo_cache_root": str(repo_root / "data/raw/swisstopo/tschamut_public_pilot"),
                "processed_input_root": str(default_repo_path(repo_root, DEFAULT_TERRAIN_CROP).parent),
                "output_root": str(default_repo_path(repo_root, DEFAULT_TERRAIN_CROP).parent),
            },
        },
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "candidate_metrics_status": blocked_status,
        "candidate_release_zone_set_status": "not_emitted",
        "candidate_release_zone_interpretation": "not_claimed",
        "candidate_site_id": "tschamut_public_pilot",
        "candidate_site_name": "Balfrin / Tschamut AOI",
        "candidate_selection_rationale": (
            "The committed Tschamut public pilot terrain and frozen source-zone metadata are the "
            "reproducible Balfrin/Tschamut AOI inputs available in-repo."
        ),
        "repo_root": str(repo_root),
        "site_extent": {},
        "screening_criteria": screening_criteria_stub(),
        "terrain_inputs": {
            "terrain_crop_path": display_path(default_repo_path(repo_root, DEFAULT_TERRAIN_CROP), repo_root),
            "terrain_metadata_path": display_path(default_repo_path(repo_root, DEFAULT_TERRAIN_METADATA), repo_root),
            "terrain_preprocessing_status": terrain_preprocessing["terrain_preprocessing_status"],
            "terrain_preprocessing_manifest_path": terrain_preprocessing.get("terrain_preprocessing_manifest_path"),
            "terrain_preprocessing_package": terrain_preprocessing["terrain_preprocessing_package"],
        },
        "source_zone_inputs": {
            "source_zone_metadata_path": display_path(
                default_repo_path(repo_root, DEFAULT_SOURCE_ZONE_METADATA), repo_root
            ),
        },
        "terrain_preprocessing": terrain_preprocessing,
        "terrain_summary": {},
        "candidate_summary": {},
        "candidate_sensitivity_report": candidate_sensitivity_report_stub(),
        "excluded_area_summary": [],
        "frozen_source_zone_footprint": {},
        "candidate_footprint_comparison": {
            "comparison_status": "blocked_missing_inputs",
            "candidate_excludes_frozen_footprint": False,
        },
        "provenance": {},
        "claim_boundaries": {
            "heuristic_workflow_input_only": True,
            "validated_release_zone_evidence": False,
            "field_validation_claims_allowed": False,
            "physical_release_probability_claims_allowed": False,
            "scale_up_authorized": False,
            "operational_claims_allowed": False,
            "notes": [
                "candidate cells are heuristic workflow inputs, not validated release zones",
                "bounded threshold and preprocessing perturbations only characterize heuristic stability",
                "stable regions are agreement regions across bounded heuristic settings, not validated release zones",
                "unstable regions are heuristic-sensitive regions, not invalidated release zones",
                "slope screening is fixed and deterministic",
                "no annual-frequency, risk, exposure, or vulnerability claim is authorized here",
            ],
        },
        "blocked_missing_inputs": missing_inputs,
        "blocked_reason": (
            terrain_preprocessing.get("blocked_reason")
            if terrain_preprocessing["terrain_preprocessing_status"] not in {"not_available", "ready"}
            else "required public inputs are missing: " + ", ".join(missing_inputs)
        ),
        "scale_up_authorized": False,
        "operational_claims_allowed": False,
        "candidate_release_zone_products": {
            "output_status": "not_emitted",
            "output_mode": DEFAULT_OUTPUT_MODE,
            "output_root": None,
        },
        "candidate_review_package": candidate_review_package_stub(repo_root=repo_root),
    }


def screening_criteria_stub() -> dict[str, Any]:
    return {
        "slope_algorithm": "horn_3x3_cell_center_deg",
        "minimum_finite_neighborhood": "3x3",
        "candidate_slope_min_deg": MIN_CANDIDATE_SLOPE_DEG,
        "candidate_slope_max_deg": MAX_CANDIDATE_SLOPE_DEG,
        "frozen_release_zone_footprint_buffer_cells": 0,
        "exclude_nodata": True,
        "exclude_incomplete_neighborhood": True,
        "exclude_frozen_release_zone_footprint": True,
        "frozen_release_zone_footprint_mask": "cell_center_in_polygon",
    }


def build_screening_criteria(terrain_metadata: dict[str, Any], source_zone_metadata: dict[str, Any]) -> dict[str, Any]:
    criteria = screening_criteria_stub()
    criteria.update(
        {
            "terrain_crs_epsg": terrain_metadata.get("coordinate_reference_system", {}).get("epsg"),
            "terrain_vertical_datum": terrain_metadata.get("coordinate_reference_system", {}).get("vertical_datum"),
            "source_zone_id": source_zone_metadata.get("source_zone_id"),
        }
    )
    return criteria


def build_screening_criteria_from_terrain_package(terrain_preprocessing: dict[str, Any]) -> dict[str, Any]:
    if terrain_preprocessing.get("terrain_preprocessing_status") == "not_available":
        return {}
    package = terrain_preprocessing.get("terrain_preprocessing_package") or {}
    if not isinstance(package, dict):
        return {}
    return {
        "terrain_crop_extent_lv95_m": package.get("crop_extent_lv95_m", {}),
        "terrain_resolution_m": package.get("resolution_m"),
        "terrain_crs_epsg": package.get("crs_epsg"),
        "terrain_nodata": package.get("nodata"),
        "terrain_source_tile_ids": package.get("source_tile_ids", []),
    }


def build_terrain_preprocessing_report(
    *,
    repo_root: Path,
    terrain_crop_path: Path,
    terrain_metadata_path: Path,
    terrain_catalog_path: Path | None,
) -> dict[str, Any]:
    if terrain_catalog_path is None:
        return {
            "terrain_preprocessing_status": "not_available",
            "terrain_preprocessing_manifest_path": None,
            "terrain_preprocessing_package": {
                "preprocessing_status": "not_available",
                "crop_extent_lv95_m": {},
                "resolution_m": None,
                "crs_epsg": None,
                "nodata": None,
                "source_tile_ids": [],
                "source_tiles": [],
                "output_roots": {
                    "raw_swisstopo_cache_root": str(repo_root / "data/raw/swisstopo/tschamut_public_pilot"),
                    "processed_input_root": str(terrain_crop_path.parent),
                    "output_root": str(terrain_crop_path.parent),
                },
                "output_paths": {},
                "source_tile_count": 0,
                "manifest_path": None,
            },
            "blocked_reason": "AOI tile catalog is not staged next to the terrain crop",
        }

    return TERRAIN_PREPROCESSING.build_report(
        repo_root=repo_root,
        terrain_crop_path=terrain_crop_path,
        terrain_metadata_path=terrain_metadata_path,
        aoi_tile_catalog_path=terrain_catalog_path,
    )


def build_terrain_summary(terrain: dict[str, Any]) -> dict[str, Any]:
    values = terrain["values"]
    valid_mask = terrain["valid_mask"]
    cell_count = int(values.size)
    valid_cell_count = int(valid_mask.sum())
    cell_area_m2 = terrain["cellsize"] ** 2
    return {
        "cell_count": cell_count,
        "valid_cell_count": valid_cell_count,
        "invalid_cell_count": cell_count - valid_cell_count,
        "cell_area_m2": cell_area_m2,
        "total_area_m2": cell_count * cell_area_m2,
        "valid_area_m2": valid_cell_count * cell_area_m2,
        "elevation_min_m": float(np.nanmin(np.where(valid_mask, values, np.nan))),
        "elevation_max_m": float(np.nanmax(np.where(valid_mask, values, np.nan))),
        "elevation_mean_m": float(np.nanmean(np.where(valid_mask, values, np.nan))),
        "resolution_m": terrain["cellsize"],
        "ncols": terrain["ncols"],
        "nrows": terrain["nrows"],
        "extent_lv95_m": {
            "xmin": terrain["xllcorner"],
            "ymin": terrain["yllcorner"],
            "xmax": terrain["xllcorner"] + terrain["ncols"] * terrain["cellsize"],
            "ymax": terrain["yllcorner"] + terrain["nrows"] * terrain["cellsize"],
        },
    }


def build_source_zone_inputs(
    source_zone_metadata_path: Path,
    source_zone_metadata: dict[str, Any],
    repo_root: Path,
) -> dict[str, Any]:
    vertices = extract_polygon_vertices(source_zone_metadata)
    provenance = source_zone_metadata.get("provenance", {})
    return {
        "source_zone_metadata_path": display_path(source_zone_metadata_path, repo_root),
        "source_zone_metadata_sha256": sha256_file(source_zone_metadata_path),
        "source_zone_id": source_zone_metadata.get("source_zone_id"),
        "crs_epsg": source_zone_metadata.get("crs_epsg"),
        "vertical_datum": source_zone_metadata.get("vertical_datum"),
        "release_sampling_policy": source_zone_metadata.get("release_sampling_policy", {}),
        "provenance": provenance,
        "release_zone_provenance_intake": WORKFLOW_VALIDATION.build_release_zone_provenance_intake(
            provenance,
            provenance_source=display_path(source_zone_metadata_path, repo_root),
        ),
        "footprint": {
            "polygon_area_m2_exact": polygon_area(vertices),
            "vertex_count": len(vertices),
            "vertices": vertices,
        },
    }


def build_candidate_summary(
    terrain: dict[str, Any],
    candidate_mask: np.ndarray,
    terrain_masks: dict[str, np.ndarray],
    screening: dict[str, Any],
) -> dict[str, Any]:
    slope_deg = terrain_masks["slope_deg"]
    candidate_values = slope_deg[candidate_mask]
    cell_area_m2 = terrain["cellsize"] ** 2
    candidate_count = int(candidate_mask.sum())
    screenable_count = int(terrain_masks["screenable_mask"].sum())
    valid_interior_count = int(terrain_masks["valid_interior_mask"].sum())
    return {
        "candidate_cell_count": candidate_count,
        "candidate_area_m2": candidate_count * cell_area_m2,
        "candidate_fraction_of_screenable_cells": fraction(candidate_count, screenable_count),
        "candidate_fraction_of_valid_interior_cells": fraction(candidate_count, valid_interior_count),
        "candidate_slope_min_deg": float(np.min(candidate_values)) if candidate_count else None,
        "candidate_slope_max_deg": float(np.max(candidate_values)) if candidate_count else None,
        "candidate_slope_mean_deg": float(np.mean(candidate_values)) if candidate_count else None,
        "candidate_slope_median_deg": float(np.median(candidate_values)) if candidate_count else None,
        "candidate_slope_p95_deg": float(np.quantile(candidate_values, 0.95)) if candidate_count else None,
        "screenable_cell_count": screenable_count,
        "screenable_area_m2": screenable_count * cell_area_m2,
        "screenable_fraction_of_valid_cells": fraction(screenable_count, int(terrain["valid_mask"].sum())),
        "screening_summary": {
            "candidate_slope_min_deg": screening["candidate_slope_min_deg"],
            "candidate_slope_max_deg": screening["candidate_slope_max_deg"],
            "slope_algorithm": screening["slope_algorithm"],
            "frozen_release_zone_footprint_buffer_cells": screening.get("frozen_release_zone_footprint_buffer_cells", 0),
        },
    }


def build_frozen_footprint_summary(
    terrain: dict[str, Any],
    source_zone_metadata: dict[str, Any],
    terrain_masks: dict[str, np.ndarray],
) -> dict[str, Any]:
    vertices = extract_polygon_vertices(source_zone_metadata)
    mask = terrain_masks["footprint_mask"]
    cell_area_m2 = terrain["cellsize"] ** 2
    return {
        "source_zone_id": source_zone_metadata.get("source_zone_id"),
        "geometry_type": source_zone_metadata.get("geometry", {}).get("type", "polygon"),
        "vertex_count": len(vertices),
        "vertex_coordinates": [[x, y] for x, y in vertices],
        "polygon_area_m2_exact": polygon_area(vertices),
        "masked_cell_count_on_terrain_grid": int(mask.sum()),
        "masked_area_m2_on_terrain_grid": int(mask.sum()) * cell_area_m2,
        "bbox_lv95_m": polygon_bbox(vertices),
    }


def build_candidate_footprint_comparison(
    terrain: dict[str, Any],
    terrain_masks: dict[str, np.ndarray],
) -> dict[str, Any]:
    candidate_mask = terrain_masks["candidate_mask"]
    footprint_mask = terrain_masks["footprint_mask"]
    intersection_mask = candidate_mask & footprint_mask
    cell_area_m2 = terrain["cellsize"] ** 2
    candidate_count = int(candidate_mask.sum())
    footprint_count = int(footprint_mask.sum())
    intersection_count = int(intersection_mask.sum())
    return {
        "comparison_status": "ready",
        "comparison_mode": "candidate_mask_vs_frozen_source_zone_footprint_mask",
        "candidate_excludes_frozen_footprint": intersection_count == 0,
        "candidate_cell_count": candidate_count,
        "frozen_footprint_cell_count": footprint_count,
        "candidate_and_frozen_footprint_intersection_cell_count": intersection_count,
        "candidate_and_frozen_footprint_intersection_area_m2": intersection_count * cell_area_m2,
        "candidate_overlap_fraction_of_candidate_cells": fraction(intersection_count, candidate_count),
        "candidate_overlap_fraction_of_frozen_footprint_cells": fraction(intersection_count, footprint_count),
    }


def build_excluded_area_summary(
    terrain_masks: dict[str, np.ndarray],
    terrain: dict[str, Any],
    screening: dict[str, Any],
) -> list[dict[str, Any]]:
    cell_area_m2 = terrain["cellsize"] ** 2
    slope = terrain_masks["slope_deg"]
    low_mask = terrain_masks["low_slope_mask"]
    high_mask = terrain_masks["high_slope_mask"]
    return [
        {
            "category": "nodata_or_invalid",
            "cell_count": int(terrain_masks["nodata_mask"].sum()),
            "area_m2": int(terrain_masks["nodata_mask"].sum()) * cell_area_m2,
            "reason": "cells with nodata or non-finite terrain values",
        },
        {
            "category": "incomplete_neighborhood",
            "cell_count": int(terrain_masks["incomplete_neighborhood_mask"].sum()),
            "area_m2": int(terrain_masks["incomplete_neighborhood_mask"].sum()) * cell_area_m2,
            "reason": "border cells without a full 3x3 slope kernel",
        },
        {
            "category": "frozen_release_zone_footprint",
            "cell_count": int(terrain_masks["footprint_mask"].sum()),
            "area_m2": int(terrain_masks["footprint_mask"].sum()) * cell_area_m2,
            "reason": "cells inside the committed frozen source-zone footprint are excluded from candidate screening",
        },
        {
            "category": "slope_below_candidate_band",
            "cell_count": int(low_mask.sum()),
            "area_m2": int(low_mask.sum()) * cell_area_m2,
            "reason": f"slope below {screening['candidate_slope_min_deg']} degrees",
        },
        {
            "category": "slope_above_candidate_band",
            "cell_count": int(high_mask.sum()),
            "area_m2": int(high_mask.sum()) * cell_area_m2,
            "reason": f"slope above {screening['candidate_slope_max_deg']} degrees",
        },
        {
            "category": "candidate_band",
            "cell_count": int(terrain_masks["candidate_mask"].sum()),
            "area_m2": int(terrain_masks["candidate_mask"].sum()) * cell_area_m2,
            "reason": (
                f"slope within [{screening['candidate_slope_min_deg']}, {screening['candidate_slope_max_deg']}] degrees "
                "and outside the frozen release-zone footprint"
            ),
        },
    ]


def compute_candidate_masks(
    terrain: dict[str, Any],
    source_zone_metadata: dict[str, Any],
    screening: dict[str, Any],
) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    values = terrain["values"]
    valid_mask = terrain["valid_mask"]
    nrows, ncols = values.shape

    slope_deg = np.full_like(values, np.nan, dtype=float)
    valid_interior_mask = np.zeros_like(valid_mask, dtype=bool)
    nodata_mask = ~valid_mask
    incomplete_neighborhood_mask = np.ones_like(valid_mask, dtype=bool)
    incomplete_neighborhood_mask[1:-1, 1:-1] = False
    footprint_mask = point_in_polygon_mask(terrain, extract_polygon_vertices(source_zone_metadata))
    footprint_buffer_cells = int(screening.get("frozen_release_zone_footprint_buffer_cells", 0) or 0)
    if footprint_buffer_cells > 0:
        footprint_mask = dilate_mask(footprint_mask, footprint_buffer_cells)

    for row in range(1, nrows - 1):
        for col in range(1, ncols - 1):
            neighborhood = values[row - 1 : row + 2, col - 1 : col + 2]
            if not np.isfinite(neighborhood).all():
                continue
            valid_interior_mask[row, col] = True
            dzdx = (
                (neighborhood[0, 2] + 2.0 * neighborhood[1, 2] + neighborhood[2, 2])
                - (neighborhood[0, 0] + 2.0 * neighborhood[1, 0] + neighborhood[2, 0])
            ) / (8.0 * terrain["cellsize"])
            dzdy = (
                (neighborhood[2, 0] + 2.0 * neighborhood[2, 1] + neighborhood[2, 2])
                - (neighborhood[0, 0] + 2.0 * neighborhood[0, 1] + neighborhood[0, 2])
            ) / (8.0 * terrain["cellsize"])
            slope_deg[row, col] = math.degrees(math.atan(math.hypot(dzdx, dzdy)))

    screenable_mask = valid_interior_mask & ~footprint_mask
    min_slope_deg = float(screening.get("candidate_slope_min_deg", MIN_CANDIDATE_SLOPE_DEG))
    max_slope_deg = float(screening.get("candidate_slope_max_deg", MAX_CANDIDATE_SLOPE_DEG))
    candidate_mask = screenable_mask & (slope_deg >= min_slope_deg) & (slope_deg <= max_slope_deg)
    low_slope_mask = screenable_mask & np.isfinite(slope_deg) & (slope_deg < min_slope_deg)
    high_slope_mask = screenable_mask & np.isfinite(slope_deg) & (slope_deg > max_slope_deg)

    terrain_masks = {
        "slope_deg": slope_deg,
        "valid_interior_mask": valid_interior_mask,
        "nodata_mask": nodata_mask,
        "incomplete_neighborhood_mask": incomplete_neighborhood_mask,
        "footprint_mask": footprint_mask,
        "screenable_mask": screenable_mask,
        "candidate_mask": candidate_mask,
        "low_slope_mask": low_slope_mask,
        "high_slope_mask": high_slope_mask,
    }
    return candidate_mask, terrain_masks


def clone_terrain_with_values(terrain: dict[str, Any], values: np.ndarray) -> dict[str, Any]:
    variant_values = np.array(values, dtype=float, copy=True)
    return {
        **terrain,
        "values": variant_values,
        "valid_mask": np.isfinite(variant_values),
    }


def smooth_terrain_3x3_mean(terrain: dict[str, Any]) -> np.ndarray:
    values = terrain["values"]
    smoothed = np.full_like(values, np.nan, dtype=float)
    nrows, ncols = values.shape
    for row in range(nrows):
        for col in range(ncols):
            center = values[row, col]
            if not np.isfinite(center):
                continue
            neighbourhood = values[
                max(0, row - 1) : min(nrows, row + 2),
                max(0, col - 1) : min(ncols, col + 2),
            ]
            finite_neighbourhood = neighbourhood[np.isfinite(neighbourhood)]
            if finite_neighbourhood.size:
                smoothed[row, col] = float(np.mean(finite_neighbourhood))
    return smoothed


def coarsen_terrain_2x2_mean_reexpanded(terrain: dict[str, Any]) -> np.ndarray:
    values = terrain["values"]
    reexpanded = np.full_like(values, np.nan, dtype=float)
    nrows, ncols = values.shape
    for row_start in range(0, nrows, 2):
        for col_start in range(0, ncols, 2):
            block = values[row_start : min(row_start + 2, nrows), col_start : min(col_start + 2, ncols)]
            finite_block = block[np.isfinite(block)]
            if finite_block.size == 0:
                continue
            block_value = float(np.mean(finite_block))
            for row in range(row_start, min(row_start + 2, nrows)):
                for col in range(col_start, min(col_start + 2, ncols)):
                    if np.isfinite(values[row, col]):
                        reexpanded[row, col] = block_value
    return reexpanded


def trim_aoi_boundary_values(terrain: dict[str, Any], trim_cells: int = 1) -> np.ndarray:
    values = np.array(terrain["values"], dtype=float, copy=True)
    if trim_cells <= 0:
        return values
    if trim_cells * 2 >= values.shape[0] or trim_cells * 2 >= values.shape[1]:
        return np.full_like(values, np.nan, dtype=float)
    values[:trim_cells, :] = np.nan
    values[-trim_cells:, :] = np.nan
    values[:, :trim_cells] = np.nan
    values[:, -trim_cells:] = np.nan
    return values


def build_candidate_sensitivity_report(
    *,
    terrain: dict[str, Any],
    source_zone_metadata: dict[str, Any],
    screening: dict[str, Any],
    baseline_candidate_mask: np.ndarray,
    baseline_terrain_masks: dict[str, np.ndarray],
) -> dict[str, Any]:
    variant_specs = [
        {
            "variant_id": "baseline",
            "variant_kind": "reference",
            "sensitivity_dimension": "baseline",
            "terrain_transform": "identity",
            "candidate_slope_min_deg": float(screening["candidate_slope_min_deg"]),
            "candidate_slope_max_deg": float(screening["candidate_slope_max_deg"]),
            "frozen_release_zone_footprint_buffer_cells": 0,
            "terrain_resolution_m": terrain["cellsize"],
            "terrain_smoothing_window_cells": 0,
            "aoi_boundary_trim_cells": 0,
        },
        {
            "variant_id": "tight_threshold_band",
            "variant_kind": "threshold_perturbation",
            "sensitivity_dimension": "slope_threshold",
            "terrain_transform": "identity",
            "candidate_slope_min_deg": float(screening["candidate_slope_min_deg"]) + HEURISTIC_SENSITIVITY_THRESHOLD_DELTA_DEG,
            "candidate_slope_max_deg": float(screening["candidate_slope_max_deg"]) - HEURISTIC_SENSITIVITY_THRESHOLD_DELTA_DEG,
            "frozen_release_zone_footprint_buffer_cells": 0,
            "terrain_resolution_m": terrain["cellsize"],
            "terrain_smoothing_window_cells": 0,
            "aoi_boundary_trim_cells": 0,
        },
        {
            "variant_id": "wide_threshold_band",
            "variant_kind": "threshold_perturbation",
            "sensitivity_dimension": "slope_threshold",
            "terrain_transform": "identity",
            "candidate_slope_min_deg": float(screening["candidate_slope_min_deg"]) - HEURISTIC_SENSITIVITY_THRESHOLD_DELTA_DEG,
            "candidate_slope_max_deg": float(screening["candidate_slope_max_deg"]) + HEURISTIC_SENSITIVITY_THRESHOLD_DELTA_DEG,
            "frozen_release_zone_footprint_buffer_cells": 0,
            "terrain_resolution_m": terrain["cellsize"],
            "terrain_smoothing_window_cells": 0,
            "aoi_boundary_trim_cells": 0,
        },
        {
            "variant_id": "smoothed_3x3_mean",
            "variant_kind": "smoothing_perturbation",
            "sensitivity_dimension": "smoothing",
            "terrain_transform": "smoothed_3x3_mean",
            "candidate_slope_min_deg": float(screening["candidate_slope_min_deg"]),
            "candidate_slope_max_deg": float(screening["candidate_slope_max_deg"]),
            "frozen_release_zone_footprint_buffer_cells": 0,
            "terrain_resolution_m": terrain["cellsize"],
            "terrain_smoothing_window_cells": 3,
            "aoi_boundary_trim_cells": 0,
        },
        {
            "variant_id": "coarsened_2x2_mean_reexpanded",
            "variant_kind": "terrain_resolution_perturbation",
            "sensitivity_dimension": "terrain_resolution",
            "terrain_transform": "coarsened_2x2_mean_reexpanded",
            "candidate_slope_min_deg": float(screening["candidate_slope_min_deg"]),
            "candidate_slope_max_deg": float(screening["candidate_slope_max_deg"]),
            "frozen_release_zone_footprint_buffer_cells": 0,
            "terrain_resolution_m": terrain["cellsize"] * 2.0,
            "terrain_smoothing_window_cells": 0,
            "aoi_boundary_trim_cells": 0,
        },
        {
            "variant_id": "trimmed_aoi_boundary_1_cell",
            "variant_kind": "aoi_boundary_perturbation",
            "sensitivity_dimension": "aoi_boundary",
            "terrain_transform": "trimmed_aoi_boundary_1_cell",
            "candidate_slope_min_deg": float(screening["candidate_slope_min_deg"]),
            "candidate_slope_max_deg": float(screening["candidate_slope_max_deg"]),
            "frozen_release_zone_footprint_buffer_cells": 0,
            "terrain_resolution_m": terrain["cellsize"],
            "terrain_smoothing_window_cells": 0,
            "aoi_boundary_trim_cells": 1,
        },
    ]

    baseline_variant_mask = baseline_candidate_mask
    variant_masks: dict[str, np.ndarray] = {"baseline": baseline_variant_mask}
    variant_summaries: list[dict[str, Any]] = []
    for spec in variant_specs:
        variant_screening = dict(screening)
        variant_screening.update(
            {
                "candidate_slope_min_deg": spec["candidate_slope_min_deg"],
                "candidate_slope_max_deg": spec["candidate_slope_max_deg"],
                "frozen_release_zone_footprint_buffer_cells": spec["frozen_release_zone_footprint_buffer_cells"],
            }
        )
        if spec["terrain_transform"] == "smoothed_3x3_mean":
            variant_terrain = clone_terrain_with_values(terrain, smooth_terrain_3x3_mean(terrain))
        elif spec["terrain_transform"] == "coarsened_2x2_mean_reexpanded":
            variant_terrain = clone_terrain_with_values(terrain, coarsen_terrain_2x2_mean_reexpanded(terrain))
        elif spec["terrain_transform"] == "trimmed_aoi_boundary_1_cell":
            variant_terrain = clone_terrain_with_values(terrain, trim_aoi_boundary_values(terrain, 1))
        else:
            variant_terrain = terrain
        if spec["variant_id"] == "baseline":
            candidate_mask = baseline_candidate_mask
            terrain_masks = baseline_terrain_masks
        else:
            candidate_mask, terrain_masks = compute_candidate_masks(
                variant_terrain,
                source_zone_metadata,
                variant_screening,
            )
        variant_masks[spec["variant_id"]] = candidate_mask
        summary = build_candidate_summary(variant_terrain, candidate_mask, terrain_masks, variant_screening)
        baseline_overlap_mask = candidate_mask & baseline_variant_mask
        baseline_union_mask = candidate_mask | baseline_variant_mask
        baseline_overlap_count = int(baseline_overlap_mask.sum())
        candidate_count = int(candidate_mask.sum())
        baseline_count = int(baseline_variant_mask.sum())
        summary.update(
            {
                "variant_id": spec["variant_id"],
                "variant_kind": spec["variant_kind"],
                "sensitivity_dimension": spec["sensitivity_dimension"],
                "terrain_transform": spec["terrain_transform"],
                "terrain_resolution_m": spec["terrain_resolution_m"],
                "terrain_smoothing_window_cells": spec["terrain_smoothing_window_cells"],
                "aoi_boundary_trim_cells": spec["aoi_boundary_trim_cells"],
                "candidate_overlap_with_baseline_cell_count": baseline_overlap_count,
                "candidate_overlap_with_baseline_area_m2": baseline_overlap_count * (terrain["cellsize"] ** 2),
                "candidate_overlap_fraction_of_baseline_cells": fraction(baseline_overlap_count, baseline_count),
                "candidate_overlap_fraction_of_variant_cells": fraction(baseline_overlap_count, candidate_count),
                "candidate_overlap_jaccard_index_with_baseline": fraction(
                    baseline_overlap_count, int(baseline_union_mask.sum())
                ),
                "candidate_delta_cell_count_vs_baseline": candidate_count - baseline_count,
                "candidate_delta_area_m2_vs_baseline": (candidate_count - baseline_count) * (terrain["cellsize"] ** 2),
            }
        )
        variant_summaries.append(summary)

    union_mask = np.logical_or.reduce(list(variant_masks.values()))
    stable_mask = np.logical_and.reduce(list(variant_masks.values()))
    unstable_mask = union_mask & ~stable_mask
    baseline_candidate_count = int(baseline_variant_mask.sum())
    union_candidate_count = int(union_mask.sum())
    stable_region_summary = summarize_region_mask(stable_mask, terrain, "stable_across_bounded_heuristics")
    unstable_region_summary = summarize_region_mask(unstable_mask, terrain, "unstable_across_bounded_heuristics")
    heuristic_sensitive_region_summary = summarize_region_mask(
        unstable_mask,
        terrain,
        "heuristic_sensitive_across_bounded_heuristics",
    )
    stable_region_summary["coverage_fraction_of_union_candidate_cells"] = fraction(
        stable_region_summary["cell_count"], union_candidate_count
    )
    stable_region_summary["coverage_fraction_of_baseline_candidate_cells"] = fraction(
        stable_region_summary["cell_count"], baseline_candidate_count
    )
    unstable_region_summary["coverage_fraction_of_union_candidate_cells"] = fraction(
        unstable_region_summary["cell_count"], union_candidate_count
    )
    unstable_region_summary["coverage_fraction_of_baseline_candidate_cells"] = fraction(
        unstable_region_summary["cell_count"], baseline_candidate_count
    )
    heuristic_sensitive_region_summary["coverage_fraction_of_union_candidate_cells"] = fraction(
        heuristic_sensitive_region_summary["cell_count"], union_candidate_count
    )
    heuristic_sensitive_region_summary["coverage_fraction_of_baseline_candidate_cells"] = fraction(
        heuristic_sensitive_region_summary["cell_count"], baseline_candidate_count
    )

    pairwise_overlap_summary: list[dict[str, Any]] = []
    for left, right in combinations(variant_summaries, 2):
        left_mask = variant_masks[left["variant_id"]]
        right_mask = variant_masks[right["variant_id"]]
        shared_mask = left_mask & right_mask
        shared_count = int(shared_mask.sum())
        union_count = int((left_mask | right_mask).sum())
        cell_area_m2 = terrain["cellsize"] ** 2
        pairwise_overlap_summary.append(
            {
                "left_variant_id": left["variant_id"],
                "right_variant_id": right["variant_id"],
                "shared_cell_count": shared_count,
                "shared_area_m2": shared_count * cell_area_m2,
                "union_cell_count": union_count,
                "union_area_m2": union_count * cell_area_m2,
                "left_overlap_fraction": fraction(shared_count, int(left_mask.sum())),
                "right_overlap_fraction": fraction(shared_count, int(right_mask.sum())),
                "jaccard_index": fraction(shared_count, union_count),
            }
        )

    candidate_counts = [summary["candidate_cell_count"] for summary in variant_summaries]
    candidate_areas = [summary["candidate_area_m2"] for summary in variant_summaries]
    baseline_comparison_summaries = [summary for summary in variant_summaries if summary["variant_id"] != "baseline"]
    sensitivity_matrix = build_candidate_sensitivity_matrix(baseline_comparison_summaries)
    candidate_persistence_metrics = build_candidate_persistence_metrics(
        baseline_variant_id="baseline",
        baseline_candidate_count=baseline_candidate_count,
        union_candidate_count=union_candidate_count,
        stable_region_summary=stable_region_summary,
        unstable_region_summary=unstable_region_summary,
        heuristic_sensitive_region_summary=heuristic_sensitive_region_summary,
        variant_summaries=baseline_comparison_summaries,
        pairwise_overlap_summary=pairwise_overlap_summary,
    )
    candidate_region_classifications = [
        stable_region_summary,
        unstable_region_summary,
        heuristic_sensitive_region_summary,
    ]
    return {
        "sensitivity_status": "ready",
        "sensitivity_scope": "bounded_threshold_smoothing_resolution_and_boundary_perturbations",
        "baseline_variant_id": "baseline",
        "variant_count": len(variant_summaries),
        "variant_summaries": variant_summaries,
        "candidate_count_range": {
            "min": min(candidate_counts),
            "max": max(candidate_counts),
        },
        "candidate_area_range_m2": {
            "min": min(candidate_areas),
            "max": max(candidate_areas),
        },
        "baseline_candidate_cell_count": baseline_candidate_count,
        "baseline_candidate_area_m2": baseline_candidate_count * (terrain["cellsize"] ** 2),
        "union_candidate_cell_count": union_candidate_count,
        "union_candidate_area_m2": union_candidate_count * (terrain["cellsize"] ** 2),
        "stable_candidate_region": stable_region_summary,
        "unstable_candidate_region": unstable_region_summary,
        "heuristic_sensitive_candidate_region": heuristic_sensitive_region_summary,
        "candidate_region_classifications": candidate_region_classifications,
        "candidate_sensitivity_matrix": sensitivity_matrix,
        "candidate_persistence_metrics": candidate_persistence_metrics,
        "pairwise_overlap_summary": pairwise_overlap_summary,
        "claim_boundaries": {
            "heuristic_stability_characterization_only": True,
            "validated_release_zone_evidence": False,
            "field_validation_claims_allowed": False,
            "physical_release_probability_claims_allowed": False,
            "scale_up_authorized": False,
            "operational_claims_allowed": False,
            "notes": [
                "bounded perturbations only characterize heuristic agreement and disagreement",
                "stable regions are agreement regions across bounded heuristic settings, not validated release zones",
                "unstable regions are heuristic-sensitive regions, not invalidated release zones",
                "heuristic-sensitive regions are candidate-persistence summaries, not validated release zones",
            ],
        },
    }


def summarize_region_mask(mask: np.ndarray, terrain: dict[str, Any], region_class: str) -> dict[str, Any]:
    cell_count = int(mask.sum())
    cell_area_m2 = terrain["cellsize"] ** 2
    components = connected_candidate_components(mask)
    component_sizes = [len(component) for component in components]
    return {
        "region_class": region_class,
        "cell_count": cell_count,
        "area_m2": cell_count * cell_area_m2,
        "component_count": len(components),
        "largest_component_cell_count": max(component_sizes) if component_sizes else 0,
        "largest_component_area_m2": (max(component_sizes) if component_sizes else 0) * cell_area_m2,
        "region_bbox_lv95_m": mask_bbox(mask, terrain),
        "coverage_fraction_of_union_candidate_cells": None,
        "coverage_fraction_of_baseline_candidate_cells": None,
    }


def build_candidate_sensitivity_matrix(variant_summaries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for summary in variant_summaries:
        grouped.setdefault(summary["sensitivity_dimension"], []).append(summary)

    matrix: list[dict[str, Any]] = []
    for sensitivity_dimension in ("slope_threshold", "smoothing", "terrain_resolution", "aoi_boundary"):
        dimension_summaries = grouped.get(sensitivity_dimension, [])
        if not dimension_summaries:
            matrix.append(
                {
                    "sensitivity_dimension": sensitivity_dimension,
                    "variant_count": 0,
                    "variant_ids": [],
                    "candidate_count_range": {"min": None, "max": None, "mean": None, "median": None},
                    "candidate_area_range_m2": {"min": None, "max": None, "mean": None, "median": None},
                    "candidate_delta_cell_count_vs_baseline_range": {"min": None, "max": None, "mean": None, "median": None},
                    "candidate_delta_area_m2_vs_baseline_range": {"min": None, "max": None, "mean": None, "median": None},
                    "candidate_overlap_fraction_of_baseline_range": {"min": None, "max": None, "mean": None, "median": None},
                    "candidate_overlap_fraction_of_variant_range": {"min": None, "max": None, "mean": None, "median": None},
                    "jaccard_index_range": {"min": None, "max": None, "mean": None, "median": None},
                    "terrain_transform_types": [],
                }
            )
            continue

        matrix.append(
            {
                "sensitivity_dimension": sensitivity_dimension,
                "variant_count": len(dimension_summaries),
                "variant_ids": [summary["variant_id"] for summary in dimension_summaries],
                "candidate_count_range": summarize_distribution(
                    [summary["candidate_cell_count"] for summary in dimension_summaries]
                ),
                "candidate_area_range_m2": summarize_distribution(
                    [summary["candidate_area_m2"] for summary in dimension_summaries]
                ),
                "candidate_delta_cell_count_vs_baseline_range": summarize_distribution(
                    [summary["candidate_delta_cell_count_vs_baseline"] for summary in dimension_summaries]
                ),
                "candidate_delta_area_m2_vs_baseline_range": summarize_distribution(
                    [summary["candidate_delta_area_m2_vs_baseline"] for summary in dimension_summaries]
                ),
                "candidate_overlap_fraction_of_baseline_range": summarize_distribution(
                    [summary["candidate_overlap_fraction_of_baseline_cells"] for summary in dimension_summaries]
                ),
                "candidate_overlap_fraction_of_variant_range": summarize_distribution(
                    [summary["candidate_overlap_fraction_of_variant_cells"] for summary in dimension_summaries]
                ),
                "jaccard_index_range": summarize_distribution(
                    [summary["candidate_overlap_jaccard_index_with_baseline"] for summary in dimension_summaries]
                ),
                "terrain_transform_types": sorted({summary["terrain_transform"] for summary in dimension_summaries}),
            }
        )
    return matrix


def build_candidate_persistence_metrics(
    *,
    baseline_variant_id: str,
    baseline_candidate_count: int,
    union_candidate_count: int,
    stable_region_summary: dict[str, Any],
    unstable_region_summary: dict[str, Any],
    heuristic_sensitive_region_summary: dict[str, Any],
    variant_summaries: list[dict[str, Any]],
    pairwise_overlap_summary: list[dict[str, Any]],
) -> dict[str, Any]:
    baseline_comparison_jaccard = [
        summary["candidate_overlap_jaccard_index_with_baseline"] for summary in variant_summaries
    ]
    baseline_comparison_candidate_overlap = [
        summary["candidate_overlap_fraction_of_baseline_cells"] for summary in variant_summaries
    ]
    baseline_comparison_variant_overlap = [
        summary["candidate_overlap_fraction_of_variant_cells"] for summary in variant_summaries
    ]
    return {
        "baseline_variant_id": baseline_variant_id,
        "baseline_candidate_cell_count": baseline_candidate_count,
        "union_candidate_cell_count": union_candidate_count,
        "stable_candidate_cell_count": stable_region_summary["cell_count"],
        "unstable_candidate_cell_count": unstable_region_summary["cell_count"],
        "heuristic_sensitive_candidate_cell_count": heuristic_sensitive_region_summary["cell_count"],
        "stable_fraction_of_union_candidate_cells": stable_region_summary["coverage_fraction_of_union_candidate_cells"],
        "stable_fraction_of_baseline_candidate_cells": stable_region_summary["coverage_fraction_of_baseline_candidate_cells"],
        "unstable_fraction_of_union_candidate_cells": unstable_region_summary["coverage_fraction_of_union_candidate_cells"],
        "unstable_fraction_of_baseline_candidate_cells": unstable_region_summary["coverage_fraction_of_baseline_candidate_cells"],
        "heuristic_sensitive_fraction_of_union_candidate_cells": heuristic_sensitive_region_summary[
            "coverage_fraction_of_union_candidate_cells"
        ],
        "heuristic_sensitive_fraction_of_baseline_candidate_cells": heuristic_sensitive_region_summary[
            "coverage_fraction_of_baseline_candidate_cells"
        ],
        "baseline_comparison_jaccard_range": summarize_distribution(baseline_comparison_jaccard),
        "baseline_comparison_candidate_overlap_range": summarize_distribution(
            baseline_comparison_candidate_overlap
        ),
        "baseline_comparison_variant_overlap_range": summarize_distribution(
            baseline_comparison_variant_overlap
        ),
        "pairwise_jaccard_index_range": summarize_distribution(
            [summary["jaccard_index"] for summary in pairwise_overlap_summary]
        ),
        "pairwise_candidate_overlap_fraction_range": summarize_distribution(
            [summary["left_overlap_fraction"] for summary in pairwise_overlap_summary]
        ),
    }


def summarize_distribution(values: list[float]) -> dict[str, float | None]:
    finite_values = [
        value
        for value in values
        if value is not None and isinstance(value, (int, float)) and math.isfinite(float(value))
    ]
    if not finite_values:
        return {"min": None, "max": None, "mean": None, "median": None}
    array = np.asarray(finite_values, dtype=float)
    return {
        "min": float(np.min(array)),
        "max": float(np.max(array)),
        "mean": float(np.mean(array)),
        "median": float(np.median(array)),
    }


def mask_bbox(mask: np.ndarray, terrain: dict[str, Any]) -> dict[str, float]:
    rows, cols = np.where(mask)
    if len(rows) == 0:
        return {"crs": "EPSG:2056", "xmin": 0.0, "ymin": 0.0, "xmax": 0.0, "ymax": 0.0}
    xmin = terrain["xllcorner"] + int(cols.min()) * terrain["cellsize"]
    xmax = terrain["xllcorner"] + (int(cols.max()) + 1) * terrain["cellsize"]
    ymin = terrain["yllcorner"] + (terrain["nrows"] - int(rows.max()) - 1) * terrain["cellsize"]
    ymax = terrain["yllcorner"] + (terrain["nrows"] - int(rows.min())) * terrain["cellsize"]
    return {
        "crs": "EPSG:2056",
        "xmin": xmin,
        "ymin": ymin,
        "xmax": xmax,
        "ymax": ymax,
    }


def dilate_mask(mask: np.ndarray, buffer_cells: int) -> np.ndarray:
    if buffer_cells <= 0:
        return mask.copy()
    dilated = mask.copy()
    rows, cols = np.where(mask)
    nrows, ncols = mask.shape
    for row, col in zip(rows, cols):
        row_min = max(0, row - buffer_cells)
        row_max = min(nrows - 1, row + buffer_cells)
        col_min = max(0, col - buffer_cells)
        col_max = min(ncols - 1, col + buffer_cells)
        dilated[row_min : row_max + 1, col_min : col_max + 1] = True
    return dilated


def candidate_sensitivity_report_stub() -> dict[str, Any]:
    return {
        "sensitivity_status": "blocked_missing_inputs",
        "sensitivity_scope": "bounded_threshold_smoothing_resolution_and_boundary_perturbations",
        "baseline_variant_id": "baseline",
        "variant_count": 0,
        "variant_summaries": [],
        "candidate_count_range": {"min": None, "max": None},
        "candidate_area_range_m2": {"min": None, "max": None},
        "baseline_candidate_cell_count": 0,
        "baseline_candidate_area_m2": 0.0,
        "union_candidate_cell_count": 0,
        "union_candidate_area_m2": 0.0,
        "stable_candidate_region": {
            "region_class": "stable_across_bounded_heuristics",
            "cell_count": 0,
            "area_m2": 0.0,
            "component_count": 0,
            "largest_component_cell_count": 0,
            "largest_component_area_m2": 0.0,
            "region_bbox_lv95_m": {"crs": "EPSG:2056", "xmin": 0.0, "ymin": 0.0, "xmax": 0.0, "ymax": 0.0},
            "coverage_fraction_of_union_candidate_cells": None,
            "coverage_fraction_of_baseline_candidate_cells": None,
        },
        "unstable_candidate_region": {
            "region_class": "unstable_across_bounded_heuristics",
            "cell_count": 0,
            "area_m2": 0.0,
            "component_count": 0,
            "largest_component_cell_count": 0,
            "largest_component_area_m2": 0.0,
            "region_bbox_lv95_m": {"crs": "EPSG:2056", "xmin": 0.0, "ymin": 0.0, "xmax": 0.0, "ymax": 0.0},
            "coverage_fraction_of_union_candidate_cells": None,
            "coverage_fraction_of_baseline_candidate_cells": None,
        },
        "heuristic_sensitive_candidate_region": {
            "region_class": "heuristic_sensitive_across_bounded_heuristics",
            "cell_count": 0,
            "area_m2": 0.0,
            "component_count": 0,
            "largest_component_cell_count": 0,
            "largest_component_area_m2": 0.0,
            "region_bbox_lv95_m": {"crs": "EPSG:2056", "xmin": 0.0, "ymin": 0.0, "xmax": 0.0, "ymax": 0.0},
            "coverage_fraction_of_union_candidate_cells": None,
            "coverage_fraction_of_baseline_candidate_cells": None,
        },
        "candidate_region_classifications": [],
        "candidate_sensitivity_matrix": [],
        "candidate_persistence_metrics": {},
        "pairwise_overlap_summary": [],
        "claim_boundaries": {
            "heuristic_stability_characterization_only": True,
            "validated_release_zone_evidence": False,
            "field_validation_claims_allowed": False,
            "physical_release_probability_claims_allowed": False,
            "scale_up_authorized": False,
            "operational_claims_allowed": False,
            "notes": [
                "bounded perturbations only characterize heuristic agreement and disagreement",
                "stable regions are agreement regions across bounded heuristic settings, not validated release zones",
                "unstable regions are heuristic-sensitive regions, not invalidated release zones",
                "heuristic-sensitive regions are candidate-persistence summaries, not validated release zones",
            ],
        },
    }


def emit_candidate_products(
    *,
    report: dict[str, Any],
    terrain: dict[str, Any],
    terrain_masks: dict[str, np.ndarray],
    source_zone_metadata: dict[str, Any],
    repo_root: Path,
    output_root: Path,
    output_mode: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    output_root = Path(output_root)
    output_root.mkdir(parents=True, exist_ok=True)
    source_zone_id = source_zone_metadata.get("source_zone_id") or report["candidate_site_id"]
    components = connected_candidate_components(terrain_masks["candidate_mask"])
    width = max(3, len(str(max(0, len(components) - 1))))
    component_features = [
        build_candidate_component_feature(
            terrain=terrain,
            terrain_masks=terrain_masks,
            source_zone_metadata=source_zone_metadata,
            component=cells,
            index=index,
            width=width,
            source_zone_id=str(source_zone_id),
            candidate_site_id=report["candidate_site_id"],
            source_inputs=[
                report["terrain_inputs"]["terrain_crop_path"],
                report["terrain_inputs"]["terrain_metadata_path"],
                report["source_zone_inputs"]["source_zone_metadata_path"],
            ],
            candidate_sensitivity_label=report["candidate_sensitivity_report"]["heuristic_sensitive_candidate_region"]["region_class"],
        )
        for index, cells in enumerate(components)
    ]
    component_area_values = [float(feature["properties"]["component_area_m2"]) for feature in component_features]

    manifest_path = output_root / f"{report['candidate_site_id']}_release_zone_candidates_manifest.json"
    product_bundle: dict[str, Any] = {
        "schema_version": PRODUCT_SCHEMA_VERSION,
        "output_status": "emitted",
        "output_mode": output_mode,
        "candidate_site_id": report["candidate_site_id"],
        "candidate_site_name": report["candidate_site_name"],
        "candidate_release_zone_set_status": "emitted",
        "source_zone_id": source_zone_id,
        "output_root": str(output_root),
        "outputs": {},
        "candidate_footprint_comparison": report["candidate_footprint_comparison"],
        "frozen_source_zone_footprint": report["frozen_source_zone_footprint"],
        "candidate_summary": report["candidate_summary"],
        "provenance": report["provenance"],
        "component_area_distribution_m2": summarize_distribution(component_area_values),
    }

    if output_mode in {"polygon", "both"}:
        polygon_path = output_root / f"{report['candidate_site_id']}_release_zone_candidates.geojson"
        polygon_payload = {
            "schema_version": PRODUCT_SCHEMA_VERSION,
            "type": "FeatureCollection",
            "candidate_generation_label": "heuristic_candidate_generation_only",
            "candidate_site_id": report["candidate_site_id"],
            "candidate_site_name": report["candidate_site_name"],
            "source_zone_id": source_zone_id,
            "features": component_features,
        }
        polygon_path.write_text(json.dumps(polygon_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        product_bundle["outputs"]["polygon"] = display_path(polygon_path, repo_root)
        product_bundle["polygon_feature_count"] = len(component_features)
        product_bundle["polygon_path"] = display_path(polygon_path, repo_root)

    if output_mode in {"mask", "both"}:
        mask_path = output_root / f"{report['candidate_site_id']}_release_zone_candidates_mask.asc"
        write_candidate_mask_ascii_grid(mask_path, terrain, terrain_masks["candidate_mask"])
        product_bundle["outputs"]["mask"] = display_path(mask_path, repo_root)
        product_bundle["mask_path"] = display_path(mask_path, repo_root)

    product_bundle["manifest_path"] = display_path(manifest_path, repo_root)
    product_bundle["candidate_release_zone_ids"] = [feature["properties"]["candidate_release_zone_id"] for feature in component_features]
    product_bundle["component_count"] = len(component_features)
    product_bundle["candidate_cell_count"] = int(terrain_masks["candidate_mask"].sum())
    product_bundle["candidate_excludes_frozen_footprint"] = report["candidate_footprint_comparison"]["candidate_excludes_frozen_footprint"]
    product_bundle["source_inputs"] = [
        report["terrain_inputs"]["terrain_crop_path"],
        report["terrain_inputs"]["terrain_metadata_path"],
        report["source_zone_inputs"]["source_zone_metadata_path"],
    ]
    manifest_path.write_text(json.dumps(product_bundle, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    product_bundle["outputs"]["manifest"] = display_path(manifest_path, repo_root)
    candidate_review_package = build_candidate_review_package(
        report=report,
        terrain=terrain,
        terrain_masks=terrain_masks,
        source_zone_id=str(source_zone_id),
        component_features=component_features,
        repo_root=repo_root,
        output_root=output_root,
    )
    return product_bundle, candidate_review_package


def build_candidate_review_package(
    *,
    report: dict[str, Any],
    terrain: dict[str, Any],
    terrain_masks: dict[str, np.ndarray],
    source_zone_id: str,
    component_features: list[dict[str, Any]],
    repo_root: Path,
    output_root: Path,
) -> dict[str, Any]:
    geojson_path = output_root / f"{report['candidate_site_id']}_release_zone_candidate_review.geojson"
    csv_path = output_root / f"{report['candidate_site_id']}_release_zone_candidate_review.csv"
    mask_path = output_root / f"{report['candidate_site_id']}_release_zone_candidate_review_mask.asc"
    manifest_path = output_root / f"{report['candidate_site_id']}_release_zone_candidate_review_manifest.json"

    review_rows = [build_candidate_review_row(feature) for feature in component_features]
    review_summary = build_candidate_review_summary(review_rows)
    review_geojson = {
        "schema_version": REVIEW_PACKAGE_SCHEMA_VERSION,
        "type": "FeatureCollection",
        "candidate_site_id": report["candidate_site_id"],
        "candidate_site_name": report["candidate_site_name"],
        "source_zone_id": source_zone_id,
        "candidate_generation_label": "heuristic_candidate_generation_only",
        "review_decision_options": list(REVIEW_DECISION_OPTIONS),
        "provenance_label_legend": provenance_label_legend(),
        "features": component_features,
    }
    geojson_path.write_text(json.dumps(review_geojson, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_candidate_mask_ascii_grid(mask_path, terrain, terrain_masks["candidate_mask"])
    write_candidate_review_csv(csv_path, review_rows)

    review_package = {
        "schema_version": REVIEW_PACKAGE_SCHEMA_VERSION,
        "review_package_status": "emitted",
        "candidate_site_id": report["candidate_site_id"],
        "candidate_site_name": report["candidate_site_name"],
        "source_zone_id": source_zone_id,
        "candidate_release_zone_set_status": "review_ready",
        "candidate_release_zone_ids": [feature["properties"]["candidate_release_zone_id"] for feature in component_features],
        "review_decision_options": list(REVIEW_DECISION_OPTIONS),
        "editable_acceptance_fields": ["review_decision", "accepted", "rejected", "needs_field_review"],
        "provenance_label_legend": provenance_label_legend(),
        "review_summary": review_summary,
        "candidate_review_rows": review_rows,
        "candidate_sensitivity_summary": candidate_review_sensitivity_summary(report["candidate_sensitivity_report"]),
        "candidate_footprint_comparison": report["candidate_footprint_comparison"],
        "frozen_source_zone_footprint": report["frozen_source_zone_footprint"],
        "claim_boundaries": report["claim_boundaries"],
        "outputs": {
            "polygon": display_path(geojson_path, repo_root),
            "mask": display_path(mask_path, repo_root),
            "csv": display_path(csv_path, repo_root),
            "manifest": display_path(manifest_path, repo_root),
        },
        "output_root": display_path(output_root, repo_root),
    }
    manifest_path.write_text(json.dumps(review_package, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return review_package


def summarize_distribution(values: list[float]) -> dict[str, float | None]:
    finite_values = [
        value
        for value in values
        if value is not None and isinstance(value, (int, float)) and math.isfinite(float(value))
    ]
    if not finite_values:
        return {"min": None, "max": None, "mean": None, "median": None, "p95": None}
    array = np.asarray(finite_values, dtype=float)
    return {
        "min": float(np.min(array)),
        "max": float(np.max(array)),
        "mean": float(np.mean(array)),
        "median": float(np.median(array)),
        "p95": float(np.quantile(array, 0.95)),
    }


def build_candidate_review_row(feature: dict[str, Any]) -> dict[str, Any]:
    properties = feature["properties"]
    return {
        "candidate_release_zone_id": properties["candidate_release_zone_id"],
        "candidate_generation_label": properties["candidate_generation_label"],
        "review_decision": properties["review_decision"],
        "accepted": properties["accepted"],
        "rejected": properties["rejected"],
        "needs_field_review": properties["needs_field_review"],
        "provenance_label": properties["provenance_label"],
        "candidate_sensitivity_label": properties["candidate_sensitivity_label"],
        "release_cell_count": properties["release_cell_count"],
        "release_cell_ids": ";".join(properties["release_cell_ids"]),
        "component_cell_count": properties["component_cell_count"],
        "component_area_m2": properties["component_area_m2"],
        "component_slope_min_deg": properties["component_slope_min_deg"],
        "component_slope_max_deg": properties["component_slope_max_deg"],
        "component_slope_mean_deg": properties["component_slope_mean_deg"],
        "component_slope_median_deg": properties["component_slope_median_deg"],
    }


def build_candidate_review_summary(review_rows: list[dict[str, Any]]) -> dict[str, Any]:
    decision_counts = {decision: 0 for decision in REVIEW_DECISION_OPTIONS}
    provenance_counts = {label: 0 for label in PROVENANCE_LABELS}
    for row in review_rows:
        review_decision = str(row.get("review_decision") or "")
        if review_decision in decision_counts:
            decision_counts[review_decision] += 1
        provenance_label = str(row.get("provenance_label") or "")
        if provenance_label in provenance_counts:
            provenance_counts[provenance_label] += 1
    return {
        "review_row_count": len(review_rows),
        "candidate_count": len(review_rows),
        "review_decision_counts": decision_counts,
        "provenance_label_counts": provenance_counts,
        "default_review_decision": "needs_field_review",
    }


def candidate_review_sensitivity_summary(candidate_sensitivity_report: dict[str, Any]) -> dict[str, Any]:
    return {
        "sensitivity_status": candidate_sensitivity_report.get("sensitivity_status"),
        "sensitivity_scope": candidate_sensitivity_report.get("sensitivity_scope"),
        "stable_candidate_region_label": candidate_sensitivity_report.get("stable_candidate_region", {}).get("region_class"),
        "unstable_candidate_region_label": candidate_sensitivity_report.get("unstable_candidate_region", {}).get("region_class"),
        "heuristic_sensitive_candidate_region_label": candidate_sensitivity_report.get("heuristic_sensitive_candidate_region", {}).get("region_class"),
        "candidate_region_classifications": [
            {
                "region_class": row.get("region_class"),
                "cell_count": row.get("cell_count"),
                "area_m2": row.get("area_m2"),
            }
            for row in candidate_sensitivity_report.get("candidate_region_classifications", [])
        ],
    }


def provenance_label_legend() -> list[dict[str, str]]:
    return [
        {
            "provenance_label": "workflow_generated",
            "meaning": "Candidate generated from workflow terrain and context screening only.",
        },
        {
            "provenance_label": "field_supported",
            "meaning": "Candidate can only be treated as field-supported once review has explicitly accepted it.",
        },
        {
            "provenance_label": "mixed_provenance",
            "meaning": "Candidate combines workflow generation with accepted field support.",
        },
        {
            "provenance_label": "blocked_missing_provenance",
            "meaning": "Candidate cannot be treated as evidence because provenance is missing or overclaimed.",
        },
    ]


def candidate_review_package_stub(*, repo_root: Path) -> dict[str, Any]:
    return {
        "schema_version": REVIEW_PACKAGE_SCHEMA_VERSION,
        "review_package_status": "not_emitted",
        "candidate_site_id": "tschamut_public_pilot",
        "candidate_site_name": "Balfrin / Tschamut AOI",
        "source_zone_id": None,
        "candidate_release_zone_set_status": "not_emitted",
        "candidate_release_zone_ids": [],
        "review_decision_options": list(REVIEW_DECISION_OPTIONS),
        "editable_acceptance_fields": ["review_decision", "accepted", "rejected", "needs_field_review"],
        "provenance_label_legend": provenance_label_legend(),
        "review_summary": {
            "review_row_count": 0,
            "candidate_count": 0,
            "review_decision_counts": {decision: 0 for decision in REVIEW_DECISION_OPTIONS},
            "provenance_label_counts": {label: 0 for label in PROVENANCE_LABELS},
            "default_review_decision": "needs_field_review",
        },
        "candidate_review_rows": [],
        "candidate_sensitivity_summary": {},
        "candidate_footprint_comparison": {},
        "frozen_source_zone_footprint": {},
        "claim_boundaries": {
            "heuristic_workflow_input_only": True,
            "validated_release_zone_evidence": False,
            "field_validation_claims_allowed": False,
            "physical_release_probability_claims_allowed": False,
            "scale_up_authorized": False,
            "operational_claims_allowed": False,
            "notes": [
                "candidate review rows remain workflow review inputs until the source zone is frozen",
                "accepted, rejected, and needs_field_review are editable review states, not evidence claims",
                "no annual-frequency, risk, exposure, or vulnerability claim is authorized here",
            ],
        },
        "outputs": {
            "polygon": None,
            "mask": None,
            "csv": None,
            "manifest": None,
        },
        "output_root": None,
        "repo_root": str(repo_root),
    }


def write_candidate_review_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    columns = [
        "candidate_release_zone_id",
        "candidate_generation_label",
        "review_decision",
        "accepted",
        "rejected",
        "needs_field_review",
        "provenance_label",
        "candidate_sensitivity_label",
        "release_cell_count",
        "release_cell_ids",
        "component_cell_count",
        "component_area_m2",
        "component_slope_min_deg",
        "component_slope_max_deg",
        "component_slope_mean_deg",
        "component_slope_median_deg",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: csv_safe_value(row.get(column)) for column in columns})


def csv_safe_value(value: Any) -> Any:
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, list):
        return ";".join(str(item) for item in value)
    if value is None:
        return ""
    return value


def connected_candidate_components(candidate_mask: np.ndarray) -> list[list[tuple[int, int]]]:
    nrows, ncols = candidate_mask.shape
    visited = np.zeros_like(candidate_mask, dtype=bool)
    components: list[list[tuple[int, int]]] = []
    for row in range(nrows):
        for col in range(ncols):
            if not candidate_mask[row, col] or visited[row, col]:
                continue
            component = flood_fill_component(candidate_mask, visited, row, col)
            component.sort()
            components.append(component)
    components.sort(key=component_sort_key)
    return components


def flood_fill_component(
    candidate_mask: np.ndarray,
    visited: np.ndarray,
    start_row: int,
    start_col: int,
) -> list[tuple[int, int]]:
    stack = [(start_row, start_col)]
    visited[start_row, start_col] = True
    cells: list[tuple[int, int]] = []
    nrows, ncols = candidate_mask.shape
    while stack:
        row, col = stack.pop()
        cells.append((row, col))
        for next_row, next_col in (
            (row - 1, col),
            (row, col - 1),
            (row, col + 1),
            (row + 1, col),
        ):
            if next_row < 0 or next_row >= nrows or next_col < 0 or next_col >= ncols:
                continue
            if visited[next_row, next_col] or not candidate_mask[next_row, next_col]:
                continue
            visited[next_row, next_col] = True
            stack.append((next_row, next_col))
    return cells


def component_sort_key(component: list[tuple[int, int]]) -> tuple[int, int, int, int, int]:
    rows = [row for row, _ in component]
    cols = [col for _, col in component]
    return (min(rows), min(cols), max(rows), max(cols), len(component))


def build_candidate_component_feature(
    *,
    terrain: dict[str, Any],
    terrain_masks: dict[str, np.ndarray],
    source_zone_metadata: dict[str, Any],
    component: list[tuple[int, int]],
    index: int,
    width: int,
    source_zone_id: str,
    candidate_site_id: str,
    source_inputs: list[str],
    candidate_sensitivity_label: str,
) -> dict[str, Any]:
    component_mask = np.zeros_like(terrain_masks["candidate_mask"], dtype=bool)
    for row, col in component:
        component_mask[row, col] = True
    slope_deg = terrain_masks["slope_deg"][component_mask]
    candidate_release_zone_id = report_candidate_id(source_zone_id, index, width)
    cell_area_m2 = terrain["cellsize"] ** 2
    release_cell_ids = [release_cell_id(candidate_release_zone_id, row, col) for row, col in component]
    properties = {
        "candidate_release_zone_id": candidate_release_zone_id,
        "candidate_generation_label": "heuristic_candidate_generation_only",
        "candidate_site_id": candidate_site_id,
        "source_zone_id": source_zone_id,
        "source_inputs": source_inputs,
        "provenance_ref": "terrain_and_source_zone_inputs",
        "provenance_label": "workflow_generated",
        "component_index": index,
        "component_cell_count": len(component),
        "component_area_m2": len(component) * cell_area_m2,
        "component_slope_min_deg": float(np.min(slope_deg)) if len(slope_deg) else None,
        "component_slope_max_deg": float(np.max(slope_deg)) if len(slope_deg) else None,
        "component_slope_mean_deg": float(np.mean(slope_deg)) if len(slope_deg) else None,
        "component_slope_median_deg": float(np.median(slope_deg)) if len(slope_deg) else None,
        "comparison_to_frozen_footprint_cell_count": int((component_mask & terrain_masks["footprint_mask"]).sum()),
        "comparison_to_frozen_footprint_excludes_source_zone": bool(not (component_mask & terrain_masks["footprint_mask"]).any()),
        "release_cell_ids": release_cell_ids,
        "release_cell_count": len(release_cell_ids),
        "review_decision": "needs_field_review",
        "accepted": False,
        "rejected": False,
        "needs_field_review": True,
        "candidate_sensitivity_label": candidate_sensitivity_label,
        "review_editable": True,
    }
    geometry = component_multipolygon_geometry(component, terrain)
    bbox = component_bbox(component, terrain)
    properties["component_bbox_lv95_m"] = bbox
    properties["source_zone_footprint_area_m2_exact"] = polygon_area(extract_polygon_vertices(source_zone_metadata))
    return {
        "type": "Feature",
        "id": properties["candidate_release_zone_id"],
        "geometry": geometry,
        "properties": properties,
    }


def release_cell_id(candidate_release_zone_id: str, row: int, col: int) -> str:
    return f"{candidate_release_zone_id}__cell_r{row:03d}_c{col:03d}"


def report_candidate_id(source_zone_id: str, index: int, width: int) -> str:
    return f"{source_zone_id}_candidate_{index:0{width}d}"


def component_multipolygon_geometry(component: list[tuple[int, int]], terrain: dict[str, Any]) -> dict[str, Any]:
    coordinates = []
    for row, col in component:
        coordinates.append([cell_polygon_coordinates(row, col, terrain)])
    return {"type": "MultiPolygon", "coordinates": coordinates}


def cell_polygon_coordinates(row: int, col: int, terrain: dict[str, Any]) -> list[list[float]]:
    x0 = terrain["xllcorner"] + col * terrain["cellsize"]
    x1 = x0 + terrain["cellsize"]
    y0 = terrain["yllcorner"] + (terrain["nrows"] - row - 1) * terrain["cellsize"]
    y1 = y0 + terrain["cellsize"]
    return [
        [x0, y0],
        [x1, y0],
        [x1, y1],
        [x0, y1],
        [x0, y0],
    ]


def component_bbox(component: list[tuple[int, int]], terrain: dict[str, Any]) -> dict[str, float]:
    rows = [row for row, _ in component]
    cols = [col for _, col in component]
    xmin = terrain["xllcorner"] + min(cols) * terrain["cellsize"]
    xmax = terrain["xllcorner"] + (max(cols) + 1) * terrain["cellsize"]
    ymin = terrain["yllcorner"] + (terrain["nrows"] - max(rows) - 1) * terrain["cellsize"]
    ymax = terrain["yllcorner"] + (terrain["nrows"] - min(rows)) * terrain["cellsize"]
    return {
        "crs": "EPSG:2056",
        "xmin": xmin,
        "ymin": ymin,
        "xmax": xmax,
        "ymax": ymax,
    }


def polygon_bbox(vertices: list[tuple[float, float]]) -> dict[str, float]:
    if not vertices:
        return {"crs": "EPSG:2056", "xmin": 0.0, "ymin": 0.0, "xmax": 0.0, "ymax": 0.0}
    xs = [vertex[0] for vertex in vertices]
    ys = [vertex[1] for vertex in vertices]
    return {
        "crs": "EPSG:2056",
        "xmin": min(xs),
        "ymin": min(ys),
        "xmax": max(xs),
        "ymax": max(ys),
    }


def write_candidate_mask_ascii_grid(mask_path: Path, terrain: dict[str, Any], candidate_mask: np.ndarray) -> None:
    lines = [
        f"ncols {terrain['ncols']}",
        f"nrows {terrain['nrows']}",
        f"xllcorner {format_number(terrain['xllcorner'])}",
        f"yllcorner {format_number(terrain['yllcorner'])}",
        f"cellsize {format_number(terrain['cellsize'])}",
        f"NODATA_value {format_number(terrain['nodata_value'])}",
    ]
    values = np.where(candidate_mask, 1.0, terrain["nodata_value"])
    for row in values:
        lines.append(" ".join(format_number(float(value)) for value in row))
    mask_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def format_number(value: float) -> str:
    if float(value).is_integer():
        return str(int(value))
    return f"{value:g}"


def point_in_polygon_mask(terrain: dict[str, Any], vertices: list[tuple[float, float]]) -> np.ndarray:
    mask = np.zeros((terrain["nrows"], terrain["ncols"]), dtype=bool)
    if not vertices:
        return mask
    for row in range(terrain["nrows"]):
        y = terrain["yllcorner"] + (terrain["nrows"] - row - 0.5) * terrain["cellsize"]
        for col in range(terrain["ncols"]):
            x = terrain["xllcorner"] + (col + 0.5) * terrain["cellsize"]
            mask[row, col] = point_in_polygon(x, y, vertices)
    return mask


def point_in_polygon(x: float, y: float, vertices: list[tuple[float, float]]) -> bool:
    inside = False
    j = len(vertices) - 1
    for i, (xi, yi) in enumerate(vertices):
        xj, yj = vertices[j]
        intersects = ((yi > y) != (yj > y)) and (
            x < ((xj - xi) * (y - yi)) / ((yj - yi) if (yj - yi) != 0 else 1e-12) + xi
        )
        if intersects:
            inside = not inside
        j = i
    return inside


def extract_polygon_vertices(source_zone_metadata: dict[str, Any]) -> list[tuple[float, float]]:
    geometry = source_zone_metadata.get("geometry", {})
    raw_vertices = None
    if isinstance(geometry, dict):
        raw_vertices = geometry.get("vertices") or geometry.get("coordinates")
    if not isinstance(raw_vertices, list):
        return []
    vertices: list[tuple[float, float]] = []
    for entry in raw_vertices:
        if not isinstance(entry, (list, tuple)) or len(entry) < 2:
            continue
        vertices.append((float(entry[0]), float(entry[1])))
    if vertices and vertices[0] == vertices[-1]:
        vertices.pop()
    return vertices


def polygon_area(vertices: list[tuple[float, float]]) -> float:
    if len(vertices) < 3:
        return 0.0
    area = 0.0
    for idx, (x0, y0) in enumerate(vertices):
        x1, y1 = vertices[(idx + 1) % len(vertices)]
        area += x0 * y1 - x1 * y0
    return abs(area) / 2.0


def build_provenance(
    terrain_crop_path: Path,
    terrain_metadata_path: Path,
    source_zone_metadata_path: Path,
    terrain_metadata: dict[str, Any],
    source_zone_metadata: dict[str, Any],
) -> dict[str, Any]:
    return {
        "terrain_source": {
            "source_dataset": terrain_metadata.get("source_dataset"),
            "source_product": terrain_metadata.get("source_product"),
            "source_url": terrain_metadata.get("source_url"),
            "source_filename": terrain_metadata.get("source_filename"),
            "source_file_present": terrain_metadata.get("source_file_present"),
            "download_status": terrain_metadata.get("download_status"),
            "license": terrain_metadata.get("license"),
            "processed_utc": terrain_metadata.get("preprocessing", {}).get("processed_utc"),
            "raw_sha256": terrain_metadata.get("preprocessing", {}).get("raw_sha256"),
            "processed_sha256": terrain_metadata.get("preprocessing", {}).get("processed_sha256"),
            "tool": terrain_metadata.get("preprocessing", {}).get("tool"),
            "crop_extent_lv95_m": terrain_metadata.get("preprocessing", {}).get("crop_extent_lv95_m"),
            "terrain_crop_sha256": sha256_file(terrain_crop_path),
            "terrain_metadata_sha256": sha256_file(terrain_metadata_path),
        },
        "source_zone_source": {
            "source_zone_id": source_zone_metadata.get("source_zone_id"),
            "license": source_zone_metadata.get("provenance", {}).get("license"),
            "source": source_zone_metadata.get("provenance", {}).get("source"),
            "notes": source_zone_metadata.get("provenance", {}).get("notes", []),
            "source_zone_metadata_sha256": sha256_file(source_zone_metadata_path),
        },
        "heuristic_notes": [
            "cell-center inclusion against the frozen source-zone polygon is deterministic",
            "the 3x3 Horn slope kernel is fixed and does not fit outcomes",
            "candidate cells are workflow inputs only and are not validated release zones",
        ],
    }


def read_esri_ascii_grid(path: Path) -> dict[str, Any]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if len(lines) < 6:
        raise TerrainReleaseZoneCandidateMetricsError(f"ESRI ASCII grid is too short: {path}")

    header: dict[str, float] = {}
    for line in lines[:6]:
        key, value = line.split(maxsplit=1)
        header[key.lower()] = float(value)

    ncols = int(header["ncols"])
    nrows = int(header["nrows"])
    cellsize = float(header["cellsize"])
    nodata = float(header.get("nodata_value", NODATA_SENTINEL))
    data = np.loadtxt(lines[6:], dtype=float)
    if data.shape != (nrows, ncols):
        raise TerrainReleaseZoneCandidateMetricsError(
            f"terrain grid shape mismatch for {path}: expected {(nrows, ncols)}, got {data.shape}"
        )
    valid_mask = np.isfinite(data) & (data != nodata)
    data = np.where(valid_mask, data, np.nan)
    return {
        "values": data,
        "valid_mask": valid_mask,
        "ncols": ncols,
        "nrows": nrows,
        "xllcorner": float(header.get("xllcorner", 0.0)),
        "yllcorner": float(header.get("yllcorner", 0.0)),
        "cellsize": cellsize,
        "nodata_value": nodata,
    }


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - file context matters.
        raise TerrainReleaseZoneCandidateMetricsError(f"failed to read YAML {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise TerrainReleaseZoneCandidateMetricsError(f"expected YAML mapping in {path}")
    return data


def load_yaml_or_json(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        data = json.loads(text)
    else:
        try:
            data = yaml.safe_load(text)
        except Exception:
            data = json.loads(text)
    if not isinstance(data, dict):
        raise TerrainReleaseZoneCandidateMetricsError(f"expected YAML or JSON mapping in {path}")
    return data


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def display_path(path: Path, repo_root: Path) -> str:
    try:
        return str(path.relative_to(repo_root))
    except ValueError:
        return str(path)


def repo_path(value: Any) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise TerrainReleaseZoneCandidateMetricsError("missing output path value")
    path = Path(value)
    return path if path.is_absolute() else (ROOT / path)


def text_value(value: Any) -> str:
    return str(value).strip() if value not in (None, "") else ""


def package_path(review_package: dict[str, Any], value: Any) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise TerrainReleaseZoneCandidateMetricsError("missing package path value")
    path = Path(value)
    if path.is_absolute():
        return path
    repo_root = text_value(review_package.get("repo_root"))
    base_root = Path(repo_root) if repo_root else ROOT
    return base_root / path


def resolve_path(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else (repo_root / path).resolve()


def is_allowed_output_root(output_root: Path) -> bool:
    resolved = output_root.resolve(strict=False)
    allowed_roots = [
        Path("/tmp"),
        Path("/private/tmp"),
        ROOT / "validation/private",
        ROOT / "data/processed/swisstopo",
        ROOT / "validation/policies",
        ROOT / "hazard/results",
        ROOT / "validation/results",
        ROOT / "verification/results",
        ROOT / "target",
    ]
    return any(resolved == root or resolved.is_relative_to(root) for root in allowed_roots)


def default_repo_path(repo_root: Path, path: Path) -> Path:
    try:
        rel = path.relative_to(ROOT)
    except ValueError:
        return path
    return (repo_root / rel).resolve()


def fraction(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return numerator / denominator


def render_text_report(report: dict[str, Any]) -> str:
    lines = [
        f"schema_version: {report['schema_version']}",
        f"candidate_metrics_status: {report['candidate_metrics_status']}",
        f"candidate_release_zone_set_status: {report['candidate_release_zone_set_status']}",
        f"candidate_release_zone_interpretation: {report['candidate_release_zone_interpretation']}",
        f"candidate_site_id: {report['candidate_site_id']}",
        f"candidate_site_name: {report['candidate_site_name']}",
        f"candidate_selection_rationale: {report['candidate_selection_rationale']}",
        "",
        "terrain_preprocessing:",
    ]
    lines.extend(render_mapping(report.get("terrain_preprocessing") or {}))
    lines.append("")
    lines.append("screening_criteria:")
    lines.extend(f"- {key}: {value}" for key, value in report["screening_criteria"].items())
    lines.append("")
    lines.append("terrain_summary:")
    lines.extend(render_mapping(report["terrain_summary"]))
    lines.append("")
    lines.append("candidate_summary:")
    lines.extend(render_mapping(report["candidate_summary"]))
    lines.append("")
    lines.append("candidate_sensitivity_report:")
    lines.extend(render_mapping(report["candidate_sensitivity_report"]))
    lines.append("")
    lines.append("frozen_source_zone_footprint:")
    lines.extend(render_mapping(report["frozen_source_zone_footprint"]))
    lines.append("")
    lines.append("candidate_footprint_comparison:")
    lines.extend(render_mapping(report["candidate_footprint_comparison"]))
    lines.append("")
    lines.append("excluded_area_summary:")
    for row in report["excluded_area_summary"]:
        lines.append(
            f"- {row['category']}: cell_count={row['cell_count']}, area_m2={row['area_m2']}, reason={row['reason']}"
        )
    lines.append("")
    lines.append("source_zone_inputs:")
    lines.extend(render_mapping(report["source_zone_inputs"]))
    lines.append("")
    lines.append("terrain_inputs:")
    lines.extend(render_mapping(report["terrain_inputs"]))
    lines.append("")
    lines.append("provenance:")
    lines.extend(render_mapping(report["provenance"]))
    lines.append("")
    lines.append("candidate_release_zone_products:")
    lines.extend(render_mapping(report["candidate_release_zone_products"]))
    lines.append("")
    lines.append("candidate_review_package:")
    lines.extend(render_mapping(report["candidate_review_package"]))
    lines.append("")
    lines.append("claim_boundaries:")
    lines.extend(render_mapping(report["claim_boundaries"]))
    lines.append("")
    lines.append(f"blocked_reason: {report['blocked_reason']}")
    return "\n".join(lines)


def render_review_apply_text_report(report: dict[str, Any]) -> str:
    validation = report.get("review_application", {}).get("validation_checks", {})
    lines = [
        "Candidate Review Apply",
        "",
        f"- Schema version: `{report['schema_version']}`",
        f"- Review package status: `{report.get('review_package_status', '')}`",
        f"- Review application status: `{report.get('review_application_status', '')}`",
        f"- Accepted candidate count: `{len(report.get('accepted_candidate_ids', []))}`",
        f"- Rejected candidate count: `{len(report.get('rejected_candidate_ids', []))}`",
        f"- Needs field review candidate count: `{len(report.get('needs_field_review_candidate_ids', []))}`",
        "",
        "Validation",
        f"- validation_status: `{report.get('review_application', {}).get('validation_status', '')}`",
        f"- unknown_candidate_ids: `{', '.join(validation.get('unknown_candidate_ids', []))}`",
        f"- unreviewed_accepted_candidate_ids: `{', '.join(validation.get('unreviewed_accepted_candidate_ids', []))}`",
        f"- mixed_provenance_overclaim_candidate_ids: `{', '.join(validation.get('mixed_provenance_overclaim_candidate_ids', []))}`",
        f"- accepted_missing_validation_candidate_ids: `{', '.join(validation.get('accepted_missing_validation_candidate_ids', []))}`",
        "",
        "Output Paths",
    ]
    for key, value in (report.get("outputs") or {}).items():
        lines.append(f"- {key}: `{value}`")
    return "\n".join(lines)


def render_mapping(mapping: dict[str, Any], indent: str = "") -> list[str]:
    lines: list[str] = []
    for key, value in mapping.items():
        if isinstance(value, dict):
            lines.append(f"{indent}- {key}:")
            lines.extend(render_mapping(value, indent=f"{indent}  "))
        elif isinstance(value, list):
            lines.append(f"{indent}- {key}:")
            for item in value:
                if isinstance(item, dict):
                    lines.append(f"{indent}  -")
                    lines.extend(render_mapping(item, indent=f"{indent}    "))
                else:
                    lines.append(f"{indent}  - {item}")
        else:
            lines.append(f"{indent}- {key}: {value}")
    return lines


if __name__ == "__main__":
    raise SystemExit(main())
