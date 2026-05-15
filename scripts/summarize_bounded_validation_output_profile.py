#!/usr/bin/env python3
"""Summarize bounded validation-output evidence for the selected Tschamut pilot.

The summary is record-driven. It reads the existing pilot gate, Balfrin
reproduction, convergence, output-budget, and feasibility records, records the
bounded output profile controls and measured file/byte/inode pressure, and
returns an explicit blocked state when local ignored outputs are absent.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CURRENT_PRESSURE_RECORD = ROOT / "validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml"
DEFAULT_BOUNDED_PROFILE_RECORD = ROOT / "validation/pilot_runs/tschamut_public_balfrin_target_gate_reproduction_v1.yaml"
DEFAULT_OUTPUT_BUDGET_RECORD = ROOT / "validation/pilot_runs/tschamut_public_output_budget_reducer_gate_v1.yaml"
DEFAULT_CONVERGENCE_RECORD = ROOT / "validation/pilot_runs/tschamut_public_conditional_convergence_protocol_v1.yaml"
DEFAULT_ENSEMBLE_FEASIBILITY_RECORD = ROOT / "validation/pilot_runs/tschamut_public_ensemble_feasibility_v1.yaml"
DEFAULT_LOCAL_MANIFESTS = (
    ROOT / "validation/private/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_manifest.json",
    ROOT / "hazard/results/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_manifest.json",
    ROOT / "hazard/results/tschamut_public_pilot/gate_v1/tschamut_public_conditional_gate_v1_pilot_gis_package_manifest.json",
)

SUMMARY_SCHEMA_VERSION = "bounded_validation_output_profile_v1"


class BoundedValidationOutputProfileError(ValueError):
    """User-facing bounded output profile summary error."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--current-pressure-record", type=Path, default=DEFAULT_CURRENT_PRESSURE_RECORD)
    parser.add_argument("--bounded-profile-record", type=Path, default=DEFAULT_BOUNDED_PROFILE_RECORD)
    parser.add_argument("--output-budget-record", type=Path, default=DEFAULT_OUTPUT_BUDGET_RECORD)
    parser.add_argument("--convergence-record", type=Path, default=DEFAULT_CONVERGENCE_RECORD)
    parser.add_argument("--ensemble-feasibility-record", type=Path, default=DEFAULT_ENSEMBLE_FEASIBILITY_RECORD)
    parser.add_argument("--markdown-output", type=Path, default=None)
    parser.add_argument("--json-output", type=Path, default=None)
    parser.add_argument("--format", choices=["text", "markdown", "json"], default="text")
    args = parser.parse_args(argv)

    try:
        summary = build_summary(
            current_pressure_record_path=args.current_pressure_record,
            bounded_profile_record_path=args.bounded_profile_record,
            output_budget_record_path=args.output_budget_record,
            convergence_record_path=args.convergence_record,
            ensemble_feasibility_record_path=args.ensemble_feasibility_record,
        )
    except BoundedValidationOutputProfileError as exc:
        print(f"bounded validation output profile error: {exc}", file=sys.stderr)
        return 2

    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.markdown_output is not None:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(render_markdown(summary), encoding="utf-8")

    if args.format == "json":
        print(json.dumps(summary, indent=2, sort_keys=True))
    elif args.format == "markdown":
        print(render_markdown(summary), end="")
    else:
        print(
            "bounded validation output profile summary: "
            f"{summary['acceptance_classification']} "
            f"(profile={summary['bounded_profile']['profile']}, "
            f"hazard_files={summary['bounded_profile']['hazard_output_file_count']}, "
            f"hazard_bytes={summary['bounded_profile']['hazard_output_bytes']})"
        )
    return 0


