from __future__ import annotations

import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "verify_public_geodata_cache.py"
SPEC = importlib.util.spec_from_file_location("verify_public_geodata_cache", SCRIPT_PATH)
assert SPEC is not None
verifier = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(verifier)


class PublicGeodataCacheVerifierTests(unittest.TestCase):
    def test_verified_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest_path = self._write_cache_manifest(root, checksum_source=b"verified-cache")
            report = verifier.PREFLIGHT.verify_public_geodata_cache(manifest_path)

        self.assertEqual(report["verification_status"], "verified")
        self.assertEqual(report["product_count"], 1)
        self.assertEqual(report["products"][0]["verification_status"], "verified")
        self.assertEqual(report["products"][0]["checksum_match"], True)
        self.assertEqual(report["products"][0]["metadata_mismatches"], [])

    def test_missing_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest_path = self._write_cache_manifest(root, create_files=False)
            report = verifier.PREFLIGHT.verify_public_geodata_cache(manifest_path)

        self.assertEqual(report["verification_status"], "missing")
        self.assertEqual(report["products"][0]["verification_status"], "missing")
        self.assertIn("staged_path", report["products"][0]["missing_paths"])
        self.assertIn("metadata_path", report["products"][0]["missing_paths"])

    def test_checksum_mismatch_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest_path = self._write_cache_manifest(
                root,
                checksum_source=b"expected-bytes",
                staged_bytes=b"actual-bytes",
            )
            report = verifier.PREFLIGHT.verify_public_geodata_cache(manifest_path)

        self.assertEqual(report["verification_status"], "checksum_mismatch")
        self.assertEqual(report["products"][0]["verification_status"], "checksum_mismatch")
        self.assertFalse(report["products"][0]["checksum_match"])
        self.assertEqual(report["products"][0]["metadata_mismatches"], [])

    def test_metadata_mismatch_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest_path = self._write_cache_manifest(
                root,
                metadata_overrides={"resolution_m": 1.0},
            )
            report = verifier.PREFLIGHT.verify_public_geodata_cache(manifest_path)

        self.assertEqual(report["verification_status"], "metadata_mismatch")
        self.assertEqual(report["products"][0]["verification_status"], "metadata_mismatch")
        self.assertTrue(report["products"][0]["checksum_match"])
        self.assertIn("resolution_m", report["products"][0]["metadata_mismatches"])

    def _write_cache_manifest(
        self,
        root: Path,
        *,
        checksum_source: bytes = b"cache-bytes",
        staged_bytes: bytes | None = None,
        metadata_overrides: dict[str, object] | None = None,
        create_files: bool = True,
    ) -> Path:
        staged_path = root / "cache" / "terrain.asc"
        metadata_path = root / "cache" / "terrain.yaml"
        staged_checksum = hashlib.sha256(checksum_source).hexdigest()
        metadata = {
            "source_product_id": "swissalti3d_2m",
            "source_product_name": "swissALTI3D",
            "source_url": "https://example.invalid/swisstopo",
            "product_version": "2019",
            "tile_id": "2696-1167",
            "crs": "EPSG:2056",
            "resolution_m": 2.0,
            "crop_extent_lv95_m": {"xmin": 1.0, "ymin": 2.0, "xmax": 3.0, "ymax": 4.0},
            "license_or_terms_reference": "terms example",
        }
        if metadata_overrides:
            metadata.update(metadata_overrides)

        if create_files:
            staged_path.parent.mkdir(parents=True, exist_ok=True)
            staged_path.write_bytes(staged_bytes if staged_bytes is not None else checksum_source)
            metadata_path.write_text(yaml.safe_dump(metadata, sort_keys=False), encoding="utf-8")

        manifest = {
            "schema_version": "public_geodata_cache_verification_manifest_v1",
            "candidate_site_id": "demo_site",
            "candidate_site_name": "Demo Site",
            "products": [
                {
                    "product_id": "terrain_crop",
                    "source_product_id": "swissalti3d_2m",
                    "source_product_name": "swissALTI3D",
                    "source_url_or_download_record": "https://example.invalid/swisstopo",
                    "product_version_or_date": "2019",
                    "tile_id_or_delivery_identifier": "2696-1167",
                    "checksum_sha256": staged_checksum,
                    "crs": "EPSG:2056",
                    "resolution_m": 2.0,
                    "crop_extent_lv95_m": {"xmin": 1.0, "ymin": 2.0, "xmax": 3.0, "ymax": 4.0},
                    "license_or_terms_reference": "terms example",
                    "staged_path": str(staged_path),
                    "metadata_path": str(metadata_path),
                }
            ],
        }
        manifest_path = root / "cache_manifest.yaml"
        manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
        return manifest_path


if __name__ == "__main__":
    unittest.main()
