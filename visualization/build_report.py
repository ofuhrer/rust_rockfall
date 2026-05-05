#!/usr/bin/env python3
"""Build a local HTML report for standard v0 verification/validation cases.

The report is a consumer of existing YAML case definitions, JSON diagnostics,
CSV trajectories, and PNG plots. It does not run the Rust simulation unless the
caller has already generated those outputs. Use --render-plots to refresh PNGs
from existing CSV/JSON results.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT_DIR = ROOT / "visualization" / "reports" / "standard_v0"
DEFAULT_PLOT_ROOT = ROOT / "visualization" / "output" / "standard_cases"
STANDARD_CASE_GLOBS = (
    "verification/analytic/*.yaml",
    "verification/synthetic/*.yaml",
    "verification/stochastic/*.yaml",
    "validation/cases/*.yaml",
)
PLOT_KINDS = (
    ("trajectory_xz", "Trajectory x-z"),
    ("trajectory_xy", "Plan view"),
    ("energy", "Energy"),
)


@dataclass
class CaseReport:
    path: Path
    data: dict[str, Any]
    diagnostics: dict[str, Any] | None
    diagnostics_path: Path | None
    trajectory_path: Path | None
    plot_paths: dict[str, Path]

    @property
    def case_id(self) -> str:
        return str(self.data.get("case_id") or self.path.stem)

    @property
    def title(self) -> str:
        return str(self.data.get("title") or self.case_id)

    @property
    def level(self) -> str:
        return str(self.data.get("level", "unknown"))

    @property
    def status(self) -> str:
        if self.diagnostics is None:
            if self.missing_observation_paths():
                return "skipped"
            return "missing"
        return str(self.diagnostics.get("status") or "unknown").lower()

    def missing_observation_paths(self) -> list[Path]:
        observations = self.data.get("observations", {})
        if not isinstance(observations, dict):
            return []
        missing = []
        for value in observations.values():
            if isinstance(value, str):
                path = ROOT / value
                if not path.exists():
                    missing.append(path)
        return missing


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--report-dir",
        type=Path,
        default=DEFAULT_REPORT_DIR,
        help="directory receiving index.html and report_manifest.json",
    )
    parser.add_argument(
        "--plot-root",
        type=Path,
        default=DEFAULT_PLOT_ROOT,
        help="directory containing standard case plot subdirectories",
    )
    parser.add_argument(
        "--case",
        action="append",
        type=Path,
        default=[],
        help="specific YAML case to include; repeatable. Defaults to standard v0 cases.",
    )
    parser.add_argument(
        "--render-plots",
        action="store_true",
        help="refresh PNG plots for cases that have an existing trajectory CSV",
    )
    args = parser.parse_args()

    cases = discover_cases(args.case)
    if args.render_plots:
        render_plots(cases, args.plot_root)

    reports = [load_case_report(path, args.plot_root) for path in cases]
    args.report_dir.mkdir(parents=True, exist_ok=True)
    html_text = render_html(reports, args.report_dir, args.plot_root)
    manifest = render_manifest(reports, args.report_dir)

    (args.report_dir / "index.html").write_text(html_text, encoding="utf-8")
    (args.report_dir / "report_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"wrote HTML report to {args.report_dir / 'index.html'}")
    return 0


def discover_cases(explicit_cases: list[Path]) -> list[Path]:
    if explicit_cases:
        return sorted(resolve_path(path) for path in explicit_cases)
    cases: list[Path] = []
    for pattern in STANDARD_CASE_GLOBS:
        cases.extend(ROOT.glob(pattern))
    return sorted(cases)


def render_plots(case_paths: list[Path], plot_root: Path) -> None:
    plot_script = ROOT / "visualization" / "plot_case.py"
    rendered = 0
    skipped = 0
    for case_path in case_paths:
        data = load_yaml(case_path)
        case_id = str(data.get("case_id") or case_path.stem)
        trajectory = nested_path(data, "outputs", "trajectory_csv")
        if not trajectory or not (ROOT / trajectory).exists():
            skipped += 1
            continue
        output_dir = plot_root / case_id
        command = [
            sys.executable,
            str(plot_script),
            "--case",
            str(case_path),
            "--output-dir",
            str(output_dir),
            "--prefix",
            case_id,
        ]
        subprocess.run(command, check=True)
        rendered += 1
    print(f"rendered plots for {rendered} cases; skipped {skipped} without trajectory CSV")


def load_case_report(path: Path, plot_root: Path) -> CaseReport:
    data = load_yaml(path)
    diagnostics_rel = nested_path(data, "outputs", "diagnostics_json")
    trajectory_rel = nested_path(data, "outputs", "trajectory_csv")
    diagnostics_path = ROOT / diagnostics_rel if diagnostics_rel else None
    trajectory_path = ROOT / trajectory_rel if trajectory_rel else None
    diagnostics = read_json(diagnostics_path) if diagnostics_path and diagnostics_path.exists() else None
    case_id = str(data.get("case_id") or path.stem)
    plot_paths = {
        kind: plot_root / case_id / f"{case_id}_{kind}.png"
        for kind, _label in PLOT_KINDS
    }
    return CaseReport(
        path=path,
        data=data,
        diagnostics=diagnostics,
        diagnostics_path=diagnostics_path,
        trajectory_path=trajectory_path,
        plot_paths=plot_paths,
    )


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml  # type: ignore
    except ImportError as exc:
        raise SystemExit("PyYAML is required. Install with `python3 -m pip install PyYAML`.") from exc
    with path.open(encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}
    if not isinstance(data, dict):
        raise SystemExit(f"case file must contain a mapping: {path}")
    return data


def read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as file:
        data = json.load(file)
    return data if isinstance(data, dict) else {}


def render_html(reports: list[CaseReport], report_dir: Path, plot_root: Path) -> str:
    status_counts: dict[str, int] = {}
    for report in reports:
        status_counts[report.status] = status_counts.get(report.status, 0) + 1

    generated_at = time.strftime("%Y-%m-%d %H:%M:%S %Z")
    rows = "\n".join(render_case_nav(report) for report in reports)
    sections = "\n".join(render_case_section(report, report_dir) for report in reports)
    summary = ", ".join(
        f"{escape(status)}: {count}" for status, count in sorted(status_counts.items())
    )
    plot_root_link = rel_link(plot_root, report_dir)
    plot_root_label = path_label(plot_root)

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Rockfall v0 Verification and Validation Report</title>
  <style>
    :root {{
      --bg: #f8fafc;
      --panel: #ffffff;
      --ink: #111827;
      --muted: #5f6b7a;
      --line: #d9e1ea;
      --pass: #0f7b4f;
      --fail: #b42318;
      --skip: #8a5a00;
      --missing: #475569;
    }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      line-height: 1.45;
    }}
    main {{ max-width: 1180px; margin: 0 auto; padding: 32px 24px 56px; }}
    h1 {{ margin: 0 0 8px; font-size: 2rem; }}
    h2 {{ margin: 32px 0 12px; font-size: 1.35rem; }}
    h3 {{ margin: 0; font-size: 1.05rem; }}
    p {{ margin: 8px 0; }}
    a {{ color: #155eef; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 0.9rem; }}
    th, td {{ border-bottom: 1px solid var(--line); padding: 8px 10px; text-align: left; vertical-align: top; }}
    th {{ background: #eef3f8; color: #27364a; font-weight: 650; }}
    code, pre {{ font-family: "SFMono-Regular", Consolas, monospace; font-size: 0.85rem; }}
    pre {{ white-space: pre-wrap; background: #f3f6fa; border: 1px solid var(--line); padding: 10px; border-radius: 6px; }}
    .lede {{ color: var(--muted); max-width: 900px; }}
    .meta {{ color: var(--muted); font-size: 0.92rem; }}
    .card {{ background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 18px; margin: 18px 0; }}
    .case-head {{ display: flex; justify-content: space-between; gap: 16px; align-items: flex-start; }}
    .badge {{ display: inline-block; border-radius: 999px; padding: 3px 10px; font-size: 0.78rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.03em; }}
    .status-passed {{ color: var(--pass); background: #e8f6ef; }}
    .status-failed {{ color: var(--fail); background: #fde8e7; }}
    .status-skipped {{ color: var(--skip); background: #fff3cf; }}
    .status-missing, .status-unknown {{ color: var(--missing); background: #e9eef5; }}
    .plots {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 14px; margin-top: 14px; }}
    .plot {{ border: 1px solid var(--line); border-radius: 8px; padding: 10px; background: #fbfdff; }}
    .plot img {{ display: block; width: 100%; height: auto; border-radius: 5px; border: 1px solid var(--line); }}
    .links {{ display: flex; flex-wrap: wrap; gap: 10px; margin: 10px 0; }}
    .links a {{ background: #eef3f8; border-radius: 6px; padding: 5px 8px; }}
    .grid {{ display: grid; grid-template-columns: minmax(260px, 1fr) minmax(320px, 1.5fr); gap: 18px; }}
    @media (max-width: 760px) {{
      main {{ padding: 22px 14px 40px; }}
      .case-head, .grid {{ display: block; }}
    }}
  </style>
</head>
<body>
<main>
  <h1>Rockfall v0 Verification and Validation Report</h1>
  <p class="lede">Local diagnostic report assembled from checked-in YAML case definitions, JSON result reports, trajectory CSVs, and PNG plots. This is a browsing aid; numerical verification and validation commands remain authoritative.</p>
  <p class="meta">Generated: {escape(generated_at)}. Cases: {len(reports)}. Status summary: {summary or "none"}. Plot root: <a href="{plot_root_link}">{escape(plot_root_label)}</a>.</p>

  <h2>Case Index</h2>
  <table>
    <thead><tr><th>Case</th><th>Level</th><th>Status</th><th>Metrics</th></tr></thead>
    <tbody>
      {rows}
    </tbody>
  </table>

  <h2>Case Details</h2>
  {sections}
</main>
</body>
</html>
"""


