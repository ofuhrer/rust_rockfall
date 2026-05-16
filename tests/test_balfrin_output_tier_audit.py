from __future__ import annotations

import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "summarize_balfrin_output_tier_audit.py"


def load_module():
    spec = importlib.util.spec_from_file_location("summarize_balfrin_output_tier_audit", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MODULE = load_module()


class BalfrinOutputTierAuditTests(unittest.TestCase):
    def test_complete_fixture_metrics_classify_as_fixture_backed_and_sufficient(self) -> None:
        report = MODULE.build_report(self.complete_metrics())

        self.assertEqual(report["schema_version"], "balfrin_output_tier_audit_v1")
        self.assertEqual(report["audit_status"], "fixture_backed")
        self.assertEqual(report["evidence_provenance_status"], "fixture_backed")
        self.assertEqual(report["source_provenance"]["status"], "fixture_backed")
        self.assertEqual(report["rebuildability_status"], "sufficient")
        self.assertEqual(report["rebuildability_classification"], "rebuildable_reduced_output")
        self.assertEqual(report["required_family_counts"], {
            "map_package_manifest": 1,
            "pilot_gis_package_manifest": 1,
            "trajectory_chunk_manifest": 1,
            "reducer_chunk_manifest": 1,
        })
        self.assertTrue(all(report["required_family_counts_status"].values()))
        self.assertEqual(report["file_counts"]["validation_output"]["file_count"], 2005)
        self.assertEqual(report["file_counts"]["validation_output"]["bytes"], 571377719)
        self.assertEqual(report["file_counts"]["hazard_output"]["file_count"], 46)
        self.assertEqual(report["curve_availability"]["row_count"], 729600)
        self.assertIn("preserves the required manifest and chunk families", report["omitted_output_implications"][0])
        self.assertFalse(report["claim_boundaries"]["scale_up_authorized"])

    def test_non_fixture_source_paths_classify_as_measured(self) -> None:
        evidence = self.complete_metrics()
        evidence.update(
            {
                "run_root": "/scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_single_release_zone_v3",
                "output_root": "/scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_single_release_zone_v3/output",
                "hazard_manifest_path": "/scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_single_release_zone_v3/output/validation_balfrin_probe_manifest.json",
                "probe_manifest_path": "/scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_single_release_zone_v3/probe_manifest.yaml",
                "command_plan_path": "/scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_single_release_zone_v3/command_plan.json",
            }
        )

        report = MODULE.build_report(evidence)

        self.assertEqual(report["audit_status"], "measured")
        self.assertEqual(report["evidence_provenance_status"], "measured")
        self.assertEqual(report["source_provenance"]["status"], "measured")
        self.assertIn(
            "/scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_single_release_zone_v3",
            report["source_provenance"]["paths"][0],
        )

    def test_missing_required_family_classifies_as_insufficient(self) -> None:
        evidence = self.complete_metrics()
        evidence["reduced_output_family_counts"] = {
            "map_package_manifest": 1,
            "pilot_gis_package_manifest": 1,
            "trajectory_chunk_manifest": 1,
        }

        report = MODULE.build_report(evidence)

        self.assertEqual(report["rebuildability_status"], "insufficient")
        self.assertEqual(report["rebuildability_classification"], "rebuildable_reduced_output_insufficient")
        self.assertIn("reducer_chunk_manifest", report["blocked_reasons"])
        self.assertFalse(report["required_family_counts_status"]["reducer_chunk_manifest"])
        self.assertIn("Required measured output families are omitted", report["omitted_output_implications"][0])

    def test_missing_measured_output_is_blocked(self) -> None:
        evidence = {
            "metrics_contract_status": "blocked_missing_inputs",
            "metrics_contract_missing_metrics": [
                "validation_output.file_count",
                "hazard_output.bytes",
                "conditional_curve_row_count",
            ],
        }

        report = MODULE.build_report(evidence)

        self.assertEqual(report["audit_status"], "blocked_missing_inputs")
        self.assertEqual(report["evidence_provenance_status"], "blocked_missing_inputs")
        self.assertEqual(report["rebuildability_status"], "blocked_missing_measured_output")
        self.assertEqual(report["rebuildability_classification"], "blocked_missing_measured_output")
        self.assertIn("validation_output.file_count", report["blocked_reasons"])
        self.assertIn("metrics contract is incomplete", report["omitted_output_implications"][0])
        self.assertEqual(report["curve_availability"]["row_count"], None)

    def test_cli_emits_json_and_text(self) -> None:
        evidence = self.complete_metrics()
        path = self.write_json(evidence)
        try:
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = MODULE.main(["--format", "text", "--evidence-json", str(path)])
            self.assertEqual(exit_code, 0)
            text = buffer.getvalue()
            self.assertIn("Balfrin Output-Tier Audit", text)
            self.assertIn("rebuildability_classification: rebuildable_reduced_output", text)
            self.assertIn("evidence_provenance_status:", text)

            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = MODULE.main(["--format", "json", "--evidence-json", str(path)])
            self.assertEqual(exit_code, 0)
            json.loads(buffer.getvalue())
        finally:
            path.unlink(missing_ok=True)

    def test_write_json_and_markdown(self) -> None:
        evidence = self.complete_metrics()
        report = MODULE.build_report(evidence)
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            json_path = tmp / "audit.json"
            md_path = tmp / "audit.md"
            MODULE.materialize_artifacts(report, output_json=json_path, output_md=md_path)
            self.assertTrue(json_path.exists())
            self.assertTrue(md_path.exists())
            self.assertIn("Balfrin Output-Tier Audit", md_path.read_text(encoding="utf-8"))

    def complete_metrics(self) -> dict[str, object]:
        fixture_root = ROOT / "tests/fixtures/balfrin_probe_metrics_contract/complete_run_root"
        return MODULE.probe_metrics.collect_run_metrics(fixture_root)

    def write_json(self, payload: dict[str, object]) -> Path:
        tmp = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
        with tmp:
            json.dump(payload, tmp, indent=2, sort_keys=True)
            tmp.write("\n")
        return Path(tmp.name)


if __name__ == "__main__":
    unittest.main()
