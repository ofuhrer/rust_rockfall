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
    parser.add_argument(
        "--describe-objective",
        action="store_true",
        help="write the executable calibration objective contract and exit without running candidates",
    )
    parser.add_argument(
        "--refresh-summary-only",
        action="store_true",
        help="rewrite selected parameters, summary JSON, and HTML from existing candidate and ensemble outputs",
    )
    parser.add_argument(
        "--objective-json-output",
        type=Path,
        default=None,
        help="optional objective-contract JSON output path; defaults to the config output path",
    )
    args = parser.parse_args()

    config = load_yaml(resolve(args.config))
    if args.describe_objective:
        output_path = args.objective_json_output
        if output_path is None:
            output_path = Path(objective_contract_output_path(config))
        contract = write_objective_contract(resolve(output_path), config)
        print(json.dumps(contract, indent=2, sort_keys=True))
        return 0
    prepare_split(config)
    if args.prepare_only:
        print("prepared calibration split")
        return 0
    if args.refresh_summary_only:
        refresh_summaries_from_existing_outputs(config)
        print("refreshed calibration summaries")
        return 0
    run_experiment(config)
    return 0


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml  # type: ignore
    except ImportError as exc:
        raise SystemExit(
            "PyYAML is required. From the repo root, run "
            "`PYENV_VERSION=system uv run python scripts/run_tschamut_calibration.py ...`. "
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
            "`PYENV_VERSION=system uv run python scripts/run_tschamut_calibration.py ...`. "
            "CI may install `requirements-tools.txt` with system Python instead."
        ) from exc
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
    if not releases:
        raise stage_error(
            "split preparation",
            f"release CSV {dataset['release_points_csv']} has no rows",
        )
    if not depositions:
        raise stage_error(
            "split preparation",
            f"deposition CSV {dataset['deposition_points_csv']} has no rows",
        )
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
    missing = sorted(set(calibration_ids + holdout_ids) - set(deposition_by_id))
    if missing:
        raise stage_error(
            "split preparation",
            f"deposition CSV {dataset['deposition_points_csv']} is missing trajectory_id rows for {missing}",
        )
    split_path = resolve(split_cfg["path"])
    write_yaml(split_path, split)

    out_dir = split_path.parent
    write_subset_csv(
        out_dir / "calibration_release_points.csv",
        releases,
        calibration_ids,
        stage="split preparation",
        source_label=f"release CSV {dataset['release_points_csv']}",
    )
    write_subset_csv(
        out_dir / "calibration_observed_deposition.csv",
        depositions,
        calibration_ids,
        stage="split preparation",
        source_label=f"deposition CSV {dataset['deposition_points_csv']}",
    )
    write_subset_csv(
        out_dir / "holdout_release_points.csv",
        releases,
        holdout_ids,
        stage="split preparation",
        source_label=f"release CSV {dataset['release_points_csv']}",
    )
    write_subset_csv(
        out_dir / "holdout_observed_deposition.csv",
        depositions,
        holdout_ids,
        stage="split preparation",
        source_label=f"deposition CSV {dataset['deposition_points_csv']}",
    )


def stable_key(seed: int, block_id: str, trajectory_id: str) -> str:
    text = f"{seed}:{block_id}:{trajectory_id}".encode("utf-8")
    return hashlib.sha256(text).hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def write_subset_csv(
    path: Path,
    rows: list[dict[str, str]],
    selected_ids: list[str],
    *,
    stage: str,
    source_label: str,
) -> None:
    if not rows:
        raise stage_error(stage, f"{source_label} is empty")
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
    if not candidates:
        raise stage_error("parameter grid evaluation", "parameter_grid produced no candidates")
    write_objective_contract(resolve(objective_contract_output_path(config)), config)
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
    if not rows:
        raise stage_error("candidate evaluation", "parameter_grid produced no candidate rows")
    write_candidate_results(resolve(config["outputs"]["candidate_results_csv"]), rows)
    write_selected_parameters(resolve(config["outputs"]["selected_parameters_yaml"]), rows[0], config)
    write_summary(resolve(config["outputs"]["summary_json"]), rows, config)
    write_html_report(resolve(config["outputs"]["report_html"]), rows, config)


