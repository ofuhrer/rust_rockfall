#!/usr/bin/env python3
"""Summarize an adaptive AOI ensemble convergence controller.

The helper is read-only. It combines a measured hazard-map comparison, the
output-budget gate, the same-scale Balfrin frontier, and the bounded next-step
feasibility probe into one controller report. It proposes bounded
trajectory-count increments until convergence stabilizes or a runtime/output
budget stops the run.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.lib import output_profile_policy as OUTPUT_PROFILE_POLICY


SCHEMA_VERSION = "adaptive_aoi_ensemble_convergence_controller_v1"
DEFAULT_CURRENT_MANIFEST = ROOT / "hazard/results/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_manifest.json"
DEFAULT_CANDIDATE_MANIFEST = ROOT / "hazard/results/tschamut_public_pilot/target_gate_v1/validation_tschamut_public_target_gate_v1_manifest.json"
DEFAULT_OUTPUT_BUDGET_RECORD = ROOT / "validation/pilot_runs/tschamut_public_output_budget_reducer_gate_v1.yaml"
DEFAULT_CONVERGENCE_PROTOCOL_RECORD = ROOT / "validation/pilot_runs/tschamut_public_conditional_convergence_protocol_v1.yaml"
DEFAULT_CURRENT_TRAJECTORY_COUNT = 60
DEFAULT_TRAJECTORY_CAP = 1000


def _load_module(module_name: str, filename: str):
    path = ROOT / "scripts" / filename
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ControllerError(f"failed to load helper module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


COMPARE = _load_module("adaptive_aoi_controller_compare", "compare_hazard_map_convergence.py")
FRONTIER = _load_module("adaptive_aoi_controller_frontier", "summarize_balfrin_ensemble_frontier.py")
FEASIBILITY = _load_module("adaptive_aoi_controller_feasibility", "summarize_bounded_next_ensemble_feasibility_probe.py")


class ControllerError(ValueError):
    """User-facing adaptive controller error."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    parser.add_argument("--current-manifest", type=Path, default=DEFAULT_CURRENT_MANIFEST)
    parser.add_argument("--candidate-manifest", type=Path, default=DEFAULT_CANDIDATE_MANIFEST)
    parser.add_argument("--current-trajectory-count", type=int, default=DEFAULT_CURRENT_TRAJECTORY_COUNT)
    parser.add_argument("--trajectory-cap", type=int, default=DEFAULT_TRAJECTORY_CAP)
    parser.add_argument("--output-budget-record", type=Path, default=DEFAULT_OUTPUT_BUDGET_RECORD)
    parser.add_argument(
        "--convergence-protocol-record",
        type=Path,
        default=DEFAULT_CONVERGENCE_PROTOCOL_RECORD,
    )
    args = parser.parse_args(argv)

    try:
        report = build_report(
            current_manifest=args.current_manifest,
            candidate_manifest=args.candidate_manifest,
            current_trajectory_count=args.current_trajectory_count,
            trajectory_cap=args.trajectory_cap,
            output_budget_record=args.output_budget_record,
            convergence_protocol_record=args.convergence_protocol_record,
        )
    except ControllerError as exc:
        print(f"adaptive AOI ensemble convergence controller error: {exc}", file=sys.stderr)
        return 2

    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text_report(report))

    return 0 if report["controller_status"] != "blocked_missing_inputs" else 2


