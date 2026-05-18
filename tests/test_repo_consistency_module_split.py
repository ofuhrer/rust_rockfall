from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

from scripts.lib import repo_consistency_backlog as backlog_hygiene
from scripts.lib import repo_consistency_claims as claim_hygiene


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "check_repo_consistency.py"
SPEC = importlib.util.spec_from_file_location("check_repo_consistency", SCRIPT_PATH)
assert SPEC is not None
check_repo_consistency = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(check_repo_consistency)


def _write_backlog_fixture(root: Path, *, bad_heading: bool = False, missing_inspect_first: bool = False) -> None:
    docs = root / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    (docs / "example.md").write_text("example", encoding="utf-8")
    heading = "### TB-001 (P1): Example Task" if bad_heading else "### TB-001: Example Task"
    inspect_first = "docs/missing.md" if missing_inspect_first else "docs/example.md"
    (docs / "task_backlog.md").write_text(
        "\n".join(
            [
                "# Task Backlog",
                "",
                "Status: authoritative executable task backlog.",
                "",
                "## Active Tasks",
                "",
                heading,
                "",
                "Inspect first:",
                "",
                f"- `{inspect_first}`",
                "",
                "## Backlog Protocol",
                "",
                "Task headings must always be exactly:",
                "Do not put priority, status, owner, or tags in the heading.",
                "Do not keep completed tasks here.",
                "Append completed TB work to the bottom of `docs/agent_work_log.md`",
                "Inspect first entries must resolve to tracked repository files unless explicitly marked `external:` or `generated scratch:`.",
            ]
        ),
        encoding="utf-8",
    )


def _write_work_log_fixture(root: Path, *, stale_commit_placeholder: bool = False) -> None:
    docs = root / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    commit_line = "- Commit: pending" if stale_commit_placeholder else "- Commit: local"
    (docs / "agent_work_log.md").write_text(
        "\n".join(
            [
                "# Agent Work Log",
                "",
                "Append-only current work log for TB tasks.",
                "",
                "### TB-002: Example Work",
                "",
                "- Date: 2026-05-18",
                commit_line,
                "- Objective: Example.",
                "- Files changed: `scripts/example.py`, `tests/test_example.py`",
                "- Implementation summary: Example.",
                "- Checks run: example",
                "- Result/status: completed",
                "- Boundaries: example",
                "- Next task: backlog refill needed",
                "",
                "## Entry Template",
                "",
                "Always append new entries at the bottom of this file.",
                "Use one `### TB-XXX: Short Title` heading per completed task.",
                "Keep the TB entries in ascending order.",
            ]
        ),
        encoding="utf-8",
    )


class RepoConsistencyModuleSplitTests(unittest.TestCase):
    def test_backlog_module_accepts_clean_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_backlog_fixture(root)
            _write_work_log_fixture(root)
            original_root = backlog_hygiene.ROOT
            try:
                backlog_hygiene.ROOT = root
                self.assertEqual(backlog_hygiene.check_task_backlog_and_work_log_hygiene(), [])
                self.assertEqual(backlog_hygiene.check_active_backlog_inspect_first_paths(), [])
            finally:
                backlog_hygiene.ROOT = original_root

    def test_backlog_module_rejects_targeted_failure_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_backlog_fixture(root, missing_inspect_first=True)
            _write_work_log_fixture(root, stale_commit_placeholder=True)
            original_root = backlog_hygiene.ROOT
            try:
                backlog_hygiene.ROOT = root
                errors = backlog_hygiene.check_task_backlog_and_work_log_hygiene()
                inspect_errors = backlog_hygiene.check_active_backlog_inspect_first_paths()
            finally:
                backlog_hygiene.ROOT = original_root

        self.assertTrue(errors)
        self.assertTrue(
            any("Commit: pending" in error for error in errors),
            msg=f"expected stale work-log failure, got: {errors}",
        )
        self.assertTrue(
            any("inspect-first path missing" in error for error in inspect_errors),
            msg=f"expected inspect-first failure, got: {inspect_errors}",
        )

    def test_claim_module_accepts_clean_fixture(self) -> None:
        errors = claim_hygiene.find_hazard_claim_hygiene_errors(
            "Future annual frequency products require source-frequency contracts.",
            "fixture.md",
        )

        self.assertEqual(errors, [])

    def test_claim_module_rejects_targeted_failure_fixture(self) -> None:
        errors = claim_hygiene.find_hazard_claim_hygiene_errors(
            "The generated package is a risk map for the pilot area.",
            "fixture.md",
        )

        self.assertTrue(errors)
        self.assertTrue(any("risk-map claim" in error for error in errors))

    def test_main_returns_success_for_clean_split_family_checks(self) -> None:
        check_names = [
            name
            for name, value in vars(check_repo_consistency).items()
            if name.startswith("check_") and callable(value)
        ]
        originals = {name: getattr(check_repo_consistency, name) for name in check_names}
        try:
            for name in check_names:
                setattr(check_repo_consistency, name, lambda: [])
            self.assertEqual(check_repo_consistency.main(), 0)
        finally:
            for name, original in originals.items():
                setattr(check_repo_consistency, name, original)

    def test_main_returns_failure_for_targeted_split_family_error(self) -> None:
        check_names = [
            name
            for name, value in vars(check_repo_consistency).items()
            if name.startswith("check_") and callable(value)
        ]
        originals = {name: getattr(check_repo_consistency, name) for name in check_names}
        try:
            for name in check_names:
                setattr(check_repo_consistency, name, lambda: [])
            setattr(
                check_repo_consistency,
                "check_task_backlog_and_work_log_hygiene",
                lambda: ["docs/task_backlog.md TB-001 example failure"],
            )
            self.assertEqual(check_repo_consistency.main(), 1)
        finally:
            for name, original in originals.items():
                setattr(check_repo_consistency, name, original)


if __name__ == "__main__":
    unittest.main()
