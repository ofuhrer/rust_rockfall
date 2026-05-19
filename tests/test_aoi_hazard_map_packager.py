from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import package_aoi_hazard_map as packager
from scripts import summarize_observed_runout_deposition_intake_contract as observed_intake_helper
from scripts.lib.workflow_validation import build_release_zone_provenance_intake
from scripts.hazard_output_writers import sha256_file
import yaml


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = ROOT / "hazard/results/tschamut_public_pilot/gate_v1"
MAP_MANIFEST = FIXTURE_ROOT / "tschamut_public_conditional_gate_v1_map_package_manifest.json"
PILOT_MANIFEST = FIXTURE_ROOT / "tschamut_public_conditional_gate_v1_pilot_gis_package_manifest.json"


class AoiHazardMapPackagerTests(unittest.TestCase):
    def test_fixture_hazard_outputs_package_into_cog_ready_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "aoi_map_package"

            with patch("scripts.package_aoi_hazard_map.convert_to_cog", side_effect=self.fake_cog_conversion_ready):
                report = packager.package_aoi_hazard_map(FIXTURE_ROOT, output_root, overwrite=True)

            manifest = json.loads((output_root / "aoi_hazard_map_package_manifest.json").read_text(encoding="utf-8"))
            summary = (output_root / "aoi_hazard_map_package_summary.txt").read_text(encoding="utf-8")
            release_overlay = json.loads((output_root / "overlays/release_zone.geojson").read_text(encoding="utf-8"))
            scenario_overlay = json.loads((output_root / "overlays/scenario_table.geojson").read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "map_package_ready")
            self.assertEqual(manifest["package_status"], "map_package_ready")
            self.assertEqual(manifest["layer_inventory_status"], "parity_match")
            self.assertEqual(manifest["claim_boundary"]["operational_status"], "research_diagnostic")
            self.assertFalse(manifest["claim_boundary"]["annualized"])
            self.assertEqual(manifest["review_surface_status"], "review_ready_with_warnings")
            self.assertEqual(manifest["review_surface_paths"]["entrypoint"], str(output_root / "index.html"))
            self.assertEqual(len(manifest["raster_outputs"]), len(report["raster_outputs"]))
            self.assertEqual(len(manifest["layer_inventory"]), len(report["inventory"]))
            self.assertTrue(all(entry["cloud_optimized"] for entry in manifest["raster_outputs"]))
            self.assertEqual(release_overlay["schema_version"], "aoi_release_zone_overlay_v1")
            self.assertEqual(release_overlay["type"], "FeatureCollection")
            self.assertEqual(len(release_overlay["features"]), 1)
            self.assertEqual(release_overlay["features"][0]["geometry"]["type"], "Polygon")
            self.assertEqual(scenario_overlay["schema_version"], "aoi_scenario_overlay_v1")
            self.assertEqual(len(scenario_overlay["features"]), 1)
            self.assertTrue((output_root / "index.html").exists())
            self.assertTrue((output_root / "aoi_map_qa_review_manifest.json").exists())
            review_html = (output_root / "index.html").read_text(encoding="utf-8")
            self.assertIn("Diagnostic hazard layers", review_html)
            self.assertIn("Release and scenario overlays", review_html)
            self.assertIn("Optional observed evidence", review_html)
            self.assertIn("Claim boundaries", review_html)
            self.assertIn("diagnostic review only", review_html)
            self.assertIn("map_package_ready", summary)
            self.assertTrue((output_root / "rasters" / "reach_probability.tif").exists())
            self.assertTrue((output_root / "rasters" / "weighted_reach_probability.tif").exists())
            self.assertEqual(manifest["diagnostic_hazard_outputs"]["status"], "present")
            self.assertEqual(manifest["observed_evidence_overlay_hook"]["hook_status"], "blocked_missing_evidence")
            self.assertEqual(manifest["observed_evidence_overlays"]["status"], "blocked_missing_evidence")
            self.assertEqual(manifest["calibration_inputs"]["status"], "not_included")
            self.assertEqual(manifest["holdout_evidence"]["status"], "not_included")
            self.assertEqual(manifest["deferred_source_frequency_records"]["status"], "deferred")

    def test_observed_evidence_overlay_hook_accepts_real_observed_and_field_supported_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            input_root = FIXTURE_ROOT
            output_root = tmp_path / "package"
            evidence_root = tmp_path / "evidence"
            self.write_real_observed_evidence_package(evidence_root)
            self.write_field_supported_release_zone_provenance(evidence_root)

            with patch("scripts.package_aoi_hazard_map.convert_to_cog", side_effect=self.fake_cog_conversion_ready):
                report = packager.package_aoi_hazard_map(
                    input_root,
                    output_root,
                    overwrite=True,
                    evidence_root=evidence_root,
                )
            manifest = json.loads((output_root / "aoi_hazard_map_package_manifest.json").read_text(encoding="utf-8"))
            observed_overlay = json.loads((output_root / "overlays/observed_runout_deposition.geojson").read_text(encoding="utf-8"))
            release_overlay = json.loads((output_root / "overlays/release_zone_provenance.geojson").read_text(encoding="utf-8"))
            self.assertEqual(report["observed_evidence_overlay_hook"]["hook_status"], "ready")
            self.assertEqual(report["observed_evidence_overlay_hook"]["observed_runout_deposition_overlay_status"], "ready")
            self.assertEqual(report["observed_evidence_overlay_hook"]["release_zone_provenance_overlay_status"], "ready")
            self.assertEqual(len(report["observed_evidence_overlays"]["items"]), 2)
            self.assertEqual(manifest["observed_evidence_overlay_hook"]["hook_status"], "ready")
            self.assertEqual(manifest["observed_evidence_overlays"]["status"], "ready")
            self.assertEqual(manifest["observed_evidence_overlays"]["items"][0]["acceptance_status"], "accepted")
            self.assertEqual(manifest["observed_evidence_overlays"]["items"][1]["acceptance_status"], "accepted")
            self.assertEqual(manifest["observed_evidence_overlays"]["blockers"]["observed_runout_deposition"], [])
            self.assertEqual(manifest["observed_evidence_overlays"]["blockers"]["release_zone_provenance"], [])
            self.assertEqual(manifest["calibration_inputs"]["status"], "not_included")
            self.assertEqual(manifest["holdout_evidence"]["status"], "not_included")
            self.assertEqual(manifest["deferred_source_frequency_records"]["status"], "deferred")
            self.assertEqual(observed_overlay["schema_version"], "aoi_observed_runout_deposition_overlay_v1")
            self.assertEqual(release_overlay["schema_version"], "aoi_release_zone_provenance_overlay_v1")
            self.assertEqual(observed_overlay["features"][0]["properties"]["source_name"], "Chant Sura observed benchmark intake")
            self.assertEqual(release_overlay["features"][0]["properties"]["release_zone_provenance_state"], "field_supported")

    def test_missing_layer_reports_blocked_missing_hazard_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            input_root = tmp_path / "fixture_root"
            input_root.mkdir(parents=True, exist_ok=True)
            self.copy_fixture_manifests(input_root)
            map_manifest_path = input_root / MAP_MANIFEST.name
            map_manifest = json.loads(map_manifest_path.read_text(encoding="utf-8"))
            map_manifest["raster_outputs"][0]["path"] = str(tmp_path / "missing" / "reach_probability.tif")
            map_manifest_path.write_text(json.dumps(map_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

            report = packager.package_aoi_hazard_map(input_root, tmp_path / "package", overwrite=True)

        self.assertEqual(report["status"], "blocked_missing_hazard_outputs")
        self.assertTrue(report["missing_hazard_outputs"])
        self.assertIn("reach_probability.tif", report["missing_hazard_outputs"][0])

    def test_observed_evidence_overlay_hook_blocks_fixture_only_and_ambiguous_roles(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            input_root = FIXTURE_ROOT
            output_root = tmp_path / "package"
            fixture_evidence_root = tmp_path / "fixture_evidence"
            ambiguous_evidence_root = tmp_path / "ambiguous_evidence"
            self.write_fixture_only_observed_evidence_package(fixture_evidence_root)
            self.write_ambiguous_release_zone_provenance(ambiguous_evidence_root)

            with patch("scripts.package_aoi_hazard_map.convert_to_cog", side_effect=self.fake_cog_conversion_ready):
                fixture_report = packager.package_aoi_hazard_map(
                    input_root,
                    output_root,
                    overwrite=True,
                    evidence_root=fixture_evidence_root,
                )
            with patch("scripts.package_aoi_hazard_map.convert_to_cog", side_effect=self.fake_cog_conversion_ready):
                ambiguous_report = packager.package_aoi_hazard_map(
                    input_root,
                    tmp_path / "ambiguous_package",
                    overwrite=True,
                    evidence_root=ambiguous_evidence_root,
                )

        self.assertEqual(fixture_report["observed_evidence_overlay_hook"]["observed_runout_deposition_overlay_status"], "blocked_fixture_only_inputs")
        self.assertEqual(fixture_report["observed_evidence_overlay_hook"]["hook_status"], "blocked_fixture_only_inputs")
        self.assertEqual(fixture_report["observed_evidence_overlays"]["items"], [])
        self.assertEqual(ambiguous_report["observed_evidence_overlay_hook"]["release_zone_provenance_overlay_status"], "blocked_schema_gap")
        self.assertEqual(ambiguous_report["observed_evidence_overlay_hook"]["hook_status"], "blocked_schema_gap")
        self.assertEqual(ambiguous_report["observed_evidence_overlays"]["items"], [])
        self.assertEqual(ambiguous_report["observed_evidence_overlays"]["blockers"]["release_zone_provenance"], [str(ambiguous_evidence_root / "release_zone_provenance.yaml")])

    def test_cog_conversion_failure_reports_cog_blocked_and_falls_back(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "aoi_map_package"

            def fake_failure(input_path: Path, output_path: Path, *, overwrite: bool = False) -> dict[str, object]:
                return {
                    "status": "conversion_failed",
                    "input_path": str(input_path),
                    "output_path": str(output_path),
                    "error": "simulated conversion failure",
                }

            with patch("scripts.package_aoi_hazard_map.convert_to_cog", side_effect=fake_failure):
                report = packager.package_aoi_hazard_map(FIXTURE_ROOT, output_root, overwrite=True)

            manifest = json.loads((output_root / "aoi_hazard_map_package_manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "cog_blocked")
            self.assertTrue(report["cog_blockers"])
            self.assertFalse(all(entry["cloud_optimized"] for entry in manifest["raster_outputs"]))
            self.assertTrue((output_root / "rasters" / "reach_probability.tif").exists())
            self.assertTrue((output_root / "rasters" / "reach_probability.tif").stat().st_size > 0)

    def test_manifest_inventory_matches_written_files_and_checksums(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "aoi_map_package"

            with patch("scripts.package_aoi_hazard_map.convert_to_cog", side_effect=self.fake_cog_conversion_ready):
                report = packager.package_aoi_hazard_map(FIXTURE_ROOT, output_root, overwrite=True)

            manifest = json.loads((output_root / "aoi_hazard_map_package_manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(report["layer_inventory_status"], "parity_match")
            self.assertEqual(len(manifest["layer_inventory"]), len(report["inventory"]))
            self.assertTrue(Path(manifest["review_surface_paths"]["manifest"]).exists())
            self.assertTrue(Path(manifest["review_surface_paths"]["entrypoint"]).exists())
            for entry in manifest["layer_inventory"]:
                path = Path(entry["path"])
                self.assertTrue(path.exists())
                self.assertEqual(entry["sha256"], sha256_file(path))
                self.assertEqual(entry["total_bytes"], path.stat().st_size)
            self.assertEqual(manifest["summary_sha256"], sha256_file(output_root / "aoi_hazard_map_package_summary.txt"))

    def fake_cog_conversion_ready(self, input_path: Path, output_path: Path, *, overwrite: bool = False) -> dict[str, object]:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(f"converted:{input_path.name}".encode("utf-8"))
        return {
            "status": "cog_conversion_sample_ready",
            "input_path": str(input_path),
            "output_path": str(output_path),
            "verification": {
                "status": "ok",
                "sample_raster_tiled": True,
                "sample_raster_overviews": True,
                "sample_raster_cog_layout": True,
            },
            "output_exists": True,
            "output_bytes": output_path.stat().st_size,
            "blockers": [],
        }

    def copy_fixture_manifests(self, root: Path) -> None:
        root.mkdir(parents=True, exist_ok=True)
        (root / MAP_MANIFEST.name).write_text(MAP_MANIFEST.read_text(encoding="utf-8"), encoding="utf-8")
        (root / PILOT_MANIFEST.name).write_text(PILOT_MANIFEST.read_text(encoding="utf-8"), encoding="utf-8")

    def write_real_observed_evidence_package(self, evidence_root: Path) -> None:
        package = observed_intake_helper.load_yaml_fixture(observed_intake_helper.EXPECTED_ACCEPTED_ACQUISITION_FIXTURE)
        package["license"]["status"] = "reviewed"
        package["license"]["note"] = "real benchmark intake"
        package["provenance"]["source_origin_description"] = "Field survey record staged for intake"
        package["provenance"]["provenance_uri"] = "https://example.com/observed-runout-deposition/real-001"
        package["provenance"]["source_name"] = "Chant Sura observed benchmark intake"
        benchmark_root = evidence_root / "observed_runout_deposition_benchmark"
        benchmark_root.mkdir(parents=True, exist_ok=True)
        (benchmark_root / "manifest.json").write_text(
            json.dumps(package, indent=2, sort_keys=True, default=str),
            encoding="utf-8",
        )
        (benchmark_root / "observed_runout_deposition.geojson").write_text(
            json.dumps(
                {
                    "type": "FeatureCollection",
                    "features": [
                        {
                            "type": "Feature",
                            "geometry": {"type": "LineString", "coordinates": [[0.0, 0.0], [1.0, 1.0]]},
                            "properties": {"source_name": "Chant Sura observed benchmark intake"},
                        }
                    ],
                },
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )

    def write_fixture_only_observed_evidence_package(self, evidence_root: Path) -> None:
        package = observed_intake_helper.load_yaml_fixture(observed_intake_helper.EXPECTED_ACCEPTED_ACQUISITION_FIXTURE)
        benchmark_root = evidence_root / "observed_runout_deposition_benchmark"
        benchmark_root.mkdir(parents=True, exist_ok=True)
        (benchmark_root / "manifest.json").write_text(
            json.dumps(package, indent=2, sort_keys=True, default=str),
            encoding="utf-8",
        )
        (benchmark_root / "observed_runout_deposition.geojson").write_text(
            json.dumps(
                {
                    "type": "FeatureCollection",
                    "features": [
                        {
                            "type": "Feature",
                            "geometry": {"type": "LineString", "coordinates": [[0.0, 0.0], [1.0, 1.0]]},
                            "properties": {},
                        }
                    ],
                },
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )

    def write_field_supported_release_zone_provenance(self, evidence_root: Path) -> None:
        record = build_release_zone_provenance_intake(
            {
                "release_zone_provenance_state": "field_supported",
                "review_decision": "accepted",
                "notes": ["field survey record"],
                "source": "field survey record",
            }
        )
        record["source_id"] = "chant_sura_release_zone"
        record["source_origin_description"] = "Field-supported release-zone provenance"
        record["source_reference_frame"] = "LV95"
        record["source_geometry_reference"] = "recorded field polygon"
        record["provenance_uri"] = "https://example.com/release-zone/real-001"
        record["geometry"] = {
            "type": "Polygon",
            "coordinates": [[[0.0, 0.0], [0.0, 1.0], [1.0, 1.0], [0.0, 0.0]]],
        }
        (evidence_root).mkdir(parents=True, exist_ok=True)
        (evidence_root / "release_zone_provenance.yaml").write_text(yaml.safe_dump(record, sort_keys=True), encoding="utf-8")

    def write_ambiguous_release_zone_provenance(self, evidence_root: Path) -> None:
        record = build_release_zone_provenance_intake(
            {
                "release_zone_provenance_state": "mixed_provenance",
                "review_decision": "accepted",
                "notes": ["ambiguous mixed provenance"],
                "source": "mixed provenance fixture",
            }
        )
        record["source_id"] = "ambiguous_release_zone"
        record["source_origin_description"] = "Ambiguous mixed provenance"
        record["source_reference_frame"] = "LV95"
        record["source_geometry_reference"] = "mixed provenance record"
        record["provenance_uri"] = "https://example.com/release-zone/ambiguous-001"
        record["geometry"] = {
            "type": "Polygon",
            "coordinates": [[[0.0, 0.0], [0.0, 2.0], [2.0, 2.0], [0.0, 0.0]]],
        }
        evidence_root.mkdir(parents=True, exist_ok=True)
        (evidence_root / "release_zone_provenance.yaml").write_text(yaml.safe_dump(record, sort_keys=True), encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
