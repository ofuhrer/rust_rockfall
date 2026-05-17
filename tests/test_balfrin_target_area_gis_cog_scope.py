from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts import summarize_balfrin_target_area_gis_cog_scope as scope_audit


class BalfrinTargetAreaGisCogScopeTests(unittest.TestCase):
    def test_full_scope_report_surfaces_parity_and_demo_boundaries(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            standard_root = tmp_path / "target_gate_v1"
            converted_root = tmp_path / "target_gate_v1_cog_export"
            layer_names = ["reach_probability", "max_kinetic_energy"]
            self._write_manifests(standard_root, artifact_id="validation_tschamut_public_target_gate_v1", layer_names=layer_names, cloud_optimized=False)
            self._write_manifests(converted_root, artifact_id="validation_tschamut_public_target_gate_v1", layer_names=layer_names, cloud_optimized=True)

            report = scope_audit.build_report(
                artifact_root=standard_root,
                converted_package_root=converted_root,
                scope_summary=self._scope_summary(),
                raster_metadata_provider=self._fake_cog_metadata,
            )

        self.assertEqual(report["report_status"], "ready")
        self.assertEqual(report["scope_classification"], "full_scope")
        self.assertEqual(report["demo_usability_status"], "usable_for_local_diagnostic_review")
        self.assertEqual(report["gis_cog_readiness_status"], "gis_package_ready_cog_blocked")
        self.assertEqual(report["standard_package_readiness_status"], "gis_package_ready_cog_blocked")
        self.assertEqual(report["converted_package_readiness_status"], "cog_package_ready")
        self.assertEqual(report["layer_parity"]["status"], "parity_match")
        self.assertEqual(report["layer_parity"]["missing_layer_names"], [])
        self.assertEqual(report["layer_parity"]["extra_layer_names"], [])
        self.assertEqual(report["cog_conversion_scope"]["status"], "full_scope")
        self.assertEqual(report["missing_layer_summary"]["status"], "parity_match")
        self.assertIn("full-scope parity", report["demo_usability_summary"])
        self.assertFalse(report["claim_boundaries"]["operational_claims_allowed"])
        self.assertFalse(report["target_area_demo_non_operational_boundaries"]["cog_export_generated"])
        json.dumps(report, sort_keys=True)
        text = scope_audit.render_text_report(report)
        self.assertIn("scope_classification: full_scope", text)
        self.assertIn("missing_layer_names: none", text)
        self.assertIn("demo_usability_status: usable_for_local_diagnostic_review", text)

    def test_blocked_report_surfaces_missing_layers_when_no_converted_package_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            standard_root = tmp_path / "target_gate_v1"
            self._write_manifests(
                standard_root,
                artifact_id="validation_tschamut_public_target_gate_v1",
                layer_names=["reach_probability", "max_kinetic_energy"],
                cloud_optimized=False,
            )

            report = scope_audit.build_report(
                artifact_root=standard_root,
                converted_package_root=None,
                scope_summary=self._scope_summary(),
                raster_metadata_provider=self._fake_cog_metadata,
            )

        self.assertEqual(report["report_status"], "blocked_missing_inputs")
        self.assertEqual(report["scope_classification"], "blocked_missing_products")
        self.assertEqual(report["demo_usability_status"], "blocked_missing_products")
        self.assertEqual(report["layer_parity"]["status"], "blocked_missing_products")
        self.assertEqual(report["missing_layer_summary"]["status"], "blocked_missing_products")
        self.assertEqual(
            report["cog_conversion_scope"]["omitted_layer_names"],
            ["reach_probability", "max_kinetic_energy"],
        )
        self.assertIn("converted COG package is missing or incomplete", report["demo_usability_summary"])

    def _scope_summary(self) -> dict[str, object]:
        return {
            "schema_version": "balfrin_target_area_demo_gis_scope_summary_v1",
            "status": "template_only",
            "summary": "The frozen target-area case skeleton records planned GIS inputs separately from downstream template-only outputs and does not imply any hazard layers were generated.",
            "no_hazard_layers_generated": True,
            "cog_export_expectation": {
                "status": "template_only",
                "generated_now": False,
                "hazard_layers_generated": False,
                "cog_export_generated": False,
            },
            "non_operational_gis_boundaries": {
                "operational_claims_allowed": False,
                "hazard_layers_generated": False,
                "cog_export_generated": False,
                "scale_up_authorized": False,
                "distributed_execution_authorized": False,
                "annual_frequency_claims_allowed": False,
                "physical_probability_claims_allowed": False,
                "risk_exposure_vulnerability_claims_allowed": False,
            },
            "claim_boundary": {
                "operational_claims_allowed": False,
                "annual_frequency_claims_allowed": False,
                "physical_probability_claims_allowed": False,
                "risk_exposure_vulnerability_claims_allowed": False,
                "scale_up_authorized": False,
                "distributed_execution_authorized": False,
            },
            "planned_raster_products": [
                {"product_kind": "raster", "product": "target hazard layers and conditional curves"},
            ],
            "planned_vector_products": [
                {"product_kind": "vector", "product": "target-area boundary and extent summary"},
                {"product_kind": "vector", "product": "target pilot GIS package"},
            ],
            "template_only_products": [
                {"product_kind": "metadata", "product": "ignored target-area handoff bundle"},
            ],
        }

    def _write_manifests(
        self,
        root: Path,
        *,
        artifact_id: str,
        layer_names: list[str],
        cloud_optimized: bool,
    ) -> None:
        root.mkdir(parents=True, exist_ok=True)
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
            "layer_semantics": [
                {
                    "layer_name": layer_name,
                    "units": "dimensionless",
                    "numerator": f"{layer_name} numerator",
                    "denominator": "trajectory count conditioned on source/scenario metadata",
                    "is_annualized": False,
                    "weighted": layer_name.startswith("weighted_"),
                }
                for layer_name in layer_names
            ],
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
            "terrain_metadata": {
                "file_count": 1,
                "format": "yaml",
                "kind": "terrain_metadata",
                "path": str(root.parent / "input" / "terrain_metadata.yaml"),
                "sha256": "abc",
                "total_bytes": 1,
            },
            "hazard_manifest_paths": [str(root / f"{artifact_id}_manifest.json")],
            "raster_outputs": raster_outputs,
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
        (root / f"{artifact_id}_map_package_manifest.json").write_text(
            json.dumps(map_manifest, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        (root / f"{artifact_id}_pilot_gis_package_manifest.json").write_text(
            json.dumps(pilot_manifest, indent=2, sort_keys=True),
            encoding="utf-8",
        )

    def _fake_cog_metadata(self, path: Path) -> dict[str, object]:
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
