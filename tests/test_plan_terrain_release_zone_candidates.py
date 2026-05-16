from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "plan_terrain_release_zone_candidates.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


planner = load_module(SCRIPT_PATH, "plan_terrain_release_zone_candidates")


class TerrainReleaseZoneCandidateMetricsTests(unittest.TestCase):
    def test_committed_tschamut_inputs_produce_deterministic_candidate_metrics(self) -> None:
        first = planner.build_report()
        second = planner.build_report()

        self.assertEqual(first, second)
        self.assertEqual(first["schema_version"], "terrain_release_zone_candidate_metrics_v1")
        self.assertEqual(first["candidate_metrics_status"], "ready")
        self.assertEqual(first["candidate_release_zone_set_status"], "not_emitted")
        self.assertEqual(first["candidate_release_zone_interpretation"], "heuristic_workflow_input_only")
        self.assertEqual(first["candidate_site_id"], "tschamut_public_pilot")
        self.assertEqual(first["candidate_site_name"], "Balfrin / Tschamut AOI")
        self.assertEqual(first["screening_criteria"]["candidate_slope_min_deg"], 30.0)
        self.assertEqual(first["screening_criteria"]["candidate_slope_max_deg"], 55.0)
        self.assertEqual(first["screening_criteria"]["slope_algorithm"], "horn_3x3_cell_center_deg")
        self.assertGreater(first["candidate_summary"]["candidate_cell_count"], 0)
        self.assertGreater(first["candidate_summary"]["candidate_area_m2"], 0)
        self.assertGreater(first["candidate_summary"]["candidate_fraction_of_screenable_cells"], 0.0)
        self.assertIn(
            "candidate cells are heuristic workflow inputs, not validated release zones",
            " ".join(first["claim_boundaries"]["notes"]),
        )
        self.assertEqual(
            [row["category"] for row in first["excluded_area_summary"]],
            [
                "nodata_or_invalid",
                "incomplete_neighborhood",
                "frozen_release_zone_footprint",
                "slope_below_candidate_band",
                "slope_above_candidate_band",
                "candidate_band",
            ],
        )
        self.assertEqual(first["source_zone_inputs"]["source_zone_id"], "tschamut_public_lps_release_bbox")
        self.assertAlmostEqual(first["source_zone_inputs"]["footprint"]["polygon_area_m2_exact"], 327.01513671875, places=6)
        self.assertEqual(first["terrain_inputs"]["terrain_download_status"], "downloaded_public_open_data_to_ignored_raw_cache")

        text_report = planner.render_text_report(first)
        self.assertEqual(text_report, planner.render_text_report(second))
        self.assertIn("schema_version: terrain_release_zone_candidate_metrics_v1", text_report)
        self.assertIn("candidate_metrics_status: ready", text_report)
        self.assertIn("excluded_area_summary:", text_report)
        self.assertIn("frozen_release_zone_footprint", text_report)

    def test_missing_public_inputs_are_reported_as_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            report = planner.build_report(repo_root=repo_root)

        self.assertEqual(report["candidate_metrics_status"], "blocked_missing_inputs")
        self.assertEqual(report["candidate_release_zone_set_status"], "not_emitted")
        self.assertEqual(report["candidate_release_zone_interpretation"], "not_claimed")
        self.assertGreaterEqual(len(report["blocked_missing_inputs"]), 3)
        self.assertIn("required public inputs are missing", report["blocked_reason"])
        self.assertEqual(report["terrain_summary"], {})
        self.assertEqual(report["candidate_summary"], {})
        self.assertEqual(report["excluded_area_summary"], [])
        self.assertEqual(report["provenance"], {})


if __name__ == "__main__":
    unittest.main()
