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
STATUS_BLOCKED_DIRTY_CHECKOUT = "blocked_dirty_remote_checkout"
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


def _remote_checkout_hygiene_command(path: str) -> str:
    repo_root = str(PurePosixPath(path))
    quoted_root = shlex.quote(repo_root)
    return "\n".join(
        [
            f"cd {quoted_root}",
            "printf '__REMOTE_HEAD__\\n'",
            "git rev-parse --abbrev-ref HEAD",
            "git rev-parse HEAD",
            "printf '__REMOTE_STATUS__\\n'",
            "git status --porcelain=v1 -uall",
            "printf '__STALE_SUBMISSION_PACKAGES__\\n'",
            (
                "find . -path ./.git -prune -o \\( "
                "-name 'balfrin_submission_package*.json' -o "
                "-name 'balfrin_submission_package*.md' -o "
                "-name 'balfrin_submission_report*.json' -o "
                "-name 'balfrin_submission_report*.md' -o "
                "-name 'command_plan.json' -o "
                "-name 'probe.sbatch' "
                "\\) -type f -print | sort | while IFS= read -r path; do "
                "cleaned=${path#./}; "
                "git ls-files --error-unmatch \"$cleaned\" >/dev/null 2>&1 || printf '%s\\n' \"$cleaned\"; "
                "done"
            ),
            "printf '__STALE_LOGS__\\n'",
            (
                "find . -path ./.git -prune -o \\( "
                "-name 'slurm-*.out' -o "
                "-name 'slurm-*.err' -o "
                "-name '*.log' "
                "\\) -type f -print | sort | while IFS= read -r path; do "
                "cleaned=${path#./}; "
                "git ls-files --error-unmatch \"$cleaned\" >/dev/null 2>&1 || printf '%s\\n' \"$cleaned\"; "
                "done"
            ),
        ]
    )


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


def _quote_path_list(paths: list[str]) -> str:
    return " ".join(shlex.quote(path) for path in paths)


def _status_path(line: str) -> tuple[str, str]:
    status = line[:2]
    path = line[3:].strip() if len(line) > 3 else ""
    if " -> " in path:
        path = path.split(" -> ", 1)[1]
    return status, path


def _is_generated_untracked(path: str) -> bool:
    generated_prefixes = (
        "hazard/results/",
        "validation/private/",
        "validation/results/",
        "verification/results/",
        "target/",
    )
    generated_names = (
        "balfrin_submission_package",
        "balfrin_submission_report",
        "command_plan.json",
        "probe.sbatch",
    )
    return path.startswith(generated_prefixes) or any(name in path for name in generated_names)


