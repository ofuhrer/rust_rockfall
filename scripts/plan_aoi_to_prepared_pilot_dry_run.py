#!/usr/bin/env python3
"""Compose the Chant Sura AOI-to-prepared-pilot dry-run workflow.

This is a read-only orchestrator. It chains the existing AOI acquisition,
real-context gate, release-zone heuristic dry run, release-plan dry run, and
portable command-plan helpers into one deterministic workflow report. It does
not download data, stage public products, or run any ensemble work.
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
SCHEMA_VERSION = "aoi_to_prepared_pilot_dry_run_v1"
DEFAULT_SITE_CONFIG = ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml"
DEFAULT_COMMAND_PLAN_SITE = "chant_sura_fluelapass"


def _load_module(module_name: str, filename: str):
    path = ROOT / "scripts" / filename
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load helper module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


AOI_ACQUISITION = _load_module("aoi_to_prepared_pilot_aoi_acquisition", "plan_swisstopo_aoi_acquisition.py")
REAL_CONTEXT_GATE = _load_module("aoi_to_prepared_pilot_real_context_gate", "check_chant_sura_real_context_readiness_gate.py")
RELEASE_ZONE = _load_module("aoi_to_prepared_pilot_release_zone", "plan_release_zone_heuristic_dry_run.py")
RELEASE_PLAN = _load_module("aoi_to_prepared_pilot_release_plan", "plan_release_plan_dry_run.py")
COMMAND_PLAN = _load_module("aoi_to_prepared_pilot_command_plan", "generate_pilot_command_plan.py")


@contextmanager
def _patched_repo_root(repo_root: Path) -> Iterator[None]:
    patched_targets = [
        (AOI_ACQUISITION, "ROOT"),
        (AOI_ACQUISITION.PREFLIGHT, "ROOT"),
        (REAL_CONTEXT_GATE, "ROOT"),
        (REAL_CONTEXT_GATE.PREFLIGHT, "ROOT"),
        (RELEASE_ZONE, "ROOT"),
        (RELEASE_ZONE.PREFLIGHT, "ROOT"),
        (RELEASE_PLAN, "ROOT"),
        (RELEASE_PLAN.PREFLIGHT, "ROOT"),
    ]
    originals: list[tuple[Any, str, Any]] = []
    for module, attr in patched_targets:
        originals.append((module, attr, getattr(module, attr)))
        setattr(module, attr, repo_root)
    try:
        yield
    finally:
        for module, attr, original in reversed(originals):
            setattr(module, attr, original)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site-config", type=Path, default=DEFAULT_SITE_CONFIG)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    args = parser.parse_args(argv)

    report = build_report(args.site_config, repo_root=args.repo_root)

    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    output = json.dumps(report, indent=2, sort_keys=True) if args.format == "json" else render_text_report(report)
    print(output)
    return 0 if report["workflow_status"] == "ready" else 2


def build_report(site_config: Path | None, repo_root: Path | None = None) -> dict[str, Any]:
    config_path = site_config or DEFAULT_SITE_CONFIG
    repo_root = repo_root or ROOT

    with _patched_repo_root(repo_root):
        acquisition_report = AOI_ACQUISITION.build_report(config_path)
        real_context_report = REAL_CONTEXT_GATE.build_report(config_path, repo_root=repo_root)
        release_zone_report = RELEASE_ZONE.build_report(config_path, repo_root=repo_root)
        release_plan_report = RELEASE_PLAN.build_report(config_path, repo_root=repo_root)

    command_plan_report = COMMAND_PLAN.build_report(DEFAULT_COMMAND_PLAN_SITE, config_path)

    steps = build_steps(
        acquisition_report=acquisition_report,
        real_context_report=real_context_report,
        release_zone_report=release_zone_report,
        release_plan_report=release_plan_report,
        command_plan_report=command_plan_report,
    )
    generated_output_roots = sorted({root for step in steps for root in step["generated_output_roots"]})
    ignored_output_roots = sorted({root for step in steps for root in step["ignored_output_roots"]})
    blockers = [blocker for step in steps for blocker in step["blockers"]]

    workflow_status = aggregate_workflow_status(step["status"] for step in steps)

    report = {
        "schema_version": SCHEMA_VERSION,
        "workflow_status": workflow_status,
        "candidate_site_id": acquisition_report["candidate_site_id"],
        "candidate_site_name": acquisition_report["candidate_site_name"],
        "candidate_selection_rationale": acquisition_report["candidate_selection_rationale"],
        "site_extent": acquisition_report["site_extent"],
        "step_order": [step["step_id"] for step in steps],
        "workflow_steps": steps,
        "workflow_blockers": blockers,
        "workflow_blocker_count": len(blockers),
        "workflow_generated_output_roots": generated_output_roots,
        "workflow_ignored_output_roots": ignored_output_roots,
        "expected_inputs_by_step": {step["step_id"]: step["expected_inputs"] for step in steps},
        "generated_output_roots_by_step": {
            step["step_id"]: step["generated_output_roots"] for step in steps
        },
        "ignored_output_roots_by_step": {step["step_id"]: step["ignored_output_roots"] for step in steps},
        "acquisition_report": acquisition_report,
        "real_context_gate_report": real_context_report,
        "release_zone_heuristic_report": release_zone_report,
        "release_plan_report": release_plan_report,
        "command_plan_report": command_plan_report,
        "claim_boundaries": real_context_report["claim_boundaries"],
        "scale_up_authorized": False,
        "operational_claims_allowed": False,
    }
    return report


def build_steps(
    *,
    acquisition_report: dict[str, Any],
    real_context_report: dict[str, Any],
    release_zone_report: dict[str, Any],
    release_plan_report: dict[str, Any],
    command_plan_report: dict[str, Any],
) -> list[dict[str, Any]]:
    candidate_site_id = acquisition_report["candidate_site_id"]
    ignored_site_roots = [
        f"validation/private/{candidate_site_id}",
        f"hazard/results/{candidate_site_id}",
    ]

    steps: list[dict[str, Any]] = [
        {
            "step_id": "aoi_acquisition",
            "label": "AOI acquisition contract",
            "status": acquisition_report["acquisition_boundary_status"],
            "blocked_reason": (
                "required core inputs remain missing"
                if acquisition_report["acquisition_boundary_status"] == "blocked_missing_inputs"
                else "public-context products remain deferred"
                if acquisition_report["acquisition_boundary_status"] != "ready"
                else ""
            ),
            "expected_inputs": [
                acquisition_report["acquisition_manifest_path"],
                *acquisition_expected_inputs(acquisition_report),
            ],
            "generated_output_roots": acquisition_report["public_context_acquisition_summary"].get("expected_staging_roots", []),
            "ignored_output_roots": acquisition_report.get("acquisition_manifest_expected_ignored_roots", []),
            "blockers": build_step_blockers(
                "aoi_acquisition",
                acquisition_report["acquisition_boundary_status"],
                acquisition_report.get("acquisition_manifest_expected_ignored_roots", []),
                acquisition_report.get("deferred_public_context_categories", []),
            ),
        },
        {
            "step_id": "public_context_gate",
            "label": "Public-context readiness gate",
            "status": real_context_report["real_context_readiness_gate_status"],
            "blocked_reason": (
                "public-context products are intentionally deferred"
                if real_context_report["real_context_readiness_gate_status"] != "ready"
                else ""
            ),
            "expected_inputs": expected_inputs_from_real_context_gate(real_context_report),
            "generated_output_roots": [],
            "ignored_output_roots": ignored_site_roots,
            "blockers": build_step_blockers(
                "public_context_gate",
                real_context_report["real_context_readiness_gate_status"],
                ignored_site_roots,
                [entry["category"] for entry in real_context_report.get("deferred_public_context_products", [])],
            ),
        },
        {
            "step_id": "release_zone_heuristic_dry_run",
            "label": "Release-zone heuristic dry run",
            "status": release_zone_report["heuristic_dry_run_status"],
            "blocked_reason": release_zone_report["blocked_reason"],
            "expected_inputs": expected_inputs_from_release_zone(release_zone_report),
            "generated_output_roots": [],
            "ignored_output_roots": [],
            "blockers": build_step_blockers(
                "release_zone_heuristic_dry_run",
                release_zone_report["heuristic_dry_run_status"],
                [],
                [entry["category"] for entry in release_zone_report.get("blocked_missing_products", [])],
            ),
        },
        {
            "step_id": "release_plan_dry_run",
            "label": "Release-plan dry run",
            "status": release_plan_report["release_plan_dry_run_status"],
            "blocked_reason": release_plan_report["blocked_reason"],
            "expected_inputs": expected_inputs_from_release_plan(release_plan_report),
            "generated_output_roots": release_plan_generated_output_roots(release_plan_report),
            "ignored_output_roots": release_plan_ignored_output_roots(release_plan_report),
            "blockers": build_step_blockers(
                "release_plan_dry_run",
                release_plan_report["release_plan_dry_run_status"],
                release_plan_ignored_output_roots(release_plan_report),
                [release_plan_report["blocked_reason"]] if release_plan_report["blocked_reason"] else [],
            ),
        },
        {
            "step_id": "prepared_pilot_command_plan",
            "label": "Prepared-pilot command-plan helper",
            "status": command_plan_step_status(command_plan_report),
            "blocked_reason": command_plan_blocked_reason(command_plan_report),
            "expected_inputs": command_plan_expected_inputs(command_plan_report),
            "generated_output_roots": [],
            "ignored_output_roots": command_plan_report["ignored_output_paths"],
            "blockers": build_step_blockers(
                "prepared_pilot_command_plan",
                command_plan_step_status(command_plan_report),
                command_plan_report["ignored_output_paths"],
                command_plan_report.get("blocked_template_commands", []),
            ),
        },
    ]
    return steps


def build_step_blockers(
    step_id: str,
    status: str,
    ignored_output_roots: list[str],
    blocker_payload: list[Any],
) -> list[dict[str, Any]]:
    blockers: list[dict[str, Any]] = []
    if status == "ready":
        return blockers
    blockers.append(
        {
            "step_id": step_id,
            "status": status,
            "ignored_output_roots": ignored_output_roots,
            "details": blocker_payload,
        }
    )
    return blockers


def acquisition_expected_inputs(report: dict[str, Any]) -> list[str]:
    paths: list[str] = []
    for entry in report.get("required_public_geodata_products", []):
        path = entry.get("expected_staged_path")
        if path:
            paths.append(path)
    for entry in report.get("required_metadata_records", []):
        path = entry.get("path_or_pattern")
        if path:
            paths.append(path)
    return dedupe(paths)


def expected_inputs_from_real_context_gate(report: dict[str, Any]) -> list[str]:
    inputs: list[str] = []
    for entry in report.get("local_core_inputs", []):
        expected_path = entry.get("expected_path")
        if expected_path:
            inputs.append(expected_path)
    for entry in report.get("supporting_local_roots", []):
        expected_path = entry.get("expected_path")
        if expected_path:
            inputs.append(expected_path)
    return dedupe(inputs)


def expected_inputs_from_release_zone(report: dict[str, Any]) -> list[str]:
    inputs: list[str] = []
    for entry in report.get("heuristic_inputs", []):
        expected_path = entry.get("path_or_pattern")
        if expected_path:
            inputs.append(expected_path)
    return dedupe(inputs)


def expected_inputs_from_release_plan(report: dict[str, Any]) -> list[str]:
    inputs: list[str] = []
    site_specific_inputs = report.get("site_specific_inputs", {})
    for path in (site_specific_inputs.get("expected_paths") or {}).values():
        if path:
            inputs.append(path)
    return dedupe(inputs)


def release_plan_generated_output_roots(report: dict[str, Any]) -> list[str]:
    outputs = report.get("blocked_second_site_execution_template", {}).get("expected_outputs", [])
    roots = [str(Path(path).parent) for path in outputs if path]
    return dedupe(roots)


def release_plan_ignored_output_roots(report: dict[str, Any]) -> list[str]:
    blocked_template = report.get("blocked_second_site_execution_template", {})
    output_roots = [str(Path(path).parent) for path in blocked_template.get("expected_outputs", []) if path]
    return dedupe(output_roots)


def command_plan_step_status(report: dict[str, Any]) -> str:
    if report.get("blocked_template_commands"):
        return "deferred_public_context_inputs"
    return report.get("second_site_portability_status", "ready")


def command_plan_blocked_reason(report: dict[str, Any]) -> str:
    if report.get("blocked_template_commands"):
        return f"blocked_template_commands: {', '.join(report['blocked_template_commands'])}"
    return ""


def command_plan_expected_inputs(report: dict[str, Any]) -> list[str]:
    inputs: list[str] = []
    for command in report.get("commands", []):
        inputs.extend(command.get("expected_inputs", []))
    return dedupe(inputs)


def aggregate_workflow_status(statuses: Any) -> str:
    statuses = list(statuses)
    if any(status == "blocked_missing_inputs" for status in statuses):
        return "blocked_missing_inputs"
    if any(status != "ready" for status in statuses):
        return "deferred_public_context_inputs"
    return "ready"


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
        f"workflow_status: {report['workflow_status']}",
        f"candidate_site_id: {report['candidate_site_id']}",
        f"candidate_site_name: {report['candidate_site_name']}",
        f"candidate_selection_rationale: {report['candidate_selection_rationale']}",
        f"site_extent: {report['site_extent']}",
        f"scale_up_authorized: {str(report['scale_up_authorized']).lower()}",
        f"operational_claims_allowed: {str(report['operational_claims_allowed']).lower()}",
        "",
        "workflow_steps:",
    ]
    for step in report["workflow_steps"]:
        lines.append(f"- {step['step_id']}: {step['status']} [{step['label']}]")
        if step["blocked_reason"]:
            lines.append(f"  blocked_reason: {step['blocked_reason']}")
        if step["expected_inputs"]:
            lines.append("  expected_inputs:")
            lines.extend(f"  - {item}" for item in step["expected_inputs"])
        if step["generated_output_roots"]:
            lines.append("  generated_output_roots:")
            lines.extend(f"  - {item}" for item in step["generated_output_roots"])
        if step["ignored_output_roots"]:
            lines.append("  ignored_output_roots:")
            lines.extend(f"  - {item}" for item in step["ignored_output_roots"])
    lines.append("")
    lines.append("workflow_generated_output_roots:")
    if report["workflow_generated_output_roots"]:
        lines.extend(f"- {item}" for item in report["workflow_generated_output_roots"])
    else:
        lines.append("- none")
    lines.append("")
    lines.append("workflow_ignored_output_roots:")
    if report["workflow_ignored_output_roots"]:
        lines.extend(f"- {item}" for item in report["workflow_ignored_output_roots"])
    else:
        lines.append("- none")
    lines.append("")
    lines.append("workflow_blockers:")
    if report["workflow_blockers"]:
        for blocker in report["workflow_blockers"]:
            lines.append(
                f"- {blocker['step_id']}: {blocker['status']} ({', '.join(str(item) for item in blocker['details']) if blocker['details'] else 'none'})"
            )
    else:
        lines.append("- none")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
