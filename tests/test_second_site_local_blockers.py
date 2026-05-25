from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts import inventory_second_site_local_blockers as blockers


class SecondSiteLocalBlockerTests(unittest.TestCase):
    def test_default_inventory_groups_current_local_blockers(self) -> None:
        report = blockers.build_report()

        self.assertEqual(report["schema_version"], blockers.SCHEMA_VERSION)
        self.assertEqual(report["inventory_status"], "blocked_local_inputs")
        groups = {group["group_id"]: group for group in report["blocker_groups"]}
        self.assertEqual(groups["terrain_inputs"]["status"], "ready")
        self.assertEqual(groups["public_context_inputs"]["status"], "blocked_deferred_public_context")
        self.assertEqual(groups["prepared_pilot_inputs"]["status"], "blocked_by_local_inputs")
        self.assertEqual(groups["source_zone_inputs"]["status"], "ready")
        self.assertEqual(groups["scenario_inputs"]["status"], "ready")
        self.assertIn("plan_swisstopo_aoi_acquisition.py", report["next_local_unblock_command"])
        self.assertFalse(report["claim_boundaries"]["balfrin_required"])
        self.assertFalse(report["claim_boundaries"]["downloads_authorized"])

    def test_ready_terrain_extent_shape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            metadata_path = root / "terrain_metadata.yaml"
            metadata_path.write_text(
                "\n".join(
                    [
                        "crop_extent_lv95_m:",
                        "  xmin: 0",
                        "  ymin: 0",
                        "  xmax: 10",
                        "  ymax: 10",
                    ]
                ),
                encoding="utf-8",
            )
            site_config = {"site_extent": {"xmin": 1, "ymin": 1, "xmax": 9, "ymax": 9}}
            requirements = {
                "terrain_crs_vertical_datum": {"path_or_pattern": str(metadata_path)},
            }

            result = blockers.terrain_domain_qa_status(site_config, requirements)

        self.assertEqual(result["status"], "ready")

    def test_blocked_terrain_extent_shape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            metadata_path = root / "terrain_metadata.yaml"
            metadata_path.write_text(
                "\n".join(
                    [
                        "crop_extent_lv95_m:",
                        "  xmin: 0",
                        "  ymin: 0",
                        "  xmax: 2",
                        "  ymax: 2",
                    ]
                ),
                encoding="utf-8",
            )
            site_config = {"site_extent": {"xmin": 0, "ymin": 0, "xmax": 9, "ymax": 9}}
            requirements = {
                "terrain_crs_vertical_datum": {"path_or_pattern": str(metadata_path)},
            }

            result = blockers.terrain_domain_qa_status(site_config, requirements)

        self.assertEqual(result["status"], "blocked_terrain_qa")
        self.assertEqual(result["blocked_reason"], "configured_site_extent_exceeds_terrain_crop")
        self.assertIn("terrain crop", result["next_local_action"])

    def test_blocked_aoi_tile_catalog_shape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            catalog_path = root / "aoi_tile_catalog.yaml"
            catalog_path.write_text(
                "\n".join(
                    [
                        "tiles:",
                        "  - tile_id: small",
                        "    extent_lv95_m:",
                        "      xmin: 0",
                        "      ymin: 0",
                        "      xmax: 2",
                        "      ymax: 2",
                    ]
                ),
                encoding="utf-8",
            )
            site_config = {"site_extent": {"xmin": 0, "ymin": 0, "xmax": 9, "ymax": 9}}
            requirements = {
                "aoi_tile_catalog": {"path_or_pattern": str(catalog_path)},
            }

            result = blockers.aoi_tile_catalog_qa_status(site_config, requirements)

        self.assertEqual(result["status"], "blocked_aoi_tile_qa")
        self.assertEqual(result["blocked_reason"], "configured_site_extent_exceeds_aoi_tile_catalog")
        self.assertIn("AOI tile catalog", result["next_local_action"])

    def test_blocked_source_zone_domain_shape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_zone_path = root / "source_zone_metadata.yaml"
            source_zone_path.write_text(
                "\n".join(
                    [
                        "geometry:",
                        "  vertices:",
                        "    - [1, 1]",
                        "    - [12, 1]",
                        "release_points:",
                        "  - x: 2",
                        "    y: 20",
                    ]
                ),
                encoding="utf-8",
            )
            site_config = {"site_extent": {"xmin": 0, "ymin": 0, "xmax": 9, "ymax": 9}}
            requirements = {
                "source_zone_metadata": {"path_or_pattern": str(source_zone_path)},
            }

            result = blockers.source_zone_domain_qa_status(site_config, requirements)

        self.assertEqual(result["status"], "blocked_source_zone_domain_qa")
        self.assertEqual(result["blocked_reason"], "source_zone_coordinates_outside_configured_site_extent")
        self.assertEqual(result["outside_vertex_count"], 1)
        self.assertEqual(result["outside_release_point_count"], 1)
        self.assertIn("source-zone metadata", result["next_local_action"])

    def test_text_report_names_groups_and_commands(self) -> None:
        text = blockers.render_text_report(blockers.build_report())

        self.assertIn("terrain_inputs", text)
        self.assertIn("public_context_inputs", text)
        self.assertIn("prepared_pilot_inputs", text)
        self.assertIn("plan_swisstopo_aoi_acquisition.py", text)
        self.assertIn("balfrin_required: False", text)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
