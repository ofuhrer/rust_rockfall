from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "summarize_bounded_reducer_runtime_scaling.py"
SPEC = importlib.util.spec_from_file_location("summarize_bounded_reducer_runtime_scaling", SCRIPT_PATH)
assert SPEC is not None
summary_script = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = summary_script
SPEC.loader.exec_module(summary_script)


class BoundedReducerRuntimeScalingTests(unittest.TestCase):
    def test_reports_ready_scaling_comparisons(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifacts = self._write_artifacts(Path(tmp))
            report = summary_script.build_report(artifacts)

            self.assertEqual(report["reducer_scaling_status"], "measured_existing_artifacts")
            self.assertEqual(report["readiness_status"], "ready")
            self.assertTrue(report["local_single_job_sufficient_for_next_step"])
            self.assertFalse(report["distributed_execution_authorized"])
            self.assertEqual(report["bottleneck_classification"], "validation_output_size")
            self.assertEqual(report["hazard_layer_counts"]["gate_v1"], 2)
            self.assertEqual(report["reducer_worker_counts"]["gate_v1"], 2)
            self.assertEqual(report["validation_roots"][2]["artifact_id"], "target_rebuildable_reduced")
            self.assertEqual(report["artifacts_measured"][2]["validation_output_mode"], "rebuildable_reduced_output")
            self.assertEqual(report["reducer_worker_counts"]["sampling_sensitivity_v1_full"], None)
            self.assertTrue(report["artifacts_measured"][0]["map_package_manifest_present"])
            self.assertTrue(report["artifacts_measured"][0]["pilot_gis_manifest_present"])
            self.assertEqual(report["comparison_pairs"][0]["label"], "gate_vs_target")
            self.assertEqual(report["comparison_pairs"][1]["label"], "target_full_vs_native_rebuildable_reduced")
            self.assertGreater(report["comparison_pairs"][0]["validation_file_count_delta"], 0)
            self.assertEqual(report["bottleneck_classification"], "validation_output_size")

    def test_missing_inputs_are_blocked_explicitly(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifacts = self._write_artifacts(Path(tmp))
            missing = artifacts[1].hazard_manifest
            missing.unlink()

            with self.assertRaisesRegex(summary_script.BoundedReducerRuntimeScalingError, "missing"):
                summary_script.build_report(artifacts)

            blocked = summary_script.build_report(artifacts, allow_missing=True)
            self.assertEqual(blocked["reducer_scaling_status"], "blocked_missing_inputs")
            self.assertIn("missing same-scale artifacts", blocked["blocked_reason"])

    def test_text_render_includes_required_contract_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifacts = self._write_artifacts(Path(tmp))
            report = summary_script.build_report(artifacts)
            text = summary_script.render_text(report)

            self.assertIn("reducer_scaling_status: measured_existing_artifacts", text)
            self.assertIn("timing_source: manifest_performance.total_wall_seconds", text)
            self.assertIn("local_single_job_sufficient_for_next_step: true", text)
            self.assertIn("distributed_execution_authorized: false", text)
            self.assertIn("gate_vs_target", text)

    def _write_artifacts(self, root: Path):
        specs = []
        for item in [
            ("gate_v1", 3, 1000, 1.0, 4, 4000, 2.0, 2, None),
            ("target_gate_v1", 5, 5000, 3.0, 6, 6000, 4.0, 2, None),
            ("target_rebuildable_reduced", 2, 1500, 1.5, 3, 2500, 2.2, 2, "rebuildable_reduced_output"),
            ("sampling_sensitivity_v1_full", 4, 4500, 2.5, 5, 5500, 3.5, None, None),
            ("sampling_sensitivity_v2_full", 4, 4700, 2.2, 5, 5200, 3.8, 2, None),
        ]:
            artifact_id, validation_files, validation_bytes, validation_wall, hazard_files, hazard_bytes, hazard_wall, reducer_workers, validation_mode = item
            validation_root = root / "validation" / artifact_id
            hazard_root = root / "hazard" / artifact_id
            validation_manifest = validation_root / f"{artifact_id}_validation_manifest.json"
            hazard_manifest = hazard_root / f"{artifact_id}_hazard_manifest.json"
            self._write_manifest(
                validation_manifest,
                self._validation_manifest(artifact_id, validation_files, validation_bytes, validation_wall, validation_mode),
            )
            self._write_manifest(hazard_manifest, self._hazard_manifest(artifact_id, hazard_files, hazard_bytes, hazard_wall, reducer_workers))
            # file-system footprints
            for i in range(validation_files):
                (validation_root / f"v{i}.txt").parent.mkdir(parents=True, exist_ok=True)
                (validation_root / f"v{i}.txt").write_text("x", encoding="utf-8")
            for i in range(hazard_files):
                (hazard_root / f"h{i}.txt").parent.mkdir(parents=True, exist_ok=True)
                (hazard_root / f"h{i}.txt").write_text("x", encoding="utf-8")
            map_manifest = hazard_root / f"{artifact_id}_map_package_manifest.json"
            gis_manifest = hazard_root / f"{artifact_id}_pilot_gis_package_manifest.json"
            self._write_manifest(map_manifest, {"schema_version": "map_package_manifest_v1"})
            self._write_manifest(gis_manifest, {"schema_version": "pilot_gis_package_manifest_v1"})
            self._hazard_outputs(hazard_manifest, map_manifest, gis_manifest)
            specs.append(
                summary_script.ArtifactSpec(
                    artifact_id,
                    validation_root,
                    validation_manifest,
                    hazard_root,
                    hazard_manifest,
                )
            )
        return tuple(specs)

    def _validation_manifest(
        self,
        artifact_id: str,
        file_count: int,
        total_bytes: int,
        wall_seconds: float,
        validation_mode: str | None = None,
    ) -> dict:
        return {
            "schema_version": "run_manifest_v1",
            "case_id": artifact_id,
            "performance": {
                "total_wall_seconds": wall_seconds,
                "output_file_count": file_count,
                "output_bytes": total_bytes,
            },
            **({"validation_output_mode": validation_mode} if validation_mode is not None else {}),
            "outputs": [],
        }

    def _hazard_manifest(self, artifact_id: str, file_count: int, total_bytes: int, wall_seconds: float, reducer_workers: int | None) -> dict:
        return {
            "schema_version": "run_manifest_v1",
            "case_id": artifact_id,
            "performance": {
                "total_wall_seconds": wall_seconds,
                "output_file_count": file_count,
                "output_bytes": total_bytes,
            },
            "cellwise_layers": [{"name": "layer_a"}, {"name": "layer_b"}],
            "reducer_execution": {
                "worker_count": reducer_workers,
                "chunk_count": 2,
                "merge_order": "sorted_chunk_id",
            },
            "outputs": [],
        }

    def _hazard_outputs(self, hazard_manifest_path: Path, map_manifest: Path, gis_manifest: Path) -> None:
        data = json.loads(hazard_manifest_path.read_text(encoding="utf-8"))
        data["outputs"] = [
            {"kind": "map_package_manifest", "path": str(map_manifest)},
            {"kind": "pilot_gis_package_manifest", "path": str(gis_manifest)},
        ]
        hazard_manifest_path.write_text(json.dumps(data), encoding="utf-8")

    def _write_manifest(self, path: Path, data: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data), encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
