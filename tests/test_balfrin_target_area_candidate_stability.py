from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "summarize_balfrin_target_area_candidate_stability.py"
CONTRACT_PATH = ROOT / "validation/pilot_runs/tschamut_public_balfrin_target_area_demo_v1.yaml"


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


MODULE = _load_module(SCRIPT_PATH, "summarize_balfrin_target_area_candidate_stability")


class BalfrinTargetAreaCandidateStabilityTests(unittest.TestCase):
    def test_target_area_candidate_stability_report_is_deterministic_and_gis_readable(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as output_tmp:
            output_root = Path(output_tmp) / "candidate_products"
            first = MODULE.build_report(output_root=output_root)
            second = MODULE.build_report(output_root=output_root)

            report_json = json.loads(json.dumps(first, sort_keys=True))
            report_text = MODULE.render_text_report(first)
            contract = yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8"))

            self.assertEqual(first, second)
            self.assertEqual(first["schema_version"], "balfrin_target_area_candidate_stability_v1")
            self.assertEqual(first["contract_status"], "ready_for_balfrin_target_area_demo")
            self.assertEqual(first["target_area"]["target_area_id"], "tschamut_public_pilot")
            self.assertEqual(first["target_area"]["target_area_name"], "Tschamut public pilot")
            self.assertEqual(first["candidate_metrics_status"], "ready")
            self.assertEqual(first["candidate_release_zone_interpretation"], "heuristic_workflow_input_only")
            self.assertEqual(first["candidate_stability_summary"]["stability_status"], "ready")
            self.assertEqual(
                first["candidate_stability_summary"]["stable_candidate_region"]["region_class"],
                "stable_across_bounded_heuristics",
            )
            self.assertEqual(
                first["candidate_stability_summary"]["heuristic_sensitive_candidate_region"]["region_class"],
                "heuristic_sensitive_across_bounded_heuristics",
            )
            self.assertEqual(first["candidate_release_zone_products"]["output_status"], "emitted")
            self.assertEqual(first["candidate_release_zone_products"]["output_mode"], "both")
            self.assertTrue(first["candidate_release_zone_products"]["candidate_excludes_frozen_footprint"])
            self.assertTrue(Path(first["candidate_release_zone_products"]["outputs"]["polygon"]).exists())
            self.assertTrue(Path(first["candidate_release_zone_products"]["outputs"]["mask"]).exists())
            self.assertTrue(Path(first["candidate_release_zone_products"]["outputs"]["manifest"]).exists())
            self.assertEqual(first["candidate_release_zone_products"]["component_count"], 390)
            self.assertEqual(first["candidate_summary"]["candidate_cell_count"], 29499)
            self.assertEqual(first["candidate_summary"]["screenable_cell_count"], 89915)
            self.assertEqual(first["candidate_stability_summary"]["variant_count"], 4)
            self.assertEqual(first["candidate_stability_summary"]["baseline_variant_id"], "baseline")
            self.assertEqual(first["candidate_stability_summary"]["candidate_count_range"], {"min": 22793, "max": 36751})
            self.assertEqual(first["candidate_stability_summary"]["candidate_area_range_m2"], {"min": 91172.0, "max": 147004.0})
            self.assertFalse(first["scale_up_authorized"])
            self.assertFalse(first["operational_claims_allowed"])
            self.assertTrue(first["gis_readable_candidate_outputs_supported"])
            self.assertTrue(first["gis_readable_candidate_outputs_emitted"])
            self.assertIn("Balfrin Target-Area Candidate Stability Summary", report_text)
            self.assertIn("stable_across_bounded_heuristics", report_text)
            self.assertIn("heuristic_sensitive_across_bounded_heuristics", report_text)
            self.assertIn("candidate_release_zone_products", json.dumps(report_json, sort_keys=True))
            self.assertEqual(contract["target_area"]["target_area_id"], first["target_area"]["target_area_id"])
            self.assertEqual(
                contract["input_freeze"]["source_zone_metadata_path"],
                "data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_source_zone_metadata_v1.yaml",
            )

    def test_text_output_smoke(self) -> None:
        report = MODULE.build_report()
        text = MODULE.render_text_report(report)

        self.assertEqual(text, MODULE.render_text_report(report))
        self.assertIn("Candidate metrics status: `ready`", text)
        self.assertIn("Candidate release-zone output mode: `both`", text)
        self.assertIn("Candidate release-zone output status: `not_emitted`", text)


if __name__ == "__main__":
    unittest.main()
