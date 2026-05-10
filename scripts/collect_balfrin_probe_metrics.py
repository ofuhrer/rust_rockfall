#!/usr/bin/env python3
"""Collect lightweight summary metrics from a balfrin probe run directory."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--run-root",
        type=Path,
        required=True,
        help="Run root produced by submit_balfrin_probe.py.",
    )
    parser.add_argument(
        "--probe-manifest",
        type=Path,
        default=None,
        help="Optional explicit probe manifest path.",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        help="Optional JSON path to write the summary.",
    )
    return parser.parse_args(argv)


def _safe_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _safe_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _load_json(path: Path | None) -> dict[str, Any] | None:
    if path is None or not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def _command_output_dir(
    command_plan: dict[str, Any],
    *,
    run_root: Path,
) -> Path | None:
    commands = command_plan.get("commands")
    if not isinstance(commands, list):
        return None
    for entry in commands:
        if not isinstance(entry, dict):
            continue
        if entry.get("name") != "build_conditional_hazard_layers":
            continue
        command = entry.get("command")
        if not isinstance(command, list):
            continue
        cwd = Path(str(entry.get("cwd", str(run_root)))).expanduser()
        if not cwd.is_absolute():
            cwd = (run_root / cwd).resolve()
        tokens = [str(token) for token in command]
        for idx, token in enumerate(tokens):
            if token == "--output-dir" and idx + 1 < len(tokens):
                output_dir = Path(tokens[idx + 1]).expanduser()
                if not output_dir.is_absolute():
                    return (cwd / output_dir).resolve()
                return output_dir
    return None


def _find_hazard_manifest(output_dir: Path) -> Path | None:
    if not output_dir.exists():
        return None
    candidates = sorted(output_dir.glob("*_manifest.json"))
    if not candidates:
        return None
    preferred = [path for path in candidates if path.name.startswith("validation_")]
    return preferred[0] if preferred else candidates[0]


def _load_scaling_summary(output_dir: Path) -> dict[str, Any]:
    for path in sorted(output_dir.glob("*scaling_summary*.json")):
        summary = _load_json(path)
        if not isinstance(summary, dict):
            continue
        performance = summary.get("performance")
        if isinstance(performance, dict):
            return performance
    return {}


def _count_decision_manifests(directory: Path) -> dict[str, int]:
    counts: dict[str, int] = {}
    if not directory.exists():
        return counts
    for manifest_path in sorted(directory.glob("*_manifest.json")):
        payload = _load_json(manifest_path)
        if payload is None:
            continue
        decision = payload.get("orchestration_decision")
        if not isinstance(decision, str):
            continue
        counts[decision] = counts.get(decision, 0) + 1
    return counts


def _find_optional_plan_id(path_candidates: list[Path], key: str) -> str | None:
    for path in path_candidates:
        payload = _load_json(path)
        if payload is None:
            continue
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def collect_run_metrics(
    run_root: Path,
    *,
    probe_manifest: Path | None = None,
) -> dict[str, Any]:
    run_root = run_root.resolve()
    command_plan = _load_json(run_root / "command_plan.json") or {}
    command_plan_probe_manifest = command_plan.get("input")
    command_plan_path = run_root / "command_plan.json"
    output_root = _command_output_dir(command_plan, run_root=run_root) or (run_root / "output")

    output_manifest = _find_hazard_manifest(output_root)
    manifest = _load_json(output_manifest) if output_manifest else None
    performance = manifest.get("performance", {}) if isinstance(manifest, dict) else {}
    conditional_execution = manifest.get("conditional_execution", {}) if isinstance(manifest, dict) else {}
    output_budget = conditional_execution.get("output_budget", {}) if isinstance(conditional_execution, dict) else {}
    trajectory_execution = conditional_execution.get("trajectory_generation", {}) if isinstance(conditional_execution, dict) else {}
    reducer_execution = conditional_execution.get("reducer", {}) if isinstance(conditional_execution, dict) else {}

    scaling_summary = _load_scaling_summary(output_root) if output_root.exists() else {}

    trajectory_plan_candidates = sorted(output_root.glob("*trajectory_execution_plan_v1.json"))
    reducer_plan_candidates = sorted(output_root.glob("*execution_plan_v1.json"))
    reducer_plan_id = _find_optional_plan_id(reducer_plan_candidates, "plan_id")
    trajectory_plan_id = _find_optional_plan_id(trajectory_plan_candidates, "plan_id")
    if isinstance(trajectory_execution, dict) and isinstance(trajectory_execution.get("plan_id"), str):
        trajectory_plan_id = trajectory_plan_id or trajectory_execution.get("plan_id")
    if isinstance(reducer_execution, dict) and isinstance(reducer_execution.get("trajectory_execution_plan_id"), str):
        reducer_plan_id = reducer_plan_id or reducer_execution.get("trajectory_execution_plan_id")

    result = {
        "schema_version": "balfrin_probe_metrics_v1",
        "run_root": str(run_root),
        "probe_manifest_path": str(probe_manifest.resolve()) if probe_manifest else command_plan_probe_manifest,
        "command_plan_path": str(command_plan_path),
        "output_root": str(output_root),
        "hazard_manifest_path": str(output_manifest) if output_manifest else None,
        "git_commit": manifest.get("git_hash") if isinstance(manifest, dict) else None,
        "total_wall_seconds": _safe_float(
            (
                performance.get("total_wall_seconds")
                if isinstance(performance, dict)
                else None
            )
        ),
        "output_bytes": _safe_int(
            (
                performance.get("output_bytes")
                if isinstance(performance, dict)
                else None
            )
            or output_budget.get("output_bytes")
        ),
        "output_file_count": _safe_int(
            (
                performance.get("output_file_count")
                if isinstance(performance, dict)
                else None
            )
            or output_budget.get("output_file_count")
        ),
        "output_write_seconds": _safe_float(
            performance.get("output_write_seconds") if isinstance(performance, dict) else None
        ),
        "output_write_kind_seconds": (
            scaling_summary.get("output_write_kind_seconds", {})
            if isinstance(scaling_summary, dict)
            else {}
        ),
        "output_write_kind_bytes": (
            scaling_summary.get("output_write_kind_bytes", {})
            if isinstance(scaling_summary, dict)
            else {}
        ),
        "trajectory_plan_id": trajectory_plan_id,
        "reducer_plan_id": reducer_plan_id,
        "trajectory_decision_counts": _count_decision_manifests(output_root / "trajectory_chunks"),
        "reducer_decision_counts": _count_decision_manifests(output_root / "chunks"),
    }
    return result


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    summary = collect_run_metrics(
        args.run_root,
        probe_manifest=args.probe_manifest,
    )
    if args.output_json:
        args.output_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(f"wrote probe metrics summary to {args.output_json}")
    else:
        print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
