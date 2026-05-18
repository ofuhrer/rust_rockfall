from __future__ import annotations

import importlib.util
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "recover_balfrin_target_area_spatial_artifacts_from_run_root.py"
SPEC = importlib.util.spec_from_file_location("recover_balfrin_target_area_spatial_artifacts_from_run_root", SCRIPT_PATH)
assert SPEC is not None
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class BalfrinTargetAreaSpatialArtifactRecoveryTests(unittest.TestCase):
    def _ready_access(self) -> dict[str, object]:
        return {
            "schema_version": "balfrin_remote_access_preflight_v1",
            "status": "ready_for_read_only_collection",
            "ready_for_read_only_collection": True,
            "read_only": True,
            "live_submission_authorized": False,
            "checked_commands": [
                {"name": "ssh_availability", "status": "pass", "returncode": 0},
                {"name": "remote_clone", "status": "pass", "returncode": 0},
                {"name": "run_root_visibility", "status": "pass", "returncode": 0},
                {"name": "scheduler_query", "status": "pass", "returncode": 0},
            ],
        }

    def _blocked_access(self) -> dict[str, object]:
        return {
            "schema_version": "balfrin_remote_access_preflight_v1",
            "status": "blocked_ssh_unavailable",
            "ready_for_read_only_collection": False,
            "read_only": True,
            "live_submission_authorized": False,
            "checked_commands": [
                {"name": "ssh_availability", "status": "fail", "returncode": 255},
            ],
        }

    def _write_run_root(self, run_root: Path, *, complete: bool) -> None:
        output = run_root / "output"
        output.mkdir(parents=True)
        (run_root / "command_plan.json").write_text(
            json.dumps(
                {
                    "commands": [
                        {
                            "name": "build_conditional_hazard_layers",
                            "cwd": ".",
                            "command": ["python3", "scripts/build_hazard_layers.py", "--output-dir", "output"],
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        manifest = {
            "schema_version": "run_manifest_v1",
            "case_id": "balfrin_target_area_spatial_fixture",
            "cellwise_layers": [
                {"key": "max_kinetic_energy", "grid_path": "max_kinetic_energy.asc"},
                {"key": "max_jump_height", "grid_path": "max_jump_height.asc"},
                {"key": "velocity_exceedance_5mps", "grid_path": "velocity_exceedance_5mps.asc"},
            ],
            "outputs": [
                {"kind": "map_package_manifest", "path": "map_package_manifest.json"},
                {"kind": "pilot_gis_package_manifest", "path": "pilot_gis_package_manifest.json"},
            ],
        }
        (output / "validation_balfrin_target_area_manifest.json").write_text(
            json.dumps(manifest),
            encoding="utf-8",
        )
        if not complete:
            return
        for filename in (
            "map_package_manifest.json",
            "pilot_gis_package_manifest.json",
            "max_kinetic_energy.asc",
            "max_jump_height.asc",
            "velocity_exceedance_5mps.asc",
            "spatial_uncertainty_layer_summary.json",
            "spatial_uncertainty_region_products.geojson",
            "spatial_confidence_product_manifest.json",
        ):
            (output / filename).write_text("{}\n", encoding="utf-8")

    def test_complete_fixture_recovers_required_target_area_spatial_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            run_root = Path(tmpdir) / "run_root"
            self._write_run_root(run_root, complete=True)

            report = MODULE.build_report(access_report=self._ready_access(), local_run_root=run_root)

        self.assertEqual(report["schema_version"], "balfrin_target_area_spatial_artifact_recovery_v1")
        self.assertEqual(report["report_status"], "spatial_artifacts_recovered")
        self.assertEqual(
            report["spatial_artifact_recovery"]["status_counts"],
            {"recovered": len(MODULE.REQUIRED_SPATIAL_ARTIFACTS)},
        )
        self.assertEqual(report["spatial_interpretation_evidence"]["status"], "recovered_existing_run_root")
        self.assertTrue(
            report["spatial_interpretation_evidence"]["usable_as_target_area_spatial_interpretation_evidence"]
        )
        self.assertFalse(report["claim_boundaries"]["physical_validation_evidence_established"])
        for entry in report["execution_metrics_closure_separation"]["entries"]:
            self.assertEqual(entry["status"], "not_required_for_execution_metrics_closure")

    def test_unavailable_spatial_artifacts_remain_explicit_non_validation_deferrals(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            run_root = Path(tmpdir) / "run_root"
            self._write_run_root(run_root, complete=False)

            report = MODULE.build_report(access_report=self._ready_access(), local_run_root=run_root)

        recovery = report["spatial_artifact_recovery"]
        self.assertEqual(report["report_status"], "spatial_artifacts_deferred")
        self.assertGreater(recovery["status_counts"]["unavailable_from_preserved_root"], 0)
        self.assertIn("map_package_manifest", recovery["unrecovered_artifacts"])
        self.assertEqual(
            recovery["by_artifact"]["map_package_manifest"]["status"],
            "unavailable_from_preserved_root",
        )
        self.assertEqual(
            report["spatial_interpretation_evidence"]["status"],
            "deferred_missing_spatial_artifacts",
        )
        self.assertEqual(
            report["spatial_interpretation_evidence"]["physical_validation_evidence_status"],
            "not_established",
        )
        self.assertFalse(report["spatial_interpretation_evidence"]["usable_as_physical_validation_evidence"])
        self.assertFalse(report["claim_boundaries"]["physical_probability_claims_allowed"])

    def test_access_blocked_fails_closed_without_remote_collection(self) -> None:
        report = MODULE.build_report(access_report=self._blocked_access())

        self.assertEqual(report["report_status"], "blocked_access")
        self.assertEqual(report["collection"]["status"], "not_run")
        self.assertEqual(
            report["spatial_artifact_recovery"]["status_counts"],
            {"blocked_access": len(MODULE.REQUIRED_SPATIAL_ARTIFACTS)},
        )
        self.assertEqual(report["spatial_interpretation_evidence"]["status"], "blocked_access")
        for artifact_id in report["spatial_artifact_recovery"]["required_artifacts"]:
            self.assertEqual(
                report["spatial_artifact_recovery"]["by_artifact"][artifact_id]["status"],
                "blocked_access",
            )

    def test_cli_writes_spatial_artifact_recovery_report_from_local_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            run_root = tmp / "run_root"
            self._write_run_root(run_root, complete=False)
            access_json = tmp / "access.json"
            artifact_dir = tmp / "validation/private/tschamut_public_pilot/balfrin_target_area_spatial_artifact_recovery_v1"
            access_json.write_text(json.dumps(self._ready_access()), encoding="utf-8")

            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = MODULE.main(
                    [
                        "--balfrin-access-json",
                        str(access_json),
                        "--local-run-root",
                        str(run_root),
                        "--artifact-dir",
                        str(artifact_dir),
                        "--format",
                        "json",
                    ]
                )

            self.assertEqual(exit_code, 0)
            json_path = artifact_dir / "balfrin_target_area_spatial_artifact_recovery_v1.json"
            text_path = artifact_dir / "balfrin_target_area_spatial_artifact_recovery_v1.txt"
            self.assertTrue(json_path.exists())
            self.assertTrue(text_path.exists())
            report = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(report["report_status"], "spatial_artifacts_deferred")
            self.assertIn("Balfrin Target-Area Spatial Artifact Recovery", text_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
