from __future__ import annotations

import hashlib
import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path

from scripts import hazard_output_manifests as manifests
from scripts import hazard_output_reports as reports
from scripts import hazard_output_writers as writers


@dataclass
class DummyLayer:
    key: str = "reach_probability"
    title: str = "Reach Probability"
    units: str = "fraction"
    note: str = "Diagnostic reach probability."


class HazardOutputHelperTests(unittest.TestCase):
    def test_writer_records_text_file_metadata_and_checksum(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "nested" / "payload.txt"
            metadata: dict[Path, dict[str, object]] = {}
            kind_seconds: dict[str, float] = {}
            kind_bytes: dict[str, int] = {}

            writers.write_file_text(path, "hello\n", "text", metadata, kind_seconds, kind_bytes, elapsed_seconds=0.25)

            self.assertEqual(path.read_text(encoding="utf-8"), "hello\n")
            self.assertEqual(metadata[path]["total_bytes"], 6)
            self.assertEqual(metadata[path]["sha256"], hashlib.sha256(b"hello\n").hexdigest())
            self.assertEqual(kind_bytes["text"], 6)
            self.assertGreaterEqual(kind_seconds["text"], 0.25)

    def test_manifest_entry_prefers_recorded_writer_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "layer.asc"
            path.write_text("different contents\n", encoding="utf-8")
            entry = manifests.output_manifest_entry(
                path,
                "hazard_layer",
                "esri_ascii_grid",
                output_file_metadata={path: {"total_bytes": 3, "sha256": "abc"}},
            )

            self.assertEqual(entry["total_bytes"], 3)
            self.assertEqual(entry["sha256"], "abc")
            self.assertEqual(entry["row_count"], None)
            self.assertEqual(entry["skipped_empty_files"], None)

    def test_manifest_entry_hashes_file_when_writer_metadata_absent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "layer.asc"
            path.write_text("abc", encoding="utf-8")

            entry = manifests.output_manifest_entry(path, "hazard_layer", "esri_ascii_grid")

            self.assertEqual(entry["total_bytes"], 3)
            self.assertEqual(entry["sha256"], hashlib.sha256(b"abc").hexdigest())

    def test_report_renderer_delegates_output_accounting_to_writer(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "index.html"
            metadata: dict[Path, dict[str, object]] = {}
            kind_seconds: dict[str, float] = {}
            kind_bytes: dict[str, int] = {}

            reports.write_html_report(
                path,
                {"title": "Fixture"},
                {
                    "case_id": "case-a",
                    "model_version": "test",
                    "inputs": {
                        "trajectory_count": 1,
                        "trajectory_sample_count": 2,
                        "deposition_point_count": 3,
                        "impact_event_count": 4,
                    },
                    "grid": {"cell_size_m": 2.0},
                    "layers": [
                        {
                            "key": "reach_probability",
                            "summary": {
                                "valid_cell_count": 2,
                                "nonzero_cell_count": 1,
                                "minimum": 0.0,
                                "maximum": 1.0,
                                "sum": 1.0,
                            },
                        }
                    ],
                    "warnings": [],
                    "limitations": ["No operational claim."],
                    "raster_exports": {"geotiff": False},
                },
                [DummyLayer()],
                {},
                "hazard_fixture",
                metadata,
                kind_seconds,
                kind_bytes,
            )

            text = path.read_text(encoding="utf-8")
            self.assertIn("Fixture Hazard Layers", text)
            self.assertIn("not operational risk", text)
            self.assertIn("valid=2, nonzero=1", text)
            self.assertEqual(metadata[path]["total_bytes"], kind_bytes["html"])
            self.assertIsNotNone(metadata[path]["sha256"])


if __name__ == "__main__":
    unittest.main()
