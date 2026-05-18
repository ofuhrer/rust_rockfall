#!/usr/bin/env python3
"""Validate the DT-08 output budget and reducer scaling gate record."""

from __future__ import annotations

import argparse
import json
import re
import sys
from functools import partial
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from lib.workflow_validation import (
    read_yaml as shared_read_yaml,
    render_status_message,
    require as shared_require,
    require_checksum_fields as shared_require_checksum_fields,
    require_false_fields as shared_require_false_fields,
    require_list as shared_require_list,
    require_mapping as shared_require_mapping,
    require_paths_exist as shared_require_paths_exist,
    require_text as shared_require_text,
    scan_text_for_misleading_claims as shared_scan_text_for_misleading_claims,
)

ALLOWED_CLASSIFICATIONS = {
    "passed",
    "diagnostic_incomplete",
    "blocked_before_scale_up",
    "no_go",
}
REQUIRED_REFERENCES = {
    "validation/pilot_runs/tschamut_public_scalable_conditional_target_gate_v1.yaml",
    "validation/pilot_runs/tschamut_public_balfrin_target_gate_reproduction_v1.yaml",
    "validation/pilot_runs/tschamut_public_ensemble_feasibility_v1.yaml",
    "docs/tschamut_public_pilot_scaling_review.md",
    "docs/conditional_hazard_convergence_acceptance_protocol.md",
    "validation/pilot_runs/tschamut_public_conditional_convergence_protocol_v1.yaml",
}
REQUIRED_BLOCKERS = {
    "validation_debug_output_volume_requires_reduction_or_justification",
    "full_curve_csv_scalable_default_not_authorized",
    "grid_csv_scalable_default_not_authorized",
    "reducer_restart_and_merge_state_not_rehearsed_for_larger_scale",
    "dense_grid_accumulator_risk_not_bound",
    "distributed_execution_not_authorized",
}
REQUIRED_FOLLOWUP_CONTROLS = {
    "--conditional-curve-export summary-only",
    "--grid-csv-export none",
    "--no-plots",
}
PROHIBITED_PATTERNS = [
    re.compile(r"\bannual(?:ized)?\s+(?:frequency|probability|rate)\b", re.IGNORECASE),
    re.compile(r"\breturn[- ]?period\b", re.IGNORECASE),
    re.compile(r"\brisk[- ]?map\b", re.IGNORECASE),
    re.compile(r"\boperational(?:ly)?\s+(?:approved|validated|ready|hazard)\b", re.IGNORECASE),
    re.compile(r"\bphysical\s+probability\b", re.IGNORECASE),
    re.compile(r"\btune(?:d|ing)?\b", re.IGNORECASE),
    re.compile(r"\bphysics\s+change\b", re.IGNORECASE),
    re.compile(r"\breducer\s+behavior\s+change\b", re.IGNORECASE),
    re.compile(r"\boutput\s+default\s+change\b", re.IGNORECASE),
    re.compile(r"\bensemble\s+size\s+increase\b", re.IGNORECASE),
]
LEGACY_SUCCESS_MESSAGE = "output/reducer gate record is valid"
# Compatibility note: downstream reports preserve the current_classification and qa_status vocabulary
# (`passed`, `diagnostic_incomplete`, `blocked_before_scale_up`, `no_go`) so existing consumers do not need
# to remap labels during this helper migration.


class OutputBudgetReducerGateError(ValueError):
    """User-facing validation error for DT-08 records."""


require = partial(shared_require, error_cls=OutputBudgetReducerGateError)
require_list = partial(shared_require_list, error_cls=OutputBudgetReducerGateError)
require_mapping = partial(shared_require_mapping, error_cls=OutputBudgetReducerGateError)
require_text = partial(shared_require_text, error_cls=OutputBudgetReducerGateError)
read_yaml = partial(shared_read_yaml, error_cls=OutputBudgetReducerGateError)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", type=Path)
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args(argv)
    try:
        summary = validate_output_budget_reducer_gate(args.record)
    except OutputBudgetReducerGateError as exc:
        print(f"output/reducer gate validation error: {exc}", file=sys.stderr)
        return 2
    if args.format == "json":
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(
            render_status_message(
                "output/reducer gate record",
                args.record,
                summary,
                "current_classification",
                extra_fields=(("qa_status", "qa_status"),),
            )
        )
    return 0