def refresh_summaries_from_existing_outputs(config: dict[str, Any]) -> None:
    rows = read_candidate_results(resolve(config["outputs"]["candidate_results_csv"]))
    if not rows:
        raise stage_error("summary refresh", "candidate_results_csv produced no candidate rows")
    rows.sort(key=lambda row: (float(row["calibration_objective"]), float(row["holdout_objective"])))
    write_selected_parameters(resolve(config["outputs"]["selected_parameters_yaml"]), rows[0], config)
    write_summary(resolve(config["outputs"]["summary_json"]), rows, config)
    write_html_report(resolve(config["outputs"]["report_html"]), rows, config)


def read_candidate_results(path: Path) -> list[dict[str, Any]]:
    numeric_fields = {
        "normal_restitution",
        "tangential_restitution",
        "friction_coefficient",
        "roughness_std_normal",
        "roughness_std_tangent",
        "roughness_std_angle",
        "calibration_objective",
        "holdout_objective",
        "calibration_observed_mean_runout_m",
        "calibration_simulated_mean_runout_m",
        "calibration_runout_distance_error_m",
        "calibration_deposition_centroid_error_m",
        "calibration_deposition_cloud_mean_nearest_error_m",
        "calibration_lateral_spread_error_m",
        "calibration_deposition_cloud_overlap_fraction",
        "holdout_observed_mean_runout_m",
        "holdout_simulated_mean_runout_m",
        "holdout_runout_distance_error_m",
        "holdout_deposition_centroid_error_m",
        "holdout_deposition_cloud_mean_nearest_error_m",
        "holdout_lateral_spread_error_m",
        "holdout_deposition_cloud_overlap_fraction",
        "calibration_validation_release_count",
        "calibration_validation_simulated_trajectory_count",
        "holdout_validation_release_count",
        "holdout_validation_simulated_trajectory_count",
    }
    rows = []
    for row in read_csv(path):
        normalized: dict[str, Any] = dict(row)
        for field in numeric_fields & set(normalized):
            normalized[field] = float(normalized[field])
        rows.append(normalized)
    return rows