def build_summary(
    *,
    current_pressure_record_path: Path = DEFAULT_CURRENT_PRESSURE_RECORD,
    bounded_profile_record_path: Path = DEFAULT_BOUNDED_PROFILE_RECORD,
    output_budget_record_path: Path = DEFAULT_OUTPUT_BUDGET_RECORD,
    convergence_record_path: Path = DEFAULT_CONVERGENCE_RECORD,
    ensemble_feasibility_record_path: Path = DEFAULT_ENSEMBLE_FEASIBILITY_RECORD,
) -> dict[str, Any]:
    current_pressure_record = read_yaml(require_existing_path(current_pressure_record_path, "current_pressure_record_path"))
    bounded_profile_record = read_yaml(require_existing_path(bounded_profile_record_path, "bounded_profile_record_path"))
    output_budget_record = read_yaml(require_existing_path(output_budget_record_path, "output_budget_record_path"))
    convergence_record = read_yaml(require_existing_path(convergence_record_path, "convergence_record_path"))
    ensemble_feasibility_record = read_yaml(
        require_existing_path(ensemble_feasibility_record_path, "ensemble_feasibility_record_path")
    )

    current_evidence = require_mapping(current_pressure_record.get("run_evidence"), "current_pressure_record.run_evidence")
    current_budget = require_mapping(current_pressure_record.get("output_budget"), "current_pressure_record.output_budget")
    current_file_count = require_positive_int(current_evidence.get("output_file_count"), "current_pressure_record.run_evidence.output_file_count")
    current_bytes = require_positive_int(current_evidence.get("output_total_bytes"), "current_pressure_record.run_evidence.output_total_bytes")
    current_file_ceiling = require_positive_int(current_budget.get("max_private_file_count"), "current_pressure_record.output_budget.max_private_file_count")
    current_byte_ceiling = require_positive_int(current_budget.get("max_private_total_bytes"), "current_pressure_record.output_budget.max_private_total_bytes")

    bounded_profile = require_mapping(
        bounded_profile_record.get("hazard_output_profile"), "bounded_profile_record.hazard_output_profile"
    )
    bounded_performance = require_mapping(bounded_profile_record.get("performance"), "bounded_profile_record.performance")
    bounded_conditional = require_mapping(
        bounded_profile_record.get("conditional_execution"), "bounded_profile_record.conditional_execution"
    )
    bounded_validation_metrics = require_mapping(
        bounded_profile_record.get("validation_metrics"), "bounded_profile_record.validation_metrics"
    )
    bounded_checksums = require_mapping(bounded_profile_record.get("checksums"), "bounded_profile_record.checksums")
    bounded_run_environment = require_mapping(
        bounded_profile_record.get("run_environment"), "bounded_profile_record.run_environment"
    )
    bounded_input_freeze = require_mapping(bounded_profile_record.get("input_freeze"), "bounded_profile_record.input_freeze")
    bounded_claim_boundary = require_mapping(bounded_profile_record.get("claim_boundary"), "bounded_profile_record.claim_boundary")
    bounded_limitations = require_list(bounded_profile_record.get("limitations"), "bounded_profile_record.limitations")
    bounded_target_gate = read_yaml(
        require_existing_path(
            ROOT / require_text(
                require_mapping(output_budget_record.get("selected_dt04_output_evidence"), "output_budget_record.selected_dt04_output_evidence").get(
                    "target_gate_record_path"
                ),
                "output_budget_record.selected_dt04_output_evidence.target_gate_record_path",
            ),
            "output_budget_record.selected_dt04_output_evidence.target_gate_record_path",
        )
    )
    target_execution = require_mapping(bounded_target_gate.get("execution_evidence"), "target_gate_record.execution_evidence")
    target_validation_run = require_mapping(target_execution.get("validation_run"), "target_gate_record.execution_evidence.validation_run")
    target_hazard_run = require_mapping(target_execution.get("hazard_run"), "target_gate_record.execution_evidence.hazard_run")

    selected_dt04 = require_mapping(output_budget_record.get("selected_dt04_output_evidence"), "output_budget_record.selected_dt04_output_evidence")
    current_target_profile = require_mapping(
        require_mapping(output_budget_record.get("output_profile"), "output_budget_record.output_profile").get(
            "current_target_gate_profile"
        ),
        "output_budget_record.output_profile.current_target_gate_profile",
    )
    selected_followup_profile = require_mapping(
        require_mapping(output_budget_record.get("output_profile"), "output_budget_record.output_profile").get(
            "selected_followup_profile"
        ),
        "output_budget_record.output_profile.selected_followup_profile",
    )
    validation_debug_budget = require_mapping(
        require_mapping(output_budget_record.get("output_profile"), "output_budget_record.output_profile").get(
            "validation_debug_output_budget"
        ),
        "output_budget_record.output_profile.validation_debug_output_budget",
    )
    validation_output_budget = require_mapping(output_budget_record.get("validation_output_budget"), "output_budget_record.validation_output_budget")
    hazard_output_budget = require_mapping(output_budget_record.get("hazard_output_budget"), "output_budget_record.hazard_output_budget")
    inode_budget = require_mapping(output_budget_record.get("inode_and_file_family_budget"), "output_budget_record.inode_and_file_family_budget")
    required_blockers = require_list(output_budget_record.get("required_blockers"), "output_budget_record.required_blockers")
    required_future_evidence = require_list(output_budget_record.get("required_future_evidence"), "output_budget_record.required_future_evidence")
    convergence_assessment = require_mapping(convergence_record.get("assessment"), "convergence_record.assessment")
    convergence_evidence = require_mapping(convergence_assessment.get("evidence"), "convergence_record.assessment.evidence")
    convergence_indicators = require_mapping(
        convergence_evidence.get("convergence_indicators"), "convergence_record.assessment.evidence.convergence_indicators"
    )
    convergence_blockers = require_list(convergence_assessment.get("blocking_reasons"), "convergence_record.assessment.blocking_reasons")
    feasibility_decision = require_text(ensemble_feasibility_record.get("decision"), "ensemble_feasibility_record.decision")
    feasibility_output_budget = require_mapping(
        ensemble_feasibility_record.get("output_budget_assessment"), "ensemble_feasibility_record.output_budget_assessment"
    )
    feasibility_blockers = require_list(ensemble_feasibility_record.get("blockers"), "ensemble_feasibility_record.blockers")

    target_validation_count = require_positive_int(
        validation_output_budget.get("file_count"), "output_budget_record.validation_output_budget.file_count"
    )
    target_validation_bytes = require_positive_int(
        validation_output_budget.get("bytes"), "output_budget_record.validation_output_budget.bytes"
    )
    target_hazard_count = require_positive_int(hazard_output_budget.get("file_count"), "output_budget_record.hazard_output_budget.file_count")
    target_hazard_bytes = require_positive_int(hazard_output_budget.get("bytes"), "output_budget_record.hazard_output_budget.bytes")

    bounded_validation_count = require_positive_int(
        bounded_performance.get("validation_output_file_count"), "bounded_profile_record.performance.validation_output_file_count"
    )
    bounded_validation_bytes = require_positive_int(
        bounded_performance.get("validation_output_bytes"), "bounded_profile_record.performance.validation_output_bytes"
    )
    bounded_hazard_count = require_positive_int(
        bounded_performance.get("hazard_output_file_count"), "bounded_profile_record.performance.hazard_output_file_count"
    )
    bounded_hazard_bytes = require_positive_int(
        bounded_performance.get("hazard_output_bytes"), "bounded_profile_record.performance.hazard_output_bytes"
    )

    profile_controls = {
        "conditional_curve_export": bounded_profile.get("conditional_curve_export"),
        "grid_csv_export": bounded_profile.get("grid_csv_export"),
        "no_plots": bool(bounded_profile.get("no_plots")),
        "export_geotiff": bool(bounded_profile.get("export_geotiff")),
        "pilot_gis_package": bool(bounded_profile.get("pilot_gis_package")),
        "probability_mode": bounded_profile.get("probability_mode"),
        "normalization_scope": bounded_profile.get("normalization_scope"),
        "trajectory_workers": require_positive_int(
            bounded_conditional.get("trajectory_generation", {}).get("worker_count", 0)
            or bounded_profile_record.get("physics_and_sampling", {}).get("trajectory_workers", 0),
            "bounded_profile_record.physics_and_sampling.trajectory_workers",
        ),
        "reducer_workers": require_positive_int(
            bounded_conditional.get("reducer", {}).get("worker_count", 0)
            or bounded_profile_record.get("physics_and_sampling", {}).get("reducer_workers", 0),
            "bounded_profile_record.physics_and_sampling.reducer_workers",
        ),
    }
    included_output_classes = [
        "conditional_curve_summary_only",
        "geotiff_rasters",
        "pilot_gis_package",
        "chunk_manifests_and_restart_state",
        "checksum_sidecars",
    ]
    excluded_output_classes = [
        "full_conditional_curve_csv",
        "grid_csv",
        "plot_outputs",
    ]

    measured_savings = {
        "validation_output_file_count_delta_vs_target_budget": bounded_validation_count - target_validation_count,
        "validation_output_bytes_delta_vs_target_budget": bounded_validation_bytes - target_validation_bytes,
        "hazard_output_file_count_delta_vs_target_budget": bounded_hazard_count - target_hazard_count,
        "hazard_output_bytes_delta_vs_target_budget": bounded_hazard_bytes - target_hazard_bytes,
    }

    current_pressure = {
        "source_record_path": str(current_pressure_record_path),
        "run_id": require_text(current_pressure_record.get("run_id"), "current_pressure_record.run_id"),
        "current_file_count": current_file_count,
        "current_total_bytes": current_bytes,
        "file_count_ceiling": current_file_ceiling,
        "byte_ceiling": current_byte_ceiling,
        "file_count_margin": current_file_ceiling - current_file_count,
        "byte_margin": current_byte_ceiling - current_bytes,
        "trajectory_count": current_evidence.get("trajectory_count"),
        "release_cell_count": current_evidence.get("release_cell_count"),
        "convergence_notes": require_mapping(
            current_evidence.get("convergence_diagnostics"), "current_pressure_record.run_evidence.convergence_diagnostics"
        ).get("notes", []),
    }

    local_output_audit = summarize_local_outputs(current_evidence)

    acceptance_classification = classify_acceptance(
        convergence_status=require_text(convergence_indicators.get("status"), "convergence_record.assessment.evidence.convergence_indicators.status"),
        output_budget_status=require_text(validation_debug_budget.get("status"), "output_budget_record.output_profile.validation_debug_output_budget.status"),
        local_output_status=local_output_audit["status"],
        feasibility_decision=feasibility_decision,
    )

    return {
        "schema_version": SUMMARY_SCHEMA_VERSION,
        "pilot_id": require_text(current_pressure_record.get("pilot_id"), "current_pressure_record.pilot_id"),
        "case_id": require_text(bounded_target_gate.get("run_id"), "target_gate_record.run_id"),
        "case_path": require_text(target_validation_run.get("case_path"), "target_gate_record.execution_evidence.validation_run.case_path"),
        "acceptance_classification": acceptance_classification,
        "final_classification": acceptance_classification,
        "scale_up_authorized": False,
        "measurement_status": "record_based_measurement",
        "bounded_profile": {
            "record_path": str(bounded_profile_record_path),
            "run_id": require_text(bounded_profile_record.get("run_id"), "bounded_profile_record.run_id"),
            "profile": require_text(bounded_profile.get("profile"), "bounded_profile_record.hazard_output_profile.profile"),
            "command_recipe": {
                "case_path": require_text(target_validation_run.get("case_path"), "target_gate_record.execution_evidence.validation_run.case_path"),
                "validation_command": "cargo run -- validate --case "
                + require_text(target_validation_run.get("case_path"), "target_gate_record.execution_evidence.validation_run.case_path"),
                "profile_controls": profile_controls,
            },
            "included_output_classes": included_output_classes,
            "excluded_output_classes": excluded_output_classes,
            "hazard_output_file_count": bounded_hazard_count,
            "hazard_output_bytes": bounded_hazard_bytes,
            "validation_output_file_count": bounded_validation_count,
            "validation_output_bytes": bounded_validation_bytes,
            "conditional_curve_row_count": require_positive_int(
                bounded_profile.get("conditional_curve_row_count"), "bounded_profile_record.hazard_output_profile.conditional_curve_row_count"
            ),
            "conditional_curve_csv_written": bool(bounded_profile.get("conditional_curve_csv_written")),
            "grid_csv_written": bool(bounded_profile.get("grid_csv_written")),
            "manual_gis_qa_status": require_text(
                bounded_profile.get("manual_gis_qa_status"), "bounded_profile_record.hazard_output_profile.manual_gis_qa_status"
            ),
            "output_profile_status": require_text(
                bounded_profile.get("profile"), "bounded_profile_record.hazard_output_profile.profile"
            ),
            "performance": {
                "validation_output_file_count": bounded_validation_count,
                "validation_output_bytes": bounded_validation_bytes,
                "hazard_output_file_count": bounded_hazard_count,
                "hazard_output_bytes": bounded_hazard_bytes,
                "validation_output_write_seconds": bounded_performance.get("validation_output_write_seconds"),
                "hazard_output_write_seconds": bounded_performance.get("hazard_output_write_seconds"),
                "validation_total_wall_seconds": bounded_performance.get("validation_total_wall_seconds"),
                "hazard_total_wall_seconds": bounded_performance.get("hazard_total_wall_seconds"),
            },
            "physics_and_sampling": bounded_profile_record.get("physics_and_sampling"),
            "run_environment": bounded_run_environment,
            "validation_metrics": bounded_validation_metrics,
            "checksums": bounded_checksums,
            "claim_boundary": bounded_claim_boundary,
            "limitations": bounded_limitations,
        },
        "current_pressure": current_pressure,
        "current_target_gate_profile": {
            "record_path": str(output_budget_record_path),
            "profile": require_text(current_target_profile.get("profile"), "output_budget_record.output_profile.current_target_gate_profile.profile"),
            "conditional_curve_export_mode": require_text(
                current_target_profile.get("conditional_curve_export_mode"), "output_budget_record.output_profile.current_target_gate_profile.conditional_curve_export_mode"
            ),
            "grid_csv_export_mode": require_text(
                current_target_profile.get("grid_csv_export_mode"), "output_budget_record.output_profile.current_target_gate_profile.grid_csv_export_mode"
            ),
            "plots_enabled": bool(current_target_profile.get("plots_enabled")),
        },
        "selected_followup_profile": {
            "profile": require_text(selected_followup_profile.get("profile"), "output_budget_record.output_profile.selected_followup_profile.profile"),
            "required_controls": require_list(selected_followup_profile.get("required_controls"), "output_budget_record.output_profile.selected_followup_profile.required_controls"),
        },
        "measured_savings": measured_savings,
        "output_budget_gate": {
            "record_path": str(output_budget_record_path),
            "current_classification": require_text(output_budget_record.get("current_classification"), "output_budget_record.current_classification"),
            "qa_status": require_text(output_budget_record.get("qa_status"), "output_budget_record.qa_status"),
            "scale_up_authorized": bool(output_budget_record.get("scale_up_authorized")),
            "validation_debug_output_budget": {
                "status": require_text(validation_debug_budget.get("status"), "output_budget_record.output_profile.validation_debug_output_budget.status"),
                "acceptable_for_next_scale_increase_without_reduction_or_justification": bool(
                    validation_debug_budget.get("acceptable_for_next_scale_increase_without_reduction_or_justification")
                ),
                "target_validation_output_file_count": require_positive_int(
                    validation_debug_budget.get("target_validation_output_file_count"),
                    "output_budget_record.output_profile.validation_debug_output_budget.target_validation_output_file_count",
                ),
                "target_validation_output_total_bytes": require_positive_int(
                    validation_debug_budget.get("target_validation_output_total_bytes"),
                    "output_budget_record.output_profile.validation_debug_output_budget.target_validation_output_total_bytes",
                ),
            },
            "validation_output_budget": {
                "file_count": target_validation_count,
                "bytes": target_validation_bytes,
            },
            "hazard_output_budget": {
                "file_count": target_hazard_count,
                "bytes": target_hazard_bytes,
            },
            "inode_and_file_family_budget": inode_budget,
            "required_blockers": required_blockers,
            "required_future_evidence": required_future_evidence,
        },
        "convergence": {
            "record_path": str(convergence_record_path),
            "status": require_text(convergence_indicators.get("status"), "convergence_record.assessment.evidence.convergence_indicators.status"),
            "blocking_reasons": convergence_blockers,
            "accepted": bool(convergence_indicators.get("target_vs_small_gate_convergence_accepted")),
            "manual_gis_visual_qa_status": require_text(
                convergence_indicators.get("manual_gis_visual_qa_status"), "convergence_record.assessment.evidence.convergence_indicators.manual_gis_visual_qa_status"
            ),
            "validation_debug_output_volume_status": require_text(
                convergence_indicators.get("validation_debug_output_volume_status"),
                "convergence_record.assessment.evidence.convergence_indicators.validation_debug_output_volume_status",
            ),
            "required_gates": require_mapping(convergence_record.get("required_gates"), "convergence_record.required_gates"),
        },
        "ensemble_feasibility": {
            "record_path": str(ensemble_feasibility_record_path),
            "decision": feasibility_decision,
            "output_budget_status": require_text(
                feasibility_output_budget.get("status"), "ensemble_feasibility_record.output_budget_assessment.status"
            ),
            "interpretation": require_text(
                feasibility_output_budget.get("interpretation"), "ensemble_feasibility_record.output_budget_assessment.interpretation"
            ),
            "blockers": feasibility_blockers,
        },
        "local_output_audit": local_output_audit,
        "provenance": {
            "current_pressure_record_path": str(current_pressure_record_path),
            "bounded_profile_record_path": str(bounded_profile_record_path),
            "output_budget_record_path": str(output_budget_record_path),
            "convergence_record_path": str(convergence_record_path),
            "ensemble_feasibility_record_path": str(ensemble_feasibility_record_path),
            "bounded_profile_run_environment": bounded_run_environment,
            "bounded_profile_input_freeze": bounded_input_freeze,
            "selected_dt04_output_evidence": selected_dt04,
            "bounded_profile_case_path": require_text(target_validation_run.get("case_path"), "target_gate_record.execution_evidence.validation_run.case_path"),
            "bounded_profile_limitations": bounded_limitations,
            "output_budget_file_family_pressure": require_text(
                inode_budget.get("file_family_pressure"), "output_budget_record.inode_and_file_family_budget.file_family_pressure"
            ),
            "convergence_classification": require_text(
                convergence_assessment.get("current_classification"), "convergence_record.assessment.current_classification"
            ),
            "ensemble_feasibility_decision": feasibility_decision,
        },
        "uncertainty_reduced": [
            "The selected profile controls are explicit: summary-only conditional curves, no grid CSV, no plots, and two local reducer workers.",
            "Hazard-side output volume is bounded in the measured Balfrin reproduction record.",
            "Validation-side file and byte pressure is now measured separately from hazard-side output volume.",
            "The output-budget gate now records the file-family pressure label validation_debug_artifacts.",
        ],
        "remaining_unresolved": [
            "Conditional hazard-map convergence remains inconclusive.",
            "Validation debug output remains retained as a blocker for the next scale increase.",
            "Local ignored manifests are absent in this clean checkout, so local output audit remains blocked_missing_outputs.",
            "Scale-up is not authorized by the selected output-budget gate.",
        ],
        "limitations": bounded_limitations
        + [
            "This summary does not change physics, defaults, thresholds, release assumptions, validation cases, or baselines.",
            "The report is diagnostic and does not authorize scale-up.",
        ],
    }


