from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Callable, Iterable


ROOT = Path(__file__).resolve().parents[2]
EXPLICIT_INSPECT_FIRST_PREFIXES = (
    "external:",
    "generated scratch:",
    "generated_scratch:",
    "scratch:",
)
WORK_LOG_META_PATHS = {"docs/agent_work_log.md", "docs/task_backlog.md"}


def check_task_backlog_and_work_log_hygiene() -> list[str]:
    errors: list[str] = []
    backlog_path = ROOT / "docs/task_backlog.md"
    work_log_path = ROOT / "docs/agent_work_log.md"
    backlog_text = backlog_path.read_text()
    work_log_text = work_log_path.read_text()

    active_backlog = _section_between(backlog_text, "## Active Tasks", "## Backlog Protocol")
    backlog_entries = _extract_tb_headings(active_backlog)
    work_log_entries = _extract_tb_headings(work_log_text)

    for line_number, line in _tb_heading_lines(backlog_text):
        if not re.match(r"^### TB-\d{3}: [^ ].+", line):
            errors.append(
                f"docs/task_backlog.md:{line_number} task heading must be exactly '### TB-XXX: Short Description'"
            )
        if re.match(r"^### TB-\d{3}\s+\(P\d+\):", line):
            errors.append(f"docs/task_backlog.md:{line_number} must not put priority in the task heading")

    backlog_ids = [task_id for task_id, _title in backlog_entries]
    if backlog_ids != sorted(backlog_ids):
        errors.append("docs/task_backlog.md active TB tasks must be sorted by numeric task id")
    duplicate_backlog_ids = sorted({task_id for task_id in backlog_ids if backlog_ids.count(task_id) > 1})
    if duplicate_backlog_ids:
        errors.append(f"docs/task_backlog.md contains duplicate active TB ids: {duplicate_backlog_ids}")

    required_backlog_terms = (
        "Task headings must always be exactly:",
        "Do not put priority, status, owner, or tags in the heading.",
        "Do not keep completed tasks here.",
        "Append completed TB work to the bottom of `docs/agent_work_log.md`",
        "Inspect first entries must resolve to tracked repository files unless explicitly marked `external:` or `generated scratch:`.",
    )
    for term in required_backlog_terms:
        if term not in backlog_text:
            errors.append(f"docs/task_backlog.md omits backlog hygiene instruction {term!r}")

    work_log_ids = [task_id for task_id, _title in work_log_entries]
    if work_log_ids != sorted(work_log_ids):
        errors.append("docs/agent_work_log.md TB entries must be sorted in ascending order")
    duplicate_work_log_ids = sorted({task_id for task_id in work_log_ids if work_log_ids.count(task_id) > 1})
    if duplicate_work_log_ids:
        errors.append(f"docs/agent_work_log.md contains duplicate TB ids: {duplicate_work_log_ids}")

    overlap = sorted(set(backlog_ids) & set(work_log_ids))
    if overlap:
        errors.append(
            "completed TB entries must not remain active in docs/task_backlog.md: "
            + ", ".join(f"TB-{task_id:03d}" for task_id in overlap)
        )

    required_work_log_terms = (
        "Always append new entries at the bottom of this file.",
        "Use one `### TB-XXX: Short Title` heading per completed task.",
        "Keep the TB entries in ascending order.",
        "## Entry Template",
    )
    for term in required_work_log_terms:
        if term not in work_log_text:
            errors.append(f"docs/agent_work_log.md omits work-log hygiene instruction {term!r}")

    if re.search(r"(?mi)^- Commit:\s*pending\b", work_log_text):
        errors.append("docs/agent_work_log.md contains stale 'Commit: pending' placeholder")
    if re.search(r"(?mi)^- Checks run:\s*pending\b", work_log_text):
        errors.append("docs/agent_work_log.md contains stale 'Checks run: pending' placeholder")
    if re.search(r"(?mi)^- Next task:\s*none\b", work_log_text):
        errors.append("docs/agent_work_log.md should say 'backlog refill needed' instead of 'Next task: none'")

    if _git_repository_is_shallow():
        errors.append(
            "docs/agent_work_log.md work-log reachability checks require full git history; "
            "shallow clone detected"
        )
    else:
        errors.extend(_find_unreachable_work_log_commits(work_log_text))
    errors.extend(_find_work_log_commits_without_task_file_changes(work_log_text))

    for task_id, block in _extract_tb_blocks(work_log_text):
        for field in (
            "Date",
            "Commit",
            "Objective",
            "Files changed",
            "Implementation summary",
            "Checks run",
            "Result/status",
            "Boundaries",
            "Next task",
        ):
            if not re.search(rf"(?m)^- {re.escape(field)}:", block):
                errors.append(f"docs/agent_work_log.md TB-{task_id:03d} omits required field {field!r}")

    return errors


def check_active_backlog_inspect_first_paths() -> list[str]:
    backlog_path = ROOT / "docs/task_backlog.md"
    if not backlog_path.exists():
        return ["docs/task_backlog.md is missing"]
    return find_missing_active_backlog_inspect_first_paths(backlog_path.read_text(), root=ROOT)


