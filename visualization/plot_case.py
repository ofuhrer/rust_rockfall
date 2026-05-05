#!/usr/bin/env python3
"""Render lightweight diagnostics from rockfall trajectory CSV outputs.

The visualizer is intentionally a consumer of existing outputs. It does not call
or link the Rust simulation core. PNG is the default output format; SVG remains
available with --format svg.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
COLORS = ["#1f77b4", "#d62728", "#2ca02c", "#9467bd", "#ff7f0e", "#17becf"]


@dataclass
class Trajectory:
    name: str
    samples: list[dict[str, float | str]]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", type=Path, help="verification/validation YAML case file")
    parser.add_argument(
        "--trajectory",
        action="append",
        type=Path,
        default=[],
        help="trajectory CSV; may be repeated for overlays",
    )
    parser.add_argument("--diagnostics", type=Path, help="JSON report produced by verify/validate")
    parser.add_argument("--output-dir", type=Path, help="directory for plot and summary outputs")
    parser.add_argument("--prefix", help="output filename prefix; defaults to case id or trajectory stem")
    parser.add_argument("--title", help="plot title override")
    parser.add_argument(
        "--format",
        action="append",
        choices=["png", "svg"],
        default=None,
        help="plot format; may be repeated. Defaults to png.",
    )
    args = parser.parse_args()

    case = load_case(args.case) if args.case else {}
    inferred_trajectory = nested_path(case, "outputs", "trajectory_csv")
    inferred_diagnostics = nested_path(case, "outputs", "diagnostics_json")
    trajectory_paths = args.trajectory or ([ROOT / inferred_trajectory] if inferred_trajectory else [])
    diagnostics_path = args.diagnostics or (ROOT / inferred_diagnostics if inferred_diagnostics else None)
    if not trajectory_paths:
        raise SystemExit("provide --trajectory or a --case with outputs.trajectory_csv")

    case_id = str(case.get("case_id") or Path(trajectory_paths[0]).stem)
    prefix = args.prefix or case_id
    output_dir = args.output_dir or ROOT / "visualization" / "output" / case_id
    output_dir.mkdir(parents=True, exist_ok=True)
    formats = args.format or ["png"]

    trajectories = [read_trajectory(path) for path in trajectory_paths]
    diagnostics = read_json(diagnostics_path) if diagnostics_path and diagnostics_path.exists() else {}
    title = args.title or str(case.get("title") or case_id)
    terrain = case.get("terrain", {}) if isinstance(case.get("terrain"), dict) else {}
    expected = case.get("expected", {}) if isinstance(case.get("expected"), dict) else {}
    radius = block_radius(case)
    observed_deposition = read_optional_points(nested_path(case, "observations", "deposition_points_csv"))
    ensemble_deposition = read_optional_points(nested_path(case, "outputs", "ensemble_deposition_csv"))

    render_trajectory_xz(title, trajectories, terrain, expected, radius, output_dir, prefix, formats)
    render_trajectory_xy(title, trajectories, expected, output_dir, prefix, formats)
    render_energy(title, trajectories, output_dir, prefix, formats)
    render_runout_histogram(title, trajectories, output_dir, prefix, formats)
    render_deposition_cloud(
        title,
        observed_deposition,
        ensemble_deposition,
        output_dir,
        prefix,
        formats,
    )
    write_text(
        output_dir / f"{prefix}_summary.json",
        json.dumps(summarize(trajectories, diagnostics), indent=2, sort_keys=True) + "\n",
    )

    print(f"wrote visualization outputs to {output_dir}")
    return 0


def load_case(path: Path | None) -> dict:
    if path is None:
        return {}
    try:
        import yaml  # type: ignore
    except ImportError as exc:
        raise SystemExit(
            "PyYAML is required when using --case. Install with `python3 -m pip install PyYAML`."
        ) from exc
    with path.open() as file:
        return yaml.safe_load(file) or {}


def read_trajectory(path: Path) -> Trajectory:
    with path.open(newline="") as file:
        reader = csv.DictReader(file)
        samples: list[dict[str, float | str]] = []
        for row in reader:
            sample: dict[str, float | str] = {}
            for key, value in row.items():
                if key == "contact_state":
                    sample[key] = value
                else:
                    sample[key] = float(value)
            samples.append(sample)
    if not samples:
        raise SystemExit(f"trajectory has no samples: {path}")
    return Trajectory(path.stem, samples)


def read_json(path: Path) -> dict:
    with path.open() as file:
        return json.load(file)


def read_optional_points(path_text: str | None) -> list[dict[str, float | str]]:
    if not path_text:
        return []
    path = ROOT / path_text
    if not path.exists():
        return []
    points: list[dict[str, float | str]] = []
    with path.open(newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            point: dict[str, float | str] = {}
            for key, value in row.items():
                if key in {"trajectory_id", "experiment_id", "release_id", "source", "block_id"}:
                    point[key] = value
                elif value not in {None, ""}:
                    point[key] = float(value)
            points.append(point)
    return points


def render_trajectory_xz(
    title: str,
    trajectories: list[Trajectory],
    terrain: dict,
    expected: dict,
    radius: float,
    output_dir: Path,
    prefix: str,
    formats: list[str],
) -> None:
    fig, ax = plt.subplots(figsize=(10.5, 6.0), constrained_layout=True)
    for index, trajectory in enumerate(trajectories):
        color = COLORS[index % len(COLORS)]
        ax.plot(series(trajectory, "x_m"), series(trajectory, "z_m"), color=color, lw=2, label=trajectory.name)
        plot_state_markers(ax, trajectory, "x_m", "z_m", color)

    xs = [x for trajectory in trajectories for x in series(trajectory, "x_m")]
    terrain_points = sample_terrain(terrain, min(xs), max(xs), radius)
    if terrain_points:
        tx, tz = zip(*terrain_points)
        ax.plot(tx, tz, color="#5f6368", lw=1.8, ls="--", label="terrain + radius")

    expected_position = expected.get("final_position_m")
    if isinstance(expected_position, list) and len(expected_position) == 3:
        ax.scatter([float(expected_position[0])], [float(expected_position[2])], marker="x", s=80, c="#111827", label="expected")

    ax.set_title(title)
    ax.set_xlabel("x [m]")
    ax.set_ylabel("z [m]")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="best", fontsize=9)
    save_figure(fig, output_dir, f"{prefix}_trajectory_xz", formats)


def render_trajectory_xy(
    title: str,
    trajectories: list[Trajectory],
    expected: dict,
    output_dir: Path,
    prefix: str,
    formats: list[str],
) -> None:
    fig, ax = plt.subplots(figsize=(10.5, 6.0), constrained_layout=True)
    for index, trajectory in enumerate(trajectories):
        color = COLORS[index % len(COLORS)]
        ax.plot(series(trajectory, "x_m"), series(trajectory, "y_m"), color=color, lw=2, label=trajectory.name)
        plot_state_markers(ax, trajectory, "x_m", "y_m", color)

    expected_position = expected.get("final_position_m")
    if isinstance(expected_position, list) and len(expected_position) == 3:
        ax.scatter([float(expected_position[0])], [float(expected_position[1])], marker="x", s=80, c="#111827", label="expected")

    ax.set_title(f"{title}: plan view")
    ax.set_xlabel("x [m]")
    ax.set_ylabel("y [m]")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="best", fontsize=9)
    save_figure(fig, output_dir, f"{prefix}_trajectory_xy", formats)


def render_energy(title: str, trajectories: list[Trajectory], output_dir: Path, prefix: str, formats: list[str]) -> None:
    fig, ax = plt.subplots(figsize=(10.5, 6.0), constrained_layout=True)
    styles = {
        "kinetic_j": ("kinetic", "#1f77b4"),
        "potential_j": ("potential", "#2ca02c"),
        "total_energy_j": ("total", "#111827"),
    }
    for trajectory_index, trajectory in enumerate(trajectories):
        alpha = 1.0 if trajectory_index == 0 else 0.45
        for key, (label, color) in styles.items():
            plot_label = label if trajectory_index == 0 else None
            ax.plot(series(trajectory, "time_s"), series(trajectory, key), color=color, lw=2, alpha=alpha, label=plot_label)
        for sample in impact_transition_samples(trajectory.samples):
            ax.axvline(float(sample["time_s"]), color="#ef4444", lw=0.9, alpha=0.18)

    ax.set_title(f"{title}: energy")
    ax.set_xlabel("time [s]")
    ax.set_ylabel("energy [J]")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="best", fontsize=9)
    save_figure(fig, output_dir, f"{prefix}_energy", formats)


def render_runout_histogram(
    title: str,
    trajectories: list[Trajectory],
    output_dir: Path,
    prefix: str,
    formats: list[str],
) -> None:
    if len(trajectories) <= 1:
        return
    runouts = []
    for trajectory in trajectories:
        first = trajectory.samples[0]
        last = trajectory.samples[-1]
        runouts.append(math.hypot(float(last["x_m"]) - float(first["x_m"]), float(last["y_m"]) - float(first["y_m"])))

    fig, ax = plt.subplots(figsize=(9.0, 5.2), constrained_layout=True)
    ax.hist(runouts, bins=min(10, max(3, len(runouts))), color="#1f77b4", alpha=0.78, edgecolor="#0f172a")
    ax.axvline(statistics.fmean(runouts), color="#111827", lw=2, label="mean")
    ax.set_title(f"{title}: runout distribution")
    ax.set_xlabel("runout [m]")
    ax.set_ylabel("trajectory count")
    ax.grid(True, axis="y", alpha=0.25)
    ax.legend(loc="best", fontsize=9)
    save_figure(fig, output_dir, f"{prefix}_runout_histogram", formats)


def render_deposition_cloud(
    title: str,
    observed: list[dict[str, float | str]],
    simulated: list[dict[str, float | str]],
    output_dir: Path,
    prefix: str,
    formats: list[str],
) -> None:
    if not observed and not simulated:
        return
    fig, ax = plt.subplots(figsize=(9.0, 6.2), constrained_layout=True)
    if observed:
        ax.scatter(
            [float(point["x_m"]) for point in observed],
            [float(point["y_m"]) for point in observed],
            marker="x",
            s=62,
            linewidths=1.8,
            color="#111827",
            label="observed deposition",
        )
    if simulated:
        ax.scatter(
            [float(point["x_m"]) for point in simulated],
            [float(point["y_m"]) for point in simulated],
            marker="o",
            s=28,
            alpha=0.62,
            color="#1f77b4",
            edgecolors="none",
            label="simulated ensemble final points",
        )
    ax.set_title(f"{title}: deposition cloud")
    ax.set_xlabel("x [m]")
    ax.set_ylabel("y [m]")
    ax.set_aspect("equal", adjustable="box")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="best", fontsize=9)
    save_figure(fig, output_dir, f"{prefix}_deposition_xy", formats)


def plot_state_markers(ax, trajectory: Trajectory, x_key: str, y_key: str, color: str) -> None:
    first = trajectory.samples[0]
    last = trajectory.samples[-1]
    ax.scatter([float(first[x_key])], [float(first[y_key])], marker="o", s=45, facecolor="white", edgecolor=color, zorder=4, label="start")
    impacts = impact_transition_samples(trajectory.samples)
    if impacts:
        ax.scatter(
            [float(sample[x_key]) for sample in impacts],
            [float(sample[y_key]) for sample in impacts],
            marker="o",
            s=26,
            color="#ef4444",
            alpha=0.75,
            zorder=4,
            label="impact",
        )
    ax.scatter([float(last[x_key])], [float(last[y_key])], marker="s", s=45, color="#111827", zorder=5, label="final")


def save_figure(fig, output_dir: Path, stem: str, formats: list[str]) -> None:
    for fmt in formats:
        fig.savefig(output_dir / f"{stem}.{fmt}", dpi=160)
    plt.close(fig)


def summarize(trajectories: list[Trajectory], diagnostics: dict) -> dict:
    runouts = []
    impact_counts = []
    max_speeds = []
    for trajectory in trajectories:
        first = trajectory.samples[0]
        last = trajectory.samples[-1]
        runout = math.hypot(float(last["x_m"]) - float(first["x_m"]), float(last["y_m"]) - float(first["y_m"]))
        runouts.append(runout)
        impact_counts.append(count_impact_transitions(trajectory.samples))
        max_speeds.append(max(float(sample["speed_mps"]) for sample in trajectory.samples))
    return {
        "trajectory_count": len(trajectories),
        "runout_m": percentile_summary(runouts),
        "impact_count": percentile_summary([float(value) for value in impact_counts]),
        "max_speed_mps": percentile_summary(max_speeds),
        "diagnostics_status": diagnostics.get("status"),
        "diagnostics_metrics": diagnostics.get("metrics", {}),
    }


def sample_terrain(terrain: dict, xmin: float, xmax: float, radius: float) -> list[tuple[float, float]]:
    terrain_type = terrain.get("type")
    params = terrain.get("parameters", {}) if isinstance(terrain.get("parameters"), dict) else {}
    if terrain_type not in {"plane", "paraboloid", "step"}:
        return []
    points = []
    for index in range(240):
        x = xmin + index * (xmax - xmin) / 239
        if terrain_type == "plane":
            z = float(params.get("z0_m", 0.0)) + float(params.get("slope_x", 0.0)) * x
        elif terrain_type == "paraboloid":
            z = float(params.get("z0_m", 0.0)) + float(params.get("ax", 0.0)) * x * x
        else:
            z = (
                float(params.get("high_z_m", 0.0))
                if x < float(params.get("step_x_m", 0.0))
                else float(params.get("low_z_m", 0.0))
            )
        points.append((x, z + radius))
    return points


def impact_transition_samples(samples: list[dict[str, float | str]]) -> list[dict[str, float | str]]:
    impacts = []
    previous_state = None
    for sample in samples:
        state = sample.get("contact_state")
        if state == "impact" and previous_state != "impact":
            impacts.append(sample)
        previous_state = state
    return impacts


def count_impact_transitions(samples: list[dict[str, float | str]]) -> int:
    return len(impact_transition_samples(samples))


def percentile_summary(values: list[float]) -> dict[str, float]:
    ordered = sorted(values)
    return {
        "min": ordered[0],
        "mean": statistics.fmean(ordered),
        "median": percentile(ordered, 0.5),
        "p05": percentile(ordered, 0.05),
        "p95": percentile(ordered, 0.95),
        "max": ordered[-1],
    }


def percentile(ordered: list[float], p: float) -> float:
    if not ordered:
        return 0.0
    rank = p * (len(ordered) - 1)
    lower = math.floor(rank)
    upper = math.ceil(rank)
    if lower == upper:
        return ordered[lower]
    weight = rank - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def series(trajectory: Trajectory, key: str) -> list[float]:
    return [float(sample[key]) for sample in trajectory.samples]


def nested_path(data: dict, first: str, second: str) -> str | None:
    child = data.get(first)
    if isinstance(child, dict) and child.get(second):
        return str(child[second])
    return None


def block_radius(case: dict) -> float:
    block = case.get("block")
    if isinstance(block, dict):
        return float(block.get("radius", block.get("radius_m", 0.0)))
    return 0.0


def write_text(path: Path, text: str) -> None:
    path.write_text(text)


if __name__ == "__main__":
    raise SystemExit(main())
