from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/run_balfrin_diagnostic.py"


def load_module():
    spec = importlib.util.spec_from_file_location("run_balfrin_diagnostic", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MODULE = load_module()


class RunBalfrinDiagnosticTests(unittest.TestCase):
    def _args(self, tmp: Path) -> Namespace:
        return Namespace(
            action="prepare",
            release_zones=16,
            reducer_chunks=2,
            reducer_workers=2,
            manifest_mode="compact",
            output_family_mix="trajectory_csv,deposition_csv,impact_events_csv,trajectory_merge_state,reducer_merge_state",
            repo_root=ROOT,
            scratch_root=tmp,
            run_root=tmp / "diagnostics" / "diagnostic_16_zone_test",
            run_id="diagnostic_16_zone_test",
            partition="postproc",
            time="00:30:00",
            cpus_per_task=16,
            poll_seconds=0.01,
            monitor_timeout_seconds=0.0,
            slurm_timeout_seconds=1.0,
            format="json",
        )

    def test_prepare_writes_one_run_record_and_sbatch_for_actual_diagnostic_shape(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmpdir:
            args = self._args(Path(tmpdir))
            run_root = MODULE.resolve_run_root(args)

            record = MODULE.prepare(args, run_root)

            record_path = run_root / "run_record.json"
            sbatch_path = run_root / "diagnostic.sbatch"
            self.assertTrue(record_path.exists())
            self.assertTrue(sbatch_path.exists())
            persisted = json.loads(record_path.read_text(encoding="utf-8"))
            self.assertEqual(persisted["schema_version"], MODULE.SCHEMA_VERSION)
            self.assertEqual(persisted["diagnostic_shape"]["release_zone_count"], 16)
            self.assertEqual(persisted["diagnostic_shape"]["manifest_mode"], "compact")
            self.assertEqual(persisted["partition"], "postproc")
            self.assertEqual(persisted["status"], "prepared")
            self.assertEqual(record["paths"]["run_record"], str(record_path))
            sbatch = sbatch_path.read_text(encoding="utf-8")
            self.assertIn("--release-zone-count 16", sbatch)
            self.assertIn("--reducer-chunk-count 2", sbatch)
            self.assertIn("--manifest-mode compact", sbatch)
            self.assertIn("scripts/summarize_multi_zone_reducer_pressure.py", sbatch)
            self.assertNotIn("authorization-record", sbatch)
            self.assertNotIn("reviewed-handoff-package", sbatch)

    def test_run_root_must_stay_under_scratch_root(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmpdir:
            args = self._args(Path(tmpdir))
            outside = Path(tmpdir).parent / "outside_run_root"

            with self.assertRaises(ValueError):
                MODULE.validate_run_shape(args, outside)

    def test_sacct_parser_prefers_batch_terminal_state(self) -> None:
        stdout = "\n".join(
            [
                "JobID|JobName|Partition|State|ExitCode|Elapsed|MaxRSS|ReqCPUS|AllocCPUS",
                "123|rr-diag-16z|postproc|COMPLETED|0:0|00:00:10||16|16",
                "123.batch|batch||FAILED|1:0|00:00:09|100M|16|16",
            ]
        )

        records = MODULE.parse_sacct(stdout)

        self.assertEqual(records[0]["JobID"], "123")
        self.assertEqual(MODULE.terminal_sacct_state(records), "FAILED")

    def test_collect_promotes_pressure_report_into_single_run_record(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmpdir:
            args = self._args(Path(tmpdir))
            run_root = MODULE.resolve_run_root(args)
            MODULE.prepare(args, run_root)
            paths = MODULE.diagnostic_paths(run_root)
            paths["pressure_json"].write_text(
                json.dumps(
                    {
                        "probe_status": "measured_scratch_root",
                        "release_zone_count": 16,
                        "scenario_count": 48,
                        "manifest_size_bytes": 123,
                        "output_file_count": 10,
                        "output_byte_count": 456,
                        "root_file_count": 12,
                        "reducer_wall_time_seconds": 3.4,
                    }
                ),
                encoding="utf-8",
            )
            paths["time"].write_text(
                "Elapsed (wall clock) time (h:mm:ss or m:ss): 0:03.20\n"
                "Maximum resident set size (kbytes): 2048\n",
                encoding="utf-8",
            )

            record = MODULE.collect(args, run_root)

            self.assertEqual(record["collection"]["status"], "complete")
            self.assertEqual(record["collection"]["pressure_report"]["release_zone_count"], 16)
            self.assertEqual(record["collection"]["time_verbose"]["max_rss_mb"], 2.0)
            self.assertEqual(record["collection"]["time_verbose"]["elapsed"], "0:03.20")


if __name__ == "__main__":
    unittest.main()
