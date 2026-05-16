from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts import audit_gis_cog_package_readiness as audit


ROOT = Path(__file__).resolve().parents[1]
GATE_MAP_MANIFEST = ROOT / "hazard/results/tschamut_public_pilot/gate_v1/tschamut_public_conditional_gate_v1_map_package_manifest.json"


class GisCogPackageReadinessTest(unittest.TestCase):
    def test_ready_report_surfaces_required_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "gate_v1"
            self._write_manifests(root, artifact_id="validation_tschamut_public_conditional_gate_v1")
            report = audit.build_gis_cog_readiness_report(
                artifact_roots=[root],
                raster_metadata_provider=self._fake_cog_metadata,
            )

        self.assertEqual(report["gis_cog_readiness_status"], "gis_package_ready")
        self.assertEqual(report["readiness_status"], "gis_package_ready")
        self.assertEqual(report["artifacts_audited"], 1)
        self.assertEqual(report["qgis_manual_qa_status"], "not_run")
        self.assertEqual(report["scientific_acceptance_status"], "inconclusive")
        self.assertFalse(report["scale_up_authorized"])
        self.assertFalse(report["operational_claims_allowed"])
        self.assertEqual(report["converted_sample_status"], "not_provided")

        artifact = report["artifacts"][0]
        self.assertEqual(artifact["raster_layer_count"], 2)
        self.assertEqual(artifact["crs_or_epsg"]["terrain_epsg"], 2056)
        self.assertEqual(artifact["grid_dimensions"], {"ncols": 300, "nrows": 304})
        self.assertEqual(artifact["transform_or_cell_size"]["cell_size_m"], 2.0)
        self.assertEqual(artifact["nodata_values"]["terrain_nodata"], -9999.0)
        self.assertTrue(artifact["geotiff_presence"]["all_declared_geotiffs_present"])
        self.assertEqual(artifact["cog_readiness_indicators"]["sample_raster_block_size"], [256, 256])
        self.assertTrue(artifact["cog_readiness_indicators"]["sample_raster_overviews"])
        self.assertTrue(artifact["cog_readiness_indicators"]["sample_raster_cog_layout"])
        self.assertEqual(artifact["manifest_completeness"]["map_package_manifest_missing_fields"], [])
        self.assertEqual(artifact["manifest_completeness"]["pilot_gis_package_manifest_missing_fields"], [])
        self.assertEqual(artifact["blockers"], [])

        json.dumps(report, sort_keys=True)
        text = audit.render_text_report(report)
        self.assertIn("GIS/COG readiness: gis_package_ready", text)
        self.assertIn("validation_tschamut_public_conditional_gate_v1", text)

    def test_missing_manifest_returns_blocked_missing_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "target_gate_v1"
            root.mkdir(parents=True, exist_ok=True)
            self._write_map_manifest_only(root, artifact_id="validation_tschamut_public_target_gate_v1")
            report = audit.build_gis_cog_readiness_report(
                artifact_roots=[root],
                raster_metadata_provider=self._fake_cog_metadata,
            )

        self.assertEqual(report["gis_cog_readiness_status"], "blocked_missing_inputs")
        self.assertEqual(report["readiness_status"], "blocked_missing_inputs")
        artifact = report["artifacts"][0]
        self.assertFalse(artifact["manifest_completeness"]["pilot_gis_package_manifest_complete"])
        self.assertTrue(artifact["manifest_completeness"]["pilot_gis_package_manifest_missing_fields"])
        self.assertTrue(any("pilot_gis_package_manifest_missing_fields" in blocker for blocker in artifact["blockers"]))

    def test_metadata_only_when_gdal_metadata_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "probe_v1"
            self._write_manifests(root, artifact_id="validation_tschamut_public_sampling_sensitivity_v1_full")
            report = audit.build_gis_cog_readiness_report(
                artifact_roots=[root],
                raster_metadata_provider=lambda path: None,
            )

        self.assertEqual(report["gis_cog_readiness_status"], "metadata_only")
        self.assertEqual(report["readiness_status"], "metadata_only")
        artifact = report["artifacts"][0]
        self.assertFalse(artifact["cog_readiness_indicators"]["gdalinfo_available"])

    def test_converted_sample_can_be_recognized_as_cog_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "gate_v1"
            self._write_manifests(root, artifact_id="validation_tschamut_public_conditional_gate_v1")
            sample_path = Path(tmp) / "tschamut_cog_sample.tif"
            sample_path.write_text("placeholder", encoding="utf-8")
            report = audit.build_gis_cog_readiness_report(
                artifact_roots=[root],
                converted_sample_path=sample_path,
                raster_metadata_provider=self._fake_cog_metadata,
            )

        self.assertEqual(report["gis_cog_readiness_status"], "gis_package_ready")
        self.assertEqual(report["converted_sample_status"], "cog_conversion_sample_ready")
        self.assertEqual(report["converted_sample"]["status"], "cog_conversion_sample_ready")
        self.assertTrue(report["converted_sample"]["metadata"]["sample_raster_cog_layout"])

    def test_converted_package_readiness_summary_surfaces_ready_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            standard_root = Path(tmp) / "gate_v1"
            converted_root = Path(tmp) / "gate_v1_cog_export"
            self._write_manifests(standard_root, artifact_id="validation_tschamut_public_conditional_gate_v1")
            self._write_manifests(converted_root, artifact_id="validation_tschamut_public_conditional_gate_v1")
            report = audit.build_gis_cog_readiness_report(
                artifact_roots=[standard_root],
                converted_package_roots=[converted_root],
                raster_metadata_provider=self._fake_cog_metadata,
            )

        self.assertEqual(report["gis_cog_readiness_status"], "gis_package_ready")
        self.assertEqual(report["converted_package_readiness_status"], "converted_package_ready")
        self.assertEqual(report["converted_package_layer_inventory_status"], "parity_match")
        self.assertTrue(report["any_converted_package_ready"])
        self.assertEqual(report["converted_package_status"]["validation_tschamut_public_conditional_gate_v1"], "cog_package_ready")
        self.assertIn("Converted package readiness: converted_package_ready", audit.render_text_report(report))

    def test_converted_gate_v1_cog_export_reports_intentional_scope_reduction(self) -> None:
        source_manifest = json.loads(GATE_MAP_MANIFEST.read_text(encoding="utf-8"))
        standard_layer_names = [entry["layer_name"] for entry in source_manifest["raster_outputs"]]
        reduced_layer_names = [
            layer_name
            for layer_name in standard_layer_names
            if layer_name not in {"jump_height_exceedance_0p5m", "weighted_jump_height_exceedance_0p5m"}
        ]

        with tempfile.TemporaryDirectory() as tmp:
            standard_root = Path(tmp) / "gate_v1"
            converted_root = Path(tmp) / "gate_v1_cog_export"
            self._write_manifests(
                standard_root,
                artifact_id="validation_tschamut_public_conditional_gate_v1",
                layer_names=standard_layer_names,
                layer_semantics=source_manifest["layer_semantics"],
            )
            self._write_manifests(
                converted_root,
                artifact_id="validation_tschamut_public_conditional_gate_v1",
                layer_names=reduced_layer_names,
                layer_semantics=[
                    entry for entry in source_manifest["layer_semantics"] if entry["layer_name"] in reduced_layer_names
                ],
            )
            report = audit.build_gis_cog_readiness_report(
                artifact_roots=[standard_root],
                converted_package_roots=[converted_root],
                raster_metadata_provider=self._fake_cog_metadata,
            )

        converted_package = report["converted_packages"][0]
        self.assertEqual(report["converted_package_layer_inventory_status"], "scope_reduced")
        self.assertEqual(converted_package["layer_inventory_status"], "scope_reduced")
        self.assertEqual(converted_package["standard_layer_count"], 22)
        self.assertEqual(converted_package["converted_layer_count"], 20)
        self.assertEqual(
            converted_package["missing_layer_names"],
            ["jump_height_exceedance_0p5m", "weighted_jump_height_exceedance_0p5m"],
        )
        self.assertEqual(
            [entry["layer_name"] for entry in converted_package["missing_layer_semantics"]],
            ["jump_height_exceedance_0p5m", "weighted_jump_height_exceedance_0p5m"],
        )
        text = audit.render_text_report(report)
        self.assertIn("Converted package layer inventory: scope_reduced", text)
        self.assertIn("omitted layers: jump_height_exceedance_0p5m, weighted_jump_height_exceedance_0p5m", text)

    def _write_manifests(
        self,
        root: Path,
        *,
        artifact_id: str,
        layer_names: list[str] | None = None,
        layer_semantics: list[dict[str, object]] | None = None,
        cloud_optimized: bool = True,
    ) -> None:
        root.mkdir(parents=True, exist_ok=True)
        layer_names = layer_names or ["reach_probability", "max_kinetic_energy"]
        layer_semantics = layer_semantics or [
            {
                "layer_name": layer_name,
                "units": "dimensionless",
                "numerator": f"{layer_name} numerator",
                "denominator": "trajectory count conditioned on source/scenario metadata",
                "is_annualized": False,
                "weighted": layer_name.startswith("weighted_"),
            }
            for layer_name in layer_names
        ]
        raster_outputs = []
        for layer_name in layer_names:
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
                    "total_bytes": 1,
                }
            )
        map_manifest = {
            "schema_version": "map_package_manifest_v1",
            "map_product_id": artifact_id,
            "map_product_version": "v1",
            "probability_mode": "sampling_weighted_conditional",
            "normalization_scope": "conditioned_on_filter",
            "source_zone_id": "source_zone_a",
            "source_zone_metadata_path": str(root.parent / "input" / "source_zone_metadata.yaml"),
            "scenario_table_path": str(root.parent / "input" / "scenario_table.csv"),
            "hazard_manifest_paths": [str(root / f"{artifact_id}_manifest.json")],
            "raster_outputs": raster_outputs,
            "layer_semantics": layer_semantics,
            "limitations": ["Research diagnostic only; not operational."],
            "operational_status": "diagnostic",
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
                "metadata_path": str(root.parent / "input" / "terrain_metadata.yaml"),
                "nodata": -9999.0,
                "path": str(root.parent / "input" / "terrain.asc"),
                "processed_sha256": "abc",
                "resolution_m": 2.0,
                "source_dataset": "swisstopo_swissalti3d",
                "source_filename": "source.tif",
                "source_product": "swissALTI3D 2 m COG",
                "terrain_type": "ascii_dem_clamped",
                "vertical_datum": "LN02",
            },
            "terrain_metadata": {"file_count": 1, "format": "yaml", "kind": "terrain_metadata", "path": str(root.parent / "input" / "terrain_metadata.yaml"), "sha256": "abc", "total_bytes": 1},
            "hazard_manifest_paths": [str(root / f"{artifact_id}_manifest.json")],
            "raster_outputs": map_manifest["raster_outputs"],
            "manifest_outputs": [],
            "parity_outputs": [],
            "conditional_intensity_exceedance_curve_outputs": [],
            "visual_qa": {"status": "not-run", "accepted_for_operational_use": False, "reviewed_artifacts": [], "note": "manual qa not run", "acceptance_scope": "local diagnostic GIS/QGIS review only"},
            "raster_contract": {"cloud_optimized": cloud_optimized, "csv_ascii_parity_required": True, "geopackage_included": False, "geotiff_required": True, "qgis_project_included": False},
            "probability_claim_boundary": {"annualized": False, "operational": False, "risk": False},
            "limitations": ["Research diagnostic only; not operational."],
            "operational_status": "diagnostic",
            "source_zone_context": {},
        }
        (root / f"{artifact_id}_map_package_manifest.json").write_text(json.dumps(map_manifest, indent=2, sort_keys=True), encoding="utf-8")
        (root / f"{artifact_id}_pilot_gis_package_manifest.json").write_text(json.dumps(pilot_manifest, indent=2, sort_keys=True), encoding="utf-8")

    def _write_map_manifest_only(self, root: Path, *, artifact_id: str) -> None:
        root.mkdir(parents=True, exist_ok=True)
        raster_path = root / f"{artifact_id}_reach_probability.tif"
        raster_path.write_bytes(b"not a real tif, only a tiny fixture placeholder")
        second_raster_path = root / f"{artifact_id}_max_kinetic_energy.tif"
        second_raster_path.write_bytes(b"not a real tif, only a tiny fixture placeholder")
        map_manifest = {
            "schema_version": "map_package_manifest_v1",
            "map_product_id": artifact_id,
            "map_product_version": "v1",
            "probability_mode": "sampling_weighted_conditional",
            "normalization_scope": "conditioned_on_filter",
            "source_zone_id": "source_zone_a",
            "source_zone_metadata_path": str(root.parent / "input" / "source_zone_metadata.yaml"),
            "scenario_table_path": str(root.parent / "input" / "scenario_table.csv"),
            "hazard_manifest_paths": [str(root / f"{artifact_id}_manifest.json")],
            "raster_outputs": [
                {
                    "layer_name": "reach_probability",
                    "path": str(raster_path),
                    "format": "geotiff",
                    "cloud_optimized": False,
                    "annualized": False,
                    "is_annualized": False,
                    "sha256": "abc",
                    "total_bytes": 1,
                }
                ,
                {
                    "layer_name": "max_kinetic_energy",
                    "path": str(second_raster_path),
                    "format": "geotiff",
                    "cloud_optimized": False,
                    "annualized": False,
                    "is_annualized": False,
                    "sha256": "def",
                    "total_bytes": 1,
                }
            ],
            "layer_semantics": [],
            "limitations": ["Research diagnostic only; not operational."],
            "operational_status": "diagnostic",
        }
        (root / f"{artifact_id}_map_package_manifest.json").write_text(json.dumps(map_manifest, indent=2, sort_keys=True), encoding="utf-8")

    def _fake_cog_metadata(self, path: Path):
        return {
            "status": "ok",
            "driver": "GTiff",
            "size": [300, 304],
            "epsg": 2056,
            "geo_transform": [2696376.0, 2.0, 0.0, 1167992.0, 0.0, -2.0],
            "block_size": [256, 256],
            "nodata": -9999.0,
            "overview_count": 2,
            "image_structure": {"INTERLEAVE": "BAND", "LAYOUT": "COG", "COMPRESSION": "ZSTD"},
        }


if __name__ == "__main__":
    unittest.main()
