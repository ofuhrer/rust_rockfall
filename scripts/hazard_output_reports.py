"""HTML and text report helpers for hazard-layer outputs."""

from __future__ import annotations

import html
from pathlib import Path
from typing import Any

from scripts.hazard_output_writers import write_file_text


def write_html_report(
    path: Path,
    case: dict[str, Any],
    metadata: dict[str, Any],
    layers: list[Any],
    plot_paths: dict[str, str],
    prefix: str,
    output_file_metadata: dict[Path, dict[str, Any]],
    output_write_kind_seconds: dict[str, float],
    output_write_kind_bytes: dict[str, int],
) -> None:
    title = str(case.get("title") or metadata.get("case_id") or "Hazard Layers")
    rows = []
    geotiff_enabled = bool((metadata.get("raster_exports") or {}).get("geotiff"))
    for layer in layers:
        summary = next(
            (entry.get("summary", {}) for entry in metadata.get("layers", []) if entry.get("key") == layer.key),
            {},
        )
        files = (
            f"<a href=\"{prefix}_{layer.key}.csv\">CSV grid</a> | "
            f"<a href=\"{prefix}_{layer.key}.asc\">ASCII grid</a>"
        )
        if geotiff_enabled:
            files += f" | <a href=\"{prefix}_{layer.key}.tif\">GeoTIFF</a>"
        rows.append(
            "<tr>"
            f"<td>{html.escape(layer.title)}</td>"
            f"<td>{html.escape(layer.units)}</td>"
            f"<td>{files}</td>"
            f"<td>{html.escape(layer.note)}</td>"
            f"<td>{html.escape(format_summary(summary))}</td>"
            "</tr>"
        )
    plots = []
    for layer in layers:
        plot = plot_paths.get(layer.key)
        if plot:
            plots.append(
                f"<figure><img src=\"{html.escape(plot)}\" alt=\"{html.escape(layer.title)}\">"
                f"<figcaption>{html.escape(layer.title)} ({html.escape(layer.units)}). {html.escape(layer.note)}</figcaption></figure>"
            )
    warnings = "".join(f"<li>{html.escape(warning)}</li>" for warning in metadata.get("warnings", []))
    limitations = "".join(f"<li>{html.escape(item)}</li>" for item in metadata.get("limitations", []))
    content = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{html.escape(title)} Hazard Layers</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 2rem; line-height: 1.45; color: #172033; }}
    h1, h2 {{ line-height: 1.15; }}
    .badge {{ display: inline-block; padding: 0.15rem 0.45rem; border-radius: 0.35rem; background: #e8f0fe; color: #174ea6; font-size: 0.86rem; }}
    table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
    th, td {{ border: 1px solid #d8dee9; padding: 0.5rem; text-align: left; vertical-align: top; }}
    th {{ background: #f5f7fb; }}
    img {{ max-width: 920px; width: 100%; border: 1px solid #d8dee9; }}
    figure {{ margin: 1.5rem 0; }}
    figcaption {{ color: #4b5563; font-size: 0.92rem; margin-top: 0.35rem; }}
    code {{ background: #f5f7fb; padding: 0.1rem 0.25rem; }}
  </style>
</head>
<body>
  <h1>{html.escape(title)} Hazard Layers</h1>
  <p><span class="badge">research hazard layer</span> <span class="badge">not operational risk</span></p>
  <p>This report converts existing rockfall simulation outputs into first-pass spatial hazard layers. It does not add physics, does not include exposure or vulnerability, and must not be interpreted as an operational Swiss hazard or risk map.</p>
  <h2>How to Read Hazard Layers</h2>
  <p>Probability and density layers are normalized diagnostic rasters. A value near 1 means all supplied samples for that layer occupied the cell; a value near 0 means few or none did. Maximum-energy and maximum-jump-height layers record the largest sampled value in each cell, not an expected value or design value. Exceedance layers count each trajectory at most once per cell and threshold.</p>
  <ul>
    <li><strong>Reach probability</strong>: cells touched by supplied trajectory CSVs. With <code>outputs.ensemble_trajectories_dir</code> it represents the full written ensemble; with one representative trajectory it is only a 0/1 path mask.</li>
    <li><strong>Deposition density</strong>: final-position density from ensemble deposition points. Weighted deposition density is normalized by filtered sampling weight when <code>hazard_probability</code> is configured.</li>
    <li><strong>Maximum kinetic energy</strong>: largest kinetic energy sampled in each cell from supplied trajectories.</li>
    <li><strong>Maximum jump height</strong>: largest sampled height above terrain plus block radius where terrain metadata can be evaluated.</li>
    <li><strong>Exceedance probability</strong>: fraction of supplied trajectories that exceeded a configured kinetic-energy, jump-height, or velocity threshold in each cell.</li>
    <li><strong>Significant impact density</strong>: normalized locations of impact events above the configured normal-speed threshold.</li>
  </ul>
  <h2>Inputs</h2>
  <ul>
    <li>Case: <code>{html.escape(str(metadata.get("case_id") or "unspecified"))}</code></li>
    <li>Model version: <code>{html.escape(str(metadata.get("model_version") or "unknown"))}</code></li>
    <li>Trajectory CSV count: {metadata["inputs"]["trajectory_count"]}</li>
    <li>Trajectory samples: {metadata["inputs"]["trajectory_sample_count"]}</li>
    <li>Deposition points: {metadata["inputs"]["deposition_point_count"]}</li>
    <li>Impact events: {metadata["inputs"]["impact_event_count"]}</li>
    <li>Cell size: {metadata["grid"]["cell_size_m"]} m</li>
  </ul>
  <h2>Layer Exports</h2>
  <table>
    <thead><tr><th>Layer</th><th>Units</th><th>Files</th><th>Interpretation</th><th>Summary</th></tr></thead>
    <tbody>{''.join(rows)}</tbody>
  </table>
  <p>Deposition points are also exported as <a href="{prefix}_deposition_points.geojson">GeoJSON</a>. Run metadata are in <a href="{prefix}_metadata.json">JSON</a>.</p>
  <h2>Plots</h2>
  {''.join(plots) if plots else '<p>PNG plots were not generated for this run.</p>'}
  <h2>Warnings</h2>
  <ul>{warnings or '<li>No warnings.</li>'}</ul>
  <h2>Known Limitations</h2>
  <ul>{limitations}</ul>
</body>
</html>
"""
    write_file_text(
        path,
        content,
        "html",
        output_file_metadata,
        output_write_kind_seconds,
        output_write_kind_bytes,
        elapsed_seconds=0.0,
    )


def format_summary(summary: dict[str, Any]) -> str:
    valid = summary.get("valid_cell_count", 0)
    nonzero = summary.get("nonzero_cell_count", 0)
    minimum = summary.get("minimum")
    maximum = summary.get("maximum")
    total = summary.get("sum")
    if valid == 0:
        return "no valid cells"
    return f"valid={valid}, nonzero={nonzero}, min={format_number(minimum)}, max={format_number(maximum)}, sum={format_number(total)}"


def format_number(value: Any) -> str:
    if isinstance(value, (int, float)):
        return f"{value:.6g}"
    return "n/a"
