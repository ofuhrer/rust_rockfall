#!/usr/bin/env python3
"""Emit canonical portable pilot command plans without executing them.

The helper consolidates the frozen Tschamut same-scale execution steps and the
metadata-only Chant Sura / Flüelapass portability checks into a stable
machine-readable plan. It is read-only and does not run any of the commands it
reports.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.lib import command_plan_contract as COMMAND_PLAN
from scripts.lib import command_plan_output_profile_validator as OUTPUT_PROFILE_VALIDATOR
from scripts.lib import output_profile_policy as OUTPUT_PROFILE_POLICY
from scripts.lib.workflow_validation import load_repo_script_module


SCHEMA_VERSION = "portable_pilot_command_plan_v1"
DISTRIBUTED_EXECUTION_CONTRACT_SCHEMA_VERSION = "distributed_execution_contract_v1"
LOCAL_DISTRIBUTED_ORCHESTRATION_DRY_RUN_SCHEMA_VERSION = "local_distributed_orchestration_dry_run_v1"
DEFAULT_SECOND_SITE_CONFIG = ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml"


READINESS = load_repo_script_module(
    ROOT,
    "pilot_command_plan_same_scale_readiness",
    "check_same_scale_artifact_readiness.py",
    error_message="unable to load helper module from",
)
PORTABILITY = load_repo_script_module(
    ROOT,
    "pilot_command_plan_second_site_portability",
    "check_second_site_public_geodata_preflight.py",
    error_message="unable to load helper module from",
)
CASE_GENERATION = load_repo_script_module(
    ROOT,
    "pilot_command_plan_case_generation",
    "generate_tschamut_same_scale_cases.py",
    error_message="unable to load helper module from",
)
CONTRACT = load_repo_script_module(
    ROOT,
    "pilot_command_plan_contract_audit",
    "audit_multisite_source_scenario_contract.py",
    error_message="unable to load helper module from",
)
OUTPUT_PROFILE = load_repo_script_module(
    ROOT,
    "pilot_command_plan_output_profile",
    "check_hazard_rebuild_output_profile.py",
    error_message="unable to load helper module from",
)
REDUCED_PROFILE = load_repo_script_module(
    ROOT,
    "pilot_command_plan_reduced_profile",
    "derive_hazard_rebuild_reduced_profile.py",
    error_message="unable to load helper module from",
)
CHANT_SURA_DRY_RUN_CASE_SKELETON = load_repo_script_module(
    ROOT,
    "pilot_command_plan_chant_sura_dry_run_case_skeleton",
    "generate_chant_sura_fluelapass_dry_run_case_skeleton.py",
    error_message="unable to load helper module from",
)
REDUCED_VALIDATION_CASE = ROOT / "tests/fixtures/rebuildable_reduced_output/tschamut_public_target_gate_rebuildable_reduced_case.yaml"
CASE_SKELETON_OUTPUT_ROOT = CHANT_SURA_DRY_RUN_CASE_SKELETON.DEFAULT_OUTPUT_ROOT
CASE_SKELETON_OUTPUT_PATH = CASE_SKELETON_OUTPUT_ROOT / CHANT_SURA_DRY_RUN_CASE_SKELETON.CASE_FILENAME
VALIDATION_OUTPUT_REPLAY_CRITICAL_CLASSES = [
    "manifest_json",
    "diagnostics_json",
    "trajectory_csv",
    "trajectory_metadata_csv",
    "ensemble_deposition_csv",
    "impact_events_csv",
    "stop_state_summary_csv",
]
VALIDATION_OUTPUT_DEBUG_CLASSES = [
    "ensemble_trajectories_dir",
    "ensemble_impact_events_dir",
    "ensemble_impact_events_parquet",
]
SUPPORTED_DISTRIBUTED_PHASES = ("trajectory_generation", "hazard_reduction")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--site",
        choices=("all", "tschamut_same_scale", "chant_sura_fluelapass"),
        default="all",
        help="which portable plan to emit",
    )
    parser.add_argument(
        "--site-config",
        type=Path,
        default=DEFAULT_SECOND_SITE_CONFIG,
        help="second-site portability config used for Chant Sura / Flüelapass",
    )
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    args = parser.parse_args(argv)

    report = build_report(args.site, args.site_config)

    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    output = json.dumps(report, indent=2, sort_keys=True) if args.format == "json" else render_text_report(report)
    print(output)
    return 0


def build_report(site: str, site_config: Path) -> dict[str, Any]:
    readiness_report = READINESS.build_readiness_report()
    second_site_report = PORTABILITY.build_report(site_config, site_id=None)
    contract_report = CONTRACT.build_report(site_config)
    output_profile_report = OUTPUT_PROFILE.build_report(list(OUTPUT_PROFILE.DEFAULT_PROFILE_SPECS))

    site_plans: dict[str, dict[str, Any]] = {}
    if site in {"all", "tschamut_same_scale"}:
        site_plans["tschamut_same_scale"] = build_tschamut_site_plan(readiness_report, output_profile_report)
    if site in {"all", "chant_sura_fluelapass"}:
        site_plans["chant_sura_fluelapass"] = build_second_site_plan(second_site_report, contract_report, site_config)

    flattened_groups: list[dict[str, Any]] = []
    flattened_commands: list[dict[str, Any]] = []
    for site_name, plan in site_plans.items():
        for group in plan["command_groups"]:
            group_with_key = dict(group)
            group_with_key["site"] = site_name
            group_with_key["group_key"] = f"{site_name}::{group['id']}"
            flattened_groups.append(group_with_key)
        flattened_commands.extend(plan["commands"])

    blocked_template_commands = sorted(
        command["id"] for command in flattened_commands if command.get("blocked_reason")
    )
    output_profile_policies = [
        plan["output_profile_policy"]
        for plan in site_plans.values()
        if plan.get("output_profile_policy") is not None
    ]
    output_profile_validation = OUTPUT_PROFILE_VALIDATOR.validate_command_plan_output_profile(
        flattened_commands,
        label="pilot_command_plan",
    )
    distributed_execution_contract = build_distributed_execution_contract(flattened_commands)
    local_distributed_dry_run = build_local_distributed_orchestration_dry_run(distributed_execution_contract)
    ignored_output_paths = sorted(
        {
            *readiness_ignored_output_paths(),
            *(path for plan in site_plans.values() for path in plan.get("ignored_output_paths", [])),
        }
    )

    report = {
        "schema_version": SCHEMA_VERSION,
        "command_plan_status": (
            "ready"
            if output_profile_validation["status"] == OUTPUT_PROFILE_VALIDATOR.STATUS_READY
            else output_profile_validation["status"]
        ),
        "tschamut_readiness_status": readiness_report["readiness_status"],
        "tschamut_hazard_rebuild_output_profile_status": output_profile_report["hazard_rebuild_output_profile_status"],
        "tschamut_rebuildable_reduced_profile_classification": output_profile_report["profile_classifications"].get(
            "target_rebuildable_reduced"
        ),
        "tschamut_native_rebuildable_reduced_profile_classification": output_profile_report["profile_classifications"].get(
            "native_rebuildable_reduced_output"
        ),
        "default_local_hazard_smoke_recommendation": output_profile_report.get(
            "default_local_hazard_smoke_recommendation",
            {
                "recommendation_status": "blocked_missing_rebuildable_reduced_profile",
                "recommended_validation_output_mode": "rebuildable_reduced_output",
                "recommended_profile_id": None,
                "recommended_profile_label": None,
                "recommended_profile_root": None,
                "next_command": "PYENV_VERSION=system uv run python scripts/check_hazard_rebuild_output_profile.py --format json",
                "rebuild_instruction": "restore or derive the native rebuildable reduced profile before local hazard smoke replay",
                "full_output_recovery": {
                    "recovery_status": "full_outputs_available_on_explicit_request",
                    "full_output_profile_id": "target_validation",
                    "full_output_profile_label": "bounded_probe_full_v1",
                    "full_output_profile_root": "validation/private/tschamut_public_pilot/target_gate_v1",
                    "full_output_case_path": "validation/private/tschamut_public_pilot/target_gate_v1/tschamut_public_target_gate_case.yaml",
                    "full_output_command": (
                        "PYENV_VERSION=system CARGO_TARGET_DIR=/tmp/rust-rockfall-target cargo run -- validate --case "
                        "validation/private/tschamut_public_pilot/target_gate_v1/tschamut_public_target_gate_case.yaml"
                    ),
                    "full_output_notes": (
                        "Use the full validation case when explicitly requesting the heavier historical output set; "
                        "the reduced profile remains the local default."
                    ),
                },
                "claim_boundary": "local smoke recommendation only; no scale-up authorization or claim upgrade",
            },
        ),
        "second_site_portability_status": second_site_report["portability_preflight_status"],
        "second_site_portability_semantics_summary": contract_report.get("portability_semantics_summary", {}),
        "public_context_boundary_status": second_site_report["public_context_boundary_status"],
        "deferred_public_context_categories": second_site_report["deferred_public_context_categories"],
        "public_context_product_requirements": second_site_report["public_context_product_requirements"],
        "blocked_second_site_commands": second_site_report["blocked_second_site_commands"],
        "claim_boundaries": second_site_report["claim_boundaries"],
        "supported_sites_or_modes": ["all", "tschamut_same_scale", "chant_sura_fluelapass"],
        "read_only": True,
        "scale_up_authorized": False,
        "operational_claims_allowed": False,
        "site_plans": site_plans,
        "output_profile_policy": OUTPUT_PROFILE_POLICY.summarize_output_profile_policies(
            output_profile_policies, label="pilot_command_plan"
        ),
        "output_profile_validation": output_profile_validation,
        "distributed_execution_contract": distributed_execution_contract,
        "local_distributed_orchestration_dry_run": local_distributed_dry_run,
        "command_groups": flattened_groups,
        "commands": flattened_commands,
        "command_ids": COMMAND_PLAN.command_ids(flattened_commands),
        "command_descriptions": COMMAND_PLAN.command_descriptions(flattened_commands),
        "blocked_template_commands": blocked_template_commands,
        "ignored_output_paths": ignored_output_paths,
        "command_group_ids": [group["id"] for group in flattened_groups],
        "command_group_keys": [group["group_key"] for group in flattened_groups],
    }
    return report


def build_local_distributed_orchestration_dry_run(contract: dict[str, Any]) -> dict[str, Any]:
    fixture_rows = [
        {"fixture_row": 0, "cell": "0,0", "reach": 1, "kinetic_j": 10.0, "jump_m": 0.5, "deposition": 1, "significant_impact": 0},
        {"fixture_row": 1, "cell": "0,1", "reach": 1, "kinetic_j": 15.0, "jump_m": 0.2, "deposition": 0, "significant_impact": 1},
        {"fixture_row": 2, "cell": "0,0", "reach": 1, "kinetic_j": 6.0, "jump_m": 1.5, "deposition": 2, "significant_impact": 0},
        {"fixture_row": 3, "cell": "1,1", "reach": 1, "kinetic_j": 20.0, "jump_m": 0.7, "deposition": 1, "significant_impact": 1},
        {"fixture_row": 4, "cell": "0,1", "reach": 1, "kinetic_j": 12.0, "jump_m": 0.9, "deposition": 1, "significant_impact": 0},
    ]
    chunk_records = build_distributed_fixture_chunk_records(
        prefix="fixture_local_distributed",
        chunk_count=3,
        phase="hazard_reduction",
    )
    chunk_payloads: list[dict[str, Any]] = []
    for chunk in chunk_records:
        start = int(chunk["chunk_index"]) * 2
        end = min(start + 2, len(fixture_rows))
        if start >= len(fixture_rows):
            rows: list[dict[str, Any]] = []
        else:
            rows = fixture_rows[start:end]
        chunk_payloads.append(
            {
                **chunk,
                "input_index_start": start,
                "input_index_end_exclusive": end,
                "input_signature": stable_json_digest(rows),
                "first_attempt_status": "failed" if chunk["chunk_index"] == 1 else "completed",
                "final_status": "completed",
                "attempt_count": 2 if chunk["chunk_index"] == 1 else 1,
                "retry_count": 1 if chunk["chunk_index"] == 1 else 0,
                "orchestration_decision": "retried_after_transient_fixture_failure"
                if chunk["chunk_index"] == 1
                else "executed",
                "partial_state": reduce_fixture_rows(rows),
            }
        )
    merged_state = merge_fixture_states([chunk["partial_state"] for chunk in sorted(chunk_payloads, key=lambda item: item["chunk_id"])])
    single_process_state = reduce_fixture_rows(fixture_rows)
    comparison = {
        "match": merged_state == single_process_state,
        "merged_state": merged_state,
        "single_process_state": single_process_state,
    }
    return {
        "schema_version": LOCAL_DISTRIBUTED_ORCHESTRATION_DRY_RUN_SCHEMA_VERSION,
        "dry_run_status": "fixture_replay_matched" if comparison["match"] else "fixture_replay_mismatch",
        "contract_schema_version": contract.get("schema_version"),
        "executed_locally": True,
        "distributed_execution_authorized": False,
        "chunk_count": len(chunk_payloads),
        "simulated_retry_count": sum(int(chunk["retry_count"]) for chunk in chunk_payloads),
        "merge_order": "sorted_chunk_id",
        "chunk_ids": [str(chunk["chunk_id"]) for chunk in sorted(chunk_payloads, key=lambda item: item["chunk_id"])],
        "chunk_records": chunk_payloads,
        "comparison": comparison,
        "replay_critical_outputs_preserved": [
            "execution_plan",
            "chunk_manifests",
            "partial_state",
            "execution_index",
            "merge_state",
        ],
        "remaining_cluster_side_blockers": [
            "scheduler submission and collection are not implemented for distributed chunks",
            "shared filesystem locking/lease behavior has not been exercised on Balfrin",
            "multi-process or multi-node worker isolation has not been measured",
            "large AOI output budgets and restart costs remain unmeasured",
        ],
        "claim_boundary": "local in-memory fixture orchestration only; no distributed, Swiss-wide, or operational execution claim",
    }


def reduce_fixture_rows(rows: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    reach: dict[str, float] = {}
    max_ke: dict[str, float] = {}
    max_jump: dict[str, float] = {}
    deposition: dict[str, float] = {}
    significant_impact: dict[str, float] = {}
    for row in rows:
        cell = str(row["cell"])
        reach[cell] = reach.get(cell, 0.0) + float(row["reach"])
        max_ke[cell] = max(max_ke.get(cell, float("-inf")), float(row["kinetic_j"]))
        max_jump[cell] = max(max_jump.get(cell, float("-inf")), float(row["jump_m"]))
        deposition[cell] = deposition.get(cell, 0.0) + float(row["deposition"])
        significant_impact[cell] = significant_impact.get(cell, 0.0) + float(row["significant_impact"])
    return {
        "reach_counts": sorted_numeric_mapping(reach),
        "max_kinetic_energy": sorted_numeric_mapping(max_ke),
        "max_jump_height": sorted_numeric_mapping(max_jump),
        "deposition_density_counts": sorted_numeric_mapping(deposition),
        "significant_impact_counts": sorted_numeric_mapping(significant_impact),
    }


def merge_fixture_states(states: list[dict[str, dict[str, float]]]) -> dict[str, dict[str, float]]:
    merged = {
        "reach_counts": {},
        "max_kinetic_energy": {},
        "max_jump_height": {},
        "deposition_density_counts": {},
        "significant_impact_counts": {},
    }
    for state in states:
        add_numeric_mapping(merged["reach_counts"], state.get("reach_counts", {}))
        max_numeric_mapping(merged["max_kinetic_energy"], state.get("max_kinetic_energy", {}))
        max_numeric_mapping(merged["max_jump_height"], state.get("max_jump_height", {}))
        add_numeric_mapping(merged["deposition_density_counts"], state.get("deposition_density_counts", {}))
        add_numeric_mapping(merged["significant_impact_counts"], state.get("significant_impact_counts", {}))
    return {key: sorted_numeric_mapping(value) for key, value in merged.items()}


def add_numeric_mapping(target: dict[str, float], source: dict[str, float]) -> None:
    for key, value in source.items():
        target[key] = target.get(key, 0.0) + float(value)


def max_numeric_mapping(target: dict[str, float], source: dict[str, float]) -> None:
    for key, value in source.items():
        target[key] = max(target.get(key, float("-inf")), float(value))


def sorted_numeric_mapping(values: dict[str, float]) -> dict[str, float]:
    return {key: values[key] for key in sorted(values)}


def stable_json_digest(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def build_distributed_execution_contract(commands: list[dict[str, Any]]) -> dict[str, Any]:
    scalable_hazard_commands = [
        command
        for command in commands
        if command.get("group") == "hazard_builds"
        and command.get("output_profile_policy", {}).get("classification") == OUTPUT_PROFILE_POLICY.SCALABLE_DEFAULT
    ]
    return {
        "schema_version": DISTRIBUTED_EXECUTION_CONTRACT_SCHEMA_VERSION,
        "contract_status": "defined_not_executed",
        "distributed_execution_authorized": False,
        "execution_model": "single_node_chunk_contract_ready_multi_process_deferred",
        "supported_phases": list(SUPPORTED_DISTRIBUTED_PHASES),
        "applicable_command_ids": [str(command["id"]) for command in scalable_hazard_commands],
        "split_task_manifest": {
            "schema_versions": {
                "trajectory_execution_plan": "trajectory_execution_plan_v1",
                "hazard_reducer_execution_plan": "execution_plan_v1",
                "trajectory_chunk_manifest": "trajectory_generation_chunk_manifest_v1",
                "hazard_reducer_chunk_manifest": "hazard_reducer_chunk_manifest_v1",
                "execution_index": "reducer_execution_index_v1",
                "merge_state": "reducer_merge_state_v1",
            },
            "required_fields": [
                "plan_id",
                "plan_status",
                "chunk_count",
                "chunk_ids",
                "chunk_manifests",
                "merge_order",
                "merge_group_id",
                "scheduler_index",
                "scheduler_count",
                "owner_id",
                "max_chunk_attempts",
                "claim_ttl_seconds",
                "input_file_count",
            ],
        },
        "chunk_key_contract": {
            "chunk_id_policy": "stable_prefix_sorted_chunk_index",
            "trajectory_chunk_template": "{prefix}__trajectory_chunk_{chunk_index:04d}",
            "hazard_reducer_chunk_template": "{prefix}__chunk_{chunk_index:04d}",
            "chunk_index_base": 0,
            "chunk_assignment_rule": "scheduler_index selects chunks where chunk_index % scheduler_count == scheduler_index",
            "identity_fields": [
                "site",
                "phase",
                "prefix",
                "chunk_index",
                "input_index_start",
                "input_index_end_exclusive",
                "input_signature",
                "execution_signature",
            ],
            "fixture_chunk_id_examples": build_distributed_fixture_chunk_records(
                prefix="tschamut_public_target_gate_v1",
                chunk_count=4,
                phase="hazard_reduction",
            ),
        },
        "merge_contract": {
            "merge_order": "sorted_chunk_id",
            "merge_group_id_source": "hash_of_plan_prefix_ranges_and_input_artifacts",
            "operations": {
                "reach_counts": "cellwise integer counts add across chunks",
                "threshold_exceedance_counts": "cellwise integer or sampling-weighted counts add across chunks",
                "max_kinetic_energy": "cellwise maximum across chunks",
                "max_jump_height": "cellwise maximum across chunks",
                "deposition_density_counts": "cellwise deposition counts add across chunks",
                "significant_impact_counts": "cellwise significant-impact counts add across chunks",
            },
            "required_pre_merge_state": "all chunks completed or merge_state remains incomplete",
        },
        "retry_and_restart_contract": {
            "max_chunk_attempts": 3,
            "claim_ttl_seconds": 3600,
            "restart_state": "partial_state_path plus execution_signature",
            "reuse_rule": "reuse completed partial state only when chunk_id and input_signature and execution_signature match",
            "stale_state_rule": "release and rerun stale chunks when signatures differ or claims expire",
            "failure_rule": "record failed chunk ids; do not emit a completed merge state until all planned chunks complete",
        },
        "idempotency_contract": {
            "rerun_same_plan": "same prefix and sorted input artifacts keep chunk ids stable",
            "rerun_changed_inputs": "input_signature changes force stale-state rejection",
            "output_write_policy": "chunk manifests and partial states are addressed by chunk id; final merge output is deterministic after sorted merge",
        },
        "provenance_contract": {
            "required_per_chunk_fields": [
                "chunk_id",
                "chunk_index",
                "input_signature",
                "execution_signature",
                "execution_plan.plan_id",
                "execution_plan.plan_path",
                "merge_group_id",
                "attempt_count",
                "retry_count",
                "ownership",
                "input_artifacts",
                "output_bytes",
                "timings",
            ],
            "required_plan_fields": [
                "plan_id",
                "output_manifest_path",
                "scheduled_chunk_ids",
                "completed_chunk_count",
                "failed_chunk_count",
                "chunk_ids_completed",
                "chunk_ids_failed",
            ],
            "claim_boundary": "contract only; no multi-node, scheduler, Swiss-wide, or operational execution claim",
        },
        "smallest_future_distributed_dry_run_task": {
            "task": "Implement a local distributed dry run that splits fixture hazard inputs into at least three chunks, simulates one stale/retried chunk by preserving partial state, merges by sorted chunk id, and compares the merged output with an equivalent single-process fixture output.",
            "expected_fixture_inputs": [
                "tests/fixtures/hazard/plane_case.yaml",
                "tests/fixtures/hazard/*trajectory*.csv",
            ],
            "expected_assertions": [
                "chunk ids are stable across reruns",
                "changed input signatures invalidate stale partial state",
                "merge order is sorted by chunk id",
                "merged fixture output equals single-process fixture output",
            ],
        },
    }


def build_distributed_fixture_chunk_records(
    *,
    prefix: str,
    chunk_count: int,
    phase: str,
) -> list[dict[str, Any]]:
    if chunk_count < 1:
        raise ValueError("chunk_count must be at least 1")
    if phase not in SUPPORTED_DISTRIBUTED_PHASES:
        raise ValueError(f"unsupported distributed phase: {phase}")
    safe_prefix = str(prefix).replace(" ", "_")
    infix = "trajectory_chunk" if phase == "trajectory_generation" else "chunk"
    records = [
        {
            "phase": phase,
            "chunk_index": index,
            "chunk_id": f"{safe_prefix}__{infix}_{index:04d}",
            "input_index_start": index,
            "input_index_end_exclusive": index + 1,
            "partial_state_path": f"<output_root>/{phase}_chunks/{safe_prefix}__{infix}_{index:04d}_state.json",
            "manifest_path": f"<output_root>/{phase}_chunks/{safe_prefix}__{infix}_{index:04d}_manifest.json",
        }
        for index in range(chunk_count)
    ]
    return sorted(records, key=lambda record: record["chunk_id"])


def build_tschamut_site_plan(
    readiness_report: dict[str, Any],
    output_profile_report: dict[str, Any],
) -> dict[str, Any]:
    ignored_output_paths = readiness_ignored_output_paths()
    ignored_output_paths.append(rel(REDUCED_PROFILE.DEFAULT_OUTPUT_ROOT))
    commands: list[dict[str, Any]] = []

    commands.append(
        command_entry(
            site="tschamut_same_scale",
            group="readiness_checks",
            command_id="tschamut_readiness_preflight",
            description="Check same-scale Tschamut artifact readiness and regeneration commands.",
            command=command_string(
                [
                    "PYENV_VERSION=system",
                    "uv",
                    "run",
                    "python",
                    rel(ROOT / "scripts" / "check_same_scale_artifact_readiness.py"),
                    "--format",
                    "json",
                ]
            ),
            expected_inputs=[
                "validation/private/tschamut_public_pilot/gate_v1",
                "validation/private/tschamut_public_pilot/target_gate_v1",
                "validation/private/tschamut_public_pilot/target_gate_v1_summary_only",
                "hazard/results/tschamut_public_pilot/gate_v1",
                "hazard/results/tschamut_public_pilot/target_gate_v1",
                "data/processed/swisstopo/tschamut_public_pilot/context",
            ],
            expected_outputs=["JSON readiness report", "human-readable readiness summary"],
            read_only=True,
            may_produce_ignored_outputs=False,
        )
    )
    commands.append(
        command_entry(
            site="tschamut_same_scale",
            group="case_generation",
            command_id="tschamut_case_generation",
            description="Regenerate the frozen Tschamut same-scale gate and target case YAMLs.",
            command=command_string(
                [
                    "PYENV_VERSION=system",
                    "uv",
                    "run",
                    "python",
                    rel(ROOT / "scripts" / "generate_tschamut_same_scale_cases.py"),
                    "--role",
                    "both",
                    "--output-root",
                    rel(ROOT / "validation/private/tschamut_public_pilot"),
                    "--format",
                    "json",
                ]
            ),
            expected_inputs=[
                "validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml",
                "validation/pilot_runs/tschamut_public_scalable_conditional_target_gate_v1.yaml",
                "validation/policies/tschamut_public_source_scenario_policy_v1.yaml",
                "data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_source_zone_metadata_v1.yaml",
                "data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_scenario_table_v1.csv",
                "data/processed/swisstopo/tschamut_public_pilot/input/release_points_lv95.csv",
                "data/processed/swisstopo/tschamut_public_pilot/input/observed_deposition_lv95.csv",
                "data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_swissalti3d_metadata.yaml",
                "data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_swissalti3d_crop.asc",
            ],
            expected_outputs=[
                "validation/private/tschamut_public_pilot/gate_v1/tschamut_public_conditional_gate_case.yaml",
                "validation/private/tschamut_public_pilot/target_gate_v1/tschamut_public_target_gate_case.yaml",
            ],
            read_only=False,
            may_produce_ignored_outputs=True,
            ignored_output_paths=[
                "validation/private/tschamut_public_pilot/gate_v1",
                "validation/private/tschamut_public_pilot/target_gate_v1",
            ],
        )
    )
    commands.extend(build_gis_cog_package_conversion_commands())
    commands.extend(build_rebuildable_reduced_output_commands())
    commands.extend(build_balfrin_single_release_zone_plan_commands())
    commands.extend(
        [
            command_entry(
                site="tschamut_same_scale",
                group="validation_runs",
                command_id="tschamut_gate_validation",
                description="Run the frozen Tschamut gate validation case.",
                command=READINESS.cargo_validate_command(READINESS.GATE_VALIDATION_CASE),
                expected_inputs=["validation/private/tschamut_public_pilot/gate_v1/tschamut_public_conditional_gate_case.yaml"],
                expected_outputs=[
                    "validation/private/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_manifest.json",
                    "validation/private/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_trajectory.csv",
                    "validation/private/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_deposition.csv",
                ],
                read_only=False,
                may_produce_ignored_outputs=True,
                ignored_output_paths=["validation/private/tschamut_public_pilot/gate_v1"],
            ),
            command_entry(
                site="tschamut_same_scale",
                group="validation_runs",
                command_id="tschamut_target_validation",
                description="Run the frozen Tschamut target validation case.",
                command=READINESS.cargo_validate_command(READINESS.TARGET_VALIDATION_CASE),
                expected_inputs=["validation/private/tschamut_public_pilot/target_gate_v1/tschamut_public_target_gate_case.yaml"],
                expected_outputs=[
                    "validation/private/tschamut_public_pilot/target_gate_v1/validation_tschamut_public_target_gate_v1_manifest.json",
                    "validation/private/tschamut_public_pilot/target_gate_v1/validation_tschamut_public_target_gate_v1_trajectory.csv",
                    "validation/private/tschamut_public_pilot/target_gate_v1/validation_tschamut_public_target_gate_v1_deposition.csv",
                ],
                read_only=False,
                may_produce_ignored_outputs=True,
                ignored_output_paths=["validation/private/tschamut_public_pilot/target_gate_v1"],
            ),
            command_entry(
                site="tschamut_same_scale",
                group="validation_runs",
                command_id="tschamut_target_summary_only_validation",
                description="Run the reduced-output summary-only Tschamut target validation case.",
                command=READINESS.cargo_validate_command(READINESS.TARGET_SUMMARY_ONLY_CASE),
                expected_inputs=[
                    "validation/private/tschamut_public_pilot/target_gate_v1_summary_only/tschamut_public_target_gate_summary_only_case.yaml"
                ],
                expected_outputs=[
                    "validation/private/tschamut_public_pilot/target_gate_v1_summary_only/validation_tschamut_public_target_gate_v1_summary_only_manifest.json",
                ],
                read_only=False,
                may_produce_ignored_outputs=True,
                ignored_output_paths=["validation/private/tschamut_public_pilot/target_gate_v1_summary_only"],
                extra_fields={
                    "validation_output_inventory": validation_output_inventory(mode="summary_only"),
                },
            ),
            command_entry(
                site="tschamut_same_scale",
                group="hazard_builds",
                command_id="tschamut_gate_hazard_build",
                description="Build gate-side conditional hazard layers and manifests from the frozen gate validation case.",
                command=READINESS.hazard_command(
                    case_path=READINESS.GATE_VALIDATION_CASE,
                    output_dir=READINESS.GATE_HAZARD_ROOT,
                    map_product_id=READINESS.GATE_MAP_PRODUCT_ID,
                    diagnostics_path=READINESS.GATE_VALIDATION_ROOT / "validation_tschamut_public_conditional_gate_v1_metrics.json",
                    trajectory_path=READINESS.GATE_VALIDATION_ROOT / "validation_tschamut_public_conditional_gate_v1_trajectory.csv",
                    trajectories_dir=READINESS.GATE_VALIDATION_ROOT / "validation_tschamut_public_conditional_gate_v1_trajectories",
                    deposition_path=READINESS.GATE_VALIDATION_ROOT / "validation_tschamut_public_conditional_gate_v1_deposition.csv",
                    impact_events_dir=READINESS.GATE_VALIDATION_ROOT / "validation_tschamut_public_conditional_gate_v1_impacts",
                    map_package_manifest=READINESS.GATE_HAZARD_ROOT / "tschamut_public_conditional_gate_v1_map_package_manifest.json",
                    pilot_gis_manifest=READINESS.GATE_HAZARD_ROOT / "tschamut_public_conditional_gate_v1_pilot_gis_package_manifest.json",
                    thresholds=READINESS.GATE_HAZARD_THRESHOLDS,
                ),
                expected_inputs=["validation/private/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_manifest.json"],
                expected_outputs=[
                    "hazard/results/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_manifest.json",
                    "hazard/results/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_conditional_intensity_exceedance_curves.csv",
            ],
            read_only=False,
            may_produce_ignored_outputs=True,
            ignored_output_paths=["hazard/results/tschamut_public_pilot/gate_v1"],
            output_profile_policy=OUTPUT_PROFILE_POLICY.classify_output_profile_policy(
                conditional_curve_export="summary-only",
                grid_csv_export="none",
                no_plots=True,
                label="tschamut_gate_hazard_build",
            ),
        ),
            command_entry(
                site="tschamut_same_scale",
                group="hazard_builds",
                command_id="tschamut_target_hazard_build",
                description="Build target-side conditional hazard layers and manifests from the frozen target validation case.",
                command=READINESS.hazard_command(
                    case_path=READINESS.TARGET_VALIDATION_CASE,
                    output_dir=READINESS.TARGET_HAZARD_ROOT,
                    map_product_id=READINESS.TARGET_MAP_PRODUCT_ID,
                    diagnostics_path=READINESS.TARGET_VALIDATION_ROOT / "validation_tschamut_public_target_gate_v1_metrics.json",
                    trajectory_path=READINESS.TARGET_VALIDATION_ROOT / "validation_tschamut_public_target_gate_v1_trajectory.csv",
                    trajectories_dir=READINESS.TARGET_VALIDATION_ROOT / "validation_tschamut_public_target_gate_v1_trajectories",
                    deposition_path=READINESS.TARGET_VALIDATION_ROOT / "validation_tschamut_public_target_gate_v1_deposition.csv",
                    impact_events_dir=READINESS.TARGET_VALIDATION_ROOT / "validation_tschamut_public_target_gate_v1_impacts",
                    map_package_manifest=READINESS.TARGET_HAZARD_ROOT / "tschamut_public_scalable_conditional_target_gate_v1_map_package_manifest.json",
                    pilot_gis_manifest=READINESS.TARGET_HAZARD_ROOT / "tschamut_public_scalable_conditional_target_gate_v1_pilot_gis_package_manifest.json",
                    thresholds=READINESS.TARGET_HAZARD_THRESHOLDS,
                ),
                expected_inputs=["validation/private/tschamut_public_pilot/target_gate_v1/validation_tschamut_public_target_gate_v1_manifest.json"],
                expected_outputs=[
                    "hazard/results/tschamut_public_pilot/target_gate_v1/validation_tschamut_public_target_gate_v1_manifest.json",
                    "hazard/results/tschamut_public_pilot/target_gate_v1/validation_tschamut_public_target_gate_v1_conditional_intensity_exceedance_curves.csv",
            ],
            read_only=False,
            may_produce_ignored_outputs=True,
            ignored_output_paths=["hazard/results/tschamut_public_pilot/target_gate_v1"],
            output_profile_policy=OUTPUT_PROFILE_POLICY.classify_output_profile_policy(
                conditional_curve_export="summary-only",
                grid_csv_export="none",
                no_plots=True,
                label="tschamut_target_hazard_build",
            ),
        ),
        ]
    )
    commands.extend(
        [
            command_entry(
                site="tschamut_same_scale",
                group="convergence_comparisons",
                command_id="tschamut_convergence_comparison",
                description="Compare the gate and target same-scale hazard manifests cell-wise.",
                command=command_string(
                    [
                        "PYENV_VERSION=system",
                        "uv",
                        "run",
                        "python",
                        rel(ROOT / "scripts" / "compare_hazard_map_convergence.py"),
                        rel(READINESS.GATE_HAZARD_MANIFEST),
                        rel(READINESS.TARGET_HAZARD_MANIFEST),
                        "--format",
                        "json",
                    ]
                ),
                expected_inputs=[
                    "hazard/results/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_manifest.json",
                    "hazard/results/tschamut_public_pilot/target_gate_v1/validation_tschamut_public_target_gate_v1_manifest.json",
                ],
                expected_outputs=["JSON convergence comparison with per-layer metrics"],
                read_only=True,
                may_produce_ignored_outputs=False,
            ),
            command_entry(
                site="tschamut_same_scale",
                group="output_profile_checks",
                command_id="tschamut_output_profile_summary",
                description="Summarize bounded validation-output reduction between full and summary-only target manifests.",
                command=command_string(
                    [
                        "PYENV_VERSION=system",
                        "uv",
                        "run",
                        "python",
                        rel(ROOT / "scripts" / "summarize_bounded_validation_output_profile.py"),
                        "--validation-output-baseline-manifest",
                        rel(READINESS.TARGET_VALIDATION_MANIFEST),
                        "--validation-output-reduced-manifest",
                        rel(READINESS.TARGET_SUMMARY_ONLY_MANIFEST),
                        "--format",
                        "json",
                    ]
                ),
                expected_inputs=[
                    "validation/private/tschamut_public_pilot/target_gate_v1/validation_tschamut_public_target_gate_v1_manifest.json",
                    "validation/private/tschamut_public_pilot/target_gate_v1_summary_only/validation_tschamut_public_target_gate_v1_summary_only_manifest.json",
                ],
                expected_outputs=["JSON bounded validation-output summary with before/after accounting"],
                read_only=True,
                may_produce_ignored_outputs=False,
            ),
            command_entry(
                site="tschamut_same_scale",
                group="context_inspection",
                command_id="tschamut_context_inspection",
                description="Inspect the staged Tschamut public context layers and corridor relevance.",
                command=command_string(
                    [
                        "PYENV_VERSION=system",
                        "uv",
                        "run",
                        "python",
                        rel(ROOT / "scripts" / "inspect_tschamut_public_context_layers.py"),
                        "--format",
                        "json",
                    ]
                ),
                expected_inputs=["data/processed/swisstopo/tschamut_public_pilot/context"],
                expected_outputs=["JSON public-context inspection report"],
                read_only=True,
                may_produce_ignored_outputs=False,
            ),
            command_entry(
                site="tschamut_same_scale",
                group="hazard_context_overlap",
                command_id="tschamut_hazard_context_overlap",
                description="Measure hazard/context proximity on the staged Tschamut hazard envelope.",
                command=command_string(
                    [
                        "PYENV_VERSION=system",
                        "uv",
                        "run",
                        "python",
                        rel(ROOT / "scripts" / "measure_hazard_context_overlap.py"),
                        "--top-cell-count",
                        "1",
                        "--buffer-radii-m",
                        "20",
                        "--hazard-layer",
                        "reach_probability",
                        "--hazard-layer",
                        "max_kinetic_energy",
                        "--hazard-layer",
                        "max_jump_height",
                        "--format",
                        "json",
                    ]
                ),
                expected_inputs=[
                    "hazard/results/tschamut_public_pilot/target_gate_v1/validation_tschamut_public_target_gate_v1_manifest.json",
                    "data/processed/swisstopo/tschamut_public_pilot/context",
                ],
                expected_outputs=["JSON hazard/context overlap report"],
                read_only=True,
                may_produce_ignored_outputs=False,
            ),
            command_entry(
                site="tschamut_same_scale",
                group="uncertainty_summary",
                command_id="tschamut_uncertainty_summary",
                description="Compose convergence, output profile, context, and execution-sufficiency evidence into one summary.",
                command=command_string(
                    [
                        "PYENV_VERSION=system",
                        "uv",
                        "run",
                        "python",
                        rel(ROOT / "scripts" / "summarize_same_scale_uncertainty_envelope.py"),
                        "--format",
                        "json",
                    ]
                ),
                expected_inputs=[
                    "docs/tschamut_public_conditional_pilot_gate_report.md",
                    "docs/tschamut_public_bounded_validation_output_profile.md",
                    "docs/balfrin_single_job_execution_sufficiency.md",
                ],
                expected_outputs=["JSON same-scale uncertainty envelope summary"],
                read_only=True,
                may_produce_ignored_outputs=False,
            ),
        ]
    )

    command_groups = group_summaries(commands, site="tschamut_same_scale", ignored_output_paths=ignored_output_paths)
    output_profile_policies = [
        command["output_profile_policy"]
        for command in commands
        if command.get("output_profile_policy") is not None
    ]
    return {
        "site": "tschamut_same_scale",
        "read_only": all(command["read_only"] for command in commands),
        "command_groups": command_groups,
        "commands": commands,
        "ignored_output_paths": ignored_output_paths,
        "output_profile_policy": OUTPUT_PROFILE_POLICY.summarize_output_profile_policies(
            output_profile_policies, label="tschamut_same_scale_command_plan"
        ),
        "readiness_status": readiness_report["readiness_status"],
        "hazard_rebuild_output_profile_status": output_profile_report["hazard_rebuild_output_profile_status"],
        "rebuildable_reduced_profile_classification": output_profile_report["profile_classifications"].get(
            "target_rebuildable_reduced"
        ),
        "native_rebuildable_reduced_profile_classification": output_profile_report["profile_classifications"].get(
            "native_rebuildable_reduced_output"
        ),
    }


def build_rebuildable_reduced_output_commands() -> list[dict[str, Any]]:
    reduced_root = REDUCED_PROFILE.DEFAULT_OUTPUT_ROOT
    reduced_manifest = REDUCED_PROFILE.DEFAULT_OUTPUT_MANIFEST
    reduced_case = REDUCED_PROFILE.DEFAULT_SOURCE_MANIFEST.parent / "tschamut_public_target_gate_case.yaml"
    scratch_hazard_root = Path("/tmp/tb049_reduced_hazard")
    scratch_map_manifest = scratch_hazard_root / "tschamut_public_scalable_conditional_target_gate_v1_rebuildable_reduced_map_package_manifest.json"
    scratch_pilot_manifest = scratch_hazard_root / "tschamut_public_scalable_conditional_target_gate_v1_rebuildable_reduced_pilot_gis_package_manifest.json"

    native_validation_command = command_string(
        [
            "PYENV_VERSION=system",
            "CARGO_TARGET_DIR=/tmp/rust-rockfall-target",
            "cargo",
            "run",
            "--",
            "validate",
            "--case",
            rel(REDUCED_VALIDATION_CASE),
        ]
    )
    derivation_command = command_string(
        [
            "PYENV_VERSION=system",
            "uv",
            "run",
            "python",
            rel(ROOT / "scripts" / "derive_hazard_rebuild_reduced_profile.py"),
            "--format",
            "json",
        ]
    )
    rebuild_command = command_string(
        [
            "PYENV_VERSION=system",
            "uv",
            "run",
            "python",
            rel(ROOT / "scripts" / "build_hazard_layers.py"),
            "--case",
            rel(reduced_case),
            "--trajectory",
            rel(reduced_root / "validation_tschamut_public_target_gate_v1_trajectory.csv"),
            "--deposition",
            rel(reduced_root / "validation_tschamut_public_target_gate_v1_deposition.csv"),
            "--impact-events",
            rel(reduced_root / "validation_tschamut_public_target_gate_v1_rebuildable_reduced_impact_events.csv"),
            "--diagnostics",
            rel(reduced_root / "validation_tschamut_public_target_gate_v1_metrics.json"),
            "--output-dir",
            rel(scratch_hazard_root),
            "--grid-xmin",
            "2696376.0",
            "--grid-ymin",
            "1167384.0",
            "--grid-ncols",
            "300",
            "--grid-nrows",
            "304",
            "--grid-cell-size",
            "2.0",
            "--map-product-id",
            "tschamut_public_scalable_conditional_target_gate_v1_rebuildable_reduced",
            "--map-package-manifest-json",
            rel(scratch_map_manifest),
            "--export-geotiff",
            "--pilot-gis-package",
            "--pilot-gis-package-manifest-json",
            rel(scratch_pilot_manifest),
            "--pilot-gis-qa-status",
            "not-run",
            "--pilot-gis-qa-note",
            "Reduced rebuildable profile proof; manual GIS/QGIS QA not run.",
            "--trajectory-workers",
            "2",
            "--reducer-workers",
            "2",
            "--no-plots",
            "--conditional-curve-export",
            "summary-only",
            "--grid-csv-export",
            "none",
        ]
    )
    rebuild_policy = OUTPUT_PROFILE_POLICY.classify_output_profile_policy(
        conditional_curve_export="summary-only",
        grid_csv_export="none",
        no_plots=True,
        label="tschamut_reduced_profile_hazard_rebuild",
    )

    return [
        command_entry(
            site="tschamut_same_scale",
            group="rebuildable_reduced_output",
            command_id="tschamut_reduced_profile_validation",
            description="Run the frozen Tschamut target validation case with the native rebuildable_reduced_output mode.",
            command=native_validation_command,
            expected_inputs=[
                rel(REDUCED_VALIDATION_CASE),
            ],
            expected_outputs=[
                rel(reduced_root / "validation_tschamut_public_target_gate_v1_rebuildable_reduced_manifest.json"),
                rel(reduced_root / "validation_tschamut_public_target_gate_v1_rebuildable_reduced_trajectory.csv"),
                rel(reduced_root / "validation_tschamut_public_target_gate_v1_rebuildable_reduced_deposition.csv"),
                rel(reduced_root / "validation_tschamut_public_target_gate_v1_rebuildable_reduced_impact_events.csv"),
                rel(reduced_root / "validation_tschamut_public_target_gate_v1_rebuildable_reduced_trajectory_metadata.csv"),
                rel(reduced_root / "validation_tschamut_public_target_gate_v1_rebuildable_reduced_metrics.json"),
            ],
            read_only=False,
            may_produce_ignored_outputs=True,
            ignored_output_paths=[rel(reduced_root)],
            extra_fields={
                "validation_output_inventory": validation_output_inventory(mode="rebuildable_reduced_output"),
            },
        ),
        command_entry(
            site="tschamut_same_scale",
            group="rebuildable_reduced_output",
            command_id="tschamut_next_ensemble_feasibility_probe_template",
            description="Template the smallest additional same-scale probe with the native rebuildable_reduced_output case; execution remains deferred until explicitly authorized.",
            command=native_validation_command,
            expected_inputs=[
                rel(REDUCED_VALIDATION_CASE),
            ],
            expected_outputs=[
                rel(reduced_root / "validation_tschamut_public_target_gate_v1_rebuildable_reduced_manifest.json"),
                rel(reduced_root / "validation_tschamut_public_target_gate_v1_rebuildable_reduced_trajectory.csv"),
                rel(reduced_root / "validation_tschamut_public_target_gate_v1_rebuildable_reduced_deposition.csv"),
                rel(reduced_root / "validation_tschamut_public_target_gate_v1_rebuildable_reduced_impact_events.csv"),
                rel(reduced_root / "validation_tschamut_public_target_gate_v1_rebuildable_reduced_trajectory_metadata.csv"),
                rel(reduced_root / "validation_tschamut_public_target_gate_v1_rebuildable_reduced_metrics.json"),
            ],
            read_only=False,
            may_produce_ignored_outputs=True,
            blocked_reason="execution deferred until explicitly authorized",
            ignored_output_paths=[rel(reduced_root)],
            extra_fields={
                "validation_output_inventory": validation_output_inventory(mode="rebuildable_reduced_output"),
            },
        ),
        command_entry(
            site="tschamut_same_scale",
            group="rebuildable_reduced_output",
            command_id="tschamut_reduced_profile_hazard_rebuild",
            description="Rebuild hazard layers from the canonical reduced-output root into a scratch proof directory only.",
            command=rebuild_command,
            expected_inputs=[
                rel(reduced_case),
                rel(reduced_root / "validation_tschamut_public_target_gate_v1_trajectory.csv"),
                rel(reduced_root / "validation_tschamut_public_target_gate_v1_deposition.csv"),
                rel(reduced_root / "validation_tschamut_public_target_gate_v1_rebuildable_reduced_impact_events.csv"),
                rel(reduced_root / "validation_tschamut_public_target_gate_v1_metrics.json"),
            ],
            expected_outputs=[
                rel(scratch_hazard_root),
                rel(scratch_map_manifest),
                rel(scratch_pilot_manifest),
            ],
            read_only=False,
            may_produce_ignored_outputs=False,
            output_profile_policy=rebuild_policy,
            extra_fields={
                "validation_output_inventory": validation_output_inventory(mode="rebuildable_reduced_output"),
            },
        ),
        command_entry(
            site="tschamut_same_scale",
            group="rebuildable_reduced_output",
            command_id="tschamut_reduced_profile_derivation",
            description="Derive the canonical rebuildable reduced-output root from the full target validation artifacts as a legacy compatibility and proof fallback.",
            command=derivation_command,
            expected_inputs=[
                rel(REDUCED_PROFILE.DEFAULT_SOURCE_ROOT),
                rel(REDUCED_PROFILE.DEFAULT_SOURCE_MANIFEST),
            ],
            expected_outputs=[
                rel(reduced_manifest),
                rel(reduced_root / "validation_tschamut_public_target_gate_v1_trajectory.csv"),
                rel(reduced_root / "validation_tschamut_public_target_gate_v1_deposition.csv"),
                rel(reduced_root / "validation_tschamut_public_target_gate_v1_rebuildable_reduced_trajectory_metadata.csv"),
                rel(reduced_root / "validation_tschamut_public_target_gate_v1_rebuildable_reduced_impact_events.csv"),
                rel(reduced_root / "validation_tschamut_public_target_gate_v1_metrics.json"),
            ],
            read_only=False,
            may_produce_ignored_outputs=True,
            ignored_output_paths=[rel(reduced_root)],
            extra_fields={
                "validation_output_inventory": validation_output_inventory(mode="rebuildable_reduced_output"),
            },
        ),
    ]


def build_balfrin_single_release_zone_plan_commands() -> list[dict[str, Any]]:
    return [
        command_entry(
            site="tschamut_same_scale",
            group="balfrin_single_release_zone_plan",
            command_id="tschamut_terrain_release_zone_candidate_metrics",
            description="Generate deterministic terrain-driven release-zone candidate metrics for the Balfrin/Tschamut AOI without emitting validated release zones.",
            command=command_string(
                [
                    "PYENV_VERSION=system",
                    "uv",
                    "run",
                    "python",
                    rel(ROOT / "scripts" / "plan_terrain_release_zone_candidates.py"),
                    "--format",
                    "json",
                ]
            ),
            expected_inputs=[
                "data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_swissalti3d_crop.asc",
                "data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_swissalti3d_metadata.yaml",
                "data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_source_zone_metadata_v1.yaml",
            ],
            expected_outputs=["JSON terrain candidate metrics report for the Balfrin/Tschamut AOI"],
            read_only=True,
            may_produce_ignored_outputs=False,
        ),
        command_entry(
            site="tschamut_same_scale",
            group="balfrin_single_release_zone_plan",
            command_id="tschamut_balfrin_single_release_zone_case_plan_dry_run",
            description="Generate the large Balfrin single-release-zone dry-run case plan without executing a validation case.",
            command=command_string(
                [
                    "PYENV_VERSION=system",
                    "uv",
                    "run",
                    "python",
                    rel(ROOT / "scripts" / "plan_balfrin_single_release_zone_case_dry_run.py"),
                    "--format",
                    "json",
                ]
            ),
            expected_inputs=[
                "validation/pilot_runs/tschamut_public_balfrin_single_release_zone_pilot_contract_v1.yaml",
                "validation/policies/tschamut_public_source_scenario_policy_v1.yaml",
                "data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_source_zone_metadata_v1.yaml",
                "data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_scenario_table_v1.csv",
                "tests/fixtures/rebuildable_reduced_output/tschamut_public_target_gate_rebuildable_reduced_case.yaml",
            ],
            expected_outputs=["JSON large-case dry-run plan"],
            read_only=True,
            may_produce_ignored_outputs=False,
        ),
        command_entry(
            site="tschamut_same_scale",
            group="balfrin_single_release_zone_plan",
            command_id="tschamut_balfrin_target_area_case_handoff_dry_run",
            description="Materialize the frozen Tschamut target-area Balfrin handoff bundle into an ignored validation/private root.",
            command=command_string(
                [
                    "PYENV_VERSION=system",
                    "uv",
                    "run",
                    "python",
                    rel(ROOT / "scripts" / "generate_balfrin_target_area_demo_handoff.py"),
                    "--output-root",
                    rel(ROOT / "validation/private/tschamut_public_pilot/balfrin_target_area_demo_v1"),
                    "--format",
                    "json",
                ]
            ),
            expected_inputs=[
                "validation/pilot_runs/tschamut_public_balfrin_target_area_demo_v1.yaml",
                "validation/pilot_runs/tschamut_public_balfrin_target_gate_reproduction_v1.yaml",
                "validation/pilot_runs/tschamut_public_scalable_conditional_target_gate_v1.yaml",
                "validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml",
                "validation/policies/tschamut_public_source_scenario_policy_v1.yaml",
                "data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_source_zone_metadata_v1.yaml",
                "data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_scenario_table_v1.csv",
            ],
            expected_outputs=[
                "validation/private/tschamut_public_pilot/balfrin_target_area_demo_v1/tschamut_public_balfrin_target_area_demo_case_skeleton.yaml",
                "validation/private/tschamut_public_pilot/balfrin_target_area_demo_v1/tschamut_public_balfrin_target_area_demo_command_manifest.json",
                "validation/private/tschamut_public_pilot/balfrin_target_area_demo_v1/tschamut_public_balfrin_target_area_demo_expected_output_roots.yaml",
                "validation/private/tschamut_public_pilot/balfrin_target_area_demo_v1/tschamut_public_balfrin_target_area_demo_scenario_generation_handoff.json",
                "validation/private/tschamut_public_pilot/balfrin_target_area_demo_v1/tschamut_public_balfrin_target_area_demo_gis_scope_summary.yaml",
                "validation/private/tschamut_public_pilot/balfrin_target_area_demo_v1/tschamut_public_balfrin_target_area_demo_bundle_report.json",
            ],
            read_only=False,
            may_produce_ignored_outputs=True,
        ),
    ]


def build_gis_cog_package_conversion_commands() -> list[dict[str, Any]]:
    converted_root = Path("hazard/results/tschamut_public_pilot/gate_v1_cog_export")
    staging_root = Path("/tmp/tb056_cog_export_staging")
    source_manifest_path = (
        ROOT
        / "hazard/results/tschamut_public_pilot/gate_v1/tschamut_public_conditional_gate_v1_map_package_manifest.json"
    )
    if source_manifest_path.exists():
        source_manifest = json.loads(source_manifest_path.read_text(encoding="utf-8"))
        source_manifest_status = "available"
    else:
        source_manifest = {}
        source_manifest_status = "missing_generated_artifact"
    source_layer_names = [entry["layer_name"] for entry in source_manifest.get("raster_outputs", [])]
    source_0p5m_jump_height_layers = [
        layer_name
        for layer_name in source_layer_names
        if layer_name in {"jump_height_exceedance_0p5m", "weighted_jump_height_exceedance_0p5m"}
    ]
    coggable_policy = OUTPUT_PROFILE_POLICY.classify_output_profile_policy(
        conditional_curve_export="summary-only",
        grid_csv_export="none",
        no_plots=True,
        label="tschamut_package_cog_export",
    )
    commands = [
        command_entry(
            site="tschamut_same_scale",
            group="gis_cog_package_conversion",
            command_id="tschamut_standard_package_audit",
            description="Audit the committed same-scale GIS packages and report their current COG-blocked status.",
            command=command_string(
                [
                    "PYENV_VERSION=system",
                    "uv",
                    "run",
                    "python",
                    rel(ROOT / "scripts" / "audit_gis_cog_package_readiness.py"),
                    "--format",
                    "json",
                ]
            ),
            expected_inputs=[
                "hazard/results/tschamut_public_pilot/gate_v1",
                "hazard/results/tschamut_public_pilot/target_gate_v1",
                "hazard/results/tschamut_public_pilot/sampling_sensitivity_v1_full",
                "hazard/results/tschamut_public_pilot/sampling_sensitivity_v2_full",
            ],
            expected_outputs=["JSON GIS/COG readiness report for standard same-scale package roots"],
            read_only=True,
            may_produce_ignored_outputs=False,
        ),
        command_entry(
            site="tschamut_same_scale",
            group="gis_cog_package_conversion",
            command_id="tschamut_package_cog_export",
            description="Build the gate package and post-export an ignored COG-ready same-scale package root with the full gate threshold scope.",
            command=command_string(
                [
                    "PYENV_VERSION=system",
                    "uv",
                    "run",
                    "python",
                    rel(ROOT / "scripts" / "build_hazard_layers.py"),
                    "--case",
                    rel(READINESS.GATE_VALIDATION_CASE),
                    "--output-dir",
                    str(staging_root),
                    "--grid-xmin",
                    "2696376.0",
                    "--grid-ymin",
                    "1167384.0",
                    "--grid-ncols",
                    "300",
                    "--grid-nrows",
                    "304",
                    "--grid-cell-size",
                    "2.0",
                    "--map-product-id",
                    READINESS.GATE_MAP_PRODUCT_ID,
                    "--probability-mode",
                    "sampling_weighted_conditional",
                    "--normalization-scope",
                    "conditioned_on_filter",
                    "--source-zone-metadata-path",
                    "data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_source_zone_metadata_v1.yaml",
                    "--scenario-table-path",
                    "data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_scenario_table_v1.csv",
                    "--export-geotiff",
                    "--pilot-gis-package",
                    "--pilot-gis-qa-status",
                    "not-run",
                    "--pilot-gis-qa-note",
                    "Manual GIS/QGIS inspection has not been run for this generated package.",
                    "--map-package-manifest-json",
                    str(staging_root / "tschamut_public_conditional_gate_v1_map_package_manifest.json"),
                    "--pilot-gis-package-manifest-json",
                    str(staging_root / "tschamut_public_conditional_gate_v1_pilot_gis_package_manifest.json"),
                    "--reducer-workers",
                    "2",
                    "--no-plots",
                    "--conditional-curve-export",
                    "summary-only",
                    "--grid-csv-export",
                    "none",
                    "--diagnostics",
                    "validation/private/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_metrics.json",
                    "--trajectory",
                    "validation/private/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_trajectory.csv",
                    "--ensemble-trajectories-dir",
                    "validation/private/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_trajectories",
                    "--deposition",
                    "validation/private/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_deposition.csv",
                    "--ensemble-impact-events-dir",
                    "validation/private/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_impacts",
                    "--kinetic-energy-exceedance-j",
                    "1000.0",
                    "--kinetic-energy-exceedance-j",
                    "10000.0",
                    "--jump-height-exceedance-m",
                    "0.5",
                    "--jump-height-exceedance-m",
                    "1.0",
                    "--jump-height-exceedance-m",
                    "2.0",
                    "--export-cog",
                    "--cog-package-output-root",
                    str(converted_root),
                ]
            ),
            expected_inputs=[
                "validation/private/tschamut_public_pilot/gate_v1/tschamut_public_conditional_gate_case.yaml",
                "data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_source_zone_metadata_v1.yaml",
                "data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_scenario_table_v1.csv",
            ],
            expected_outputs=[
                str(converted_root),
                str(converted_root / "tschamut_public_conditional_gate_v1_map_package_manifest.json"),
                str(converted_root / "tschamut_public_conditional_gate_v1_pilot_gis_package_manifest.json"),
            ],
            cog_scope_intent={
                "status": "full_scope" if source_layer_names else source_manifest_status,
                "reference_layer_count": len(source_layer_names),
                "reference_layer_names": source_layer_names,
                "included_jump_height_layers_m": [0.5, 1.0, 2.0],
                "omitted_layer_names": [],
                "required_0p5m_jump_height_layers": source_0p5m_jump_height_layers,
                "source_manifest_path": source_manifest_path.relative_to(ROOT).as_posix(),
            },
            read_only=False,
            may_produce_ignored_outputs=True,
            ignored_output_paths=[str(converted_root)],
            output_profile_policy=coggable_policy,
        ),
        command_entry(
            site="tschamut_same_scale",
            group="gis_cog_package_conversion",
            command_id="tschamut_converted_package_audit",
            description="Audit the ignored converted same-scale package and verify its COG-ready metadata.",
            command=command_string(
                [
                    "PYENV_VERSION=system",
                    "uv",
                    "run",
                    "python",
                    rel(ROOT / "scripts" / "audit_gis_cog_package_readiness.py"),
                    "--format",
                    "json",
                    "--converted-package-root",
                    str(converted_root),
                ]
            ),
            expected_inputs=[
                str(converted_root),
                str(converted_root / "tschamut_public_conditional_gate_v1_map_package_manifest.json"),
                str(converted_root / "tschamut_public_conditional_gate_v1_pilot_gis_package_manifest.json"),
            ],
            expected_outputs=["JSON GIS/COG readiness report for the converted ignored package"],
            read_only=True,
            may_produce_ignored_outputs=False,
        ),
    ]
    return commands


def build_second_site_plan(
    second_site_report: dict[str, Any],
    contract_report: dict[str, Any],
    site_config: Path,
) -> dict[str, Any]:
    candidate_site_id = second_site_report["candidate_site_id"]
    candidate_site_name = second_site_report["candidate_site_name"]
    blocked_reason = second_site_report["blocked_reason"]
    ignored_output_paths = [
        f"validation/private/{candidate_site_id}",
        f"hazard/results/{candidate_site_id}",
    ]

    commands = [
        command_entry(
            site="chant_sura_fluelapass",
            group="readiness_checks",
            command_id="second_site_aoi_acquisition_dry_run_planner",
            description="Plan the swisstopo acquisition contract from the candidate AOI before any real staging.",
            command=command_string(
                [
                    "PYENV_VERSION=system",
                    "uv",
                    "run",
                    "python",
                    rel(ROOT / "scripts" / "plan_swisstopo_aoi_acquisition.py"),
                    "--site-config",
                    rel(site_config),
                    "--format",
                    "json",
                ]
            ),
            expected_inputs=[
                "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml",
                "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_public_geodata_acquisition.yaml",
            ],
            expected_outputs=["JSON AOI-to-swisstopo acquisition dry-run plan"],
            read_only=True,
            may_produce_ignored_outputs=False,
        ),
        command_entry(
            site="chant_sura_fluelapass",
            group="readiness_checks",
            command_id="second_site_aoi_to_prepared_pilot_dry_run",
            description="Compose the AOI-to-demonstration preparation scaffold without executing an ensemble.",
            command=command_string(
                [
                    "PYENV_VERSION=system",
                    "uv",
                    "run",
                    "python",
                    rel(ROOT / "scripts" / "run_aoi_hazard_workflow.py"),
                    "prepare",
                    "--site-config",
                    rel(site_config),
                    "--format",
                    "json",
                ]
            ),
            expected_inputs=[
                "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml",
                "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_public_geodata_acquisition.yaml",
            ],
            expected_outputs=["JSON AOI-to-prepared-pilot dry-run preparation report"],
            read_only=True,
            may_produce_ignored_outputs=False,
        ),
        command_entry(
            site="chant_sura_fluelapass",
            group="readiness_checks",
            command_id="second_site_acquisition_manifest_review",
            description="Review the committed Chant Sura / Flüelapass public-geodata acquisition manifest and staging contract.",
            command=command_string(
                [
                    "cat",
                    rel(ROOT / "tests" / "fixtures" / "second_site_public_geodata_preflight" / "chant_sura_fluelapass_public_geodata_acquisition.yaml"),
                ]
            ),
            expected_inputs=[
                "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_public_geodata_acquisition.yaml"
            ],
            expected_outputs=["YAML public-geodata acquisition manifest review"],
            blocked_reason=""
            if (ROOT / "tests" / "fixtures" / "second_site_public_geodata_preflight" / "chant_sura_fluelapass_public_geodata_acquisition.yaml").exists()
            else blocked_reason,
            read_only=True,
            may_produce_ignored_outputs=False,
        ),
        command_entry(
            site="chant_sura_fluelapass",
            group="readiness_checks",
            command_id="second_site_portability_preflight",
            description="Check the staged second-site public-geodata portability requirements.",
            command=command_string(
                [
                    "PYENV_VERSION=system",
                    "uv",
                    "run",
                    "python",
                    rel(ROOT / "scripts" / "check_second_site_public_geodata_preflight.py"),
                    "--site-config",
                    rel(site_config),
                    "--format",
                    "json",
                ]
            ),
            expected_inputs=[
                "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml"
            ],
            expected_outputs=["JSON portability preflight with missing-input inventory"],
            read_only=True,
            may_produce_ignored_outputs=False,
        ),
        command_entry(
            site="chant_sura_fluelapass",
            group="multisite_source_scenario_contract",
            command_id="second_site_contract_audit",
            description=(
                "Audit which Tschamut source-zone and scenario-contract fields are portable versus site-specific "
                "and surface the next local fixture/staging action."
            ),
            command=command_string(
                [
                    "PYENV_VERSION=system",
                    "uv",
                    "run",
                    "python",
                    rel(ROOT / "scripts" / "audit_multisite_source_scenario_contract.py"),
                    "--candidate-site-config",
                    rel(site_config),
                    "--format",
                    "json",
                ]
            ),
            expected_inputs=[
                "validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml",
                "validation/pilot_runs/tschamut_public_scalable_conditional_target_gate_v1.yaml",
                "validation/policies/tschamut_public_source_scenario_policy_v1.yaml",
                "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml",
            ],
            expected_outputs=[
                "JSON portable vs site-specific contract audit with portable and site-specific field names plus next local fixture/staging action"
            ],
            read_only=True,
            may_produce_ignored_outputs=False,
        ),
        command_entry(
            site="chant_sura_fluelapass",
            group="second_site_case_generation",
            command_id="second_site_case_skeleton_dry_run",
            description="Generate a Chant Sura / Fluelapass dry-run case skeleton into /tmp without authorizing ensemble execution.",
            command=command_string(
                [
                    "PYENV_VERSION=system",
                    "uv",
                    "run",
                    "python",
                    rel(ROOT / "scripts" / "generate_chant_sura_fluelapass_dry_run_case_skeleton.py"),
                    "--site-config",
                    rel(site_config),
                    "--output-root",
                    rel(CASE_SKELETON_OUTPUT_ROOT),
                    "--format",
                    "json",
                ]
            ),
            expected_inputs=[
                "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml",
                "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_public_geodata_acquisition.yaml",
            ],
            expected_outputs=[
                rel(CASE_SKELETON_OUTPUT_PATH)
            ],
            read_only=False,
            may_produce_ignored_outputs=False,
        ),
        command_entry(
            site="chant_sura_fluelapass",
            group="second_site_release_plan",
            command_id="second_site_release_plan_dry_run",
            description=(
                "Internal/deprecated direct helper retained for deterministic release-plan dry-run reports; "
                "prefer this portable command plan for user-facing release-plan routing."
            ),
            command=command_string(
                [
                    "PYENV_VERSION=system",
                    "uv",
                    "run",
                    "python",
                    rel(ROOT / "scripts" / "plan_release_plan_dry_run.py"),
                    "--site-config",
                    rel(site_config),
                    "--repo-root",
                    rel(ROOT),
                    "--format",
                    "json",
                ]
            ),
            expected_inputs=[
                "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml",
                "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/terrain.asc",
                "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/terrain_metadata.yaml",
                "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/source_zone_metadata.yaml",
                "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/scenario_table.csv",
                "validation/policies/tschamut_public_source_scenario_policy_v1.yaml",
            ],
            expected_outputs=["JSON deterministic release-plan dry-run report"],
            read_only=True,
            may_produce_ignored_outputs=False,
        ),
        command_entry(
            site="chant_sura_fluelapass",
            group="second_site_release_plan",
            command_id="second_site_release_plan_execution_template",
            description="Template the future second-site release-plan execution path without authorizing it before public context is present.",
            command=command_string(
                [
                    "PYENV_VERSION=system",
                    "uv",
                    "run",
                    "python",
                    "scripts/generate_second_site_release_plan.py",
                    "--site-config",
                    rel(site_config),
                    "--output-root",
                    "validation/private/<site_id>",
                    "--format",
                    "json",
                ]
            ),
            expected_inputs=[
                "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml",
                "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/context",
                "validation/private/chant_sura_fluelapass_portability_example_v1",
                "hazard/results/chant_sura_fluelapass_portability_example_v1",
            ],
            expected_outputs=[
                "validation/private/<site_id>/release_plan_case.yaml",
                "validation/private/<site_id>/release_plan_manifest.json",
            ],
            blocked_reason=blocked_reason,
            read_only=False,
            may_produce_ignored_outputs=True,
            ignored_output_paths=[f"validation/private/{candidate_site_id}"],
        ),
        command_entry(
            site="chant_sura_fluelapass",
            group="second_site_portability",
            command_id="second_site_geodata_manifest_validation",
            description="Validate the staged second-site geodata manifest before any porting step.",
            command=command_string(
                [
                    "PYENV_VERSION=system",
                    "uv",
                    "run",
                    "python",
                    rel(ROOT / "scripts" / "validate_public_real_site_geodata_manifest.py"),
                    f"data/processed/swisstopo/{candidate_site_id}_manifest.yaml",
                ]
            ),
            expected_inputs=[f"data/processed/swisstopo/{candidate_site_id}_manifest.yaml"],
            expected_outputs=["Validated geodata-manifest record"],
            blocked_reason=blocked_reason,
            read_only=True,
            may_produce_ignored_outputs=False,
        ),
        command_entry(
            site="chant_sura_fluelapass",
            group="second_site_portability",
            command_id="second_site_run_freeze_validation",
            description="Validate the second-site pilot run freeze template before any selected-site execution.",
            command=command_string(
                [
                    "PYENV_VERSION=system",
                    "uv",
                    "run",
                    "python",
                    rel(ROOT / "scripts" / "validate_public_real_site_conditional_pilot_run.py"),
                    "validation/templates/public_real_site_conditional_pilot_run_v1.yaml",
                ]
            ),
            expected_inputs=["validation/templates/public_real_site_conditional_pilot_run_v1.yaml"],
            expected_outputs=["Dry-run command-plan validation output"],
            blocked_reason="template_not_run; no second-site freeze is populated yet",
            read_only=True,
            may_produce_ignored_outputs=False,
        ),
        command_entry(
            site="chant_sura_fluelapass",
            group="second_site_portability",
            command_id="second_site_benchmark_preparation_template",
            description="Prepare the site-specific public benchmark inputs for Chant Sura / Flüelapass once public inputs are staged.",
            command=command_string(
                [
                    "PYENV_VERSION=system",
                    "uv",
                    "run",
                    "python",
                    "scripts/prepare_<site_id>_public_benchmark.py",
                    "--output-root",
                    f"data/processed/swisstopo/{candidate_site_id}",
                    "--padding-m",
                    "<buffer>",
                    "--force",
                ]
            ),
            expected_inputs=[
                "terrain crop",
                "terrain metadata",
                "source-zone metadata",
                "scenario table",
                "public context products",
            ],
            expected_outputs=[
                f"data/processed/swisstopo/{candidate_site_id}/input",
                f"data/processed/swisstopo/{candidate_site_id}/context",
            ],
            blocked_reason=blocked_reason,
            read_only=False,
            may_produce_ignored_outputs=True,
            ignored_output_paths=[f"data/processed/swisstopo/{candidate_site_id}"],
        ),
        command_entry(
            site="chant_sura_fluelapass",
            group="second_site_portability",
            command_id="second_site_validation_template",
            description="Run the second-site validation case once the ignored private case exists locally.",
            command=command_string(
                [
                    "PYENV_VERSION=system",
                    "CARGO_TARGET_DIR=/tmp/rust-rockfall-target",
                    "cargo",
                    "run",
                    "--",
                    "validate",
                    "--case",
                    f"validation/private/{candidate_site_id}/<site_case>.yaml",
                ]
            ),
            expected_inputs=[f"validation/private/{candidate_site_id}/<site_case>.yaml"],
            expected_outputs=[f"validation/private/{candidate_site_id}/validation_<site_id>_manifest.json"],
            blocked_reason=blocked_reason,
            read_only=False,
            may_produce_ignored_outputs=True,
            ignored_output_paths=[f"validation/private/{candidate_site_id}"],
        ),
        command_entry(
            site="chant_sura_fluelapass",
            group="second_site_portability",
            command_id="second_site_hazard_build_template",
            description="Build second-site hazard layers once the validation outputs and site-specific grids are staged.",
            command=command_string(
                [
                    "PYENV_VERSION=system",
                    "uv",
                    "run",
                    "python",
                    rel(ROOT / "scripts" / "build_hazard_layers.py"),
                    "--case",
                    f"validation/private/{candidate_site_id}/<site_case>.yaml",
                    "--output-dir",
                    f"hazard/results/{candidate_site_id}",
                    "--grid-xmin",
                    "<grid_xmin>",
                    "--grid-ymin",
                    "<grid_ymin>",
                    "--grid-ncols",
                    "<grid_ncols>",
                    "--grid-nrows",
                    "<grid_nrows>",
                    "--grid-cell-size",
                    "<grid_cell_size_m>",
                    "--map-product-id",
                    "<site_map_product_id>",
                    "--probability-mode",
                    "sampling_weighted_conditional",
                    "--normalization-scope",
                    "conditioned_on_filter",
                    "--source-zone-metadata-path",
                    f"data/processed/swisstopo/{candidate_site_id}/input/source_zone_metadata.yaml",
                    "--scenario-table-path",
                    f"data/processed/swisstopo/{candidate_site_id}/input/scenario_table.csv",
                    "--map-package-manifest-json",
                    f"hazard/results/{candidate_site_id}/<site_case>_map_package_manifest.json",
                    "--export-geotiff",
                    "--pilot-gis-package",
                    "--pilot-gis-package-manifest-json",
                    f"hazard/results/{candidate_site_id}/<site_case>_pilot_gis_package_manifest.json",
                    "--pilot-gis-qa-status",
                    "not-run",
                    "--pilot-gis-qa-note",
                    "Manual GIS/QGIS inspection has not been run for this generated package.",
                    "--reducer-workers",
                    "2",
                    "--no-plots",
                    "--conditional-curve-export",
                    "summary-only",
                    "--grid-csv-export",
                    "none",
                    "--diagnostics",
                    f"validation/private/{candidate_site_id}/<site_case>_metrics.json",
                    "--trajectory",
                    f"validation/private/{candidate_site_id}/<site_case>_trajectory.csv",
                    "--ensemble-trajectories-dir",
                    f"validation/private/{candidate_site_id}/<site_case>_trajectories",
                    "--deposition",
                    f"validation/private/{candidate_site_id}/<site_case>_deposition.csv",
                    "--ensemble-impact-events-dir",
                    f"validation/private/{candidate_site_id}/<site_case>_impacts",
                ]
            ),
            expected_inputs=[
                f"validation/private/{candidate_site_id}/<site_case>.yaml",
                f"data/processed/swisstopo/{candidate_site_id}/input/source_zone_metadata.yaml",
                f"data/processed/swisstopo/{candidate_site_id}/input/scenario_table.csv",
            ],
            expected_outputs=[
                f"hazard/results/{candidate_site_id}/<site_case>_map_package_manifest.json",
                f"hazard/results/{candidate_site_id}/<site_case>_pilot_gis_package_manifest.json",
            ],
            blocked_reason=blocked_reason,
            read_only=False,
            may_produce_ignored_outputs=True,
            ignored_output_paths=[f"hazard/results/{candidate_site_id}"],
            output_profile_policy=OUTPUT_PROFILE_POLICY.classify_output_profile_policy(
                conditional_curve_export="summary-only",
                grid_csv_export="none",
                no_plots=True,
                label="second_site_hazard_build_template",
            ),
        ),
    ]

    command_groups = group_summaries(commands, site="chant_sura_fluelapass", ignored_output_paths=ignored_output_paths)
    output_profile_policies = [
        command["output_profile_policy"]
        for command in commands
        if command.get("output_profile_policy") is not None
    ]
    return {
        "site": "chant_sura_fluelapass",
        "read_only": all(command["read_only"] for command in commands),
        "command_groups": command_groups,
        "commands": commands,
        "ignored_output_paths": ignored_output_paths,
        "portability_status": second_site_report["portability_preflight_status"],
        "public_context_boundary_status": second_site_report["public_context_boundary_status"],
        "deferred_public_context_categories": second_site_report["deferred_public_context_categories"],
        "public_context_product_requirements": second_site_report["public_context_product_requirements"],
        "blocked_second_site_commands": second_site_report["blocked_second_site_commands"],
        "claim_boundaries": second_site_report["claim_boundaries"],
        "blocked_reason": blocked_reason,
        "contract_audit_status": contract_report["source_scenario_contract_audit_status"],
        "portability_semantics_summary": contract_report.get("portability_semantics_summary", {}),
        "output_profile_policy": OUTPUT_PROFILE_POLICY.summarize_output_profile_policies(
            output_profile_policies, label="chant_sura_fluelapass_command_plan"
        ),
    }


def command_entry(
    *,
    site: str,
    group: str,
    command_id: str,
    description: str,
    command: str,
    expected_inputs: list[str],
    expected_outputs: list[str],
    cog_scope_intent: dict[str, Any] | None = None,
    read_only: bool,
    may_produce_ignored_outputs: bool,
    blocked_reason: str = "",
    ignored_output_paths: list[str] | None = None,
    output_profile_policy: dict[str, Any] | None = None,
    extra_fields: dict[str, Any] | None = None,
) -> dict[str, Any]:
    merged_extra_fields: dict[str, Any] = {}
    if extra_fields:
        merged_extra_fields.update(extra_fields)
    if cog_scope_intent is not None:
        merged_extra_fields["cog_scope_intent"] = cog_scope_intent
    return COMMAND_PLAN.build_command_record(
        site=site,
        group=group,
        command_id=command_id,
        description=description,
        command=command,
        expected_inputs=expected_inputs,
        expected_outputs=expected_outputs,
        read_only=read_only,
        may_produce_ignored_outputs=may_produce_ignored_outputs,
        blocked_reason=blocked_reason,
        ignored_output_paths=ignored_output_paths,
        output_profile_policy=output_profile_policy,
        extra_fields=merged_extra_fields,
        include_none_extra_fields=tuple(
            field_name for field_name, value in (("cog_scope_intent", cog_scope_intent),) if value is None
        ),
    )


def validation_output_inventory(*, mode: str) -> dict[str, Any]:
    if mode == "rebuildable_reduced_output":
        return {
            "validation_output_mode": mode,
            "replay_critical_output_classes": list(VALIDATION_OUTPUT_REPLAY_CRITICAL_CLASSES),
            "debug_output_classes": list(VALIDATION_OUTPUT_DEBUG_CLASSES),
            "notes": [
                "replay-critical families stay committed to the manifest and builder-facing outputs",
                "debug fanout is suppressed in the reduced path",
            ],
        }
    if mode == "summary_only":
        return {
            "validation_output_mode": mode,
            "replay_critical_output_classes": [
                "manifest_json",
                "diagnostics_json",
                "trajectory_metadata_csv",
                "ensemble_deposition_csv",
                "stop_state_summary_csv",
            ],
            "debug_output_classes": [
                "trajectory_csv",
                "impact_events_csv",
                "ensemble_trajectories_dir",
                "ensemble_impact_events_dir",
                "ensemble_impact_events_parquet",
            ],
            "notes": [
                "summary-only output is not replayable without the frozen full or rebuildable-reduced case",
                "use the rebuildable reduced mode when required trajectories must remain available",
            ],
        }
    raise ValueError(f"unsupported validation output inventory mode: {mode}")


def group_summaries(
    commands: list[dict[str, Any]],
    *,
    site: str,
    ignored_output_paths: list[str],
) -> list[dict[str, Any]]:
    return COMMAND_PLAN.summarize_command_groups(
        commands,
        group_order=ordered_group_ids(site),
        group_descriptions=GROUP_DESCRIPTIONS,
        ignored_output_paths=ignored_output_paths,
        site=site,
    )


GROUP_DESCRIPTIONS = {
    "readiness_checks": "Check artifact readiness and portability prerequisites.",
    "case_generation": "Regenerate frozen pilot case YAMLs from committed records.",
    "validation_runs": "Run the frozen validation cases that feed the hazard builder.",
    "hazard_builds": "Build hazard-layer outputs and package manifests.",
    "gis_cog_package_conversion": "Audit and convert same-scale GIS packages to COG-ready ignored outputs.",
    "convergence_comparisons": "Compare gate and target hazard manifests cell-wise.",
    "output_profile_checks": "Summarize bounded validation-output pressure.",
    "rebuildable_reduced_output": "Run the native hazard-rebuild-compatible reduced target profile; keep derivation as fallback only.",
    "context_inspection": "Inspect staged public context layers.",
    "hazard_context_overlap": "Measure hazard/context proximity on the staged envelope.",
    "uncertainty_summary": "Compose the same-scale uncertainty envelope summary.",
    "second_site_case_generation": "Generate a dry-run Chant Sura / Flüelapass case skeleton.",
    "second_site_release_plan": "Dry-run the deterministic release and block-scenario row plan.",
    "second_site_portability": "Template portability steps for Chant Sura / Flüelapass.",
    "multisite_source_scenario_contract": "Audit portable versus site-specific source/scenario fields.",
}


def ordered_group_ids(site: str) -> list[str]:
    if site == "tschamut_same_scale":
        return [
            "readiness_checks",
            "case_generation",
            "validation_runs",
            "hazard_builds",
            "gis_cog_package_conversion",
            "convergence_comparisons",
            "output_profile_checks",
            "rebuildable_reduced_output",
            "context_inspection",
            "hazard_context_overlap",
            "uncertainty_summary",
        ]
    if site == "chant_sura_fluelapass":
        return [
            "readiness_checks",
            "multisite_source_scenario_contract",
            "second_site_case_generation",
            "second_site_release_plan",
            "second_site_portability",
        ]
    return list(GROUP_DESCRIPTIONS)


def readiness_ignored_output_paths() -> list[str]:
    return [
        "validation/private/tschamut_public_pilot/gate_v1",
        "validation/private/tschamut_public_pilot/target_gate_v1",
        "validation/private/tschamut_public_pilot/target_gate_v1_summary_only",
        "hazard/results/tschamut_public_pilot/gate_v1",
        "hazard/results/tschamut_public_pilot/target_gate_v1",
        "hazard/results/tschamut_public_pilot/gate_v1_cog_poc",
        "hazard/results/tschamut_public_pilot/gate_v1_cog_export",
    ]


def command_string(parts: list[str]) -> str:
    return COMMAND_PLAN.command_string(parts)


def rel(path: Path) -> str:
    return COMMAND_PLAN.relative_path(path, root=ROOT)


def render_text_report(report: dict[str, Any]) -> str:
    lines = [
        f"command_plan_status: {report['command_plan_status']}",
        f"tschamut_readiness_status: {report['tschamut_readiness_status']}",
        f"second_site_portability_status: {report['second_site_portability_status']}",
        f"supported_sites_or_modes: {', '.join(report['supported_sites_or_modes'])}",
        f"read_only: {str(report['read_only']).lower()}",
        f"scale_up_authorized: {str(report['scale_up_authorized']).lower()}",
        f"operational_claims_allowed: {str(report['operational_claims_allowed']).lower()}",
        "",
        "default_local_hazard_smoke_recommendation:",
    ]
    recommendation = report.get("default_local_hazard_smoke_recommendation") or {}
    lines.extend(
        [
            f"- status: {recommendation.get('recommendation_status')}",
            f"- profile_id: {recommendation.get('recommended_profile_id')}",
            f"- validation_output_mode: {recommendation.get('recommended_validation_output_mode')}",
        ]
    )
    if recommendation.get("recommended_profile_label"):
        lines.append(f"- profile_label: {recommendation.get('recommended_profile_label')}")
    if recommendation.get("recommended_profile_root"):
        lines.append(f"- profile_root: {recommendation.get('recommended_profile_root')}")
    if recommendation.get("next_command"):
        lines.append(f"- replay_command: {recommendation.get('next_command')}")
    recovery = recommendation.get("full_output_recovery") or {}
    if recovery:
        lines.extend(
            [
                f"- full_output_recovery_status: {recovery.get('recovery_status')}",
                f"- full_output_profile_id: {recovery.get('full_output_profile_id')}",
            ]
        )
        if recovery.get("full_output_case_path"):
            lines.append(f"- full_output_case_path: {recovery.get('full_output_case_path')}")
        if recovery.get("full_output_command"):
            lines.append(f"- full_output_command: {recovery.get('full_output_command')}")
    distributed_contract = report.get("distributed_execution_contract") or {}
    if distributed_contract:
        lines.extend(
            [
                "",
                "distributed_execution_contract:",
                f"- schema_version: {distributed_contract.get('schema_version')}",
                f"- status: {distributed_contract.get('contract_status')}",
                f"- execution_model: {distributed_contract.get('execution_model')}",
                f"- distributed_execution_authorized: {str(distributed_contract.get('distributed_execution_authorized')).lower()}",
                f"- merge_order: {distributed_contract.get('merge_contract', {}).get('merge_order')}",
                f"- chunk_id_policy: {distributed_contract.get('chunk_key_contract', {}).get('chunk_id_policy')}",
                f"- future_task: {distributed_contract.get('smallest_future_distributed_dry_run_task', {}).get('task')}",
            ]
        )
    local_dry_run = report.get("local_distributed_orchestration_dry_run") or {}
    if local_dry_run:
        blockers = local_dry_run.get("remaining_cluster_side_blockers") or []
        lines.extend(
            [
                "",
                "local_distributed_orchestration_dry_run:",
                f"- schema_version: {local_dry_run.get('schema_version')}",
                f"- status: {local_dry_run.get('dry_run_status')}",
                f"- chunk_count: {local_dry_run.get('chunk_count')}",
                f"- simulated_retry_count: {local_dry_run.get('simulated_retry_count')}",
                f"- merge_order: {local_dry_run.get('merge_order')}",
                f"- comparison_match: {str(local_dry_run.get('comparison', {}).get('match')).lower()}",
                f"- first_cluster_side_blocker: {blockers[0] if blockers else 'none'}",
            ]
        )
    lines.extend(["", "command_groups:"])
    for group in report["command_groups"]:
        lines.append(f"- {group['site']}::{group['id']} [{group['status']}]: {group['description']}")
    lines.append("")
    lines.append("blocked_template_commands:")
    if report["blocked_template_commands"]:
        for command_id in report["blocked_template_commands"]:
            lines.append(f"- {command_id}")
    else:
        lines.append("- none")
    summary = report.get("second_site_portability_semantics_summary") or {}
    if summary:
        lines.extend(
            [
                "",
                "second_site_portability_semantics:",
                f"- portable_fields: {', '.join(summary.get('portable_semantic_fields', []))}",
                f"- site_specific_fields: {', '.join(summary.get('site_specific_assumption_fields', []))}",
                f"- decision: {summary.get('portability_decision')}",
                f"- first_site_specific_blocker: {summary.get('first_site_specific_blocker')}",
                f"- next_local_fixture_or_staging_action: {summary.get('next_local_fixture_or_staging_action')}",
            ]
        )
    lines.append("")
    lines.append("ignored_output_paths:")
    for path in report["ignored_output_paths"]:
        lines.append(f"- {path}")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
