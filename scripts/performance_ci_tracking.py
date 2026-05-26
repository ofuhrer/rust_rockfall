#!/usr/bin/env python3
"""Performance tracking helpers for PR baseline comparison and main trend pages."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import urllib.error
import urllib.request
from urllib.parse import urlparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any


METRICS: tuple[str, ...] = (
    "total_wall_seconds",
    "terrain_load_seconds",
    "release_generation_seconds",
    "simulation_seconds",
    "validation_output_write_seconds",
    "hazard_total_seconds",
    "hazard_accumulation_seconds",
    "hazard_output_write_seconds",
    "bounds_discovery_seconds",
)

METRIC_LABELS: dict[str, str] = {
    "total_wall_seconds": "Total workflow time",
    "terrain_load_seconds": "Terrain load",
    "release_generation_seconds": "Release generation",
    "simulation_seconds": "Simulation kernel",
    "validation_output_write_seconds": "Validation output write",
    "hazard_total_seconds": "Hazard total",
    "hazard_accumulation_seconds": "Hazard accumulation",
    "hazard_output_write_seconds": "Hazard output write",
    "bounds_discovery_seconds": "Hazard bounds discovery",
}

CHART_METRICS: tuple[tuple[str, str, str], ...] = (
    ("total_wall_seconds", "Total", "#2563eb"),
    ("simulation_seconds", "Simulation", "#dc2626"),
    ("hazard_accumulation_seconds", "Hazard accumulation", "#16a34a"),
    ("validation_output_write_seconds", "Validation write", "#7c3aed"),
    ("hazard_output_write_seconds", "Hazard write", "#ea580c"),
)

BALFRIN_EFFICIENCY_RUNS: tuple[dict[str, Any], ...] = (
    {
        "task_id": "TB-448",
        "label": "regional split metrics baseline",
        "job_id": "4350232",
        "source": "docs/balfrin_regional_split_run_root_metrics_tb448.md",
        "scheduler_elapsed": "00:00:24",
        "scheduler_max_rss_kb": 5488,
        "collector_wall_seconds": 6.738646155004972,
        "memory_peak_mb": 172.921875,
        "validation_output_file_count": 130,
        "validation_output_bytes": 34_565_323,
        "hazard_output_file_count": 53,
        "hazard_output_bytes": 55_837_701,
        "conditional_curve_rows": 729_600,
        "trajectory_count": None,
    },
    {
        "task_id": "TB-557",
        "label": "bounded reduced-output probe",
        "job_id": "4366534",
        "source": "docs/balfrin_bounded_reduced_output_run_tb557.md",
        "scheduler_elapsed": "00:01:29",
        "scheduler_max_rss_kb": 390804,
        "collector_wall_seconds": 6.536354579031467,
        "memory_peak_mb": 381.64453125,
        "validation_output_file_count": 130,
        "validation_output_bytes": 34_565_316,
        "hazard_output_file_count": 57,
        "hazard_output_bytes": 31_436_405,
        "conditional_curve_rows": 729_600,
        "trajectory_count": None,
    },
    {
        "task_id": "TB-566",
        "label": "current regional split evidence",
        "job_id": "4367244",
        "source": "docs/balfrin_regional_split_run_root_metrics_tb566.md",
        "scheduler_elapsed": "00:00:24",
        "scheduler_max_rss_kb": 5512,
        "collector_wall_seconds": 5.261369686049875,
        "memory_peak_mb": 172.921875,
        "validation_output_file_count": 130,
        "validation_output_bytes": 34_565_330,
        "hazard_output_file_count": 57,
        "hazard_output_bytes": 57_670_915,
        "conditional_curve_rows": 729_600,
        "trajectory_count": None,
    },
)
BALFRIN_PROJECTION_REFERENCE = {
    "source": "scripts/summarize_balfrin_scale_readiness_matrix.py",
    "runtime_seconds": 463.84,
    "output_bytes": 102_793_652,
    "memory_peak_mb": 409.22,
    "classification": "projection_only_not_measured",
}

BALFRIN_DIAGNOSTIC_RUNS: tuple[dict[str, Any], ...] = (
    {
        "task_id": "TB-579",
        "label": "24-zone diagnostic",
        "job_id": "4368588",
        "run_id": "diagnostic_24_zone_simplified_next",
        "release_zone_count": 24,
        "source": "docs/balfrin_24_zone_diagnostic_run_tb579.md",
        "run_root": "/scratch/mch/olifu/rust_rockfall/diagnostics/diagnostic_24_zone_simplified_next",
        "git_head": "d6863e299a590f97d93cc16ba0018745b2bf6506",
        "reducer_wall_time_seconds": 4.03,
        "memory_peak_mb": 33.711,
        "output_file_count": 76,
        "output_bytes": 32_904,
        "manifest_bytes": 20_170,
    },
    {
        "task_id": "TB-581",
        "label": "24-zone repeatability A",
        "job_id": "4368592",
        "run_id": "diagnostic_24_zone_repeatability_a_tb581",
        "release_zone_count": 24,
        "source": "docs/balfrin_24_zone_repeatability_runs_tb581.md",
        "run_root": "/scratch/mch/olifu/rust_rockfall/diagnostics/diagnostic_24_zone_repeatability_a_tb581",
        "git_head": "5f9c93790cfa89855fdbbb3d30be81a31298bb50",
        "reducer_wall_time_seconds": 4.03,
        "memory_peak_mb": 34.242,
        "output_file_count": 76,
        "output_bytes": 32_922,
        "manifest_bytes": 20_218,
    },
    {
        "task_id": "TB-581",
        "label": "24-zone repeatability B",
        "job_id": "4368593",
        "run_id": "diagnostic_24_zone_repeatability_b_tb581",
        "release_zone_count": 24,
        "source": "docs/balfrin_24_zone_repeatability_runs_tb581.md",
        "run_root": "/scratch/mch/olifu/rust_rockfall/diagnostics/diagnostic_24_zone_repeatability_b_tb581",
        "git_head": "5f9c93790cfa89855fdbbb3d30be81a31298bb50",
        "reducer_wall_time_seconds": 4.03,
        "memory_peak_mb": 39.879,
        "output_file_count": 76,
        "output_bytes": 32_922,
        "manifest_bytes": 20_218,
    },
)


@dataclass(frozen=True)
class AggregateMetrics:
    values: dict[str, float]
    run_count: int
    validation_rows: int
    hazard_rows: int
    trajectory_count: int
    impact_count: int
    output_bytes: int


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    compare = subparsers.add_parser("compare-pr", help="compare current PR benchmark vs baseline")
    compare.add_argument("--summary-csv", type=Path, required=True)
    compare.add_argument("--baseline-url", required=True)
    compare.add_argument("--sha", required=True)
    compare.add_argument("--output-json", type=Path, required=True)
    compare.add_argument("--output-markdown", type=Path, required=True)

    record = subparsers.add_parser("record-main", help="append main benchmark to history and chart")
    record.add_argument("--summary-csv", type=Path, required=True)
    record.add_argument("--history-url", required=True)
    record.add_argument("--commit-sha", required=True)
    record.add_argument("--commit-date", required=True)
    record.add_argument("--history-out", type=Path, required=True)
    record.add_argument("--latest-out", type=Path, required=True)
    record.add_argument("--chart-out", type=Path, required=True)
    record.add_argument("--index-out", type=Path, required=True)
    record.add_argument("--site-index-out", type=Path, default=None)
    record.add_argument("--max-points", type=int, default=180)

    balfrin = subparsers.add_parser("balfrin-efficiency", help="compare measured Balfrin runs with CI kept separate")
    balfrin.add_argument("--summary-csv", type=Path, default=None)
    balfrin.add_argument("--output-json", type=Path, required=True)
    balfrin.add_argument("--output-markdown", type=Path, required=True)

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.command == "compare-pr":
        return compare_pr(args)
    if args.command == "record-main":
        return record_main(args)
    if args.command == "balfrin-efficiency":
        return balfrin_efficiency(args)
    raise ValueError(f"unsupported command: {args.command}")


def balfrin_efficiency(args: argparse.Namespace) -> int:
    report = build_balfrin_efficiency_report(summary_csv=args.summary_csv)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.output_markdown.parent.mkdir(parents=True, exist_ok=True)
    args.output_markdown.write_text(render_balfrin_efficiency_markdown(report), encoding="utf-8")
    return 0


def build_balfrin_efficiency_report(summary_csv: Path | None = None) -> dict[str, Any]:
    runs = [normalize_balfrin_run(row) for row in BALFRIN_EFFICIENCY_RUNS]
    current = next(row for row in runs if row["task_id"] == "TB-566")
    historical = [row for row in runs if row["task_id"] != current["task_id"]]
    ci_section: dict[str, Any]
    if summary_csv is not None:
        aggregate = aggregate_summary_csv(summary_csv)
        ci_section = {
            "status": "measured_ci_standard_profile",
            "summary_csv": str(summary_csv),
            "metrics": aggregate.values,
            "run_count": aggregate.run_count,
            "trajectory_count": aggregate.trajectory_count,
            "impact_count": aggregate.impact_count,
            "output_bytes": aggregate.output_bytes,
        }
    else:
        ci_section = {
            "status": "not_supplied",
            "summary_csv": None,
            "metrics": {},
            "run_count": 0,
            "trajectory_count": None,
            "impact_count": None,
            "output_bytes": None,
        }
    projection = build_projection_delta(current)
    return {
        "schema_version": "balfrin_efficiency_comparison_v1",
        "comparison_status": "measured_current_with_separate_ci_context",
        "current_task_id": current["task_id"],
        "current_job_id": current["job_id"],
        "current_run": current,
        "historical_balfrin_runs": historical,
        "deltas_vs_current": [build_balfrin_delta(current=current, baseline=row) for row in historical],
        "projection_delta": projection,
        "ci_standard_profile": ci_section,
        "ci_balfrin_separation": {
            "status": "separate_contexts",
            "reason": "CI benchmark timings run on GitHub-hosted runners and are not normalized into Balfrin scheduler/runtime claims.",
        },
        "claim_boundaries": {
            "operational_claims_allowed": False,
            "physical_probability_claims_allowed": False,
            "scale_up_authorized": False,
            "benchmark_as_validation_claim_allowed": False,
        },
        "regeneration_command": (
            "PYENV_VERSION=system uv run python scripts/performance_ci_tracking.py balfrin-efficiency "
            "--summary-csv <optional_ci_summary.csv> --output-json /tmp/balfrin_efficiency.json "
            "--output-markdown /tmp/balfrin_efficiency.md"
        ),
    }


def normalize_balfrin_run(row: dict[str, Any]) -> dict[str, Any]:
    scheduler_elapsed_seconds = parse_slurm_elapsed(str(row["scheduler_elapsed"]))
    validation_bytes = int(row["validation_output_bytes"])
    hazard_bytes = int(row["hazard_output_bytes"])
    conditional_rows = int(row["conditional_curve_rows"])
    total_output_bytes = validation_bytes + hazard_bytes
    total_output_files = int(row["validation_output_file_count"]) + int(row["hazard_output_file_count"])
    return {
        **row,
        "scheduler_elapsed_seconds": scheduler_elapsed_seconds,
        "scheduler_max_rss_mb": round(float(row["scheduler_max_rss_kb"]) / 1024.0, 6),
        "total_output_file_count": total_output_files,
        "total_output_bytes": total_output_bytes,
        "collector_seconds_per_100k_conditional_rows": round(float(row["collector_wall_seconds"]) / conditional_rows * 100_000, 6),
        "scheduler_seconds_per_100k_conditional_rows": round(scheduler_elapsed_seconds / conditional_rows * 100_000, 6),
        "output_bytes_per_conditional_row": round(total_output_bytes / conditional_rows, 6),
        "trajectory_count_status": "not_recorded_in_preserved_balfrin_metrics" if row.get("trajectory_count") is None else "measured",
    }


def build_balfrin_delta(*, current: dict[str, Any], baseline: dict[str, Any]) -> dict[str, Any]:
    return {
        "baseline_task_id": baseline["task_id"],
        "baseline_job_id": baseline["job_id"],
        "scheduler_elapsed_seconds_delta": round(current["scheduler_elapsed_seconds"] - baseline["scheduler_elapsed_seconds"], 6),
        "collector_wall_seconds_delta": round(float(current["collector_wall_seconds"]) - float(baseline["collector_wall_seconds"]), 6),
        "scheduler_max_rss_mb_delta": round(float(current["scheduler_max_rss_mb"]) - float(baseline["scheduler_max_rss_mb"]), 6),
        "memory_peak_mb_delta": round(float(current["memory_peak_mb"]) - float(baseline["memory_peak_mb"]), 6),
        "validation_output_bytes_delta": int(current["validation_output_bytes"]) - int(baseline["validation_output_bytes"]),
        "hazard_output_bytes_delta": int(current["hazard_output_bytes"]) - int(baseline["hazard_output_bytes"]),
        "total_output_bytes_delta": int(current["total_output_bytes"]) - int(baseline["total_output_bytes"]),
        "validation_output_file_count_delta": int(current["validation_output_file_count"]) - int(baseline["validation_output_file_count"]),
        "hazard_output_file_count_delta": int(current["hazard_output_file_count"]) - int(baseline["hazard_output_file_count"]),
        "conditional_curve_rows_delta": int(current["conditional_curve_rows"]) - int(baseline["conditional_curve_rows"]),
    }


def build_projection_delta(current: dict[str, Any]) -> dict[str, Any]:
    projection = dict(BALFRIN_PROJECTION_REFERENCE)
    return {
        **projection,
        "scheduler_elapsed_seconds_delta": round(float(current["scheduler_elapsed_seconds"]) - float(projection["runtime_seconds"]), 6),
        "total_output_bytes_delta": int(current["total_output_bytes"]) - int(projection["output_bytes"]),
        "memory_peak_mb_delta": round(float(current["memory_peak_mb"]) - float(projection["memory_peak_mb"]), 6),
        "interpretation": "current_measured_runtime_below_projection_but_output_budget_still_blocked",
    }


def parse_slurm_elapsed(value: str) -> float:
    days = 0
    time_part = value
    if "-" in value:
        day_part, time_part = value.split("-", 1)
        days = int(day_part)
    parts = [int(part) for part in time_part.split(":")]
    if len(parts) == 3:
        hours, minutes, seconds = parts
    elif len(parts) == 2:
        hours = 0
        minutes, seconds = parts
    else:
        raise ValueError(f"unsupported Slurm elapsed value: {value}")
    return float(days * 86400 + hours * 3600 + minutes * 60 + seconds)


def compare_pr(args: argparse.Namespace) -> int:
    aggregate = aggregate_summary_csv(args.summary_csv)
    baseline_raw = read_json_url(args.baseline_url)
    baseline = baseline_raw if isinstance(baseline_raw, dict) else None
    baseline_metrics = (baseline or {}).get("metrics") or {}
    deltas = build_deltas(aggregate.values, baseline_metrics)

    output = {
        "schema_version": "performance_pr_compare_v1",
        "sha": args.sha,
        "baseline_url": args.baseline_url,
        "baseline_available": bool(baseline),
        "metrics": aggregate.values,
        "deltas": deltas,
        "run_count": aggregate.run_count,
        "validation_rows": aggregate.validation_rows,
        "hazard_rows": aggregate.hazard_rows,
        "trajectory_count": aggregate.trajectory_count,
        "impact_count": aggregate.impact_count,
        "output_bytes": aggregate.output_bytes,
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(output, indent=2), encoding="utf-8")
    args.output_markdown.parent.mkdir(parents=True, exist_ok=True)
    args.output_markdown.write_text(render_pr_markdown(output), encoding="utf-8")
    return 0


def record_main(args: argparse.Namespace) -> int:
    if args.max_points <= 0:
        raise ValueError("--max-points must be positive")
    aggregate = aggregate_summary_csv(args.summary_csv)
    history_data = read_json_url(args.history_url)
    history_rows = history_data if isinstance(history_data, list) else []
    history_rows = [row for row in history_rows if isinstance(row, dict) and row.get("sha") != args.commit_sha]

    entry = {
        "sha": args.commit_sha,
        "commit_date": args.commit_date,
        "recorded_at_utc": dt.datetime.now(dt.UTC).isoformat(),
        "metrics": aggregate.values,
        "run_count": aggregate.run_count,
        "validation_rows": aggregate.validation_rows,
        "hazard_rows": aggregate.hazard_rows,
        "trajectory_count": aggregate.trajectory_count,
        "impact_count": aggregate.impact_count,
        "output_bytes": aggregate.output_bytes,
    }
    history_rows.append(entry)
    history_rows = history_rows[-args.max_points :]

    args.history_out.parent.mkdir(parents=True, exist_ok=True)
    args.history_out.write_text(json.dumps(history_rows, indent=2), encoding="utf-8")
    args.latest_out.parent.mkdir(parents=True, exist_ok=True)
    args.latest_out.write_text(json.dumps(entry, indent=2), encoding="utf-8")
    args.chart_out.parent.mkdir(parents=True, exist_ok=True)
    args.chart_out.write_text(build_history_svg(history_rows), encoding="utf-8")
    args.index_out.parent.mkdir(parents=True, exist_ok=True)
    balfrin_diagnostic = build_balfrin_diagnostic_report()
    balfrin_json_out = args.index_out.parent / "balfrin_diagnostic.json"
    balfrin_svg_out = args.index_out.parent / "balfrin_diagnostic.svg"
    balfrin_json_out.write_text(json.dumps(balfrin_diagnostic, indent=2, sort_keys=True), encoding="utf-8")
    balfrin_svg_out.write_text(build_balfrin_diagnostic_svg(balfrin_diagnostic), encoding="utf-8")
    args.index_out.write_text(render_index_html(entry, balfrin_diagnostic=balfrin_diagnostic), encoding="utf-8")
    site_index_out = getattr(args, "site_index_out", None)
    if site_index_out is not None:
        site_index_out.parent.mkdir(parents=True, exist_ok=True)
        site_index_out.write_text(render_site_index_html(entry), encoding="utf-8")
    return 0


def aggregate_summary_csv(path: Path) -> AggregateMetrics:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError(f"{path} has no benchmark rows")

    validation_rows = [row for row in rows if row.get("stage") == "validation"]
    hazard_rows = [row for row in rows if (row.get("stage") or "").startswith("hazard_")]

    metrics = {
        "total_wall_seconds": sum_float(rows, "total_wall_seconds"),
        "terrain_load_seconds": sum_float(validation_rows, "terrain_load_seconds"),
        "release_generation_seconds": sum_float(validation_rows, "release_generation_seconds"),
        "simulation_seconds": sum_float(validation_rows, "simulation_seconds"),
        "validation_output_write_seconds": sum_float(validation_rows, "output_write_seconds"),
        "hazard_total_seconds": sum_float(hazard_rows, "total_wall_seconds"),
        "hazard_accumulation_seconds": sum_float(hazard_rows, "accumulation_seconds"),
        "hazard_output_write_seconds": sum_float(hazard_rows, "core_output_write_seconds"),
        "bounds_discovery_seconds": sum_float(hazard_rows, "bounds_discovery_seconds"),
    }

    return AggregateMetrics(
        values=metrics,
        run_count=len(rows),
        validation_rows=len(validation_rows),
        hazard_rows=len(hazard_rows),
        trajectory_count=sum_int(rows, "trajectory_count"),
        impact_count=sum_int(rows, "impact_event_count"),
        output_bytes=sum_int(rows, "output_bytes"),
    )


def render_pr_markdown(report: dict[str, Any]) -> str:
    lines = [
        "## Performance benchmark (standard profile)",
        "",
        f"- Commit: `{report['sha']}`",
        f"- Rows: `{report['run_count']}` (`validation={report['validation_rows']}`, `hazard={report['hazard_rows']}`)",
        f"- Trajectories: `{report['trajectory_count']}`",
        f"- Impact events: `{report['impact_count']}`",
        f"- Output bytes: `{report['output_bytes']}`",
        "",
    ]
    if not report.get("baseline_available"):
        lines.append(
            f"_Baseline not available from `{report['baseline_url']}` yet; showing current component timings only._"
        )
        lines.append("")

    lines.extend(
        [
            "| Component | Current s | Baseline s | Δ s | Δ % |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    deltas = report.get("deltas") or {}
    for key in METRICS:
        metric_delta = deltas.get(key) or {}
        lines.append(
            "| {label} | {current:.3f} | {baseline} | {delta} | {pct} |".format(
                label=METRIC_LABELS[key],
                current=float((report.get("metrics") or {}).get(key) or 0.0),
                baseline=fmt_optional(metric_delta.get("baseline")),
                delta=fmt_signed_optional(metric_delta.get("delta")),
                pct=fmt_signed_percent(metric_delta.get("percent")),
            )
        )
    lines.append("")
    lines.append("_Positive deltas mean slower runtime; negative deltas mean faster runtime._")
    lines.append("")
    return "\n".join(lines)


def render_index_html(latest: dict[str, Any], *, balfrin_diagnostic: dict[str, Any] | None = None) -> str:
    metrics = latest.get("metrics") or {}
    rows = "\n".join(
        f"<tr><th>{METRIC_LABELS[key]}</th><td>{float(metrics.get(key, 0.0)):.3f}</td></tr>" for key in METRICS
    )
    balfrin_section = render_balfrin_diagnostic_html_section(balfrin_diagnostic or build_balfrin_diagnostic_report())
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>rust_rockfall performance trend</title>
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 1100px; margin: 2rem auto; padding: 0 1rem; }}
    img {{ max-width: 100%; border: 1px solid #d0d7de; border-radius: 6px; }}
    table {{ border-collapse: collapse; margin-top: 1rem; }}
    th, td {{ border: 1px solid #d0d7de; padding: 0.4rem 0.6rem; text-align: right; }}
    th {{ text-align: left; background: #f6f8fa; }}
  </style>
</head>
<body>
  <h1>rust_rockfall main performance trend</h1>
  <p>Latest commit: <code>{latest.get("sha", "")}</code> at {latest.get("commit_date", "")}</p>
  <img src="main_performance.svg" alt="Main branch benchmark trend chart">
  <h2>Latest component timings (seconds)</h2>
  <table>{rows}</table>
  {balfrin_section}
</body>
</html>
"""


