#!/usr/bin/env python3
"""Assess evidence gaps between workflow credibility and physical credibility.

This helper is read-only. It composes existing manifests, fixtures, and docs
into a structured gap assessment and does not calibrate, tune, or run any
simulations.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except ImportError as exc:  # pragma: no cover - environment setup.
    raise SystemExit("PyYAML is required; install with `python3 -m pip install PyYAML`") from exc


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "validation_calibration_evidence_gaps_v1"
ALLOWED_CLASSIFICATIONS = {"present", "partial", "missing", "out_of_scope", "not_inferred"}


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


def build_report() -> dict[str, Any]:
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

    observed_deposition = observed_deposition_gap(datasets, tschamut_manifest, tschamut_gate, chant_contact, chant_contact_heldout)
    release_zone = release_zone_gap(datasets, tschamut_manifest, candidate_portability)
    block_population = block_population_gap(datasets, tschamut_gate, chant_model_selection)
    terrain_context = terrain_context_gap(tschamut_manifest, tschamut_gate, tschamut_target, candidate_portability)
    calibration = calibration_gap(tschamut_manifest, tschamut_gate, chant_contact, chant_contact_heldout, chant_model_selection)
    holdout = holdout_gap(tschamut_gate, tschamut_target, chant_contact_heldout, chant_split, balfrin_readiness, balfrin_reproduction)
    transfer = transfer_gap(candidate_manifest, candidate_portability, chant_contact, chant_contact_heldout, balfrin_readiness)

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
        "physical_credibility_status": derive_physical_credibility_status(evidence_gap_categories),
        "calibration_status": "missing",
        "validation_status": "partial",
        "annual_frequency_claims_allowed": False,
        "operational_claims_allowed": False,
        "risk_exposure_vulnerability_claims_allowed": False,
        "scale_up_authorized": False,
        "evidence_gap_categories": evidence_gap_categories,
        "claim_boundary_matrix": claim_boundary_matrix,
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
    return report


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
    missing_input_categories: list[str] = []
    missing_input_paths_or_patterns: list[str] = []
    for category, raw_path in required_path_items.items():
        path_text = str(raw_path or "").strip()
        if not path_text:
            missing_input_categories.append(category)
            missing_input_paths_or_patterns.append(f"<missing:{category}>")
            continue
        path = ROOT / path_text if not Path(path_text).is_absolute() else Path(path_text)
        if not path.exists():
            missing_input_categories.append(category)
            missing_input_paths_or_patterns.append(str(path))

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
        "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml",
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
) -> dict[str, Any]:
    current = {
        "category": "observed_deposition_runout_evidence",
        "classification": "partial",
        "current_evidence": [
            dataset_summary(datasets, "tschamut2014"),
            "Tschamut gate freeze records observed deposition / runout metrics and deterministic release sampling",
            "Chant Sura contact fixtures record trajectory/contact metrics and a held-out contact subset",
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
        ],
        "minimum_additional_evidence_needed": (
            "A held-out field or benchmark deposition/runout dataset with explicit provenance, spatial reference, "
            "and comparison metrics that is not used to fit the model."
        ),
        "support_role": "diagnostic_QA_only",
        "claim_boundary": "diagnostic_QA_only",
        "physical_probability_relevance": "partial",
        "holdout_validation_relevance": "partial",
    }
    return current


def release_zone_gap(
    datasets: dict[str, dict[str, Any]],
    tschamut_manifest: dict[str, Any],
    candidate_portability: dict[str, Any],
) -> dict[str, Any]:
    return {
        "category": "release_zone_evidence",
        "classification": "partial",
        "current_evidence": [
            dataset_summary(datasets, "tschamut2014"),
            tschamut_manifest.get("selected_domain", {}),
            candidate_portability["candidate_site"],
        ],
        "what_exists": [
            "Tschamut source-zone metadata and policy are frozen and deterministic",
            "The candidate Chant Sura / Flüelapass manifest declares a source-zone contract shape",
        ],
        "what_is_missing": [
            "A second-site release-zone geometry with staged public geodata and provenance",
            "Independent field justification that can be tested against holdout data",
        ],
        "minimum_additional_evidence_needed": (
            "A site-specific release-zone geometry with documented derivation rules and comparison data that can be "
            "validated independently of the current pilot."
        ),
        "support_role": "diagnostic_and_portability_only",
        "claim_boundary": "conditional_diagnostic_only",
        "physical_probability_relevance": "partial",
        "holdout_validation_relevance": "partial",
    }


def block_population_gap(
    datasets: dict[str, dict[str, Any]],
    tschamut_gate: dict[str, Any],
    chant_model_selection: dict[str, Any],
) -> dict[str, Any]:
    return {
        "category": "block_size_and_block_population_evidence",
        "classification": "missing",
        "current_evidence": [
            dataset_summary(datasets, "tschamut2014"),
            dataset_summary(datasets, "chant_sura_2020"),
            tschamut_gate.get("sampling_plan", {}),
            chant_model_selection.get("shape_source", {}),
        ],
        "what_exists": [
            "Tschamut uses conditional sampling only",
            "Chant Sura contact fixtures carry block mass / radius and shape proxies for contact comparisons",
        ],
        "what_is_missing": [
            "Source occurrence rates or block-population frequencies",
            "A physical-probability semantics for block size / frequency",
            "A benchmark that explicitly separates representative scenarios from population semantics",
        ],
        "minimum_additional_evidence_needed": (
            "Observed block-population or source-frequency evidence, or a documented external model for frequency "
            "semantics, before any physical probability claim."
        ),
        "support_role": "conditional_scenario_only",
        "claim_boundary": "conditional_only",
        "physical_probability_relevance": "missing",
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
) -> dict[str, Any]:
    return {
        "category": "calibration_evidence",
        "classification": "missing",
        "current_evidence": [
            tschamut_manifest.get("claim_boundary", {}),
            tschamut_gate.get("physics_freeze", {}),
            chant_contact.get("expected", {}).get("metrics", []),
            chant_contact_heldout.get("expected", {}).get("metrics", []),
            chant_model_selection.get("frozen_reference_metrics", {}),
        ],
        "what_exists": [
            "Current pilot evidence is explicitly non-tuning and non-operational",
            "Chant Sura contact fixtures support model comparison and shape sensitivity only",
        ],
        "what_is_missing": [
            "A calibration dataset with a documented objective function and parameter bounds",
            "A holdout split reserved for post-fit validation",
            "A statement that current Tschamut outputs are calibrated evidence",
        ],
        "minimum_additional_evidence_needed": (
            "A calibration record that names the calibration dataset, objective function, parameter bounds, fitted "
            "values, and a separate holdout validation dataset."
        ),
        "support_role": "not_calibrated",
        "claim_boundary": "calibration_out_of_scope_for_current_pilot",
        "physical_probability_relevance": "missing",
        "holdout_validation_relevance": "missing",
    }


def holdout_gap(
    tschamut_gate: dict[str, Any],
    tschamut_target: dict[str, Any],
    chant_contact_heldout: dict[str, Any],
    chant_split: dict[str, Any],
    balfrin_readiness: dict[str, Any],
    balfrin_reproduction: dict[str, Any],
) -> dict[str, Any]:
    return {
        "category": "holdout_and_validation_evidence",
        "classification": "partial",
        "current_evidence": [
            tschamut_gate.get("workflow_gates", {}),
            tschamut_target.get("evidence_result", {}),
            chant_contact_heldout.get("report", {}),
            chant_split,
            balfrin_readiness.get("readiness_status", ""),
            balfrin_reproduction.get("evidence_result", {}).get("interpretation", ""),
        ],
        "what_exists": [
            "Tschamut diagnostic validation and same-scale comparisons are measured",
            "Chant Sura includes held-out contact fixture metadata",
            "Balfrin execution evidence shows local job sufficiency, not field validation",
        ],
        "what_is_missing": [
            "An independent holdout benchmark that is not part of the current diagnostic or model-selection fixtures",
            "Field evidence reserved for predictive credibility rather than replaying diagnostic data",
        ],
        "minimum_additional_evidence_needed": (
            "A reserved holdout dataset with site provenance, explicit split rules, and a scoring protocol that does "
            "not reuse the same data for selection."
        ),
        "support_role": "diagnostic_validation_only",
        "claim_boundary": "diagnostic_validation_not_holdout_credibility",
        "physical_probability_relevance": "partial",
        "holdout_validation_relevance": "partial",
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
    if labels.get("calibration_evidence") == "missing" or labels.get("holdout_and_validation_evidence") in {"missing", "partial"}:
        return "not_established"
    return "partial"


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


def render_text_report(report: dict[str, Any]) -> str:
    lines = [
        f"schema_version: {report['schema_version']}",
        f"physical_credibility_status: {report['physical_credibility_status']}",
        f"calibration_status: {report['calibration_status']}",
        f"validation_status: {report['validation_status']}",
        f"annual_frequency_claims_allowed: {str(report['annual_frequency_claims_allowed']).lower()}",
        f"operational_claims_allowed: {str(report['operational_claims_allowed']).lower()}",
        f"risk_exposure_vulnerability_claims_allowed: {str(report['risk_exposure_vulnerability_claims_allowed']).lower()}",
        f"scale_up_authorized: {str(report['scale_up_authorized']).lower()}",
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
    lines.append("site_reference_evidence:")
    for entry in report["site_reference_evidence"]:
        lines.append(f"- {entry['site']}: {entry['classification']} ({entry['role']})")
    return "\n".join(lines)


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
