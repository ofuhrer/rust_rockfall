from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "validate_pilot_gis_package.py"
SPEC = importlib.util.spec_from_file_location("validate_pilot_gis_package", SCRIPT_PATH)
assert SPEC is not None
validator = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(validator)


class PilotGisPackageValidatorTests(unittest.TestCase):
    def test_accepts_real_site_package_contract_with_existing_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            paths = self.write_artifacts(work)
            manifest_path = self.write_manifest(work, paths)

            summary = validator.validate_package(
                manifest_path,
                require_real_site=True,
                require_existing_files=True,
            )

            self.assertEqual(summary["geotiff_count"], 1)
            self.assertEqual(summary["csv_parity_count"], 1)
            self.assertEqual(summary["ascii_parity_count"], 1)
            self.assertEqual(summary["terrain_epsg"], 2056)
            self.assertEqual(summary["terrain_vertical_datum"], "LN02")
            self.assertEqual(summary["source_context_status"], "map_package_source_zone_metadata")

    def test_rejects_missing_ascii_parity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            paths = self.write_artifacts(work)
            manifest_path = self.write_manifest(work, paths)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["parity_outputs"] = [
                output for output in manifest["parity_outputs"] if output["format"] != "esri_ascii_grid"
            ]
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            with self.assertRaisesRegex(validator.PackageValidationError, "missing ESRI ASCII"):
                validator.validate_package(manifest_path)

    def test_rejects_annualized_geotiff_claim(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            paths = self.write_artifacts(work)
            manifest_path = self.write_manifest(work, paths)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["raster_outputs"][0]["annualized"] = True
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            with self.assertRaisesRegex(validator.PackageValidationError, "must not be annualized"):
                validator.validate_package(manifest_path)

    def test_rejects_missing_unsupported_claim_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            paths = self.write_artifacts(work)
            manifest_path = self.write_manifest(work, paths)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["probability_claim_boundary"]["future_unsupported_product_labels"].remove("risk_map")
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            with self.assertRaisesRegex(validator.PackageValidationError, "risk_map"):
                validator.validate_package(manifest_path)

    def test_rejects_bad_checksum_when_existing_files_required(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            paths = self.write_artifacts(work)
            manifest_path = self.write_manifest(work, paths)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["raster_outputs"][0]["sha256"] = "0" * 64
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            with self.assertRaisesRegex(validator.PackageValidationError, "sha256 does not match"):
                validator.validate_package(manifest_path, require_existing_files=True)

    def write_artifacts(self, work: Path) -> dict[str, Path]:
        paths = {
            "tif": work / "gate_reach_probability.tif",
            "csv": work / "gate_reach_probability.csv",
            "asc": work / "gate_reach_probability.asc",
            "metadata": work / "gate_metadata.json",
            "hazard": work / "gate_manifest.json",
            "map": work / "gate_map_package_manifest.json",
        }
        paths["tif"].write_bytes(b"tiny-geotiff-placeholder")
        paths["csv"].write_text("row,col,value\n0,0,1.0\n", encoding="utf-8")
        paths["asc"].write_text(
            "\n".join(
                [
                    "ncols 2",
                    "nrows 2",
                    "xllcorner 2600000.0",
                    "yllcorner 1200000.0",
                    "cellsize 2.0",
                    "NODATA_value -9999.0",
                    "1 0",
                    "0 0",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        paths["metadata"].write_text("{}", encoding="utf-8")
        paths["map"].write_text(
            json.dumps(
                {
                    "schema_version": "map_package_manifest_v1",
                    "map_product_id": "gate_map",
                    "probability_mode": "sampling_weighted_conditional",
                    "normalization_scope": "conditioned_on_filter",
                    "source_zone_id": "source_zone_a",
                    "source_zone_metadata_path": str(work / "source_zone.yaml"),
                    "operational_status": "research_diagnostic",
                }
            ),
            encoding="utf-8",
        )
        paths["hazard"].write_text(json.dumps(self.hazard_manifest(paths)), encoding="utf-8")
        return paths

    def write_manifest(self, work: Path, paths: dict[str, Path]) -> Path:
        manifest = {
            "schema_version": "pilot_gis_package_manifest_v1",
            "case_id": "gate_case",
            "package_version": "pilot_gis_package_v1",
            "operational_status": "research_diagnostic",
            "grid": {
                "source": "explicit",
                "xmin_m": 2600000.0,
                "ymin_m": 1200000.0,
                "ncols": 2,
                "nrows": 2,
                "cell_size_m": 2.0,
            },
            "hazard_manifest_paths": [str(paths["hazard"])],
            "raster_contract": {
                "geotiff_required": True,
                "csv_ascii_parity_required": True,
                "cloud_optimized": False,
                "qgis_project_included": False,
                "geopackage_included": False,
            },
            "raster_outputs": [self.artifact(paths["tif"], "geotiff", layer_name="reach_probability")],
            "parity_outputs": [
                self.artifact(paths["csv"], "csv_grid"),
                self.artifact(paths["asc"], "esri_ascii_grid"),
            ],
            "manifest_outputs": [
                self.artifact(paths["metadata"], "json", kind="hazard_metadata"),
                self.artifact(paths["map"], "json", kind="map_package_manifest"),
            ],
            "source_zone_context": [],
            "terrain": {
                "terrain_type": "ascii_dem_clamped",
                "path": str(work / "terrain.asc"),
                "metadata_path": str(work / "terrain_metadata.yaml"),
                "crs": "CH1903+ / LV95",
                "epsg": 2056,
                "vertical_datum": "LN02",
                "resolution_m": 2.0,
                "nodata": -9999.0,
                "extent": {
                    "xmin": 2600000.0,
                    "xmax": 2600004.0,
                    "ymin": 1200000.0,
                    "ymax": 1200004.0,
                },
                "source_dataset": "swisstopo_swissalti3d",
            },
            "terrain_metadata": self.artifact(paths["metadata"], "yaml", kind="terrain_metadata"),
            "visual_qa": {
                "status": "inconclusive",
                "note": "Automated package check only; no manual QGIS inspection.",
                "reviewed_artifacts": [],
                "acceptance_scope": "local diagnostic GIS/QGIS review only",
                "accepted_for_operational_use": False,
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
        }
        manifest_path = work / "pilot_gis_package_manifest.json"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        return manifest_path

    def artifact(
        self,
        path: Path,
        format_name: str,
        *,
        kind: str = "hazard_layer",
        layer_name: str | None = None,
    ) -> dict:
        data = path.read_bytes()
        entry = {
            "path": str(path),
            "format": format_name,
            "kind": kind,
            "sha256": hashlib.sha256(data).hexdigest(),
            "total_bytes": len(data),
        }
        if layer_name is not None:
            entry.update(
                {
                    "layer_name": layer_name,
                    "annualized": False,
                    "is_annualized": False,
                    "cloud_optimized": False,
                }
            )
        return entry

    def hazard_manifest(self, paths: dict[str, Path]) -> dict:
        geotiff = copy.deepcopy(self.artifact(paths["tif"], "geotiff", layer_name="reach_probability"))
        geotiff.update(
            {
                "cloud_optimized": False,
                "cog": False,
                "compression": "none",
                "raster": {
                    "affine_transform": [2.0, 0.0, 2600000.0, 0.0, -2.0, 1200004.0],
                    "cell_size_m": 2.0,
                    "cloud_optimized": False,
                    "cog": False,
                    "compression": "none",
                    "crs": "CH1903+ / LV95",
                    "epsg": 2056,
                    "extent": {
                        "xmin_m": 2600000.0,
                        "xmax_m": 2600004.0,
                        "ymin_m": 1200000.0,
                        "ymax_m": 1200004.0,
                    },
                    "ncols": 2,
                    "nrows": 2,
                    "nodata": -9999.0,
                    "vertical_datum": "LN02",
                },
            }
        )
        return {"schema_version": "run_manifest_v1", "outputs": [geotiff]}


if __name__ == "__main__":
    unittest.main()
