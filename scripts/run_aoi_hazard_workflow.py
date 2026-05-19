#!/usr/bin/env python3
"""Front door for the AOI-to-hazard-map workflow.

The helper is read-only. It normalizes the existing AOI dry-run, portable
command-plan, and GIS/COG audit helpers into one compact JSON status object
with the next action, first blocker, expected paths, and claim boundaries.
It does not download data, submit Balfrin jobs, or write heavy outputs.
"""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "aoi_hazard_workflow_front_door_v1"
DEFAULT_SITE_CONFIG = ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml"
DEFAULT_ACQUISITION_PACKAGE = ROOT / "docs/chant_sura_fluelapass_public_context_acquisition_package.yaml"
DEFAULT_ARTIFACT_ROOT = ROOT / "hazard/results/tschamut_public_pilot/target_gate_v1"
DEFAULT_COMMAND_PLAN_SITE = "chant_sura_fluelapass"
DEFAULT_LOCAL_SMOKE_CASE = ROOT / "validation/cases/probabilistic_phase1_smoke.yaml"
DEFAULT_LOCAL_SMOKE_OUTPUT_ROOT = Path("/tmp/tb263_local_tiny_aoi_smoke")
SUPPORTED_COMMANDS = ("status", "prepare", "plan", "run-local-smoke", "submit-balfrin", "collect", "package-map")
PREPARE_SCHEMA_VERSION = "aoi_hazard_prepare_front_door_v1"
STATUS_READY = "ready"
STATUS_BLOCKED = "blocked_missing_inputs"
STATUS_INVALID_INPUT = "blocked_invalid_input"
STATUS_INTERNAL_ERROR = "blocked_internal_error"
STATUS_EXIT_CODES = {
    STATUS_READY: 0,
    STATUS_BLOCKED: 2,
    STATUS_INVALID_INPUT: 64,
    STATUS_INTERNAL_ERROR: 70,
}


def _load_module(module_name: str, filename: str):
    path = ROOT / "scripts" / filename
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load helper module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


AOI_WORKFLOW = _load_module("aoi_hazard_front_door_aoi_workflow", "summarize_chant_sura_fluelapass_dry_run_report.py")
PREFLIGHT = _load_module("aoi_hazard_front_door_preflight", "check_second_site_public_geodata_preflight.py")
AOI_ACQUISITION = _load_module("aoi_hazard_front_door_aoi_acquisition", "plan_swisstopo_aoi_acquisition.py")
TERRAIN_PREP = _load_module("aoi_hazard_front_door_terrain_prep", "plan_aoi_terrain_preprocessing.py")
RELEASE_CANDIDATES = _load_module("aoi_hazard_front_door_release_candidates", "plan_terrain_release_zone_candidates.py")
COMMAND_PLAN = _load_module("aoi_hazard_front_door_command_plan", "generate_pilot_command_plan.py")
GIS_COG = _load_module("aoi_hazard_front_door_gis_cog", "audit_gis_cog_package_readiness.py")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "status":
        report = build_status_report(
            command=args.command,
            site_config=args.site_config,
            repo_root=args.repo_root,
            release_polygon=args.release_polygon,
            acquisition_package_path=args.acquisition_package_path,
            artifact_root=args.artifact_root,
            smoke_case_path=args.smoke_case_path,
            smoke_output_root=args.smoke_output_root,
        )
        output = json.dumps(report, indent=2, sort_keys=True) if args.format == "json" else render_status_text_report(report)
    else:
        report = build_report(
            command=args.command,
            site_config=args.site_config,
            repo_root=args.repo_root,
            release_polygon=args.release_polygon,
            acquisition_package_path=args.acquisition_package_path,
            artifact_root=args.artifact_root,
            smoke_case_path=args.smoke_case_path,
            smoke_output_root=args.smoke_output_root,
        )
        output = json.dumps(report, indent=2, sort_keys=True) if args.format == "json" else render_text_report(report)

    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(output)
    return status_exit_code(report) if args.command == "status" else (0 if not str(report["status"]).startswith("blocked") else 2)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", nargs="?", choices=SUPPORTED_COMMANDS, default="status")
    parser.add_argument("--site-config", type=Path, default=DEFAULT_SITE_CONFIG)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--release-polygon", type=Path, default=None)
    parser.add_argument("--acquisition-package-path", type=Path, default=DEFAULT_ACQUISITION_PACKAGE)
    parser.add_argument("--artifact-root", type=Path, default=DEFAULT_ARTIFACT_ROOT)
    parser.add_argument("--smoke-case-path", type=Path, default=DEFAULT_LOCAL_SMOKE_CASE)
    parser.add_argument("--smoke-output-root", type=Path, default=DEFAULT_LOCAL_SMOKE_OUTPUT_ROOT)
    parser.add_argument("--format", choices=("text", "json"), default="json")
    parser.add_argument("--json-output", type=Path, default=None)
    return parser


def build_report(
    *,
    command: str,
    site_config: Path,
    repo_root: Path,
    release_polygon: Path | None = None,
    acquisition_package_path: Path | None = None,
    artifact_root: Path | None = None,
    smoke_case_path: Path | None = None,
    smoke_output_root: Path | None = None,
) -> dict[str, Any]:
    if command == "prepare":
        return build_prepare_report(
            site_config=site_config,
            repo_root=repo_root,
        )
    if command == "run-local-smoke":
        return build_local_smoke_report(
            repo_root=repo_root,
            smoke_case_path=smoke_case_path or DEFAULT_LOCAL_SMOKE_CASE,
            smoke_output_root=smoke_output_root or DEFAULT_LOCAL_SMOKE_OUTPUT_ROOT,
        )

    aoi_report = build_aoi_workflow_report(
        site_config=site_config,
        repo_root=repo_root,
        release_polygon=release_polygon,
        acquisition_package_path=acquisition_package_path,
    )
    command_plan_report = COMMAND_PLAN.build_report(DEFAULT_COMMAND_PLAN_SITE, site_config)
    package_report = build_package_report(artifact_root or DEFAULT_ARTIFACT_ROOT)
    status = resolve_status(command, aoi_report=aoi_report, command_plan_report=command_plan_report, package_report=package_report)

    report = {
        "schema_version": SCHEMA_VERSION,
        "command": command,
        "status": status,
        "next_action": resolve_next_action(command, aoi_report=aoi_report, package_report=package_report),
        "first_blocker": resolve_first_blocker(command, aoi_report=aoi_report, package_report=package_report),
        "expected_paths": resolve_expected_paths(
            command,
            aoi_report=aoi_report,
            command_plan_report=command_plan_report,
            package_report=package_report,
        ),
        "claim_boundaries": resolve_claim_boundaries(command, aoi_report=aoi_report, package_report=package_report),
        "workflow_summary": summarize_workflow(command, aoi_report=aoi_report, command_plan_report=command_plan_report),
        "delegate_statuses": {
            "aoi_workflow": aoi_report.get("workflow_classification", "blocked_missing_inputs"),
            "portable_command_plan": command_plan_report.get("command_plan_status", "blocked_missing_inputs"),
            "gis_cog_audit": package_report.get("gis_cog_readiness_status", "blocked_missing_inputs"),
        },
        "delegate_reports": {
            "aoi_workflow_schema_version": aoi_report.get("schema_version", ""),
            "portable_command_plan_schema_version": command_plan_report.get("schema_version", ""),
            "gis_cog_schema_version": package_report.get("schema_version", ""),
        },
    }
    return report


