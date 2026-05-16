from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "check_same_scale_artifact_readiness.py"
SPEC = importlib.util.spec_from_file_location("check_same_scale_artifact_readiness", SCRIPT_PATH)
assert SPEC is not None
readiness = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys_modules_name = SPEC.name
import sys

sys.modules[sys_modules_name] = readiness
SPEC.loader.exec_module(readiness)


class SameScaleArtifactReadinessTests(unittest.TestCase):
    def test_ready_fixture_reports_all_required_categories_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = self._build_ready_report(Path(tmp))

        self.assertEqual(report["readiness_status"], "ready")
        self.assertTrue(report["gate_validation_ready"])
        self.assertTrue(report["gate_hazard_ready"])
        self.assertTrue(report["target_validation_ready"])
        self.assertTrue(report["target_hazard_ready"])
        self.assertTrue(report["target_summary_only_ready"])
        self.assertTrue(report["target_rebuildable_reduced_ready"])
        self.assertTrue(report["context_ready"])
        self.assertTrue(report["swisstlm3d_ready"])
        self.assertTrue(report["convergence_ready"])
        self.assertTrue(report["output_profile_ready"])
        self.assertTrue(report["hazard_context_overlap_ready"])
        self.assertEqual(report["missing_paths"], [])
        self.assertFalse(report["scale_up_authorized"])
        self.assertFalse(report["operational_claims_allowed"])
        categories = [entry["category"] for entry in report["regeneration_commands"]]
        self.assertIn("target_validation", categories)
        self.assertIn("convergence_comparison", categories)
        self.assertIn("same_scale_uncertainty_envelope", categories)
        self.assertIn("PYENV_VERSION=system", report["regeneration_commands"][0]["command"])
        self.assertIn("--format json", readiness.render_text_report(report))
        self.assertEqual(
            set(report.keys()),
            {
                "artifact_counts",
                "blocked_reason",
                "checked_paths",
                "convergence_ready",
                "context_ready",
                "gate_hazard_ready",
                "gate_validation_ready",
                "hazard_context_overlap_ready",
                "missing_paths",
                "operational_claims_allowed",
                "output_profile_ready",
                "readiness_status",
                "regeneration_commands",
                "scale_up_authorized",
                "swisstlm3d_ready",
                "target_hazard_ready",
                "target_rebuildable_reduced_case",
                "target_rebuildable_reduced_manifest",
                "target_rebuildable_reduced_ready",
                "target_rebuildable_reduced_root",
                "target_summary_only_ready",
                "target_validation_ready",
            },
        )

    def test_missing_target_hazard_manifest_is_blocked_with_exact_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = self._build_ready_report(root, omit_target_hazard_manifest=True)

        self.assertEqual(report["readiness_status"], "blocked_missing_inputs")
        self.assertFalse(report["target_hazard_ready"])
        self.assertIn(str(root / "hazard/results/tschamut_public_pilot/target_gate_v1/validation_tschamut_public_target_gate_v1_manifest.json"), report["missing_paths"])
        self.assertIn("target_hazard", {entry["category"]: entry["status"] for entry in report["regeneration_commands"]})
        self.assertIn("missing readiness inputs", report["blocked_reason"])

    def test_missing_swisstlm3d_metadata_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = self._build_ready_report(root, omit_swisstlm3d_metadata=True)

        self.assertEqual(report["readiness_status"], "blocked_missing_inputs")
        self.assertFalse(report["swisstlm3d_ready"])
        self.assertIn(str(root / "data/processed/swisstopo/tschamut_public_pilot/context/swisstlm3d/metadata.json"), report["missing_paths"])

    def test_text_output_mentions_ready_and_blocked_categories(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = self._build_ready_report(Path(tmp), omit_target_hazard_manifest=True)

        text = readiness.render_text_report(report)
        self.assertIn("target hazard: false", text)
        self.assertIn("missing_paths:", text)
        self.assertIn("regeneration_commands:", text)

    def _build_ready_report(
        self,
        root: Path,
        *,
        omit_target_hazard_manifest: bool = False,
        omit_swisstlm3d_metadata: bool = False,
    ) -> dict[str, object]:
        gate_validation_root = root / "validation/private/tschamut_public_pilot/gate_v1"
        gate_hazard_root = root / "hazard/results/tschamut_public_pilot/gate_v1"
        target_validation_root = root / "validation/private/tschamut_public_pilot/target_gate_v1"
        target_hazard_root = root / "hazard/results/tschamut_public_pilot/target_gate_v1"
        target_summary_only_root = root / "validation/private/tschamut_public_pilot/target_gate_v1_summary_only"
        target_rebuildable_reduced_root = root / "validation/private/tschamut_public_pilot/target_gate_v1_rebuildable_reduced"
        context_root = root / "data/processed/swisstopo/tschamut_public_pilot/context"
        swisstlm3d_root = context_root / "swisstlm3d"
        raw_archive = root / "data/raw/swisstopo/swisstlm3d/swisstlm3d_2021-04_2056_5728.shp.zip"
        local_archive = swisstlm3d_root / "swisstlm3d_2021-04_2056_5728.shp.zip"

        for path in [
            gate_validation_root,
            gate_hazard_root,
            target_validation_root,
            target_hazard_root,
            target_summary_only_root,
            target_rebuildable_reduced_root,
            context_root / "swisssurface3d_raster",
            context_root / "swissimage",
            context_root / "swissbuildings3d",
            swisstlm3d_root,
            raw_archive.parent,
            local_archive.parent,
        ]:
            path.mkdir(parents=True, exist_ok=True)

        self._write_case(gate_validation_root / "tschamut_public_conditional_gate_case.yaml", "validation_tschamut_public_conditional_gate_v1")
        self._write_case(target_validation_root / "tschamut_public_target_gate_case.yaml", "validation_tschamut_public_target_gate_v1")
        self._write_case(
            target_summary_only_root / "tschamut_public_target_gate_summary_only_case.yaml",
            "validation_tschamut_public_target_gate_v1_summary_only",
        )
        self._write_manifest(gate_validation_root / "validation_tschamut_public_conditional_gate_v1_manifest.json")
        self._write_manifest(target_validation_root / "validation_tschamut_public_target_gate_v1_manifest.json")
        self._write_manifest(
            target_summary_only_root / "validation_tschamut_public_target_gate_v1_summary_only_manifest.json",
            validation_output_mode="summary_only",
        )
        self._write_case(
            target_rebuildable_reduced_root / "tschamut_public_target_gate_rebuildable_reduced_case.yaml",
            "validation_tschamut_public_target_gate_v1_rebuildable_reduced",
        )
        self._write_manifest(
            target_rebuildable_reduced_root / "validation_tschamut_public_target_gate_v1_rebuildable_reduced_manifest.json",
            validation_output_mode="rebuildable_reduced_output",
        )

        gate_grid_a = gate_hazard_root / "reach_probability.asc"
        gate_grid_b = gate_hazard_root / "max_kinetic_energy.asc"
        target_grid_a = target_hazard_root / "reach_probability.asc"
        target_grid_b = target_hazard_root / "max_kinetic_energy.asc"
        self._write_grid(gate_grid_a, [[1.0, 0.0], [0.0, 2.0]])
        self._write_grid(gate_grid_b, [[0.0, 3.0], [1.0, 0.0]])
        self._write_grid(target_grid_a, [[1.0, 1.0], [0.0, 1.0]])
        self._write_grid(target_grid_b, [[0.0, 2.0], [1.0, 0.0]])
        self._write_manifest(
            gate_hazard_root / "validation_tschamut_public_conditional_gate_v1_manifest.json",
            cellwise_layers=[
                {"layer_name": "reach_probability", "grid_path": str(gate_grid_a), "format": "esri_ascii_grid", "thresholds": []},
                {"layer_name": "max_kinetic_energy", "grid_path": str(gate_grid_b), "format": "esri_ascii_grid", "thresholds": [1000.0]},
            ],
        )
        if not omit_target_hazard_manifest:
            self._write_manifest(
                target_hazard_root / "validation_tschamut_public_target_gate_v1_manifest.json",
                cellwise_layers=[
                    {"layer_name": "reach_probability", "grid_path": str(target_grid_a), "format": "esri_ascii_grid", "thresholds": []},
                    {"layer_name": "max_kinetic_energy", "grid_path": str(target_grid_b), "format": "esri_ascii_grid", "thresholds": [1000.0]},
                ],
            )

        for path in [
            context_root / "swisssurface3d_raster" / "tile.txt",
            context_root / "swissimage" / "tile.txt",
            context_root / "swissbuildings3d" / "tile.txt",
        ]:
            path.write_text("fixture\n", encoding="utf-8")

        raw_archive.write_bytes(b"raw archive")
        local_archive.write_bytes(b"local archive")
        if not omit_swisstlm3d_metadata:
            self._write_json(
                swisstlm3d_root / "metadata.json",
                {
                    "source_product": "swissTLM3D",
                    "staged_asset_present": True,
                    "raw_asset_path": str(raw_archive),
                    "local_asset_path": str(local_archive),
                    "coordinate_reference_system": {"epsg": 2056, "horizontal_name": "CH1903+ / LV95", "vertical_datum": "LN02"},
                    "local_asset_bytes": local_archive.stat().st_size,
                    "local_asset_sha256": "a" * 64,
                    "review_classification": "limiting",
                },
            )

        patches = {
            "GATE_VALIDATION_ROOT": gate_validation_root,
            "GATE_VALIDATION_CASE": gate_validation_root / "tschamut_public_conditional_gate_case.yaml",
            "GATE_VALIDATION_MANIFEST": gate_validation_root / "validation_tschamut_public_conditional_gate_v1_manifest.json",
            "GATE_HAZARD_ROOT": gate_hazard_root,
            "GATE_HAZARD_MANIFEST": gate_hazard_root / "validation_tschamut_public_conditional_gate_v1_manifest.json",
            "TARGET_VALIDATION_ROOT": target_validation_root,
            "TARGET_VALIDATION_CASE": target_validation_root / "tschamut_public_target_gate_case.yaml",
            "TARGET_VALIDATION_MANIFEST": target_validation_root / "validation_tschamut_public_target_gate_v1_manifest.json",
            "TARGET_HAZARD_ROOT": target_hazard_root,
            "TARGET_HAZARD_MANIFEST": (
                target_hazard_root / "validation_tschamut_public_target_gate_v1_manifest.json"
            ),
            "TARGET_SUMMARY_ONLY_ROOT": target_summary_only_root,
            "TARGET_SUMMARY_ONLY_CASE": target_summary_only_root / "tschamut_public_target_gate_summary_only_case.yaml",
            "TARGET_SUMMARY_ONLY_MANIFEST": target_summary_only_root / "validation_tschamut_public_target_gate_v1_summary_only_manifest.json",
            "TARGET_REBUILDABLE_REDUCED_ROOT": target_rebuildable_reduced_root,
            "TARGET_REBUILDABLE_REDUCED_CASE": (
                target_rebuildable_reduced_root / "tschamut_public_target_gate_rebuildable_reduced_case.yaml"
            ),
            "TARGET_REBUILDABLE_REDUCED_MANIFEST": (
                target_rebuildable_reduced_root / "validation_tschamut_public_target_gate_v1_rebuildable_reduced_manifest.json"
            ),
            "CONTEXT_ROOT": context_root,
            "CONTEXT_SWISSTLM3D_ROOT": swisstlm3d_root,
            "CONTEXT_SWISSTLM3D_METADATA": (
                swisstlm3d_root / "metadata.json"
            ),
            "CONTEXT_SWISSTLM3D_RAW_ARCHIVE": raw_archive,
        }
        with mock.patch.multiple(readiness, **patches):
            return readiness.build_readiness_report()

    @staticmethod
    def _write_case(path: Path, case_id: str) -> None:
        path.write_text(f"case_id: {case_id}\n", encoding="utf-8")

    @staticmethod
    def _write_manifest(path: Path, *, validation_output_mode: str | None = None, cellwise_layers: list[dict[str, object]] | None = None) -> None:
        payload: dict[str, object] = {"schema_version": "run_manifest_v1", "outputs": [{"kind": "diagnostics_json", "path": "dummy", "file_count": 1, "total_bytes": 1}]}
        if validation_output_mode is not None:
            payload["validation_output_mode"] = validation_output_mode
        if cellwise_layers is not None:
            payload["cellwise_layers"] = cellwise_layers
        path.write_text(json.dumps(payload), encoding="utf-8")

    @staticmethod
    def _write_json(path: Path, payload: dict[str, object]) -> None:
        path.write_text(json.dumps(payload), encoding="utf-8")

    @staticmethod
    def _write_grid(path: Path, values: list[list[float]]) -> None:
        rows = len(values)
        cols = len(values[0]) if values else 0
        lines = [
            f"ncols {cols}",
            f"nrows {rows}",
            "xllcorner 0",
            "yllcorner 0",
            "cellsize 1",
            "NODATA_value -9999",
        ]
        for row in values:
            lines.append(" ".join(str(value) for value in row))
        path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
