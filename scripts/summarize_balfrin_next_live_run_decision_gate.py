#!/usr/bin/env python3
"""Decide the next authorized live Balfrin action from measured evidence.

This helper compares five next-action families:

- metrics-completion rerun
- smallest bounded multi-zone probe
- second-site public-context progress
- physical-evidence acquisition
- hazard-builder optimization

It stays read-only, synthesizes the current evidence helpers and tracked
fixtures into one deterministic decision report, and fails closed whenever the
required measured inputs or Balfrin access prerequisites are missing.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import generate_balfrin_multi_release_zone_demo_handoff as multi_zone_handoff  # noqa: E402
from scripts import summarize_balfrin_target_area_candidate_stability as candidate_stability  # noqa: E402
from scripts import summarize_balfrin_evidence_bundle as evidence_bundle  # noqa: E402
from scripts import summarize_balfrin_probe_metrics_report as metrics_report  # noqa: E402
from scripts import summarize_balfrin_probe_preservation_gate as preservation_gate  # noqa: E402
from scripts import summarize_management_aoi_scenario_pressure as scenario_pressure  # noqa: E402
from scripts import summarize_multi_zone_reducer_pressure as reducer_pressure  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "balfrin_next_live_run_decision_gate_v1"
REPORT_BASENAME = "balfrin_next_live_run_decision_gate_v1"
DEFAULT_ARTIFACT_DIR = ROOT / "validation/private/tschamut_public_pilot/balfrin_next_live_run_decision_gate_v1"
DEFAULT_EVIDENCE_BUNDLE = ROOT / "tests/fixtures/balfrin_next_live_run_decision_gate/default_bundle.json"
DEFAULT_PRESERVATION_RUN_ROOT = ROOT / "tests/fixtures/balfrin_probe_metrics_contract/complete_run_root"
DEFAULT_REDUCER_PRESSURE_ROOT = Path("/tmp/rust_rockfall/balfrin_next_live_run_decision_gate_v1/reducer_pressure")
DIAGNOSTIC_QUEUE_SNAPSHOT_MAX_AGE_MINUTES = 30
DIAGNOSTIC_POSTPROC_PARTITION_FILL_LIMIT_MINUTES = 360
REDUCER_PRESSURE_REGENERATION_COMMAND = (
    "PYENV_VERSION=system uv run python scripts/validate_multi_zone_reducer_pressure_gate.py "
    "--materialize-root /tmp/rust_rockfall/balfrin_next_live_run_decision_gate_v1/reducer_pressure --format json"
)

REQUIRED_BUNDLE_KEYS = (
    "probe_metrics_report",
    "preservation_gate_report",
    "multi_zone_reducer_pressure_report",
    "multi_zone_handoff_report",
)

OPTION_METRICS = "metrics_completion_rerun"
OPTION_REDUCER = "reducer_pressure_optimization"
OPTION_MULTI_ZONE = "smallest_bounded_multi_zone_probe"
OPTION_DEFER = "defer_portability_or_physical_evidence"
OPTION_SECOND_SITE = "second_site_public_context_progress"
OPTION_PHYSICAL_EVIDENCE = "physical_evidence_acquisition"
OPTION_HAZARD_OPTIMIZATION = "hazard_builder_accumulation_optimization"

RANKED_ACTION_OPTIONS = (
    OPTION_METRICS,
    OPTION_REDUCER,
    OPTION_MULTI_ZONE,
    OPTION_SECOND_SITE,
    OPTION_PHYSICAL_EVIDENCE,
    OPTION_HAZARD_OPTIMIZATION,
)
NEXT_ACTION_LABELS = {
    OPTION_METRICS: "metrics completion",
    OPTION_REDUCER: "reducer-pressure optimization",
    OPTION_MULTI_ZONE: "smallest multi-zone measurement",
    OPTION_DEFER: "real second-site staging",
    OPTION_SECOND_SITE: "real second-site staging",
    OPTION_PHYSICAL_EVIDENCE: "physical-evidence intake",
    OPTION_HAZARD_OPTIMIZATION: "hazard-builder optimization",
}
REDUCER_FIRST_PROBE_RANKING = (
    {
        "rank": 1,
        "candidate_id": "reducer_pressure_optimization_probe",
        "action_id": "summarize_multi_zone_reducer_pressure",
        "category": "reducer_pressure",
        "probe_scope": "scratch_local_and_fixture_backed",
        "blocker": "reducer_pressure_and_replay_metadata_growth_remain_the_next_bottlenecks",
        "expected_evidence_gain": (
            "compact reducer manifest pressure and explicit replay-critical family budgets for larger multi-zone batches"
        ),
        "required_pre_submit_gates": [
            "measured_reducer_pressure_baseline",
            "replay_critical_families_retained",
            "merge_order_deterministic",
            "no_live_submission",
        ],
        "evidence_basis": [
            "tb312_four_zone_postproc_probe",
            "multi_zone_reducer_pressure_probe",
        ],
        "summary": (
            "Optimize reducer pressure next because the measured regional split comparison is complete and the reducer "
            "helper still shows manifest and replay metadata pressure as the next visible bottleneck."
        ),
    },
    {
        "rank": 2,
        "candidate_id": "scenario_batching_pressure_probe",
        "action_id": "measure_scenario_storage_output_tier_pressure",
        "category": "scenario_cardinality",
        "probe_scope": "scratch_local_and_fixture_backed",
        "blocker": "scenario_cardinality_and_manifest_size_are_the_first_planning_bottlenecks",
        "expected_evidence_gain": (
            "measured scenario-table growth, CSV/manifest bytes, and batch-count pressure for compact candidate batches"
        ),
        "required_pre_submit_gates": [
            "deterministic_candidate_bundle",
            "compact_scenario_table",
            "fixture_or_scratch_local_measurement_root",
            "no_live_balfrin_submission",
        ],
        "evidence_basis": [
            "management_aoi_multi_zone_run_failed_closed",
            "swiss_scale_projection_scenario_cardinality_rank",
        ],
        "summary": (
            "Batch scenarios next if the regional split retry is not the immediate target, because scenario cardinality "
            "and manifest size are the first planning bottlenecks in the projection surface."
        ),
    },
    {
        "rank": 3,
        "candidate_id": "local_candidate_evidence_probe",
        "action_id": "summarize_balfrin_target_area_candidate_stability",
        "category": "local_evidence",
        "probe_scope": "scratch_local",
        "blocker": "no_larger_measured_multi_zone_hazard_execution_exists_yet",
        "expected_evidence_gain": (
            "scratch-local candidate stability and accumulation-pressure evidence to refine the next live probe"
        ),
        "required_pre_submit_gates": [
            "scratch_local_only",
            "deterministic_inputs",
            "placeholder_scan_clear",
            "no_live_submission",
        ],
        "evidence_basis": [
            "tb189_candidate_stability_sweep",
            "tb181_real_terrain_candidate_sweep",
        ],
        "summary": (
            "Collect more local evidence last because it can refine the next live probe, but it does not outrank a "
            "live bounded retry or the measured scenario/reducer bottlenecks."
        ),
    },
)


class BalfrinNextLiveRunDecisionGateError(ValueError):
    """User-facing Balfrin decision-gate error."""


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-json", type=Path, default=None, help="Optional evidence bundle JSON override.")
    parser.add_argument(
        "--balfrin-access-preflight-json",
        type=Path,
        default=None,
        help="Optional current Balfrin access preflight JSON to thread into the decision refresh.",
    )
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


def describe_next_action(action_id: str, default: str = "physical-evidence intake") -> str:
    return NEXT_ACTION_LABELS.get(str(action_id), default)


def build_reducer_first_probe_ranking() -> list[dict[str, Any]]:
    return [dict(row) for row in REDUCER_FIRST_PROBE_RANKING]


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    try:
        report = build_report(
            load_evidence_override(args.evidence_json),
            balfrin_access_preflight=load_access_preflight(args.balfrin_access_preflight_json),
        )
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


def load_access_preflight(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    if not path.exists():
        raise BalfrinNextLiveRunDecisionGateError(f"Balfrin access preflight is missing: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise BalfrinNextLiveRunDecisionGateError("Balfrin access preflight must be a JSON object")
    return payload


def build_report(
    evidence_override: dict[str, Any] | None = None,
    *,
    balfrin_access_preflight: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if evidence_override is None:
        try:
            evidence_override = build_current_evidence_bundle(balfrin_access_preflight=balfrin_access_preflight)
        except FileNotFoundError as exc:
            return blocked_reducer_pressure_scratch_report(exc)

    if isinstance(evidence_override.get("decision_gate_report"), dict):
        return dict(evidence_override["decision_gate_report"])

    if balfrin_access_preflight is not None:
        evidence_override = dict(evidence_override)
        evidence_override["balfrin_access"] = build_balfrin_access_from_preflight(balfrin_access_preflight)

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
        "ranked_actions": build_ranked_actions(option_assessments),
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
        "multi_zone_balfrin_evidence": evidence_bundle.build_multi_zone_balfrin_evidence(
            bundle.get("multi_zone_balfrin_evidence")
        ),
        "scientific_value": _copy_mapping(bundle.get("scientific_value")),
        "portability_value": _copy_mapping(bundle.get("portability_value")),
        "balfrin_access": _copy_mapping(bundle.get("balfrin_access")),
        "second_site_progress": _copy_mapping(bundle.get("second_site_progress")),
        "physical_evidence_acquisition": _copy_mapping(bundle.get("physical_evidence_acquisition")),
        "hazard_builder_optimization": _copy_mapping(bundle.get("hazard_builder_optimization")),
        "scenario_batching": _copy_mapping(bundle.get("scenario_batching")),
        "candidate_stability": _copy_mapping(bundle.get("candidate_stability")),
        "post_tb_221_evidence": _safe_list(bundle.get("post_tb_221_evidence")),
        "source_paths": _copy_mapping(bundle.get("source_paths")),
    }


def build_current_evidence_bundle(
    *,
    balfrin_access_preflight: dict[str, Any] | None = None,
) -> dict[str, Any]:
    default_bundle = _load_json(DEFAULT_EVIDENCE_BUNDLE)
    if default_bundle is None:
        raise BalfrinNextLiveRunDecisionGateError(f"default evidence bundle is missing: {DEFAULT_EVIDENCE_BUNDLE}")
    current_bundle = evidence_bundle.build_current_report()

    with tempfile.TemporaryDirectory(dir="/tmp") as tmpdir:
        reducer_root = Path(tmpdir) / "reducer_pressure"
        reducer_pressure.materialize_probe_root(reducer_root)
        reducer_report = reducer_pressure.build_report(reducer_root)
        scenario_report = scenario_pressure.build_report(
            output_root=Path(tmpdir) / "management_aoi_scenario_pressure",
            scenario_output_root=Path(tmpdir) / "management_aoi_scenario_table",
        )
        candidate_report = candidate_stability.build_report(output_root=Path(tmpdir) / "candidate_stability")

    return {
        "schema_version": str(default_bundle.get("schema_version") or "balfrin_next_live_run_decision_gate_bundle_v1"),
        "probe_metrics_report": _copy_mapping(current_bundle.get("probe_metrics")),
        "preservation_gate_report": preservation_gate.build_report(run_root=DEFAULT_PRESERVATION_RUN_ROOT),
        "multi_zone_reducer_pressure_report": reducer_report,
        "multi_zone_handoff_report": multi_zone_handoff.build_report(),
        "multi_zone_balfrin_evidence": evidence_bundle.build_multi_zone_balfrin_evidence(
            current_bundle.get("multi_zone_balfrin_evidence")
        ),
        "scientific_value": _copy_mapping(default_bundle.get("scientific_value")),
        "portability_value": _copy_mapping(default_bundle.get("portability_value")),
        "balfrin_access": build_balfrin_access_from_preflight(balfrin_access_preflight)
        if balfrin_access_preflight is not None
        else _copy_mapping(default_bundle.get("balfrin_access")),
        "second_site_progress": _copy_mapping(default_bundle.get("second_site_progress")),
        "physical_evidence_acquisition": _copy_mapping(default_bundle.get("physical_evidence_acquisition")),
        "hazard_builder_optimization": _copy_mapping(default_bundle.get("hazard_builder_optimization")),
        "scenario_batching": scenario_report,
        "candidate_stability": candidate_report,
        "post_tb_221_evidence": _safe_list(default_bundle.get("post_tb_221_evidence")),
        "source_paths": _copy_mapping(default_bundle.get("source_paths")),
    }


def build_balfrin_access_from_preflight(access_report: dict[str, Any]) -> dict[str, Any]:
    status = str(access_report.get("status") or "blocked_missing_access_preflight")
    hygiene = _copy_mapping(access_report.get("remote_checkout_hygiene"))
    ready = bool(access_report.get("ready_for_pre_submit")) and status == "ready_for_read_only_collection"
    blockers: list[str] = []
    if not ready:
        blockers.append(status)
        hygiene_status = str(hygiene.get("status") or "")
        if hygiene_status and hygiene_status != "pass":
            blockers.append(f"remote_checkout_hygiene:{hygiene_status}")
    return {
        "status": status,
        "path_state": "ready_for_pre_submit" if ready else "blocked",
        "ssh_access_state": "ready" if ready else status,
        "live_submission_authorized": bool(access_report.get("live_submission_authorized")),
        "blockers": blockers,
        "remote_head": access_report.get("remote_head"),
        "remote_checkout_hygiene_status": hygiene.get("status"),
        "remote_dirty_path_count": hygiene.get("dirty_path_count"),
        "ready_for_pre_submit": bool(access_report.get("ready_for_pre_submit")),
        "diagnostic_run_planner": build_diagnostic_run_planner(access_report),
        "summary": (
            "Balfrin access preflight is current, remote checkout hygiene passed, and the checkout is ready for pre-submit gates."
            if ready
            else "Balfrin access preflight is not ready for pre-submit gates."
        ),
    }


def current_git_head() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return None
    head = result.stdout.strip()
    return head if result.returncode == 0 and head else None


def _parse_datetime(value: Any) -> dt.datetime | None:
    if not value:
        return None
    text = str(value).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = dt.datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.UTC)
    return parsed.astimezone(dt.UTC)


def _scheduler_stdout(access_report: dict[str, Any]) -> str:
    for check in access_report.get("checked_commands") or []:
        if isinstance(check, dict) and check.get("name") == "scheduler_query":
            return str(check.get("stdout") or "")
    return ""


def parse_postproc_queue_snapshot(snapshot: Any) -> dict[str, Any]:
    if isinstance(snapshot, dict):
        return {
            "status": "parsed",
            "idle_nodes": int(snapshot.get("idle_nodes") or 0),
            "total_nodes": int(snapshot.get("total_nodes") or snapshot.get("idle_nodes") or 0),
            "running_jobs": int(snapshot.get("running_jobs") or 0),
            "pending_jobs": int(snapshot.get("pending_jobs") or 0),
            "current_user_jobs": int(snapshot.get("current_user_jobs") or 0),
            "partition": str(snapshot.get("partition") or "postproc"),
            "captured_at": snapshot.get("captured_at"),
        }
    text = str(snapshot or "")
    if not text.strip():
        return {"status": "missing", "idle_nodes": None, "total_nodes": None}
    idle_nodes = 0
    total_nodes = 0
    running_jobs = 0
    pending_jobs = 0
    current_user_jobs = 0
    captured_at = None
    for raw_line in text.splitlines():
        line = raw_line.strip()
        lower = line.lower()
        if "=" in line and not line.startswith("__"):
            key, value = [part.strip() for part in line.split("=", 1)]
            if key == "captured_at":
                captured_at = value
            elif key == "running_jobs":
                running_jobs = int(value or 0)
            elif key == "pending_jobs":
                pending_jobs = int(value or 0)
            elif key == "current_user_jobs":
                current_user_jobs = int(value or 0)
            elif key == "idle_nodes":
                idle_nodes = int(value or 0)
            elif key == "total_nodes":
                total_nodes = int(value or 0)
            continue
        if lower.startswith("captured at:"):
            captured_at = line.split(":", 1)[1].strip()
        if lower.startswith("- captured at:"):
            captured_at = line.split(":", 1)[1].strip()
        if lower.startswith("- running jobs in `postproc`:"):
            running_jobs = int(line.rsplit(":", 1)[1].strip().split()[0])
        elif lower.startswith("- pending jobs in `postproc`:"):
            pending_jobs = int(line.rsplit(":", 1)[1].strip().split()[0])
        elif lower.startswith("- current `olifu` jobs in `postproc`:"):
            current_user_jobs = int(line.rsplit(":", 1)[1].strip().split()[0])
        elif "|" in line and "`idle`" in line:
            idle_nodes = int(line.rsplit("|", 1)[1].strip())
            total_nodes += idle_nodes
        elif "|" in line and any(state in line for state in ("`alloc`", "`mix`", "`resv`")):
            total_nodes += int(line.rsplit("|", 1)[1].strip())
        elif "|" in line and not line.startswith("|"):
            parts = [part.strip() for part in line.split("|")]
            if len(parts) >= 2 and parts[1].isdigit():
                state = parts[0].lower()
                node_count = int(parts[1])
                total_nodes += node_count
                if state == "idle":
                    idle_nodes += node_count
        elif "|" in line and not line.startswith("__"):
            parts = [part.strip() for part in line.split("|")]
            if len(parts) >= 3:
                state = parts[2].upper()
                if state.startswith("R"):
                    running_jobs += 1
                elif state.startswith("P"):
                    pending_jobs += 1
                if len(parts) >= 2 and parts[1] == "olifu":
                    current_user_jobs += 1
    return {
        "status": "parsed",
        "idle_nodes": idle_nodes,
        "total_nodes": total_nodes or idle_nodes,
        "running_jobs": running_jobs,
        "pending_jobs": pending_jobs,
        "current_user_jobs": current_user_jobs,
        "partition": "postproc",
        "captured_at": captured_at,
    }


def build_diagnostic_run_planner(
    access_report: dict[str, Any],
    *,
    diagnostic_job_count: int = 1,
    expected_wall_minutes: int = 30,
    now: dt.datetime | None = None,
    local_head: str | None = None,
) -> dict[str, Any]:
    now = now or dt.datetime.now(dt.UTC)
    if now.tzinfo is None:
        now = now.replace(tzinfo=dt.UTC)
    local_head = local_head if local_head is not None else current_git_head()
    snapshot = parse_postproc_queue_snapshot(
        access_report.get("postproc_queue_snapshot")
        or access_report.get("postproc_queue_snapshot_text")
        or _scheduler_stdout(access_report)
    )
    captured_at = _parse_datetime(access_report.get("captured_at") or snapshot.get("captured_at"))
    snapshot_age_minutes = None
    stale_preflight = captured_at is None
    if captured_at is not None:
        snapshot_age_minutes = max(0.0, (now.astimezone(dt.UTC) - captured_at).total_seconds() / 60.0)
        stale_preflight = snapshot_age_minutes > DIAGNOSTIC_QUEUE_SNAPSHOT_MAX_AGE_MINUTES

    idle_nodes = snapshot.get("idle_nodes")
    total_nodes = snapshot.get("total_nodes")
    pending_jobs = snapshot.get("pending_jobs")
    remote_head = access_report.get("remote_head") or dict(access_report.get("remote_checkout_hygiene") or {}).get("remote_head")
    remote_head_mismatch = bool(local_head and remote_head and local_head != remote_head)
    expected_walltime_ok = expected_wall_minutes <= DIAGNOSTIC_POSTPROC_PARTITION_FILL_LIMIT_MINUTES
    partition_fill_minutes = (
        expected_wall_minutes
        if isinstance(total_nodes, int) and total_nodes > 0 and diagnostic_job_count >= total_nodes
        else 0
    )
    six_hour_partition_fill_ok = partition_fill_minutes <= DIAGNOSTIC_POSTPROC_PARTITION_FILL_LIMIT_MINUTES

    blockers: list[str] = []
    if access_report.get("status") != "ready_for_read_only_collection" or not access_report.get("ready_for_pre_submit"):
        blockers.append(f"access_preflight:{access_report.get('status') or 'missing'}")
    if stale_preflight:
        blockers.append("stale_preflight_or_missing_timestamp")
    if remote_head_mismatch:
        blockers.append("remote_head_mismatch")
    if not expected_walltime_ok:
        blockers.append("expected_walltime_exceeds_six_hours")
    if not six_hour_partition_fill_ok:
        blockers.append("partition_fill_exceeds_six_hours")
    if snapshot.get("status") != "parsed" or not isinstance(idle_nodes, int):
        blockers.append("queue_snapshot_unavailable")

    if blockers:
        classification = "unknown" if any(item in blockers for item in ("stale_preflight_or_missing_timestamp", "remote_head_mismatch", "queue_snapshot_unavailable")) else "defer_due_to_capacity"
    elif isinstance(pending_jobs, int) and pending_jobs > 0 and (not isinstance(idle_nodes, int) or idle_nodes < diagnostic_job_count):
        classification = "defer_due_to_capacity"
        blockers.append("pending_postproc_jobs")
    elif isinstance(idle_nodes, int) and idle_nodes >= diagnostic_job_count and diagnostic_job_count > 1:
        classification = "run_batch_now"
    elif isinstance(idle_nodes, int) and idle_nodes >= 1:
        classification = "run_now"
    else:
        classification = "run_soon"

    return {
        "schema_version": "balfrin_diagnostic_run_planner_v1",
        "classification": classification,
        "diagnostic_job_count": diagnostic_job_count,
        "expected_wall_minutes": expected_wall_minutes,
        "partition": "postproc",
        "queue_snapshot": snapshot,
        "snapshot_age_minutes": round(snapshot_age_minutes, 3) if snapshot_age_minutes is not None else None,
        "stale_preflight": stale_preflight,
        "remote_head": remote_head,
        "local_head": local_head,
        "remote_head_mismatch": remote_head_mismatch,
        "expected_walltime_ok": expected_walltime_ok,
        "six_hour_partition_fill_ok": six_hour_partition_fill_ok,
        "partition_fill_minutes": partition_fill_minutes,
        "blockers": blockers,
        "summary": diagnostic_run_planner_summary(classification, diagnostic_job_count, expected_wall_minutes, blockers),
    }


def diagnostic_run_planner_summary(
    classification: str,
    diagnostic_job_count: int,
    expected_wall_minutes: int,
    blockers: list[str],
) -> str:
    if classification == "run_batch_now":
        return f"The postproc queue supports a {diagnostic_job_count}-job diagnostic batch now for the expected {expected_wall_minutes} minute wall time."
    if classification == "run_now":
        return f"The postproc queue supports one bounded diagnostic job now for the expected {expected_wall_minutes} minute wall time."
    if classification == "run_soon":
        return "The postproc queue is occupied but has no hard local blocker; retry the capacity snapshot before submitting."
    if classification == "defer_due_to_capacity":
        return "Capacity or six-hour partition-fill checks say to defer: " + ", ".join(blockers)
    return "The diagnostic queue decision is unknown until the preflight, remote head, and queue snapshot are current."


def build_criteria(bundle: dict[str, Any]) -> dict[str, Any]:
    metrics = bundle["sections"]["probe_metrics_report"]
    preservation = bundle["sections"]["preservation_gate_report"]
    reducer = bundle["sections"]["multi_zone_reducer_pressure_report"]
    package = bundle["sections"]["multi_zone_handoff_report"]
    multi_zone_evidence = bundle["multi_zone_balfrin_evidence"]
    scientific_value = bundle["scientific_value"]
    portability_value = bundle["portability_value"]
    balfrin_access = bundle["balfrin_access"]
    second_site = bundle["second_site_progress"]
    physical_evidence = bundle["physical_evidence_acquisition"]
    hazard_optimization = bundle["hazard_builder_optimization"]
    scenario_batching = bundle["scenario_batching"]
    candidate_stability_report = bundle["candidate_stability"]

    missing_metrics = _safe_list(metrics.get("metrics_contract_missing_metrics"))
    next_run_required = _safe_list(metrics.get("metrics_remediation", {}).get("next_run_required_metrics"))
    metrics_completion_source = _status(metrics.get("metrics_completion_source"), "blocked_missing_metrics")
    metrics_completion_outcome = _status(metrics.get("metrics_completion_outcome"), "blocked")
    metrics_completion_attempt_status = metrics.get("metrics_completion_attempt_status")
    metrics_evidence_state = _copy_mapping(metrics.get("metrics_evidence_state"))
    preservation_ready = preservation.get("gate_status") == "ready_for_demonstration_evidence"
    reducer_blocked = _bool(reducer.get("multi_zone_dry_run_blocked"))
    output_pressure = _copy_mapping(package.get("pressure_checkpoints", {}).get("output_pressure"))
    multi_zone_ready = (
        package.get("package_status") == "ready"
        and not reducer_blocked
        and output_pressure.get("status") in {"ready", "acceptable"}
    )

    missing_target_area_metrics = build_missing_target_area_metrics_criteria(
        metrics=metrics,
        missing_metrics=missing_metrics,
        next_run_required=next_run_required,
        metrics_completion_source=metrics_completion_source,
        metrics_completion_outcome=metrics_completion_outcome,
        metrics_completion_attempt_status=metrics_completion_attempt_status,
        metrics_evidence_state=metrics_evidence_state,
    )

    return {
        "missing_target_area_metrics": missing_target_area_metrics,
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
        "multi_zone_balfrin_evidence": build_multi_zone_balfrin_evidence_criteria(multi_zone_evidence),
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
        "balfrin_access": build_balfrin_access_criteria(balfrin_access),
        "second_site_progress": {
            "status": _status(second_site.get("status"), "blocked_missing_inputs"),
            "path_state": _status(second_site.get("path_state"), "blocked"),
            "blockers": _safe_list(second_site.get("blockers")),
            "follow_up_task": str(second_site.get("follow_up_task") or "TB-231"),
            "summary": str(second_site.get("summary") or ""),
        },
        "physical_evidence_acquisition": {
            "status": _status(physical_evidence.get("status"), "blocked_missing_inputs"),
            "path_state": _status(physical_evidence.get("path_state"), "blocked"),
            "blockers": _safe_list(physical_evidence.get("blockers")),
            "follow_up_task": str(physical_evidence.get("follow_up_task") or "TB-233"),
            "summary": str(physical_evidence.get("summary") or ""),
        },
        "hazard_builder_optimization": {
            "status": _status(hazard_optimization.get("status"), "fixture_backed"),
            "path_state": _status(hazard_optimization.get("path_state"), "fixture_backed"),
            "blockers": _safe_list(hazard_optimization.get("blockers")),
            "follow_up_task": str(hazard_optimization.get("follow_up_task") or "TB-229"),
            "summary": str(hazard_optimization.get("summary") or ""),
        },
        "scenario_batching_cap": build_scenario_batching_cap_criteria(scenario_batching),
        "candidate_stability_result": build_candidate_stability_result_criteria(candidate_stability_report),
        "reducer_first_ranked_evidence": build_reducer_first_ranked_evidence(
            reducer=reducer,
            scenario_batching=scenario_batching,
            candidate_stability_report=candidate_stability_report,
        ),
        "post_tb_221_evidence": {
            "status": "recorded",
            "evidence_items": bundle["post_tb_221_evidence"],
        },
    }


def build_scenario_batching_cap_criteria(report: dict[str, Any]) -> dict[str, Any]:
    pressure = _copy_mapping(report.get("scenario_generation_pressure"))
    expansion_counts = pressure.get("candidate_expansion_counts")
    counts = [int(item) for item in expansion_counts] if isinstance(expansion_counts, list) else []
    scenario_table = _copy_mapping(report.get("scenario_table_generation"))
    smoke = _copy_mapping(report.get("prepared_pilot_smoke_handoff"))
    return {
        "status": _status(report.get("scenario_pressure_status"), "blocked_missing_inputs"),
        "scenario_batching_cap": max(counts) if counts else None,
        "candidate_expansion_counts": counts,
        "scenario_row_count": scenario_table.get("scenario_row_count"),
        "prepared_pilot_smoke_status": _status(smoke.get("smoke_status"), "blocked_missing_inputs"),
        "summary": (
            "Scenario batching is ready for scratch/local planning through the current candidate expansion cap."
            if report.get("scenario_pressure_status") == "ready"
            else str(report.get("blocked_reason") or "Scenario batching evidence is unavailable.")
        ),
    }


def build_candidate_stability_result_criteria(report: dict[str, Any]) -> dict[str, Any]:
    summary = _copy_mapping(report.get("candidate_stability_summary"))
    selected = _copy_mapping(report.get("selected_candidate_assessment"))
    stable_region = _copy_mapping(summary.get("stable_candidate_region"))
    return {
        "status": _status(report.get("candidate_metrics_status"), "blocked_missing_inputs"),
        "stability_status": _status(summary.get("stability_status"), "blocked_missing_inputs"),
        "selected_candidate_id": selected.get("candidate_release_zone_id"),
        "selected_candidate_class": selected.get("candidate_stability_class"),
        "selected_candidate_status": selected.get("selected_candidate_status"),
        "stability_score": selected.get("stability_score"),
        "minimum_retention_fraction": selected.get("minimum_retention_fraction"),
        "variant_count": summary.get("variant_count"),
        "stable_candidate_cell_count": stable_region.get("cell_count"),
        "summary": str(
            _copy_mapping(selected.get("selected_candidate_recommendation")).get("reason")
            or "Candidate stability evidence is unavailable."
        ),
    }


def build_reducer_first_ranked_evidence(
    *,
    reducer: dict[str, Any],
    scenario_batching: dict[str, Any],
    candidate_stability_report: dict[str, Any],
) -> dict[str, Any]:
    scenario_cap = build_scenario_batching_cap_criteria(scenario_batching)
    candidate_result = build_candidate_stability_result_criteria(candidate_stability_report)
    status_by_action = {
        "summarize_multi_zone_reducer_pressure": _status(reducer.get("probe_status"), "blocked_missing_inputs"),
        "measure_scenario_storage_output_tier_pressure": scenario_cap["status"],
        "summarize_balfrin_target_area_candidate_stability": candidate_result["status"],
    }
    contextual_fields = {
        "measure_scenario_storage_output_tier_pressure": {
            "scenario_batching_cap": scenario_cap["scenario_batching_cap"],
        },
        "summarize_balfrin_target_area_candidate_stability": {
            "selected_candidate_id": candidate_result["selected_candidate_id"],
            "selected_candidate_class": candidate_result["selected_candidate_class"],
        },
    }
    ladder = []
    for row in build_reducer_first_probe_ranking():
        action_id = str(row["action_id"])
        ladder.append(
            {
                "rank": row["rank"],
                "action_id": action_id,
                "category": row["category"],
                "status": status_by_action.get(action_id, "blocked_missing_inputs"),
                "summary": row["summary"],
                **contextual_fields.get(action_id, {}),
            }
        )
    return {
        "status": "ready",
        "ranked_next_probe_ladder": ladder,
    }


def build_missing_target_area_metrics_criteria(
    *,
    metrics: dict[str, Any],
    missing_metrics: list[str],
    next_run_required: list[str],
    metrics_completion_source: str,
    metrics_completion_outcome: str,
    metrics_completion_attempt_status: Any,
    metrics_evidence_state: dict[str, Any],
) -> dict[str, Any]:
    if metrics_completion_source == "blocked_pre_submit":
        status = "blocked_pre_submit"
        summary = "The latest metrics-completion path is blocked before submit; no live job or measured run-root evidence is promoted."
    elif metrics_completion_source == "failed_closed" or metrics_completion_outcome == "failed_closed":
        status = "failed_closed"
        summary = "The latest metrics-completion attempt failed closed; no completed preservation-checked metrics record is promoted."
    elif metrics_completion_source == "blocked_missing_metrics" and missing_metrics:
        status = "missing"
        summary = "Target-area metrics remain incomplete and can be closed by the next measured rerun."
    elif metrics_completion_source == "blocked_missing_metrics":
        status = "blocked_missing_metrics"
        summary = "Target-area metrics are blocked by missing or unclassified metric evidence, so the gate fails closed."
    elif metrics_completion_outcome == "incomplete":
        status = "blocked_missing_metrics"
        summary = "The latest metrics-completion attempt is incomplete; target-area metrics remain blocked until a preservation-checked measured run is supplied."
    else:
        status = "complete"
        summary = (
            "The target-area metrics contract is complete "
            f"from {metrics_completion_source.replace('_', ' ')}, so a rerun would not close a current gap."
        )
    return {
        "status": status,
        "metrics_contract_status": _status(metrics.get("metrics_contract_status")),
        "metrics_completion_source": metrics_completion_source,
        "metrics_completion_outcome": metrics_completion_outcome,
        "metrics_completion_attempt_status": metrics_completion_attempt_status,
        "missing_mandatory_metrics": missing_metrics,
        "next_run_required_metrics": next_run_required,
        "metrics_evidence_state": metrics_evidence_state,
        "summary": summary,
    }


def _metrics_gap_blocker(metrics_status: str) -> str:
    if metrics_status == "blocked_pre_submit":
        return "target_area_metrics_blocked_pre_submit"
    if metrics_status == "failed_closed":
        return "target_area_metrics_failed_closed"
    if metrics_status == "blocked_missing_metrics":
        return "target_area_metrics_blocked_missing_metrics"
    return "missing_target_area_metrics"


def build_multi_zone_balfrin_evidence_criteria(evidence: dict[str, Any]) -> dict[str, Any]:
    status = _status(evidence.get("status"), "blocked_incomplete")
    evidence_type = _status(evidence.get("evidence_type"), "blocked")
    first_bottleneck = _status(evidence.get("first_bottleneck_label"), "manifest_size_bytes")
    release_zone_count = evidence.get("release_zone_count")
    measured = status == "measured" and evidence_type == "measured"
    diagnostic = measured and evidence.get("output_mode") == "diagnostic_reducer_pressure"
    next_diagnostic_release_zone_count = 24 if diagnostic and release_zone_count == 16 else None
    diagnostic_ceiling = {
        "status": "measured" if diagnostic else "missing",
        "provenance_label": "diagnostic_single_node_postproc",
        "simultaneous_release_zone_batch_max": release_zone_count if diagnostic else None,
        "release_zone_count": release_zone_count if diagnostic else None,
        "next_diagnostic_release_zone_count": next_diagnostic_release_zone_count,
        "job_id": evidence.get("slurm_job_id") if diagnostic else None,
        "run_root": evidence.get("run_root") if diagnostic else None,
    }
    failed_closed = status == "failed_closed"
    blocked = status.startswith("blocked")
    return {
        "status": "measured" if measured else "blocked" if blocked else status,
        "evidence_status": status,
        "evidence_type": evidence_type,
        "task_id": evidence.get("task_id"),
        "root_class": _status(evidence.get("root_class"), "blocked_pre_authorization"),
        "output_mode": evidence.get("output_mode"),
        "release_zone_count": release_zone_count,
        "diagnostic_output_file_count": evidence.get("diagnostic_output_file_count"),
        "diagnostic_output_bytes": evidence.get("diagnostic_output_bytes"),
        "diagnostic_single_node_postproc_ceiling": diagnostic_ceiling,
        "first_bottleneck_label": first_bottleneck,
        "preflight_status": _status(evidence.get("preflight_status"), "not_supplied"),
        "authorization_record_status": _status(evidence.get("authorization_record_status"), "not_supplied"),
        "slurm_job_id": evidence.get("slurm_job_id"),
        "required_run_root_entries_status": evidence.get("required_run_root_entries_status"),
        "output_family_status": evidence.get("output_family_status"),
        "output_budget_audit_status": evidence.get("output_budget_audit_status"),
        "latest_prior_measured_task": evidence.get("latest_prior_measured_task"),
        "metrics_json_promoted": bool(evidence.get("metrics_json_promoted")),
        "preservation_gate_promoted": bool(evidence.get("preservation_gate_promoted")),
        "post_run_collector_promoted": bool(evidence.get("post_run_collector_promoted")),
        "next_blocker": str(evidence.get("next_blocker") or f"blocked_reducer_budget:{first_bottleneck}"),
        "scaling_frontier_branch": (
            "diagnostic_single_node_postproc_boundary"
            if diagnostic
            else "measured_two_zone_boundary"
            if measured and release_zone_count == 2
            else "measured_regional_split_boundary"
            if measured and isinstance(release_zone_count, int) and release_zone_count > 2
            else "failed_closed_two_zone_boundary"
            if failed_closed and release_zone_count == 2
            else "blocked_pre_authorization"
            if blocked
            else "not_measured_balfrin_root"
        ),
        "next_safe_expansion": (
            f"run a {next_diagnostic_release_zone_count}-zone diagnostic with scripts/run_balfrin_diagnostic.py after queue and scratch-capacity checks; keep it diagnostic single-node postproc evidence only"
            if diagnostic
            else "prepare reviewed next-larger package only after explicit authorization; this helper does not authorize it"
            if measured and release_zone_count == 2
            else "thread measured regional split replay/output-budget blockers into the next package before any larger live recommendation"
            if measured and isinstance(release_zone_count, int) and release_zone_count > 2
            else "repair or rerun the reviewed two-zone package before any live scale action; this helper does not authorize it"
            if failed_closed and release_zone_count == 2
            else f"no-go until {first_bottleneck} reducer-budget blocker and missing authorization record are resolved"
            if blocked
            else "no-go until scratch or fixture-backed evidence is replaced by preservation-checked measured Balfrin output"
        ),
        "summary": str(evidence.get("summary") or ""),
    }


def build_balfrin_access_criteria(access: dict[str, Any]) -> dict[str, Any]:
    status = _status(access.get("status"), "not_checked_not_needed_for_decision_refresh")
    path_state = _status(access.get("path_state"), "not_required_for_refresh")
    hard_blocked_statuses = {
        "ssh_access_expired",
        "authentication_failed",
        "permission_denied",
        "unavailable",
        "blocked_unavailable",
    }
    if status in hard_blocked_statuses:
        path_state = "ssh_access_expired" if status == "ssh_access_expired" else "unavailable"
    return {
        "status": status,
        "path_state": path_state,
        "ssh_access_state": _status(access.get("ssh_access_state"), status),
        "hard_live_run_blocker": status in hard_blocked_statuses,
        "live_submission_authorized": _bool(access.get("live_submission_authorized")),
        "blockers": _safe_list(access.get("blockers")),
        "remote_head": access.get("remote_head"),
        "remote_checkout_hygiene_status": access.get("remote_checkout_hygiene_status"),
        "remote_dirty_path_count": access.get("remote_dirty_path_count"),
        "ready_for_pre_submit": _bool(access.get("ready_for_pre_submit")),
        "diagnostic_run_planner": _copy_mapping(access.get("diagnostic_run_planner")),
        "summary": str(
            access.get("summary")
            or "Remote Balfrin SSH access was not checked because this helper is a deterministic local decision refresh."
        ),
    }


def build_option_assessments(criteria: dict[str, Any]) -> dict[str, Any]:
    metrics = criteria["missing_target_area_metrics"]
    preservation = criteria["preservation_gate_readiness"]
    reducer = criteria["reducer_pressure"]
    package = criteria["multi_zone_package_readiness"]
    multi_zone_evidence = criteria["multi_zone_balfrin_evidence"]
    runtime_pressure = criteria["expected_runtime_output_pressure"]
    scientific = criteria["scientific_value"]
    portability = criteria["portability_or_physical_evidence_value"]
    access = criteria["balfrin_access"]
    second_site = criteria["second_site_progress"]
    physical_evidence = criteria["physical_evidence_acquisition"]
    hazard_optimization = criteria["hazard_builder_optimization"]
    scenario_cap = criteria["scenario_batching_cap"]
    candidate_result = criteria["candidate_stability_result"]

    access_blockers = []
    if access["hard_live_run_blocker"]:
        access_blockers.append(f"balfrin_ssh_access:{access['status']}")

    metrics_source = metrics["metrics_completion_source"]
    metrics_pre_submit_blocked = metrics["status"] == "blocked_pre_submit"
    metrics_gap_open = metrics["status"] in {"missing", "blocked_pre_submit", "failed_closed", "blocked_missing_metrics"}
    metrics_complete = metrics["status"] == "complete"
    metrics_gap_blocker = _metrics_gap_blocker(str(metrics["status"]))
    metrics_blockers: list[str] = []
    if metrics_pre_submit_blocked:
        metrics_blockers.append(
            f"metrics_completion_pre_submit:{metrics.get('metrics_completion_attempt_status') or metrics_source}"
        )
    if metrics["status"] == "failed_closed":
        metrics_blockers.append(
            f"metrics_completion_failed_closed:{metrics.get('metrics_completion_attempt_status') or metrics_source}"
        )
    if metrics["status"] == "blocked_missing_metrics":
        metrics_blockers.append("metrics_completion_blocked_missing_metrics")
    if metrics_gap_open:
        if preservation["status"] != "ready":
            metrics_blockers.append(f"preservation_gate:{preservation['gate_status']}")
    metrics_blockers.extend(access_blockers)

    multi_zone_blockers: list[str] = []
    if metrics_gap_open:
        multi_zone_blockers.append(metrics_gap_blocker)
    if preservation["status"] != "ready":
        multi_zone_blockers.append(f"preservation_gate:{preservation['gate_status']}")
    if reducer["status"] != "ready":
        multi_zone_blockers.append(f"reducer_pressure:{reducer['bottleneck_classification']}")
    if package["status"] != "ready":
        multi_zone_blockers.append(f"multi_zone_package:{package['package_status']}")
    if multi_zone_evidence["status"] != "measured":
        multi_zone_blockers.append(f"multi_zone_evidence:{multi_zone_evidence['next_blocker']}")
    if runtime_pressure["status"] != "acceptable":
        multi_zone_blockers.append(f"output_pressure:{runtime_pressure['output_pressure_status']}")
    if scientific["status"] not in {"high", "ready"}:
        multi_zone_blockers.append(f"scientific_value:{scientific['status']}")
    if not access["live_submission_authorized"]:
        multi_zone_blockers.append("live_multi_zone_measurement_unauthorized")
    multi_zone_blockers.extend(access_blockers)

    defer_blockers: list[str] = []
    if metrics_gap_open:
        defer_blockers.append(metrics_gap_blocker)
    if preservation["status"] != "ready":
        defer_blockers.append(f"preservation_gate:{preservation['gate_status']}")
    if package["status"] == "ready" and reducer["status"] == "ready" and runtime_pressure["status"] == "acceptable":
        defer_blockers.append("multi_zone_probe_is_ready")
    if portability["status"] not in {"high", "preferred", "defer"} and scientific["status"] != "low":
        defer_blockers.append(f"portability_or_physical_evidence_value:{portability['status']}")

    second_site_blockers = list(second_site["blockers"])
    if metrics_gap_open:
        second_site_blockers.append(metrics_gap_blocker)
    if second_site["status"] not in {"preferred", "defer", "ready"}:
        second_site_blockers.append(f"second_site_progress:{second_site['status']}")

    physical_evidence_blockers = list(physical_evidence["blockers"])
    if metrics_gap_open:
        physical_evidence_blockers.append(metrics_gap_blocker)
    if physical_evidence["status"] not in {"preferred", "defer", "ready"}:
        physical_evidence_blockers.append(f"physical_evidence_acquisition:{physical_evidence['status']}")

    hazard_optimization_blockers = list(hazard_optimization["blockers"])
    if metrics_gap_open:
        hazard_optimization_blockers.append(metrics_gap_blocker)
    if hazard_optimization["path_state"] == "fixture_backed":
        hazard_optimization_blockers.append("hazard_hotspot_evidence:fixture_backed")
    if hazard_optimization["status"] not in {"preferred", "defer", "ready", "fixture_backed"}:
        hazard_optimization_blockers.append(f"hazard_builder_optimization:{hazard_optimization['status']}")

    metrics_ready = metrics["status"] == "missing" and preservation["status"] == "ready" and not access_blockers
    metrics_closed = metrics_complete and not access_blockers
    metrics_path_state = (
        access["path_state"]
        if access_blockers
        else ("measured" if metrics_ready else "closed" if metrics_closed else "blocked")
    )
    multi_zone_path_state = access["path_state"] if access_blockers else ("measured" if not multi_zone_blockers else "blocked")
    reducer_blockers: list[str] = []
    if metrics_gap_open:
        reducer_blockers.append(metrics_gap_blocker)
    if reducer["probe_status"] != "measured_scratch_root":
        reducer_blockers.append(f"reducer_pressure:{reducer['probe_status']}")
    if scenario_cap["status"] != "ready":
        reducer_blockers.append(f"scenario_batching:{scenario_cap['status']}")
    if candidate_result["status"] != "ready":
        reducer_blockers.append(f"candidate_stability:{candidate_result['status']}")
    reducer_ready = metrics_complete and reducer["probe_status"] == "measured_scratch_root" and not reducer_blockers
    diagnostic_ceiling = _copy_mapping(multi_zone_evidence.get("diagnostic_single_node_postproc_ceiling"))
    diagnostic_batch_max = diagnostic_ceiling.get("simultaneous_release_zone_batch_max")
    reducer_summary_batch_clause = (
        f"diagnostic single-node postproc batching is measured to {diagnostic_batch_max} release zones"
        if isinstance(diagnostic_batch_max, int)
        else "scenario batching is capped at 8 candidates"
    )

    assessments = {
        OPTION_METRICS: {
            "status": "ready" if metrics_ready else "complete" if metrics_closed else "blocked",
            "path_state": metrics_path_state,
            "follow_up_task": "TB-223",
            "action_package_task": "TB-225",
            "summary": (
                "Missing target-area metrics remain the clearest measured gap, so the metrics-completion rerun (metrics rerun) path is the next ranked action after SSH/access preflight."
                if metrics_ready
                else (
                    "Target-area metrics are already recovered from the preserved run root, so another metrics-completion rerun is no longer the next action."
                    if metrics_source == "recovered_existing_run_root"
                    else "Target-area metrics were already completed by an authorized rerun, so another metrics-completion rerun is no longer the next action."
                    if metrics_source == "new_metrics_completion_rerun"
                    else "The metrics-completion path is blocked before submit; rerun authorization must not proceed until the pre-submit blocker is cleared."
                    if metrics_source == "blocked_pre_submit"
                    else "No current target-area metrics gap is open for a rerun to close."
                )
            ),
            "exact_evidence_blockers": metrics_blockers,
            "boundary_that_prevents_claim_upgrade": "A metrics-completion rerun would collect missing execution metrics only; it does not establish physical credibility, annual frequency, risk, or operational hazard-map status.",
            "criteria": ["missing_target_area_metrics", "preservation_gate_readiness"],
            "metrics_completion_source": metrics_source,
        },
        OPTION_REDUCER: {
            "status": "defer" if reducer_ready else "blocked",
            "path_state": "scratch_local" if reducer_ready else "blocked",
            "follow_up_task": "TB-462",
            "summary": (
                "Reducer-pressure optimization is the next ranked executable action: metrics are complete, live scale remains unauthorized, "
                f"{reducer_summary_batch_clause}, replay smoke stays fixture-backed, and the selected candidate is stable for bounded engineering follow-up."
                if reducer_ready
                else "Reducer-pressure optimization cannot be ranked first until the metrics gap is closed and refreshed reducer evidence is present."
            ),
            "exact_evidence_blockers": reducer_blockers,
            "boundary_that_prevents_claim_upgrade": "Reducer-pressure optimization is scratch/local planning evidence only; it does not authorize a Balfrin submission, distributed execution, scale-up, or operational hazard use.",
            "criteria": [
                "missing_target_area_metrics",
                "reducer_pressure",
                "scenario_batching_cap",
                "candidate_stability_result",
            ],
            "scenario_batching_cap": scenario_cap["scenario_batching_cap"],
            "selected_candidate_id": candidate_result["selected_candidate_id"],
            "selected_candidate_class": candidate_result["selected_candidate_class"],
        },
        OPTION_MULTI_ZONE: {
            "status": "ready" if not multi_zone_blockers else "blocked",
            "path_state": multi_zone_path_state,
            "follow_up_task": "TB-226",
            "summary": (
                "The smallest bounded multi-zone probe is ready only when the preservation gate, reducer pressure, package readiness, runtime/output pressure, and scientific value all align."
            ),
            "exact_evidence_blockers": multi_zone_blockers,
            "boundary_that_prevents_claim_upgrade": "A smallest multi-zone measurement would remain a bounded conditional diagnostic and would not authorize distributed execution, scale-up, or operational use.",
            "criteria": [
                "missing_target_area_metrics",
                "preservation_gate_readiness",
                "reducer_pressure",
                "multi_zone_package_readiness",
                "multi_zone_balfrin_evidence",
                "expected_runtime_output_pressure",
                "scientific_value",
            ],
            "scaling_frontier_branch": multi_zone_evidence["scaling_frontier_branch"],
            "next_safe_expansion": multi_zone_evidence["next_safe_expansion"],
        },
        OPTION_DEFER: {
            "status": "defer" if metrics["status"] == "complete" and multi_zone_blockers else "blocked",
            "path_state": "blocked" if defer_blockers else "measured",
            "follow_up_task": "TB-231",
            "summary": (
                "Deferral is justified once the target-area metrics gap is closed and the multi-zone path remains no-go, so portability or physical-evidence work can proceed first."
            ),
            "exact_evidence_blockers": defer_blockers,
            "boundary_that_prevents_claim_upgrade": "Deferring to portability or physical-evidence work does not convert staged context, acquisition planning, or observed-data schemas into validation or calibration evidence.",
            "criteria": [
                "missing_target_area_metrics",
                "preservation_gate_readiness",
                "multi_zone_package_readiness",
                "expected_runtime_output_pressure",
                "portability_or_physical_evidence_value",
            ],
        },
        OPTION_SECOND_SITE: {
            "status": "defer" if metrics["status"] == "complete" and second_site["status"] in {"preferred", "defer", "ready"} else "blocked",
            "path_state": second_site["path_state"],
            "follow_up_task": second_site["follow_up_task"],
            "summary": second_site["summary"],
            "exact_evidence_blockers": second_site_blockers,
            "boundary_that_prevents_claim_upgrade": "Second-site public-context progress may improve portability only after real inputs are staged; it does not authorize a second-site ensemble or hazard build.",
            "criteria": ["missing_target_area_metrics", "second_site_progress"],
        },
        OPTION_PHYSICAL_EVIDENCE: {
            "status": "defer" if metrics["status"] == "complete" and physical_evidence["status"] in {"preferred", "defer", "ready"} else "blocked",
            "path_state": physical_evidence["path_state"],
            "follow_up_task": physical_evidence["follow_up_task"],
            "summary": physical_evidence["summary"],
            "exact_evidence_blockers": physical_evidence_blockers,
            "boundary_that_prevents_claim_upgrade": "Physical-evidence acquisition can reduce evidence gaps only after independent observed/provenance inputs are staged; it does not authorize calibration, annual-frequency, risk, or operational claims.",
            "criteria": ["missing_target_area_metrics", "physical_evidence_acquisition"],
        },
        OPTION_HAZARD_OPTIMIZATION: {
            "status": "defer" if metrics["status"] == "complete" and hazard_optimization["status"] in {"preferred", "defer", "ready", "fixture_backed"} else "blocked",
            "path_state": hazard_optimization["path_state"],
            "follow_up_task": hazard_optimization["follow_up_task"],
            "summary": hazard_optimization["summary"],
            "exact_evidence_blockers": hazard_optimization_blockers,
            "boundary_that_prevents_claim_upgrade": "A hazard-builder optimization may improve throughput only if semantic guardrails pass; it does not change hazard semantics, physics, probability meaning, or claim maturity.",
            "criteria": ["missing_target_area_metrics", "hazard_builder_optimization"],
        },
    }
    return assessments


def choose_recommendation(option_assessments: dict[str, Any]) -> dict[str, Any]:
    metrics = option_assessments[OPTION_METRICS]
    reducer = option_assessments[OPTION_REDUCER]
    multi_zone = option_assessments[OPTION_MULTI_ZONE]
    defer = option_assessments[OPTION_DEFER]
    second_site = option_assessments[OPTION_SECOND_SITE]
    physical_evidence = option_assessments[OPTION_PHYSICAL_EVIDENCE]
    hazard_optimization = option_assessments[OPTION_HAZARD_OPTIMIZATION]

    if metrics["status"] == "ready":
        return {
            "action_id": OPTION_METRICS,
            "status": "ready",
            "classification": "ready",
            "path_state": metrics["path_state"],
            "follow_up_task": metrics["follow_up_task"],
            "summary": metrics["summary"],
            "exact_evidence_blockers": metrics["exact_evidence_blockers"],
            "boundary_that_prevents_claim_upgrade": metrics["boundary_that_prevents_claim_upgrade"],
            "blocked_reason": "none",
        }
    if multi_zone["status"] == "ready":
        return {
            "action_id": OPTION_MULTI_ZONE,
            "status": "ready",
            "classification": "ready",
            "path_state": multi_zone["path_state"],
            "follow_up_task": multi_zone["follow_up_task"],
            "summary": multi_zone["summary"],
            "exact_evidence_blockers": multi_zone["exact_evidence_blockers"],
            "boundary_that_prevents_claim_upgrade": multi_zone["boundary_that_prevents_claim_upgrade"],
            "blocked_reason": "none",
        }
    if reducer["status"] == "defer":
        return {
            "action_id": OPTION_REDUCER,
            "status": "defer",
            "classification": "reducer_first",
            "path_state": reducer["path_state"],
            "follow_up_task": reducer["follow_up_task"],
            "summary": reducer["summary"],
            "exact_evidence_blockers": reducer["exact_evidence_blockers"],
            "boundary_that_prevents_claim_upgrade": reducer["boundary_that_prevents_claim_upgrade"],
            "blocked_reason": "none",
        }
    for action_id, option in (
        (OPTION_SECOND_SITE, second_site),
        (OPTION_PHYSICAL_EVIDENCE, physical_evidence),
        (OPTION_HAZARD_OPTIMIZATION, hazard_optimization),
        (OPTION_DEFER, defer),
    ):
        if option["status"] == "defer":
            return {
                "action_id": action_id,
                "status": "defer",
                "classification": "defer",
                "path_state": option["path_state"],
                "follow_up_task": option["follow_up_task"],
                "summary": option["summary"],
                "exact_evidence_blockers": option["exact_evidence_blockers"],
                "boundary_that_prevents_claim_upgrade": option["boundary_that_prevents_claim_upgrade"],
                "blocked_reason": "none",
            }

    blocked_path_states = {
        str(option.get("path_state"))
        for option in option_assessments.values()
        if isinstance(option, dict) and option.get("status") == "blocked"
    }
    if "ssh_access_expired" in blocked_path_states:
        return {
            "action_id": OPTION_METRICS,
            "status": "blocked",
            "classification": "ssh_access_expired",
            "path_state": "ssh_access_expired",
            "follow_up_task": "TB-223",
            "summary": "Balfrin SSH access is expired or unavailable, so live Balfrin measurement paths fail closed before any run request is prepared.",
            "exact_evidence_blockers": sorted(
                set(metrics["exact_evidence_blockers"] + multi_zone["exact_evidence_blockers"])
            ),
            "boundary_that_prevents_claim_upgrade": metrics["boundary_that_prevents_claim_upgrade"],
            "blocked_reason": "Balfrin SSH access expired or unavailable",
        }

    return {
        "action_id": OPTION_DEFER,
        "status": "blocked",
        "classification": "blocked",
        "path_state": "blocked",
        "follow_up_task": defer["follow_up_task"],
        "summary": "The current evidence remains insufficient for any ranked next-action path.",
        "exact_evidence_blockers": sorted(
            set(
                metrics["exact_evidence_blockers"]
                + multi_zone["exact_evidence_blockers"]
                + defer["exact_evidence_blockers"]
                + second_site["exact_evidence_blockers"]
                + physical_evidence["exact_evidence_blockers"]
                + hazard_optimization["exact_evidence_blockers"]
            )
        ),
        "boundary_that_prevents_claim_upgrade": defer["boundary_that_prevents_claim_upgrade"],
        "blocked_reason": "required measured inputs are missing or unresolved",
    }


def build_ranked_actions(option_assessments: dict[str, Any]) -> list[dict[str, Any]]:
    status_score = {"ready": 100, "defer": 70, "blocked": 10, "complete": -40}
    path_score = {
        "measured": 30,
        "fixture_backed": 20,
        "scratch_local": 25,
        "blocked": 0,
        "closed": -30,
        "unavailable": -10,
        "unauthorized": -20,
        "ssh_access_expired": -30,
    }
    priority_bias = {
        OPTION_METRICS: 50,
        OPTION_REDUCER: 45,
        OPTION_MULTI_ZONE: 40,
        OPTION_SECOND_SITE: 30,
        OPTION_PHYSICAL_EVIDENCE: 25,
        OPTION_HAZARD_OPTIMIZATION: 20,
    }
    rows: list[dict[str, Any]] = []
    for action_id in RANKED_ACTION_OPTIONS:
        option = option_assessments[action_id]
        score = (
            status_score.get(str(option.get("status")), 0)
            + path_score.get(str(option.get("path_state")), 0)
            + priority_bias[action_id]
        )
        rows.append(
            {
                "action_id": action_id,
                "rank_score": score,
                "status": option.get("status", "unknown"),
                "path_state": option.get("path_state", "unknown"),
                "follow_up_task": option.get("follow_up_task", "unknown"),
                "exact_evidence_blockers": option.get("exact_evidence_blockers", []),
                "boundary_that_prevents_claim_upgrade": option.get("boundary_that_prevents_claim_upgrade", ""),
            }
        )
    rows.sort(key=lambda row: (-int(row["rank_score"]), str(row["action_id"])))
    for index, row in enumerate(rows, start=1):
        row["rank"] = index
    return rows


def build_evidence_sources(bundle: dict[str, Any]) -> dict[str, Any]:
    source_paths = _copy_mapping(bundle.get("source_paths"))
    return {
        "schema_version": "balfrin_next_live_run_decision_gate_evidence_sources_v1",
        "probe_metrics_report": source_paths.get("probe_metrics_report"),
        "preservation_gate_report": source_paths.get("preservation_gate_report"),
        "multi_zone_reducer_pressure_report": source_paths.get("multi_zone_reducer_pressure_report"),
        "multi_zone_handoff_report": source_paths.get("multi_zone_handoff_report"),
        "multi_zone_balfrin_evidence": source_paths.get("multi_zone_balfrin_evidence") or "docs/agent_work_log.md",
        "balfrin_access": source_paths.get("balfrin_access"),
        "second_site_progress": source_paths.get("second_site_progress"),
        "physical_evidence_acquisition": source_paths.get("physical_evidence_acquisition"),
        "hazard_builder_optimization": source_paths.get("hazard_builder_optimization"),
        "scenario_batching": source_paths.get("scenario_batching") or "scripts/summarize_management_aoi_scenario_pressure.py",
        "candidate_stability": source_paths.get("candidate_stability") or "scripts/summarize_balfrin_target_area_candidate_stability.py",
        "post_tb_221_evidence": source_paths.get("post_tb_221_evidence"),
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
            "follow_up_task": "TB-223",
            "summary": "Missing measured inputs prevent the gate from deciding whether a metrics rerun, multi-zone probe, or deferral should proceed.",
            "exact_evidence_blockers": missing,
            "boundary_that_prevents_claim_upgrade": "Missing inputs prevent any claim upgrade; no physical, annual-frequency, risk, scale-up, distributed-execution, or operational claim is allowed.",
            "blocked_reason": "required measured inputs are missing",
        },
        "next_follow_up_package_task": "TB-223",
        "criteria": {
            "missing_target_area_metrics": {
                "status": "blocked_missing_inputs",
                "metrics_completion_source": "blocked_missing_metrics",
                "missing_mandatory_metrics": [],
            },
            "preservation_gate_readiness": {"status": "blocked_missing_inputs"},
            "reducer_pressure": {"status": "blocked_missing_inputs"},
            "multi_zone_package_readiness": {"status": "blocked_missing_inputs"},
            "multi_zone_balfrin_evidence": {
                "status": "blocked",
                "evidence_status": "blocked_missing_inputs",
                "first_bottleneck_label": "missing_inputs",
                "next_blocker": "missing_inputs",
                "scaling_frontier_branch": "blocked_missing_inputs",
                "next_safe_expansion": "no-go until required evidence inputs are supplied",
            },
            "expected_runtime_output_pressure": {"status": "blocked_missing_inputs"},
            "scientific_value": {"status": "blocked_missing_inputs"},
            "portability_or_physical_evidence_value": {"status": "blocked_missing_inputs"},
            "balfrin_access": {"status": "blocked_missing_inputs", "path_state": "blocked"},
            "second_site_progress": {"status": "blocked_missing_inputs", "path_state": "blocked"},
            "physical_evidence_acquisition": {"status": "blocked_missing_inputs", "path_state": "blocked"},
            "hazard_builder_optimization": {"status": "blocked_missing_inputs", "path_state": "blocked"},
            "scenario_batching_cap": {"status": "blocked_missing_inputs"},
            "candidate_stability_result": {"status": "blocked_missing_inputs"},
            "reducer_first_ranked_evidence": {"status": "blocked_missing_inputs", "ranked_next_probe_ladder": []},
            "post_tb_221_evidence": {"status": "blocked_missing_inputs", "evidence_items": []},
        },
        "option_assessments": {
            OPTION_METRICS: {
                "status": "blocked",
                "path_state": "blocked",
                "follow_up_task": "TB-223",
                "summary": "The metrics-completion rerun cannot be prioritized until the missing measured inputs are supplied.",
                "exact_evidence_blockers": missing,
                "boundary_that_prevents_claim_upgrade": "Missing measured inputs prevent any claim upgrade.",
                "criteria": ["missing_target_area_metrics", "preservation_gate_readiness"],
                "metrics_completion_source": "blocked_missing_metrics",
            },
            OPTION_REDUCER: {
                "status": "blocked",
                "path_state": "blocked",
                "follow_up_task": "TB-462",
                "summary": "Reducer-pressure optimization cannot be ranked until the missing measured inputs are supplied.",
                "exact_evidence_blockers": missing,
                "boundary_that_prevents_claim_upgrade": "Missing measured inputs prevent any reducer, scale-up, distributed-execution, or operational claim upgrade.",
                "criteria": ["reducer_pressure", "scenario_batching_cap", "candidate_stability_result"],
            },
            OPTION_MULTI_ZONE: {
                "status": "blocked",
                "path_state": "blocked",
                "follow_up_task": "TB-226",
                "summary": "The smallest bounded multi-zone probe is blocked because the evidence bundle is incomplete.",
                "exact_evidence_blockers": missing,
                "boundary_that_prevents_claim_upgrade": "Missing measured inputs prevent any multi-zone or scale-up claim upgrade.",
                "criteria": ["reducer_pressure", "multi_zone_package_readiness"],
            },
            OPTION_DEFER: {
                "status": "blocked",
                "path_state": "blocked",
                "follow_up_task": "TB-231",
                "summary": "Deferral is blocked because the gate cannot establish whether a direct measured gap still needs closure.",
                "exact_evidence_blockers": missing,
                "boundary_that_prevents_claim_upgrade": "Missing measured inputs prevent any portability or physical-evidence claim upgrade.",
                "criteria": ["scientific_value", "portability_or_physical_evidence_value"],
            },
            OPTION_SECOND_SITE: {
                "status": "blocked",
                "path_state": "blocked",
                "follow_up_task": "TB-231",
                "summary": "Second-site progress cannot be ranked until the missing measured inputs are supplied.",
                "exact_evidence_blockers": missing,
                "boundary_that_prevents_claim_upgrade": "No second-site ensemble or hazard build is authorized.",
                "criteria": ["second_site_progress"],
            },
            OPTION_PHYSICAL_EVIDENCE: {
                "status": "blocked",
                "path_state": "blocked",
                "follow_up_task": "TB-233",
                "summary": "Physical-evidence acquisition cannot be ranked until the missing measured inputs are supplied.",
                "exact_evidence_blockers": missing,
                "boundary_that_prevents_claim_upgrade": "No calibration, annual-frequency, risk, or operational claim is allowed.",
                "criteria": ["physical_evidence_acquisition"],
            },
            OPTION_HAZARD_OPTIMIZATION: {
                "status": "blocked",
                "path_state": "blocked",
                "follow_up_task": "TB-229",
                "summary": "Hazard-builder optimization cannot outrank missing measured evidence.",
                "exact_evidence_blockers": missing,
                "boundary_that_prevents_claim_upgrade": "No hazard semantics or physics change is authorized.",
                "criteria": ["hazard_builder_optimization"],
            },
        },
        "ranked_actions": [],
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


def blocked_reducer_pressure_scratch_report(exc: FileNotFoundError) -> dict[str, Any]:
    report = blocked_missing_inputs_report(["multi_zone_reducer_pressure_report"])
    missing_path = str(getattr(exc, "filename", "") or exc)
    blocker = "reducer_pressure_scratch_root_missing"
    report["decision_summary"] = (
        "The next live Balfrin decision gate is blocked because reducer-pressure scratch artifacts "
        "are missing or were removed during local measurement."
    )
    report["recommended_next_action"].update(
        {
            "action_id": OPTION_REDUCER,
            "follow_up_task": "TB-551",
            "summary": "Regenerate the reducer-pressure scratch root before ranking the next Balfrin action.",
            "exact_evidence_blockers": [blocker],
            "blocked_reason": blocker,
            "recovery_command": REDUCER_PRESSURE_REGENERATION_COMMAND,
        }
    )
    report["next_follow_up_package_task"] = "TB-551"
    report["criteria"]["reducer_pressure"] = {
        "status": "blocked_missing_scratch_root",
        "probe_status": "blocked_missing_scratch_root",
        "missing_path": missing_path,
        "recovery_command": REDUCER_PRESSURE_REGENERATION_COMMAND,
        "summary": "Reducer-pressure scratch artifacts are absent; regenerate them before using this decision gate.",
    }
    report["option_assessments"][OPTION_REDUCER].update(
        {
            "follow_up_task": "TB-551",
            "summary": "Reducer-pressure optimization cannot be ranked until the scratch-root artifacts are regenerated.",
            "exact_evidence_blockers": [blocker],
            "recovery_command": REDUCER_PRESSURE_REGENERATION_COMMAND,
        }
    )
    report["evidence_sources"]["multi_zone_reducer_pressure_report"] = None
    report["recovery_commands"] = {
        "multi_zone_reducer_pressure_report": REDUCER_PRESSURE_REGENERATION_COMMAND,
    }
    report["blocked_reason"] = blocker
    return report


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
        "multi_zone_balfrin_evidence",
        "expected_runtime_output_pressure",
        "scientific_value",
        "portability_or_physical_evidence_value",
        "balfrin_access",
        "second_site_progress",
        "physical_evidence_acquisition",
        "hazard_builder_optimization",
        "scenario_batching_cap",
        "candidate_stability_result",
        "reducer_first_ranked_evidence",
        "post_tb_221_evidence",
    ):
        entry = criteria.get(key, {}) if isinstance(criteria, dict) else {}
        lines.append(f"  - {key}: {entry.get('status', 'unknown')}")
        if key == "missing_target_area_metrics":
            lines.append(f"    metrics_completion_source: {entry.get('metrics_completion_source', 'unknown')}")
            lines.append(f"    metrics_completion_outcome: {entry.get('metrics_completion_outcome', 'unknown')}")
            lines.append(f"    metrics_completion_attempt_status: {entry.get('metrics_completion_attempt_status', 'unknown')}")
            lines.append(f"    missing_mandatory_metrics: {entry.get('missing_mandatory_metrics', [])}")
            lines.append(f"    next_run_required_metrics: {entry.get('next_run_required_metrics', [])}")
            state = entry.get("metrics_evidence_state") or {}
            if isinstance(state, dict) and state:
                lines.append(f"    memory_peak_mb: {state.get('memory_peak_mb', 'unknown')}")
                lines.append(f"    validation_output: {state.get('validation_output', {})}")
                lines.append(f"    hazard_output: {state.get('hazard_output', {})}")
                lines.append(f"    slurm: {state.get('slurm', {})}")
                lines.append(f"    run_root_hashes: {state.get('run_root_hashes', {})}")
                lines.append(f"    preservation_status: {state.get('preservation_status', 'unknown')}")
                lines.append(f"    preservation_checked: {state.get('preservation_checked', False)}")
        if key == "reducer_pressure":
            lines.append(f"    bottleneck_classification: {entry.get('bottleneck_classification', '')}")
            lines.append(f"    blocked_reason: {entry.get('blocked_reason', '')}")
        if key == "multi_zone_package_readiness":
            lines.append(f"    package_status: {entry.get('package_status', '')}")
            lines.append(f"    output_pressure_status: {entry.get('output_pressure_status', '')}")
        if key == "multi_zone_balfrin_evidence":
            lines.append(f"    evidence_status: {entry.get('evidence_status', '')}")
            lines.append(f"    first_bottleneck_label: {entry.get('first_bottleneck_label', '')}")
            lines.append(f"    scaling_frontier_branch: {entry.get('scaling_frontier_branch', '')}")
            lines.append(f"    next_safe_expansion: {entry.get('next_safe_expansion', '')}")
        if key == "scientific_value":
            lines.append(f"    summary: {entry.get('summary', '')}")
        if key == "balfrin_access":
            lines.append(f"    path_state: {entry.get('path_state', '')}")
            lines.append(f"    hard_live_run_blocker: {entry.get('hard_live_run_blocker', False)}")
        if key in {"second_site_progress", "physical_evidence_acquisition", "hazard_builder_optimization"}:
            lines.append(f"    path_state: {entry.get('path_state', '')}")
            lines.append(f"    blockers: {entry.get('blockers', [])}")
        if key == "scenario_batching_cap":
            lines.append(f"    scenario_batching_cap: {entry.get('scenario_batching_cap', '')}")
            lines.append(f"    prepared_pilot_smoke_status: {entry.get('prepared_pilot_smoke_status', '')}")
        if key == "candidate_stability_result":
            lines.append(f"    selected_candidate_id: {entry.get('selected_candidate_id', '')}")
            lines.append(f"    selected_candidate_class: {entry.get('selected_candidate_class', '')}")
            lines.append(f"    stability_score: {entry.get('stability_score', '')}")
        if key == "reducer_first_ranked_evidence":
            lines.append(f"    ranked_next_probe_ladder: {entry.get('ranked_next_probe_ladder', [])}")
        if key == "post_tb_221_evidence":
            lines.append(f"    evidence_items: {entry.get('evidence_items', [])}")

    lines.extend(["", "options:"])
    for option_key in (
        OPTION_METRICS,
        OPTION_REDUCER,
        OPTION_MULTI_ZONE,
        OPTION_SECOND_SITE,
        OPTION_PHYSICAL_EVIDENCE,
        OPTION_HAZARD_OPTIMIZATION,
        OPTION_DEFER,
    ):
        option = report.get("option_assessments", {}).get(option_key, {})
        lines.append(f"  - {option_key}: {option.get('status', 'unknown')}")
        lines.append(f"    path_state: {option.get('path_state', 'unknown')}")
        lines.append(f"    follow_up_task: {option.get('follow_up_task', 'unknown')}")
        lines.append(f"    blockers: {option.get('exact_evidence_blockers', [])}")
        if option_key == OPTION_METRICS:
            lines.append(f"    metrics_completion_source: {option.get('metrics_completion_source', 'unknown')}")
        if option_key == OPTION_REDUCER:
            lines.append(f"    scenario_batching_cap: {option.get('scenario_batching_cap', 'unknown')}")
            lines.append(f"    selected_candidate_id: {option.get('selected_candidate_id', 'unknown')}")
            lines.append(f"    selected_candidate_class: {option.get('selected_candidate_class', 'unknown')}")
        if option_key == OPTION_MULTI_ZONE:
            lines.append(f"    scaling_frontier_branch: {option.get('scaling_frontier_branch', 'unknown')}")
            lines.append(f"    next_safe_expansion: {option.get('next_safe_expansion', 'unknown')}")
        lines.append(f"    boundary: {option.get('boundary_that_prevents_claim_upgrade', '')}")
        lines.append(f"    summary: {option.get('summary', '')}")

    lines.extend(["", "ranked_actions:"])
    for row in report.get("ranked_actions", []):
        lines.append(
            f"  - rank {row.get('rank', '?')}: {row.get('action_id', 'unknown')} "
            f"({row.get('status', 'unknown')}, {row.get('path_state', 'unknown')})"
        )

    recommended = report.get("recommended_next_action", {})
    lines.extend(
        [
            "",
            "recommended_next_action:",
            f"  action_id: {recommended.get('action_id', 'unknown')}",
            f"  classification: {recommended.get('classification', 'unknown')}",
            f"  path_state: {recommended.get('path_state', 'unknown')}",
            f"  follow_up_task: {recommended.get('follow_up_task', 'unknown')}",
            f"  exact_evidence_blockers: {recommended.get('exact_evidence_blockers', [])}",
            f"  boundary_that_prevents_claim_upgrade: {recommended.get('boundary_that_prevents_claim_upgrade', '')}",
            f"  summary: {recommended.get('summary', '')}",
        ]
    )
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
