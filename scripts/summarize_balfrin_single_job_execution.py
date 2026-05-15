#!/usr/bin/env python3
"""Summarize whether the current Balfrin single-job path is sufficient.

This summary is intentionally record-driven. It reads the existing Balfrin and
reducer evidence records, reports measured wall time, memory, output size,
restartability, and reducer-state evidence, and classifies distributed
execution as deferred, design-needed, or blocked pending evidence.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml


DEFAULT_REPEATABILITY_RECORD = Path(
    "validation/pilot_runs/tschamut_public_slurm_probe_repeatability_v1.yaml"
)
DEFAULT_REPRODUCTION_RECORD = Path(
    "validation/pilot_runs/tschamut_public_balfrin_target_gate_reproduction_v1.yaml"
)
DEFAULT_OUTPUT_BUDGET_RECORD = Path(
    "validation/pilot_runs/tschamut_public_output_budget_reducer_gate_v1.yaml"
)
DEFAULT_CONVERGENCE_RECORD = Path(
    "validation/pilot_runs/tschamut_public_conditional_convergence_protocol_v1.yaml"
)
DEFAULT_FEASIBILITY_RECORD = Path(
    "validation/pilot_runs/tschamut_public_ensemble_feasibility_v1.yaml"
)
DEFAULT_CURRENT_GAP_RECORD = Path(
    "validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml"
)


class SufficiencySummaryError(ValueError):
    """User-facing sufficiency summary error."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeatability-record", type=Path, default=DEFAULT_REPEATABILITY_RECORD)
    parser.add_argument("--reproduction-record", type=Path, default=DEFAULT_REPRODUCTION_RECORD)
    parser.add_argument("--output-budget-record", type=Path, default=DEFAULT_OUTPUT_BUDGET_RECORD)
    parser.add_argument("--convergence-record", type=Path, default=DEFAULT_CONVERGENCE_RECORD)
    parser.add_argument("--feasibility-record", type=Path, default=DEFAULT_FEASIBILITY_RECORD)
    parser.add_argument("--current-gap-record", type=Path, default=DEFAULT_CURRENT_GAP_RECORD)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    args = parser.parse_args(argv)

    try:
        summary = build_summary(
            repeatability_record=args.repeatability_record,
            reproduction_record=args.reproduction_record,
            output_budget_record=args.output_budget_record,
            convergence_record=args.convergence_record,
            feasibility_record=args.feasibility_record,
            current_gap_record=args.current_gap_record,
        )
    except SufficiencySummaryError as exc:
        print(f"balfrin single-job sufficiency summary error: {exc}", file=sys.stderr)
        return 2

    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.output_md:
        args.output_md.parent.mkdir(parents=True, exist_ok=True)
        args.output_md.write_text(render_markdown(summary), encoding="utf-8")
    if not args.output_json and not args.output_md:
        print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


