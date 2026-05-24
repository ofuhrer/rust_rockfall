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

    def test_text_report_names_groups_and_commands(self) -> None:
        text = blockers.render_text_report(blockers.build_report())

        self.assertIn("terrain_inputs", text)
        self.assertIn("public_context_inputs", text)
        self.assertIn("prepared_pilot_inputs", text)
        self.assertIn("plan_swisstopo_aoi_acquisition.py", text)
        self.assertIn("balfrin_required: False", text)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