def classify_acceptance(*, convergence_status: str, output_budget_status: str, local_output_status: str, feasibility_decision: str) -> str:
    if output_budget_status == "blocker_retained" or local_output_status == "blocked_missing_outputs":
        return "inconclusive"
    if convergence_status == "inconclusive" or feasibility_decision == "no_go":
        return "inconclusive"
    if convergence_status == "pass" and output_budget_status == "complete" and local_output_status == "available" and feasibility_decision != "no_go":
        return "accepted_conditional_diagnostic_pilot"
    if output_budget_status == "no_go" or feasibility_decision == "no_go":
        return "no_go"
    return "inconclusive"


def summarize_local_outputs(run_evidence: dict[str, Any]) -> dict[str, Any]:
    paths = [
        require_text(run_evidence.get("validation_manifest_path"), "current_pressure_record.run_evidence.validation_manifest_path"),
        require_text(run_evidence.get("hazard_manifest_path"), "current_pressure_record.run_evidence.hazard_manifest_path"),
        require_text(run_evidence.get("map_package_manifest_path"), "current_pressure_record.run_evidence.map_package_manifest_path"),
        require_text(run_evidence.get("pilot_gis_package_manifest_path"), "current_pressure_record.run_evidence.pilot_gis_package_manifest_path"),
    ]
    checked_paths = [str(path) for path in paths]
    missing_paths = [str(path) for path in paths if not Path(path).exists()]
    if missing_paths:
        return {
            "status": "blocked_missing_outputs",
            "checked_paths": checked_paths,
            "missing_paths": missing_paths,
        }

    summaries = [summarize_tree(Path(path).parent) for path in paths]
    total_files = sum(item["file_count"] for item in summaries)
    total_bytes = sum(item["total_bytes"] for item in summaries)
    return {
        "status": "available",
        "checked_paths": checked_paths,
        "missing_paths": [],
        "summaries": summaries,
        "total_file_count": total_files,
        "total_bytes": total_bytes,
    }