def build_status_report(
    *,
    command: str,
    site_config: Path,
    repo_root: Path,
    release_polygon: Path | None = None,
    acquisition_package_path: Path | None = None,
    artifact_root: Path | None = None,
    smoke_case_path: Path | None = None,
    smoke_output_root: Path | None = None,
) -> dict[str, Any]:
    try:
        if command not in SUPPORTED_COMMANDS:
            raise FrontDoorStatusInvalidInputError(
                f"unsupported command state: {command}; supported commands: {', '.join(SUPPORTED_COMMANDS)}",
            )
        validate_site_config_for_status(site_config)
        detailed_report = build_report(
            command=command,
            site_config=site_config,
            repo_root=repo_root,
            release_polygon=release_polygon,
            acquisition_package_path=acquisition_package_path,
            artifact_root=artifact_root,
            smoke_case_path=smoke_case_path,
            smoke_output_root=smoke_output_root,
        )
    except FrontDoorStatusInvalidInputError as exc:
        return build_status_failure_report(
            workflow_status=STATUS_INVALID_INPUT,
            command=command,
            site_config=site_config,
            next_action="fix site config and rerun",
            first_blocker={
                "step_id": "command",
                "label": "Unsupported command state",
                "status": STATUS_INVALID_INPUT,
                "blocked_reason": str(exc),
                "expected_inputs": list(SUPPORTED_COMMANDS),
                "expected_outputs": [],
                "next_command": build_status_next_command(
                    "status",
                    site_config=site_config,
                    repo_root=repo_root,
                    release_polygon=release_polygon,
                    acquisition_package_path=acquisition_package_path,
                    artifact_root=artifact_root,
                    smoke_case_path=smoke_case_path,
                    smoke_output_root=smoke_output_root,
                ),
            },
            expected_inputs=list(SUPPORTED_COMMANDS),
            expected_outputs=[],
            claim_boundaries=default_claim_boundaries(),
            candidate_site_id="",
            candidate_site_name="",
        )
    except FrontDoorStatusInvalidSiteConfigError as exc:
        return build_status_failure_report(
            workflow_status=STATUS_INVALID_INPUT,
            command=command,
            site_config=site_config,
            next_action="fix site config and rerun",
            first_blocker={
                "step_id": "site_config",
                "label": "Invalid site config",
                "status": STATUS_INVALID_INPUT,
                "blocked_reason": str(exc),
                "expected_inputs": [str(site_config)],
                "expected_outputs": [],
                "next_command": build_status_next_command(
                    "status",
                    site_config=site_config,
                    repo_root=repo_root,
                    release_polygon=release_polygon,
                    acquisition_package_path=acquisition_package_path,
                    artifact_root=artifact_root,
                    smoke_case_path=smoke_case_path,
                    smoke_output_root=smoke_output_root,
                ),
            },
            expected_inputs=[str(site_config)],
            expected_outputs=[],
            claim_boundaries=default_claim_boundaries(),
            candidate_site_id="",
            candidate_site_name="",
        )
    except Exception as exc:  # pragma: no cover - defensive fail-closed wrapper.
        return build_status_failure_report(
            workflow_status=STATUS_INTERNAL_ERROR,
            command=command,
            site_config=site_config,
            next_action="inspect the error and rerun",
            first_blocker={
                "step_id": "internal_error",
                "label": "Internal error",
                "status": STATUS_INTERNAL_ERROR,
                "blocked_reason": str(exc),
                "expected_inputs": [],
                "expected_outputs": [],
                "next_command": build_status_next_command(
                    "status",
                    site_config=site_config,
                    repo_root=repo_root,
                    release_polygon=release_polygon,
                    acquisition_package_path=acquisition_package_path,
                    artifact_root=artifact_root,
                    smoke_case_path=smoke_case_path,
                    smoke_output_root=smoke_output_root,
                ),
            },
            expected_inputs=[],
            expected_outputs=[],
            claim_boundaries=default_claim_boundaries(),
            candidate_site_id="",
            candidate_site_name="",
        )

    return normalize_status_report(
        command=command,
        site_config=site_config,
        repo_root=repo_root,
        release_polygon=release_polygon,
        acquisition_package_path=acquisition_package_path,
        artifact_root=artifact_root,
        smoke_case_path=smoke_case_path,
        smoke_output_root=smoke_output_root,
        detailed_report=detailed_report,
    )


def build_prepare_report(*, site_config: Path, repo_root: Path) -> dict[str, Any]:
    with patched_preflight_root(repo_root):
        config = PREFLIGHT.load_site_config(site_config) if site_config.exists() else {}
        candidate_site_id = PREFLIGHT.text_value(config.get("candidate_site_id")) or "unspecified_second_site"
        candidate_site_name = PREFLIGHT.text_value(config.get("candidate_site_name")) or "unspecified"
        paths = PREFLIGHT.build_paths(candidate_site_id, config) if config else {}
        acquisition_manifest_path = resolve_acquisition_manifest_path(site_config, config, repo_root)

        bootstrap_report = build_bootstrap_step(site_config=site_config, config=config, candidate_site_id=candidate_site_id)
        acquisition_report = build_acquisition_step(site_config=site_config, repo_root=repo_root)
        cache_report = build_cache_step(repo_root=repo_root, candidate_site_id=candidate_site_id, paths=paths)
        terrain_report = build_terrain_step(repo_root=repo_root, site_config=site_config, paths=paths)
        release_candidate_report = build_release_candidate_step(repo_root=repo_root, paths=paths)
        scenario_freeze_report = build_scenario_freeze_step(
            repo_root=repo_root,
            candidate_site_id=candidate_site_id,
            release_candidate_report=release_candidate_report,
            paths=paths,
        )

    workflow_steps = [
        bootstrap_report,
        acquisition_report,
        cache_report,
        terrain_report,
        release_candidate_report,
        scenario_freeze_report,
    ]
    first_blocker = first_unready_step(workflow_steps)
    if first_blocker is None:
        next_step = release_candidate_report
        status = "ready_for_planning"
    else:
        next_step = first_blocker
        status = str(first_blocker.get("status") or "blocked_missing_inputs")

    expected_paths = {
        "site_config": str(site_config),
        "acquisition_manifest": str(acquisition_manifest_path),
        "cache_manifest": cache_report.get("expected_input_path", ""),
        "terrain_crop": terrain_report.get("expected_input_paths", [""])[0] if terrain_report.get("expected_input_paths") else "",
        "terrain_metadata": terrain_report.get("expected_input_paths", ["", ""])[1] if len(terrain_report.get("expected_input_paths") or []) > 1 else "",
        "source_zone_metadata": release_candidate_report.get("expected_input_paths", ["", "", ""])[2] if len(release_candidate_report.get("expected_input_paths") or []) > 2 else "",
        "scenario_table": scenario_freeze_report.get("expected_input_path", ""),
        "source_scenario_policy": scenario_freeze_report.get("expected_input_paths", [""])[0] if scenario_freeze_report.get("expected_input_paths") else "",
    }

    report = {
        "schema_version": PREPARE_SCHEMA_VERSION,
        "command": "prepare",
        "status": status,
        "next_command": next_step.get("command", ""),
        "next_step": next_step.get("step_id", ""),
        "first_blocker": first_blocker,
        "expected_input_path": first_blocker.get("expected_input_path", "") if first_blocker is not None else release_candidate_report.get("expected_input_path", ""),
        "expected_paths": expected_paths,
        "workflow_steps": workflow_steps,
        "workflow_summary": {
            "step_count": len(workflow_steps),
            "ready_step_count": len([step for step in workflow_steps if step.get("status") == "ready"]),
            "blocked_step_count": len([step for step in workflow_steps if step.get("status") != "ready"]),
            "first_blocked_step": first_blocker.get("step_id", "") if first_blocker is not None else "",
        },
        "claim_boundaries": prepare_claim_boundaries(
            bootstrap_report=bootstrap_report,
            acquisition_report=acquisition_report,
            cache_report=cache_report,
            terrain_report=terrain_report,
            release_candidate_report=release_candidate_report,
            scenario_freeze_report=scenario_freeze_report,
        ),
        "delegate_statuses": {
            "bootstrap": bootstrap_report.get("status", "blocked_missing_inputs"),
            "acquisition_resolution": acquisition_report.get("status", "blocked_missing_inputs"),
            "public_geodata_cache": cache_report.get("status", "blocked_missing_inputs"),
            "terrain_preparation": terrain_report.get("status", "blocked_missing_inputs"),
            "release_candidate_planning": release_candidate_report.get("status", "blocked_missing_inputs"),
            "scenario_freeze_readiness": scenario_freeze_report.get("status", "blocked_missing_inputs"),
        },
        "delegate_reports": {
            "bootstrap_schema_version": bootstrap_report.get("schema_version", ""),
            "acquisition_schema_version": acquisition_report.get("schema_version", ""),
            "terrain_schema_version": terrain_report.get("schema_version", ""),
            "release_candidate_schema_version": release_candidate_report.get("schema_version", ""),
            "scenario_freeze_schema_version": scenario_freeze_report.get("schema_version", ""),
        },
        "candidate_site_id": candidate_site_id,
        "candidate_site_name": candidate_site_name if candidate_site_name != "unspecified" else "placeholder_second_site",
    }
    return report


