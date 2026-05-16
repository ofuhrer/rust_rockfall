from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "measure_hazard_context_overlap.py"
SPEC = importlib.util.spec_from_file_location("measure_hazard_context_overlap", SCRIPT_PATH)
assert SPEC is not None
overlap = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = overlap
SPEC.loader.exec_module(overlap)


class HazardContextOverlapTests(unittest.TestCase):
    def test_missing_hazard_manifest_returns_blocked_report(self) -> None:
        report = overlap.build_summary(hazard_manifest_path=Path("/tmp/missing-hazard-manifest.json"))

        self.assertEqual(report["hazard_context_overlap_status"], "blocked_missing_inputs")
        self.assertEqual(report["final_classification"], "blocked_missing_inputs")
        self.assertIn("hazard manifest is absent", report["blocked_reason"])
        self.assertEqual(report["selected_hazard_layers"], [])
        self.assertFalse(report["scale_up_authorized"])
        self.assertFalse(report["operational_claims_allowed"])

    def test_missing_archive_returns_blocked_report(self) -> None:
        # Clean-checkout unit coverage: this test synthesizes a tiny manifest and
        # explicitly models the absent staged archive instead of requiring ignored
        # local artifact roots.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            hazard_manifest = root / "manifest.json"
            hazard_manifest.write_text(
                json.dumps(
                    {
                        "schema_version": "run_manifest_v1",
                        "cellwise_layers": [
                            {
                                "layer_name": "reach_probability",
                                "grid_path": str(root / "reach_probability.asc"),
                                "format": "esri_ascii_grid",
                                "thresholds": [],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            (root / "reach_probability.asc").write_text(
                "\n".join(
                    [
                        "ncols 2",
                        "nrows 2",
                        "xllcorner 0",
                        "yllcorner 0",
                        "cellsize 10",
                        "NODATA_value -9999",
                        "0 1",
                        "0 2",
                    ]
                ),
                encoding="utf-8",
            )

            context_metadata = root / "context_metadata.json"
            context_metadata.write_text(
                json.dumps(
                    {
                        "pilot_id": "tschamut_public_pilot",
                        "review_classification": "limiting",
                        "staged_asset_present": False,
                        "local_asset_path": str(root / "missing.zip"),
                        "raw_asset_path": str(root / "missing.zip"),
                        "local_asset_sha256": "abc123",
                        "coordinate_reference_system": {"epsg": 2056},
                    }
                ),
                encoding="utf-8",
            )

            report = overlap.build_summary(
                hazard_manifest_path=hazard_manifest,
                context_metadata_path=context_metadata,
                scope_record_path=ROOT / "validation/pilot_runs/tschamut_public_obstacle_scope_v1.yaml",
                hazard_layers=["reach_probability"],
                top_cell_count=1,
            )

        self.assertEqual(report["hazard_context_overlap_status"], "blocked_missing_inputs")
        self.assertEqual(report["context_archive_status"], "blocked_missing_inputs")
        self.assertIn("staged swissTLM3D archive is absent", report["blocked_reason"])
        self.assertEqual(report["selected_hazard_layers"], [])
        self.assertEqual(report["selected_cell_total"], 0)

    def test_measured_overlap_reports_per_category_counts_and_conservative_classification(self) -> None:
        # Clean-checkout unit coverage: the overlap path is exercised with a fake
        # archive and mocked GDAL query results so the regression suite does not
        # depend on local Tschamut artifacts or binaries.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / "swisstlm3d.zip"
            archive.write_bytes(b"fake archive")
            context_metadata = root / "context_metadata.json"
            context_metadata.write_text(
                json.dumps(
                    {
                        "pilot_id": "tschamut_public_pilot",
                        "review_classification": "limiting",
                        "staged_asset_present": True,
                        "local_asset_path": str(archive),
                        "raw_asset_path": str(archive),
                        "local_asset_sha256": "abc123",
                        "local_asset_bytes": archive.stat().st_size,
                        "coordinate_reference_system": {
                            "epsg": 2056,
                            "horizontal_name": "CH1903+ / LV95",
                            "vertical_datum": "LN02",
                        },
                    }
                ),
                encoding="utf-8",
            )

            grids = {
                "reach_probability": [
                    "ncols 2",
                    "nrows 2",
                    "xllcorner 0",
                    "yllcorner 0",
                    "cellsize 10",
                    "NODATA_value -9999",
                    "1 3",
                    "0 2",
                ],
                "max_kinetic_energy": [
                    "ncols 2",
                    "nrows 2",
                    "xllcorner 0",
                    "yllcorner 0",
                    "cellsize 10",
                    "NODATA_value -9999",
                    "0 4",
                    "5 1",
                ],
                "max_jump_height": [
                    "ncols 2",
                    "nrows 2",
                    "xllcorner 0",
                    "yllcorner 0",
                    "cellsize 10",
                    "NODATA_value -9999",
                    "0 2",
                    "0 7",
                ],
            }
            cellwise_layers: list[dict[str, object]] = []
            for layer_name, lines in grids.items():
                grid_path = root / f"{layer_name}.asc"
                grid_path.write_text("\n".join(lines), encoding="utf-8")
                cellwise_layers.append(
                    {
                        "layer_name": layer_name,
                        "grid_path": str(grid_path),
                        "format": "esri_ascii_grid",
                        "thresholds": [],
                    }
                )

            hazard_manifest = root / "manifest.json"
            hazard_manifest.write_text(
                json.dumps(
                    {
                        "schema_version": "run_manifest_v1",
                        "cellwise_layers": cellwise_layers,
                    }
                ),
                encoding="utf-8",
            )

            feature_boxes = {
                "swissTLM3D_TLM_STRASSE": (12.0, 12.0, 18.0, 18.0),
                "swissTLM3D_TLM_STRASSENINFO": None,
                "swissTLM3D_TLM_MAUER": (2.0, 2.0, 8.0, 8.0),
                "swissTLM3D_TLM_VERBAUUNG": None,
                "swissTLM3D_TLM_STAUBAUTE": None,
                "swissTLM3D_TLM_FLIESSGEWAESSER": (12.0, 2.0, 18.0, 8.0),
                "swissTLM3D_TLM_STEHENDES_GEWAESSER": None,
                "swissTLM3D_TLM_GEBAEUDE_FOOTPRINT": None,
                "swissTLM3D_TLM_VERKEHRSBAUTE_LIN": None,
                "swissTLM3D_TLM_VERKEHRSBAUTE_PLY": None,
                "swissTLM3D_TLM_VERSORGUNGS_BAUTE_LIN": None,
                "swissTLM3D_TLM_VERSORGUNGS_BAUTE_PKT": None,
            }

            def fake_query_feature_count(*, archive_path, layer_name, bbox, member_path=None):
                bounds = feature_boxes[layer_name]
                if bounds is None:
                    return 0
                xmin, ymin, xmax, ymax = bounds
                if bbox["xmax"] < xmin or bbox["xmin"] > xmax or bbox["ymax"] < ymin or bbox["ymin"] > ymax:
                    return 0
                return 1

            with mock.patch.object(overlap.shutil, "which", return_value="/opt/homebrew/bin/ogrinfo"), mock.patch.object(
                overlap, "query_feature_count", side_effect=fake_query_feature_count
            ):
                report = overlap.build_summary(
                    hazard_manifest_path=hazard_manifest,
                    context_metadata_path=context_metadata,
                    scope_record_path=ROOT / "validation/pilot_runs/tschamut_public_obstacle_scope_v1.yaml",
                    hazard_layers=["reach_probability", "max_kinetic_energy", "max_jump_height"],
                    top_cell_count=1,
                    buffer_radii_m=[0.0, 10.0, 20.0],
                )

        self.assertEqual(report["hazard_context_overlap_status"], "measured")
        self.assertEqual(report["context_archive_status"], "measured_corridor_relevance")
        self.assertEqual(report["context_classification"], "limiting")
        self.assertEqual(report["final_classification"], "limiting")
        self.assertEqual(report["target_convergence_interpretation"], "inconclusive")
        self.assertEqual(report["validation_output_context"], "summary_only")
        self.assertFalse(report["scale_up_authorized"])
        self.assertFalse(report["operational_claims_allowed"])
        self.assertEqual([item["layer_name"] for item in report["selected_hazard_layers"]], [
            "reach_probability",
            "max_kinetic_energy",
            "max_jump_height",
        ])
        self.assertEqual(report["roads_or_transport_overlap"]["classification"], "limiting")
        self.assertEqual(report["barriers_or_protection_overlap"]["classification"], "limiting")
        self.assertEqual(report["water_or_channel_overlap"]["classification"], "limiting")
        self.assertGreater(report["roads_or_transport_overlap"]["within_20m_cell_count_total"], 0)
        self.assertGreater(report["barriers_or_protection_overlap"]["within_20m_cell_count_total"], 0)
        self.assertGreater(report["water_or_channel_overlap"]["within_20m_cell_count_total"], 0)
        self.assertEqual(report["nearest_distances_m"]["reach_probability"]["roads_or_transport"], 0.0)
        self.assertEqual(report["nearest_distances_m"]["max_kinetic_energy"]["barriers_or_protection"], 0.0)
        self.assertEqual(report["nearest_distances_m"]["max_jump_height"]["water_or_channel"], 0.0)
        self.assertIn("roads_or_transport: limiting", report["interpretation_impact"]["category_summary"])
        self.assertIn("No obstacle physics are implemented here.", overlap.render_markdown(report))

        self.assertEqual(
            set(report.keys()),
            {
                "blocked_reason",
                "barriers_or_protection_overlap",
                "context_archive_status",
                "context_categories_queried",
                "context_classification",
                "context_metadata_path",
                "final_classification",
                "hazard_context_overlap_status",
                "hazard_manifest_path",
                "hazard_mask_criteria",
                "interpretation_impact",
                "nearest_distances_m",
                "operational_claims_allowed",
                "overlap_cell_counts",
                "overlap_cell_fractions",
                "pilot_id",
                "report_schema_version",
                "roads_or_transport_overlap",
                "scale_up_authorized",
                "selected_cell_total",
                "selected_extent_or_corridor",
                "selected_hazard_layers",
                "status",
                "target_convergence_interpretation",
                "validation_output_context",
                "water_or_channel_overlap",
            },
        )

    def test_zero_overlap_is_not_treated_as_obstacle_absence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / "swisstlm3d.zip"
            archive.write_bytes(b"fake archive")
            context_metadata = root / "context_metadata.json"
            context_metadata.write_text(
                json.dumps(
                    {
                        "pilot_id": "tschamut_public_pilot",
                        "review_classification": "limiting",
                        "staged_asset_present": True,
                        "local_asset_path": str(archive),
                        "raw_asset_path": str(archive),
                    }
                ),
                encoding="utf-8",
            )
            grid_path = root / "reach_probability.asc"
            grid_path.write_text(
                "\n".join(
                    [
                        "ncols 2",
                        "nrows 2",
                        "xllcorner 0",
                        "yllcorner 0",
                        "cellsize 10",
                        "NODATA_value -9999",
                        "1 0",
                        "0 0",
                    ]
                ),
                encoding="utf-8",
            )
            manifest = root / "manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "schema_version": "run_manifest_v1",
                        "cellwise_layers": [
                            {
                                "layer_name": "reach_probability",
                                "grid_path": str(grid_path),
                                "format": "esri_ascii_grid",
                                "thresholds": [],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            with mock.patch.object(overlap.shutil, "which", return_value="/opt/homebrew/bin/ogrinfo"), mock.patch.object(
                overlap, "query_feature_count", return_value=0
            ):
                report = overlap.build_summary(
                    hazard_manifest_path=manifest,
                    context_metadata_path=context_metadata,
                    scope_record_path=ROOT / "validation/pilot_runs/tschamut_public_obstacle_scope_v1.yaml",
                    hazard_layers=["reach_probability"],
                    top_cell_count=1,
                    buffer_radii_m=[0.0, 10.0],
                )

        self.assertEqual(report["final_classification"], "unresolved")
        self.assertIn("No absence claim is made from a zero-overlap result.", overlap.render_markdown(report))


if __name__ == "__main__":
    unittest.main()
