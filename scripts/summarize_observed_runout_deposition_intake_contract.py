#!/usr/bin/env python3
"""Summarize the future observed runout/deposition benchmark intake contract.

This helper is read-only. It defines the minimum benchmark-intake schema that
would be needed for observed runout/deposition evidence, maps each field to the
physical-credibility requirement it would satisfy, and reports the current
blocked state when no independent benchmark dataset is staged in the repo.
It does not fabricate validation data, fit parameters, or authorize any
calibration, annual-frequency, risk, exposure, vulnerability, or operational
claim.
"""

from __future__ import annotations

import argparse
import json
import sys
from copy import deepcopy
from functools import partial
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except ImportError as exc:  # pragma: no cover - environment setup.
    raise SystemExit("PyYAML is required. Run this script with `PYENV_VERSION=system uv run python ...`; CI may use `requirements-tools.txt`") from exc


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from scripts import map_physical_credibility_evidence_requirements as physical_credibility_requirements
from lib.workflow_validation import (
    build_blocked_report as shared_build_blocked_report,
    missing_repo_paths as shared_missing_repo_paths,
    require as shared_require,
    require_false_fields as shared_require_false_fields,
    require_paths_exist as shared_require_paths_exist,
    scan_text_for_misleading_claims as shared_scan_text_for_misleading_claims,
)

SCHEMA_VERSION = "observed_runout_deposition_intake_contract_v1"
EXPECTED_BENCHMARK_ROOT = ROOT / "validation/data/processed/observed_runout_deposition_benchmark"
EXPECTED_BENCHMARK_MANIFEST = EXPECTED_BENCHMARK_ROOT / "manifest.json"
EXPECTED_BENCHMARK_GEOMETRY = EXPECTED_BENCHMARK_ROOT / "observed_runout_deposition.geojson"
EXPECTED_ACCEPTED_ACQUISITION_FIXTURE = ROOT / "tests/fixtures/observed_runout_deposition_intake_contract/accepted_fixture.yaml"
EXPECTED_CALIBRATION_ROOT = ROOT / "validation/data/processed/observed_runout_deposition_calibration"
EXPECTED_VALIDATION_INPUT_MANIFEST = ROOT / "validation/data/processed/chant_sura_2020/metadata_contact_split.json"
EXPECTED_VALIDATION_INPUT_CASE = ROOT / "validation/cases/chant_sura_contact.yaml"
EXPECTED_HOLDOUT_MANIFEST = ROOT / "validation/data/processed/chant_sura_2020/holdout_validation_evidence_manifest.json"
EXPECTED_HOLDOUT_CASE = ROOT / "validation/cases/chant_sura_contact_heldout.yaml"
EXPECTED_BENCHMARK_INPUTS = (
    EXPECTED_BENCHMARK_MANIFEST,
    EXPECTED_BENCHMARK_GEOMETRY,
)
LOCAL_OBSERVED_DEPOSITION_CANDIDATE_PATHS = (
    ROOT / "data/processed/tschamut2014/observed_deposition.csv",
    ROOT / "validation/data/processed/tschamut/observed_deposition.csv",
)

ACQUISITION_MATRIX_SCHEMA_VERSION = "observed_runout_deposition_acquisition_matrix_v1"
OBSERVED_RUNOUT_DEPOSITION_CANDIDATE_REPORT_SCHEMA_VERSION = "observed_runout_deposition_candidate_acquisition_report_v1"

ACQUISITION_MATRIX_BLUEPRINTS: tuple[dict[str, Any], ...] = (
    {
        "category": "observed_runout_deposition",
        "dataset_role": "observed_runout_deposition_benchmark",
        "label": "Independent observed runout/deposition benchmark",
        "required_fields": {
            "geometry": [
                "geometry_id",
                "geometry_role",
                "geometry_encoding",
                "geometry_crs",
                "geometry_value",
            ],
            "provenance": [
                "event_id",
                "event_date",
                "site_id",
                "source_id",
                "source_name",
                "observer",
                "observation_method",
                "provenance_uri",
                "source_origin_description",
                "source_reference_frame",
                "source_geometry_reference",
            ],
            "uncertainty": [
                "geometry_tolerance_m",
                "position_tolerance_m",
                "timing_tolerance_days",
                "coverage_completeness",
                "qa_status",
                "uncertainty_notes",
            ],
        },
        "acceptable_provenance": [
            "Independent field or benchmark intake staged as a separate observed package.",
            "Observed geometry must be traceable to the event and not reused for calibration selection.",
            "License or usage notes must allow review without silently inheriting calibration permissions.",
        ],
        "uncertainty_fields": [
            "geometry_tolerance_m",
            "position_tolerance_m",
            "timing_tolerance_days",
            "coverage_completeness",
            "qa_status",
            "uncertainty_notes",
        ],
        "licensing_readiness_notes": [
            "Record the access, citation, or usage-rights note with the package.",
            "Do not mark the package ready if geometry or uncertainty metadata are missing.",
        ],
        "calibration_validation_role": {
            "calibration": "not_allowed",
            "validation": "benchmark_intake_only",
            "holdout": "ineligible",
        },
        "holdout_eligibility": False,
        "required_inputs": (
            EXPECTED_BENCHMARK_MANIFEST,
            EXPECTED_BENCHMARK_GEOMETRY,
        ),
        "blocked_reason": "no independent observed runout/deposition benchmark intake is staged in the repo",
        "acceptance_notes": [
            "The observed intake is the physical-credibility anchor for this task.",
            "If a real package later appears, it still cannot be converted into calibration data.",
        ],
    },
    {
        "category": "release_zone_provenance",
        "dataset_role": "release_zone_provenance",
        "label": "Site-specific release-zone provenance",
        "required_fields": {
            "geometry": [
                "geometry_id",
                "geometry_role",
                "geometry_encoding",
                "geometry_crs",
                "geometry_value",
            ],
            "provenance": [
                "source_id",
                "source_origin_description",
                "source_reference_frame",
                "source_geometry_reference",
                "provenance_uri",
            ],
            "uncertainty": [
                "geometry_tolerance_m",
                "position_tolerance_m",
                "qa_status",
                "uncertainty_notes",
            ],
        },
        "acceptable_provenance": [
            "Field reconnaissance or mapped release geometry with a stable provenance record.",
            "Geometry must be distinct from workflow-only candidate release-zone inputs.",
            "Release-zone provenance may support validation context, but not calibration by itself.",
        ],
        "uncertainty_fields": [
            "geometry_tolerance_m",
            "position_tolerance_m",
            "qa_status",
            "uncertainty_notes",
        ],
        "licensing_readiness_notes": [
            "Record the provenance citation or access note before treating the geometry as reviewable evidence.",
        ],
        "calibration_validation_role": {
            "calibration": "not_allowed",
            "validation": "context_only",
            "holdout": "ineligible",
        },
        "holdout_eligibility": False,
        "required_inputs": (
            EXPECTED_BENCHMARK_MANIFEST,
            EXPECTED_BENCHMARK_GEOMETRY,
        ),
        "blocked_reason": "no independent release-zone provenance package is staged in the repo",
        "acceptance_notes": [
            "Release-zone provenance is a separate acquisition path from the benchmark intake.",
        ],
    },
    {
        "category": "block_population_evidence",
        "dataset_role": "block_population_evidence",
        "label": "Block-population or block-size evidence",
        "required_fields": {
            "geometry": [
                "geometry_id",
                "geometry_role",
                "geometry_encoding",
                "geometry_crs",
                "geometry_value",
            ],
            "provenance": [
                "survey_id",
                "observer",
                "observation_method",
                "provenance_uri",
                "source_origin_description",
                "source_reference_frame",
            ],
            "uncertainty": [
                "block_count",
                "size_class_notes",
                "sampling_frame_description",
                "uncertainty_notes",
            ],
        },
        "acceptable_provenance": [
            "Field census, photogrammetry survey, or another defensible block-population record.",
            "Must be traceable to a survey frame rather than a source-frequency catalogue.",
        ],
        "uncertainty_fields": [
            "block_count",
            "size_class_notes",
            "sampling_frame_description",
            "uncertainty_notes",
        ],
        "licensing_readiness_notes": [
            "Include the survey access or citation note so the census can be audited later.",
        ],
        "calibration_validation_role": {
            "calibration": "not_allowed",
            "validation": "future_probability_bridge_only",
            "holdout": "ineligible",
        },
        "holdout_eligibility": False,
        "required_inputs": (ROOT / "docs/target_area_physical_evidence_acquisition_pack.md",),
        "blocked_reason": "no block-population or block-size survey is staged in the repo",
        "acceptance_notes": [
            "Block-population evidence is a future physical-probability bridge, not a calibration target.",
        ],
    },
    {
        "category": "calibration_inputs",
        "dataset_role": "calibration_inputs",
        "label": "Calibration inputs",
        "required_fields": {
            "geometry": [
                "dataset_id",
                "case_id",
                "split_id",
                "objective_function_id",
            ],
            "provenance": [
                "calibration_dataset_ids",
                "objective_function_id",
                "fit_record_provenance_uri",
                "split_rules",
            ],
            "uncertainty": [
                "parameter_bounds",
                "fit_residual_notes",
                "split_uncertainty_notes",
            ],
        },
        "acceptable_provenance": [
            "Calibration dataset must be separate from the validation and holdout evidence used by the task.",
            "Objective function and fit record must be explicit if calibration is later authorized.",
        ],
        "uncertainty_fields": [
            "parameter_bounds",
            "fit_residual_notes",
            "split_uncertainty_notes",
        ],
        "licensing_readiness_notes": [
            "Calibration data may be useful only after a later task explicitly authorizes fitting.",
        ],
        "calibration_validation_role": {
            "calibration": "primary",
            "validation": "separated_from_holdout",
            "holdout": "ineligible",
        },
        "holdout_eligibility": False,
        "required_inputs": (EXPECTED_CALIBRATION_ROOT,),
        "blocked_reason": "no calibration dataset is staged in the repo",
        "acceptance_notes": [
            "Calibration inputs must never be inferred from the observed benchmark intake.",
        ],
    },
    {
        "category": "validation_inputs",
        "dataset_role": "validation_inputs",
        "label": "Validation inputs",
        "required_fields": {
            "geometry": [
                "case_id",
                "split_id",
                "validation_case_path",
                "validation_manifest_path",
            ],
            "provenance": [
                "validation_dataset_ids",
                "split_rules",
                "selection_boundary_notes",
                "provenance_uri",
            ],
            "uncertainty": [
                "validation_scoring_notes",
                "selection_boundary_notes",
            ],
        },
        "acceptable_provenance": [
            "Validation fixtures must be disjoint from calibration fixtures and selection data.",
            "The record is acceptable when the split provenance is explicit and deterministic.",
        ],
        "uncertainty_fields": [
            "validation_scoring_notes",
            "selection_boundary_notes",
        ],
        "licensing_readiness_notes": [
            "Validation data are acceptable only when the split and provenance are documented.",
        ],
        "calibration_validation_role": {
            "calibration": "not_allowed",
            "validation": "primary",
            "holdout": "ineligible",
        },
        "holdout_eligibility": False,
        "required_inputs": (
            EXPECTED_VALIDATION_INPUT_MANIFEST,
            EXPECTED_VALIDATION_INPUT_CASE,
        ),
        "blocked_reason": None,
        "acceptance_notes": [
            "Validation inputs remain separate from calibration inputs and holdout data.",
        ],
    },
    {
        "category": "holdout_data",
        "dataset_role": "holdout_data",
        "label": "Holdout data",
        "required_fields": {
            "geometry": [
                "case_id",
                "split_id",
                "holdout_case_path",
                "holdout_manifest_path",
            ],
            "provenance": [
                "holdout_dataset_ids",
                "split_rules",
                "selection_boundary_notes",
                "provenance_uri",
            ],
            "uncertainty": [
                "holdout_scoring_notes",
                "selection_boundary_notes",
            ],
        },
        "acceptable_provenance": [
            "Holdout data must be disjoint from selection and calibration data.",
            "The package is acceptable only when reuse-for-fitting is explicitly forbidden.",
        ],
        "uncertainty_fields": [
            "holdout_scoring_notes",
            "selection_boundary_notes",
        ],
        "licensing_readiness_notes": [
            "Holdout data are only ready when the split fence is explicit and stable.",
        ],
        "calibration_validation_role": {
            "calibration": "not_allowed",
            "validation": "holdout_only",
            "holdout": "primary",
        },
        "holdout_eligibility": True,
        "required_inputs": (
            EXPECTED_HOLDOUT_MANIFEST,
            EXPECTED_HOLDOUT_CASE,
        ),
        "blocked_reason": None,
        "acceptance_notes": [
            "Holdout data are validation-side evidence only and must remain separated from calibration.",
        ],
    },
)