def build_summary(
    *,
    repeatability_record: Path = DEFAULT_REPEATABILITY_RECORD,
    reproduction_record: Path = DEFAULT_REPRODUCTION_RECORD,
    output_budget_record: Path = DEFAULT_OUTPUT_BUDGET_RECORD,
    convergence_record: Path = DEFAULT_CONVERGENCE_RECORD,
    feasibility_record: Path = DEFAULT_FEASIBILITY_RECORD,
    current_gap_record: Path = DEFAULT_CURRENT_GAP_RECORD,
) -> dict[str, Any]:
    required_paths = [
        repeatability_record,
        reproduction_record,
        output_budget_record,
        convergence_record,
        feasibility_record,
        current_gap_record,
    ]
    missing = [str(path) for path in required_paths if not path.exists()]
    if missing:
        return {
            "schema_version": "balfrin_single_job_execution_sufficiency_v1",
            "pilot_id": "tschamut_public_pilot",
            "measurement_status": "blocked_pending_evidence",
            "decision": "blocked_pending_evidence",
            "feasibility_decision": "blocked_pending_evidence",
            "final_classification": "blocked_pending_evidence",
            "single_job_sufficient_for_next_step": False,
            "distributed_execution_authorized": False,
            "missing_required_inputs": missing,
            "record_paths": record_paths(
                repeatability_record,
                reproduction_record,
                output_budget_record,
                convergence_record,
                feasibility_record,
                current_gap_record,
            ),
            "recommended_next_step": (
                "Acquire the missing Balfrin evidence records and rerun the sufficiency summary."
            ),
            "defaults_changed": False,
        }

    repeatability = load_yaml(repeatability_record)
    reproduction = load_yaml(reproduction_record)
    output_budget = load_yaml(output_budget_record)
    convergence = load_yaml(convergence_record)
    feasibility = load_yaml(feasibility_record)
    current_gap = load_yaml(current_gap_record)

    driver_ready = bool(
        dig(repeatability, "selected_gate_readiness_decision", "driver_ready_for_selected_gate_use")
    )
    repeat_runs = ensure_list(dig(repeatability, "repeat_runs"), "repeatability.repeat_runs")
    repeatability_assessment = ensure_mapping(
        dig(repeatability, "repeatability_assessment"), "repeatability.repeatability_assessment"
    )
    numerical_stability = ensure_mapping(
        dig(repeatability, "numerical_artifact_stability"), "repeatability.numerical_artifact_stability"
    )
    restartability_ok = (
        repeatability.get("classification") == "pass_with_scope_limits"
        and repeatability_assessment.get("repeat_reuse_classification") == "pass_reuse_stable"
        and repeatability_assessment.get("trajectory_plan_id_stable") is True
        and repeatability_assessment.get("reducer_plan_id_stable") is True
        and bool(repeatability_assessment.get("trajectory_reuse_decisions_stable"))
        and bool(repeatability_assessment.get("reducer_reuse_decisions_stable"))
        and numerical_stability.get("classification") == "pass_hash_stable"
        and numerical_stability.get("changed_artifact_count") == 0
        and len(repeat_runs) >= 2
        and all(
            repeatability_run.get("trajectory_decision_counts", {}).get("reused_completed_state") == 2
            and repeatability_run.get("reducer_decision_counts", {}).get("reused_completed_state") == 2
            for repeatability_run in repeat_runs
        )
        and driver_ready
    )

    reducer_execution = ensure_mapping(
        dig(reproduction, "conditional_execution", "reducer"), "reproduction.conditional_execution.reducer"
    )
    output_budget_reducer = ensure_mapping(
        dig(output_budget, "reducer_scaling"), "output_budget.reducer_scaling"
    )
    reducer_state_ok = (
        output_budget_reducer.get("status") == "recorded"
        and output_budget_reducer.get("local_restartability_status") == "recorded"
        and output_budget_reducer.get("reducer_chunk_manifest_status") == "generated"
        and output_budget_reducer.get("reducer_execution_index_status") == "generated"
        and output_budget_reducer.get("reducer_merge_state_status") == "generated"
        and reducer_execution.get("merge_order") == "sorted_chunk_id"
        and reducer_execution.get("merge_order_independent") is True
    )

    wall_time_evidence = {
        "repeatability_fresh_baseline_total_wall_seconds": dig(
            repeatability, "fresh_baseline", "total_wall_seconds"
        ),
        "repeatability_fresh_baseline_command_sequence_wall_seconds": dig(
            repeatability, "fresh_baseline", "command_sequence_wall_seconds"
        ),
        "repeatability_repeat_run_total_wall_seconds": [
            dig(run, "total_wall_seconds") for run in repeat_runs
        ],
        "reproduction_validation_wall_seconds": dig(
            reproduction, "performance", "validation_total_wall_seconds"
        ),
        "reproduction_hazard_wall_seconds": dig(reproduction, "performance", "hazard_total_wall_seconds"),
        "current_gap_runtime_seconds": dig(current_gap, "run_evidence", "runtime_seconds"),
    }

    memory_evidence = {
        "current_gap_memory_peak_mb": dig(current_gap, "run_evidence", "memory_peak_mb"),
        "reproduction_validation_memory_peak_bytes_on_darwin": dig(
            feasibility, "output_budget_assessment", "target_validation_memory_peak_bytes_on_darwin"
        ),
        "reproduction_hazard_memory_peak_bytes_on_darwin": dig(
            feasibility, "output_budget_assessment", "target_hazard_memory_peak_bytes_on_darwin"
        ),
        "output_budget_validation_memory_peak_bytes_on_darwin": dig(
            feasibility, "output_budget_assessment", "target_validation_memory_peak_bytes_on_darwin"
        ),
        "output_budget_hazard_memory_peak_bytes_on_darwin": dig(
            feasibility, "output_budget_assessment", "target_hazard_memory_peak_bytes_on_darwin"
        ),
    }

    output_size_evidence = {
        "repeatability_fresh_baseline_output_file_count": dig(
            repeatability, "fresh_baseline", "output_file_count"
        ),
        "repeatability_fresh_baseline_output_bytes": dig(repeatability, "fresh_baseline", "output_bytes"),
        "repeatability_repeat_output_file_counts": [
            dig(run, "output_file_count") for run in repeat_runs
        ],
        "repeatability_repeat_output_bytes": [
            dig(run, "output_bytes") for run in repeat_runs
        ],
        "reproduction_validation_output_file_count": dig(
            reproduction, "performance", "validation_output_file_count"
        ),
        "reproduction_validation_output_bytes": dig(
            reproduction, "performance", "validation_output_bytes"
        ),
        "reproduction_hazard_output_file_count": dig(
            reproduction, "performance", "hazard_output_file_count"
        ),
        "reproduction_hazard_output_bytes": dig(reproduction, "performance", "hazard_output_bytes"),
        "current_gap_output_file_count": dig(current_gap, "run_evidence", "output_file_count"),
        "current_gap_output_bytes": dig(current_gap, "run_evidence", "output_total_bytes"),
        "output_budget_validation_output_file_count": dig(
            output_budget, "validation_output_budget", "file_count"
        ),
        "output_budget_validation_output_bytes": dig(
            output_budget, "validation_output_budget", "bytes"
        ),
        "output_budget_hazard_output_file_count": dig(
            output_budget, "hazard_output_budget", "file_count"
        ),
        "output_budget_hazard_output_bytes": dig(output_budget, "hazard_output_budget", "bytes"),
    }

    restartability_evidence = {
        "driver_ready_for_selected_gate_use": driver_ready,
        "fresh_baseline_job_id": dig(repeatability, "fresh_baseline", "job_id"),
        "repeat_job_ids": [dig(run, "job_id") for run in repeat_runs],
        "repeat_reuse_classification": dig(repeatability, "repeatability_assessment", "repeat_reuse_classification"),
        "trajectory_plan_id_stable": dig(
            repeatability, "repeatability_assessment", "trajectory_plan_id_stable"
        ),
        "reducer_plan_id_stable": dig(repeatability, "repeatability_assessment", "reducer_plan_id_stable"),
        "numerical_artifact_classification": dig(
            repeatability, "numerical_artifact_stability", "classification"
        ),
        "changed_artifact_count": dig(repeatability, "numerical_artifact_stability", "changed_artifact_count"),
        "output_file_count_stable": dig(
            repeatability, "repeatability_assessment", "output_file_count_stable"
        ),
        "metadata_byte_identity_required": dig(
            repeatability, "repeatability_assessment", "metadata_byte_identity_required"
        ),
    }

    reducer_state_evidence = {
        "reducer_mode": dig(reproduction, "conditional_execution", "reducer", "mode"),
        "reducer_workers": dig(reproduction, "conditional_execution", "reducer", "worker_count"),
        "reducer_chunk_count": dig(reproduction, "conditional_execution", "reducer", "chunk_count"),
        "reducer_merge_order": dig(reproduction, "conditional_execution", "reducer", "merge_order"),
        "reducer_merge_order_independent": dig(
            reproduction, "conditional_execution", "reducer", "merge_order_independent"
        ),
        "reducer_parity_status": dig(
            output_budget, "selected_dt04_output_evidence", "reducer_parity_status"
        ),
        "local_restartability_status": dig(output_budget, "reducer_scaling", "local_restartability_status"),
        "reducer_chunk_manifest_status": dig(output_budget, "reducer_scaling", "reducer_chunk_manifest_status"),
        "reducer_execution_index_status": dig(output_budget, "reducer_scaling", "reducer_execution_index_status"),
        "reducer_merge_state_status": dig(output_budget, "reducer_scaling", "reducer_merge_state_status"),
        "worker_counts_compared": dig(output_budget, "reducer_scaling", "worker_counts_compared"),
    }

    convergence_blockers = ensure_list(
        dig(convergence, "assessment", "blocking_reasons"), "convergence.assessment.blocking_reasons"
    )
    feasibility_blockers = ensure_list(dig(feasibility, "blockers"), "feasibility.blockers")
    feasibility_missing = ensure_list(
        dig(feasibility, "convergence_assessment", "missing_diagnostics"),
        "feasibility.convergence_assessment.missing_diagnostics",
    )
    scientific_blockers = []
    for name, source, basis in (
        (
            "conditional_hazard_convergence_not_accepted",
            "conditional_convergence_protocol",
            "current_classification remains inconclusive in the convergence protocol",
        ),
        (
            "manual_gis_visual_qa_secondary_only",
            "conditional_convergence_protocol",
            "manual GIS/QGIS QA remains secondary and not run here",
        ),
        (
            "forest_obstacle_context_limiting",
            "conditional_convergence_protocol",
            "forest/obstacle context remains limiting",
        ),
        (
            "validation_debug_output_budget_retained",
            "conditional_convergence_protocol",
            "validation-side debug output remains retained",
        ),
    ):
        scientific_blockers.append({"name": name, "source": source, "basis": basis})
    for blocker in feasibility_blockers:
        scientific_blockers.append(
            {
                "name": blocker,
                "source": "ensemble_feasibility_record",
                "basis": "recorded as a current blocker to increase the selected-domain run",
            }
        )
    for blocker in convergence_blockers:
        scientific_blockers.append(
            {
                "name": blocker,
                "source": "conditional_convergence_protocol",
                "basis": "recorded as an active convergence blocker",
            }
        )
    for diagnostic in feasibility_missing:
        scientific_blockers.append(
            {
                "name": diagnostic,
                "source": "ensemble_feasibility_record",
                "basis": "missing diagnostic remains part of the no-go record",
            }
        )
    scientific_blockers = dedupe_by_name(scientific_blockers)

    execution_blockers = dedupe_by_name(
        [
            {
                "name": "distributed_execution_not_authorized",
                "source": "output_budget_reducer_gate",
                "basis": "distributed reducers and SLURM arrays remain outside the current authorization",
            },
            {
                "name": "single_job_driver_remains_sufficient",
                "source": "balfrin_probe_repeatability",
                "basis": "repeat and reproduction evidence show the single-job path is stable for the next same-scale step",
            },
            {
                "name": "single_job_restartability_recorded",
                "source": "output_budget_reducer_gate",
                "basis": "restart and merge state evidence is recorded under the single-job boundary",
            },
        ]
    )

    current_file_count = dig(current_gap, "run_evidence", "output_file_count")
    current_byte_count = dig(current_gap, "run_evidence", "output_total_bytes")
    file_margin = None
    byte_margin = None
    if isinstance(current_file_count, int):
        file_margin = 200 - current_file_count
    if isinstance(current_byte_count, int):
        byte_margin = 250_000_000 - current_byte_count

    final_decision = classify_distribution_decision(
        restartability_ok=restartability_ok,
        reducer_state_ok=reducer_state_ok,
        current_file_count=current_file_count,
        current_byte_count=current_byte_count,
    )

    summary = {
        "schema_version": "balfrin_single_job_execution_sufficiency_v1",
        "pilot_id": "tschamut_public_pilot",
        "run_id": "tschamut_public_conditional_gate_v1",
        "measurement_status": "completed_local_record_measurement",
        "decision": final_decision,
        "feasibility_decision": final_decision,
        "final_classification": final_decision,
        "single_job_sufficient_for_next_step": final_decision == "defer",
        "distributed_execution_authorized": False,
        "defaults_changed": bool(dig(current_gap, "physics_freeze", "defaults_changed") is True),
        "file_family_pressure": "validation_debug_artifacts",
        "validation_output_blocker_status": dig(
            output_budget, "validation_output_budget", "status"
        ),
        "record_paths": record_paths(
            repeatability_record,
            reproduction_record,
            output_budget_record,
            convergence_record,
            feasibility_record,
            current_gap_record,
        ),
        "wall_time_evidence": wall_time_evidence,
        "memory_evidence": memory_evidence,
        "output_size_evidence": output_size_evidence,
        "restartability_evidence": restartability_evidence,
        "reducer_state_evidence": reducer_state_evidence,
        "scientific_blockers": scientific_blockers,
        "execution_blockers": execution_blockers,
        "required_inputs": {
            "repeatability_record": str(repeatability_record),
            "reproduction_record": str(reproduction_record),
            "output_budget_record": str(output_budget_record),
            "convergence_record": str(convergence_record),
            "feasibility_record": str(feasibility_record),
            "current_gap_record": str(current_gap_record),
        },
        "current_pressure": {
            "current_file_count": current_file_count,
            "current_byte_count": current_byte_count,
            "file_margin_to_ceiling": file_margin,
            "byte_margin_to_ceiling": byte_margin,
        },
        "limitations": [
            "This summary reuses recorded Balfrin and reducer evidence; it does not run a new simulation.",
            "Distributed execution remains unauthorized by the current evidence set.",
            "The summary stays conditional and non-operational and does not change physics, defaults, thresholds, or baselines.",
        ],
        "recommended_next_step": recommended_next_step(final_decision),
    }
    return summary