def render_case_nav(report: CaseReport) -> str:
    metrics = report.diagnostics.get("metrics", {}) if report.diagnostics else {}
    metric_names = ", ".join(sorted(metrics.keys())) if metrics else "none"
    return (
        "<tr>"
        f"<td><a href=\"#{escape_attr(report.case_id)}\">{escape(report.title)}</a><br><code>{escape(report.case_id)}</code></td>"
        f"<td>{escape(level_label(report.level))}</td>"
        f"<td>{status_badge(report.status)}</td>"
        f"<td>{escape(metric_names)}</td>"
        "</tr>"
    )


def render_case_section(report: CaseReport, report_dir: Path) -> str:
    expected = report.data.get("expected", {})
    references = report.data.get("references", {})
    description = str(report.data.get("description") or "")
    links = render_links(report, report_dir)
    metrics_table = render_metrics_table(report)
    plots = render_plots_html(report, report_dir)
    expected_block = render_expected_block(expected)
    notes = render_reference_notes(references)
    warnings = render_messages(report.diagnostics, "warnings")
    failures = render_messages(report.diagnostics, "failures")

    return f"""
<section class="card" id="{escape_attr(report.case_id)}">
  <div class="case-head">
    <div>
      <h3>{escape(report.title)}</h3>
      <p class="meta"><code>{escape(report.case_id)}</code> · {escape(level_label(report.level))} · <a href="{rel_link(report.path, report_dir)}">case YAML</a></p>
    </div>
    <div>{status_badge(report.status)}</div>
  </div>
  <p>{escape(description)}</p>
  {links}
  <div class="grid">
    <div>
      <h4>Expected Behavior</h4>
      {expected_block}
      {notes}
      {warnings}
      {failures}
    </div>
    <div>
      <h4>Metrics</h4>
      {metrics_table}
    </div>
  </div>
  {plots}
</section>
"""


