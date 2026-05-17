from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "generate_candidate_source_zone_scenarios.py"
POLICY_PATH = ROOT / "validation/policies/tschamut_public_source_scenario_policy_v1.yaml"
RELEASE_POINTS_PATH = ROOT / "data/processed/swisstopo/tschamut_public_pilot/input/release_points_lv95.csv"


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


MODULE = _load_module(SCRIPT_PATH, "generate_candidate_source_zone_scenarios")


class CandidateSourceZoneScenarioStressTests(unittest.TestCase):
    def test_deterministic_release_candidates_generate_a_large_manifest_rich_table(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            output_root = Path(tmp) / "validation/private/tschamut_public_pilot/candidate_source_zone_stress_v1"

            first = MODULE.build_report(
                policy_path=POLICY_PATH,
                release_points_path=RELEASE_POINTS_PATH,
                output_root=output_root,
                candidate_repeat_count=3,
                template_ids=("candidate_release_point_summary_v1", "policy_block_family_v1"),
            )
            second = MODULE.build_report(
                policy_path=POLICY_PATH,
                release_points_path=RELEASE_POINTS_PATH,
                output_root=output_root,
                candidate_repeat_count=3,
                template_ids=("candidate_release_point_summary_v1", "policy_block_family_v1"),
            )

            manifest_path = Path(first["output_paths"]["scenario_table_manifest_json"])
            csv_path = Path(first["output_paths"]["scenario_table_csv"])
            report_path = Path(first["output_paths"]["stress_report_json"])
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            csv_text = csv_path.read_text(encoding="utf-8")
            report_text = report_path.read_text(encoding="utf-8")

        self.assertEqual(first["generated_scenario_table_rows"], second["generated_scenario_table_rows"])
        self.assertEqual(first["scenario_table_manifest"], second["scenario_table_manifest"])
        self.assertEqual(first["storage_measurements"], second["storage_measurements"])
        self.assertEqual(first["first_scaling_bottleneck"], second["first_scaling_bottleneck"])
        self.assertEqual(first["tb_183_planning_input"], second["tb_183_planning_input"])
        self.assertEqual(first["stress_test_status"], "ready")
        self.assertEqual(first["candidate_repeat_count"], 3)
        self.assertEqual(first["candidate_release_zone_record_count"], 30)
        self.assertEqual(first["scenario_row_count"], 120)
        self.assertTrue(first["tb_183_planning_input"]["ready_for_tb_183"])
        self.assertEqual(first["tb_183_planning_input"]["status"], "ready")
        self.assertGreater(first["storage_measurements"]["csv_bytes"], 0)
        self.assertGreater(first["storage_measurements"]["manifest_bytes"], first["storage_measurements"]["csv_bytes"])
        self.assertGreater(first["runtime_measurements"]["total_seconds"], 0.0)
        self.assertEqual(first["first_scaling_bottleneck"]["name"], "manifest_size")

        self.assertEqual(manifest["candidate_release_zone_record_count"], 30)
        self.assertEqual(manifest["scenario_row_count"], 120)
        self.assertEqual(manifest["candidate_repeat_count"], 3)
        self.assertEqual(manifest["candidate_cardinality"][0]["row_count"], 4)
        self.assertEqual(manifest["candidate_cardinality"][0]["template_count"], 2)
        self.assertEqual(manifest["source_zone_family_cardinality"], [
            {"group_id": "release_block_1", "row_count": 60},
            {"group_id": "release_block_2", "row_count": 24},
            {"group_id": "release_block_4", "row_count": 36},
        ])
        self.assertEqual(manifest["scenario_family_template_cardinality"], [
            {"group_id": "candidate_release_point_summary_v1", "row_count": 30},
            {"group_id": "policy_block_family_v1", "row_count": 90},
        ])
        self.assertEqual(manifest["row_ids"][0], "v004__repeat_000__candidate_release_point_summary")
        self.assertTrue(csv_text.startswith("scenario_id,"))
        self.assertIn("candidate_release_point_summary_v1", report_text)
        self.assertIn("policy_block_family_v1", report_text)

    def test_missing_inputs_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            output_root = Path(tmp) / "validation/private/tschamut_public_pilot/candidate_source_zone_stress_v1"
            missing_release_points = Path(tmp) / "missing_release_points.csv"

            report = MODULE.build_report(
                policy_path=POLICY_PATH,
                release_points_path=missing_release_points,
                output_root=output_root,
                candidate_repeat_count=3,
                template_ids=("candidate_release_point_summary_v1", "policy_block_family_v1"),
            )

        self.assertEqual(report["stress_test_status"], "blocked_missing_inputs")
        self.assertIn("missing_release_points.csv", " ".join(report["scenario_table_manifest"]["missing_inputs"]))
        self.assertEqual(report["candidate_release_zone_record_count"], 0)
        self.assertEqual(report["scenario_row_count"], 0)
        self.assertEqual(report["tb_183_planning_input"]["status"], "blocked_missing_inputs")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
