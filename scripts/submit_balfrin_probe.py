#!/usr/bin/env python3
"""Generate and submit SLURM-first balfrin probe runs from tracked probe manifests."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]

VALID_PARTITIONS = {
    "postproc",
    "pp-short",
    "pp-long",
    "pp-serial",
}

DEFAULT_PARTITION = "postproc"
DEFAULT_SBATCH_TIME = "00:30:00"
DEFAULT_NODES = 1
DEFAULT_NTASKS = 1
DEFAULT_CPUS_PER_TASK = 16
PACKAGE_SCHEMA_VERSION = "balfrin_submission_package_v1"
PACKAGE_BASENAME = "balfrin_submission_package"
PACKAGE_EXECUTION_STATUS = "deferred_pending_authorization"
SUBMISSION_REPORT_SCHEMA_VERSION = "balfrin_scheduler_submission_report_v1"
SUBMISSION_REPORT_BASENAME = "balfrin_submission_report"
AUTHORIZED_SUBMISSION_REPORT_SCHEMA_VERSION = "balfrin_authorized_submission_report_v1"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "probe_manifest",
        type=Path,
        nargs="?",
        help="Tracked probe manifest used to generate the command plan.",
    )
    parser.add_argument(
        "--run-root",
        type=Path,
        help="Optional explicit run root under which outputs and script are generated.",
    )
    parser.add_argument(
        "--probe-id",
        help="Optional probe identifier for run-root grouping.",
    )
    parser.add_argument(
        "--run-id",
        help="Optional deterministic run id. If omitted, uses run id from manifest in dry-run and timestamp otherwise.",
    )
    parser.add_argument(
        "--partition",
        default=DEFAULT_PARTITION,
        choices=sorted(VALID_PARTITIONS),
        help="SLURM partition (default: postproc).",
    )
    parser.add_argument(
        "--time",
        default=DEFAULT_SBATCH_TIME,
        help="SLURM time budget (default: 00:30:00).",
    )
    parser.add_argument(
        "--nodes",
        type=int,
        default=DEFAULT_NODES,
        help="SLURM nodes (default: 1).",
    )
    parser.add_argument(
        "--ntasks",
        type=int,
        default=DEFAULT_NTASKS,
        help="SLURM ntasks (default: 1).",
    )
    parser.add_argument(
        "--cpus-per-task",
        type=int,
        default=DEFAULT_CPUS_PER_TASK,
        help="SLURM cpus-per-task (default: 16).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned script and paths without writing files.",
    )
    parser.add_argument(
        "--generate-only",
        action="store_true",
        help="Generate the submission package artifacts and sbatch script, but do not submit.",
    )
    parser.add_argument(
        "--submit",
        action="store_true",
        help="Generate and submit a SLURM job (implemented, but not exercised in this task).",
    )
    parser.add_argument(
        "--authorized-submit",
        action="store_true",
        help=(
            "Generate and submit the smallest bounded multi-zone Balfrin job only after validating a reviewed "
            "handoff package and live-run authorization record."
        ),
    )
    parser.add_argument(
        "--collect",
        action="store_true",
        help="Collect metrics from an existing run root.",
    )
    parser.add_argument(
        "--local-command-plan",
        action="store_true",
        help="Generate and print command plan only, no SLURM artifacts.",
    )
    parser.add_argument(
        "--slurm-timeout",
        type=int,
        default=60,
        help="Timeout for sbatch submission call in seconds.",
    )
    parser.add_argument(
        "--reviewed-handoff-package",
        type=Path,
        default=None,
        help="Reviewed handoff package JSON required for --authorized-submit.",
    )
    parser.add_argument(
        "--authorization-record",
        type=Path,
        default=None,
        help="Live-run authorization record YAML or JSON required for --authorized-submit.",
    )
    parser.add_argument(
        "--balfrin-access-preflight-json",
        type=Path,
        default=None,
        help=(
            "Optional JSON output from check_balfrin_remote_access_preflight.py. "
            "When omitted with --authorized-submit, the read-only access preflight is run before any scheduler submit."
        ),
    )

    args = parser.parse_args(argv)

    modes = (
        args.dry_run,
        args.generate_only,
        args.submit,
        args.authorized_submit,
        args.collect,
        args.local_command_plan,
    )
    if sum(1 for mode in modes if mode) != 1:
        parser.error(
            "exactly one of --dry-run, --generate-only, --submit, --authorized-submit, "
            "--collect, --local-command-plan is required"
        )
    if args.collect:
        if args.run_root is None:
            parser.error("--run-root is required with --collect")
        if args.probe_manifest is not None:
            parser.error("--collect does not accept a probe manifest argument")
    elif args.probe_manifest is None:
        parser.error("probe_manifest is required unless --collect is used")
    if args.authorized_submit:
        if args.reviewed_handoff_package is None:
            parser.error("--reviewed-handoff-package is required with --authorized-submit")
        if args.authorization_record is None:
            parser.error("--authorization-record is required with --authorized-submit")

    return args


def _load_plan_validator() -> Any:
    validator_path = ROOT / "scripts" / "validate_public_real_site_conditional_pilot_run.py"
    spec = importlib.util.spec_from_file_location(
        "validate_public_real_site_conditional_pilot_run",
        validator_path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load command-plan validator module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def _load_collect_script() -> Any:
    collector_path = ROOT / "scripts" / "collect_balfrin_probe_metrics.py"
    spec = importlib.util.spec_from_file_location(
        "collect_balfrin_probe_metrics",
        collector_path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load probe metrics collector module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def _load_yaml_or_json(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"unable to read structured document: {path}: {exc}") from exc

    if path.suffix.lower() in {".json"}:
        payload = json.loads(text)
    else:
        payload = yaml.safe_load(text)

    if not isinstance(payload, dict):
        raise ValueError(f"structured document must be a mapping: {path}")
    return payload


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _structured_document_status(path: Path, *, label: str) -> dict[str, Any]:
    if not path.exists():
        return {
            "status": "missing",
            "label": label,
            "path": str(path),
            "sha256": None,
            "value": None,
            "blocked_reason": f"{label} is missing: {path}",
        }
    payload = _load_yaml_or_json(path)
    return {
        "status": "loaded",
        "label": label,
        "path": str(path),
        "sha256": _sha256_file(path),
        "value": payload,
        "blocked_reason": "",
    }


def _load_readiness_checker() -> Any:
    checker_path = ROOT / "scripts" / "check_balfrin_tschamut_readiness.py"
    spec = importlib.util.spec_from_file_location(
        "check_balfrin_tschamut_readiness",
        checker_path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load readiness checker module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def _load_ensemble_frontier() -> Any:
    frontier_path = ROOT / "scripts" / "summarize_balfrin_ensemble_frontier.py"
    spec = importlib.util.spec_from_file_location(
        "summarize_balfrin_ensemble_frontier",
        frontier_path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load ensemble frontier helper module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def _load_feasibility_probe() -> Any:
    feasibility_path = ROOT / "scripts" / "summarize_bounded_next_ensemble_feasibility_probe.py"
    spec = importlib.util.spec_from_file_location(
        "submit_balfrin_probe_feasibility",
        feasibility_path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load bounded next-ensemble feasibility helper module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def _load_authorization_preflight() -> Any:
    preflight_path = ROOT / "scripts" / "preflight_balfrin_smallest_multi_zone_probe_authorization.py"
    spec = importlib.util.spec_from_file_location(
        "preflight_balfrin_smallest_multi_zone_probe_authorization",
        preflight_path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load smallest multi-zone authorization preflight helper module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def _read_command_plan(probe_manifest: Path) -> tuple[dict[str, Any], str]:
    module = _load_plan_validator()
    manifest = module.read_yaml(probe_manifest)
    command_plan = module.build_command_plan(manifest)
    if command_plan.get("run_status") == "no_go":
        raise ValueError(
            "probe manifest resolved to no_go plan; command execution would be blocked"
        )
    run_id = str(command_plan.get("run_id", "")).strip()
    if not run_id:
        raise ValueError("generated command-plan does not contain run_id")
    return command_plan, run_id


def _safe_fragment(value: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in value.strip())
    return cleaned or "probe"


def _timestamp_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_utc")


def _default_run_root(probe_id: str, run_id: str) -> Path:
    scratch_root = Path(os.environ.get("SCRATCH", "/scratch")).resolve()
    return scratch_root / "rust_rockfall" / "probes" / _safe_fragment(probe_id) / _safe_fragment(run_id)


def _git_info(repo_root: Path) -> dict[str, str | None]:
    info: dict[str, str | None] = {"branch": None, "commit": None}
    try:
        info["branch"] = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        info["commit"] = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return info
    return info


def _to_repo_path(value: str, *, repo_root: Path) -> Path:
    path = Path(str(value).strip().replace("\\", "/"))
    if path.is_absolute():
        return path
    return (repo_root / path).resolve()


def _collect_output_roots(command_plan: dict[str, Any], *, repo_root: Path) -> list[str]:
    commands = command_plan.get("commands")
    if not isinstance(commands, list):
        return []

    root_paths: set[Path] = set()
    root_flags = {
        "--output-dir",
    }
    dir_flags = {
        "--ensemble-trajectories-dir",
        "--ensemble-impact-events-dir",
    }
    file_flags = {
        "--diagnostics",
        "--trajectory",
        "--deposition",
        "--map-package-manifest-json",
        "--pilot-gis-package-manifest-json",
    }

    for entry in commands:
        if not isinstance(entry, dict):
            continue
        command = entry.get("command")
        if not isinstance(command, list):
            continue
        tokens = [str(token) for token in command]
        for idx, token in enumerate(tokens):
            if token not in root_flags | dir_flags | file_flags:
                continue
            if idx + 1 >= len(tokens):
                continue
            resolved = _to_repo_path(tokens[idx + 1], repo_root=repo_root)
            if token in root_flags:
                root_paths.add(resolved)
            else:
                root_paths.add(resolved.parent)

    return sorted(str(path) for path in root_paths)


def _collect_reduced_output_settings(command_plan: dict[str, Any]) -> dict[str, Any]:
    commands = command_plan.get("commands")
    if not isinstance(commands, list):
        return {}

    settings: dict[str, Any] = {}
    flag_map = {
        "--conditional-curve-export": "conditional_curve_export",
        "--grid-csv-export": "grid_csv_export",
        "--trajectory-workers": "trajectory_workers",
        "--reducer-workers": "reducer_workers",
        "--map-product-id": "map_product_id",
        "--probability-mode": "probability_mode",
        "--normalization-scope": "normalization_scope",
    }
    boolean_flags = {
        "--export-geotiff": "export_geotiff",
        "--pilot-gis-package": "pilot_gis_package",
        "--no-plots": "no_plots",
    }

    for entry in commands:
        if not isinstance(entry, dict):
            continue
        command = entry.get("command")
        if not isinstance(command, list):
            continue
        tokens = [str(token) for token in command]
        for idx, token in enumerate(tokens):
            if token in flag_map and idx + 1 < len(tokens):
                value: str | int | None = tokens[idx + 1]
                if token in {"--trajectory-workers", "--reducer-workers"}:
                    try:
                        value = int(tokens[idx + 1])
                    except ValueError:
                        value = tokens[idx + 1]
                settings[flag_map[token]] = value
            elif token in boolean_flags:
                settings[boolean_flags[token]] = True

    return settings


def _build_expected_outputs(run_root: Path) -> list[str]:
    return [
        str(run_root / "command_plan.json"),
        str(run_root / "probe.sbatch"),
        str(run_root / f"{PACKAGE_BASENAME}.json"),
        str(run_root / f"{PACKAGE_BASENAME}.md"),
        str(run_root / "logs"),
    ]


def _build_collection_instructions(run_root: Path) -> list[str]:
    return [
        f"PYENV_VERSION=system uv run python scripts/submit_balfrin_probe.py --collect --run-root {run_root}",
        f"PYENV_VERSION=system uv run python scripts/collect_balfrin_probe_metrics.py --run-root {run_root}",
    ]


def _build_operator_sequence(
    *,
    run_root: Path,
    run_id: str,
    probe_manifest: Path,
    partition: str,
    time_budget: str,
    nodes: int,
    ntasks: int,
    cpus_per_task: int,
) -> dict[str, list[str]]:
    submit_base = (
        "PYENV_VERSION=system uv run python scripts/submit_balfrin_probe.py "
        f"{probe_manifest} --run-root {run_root} --run-id {run_id} "
        f"--partition {partition} --time {time_budget} --nodes {nodes} "
        f"--ntasks {ntasks} --cpus-per-task {cpus_per_task}"
    )
    return {
        "preflight": [
            f"RUN_MANIFEST={probe_manifest}",
            "PYENV_VERSION=system uv run python scripts/check_balfrin_tschamut_readiness.py \"$RUN_MANIFEST\" --format both",
        ],
        "generate_only": [f"{submit_base} --generate-only"],
        "submit": [f"{submit_base} --submit"],
        "stop": [
            "JOB_ID=<job-id-from-sbatch-or-sacct>",
            "scancel \"${JOB_ID}\"",
        ],
        "resume": [
            "# Reuse the same RUN_ROOT and RUN_ID so the job picks up the same deterministic layout.",
            f"{submit_base} --submit",
        ],
        "collect": [
            f"PYENV_VERSION=system uv run python scripts/submit_balfrin_probe.py --collect --run-root {run_root}",
            f"PYENV_VERSION=system uv run python scripts/collect_balfrin_probe_metrics.py --run-root {run_root}",
        ],
        "verify": [
            f"PYENV_VERSION=system uv run python scripts/summarize_balfrin_post_run_interpretation_gate.py --format json --evidence-json {run_root}/balfrin_post_run_evidence.json",
            f"PYENV_VERSION=system uv run python scripts/submit_balfrin_probe.py --collect --run-root {run_root}",
        ],
        "cleanup": [
            f"rm -rf {run_root}",
        ],
        "failure_handoff": [
            f"tar -C {run_root} -czf /tmp/{_safe_fragment(run_id)}_balfrin_probe_handoff.tgz logs command_plan.json probe.sbatch balfrin_submission_package.json balfrin_submission_package.md balfrin_probe_summary.json balfrin_probe_context.txt balfrin_probe_full_time.txt balfrin_hazard_stage_time.txt",
        ],
    }


def _build_submission_package_report(
    *,
    run_root: Path,
    probe_manifest: Path,
    command_plan: dict[str, Any],
    partition: str,
    time_budget: str,
    nodes: int,
    ntasks: int,
    cpus_per_task: int,
    frontier_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    repo_root = ROOT.resolve()
    readiness_module = _load_readiness_checker()
    readiness_report = readiness_module.collect_readiness_report(
        repo_root=repo_root,
        run_manifest_path=probe_manifest.resolve(),
    )
    if frontier_report is None:
        frontier_report = _build_fast_submission_frontier_report()
    git_info = _git_info(repo_root)
    output_roots = _collect_output_roots(command_plan, repo_root=repo_root)
    reduced_output_settings = _collect_reduced_output_settings(command_plan)
    generated_output_roots = [str(run_root.resolve()), str((run_root / "logs").resolve())]
    run_id = str(command_plan.get("run_id") or "").strip() or run_root.name
    recommended_next_probe = dict(frontier_report.get("minimum_useful_ensemble_recommendation") or {})
    if recommended_next_probe.get("validation_output_mode") and "validation_output_mode" not in reduced_output_settings:
        reduced_output_settings["validation_output_mode"] = recommended_next_probe["validation_output_mode"]
    if recommended_next_probe.get("expected_artifact_families") and "expected_artifact_families" not in reduced_output_settings:
        reduced_output_settings["expected_artifact_families"] = list(recommended_next_probe["expected_artifact_families"])
    operator_sequence = _build_operator_sequence(
        run_root=run_root,
        run_id=run_id,
        probe_manifest=probe_manifest.resolve(),
        partition=partition,
        time_budget=time_budget,
        nodes=nodes,
        ntasks=ntasks,
        cpus_per_task=cpus_per_task,
    )

    return {
        "schema_version": PACKAGE_SCHEMA_VERSION,
        "package_mode": "generate-only",
        "execution_status": PACKAGE_EXECUTION_STATUS,
        "launch_authorized": False,
        "probe_manifest": str(probe_manifest.resolve()),
        "expected_run_root": str(run_root.resolve()),
        "run_root": str(run_root.resolve()),
        "run_id": run_id,
        "repository": {
            "repo_root": str(repo_root),
            "branch": git_info.get("branch") or readiness_report.get("branch"),
            "commit": git_info.get("commit") or readiness_report.get("commit"),
        },
        "slurm": {
            "partition": partition,
            "time": time_budget,
            "nodes": nodes,
            "ntasks": ntasks,
            "cpus_per_task": cpus_per_task,
        },
        "scratch_paths": {
            "scratch_root": str(Path(os.environ.get("SCRATCH", "/scratch")).resolve()),
            "uv_cache_dir": str(Path(os.environ.get("UV_CACHE_DIR", "/scratch/.cache/uv")).resolve()),
            "cargo_target_dir": str(Path(os.environ.get("CARGO_TARGET_DIR", "/scratch/rust_rockfall/target")).resolve()),
        },
        "input_checks": {
            "status": readiness_report.get("status"),
            "blocking_checks": readiness_report.get("blocking_checks", []),
            "checks": readiness_report.get("checks", []),
        },
        "command_plan_path": str(run_root / "command_plan.json"),
        "sbatch_script_path": str(run_root / "probe.sbatch"),
        "command_script_path": str(run_root / "probe.sbatch"),
        "command_script": str(run_root / "probe.sbatch"),
        "generated_output_roots": generated_output_roots,
        "ignored_output_roots": output_roots,
        "recommended_next_probe": {
            "frontier_status": frontier_report.get("frontier_status"),
            "recommendation_class": frontier_report.get("recommendation_class"),
            "recommendation_reason": frontier_report.get("recommendation_reason"),
            "minimum_useful_ensemble_recommendation": recommended_next_probe,
        },
        "reduced_output_settings": reduced_output_settings,
        "metrics_collection_command": f"PYENV_VERSION=system uv run python scripts/collect_balfrin_probe_metrics.py --run-root {run_root}",
        "stop_resume_notes": [
            "Keep the same RUN_ROOT and RUN_ID when resuming or collecting.",
            "Stop with scancel after the job id is known, then rerun the same submit command from the same checkout.",
            "Do not create a branch or worktree, and do not commit generated run artifacts from the run root.",
        ],
        "ignored_artifacts": [
            str((run_root / "command_plan.json").resolve()),
            str((run_root / "probe.sbatch").resolve()),
            str((run_root / f"{PACKAGE_BASENAME}.json").resolve()),
            str((run_root / f"{PACKAGE_BASENAME}.md").resolve()),
            str((run_root / "balfrin_probe_summary.json").resolve()),
            str((run_root / "balfrin_probe_context.txt").resolve()),
            str((run_root / "balfrin_probe_full_time.txt").resolve()),
            str((run_root / "balfrin_hazard_stage_time.txt").resolve()),
            str((run_root / "logs").resolve()),
        ],
        "operator_sequence": operator_sequence,
        "expected_outputs": _build_expected_outputs(run_root),
        "collection_instructions": _build_collection_instructions(run_root),
    }


def _build_fast_submission_frontier_report() -> dict[str, Any]:
    """Build a bounded-probe recommendation without live full-frontier scans.

    The full Balfrin frontier helper composes several live reports and may be
    slow or blocked in a fresh checkout. Submission-package generation should
    stay deterministic and quick because it is an unlaunched operator handoff.
    It therefore uses the bounded feasibility helper as the source for the
    exact probe package fields while preserving fail-closed status when that
    helper is blocked.
    """

    feasibility_module = _load_feasibility_probe()
    try:
        reduced_case = yaml.safe_load(feasibility_module.REDUCED_CASE.read_text(encoding="utf-8")) or {}
        target_gate = yaml.safe_load(feasibility_module.TARGET_GATE_RECORD.read_text(encoding="utf-8")) or {}
        metadata_contract = feasibility_module.summarize_optional_probabilistic_metadata_contract(reduced_case)
    except Exception as exc:  # pragma: no cover - defensive dry-run fallback.
        return {
            "frontier_status": "blocked_missing_inputs",
            "recommendation_class": "blocked_pending_helper_contract",
            "recommendation_reason": str(exc),
            "minimum_useful_ensemble_recommendation": {},
        }

    metadata_status = str(metadata_contract.get("status") or "")
    if metadata_status != "complete":
        return {
            "frontier_status": "blocked_missing_inputs",
            "recommendation_class": "blocked_pending_helper_contract",
            "recommendation_reason": (
                f"bounded next-ensemble feasibility metadata is blocked: {metadata_status}"
            ),
            "minimum_useful_ensemble_recommendation": {},
        }

    validation_output_mode = str(
        dict(reduced_case.get("outputs") or {}).get("validation_output_mode") or ""
    )
    validation_run = dict(dict(target_gate.get("execution_evidence") or {}).get("validation_run") or {})
    trajectory_count = validation_run.get("validation_simulated_trajectory_count")
    try:
        trajectory_count = int(trajectory_count)
    except (TypeError, ValueError):
        trajectory_count = None
    recommendation = {
        "decision": "defer",
        "probe_id": "tschamut_native_rebuildable_reduced_next_probe",
        "ensemble_size": trajectory_count,
        "validation_output_mode": validation_output_mode,
        "expected_output_file_count": None,
        "expected_output_bytes": None,
        "expected_artifact_families": [
            "diagnostics_json",
            "manifest_json",
            "trajectory_csv",
            "ensemble_deposition_csv",
            "trajectory_metadata_csv",
            "impact_events_csv",
        ],
    }
    return {
        "frontier_status": "measured_existing_artifacts",
        "recommendation_class": "defer_small_bounded_ensemble",
        "recommendation_reason": (
            "bounded feasibility metadata is complete; package generation remains "
            "deferred pending explicit launch authorization"
        ),
        "minimum_useful_ensemble_recommendation": recommendation,
    }


def _build_submission_package_markdown(package: dict[str, Any]) -> str:
    lines = [
        "# Balfrin Submission Package",
        "",
        f"- Schema: `{package['schema_version']}`",
        f"- Mode: `{package['package_mode']}`",
        f"- Launch status: `{package['execution_status']}`",
        f"- Probe manifest: `{package['probe_manifest']}`",
        f"- Expected run root: `{package['expected_run_root']}`",
        f"- Run root: `{package['run_root']}`",
        f"- Run id: `{package['run_id']}`",
        "",
        "## SLURM",
        "",
        f"- Partition: `{package['slurm']['partition']}`",
        f"- Time: `{package['slurm']['time']}`",
        f"- Nodes: `{package['slurm']['nodes']}`",
        f"- Ntasks: `{package['slurm']['ntasks']}`",
        f"- Cpus per task: `{package['slurm']['cpus_per_task']}`",
        "",
        "## Repository",
        "",
        f"- Repo root: `{package['repository']['repo_root']}`",
        f"- Branch: `{package['repository']['branch']}`",
        f"- Commit: `{package['repository']['commit']}`",
        "",
        "## Input Checks",
        "",
        f"- Status: `{package['input_checks']['status']}`",
        f"- Blocking checks: `{len(package['input_checks']['blocking_checks'])}`",
        "",
        "## Recommendation",
        "",
        f"- Frontier status: `{package['recommended_next_probe']['frontier_status']}`",
        f"- Recommendation class: `{package['recommended_next_probe']['recommendation_class']}`",
        f"- Recommendation reason: {package['recommended_next_probe']['recommendation_reason']}",
        f"- Probe id: `{package['recommended_next_probe']['minimum_useful_ensemble_recommendation'].get('probe_id')}`",
        f"- Ensemble size: `{package['recommended_next_probe']['minimum_useful_ensemble_recommendation'].get('ensemble_size')}`",
        f"- Validation output mode: `{package['recommended_next_probe']['minimum_useful_ensemble_recommendation'].get('validation_output_mode')}`",
        "",
        "## Reduced Output Settings",
        "",
    ]
    if package["reduced_output_settings"]:
        for key, value in sorted(package["reduced_output_settings"].items()):
            lines.append(f"- {key}: `{value}`")
    else:
        lines.append("- No reduced-output settings were resolved from the command plan.")
    lines.extend(
        [
            "",
            "## Launch Boundary",
            "",
            f"- Metrics collection command: `{package['metrics_collection_command']}`",
            "- Stop / resume notes:",
        ]
    )
    for note in package["stop_resume_notes"]:
        lines.append(f"  - {note}")
    lines.extend(
        [
            "",
            "## Output Roots",
            "",
            "- Generated roots:",
        ]
    )
    for root in package["generated_output_roots"]:
        lines.append(f"  - `{root}`")
    lines.append("- Ignored roots:")
    for root in package["ignored_output_roots"]:
        lines.append(f"  - `{root}`")
    lines.extend(
        [
            "",
            "## Operator Sequence",
            "",
        ]
    )
    for step_name, commands in package["operator_sequence"].items():
        lines.append(f"- {step_name}:")
        for command in commands:
            lines.append("```bash")
            lines.append(command)
            lines.append("```")
    lines.extend(
        [
            "",
            "## Expected Outputs",
            "",
        ]
    )
    for output in package["expected_outputs"]:
        lines.append(f"- `{output}`")
    lines.extend(
        [
            "",
            "## Collection Instructions",
            "",
        ]
    )
    for instruction in package["collection_instructions"]:
        lines.append(f"```bash\n{instruction}\n```")
    lines.extend(
        [
            "",
            "## Do Not Commit",
            "",
            "Do not commit any generated Balfrin probe outputs or scratch-run artifacts from the paths listed below.",
        ]
    )
    for root in package["ignored_output_roots"]:
        lines.append(f"- `{root}`")
    for artifact in package["ignored_artifacts"]:
        lines.append(f"- `{artifact}`")
    return "\n".join(lines)


def _build_scheduler_submission_report(
    *,
    run_root: Path,
    run_id: str,
    probe_manifest: Path,
    command_plan_path: Path,
    sbatch_path: Path,
    partition: str,
    time_budget: str,
    nodes: int,
    ntasks: int,
    cpus_per_task: int,
    submit_command: list[str],
    stdout: str = "",
    stderr: str = "",
    returncode: int | None = None,
    error: BaseException | None = None,
) -> dict[str, Any]:
    error_type = type(error).__name__ if error is not None else None
    error_message = str(error).strip() if error is not None else ""
    report: dict[str, Any] = {
        "schema_version": SUBMISSION_REPORT_SCHEMA_VERSION,
        "status": "scheduler_submission_failed",
        "submission_status": "scheduler_submission_failed",
        "failure_class": "scheduler_submission_failed",
        "probe_manifest": str(probe_manifest.resolve()),
        "run_root": str(run_root.resolve()),
        "run_id": run_id,
        "command_plan_path": str(command_plan_path.resolve()),
        "sbatch_script_path": str(sbatch_path.resolve()),
        "submit_command": submit_command,
        "slurm": {
            "partition": partition,
            "time": time_budget,
            "nodes": nodes,
            "ntasks": ntasks,
            "cpus_per_task": cpus_per_task,
        },
        "submitted_job_id": None,
        "stdout": stdout.strip(),
        "stderr": stderr.strip(),
        "returncode": returncode,
        "error": {
            "type": error_type,
            "message": error_message,
        },
        "recovery_action": (
            "regenerate the same submission package and retry submit from the Balfrin SSH entry point with the same run root and run id"
        ),
        "escalation_boundary": (
            "scheduler failures are operational; they should not be reclassified as scientific outcomes"
        ),
        "source_helper": "scripts/submit_balfrin_probe.py",
        "escalate_to": "scheduler or operator support",
        "claim_boundaries": {
            "operational_claims_allowed": False,
            "physical_probability_claims_allowed": False,
            "annual_frequency_claims_allowed": False,
            "risk_exposure_vulnerability_claims_allowed": False,
            "scale_up_authorized": False,
            "distributed_execution_authorized": False,
        },
    }
    if error_message:
        report["blocked_reason"] = error_message
    return report


def _build_blocked_authorized_submission_report(
    *,
    run_root: Path,
    run_id: str,
    probe_manifest: Path,
    command_plan_path: Path,
    sbatch_path: Path,
    partition: str,
    time_budget: str,
    nodes: int,
    ntasks: int,
    cpus_per_task: int,
    reviewed_handoff_package: Path | None,
    authorization_record: Path | None,
    package_report: dict[str, Any],
    authorization_report: dict[str, Any],
) -> dict[str, Any]:
    blocked_reason = authorization_report.get("blocked_reason") or "live execution is missing the reviewed handoff package or authorization record"
    report: dict[str, Any] = {
        "schema_version": AUTHORIZED_SUBMISSION_REPORT_SCHEMA_VERSION,
        "status": authorization_report.get("status", "blocked_missing_authorization"),
        "submission_status": authorization_report.get("status", "blocked_missing_authorization"),
        "failure_class": authorization_report.get("status", "blocked_missing_authorization"),
        "probe_manifest": str(probe_manifest.resolve()),
        "run_root": str(run_root.resolve()),
        "run_id": run_id,
        "command_plan_path": str(command_plan_path.resolve()),
        "sbatch_script_path": str(sbatch_path.resolve()),
        "submit_command": [
            "sbatch",
            "--parsable",
            str(sbatch_path),
        ],
        "slurm": {
            "partition": partition,
            "time": time_budget,
            "nodes": nodes,
            "ntasks": ntasks,
            "cpus_per_task": cpus_per_task,
        },
        "reviewed_handoff_package_path": str(reviewed_handoff_package) if reviewed_handoff_package else None,
        "authorization_record_path": str(authorization_record) if authorization_record else None,
        "reviewed_handoff_package_status": authorization_report.get("reviewed_handoff_package_status"),
        "authorization_record_status": authorization_report.get("authorization_record_status"),
        "reviewed_handoff_package_sha256": authorization_report.get("reviewed_handoff_package_sha256"),
        "authorization_record_sha256": authorization_report.get("authorization_record_sha256"),
        "authorization_status": authorization_report.get("authorization_status", "blocked_missing_authorization"),
        "blocked_reason": blocked_reason,
        "remediation": authorization_report.get(
            "remediation",
            "Provide the reviewed handoff package JSON and live-run authorization record before calling --authorized-submit again.",
        ),
        "package_report": package_report,
        "authorization_report": authorization_report,
        "claim_boundaries": {
            "operational_claims_allowed": False,
            "physical_probability_claims_allowed": False,
            "annual_frequency_claims_allowed": False,
            "risk_exposure_vulnerability_claims_allowed": False,
            "scale_up_authorized": False,
            "distributed_execution_authorized": False,
        },
    }
    return report


def _validate_authorized_submission(
    *,
    reviewed_handoff_package: Path,
    authorization_record: Path,
    run_root: Path,
) -> dict[str, Any]:
    package_status = _structured_document_status(reviewed_handoff_package, label="reviewed handoff package")
    authorization_status = _structured_document_status(authorization_record, label="live-run authorization record")

    if package_status["status"] == "missing" or authorization_status["status"] == "missing":
        return {
            "status": "blocked_missing_authorization",
            "authorization_status": "blocked_missing_authorization",
            "reviewed_handoff_package_status": package_status["status"],
            "authorization_record_status": authorization_status["status"],
            "reviewed_handoff_package_sha256": package_status["sha256"],
            "authorization_record_sha256": authorization_status["sha256"],
            "blocked_reason": "live execution requires both a reviewed handoff package and a live-run authorization record",
            "remediation": "Provide both files before retrying the live multi-zone submit.",
        }

    package = dict(package_status["value"] or {})
    record = dict(authorization_status["value"] or {})

    package_sha256 = package_status["sha256"]
    record_sha256 = authorization_status["sha256"]
    package_digest = package.get("package_sha256")
    record_package_path = record.get("reviewed_handoff_package_path")
    record_package_sha256 = record.get("reviewed_handoff_package_sha256")
    authorization_value = str(record.get("authorization_status") or "").strip()
    authorized_task = str(record.get("authorized_task") or "").strip()

    missing_inputs: list[str] = []
    if str(package.get("package_status") or "") == "blocked_missing_inputs":
        missing_inputs.append("reviewed handoff package is blocked_missing_inputs")
    if not package.get("live_execution_requires_new_human_authorization", False):
        missing_inputs.append("reviewed handoff package does not record live execution authorization requirements")
    if authorized_task not in {
        "TB-211",
        "TB-211: Authorization-Gated Multi-Zone Balfrin Execution",
        "TB-226",
        "TB-226: Smallest Multi-Zone Probe Authorization Preflight",
    }:
        missing_inputs.append("authorization record does not target TB-211 or TB-226")
    if authorization_value != "authorized_for_one_bounded_probe":
        missing_inputs.append(
            f"authorization_status must be authorized_for_one_bounded_probe, got {authorization_value or 'missing'}"
        )
    if record_package_path and Path(str(record_package_path)).resolve() != reviewed_handoff_package.resolve():
        missing_inputs.append("authorization record does not reference the reviewed handoff package path")
    if record_package_sha256 and str(record_package_sha256) != str(package_sha256):
        missing_inputs.append("authorization record reviewed-handoff checksum does not match")
    if package_digest and str(package_digest) != str(package_sha256):
        missing_inputs.append("reviewed handoff package checksum does not match the file contents")
    if record.get("no_rerun_without_renewed_authorization") is not True:
        missing_inputs.append("authorization record does not prohibit rerun without renewed authorization")

    if missing_inputs:
        return {
            "status": "blocked_missing_inputs",
            "authorization_status": "blocked_missing_inputs",
            "reviewed_handoff_package_status": "reviewed",
            "authorization_record_status": "reviewed",
            "reviewed_handoff_package_sha256": package_sha256,
            "authorization_record_sha256": record_sha256,
            "blocked_reason": "; ".join(missing_inputs),
            "remediation": "Correct the reviewed handoff package and authorization record before retrying.",
        }

    return {
        "status": "authorized",
        "authorization_status": "authorized",
        "reviewed_handoff_package_status": "reviewed",
        "authorization_record_status": "reviewed",
        "reviewed_handoff_package_sha256": package_sha256,
        "authorization_record_sha256": record_sha256,
        "blocked_reason": "",
        "remediation": "",
        "authorization_record_path": str(authorization_record.resolve()),
        "reviewed_handoff_package_path": str(reviewed_handoff_package.resolve()),
        "authorization_record": record,
        "reviewed_handoff_package": package,
    }


def _write_submission_report(run_root: Path, report: dict[str, Any]) -> Path:
    report_path = run_root / f"{SUBMISSION_REPORT_BASENAME}.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report_path


def _resolve_run_id(args: argparse.Namespace, manifest_run_id: str, *, is_dry_run: bool) -> str:
    if args.run_id:
        return _safe_fragment(args.run_id)
    if is_dry_run:
        return manifest_run_id
    return _timestamp_run_id()


def _build_python_executor() -> str:
    return """
