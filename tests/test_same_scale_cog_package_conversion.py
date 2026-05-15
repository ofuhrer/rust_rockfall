from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.audit_gis_cog_package_readiness import build_gis_cog_readiness_report
from scripts.convert_same_scale_package_to_cog import convert_same_scale_package_to_cog


class SameScaleCogPackageConversionTest(unittest.TestCase):
    def test_convert_same_scale_package_to_cog_rewrites_ignored_copy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            input_root = tmp_path / "gate_v1"
            output_root = tmp_path / "gate_v1_cog_poc"
            self._write_package(input_root, artifact_id="validation_tschamut_public_conditional_gate_v1", cloud_optimized=False)

            source_files = sorted(path.name for path in input_root.iterdir())
            original_manifest = json.loads((input_root / "validation_tschamut_public_conditional_gate_v1_pilot_gis_package_manifest.json").read_text())

            def fake_convert_to_cog(input_path: Path, output_path: Path, *, overwrite: bool = False):
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_bytes(f"converted:{input_path.name}".encode("utf-8"))
                return {
                    "status": "cog_conversion_sample_ready",
                    "input_path": str(input_path),
                    "output_path": str(output_path),
                    "verification": {"status": "ok"},
                    "output_exists": True,
                    "output_bytes": output_path.stat().st_size,
                    "blockers": [],
                }

            def fake_gdal(path: Path):
                return {
                    "status": "ok",
                    "driver": "GTiff",
                    "size": [300, 304],
                    "geo_transform": [2696376.0, 2.0, 0.0, 1167992.0, 0.0, -2.0],
                    "block_size": [256, 256],
                    "nodata": -9999.0,
                    "overview_count": 2,
                    "image_structure": {"LAYOUT": "COG", "COMPRESSION": "ZSTD"},
                    "sample_raster_tiled": True,
                    "sample_raster_overviews": True,
                    "sample_raster_cog_layout": True,
                }

            with patch("scripts.convert_same_scale_package_to_cog.shutil.which", return_value="/usr/bin/tool"), patch(
                "scripts.convert_same_scale_package_to_cog.convert_to_cog",
                side_effect=fake_convert_to_cog,
            ), patch("scripts.convert_same_scale_package_to_cog.inspect_gdal", side_effect=fake_gdal):
                report = convert_same_scale_package_to_cog(input_root, output_root, overwrite=True)

            self.assertEqual(report["status"], "cog_package_ready")
            self.assertEqual(report["package_file_count"], len([path for path in output_root.rglob("*") if path.is_file()]))
            self.assertTrue(report["all_declared_geotiffs_cog_ready"])
            self.assertEqual(len(report["converted_rasters"]), 2)
            self.assertTrue(output_root.exists())
            self.assertTrue((output_root / "validation_tschamut_public_conditional_gate_v1_manifest.json").exists())
            self.assertTrue((output_root / "validation_tschamut_public_conditional_gate_v1_pilot_gis_package_manifest.json").exists())
            self.assertEqual(sorted(path.name for path in input_root.iterdir()), source_files)

            output_manifest = json.loads((output_root / "validation_tschamut_public_conditional_gate_v1_pilot_gis_package_manifest.json").read_text())
            output_map_manifest = json.loads((output_root / "validation_tschamut_public_conditional_gate_v1_map_package_manifest.json").read_text())
            self.assertEqual(output_manifest["visual_qa"]["status"], "not-run")
            self.assertTrue(output_manifest["raster_contract"]["cloud_optimized"])
            self.assertIn(str(output_root), output_manifest["conversion_provenance"]["output_root"])
            self.assertTrue(output_map_manifest["raster_outputs"][0]["cloud_optimized"])
            self.assertIn(str(output_root), output_map_manifest["raster_outputs"][0]["path"])
            source_manifest = json.loads((input_root / "validation_tschamut_public_conditional_gate_v1_pilot_gis_package_manifest.json").read_text())
            self.assertFalse(source_manifest["raster_contract"]["cloud_optimized"])
            self.assertFalse(original_manifest["raster_outputs"][0]["cloud_optimized"])

    def test_audit_distinguishes_standard_blocked_and_converted_ready_package(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            blocked_root = tmp_path / "blocked"
            ready_root = tmp_path / "ready"
            self._write_package(blocked_root, artifact_id="validation_tschamut_public_conditional_gate_v1", cloud_optimized=False)
            self._write_package(ready_root, artifact_id="validation_tschamut_public_conditional_gate_v1", cloud_optimized=True)

            def fake_cog_metadata(path: Path):
                return {
                    "status": "ok",
                    "driver": "GTiff",
                    "size": [300, 304],
                    "geo_transform": [2696376.0, 2.0, 0.0, 1167992.0, 0.0, -2.0],
                    "block_size": [256, 256],
                    "nodata": -9999.0,
                    "overview_count": 2,
                    "image_structure": {"LAYOUT": "COG", "COMPRESSION": "ZSTD"},
                    "sample_raster_tiled": True,
                    "sample_raster_overviews": True,
                    "sample_raster_cog_layout": True,
                }

            report = build_gis_cog_readiness_report(
                artifact_roots=[blocked_root],
                converted_package_roots=[ready_root],
                raster_metadata_provider=fake_cog_metadata,
            )

        self.assertEqual(report["gis_cog_readiness_status"], "gis_package_ready_cog_blocked")
        self.assertEqual(report["converted_package_status"]["validation_tschamut_public_conditional_gate_v1"], "cog_package_ready")
        self.assertEqual(report["converted_packages"][0]["cog_package_status"], "cog_package_ready")
        self.assertFalse(report["scale_up_authorized"])
        self.assertFalse(report["operational_claims_allowed"])

    def test_blocked_missing_inputs_and_missing_gdal_are_explicit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            output_root = tmp_path / "cog"
            missing_root = tmp_path / "missing"
            report = convert_same_scale_package_to_cog(missing_root, output_root, overwrite=True)
            self.assertEqual(report["status"], "blocked_missing_inputs")

            input_root = tmp_path / "input"
            self._write_package(input_root, artifact_id="validation_tschamut_public_conditional_gate_v1", cloud_optimized=False)
            with patch("scripts.convert_same_scale_package_to_cog.shutil.which", return_value=None):
                missing_gdal_report = convert_same_scale_package_to_cog(input_root, output_root, overwrite=True)
            self.assertEqual(missing_gdal_report["status"], "blocked_missing_gdal")

    def _write_package(self, root: Path, *, artifact_id: str, cloud_optimized: bool) -> None:
        root.mkdir(parents=True, exist_ok=True)
        input_dir = root / "input"
        input_dir.mkdir(parents=True, exist_ok=True)
        (input_dir / "terrain.asc").write_text("ncols 1\nnrows 1\nxllcorner 0\nyllcorner 0\ncellsize 1\nNODATA_value -9999\n1\n", encoding="utf-8")
        (input_dir / "terrain_metadata.yaml").write_text("terrain: test\n", encoding="utf-8")
        (input_dir / "source_zone_metadata.yaml").write_text("source_zone: test\n", encoding="utf-8")
        (input_dir / "scenario_table.csv").write_text("scenario_id,probability\n1,1.0\n", encoding="utf-8")
        raster_names = [
            f"{artifact_id}_reach_probability.tif",
            f"{artifact_id}_max_kinetic_energy.tif",
        ]
        raster_paths = []
        for name in raster_names:
            path = root / name
            path.write_bytes(b"placeholder raster")
            raster_paths.append(path)
        hazard_manifest = root / f"{artifact_id}_manifest.json"
        hazard_manifest.write_text(json.dumps({"schema_version": "manifest_v1"}, indent=2, sort_keys=True), encoding="utf-8")
        map_manifest = {
            "schema_version": "map_package_manifest_v1",
            "map_product_id": artifact_id,
            "map_product_version": "v1",
            "probability_mode": "sampling_weighted_conditional",
            "normalization_scope": "conditioned_on_filter",
            "source_zone_id": "source_zone_a",
            "source_zone_metadata_path": str(root / "input" / "source_zone_metadata.yaml"),
            "scenario_table_path": str(root / "input" / "scenario_table.csv"),
            "hazard_manifest_paths": [str(hazard_manifest)],
            "raster_outputs": [
                {
                    "layer_name": "reach_probability",
                    "path": str(raster_paths[0]),
                    "format": "geotiff",
                    "cloud_optimized": cloud_optimized,
                    "annualized": False,
                    "is_annualized": False,
                    "sha256": "abc",
                    "total_bytes": raster_paths[0].stat().st_size,
                },
                {
                    "layer_name": "max_kinetic_energy",
                    "path": str(raster_paths[1]),
                    "format": "geotiff",
                    "cloud_optimized": cloud_optimized,
                    "annualized": False,
                    "is_annualized": False,
                    "sha256": "def",
                    "total_bytes": raster_paths[1].stat().st_size,
                },
            ],
            "layer_semantics": [],
            "limitations": ["Research diagnostic only; not operational."],
            "operational_status": "diagnostic",
            "validation_context": {"status": "local-diagnostic"},
        }
        pilot_manifest = {
            "schema_version": "pilot_gis_package_manifest_v1",
            "package_version": "v1",
            "case_id": artifact_id,
            "grid": {"cell_size_m": 2.0, "ncols": 300, "nrows": 304, "source": "explicit", "xmin_m": 1.0, "ymin_m": 2.0},
            "terrain": {
                "crs": "CH1903+ / LV95",
                "epsg": 2056,
                "extent": {"xmin": 1.0, "xmax": 601.0, "ymin": 2.0, "ymax": 610.0},
                "license": "test",
                "metadata_path": str(root / "input" / "terrain_metadata.yaml"),
                "nodata": -9999.0,
                "path": str(root / "input" / "terrain.asc"),
                "processed_sha256": "abc",
                "resolution_m": 2.0,
                "source_dataset": "swisstopo_swissalti3d",
                "source_filename": "source.tif",
                "source_product": "swissALTI3D 2 m COG",
                "terrain_type": "ascii_dem_clamped",
                "vertical_datum": "LN02",
            },
            "terrain_metadata": {
                "file_count": 1,
                "format": "yaml",
                "kind": "terrain_metadata",
                "path": str(root / "input" / "terrain_metadata.yaml"),
                "sha256": "abc",
                "total_bytes": 1,
            },
            "hazard_manifest_paths": [str(hazard_manifest)],
            "raster_outputs": map_manifest["raster_outputs"],
            "manifest_outputs": [],
            "parity_outputs": [],
            "conditional_intensity_exceedance_curve_outputs": [],
            "visual_qa": {
                "status": "not-run",
                "accepted_for_operational_use": False,
                "reviewed_artifacts": [],
                "note": "manual qa not run",
                "acceptance_scope": "local diagnostic GIS/QGIS review only",
            },
            "raster_contract": {
                "cloud_optimized": cloud_optimized,
                "csv_ascii_parity_required": True,
                "geopackage_included": False,
                "geotiff_required": True,
                "qgis_project_included": False,
            },
            "probability_claim_boundary": {"annualized": False, "operational": False, "risk": False},
            "limitations": ["Research diagnostic only; not operational."],
            "operational_status": "diagnostic",
            "source_zone_context": {},
        }
        (root / f"{artifact_id}_map_package_manifest.json").write_text(json.dumps(map_manifest, indent=2, sort_keys=True), encoding="utf-8")
        (root / f"{artifact_id}_pilot_gis_package_manifest.json").write_text(json.dumps(pilot_manifest, indent=2, sort_keys=True), encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
