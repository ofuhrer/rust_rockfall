from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "summarize_management_aoi_scenario_pressure.py"
POLICY_PATH = ROOT / "validation/policies/tschamut_public_source_scenario_policy_v1.yaml"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MODULE = load_module(SCRIPT_PATH, "summarize_management_aoi_scenario_pressure")


class ManagementAoiScenarioPressureTests(unittest.TestCase):
    def test_zero_candidate_set_reports_blocked_empty_pressure(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            tmp_root = Path(tmp)
            bundle_root = tmp_root / "validation/private/chant_sura_fluelapass_portability_example_v1/tb377_candidate_stability"
            bundle_root.mkdir(parents=True, exist_ok=True)
            metrics_path = bundle_root / "tschamut_public_pilot_release_zone_candidates_manifest.json"
            review_path = bundle_root / "tschamut_public_pilot_release_zone_candidate_review_manifest.json"

            metrics_path.write_text(
                json.dumps(
                    {
                        "schema_version": "terrain_release_zone_candidate_products_v1",
                        "candidate_release_zone_set_status": "emitted",
                        "candidate_cell_count": 0,
                        "candidate_area_m2": 0.0,
                        "candidate_summary": {
                            "candidate_cell_count": 0,
                            "candidate_area_m2": 0.0,
                        },
                    },
                    indent=2,
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            review_path.write_text(
                json.dumps(
                    {
                        "schema_version": "terrain_release_zone_candidate_selection_manifest_v1",
                        "review_package_status": "emitted",
                        "candidate_release_zone_set_status": "review_ready",
                        "candidate_release_zone_ids": [],
                        "review_summary": {
                            "candidate_count": 0,
                            "review_row_count": 0,
                            "review_decision_counts": {"accepted": 0, "rejected": 0, "needs_field_review": 0},
                            "candidate_stability_class_counts": {"stable": 0, "unstable": 0, "sensitive": 0},
                        },
                    },
                    indent=2,
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            (bundle_root / "candidate_mask.asc").write_text("mask\n", encoding="utf-8")
            (bundle_root / "candidate_review.geojson").write_text("{\"type\":\"FeatureCollection\",\"features\":[]}\n", encoding="utf-8")

            output_root = tmp_root / "scenario_pressure"
            report = MODULE.build_report(
                candidate_metrics_manifest_path=metrics_path,
                candidate_review_manifest_path=review_path,
                policy_path=POLICY_PATH,
                output_root=output_root,
            )
            report_path = output_root / "management_aoi_scenario_pressure_report.json"
            self.assertTrue(report_path.exists())

        self.assertEqual(report["schema_version"], "management_aoi_scenario_pressure_v1")
        self.assertEqual(report["scenario_pressure_status"], "blocked_empty_candidate_set")
        self.assertEqual(report["candidate_evidence"]["candidate_release_zone_set_status"], "emitted")
        self.assertEqual(report["candidate_evidence"]["candidate_cell_count"], 0)
        self.assertEqual(report["candidate_evidence"]["candidate_area_m2"], 0.0)
        self.assertEqual(report["candidate_evidence"]["bundle_measurements"]["file_count"], 4)
        self.assertGreater(report["candidate_evidence"]["bundle_measurements"]["total_bytes"], 0)
        self.assertEqual(report["candidate_evidence"]["review_summary"]["candidate_count"], 0)
        self.assertEqual(report["scenario_generation_pressure"]["scenario_row_count"], 0)
        self.assertEqual(report["scenario_generation_pressure"]["scenario_table_csv_bytes"], 0)
        self.assertEqual(report["scenario_generation_pressure"]["scenario_table_manifest_bytes"], 0)
        self.assertEqual(
            [row["block_family_id"] for row in report["scenario_generation_pressure"]["policy_block_family_cardinality"]],
            ["tschamut_selected_rows_small", "tschamut_selected_rows_medium", "tschamut_selected_rows_large"],
        )
        self.assertTrue(all(row["row_count"] == 0 for row in report["scenario_generation_pressure"]["policy_block_family_cardinality"]))
        self.assertEqual(report["command_plan_implications"][1]["command_id"], "second_site_release_plan_execution_template")
        self.assertEqual(report["command_plan_implications"][1]["status"], "blocked_not_ready")
        self.assertIn("no scenario rows", report["blocked_reason"])
        self.assertEqual(report["claim_boundary"]["annual_frequency_supported"], False)

        text = MODULE.render_text_report(report)
        self.assertIn("Management AOI Scenario Pressure", text)
        self.assertIn("scenario_pressure_status: `blocked_empty_candidate_set`", text)
        self.assertIn("second_site_release_plan_execution_template", text)


if __name__ == "__main__":
    unittest.main()
