#!/usr/bin/env python3
"""Summarize the Balfrin target-area metrics-completion rerun package.

This helper is read-only. It packages a dry-run rerun plan, a bounded SBATCH
handoff, a preservation checklist, and a comparison against the currently
recorded target-area run so the next execution can be scoped strictly to the
missing peak-memory and split validation/hazard output metrics.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shlex
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import submit_balfrin_probe as submit  # noqa: E402
from scripts import summarize_balfrin_probe_metrics_report as probe_metrics_report  # noqa: E402
from scripts import summarize_balfrin_probe_preservation_gate as preservation_gate  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "balfrin_target_area_metrics_completion_rerun_package_v1"
REPORT_BASENAME = "balfrin_target_area_metrics_completion_rerun_package_v1"
DEFAULT_ARTIFACT_DIR = ROOT / "validation/private/tschamut_public_pilot/balfrin_target_area_metrics_completion_rerun_package_v1"
DEFAULT_PROBE_MANIFEST = ROOT / "validation/pilot_runs/tschamut_public_balfrin_target_area_demo_v1.yaml"
DEFAULT_RERUN_RUN_ROOT = Path(
    "/scratch/mch/olifu/rust_rockfall/probes/tschamut_public_balfrin_target_area_demo_v1/metrics_completion_v1"
)
DEFAULT_RERUN_RUN_ID = "tschamut_public_balfrin_target_area_demo_metrics_completion_v1"
DEFAULT_PARTITION = "postproc"
DEFAULT_TIME_BUDGET = "00:30:00"
DEFAULT_NODES = 1
DEFAULT_NTASKS = 1
DEFAULT_CPUS_PER_TASK = 16
DEFAULT_EXISTING_TARGET_AREA_JOB_ID = 4329024
DEFAULT_EXISTING_TARGET_AREA_RUN_ROOT = Path(
    "/scratch/mch/olifu/rust_rockfall/probes/tschamut_public_balfrin_target_area_demo_v1/authorized_tb168_20260517"
)
DEFAULT_EXISTING_TARGET_AREA_SOURCE = "docs/balfrin_probe_slurm_driver.md"

REQUIRED_METRICS = [
    "memory_peak_mb",
    "validation_output.file_count",
    "validation_output.bytes",
    "hazard_output.file_count",
    "hazard_output.bytes",
]

REQUIRED_REPLAY_METADATA = [
    "run_root",
    "probe_manifest",
    "command_plan_path",
    "sbatch_script_path",
    "metrics_collection_command",
    "preservation_gate_command",
    "existing_target_area_run_root",
    "existing_target_area_job_id",
    "git_commit",
]

REQUIRED_RUN_ROOT_ENTRIES = [
    {"path": "command_plan.json", "kind": "file"},
    {"path": "probe.sbatch", "kind": "file"},
    {"path": "balfrin_submission_package.json", "kind": "file"},
    {"path": "balfrin_submission_package.md", "kind": "file"},
    {"path": "balfrin_probe_metrics.json", "kind": "file"},
    {"path": "balfrin_probe_summary.json", "kind": "file"},
    {"path": "balfrin_probe_context.txt", "kind": "file"},
    {"path": "balfrin_probe_full_time.txt", "kind": "file"},
    {"path": "balfrin_hazard_stage_time.txt", "kind": "file"},
    {"path": "logs", "kind": "dir"},
    {"path": "output", "kind": "dir"},
    {"path": "output/validation_balfrin_probe_manifest.json", "kind": "file"},
    {"path": "output/validation_balfrin_probe_scaling_summary.json", "kind": "file"},
    {"path": "output/trajectory_chunks", "kind": "dir"},
    {"path": "output/chunks", "kind": "dir"},
]

EXISTING_TARGET_AREA_RUN = {
    "job_id": DEFAULT_EXISTING_TARGET_AREA_JOB_ID,
    "run_root": str(DEFAULT_EXISTING_TARGET_AREA_RUN_ROOT),
    "partition": DEFAULT_PARTITION,
    "cpus_per_task": DEFAULT_CPUS_PER_TASK,
    "time_budget": DEFAULT_TIME_BUDGET,
    "slurm_state": "COMPLETED",
    "exit_code": "0:0",
    "elapsed": "00:00:43",
    "output_file_count": 58,
    "output_bytes": 192_350_243,
    "conditional_curve_row_count": 729_600,
    "known_completion_gaps": REQUIRED_METRICS,
    "source": DEFAULT_EXISTING_TARGET_AREA_SOURCE,
}


class BalfrinTargetAreaMetricsCompletionRerunPackageError(ValueError):
    """User-facing rerun-package error."""


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--run-root",
        type=Path,
        default=DEFAULT_RERUN_RUN_ROOT,
        help="Dry-run rerun root for the metrics-completion package.",
    )
    parser.add_argument(
        "--probe-manifest",
        type=Path,
        default=DEFAULT_PROBE_MANIFEST,
        help="Frozen target-area probe manifest used for the rerun package.",
    )
    parser.add_argument(
        "--artifact-dir",
        type=Path,
        default=DEFAULT_ARTIFACT_DIR,
        help="Artifact directory for the package JSON and text report.",
    )
    parser.add_argument(
        "--format",
        choices=("json", "text"),
        default="text",
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=None,
    )
    parser.add_argument(
        "--text-output",
        type=Path,
        default=None,
    )
    parser.add_argument(
        "--evidence-json",
        type=Path,
        default=None,
        help="Optional override JSON file for tests or alternate package snapshots.",
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


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sha256_json(payload: Any) -> str:
    return _sha256_text(json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str))


def _bash_command(tokens: list[str]) -> str:
    return " ".join(shlex.quote(token) for token in tokens)


def _default_existing_target_area_run() -> dict[str, Any]:
    return dict(EXISTING_TARGET_AREA_RUN)


def _build_dry_run_command_plan(
    *,
    run_root: Path,
    probe_manifest: Path,
    artifact_dir: Path,
    run_id: str,
    partition: str,
    time_budget: str,
    nodes: int,
    ntasks: int,
    cpus_per_task: int,
    sbatch_script_text: str,
) -> dict[str, Any]:
    submit_base = [
        "PYENV_VERSION=system",
        "uv",
        "run",
        "python",
        "scripts/submit_balfrin_probe.py",
        str(probe_manifest),
        "--run-root",
        str(run_root),
        "--run-id",
        run_id,
        "--partition",
        partition,
        "--time",
        time_budget,
        "--nodes",
        str(nodes),
        "--ntasks",
        str(ntasks),
        "--cpus-per-task",
        str(cpus_per_task),
    ]
    return {
        "schema_version": "balfrin_target_area_metrics_completion_rerun_command_plan_v1",
        "status": "complete",
        "run_root": str(run_root),
        "probe_manifest": str(probe_manifest),
        "run_id": run_id,
        "dry_run_command": _bash_command(submit_base + ["--dry-run"]),
        "generate_only_command": _bash_command(submit_base + ["--generate-only"]),
        "collect_command": _bash_command(
            [
                "PYENV_VERSION=system",
                "uv",
                "run",
                "python",
                "scripts/collect_balfrin_probe_metrics.py",
                "--run-root",
                str(run_root),
                "--probe-manifest",
                str(probe_manifest),
                "--output-json",
                str(run_root / "balfrin_probe_metrics.json"),
            ]
        ),
        "preservation_gate_command": _bash_command(
            [
                "PYENV_VERSION=system",
                "uv",
                "run",
                "python",
                "scripts/summarize_balfrin_probe_preservation_gate.py",
                "--run-root",
                str(run_root),
                "--format",
                "json",
                "--artifact-dir",
                str(artifact_dir / "balfrin_probe_preservation_gate_v1"),
            ]
        ),
        "metrics_report_command": _bash_command(
            [
                "PYENV_VERSION=system",
                "uv",
                "run",
                "python",
                "scripts/summarize_balfrin_probe_metrics_report.py",
                "--run-root",
                str(DEFAULT_EXISTING_TARGET_AREA_RUN_ROOT),
                "--format",
                "json",
                "--artifact-dir",
                str(artifact_dir / "balfrin_probe_metrics_report_v1"),
            ]
        ),
        "sbatch_script_text": sbatch_script_text,
        "sbatch_script_sha256": _sha256_text(sbatch_script_text),
        "source_paths": {
            "probe_manifest": str(probe_manifest),
            "run_root": str(run_root),
            "artifact_dir": str(artifact_dir),
        },
        "summary": (
            "Dry-run only: generate the SBATCH package, preserve the run-root contract, and compare against the recorded target-area run without authorizing a live submission."
        ),
    }


def _build_sbatch_package(
    *,
    run_root: Path,
    probe_manifest: Path,
    run_id: str,
    partition: str,
    time_budget: str,
    nodes: int,
    ntasks: int,
    cpus_per_task: int,
    command_plan: dict[str, Any],
) -> dict[str, Any]:
    sbatch_script_text = submit._build_sbatch_script(  # noqa: SLF001
        run_root=run_root,
        probe_manifest=probe_manifest,
        partition=partition,
        time_budget=time_budget,
        nodes=nodes,
        ntasks=ntasks,
        cpus_per_task=cpus_per_task,
    )
    return {
        "schema_version": "balfrin_target_area_metrics_completion_rerun_sbatch_package_v1",
        "status": "complete",
        "launch_authorized": False,
        "run_root": str(run_root),
        "run_id": run_id,
        "probe_manifest": str(probe_manifest),
        "partition": partition,
        "time_budget": time_budget,
        "nodes": nodes,
        "ntasks": ntasks,
        "cpus_per_task": cpus_per_task,
        "command_plan_path": str(run_root / "command_plan.json"),
        "sbatch_script_path": str(run_root / "probe.sbatch"),
        "sbatch_script_text": sbatch_script_text,
        "sbatch_script_sha256": _sha256_text(sbatch_script_text),
        "command_plan_sha256": _sha256_json(command_plan),
        "expected_outputs": [
            str(run_root / "command_plan.json"),
            str(run_root / "probe.sbatch"),
            str(run_root / "balfrin_submission_package.json"),
            str(run_root / "balfrin_submission_package.md"),
            str(run_root / "balfrin_probe_metrics.json"),
            str(run_root / "balfrin_probe_summary.json"),
            str(run_root / "balfrin_probe_context.txt"),
            str(run_root / "balfrin_probe_full_time.txt"),
            str(run_root / "balfrin_hazard_stage_time.txt"),
            str(run_root / "logs"),
        ],
        "collection_command": _bash_command(
            [
                "PYENV_VERSION=system",
                "uv",
                "run",
                "python",
                "scripts/collect_balfrin_probe_metrics.py",
                "--run-root",
                str(run_root),
                "--probe-manifest",
                str(probe_manifest),
                "--output-json",
                str(run_root / "balfrin_probe_metrics.json"),
            ]
        ),
        "source_paths": {
            "run_root": str(run_root),
            "probe_manifest": str(probe_manifest),
            "command_plan_path": str(run_root / "command_plan.json"),
            "sbatch_script_path": str(run_root / "probe.sbatch"),
        },
        "summary": (
            "SBATCH package kept bounded to the frozen target-area rerun root and the metrics-completion handoff only."
        ),
    }


def _build_preservation_checklist(
    *,
    declared_metrics: set[str],
    declared_run_root_entries: set[str],
    declared_replay_metadata: set[str],
) -> dict[str, Any]:
    required_run_root_entries = []
    missing_run_root_entries: list[str] = []
    for entry in REQUIRED_RUN_ROOT_ENTRIES:
        path = entry["path"]
        declared = path in declared_run_root_entries
        required_run_root_entries.append({**entry, "declared": declared})
        if not declared:
            missing_run_root_entries.append(path)

    required_metrics = []
    missing_metrics: list[str] = []
    for metric in REQUIRED_METRICS:
        declared = metric in declared_metrics
        required_metrics.append({"metric": metric, "declared": declared})
        if not declared:
            missing_metrics.append(metric)

    required_replay_metadata = []
    missing_replay_metadata: list[str] = []
    for field in REQUIRED_REPLAY_METADATA:
        declared = field in declared_replay_metadata
        required_replay_metadata.append({"field": field, "declared": declared})
        if not declared:
            missing_replay_metadata.append(field)

    status = (
        "complete"
        if not missing_run_root_entries and not missing_metrics and not missing_replay_metadata
        else "blocked_missing_inputs"
    )
    return {
        "schema_version": "balfrin_target_area_metrics_completion_rerun_preservation_checklist_v1",
        "status": status,
        "required_metrics": required_metrics,
        "required_run_root_entries": required_run_root_entries,
        "required_replay_metadata": required_replay_metadata,
        "missing_metrics": missing_metrics,
        "missing_run_root_entries": missing_run_root_entries,
        "missing_replay_metadata": missing_replay_metadata,
        "summary": (
            "Preservation checklist complete for the metrics-completion rerun package."
            if status == "complete"
            else "Preservation checklist fails closed until every required metric, run-root file, and replay metadata field is declared."
        ),
    }


def _build_existing_target_area_run_comparison(
    *,
    existing_target_area_run: dict[str, Any],
) -> dict[str, Any]:
    closure_targets = list(REQUIRED_METRICS)
    measured_fields = {
        "job_id": existing_target_area_run.get("job_id"),
        "run_root": existing_target_area_run.get("run_root"),
        "partition": existing_target_area_run.get("partition"),
        "cpus_per_task": existing_target_area_run.get("cpus_per_task"),
        "time_budget": existing_target_area_run.get("time_budget"),
        "slurm_state": existing_target_area_run.get("slurm_state"),
        "exit_code": existing_target_area_run.get("exit_code"),
        "elapsed": existing_target_area_run.get("elapsed"),
        "output_file_count": existing_target_area_run.get("output_file_count"),
        "output_bytes": existing_target_area_run.get("output_bytes"),
        "conditional_curve_row_count": existing_target_area_run.get("conditional_curve_row_count"),
    }
    return {
        "schema_version": "balfrin_target_area_metrics_completion_existing_run_comparison_v1",
        "status": "measured_existing_target_area_run",
        "source": existing_target_area_run.get("source", DEFAULT_EXISTING_TARGET_AREA_SOURCE),
        "existing_target_area_run": existing_target_area_run,
        "measured_fields": measured_fields,
        "closure_targets": closure_targets,
        "closure_target_summary": (
            "The rerun package is scoped only to the missing target-area peak-memory and split validation/hazard output metrics."
        ),
        "missing_from_existing_run": closure_targets,
        "summary": (
            "Existing target-area run recorded the total output footprint and conditional-curve count, but the rerun package is meant to close peak-memory and split validation/hazard output metrics only."
        ),
    }


def _build_replay_metadata(
    *,
    run_root: Path,
    probe_manifest: Path,
    command_plan_path: Path,
    sbatch_script_path: Path,
    existing_target_area_run: dict[str, Any],
    git_commit: str | None,
    metrics_collection_command: str,
    preservation_gate_command: str,
) -> dict[str, Any]:
    return {
        "schema_version": "balfrin_target_area_metrics_completion_replay_metadata_v1",
        "status": "complete" if git_commit else "blocked_missing_inputs",
        "run_root": str(run_root),
        "probe_manifest": str(probe_manifest),
        "command_plan_path": str(command_plan_path),
        "sbatch_script_path": str(sbatch_script_path),
        "metrics_collection_command": metrics_collection_command,
        "preservation_gate_command": preservation_gate_command,
        "existing_target_area_run_root": existing_target_area_run.get("run_root"),
        "existing_target_area_job_id": existing_target_area_run.get("job_id"),
        "git_commit": git_commit,
        "source_paths": {
            "run_root": str(run_root),
            "probe_manifest": str(probe_manifest),
            "command_plan_path": str(command_plan_path),
            "sbatch_script_path": str(sbatch_script_path),
            "existing_target_area_source": existing_target_area_run.get("source", DEFAULT_EXISTING_TARGET_AREA_SOURCE),
        },
        "summary": (
            "Replay metadata preserves the dry-run rerun root, manifest path, SBATCH path, collector command, and the recorded target-area run anchor."
        ),
    }


def _build_hashes(
    *,
    command_plan: dict[str, Any],
    sbatch_script_text: str,
    existing_target_area_run: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": "balfrin_target_area_metrics_completion_hashes_v1",
        "status": "complete",
        "command_plan_sha256": _sha256_json(command_plan),
        "sbatch_script_sha256": _sha256_text(sbatch_script_text),
        "existing_target_area_run_sha256": _sha256_json(existing_target_area_run),
    }


def _section_status(section: dict[str, Any]) -> str:
    return str(section.get("status") or "unknown")


def _section_evidence_type(section_name: str) -> str:
    if section_name == "existing_target_area_run_comparison":
        return "measured"
    if section_name == "preservation_checklist":
        return "template_only"
    return "template_only"


def _build_section_provenance_profile(sections: list[tuple[str, dict[str, Any]]]) -> list[dict[str, Any]]:
    profile = []
    for section_name, section_payload in sections:
        profile.append(
            {
                "section": section_name,
                "status": _section_status(section_payload),
                "evidence_type": _section_evidence_type(section_name),
                "source_paths": _safe_list(section_payload.get("source_paths")) if isinstance(section_payload.get("source_paths"), list) else _safe_mapping(section_payload.get("source_paths")),
            }
        )
    return profile


def _package_status(section_provenance_profile: list[dict[str, Any]], preservation_status: str) -> str:
    allowed_statuses = {"complete", "measured_existing_target_area_run"}
    if preservation_status == "complete" and all(section.get("status") in allowed_statuses for section in section_provenance_profile):
        return "complete_rerun_package"
    return "partial_rerun_package"


def build_report(
    evidence_override: dict[str, Any] | None = None,
    *,
    run_root: Path | None = None,
    probe_manifest: Path | None = None,
    artifact_dir: Path | None = None,
) -> dict[str, Any]:
    run_root = (run_root or DEFAULT_RERUN_RUN_ROOT).resolve()
    probe_manifest = (probe_manifest or DEFAULT_PROBE_MANIFEST).resolve()
    artifact_dir = (artifact_dir or DEFAULT_ARTIFACT_DIR).resolve()

    if evidence_override is not None:
        if isinstance(evidence_override.get("rerun_package_report"), dict):
            return dict(evidence_override["rerun_package_report"])
        if evidence_override.get("missing_inputs"):
            return blocked_report(
                [str(item) for item in evidence_override.get("missing_inputs", [])],
                reason="required rerun-package inputs are missing",
                run_root=run_root,
                probe_manifest=probe_manifest,
                artifact_dir=artifact_dir,
            )

    if evidence_override is None:
        evidence_override = {}

    declared_metrics = set(
        _safe_list(evidence_override.get("declared_metrics")) or REQUIRED_METRICS
    )
    declared_run_root_entries = set(
        _safe_list(evidence_override.get("declared_run_root_entries"))
        or [entry["path"] for entry in REQUIRED_RUN_ROOT_ENTRIES]
    )
    declared_replay_metadata = set(
        _safe_list(evidence_override.get("declared_replay_metadata")) or REQUIRED_REPLAY_METADATA
    )

    existing_target_area_run = _safe_mapping(
        evidence_override.get("existing_target_area_run") or _default_existing_target_area_run()
    )
    command_plan = _safe_mapping(evidence_override.get("command_plan"))
    if not command_plan:
        command_plan = {
            "schema_version": "balfrin_target_area_metrics_completion_rerun_command_plan_v1",
            "status": "complete",
            "run_root": str(run_root),
            "probe_manifest": str(probe_manifest),
            "run_id": str(evidence_override.get("run_id") or DEFAULT_RERUN_RUN_ID),
        }

    run_id = str(evidence_override.get("run_id") or DEFAULT_RERUN_RUN_ID)
    partition = str(evidence_override.get("partition") or DEFAULT_PARTITION)
    time_budget = str(evidence_override.get("time_budget") or DEFAULT_TIME_BUDGET)
    nodes = int(evidence_override.get("nodes") or DEFAULT_NODES)
    ntasks = int(evidence_override.get("ntasks") or DEFAULT_NTASKS)
    cpus_per_task = int(evidence_override.get("cpus_per_task") or DEFAULT_CPUS_PER_TASK)

    sbatch_script_text = str(evidence_override.get("sbatch_script_text") or submit._build_sbatch_script(  # noqa: SLF001
        run_root=run_root,
        probe_manifest=probe_manifest,
        partition=partition,
        time_budget=time_budget,
        nodes=nodes,
        ntasks=ntasks,
        cpus_per_task=cpus_per_task,
    ))

    rerun_command_plan = _build_dry_run_command_plan(
        run_root=run_root,
        probe_manifest=probe_manifest,
        artifact_dir=artifact_dir,
        run_id=run_id,
        partition=partition,
        time_budget=time_budget,
        nodes=nodes,
        ntasks=ntasks,
        cpus_per_task=cpus_per_task,
        sbatch_script_text=sbatch_script_text,
    )
    if isinstance(evidence_override.get("dry_run_command_plan"), dict):
        rerun_command_plan = dict(evidence_override["dry_run_command_plan"])

    sbatch_package = _build_sbatch_package(
        run_root=run_root,
        probe_manifest=probe_manifest,
        run_id=run_id,
        partition=partition,
        time_budget=time_budget,
        nodes=nodes,
        ntasks=ntasks,
        cpus_per_task=cpus_per_task,
        command_plan=command_plan,
    )
    if isinstance(evidence_override.get("sbatch_package"), dict):
        sbatch_package = dict(evidence_override["sbatch_package"])

    preservation_checklist = _build_preservation_checklist(
        declared_metrics=declared_metrics,
        declared_run_root_entries=declared_run_root_entries,
        declared_replay_metadata=declared_replay_metadata,
    )
    if isinstance(evidence_override.get("preservation_checklist"), dict):
        preservation_checklist = dict(evidence_override["preservation_checklist"])

    existing_run_comparison = _build_existing_target_area_run_comparison(
        existing_target_area_run=existing_target_area_run,
    )
    if isinstance(evidence_override.get("existing_target_area_run_comparison"), dict):
        existing_run_comparison = dict(evidence_override["existing_target_area_run_comparison"])

    metrics_collection_command = sbatch_package.get("collection_command") or rerun_command_plan.get("collect_command")
    preservation_gate_command = rerun_command_plan.get("preservation_gate_command")
    replay_metadata = _build_replay_metadata(
        run_root=run_root,
        probe_manifest=probe_manifest,
        command_plan_path=run_root / "command_plan.json",
        sbatch_script_path=run_root / "probe.sbatch",
        existing_target_area_run=existing_target_area_run,
        git_commit=submit._git_info(ROOT).get("commit"),  # noqa: SLF001
        metrics_collection_command=str(metrics_collection_command),
        preservation_gate_command=str(preservation_gate_command),
    )
    if isinstance(evidence_override.get("replay_metadata"), dict):
        replay_metadata = dict(evidence_override["replay_metadata"])

    hashes = _build_hashes(
        command_plan=command_plan,
        sbatch_script_text=sbatch_script_text,
        existing_target_area_run=existing_target_area_run,
    )
    if isinstance(evidence_override.get("hashes"), dict):
        hashes = dict(evidence_override["hashes"])

    sections = [
        ("rerun_command_plan", rerun_command_plan),
        ("sbatch_package", sbatch_package),
        ("preservation_checklist", preservation_checklist),
        ("existing_target_area_run_comparison", existing_run_comparison),
        ("replay_metadata", replay_metadata),
        ("hashes", hashes),
    ]
    section_provenance_profile = _build_section_provenance_profile(sections)
    package_status = _package_status(section_provenance_profile, preservation_checklist.get("status", "unknown"))
    measured_count = sum(1 for entry in section_provenance_profile if entry["evidence_type"] == "measured")
    template_count = sum(1 for entry in section_provenance_profile if entry["evidence_type"] == "template_only")
    blocked_count = sum(1 for entry in section_provenance_profile if entry["status"] == "blocked_missing_inputs")

    report = {
        "schema_version": SCHEMA_VERSION,
        "package_status": package_status,
        "package_provenance_status": "mixed_provenance" if measured_count and template_count else package_status,
        "package_artifact_dir": str(artifact_dir),
        "run_root": str(run_root),
        "probe_manifest": str(probe_manifest),
        "package_summary": {
            "status": package_status,
            "summary": summarize_package(
                package_status,
                rerun_command_plan,
                sbatch_package,
                preservation_checklist,
                existing_run_comparison,
                replay_metadata,
            ),
            "section_counts": {
                "measured": measured_count,
                "template_only": template_count,
                "blocked_missing_inputs": blocked_count,
            },
        },
        "rerun_command_plan": rerun_command_plan,
        "sbatch_package": sbatch_package,
        "preservation_checklist": preservation_checklist,
        "existing_target_area_run_comparison": existing_run_comparison,
        "replay_metadata": replay_metadata,
        "hashes": hashes,
        "claim_boundaries": {
            "operational_claims_allowed": False,
            "physical_probability_claims_allowed": False,
            "annual_frequency_claims_allowed": False,
            "risk_exposure_vulnerability_claims_allowed": False,
            "scale_up_authorized": False,
            "distributed_execution_authorized": False,
        },
        "section_provenance_profile": section_provenance_profile,
        "source_paths": {
            "artifact_dir": str(artifact_dir),
            "run_root": str(run_root),
            "probe_manifest": str(probe_manifest),
            "existing_target_area_run_root": str(DEFAULT_EXISTING_TARGET_AREA_RUN_ROOT),
            "existing_target_area_source": DEFAULT_EXISTING_TARGET_AREA_SOURCE,
        },
        "missing_inputs": [],
    }
    return report


def summarize_package(
    package_status: str,
    rerun_command_plan: dict[str, Any],
    sbatch_package: dict[str, Any],
    preservation_checklist: dict[str, Any],
    existing_run_comparison: dict[str, Any],
    replay_metadata: dict[str, Any],
) -> str:
    if package_status == "missing_rerun_package":
        return "Target-area metrics completion rerun package is blocked because required package inputs are missing."
    closure_targets = existing_run_comparison.get("closure_targets", [])
    missing_metrics = preservation_checklist.get("missing_metrics", [])
    missing_run_root_entries = preservation_checklist.get("missing_run_root_entries", [])
    missing_replay_metadata = preservation_checklist.get("missing_replay_metadata", [])
    return (
        "Dry-run target-area rerun package prepared for metrics completion only; "
        "no live submission is authorized. "
        f"{len(closure_targets)} closure targets, "
        f"{len(missing_metrics)} missing metrics declarations, "
        f"{len(missing_run_root_entries)} missing run-root declarations, "
        f"{len(missing_replay_metadata)} missing replay metadata fields, "
        f"command plan status {rerun_command_plan.get('status', 'unknown')}."
    )


def blocked_report(
    missing_inputs: list[str],
    *,
    reason: str,
    run_root: Path,
    probe_manifest: Path,
    artifact_dir: Path,
) -> dict[str, Any]:
    section_names = (
        "rerun_command_plan",
        "sbatch_package",
        "preservation_checklist",
        "existing_target_area_run_comparison",
        "replay_metadata",
        "hashes",
    )
    section_provenance_profile = [
        {
            "section": section_name,
            "status": "blocked_missing_inputs",
            "evidence_type": "blocked",
            "source_paths": [],
        }
        for section_name in section_names
    ]
    claim_boundaries = {
        "operational_claims_allowed": False,
        "physical_probability_claims_allowed": False,
        "annual_frequency_claims_allowed": False,
        "risk_exposure_vulnerability_claims_allowed": False,
        "scale_up_authorized": False,
        "distributed_execution_authorized": False,
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "package_status": "missing_rerun_package",
        "package_provenance_status": "blocked_missing_inputs",
        "package_artifact_dir": str(artifact_dir),
        "run_root": str(run_root),
        "probe_manifest": str(probe_manifest),
        "package_summary": {
            "status": "missing_rerun_package",
            "summary": reason,
            "section_counts": {
                "measured": 0,
                "template_only": 0,
                "blocked_missing_inputs": len(section_names),
            },
        },
        "rerun_command_plan": {"status": "blocked_missing_inputs"},
        "sbatch_package": {"status": "blocked_missing_inputs", "launch_authorized": False},
        "preservation_checklist": {
            "status": "blocked_missing_inputs",
            "missing_metrics": list(REQUIRED_METRICS),
            "missing_run_root_entries": [entry["path"] for entry in REQUIRED_RUN_ROOT_ENTRIES],
            "missing_replay_metadata": list(REQUIRED_REPLAY_METADATA),
        },
        "existing_target_area_run_comparison": {
            "status": "blocked_missing_inputs",
            "closure_targets": list(REQUIRED_METRICS),
        },
        "replay_metadata": {
            "status": "blocked_missing_inputs",
            "run_root": str(run_root),
            "probe_manifest": str(probe_manifest),
        },
        "hashes": {"status": "blocked_missing_inputs"},
        "claim_boundaries": claim_boundaries,
        "section_provenance_profile": section_provenance_profile,
        "source_paths": {
            "artifact_dir": str(artifact_dir),
            "run_root": str(run_root),
            "probe_manifest": str(probe_manifest),
            "existing_target_area_run_root": str(DEFAULT_EXISTING_TARGET_AREA_RUN_ROOT),
            "existing_target_area_source": DEFAULT_EXISTING_TARGET_AREA_SOURCE,
        },
        "missing_inputs": list(missing_inputs),
        "blocked_reason": reason,
    }


def render_text_report(report: dict[str, Any]) -> str:
    lines = [
        "Balfrin Target-Area Metrics Completion Rerun Package",
        f"schema_version: {report.get('schema_version', 'unknown')}",
        f"package_status: {report.get('package_status', 'unknown')}",
        f"package_provenance_status: {report.get('package_provenance_status', 'unknown')}",
        f"package_artifact_dir: {report.get('package_artifact_dir', 'unknown')}",
        f"run_root: {report.get('run_root', 'unknown')}",
        f"probe_manifest: {report.get('probe_manifest', 'unknown')}",
        "package_summary:",
        f"  status: {report.get('package_summary', {}).get('status', 'unknown')}",
        f"  summary: {report.get('package_summary', {}).get('summary', '')}",
        f"  section_counts: {report.get('package_summary', {}).get('section_counts', {})}",
        "rerun_command_plan:",
        f"  status: {report.get('rerun_command_plan', {}).get('status', 'unknown')}",
        f"  dry_run_command: {report.get('rerun_command_plan', {}).get('dry_run_command', '')}",
        f"  generate_only_command: {report.get('rerun_command_plan', {}).get('generate_only_command', '')}",
        f"  collect_command: {report.get('rerun_command_plan', {}).get('collect_command', '')}",
        f"  preservation_gate_command: {report.get('rerun_command_plan', {}).get('preservation_gate_command', '')}",
        "sbatch_package:",
        f"  status: {report.get('sbatch_package', {}).get('status', 'unknown')}",
        f"  launch_authorized: {report.get('sbatch_package', {}).get('launch_authorized', False)}",
        f"  command_plan_path: {report.get('sbatch_package', {}).get('command_plan_path', '')}",
        f"  sbatch_script_path: {report.get('sbatch_package', {}).get('sbatch_script_path', '')}",
        "preservation_checklist:",
        f"  status: {report.get('preservation_checklist', {}).get('status', 'unknown')}",
        f"  missing_metrics: {report.get('preservation_checklist', {}).get('missing_metrics', [])}",
        f"  missing_run_root_entries: {report.get('preservation_checklist', {}).get('missing_run_root_entries', [])}",
        f"  missing_replay_metadata: {report.get('preservation_checklist', {}).get('missing_replay_metadata', [])}",
        "existing_target_area_run_comparison:",
        f"  status: {report.get('existing_target_area_run_comparison', {}).get('status', 'unknown')}",
        f"  closure_targets: {report.get('existing_target_area_run_comparison', {}).get('closure_targets', [])}",
        f"  measured_fields: {report.get('existing_target_area_run_comparison', {}).get('measured_fields', {})}",
        "replay_metadata:",
        f"  status: {report.get('replay_metadata', {}).get('status', 'unknown')}",
        f"  existing_target_area_run_root: {report.get('replay_metadata', {}).get('existing_target_area_run_root', '')}",
        f"  existing_target_area_job_id: {report.get('replay_metadata', {}).get('existing_target_area_job_id', '')}",
        f"  git_commit: {report.get('replay_metadata', {}).get('git_commit', '')}",
        "hashes:",
        f"  command_plan_sha256: {report.get('hashes', {}).get('command_plan_sha256', '')}",
        f"  sbatch_script_sha256: {report.get('hashes', {}).get('sbatch_script_sha256', '')}",
        f"  existing_target_area_run_sha256: {report.get('hashes', {}).get('existing_target_area_run_sha256', '')}",
        "claim_boundaries:",
    ]
    for key in (
        "operational_claims_allowed",
        "physical_probability_claims_allowed",
        "annual_frequency_claims_allowed",
        "risk_exposure_vulnerability_claims_allowed",
        "scale_up_authorized",
        "distributed_execution_authorized",
    ):
        lines.append(f"  {key}: {report.get('claim_boundaries', {}).get(key, False)}")
    lines.append("section_provenance_profile:")
    for section in report.get("section_provenance_profile", []):
        lines.append(
            f"  - {section.get('section', 'unknown')}: {section.get('evidence_type', 'unknown')} | {section.get('status', 'unknown')}"
        )
    if report.get("missing_inputs"):
        lines.append("missing_inputs:")
        lines.extend(f"  - {item}" for item in report["missing_inputs"])
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
        report = build_report(
            evidence_override,
            run_root=args.run_root,
            probe_manifest=args.probe_manifest,
            artifact_dir=args.artifact_dir,
        )
    except (OSError, ValueError) as exc:
        print(f"balfrin target-area metrics completion rerun package error: {exc}", file=sys.stderr)
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
    return 0 if report["package_status"] == "complete_rerun_package" else 2


if __name__ == "__main__":
    raise SystemExit(main())
