#!/usr/bin/env python3
"""Validate a selected-pilot ensemble-size feasibility decision record.

The record is a share-safe gate for deciding whether to increase a conditional
pilot ensemble. It does not run trajectories, tune model parameters, introduce
annual frequency, or approve operational use.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml


DECISIONS = {"proceed", "no_go", "inconclusive"}
STATUSES = {"pass", "no-go", "inconclusive"}
REQUIRED_BLOCKERS_FOR_NO_GO = {
    "target_scale_convergence_not_established",
    "manual_gis_visual_qa_inconclusive",
    "forest_obstacle_omission_limiting",
}
REQUIRED_PRECONDITIONS = {
    "use_summary_only_conditional_curve_export",
    "record_convergence_diagnostics",
    "record_output_budget",
    "review_manual_gis_visual_qa",
    "review_forest_obstacle_context",
}
MISLEADING_PATTERNS = [
    re.compile(r"\bannual(?:ized)?\s+(?:frequency|probability|rate)\b", re.IGNORECASE),
    re.compile(r"\breturn[- ]?period\b", re.IGNORECASE),
    re.compile(r"\brisk[- ]?map\b", re.IGNORECASE),
    re.compile(r"\boperational(?:ly)?\s+(?:approved|validated|ready|hazard)\b", re.IGNORECASE),
    re.compile(r"\bvalidated\s+hazard\b", re.IGNORECASE),
]


class EnsembleFeasibilityError(ValueError):
    """User-facing ensemble feasibility validation error."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", type=Path)
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args(argv)
    try:
        summary = validate_feasibility_record(args.record)
    except EnsembleFeasibilityError as exc:
        print(f"pilot ensemble feasibility validation error: {exc}", file=sys.stderr)
        return 2
    if args.format == "json":
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(
            "pilot ensemble feasibility record is valid: "
            f"{args.record} ({summary['decision']}, "
            f"{summary['gate_trajectories_per_release_zone']} -> "
            f"{summary['proposed_trajectories_per_release_zone']} trajectories/release)"
        )
    return 0


def validate_feasibility_record(record_path: Path) -> dict[str, Any]:
    record = read_yaml(record_path)
    require(
        record.get("schema_version") == "pilot_ensemble_feasibility_v1",
        "schema_version must be pilot_ensemble_feasibility_v1",
    )
    require_text(record.get("pilot_id"), "pilot_id")
    require_text(record.get("run_id"), "run_id")
    require(record.get("roadmap_item") == "target_5_ensemble_size_feasibility", "roadmap_item must be target_5_ensemble_size_feasibility")
    decision = require_text(record.get("decision"), "decision")
    require(decision in DECISIONS, f"decision must be one of {sorted(DECISIONS)}")
    require(record.get("operational_status") == "research_diagnostic", "operational_status must remain research_diagnostic")

    inputs = validate_input_evidence(require_mapping(record.get("input_evidence"), "input_evidence"))
    convergence = validate_convergence(require_mapping(record.get("convergence_assessment"), "convergence_assessment"))
    output_budget = validate_output_budget(require_mapping(record.get("output_budget_assessment"), "output_budget_assessment"))
    validate_execution_plan(require_mapping(record.get("execution_plan"), "execution_plan"), decision)
    preconditions = set(require_list(record.get("required_preconditions_before_increase"), "required_preconditions_before_increase"))
    missing_preconditions = sorted(REQUIRED_PRECONDITIONS - preconditions)
    require(not missing_preconditions, f"missing required preconditions before ensemble increase: {missing_preconditions}")
    validate_claim_boundary(require_mapping(record.get("claim_boundary"), "claim_boundary"))

    blockers = set(require_list(record.get("blockers"), "blockers"))
    if decision == "proceed":
        require(not blockers, "proceed decision must not list blockers")
        require(convergence["status"] == "pass", "proceed decision requires convergence_assessment.status pass")
        require(output_budget["status"] == "pass", "proceed decision requires output_budget_assessment.status pass")
    elif decision == "no_go":
        missing_blockers = sorted(REQUIRED_BLOCKERS_FOR_NO_GO - blockers)
        require(not missing_blockers, f"no_go decision missing required blockers: {missing_blockers}")
        require(convergence["status"] == "no-go", "no_go decision requires convergence_assessment.status no-go")
    else:
        require(blockers, "inconclusive decision requires explicit blockers or unresolved limitations")

    scan_text_for_misleading_claims(record)
    return {
        "schema_version": record["schema_version"],
        "pilot_id": record["pilot_id"],
        "run_id": record["run_id"],
        "decision": decision,
        "gate_trajectories_per_release_zone": inputs["gate_trajectories_per_release_zone"],
        "proposed_trajectories_per_release_zone": inputs["proposed_trajectories_per_release_zone"],
        "convergence_status": convergence["status"],
        "output_budget_status": output_budget["status"],
        "blocker_count": len(blockers),
    }


def validate_input_evidence(inputs: dict[str, Any]) -> dict[str, int]:
    require_text(inputs.get("run_freeze_path"), "input_evidence.run_freeze_path")
    require_text(inputs.get("scaling_review_path"), "input_evidence.scaling_review_path")
    require_text(inputs.get("obstacle_scope_path"), "input_evidence.obstacle_scope_path")
    require_text(inputs.get("visual_qa_record_path"), "input_evidence.visual_qa_record_path")
    require(inputs.get("small_gate_status") == "gate_run_completed", "input_evidence.small_gate_status must be gate_run_completed")
    gate = require_positive_int(inputs.get("gate_trajectories_per_release_zone"), "input_evidence.gate_trajectories_per_release_zone")
    proposed = require_positive_int(inputs.get("proposed_trajectories_per_release_zone"), "input_evidence.proposed_trajectories_per_release_zone")
    require(proposed > gate, "proposed_trajectories_per_release_zone must be larger than gate_trajectories_per_release_zone")
    require_positive_int(inputs.get("release_cell_count"), "input_evidence.release_cell_count")
    return {
        "gate_trajectories_per_release_zone": gate,
        "proposed_trajectories_per_release_zone": proposed,
    }