def build_report(
    *,
    current_manifest: Path = DEFAULT_CURRENT_MANIFEST,
    candidate_manifest: Path = DEFAULT_CANDIDATE_MANIFEST,
    current_trajectory_count: int = DEFAULT_CURRENT_TRAJECTORY_COUNT,
    trajectory_cap: int = DEFAULT_TRAJECTORY_CAP,
    output_budget_record: Path = DEFAULT_OUTPUT_BUDGET_RECORD,
    convergence_protocol_record: Path = DEFAULT_CONVERGENCE_PROTOCOL_RECORD,
    comparison_override: dict[str, Any] | None = None,
    frontier_override: dict[str, Any] | None = None,
    feasibility_override: dict[str, Any] | None = None,
    output_budget_override: dict[str, Any] | None = None,
    current_manifest_report_override: dict[str, Any] | None = None,
    candidate_manifest_report_override: dict[str, Any] | None = None,
) -> dict[str, Any]:
    comparison = comparison_override or COMPARE.compare_hazard_map_convergence([current_manifest, candidate_manifest])
    if current_manifest_report_override is not None:
        current_manifest_report = dict(current_manifest_report_override)
    else:
        current_manifest_report = manifest_report(current_manifest)
    if candidate_manifest_report_override is not None:
        candidate_manifest_report = dict(candidate_manifest_report_override)
    else:
        candidate_manifest_report = manifest_report(candidate_manifest)
    output_budget = output_budget_override or load_yaml(output_budget_record)
    convergence_protocol = load_yaml(convergence_protocol_record)
    frontier = frontier_override or FRONTIER.build_report()
    feasibility = feasibility_override or FEASIBILITY.build_report()

    output_profile = dict(output_budget.get("output_profile") or {})
    current_profile = dict(output_profile.get("current_target_gate_profile") or {})
    followup_profile = dict(output_profile.get("selected_followup_profile") or {})
    selected_profile_policy = OUTPUT_PROFILE_POLICY.classify_output_profile_policy(
        conditional_curve_export="summary-only" if followup_profile else None,
        grid_csv_export="none" if followup_profile else None,
        no_plots=True if followup_profile else None,
        label="adaptive_aoi_followup_profile",
    )

    convergence_assessment = assess_convergence(comparison)
    budget_assessment = assess_output_budget(output_budget, selected_profile_policy)
    trajectory_schedule = build_trajectory_schedule(
        current_trajectory_count=current_trajectory_count,
        trajectory_cap=trajectory_cap,
        base_output_file_count=number_or_none(current_manifest_report.get("performance", {}).get("output_file_count")),
        base_output_bytes=number_or_none(current_manifest_report.get("performance", {}).get("output_bytes")),
        base_hazard_file_count=number_or_none(candidate_manifest_report.get("performance", {}).get("output_file_count")),
        base_hazard_bytes=number_or_none(candidate_manifest_report.get("performance", {}).get("output_bytes")),
    )
    controller_status = classify_controller_status(convergence_assessment, budget_assessment)
    execution_mode = classify_execution_mode(controller_status, selected_profile_policy, frontier, feasibility)

    adaptive_plan = build_adaptive_plan(
        controller_status=controller_status,
        execution_mode=execution_mode,
        current_trajectory_count=current_trajectory_count,
        trajectory_cap=trajectory_cap,
        trajectory_schedule=trajectory_schedule,
        convergence_assessment=convergence_assessment,
        budget_assessment=budget_assessment,
        frontier=frontier,
        feasibility=feasibility,
        current_manifest=current_manifest,
        candidate_manifest=candidate_manifest,
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "controller_status": controller_status,
        "execution_mode": execution_mode,
        "read_only": True,
        "scale_up_authorized": False,
        "distributed_execution_authorized": False,
        "operational_claims_allowed": False,
        "claim_boundaries": {
            "annual_frequency_claims_allowed": False,
            "physical_probability_claims_allowed": False,
            "risk_exposure_vulnerability_claims_allowed": False,
            "operational_claims_allowed": False,
            "scale_up_authorized": False,
            "distributed_execution_authorized": False,
        },
        "current_trajectory_count": current_trajectory_count,
        "trajectory_cap": trajectory_cap,
        "current_manifest": str(current_manifest),
        "candidate_manifest": str(candidate_manifest),
        "current_manifest_report": current_manifest_report,
        "candidate_manifest_report": candidate_manifest_report,
        "comparison": comparison,
        "output_budget_record": output_budget,
        "convergence_protocol_record": convergence_protocol,
        "frontier_report": frontier,
        "feasibility_report": feasibility,
        "output_profile_policy": selected_profile_policy,
        "adaptive_plan": adaptive_plan,
    }