def validate_output_budget_reducer_gate(record_path: Path) -> dict[str, Any]:
    record = read_yaml(record_path)
    require(record.get("schema_version") == "output_budget_reducer_gate_v1", "schema_version must be output_budget_reducer_gate_v1")
    require_text(record.get("record_id"), "record_id")
    require_text(record.get("pilot_id"), "pilot_id")
    require(record.get("roadmap_item") == "DT-08", "roadmap_item must be DT-08")
    assessed = require_mapping(record.get("assessed_domain"), "assessed_domain")
    require_text(assessed.get("name"), "assessed_domain.name")
    require_text(assessed.get("selected_manifest_path"), "assessed_domain.selected_manifest_path")
    require_text(assessed.get("selected_classification"), "assessed_domain.selected_classification")
    require_text(record.get("current_classification"), "current_classification")
    current_classification = record["current_classification"]
    require(current_classification in ALLOWED_CLASSIFICATIONS, f"current_classification must be one of {sorted(ALLOWED_CLASSIFICATIONS)}")
    qa_status = require_text(record.get("qa_status"), "qa_status")
    require(qa_status in {"diagnostic_incomplete", "passed", "blocked_before_scale_up", "no_go"}, "qa_status must be conservative")
    require(record.get("scale_up_authorized") is False, "scale_up_authorized must be false")

    shared_require_false_fields(
        record,
        (
            "physics_changes_claimed",
            "reducer_behavior_changes_claimed",
            "output_default_changes_claimed",
            "ensemble_size_increase_claimed",
            "annual_or_physical_claimed",
            "risk_exposure_or_operational_claimed",
        ),
        OutputBudgetReducerGateError,
        label_prefix="record",
    )

    selected_dt04 = require_mapping(record.get("selected_dt04_output_evidence"), "selected_dt04_output_evidence")
    shared_require_paths_exist(
        {
            "target_gate_record_path": selected_dt04["target_gate_record_path"],
            "balfrin_reproduction_record_path": selected_dt04["balfrin_reproduction_record_path"],
            "ensemble_feasibility_record_path": selected_dt04["ensemble_feasibility_record_path"],
            "scaling_review_doc_path": selected_dt04["scaling_review_doc_path"],
            "selected_manifest_path": assessed["selected_manifest_path"],
        },
        OutputBudgetReducerGateError,
        root=Path(__file__).resolve().parents[1],
        label_prefix="selected_dt04_output_evidence",
    )
    for field in (
        "validation_output_file_count",
        "validation_output_bytes",
        "hazard_output_file_count",
        "hazard_output_bytes",
        "conditional_curve_export_mode",
        "grid_csv_export_mode",
        "reducer_workers",
        "reducer_chunk_count",
        "reducer_merge_order",
        "reducer_parity_status",
        "output_profile_status",
    ):
        require(field in selected_dt04, f"selected_dt04_output_evidence.{field} must be present")
    require(selected_dt04.get("conditional_curve_export_mode") == "summary-only", "selected_dt04_output_evidence.conditional_curve_export_mode must be summary-only")
    require(selected_dt04.get("grid_csv_export_mode") != "full", "selected_dt04_output_evidence.grid_csv_export_mode must not be full")

    output_profile = require_mapping(record.get("output_profile"), "output_profile")
    require_text(output_profile.get("status"), "output_profile.status")
    current_profile = require_mapping(output_profile.get("current_target_gate_profile"), "output_profile.current_target_gate_profile")
    require(current_profile.get("conditional_curve_export_mode") == "summary-only", "current_target_gate_profile.conditional_curve_export_mode must be summary-only")
    require(current_profile.get("grid_csv_export_mode") != "full", "current_target_gate_profile.grid_csv_export_mode must not be full")
    selected_followup = require_mapping(output_profile.get("selected_followup_profile"), "output_profile.selected_followup_profile")
    require_text(selected_followup.get("profile"), "output_profile.selected_followup_profile.profile")
    required_controls = require_list(selected_followup.get("required_controls"), "output_profile.selected_followup_profile.required_controls")
    required_controls_values = [require_text(control, f"output_profile.selected_followup_profile.required_controls[{index}]") for index, control in enumerate(required_controls)]
    missing_controls = sorted(REQUIRED_FOLLOWUP_CONTROLS - set(required_controls_values))
    require(not missing_controls, f"output_profile.selected_followup_profile.required_controls missing: {missing_controls}")
    debug_budget = require_mapping(output_profile.get("validation_debug_output_budget"), "output_profile.validation_debug_output_budget")
    require(debug_budget.get("status") == "blocker_retained", "output_profile.validation_debug_output_budget.status must be blocker_retained")
    require(debug_budget.get("acceptable_for_next_scale_increase_without_reduction_or_justification") is False, "validation_debug_output_budget must block next scale increase")

    validation_budget = validate_budget_block(require_mapping(record.get("validation_output_budget"), "validation_output_budget"), "validation_output_budget")
    hazard_budget = validate_budget_block(require_mapping(record.get("hazard_output_budget"), "hazard_output_budget"), "hazard_output_budget")
    reducer_scaling = require_mapping(record.get("reducer_scaling"), "reducer_scaling")
    require_text(reducer_scaling.get("status"), "reducer_scaling.status")
    require(reducer_scaling.get("mode") == "chunked_local_threads", "reducer_scaling.mode must be chunked_local_threads")
    worker_counts = require_list(reducer_scaling.get("worker_counts_compared"), "reducer_scaling.worker_counts_compared")
    worker_counts_values = [require_text(str(count), f"reducer_scaling.worker_counts_compared[{index}]") for index, count in enumerate(worker_counts)]
    require(set(worker_counts_values) == {"1", "2"}, "reducer_scaling.worker_counts_compared must compare 1 and 2")
    require(reducer_scaling.get("parity_status") == "pass_for_hazard_reducer_outputs", "reducer_scaling.parity_status must record reducer parity")
    require_text(reducer_scaling.get("merge_order"), "reducer_scaling.merge_order")
    require(reducer_scaling.get("chunk_count") == 2, "reducer_scaling.chunk_count must be 2")
    require(reducer_scaling.get("chunk_manifest_count") == 2, "reducer_scaling.chunk_manifest_count must be 2")
    require_text(reducer_scaling.get("local_restartability_status"), "reducer_scaling.local_restartability_status")
    for field in (
        "reducer_chunk_manifest_status",
        "reducer_execution_index_status",
        "reducer_merge_state_status",
    ):
        require_text(reducer_scaling.get(field), f"reducer_scaling.{field}")

    dense_grid_risk = require_mapping(record.get("dense_grid_risk"), "dense_grid_risk")
    require_text(dense_grid_risk.get("status"), "dense_grid_risk.status")
    require_text(dense_grid_risk.get("classification"), "dense_grid_risk.classification")

    checksum_evidence = require_mapping(record.get("checksum_evidence"), "checksum_evidence")
    require_text(checksum_evidence.get("status"), "checksum_evidence.status")
    shared_require_checksum_fields(
        checksum_evidence,
        ("validation_manifest_sha256", "hazard_manifest_sha256"),
        OutputBudgetReducerGateError,
        label_prefix="checksum_evidence",
    )

    references = require_list(record.get("referenced_records"), "referenced_records")
    reference_values = [require_text(reference, f"referenced_records[{index}]") for index, reference in enumerate(references)]
    missing_refs = sorted(REQUIRED_REFERENCES - set(reference_values))
    require(not missing_refs, f"referenced_records missing: {missing_refs}")

    blockers = require_list(record.get("required_blockers"), "required_blockers")
    blocker_values = [require_text(blocker, f"required_blockers[{index}]") for index, blocker in enumerate(blockers)]
    blocker_set = set(blocker_values)
    if current_classification != "passed":
        missing_blockers = sorted(REQUIRED_BLOCKERS - blocker_set)
        require(not missing_blockers, f"required_blockers missing: {missing_blockers}")
        require(blockers, "non-passed records must keep blockers visible")
        limitations = require_list(record.get("limitations"), "limitations")
        require(limitations, "non-passed records must keep limitations visible")
        required_future_evidence = require_list(record.get("required_future_evidence"), "required_future_evidence")
        require(required_future_evidence, "non-passed records must keep future evidence visible")
    else:
        require(not blockers, "passed records must not retain blockers")
        limitations = require_list(record.get("limitations", []), "limitations")
        require(not limitations, "passed records must not retain limitations")
        required_future_evidence = require_list(record.get("required_future_evidence", []), "required_future_evidence")
        require(not required_future_evidence, "passed records must not retain future evidence items")
        require(validation_budget.get("status") == "complete", "passed records require validation_output_budget.status = complete")
        require(hazard_budget.get("status") == "complete", "passed records require hazard_output_budget.status = complete")
        require(reducer_scaling.get("status") == "complete", "passed records require reducer_scaling.status = complete")
        require(dense_grid_risk.get("status") == "complete", "passed records require dense_grid_risk.status = complete")
        require(checksum_evidence.get("status") == "complete", "passed records require checksum_evidence.status = complete")

    claim_boundary = require_mapping(record.get("claim_boundary"), "claim_boundary")
    validate_claim_boundary(claim_boundary)

    scan_text_for_prohibited_claims(record)
    return {
        "schema_version": record["schema_version"],
        "record_id": record["record_id"],
        "current_classification": current_classification,
        "qa_status": qa_status,
    }


