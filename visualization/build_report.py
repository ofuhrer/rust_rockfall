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
    ("runout_histogram", "Runout histogram"),
    ("deposition_xy", "Deposition cloud"),
)
PLOT_CAPTIONS = {
    "trajectory_xz": (
        "Vertical x-z section of the simulated trajectory. Start, impact, and final markers "
        "support visual debugging; when available, the dashed line is the terrain surface offset "
        "by the block radius, not an observed field profile."
    ),
    "trajectory_xy": (
        "Plan-view x-y trajectory. For many v0 analytic cases the y coordinate is intentionally "
        "constant, so a straight line can be the expected result rather than a plotting issue."
    ),
    "energy": (
        "Kinetic, potential, and total mechanical energy versus time. Red time markers indicate "
        "impact transitions. Use this plot to inspect conservation or dissipation trends; the "
        "numeric tolerances in the JSON report remain authoritative."
    ),
    "runout_histogram": (
        "Distribution of final horizontal runout for overlaid trajectory ensembles. This is a "
        "diagnostic summary of simulated spread, not a calibrated exceedance probability."
    ),
    "deposition_xy": (
        "Observed deposition points and simulated ensemble final positions in the local dataset "
        "coordinate system. For real-world validation cases, this plot supports qualitative review "
        "of distribution-level mismatch; it is not an operational hazard-skill score."
    ),
}
FALLBACK_MODEL_VERSION = "0.4.0"


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
        return sorted((resolve_path(path) for path in explicit_cases), key=case_sort_key)
    cases: list[Path] = []
    for pattern in STANDARD_CASE_GLOBS:
        cases.extend(ROOT.glob(pattern))
    return sorted(cases, key=case_sort_key)


def case_sort_key(path: Path) -> tuple[int, int, int, str]:
    data = load_yaml(path)
    case_id = str(data.get("case_id") or path.stem)
    level = int(data.get("level", 99))
    return (level, family_order(path, case_id), case_order(case_id), str(path))


def family_order(path: Path, case_id: str) -> int:
    text = str(path)
    if "/analytic/" in text:
        return 0
    if "/synthetic/" in text and not case_id.startswith("regime_"):
        return 1
    if case_id.startswith("regime_"):
        return 2
    if "/stochastic/" in text:
        return 3
    if "validation/cases" in text:
        return 4
    return 9


