#!/usr/bin/env python3
"""Front door for the AOI-to-hazard-map workflow.

The helper is read-only. It normalizes the existing AOI dry-run, portable
command-plan, and GIS/COG audit helpers into one compact JSON status object
with the next action, first blocker, expected paths, and claim boundaries.
It does not download data, submit Balfrin jobs, or write heavy outputs.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "aoi_hazard_workflow_front_door_v1"
DEFAULT_SITE_CONFIG = ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml"
DEFAULT_ACQUISITION_PACKAGE = ROOT / "docs/chant_sura_fluelapass_public_context_acquisition_package.yaml"
DEFAULT_ARTIFACT_ROOT = ROOT / "hazard/results/tschamut_public_pilot/target_gate_v1"
DEFAULT_COMMAND_PLAN_SITE = "chant_sura_fluelapass"
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
) -> dict[str, Any]:
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
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
