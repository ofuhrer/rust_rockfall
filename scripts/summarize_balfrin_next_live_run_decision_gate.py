#!/usr/bin/env python3
"""Decide the next authorized live Balfrin action from measured evidence.

This helper compares three options:

- metrics-completion rerun
- smallest bounded multi-zone probe
- deferral in favor of portability or physical-evidence work

It stays read-only, synthesizes the current evidence helpers and tracked
fixtures into one deterministic decision report, and fails closed whenever the
required measured inputs are missing.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import generate_balfrin_multi_release_zone_demo_handoff as multi_zone_handoff  # noqa: E402
from scripts import summarize_balfrin_probe_metrics_report as metrics_report  # noqa: E402
from scripts import summarize_balfrin_probe_preservation_gate as preservation_gate  # noqa: E402
from scripts import summarize_multi_zone_reducer_pressure as reducer_pressure  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "balfrin_next_live_run_decision_gate_v1"
REPORT_BASENAME = "balfrin_next_live_run_decision_gate_v1"
DEFAULT_ARTIFACT_DIR = ROOT / "validation/private/tschamut_public_pilot/balfrin_next_live_run_decision_gate_v1"
DEFAULT_EVIDENCE_BUNDLE = ROOT / "tests/fixtures/balfrin_next_live_run_decision_gate/default_bundle.json"
DEFAULT_PRESERVATION_RUN_ROOT = ROOT / "tests/fixtures/balfrin_probe_metrics_contract/complete_run_root"
DEFAULT_REDUCER_PRESSURE_ROOT = Path("/tmp/rust_rockfall/balfrin_next_live_run_decision_gate_v1/reducer_pressure")

REQUIRED_BUNDLE_KEYS = (
    "probe_metrics_report",
    "preservation_gate_report",
    "multi_zone_reducer_pressure_report",
    "multi_zone_handoff_report",
)

OPTION_METRICS = "metrics_completion_rerun"
OPTION_MULTI_ZONE = "smallest_bounded_multi_zone_probe"
OPTION_DEFER = "defer_portability_or_physical_evidence"


class BalfrinNextLiveRunDecisionGateError(ValueError):
    """User-facing Balfrin decision-gate error."""


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-json", type=Path, default=None, help="Optional evidence bundle JSON override.")
    parser.add_argument("--format", choices=("json", "text"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    parser.add_argument("--text-output", type=Path, default=None)
    parser.add_argument("--artifact-dir", type=Path, default=None)
    return parser.parse_args(argv)


def _load_json(path: Path | None) -> dict[str, Any] | None:
    if path is None or not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else None


def _copy_mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _safe_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if isinstance(item, str) and item]


def _status(value: Any, default: str = "blocked_missing_inputs") -> str:
    return str(value) if isinstance(value, str) and value else default


def _bool(value: Any) -> bool:
    return bool(value)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    try:
        report = build_report(load_evidence_override(args.evidence_json))
    except BalfrinNextLiveRunDecisionGateError as exc:
        print(f"balfrin next live-run decision gate error: {exc}", file=sys.stderr)
        return 2

    materialize_artifacts(report, json_output=args.json_output, text_output=args.text_output, artifact_dir=args.artifact_dir)

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
    else:
        print(render_text_report(report))
    return 0 if report["decision_status"] != "blocked" else 2


def load_evidence_override(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    if not path.exists():
        raise BalfrinNextLiveRunDecisionGateError(f"evidence override is missing: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise BalfrinNextLiveRunDecisionGateError("evidence override must be a JSON object")
    return payload


def build_report(evidence_override: dict[str, Any] | None = None) -> dict[str, Any]:
    if evidence_override is None:
        evidence_override = _load_json(DEFAULT_EVIDENCE_BUNDLE)
        if evidence_override is None:
            evidence_override = build_current_evidence_bundle()

    if isinstance(evidence_override.get("decision_gate_report"), dict):
        return dict(evidence_override["decision_gate_report"])

    if evidence_override.get("missing_inputs"):
        return blocked_missing_inputs_report(_safe_list(evidence_override.get("missing_inputs")))

    bundle = normalize_bundle(evidence_override)
    missing_sections = [name for name, section in bundle["sections"].items() if section.get("status") == "missing"]
    if missing_sections:
        return blocked_missing_inputs_report(missing_sections)

    criteria = build_criteria(bundle)
    option_assessments = build_option_assessments(criteria)
    recommended = choose_recommendation(option_assessments)

    report = {
        "schema_version": SCHEMA_VERSION,
        "decision_status": recommended["status"],
        "decision_summary": recommended["summary"],
        "recommended_next_action": recommended,
        "next_follow_up_package_task": recommended["follow_up_task"],
        "criteria": criteria,
        "option_assessments": option_assessments,
        "evidence_sources": build_evidence_sources(bundle),
        "claim_boundaries": {
            "operational_claims_allowed": False,
            "physical_probability_claims_allowed": False,
            "annual_frequency_claims_allowed": False,
            "risk_exposure_vulnerability_claims_allowed": False,
            "scale_up_authorized": False,
            "distributed_execution_authorized": False,
        },
        "blocked_reason": recommended.get("blocked_reason", "none") if recommended["status"] == "blocked" else "none",
    }
    return report


def normalize_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    sections = {key: _copy_mapping(bundle.get(key)) for key in REQUIRED_BUNDLE_KEYS}
    return {
        "schema_version": str(bundle.get("schema_version") or "balfrin_next_live_run_decision_gate_bundle_v1"),
        "sections": sections,
        "scientific_value": _copy_mapping(bundle.get("scientific_value")),
        "portability_value": _copy_mapping(bundle.get("portability_value")),
        "source_paths": _copy_mapping(bundle.get("source_paths")),
    }


def build_current_evidence_bundle() -> dict[str, Any]:
    default_bundle = _load_json(DEFAULT_EVIDENCE_BUNDLE)
    if default_bundle is None:
        raise BalfrinNextLiveRunDecisionGateError(f"default evidence bundle is missing: {DEFAULT_EVIDENCE_BUNDLE}")

    with tempfile.TemporaryDirectory() as tmpdir:
        reducer_root = Path(tmpdir) / "reducer_pressure"
        reducer_pressure.materialize_probe_root(reducer_root)
        reducer_report = reducer_pressure.build_report(reducer_root)

    return {
        "schema_version": str(default_bundle.get("schema_version") or "balfrin_next_live_run_decision_gate_bundle_v1"),
        "probe_metrics_report": metrics_report.build_report(_copy_mapping(default_bundle.get("probe_metrics_report"))),
        "preservation_gate_report": preservation_gate.build_report(run_root=DEFAULT_PRESERVATION_RUN_ROOT),
        "multi_zone_reducer_pressure_report": reducer_report,
        "multi_zone_handoff_report": multi_zone_handoff.build_report(),
        "scientific_value": _copy_mapping(default_bundle.get("scientific_value")),
        "portability_value": _copy_mapping(default_bundle.get("portability_value")),
        "source_paths": _copy_mapping(default_bundle.get("source_paths")),
    }


def build_criteria(bundle: dict[str, Any]) -> dict[str, Any]:
    metrics = bundle["sections"]["probe_metrics_report"]
    preservation = bundle["sections"]["preservation_gate_report"]
    reducer = bundle["sections"]["multi_zone_reducer_pressure_report"]
    package = bundle["sections"]["multi_zone_handoff_report"]
    scientific_value = bundle["scientific_value"]
    portability_value = bundle["portability_value"]

    missing_metrics = _safe_list(metrics.get("metrics_contract_missing_metrics"))
    next_run_required = _safe_list(metrics.get("metrics_remediation", {}).get("next_run_required_metrics"))
    preservation_ready = preservation.get("gate_status") == "ready_for_demonstration_evidence"
    reducer_blocked = _bool(reducer.get("multi_zone_dry_run_blocked"))
    output_pressure = _copy_mapping(package.get("pressure_checkpoints", {}).get("output_pressure"))
    multi_zone_ready = (
        package.get("package_status") == "ready"
        and not reducer_blocked
        and output_pressure.get("status") in {"ready", "acceptable"}
    )

    return {
        "missing_target_area_metrics": {
            "status": "missing" if missing_metrics else "complete",
            "metrics_contract_status": _status(metrics.get("metrics_contract_status")),
            "missing_mandatory_metrics": missing_metrics,
            "next_run_required_metrics": next_run_required,
            "summary": (
                "Target-area metrics remain incomplete and can be closed by the next measured rerun."
                if missing_metrics
                else "The target-area metrics contract is complete, so a rerun would not close a current gap."
            ),
        },
        "preservation_gate_readiness": {
            "status": "ready" if preservation_ready else "blocked",
            "gate_status": _status(preservation.get("gate_status")),
            "required_run_root_entries_status": _status(preservation.get("required_run_root_entries_status")),
            "output_family_summaries_status": _status(preservation.get("output_family_summaries", {}).get("status")),
            "spatial_gis_artifact_paths_status": _status(preservation.get("spatial_gis_artifact_paths", {}).get("status")),
            "blocked_reasons": _safe_list(preservation.get("blocked_reasons")),
            "summary": preservation.get("summary", ""),
        },
        "reducer_pressure": {
            "status": "blocked" if reducer_blocked else "ready",
            "probe_status": _status(reducer.get("probe_status")),
            "bottleneck_classification": _status(reducer.get("bottleneck_classification")),
            "multi_zone_dry_run_blocked": reducer_blocked,
            "blocked_reason": reducer.get("blocked_reason", ""),
            "reducer_wall_time_seconds": reducer.get("reducer_wall_time_seconds"),
            "recommended_reducer_constraints": _copy_mapping(reducer.get("recommended_reducer_constraints")),
        },
        "multi_zone_package_readiness": {
            "status": "ready" if multi_zone_ready else "blocked",
            "package_status": _status(package.get("package_status")),
            "output_pressure_status": _status(output_pressure.get("status")),
            "validation_output_blocker_status": _status(output_pressure.get("validation_output_blocker_status")),
            "reducer_pressure_status": _status(package.get("pressure_checkpoints", {}).get("reducer_chunk_pressure", {}).get("status")),
            "follow_up_status": _status(package.get("follow_up_recommendation", {}).get("status")),
            "summary": package.get("pressure_checkpoints", {}).get("output_pressure", {}).get("status", ""),
        },
        "expected_runtime_output_pressure": {
            "status": "acceptable" if output_pressure.get("status") in {"ready", "acceptable"} else "retained",
            "output_pressure_status": _status(output_pressure.get("status")),
            "validation_output_blocker_status": _status(output_pressure.get("validation_output_blocker_status")),
            "reducer_wall_time_seconds": reducer.get("reducer_wall_time_seconds"),
            "summary": package.get("pressure_checkpoints", {}).get("output_pressure", {}).get("status", ""),
        },
        "scientific_value": {
            "status": _status(scientific_value.get("status"), "unknown"),
            "summary": scientific_value.get("summary", ""),
        },
        "portability_or_physical_evidence_value": {
            "status": _status(portability_value.get("status"), "unknown"),
            "summary": portability_value.get("summary", ""),
        },
    }


def build_option_assessments(criteria: dict[str, Any]) -> dict[str, Any]:
    metrics = criteria["missing_target_area_metrics"]
    preservation = criteria["preservation_gate_readiness"]
    reducer = criteria["reducer_pressure"]
    package = criteria["multi_zone_package_readiness"]
    runtime_pressure = criteria["expected_runtime_output_pressure"]
    scientific = criteria["scientific_value"]
    portability = criteria["portability_or_physical_evidence_value"]

    metrics_blockers: list[str] = []
    if metrics["status"] == "missing":
        if preservation["status"] != "ready":
            metrics_blockers.append(f"preservation_gate:{preservation['gate_status']}")
    else:
        metrics_blockers.append("no_missing_target_area_metrics")

    multi_zone_blockers: list[str] = []
    if metrics["status"] == "missing":
        multi_zone_blockers.append("missing_target_area_metrics")
    if preservation["status"] != "ready":
        multi_zone_blockers.append(f"preservation_gate:{preservation['gate_status']}")
    if reducer["status"] != "ready":
        multi_zone_blockers.append(f"reducer_pressure:{reducer['bottleneck_classification']}")
    if package["status"] != "ready":
        multi_zone_blockers.append(f"multi_zone_package:{package['package_status']}")
    if runtime_pressure["status"] != "acceptable":
        multi_zone_blockers.append(f"output_pressure:{runtime_pressure['output_pressure_status']}")
    if scientific["status"] not in {"high", "ready"}:
        multi_zone_blockers.append(f"scientific_value:{scientific['status']}")

    defer_blockers: list[str] = []
    if metrics["status"] == "missing":
        defer_blockers.append("missing_target_area_metrics")
    if preservation["status"] != "ready":
        defer_blockers.append(f"preservation_gate:{preservation['gate_status']}")
    if package["status"] == "ready" and reducer["status"] == "ready" and runtime_pressure["status"] == "acceptable":
        defer_blockers.append("multi_zone_probe_is_ready")
    if portability["status"] not in {"high", "preferred", "defer"} and scientific["status"] != "low":
        defer_blockers.append(f"portability_or_physical_evidence_value:{portability['status']}")

    assessments = {
        OPTION_METRICS: {
            "status": "ready" if metrics["status"] == "missing" and preservation["status"] == "ready" else "blocked",
            "follow_up_task": "TB-206",
            "summary": (
                "Missing target-area metrics remain the clearest measured gap, so the metrics-completion rerun (metrics rerun) is the next ready action and the preservation gate is ready."
                if metrics["status"] == "missing" and preservation["status"] == "ready"
                else "No current target-area metrics gap is open for a rerun to close."
            ),
            "exact_evidence_blockers": metrics_blockers,
            "criteria": ["missing_target_area_metrics", "preservation_gate_readiness"],
        },
        OPTION_MULTI_ZONE: {
            "status": "ready" if not multi_zone_blockers else "blocked",
            "follow_up_task": "TB-205",
            "summary": (
                "The smallest bounded multi-zone probe is ready only when the preservation gate, reducer pressure, package readiness, runtime/output pressure, and scientific value all align."
            ),
            "exact_evidence_blockers": multi_zone_blockers,
            "criteria": [
                "missing_target_area_metrics",
                "preservation_gate_readiness",
                "reducer_pressure",
                "multi_zone_package_readiness",
                "expected_runtime_output_pressure",
                "scientific_value",
            ],
        },
        OPTION_DEFER: {
            "status": "defer" if metrics["status"] == "complete" and multi_zone_blockers else "blocked",
            "follow_up_task": "TB-207",
            "summary": (
                "Deferral is justified once the target-area metrics gap is closed and the multi-zone path remains no-go, so portability or physical-evidence work can proceed first."
            ),
            "exact_evidence_blockers": defer_blockers,
            "criteria": [
                "missing_target_area_metrics",
                "preservation_gate_readiness",
                "multi_zone_package_readiness",
                "expected_runtime_output_pressure",
                "portability_or_physical_evidence_value",
            ],
        },
    }
    return assessments


def choose_recommendation(option_assessments: dict[str, Any]) -> dict[str, Any]:
    metrics = option_assessments[OPTION_METRICS]
    multi_zone = option_assessments[OPTION_MULTI_ZONE]
    defer = option_assessments[OPTION_DEFER]

    if metrics["status"] == "ready":
        return {
            "action_id": OPTION_METRICS,
            "status": "ready",
            "classification": "ready",
            "follow_up_task": metrics["follow_up_task"],
            "summary": metrics["summary"],
            "exact_evidence_blockers": metrics["exact_evidence_blockers"],
            "blocked_reason": "none",
        }
    if multi_zone["status"] == "ready":
        return {
            "action_id": OPTION_MULTI_ZONE,
            "status": "ready",
            "classification": "ready",
            "follow_up_task": multi_zone["follow_up_task"],
            "summary": multi_zone["summary"],
            "exact_evidence_blockers": multi_zone["exact_evidence_blockers"],
            "blocked_reason": "none",
        }
    if defer["status"] == "defer":
        return {
            "action_id": OPTION_DEFER,
            "status": "defer",
            "classification": "defer",
            "follow_up_task": defer["follow_up_task"],
            "summary": defer["summary"],
            "exact_evidence_blockers": defer["exact_evidence_blockers"],
            "blocked_reason": "none",
        }

    return {
        "action_id": OPTION_DEFER,
        "status": "blocked",
        "classification": "blocked",
        "follow_up_task": defer["follow_up_task"],
        "summary": "The current evidence remains insufficient for any of the three options.",
        "exact_evidence_blockers": sorted(
            set(metrics["exact_evidence_blockers"] + multi_zone["exact_evidence_blockers"] + defer["exact_evidence_blockers"])
        ),
        "blocked_reason": "required measured inputs are missing or unresolved",
    }


def build_evidence_sources(bundle: dict[str, Any]) -> dict[str, Any]:
    source_paths = _copy_mapping(bundle.get("source_paths"))
    return {
        "schema_version": "balfrin_next_live_run_decision_gate_evidence_sources_v1",
        "probe_metrics_report": source_paths.get("probe_metrics_report"),
        "preservation_gate_report": source_paths.get("preservation_gate_report"),
        "multi_zone_reducer_pressure_report": source_paths.get("multi_zone_reducer_pressure_report"),
        "multi_zone_handoff_report": source_paths.get("multi_zone_handoff_report"),
    }


def blocked_missing_inputs_report(missing_inputs: list[str]) -> dict[str, Any]:
    missing = [str(item) for item in missing_inputs if str(item)]
    return {
        "schema_version": SCHEMA_VERSION,
        "decision_status": "blocked",
        "decision_summary": "The next live Balfrin decision gate is blocked because required measured inputs are missing.",
        "recommended_next_action": {
            "action_id": OPTION_METRICS,
            "status": "blocked",
            "classification": "blocked",
            "follow_up_task": "TB-206",
            "summary": "Missing measured inputs prevent the gate from deciding whether a metrics rerun, multi-zone probe, or deferral should proceed.",
            "exact_evidence_blockers": missing,
            "blocked_reason": "required measured inputs are missing",
        },
        "next_follow_up_package_task": "TB-206",
        "criteria": {
            "missing_target_area_metrics": {"status": "blocked_missing_inputs", "missing_mandatory_metrics": []},
            "preservation_gate_readiness": {"status": "blocked_missing_inputs"},
            "reducer_pressure": {"status": "blocked_missing_inputs"},
            "multi_zone_package_readiness": {"status": "blocked_missing_inputs"},
            "expected_runtime_output_pressure": {"status": "blocked_missing_inputs"},
            "scientific_value": {"status": "blocked_missing_inputs"},
            "portability_or_physical_evidence_value": {"status": "blocked_missing_inputs"},
        },
        "option_assessments": {
            OPTION_METRICS: {
                "status": "blocked",
                "follow_up_task": "TB-206",
                "summary": "The metrics-completion rerun cannot be prioritized until the missing measured inputs are supplied.",
                "exact_evidence_blockers": missing,
                "criteria": ["missing_target_area_metrics", "preservation_gate_readiness"],
            },
            OPTION_MULTI_ZONE: {
                "status": "blocked",
                "follow_up_task": "TB-205",
                "summary": "The smallest bounded multi-zone probe is blocked because the evidence bundle is incomplete.",
                "exact_evidence_blockers": missing,
                "criteria": ["reducer_pressure", "multi_zone_package_readiness"],
            },
            OPTION_DEFER: {
                "status": "blocked",
                "follow_up_task": "TB-207",
                "summary": "Deferral is blocked because the gate cannot establish whether a direct measured gap still needs closure.",
                "exact_evidence_blockers": missing,
                "criteria": ["scientific_value", "portability_or_physical_evidence_value"],
            },
        },
        "evidence_sources": {
            "schema_version": "balfrin_next_live_run_decision_gate_evidence_sources_v1",
            "probe_metrics_report": None,
            "preservation_gate_report": None,
            "multi_zone_reducer_pressure_report": None,
            "multi_zone_handoff_report": None,
        },
        "claim_boundaries": {
            "operational_claims_allowed": False,
            "physical_probability_claims_allowed": False,
            "annual_frequency_claims_allowed": False,
            "risk_exposure_vulnerability_claims_allowed": False,
            "scale_up_authorized": False,
            "distributed_execution_authorized": False,
        },
        "blocked_reason": "required measured inputs are missing: " + ", ".join(missing) if missing else "required measured inputs are missing",
    }


def materialize_artifacts(
    report: dict[str, Any],
    *,
    json_output: Path | None = None,
    text_output: Path | None = None,
    artifact_dir: Path | None = None,
) -> None:
    if artifact_dir is not None:
        artifact_dir.mkdir(parents=True, exist_ok=True)
        json_output = json_output or artifact_dir / f"{REPORT_BASENAME}.json"
        text_output = text_output or artifact_dir / f"{REPORT_BASENAME}.txt"
    if json_output is not None:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(report, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    if text_output is not None:
        text_output.parent.mkdir(parents=True, exist_ok=True)
        text_output.write_text(render_text_report(report) + "\n", encoding="utf-8")


def render_text_report(report: dict[str, Any]) -> str:
    lines = [
        "Balfrin Next Live-Run Decision Gate",
        f"schema_version: {report.get('schema_version', 'unknown')}",
        f"decision_status: {report.get('decision_status', 'unknown')}",
        f"decision_summary: {report.get('decision_summary', '')}",
        f"next_follow_up_package_task: {report.get('next_follow_up_package_task', 'unknown')}",
        "",
        "criteria:",
    ]
    criteria = report.get("criteria", {})
    for key in (
        "missing_target_area_metrics",
        "preservation_gate_readiness",
        "reducer_pressure",
        "multi_zone_package_readiness",
        "expected_runtime_output_pressure",
        "scientific_value",
        "portability_or_physical_evidence_value",
    ):
        entry = criteria.get(key, {}) if isinstance(criteria, dict) else {}
        lines.append(f"  - {key}: {entry.get('status', 'unknown')}")
        if key == "missing_target_area_metrics":
            lines.append(f"    missing_mandatory_metrics: {entry.get('missing_mandatory_metrics', [])}")
            lines.append(f"    next_run_required_metrics: {entry.get('next_run_required_metrics', [])}")
        if key == "reducer_pressure":
            lines.append(f"    bottleneck_classification: {entry.get('bottleneck_classification', '')}")
            lines.append(f"    blocked_reason: {entry.get('blocked_reason', '')}")
        if key == "multi_zone_package_readiness":
            lines.append(f"    package_status: {entry.get('package_status', '')}")
            lines.append(f"    output_pressure_status: {entry.get('output_pressure_status', '')}")
        if key == "scientific_value":
            lines.append(f"    summary: {entry.get('summary', '')}")

    lines.extend(["", "options:"])
    for option_key in (OPTION_METRICS, OPTION_MULTI_ZONE, OPTION_DEFER):
        option = report.get("option_assessments", {}).get(option_key, {})
        lines.append(f"  - {option_key}: {option.get('status', 'unknown')}")
        lines.append(f"    follow_up_task: {option.get('follow_up_task', 'unknown')}")
        lines.append(f"    blockers: {option.get('exact_evidence_blockers', [])}")
        lines.append(f"    summary: {option.get('summary', '')}")

    recommended = report.get("recommended_next_action", {})
    lines.extend(
        [
            "",
            "recommended_next_action:",
            f"  action_id: {recommended.get('action_id', 'unknown')}",
            f"  classification: {recommended.get('classification', 'unknown')}",
            f"  follow_up_task: {recommended.get('follow_up_task', 'unknown')}",
            f"  exact_evidence_blockers: {recommended.get('exact_evidence_blockers', [])}",
            f"  summary: {recommended.get('summary', '')}",
        ]
    )
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