def render_site_index_html(latest: dict[str, Any]) -> str:
    total = float((latest.get("metrics") or {}).get("total_wall_seconds") or 0.0)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>rust_rockfall CI performance</title>
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta http-equiv="refresh" content="0; url=performance/">
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 760px; margin: 2rem auto; padding: 0 1rem; }}
    a {{ color: #0969da; }}
  </style>
</head>
<body>
  <h1>rust_rockfall CI performance</h1>
  <p>Latest main benchmark: <code>{total:.3f}s</code> at commit <code>{latest.get("sha", "")}</code>.</p>
  <p><a href="performance/">Open the performance dashboard</a>.</p>
</body>
</html>
"""


def build_history_svg(history_rows: list[dict[str, Any]]) -> str:
    width = 1080
    height = 460
    left = 68
    right = 20
    top = 28
    bottom = 72
    chart_w = width - left - right
    chart_h = height - top - bottom

    if not history_rows:
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">'
            "<text x='20' y='40' font-size='18'>No benchmark history yet.</text></svg>"
        )

    all_values = [
        float((entry.get("metrics") or {}).get(metric) or 0.0)
        for entry in history_rows
        for metric, _, _ in CHART_METRICS
    ]
    max_value = max(max(all_values), 1.0)
    n = len(history_rows)

    def x_at(index: int) -> float:
        if n == 1:
            return left + chart_w / 2.0
        return left + chart_w * (index / (n - 1))

    def y_at(value: float) -> float:
        return top + chart_h * (1.0 - min(max(value / max_value, 0.0), 1.0))

    def short_sha(entry: dict[str, Any]) -> str:
        sha = str(entry.get("sha", ""))
        return sha[:7] if sha else "unknown"

    def short_commit_date(entry: dict[str, Any]) -> str:
        commit_date = str(entry.get("commit_date", ""))
        if len(commit_date) >= 10:
            return commit_date[:10]
        return commit_date or "unknown"

    series = []
    point_markers: list[str] = []
    for metric, label, color in CHART_METRICS:
        metric_points: list[tuple[float, float, float, dict[str, Any]]] = []
        for index, entry in enumerate(history_rows):
            value = float((entry.get("metrics") or {}).get(metric) or 0.0)
            x = x_at(index)
            y = y_at(value)
            metric_points.append((x, y, value, entry))
            point_markers.append(
                "<g>"
                f"<circle cx='{x:.2f}' cy='{y:.2f}' r='2.8' fill='{color}' fill-opacity='0.2' stroke='{color}' stroke-width='1.2' />"
                f"<circle cx='{x:.2f}' cy='{y:.2f}' r='1.3' fill='{color}' />"
                f"<title>{short_sha(entry)} ({label}) · {value:.2f}s</title>"
                "</g>"
            )

        points = " ".join(f"{x:.2f},{y:.2f}" for x, y, _, _ in metric_points)
        latest = float(metric_points[-1][2])
        series.append((label, color, points, latest))

    commit_tick_indices = set(range(n))
    commit_ticks: list[str] = []
    for index in sorted(commit_tick_indices):
        row = history_rows[index]
        x = x_at(index)
        commit_label = short_sha(row)
        commit_ticks.append(
            f"<text x='{x:.2f}' y='{top + chart_h + 16:.2f}' text-anchor='middle' font-size='7' fill='#57606a' "
            f"transform='rotate(-90 {x:.2f} {top + chart_h + 16:.2f})'>{commit_label}</text>"
        )

    grid = []
    for i in range(6):
        y = top + chart_h * (i / 5.0)
        value = max_value * (1.0 - i / 5.0)
        grid.append(
            f"<line x1='{left}' y1='{y:.2f}' x2='{left + chart_w}' y2='{y:.2f}' stroke='#d0d7de' stroke-width='1' />"
        )
        grid.append(
            f"<text x='8' y='{y + 4:.2f}' font-size='11' fill='#57606a'>{value:.2f}s</text>"
        )

    polylines = [
        f"<polyline fill='none' stroke='{color}' stroke-width='2.4' points='{points}' />"
        for _, color, points, _ in series
    ]
    legend = []
    for index, (label, color, _, latest) in enumerate(series):
        lx = left + index * 190
        ly = top + chart_h + 70
        legend.append(
            f"<rect x='{lx}' y='{ly - 10}' width='12' height='12' fill='{color}' />"
            f"<text x='{lx + 18}' y='{ly}' font-size='12' fill='#24292f'>{label}: {latest:.2f}s</text>"
        )

    return "\n".join(
        [
            f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}' role='img' aria-label='main branch performance trend'>",
            "<rect x='0' y='0' width='100%' height='100%' fill='white'/>",
            f"<text x='{left}' y='16' font-size='16' font-weight='600' fill='#24292f'>rust_rockfall main benchmark trend</text>",
            *grid,
            f"<line x1='{left}' y1='{top + chart_h}' x2='{left + chart_w}' y2='{top + chart_h}' stroke='#8c959f' stroke-width='1.2' />",
            f"<line x1='{left}' y1='{top}' x2='{left}' y2='{top + chart_h}' stroke='#8c959f' stroke-width='1.2' />",
            *polylines,
            *point_markers,
            *commit_ticks,
            "<text x='{x:.2f}' y='{y:.2f}' font-size='10' fill='#57606a' text-anchor='middle'>commit</text>".format(
                x=left + chart_w / 2.0, y=top + chart_h + 52.0
            ),
            *legend,
            "</svg>",
        ]
    )


def build_balfrin_diagnostic_report() -> dict[str, Any]:
    rows = [dict(row) for row in BALFRIN_DIAGNOSTIC_RUNS]
    runtime_values = [float(row["reducer_wall_time_seconds"]) for row in rows]
    memory_values = [float(row["memory_peak_mb"]) for row in rows]
    output_values = [int(row["output_bytes"]) for row in rows]
    manifest_values = [int(row["manifest_bytes"]) for row in rows]
    return {
        "schema_version": "balfrin_diagnostic_performance_pages_v1",
        "status": "measured_diagnostic_repeatability",
        "section_type": "balfrin_diagnostic_postproc",
        "summary": (
            "Measured Balfrin single-node postproc diagnostic evidence. Kept separate from GitHub Actions CI timing trends."
        ),
        "latest_release_zone_count": 24,
        "runs": rows,
        "bounds": {
            "reducer_wall_time_seconds": bounds(runtime_values),
            "memory_peak_mb": bounds(memory_values),
            "output_bytes": bounds(output_values),
            "manifest_bytes": bounds(manifest_values),
        },
        "pages_artifacts": {
            "json": "balfrin_diagnostic.json",
            "svg": "balfrin_diagnostic.svg",
        },
        "claim_boundaries": {
            "ci_timing_context": "separate",
            "operational_claims_allowed": False,
            "physical_probability_claims_allowed": False,
            "swiss_wide_claims_allowed": False,
            "distributed_execution_claims_allowed": False,
            "non_postproc_claims_allowed": False,
        },
    }


def bounds(values: list[float] | list[int]) -> dict[str, float | int]:
    ordered = sorted(values)
    middle = len(ordered) // 2
    median = ordered[middle] if len(ordered) % 2 else (ordered[middle - 1] + ordered[middle]) / 2
    spread = ordered[-1] - ordered[0]
    return {"min": ordered[0], "median": median, "max": ordered[-1], "spread": round(float(spread), 6)}


def build_balfrin_diagnostic_svg(report: dict[str, Any]) -> str:
    rows = list(report.get("runs") or [])
    width = 760
    height = 280
    left = 70
    right = 24
    top = 34
    bottom = 58
    chart_w = width - left - right
    chart_h = height - top - bottom
    max_runtime = max([float(row.get("reducer_wall_time_seconds") or 0.0) for row in rows] + [1.0])
    max_memory = max([float(row.get("memory_peak_mb") or 0.0) for row in rows] + [1.0])

    def x_at(index: int) -> float:
        return left + chart_w / 2.0 if len(rows) == 1 else left + chart_w * (index / (len(rows) - 1))

    def y_runtime(value: float) -> float:
        return top + chart_h * (1.0 - value / max_runtime)

    def y_memory(value: float) -> float:
        return top + chart_h * (1.0 - value / max_memory)

    runtime_points = []
    memory_points = []
    markers = []
    for index, row in enumerate(rows):
        x = x_at(index)
        runtime = float(row.get("reducer_wall_time_seconds") or 0.0)
        memory = float(row.get("memory_peak_mb") or 0.0)
        runtime_points.append(f"{x:.2f},{y_runtime(runtime):.2f}")
        memory_points.append(f"{x:.2f},{y_memory(memory):.2f}")
        markers.append(
            f"<circle cx='{x:.2f}' cy='{y_runtime(runtime):.2f}' r='3' fill='#2563eb'><title>{row.get('job_id')} runtime {runtime:.2f}s</title></circle>"
        )
        markers.append(
            f"<circle cx='{x:.2f}' cy='{y_memory(memory):.2f}' r='3' fill='#16a34a'><title>{row.get('job_id')} memory {memory:.3f}MB</title></circle>"
        )
        markers.append(
            f"<text x='{x:.2f}' y='{height - 24}' text-anchor='middle' font-size='10' fill='#57606a'>{row.get('job_id')}</text>"
        )
    return "\n".join(
        [
            f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}' role='img' aria-label='Balfrin diagnostic performance'>",
            "<rect width='100%' height='100%' fill='white'/>",
            f"<text x='{left}' y='20' font-size='16' font-weight='600' fill='#24292f'>Balfrin 24-zone diagnostic performance</text>",
            f"<line x1='{left}' y1='{top + chart_h}' x2='{left + chart_w}' y2='{top + chart_h}' stroke='#8c959f'/>",
            f"<line x1='{left}' y1='{top}' x2='{left}' y2='{top + chart_h}' stroke='#8c959f'/>",
            f"<polyline fill='none' stroke='#2563eb' stroke-width='2.4' points='{' '.join(runtime_points)}'/>",
            f"<polyline fill='none' stroke='#16a34a' stroke-width='2.4' points='{' '.join(memory_points)}'/>",
            *markers,
            f"<text x='{left}' y='{height - 8}' font-size='11' fill='#2563eb'>runtime seconds</text>",
            f"<text x='{left + 140}' y='{height - 8}' font-size='11' fill='#16a34a'>memory MB (separate scale)</text>",
            "</svg>",
        ]
    )


def render_balfrin_diagnostic_html_section(report: dict[str, Any]) -> str:
    rows = "\n".join(
        "<tr>"
        f"<td>{row.get('job_id')}</td>"
        f"<td>{row.get('release_zone_count')}</td>"
        f"<td>{float(row.get('reducer_wall_time_seconds') or 0.0):.2f}</td>"
        f"<td>{float(row.get('memory_peak_mb') or 0.0):.3f}</td>"
        f"<td>{int(row.get('output_file_count') or 0)}</td>"
        f"<td>{int(row.get('output_bytes') or 0)}</td>"
        "</tr>"
        for row in report.get("runs", [])
    )
    return f"""
  <h2>Balfrin diagnostic performance</h2>
  <p>{report.get("summary", "")} These measurements do not modify the CI trend above.</p>
  <img src="balfrin_diagnostic.svg" alt="Balfrin diagnostic runtime and memory chart">
  <table>
    <tr><th>Job</th><th>Zones</th><th>Reducer s</th><th>Memory MB</th><th>Files</th><th>Bytes</th></tr>
    {rows}
  </table>
  <p><a href="balfrin_diagnostic.json">Download Balfrin diagnostic JSON</a>.</p>
"""


def render_balfrin_efficiency_markdown(report: dict[str, Any]) -> str:
    current = report["current_run"]
    lines = [
        "# Balfrin Efficiency Comparison",
        "",
        f"Status: `{report['comparison_status']}`",
        "",
        "This compares measured Balfrin scheduler/runtime evidence with historical Balfrin runs. CI benchmark data is shown separately and is not normalized into Balfrin scheduler claims.",
        "",
        "## Current Run",
        "",
        f"- Task/job: `{current['task_id']}` / `{current['job_id']}`",
        f"- Scheduler elapsed: `{current['scheduler_elapsed_seconds']:.3f}` seconds",
        f"- Collector wall time: `{float(current['collector_wall_seconds']):.3f}` seconds",
        f"- Scheduler MaxRSS: `{current['scheduler_max_rss_mb']:.3f}` MB",
        f"- Collector memory peak: `{float(current['memory_peak_mb']):.3f}` MB",
        f"- Outputs: `{current['total_output_file_count']}` files / `{current['total_output_bytes']}` bytes",
        f"- Conditional curve rows: `{current['conditional_curve_rows']}`",
        f"- Trajectory count: `{current.get('trajectory_count')}` ({current['trajectory_count_status']})",
        "",
        "## Historical Balfrin Deltas",
        "",
        "| Baseline | Scheduler Δ s | Collector Δ s | MaxRSS Δ MB | Total bytes Δ | Hazard files Δ | Conditional rows Δ |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for delta in report["deltas_vs_current"]:
        lines.append(
            "| {task} / {job} | {sched:+.3f} | {collector:+.3f} | {rss:+.3f} | {bytes_delta:+d} | {hazard_files:+d} | {rows:+d} |".format(
                task=delta["baseline_task_id"],
                job=delta["baseline_job_id"],
                sched=float(delta["scheduler_elapsed_seconds_delta"]),
                collector=float(delta["collector_wall_seconds_delta"]),
                rss=float(delta["scheduler_max_rss_mb_delta"]),
                bytes_delta=int(delta["total_output_bytes_delta"]),
                hazard_files=int(delta["hazard_output_file_count_delta"]),
                rows=int(delta["conditional_curve_rows_delta"]),
            )
        )
    projection = report["projection_delta"]
    lines.extend(
        [
            "",
            "## Projection Context",
            "",
            f"- Source: `{projection['source']}`",
            f"- Runtime delta versus projection: `{float(projection['scheduler_elapsed_seconds_delta']):+.3f}` seconds",
            f"- Output-byte delta versus projection: `{int(projection['total_output_bytes_delta']):+d}` bytes",
            f"- Memory delta versus projection: `{float(projection['memory_peak_mb_delta']):+.3f}` MB",
            f"- Interpretation: `{projection['interpretation']}`",
            "",
            "## CI Context",
            "",
        ]
    )
    ci = report["ci_standard_profile"]
    lines.append(f"- Status: `{ci['status']}`")
    if ci["status"] == "measured_ci_standard_profile":
        metrics = ci.get("metrics") or {}
        lines.extend(
            [
                f"- Summary CSV: `{ci['summary_csv']}`",
                f"- CI total wall seconds: `{float(metrics.get('total_wall_seconds') or 0.0):.3f}`",
                f"- CI trajectories: `{ci['trajectory_count']}`",
                f"- CI output bytes: `{ci['output_bytes']}`",
            ]
        )
    lines.extend(
        [
            f"- Separation: `{report['ci_balfrin_separation']['status']}`",
            "",
            "## Regeneration",
            "",
            "```bash",
            report["regeneration_command"],
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def read_json_url(url: str) -> Any:
    _assert_https_url(url)
    try:
        with urllib.request.urlopen(url, timeout=15) as response:
            content = response.read().decode("utf-8")
            return json.loads(content)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return None


def _assert_https_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError(f"performance tracking URLs must be HTTPS URLs: {url}")


def build_deltas(current: dict[str, float], baseline: dict[str, Any]) -> dict[str, dict[str, float | None]]:
    output: dict[str, dict[str, float | None]] = {}
    for key in METRICS:
        current_value = float(current.get(key) or 0.0)
        baseline_value = baseline.get(key)
        if baseline_value in (None, ""):
            output[key] = {"baseline": None, "delta": None, "percent": None}
            continue
        baseline_float = float(baseline_value)
        delta = current_value - baseline_float
        percent = (delta / baseline_float * 100.0) if baseline_float != 0.0 else None
        output[key] = {"baseline": baseline_float, "delta": delta, "percent": percent}
    return output


def sum_float(rows: list[dict[str, Any]], key: str) -> float:
    total = 0.0
    for row in rows:
        value = row.get(key)
        if value in (None, ""):
            continue
        total += float(value)
    return total


def sum_int(rows: list[dict[str, Any]], key: str) -> int:
    total = 0
    for row in rows:
        value = row.get(key)
        if value in (None, ""):
            continue
        total += int(float(value))
    return total


def fmt_optional(value: Any) -> str:
    if value is None:
        return "n/a"
    return f"{float(value):.3f}"


def fmt_signed_optional(value: Any) -> str:
    if value is None:
        return "n/a"
    return f"{float(value):+,.3f}"


def fmt_signed_percent(value: Any) -> str:
    if value is None:
        return "n/a"
    return f"{float(value):+,.2f}%"


if __name__ == "__main__":
    raise SystemExit(main())
