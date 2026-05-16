#!/usr/bin/env python3
"""Emit canonical portable pilot command plans without executing them.

The helper consolidates the frozen Tschamut same-scale execution steps and the
metadata-only Chant Sura / Flüelapass portability checks into a stable
machine-readable plan. It is read-only and does not run any of the commands it
reports.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import shlex
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "portable_pilot_command_plan_v1"
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


READINESS = _load_module("pilot_command_plan_same_scale_readiness", "check_same_scale_artifact_readiness.py")
PORTABILITY = _load_module("pilot_command_plan_second_site_portability", "check_second_site_public_geodata_preflight.py")
CASE_GENERATION = _load_module("pilot_command_plan_case_generation", "generate_tschamut_same_scale_cases.py")
CONTRACT = _load_module("pilot_command_plan_contract_audit", "audit_multisite_source_scenario_contract.py")
OUTPUT_PROFILE = _load_module("pilot_command_plan_output_profile", "check_hazard_rebuild_output_profile.py")
REDUCED_PROFILE = _load_module("pilot_command_plan_reduced_profile", "derive_hazard_rebuild_reduced_profile.py")
REDUCED_VALIDATION_CASE = ROOT / "tests/fixtures/rebuildable_reduced_output/tschamut_public_target_gate_rebuildable_reduced_case.yaml"


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
    ignored_output_paths = sorted(
        {
            *readiness_ignored_output_paths(),
            *(path for plan in site_plans.values() for path in plan.get("ignored_output_paths", [])),
        }
    )

    report = {
        "schema_version": SCHEMA_VERSION,
        "command_plan_status": "ready",
        "tschamut_readiness_status": readiness_report["readiness_status"],
        "tschamut_hazard_rebuild_output_profile_status": output_profile_report["hazard_rebuild_output_profile_status"],
        "tschamut_rebuildable_reduced_profile_classification": output_profile_report["profile_classifications"].get(
            "target_rebuildable_reduced"
        ),
        "tschamut_native_rebuildable_reduced_profile_classification": output_profile_report["profile_classifications"].get(
            "native_rebuildable_reduced_output"
        ),
        "second_site_portability_status": second_site_report["portability_preflight_status"],
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
        "command_groups": flattened_groups,
        "commands": flattened_commands,
        "command_ids": [command["id"] for command in flattened_commands],
        "command_descriptions": {command["id"]: command["description"] for command in flattened_commands},
        "blocked_template_commands": blocked_template_commands,
        "ignored_output_paths": ignored_output_paths,
        "command_group_ids": [group["id"] for group in flattened_groups],
        "command_group_keys": [group["group_key"] for group in flattened_groups],
    }
    return report


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
    return {
        "site": "tschamut_same_scale",
        "read_only": all(command["read_only"] for command in commands),
        "command_groups": command_groups,
        "commands": commands,
        "ignored_output_paths": ignored_output_paths,
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
        ),
    ]


def build_gis_cog_package_conversion_commands() -> list[dict[str, Any]]:
    converted_root = Path("hazard/results/tschamut_public_pilot/gate_v1_cog_export")
    staging_root = Path("/tmp/tb056_cog_export_staging")
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
            description="Build the gate package and post-export an ignored COG-ready same-scale package root.",
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
            read_only=False,
            may_produce_ignored_outputs=True,
            ignored_output_paths=[str(converted_root)],
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
            description="Audit which Tschamut source-zone and scenario-contract fields are portable to the candidate site.",
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
            expected_outputs=["JSON portable vs site-specific contract audit"],
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
                    "/tmp/tb062_chant_sura_fluelapass_case_skeleton",
                    "--format",
                    "json",
                ]
            ),
            expected_inputs=[
                "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml",
                "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_public_geodata_acquisition.yaml",
            ],
            expected_outputs=[
                "/tmp/tb062_chant_sura_fluelapass_case_skeleton/chant_sura_fluelapass_dry_run_case_skeleton.yaml"
            ],
            read_only=False,
            may_produce_ignored_outputs=False,
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
                ]
            ),
            expected_inputs=[
                f"validation/private/{candidate_site_id}/<site_case>.yaml",
                f"data/processed/swisstopo/{candidate_site_id}/input/source_zone_metadata.yaml",
                f"data/processed/swisstopo/{candidate_site_id}/input/scenario_table.csv",
            ],
            expected_outputs=[f"hazard/results/{candidate_site_id}/<site_case>_map_package_manifest.json"],
            blocked_reason=blocked_reason,
            read_only=False,
            may_produce_ignored_outputs=True,
            ignored_output_paths=[f"hazard/results/{candidate_site_id}"],
        ),
    ]

    command_groups = group_summaries(commands, site="chant_sura_fluelapass", ignored_output_paths=ignored_output_paths)
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
    read_only: bool,
    may_produce_ignored_outputs: bool,
    blocked_reason: str = "",
    ignored_output_paths: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "site": site,
        "group": group,
        "id": command_id,
        "description": description,
        "command": command,
        "expected_inputs": expected_inputs,
        "expected_outputs": expected_outputs,
        "blocked_reason": blocked_reason,
        "read_only": read_only,
        "may_produce_ignored_outputs": may_produce_ignored_outputs,
        "ignored_output_paths": ignored_output_paths or [],
    }


def group_summaries(
    commands: list[dict[str, Any]],
    *,
    site: str,
    ignored_output_paths: list[str],
) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for group_id in ordered_group_ids(site):
        group_commands = [command for command in commands if command["group"] == group_id]
        if not group_commands:
            continue
        summaries.append(
            {
                "site": site,
                "id": group_id,
                "description": GROUP_DESCRIPTIONS[group_id],
                "command_ids": [command["id"] for command in group_commands],
                "status": "blocked_template" if any(command["blocked_reason"] for command in group_commands) else "ready",
                "read_only": all(command["read_only"] for command in group_commands),
                "may_produce_ignored_outputs": any(command["may_produce_ignored_outputs"] for command in group_commands),
                "ignored_output_paths": ignored_output_paths,
            }
        )
    return summaries


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
    return shlex.join(parts)


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


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
        "command_groups:",
    ]
    for group in report["command_groups"]:
        lines.append(f"- {group['site']}::{group['id']} [{group['status']}]: {group['description']}")
    lines.append("")
    lines.append("blocked_template_commands:")
    if report["blocked_template_commands"]:
        for command_id in report["blocked_template_commands"]:
            lines.append(f"- {command_id}")
    else:
        lines.append("- none")
    lines.append("")
    lines.append("ignored_output_paths:")
    for path in report["ignored_output_paths"]:
        lines.append(f"- {path}")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