def build_local_smoke_report(*, repo_root: Path, smoke_case_path: Path, smoke_output_root: Path) -> dict[str, Any]:
    smoke_result = execute_local_smoke_run(
        repo_root=repo_root,
        smoke_case_path=smoke_case_path,
        smoke_output_root=smoke_output_root,
    )
    try:
        command_plan_report = COMMAND_PLAN.build_report(DEFAULT_COMMAND_PLAN_SITE, DEFAULT_SITE_CONFIG)
    except Exception:  # pragma: no cover - metadata fallback only.
        command_plan_report = {
            "schema_version": "portable_pilot_command_plan_v1",
            "command_plan_status": "ready",
        }
    return {
        "schema_version": SCHEMA_VERSION,
        "command": "run-local-smoke",
        "status": smoke_result["status"],
        "next_action": "collect",
        "first_blocker": {
            "step_id": "run-local-smoke",
            "label": "Local AOI smoke run",
            "status": smoke_result["status"],
            "blocked_reason": "",
            "missing_input_count": 0,
            "missing_inputs": [],
        },
        "expected_paths": smoke_result["expected_paths"],
        "claim_boundaries": smoke_result["claim_boundaries"],
        "workflow_summary": smoke_result["workflow_summary"],
        "delegate_statuses": {
            "aoi_workflow": smoke_result["status"],
            "portable_command_plan": command_plan_report.get("command_plan_status", "ready"),
            "gis_cog_audit": smoke_result["status"],
        },
        "delegate_reports": {
            "aoi_workflow_schema_version": smoke_result["schema_version"],
            "portable_command_plan_schema_version": command_plan_report.get("schema_version", ""),
            "gis_cog_schema_version": smoke_result["schema_version"],
        },
        "smoke_run": smoke_result,
    }


def execute_local_smoke_run(*, repo_root: Path, smoke_case_path: Path, smoke_output_root: Path) -> dict[str, Any]:
    if not smoke_case_path.exists():
        raise FileNotFoundError(f"smoke case does not exist: {smoke_case_path}")

    smoke_output_root = smoke_output_root.resolve()
    if smoke_output_root.exists():
        shutil.rmtree(smoke_output_root)
    smoke_output_root.mkdir(parents=True, exist_ok=True)

    smoke_case = yaml.safe_load(smoke_case_path.read_text(encoding="utf-8"))
    if not isinstance(smoke_case, dict):
        raise ValueError(f"smoke case must be a mapping: {smoke_case_path}")
    smoke_case = rewrite_smoke_case(smoke_case, smoke_output_root)
    smoke_case_copy = smoke_output_root / smoke_case_path.name
    smoke_case_copy.write_text(yaml.safe_dump(smoke_case, sort_keys=False), encoding="utf-8")

    validation_command = [
        "cargo",
        "run",
        "--quiet",
        "--",
        "validate",
        "--case",
        str(smoke_case_copy),
    ]
    validation_proc = subprocess.run(
        validation_command,
        cwd=repo_root,
        env={**os.environ, "CARGO_TARGET_DIR": "/tmp/rust-rockfall-target"},
        capture_output=True,
        text=True,
        check=True,
    )

    hazard_output_root = smoke_output_root / "hazard" / "results" / str(smoke_case.get("case_id") or "smoke_case")
    hazard_command = [
        "uv",
        "run",
        "python",
        "-m",
        "scripts.build_hazard_layers",
        "--case",
        str(smoke_case_copy),
        "--output-dir",
        str(hazard_output_root),
        "--no-plots",
        "--export-geotiff",
        "--pilot-gis-package",
        "--conditional-curve-export",
        "summary-only",
        "--grid-csv-export",
        "none",
        "--reducer-workers",
        "1",
    ]
    hazard_proc = subprocess.run(
        hazard_command,
        cwd=repo_root,
        env={**os.environ, "PYENV_VERSION": "system", "UV_CACHE_DIR": "/tmp/uv-cache"},
        capture_output=True,
        text=True,
        check=True,
    )

    validation_root = smoke_output_root / "validation" / "results"
    validation_manifest = validation_root / "probabilistic_phase1_smoke_manifest.json"
    validation_trajectory = validation_root / "probabilistic_phase1_smoke_trajectory.csv"
    validation_deposition = validation_root / "probabilistic_phase1_smoke_deposition.csv"
    validation_metadata = validation_root / "probabilistic_phase1_smoke_trajectory_metadata.csv"
    hazard_manifest = hazard_output_root / "probabilistic_phase1_smoke_manifest.json"
    map_package_manifest = hazard_output_root / "probabilistic_phase1_smoke_map_package_manifest.json"
    pilot_gis_manifest = hazard_output_root / "probabilistic_phase1_smoke_pilot_gis_package_manifest.json"
    reach_probability_asc = hazard_output_root / "probabilistic_phase1_smoke_reach_probability.asc"
    reach_probability_tif = hazard_output_root / "probabilistic_phase1_smoke_reach_probability.tif"

    hazard_manifest_json = json.loads(hazard_manifest.read_text(encoding="utf-8"))
    map_package_json = json.loads(map_package_manifest.read_text(encoding="utf-8"))
    pilot_gis_json = json.loads(pilot_gis_manifest.read_text(encoding="utf-8"))

    return {
        "schema_version": "aoi_local_tiny_smoke_run_v1",
        "status": "smoke_completed",
        "case_path": str(smoke_case_copy),
        "validation_output_root": str(validation_root),
        "hazard_output_root": str(hazard_output_root),
        "commands": {
            "validation": validation_command,
            "hazard": hazard_command,
        },
        "no_heavy_debug_defaults": {
            "validation_output_mode": smoke_case.get("outputs", {}).get("validation_output_mode"),
            "conditional_curve_export": "summary-only",
            "grid_csv_export": "none",
            "plots_enabled": False,
        },
        "claim_boundaries": {
            "operational_claims_allowed": False,
            "scale_up_authorized": False,
            "annual_frequency_claims_allowed": False,
            "physical_probability_claims_allowed": False,
            "risk_exposure_vulnerability_claims_allowed": False,
        },
        "expected_paths": {
            "validation_manifest": str(validation_manifest),
            "validation_trajectory": str(validation_trajectory),
            "validation_deposition": str(validation_deposition),
            "validation_metadata": str(validation_metadata),
            "hazard_manifest": str(hazard_manifest),
            "map_package_manifest": str(map_package_manifest),
            "pilot_gis_manifest": str(pilot_gis_manifest),
            "required_rasters": [
                str(hazard_output_root / "probabilistic_phase1_smoke_reach_probability.csv"),
                str(hazard_output_root / "probabilistic_phase1_smoke_reach_probability.asc"),
                str(hazard_output_root / "probabilistic_phase1_smoke_reach_probability.tif"),
                str(hazard_output_root / "probabilistic_phase1_smoke_max_kinetic_energy.csv"),
                str(hazard_output_root / "probabilistic_phase1_smoke_max_jump_height.csv"),
                str(hazard_output_root / "probabilistic_phase1_smoke_significant_impact_density.csv"),
            ],
        },
        "artifact_sha256": {
            "validation_trajectory": sha256_text(validation_trajectory),
            "validation_metadata": sha256_text(validation_metadata),
            "validation_deposition": sha256_text(validation_deposition),
            "hazard_reach_probability_asc": sha256_text(reach_probability_asc),
            "hazard_reach_probability_tif": sha256_text(reach_probability_tif),
            "map_package_manifest": sha256_text(map_package_manifest),
            "pilot_gis_manifest": sha256_text(pilot_gis_manifest),
        },
        "validation_stdout": validation_proc.stdout,
        "validation_stderr": validation_proc.stderr,
        "hazard_stdout": hazard_proc.stdout,
        "hazard_stderr": hazard_proc.stderr,
        "hazard_manifest": hazard_manifest_json,
        "map_package_manifest_json": map_package_json,
        "pilot_gis_package_manifest_json": pilot_gis_json,
        "workflow_summary": {
            "command_focus": "run-local-smoke",
            "workflow_classification": "smoke_completed",
            "prepared_pilot_input_classification": "fixture_backed",
            "first_missing_real_input_category": "",
            "first_missing_real_input_classification": "",
            "workflow_step_count": 2,
            "first_non_ready_step": "",
            "command_plan_status": "ready",
            "ready_for_next_step": {"status": "smoke_completed", "next_step": "none"},
        },
    }


