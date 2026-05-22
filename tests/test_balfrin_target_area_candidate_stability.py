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
            timer_values = iter([100.0, 103.25, 200.0, 203.25])
            timer = lambda: next(timer_values)
            first = MODULE.build_report(output_root=output_root, timer=timer)
            second = MODULE.build_report(output_root=output_root, timer=timer)

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
                first["candidate_stability_summary"]["unstable_candidate_region"]["region_class"],
                "unstable_across_bounded_heuristics",
            )
            self.assertEqual(
                first["candidate_stability_summary"]["heuristic_sensitive_candidate_region"]["region_class"],
                "heuristic_sensitive_across_bounded_heuristics",
            )
            self.assertEqual(first["candidate_release_zone_products"]["output_status"], "emitted")
            self.assertEqual(first["candidate_release_zone_products"]["output_mode"], "both")
            self.assertTrue(first["candidate_release_zone_products"]["candidate_excludes_frozen_footprint"])
            self.assertEqual(first["candidate_release_zone_products"]["component_area_distribution_m2"]["min"], 8.0)
            self.assertGreater(first["candidate_release_zone_products"]["component_area_distribution_m2"]["max"], 4.0)
            self.assertGreater(first["candidate_release_zone_products"]["component_area_distribution_m2"]["mean"], 0.0)
            self.assertTrue(Path(first["candidate_release_zone_products"]["outputs"]["polygon"]).exists())
            self.assertTrue(Path(first["candidate_release_zone_products"]["outputs"]["mask"]).exists())
            self.assertTrue(Path(first["candidate_release_zone_products"]["outputs"]["manifest"]).exists())
            self.assertEqual(first["candidate_sweep_summary"]["sweep_status"], "ready")
            self.assertEqual(first["candidate_sweep_summary"]["candidate_count"], 3419)
            self.assertEqual(first["candidate_sweep_summary"]["candidate_area_m2"], 13676.0)
            self.assertEqual(first["candidate_sweep_summary"]["slope_thresholds_deg"], {"minimum": 45.0, "maximum": 75.0})
            self.assertEqual(first["candidate_sweep_summary"]["topography_thresholds"]["resolution_m"], 2.0)
            self.assertEqual(first["candidate_sweep_summary"]["topography_thresholds"]["valid_area_fraction"], 1.0)
            self.assertEqual(first["candidate_sweep_summary"]["sweep_measurements"]["runtime_seconds"], 3.25)
            self.assertEqual(first["candidate_sweep_summary"]["sweep_measurements"]["output_file_count"], 8)
            self.assertIn("search_domain", first["candidate_sweep_summary"]["sweep_measurements"]["output_paths"])
            self.assertGreater(first["candidate_sweep_summary"]["sweep_measurements"]["output_total_bytes"], 6_000_000)
            self.assertEqual(first["candidate_sweep_summary"]["multi_zone_stress_test_readiness"]["status"], "ready")
            self.assertIn("multi-zone scenario-generation stress tests", first["candidate_sweep_summary"]["multi_zone_stress_test_readiness"]["summary"])
            self.assertEqual(first["candidate_release_zone_products"]["component_count"], 65)
            self.assertEqual(first["candidate_summary"]["candidate_cell_count"], 3419)
            self.assertEqual(first["candidate_summary"]["screenable_cell_count"], 89915)
            self.assertEqual(first["candidate_stability_summary"]["variant_count"], 6)
            self.assertEqual(first["candidate_stability_summary"]["baseline_variant_id"], "baseline")
            self.assertEqual(
                [row["variant_id"] for row in first["candidate_stability_summary"]["variant_summaries"]],
                [
                    "baseline",
                    "tight_threshold_band",
                    "wide_threshold_band",
                    "smoothed_3x3_mean",
                    "coarsened_2x2_mean_reexpanded",
                    "trimmed_aoi_boundary_1_cell",
                ],
            )
            self.assertEqual(first["candidate_stability_summary"]["candidate_count_range"], {"min": 3077, "max": 3419})
            self.assertEqual(first["candidate_stability_summary"]["candidate_area_range_m2"], {"min": 12308.0, "max": 13676.0})
            self.assertEqual(
                first["candidate_stability_summary"]["stability_score_method"],
                "minimum_retention_fraction_across_bounded_heuristic_variants",
            )
            self.assertEqual(first["candidate_stability_summary"]["ranked_candidate_count"], 65)
            self.assertEqual(first["candidate_stability_summary"]["variant_summaries"][0]["candidate_delta_cell_count_vs_baseline"], 0)
            self.assertEqual(first["candidate_stability_summary"]["variant_summaries"][3]["candidate_delta_cell_count_vs_baseline"], -342)
            self.assertEqual(first["candidate_stability_summary"]["variant_summaries"][4]["candidate_delta_area_m2_vs_baseline"], -992.0)
            self.assertEqual(first["candidate_stability_summary"]["variant_summaries"][5]["candidate_overlap_jaccard_index_with_baseline"], 0.9570049722140976)
            self.assertEqual(first["selected_candidate_assessment"]["candidate_release_zone_id"], "tschamut_public_lps_release_bbox_candidate_058")
            self.assertEqual(first["selected_candidate_assessment"]["candidate_stability_class"], "stable")
            self.assertEqual(first["selected_candidate_assessment"]["selected_candidate_classification"], "stable")
            self.assertEqual(
                first["selected_candidate_assessment"]["selected_candidate_recommendation"]["status"],
                "adequate_for_bounded_engineering_probe",
            )
            self.assertEqual(
                [row["sensitivity_dimension"] for row in first["candidate_sensitivity_matrix"]],
                ["slope_threshold", "smoothing", "terrain_resolution", "aoi_boundary"],
            )
            self.assertEqual(first["candidate_persistence_metrics"]["stable_candidate_cell_count"], 2828)
            self.assertEqual(first["candidate_persistence_metrics"]["heuristic_sensitive_candidate_cell_count"], 751)
            self.assertEqual(first["candidate_stability_ranking"][0]["stability_rank"], 1)
            self.assertEqual(first["candidate_stability_ranking"][0]["candidate_stability_class"], "stable")
            self.assertEqual(first["candidate_stability_ranking"][-1]["stability_rank"], 65)
            self.assertIn(first["candidate_stability_ranking"][-1]["candidate_stability_class"], {"sensitive", "unstable"})
            self.assertTrue(
                any(row["candidate_stability_class"] == "sensitive" for row in first["candidate_stability_ranking"])
            )
            self.assertEqual(
                first["bounded_probe_candidate_selection"]["selection_sizes"],
                [2, 4, 8],
            )
            self.assertEqual(
                first["bounded_probe_candidate_selection"]["selection_by_size"]["2"]["candidate_release_zone_ids"],
                [row["candidate_release_zone_id"] for row in first["candidate_stability_ranking"][:2]],
            )
            self.assertEqual(
                first["bounded_probe_candidate_selection"]["selection_by_size"]["4"]["candidate_release_zone_ids"],
                [row["candidate_release_zone_id"] for row in first["candidate_stability_ranking"][:4]],
            )
            self.assertEqual(
                first["bounded_probe_candidate_selection"]["selection_by_size"]["8"]["candidate_release_zone_ids"],
                [row["candidate_release_zone_id"] for row in first["candidate_stability_ranking"][:8]],
            )
            self.assertEqual(len(first["candidate_region_classifications"]), 3)
            self.assertFalse(first["scale_up_authorized"])
            self.assertFalse(first["operational_claims_allowed"])
            self.assertTrue(first["gis_readable_candidate_outputs_supported"])
            self.assertTrue(first["gis_readable_candidate_outputs_emitted"])
            self.assertIn("Balfrin Target-Area Candidate Stability Summary", report_text)
            self.assertIn("stable_across_bounded_heuristics", report_text)
            self.assertIn("unstable_across_bounded_heuristics", report_text)
            self.assertIn("heuristic_sensitive_across_bounded_heuristics", report_text)
            self.assertIn("## Selected Candidate", report_text)
            self.assertIn("adequate_for_bounded_engineering_probe", report_text)
            self.assertIn("## Candidate Ranking", report_text)
            self.assertIn("## Bounded Probe Selection", report_text)
            self.assertIn("## Stability Deltas", report_text)
            self.assertIn("top 2 candidate ids", report_text)
            self.assertIn("Persistence Metrics", report_text)
            self.assertIn("Sensitivity Matrix", report_text)
            self.assertIn("Sweep Measurements", report_text)
            self.assertIn("Candidate excludes frozen footprint", report_text)
            self.assertIn("search_domain", report_text)
            self.assertIn("candidate_release_zone_products", json.dumps(report_json, sort_keys=True))
            self.assertTrue(Path(first["candidate_stability_report_path"]).exists())
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
        self.assertIn("## Selected Candidate", text)
        self.assertIn("top 2 candidate ids", text)
        self.assertIn("Stability score method", text)

    def test_selection_is_order_independent(self) -> None:
        report = MODULE.build_report()
        ranked_candidates = list(report["candidate_stability_ranking"])
        scrambled = list(reversed(ranked_candidates))

        reordered_selection = MODULE.CANDIDATE_PLANNER.build_bounded_probe_candidate_selection(scrambled)

        self.assertEqual(
            reordered_selection["selection_by_size"]["2"]["candidate_release_zone_ids"],
            report["bounded_probe_candidate_selection"]["selection_by_size"]["2"]["candidate_release_zone_ids"],
        )
        self.assertEqual(
            reordered_selection["selection_by_size"]["4"]["candidate_release_zone_ids"],
            report["bounded_probe_candidate_selection"]["selection_by_size"]["4"]["candidate_release_zone_ids"],
        )
        self.assertEqual(
            reordered_selection["selection_by_size"]["8"]["candidate_release_zone_ids"],
            report["bounded_probe_candidate_selection"]["selection_by_size"]["8"]["candidate_release_zone_ids"],
        )

    def test_missing_inputs_are_reported_as_blocked(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            repo_root = Path(tmp)
            output_root = repo_root / "candidate_products"
            report = MODULE.build_report(repo_root=repo_root, output_root=output_root)

        self.assertEqual(report["candidate_metrics_status"], "blocked_missing_inputs")
        self.assertEqual(report["candidate_sweep_summary"]["multi_zone_stress_test_readiness"]["status"], "blocked_missing_inputs")
        self.assertEqual(report["candidate_sweep_summary"]["sweep_measurements"]["output_file_count"], 0)
        self.assertFalse(output_root.exists())
        self.assertIn("missing required inputs", report["blocked_reason"])


if __name__ == "__main__":
    unittest.main()