def write_objective_contract(path: Path, config: dict[str, Any]) -> dict[str, Any]:
    contract = build_objective_contract(config)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(contract, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return contract


def build_objective_contract(config: dict[str, Any]) -> dict[str, Any]:
    split = load_yaml(resolve(config["split"]["path"]))
    candidates = parameter_candidates(config)
    objective = config["objective"]
    weights = dict(objective["weights"])
    metric_names = list(weights)
    outputs = config["outputs"]
    return {
        "schema_version": "tschamut_calibration_objective_v1",
        "objective_status": "executable_smoke_ready",
        "experiment_id": config["experiment_id"],
        "title": config["title"],
        "model_version": config["model_version"],
        "dataset": config["dataset"],
        "training_data": {
            "partition": "calibration",
            "release_points_csv": "calibration/data/tschamut/calibration_release_points.csv",
            "observed_deposition_csv": "calibration/data/tschamut/calibration_observed_deposition.csv",
            "trajectory_ids": split.get("calibration_ids", []),
            "trajectory_count": len(split.get("calibration_ids", [])),
        },
        "excluded_holdout_data": {
            "partition": "holdout",
            "release_points_csv": "calibration/data/tschamut/holdout_release_points.csv",
            "observed_deposition_csv": "calibration/data/tschamut/holdout_observed_deposition.csv",
            "trajectory_ids": split.get("holdout_ids", []),
            "trajectory_count": len(split.get("holdout_ids", [])),
            "use_for_fitting": False,
        },
        "split": {
            "path": config["split"]["path"],
            "method": split.get("method", ""),
            "seed": split.get("seed", config["split"]["seed"]),
            "intersection_size": (split.get("leakage_check") or {}).get("intersection_size"),
        },
        "parameters": {
            "fixed": config["fixed_parameters"],
            "grid": config["parameter_grid"],
            "candidate_count": len(candidates),
        },
        "objective": {
            "direction": "lower_is_better",
            "description": objective.get("description", ""),
            "normalization_metric": objective["normalization"],
            "metric_weights": weights,
            "formula_terms": [
                {
                    "metric": metric,
                    "weight": float(weight),
                    "normalization_metric": objective["normalization"],
                }
                for metric, weight in weights.items()
            ],
        },
        "metrics": metric_names,
        "expected_output_artifacts": {
            "candidate_results_csv": outputs["candidate_results_csv"],
            "selected_parameters_yaml": outputs["selected_parameters_yaml"],
            "summary_json": outputs["summary_json"],
            "report_html": outputs["report_html"],
            "objective_contract_json": objective_contract_output_path(config),
            "generated_results_dir": outputs["generated_results_dir"],
        },
        "dry_run_command": (
            "PYENV_VERSION=system uv run python scripts/run_tschamut_calibration.py "
            "--describe-objective"
        ),
        "smoke_run_command": (
            "PYENV_VERSION=system uv run python scripts/run_tschamut_calibration.py "
            "--config calibration/experiments/tschamut_v0_3/config.yaml"
        ),
        "claim_boundary": {
            "calibration_claim_supported": False,
            "validation_acceptance_claimed": False,
            "physical_probability_supported": False,
            "annual_frequency_supported": False,
            "operational_hazard_map_supported": False,
            "selected_parameters_promoted_to_validation": False,
        },
    }


def objective_contract_output_path(config: dict[str, Any]) -> str:
    outputs = config.get("outputs") or {}
    return str(outputs.get("objective_contract_json") or "calibration/experiments/tschamut_v0_3/objective_contract.json")


def parameter_candidates(config: dict[str, Any]) -> list[dict[str, Any]]:
    grid = config["parameter_grid"]
    grid_axes = {
        "normal_restitution": grid.get("normal_restitution", []),
        "tangential_restitution": grid.get("tangential_restitution", []),
        "friction_coefficient": grid.get("friction_coefficient", []),
        "roughness_profile": grid.get("roughness_profile", []),
    }
    missing = [name for name, values in grid_axes.items() if not values]
    if missing:
        raise stage_error(
            "parameter grid evaluation",
            f"parameter_grid is empty for {', '.join(missing)}",
        )
    candidates = []
    for normal, tangential, friction, roughness in itertools.product(
        grid_axes["normal_restitution"],
        grid_axes["tangential_restitution"],
        grid_axes["friction_coefficient"],
        grid_axes["roughness_profile"],
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
    try:
        subprocess.run(
            ["cargo", "run", "-q", "--", "validate", "--case", str(case_path)],
            cwd=ROOT,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        detail = f"cargo run failed for {case_path} with exit code {exc.returncode}"
        if stderr:
            detail = f"{detail}: {stderr.splitlines()[-1]}"
        raise stage_error("validation subprocess", detail) from exc
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
    if not rows:
        raise stage_error("candidate result writing", f"no candidate rows are available for {path}")
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
    if not rows:
        raise stage_error("summary writing", f"no candidate rows are available for {path}")
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
        "parameter_sensitivity": summarize_parameter_sensitivity(rows),
        "residual_diagnostics": build_residual_diagnostics(best["candidate_id"], config),
        "interpretation": (
            "The selected set minimizes the calibration subset objective in an explicit local grid. "
            "Holdout performance must be interpreted as a research diagnostic, not predictive skill."
        ),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def summarize_parameter_sensitivity(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {"status": "no_candidate_rows"}
    parameter_names = [
        "normal_restitution",
        "tangential_restitution",
        "friction_coefficient",
        "roughness_profile",
    ]
    effects = []
    for parameter in parameter_names:
        groups: dict[str, list[dict[str, Any]]] = {}
        for row in rows:
            groups.setdefault(str(row[parameter]), []).append(row)
        levels = []
        for value, group_rows in sorted(groups.items()):
            levels.append(
                {
                    "value": value,
                    "candidate_count": len(group_rows),
                    "mean_calibration_objective": mean_float(group_rows, "calibration_objective"),
                    "mean_holdout_objective": mean_float(group_rows, "holdout_objective"),
                    "best_calibration_objective": min(float(row["calibration_objective"]) for row in group_rows),
                    "best_candidate_id": min(
                        group_rows,
                        key=lambda row: (float(row["calibration_objective"]), float(row["holdout_objective"])),
                    )["candidate_id"],
                }
            )
        means = [float(level["mean_calibration_objective"]) for level in levels]
        effects.append(
            {
                "parameter": parameter,
                "levels": levels,
                "mean_calibration_objective_range": max(means) - min(means) if means else 0.0,
                "lower_is_better": True,
            }
        )
    strongest = max(effects, key=lambda item: float(item["mean_calibration_objective_range"]))
    best = rows[0]
    worst = max(rows, key=lambda row: float(row["calibration_objective"]))
    return {
        "schema_version": "tschamut_calibration_parameter_sensitivity_v1",
        "status": "measured",
        "strongest_mean_effect_parameter": strongest["parameter"],
        "strongest_mean_effect_range": strongest["mean_calibration_objective_range"],
        "best_candidate_id": best["candidate_id"],
        "best_calibration_objective": float(best["calibration_objective"]),
        "best_holdout_objective": float(best["holdout_objective"]),
        "worst_candidate_id": worst["candidate_id"],
        "worst_calibration_objective": float(worst["calibration_objective"]),
        "calibration_objective_span": float(worst["calibration_objective"]) - float(best["calibration_objective"]),
        "effects": effects,
        "interpretation": (
            f"{strongest['parameter']} has the largest mean objective separation across the explicit grid. "
            "The result is a bounded sensitivity smoke, not a validation acceptance claim."
        ),
    }


def mean_float(rows: list[dict[str, Any]], field: str) -> float:
    return sum(float(row[field]) for row in rows) / max(len(rows), 1)


def build_residual_diagnostics(candidate_id: str, config: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "tschamut_calibration_residual_diagnostics_v1",
        "candidate_id": candidate_id,
        "calibration": residual_diagnostics_for_partition(candidate_id, "calibration", config),
        "holdout": residual_diagnostics_for_partition(candidate_id, "holdout", config),
        "interpretation": (
            "Residual diagnostics compare per-trajectory observed deposition/runout rows with "
            "the selected candidate's ensemble mean endpoint for the same release_id."
        ),
    }


def residual_diagnostics_for_partition(candidate_id: str, partition: str, config: dict[str, Any]) -> dict[str, Any]:
    result_dir = resolve(config["outputs"]["generated_results_dir"])
    ensemble_path = result_dir / "reports" / f"calibration_tschamut_{partition}_{candidate_id}_ensemble_deposition.csv"
    observed_path = ROOT / "calibration" / "data" / "tschamut" / f"{partition}_observed_deposition.csv"
    if not ensemble_path.exists():
        return {
            "status": "missing_ensemble_deposition_csv",
            "partition": partition,
            "candidate_id": candidate_id,
            "path": str(ensemble_path.relative_to(ROOT)) if ensemble_path.is_relative_to(ROOT) else str(ensemble_path),
        }
    if not observed_path.exists():
        return {
            "status": "missing_observed_deposition_csv",
            "partition": partition,
            "candidate_id": candidate_id,
            "path": str(observed_path.relative_to(ROOT)) if observed_path.is_relative_to(ROOT) else str(observed_path),
        }
    observed_by_id = {row["trajectory_id"]: row for row in read_csv(observed_path)}
    ensemble_by_release: dict[str, list[dict[str, str]]] = {}
    for row in read_csv(ensemble_path):
        ensemble_by_release.setdefault(row["release_id"], []).append(row)

    residual_rows = []
    missing_observed_ids = []
    for release_id, ensemble_rows in sorted(ensemble_by_release.items()):
        observed = observed_by_id.get(release_id)
        if observed is None:
            missing_observed_ids.append(release_id)
            continue
        mean_x = mean_numeric(ensemble_rows, "x_m")
        mean_y = mean_numeric(ensemble_rows, "y_m")
        mean_z = mean_numeric(ensemble_rows, "z_m")
        simulated_runout = mean_numeric(ensemble_rows, "runout_m")
        observed_runout = float(observed["observed_runout_m"])
        runout_residual = simulated_runout - observed_runout
        endpoint_distance = euclidean_distance(
            (mean_x, mean_y, mean_z),
            (float(observed["x_m"]), float(observed["y_m"]), float(observed["z_m"])),
        )
        residual_rows.append(
            {
                "trajectory_id": release_id,
                "ensemble_member_count": len(ensemble_rows),
                "observed_runout_m": observed_runout,
                "simulated_mean_runout_m": simulated_runout,
                "runout_residual_m": runout_residual,
                "runout_abs_error_m": abs(runout_residual),
                "endpoint_distance_m": endpoint_distance,
                "simulated_mean_x_m": mean_x,
                "simulated_mean_y_m": mean_y,
                "simulated_mean_z_m": mean_z,
                "observed_x_m": float(observed["x_m"]),
                "observed_y_m": float(observed["y_m"]),
                "observed_z_m": float(observed["z_m"]),
            }
        )

    if not residual_rows:
        return {
            "status": "no_matching_residual_rows",
            "partition": partition,
            "candidate_id": candidate_id,
            "missing_observed_ids": missing_observed_ids,
        }

    return {
        "status": "measured",
        "partition": partition,
        "candidate_id": candidate_id,
        "trajectory_count": len(residual_rows),
        "ensemble_member_count": sum(int(row["ensemble_member_count"]) for row in residual_rows),
        "missing_observed_ids": missing_observed_ids,
        "summaries": {
            "runout_residual_m": summarize_values([float(row["runout_residual_m"]) for row in residual_rows]),
            "runout_abs_error_m": summarize_values([float(row["runout_abs_error_m"]) for row in residual_rows]),
            "endpoint_distance_m": summarize_values([float(row["endpoint_distance_m"]) for row in residual_rows]),
        },
        "worst_cases": {
            "runout_abs_error_m": top_residual_cases(residual_rows, "runout_abs_error_m"),
            "endpoint_distance_m": top_residual_cases(residual_rows, "endpoint_distance_m"),
        },
    }


def mean_numeric(rows: list[dict[str, str]], field: str) -> float:
    return sum(float(row[field]) for row in rows) / max(len(rows), 1)


def euclidean_distance(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    return sum((left - right) ** 2 for left, right in zip(a, b)) ** 0.5


def summarize_values(values: list[float]) -> dict[str, float | int | None]:
    if not values:
        return {"count": 0, "mean": None, "median": None, "min": None, "max": None}
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        median = ordered[middle]
    else:
        median = (ordered[middle - 1] + ordered[middle]) / 2.0
    return {
        "count": len(ordered),
        "mean": sum(ordered) / len(ordered),
        "median": median,
        "min": ordered[0],
        "max": ordered[-1],
    }


def top_residual_cases(rows: list[dict[str, Any]], field: str, *, limit: int = 5) -> list[dict[str, Any]]:
    return [
        {
            "trajectory_id": row["trajectory_id"],
            "ensemble_member_count": row["ensemble_member_count"],
            "observed_runout_m": row["observed_runout_m"],
            "simulated_mean_runout_m": row["simulated_mean_runout_m"],
            "runout_residual_m": row["runout_residual_m"],
            "runout_abs_error_m": row["runout_abs_error_m"],
            "endpoint_distance_m": row["endpoint_distance_m"],
        }
        for row in sorted(rows, key=lambda item: float(item[field]), reverse=True)[:limit]
    ]


def write_html_report(path: Path, rows: list[dict[str, Any]], config: dict[str, Any]) -> None:
    if not rows:
        raise stage_error("report generation", f"no candidate rows are available for {path}")
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


def stage_error(stage: str, message: str) -> SystemExit:
    return SystemExit(f"{stage}: {message}")


if __name__ == "__main__":
    sys.exit(main())