def case_order(case_id: str) -> int:
    orders = {
        "analytic_free_fall": 10,
        "analytic_projectile_motion": 20,
        "analytic_energy_conservation_no_dissipation": 30,
        "analytic_vertical_rebound": 40,
        "analytic_repeated_bounce": 50,
        "analytic_oblique_rebound_flat_plane": 60,
        "analytic_inclined_slide_stop": 70,
        "analytic_no_motion_threshold": 80,
        "analytic_rolling_incline_solid_sphere": 90,
        "analytic_rolling_resistance_stop": 100,
        "analytic_rolling_energy_monotonic": 110,
        "analytic_insufficient_static_friction_slides": 120,
        "synthetic_flat_plane_rebound": 210,
        "synthetic_inclined_plane_bounce_runout": 220,
        "synthetic_paraboloid_basin_capture": 230,
        "synthetic_step_terrain_single_drop": 240,
        "synthetic_step_terrain_multi_bounce": 250,
        "synthetic_ascii_dem_fixture": 260,
        "synthetic_clamped_dem_terrain_variation": 270,
        "synthetic_contact_roughness_energy_stability": 280,
        "synthetic_scarring_zero_baseline": 290,
        "synthetic_scarring_energy_dissipation": 300,
        "synthetic_scarring_depth_velocity_scaling": 310,
        "synthetic_scarring_depth_soil_strength_scaling": 320,
        "regime_bounce_to_slide_transition": 310,
        "regime_slide_to_stop_transition": 320,
        "regime_repeated_low_energy_impacts": 330,
        "stochastic_seeded_release_reproducibility": 410,
        "stochastic_different_seed_spread": 420,
        "stochastic_ensemble_runout_statistics": 430,
        "stochastic_contact_roughness_zero_consistency": 440,
        "stochastic_contact_roughness_reproducibility": 450,
        "stochastic_contact_roughness_ensemble_spread": 460,
        "validation_synthetic_plane_basic": 510,
        "validation_tschamut_proxy_plane": 580,
        "validation_tschamut_basic": 590,
    }
    return orders.get(case_id, 1000)


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
    model_versions = ", ".join(sorted(model_versions_in_reports(reports))) or f"v{FALLBACK_MODEL_VERSION}"
    rows = "\n".join(render_case_nav(report) for report in reports)
    sections = "\n".join(render_case_section(report, report_dir) for report in reports)
    summary = ", ".join(
        f"{escape(status_label(status))}: {count}" for status, count in sorted(status_counts.items())
    )
    plot_root_link = rel_link(plot_root, report_dir)
    plot_root_label = path_label(plot_root)

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Rockfall v0.4.0 Verification and Validation Report</title>
  <style>
    :root {{
      --bg: #f8fafc;
      --panel: #ffffff;
      --ink: #111827;
      --muted: #5f6b7a;
      --line: #d9e1ea;
      --pass: #0f7b4f;
      --fail: #b42318;
      --skip: #38546a;
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
    .intro-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 16px; margin-top: 18px; }}
    .intro-card {{ background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 16px 18px; }}
    .intro-card ul, .scope ul {{ margin: 8px 0 0 20px; padding: 0; }}
    .scope {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 14px; margin: 12px 0; }}
    .scope-box {{ border: 1px solid var(--line); border-radius: 8px; background: #fbfdff; padding: 12px; }}
    .case-head {{ display: flex; justify-content: space-between; gap: 16px; align-items: flex-start; }}
    .badge {{ display: inline-block; border-radius: 999px; padding: 3px 10px; font-size: 0.78rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.03em; }}
    .status-passed {{ color: var(--pass); background: #e8f6ef; }}
    .status-failed {{ color: var(--fail); background: #fde8e7; }}
    .status-skipped {{ color: var(--skip); background: #eef4f8; }}
    .status-missing, .status-unknown {{ color: var(--missing); background: #e9eef5; }}
    .case-skipped {{ border-left: 5px solid #9db4c5; }}
    .case-failed {{ border-left: 5px solid var(--fail); }}
    .case-passed {{ border-left: 5px solid #8bc9aa; }}
    .plots {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 14px; margin-top: 14px; }}
    .plot {{ border: 1px solid var(--line); border-radius: 8px; padding: 10px; background: #fbfdff; }}
    .plot img {{ display: block; width: 100%; height: auto; border-radius: 5px; border: 1px solid var(--line); }}
    .caption {{ color: var(--muted); font-size: 0.86rem; margin-top: 7px; }}
    .notice {{ background: #f3f7fb; border: 1px solid #cfdbe7; border-radius: 8px; color: #38546a; padding: 10px 12px; }}
    .links {{ display: flex; flex-wrap: wrap; gap: 10px; margin: 10px 0; }}
    .links a {{ background: #eef3f8; border-radius: 6px; padding: 5px 8px; }}
    .grid {{ display: grid; grid-template-columns: minmax(260px, 1fr) minmax(320px, 1.5fr); gap: 18px; }}
    @media print {{
      body {{ background: #ffffff; }}
      main {{ max-width: none; padding: 16px; }}
      .card, .intro-card, .plot, .scope-box {{ break-inside: avoid; }}
      a {{ color: inherit; text-decoration: underline; }}
    }}
    @media (max-width: 760px) {{
      main {{ padding: 22px 14px 40px; }}
      .case-head, .grid {{ display: block; }}
    }}
  </style>
</head>
<body>
<main>
  <h1>Rockfall v0.4.0 Verification and Validation Report</h1>
  <p class="lede">Local diagnostic report assembled from checked-in YAML case definitions, JSON result reports, trajectory CSVs, and PNG plots. This is a browsing aid; numerical verification and validation commands remain authoritative.</p>
  <p class="meta">Generated: {escape(generated_at)}. Model version(s): {escape(model_versions)}. Cases: {len(reports)}. Status summary: {summary or "none"}. Plot root: <a href="{plot_root_link}">{escape(plot_root_label)}</a>.</p>

  <div class="intro-grid">
    <section class="intro-card">
      <h2>How To Interpret This Report</h2>
      <ul>
        <li><strong>Passed</strong> means the current version met the case-specific numerical tolerances in the JSON diagnostics.</li>
        <li><strong>Skipped optional</strong> means required external validation data are not present locally; this is expected for public datasets that are downloaded separately.</li>
        <li>Plots are diagnostic aids for spotting unexpected trajectories, energy trends, and contact markers. The metric tables and linked JSON reports are the source of truth.</li>
        <li>Synthetic and analytic cases verify controlled behavior only. They do not demonstrate operational hazard-assessment skill.</li>
      </ul>
    </section>
    <section class="intro-card">
      <h2>Known Limitations Of v0.4.0</h2>
      <ul>
        <li>Spherical blocks only; no polyhedral shape, fragmentation, or shape-dependent terrain contact.</li>
        <li>Simplified restitution/friction contact; opt-in contact roughness is not a calibrated spatial roughness field.</li>
        <li>Opt-in scarring_contact_v1 is a minimal impact-local energy-loss diagnostic; no calibrated scarring, drag torque, terrain categories, forest interaction, fragmentation, or nonsmooth multi-contact solver is implemented.</li>
        <li>DEM support is limited to small fixtures; no production GIS or calibrated terrain-class workflow is implemented.</li>
        <li>The opt-in rotational sphere model is experimental and its rolling resistance parameter is not field-calibrated.</li>
      </ul>
    </section>
  </div>

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
    terrain = render_terrain_note(report)
    roughness = render_roughness_note(report)
    scarring = render_scarring_note(report)
    validation_scope = render_validation_scope_note(report)
    scope = render_case_scope(report)
    metrics_table = render_metrics_table(report)
    plots = render_plots_html(report, report_dir)
    expected_block = render_expected_block(expected)
    notes = render_reference_notes(references)
    warnings = render_messages(report.diagnostics, "warnings")
    failures = render_messages(report.diagnostics, "failures")

    return f"""
<section class="card case-{escape_attr(status_class(report.status))}" id="{escape_attr(report.case_id)}">
  <div class="case-head">
    <div>
      <h3>{escape(report.title)}</h3>
      <p class="meta"><code>{escape(report.case_id)}</code> · {escape(level_label(report.level))} · <a href="{rel_link(report.path, report_dir)}">case YAML</a></p>
    </div>
    <div>{status_badge(report.status)}</div>
  </div>
  <p>{escape(description)}</p>
  {terrain}
  {roughness}
  {scarring}
  {validation_scope}
  {scope}
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
    ensemble_rel = nested_path(report.data, "outputs", "ensemble_deposition_csv")
    if ensemble_rel:
        ensemble_path = ROOT / ensemble_rel
        label = "ensemble deposition CSV" if ensemble_path.exists() else "ensemble deposition CSV missing"
        links.append((label, ensemble_path))
    if not links:
        return ""
    parts = [f"<a href=\"{rel_link(path, report_dir)}\">{escape(label)}</a>" for label, path in links]
    return f"<div class=\"links\">{''.join(parts)}</div>"


def render_roughness_note(report: CaseReport) -> str:
    parameters = report.data.get("parameters", {})
    if not isinstance(parameters, dict):
        return ""
    if parameters.get("roughness_model", "none") != "stochastic_contact_v1":
        return ""
    normal = parameters.get("roughness_std_normal", 0.0)
    tangent = parameters.get("roughness_std_tangent", 0.0)
    angle = parameters.get("roughness_std_angle", 0.0)
    return (
        "<p class=\"notice\"><strong>Roughness enabled:</strong> "
        "stochastic_contact_v1 perturbs impact contact normals and dissipative contact parameters "
        f"with std normal={escape(format_value(normal))}, tangent={escape(format_value(tangent))}, "
        f"angle={escape(format_value(angle))} rad. This is an opt-in verification model, not a calibrated terrain law.</p>"
    )


def render_scarring_note(report: CaseReport) -> str:
    parameters = report.data.get("parameters", {})
    if not isinstance(parameters, dict):
        return ""
    if parameters.get("soil_interaction_model", "none") != "scarring_contact_v1":
        return ""
    strength = parameters.get("soil_strength_pa", 0.0)
    drag = parameters.get("scarring_drag_coefficient", 0.0)
    density = parameters.get("scarring_layer_density_kgpm3", 0.0)
    max_depth = parameters.get("scarring_max_depth_m")
    max_depth_text = "inferred" if max_depth is None else f"{format_value(max_depth)} m"
    return (
        "<p class=\"notice\"><strong>Scarring model enabled:</strong> "
        "scarring_contact_v1 applies an opt-in, impact-local compactable-soil energy-loss diagnostic "
        "for spherical blocks. It is not calibrated and does not add drag torque, terrain categories, "
        "or slip-dependent friction. "
        f"soil_strength={escape(format_value(strength))} Pa, Cd={escape(format_value(drag))}, "
        f"layer_density={escape(format_value(density))} kg/m3, max_depth={escape(max_depth_text)}.</p>"
    )


def render_terrain_note(report: CaseReport) -> str:
    terrain = report.data.get("terrain", {})
    if not isinstance(terrain, dict):
        return ""
    terrain_type = terrain.get("type", terrain.get("kind", "unknown"))
    details = [f"type={terrain_type}"]
    if terrain.get("path"):
        details.append(f"path={terrain.get('path')}")
    parameters = terrain.get("parameters", {})
    if isinstance(parameters, dict) and parameters:
        compact = ", ".join(f"{key}={format_value(value)}" for key, value in parameters.items())
        details.append(compact)
    note = ""
    if terrain_type in {"ascii_dem_clamped", "esri_ascii_grid_clamped"}:
        note = (
            " Queries outside the grid are clamped to the terrain boundary for this opt-in "
            "limited-patch model; this avoids edge failures but is not a substitute for a larger "
            "field DEM."
        )
    return (
        "<p class=\"notice\"><strong>Terrain:</strong> "
        f"{escape('; '.join(str(item) for item in details))}.{escape(note)}</p>"
    )


def render_validation_scope_note(report: CaseReport) -> str:
    scope = report.data.get("validation_scope", {})
    if not isinstance(scope, dict) or not scope:
        return ""
    scope_type = scope.get("type", "limited")
    note = scope.get("note", "")
    return (
        "<p class=\"notice\"><strong>Real-world validation "
        f"({escape(str(scope_type))}):</strong> {escape(str(note))} "
        "This comparison is intended to expose model plausibility and deficiencies, not to certify "
        "field accuracy or operational hazard validity.</p>"
    )


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
            caption = PLOT_CAPTIONS.get(kind, "")
            cards.append(
                "<div class=\"plot\">"
                f"<h4>{escape(label)}</h4>"
                f"<a href=\"{rel_link(path, report_dir)}\"><img alt=\"{escape_attr(label)} for {escape_attr(report.case_id)}\" src=\"{rel_link(path, report_dir)}\"></a>"
                f"<p class=\"caption\">{escape(caption)}</p>"
                "</div>"
            )
    if not cards:
        return f"<p class=\"notice\">{escape(no_plot_explanation(report))}</p>"
    return f"<div class=\"plots\">{''.join(cards)}</div>"


def render_case_scope(report: CaseReport) -> str:
    verifies, not_verified = case_scope(report)
    verifies_items = "".join(f"<li>{escape(item)}</li>" for item in verifies)
    not_verified_items = "".join(f"<li>{escape(item)}</li>" for item in not_verified)
    return (
        "<div class=\"scope\">"
        f"<div class=\"scope-box\"><h4>What This Checks</h4><ul>{verifies_items}</ul></div>"
        f"<div class=\"scope-box\"><h4>What This Does Not Check</h4><ul>{not_verified_items}</ul></div>"
        "</div>"
    )


def case_scope(report: CaseReport) -> tuple[list[str], list[str]]:
    explicit = report.data.get("report", {})
    if isinstance(explicit, dict):
        verifies = list_of_strings(explicit.get("verifies"))
        not_verified = list_of_strings(explicit.get("does_not_verify"))
        if verifies and not_verified:
            return verifies, not_verified

    description = str(report.data.get("description") or "").strip()
    verifies = [description] if description else [f"Configured {level_label(report.level).lower()} behavior for this case."]
    references = report.data.get("references", {})
    if isinstance(references, dict):
        notes = list_of_strings(references.get("notes"))
        verifies.extend(notes[:1])

    level_defaults = {
        "0": [
            "Field-scale runout, lateral dispersion, terrain roughness, block-shape effects, or operational hazard performance.",
        ],
        "1": [
            "Real terrain validity, calibrated material parameters, vegetation, fragmentation, or operational hazard performance.",
        ],
        "2": [
            "Complete rockfall regime physics beyond the contact states and diagnostics exposed by the current v0 model.",
        ],
        "3": [
            "Probability calibration or real-world exceedance skill; these cases check deterministic stochastic plumbing and summary statistics.",
        ],
        "4": [
            "Operational hazard skill; synthetic benchmarks are controlled regression cases, not field validation.",
        ],
        "5": [
            "Operational hazard validity. v0 real-data cases are scaffolds or limited smoke tests until public observations are downloaded, processed, and independently reviewed.",
        ],
    }
    return verifies, level_defaults.get(report.level, ["Behavior outside the case definition and configured metrics."])


def list_of_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    return []


def no_plot_explanation(report: CaseReport) -> str:
    if report.status == "skipped":
        return (
            "No plots are expected for this optional skipped case because required external validation "
            "data are not present locally. Download and preprocess the public dataset before rendering plots."
        )
    if report.level == "3" and not nested_path(report.data, "outputs", "trajectory_csv"):
        return (
            "This stochastic case is metric-only for the current model: it checks seeded reproducibility or ensemble "
            "summary statistics without writing a per-trajectory CSV, so there is no trajectory plot to render."
        )
    if report.trajectory_path and not report.trajectory_path.exists():
        return "No plots are available because the trajectory CSV has not been generated for this case."
    return "No PNG plots are available for this case; review the linked diagnostics JSON and case YAML."


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


def model_versions_in_reports(reports: list[CaseReport]) -> set[str]:
    versions = set()
    for report in reports:
        if report.diagnostics and report.diagnostics.get("model_version"):
            versions.add(f"v{report.diagnostics['model_version']}")
    return versions


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
    safe = escape(status_label(status))
    cls = "status-skipped" if status == "skipped" else f"status-{safe}"
    return f"<span class=\"badge {cls}\">{safe}</span>"


def status_label(status: str) -> str:
    return "skipped optional" if status == "skipped" else status


def status_class(status: str) -> str:
    if status == "skipped":
        return "skipped"
    if status == "failed":
        return "failed"
    if status == "passed":
        return "passed"
    return "unknown"


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