def render_links(report: CaseReport, report_dir: Path) -> str:
    links = []
    if report.diagnostics_path:
        label = "diagnostics JSON" if report.diagnostics_path.exists() else "diagnostics JSON missing"
        links.append((label, report.diagnostics_path))
    if report.trajectory_path:
        label = "trajectory CSV" if report.trajectory_path.exists() else "trajectory CSV missing"
        links.append((label, report.trajectory_path))
    if not links:
        return ""
    parts = [f"<a href=\"{rel_link(path, report_dir)}\">{escape(label)}</a>" for label, path in links]
    return f"<div class=\"links\">{''.join(parts)}</div>"


def render_metrics_table(report: CaseReport) -> str:
    diagnostics = report.diagnostics or {}
    metrics = diagnostics.get("metrics", {}) if isinstance(diagnostics.get("metrics", {}), dict) else {}
    tolerances = diagnostics.get("tolerances", {}) if isinstance(diagnostics.get("tolerances", {}), dict) else {}
    expected = report.data.get("expected", {}) if isinstance(report.data.get("expected", {}), dict) else {}
    expected_metrics = expected.get("metrics", [])
    if not isinstance(expected_metrics, list):
        expected_metrics = []
    minimums = expected.get("minimums", {}) if isinstance(expected.get("minimums", {}), dict) else {}
    maximums = expected.get("maximums", {}) if isinstance(expected.get("maximums", {}), dict) else {}
    case_tolerances = expected.get("tolerances", {}) if isinstance(expected.get("tolerances", {}), dict) else {}
    metric_names = sorted(
        set(str(name) for name in expected_metrics)
        | set(metrics.keys())
        | set(tolerances.keys())
        | set(case_tolerances.keys())
        | set(minimums.keys())
        | set(maximums.keys())
    )
    if not metric_names:
        return "<p class=\"meta\">No numerical metrics reported.</p>"

    rows = []
    for name in metric_names:
        tolerance = tolerances.get(name, case_tolerances.get(name, ""))
        rows.append(
            "<tr>"
            f"<td><code>{escape(name)}</code></td>"
            f"<td>{escape(format_value(metrics.get(name, '')))}</td>"
            f"<td>{escape(format_value(tolerance))}</td>"
            f"<td>{escape(format_value(minimums.get(name, '')))}</td>"
            f"<td>{escape(format_value(maximums.get(name, '')))}</td>"
            "</tr>"
        )
    return (
        "<table><thead><tr><th>Metric</th><th>Value</th><th>Tolerance</th><th>Min</th><th>Max</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>"
    )


