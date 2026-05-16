#!/usr/bin/env python3
"""Map physical credibility requirements to concrete evidence sources.

This helper is read-only. It composes the existing validation-gap, holdout,
and dataset metadata into a machine-readable evidence-requirements matrix.
It does not calibrate, fit, tune, download geodata, or run simulations.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    import yaml  # type: ignore
except ImportError as exc:  # pragma: no cover - environment setup.
    raise SystemExit("PyYAML is required; install with `python3 -m pip install PyYAML`") from exc

from scripts import assess_validation_calibration_evidence_gaps as assessment
from scripts import summarize_chant_sura_holdout_evidence as chant_holdout


SCHEMA_VERSION = "physical_credibility_evidence_requirements_v1"

REQUIRED_INPUT_PATHS = (
    ROOT / "data/datasets.yaml",
    ROOT / "validation/data/processed/chant_sura_2020/holdout_validation_evidence_manifest.json",
    ROOT / "validation/data/processed/chant_sura_2020/metadata_contact_split.json",
    ROOT / "validation/cases/chant_sura_contact_heldout.yaml",
    ROOT / "docs/public_real_site_geodata_preparation.md",
    ROOT / "docs/swisstopo_data_strategy.md",
    ROOT / "docs/tschamut_public_conditional_pilot_gate_report.md",
)

EVIDENCE_ACQUISITION_PRIORITY_BLUEPRINTS = (
    {
        "category": "observed_runout_deposition",
        "priority": 1,
        "priority_label": "first_actionable",
        "expected_claim_unlocked": "Stronger physical-credibility interpretation of observed runout and deposition against an independent benchmark.",
        "required_data": [
            "Independent holdout field or benchmark deposition/runout geometry with explicit spatial reference",
            "Provenance, QA, and measurement metadata for the observed runout/deposition record",
            "A separation note showing the evidence was not reused for model selection or calibration",
        ],
        "current_repo_gap": "Current repo evidence is diagnostic and holdout-adjacent, but it does not yet include an independent field or benchmark deposition/runout acquisition.",
    },
    {
        "category": "release_zone_evidence",
        "priority": 2,
        "priority_label": "near_term_supporting",
        "expected_claim_unlocked": "Testable release-zone provenance for site-specific physical interpretation.",
        "required_data": [
            "Site-specific release-zone geometry package with LV95 / CRS provenance",
            "Field reconnaissance, mapping, or reference-data basis for the release-zone boundary",
            "Documentation showing the release-zone package is distinct from the frozen conditional contract",
        ],
        "current_repo_gap": "The repo has manifest and policy scaffolding, but no site-specific field-derived release-zone package that can stand as physical evidence.",
    },
    {
        "category": "independent_holdout_validation",
        "priority": 3,
        "priority_label": "validation_boundary",
        "expected_claim_unlocked": "Independent validation credibility separated from model selection.",
        "required_data": [
            "Independent holdout benchmark dataset with explicit split rules",
            "Scoring protocol separated from calibration and model-selection fixtures",
            "Holdout benchmark provenance showing the evidence was not reused for tuning",
        ],
        "current_repo_gap": "The repo already has holdout fixtures and split metadata, but the holdout evidence remains contact/trajectory validation rather than a broader physical-credibility benchmark.",
    },
    {
        "category": "calibration_data_and_objective_functions",
        "priority": 4,
        "priority_label": "calibration_ready_only",
        "expected_claim_unlocked": "Calibration-readiness for parameter-fitting claims, if calibration is later authorized.",
        "required_data": [
            "Calibration dataset with explicit objective function and measurement targets",
            "Parameter bounds and fit record",
            "A reserved calibration split separated from the holdout benchmark",
        ],
        "current_repo_gap": "The repo contains model-selection and holdout fixtures, but no calibration dataset, objective function, or fit record.",
    },
    {
        "category": "multi_site_transfer_evidence",
        "priority": 5,
        "priority_label": "transfer_generalization",
        "expected_claim_unlocked": "Portable second-site generalization evidence across site-specific public inputs.",
        "required_data": [
            "Staged second-site public geodata package with matching terrain, source-zone, scenario, and context inputs",
            "Independent second-site holdout benchmark",
            "A site-specific portability record showing the second site is not just metadata-ready",
        ],
        "current_repo_gap": "The repo has a second-site candidate manifest and acquisition contract, but no staged real public-context package or independent second-site benchmark.",
    },
    {
        "category": "block_size_and_block_population_evidence",
        "priority": 6,
        "priority_label": "physical_probability_bridge",
        "expected_claim_unlocked": "Physical-probability semantics from block-size or block-population distributions, if that claim phase is authorized later.",
        "required_data": [
            "Block-size survey or photogrammetry census",
            "Observed block-population counts or a defensible reference-data proxy",
            "Documentation that ties the block-population record to a frequency interpretation",
        ],
        "current_repo_gap": "The repo has trajectory/contact proxies and split bookkeeping, but no block-population survey or frequency-bearing census.",
    },
    {
        "category": "source_frequency_and_temporal_frequency_evidence",
        "priority": 7,
        "priority_label": "deferred_frequency_semantics",
        "expected_claim_unlocked": "Source-frequency and annual-frequency semantics, if a physical-probability phase change is later authorized.",
        "required_data": [
            "Historical rockfall event catalogue",
            "Repeat source-zone observations with temporal window and censoring rules",
            "A source-occurrence record that can support frequency semantics instead of only conditional sampling",
        ],
        "current_repo_gap": "The repo only has conditional benchmarks and trajectory inventories; it does not stage source-occurrence or temporal-frequency data.",
    },
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    parser.add_argument(
        "--evidence-json",
        type=Path,
        default=None,
        help="optional override JSON file for tests or alternate evidence snapshots",
    )
    args = parser.parse_args(argv)

    report = build_report(load_evidence_override(args.evidence_json))

    if args.json_output is not None:
        output_path = args.json_output if args.json_output.is_absolute() else ROOT / args.json_output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    output = json.dumps(report, indent=2, sort_keys=True) if args.format == "json" else render_text_report(report)
    print(output)
    return 2 if report["physical_credibility_requirements_status"] == "blocked_missing_inputs" else 0


def load_evidence_override(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    if not path.exists():
        return {"missing_inputs": [str(path)]}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return {"missing_inputs": [str(path)]}
    return data


def build_report(evidence_override: dict[str, Any] | None = None) -> dict[str, Any]:
    override_missing = [str(item) for item in (evidence_override or {}).get("missing_inputs", []) if str(item).strip()]
    missing_inputs = override_missing or missing_required_inputs()
    if missing_inputs:
        return blocked_report(missing_inputs)

    datasets = load_dataset_registry()
    gap_report = assessment.build_report()
    holdout_report = chant_holdout.build_report()

    categories = build_evidence_requirement_categories(datasets, gap_report, holdout_report)
    candidate_sources = build_candidate_data_sources(categories)
    acquisition_matrix = build_evidence_acquisition_matrix(categories)
    missing_acquisition_classes = sorted(
        {
            entry["class_name"]
            for category in categories
            for entry in category["future_acquisition_classes"]
        }
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "physical_credibility_requirements_status": "mapped_current_gaps",
        "current_physical_credibility_status": gap_report.get("physical_credibility_status", "unknown"),
        "calibration_status": gap_report.get("calibration_status", "unknown"),
        "validation_status": gap_report.get("validation_status", "unknown"),
        "evidence_requirement_categories": categories,
        "evidence_acquisition_matrix": acquisition_matrix,
        "candidate_data_sources": candidate_sources,
        "missing_acquisition_classes": missing_acquisition_classes,
        "calibration_split_requirements": calibration_split_requirements(holdout_report),
        "holdout_validation_requirements": holdout_validation_requirements(holdout_report),
        "source_frequency_requirements": source_frequency_requirements(datasets, gap_report),
        "intensity_frequency_status": "deferred_unsupported",
        "evidence_acquisition_summary": evidence_acquisition_summary(acquisition_matrix),
        "claim_boundaries": claim_boundaries(),
        "blocked_reason": None,
        "missing_inputs": [],
        "current_evidence_summary": current_evidence_summary(gap_report, holdout_report),
    }


def blocked_report(missing_inputs: list[str]) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "physical_credibility_requirements_status": "blocked_missing_inputs",
        "current_physical_credibility_status": "blocked_missing_inputs",
        "calibration_status": "blocked_missing_inputs",
        "validation_status": "blocked_missing_inputs",
        "evidence_requirement_categories": [],
        "evidence_acquisition_matrix": [],
        "candidate_data_sources": [],
        "missing_acquisition_classes": [],
        "calibration_split_requirements": [],
        "holdout_validation_requirements": [],
        "source_frequency_requirements": [],
        "intensity_frequency_status": "blocked_missing_inputs",
        "evidence_acquisition_summary": {
            "first_actionable_category": None,
            "deferred_category": None,
            "priority_order": [],
        },
        "claim_boundaries": claim_boundaries(),
        "blocked_reason": "required evidence inputs are missing",
        "missing_inputs": sorted(set(missing_inputs)),
        "current_evidence_summary": [],
    }


def missing_required_inputs() -> list[str]:
    return [str(path) for path in REQUIRED_INPUT_PATHS if not path.exists()]


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def load_dataset_registry() -> dict[str, dict[str, Any]]:
    registry = load_yaml(ROOT / "data/datasets.yaml")
    datasets = registry.get("datasets")
    if not isinstance(datasets, list):
        return {}
    out: dict[str, dict[str, Any]] = {}
    for entry in datasets:
        if isinstance(entry, dict) and isinstance(entry.get("id"), str):
            out[entry["id"]] = entry
    return out


def dataset_label(datasets: dict[str, dict[str, Any]], dataset_id: str) -> str:
    entry = datasets.get(dataset_id, {})
    name = str(entry.get("name") or "").strip()
    return name or dataset_id


def evidence_source(
    *,
    category: str,
    kind: str,
    label: str,
    reference: str,
    status: str,
    role: str,
    notes: str,
) -> dict[str, Any]:
    return {
        "category": category,
        "source_kind": kind,
        "label": label,
        "reference": reference,
        "status": status,
        "role": role,
        "notes": notes,
    }


def build_evidence_requirement_categories(
    datasets: dict[str, dict[str, Any]],
    gap_report: dict[str, Any],
    holdout_report: dict[str, Any],
) -> list[dict[str, Any]]:
    categories = [
        {
            "category": "observed_runout_deposition",
            "current_repo_evidence_status": category_status(gap_report, "observed_deposition_runout_evidence"),
            "current_repo_evidence_sources": [
                {
                    "label": f"Tschamut 2014 ({dataset_label(datasets, 'tschamut2014')})",
                    "reference": "data/datasets.yaml:tschamut2014",
                    "status": "partial",
                    "role": "diagnostic deposition/runout benchmark",
                    "notes": "Supports workflow reproducibility and diagnostic QA, not physical credibility by itself.",
                },
                {
                    "label": "Chant Sura held-out contact validation manifest",
                    "reference": "validation/data/processed/chant_sura_2020/holdout_validation_evidence_manifest.json",
                    "status": "present",
                    "role": "independent holdout validation evidence",
                    "notes": "Separated from model-selection fixtures and kept as a holdout boundary reference.",
                },
                {
                    "label": "Chant Sura held-out contact case",
                    "reference": "validation/cases/chant_sura_contact_heldout.yaml",
                    "status": "present",
                    "role": "independent holdout validation evidence",
                    "notes": "The held-out subset is disjoint from the internal model-selection subset.",
                },
            ],
            "future_acquisition_classes": [
                {
                    "class_name": "independent_holdout_field_deposition_runout_benchmark",
                    "label": "Independent holdout field deposition/runout benchmark",
                    "status": "missing",
                    "role": "future physical-credibility evidence",
                    "notes": "Would provide a benchmark not reused for current diagnostic selection.",
                },
                {
                    "class_name": "future_event_inventory_deposition_runout",
                    "label": "Future event inventory with deposition/runout geometry",
                    "status": "missing",
                    "role": "future physical-credibility evidence",
                    "notes": "A new event catalogue would strengthen observed runout/deposition coverage.",
                },
            ],
            "missing_acquisition_classes": [
                "independent_holdout_field_deposition_runout_benchmark",
                "future_event_inventory_deposition_runout",
            ],
            "why_it_matters": "Observed runout/deposition is the nearest analogue to physical credibility, but the current repo only has diagnostic and held-out contact proxies.",
        },
        {
            "category": "release_zone_evidence",
            "current_repo_evidence_status": category_status(gap_report, "release_zone_evidence"),
            "current_repo_evidence_sources": [
                {
                    "label": "Tschamut public pilot manifest",
                    "reference": "data/processed/swisstopo/tschamut_public_pilot_manifest.yaml",
                    "status": "partial",
                    "role": "frozen release-zone provenance for the Tschamut diagnostic pilot",
                    "notes": "Defines the current release-zone corridor and crop provenance.",
                },
                {
                    "label": "Tschamut source-scenario policy",
                    "reference": "validation/policies/tschamut_public_source_scenario_policy_v1.yaml",
                    "status": "partial",
                    "role": "conditional release/scenario contract",
                    "notes": "Provides deterministic release semantics for the pilot.",
                },
                {
                    "label": "Chant Sura / Flüelapass candidate acquisition manifest",
                    "reference": "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_public_geodata_acquisition.yaml",
                    "status": "partial",
                    "role": "public-context acquisition boundary for a second site",
                    "notes": "Separates the core staging contract from the deferred public-context bundle.",
                },
            ],
            "future_acquisition_classes": [
                {
                    "class_name": "site_specific_release_zone_geometry_package",
                    "label": "Site-specific release-zone geometry with provenance",
                    "status": "missing",
                    "role": "future physical-credibility evidence",
                    "notes": "Would need independent site-specific derivation and provenance metadata.",
                },
                {
                    "class_name": "field_reconnaissance_release_geometry",
                    "label": "Field reconnaissance or release-geometry survey",
                    "status": "missing",
                    "role": "future physical-credibility evidence",
                    "notes": "Would support a testable release-zone justification.",
                },
            ],
            "missing_acquisition_classes": [
                "site_specific_release_zone_geometry_package",
                "field_reconnaissance_release_geometry",
            ],
            "why_it_matters": "Release-zone evidence must be site-specific before it can be treated as credibility evidence rather than a frozen conditional contract.",
        },
        {
            "category": "block_size_and_block_population_evidence",
            "current_repo_evidence_status": category_status(gap_report, "block_size_and_block_population_evidence"),
            "current_repo_evidence_sources": [
                {
                    "label": "Chant Sura internal model-selection fixture",
                    "reference": "validation/internal/shape_contact_v0_chant_sura_model_selection.yaml",
                    "status": "missing",
                    "role": "proxy-only shape comparison",
                    "notes": "Proxy-only contact-model evidence, not a block-population frequency source.",
                },
                {
                    "label": "Chant Sura held-out split metadata",
                    "reference": "validation/data/processed/chant_sura_2020/metadata_contact_split.json",
                    "status": "partial",
                    "role": "deterministic split bookkeeping",
                    "notes": "Useful for benchmark separation, but not for population semantics.",
                },
                {
                    "label": f"Chant Sura dataset ({dataset_label(datasets, 'chant_sura_2020')})",
                    "reference": "data/datasets.yaml:chant_sura_2020",
                    "status": "partial",
                    "role": "trajectory/contact benchmark with shape and mass proxies",
                    "notes": "Contains public shape and mass-related context, but not block-population frequencies.",
                },
            ],
            "future_acquisition_classes": [
                {
                    "class_name": "block_size_survey_or_photogrammetry_census",
                    "label": "Block-size survey or photogrammetry census",
                    "status": "missing",
                    "role": "future physical-probability evidence",
                    "notes": "Would support block-size distributions and representative block-population semantics.",
                },
                {
                    "class_name": "source_occurrence_temporal_frequency_catalogue",
                    "label": "Source occurrence / temporal frequency catalogue",
                    "status": "missing",
                    "role": "future physical-probability evidence",
                    "notes": "Would help distinguish scenario sampling from physical occurrence frequency.",
                },
            ],
            "missing_acquisition_classes": [
                "block_size_survey_or_photogrammetry_census",
                "source_occurrence_temporal_frequency_catalogue",
            ],
            "why_it_matters": "Block-population or source-frequency semantics are required before any physical-probability claim can be made.",
        },
        {
            "category": "terrain_and_context_evidence",
            "current_repo_evidence_status": category_status(gap_report, "terrain_and_context_evidence"),
            "current_repo_evidence_sources": [
                {
                    "label": f"swissALTI3D ({dataset_label(datasets, 'swisstopo_swissalti3d')})",
                    "reference": "data/datasets.yaml:swisstopo_swissalti3d",
                    "status": "partial",
                    "role": "authoritative terrain input class",
                    "notes": "Terrain input is required for current and future pilots, but does not by itself establish credibility.",
                },
                {
                    "label": f"SWISSIMAGE ({dataset_label(datasets, 'swisstopo_swissimage')})",
                    "reference": "data/datasets.yaml:swisstopo_swissimage",
                    "status": "partial",
                    "role": "visual QA context class",
                    "notes": "Used for corridor review and interpretation, not as field validation.",
                },
                {
                    "label": f"swissTLM3D ({dataset_label(datasets, 'swisstopo_swisstlm3d')})",
                    "reference": "data/datasets.yaml:swisstopo_swisstlm3d",
                    "status": "partial",
                    "role": "transport / barrier / hydro context class",
                    "notes": "Supports interpretation of roads, water, and barriers where staged.",
                },
                {
                    "label": f"swissSURFACE3D Raster ({dataset_label(datasets, 'swisstopo_swisssurface3d_raster')})",
                    "reference": "data/datasets.yaml:swisstopo_swisssurface3d_raster",
                    "status": "partial",
                    "role": "surface / obstacle context class",
                    "notes": "Useful for canopy or surface-height QA, but still context rather than credibility evidence.",
                },
                {
                    "label": f"swissBUILDINGS3D ({dataset_label(datasets, 'swisstopo_swissbuildings3d')})",
                    "reference": "data/datasets.yaml:swisstopo_swissbuildings3d",
                    "status": "partial",
                    "role": "built-environment context class",
                    "notes": "Relevant for obstacle interpretation and future risk workflows, not current physical credibility.",
                },
            ],
            "future_acquisition_classes": [
                {
                    "class_name": "staged_second_site_public_context_bundle",
                    "label": "Staged second-site public-context bundle",
                    "status": "missing",
                    "role": "future physical-credibility evidence",
                    "notes": "Would provide concrete local products and metadata for a second site.",
                },
                {
                    "class_name": "independent_context_validation_benchmark",
                    "label": "Independent context-validation benchmark",
                    "status": "missing",
                    "role": "future physical-credibility evidence",
                    "notes": "Would test whether context interpretation is predictive rather than merely descriptive.",
                },
            ],
            "missing_acquisition_classes": [
                "staged_second_site_public_context_bundle",
                "independent_context_validation_benchmark",
            ],
            "why_it_matters": "Terrain/context products are essential inputs, but they remain interpretation aids until a separate validation benchmark is staged.",
        },
        {
            "category": "source_frequency_and_temporal_frequency_evidence",
            "current_repo_evidence_status": "missing",
            "current_repo_evidence_sources": [
                {
                    "label": f"Tschamut dataset ({dataset_label(datasets, 'tschamut2014')})",
                    "reference": "data/datasets.yaml:tschamut2014",
                    "status": "partial",
                    "role": "trajectory/test inventory only",
                    "notes": "Supports conditional diagnostics, but not source-occurrence rates.",
                },
                {
                    "label": f"Chant Sura dataset ({dataset_label(datasets, 'chant_sura_2020')})",
                    "reference": "data/datasets.yaml:chant_sura_2020",
                    "status": "partial",
                    "role": "trajectory/contact inventory only",
                    "notes": "Supports holdout validation and contact benchmarking, not temporal frequency semantics.",
                },
            ],
            "future_acquisition_classes": [
                {
                    "class_name": "historical_rockfall_event_catalogue",
                    "label": "Historical rockfall event catalogue",
                    "status": "missing",
                    "role": "future physical-probability evidence",
                    "notes": "Would provide an observed source-occurrence catalogue instead of a conditional sample.",
                },
                {
                    "class_name": "repeat_source_zone_observations",
                    "label": "Repeated source-zone observations",
                    "status": "missing",
                    "role": "future physical-probability evidence",
                    "notes": "Would support temporal-frequency and censoring assumptions.",
                },
            ],
            "missing_acquisition_classes": [
                "historical_rockfall_event_catalogue",
                "repeat_source_zone_observations",
            ],
            "why_it_matters": "Source-frequency evidence is required for intensity-frequency products; the current repo only has conditional sampling and benchmark trajectories.",
        },
        {
            "category": "calibration_data_and_objective_functions",
            "current_repo_evidence_status": category_status(gap_report, "calibration_evidence"),
            "current_repo_evidence_sources": [
                {
                    "label": "Chant Sura internal model-selection fixture",
                    "reference": "validation/internal/shape_contact_v0_chant_sura_model_selection.yaml",
                    "status": "missing",
                    "role": "diagnostic model comparison only",
                    "notes": "Useful for model selection, not for parameter fitting or calibration.",
                },
                {
                    "label": "Chant Sura held-out split metadata",
                    "reference": "validation/data/processed/chant_sura_2020/metadata_contact_split.json",
                    "status": "partial",
                    "role": "split bookkeeping only",
                    "notes": "Confirms a reserved split exists, but not a calibration objective.",
                },
            ],
            "future_acquisition_classes": [
                {
                    "class_name": "calibration_dataset_with_objective_function",
                    "label": "Calibration dataset with objective function",
                    "status": "missing",
                    "role": "future calibration evidence",
                    "notes": "Would be needed before any parameter fitting or calibration claim.",
                },
                {
                    "class_name": "parameter_bounds_and_fit_record",
                    "label": "Parameter bounds and fit record",
                    "status": "missing",
                    "role": "future calibration evidence",
                    "notes": "Would document fitted values and the optimization objective.",
                },
            ],
            "missing_acquisition_classes": [
                "calibration_dataset_with_objective_function",
                "parameter_bounds_and_fit_record",
            ],
            "why_it_matters": "Calibration requires a different evidence contract than the current diagnostic or holdout fixtures.",
        },
        {
            "category": "independent_holdout_validation",
            "current_repo_evidence_status": category_status(gap_report, "holdout_and_validation_evidence"),
            "current_repo_evidence_sources": [
                {
                    "label": "Chant Sura holdout validation manifest",
                    "reference": "validation/data/processed/chant_sura_2020/holdout_validation_evidence_manifest.json",
                    "status": "present",
                    "role": "independent holdout validation evidence",
                    "notes": "The held-out split is deterministic and disjoint from model-selection trajectories.",
                },
                {
                    "label": "Chant Sura held-out contact case",
                    "reference": "validation/cases/chant_sura_contact_heldout.yaml",
                    "status": "present",
                    "role": "independent holdout validation evidence",
                    "notes": "The held-out subset is disjoint from the internal model-selection subset.",
                },
                {
                    "label": "Chant Sura held-out rotational contact case",
                    "reference": "validation/cases/chant_sura_contact_heldout_rotational.yaml",
                    "status": "present",
                    "role": "independent holdout validation evidence",
                    "notes": "Rotational variant is part of the held-out split metadata boundary.",
                },
            ],
            "future_acquisition_classes": [
                {
                    "class_name": "independent_holdout_benchmark_dataset",
                    "label": "Independent holdout benchmark dataset",
                    "status": "partial",
                    "role": "future credibility evidence",
                    "notes": "Would need to remain separate from selection and calibration data.",
                },
                {
                    "class_name": "field_benchmark_not_reused_for_selection",
                    "label": "Field benchmark not reused for selection",
                    "status": "partial",
                    "role": "future credibility evidence",
                    "notes": "Would let holdout validation test predictive credibility rather than replay selection evidence.",
                },
            ],
            "missing_acquisition_classes": [
                "independent_holdout_benchmark_dataset",
                "field_benchmark_not_reused_for_selection",
            ],
            "why_it_matters": "The repo has partial holdout evidence, but it still does not establish physical credibility or calibration.",
        },
        {
            "category": "multi_site_transfer_evidence",
            "current_repo_evidence_status": category_status(gap_report, "multi_site_transfer_evidence"),
            "current_repo_evidence_sources": [
                {
                    "label": "Chant Sura / Flüelapass candidate manifest",
                    "reference": "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml",
                    "status": "partial",
                    "role": "second-site portability candidate",
                    "notes": "Keeps the candidate site explicit while the public-context boundary stays deferred.",
                },
                {
                    "label": "Chant Sura / Flüelapass acquisition manifest",
                    "reference": "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_public_geodata_acquisition.yaml",
                    "status": "partial",
                    "role": "public-context staging contract",
                    "notes": "Defines the exact public-context bundle expected for a second site.",
                },
                {
                    "label": "Second-site public geodata preflight",
                    "reference": "scripts/check_second_site_public_geodata_preflight.py",
                    "status": "partial",
                    "role": "metadata-only portability preflight",
                    "notes": "Separates reusable core readiness from deferred public-context readiness.",
                },
            ],
            "future_acquisition_classes": [
                {
                    "class_name": "staged_second_site_public_geodata_package",
                    "label": "Staged second-site public geodata package",
                    "status": "missing",
                    "role": "future portability evidence",
                    "notes": "Would show the second site can be prepared from real public context inputs.",
                },
                {
                    "class_name": "independent_second_site_holdout_benchmark",
                    "label": "Independent second-site holdout benchmark",
                    "status": "missing",
                    "role": "future portability evidence",
                    "notes": "Would be needed before portability becomes credibility rather than just metadata readiness.",
                },
            ],
            "missing_acquisition_classes": [
                "staged_second_site_public_geodata_package",
                "independent_second_site_holdout_benchmark",
            ],
            "why_it_matters": "Portability is currently a metadata/template exercise, not a physical-credibility claim.",
        },
    ]
    return categories


def category_status(gap_report: dict[str, Any], category_name: str) -> str:
    for entry in gap_report.get("evidence_gap_categories", []):
        if entry.get("category") == category_name:
            return str(entry.get("classification") or "unknown")
    return "missing"


def build_candidate_data_sources(categories: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sources: list[dict[str, Any]] = []
    for category in categories:
        category_name = str(category.get("category") or "")
        for source in category.get("current_repo_evidence_sources") or []:
            sources.append(
                evidence_source(
                    category=category_name,
                    kind="current_repo_evidence",
                    label=str(source.get("label") or ""),
                    reference=str(source.get("reference") or ""),
                    status=str(source.get("status") or "unknown"),
                    role=str(source.get("role") or ""),
                    notes=str(source.get("notes") or ""),
                )
            )
        for source in category.get("future_acquisition_classes") or []:
            sources.append(
                evidence_source(
                    category=category_name,
                    kind="future_acquisition_class",
                    label=str(source.get("label") or ""),
                    reference=str(source.get("class_name") or ""),
                    status=str(source.get("status") or "missing"),
                    role=str(source.get("role") or "future evidence"),
                    notes=str(source.get("notes") or ""),
                )
            )
    return sources


def build_evidence_acquisition_matrix(categories: list[dict[str, Any]]) -> list[dict[str, Any]]:
    category_map = {str(entry.get("category") or ""): entry for entry in categories}
    matrix: list[dict[str, Any]] = []
    for blueprint in EVIDENCE_ACQUISITION_PRIORITY_BLUEPRINTS:
        category = str(blueprint["category"])
        category_entry = category_map.get(category, {})
        matrix.append(
            {
                "category": category,
                "priority": blueprint["priority"],
                "priority_label": blueprint["priority_label"],
                "expected_claim_unlocked": blueprint["expected_claim_unlocked"],
                "required_data": list(blueprint["required_data"]),
                "current_repo_gap": blueprint["current_repo_gap"],
                "current_repo_evidence_status": category_entry.get("current_repo_evidence_status", "missing"),
                "current_repo_evidence": summarize_current_repo_evidence(category_entry),
                "future_field_or_reference_data_needs": summarize_future_acquisition_needs(category_entry),
                "why_it_matters": str(category_entry.get("why_it_matters") or ""),
            }
        )
    return matrix


def evidence_acquisition_summary(matrix: list[dict[str, Any]]) -> dict[str, Any]:
    if not matrix:
        return {
            "first_actionable_category": None,
            "deferred_category": None,
            "priority_order": [],
        }
    ordered = sorted(matrix, key=lambda entry: int(entry.get("priority", 999)))
    first = ordered[0]
    deferred = ordered[-1]
    return {
        "first_actionable_category": first.get("category"),
        "deferred_category": deferred.get("category"),
        "priority_order": [entry.get("category") for entry in ordered],
    }


def summarize_current_repo_evidence(category_entry: dict[str, Any]) -> list[str]:
    summary: list[str] = []
    for source in category_entry.get("current_repo_evidence_sources") or []:
        label = str(source.get("label") or "").strip()
        status = str(source.get("status") or "unknown").strip()
        role = str(source.get("role") or "").strip()
        reference = str(source.get("reference") or "").strip()
        pieces = [piece for piece in (label, f"[{status}]" if status else "", role) if piece]
        text = " ".join(pieces)
        if reference:
            text = f"{text} ({reference})"
        summary.append(text)
    return summary


def summarize_future_acquisition_needs(category_entry: dict[str, Any]) -> list[str]:
    summary: list[str] = []
    for source in category_entry.get("future_acquisition_classes") or []:
        label = str(source.get("label") or "").strip()
        status = str(source.get("status") or "missing").strip()
        class_name = str(source.get("class_name") or "").strip()
        pieces = [piece for piece in (label, f"[{status}]" if status else "") if piece]
        text = " ".join(pieces)
        if class_name:
            text = f"{text} ({class_name})"
        summary.append(text)
    return summary


def calibration_split_requirements(holdout_report: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "requirement": "Calibration dataset provenance",
            "status": "missing",
            "current_repo_evidence": "Current model-selection and holdout fixtures are diagnostic only; no calibration dataset is staged.",
            "required_artifact_class": "calibration_dataset_with_objective_function",
        },
        {
            "requirement": "Objective function and parameter bounds",
            "status": "missing",
            "current_repo_evidence": "No parameter-fitting objective or bounds record is present in the current repo evidence.",
            "required_artifact_class": "parameter_bounds_and_fit_record",
        },
        {
            "requirement": "Reserved calibration split separate from diagnostic selection",
            "status": "partial",
            "current_repo_evidence": (
                "Chant Sura metadata records a deterministic diagnostic / held-out split, but the current "
                "evidence is not a calibration split."
            ),
            "required_artifact_class": "reserved_calibration_split",
        },
        {
            "requirement": "Calibration record separated from holdout validation",
            "status": "missing",
            "current_repo_evidence": holdout_report.get("limitations", []),
            "required_artifact_class": "calibration_and_holdout_separation_record",
        },
    ]


def holdout_validation_requirements(holdout_report: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "requirement": "Independent holdout benchmark",
            "status": "present",
            "current_repo_evidence": [
                holdout_report.get("holdout_validation_evidence", {}).get("source_case", ""),
                holdout_report.get("holdout_validation_evidence", {}).get("source_rotational_case", ""),
                holdout_report.get("manifest_path", ""),
            ],
            "required_artifact_class": "independent_holdout_benchmark_dataset",
        },
        {
            "requirement": "Deterministic split metadata and overlap check",
            "status": "present",
            "current_repo_evidence": [
                holdout_report.get("split_metadata", {}).get("split_method", ""),
                holdout_report.get("overlap_check", {}).get("status", ""),
            ],
            "required_artifact_class": "split_metadata_and_overlap_audit",
        },
        {
            "requirement": "Scoring protocol separated from selection",
            "status": "partial",
            "current_repo_evidence": holdout_report.get("holdout_validation_evidence", {}).get("selection_boundary_notes", []),
            "required_artifact_class": "independent_holdout_scoring_protocol",
        },
        {
            "requirement": "No reuse of holdout data for calibration or model selection",
            "status": "present",
            "current_repo_evidence": holdout_report.get("limitations", []),
            "required_artifact_class": "holdout_not_reused_for_selection_record",
        },
    ]


def source_frequency_requirements(datasets: dict[str, dict[str, Any]], gap_report: dict[str, Any]) -> list[dict[str, Any]]:
    tschamut_name = dataset_label(datasets, "tschamut2014")
    chant_name = dataset_label(datasets, "chant_sura_2020")
    return [
        {
            "requirement": "Source occurrence or temporal frequency catalogue",
            "status": "missing",
            "current_repo_evidence": [
                f"{tschamut_name} is a conditional deposition/runout benchmark, not a source-occurrence catalogue.",
                f"{chant_name} is a trajectory/contact benchmark, not a source-occurrence catalogue.",
            ],
            "required_artifact_class": "historical_rockfall_event_catalogue",
        },
        {
            "requirement": "Block-population or block-size frequency semantics",
            "status": "missing",
            "current_repo_evidence": [
                "Current scenarios are conditional and proxy-driven.",
                "Shape and mass proxies do not provide population frequencies.",
            ],
            "required_artifact_class": "block_size_survey_or_photogrammetry_census",
        },
        {
            "requirement": "Temporal window / censoring rules for frequency estimates",
            "status": "missing",
            "current_repo_evidence": [
                "The current repository does not stage a temporal-frequency model.",
            ],
            "required_artifact_class": "temporal_frequency_model_with_censoring_rules",
        },
        {
            "requirement": "Propagation of source frequency into intensity-frequency products",
            "status": "missing",
            "current_repo_evidence": gap_report.get("claim_boundary_matrix", []),
            "required_artifact_class": "intensity_frequency_propagation_record",
        },
    ]


def claim_boundaries() -> dict[str, bool]:
    return {
        "physical_probability_claims_allowed": False,
        "annual_frequency_claims_allowed": False,
        "risk_exposure_vulnerability_claims_allowed": False,
        "operational_claims_allowed": False,
        "scale_up_authorized": False,
        "distributed_execution_authorized": False,
    }


def current_evidence_summary(gap_report: dict[str, Any], holdout_report: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "summary": "Tschamut diagnostic validation remains reproducible but not physically credible.",
            "status": gap_report.get("physical_credibility_status", "unknown"),
        },
        {
            "summary": "Chant Sura provides separated holdout validation evidence, not calibration evidence.",
            "status": holdout_report.get("holdout_evidence_status", "unknown"),
        },
        {
            "summary": "Source-frequency semantics remain unsupported and deferred.",
            "status": "deferred_unsupported",
        },
        {
            "summary": "Multi-site portability remains metadata-only until public-context products are staged.",
            "status": "deferred_public_context_inputs",
        },
    ]


def render_text_report(report: dict[str, Any]) -> str:
    lines = [
        f"schema_version: {report['schema_version']}",
        f"physical_credibility_requirements_status: {report['physical_credibility_requirements_status']}",
        f"current_physical_credibility_status: {report['current_physical_credibility_status']}",
        f"calibration_status: {report['calibration_status']}",
        f"validation_status: {report['validation_status']}",
        f"intensity_frequency_status: {report['intensity_frequency_status']}",
        "",
        "evidence_acquisition_summary:",
        f"- first_actionable_category: {report['evidence_acquisition_summary']['first_actionable_category']}",
        f"- deferred_category: {report['evidence_acquisition_summary']['deferred_category']}",
        f"- priority_order: {', '.join(report['evidence_acquisition_summary']['priority_order'])}",
        "",
        "claim_boundaries:",
    ]
    for key, value in report["claim_boundaries"].items():
        lines.append(f"- {key}: {str(value).lower()}")

    lines.append("")
    lines.append("evidence_requirement_categories:")
    for entry in report["evidence_requirement_categories"]:
        lines.append(f"- {entry['category']}: {entry['current_repo_evidence_status']}")
        lines.append(f"  why_it_matters: {entry['why_it_matters']}")
        if entry.get("current_repo_evidence_sources"):
            lines.append("  current_repo_evidence_sources:")
            for source in entry["current_repo_evidence_sources"]:
                lines.append(f"  - {source['label']} [{source['status']}]")
                lines.append(f"    reference: {source['reference']}")
        if entry.get("future_acquisition_classes"):
            lines.append("  future_acquisition_classes:")
            for source in entry["future_acquisition_classes"]:
                lines.append(f"  - {source['label']} [{source['status']}]")
                lines.append(f"    class_name: {source['class_name']}")

    lines.append("")
    lines.append("evidence_acquisition_matrix:")
    for entry in report["evidence_acquisition_matrix"]:
        lines.append(f"- priority {entry['priority']}: {entry['category']} ({entry['priority_label']})")
        lines.append(f"  expected_claim_unlocked: {entry['expected_claim_unlocked']}")
        lines.append(f"  current_repo_gap: {entry['current_repo_gap']}")
        if entry.get("required_data"):
            lines.append("  required_data:")
            for item in entry["required_data"]:
                lines.append(f"  - {item}")
        if entry.get("current_repo_evidence"):
            lines.append("  current_repo_evidence:")
            for item in entry["current_repo_evidence"]:
                lines.append(f"  - {item}")
        if entry.get("future_field_or_reference_data_needs"):
            lines.append("  future_field_or_reference_data_needs:")
            for item in entry["future_field_or_reference_data_needs"]:
                lines.append(f"  - {item}")

    lines.append("")
    lines.append("candidate_data_sources:")
    for source in report["candidate_data_sources"]:
        lines.append(f"- {source['category']} / {source['source_kind']} / {source['label']} [{source['status']}]")
        lines.append(f"  reference: {source['reference']}")

    lines.append("")
    lines.append("calibration_split_requirements:")
    for item in report["calibration_split_requirements"]:
        lines.append(f"- {item['requirement']} [{item['status']}]")

    lines.append("")
    lines.append("holdout_validation_requirements:")
    for item in report["holdout_validation_requirements"]:
        lines.append(f"- {item['requirement']} [{item['status']}]")

    lines.append("")
    lines.append("source_frequency_requirements:")
    for item in report["source_frequency_requirements"]:
        lines.append(f"- {item['requirement']} [{item['status']}]")

    lines.append("")
    lines.append("current_evidence_summary:")
    for item in report["current_evidence_summary"]:
        lines.append(f"- {item['summary']} [{item['status']}]")

    if report.get("missing_inputs"):
        lines.append("")
        lines.append("missing_inputs:")
        for item in report["missing_inputs"]:
            lines.append(f"- {item}")
    if report.get("blocked_reason"):
        lines.append("")
        lines.append(f"blocked_reason: {report['blocked_reason']}")
    return "\n".join(lines)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