def summarize_tree(path: Path) -> dict[str, Any]:
    file_count = 0
    total_bytes = 0
    if path.exists():
        for child in path.rglob("*"):
            if child.is_file():
                file_count += 1
                total_bytes += child.stat().st_size
    return {"path": str(path), "file_count": file_count, "total_bytes": total_bytes}


def render_markdown(summary: dict[str, Any]) -> str:
    bounded = summary["bounded_profile"]
    current = summary["current_pressure"]
    budget = summary["output_budget_gate"]
    convergence = summary["convergence"]
    feasibility = summary["ensemble_feasibility"]
    local = summary["local_output_audit"]
    savings = summary["measured_savings"]
    provenance = summary["provenance"]

    lines = [
        "# Bounded Validation Output Profile Summary",
        "",
        f"Final classification: `{summary['acceptance_classification']}`",
        f"Scale-up authorized: `{summary['scale_up_authorized']}`",
        f"Local output audit: `{local['status']}`",
        "",
        "## Bounded Profile",
        "",
        f"- Case id: `{summary['case_id']}`",
        f"- Case path: `{summary['case_path']}`",
        f"- Run id: `{bounded['run_id']}`",
        f"- Profile: `{bounded['profile']}`",
        f"- Validation command: `{bounded['command_recipe']['validation_command']}`",
        f"- Conditional-curve export: `{bounded['command_recipe']['profile_controls']['conditional_curve_export']}`",
        f"- Grid CSV export: `{bounded['command_recipe']['profile_controls']['grid_csv_export']}`",
        f"- Plots enabled: `{bounded['command_recipe']['profile_controls']['no_plots'] is False}`",
        f"- Trajectory workers: `{bounded['command_recipe']['profile_controls']['trajectory_workers']}`",
        f"- Reducer workers: `{bounded['command_recipe']['profile_controls']['reducer_workers']}`",
        f"- Hazard output files: `{bounded['hazard_output_file_count']}`",
        f"- Hazard output bytes: `{bounded['hazard_output_bytes']}`",
        f"- Validation output files: `{bounded['validation_output_file_count']}`",
        f"- Validation output bytes: `{bounded['validation_output_bytes']}`",
        "",
        "Included output classes:",
    ]
    lines.extend(f"- `{value}`" for value in bounded["included_output_classes"])
    lines.append("")
    lines.append("Excluded output classes:")
    lines.extend(f"- `{value}`" for value in bounded["excluded_output_classes"])
    lines.extend(
        [
            "",
            "## Measured Pressure",
            "",
            f"- Current file count: `{current['current_file_count']}`",
            f"- Current total bytes: `{current['current_total_bytes']}`",
            f"- File ceiling: `{current['file_count_ceiling']}`",
            f"- Byte ceiling: `{current['byte_ceiling']}`",
            f"- File-count margin: `{current['file_count_margin']}`",
            f"- Byte margin: `{current['byte_margin']}`",
            f"- Inode/file-family pressure: `{budget['inode_and_file_family_budget']['file_family_pressure']}`",
            "",
            "## Measured Deltas vs Selected Target Budget",
            "",
            f"- Validation file-count delta: `{savings['validation_output_file_count_delta_vs_target_budget']}`",
            f"- Validation byte delta: `{savings['validation_output_bytes_delta_vs_target_budget']}`",
            f"- Hazard file-count delta: `{savings['hazard_output_file_count_delta_vs_target_budget']}`",
            f"- Hazard byte delta: `{savings['hazard_output_bytes_delta_vs_target_budget']}`",
            "",
            "## Convergence And Blockers",
            "",
            f"- Convergence status: `{convergence['status']}`",
            f"- Validation debug output status: `{convergence['validation_debug_output_volume_status']}`",
            f"- Output-budget status: `{budget['current_classification']}`",
            f"- QA status: `{budget['qa_status']}`",
            f"- Feasibility decision: `{feasibility['decision']}`",
            "",
            "## Local Output Audit",
            "",
            f"- Status: `{local['status']}`",
        ]
    )
    if local["missing_paths"]:
        lines.extend(f"- Missing path: `{path}`" for path in local["missing_paths"])
    lines.extend(
        [
            "",
            "## Uncertainty Reduced",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in summary["uncertainty_reduced"])
    lines.extend(
        [
            "",
            "## Remaining Unresolved",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in summary["remaining_unresolved"])
    lines.extend(
        [
            "",
            "## Provenance",
            "",
            f"- `current_pressure_record_path`: `{provenance['current_pressure_record_path']}`",
            f"- `bounded_profile_record_path`: `{provenance['bounded_profile_record_path']}`",
            f"- `output_budget_record_path`: `{provenance['output_budget_record_path']}`",
            f"- `convergence_record_path`: `{provenance['convergence_record_path']}`",
            f"- `ensemble_feasibility_record_path`: `{provenance['ensemble_feasibility_record_path']}`",
            f"- `output_budget_file_family_pressure`: `{provenance['output_budget_file_family_pressure']}`",
            f"- `convergence_classification`: `{provenance['convergence_classification']}`",
            f"- `ensemble_feasibility_decision`: `{provenance['ensemble_feasibility_decision']}`",
            "",
            "## Limitations",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in summary["limitations"])
    return "\n".join(lines) + "\n"


def require_existing_path(path: Path, label: str) -> Path:
    if not path.exists():
        raise BoundedValidationOutputProfileError(f"{label} does not exist: {path}")
    return path


def read_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - keep path context.
        raise BoundedValidationOutputProfileError(f"failed to read YAML {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise BoundedValidationOutputProfileError(f"YAML document must be an object: {path}")
    return data


def require_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise BoundedValidationOutputProfileError(f"{label} must be a mapping")
    return value


def require_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise BoundedValidationOutputProfileError(f"{label} must be a list")
    return value


def require_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise BoundedValidationOutputProfileError(f"{label} must be a non-empty string")
    return value


def require_positive_int(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise BoundedValidationOutputProfileError(f"{label} must be a positive integer")
    return value


if __name__ == "__main__":
    raise SystemExit(main())