import json
import os
import subprocess
import time
from pathlib import Path

run_root = Path(os.environ["RUN_ROOT"])
quote_chars = chr(34) + chr(39)
repo_root = Path(str(os.environ.get("REPO_ROOT", "")).strip().strip(quote_chars))
command_plan_path = Path(os.environ["COMMAND_PLAN_PATH"])

plan = json.loads(command_plan_path.read_text(encoding="utf-8"))
commands = plan.get("commands", [])

full_start = time.perf_counter()
hazard_start = None
hazard_end = None

for entry in commands:
    if not isinstance(entry, dict):
        continue
    command = entry.get("command")
    if not isinstance(command, list):
        raise SystemExit("command-plan entry is malformed")

    args = [str(token) for token in command]
    name = str(entry.get("name", ""))
    cwd = str(entry.get("cwd", str(repo_root))).strip().strip(quote_chars)
    env = os.environ.copy()
    for key, value in (entry.get("env") or {}).items():
        env[str(key)] = str(value)

    if name == "build_conditional_hazard_layers":
        hazard_start = time.perf_counter()

    completed = subprocess.run(args, cwd=cwd, env=env, check=False)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)

    if name == "build_conditional_hazard_layers":
        hazard_end = time.perf_counter()

full_end = time.perf_counter()
full_seconds = full_end - full_start
(run_root / "balfrin_probe_full_time.txt").write_text(f"{full_seconds}\\n", encoding="utf-8")
if hazard_start is None or hazard_end is None:
    (run_root / "balfrin_hazard_stage_time.txt").write_text("0\\n", encoding="utf-8")