class FrontDoorStatusInvalidInputError(ValueError):
    pass


class FrontDoorStatusInvalidSiteConfigError(ValueError):
    pass


def validate_site_config_for_status(site_config: Path) -> None:
    if not site_config.exists():
        return
    try:
        raw = site_config.read_text(encoding="utf-8")
    except OSError as exc:  # pragma: no cover - filesystem failure.
        raise FrontDoorStatusInvalidSiteConfigError(f"unable to read site config: {site_config}") from exc
    try:
        parsed = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        raise FrontDoorStatusInvalidSiteConfigError(f"invalid YAML site config: {site_config}") from exc
    if parsed is not None and not isinstance(parsed, dict):
        raise FrontDoorStatusInvalidSiteConfigError(f"site config must be a mapping: {site_config}")


def default_claim_boundaries() -> dict[str, Any]:
    return {
        "operational_claims_allowed": False,
        "scale_up_authorized": False,
        "annual_frequency_claims_allowed": False,
        "physical_probability_claims_allowed": False,
        "risk_exposure_vulnerability_claims_allowed": False,
    }


def normalize_status_report(
    *,
    command: str,
    site_config: Path,
    repo_root: Path,
    release_polygon: Path | None,
    acquisition_package_path: Path | None,
    artifact_root: Path | None,
    smoke_case_path: Path | None,
    smoke_output_root: Path | None,
    detailed_report: dict[str, Any],
) -> dict[str, Any]:
    next_action = resolve_next_action(command, aoi_report=detailed_report, package_report=build_package_report(artifact_root or DEFAULT_ARTIFACT_ROOT))
    first_blocker = normalize_first_blocker(
        detailed_report=detailed_report,
        command=command,
        next_action=next_action,
        site_config=site_config,
        repo_root=repo_root,
        release_polygon=release_polygon,
        acquisition_package_path=acquisition_package_path,
        artifact_root=artifact_root,
        smoke_case_path=smoke_case_path,
        smoke_output_root=smoke_output_root,
    )
    expected_inputs = first_blocker.get("expected_inputs", []) if isinstance(first_blocker, dict) else []
    expected_outputs = (
        first_blocker.get("expected_outputs", []) if isinstance(first_blocker, dict) else []
    ) or expected_outputs_for_next_action(
        next_action,
        site_config=site_config,
        repo_root=repo_root,
        release_polygon=release_polygon,
        acquisition_package_path=acquisition_package_path,
        artifact_root=artifact_root,
        smoke_case_path=smoke_case_path,
        smoke_output_root=smoke_output_root,
    )
    claim_boundaries = dict(resolve_claim_boundaries(command, aoi_report=detailed_report, package_report=build_package_report(artifact_root or DEFAULT_ARTIFACT_ROOT)))
    claim_boundaries.setdefault("notes", [
        "read-only front door only",
        "no simulation, no live Balfrin submission, and no claim upgrade",
    ])
    workflow_status = normalize_workflow_status(command, detailed_report)
    return {
        "schema_version": SCHEMA_VERSION,
        "command": command,
        "workflow_status": workflow_status,
        "next_action": next_action,
        "first_blocker": first_blocker,
        "next_command": build_status_next_command(
            next_action,
            site_config=site_config,
            repo_root=repo_root,
            release_polygon=release_polygon,
            acquisition_package_path=acquisition_package_path,
            artifact_root=artifact_root,
            smoke_case_path=smoke_case_path,
            smoke_output_root=smoke_output_root,
        ),
        "expected_inputs": expected_inputs,
        "expected_outputs": expected_outputs,
        "claim_boundaries": claim_boundaries,
        "candidate_site_id": detailed_report.get("candidate_site_id", ""),
        "candidate_site_name": detailed_report.get("candidate_site_name", ""),
    }


def build_status_failure_report(
    *,
    workflow_status: str,
    command: str,
    site_config: Path,
    next_action: str,
    first_blocker: dict[str, Any],
    expected_inputs: list[str],
    expected_outputs: list[str],
    claim_boundaries: dict[str, Any],
    candidate_site_id: str,
    candidate_site_name: str,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "command": command,
        "workflow_status": workflow_status,
        "next_action": next_action,
        "first_blocker": first_blocker,
        "next_command": first_blocker.get("next_command", ""),
        "expected_inputs": expected_inputs,
        "expected_outputs": expected_outputs,
        "claim_boundaries": claim_boundaries,
        "candidate_site_id": candidate_site_id,
        "candidate_site_name": candidate_site_name,
        "site_config": str(site_config),
    }


def normalize_workflow_status(command: str, detailed_report: dict[str, Any]) -> str:
    if command not in SUPPORTED_COMMANDS:
        return STATUS_INVALID_INPUT
    status = str(detailed_report.get("status") or detailed_report.get("workflow_classification") or STATUS_BLOCKED)
    if status in {STATUS_READY, "ready_for_next_step"}:
        return STATUS_READY
    if status.startswith("blocked_invalid") or status == "invalid_input":
        return STATUS_INVALID_INPUT
    if status.startswith("blocked"):
        return STATUS_BLOCKED
    return STATUS_BLOCKED


def normalize_first_blocker(
    *,
    detailed_report: dict[str, Any],
    command: str,
    next_action: str,
    site_config: Path,
    repo_root: Path,
    release_polygon: Path | None,
    acquisition_package_path: Path | None,
    artifact_root: Path | None,
    smoke_case_path: Path | None,
    smoke_output_root: Path | None,
) -> dict[str, Any] | None:
    if command == "status" and detailed_report.get("workflow_classification") == "ready_for_next_step":
        return None
    if command == "package-map":
        package_blocker = resolve_first_blocker(command, aoi_report=detailed_report, package_report=build_package_report(artifact_root or DEFAULT_ARTIFACT_ROOT))
        return normalize_blocker_dict(
            package_blocker,
            next_action=next_action,
            next_command=build_status_next_command(
                next_action,
                site_config=site_config,
                repo_root=repo_root,
                release_polygon=release_polygon,
                acquisition_package_path=acquisition_package_path,
                artifact_root=artifact_root,
                smoke_case_path=smoke_case_path,
                smoke_output_root=smoke_output_root,
            ),
        )
    step = first_non_ready_step_report(detailed_report)
    if step is None:
        blocker = resolve_first_blocker(command, aoi_report=detailed_report, package_report=build_package_report(artifact_root or DEFAULT_ARTIFACT_ROOT))
        return normalize_blocker_dict(
            blocker,
            next_action=next_action,
            next_command=build_status_next_command(
                next_action,
                site_config=site_config,
                repo_root=repo_root,
                release_polygon=release_polygon,
                acquisition_package_path=acquisition_package_path,
                artifact_root=artifact_root,
                smoke_case_path=smoke_case_path,
                smoke_output_root=smoke_output_root,
            ),
        )
    blocker = resolve_first_blocker(command, aoi_report=detailed_report, package_report=build_package_report(artifact_root or DEFAULT_ARTIFACT_ROOT))
    expected_outputs = expected_outputs_for_next_action(
        next_action,
        site_config=site_config,
        repo_root=repo_root,
        release_polygon=release_polygon,
        acquisition_package_path=acquisition_package_path,
        artifact_root=artifact_root,
        smoke_case_path=smoke_case_path,
        smoke_output_root=smoke_output_root,
    )
    normalized = normalize_blocker_dict(
        blocker,
        next_action=next_action,
        next_command=build_status_next_command(
            next_action,
            site_config=site_config,
            repo_root=repo_root,
            release_polygon=release_polygon,
            acquisition_package_path=acquisition_package_path,
            artifact_root=artifact_root,
            smoke_case_path=smoke_case_path,
            smoke_output_root=smoke_output_root,
        ),
    )
    normalized["expected_outputs"] = expected_outputs
    if not normalized.get("expected_inputs"):
        normalized["expected_inputs"] = list(step.get("expected_inputs", []))
    return normalized


