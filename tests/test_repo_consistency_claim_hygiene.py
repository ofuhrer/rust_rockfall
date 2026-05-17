from __future__ import annotations

import importlib.util
import unittest
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "check_repo_consistency.py"
SPEC = importlib.util.spec_from_file_location("check_repo_consistency", SCRIPT_PATH)
assert SPEC is not None
check_repo_consistency = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(check_repo_consistency)


class HazardClaimHygieneTests(unittest.TestCase):
    def test_rejects_tracked_copy_suffix_docs(self) -> None:
        tracked = [
            "docs/next_development_targets.md",
            "docs/next_development_targets 2.md",
            "docs/archive/old copy.md",
        ]

        self.assertEqual(
            check_repo_consistency.find_copy_suffix_doc_paths(tracked),
            ["docs/next_development_targets 2.md", "docs/archive/old copy.md"],
        )

    def test_current_roadmap_target_authority_is_unambiguous(self) -> None:
        self.assertEqual(check_repo_consistency.check_roadmap_target_authority(), [])

    def test_task_backlog_and_work_log_hygiene_is_clean(self) -> None:
        self.assertEqual(check_repo_consistency.check_task_backlog_and_work_log_hygiene(), [])

    def test_active_backlog_inspect_first_paths_are_resolvable(self) -> None:
        backlog_text = (ROOT / "docs/task_backlog.md").read_text()

        self.assertEqual(
            check_repo_consistency.find_missing_active_backlog_inspect_first_paths(backlog_text, root=ROOT),
            [],
        )

    def test_active_backlog_inspect_first_paths_detect_missing_file(self) -> None:
        backlog_text = """## Active Tasks

### TB-999: Example Task

Inspect first:

- `docs/example.md`
- `scripts/missing_reference.py`
- `external: /tmp/external-reference.pdf`

## Backlog Protocol
"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / "scripts").mkdir()
            (root / "docs/example.md").write_text("example", encoding="utf-8")

            errors = check_repo_consistency.find_missing_active_backlog_inspect_first_paths(backlog_text, root=root)

        self.assertEqual(
            errors,
            ["docs/task_backlog.md TB-999 inspect-first path missing: scripts/missing_reference.py"],
        )

    def test_command_plan_script_reference_audit_detects_stale_reference(self) -> None:
        report = {
            "commands": [
                {
                    "command": "PYENV_VERSION=system uv run python scripts/does_not_exist.py --format json",
                    "blocked_reason": "",
                }
            ]
        }

        errors = check_repo_consistency.find_command_plan_script_reference_errors(
            report,
            label="fake command plan",
        )

        self.assertEqual(
            errors,
            [
                "fake command plan references missing tracked script scripts/does_not_exist.py "
                "at fake command plan.commands[0].command"
            ],
        )

    def test_task_hygiene_detects_unsorted_duplicate_or_stale_entries(self) -> None:
        backlog_text = """## Active Tasks

### TB-002: Second

### TB-001 (P0): First

### TB-002: Duplicate

## Backlog Protocol
"""
        work_log_text = """### TB-003: Third

- Date: 2026-05-16
- Commit: pending
- Objective: x
- Files changed: x
- Implementation summary: x
- Checks run: pending
- Result/status: completed.
- Boundaries: x
- Next task: none

### TB-002: Second

- Date: 2026-05-16
- Commit: `abc1234`
- Objective: x
- Files changed: x
- Implementation summary: x
- Checks run: x
- Result/status: completed.
- Boundaries: x
- Next task: backlog refill needed
"""

        backlog_entries = check_repo_consistency._extract_tb_headings(
            check_repo_consistency._section_between(backlog_text, "## Active Tasks", "## Backlog Protocol")
        )
        work_log_entries = check_repo_consistency._extract_tb_headings(work_log_text)

        self.assertEqual([task_id for task_id, _ in backlog_entries], [2, 2])
        self.assertEqual([task_id for task_id, _ in work_log_entries], [3, 2])
        self.assertRegex(backlog_text, r"(?m)^### TB-\d{3} \(P\d+\):", msg="fixture should contain bad priority heading")
        self.assertRegex(work_log_text, r"Commit:\s*pending", msg="fixture should contain stale commit placeholder")

    def test_task_hygiene_detects_unreachable_work_log_commits(self) -> None:
        work_log_text = """### TB-010: Good

- Date: 2026-05-16
- Commit: `abc1234`
- Objective: x
- Files changed: x
- Implementation summary: x
- Checks run: x
- Result/status: completed.
- Boundaries: x
- Next task: `TB-011`

### TB-011: Bad

