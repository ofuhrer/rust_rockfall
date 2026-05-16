#!/usr/bin/env python3
"""Collect lightweight summary metrics from a balfrin probe run directory."""

from __future__ import annotations

import argparse
import json
import re
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


def _count_output_families(outputs: list[Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for entry in outputs:
        if not isinstance(entry, dict):
            continue
        kind = entry.get("kind")
        if not isinstance(kind, str) or not kind:
            continue
        counts[kind] = counts.get(kind, 0) + 1
    return counts


def _first_present(*values: Any) -> Any:
    for value in values:
        if value is not None:
            return value
    return None


def _missing_metrics(metrics: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    if metrics.get("wall_time_seconds") is None:
        missing.append("wall_time_seconds")
    if metrics.get("memory_peak_mb") is None:
        missing.append("memory_peak_mb")

    validation_output = metrics.get("validation_output") if isinstance(metrics.get("validation_output"), dict) else {}
    hazard_output = metrics.get("hazard_output") if isinstance(metrics.get("hazard_output"), dict) else {}
    restartability = (
        metrics.get("restartability_metadata")
        if isinstance(metrics.get("restartability_metadata"), dict)
        else {}
    )

    if validation_output.get("file_count") is None:
        missing.append("validation_output.file_count")
    if validation_output.get("bytes") is None:
        missing.append("validation_output.bytes")
    if hazard_output.get("file_count") is None:
        missing.append("hazard_output.file_count")
    if hazard_output.get("bytes") is None:
        missing.append("hazard_output.bytes")
    if metrics.get("conditional_curve_row_count") is None:
        missing.append("conditional_curve_row_count")
    if not metrics.get("reduced_output_family_counts"):
        missing.append("reduced_output_family_counts")
    if restartability.get("trajectory_plan_id") is None:
        missing.append("restartability_metadata.trajectory_plan_id")
    if restartability.get("reducer_plan_id") is None:
        missing.append("restartability_metadata.reducer_plan_id")
    if not restartability.get("trajectory_decision_counts"):
        missing.append("restartability_metadata.trajectory_decision_counts")
    if not restartability.get("reducer_decision_counts"):
        missing.append("restartability_metadata.reducer_decision_counts")
    return missing


def _build_metrics_contract(
    *,
    performance: dict[str, Any],
    conditional_execution: dict[str, Any],
    outputs: list[Any],
    scaling_summary: dict[str, Any],
    probe_metrics: dict[str, Any] | None,
    trajectory_plan_id: str | None,
    reducer_plan_id: str | None,
    trajectory_decision_counts: dict[str, int],
    reducer_decision_counts: dict[str, int],
) -> dict[str, Any]:
    output_budget = conditional_execution.get("output_budget", {}) if isinstance(conditional_execution, dict) else {}
    conditional_curve_export = (
        conditional_execution.get("conditional_curve_export", {}) if isinstance(conditional_execution, dict) else {}
    )
    restartability_probe = probe_metrics.get("restartability", {}) if isinstance(probe_metrics, dict) else {}
    validation_output = {
        "file_count": _safe_int(
            _first_present(
                performance.get("validation_output_file_count"),
                restartability_probe.get("validation_output_file_count"),
                output_budget.get("validation_output_file_count"),
            )
        ),
        "bytes": _safe_int(
            _first_present(
                performance.get("validation_output_bytes"),
                restartability_probe.get("validation_output_bytes"),
                output_budget.get("validation_output_bytes"),
            )
        ),
    }
    hazard_output = {
        "file_count": _safe_int(
            _first_present(
                performance.get("hazard_output_file_count"),
                restartability_probe.get("hazard_output_file_count"),
                output_budget.get("hazard_output_file_count"),
            )
        ),
        "bytes": _safe_int(
            _first_present(
                performance.get("hazard_output_bytes"),
                restartability_probe.get("hazard_output_bytes"),
                output_budget.get("hazard_output_bytes"),
            )
        ),
    }
    restartability_metadata = {
        "trajectory_plan_id": _first_present(
            trajectory_plan_id,
            restartability_probe.get("trajectory_plan_id"),
        ),
        "reducer_plan_id": _first_present(
            reducer_plan_id,
            restartability_probe.get("reducer_plan_id"),
        ),
        "trajectory_decision_counts": _first_present(
            trajectory_decision_counts,
            restartability_probe.get("trajectory_decision_counts"),
        ),
        "reducer_decision_counts": _first_present(
            reducer_decision_counts,
            restartability_probe.get("reducer_decision_counts"),
        ),
    }
    metrics = {
        "wall_time_seconds": _safe_float(
            _first_present(
                performance.get("total_wall_seconds"),
                restartability_probe.get("wall_time_seconds"),
            )
        ),
        "memory_peak_mb": _safe_float(
            _first_present(
                performance.get("memory_peak_mb"),
                probe_metrics.get("memory_peak_mb") if isinstance(probe_metrics, dict) else None,
                restartability_probe.get("memory_peak_mb"),
            )
        ),
        "validation_output": validation_output,
        "hazard_output": hazard_output,
        "reduced_output_family_counts": (
            probe_metrics.get("reduced_output_family_counts")
            if isinstance(probe_metrics, dict) and isinstance(probe_metrics.get("reduced_output_family_counts"), dict)
            else _count_output_families(outputs)
        ),
        "conditional_curve_row_count": _safe_int(
            _first_present(
                conditional_curve_export.get("row_count"),
                restartability_probe.get("conditional_curve_row_count"),
                output_budget.get("conditional_curve_row_count"),
            )
        ),
        "restartability_metadata": restartability_metadata,
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
    }
    missing = _missing_metrics(metrics)
    return {
        "status": "complete" if not missing else "blocked_missing_inputs",
        "blocked_reason": "" if not missing else "missing metrics: " + ", ".join(missing),
        "missing_metrics": missing,
        "source_paths": {
            "probe_metrics": str((Path("balfrin_probe_metrics.json")).as_posix()) if probe_metrics else None,
        },
        **metrics,
    }


_LOG_AUDIT_PATTERN = re.compile(
    r"\b(?:warn\w*|error\w*|fatal\w*|exception\w*|traceback\w*)\b",
    re.IGNORECASE,
)


def _log_audit_summary(logs_root: Path) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "logs_root": str(logs_root),
        "file_count": 0,
        "matched_line_count": 0,
        "warning_like_line_count": 0,
        "error_like_line_count": 0,
        "affected_log_paths": [],
        "files": [],
    }
    if not logs_root.exists():
        return summary

    file_summaries: list[dict[str, Any]] = []
    affected_paths: list[str] = []
    matched_line_count = 0
    warning_like_line_count = 0
    error_like_line_count = 0

    for path in sorted(candidate for candidate in logs_root.rglob("*") if candidate.is_file()):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        path_matched_line_count = 0
        path_warning_like_line_count = 0
        path_error_like_line_count = 0
        for line in text.splitlines():
            if not _LOG_AUDIT_PATTERN.search(line):
                continue
            path_matched_line_count += 1
            line_lower = line.lower()
            if "warn" in line_lower:
                path_warning_like_line_count += 1
            if "error" in line_lower or "fatal" in line_lower or "exception" in line_lower or "traceback" in line_lower:
                path_error_like_line_count += 1
        if path_matched_line_count == 0:
            continue
        affected_paths.append(str(path))
        file_summaries.append(
            {
                "path": str(path),
                "matched_line_count": path_matched_line_count,
                "warning_like_line_count": path_warning_like_line_count,
                "error_like_line_count": path_error_like_line_count,
            }
        )
        matched_line_count += path_matched_line_count
        warning_like_line_count += path_warning_like_line_count
        error_like_line_count += path_error_like_line_count

    summary["file_count"] = len(file_summaries)
    summary["matched_line_count"] = matched_line_count
    summary["warning_like_line_count"] = warning_like_line_count
    summary["error_like_line_count"] = error_like_line_count
    summary["affected_log_paths"] = affected_paths
    summary["files"] = file_summaries
    return summary


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
    probe_metrics = _load_json(run_root / "balfrin_probe_metrics.json")
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

    trajectory_decision_counts = _count_decision_manifests(output_root / "trajectory_chunks")
    reducer_decision_counts = _count_decision_manifests(output_root / "chunks")
    metrics_contract = _build_metrics_contract(
        performance=performance,
        conditional_execution=conditional_execution,
        outputs=manifest.get("outputs", []) if isinstance(manifest, dict) else [],
        scaling_summary=scaling_summary,
        probe_metrics=probe_metrics,
        trajectory_plan_id=trajectory_plan_id,
        reducer_plan_id=reducer_plan_id,
        trajectory_decision_counts=trajectory_decision_counts,
        reducer_decision_counts=reducer_decision_counts,
    )

    result = {
        "schema_version": "balfrin_probe_metrics_v1",
        "run_root": str(run_root),
        "probe_manifest_path": str(probe_manifest.resolve()) if probe_manifest else command_plan_probe_manifest,
        "command_plan_path": str(command_plan_path),
        "output_root": str(output_root),
        "hazard_manifest_path": str(output_manifest) if output_manifest else None,
        "git_commit": manifest.get("git_hash") if isinstance(manifest, dict) else None,
        "total_wall_seconds": metrics_contract["wall_time_seconds"],
        "memory_peak_mb": metrics_contract["memory_peak_mb"],
        "validation_output_file_count": metrics_contract["validation_output"]["file_count"],
        "validation_output_bytes": metrics_contract["validation_output"]["bytes"],
        "hazard_output_file_count": metrics_contract["hazard_output"]["file_count"],
        "hazard_output_bytes": metrics_contract["hazard_output"]["bytes"],
        "conditional_curve_row_count": metrics_contract["conditional_curve_row_count"],
        "reduced_output_family_counts": metrics_contract["reduced_output_family_counts"],
        "metrics_contract_status": metrics_contract["status"],
        "metrics_contract_blocked_reason": metrics_contract["blocked_reason"],
        "metrics_contract_missing_metrics": metrics_contract["missing_metrics"],
        "metrics_contract": metrics_contract,
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
        "output_write_kind_seconds": metrics_contract["output_write_kind_seconds"],
        "output_write_kind_bytes": metrics_contract["output_write_kind_bytes"],
        "trajectory_plan_id": trajectory_plan_id,
        "reducer_plan_id": reducer_plan_id,
        "trajectory_decision_counts": trajectory_decision_counts,
        "reducer_decision_counts": reducer_decision_counts,
        "log_audit": _log_audit_summary(run_root / "logs"),
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
