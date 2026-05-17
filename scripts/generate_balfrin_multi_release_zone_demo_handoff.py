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
DEFAULT_PACKAGE_JSON = DEFAULT_ARTIFACT_DIR / f"{SCHEMA_VERSION}.json"
DEFAULT_PACKAGE_MD = DEFAULT_ARTIFACT_DIR / f"{SCHEMA_VERSION}.txt"
DEFAULT_COMMAND_PLAN_JSON = DEFAULT_ARTIFACT_DIR / "balfrin_multi_release_zone_command_plan_v1.json"
DEFAULT_SBATCH_PATH = DEFAULT_ARTIFACT_DIR / "balfrin_multi_release_zone_handoff.sbatch"
DEFAULT_SECOND_SITE_CONFIG = ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml"


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
class BalfrinMultiReleaseZoneDemoHandoffError(ValueError):
    """User-facing multi-zone dry-run handoff error."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-dir", type=Path, default=DEFAULT_ARTIFACT_DIR)
    parser.add_argument("--candidate-output-root", type=Path, default=None)
    parser.add_argument("--target-area-output-root", type=Path, default=None)
    parser.add_argument("--format", choices=("json", "text"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    parser.add_argument("--text-output", type=Path, default=None)
    args = parser.parse_args(argv)

    try:
        report = build_report(
            artifact_dir=args.artifact_dir,
            candidate_output_root=args.candidate_output_root,
            target_area_output_root=args.target_area_output_root,
        )
    except BalfrinMultiReleaseZoneDemoHandoffError as exc:
        print(f"balfrin multi-release-zone demo handoff error: {exc}", file=sys.stderr)
        return 2

    materialize_artifacts(report, json_output=args.json_output, text_output=args.text_output)

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
    else:
        print(render_text_report(report))
    return 0 if report["package_status"] != "blocked_missing_inputs" else 2


def build_report(
    *,
    artifact_dir: Path = DEFAULT_ARTIFACT_DIR,
    candidate_output_root: Path | None = None,
    target_area_output_root: Path | None = None,
) -> dict[str, Any]:
    artifact_dir = resolve_output_root(artifact_dir)
    if not is_allowed_output_root(artifact_dir):
        raise BalfrinMultiReleaseZoneDemoHandoffError(
            f"artifact-dir must stay under /tmp or validation/private: {artifact_dir}"
        )

    candidate_output_root = resolve_output_root(candidate_output_root or (artifact_dir / "candidate_outputs"))
    target_area_output_root = resolve_output_root(target_area_output_root or (artifact_dir / "target_area_handoff"))
    if not is_allowed_output_root(candidate_output_root) or not is_allowed_output_root(target_area_output_root):
        raise BalfrinMultiReleaseZoneDemoHandoffError(
            "candidate and target-area output roots must stay under /tmp or validation/private"
        )

    command_plan = build_command_plan(
        artifact_dir=artifact_dir,
        candidate_output_root=candidate_output_root,
        target_area_output_root=target_area_output_root,
    )
    candidate_report = safe_build(
        "candidate_stability",
        lambda: CANDIDATE_STABILITY.build_report(
            output_root=candidate_output_root,
            output_mode="both",
        ),
    )
    candidate_report = normalize_candidate_report(candidate_report)
    target_area_contract = load_yaml(DEFAULT_TARGET_AREA_CONTRACT)
    output_profile_report = safe_build("output_profile", OUTPUT_PROFILE.build_summary)
    reducer_scaling_report = safe_build(
        "reducer_scaling",
        lambda: REDUCER_SCALING.build_report(REDUCER_SCALING.DEFAULT_ARTIFACTS),
    )
    single_job_report = safe_build("single_job", SINGLE_JOB.build_summary)

    package_status = classify_package_status(
        candidate_report=candidate_report,
        output_profile_report=output_profile_report,
        reducer_scaling_report=reducer_scaling_report,
        single_job_report=single_job_report,
    )
    section_provenance_profile = build_section_provenance_profile(
        candidate_report=candidate_report,
        target_area_contract=target_area_contract,
        output_profile_report=output_profile_report,
        reducer_scaling_report=reducer_scaling_report,
        single_job_report=single_job_report,
        command_plan=command_plan,
    )

    follow_up_recommendation = build_follow_up_recommendation(
        candidate_report=candidate_report,
        single_job_report=single_job_report,
        output_profile_report=output_profile_report,
    )

    report = {
        "schema_version": SCHEMA_VERSION,
        "package_status": package_status,
        "package_provenance_status": package_status,
        "submission_classification": "blocked_pending_new_human_authorization",
        "live_execution_requires_new_human_authorization": True,
        "package_summary": {
            "status": package_status,
            "summary": (
                "The multi-release-zone Balfrin dry-run package is ready for review; live execution remains blocked "
                "until new human authorization is granted."
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
        "uncertainty_post_processing": build_uncertainty_post_processing(
            single_job_report=single_job_report,
            target_area_contract=target_area_contract,
            command_plan=command_plan,
        ),
        "follow_up_recommendation": follow_up_recommendation,
        "command_plan": command_plan,
        "claim_boundaries": claim_boundaries(target_area_contract),
        "ignored_output_roots": [
            str(candidate_output_root),
            str(target_area_output_root),
            str(artifact_dir),
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
) -> dict[str, Any]:
    scientific_delta_dir = artifact_dir / "scientific_delta"
    restartability_dir = artifact_dir / DEFAULT_RESTARTABILITY_ARTIFACT_DIR.name
    output_profile_dir = artifact_dir / DEFAULT_OUTPUT_PROFILE_ARTIFACT_DIR.name
    reducer_dir = artifact_dir / DEFAULT_REDUCER_ARTIFACT_DIR.name

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
                "description": "Record output pressure, reducer/chunk pressure, and restartability checkpoints.",
                "status": "ready",
            },
            {
                "id": "uncertainty_post_processing",
                "description": "Compose the uncertainty-aware post-processing and interpretation gate reports.",
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
) -> dict[str, Any]:
    readiness = dict(candidate_report.get("candidate_sweep_summary", {}).get("multi_zone_stress_test_readiness") or {})
    return {
        "status": "deferred_pending_authorization",
        "live_execution_requires_new_human_authorization": True,
        "minimum_measured_multi_zone_run": {
            "release_zone_count": 2,
            "trajectory_count_target": 1000,
            "output_mode": output_profile_report.get("validation_output_mode"),
            "conditional_curve_export": "summary-only",
            "grid_csv_export": "none",
            "export_geotiff": True,
            "pilot_gis_package": True,
            "trajectory_workers": 2,
            "reducer_workers": 2,
        },
        "reason": (
            "The deterministic candidate sweep is ready for multi-zone scenario-generation stress tests, but the "
            "next live step should remain the smallest extra zone count and still require renewed human authorization."
        ),
        "candidate_readiness": readiness,
        "recommended_next_check": "Review the package, then seek a new human authorization before any live multi-zone Balfrin job.",
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
) -> str:
    sections = [
        candidate_report.get("candidate_metrics_status"),
        output_profile_report.get("acceptance_classification"),
        reducer_scaling_report.get("reducer_scaling_status"),
        single_job_report.get("final_classification"),
    ]
    if any(status == "blocked_missing_inputs" for status in sections):
        return "blocked_missing_inputs"
    if any(status in {"defer", "ready", "mixed_provenance", "measured_existing_artifacts"} for status in sections):
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
    lines = [
        "Balfrin Multi-Release-Zone Demo Package",
        "",
        f"- Package status: `{report['package_status']}`",
        f"- Submission classification: `{report['submission_classification']}`",
        f"- Live execution requires new human authorization: `{report['live_execution_requires_new_human_authorization']}`",
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
        f"- Recommended validation output mode: `{report['follow_up_recommendation']['minimum_measured_multi_zone_run']['output_mode']}`",
        f"- Reason: {report['follow_up_recommendation']['reason']}",
        "",
        "## Command Plan",
        "",
        f"- Canonical ancestor: `{report['canonical_command_plan_reference']['source_script']}`",
    ]
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