class ObservedRunoutDepositionIntakeContractError(ValueError):
    """User-facing observed runout/deposition intake contract error."""


require = partial(shared_require, error_cls=ObservedRunoutDepositionIntakeContractError)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    parser.add_argument("--output-root", type=Path, default=None)
    args = parser.parse_args(argv)

    report = build_report(output_root=args.output_root)
    if args.json_output is not None:
        output_path = args.json_output if args.json_output.is_absolute() else ROOT / args.json_output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    output = json.dumps(report, indent=2, sort_keys=True) if args.format == "json" else render_text_report(report)
    print(output)
    readiness_pack = report.get("readiness_pack", {})
    if readiness_pack.get("readiness_pack_status") == "written":
        return 0
    return 2 if report["observed_runout_deposition_intake_status"] == "blocked_missing_inputs" else 0


def build_report(output_root: Path | None = None) -> dict[str, Any]:
    contract = build_contract()
    field_requirement_map = build_field_requirement_map()
    current_state = build_current_state()
    acquisition_blocker_matrix = build_acquisition_blocker_matrix(current_state=current_state)
    next_action_recommendation = build_next_action_recommendation(acquisition_blocker_matrix)
    physical_credibility_gap_update = build_physical_credibility_gap_update()
    dataset_role_classification = build_dataset_role_classification(current_state=current_state)
    fixture_acceptance_smoke = build_fixture_acceptance_smoke()
    candidate_acquisition_report = build_candidate_acquisition_report(current_state=current_state)
    benchmark_missing_inputs = current_state["benchmark_intake_missing_inputs"]
    benchmark_intake_manifest = build_benchmark_intake_manifest(
        contract=contract,
        current_state=current_state,
        acquisition_blocker_matrix=acquisition_blocker_matrix,
        next_action_recommendation=next_action_recommendation,
        physical_credibility_gap_update=physical_credibility_gap_update,
        dataset_role_classification=dataset_role_classification,
        pack_root=None,
    )

    if benchmark_missing_inputs:
        report: dict[str, Any] = shared_build_blocked_report(
            schema_version=SCHEMA_VERSION,
            status_key="observed_runout_deposition_intake_status",
            missing_inputs=benchmark_missing_inputs,
            blocked_reason="no independent observed runout/deposition benchmark intake is staged in the repo",
            extra_fields={
                "benchmark_intake_contract": contract,
                "benchmark_intake_manifest": benchmark_intake_manifest,
                "field_requirement_map": field_requirement_map,
                "current_repo_state": current_state,
                "acquisition_blocker_matrix": acquisition_blocker_matrix,
                "next_action_recommendation": next_action_recommendation,
                "physical_credibility_gap_update": physical_credibility_gap_update,
                "candidate_acquisition_report": candidate_acquisition_report,
                "dataset_role_classification": dataset_role_classification,
                "fixture_acceptance_smoke": fixture_acceptance_smoke,
                "claim_boundaries": claim_boundaries(),
                "current_state_summary": current_state_summary(current_state),
            },
        )
    else:
        report = {
            "schema_version": SCHEMA_VERSION,
            "observed_runout_deposition_intake_status": "ready",
            "benchmark_intake_contract": contract,
            "benchmark_intake_manifest": benchmark_intake_manifest,
            "field_requirement_map": field_requirement_map,
            "current_repo_state": current_state,
            "acquisition_blocker_matrix": acquisition_blocker_matrix,
            "next_action_recommendation": next_action_recommendation,
            "physical_credibility_gap_update": physical_credibility_gap_update,
            "candidate_acquisition_report": candidate_acquisition_report,
            "dataset_role_classification": dataset_role_classification,
            "fixture_acceptance_smoke": fixture_acceptance_smoke,
            "claim_boundaries": claim_boundaries(),
            "blocked_reason": None,
            "missing_inputs": [],
            "current_state_summary": current_state_summary(current_state),
        }
    validate_claim_boundaries(report["claim_boundaries"])
    shared_scan_text_for_misleading_claims(report, require_fn=require)
    if output_root is not None:
        readiness_pack = build_readiness_pack(output_root=output_root, report=report)
        report["readiness_pack"] = readiness_pack
    return report


