#!/usr/bin/env python3
"""Read-only SSH and remote-artifact preflight for Balfrin collection work."""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from pathlib import PurePosixPath
from typing import Any, Callable, Sequence


SCHEMA_VERSION = "balfrin_remote_access_preflight_v1"

STATUS_READY = "ready_for_read_only_collection"
STATUS_BLOCKED_SSH = "blocked_ssh_unavailable"
STATUS_BLOCKED_CLONE = "blocked_missing_remote_clone"
STATUS_BLOCKED_RUN_ROOT = "blocked_missing_run_root"
STATUS_BLOCKED_SCHEDULER = "blocked_scheduler_unavailable"

DEFAULT_SSH_TARGET = "balfrin"
DEFAULT_REMOTE_REPO_ROOT = "/users/olifu/work/rust_rockfall"
DEFAULT_RUN_ROOT = (
    "/scratch/mch/olifu/rust_rockfall/probes/"
    "tschamut_public_balfrin_target_area_demo_v1/authorized_tb168_20260517"
)
DEFAULT_SCHEDULER_QUERY_COMMAND = 'command -v squeue >/dev/null && squeue -h -u "$(whoami)" -o "%.18i" >/dev/null'


Runner = Callable[..., subprocess.CompletedProcess[str]]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ssh-target", default=DEFAULT_SSH_TARGET, help="SSH host alias for Balfrin.")
    parser.add_argument(
        "--remote-repo-root",
        default=DEFAULT_REMOTE_REPO_ROOT,
        help="Expected Balfrin git checkout path.",
    )
    parser.add_argument(
        "--run-root",
        default=DEFAULT_RUN_ROOT,
        help="Expected non-git Balfrin run root to inspect for read-only collection.",
    )
    parser.add_argument(
        "--connect-timeout",
        type=int,
        default=10,
        help="SSH ConnectTimeout in seconds.",
    )
    parser.add_argument(
        "--scheduler-query-command",
        default=DEFAULT_SCHEDULER_QUERY_COMMAND,
        help="Read-only scheduler query run after SSH, clone, and run-root checks pass.",
    )
    parser.add_argument("--format", choices=("json", "text"), default="json")
    return parser.parse_args(argv)


def _remote_test_directory(path: str) -> str:
    quoted = shlex.quote(str(PurePosixPath(path)))
    return f"test -d {quoted} && test -r {quoted}"


def _remote_clone_check(path: str) -> str:
    repo_root = str(PurePosixPath(path))
    quoted_root = shlex.quote(repo_root)
    quoted_git = shlex.quote(f"{repo_root}/.git")
    quoted_submit = shlex.quote(f"{repo_root}/scripts/submit_balfrin_probe.py")
    return f"test -d {quoted_root} && test -d {quoted_git} && test -r {quoted_submit}"


def _ssh_base_args(ssh_target: str, connect_timeout: int) -> list[str]:
    return [
        "ssh",
        "-o",
        "BatchMode=yes",
        "-o",
        f"ConnectTimeout={connect_timeout}",
        ssh_target,
    ]


def _trim(value: str | None, limit: int = 600) -> str:
    if value is None:
        return ""
    text = value.strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def _run_remote_check(
    *,
    name: str,
    remote_command: str,
    ssh_target: str,
    connect_timeout: int,
    runner: Runner,
) -> dict[str, Any]:
    command = [*_ssh_base_args(ssh_target, connect_timeout), remote_command]
    try:
        result = runner(command, check=False, capture_output=True, text=True)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {
            "name": name,
            "status": "fail",
            "command": command,
            "remote_command": remote_command,
            "returncode": None,
            "stdout": "",
            "stderr": _trim(str(exc)),
        }
    return {
        "name": name,
        "status": "pass" if result.returncode == 0 else "fail",
        "command": command,
        "remote_command": remote_command,
        "returncode": result.returncode,
        "stdout": _trim(result.stdout),
        "stderr": _trim(result.stderr),
    }


def collect_preflight_report(
    *,
    ssh_target: str = DEFAULT_SSH_TARGET,
    remote_repo_root: str = DEFAULT_REMOTE_REPO_ROOT,
    run_root: str = DEFAULT_RUN_ROOT,
    connect_timeout: int = 10,
    scheduler_query_command: str = DEFAULT_SCHEDULER_QUERY_COMMAND,
    runner: Runner = subprocess.run,
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    ordered_checks: Sequence[tuple[str, str, str]] = (
        ("ssh_availability", "true", STATUS_BLOCKED_SSH),
        ("remote_clone", _remote_clone_check(remote_repo_root), STATUS_BLOCKED_CLONE),
        ("run_root_visibility", _remote_test_directory(run_root), STATUS_BLOCKED_RUN_ROOT),
        ("scheduler_query", scheduler_query_command, STATUS_BLOCKED_SCHEDULER),
    )

    status = STATUS_READY
    for name, remote_command, blocked_status in ordered_checks:
        check = _run_remote_check(
            name=name,
            remote_command=remote_command,
            ssh_target=ssh_target,
            connect_timeout=connect_timeout,
            runner=runner,
        )
        checks.append(check)
        if check["status"] != "pass":
            status = blocked_status
            break

    return {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "ready_for_read_only_collection": status == STATUS_READY,
        "read_only": True,
        "live_submission_authorized": False,
        "ssh_target": ssh_target,
        "remote_repo_root": str(PurePosixPath(remote_repo_root)),
        "run_root": str(PurePosixPath(run_root)),
        "scheduler_query_command": scheduler_query_command,
        "checked_commands": checks,
        "boundary_note": (
            "Read-only SSH preflight only: checks availability, expected checkout, "
            "non-git run-root visibility, and scheduler query reachability; it does not launch jobs or mutate remote state."
        ),
    }


def _format_text(report: dict[str, Any]) -> str:
    lines = [
        f"status={report['status']}",
        f"ssh_target={report['ssh_target']}",
        f"remote_repo_root={report['remote_repo_root']}",
        f"run_root={report['run_root']}",
    ]
    for check in report["checked_commands"]:
        lines.append(f"{check['name']}={check['status']} returncode={check['returncode']}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report = collect_preflight_report(
        ssh_target=args.ssh_target,
        remote_repo_root=args.remote_repo_root,
        run_root=args.run_root,
        connect_timeout=args.connect_timeout,
        scheduler_query_command=args.scheduler_query_command,
    )
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(_format_text(report))
    return 0 if report["status"] == STATUS_READY else 2


if __name__ == "__main__":
    raise SystemExit(main())
