#!/usr/bin/env python3
"""Generate a bounded multi-release-zone Balfrin dry-run handoff package.

The helper stays at the package boundary. It composes the deterministic
release-candidate sweep, the frozen target-area scenario handoff, bounded
output/reducer pressure summaries, restartability evidence, and
uncertainty-aware post-processing commands into one reviewable scratch-root
package. It does not submit a Balfrin job, authorize scale-up, or introduce
operational claims.
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import shlex
import sys
from pathlib import Path
from typing import Any, Callable

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.lib import output_profile_policy as OUTPUT_PROFILE_POLICY


SCHEMA_VERSION = "balfrin_multi_release_zone_demo_package_v1"
COMMAND_PLAN_SCHEMA_VERSION = "balfrin_multi_release_zone_demo_command_plan_v1"
SBATCH_SCHEMA_VERSION = "balfrin_multi_release_zone_demo_handoff_v1"
DEFAULT_ARTIFACT_DIR = Path("/tmp/rust_rockfall/balfrin_multi_release_zone_demo_v1")
DEFAULT_CANDIDATE_OUTPUT_ROOT = DEFAULT_ARTIFACT_DIR / "candidate_outputs"
DEFAULT_TARGET_AREA_OUTPUT_ROOT = DEFAULT_ARTIFACT_DIR / "target_area_handoff"
DEFAULT_TARGET_AREA_CONTRACT = ROOT / "validation/pilot_runs/tschamut_public_balfrin_target_area_demo_v1.yaml"
DEFAULT_OUTPUT_PROFILE_ARTIFACT_DIR = DEFAULT_ARTIFACT_DIR / "output_profile"
DEFAULT_REDUCER_ARTIFACT_DIR = DEFAULT_ARTIFACT_DIR / "reducer_pressure"
DEFAULT_RESTARTABILITY_ARTIFACT_DIR = DEFAULT_ARTIFACT_DIR / "restartability"
DEFAULT_UNCERTAINTY_ARTIFACT_DIR = DEFAULT_ARTIFACT_DIR / "uncertainty"
DEFAULT_PRESSURE_ARTIFACT_DIR = DEFAULT_ARTIFACT_DIR / "multi_zone_pressure"
DEFAULT_PRESSURE_PROBE_ROOT = Path("/tmp/rust_rockfall/tb187_multi_zone_probe")
DEFAULT_AUTHORIZATION_RECORD_PATH = DEFAULT_ARTIFACT_DIR / "balfrin_multi_zone_live_authorization_record_v1.yaml"
DEFAULT_PACKAGE_JSON = DEFAULT_ARTIFACT_DIR / f"{SCHEMA_VERSION}.json"
DEFAULT_PACKAGE_MD = DEFAULT_ARTIFACT_DIR / f"{SCHEMA_VERSION}.txt"
DEFAULT_COMMAND_PLAN_JSON = DEFAULT_ARTIFACT_DIR / "balfrin_multi_release_zone_command_plan_v1.json"
DEFAULT_SBATCH_PATH = DEFAULT_ARTIFACT_DIR / "balfrin_multi_release_zone_handoff.sbatch"
DEFAULT_SECOND_SITE_CONFIG = ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml"
SMALLEST_MULTI_ZONE_RELEASE_ZONE_COUNT = 2
SMALLEST_MULTI_ZONE_SCENARIO_COUNT = 2
SMALLEST_MULTI_ZONE_TRAJECTORY_COUNT_TARGET = 1000
SMALLEST_MULTI_ZONE_REVIEW_RUN_ROOT = Path(
    "/scratch/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_multi_release_zone_v1"
)
SMALLEST_MULTI_ZONE_REVIEW_RUN_ID = "tschamut_public_balfrin_multi_release_zone_v1"


def _load_module(module_name: str, filename: str):
    path = ROOT / "scripts" / filename
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load helper module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


CANDIDATE_STABILITY = _load_module(
    "balfrin_multi_release_zone_candidate_stability",
    "summarize_balfrin_target_area_candidate_stability.py",
)
OUTPUT_PROFILE = _load_module(
    "balfrin_multi_release_zone_output_profile",
    "summarize_bounded_validation_output_profile.py",
)
REDUCER_SCALING = _load_module(
    "balfrin_multi_release_zone_reducer_scaling",
    "summarize_bounded_reducer_runtime_scaling.py",
)
SINGLE_JOB = _load_module(
    "balfrin_multi_release_zone_single_job",
    "summarize_balfrin_single_job_execution.py",
)
MULTI_ZONE_PRESSURE = _load_module(
    "balfrin_multi_release_zone_pressure",
    "summarize_multi_zone_reducer_pressure.py",
)


class BalfrinMultiReleaseZoneDemoHandoffError(ValueError):
    """User-facing multi-zone dry-run handoff error."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-dir", type=Path, default=DEFAULT_ARTIFACT_DIR)
    parser.add_argument("--candidate-output-root", type=Path, default=None)
    parser.add_argument("--target-area-output-root", type=Path, default=None)
    parser.add_argument("--pressure-probe-root", type=Path, default=DEFAULT_PRESSURE_PROBE_ROOT)
    parser.add_argument("--requested-release-zone-batch-size", type=int, default=2)
    parser.add_argument("--requested-reducer-chunk-count", type=int, default=2)
    parser.add_argument("--requested-reducer-worker-count", type=int, default=2)
    parser.add_argument("--format", choices=("json", "text"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    parser.add_argument("--text-output", type=Path, default=None)
    args = parser.parse_args(argv)

    try:
        report = build_report(
            artifact_dir=args.artifact_dir,
            candidate_output_root=args.candidate_output_root,
            target_area_output_root=args.target_area_output_root,
            pressure_probe_root=args.pressure_probe_root,
            requested_release_zone_batch_size=args.requested_release_zone_batch_size,
            requested_reducer_chunk_count=args.requested_reducer_chunk_count,
            requested_reducer_worker_count=args.requested_reducer_worker_count,
        )
    except BalfrinMultiReleaseZoneDemoHandoffError as exc:
        print(f"balfrin multi-release-zone demo handoff error: {exc}", file=sys.stderr)
        return 2

    materialize_artifacts(report, json_output=args.json_output, text_output=args.text_output)

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
    else:
        print(render_text_report(report))
    return 0 if report["package_status"] != "blocked_missing_inputs" and report["package_constraint_status"] not in {"blocked", "blocked_missing_inputs"} else 2


def build_blocked_missing_inputs_report(
    *,
    missing_inputs: list[str],
    artifact_dir: Path,
    candidate_output_root: Path,
    target_area_output_root: Path,
    pressure_probe_root: Path,
) -> dict[str, Any]:
    command_plan_path = artifact_dir / DEFAULT_COMMAND_PLAN_JSON.name
    sbatch_script_path = artifact_dir / DEFAULT_SBATCH_PATH.name
    package_json_path = artifact_dir / DEFAULT_PACKAGE_JSON.name
    package_md_path = artifact_dir / DEFAULT_PACKAGE_MD.name
    review_command = build_authorization_review_command()
    blocked_reason = "required inputs are missing: " + ", ".join(missing_inputs)
    blocked_output_profile_policy = OUTPUT_PROFILE_POLICY.classify_output_profile_policy(
        conditional_curve_export=None,
        grid_csv_export=None,
        no_plots=False,
        label="blocked_missing_inputs",
    )
    minimum_output_profile_policy = OUTPUT_PROFILE_POLICY.classify_output_profile_policy(
        conditional_curve_export="summary-only",
        grid_csv_export="none",
        no_plots=True,
        label="minimum_measured_multi_zone_run",
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "package_status": "blocked_missing_inputs",
        "package_provenance_status": "blocked_missing_inputs",
        "submission_classification": "blocked_pending_new_human_authorization",
        "authorization_classification": "blocked_missing_inputs",
        "live_execution_requires_new_human_authorization": True,
        "package_constraint_status": "blocked_missing_inputs",
        "package_constraint_summary": {
            "status": "blocked_missing_inputs",
            "summary": blocked_reason,
            "constraint_source": {},
            "requested_release_zone_batch_size": None,
            "requested_reducer_chunk_count": None,
            "requested_reducer_worker_count": None,
            "measured_constraints": {},
            "constraint_checks": [],
            "blocked_reason": blocked_reason,
        },
        "package_summary": {
            "status": "blocked_missing_inputs",
            "summary": blocked_reason,
            "section_counts": {"measured": 0, "fixture_backed": 0, "blocked_missing_inputs": 0},
        },
        "artifact_dir": str(artifact_dir),
        "candidate_output_root": str(candidate_output_root),
        "target_area_output_root": str(target_area_output_root),
        "command_plan_path": str(command_plan_path),
        "sbatch_script_path": str(sbatch_script_path),
        "package_json_path": str(package_json_path),
        "package_md_path": str(package_md_path),
        "missing_inputs": list(missing_inputs),
        "blocked_reason": blocked_reason,
        "candidate_release_candidates": {
            "status": "blocked_missing_inputs",
            "blocked_reason": blocked_reason,
            "candidate_count": 0,
            "candidate_component_count": 0,
            "candidate_output_mode": None,
            "candidate_output_status": None,
            "candidate_output_root": None,
            "candidate_sweep_summary": {},
            "multi_zone_stress_test_readiness": {},
        },
        "deterministic_scenarios": {
            "status": "blocked_missing_inputs",
            "bundle_runnable_status": "blocked_missing_inputs",
            "scenario_table_row_count": 0,
            "scenario_probability_semantics": None,
            "template_only_command_ids": [],
            "runnable_command_ids": [],
            "blocked_reason": blocked_reason,
        },
        "pressure_checkpoints": {
            "estimated_runtime": {
                "candidate_sweep_runtime_seconds": 0,
                "current_gap_runtime_seconds": 0,
                "reproduction_validation_wall_seconds": 0,
                "reproduction_hazard_wall_seconds": 0,
                "single_job_decision": "blocked_missing_inputs",
                "single_job_sufficient_for_next_step": False,
            },
            "output_pressure": {
                "status": "blocked_missing_inputs",
                "validation_output_blocker_status": "blocked_missing_inputs",
                "validation_output_mode": None,
                "current_file_count": 0,
                "current_total_bytes": 0,
                "file_margin": 0,
                "byte_margin": 0,
                "validation_output_file_count": 0,
                "validation_output_bytes": 0,
                "hazard_output_file_count": 0,
                "hazard_output_bytes": 0,
                "reduced_output_family_counts": {},
            },
            "reducer_chunk_pressure": {
                "status": "blocked_missing_inputs",
                "bottleneck_classification": "blocked_missing_inputs",
                "reducer_worker_counts": {},
                "hazard_layer_counts": {},
                "comparison_pairs": [],
                "local_single_job_sufficient_for_next_step": False,
            },
            "restartability": {
                "status": "blocked_missing_inputs",
                "single_job_sufficient_for_next_step": False,
                "driver_ready_for_selected_gate_use": False,
                "repeat_reuse_classification": "blocked_missing_inputs",
                "trajectory_plan_id_stable": False,
                "reducer_plan_id_stable": False,
                "numerical_artifact_classification": "blocked_missing_inputs",
                "changed_artifact_count": 0,
                "output_file_count_stable": False,
                "reducer_state": {},
            },
        },
        "multi_zone_pressure": {
            "status": "blocked_missing_inputs",
            "summary": blocked_reason,
            "pressure_probe_root": str(pressure_probe_root),
            "pressure_artifact_dir": str(artifact_dir / DEFAULT_PRESSURE_ARTIFACT_DIR.name),
            "pressure_probe_status": "blocked_missing_inputs",
            "measurement_command": None,
            "constraint_source": {},
            "measured_reducer_constraints": {},
            "recommended_reducer_constraints": {},
            "bottleneck_classification": "blocked_missing_inputs",
            "multi_zone_dry_run_blocked": True,
            "blocked_reason": blocked_reason,
            "release_zone_count": 0,
            "scenario_count": 0,
            "trajectory_chunk_count": 0,
            "reducer_worker_count": 0,
            "reducer_chunk_count": 0,
            "merge_order": None,
            "merge_order_independent": False,
            "reducer_wall_time_seconds": 0,
            "manifest_size_bytes": 0,
            "manifest_size_by_path": {},
            "root_file_count": 0,
            "root_byte_count": 0,
            "output_file_count": 0,
            "output_byte_count": 0,
            "output_family_file_counts": {},
            "output_family_bytes": {},
            "largest_output_families_by_bytes": [],
            "bottleneck_labels": {},
        },
        "constraint_pressure": {
            "status": "blocked_missing_inputs",
            "summary": blocked_reason,
            "constraint_source": {},
            "requested_release_zone_batch_size": None,
            "requested_reducer_chunk_count": None,
            "requested_reducer_worker_count": None,
            "measured_constraints": {},
            "constraint_checks": [],
            "blocked_reason": blocked_reason,
        },
        "uncertainty_post_processing": {
            "status": "blocked_missing_inputs",
            "claim_boundaries": {},
            "uncertainty_reduced": [],
            "remaining_uncertainty": [],
            "measurement_commands": {},
            "post_run_interpretation_gate_status": "blocked_missing_inputs",
            "post_run_interpretation_summary": blocked_reason,
            "minimum_useful_next_probe": {
                "probe_id": "multi_zone_balfrin_next_measured_run",
                "release_zone_count": SMALLEST_MULTI_ZONE_RELEASE_ZONE_COUNT,
                "trajectory_count_target": SMALLEST_MULTI_ZONE_TRAJECTORY_COUNT_TARGET,
            },
            "summary": blocked_reason,
        },
        "follow_up_recommendation": {
            "status": "blocked_missing_inputs",
            "live_execution_requires_new_human_authorization": True,
            "authorization_classification": "blocked_missing_inputs",
            "authorization_review_command": review_command,
            "authorization_submit_command": None,
            "minimum_measured_multi_zone_run": {
                "release_zone_count": SMALLEST_MULTI_ZONE_RELEASE_ZONE_COUNT,
                "scenario_count": SMALLEST_MULTI_ZONE_SCENARIO_COUNT,
                "trajectory_count_target": SMALLEST_MULTI_ZONE_TRAJECTORY_COUNT_TARGET,
                "seed_policy": {},
                "output_mode": None,
                "conditional_curve_export": "summary-only",
                "grid_csv_export": "none",
                "export_geotiff": True,
                "pilot_gis_package": True,
                "trajectory_workers": 2,
                "reducer_workers": 2,
            "authorization_review_command": review_command,
            "authorization_submit_command": "unavailable",
            "output_profile_policy": minimum_output_profile_policy,
            "command_plan_review_command": review_command,
            "command_plan_submit_command": "unavailable",
        },
            "reason": blocked_reason,
            "candidate_readiness": {},
            "recommended_next_check": "Review the package, then seek a new human authorization before any live multi-zone Balfrin job.",
            "blocked_reason": blocked_reason,
        },
        "smallest_measured_multi_zone_run": {
            "release_zone_count": SMALLEST_MULTI_ZONE_RELEASE_ZONE_COUNT,
            "scenario_count": SMALLEST_MULTI_ZONE_SCENARIO_COUNT,
            "trajectory_count_target": SMALLEST_MULTI_ZONE_TRAJECTORY_COUNT_TARGET,
        },
        "command_plan": {
            "schema_version": COMMAND_PLAN_SCHEMA_VERSION,
            "command_plan_status": "blocked_missing_inputs",
            "site": "tschamut_same_scale",
            "command_plan_source": "scripts/generate_pilot_command_plan.py",
            "command_plan_source_command": (
                "PYENV_VERSION=system uv run python scripts/generate_pilot_command_plan.py "
                "--site tschamut_same_scale --format json"
            ),
            "command_groups": [],
            "commands": [],
            "command_ids": [],
            "command_descriptions": {},
            "blocked_template_commands": [],
            "output_profile_policy": blocked_output_profile_policy,
            "ignored_output_paths": [str(artifact_dir), str(candidate_output_root), str(target_area_output_root)],
        },
        "claim_boundaries": {
            "operational_claims_allowed": False,
            "annual_frequency_claims_allowed": False,
            "physical_probability_claims_allowed": False,
            "risk_exposure_vulnerability_claims_allowed": False,
            "scale_up_authorized": False,
            "distributed_execution_authorized": False,
            "target_area_demo_non_operational": True,
            "multi_zone_live_execution_authorized": False,
            "target_area_demo_bundle_status": "template_only",
        },
        "ignored_output_roots": [
            str(candidate_output_root),
            str(target_area_output_root),
            str(artifact_dir),
            str(artifact_dir / DEFAULT_PRESSURE_ARTIFACT_DIR.name),
            str(pressure_probe_root),
        ],
        "generated_output_roots": [str(artifact_dir), str(candidate_output_root), str(target_area_output_root)],
        "evidence_sources": [],
        "blocked_reason": blocked_reason,
        "output_profile_policy": blocked_output_profile_policy,
        "pressure_artifact_dir": str(artifact_dir / DEFAULT_PRESSURE_ARTIFACT_DIR.name),
        "pressure_probe_root": str(pressure_probe_root),
        "authorization_review_command": review_command,
        "authorization_submit_command": "unavailable",
    }


def build_report(
    *,
    artifact_dir: Path = DEFAULT_ARTIFACT_DIR,
    candidate_output_root: Path | None = None,
    target_area_output_root: Path | None = None,
    pressure_probe_root: Path = DEFAULT_PRESSURE_PROBE_ROOT,
    requested_release_zone_batch_size: int = 2,
    requested_reducer_chunk_count: int = 2,
    requested_reducer_worker_count: int = 2,
) -> dict[str, Any]:
    artifact_dir = resolve_output_root(artifact_dir)
    if not is_allowed_output_root(artifact_dir):
        raise BalfrinMultiReleaseZoneDemoHandoffError(
            f"artifact-dir must stay under /tmp or validation/private: {artifact_dir}"
        )
    requested_release_zone_batch_size = positive_int(
        requested_release_zone_batch_size, "requested_release_zone_batch_size"
    )
    requested_reducer_chunk_count = positive_int(requested_reducer_chunk_count, "requested_reducer_chunk_count")
    requested_reducer_worker_count = positive_int(requested_reducer_worker_count, "requested_reducer_worker_count")

    candidate_output_root = resolve_output_root(candidate_output_root or (artifact_dir / "candidate_outputs"))
    target_area_output_root = resolve_output_root(target_area_output_root or (artifact_dir / "target_area_handoff"))
    if not is_allowed_output_root(candidate_output_root) or not is_allowed_output_root(target_area_output_root):
        raise BalfrinMultiReleaseZoneDemoHandoffError(
            "candidate and target-area output roots must stay under /tmp or validation/private"
        )

    pressure_artifact_dir = artifact_dir / DEFAULT_PRESSURE_ARTIFACT_DIR.name
    command_plan = build_command_plan(
        artifact_dir=artifact_dir,
        candidate_output_root=candidate_output_root,
        target_area_output_root=target_area_output_root,
        pressure_probe_root=pressure_probe_root,
        pressure_artifact_dir=pressure_artifact_dir,
    )
    candidate_report = safe_build(
        "candidate_stability",
        lambda: CANDIDATE_STABILITY.build_report(
            output_root=candidate_output_root,
            output_mode="both",
        ),
    )
    candidate_report = normalize_candidate_report(candidate_report)
    if not DEFAULT_TARGET_AREA_CONTRACT.exists():
        return build_blocked_missing_inputs_report(
            missing_inputs=[display_path(DEFAULT_TARGET_AREA_CONTRACT)],
            artifact_dir=artifact_dir,
            candidate_output_root=candidate_output_root,
            target_area_output_root=target_area_output_root,
            pressure_probe_root=pressure_probe_root,
        )

    target_area_contract = load_yaml(DEFAULT_TARGET_AREA_CONTRACT)
    target_area_input_freeze = dict(target_area_contract.get("input_freeze") or {})
    source_zone_metadata_path = resolve_repo_path(target_area_input_freeze.get("source_zone_metadata_path"))
    source_scenario_policy_path = resolve_repo_path(target_area_input_freeze.get("source_scenario_policy_path"))
    missing_required_inputs = [
        display_path(path)
        for path in (
            DEFAULT_TARGET_AREA_CONTRACT,
            source_zone_metadata_path,
            source_scenario_policy_path,
        )
        if not path.exists()
    ]
    if missing_required_inputs:
        return build_blocked_missing_inputs_report(
            missing_inputs=missing_required_inputs,
            artifact_dir=artifact_dir,
            candidate_output_root=candidate_output_root,
            target_area_output_root=target_area_output_root,
            pressure_probe_root=pressure_probe_root,
        )

    source_zone_metadata = load_yaml(source_zone_metadata_path)
    source_scenario_policy = load_yaml(source_scenario_policy_path)
    output_profile_report = safe_build("output_profile", OUTPUT_PROFILE.build_summary)
    reducer_scaling_report = safe_build(
        "reducer_scaling",
        lambda: REDUCER_SCALING.build_report(REDUCER_SCALING.DEFAULT_ARTIFACTS),
    )
    single_job_report = safe_build("single_job", SINGLE_JOB.build_summary)
    pressure_report = safe_build(
        "multi_zone_pressure",
        lambda: build_multi_zone_pressure_report(
            pressure_probe_root=pressure_probe_root,
            pressure_artifact_dir=artifact_dir / DEFAULT_PRESSURE_ARTIFACT_DIR.name,
        ),
    )
    constraint_pressure_report = build_constraint_pressure_report(
        pressure_report=pressure_report,
        requested_release_zone_batch_size=requested_release_zone_batch_size,
        requested_reducer_chunk_count=requested_reducer_chunk_count,
        requested_reducer_worker_count=requested_reducer_worker_count,
    )

    current_target_profile = dict(output_profile_report.get("current_target_gate_profile") or {})
    current_plots_enabled = current_target_profile.get("plots_enabled")
    current_output_profile_policy = OUTPUT_PROFILE_POLICY.classify_output_profile_policy(
        conditional_curve_export=current_target_profile.get("conditional_curve_export_mode"),
        grid_csv_export=current_target_profile.get("grid_csv_export_mode"),
        no_plots=False if current_plots_enabled is None else not bool(current_plots_enabled),
        label="current_target_gate_profile",
    )
    minimum_output_profile_policy = OUTPUT_PROFILE_POLICY.classify_output_profile_policy(
        conditional_curve_export="summary-only",
        grid_csv_export="none",
        no_plots=True,
        label="minimum_measured_multi_zone_run",
    )
    command_plan["output_profile_policy"] = OUTPUT_PROFILE_POLICY.summarize_output_profile_policies(
        [current_output_profile_policy, minimum_output_profile_policy],
        label="balfrin_multi_release_zone_demo_command_plan",
    )

    package_status = classify_package_status(
        candidate_report=candidate_report,
        output_profile_report=output_profile_report,
        reducer_scaling_report=reducer_scaling_report,
        single_job_report=single_job_report,
        pressure_report=pressure_report,
    )
    section_provenance_profile = build_section_provenance_profile(
        candidate_report=candidate_report,
        target_area_contract=target_area_contract,
        output_profile_report=output_profile_report,
        reducer_scaling_report=reducer_scaling_report,
        single_job_report=single_job_report,
        pressure_report=pressure_report,
        command_plan=command_plan,
    )

    follow_up_recommendation = build_follow_up_recommendation(
        candidate_report=candidate_report,
        single_job_report=single_job_report,
        output_profile_report=output_profile_report,
        target_area_contract=target_area_contract,
        source_zone_metadata=source_zone_metadata,
        source_scenario_policy=source_scenario_policy,
        pressure_report=pressure_report,
        constraint_pressure_report=constraint_pressure_report,
        artifact_dir=artifact_dir,
        candidate_output_root=candidate_output_root,
        target_area_output_root=target_area_output_root,
        pressure_artifact_dir=pressure_artifact_dir,
        pressure_probe_root=pressure_probe_root,
    )

    report = {
        "schema_version": SCHEMA_VERSION,
        "package_status": package_status,
        "package_provenance_status": package_status,
        "submission_classification": "blocked_pending_new_human_authorization",
        "authorization_classification": "blocked_pending_authorization",
        "live_execution_requires_new_human_authorization": True,
        "package_constraint_status": constraint_pressure_report["status"],
        "package_constraint_summary": constraint_pressure_report,
        "package_summary": {
            "status": package_status,
            "summary": (
                "The multi-release-zone Balfrin dry-run package is ready for review; live execution remains blocked "
                "until new human authorization is granted. "
                f"Constraint gate status: {constraint_pressure_report['status']}."
            ),
            "section_counts": section_provenance_counts(section_provenance_profile),
        },
        "artifact_dir": str(artifact_dir),
        "candidate_output_root": str(candidate_output_root),
        "target_area_output_root": str(target_area_output_root),
        "command_plan_path": str(artifact_dir / DEFAULT_COMMAND_PLAN_JSON.name),
        "sbatch_script_path": str(artifact_dir / DEFAULT_SBATCH_PATH.name),
        "package_json_path": str(artifact_dir / DEFAULT_PACKAGE_JSON.name),
        "package_md_path": str(artifact_dir / DEFAULT_PACKAGE_MD.name),
        "canonical_command_plan_reference": {
            "source_script": "scripts/generate_pilot_command_plan.py",
            "source_command": (
                "PYENV_VERSION=system uv run python scripts/generate_pilot_command_plan.py "
                "--site tschamut_same_scale --format json"
            ),
            "purpose": "Ancestor command-plan reference used to keep the package aligned with the existing Balfrin plan shape.",
        },
        "candidate_release_candidates": build_candidate_release_candidates(candidate_report),
        "deterministic_scenarios": safe_build(
            "deterministic_scenarios",
            lambda: build_deterministic_scenarios(
                target_area_contract=target_area_contract,
                command_plan=command_plan,
                target_area_output_root=target_area_output_root,
            ),
        ),
        "pressure_checkpoints": build_pressure_checkpoints(
            candidate_report=candidate_report,
            output_profile_report=output_profile_report,
            reducer_scaling_report=reducer_scaling_report,
            single_job_report=single_job_report,
        ),
        "multi_zone_pressure": pressure_report,
        "constraint_pressure": constraint_pressure_report,
        "uncertainty_post_processing": build_uncertainty_post_processing(
            single_job_report=single_job_report,
            target_area_contract=target_area_contract,
            command_plan=command_plan,
        ),
        "follow_up_recommendation": follow_up_recommendation,
        "authorization_review_command": follow_up_recommendation["authorization_review_command"],
        "authorization_submit_command": follow_up_recommendation["authorization_submit_command"],
        "smallest_measured_multi_zone_run": follow_up_recommendation["minimum_measured_multi_zone_run"],
        "output_profile_policy": command_plan.get("output_profile_policy", {}),
        "command_plan": command_plan,
        "claim_boundaries": claim_boundaries(target_area_contract),
        "ignored_output_roots": [
            str(candidate_output_root),
            str(target_area_output_root),
            str(artifact_dir),
            str(pressure_report.get("pressure_artifact_dir", artifact_dir / DEFAULT_PRESSURE_ARTIFACT_DIR.name)),
            str(pressure_report.get("pressure_probe_root", pressure_probe_root)),
        ],
        "generated_output_roots": [
            str(artifact_dir),
            str(candidate_output_root),
            str(target_area_output_root),
        ],
        "evidence_sources": [
            "scripts/summarize_balfrin_target_area_candidate_stability.py",
            "validation/pilot_runs/tschamut_public_balfrin_target_area_demo_v1.yaml",
            "scripts/summarize_bounded_validation_output_profile.py",
            "scripts/summarize_bounded_reducer_runtime_scaling.py",
            "scripts/summarize_balfrin_single_job_execution.py",
            "scripts/summarize_balfrin_scientific_delta_report.py",
            "scripts/summarize_balfrin_post_run_interpretation_gate.py",
        ],
        "blocked_reason": "live execution requires new human authorization; this helper only materializes a dry-run package",
    }

    write_package_files(report)
    return report


def build_command_plan(
    *,
    artifact_dir: Path,
    candidate_output_root: Path,
    target_area_output_root: Path,
    pressure_probe_root: Path,
    pressure_artifact_dir: Path,
) -> dict[str, Any]:
    scientific_delta_dir = artifact_dir / "scientific_delta"
    restartability_dir = artifact_dir / DEFAULT_RESTARTABILITY_ARTIFACT_DIR.name
    output_profile_dir = artifact_dir / DEFAULT_OUTPUT_PROFILE_ARTIFACT_DIR.name
    reducer_dir = artifact_dir / DEFAULT_REDUCER_ARTIFACT_DIR.name
    pressure_dir = pressure_artifact_dir

    commands = [
        command_entry(
            command_id="candidate_stability_sweep",
            group="candidate_release_candidates",
            description="Generate deterministic Balfrin release-candidate outputs from the frozen target-area contract.",
            command=command_string(
                [
                    "PYENV_VERSION=system",
                    "uv",
                    "run",
                    "python",
                    rel(ROOT / "scripts" / "summarize_balfrin_target_area_candidate_stability.py"),
                    "--contract",
                    rel(DEFAULT_TARGET_AREA_CONTRACT),
                    "--output-root",
                    str(candidate_output_root),
                    "--output-mode",
                    "both",
                    "--format",
                    "json",
                ]
            ),
            expected_inputs=[
                rel(DEFAULT_TARGET_AREA_CONTRACT),
                "data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_source_zone_metadata_v1.yaml",
                "data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_scenario_table_v1.csv",
                "validation/policies/tschamut_public_source_scenario_policy_v1.yaml",
            ],
            expected_outputs=[
                "GIS-readable candidate polygon, mask, and manifest outputs in the ignored candidate output root",
            ],
            read_only=False,
            may_produce_ignored_outputs=True,
            ignored_output_paths=[str(candidate_output_root)],
        ),
        command_entry(
            command_id="target_area_handoff_bundle",
            group="deterministic_scenarios",
            description="Materialize the frozen target-area handoff bundle that keeps deterministic scenario generation explicit.",
            command=command_string(
                [
                    "PYENV_VERSION=system",
                    "uv",
                    "run",
                    "python",
                    rel(ROOT / "scripts" / "generate_balfrin_target_area_demo_handoff.py"),
                    "--contract",
                    rel(DEFAULT_TARGET_AREA_CONTRACT),
                    "--output-root",
                    str(target_area_output_root),
                    "--format",
                    "json",
                ]
            ),
            expected_inputs=[
                rel(DEFAULT_TARGET_AREA_CONTRACT),
                "validation/pilot_runs/tschamut_public_balfrin_target_area_demo_v1.yaml",
                "validation/pilot_runs/tschamut_public_balfrin_target_gate_reproduction_v1.yaml",
                "validation/pilot_runs/tschamut_public_scalable_conditional_target_gate_v1.yaml",
                "validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml",
            ],
            expected_outputs=[
                str(target_area_output_root / "tschamut_public_balfrin_target_area_demo_case_skeleton.yaml"),
                str(target_area_output_root / "tschamut_public_balfrin_target_area_demo_command_manifest.json"),
                str(target_area_output_root / "tschamut_public_balfrin_target_area_demo_expected_output_roots.yaml"),
                str(target_area_output_root / "tschamut_public_balfrin_target_area_demo_scenario_generation_handoff.json"),
                str(target_area_output_root / "tschamut_public_balfrin_target_area_demo_gis_scope_summary.yaml"),
                str(target_area_output_root / "tschamut_public_balfrin_target_area_demo_bundle_report.json"),
            ],
            read_only=False,
            may_produce_ignored_outputs=True,
            ignored_output_paths=[str(target_area_output_root)],
        ),
        command_entry(
            command_id="multi_zone_reducer_pressure_summary",
            group="pressure_checks",
            description="Materialize the measured multi-zone reducer-pressure probe and record the fail-closed constraint source.",
            command=command_string(
                [
                    "PYENV_VERSION=system",
                    "uv",
                    "run",
                    "python",
                    rel(ROOT / "scripts" / "summarize_multi_zone_reducer_pressure.py"),
                    "--materialize-root",
                    str(pressure_probe_root),
                    "--format",
                    "json",
                    "--json-output",
                    str(pressure_dir / "multi_zone_reducer_pressure_probe_v1.json"),
                    "--markdown-output",
                    str(pressure_dir / "multi_zone_reducer_pressure_probe_v1.md"),
                ]
            ),
            expected_inputs=[
                "docs/multi_zone_reducer_pressure_probe.md",
                "scripts/summarize_multi_zone_reducer_pressure.py",
            ],
            expected_outputs=[
                str(pressure_dir / "multi_zone_reducer_pressure_probe_v1.json"),
                str(pressure_dir / "multi_zone_reducer_pressure_probe_v1.md"),
            ],
            read_only=False,
            may_produce_ignored_outputs=True,
            ignored_output_paths=[str(pressure_dir), str(pressure_probe_root)],
        ),
        command_entry(
            command_id="bounded_validation_output_profile_summary",
            group="pressure_checks",
            description="Summarize the bounded validation-output pressure that keeps the next step in reduced-output mode.",
            command=command_string(
                [
                    "PYENV_VERSION=system",
                    "uv",
                    "run",
                    "python",
                    rel(ROOT / "scripts" / "summarize_bounded_validation_output_profile.py"),
                    "--format",
                    "json",
                    "--json-output",
                    str(output_profile_dir / "bounded_validation_output_profile_v1.json"),
                    "--markdown-output",
                    str(output_profile_dir / "bounded_validation_output_profile_v1.md"),
                ]
            ),
            expected_inputs=[
                "validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml",
                "validation/pilot_runs/tschamut_public_balfrin_target_gate_reproduction_v1.yaml",
                "validation/pilot_runs/tschamut_public_output_budget_reducer_gate_v1.yaml",
                "validation/pilot_runs/tschamut_public_conditional_convergence_protocol_v1.yaml",
                "validation/pilot_runs/tschamut_public_ensemble_feasibility_v1.yaml",
            ],
            expected_outputs=["JSON and Markdown bounded validation-output profile report"],
            read_only=True,
            may_produce_ignored_outputs=False,
        ),
        command_entry(
            command_id="bounded_reducer_runtime_scaling_summary",
            group="pressure_checks",
            description="Summarize reducer chunk pressure, worker counts, and same-scale runtime scaling.",
            command=command_string(
                [
                    "PYENV_VERSION=system",
                    "uv",
                    "run",
                    "python",
                    rel(ROOT / "scripts" / "summarize_bounded_reducer_runtime_scaling.py"),
                    "--format",
                    "json",
                    "--json-output",
                    str(reducer_dir / "bounded_reducer_runtime_scaling_v1.json"),
                    "--markdown-output",
                    str(reducer_dir / "bounded_reducer_runtime_scaling_v1.md"),
                ]
            ),
            expected_inputs=[
                "validation/private/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_manifest.json",
                "hazard/results/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_manifest.json",
                "validation/private/tschamut_public_pilot/target_gate_v1/validation_tschamut_public_target_gate_v1_manifest.json",
                "hazard/results/tschamut_public_pilot/target_gate_v1/validation_tschamut_public_target_gate_v1_manifest.json",
            ],
            expected_outputs=["JSON and Markdown bounded reducer/runtime scaling report"],
            read_only=True,
            may_produce_ignored_outputs=False,
        ),
        command_entry(
            command_id="single_job_restartability_summary",
            group="pressure_checks",
            description="Record restartability checkpoints and the single-job sufficiency boundary for the next step.",
            command=command_string(
                [
                    "PYENV_VERSION=system",
                    "uv",
                    "run",
                    "python",
                    rel(ROOT / "scripts" / "summarize_balfrin_single_job_execution.py"),
                    "--output-json",
                    str(restartability_dir / "balfrin_single_job_execution_sufficiency_v1.json"),
                    "--output-md",
                    str(restartability_dir / "balfrin_single_job_execution_sufficiency_v1.md"),
                ]
            ),
            expected_inputs=[
                "validation/pilot_runs/tschamut_public_slurm_probe_repeatability_v1.yaml",
                "validation/pilot_runs/tschamut_public_balfrin_target_gate_reproduction_v1.yaml",
                "validation/pilot_runs/tschamut_public_output_budget_reducer_gate_v1.yaml",
                "validation/pilot_runs/tschamut_public_conditional_convergence_protocol_v1.yaml",
                "validation/pilot_runs/tschamut_public_ensemble_feasibility_v1.yaml",
                "validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml",
            ],
            expected_outputs=["JSON and Markdown single-job sufficiency report"],
            read_only=True,
            may_produce_ignored_outputs=False,
        ),
        command_entry(
            command_id="scientific_delta_report",
            group="uncertainty_post_processing",
            description="Compose the uncertainty-aware scientific delta report and its post-run interpretation gate.",
            command=command_string(
                [
                    "PYENV_VERSION=system",
                    "uv",
                    "run",
                    "python",
                    rel(ROOT / "scripts" / "summarize_balfrin_scientific_delta_report.py"),
                    "--format",
                    "json",
                    "--artifact-dir",
                    str(scientific_delta_dir),
                ]
            ),
            expected_inputs=[
                "validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml",
                "validation/pilot_runs/tschamut_public_balfrin_target_gate_reproduction_v1.yaml",
                "validation/pilot_runs/tschamut_public_conditional_convergence_protocol_v1.yaml",
                "validation/pilot_runs/tschamut_public_ensemble_feasibility_v1.yaml",
                "validation/pilot_runs/tschamut_public_slurm_probe_repeatability_v1.yaml",
            ],
            expected_outputs=[
                str(scientific_delta_dir / "balfrin_scientific_delta_report_v1.json"),
                str(scientific_delta_dir / "balfrin_scientific_delta_report_v1.txt"),
            ],
            read_only=True,
            may_produce_ignored_outputs=False,
        ),
        command_entry(
            command_id="post_run_gate_preview",
            group="uncertainty_post_processing",
            description="Preview the post-run interpretation gate against the scientific delta report evidence bundle.",
            command=command_string(
                [
                    "PYENV_VERSION=system",
                    "uv",
                    "run",
                    "python",
                    rel(ROOT / "scripts" / "summarize_balfrin_post_run_interpretation_gate.py"),
                    "--format",
                    "json",
                    "--evidence-json",
                    str(scientific_delta_dir / "balfrin_scientific_delta_report_v1.json"),
                ]
            ),
            expected_inputs=[
                str(scientific_delta_dir / "balfrin_scientific_delta_report_v1.json"),
            ],
            expected_outputs=["JSON post-run interpretation gate report"],
            read_only=True,
            may_produce_ignored_outputs=False,
        ),
        command_entry(
            command_id="authorization_review_command",
            group="authorization_review",
            description="Review the exact later submit command for the smallest bounded multi-zone Balfrin probe.",
            command=build_authorization_review_command(),
            expected_inputs=[
                "scripts/submit_balfrin_probe.py",
                "validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml",
                "docs/balfrin_probe_slurm_driver.md",
            ],
            expected_outputs=[
                "A deterministic later-review command for the smallest bounded multi-zone Balfrin probe.",
            ],
            read_only=True,
            may_produce_ignored_outputs=False,
        ),
        command_entry(
            command_id="package_materialization",
            group="package_materialization",
            description="Materialize the multi-release-zone dry-run package into the ignored scratch-root handoff directory.",
            command=command_string(
                [
                    "PYENV_VERSION=system",
                    "uv",
                    "run",
                    "python",
                    rel(ROOT / "scripts" / "generate_balfrin_multi_release_zone_demo_handoff.py"),
                    "--artifact-dir",
                    str(artifact_dir),
                    "--format",
                    "json",
                ]
            ),
            expected_inputs=[
                "candidate stability sweep",
                "target-area handoff bundle",
                "bounded validation-output profile summary",
                "bounded reducer/runtime scaling summary",
                "single-job sufficiency summary",
                "scientific delta report",
            ],
            expected_outputs=[
                str(artifact_dir / DEFAULT_COMMAND_PLAN_JSON.name),
                str(artifact_dir / DEFAULT_SBATCH_PATH.name),
                str(artifact_dir / DEFAULT_PACKAGE_JSON.name),
                str(artifact_dir / DEFAULT_PACKAGE_MD.name),
            ],
            read_only=False,
            may_produce_ignored_outputs=True,
            ignored_output_paths=[
                str(artifact_dir),
                str(candidate_output_root),
                str(target_area_output_root),
            ],
        ),
    ]

    return {
        "schema_version": COMMAND_PLAN_SCHEMA_VERSION,
        "command_plan_status": "ready",
        "site": "tschamut_same_scale",
        "command_plan_source": "scripts/generate_pilot_command_plan.py",
        "command_plan_source_command": (
            "PYENV_VERSION=system uv run python scripts/generate_pilot_command_plan.py "
            "--site tschamut_same_scale --format json"
        ),
        "command_groups": [
            {
                "id": "candidate_release_candidates",
                "description": "Generate deterministic candidate release-zone outputs from the frozen target-area contract.",
                "status": "ready",
            },
            {
                "id": "deterministic_scenarios",
                "description": "Materialize the frozen target-area scenario handoff and deterministic scenario-generation bundle.",
                "status": "ready",
            },
            {
                "id": "pressure_checks",
                "description": "Record multi-zone reducer pressure, output pressure, reducer/chunk pressure, and restartability checkpoints.",
                "status": "ready",
            },
            {
                "id": "uncertainty_post_processing",
                "description": "Compose the uncertainty-aware post-processing and interpretation gate reports.",
                "status": "ready",
            },
            {
                "id": "authorization_review",
                "description": "Stage the exact later review command for the smallest bounded multi-zone probe.",
                "status": "ready",
            },
            {
                "id": "package_materialization",
                "description": "Write the scratch-root package and handoff script.",
                "status": "ready",
            },
        ],
        "commands": commands,
        "command_ids": [command["id"] for command in commands],
        "command_descriptions": {command["id"]: command["description"] for command in commands},
        "blocked_template_commands": [],
        "ignored_output_paths": sorted(
            {
                str(artifact_dir),
                str(candidate_output_root),
                str(target_area_output_root),
                str(output_profile_dir),
                str(reducer_dir),
                str(restartability_dir),
                str(scientific_delta_dir),
            }
        ),
    }


def build_candidate_release_candidates(candidate_report: dict[str, Any]) -> dict[str, Any]:
    candidate_products = dict(candidate_report.get("candidate_release_zone_products") or {})
    sweep_summary = dict(candidate_report.get("candidate_sweep_summary") or {})
    return {
        "schema_version": candidate_report.get("schema_version"),
        "status": candidate_report.get("candidate_metrics_status"),
        "candidate_release_zone_interpretation": candidate_report.get("candidate_release_zone_interpretation"),
        "target_area_id": candidate_report.get("target_area", {}).get("target_area_id"),
        "candidate_release_zone_set_status": candidate_report.get("candidate_release_zone_set_status"),
        "candidate_site_name": candidate_products.get("candidate_site_name"),
        "candidate_count": candidate_products.get("candidate_cell_count", 0),
        "candidate_component_count": candidate_products.get("component_count", 0),
        "candidate_output_status": candidate_products.get("output_status"),
        "candidate_output_mode": candidate_products.get("output_mode"),
        "candidate_output_root": candidate_products.get("manifest_path"),
        "candidate_sweep_summary": sweep_summary,
        "candidate_selection_rationale": candidate_report.get("candidate_selection_rationale"),
        "blocked_reason": candidate_report.get("blocked_reason", "none"),
        "multi_zone_stress_test_readiness": sweep_summary.get("multi_zone_stress_test_readiness", {}),
    }


def normalize_candidate_report(candidate_report: dict[str, Any]) -> dict[str, Any]:
    if candidate_report.get("status") == "blocked_missing_inputs":
        return candidate_report

    normalized = dict(candidate_report)
    candidate_sweep_summary = dict(candidate_report.get("candidate_sweep_summary") or {})
    sweep_measurements = dict(candidate_sweep_summary.get("sweep_measurements") or {})
    runtime_seconds = sweep_measurements.get("runtime_seconds")
    if isinstance(runtime_seconds, (int, float)):
        sweep_measurements["runtime_seconds"] = int(round(float(runtime_seconds)))
    candidate_sweep_summary["sweep_measurements"] = sweep_measurements
    normalized["candidate_sweep_summary"] = candidate_sweep_summary
    return normalized


def build_deterministic_scenarios(
    *,
    target_area_contract: dict[str, Any],
    command_plan: dict[str, Any],
    target_area_output_root: Path,
) -> dict[str, Any]:
    target_area = dict(target_area_contract.get("target_area") or {})
    input_freeze = dict(target_area_contract.get("input_freeze") or {})
    boundary = dict(target_area_contract.get("balfrin_execution_boundary") or {})
    claim_boundary = dict(target_area_contract.get("claim_boundary") or {})
    scenario_table_path = resolve_repo_path(input_freeze.get("scenario_table_path"))
    source_zone_metadata_path = resolve_repo_path(input_freeze.get("source_zone_metadata_path"))
    source_scenario_policy_path = resolve_repo_path(input_freeze.get("source_scenario_policy_path"))
    release_points_path = resolve_repo_path(input_freeze.get("release_points_csv"))
    scenario_generation_command = command_string(
        [
            "PYENV_VERSION=system",
            "uv",
            "run",
            "python",
            rel(ROOT / "scripts" / "generate_balfrin_target_area_scenario_tables.py"),
            "--contract",
            rel(DEFAULT_TARGET_AREA_CONTRACT),
            "--source-scenario-policy",
            rel(source_scenario_policy_path),
            "--source-zone-metadata",
            rel(source_zone_metadata_path),
            "--release-points",
            rel(release_points_path),
            "--reference-scenario-table",
            rel(scenario_table_path),
            "--output-root",
            str(target_area_output_root),
            "--format",
            "json",
        ]
    )
    scenario_table_row_count = count_csv_rows(scenario_table_path)
    scenario_generation_handoff = {
        "status": "template_only",
        "summary": (
            "The frozen target-area contract is retained as a template-only handoff; scenario-table generation is "
            "staged in the command plan but not executed by this dry-run package."
        ),
        "schema_version": target_area_contract.get("schema_version"),
        "contract_path": str(DEFAULT_TARGET_AREA_CONTRACT),
        "target_area_id": target_area.get("target_area_id"),
        "target_area_name": target_area.get("target_area_name"),
        "target_area_label": target_area.get("target_area_label"),
        "target_area_output_root": str(target_area_output_root),
        "scenario_table_path": str(scenario_table_path),
        "source_zone_metadata_path": str(source_zone_metadata_path),
        "source_scenario_policy_path": str(source_scenario_policy_path),
        "release_points_csv": str(release_points_path),
        "scenario_table_row_count": scenario_table_row_count,
        "scenario_probability_semantics": input_freeze.get("scenario_probability_semantics"),
        "scenario_table_generation": {
            "command_id": "target_area_scenario_table_generation",
            "command": scenario_generation_command,
            "output_root": str(target_area_output_root),
            "scenario_table_csv": str(target_area_output_root / "tschamut_public_balfrin_target_area_demo_scenario_table.csv"),
            "scenario_manifest_json": str(target_area_output_root / "tschamut_public_balfrin_target_area_demo_scenario_manifest.json"),
            "conditional_only_weighting": True,
        },
        "command_plan_hook": boundary.get("command_plan_hook", {}),
        "template_only_command_ids": ["target_area_handoff_bundle"],
        "runnable_command_ids": [],
        "blocked_reason": "template_only_frozen_target_area_handoff",
    }
    gis_scope_summary = {
        "status": "template_only",
        "summary": (
            "The multi-release-zone dry-run package records the frozen target-area contract separately from any "
            "downstream template-only outputs and does not imply that GIS or hazard layers were generated."
        ),
        "planned_products": [],
        "planned_raster_products": [],
        "planned_vector_products": [],
        "template_only_products": [
            {
                "category": "target_area_handoff_bundle",
                "product": "multi-release-zone target-area handoff bundle",
                "product_kind": "metadata",
                "scope_state": "template_only",
                "current_status": "not_generated",
                "expected_staged_path": str(target_area_output_root),
                "source": "bundle_generator",
            }
        ],
        "blocked_missing_inputs": [],
        "cog_export_expectation": {
            "status": "template_only",
            "generated_now": False,
            "hazard_layers_generated": False,
            "cog_export_generated": False,
            "downstream_template_only_command_ids": ["target_area_handoff_bundle"],
            "summary": (
                "The target-area handoff remains a template-only expectation in this package; it is staged for later "
                "review rather than generated here."
            ),
        },
        "non_operational_gis_boundaries": {
            "operational_claims_allowed": False,
            "hazard_layers_generated": False,
            "cog_export_generated": False,
            "scale_up_authorized": False,
            "distributed_execution_authorized": False,
            "annual_frequency_claims_allowed": False,
            "physical_probability_claims_allowed": False,
            "risk_exposure_vulnerability_claims_allowed": False,
        },
        "no_hazard_layers_generated": True,
        "output_mode": dict(target_area_contract.get("output_mode") or {}),
        "balfrin_execution_boundary": boundary,
        "claim_boundary": claim_boundary,
    }
    command_manifest = {
        "status": "planned",
        "command_ids": [command["id"] for command in command_plan["commands"]],
        "template_only_command_ids": ["target_area_handoff_bundle"],
        "command_plan_hook": boundary.get("command_plan_hook", {}),
        "target_area_output_root": str(target_area_output_root),
        "summary": (
            "The command plan keeps the multi-release-zone bundle explicit, but the target-area handoff remains "
            "template-only in this package."
        ),
    }
    return {
        "schema_version": target_area_contract.get("schema_version"),
        "status": "template_only",
        "bundle_runnable_status": "planned",
        "target_area_id": target_area.get("target_area_id"),
        "target_area_name": target_area.get("target_area_name"),
        "target_area_label": target_area.get("target_area_label"),
        "contract_status": target_area_contract.get("contract_status"),
        "scenario_generation_handoff": scenario_generation_handoff,
        "gis_scope_summary": gis_scope_summary,
        "command_manifest": command_manifest,
        "scenario_generation_command": scenario_generation_command,
        "scenario_table_row_count": scenario_table_row_count,
        "scenario_probability_semantics": input_freeze.get("scenario_probability_semantics"),
        "template_only_command_ids": ["target_area_handoff_bundle"],
        "runnable_command_ids": [command["id"] for command in command_plan["commands"] if command["id"] != "target_area_handoff_bundle"],
        "blocked_reason": "template_only_frozen_target_area_handoff",
    }


def build_pressure_checkpoints(
    *,
    candidate_report: dict[str, Any],
    output_profile_report: dict[str, Any],
    reducer_scaling_report: dict[str, Any],
    single_job_report: dict[str, Any],
) -> dict[str, Any]:
    candidate_sweep = dict(candidate_report.get("candidate_sweep_summary") or {})
    candidate_measurements = dict(candidate_sweep.get("sweep_measurements") or {})
    current_pressure = dict(output_profile_report.get("current_pressure") or {})
    bounded_profile = dict(output_profile_report.get("bounded_profile") or {})
    reducer_state = dict(single_job_report.get("reducer_state_evidence") or {})
    restartability = dict(single_job_report.get("restartability_evidence") or {})
    wall_time = dict(single_job_report.get("wall_time_evidence") or {})

    return {
        "estimated_runtime": {
            "candidate_sweep_runtime_seconds": candidate_measurements.get("runtime_seconds"),
            "current_gap_runtime_seconds": wall_time.get("current_gap_runtime_seconds"),
            "reproduction_validation_wall_seconds": wall_time.get("reproduction_validation_wall_seconds"),
            "reproduction_hazard_wall_seconds": wall_time.get("reproduction_hazard_wall_seconds"),
            "single_job_decision": single_job_report.get("decision"),
            "single_job_sufficient_for_next_step": single_job_report.get("single_job_sufficient_for_next_step"),
        },
        "output_pressure": {
            "status": output_profile_report.get("acceptance_classification"),
            "validation_output_blocker_status": output_profile_report.get("validation_output_blocker_status"),
            "validation_output_mode": output_profile_report.get("validation_output_mode"),
            "current_file_count": current_pressure.get("current_file_count"),
            "current_total_bytes": current_pressure.get("current_total_bytes"),
            "file_margin": current_pressure.get("file_margin"),
            "byte_margin": current_pressure.get("byte_margin"),
            "validation_output_file_count": bounded_profile.get("validation_output_file_count"),
            "validation_output_bytes": bounded_profile.get("validation_output_bytes"),
            "hazard_output_file_count": bounded_profile.get("hazard_output_file_count"),
            "hazard_output_bytes": bounded_profile.get("hazard_output_bytes"),
            "reduced_output_family_counts": output_profile_report.get("reduced_output_family_counts", {}),
        },
        "reducer_chunk_pressure": {
            "status": reducer_scaling_report.get("reducer_scaling_status"),
            "bottleneck_classification": reducer_scaling_report.get("bottleneck_classification"),
            "reducer_worker_counts": reducer_scaling_report.get("reducer_worker_counts", {}),
            "hazard_layer_counts": reducer_scaling_report.get("hazard_layer_counts", {}),
            "comparison_pairs": reducer_scaling_report.get("comparison_pairs", []),
            "local_single_job_sufficient_for_next_step": reducer_scaling_report.get(
                "local_single_job_sufficient_for_next_step"
            ),
        },
        "restartability": {
            "status": single_job_report.get("final_classification"),
            "single_job_sufficient_for_next_step": single_job_report.get("single_job_sufficient_for_next_step"),
            "driver_ready_for_selected_gate_use": restartability.get("driver_ready_for_selected_gate_use"),
            "repeat_reuse_classification": restartability.get("repeat_reuse_classification"),
            "trajectory_plan_id_stable": restartability.get("trajectory_plan_id_stable"),
            "reducer_plan_id_stable": restartability.get("reducer_plan_id_stable"),
            "numerical_artifact_classification": restartability.get("numerical_artifact_classification"),
            "changed_artifact_count": restartability.get("changed_artifact_count"),
            "output_file_count_stable": restartability.get("output_file_count_stable"),
            "reducer_state": reducer_state,
        },
    }


def build_multi_zone_pressure_report(
    *,
    pressure_probe_root: Path,
    pressure_artifact_dir: Path,
) -> dict[str, Any]:
    pressure_probe_root = resolve_output_root(pressure_probe_root)
    pressure_artifact_dir = resolve_output_root(pressure_artifact_dir)
    if not is_allowed_output_root(pressure_artifact_dir):
        raise BalfrinMultiReleaseZoneDemoHandoffError(
            f"pressure artifact dir must stay under /tmp or validation/private: {pressure_artifact_dir}"
        )
    if not is_allowed_output_root(pressure_probe_root):
        raise BalfrinMultiReleaseZoneDemoHandoffError(
            f"pressure probe root must stay under /tmp or validation/private: {pressure_probe_root}"
        )

    MULTI_ZONE_PRESSURE.materialize_probe_root(pressure_probe_root)
    report = MULTI_ZONE_PRESSURE.build_report(pressure_probe_root)
    pressure_artifact_dir.mkdir(parents=True, exist_ok=True)
    dump_json(pressure_artifact_dir / "multi_zone_reducer_pressure_probe_v1.json", report)
    (pressure_artifact_dir / "multi_zone_reducer_pressure_probe_v1.md").write_text(
        MULTI_ZONE_PRESSURE.render_markdown(report),
        encoding="utf-8",
    )
    return {
        "status": report.get("probe_status", "blocked_missing_inputs"),
        "summary": report.get("blocked_reason")
        or "Measured multi-zone reducer pressure is recorded for fail-closed handoff enforcement.",
        "pressure_probe_root": str(pressure_probe_root),
        "pressure_artifact_dir": str(pressure_artifact_dir),
        "pressure_probe_status": report.get("probe_status"),
        "measurement_command": report.get("measurement_command"),
        "constraint_source": report.get("measured_reducer_constraints", {}).get("constraint_source", {}),
        "measured_reducer_constraints": dict(report.get("measured_reducer_constraints") or {}),
        "recommended_reducer_constraints": dict(report.get("recommended_reducer_constraints") or {}),
        "bottleneck_classification": report.get("bottleneck_classification"),
        "multi_zone_dry_run_blocked": report.get("multi_zone_dry_run_blocked"),
        "blocked_reason": report.get("blocked_reason"),
        "release_zone_count": report.get("release_zone_count", 0),
        "scenario_count": report.get("scenario_count", 0),
        "trajectory_chunk_count": report.get("trajectory_chunk_count", 0),
        "reducer_worker_count": report.get("reducer_worker_count", 0),
        "reducer_chunk_count": report.get("reducer_chunk_count", 0),
        "merge_order": report.get("merge_order"),
        "merge_order_independent": report.get("merge_order_independent"),
        "reducer_wall_time_seconds": report.get("reducer_wall_time_seconds", 0),
        "manifest_size_bytes": report.get("manifest_size_bytes", 0),
        "root_file_count": report.get("root_file_count", 0),
        "output_file_count": report.get("output_file_count", 0),
        "output_byte_count": report.get("output_byte_count", 0),
        "output_family_file_counts": dict(report.get("output_family_file_counts") or {}),
        "output_family_bytes": dict(report.get("output_family_bytes") or {}),
        "largest_output_families_by_bytes": list(report.get("largest_output_families_by_bytes") or []),
        "manifest_size_by_path": dict(report.get("manifest_size_by_path") or {}),
    }


def build_constraint_pressure_report(
    *,
    pressure_report: dict[str, Any],
    requested_release_zone_batch_size: int,
    requested_reducer_chunk_count: int,
    requested_reducer_worker_count: int,
) -> dict[str, Any]:
    measured_constraints = dict(pressure_report.get("measured_reducer_constraints") or {})
    constraint_source = dict(measured_constraints.get("constraint_source") or {})
    if pressure_report.get("status") == "blocked_missing_inputs" or not measured_constraints:
        return {
            "status": "blocked_missing_inputs",
            "summary": "Measured multi-zone reducer constraints could not be loaded.",
            "constraint_source": constraint_source,
            "requested_release_zone_batch_size": requested_release_zone_batch_size,
            "requested_reducer_chunk_count": requested_reducer_chunk_count,
            "requested_reducer_worker_count": requested_reducer_worker_count,
            "measured_constraints": measured_constraints,
            "constraint_checks": [],
            "blocked_reason": pressure_report.get("blocked_reason", "missing measured reducer constraints"),
        }

    checks = [
        constraint_check(
            label="simultaneous_release_zone_batch_size",
            requested=requested_release_zone_batch_size,
            limit=positive_int(measured_constraints.get("simultaneous_release_zone_batch_max"), "measured simultaneous release-zone batch max"),
        ),
        constraint_check(
            label="reducer_chunk_count",
            requested=requested_reducer_chunk_count,
            limit=positive_int(measured_constraints.get("reducer_chunk_count_max"), "measured reducer chunk count max"),
        ),
        constraint_check(
            label="reducer_worker_count",
            requested=requested_reducer_worker_count,
            limit=positive_int(measured_constraints.get("reducer_worker_count_max"), "measured reducer worker count max"),
        ),
    ]
    status = overall_constraint_status(checks)
    summary = constraint_pressure_summary(status, checks)
    return {
        "status": status,
        "summary": summary,
        "constraint_source": constraint_source,
        "requested_release_zone_batch_size": requested_release_zone_batch_size,
        "requested_reducer_chunk_count": requested_reducer_chunk_count,
        "requested_reducer_worker_count": requested_reducer_worker_count,
        "measured_constraints": measured_constraints,
        "constraint_checks": checks,
        "blocked_reason": summary if status == "blocked" else None,
        "warning_reason": summary if status == "warning" else None,
    }


def constraint_check(*, label: str, requested: int, limit: int) -> dict[str, Any]:
    if requested < 1:
        raise BalfrinMultiReleaseZoneDemoHandoffError(f"{label} must be greater than 0")
    if requested > limit:
        status = "blocked"
        reason = f"requested {label}={requested} exceeds measured max {limit}"
    elif requested == limit:
        status = "warning"
        reason = f"requested {label}={requested} reaches measured max {limit}"
    else:
        status = "acceptable"
        reason = f"requested {label}={requested} stays within measured max {limit}"
    return {
        "label": label,
        "status": status,
        "requested": requested,
        "limit": limit,
        "reason": reason,
    }


def overall_constraint_status(checks: list[dict[str, Any]]) -> str:
    if any(check["status"] == "blocked" for check in checks):
        return "blocked"
    if any(check["status"] == "warning" for check in checks):
        return "warning"
    return "acceptable"


def constraint_pressure_summary(status: str, checks: list[dict[str, Any]]) -> str:
    reasons = [check["reason"] for check in checks if check["status"] != "acceptable"]
    if status == "blocked":
        return "blocked: " + "; ".join(reasons)
    if status == "warning":
        return "warning: " + "; ".join(reasons)
    return "acceptable: requested multi-zone settings stay below measured reducer constraints"


def positive_int(value: Any, context: str) -> int:
    if not isinstance(value, int) or value <= 0:
        raise BalfrinMultiReleaseZoneDemoHandoffError(f"{context} must be a positive integer")
    return value


def _number_or_zero(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def build_authorization_review_command() -> str:
    return command_string(
        [
            "PYENV_VERSION=system",
            "uv",
            "run",
            "python",
            rel(ROOT / "scripts" / "submit_balfrin_probe.py"),
            rel(DEFAULT_TARGET_AREA_CONTRACT),
            "--run-root",
            str(SMALLEST_MULTI_ZONE_REVIEW_RUN_ROOT),
            "--run-id",
            SMALLEST_MULTI_ZONE_REVIEW_RUN_ID,
            "--partition",
            "postproc",
            "--time",
            "00:30:00",
            "--nodes",
            "1",
            "--ntasks",
            "1",
            "--cpus-per-task",
            "16",
            "--generate-only",
        ]
    )


def build_authorized_submit_command(*, reviewed_handoff_package_path: Path, authorization_record_path: Path) -> str:
    return command_string(
        [
            "PYENV_VERSION=system",
            "uv",
            "run",
            "python",
            rel(ROOT / "scripts" / "submit_balfrin_probe.py"),
            rel(DEFAULT_TARGET_AREA_CONTRACT),
            "--run-root",
            str(SMALLEST_MULTI_ZONE_REVIEW_RUN_ROOT),
            "--run-id",
            SMALLEST_MULTI_ZONE_REVIEW_RUN_ID,
            "--partition",
            "postproc",
            "--time",
            "00:30:00",
            "--nodes",
            "1",
            "--ntasks",
            "1",
            "--cpus-per-task",
            "16",
            "--authorized-submit",
            "--reviewed-handoff-package",
            str(reviewed_handoff_package_path),
            "--authorization-record",
            str(authorization_record_path),
        ]
    )


def build_smallest_multi_zone_run_estimates(pressure_report: dict[str, Any]) -> dict[str, Any]:
    measured_release_zone_count = positive_int(
        pressure_report.get("release_zone_count", 1), "measured multi-zone release zone count"
    )
    scale = SMALLEST_MULTI_ZONE_RELEASE_ZONE_COUNT / measured_release_zone_count
    estimated_runtime_seconds = round(_number_or_zero(pressure_report.get("reducer_wall_time_seconds")) * scale, 3)
    estimated_storage_bytes = max(1, int(round(_number_or_zero(pressure_report.get("output_byte_count")) * scale)))
    estimated_file_count = max(1, int(round(_number_or_zero(pressure_report.get("output_file_count")) * scale)))
    estimated_manifest_pressure_bytes = max(
        1, int(round(_number_or_zero(pressure_report.get("manifest_size_bytes")) * scale))
    )
    return {
        "reference_release_zone_count": measured_release_zone_count,
        "reference_scale_factor": round(scale, 6),
        "estimated_runtime_seconds": estimated_runtime_seconds,
        "estimated_storage_bytes": estimated_storage_bytes,
        "estimated_file_count": estimated_file_count,
        "estimated_manifest_pressure_bytes": estimated_manifest_pressure_bytes,
    }


def build_smallest_multi_zone_preservation_checklist(
    *,
    command_plan_path: Path,
    sbatch_script_path: Path,
    package_json_path: Path,
    package_md_path: Path,
    artifact_dir: Path,
    candidate_output_root: Path,
    target_area_output_root: Path,
    pressure_artifact_dir: Path,
    pressure_probe_root: Path,
    reviewed_handoff_package_path: Path,
    authorization_record_path: Path,
    review_command: str,
) -> list[str]:
    return [
        "Review the package JSON and Markdown together before any later authorization request.",
        f"Confirm the package remains blocked pending authorization and keep the review command unchanged: {review_command}",
        f"Keep the reviewed handoff package at {reviewed_handoff_package_path}.",
        f"Keep the live-run authorization record at {authorization_record_path}.",
        f"Confirm the scratch handoff root stays under {artifact_dir} and is not committed.",
        f"Keep the command plan at {command_plan_path} and the SBATCH script at {sbatch_script_path}.",
        f"Keep the package outputs at {package_json_path} and {package_md_path}.",
        f"Keep the ignored candidate and target-area roots separate: {candidate_output_root} and {target_area_output_root}.",
        f"Keep the measured reducer-pressure scratch root separate: {pressure_probe_root} and {pressure_artifact_dir}.",
        "Do not submit a live Balfrin job unless the conversation explicitly authorizes execution later.",
        "If authorization is granted later, review the exact submit command again before launch.",
        "Later preservation-gate verification command: PYENV_VERSION=system uv run python scripts/summarize_balfrin_probe_preservation_gate.py --run-root <run-root> --format json",
    ]


def build_uncertainty_post_processing(
    *,
    single_job_report: dict[str, Any],
    target_area_contract: dict[str, Any],
    command_plan: dict[str, Any],
) -> dict[str, Any]:
    measurement_commands = {
        command["id"]: command["command"]
        for command in command_plan["commands"]
        if command["id"] in {"scientific_delta_report", "post_run_gate_preview"}
    }
    uncertainty_reduced = ["bounded validation-output pressure is summarized", "reducer/chunk pressure is summarized"]
    if single_job_report.get("single_job_sufficient_for_next_step"):
        uncertainty_reduced.insert(0, "single-job sufficiency is recorded")
    return {
        "status": "planned",
        "claim_boundaries": target_area_contract.get("claim_boundary", {}),
        "uncertainty_reduced": uncertainty_reduced,
        "remaining_uncertainty": [
            "scientific-delta synthesis is staged as a later command, not executed here",
            "post-run interpretation gate preview is staged as a later command, not executed here",
        ],
        "measurement_commands": measurement_commands,
        "post_run_interpretation_gate_status": "not_run",
        "post_run_interpretation_summary": "The gate preview is staged in the command plan only.",
        "minimum_useful_next_probe": {
            "probe_id": "multi_zone_balfrin_next_measured_run",
            "release_zone_count": 2,
            "trajectory_count_target": 1000,
        },
        "summary": (
            "The uncertainty-aware post-processing chain keeps the gate interpretation explicit and preserves "
            "the non-operational boundaries."
        ),
    }


def build_follow_up_recommendation(
    *,
    candidate_report: dict[str, Any],
    single_job_report: dict[str, Any],
    output_profile_report: dict[str, Any],
    target_area_contract: dict[str, Any],
    source_zone_metadata: dict[str, Any],
    source_scenario_policy: dict[str, Any],
    pressure_report: dict[str, Any],
    constraint_pressure_report: dict[str, Any],
    artifact_dir: Path,
    candidate_output_root: Path,
    target_area_output_root: Path,
    pressure_artifact_dir: Path,
    pressure_probe_root: Path,
) -> dict[str, Any]:
    readiness = dict(candidate_report.get("candidate_sweep_summary", {}).get("multi_zone_stress_test_readiness") or {})
    review_command = build_authorization_review_command()
    package_json_path = artifact_dir / DEFAULT_PACKAGE_JSON.name
    authorization_record_path = artifact_dir / DEFAULT_AUTHORIZATION_RECORD_PATH.name
    review_submit_command = build_authorized_submit_command(
        reviewed_handoff_package_path=package_json_path,
        authorization_record_path=authorization_record_path,
    )
    estimates = build_smallest_multi_zone_run_estimates(pressure_report)
    source_release_sampling = dict(source_zone_metadata.get("release_sampling_policy") or {})
    source_zone_policy = dict(source_scenario_policy.get("source_zone_policy") or {})
    block_scenarios = list((source_scenario_policy.get("block_scenario_policy") or {}).get("scenarios") or [])
    return {
        "status": "deferred_pending_authorization",
        "live_execution_requires_new_human_authorization": True,
        "authorization_classification": "blocked_pending_authorization",
        "authorization_review_command": review_command,
        "authorization_submit_command": review_submit_command,
        "minimum_measured_multi_zone_run": {
            "release_zone_count": SMALLEST_MULTI_ZONE_RELEASE_ZONE_COUNT,
            "scenario_count": SMALLEST_MULTI_ZONE_SCENARIO_COUNT,
            "trajectory_count_target": SMALLEST_MULTI_ZONE_TRAJECTORY_COUNT_TARGET,
            "release_cell_count": positive_int(
                source_release_sampling.get("release_count", 1), "source-zone release cell count"
            ),
            "seed_policy": {
                "mode": source_release_sampling.get("mode"),
                "seed_policy": source_release_sampling.get("seed_policy"),
                "seed": source_release_sampling.get("seed"),
                "release_cell_id_policy": source_release_sampling.get("release_cell_id_policy"),
                "release_cell_id_prefix": source_release_sampling.get("release_cell_id_prefix"),
                "sampling_weight_semantics": source_zone_policy.get("release_sampling", {}).get(
                    "sampling_weight_semantics"
                ),
                "annual_source_frequency_supported": source_release_sampling.get("annual_source_frequency_supported"),
                "physical_release_probability_supported": source_release_sampling.get(
                    "physical_release_probability_supported"
                ),
            },
            "output_mode": output_profile_report.get("validation_output_mode"),
            "conditional_curve_export": "summary-only",
            "grid_csv_export": "none",
            "output_profile_policy": OUTPUT_PROFILE_POLICY.classify_output_profile_policy(
                conditional_curve_export="summary-only",
                grid_csv_export="none",
                no_plots=True,
                label="minimum_measured_multi_zone_run",
            ),
            "export_geotiff": True,
            "pilot_gis_package": True,
            "trajectory_workers": 2,
            "reducer_workers": 2,
            "block_scenario_count": len(block_scenarios),
            "block_scenario_ids": [
                str(block_scenario.get("block_scenario_id"))
                for block_scenario in block_scenarios
                if isinstance(block_scenario, dict) and block_scenario.get("block_scenario_id")
            ],
            "estimated_runtime_seconds": estimates["estimated_runtime_seconds"],
            "estimated_storage_bytes": estimates["estimated_storage_bytes"],
            "estimated_file_count": estimates["estimated_file_count"],
            "estimated_manifest_pressure_bytes": estimates["estimated_manifest_pressure_bytes"],
            "manifest_pressure_reference": {
                "status": pressure_report.get("status"),
                "manifest_size_bytes": pressure_report.get("manifest_size_bytes"),
                "root_file_count": pressure_report.get("root_file_count"),
                "output_file_count": pressure_report.get("output_file_count"),
                "output_byte_count": pressure_report.get("output_byte_count"),
            },
            "reducer_pressure": dict(constraint_pressure_report),
            "preservation_gate_checklist": build_smallest_multi_zone_preservation_checklist(
                command_plan_path=artifact_dir / DEFAULT_COMMAND_PLAN_JSON.name,
                sbatch_script_path=artifact_dir / DEFAULT_SBATCH_PATH.name,
                package_json_path=artifact_dir / DEFAULT_PACKAGE_JSON.name,
                package_md_path=artifact_dir / DEFAULT_PACKAGE_MD.name,
                artifact_dir=artifact_dir,
                candidate_output_root=candidate_output_root,
                target_area_output_root=target_area_output_root,
                pressure_artifact_dir=pressure_artifact_dir,
                pressure_probe_root=pressure_probe_root,
                reviewed_handoff_package_path=package_json_path,
                authorization_record_path=authorization_record_path,
                review_command=review_command,
            ),
            "authorization_review_command": review_command,
            "authorization_submit_command": review_submit_command,
            "command_plan_review_command": review_command,
            "command_plan_submit_command": review_submit_command,
            "command_plan_path": str(artifact_dir / DEFAULT_COMMAND_PLAN_JSON.name),
            "sbatch_script_path": str(artifact_dir / DEFAULT_SBATCH_PATH.name),
            "reviewed_handoff_package_path": str(package_json_path),
            "authorization_record_path": str(authorization_record_path),
            "output_roots": {
                "artifact_dir": str(artifact_dir),
                "candidate_output_root": str(candidate_output_root),
                "target_area_output_root": str(target_area_output_root),
                "pressure_artifact_dir": str(pressure_artifact_dir),
                "pressure_probe_root": str(pressure_probe_root),
            },
        },
        "reason": (
            "The deterministic candidate sweep is ready for multi-zone scenario-generation stress tests, but the "
            "next live step should remain the smallest extra zone count and still require renewed human authorization."
        ),
        "candidate_readiness": readiness,
        "recommended_next_check": (
            "Review the package, then seek a new human authorization before any live multi-zone Balfrin job."
        ),
        "blocked_reason": "blocked_pending_authorization: review the exact later-submit command before any live run",
    }


def claim_boundaries(
    target_area_contract: dict[str, Any],
) -> dict[str, Any]:
    boundaries = dict(target_area_contract.get("claim_boundary") or {})
    boundaries.update(
        {
            "operational_claims_allowed": False,
            "annual_frequency_claims_allowed": False,
            "physical_probability_claims_allowed": False,
            "risk_exposure_vulnerability_claims_allowed": False,
            "scale_up_authorized": False,
            "distributed_execution_authorized": False,
            "target_area_demo_non_operational": True,
            "multi_zone_live_execution_authorized": False,
            "target_area_demo_bundle_status": "template_only",
        }
    )
    return boundaries


def section_provenance_counts(section_provenance_profile: list[dict[str, Any]]) -> dict[str, int]:
    counts = {"measured": 0, "fixture_backed": 0, "blocked_missing_inputs": 0}
    for section in section_provenance_profile:
        status = str(section.get("evidence_type") or "blocked_missing_inputs")
        if status not in counts:
            counts[status] = 0
        counts[status] += 1
    return counts


def build_section_provenance_profile(
    *,
    candidate_report: dict[str, Any],
    target_area_contract: dict[str, Any],
    output_profile_report: dict[str, Any],
    reducer_scaling_report: dict[str, Any],
    single_job_report: dict[str, Any],
    pressure_report: dict[str, Any],
    command_plan: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        {
            "section": "candidate_release_candidates",
            "status": candidate_report.get("candidate_metrics_status"),
            "evidence_type": evidence_type(candidate_report),
            "source_paths": [candidate_report.get("candidate_release_zone_products", {}).get("manifest_path")],
        },
        {
            "section": "deterministic_scenarios",
            "status": target_area_contract.get("contract_status"),
            "evidence_type": "derived",
            "source_paths": [str(DEFAULT_TARGET_AREA_CONTRACT), command_plan["command_plan_source_command"]],
        },
        {
            "section": "pressure_checkpoints",
            "status": output_profile_report.get("acceptance_classification"),
            "evidence_type": "measured",
            "source_paths": [
                output_profile_report.get("current_pressure", {}).get("source_record_path"),
                reducer_scaling_report.get("artifacts_measured", [{}])[0].get("validation_manifest_path")
                if reducer_scaling_report.get("artifacts_measured")
                else None,
            ],
        },
        {
            "section": "pressure_constraints",
            "status": pressure_report.get("status"),
            "evidence_type": "measured"
            if pressure_report.get("status") != "blocked_missing_inputs"
            else "blocked_missing_inputs",
            "source_paths": [
                pressure_report.get("measurement_command"),
                pressure_report.get("constraint_source", {}).get("source_document"),
                pressure_report.get("pressure_artifact_dir"),
            ],
        },
        {
            "section": "restartability",
            "status": single_job_report.get("final_classification"),
            "evidence_type": "measured",
            "source_paths": list(single_job_report.get("record_paths") or []),
        },
        {
            "section": "uncertainty_post_processing",
            "status": "planned",
            "evidence_type": "planned",
            "source_paths": [command["command"] for command in command_plan["commands"] if command["id"] in {"scientific_delta_report", "post_run_gate_preview"}],
        },
        {
            "section": "follow_up_recommendation",
            "status": "deferred_pending_authorization",
            "evidence_type": "derived",
            "source_paths": [],
        },
    ]


def classify_package_status(
    *,
    candidate_report: dict[str, Any],
    output_profile_report: dict[str, Any],
    reducer_scaling_report: dict[str, Any],
    single_job_report: dict[str, Any],
    pressure_report: dict[str, Any],
) -> str:
    sections = [
        candidate_report.get("candidate_metrics_status"),
        output_profile_report.get("acceptance_classification"),
        reducer_scaling_report.get("reducer_scaling_status"),
        single_job_report.get("final_classification"),
        pressure_report.get("status"),
    ]
    if any(status == "blocked_missing_inputs" for status in sections):
        return "blocked_missing_inputs"
    if any(
        status in {"defer", "ready", "mixed_provenance", "measured_existing_artifacts", "measured_scratch_root"}
        for status in sections
    ):
        return "mixed_provenance"
    return "ready"


def evidence_type(section_report: dict[str, Any]) -> str:
    if "candidate_release_zone_products" in section_report:
        return "generated"
    report_path = str(section_report.get("case_skeleton_output", {}).get("case_skeleton_path") or "")
    if report_path.startswith("/tmp/") or report_path.startswith(str(DEFAULT_ARTIFACT_DIR)):
        return "generated"
    return "measured"


def command_entry(
    *,
    command_id: str,
    group: str,
    description: str,
    command: str,
    expected_inputs: list[str],
    expected_outputs: list[str],
    read_only: bool,
    may_produce_ignored_outputs: bool,
    blocked_reason: str = "",
    ignored_output_paths: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "id": command_id,
        "group": group,
        "description": description,
        "command": command,
        "expected_inputs": expected_inputs,
        "expected_outputs": expected_outputs,
        "read_only": read_only,
        "may_produce_ignored_outputs": may_produce_ignored_outputs,
        "blocked_reason": blocked_reason,
        "ignored_output_paths": ignored_output_paths or [],
    }


def build_sbatch_script(report: dict[str, Any]) -> str:
    artifact_dir = Path(report["artifact_dir"])
    command_plan_path = Path(report["command_plan_path"])
    package_json_path = Path(report["package_json_path"])
    constraint_source = dict(report.get("constraint_pressure", {}).get("constraint_source") or {})
    follow_up = dict(report.get("follow_up_recommendation") or {})
    smallest_run = dict(follow_up.get("minimum_measured_multi_zone_run") or {})
    lines = [
        "#!/usr/bin/env bash",
        "#SBATCH --job-name=balfrin-multi-zone-demo",
        "#SBATCH --partition=postproc",
        "#SBATCH --time=00:30:00",
        "#SBATCH --nodes=1",
        "#SBATCH --ntasks=1",
        "#SBATCH --cpus-per-task=16",
        f"#SBATCH --output={shlex.quote((artifact_dir / 'logs' / 'slurm-%j.out').as_posix())}",
        f"#SBATCH --error={shlex.quote((artifact_dir / 'logs' / 'slurm-%j.err').as_posix())}",
        "",
        "set -euo pipefail",
        "",
        f"ARTIFACT_DIR={artifact_dir.as_posix()}",
        f"COMMAND_PLAN_PATH={command_plan_path.as_posix()}",
        f"PACKAGE_JSON_PATH={package_json_path.as_posix()}",
        "",
        'echo "Balfrin multi-release-zone dry-run handoff only."',
        'echo "Live execution requires new human authorization."',
        'echo "Deterministic merge order: sorted_chunk_id"',
        'echo "Restart/replay checkpoints: trajectory_execution_index.json, trajectory_merge_state.json, reducer_execution_index.json, reducer_merge_state.json"',
        f'echo "Blocked classification: {report.get("authorization_classification", report.get("submission_classification", "unknown"))}"',
        f'echo "Later review command: {smallest_run.get("authorization_review_command") or report.get("authorization_review_command", "unavailable")}"',
        f'echo "Later submit command: {smallest_run.get("command_plan_submit_command") or report.get("authorization_submit_command", "unavailable")}"',
        f'echo "Reviewed handoff package: {smallest_run.get("reviewed_handoff_package_path") or report.get("reviewed_handoff_package_path", "unavailable")}"',
        f'echo "Authorization record: {smallest_run.get("authorization_record_path") or report.get("authorization_record_path", "unavailable")}"',
        f'echo "Constraint source: {constraint_source.get("source_script", "scripts/summarize_multi_zone_reducer_pressure.py")}"',
        'echo "Command plan follows for review:"',
        'cat "${COMMAND_PLAN_PATH}"',
        "",
    ]
    return "\n".join(lines)


def write_package_files(report: dict[str, Any]) -> None:
    artifact_dir = Path(report["artifact_dir"])
    artifact_dir.mkdir(parents=True, exist_ok=True)
    (artifact_dir / "logs").mkdir(parents=True, exist_ok=True)
    (artifact_dir / DEFAULT_CANDIDATE_OUTPUT_ROOT.name).mkdir(parents=True, exist_ok=True)
    (artifact_dir / DEFAULT_TARGET_AREA_OUTPUT_ROOT.name).mkdir(parents=True, exist_ok=True)
    (artifact_dir / DEFAULT_OUTPUT_PROFILE_ARTIFACT_DIR.name).mkdir(parents=True, exist_ok=True)
    (artifact_dir / DEFAULT_REDUCER_ARTIFACT_DIR.name).mkdir(parents=True, exist_ok=True)
    (artifact_dir / DEFAULT_RESTARTABILITY_ARTIFACT_DIR.name).mkdir(parents=True, exist_ok=True)
    (artifact_dir / DEFAULT_UNCERTAINTY_ARTIFACT_DIR.name).mkdir(parents=True, exist_ok=True)

    command_plan_path = artifact_dir / DEFAULT_COMMAND_PLAN_JSON.name
    sbatch_path = artifact_dir / DEFAULT_SBATCH_PATH.name
    package_json_path = artifact_dir / DEFAULT_PACKAGE_JSON.name
    package_md_path = artifact_dir / DEFAULT_PACKAGE_MD.name

    command_plan_path.write_text(
        json.dumps(report["command_plan"], indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    sbatch_path.write_text(build_sbatch_script(report) + "\n", encoding="utf-8")
    sbatch_path.chmod(0o750)
    package_json_path.write_text(json.dumps(report, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    package_md_path.write_text(render_text_report(report) + "\n", encoding="utf-8")


def materialize_artifacts(
    report: dict[str, Any],
    *,
    json_output: Path | None = None,
    text_output: Path | None = None,
) -> None:
    if json_output is not None:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(report, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    if text_output is not None:
        text_output.parent.mkdir(parents=True, exist_ok=True)
        text_output.write_text(render_text_report(report) + "\n", encoding="utf-8")


def render_text_report(report: dict[str, Any]) -> str:
    if report.get("package_status") == "blocked_missing_inputs":
        missing_inputs = report.get("missing_inputs", [])
        lines = [
            "Balfrin Multi-Release-Zone Demo Package",
            "",
            f"- Package status: `{report.get('package_status', 'unknown')}`",
            f"- Authorization classification: `{report.get('authorization_classification', 'blocked_missing_inputs')}`",
            f"- Blocked classification: `{report.get('authorization_classification', 'blocked_missing_inputs')}`",
            f"- Blocked reason: {report.get('blocked_reason', '')}",
            f"- Output profile policy: `{report.get('output_profile_policy', {}).get('classification')}`",
            f"- Missing inputs: `{missing_inputs}`",
            f"- Review command: `{report.get('authorization_review_command', 'unavailable')}`",
            f"- Artifact dir: `{report.get('artifact_dir', 'unknown')}`",
            f"- Candidate output root: `{report.get('candidate_output_root', 'unknown')}`",
            f"- Target-area output root: `{report.get('target_area_output_root', 'unknown')}`",
        ]
        return "\n".join(lines)

    constraint_pressure = dict(report.get("constraint_pressure") or {})
    measured_constraints = dict(constraint_pressure.get("measured_constraints") or {})
    constraint_source = dict(constraint_pressure.get("constraint_source") or {})
    lines = [
        "Balfrin Multi-Release-Zone Demo Package",
        "",
        f"- Package status: `{report['package_status']}`",
        f"- Submission classification: `{report['submission_classification']}`",
        f"- Live execution requires new human authorization: `{report['live_execution_requires_new_human_authorization']}`",
        f"- Package constraint status: `{report['package_constraint_status']}`",
        f"- Constraint summary: {constraint_pressure.get('summary', 'unavailable')}",
        f"- Artifact dir: `{report['artifact_dir']}`",
        f"- Candidate output root: `{report['candidate_output_root']}`",
        f"- Target-area output root: `{report['target_area_output_root']}`",
        "",
        "## Candidate Release Candidates",
        "",
        f"- Candidate metrics status: `{report['candidate_release_candidates']['status']}`",
        f"- Multi-zone stress-test readiness: `{report['candidate_release_candidates']['multi_zone_stress_test_readiness'].get('status')}`",
        f"- Candidate output status: `{report['candidate_release_candidates']['candidate_output_status']}`",
        f"- Candidate output mode: `{report['candidate_release_candidates']['candidate_output_mode']}`",
        f"- Candidate count: `{report['candidate_release_candidates']['candidate_count']}`",
        f"- Candidate component count: `{report['candidate_release_candidates']['candidate_component_count']}`",
        "",
        "## Deterministic Scenarios",
        "",
        f"- Target-area bundle status: `{report['deterministic_scenarios']['status']}`",
        f"- Scenario generation command: `{report['deterministic_scenarios']['scenario_generation_command']}`",
        f"- Scenario table row count: `{report['deterministic_scenarios']['scenario_table_row_count']}`",
        f"- Scenario probability semantics: `{report['deterministic_scenarios']['scenario_probability_semantics']}`",
        "",
        "## Pressure Checkpoints",
        "",
        f"- Estimated runtime checkpoint status: `{report['pressure_checkpoints']['estimated_runtime']['single_job_decision']}`",
        f"- Output-pressure status: `{report['pressure_checkpoints']['output_pressure']['status']}`",
        f"- Reducer-chunk pressure status: `{report['pressure_checkpoints']['reducer_chunk_pressure']['status']}`",
        f"- Restartability status: `{report['pressure_checkpoints']['restartability']['status']}`",
        f"- Reducer merge order: `{report['pressure_checkpoints']['restartability']['reducer_state'].get('reducer_merge_order')}`",
        "",
        "## Multi-Zone Constraints",
        "",
        f"- Constraint status: `{constraint_pressure.get('status')}`",
        f"- Requested release-zone batch size: `{constraint_pressure.get('requested_release_zone_batch_size')}`",
        f"- Requested reducer chunk count: `{constraint_pressure.get('requested_reducer_chunk_count')}`",
        f"- Requested reducer worker count: `{constraint_pressure.get('requested_reducer_worker_count')}`",
        f"- Measured simultaneous release-zone batch max: `{measured_constraints.get('simultaneous_release_zone_batch_max')}`",
        f"- Measured reducer chunk max: `{measured_constraints.get('reducer_chunk_count_max')}`",
        f"- Measured reducer worker max: `{measured_constraints.get('reducer_worker_count_max')}`",
        f"- Measured manifest size bytes max: `{measured_constraints.get('manifest_size_bytes_max')}`",
        f"- Measured root file count max: `{measured_constraints.get('root_file_count_max')}`",
        f"- Measured output file count max: `{measured_constraints.get('output_file_count_max')}`",
        f"- Constraint source: `{constraint_source.get('source_document')}`",
        "",
        "## Output Profile Policy",
        "",
        f"- Command-plan classification: `{report.get('output_profile_policy', {}).get('classification')}`",
        f"- Blocked policy labels: `{report.get('output_profile_policy', {}).get('blocked_policy_labels', [])}`",
        f"- Scalable policy labels: `{report.get('output_profile_policy', {}).get('scalable_policy_labels', [])}`",
        "",
        "## Uncertainty Post-Processing",
        "",
        f"- Scientific delta status: `{report['uncertainty_post_processing']['status']}`",
        f"- Post-run gate status: `{report['uncertainty_post_processing']['post_run_interpretation_gate_status']}`",
        f"- Remaining uncertainty count: `{len(report['uncertainty_post_processing']['remaining_uncertainty'])}`",
        f"- Uncertainty-reduced count: `{len(report['uncertainty_post_processing']['uncertainty_reduced'])}`",
        "",
        "## Follow-Up Recommendation",
        "",
        f"- Status: `{report['follow_up_recommendation']['status']}`",
        f"- Live execution requires new human authorization: `{report['follow_up_recommendation']['live_execution_requires_new_human_authorization']}`",
        f"- Recommended release-zone count: `{report['follow_up_recommendation']['minimum_measured_multi_zone_run']['release_zone_count']}`",
        f"- Recommended scenario count: `{report['follow_up_recommendation']['minimum_measured_multi_zone_run'].get('scenario_count')}`",
        f"- Recommended trajectory count target: `{report['follow_up_recommendation']['minimum_measured_multi_zone_run'].get('trajectory_count_target')}`",
        f"- Authorization classification: `{report.get('authorization_classification', 'unknown')}`",
        f"- Blocked classification: `{report.get('authorization_classification', 'unknown')}`",
        f"- Review command: `{report['follow_up_recommendation']['authorization_review_command']}`",
        f"- Submit command: `{report['follow_up_recommendation']['authorization_submit_command']}`",
        f"- Reviewed handoff package: `{report['follow_up_recommendation']['minimum_measured_multi_zone_run'].get('reviewed_handoff_package_path')}`",
        f"- Authorization record: `{report['follow_up_recommendation']['minimum_measured_multi_zone_run'].get('authorization_record_path')}`",
        f"- Recommended validation output mode: `{report['follow_up_recommendation']['minimum_measured_multi_zone_run']['output_mode']}`",
        f"- Recommended output profile policy: `{report['follow_up_recommendation']['minimum_measured_multi_zone_run'].get('output_profile_policy', {}).get('classification')}`",
        f"- Reason: {report['follow_up_recommendation']['reason']}",
        "",
        "## Smallest Run Estimates",
        "",
        f"- Release cell count: `{report['follow_up_recommendation']['minimum_measured_multi_zone_run'].get('release_cell_count')}`",
        f"- Seed policy: `{report['follow_up_recommendation']['minimum_measured_multi_zone_run'].get('seed_policy')}`",
        f"- Block scenario count: `{report['follow_up_recommendation']['minimum_measured_multi_zone_run'].get('block_scenario_count')}`",
        f"- Estimated runtime seconds: `{report['follow_up_recommendation']['minimum_measured_multi_zone_run'].get('estimated_runtime_seconds')}`",
        f"- Estimated storage bytes: `{report['follow_up_recommendation']['minimum_measured_multi_zone_run'].get('estimated_storage_bytes')}`",
        f"- Estimated file count: `{report['follow_up_recommendation']['minimum_measured_multi_zone_run'].get('estimated_file_count')}`",
        f"- Estimated manifest pressure bytes: `{report['follow_up_recommendation']['minimum_measured_multi_zone_run'].get('estimated_manifest_pressure_bytes')}`",
        "",
        "## Preservation Checklist",
        "",
    ]
    for checklist_item in report["follow_up_recommendation"]["minimum_measured_multi_zone_run"].get("preservation_gate_checklist", []):
        lines.append(f"- {checklist_item}")
    lines.extend(
        [
            "",
            "## Output Roots",
            "",
        ]
    )
    for key, value in report["follow_up_recommendation"]["minimum_measured_multi_zone_run"].get("output_roots", {}).items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(
        [
            "",
            "## Command Plan",
            "",
            f"- Canonical ancestor: `{report['canonical_command_plan_reference']['source_script']}`",
        ]
    )
    for command in report["command_plan"]["commands"]:
        lines.append(f"- `{command['id']}`: {command['description']}")
    lines.extend(
        [
            "",
            "## Do Not Commit",
            "",
            "Do not commit any generated Balfrin multi-zone outputs or scratch-root artifacts from the paths listed below.",
        ]
    )
    for root in report["ignored_output_roots"]:
        lines.append(f"- `{root}`")
    for path in (
        report["command_plan_path"],
        report["sbatch_script_path"],
        report["package_json_path"],
        report["package_md_path"],
    ):
        lines.append(f"- `{path}`")
    return "\n".join(lines)


def command_string(parts: list[str]) -> str:
    return shlex.join(parts)


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def safe_build(label: str, builder: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    try:
        return builder()
    except Exception as exc:  # noqa: BLE001 - package generation should fail closed with explicit context.
        return {
            "status": "blocked_missing_inputs",
            "blocked_reason": f"{label} helper failed: {exc}",
            "missing_inputs": [str(exc)],
        }


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def dump_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def dump_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def require_mapping(value: Any, context: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise BalfrinMultiReleaseZoneDemoHandoffError(f"{context} must be a YAML mapping")
    return value


def resolve_repo_path(value: Any) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise BalfrinMultiReleaseZoneDemoHandoffError("missing required repository path value")
    path = Path(value)
    return path if path.is_absolute() else (ROOT / path)


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def text_value(value: Any, context: str) -> str:
    if value in (None, ""):
        raise BalfrinMultiReleaseZoneDemoHandoffError(f"{context} is missing")
    return str(value).strip()


def count_csv_rows(path: Path) -> int:
    with path.open("r", encoding="utf-8", newline="") as fh:
        return sum(1 for _ in csv.DictReader(fh))


def resolve_output_root(path: Path) -> Path:
    if path.is_absolute():
        return path.resolve()
    return (ROOT / path).resolve()


def is_allowed_output_root(path: Path) -> bool:
    try:
        path.relative_to(Path("/tmp").resolve())
        return True
    except ValueError:
        pass
    try:
        path.relative_to((ROOT / "validation" / "private").resolve())
        return True
    except ValueError:
        return False


def section_provenance_counts(section_provenance_profile: list[dict[str, Any]]) -> dict[str, int]:
    counts = {"measured": 0, "generated": 0, "blocked_missing_inputs": 0}
    for section in section_provenance_profile:
        evidence_type = str(section.get("evidence_type") or "blocked_missing_inputs")
        if evidence_type not in counts:
            counts[evidence_type] = 0
        counts[evidence_type] += 1
    return counts


def build_sbatch_script_text(report: dict[str, Any]) -> str:
    return build_sbatch_script(report)


def build_follow_up_recommendation_summary(report: dict[str, Any]) -> str:
    recommendation = report["follow_up_recommendation"]["minimum_measured_multi_zone_run"]
    return (
        f"{report['follow_up_recommendation']['reason']} "
        f"Smallest measured multi-zone run: {recommendation['release_zone_count']} release zones, "
        f"{recommendation['output_mode']} output mode, {recommendation['trajectory_workers']} trajectory workers, "
        f"{recommendation['reducer_workers']} reducer workers."
    )


if __name__ == "__main__":
    raise SystemExit(main())
