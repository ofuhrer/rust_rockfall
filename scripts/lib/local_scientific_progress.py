"""Local scientific progress report helpers.

The report is read-only. It composes existing local evidence reports into a
compact ranking of work that can improve scientific auditability without
claiming physical probability, annual frequency, operational use, or scale-up.
"""

from __future__ import annotations

from typing import Any

from scripts import assess_validation_calibration_evidence_gaps as evidence_gaps
from scripts import check_same_scale_artifact_readiness as same_scale_readiness


SCHEMA_VERSION = "local_scientific_progress_summary_v1"


def build_report() -> dict[str, Any]:
    gap_report = evidence_gaps.build_report()
    readiness_report = same_scale_readiness.build_readiness_report()
    categories = {entry["category"]: entry for entry in gap_report["evidence_gap_categories"]}
    layers = {entry["layer_key"]: entry for entry in gap_report["product_layer_claim_boundaries"]}

    tracks = [
        {
            "rank": 1,
            "track_id": "conditional_denominator_provenance",
            "status": readiness_status_to_track_status(readiness_report),
            "why_now": "Conditional reach and threshold layers are locally ready, but denominator provenance is still the first interpretation guardrail.",
            "uses_local_evidence": [
                "hazard/results/tschamut_public_pilot/target_gate_v1",
                "validation/private/tschamut_public_pilot/target_gate_v1",
            ],
            "unblocks": "safer interpretation of conditional reach and exceedance layers without changing their claim level",
            "next_command": "PYENV_VERSION=system uv run python scripts/audit_conditional_denominator_provenance.py --format json",
        },
        {
            "rank": 2,
            "track_id": "trajectory_deposition_traceability",
            "status": readiness_status_to_track_status(readiness_report),
            "why_now": "Deposition density is one of the more interpretable diagnostics and can be traced locally before external field evidence exists.",
            "uses_local_evidence": [
                "validation/private/tschamut_public_pilot/target_gate_v1",
                "hazard/results/tschamut_public_pilot/target_gate_v1",
            ],
            "unblocks": "explicit map-to-validation traceability for deposition diagnostics",
            "next_command": "PYENV_VERSION=system uv run python scripts/audit_trajectory_deposition_traceability.py --format json",
        },
        {
            "rank": 3,
            "track_id": "extreme_layer_fragility",
            "status": "ready_for_local_audit",
            "why_now": "Max kinetic energy and max jump height are the most fragile current layers and should drive local sensitivity work.",
            "uses_local_evidence": [
                "docs/tschamut_public_same_scale_uncertainty_envelope.md",
                "hazard/results/tschamut_public_pilot/gate_v1",
                "hazard/results/tschamut_public_pilot/target_gate_v1",
            ],
            "unblocks": "prioritized sensitivity checks for the least stable scientific surfaces",
            "next_command": "PYENV_VERSION=system uv run python scripts/rank_local_hazard_layer_fragility.py --format json",
        },
        {
            "rank": 4,
            "track_id": "second_site_local_blockers",
            "status": gap_report["second_site_portability_status"],
            "why_now": "Second-site portability is the clearest path beyond Tschamut, but the local prepared-pilot blockers must be grouped first.",
            "uses_local_evidence": [
                "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml",
                "docs/aoi_user_manual.md",
            ],
            "unblocks": "local Chant Sura / Fluelapass input staging without remote execution",
            "next_command": "PYENV_VERSION=system uv run python scripts/inventory_second_site_local_blockers.py --format json",
        },
        {
            "rank": 5,
            "track_id": "chant_sura_holdout_split",
            "status": "ready_for_local_audit",
            "why_now": "Chant Sura is the main holdout-style contact evidence, so split independence should be executable.",
            "uses_local_evidence": [
                "validation/data/processed/chant_sura_2020/metadata_contact_split.json",
                "validation/data/processed/chant_sura_2020/holdout_validation_evidence_manifest.json",
            ],
            "unblocks": "guarded use of Chant Sura contact evidence as diagnostic holdout evidence",
            "next_command": "PYENV_VERSION=system uv run python scripts/audit_chant_sura_holdout_split.py --format json",
        },
        {
            "rank": 6,
            "track_id": "calibration_separation",
            "status": categories["calibration_evidence"]["classification"],
            "why_now": "Calibration is missing for claim purposes, so current calibration artifacts need an explicit non-default guardrail before tuning work appears.",
            "uses_local_evidence": [
                "calibration/experiments",
                "validation/cases",
            ],
            "unblocks": "future calibration tasks without contaminating validation acceptance evidence",
            "next_command": "PYENV_VERSION=system uv run python scripts/check_calibration_separation_preflight.py --format json",
        },
    ]

    return {
        "schema_version": SCHEMA_VERSION,
        "scientific_status": {
            "physical_credibility_status": gap_report["physical_credibility_status"],
            "validation_status": gap_report["validation_status"],
            "calibration_status": gap_report["calibration_status"],
            "same_scale_readiness_status": readiness_report["readiness_status"],
            "second_site_portability_status": gap_report["second_site_portability_status"],
        },
        "claim_boundaries": {
            "annual_frequency_claims_allowed": gap_report["annual_frequency_claims_allowed"],
            "operational_claims_allowed": gap_report["operational_claims_allowed"],
            "physical_probability_claims_allowed": False,
            "risk_exposure_vulnerability_claims_allowed": gap_report["risk_exposure_vulnerability_claims_allowed"],
            "scale_up_authorized": gap_report["scale_up_authorized"],
            "balfrin_required": False,
        },
        "local_artifact_status": {
            "readiness_status": readiness_report["readiness_status"],
            "missing_paths": readiness_report["missing_paths"],
            "target_hazard_ready": readiness_report["target_hazard_ready"],
            "target_validation_ready": readiness_report["target_validation_ready"],
            "convergence_ready": readiness_report["convergence_ready"],
            "output_profile_ready": readiness_report["output_profile_ready"],
        },
        "most_fragile_layers": [
            {
                "layer_key": "max_kinetic_energy",
                "fragility": layers["max_kinetic_energy"]["scientific_fragility"]["level"],
                "reason": layers["max_kinetic_energy"]["scientific_fragility"]["summary"],
            },
            {
                "layer_key": "max_jump_height",
                "fragility": layers["max_jump_height"]["scientific_fragility"]["level"],
                "reason": layers["max_jump_height"]["scientific_fragility"]["summary"],
            },
        ],
        "ranked_local_tracks": tracks,
        "required_external_evidence_not_solved_locally": gap_report["required_evidence_for_physical_credibility"],
    }


