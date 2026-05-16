#!/usr/bin/env python3
"""Print the current task context for worker agents.

This helper is intentionally read-only. It gives agents a compact view of the
active backlog task, canonical evidence helpers, known local environment
friction, and generated roots that should not be committed.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PYTHON_INVOCATION = "PYENV_VERSION=system uv run python"
CHANT_SURA_CONFIG = (
    "tests/fixtures/second_site_public_geodata_preflight/"
    "chant_sura_fluelapass_candidate.yaml"
)
CURRENT_EXECUTION_FOCUS = (
    "Balfrin single-release-zone pilot track: dry-run automation is in place, "
    "and measured Balfrin execution plus post-run evidence are the next step."
)


@dataclass(frozen=True)
class ActiveTask:
    task_id: str
    title: str
    priority: str | None
    inspect_first: list[str]
    text: str

    def summary(self, *, include_details: bool = True) -> dict[str, Any]:
        summary: dict[str, Any] = {
            "task_id": self.task_id,
            "title": self.title,
        }
        if self.priority:
            summary["priority"] = self.priority
        if include_details:
            summary["inspect_first"] = self.inspect_first
        return summary


CANONICAL_HELPERS = [
    {
        "name": "Tschamut artifact readiness",
        "path": "scripts/check_same_scale_artifact_readiness.py",
        "command": f"{PYTHON_INVOCATION} scripts/check_same_scale_artifact_readiness.py --format json",
    },
    {
        "name": "portable command plans",
        "path": "scripts/generate_pilot_command_plan.py",
        "command": f"{PYTHON_INVOCATION} scripts/generate_pilot_command_plan.py --format json",
    },
    {
        "name": "conditional pilot closure",
        "path": "scripts/summarize_tschamut_conditional_pilot_closure.py",
        "command": f"{PYTHON_INVOCATION} scripts/summarize_tschamut_conditional_pilot_closure.py --format json",
    },
    {
        "name": "hazard rebuild output contract",
        "path": "scripts/check_hazard_rebuild_output_profile.py",
        "command": f"{PYTHON_INVOCATION} scripts/check_hazard_rebuild_output_profile.py --format json",
    },
    {
        "name": "spatial same-scale uncertainty",
        "path": "scripts/summarize_spatial_same_scale_uncertainty.py",
        "command": f"{PYTHON_INVOCATION} scripts/summarize_spatial_same_scale_uncertainty.py --format json",
    },
    {
        "name": "GIS/COG readiness",
        "path": "scripts/audit_gis_cog_package_readiness.py",
        "command": f"{PYTHON_INVOCATION} scripts/audit_gis_cog_package_readiness.py --format json",
    },
    {
        "name": "scratch/sample COG conversion proof",
        "path": "scripts/prototype_cog_conversion.py",
        "command": f"{PYTHON_INVOCATION} scripts/prototype_cog_conversion.py --help",
    },
    {
        "name": "package-level COG conversion",
        "path": "scripts/convert_same_scale_package_to_cog.py",
        "command": f"{PYTHON_INVOCATION} scripts/convert_same_scale_package_to_cog.py --help",
    },
    {
        "name": "bounded reducer/runtime scaling",
        "path": "scripts/summarize_bounded_reducer_runtime_scaling.py",
        "command": f"{PYTHON_INVOCATION} scripts/summarize_bounded_reducer_runtime_scaling.py --format json",
    },
    {
        "name": "second-site portability preflight",
        "path": "scripts/check_second_site_public_geodata_preflight.py",
        "command": (
            f"{PYTHON_INVOCATION} scripts/check_second_site_public_geodata_preflight.py "
            f"--site-config {CHANT_SURA_CONFIG} --format json"
        ),
    },
    {
        "name": "multisite source/scenario audit",
        "path": "scripts/audit_multisite_source_scenario_contract.py",
        "command": f"{PYTHON_INVOCATION} scripts/audit_multisite_source_scenario_contract.py --format json",
    },
    {
        "name": "validation/calibration evidence gaps",
        "path": "scripts/assess_validation_calibration_evidence_gaps.py",
        "command": f"{PYTHON_INVOCATION} scripts/assess_validation_calibration_evidence_gaps.py --format json",
    },
]

GENERATED_ROOTS_TO_AVOID = [
    "data/processed/swisstopo/placeholder_second_site_v1",
    "validation/private/placeholder_second_site_v1",
    "hazard/results/placeholder_second_site_v1",
    "validation/policies/*placeholder*",
    "verification/results/",
    "validation/results/",
    "hazard/results/",
    "target/",
]

KNOWN_ENVIRONMENT_ISSUES = [
    {
        "issue": "local pyenv shims can point at a missing interpreter",
        "instruction": f"use `{PYTHON_INVOCATION}` instead of plain `python` or `python3`",
    },
    {
        "issue": "no repository pre-push hook is installed",
        "instruction": (
            "run task-specific checks, git diff --check, check_repo_consistency.py, "
            "and scripts/git-hooks/pre-commit before committing or pushing"
        ),
    },
    {
        "issue": "tests for second-site fixtures can create stray placeholder paths",
        "instruction": "check placeholder roots before committing and remove unintended generated files",
    },
]

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", help="task id to focus, for example TB-041")
    parser.add_argument("--format", choices=("json", "text"), default="text")
    parser.add_argument(
        "--detail",
        choices=("compact", "full"),
        default="compact",
        help="compact is worker-oriented; full includes all active task details and all helpers",
    )
    parser.add_argument(
        "--no-live-checks",
        action="store_true",
        help="summarize canonical commands without running read-only checks",
    )
    return parser.parse_args()


def read_backlog(root: Path = ROOT) -> str:
    return (root / "docs/task_backlog.md").read_text()


def parse_active_tasks(backlog_text: str) -> list[ActiveTask]:
    active_match = re.search(r"^## Active Tasks\s*$", backlog_text, re.MULTILINE)
    deferred_match = re.search(r"^## Deferred Backlog\s*$", backlog_text, re.MULTILINE)
    if not active_match or not deferred_match or deferred_match.start() <= active_match.end():
        return []

    active_text = backlog_text[active_match.end() : deferred_match.start()]
    headings = list(re.finditer(r"^###\s+(TB-\d+):?\s+(.+?)\s*$", active_text, re.MULTILINE))
    tasks: list[ActiveTask] = []
    for index, heading in enumerate(headings):
        start = heading.end()
        end = headings[index + 1].start() if index + 1 < len(headings) else len(active_text)
        section = active_text[start:end].strip()
        tasks.append(
            ActiveTask(
                task_id=heading.group(1),
                title=heading.group(2).strip(),
                priority=parse_priority(section),
                inspect_first=parse_inspect_first(section),
                text=section,
            )
        )
    return tasks


def parse_priority(section: str) -> str | None:
    match = re.search(r"^Priority:\s*(P\d+)\s*$", section, re.MULTILINE)
    return match.group(1) if match else None


def parse_inspect_first(section: str) -> list[str]:
    match = re.search(r"^Inspect first:\s*$", section, re.MULTILINE)
    if not match:
        return []
    rest = section[match.end() :]
    items: list[str] = []
    for line in rest.splitlines():
        stripped = line.strip()
        if not stripped:
            if items:
                break
            continue
        if not stripped.startswith("- "):
            if items:
                break
            continue
        item = stripped[2:].strip()
        if item.startswith("`") and item.endswith("`"):
            item = item[1:-1]
        items.append(item)
    return items


def run_json_command(command: list[str], *, timeout_s: int = 120) -> dict[str, Any]:
    env = os.environ.copy()
    env["PYENV_VERSION"] = "system"
    try:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            env=env,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
    except FileNotFoundError as exc:
        return {"status": "command_unavailable", "error": str(exc), "command": command}
    except subprocess.TimeoutExpired:
        return {"status": "command_timed_out", "timeout_s": timeout_s, "command": command}

    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        if completed.returncode != 0:
            return {
                "status": "command_failed",
                "returncode": completed.returncode,
                "stderr": completed.stderr.strip()[-2000:],
                "command": command,
            }
        return {
            "status": "non_json_output",
            "stdout": completed.stdout.strip()[:2000],
            "command": command,
        }
    status = "ok" if completed.returncode == 0 else payload.get("readiness_status") or payload.get("portability_preflight_status") or "json_nonzero_exit"
    return {"status": status, "returncode": completed.returncode, "payload": payload, "command": command}


def should_run_chant_sura_preflight(task: ActiveTask | None, tasks: list[ActiveTask]) -> bool:
    haystack = " ".join([task.title + " " + task.text if task else "", *(t.title for t in tasks)])
    terms = ("Chant Sura", "second-site", "Flüelapass", "holdout")
    return any(term.lower() in haystack.lower() for term in terms)


def relevant_helpers(task: ActiveTask | None, *, detail: str) -> list[dict[str, str]]:
    if detail == "full" or task is None:
        return CANONICAL_HELPERS

    haystack = " ".join([task.title, task.text, *task.inspect_first]).lower()
    selected: list[dict[str, str]] = []

    def add_by_path(path: str) -> None:
        helper = next((candidate for candidate in CANONICAL_HELPERS if candidate["path"] == path), None)
        if helper and helper not in selected:
            selected.append(helper)

    for helper in CANONICAL_HELPERS:
        if helper["path"].lower() in haystack:
            selected.append(helper)

    keyword_paths = [
        (("same-scale", "tschamut", "readiness"), "scripts/check_same_scale_artifact_readiness.py"),
        (("command", "plan"), "scripts/generate_pilot_command_plan.py"),
        (("closure",), "scripts/summarize_tschamut_conditional_pilot_closure.py"),
        (("rebuild", "reduced", "output"), "scripts/check_hazard_rebuild_output_profile.py"),
        (("spatial", "uncertainty", "hotspot", "stability"), "scripts/summarize_spatial_same_scale_uncertainty.py"),
        (("cog", "gis", "geotiff"), "scripts/audit_gis_cog_package_readiness.py"),
        (("cog", "conversion", "package"), "scripts/convert_same_scale_package_to_cog.py"),
        (("runtime", "scaling", "ensemble feasibility"), "scripts/summarize_bounded_reducer_runtime_scaling.py"),
        (("chant sura", "second-site", "flüelapass", "aoi"), "scripts/check_second_site_public_geodata_preflight.py"),
        (("source", "scenario", "multisite"), "scripts/audit_multisite_source_scenario_contract.py"),
        (("physical", "credibility", "calibration", "validation"), "scripts/assess_validation_calibration_evidence_gaps.py"),
    ]
    for terms, path in keyword_paths:
        if any(term in haystack for term in terms):
            add_by_path(path)

    if not selected:
        add_by_path("scripts/generate_pilot_command_plan.py")
    return selected


def build_report(task_id: str | None = None, *, run_checks: bool = True, detail: str = "compact") -> dict[str, Any]:
    backlog_text = read_backlog()
    active_tasks = parse_active_tasks(backlog_text)
    task = next((candidate for candidate in active_tasks if candidate.task_id == task_id), None) if task_id else None
    backlog_refill_needed = not active_tasks

    status = "ready"
    if task_id and task is None:
        status = "blocked_missing_task"

    report: dict[str, Any] = {
        "agent_task_context_status": status,
        "repo_root": str(ROOT),
        "invocation_cwd": str(Path.cwd()),
        "running_from_repo_root": Path.cwd().resolve() == ROOT.resolve(),
        "python_invocation": PYTHON_INVOCATION,
        "requested_task_id": task_id,
        "detail": detail,
        "selected_task": task.summary(include_details=True) if task else None,
        "active_tasks": [
            candidate.summary(include_details=(detail == "full" or candidate == task))
            for candidate in active_tasks
        ],
        "backlog_refill_needed": backlog_refill_needed,
        "backlog_note": "Backlog refill needed" if backlog_refill_needed else None,
        "current_execution_focus": CURRENT_EXECUTION_FOCUS if backlog_refill_needed else None,
        "canonical_helpers": relevant_helpers(task, detail=detail),
        "known_environment_issues": KNOWN_ENVIRONMENT_ISSUES,
        "generated_roots_to_avoid": GENERATED_ROOTS_TO_AVOID,
        "existing_generated_placeholder_paths": scan_existing_placeholder_paths(),
        "push_policy": {
            "repository_pre_push_hook": "not_installed",
            "instruction": (
                "run task-specific checks, git diff --check, "
                "scripts/check_repo_consistency.py, and scripts/git-hooks/pre-commit "
                "before committing or pushing"
            ),
        },
        "read_only": True,
        "recommended_first_commands": recommended_first_commands(task_id),
        "live_checks": {},
    }

    if run_checks:
        report["live_checks"]["same_scale_readiness"] = run_json_command(
            ["uv", "run", "python", "scripts/check_same_scale_artifact_readiness.py", "--format", "json"]
        )
        report["live_checks"]["command_plan"] = run_json_command(
            ["uv", "run", "python", "scripts/generate_pilot_command_plan.py", "--format", "json"]
        )
        if should_run_chant_sura_preflight(task, active_tasks):
            report["live_checks"]["chant_sura_preflight"] = run_json_command(
                [
                    "uv",
                    "run",
                    "python",
                    "scripts/check_second_site_public_geodata_preflight.py",
                    "--site-config",
                    CHANT_SURA_CONFIG,
                    "--format",
                    "json",
                ]
            )
    else:
        report["live_checks_status"] = "skipped"

    return report


def recommended_first_commands(task_id: str | None) -> list[str]:
    commands = [
        "cd /Users/fuhrer/Desktop/rust_rockfall/main",
        "git pull --ff-only origin main",
    ]
    task_arg = f" --task {task_id}" if task_id else ""
    commands.append(f"{PYTHON_INVOCATION} scripts/print_agent_task_context.py{task_arg} --format json")
    return commands


def scan_existing_placeholder_paths(root: Path = ROOT) -> list[str]:
    paths: list[Path] = []
    for base in (
        root / "data/processed/swisstopo",
        root / "validation/private",
        root / "hazard/results",
        root / "validation/policies",
    ):
        if not base.exists():
            continue
        paths.extend(path for path in base.rglob("*") if "placeholder_second_site_v1" in str(path))
        paths.extend(path for path in base.rglob("*placeholder*") if path.is_file())
    return sorted({str(path.relative_to(root)) for path in paths})


def render_text(report: dict[str, Any]) -> str:
    lines = [
        f"agent_task_context_status: {report['agent_task_context_status']}",
        f"repo_root: {report['repo_root']}",
        f"invocation_cwd: {report['invocation_cwd']}",
        f"running_from_repo_root: {str(report['running_from_repo_root']).lower()}",
        f"python_invocation: {report['python_invocation']}",
        f"requested_task_id: {report.get('requested_task_id') or ''}",
    ]
    selected = report.get("selected_task")
    if selected:
        lines.append(f"selected_task: {selected['task_id']} {selected['title']}")
        if selected["inspect_first"]:
            lines.append("inspect_first:")
            lines.extend(f"- {item}" for item in selected["inspect_first"])
    lines.append("active_tasks:")
    for task in report["active_tasks"]:
        lines.append(f"- {task['task_id']}: {task['title']}")
    if report.get("backlog_note"):
        lines.append(f"backlog_note: {report['backlog_note']}")
    if report.get("current_execution_focus"):
        lines.append(f"current_execution_focus: {report['current_execution_focus']}")
    lines.append("recommended_first_commands:")
    lines.extend(f"- {command}" for command in report["recommended_first_commands"])
    lines.append("canonical_helpers:")
    lines.extend(f"- {helper['name']}: {helper['path']}" for helper in report["canonical_helpers"])
    lines.append("generated_roots_to_avoid:")
    lines.extend(f"- {root}" for root in report["generated_roots_to_avoid"])
    if report.get("existing_generated_placeholder_paths"):
        lines.append("existing_generated_placeholder_paths:")
        lines.extend(f"- {path}" for path in report["existing_generated_placeholder_paths"])
    if report.get("live_checks"):
        lines.append("live_checks:")
        for name, result in report["live_checks"].items():
            lines.append(f"- {name}: {result.get('status')}")
    lines.append(f"push_policy: {report['push_policy']['repository_pre_push_hook']}")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    report = build_report(args.task, run_checks=not args.no_live_checks, detail=args.detail)
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text(report))
    return 0 if report["agent_task_context_status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
