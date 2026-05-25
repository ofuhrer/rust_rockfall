from __future__ import annotations

import argparse
import unittest

from scripts import run_ci_local


class RunCiLocalTests(unittest.TestCase):
    def test_ci_alias_matches_github_actions_job_order(self) -> None:
        self.assertEqual(
            run_ci_local.expand_suites(["ci"]),
            [
                "lint",
                "rust-tests",
                "verify",
                "python-tests",
                "repo-consistency",
                "performance-standard",
            ],
        )

    def test_focused_aliases_keep_repo_consistency_with_python_suites(self) -> None:
        self.assertEqual(run_ci_local.expand_suites(["python"]), ["python-tests", "repo-consistency"])
        self.assertEqual(run_ci_local.expand_suites(["python-full"]), ["python-full-tests", "repo-consistency"])
        self.assertEqual(run_ci_local.expand_suites(["performance"]), ["performance-standard"])

    def test_clean_checkout_ci_tier_is_nonempty(self) -> None:
        modules = run_ci_local.clean_checkout_test_modules()

        self.assertIn("tests.test_run_ci_local", modules)
        self.assertEqual(tuple(sorted(modules)), modules)

    def test_build_commands_uses_clean_checkout_tier_for_python_tests(self) -> None:
        commands = run_ci_local.build_commands(
            argparse.Namespace(performance_output_root="/tmp/rust-rockfall-ci-test")
        )
        python_tests = commands["python-tests"][0]

        self.assertEqual(python_tests.label, "clean-checkout Python unit tests")
        self.assertEqual(python_tests.argv[:3], (run_ci_local.sys.executable, "-m", "unittest"))
        self.assertIn("tests.test_run_ci_local", python_tests.argv)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