def readiness_status_to_track_status(readiness_report: dict[str, Any]) -> str:
    if readiness_report["readiness_status"] == "ready":
        return "ready_from_local_artifacts"
    return "blocked_missing_local_artifacts"


def render_text_report(report: dict[str, Any]) -> str:
    lines = [
        f"schema_version: {report['schema_version']}",
        "scientific_status:",
        f"  physical_credibility_status: {report['scientific_status']['physical_credibility_status']}",
        f"  validation_status: {report['scientific_status']['validation_status']}",
        f"  calibration_status: {report['scientific_status']['calibration_status']}",
        f"  same_scale_readiness_status: {report['scientific_status']['same_scale_readiness_status']}",
        f"  second_site_portability_status: {report['scientific_status']['second_site_portability_status']}",
        "claim_boundaries:",
    ]
    for key, value in report["claim_boundaries"].items():
        lines.append(f"  {key}: {value}")
    lines.append("ranked_local_tracks:")
    for track in report["ranked_local_tracks"]:
        lines.append(
            f"  {track['rank']}. {track['track_id']} [{track['status']}]: {track['why_now']}"
        )
        lines.append(f"     next_command: {track['next_command']}")
    lines.append("most_fragile_layers:")
    for layer in report["most_fragile_layers"]:
        lines.append(f"  - {layer['layer_key']}: {layer['fragility']} ({layer['reason']})")
    return "\n".join(lines)