def build_readiness_pack(*, output_root: Path, report: dict[str, Any]) -> dict[str, Any]:
    pack_root = resolve_output_root(output_root)
    pack_root.mkdir(parents=True, exist_ok=True)

    acquisition_checklist = build_acquisition_checklist(report=report, pack_root=pack_root)
    dataset_inventory = build_required_dataset_inventory(report=report, pack_root=pack_root)
    geometry_template = build_geometry_template(report=report, pack_root=pack_root)
    provenance_template = build_provenance_template(report=report, pack_root=pack_root)
    objective_placeholders = build_objective_function_placeholders(report=report, pack_root=pack_root)
    blocked_no_evidence_report = build_blocked_no_evidence_report(report=report, pack_root=pack_root)
    template_manifest = build_template_manifest(report=report, pack_root=pack_root)
    benchmark_intake_manifest = build_benchmark_intake_manifest(
        contract=report["benchmark_intake_contract"],
        current_state=report["current_repo_state"],
        acquisition_blocker_matrix=report["acquisition_blocker_matrix"],
        next_action_recommendation=report["next_action_recommendation"],
        physical_credibility_gap_update=report["physical_credibility_gap_update"],
        dataset_role_classification=report["dataset_role_classification"],
        pack_root=pack_root,
    )

    acquisition_checklist_path = pack_root / "acquisition_checklist.md"
    dataset_inventory_path = pack_root / "required_dataset_inventory.yaml"
    geometry_template_path = pack_root / "geometry_template.yaml"
    provenance_template_path = pack_root / "provenance_template.yaml"
    objective_placeholders_path = pack_root / "objective_function_placeholders.yaml"
    blocked_no_evidence_report_path = pack_root / "blocked_no_evidence_report.md"
    template_manifest_path = pack_root / "template_manifest.yaml"
    benchmark_intake_manifest_path = pack_root / "benchmark_intake_manifest.yaml"
    validation_summary_path = pack_root / "validation_summary.json"

    acquisition_checklist_path.write_text(acquisition_checklist, encoding="utf-8")
    dataset_inventory_path.write_text(yaml.safe_dump(dataset_inventory, sort_keys=False), encoding="utf-8")
    geometry_template_path.write_text(yaml.safe_dump(geometry_template, sort_keys=False), encoding="utf-8")
    provenance_template_path.write_text(yaml.safe_dump(provenance_template, sort_keys=False), encoding="utf-8")
    objective_placeholders_path.write_text(yaml.safe_dump(objective_placeholders, sort_keys=False), encoding="utf-8")
    blocked_no_evidence_report_path.write_text(blocked_no_evidence_report, encoding="utf-8")
    template_manifest_path.write_text(yaml.safe_dump(template_manifest, sort_keys=False), encoding="utf-8")
    benchmark_intake_manifest_path.write_text(yaml.safe_dump(benchmark_intake_manifest, sort_keys=False), encoding="utf-8")

    validation_summary = validate_readiness_pack(
        pack_root=pack_root,
        acquisition_checklist_path=acquisition_checklist_path,
        dataset_inventory_path=dataset_inventory_path,
        geometry_template_path=geometry_template_path,
        provenance_template_path=provenance_template_path,
        objective_placeholders_path=objective_placeholders_path,
        blocked_no_evidence_report_path=blocked_no_evidence_report_path,
        template_manifest_path=template_manifest_path,
        benchmark_intake_manifest_path=benchmark_intake_manifest_path,
    )
    validation_summary_path.write_text(json.dumps(validation_summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return {
        "readiness_pack_status": "written",
        "artifact_classification": "template_non_evidence",
        "readiness_pack_root": str(pack_root),
        "generated_files": {
            "acquisition_checklist": str(acquisition_checklist_path),
            "required_dataset_inventory": str(dataset_inventory_path),
            "geometry_template": str(geometry_template_path),
            "provenance_template": str(provenance_template_path),
            "objective_function_placeholders": str(objective_placeholders_path),
            "blocked_no_evidence_report": str(blocked_no_evidence_report_path),
            "template_manifest": str(template_manifest_path),
            "benchmark_intake_manifest": str(benchmark_intake_manifest_path),
            "validation_summary": str(validation_summary_path),
        },
        "validation_summary": validation_summary,
    }


def build_template_manifest(*, report: dict[str, Any], pack_root: Path) -> dict[str, Any]:
    contract = report["benchmark_intake_contract"]
    current_state = report["current_repo_state"]
    return {
        "schema_version": SCHEMA_VERSION,
        "artifact_classification": "template_non_evidence",
        "pack_status": "dry_run_template",
        "pack_root": str(pack_root),
        "source_script": "scripts/summarize_observed_runout_deposition_intake_contract.py",
        "observed_runout_deposition_intake_status": report["observed_runout_deposition_intake_status"],
        "blocked_reason": report["blocked_reason"],
        "benchmark_intake_contract": {
            "geometry": contract["geometry"],
            "event_source_metadata": contract["event_source_metadata"],
            "uncertainty": contract["uncertainty"],
            "objective_function_placeholders": contract["objective_function_placeholders"],
        },
        "required_inputs": [
            {
                "path": str(EXPECTED_BENCHMARK_MANIFEST),
                "exists": EXPECTED_BENCHMARK_MANIFEST.exists(),
            },
            {
                "path": str(EXPECTED_BENCHMARK_GEOMETRY),
                "exists": EXPECTED_BENCHMARK_GEOMETRY.exists(),
            },
        ],
        "validation_boundary": current_state["evidence_boundary"],
        "claim_boundaries": report["claim_boundaries"],
        "notes": [
            "Template/non-evidence artifact only.",
            "No real benchmark data, calibration fit, or operational claim is encoded here.",
        ],
    }


def build_benchmark_intake_manifest(
    *,
    contract: dict[str, Any],
    current_state: dict[str, Any],
    acquisition_blocker_matrix: list[dict[str, Any]],
    next_action_recommendation: dict[str, Any],
    physical_credibility_gap_update: dict[str, Any],
    dataset_role_classification: list[dict[str, Any]],
    pack_root: Path | None,
) -> dict[str, Any]:
    geometry = contract["geometry"]
    event_source_metadata = contract["event_source_metadata"]
    uncertainty = contract["uncertainty"]
    objective_function_placeholders = contract["objective_function_placeholders"]
    return {
        "schema_version": SCHEMA_VERSION,
        "artifact_classification": "template_non_evidence",
        "manifest_status": "dry_run_template" if pack_root is not None else "report_only",
        "pack_root": str(pack_root) if pack_root is not None else None,
        "blocked_reason": (
            "no independent observed runout/deposition benchmark intake is staged in the repo"
            if current_state["benchmark_intake_readiness_status"] != "ready"
            else None
        ),
        "observed_geometry": {
            "required_crs": geometry["required_crs"],
            "required_vertical_datum": geometry["required_vertical_datum"],
            "allowed_geometry_roles": list(geometry["allowed_geometry_roles"]),
            "required_fields": list(geometry["required_fields"]),
            "geometry_roles": [
                {
                    "geometry_role": role,
                    "required": True,
                    "description": geometry_role_description(role),
                }
                for role in geometry["allowed_geometry_roles"]
            ],
        },
        "provenance": {
            "required_fields": list(event_source_metadata["required_fields"]),
            "source_metadata_required": list(event_source_metadata["source_metadata_required"]),
            "current_repo_state": {
                "benchmark_intake_readiness_status": current_state["benchmark_intake_readiness_status"],
                "calibration_readiness_status": current_state["calibration_readiness_status"],
            },
        },
        "uncertainty": {
            "required_fields": list(uncertainty["required_fields"]),
            "measurement_units": dict(uncertainty["measurement_units"]),
        },
        "objective_function_readiness": {
            "required_fields": list(objective_function_placeholders["required_fields"]),
            "objective_status": objective_function_placeholders["objective_status"],
            "fit_record_required": objective_function_placeholders["fit_record_required"],
            "notes": list(objective_function_placeholders["notes"]),
        },
        "calibration_validation_separation": {
            "benchmark_intake_missing_inputs": list(current_state["benchmark_intake_missing_inputs"]),
            "calibration_missing_inputs": list(current_state["calibration_missing_inputs"]),
            "calibration_readiness_status": current_state["calibration_readiness_status"],
            "validation_inputs_status": dataset_role_status(dataset_role_classification, "validation_inputs"),
            "holdout_data_status": dataset_role_status(dataset_role_classification, "holdout_data"),
            "calibration_validation_overlap_allowed": False,
            "no_reuse_for_fit": True,
        },
        "acquisition_blocker_matrix": acquisition_blocker_matrix,
        "next_action_recommendation": next_action_recommendation,
        "dataset_role_classification": dataset_role_classification,
        "physical_credibility_gap_update": physical_credibility_gap_update,
        "claim_boundaries": claim_boundaries(),
        "notes": [
            "Template/non-evidence manifest for a future observed runout/deposition intake.",
            "No real benchmark data, calibration fit, or operational claim is encoded here.",
        ],
    }


def build_physical_credibility_gap_update() -> dict[str, Any]:
    report = physical_credibility_requirements.build_report()
    return {
        "schema_version": physical_credibility_requirements.SCHEMA_VERSION,
        "physical_credibility_requirements_status": report["physical_credibility_requirements_status"],
        "current_physical_credibility_status": report["current_physical_credibility_status"],
        "calibration_status": report["calibration_status"],
        "validation_status": report["validation_status"],
        "blocked_reason": report["blocked_reason"],
        "missing_inputs": list(report["missing_inputs"]),
        "claim_boundaries": dict(report["claim_boundaries"]),
        "evidence_acquisition_summary": dict(report["evidence_acquisition_summary"]),
    }


def build_fixture_acceptance_smoke() -> dict[str, Any]:
    fixture = load_yaml_fixture(EXPECTED_ACCEPTED_ACQUISITION_FIXTURE)
    blueprint = acquisition_blueprint("observed_runout_deposition")
    contract = build_contract()
    classification = classify_acquisition_fixture_row("observed_runout_deposition", fixture)
    return {
        "schema_version": ACQUISITION_MATRIX_SCHEMA_VERSION,
        "fixture_path": str(EXPECTED_ACCEPTED_ACQUISITION_FIXTURE),
        "fixture_status": "fixture_backed",
        "accepted_schema_shape": {
            "geometry": {
                "required_crs": contract["geometry"]["required_crs"],
                "required_vertical_datum": contract["geometry"]["required_vertical_datum"],
                "allowed_geometry_roles": list(contract["geometry"]["allowed_geometry_roles"]),
                "required_fields": list(contract["geometry"]["required_fields"]),
            },
            "provenance": {
                "required_fields": list(contract["event_source_metadata"]["required_fields"]),
                "source_metadata_required": list(contract["event_source_metadata"]["source_metadata_required"]),
            },
            "uncertainty": {
                "required_fields": list(contract["uncertainty"]["required_fields"]),
                "measurement_units": dict(contract["uncertainty"]["measurement_units"]),
            },
            "calibration_validation_role": dict(blueprint["calibration_validation_role"]),
            "holdout_eligibility": blueprint["holdout_eligibility"],
        },
        "fixture_classification": classification,
        "physical_evidence_status": "not_established",
        "physical_evidence_note": "Fixture-backed schema smoke only; real physical evidence is not established by this report.",
    }


def build_candidate_acquisition_report(*, current_state: dict[str, Any]) -> dict[str, Any]:
    contract = build_contract()
    candidate_sources = list(current_state.get("adjacent_diagnostic_materials", []))
    available_local_candidates = [
        summarize_local_candidate_source(source, contract=contract)
        for source in candidate_sources
        if str(source.get("status") or "") == "present"
    ]
    selected_candidate = available_local_candidates[0] if available_local_candidates else None

    if selected_candidate is None:
        recommendation = "blocked_no_candidate"
        blocked_reason = "no local observed runout/deposition candidate source is staged"
    elif selected_candidate["license_provenance_blockers"]:
        recommendation = "blocked_license_or_provenance"
        blocked_reason = "the available local candidate remains diagnostic-only and lacks a standalone benchmark package"
    elif EXPECTED_BENCHMARK_MANIFEST.exists() and EXPECTED_BENCHMARK_GEOMETRY.exists():
        recommendation = "stage_candidate"
        blocked_reason = None
    else:
        recommendation = "defer_scientific_claim"
        blocked_reason = "the candidate shape is present, but the staged package still does not justify a stronger scientific claim"

    first_missing_geometry_fields = list(selected_candidate["first_missing_geometry_fields"]) if selected_candidate else list(contract["geometry"]["required_fields"])
    first_missing_provenance_fields = list(selected_candidate["first_missing_provenance_fields"]) if selected_candidate else list(contract["event_source_metadata"]["required_fields"]) + list(contract["event_source_metadata"]["source_metadata_required"])
    first_missing_uncertainty_fields = list(selected_candidate["first_missing_uncertainty_fields"]) if selected_candidate else list(contract["uncertainty"]["required_fields"])

    return {
        "schema_version": OBSERVED_RUNOUT_DEPOSITION_CANDIDATE_REPORT_SCHEMA_VERSION,
        "candidate_acquisition_status": recommendation,
        "recommendation": recommendation,
        "selected_candidate_path": selected_candidate["candidate_path"] if selected_candidate else None,
        "selected_candidate_kind": selected_candidate["candidate_kind"] if selected_candidate else None,
        "available_local_candidates": available_local_candidates,
        "candidate_sources": candidate_sources,
        "required_external_acquisition_actions": candidate_required_external_actions(),
        "licensing_provenance_blockers": candidate_licensing_provenance_blockers(selected_candidate),
        "first_missing_geometry_fields": first_missing_geometry_fields,
        "first_missing_geometry_field": first_missing_geometry_fields[0] if first_missing_geometry_fields else None,
        "first_missing_provenance_fields": first_missing_provenance_fields,
        "first_missing_provenance_field": first_missing_provenance_fields[0] if first_missing_provenance_fields else None,
        "first_missing_uncertainty_fields": first_missing_uncertainty_fields,
        "first_missing_uncertainty_field": first_missing_uncertainty_fields[0] if first_missing_uncertainty_fields else None,
        "blocked_reason": blocked_reason,
    }


def summarize_local_candidate_source(source: dict[str, Any], *, contract: dict[str, Any]) -> dict[str, Any]:
    path = Path(str(source.get("path") or ""))
    metadata_path = Path(str(source.get("supporting_metadata_path") or path.with_name("metadata.json")))
    candidate_present = path.exists()
    metadata = load_json(metadata_path) if metadata_path.exists() else {}
    provenance_note = str(source.get("provenance_note") or metadata.get("coordinate_system") or "").strip()
    source_note = str(source.get("source_note") or metadata.get("terrain_proxy", {}).get("note") or "").strip()
    required_geometry_fields = list(contract["geometry"]["required_fields"])
    required_provenance_fields = list(contract["event_source_metadata"]["required_fields"]) + list(contract["event_source_metadata"]["source_metadata_required"])
    required_uncertainty_fields = list(contract["uncertainty"]["required_fields"])
    blockers = candidate_source_blockers(
        candidate_present=candidate_present,
        metadata_present=metadata_path.exists(),
        candidate_kind=str(source.get("candidate_kind") or "diagnostic_observed_deposition_csv"),
    )

    return {
        "candidate_id": str(source.get("candidate_id") or path.stem),
        "candidate_path": str(path),
        "candidate_kind": str(source.get("candidate_kind") or "diagnostic_observed_deposition_csv"),
        "candidate_status": "present" if candidate_present else "missing",
        "supporting_metadata_path": str(metadata_path),
        "supporting_metadata_status": "present" if metadata_path.exists() else "missing",
        "supporting_license": str(metadata.get("license") or source.get("supporting_license") or ""),
        "provenance_note": provenance_note,
        "source_note": source_note,
        "required_external_acquisition_actions": candidate_required_external_actions(),
        "license_provenance_blockers": blockers,
        "first_missing_geometry_fields": required_geometry_fields,
        "first_missing_provenance_fields": required_provenance_fields,
        "first_missing_uncertainty_fields": required_uncertainty_fields,
        "first_missing_geometry_field": required_geometry_fields[0] if required_geometry_fields else None,
        "first_missing_provenance_field": required_provenance_fields[0] if required_provenance_fields else None,
        "first_missing_uncertainty_field": required_uncertainty_fields[0] if required_uncertainty_fields else None,
        "candidate_record_role": "diagnostic_only" if candidate_present else "missing",
        "benchmark_package_status": "not_staged" if not candidate_present else "diagnostic_only",
    }


def candidate_required_external_actions() -> list[str]:
    return [
        f"Stage the observed benchmark manifest at {EXPECTED_BENCHMARK_MANIFEST}.",
        f"Stage the observed benchmark geometry at {EXPECTED_BENCHMARK_GEOMETRY}.",
        "Record geometry_id, geometry_role, geometry_encoding, geometry_crs, and geometry_value for the observed evidence package.",
        "Record event_id, event_date, site_id, source_id, source_name, observer, observation_method, provenance_uri, source_origin_description, source_reference_frame, and source_geometry_reference.",
        "Record geometry_tolerance_m, position_tolerance_m, timing_tolerance_days, coverage_completeness, qa_status, and uncertainty_notes.",
        "Add a no-reuse separation note so the observed package is not repurposed for calibration or tuning.",
    ]


def candidate_source_blockers(*, candidate_present: bool, metadata_present: bool, candidate_kind: str) -> list[str]:
    blockers: list[str] = []
    if not candidate_present:
        blockers.append("no_local_candidate_file_present")
        return blockers
    if candidate_kind == "diagnostic_observed_deposition_csv":
        blockers.append("diagnostic_only_candidate_not_independent_benchmark_intake")
    if not metadata_present:
        blockers.append("supporting_metadata_missing")
    if not EXPECTED_BENCHMARK_MANIFEST.exists():
        blockers.append("missing_staged_benchmark_manifest")
    if not EXPECTED_BENCHMARK_GEOMETRY.exists():
        blockers.append("missing_staged_benchmark_geometry")
    return blockers


def candidate_licensing_provenance_blockers(selected_candidate: dict[str, Any] | None) -> list[str]:
    if selected_candidate is None:
        return ["no_local_candidate_file_present"]
    blockers = list(selected_candidate.get("license_provenance_blockers") or [])
    if selected_candidate.get("candidate_record_role") == "diagnostic_only":
        blockers.append("candidate_record_is_diagnostic_only")
    return blockers


def build_dataset_role_classification(current_state: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for blueprint in ACQUISITION_MATRIX_BLUEPRINTS:
        dataset_role = str(blueprint["dataset_role"])
        if dataset_role in {"observed_runout_deposition_benchmark", "release_zone_provenance"}:
            status = "present" if current_state["benchmark_intake_readiness_status"] == "ready" else "missing"
        elif dataset_role == "block_population_evidence":
            status = "missing"
        elif dataset_role == "calibration_inputs":
            status = "present" if current_state["calibration_readiness_status"] == "ready" else "missing"
        elif dataset_role == "validation_inputs":
            status = "present" if validation_inputs_available() else "missing"
        elif dataset_role == "holdout_data":
            status = "present" if holdout_data_available() else "missing"
        else:  # pragma: no cover - blueprints are exhaustive.
            status = "missing"
        rows.append(
            {
                "schema_version": ACQUISITION_MATRIX_SCHEMA_VERSION,
                "category": blueprint["category"],
                "dataset_role": dataset_role,
                "label": blueprint["label"],
                "status": status,
                "repository_status": status,
                "acceptance_status": "ready" if status == "present" else "blocked_missing_inputs",
                "required_inputs": [str(path) for path in blueprint["required_inputs"]],
                "required_fields": deepcopy(blueprint["required_fields"]),
                "acceptable_provenance": list(blueprint["acceptable_provenance"]),
                "uncertainty_fields": list(blueprint["uncertainty_fields"]),
                "licensing_readiness_notes": list(blueprint["licensing_readiness_notes"]),
                "calibration_validation_role": dict(blueprint["calibration_validation_role"]),
                "holdout_eligibility": blueprint["holdout_eligibility"],
                "claim_boundary": claim_boundary_for_dataset_role(dataset_role),
                "blocking_reasons": missing_blocking_reasons(
                    repository_status=status,
                    missing_inputs=[str(path) for path in blueprint["required_inputs"] if not Path(path).exists()],
                    required_fields=blueprint["required_fields"],
                )
                if status != "present"
                else [],
                "acceptance_notes": list(blueprint["acceptance_notes"]),
            }
        )
    return rows


def claim_boundary_for_dataset_role(dataset_role: str) -> str:
    claim_boundaries = {
        "observed_runout_deposition_benchmark": "benchmark intake only; no calibration or operational claim",
        "release_zone_provenance": "release-zone provenance only; no validation or calibration claim",
        "block_population_evidence": "future physical-probability bridge only",
        "calibration_inputs": "calibration only; separated from benchmark intake and holdout data",
        "validation_inputs": "validation-only inputs; separated from calibration inputs",
        "holdout_data": "holdout-only data; no reuse for tuning",
    }
    return claim_boundaries.get(dataset_role, "non-operational acquisition-only boundary")


def dataset_role_status(dataset_roles: list[dict[str, Any]], dataset_role: str) -> str:
    for entry in dataset_roles:
        if entry.get("dataset_role") == dataset_role:
            return str(entry.get("status") or "missing")
    return "missing"


def validation_inputs_available() -> bool:
    return EXPECTED_VALIDATION_INPUT_MANIFEST.exists() and EXPECTED_VALIDATION_INPUT_CASE.exists()


def holdout_data_available() -> bool:
    return EXPECTED_HOLDOUT_MANIFEST.exists() and EXPECTED_HOLDOUT_CASE.exists()


def build_required_dataset_inventory(*, report: dict[str, Any], pack_root: Path) -> dict[str, Any]:
    current_state = report["current_repo_state"]
    return {
        "schema_version": SCHEMA_VERSION,
        "artifact_classification": "template_non_evidence",
        "inventory_status": "dry_run_template",
        "pack_root": str(pack_root),
        "dataset_roles": [
            {
                "dataset_role": "independent_observed_runout_deposition_benchmark",
                "status": "missing" if current_state["benchmark_intake_readiness_status"] != "ready" else "present",
                "required_inputs": [
                    str(EXPECTED_BENCHMARK_MANIFEST),
                    str(EXPECTED_BENCHMARK_GEOMETRY),
                ],
                "notes": [
                    "Benchmark intake only.",
                    "Separate from calibration data and fit targets.",
                ],
            },
            {
                "dataset_role": "release_zone_provenance",
                "status": "missing" if current_state["benchmark_intake_readiness_status"] != "ready" else "present",
                "required_inputs": [str(EXPECTED_BENCHMARK_MANIFEST), str(EXPECTED_BENCHMARK_GEOMETRY)],
                "notes": [
                    "Release-zone provenance must be independent from the benchmark intake and current workflow heuristics.",
                ],
            },
            {
                "dataset_role": "block_population_evidence",
                "status": "missing",
                "required_inputs": [str(ROOT / "docs/target_area_physical_evidence_acquisition_pack.md")],
                "notes": [
                    "No block-population or block-size evidence is staged in the repo.",
                ],
            },
            {
                "dataset_role": "calibration_inputs",
                "status": "missing" if current_state["calibration_readiness_status"] != "ready" else "present",
                "required_inputs": [str(EXPECTED_CALIBRATION_ROOT)],
                "notes": [
                    "Kept separate so calibration readiness does not contaminate benchmark intake readiness.",
                ],
            },
            {
                "dataset_role": "validation_inputs",
                "status": "present" if validation_inputs_available() else "missing",
                "required_inputs": [
                    str(EXPECTED_VALIDATION_INPUT_MANIFEST),
                    str(EXPECTED_VALIDATION_INPUT_CASE),
                ],
                "notes": [
                    "Validation inputs remain separate from calibration inputs.",
                ],
            },
            {
                "dataset_role": "holdout_data",
                "status": "present" if holdout_data_available() else "missing",
                "required_inputs": [
                    str(EXPECTED_HOLDOUT_MANIFEST),
                    str(EXPECTED_HOLDOUT_CASE),
                ],
                "notes": [
                    "Holdout data remain separated from calibration and model-selection fixtures.",
                ],
            },
        ],
        "notes": [
            "Template/non-evidence artifact only.",
            "No real benchmark data is staged here.",
        ],
    }


def build_geometry_template(*, report: dict[str, Any], pack_root: Path) -> dict[str, Any]:
    contract = report["benchmark_intake_contract"]
    return {
        "schema_version": SCHEMA_VERSION,
        "artifact_classification": "template_non_evidence",
        "template_status": "dry_run_template",
        "pack_root": str(pack_root),
        "required_crs": contract["geometry"]["required_crs"],
        "required_vertical_datum": contract["geometry"]["required_vertical_datum"],
        "allowed_geometry_roles": contract["geometry"]["allowed_geometry_roles"],
        "required_fields": contract["geometry"]["required_fields"],
        "geometry_roles": [
            {
                "geometry_role": role,
                "required": True,
                "description": geometry_role_description(role),
            }
            for role in contract["geometry"]["allowed_geometry_roles"]
        ],
        "notes": [
            "This inventory is a template for future geometry intake.",
            "It does not contain observed benchmark geometries.",
        ],
    }


def build_provenance_template(*, report: dict[str, Any], pack_root: Path) -> dict[str, Any]:
    contract = report["benchmark_intake_contract"]
    return {
        "schema_version": SCHEMA_VERSION,
        "artifact_classification": "template_non_evidence",
        "template_status": "dry_run_template",
        "pack_root": str(pack_root),
        "required_provenance_fields": contract["event_source_metadata"]["required_fields"],
        "required_source_metadata_fields": contract["event_source_metadata"]["source_metadata_required"],
        "required_uncertainty_fields": contract["uncertainty"]["required_fields"],
        "notes": [
            "Template for future provenance intake only.",
            "It does not contain observed benchmark provenance.",
        ],
    }


def build_objective_function_placeholders(*, report: dict[str, Any], pack_root: Path) -> dict[str, Any]:
    contract = report["benchmark_intake_contract"]
    return {
        "schema_version": SCHEMA_VERSION,
        "artifact_classification": "template_non_evidence",
        "template_status": "dry_run_template",
        "pack_root": str(pack_root),
        "required_fields": contract["objective_function_placeholders"]["required_fields"],
        "objective_status": contract["objective_function_placeholders"]["objective_status"],
        "fit_record_required": contract["objective_function_placeholders"]["fit_record_required"],
        "notes": contract["objective_function_placeholders"]["notes"],
    }


def build_acquisition_checklist(*, report: dict[str, Any], pack_root: Path) -> str:
    contract = report["benchmark_intake_contract"]
    current_state = report["current_repo_state"]
    next_action = report["next_action_recommendation"]
    lines = [
        "# Observed runout/deposition acquisition checklist",
        "",
        "Template / non-evidence artifact.",
        "This checklist identifies the independent benchmark artifacts that must exist before the intake can be treated as real evidence.",
        "",
        "First acquisition action:",
        f"- {next_action['first_acquisition_action']}",
        "",
        "Required acquisition items:",
        f"- Benchmark manifest: {EXPECTED_BENCHMARK_MANIFEST}",
        f"- Benchmark geometry: {EXPECTED_BENCHMARK_GEOMETRY}",
        f"- Required CRS: {contract['geometry']['required_crs']}",
        f"- Required vertical datum: {contract['geometry']['required_vertical_datum']}",
        f"- Allowed geometry roles: {', '.join(contract['geometry']['allowed_geometry_roles'])}",
        f"- Required geometry fields: {', '.join(contract['geometry']['required_fields'])}",
        f"- Required provenance fields: {', '.join(contract['event_source_metadata']['required_fields'])}",
        f"- Required source metadata fields: {', '.join(contract['event_source_metadata']['source_metadata_required'])}",
        f"- Required uncertainty fields: {', '.join(contract['uncertainty']['required_fields'])}",
        f"- Required objective placeholder fields: {', '.join(contract['objective_function_placeholders']['required_fields'])}",
        "",
        "Current boundary:",
        f"- {current_state['evidence_boundary']}",
        "",
        "Acquisition steps:",
        "- Stage an independent observed runout/deposition benchmark manifest.",
        "- Stage the matching observed geometry record(s) with provenance URIs intact.",
        "- Keep the benchmark intake separate from calibration data and fit targets.",
        "- Verify the CRS, vertical datum, geometry roles, and uncertainty metadata before any analysis.",
        "",
        "Artifact root:",
        f"- {pack_root}",
    ]
    return "\n".join(lines) + "\n"


def build_blocked_no_evidence_report(*, report: dict[str, Any], pack_root: Path) -> str:
    current_state = report["current_repo_state"]
    physical_gap = report["physical_credibility_gap_update"]
    candidate_report = report["candidate_acquisition_report"]
    acquisition_blocker_matrix = report["acquisition_blocker_matrix"]
    next_action_recommendation = report["next_action_recommendation"]
    lines = [
        "# Blocked no-evidence report",
        "",
        "Status: blocked_missing_inputs",
        "",
        "Reason:",
        f"- {report['blocked_reason']}",
        "",
        "Missing benchmark inputs:",
    ]
    for item in current_state["benchmark_intake_missing_inputs"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "Calibration separation:",
            f"- calibration_readiness_status: {current_state['calibration_readiness_status']}",
            f"- calibration_missing_inputs: {', '.join(current_state['calibration_missing_inputs']) if current_state['calibration_missing_inputs'] else 'none'}",
            "",
            "Dataset-role classification:",
        ]
    )
    for role in report["dataset_role_classification"]:
        lines.append(f"- {role['dataset_role']}: {role['status']}")
    lines.extend(
        [
            "",
            "Candidate acquisition report:",
            f"- recommendation: {candidate_report['recommendation']}",
            f"- selected_candidate_path: {candidate_report['selected_candidate_path']}",
            f"- available_local_candidate_count: {len(candidate_report['available_local_candidates'])}",
            f"- first_missing_geometry_fields: {', '.join(candidate_report['first_missing_geometry_fields']) if candidate_report['first_missing_geometry_fields'] else 'none'}",
            f"- first_missing_provenance_fields: {', '.join(candidate_report['first_missing_provenance_fields']) if candidate_report['first_missing_provenance_fields'] else 'none'}",
            f"- first_missing_uncertainty_fields: {', '.join(candidate_report['first_missing_uncertainty_fields']) if candidate_report['first_missing_uncertainty_fields'] else 'none'}",
            "",
            "Acquisition blocker matrix:",
        ]
    )
    for row in acquisition_blocker_matrix:
        lines.append(
            "- {category}: repository={repository_status}, acceptance={acceptance_status}, holdout={holdout}".format(
                category=row["category"],
                repository_status=row["repository_status"],
                acceptance_status=row["acceptance_status"],
                holdout=str(row["holdout_eligibility"]).lower(),
            )
        )
        lines.append(f"  required geometry: {', '.join(row['required_fields']['geometry'])}")
        lines.append(f"  required provenance: {', '.join(row['required_fields']['provenance'])}")
        lines.append(f"  required uncertainty: {', '.join(row['required_fields']['uncertainty'])}")
        lines.append(f"  acceptable provenance: {'; '.join(row['acceptable_provenance'])}")
        lines.append(f"  licensing readiness notes: {'; '.join(row['licensing_readiness_notes'])}")
        lines.append(f"  calibration/validation role: {row['calibration_validation_role']}")
        lines.append(f"  blocking reasons: {', '.join(row['blocking_reasons']) if row['blocking_reasons'] else 'none'}")
    lines.extend(
        [
            "",
            "Next-action recommendation:",
            f"- primary_track: {next_action_recommendation['primary_track']}",
            f"- first_acquisition_action: {next_action_recommendation['first_acquisition_action']}",
            f"- summary: {next_action_recommendation['summary']}",
            f"- data_acquisition: {next_action_recommendation['data_acquisition']['summary']}",
            f"- schema_repair: {next_action_recommendation['schema_repair']['summary']}",
            f"- scientific_deferral: {next_action_recommendation['scientific_deferral']['summary']}",
            "",
            "Physical-credibility gap update:",
            f"- physical_credibility_requirements_status: {physical_gap['physical_credibility_requirements_status']}",
            f"- current_physical_credibility_status: {physical_gap['current_physical_credibility_status']}",
            f"- blocked_reason: {physical_gap['blocked_reason']}",
            "",
            "This report is a blocker summary only and does not encode benchmark evidence.",
            "",
            "Artifact root:",
            f"- {pack_root}",
        ]
    )
    return "\n".join(lines) + "\n"


def validate_readiness_pack(
    *,
    pack_root: Path,
    acquisition_checklist_path: Path,
    dataset_inventory_path: Path,
    geometry_template_path: Path,
    provenance_template_path: Path,
    objective_placeholders_path: Path,
    blocked_no_evidence_report_path: Path,
    template_manifest_path: Path,
    benchmark_intake_manifest_path: Path,
) -> dict[str, Any]:
    required_paths = {
        "acquisition_checklist": acquisition_checklist_path,
        "required_dataset_inventory": dataset_inventory_path,
        "geometry_template": geometry_template_path,
        "provenance_template": provenance_template_path,
        "objective_function_placeholders": objective_placeholders_path,
        "blocked_no_evidence_report": blocked_no_evidence_report_path,
        "template_manifest": template_manifest_path,
        "benchmark_intake_manifest": benchmark_intake_manifest_path,
    }
    validated_paths = shared_require_paths_exist(
        required_paths,
        ObservedRunoutDepositionIntakeContractError,
        root=None,
        label_prefix="readiness_pack",
    )
    missing: list[str] = []
    unexpected = [
        str(path.relative_to(pack_root))
        for path in pack_root.iterdir()
        if path.is_file() and path.name not in {p.name for p in required_paths.values()}
    ]
    return {
        "validation_status": "ready" if not unexpected else "blocked_missing_inputs",
        "artifact_classification": "template_non_evidence",
        "pack_root": str(pack_root),
        "required_files_present": True,
        "missing_files": [],
        "unexpected_files": unexpected,
        "validation_boundary": "template_non_evidence_only",
        "checked_files": {name: str(path) for name, path in validated_paths.items()},
    }


def geometry_role_description(role: str) -> str:
    descriptions = {
        "source_polygon": "observed source geometry tied to provenance and release-zone screening",
        "runout_axis_line": "measured or digitized axis used for runout comparison",
        "deposition_footprint_polygon": "observed deposition footprint used for overlap comparison",
        "reference_observation_points": "site reference points used for future QA or alignment",
    }
    return descriptions.get(role, "required geometry role for benchmark intake")


def resolve_output_root(output_root: Path) -> Path:
    return output_root if output_root.is_absolute() else ROOT / output_root


def build_contract() -> dict[str, Any]:
    return {
        "geometry": {
            "required_crs": "EPSG:2056",
            "required_vertical_datum": "LN02",
            "allowed_geometry_roles": [
                "source_polygon",
                "runout_axis_line",
                "deposition_footprint_polygon",
                "reference_observation_points",
            ],
            "allowed_encodings": ["GeoJSON", "WKT"],
            "required_fields": [
                "geometry_id",
                "geometry_role",
                "geometry_encoding",
                "geometry_crs",
                "geometry_value",
            ],
        },
        "event_source_metadata": {
            "required_fields": [
                "event_id",
                "event_date",
                "site_id",
                "source_id",
                "source_name",
                "observer",
                "observation_method",
                "provenance_uri",
            ],
            "source_metadata_required": [
                "source_origin_description",
                "source_reference_frame",
                "source_geometry_reference",
            ],
        },
        "uncertainty": {
            "required_fields": [
                "geometry_tolerance_m",
                "position_tolerance_m",
                "timing_tolerance_days",
                "coverage_completeness",
                "qa_status",
                "uncertainty_notes",
            ],
            "measurement_units": {
                "geometry_tolerance_m": "m",
                "position_tolerance_m": "m",
                "timing_tolerance_days": "days",
            },
        },
        "objective_function_placeholders": {
            "required_fields": [
                "runout_endpoint_error_m",
                "runout_axis_distance_residual_m",
                "deposition_footprint_iou",
                "source_to_deposition_distance_residual_m",
                "objective_status",
            ],
            "objective_status": "placeholder_only",
            "fit_record_required": False,
            "notes": [
                "placeholders define future scoring interfaces only",
                "no objective fitting is claimed until real benchmark evidence is staged",
            ],
        },
    }


def build_field_requirement_map() -> list[dict[str, Any]]:
    return [
        field_requirement(
            "geometry.geometry_crs",
            "terrain_and_context_evidence",
            "site-specific spatial reference needed to interpret the observation in LV95",
        ),
        field_requirement(
            "geometry.geometry_role=source_polygon",
            "release_zone_evidence",
            "ties the observed record to source-zone provenance and release geometry",
        ),
        field_requirement(
            "geometry.geometry_id",
            "observed_runout_deposition",
            "provides a stable identifier for the geometry record",
        ),
        field_requirement(
            "geometry.geometry_role=runout_axis_line",
            "observed_runout_deposition",
            "captures the measured runout path for the benchmark intake",
        ),
        field_requirement(
            "geometry.geometry_role=deposition_footprint_polygon",
            "observed_runout_deposition",
            "captures the observed deposition extent for benchmark comparison",
        ),
        field_requirement(
            "geometry.geometry_encoding",
            "observed_runout_deposition",
            "records the geometry serialization needed to preserve the observation",
        ),
        field_requirement(
            "geometry.geometry_value",
            "observed_runout_deposition",
            "holds the actual geometry payload for the benchmark record",
        ),
        field_requirement(
            "event_source_metadata.event_id",
            "observed_runout_deposition",
            "creates a stable key for a future benchmark intake record",
        ),
        field_requirement(
            "event_source_metadata.event_date",
            "observed_runout_deposition",
            "anchors the observed event in time",
        ),
        field_requirement(
            "event_source_metadata.site_id",
            "observed_runout_deposition",
            "anchors the benchmark to a specific site record",
        ),
        field_requirement(
            "event_source_metadata.source_id",
            "release_zone_evidence",
            "connects the observation to source provenance",
        ),
        field_requirement(
            "event_source_metadata.source_name",
            "observed_runout_deposition",
            "names the source record attached to the observed event",
        ),
        field_requirement(
            "event_source_metadata.observer",
            "observed_runout_deposition",
            "records who captured or validated the observation",
        ),
        field_requirement(
            "event_source_metadata.observation_method",
            "observed_runout_deposition",
            "records the observation method used for the benchmark intake",
        ),
        field_requirement(
            "event_source_metadata.provenance_uri",
            "observed_runout_deposition",
            "supports traceability and audit of the intake record",
        ),
        field_requirement(
            "event_source_metadata.source_origin_description",
            "release_zone_evidence",
            "documents the origin of the source record and its release provenance",
        ),
        field_requirement(
            "event_source_metadata.source_reference_frame",
            "terrain_and_context_evidence",
            "keeps the source record anchored to the same spatial frame as the benchmark",
        ),
        field_requirement(
            "event_source_metadata.source_geometry_reference",
            "release_zone_evidence",
            "links the observation back to the source geometry used in the intake",
        ),
        field_requirement(
            "uncertainty.geometry_tolerance_m",
            "observed_runout_deposition",
            "records spatial measurement tolerance around the observed geometry",
        ),
        field_requirement(
            "uncertainty.position_tolerance_m",
            "observed_runout_deposition",
            "records point-position uncertainty for the intake geometry",
        ),
        field_requirement(
            "uncertainty.timing_tolerance_days",
            "observed_runout_deposition",
            "records event-time uncertainty for the observed record",
        ),
        field_requirement(
            "uncertainty.coverage_completeness",
            "observed_runout_deposition",
            "states whether the benchmark intake is complete or partial",
        ),
        field_requirement(
            "uncertainty.qa_status",
            "observed_runout_deposition",
            "records quality-assurance status for the intake record",
        ),
        field_requirement(
            "uncertainty.uncertainty_notes",
            "observed_runout_deposition",
            "captures the free-text uncertainty notes needed for review",
        ),
        field_requirement(
            "objective_function_placeholders.runout_endpoint_error_m",
            "calibration_data_and_objective_functions",
            "placeholder scoring term for a future calibration or fit record",
        ),
        field_requirement(
            "objective_function_placeholders.runout_axis_distance_residual_m",
            "calibration_data_and_objective_functions",
            "placeholder residual for future objective-function design",
        ),
        field_requirement(
            "objective_function_placeholders.deposition_footprint_iou",
            "calibration_data_and_objective_functions",
            "placeholder overlap score for future objective-function design",
        ),
        field_requirement(
            "objective_function_placeholders.source_to_deposition_distance_residual_m",
            "calibration_data_and_objective_functions",
            "placeholder residual connecting source provenance to deposition comparison",
        ),
        field_requirement(
            "objective_function_placeholders.objective_status",
            "calibration_data_and_objective_functions",
            "labels the objective terms as placeholders rather than fit results",
        ),
    ]


def field_requirement(field_path: str, requirement_category: str, why_it_matters: str) -> dict[str, Any]:
    return {
        "field_path": field_path,
        "physical_credibility_requirement": requirement_category,
        "why_it_matters": why_it_matters,
    }


def build_current_state() -> dict[str, Any]:
    benchmark_missing_inputs = shared_missing_repo_paths(
        {
            "manifest": EXPECTED_BENCHMARK_MANIFEST,
            "geometry": EXPECTED_BENCHMARK_GEOMETRY,
        }
    )
    calibration_missing_inputs = shared_missing_repo_paths({"calibration_root": EXPECTED_CALIBRATION_ROOT})
    adjacent_diagnostic_materials = []
    for path in LOCAL_OBSERVED_DEPOSITION_CANDIDATE_PATHS:
        metadata_path = path.with_name("metadata.json")
        metadata = load_json(metadata_path) if metadata_path.exists() else {}
        adjacent_diagnostic_materials.append(
            {
                "path": str(path),
                "classification": "diagnostic_only",
                "status": "present" if path.exists() else "missing",
                "supporting_metadata_path": str(metadata_path),
                "supporting_metadata_status": "present" if metadata_path.exists() else "missing",
                "supporting_license": str(metadata.get("license") or ""),
                "source_dataset": str(metadata.get("dataset_id") or path.parent.name),
                "provenance_note": str(metadata.get("coordinate_system") or "").strip(),
                "source_note": str((metadata.get("terrain_proxy") or {}).get("note") or "").strip(),
            }
        )
    return {
        "benchmark_intake_readiness_status": "blocked_missing_inputs" if benchmark_missing_inputs else "ready",
        "calibration_readiness_status": "blocked_missing_inputs" if calibration_missing_inputs else "ready",
        "benchmark_intake_dataset_status": "absent" if benchmark_missing_inputs else "present",
        "calibration_dataset_status": "absent" if calibration_missing_inputs else "present",
        "required_inputs": [
            {"path": str(EXPECTED_BENCHMARK_MANIFEST), "exists": EXPECTED_BENCHMARK_MANIFEST.exists()},
            {"path": str(EXPECTED_BENCHMARK_GEOMETRY), "exists": EXPECTED_BENCHMARK_GEOMETRY.exists()},
            {"path": str(EXPECTED_CALIBRATION_ROOT), "exists": EXPECTED_CALIBRATION_ROOT.exists()},
        ],
        "adjacent_diagnostic_materials": adjacent_diagnostic_materials,
        "benchmark_intake_missing_inputs": benchmark_missing_inputs,
        "calibration_missing_inputs": calibration_missing_inputs,
        "missing_inputs": benchmark_missing_inputs,
        "evidence_boundary": "diagnostic_only_until_independent_benchmark_is_staged",
    }


def current_state_summary(current_state: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "summary": "No independent observed runout/deposition benchmark intake is staged in the repo.",
            "status": current_state["benchmark_intake_readiness_status"],
        },
        {
            "summary": "No calibration dataset is available for objective fitting.",
            "status": current_state["calibration_readiness_status"],
        },
        {
            "summary": "Existing observed deposition files are diagnostic-only and not accepted as benchmark intake.",
            "status": "diagnostic_only",
        },
    ]


def build_acquisition_blocker_matrix(current_state: dict[str, Any]) -> list[dict[str, Any]]:
    matrix: list[dict[str, Any]] = []
    dataset_roles = build_dataset_role_classification(current_state)
    for blueprint in ACQUISITION_MATRIX_BLUEPRINTS:
        repository_status = dataset_role_status(dataset_roles, str(blueprint["dataset_role"]))
        acceptance_status = "ready" if repository_status == "present" else "blocked_missing_inputs"
        missing_inputs = [
            str(path)
            for path in blueprint["required_inputs"]
            if not Path(path).exists()
        ]
        matrix.append(
            {
                "schema_version": ACQUISITION_MATRIX_SCHEMA_VERSION,
                "category": blueprint["category"],
                "dataset_role": blueprint["dataset_role"],
                "label": blueprint["label"],
                "repository_status": repository_status,
                "acceptance_status": acceptance_status,
                "required_fields": deepcopy(blueprint["required_fields"]),
                "acceptable_provenance": list(blueprint["acceptable_provenance"]),
                "uncertainty_fields": list(blueprint["uncertainty_fields"]),
                "licensing_readiness_notes": list(blueprint["licensing_readiness_notes"]),
                "calibration_validation_role": dict(blueprint["calibration_validation_role"]),
                "holdout_eligibility": blueprint["holdout_eligibility"],
                "required_inputs": [str(path) for path in blueprint["required_inputs"]],
                "missing_inputs": missing_inputs,
                "acceptance_notes": list(blueprint["acceptance_notes"]),
                "blocking_reasons": missing_blocking_reasons(
                    repository_status=repository_status,
                    missing_inputs=missing_inputs,
                    required_fields=blueprint["required_fields"],
                ),
                "blocked_reason": blueprint["blocked_reason"],
            }
        )
    return matrix


def missing_blocking_reasons(
    *,
    repository_status: str,
    missing_inputs: list[str],
    required_fields: dict[str, list[str]],
) -> list[str]:
    reasons: list[str] = []
    if repository_status != "present":
        reasons.append("missing_inputs")
    if missing_inputs:
        reasons.append("missing_required_artifacts")
    if not required_fields.get("geometry"):
        reasons.append("missing_geometry")
    if not required_fields.get("provenance"):
        reasons.append("missing_provenance")
    if not required_fields.get("uncertainty"):
        reasons.append("missing_uncertainty")
    return reasons


def build_acquisition_fixture_template(category: str) -> dict[str, Any]:
    blueprint = acquisition_blueprint(category)
    return {
        "category": blueprint["category"],
        "dataset_role": blueprint["dataset_role"],
        "geometry": {
            field: f"placeholder_{category}_{field}"
            for field in blueprint["required_fields"]["geometry"]
        },
        "provenance": {
            field: f"placeholder_{category}_{field}"
            for field in blueprint["required_fields"]["provenance"]
        },
        "uncertainty": {
            field: f"placeholder_{category}_{field}"
            for field in blueprint["required_fields"]["uncertainty"]
        },
        "calibration_validation_role": dict(blueprint["calibration_validation_role"]),
        "holdout_eligibility": blueprint["holdout_eligibility"],
        "license": {
            "status": "placeholder_only",
            "note": "synthetic acquisition fixture for acceptance tests",
        },
    }


def classify_acquisition_fixture_row(category: str, fixture: dict[str, Any]) -> dict[str, Any]:
    blueprint = acquisition_blueprint(category)
    geometry = fixture.get("geometry") if isinstance(fixture.get("geometry"), dict) else {}
    provenance = fixture.get("provenance") if isinstance(fixture.get("provenance"), dict) else {}
    uncertainty = fixture.get("uncertainty") if isinstance(fixture.get("uncertainty"), dict) else {}
    role = fixture.get("calibration_validation_role")
    expected_role = blueprint["calibration_validation_role"]

    missing_geometry = [field for field in blueprint["required_fields"]["geometry"] if field not in geometry]
    missing_provenance = [field for field in blueprint["required_fields"]["provenance"] if field not in provenance]
    missing_uncertainty = [field for field in blueprint["required_fields"]["uncertainty"] if field not in uncertainty]

    calibration_validation_role_status = "clear" if role == expected_role else "unclear"
    blocking_reasons = []
    if missing_geometry:
        blocking_reasons.append("missing_geometry")
    if missing_provenance:
        blocking_reasons.append("missing_provenance")
    if missing_uncertainty:
        blocking_reasons.append("missing_uncertainty")
    if calibration_validation_role_status != "clear":
        blocking_reasons.append("unclear_calibration_role")

    if blocking_reasons:
        acceptance_status = "blocked_schema_gap" if any(
            reason.startswith("missing_") for reason in blocking_reasons
        ) else "blocked_role_unclear"
    else:
        acceptance_status = "ready"

    blocked_status = fixture.get("blocked_status")
    if blocked_status == "blocked_missing_inputs" and acceptance_status == "ready":
        blocking_reasons.append("overclaimed_blocked_status")
        acceptance_status = "blocked_claim_overclaim"

    return {
        "schema_version": ACQUISITION_MATRIX_SCHEMA_VERSION,
        "category": blueprint["category"],
        "dataset_role": blueprint["dataset_role"],
        "label": blueprint["label"],
        "repository_status": "present" if acceptance_status == "ready" else "missing",
        "acceptance_status": acceptance_status,
        "required_fields": deepcopy(blueprint["required_fields"]),
        "acceptable_provenance": list(blueprint["acceptable_provenance"]),
        "uncertainty_fields": list(blueprint["uncertainty_fields"]),
        "licensing_readiness_notes": list(blueprint["licensing_readiness_notes"]),
        "calibration_validation_role": dict(blueprint["calibration_validation_role"]),
        "holdout_eligibility": blueprint["holdout_eligibility"],
        "missing_geometry_fields": missing_geometry,
        "missing_provenance_fields": missing_provenance,
        "missing_uncertainty_fields": missing_uncertainty,
        "calibration_validation_role_status": calibration_validation_role_status,
        "blocking_reasons": blocking_reasons,
        "acceptance_notes": list(blueprint["acceptance_notes"]),
        "blocked_reason": blueprint["blocked_reason"],
    }


def acquisition_blueprint(category: str) -> dict[str, Any]:
    for blueprint in ACQUISITION_MATRIX_BLUEPRINTS:
        if blueprint["category"] == category:
            return blueprint
    raise KeyError(category)


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def load_yaml_fixture(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ObservedRunoutDepositionIntakeContractError(f"missing fixture-backed acceptance smoke fixture: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ObservedRunoutDepositionIntakeContractError(f"fixture-backed acceptance smoke fixture must be a mapping: {path}")
    return data


def build_next_action_recommendation(acquisition_blocker_matrix: list[dict[str, Any]]) -> dict[str, Any]:
    acquisition_gap_categories = {
        "observed_runout_deposition",
        "release_zone_provenance",
        "block_population_evidence",
        "calibration_inputs",
    }
    acquisition_gap_rows = [
        row
        for row in acquisition_blocker_matrix
        if row["category"] in acquisition_gap_categories and row["repository_status"] != "present"
    ]
    schema_gap_rows = [
        row
        for row in acquisition_blocker_matrix
        if row["acceptance_status"] in {"blocked_schema_gap", "blocked_role_unclear", "blocked_claim_overclaim"}
    ]
    if acquisition_gap_rows:
        primary_track = "data_acquisition"
    elif schema_gap_rows:
        primary_track = "schema_repair"
    else:
        primary_track = "scientific_deferral"
    return {
        "primary_track": primary_track,
        "first_acquisition_action": "Stage an independent observed runout/deposition benchmark manifest and the matching observed geometry record(s).",
        "data_acquisition": {
            "summary": "Acquire a real observed runout/deposition package before trying to reuse the evidence for anything else.",
            "applies_when": "no independent benchmark package is staged",
        },
        "schema_repair": {
            "summary": "Repair geometry, provenance, uncertainty, or role metadata only after a package has been staged.",
            "applies_when": "a package exists but fails the acceptance fixture shape",
        },
        "scientific_deferral": {
            "summary": "Defer any stronger scientific claim if the staged evidence still does not justify it.",
            "applies_when": "the package is complete but the claim would still exceed the evidence boundary",
        },
        "summary": (
            "Acquire the observed benchmark first; repair schema only if a staged package fails geometry, provenance, "
            "uncertainty, or role checks; defer the scientific claim if the staged package is still insufficient for "
            "the requested interpretation."
        ),
    }


def claim_boundaries() -> dict[str, bool]:
    return {
        "calibration_claims_allowed": False,
        "physical_probability_claims_allowed": False,
        "annual_frequency_claims_allowed": False,
        "risk_exposure_vulnerability_claims_allowed": False,
        "operational_claims_allowed": False,
    }


def validate_claim_boundaries(boundaries: dict[str, Any]) -> None:
    shared_require_false_fields(
        boundaries,
        (
            "calibration_claims_allowed",
            "physical_probability_claims_allowed",
            "annual_frequency_claims_allowed",
            "risk_exposure_vulnerability_claims_allowed",
            "operational_claims_allowed",
        ),
        ObservedRunoutDepositionIntakeContractError,
        label_prefix="claim_boundaries",
    )


def render_text_report(report: dict[str, Any]) -> str:
    contract = report["benchmark_intake_contract"]
    benchmark_manifest = report["benchmark_intake_manifest"]
    current_state = report["current_repo_state"]
    candidate_report = report["candidate_acquisition_report"]
    acquisition_blocker_matrix = report["acquisition_blocker_matrix"]
    next_action_recommendation = report["next_action_recommendation"]
    lines = [
        f"schema_version: {report['schema_version']}",
        f"observed_runout_deposition_intake_status: {report['observed_runout_deposition_intake_status']}",
        f"blocked_reason: {report['blocked_reason']}",
        "",
        "benchmark_intake_contract:",
        f"- geometry.required_crs: {contract['geometry']['required_crs']}",
        f"- geometry.required_vertical_datum: {contract['geometry']['required_vertical_datum']}",
        f"- geometry.allowed_geometry_roles: {', '.join(contract['geometry']['allowed_geometry_roles'])}",
        f"- event_source_metadata.required_fields: {', '.join(contract['event_source_metadata']['required_fields'])}",
        f"- uncertainty.required_fields: {', '.join(contract['uncertainty']['required_fields'])}",
        f"- objective_function_placeholders.required_fields: {', '.join(contract['objective_function_placeholders']['required_fields'])}",
        "",
        "benchmark_intake_manifest:",
        f"- manifest_status: {benchmark_manifest['manifest_status']}",
        f"- dataset_roles: {', '.join(role['dataset_role'] for role in benchmark_manifest['dataset_role_classification'])}",
        f"- physical_credibility_status: {benchmark_manifest['physical_credibility_gap_update']['current_physical_credibility_status']}",
        "",
        "fixture_acceptance_smoke:",
        f"- fixture_path: {report['fixture_acceptance_smoke']['fixture_path']}",
        f"- fixture_status: {report['fixture_acceptance_smoke']['fixture_status']}",
        f"- schema_acceptance_status: {report['fixture_acceptance_smoke']['fixture_classification']['acceptance_status']}",
        f"- calibration_validation_role_status: {report['fixture_acceptance_smoke']['fixture_classification']['calibration_validation_role_status']}",
        f"- holdout_eligibility: {str(report['fixture_acceptance_smoke']['fixture_classification']['holdout_eligibility']).lower()}",
        f"- physical_evidence_status: {report['fixture_acceptance_smoke']['physical_evidence_status']}",
        "",
        "physical_credibility_gap_update:",
        f"- physical_credibility_requirements_status: {report['physical_credibility_gap_update']['physical_credibility_requirements_status']}",
        f"- current_physical_credibility_status: {report['physical_credibility_gap_update']['current_physical_credibility_status']}",
        f"- blocked_reason: {report['physical_credibility_gap_update']['blocked_reason']}",
        "",
        "candidate_acquisition_report:",
        f"- recommendation: {candidate_report['recommendation']}",
        f"- selected_candidate_path: {candidate_report['selected_candidate_path']}",
        f"- available_local_candidate_count: {len(candidate_report['available_local_candidates'])}",
        f"- first_missing_geometry_fields: {', '.join(candidate_report['first_missing_geometry_fields']) if candidate_report['first_missing_geometry_fields'] else 'none'}",
        f"- first_missing_provenance_fields: {', '.join(candidate_report['first_missing_provenance_fields']) if candidate_report['first_missing_provenance_fields'] else 'none'}",
        f"- first_missing_uncertainty_fields: {', '.join(candidate_report['first_missing_uncertainty_fields']) if candidate_report['first_missing_uncertainty_fields'] else 'none'}",
        "",
        "dataset_role_classification:",
    ]
    for item in report["dataset_role_classification"]:
        lines.append(f"- {item['dataset_role']}: {item['status']}")
    lines.extend(
        [
            "",
            "field_requirement_map:",
        ]
    )
    for item in report["field_requirement_map"]:
        lines.append(
            f"- {item['field_path']} -> {item['physical_credibility_requirement']}: {item['why_it_matters']}"
        )
    lines.append("")
    lines.append("current_repo_state:")
    lines.append(f"- benchmark_intake_readiness_status: {current_state['benchmark_intake_readiness_status']}")
    lines.append(f"- calibration_readiness_status: {current_state['calibration_readiness_status']}")
    lines.append(f"- benchmark_intake_dataset_status: {current_state['benchmark_intake_dataset_status']}")
    lines.append(f"- calibration_dataset_status: {current_state['calibration_dataset_status']}")
    lines.append(f"- evidence_boundary: {current_state['evidence_boundary']}")
    lines.append("acquisition_blocker_matrix:")
    for item in acquisition_blocker_matrix:
        lines.append(
            f"- {item['category']}: repository={item['repository_status']} acceptance={item['acceptance_status']} "
            f"holdout={str(item['holdout_eligibility']).lower()}"
        )
        lines.append(f"  required_geometry: {', '.join(item['required_fields']['geometry'])}")
        lines.append(f"  required_provenance: {', '.join(item['required_fields']['provenance'])}")
        lines.append(f"  required_uncertainty: {', '.join(item['required_fields']['uncertainty'])}")
        lines.append(f"  acceptable_provenance: {'; '.join(item['acceptable_provenance'])}")
        lines.append(f"  calibration_validation_role: {item['calibration_validation_role']}")
    lines.append("next_action_recommendation:")
    lines.append(f"- primary_track: {next_action_recommendation['primary_track']}")
    lines.append(f"- first_acquisition_action: {next_action_recommendation['first_acquisition_action']}")
    lines.append(f"- summary: {next_action_recommendation['summary']}")
    lines.append("benchmark_intake_missing_inputs:")
    for item in current_state["benchmark_intake_missing_inputs"]:
        lines.append(f"- {item}")
    lines.append("calibration_missing_inputs:")
    for item in current_state["calibration_missing_inputs"]:
        lines.append(f"- {item}")
    lines.append("current_state_summary:")
    for item in report["current_state_summary"]:
        lines.append(f"- {item['summary']} [{item['status']}]")
    lines.append("missing_inputs:")
    for item in current_state["missing_inputs"]:
        lines.append(f"- {item}")
    if "readiness_pack" in report:
        readiness_pack = report["readiness_pack"]
        lines.append("")
        lines.append("readiness_pack:")
        lines.append(f"- readiness_pack_status: {readiness_pack['readiness_pack_status']}")
        lines.append(f"- artifact_classification: {readiness_pack['artifact_classification']}")
        lines.append(f"- readiness_pack_root: {readiness_pack['readiness_pack_root']}")
        for name, path in readiness_pack["generated_files"].items():
            lines.append(f"- {name}: {path}")
    lines.append("")
    lines.append("claim_boundaries:")
    for key, value in report["claim_boundaries"].items():
        lines.append(f"- {key}: {str(value).lower()}")
    return "\n".join(lines)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
