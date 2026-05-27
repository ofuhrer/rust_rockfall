#!/usr/bin/env python3
"""Assess evidence gaps between workflow credibility and physical credibility.

This helper is read-only. It composes existing manifests, fixtures, and docs
into a structured gap assessment and does not calibrate, tune, or run any
simulations.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any
from functools import partial

try:
    import yaml  # type: ignore
except ImportError as exc:  # pragma: no cover - environment setup.
    raise SystemExit("PyYAML is required. Run this script with `PYENV_VERSION=system uv run python ...`; CI may use `requirements-tools.txt`") from exc

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from lib.workflow_validation import (
    missing_repo_paths as shared_missing_repo_paths,
    require as shared_require,
    require_false_fields as shared_require_false_fields,
    scan_text_for_misleading_claims as shared_scan_text_for_misleading_claims,
)

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "validation_calibration_evidence_gaps_v1"
ALLOWED_CLASSIFICATIONS = {"present", "partial", "missing", "out_of_scope", "not_inferred"}

import audit_chant_sura_holdout_split as holdout_split  # noqa: E402
import audit_conditional_denominator_provenance as denominator_provenance  # noqa: E402
import check_calibration_separation_preflight as calibration_separation  # noqa: E402
import audit_trajectory_deposition_traceability as deposition_traceability  # noqa: E402
import validate_source_frequency_evidence as source_frequency_evidence  # noqa: E402
import validate_block_release_probability_evidence as block_release_probability_evidence  # noqa: E402

BLOCK_POPULATION_ACQUISITION_BLOCKERS: tuple[dict[str, Any], ...] = (
    {
        "blocker_id": "block_population_survey_missing",
        "first_missing_input": "block_size_survey_or_photogrammetry_census",
        "missing_inputs": [
            "survey_footprint_geometry",
            "block_count_or_size_class_record",
            "survey_provenance_uri",
            "explicit_not_source_frequency_catalogue_note",
        ],
        "blocked_claims": ["physical_probability", "annual_frequency"],
    },
)

BLOCK_POPULATION_FUTURE_GATE_PREREQUISITES: tuple[dict[str, Any], ...] = (
    {
        "gate_id": "physical_probability_phase_gate",
        "prerequisite_id": "accepted_block_population_evidence_contract",
        "summary": "Block-population evidence must be accepted before any physical-probability bridge is considered.",
    },
)

SOURCE_FREQUENCY_ACQUISITION_BLOCKERS: tuple[dict[str, Any], ...] = (
    {
        "blocker_id": "source_frequency_catalogue_missing",
        "first_missing_input": "historical_rockfall_event_catalogue",
        "missing_inputs": [
            "repeat_source_zone_observations",
            "rate_time_window_and_censoring_rules",
            "rate_provenance",
        ],
        "blocked_claims": ["physical_probability", "annual_frequency"],
    },
)

SOURCE_FREQUENCY_FUTURE_GATE_PREREQUISITES: tuple[dict[str, Any], ...] = (
    {
        "gate_id": "physical_source_frequency_design_gate",
        "prerequisite_id": "accepted_source_frequency_evidence_contract",
        "summary": "Accepted source-frequency evidence is required before the design gate can consider prototype authorization.",
    },
    {
        "gate_id": "physical_frequency_reducer_preconditions",
        "prerequisite_id": "accepted_overlap_adjusted_reducer_and_uncertainty_propagation_contract",
        "summary": "Overlap-adjusted reducers and uncertainty propagation must be accepted before annual or physical products are contemplated.",
    },
)
DEFAULT_SOURCE_FREQUENCY_EVIDENCE_PATH = ROOT / "validation/private/source_frequency_evidence_tschamut_design_review_v1.yaml"
DEFAULT_BLOCK_RELEASE_PROBABILITY_EVIDENCE_PATH = (
    ROOT / "validation/data/processed/tschamut/block_release_probability_evidence_tschamut_public_candidate_v1.yaml"
)
DEFAULT_BLOCK_POPULATION_EVIDENCE_PATH = (
    ROOT / "validation/data/processed/tschamut/block_population_evidence_tschamut_public_candidate_v1.yaml"
)
DEFAULT_OBSERVED_RUNOUT_DEPOSITION_BENCHMARK_ROOT = ROOT / "validation/data/processed/observed_runout_deposition_benchmark"
DEFAULT_OBSERVED_RUNOUT_DEPOSITION_BENCHMARK_MANIFEST = DEFAULT_OBSERVED_RUNOUT_DEPOSITION_BENCHMARK_ROOT / "manifest.json"
DEFAULT_OBSERVED_RUNOUT_DEPOSITION_BENCHMARK_GEOMETRY = (
    DEFAULT_OBSERVED_RUNOUT_DEPOSITION_BENCHMARK_ROOT / "observed_runout_deposition.geojson"
)
DEFAULT_TSCHAMUT_CALIBRATION_OBJECTIVE_CONTRACT = (
    ROOT / "calibration/experiments/tschamut_v0_3/objective_contract.json"
)

PHYSICAL_PROBABILITY_EVIDENCE_REQUIREMENTS: tuple[dict[str, Any], ...] = (
    {
        "evidence_class": "source_frequency_evidence",
        "source_category": "source_frequency_and_temporal_frequency_evidence",
        "required_status": "present",
        "pass_criteria": [
            "historical or monitored source-occurrence catalogue is staged",
            "time window, censoring rules, uncertainty, and provenance are explicit",
            "conditional sampling weights are not reused as source frequency",
        ],
        "failure_modes": [
            "missing historical_rockfall_event_catalogue",
            "missing rate_time_window_and_censoring_rules",
            "conditional sampling weights used as frequency evidence",
        ],
    },
    {
        "evidence_class": "release_probability_model",
        "source_category": "release_zone_evidence",
        "required_status": "present",
        "pass_criteria": [
            "site-specific release-zone geometry is field-supported or independently justified",
            "release-probability semantics are documented separately from deterministic candidate generation",
            "source-zone provenance can be checked against holdout evidence",
        ],
        "failure_modes": [
            "missing site_specific_release_zone_geometry_package",
            "release candidates remain workflow generated only",
            "no release-probability semantics distinct from conditional scenario design",
        ],
    },
    {
        "evidence_class": "block_population_evidence",
        "source_category": "block_size_and_block_population_evidence",
        "required_status": "present",
        "pass_criteria": [
            "block-size or block-population survey/census is staged",
            "survey frame, size classes, counts, uncertainty, and provenance are explicit",
            "representative scenarios are separated from population semantics",
        ],
        "failure_modes": [
            "missing block_size_survey_or_photogrammetry_census",
            "missing block_count_or_size_class_record",
            "representative block scenarios treated as population evidence",
        ],
    },
    {
        "evidence_class": "calibration_evidence",
        "source_category": "calibration_evidence",
        "required_status": "present",
        "pass_criteria": [
            "calibration dataset, objective function, parameter bounds, and fitted values are recorded",
            "calibration data are not reused as holdout validation evidence",
            "selected parameters are tied to a reproducible calibration record",
        ],
        "failure_modes": [
            "missing calibration dataset and objective function",
            "missing parameter bounds or fitted-value provenance",
            "calibration and validation evidence overlap without a holdout label",
        ],
    },
    {
        "evidence_class": "independent_holdout_validation",
        "source_category": "holdout_and_validation_evidence",
        "required_status": "present",
        "pass_criteria": [
            "independent holdout deposition/runout or field benchmark is staged",
            "split rules show the holdout was not used for model selection or calibration",
            "scoring protocol is explicit before interpreting physical probability products",
        ],
        "failure_modes": [
            "missing independent holdout benchmark",
            "holdout data reused for selection, calibration, or diagnostics",
            "missing scoring protocol for physical-probability interpretation",
        ],
    },
    {
        "evidence_class": "conditional_denominator_provenance",
        "source_category": "conditional_denominator_audit",
        "required_status": "complete",
        "pass_criteria": [
            "trajectory denominator, filters, conditional scope, and annualized=false fields are present",
            "conditional layers do not infer source frequency",
            "denominator provenance remains replayable from the hazard manifest",
        ],
        "failure_modes": [
            "missing local hazard manifest",
            "missing trajectory denominator or conditioning fields",
            "annualized or physical-probability flags are not explicitly false",
        ],
    },
    {
        "evidence_class": "trajectory_deposition_traceability",
        "source_category": "trajectory_deposition_traceability_audit",
        "required_status": "traceable",
        "pass_criteria": [
            "deposition-density layer traces to validation deposition and trajectory outputs",
            "validation row counts match hazard manifest input counts",
            "missing output families fail closed before scientific interpretation",
        ],
        "failure_modes": [
            "missing local validation or hazard manifest",
            "missing deposition, trajectory, or hazard-layer output",
            "validation/hazard row counts disagree",
        ],
    },
)


class ValidationCalibrationEvidenceGapsError(ValueError):
    """User-facing validation/calibration evidence gap error."""


require = partial(shared_require, error_cls=ValidationCalibrationEvidenceGapsError)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    args = parser.parse_args(argv)

    report = build_report()
    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    output = json.dumps(report, indent=2, sort_keys=True) if args.format == "json" else render_text_report(report)
    print(output)
    return 0


def build_report(source_frequency_evidence_path: Path | None = None) -> dict[str, Any]:
    sources = source_documents()
    datasets = load_dataset_registry()
    tschamut_manifest = load_yaml(ROOT / "data/processed/swisstopo/tschamut_public_pilot_manifest.yaml")
    tschamut_gate = load_yaml(ROOT / "validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml")
    tschamut_target = load_yaml(ROOT / "validation/pilot_runs/tschamut_public_scalable_conditional_target_gate_v1.yaml")
    chant_contact = load_yaml(ROOT / "validation/cases/chant_sura_contact.yaml")
    chant_contact_heldout = load_yaml(ROOT / "validation/cases/chant_sura_contact_heldout.yaml")
    chant_model_selection = load_yaml(ROOT / "validation/internal/shape_contact_v0_chant_sura_model_selection.yaml")
    chant_split = load_json(ROOT / "validation/data/processed/chant_sura_2020/metadata_contact_split.json")
    balfrin_readiness = load_yaml(ROOT / "validation/pilot_runs/tschamut_public_balfrin_readiness_v1.yaml")
    balfrin_reproduction = load_yaml(ROOT / "validation/pilot_runs/tschamut_public_balfrin_target_gate_reproduction_v1.yaml")
    candidate_manifest = load_yaml(
        ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml"
    )
    candidate_portability = assess_candidate_portability(candidate_manifest)

    observed_intake_report = safe_observed_runout_deposition_intake()
    observed_deposition = observed_deposition_gap(
        datasets,
        tschamut_manifest,
        tschamut_gate,
        chant_contact,
        chant_contact_heldout,
        observed_intake_report,
    )
    block_release_probability_intake = load_block_release_probability_intake()
    release_zone = release_zone_gap(
        datasets,
        tschamut_manifest,
        candidate_portability,
        block_release_probability_intake,
    )
    block_population_intake = load_block_population_intake()
    block_population = block_population_gap(
        datasets,
        tschamut_gate,
        chant_model_selection,
        block_population_intake,
    )
    source_frequency_intake = load_source_frequency_intake(source_frequency_evidence_path)
    source_frequency = source_frequency_gap(datasets, tschamut_gate, chant_model_selection, source_frequency_intake)
    terrain_context = terrain_context_gap(tschamut_manifest, tschamut_gate, tschamut_target, candidate_portability)
    calibration_objective_contract = load_tschamut_calibration_objective_contract()
    calibration = calibration_gap(
        tschamut_manifest,
        tschamut_gate,
        chant_contact,
        chant_contact_heldout,
        chant_model_selection,
        calibration_objective_contract,
    )
    transfer = transfer_gap(candidate_manifest, candidate_portability, chant_contact, chant_contact_heldout, balfrin_readiness)
    validation_leakage_guardrails = build_validation_leakage_guardrails(
        holdout_split.build_report(),
        calibration_separation.build_report(),
    )
    calibration_holdout_separation = build_chant_sura_calibration_holdout_separation_check(chant_split)
    holdout = holdout_gap(
        tschamut_gate,
        tschamut_target,
        chant_contact_heldout,
        chant_split,
        balfrin_readiness,
        balfrin_reproduction,
        observed_intake_report,
        validation_leakage_guardrails,
        calibration_holdout_separation,
    )
    denominator_audit = safe_denominator_audit()
    traceability_audit = safe_deposition_traceability_audit()

    claim_boundary_matrix = [
        {
            "boundary": "workflow_reproducibility",
            "classification": "present",
            "evidence": [
                "same-scale readiness, deterministic case regeneration, and bounded uncertainty outputs exist",
                "Tschamut gate/target manifests and package audits are reproducible",
            ],
            "why_it_matters": "Supports repeatable workflow execution, not physical credibility by itself.",
        },
        {
            "boundary": "conditional_diagnostic_interpretation",
            "classification": "present",
            "evidence": [
                "same-scale convergence remains inconclusive",
                "context remains limiting rather than absent",
                "output profile and runtime evidence are measured",
            ],
            "why_it_matters": "Supports diagnostic interpretation only.",
        },
        {
            "boundary": "release_candidate_physical_meaning",
            "classification": "present",
            "evidence": [
                "workflow-generated release candidates are labeled workflow_generated, field_supported, mixed_provenance, or blocked_missing_provenance",
                "scenario sampling weights are conditional only and are not occurrence probabilities, annual frequencies, return periods, or risk",
            ],
            "why_it_matters": "Prevents release-zone and scenario automation from being overread as field-supported source probability evidence.",
        },
        {
            "boundary": "physical_probability",
            "classification": "missing",
            "evidence": [
                "no source occurrence rates are staged",
                "no block-population frequency model is staged",
                "current scenario weights are conditional only",
            ],
            "why_it_matters": "Physical probability requires frequency semantics that the current pilot does not have.",
        },
        {
            "boundary": "annual_frequency",
            "classification": "out_of_scope",
            "evidence": [
                "backlog and run-frozen manifests explicitly exclude annual-frequency claims",
            ],
            "why_it_matters": "Annual intensity-frequency products remain deferred.",
        },
        {
            "boundary": "risk_exposure_vulnerability",
            "classification": "out_of_scope",
            "evidence": [
                "current products are hazard diagnostics, not exposure or vulnerability products",
            ],
            "why_it_matters": "Risk mapping needs additional socioeconomic and consequence assumptions not present here.",
        },
        {
            "boundary": "operational_use",
            "classification": "out_of_scope",
            "evidence": [
                "the selected pilot is still classified as research diagnostic and not operational",
            ],
            "why_it_matters": "Operational use requires a separate acceptance path and more evidence.",
        },
    ]

    evidence_gap_categories = [
        observed_deposition,
        release_zone,
        block_population,
        source_frequency,
        terrain_context,
        calibration,
        holdout,
        transfer,
    ]

    report = {
        "schema_version": SCHEMA_VERSION,
        "candidate_site_id": candidate_portability["candidate_site"]["candidate_site_id"],
        "candidate_site_name": candidate_portability["candidate_site"]["candidate_site_name"],
        "second_site_portability_status": candidate_portability["second_site_portability_status"],
        "post_diagnostic_scale_context": post_diagnostic_scale_context(),
        "source_frequency_intake": source_frequency_intake,
        "block_release_probability_intake": block_release_probability_intake,
        "block_population_intake": block_population_intake,
        "calibration_objective_contract": calibration_objective_contract,
        "physical_credibility_status": derive_physical_credibility_status(evidence_gap_categories),
        "physical_probability_claims_allowed": False,
        "physical_probability_readiness_check": build_physical_probability_readiness_check(
            evidence_gap_categories,
            denominator_audit=denominator_audit,
            traceability_audit=traceability_audit,
        ),
        "calibration_status": calibration["classification"],
        "validation_status": "partial",
        "annual_frequency_claims_allowed": False,
        "operational_claims_allowed": False,
        "risk_exposure_vulnerability_claims_allowed": False,
        "scale_up_authorized": False,
        "evidence_gap_categories": evidence_gap_categories,
        "claim_boundary_matrix": claim_boundary_matrix,
        "validation_leakage_guardrails": validation_leakage_guardrails,
        "calibration_holdout_separation_check": calibration_holdout_separation,
        "next_concrete_scientific_tasks": next_concrete_scientific_tasks(evidence_gap_categories),
        "product_layer_claim_boundaries": product_layer_claim_boundaries(),
        "site_reference_evidence": site_reference_evidence(
            datasets,
            tschamut_manifest,
            tschamut_gate,
            tschamut_target,
            chant_contact,
            chant_contact_heldout,
            chant_model_selection,
            chant_split,
            balfrin_readiness,
            balfrin_reproduction,
        ),
        "required_evidence_for_physical_credibility": [
            "Independent holdout field or benchmark deposition/runout evidence not used to tune the current model",
            "Site-specific release-zone geometry and source-zone provenance that can be tested against held-out evidence",
            "Block occurrence / block-population evidence if physical probability semantics are ever claimed",
            "Terrain and context provenance at the site-specific CRS / extent / resolution needed for interpretation",
            "Explicit calibration dataset and objective if parameter fitting is ever pursued",
            "A staged second-site public-geodata contract and holdout benchmark if portability beyond Tschamut is claimed",
        ],
        "current_evidence_sources": sources,
    }
    validate_report_boundaries(report)
    shared_scan_text_for_misleading_claims(report, require_fn=require)
    return report


def post_diagnostic_scale_context() -> dict[str, Any]:
    return {
        "status": "diagnostic_scale_progress_does_not_close_scientific_gaps",
        "measured_diagnostic_evidence": {
            "release_zone_count": 24,
            "evidence_type": "single_node_postproc_reducer_pressure",
            "repeatability_status": "measured_repeatability_pair",
            "source_documents": [
                "docs/balfrin_24_zone_diagnostic_run_tb579.md",
                "docs/balfrin_24_zone_repeatability_runs_tb581.md",
                "docs/balfrin_24_zone_repeatability_metrics_tb582.md",
                "docs/balfrin_scale_demonstration_management_package.md",
            ],
        },
        "scientific_interpretation": (
            "The 24-zone diagnostic push improves execution and output-footprint confidence, but it does not add calibration, holdout, source-frequency, "
            "block-population, or field-observation evidence."
        ),
        "claim_boundaries": {
            "performance_feasibility_progress": True,
            "scientific_validity_upgraded": False,
            "physical_probability_claims_allowed": False,
            "operational_claims_allowed": False,
            "swiss_wide_claims_allowed": False,
        },
    }


def next_concrete_scientific_tasks(evidence_gap_categories: list[dict[str, Any]]) -> list[dict[str, Any]]:
    categories = {entry["category"]: entry for entry in evidence_gap_categories}
    task_specs = [
        (
            "stage_independent_holdout_deposition_runout_evidence",
            "holdout_and_validation_evidence",
            "Stage an independent holdout deposition/runout benchmark with site provenance, split rules, and scoring fields.",
            "validation/data/processed/<site>/holdout_validation_evidence_manifest.json",
        ),
        (
            "stage_source_frequency_catalogue",
            "source_frequency_and_temporal_frequency_evidence",
            "Stage source-frequency evidence with observation windows, censoring assumptions, provenance, and uncertainty.",
            "validation/source_frequency/<site>_source_frequency_evidence.yaml",
        ),
        (
            "stage_block_population_survey",
            "block_size_and_block_population_evidence",
            "Stage block-population or block-size survey evidence before any physical-probability bridge is considered.",
            "validation/block_population/<site>_block_population_evidence.yaml",
        ),
        (
            "define_calibration_dataset_and_objective",
            "calibration_evidence",
            "Define a calibration dataset, objective function, parameter scope, and separate holdout split before parameter fitting.",
            "calibration/experiments/<site>/calibration_design.yaml",
        ),
        (
            "stage_second_site_public_geodata_inputs",
            "multi_site_transfer_evidence",
            "Stage the Chant Sura / Fluelapass public geodata inputs needed to turn portability planning into a second-site check.",
            "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/",
        ),
    ]
    tasks: list[dict[str, Any]] = []
    for task_id, category, action, target_artifact in task_specs:
        gap = categories.get(category, {})
        if gap.get("classification") == "present":
            continue
        if category == "calibration_evidence" and gap.get("support_role") == "objective_defined_pending_smoke":
            continue
        tasks.append(
            {
                "rank": len(tasks) + 1,
                "task_id": task_id,
                "category": category,
                "current_classification": gap.get("classification", "unknown"),
                "first_missing_input": gap.get("first_missing_input"),
                "action": action,
                "target_artifact": target_artifact,
                "why_now": (
                    "Performance feasibility has improved enough that the next limiting factor is scientific evidence rather than another local execution report."
                ),
                "claim_boundary": "preparatory evidence acquisition only; no calibration, validation acceptance, physical-probability, or operational claim",
            }
        )
    return tasks


def build_validation_leakage_guardrails(
    holdout_report: dict[str, Any],
    calibration_report: dict[str, Any],
) -> dict[str, Any]:
    failing_checks = []
    if holdout_report.get("audit_status") != "passed":
        failing_checks.append(
            {
                "guardrail": "holdout_split_independence",
                "status": holdout_report.get("audit_status", "unknown"),
                "dataset_or_parameter_source": holdout_report.get("dataset_id", "unknown"),
                "failure_detail": ", ".join(holdout_report.get("shared_trajectory_ids") or []) or "holdout split did not pass",
                "next_local_command": (
                    "PYENV_VERSION=system uv run python scripts/audit_chant_sura_holdout_split.py --format json"
                ),
            }
        )
    if calibration_report.get("preflight_status") != "passed":
        replay = calibration_report.get("failure_replay") or {}
        blocker = replay.get("first_blocker") if isinstance(replay.get("first_blocker"), dict) else {}
        failing_checks.append(
            {
                "guardrail": "calibration_validation_separation",
                "status": calibration_report.get("preflight_status", "unknown"),
                "dataset_or_parameter_source": blocker.get("value")
                or blocker.get("case_path")
                or calibration_report.get("calibration_root", "unknown"),
                "failure_detail": replay.get("missing_evidence_or_invalid_coupling")
                or "calibration separation preflight did not pass",
                "next_local_command": (
                    "PYENV_VERSION=system uv run python scripts/check_calibration_separation_preflight.py --format json"
                ),
            }
        )
    return {
        "schema_version": "validation_leakage_guardrails_v1",
        "guardrail_status": "passed" if not failing_checks else "blocked_validation_leakage_risk",
        "holdout_split_audit_status": holdout_report.get("audit_status", "unknown"),
        "calibration_separation_preflight_status": calibration_report.get("preflight_status", "unknown"),
        "failing_checks": failing_checks,
        "interpretation_allowed": not failing_checks,
        "next_local_recovery_command": (
            failing_checks[0]["next_local_command"]
            if failing_checks
            else "PYENV_VERSION=system uv run python scripts/assess_validation_calibration_evidence_gaps.py --format json"
        ),
        "claim_boundaries": {
            "calibration_performed": False,
            "parameter_tuning_performed": False,
            "external_validation_claimed": False,
            "validation_acceptance_claimed": False,
            "operational_claims_allowed": False,
            "physical_probability_claims_allowed": False,
        },
    }


def build_chant_sura_calibration_holdout_separation_check(chant_split: dict[str, Any]) -> dict[str, Any]:
    model_selection = dict(chant_split.get("model_selection_subset") or {})
    heldout = dict(chant_split.get("held_out_evaluation_subset") or {})
    records = []
    for trajectory_id in model_selection.get("trajectory_ids") or []:
        records.append(
            {
                "dataset_id": str(trajectory_id),
                "site_id": "chant_sura",
                "event_id": str(trajectory_id).split("_seg", 1)[0],
                "sample_id": str(trajectory_id),
                "role": "calibration_candidate",
            }
        )
    for trajectory_id in heldout.get("trajectory_ids") or []:
        records.append(
            {
                "dataset_id": str(trajectory_id),
                "site_id": "chant_sura",
                "event_id": str(trajectory_id).split("_seg", 1)[0],
                "sample_id": str(trajectory_id),
                "role": "holdout_validation",
            }
        )
    return build_calibration_holdout_separation_check(records)


def build_calibration_holdout_separation_check(records: list[dict[str, Any]]) -> dict[str, Any]:
    calibration_records = [
        record for record in records if str(record.get("role")) in {"calibration", "calibration_candidate"}
    ]
    validation_records = [
        record for record in records if str(record.get("role")) in {"validation", "holdout_validation"}
    ]
    holdout_records = [record for record in validation_records if str(record.get("role")) == "holdout_validation"]

    missing_reasons: list[str] = []
    if not calibration_records:
        missing_reasons.append("missing_calibration_dataset_record")
    if not validation_records:
        missing_reasons.append("missing_validation_dataset_record")
    if not holdout_records:
        missing_reasons.append("missing_explicit_holdout_validation_label")

    overlaps = find_calibration_validation_overlaps(calibration_records, validation_records)
    if overlaps:
        status = "blocked_calibration_validation_overlap"
    elif missing_reasons:
        status = "blocked_missing_holdout_or_calibration_record"
    else:
        status = "separated_holdout_ready"

    return {
        "schema_version": "calibration_holdout_separation_check_v1",
        "separation_status": status,
        "stronger_scientific_conclusions_allowed": status == "separated_holdout_ready",
        "calibration_record_count": len(calibration_records),
        "validation_record_count": len(validation_records),
        "holdout_record_count": len(holdout_records),
        "missing_reasons": missing_reasons,
        "overlap_count": len(overlaps),
        "overlaps": overlaps,
        "next_required_acquisition_step": calibration_holdout_next_step(status, missing_reasons, overlaps),
        "claim_boundary": (
            "This check only verifies separation. It does not prove calibration quality, holdout adequacy, "
            "physical probability, operational readiness, or annual frequency."
        ),
    }


def find_calibration_validation_overlaps(
    calibration_records: list[dict[str, Any]],
    validation_records: list[dict[str, Any]],
) -> list[dict[str, str]]:
    overlaps: list[dict[str, str]] = []
    for calibration_record in calibration_records:
        for validation_record in validation_records:
            overlap_keys = ("dataset_id", "event_id", "sample_id")
            if str(validation_record.get("role")) != "holdout_validation":
                overlap_keys = ("dataset_id", "site_id", "event_id", "sample_id")
            shared_keys = [
                key
                for key in overlap_keys
                if calibration_record.get(key) and calibration_record.get(key) == validation_record.get(key)
            ]
            if shared_keys:
                overlaps.append(
                    {
                        "calibration_dataset_id": str(calibration_record.get("dataset_id") or ""),
                        "validation_dataset_id": str(validation_record.get("dataset_id") or ""),
                        "shared_keys": ",".join(shared_keys),
                        "validation_role": str(validation_record.get("role") or ""),
                    }
                )
    return overlaps


def calibration_holdout_next_step(
    status: str,
    missing_reasons: list[str],
    overlaps: list[dict[str, str]],
) -> str:
    if status == "separated_holdout_ready":
        return "Use the separated holdout labels as a boundary check, then acquire stronger field/runout evidence if scientific conclusions need to increase."
    if overlaps:
        first = overlaps[0]
        return (
            "Replace or relabel validation evidence so it does not share "
            f"{first['shared_keys']} with calibration evidence before making stronger conclusions."
        )
    if "missing_explicit_holdout_validation_label" in missing_reasons:
        return "Stage an explicit holdout_validation evidence record before treating validation evidence as independent."
    return "Stage calibration and validation evidence records with explicit roles and no shared event/site/sample identifiers."


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def load_tschamut_calibration_objective_contract(path: Path | None = None) -> dict[str, Any]:
    contract_path = path or DEFAULT_TSCHAMUT_CALIBRATION_OBJECTIVE_CONTRACT
    try:
        contract = load_json(contract_path)
        validate_tschamut_calibration_objective_contract(contract)
    except Exception as exc:
        return {
            "schema_version": "tschamut_calibration_objective_intake_v1",
            "objective_status": "missing_or_invalid",
            "record_path": str(contract_path),
            "missing_or_invalid_reason": str(exc),
        }
    return {
        "schema_version": "tschamut_calibration_objective_intake_v1",
        "objective_status": "executable_smoke_ready",
        "record_path": str(contract_path),
        "experiment_id": str(contract.get("experiment_id") or ""),
        "training_trajectory_count": int((contract.get("training_data") or {}).get("trajectory_count") or 0),
        "excluded_holdout_trajectory_count": int(
            (contract.get("excluded_holdout_data") or {}).get("trajectory_count") or 0
        ),
        "candidate_count": int((contract.get("parameters") or {}).get("candidate_count") or 0),
        "metrics": [str(item) for item in contract.get("metrics", [])],
        "expected_output_artifacts": contract.get("expected_output_artifacts") or {},
        "claim_boundary": contract.get("claim_boundary") or {},
    }


def validate_tschamut_calibration_objective_contract(contract: dict[str, Any]) -> None:
    require(contract.get("schema_version") == "tschamut_calibration_objective_v1", "calibration objective schema mismatch")
    require(contract.get("objective_status") == "executable_smoke_ready", "calibration objective is not executable_smoke_ready")
    training = contract.get("training_data")
    holdout = contract.get("excluded_holdout_data")
    require(isinstance(training, dict), "training_data must be a mapping")
    require(isinstance(holdout, dict), "excluded_holdout_data must be a mapping")
    require(int(training.get("trajectory_count") or 0) > 0, "training trajectory_count must be positive")
    require(int(holdout.get("trajectory_count") or 0) > 0, "holdout trajectory_count must be positive")
    require(holdout.get("use_for_fitting") is False, "excluded holdout data must not be used for fitting")
    require(isinstance(contract.get("metrics"), list) and contract["metrics"], "metrics must be nonempty")
    require(int((contract.get("parameters") or {}).get("candidate_count") or 0) > 0, "candidate_count must be positive")
    outputs = contract.get("expected_output_artifacts")
    require(isinstance(outputs, dict) and outputs, "expected_output_artifacts must be a mapping")
    boundary = contract.get("claim_boundary")
    require(isinstance(boundary, dict), "claim_boundary must be a mapping")
    for field in (
        "calibration_claim_supported",
        "validation_acceptance_claimed",
        "physical_probability_supported",
        "annual_frequency_supported",
        "operational_hazard_map_supported",
        "selected_parameters_promoted_to_validation",
    ):
        require(boundary.get(field) is False, f"calibration objective {field} must be false")


def assess_candidate_portability(candidate_manifest: dict[str, Any]) -> dict[str, Any]:
    candidate_site_id = str(candidate_manifest.get("candidate_site_id") or "unspecified_second_site").strip()
    candidate_site_name = str(candidate_manifest.get("candidate_site_name") or "unspecified").strip()
    site_extent = candidate_manifest.get("site_extent") if isinstance(candidate_manifest.get("site_extent"), dict) else {}

    required_path_items = {
        "terrain_crop": candidate_manifest.get("expected_terrain_crop_path"),
        "terrain_metadata": candidate_manifest.get("expected_terrain_metadata_path"),
        "source_zone_metadata": candidate_manifest.get("expected_source_zone_metadata_path"),
        "scenario_table": candidate_manifest.get("expected_scenario_table_path"),
        "source_scenario_policy": candidate_manifest.get("expected_source_scenario_policy_path"),
        "swissimage_context": candidate_manifest.get("expected_swissimage_context_root"),
        "swisstlm3d_context": candidate_manifest.get("expected_swisstlm3d_context_root"),
        "swisstlm3d_metadata": candidate_manifest.get("expected_swisstlm3d_metadata_path"),
        "swisssurface3d_context": candidate_manifest.get("expected_swisssurface3d_context_root"),
        "swisssurface3d_raster_context": candidate_manifest.get("expected_swisssurface3d_raster_context_root"),
        "swissbuildings3d_context": candidate_manifest.get("expected_swissbuildings3d_context_root"),
        "validation_case_root": candidate_manifest.get("expected_validation_private_root"),
        "hazard_results_root": candidate_manifest.get("expected_hazard_results_root"),
        "processed_input_root": candidate_manifest.get("expected_processed_input_root"),
        "processed_context_root": candidate_manifest.get("expected_processed_context_root"),
    }
    resolved_required_paths: dict[str, Path] = {}
    missing_input_categories: list[str] = []
    missing_input_paths_or_patterns: list[str] = []
    for category, raw_path in required_path_items.items():
        path_text = str(raw_path or "").strip()
        if not path_text:
            missing_input_categories.append(category)
            missing_input_paths_or_patterns.append(f"<missing:{category}>")
            continue
        path = ROOT / path_text if not Path(path_text).is_absolute() else Path(path_text)
        resolved_required_paths[category] = path
    missing_input_paths_or_patterns.extend(shared_missing_repo_paths(resolved_required_paths))
    for category, path in resolved_required_paths.items():
        if not path.exists():
            missing_input_categories.append(category)

    if not all(
        part in site_extent and site_extent.get(part) not in (None, "")
        for part in ("crs", "xmin", "ymin", "xmax", "ymax")
    ):
        missing_input_categories.append("site_extent_definition")
        missing_input_paths_or_patterns.append("site_extent.crs + site_extent.xmin/ymin/xmax/ymax")

    status = "ready" if not missing_input_categories else "blocked_missing_inputs"
    return {
        "candidate_site": {
            "candidate_site_id": candidate_site_id,
            "candidate_site_name": candidate_site_name,
            "site_extent": site_extent,
            "candidate_selection_rationale": candidate_manifest.get("candidate_selection_rationale", ""),
            "source_zone_scenario_contract": candidate_manifest.get("source_zone_scenario_contract", {}),
        },
        "second_site_portability_status": status,
        "candidate_manifest_status": "staged_candidate_manifest" if candidate_manifest else "missing_candidate_manifest",
        "missing_input_categories": missing_input_categories,
        "missing_input_paths_or_patterns": missing_input_paths_or_patterns,
    }


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


def source_documents() -> list[str]:
    return [
        "docs/task_backlog.md",
        "docs/agent_work_log.md",
        "docs/tschamut_public_conditional_pilot_gate_report.md",
        "docs/tschamut_public_same_scale_uncertainty_envelope.md",
        "docs/public_real_site_geodata_preparation.md",
        "docs/swisstopo_data_strategy.md",
        "data/datasets.yaml",
        "data/processed/swisstopo/tschamut_public_pilot_manifest.yaml",
        "validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml",
        "validation/pilot_runs/tschamut_public_scalable_conditional_target_gate_v1.yaml",
        "validation/pilot_runs/tschamut_public_balfrin_readiness_v1.yaml",
        "validation/pilot_runs/tschamut_public_balfrin_target_gate_reproduction_v1.yaml",
        "validation/cases/chant_sura_contact.yaml",
        "validation/cases/chant_sura_contact_heldout.yaml",
        "validation/internal/shape_contact_v0_chant_sura_model_selection.yaml",
        "validation/data/processed/chant_sura_2020/metadata_contact_split.json",
        "validation/data/processed/chant_sura_2020/holdout_validation_evidence_manifest.json",
        "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml",
        "scripts/summarize_chant_sura_holdout_evidence.py",
    ]


def dataset_summary(datasets: dict[str, dict[str, Any]], dataset_id: str) -> dict[str, Any]:
    entry = datasets.get(dataset_id, {})
    return {
        "dataset_id": dataset_id,
        "name": entry.get("name", ""),
        "intended_validation_use": entry.get("intended_validation_use") or [],
        "download_status": entry.get("download_status", ""),
    }


def observed_deposition_gap(
    datasets: dict[str, dict[str, Any]],
    tschamut_manifest: dict[str, Any],
    tschamut_gate: dict[str, Any],
    chant_contact: dict[str, Any],
    chant_contact_heldout: dict[str, Any],
    observed_intake_report: dict[str, Any],
) -> dict[str, Any]:
    intake_status = str(observed_intake_report.get("observed_runout_deposition_intake_status") or "missing")
    intake_ready = intake_status == "ready"
    current = {
        "category": "observed_deposition_runout_evidence",
        "classification": "present" if intake_ready else "partial",
        "first_missing_input": "" if intake_ready else "independent_observed_runout_deposition_benchmark",
        "current_evidence": [
            dataset_summary(datasets, "tschamut2014"),
            "Tschamut gate freeze records observed deposition / runout metrics and deterministic release sampling",
            "Chant Sura contact fixtures record trajectory/contact metrics and a held-out contact subset",
            observed_intake_report.get("real_input_intake_report", {}),
        ],
        "what_exists": [
            tschamut_manifest.get("selected_domain", {}).get("name", ""),
            tschamut_gate.get("workflow_gates", {}).get("report_classification", ""),
            chant_contact.get("case_id", ""),
            chant_contact_heldout.get("case_id", ""),
        ],
        "what_is_missing": [
            "Independent holdout field or benchmark deposition/runout data not used in the current diagnostic selection",
            "A physical-credibility benchmark separate from the current diagnostic Tschamut evidence",
        ] if not intake_ready else [
            "Deposition-footprint polygon evidence beyond the staged runout-axis proxy",
            "A production-grade field benchmark before operational use",
        ],
        "minimum_additional_evidence_needed": (
            "A held-out field or benchmark deposition/runout dataset with explicit provenance, spatial reference, "
            "and comparison metrics that is not used to fit the model."
        ) if not intake_ready else (
            "Observed runout-axis intake is staged for design review; full deposition footprint and production "
            "acceptance remain separate future evidence."
        ),
        "support_role": "diagnostic_QA_only",
        "claim_boundary": "diagnostic_QA_only",
        "physical_probability_relevance": "present" if intake_ready else "partial",
        "holdout_validation_relevance": "present" if intake_ready else "partial",
    }
    return current


def release_zone_gap(
    datasets: dict[str, dict[str, Any]],
    tschamut_manifest: dict[str, Any],
    candidate_portability: dict[str, Any],
    block_release_probability_intake: dict[str, Any],
) -> dict[str, Any]:
    intake_classification = str(block_release_probability_intake.get("intake_classification") or "missing")
    candidate_present = intake_classification == "present"
    return {
        "category": "release_zone_evidence",
        "classification": "present" if candidate_present else "partial",
        "first_missing_input": "" if candidate_present else "site_specific_release_zone_geometry_package",
        "acquisition_blockers": [] if candidate_present else [
            {
                "blocker_id": "site_specific_release_zone_geometry_missing",
                "first_missing_input": "site_specific_release_zone_geometry_package",
                "missing_inputs": [
                    "field_reconnaissance_release_geometry",
                    "release_zone_geometry_provenance_uri",
                    "release_zone_geometry_crs_and_vertical_datum",
                ],
                "blocked_claims": ["physical_probability", "annual_frequency"],
            }
        ],
        "future_gate_prerequisites": [
            {
                "gate_id": "physical_release_zone_provenance_phase_gate",
                "prerequisite_id": "accepted_site_specific_release_zone_geometry_package",
                "summary": (
                    "Field-supported release-zone provenance must be accepted before any physical-probability bridge is considered."
                ),
            }
        ],
        "current_evidence": [
            dataset_summary(datasets, "tschamut2014"),
            tschamut_manifest.get("selected_domain", {}),
            candidate_portability["candidate_site"],
            block_release_probability_intake,
        ],
        "what_exists": [
            "Tschamut source-zone metadata and policy are frozen and deterministic",
            "Release-zone provenance intake bridge labels workflow_generated, field_supported, mixed_provenance, and blocked_missing_provenance records without converting sampling weights into probabilities",
            "The candidate Chant Sura / Flüelapass manifest declares a source-zone contract shape",
            "A Tschamut public block/release probability candidate is staged for design review from observed release-point inventory counts",
        ],
        "what_is_missing": [] if candidate_present else [
            "A second-site release-zone geometry with staged public geodata and provenance",
            "Independent field justification that can be tested against holdout data",
        ],
        "minimum_additional_evidence_needed": (
            "The staged candidate is enough to make the release-probability evidence class inspectable for design review; "
            "block-population evidence, calibration evidence, and final review remain separate blockers."
            if candidate_present
            else "A field-supported site-specific release-zone geometry package with documented derivation rules and "
            "comparison data that can be validated independently of the current pilot."
        ),
        "support_role": "design_review_candidate_only" if candidate_present else "diagnostic_and_portability_only",
        "claim_boundary": "conditional_diagnostic_only",
        "physical_probability_relevance": "present" if candidate_present else "partial",
        "holdout_validation_relevance": "partial",
    }


def block_population_gap(
    datasets: dict[str, dict[str, Any]],
    tschamut_gate: dict[str, Any],
    chant_model_selection: dict[str, Any],
    block_population_intake: dict[str, Any],
) -> dict[str, Any]:
    intake_classification = str(block_population_intake.get("intake_classification") or "missing")
    candidate_present = intake_classification == "present"
    return {
        "category": "block_size_and_block_population_evidence",
        "classification": "present" if candidate_present else "missing",
        "first_missing_input": "" if candidate_present else "block_size_survey_or_photogrammetry_census",
        "acquisition_blockers": [] if candidate_present else [dict(item) for item in BLOCK_POPULATION_ACQUISITION_BLOCKERS],
        "future_gate_prerequisites": [dict(item) for item in BLOCK_POPULATION_FUTURE_GATE_PREREQUISITES],
        "current_evidence": [
            dataset_summary(datasets, "tschamut2014"),
            dataset_summary(datasets, "chant_sura_2020"),
            tschamut_gate.get("sampling_plan", {}),
            chant_model_selection.get("shape_source", {}),
            block_population_intake,
        ],
        "what_exists": [
            "Tschamut uses conditional sampling only",
            "Chant Sura contact fixtures carry block mass / radius and shape proxies for contact comparisons",
            "Conditional scenario weights remain conditional only and are not frequency evidence",
            "A Tschamut public block-population candidate is staged for design review from processed block metadata",
        ],
        "what_is_missing": [] if candidate_present else [
            "A block-size survey or photogrammetry census with survey-frame provenance",
            "A block-count or size-class record that is separate from source-frequency catalogues",
            "A benchmark that explicitly separates representative scenarios from population semantics",
        ],
        "minimum_additional_evidence_needed": (
            "The staged candidate is enough to make block-population evidence inspectable for design review; calibration evidence and final review remain separate blockers."
            if candidate_present
            else "Observed block-population evidence with survey provenance, block counts or size classes, and an explicit "
            "boundary showing the record is not a source-frequency catalogue before any physical probability claim."
        ),
        "support_role": "design_review_candidate_only" if candidate_present else "conditional_scenario_only",
        "claim_boundary": "conditional_only",
        "physical_probability_relevance": "present" if candidate_present else "missing",
        "holdout_validation_relevance": "missing",
    }


def source_frequency_gap(
    datasets: dict[str, dict[str, Any]],
    tschamut_gate: dict[str, Any],
    chant_model_selection: dict[str, Any],
    source_frequency_intake: dict[str, Any],
) -> dict[str, Any]:
    intake_classification = str(source_frequency_intake.get("intake_classification") or "missing")
    classification = {
        "accepted": "present",
        "partial": "partial",
        "missing": "missing",
    }.get(intake_classification, "missing")
    first_missing_input = "" if classification == "present" else "historical_rockfall_event_catalogue"
    what_exists = [
        "Conditional scenario rows exist, but they remain workflow outputs rather than occurrence catalogues",
        "Current sampling weights are conditional design weights only and are not frequency evidence",
    ]
    if classification == "present":
        what_exists.append(
            "A source-frequency evidence record is accepted for design review with explicit non-production status."
        )
    elif classification == "partial":
        what_exists.append("A candidate source-frequency evidence record exists, but it is not accepted.")
    return {
        "category": "source_frequency_and_temporal_frequency_evidence",
        "classification": classification,
        "first_missing_input": first_missing_input,
        "acquisition_blockers": [dict(item) for item in SOURCE_FREQUENCY_ACQUISITION_BLOCKERS],
        "future_gate_prerequisites": [dict(item) for item in SOURCE_FREQUENCY_FUTURE_GATE_PREREQUISITES],
        "conditional_sampling_weights_are_not_frequency_evidence": True,
        "intake_summary": source_frequency_intake,
        "current_evidence": [
            "Current scenario tables remain conditional and proxy-driven.",
            "Sampling weights are conditional design weights only and are not source-occurrence rates.",
            source_frequency_intake,
            dataset_summary(datasets, "tschamut2014"),
            dataset_summary(datasets, "chant_sura_2020"),
            tschamut_gate.get("sampling_plan", {}),
            chant_model_selection.get("shape_source", {}),
        ],
        "what_exists": what_exists,
        "what_is_missing": [
            "Historical rockfall event catalogue with provenance and observation windows",
            "Repeat source-zone observations with censoring rules and a temporal window",
            "A source-occurrence record that supports frequency semantics instead of conditional sampling",
        ] if classification != "present" else [
            "Real-site acceptance beyond the design-review fixture",
            "Connection from accepted source-frequency evidence to release-probability and block-population evidence",
        ],
        "minimum_additional_evidence_needed": (
            "Observed source-occurrence evidence with explicit time windows, censoring rules, and provenance, kept "
            "separate from conditional sampling weights before any physical probability claim."
        ) if classification != "present" else (
            "The source-frequency class is satisfied for this assessment input; the next physical-probability blockers "
            "are release-probability, block-population, calibration, and holdout evidence."
        ),
        "support_role": "conditional_scenario_only",
        "claim_boundary": "conditional_only",
        "physical_probability_relevance": classification,
        "holdout_validation_relevance": "missing",
    }


def terrain_context_gap(
    tschamut_manifest: dict[str, Any],
    tschamut_gate: dict[str, Any],
    tschamut_target: dict[str, Any],
    candidate_portability: dict[str, Any],
) -> dict[str, Any]:
    return {
        "category": "terrain_and_context_evidence",
        "classification": "partial",
        "current_evidence": [
            tschamut_manifest.get("selected_domain", {}),
            tschamut_gate.get("hazard_output_plan", {}),
            tschamut_target.get("target_execution_plan", {}),
            candidate_portability["second_site_portability_status"],
        ],
        "what_exists": [
            "Tschamut terrain provenance, extent, resolution, and nodata metadata are committed",
            "Same-scale context evidence and GIS/COG readiness have been audited",
            "Second-site portability manifests the missing terrain and context paths for Chant Sura / Flüelapass",
        ],
        "what_is_missing": [
            "A second-site staged terrain crop and context product set",
            "An independent site-specific validation that turns context into a predictive rather than diagnostic claim",
        ],
        "minimum_additional_evidence_needed": (
            "Staged site-specific terrain and context products, with provenance and resolution metadata, plus an "
            "independent benchmark that tests the context interpretation rather than only recording it."
        ),
        "support_role": "interpretation_limiter",
        "claim_boundary": "context_limited_diagnostic_only",
        "physical_probability_relevance": "partial",
        "holdout_validation_relevance": "partial",
    }


def calibration_gap(
    tschamut_manifest: dict[str, Any],
    tschamut_gate: dict[str, Any],
    chant_contact: dict[str, Any],
    chant_contact_heldout: dict[str, Any],
    chant_model_selection: dict[str, Any],
    calibration_objective_contract: dict[str, Any],
) -> dict[str, Any]:
    objective_ready = calibration_objective_contract.get("objective_status") == "executable_smoke_ready"
    return {
        "category": "calibration_evidence",
        "classification": "partial" if objective_ready else "missing",
        "current_evidence": [
            tschamut_manifest.get("claim_boundary", {}),
            tschamut_gate.get("physics_freeze", {}),
            chant_contact.get("expected", {}).get("metrics", []),
            chant_contact_heldout.get("expected", {}).get("metrics", []),
            chant_model_selection.get("frozen_reference_metrics", {}),
            calibration_objective_contract,
        ],
        "what_exists": [
            "Current pilot evidence is explicitly non-tuning and non-operational",
            "Chant Sura contact fixtures support model comparison and shape sensitivity only",
            (
                "The Tschamut calibration objective names its training partition, excluded holdout partition, "
                "parameter grid, metrics, and expected artifacts"
                if objective_ready
                else "No executable calibration objective contract is staged"
            ),
        ],
        "what_is_missing": [
            (
                "A completed calibration smoke or fit record from the staged objective"
                if objective_ready
                else "A calibration dataset with a documented objective function and parameter bounds"
            ),
            (
                "A post-fit comparison that keeps the excluded holdout partition out of fitting"
                if objective_ready
                else "A holdout split reserved for post-fit validation"
            ),
            "A statement that current Tschamut outputs are calibrated evidence",
        ],
        "minimum_additional_evidence_needed": (
            "Run the staged calibration objective in smoke mode, record candidate sensitivity and fitted values, "
            "and keep the excluded holdout partition out of fitting."
            if objective_ready
            else "A calibration record that names the calibration dataset, objective function, parameter bounds, "
            "fitted values, and a separate holdout validation dataset."
        ),
        "support_role": "objective_defined_pending_smoke" if objective_ready else "not_calibrated",
        "claim_boundary": "calibration_objective_only_not_validation_evidence"
        if objective_ready
        else "calibration_out_of_scope_for_current_pilot",
        "physical_probability_relevance": "partial" if objective_ready else "missing",
        "holdout_validation_relevance": "partial" if objective_ready else "missing",
    }


def holdout_gap(
    tschamut_gate: dict[str, Any],
    tschamut_target: dict[str, Any],
    chant_contact_heldout: dict[str, Any],
    chant_split: dict[str, Any],
    balfrin_readiness: dict[str, Any],
    balfrin_reproduction: dict[str, Any],
    observed_intake_report: dict[str, Any],
    validation_leakage_guardrails: dict[str, Any],
    calibration_holdout_separation: dict[str, Any],
) -> dict[str, Any]:
    intake_ready = observed_intake_report.get("observed_runout_deposition_intake_status") == "ready"
    leakage_clear = validation_leakage_guardrails.get("guardrail_status") == "passed"
    separation_clear = calibration_holdout_separation.get("separation_status") == "separated_holdout_ready"
    classification = "present" if intake_ready and leakage_clear and separation_clear else "partial"
    return {
        "category": "holdout_and_validation_evidence",
        "classification": classification,
        "first_missing_input": "" if classification == "present" else "independent_holdout_benchmark",
        "current_evidence": [
            tschamut_gate.get("workflow_gates", {}),
            tschamut_target.get("evidence_result", {}),
            chant_contact_heldout.get("report", {}),
            chant_split,
            balfrin_readiness.get("readiness_status", ""),
            balfrin_reproduction.get("evidence_result", {}).get("interpretation", ""),
            observed_intake_report.get("real_input_intake_report", {}),
            validation_leakage_guardrails,
            calibration_holdout_separation,
        ],
        "what_exists": [
            "Tschamut diagnostic validation and same-scale comparisons are measured",
            "Chant Sura includes held-out contact fixture metadata",
            "Balfrin execution evidence shows local job sufficiency, not field validation",
        ] + (
            ["A separated Chant Sura held-out runout-axis benchmark intake is staged for design review"]
            if classification == "present"
            else []
        ),
        "what_is_missing": [
            "An independent holdout benchmark that is not part of the current diagnostic or model-selection fixtures",
            "Field evidence reserved for predictive credibility rather than replaying diagnostic data",
        ] if classification != "present" else [
            "Full deposition-footprint scoring evidence",
            "Post-calibration validation once calibration evidence exists",
        ],
        "minimum_additional_evidence_needed": (
            "A reserved holdout dataset with site provenance, explicit split rules, and a scoring protocol that does "
            "not reuse the same data for selection."
        ) if classification != "present" else (
            "The independent holdout class is satisfied for this design-review assessment; remaining validation work "
            "is calibration-linked scoring and full deposition-footprint evidence."
        ),
        "support_role": "diagnostic_validation_only",
        "claim_boundary": "diagnostic_validation_not_holdout_credibility",
        "physical_probability_relevance": classification,
        "holdout_validation_relevance": classification,
    }


def transfer_gap(
    candidate_manifest: dict[str, Any],
    candidate_portability: dict[str, Any],
    chant_contact: dict[str, Any],
    chant_contact_heldout: dict[str, Any],
    balfrin_readiness: dict[str, Any],
) -> dict[str, Any]:
    return {
        "category": "multi_site_transfer_evidence",
        "classification": "partial",
        "current_evidence": [
            candidate_manifest.get("candidate_site_name", ""),
            candidate_portability["missing_input_categories"],
            chant_contact.get("references", {}).get("dataset", ""),
            chant_contact_heldout.get("case_id", ""),
            balfrin_readiness.get("readiness_status", ""),
        ],
        "what_exists": [
            "A concrete Chant Sura / Flüelapass candidate manifest exists",
            "Portable command-plan and multisite source/scenario contract helpers exist",
            "Balfrin runtime evidence shows the current single-job path is sufficient",
        ],
        "what_is_missing": [
            "Staged second-site public geodata for Chant Sura / Flüelapass",
            "Any direct Schiers validation fixture surfaced in the current checkout",
            "Any field/benchmark evidence proving portability beyond Tschamut",
        ],
        "minimum_additional_evidence_needed": (
            "At least one staged second-site public-geodata package with matching terrain, source-zone, scenario, and "
            "context inputs, plus an independent validation or holdout benchmark."
        ),
        "support_role": "portability_only",
        "claim_boundary": "portability_not_physical_credibility",
        "physical_probability_relevance": "partial",
        "holdout_validation_relevance": "partial",
    }


def derive_physical_credibility_status(evidence_gap_categories: list[dict[str, Any]]) -> str:
    labels = {entry["category"]: entry["classification"] for entry in evidence_gap_categories}
    if labels.get("calibration_evidence") == "present" and labels.get("holdout_and_validation_evidence") == "present":
        return "established"
    if labels.get("calibration_evidence") != "present" or labels.get("holdout_and_validation_evidence") in {"missing", "partial"}:
        return "not_established"
    return "partial"


def safe_denominator_audit() -> dict[str, Any]:
    try:
        return denominator_provenance.build_report()
    except Exception as exc:  # pragma: no cover - depends on ignored local artifacts.
        return {
            "schema_version": denominator_provenance.SCHEMA_VERSION,
            "audit_status": "blocked_missing_local_artifacts",
            "missing_evidence": [str(exc)],
            "claim_boundaries": {
                "annual_frequency_claims_allowed": False,
                "physical_probability_claims_allowed": False,
                "operational_claims_allowed": False,
                "risk_exposure_vulnerability_claims_allowed": False,
                "source_frequency_inferred": False,
                "balfrin_required": False,
            },
        }


def safe_deposition_traceability_audit() -> dict[str, Any]:
    try:
        return deposition_traceability.build_report()
    except Exception as exc:  # pragma: no cover - depends on ignored local artifacts.
        return {
            "schema_version": deposition_traceability.SCHEMA_VERSION,
            "audit_status": "blocked_missing_local_artifacts",
            "missing_or_failed_checks": [str(exc)],
            "claim_boundaries": {
                "field_validation_claim_added": False,
                "calibration_claim_added": False,
                "operational_map_claim_added": False,
                "physical_probability_claim_added": False,
                "balfrin_required": False,
            },
        }


def safe_observed_runout_deposition_intake() -> dict[str, Any]:
    missing_inputs = [
        str(path)
        for path in (
            DEFAULT_OBSERVED_RUNOUT_DEPOSITION_BENCHMARK_MANIFEST,
            DEFAULT_OBSERVED_RUNOUT_DEPOSITION_BENCHMARK_GEOMETRY,
        )
        if not path.exists()
    ]
    if missing_inputs:
        return {
            "schema_version": "observed_runout_deposition_intake_summary_v1",
            "observed_runout_deposition_intake_status": "blocked_missing_inputs",
            "missing_inputs": missing_inputs,
            "real_input_intake_report": {
                "real_input_intake_status": "blocked_missing_inputs",
                "blocking_reasons": ["missing_observed_runout_deposition_benchmark"],
            },
        }
    try:
        manifest = load_json(DEFAULT_OBSERVED_RUNOUT_DEPOSITION_BENCHMARK_MANIFEST)
        geometry = load_json(DEFAULT_OBSERVED_RUNOUT_DEPOSITION_BENCHMARK_GEOMETRY)
    except Exception as exc:  # pragma: no cover - depends on optional staged evidence.
        return {
            "schema_version": "observed_runout_deposition_intake_summary_v1",
            "observed_runout_deposition_intake_status": "blocked_schema_gap",
            "blocked_reason": str(exc),
            "real_input_intake_report": {
                "real_input_intake_status": "blocked_schema_gap",
                "blocking_reasons": [str(exc)],
            },
        }
    required_manifest_sections = ("geometry", "provenance", "uncertainty", "calibration_validation_role", "license")
    missing_sections = [section for section in required_manifest_sections if not isinstance(manifest.get(section), dict)]
    role = manifest.get("calibration_validation_role") if isinstance(manifest.get("calibration_validation_role"), dict) else {}
    role_ready = (
        role.get("calibration") == "not_allowed"
        and role.get("validation") == "benchmark_intake_only"
        and manifest.get("holdout_eligibility") is False
    )
    status = "ready" if not missing_sections and role_ready and geometry else "blocked_schema_gap"
    return {
        "schema_version": "observed_runout_deposition_intake_summary_v1",
        "observed_runout_deposition_intake_status": status,
        "manifest_path": str(DEFAULT_OBSERVED_RUNOUT_DEPOSITION_BENCHMARK_MANIFEST),
        "geometry_path": str(DEFAULT_OBSERVED_RUNOUT_DEPOSITION_BENCHMARK_GEOMETRY),
        "dataset_id": manifest.get("dataset_id", ""),
        "geometry_id": (manifest.get("geometry") or {}).get("geometry_id", ""),
        "split": manifest.get("split", {}),
        "missing_sections": missing_sections,
        "real_input_intake_report": {
            "real_input_intake_status": status,
            "blocking_reasons": [] if status == "ready" else ["observed_runout_deposition_benchmark_schema_gap"],
            "manifest_path": str(DEFAULT_OBSERVED_RUNOUT_DEPOSITION_BENCHMARK_MANIFEST),
            "geometry_path": str(DEFAULT_OBSERVED_RUNOUT_DEPOSITION_BENCHMARK_GEOMETRY),
        },
    }


def load_source_frequency_intake(path: Path | None = None) -> dict[str, Any]:
    record_path = path or DEFAULT_SOURCE_FREQUENCY_EVIDENCE_PATH
    try:
        summary = source_frequency_evidence.validate_source_frequency_evidence(record_path)
    except Exception as exc:
        return {
            "schema_version": "source_frequency_intake_summary_v1",
            "record_path": str(record_path),
            "record_status": "invalid_or_missing",
            "intake_classification": "missing",
            "source_event_rate_available": False,
            "non_production_status": "invalid_or_missing",
            "missing_or_invalid_reason": str(exc),
            "claim_boundary": {
                "annual_frequency_supported": False,
                "physical_probability_supported": False,
                "operational_hazard_map_supported": False,
            },
        }
    return {
        "schema_version": "source_frequency_intake_summary_v1",
        "record_path": str(record_path),
        **summary,
        "claim_boundary": {
            "annual_frequency_supported": False,
            "physical_probability_supported": False,
            "operational_hazard_map_supported": False,
        },
    }


def load_block_release_probability_intake(path: Path | None = None) -> dict[str, Any]:
    record_path = path or DEFAULT_BLOCK_RELEASE_PROBABILITY_EVIDENCE_PATH
    try:
        summary = block_release_probability_evidence.validate_block_release_probability_evidence(record_path)
    except Exception as exc:
        return {
            "schema_version": "block_release_probability_intake_summary_v1",
            "record_path": str(record_path),
            "record_status": "invalid_or_missing",
            "intake_classification": "missing",
            "missing_or_invalid_reason": str(exc),
            "block_scenario_count": 0,
            "release_cell_count": 0,
            "claim_boundary": {
                "annual_frequency_supported": False,
                "physical_probability_supported": False,
                "operational_hazard_map_supported": False,
            },
        }
    record_status = str(summary.get("record_status") or "")
    intake_classification = (
        "present"
        if record_status == "accepted_for_design_review"
        else "partial"
        if record_status == "candidate_not_authorized"
        else "missing"
    )
    return {
        "schema_version": "block_release_probability_intake_summary_v1",
        "record_path": str(record_path),
        "intake_classification": intake_classification,
        **summary,
        "claim_boundary": {
            "annual_frequency_supported": False,
            "physical_probability_supported": False,
            "operational_hazard_map_supported": False,
        },
    }


def load_block_population_intake(path: Path | None = None) -> dict[str, Any]:
    record_path = path or DEFAULT_BLOCK_POPULATION_EVIDENCE_PATH
    try:
        summary = validate_block_population_evidence_record(record_path)
    except Exception as exc:
        return {
            "schema_version": "block_population_intake_summary_v1",
            "record_path": str(record_path),
            "record_status": "invalid_or_missing",
            "intake_classification": "missing",
            "missing_or_invalid_reason": str(exc),
            "block_population_class_count": 0,
            "total_count": 0,
            "claim_boundary": {
                "annual_frequency_supported": False,
                "physical_probability_supported": False,
                "operational_hazard_map_supported": False,
            },
        }
    return {
        "schema_version": "block_population_intake_summary_v1",
        "record_path": str(record_path),
        "intake_classification": "present",
        **summary,
        "claim_boundary": {
            "annual_frequency_supported": False,
            "physical_probability_supported": False,
            "operational_hazard_map_supported": False,
        },
    }


def validate_block_population_evidence_record(record_path: Path) -> dict[str, Any]:
    record = load_yaml(record_path)
    require(record.get("schema_version") == "block_population_evidence_v1", "block population schema mismatch")
    require(str(record.get("record_status") or "") == "accepted_for_design_review", "block population candidate must be accepted_for_design_review")
    require(record.get("prototype_authorized") is False, "block population prototype_authorized must be false")
    require(record.get("operational_status") == "research_diagnostic", "block population operational_status must be research_diagnostic")
    distribution = record.get("block_population_distribution")
    require(isinstance(distribution, dict), "block_population_distribution must be a mapping")
    classes = distribution.get("classes")
    require(isinstance(classes, list) and classes, "block population classes must be nonempty")
    total_count = distribution.get("total_count")
    require(isinstance(total_count, int | float) and int(total_count) > 0, "block population total_count must be positive")
    probability_sum = 0.0
    counted = 0
    seen: set[str] = set()
    for index, item in enumerate(classes):
        require(isinstance(item, dict), f"block population class {index} must be a mapping")
        class_id = str(item.get("block_population_class_id") or "")
        require(class_id, f"block population class {index} requires block_population_class_id")
        require(class_id not in seen, f"duplicate block population class id: {class_id}")
        seen.add(class_id)
        count = item.get("count")
        require(isinstance(count, int | float) and int(count) > 0, f"{class_id}.count must be positive")
        counted += int(count)
        probability = item.get("probability")
        require(isinstance(probability, int | float) and float(probability) > 0, f"{class_id}.probability must be positive")
        probability_sum += float(probability)
        require(str(item.get("evidence_basis") or ""), f"{class_id}.evidence_basis is required")
    require(counted == int(total_count), "block population class counts must equal total_count")
    require(abs(probability_sum - 1.0) <= 1e-9, "block population probabilities must sum to 1.0")
    claim_boundary = record.get("claim_boundary")
    require(isinstance(claim_boundary, dict), "block population claim_boundary must be a mapping")
    for field in (
        "annual_frequency_supported",
        "physical_probability_supported",
        "return_period_supported",
        "operational_hazard_map_supported",
        "risk_or_exposure_supported",
    ):
        require(claim_boundary.get(field) is False, f"block population {field} must be false")
    return {
        "record_id": str(record.get("record_id") or ""),
        "record_status": str(record.get("record_status") or ""),
        "source_zone_id": str(record.get("source_zone_id") or ""),
        "block_population_class_count": len(classes),
        "total_count": int(total_count),
        "prototype_authorized": False,
    }


def build_physical_probability_readiness_check(
    evidence_gap_categories: list[dict[str, Any]],
    *,
    denominator_audit: dict[str, Any] | None = None,
    traceability_audit: dict[str, Any] | None = None,
) -> dict[str, Any]:
    category_status = {entry["category"]: entry["classification"] for entry in evidence_gap_categories}
    category_first_missing = {
        entry["category"]: entry.get("first_missing_input", "unspecified_missing_input")
        for entry in evidence_gap_categories
    }
    denominator_status = (
        str((denominator_audit or {}).get("audit_status") or "not_checked")
    )
    traceability_status = (
        str((traceability_audit or {}).get("audit_status") or "not_checked")
    )

    evidence_checks = []
    for requirement in PHYSICAL_PROBABILITY_EVIDENCE_REQUIREMENTS:
        source_category = str(requirement["source_category"])
        if source_category == "conditional_denominator_audit":
            current_status = denominator_status
            first_missing = "; ".join(str(item) for item in (denominator_audit or {}).get("missing_evidence", []))
        elif source_category == "trajectory_deposition_traceability_audit":
            current_status = traceability_status
            first_missing = "; ".join(
                str(item) for item in (traceability_audit or {}).get("missing_or_failed_checks", [])
            )
        else:
            current_status = str(category_status.get(source_category, "missing"))
            first_missing = str(category_first_missing.get(source_category, "unspecified_missing_input"))

        required_status = str(requirement["required_status"])
        passed = current_status == required_status
        evidence_checks.append(
            {
                "evidence_class": requirement["evidence_class"],
                "source_category": source_category,
                "required_status": required_status,
                "current_status": current_status,
                "check_status": "pass" if passed else "fail",
                "first_missing_input": "" if passed else first_missing,
                "pass_criteria": list(requirement["pass_criteria"]),
                "failure_modes": list(requirement["failure_modes"]),
            }
        )

    failing = [item for item in evidence_checks if item["check_status"] != "pass"]
    passed_count = len(evidence_checks) - len(failing)
    if not failing:
        readiness_status = "ready_for_physical_probability_product"
    elif passed_count:
        readiness_status = "partial_evidence_missing_critical_inputs"
    else:
        readiness_status = "blocked_missing_required_evidence"

    return {
        "schema_version": "physical_probability_readiness_check_v1",
        "readiness_status": readiness_status,
        "physical_probability_claims_allowed": not failing,
        "annual_frequency_claims_allowed": False,
        "required_evidence_count": len(evidence_checks),
        "passing_evidence_count": passed_count,
        "failing_evidence_classes": [item["evidence_class"] for item in failing],
        "first_blocking_evidence_class": failing[0]["evidence_class"] if failing else "",
        "evidence_checks": evidence_checks,
        "supporting_audits": {
            "conditional_denominator_provenance": denominator_status,
            "trajectory_deposition_traceability": traceability_status,
        },
        "boundary_note": (
            "This check is necessary but not sufficient for an operational or annual-frequency product. "
            "It only says whether the physical-probability evidence classes are staged and internally checkable."
        ),
    }


def site_reference_evidence(
    datasets: dict[str, dict[str, Any]],
    tschamut_manifest: dict[str, Any],
    tschamut_gate: dict[str, Any],
    tschamut_target: dict[str, Any],
    chant_contact: dict[str, Any],
    chant_contact_heldout: dict[str, Any],
    chant_model_selection: dict[str, Any],
    chant_split: dict[str, Any],
    balfrin_readiness: dict[str, Any],
    balfrin_reproduction: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        {
            "site": "Tschamut",
            "classification": "partial",
            "role": "diagnostic deposition/runout benchmark",
            "evidence_sources": [
                "data/datasets.yaml:tschamut2014",
                "data/processed/swisstopo/tschamut_public_pilot_manifest.yaml",
                "validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml",
                "validation/pilot_runs/tschamut_public_scalable_conditional_target_gate_v1.yaml",
            ],
            "what_it_supports": "workflow reproducibility and conditional diagnostic interpretation",
            "what_it_does_not_support": "independent calibration or physical credibility by itself",
        },
        {
            "site": "Chant Sura",
            "classification": "partial",
            "role": "trajectory/contact validation benchmark and second-site candidate",
            "evidence_sources": [
                "data/datasets.yaml:chant_sura_2020",
                "validation/cases/chant_sura_contact.yaml",
                "validation/cases/chant_sura_contact_heldout.yaml",
                "validation/internal/shape_contact_v0_chant_sura_model_selection.yaml",
                "validation/data/processed/chant_sura_2020/metadata_contact_split.json",
                "validation/data/processed/chant_sura_2020/holdout_validation_evidence_manifest.json",
                "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml",
            ],
            "what_it_supports": "contact/trajectory benchmarking and portability template work",
            "what_it_does_not_support": "Tschamut physical credibility without staged second-site geodata and holdout evidence",
        },
        {
            "site": "Schiers",
            "classification": "missing",
            "role": "future forest/deadwood benchmark candidate",
            "evidence_sources": [
                "data/datasets.yaml:schiers_deadwood_2022",
            ],
            "what_it_supports": "project metadata only",
            "what_it_does_not_support": "direct validation or calibration evidence in this checkout",
        },
        {
            "site": "Balfrin",
            "classification": "not_inferred",
            "role": "execution sufficiency and runtime evidence",
            "evidence_sources": [
                "validation/pilot_runs/tschamut_public_balfrin_readiness_v1.yaml",
                "validation/pilot_runs/tschamut_public_balfrin_target_gate_reproduction_v1.yaml",
                "docs/balfrin_single_job_execution_sufficiency.md",
            ],
            "what_it_supports": "single-job execution sufficiency and reducer/runtime interpretation",
            "what_it_does_not_support": "physical credibility or field validation",
        },
    ]


def product_layer_claim_boundaries() -> list[dict[str, Any]]:
    return [
        {
            "layer_key": "reach_probability",
            "layer_label": "reach probability",
            "layer_family": "trajectory-derived conditional summary",
            "diagnostic_usefulness": {
                "status": "present",
                "summary": "Useful for closure review, spatial QA, and cellwise reach coverage checks.",
            },
            "reproducibility": {
                "status": "present",
                "summary": "Deterministic for a fixed trajectory set, denominator, and grid contract.",
            },
            "physical_credibility": {
                "status": "not_established",
                "summary": "A conditional reach fraction is not an independent physical-probability statement.",
            },
            "operational_inadmissibility": {
                "status": "not_authorized",
                "summary": "The current product is not an operational hazard map or acceptance artifact.",
            },
            "scientific_fragility": {
                "level": "moderate",
                "summary": "Sensitive to trajectory completeness and denominator choice, but not an extreme-value layer.",
            },
            "current_repo_basis": [
                "Same-scale reach outputs and probability standard-error diagnostics are reproducible once the trajectory set is fixed.",
                "The current denominator is the supplied trajectory count, not a physical occurrence frequency.",
            ],
            "evidence_classes_needed": [
                {
                    "class_name": "independent_holdout_reach_benchmark",
                    "label": "Independent holdout reach benchmark",
                    "status": "missing",
                    "why": "Would test reach coverage against evidence held out from selection and diagnostics.",
                },
                {
                    "class_name": "trajectory_denominator_provenance_audit",
                    "label": "Trajectory denominator provenance audit",
                    "status": "missing",
                    "why": "Would document exactly which trajectories and filters define the reach denominator.",
                },
                {
                    "class_name": "site_scale_reach_validation_dataset",
                    "label": "Site-scale reach validation dataset",
                    "status": "missing",
                    "why": "Would strengthen the boundary with an independent site-scale benchmark.",
                },
            ],
        },
        {
            "layer_key": "deposition_density",
            "layer_label": "deposition density",
            "layer_family": "ensemble deposition distribution",
            "diagnostic_usefulness": {
                "status": "present",
                "summary": "Useful for deposition footprint QA and comparing where the ensemble comes to rest.",
            },
            "reproducibility": {
                "status": "present",
                "summary": "Deterministic for a fixed ensemble deposition CSV and grid contract.",
            },
            "physical_credibility": {
                "status": "not_established",
                "summary": "A deposition density is a conditional footprint summary, not a field-validated deposit model.",
            },
            "operational_inadmissibility": {
                "status": "not_authorized",
                "summary": "The current product is diagnostic only and not an operational hazard decision layer.",
            },
            "scientific_fragility": {
                "level": "moderate",
                "summary": "More stable than cellwise maxima, but still bound to the supplied deposition sample set.",
            },
            "current_repo_basis": [
                "Validation already writes an ensemble deposition CSV, so the layer can be replayed deterministically.",
                "The layer remains a supplied-sample density rather than an observed deposit inventory.",
            ],
            "evidence_classes_needed": [
                {
                    "class_name": "independent_holdout_deposition_benchmark",
                    "label": "Independent holdout deposition benchmark",
                    "status": "missing",
                    "why": "Would compare final-position density against held-out deposition evidence.",
                },
                {
                    "class_name": "georeferenced_deposition_point_inventory",
                    "label": "Georeferenced deposition point inventory",
                    "status": "missing",
                    "why": "Would ground the density field in independent spatial observations.",
                },
                {
                    "class_name": "trajectory_to_deposition_traceability_audit",
                    "label": "Trajectory-to-deposition traceability audit",
                    "status": "missing",
                    "why": "Would separate reproducibility of the CSV inputs from claim strength.",
                },
            ],
        },
        {
            "layer_key": "max_kinetic_energy",
            "layer_label": "max kinetic energy",
            "layer_family": "trajectory-derived extreme-value summary",
            "diagnostic_usefulness": {
                "status": "present",
                "summary": "Useful for identifying high-energy cells and closure-limiting disagreement.",
            },
            "reproducibility": {
                "status": "partial",
                "summary": "Deterministic for the same trajectories, but most sensitive to ensemble membership and support/nodata variation.",
            },
            "physical_credibility": {
                "status": "not_established",
                "summary": "A cellwise maximum is an extreme-value diagnostic, not a validated energy envelope.",
            },
            "operational_inadmissibility": {
                "status": "not_authorized",
                "summary": "The layer remains non-operational and cannot be treated as an approved hazard metric.",
            },
            "scientific_fragility": {
                "level": "highest",
                "summary": "This is the most fragile layer because cellwise maxima amplify rare trajectories and support/nodata differences.",
            },
            "current_repo_basis": [
                "The same-scale closure summaries repeatedly identify max kinetic energy as a dominant disagreement layer.",
                "Current evidence shows the layer is reproducible but still support/nodata sensitive.",
            ],
            "evidence_classes_needed": [
                {
                    "class_name": "instrumented_impact_energy_benchmark",
                    "label": "Instrumented impact-energy benchmark",
                    "status": "missing",
                    "why": "Would compare the maximum-energy envelope against independently measured impact energy.",
                },
                {
                    "class_name": "independent_energy_holdout_dataset",
                    "label": "Independent energy holdout dataset",
                    "status": "missing",
                    "why": "Would keep the energy benchmark separate from any selection or tuning evidence.",
                },
                {
                    "class_name": "energy_measurement_provenance_record",
                    "label": "Energy measurement provenance record",
                    "status": "missing",
                    "why": "Would document the measurement basis for any future energy credibility claim.",
                },
            ],
        },
        {
            "layer_key": "max_jump_height",
            "layer_label": "max jump height",
            "layer_family": "trajectory-derived extreme-value summary",
            "diagnostic_usefulness": {
                "status": "present",
                "summary": "Useful for locating cells where terrain clearance and obstacle interaction remain uncertain.",
            },
            "reproducibility": {
                "status": "partial",
                "summary": "Deterministic for fixed inputs, but sensitive to terrain support, nodata coverage, and block-radius assumptions.",
            },
            "physical_credibility": {
                "status": "not_established",
                "summary": "A cellwise maximum jump height remains an extreme-value diagnostic, not a validated clearance envelope.",
            },
            "operational_inadmissibility": {
                "status": "not_authorized",
                "summary": "The current product is diagnostic only and not an operational clearance or hazard approval layer.",
            },
            "scientific_fragility": {
                "level": "high",
                "summary": "This layer is fragile because terrain support/nodata differences and maximum reduction amplify small input changes.",
            },
            "current_repo_basis": [
                "Current closure summaries treat max jump height as support/nodata sensitive and still unresolved.",
                "The layer depends on terrain reference quality and block-radius handling as well as the trajectory set.",
            ],
            "evidence_classes_needed": [
                {
                    "class_name": "terrain_anchored_clearance_benchmark",
                    "label": "Terrain-anchored clearance benchmark",
                    "status": "missing",
                    "why": "Would compare jump-height maxima against independent terrain-clearance observations.",
                },
                {
                    "class_name": "independent_clearance_height_dataset",
                    "label": "Independent clearance-height dataset",
                    "status": "missing",
                    "why": "Would keep the clearance benchmark separate from the current diagnostic set.",
                },
                {
                    "class_name": "terrain_provenance_and_resolution_audit",
                    "label": "Terrain provenance and resolution audit",
                    "status": "missing",
                    "why": "Would document the terrain inputs needed to interpret jump-height maxima credibly.",
                },
            ],
        },
        {
            "layer_key": "conditional_intensity_exceedance_layers",
            "layer_label": "conditional intensity-exceedance layers",
            "layer_family": "trajectory-level threshold exceedance summary",
            "diagnostic_usefulness": {
                "status": "present",
                "summary": "Useful for threshold QA, convergence checks, and conditional intensity interpretation.",
            },
            "reproducibility": {
                "status": "present",
                "summary": "Deterministic for fixed thresholds, denominators, and trajectory inputs.",
            },
            "physical_credibility": {
                "status": "not_established",
                "summary": "Threshold exceedance remains conditional and does not become a physical-probability or annual-frequency product here.",
            },
            "operational_inadmissibility": {
                "status": "not_authorized",
                "summary": "The current exceedance layers are conditional diagnostics, not operational or return-period products.",
            },
            "scientific_fragility": {
                "level": "high",
                "summary": "Threshold choice and denominator conditioning can move the layer even when the trajectory ensemble is unchanged.",
            },
            "current_repo_basis": [
                "Current exceedance layers are written as conditional intensity-exceedance diagnostics with explicit thresholds.",
                "The supporting curve table records the denominator and conditioning semantics for each threshold.",
            ],
            "evidence_classes_needed": [
                {
                    "class_name": "threshold_tagged_holdout_benchmark",
                    "label": "Threshold-tagged holdout benchmark",
                    "status": "missing",
                    "why": "Would compare threshold crossings against held-out benchmark evidence.",
                },
                {
                    "class_name": "reserved_threshold_scoring_protocol",
                    "label": "Reserved threshold scoring protocol",
                    "status": "missing",
                    "why": "Would keep the exceedance score definition separate from selection and replay data.",
                },
                {
                    "class_name": "conditional_denominator_provenance_audit",
                    "label": "Conditional denominator provenance audit",
                    "status": "missing",
                    "why": "Would explain exactly which samples and filters define the current exceedance denominator.",
                },
            ],
        },
    ]


def render_text_report(report: dict[str, Any]) -> str:
    lines = [
        f"schema_version: {report['schema_version']}",
        f"physical_credibility_status: {report['physical_credibility_status']}",
        f"physical_probability_claims_allowed: {str(report['physical_probability_claims_allowed']).lower()}",
        f"calibration_status: {report['calibration_status']}",
        f"validation_status: {report['validation_status']}",
        f"annual_frequency_claims_allowed: {str(report['annual_frequency_claims_allowed']).lower()}",
        f"operational_claims_allowed: {str(report['operational_claims_allowed']).lower()}",
        f"risk_exposure_vulnerability_claims_allowed: {str(report['risk_exposure_vulnerability_claims_allowed']).lower()}",
        f"scale_up_authorized: {str(report['scale_up_authorized']).lower()}",
        "",
        "post_diagnostic_scale_context:",
        f"- status: {report['post_diagnostic_scale_context']['status']}",
        f"- scientific_validity_upgraded: {str(report['post_diagnostic_scale_context']['claim_boundaries']['scientific_validity_upgraded']).lower()}",
        "",
        "physical_probability_readiness_check:",
        f"- readiness_status: {report['physical_probability_readiness_check']['readiness_status']}",
        f"- passing_evidence_count: {report['physical_probability_readiness_check']['passing_evidence_count']}/{report['physical_probability_readiness_check']['required_evidence_count']}",
        f"- failing_evidence_classes: {', '.join(report['physical_probability_readiness_check']['failing_evidence_classes']) or 'none'}",
        f"- first_blocking_evidence_class: {report['physical_probability_readiness_check']['first_blocking_evidence_class'] or 'none'}",
        f"- source_frequency_intake: {report['source_frequency_intake']['intake_classification']} ({report['source_frequency_intake']['record_status']})",
        "",
        "evidence_gap_categories:",
    ]
    for entry in report["evidence_gap_categories"]:
        lines.append(f"- {entry['category']}: {entry['classification']}")
        lines.append(f"  what_exists: {', '.join(_stringify_list(entry.get('what_exists', [])))}")
        lines.append(f"  what_is_missing: {', '.join(_stringify_list(entry.get('what_is_missing', [])))}")
        lines.append(
            f"  minimum_additional_evidence_needed: {entry.get('minimum_additional_evidence_needed', '')}"
        )
    lines.append("")
    lines.append("claim_boundary_matrix:")
    for entry in report["claim_boundary_matrix"]:
        lines.append(f"- {entry['boundary']}: {entry['classification']}")
    lines.append("")
    guardrails = report["validation_leakage_guardrails"]
    lines.append("validation_leakage_guardrails:")
    lines.append(f"- guardrail_status: {guardrails['guardrail_status']}")
    lines.append(f"- holdout_split_audit_status: {guardrails['holdout_split_audit_status']}")
    lines.append(f"- calibration_separation_preflight_status: {guardrails['calibration_separation_preflight_status']}")
    if guardrails["failing_checks"]:
        lines.append("- failing_checks:")
        for item in guardrails["failing_checks"]:
            lines.append(f"  - {item['guardrail']}: {item['status']} ({item['dataset_or_parameter_source']})")
    else:
        lines.append("- failing_checks: none")
    lines.append("")
    separation = report["calibration_holdout_separation_check"]
    lines.append("calibration_holdout_separation_check:")
    lines.append(f"- separation_status: {separation['separation_status']}")
    lines.append(f"- overlap_count: {separation['overlap_count']}")
    lines.append(f"- next_required_acquisition_step: {separation['next_required_acquisition_step']}")
    lines.append("")
    lines.append("next_concrete_scientific_tasks:")
    for item in report.get("next_concrete_scientific_tasks", []):
        lines.append(f"- {item['rank']}. {item['task_id']}: {item['current_classification']} ({item['first_missing_input']})")
    lines.append("")
    lines.append("site_reference_evidence:")
    for entry in report["site_reference_evidence"]:
        lines.append(f"- {entry['site']}: {entry['classification']} ({entry['role']})")
    lines.append("")
    lines.append("product_layer_claim_boundaries:")
    for entry in report.get("product_layer_claim_boundaries", []):
        diag = entry.get("diagnostic_usefulness", {})
        repro = entry.get("reproducibility", {})
        physical = entry.get("physical_credibility", {})
        operational = entry.get("operational_inadmissibility", {})
        fragility = entry.get("scientific_fragility", {})
        lines.append(
            f"- {entry['layer_key']}: diagnostic={diag.get('status', '')} reproducibility={repro.get('status', '')} "
            f"physical={physical.get('status', '')} operational={operational.get('status', '')} "
            f"fragility={fragility.get('level', '')}"
        )
        evidence_classes = ", ".join(
            str(item.get("class_name") or "") for item in entry.get("evidence_classes_needed", [])
        )
        if evidence_classes:
            lines.append(f"  evidence_classes_needed: {evidence_classes}")
    return "\n".join(lines)


def validate_report_boundaries(report: dict[str, Any]) -> None:
    shared_require_false_fields(
        report,
        (
            "annual_frequency_claims_allowed",
            "physical_probability_claims_allowed",
            "operational_claims_allowed",
            "risk_exposure_vulnerability_claims_allowed",
            "scale_up_authorized",
        ),
        ValidationCalibrationEvidenceGapsError,
        label_prefix="report",
    )


def _stringify_list(values: list[Any]) -> list[str]:
    out: list[str] = []
    for value in values:
        if isinstance(value, str):
            out.append(value)
        else:
            out.append(json.dumps(value, sort_keys=True))
    return out


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
