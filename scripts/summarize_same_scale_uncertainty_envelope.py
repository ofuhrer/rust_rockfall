#!/usr/bin/env python3
"""Summarize the same-scale uncertainty envelope for the selected Tschamut pilot.

This generator composes existing measured diagnostics for convergence,
validation-output pressure, context relevance, and Balfrin execution
sufficiency. It does not change physics, defaults, thresholds, release
assumptions, or validation baselines.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPORT_SCHEMA_VERSION = "tschamut_same_scale_uncertainty_envelope_v1"

DEFAULT_ACCEPTANCE_RECORD = ROOT / "validation/pilot_runs/tschamut_public_conditional_convergence_protocol_v1.yaml"
DEFAULT_BOUNDED_OUTPUT_RECORD = ROOT / "docs/tschamut_public_bounded_validation_output_profile.md"
DEFAULT_BOUNDED_BASELINE_MANIFEST = ROOT / "tests/fixtures/bounded_validation_output_profile/baseline_manifest.json"
DEFAULT_BOUNDED_REDUCED_MANIFEST = ROOT / "tests/fixtures/bounded_validation_output_profile/reduced_manifest.json"
DEFAULT_BALFRIN_SUFICIENCY_RECORD = ROOT / "docs/balfrin_single_job_execution_sufficiency.md"
DEFAULT_CONTEXT_SCOPE_RECORD = ROOT / "validation/pilot_runs/tschamut_public_obstacle_scope_v1.yaml"
DEFAULT_CONDITIONAL_GATE_REPORT = ROOT / "docs/tschamut_public_conditional_pilot_gate_report.md"
DEFAULT_GATE_MANIFEST = ROOT / "hazard/results/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_manifest.json"
DEFAULT_TARGET_VALIDATION_MANIFEST = ROOT / "validation/private/tschamut_public_pilot/target_gate_v1/validation_tschamut_public_target_gate_v1_manifest.json"
DEFAULT_TARGET_HAZARD_MANIFEST = ROOT / "hazard/results/tschamut_public_pilot/target_gate_v1/validation_tschamut_public_target_gate_v1_manifest.json"
DEFAULT_CONTEXT_ROOT = ROOT / "data/processed/swisstopo/tschamut_public_pilot/context"


class SameScaleUncertaintyEnvelopeError(ValueError):
    """User-facing same-scale uncertainty envelope error."""


def _load_module(module_name: str, filename: str):
    path = ROOT / "scripts" / filename
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise SameScaleUncertaintyEnvelopeError(f"failed to load helper module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


ACCEPTANCE = _load_module("summarize_conditional_pilot_acceptance", "summarize_conditional_pilot_acceptance.py")
BOUNDED = _load_module("summarize_bounded_validation_output_profile", "summarize_bounded_validation_output_profile.py")
SINGLE_JOB = _load_module("summarize_balfrin_single_job_execution", "summarize_balfrin_single_job_execution.py")
CONTEXT = _load_module("inspect_tschamut_public_context_layers", "inspect_tschamut_public_context_layers.py")
CONVERGENCE = _load_module("compare_hazard_map_convergence", "compare_hazard_map_convergence.py")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--acceptance-record", type=Path, default=DEFAULT_ACCEPTANCE_RECORD)
    parser.add_argument("--bounded-output-record", type=Path, default=DEFAULT_BOUNDED_OUTPUT_RECORD)
    parser.add_argument("--single-job-record", type=Path, default=DEFAULT_BALFRIN_SUFICIENCY_RECORD)
    parser.add_argument("--context-scope-record", type=Path, default=DEFAULT_CONTEXT_SCOPE_RECORD)
    parser.add_argument("--conditional-gate-report", type=Path, default=DEFAULT_CONDITIONAL_GATE_REPORT)
    parser.add_argument("--context-root", type=Path, default=DEFAULT_CONTEXT_ROOT)
    parser.add_argument("--gate-manifest", type=Path, default=DEFAULT_GATE_MANIFEST)
    parser.add_argument("--target-validation-manifest", type=Path, default=DEFAULT_TARGET_VALIDATION_MANIFEST)
    parser.add_argument("--target-hazard-manifest", type=Path, default=DEFAULT_TARGET_HAZARD_MANIFEST)
    parser.add_argument("--json-output", type=Path, default=None)
    parser.add_argument("--markdown-output", type=Path, default=None)
    parser.add_argument("--format", choices=("text", "markdown", "json"), default="text")
    args = parser.parse_args(argv)

    try:
        report = build_uncertainty_envelope(
            acceptance_record=args.acceptance_record,
            bounded_output_record=args.bounded_output_record,
            single_job_record=args.single_job_record,
            context_scope_record=args.context_scope_record,
            conditional_gate_report=args.conditional_gate_report,
            context_root=args.context_root,
            gate_manifest=args.gate_manifest,
            target_validation_manifest=args.target_validation_manifest,
            target_hazard_manifest=args.target_hazard_manifest,
        )
    except SameScaleUncertaintyEnvelopeError as exc:
        print(f"same-scale uncertainty envelope error: {exc}", file=sys.stderr)
        return 2

    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.markdown_output is not None:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(render_markdown_report(report), encoding="utf-8")

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    elif args.format == "markdown":
        print(render_markdown_report(report), end="")
    else:
        print(
            "same-scale uncertainty envelope: "
            f"{report['final_classification']} "
            f"(convergence={report['convergence_status']}, "
            f"validation_output={report['validation_output_status']}, "
            f"context={report['context_status']}, "
            f"execution_sufficiency={report['execution_sufficiency_status']})"
        )
    return 0


def build_uncertainty_envelope(
    *,
    acceptance_record: Path = DEFAULT_ACCEPTANCE_RECORD,
    bounded_output_record: Path = DEFAULT_BOUNDED_OUTPUT_RECORD,
    single_job_record: Path = DEFAULT_BALFRIN_SUFICIENCY_RECORD,
    context_scope_record: Path = DEFAULT_CONTEXT_SCOPE_RECORD,
    conditional_gate_report: Path = DEFAULT_CONDITIONAL_GATE_REPORT,
    context_root: Path = DEFAULT_CONTEXT_ROOT,
    gate_manifest: Path = DEFAULT_GATE_MANIFEST,
    target_validation_manifest: Path = DEFAULT_TARGET_VALIDATION_MANIFEST,
    target_hazard_manifest: Path = DEFAULT_TARGET_HAZARD_MANIFEST,
) -> dict[str, Any]:
    acceptance_summary = ACCEPTANCE.build_acceptance_summary(
        convergence_record=acceptance_record,
    )
    bounded_summary = load_bounded_output_summary(
        bounded_output_record=bounded_output_record,
    )
    single_job_summary = SINGLE_JOB.build_summary()
    context_summary = CONTEXT.inspect_context_layers(
        scope_record_path=context_scope_record,
        datasets_registry_path=ROOT / "data/datasets.yaml",
        context_root=context_root,
    )
    convergence_summary = build_convergence_summary(
        gate_manifest=gate_manifest,
        target_validation_manifest=target_validation_manifest,
        target_hazard_manifest=target_hazard_manifest,
    )

    envelope_status = classify_envelope_status(
        convergence_status=convergence_summary["convergence_status"],
        target_artifact_restore_status=convergence_summary["target_artifact_restore_status"],
        validation_output_status=bounded_summary["validation_output_blocker_status"],
        validation_output_reduced=bounded_summary["validation_output_reduced"],
        context_status=context_summary["classification"],
        context_review_status=context_summary["context_review_status"],
        swisstlm3d_archive_status=context_summary["swisstlm3d_archive_status"],
        execution_sufficiency_status=single_job_summary["final_classification"],
        single_job_sufficient_for_next_step=single_job_summary["single_job_sufficient_for_next_step"],
        distributed_execution_authorized=single_job_summary["distributed_execution_authorized"],
        artifact_readiness_status=convergence_summary["artifact_readiness_status"],
        validation_output_mode_context=bounded_summary["validation_output_comparison"].get("validation_output_mode"),
    )

    missing_or_pending_inputs = collect_missing_or_pending_inputs(
        convergence_summary=convergence_summary,
        bounded_summary=bounded_summary,
        single_job_summary=single_job_summary,
        context_summary=context_summary,
    )

    report = {
        "report_schema_version": REPORT_SCHEMA_VERSION,
        "pilot_id": acceptance_summary["pilot_id"],
        "final_classification": envelope_status["final_classification"],
        "uncertainty_envelope_status": envelope_status["uncertainty_envelope_status"],
        "convergence_status": convergence_summary["convergence_status"],
        "target_artifact_restore_status": convergence_summary["target_artifact_restore_status"],
        "gate_manifest_available": convergence_summary["gate_manifest_available"],
        "target_validation_manifest_available": convergence_summary["target_validation_manifest_available"],
        "target_hazard_manifest_available": convergence_summary["target_hazard_manifest_available"],
        "target_cellwise_layers_available": convergence_summary["target_cellwise_layers_available"],
        "tb014_ready": convergence_summary["tb014_ready"],
        "convergence_evidence": convergence_summary,
        "validation_output_status": bounded_summary["validation_output_blocker_status"],
        "validation_output_mode_context": bounded_summary["validation_output_comparison"].get("validation_output_mode"),
        "validation_output_evidence": bounded_summary,
        "context_status": context_summary["classification"],
        "context_evidence": context_summary,
        "execution_sufficiency_status": single_job_summary["final_classification"],
        "execution_sufficiency_evidence": single_job_summary,
        "artifact_readiness_status": convergence_summary["artifact_readiness_status"],
        "missing_or_pending_inputs": missing_or_pending_inputs,
        "limiting_factors": envelope_status["limiting_factors"],
        "uncertainty_reduced": envelope_status["uncertainty_reduced"],
        "remaining_uncertainty": envelope_status["remaining_uncertainty"],
        "scale_up_authorized": False,
        "operational_claims_allowed": False,
    }
    return report


def load_bounded_output_summary(*, bounded_output_record: Path) -> dict[str, Any]:
    if bounded_output_record.exists() and bounded_output_record.suffix.lower() == ".md":
        parsed = parse_bounded_output_markdown(bounded_output_record.read_text(encoding="utf-8"))
        if parsed is not None:
            return parsed

    return BOUNDED.build_summary(
        validation_output_baseline_manifest_path=DEFAULT_BOUNDED_BASELINE_MANIFEST,
        validation_output_reduced_manifest_path=DEFAULT_BOUNDED_REDUCED_MANIFEST,
    )


def build_convergence_summary(
    *,
    gate_manifest: Path,
    target_validation_manifest: Path,
    target_hazard_manifest: Path,
) -> dict[str, Any]:
    gate_exists = gate_manifest.exists()
    target_validation_exists = target_validation_manifest.exists()
    target_hazard_exists = target_hazard_manifest.exists()
    target_cellwise_layers_available = False
    compare_result: dict[str, Any] | None = None

    if target_hazard_exists:
        target_hazard_manifest_data = load_json_manifest(target_hazard_manifest)
        target_cellwise_layers_available = bool(target_hazard_manifest_data.get("cellwise_layers"))

    if gate_exists and target_validation_exists and target_hazard_exists and target_cellwise_layers_available:
        compare_result = CONVERGENCE.compare_hazard_map_convergence([gate_manifest, target_hazard_manifest])
        if compare_result.get("status") == CONVERGENCE.OK_STATUS:
            comparisons = compare_result.get("comparisons", [])
            return {
                "convergence_status": "measured",
                "artifact_readiness_status": "ready",
                "target_artifact_restore_status": "ready",
                "gate_manifest_available": gate_exists,
                "target_validation_manifest_available": target_validation_exists,
                "target_hazard_manifest_available": target_hazard_exists,
                "target_cellwise_layers_available": target_cellwise_layers_available,
                "tb014_ready": True,
                "compared_artifacts": [str(gate_manifest), str(target_hazard_manifest)],
                "per_layer_metrics": build_per_layer_metrics(comparisons),
                "strongest_disagreement_layers": strongest_disagreement_layers(comparisons),
                "overall_metrics": compare_result.get("overall_metrics", {}),
                "missing_inputs": [],
                "compare_result": compare_result,
            }

    missing_inputs = []
    if not gate_exists:
        missing_inputs.append(
            {
                "category": "convergence",
                "requested_path": str(gate_manifest),
                "status": "blocked_missing_inputs",
                "reason": f"pending gate-side same-scale hazard manifest at {gate_manifest}",
            }
        )
    if not target_validation_exists:
        missing_inputs.append(
            {
                "category": "convergence",
                "requested_path": str(target_validation_manifest),
                "status": "blocked_missing_inputs",
                "reason": f"pending target-side same-scale validation manifest at {target_validation_manifest}",
            }
        )
    if not target_hazard_exists:
        missing_inputs.append(
            {
                "category": "convergence",
                "requested_path": str(target_hazard_manifest),
                "status": "blocked_missing_inputs",
                "reason": f"pending target-side same-scale hazard manifest at {target_hazard_manifest}",
            }
        )
    if target_hazard_exists and not target_cellwise_layers_available:
        missing_inputs.append(
            {
                "category": "convergence",
                "requested_path": str(target_hazard_manifest),
                "status": "blocked_missing_inputs",
                "reason": "target hazard manifest does not expose cellwise_layers for cell-wise comparison",
            }
        )

    return {
        "convergence_status": "blocked_missing_target_artifacts",
        "artifact_readiness_status": "blocked_missing_target_artifacts",
        "target_artifact_restore_status": "blocked_missing_inputs",
        "gate_manifest_available": gate_exists,
        "target_validation_manifest_available": target_validation_exists,
        "target_hazard_manifest_available": target_hazard_exists,
        "target_cellwise_layers_available": target_cellwise_layers_available,
        "tb014_ready": False,
        "compared_artifacts": [str(gate_manifest), str(target_hazard_manifest)],
        "per_layer_metrics": [],
        "strongest_disagreement_layers": [],
        "overall_metrics": (compare_result or {}).get("overall_metrics", {}),
        "missing_inputs": missing_inputs,
        "compare_result": compare_result or {
            "status": "blocked_missing_target_artifacts",
            "missing_inputs": missing_inputs,
            "compared_artifacts": [str(gate_manifest), str(target_hazard_manifest)],
        },
    }


def classify_envelope_status(
    *,
    convergence_status: str,
    target_artifact_restore_status: str,
    validation_output_status: str,
    validation_output_reduced: bool,
    context_status: str,
    context_review_status: str,
    swisstlm3d_archive_status: str,
    execution_sufficiency_status: str,
    single_job_sufficient_for_next_step: bool,
    distributed_execution_authorized: bool,
    artifact_readiness_status: str,
    validation_output_mode_context: str | None,
) -> dict[str, Any]:
    limiting_factors = []
    uncertainty_reduced = []
    remaining_uncertainty = []

    if convergence_status == "measured":
        uncertainty_reduced.append("target_vs_gate convergence metrics are measured at cell-wise granularity")
    else:
        limiting_factors.append("target_vs_gate_convergence_pending")
        if convergence_status == "blocked_missing_target_artifacts":
            remaining_uncertainty.append("target-side same-scale artifacts are pending or blocked, so convergence remains unmeasured")
        else:
            remaining_uncertainty.append("same-scale convergence is not yet measured or accepted")

    if validation_output_reduced:
        uncertainty_reduced.append(
            f"validation output reduction is measured with mode={validation_output_mode_context or 'unknown'}"
        )
    if validation_output_status in {"no_go", "blocked_before_scale_up", "blocker_retained"}:
        limiting_factors.append("validation_output_pressure_retained")
        remaining_uncertainty.append("validation debug-output pressure is still a scale-up blocker")

    if context_review_status == "reviewed_local_context":
        uncertainty_reduced.append("real local context evidence is reviewed and no longer a missing-cache problem")
    if context_status == "limiting":
        limiting_factors.append("context_is_limiting")
        remaining_uncertainty.append("corridor-level context remains interpretive evidence, not obstacle physics")

    if single_job_sufficient_for_next_step:
        uncertainty_reduced.append("single-job execution sufficiency is recorded")
    if execution_sufficiency_status in {"defer", "blocked_pending_evidence"} or not distributed_execution_authorized:
        limiting_factors.append("single_job_path_deferred")
        remaining_uncertainty.append("distributed execution remains deferred on measured evidence")

    if target_artifact_restore_status != "ready":
        limiting_factors.append("target_artifact_readiness_pending")
        remaining_uncertainty.append("target-side same-scale hazard artifacts are still pending or blocked")
    if swisstlm3d_archive_status == "measured_corridor_relevance":
        uncertainty_reduced.append("corridor-level swissTLM3D relevance is measured for roads, barriers, and water")

    return {
        "uncertainty_envelope_status": "measured_with_pending_target_artifacts" if limiting_factors else "measured",
        "final_classification": "inconclusive",
        "limiting_factors": limiting_factors,
        "uncertainty_reduced": uncertainty_reduced,
        "remaining_uncertainty": remaining_uncertainty,
    }


def load_json_manifest(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SameScaleUncertaintyEnvelopeError(f"missing manifest: {path}") from exc


def parse_bounded_output_markdown(text: str) -> dict[str, Any] | None:
    def section(heading: str) -> str:
        match = re.search(
            rf"^## {re.escape(heading)}\n(?P<body>.*?)(?=^## |\Z)",
            text,
            flags=re.MULTILINE | re.DOTALL,
        )
        return match.group("body") if match else ""

    def text_value(body: str, label: str) -> str | None:
        match = re.search(rf"^\s*-?\s*{re.escape(label)}:\s*`([^`]*)`$", body, re.MULTILINE)
        return match.group(1) if match else None

    def int_value(body: str, label: str) -> int | None:
        value = text_value(body, label)
        return int(value) if value is not None and value != "None" else None

    def bool_value(body: str, label: str) -> bool | None:
        value = text_value(body, label)
        if value is None:
            return None
        if value in {"True", "true"}:
            return True
        if value in {"False", "false"}:
            return False
        return None

    preamble = text.split("\n## ", 1)[0]
    comparison = section("Validation Output")
    comparison_details = section("Validation Output Comparison")
    audit = section("Validation Output Audit")
    pressure = section("Measured Pressure")
    deltas = section("Measured Deltas vs Selected Target Budget")
    convergence = section("Convergence")
    sufficiency = section("Execution Sufficiency")

    final_classification = text_value(preamble, "Final classification")
    if final_classification is None:
        return None

    validation_output_comparison = {
        "status": text_value(comparison_details, "Validation output comparison status"),
        "validation_output_mode": text_value(comparison_details, "Validation output mode"),
        "baseline_file_count": int_value(comparison_details, "Baseline file count"),
        "baseline_bytes": int_value(comparison_details, "Baseline bytes"),
        "reduced_file_count": int_value(comparison_details, "Reduced file count"),
        "reduced_bytes": int_value(comparison_details, "Reduced bytes"),
        "reduction_file_count_delta": int_value(comparison_details, "Reduction file-count delta"),
        "reduction_bytes_delta": int_value(comparison_details, "Reduction byte delta"),
        "required_provenance_retained": bool_value(comparison_details, "Required provenance retained"),
    }
    if validation_output_comparison["status"] is None and validation_output_comparison["validation_output_mode"] is not None:
        validation_output_comparison["status"] = "available"

    validation_output_audit = {
        "status": text_value(audit, "Status"),
        "manifest_path": text_value(audit, "Manifest path"),
        "reduced": bool_value(audit, "Reduced"),
        "validation_output_mode": text_value(audit, "Validation output mode"),
        "family_count": int_value(audit, "Family count"),
        "total_file_count": int_value(audit, "Total file count"),
        "total_bytes": int_value(audit, "Total bytes"),
    }

    current_pressure = {
        "current_file_count": int_value(pressure, "Current file count"),
        "current_total_bytes": int_value(pressure, "Current total bytes"),
        "file_count_ceiling": int_value(pressure, "File ceiling"),
        "byte_ceiling": int_value(pressure, "Byte ceiling"),
        "file_count_margin": int_value(pressure, "File-count margin"),
        "byte_margin": int_value(pressure, "Byte margin"),
        "file_family_pressure": text_value(pressure, "Inode/file-family pressure"),
    }

    measured_savings = {
        "validation_output_file_count_delta_vs_target_budget": int_value(deltas, "Validation file-count delta"),
        "validation_output_bytes_delta_vs_target_budget": int_value(deltas, "Validation byte delta"),
        "hazard_output_file_count_delta_vs_target_budget": int_value(deltas, "Hazard file-count delta"),
        "hazard_output_bytes_delta_vs_target_budget": int_value(deltas, "Hazard byte delta"),
    }

    return {
        "schema_version": getattr(BOUNDED, "SUMMARY_SCHEMA_VERSION", "bounded_validation_output_profile_v1"),
        "final_classification": final_classification,
        "validation_output_blocker_status": text_value(preamble, "Validation output blocker status") or "blocker_retained",
        "validation_output_reduced": bool_value(preamble, "Validation output reduced")
        if bool_value(preamble, "Validation output reduced") is not None
        else True,
        "validation_output_comparison": validation_output_comparison,
        "validation_output_audit": validation_output_audit,
        "local_output_audit": {
            "status": text_value(preamble, "Local output audit") or "available",
        },
        "current_pressure": current_pressure,
        "measured_savings": measured_savings,
        "convergence": {
            "status": text_value(convergence, "Convergence status") or None,
            "validation_debug_output_status": text_value(convergence, "Validation debug output status") or None,
            "output_budget_status": text_value(convergence, "Output-budget status") or None,
            "qa_status": text_value(convergence, "QA status") or None,
        },
        "execution_sufficiency": {
            "decision": text_value(sufficiency, "Decision") or None,
            "final_classification": text_value(sufficiency, "Final classification") or None,
        },
    }



def collect_missing_or_pending_inputs(
    *,
    convergence_summary: dict[str, Any],
    bounded_summary: dict[str, Any],
    single_job_summary: dict[str, Any],
    context_summary: dict[str, Any],
) -> list[dict[str, Any]]:
    missing: list[dict[str, Any]] = []
    if convergence_summary.get("target_artifact_restore_status") != "ready":
        missing.append(
            {
                "category": "target_artifact_restore",
                "status": convergence_summary.get("target_artifact_restore_status"),
                "reason": "TB-017 completed as a blocked restoration record; target-side same-scale artifacts remain absent",
            }
        )
    for item in convergence_summary.get("missing_inputs", []):
        missing.append(
            {
                "category": "convergence",
                "requested_path": item.get("requested_path"),
                "status": item.get("status"),
                "reason": item.get("reason"),
            }
        )
    if convergence_summary.get("convergence_status") != "measured":
        missing.append(
            {
                "category": "convergence",
                "status": convergence_summary.get("convergence_status"),
                "reason": "same-scale target-vs-gate convergence remains pending",
            }
        )
    if bounded_summary.get("local_output_audit", {}).get("status") != "available":
        missing.append(
            {
                "category": "validation_output",
                "status": bounded_summary.get("local_output_audit", {}).get("status"),
                "reason": "local validation-output audit is not available",
            }
        )
    if single_job_summary.get("final_classification") in {"blocked_pending_evidence", "defer"}:
        missing.append(
            {
                "category": "execution_sufficiency",
                "status": single_job_summary.get("final_classification"),
                "reason": "single-job sufficiency remains deferred or pending",
            }
        )
    if context_summary.get("swisstlm3d_archive_status") != "measured_corridor_relevance":
        missing.append(
            {
                "category": "context",
                "status": context_summary.get("swisstlm3d_archive_status"),
                "reason": context_summary.get("swisstlm3d_archive_blocked_reason") or "context corridor relevance not measured",
            }
        )
    return missing


def build_per_layer_metrics(comparisons: list[dict[str, Any]]) -> list[dict[str, Any]]:
    per_layer: list[dict[str, Any]] = []
    for comparison in comparisons:
        for layer in comparison.get("cellwise_metrics", {}).get("layer_comparisons", []):
            per_layer.append(
                {
                    "reference_manifest_path": comparison.get("reference_run", {}).get("manifest_path"),
                    "compare_manifest_path": comparison.get("compare_run", {}).get("manifest_path"),
                    "layer_name": layer.get("layer_key"),
                    "grid_shape": layer.get("grid_shape"),
                    "linf_abs_diff": layer.get("value_metrics", {}).get("linf_abs_diff"),
                    "l1_abs_diff": layer.get("value_metrics", {}).get("l1_abs_diff"),
                    "rmse": layer.get("value_metrics", {}).get("rmse"),
                    "nonzero_jaccard": layer.get("nonzero_metrics", {}).get("nonzero_jaccard"),
                    "threshold_exceedance_disagreement": layer.get("threshold_metrics", {}),
                    "reference_missing_cell_count": layer.get("missing_cell_metrics", {}).get("reference_missing_cell_count"),
                    "compare_missing_cell_count": layer.get("missing_cell_metrics", {}).get("compare_missing_cell_count"),
                    "nodata_mismatch_count": layer.get("missing_cell_metrics", {}).get("nodata_mismatch_count"),
                }
            )
    return per_layer


def strongest_disagreement_layers(comparisons: list[dict[str, Any]]) -> list[str]:
    layers = []
    for comparison in comparisons:
        for layer in comparison.get("cellwise_metrics", {}).get("layer_comparisons", []):
            layers.append((layer.get("value_metrics", {}).get("linf_abs_diff", 0.0), layer.get("layer_key")))
    layers.sort(reverse=True)
    return [layer_name for _, layer_name in layers[:3] if layer_name]


def render_markdown_report(report: dict[str, Any]) -> str:
    lines = [
        "# Same-Scale Uncertainty Envelope",
        "",
        f"- Pilot id: `{report['pilot_id']}`",
        f"- Final classification: `{report['final_classification']}`",
        f"- Envelope status: `{report['uncertainty_envelope_status']}`",
        f"- Scale-up authorized: `{str(report['scale_up_authorized']).lower()}`",
        f"- Operational claims allowed: `{str(report['operational_claims_allowed']).lower()}`",
        f"- Convergence status: `{report['convergence_status']}`",
        f"- Target artifact restore status: `{report['target_artifact_restore_status']}`",
        "",
        "## Convergence",
        f"- Artifact readiness: `{report['artifact_readiness_status']}`",
    ]
    convergence = report["convergence_evidence"]
    if convergence.get("missing_inputs"):
        lines.append("- Missing or pending inputs:")
        for item in convergence["missing_inputs"]:
            lines.append(f"  - `{item.get('requested_path')}`: {item.get('reason')}")
    else:
        lines.append("- Measured per-layer convergence metrics are available.")
    lines.extend(
        [
            "",
            "## Validation Output",
            f"- Status: `{report['validation_output_status']}`",
            f"- Validation output mode context: `{report['validation_output_mode_context']}`",
            f"- Validation output reduced: `{report['validation_output_evidence'].get('validation_output_reduced')}`",
        ]
    )
    val = report["validation_output_evidence"]
    lines.extend(
        [
            f"- Validation output comparison status: `{val.get('validation_output_comparison', {}).get('status')}`",
            f"- Baseline validation output files: `{val.get('validation_output_audit', {}).get('total_file_count')}`",
            f"- Baseline validation output bytes: `{val.get('validation_output_audit', {}).get('total_bytes')}`",
            f"- Summary-only validation output files: `{val.get('validation_output_comparison', {}).get('reduced_file_count')}`",
            f"- Summary-only validation output bytes: `{val.get('validation_output_comparison', {}).get('reduced_bytes')}`",
            f"- Reduction file count delta: `{val.get('validation_output_comparison', {}).get('reduction_file_count_delta')}`",
            f"- Reduction byte delta: `{val.get('validation_output_comparison', {}).get('reduction_bytes_delta')}`",
            "",
            "## Context",
            f"- Status: `{report['context_status']}`",
            f"- swissTLM3D corridor status: `{report['context_evidence'].get('swisstlm3d_archive_status')}`",
            f"- Roads/transport relevance: `{report['context_evidence'].get('roads_or_transport_relevance', {}).get('classification')}`",
            f"- Water/channel relevance: `{report['context_evidence'].get('water_or_channel_relevance', {}).get('classification')}`",
            f"- Barriers/protection relevance: `{report['context_evidence'].get('barriers_or_protection_relevance', {}).get('classification')}`",
            "",
            "## Execution Sufficiency",
            f"- Status: `{report['execution_sufficiency_status']}`",
            f"- Decision: `{report['execution_sufficiency_evidence'].get('decision')}`",
            "",
            "## Limiting Factors",
        ]
    )
    for item in report["limiting_factors"]:
        lines.append(f"- `{item}`")
    lines.extend(["", "## Remaining Uncertainty"])
    for item in report["remaining_uncertainty"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Target-Artifact Readiness",
            f"- Gate manifest available: `{str(report['gate_manifest_available']).lower()}`",
            f"- Target validation manifest available: `{str(report['target_validation_manifest_available']).lower()}`",
            f"- Target hazard manifest available: `{str(report['target_hazard_manifest_available']).lower()}`",
            f"- Target cell-wise layers available: `{str(report['target_cellwise_layers_available']).lower()}`",
            f"- TB-014 ready: `{str(report['tb014_ready']).lower()}`",
            f"- Target artifact restore status: `{report['target_artifact_restore_status']}`",
        ]
    )
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
