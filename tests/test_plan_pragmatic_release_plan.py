from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "plan_pragmatic_release_plan.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


planner = load_module(SCRIPT_PATH, "plan_pragmatic_release_plan")


def feature(candidate_id: str, geometry_type: str, coordinates):
    return {
        "type": "Feature",
        "properties": {
            "candidate_release_zone_id": candidate_id,
            "source_zone_id": candidate_id,
            "mass_kg": 12.0,
            "radius_m": 0.3,
        },
        "geometry": {"type": geometry_type, "coordinates": coordinates},
    }


def write_geojson(path: Path, features: list[dict]) -> None:
    path.write_text(
        json.dumps({"type": "FeatureCollection", "features": features}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


class PragmaticReleasePlanTests(unittest.TestCase):
    def test_report_is_deterministic_from_frozen_inputs(self) -> None:
        first = planner.build_report()
        second = planner.build_report()

        self.assertEqual(first, second)
        self.assertEqual(first["schema_version"], "balfrin_block_scenario_sensitivity_plan_v1")
        self.assertEqual(first["scenario_plan_status"], "ready")
        self.assertTrue(first["read_only"])
        self.assertFalse(first["scale_up_authorized"])
        self.assertFalse(first["operational_claims_allowed"])
        self.assertEqual(first["source_policy_provenance"]["policy_id"], "tschamut_public_source_scenario_policy_v1")
        self.assertEqual(first["source_policy_provenance"]["policy_path"], "validation/policies/tschamut_public_source_scenario_policy_v1.yaml")
        self.assertEqual(first["source_policy_provenance"]["release_sampling_mode"], "deterministic_grid")
        self.assertEqual(first["scenario_plan_summary"]["block_size_bin_count"], 3)
        self.assertEqual(first["scenario_plan_summary"]["reference_row_count"], 1)
        self.assertEqual(first["scenario_plan_summary"]["policy_sampling_weight_total"], 10.0)
        self.assertEqual(first["scenario_plan_summary"]["normalized_sampling_share_total"], 1.0)

        bins = first["block_size_bins"]
        self.assertEqual([entry["bin_label"] for entry in bins], ["small", "medium", "large"])
        self.assertEqual([entry["block_scenario_id"] for entry in bins], [
            "tschamut_public_block_small__tschamut_public_shape_equant",
            "tschamut_public_block_medium__tschamut_public_shape_equant",
            "tschamut_public_block_large__tschamut_public_shape_equant",
        ])
        self.assertEqual([entry["normalized_sampling_share"] for entry in bins], [0.3, 0.5, 0.2])
        self.assertTrue(all("conditional_sampling_only" in entry["non_frequency_labels"] for entry in bins))
        self.assertTrue(all(entry["plan_label"] == "pragmatic_sensitivity_bin" for entry in bins))

        weighting = first["weighting_semantics"]
        self.assertEqual(weighting["sampling_weight_semantics"], "conditional_sampling_only")
        self.assertEqual(weighting["scenario_probability_semantics"], "normalized within a block family; no annual frequency claim")
        self.assertTrue(weighting["sampling_weight_is_not_physical_probability"])
        self.assertTrue(weighting["sampling_weight_is_not_annual_frequency"])

        reference = first["reference_scenario_table"]
        self.assertEqual(reference["role"], "frozen_reference_record")
        self.assertEqual(reference["row_count"], 1)
        self.assertEqual(reference["row_ids"], ["tschamut_public_block_observed_rows"])
        self.assertEqual(reference["block_scenario_ids"], ["tschamut_public_observed_rows"])
        self.assertIn("annual_frequency_per_year", reference["non_frequency_columns"])
        self.assertEqual(reference["rows"][0]["release_probability"], "")
        self.assertEqual(reference["rows"][0]["scenario_probability"], "")
        self.assertEqual(reference["rows"][0]["annual_frequency_per_year"], "")
        self.assertEqual(reference["rows"][0]["time_horizon_years"], "")

        self.assertFalse(first["claim_boundary"]["annual_frequency_supported"])
        self.assertFalse(first["claim_boundary"]["physical_probability_supported"])
        self.assertIn("conditional_sampling_only", first["explicit_non_frequency_labels"])
        self.assertEqual(first["same_scale_reference"]["document_status"], "available")

    def test_missing_inputs_block_generation_and_list_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            missing_policy = root / "missing_policy.yaml"
            missing_table = root / "missing_table.csv"
            report = planner.build_report(policy_path=missing_policy, scenario_table_path=missing_table)

        self.assertEqual(report["scenario_plan_status"], "blocked_missing_inputs")
        self.assertIn(str(missing_policy), report["missing_inputs"][0])
        self.assertIn(str(missing_table), report["missing_inputs"][1])
        self.assertEqual(report["scenario_plan_summary"]["block_size_bin_count"], 0)
        self.assertEqual(report["reference_scenario_table"]["row_count"], 0)
        self.assertTrue(report["pragmatic_coverage_boundary"]["coverage_is_not_physical_frequency"])
        self.assertTrue(report["weighting_semantics"]["sampling_weights_are_not_physical_probabilities"])

    def test_text_output_is_stable(self) -> None:
        report = planner.build_report()
        text = planner.render_text_report(report)
        self.assertEqual(text, planner.render_text_report(report))
        self.assertIn("Balfrin Block-Scenario Sensitivity Plan", text)
        self.assertIn("Scenario plan status: `ready`", text)
        self.assertIn("Block-Size Bins", text)
        self.assertIn("Pragmatic Coverage Boundary", text)
        self.assertIn("not_annual_frequency", text)
        self.assertIn("Same-Scale Reference", text)

    def test_release_geometry_sampling_stable_ids_for_point_line_and_area(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidates = root / "candidate_geometries.geojson"
            write_geojson(
                candidates,
                [
                    feature("point_zone", "Point", [100.0, 200.0]),
                    feature("line_zone", "LineString", [[0.0, 0.0], [10.0, 0.0]]),
                    feature(
                        "area_zone",
                        "Polygon",
                        [[[0.0, 0.0], [10.0, 0.0], [10.0, 10.0], [0.0, 10.0], [0.0, 0.0]]],
                    ),
                ],
            )

            first = planner.build_release_geometry_sampling_report(
                candidate_geometries_path=candidates,
                sampling_spacing_m=5.0,
                seed=123,
            )
            second = planner.build_release_geometry_sampling_report(
                candidate_geometries_path=candidates,
                sampling_spacing_m=5.0,
                seed=123,
            )

        self.assertEqual(first, second)
        self.assertEqual(first["schema_version"], "deterministic_release_geometry_sampling_plan_v1")
        self.assertEqual(first["release_plan_status"], "ready")
        self.assertFalse(first["scale_up_authorized"])
        self.assertFalse(first["operational_claims_allowed"])
        self.assertEqual(first["release_count_summary"]["candidate_geometry_count"], 3)
        self.assertEqual(first["release_count_summary"]["geometry_type_counts"], {"point": 1, "linestring": 1, "polygon": 1})
        release_ids = [row["trajectory_id"] for row in first["release_points"]]
        self.assertEqual(len(release_ids), len(set(release_ids)))
        self.assertIn("point_zone__point__release_0001", release_ids)
        self.assertIn("line_zone__linestring__release_0001", release_ids)
        self.assertTrue(any(release_id.startswith("area_zone__polygon__release_") for release_id in release_ids))
        self.assertEqual(first["sampling_policy"]["sampling_spacing_m"], 5.0)
        self.assertEqual(first["sampling_policy"]["sampling_seed"], 123)
        self.assertEqual(first["provenance"]["candidate_interpretation"], "workflow_candidate_only_not_validated_source_zone")

    def test_release_geometry_sampling_preserves_line_boundaries(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            candidates = Path(tmp) / "line.geojson"
            write_geojson(candidates, [feature("edge_line", "LineString", [[0.0, 0.0], [10.0, 0.0]])])

            report = planner.build_release_geometry_sampling_report(
                candidate_geometries_path=candidates,
                sampling_spacing_m=4.0,
                seed=7,
            )

        coordinates = [(row["x_m"], row["y_m"]) for row in report["release_points"]]
        self.assertEqual(coordinates[0], (0.0, 0.0))
        self.assertEqual(coordinates[-1], (10.0, 0.0))
        self.assertEqual(coordinates, [(0.0, 0.0), (4.0, 0.0), (8.0, 0.0), (10.0, 0.0)])
        self.assertEqual(report["release_count_summary"]["release_count_by_geometry_type"], {"linestring": 4})

    def test_release_geometry_sampling_handles_empty_and_small_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            empty_candidates = root / "empty.geojson"
            small_candidates = root / "small.geojson"
            write_geojson(empty_candidates, [])
            write_geojson(
                small_candidates,
                [
                    feature(
                        "tiny_area",
                        "Polygon",
                        [[[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0], [0.0, 0.0]]],
                    )
                ],
            )

            empty_report = planner.build_release_geometry_sampling_report(
                candidate_geometries_path=empty_candidates,
                sampling_spacing_m=5.0,
                seed=1,
            )
            small_report = planner.build_release_geometry_sampling_report(
                candidate_geometries_path=small_candidates,
                sampling_spacing_m=5.0,
                seed=1,
            )

        self.assertEqual(empty_report["release_plan_status"], "ready")
        self.assertTrue(empty_report["release_count_summary"]["empty_candidate_handled"])
        self.assertEqual(empty_report["release_count_summary"]["release_point_count"], 0)
        self.assertEqual(empty_report["release_points"], [])

        self.assertEqual(small_report["release_count_summary"]["release_point_count"], 1)
        self.assertEqual(small_report["release_points"][0]["trajectory_id"], "tiny_area__polygon__release_0001")
        self.assertEqual((small_report["release_points"][0]["x_m"], small_report["release_points"][0]["y_m"]), (0.5, 0.5))
        self.assertEqual(small_report["geometry_summaries"][0]["sampling_mode"], "area_grid")

    def test_release_geometry_sampling_writes_manifest_and_compatible_release_points_csv(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            root = Path(tmp)
            candidates = root / "point.geojson"
            output_root = root / "outputs"
            write_geojson(candidates, [feature("point_zone", "Point", [100.0, 200.0])])

            report = planner.build_release_geometry_sampling_report(
                candidate_geometries_path=candidates,
                output_root=output_root,
                sampling_spacing_m=5.0,
                seed=99,
                write_outputs=True,
            )
            csv_path = output_root / "release_points_lv95.csv"
            manifest_path = output_root / "release_geometry_sampling_manifest.json"

            self.assertTrue(csv_path.exists())
            self.assertTrue(manifest_path.exists())
            header = csv_path.read_text(encoding="utf-8").splitlines()[0].split(",")
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        self.assertIn("trajectory_id", header)
        self.assertIn("x_m", header)
        self.assertIn("release_geometry_type", header)
        self.assertEqual(manifest["release_count_summary"], report["release_count_summary"])


if __name__ == "__main__":
    unittest.main()
