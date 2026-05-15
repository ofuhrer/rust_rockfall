from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import summarize_same_scale_sampling_uncertainty as summary


class SameScaleSamplingUncertaintyTests(unittest.TestCase):
    def test_sampling_uncertainty_summary_from_four_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            manifests = [
                self._make_artifact(tmp, "gate_v1", seed=34013, mode="full", validation_files=2, hazard_files=3),
                self._make_artifact(tmp, "target_gate_v1", seed=34014, mode="full", validation_files=3, hazard_files=4),
                self._make_artifact(tmp, "sampling_sensitivity_v1_full", seed=34014, mode="full", validation_files=4, hazard_files=5),
                self._make_artifact(tmp, "sampling_sensitivity_v2_full", seed=34015, mode="full", validation_files=5, hazard_files=6),
            ]

            with patch.object(summary, "compare_manifest_pair", side_effect=lambda ref, cand: self._fake_compare(ref, cand)):
                report = summary.build_sampling_uncertainty_summary(manifests)

        expected_keys = {
            "schema_version",
            "sampling_uncertainty_status",
            "readiness_status",
            "artifacts_included",
            "artifact_ids",
            "case_ids",
            "seeds_or_splits",
            "ensemble_sizes",
            "validation_output_modes",
            "output_file_counts",
            "output_byte_counts",
            "hazard_output_file_counts",
            "hazard_output_byte_counts",
            "comparison_pairs_run",
            "pairwise_comparison_count",
            "shared_cellwise_layer_counts",
            "dominant_layer_spread",
            "max_kinetic_energy_uncertainty",
            "max_jump_height_uncertainty",
            "velocity_exceedance_uncertainty",
            "support_or_nodata_sensitivity",
            "uncertainty_reduced",
            "remaining_uncertainty",
            "defaults_changed",
            "physics_changed",
            "thresholds_changed",
            "source_or_scenario_inputs_changed",
            "target_convergence_interpretation",
            "scale_up_authorized",
            "operational_claims_allowed",
            "comparison_status",
            "interpretation",
            "blocked_reason",
        }
        self.assertTrue(expected_keys.issubset(report.keys()))
        self.assertEqual(report["sampling_uncertainty_status"], "sampling_uncertainty_measured")
        self.assertEqual(report["pairwise_comparison_count"], 6)
        self.assertEqual(report["shared_cellwise_layer_counts"], [22, 22, 22, 22, 22, 22])
        self.assertEqual(report["validation_output_modes"], ["full", "full", "full", "full"])
        self.assertFalse(report["defaults_changed"])
        self.assertFalse(report["physics_changed"])
        self.assertFalse(report["thresholds_changed"])
        self.assertFalse(report["source_or_scenario_inputs_changed"])
        self.assertFalse(report["scale_up_authorized"])
        self.assertFalse(report["operational_claims_allowed"])
        self.assertEqual(report["comparison_status"], "ok")
        self.assertEqual(report["interpretation"], "sampling_uncertainty_measured")

        self.assertEqual(report["output_file_counts"][report["artifact_ids"][0]], 3)
        self.assertGreater(report["output_byte_counts"][report["artifact_ids"][3]], 0)

        max_ke = report["max_kinetic_energy_uncertainty"]
        self.assertEqual(max_ke["l1_abs_diff"]["min"], 102270.95572600431)
        self.assertEqual(max_ke["l1_abs_diff"]["max"], 190718.90391041967)
        self.assertEqual(max_ke["nodata_mismatch_count"]["min"], 13)
        self.assertEqual(max_ke["nodata_mismatch_count"]["max"], 56)

        max_jump = report["max_jump_height_uncertainty"]
        self.assertEqual(max_jump["l1_abs_diff"]["min"], 17.312950101751824)
        self.assertEqual(max_jump["l1_abs_diff"]["max"], 30.019475562139338)
        self.assertEqual(max_jump["nodata_mismatch_count"]["max"], 56)

        velocity = report["velocity_exceedance_uncertainty"]
        self.assertIn("velocity_exceedance_5mps", velocity)
        self.assertIn("weighted_velocity_exceedance_5mps", velocity)
        self.assertIn("velocity_exceedance_10mps", velocity)

        self.assertTrue(any("max_kinetic_energy remains the dominant layer" in item for item in report["uncertainty_reduced"]))
        self.assertTrue(any("seed sensitivity remains structurally limiting" in item for item in report["remaining_uncertainty"]))

    def test_missing_manifest_reports_blocked_missing_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            good_manifest = self._make_artifact(tmp, "gate_v1", seed=34013, mode="full")
            missing_manifest = tmp / "hazard/results/tschamut_public_pilot/missing_site/validation_tschamut_public_missing_site_manifest.json"
            report = summary.build_sampling_uncertainty_summary([good_manifest, missing_manifest])

        self.assertEqual(report["sampling_uncertainty_status"], "blocked_missing_inputs")
        self.assertEqual(report["readiness_status"], "blocked_missing_inputs")
        self.assertFalse(report["scale_up_authorized"])
        self.assertFalse(report["operational_claims_allowed"])
        self.assertIn(str(missing_manifest), report["missing_input_paths"])
        self.assertEqual(report["comparison_pairs_run"], [])

    def test_markdown_render_includes_pairwise_summary(self) -> None:
        report = {
            "sampling_uncertainty_status": "sampling_uncertainty_measured",
            "pairwise_comparison_count": 6,
            "case_ids": ["a", "b"],
            "seeds_or_splits": [1, 2],
            "ensemble_sizes": [12, 12],
            "dominant_layer_spread": {
                "max_kinetic_energy": {
                    "l1_abs_diff": {"min": 1.0, "max": 2.0},
                    "linf_abs_diff": {"min": 3.0, "max": 4.0},
                    "rmse": {"min": 5.0, "max": 6.0},
                    "nonzero_jaccard": {"min": 0.9, "max": 1.0},
                },
                "max_jump_height": {
                    "l1_abs_diff": {"min": 1.0, "max": 2.0},
                    "linf_abs_diff": {"min": 3.0, "max": 4.0},
                    "rmse": {"min": 5.0, "max": 6.0},
                    "nonzero_jaccard": {"min": 0.8, "max": 0.9},
                },
                "velocity_exceedance_5mps": {
                    "l1_abs_diff": {"min": 1.0, "max": 2.0},
                    "linf_abs_diff": {"min": 3.0, "max": 4.0},
                    "rmse": {"min": 5.0, "max": 6.0},
                    "nonzero_jaccard": {"min": 0.7, "max": 0.8},
                },
                "weighted_velocity_exceedance_5mps": {
                    "l1_abs_diff": {"min": 1.0, "max": 2.0},
                    "linf_abs_diff": {"min": 3.0, "max": 4.0},
                    "rmse": {"min": 5.0, "max": 6.0},
                    "nonzero_jaccard": {"min": 0.7, "max": 0.8},
                },
                "velocity_exceedance_10mps": {
                    "l1_abs_diff": {"min": 1.0, "max": 2.0},
                    "linf_abs_diff": {"min": 3.0, "max": 4.0},
                    "rmse": {"min": 5.0, "max": 6.0},
                    "nonzero_jaccard": {"min": 0.6, "max": 0.7},
                },
            },
            "uncertainty_reduced": ["dominant disagreement shrinks"],
            "remaining_uncertainty": ["seed sensitivity persists"],
            "blocked_reason": "none",
        }

        markdown = summary.render_markdown_report(report)
        self.assertIn("# Same-Scale Sampling Uncertainty Envelope", markdown)
        self.assertIn("Pairwise comparisons: `6`", markdown)
        self.assertIn("max_kinetic_energy", markdown)

    def _make_artifact(self, root: Path, artifact_name: str, *, seed: int, mode: str, validation_files: int = 1, hazard_files: int = 1) -> Path:
        validation_root = root / "validation/private/tschamut_public_pilot" / artifact_name
        hazard_root = root / "hazard/results/tschamut_public_pilot" / artifact_name
        validation_root.mkdir(parents=True, exist_ok=True)
        hazard_root.mkdir(parents=True, exist_ok=True)
        case_path = validation_root / f"tschamut_public_{artifact_name}_case.yaml"
        manifest_path = hazard_root / f"validation_tschamut_public_{artifact_name}_manifest.json"

        outputs = {
            "diagnostics_json": str(validation_root / "metrics.json"),
            "ensemble_deposition_csv": str(validation_root / "deposition.csv"),
            "trajectory_metadata_csv": str(validation_root / "trajectory_metadata.csv"),
        }
        if mode == "full":
            outputs.update(
                {
                    "trajectory_csv": str(validation_root / "trajectory.csv"),
                    "ensemble_trajectories_dir": str(validation_root / "trajectories"),
                    "ensemble_impact_events_dir": str(validation_root / "impacts"),
                }
            )

        case_path.write_text(
            "\n".join(
                [
                    f"case_id: validation_tschamut_public_{artifact_name}",
                    "random:",
                    f"  seed: {seed}",
                    "  ensemble_size: 12",
                    "outputs:",
                    *[f"  {key}: {value}" for key, value in outputs.items()],
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        manifest_path.write_text(
            json.dumps(
                {
                    "case_id": f"validation_tschamut_public_{artifact_name}",
                    "seed_policy": {"global_seed": seed, "ensemble_size": 12},
                    "cellwise_layers": [{"layer_key": "max_kinetic_energy"} for _ in range(22)],
                }
            ),
            encoding="utf-8",
        )
        for index in range(validation_files):
            (validation_root / f"file_{index}.txt").write_text("x" * (index + 1), encoding="utf-8")
        for index in range(hazard_files):
            (hazard_root / f"file_{index}.txt").write_text("y" * (index + 2), encoding="utf-8")
        return manifest_path

    def _fake_compare(self, reference_manifest: Path, compare_manifest: Path) -> dict[str, object]:
        pair_key = tuple(sorted((reference_manifest.parent.name, compare_manifest.parent.name)))
        pair_metrics = self._pair_metrics()[pair_key]
        layer_comparisons = []
        for layer_key, metrics in pair_metrics.items():
            layer_comparisons.append(
                {
                    "layer_key": layer_key,
                    "layer_name": layer_key,
                    "value_metrics": {
                        "l1_abs_diff": metrics["l1"],
                        "linf_abs_diff": metrics["linf"],
                        "rmse": metrics["rmse"],
                        "compared_cell_count": 91200,
                    },
                    "nonzero_metrics": {
                        "nonzero_jaccard": metrics["jaccard"],
                    },
                    "missing_cell_metrics": {
                        "nodata_mismatch_count": metrics["nodata"],
                    },
                }
            )
        return {
            "schema_version": "hazard_map_convergence_diagnostic_v1",
            "status": "ok",
            "comparisons": [
                {
                    "cellwise_metrics": {
                        "layer_comparisons": layer_comparisons,
                    }
                }
            ],
            "overall_metrics": {
                "shared_layer_count": 22,
                "cellwise_linf_abs_diff_max": max(item["linf"] for item in pair_metrics.values()),
                "cellwise_l1_abs_diff_sum": sum(item["l1"] for item in pair_metrics.values()),
                "cellwise_rmse_max": max(item["rmse"] for item in pair_metrics.values()),
                "cellwise_nonzero_jaccard_min": min(item["jaccard"] for item in pair_metrics.values()),
                "cellwise_nodata_mismatch_count": sum(item["nodata"] for item in pair_metrics.values()),
                "output_checksum_match_count": 8,
                "output_checksum_mismatch_count": 36,
                "output_checksum_missing_count": 13,
            },
        }

    def _pair_metrics(self) -> dict[tuple[str, str], dict[str, dict[str, float]]]:
        return {
            ("gate_v1", "target_gate_v1"): {
                "max_kinetic_energy": {"l1": 190718.90391041967, "linf": 3028.22579673, "rmse": 983.451160251898, "jaccard": 1.0, "nodata": 45},
                "max_jump_height": {"l1": 30.019475562139338, "linf": 1.42875571255, "rmse": 0.21594778911463908, "jaccard": 0.7598039215686274, "nodata": 45},
                "velocity_exceedance_5mps": {"l1": 5.312621804416979, "linf": 0.155778647582, "rmse": 0.0016156994693019395, "jaccard": 0.8279569892473119, "nodata": 0},
                "weighted_velocity_exceedance_5mps": {"l1": 4.92878787878956, "linf": 0.13545454545400004, "rmse": 0.001482538767662409, "jaccard": 0.8279569892473119, "nodata": 0},
                "velocity_exceedance_10mps": {"l1": 4.4495832036858225, "linf": 0.12553020749800003, "rmse": 0.0014119067351479587, "jaccard": 0.7389162561576355, "nodata": 0},
            },
            ("gate_v1", "sampling_sensitivity_v1_full"): {
                "max_kinetic_energy": {"l1": 111881.5884327295, "linf": 3659.1261796799995, "rmse": 739.8748114022868, "jaccard": 1.0, "nodata": 25},
                "max_jump_height": {"l1": 17.312950101751824, "linf": 0.886003586508, "rmse": 0.15614702267928676, "jaccard": 0.8218390804597702, "nodata": 25},
                "velocity_exceedance_5mps": {"l1": 6.378539493288022, "linf": 0.15241837149399995, "rmse": 0.0019315928157124969, "jaccard": 0.9037656903765691, "nodata": 0},
                "weighted_velocity_exceedance_5mps": {"l1": 5.840909090913057, "linf": 0.13636363636400006, "rmse": 0.0017704632666337558, "jaccard": 0.9037656903765691, "nodata": 0},
                "velocity_exceedance_10mps": {"l1": 5.3471074380172805, "linf": 0.161495732286, "rmse": 0.0017624252667342744, "jaccard": 0.8117647058823529, "nodata": 0},
            },
            ("gate_v1", "sampling_sensitivity_v2_full"): {
                "max_kinetic_energy": {"l1": 149693.4021386152, "linf": 3751.2327569500003, "rmse": 897.810025337777, "jaccard": 1.0, "nodata": 28},
                "max_jump_height": {"l1": 17.820106096599282, "linf": 1.14323722766, "rmse": 0.16839141722002612, "jaccard": 0.8125, "nodata": 28},
                "velocity_exceedance_5mps": {"l1": 7.510928961744405, "linf": 0.21461748633899996, "rmse": 0.0022902866740530147, "jaccard": 0.8888888888888888, "nodata": 0},
                "weighted_velocity_exceedance_5mps": {"l1": 6.863636363644098, "linf": 0.18939393939400007, "rmse": 0.0020913227021608824, "jaccard": 0.8888888888888888, "nodata": 0},
                "velocity_exceedance_10mps": {"l1": 5.620628415301155, "linf": 0.129098360656, "rmse": 0.0018334883288493604, "jaccard": 0.8045977011494253, "nodata": 0},
            },
            ("sampling_sensitivity_v1_full", "sampling_sensitivity_v2_full"): {
                "max_kinetic_energy": {"l1": 102270.95572600431, "linf": 3294.73639652, "rmse": 694.3937457555284, "jaccard": 1.0, "nodata": 13},
                "max_jump_height": {"l1": 18.021506019975554, "linf": 1.041637408833, "rmse": 0.15861381731226953, "jaccard": 0.8507462686567164, "nodata": 13},
                "velocity_exceedance_5mps": {"l1": 5.46225895316802, "linf": 0.15261707989, "rmse": 0.00178930691247105, "jaccard": 0.9482758620689655, "nodata": 0},
                "weighted_velocity_exceedance_5mps": {"l1": 4.977272727284121, "linf": 0.13636363636299997, "rmse": 0.0016363584061806354, "jaccard": 0.9482758620689655, "nodata": 0},
                "velocity_exceedance_10mps": {"l1": 3.8672865013843314, "linf": 0.12305875942200001, "rmse": 0.0013993098543827903, "jaccard": 0.9053254437869822, "nodata": 0},
            },
            ("sampling_sensitivity_v1_full", "target_gate_v1"): {
                "max_kinetic_energy": {"l1": 130872.16413540982, "linf": 4484.5620665999995, "rmse": 835.754935708074, "jaccard": 1.0, "nodata": 56},
                "max_jump_height": {"l1": 24.3774694688961, "linf": 1.041637408833, "rmse": 0.17441897492511943, "jaccard": 0.8507462686567164, "nodata": 56},
                "velocity_exceedance_5mps": {"l1": 4.07156479883833, "linf": 0.11543002452000001, "rmse": 0.001289806138060068, "jaccard": 0.8028673835125448, "nodata": 0},
                "weighted_velocity_exceedance_5mps": {"l1": 3.744242424251889, "linf": 0.10272727272700005, "rmse": 0.001188329775839792, "jaccard": 0.8028673835125448, "nodata": 0},
                "velocity_exceedance_10mps": {"l1": 3.2677322677353717, "linf": 0.12305875942200001, "rmse": 0.0011360928838591929, "jaccard": 0.7783251231527094, "nodata": 0},
            },
            ("sampling_sensitivity_v2_full", "target_gate_v1"): {
                "max_kinetic_energy": {"l1": 102330.21041949901, "linf": 3294.73639652, "rmse": 694.3937457555284, "jaccard": 1.0, "nodata": 26},
                "max_jump_height": {"l1": 21.98376725591462, "linf": 0.518719414238, "rmse": 0.13600226028761866, "jaccard": 0.8431372549019608, "nodata": 26},
                "velocity_exceedance_5mps": {"l1": 4.4277722277755345, "linf": 0.13470695970700003, "rmse": 0.0014313304698311909, "jaccard": 0.8172043010752689, "nodata": 0},
                "weighted_velocity_exceedance_5mps": {"l1": 4.022727272731252, "linf": 0.12212121212099997, "rmse": 0.0013010262552210204, "jaccard": 0.8172043010752689, "nodata": 0},
                "velocity_exceedance_10mps": {"l1": 3.1839910089909624, "linf": 0.10726773226800002, "rmse": 0.001105428916389202, "jaccard": 0.8078817733990148, "nodata": 0},
            },
        }
