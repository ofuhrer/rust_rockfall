#!/usr/bin/env python3
"""Run the same repository checks locally and in GitHub Actions."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Command:
    label: str
    argv: tuple[str, ...]


CLEAN_CHECKOUT_EXCLUDED_MARKERS = (
    "data/processed/swisstopo/",
    "hazard/results/",
    "validation/private/",
)

CLEAN_CHECKOUT_EXCLUDED_MODULES = {
    "tests.test_aoi_scenario_preview",
    "tests.test_balfrin_demonstration_replay_smoke",
    "tests.test_balfrin_management_demo_package",
    "tests.test_balfrin_multi_release_zone_demo_handoff",
    "tests.test_balfrin_physical_credibility_evidence_gaps",
    "tests.test_balfrin_scale_readiness_matrix",
    "tests.test_conditional_denominator_provenance",
    "tests.test_execute_management_aoi_balfrin_run",
    "tests.test_extreme_layer_sensitivity_smoke",
    "tests.test_local_scientific_backlog_recommendation",
    "tests.test_multi_zone_reducer_pressure",
    "tests.test_plan_pragmatic_release_plan",
    "tests.test_public_geodata_cache_stager",
    "tests.test_release_candidate_zero_result_diagnostic",
    "tests.test_scenario_storage_output_tier_pressure",
    "tests.test_swiss_wide_execution_envelope",
    "tests.test_trajectory_deposition_traceability",
    "tests.test_tschamut_block_scenario_table_generation",
}


def python_command(*args: str) -> tuple[str, ...]:
    return (sys.executable, *args)


def clean_checkout_test_modules() -> tuple[str, ...]:
    modules: list[str] = []
    for path in sorted((ROOT / "tests").glob("test_*.py")):
        text = path.read_text(encoding="utf-8")
        if any(marker in text for marker in CLEAN_CHECKOUT_EXCLUDED_MARKERS):
            continue
        relative_module = path.relative_to(ROOT).with_suffix("")
        module = relative_module.as_posix().replace("/", ".")
        if module in CLEAN_CHECKOUT_EXCLUDED_MODULES:
            continue
        modules.append(module)
    return tuple(modules)


def build_commands(args: argparse.Namespace) -> dict[str, list[Command]]:
    performance_output_root = Path(args.performance_output_root)
    return {
        "lint": [
            Command("cargo fmt --check", ("cargo", "fmt", "--check")),
            Command(
                "cargo clippy",
                ("cargo", "clippy", "--all-targets", "--all-features", "--", "-D", "warnings"),
            ),
        ],
        "rust-tests": [
            Command("cargo test", ("cargo", "test")),
        ],
        "verify": [
            Command(
                "cargo run --release -- verify --all",
                ("cargo", "run", "--release", "--", "verify", "--all"),
            ),
            Command(
                "cargo run --release -- validate --all",
                ("cargo", "run", "--release", "--", "validate", "--all"),
            ),
        ],
        "python-tests": [
            Command(
                "clean-checkout Python unit tests",
                python_command("-m", "unittest", *clean_checkout_test_modules()),
            ),
        ],
        "python-full-tests": [
            Command(
                "full Python unit tests",
                python_command("-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"),
            ),
        ],
        "repo-consistency": [
            Command("repository consistency", python_command("scripts/check_repo_consistency.py")),
        ],
        "performance-standard": [
            Command(
                "standard synthetic benchmark",
                python_command(
                    "scripts/run_performance_benchmark.py",
                    "--profile",
                    "standard",
                    "--output-root",
                    performance_output_root.as_posix(),
                ),
            ),
        ],
    }


SUITE_ALIASES = {
    "python": ("python-tests", "repo-consistency"),
    "python-full": ("python-full-tests", "repo-consistency"),
    "performance": ("performance-standard",),
    "ci": (
        "lint",
        "rust-tests",
        "verify",
        "python-tests",
        "repo-consistency",
        "performance-standard",
    ),
}


def expand_suites(suites: Iterable[str]) -> list[str]:
    expanded: list[str] = []
    for suite in suites:
        for item in SUITE_ALIASES.get(suite, (suite,)):
            if item not in expanded:
                expanded.append(item)
    return expanded


def run_command(command: Command, *, dry_run: bool) -> int:
    printable = " ".join(command.argv)
    print(f"\n==> {command.label}")
    print(f"$ {printable}", flush=True)
    if dry_run:
        return 0

    env = os.environ.copy()
    env.setdefault("PYENV_VERSION", "system")
    started = time.perf_counter()
    result = subprocess.run(command.argv, cwd=ROOT, env=env, check=False)
    elapsed = time.perf_counter() - started
    print(f"<== {command.label} exited {result.returncode} after {elapsed:.1f}s", flush=True)
    return result.returncode


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run canonical CI checks from the repository root. Use "
            "`PYENV_VERSION=system uv run python scripts/run_ci_local.py --suite ci` locally."
        )
    )
    parser.add_argument(
        "--suite",
        action="append",
        choices=(
            "ci",
            "python",
            "python-full",
            "performance",
            "lint",
            "rust-tests",
            "verify",
            "python-tests",
            "python-full-tests",
            "repo-consistency",
            "performance-standard",
        ),
        help="Suite to run. May be passed multiple times. Defaults to ci.",
    )
    parser.add_argument(
        "--performance-output-root",
        default="validation/results/performance_ci_local",
        help="Output root for the standard synthetic benchmark suite.",
    )
    parser.add_argument(
        "--keep-going",
        action="store_true",
        help="Continue after failures and return nonzero after all selected commands finish.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the resolved command plan without running commands.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    commands_by_suite = build_commands(args)
    suites = expand_suites(args.suite or ["ci"])
    failures: list[tuple[str, int]] = []

    for suite in suites:
        commands = commands_by_suite.get(suite)
        if commands is None:
            raise SystemExit(f"unknown suite: {suite}")
        print(f"\n# Suite: {suite}", flush=True)
        for command in commands:
            returncode = run_command(command, dry_run=args.dry_run)
            if returncode != 0:
                failures.append((command.label, returncode))
                if not args.keep_going:
                    print(f"\nFAILED: {command.label} exited {returncode}", file=sys.stderr)
                    return returncode

    if failures:
        print("\nFailed commands:", file=sys.stderr)
        for label, returncode in failures:
            print(f"- {label}: {returncode}", file=sys.stderr)
        return 1

    print("\nAll selected CI commands passed.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
