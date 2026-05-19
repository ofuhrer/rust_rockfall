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
VALIDATION_OUTPUT_DEFAULT_MODE = "rebuildable_reduced_output"
REPLAY_CRITICAL_OUTPUT_CLASSES = [
    "manifest_json",
    "diagnostics_json",
    "trajectory_csv",
    "trajectory_metadata_csv",
    "ensemble_deposition_csv",
    "impact_events_csv",
    "stop_state_summary_csv",
]
DEBUG_OUTPUT_CLASSES = [
    "ensemble_trajectories_dir",
    "ensemble_impact_events_dir",
    "ensemble_impact_events_parquet",
    "ensemble_impact_terrain_material_dir",
]


class BoundedValidationOutputProfileError(ValueError):
    """User-facing bounded output profile summary error."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--current-pressure-record", type=Path, default=DEFAULT_CURRENT_PRESSURE_RECORD)
    parser.add_argument("--bounded-profile-record", type=Path, default=DEFAULT_BOUNDED_PROFILE_RECORD)
    parser.add_argument("--output-budget-record", type=Path, default=DEFAULT_OUTPUT_BUDGET_RECORD)
    parser.add_argument("--convergence-record", type=Path, default=DEFAULT_CONVERGENCE_RECORD)
    parser.add_argument("--ensemble-feasibility-record", type=Path, default=DEFAULT_ENSEMBLE_FEASIBILITY_RECORD)
    parser.add_argument("--validation-output-manifest", type=Path, default=None)
    parser.add_argument("--validation-output-baseline-manifest", type=Path, default=None)
    parser.add_argument("--validation-output-reduced-manifest", type=Path, default=None)
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
            validation_output_manifest_path=args.validation_output_manifest,
            validation_output_baseline_manifest_path=args.validation_output_baseline_manifest,
            validation_output_reduced_manifest_path=args.validation_output_reduced_manifest,
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
            f"{summary['final_classification']} "
            f"(profile={summary['bounded_profile']['profile']}, "
            f"validation_mode={summary['validation_output_mode'] or 'unavailable'}, "
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
    validation_output_manifest_path: Path | None = None,
    validation_output_baseline_manifest_path: Path | None = None,
    validation_output_reduced_manifest_path: Path | None = None,
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

    validation_output_audit = summarize_validation_output_audit(
        validation_output_manifest_path
        if validation_output_manifest_path is not None
        else optional_existing_path(require_text(current_evidence.get("validation_manifest_path"), "current_pressure_record.run_evidence.validation_manifest_path"))
    )
    validation_output_comparison = summarize_validation_output_comparison(
        baseline_manifest_path=validation_output_baseline_manifest_path,
        reduced_manifest_path=validation_output_reduced_manifest_path,
    )
    validation_output_inventory = build_validation_output_inventory(validation_output_comparison)
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
        "feasibility_decision": feasibility_decision,
        "scale_up_authorized": False,
        "validation_output_mode": validation_output_comparison.get("validation_output_mode"),
        "baseline_file_count": validation_output_comparison.get("baseline_file_count"),
        "reduced_file_count": validation_output_comparison.get("reduced_file_count"),
        "baseline_bytes": validation_output_comparison.get("baseline_bytes"),
        "reduced_bytes": validation_output_comparison.get("reduced_bytes"),
        "reduction_file_count_delta": validation_output_comparison.get("reduction_file_count_delta"),
        "reduction_bytes_delta": validation_output_comparison.get("reduction_bytes_delta"),
        "retained_output_classes": validation_output_comparison.get("retained_output_classes", []),
        "omitted_or_sampled_output_classes": validation_output_comparison.get("omitted_or_sampled_output_classes", []),
        "required_provenance_retained": bool(validation_output_comparison.get("required_provenance_retained")),
        "validation_output_reduced": bool(validation_output_comparison.get("validation_output_reduced")),
        "validation_output_blocker_status": require_text(
            validation_debug_budget.get("status"), "output_budget_record.output_profile.validation_debug_output_budget.status"
        ),
        "file_family_pressure": require_text(inode_budget.get("file_family_pressure"), "output_budget_record.inode_and_file_family_budget.file_family_pressure"),
        "defaults_changed": bool(bounded_claim_boundary.get("changes_defaults")),
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
        "validation_output_audit": validation_output_audit,
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
        "validation_output_comparison": validation_output_comparison,
        "validation_output_inventory": validation_output_inventory,
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
            "Validation output families can be audited from a run manifest when the ignored manifest is locally available.",
        ],
        "remaining_unresolved": build_remaining_unresolved(
            local_output_status=local_output_audit["status"],
            validation_output_reduced=bool(validation_output_comparison.get("validation_output_reduced")),
        ),
        "limitations": bounded_limitations
        + [
            "This summary does not change physics, defaults, thresholds, release assumptions, validation cases, or baselines.",
            "The report is diagnostic and does not authorize scale-up.",
        ],
    }


def classify_acceptance(*, convergence_status: str, output_budget_status: str, local_output_status: str, feasibility_decision: str) -> str:
    if feasibility_decision == "no_go" and output_budget_status == "blocker_retained":
        return "no_go"
    if feasibility_decision == "no_go" or output_budget_status == "no_go":
        return "no_go"
    if output_budget_status == "blocker_retained" or local_output_status == "blocked_missing_outputs":
        return "inconclusive"
    if convergence_status == "inconclusive":
        return "inconclusive"
    if convergence_status == "pass" and output_budget_status == "complete" and local_output_status == "available":
        return "accepted_conditional_diagnostic_pilot"
    return "inconclusive"


def build_remaining_unresolved(*, local_output_status: str, validation_output_reduced: bool) -> list[str]:
    remaining = [
        "Conditional hazard-map convergence remains inconclusive.",
        "Scale-up is not authorized by the selected output-budget gate.",
    ]
    if validation_output_reduced:
        remaining.insert(
            1,
            "Validation debug output is reduced for the supplied comparison manifests, but target-scale scale-up still requires accepted convergence and output-budget evidence.",
        )
    else:
        remaining.insert(
            1,
            "Validation debug output remains retained as a blocker for the next scale increase.",
        )
    if local_output_status == "blocked_missing_outputs":
        remaining.insert(
            -1,
            "Local ignored manifests are absent in this clean checkout, so local output audit remains blocked_missing_outputs.",
        )
    else:
        remaining.insert(
            -1,
            "Local ignored manifests are available for this audit, but generated outputs remain uncommitted and must be regenerated or staged on other checkouts.",
        )
    return remaining


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


def summarize_validation_output_audit(manifest_path: Path | None) -> dict[str, Any]:
    if manifest_path is None:
        return {
            "status": "blocked_missing_outputs",
            "manifest_path": None,
            "required_for_audit": ["validation_manifest"],
            "families": [],
            "reduced": False,
            "validation_output_mode": None,
        }
    if not manifest_path.exists():
        return {
            "status": "blocked_missing_outputs",
            "manifest_path": str(manifest_path),
            "required_for_audit": ["validation_manifest"],
            "families": [],
            "reduced": False,
            "validation_output_mode": None,
        }
    manifest = read_json(manifest_path)
    summary = summarize_validation_output_manifest(manifest, manifest_path)
    summary["reduced"] = False
    return summary


def summarize_validation_output_comparison(
    *,
    baseline_manifest_path: Path | None,
    reduced_manifest_path: Path | None,
) -> dict[str, Any]:
    if baseline_manifest_path is None or reduced_manifest_path is None:
        missing_paths = [
            label
            for label, path in (
                ("baseline_validation_manifest", baseline_manifest_path),
                ("reduced_validation_manifest", reduced_manifest_path),
            )
            if path is None
        ]
        return {
            "status": "blocked_missing_outputs",
            "baseline_manifest_path": str(baseline_manifest_path) if baseline_manifest_path is not None else None,
            "reduced_manifest_path": str(reduced_manifest_path) if reduced_manifest_path is not None else None,
            "missing_paths": missing_paths,
            "validation_output_mode": None,
            "baseline_file_count": None,
            "reduced_file_count": None,
            "baseline_bytes": None,
            "reduced_bytes": None,
            "reduction_file_count_delta": None,
            "reduction_bytes_delta": None,
            "retained_output_classes": [],
            "omitted_or_sampled_output_classes": [],
            "required_provenance_retained": False,
            "validation_output_reduced": False,
        }
    missing_paths = [path for path in (baseline_manifest_path, reduced_manifest_path) if not path.exists()]
    if missing_paths:
        return {
            "status": "blocked_missing_outputs",
            "baseline_manifest_path": str(baseline_manifest_path),
            "reduced_manifest_path": str(reduced_manifest_path),
            "missing_paths": [str(path) for path in missing_paths],
            "validation_output_mode": None,
            "baseline_file_count": None,
            "reduced_file_count": None,
            "baseline_bytes": None,
            "reduced_bytes": None,
            "reduction_file_count_delta": None,
            "reduction_bytes_delta": None,
            "retained_output_classes": [],
            "omitted_or_sampled_output_classes": [],
            "required_provenance_retained": False,
            "validation_output_reduced": False,
        }

    baseline_manifest = read_json(baseline_manifest_path)
    reduced_manifest = read_json(reduced_manifest_path)
    baseline_audit = summarize_validation_output_manifest(baseline_manifest, baseline_manifest_path)
    reduced_audit = summarize_validation_output_manifest(reduced_manifest, reduced_manifest_path)

    if baseline_audit["status"] != "available" or reduced_audit["status"] != "available":
        return {
            "status": "blocked_invalid_inputs",
            "baseline_manifest_path": str(baseline_manifest_path),
            "reduced_manifest_path": str(reduced_manifest_path),
            "missing_paths": [],
            "validation_output_mode": None,
            "baseline_file_count": None,
            "reduced_file_count": None,
            "baseline_bytes": None,
            "reduced_bytes": None,
            "reduction_file_count_delta": None,
            "reduction_bytes_delta": None,
            "retained_output_classes": [],
            "omitted_or_sampled_output_classes": [],
            "required_provenance_retained": False,
            "validation_output_reduced": False,
        }

    baseline_families = {family["family"]: family for family in baseline_audit["families"]}
    reduced_families = {family["family"]: family for family in reduced_audit["families"]}
    retained_output_classes: list[str] = []
    omitted_or_sampled_output_classes: list[str] = []
    for family_name in sorted(baseline_families):
        baseline_family = baseline_families[family_name]
        reduced_family = reduced_families.get(family_name)
        if reduced_family is None:
            omitted_or_sampled_output_classes.append(family_name)
            continue
        if (
            baseline_family["file_count"] == reduced_family["file_count"]
            and baseline_family["total_bytes"] == reduced_family["total_bytes"]
        ):
            retained_output_classes.append(family_name)
        else:
            omitted_or_sampled_output_classes.append(family_name)

    reduced_mode = reduced_manifest.get("validation_output_mode")
    baseline_file_count = baseline_audit["total_file_count"]
    reduced_file_count = reduced_audit["total_file_count"]
    baseline_bytes = baseline_audit["total_bytes"]
    reduced_bytes = reduced_audit["total_bytes"]
    required_provenance_retained = (
        require_text(reduced_manifest.get("schema_version"), "reduced_validation_manifest.schema_version") == "run_manifest_v1"
        and isinstance(reduced_manifest.get("performance"), dict)
        and isinstance(reduced_manifest.get("trajectory_metadata"), dict)
        and bool(reduced_manifest.get("outputs"))
        and any(entry["family"] == "diagnostics_json" for entry in reduced_audit["families"])
        and any(entry["family"] == "trajectory_metadata_csv" for entry in reduced_audit["families"])
        and reduced_mode == "summary_only"
    )
    return {
        "status": "available",
        "baseline_manifest_path": str(baseline_manifest_path),
        "reduced_manifest_path": str(reduced_manifest_path),
        "missing_paths": [],
        "validation_output_mode": reduced_mode,
        "baseline_file_count": baseline_file_count,
        "reduced_file_count": reduced_file_count,
        "baseline_bytes": baseline_bytes,
        "reduced_bytes": reduced_bytes,
        "reduction_file_count_delta": baseline_file_count - reduced_file_count,
        "reduction_bytes_delta": baseline_bytes - reduced_bytes,
        "retained_output_classes": retained_output_classes,
        "omitted_or_sampled_output_classes": omitted_or_sampled_output_classes,
        "required_provenance_retained": required_provenance_retained,
        "validation_output_reduced": (baseline_file_count > reduced_file_count)
        or (baseline_bytes > reduced_bytes),
        "baseline": baseline_audit,
        "reduced": reduced_audit,
    }


def summarize_validation_output_manifest(manifest: dict[str, Any], manifest_path: Path) -> dict[str, Any]:
    outputs = require_list(manifest.get("outputs"), "validation_manifest.outputs")
    families: list[dict[str, Any]] = []
    total_file_count = 0
    total_bytes = 0
    for output in outputs:
        entry = require_mapping(output, "validation_manifest.output")
        family = classify_validation_output_family(entry)
        file_count = require_positive_int(entry.get("file_count"), f"validation_manifest.outputs[{family}].file_count")
        total = require_positive_int(entry.get("total_bytes"), f"validation_manifest.outputs[{family}].total_bytes")
        families.append(
            {
                "family": family,
                "kind": require_text(entry.get("kind"), "validation_manifest.output.kind"),
                "format": require_text(entry.get("format"), "validation_manifest.output.format"),
                "path": require_text(entry.get("path"), "validation_manifest.output.path"),
                "file_count": file_count,
                "total_bytes": total,
                "row_count": entry.get("row_count"),
                "skipped_empty_files": entry.get("skipped_empty_files"),
                "sha256": entry.get("sha256"),
            }
        )
        total_file_count += file_count
        total_bytes += total
    families.sort(key=lambda item: item["family"])
    return {
        "status": "available",
        "manifest_path": str(manifest_path),
        "validation_output_mode": manifest.get("validation_output_mode"),
        "family_count": len(families),
        "total_file_count": total_file_count,
        "total_bytes": total_bytes,
        "families": families,
    }


def build_validation_output_inventory(validation_output_comparison: dict[str, Any]) -> dict[str, Any]:
    reduced_families = {family["family"]: family for family in validation_output_comparison.get("reduced", {}).get("families", [])}
    baseline_families = {family["family"]: family for family in validation_output_comparison.get("baseline", {}).get("families", [])}
    replay_critical_budgets = {
        family: {
            "file_count": int(reduced_families.get(family, {}).get("file_count", 0) or 0),
            "bytes": int(reduced_families.get(family, {}).get("total_bytes", 0) or 0),
            "present_in_reduced_manifest": family in reduced_families,
        }
        for family in REPLAY_CRITICAL_OUTPUT_CLASSES
    }
    debug_family_budgets = {
        family: {
            "file_count": int(baseline_families.get(family, {}).get("file_count", 0) or 0),
            "bytes": int(baseline_families.get(family, {}).get("total_bytes", 0) or 0),
            "suppressed_in_reduced_manifest": family not in reduced_families,
        }
        for family in DEBUG_OUTPUT_CLASSES
    }
    return {
        "validation_output_mode": VALIDATION_OUTPUT_DEFAULT_MODE,
        "comparison_validation_output_mode": validation_output_comparison.get("validation_output_mode"),
        "replay_critical_output_classes": REPLAY_CRITICAL_OUTPUT_CLASSES,
        "debug_output_classes": DEBUG_OUTPUT_CLASSES,
        "replay_critical_family_budgets": replay_critical_budgets,
        "debug_family_budgets": debug_family_budgets,
        "reduced_inventory_present": bool(reduced_families),
    }


def classify_validation_output_family(entry: dict[str, Any]) -> str:
    kind = require_text(entry.get("kind"), "validation_manifest.output.kind")
    format_name = require_text(entry.get("format"), "validation_manifest.output.format")
    if kind == "ensemble_trajectories":
        return "ensemble_trajectories_dir"
    if kind == "ensemble_impact_events" and format_name == "csv_directory":
        return "ensemble_impact_events_dir"
    if kind == "ensemble_impact_events" and format_name == "parquet":
        return "ensemble_impact_events_parquet"
    if kind == "ensemble_impact_terrain_material" and format_name == "csv_directory":
        return "ensemble_impact_terrain_material_dir"
    if kind == "trajectory_metadata":
        return "trajectory_metadata_csv"
    if kind == "ensemble_deposition":
        return "ensemble_deposition_csv"
    if kind == "release_zone_deposition":
        return "release_zone_deposition_csv"
    if kind == "stop_state":
        return "stop_state_summary_csv"
    if kind == "terrain_material_exposure":
        return "terrain_material_exposure_csv"
    if kind == "manifest":
        return "manifest_json"
    if kind == "map_package_manifest":
        return "map_package_manifest_json"
    if kind == "pilot_gis_package_manifest":
        return "pilot_gis_package_manifest_json"
    if kind == "diagnostics":
        return f"{kind}_{format_name}"
    return f"{kind}_{format_name}"


def summarize_tree(path: Path) -> dict[str, Any]:
    file_count = 0
    total_bytes = 0
    if path.exists():
        for child in path.rglob("*"):
            if child.is_file():
                file_count += 1
                total_bytes += child.stat().st_size
    return {"path": str(path), "file_count": file_count, "total_bytes": total_bytes}


def read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - keep path context.
        raise BoundedValidationOutputProfileError(f"failed to read JSON {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise BoundedValidationOutputProfileError(f"JSON document must be an object: {path}")
    return data


def optional_existing_path(path: Path | str) -> Path | None:
    candidate = Path(path)
    return candidate if candidate.exists() else None


def render_markdown(summary: dict[str, Any]) -> str:
    bounded = summary["bounded_profile"]
    current = summary["current_pressure"]
    budget = summary["output_budget_gate"]
    convergence = summary["convergence"]
    feasibility = summary["ensemble_feasibility"]
    local = summary["local_output_audit"]
    validation_audit = summary["validation_output_audit"]
    comparison = summary["validation_output_comparison"]
    savings = summary["measured_savings"]
    provenance = summary["provenance"]

    lines = [
        "# Bounded Validation Output Profile Summary",
        "",
        f"Final classification: `{summary['final_classification']}`",
        f"Feasibility decision: `{summary['feasibility_decision']}`",
        f"Scale-up authorized: `{summary['scale_up_authorized']}`",
        f"Validation output reduced: `{summary['validation_output_reduced']}`",
        f"Validation output blocker status: `{summary['validation_output_blocker_status']}`",
        f"File-family pressure: `{summary['file_family_pressure']}`",
        f"Defaults changed: `{summary['defaults_changed']}`",
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
    validation_inventory = summary["validation_output_inventory"]
    lines.extend(
        [
            "",
            "Validation output inventory:",
            f"- Validation output mode: `{validation_inventory['validation_output_mode']}`",
            f"- Comparison validation output mode: `{validation_inventory['comparison_validation_output_mode']}`",
            "- Replay-critical output classes:",
        ]
    )
    lines.extend(f"- `{value}`" for value in validation_inventory["replay_critical_output_classes"])
    lines.append("- Debug output classes:")
    lines.extend(f"- `{value}`" for value in validation_inventory["debug_output_classes"])
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
            "## Validation Output Audit",
            "",
            f"- Status: `{validation_audit['status']}`",
            f"- Manifest path: `{validation_audit['manifest_path']}`",
            f"- Reduced: `{validation_audit['reduced']}`",
            f"- Validation output mode: `{validation_audit.get('validation_output_mode')}`",
        ]
    )
    if validation_audit["status"] == "available":
        lines.extend(
            [
                f"- Family count: `{validation_audit['family_count']}`",
                f"- Total file count: `{validation_audit['total_file_count']}`",
                f"- Total bytes: `{validation_audit['total_bytes']}`",
                "",
                "Validation output families:",
            ]
        )
        for family in validation_audit["families"]:
            lines.append(
                f"- `{family['family']}`: files=`{family['file_count']}` bytes=`{family['total_bytes']}` kind=`{family['kind']}` format=`{family['format']}`"
            )
    else:
        lines.extend(
            [
                "- Validation output families are blocked until the ignored manifest is locally available.",
                "",
                "Required for audit:",
            ]
        )
        lines.extend(f"- `{value}`" for value in validation_audit["required_for_audit"])
    lines.extend(
        [
            "",
            "## Validation Output Comparison",
            "",
            f"- Status: `{comparison['status']}`",
            f"- Validation output mode: `{summary['validation_output_mode']}`",
            f"- Baseline file count: `{summary['baseline_file_count']}`",
            f"- Reduced file count: `{summary['reduced_file_count']}`",
            f"- Baseline bytes: `{summary['baseline_bytes']}`",
            f"- Reduced bytes: `{summary['reduced_bytes']}`",
            f"- Reduction file-count delta: `{summary['reduction_file_count_delta']}`",
            f"- Reduction byte delta: `{summary['reduction_bytes_delta']}`",
            f"- Required provenance retained: `{summary['required_provenance_retained']}`",
        ]
    )
    if comparison["status"] == "available":
        lines.append("")
        lines.append("Retained output classes:")
        lines.extend(f"- `{item}`" for item in summary["retained_output_classes"])
        lines.append("")
        lines.append("Omitted or sampled output classes:")
        lines.extend(f"- `{item}`" for item in summary["omitted_or_sampled_output_classes"])
    elif comparison.get("missing_paths"):
        lines.append("")
        lines.append("Missing comparison inputs:")
        lines.extend(f"- `{item}`" for item in comparison["missing_paths"])
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
