from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "audit_balfrin_run_root_output_budget.py"
SPEC = importlib.util.spec_from_file_location("audit_balfrin_run_root_output_budget", SCRIPT_PATH)
assert SPEC is not None
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class BalfrinRunRootOutputBudgetAuditTests(unittest.TestCase):
    def _write_json(self, path: Path, payload: dict[str, object]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def _write_text(self, path: Path, text: str = "fixture\n") -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def _build_run_root(
        self,
        root: Path,
        *,
        oversized: bool = False,
        incomplete: bool = False,
    ) -> Path:
        run_root = root / "run_root"
        output = run_root / "output"
        self._write_text(run_root / "probe_manifest.yaml", "probe: fixture\n")
        self._write_json(
            run_root / "command_plan.json",
            {
                "input": "probe_manifest.yaml",
                "commands": [
                    {
                        "name": "build_conditional_hazard_layers",
                        "cwd": ".",
                        "command": ["python", "scripts/build_hazard_layers.py", "--output-dir", "output"],
                    }
                ],
            },
        )

        outputs = [
            ("trajectory_csv", "trajectory.csv"),
            ("deposition_csv", "deposition.csv"),
            ("impact_events_csv", "impacts.csv"),
            ("trajectory_chunk_manifest", "trajectory_chunks/chunk_0000_manifest.json"),
            ("reducer_chunk_manifest", "chunks/chunk_0000_manifest.json"),
            ("reducer_chunk_manifest", "chunks/chunk_0001_manifest.json"),
            ("trajectory_execution_plan", "trajectory_execution_plan_v1.json"),
            ("trajectory_execution_index", "trajectory_execution_index_v1.json"),
            ("trajectory_merge_state", "trajectory_merge_state_v1.json"),
            ("reducer_execution_plan", "reducer_execution_plan_v1.json"),
            ("reducer_execution_index", "reducer_execution_index_v1.json"),
            ("reducer_merge_state", "reducer_merge_state_v1.json"),
            ("map_package_manifest", "map_package_manifest.json"),
            ("pilot_gis_package_manifest", "pilot_gis_package_manifest.json"),
        ]
        if incomplete:
            outputs = [item for item in outputs if item[0] not in {"impact_events_csv", "reducer_merge_state"}]
        if oversized:
            outputs.extend(("trajectory_csv", f"trajectory_extra_{index:02d}.csv") for index in range(4))

        for family, relative in outputs:
            path = output / relative
            if relative.endswith(".json"):
                self._write_json(path, {"family": family, "relative_path": relative})
            else:
                self._write_text(path, f"{family}\n")

        self._write_json(
            output / "validation_balfrin_probe_manifest.json",
            {
                "schema_version": "run_manifest_v1",
                "outputs": [{"kind": family, "path": relative} for family, relative in outputs],
            },
        )
        self._write_text(run_root / "balfrin_probe_metrics.json", "{}\n")
        return run_root

    def test_compliant_run_root_passes_budget_audit(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            run_root = self._build_run_root(Path(tmpdir))

            report = MODULE.build_report(run_root)

        self.assertEqual(report["schema_version"], "balfrin_run_root_output_budget_audit_v1")
        self.assertEqual(report["audit_status"], "compliant")
        self.assertEqual(report["budget_acceptance"]["status"], "accepted")
        self.assertEqual(report["projection"]["reducer_chunk_count"], 2)
        self.assertEqual(report["projection"]["sidecar_file_count"], 9)
        self.assertEqual(report["per_family"]["trajectory_csv"]["file_count"], 1)
        self.assertEqual(report["missing_replay_critical_artifacts"], [])
        self.assertEqual(report["missing_required_hashes"], [])
        self.assertEqual(len(report["hashes"]["command_plan_sha256"]["sha256"]), 64)
        self.assertIn("compliant", MODULE.render_text_report(report))

    def test_oversized_run_root_blocks_on_budget_thresholds(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            run_root = self._build_run_root(Path(tmpdir), oversized=True)

            report = MODULE.build_report(run_root)

        self.assertEqual(report["audit_status"], "blocked_budget_exceeded")
        self.assertEqual(report["budget_acceptance"]["status"], "blocked_threshold_exceeded")
        self.assertIn("output_family_file_count", report["budget_acceptance"]["exceeded_thresholds"])
        self.assertGreater(report["projection"]["output_family_file_counts"]["trajectory_csv"], 2)

    def test_incomplete_run_root_reports_missing_replay_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            run_root = self._build_run_root(Path(tmpdir), incomplete=True)
            (run_root / "probe_manifest.yaml").unlink()

            report = MODULE.build_report(run_root)

        self.assertEqual(report["audit_status"], "blocked_missing_replay_artifacts")
        self.assertIn("impact_events_csv", report["missing_replay_critical_artifacts"])
        self.assertIn("reducer_merge_state", report["missing_replay_critical_artifacts"])
        self.assertIn("probe_manifest_sha256", report["missing_required_hashes"])

    def test_missing_run_root_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            run_root = Path(tmpdir) / "missing"

            report = MODULE.build_report(run_root)

        self.assertEqual(report["audit_status"], "blocked_missing_run_root")
        self.assertEqual(report["projection"]["output_file_count"], 0)
        self.assertIn("run root does not exist", report["blocked_reasons"][0])


if __name__ == "__main__":
    unittest.main()