- Date: 2026-05-16
- Commit: `def5678`
- Objective: x
- Files changed: x
- Implementation summary: x
- Checks run: x
- Result/status: completed.
- Boundaries: x
- Next task: backlog refill needed
"""

        errors = check_repo_consistency._find_unreachable_work_log_commits(
            work_log_text,
            is_ancestor=lambda commit_hash: commit_hash == "abc1234",
        )

        self.assertEqual(
            errors,
            ["docs/agent_work_log.md TB-011 commit def5678 is not reachable from HEAD"],
        )

    def test_task_hygiene_detects_commit_that_does_not_touch_task_files(self) -> None:
        work_log_text = """### TB-012: Task

- Date: 2026-05-16
- Commit: `abc1234`
- Objective: x
- Files changed: `scripts/task_helper.py`, `tests/test_task_helper.py`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary: x
- Checks run: x
- Result/status: completed.
- Boundaries: x
- Next task: backlog refill needed
"""

        errors = check_repo_consistency._find_work_log_commits_without_task_file_changes(
            work_log_text,
            changed_files_provider=lambda _commit_hash: {"docs/agent_work_log.md", "docs/task_backlog.md"},
        )

        self.assertEqual(
            errors,
            ["docs/agent_work_log.md TB-012 commit abc1234 does not touch listed task files"],
        )

    def test_task_hygiene_accepts_commit_that_touches_any_task_file(self) -> None:
        work_log_text = """### TB-013: Task

- Date: 2026-05-16
- Commit: `abc1234`
- Objective: x
- Files changed: scripts/task_helper.py, tests/test_task_helper.py, docs/task_backlog.md, docs/agent_work_log.md
- Implementation summary: x
- Checks run: x
- Result/status: completed.
- Boundaries: x
- Next task: backlog refill needed
"""

        errors = check_repo_consistency._find_work_log_commits_without_task_file_changes(
            work_log_text,
            changed_files_provider=lambda _commit_hash: {"scripts/task_helper.py"},
        )

        self.assertEqual(errors, [])

    def test_python_tool_dependency_metadata_is_consistent(self) -> None:
        self.assertEqual(check_repo_consistency.check_python_tool_dependency_metadata(), [])

    def test_python_execution_policy_guidance_is_clean(self) -> None:
        self.assertEqual(check_repo_consistency.check_python_execution_policy_guidance(), [])

    def test_demo_claim_boundary_audit_current_artifacts_are_clean(self) -> None:
        self.assertEqual(check_repo_consistency.check_hazard_claim_hygiene(), [])

    def test_rejects_bare_annual_current_product_claim(self) -> None:
        errors = check_repo_consistency.find_hazard_claim_hygiene_errors(
            "Current hazard layers report annual frequency for each cell.",
            "fixture.md",
        )

        self.assertTrue(errors)
        self.assertIn("annual frequency claim", errors[0])

    def test_allows_explicit_future_annual_boundary(self) -> None:
        errors = check_repo_consistency.find_hazard_claim_hygiene_errors(
            "Future annual frequency products require source-frequency contracts.",
            "fixture.md",
        )

        self.assertEqual(errors, [])

    def test_rejects_bare_intensity_frequency_for_current_products(self) -> None:
        errors = check_repo_consistency.find_hazard_claim_hygiene_errors(
            "Current threshold layers are intensity-frequency products.",
            "fixture.md",
        )

        self.assertTrue(errors)
        self.assertIn("intensity-frequency", errors[0])

    def test_allows_current_conditional_intensity_exceedance(self) -> None:
        errors = check_repo_consistency.find_hazard_claim_hygiene_errors(
            "Current threshold layers are conditional intensity-exceedance products.",
            "fixture.md",
        )

        self.assertEqual(errors, [])

    def test_rejects_bare_risk_map_language(self) -> None:
        errors = check_repo_consistency.find_hazard_claim_hygiene_errors(
            "The generated package is a risk map for the pilot area.",
            "fixture.md",
        )

        self.assertTrue(errors)
        self.assertIn("risk-map claim", errors[0])

    def test_rejects_true_demo_claim_boundary_flags(self) -> None:
        text = """operational_claims_allowed: true
physical_probability_claims_allowed: true
annual_frequency_claims_allowed: true
risk_exposure_vulnerability_claims_allowed: true
scale_up_authorized: true
distributed_execution_authorized: true
The package is a risk map and an official hazard map.
"""

        errors = check_repo_consistency.find_hazard_claim_hygiene_errors(text, "demo.md")

        self.assertTrue(errors)
        self.assertTrue(any("claim-boundary flag" in error for error in errors))
        self.assertTrue(any("risk-map claim" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
