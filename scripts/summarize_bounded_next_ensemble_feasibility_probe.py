#!/usr/bin/env python3
"""Summarize a bounded next-ensemble feasibility probe without executing it.

The helper is read-only. It composes the measured closure-gap, bounded-output,
runtime-scaling, rebuildable-reduced-output, and single-job-sufficiency
evidence into one feasibility report for the smallest additional same-scale
probe that is currently worth describing. It does not run an ensemble or
authorize scale-up.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "bounded_next_ensemble_feasibility_probe_v1"
REDUCED_CASE = ROOT / "tests/fixtures/rebuildable_reduced_output/tschamut_public_target_gate_rebuildable_reduced_case.yaml"
REDUCED_VALIDATION_ROOT = ROOT / "validation/private/tschamut_public_pilot/target_gate_v1_rebuildable_reduced"
REDUCED_VALIDATION_MANIFEST = (
    REDUCED_VALIDATION_ROOT / "validation_tschamut_public_target_gate_v1_rebuildable_reduced_manifest.json"
)
TARGET_GATE_RECORD = ROOT / "validation/pilot_runs/tschamut_public_scalable_conditional_target_gate_v1.yaml"


def _load_module(module_name: str, filename: str):
    path = ROOT / "scripts" / filename
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise FeasibilityProbeError(f"failed to load helper module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


CLOSURE_GAP = _load_module("bounded_next_ensemble_closure_gap", "summarize_tschamut_closure_gap_deltas.py")
REDUCED_OUTPUT = _load_module("bounded_next_ensemble_reduced_output_profile", "check_hazard_rebuild_output_profile.py")
RUNTIME_SCALING = _load_module("bounded_next_ensemble_runtime_scaling", "summarize_bounded_reducer_runtime_scaling.py")
SINGLE_JOB = _load_module("bounded_next_ensemble_single_job", "summarize_balfrin_single_job_execution.py")


class FeasibilityProbeError(ValueError):
    """User-facing feasibility probe error."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("json", "text"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    args = parser.parse_args(argv)

    try:
        report = build_report()
    except FeasibilityProbeError as exc:
        print(f"bounded next-ensemble feasibility probe error: {exc}", file=sys.stderr)
        return 2

    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text_report(report))
    return 0


