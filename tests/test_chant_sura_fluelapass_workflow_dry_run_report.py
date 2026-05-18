from __future__ import annotations

import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "summarize_chant_sura_fluelapass_dry_run_report.py"
STAGING_SCRIPT_PATH = ROOT / "scripts" / "prepare_chant_sura_fluelapass_minimal_preflight_inputs.py"


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


reporter = _load_module(SCRIPT_PATH, "summarize_chant_sura_fluelapass_dry_run_report")
staging = _load_module(
    STAGING_SCRIPT_PATH,
    "prepare_chant_sura_fluelapass_minimal_preflight_inputs_for_chant_sura_workflow_report_test",
)


class ChantSuraFluelapassWorkflowDryRunReportTests(unittest.TestCase):
    def test_ready_fixture_path_is_ready_for_next_step_and_permission_gates_tiny_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            site_config = self._write_site_config(repo_root)
            staging.stage_minimal_inputs(
                repo_root=repo_root,
                site_config=site_config,
                fixture_root=ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_minimal_staging",
            )
            self._write_real_context_cache_manifest(repo_root)

            first = reporter.build_report(site_config, repo_root=repo_root)
            repeat = reporter.build_report(site_config, repo_root=repo_root)
            second = reporter.build_report(
                site_config,
                repo_root=repo_root,
                allow_tiny_ensemble_handoff=True,
                tiny_ensemble_note="explicitly permitted for dry-run handoff coverage",
            )

        self.assertEqual(first["workflow_classification"], "ready_for_next_step")
        self.assertEqual(second["workflow_classification"], "ready_for_next_step")
        self.assertEqual(first, repeat)
        self.assertEqual(first["public_context_readiness"]["real_context_readiness_gate_status"], "ready_for_real_context_acquisition")
        self.assertEqual(first["public_context_readiness"]["real_context_product_readiness"]["readiness_status"], "ready")
        self.assertEqual(first["aoi_preparation"]["case_skeleton_status"], "ready")
        self.assertEqual(first["release_candidate_generation"]["candidate_metrics_status"], "ready")
        self.assertEqual(first["scenario_generation"]["scenario_plan_status"], "ready")
        self.assertEqual(first["command_planning"]["command_plan_status"], "ready")
        self.assertEqual(first["tiny_bounded_ensemble_handoff"]["status"], "blocked_missing_permission")
        self.assertEqual(second["tiny_bounded_ensemble_handoff"]["status"], "ready")
        self.assertTrue(second["tiny_bounded_ensemble_handoff"]["permission_note"])
        self.assertFalse(first["operational_claims_allowed"])
        self.assertFalse(first["scale_up_authorized"])
        self.assertFalse(first["public_context_readiness"]["synthetic_core_inputs_are_public_context_evidence"])
        self.assertTrue(first["aoi_preparation"]["case_skeleton"]["claim_boundaries"]["operational_claims_allowed"] is False)
        self.assertTrue(first["workflow_steps"])
        self.assertEqual(
            [step["step_id"] for step in first["workflow_steps"]],
            [
                "public_context_readiness",
                "aoi_preparation",
                "release_candidate_generation",
                "scenario_generation",
                "command_planning",
                "tiny_bounded_ensemble_handoff",
            ],
        )
        self.assertEqual(first["blocked_missing_inputs"], [])
        self.assertIn("ready_for_next_step", first["ready_for_next_step"]["status"])

        text_report = reporter.render_text_report(first)
        self.assertEqual(text_report, reporter.render_text_report(first))
        self.assertIn("workflow_classification: ready_for_next_step", text_report)
        self.assertIn("public_context_readiness:", text_report)
        self.assertIn("real_context_product_readiness_status: ready", text_report)
        self.assertIn("tiny_bounded_ensemble_handoff:", text_report)
        self.assertIn("ready_for_next_step:", text_report)

    def test_missing_fixture_inputs_fail_closed_as_blocked_missing_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            site_config = self._write_site_config(repo_root)

            report = reporter.build_report(site_config, repo_root=repo_root)

        self.assertEqual(report["workflow_classification"], "blocked_missing_inputs")
        self.assertEqual(report["public_context_readiness"]["real_context_readiness_gate_status"], "blocked_missing_inputs")
        self.assertEqual(report["public_context_readiness"]["real_context_product_readiness"]["readiness_status"], "missing")
        self.assertEqual(report["aoi_preparation"]["case_skeleton_status"], "blocked_missing_inputs")
        self.assertEqual(report["release_candidate_generation"]["candidate_metrics_status"], "blocked_missing_inputs")
        self.assertEqual(report["scenario_generation"]["scenario_plan_status"], "blocked_missing_inputs")
        self.assertEqual(report["tiny_bounded_ensemble_handoff"]["status"], "blocked_missing_inputs")
        self.assertTrue(report["blocked_missing_inputs"])
        self.assertIn("missing", report["aoi_preparation"]["blocked_reason"])
        self.assertIn("blocked_missing_inputs", report["ready_for_next_step"]["status"])

    def _write_site_config(self, repo_root: Path) -> Path:
        config_source = ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml"
        config_data = yaml.safe_load(config_source.read_text(encoding="utf-8"))
        config_data["acquisition_manifest_path"] = str(
            ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_public_geodata_acquisition.yaml"
        )
        config_path = repo_root / "site_config.yaml"
        config_path.write_text(yaml.safe_dump(config_data, sort_keys=False), encoding="utf-8")
        return config_path

    def _write_real_context_cache_manifest(self, repo_root: Path) -> None:
        manifest_path = (
            repo_root
            / "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/public_geodata_cache_manifest.yaml"
        )
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        records = []
        product_ids = [
            "swissimage_context",
            "swisstlm3d_context",
            "swisssurface3d_context",
            "swisssurface3d_raster_context",
            "swissbuildings3d_context",
        ]
        for index, product_id in enumerate(product_ids, start=1):
            staged_path = manifest_path.parent / f"{product_id}.bin"
            metadata_path = manifest_path.parent / f"{product_id}.yaml"
            payload = f"expected-{product_id}".encode("utf-8")
            staged_path.write_bytes(payload)
            metadata = {
                "source_product_id": product_id,
                "source_product_name": product_id.replace("_", " "),
                "source_url_or_download_record": f"https://example.invalid/{product_id}",
                "product_version_or_date": "2026-05-17",
                "tile_id_or_delivery_identifier": f"tile-{index}",
                "checksum_sha256": hashlib.sha256(payload).hexdigest(),
                "crs": "EPSG:2056",
                "resolution_m": 1.0,
                "crop_extent_lv95_m": {"xmin": 1.0, "ymin": 2.0, "xmax": 3.0, "ymax": 4.0},
                "license_or_terms_reference": "example terms",
            }
            metadata_path.write_text(yaml.safe_dump(metadata, sort_keys=False), encoding="utf-8")
            records.append(
                {
                    "product_id": product_id,
                    "source_product_id": product_id,
                    "source_product_name": product_id.replace("_", " "),
                    "source_url_or_download_record": f"https://example.invalid/{product_id}",
                    "product_version_or_date": "2026-05-17",
                    "tile_id_or_delivery_identifier": f"tile-{index}",
                    "checksum_sha256": hashlib.sha256(payload).hexdigest(),
                    "crs": "EPSG:2056",
                    "resolution_m": 1.0,
                    "crop_extent_lv95_m": {"xmin": 1.0, "ymin": 2.0, "xmax": 3.0, "ymax": 4.0},
                    "license_or_terms_reference": "example terms",
                    "staged_path": str(staged_path),
                    "metadata_path": str(metadata_path),
                }
            )
        manifest = {
            "schema_version": "public_geodata_cache_verification_manifest_v1",
            "candidate_site_id": "chant_sura_fluelapass_portability_example_v1",
            "candidate_site_name": "Chant Sura / Flüelapass portability example",
            "products": records,
        }
        manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