def classify_distribution_decision(
    *,
    restartability_ok: bool,
    reducer_state_ok: bool,
    current_file_count: int | None,
    current_byte_count: int | None,
) -> str:
    if current_file_count is None or current_byte_count is None:
        return "blocked_pending_evidence"
    if not restartability_ok or not reducer_state_ok:
        return "design_needed"
    return "defer"


def recommended_next_step(decision: str) -> str:
    if decision == "defer":
        return (
            "Continue using the single-job Balfrin SLURM driver for the next same-scale "
            "selected Tschamut conditional hazard-map reproduction; keep distributed "
            "execution deferred until a new measurement shows a capacity need."
        )
    if decision == "design_needed":
        return (
            "Collect a new measured probe that demonstrates single-job saturation or failed "
            "restartability before designing distributed execution."
        )
    return "Acquire the missing Balfrin evidence records and rerun the sufficiency summary."


def render_markdown(summary: dict[str, Any]) -> str:
    if summary["decision"] == "blocked_pending_evidence":
        missing = "\n".join(f"- `{path}`" for path in summary.get("missing_required_inputs", []))
        return (
            "# Balfrin Single-Job Execution Sufficiency\n\n"
            "Status: blocked because required evidence records are absent.\n\n"
            f"Missing inputs:\n\n{missing}\n"
        )

    lines = [
        "# Balfrin Single-Job Execution Sufficiency",
        "",
        f"- Decision: `{summary['decision']}`",
        f"- Single-job sufficient for next step: `{summary['single_job_sufficient_for_next_step']}`",
        f"- Distributed execution authorized: `{summary['distributed_execution_authorized']}`",
        f"- Final classification: `{summary['final_classification']}`",
        f"- Feasibility decision: `{summary['feasibility_decision']}`",
        f"- Validation output blocker status: `{summary['validation_output_blocker_status']}`",
        f"- File-family pressure: `{summary['file_family_pressure']}`",
        f"- Defaults changed: `{summary['defaults_changed']}`",
        "",
        "## Wall Time Evidence",
        "",
    ]
    for key, value in summary["wall_time_evidence"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Memory Evidence", ""])
    for key, value in summary["memory_evidence"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Output Size Evidence", ""])
    for key, value in summary["output_size_evidence"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Restartability Evidence", ""])
    for key, value in summary["restartability_evidence"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Reducer State Evidence", ""])
    for key, value in summary["reducer_state_evidence"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Scientific Blockers", ""])
    for blocker in summary["scientific_blockers"]:
        lines.append(
            f"- `{blocker['name']}` from `{blocker['source']}`: {blocker['basis']}"
        )
    lines.extend(["", "## Execution Blockers", ""])
    for blocker in summary["execution_blockers"]:
        lines.append(
            f"- `{blocker['name']}` from `{blocker['source']}`: {blocker['basis']}"
        )
    lines.extend(
        [
            "",
            "## Recommended Next Step",
            "",
            summary["recommended_next_step"],
            "",
            "## Limitations",
            "",
        ]
    )
    for item in summary["limitations"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Record Paths",
            "",
        ]
    )
    for label, path in summary["record_paths"].items():
        lines.append(f"- `{label}`: `{path}`")
    return "\n".join(lines)


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - user-facing path context.
        raise SufficiencySummaryError(f"failed to read YAML {path}: {exc}") from exc
    return ensure_mapping(data, str(path))


def ensure_mapping(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SufficiencySummaryError(f"{name} must be a mapping")
    return value


def ensure_list(value: Any, name: str) -> list[Any]:
    if not isinstance(value, list):
        raise SufficiencySummaryError(f"{name} must be a list")
    return value


def dig(mapping: dict[str, Any], *keys: str) -> Any:
    current: Any = mapping
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
    return current


def dedupe_by_name(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    deduped: list[dict[str, Any]] = []
    for entry in entries:
        name = str(entry.get("name"))
        if name in seen:
            continue
        seen.add(name)
        deduped.append(entry)
    return deduped


def record_paths(
    repeatability_record: Path,
    reproduction_record: Path,
    output_budget_record: Path,
    convergence_record: Path,
    feasibility_record: Path,
    current_gap_record: Path,
) -> dict[str, str]:
    return {
        "repeatability_record": str(repeatability_record),
        "reproduction_record": str(reproduction_record),
        "output_budget_record": str(output_budget_record),
        "convergence_record": str(convergence_record),
        "feasibility_record": str(feasibility_record),
        "current_gap_record": str(current_gap_record),
    }


if __name__ == "__main__":
    raise SystemExit(main())