def manifest_report(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ControllerError(f"manifest is missing: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ControllerError(f"manifest must be a JSON object: {path}")
    return data


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ControllerError(f"record is missing: {path}")
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ControllerError(f"record must be a mapping: {path}")
    return payload


def assess_convergence(comparison: dict[str, Any]) -> dict[str, Any]:
    overall = dict(comparison.get("overall_metrics") or {})
    cellwise = {}
    first_comparison = (comparison.get("comparisons") or [{}])[0]
    if isinstance(first_comparison, dict):
        cellwise = dict(first_comparison.get("cellwise_metrics") or {})
    cellwise_overall = dict(cellwise.get("overall_metrics") or {})
    stable = (
        comparison.get("status") == COMPARE.OK_STATUS
        and float(overall.get("layer_summary_max_abs_diff") or 0.0) == 0.0
        and float(overall.get("layer_summary_sum_abs_diff") or 0.0) == 0.0
        and int(overall.get("output_checksum_mismatch_count") or 0) == 0
        and int(overall.get("output_checksum_missing_count") or 0) == 0
        and float(cellwise_overall.get("cellwise_linf_abs_diff_max") or 0.0) == 0.0
        and float(cellwise_overall.get("cellwise_l1_abs_diff_sum") or 0.0) == 0.0
        and float(cellwise_overall.get("cellwise_rmse_max") or 0.0) == 0.0
        and int(cellwise_overall.get("cellwise_nodata_mismatch_count") or 0) == 0
    )
    return {
        "status": "converged" if stable else "not_converged",
        "comparison_status": comparison.get("status"),
        "shared_layer_count": overall.get("shared_layer_count"),
        "layer_summary_max_abs_diff": overall.get("layer_summary_max_abs_diff"),
        "layer_summary_sum_abs_diff": overall.get("layer_summary_sum_abs_diff"),
        "output_checksum_mismatch_count": overall.get("output_checksum_mismatch_count"),
        "cellwise_metrics": cellwise_overall,
        "stop_reason": (
            "spatial convergence stabilized"
            if stable
            else "spatial convergence still changes across one or more layers"
        ),
    }


def assess_output_budget(output_budget: dict[str, Any], profile_policy: dict[str, Any]) -> dict[str, Any]:
    output_profile = dict(output_budget.get("output_profile") or {})
    selected_followup_profile = dict(output_profile.get("selected_followup_profile") or {})
    validation_budget = dict(output_budget.get("validation_output_budget") or {})
    hazard_budget = dict(output_budget.get("hazard_output_budget") or {})
    reducer_scaling = dict(output_budget.get("reducer_scaling") or {})
    current_classification = str(output_budget.get("current_classification") or "")
    validation_blocked = validation_budget.get("status") in {"blocker_retained", "blocked_before_scale_up"}
    hazard_blocked = hazard_budget.get("status") in {"blocker_retained", "blocked_before_scale_up"}
    reducer_blocked = reducer_scaling.get("status") not in {None, "recorded"}
    profile_blocked = profile_policy.get("classification") == OUTPUT_PROFILE_POLICY.BLOCKED_UNSCALABLE_DEFAULT

    blocked = bool(validation_blocked or hazard_blocked or reducer_blocked or profile_blocked or current_classification == "blocked_before_scale_up")
    return {
        "status": "budget_stopped" if blocked else "budget_open",
        "current_classification": current_classification,
        "validation_output_budget": validation_budget,
        "hazard_output_budget": hazard_budget,
        "reducer_scaling": reducer_scaling,
        "selected_followup_profile": selected_followup_profile,
        "profile_policy": profile_policy,
        "stop_reason": (
            "runtime/output budget blocks another escalation"
            if blocked
            else "output budget remains open for another bounded step"
        ),
    }


def classify_controller_status(convergence_assessment: dict[str, Any], budget_assessment: dict[str, Any]) -> str:
    if convergence_assessment["status"] == "converged":
        return "converged"
    if budget_assessment["status"] == "budget_stopped":
        return "budget_stopped"
    return "inconclusive"


def classify_execution_mode(
    controller_status: str,
    profile_policy: dict[str, Any],
    frontier: dict[str, Any],
    feasibility: dict[str, Any],
) -> str:
    if controller_status != "inconclusive":
        return "local"
    if (
        profile_policy.get("classification") == OUTPUT_PROFILE_POLICY.SCALABLE_DEFAULT
        and frontier.get("frontier_status") == "measured_existing_artifacts"
        and frontier.get("recommendation_class") == "defer_small_bounded_ensemble"
        and str(feasibility.get("bounded_probe_recommendation_status") or "") != "blocked_pending_evidence"
    ):
        return "balfrin_ready"
    return "local"


def build_trajectory_schedule(
    *,
    current_trajectory_count: int,
    trajectory_cap: int,
    base_output_file_count: float | None,
    base_output_bytes: float | None,
    base_hazard_file_count: float | None,
    base_hazard_bytes: float | None,
) -> dict[str, Any]:
    current = max(int(current_trajectory_count), 1)
    cap = max(int(trajectory_cap), current)
    increments = [max(20, current // 2), max(20, current), max(20, current * 2)]
    counts: list[int] = []
    step_rows: list[dict[str, Any]] = []
    running = current
    for increment in increments:
        next_count = min(cap, running + increment)
        if counts and next_count == counts[-1]:
            continue
        counts.append(next_count)
        step_rows.append(
            {
                "trajectory_count": next_count,
                "trajectory_increment": next_count - running,
                "expected_validation_output_file_count": scale_value(base_output_file_count, current, next_count),
                "expected_validation_output_bytes": scale_value(base_output_bytes, current, next_count),
                "expected_hazard_output_file_count": scale_value(base_hazard_file_count, current, next_count),
                "expected_hazard_output_bytes": scale_value(base_hazard_bytes, current, next_count),
            }
        )
        running = next_count

    return {
        "current_trajectory_count": current,
        "trajectory_cap": cap,
        "trajectory_increments": [row["trajectory_increment"] for row in step_rows],
        "planned_trajectory_counts": counts,
        "step_rows": step_rows,
    }


def scale_value(value: float | None, current: int, next_count: int) -> int | None:
    if value is None:
        return None
    return int(math.ceil(float(value) * (next_count / max(current, 1))))


def build_adaptive_plan(
    *,
    controller_status: str,
    execution_mode: str,
    current_trajectory_count: int,
    trajectory_cap: int,
    trajectory_schedule: dict[str, Any],
    convergence_assessment: dict[str, Any],
    budget_assessment: dict[str, Any],
    frontier: dict[str, Any],
    feasibility: dict[str, Any],
    current_manifest: Path,
    candidate_manifest: Path,
) -> dict[str, Any]:
    feasibility_proposed = dict(feasibility.get("proposed_probe") or {})
    proposed_probe = dict(feasibility_proposed)
    expected_command = proposed_probe.get("expected_command") or dict(feasibility.get("command_plan_template") or {}).get("command")
    if trajectory_schedule["step_rows"]:
        next_row = dict(trajectory_schedule["step_rows"][0])
        proposed_probe["trajectory_count"] = next_row["trajectory_count"]
        proposed_probe["expected_output_file_count"] = next_row["expected_validation_output_file_count"]
        proposed_probe["expected_output_bytes"] = next_row["expected_validation_output_bytes"]
        proposed_probe["expected_hazard_output_file_count"] = next_row["expected_hazard_output_file_count"]
        proposed_probe["expected_hazard_output_bytes"] = next_row["expected_hazard_output_bytes"]

    command_plan_status = "ready" if execution_mode == "balfrin_ready" else "local_only"
    command_plan = {
        "schema_version": "adaptive_aoi_ensemble_convergence_command_plan_v1",
        "status": command_plan_status,
        "execution_mode": execution_mode,
        "current_trajectory_count": current_trajectory_count,
        "trajectory_cap": trajectory_cap,
        "trajectory_schedule": trajectory_schedule,
        "stop_criteria": [
            {
                "name": "spatial_convergence_stable",
                "status": convergence_assessment["status"],
                "reason": convergence_assessment["stop_reason"],
            },
            {
                "name": "runtime_output_budget_open",
                "status": budget_assessment["status"],
                "reason": budget_assessment["stop_reason"],
            },
        ],
        "recommended_probe": proposed_probe,
        "frontier_recommendation_class": frontier.get("recommendation_class"),
        "frontier_recommendation_reason": frontier.get("recommendation_reason"),
        "expected_command": expected_command,
        "command_plan_summary": (
            "Bounded local post-processing remains the default"
            if execution_mode == "local"
            else "Preflights pass, so the next bounded post-processing step is Balfrin-ready"
        ),
    }

    if execution_mode == "balfrin_ready":
        command_plan["command_templates"] = [
            {
                "command_id": "adaptive_aoi_convergence_compare",
                "command": (
                    "PYENV_VERSION=system uv run python scripts/compare_hazard_map_convergence.py "
                    f"{current_manifest} {candidate_manifest} --format json"
                ),
                "expected_outputs": ["JSON convergence comparison"],
            },
            {
                "command_id": "adaptive_aoi_balfrin_probe_plan",
                "command": "PYENV_VERSION=system uv run python scripts/submit_balfrin_probe.py --local-command-plan <probe-manifest>",
                "expected_outputs": ["JSON submission-package-ready command plan"],
            },
        ]
    else:
        command_plan["command_templates"] = [
            {
                "command_id": "adaptive_aoi_local_convergence_compare",
                "command": (
                    "PYENV_VERSION=system uv run python scripts/compare_hazard_map_convergence.py "
                    f"{current_manifest} {candidate_manifest} --format json"
                ),
                "expected_outputs": ["JSON convergence comparison"],
            }
        ]

    return command_plan


def render_text_report(report: dict[str, Any]) -> str:
    plan = report.get("adaptive_plan") or {}
    convergence = report.get("comparison") or {}
    budget = report.get("output_budget_record") or {}
    lines = [
        "# Adaptive AOI Ensemble Convergence Controller",
        f"- Controller status: `{report['controller_status']}`",
        f"- Execution mode: `{report['execution_mode']}`",
        f"- Current trajectory count: `{report['current_trajectory_count']}`",
        f"- Planned trajectory counts: `{', '.join(str(item) for item in plan.get('trajectory_schedule', {}).get('planned_trajectory_counts', []))}`",
        f"- Stop reason: {plan.get('stop_criteria', [{}])[0].get('reason')}",
        f"- Budget reason: {plan.get('stop_criteria', [{}, {}])[1].get('reason')}",
        "",
        "## Convergence",
        "",
        f"- Comparison status: `{convergence.get('status')}`",
        f"- Max abs diff: `{(convergence.get('overall_metrics') or {}).get('layer_summary_max_abs_diff')}`",
        f"- Output checksum mismatches: `{(convergence.get('overall_metrics') or {}).get('output_checksum_mismatch_count')}`",
        "",
        "## Output Budget",
        "",
        f"- Current classification: `{budget.get('current_classification')}`",
        f"- Follow-up policy: `{(report.get('output_profile_policy') or {}).get('classification')}`",
        "",
        "## Command Plan",
        "",
        f"- Status: `{plan.get('status')}`",
        f"- Summary: {plan.get('command_plan_summary')}",
    ]
    for row in plan.get("trajectory_schedule", {}).get("step_rows", []):
        lines.append(
            "- "
            f"trajectory_count `{row['trajectory_count']}` "
            f"file_count `{row['expected_validation_output_file_count']}` "
            f"bytes `{row['expected_validation_output_bytes']}`"
        )
    return "\n".join(lines)


def number_or_none(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


if __name__ == "__main__":
    raise SystemExit(main())
