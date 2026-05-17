from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "generate_tschamut_block_scenario_tables.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


generator = load_module(SCRIPT_PATH, "generate_tschamut_block_scenario_tables")


class TschamutBlockScenarioTableGenerationTests(unittest.TestCase):
    def test_default_template_recreates_the_committed_summary_table(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            tmp_root = Path(tmp)
            csv_path = tmp_root / "scenario_table.csv"
            manifest_path = tmp_root / "scenario_table_manifest.json"

            report = generator.build_report()
            self.assertEqual(report["scenario_table_status"], "ready")
            generator.write_csv(csv_path, report["generated_scenario_table_rows"])
            manifest_path.write_text(
                json.dumps(report["scenario_table_manifest"], indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )

            self.assertEqual(
                csv_path.read_text(encoding="utf-8"),
                (ROOT / "data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_scenario_table_v1.csv").read_text(encoding="utf-8"),
            )

            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["schema_version"], "candidate_source_zone_block_scenario_generation_manifest_v1")
            self.assertEqual(manifest["template_id"], "observed_rows_summary_v1")
            self.assertEqual(manifest["row_count"], 1)
            self.assertEqual(manifest["row_ids"], ["tschamut_public_block_observed_rows"])
            self.assertEqual(manifest["block_scenario_ids"], ["tschamut_public_observed_rows"])
            self.assertEqual(manifest["scenario_family_id"], "tschamut_public_lps_release_bbox__tschamut_public__observed_rows_summary_v1")
            self.assertEqual(manifest["source_zone_provenance"]["source_zone_id_source"], "policy_and_candidate_match")
            self.assertEqual(manifest["source_zone_provenance"]["resolved_source_zone_id"], "tschamut_public_lps_release_bbox")
            self.assertEqual(manifest["release_metadata_provenance"]["release_point_count"], 10)
            self.assertEqual(manifest["release_metadata_provenance"]["release_mass_kg_mean"], 62.3)
            self.assertEqual(manifest["release_metadata_provenance"]["release_radius_m_mean"], 0.176)
            self.assertEqual(manifest["normalized_sampling_share_total"], 1.0)
            self.assertEqual(manifest["conditional_weighting_semantics"]["sampling_weight_semantics"], "conditional_sampling_only")
            self.assertTrue(manifest["conditional_weighting_semantics"]["conditional_only_weighting"])
            self.assertEqual(manifest["rows"][0]["row_id"], "tschamut_public_block_observed_rows")
            self.assertEqual(manifest["rows"][0]["non_frequency_columns"], [
                "release_probability",
                "scenario_probability",
                "annual_frequency_per_year",
                "time_horizon_years",
            ])

    def test_policy_family_template_is_deterministic_and_weighted(self) -> None:
        first = generator.build_report(template_id="policy_block_family_v1")
        second = generator.build_report(template_id="policy_block_family_v1")

        self.assertEqual(first, second)
        self.assertEqual(first["scenario_table_status"], "ready")
        self.assertEqual(first["scenario_table_summary"]["row_count"], 3)
        self.assertEqual(first["scenario_table_summary"]["row_ids"], [
            "tschamut_public_lps_release_bbox__tschamut_public_block_small",
            "tschamut_public_lps_release_bbox__tschamut_public_block_medium",
            "tschamut_public_lps_release_bbox__tschamut_public_block_large",
        ])
        self.assertEqual(first["scenario_table_summary"]["block_scenario_ids"], [
            "tschamut_public_block_small",
            "tschamut_public_block_medium",
            "tschamut_public_block_large",
        ])
        self.assertEqual(first["scenario_table_summary"]["policy_sampling_weight_total"], 10.0)
        self.assertEqual(first["scenario_table_summary"]["normalized_sampling_share_total"], 1.0)
        self.assertEqual([row["sampling_weight"] for row in first["generated_scenario_table_rows"]], [3.0, 5.0, 2.0])
        self.assertEqual([row["normalized_sampling_share"] for row in first["scenario_table_manifest"]["rows"]], [0.3, 0.5, 0.2])
        self.assertTrue(all(row["release_probability"] == "" for row in first["generated_scenario_table_rows"]))
        self.assertTrue(all(row["scenario_probability"] == "" for row in first["generated_scenario_table_rows"]))
        self.assertTrue(all(row["annual_frequency_per_year"] == "" for row in first["generated_scenario_table_rows"]))
        self.assertTrue(first["scenario_table_manifest"]["conditional_only_weighting"])

    def test_generic_candidate_policy_template_uses_candidate_metadata(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            tmp_root = Path(tmp)
            policy_path = tmp_root / "synthetic_policy_template.yaml"
            candidate_metadata_path = tmp_root / "synthetic_candidate_source_zone_metadata.yaml"
            missing_reference_path = tmp_root / "missing_reference_table.csv"

            policy = yaml.safe_load((ROOT / "validation/templates/public_real_site_source_scenario_policy_v1.yaml").read_text(encoding="utf-8"))
            policy["policy_id"] = "synthetic_candidate_source_scenario_policy_v1"
            policy["pilot_id"] = "synthetic_candidate_pilot_v1"
            policy["policy_status"] = "draft_predeclared"
            policy["source_zone_policy"]["source_zone_id"] = ""
            policy["source_zone_policy"]["derivation_criteria"]["status"] = "predeclared_manual_review"
            policy["source_zone_policy"]["derivation_criteria"]["manual_interpretation_notes"] = "Synthetic candidate source-zone for deterministic scenario-generation regression coverage."
            policy["block_scenario_policy"]["scenarios"] = [
                {
                    "block_scenario_id": "synthetic_candidate_block_small",
                    "block_size_class": "synthetic_candidate_small",
                    "block_shape_class": "sphere",
                    "block_radius_m": 0.11,
                    "block_mass_kg": 22.0,
                    "sampling_weight": 4.0,
                    "derivation_basis": "synthetic fixture row",
                },
                {
                    "block_scenario_id": "synthetic_candidate_block_large",
                    "block_size_class": "synthetic_candidate_large",
                    "block_shape_class": "sphere",
                    "block_radius_m": 0.19,
                    "block_mass_kg": 96.0,
                    "sampling_weight": 6.0,
                    "derivation_basis": "synthetic fixture row",
                },
            ]
            policy_path.write_text(yaml.safe_dump(policy, sort_keys=False), encoding="utf-8")

            candidate_metadata = {
                "schema_version": "source_zone_metadata_v1",
                "source_zone_id": "synthetic_candidate_zone_alpha",
                "crs_epsg": 2056,
                "vertical_datum": "LN02",
                "geometry": {
                    "type": "polygon",
                    "vertices": [
                        [2600000.0, 1200000.0],
                        [2600040.0, 1200000.0],
                        [2600040.0, 1200040.0],
                        [2600000.0, 1200040.0],
                    ],
                },
                "release_sampling_policy": {
                    "mode": "deterministic_grid",
                    "seed": 77,
                    "release_count": 4,
                    "release_cell_id_prefix": "synthetic_candidate_cell",
                },
                "annual_release_frequency_per_year": None,
            }
            candidate_metadata_path.write_text(yaml.safe_dump(candidate_metadata, sort_keys=False), encoding="utf-8")

            report = generator.build_candidate_source_zone_report(
                policy_template_path=policy_path,
                candidate_source_zone_metadata_path=candidate_metadata_path,
                reference_scenario_table_path=missing_reference_path,
                template_id="policy_block_family_v1",
            )

        self.assertEqual(report["scenario_table_status"], "ready")
        self.assertEqual(report["scenario_table_summary"]["row_count"], 2)
        self.assertEqual(report["scenario_table_summary"]["row_ids"], [
            "synthetic_candidate_zone_alpha__synthetic_candidate_block_small",
            "synthetic_candidate_zone_alpha__synthetic_candidate_block_large",
        ])
        self.assertEqual(report["scenario_table_manifest"]["scenario_family_id"], "synthetic_candidate_zone_alpha__synthetic_candidate__policy_block_family_v1")
        self.assertEqual(report["scenario_table_manifest"]["source_zone_provenance"]["source_zone_id_source"], "candidate_source_zone_metadata")
        self.assertEqual(report["scenario_table_manifest"]["source_zone_provenance"]["resolved_source_zone_id"], "synthetic_candidate_zone_alpha")
        self.assertEqual(report["scenario_table_manifest"]["conditional_weighting_semantics"]["sampling_weight_semantics"], "conditional_sampling_only")
        self.assertTrue(report["scenario_table_manifest"]["conditional_weighting_semantics"]["conditional_only_weighting"])
        self.assertFalse(report["scenario_table_manifest"]["reference_scenario_table"]["available"])
        self.assertEqual(report["generated_scenario_table_rows"][0]["scenario_id"], "synthetic_candidate_zone_alpha__synthetic_candidate_block_small")
        self.assertEqual(report["generated_scenario_table_rows"][1]["sampling_weight"], 6.0)

    def test_missing_inputs_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            tmp_root = Path(tmp)
            missing_policy = tmp_root / "missing_policy.yaml"
            report = generator.build_report(policy_path=missing_policy)

        self.assertEqual(report["scenario_table_status"], "blocked_missing_inputs")
        self.assertIn("missing_policy.yaml", " ".join(report["scenario_table_manifest"]["missing_inputs"]))
        self.assertEqual(report["scenario_table_summary"]["row_count"], 0)
        self.assertTrue(report["scenario_table_manifest"]["supported_templates"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
