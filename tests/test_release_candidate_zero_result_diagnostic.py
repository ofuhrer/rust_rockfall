from __future__ import annotations

import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "diagnose_release_candidate_zero_result.py"


def load_module():
    spec = importlib.util.spec_from_file_location("diagnose_release_candidate_zero_result", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {SCRIPT_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


diagnostic = load_module()


class ReleaseCandidateZeroResultDiagnosticTests(unittest.TestCase):
    def test_real_committed_inputs_report_source_zone_footprint_overlap_deferral(self) -> None:
        terrain_path = (
            ROOT
            / "data"
            / "processed"
            / "swisstopo"
            / "chant_sura_fluelapass_portability_example_v1"
            / "input"
            / "terrain.asc"
        )
        metadata_path = (
            ROOT
            / "data"
            / "processed"
            / "swisstopo"
            / "chant_sura_fluelapass_portability_example_v1"
            / "input"
            / "terrain_metadata.yaml"
        )
        source_path = (
            ROOT
            / "data"
            / "processed"
            / "swisstopo"
            / "chant_sura_fluelapass_portability_example_v1"
            / "input"
            / "source_zone_metadata.yaml"
        )

        report = diagnostic.build_report(
            repo_root=ROOT,
            terrain_crop_path=terrain_path,
            terrain_metadata_path=metadata_path,
            source_zone_metadata_path=source_path,
        )

        self.assertEqual(report["diagnostic_status"], "zero_candidates_diagnosed")
        self.assertEqual(report["deferral_record"]["blocker_type"], "source_zone_footprint_overlap")
        self.assertEqual(report["deferral_record"]["slope_band_status"], "not_reached")
        self.assertIn("larger real-staged AOI crop", report["deferral_record"]["required_upstream_replacement"])
        self.assertIn("source-zone footprint", report["deferral_record"]["required_upstream_replacement"])
        self.assertEqual(report["deferral_record"]["downstream_boundary"]["scenario_generation_should_remain_blocked"], True)
        self.assertEqual(report["terrain_screening_decomposition"]["screenable_cell_count"], 0)
        self.assertEqual(report["terrain_screening_decomposition"]["valid_interior_cell_count"], 4)

    def test_flat_screenable_terrain_names_below_band_blocker(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            root = Path(tmp)
            terrain_path, metadata_path, source_path = self._write_inputs(root, slope_step=0.1)

            report = diagnostic.build_report(
                repo_root=root,
                terrain_crop_path=terrain_path,
                terrain_metadata_path=metadata_path,
                source_zone_metadata_path=source_path,
            )

        self.assertEqual(report["schema_version"], "release_candidate_zero_result_diagnostic_v1")
        self.assertEqual(report["diagnostic_status"], "zero_candidates_diagnosed")
        self.assertEqual(report["candidate_cell_count"], 0)
        self.assertEqual(report["first_blocker"]["blocker_id"], "all_screenable_slopes_below_candidate_band")
        self.assertEqual(report["terrain_screening_decomposition"]["screenable_cell_count"], 4)
        self.assertEqual(report["terrain_screening_decomposition"]["candidate_band_cell_count"], 0)
        self.assertTrue(report["unblock_guidance"]["scenario_generation_should_remain_blocked"])
        self.assertFalse(report["claim_boundaries"]["threshold_tuning_performed"])

    def test_steep_screenable_terrain_reports_candidates_present(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            root = Path(tmp)
            terrain_path, metadata_path, source_path = self._write_inputs(root, slope_step=1.3)

            report = diagnostic.build_report(
                repo_root=root,
                terrain_crop_path=terrain_path,
                terrain_metadata_path=metadata_path,
                source_zone_metadata_path=source_path,
            )

        self.assertEqual(report["diagnostic_status"], "candidates_present")
        self.assertGreater(report["candidate_cell_count"], 0)
        self.assertEqual(report["first_blocker"]["blocker_id"], "none")
        self.assertFalse(report["unblock_guidance"]["scenario_generation_should_remain_blocked"])

    def test_cli_writes_json_and_returns_success_for_diagnosed_zero(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            root = Path(tmp)
            terrain_path, metadata_path, source_path = self._write_inputs(root, slope_step=0.1)
            output_path = root / "diagnostic.json"

            with redirect_stdout(io.StringIO()):
                exit_code = diagnostic.main(
                    [
                        "--repo-root",
                        str(root),
                        "--terrain-crop",
                        str(terrain_path),
                        "--terrain-metadata",
                        str(metadata_path),
                        "--source-zone-metadata",
                        str(source_path),
                        "--format",
                        "json",
                        "--json-output",
                        str(output_path),
                    ]
                )
            written = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(exit_code, 0)
        self.assertEqual(written["diagnostic_status"], "zero_candidates_diagnosed")

    def _write_inputs(self, root: Path, *, slope_step: float) -> tuple[Path, Path, Path]:
        terrain_path = root / "terrain.asc"
        metadata_path = root / "terrain_metadata.yaml"
        source_path = root / "source_zone_metadata.yaml"
        rows = []
        for row in range(4):
            values = [100.0 + row * slope_step for _ in range(4)]
            rows.append(" ".join(f"{value:.3f}" for value in values))
        terrain_path.write_text(
            "\n".join(
                [
                    "ncols 4",
                    "nrows 4",
                    "xllcorner 0",
                    "yllcorner 0",
                    "cellsize 2",
                    "NODATA_value -9999",
                    *rows,
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        metadata_path.write_text(
            yaml.safe_dump(
                {
                    "schema_version": 1,
                    "source_product_id": "synthetic_test",
                    "source_product_name": "synthetic",
                    "coordinate_reference_system": {"epsg": 2056, "vertical_datum": "LN02"},
                    "preprocessing": {"crop_extent_lv95_m": {"xmin": 0, "ymin": 0, "xmax": 8, "ymax": 8}},
                },
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        source_path.write_text(
            yaml.safe_dump(
                {
                    "source_zone_id": "outside_test_zone",
                    "crs_epsg": 2056,
                    "vertical_datum": "LN02",
                    "geometry": {
                        "type": "polygon",
                        "vertices": [[20, 20], [22, 20], [22, 22], [20, 22]],
                    },
                    "provenance": {"source": "synthetic test"},
                },
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        return terrain_path, metadata_path, source_path


if __name__ == "__main__":
    unittest.main()
