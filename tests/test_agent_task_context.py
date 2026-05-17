import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "print_agent_task_context.py"
SPEC = importlib.util.spec_from_file_location("print_agent_task_context", SCRIPT_PATH)
assert SPEC is not None
agent_context = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = agent_context
SPEC.loader.exec_module(agent_context)


class AgentTaskContextTest(unittest.TestCase):
    def current_active_task_id(self) -> str:
        report = agent_context.build_report(run_checks=False)
        if not report["active_tasks"]:
            self.skipTest("No active tasks are listed in docs/task_backlog.md")
        return report["active_tasks"][0]["task_id"]

    def test_extracts_active_task_and_inspect_first_files(self) -> None:
        backlog = """
# Task Backlog

## Active Tasks

### TB-999: Example Task

Priority: P0

Inspect first:

- `docs/example.md`
- `scripts/example.py`

Expected work:

- do something.

## Deferred Backlog
"""
        tasks = agent_context.parse_active_tasks(backlog)
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].task_id, "TB-999")
        self.assertEqual(tasks[0].title, "Example Task")
        self.assertEqual(tasks[0].priority, "P0")
        self.assertEqual(tasks[0].inspect_first, ["docs/example.md", "scripts/example.py"])

    def test_extracts_active_tasks_before_backlog_protocol(self) -> None:
        backlog = """
# Task Backlog

## Active Tasks

### TB-998: Compact Backlog Task

Inspect first:

- `docs/example.md`

## Backlog Protocol
"""
        tasks = agent_context.parse_active_tasks(backlog)
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].task_id, "TB-998")
        self.assertEqual(tasks[0].title, "Compact Backlog Task")
        self.assertEqual(tasks[0].inspect_first, ["docs/example.md"])

    def test_report_contains_required_json_fields_without_live_checks(self) -> None:
        report = agent_context.build_report(run_checks=False)

        self.assertEqual(report["agent_task_context_status"], "ready")
        self.assertEqual(report["repo_root"], str(ROOT))
        self.assertEqual(report["python_invocation"], "PYENV_VERSION=system uv run python")
        self.assertIn("canonical_helpers", report)
        self.assertIn(
            "scripts/convert_same_scale_package_to_cog.py",
            {helper["path"] for helper in report["canonical_helpers"]},
        )
        self.assertIn("worker_output_guidance", report)
        self.assertEqual(
            report["worker_output_guidance"]["schema_version"],
            agent_context.WORKER_OUTPUT_GUIDANCE_SCHEMA_VERSION,
        )
        self.assertEqual(
            report["worker_output_guidance"]["final_report_schema"],
            agent_context.WORKER_OUTPUT_REPORT_SCHEMA,
        )
        self.assertIn("Redirect large JSON, logs, and diffs to /tmp.", report["worker_output_guidance"]["command_output_policy"])
        self.assertIn("known_environment_issues", report)
        self.assertIn("generated_roots_to_avoid", report)
        self.assertEqual(report["push_policy"]["repository_pre_push_hook"], "not_installed")
        self.assertTrue(report["read_only"])
        self.assertEqual(report["live_checks_status"], "skipped")
        self.assertIn("docs/agent_work_log.md", ROOT.joinpath("AGENTS.md").read_text())

    def test_report_can_focus_current_active_task_without_live_checks(self) -> None:
        current_task_id = self.current_active_task_id()

        report = agent_context.build_report(current_task_id, run_checks=False)

        self.assertEqual(report["agent_task_context_status"], "ready")
        self.assertEqual(report["selected_task"]["task_id"], current_task_id)
        self.assertEqual(report["detail"], "compact")
        self.assertIn("inspect_first", report["selected_task"])
        other_tasks = [task for task in report["active_tasks"] if task["task_id"] != current_task_id]
        self.assertTrue(other_tasks)
        self.assertNotIn("inspect_first", other_tasks[0])
        self.assertLess(len(report["canonical_helpers"]), len(agent_context.CANONICAL_HELPERS))

    def test_full_detail_keeps_all_task_details_and_helpers(self) -> None:
        current_task_id = self.current_active_task_id()

        report = agent_context.build_report(current_task_id, run_checks=False, detail="full")

        self.assertEqual(report["detail"], "full")
        self.assertEqual(len(report["canonical_helpers"]), len(agent_context.CANONICAL_HELPERS))
        self.assertTrue(all("inspect_first" in task for task in report["active_tasks"]))

    def test_rendered_report_includes_compact_worker_output_guidance(self) -> None:
        report = agent_context.build_report(run_checks=False)
        text = agent_context.render_text(report)

        self.assertIn("worker_output_guidance:", text)
        self.assertIn("agent_worker_output_guidance_v1", text)
        self.assertIn("final_report_schema: TASK, STATUS, SUMMARY, FILES_CHANGED", text)
        self.assertIn("Preserve the final relevant error block", text)

    def test_missing_task_is_explicitly_blocked(self) -> None:
        report = agent_context.build_report("TB-000", run_checks=False)

        self.assertEqual(report["agent_task_context_status"], "blocked_missing_task")
        self.assertIsNone(report["selected_task"])
        self.assertIn("backlog_refill_needed", report)
        self.assertEqual(report["backlog_refill_needed"], not bool(report["active_tasks"]))
        if not report["active_tasks"]:
            self.assertEqual(report["backlog_note"], "Backlog refill needed")

    def test_script_run_outside_repo_root_reports_resolved_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--task",
                    self.current_active_task_id(),
                    "--format",
                    "json",
                    "--no-live-checks",
                ],
                cwd=tmp,
                check=True,
                capture_output=True,
                text=True,
            )

        report = json.loads(completed.stdout)
        self.assertEqual(report["repo_root"], str(ROOT))
        self.assertFalse(report["running_from_repo_root"])
        self.assertEqual(report["agent_task_context_status"], "ready")

    def test_chant_sura_task_triggers_second_site_preflight(self) -> None:
        task = agent_context.ActiveTask(
            task_id="TB-999",
            title="Example Chant Sura Task",
            priority="P0",
            inspect_first=[],
            text="Chant Sura public-context staging boundary",
        )

        self.assertTrue(agent_context.should_run_chant_sura_preflight(task, [task]))

    def test_generated_roots_list_mentions_placeholder_paths(self) -> None:
        report = agent_context.build_report(run_checks=False)

        roots = "\n".join(report["generated_roots_to_avoid"])
        self.assertIn("data/processed/swisstopo/placeholder_second_site_v1", roots)
        self.assertIn("validation/policies/*placeholder*", roots)
        self.assertIn("existing_generated_placeholder_paths", report)

    def test_json_payload_from_nonzero_readiness_command_is_preserved(self) -> None:
        original_run = agent_context.subprocess.run

        def fake_run(*_args, **_kwargs):
            return subprocess.CompletedProcess(
                args=["uv"],
                returncode=2,
                stdout='{"readiness_status": "blocked_missing_inputs"}',
                stderr="",
            )

        try:
            agent_context.subprocess.run = fake_run
            result = agent_context.run_json_command(["uv"])
        finally:
            agent_context.subprocess.run = original_run

        self.assertEqual(result["status"], "blocked_missing_inputs")
        self.assertEqual(result["returncode"], 2)
        self.assertEqual(result["payload"]["readiness_status"], "blocked_missing_inputs")


if __name__ == "__main__":
    unittest.main()