def normalize_blocker_dict(blocker: dict[str, Any], *, next_action: str, next_command: str) -> dict[str, Any]:
    missing_inputs = blocker.get("missing_inputs", [])
    expected_inputs = [str(item) for item in missing_inputs if str(item)]
    return {
        "step_id": blocker.get("step_id", ""),
        "label": blocker.get("label", blocker.get("step_id", "")),
        "status": normalize_status_label(str(blocker.get("status") or STATUS_BLOCKED)),
        "blocked_reason": blocker.get("blocked_reason", ""),
        "expected_inputs": expected_inputs,
        "expected_outputs": [],
        "next_action": next_action,
        "next_command": next_command,
    }


def normalize_status_label(status: str) -> str:
    if status in {STATUS_READY, "ready_for_next_step", "ready"}:
        return STATUS_READY
    if status in {STATUS_INVALID_INPUT, "invalid_input"} or status.startswith("blocked_invalid"):
        return STATUS_INVALID_INPUT
    if status.startswith("blocked"):
        return STATUS_BLOCKED
    return status


def build_status_next_command(
    next_action: str,
    *,
    site_config: Path,
    repo_root: Path,
    release_polygon: Path | None,
    acquisition_package_path: Path | None,
    artifact_root: Path | None,
    smoke_case_path: Path | None,
    smoke_output_root: Path | None,
) -> str:
    base = [
        "PYENV_VERSION=system",
        "uv",
        "run",
        "python",
        "scripts/run_aoi_hazard_workflow.py",
        next_action,
        "--site-config",
        shlex.quote(str(site_config)),
        "--repo-root",
        shlex.quote(str(repo_root)),
        "--acquisition-package-path",
        shlex.quote(str(acquisition_package_path or DEFAULT_ACQUISITION_PACKAGE)),
        "--artifact-root",
        shlex.quote(str(artifact_root or DEFAULT_ARTIFACT_ROOT)),
    ]
    if release_polygon is not None:
        base.extend(["--release-polygon", shlex.quote(str(release_polygon))])
    if smoke_case_path is not None:
        base.extend(["--smoke-case-path", shlex.quote(str(smoke_case_path))])
    if smoke_output_root is not None:
        base.extend(["--smoke-output-root", shlex.quote(str(smoke_output_root))])
    base.extend(["--format", "json"])
    return " ".join(base)


def expected_outputs_for_next_action(
    next_action: str,
    *,
    site_config: Path,
    repo_root: Path,
    release_polygon: Path | None,
    acquisition_package_path: Path | None,
    artifact_root: Path | None,
    smoke_case_path: Path | None,
    smoke_output_root: Path | None,
) -> list[str]:
    if next_action == "run-local-smoke":
        smoke_case = smoke_case_path or DEFAULT_LOCAL_SMOKE_CASE
        smoke_root = smoke_output_root or DEFAULT_LOCAL_SMOKE_OUTPUT_ROOT
        return [
            str(smoke_root / "validation" / "results" / "probabilistic_phase1_smoke_manifest.json"),
            str(smoke_root / "hazard" / "results" / "probabilistic_phase1_smoke" / "probabilistic_phase1_smoke_map_package_manifest.json"),
            str(smoke_root / "hazard" / "results" / "probabilistic_phase1_smoke" / "probabilistic_phase1_smoke_pilot_gis_package_manifest.json"),
            str(smoke_case),
        ]
    if next_action in {"prepare", "plan", "package-map", "collect", "submit-balfrin"}:
        try:
            report = build_report(
                command=next_action,
                site_config=site_config,
                repo_root=repo_root,
                release_polygon=release_polygon,
                acquisition_package_path=acquisition_package_path,
                artifact_root=artifact_root,
                smoke_case_path=smoke_case_path,
                smoke_output_root=smoke_output_root,
            )
        except Exception:
            return []
        return flatten_status_paths(report.get("expected_paths", {}))
    return []


def flatten_status_paths(value: Any) -> list[str]:
    items: list[str] = []
    if isinstance(value, str):
        if value:
            items.append(value)
        return items
    if isinstance(value, list):
        for item in value:
            items.extend(flatten_status_paths(item))
        return items
    if isinstance(value, dict):
        for key in ("expected_staged_path", "expected_input_path", "expected_output_path", "path", "artifact_root", "case_skeleton_path"):
            item = value.get(key)
            if isinstance(item, str) and item:
                items.append(item)
        for item in value.values():
            if isinstance(item, (dict, list)):
                items.extend(flatten_status_paths(item))
            elif isinstance(item, str) and item and item not in items:
                items.append(item)
    return dedupe(items)


def dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        if item in seen or not item:
            continue
        seen.add(item)
        ordered.append(item)
    return ordered


def status_exit_code(report: dict[str, Any]) -> int:
    return STATUS_EXIT_CODES.get(str(report.get("workflow_status") or STATUS_BLOCKED), 2)


def render_status_text_report(report: dict[str, Any]) -> str:
    lines = [
        f"schema_version: {report['schema_version']}",
        f"command: {report['command']}",
        f"workflow_status: {report['workflow_status']}",
        f"next_action: {report['next_action']}",
        f"next_command: {report['next_command']}",
        "first_blocker:",
    ]
    blocker = report.get("first_blocker")
    if isinstance(blocker, dict):
        lines.append(f"- step_id: {blocker.get('step_id', '')}")
        lines.append(f"- label: {blocker.get('label', '')}")
        lines.append(f"- status: {blocker.get('status', '')}")
        lines.append(f"- blocked_reason: {blocker.get('blocked_reason', '')}")
    else:
        lines.append("- none")
    lines.append("expected_inputs:")
    lines.extend(f"- {item}" for item in report.get("expected_inputs", []) or [])
    if not report.get("expected_inputs"):
        lines.append("- none")
    lines.append("expected_outputs:")
    lines.extend(f"- {item}" for item in report.get("expected_outputs", []) or [])
    if not report.get("expected_outputs"):
        lines.append("- none")
    lines.append("claim_boundaries:")
    for key, value in sorted(report.get("claim_boundaries", {}).items()):
        if key == "notes" and isinstance(value, list):
            lines.append(f"- {key}:")
            lines.extend(f"  - {item}" for item in value)
        else:
            lines.append(f"- {key}: {value}")
    return "\n".join(lines)


