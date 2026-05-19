from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
STAGE_SCRIPT_PATH = ROOT / "scripts" / "stage_public_geodata_cache.py"
VERIFY_SCRIPT_PATH = ROOT / "scripts" / "verify_public_geodata_cache.py"
SITE_ID = "demo_site"
SITE_ROOT_RELATIVE = Path("data/processed/swisstopo") / SITE_ID


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


stager = _load_module(STAGE_SCRIPT_PATH, "stage_public_geodata_cache")
verifier = _load_module(VERIFY_SCRIPT_PATH, "verify_public_geodata_cache_for_stager_tests")


class PublicGeodataCacheStagerTests(unittest.TestCase):
    def test_wizard_mode_writes_proposal_before_applying_verified_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            site_root = root / SITE_ROOT_RELATIVE
            manifest_path = site_root / "input" / "public_geodata_cache_manifest.yaml"
            terrain_path, terrain_metadata_path, context_path, context_metadata_path, context_dir = self._write_wizard_inputs(root)

            original_stage_root = stager.PREFLIGHT.ROOT
            original_verify_root = verifier.PREFLIGHT.ROOT
            stager.PREFLIGHT.ROOT = root
            verifier.PREFLIGHT.ROOT = root
            try:
                manifest_path.parent.mkdir(parents=True, exist_ok=True)
                manifest_path.write_text(
                    yaml.safe_dump(
                        {
                            "schema_version": "swiss_public_geodata_cache_manifest_template_v1",
                            "candidate_site_id": SITE_ID,
                            "candidate_site_name": "Demo Site",
                            "products": [
                                self._terrain_product_row(root, terrain_path, terrain_metadata_path),
                                self._context_product_row(root, context_path, context_metadata_path),
                                self._optional_barrier_row(root),
                            ],
                        },
                        sort_keys=False,
                    ),
                    encoding="utf-8",
                )

                proposal_output = site_root / "input" / "wizard_proposal.json"
                dry_run_report = stager.stage_public_geodata_cache(
                    manifest_path,
                    local_paths=[terrain_path, terrain_metadata_path, context_dir],
                    proposal_output=proposal_output,
                )
                self.assertTrue(proposal_output.exists())
                applied_report = stager.stage_public_geodata_cache(
                    manifest_path,
                    local_paths=[terrain_path, terrain_metadata_path, context_dir],
                    proposal_output=proposal_output,
                    apply=True,
                )
                verified_manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
                verification_report = verifier.PREFLIGHT.verify_public_geodata_cache(manifest_path)
            finally:
                stager.PREFLIGHT.ROOT = original_stage_root
                verifier.PREFLIGHT.ROOT = original_verify_root

        self.assertEqual(dry_run_report["wizard_mode"], True)
        self.assertIn(dry_run_report["proposal_status"], {"ready_to_apply", "ready_with_optional_deferred"})
        self.assertEqual(applied_report["wizard_mode"], True)
        self.assertEqual(applied_report["staging_status"], "verified")
        self.assertEqual(applied_report["proposal"]["proposal_status"], dry_run_report["proposal_status"])
        self.assertEqual(verified_manifest["staging_status"], "verified")
        self.assertEqual(verified_manifest["products"][0]["staging_status"], "verified")
        self.assertEqual(verified_manifest["products"][1]["staging_status"], "verified")
        self.assertEqual(verified_manifest["products"][2]["staging_status"], "optional_missing")
        self.assertEqual(verification_report["verification_status"], "verified")

    def test_wizard_mode_reports_missing_metadata_before_apply(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            site_root = root / SITE_ROOT_RELATIVE
            manifest_path = site_root / "input" / "public_geodata_cache_manifest.yaml"
            terrain_path = site_root / "input" / "terrain.asc"
            terrain_path.parent.mkdir(parents=True, exist_ok=True)
            terrain_path.write_text("terrain-bytes\n", encoding="utf-8")

            original_stage_root = stager.PREFLIGHT.ROOT
            stager.PREFLIGHT.ROOT = root
            try:
                manifest_path.parent.mkdir(parents=True, exist_ok=True)
                manifest_path.write_text(
                    yaml.safe_dump(
                        {
                            "schema_version": "swiss_public_geodata_cache_manifest_template_v1",
                            "candidate_site_id": SITE_ID,
                            "candidate_site_name": "Demo Site",
                            "products": [self._terrain_product_row(root, terrain_path, None)],
                        },
                        sort_keys=False,
                    ),
                    encoding="utf-8",
                )

                report = stager.stage_public_geodata_cache(manifest_path, local_paths=[terrain_path])
            finally:
                stager.PREFLIGHT.ROOT = original_stage_root

        self.assertEqual(report["wizard_mode"], True)
        self.assertEqual(report["proposal_status"], "blocked_missing_metadata")
        self.assertEqual(report["products"][0]["proposal_status"], "missing_metadata")
        self.assertIn("missing metadata", report["products"][0]["blocking_reasons"])

    def test_wizard_mode_reports_ambiguous_directory_match(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            site_root = root / SITE_ROOT_RELATIVE
            manifest_path = site_root / "input" / "public_geodata_cache_manifest.yaml"
            ambiguous_root = root / "downloads"
            bundle_a = ambiguous_root / "alpha" / "swisstlm3d"
            bundle_b = ambiguous_root / "beta" / "swisstlm3d"
            self._write_directory_bundle(bundle_a)
            self._write_directory_bundle(bundle_b)

            original_stage_root = stager.PREFLIGHT.ROOT
            stager.PREFLIGHT.ROOT = root
            try:
                manifest_path.parent.mkdir(parents=True, exist_ok=True)
                manifest_path.write_text(
                    yaml.safe_dump(
                        {
                            "schema_version": "swiss_public_geodata_cache_manifest_template_v1",
                            "candidate_site_id": SITE_ID,
                            "candidate_site_name": "Demo Site",
                            "products": [
                                {
                                    "category": "swisstlm3d_context",
                                    "product_id": "swisstlm3d_context",
                                    "source_product_id": "swisstlm3d",
                                    "source_product_name": "swissTLM3D",
                                    "source_url_or_download_record": "https://example.invalid/swisstlm3d",
                                    "product_version_or_date": "2026.1",
                                    "tile_id_or_delivery_identifier": "tile-1",
                                    "checksum_sha256": stager.PREFLIGHT.sha256_path(bundle_a / "payload.bin"),
                                    "crs": "EPSG:2056",
                                    "resolution_m": 1.0,
                                    "crop_extent_lv95_m": {"xmin": 2793000.0, "ymin": 1180200.0, "xmax": 2793008.0, "ymax": 1180208.0},
                                    "license_or_terms_reference": "example terms",
                                    "raw_checksum": stager.PREFLIGHT.sha256_path(bundle_a / "payload.bin"),
                                    "processed_checksum": stager.PREFLIGHT.sha256_path(bundle_a / "payload.bin"),
                                    "preprocessing_command_and_timestamp": "manual fixture staging",
                                    "required": True,
                                    "staged_path": str(SITE_ROOT_RELATIVE / "context" / "swisstlm3d.bin"),
                                    "metadata_path": str(SITE_ROOT_RELATIVE / "context" / "swisstlm3d" / "metadata.json"),
                                }
                            ],
                        },
                        sort_keys=False,
                    ),
                    encoding="utf-8",
                )

                report = stager.stage_public_geodata_cache(manifest_path, local_paths=[ambiguous_root])
            finally:
                stager.PREFLIGHT.ROOT = original_stage_root

        self.assertEqual(report["wizard_mode"], True)
        self.assertEqual(report["proposal_status"], "blocked_ambiguous_match")
        self.assertEqual(report["products"][0]["proposal_status"], "ambiguous_match")

    def test_verified_manifest_records_file_and_directory_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            site_root = root / SITE_ROOT_RELATIVE
            manifest_path = site_root / "input" / "public_geodata_cache_manifest.yaml"
            terrain_path, terrain_metadata_path, context_path, context_metadata_path = self._write_verified_inputs(root)

            original_stage_root = stager.PREFLIGHT.ROOT
            original_verify_root = verifier.PREFLIGHT.ROOT
            stager.PREFLIGHT.ROOT = root
            verifier.PREFLIGHT.ROOT = root
            try:
                manifest_path.parent.mkdir(parents=True, exist_ok=True)
                manifest_path.write_text(
                    yaml.safe_dump(
                        {
                            "schema_version": "swiss_public_geodata_cache_manifest_template_v1",
                            "candidate_site_id": SITE_ID,
                            "candidate_site_name": "Demo Site",
                            "products": [
                                self._terrain_product_row(root, terrain_path, terrain_metadata_path),
                                self._context_product_row(root, context_path, context_metadata_path),
                                self._optional_barrier_row(root),
                            ],
                        },
                        sort_keys=False,
                    ),
                    encoding="utf-8",
                )

                report = stager.stage_public_geodata_cache(manifest_path)
                verified_manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
                verification_report = verifier.PREFLIGHT.verify_public_geodata_cache(manifest_path)
            finally:
                stager.PREFLIGHT.ROOT = original_stage_root
                verifier.PREFLIGHT.ROOT = original_verify_root

        self.assertEqual(report["staging_status"], "verified")
        self.assertEqual(report["staged_product_count"], 2)
        self.assertEqual(report["optional_missing_product_count"], 1)
        self.assertEqual(report["missing_product_count"], 0)
        self.assertEqual(report["checksum_mismatch_product_count"], 0)
        self.assertEqual(report["metadata_mismatch_product_count"], 0)
        self.assertEqual(report["unsupported_product_count"], 0)
        self.assertEqual(verified_manifest["staging_status"], "verified")
        self.assertEqual(verified_manifest["products"][0]["staging_status"], "verified")
        self.assertEqual(verified_manifest["products"][1]["staging_status"], "verified")
        self.assertEqual(verified_manifest["products"][2]["staging_status"], "optional_missing")
        self.assertEqual(verification_report["verification_status"], "verified")
        self.assertEqual(verification_report["product_count"], 3)
        self.assertEqual(verification_report["products"][2]["verification_status"], "optional_missing")

    def test_fail_closed_statuses_cover_missing_checksum_metadata_and_unsupported(self) -> None:
        cases = [
            (
                "missing",
                self._terrain_product_row(Path("/"), None, None, staged_exists=False),
                "missing",
            ),
            (
                "checksum_mismatch",
                self._terrain_product_row_with_checksum_mismatch(),
                "checksum_mismatch",
            ),
            (
                "metadata_mismatch",
                self._terrain_product_row_with_metadata_mismatch(),
                "metadata_mismatch",
            ),
            (
                "unsupported_product",
                {
                    "category": "bogus_product",
                    "product_id": "bogus_product",
                    "source_product_id": "bogus_product",
                    "source_product_name": "Bogus",
                    "staged_path": str(SITE_ROOT_RELATIVE / "input" / "bogus.bin"),
                    "metadata_path": str(SITE_ROOT_RELATIVE / "input" / "bogus.yaml"),
                    "required": True,
                },
                "unsupported_product",
            ),
        ]

        for label, product_row, expected_status in cases:
            with self.subTest(label=label):
                with tempfile.TemporaryDirectory() as tmp:
                    root = Path(tmp)
                    site_root = root / SITE_ROOT_RELATIVE
                    manifest_path = site_root / "input" / "public_geodata_cache_manifest.yaml"
                    original_stage_root = stager.PREFLIGHT.ROOT
                    original_verify_root = verifier.PREFLIGHT.ROOT
                    stager.PREFLIGHT.ROOT = root
                    verifier.PREFLIGHT.ROOT = root
                    try:
                        manifest_path.parent.mkdir(parents=True, exist_ok=True)
                        if expected_status == "metadata_mismatch":
                            self._write_metadata_mismatch_inputs(root)
                        elif expected_status == "checksum_mismatch":
                            self._write_checksum_mismatch_inputs(root)
                        elif expected_status == "missing":
                            self._write_missing_inputs(root)
                        elif expected_status == "unsupported_product":
                            bogus_bin = site_root / "input" / "bogus.bin"
                            bogus_yaml = site_root / "input" / "bogus.yaml"
                            bogus_bin.parent.mkdir(parents=True, exist_ok=True)
                            bogus_bin.write_text("bogus", encoding="utf-8")
                            bogus_yaml.write_text("source_product_id: bogus_product\n", encoding="utf-8")

                        manifest_path.write_text(
                            yaml.safe_dump(
                                {
                                    "schema_version": "swiss_public_geodata_cache_manifest_template_v1",
                                    "candidate_site_id": SITE_ID,
                                    "candidate_site_name": "Demo Site",
                                    "products": [product_row],
                                },
                                sort_keys=False,
                            ),
                            encoding="utf-8",
                        )

                        report = stager.stage_public_geodata_cache(manifest_path)
                        verification_report = verifier.PREFLIGHT.verify_public_geodata_cache(manifest_path)
                    finally:
                        stager.PREFLIGHT.ROOT = original_stage_root
                        verifier.PREFLIGHT.ROOT = original_verify_root

                self.assertEqual(report["staging_status"], expected_status)
                self.assertEqual(report["products"][0]["staging_status"], expected_status)
                self.assertEqual(verification_report["verification_status"], expected_status)

    def _write_verified_inputs(self, root: Path) -> tuple[Path, Path, Path, Path]:
        terrain_path = root / SITE_ROOT_RELATIVE / "input" / "terrain.asc"
        terrain_metadata_path = root / SITE_ROOT_RELATIVE / "input" / "terrain_metadata.yaml"
        context_path = root / SITE_ROOT_RELATIVE / "context" / "swisstlm3d.bin"
        context_metadata_path = root / SITE_ROOT_RELATIVE / "context" / "swisstlm3d" / "metadata.json"
        terrain_path.parent.mkdir(parents=True, exist_ok=True)
        context_metadata_path.parent.mkdir(parents=True, exist_ok=True)
        terrain_path.write_text("terrain-bytes\n", encoding="utf-8")
        context_path.write_text("context-bytes\n", encoding="utf-8")

        terrain_checksum = stager.PREFLIGHT.sha256_path(terrain_path)
        context_checksum = stager.PREFLIGHT.sha256_path(context_path)
        terrain_metadata = {
            "source_product_id": "swissalti3d_2m",
            "source_product_name": "swissALTI3D",
            "source_url_or_download_record": "https://example.invalid/swissalti3d",
            "product_version_or_date": "2026.1",
            "tile_id_or_delivery_identifier": "2793-1180",
            "crs": "EPSG:2056",
            "resolution_m": 2.0,
            "crop_extent_lv95_m": {"xmin": 2793000.0, "ymin": 1180200.0, "xmax": 2793008.0, "ymax": 1180208.0},
            "license_or_terms_reference": "example terms",
            "raw_checksum": terrain_checksum,
            "processed_checksum": terrain_checksum,
            "preprocessing_command_and_timestamp": "manual fixture staging",
        }
        context_metadata = {
            "source_product_id": "swisstlm3d",
            "source_product_name": "swissTLM3D",
            "source_url_or_download_record": "https://example.invalid/swisstlm3d",
            "product_version_or_date": "2026.1",
            "tile_id_or_delivery_identifier": "tile-1",
            "crs": "EPSG:2056",
            "resolution_m": 1.0,
            "crop_extent_lv95_m": {"xmin": 2793000.0, "ymin": 1180200.0, "xmax": 2793008.0, "ymax": 1180208.0},
            "license_or_terms_reference": "example terms",
            "raw_checksum": context_checksum,
            "processed_checksum": context_checksum,
            "preprocessing_command_and_timestamp": "manual fixture staging",
        }
        terrain_metadata_path.write_text(yaml.safe_dump(terrain_metadata, sort_keys=False), encoding="utf-8")
        context_metadata_path.write_text(json.dumps(context_metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return terrain_path, terrain_metadata_path, context_path, context_metadata_path

    def _write_wizard_inputs(self, root: Path) -> tuple[Path, Path, Path, Path, Path]:
        terrain_path = root / SITE_ROOT_RELATIVE / "input" / "terrain.asc"
        terrain_metadata_path = root / SITE_ROOT_RELATIVE / "input" / "terrain_metadata.yaml"
        context_dir = root / SITE_ROOT_RELATIVE / "context" / "swisstlm3d"
        terrain_path.parent.mkdir(parents=True, exist_ok=True)
        context_dir.mkdir(parents=True, exist_ok=True)
        terrain_path.write_text("terrain-bytes\n", encoding="utf-8")
        terrain_checksum = stager.PREFLIGHT.sha256_path(terrain_path)
        terrain_metadata = {
            "source_product_id": "swissalti3d_2m",
            "source_product_name": "swissALTI3D",
            "source_url_or_download_record": "https://example.invalid/swissalti3d",
            "product_version_or_date": "2026.1",
            "tile_id_or_delivery_identifier": "2793-1180",
            "crs": "EPSG:2056",
            "resolution_m": 2.0,
            "crop_extent_lv95_m": {"xmin": 2793000.0, "ymin": 1180200.0, "xmax": 2793008.0, "ymax": 1180208.0},
            "license_or_terms_reference": "example terms",
            "raw_checksum": terrain_checksum,
            "processed_checksum": terrain_checksum,
            "preprocessing_command_and_timestamp": "manual fixture staging",
        }
        terrain_metadata_path.write_text(yaml.safe_dump(terrain_metadata, sort_keys=False), encoding="utf-8")
        context_path = context_dir / "swisstlm3d.bin"
        context_path.write_text("context-bytes\n", encoding="utf-8")
        context_metadata = {
            "source_product_id": "swisstlm3d",
            "source_product_name": "swissTLM3D",
            "source_url_or_download_record": "https://example.invalid/swisstlm3d",
            "product_version_or_date": "2026.1",
            "tile_id_or_delivery_identifier": "tile-1",
            "crs": "EPSG:2056",
            "resolution_m": 1.0,
            "crop_extent_lv95_m": {"xmin": 2793000.0, "ymin": 1180200.0, "xmax": 2793008.0, "ymax": 1180208.0},
            "license_or_terms_reference": "example terms",
            "raw_checksum": stager.PREFLIGHT.sha256_path(context_path),
            "processed_checksum": stager.PREFLIGHT.sha256_path(context_path),
            "preprocessing_command_and_timestamp": "manual fixture staging",
        }
        (context_dir / "metadata.json").write_text(json.dumps(context_metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return terrain_path, terrain_metadata_path, context_path, context_dir / "metadata.json", context_dir

    def _write_missing_inputs(self, root: Path) -> None:
        (root / SITE_ROOT_RELATIVE / "input").mkdir(parents=True, exist_ok=True)

    def _write_checksum_mismatch_inputs(self, root: Path) -> None:
        terrain_path = root / SITE_ROOT_RELATIVE / "input" / "terrain.asc"
        terrain_metadata_path = root / SITE_ROOT_RELATIVE / "input" / "terrain_metadata.yaml"
        terrain_path.parent.mkdir(parents=True, exist_ok=True)
        terrain_path.write_text("actual-bytes\n", encoding="utf-8")
        metadata = self._base_terrain_metadata(terrain_path)
        metadata["checksum_sha256"] = "0" * 64
        terrain_metadata_path.write_text(yaml.safe_dump(metadata, sort_keys=False), encoding="utf-8")

    def _write_metadata_mismatch_inputs(self, root: Path) -> None:
        terrain_path = root / SITE_ROOT_RELATIVE / "input" / "terrain.asc"
        terrain_metadata_path = root / SITE_ROOT_RELATIVE / "input" / "terrain_metadata.yaml"
        terrain_path.parent.mkdir(parents=True, exist_ok=True)
        terrain_path.write_text("terrain-bytes\n", encoding="utf-8")
        metadata = self._base_terrain_metadata(terrain_path)
        metadata["crs"] = "EPSG:21781"
        terrain_metadata_path.write_text(yaml.safe_dump(metadata, sort_keys=False), encoding="utf-8")

    def _base_terrain_metadata(self, terrain_path: Path) -> dict[str, object]:
        checksum = stager.PREFLIGHT.sha256_path(terrain_path)
        return {
            "source_product_id": "swissalti3d_2m",
            "source_product_name": "swissALTI3D",
            "source_url_or_download_record": "https://example.invalid/swissalti3d",
            "product_version_or_date": "2026.1",
            "tile_id_or_delivery_identifier": "2793-1180",
            "crs": "EPSG:2056",
            "resolution_m": 2.0,
            "crop_extent_lv95_m": {"xmin": 2793000.0, "ymin": 1180200.0, "xmax": 2793008.0, "ymax": 1180208.0},
            "license_or_terms_reference": "example terms",
            "raw_checksum": checksum,
            "processed_checksum": checksum,
            "preprocessing_command_and_timestamp": "manual fixture staging",
        }

    def _terrain_product_row(
        self,
        repo_root: Path,
        terrain_path: Path | None,
        terrain_metadata_path: Path | None,
        *,
        staged_exists: bool = True,
    ) -> dict[str, object]:
        row = {
            "category": "terrain_crop",
            "product_id": "terrain_crop",
            "source_product_id": "swissalti3d_2m",
            "source_product_name": "swissALTI3D",
            "source_url_or_download_record": "https://example.invalid/swissalti3d",
            "product_version_or_date": "2026.1",
            "tile_id_or_delivery_identifier": "2793-1180",
            "checksum_sha256": "",
            "crs": "EPSG:2056",
            "resolution_m": 2.0,
            "crop_extent_lv95_m": {"xmin": 2793000.0, "ymin": 1180200.0, "xmax": 2793008.0, "ymax": 1180208.0},
            "license_or_terms_reference": "example terms",
            "raw_checksum": "",
            "processed_checksum": "",
            "preprocessing_command_and_timestamp": "manual fixture staging",
            "required": True,
            "staged_path": str(terrain_path.relative_to(repo_root)) if terrain_path is not None else str(SITE_ROOT_RELATIVE / "input" / "terrain.asc"),
            "metadata_path": str(terrain_metadata_path.relative_to(repo_root)) if terrain_metadata_path is not None else str(SITE_ROOT_RELATIVE / "input" / "terrain_metadata.yaml"),
        }
        if terrain_path is not None and staged_exists:
            checksum = stager.PREFLIGHT.sha256_path(terrain_path)
            row["checksum_sha256"] = checksum
            row["raw_checksum"] = checksum
            row["processed_checksum"] = checksum
        return row

    def _terrain_product_row_with_checksum_mismatch(self) -> dict[str, object]:
        row = self._terrain_product_row(Path("/"), Path("/tmp/terrain.asc"), Path("/tmp/terrain_metadata.yaml"))
        row["staged_path"] = str(SITE_ROOT_RELATIVE / "input" / "terrain.asc")
        row["metadata_path"] = str(SITE_ROOT_RELATIVE / "input" / "terrain_metadata.yaml")
        row["checksum_sha256"] = "0" * 64
        return row

    def _terrain_product_row_with_metadata_mismatch(self) -> dict[str, object]:
        row = self._terrain_product_row(Path("/"), Path("/tmp/terrain.asc"), Path("/tmp/terrain_metadata.yaml"))
        row["staged_path"] = str(SITE_ROOT_RELATIVE / "input" / "terrain.asc")
        row["metadata_path"] = str(SITE_ROOT_RELATIVE / "input" / "terrain_metadata.yaml")
        return row

    def _context_product_row(self, repo_root: Path, context_path: Path, context_metadata_path: Path) -> dict[str, object]:
        checksum = stager.PREFLIGHT.sha256_path(context_path)
        return {
            "category": "swisstlm3d_context",
            "product_id": "swisstlm3d_context",
            "source_product_id": "swisstlm3d",
            "source_product_name": "swissTLM3D",
            "source_url_or_download_record": "https://example.invalid/swisstlm3d",
            "product_version_or_date": "2026.1",
            "tile_id_or_delivery_identifier": "tile-1",
            "checksum_sha256": checksum,
            "crs": "EPSG:2056",
            "resolution_m": 1.0,
            "crop_extent_lv95_m": {"xmin": 2793000.0, "ymin": 1180200.0, "xmax": 2793008.0, "ymax": 1180208.0},
            "license_or_terms_reference": "example terms",
            "raw_checksum": checksum,
            "processed_checksum": checksum,
            "preprocessing_command_and_timestamp": "manual fixture staging",
            "required": True,
            "staged_path": str(context_path.relative_to(repo_root)),
            "metadata_path": str(context_metadata_path.relative_to(repo_root)),
        }

    def _optional_barrier_row(self, root: Path) -> dict[str, object]:
        return {
            "category": "barrier_inventory",
            "product_id": "barrier_inventory",
            "source_product_id": "barrier_inventory",
            "source_product_name": "barrier inventory",
            "source_url_or_download_record": "https://example.invalid/barriers",
            "product_version_or_date": "2026.1",
            "tile_id_or_delivery_identifier": "barrier-1",
            "checksum_sha256": "",
            "crs": "EPSG:2056",
            "resolution_m": 1.0,
            "crop_extent_lv95_m": {"xmin": 2793000.0, "ymin": 1180200.0, "xmax": 2793008.0, "ymax": 1180208.0},
            "license_or_terms_reference": "example terms",
            "raw_checksum": "",
            "processed_checksum": "",
            "preprocessing_command_and_timestamp": "manual fixture staging",
            "required": False,
            "staged_path": str(root / SITE_ROOT_RELATIVE / "context" / "barriers"),
            "metadata_path": str(root / SITE_ROOT_RELATIVE / "context" / "barriers" / "metadata.yaml"),
        }

    def _write_directory_bundle(self, bundle_root: Path) -> None:
        bundle_root.mkdir(parents=True, exist_ok=True)
        payload_path = bundle_root / "payload.bin"
        payload_path.write_text("bundle-bytes\n", encoding="utf-8")
        payload_checksum = stager.PREFLIGHT.sha256_path(payload_path)
        metadata = {
            "source_product_id": "swisstlm3d",
            "source_product_name": "swissTLM3D",
            "source_url_or_download_record": "https://example.invalid/swisstlm3d",
            "product_version_or_date": "2026.1",
            "tile_id_or_delivery_identifier": "tile-1",
            "crs": "EPSG:2056",
            "resolution_m": 1.0,
            "license_or_terms_reference": "example terms",
            "raw_checksum": payload_checksum,
            "processed_checksum": payload_checksum,
            "preprocessing_command_and_timestamp": "manual fixture staging",
        }
        (bundle_root / "metadata.json").write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