def build_report() -> dict[str, Any]:
    closure_gap = CLOSURE_GAP.build_report()
    reduced_output = REDUCED_OUTPUT.build_report(list(REDUCED_OUTPUT.DEFAULT_PROFILE_SPECS))
    runtime_scaling = RUNTIME_SCALING.build_report(RUNTIME_SCALING.DEFAULT_ARTIFACTS)
    single_job = SINGLE_JOB.build_summary()
    reduced_case = load_yaml(REDUCED_CASE)
    target_gate = load_yaml(TARGET_GATE_RECORD)

    reduced_profile = reduced_output["reduced_profile"]
    rebuildable_reduced_profile = reduced_output["rebuildable_reduced_profile"]
    summary_only_profile = next(
        profile for profile in reduced_output["profiles"] if profile["profile_id"] == "target_summary_only"
    )
    reduced_profile_classification = reduced_output["profile_classifications"].get("target_rebuildable_reduced")
    if reduced_profile_classification != "rebuildable_reduced_output":
        raise FeasibilityProbeError(
            "native rebuildable reduced output is not classified as rebuildable_reduced_output"
        )

    target_validation_bytes = int(target_gate["execution_evidence"]["validation_run"]["output_total_bytes"])
    target_validation_files = int(target_gate["execution_evidence"]["validation_run"]["output_file_count"])
    target_hazard_bytes = int(target_gate["execution_evidence"]["hazard_run"]["output_total_bytes"])
    target_hazard_files = int(target_gate["execution_evidence"]["hazard_run"]["output_file_count"])
    reduced_bytes = int(reduced_profile["byte_count"])
    reduced_files = int(reduced_profile["file_count"])

    output_byte_ratio_to_target_validation = reduced_bytes / target_validation_bytes
    output_file_ratio_to_target_validation = reduced_files / target_validation_files
    output_byte_ratio_to_target_hazard = reduced_bytes / target_hazard_bytes
    output_file_ratio_to_target_hazard = reduced_files / target_hazard_files

    go_criteria = [
        "run only if the probe stays on the native rebuildable_reduced_output path with the frozen case at tests/fixtures/rebuildable_reduced_output/tschamut_public_target_gate_rebuildable_reduced_case.yaml",
        "run only if the expected output families remain trajectory, ensemble_deposition, impact_events_csv, trajectory_metadata, diagnostics, and the manifest family with no full-debug regression",
        "run only if the expected output root remains bounded below the measured full target validation root and full target hazard root",
        "run only if the probe is being used to answer the unresolved convergence interpretation rather than to tune physics, seed selection, or output controls",
    ]
    no_go_criteria = [
        "do not run if the probe would expand to the 1,000-trajectory full target validation profile or reintroduce the debug-heavy output families that keep the current gate inconclusive",
        "do not run if manual GIS/QGIS review, obstacle-context review, or validation-debug-output reduction would still be required before the same question could be answered",
        "do not run if the command would need distributed execution, scale-up authorization, or parameter tuning to be meaningful",
        "do not run if the command-plan entry cannot remain read-only and explicitly deferred until authorized",
    ]

    command = (
        "PYENV_VERSION=system CARGO_TARGET_DIR=/tmp/rust-rockfall-target cargo run -- validate --case "
        "tests/fixtures/rebuildable_reduced_output/tschamut_public_target_gate_rebuildable_reduced_case.yaml"
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "probe_status": "deferred_pending_authorization",
        "read_only": True,
        "scale_up_authorized": False,
        "distributed_execution_authorized": False,
        "operational_claims_allowed": False,
        "target_gate_record_path": str(TARGET_GATE_RECORD),
        "reduced_case_path": str(REDUCED_CASE),
        "proposed_probe": {
            "probe_id": "tschamut_native_rebuildable_reduced_next_probe",
            "validation_output_mode": reduced_case["outputs"]["validation_output_mode"],
            "seed": int(reduced_case["random"]["seed"]),
            "ensemble_size": int(target_gate["execution_evidence"]["validation_run"]["validation_simulated_trajectory_count"]),
            "scenario_id": str(reduced_case["probabilistic_metadata"]["scenario_id"]),
            "source_zone_id": str(reduced_case["hazard_probability"]["filters"]["source_zone_ids"][0]),
            "release_cell_count": int(target_gate["target_execution_plan"]["release_cell_count"]),
            "trajectory_count": int(target_gate["execution_evidence"]["validation_run"]["validation_simulated_trajectory_count"]),
            "expected_artifact_families": [
                "diagnostics_json",
                "manifest_json",
                "trajectory_csv",
                "ensemble_deposition_csv",
                "trajectory_metadata_csv",
                "impact_events_csv",
            ],
            "expected_output_root": str(REDUCED_VALIDATION_ROOT),
            "expected_output_manifest": str(REDUCED_VALIDATION_MANIFEST),
            "expected_output_file_count": reduced_files,
            "expected_output_bytes": reduced_bytes,
            "expected_command": command,
        },
        "measured_evidence": {
            "closure_gap_status": closure_gap["closure_gap_status"],
            "current_closure_status": closure_gap["current_closure_status"],
            "current_interpretation_status": closure_gap["current_interpretation_status"],
            "closure_limiting_layers": closure_gap["closure_limiting_layers"],
            "deferrable_layers": closure_gap["deferrable_layers"],
            "runtime_scaling_status": runtime_scaling["reducer_scaling_status"],
            "rebuildable_reduced_profile_classification": reduced_profile_classification,
            "rebuildable_reduced_profile_status": rebuildable_reduced_profile["status"],
            "rebuildable_reduced_output_file_count": reduced_files,
            "rebuildable_reduced_output_bytes": reduced_bytes,
            "target_validation_output_file_count": target_validation_files,
            "target_validation_output_bytes": target_validation_bytes,
            "target_hazard_output_file_count": target_hazard_files,
            "target_hazard_output_bytes": target_hazard_bytes,
            "summary_only_output_file_count": int(summary_only_profile["file_count"]),
            "summary_only_output_bytes": int(summary_only_profile["total_bytes"]),
            "single_job_decision": single_job["decision"],
            "single_job_sufficient_for_next_step": single_job["single_job_sufficient_for_next_step"],
        },
        "boundedness_proof": {
            "bounded_relative_to_target_validation": reduced_bytes < target_validation_bytes
            and reduced_files < target_validation_files,
            "bounded_relative_to_target_hazard": reduced_bytes < target_hazard_bytes and reduced_files < target_hazard_files,
            "output_byte_ratio_to_target_validation": output_byte_ratio_to_target_validation,
            "output_file_ratio_to_target_validation": output_file_ratio_to_target_validation,
            "output_byte_ratio_to_target_hazard": output_byte_ratio_to_target_hazard,
            "output_file_ratio_to_target_hazard": output_file_ratio_to_target_hazard,
            "boundedness_summary": (
                "The native rebuildable_reduced_output probe stays far below the measured full target validation "
                f"root ({reduced_bytes} bytes versus {target_validation_bytes} bytes) and below the measured full "
                f"target hazard root ({reduced_bytes} bytes versus {target_hazard_bytes} bytes)."
            ),
        },
        "expected_closure_question": (
            "Would a single native rebuildable_reduced_output probe with the frozen target gate case keep the "
            "closure question focused on the unresolved target-vs-small-gate convergence interpretation while "
            "avoiding the debug-heavy output families that keep the current gate inconclusive?"
        ),
        "go_no_go_criteria": {
            "go": go_criteria,
            "no_go": no_go_criteria,
        },
        "command_plan_template": {
            "command_id": "tschamut_next_ensemble_feasibility_probe_template",
            "group": "rebuildable_reduced_output",
            "site": "tschamut_same_scale",
            "description": (
                "Template the smallest additional same-scale probe with the native rebuildable_reduced_output case; "
                "execution remains deferred until explicitly authorized."
            ),
            "command": command,
            "expected_inputs": [
                str(REDUCED_CASE),
                "data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_source_zone_metadata_v1.yaml",
                "data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_scenario_table_v1.csv",
                "data/processed/swisstopo/tschamut_public_pilot/input/release_points_lv95.csv",
                "data/processed/swisstopo/tschamut_public_pilot/input/observed_deposition_lv95.csv",
                "data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_swissalti3d_metadata.yaml",
                "data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_swissalti3d_crop.asc",
            ],
            "expected_outputs": [
                str(REDUCED_VALIDATION_MANIFEST),
                str(REDUCED_VALIDATION_ROOT / "validation_tschamut_public_target_gate_v1_rebuildable_reduced_trajectory.csv"),
                str(REDUCED_VALIDATION_ROOT / "validation_tschamut_public_target_gate_v1_rebuildable_reduced_deposition.csv"),
                str(REDUCED_VALIDATION_ROOT / "validation_tschamut_public_target_gate_v1_rebuildable_reduced_impact_events.csv"),
                str(REDUCED_VALIDATION_ROOT / "validation_tschamut_public_target_gate_v1_rebuildable_reduced_trajectory_metadata.csv"),
                str(REDUCED_VALIDATION_ROOT / "validation_tschamut_public_target_gate_v1_rebuildable_reduced_metrics.json"),
            ],
            "read_only": False,
            "may_produce_ignored_outputs": True,
            "blocked_reason": "execution deferred until explicitly authorized",
            "ignored_output_paths": [str(REDUCED_VALIDATION_ROOT)],
        },
        "command_plan_status": "ready",
    }


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - user-facing path context.
        raise FeasibilityProbeError(f"failed to read YAML {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise FeasibilityProbeError(f"YAML document must be a mapping: {path}")
    return data


def render_text_report(report: dict[str, Any]) -> str:
    proposed = report["proposed_probe"]
    bounded = report["boundedness_proof"]
    evidence = report["measured_evidence"]
    lines = [
        "Bounded Next-Ensemble Feasibility Probe",
        "",
        f"- Probe status: `{report['probe_status']}`",
        f"- Read-only: `{report['read_only']}`",
        f"- Scale-up authorized: `{report['scale_up_authorized']}`",
        f"- Distributed execution authorized: `{report['distributed_execution_authorized']}`",
        f"- Operational claims allowed: `{report['operational_claims_allowed']}`",
        "",
        "## Proposed Probe",
        "",
        f"- Probe id: `{proposed['probe_id']}`",
        f"- Validation output mode: `{proposed['validation_output_mode']}`",
        f"- Seed: `{proposed['seed']}`",
        f"- Ensemble size: `{proposed['ensemble_size']}`",
        f"- Scenario id: `{proposed['scenario_id']}`",
        f"- Source zone id: `{proposed['source_zone_id']}`",
        f"- Release cell count: `{proposed['release_cell_count']}`",
        f"- Trajectory count: `{proposed['trajectory_count']}`",
        f"- Expected output file count: `{proposed['expected_output_file_count']}`",
        f"- Expected output bytes: `{proposed['expected_output_bytes']}`",
        "",
        "Expected artifact families:",
    ]
    for family in proposed["expected_artifact_families"]:
        lines.append(f"- `{family}`")
    lines.extend(
        [
            "",
            "## Boundedness Proof",
            "",
            f"- Bounded relative to target validation: `{bounded['bounded_relative_to_target_validation']}`",
            f"- Bounded relative to target hazard: `{bounded['bounded_relative_to_target_hazard']}`",
            f"- Output byte ratio to target validation: `{bounded['output_byte_ratio_to_target_validation']}`",
            f"- Output file ratio to target validation: `{bounded['output_file_ratio_to_target_validation']}`",
            f"- Output byte ratio to target hazard: `{bounded['output_byte_ratio_to_target_hazard']}`",
            f"- Output file ratio to target hazard: `{bounded['output_file_ratio_to_target_hazard']}`",
            "",
            bounded["boundedness_summary"],
            "",
            "## Expected Closure Question",
            "",
            report["expected_closure_question"],
            "",
            "## Go / No-Go Criteria",
            "",
            "Go:",
        ]
    )
    for item in report["go_no_go_criteria"]["go"]:
        lines.append(f"- {item}")
    lines.extend(["", "No-go:",])
    for item in report["go_no_go_criteria"]["no_go"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Command Plan Template",
            "",
            f"- Command id: `{report['command_plan_template']['command_id']}`",
            f"- Group: `{report['command_plan_template']['group']}`",
            f"- Command: `{report['command_plan_template']['command']}`",
            f"- Blocked reason: `{report['command_plan_template']['blocked_reason']}`",
            "",
            "## Measured Evidence",
            "",
            f"- Closure gap status: `{evidence['closure_gap_status']}`",
            f"- Current closure status: `{evidence['current_closure_status']}`",
            f"- Current interpretation status: `{evidence['current_interpretation_status']}`",
            f"- Rebuildable reduced profile classification: `{evidence['rebuildable_reduced_profile_classification']}`",
            f"- Rebuildable reduced output bytes: `{evidence['rebuildable_reduced_output_bytes']}`",
            f"- Target validation output bytes: `{evidence['target_validation_output_bytes']}`",
            f"- Target hazard output bytes: `{evidence['target_hazard_output_bytes']}`",
            f"- Single-job decision: `{evidence['single_job_decision']}`",
            f"- Single-job sufficient for next step: `{evidence['single_job_sufficient_for_next_step']}`",
        ]
    )
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
