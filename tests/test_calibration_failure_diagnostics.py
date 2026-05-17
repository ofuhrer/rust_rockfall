from __future__ import annotations

import csv
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import yaml

from scripts import calibrate_scarring_impact as scarring
from scripts import preprocess_scarring_real_data as preprocess
from scripts import run_tschamut_calibration as tschamut


class CalibrationFailureDiagnosticsTest(unittest.TestCase):
    def _write_csv(self, path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    def _write_yaml(self, path: Path, data: dict[str, object]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")

    def test_tschamut_prepare_split_reports_empty_release_and_deposition_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config_path = root / "config.yaml"
            split_path = root / "calibration/data/tschamut/split.yaml"
            release_path = root / "data/processed/tschamut2014/release_points.csv"
            deposition_path = root / "data/processed/tschamut2014/deposition_points.csv"

            self._write_csv(release_path, ["trajectory_id", "block_id"], [])
            self._write_csv(
                deposition_path,
                ["trajectory_id", "block_id"],
                [{"trajectory_id": "t1", "block_id": "b1"}],
            )
            self._write_yaml(
                config_path,
                {
                    "dataset": {
                        "id": "tschamut2014",
                        "doi": "https://doi.example/tschamut",
                        "release_points_csv": "data/processed/tschamut2014/release_points.csv",
                        "deposition_points_csv": "data/processed/tschamut2014/deposition_points.csv",
                    },
                    "split": {
                        "path": "calibration/data/tschamut/split.yaml",
                        "seed": 70314,
                        "calibration_per_block": 1,
                        "holdout_per_block": 1,
                    },
                },
            )

            with mock.patch.object(tschamut, "ROOT", root):
                config = tschamut.load_yaml(config_path)
                with self.assertRaisesRegex(SystemExit, r"split preparation: release CSV .* has no rows"):
                    tschamut.prepare_split(config)

            self.assertFalse(split_path.exists())

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config_path = root / "config.yaml"
            split_path = root / "calibration/data/tschamut/split.yaml"
            release_path = root / "data/processed/tschamut2014/release_points.csv"
            deposition_path = root / "data/processed/tschamut2014/deposition_points.csv"

            self._write_csv(
                release_path,
                ["trajectory_id", "block_id"],
                [{"trajectory_id": "t1", "block_id": "b1"}],
            )
            self._write_csv(deposition_path, ["trajectory_id", "block_id"], [])
            self._write_yaml(
                config_path,
                {
                    "dataset": {
                        "id": "tschamut2014",
                        "doi": "https://doi.example/tschamut",
                        "release_points_csv": "data/processed/tschamut2014/release_points.csv",
                        "deposition_points_csv": "data/processed/tschamut2014/deposition_points.csv",
                    },
                    "split": {
                        "path": "calibration/data/tschamut/split.yaml",
                        "seed": 70314,
                        "calibration_per_block": 1,
                        "holdout_per_block": 1,
                    },
                },
            )

            with mock.patch.object(tschamut, "ROOT", root):
                config = tschamut.load_yaml(config_path)
                with self.assertRaisesRegex(SystemExit, r"split preparation: deposition CSV .* has no rows"):
                    tschamut.prepare_split(config)

            self.assertFalse(split_path.exists())

    def test_tschamut_reports_empty_candidate_rows_before_writing_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidate_results = root / "calibration/experiments/tschamut_v0_3/candidate_results.csv"

            with mock.patch.object(tschamut, "ROOT", root):
                with self.assertRaisesRegex(
                    SystemExit,
                    r"candidate result writing: no candidate rows are available",
                ):
                    tschamut.write_candidate_results(candidate_results, [])

    def test_tschamut_reports_empty_parameter_grid(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config_path = root / "config.yaml"
            self._write_yaml(
                config_path,
                {
                    "outputs": {
                        "generated_results_dir": "calibration/results/tschamut_v0_3",
                        "candidate_results_csv": "calibration/experiments/tschamut_v0_3/candidate_results.csv",
                        "selected_parameters_yaml": "calibration/experiments/tschamut_v0_3/selected_parameters.yaml",
                        "summary_json": "calibration/experiments/tschamut_v0_3/summary.json",
                        "report_html": "calibration/experiments/tschamut_v0_3/report.html",
                    },
                    "parameter_grid": {
                        "normal_restitution": [],
                        "tangential_restitution": [],
                        "friction_coefficient": [],
                        "roughness_profile": [],
                    },
                },
            )

            with mock.patch.object(tschamut, "ROOT", root):
                config = tschamut.load_yaml(config_path)
                with self.assertRaisesRegex(
                    SystemExit,
                    r"parameter grid evaluation: parameter_grid is empty for",
                ):
                    tschamut.run_experiment(config)

    def test_tschamut_wraps_failed_validation_subprocess(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config_path = root / "config.yaml"
            metadata_path = root / "data/processed/tschamut2014/metadata.json"
            metadata_path.parent.mkdir(parents=True, exist_ok=True)
            metadata_path.write_text(
                json.dumps({"terrain_proxy": {"intercept_m": 1.0, "slope_x": 0.0, "slope_y": 0.0}}),
                encoding="utf-8",
            )
            self._write_yaml(
                config_path,
                {
                    "dataset": {
                        "id": "tschamut2014",
                        "terrain_metadata_json": "data/processed/tschamut2014/metadata.json",
                    },
                    "fixed_parameters": {
                        "gravity": 9.81,
                        "contact_model": "translational_v0",
                        "roughness_model": "stochastic_contact_v1",
                    },
                    "simulation": {"dt": 0.02, "t_max": 18.0, "stop_velocity": 0.1},
                    "random": {"seed": 43030},
                },
            )

            candidate = {
                "normal_restitution": 0.25,
                "tangential_restitution": 0.85,
                "friction_coefficient": 0.2,
                "roughness_profile": "low",
                "roughness_std_normal": 0.04,
                "roughness_std_tangent": 0.04,
                "roughness_std_angle": 0.04,
            }
            case_dir = root / "calibration/results/tschamut_v0_3/cases"
            report_dir = root / "calibration/results/tschamut_v0_3/reports"

            with mock.patch.object(tschamut, "ROOT", root), mock.patch.object(
                tschamut.subprocess,
                "run",
                side_effect=subprocess.CalledProcessError(1, ["cargo"], stderr="boom\n"),
            ):
                config = tschamut.load_yaml(config_path)
                with self.assertRaisesRegex(
                    SystemExit,
                    r"validation subprocess: cargo run failed for .* exit code 1: boom",
                ):
                    tschamut.evaluate_candidate(
                        config,
                        candidate,
                        "candidate_000",
                        "calibration",
                        case_dir,
                        report_dir,
                    )

    def test_scarring_reports_empty_parameter_grid(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config_path = root / "config.yaml"
            impacts_csv = root / "calibration/data/scarring_single_impact/reference_impacts.csv"
            self._write_csv(
                impacts_csv,
                [
                    "impact_id",
                    "mass_kg",
                    "radius_m",
                    "incoming_normal_speed_mps",
                    "incoming_tangent_speed_mps",
                    "observed_scarring_depth_m",
                    "observed_scarring_energy_loss_j",
                    "observed_post_rebound_translational_j",
                    "observed_total_translational_energy_loss_j",
                ],
                [
                    {
                        "impact_id": "impact_001",
                        "mass_kg": 780.0,
                        "radius_m": 0.45,
                        "incoming_normal_speed_mps": 0.5,
                        "incoming_tangent_speed_mps": 0.1,
                        "observed_scarring_depth_m": 0.03,
                        "observed_scarring_energy_loss_j": 12.0,
                        "observed_post_rebound_translational_j": 34.0,
                        "observed_total_translational_energy_loss_j": 46.0,
                    }
                ],
            )
            self._write_yaml(
                config_path,
                {
                    "dataset": {"path": "calibration/data/scarring_single_impact/reference_impacts.csv"},
                    "outputs": {
                        "generated_results_dir": "calibration/results/scarring_single_impact_v0_4",
                        "candidate_results_csv": "calibration/experiments/scarring_single_impact_v0_4/candidate_results.csv",
                        "selected_parameters_yaml": "calibration/experiments/scarring_single_impact_v0_4/selected_parameters.yaml",
                        "summary_json": "calibration/experiments/scarring_single_impact_v0_4/summary.json",
                        "report_html": "calibration/experiments/scarring_single_impact_v0_4/report.html",
                    },
                    "parameter_grid": {
                        "soil_strength_pa": [],
                        "scarring_drag_coefficient": [],
                        "scarring_layer_density_kgpm3": [],
                    },
                },
            )

            with mock.patch.object(scarring, "ROOT", root):
                config = scarring.load_yaml(config_path)
                with self.assertRaisesRegex(
                    SystemExit,
                    r"parameter grid evaluation: parameter_grid is empty for",
                ):
                    scarring.run_experiment(config)

    def test_scarring_reports_missing_significant_impact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config_path = root / "config.yaml"
            self._write_yaml(
                config_path,
                {
                    "simulation": {"dt": 0.001, "t_max": 0.004, "stop_velocity": 0.0},
                    "random": {"seed": 4104},
                    "fixed_parameters": {
                        "gravity": 9.81,
                        "normal_restitution": 0.4,
                        "tangential_restitution": 0.85,
                        "friction_coefficient": 0.4,
                        "contact_model": "translational_v0",
                        "soil_interaction_model": "scarring_contact_v1",
                    },
                },
            )
            candidate = {
                "soil_strength_pa": 250000.0,
                "scarring_drag_coefficient": 0.005,
                "scarring_layer_density_kgpm3": 1200.0,
            }
            impact = {
                "impact_id": "impact_001",
                "mass_kg": 780.0,
                "radius_m": 0.45,
                "incoming_normal_speed_mps": 0.5,
                "incoming_tangent_speed_mps": 0.1,
                "observed_scarring_depth_m": 0.03,
                "observed_scarring_energy_loss_j": 12.0,
                "observed_post_rebound_translational_j": 34.0,
                "observed_total_translational_energy_loss_j": 46.0,
            }

            def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
                impact_events_path = Path(command[command.index("--impact-events-json") + 1])
                impact_events_path.parent.mkdir(parents=True, exist_ok=True)
                impact_events_path.write_text(
                    json.dumps(
                        [
                            {
                                "incoming_normal_speed_mps": 0.01,
                                "scarring_depth_m": 0.0,
                                "scarring_capped_energy_loss_j": 0.0,
                                "post_scarring_translational_j": 0.0,
                                "post_contact_translational_j": 0.0,
                            }
                        ]
                    ),
                    encoding="utf-8",
                )
                return subprocess.CompletedProcess(command, 0)

            with mock.patch.object(scarring, "ROOT", root), mock.patch.object(
                scarring.subprocess,
                "run",
                side_effect=fake_run,
            ):
                config = scarring.load_yaml(config_path)
                config_dir = root / "calibration/results/scarring_single_impact_v0_4/configs"
                event_dir = root / "calibration/results/scarring_single_impact_v0_4/impact_events"
                trajectory_dir = root / "calibration/results/scarring_single_impact_v0_4/trajectories"
                for directory in (config_dir, event_dir, trajectory_dir):
                    directory.mkdir(parents=True, exist_ok=True)
                with self.assertRaisesRegex(
                    SystemExit,
                    r"impact event filtering: .* produced no significant impact events",
                ):
                    scarring.simulate_impact(
                        config,
                        candidate,
                        impact,
                        "candidate_000",
                        config_dir,
                        event_dir,
                        trajectory_dir,
                    )

    def test_scarring_wraps_failed_cargo_subprocess(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config_path = root / "config.yaml"
            self._write_yaml(
                config_path,
                {
                    "simulation": {"dt": 0.001, "t_max": 0.004, "stop_velocity": 0.0},
                    "random": {"seed": 4104},
                    "fixed_parameters": {
                        "gravity": 9.81,
                        "normal_restitution": 0.4,
                        "tangential_restitution": 0.85,
                        "friction_coefficient": 0.4,
                        "contact_model": "translational_v0",
                        "soil_interaction_model": "scarring_contact_v1",
                    },
                },
            )
            candidate = {
                "soil_strength_pa": 250000.0,
                "scarring_drag_coefficient": 0.005,
                "scarring_layer_density_kgpm3": 1200.0,
            }
            impact = {
                "impact_id": "impact_001",
                "mass_kg": 780.0,
                "radius_m": 0.45,
                "incoming_normal_speed_mps": 0.5,
                "incoming_tangent_speed_mps": 0.1,
                "observed_scarring_depth_m": 0.03,
                "observed_scarring_energy_loss_j": 12.0,
                "observed_post_rebound_translational_j": 34.0,
                "observed_total_translational_energy_loss_j": 46.0,
            }

            with mock.patch.object(scarring, "ROOT", root), mock.patch.object(
                scarring.subprocess,
                "run",
                side_effect=subprocess.CalledProcessError(2, ["cargo"], stderr="sim crash\n"),
            ):
                config = scarring.load_yaml(config_path)
                config_dir = root / "calibration/results/scarring_single_impact_v0_4/configs"
                event_dir = root / "calibration/results/scarring_single_impact_v0_4/impact_events"
                trajectory_dir = root / "calibration/results/scarring_single_impact_v0_4/trajectories"
                for directory in (config_dir, event_dir, trajectory_dir):
                    directory.mkdir(parents=True, exist_ok=True)
                with self.assertRaisesRegex(
                    SystemExit,
                    r"impact simulation: cargo run failed for candidate_000_impact_001 with exit code 2: sim crash",
                ):
                    scarring.simulate_impact(
                        config,
                        candidate,
                        impact,
                        "candidate_000",
                        config_dir,
                        event_dir,
                        trajectory_dir,
                    )

    def test_preprocess_reports_missing_source_rows_and_required_inputs(self) -> None:
        with mock.patch.object(preprocess, "read_xlsx_rows", return_value=[]):
            with self.assertRaisesRegex(SystemExit, r"scar table parsing: scar table .* has no rows"):
                preprocess.read_scar_table(Path("scar_dimensions.xlsx"))
            with self.assertRaisesRegex(SystemExit, r"trajectory table parsing: trajectory table .* has no rows"):
                preprocess.read_trajectory_table(Path("trajectory_sections.xlsx"))

        with self.assertRaisesRegex(
            SystemExit,
            r"real-data preprocessing: missing required input '21' for transition 21->22 and scar 2\.1",
        ):
            preprocess.build_rows({}, {}, {})


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
