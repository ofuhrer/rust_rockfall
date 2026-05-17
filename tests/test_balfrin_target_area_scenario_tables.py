from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "generate_balfrin_target_area_scenario_tables.py"


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


MODULE = _load_module(SCRIPT_PATH, "generate_balfrin_target_area_scenario_tables")


class BalfrinTargetAreaScenarioTableTests(unittest.TestCase):
    def test_default_frozen_inputs_reproduce_the_committed_target_area_scenario_table(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as output_tmp:
            output_root = Path(output_tmp) / "validation/private/tschamut_public_pilot/balfrin_target_area_demo_v1"

            first = MODULE.build_report(output_root=output_root)
            second = MODULE.build_report(output_root=output_root)
            MODULE.write_outputs(first)

            scenario_csv = output_root / "tschamut_public_balfrin_target_area_demo_scenario_table.csv"
            manifest_path = output_root / "tschamut_public_balfrin_target_area_demo_scenario_manifest.json"
            scenario_csv_text = scenario_csv.read_text(encoding="utf-8")
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        self.assertEqual(first, second)
        self.assertEqual(first["scenario_table_status"], "ready")
        self.assertEqual(first["target_area_id"], "tschamut_public_pilot")
        self.assertEqual(first["target_area_name"], "Tschamut public pilot")
        self.assertEqual(
            scenario_csv_text,
            (ROOT / "data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_scenario_table_v1.csv").read_text(encoding="utf-8"),
        )
        self.assertEqual(manifest["schema_version"], "candidate_source_zone_block_scenario_generation_manifest_v1")
        self.assertEqual(manifest["table_status"], "ready")
        self.assertEqual(manifest["template_id"], "observed_rows_summary_v1")
        self.assertEqual(manifest["row_count"], 1)
        self.assertEqual(manifest["row_ids"], ["tschamut_public_block_observed_rows"])
        self.assertEqual(manifest["block_scenario_ids"], ["tschamut_public_observed_rows"])
        self.assertEqual(manifest["scenario_family_id"], "tschamut_public_lps_release_bbox__tschamut_public__observed_rows_summary_v1")
        self.assertEqual(manifest["source_zone_provenance"]["resolved_source_zone_id"], "tschamut_public_lps_release_bbox")
        self.assertEqual(manifest["release_metadata_provenance"]["release_sampling_seed"], 34014)
        self.assertTrue(manifest["conditional_weighting_semantics"]["conditional_only_weighting"])
        self.assertEqual(first["deterministic_generation_evidence"]["scenario_id"], "tschamut_public_block_observed_rows")
        self.assertEqual(first["deterministic_generation_evidence"]["release_sampling_seed"], 34014)
        self.assertEqual(first["scenario_table_manifest"]["target_area"]["target_area_id"], "tschamut_public_pilot")
        self.assertTrue(first["output_paths"]["scenario_table_csv"].endswith("tschamut_public_balfrin_target_area_demo_scenario_table.csv"))
        self.assertTrue(first["output_paths"]["scenario_manifest_json"].endswith("tschamut_public_balfrin_target_area_demo_scenario_manifest.json"))

    def test_synthetic_target_area_inputs_remain_deterministic_and_contract_bound(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            contract_path = tmp_root / "validation/pilot_runs/target_area_contract.yaml"
            policy_path = tmp_root / "validation/policies/policy.yaml"
            source_zone_path = tmp_root / "data/processed/swisstopo/target_area/input/source_zone.yaml"
            release_points_path = tmp_root / "data/processed/swisstopo/target_area/input/release_points_lv95.csv"
            reference_table_path = tmp_root / "data/processed/swisstopo/target_area/input/scenario_table.csv"
            output_root = tmp_root / "validation/private/target_area_demo"

            contract = yaml.safe_load((ROOT / "validation/pilot_runs/tschamut_public_balfrin_target_area_demo_v1.yaml").read_text(encoding="utf-8"))
            contract["input_freeze"]["source_zone_metadata_path"] = str(source_zone_path)
            contract["input_freeze"]["release_points_csv"] = str(release_points_path)
            contract["input_freeze"]["scenario_table_path"] = str(reference_table_path)
            contract["input_freeze"]["source_scenario_policy_path"] = str(policy_path)
            contract_path.parent.mkdir(parents=True, exist_ok=True)
            contract_path.write_text(yaml.safe_dump(contract, sort_keys=False), encoding="utf-8")

            for source, target in (
                (ROOT / "data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_source_zone_metadata_v1.yaml", source_zone_path),
                (ROOT / "data/processed/swisstopo/tschamut_public_pilot/input/release_points_lv95.csv", release_points_path),
                (ROOT / "data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_scenario_table_v1.csv", reference_table_path),
                (ROOT / "validation/policies/tschamut_public_source_scenario_policy_v1.yaml", policy_path),
            ):
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")

            first = MODULE.build_report(
                contract_path=contract_path,
                source_scenario_policy_path=policy_path,
                source_zone_metadata_path=source_zone_path,
                release_points_path=release_points_path,
                reference_scenario_table_path=reference_table_path,
                output_root=output_root,
            )
            second = MODULE.build_report(
                contract_path=contract_path,
                source_scenario_policy_path=policy_path,
                source_zone_metadata_path=source_zone_path,
                release_points_path=release_points_path,
                reference_scenario_table_path=reference_table_path,
                output_root=output_root,
            )

        self.assertEqual(first, second)
        self.assertEqual(first["scenario_table_status"], "ready")
        self.assertEqual(first["scenario_table_manifest"]["target_area"]["target_area_name"], "Tschamut public pilot")
        self.assertEqual(first["deterministic_generation_evidence"]["source_zone_id"], "tschamut_public_lps_release_bbox")
        self.assertEqual(first["scenario_table_manifest"]["conditional_weighting_semantics"]["sampling_weight_semantics"], "conditional_sampling_only")

    def test_missing_inputs_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            contract_path = tmp_root / "validation/pilot_runs/target_area_contract.yaml"
            policy_path = tmp_root / "validation/policies/policy.yaml"
            source_zone_path = tmp_root / "data/processed/swisstopo/target_area/input/source_zone.yaml"
            release_points_path = tmp_root / "data/processed/swisstopo/target_area/input/release_points_lv95.csv"
            reference_table_path = tmp_root / "data/processed/swisstopo/target_area/input/scenario_table.csv"
            output_root = tmp_root / "validation/private/target_area_demo"

            contract = yaml.safe_load((ROOT / "validation/pilot_runs/tschamut_public_balfrin_target_area_demo_v1.yaml").read_text(encoding="utf-8"))
            contract["input_freeze"]["source_zone_metadata_path"] = str(source_zone_path)
            contract["input_freeze"]["release_points_csv"] = str(release_points_path)
            contract["input_freeze"]["scenario_table_path"] = str(reference_table_path)
            contract["input_freeze"]["source_scenario_policy_path"] = str(policy_path)
            contract_path.parent.mkdir(parents=True, exist_ok=True)
            contract_path.write_text(yaml.safe_dump(contract, sort_keys=False), encoding="utf-8")

            policy_path.parent.mkdir(parents=True, exist_ok=True)
            policy_path.write_text((ROOT / "validation/policies/tschamut_public_source_scenario_policy_v1.yaml").read_text(encoding="utf-8"), encoding="utf-8")
            release_points_path.parent.mkdir(parents=True, exist_ok=True)
            release_points_path.write_text((ROOT / "data/processed/swisstopo/tschamut_public_pilot/input/release_points_lv95.csv").read_text(encoding="utf-8"), encoding="utf-8")
            reference_table_path.parent.mkdir(parents=True, exist_ok=True)
            reference_table_path.write_text((ROOT / "data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_scenario_table_v1.csv").read_text(encoding="utf-8"), encoding="utf-8")

            source_zone_path.parent.mkdir(parents=True, exist_ok=True)

            report = MODULE.build_report(
                contract_path=contract_path,
                source_scenario_policy_path=policy_path,
                source_zone_metadata_path=source_zone_path,
                release_points_path=release_points_path,
                reference_scenario_table_path=reference_table_path,
                output_root=output_root,
            )

        self.assertEqual(report["scenario_table_status"], "blocked_missing_inputs")
        self.assertIn("source_zone.yaml", " ".join(report["scenario_table_manifest"]["missing_inputs"]))
        self.assertFalse(report["generated_scenario_table_rows"])


if __name__ == "__main__":
    unittest.main()
