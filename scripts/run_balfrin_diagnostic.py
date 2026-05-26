#!/usr/bin/env python3
"""One-command Balfrin diagnostic runner.

This is the user-facing path for bounded postproc diagnostics:

plan -> prepare -> submit -> monitor -> collect

It deliberately writes one run record under the run root instead of creating a
separate handoff package, authorization record, and preflight artifact.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

SCHEMA_VERSION = "balfrin_diagnostic_run_record_v1"
DEFAULT_REPO_ROOT = Path("/users/olifu/work/rust_rockfall")
DEFAULT_SCRATCH_ROOT = Path("/scratch/mch/olifu/rust_rockfall")
DEFAULT_PARTITION = "postproc"
DEFAULT_TIME = "00:30:00"
DEFAULT_CPUS_PER_TASK = 16
DEFAULT_OUTPUT_FAMILY_MIX = (
    "trajectory_csv",
    "deposition_csv",
    "impact_events_csv",
    "trajectory_merge_state",
    "reducer_merge_state",
)


def default_scratch_root() -> Path:
    scratch = os.environ.get("SCRATCH")
    if scratch:
        return Path(scratch) / "rust_rockfall"
    return DEFAULT_SCRATCH_ROOT


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("plan", "prepare", "submit", "monitor", "collect", "run"))
    parser.add_argument("--release-zones", type=int, default=16)
    parser.add_argument("--reducer-chunks", type=int, default=2)
    parser.add_argument("--reducer-workers", type=int, default=2)
    parser.add_argument("--manifest-mode", choices=("compact", "full"), default="compact")
    parser.add_argument("--output-family-mix", default=",".join(DEFAULT_OUTPUT_FAMILY_MIX))
    parser.add_argument("--repo-root", type=Path, default=Path(os.environ.get("ROCKFALL_REPO_ROOT", DEFAULT_REPO_ROOT)))
    parser.add_argument("--scratch-root", type=Path, default=default_scratch_root())
    parser.add_argument("--run-root", type=Path)
    parser.add_argument("--run-id")
    parser.add_argument("--partition", default=DEFAULT_PARTITION)
    parser.add_argument("--time", default=DEFAULT_TIME)
    parser.add_argument("--cpus-per-task", type=int, default=DEFAULT_CPUS_PER_TASK)
    parser.add_argument("--poll-seconds", type=float, default=30.0)
    parser.add_argument("--monitor-timeout-seconds", type=float, default=0.0)
    parser.add_argument("--slurm-timeout-seconds", type=float, default=60.0)
    parser.add_argument("--format", choices=("json", "text"), default="json")
    return parser.parse_args(argv)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def default_run_id(release_zones: int) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_utc")
    return f"diagnostic_{release_zones}_zone_{stamp}"


def resolve_run_root(args: argparse.Namespace) -> Path:
    if args.run_root is not None:
        return args.run_root.expanduser().resolve()
    run_id = args.run_id or default_run_id(args.release_zones)
    return (args.scratch_root / "diagnostics" / run_id).expanduser().resolve()


def validate_run_shape(args: argparse.Namespace, run_root: Path) -> None:
    if args.release_zones < 1:
        raise ValueError("--release-zones must be positive")
    if args.reducer_chunks < 1:
        raise ValueError("--reducer-chunks must be positive")
    if args.reducer_workers < 1:
        raise ValueError("--reducer-workers must be positive")
    if args.partition != "postproc":
        raise ValueError("this simplified runner is intentionally limited to the postproc partition")
    scratch_root = args.scratch_root.expanduser().resolve()
    try:
        run_root.relative_to(scratch_root)
    except ValueError as exc:
        raise ValueError(f"--run-root must stay under scratch root {scratch_root}") from exc


def diagnostic_paths(run_root: Path) -> dict[str, Path]:
    return {
        "run_record": run_root / "run_record.json",
        "sbatch": run_root / "diagnostic.sbatch",
        "stdout": run_root / "logs" / "diagnostic.stdout",
        "stderr": run_root / "logs" / "diagnostic.stderr",
        "time": run_root / "time_verbose.txt",
        "pressure_root": run_root / "pressure_root",
        "pressure_json": run_root / "multi_zone_reducer_pressure.json",
        "pressure_md": run_root / "multi_zone_reducer_pressure.md",
        "sacct": run_root / "slurm_accounting.psv",
    }


def public_command_sequence(args: argparse.Namespace, run_root: Path) -> list[dict[str, Any]]:
    base = [
        "PYENV_VERSION=system",
        "uv",
        "run",
        "python",
        "scripts/run_balfrin_diagnostic.py",
    ]
    shared = [
        "--release-zones",
        str(args.release_zones),
        "--reducer-chunks",
        str(args.reducer_chunks),
        "--reducer-workers",
        str(args.reducer_workers),
        "--manifest-mode",
        args.manifest_mode,
        "--run-root",
        str(run_root),
        "--partition",
        args.partition,
        "--time",
        args.time,
    ]
    return [
        {
            "name": "plan",
            "purpose": "Inspect the exact run root, generated files, and SLURM shape without writing artifacts.",
            "command": [*base, "plan", *shared, "--format", "json"],
        },
        {
            "name": "run",
            "purpose": "Prepare, submit, monitor, and collect one bounded postproc diagnostic into one run record.",
            "command": [*base, "run", *shared, "--format", "text"],
        },
    ]


def required_materialized_files(run_root: Path) -> list[dict[str, str]]:
    paths = diagnostic_paths(run_root)
    return [
        {
            "path": str(paths["run_record"]),
            "created_by": "prepare",
            "purpose": "Single source of run shape, scheduler state, collection metrics, paths, and claim boundary.",
        },
        {
            "path": str(paths["sbatch"]),
            "created_by": "prepare",
            "purpose": "Submitted SLURM script for the bounded reducer-pressure diagnostic.",
        },
        {
            "path": str(paths["stdout"]),
            "created_by": "slurm",
            "purpose": "Scheduler stdout for the diagnostic job.",
        },
        {
            "path": str(paths["stderr"]),
            "created_by": "slurm",
            "purpose": "Scheduler stderr for the diagnostic job.",
        },
        {
            "path": str(paths["time"]),
            "created_by": "slurm",
            "purpose": "Measured wall time and memory from /usr/bin/time -v.",
        },
        {
            "path": str(paths["pressure_json"]),
            "created_by": "diagnostic_command",
            "purpose": "Machine-readable reducer/output pressure report promoted into run_record.json.",
        },
        {
            "path": str(paths["pressure_md"]),
            "created_by": "diagnostic_command",
            "purpose": "Human-readable reducer/output pressure report.",
        },
        {
            "path": str(paths["sacct"]),
            "created_by": "monitor",
            "purpose": "Captured scheduler accounting used to classify terminal job state.",
        },
    ]


def pressure_command(args: argparse.Namespace, run_root: Path) -> list[str]:
    paths = diagnostic_paths(run_root)
    return [
        "env",
        "PYENV_VERSION=system",
        "uv",
        "run",
        "python",
        "scripts/summarize_multi_zone_reducer_pressure.py",
        "--materialize-root",
        str(paths["pressure_root"]),
        "--release-zone-count",
        str(args.release_zones),
        "--reducer-workers",
        str(args.reducer_workers),
        "--reducer-chunk-count",
        str(args.reducer_chunks),
        "--output-family-mix",
        args.output_family_mix,
        "--manifest-mode",
        args.manifest_mode,
        "--format",
        "json",
        "--json-output",
        str(paths["pressure_json"]),
        "--markdown-output",
        str(paths["pressure_md"]),
    ]


def build_sbatch_script(args: argparse.Namespace, run_root: Path) -> str:
    paths = diagnostic_paths(run_root)
    command = " ".join(shlex.quote(token) for token in pressure_command(args, run_root))
    return "\n".join(
        [
            "#!/bin/bash",
            f"#SBATCH --job-name=rr-diag-{args.release_zones}z",
            f"#SBATCH --partition={args.partition}",
            f"#SBATCH --time={args.time}",
            "#SBATCH --nodes=1",
            "#SBATCH --ntasks=1",
            f"#SBATCH --cpus-per-task={args.cpus_per_task}",
            f"#SBATCH --output={paths['stdout']}",
            f"#SBATCH --error={paths['stderr']}",
            "",
            "set -euo pipefail",
            f"cd {shlex.quote(str(args.repo_root.expanduser().resolve()))}",
            f"mkdir -p {shlex.quote(str(paths['stdout'].parent))}",
            f"/usr/bin/time -v -o {shlex.quote(str(paths['time']))} {command}",
        ]
    )


def git_head(repo_root: Path) -> str | None:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def base_record(args: argparse.Namespace, run_root: Path) -> dict[str, Any]:
    paths = diagnostic_paths(run_root)
    run_id = args.run_id or run_root.name
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "prepared",
        "created_at": utc_now(),
        "updated_at": utc_now(),
        "run_id": run_id,
        "run_root": str(run_root),
        "repo_root": str(args.repo_root.expanduser().resolve()),
        "git_head": git_head(args.repo_root.expanduser().resolve()),
        "partition": args.partition,
        "time_limit": args.time,
        "nodes": 1,
        "ntasks": 1,
        "cpus_per_task": args.cpus_per_task,
        "diagnostic_shape": {
            "release_zone_count": args.release_zones,
            "reducer_chunk_count": args.reducer_chunks,
            "reducer_worker_count": args.reducer_workers,
            "manifest_mode": args.manifest_mode,
            "output_family_mix": [item for item in args.output_family_mix.split(",") if item],
        },
        "paths": {key: str(value) for key, value in paths.items()},
        "command": pressure_command(args, run_root),
        "sbatch_command": ["sbatch", "--parsable", str(paths["sbatch"])],
        "public_interface": {
            "primary_script": "scripts/run_balfrin_diagnostic.py",
            "primary_actions": ["plan", "run"],
            "command_sequence": public_command_sequence(args, run_root),
            "required_materialized_files": required_materialized_files(run_root),
            "legacy_helper_policy": (
                "generate_balfrin_multi_release_zone_demo_handoff.py, "
                "preflight_balfrin_smallest_multi_zone_probe_authorization.py, "
                "submit_balfrin_probe.py, and collect_balfrin_probe_metrics.py remain compatibility and "
                "forensic helpers; routine diagnostic runs should use this runner."
            ),
        },
        "guardrails": {
            "standing_postproc_clearance": True,
            "partition_scope": "postproc_only",
            "scratch_root_required": str(args.scratch_root.expanduser().resolve()),
            "claim_boundary": "diagnostic measurement only; not operational or physical probability evidence",
        },
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_record(run_root: Path) -> dict[str, Any]:
    path = diagnostic_paths(run_root)["run_record"]
    return json.loads(path.read_text(encoding="utf-8"))


def write_record(run_root: Path, record: dict[str, Any]) -> None:
    record["updated_at"] = utc_now()
    write_json(diagnostic_paths(run_root)["run_record"], record)


def prepare(args: argparse.Namespace, run_root: Path) -> dict[str, Any]:
    validate_run_shape(args, run_root)
    paths = diagnostic_paths(run_root)
    run_root.mkdir(parents=True, exist_ok=True)
    paths["stdout"].parent.mkdir(parents=True, exist_ok=True)
    paths["sbatch"].write_text(build_sbatch_script(args, run_root) + "\n", encoding="utf-8")
    paths["sbatch"].chmod(0o750)
    record = base_record(args, run_root)
    write_record(run_root, record)
    return record


def submit(args: argparse.Namespace, run_root: Path) -> dict[str, Any]:
    record = prepare(args, run_root)
    result = subprocess.run(
        record["sbatch_command"],
        check=False,
        capture_output=True,
        text=True,
        timeout=args.slurm_timeout_seconds,
    )
    record["submit"] = {
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }
    if result.returncode == 0:
        record["status"] = "submitted"
        record["job_id"] = parse_job_id(result.stdout)
    else:
        record["status"] = "blocked_scheduler_submit"
    write_record(run_root, record)
    return record


def parse_job_id(stdout: str) -> str | None:
    text = stdout.strip()
    if not text:
        return None
    return text.split(";", 1)[0].strip()


def squeue_state(job_id: str) -> str | None:
    result = subprocess.run(
        ["squeue", "-h", "-j", job_id, "-o", "%T"],
        check=False,
        capture_output=True,
        text=True,
    )
    state = result.stdout.strip().splitlines()
    return state[0] if result.returncode == 0 and state else None


def sacct_report(job_id: str) -> dict[str, Any]:
    fields = "JobID,JobName,Partition,State,ExitCode,Elapsed,MaxRSS,ReqCPUS,AllocCPUS"
    result = subprocess.run(
        ["sacct", "-P", "-j", job_id, "--format", fields],
        check=False,
        capture_output=True,
        text=True,
    )
    return {
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
        "records": parse_sacct(result.stdout) if result.returncode == 0 else [],
    }


def parse_sacct(stdout: str) -> list[dict[str, str]]:
    lines = [line for line in stdout.splitlines() if line.strip()]
    if not lines:
        return []
    header = lines[0].split("|")
    records: list[dict[str, str]] = []
    for line in lines[1:]:
        values = line.split("|")
        records.append({header[index]: values[index] if index < len(values) else "" for index in range(len(header))})
    return records


def terminal_sacct_state(records: list[dict[str, str]]) -> str | None:
    batch = [record for record in records if record.get("JobID", "").endswith(".batch")]
    candidates = batch or records
    for record in candidates:
        state = record.get("State")
        if state:
            return state
    return None


def monitor(args: argparse.Namespace, run_root: Path) -> dict[str, Any]:
    record = read_record(run_root)
    job_id = str(record.get("job_id") or "")
    if not job_id:
        record["status"] = "blocked_missing_job_id"
        write_record(run_root, record)
        return record
    started = time.monotonic()
    queue_state = squeue_state(job_id)
    while queue_state is not None:
        record["status"] = "running_or_queued"
        record["queue_state"] = queue_state
        write_record(run_root, record)
        if args.monitor_timeout_seconds and time.monotonic() - started >= args.monitor_timeout_seconds:
            record["status"] = "monitor_timeout"
            write_record(run_root, record)
            return record
        time.sleep(args.poll_seconds)
        queue_state = squeue_state(job_id)
    accounting = sacct_report(job_id)
    record["sacct"] = accounting
    state = terminal_sacct_state(accounting.get("records", []))
    record["terminal_state"] = state
    record["status"] = "completed" if state == "COMPLETED" else "terminal_non_success"
    write_json(diagnostic_paths(run_root)["sacct"], {"job_id": job_id, **accounting})
    write_record(run_root, record)
    return record


def parse_time_verbose(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"status": "missing"}
    text = path.read_text(encoding="utf-8", errors="replace")
    elapsed = None
    max_rss_kb = None
    for line in text.splitlines():
        if "Elapsed (wall clock) time" in line:
            elapsed = line.split("):", 1)[1].strip() if "):" in line else line.rsplit(":", 1)[1].strip()
        elif "Maximum resident set size" in line:
            match = re.search(r"([0-9]+)", line)
            if match:
                max_rss_kb = int(match.group(1))
    return {
        "status": "measured",
        "elapsed": elapsed,
        "max_rss_kb": max_rss_kb,
        "max_rss_mb": round(max_rss_kb / 1024, 3) if max_rss_kb is not None else None,
    }


def directory_footprint(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"status": "missing", "file_count": 0, "bytes": 0}
    files = [entry for entry in path.rglob("*") if entry.is_file()]
    return {
        "status": "measured",
        "file_count": len(files),
        "bytes": sum(entry.stat().st_size for entry in files),
    }


def collect(args: argparse.Namespace, run_root: Path) -> dict[str, Any]:
    record = read_record(run_root)
    paths = diagnostic_paths(run_root)
    pressure = {}
    if paths["pressure_json"].exists():
        pressure = json.loads(paths["pressure_json"].read_text(encoding="utf-8"))
    record["collection"] = {
        "status": "complete" if pressure else "blocked_missing_pressure_report",
        "time_verbose": parse_time_verbose(paths["time"]),
        "run_root_footprint": directory_footprint(run_root),
        "pressure_root_footprint": directory_footprint(paths["pressure_root"]),
        "pressure_report": {
            "status": pressure.get("probe_status") or pressure.get("status"),
            "release_zone_count": pressure.get("release_zone_count"),
            "scenario_count": pressure.get("scenario_count"),
            "manifest_size_bytes": pressure.get("manifest_size_bytes"),
            "output_file_count": pressure.get("output_file_count"),
            "output_byte_count": pressure.get("output_byte_count"),
            "root_file_count": pressure.get("root_file_count"),
            "reducer_wall_time_seconds": pressure.get("reducer_wall_time_seconds"),
            "recommended_reducer_constraints": pressure.get("recommended_reducer_constraints"),
        },
    }
    if record.get("status") in {"submitted", "running_or_queued"}:
        record["status"] = "collected_without_terminal_scheduler_state"
    write_record(run_root, record)
    return record


def render_text(record: dict[str, Any]) -> str:
    collection = record.get("collection") if isinstance(record.get("collection"), dict) else {}
    pressure = collection.get("pressure_report") if isinstance(collection.get("pressure_report"), dict) else {}
    return "\n".join(
        [
            f"status: {record.get('status')}",
            f"run_root: {record.get('run_root')}",
            f"job_id: {record.get('job_id') or 'none'}",
            f"release_zone_count: {dict(record.get('diagnostic_shape') or {}).get('release_zone_count')}",
            f"pressure_status: {pressure.get('status') or 'not_collected'}",
            f"output_file_count: {pressure.get('output_file_count')}",
            f"output_byte_count: {pressure.get('output_byte_count')}",
            f"max_rss_mb: {dict(collection.get('time_verbose') or {}).get('max_rss_mb')}",
        ]
    )


def emit(record: dict[str, Any], fmt: str) -> None:
    if fmt == "json":
        print(json.dumps(record, indent=2, sort_keys=True))
    else:
        print(render_text(record))


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    run_root = resolve_run_root(args)
    try:
        if args.action == "plan":
            validate_run_shape(args, run_root)
            record = base_record(args, run_root)
            record["status"] = "planned"
        elif args.action == "prepare":
            record = prepare(args, run_root)
        elif args.action == "submit":
            record = submit(args, run_root)
        elif args.action == "monitor":
            record = monitor(args, run_root)
        elif args.action == "collect":
            record = collect(args, run_root)
        else:
            record = submit(args, run_root)
            if record.get("status") == "submitted":
                record = monitor(args, run_root)
                record = collect(args, run_root)
    except (OSError, ValueError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
        print(f"balfrin diagnostic runner error: {exc}", file=sys.stderr)
        return 2
    emit(record, args.format)
    return 0 if record.get("status") not in {"blocked_scheduler_submit", "blocked_missing_job_id"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