else:
    (run_root / "balfrin_hazard_stage_time.txt").write_text(
        f"{hazard_end - hazard_start}\\n",
        encoding="utf-8",
    )
"""


def _build_sbatch_script(
    *,
    run_root: Path,
    probe_manifest: Path,
    partition: str,
    time_budget: str,
    nodes: int,
    ntasks: int,
    cpus_per_task: int,
) -> str:
    if partition not in VALID_PARTITIONS:
        raise ValueError(f"unsupported SLURM partition: {partition}")

    run_root = run_root.resolve()
    log_root = (run_root / "logs").resolve()
    probe_manifest = probe_manifest.resolve()

    script_lines = [
        "#!/usr/bin/env bash",
        "#SBATCH --job-name=balfrin-probe",
        f"#SBATCH --partition={shlex.quote(partition)}",
        f"#SBATCH --time={shlex.quote(time_budget)}",
        f"#SBATCH --nodes={nodes}",
        f"#SBATCH --ntasks={ntasks}",
        f"#SBATCH --cpus-per-task={cpus_per_task}",
        f"#SBATCH --output={shlex.quote((log_root / 'slurm-%j.out').as_posix())}",
        f"#SBATCH --error={shlex.quote((log_root / 'slurm-%j.err').as_posix())}",
        "",
        "set -euo pipefail",
        "",
        f"RUN_ROOT={run_root.as_posix()}",
        f"REPO_ROOT={ROOT.as_posix()}",
        f"PROBE_MANIFEST={probe_manifest.as_posix()}",
        'COMMAND_PLAN_PATH="${RUN_ROOT}/command_plan.json"',
        'SUMMARY_PATH="${RUN_ROOT}/balfrin_probe_summary.json"',
        'FULL_TIME_PATH="${RUN_ROOT}/balfrin_probe_full_time.txt"',
        'HAZARD_TIME_PATH="${RUN_ROOT}/balfrin_hazard_stage_time.txt"',
        'RUN_CONTEXT_PATH="${RUN_ROOT}/balfrin_probe_context.txt"',
        "",
        "mkdir -p \"${RUN_ROOT}/logs\"",
        'export SCRATCH="${SCRATCH:-/scratch}"',
        'export UV_CACHE_DIR="${UV_CACHE_DIR:-$SCRATCH/.cache/uv}"',
        'export CARGO_TARGET_DIR="${CARGO_TARGET_DIR:-$SCRATCH/rust_rockfall/target}"',
        'export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK:-1}"',
        'export UV_CACHE_DIR',
        'export CARGO_TARGET_DIR',
        'export RUN_ROOT',
        'export REPO_ROOT',
        'export PROBE_MANIFEST',
        'export COMMAND_PLAN_PATH',
        'export SUMMARY_PATH',
        'export FULL_TIME_PATH',
        'export HAZARD_TIME_PATH',
        'export RUN_CONTEXT_PATH',
        "",
        '{',
        '  echo "hostname=$(hostname)"',
        "  echo \"date=$(date -u +'%Y-%m-%dT%H:%M:%SZ')\"",
        '  echo "SLURM_JOB_ID=${SLURM_JOB_ID:-local}"',
        '  echo "SLURM_JOB_NAME=${SLURM_JOB_NAME:-balfrin-probe}"',
        '  echo "SLURM_CPUS_PER_TASK=${SLURM_CPUS_PER_TASK:-1}"',
        '  echo "run_root=${RUN_ROOT}"',
        '  echo "probe_manifest=${PROBE_MANIFEST}"',
        '  echo "command_plan_path=${COMMAND_PLAN_PATH}"',
        '  echo "repo_root=${REPO_ROOT}"',
        '  if command -v git >/dev/null 2>&1; then',
        '    git_hash="$(git -C "$REPO_ROOT" rev-parse HEAD)"',
        '    echo "git_hash=${git_hash}"',
        '  else',
        '    echo "git_hash=unknown"',
        '  fi',
        '} > "${RUN_CONTEXT_PATH}"',
        "",
        "cd \"${REPO_ROOT}\"",
        f'UV_CACHE_DIR="$UV_CACHE_DIR" python3 "${{REPO_ROOT}}/scripts/validate_public_real_site_conditional_pilot_run.py" "${{PROBE_MANIFEST}}" --print-command-plan --format json > "${{COMMAND_PLAN_PATH}}"',
        "",
        "python3 - <<'PY'",
        _build_python_executor().strip("\n"),
        "PY",
        "",
        f'python3 "${{REPO_ROOT}}/scripts/collect_balfrin_probe_metrics.py" --run-root "${{RUN_ROOT}}" --probe-manifest "${{PROBE_MANIFEST}}" --output-json "${{SUMMARY_PATH}}"',
        'echo "summary_path=${SUMMARY_PATH}"',
        'echo "full_time_path=${FULL_TIME_PATH}"',
        'echo "hazard_time_path=${HAZARD_TIME_PATH}"',
        "",
    ]
    return "\n".join(script_lines)


def _write_outputs(
    run_root: Path,
    probe_manifest: Path,
    command_plan: dict[str, Any],
    partition: str,
    time_budget: str,
    nodes: int,
    ntasks: int,
    cpus_per_task: int,
) -> tuple[Path, Path]:
    run_root.mkdir(parents=True, exist_ok=True)
    (run_root / "logs").mkdir(parents=True, exist_ok=True)

    sbatch_path = run_root / "probe.sbatch"
    sbatch_text = _build_sbatch_script(
        run_root=run_root,
        probe_manifest=probe_manifest,
        partition=partition,
        time_budget=time_budget,
        nodes=nodes,
        ntasks=ntasks,
        cpus_per_task=cpus_per_task,
    )
    sbatch_path.write_text(sbatch_text + "\n", encoding="utf-8")
    sbatch_path.chmod(0o750)

    command_plan_path = run_root / "command_plan.json"
    command_plan_path.write_text(json.dumps(command_plan, indent=2), encoding="utf-8")
    package = _build_submission_package_report(
        run_root=run_root,
        probe_manifest=probe_manifest,
        command_plan=command_plan,
        partition=partition,
        time_budget=time_budget,
        nodes=nodes,
        ntasks=ntasks,
        cpus_per_task=cpus_per_task,
    )
    package_path = run_root / f"{PACKAGE_BASENAME}.json"
    package_path.write_text(json.dumps(package, indent=2), encoding="utf-8")
    package_md_path = run_root / f"{PACKAGE_BASENAME}.md"
    package_md_path.write_text(_build_submission_package_markdown(package) + "\n", encoding="utf-8")
    return command_plan_path, sbatch_path


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if args.collect:
        collector = _load_collect_script()
        run_root = args.run_root
        assert run_root is not None
        summary = collector.collect_run_metrics(run_root.resolve())
        print(json.dumps(summary, indent=2))
        return 0

    assert args.probe_manifest is not None
    command_plan, manifest_run_id = _read_command_plan(args.probe_manifest)
    probe_id = _safe_fragment(args.probe_id or manifest_run_id)
    run_id = _resolve_run_id(
        args=args,
        manifest_run_id=manifest_run_id,
        is_dry_run=args.dry_run,
    )
    run_root = args.run_root or _default_run_root(probe_id=probe_id, run_id=run_id)
    run_root = run_root.resolve()
    sbatch_path = run_root / "probe.sbatch"

    if args.local_command_plan:
        print(json.dumps(command_plan, indent=2))
        return 0

    if args.dry_run:
        script = _build_sbatch_script(
            run_root=run_root,
            probe_manifest=args.probe_manifest,
            partition=args.partition,
            time_budget=args.time,
            nodes=args.nodes,
            ntasks=args.ntasks,
            cpus_per_task=args.cpus_per_task,
        )
        print(f"run_root={run_root}")
        print(f"command_plan_path={run_root / 'command_plan.json'}")
        print(f"sbatch_script_path={sbatch_path}")
        print(script)
        return 0

    package_report: dict[str, Any] | None = None

    if args.authorized_submit:
        package_report = _build_submission_package_report(
            run_root=run_root,
            probe_manifest=args.probe_manifest,
            command_plan=command_plan,
            partition=args.partition,
            time_budget=args.time,
            nodes=args.nodes,
            ntasks=args.ntasks,
            cpus_per_task=args.cpus_per_task,
        )
        if package_report.get("input_checks", {}).get("status") == "blocked_for_balfrin_readiness" or package_report.get(
            "input_checks", {}
        ).get("status") == "blocked_missing_inputs":
            authorization_report = {
                "status": "blocked_missing_inputs",
                "authorization_status": "blocked_missing_inputs",
                "reviewed_handoff_package_status": "reviewed",
                "authorization_record_status": "reviewed",
                "reviewed_handoff_package_sha256": None,
                "authorization_record_sha256": None,
                "blocked_reason": "required inputs are missing for the selected Balfrin probe",
                "remediation": "Resolve the staged-input blockers before attempting the authorized multi-zone submit.",
            }
            report = _build_blocked_authorized_submission_report(
                run_root=run_root,
                run_id=run_id,
                probe_manifest=args.probe_manifest,
                command_plan_path=run_root / "command_plan.json",
                sbatch_path=sbatch_path,
                partition=args.partition,
                time_budget=args.time,
                nodes=args.nodes,
                ntasks=args.ntasks,
                cpus_per_task=args.cpus_per_task,
                reviewed_handoff_package=args.reviewed_handoff_package,
                authorization_record=args.authorization_record,
                package_report=package_report,
                authorization_report=authorization_report,
            )
            report_path = _write_submission_report(run_root, report)
            print(json.dumps(report, indent=2, sort_keys=True))
            print(f"submission_report_path={report_path}", file=sys.stderr)
            return 2

        preflight_module = _load_authorization_preflight()
        balfrin_access_report, balfrin_access_source = preflight_module._load_access_report(
            args.balfrin_access_preflight_json
        )
        authorization_report = preflight_module.build_report(
            reviewed_handoff_package=args.reviewed_handoff_package,
            authorization_record=args.authorization_record,
            balfrin_access_preflight=balfrin_access_report,
            balfrin_access_preflight_source=balfrin_access_source,
        )
        if authorization_report["preflight_status"] != preflight_module.STATUS_READY:
            report = _build_blocked_authorized_submission_report(
                run_root=run_root,
                run_id=run_id,
                probe_manifest=args.probe_manifest,
                command_plan_path=run_root / "command_plan.json",
                sbatch_path=sbatch_path,
                partition=args.partition,
                time_budget=args.time,
                nodes=args.nodes,
                ntasks=args.ntasks,
                cpus_per_task=args.cpus_per_task,
                reviewed_handoff_package=args.reviewed_handoff_package,
                authorization_record=args.authorization_record,
                package_report=package_report,
                authorization_report=authorization_report,
            )
            report_path = _write_submission_report(run_root, report)
            print(json.dumps(report, indent=2, sort_keys=True))
            print(f"submission_report_path={report_path}", file=sys.stderr)
            return 2

    command_plan_path, sbatch_path = _write_outputs(
        run_root=run_root,
        probe_manifest=args.probe_manifest,
        command_plan=command_plan,
        partition=args.partition,
        time_budget=args.time,
        nodes=args.nodes,
        ntasks=args.ntasks,
        cpus_per_task=args.cpus_per_task,
    )

    submit_command = ["sbatch", "--parsable", str(sbatch_path)]

    if args.generate_only:
        print(f"run_root={run_root}")
        print(f"command_plan_path={command_plan_path}")
        print(f"sbatch_script_path={sbatch_path}")
        return 0

    try:
        submit = subprocess.run(
            submit_command,
            check=False,
            capture_output=True,
            text=True,
            timeout=args.slurm_timeout,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        report = _build_scheduler_submission_report(
            run_root=run_root,
            run_id=run_id,
            probe_manifest=args.probe_manifest,
            command_plan_path=command_plan_path,
            sbatch_path=sbatch_path,
            partition=args.partition,
            time_budget=args.time,
            nodes=args.nodes,
            ntasks=args.ntasks,
            cpus_per_task=args.cpus_per_task,
            submit_command=submit_command,
            error=exc,
        )
        report_path = _write_submission_report(run_root, report)
        print(json.dumps(report, indent=2, sort_keys=True))
        print(f"submission_report_path={report_path}", file=sys.stderr)
        return 2

    if submit.returncode != 0:
        report = _build_scheduler_submission_report(
            run_root=run_root,
            run_id=run_id,
            probe_manifest=args.probe_manifest,
            command_plan_path=command_plan_path,
            sbatch_path=sbatch_path,
            partition=args.partition,
            time_budget=args.time,
            nodes=args.nodes,
            ntasks=args.ntasks,
            cpus_per_task=args.cpus_per_task,
            submit_command=submit_command,
            stdout=submit.stdout,
            stderr=submit.stderr,
            returncode=submit.returncode,
        )
        report_path = _write_submission_report(run_root, report)
        print(json.dumps(report, indent=2, sort_keys=True))
        print(f"submission_report_path={report_path}", file=sys.stderr)
        return 2

    print(f"submitted_job_id={submit.stdout.strip()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
