#!/usr/bin/env python3
"""Run a deterministic single-impact calibration for scarring_contact_v1.

This experiment is intentionally narrow. It uses simple flat-plane single-impact
simulations and compares ImpactEvent diagnostics to a configured impact dataset.
It is separate from validation and does not change any model defaults.
"""

from __future__ import annotations

import argparse
import csv
import html
import itertools
import json
import math
import re
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = (
    ROOT / "calibration" / "experiments" / "scarring_single_impact_v0_4" / "config.yaml"
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    args = parser.parse_args()

    config = load_yaml(resolve(args.config))
    run_experiment(config)
    return 0


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml  # type: ignore
    except ImportError as exc:
        raise SystemExit(
            "PyYAML is required. From the repo root, run "
            "`PYENV_VERSION=system uv run python scripts/calibrate_scarring_impact.py ...`. "
            "CI may install `requirements-tools.txt` with system Python instead."
        ) from exc
    with path.open(encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}
    if not isinstance(data, dict):
        raise SystemExit(f"expected mapping in {path}")
    return data


def write_yaml(path: Path, data: dict[str, Any]) -> None:
    try:
        import yaml  # type: ignore
    except ImportError as exc:
        raise SystemExit(
            "PyYAML is required. From the repo root, run "
            "`PYENV_VERSION=system uv run python scripts/calibrate_scarring_impact.py ...`. "
            "CI may install `requirements-tools.txt` with system Python instead."
        ) from exc
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def resolve(path: Path | str) -> Path:
    path = Path(path)
    return path if path.is_absolute() else ROOT / path


def run_experiment(config: dict[str, Any]) -> None:
    impacts = read_reference_impacts(resolve(config["dataset"]["path"]))
    result_dir = resolve(config["outputs"]["generated_results_dir"])
    config_dir = result_dir / "configs"
    event_dir = result_dir / "impact_events"
    trajectory_dir = result_dir / "trajectories"
    for directory in (config_dir, event_dir, trajectory_dir):
        directory.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = []
    candidates = parameter_candidates(config)
    if not candidates:
        raise stage_error("parameter grid evaluation", "parameter_grid produced no candidates")
    for candidate_index, candidate in enumerate(candidates):
        candidate_id = f"candidate_{candidate_index:03}"
        impact_rows = []
        for impact in impacts:
            event = simulate_impact(config, candidate, impact, candidate_id, config_dir, event_dir, trajectory_dir)
            impact_rows.append(compare_impact(impact, event, config))
        row = summarize_candidate(candidate_id, candidate, impact_rows, config)
        rows.append(row)
        print(
            f"{candidate_id} objective={row['objective']:.6f} "
            f"depth_err={format_progress_value(row['mean_relative_depth_error'])} "
            f"loss_err={format_progress_value(row['mean_relative_energy_loss_error'])} "
            f"post_rebound_err={format_progress_value(row['mean_relative_post_rebound_energy_error'])}"
        )

    rows.sort(key=lambda row: (float(row["objective"]), row["candidate_id"]))
    if not rows:
        raise stage_error("candidate evaluation", "parameter_grid produced no candidate rows")
    write_candidate_results(resolve(config["outputs"]["candidate_results_csv"]), rows)
    write_selected_parameters(resolve(config["outputs"]["selected_parameters_yaml"]), rows[0], config)
    write_summary(resolve(config["outputs"]["summary_json"]), rows, impacts, config)
    write_html_report(resolve(config["outputs"]["report_html"]), rows, impacts, config)


def read_reference_impacts(path: Path) -> list[dict[str, Any]]:
    with path.open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    if not rows:
        raise stage_error("impact dataset loading", f"impact CSV {path} has no rows")
    impacts = []
    for row in rows:
        impacts.append(
            {
                "impact_id": row["impact_id"],
                "mass_kg": float(row["mass_kg"]),
                "radius_m": float(row["radius_m"]),
                "incoming_normal_speed_mps": float(row["incoming_normal_speed_mps"]),
                "incoming_tangent_speed_mps": float(row["incoming_tangent_speed_mps"]),
                "impact_angle_deg": optional_float(row.get("impact_angle_deg")),
                "observed_scarring_depth_m": optional_float(row.get("observed_scarring_depth_m")),
                "observed_scarring_energy_loss_j": optional_float(
                    row.get("observed_scarring_energy_loss_j")
                ),
                "observed_post_rebound_translational_j": optional_float(
                    row.get("observed_post_rebound_translational_j")
                ),
                "observed_total_translational_energy_loss_j": optional_float(
                    row.get("observed_total_translational_energy_loss_j")
                ),
                "notes": row.get("notes", ""),
            }
        )
    return impacts


def parameter_candidates(config: dict[str, Any]) -> list[dict[str, float]]:
    grid = config["parameter_grid"]
    grid_axes = {
        "soil_strength_pa": grid.get("soil_strength_pa", []),
        "scarring_drag_coefficient": grid.get("scarring_drag_coefficient", []),
        "scarring_layer_density_kgpm3": grid.get("scarring_layer_density_kgpm3", []),
    }
    missing = [name for name, values in grid_axes.items() if not values]
    if missing:
        raise stage_error(
            "parameter grid evaluation",
            f"parameter_grid is empty for {', '.join(missing)}",
        )
    candidates = []
    for soil_strength, drag, density in itertools.product(
        grid_axes["soil_strength_pa"],
        grid_axes["scarring_drag_coefficient"],
        grid_axes["scarring_layer_density_kgpm3"],
    ):
        candidates.append(
            {
                "soil_strength_pa": float(soil_strength),
                "scarring_drag_coefficient": float(drag),
                "scarring_layer_density_kgpm3": float(density),
            }
        )
    return candidates


def simulate_impact(
    config: dict[str, Any],
    candidate: dict[str, float],
    impact: dict[str, Any],
    candidate_id: str,
    config_dir: Path,
    event_dir: Path,
    trajectory_dir: Path,
) -> dict[str, Any]:
    impact_id = impact["impact_id"]
    run_id = f"{candidate_id}_{impact_id}"
    config_path = config_dir / f"{run_id}.json"
    trajectory_path = trajectory_dir / f"{run_id}.csv"
    impact_events_path = event_dir / f"{run_id}.json"
    sim_config = build_single_impact_config(config, candidate, impact)
    config_path.write_text(json.dumps(sim_config, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    try:
        subprocess.run(
            [
                "cargo",
                "run",
                "-q",
                "--",
                "run",
                "--config",
                str(config_path),
                "--output",
                str(trajectory_path),
                "--impact-events-json",
                str(impact_events_path),
            ],
            cwd=ROOT,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        detail = f"cargo run failed for {run_id} with exit code {exc.returncode}"
        if stderr:
            detail = f"{detail}: {stderr.splitlines()[-1]}"
        raise stage_error("impact simulation", detail) from exc
    events = json.loads(impact_events_path.read_text(encoding="utf-8"))
    significant = [
        event
        for event in events
        if float(event["incoming_normal_speed_mps"]) >= 0.05
    ]
    if not significant:
        raise stage_error(
            "impact event filtering",
            f"{run_id} produced no significant impact events in {impact_events_path}",
        )
    if len(significant) != 1:
        raise stage_error(
            "impact event filtering",
            f"{run_id} produced {len(significant)} significant impact events in {impact_events_path}; expected exactly one",
        )
    return significant[0]


def build_single_impact_config(
    config: dict[str, Any], candidate: dict[str, float], impact: dict[str, Any]
) -> dict[str, Any]:
    dt = float(config["simulation"]["dt"])
    gravity = float(config["fixed_parameters"]["gravity"])
    normal_speed = float(impact["incoming_normal_speed_mps"])
    tangent_speed = float(impact["incoming_tangent_speed_mps"])
    radius = float(impact["radius_m"])
    # Choose one ballistic step that arrives at the target incoming speed.
    initial_vz = -normal_speed + gravity * dt
    initial_z = radius + 1.0e-4
    return {
        "block": {"radius_m": radius, "mass_kg": float(impact["mass_kg"])},
        "initial_position_m": [0.0, 0.0, initial_z],
        "initial_velocity_mps": [tangent_speed, 0.0, initial_vz],
        "initial_angular_velocity_radps": [0.0, 0.0, 0.0],
        "terrain": {"kind": "plane", "z0_m": 0.0, "slope_x": 0.0, "slope_y": 0.0},
        "dt_s": dt,
        "max_time_s": float(config["simulation"]["t_max"]),
        "gravity_mps2": gravity,
        "normal_restitution": float(config["fixed_parameters"]["normal_restitution"]),
        "tangential_restitution": float(config["fixed_parameters"]["tangential_restitution"]),
        "friction_coefficient": float(config["fixed_parameters"]["friction_coefficient"]),
        "rolling_resistance_coefficient": 0.0,
        "contact_model": config["fixed_parameters"]["contact_model"],
        "soil_interaction_model": config["fixed_parameters"]["soil_interaction_model"],
        "soil_strength_pa": candidate["soil_strength_pa"],
        "scarring_drag_coefficient": candidate["scarring_drag_coefficient"],
        "scarring_layer_density_kgpm3": candidate["scarring_layer_density_kgpm3"],
        "stop_speed_mps": float(config["simulation"]["stop_velocity"]),
        "random_seed": int(config["random"]["seed"]),
    }


def compare_impact(
    impact: dict[str, Any], event: dict[str, Any], config: dict[str, Any]
) -> dict[str, Any]:
    epsilon = float(config["objective"].get("epsilon", 1.0e-9))
    observed_depth = impact.get("observed_scarring_depth_m")
    observed_loss = impact.get("observed_scarring_energy_loss_j")
    observed_post_rebound = impact.get("observed_post_rebound_translational_j")
    simulated_depth = float(event["scarring_depth_m"])
    simulated_loss = float(event["scarring_capped_energy_loss_j"])
    simulated_post_rebound = float(event["post_scarring_translational_j"])
    row = {
        "impact_id": impact["impact_id"],
        "observed_depth_m": observed_depth,
        "simulated_depth_m": simulated_depth,
        "observed_energy_loss_j": observed_loss,
        "simulated_energy_loss_j": simulated_loss,
        "observed_post_rebound_translational_j": observed_post_rebound,
        "simulated_post_rebound_translational_j": simulated_post_rebound,
        "observed_total_translational_energy_loss_j": impact.get(
            "observed_total_translational_energy_loss_j"
        ),
        "incoming_normal_speed_mps": float(event["incoming_normal_speed_mps"]),
        "incoming_tangent_speed_mps": float(event["incoming_tangent_speed_mps"]),
        "post_contact_translational_j": float(event["post_contact_translational_j"]),
        "post_scarring_translational_j": float(event["post_scarring_translational_j"]),
        "scarring_loss_fraction_of_post_contact_energy": simulated_loss
        / max(float(event["post_contact_translational_j"]), epsilon),
    }
    row["relative_depth_error"] = relative_error(simulated_depth, observed_depth, epsilon)
    row["relative_energy_loss_error"] = relative_error(simulated_loss, observed_loss, epsilon)
    row["relative_post_rebound_energy_error"] = relative_error(
        simulated_post_rebound, observed_post_rebound, epsilon
    )
    return row


def summarize_candidate(
    candidate_id: str,
    candidate: dict[str, float],
    impact_rows: list[dict[str, Any]],
    config: dict[str, Any],
) -> dict[str, Any]:
    mean_depth_error = mean_present(row["relative_depth_error"] for row in impact_rows)
    mean_energy_error = mean_present(row["relative_energy_loss_error"] for row in impact_rows)
    mean_post_rebound_error = mean_present(
        row["relative_post_rebound_energy_error"] for row in impact_rows
    )
    weights = config["objective"]["weights"]
    objective_terms = {
        "mean_relative_depth_error": mean_depth_error,
        "mean_relative_energy_loss_error": mean_energy_error,
        "mean_relative_post_rebound_energy_error": mean_post_rebound_error,
    }
    objective = 0.0
    used_weight = 0.0
    for metric, weight in weights.items():
        value = objective_terms.get(metric)
        if value is not None:
            objective += float(weight) * value
            used_weight += float(weight)
    if used_weight <= 0.0:
        raise SystemExit("objective weights do not reference any available target metrics")
    row: dict[str, Any] = {
        "candidate_id": candidate_id,
        **candidate,
        "objective": objective,
        "mean_relative_depth_error": mean_depth_error,
        "mean_relative_energy_loss_error": mean_energy_error,
        "mean_relative_post_rebound_energy_error": mean_post_rebound_error,
    }
    for impact_row in impact_rows:
        impact_id = impact_row["impact_id"]
        for key, value in impact_row.items():
            if key != "impact_id":
                row[f"{impact_id}_{key}"] = value
    return row


def mean(values: Any) -> float:
    values = list(values)
    return sum(values) / len(values)


def mean_present(values: Any) -> float | None:
    values = [value for value in values if value is not None]
    if not values:
        return None
    return sum(values) / len(values)


def relative_error(simulated: float, observed: float | None, epsilon: float) -> float | None:
    if observed is None:
        return None
    return abs(simulated - observed) / max(abs(observed), epsilon)


def optional_float(value: object) -> float | None:
    text = str(value or "").strip()
    if not text or text.lower() == "nan":
        return None
    return float(text)


def write_candidate_results(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise stage_error("candidate result writing", f"no candidate rows are available for {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0])
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_selected_parameters(path: Path, best: dict[str, Any], config: dict[str, Any]) -> None:
    write_yaml(
        path,
        {
            "experiment_id": config["experiment_id"],
            "model_version": model_version(),
            "dataset_id": config["dataset"]["id"],
            "selection": "minimum weighted mean relative impact-level objective",
            "objective": float(best["objective"]),
            "parameters": {
                "soil_strength_pa": float(best["soil_strength_pa"]),
                "scarring_drag_coefficient": float(best["scarring_drag_coefficient"]),
                "scarring_layer_density_kgpm3": float(best["scarring_layer_density_kgpm3"]),
            },
            "limitations": [
                config.get("limitations_summary", "single-impact calibration only"),
                "not validation",
                "not a trajectory-level parameter set",
            ],
        },
    )


def write_summary(
    path: Path, rows: list[dict[str, Any]], impacts: list[dict[str, Any]], config: dict[str, Any]
) -> None:
    if not rows:
        raise stage_error("summary writing", f"no candidate rows are available for {path}")
    summary = {
        "experiment_id": config["experiment_id"],
        "model_version": model_version(),
        "git_hash": git_hash(),
        "dataset": config["dataset"],
        "objective": config["objective"],
        "candidate_count": len(rows),
        "impact_count": len(impacts),
        "best": rows[0],
        "top_candidates": rows[:5],
        "interpretation": (
            config.get(
                "interpretation",
                "This experiment shows impact-level sensitivity. It is not validation "
                "and must not be used for validation defaults.",
            )
        ),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_html_report(
    path: Path, rows: list[dict[str, Any]], impacts: list[dict[str, Any]], config: dict[str, Any]
) -> None:
    if not rows:
        raise stage_error("report generation", f"no candidate rows are available for {path}")
    best = rows[0]
    impact_columns = [
        "impact_id",
        "observed_depth_m",
        "simulated_depth_m",
        "observed_energy_loss_j",
        "simulated_energy_loss_j",
        "observed_post_rebound_translational_j",
        "simulated_post_rebound_translational_j",
        "relative_depth_error",
        "relative_energy_loss_error",
        "relative_post_rebound_energy_error",
    ]
    best_rows = []
    for impact in impacts:
        prefix = impact["impact_id"]
        best_rows.append(
            "<tr>"
            + "".join(
                f"<td>{escape(format_value(best[f'{prefix}_{col}']) if col != 'impact_id' else prefix)}</td>"
                for col in impact_columns
            )
            + "</tr>"
        )
    candidate_rows = []
    for row in rows[:10]:
        candidate_rows.append(
            "<tr>"
            f"<td>{escape(row['candidate_id'])}</td>"
            f"<td>{escape(format_value(row['objective']))}</td>"
            f"<td>{escape(format_value(row['soil_strength_pa']))}</td>"
            f"<td>{escape(format_value(row['scarring_drag_coefficient']))}</td>"
            f"<td>{escape(format_value(row['scarring_layer_density_kgpm3']))}</td>"
            f"<td>{escape(format_value(row['mean_relative_depth_error']))}</td>"
            f"<td>{escape(format_value(row['mean_relative_energy_loss_error']))}</td>"
            f"<td>{escape(format_value(row['mean_relative_post_rebound_energy_error']))}</td>"
            "</tr>"
        )
    html_text = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{escape(config['title'])}</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 32px; line-height: 1.45; max-width: 1100px; }}
    table {{ border-collapse: collapse; width: 100%; margin: 16px 0; font-size: 0.9rem; }}
    th, td {{ border: 1px solid #d8dee8; padding: 7px 9px; text-align: left; }}
    th {{ background: #eef3f8; }}
    code {{ background: #f3f4f6; padding: 1px 4px; border-radius: 4px; }}
  </style>
</head>
<body>
  <h1>{escape(config['title'])}</h1>
  <p><strong>Scope:</strong> {escape(config.get('scope_note', 'impact-level calibration only. This is not validation and not operational calibration.'))}</p>
  <p><strong>Best candidate:</strong> <code>{escape(best['candidate_id'])}</code>, objective {escape(format_value(best['objective']))}.</p>
  <h2>Best Candidate Parameters</h2>
  <ul>
    <li>soil_strength_pa: {escape(format_value(best['soil_strength_pa']))}</li>
    <li>scarring_drag_coefficient: {escape(format_value(best['scarring_drag_coefficient']))}</li>
    <li>scarring_layer_density_kgpm3: {escape(format_value(best['scarring_layer_density_kgpm3']))}</li>
  </ul>
  <h2>Best Candidate Impact Comparison</h2>
  <table>
    <thead><tr>{''.join(f'<th>{escape(col)}</th>' for col in impact_columns)}</tr></thead>
    <tbody>{''.join(best_rows)}</tbody>
  </table>
  <h2>Top Candidates</h2>
  <table>
    <thead><tr><th>candidate</th><th>objective</th><th>soil_strength_pa</th><th>Cd</th><th>rho</th><th>depth error</th><th>loss error</th><th>post-rebound energy error</th></tr></thead>
    <tbody>{''.join(candidate_rows)}</tbody>
  </table>
</body>
</html>
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html_text, encoding="utf-8")


def model_version() -> str:
    cargo = (ROOT / "Cargo.toml").read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', cargo, re.MULTILINE)
    return match.group(1) if match else "unknown"


def git_hash() -> str | None:
    result = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else None


def format_value(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value)


def format_progress_value(value: Any) -> str:
    if value is None:
        return "n/a"
    return f"{float(value):.6f}"


def escape(value: Any) -> str:
    return html.escape(str(value))


def stage_error(stage: str, message: str) -> SystemExit:
    return SystemExit(f"{stage}: {message}")


if __name__ == "__main__":
    raise SystemExit(main())
