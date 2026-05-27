#!/usr/bin/env python3
"""Run the same repository checks locally and in GitHub Actions."""

from __future__ import annotations

import argparse
import os
import platform
import subprocess
import sys
import time
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
PYTHON_TEST_TIERS_PATH = ROOT / "tests" / "python_test_tiers.toml"


@dataclass(frozen=True)
class Command:
    label: str
    argv: tuple[str, ...]


def python_command(*args: str) -> tuple[str, ...]:
    return (sys.executable, *args)


def load_python_test_tiers() -> dict[str, tuple[str, ...]]:
    data = tomllib.loads(PYTHON_TEST_TIERS_PATH.read_text(encoding="utf-8"))
    tiers = data.get("tiers")
    if not isinstance(tiers, dict):
        raise SystemExit(f"{PYTHON_TEST_TIERS_PATH} is missing [tiers]")
    return {
        name: tuple(modules)
        for name, modules in tiers.items()
        if isinstance(name, str) and isinstance(modules, list)
    }


def clean_checkout_test_modules() -> tuple[str, ...]:
    tiers = load_python_test_tiers()
    modules = tiers.get("clean_checkout_ci")
    if not modules:
        raise SystemExit(f"{PYTHON_TEST_TIERS_PATH} has no clean_checkout_ci tier")
    return modules


def print_python_environment_banner() -> None:
    packages = ("yaml", "numpy", "pyarrow", "pyproj", "PIL", "scipy")
    versions: list[str] = []
    for package in packages:
        try:
            module = __import__(package)
        except Exception:
            versions.append(f"{package}=unavailable")
            continue
        versions.append(f"{package}={getattr(module, '__version__', 'unknown')}")
    print("\nPython environment:", flush=True)
    print(f"- executable: {sys.executable}", flush=True)
    print(f"- version: {sys.version.split()[0]}", flush=True)
    print(f"- platform: {platform.platform()}", flush=True)
    print(f"- packages: {', '.join(versions)}", flush=True)


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
    if command.argv[:3] == (sys.executable, "-m", "unittest"):
        print_python_environment_banner()
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
