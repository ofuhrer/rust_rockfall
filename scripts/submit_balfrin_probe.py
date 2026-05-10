#!/usr/bin/env python3
"""Generate and submit SLURM-first balfrin probe runs from tracked probe manifests."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


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
        help="Generate command plan and sbatch script, but do not submit.",
    )
    parser.add_argument(
        "--submit",
        action="store_true",
        help="Generate and submit a SLURM job (implemented, but not exercised in this task).",
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

    args = parser.parse_args(argv)

    modes = (
        args.dry_run,
        args.generate_only,
        args.submit,
        args.collect,
        args.local_command_plan,
    )
    if sum(1 for mode in modes if mode) != 1:
        parser.error(
            "exactly one of --dry-run, --generate-only, --submit, --collect, "
            "--local-command-plan is required"
        )
    if args.collect:
        if args.run_root is None:
            parser.error("--run-root is required with --collect")
        if args.probe_manifest is not None:
            parser.error("--collect does not accept a probe manifest argument")
    elif args.probe_manifest is None:
        parser.error("probe_manifest is required unless --collect is used")

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
repo_root = Path(str(os.environ.get("REPO_ROOT", "")).strip().strip("\"'"))
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
    cwd = str(entry.get("cwd", str(repo_root))).strip().strip("\"'")
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

    if args.generate_only:
        print(f"run_root={run_root}")
        print(f"command_plan_path={command_plan_path}")
        print(f"sbatch_script_path={sbatch_path}")
        return 0

    submit = subprocess.run(
        ["sbatch", "--parsable", str(sbatch_path)],
        check=False,
        capture_output=True,
        text=True,
        timeout=args.slurm_timeout,
    )
    if submit.returncode != 0:
        if submit.stderr:
            print(f"sbatch submission failed: {submit.stderr.strip()}", file=sys.stderr)
        else:
            print("sbatch submission failed", file=sys.stderr)
        if submit.stdout:
            print(submit.stdout.strip(), file=sys.stderr)
        return submit.returncode

    print(f"submitted_job_id={submit.stdout.strip()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
