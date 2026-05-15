#!/usr/bin/env python3
"""Summarize the measured acceptance state for the selected Tschamut pilot.

This generator reads the existing Balfrin, convergence, target-gate, and
output-budget evidence records and derives a conservative acceptance summary.
It does not change physics, defaults, thresholds, release assumptions, or
validation baselines.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TARGET_GATE_RECORD = ROOT / "validation/pilot_runs/tschamut_public_scalable_conditional_target_gate_v1.yaml"
DEFAULT_BALFRIN_RECORD = ROOT / "validation/pilot_runs/tschamut_public_balfrin_target_gate_reproduction_v1.yaml"
DEFAULT_CONVERGENCE_RECORD = ROOT / "validation/pilot_runs/tschamut_public_conditional_convergence_protocol_v1.yaml"
DEFAULT_OUTPUT_BUDGET_RECORD = ROOT / "validation/pilot_runs/tschamut_public_output_budget_reducer_gate_v1.yaml"

SUMMARY_SCHEMA_VERSION = "tschamut_conditional_pilot_acceptance_summary_v1"


class ConditionalPilotAcceptanceSummaryError(ValueError):
    """User-facing error raised when the summary cannot be derived."""


def _load_module(module_name: str, filename: str):
    path = ROOT / "scripts" / filename
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ConditionalPilotAcceptanceSummaryError(f"failed to load helper module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


TARGET_GATE_VALIDATOR = _load_module("validate_scalable_conditional_target_gate", "validate_scalable_conditional_target_gate.py")
BALFRIN_VALIDATOR = _load_module("validate_balfrin_target_gate_reproduction", "validate_balfrin_target_gate_reproduction.py")
CONVERGENCE_VALIDATOR = _load_module("validate_conditional_convergence_protocol", "validate_conditional_convergence_protocol.py")
OUTPUT_BUDGET_VALIDATOR = _load_module("validate_output_budget_reducer_gate", "validate_output_budget_reducer_gate.py")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-gate-record", type=Path, default=DEFAULT_TARGET_GATE_RECORD)
    parser.add_argument("--balfrin-record", type=Path, default=DEFAULT_BALFRIN_RECORD)
    parser.add_argument("--convergence-record", type=Path, default=DEFAULT_CONVERGENCE_RECORD)
    parser.add_argument("--output-budget-record", type=Path, default=DEFAULT_OUTPUT_BUDGET_RECORD)
    parser.add_argument("--markdown-output", type=Path, default=None)
    parser.add_argument("--json-output", type=Path, default=None)
    parser.add_argument("--format", choices=["text", "markdown", "json"], default="text")
    args = parser.parse_args(argv)

    try:
        summary = build_acceptance_summary(
            target_gate_record=args.target_gate_record,
            balfrin_record=args.balfrin_record,
            convergence_record=args.convergence_record,
            output_budget_record=args.output_budget_record,
        )
    except ConditionalPilotAcceptanceSummaryError as exc:
        print(f"conditional pilot acceptance summary error: {exc}", file=sys.stderr)
        return 2

    if args.json_output is not None:
        args.json_output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.markdown_output is not None:
        args.markdown_output.write_text(render_markdown_report(summary), encoding="utf-8")

    if args.format == "json":
        print(json.dumps(summary, indent=2, sort_keys=True))
    elif args.format == "markdown":
        print(render_markdown_report(summary), end="")
    else:
        print(
            "conditional pilot acceptance summary: "
            f"{summary['final_classification']} "
            f"(scale_up_authorized={summary['scale_up_authorized']}, "
            f"convergence={summary['convergence_status']}, "
            f"output_budget={summary['output_budget_status']})"
        )
    return 0


def build_acceptance_summary(
    *,
    target_gate_record: Path = DEFAULT_TARGET_GATE_RECORD,
    balfrin_record: Path = DEFAULT_BALFRIN_RECORD,
    convergence_record: Path = DEFAULT_CONVERGENCE_RECORD,
    output_budget_record: Path = DEFAULT_OUTPUT_BUDGET_RECORD,
) -> dict[str, Any]:
    target_gate_path = require_existing_path(target_gate_record, "target_gate_record")
    balfrin_path = require_existing_path(balfrin_record, "balfrin_record")
    convergence_path = require_existing_path(convergence_record, "convergence_record")
    output_budget_path = require_existing_path(output_budget_record, "output_budget_record")

    target_gate_summary = call_validator(
        TARGET_GATE_VALIDATOR.validate_target_gate_record,
        target_gate_path,
        "target_gate_record",
    )
    balfrin_summary = call_validator(
        BALFRIN_VALIDATOR.validate_target_gate_reproduction_record,
        balfrin_path,
        "balfrin_record",
    )
    convergence_summary = call_validator(
        CONVERGENCE_VALIDATOR.validate_protocol_record,
        convergence_path,
        "convergence_record",
    )
    output_budget_summary = call_validator(
        OUTPUT_BUDGET_VALIDATOR.validate_output_budget_reducer_gate,
        output_budget_path,
        "output_budget_record",
    )

    target_gate = read_yaml(target_gate_path)
    balfrin = read_yaml(balfrin_path)
    convergence = read_yaml(convergence_path)
    output_budget = read_yaml(output_budget_path)

    final_classification = classify_final_state(
        target_gate_status=target_gate_summary["gate_status"],
        balfrin_classification=balfrin_summary["reproducibility_classification"],
        convergence_classification=convergence_summary["current_classification"],
        output_budget_classification=output_budget_summary["current_classification"],
        output_budget_gate_status=output_budget.get("current_classification", ""),
    )

    blocker_status = "present" if final_classification != "accepted_conditional_diagnostic_pilot" else "resolved"
    scale_up_authorized = bool(convergence["assessment"]["scale_up_authorized"])
    return {
        "schema_version": SUMMARY_SCHEMA_VERSION,
        "pilot_id": target_gate.get("pilot_id", "tschamut_public_pilot"),
        "target_gate_record": display_path(target_gate_path),
        "balfrin_record": display_path(balfrin_path),
        "convergence_record": display_path(convergence_path),
        "output_budget_record": display_path(output_budget_path),
        "target_gate_status": target_gate_summary["gate_status"],
        "balfrin_reproducibility_classification": balfrin_summary["reproducibility_classification"],
        "convergence_status": convergence_summary["current_classification"],
        "convergence_scale_up_authorized": convergence_summary["scale_up_authorized"],
        "output_budget_status": output_budget_summary["current_classification"],
        "output_budget_qa_status": output_budget_summary["qa_status"],
        "validation_debug_output_status": output_budget["output_profile"]["validation_debug_output_budget"]["status"],
        "blocker_status": blocker_status,
        "scale_up_authorized": scale_up_authorized,
        "accepted_conditional_diagnostic_pilot": final_classification == "accepted_conditional_diagnostic_pilot",
        "final_classification": final_classification,
        "classification_rationale": derive_classification_rationale(
            final_classification=final_classification,
            convergence_status=convergence_summary["current_classification"],
            output_budget_status=output_budget_summary["current_classification"],
            validation_debug_output_status=output_budget["output_profile"]["validation_debug_output_budget"]["status"],
        ),
        "measured_evidence": {
            "target_gate": {
                "gate_status": target_gate_summary["gate_status"],
                "release_cell_count": target_gate["target_execution_plan"]["release_cell_count"],
                "target_trajectories_per_release_zone": target_gate["target_execution_plan"]["target_trajectories_per_release_zone"],
                "validation_output_file_count": target_gate["execution_evidence"]["validation_run"]["output_file_count"],
                "validation_output_bytes": target_gate["execution_evidence"]["validation_run"]["output_total_bytes"],
                "hazard_output_file_count": target_gate["execution_evidence"]["hazard_run"]["output_file_count"],
                "hazard_output_bytes": target_gate["execution_evidence"]["hazard_run"]["output_total_bytes"],
            },
            "balfrin": {
                "reproducibility_classification": balfrin_summary["reproducibility_classification"],
                "simulated_trajectory_count": balfrin["physics_and_sampling"]["simulated_trajectory_count"],
                "validation_output_file_count": balfrin["performance"]["validation_output_file_count"],
                "validation_output_bytes": balfrin["performance"]["validation_output_bytes"],
                "hazard_output_file_count": balfrin["performance"]["hazard_output_file_count"],
                "hazard_output_bytes": balfrin["performance"]["hazard_output_bytes"],
            },
            "convergence": {
                "current_classification": convergence_summary["current_classification"],
                "scale_up_authorized": convergence_summary["scale_up_authorized"],
                "blocking_reasons": convergence["assessment"]["blocking_reasons"],
                "convergence_indicators": convergence["assessment"]["evidence"]["convergence_indicators"],
            },
            "output_budget": {
                "current_classification": output_budget_summary["current_classification"],
                "qa_status": output_budget_summary["qa_status"],
                "validation_output_file_count": output_budget["validation_output_budget"]["file_count"],
                "validation_output_bytes": output_budget["validation_output_budget"]["bytes"],
                "hazard_output_file_count": output_budget["hazard_output_budget"]["file_count"],
                "hazard_output_bytes": output_budget["hazard_output_budget"]["bytes"],
                "validation_debug_output_budget_status": output_budget["output_profile"]["validation_debug_output_budget"]["status"],
            },
        },
        "uncertainty_reduced": [
            "target_run_provenance is fixed across the selected gate and the Balfrin reproduction",
            "frozen inputs and deterministic seed-order-chunk metadata are recorded in the convergence protocol",
            "1-worker and 2-worker reducer outputs matched for deposition points and hazard layers",
            "summary-only conditional curves and grid-CSV suppression are recorded for the target gate",
            "checksum provenance is recorded for the validation, hazard, map-package, and pilot-GIS artifacts",
            "validation-side and hazard-side output volumes are measured for the selected gate",
        ],
        "remaining_unresolved": [
            "conditional hazard-map convergence has not been accepted",
            "manual GIS/QGIS visual QA remains secondary and was not run here",
            "forest and obstacle context remains limiting",
            "validation debug-output volume remains a blocker for larger scale-up",
        ],
        "evidence_records_read": [
            display_path(target_gate_path),
            display_path(balfrin_path),
            display_path(convergence_path),
            display_path(output_budget_path),
        ],
        "reference_documents": [
            "docs/conditional_hazard_convergence_acceptance_protocol.md",
            "docs/output_budget_reducer_scaling_gate.md",
            "docs/tschamut_public_scalable_conditional_target_gate.md",
        ],
    }


def classify_final_state(
    *,
    target_gate_status: str,
    balfrin_classification: str,
    convergence_classification: str,
    output_budget_classification: str,
    output_budget_gate_status: str,
) -> str:
    if any(
        status in {"no_go", "failed", "blocked_missing_inputs"}
        for status in (
            target_gate_status,
            balfrin_classification,
            convergence_classification,
            output_budget_classification,
            output_budget_gate_status,
        )
    ):
        return "no_go"
    if (
        target_gate_status in {"target_scale_executed", "inconclusive"}
        and balfrin_classification == "passed"
        and convergence_classification == "pass"
        and output_budget_classification == "passed"
        and output_budget_gate_status == "passed"
    ):
        return "accepted_conditional_diagnostic_pilot"
    return "inconclusive"


def derive_classification_rationale(
    *,
    final_classification: str,
    convergence_status: str,
    output_budget_status: str,
    validation_debug_output_status: str,
) -> str:
    if final_classification == "accepted_conditional_diagnostic_pilot":
        return (
            "The selected conditional pilot would be accepted because convergence "
            "and output-budget evidence are both passed and the remaining blocker "
            "status is resolved."
        )
    if final_classification == "no_go":
        return (
            "The record is not suitable for a defensible conditional assessment "
            "because required evidence is missing, contradictory, or marked no_go."
        )
    return (
        "The workflow completed and the evidence is usable, but conditional "
        f"convergence remains {convergence_status}, the output budget remains "
        f"{output_budget_status}, and the validation debug-output volume remains "
        f"a blocker with status {validation_debug_output_status}."
    )


def render_markdown_report(summary: dict[str, Any]) -> str:
    lines = [
        "# Measured Conditional Pilot Acceptance Summary",
        "",
        f"Status: {summary['final_classification']}",
        "",
        "## Result",
        "",
        f"- Pilot: `{summary['pilot_id']}`",
        f"- Final classification: `{summary['final_classification']}`",
        f"- Scale-up authorized: `{str(summary['scale_up_authorized']).lower()}`",
        f"- Convergence status: `{summary['convergence_status']}`",
        f"- Output-budget status: `{summary['output_budget_status']}`",
        f"- Blocker status: `{summary['blocker_status']}`",
        "",
        "## Measured Evidence",
        "",
    ]

    for section_name, section in summary["measured_evidence"].items():
        lines.append(f"### {section_name.replace('_', ' ').title()}")
        for key, value in section.items():
            lines.append(f"- {key}: `{value}`")
        lines.append("")

    lines.extend(
        [
            "## Uncertainty Reduced",
            "",
        ]
    )
    for item in summary["uncertainty_reduced"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Remaining Unresolved",
            "",
        ]
    )
    for item in summary["remaining_unresolved"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Evidence Records Read",
            "",
        ]
    )
    for item in summary["evidence_records_read"]:
        lines.append(f"- `{item}`")
    lines.extend(
        [
            "",
            "## Reference Documents",
            "",
        ]
    )
    for item in summary["reference_documents"]:
        lines.append(f"- `{item}`")
    lines.extend(
        [
            "",
            "## Classification Rationale",
            "",
            summary["classification_rationale"],
            "",
        ]
    )
    return "\n".join(lines)


def read_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - path context matters.
        raise ConditionalPilotAcceptanceSummaryError(f"failed to read YAML {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ConditionalPilotAcceptanceSummaryError(f"YAML document must be an object: {path}")
    return data


def call_validator(func, path: Path, field: str) -> dict[str, Any]:
    try:
        return func(path)
    except Exception as exc:  # noqa: BLE001 - wrap helper failures with field context.
        raise ConditionalPilotAcceptanceSummaryError(f"{field}: {exc}") from exc


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def require_existing_path(path: Path, field: str) -> Path:
    if not path.exists():
        raise ConditionalPilotAcceptanceSummaryError(f"{field} does not exist: {path}")
    return path


if __name__ == "__main__":
    raise SystemExit(main())
