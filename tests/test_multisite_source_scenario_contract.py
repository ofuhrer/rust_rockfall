from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import yaml

from scripts import audit_multisite_source_scenario_contract as audit


FIXTURE = Path("tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml")


class MultisiteSourceScenarioContractTests(unittest.TestCase):
    def test_blocked_candidate_reports_contract_fields_and_missing_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            candidate_config = self._write_candidate_config(Path(tmp))
            report = audit.build_report(candidate_config)

        self.assertEqual(report["source_scenario_contract_audit_status"], "measured")
        self.assertEqual(report["second_site_portability_status"], "blocked_missing_inputs")
        self.assertEqual(report["candidate_site_id"], "chant_sura_fluelapass_portability_example_v1")
        self.assertEqual(report["scale_up_authorized"], False)
        self.assertEqual(report["operational_claims_allowed"], False)

        self.assertIn("source_zone_id_pattern", report["field_classifications"]["portable_required"])
        self.assertIn("source_zone_geometry", report["field_classifications"]["portable_required"])
        self.assertIn("terrain_crop_path", report["missing_second_site_fields"])
        self.assertIn("source_zone_metadata_path", report["missing_second_site_fields"])
        self.assertIn("scenario_table_path", report["missing_second_site_fields"])
        self.assertIn("terrain_crop", report["required_path_patterns_or_manifest_keys"])
        self.assertIn("terrain.asc", report["required_path_patterns_or_manifest_keys"]["terrain_crop"])

        heuristic_fields = {item["field"]: item["value"] for item in report["tschamut_specific_heuristics"]}
        self.assertEqual(heuristic_fields["release_sampling_mode"], "deterministic_grid")
        self.assertEqual(heuristic_fields["release_sampling_seed"], 34014)
        self.assertEqual(heuristic_fields["release_count"], 10)
        self.assertEqual(heuristic_fields["release_cell_id_prefix"], "tschamut_public_release_cell")

        self.assertTrue(report["validation_or_field_evidence_boundary"]["not_validation_evidence_by_itself"])
        self.assertIn("annual_frequency", report["probability_semantics_boundary"]["unsupported_claims"])

    def test_json_contract_keys_are_stable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            candidate_config = self._write_candidate_config(Path(tmp))
            report = audit.build_report(candidate_config)

        expected_keys = {
            "source_scenario_contract_audit_status",
            "tschamut_readiness_status",
            "second_site_portability_status",
            "candidate_site_id",
            "candidate_site_name",
            "fields_audited",
            "field_classifications",
            "tschamut_available_fields",
            "second_site_available_fields",
            "missing_second_site_fields",
            "required_path_patterns_or_manifest_keys",
            "portable_contract_fields",
            "site_specific_contract_fields",
            "tschamut_specific_heuristics",
            "optional_or_deferred_fields",
            "out_of_scope_fields",
            "probability_semantics_boundary",
            "validation_or_field_evidence_boundary",
            "next_required_artifacts",
            "blocked_reason",
            "scale_up_authorized",
            "operational_claims_allowed",
        }
        self.assertTrue(expected_keys.issubset(report.keys()))

    def _write_candidate_config(self, root: Path) -> Path:
        candidate = yaml.safe_load(FIXTURE.read_text(encoding="utf-8"))
        assert isinstance(candidate, dict)
        candidate["expected_processed_input_root"] = str(root / "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input")
        candidate["expected_processed_context_root"] = str(root / "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/context")
        candidate["expected_terrain_crop_path"] = str(root / "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/terrain.asc")
        candidate["expected_terrain_metadata_path"] = str(root / "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/terrain_metadata.yaml")
        candidate["expected_source_zone_metadata_path"] = str(root / "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/source_zone_metadata.yaml")
        candidate["expected_scenario_table_path"] = str(root / "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/scenario_table.csv")
        candidate["expected_source_scenario_policy_path"] = str(root / "validation/policies/chant_sura_fluelapass_portability_example_v1_source_scenario_policy_v1.yaml")
        candidate["expected_validation_private_root"] = str(root / "validation/private/chant_sura_fluelapass_portability_example_v1")
        candidate["expected_hazard_results_root"] = str(root / "hazard/results/chant_sura_fluelapass_portability_example_v1")
        candidate["expected_swissimage_context_root"] = str(root / "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/context/swissimage")
        candidate["expected_swisstlm3d_context_root"] = str(root / "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/context/swisstlm3d")
        candidate["expected_swisstlm3d_metadata_path"] = str(root / "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/context/swisstlm3d/metadata.json")
        candidate["expected_swisssurface3d_context_root"] = str(root / "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/context/swisssurface3d")
        candidate["expected_swisssurface3d_raster_context_root"] = str(root / "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/context/swisssurface3d_raster")
        candidate["expected_swissbuildings3d_context_root"] = str(root / "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/context/swissbuildings3d")
        candidate["expected_barrier_inventory_root"] = str(root / "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/context/barriers")

        config_path = root / "candidate.yaml"
        config_path.write_text(yaml.safe_dump(candidate, sort_keys=False), encoding="utf-8")
        return config_path


if __name__ == "__main__":
    unittest.main()