def validate_budget_block(section: dict[str, Any], field: str) -> dict[str, Any]:
    require_text(section.get("status"), f"{field}.status")
    require("file_count" in section, f"{field}.file_count must be present")
    require("bytes" in section, f"{field}.bytes must be present")
    return section


def validate_claim_boundary(boundary: dict[str, Any]) -> None:
    shared_require_false_fields(
        boundary,
        (
            "physics_changes_claimed",
            "reducer_behavior_changes_claimed",
            "output_default_changes_claimed",
            "ensemble_size_increase_claimed",
            "distributed_execution_claimed",
            "annual_or_physical_claimed",
            "risk_exposure_or_operational_claimed",
            "return_period_claimed",
            "validated_hazard_map_claimed",
            "full_curve_csv_default_claimed",
            "grid_csv_default_claimed",
        ),
        OutputBudgetReducerGateError,
        label_prefix="claim_boundary",
    )
    shared_scan_text_for_misleading_claims(
        boundary,
        require_fn=require,
        patterns=PROHIBITED_PATTERNS,
        skip_keys=(),
        allow_markers=(),
    )


def scan_text_for_prohibited_claims(value: Any, *, path: str = "record") -> None:
    shared_scan_text_for_misleading_claims(
        value,
        require_fn=require,
        patterns=PROHIBITED_PATTERNS,
        path=path,
    )


if __name__ == "__main__":
    raise SystemExit(main())
