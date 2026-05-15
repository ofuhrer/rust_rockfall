from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/generate_tschamut_same_scale_cases.py"


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")


class TschamutSameScaleCaseGenerationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(dir=ROOT)
        self.root = Path(self.tmp.name)
        self.inputs = self.root / "inputs"
        self.output = self.root / "generated"
        self.build_fixture_inputs()

    def rel(self, path: str) -> str:
        return str(self.root.relative_to(ROOT) / path)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def build_fixture_inputs(self) -> None:
        write(
            self.inputs / "validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml",
            """
            schema_version: public_real_site_conditional_pilot_run_v1
            pilot_id: tschamut_public_pilot
            run_id: tschamut_public_conditional_gate_v1
            run_status: gate_run_completed
            operational_status: research_diagnostic
            input_freeze:
              terrain_metadata_path: data/processed/swisstopo/tschamut_public_pilot/input/terrain.yaml
              source_zone_metadata_path: data/processed/swisstopo/tschamut_public_pilot/input/source_zone.yaml
              scenario_table_path: data/processed/swisstopo/tschamut_public_pilot/input/scenario.csv
              source_scenario_policy_path: validation/policies/policy.yaml
            sampling_plan:
              seed: 34014
              gate_run_trajectories_per_release_zone: 6
              target_trajectories_per_release_zone: 100
            """,
        )
        write(
            self.inputs / "validation/pilot_runs/tschamut_public_scalable_conditional_target_gate_v1.yaml",
            """
            schema_version: scalable_conditional_target_gate_v1
            pilot_id: tschamut_public_pilot
            run_id: tschamut_public_scalable_conditional_target_gate_v1
            target_execution_plan:
              target_trajectories_per_release_zone: 100
            """,
        )
        write(
            self.inputs / "validation/policies/policy.yaml",
            """
            schema_version: source_zone_block_scenario_policy_v1
            pilot_id: tschamut_public_pilot
            source_zone_policy:
              source_zone_id: tschamut_public_lps_release_bbox
              release_sampling:
                seed: 34014
            block_scenario_policy:
              scenarios:
                - block_scenario_id: tschamut_public_block_small
                  block_mass_kg: 40.0
                  block_radius_m: 0.16
                - block_scenario_id: tschamut_public_block_medium
                  block_mass_kg: 69.0
                  block_radius_m: 0.176667
                - block_scenario_id: tschamut_public_block_large
                  block_mass_kg: 79.0
                  block_radius_m: 0.198333
            """,
        )
        write(
            self.inputs / "data/processed/swisstopo/tschamut_public_pilot/input/source_zone.yaml",
            """
            source_zone_id: tschamut_public_lps_release_bbox
            """,
        )
        write(
            self.inputs / "data/processed/swisstopo/tschamut_public_pilot/input/scenario.csv",
            "scenario_id,source_zone_id\ns1,sz1\n",
        )
        write(
            self.inputs / "data/processed/swisstopo/tschamut_public_pilot/input/release_points_lv95.csv",
            """
            trajectory_id,experiment_id,x_m,y_m,z_m,ground_z_m,vx_mps,vy_mps,vz_mps,block_id,mass_kg,radius_m,source
            v020,tschamut2014,1,2,3,4,5,6,7,1,69.0,0.176667,src
            v010,tschamut2014,10,20,30,40,50,60,70,4,40.0,0.16,src
            v004,tschamut2014,11,21,31,41,51,61,71,1,69.0,0.176667,src
            """,
        )
        write(
            self.inputs / "data/processed/swisstopo/tschamut_public_pilot/input/observed_deposition_lv95.csv",
            """
            trajectory_id,experiment_id,x_m,y_m,z_m,ground_z_m,release_x_m,release_y_m,release_z_m,observed_runout_m,block_id,mass_kg,radius_m,source
            v010,tschamut2014,1,2,3,4,10,20,30,42,4,40.0,0.16,src
            v004,tschamut2014,11,21,31,41,11,21,31,43,1,69.0,0.176667,src
            v020,tschamut2014,1,2,3,4,1,2,3,44,1,69.0,0.176667,src
            """,
        )
        write(
            self.inputs / "data/processed/swisstopo/tschamut_public_pilot/input/terrain.yaml",
            "schema_version: 1\n",
        )
        (self.inputs / "data/processed/swisstopo/tschamut_public_pilot/input/terrain.asc").write_text("ncols 1\nnrows 1\nxllcorner 0\nyllcorner 0\ncellsize 1\nNODATA_value -9999\n0\n", encoding="utf-8")

    def run_script(self, *extra: str) -> subprocess.CompletedProcess[str]:
        args = [
            sys.executable,
            str(SCRIPT),
            "--format",
            "json",
            "--output-root",
            str(self.output),
            "--gate-record",
            str(self.inputs / "validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml"),
            "--target-record",
            str(self.inputs / "validation/pilot_runs/tschamut_public_scalable_conditional_target_gate_v1.yaml"),
            "--source-scenario-policy",
            str(self.inputs / "validation/policies/policy.yaml"),
            "--source-zone-metadata",
            str(self.inputs / "data/processed/swisstopo/tschamut_public_pilot/input/source_zone.yaml"),
            "--scenario-table",
            str(self.inputs / "data/processed/swisstopo/tschamut_public_pilot/input/scenario.csv"),
            "--release-points",
            str(self.inputs / "data/processed/swisstopo/tschamut_public_pilot/input/release_points_lv95.csv"),
            "--observed-deposition",
            str(self.inputs / "data/processed/swisstopo/tschamut_public_pilot/input/observed_deposition_lv95.csv"),
            "--terrain-metadata",
            str(self.inputs / "data/processed/swisstopo/tschamut_public_pilot/input/terrain.yaml"),
            "--terrain-crop",
            str(self.inputs / "data/processed/swisstopo/tschamut_public_pilot/input/terrain.asc"),
        ]
        args.extend(extra)
        return subprocess.run(args, check=False, capture_output=True, text=True)

    def test_generates_deterministic_gate_and_target_cases(self) -> None:
        result = self.run_script()
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["case_regeneration_status"], "ready")
        self.assertEqual(report["generated_case_ids"], ["validation_tschamut_public_conditional_gate_v1", "validation_tschamut_public_target_gate_v1"])
        gate_path = self.output / "gate_v1/tschamut_public_conditional_gate_case.yaml"
        target_path = self.output / "target_gate_v1/tschamut_public_target_gate_case.yaml"
        self.assertTrue(gate_path.exists())
        self.assertTrue(target_path.exists())

        gate_text_first = gate_path.read_text(encoding="utf-8")
        target_text_first = target_path.read_text(encoding="utf-8")
        second = self.run_script()
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(gate_text_first, gate_path.read_text(encoding="utf-8"))
        self.assertEqual(target_text_first, target_path.read_text(encoding="utf-8"))
        gate = yaml_load(gate_path)
        target = yaml_load(target_path)
        self.assertNotEqual(gate["case_id"], target["case_id"])
        self.assertNotEqual(gate["outputs"]["manifest_json"], target["outputs"]["manifest_json"])
        self.assertEqual(gate["probabilistic_metadata"]["source_zone_metadata_path"], self.rel("inputs/data/processed/swisstopo/tschamut_public_pilot/input/source_zone.yaml"))
        self.assertEqual(gate["probabilistic_metadata"]["scenario_table_path"], self.rel("inputs/data/processed/swisstopo/tschamut_public_pilot/input/scenario.csv"))
        self.assertEqual(gate["hazard_layers"]["statistics"]["jump_height_exceedance_m"], [1.0, 2.0])
        self.assertEqual(target["hazard_layers"]["statistics"]["jump_height_exceedance_m"], [0.5, 1.0, 2.0])
        self.assertEqual(gate["random"]["ensemble_size"], 6)
        self.assertEqual(target["random"]["ensemble_size"], 100)
        self.assertEqual(gate["release"]["position"], [11.0, 21.0, 31.0])
        self.assertFalse(report["scale_up_authorized"])
        self.assertFalse(report["operational_claims_allowed"])

    def test_missing_inputs_block_explicitly(self) -> None:
        (self.inputs / "data/processed/swisstopo/tschamut_public_pilot/input/source_zone.yaml").unlink()
        result = self.run_script("--dry-run")
        self.assertNotEqual(result.returncode, 0)
        report = json.loads(result.stdout)
        self.assertEqual(report["case_regeneration_status"], "blocked_missing_inputs")
        self.assertIn("source_zone.yaml", " ".join(report["missing_input_paths"]))

    def test_json_includes_regeneration_metadata(self) -> None:
        result = self.run_script("--dry-run")
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        for key in (
            "source_record_paths",
            "required_input_paths",
            "generated_case_paths",
            "output_path_strategy",
            "deterministic_generation_evidence",
            "defaults_changed",
            "physics_changed",
            "thresholds_changed",
            "source_zone_semantics_changed",
            "scenario_probability_semantics_changed",
        ):
            self.assertIn(key, report)
        self.assertFalse(report["defaults_changed"])
        self.assertFalse(report["physics_changed"])
        self.assertFalse(report["thresholds_changed"])
        self.assertFalse(report["source_zone_semantics_changed"])
        self.assertFalse(report["scenario_probability_semantics_changed"])


def yaml_load(path: Path) -> dict[str, object]:
    import yaml  # type: ignore

    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
