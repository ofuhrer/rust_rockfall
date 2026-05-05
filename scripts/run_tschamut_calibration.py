#!/usr/bin/env python3
"""Run a controlled Tschamut calibration experiment.

The workflow is intentionally simple: build a deterministic split, evaluate a
small explicit parameter grid by calling the existing validation CLI on
temporary calibration cases, and write small committed summaries outside the
ignored calibration/results directory.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import itertools
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "calibration" / "experiments" / "tschamut_v0_3" / "config.yaml"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument(
        "--prepare-only",
        action="store_true",
        help="write split/subset files without running the parameter grid",
    )
    args = parser.parse_args()

    config = load_yaml(resolve(args.config))
    prepare_split(config)
    if args.prepare_only:
        print("prepared calibration split")
        return 0
    run_experiment(config)
    return 0


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml  # type: ignore
    except ImportError as exc:
        raise SystemExit("PyYAML is required: python3 -m pip install PyYAML") from exc
    with path.open(encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}
    if not isinstance(data, dict):
        raise SystemExit(f"expected mapping in {path}")
    return data


def write_yaml(path: Path, data: dict[str, Any]) -> None:
    try:
        import yaml  # type: ignore
    except ImportError as exc:
        raise SystemExit("PyYAML is required: python3 -m pip install PyYAML") from exc
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def resolve(path: Path | str) -> Path:
    path = Path(path)
    return path if path.is_absolute() else ROOT / path


def prepare_split(config: dict[str, Any]) -> None:
    split_cfg = config["split"]
    dataset = config["dataset"]
    releases = read_csv(resolve(dataset["release_points_csv"]))
    depositions = read_csv(resolve(dataset["deposition_points_csv"]))
    deposition_by_id = {row["trajectory_id"]: row for row in depositions}

    by_block: dict[str, list[dict[str, str]]] = {}
    for row in releases:
        by_block.setdefault(row["block_id"], []).append(row)

    calibration_ids: list[str] = []
    holdout_ids: list[str] = []
    unused_ids: list[str] = []
    seed = int(split_cfg["seed"])
    for block_id, rows in sorted(by_block.items()):
        ordered = sorted(
            rows,
            key=lambda row: stable_key(seed, block_id, row["trajectory_id"]),
        )
        cal_count = int(split_cfg["calibration_per_block"])
        holdout_count = int(split_cfg["holdout_per_block"])
        calibration_ids.extend(row["trajectory_id"] for row in ordered[:cal_count])
        holdout_ids.extend(row["trajectory_id"] for row in ordered[cal_count : cal_count + holdout_count])
        unused_ids.extend(row["trajectory_id"] for row in ordered[cal_count + holdout_count :])

    split = {
        "dataset_id": dataset["id"],
        "doi": dataset["doi"],
        "method": (
            "Within each block_id, sort trajectory_id by SHA-256(seed, block_id, trajectory_id); "
            "take the first calibration_per_block for calibration and the next holdout_per_block for holdout."
        ),
        "seed": seed,
        "calibration_per_block": int(split_cfg["calibration_per_block"]),
        "holdout_per_block": int(split_cfg["holdout_per_block"]),
        "calibration_ids": sorted(calibration_ids),
        "holdout_ids": sorted(holdout_ids),
        "unused_ids": sorted(unused_ids),
        "leakage_check": {
            "intersection_size": len(set(calibration_ids) & set(holdout_ids)),
            "calibration_count": len(calibration_ids),
            "holdout_count": len(holdout_ids),
        },
    }
    split_path = resolve(split_cfg["path"])
    write_yaml(split_path, split)

    out_dir = split_path.parent
    write_subset_csv(out_dir / "calibration_release_points.csv", releases, calibration_ids)
    write_subset_csv(out_dir / "calibration_observed_deposition.csv", depositions, calibration_ids)
    write_subset_csv(out_dir / "holdout_release_points.csv", releases, holdout_ids)
    write_subset_csv(out_dir / "holdout_observed_deposition.csv", depositions, holdout_ids)
    if missing := sorted(set(calibration_ids + holdout_ids) - set(deposition_by_id)):
        raise SystemExit(f"split contains ids without deposition rows: {missing}")


def stable_key(seed: int, block_id: str, trajectory_id: str) -> str:
    text = f"{seed}:{block_id}:{trajectory_id}".encode("utf-8")
    return hashlib.sha256(text).hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def write_subset_csv(path: Path, rows: list[dict[str, str]], selected_ids: list[str]) -> None:
    selected = set(selected_ids)
    subset = [row for row in rows if row["trajectory_id"] in selected]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(subset)


def run_experiment(config: dict[str, Any]) -> None:
    result_dir = resolve(config["outputs"]["generated_results_dir"])
    case_dir = result_dir / "cases"
    report_dir = result_dir / "reports"
    result_dir.mkdir(parents=True, exist_ok=True)
    case_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    candidates = list(parameter_candidates(config))
    rows = []
    for index, candidate in enumerate(candidates):
        candidate_id = f"candidate_{index:03}"
        calibration_report = evaluate_candidate(config, candidate, candidate_id, "calibration", case_dir, report_dir)
        holdout_report = evaluate_candidate(config, candidate, candidate_id, "holdout", case_dir, report_dir)
        calibration_objective = objective_value(calibration_report["metrics"], config)
        holdout_objective = objective_value(holdout_report["metrics"], config)
        row = {
            "candidate_id": candidate_id,
            **candidate,
            "calibration_objective": calibration_objective,
            "holdout_objective": holdout_objective,
            **prefixed_metrics("calibration", calibration_report["metrics"]),
            **prefixed_metrics("holdout", holdout_report["metrics"]),
        }
        rows.append(row)
        print(
            f"{candidate_id} calibration_objective={calibration_objective:.6f} "
            f"holdout_objective={holdout_objective:.6f}"
        )

    rows.sort(key=lambda row: (float(row["calibration_objective"]), float(row["holdout_objective"])))
    write_candidate_results(resolve(config["outputs"]["candidate_results_csv"]), rows)
    write_selected_parameters(resolve(config["outputs"]["selected_parameters_yaml"]), rows[0], config)
    write_summary(resolve(config["outputs"]["summary_json"]), rows, config)
    write_html_report(resolve(config["outputs"]["report_html"]), rows, config)


def parameter_candidates(config: dict[str, Any]) -> list[dict[str, Any]]:
    grid = config["parameter_grid"]
    candidates = []
    for normal, tangential, friction, roughness in itertools.product(
        grid["normal_restitution"],
        grid["tangential_restitution"],
        grid["friction_coefficient"],
        grid["roughness_profile"],
    ):
        candidates.append(
            {
                "normal_restitution": float(normal),
                "tangential_restitution": float(tangential),
                "friction_coefficient": float(friction),
                "roughness_profile": roughness["id"],
                "roughness_std_normal": float(roughness["roughness_std_normal"]),
                "roughness_std_tangent": float(roughness["roughness_std_tangent"]),
                "roughness_std_angle": float(roughness["roughness_std_angle"]),
            }
        )
    return candidates


def evaluate_candidate(
    config: dict[str, Any],
    candidate: dict[str, Any],
    candidate_id: str,
    partition: str,
    case_dir: Path,
    report_dir: Path,
) -> dict[str, Any]:
    case_id = f"calibration_tschamut_{partition}_{candidate_id}"
    case_path = case_dir / f"{case_id}.yaml"
    diagnostics_json = report_dir / f"{case_id}.json"
    ensemble_csv = report_dir / f"{case_id}_ensemble_deposition.csv"
    case = build_case(config, candidate, case_id, partition, diagnostics_json, ensemble_csv)
    write_yaml(case_path, case)
    subprocess.run(
        ["cargo", "run", "-q", "--", "validate", "--case", str(case_path)],
        cwd=ROOT,
        check=True,
        stdout=subprocess.DEVNULL,
    )
    return json.loads(diagnostics_json.read_text(encoding="utf-8"))


def build_case(
    config: dict[str, Any],
    candidate: dict[str, Any],
    case_id: str,
    partition: str,
    diagnostics_json: Path,
    ensemble_csv: Path,
) -> dict[str, Any]:
    data_dir = ROOT / "calibration" / "data" / "tschamut"
    release_file = data_dir / f"{partition}_release_points.csv"
    deposition_file = data_dir / f"{partition}_observed_deposition.csv"
    return {
        "case_id": case_id,
        "title": f"Tschamut calibration {partition} {candidate['roughness_profile']}",
        "level": 5,
        "description": "Generated calibration experiment case; not a validation benchmark.",
        "terrain": {
            "type": "plane",
            "parameters": calibration_terrain_parameters(config),
        },
        "block": {"mass": 69.0, "radius": 0.176667},
        "release": {"position": [33.4, 236.67, 72.934936], "velocity": [0.0, 0.0, 0.0]},
        "parameters": {
            "gravity": float(config["fixed_parameters"]["gravity"]),
            "contact_model": config["fixed_parameters"]["contact_model"],
            "roughness_model": config["fixed_parameters"]["roughness_model"],
            "normal_restitution": candidate["normal_restitution"],
            "tangential_restitution": candidate["tangential_restitution"],
            "friction_coefficient": candidate["friction_coefficient"],
            "roughness_std_normal": candidate["roughness_std_normal"],
            "roughness_std_tangent": candidate["roughness_std_tangent"],
            "roughness_std_angle": candidate["roughness_std_angle"],
        },
        "simulation": config["simulation"],
        "random": config["random"],
        "validation_scope": {
            "type": "calibration-partition",
            "note": f"Generated for Tschamut calibration {partition}; not an independent validation case.",
        },
        "observations": {
            "release_points_csv": str(release_file.relative_to(ROOT)),
            "deposition_points_csv": str(deposition_file.relative_to(ROOT)),
        },
        "expected": {
            "metrics": [
                "observed_mean_runout_m",
                "simulated_mean_runout_m",
                "runout_distance_error_m",
                "deposition_centroid_error_m",
                "deposition_cloud_mean_nearest_error_m",
                "lateral_spread_error_m",
                "deposition_cloud_overlap_fraction",
            ],
            "tolerances": {},
        },
        "outputs": {
            "diagnostics_json": str(diagnostics_json.relative_to(ROOT)),
            "ensemble_deposition_csv": str(ensemble_csv.relative_to(ROOT)),
        },
        "references": {"dataset": config["dataset"]["id"], "notes": ["Temporary generated calibration case."]},
}


def calibration_terrain_parameters(config: dict[str, Any]) -> dict[str, float]:
    metadata_path = resolve(config["dataset"]["terrain_metadata_json"])
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    terrain_proxy = metadata["terrain_proxy"]
    return {
        "z0_m": float(terrain_proxy["intercept_m"]),
        "slope_x": float(terrain_proxy["slope_x"]),
        "slope_y": float(terrain_proxy["slope_y"]),
    }


def objective_value(metrics: dict[str, float], config: dict[str, Any]) -> float:
    weights = config["objective"]["weights"]
    normalization_name = config["objective"]["normalization"]
    normalization = max(float(metrics.get(normalization_name, 1.0)), 1.0)
    total = 0.0
    for metric, weight in weights.items():
        total += float(weight) * abs(float(metrics.get(metric, 0.0))) / normalization
    return total


def prefixed_metrics(prefix: str, metrics: dict[str, Any]) -> dict[str, float]:
    wanted = [
        "observed_mean_runout_m",
        "simulated_mean_runout_m",
        "runout_distance_error_m",
        "deposition_centroid_error_m",
        "deposition_cloud_mean_nearest_error_m",
        "lateral_spread_error_m",
        "deposition_cloud_overlap_fraction",
        "validation_release_count",
        "validation_simulated_trajectory_count",
    ]
    return {f"{prefix}_{name}": float(metrics[name]) for name in wanted if name in metrics}


def write_candidate_results(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0])
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_selected_parameters(path: Path, best: dict[str, Any], config: dict[str, Any]) -> None:
    selected = {
        "experiment_id": config["experiment_id"],
        "dataset_id": config["dataset"]["id"],
        "model_version": config["model_version"],
        "selected_candidate_id": best["candidate_id"],
        "calibration_objective": float(best["calibration_objective"]),
        "holdout_objective": float(best["holdout_objective"]),
        "parameters": {
            "normal_restitution": best["normal_restitution"],
            "tangential_restitution": best["tangential_restitution"],
            "friction_coefficient": best["friction_coefficient"],
            "roughness_model": config["fixed_parameters"]["roughness_model"],
            "roughness_std_normal": best["roughness_std_normal"],
            "roughness_std_tangent": best["roughness_std_tangent"],
            "roughness_std_angle": best["roughness_std_angle"],
        },
        "caveat": "Research calibration only; not an operational parameter set.",
    }
    write_yaml(path, selected)


def write_summary(path: Path, rows: list[dict[str, Any]], config: dict[str, Any]) -> None:
    best = rows[0]
    summary = {
        "experiment_id": config["experiment_id"],
        "title": config["title"],
        "model_version": config["model_version"],
        "dataset": config["dataset"],
        "split": load_yaml(resolve(config["split"]["path"])),
        "objective": config["objective"],
        "seed": config["random"]["seed"],
        "candidate_count": len(rows),
        "generated_utc": None,
        "best_candidate": best,
        "top_candidates": rows[:5],
        "interpretation": (
            "The selected set minimizes the calibration subset objective in a small explicit grid. "
            "Holdout performance must be interpreted as a research diagnostic, not predictive skill."
        ),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_html_report(path: Path, rows: list[dict[str, Any]], config: dict[str, Any]) -> None:
    best = rows[0]
    table_rows = []
    for row in rows:
        table_rows.append(
            "<tr>"
            f"<td>{escape(row['candidate_id'])}</td>"
            f"<td>{float(row['calibration_objective']):.4f}</td>"
            f"<td>{float(row['holdout_objective']):.4f}</td>"
            f"<td>{float(row['normal_restitution']):.2f}</td>"
            f"<td>{float(row['tangential_restitution']):.2f}</td>"
            f"<td>{float(row['friction_coefficient']):.2f}</td>"
            f"<td>{escape(row['roughness_profile'])}</td>"
            f"<td>{float(row['calibration_runout_distance_error_m']):.2f}</td>"
            f"<td>{float(row['holdout_runout_distance_error_m']):.2f}</td>"
            "</tr>"
        )
    html_text = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{escape(config['title'])}</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 32px; line-height: 1.45; color: #111827; }}
    table {{ border-collapse: collapse; width: 100%; font-size: 0.9rem; }}
    th, td {{ border-bottom: 1px solid #d9e1ea; padding: 7px 9px; text-align: left; }}
    th {{ background: #eef3f8; }}
    .notice {{ background: #f3f7fb; border: 1px solid #cfdbe7; padding: 12px; border-radius: 8px; }}
    code {{ font-family: "SFMono-Regular", Consolas, monospace; }}
  </style>
</head>
<body>
  <h1>{escape(config['title'])}</h1>
  <p class="notice">Research calibration only. This is dataset-specific, uses a limited v0.3.0 spherical model and proxy terrain, and is not calibrated for operational use.</p>
  <h2>Selected Candidate</h2>
  <p><code>{escape(best['candidate_id'])}</code>: objective {float(best['calibration_objective']):.4f} on calibration, {float(best['holdout_objective']):.4f} on held-out data.</p>
  <h2>Candidate Grid</h2>
  <table>
    <thead><tr><th>ID</th><th>Calibration Obj.</th><th>Holdout Obj.</th><th>e_n</th><th>e_t</th><th>mu</th><th>Roughness</th><th>Cal. Runout Err.</th><th>Holdout Runout Err.</th></tr></thead>
    <tbody>{''.join(table_rows)}</tbody>
  </table>
</body>
</html>
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html_text, encoding="utf-8")


def escape(value: Any) -> str:
    return html.escape(str(value), quote=False)


if __name__ == "__main__":
    sys.exit(main())
