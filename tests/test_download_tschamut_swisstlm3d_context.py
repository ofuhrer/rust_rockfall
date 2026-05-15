from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "download_tschamut_swisstlm3d_context.py"
SPEC = importlib.util.spec_from_file_location("download_tschamut_swisstlm3d_context", SCRIPT_PATH)
assert SPEC is not None
downloader = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = downloader
SPEC.loader.exec_module(downloader)


class TschamutSwissTlm3dDownloadTests(unittest.TestCase):
    def test_metadata_only_mode_writes_unresolved_sidecar_without_download(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with mock.patch.object(
                downloader,
                "head_source",
                return_value={
                    "content_length_bytes": 3_136_564_656,
                    "content_type": "application/zip",
                    "last_modified": "Tue, 01 Jan 2021 00:00:00 GMT",
                    "etag": "fixture",
                },
            ), mock.patch.object(downloader, "download") as download:
                report = downloader.stage_swisstlm3d_context(
                    source_url="https://example.test/swisstlm3d.zip",
                    raw_dir=root / "raw",
                    context_dir=root / "context",
                    scope_record=ROOT / "validation/pilot_runs/tschamut_public_obstacle_scope_v1.yaml",
                    pilot_manifest=ROOT / "data/processed/swisstopo/tschamut_public_pilot_manifest.yaml",
                    accept_large_download=False,
                    force=False,
                    copy=False,
                )

                download.assert_not_called()
                self.assertEqual(report["status"], "metadata_only")
                self.assertTrue(report["accept_large_download_required"])
                metadata = json.loads(Path(report["metadata_path"]).read_text(encoding="utf-8"))
                self.assertFalse(metadata["raw_asset_downloaded"])
                self.assertEqual(metadata["review_classification"], "unresolved")
                self.assertFalse(metadata["operational_claims_allowed"])

    def test_existing_raw_archive_is_staged_and_classified_limiting(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            raw_dir = root / "raw"
            raw_dir.mkdir()
            raw_path = raw_dir / downloader.RAW_FILENAME
            raw_path.write_bytes(b"tiny fixture archive")
            with mock.patch.object(
                downloader,
                "head_source",
                return_value={"content_length_bytes": raw_path.stat().st_size, "content_type": "application/zip"},
            ):
                report = downloader.stage_swisstlm3d_context(
                    source_url="https://example.test/swisstlm3d.zip",
                    raw_dir=raw_dir,
                    context_dir=root / "context",
                    scope_record=ROOT / "validation/pilot_runs/tschamut_public_obstacle_scope_v1.yaml",
                    pilot_manifest=ROOT / "data/processed/swisstopo/tschamut_public_pilot_manifest.yaml",
                    accept_large_download=False,
                    force=False,
                    copy=True,
                )

                self.assertEqual(report["status"], "staged_existing")
                self.assertEqual(report["staged_method"], "copy")
                self.assertTrue(Path(report["context_path"]).exists())
                metadata = json.loads(Path(report["metadata_path"]).read_text(encoding="utf-8"))
                self.assertTrue(metadata["raw_asset_downloaded"])
                self.assertTrue(metadata["staged_asset_present"])
                self.assertEqual(metadata["review_classification"], "limiting")
                self.assertEqual(metadata["raw_asset_sha256"], downloader.sha256_file(raw_path))


if __name__ == "__main__":
    unittest.main()
