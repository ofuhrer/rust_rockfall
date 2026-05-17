from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import summarize_large_aoi_gis_cog_stress_test as stress


ROOT = Path(__file__).resolve().parents[1]


class LargeAoiGisCogStressTestTests(unittest.TestCase):
    def test_summary_reports_standard_blocked_root_and_converted_scope_delta(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            artifact_root = work / "target_gate_v1"
            converted_root = work / "target_gate_v1_cog_stress_test"
            self._write_package(artifact_root, artifact_id="validation_large_aoi_target_gate_v1", cloud_optimized=False)
            clock_values = iter([10.0, 10.5])

            def fake_conversion(input_root: Path, output_root: Path):
                self._write_converted_package(input_root, output_root)
                return {
                    "status": "cog_package_ready",
                    "input_root": str(input_root),
                    "output_root": str(output_root),
                    "package_file_count": len([path for path in output_root.rglob("*") if path.is_file()]),
                    "package_byte_count": sum(path.stat().st_size for path in output_root.rglob("*") if path.is_file()),
                    "copied_files": len([path for path in output_root.rglob("*") if path.is_file()]),
                    "all_declared_geotiffs_cog_ready": True,
                    "error": None,
                }

            report = stress.build_report(
                artifact_root=artifact_root,
                converted_package_root=converted_root,
                raster_metadata_provider=self._fake_cog_metadata,
                conversion_runner=fake_conversion,
                clock=lambda: next(clock_values),
            )

        self.assertEqual(report["stress_test_status"], "ready")
        self.assertEqual(report["standard_package_readiness_status"], "gis_package_ready_cog_blocked")
        self.assertEqual(report["converted_package_readiness_status"], "cog_package_ready_with_scope_delta")
        self.assertEqual(report["raster_count"], 3)
        self.assertEqual(report["converted_raster_count"], 2)
        self.assertEqual(report["package_runtime_seconds"], 12.5)
        self.assertEqual(report["cog_conversion_seconds"], 0.5)
        self.assertGreater(report["manifest_size_bytes"], 0)
        self.assertGreater(report["converted_manifest_size_bytes"], 0)
        self.assertEqual(report["layer_parity"]["status"], "scope_reduced")
        self.assertEqual(report["layer_parity"]["missing_layer_names"], ["jump_height_exceedance_1m"])
        self.assertEqual(report["missing_layer_summary"]["missing_layer_names"], ["jump_height_exceedance_1m"])
        self.assertEqual(report["first_gis_packaging_bottleneck"]["name"], "manifest_cloud_optimized_false")
        self.assertIn("scratch conversion is ready", report["first_gis_packaging_bottleneck"]["reason"])
        self.assertEqual(report["standard_package"]["package_runtime"]["total_wall_seconds"], 12.5)
        self.assertEqual(report["converted_package"]["readiness_status"], "cog_package_ready_with_scope_delta")
        self.assertTrue(report["conversion"]["all_declared_geotiffs_cog_ready"])
        self.assertEqual(report["conversion"]["status"], "cog_package_ready")
        json.dumps(report, sort_keys=True)
        text = stress.render_text_report(report)
        self.assertIn("standard_package_readiness_status: gis_package_ready_cog_blocked", text)
        self.assertIn("converted_package_readiness_status: cog_package_ready_with_scope_delta", text)
        self.assertIn("missing_layer_summary", text)

    def test_missing_standard_inputs_short_circuits_before_conversion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            artifact_root = work / "missing_target_gate_v1"
            converted_root = work / "target_gate_v1_cog_stress_test"
            called = {"value": False}

            def fake_conversion(input_root: Path, output_root: Path):
                called["value"] = True
                raise AssertionError("conversion should not run when the standard root is missing")

            report = stress.build_report(
                artifact_root=artifact_root,
                converted_package_root=converted_root,
                raster_metadata_provider=self._fake_cog_metadata,
                conversion_runner=fake_conversion,
                clock=lambda: 1.0,
            )

        self.assertFalse(called["value"])
        self.assertEqual(report["stress_test_status"], "blocked_missing_inputs")
        self.assertEqual(report["converted_package_readiness_status"], "not_run")
        self.assertEqual(report["first_gis_packaging_bottleneck"]["name"], "blocked_missing_inputs")
        self.assertEqual(report["first_gis_packaging_bottleneck"]["missing_inputs"], [str(artifact_root)])
        self.assertEqual(report["conversion"]["status"], "not_run")
        self.assertEqual(report["layer_parity"]["status"], "blocked_missing_inputs")
        self.assertEqual(report["missing_layer_summary"]["status"], "blocked_missing_inputs")
        text = stress.render_text_report(report)
        self.assertIn("blocked_missing_inputs", text)
        self.assertIn(str(artifact_root), text)

    def _write_package(self, root: Path, *, artifact_id: str, cloud_optimized: bool) -> None:
        root.mkdir(parents=True, exist_ok=True)
        input_dir = root / "input"
        input_dir.mkdir(parents=True, exist_ok=True)
        hazard_manifest = root / f"{artifact_id}_manifest.json"
        hazard_manifest.write_text(
            json.dumps(
                {
                    "schema_version": "hazard_manifest_v1",
                    "performance": {
                        "total_wall_seconds": 12.5,
                        "core_output_write_seconds": 3.25,
                        "manifest_write_seconds": 0.5,
                        "output_file_count": 14,
                        "output_bytes": 9876,
                    },
                },
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        raster_names = [
            "reach_probability",
            "max_kinetic_energy",
            "jump_height_exceedance_1m",
        ]
        raster_outputs = []
        for layer_name in raster_names:
            raster_path = root / f"{artifact_id}_{layer_name}.tif"
            raster_path.write_bytes(b"not a real tif, only a tiny fixture placeholder")
            raster_outputs.append(
                {
                    "layer_name": layer_name,
                    "path": str(raster_path),
                    "format": "geotiff",
                    "cloud_optimized": cloud_optimized,
                    "annualized": False,
                    "is_annualized": False,
                    "sha256": "placeholder",
                    "total_bytes": raster_path.stat().st_size,
                }
            )
        map_manifest = {
            "schema_version": "map_package_manifest_v1",
            "map_product_id": artifact_id,
            "map_product_version": "v1",
            "probability_mode": "sampling_weighted_conditional",
            "normalization_scope": "conditioned_on_filter",
            "source_zone_id": "source_zone_large_aoi",
            "source_zone_metadata_path": str(input_dir / "source_zone_metadata.yaml"),
            "scenario_table_path": str(input_dir / "scenario_table.csv"),
            "hazard_manifest_paths": [str(hazard_manifest)],
            "raster_outputs": raster_outputs,
            "layer_semantics": [
                {
                    "layer_name": layer_name,
                    "units": "dimensionless",
                    "conditioned_on": "source_zone_id=source_zone_large_aoi",
                    "is_annualized": False,
                    "numerator": f"{layer_name} numerator",
                    "denominator": "trajectory count conditioned on source/scenario metadata",
                    "weighted": layer_name.startswith("weighted_"),
                }
                for layer_name in raster_names
            ],
            "validation_context": ["large_aoi_fixture"],
            "limitations": ["Research diagnostic only; not operational."],
            "operational_status": "research_diagnostic",
        }
        pilot_manifest = {
            "schema_version": "pilot_gis_package_manifest_v1",
            "package_version": "pilot_gis_package_v1",
            "case_id": artifact_id,
            "operational_status": "research_diagnostic",
            "hazard_manifest_paths": [str(hazard_manifest)],
            "raster_outputs": raster_outputs,
            "parity_outputs": [],
            "manifest_outputs": [],
            "conditional_intensity_exceedance_curve_outputs": [],
            "source_zone_context": [],
            "terrain_metadata": {
                "kind": "terrain_metadata",
                "format": "yaml",
                "path": str(input_dir / "terrain_metadata.yaml"),
                "sha256": "placeholder",
                "total_bytes": 1,
            },
            "grid": {"source": "explicit", "xmin_m": 1.0, "ymin_m": 2.0, "ncols": 3, "nrows": 3, "cell_size_m": 2.0},
            "terrain": {
                "crs": "CH1903+ / LV95",
                "epsg": 2056,
                "vertical_datum": "LN02",
                "metadata_path": str(input_dir / "terrain_metadata.yaml"),
                "path": str(input_dir / "terrain.asc"),
                "resolution_m": 2.0,
                "nodata": -9999.0,
                "extent": {"xmin": 1.0, "xmax": 7.0, "ymin": 2.0, "ymax": 8.0},
            },
            "raster_contract": {
                "cloud_optimized": cloud_optimized,
                "csv_ascii_parity_required": True,
                "geopackage_included": False,
                "geotiff_required": True,
                "qgis_project_included": False,
            },
            "probability_claim_boundary": {
                "annualized": False,
                "current_allowed_product_labels": [
                    "unweighted_diagnostic",
                    "sampling_weighted_conditional",
                    "conditional_intensity_exceedance",
                ],
                "future_unsupported_product_labels": [
                    "physical_probability",
                    "annual_intensity_frequency",
                    "return_period",
                    "risk_map",
                    "operational_hazard_map",
                ],
            },
            "visual_qa": {
                "status": "not-run",
                "note": "manual QA not run",
                "reviewed_artifacts": [],
                "acceptance_scope": "local diagnostic GIS/QGIS review only",
                "accepted_for_operational_use": False,
            },
            "limitations": ["Research diagnostic only; not operational."],
        }
        (input_dir / "source_zone_metadata.yaml").write_text("source_zone: large_aoi\n", encoding="utf-8")
        (input_dir / "scenario_table.csv").write_text("scenario_id,probability\n1,1.0\n", encoding="utf-8")
        (input_dir / "terrain_metadata.yaml").write_text("terrain: large_aoi\n", encoding="utf-8")
        (input_dir / "terrain.asc").write_text("ncols 1\nnrows 1\nxllcorner 0\nyllcorner 0\ncellsize 1\nNODATA_value -9999\n1\n", encoding="utf-8")
        (root / f"{artifact_id}_map_package_manifest.json").write_text(json.dumps(map_manifest, indent=2, sort_keys=True), encoding="utf-8")
        (root / f"{artifact_id}_pilot_gis_package_manifest.json").write_text(json.dumps(pilot_manifest, indent=2, sort_keys=True), encoding="utf-8")

    def _write_converted_package(self, input_root: Path, output_root: Path) -> None:
        if output_root.exists():
            for path in sorted(output_root.rglob("*"), reverse=True):
                if path.is_file():
                    path.unlink()
                elif path.is_dir():
                    path.rmdir()
        output_root.mkdir(parents=True, exist_ok=True)
        for path in input_root.iterdir():
            if path.is_file():
                target = output_root / path.name
                target.write_bytes(path.read_bytes())
        map_manifest_path = next(output_root.glob("*_map_package_manifest.json"))
        pilot_manifest_path = next(output_root.glob("*_pilot_gis_package_manifest.json"))
        map_manifest = json.loads(map_manifest_path.read_text(encoding="utf-8"))
        pilot_manifest = json.loads(pilot_manifest_path.read_text(encoding="utf-8"))
        reduced_layer_names = [entry["layer_name"] for entry in map_manifest["raster_outputs"] if entry["layer_name"] != "jump_height_exceedance_1m"]
        for entry in map_manifest["raster_outputs"]:
            entry["path"] = str(output_root / Path(entry["path"]).name)
            entry["cloud_optimized"] = True
        map_manifest["raster_outputs"] = [entry for entry in map_manifest["raster_outputs"] if entry["layer_name"] in reduced_layer_names]
        map_manifest["layer_semantics"] = [
            entry for entry in map_manifest["layer_semantics"] if entry["layer_name"] in reduced_layer_names
        ]
        map_manifest["hazard_manifest_paths"] = [str(output_root / Path(map_manifest["hazard_manifest_paths"][0]).name)]
        pilot_manifest["hazard_manifest_paths"] = list(map_manifest["hazard_manifest_paths"])
        pilot_manifest["raster_outputs"] = list(map_manifest["raster_outputs"])
        pilot_manifest["raster_contract"]["cloud_optimized"] = True
        pilot_manifest["visual_qa"]["status"] = "not-run"
        map_manifest["cloud_optimized"] = True
        map_manifest["conversion_provenance"] = {
            "input_root": str(input_root),
            "output_root": str(output_root),
            "helper": "fake_conversion_for_test",
            "conversion_mode": "package_copy_and_cog_translate",
        }
        pilot_manifest["conversion_provenance"] = dict(map_manifest["conversion_provenance"])
        map_manifest_path.write_text(json.dumps(map_manifest, indent=2, sort_keys=True), encoding="utf-8")
        pilot_manifest_path.write_text(json.dumps(pilot_manifest, indent=2, sort_keys=True), encoding="utf-8")

    def _fake_cog_metadata(self, path: Path) -> dict[str, object]:
        return {
            "status": "ok",
            "driver": "GTiff",
            "size": [300, 304],
            "epsg": 2056,
            "geo_transform": [1.0, 2.0, 0.0, 610.0, 0.0, -2.0],
            "block_size": [256, 256],
            "nodata": -9999.0,
            "overview_count": 2,
            "image_structure": {"INTERLEAVE": "BAND", "LAYOUT": "COG", "COMPRESSION": "ZSTD"},
        }


if __name__ == "__main__":
    unittest.main()