def rewrite_smoke_case(case: dict[str, Any], smoke_output_root: Path) -> dict[str, Any]:
    smoke_case = copy.deepcopy(case)
    outputs = smoke_case.setdefault("outputs", {})
    if not isinstance(outputs, dict):
        raise ValueError("smoke case outputs must be a mapping")
    validation_root = smoke_output_root / "validation" / "results"
    hazard_root = smoke_output_root / "hazard" / "results" / str(smoke_case.get("case_id") or "smoke_case")

    outputs["validation_output_mode"] = "rebuildable_reduced_output"
    outputs["diagnostics_json"] = str(validation_root / "probabilistic_phase1_smoke_metrics.json")
    outputs["manifest_json"] = str(validation_root / "probabilistic_phase1_smoke_manifest.json")
    outputs["trajectory_csv"] = str(validation_root / "probabilistic_phase1_smoke_trajectory.csv")
    outputs["trajectory_metadata_csv"] = str(validation_root / "probabilistic_phase1_smoke_trajectory_metadata.csv")
    outputs["ensemble_trajectories_dir"] = str(validation_root / "probabilistic_phase1_smoke_trajectories")
    outputs["ensemble_deposition_csv"] = str(validation_root / "probabilistic_phase1_smoke_deposition.csv")

    release_zone = smoke_case.setdefault("release_zone", {})
    if isinstance(release_zone, dict):
        release_zone["generated_release_points_csv"] = str(
            validation_root / "probabilistic_phase1_smoke_release_points.csv"
        )

    probabilistic_metadata = smoke_case.setdefault("probabilistic_metadata", {})
    if isinstance(probabilistic_metadata, dict):
        probabilistic_metadata["metadata_path"] = str(
            validation_root / "probabilistic_phase1_smoke_trajectory_metadata.csv"
        )

    hazard_probability = smoke_case.setdefault("hazard_probability", {})
    if isinstance(hazard_probability, dict):
        hazard_probability["metadata_path"] = str(
            validation_root / "probabilistic_phase1_smoke_trajectory_metadata.csv"
        )

    hazard_map_package = smoke_case.setdefault("hazard_map_package", {})
    if isinstance(hazard_map_package, dict):
        hazard_map_package["map_package_manifest_json"] = str(
            hazard_root / "probabilistic_phase1_smoke_map_package_manifest.json"
        )

    return smoke_case