def _parse_checkout_hygiene_output(stdout: str, remote_repo_root: str) -> dict[str, Any]:
    sections: dict[str, list[str]] = {
        "__REMOTE_HEAD__": [],
        "__REMOTE_STATUS__": [],
        "__STALE_SUBMISSION_PACKAGES__": [],
        "__STALE_LOGS__": [],
    }
    current: str | None = None
    for raw_line in stdout.splitlines():
        line = raw_line.strip()
        if line in sections:
            current = line
            continue
        if current is not None and line:
            sections[current].append(raw_line if current == "__REMOTE_STATUS__" else line)

    head_lines = sections["__REMOTE_HEAD__"]
    status_lines = sections["__REMOTE_STATUS__"]
    remote_branch = head_lines[0] if head_lines else None
    remote_head = head_lines[1] if len(head_lines) > 1 else None

    tracked_modifications: list[str] = []
    untracked_files: list[str] = []
    untracked_generated_files: list[str] = []
    for line in status_lines:
        status, path = _status_path(line)
        if not path:
            continue
        if status == "??":
            untracked_files.append(path)
            if _is_generated_untracked(path):
                untracked_generated_files.append(path)
        else:
            tracked_modifications.append(f"{status} {path}")
    untracked_other_files = sorted(set(untracked_files) - set(untracked_generated_files))

    stale_submission_packages = sorted(set(sections["__STALE_SUBMISSION_PACKAGES__"]))
    stale_logs = sorted(set(sections["__STALE_LOGS__"]))
    dirty_paths = (
        tracked_modifications
        + untracked_files
        + stale_submission_packages
        + stale_logs
    )
    status = "pass" if not dirty_paths else "fail"

    cleanup_commands: list[str] = [f"git -C {shlex.quote(remote_repo_root)} status --short --untracked-files=all"]
    if tracked_modifications:
        tracked_paths = _quote_path_list([item[3:] for item in tracked_modifications])
        cleanup_commands.extend(
            [
                f"git -C {shlex.quote(remote_repo_root)} diff -- {tracked_paths}",
                f"git -C {shlex.quote(remote_repo_root)} restore -- {tracked_paths}",
            ]
        )
    cleanup_paths = sorted(set(untracked_files + stale_submission_packages + stale_logs))
    if cleanup_paths:
        quoted_paths = _quote_path_list(cleanup_paths)
        cleanup_commands.extend(
            [
                f"tar -C {shlex.quote(remote_repo_root)} -czf /tmp/balfrin_remote_checkout_generated_artifacts_preserve.tgz {quoted_paths}",
                f"git -C {shlex.quote(remote_repo_root)} clean -n -- {quoted_paths}",
                f"git -C {shlex.quote(remote_repo_root)} clean -f -- {quoted_paths}",
            ]
        )

    return {
        "status": status,
        "remote_branch": remote_branch,
        "remote_head": remote_head,
        "tracked_modifications": tracked_modifications,
        "untracked_files": untracked_files,
        "untracked_generated_files": sorted(set(untracked_generated_files)),
        "untracked_other_files": untracked_other_files,
        "stale_submission_packages": stale_submission_packages,
        "stale_logs": stale_logs,
        "dirty_path_count": len(set(dirty_paths)),
        "safe_cleanup_commands": cleanup_commands,
        "summary": (
            "Remote checkout is clean for pre-submit use."
            if status == "pass"
            else "Remote checkout is dirty; preserve or clean the reported files before packaging or submission."
        ),
    }


def _run_remote_check(
    *,
    name: str,
    remote_command: str,
    ssh_target: str,
    connect_timeout: int,
    runner: Runner,
    stdout_limit: int = 600,
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
        "stdout": _trim(result.stdout, limit=stdout_limit),
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
        ("remote_checkout_hygiene", _remote_checkout_hygiene_command(remote_repo_root), STATUS_BLOCKED_DIRTY_CHECKOUT),
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
            stdout_limit=20000 if name == "remote_checkout_hygiene" else 600,
        )
        if name == "remote_checkout_hygiene" and check["returncode"] == 0:
            hygiene = _parse_checkout_hygiene_output(check["stdout"], str(PurePosixPath(remote_repo_root)))
            check["hygiene"] = hygiene
            check["status"] = hygiene["status"]
            check["stdout"] = ""
        checks.append(check)
        if check["status"] != "pass":
            status = blocked_status
            break

    hygiene_report = next(
        (
            dict(check.get("hygiene") or {})
            for check in checks
            if check.get("name") == "remote_checkout_hygiene"
        ),
        {},
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "ready_for_read_only_collection": status == STATUS_READY,
        "ready_for_pre_submit": status == STATUS_READY,
        "read_only": True,
        "live_submission_authorized": False,
        "ssh_target": ssh_target,
        "remote_repo_root": str(PurePosixPath(remote_repo_root)),
        "remote_checkout_hygiene": hygiene_report,
        "remote_head": hygiene_report.get("remote_head"),
        "run_root": str(PurePosixPath(run_root)),
        "scheduler_query_command": scheduler_query_command,
        "checked_commands": checks,
        "boundary_note": (
            "Read-only SSH preflight only: checks availability, expected checkout, "
            "remote checkout hygiene, non-git run-root visibility, and scheduler query reachability; "
            "it does not launch jobs or mutate remote state."
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
    hygiene = report.get("remote_checkout_hygiene") or {}
    if hygiene:
        lines.append(f"remote_head={hygiene.get('remote_head')}")
        lines.append(f"remote_checkout_dirty_path_count={hygiene.get('dirty_path_count')}")
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
