from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.prototype_cog_conversion import build_translate_command, convert_to_cog


class CogConversionPrototypeTest(unittest.TestCase):
    def test_command_construction(self) -> None:
        command = build_translate_command(Path("input.tif"), Path("/tmp/output.tif"))
        self.assertEqual(
            command,
            [
                "gdal_translate",
                "-of",
                "COG",
                "-co",
                "BLOCKSIZE=256",
                "-co",
                "COMPRESS=ZSTD",
                "input.tif",
                "/tmp/output.tif",
            ],
        )

    def test_successful_conversion_reports_cog_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "input.tif"
            input_path.write_bytes(b"fake geotiff content")
            output_path = Path(tmp) / "output.tif"
            writes: list[Path] = []

            def fake_run(command, capture_output, text, check):
                if command[0] == "gdal_translate":
                    output_path.write_bytes(b"converted cog")
                    writes.append(output_path)
                    return subprocess.CompletedProcess(command, 0, stdout="translate ok", stderr="")
                if command[0] == "gdalinfo":
                    payload = {
                        "driverShortName": "GTiff",
                        "size": [300, 304],
                        "geoTransform": [2696376.0, 2.0, 0.0, 1167992.0, 0.0, -2.0],
                        "metadata": {"IMAGE_STRUCTURE": {"LAYOUT": "COG", "COMPRESSION": "ZSTD"}},
                        "bands": [
                            {
                                "block": [256, 256],
                                "noDataValue": -9999.0,
                                "overviews": [1, 2],
                            }
                        ],
                    }
                    return subprocess.CompletedProcess(command, 0, stdout=json.dumps(payload), stderr="")
                raise AssertionError(f"unexpected command: {command}")

            with patch("scripts.prototype_cog_conversion.shutil.which", return_value="/usr/bin/tool"), patch(
                "scripts.prototype_cog_conversion.subprocess.run",
                side_effect=fake_run,
            ):
                report = convert_to_cog(input_path, output_path)

            self.assertEqual(report["status"], "cog_conversion_sample_ready")
            self.assertTrue(report["output_exists"])
            self.assertEqual(report["output_path"], str(output_path))
            self.assertEqual(report["verification"]["sample_raster_cog_layout"], True)
            self.assertEqual(report["verification"]["sample_raster_tiled"], True)
            self.assertEqual(report["verification"]["sample_raster_overviews"], True)
            self.assertEqual(report["blockers"], [])
            self.assertEqual(writes, [output_path])

    def test_missing_input_reports_blocked_and_does_not_write(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "missing.tif"
            output_path = Path(tmp) / "output.tif"
            with patch("scripts.prototype_cog_conversion.shutil.which", return_value="/usr/bin/tool"):
                report = convert_to_cog(input_path, output_path)

            self.assertEqual(report["status"], "blocked_missing_inputs")
            self.assertFalse(output_path.exists())

    def test_missing_gdal_reports_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "input.tif"
            input_path.write_bytes(b"fake geotiff content")
            output_path = Path(tmp) / "output.tif"
            with patch("scripts.prototype_cog_conversion.shutil.which", return_value=None):
                report = convert_to_cog(input_path, output_path)

            self.assertEqual(report["status"], "blocked_missing_gdal")

    def test_verification_failure_reports_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "input.tif"
            input_path.write_bytes(b"fake geotiff content")
            output_path = Path(tmp) / "output.tif"

            def fake_run(command, capture_output, text, check):
                if command[0] == "gdal_translate":
                    output_path.write_bytes(b"converted cog")
                    return subprocess.CompletedProcess(command, 0, stdout="translate ok", stderr="")
                if command[0] == "gdalinfo":
                    payload = {
                        "driverShortName": "GTiff",
                        "size": [300, 304],
                        "geoTransform": [2696376.0, 2.0, 0.0, 1167992.0, 0.0, -2.0],
                        "metadata": {"IMAGE_STRUCTURE": {"LAYOUT": "GTiff", "COMPRESSION": "ZSTD"}},
                        "bands": [{"block": [300, 304], "noDataValue": -9999.0, "overviews": []}],
                    }
                    return subprocess.CompletedProcess(command, 0, stdout=json.dumps(payload), stderr="")
                raise AssertionError(f"unexpected command: {command}")

            with patch("scripts.prototype_cog_conversion.shutil.which", return_value="/usr/bin/tool"), patch(
                "scripts.prototype_cog_conversion.subprocess.run",
                side_effect=fake_run,
            ):
                report = convert_to_cog(input_path, output_path)

            self.assertEqual(report["status"], "verification_failed")
            self.assertIn("sample_raster_not_tiled", report["blockers"])
            self.assertIn("sample_raster_no_overviews", report["blockers"])
            self.assertIn("sample_raster_not_cog_layout", report["blockers"])


if __name__ == "__main__":
    unittest.main()
