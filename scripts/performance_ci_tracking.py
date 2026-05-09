#!/usr/bin/env python3
"""Performance tracking helpers for PR baseline comparison and main trend pages."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import urllib.error
import urllib.request
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
    record.add_argument("--max-points", type=int, default=180)

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.command == "compare-pr":
        return compare_pr(args)
    if args.command == "record-main":
        return record_main(args)
    raise ValueError(f"unsupported command: {args.command}")


def compare_pr(args: argparse.Namespace) -> int:
    aggregate = aggregate_summary_csv(args.summary_csv)
    baseline = read_json_url(args.baseline_url)
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
    args.index_out.write_text(render_index_html(entry), encoding="utf-8")
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


def render_index_html(latest: dict[str, Any]) -> str:
    metrics = latest.get("metrics") or {}
    rows = "\n".join(
        f"<tr><th>{METRIC_LABELS[key]}</th><td>{float(metrics.get(key, 0.0)):.3f}</td></tr>" for key in METRICS
    )
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
</body>
</html>
"""


def build_history_svg(history_rows: list[dict[str, Any]]) -> str:
    width = 1080
    height = 360
    left = 68
    right = 20
    top = 28
    bottom = 52
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

    series = []
    for metric, label, color in CHART_METRICS:
        points = " ".join(
            f"{x_at(index):.2f},{y_at(float((entry.get('metrics') or {}).get(metric) or 0.0)):.2f}"
            for index, entry in enumerate(history_rows)
        )
        latest = float((history_rows[-1].get("metrics") or {}).get(metric) or 0.0)
        series.append((label, color, points, latest))

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
        ly = height - 20
        legend.append(
            f"<rect x='{lx}' y='{ly - 10}' width='12' height='12' fill='{color}' />"
            f"<text x='{lx + 18}' y='{ly}' font-size='12' fill='#24292f'>{label}: {latest:.2f}s</text>"
        )

    first_sha = str(history_rows[0].get("sha", ""))[:7]
    last_sha = str(history_rows[-1].get("sha", ""))[:7]

    return "\n".join(
        [
            f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}' role='img' aria-label='main branch performance trend'>",
            "<rect x='0' y='0' width='100%' height='100%' fill='white'/>",
            f"<text x='{left}' y='16' font-size='16' font-weight='600' fill='#24292f'>rust_rockfall main benchmark trend</text>",
            *grid,
            f"<line x1='{left}' y1='{top + chart_h}' x2='{left + chart_w}' y2='{top + chart_h}' stroke='#8c959f' stroke-width='1.2' />",
            f"<line x1='{left}' y1='{top}' x2='{left}' y2='{top + chart_h}' stroke='#8c959f' stroke-width='1.2' />",
            *polylines,
            f"<text x='{left}' y='{height - 34}' font-size='11' fill='#57606a'>oldest: {first_sha}</text>",
            f"<text x='{left + chart_w - 90}' y='{height - 34}' font-size='11' fill='#57606a'>latest: {last_sha}</text>",
            *legend,
            "</svg>",
        ]
    )


def read_json_url(url: str) -> Any:
    try:
        with urllib.request.urlopen(url, timeout=15) as response:
            content = response.read().decode("utf-8")
            return json.loads(content)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return None


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