def sha256_text(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_aoi_workflow_report(
    *,
    site_config: Path,
    repo_root: Path,
    release_polygon: Path | None,
    acquisition_package_path: Path | None,
) -> dict[str, Any]:
    try:
        return AOI_WORKFLOW.build_report(
            site_config,
            repo_root=repo_root,
            acquisition_package_path=acquisition_package_path or DEFAULT_ACQUISITION_PACKAGE,
            allow_tiny_ensemble_handoff=False,
            tiny_ensemble_note="read-only front door only",
        )
    except Exception as exc:  # pragma: no cover - defensive fail-closed wrapper.
        return {
            "schema_version": AOI_WORKFLOW.SCHEMA_VERSION,
            "workflow_classification": "blocked_missing_inputs",
            "readiness_status": "blocked_missing_inputs",
            "prepared_pilot_input_classification": "missing",
            "workflow_steps": [],
            "blocked_missing_inputs": [str(exc)],
            "ready_for_next_step": {
                "status": "blocked_missing_inputs",
                "next_step": "none",
                "requires_explicit_permission": False,
                "permission_recorded": False,
                "permission_note": "read-only front door only",
            },
            "claim_boundaries": {
                "operational_claims_allowed": False,
                "scale_up_authorized": False,
                "annual_frequency_claims_allowed": False,
                "physical_probability_claims_allowed": False,
                "risk_exposure_vulnerability_claims_allowed": False,
            },
        }


def build_package_report(artifact_root: Path) -> dict[str, Any]:
    try:
        return GIS_COG.build_gis_cog_readiness_report(artifact_roots=[artifact_root])
    except Exception as exc:  # pragma: no cover - defensive fail-closed wrapper.
        return {
            "schema_version": GIS_COG.SCHEMA_VERSION,
            "gis_cog_readiness_status": "blocked_missing_inputs",
            "artifact_roots": [str(artifact_root)],
            "blocked_missing_inputs": [str(exc)],
            "claim_boundaries": {
                "operational_claims_allowed": False,
                "scale_up_authorized": False,
                "annual_frequency_claims_allowed": False,
                "physical_probability_claims_allowed": False,
                "risk_exposure_vulnerability_claims_allowed": False,
            },
        }


def resolve_status(
    command: str,
    *,
    aoi_report: dict[str, Any],
    command_plan_report: dict[str, Any],
    package_report: dict[str, Any],
) -> str:
    if command == "package-map":
        return str(package_report.get("gis_cog_readiness_status") or "blocked_missing_inputs")
    return str(aoi_report.get("workflow_classification") or "blocked_missing_inputs")


def resolve_next_action(
    command: str,
    *,
    aoi_report: dict[str, Any],
    package_report: dict[str, Any],
) -> str:
    if command == "package-map":
        if str(package_report.get("gis_cog_readiness_status") or "").startswith("blocked"):
            return "package-map"
        return "collect"

    workflow_status = str(aoi_report.get("workflow_classification") or "blocked_missing_inputs")
    first_step = first_non_ready_step(aoi_report)
    if workflow_status == "blocked_missing_inputs" or workflow_status == "blocked_missing_real_core_inputs":
        return "prepare"
    if workflow_status == "blocked_fixture_backed_inputs":
        return "plan"
    if workflow_status == "blocked_partial_real_inputs":
        return "run-local-smoke"
    if workflow_status == "ready_for_next_step":
        return "submit-balfrin"
    if first_step == "public_context_readiness":
        return "prepare"
    if first_step == "aoi_preparation":
        return "prepare"
    if first_step == "release_candidate_generation":
        return "plan"
    if first_step == "scenario_generation":
        return "plan"
    if first_step == "command_planning":
        return "run-local-smoke"
    if first_step == "tiny_bounded_ensemble_handoff":
        return "submit-balfrin"
    return "prepare"


def resolve_first_blocker(
    command: str,
    *,
    aoi_report: dict[str, Any],
    package_report: dict[str, Any],
) -> dict[str, Any]:
    if command == "package-map":
        blocked_inputs = list(package_report.get("blocked_missing_inputs") or [])
        return {
            "step_id": "package-map",
            "status": package_report.get("gis_cog_readiness_status", "blocked_missing_inputs"),
            "blocked_reason": blocked_inputs[0] if blocked_inputs else package_report.get("standard_package_status", {}).get("blocked_reason", ""),
            "missing_input_count": len(blocked_inputs),
            "missing_inputs": blocked_inputs[:6],
        }

    step = first_non_ready_step_report(aoi_report)
    if step is not None:
        missing_inputs = [
            str(item.get("expected_staged_path") or item.get("category") or item)
            if isinstance(item, dict)
            else str(item)
            for item in step.get("expected_inputs", [])
        ]
        return {
            "step_id": step.get("step_id", "unknown"),
            "label": step.get("label", step.get("step_id", "unknown")),
            "status": step.get("status", "blocked_missing_inputs"),
            "blocked_reason": step.get("blocked_reason", ""),
            "missing_input_count": len(missing_inputs),
            "missing_inputs": missing_inputs[:6],
        }

    blocked_inputs = list(aoi_report.get("blocked_missing_inputs") or [])
    return {
        "step_id": "tiny_bounded_ensemble_handoff",
        "status": aoi_report.get("ready_for_next_step", {}).get("status", "blocked_missing_inputs"),
        "blocked_reason": aoi_report.get("ready_for_next_step", {}).get("permission_note", ""),
        "missing_input_count": len(blocked_inputs),
        "missing_inputs": blocked_inputs[:6],
    }


def resolve_expected_paths(
    command: str,
    *,
    aoi_report: dict[str, Any],
    command_plan_report: dict[str, Any],
    package_report: dict[str, Any],
) -> dict[str, Any]:
    if command == "package-map":
        return {
            "artifact_root": package_report.get("artifact_roots", []),
            "source_paths": {
                "artifact_root": package_report.get("source_paths", {}).get("artifact_root", ""),
                "converted_package_root": package_report.get("source_paths", {}).get("converted_package_root", ""),
                "standard_package_manifest": package_report.get("source_paths", {}).get("standard_package_manifest", ""),
                "pilot_gis_package_manifest": package_report.get("source_paths", {}).get("pilot_gis_package_manifest", ""),
            },
            "missing_inputs": package_report.get("blocked_missing_inputs", []),
        }

    case_skeleton = aoi_report.get("aoi_preparation", {}) if isinstance(aoi_report.get("aoi_preparation"), dict) else {}
    required_inputs = sorted(
        {
            path
            for step in aoi_report.get("workflow_steps", [])
            if isinstance(step, dict)
            for path in step.get("expected_inputs", [])
            if isinstance(path, str) and path
        }
    )
    return {
        "required_inputs": required_inputs,
        "case_skeleton_path": case_skeleton.get("generated_case_path", ""),
        "case_skeleton_paths": case_skeleton.get("generated_case_paths", []),
        "tiny_handoff_path": aoi_report.get("tiny_bounded_ensemble_handoff", {}).get("case_skeleton_path", ""),
        "portable_command_plan_blocked_templates": command_plan_report.get("blocked_template_commands", []),
        "portable_command_plan_ignored_roots": command_plan_report.get("ignored_output_paths", []),
    }


def resolve_claim_boundaries(
    command: str,
    *,
    aoi_report: dict[str, Any],
    package_report: dict[str, Any],
) -> dict[str, Any]:
    claim_boundaries = dict(aoi_report.get("claim_boundaries") or {})
    if command == "package-map":
        claim_boundaries.update(dict(package_report.get("claim_boundaries") or {}))
    claim_boundaries.setdefault("operational_claims_allowed", False)
    claim_boundaries.setdefault("scale_up_authorized", False)
    claim_boundaries.setdefault("annual_frequency_claims_allowed", False)
    claim_boundaries.setdefault("physical_probability_claims_allowed", False)
    claim_boundaries.setdefault("risk_exposure_vulnerability_claims_allowed", False)
    return claim_boundaries


def summarize_workflow(
    command: str,
    *,
    aoi_report: dict[str, Any],
    command_plan_report: dict[str, Any],
) -> dict[str, Any]:
    workflow_steps = list(aoi_report.get("workflow_steps") or [])
    return {
        "command_focus": command,
        "workflow_classification": aoi_report.get("workflow_classification", "blocked_missing_inputs"),
        "prepared_pilot_input_classification": aoi_report.get("prepared_pilot_input_classification", "missing"),
        "first_missing_real_input_category": aoi_report.get("first_missing_real_input_category", ""),
        "first_missing_real_input_classification": aoi_report.get("first_missing_real_input_classification", ""),
        "workflow_step_count": len(workflow_steps),
        "first_non_ready_step": first_non_ready_step(aoi_report),
        "command_plan_status": command_plan_report.get("command_plan_status", "blocked_missing_inputs"),
        "ready_for_next_step": aoi_report.get("ready_for_next_step", {}),
    }


def first_non_ready_step_report(aoi_report: dict[str, Any]) -> dict[str, Any] | None:
    for step in aoi_report.get("workflow_steps", []) or []:
        if not isinstance(step, dict):
            continue
        if str(step.get("status") or "") not in {"ready", "ready_for_next_step"}:
            return step
    return None


def first_non_ready_step(aoi_report: dict[str, Any]) -> str:
    step = first_non_ready_step_report(aoi_report)
    return str(step.get("step_id") or "") if step is not None else ""


def render_text_report(report: dict[str, Any]) -> str:
    if report.get("command") == "prepare":
        return render_prepare_text_report(report)
    lines = [
        f"schema_version: {report['schema_version']}",
        f"command: {report['command']}",
        f"status: {report['status']}",
        f"next_action: {report['next_action']}",
        "first_blocker:",
        f"- step_id: {report['first_blocker'].get('step_id', '')}",
        f"- blocked_reason: {report['first_blocker'].get('blocked_reason', '')}",
        "claim_boundaries:",
    ]
    for key, value in sorted(report["claim_boundaries"].items()):
        lines.append(f"- {key}: {value}")
    lines.append("expected_paths:")
    for key, value in sorted(report["expected_paths"].items()):
        lines.append(f"- {key}: {value}")
    if "smoke_run" in report:
        smoke = report["smoke_run"]
        lines.append("smoke_run:")
        lines.append(f"- status: {smoke.get('status', '')}")
        lines.append(f"- validation_output_root: {smoke.get('validation_output_root', '')}")
        lines.append(f"- hazard_output_root: {smoke.get('hazard_output_root', '')}")
        lines.append(f"- validation_output_mode: {smoke.get('no_heavy_debug_defaults', {}).get('validation_output_mode', '')}")
    return "\n".join(lines)


def build_bootstrap_step(*, site_config: Path, config: dict[str, Any], candidate_site_id: str) -> dict[str, Any]:
    has_bootstrap_inputs = site_config.exists() and bool(candidate_site_id.strip())
    expected_input_path = str(site_config)
    command = (
        f"PYENV_VERSION=system uv run python scripts/bootstrap_aoi_manifest.py --output-root <site-root> "
        f"--site-id {candidate_site_id} --bounds <xmin> <ymin> <xmax> <ymax>"
    )
    return {
        "step_id": "bootstrap_aoi_manifest",
        "label": "AOI bootstrap manifest",
        "status": "ready" if has_bootstrap_inputs else "blocked_missing_inputs",
        "blocked_reason": "" if has_bootstrap_inputs else "missing AOI site config",
        "expected_input_path": expected_input_path,
        "expected_input_paths": [expected_input_path],
        "command": command,
    }


def build_acquisition_step(*, site_config: Path, repo_root: Path) -> dict[str, Any]:
    report = AOI_ACQUISITION.build_report(site_config)
    expected_input_path = str(report.get("acquisition_manifest_path") or "")
    command = f"PYENV_VERSION=system uv run python scripts/plan_swisstopo_aoi_acquisition.py --site-config {site_config} --format json"
    status = str(report.get("planner_status") or "blocked_missing_inputs")
    return {
        "step_id": "product_resolution",
        "label": "AOI product resolution",
        "status": "ready" if status == "ready" else status,
        "blocked_reason": "" if status == "ready" else str(report.get("blocked_reason") or "acquisition planning is not ready"),
        "expected_input_path": expected_input_path,
        "expected_input_paths": [expected_input_path] if expected_input_path else [],
        "command": command,
        "report": report,
    }


def build_cache_step(*, repo_root: Path, candidate_site_id: str, paths: dict[str, Path]) -> dict[str, Any]:
    cache_manifest_path = paths.get("processed_input_root", repo_root / "data/processed/swisstopo" / candidate_site_id / "input") / "public_geodata_cache_manifest.yaml"
    command = f"PYENV_VERSION=system uv run python scripts/verify_public_geodata_cache.py --cache-manifest {cache_manifest_path} --format json"
    if not cache_manifest_path.exists():
        return {
            "step_id": "public_geodata_cache_verification",
            "label": "Public geodata cache verification",
            "status": "blocked_missing_inputs",
            "blocked_reason": "missing public geodata cache manifest",
            "expected_input_path": str(cache_manifest_path),
            "expected_input_paths": [str(cache_manifest_path)],
            "command": command,
        }
    report = PREFLIGHT.verify_public_geodata_cache(cache_manifest_path)
    status = str(report.get("verification_status") or "blocked_missing_inputs")
    return {
        "step_id": "public_geodata_cache_verification",
        "label": "Public geodata cache verification",
        "status": "ready" if status == "verified" else status,
        "blocked_reason": "" if status == "verified" else "public geodata cache verification did not pass",
        "expected_input_path": str(cache_manifest_path),
        "expected_input_paths": [str(cache_manifest_path)],
        "command": command,
        "report": report,
    }


def build_terrain_step(*, repo_root: Path, site_config: Path, paths: dict[str, Path]) -> dict[str, Any]:
    terrain_crop = paths.get("terrain_crop", repo_root / "data/processed/swisstopo" / "unspecified_second_site" / "input" / "terrain.asc")
    terrain_metadata = paths.get("terrain_metadata", repo_root / "data/processed/swisstopo" / "unspecified_second_site" / "input" / "terrain_metadata.yaml")
    aoi_tile_catalog = paths.get("aoi_tile_catalog", repo_root / "data/processed/swisstopo" / "unspecified_second_site" / "input" / "aoi_tile_catalog.yaml")
    command = (
        f"PYENV_VERSION=system uv run python scripts/plan_aoi_terrain_preprocessing.py --repo-root {repo_root} "
        f"--site-config {site_config} --format json"
    )
    report = TERRAIN_PREP.build_report(
        repo_root=repo_root,
        site_config=site_config,
        terrain_crop_path=terrain_crop,
        terrain_metadata_path=terrain_metadata,
        aoi_tile_catalog_path=aoi_tile_catalog,
    )
    status = str(report.get("terrain_preprocessing_status") or "blocked_missing_inputs")
    expected_input_paths = [str(terrain_crop), str(terrain_metadata)]
    if aoi_tile_catalog:
        expected_input_paths.append(str(aoi_tile_catalog))
    return {
        "step_id": "terrain_preparation",
        "label": "Terrain preparation",
        "status": "ready" if status == "ready" else status,
        "blocked_reason": "" if status == "ready" else str(report.get("blocked_reason") or "terrain preparation is not ready"),
        "expected_input_path": str(terrain_crop),
        "expected_input_paths": expected_input_paths,
        "command": command,
        "report": report,
    }


def build_release_candidate_step(*, repo_root: Path, paths: dict[str, Path]) -> dict[str, Any]:
    terrain_crop = paths.get("terrain_crop", repo_root / "data/processed/swisstopo" / "unspecified_second_site" / "input" / "terrain.asc")
    terrain_metadata = paths.get("terrain_metadata", repo_root / "data/processed/swisstopo" / "unspecified_second_site" / "input" / "terrain_metadata.yaml")
    source_zone_metadata = paths.get("source_zone_metadata", repo_root / "data/processed/swisstopo" / "unspecified_second_site" / "input" / "source_zone_metadata.yaml")
    command = (
        f"PYENV_VERSION=system uv run python scripts/plan_terrain_release_zone_candidates.py --repo-root {repo_root} "
        f"--terrain-crop {terrain_crop} --terrain-metadata {terrain_metadata} --source-zone-metadata {source_zone_metadata} --format json"
    )
    report = RELEASE_CANDIDATES.build_report(
        repo_root=repo_root,
        terrain_crop_path=terrain_crop,
        terrain_metadata_path=terrain_metadata,
        source_zone_metadata_path=source_zone_metadata,
    )
    status = str(report.get("candidate_metrics_status") or "blocked_missing_inputs")
    expected_input_paths = [str(terrain_crop), str(terrain_metadata), str(source_zone_metadata)]
    return {
        "step_id": "release_candidate_planning",
        "label": "Release-candidate planning",
        "status": "ready" if status == "ready" else status,
        "blocked_reason": "" if status == "ready" else str(report.get("blocked_reason") or "release-candidate planning is not ready"),
        "expected_input_path": str(source_zone_metadata),
        "expected_input_paths": expected_input_paths,
        "command": command,
        "report": report,
    }


def build_scenario_freeze_step(*, repo_root: Path, candidate_site_id: str, release_candidate_report: dict[str, Any], paths: dict[str, Path]) -> dict[str, Any]:
    source_scenario_policy = paths.get("source_scenario_policy", repo_root / "validation/policies" / f"{candidate_site_id}_source_scenario_policy_v1.yaml")
    scenario_table = paths.get("scenario_table", repo_root / "data/processed/swisstopo" / candidate_site_id / "input" / "scenario_table.csv")
    command = (
        "PYENV_VERSION=system uv run python scripts/generate_candidate_source_zone_scenarios.py "
        f"--mode freeze --review-package <candidate-review-package> --output-root <freeze-output-root> --format json"
    )
    ready = str(release_candidate_report.get("status") or "") == "ready"
    return {
        "step_id": "scenario_freeze_readiness",
        "label": "Scenario-freeze readiness",
        "status": "ready" if ready else "blocked_missing_inputs",
        "blocked_reason": "" if ready else "release-candidate planning is not ready",
        "expected_input_path": str(scenario_table) if scenario_table.exists() else str(source_scenario_policy),
        "expected_input_paths": [str(source_scenario_policy), str(scenario_table)],
        "command": command,
        "report": {
            "schema_version": "aoi_scenario_freeze_readiness_v1",
            "status": "ready" if ready else "blocked_missing_inputs",
            "review_package_required": True,
            "review_package_ready": ready,
        },
    }


def first_unready_step(steps: list[dict[str, Any]]) -> dict[str, Any] | None:
    for step in steps:
        if str(step.get("status") or "") != "ready":
            return step
    return None


def prepare_claim_boundaries(
    *,
    bootstrap_report: dict[str, Any],
    acquisition_report: dict[str, Any],
    cache_report: dict[str, Any],
    terrain_report: dict[str, Any],
    release_candidate_report: dict[str, Any],
    scenario_freeze_report: dict[str, Any],
) -> dict[str, Any]:
    claim_boundaries: dict[str, Any] = {
        "operational_claims_allowed": False,
        "scale_up_authorized": False,
        "annual_frequency_claims_allowed": False,
        "physical_probability_claims_allowed": False,
        "risk_exposure_vulnerability_claims_allowed": False,
    }
    for candidate in (
        bootstrap_report.get("claim_boundaries"),
        acquisition_report.get("claim_boundaries"),
        cache_report.get("report", {}).get("claim_boundaries"),
        terrain_report.get("report", {}).get("claim_boundaries"),
        release_candidate_report.get("report", {}).get("claim_boundaries"),
        scenario_freeze_report.get("report", {}).get("claim_boundaries"),
    ):
        if isinstance(candidate, dict):
            claim_boundaries.update(candidate)
    claim_boundaries.setdefault("notes", [
        "guided prepare mode is read-only and does not authorize simulation or operational claims",
        "no annual-frequency, physical-probability, risk, exposure, or vulnerability claim is authorized here",
    ])
    return claim_boundaries


def patched_preflight_root(repo_root: Path):
    class _PreflightRootContext:
        def __enter__(self) -> None:
            self.original_root = PREFLIGHT.ROOT
            PREFLIGHT.ROOT = repo_root

        def __exit__(self, exc_type, exc, tb) -> None:
            PREFLIGHT.ROOT = self.original_root

    return _PreflightRootContext()


def resolve_acquisition_manifest_path(site_config: Path, config: dict[str, Any], repo_root: Path) -> Path:
    acquisition_manifest = config.get("acquisition_manifest_path")
    if acquisition_manifest:
        return PREFLIGHT.resolve_repo_path(acquisition_manifest, base=repo_root)
    return site_config.parent / "public_geodata_acquisition.yaml"


def render_prepare_text_report(report: dict[str, Any]) -> str:
    lines = [
        f"schema_version: {report['schema_version']}",
        f"command: {report['command']}",
        f"status: {report['status']}",
        f"next_command: {report['next_command']}",
        f"next_step: {report.get('next_step', '')}",
        f"expected_input_path: {report.get('expected_input_path', '')}",
        f"candidate_site_id: {report.get('candidate_site_id', '')}",
        f"candidate_site_name: {report.get('candidate_site_name', '')}",
        "",
        "workflow_steps:",
    ]
    for step in report.get("workflow_steps", []):
        lines.append(f"- {step.get('step_id', '')}: {step.get('status', '')}")
        if step.get("expected_input_path"):
            lines.append(f"  expected_input_path: {step['expected_input_path']}")
        if step.get("blocked_reason"):
            lines.append(f"  blocked_reason: {step['blocked_reason']}")
    lines.extend(["", "first_blocker:"])
    first_blocker = report.get("first_blocker")
    if isinstance(first_blocker, dict):
        lines.append(f"- step_id: {first_blocker.get('step_id', '')}")
        lines.append(f"- status: {first_blocker.get('status', '')}")
        lines.append(f"- expected_input_path: {first_blocker.get('expected_input_path', '')}")
        lines.append(f"- blocked_reason: {first_blocker.get('blocked_reason', '')}")
    else:
        lines.append("- none")
    lines.extend(["", "claim_boundaries:"])
    for key, value in sorted(report.get("claim_boundaries", {}).items()):
        if key == "notes" and isinstance(value, list):
            lines.append(f"- {key}:")
            lines.extend(f"  - {item}" for item in value)
        else:
            lines.append(f"- {key}: {value}")
    lines.extend(["", "expected_paths:"])
    for key, value in sorted(report.get("expected_paths", {}).items()):
        lines.append(f"- {key}: {value}")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
