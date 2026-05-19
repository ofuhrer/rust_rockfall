from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "generate_balfrin_postproc_microbenchmark_package.py"


def load_module():
    spec = importlib.util.spec_from_file_location("generate_balfrin_postproc_microbenchmark_package", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


MODULE = load_module()


class BalfrinPostprocMicrobenchmarkPackageTests(unittest.TestCase):
    def test_materialized_package_records_exact_bounded_shape(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_root = Path(tmpdir) / "package"
            config = MODULE.PackageConfig(
                package_id="fixture_postproc",
                file_count=5,
                manifest_size_bytes=4096,
                sidecar_count=3,
                reducer_chunk_count=2,
                payload_bytes=17,
            )

            package = MODULE.materialize_package(output_root, config=config)
            manifest_path = output_root / "balfrin_postproc_microbenchmark_package.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

            self.assertEqual(package["schema_version"], MODULE.SCHEMA_VERSION)
            self.assertEqual(manifest["schema_version"], MODULE.SCHEMA_VERSION)
            self.assertEqual(manifest["package_status"], "generated_no_live_execution")
            self.assertFalse(manifest["live_submission_authorized"])
            self.assertFalse(manifest["simulation_execution_included"])
            self.assertFalse(manifest["operational_claims_allowed"])
            self.assertEqual(manifest["config"]["file_count"], 5)
            self.assertEqual(manifest["config"]["sidecar_count"], 3)
            self.assertEqual(manifest["config"]["reducer_chunk_count"], 2)
            self.assertEqual(manifest["synthetic_inputs"]["data_files"]["count"], 5)
            self.assertEqual(manifest["synthetic_inputs"]["sidecars"]["count"], 3)
            self.assertEqual(manifest["synthetic_inputs"]["reducer_chunks"]["count"], 2)
            self.assertGreaterEqual(manifest["synthetic_inputs"]["synthetic_manifest"]["bytes"], 4096)
            self.assertIn("file_scan_seconds", manifest["measurement_plan"]["phase_metrics"])
            self.assertIn("peak_rss_kb", manifest["measurement_plan"]["resource_metrics"])
            self.assertIn("--package-root", manifest["measurement_plan"]["command"])
            self.assertTrue((output_root / "harness" / "run_balfrin_postproc_microbenchmark.py").exists())
            self.assertTrue((output_root / "README.md").exists())

    def test_generated_runner_measures_postproc_shell_overhead(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_root = Path(tmpdir) / "package"
            config = MODULE.PackageConfig(
                package_id="runner_fixture",
                file_count=4,
                manifest_size_bytes=2048,
                sidecar_count=2,
                reducer_chunk_count=3,
                payload_bytes=11,
            )
            MODULE.materialize_package(output_root, config=config)
            runner = output_root / "harness" / "run_balfrin_postproc_microbenchmark.py"
            output_json = output_root / "output" / "measurements.json"

            completed = subprocess.run(
                [sys.executable, str(runner), "--package-root", str(output_root), "--output-json", str(output_json)],
                check=True,
                text=True,
                capture_output=True,
            )
            report = json.loads(output_json.read_text(encoding="utf-8"))

            self.assertIn('"schema_version"', completed.stdout)
            self.assertEqual(report["schema_version"], MODULE.RUNNER_SCHEMA_VERSION)
            self.assertEqual(report["measurement_status"], "measured_postproc_shell_overhead")
            self.assertFalse(report["live_submission_authorized"])
            self.assertFalse(report["simulation_execution_included"])
            self.assertEqual(set(report["phase_seconds"]), {"file_scan_seconds", "manifest_scan_seconds", "reducer_merge_seconds", "package_seconds"})
            self.assertEqual(report["phase_results"]["file_scan"]["file_count"], 4)
            self.assertEqual(report["phase_results"]["manifest_scan"]["file_count"], 3)
            self.assertEqual(report["phase_results"]["reducer_merge"]["file_count"], 3)
            self.assertEqual(report["phase_results"]["package"]["file_count"], 1)
            self.assertGreater(report["files_touched"], 0)
            self.assertGreater(report["bytes_touched"], 0)
            self.assertIn("Synthetic post-processing microbenchmark", report["boundary_note"])

    def test_parser_rejects_non_positive_counts(self) -> None:
        with self.assertRaises(argparse.ArgumentTypeError):
            MODULE.positive_int("0")
        with self.assertRaises(argparse.ArgumentTypeError):
            MODULE.non_negative_int("-1")

    def test_existing_package_requires_force(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_root = Path(tmpdir) / "package"
            config = MODULE.PackageConfig(
                package_id="force_fixture",
                file_count=1,
                manifest_size_bytes=512,
                sidecar_count=0,
                reducer_chunk_count=1,
                payload_bytes=8,
            )
            MODULE.materialize_package(output_root, config=config)

            with self.assertRaisesRegex(MODULE.BalfrinPostprocMicrobenchmarkPackageError, "already exists"):
                MODULE.materialize_package(output_root, config=config)

            regenerated = MODULE.materialize_package(output_root, config=config, force=True)
            self.assertEqual(regenerated["package_id"], "force_fixture")


if __name__ == "__main__":
    unittest.main()
