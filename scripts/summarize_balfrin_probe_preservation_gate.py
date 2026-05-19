#!/usr/bin/env python3
"""Summarize the Balfrin probe metrics/run-root preservation gate.

This helper is read-only. It classifies whether a preserved Balfrin run root
contains the measured metrics, preserved run-root files, output families, and
declared GIS artifact paths needed before a future authorized live run can be
treated as demonstration evidence.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import collect_balfrin_probe_metrics as probe_metrics  # noqa: E402
from scripts import audit_balfrin_run_root_output_budget as output_budget_audit  # noqa: E402
from scripts import summarize_balfrin_probe_metrics_report as metrics_report  # noqa: E402
from scripts import summarize_balfrin_output_tier_audit as output_tier  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "balfrin_probe_preservation_gate_v1"
REPORT_BASENAME = "balfrin_probe_preservation_gate_v1"
DEFAULT_ARTIFACT_DIR = ROOT / "validation/private/tschamut_public_pilot/balfrin_probe_preservation_gate_v1"

REQUIRED_RUN_ROOT_ENTRIES: list[dict[str, str]] = [
    {"path": "command_plan.json", "kind": "file"},
    {"path": "balfrin_probe_metrics.json", "kind": "file"},
    {"path": "output", "kind": "dir"},
    {"path": "output/validation_balfrin_probe_manifest.json", "kind": "file"},
    {"path": "output/validation_balfrin_probe_scaling_summary.json", "kind": "file"},
    {"path": "output/trajectory_chunks", "kind": "dir"},
    {"path": "output/chunks", "kind": "dir"},
    {"path": "logs", "kind": "dir"},
]

REQUIRED_SLURM_ACCOUNTING_FIELDS = [
    "JobID",
    "JobName",
    "Partition",
    "State",
    "ExitCode",
    "Elapsed",
    "AllocCPUS",
    "MaxRSS",
    "MaxDiskRead",
    "MaxDiskWrite",
    "WorkDir",
]


class BalfrinProbePreservationGateError(ValueError):
    """User-facing preservation-gate error."""


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--run-root",
        type=Path,
        default=None,
        help="Preserved run root to inspect.",
    )
    parser.add_argument(
        "--evidence-json",
        type=Path,
        default=None,
        help="Optional pre-collected probe metrics JSON.",
    )
    parser.add_argument("--format", choices=("json", "text"), default="text")
    parser.add_argument(
        "--json-output",
        type=Path,
        default=None,
        help="Optional JSON path to write the report.",
    )
    parser.add_argument(
        "--text-output",
        type=Path,
        default=None,
        help="Optional text path to write the report.",
    )
    parser.add_argument(
        "--artifact-dir",
        type=Path,
        default=None,
        help="Optional directory for the JSON and text report.",
    )
    return parser.parse_args(argv)


def _load_json(path: Path | None) -> dict[str, Any] | None:
    if path is None or not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else None


def _safe_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if isinstance(item, str) and item]


def _safe_mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _safe_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _metrics_completion_source(evidence: dict[str, Any], *, report_status: str, metrics_contract_status: str) -> str:
    explicit_source = evidence.get("metrics_completion_source")
    source_paths = _safe_mapping(evidence.get("source_paths"))
    for key in ("run_root", "output_root", "probe_manifest_path", "command_plan_path", "hazard_manifest_path"):
        value = evidence.get(key)
        if isinstance(value, str) and value:
            source_paths.setdefault(key, value)
    if isinstance(explicit_source, str) and explicit_source:
        return metrics_report.classify_metrics_completion_source(
            report_status=report_status,
            metrics_contract_status=metrics_contract_status,
            source_paths=source_paths,
            explicit_source=explicit_source,
        )
    return metrics_report.classify_metrics_completion_source(
        report_status=report_status,
        metrics_contract_status=metrics_contract_status,
        source_paths=source_paths,
    )


def _require_run_root_entries(run_root: Path) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    missing: list[str] = []
    for entry in REQUIRED_RUN_ROOT_ENTRIES:
        relative_path = Path(entry["path"])
        candidate = run_root / relative_path
        exists = candidate.exists()
        entry_report = {
            "path": entry["path"],
            "kind": entry["kind"],
            "absolute_path": str(candidate.resolve()),
            "exists": exists,
        }
        entries.append(entry_report)
        if not exists:
            missing.append(entry["path"])
    return {
        "required": entries,
        "missing": missing,
        "status": "complete" if not missing else "blocked_missing_inputs",
    }


def _load_declared_spatial_artifact_paths(hazard_manifest_path: str | None) -> dict[str, Any]:
    manifest_path = Path(hazard_manifest_path) if hazard_manifest_path else None
    manifest = _load_json(manifest_path)
    outputs = manifest.get("outputs") if isinstance(manifest, dict) else None
    declared: list[dict[str, Any]] = []
    family_counts: dict[str, int] = {}
    if isinstance(outputs, list):
        for entry in outputs:
            if not isinstance(entry, dict):
                continue
            kind = entry.get("kind")
            path = entry.get("path")
            if not isinstance(kind, str) or not kind:
                continue
            family_counts[kind] = family_counts.get(kind, 0) + 1
            declared.append(
                {
                    "kind": kind,
                    "path": str((manifest_path.parent / str(path)).resolve()) if manifest_path and isinstance(path, str) else None,
                    "declared": True,
                }
            )
    status = "declared" if declared else "blocked_missing_inputs"
    return {
        "status": status,
        "manifest_path": str(manifest_path) if manifest_path is not None else None,
        "declared_artifacts": declared,
        "declared_family_counts": family_counts,
        "missing_reason": "" if declared else "hazard manifest outputs are unavailable",
    }


def _is_complete_gate(
    *,
    run_root_status: str,
    metrics_contract_status: str,
    required_run_root_status: str,
    output_tier_status: str,
    spatial_artifact_status: str,
) -> bool:
    return (
        run_root_status == "measured_run_root"
        and metrics_contract_status == "complete"
        and required_run_root_status == "complete"
        and output_tier_status == "sufficient"
        and spatial_artifact_status == "declared"
    )


def build_report(
    evidence_override: dict[str, Any] | None = None,
    *,
    run_root: Path | None = None,
) -> dict[str, Any]:
    if evidence_override is not None and isinstance(evidence_override.get("preservation_gate_report"), dict):
        return dict(evidence_override["preservation_gate_report"])

    if evidence_override is None:
        if run_root is None:
            return blocked_missing_run_root_report(Path("missing-run-root"))
        if not run_root.exists():
            return blocked_missing_run_root_report(run_root)
        evidence = probe_metrics.collect_run_metrics(run_root)
    else:
        evidence = dict(evidence_override)
        if run_root is None:
            run_root_value = evidence.get("run_root")
            run_root = Path(str(run_root_value)) if isinstance(run_root_value, str) and run_root_value else None
        if run_root is None:
            return blocked_missing_run_root_report(Path("missing-run-root"))
        if not run_root.exists():
            return blocked_missing_run_root_report(
                run_root,
                metrics_completion_attempt_status=evidence.get("metrics_completion_attempt_status")
                if isinstance(evidence.get("metrics_completion_attempt_status"), str)
                else None,
                metrics_completion_outcome=evidence.get("metrics_completion_outcome")
                if isinstance(evidence.get("metrics_completion_outcome"), str)
                else None,
            )

    run_root = run_root.resolve()
    output_tier_report = output_tier.build_report(evidence)
    output_budget_report = output_budget_audit.build_report(run_root)
    required_run_root = _require_run_root_entries(run_root)
    spatial_artifacts = _load_declared_spatial_artifact_paths(evidence.get("hazard_manifest_path"))
    metrics_contract_status = str(evidence.get("metrics_contract_status") or "unknown")
    output_tier_status = str(output_tier_report.get("rebuildability_status") or "unknown")
    metrics_completion_source = _metrics_completion_source(
        evidence,
        report_status=str(evidence.get("report_status") or "unknown"),
        metrics_contract_status=metrics_contract_status,
    )
    metrics_completion_attempt_status = (
        evidence.get("metrics_completion_attempt_status")
        if isinstance(evidence.get("metrics_completion_attempt_status"), str)
        else None
    )
    evidence_report_status = str(evidence.get("report_status") or "")
    metrics_completion_report_status = (
        "complete"
        if metrics_contract_status == "complete" and evidence_report_status in {"", "measured_run_root"}
        else evidence_report_status
        or metrics_contract_status
    )
    metrics_completion_outcome = metrics_report.classify_metrics_completion_outcome(
        report_status=metrics_completion_report_status,
        metrics_contract_status=metrics_contract_status,
        metrics_completion_source=metrics_completion_source,
        explicit_outcome=evidence.get("metrics_completion_outcome")
        if isinstance(evidence.get("metrics_completion_outcome"), str)
        else None,
        attempt_status=metrics_completion_attempt_status,
    )
    gate_status = "ready_for_demonstration_evidence"
    if not _is_complete_gate(
        run_root_status="measured_run_root",
        metrics_contract_status=metrics_contract_status,
        required_run_root_status=required_run_root["status"],
        output_tier_status=output_tier_status,
        spatial_artifact_status=spatial_artifacts["status"],
    ):
        gate_status = "blocked_missing_inputs"

    metrics_contract_missing = _safe_list(evidence.get("metrics_contract_missing_metrics"))
    metrics_contract_ancillary_unavailable = _safe_list(
        evidence.get("metrics_contract_ancillary_unavailable_metrics")
    )
    output_family_counts = (
        output_tier_report.get("measured_family_counts")
        if isinstance(output_tier_report.get("measured_family_counts"), dict)
        else {}
    )
    missing_output_families = _safe_list(
        [
            family
            for family, is_present in (output_tier_report.get("required_family_counts_status") or {}).items()
            if not is_present
        ]
    )
    blocked_reasons = []
    if metrics_contract_status != "complete":
        blocked_reasons.append(f"metrics_contract:{metrics_contract_status}")
    if required_run_root["missing"]:
        blocked_reasons.append("missing_run_root_entries:" + ",".join(required_run_root["missing"]))
    if output_tier_status != "sufficient":
        blocked_reasons.append(f"output_tier:{output_tier_status}")
    if spatial_artifacts["status"] != "declared":
        blocked_reasons.append("missing_spatial_gis_artifact_paths")

    report = {
        "schema_version": SCHEMA_VERSION,
        "gate_status": gate_status,
        "preservation_gate_status": gate_status,
        "future_live_run_would_satisfy_evidence_preservation_contract": gate_status == "ready_for_demonstration_evidence",
        "run_root_status": "measured_run_root",
        "run_root": str(run_root),
        "metrics_completion_source": metrics_completion_source,
        "metrics_completion_outcome": metrics_completion_outcome,
        "metrics_completion_attempt_status": metrics_completion_attempt_status,
        "metrics_contract_status": metrics_contract_status,
        "metrics_contract_missing_metrics": metrics_contract_missing,
        "metrics_contract_ancillary_unavailable_metrics": metrics_contract_ancillary_unavailable,
        "required_metrics": {
            "mandatory": [
                "wall_time_seconds",
                "memory_peak_mb",
                "validation_output.file_count",
                "validation_output.bytes",
                "hazard_output.file_count",
                "hazard_output.bytes",
                "conditional_curve_row_count",
                "restartability_metadata.trajectory_plan_id",
                "restartability_metadata.reducer_plan_id",
                "restartability_metadata.trajectory_decision_counts",
                "restartability_metadata.reducer_decision_counts",
            ],
            "ancillary": [
                "validation_output_mode",
                "output_write_kind_seconds",
                "output_write_kind_bytes",
            ],
        },
        "required_run_root_entries": required_run_root["required"],
        "missing_run_root_entries": required_run_root["missing"],
        "required_run_root_entries_status": required_run_root["status"],
        "slurm_accounting_contract": {
            "status": "required_for_next_live_run",
            "required_fields": REQUIRED_SLURM_ACCOUNTING_FIELDS,
            "collection_command": "sacct -j <job_id> --format="
            + ",".join(REQUIRED_SLURM_ACCOUNTING_FIELDS),
            "notes": [
                "Collect the accounting fields from sacct after the job exits so the run can be reviewed without relying on scheduler memory.",
                "Do not infer evidence completion from the SLURM job state alone.",
            ],
        },
        "output_family_summaries": {
            "status": output_tier_status,
            "required_family_counts": dict(output_tier.REQUIRED_FAMILY_COUNTS),
            "measured_family_counts": output_family_counts,
            "required_family_counts_status": output_tier_report.get("required_family_counts_status", {}),
            "missing_required_families": missing_output_families,
            "curve_availability": output_tier_report.get("curve_availability", {}),
            "rebuildability_classification": output_tier_report.get("rebuildability_classification"),
            "blocked_reasons": output_tier_report.get("blocked_reasons", []),
            "omitted_output_implications": output_tier_report.get("omitted_output_implications", []),
        },
        "run_root_output_budget_audit": output_budget_report,
        "spatial_gis_artifact_paths": {
            "status": spatial_artifacts["status"],
            "manifest_path": spatial_artifacts["manifest_path"],
            "declared_artifacts": spatial_artifacts["declared_artifacts"],
            "declared_family_counts": spatial_artifacts["declared_family_counts"],
            "missing_reason": spatial_artifacts["missing_reason"],
        },
        "source_paths": {
            "run_root": str(run_root),
            "output_root": evidence.get("output_root"),
            "probe_manifest_path": evidence.get("probe_manifest_path"),
            "probe_metrics_json_path": str((run_root / "balfrin_probe_metrics.json").resolve()),
            "command_plan_path": evidence.get("command_plan_path"),
            "hazard_manifest_path": evidence.get("hazard_manifest_path"),
            "logs_root": str(run_root / "logs"),
        },
        "blocked_reasons": blocked_reasons,
        "claim_boundaries": {
            "operational_claims_allowed": False,
            "physical_probability_claims_allowed": False,
            "annual_frequency_claims_allowed": False,
            "risk_exposure_vulnerability_claims_allowed": False,
            "scale_up_authorized": False,
            "distributed_execution_authorized": False,
        },
    }
    report["summary"] = summarize_report(report)
    return report


def blocked_missing_run_root_report(
    run_root: Path,
    *,
    metrics_completion_attempt_status: str | None = None,
    metrics_completion_outcome: str | None = None,
) -> dict[str, Any]:
    required_run_root = _require_run_root_entries(run_root)
    outcome = metrics_report.classify_metrics_completion_outcome(
        report_status="blocked_missing_run_root",
        metrics_contract_status="blocked_missing_run_root",
        metrics_completion_source="blocked_missing_metrics",
        explicit_outcome=metrics_completion_outcome,
        attempt_status=metrics_completion_attempt_status,
    )
    report = {
        "schema_version": SCHEMA_VERSION,
        "gate_status": "blocked_missing_run_root",
        "preservation_gate_status": "blocked_missing_run_root",
        "future_live_run_would_satisfy_evidence_preservation_contract": False,
        "run_root_status": "missing_run_root",
        "run_root": str(run_root),
        "metrics_completion_source": "blocked_missing_metrics",
        "metrics_completion_outcome": outcome,
        "metrics_completion_attempt_status": metrics_completion_attempt_status,
        "missing_run_root_reason": f"run root does not exist: {run_root}",
        "metrics_contract_status": "blocked_missing_run_root",
        "metrics_contract_missing_metrics": [],
        "metrics_contract_ancillary_unavailable_metrics": [],
        "required_metrics": {
            "mandatory": [
                "wall_time_seconds",
                "memory_peak_mb",
                "validation_output.file_count",
                "validation_output.bytes",
                "hazard_output.file_count",
                "hazard_output.bytes",
                "conditional_curve_row_count",
                "restartability_metadata.trajectory_plan_id",
                "restartability_metadata.reducer_plan_id",
                "restartability_metadata.trajectory_decision_counts",
                "restartability_metadata.reducer_decision_counts",
            ],
            "ancillary": [
                "validation_output_mode",
                "output_write_kind_seconds",
                "output_write_kind_bytes",
            ],
        },
        "required_run_root_entries": required_run_root["required"],
        "missing_run_root_entries": required_run_root["missing"],
        "required_run_root_entries_status": required_run_root["status"],
        "slurm_accounting_contract": {
            "status": "required_for_next_live_run",
            "required_fields": REQUIRED_SLURM_ACCOUNTING_FIELDS,
            "collection_command": "sacct -j <job_id> --format="
            + ",".join(REQUIRED_SLURM_ACCOUNTING_FIELDS),
            "notes": [
                "Collect the accounting fields from sacct after the job exits so the run can be reviewed without relying on scheduler memory.",
                "Do not infer evidence completion from the SLURM job state alone.",
            ],
        },
        "output_family_summaries": {
            "status": "blocked_missing_run_root",
            "required_family_counts": dict(output_tier.REQUIRED_FAMILY_COUNTS),
            "measured_family_counts": {},
            "required_family_counts_status": {family: False for family in output_tier.REQUIRED_FAMILY_COUNTS},
            "missing_required_families": list(output_tier.REQUIRED_FAMILY_COUNTS),
            "curve_availability": {"available": False, "row_count": None},
            "rebuildability_classification": "blocked_missing_measured_output",
            "blocked_reasons": ["missing measured output root"],
            "omitted_output_implications": [
                "The run root is missing, so the preserved output families cannot be treated as evidence.",
            ],
        },
        "run_root_output_budget_audit": output_budget_audit.build_report(run_root),
        "spatial_gis_artifact_paths": {
            "status": "blocked_missing_run_root",
            "manifest_path": None,
            "declared_artifacts": [],
            "declared_family_counts": {},
            "missing_reason": f"run root does not exist: {run_root}",
        },
        "source_paths": {
            "run_root": str(run_root),
            "output_root": None,
            "probe_manifest_path": None,
            "probe_metrics_json_path": str((run_root / "balfrin_probe_metrics.json").resolve()),
            "command_plan_path": None,
            "hazard_manifest_path": None,
            "logs_root": str(run_root / "logs"),
        },
        "blocked_reasons": [f"run root does not exist: {run_root}"],
        "claim_boundaries": {
            "operational_claims_allowed": False,
            "physical_probability_claims_allowed": False,
            "annual_frequency_claims_allowed": False,
            "risk_exposure_vulnerability_claims_allowed": False,
            "scale_up_authorized": False,
            "distributed_execution_authorized": False,
        },
    }
    report["summary"] = summarize_report(report)
    return report


def summarize_report(report: dict[str, Any]) -> str:
    if report.get("gate_status") == "blocked_missing_run_root":
        return (
            "Balfrin preservation gate is blocked because the run root is missing: "
            f"{report.get('run_root')} (metrics_completion_source: blocked_missing_metrics)"
        )

    required_run_root = report.get("required_run_root_entries", [])
    missing_run_root = report.get("missing_run_root_entries", [])
    output_families = report.get("output_family_summaries", {})
    missing_families = output_families.get("missing_required_families", []) if isinstance(output_families, dict) else []
    spatial_artifacts = report.get("spatial_gis_artifact_paths", {})
    declared_count = len(spatial_artifacts.get("declared_artifacts", [])) if isinstance(spatial_artifacts, dict) else 0
    return (
        "Balfrin preservation gate "
        f"{report.get('gate_status')}: "
        f"{len(missing_run_root)} missing run-root entries, "
        f"{len(report.get('metrics_contract_missing_metrics', []))} missing mandatory metrics, "
        f"{len(missing_families)} missing output families, "
        f"{declared_count} declared GIS artifact paths preserved from the manifest, "
        f"{len(required_run_root)} required run-root entries checked, "
        f"metrics_completion_source={report.get('metrics_completion_source', 'unknown')}."
    )


def render_text_report(report: dict[str, Any]) -> str:
    lines = [
        "Balfrin Probe Preservation Gate",
        f"schema_version: {report.get('schema_version', 'unknown')}",
        f"gate_status: {report.get('gate_status', 'unknown')}",
        f"run_root_status: {report.get('run_root_status', 'unknown')}",
        f"run_root: {report.get('run_root', 'unknown')}",
        f"metrics_completion_source: {report.get('metrics_completion_source', 'unknown')}",
        f"metrics_completion_outcome: {report.get('metrics_completion_outcome', 'unknown')}",
        f"metrics_completion_attempt_status: {report.get('metrics_completion_attempt_status', 'unknown')}",
        f"metrics_contract_status: {report.get('metrics_contract_status', 'unknown')}",
        f"summary: {report.get('summary', '')}",
    ]

    if report.get("blocked_reasons"):
        lines.append("blocked_reasons:")
        for reason in report.get("blocked_reasons", []):
            lines.append(f"  - {reason}")

    lines.append("required_metrics:")
    for group_name, metrics in report.get("required_metrics", {}).items():
        lines.append(f"  {group_name}:")
        for metric in metrics:
            lines.append(f"    - {metric}")

    lines.append("required_run_root_entries:")
    for entry in report.get("required_run_root_entries", []):
        lines.append(
            f"  - {entry.get('path')} ({entry.get('kind')}): exists={entry.get('exists')} absolute_path={entry.get('absolute_path')}"
        )

    slurm = report.get("slurm_accounting_contract", {})
    lines.append("slurm_accounting_contract:")
    lines.append(f"  status: {slurm.get('status', 'unknown')}")
    lines.append(f"  collection_command: {slurm.get('collection_command', '')}")
    lines.append("  required_fields:")
    for field in slurm.get("required_fields", []):
        lines.append(f"    - {field}")

    output_families = report.get("output_family_summaries", {})
    lines.append("output_family_summaries:")
    lines.append(f"  status: {output_families.get('status', 'unknown')}")
    lines.append(f"  required_family_counts: {output_families.get('required_family_counts', {})}")
    lines.append(f"  measured_family_counts: {output_families.get('measured_family_counts', {})}")
    lines.append(f"  missing_required_families: {output_families.get('missing_required_families', [])}")
    lines.append(f"  curve_availability: {output_families.get('curve_availability', {})}")
    lines.append(f"  rebuildability_classification: {output_families.get('rebuildability_classification', '')}")

    budget_audit = report.get("run_root_output_budget_audit", {})
    lines.append("run_root_output_budget_audit:")
    lines.append(f"  audit_status: {budget_audit.get('audit_status', 'unknown')}")
    lines.append(f"  budget_profile_id: {budget_audit.get('budget_profile_id', 'unknown')}")
    lines.append(f"  summary: {budget_audit.get('summary', '')}")

    spatial = report.get("spatial_gis_artifact_paths", {})
    lines.append("spatial_gis_artifact_paths:")
    lines.append(f"  status: {spatial.get('status', 'unknown')}")
    lines.append(f"  manifest_path: {spatial.get('manifest_path')}")
    lines.append(f"  declared_family_counts: {spatial.get('declared_family_counts', {})}")
    lines.append("  declared_artifacts:")
    for entry in spatial.get("declared_artifacts", []):
        lines.append(
            f"    - {entry.get('kind')}: {entry.get('path')} declared={entry.get('declared')}"
        )

    source_paths = report.get("source_paths", {})
    lines.append("source_paths:")
    for key in (
        "run_root",
        "output_root",
        "probe_manifest_path",
        "probe_metrics_json_path",
        "command_plan_path",
        "hazard_manifest_path",
        "logs_root",
    ):
        lines.append(f"  {key}: {source_paths.get(key)}")

    claim_boundaries = report.get("claim_boundaries", {})
    lines.append("claim_boundaries:")
    for key in (
        "operational_claims_allowed",
        "physical_probability_claims_allowed",
        "annual_frequency_claims_allowed",
        "risk_exposure_vulnerability_claims_allowed",
        "scale_up_authorized",
        "distributed_execution_authorized",
    ):
        lines.append(f"  {key}: {claim_boundaries.get(key)}")
    return "\n".join(lines)


def materialize_artifacts(
    report: dict[str, Any],
    *,
    json_output: Path | None = None,
    text_output: Path | None = None,
    artifact_dir: Path | None = None,
) -> None:
    if artifact_dir is not None:
        artifact_dir.mkdir(parents=True, exist_ok=True)
        json_output = json_output or (artifact_dir / f"{REPORT_BASENAME}.json")
        text_output = text_output or (artifact_dir / f"{REPORT_BASENAME}.txt")
    if json_output is not None:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if text_output is not None:
        text_output.parent.mkdir(parents=True, exist_ok=True)
        text_output.write_text(render_text_report(report), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        evidence_override = _load_json(args.evidence_json)
        report = build_report(evidence_override, run_root=args.run_root)
    except (OSError, ValueError) as exc:
        print(f"balfrin preservation gate error: {exc}", file=sys.stderr)
        return 2

    materialize_artifacts(
        report,
        json_output=args.json_output,
        text_output=args.text_output,
        artifact_dir=args.artifact_dir,
    )

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text_report(report))
    return 0 if report["gate_status"] == "ready_for_demonstration_evidence" else 2


if __name__ == "__main__":
    raise SystemExit(main())
