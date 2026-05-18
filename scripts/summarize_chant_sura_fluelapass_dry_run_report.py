#!/usr/bin/env python3
"""Summarize the Chant Sura / Flüelapass dry-run workflow.

This helper composes the read-only Chant Sura readiness gate, AOI staging
contract, release-candidate generator, scenario-plan generator, command-plan
helper, and dry-run case skeleton into one deterministic report.

It does not download public data, run an ensemble, or treat synthetic
fixtures as public-context evidence. The optional tiny bounded ensemble
handoff stays blocked unless the caller explicitly authorizes it.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "chant_sura_fluelapass_dry_run_report_v1"
DEFAULT_SITE_CONFIG = ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml"
DEFAULT_PERMISSION_NOTE = "no explicit tiny bounded ensemble permission recorded"
DEFAULT_TINY_ENSEMBLE_ROOT = Path("/tmp/tb188_chant_sura_fluelapass_tiny_ensemble_handoff")


def _load_module(module_name: str, filename: str):
    path = ROOT / "scripts" / filename
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load helper module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


READINESS_GATE = _load_module(
    "chant_sura_dry_run_readiness_gate",
    "check_chant_sura_real_context_readiness_gate.py",
)
PREFLIGHT = _load_module(
    "chant_sura_dry_run_preflight",
    "check_second_site_public_geodata_preflight.py",
)
AOI_CANDIDATES = _load_module(
    "chant_sura_dry_run_candidate_generation",
    "plan_terrain_release_zone_candidates.py",
)
SCENARIO_PLAN = _load_module(
    "chant_sura_dry_run_scenario_plan",
    "plan_pragmatic_release_plan.py",
)
COMMAND_PLAN = _load_module(
    "chant_sura_dry_run_command_plan",
    "generate_pilot_command_plan.py",
)
CASE_SKELETON = _load_module(
    "chant_sura_dry_run_case_skeleton",
    "generate_chant_sura_fluelapass_dry_run_case_skeleton.py",
)


@contextmanager
def _patched_repo_root(repo_root: Path) -> Iterator[None]:
    original_root = PREFLIGHT.ROOT
    PREFLIGHT.ROOT = repo_root
    try:
        yield
    finally:
        PREFLIGHT.ROOT = original_root


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site-config", type=Path, default=DEFAULT_SITE_CONFIG)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument(
        "--allow-tiny-ensemble-handoff",
        action="store_true",
        help="record explicit permission for the optional tiny bounded ensemble handoff",
    )
    parser.add_argument(
        "--tiny-ensemble-note",
        type=str,
        default=DEFAULT_PERMISSION_NOTE,
        help="record why the tiny ensemble handoff is permitted or blocked",
    )
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    args = parser.parse_args(argv)

    report = build_report(
        args.site_config,
        repo_root=args.repo_root,
        allow_tiny_ensemble_handoff=args.allow_tiny_ensemble_handoff,
        tiny_ensemble_note=args.tiny_ensemble_note,
    )

    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    output = json.dumps(report, indent=2, sort_keys=True) if args.format == "json" else render_text_report(report)
    print(output)
    return 0 if report["workflow_classification"] == "ready_for_next_step" else 2


def build_report(
    site_config: Path,
    *,
    repo_root: Path | None = None,
    allow_tiny_ensemble_handoff: bool = False,
    tiny_ensemble_note: str = DEFAULT_PERMISSION_NOTE,
) -> dict[str, Any]:
    repo_root = repo_root or ROOT
    if not site_config.exists():
        return blocked_report(
            site_config=site_config,
            repo_root=repo_root,
            blocked_reason=f"missing site config: {site_config}",
            allow_tiny_ensemble_handoff=allow_tiny_ensemble_handoff,
            tiny_ensemble_note=tiny_ensemble_note,
        )

    with _patched_repo_root(repo_root):
        config = PREFLIGHT.load_site_config(site_config)
        candidate_site_id = PREFLIGHT.text_value(config.get("candidate_site_id")) or "unspecified_second_site"
        candidate_site_name = PREFLIGHT.text_value(config.get("candidate_site_name")) or "unspecified"
        preflight_report = PREFLIGHT.build_report(site_config)
        readiness_report = READINESS_GATE.build_report(
            site_config,
            repo_root=repo_root,
        )
        paths = PREFLIGHT.build_paths(candidate_site_id, config)

    candidate_generation_report = build_candidate_generation_report(
        repo_root=repo_root,
        terrain_crop_path=paths["terrain_crop"],
        terrain_metadata_path=paths["terrain_metadata"],
        source_zone_metadata_path=paths["source_zone_metadata"],
    )
    scenario_generation_report = SCENARIO_PLAN.build_report(
        policy_path=paths["source_scenario_policy"],
        scenario_table_path=paths["scenario_table"],
    )
    command_plan_report = COMMAND_PLAN.build_report("chant_sura_fluelapass", site_config)
    case_skeleton_report = build_case_skeleton_report(
        preflight_report=preflight_report,
        paths=paths,
        repo_root=repo_root,
        readiness_report=readiness_report,
    )

    blocked_missing_inputs = collect_blocked_missing_inputs(
        readiness_report=readiness_report,
        preflight_report=preflight_report,
        candidate_generation_report=candidate_generation_report,
        scenario_generation_report=scenario_generation_report,
        command_plan_report=command_plan_report,
        case_skeleton_report=case_skeleton_report,
    )

    workflow_classification = "blocked_missing_inputs" if blocked_missing_inputs else "ready_for_next_step"
    tiny_handoff_status = build_tiny_bounded_ensemble_handoff_status(
        workflow_classification=workflow_classification,
        allow_tiny_ensemble_handoff=allow_tiny_ensemble_handoff,
    )
    tiny_handoff_report = build_tiny_bounded_ensemble_handoff(
        candidate_site_id=candidate_site_id,
        candidate_site_name=candidate_site_name,
        repo_root=repo_root,
        case_skeleton_report=case_skeleton_report,
        command_plan_report=command_plan_report,
        readiness_report=readiness_report,
        tiny_handoff_status=tiny_handoff_status,
        tiny_ensemble_note=tiny_ensemble_note,
    )

    workflow_steps = build_workflow_steps(
        readiness_report=readiness_report,
        case_skeleton_report=case_skeleton_report,
        candidate_generation_report=candidate_generation_report,
        scenario_generation_report=scenario_generation_report,
        command_plan_report=command_plan_report,
        tiny_handoff_report=tiny_handoff_report,
    )

    report = {
        "schema_version": SCHEMA_VERSION,
        "workflow_classification": workflow_classification,
        "readiness_status": workflow_classification,
        "candidate_site_id": candidate_site_id,
        "candidate_site_name": candidate_site_name,
        "site_extent": readiness_report.get("site_extent", preflight_report.get("site_extent_or_placeholder", {})),
        "public_context_readiness": readiness_report,
        "aoi_preparation": case_skeleton_report,
        "release_candidate_generation": candidate_generation_report,
        "scenario_generation": scenario_generation_report,
        "command_planning": command_plan_report,
        "tiny_bounded_ensemble_handoff": tiny_handoff_report,
        "workflow_steps": workflow_steps,
        "blocked_missing_inputs": blocked_missing_inputs,
        "ready_for_next_step": {
            "status": workflow_classification,
            "next_step": "tiny_bounded_ensemble_handoff",
            "requires_explicit_permission": True,
            "permission_recorded": allow_tiny_ensemble_handoff,
            "permission_note": tiny_ensemble_note,
        },
        "claim_boundaries": readiness_report.get("claim_boundaries", {}),
        "scale_up_authorized": False,
        "operational_claims_allowed": False,
    }
    return report


def blocked_report(
    *,
    site_config: Path,
    repo_root: Path,
    blocked_reason: str,
    allow_tiny_ensemble_handoff: bool,
    tiny_ensemble_note: str,
) -> dict[str, Any]:
    candidate_site_id = "unspecified_second_site"
    candidate_site_name = "unspecified"
    if site_config.exists():
        try:
            with _patched_repo_root(repo_root):
                config = PREFLIGHT.load_site_config(site_config)
                candidate_site_id = PREFLIGHT.text_value(config.get("candidate_site_id")) or candidate_site_id
                candidate_site_name = PREFLIGHT.text_value(config.get("candidate_site_name")) or candidate_site_name
        except Exception:  # pragma: no cover - defensive fallback for blocked path only.
            pass
    tiny_handoff_report = build_tiny_bounded_ensemble_handoff(
        candidate_site_id=candidate_site_id,
        candidate_site_name=candidate_site_name,
        repo_root=repo_root,
        case_skeleton_report={
            "case_skeleton_status": "blocked_missing_inputs",
            "blocked_reason": blocked_reason,
            "generated_case_path": "",
        },
        command_plan_report={"command_plan_status": "blocked_missing_inputs", "blocked_template_commands": []},
        readiness_report={"real_context_readiness_gate_status": "blocked_missing_inputs"},
        tiny_handoff_status="blocked_missing_inputs",
        tiny_ensemble_note=tiny_ensemble_note,
    )
    report = {
        "schema_version": SCHEMA_VERSION,
        "workflow_classification": "blocked_missing_inputs",
        "readiness_status": "blocked_missing_inputs",
        "candidate_site_id": candidate_site_id,
        "candidate_site_name": candidate_site_name,
        "site_extent": "placeholder_extent_missing",
        "public_context_readiness": {"real_context_readiness_gate_status": "blocked_missing_inputs"},
        "aoi_preparation": {
            "case_skeleton_status": "blocked_missing_inputs",
            "blocked_reason": blocked_reason,
            "generated_case_path": "",
        },
        "release_candidate_generation": {
            "candidate_metrics_status": "blocked_missing_inputs",
            "candidate_release_zone_set_status": "not_emitted",
            "candidate_release_zone_interpretation": "not_claimed",
            "blocked_missing_inputs": [blocked_reason],
            "blocked_reason": blocked_reason,
        },
        "scenario_generation": {
            "scenario_plan_status": "blocked_missing_inputs",
            "blocked_reason": blocked_reason,
            "missing_inputs": [blocked_reason],
        },
        "command_planning": {
            "command_plan_status": "blocked_missing_inputs",
            "blocked_template_commands": [],
            "blocked_reason": blocked_reason,
            "commands": [],
        },
        "tiny_bounded_ensemble_handoff": tiny_handoff_report,
        "workflow_steps": [
            {
                "step_id": "public_context_readiness",
                "status": "blocked_missing_inputs",
                "blocked_reason": blocked_reason,
            },
            {
                "step_id": "aoi_preparation",
                "status": "blocked_missing_inputs",
                "blocked_reason": blocked_reason,
            },
            {
                "step_id": "release_candidate_generation",
                "status": "blocked_missing_inputs",
                "blocked_reason": blocked_reason,
            },
            {
                "step_id": "scenario_generation",
                "status": "blocked_missing_inputs",
                "blocked_reason": blocked_reason,
            },
            {
                "step_id": "command_planning",
                "status": "blocked_missing_inputs",
                "blocked_reason": blocked_reason,
            },
            {
                "step_id": "tiny_bounded_ensemble_handoff",
                "status": tiny_handoff_report["status"],
                "blocked_reason": tiny_handoff_report["blocked_reason"],
            },
        ],
        "blocked_missing_inputs": [blocked_reason],
        "ready_for_next_step": {
            "status": "blocked_missing_inputs",
            "next_step": "none",
            "requires_explicit_permission": bool(allow_tiny_ensemble_handoff),
            "permission_recorded": allow_tiny_ensemble_handoff,
            "permission_note": tiny_ensemble_note,
        },
        "claim_boundaries": {
            "operational_claims_allowed": False,
            "scale_up_authorized": False,
            "annual_frequency_claims_allowed": False,
            "physical_probability_claims_allowed": False,
            "risk_exposure_vulnerability_claims_allowed": False,
        },
        "scale_up_authorized": False,
        "operational_claims_allowed": False,
    }
    return report


def build_candidate_generation_report(
    *,
    repo_root: Path,
    terrain_crop_path: Path,
    terrain_metadata_path: Path,
    source_zone_metadata_path: Path,
) -> dict[str, Any]:
    try:
        return AOI_CANDIDATES.build_report(
            repo_root=repo_root,
            terrain_crop_path=terrain_crop_path,
            terrain_metadata_path=terrain_metadata_path,
            source_zone_metadata_path=source_zone_metadata_path,
        )
    except AOI_CANDIDATES.TerrainReleaseZoneCandidateMetricsError as exc:
        return {
            "schema_version": AOI_CANDIDATES.SCHEMA_VERSION,
            "candidate_metrics_status": "blocked_missing_inputs",
            "candidate_release_zone_set_status": "not_emitted",
            "candidate_release_zone_interpretation": "not_claimed",
            "candidate_site_id": "chant_sura_fluelapass_portability_example_v1",
            "candidate_site_name": "Chant Sura / Flüelapass portability example",
            "blocked_missing_inputs": [
                str(terrain_crop_path),
                str(terrain_metadata_path),
                str(source_zone_metadata_path),
            ],
            "blocked_reason": str(exc),
            "scale_up_authorized": False,
            "operational_claims_allowed": False,
            "claim_boundaries": {
                "heuristic_workflow_input_only": True,
                "validated_release_zone_evidence": False,
                "field_validation_claims_allowed": False,
                "physical_release_probability_claims_allowed": False,
                "scale_up_authorized": False,
                "operational_claims_allowed": False,
                "notes": [
                    "candidate cells are heuristic workflow inputs, not validated release zones",
                    "candidate generation fails closed when the terrain crop is missing or malformed",
                ],
            },
        }


def build_case_skeleton_report(
    *,
    preflight_report: dict[str, Any],
    paths: dict[str, Path],
    repo_root: Path,
    readiness_report: dict[str, Any],
) -> dict[str, Any]:
    if preflight_report.get("core_input_status") != "ready":
        return {
            "schema_version": CASE_SKELETON.SCHEMA_VERSION,
            "case_skeleton_status": "blocked_missing_inputs",
            "reference_validation_status": "blocked_missing_inputs",
            "ensemble_execution_status": "blocked_template_only",
            "blocked_reason": preflight_report.get("blocked_reason", "required terrain, source-zone, scenario, or policy inputs are not ready"),
            "generated_case_path": "",
            "generated_case_paths": [],
            "write_status": "blocked",
            "scale_up_authorized": False,
            "operational_claims_allowed": False,
        }

    output_root = DEFAULT_TINY_ENSEMBLE_ROOT
    case_path = output_root / CASE_SKELETON.CASE_FILENAME
    case = CASE_SKELETON.build_case_skeleton(
        preflight_report=preflight_report,
        paths=paths,
        output_root=output_root,
        case_path=case_path,
    )
    case["generation_boundary"]["preflight_status"] = readiness_report["real_context_readiness_gate_status"]
    return {
        "schema_version": CASE_SKELETON.SCHEMA_VERSION,
        "case_skeleton_status": "ready",
        "reference_validation_status": "ready",
        "ensemble_execution_status": "blocked_template_only",
        "blocked_reason": "deferred_public_context_inputs",
        "candidate_site_id": preflight_report.get("candidate_site_id", ""),
        "candidate_site_name": preflight_report.get("candidate_site_name", ""),
        "preflight_status": readiness_report["real_context_readiness_gate_status"],
        "generated_case_path": str(case_path),
        "generated_case_paths": [str(case_path)],
        "output_root": str(output_root),
        "output_path_strategy": "tmp_or_ignored_only",
        "write_status": "not_written",
        "site_extent": preflight_report.get("site_extent_or_placeholder", {}),
        "source_zone_scenario_contract": preflight_report.get("source_zone_scenario_contract", {}),
        "terrain_source_zone_scenario_policy_refs": {
            "terrain_crop": str(paths["terrain_crop"]),
            "terrain_metadata": str(paths["terrain_metadata"]),
            "source_zone_metadata": str(paths["source_zone_metadata"]),
            "scenario_table": str(paths["scenario_table"]),
            "source_scenario_policy": str(paths["source_scenario_policy"]),
        },
        "deferred_public_context_categories": list(preflight_report.get("deferred_public_context_categories", [])),
        "deferred_public_context_paths_or_patterns": list(preflight_report.get("deferred_public_context_paths_or_patterns", [])),
        "deferred_public_context_placeholders": case["deferred_public_context_placeholders"],
        "claim_boundaries": case["claim_boundaries"],
        "case_skeleton": case,
        "scale_up_authorized": False,
        "operational_claims_allowed": False,
    }


def collect_blocked_missing_inputs(
    *,
    readiness_report: dict[str, Any],
    preflight_report: dict[str, Any],
    candidate_generation_report: dict[str, Any],
    scenario_generation_report: dict[str, Any],
    command_plan_report: dict[str, Any],
    case_skeleton_report: dict[str, Any],
) -> list[str]:
    blocked: list[str] = []
    blocked.extend(str(item) for item in readiness_report.get("blocked_missing_inputs", []) if item)
    blocked.extend(str(item) for item in preflight_report.get("blocked_missing_inputs", []) if item)
    blocked.extend(str(item) for item in candidate_generation_report.get("blocked_missing_inputs", []) if item)
    blocked.extend(str(item) for item in scenario_generation_report.get("missing_inputs", []) if item)
    blocked.extend(str(item) for item in case_skeleton_report.get("blocked_reason", "").split("; ") if item and case_skeleton_report.get("case_skeleton_status") == "blocked_missing_inputs")
    if command_plan_report.get("second_site_portability_status") == "blocked_missing_inputs":
        blocked.extend(str(item) for item in command_plan_report.get("blocked_missing_inputs", []) if item)
    return dedupe(blocked)


def build_tiny_bounded_ensemble_handoff_status(
    *,
    workflow_classification: str,
    allow_tiny_ensemble_handoff: bool,
) -> str:
    if workflow_classification != "ready_for_next_step":
        return "blocked_missing_inputs"
    return "ready" if allow_tiny_ensemble_handoff else "blocked_missing_permission"


def build_tiny_bounded_ensemble_handoff(
    *,
    candidate_site_id: str,
    candidate_site_name: str,
    repo_root: Path,
    case_skeleton_report: dict[str, Any],
    command_plan_report: dict[str, Any],
    readiness_report: dict[str, Any],
    tiny_handoff_status: str,
    tiny_ensemble_note: str,
) -> dict[str, Any]:
    return {
        "schema_version": "chant_sura_tiny_bounded_ensemble_handoff_v1",
        "status": tiny_handoff_status,
        "candidate_site_id": candidate_site_id,
        "candidate_site_name": candidate_site_name,
        "repo_root": str(repo_root),
        "case_skeleton_path": case_skeleton_report.get("generated_case_path", ""),
        "command_plan_status": command_plan_report.get("command_plan_status", "blocked_missing_inputs"),
        "readiness_status": readiness_report.get("real_context_readiness_gate_status", "blocked_missing_inputs"),
        "requires_explicit_permission": True,
        "permission_note": tiny_ensemble_note,
        "blocked_reason": (
            "explicit permission not recorded"
            if tiny_handoff_status == "blocked_missing_permission"
            else "required real-context inputs are missing"
            if tiny_handoff_status == "blocked_missing_inputs"
            else ""
        ),
        "claim_boundaries": {
            "operational_claims_allowed": False,
            "scale_up_authorized": False,
            "physical_probability_claims_allowed": False,
        },
    }


def build_workflow_steps(
    *,
    readiness_report: dict[str, Any],
    case_skeleton_report: dict[str, Any],
    candidate_generation_report: dict[str, Any],
    scenario_generation_report: dict[str, Any],
    command_plan_report: dict[str, Any],
    tiny_handoff_report: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        {
            "step_id": "public_context_readiness",
            "status": readiness_report.get("real_context_readiness_gate_status", "blocked_missing_inputs"),
            "blocked_reason": readiness_report.get("public_context_boundary_status", ""),
            "expected_inputs": readiness_report.get("acquisition_manifest_product_summaries", []),
        },
        {
            "step_id": "aoi_preparation",
            "status": case_skeleton_report.get("case_skeleton_status", "blocked_missing_inputs"),
            "blocked_reason": case_skeleton_report.get("blocked_reason", ""),
            "expected_inputs": list(case_skeleton_report.get("terrain_source_zone_scenario_policy_refs", {}).values()),
        },
        {
            "step_id": "release_candidate_generation",
            "status": candidate_generation_report.get("candidate_metrics_status", "blocked_missing_inputs"),
            "blocked_reason": candidate_generation_report.get("blocked_reason", ""),
            "expected_inputs": list(candidate_generation_report.get("terrain_inputs", {}).values())
            + list(candidate_generation_report.get("source_zone_inputs", {}).values()),
        },
        {
            "step_id": "scenario_generation",
            "status": scenario_generation_report.get("scenario_plan_status", "blocked_missing_inputs"),
            "blocked_reason": scenario_generation_report.get("blocked_reason", ""),
            "expected_inputs": [
                scenario_generation_report.get("source_policy_provenance", {}).get("policy_path", ""),
                scenario_generation_report.get("reference_scenario_table", {}).get("path", ""),
            ],
        },
        {
            "step_id": "command_planning",
            "status": command_plan_report.get("command_plan_status", "blocked_missing_inputs"),
            "blocked_reason": command_plan_report.get("public_context_boundary_status", ""),
            "expected_inputs": list(command_plan_report.get("blocked_second_site_commands", [])),
        },
        {
            "step_id": "tiny_bounded_ensemble_handoff",
            "status": tiny_handoff_report.get("status", "blocked_missing_inputs"),
            "blocked_reason": tiny_handoff_report.get("blocked_reason", ""),
            "expected_inputs": [tiny_handoff_report.get("case_skeleton_path", "")],
        },
    ]


def dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        ordered.append(item)
    return ordered


def render_text_report(report: dict[str, Any]) -> str:
    lines = [
        f"schema_version: {report['schema_version']}",
        f"workflow_classification: {report['workflow_classification']}",
        f"candidate_site_id: {report['candidate_site_id']}",
        f"candidate_site_name: {report['candidate_site_name']}",
        f"scale_up_authorized: {str(report['scale_up_authorized']).lower()}",
        f"operational_claims_allowed: {str(report['operational_claims_allowed']).lower()}",
        "",
        "public_context_readiness:",
        f"- real_context_readiness_gate_status: {report['public_context_readiness'].get('real_context_readiness_gate_status', '')}",
        f"- real_context_product_readiness_status: {report['public_context_readiness'].get('real_context_product_readiness', {}).get('readiness_status', '')}",
        f"- real_context_product_ready_count: {report['public_context_readiness'].get('real_context_product_readiness', {}).get('ready_product_count', '')}",
        f"- real_context_product_deferred_count: {report['public_context_readiness'].get('real_context_product_readiness', {}).get('deferred_product_count', '')}",
        f"- real_context_product_missing_count: {report['public_context_readiness'].get('real_context_product_readiness', {}).get('missing_product_count', '')}",
        f"- real_context_staging_checklist_state: {report['public_context_readiness'].get('real_context_staging_checklist_state', '')}",
        f"- deferred_public_context_status: {report['public_context_readiness'].get('deferred_public_context_status', '')}",
        "",
        "aoi_preparation:",
        f"- case_skeleton_status: {report['aoi_preparation'].get('case_skeleton_status', '')}",
        f"- generated_case_path: {report['aoi_preparation'].get('generated_case_path', '')}",
        f"- blocked_reason: {report['aoi_preparation'].get('blocked_reason', '')}",
        "",
        "release_candidate_generation:",
        f"- candidate_metrics_status: {report['release_candidate_generation'].get('candidate_metrics_status', '')}",
        f"- candidate_release_zone_set_status: {report['release_candidate_generation'].get('candidate_release_zone_set_status', '')}",
        "",
        "scenario_generation:",
        f"- scenario_plan_status: {report['scenario_generation'].get('scenario_plan_status', '')}",
        "",
        "command_planning:",
        f"- command_plan_status: {report['command_planning'].get('command_plan_status', '')}",
        f"- blocked_template_commands: {report['command_planning'].get('blocked_template_commands', [])}",
        "",
        "tiny_bounded_ensemble_handoff:",
        f"- status: {report['tiny_bounded_ensemble_handoff'].get('status', '')}",
        f"- blocked_reason: {report['tiny_bounded_ensemble_handoff'].get('blocked_reason', '')}",
        f"- permission_note: {report['tiny_bounded_ensemble_handoff'].get('permission_note', '')}",
        "",
        "workflow_steps:",
    ]
    for step in report.get("workflow_steps", []):
        lines.append(f"- {step.get('step_id', '')}: {step.get('status', '')}")
        if step.get("blocked_reason"):
            lines.append(f"  blocked_reason: {step['blocked_reason']}")
    if report.get("blocked_missing_inputs"):
        lines.extend(["", "blocked_missing_inputs:"])
        lines.extend(f"- {item}" for item in report["blocked_missing_inputs"])
    lines.extend(["", "ready_for_next_step:"])
    ready = report.get("ready_for_next_step", {})
    lines.append(f"- status: {ready.get('status', '')}")
    lines.append(f"- next_step: {ready.get('next_step', '')}")
    lines.append(f"- requires_explicit_permission: {ready.get('requires_explicit_permission', False)}")
    lines.append(f"- permission_recorded: {ready.get('permission_recorded', False)}")
    lines.append(f"- permission_note: {ready.get('permission_note', '')}")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