def find_missing_active_backlog_inspect_first_paths(backlog_text: str, *, root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    active_text = _section_between(backlog_text, "## Active Tasks", "## Backlog Protocol")
    if not active_text:
        return errors

    for task_id, block in _extract_tb_blocks(active_text):
        for item in _extract_inspect_first_paths(block):
            if _is_explicit_external_or_generated_scratch_path(item):
                continue
            if not (root / item).exists():
                errors.append(f"docs/task_backlog.md TB-{task_id:03d} inspect-first path missing: {item}")
    return errors


def _extract_inspect_first_paths(section: str) -> list[str]:
    match = re.search(r"^Inspect first:\s*$", section, re.MULTILINE)
    if not match:
        return []
    rest = section[match.end() :]
    items: list[str] = []
    for line in rest.splitlines():
        stripped = line.strip()
        if not stripped:
            if items:
                break
            continue
        if not stripped.startswith("- "):
            if items:
                break
            continue
        item = stripped[2:].strip()
        if item.startswith("`") and item.endswith("`"):
            item = item[1:-1]
        items.append(item)
    return items


def _is_explicit_external_or_generated_scratch_path(item: str) -> bool:
    lowered = item.strip().lower()
    return any(lowered.startswith(prefix) for prefix in EXPLICIT_INSPECT_FIRST_PREFIXES)


def _find_unreachable_work_log_commits(
    work_log_text: str,
    is_ancestor: Callable[[str], bool] | None = None,
) -> list[str]:
    checker = is_ancestor or _git_commit_is_ancestor_of_head
    errors: list[str] = []
    for task_id, block in _extract_tb_blocks(work_log_text):
        match = re.search(r"(?mi)^- Commit:\s*`([0-9a-f]{7,40})`", block)
        if not match:
            continue
        commit_hash = match.group(1)
        if not checker(commit_hash):
            errors.append(
                f"docs/agent_work_log.md TB-{task_id:03d} commit {commit_hash} is not reachable from HEAD"
            )
    return errors


def _find_work_log_commits_without_task_file_changes(
    work_log_text: str,
    changed_files_provider: Callable[[str], set[str]] | None = None,
) -> list[str]:
    provider = changed_files_provider or _git_commit_changed_files
    errors: list[str] = []
    for task_id, block in _extract_tb_blocks(work_log_text):
        commit_match = re.search(r"(?mi)^- Commit:\s*`([0-9a-f]{7,40})`", block)
        if not commit_match:
            continue
        expected_files = _extract_work_log_files_changed(block)
        task_files = {path for path in expected_files if path not in WORK_LOG_META_PATHS}
        if not task_files:
            continue
        commit_hash = commit_match.group(1)
        changed_files = provider(commit_hash)
        if changed_files and task_files.isdisjoint(changed_files):
            errors.append(
                f"docs/agent_work_log.md TB-{task_id:03d} commit {commit_hash} does not touch listed task files"
            )
    return errors


def _extract_work_log_files_changed(block: str) -> set[str]:
    match = re.search(r"(?mi)^- Files changed:\s*(.+)$", block)
    if not match:
        return set()
    value = match.group(1).strip()
    backtick_paths = re.findall(r"`([^`]+)`", value)
    if backtick_paths:
        return {path.strip() for path in backtick_paths if _looks_like_repo_path(path.strip())}
    return {
        part.strip()
        for part in value.split(",")
        if _looks_like_repo_path(part.strip())
    }


def _looks_like_repo_path(value: str) -> bool:
    return "/" in value and not value.startswith("see ")


def _git_commit_is_ancestor_of_head(commit_hash: str) -> bool:
    result = subprocess.run(
        ["git", "merge-base", "--is-ancestor", commit_hash, "HEAD"],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0


def _git_repository_is_shallow() -> bool:
    result = subprocess.run(
        ["git", "rev-parse", "--is-shallow-repository"],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        check=False,
    )
    return result.returncode == 0 and result.stdout.strip() == "true"


def _git_commit_changed_files(commit_hash: str) -> set[str]:
    result = subprocess.run(
        ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", commit_hash],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return set()
    return {line.strip() for line in result.stdout.splitlines() if line.strip()}


def _section_between(text: str, start_heading: str, end_heading: str) -> str:
    start = text.find(start_heading)
    if start == -1:
        return ""
    start += len(start_heading)
    end = text.find(end_heading, start)
    return text[start:] if end == -1 else text[start:end]


def _tb_heading_lines(text: str) -> list[tuple[int, str]]:
    lines: list[tuple[int, str]] = []
    in_fence = False
    for line_number, line in enumerate(text.splitlines(), start=1):
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence and line.startswith("### TB-"):
            lines.append((line_number, line))
    return lines


def _extract_tb_headings(text: str) -> list[tuple[int, str]]:
    entries: list[tuple[int, str]] = []
    for _line_number, line in _tb_heading_lines(text):
        match = re.match(r"^### TB-(\d{3}): (.+)$", line)
        if match:
            entries.append((int(match.group(1)), match.group(2).strip()))
    return entries


def _extract_tb_blocks(text: str) -> list[tuple[int, str]]:
    matches = list(re.finditer(r"(?m)^### TB-(\d{3}): .*$", text))
    blocks: list[tuple[int, str]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        blocks.append((int(match.group(1)), text[match.start():end]))
    return blocks