def render_plots_html(report: CaseReport, report_dir: Path) -> str:
    cards = []
    for kind, label in PLOT_KINDS:
        path = report.plot_paths[kind]
        if path.exists():
            cards.append(
                "<div class=\"plot\">"
                f"<h4>{escape(label)}</h4>"
                f"<a href=\"{rel_link(path, report_dir)}\"><img alt=\"{escape_attr(label)} for {escape_attr(report.case_id)}\" src=\"{rel_link(path, report_dir)}\"></a>"
                "</div>"
            )
    if not cards:
        return "<p class=\"meta\">No PNG plots available for this case.</p>"
    return f"<div class=\"plots\">{''.join(cards)}</div>"


def render_expected_block(expected: Any) -> str:
    if not isinstance(expected, dict) or not expected:
        return "<p class=\"meta\">No expected behavior block in case YAML.</p>"
    return f"<pre>{escape(json.dumps(expected, indent=2, sort_keys=True))}</pre>"


def render_reference_notes(references: Any) -> str:
    if not isinstance(references, dict):
        return ""
    notes = references.get("notes", [])
    if not isinstance(notes, list) or not notes:
        return ""
    items = "".join(f"<li>{escape(str(note))}</li>" for note in notes)
    return f"<h4>Notes</h4><ul>{items}</ul>"


def render_messages(diagnostics: dict[str, Any] | None, key: str) -> str:
    if not diagnostics:
        return ""
    values = diagnostics.get(key, [])
    if not isinstance(values, list) or not values:
        return ""
    items = "".join(f"<li>{escape(str(value))}</li>" for value in values)
    return f"<h4>{escape(key.title())}</h4><ul>{items}</ul>"


def render_manifest(reports: list[CaseReport], report_dir: Path) -> dict[str, Any]:
    return {
        "generated_unix_s": int(time.time()),
        "case_count": len(reports),
        "cases": [
            {
                "case_id": report.case_id,
                "title": report.title,
                "level": report.level,
                "status": report.status,
                "case_yaml": path_if_exists_or_declared(report.path, report_dir),
                "diagnostics_json": path_if_exists_or_declared(report.diagnostics_path, report_dir),
                "trajectory_csv": path_if_exists_or_declared(report.trajectory_path, report_dir),
                "plots": {
                    kind: path_if_exists_or_declared(path, report_dir)
                    for kind, path in report.plot_paths.items()
                    if path.exists()
                },
            }
            for report in reports
        ],
    }


def path_if_exists_or_declared(path: Path | None, report_dir: Path) -> str | None:
    if path is None:
        return None
    return os.path.relpath(path, report_dir)


def nested_path(data: dict[str, Any], *keys: str) -> str | None:
    current: Any = data
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
    return str(current) if current else None


def resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def rel_link(path: Path, report_dir: Path) -> str:
    return escape_attr(os.path.relpath(path, report_dir))


def path_label(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def status_badge(status: str) -> str:
    safe = escape(status)
    cls = "status-skipped" if status == "skipped" else f"status-{safe}"
    return f"<span class=\"badge {cls}\">{safe}</span>"


def level_label(level: str) -> str:
    labels = {
        "0": "Level 0 - analytic",
        "1": "Level 1 - idealized terrain",
        "2": "Level 2 - motion regime",
        "3": "Level 3 - stochastic",
        "4": "Level 4 - synthetic benchmark",
        "5": "Level 5 - validation",
    }
    return labels.get(level, f"Level {level}")


def format_value(value: Any) -> str:
    if value == "":
        return ""
    if isinstance(value, float):
        return f"{value:.6g}"
    if isinstance(value, (dict, list)):
        return json.dumps(value, sort_keys=True)
    return str(value)


def escape(value: str) -> str:
    return html.escape(value, quote=False)


def escape_attr(value: str) -> str:
    return html.escape(value, quote=True)


if __name__ == "__main__":
    raise SystemExit(main())
