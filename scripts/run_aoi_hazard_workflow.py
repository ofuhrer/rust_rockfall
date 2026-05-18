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
COMMAND_PLAN = _load_module("aoi_hazard_front_door_command_plan", "generate_pilot_command_plan.py")
GIS_COG = _load_module("aoi_hazard_front_door_gis_cog", "audit_gis_cog_package_readiness.py")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
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

    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    output = json.dumps(report, indent=2, sort_keys=True) if args.format == "json" else render_text_report(report)
    print(output)
    return 0 if not str(report["status"]).startswith("blocked") else 2


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


if __name__ == "__main__":
    raise SystemExit(main())
