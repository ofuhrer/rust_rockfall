from __future__ import annotations

import contextlib
import io
import json
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
        self.assertEqual(report["cache_audit_status"], "ready")
        self.assertEqual(report["product_count"], 1)
        self.assertEqual(report["products"][0]["verification_status"], "verified")
        self.assertEqual(report["products"][0]["provenance_classification"], "real_staged")
        self.assertEqual(report["products"][0]["checksum_match"], True)
        self.assertEqual(report["products"][0]["metadata_mismatches"], [])

    def test_fixture_backed_state_stays_blocked_from_real_aoi_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest_path = self._write_cache_manifest(
                root,
                checksum_source=b"fixture-backed-cache",
                product_overrides={
                    "source_product_id": "swissalti3d_fixture_terrain_crop",
                    "provenance_classification": "fixture_backed",
                },
                metadata_overrides={
                    "source_product_id": "swissalti3d_fixture_terrain_crop",
                    "provenance_classification": "fixture_backed",
                },
            )
            report = verifier.PREFLIGHT.verify_public_geodata_cache(manifest_path)

        self.assertEqual(report["verification_status"], "verified")
        self.assertEqual(report["cache_audit_status"], "fixture_backed")
        self.assertEqual(report["cache_audit_summary"]["fixture_backed_required_product_count"], 1)
        self.assertEqual(report["products"][0]["provenance_classification"], "fixture_backed")
        self.assertEqual(
            report["products"][0]["provenance_reason"],
            "explicit provenance classification from the cache contract",
        )

    def test_missing_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest_path = self._write_cache_manifest(root, create_files=False)
            report = verifier.PREFLIGHT.verify_public_geodata_cache(manifest_path)

        self.assertEqual(report["verification_status"], "missing")
        self.assertEqual(report["cache_audit_status"], "missing")
        self.assertEqual(report["products"][0]["verification_status"], "missing")
        self.assertEqual(report["products"][0]["provenance_classification"], "missing")
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
        self.assertEqual(report["cache_audit_status"], "partial")
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
        self.assertEqual(report["cache_audit_status"], "metadata_mismatch")
        self.assertEqual(report["products"][0]["verification_status"], "metadata_mismatch")
        self.assertTrue(report["products"][0]["checksum_match"])
        self.assertIn("resolution_m", report["products"][0]["metadata_mismatches"])

    def test_main_json_output_is_serializable(self) -> None:
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            exit_code = verifier.main(
                [
                    "--cache-manifest",
                    str(ROOT / "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/public_geodata_cache_manifest.yaml"),
                    "--format",
                    "json",
                ]
            )

        report = json.loads(stdout.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(report["verification_status"], "verified")
        self.assertEqual(report["cache_audit_status"], "ready")
        self.assertEqual(report["cache_integrity_status"], "ready")
        self.assertEqual(report["cache_recovery"]["status"], "ready")
        self.assertTrue(report["cache_recovery"]["next_command"].endswith("--format json"))
        self.assertEqual(report["products"][0]["provenance_classification"], "real_staged")
        self.assertEqual(report["products"][0]["actual"]["metadata"]["product_version_or_date"], "2019-01-01")

    def test_main_exit_code_tracks_cache_integrity_status(self) -> None:
        scenarios = [
            {
                "name": "ready",
                "manifest_kwargs": {"checksum_source": b"ready-cache"},
                "expected_exit_code": 0,
                "expected_integrity_status": "ready",
                "expected_audit_status": "ready",
                "expected_verification_status": "verified",
            },
            {
                "name": "missing",
                "manifest_kwargs": {"create_files": False},
                "expected_exit_code": 2,
                "expected_integrity_status": "missing",
                "expected_audit_status": "missing",
                "expected_verification_status": "missing",
            },
            {
                "name": "partial",
                "manifest_kwargs": {"checksum_source": b"expected-bytes", "staged_bytes": b"actual-bytes"},
                "expected_exit_code": 2,
                "expected_integrity_status": "partial",
                "expected_audit_status": "partial",
                "expected_verification_status": "checksum_mismatch",
            },
            {
                "name": "metadata_mismatch",
                "manifest_kwargs": {"metadata_overrides": {"resolution_m": 1.0}},
                "expected_exit_code": 2,
                "expected_integrity_status": "metadata_mismatch",
                "expected_audit_status": "metadata_mismatch",
                "expected_verification_status": "metadata_mismatch",
            },
            {
                "name": "fixture_backed",
                "manifest_kwargs": {
                    "checksum_source": b"fixture-backed-cache",
                    "product_overrides": {
                        "source_product_id": "swissalti3d_fixture_terrain_crop",
                        "provenance_classification": "fixture_backed",
                    },
                    "metadata_overrides": {
                        "source_product_id": "swissalti3d_fixture_terrain_crop",
                        "provenance_classification": "fixture_backed",
                    },
                },
                "expected_exit_code": 2,
                "expected_integrity_status": "fixture_backed",
                "expected_audit_status": "fixture_backed",
                "expected_verification_status": "verified",
            },
        ]

        for scenario in scenarios:
            with self.subTest(scenario=scenario["name"]):
                with tempfile.TemporaryDirectory() as tmp:
                    root = Path(tmp)
                    manifest_path = self._write_cache_manifest(root, **scenario["manifest_kwargs"])
                    stdout = io.StringIO()
                    with contextlib.redirect_stdout(stdout):
                        exit_code = verifier.main(["--cache-manifest", str(manifest_path), "--format", "json"])
                    report = json.loads(stdout.getvalue())

                self.assertEqual(exit_code, scenario["expected_exit_code"])
                self.assertEqual(report["cache_integrity_status"], scenario["expected_integrity_status"])
                self.assertEqual(report["cache_audit_status"], scenario["expected_audit_status"])
                self.assertEqual(report["verification_status"], scenario["expected_verification_status"])

    def test_fixture_backed_states_surface_actionable_recovery_hints(self) -> None:
        scenarios = [
            {
                "name": "ready",
                "product_specs": [
                    {
                        "product_id": "terrain_crop_real",
                        "staged_path": "cache/ready/terrain.asc",
                        "metadata_path": "cache/ready/terrain_metadata.yaml",
                        "source_mode": "copy_fixture",
                    }
                ],
                "expected_audit_status": "ready",
                "expected_integrity_status": "ready",
                "expected_recovery_status": "ready",
                "expected_recovery_next_files": [],
                "expected_product_recovery_count": 0,
            },
            {
                "name": "missing",
                "product_specs": [
                    {
                        "product_id": "terrain_crop_missing",
                        "staged_path": "cache/missing/terrain.asc",
                        "metadata_path": "cache/missing/terrain_metadata.yaml",
                        "source_mode": "missing",
                    }
                ],
                "expected_audit_status": "missing",
                "expected_integrity_status": "missing",
                "expected_recovery_status": "missing",
                "expected_recovery_next_files": [
                    str(Path("cache/missing/terrain.asc")),
                    str(Path("cache/missing/terrain_metadata.yaml")),
                ],
                "expected_product_recovery_count": 1,
            },
            {
                "name": "partial",
                "product_specs": [
                    {
                        "product_id": "terrain_crop_real",
                        "staged_path": "cache/partial/real/terrain.asc",
                        "metadata_path": "cache/partial/real/terrain_metadata.yaml",
                        "source_mode": "copy_fixture",
                    },
                    {
                        "product_id": "terrain_crop_fixture_backed",
                        "staged_path": "cache/partial/fixture_backed/fixture_terrain.asc",
                        "metadata_path": "cache/partial/fixture_backed/fixture_terrain_metadata.yaml",
                        "source_mode": "copy_fixture",
                    },
                ],
                "expected_audit_status": "partial",
                "expected_integrity_status": "partial",
                "expected_recovery_status": "partial",
                "expected_product_recovery_count": 1,
            },
            {
                "name": "metadata_mismatch",
                "product_specs": [
                    {
                        "product_id": "terrain_crop_mismatch",
                        "staged_path": "cache/mismatch/terrain.asc",
                        "metadata_path": "cache/mismatch/terrain_metadata.yaml",
                        "source_mode": "copy_fixture",
                        "manifest_overrides": {"resolution_m": 1.0},
                    }
                ],
                "expected_audit_status": "metadata_mismatch",
                "expected_integrity_status": "metadata_mismatch",
                "expected_recovery_status": "metadata_mismatch",
                "expected_recovery_next_files": [
                    str(Path("cache/mismatch/terrain.asc")),
                    str(Path("cache/mismatch/terrain_metadata.yaml")),
                ],
                "expected_product_recovery_count": 1,
            },
        ]

        for scenario in scenarios:
            with self.subTest(scenario=scenario["name"]):
                with tempfile.TemporaryDirectory() as tmp:
                    root = Path(tmp)
                    manifest_path = self._write_fixture_backed_cache_manifest(root, scenario["product_specs"])
                    report = verifier.PREFLIGHT.verify_public_geodata_cache(manifest_path)

                self.assertEqual(report["cache_audit_status"], scenario["expected_audit_status"])
                self.assertEqual(report.get("cache_integrity_status") or report["cache_audit_status"], scenario["expected_integrity_status"])
                self.assertEqual(report["cache_recovery"]["status"], scenario["expected_recovery_status"])
                self.assertEqual(len(report["cache_recovery"]["product_hints"]), scenario["expected_product_recovery_count"])
                if scenario["name"] == "ready":
                    self.assertEqual(report["cache_recovery"]["next_files"], [])
                    self.assertEqual(report["cache_recovery"]["product_hints"], [])
                    self.assertEqual(report["products"][0]["verification_status"], "verified")
                    self.assertEqual(report["products"][0]["provenance_classification"], "real_staged")
                elif scenario["name"] == "missing":
                    self.assertEqual(
                        report["cache_recovery"]["next_files"],
                        [
                            str(root / "cache/missing/terrain.asc"),
                            str(root / "cache/missing/terrain_metadata.yaml"),
                        ],
                    )
                    self.assertEqual(report["products"][0]["verification_status"], "missing")
                    self.assertEqual(report["products"][0]["recovery_hint"]["blocked_status"], "blocked_missing_inputs")
                    self.assertIn("missing_paths", report["products"][0]["recovery_hint"]["next_file_templates"][0])
                elif scenario["name"] == "partial":
                    self.assertEqual(
                        report["cache_recovery"]["next_files"],
                        [
                            str(root / "cache/partial/fixture_backed/fixture_terrain.asc"),
                            str(root / "cache/partial/fixture_backed/fixture_terrain_metadata.yaml"),
                        ],
                    )
                    self.assertEqual(report["products"][1]["provenance_classification"], "fixture_backed")
                    self.assertEqual(report["products"][1]["recovery_hint"]["blocked_status"], "blocked_fixture_backed_inputs")
                    self.assertIn("replaced by a real staged input", report["products"][1]["recovery_hint"]["recovery_note"])
                elif scenario["name"] == "metadata_mismatch":
                    self.assertEqual(
                        report["cache_recovery"]["next_files"],
                        [
                            str(root / "cache/mismatch/terrain.asc"),
                            str(root / "cache/mismatch/terrain_metadata.yaml"),
                        ],
                    )
                    self.assertEqual(report["products"][0]["verification_status"], "metadata_mismatch")
                    self.assertIn("metadata sidecar", report["products"][0]["recovery_hint"]["recovery_note"])

    def _write_cache_manifest(
        self,
        root: Path,
        *,
        checksum_source: bytes = b"cache-bytes",
        staged_bytes: bytes | None = None,
        metadata_overrides: dict[str, object] | None = None,
        product_overrides: dict[str, object] | None = None,
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
        if product_overrides:
            manifest["products"][0].update(product_overrides)
        manifest_path = root / "cache_manifest.yaml"
        manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
        return manifest_path

    def _write_fixture_backed_cache_manifest(self, root: Path, product_specs: list[dict[str, object]]) -> Path:
        fixture_root = ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_minimal_staging"
        fixture_staged_path = fixture_root / "terrain.asc"
        fixture_checksum = hashlib.sha256(fixture_staged_path.read_bytes()).hexdigest()
        normalized_metadata = {
            "source_product_id": "swissalti3d_2m",
            "source_product_name": "swissALTI3D",
            "source_url": "https://example.invalid/swisstopo",
            "product_version": "2019-01-01",
            "tile_id": "2696-1167",
            "crs": "EPSG:2056",
            "resolution_m": 2.0,
            "crop_extent_lv95_m": {"xmin": 2793000.0, "ymin": 1180200.0, "xmax": 2793008.0, "ymax": 1180208.0},
            "license_or_terms_reference": "terms example",
            "raw_checksum": fixture_checksum,
            "processed_checksum": fixture_checksum,
            "preprocessing_command_and_timestamp": "fixture-backed test",
        }

        manifest_products: list[dict[str, object]] = []
        for spec in product_specs:
            product_id = str(spec["product_id"])
            source_mode = str(spec["source_mode"])
            staged_path = root / str(spec["staged_path"])
            metadata_path = root / str(spec["metadata_path"])
            manifest_overrides = spec.get("manifest_overrides") or {}
            file_metadata_overrides = spec.get("file_metadata_overrides") or {}

            actual_staged_path = staged_path
            actual_metadata_path = metadata_path
            actual_metadata = dict(normalized_metadata)
            if isinstance(file_metadata_overrides, dict):
                actual_metadata.update(file_metadata_overrides)

            if source_mode == "copy_fixture":
                actual_staged_path.parent.mkdir(parents=True, exist_ok=True)
                actual_staged_path.write_bytes(fixture_staged_path.read_bytes())
                actual_metadata_path.parent.mkdir(parents=True, exist_ok=True)
                actual_metadata_path.write_text(yaml.safe_dump(actual_metadata, sort_keys=False), encoding="utf-8")
            elif source_mode == "missing":
                pass
            else:
                raise AssertionError(f"unsupported source mode: {source_mode}")

            product_record = {
                "product_id": product_id,
                "source_product_id": "swissalti3d_2m",
                "source_product_name": "swissALTI3D",
                "source_url_or_download_record": "https://example.invalid/swisstopo",
                "product_version_or_date": normalized_metadata["product_version"],
                "tile_id_or_delivery_identifier": "2696-1167",
                "checksum_sha256": fixture_checksum,
                "crs": "EPSG:2056",
                "resolution_m": 2.0,
                "crop_extent_lv95_m": {"xmin": 2793000.0, "ymin": 1180200.0, "xmax": 2793008.0, "ymax": 1180208.0},
                "license_or_terms_reference": "terms example",
                "staged_path": str(actual_staged_path),
                "metadata_path": str(actual_metadata_path),
            }
            if isinstance(manifest_overrides, dict):
                product_record.update(manifest_overrides)
            manifest_products.append(product_record)

        manifest = {
            "schema_version": "public_geodata_cache_verification_manifest_v1",
            "candidate_site_id": "demo_site",
            "candidate_site_name": "Demo Site",
            "products": manifest_products,
        }
        manifest_path = root / "cache_manifest.yaml"
        manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
        return manifest_path


if __name__ == "__main__":
    unittest.main()