def validate_convergence(convergence: dict[str, Any]) -> dict[str, str]:
    status = require_text(convergence.get("status"), "convergence_assessment.status")
    require(status in STATUSES, f"convergence_assessment.status must be one of {sorted(STATUSES)}")
    require_list(convergence.get("diagnostics_reviewed"), "convergence_assessment.diagnostics_reviewed")
    require_list(convergence.get("missing_diagnostics"), "convergence_assessment.missing_diagnostics")
    require_text(convergence.get("interpretation"), "convergence_assessment.interpretation")
    if status != "pass":
        require(convergence.get("missing_diagnostics"), "non-pass convergence assessment requires missing diagnostics")
    return {"status": status}


def validate_output_budget(output_budget: dict[str, Any]) -> dict[str, str]:
    status = require_text(output_budget.get("status"), "output_budget_assessment.status")
    require(status in STATUSES, f"output_budget_assessment.status must be one of {sorted(STATUSES)}")
    require_positive_int(output_budget.get("gate_output_total_bytes"), "output_budget_assessment.gate_output_total_bytes")
    require_positive_int(output_budget.get("gate_output_file_count"), "output_budget_assessment.gate_output_file_count")
    mode = require_text(output_budget.get("required_curve_export_mode"), "output_budget_assessment.required_curve_export_mode")
    require(mode == "summary-only", "output_budget_assessment.required_curve_export_mode must be summary-only")
    require(output_budget.get("full_curve_table_export_allowed_for_increase") is False, "full curve-table export must not be allowed for ensemble increase")
    require_list(output_budget.get("budget_controls"), "output_budget_assessment.budget_controls")
    require_text(output_budget.get("interpretation"), "output_budget_assessment.interpretation")
    return {"status": status}


def validate_execution_plan(plan: dict[str, Any], decision: str) -> None:
    require(plan.get("generated_outputs_committed") is False, "execution_plan.generated_outputs_committed must be false")
    require(plan.get("changes_physics") is False, "execution_plan.changes_physics must be false")
    require(plan.get("changes_defaults") is False, "execution_plan.changes_defaults must be false")
    require(plan.get("changes_sampling_weights") is False, "execution_plan.changes_sampling_weights must be false")
    command = require_text(plan.get("next_command_when_authorized"), "execution_plan.next_command_when_authorized")
    if decision == "no_go":
        require(plan.get("run_now") is False, "no_go execution_plan.run_now must be false")
    require("--conditional-curve-export summary-only" in command, "next authorized command must use --conditional-curve-export summary-only")
    require("--reducer-workers" in command, "next authorized command must keep deterministic reducer workers explicit")


def validate_claim_boundary(boundary: dict[str, Any]) -> None:
    require(boundary.get("operational_status") == "research_diagnostic", "claim_boundary.operational_status must remain research_diagnostic")
    require(boundary.get("annualized") is False, "claim_boundary.annualized must be false")
    require(boundary.get("physical_probability") is False, "claim_boundary.physical_probability must be false")
    require(boundary.get("risk_or_exposure") is False, "claim_boundary.risk_or_exposure must be false")
    allowed = set(require_list(boundary.get("current_allowed_product_labels"), "claim_boundary.current_allowed_product_labels"))
    require("conditional_intensity_exceedance" in allowed, "current labels must include conditional_intensity_exceedance")
    unsupported = set(require_list(boundary.get("unsupported_current_claims"), "claim_boundary.unsupported_current_claims"))
    required = {"annual_frequency", "return_period", "physical_probability", "risk_map", "operational_hazard_map"}
    missing = sorted(required - unsupported)
    require(not missing, f"claim_boundary.unsupported_current_claims missing: {missing}")


def scan_text_for_misleading_claims(value: Any, *, path: str = "record") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in {"claim_boundary", "unsupported_current_claims"}:
                continue
            scan_text_for_misleading_claims(child, path=f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            scan_text_for_misleading_claims(child, path=f"{path}[{index}]")
    elif isinstance(value, str):
        lower = value.lower()
        if any(marker in lower for marker in ("unsupported", "not ", "no ", "without ", "defer", "future", "out of scope")):
            return
        for pattern in MISLEADING_PATTERNS:
            require(pattern.search(value) is None, f"{path} contains misleading current-product claim: {value!r}")


def read_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - path context matters.
        raise EnsembleFeasibilityError(f"failed to read YAML {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise EnsembleFeasibilityError(f"YAML document must be an object: {path}")
    return data


def require(condition: bool, message: str) -> None:
    if not condition:
        raise EnsembleFeasibilityError(message)


def require_mapping(value: Any, field: str) -> dict[str, Any]:
    require(isinstance(value, dict), f"{field} must be an object")
    return value


def require_list(value: Any, field: str) -> list[Any]:
    require(isinstance(value, list), f"{field} must be a list")
    return value


def require_text(value: Any, field: str) -> str:
    require(isinstance(value, str) and value.strip(), f"{field} must be a nonempty string")
    return value


def require_positive_int(value: Any, field: str) -> int:
    require(isinstance(value, int) and value > 0, f"{field} must be a positive integer")
    return int(value)


if __name__ == "__main__":
    raise SystemExit(main())
