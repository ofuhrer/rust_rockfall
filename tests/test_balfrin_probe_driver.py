from __future__ import annotations

from dataclasses import dataclass
import importlib.util
import io
import json
import tempfile
import textwrap
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]

def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module {name} from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


submit_driver = _load_module(
    ROOT / "scripts/submit_balfrin_probe.py",
    "submit_balfrin_probe",
)
collect_driver = _load_module(
    ROOT / "scripts/collect_balfrin_probe_metrics.py",
    "collect_balfrin_probe_metrics",
)


def _make_json_file(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


class BalfrinProbeDriverTests(unittest.TestCase):
    def _write_manifest(self, path: Path) -> None:
        path.write_text(
            textwrap.dedent(
                """
            run_id: sbatch_smoke
            commands: []
            """
            ).strip()
            + "\n",
            encoding="utf-8",
        )

    def test_sbatch_script_contains_slurm_defaults_and_scratch_env(self) -> None:
        run_root = Path("/scratch/rust_rockfall/probes/scale-test/001")
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest = Path(tmpdir) / "manifest.yaml"
            self._write_manifest(manifest)

        script = submit_driver._build_sbatch_script(
            run_root=run_root,
            probe_manifest=manifest,
            partition="postproc",
            time_budget="00:30:00",
            nodes=1,
            ntasks=1,
            cpus_per_task=16,
        )

        lines = script.splitlines()
        first_sbatch_idx = next(i for i, line in enumerate(lines) if line.startswith("#SBATCH"))
        setu_index = lines.index("set -euo pipefail")
        self.assertEqual(lines[0], "#!/usr/bin/env bash")
        self.assertLess(first_sbatch_idx, setu_index)
        self.assertIn("export RUN_ROOT", script)
        self.assertIn("export REPO_ROOT", script)
        self.assertIn("python3 - <<'PY'", script)
        self.assertIn("#SBATCH --partition=postproc", script)
        self.assertIn("#SBATCH --time=00:30:00", script)
        self.assertIn("#SBATCH --nodes=1", script)
        self.assertIn("#SBATCH --ntasks=1", script)
        self.assertIn("#SBATCH --cpus-per-task=16", script)
        self.assertIn(
            "#SBATCH --output=/scratch/rust_rockfall/probes/scale-test/001/logs/slurm-%j.out",
            script,
        )
        self.assertIn(
            "#SBATCH --error=/scratch/rust_rockfall/probes/scale-test/001/logs/slurm-%j.err",
            script,
        )
        self.assertIn('export UV_CACHE_DIR="${UV_CACHE_DIR:-$SCRATCH/.cache/uv}"', script)
        self.assertIn('export CARGO_TARGET_DIR="${CARGO_TARGET_DIR:-$SCRATCH/rust_rockfall/target}"', script)
        self.assertIn('export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK:-1}"', script)
        self.assertNotIn("--account", script)
        self.assertNotIn("s83opr", script)
        self.assertNotIn("gpu", script.lower())
        self.assertNotIn(f'"{submit_driver.ROOT.as_posix()}"', script)
        self.assertIn('git_hash="$(git -C "$REPO_ROOT" rev-parse HEAD)"', script)

    def test_dry_run_output_is_deterministic(self) -> None:
        fake_plan = ({"run_id": "probe_fixed", "commands": []}, "probe_fixed")
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest = Path(tmpdir) / "manifest.yaml"
            self._write_manifest(manifest)

            with patch.object(submit_driver, "_read_command_plan", return_value=fake_plan):
                buf1 = io.StringIO()
                with redirect_stdout(buf1):
                    submit_driver.main(
                        [
                            str(manifest),
                            "--dry-run",
                            "--run-root",
                            f"{tmpdir}/run-root",
                            "--run-id",
                            "run-fixed",
                            "--partition",
                            "postproc",
                        ]
                    )
                out1 = buf1.getvalue()

                buf2 = io.StringIO()
                with redirect_stdout(buf2):
                    submit_driver.main(
                        [
                            str(manifest),
                            "--dry-run",
                            "--run-root",
                            f"{tmpdir}/run-root",
                            "--run-id",
                            "run-fixed",
                            "--partition",
                            "postproc",
                        ]
                    )
                out2 = buf2.getvalue()

        self.assertEqual(out1, out2)
        self.assertIn("run_root=", out1)
        self.assertIn("probe.sbatch", out1)

    def test_submission_package_report_collects_expected_roots(self) -> None:
        fake_readiness = type(
            "_Readiness",
            (),
            {
                "collect_readiness_report": staticmethod(
                    lambda **_kwargs: {
                        "status": "ready_for_balfrin_target_gate",
                        "branch": "main",
                        "commit": "abc123",
                        "blocking_checks": [],
                        "checks": [{"name": "tool.rustc", "status": "pass", "required": True, "message": "ok", "path": None}],
                    }
                )
            },
        )()
        command_plan = {
            "commands": [
                {
                    "name": "build_conditional_hazard_layers",
                    "command": [
                        "python3",
                        "scripts/build_hazard_layers.py",
                        "--output-dir",
                        "hazard/results/tschamut_public_pilot/target_gate_v1",
                        "--diagnostics",
                        "validation/private/tschamut_public_pilot/target_gate_v1/metrics.json",
                        "--trajectory",
                        "validation/private/tschamut_public_pilot/target_gate_v1/trajectory.csv",
                        "--ensemble-trajectories-dir",
                        "validation/private/tschamut_public_pilot/target_gate_v1/trajectories",
                        "--deposition",
                        "validation/private/tschamut_public_pilot/target_gate_v1/deposition.csv",
                        "--ensemble-impact-events-dir",
                        "validation/private/tschamut_public_pilot/target_gate_v1/impacts",
                        "--map-package-manifest-json",
                        "hazard/results/tschamut_public_pilot/target_gate_v1/map_package_manifest.json",
                        "--pilot-gis-package-manifest-json",
                        "hazard/results/tschamut_public_pilot/target_gate_v1/pilot_gis_package_manifest.json",
                    ],
                }
            ]
        }
        run_root = Path("/scratch/rust_rockfall/probes/scale-test/001")
        with patch.object(submit_driver, "_load_readiness_checker", return_value=fake_readiness):
            with patch.object(submit_driver, "_git_info", return_value={"branch": "main", "commit": "abc123"}):
                package = submit_driver._build_submission_package_report(
                    run_root=run_root,
                    probe_manifest=Path("validation/pilot_runs/probe.yaml"),
                    command_plan=command_plan,
                    partition="postproc",
                    time_budget="00:30:00",
                    nodes=1,
                    ntasks=1,
                    cpus_per_task=16,
                )

        self.assertEqual(package["schema_version"], "balfrin_submission_package_v1")
        self.assertEqual(package["repository"]["commit"], "abc123")
        self.assertEqual(package["generated_output_roots"], [str(run_root.resolve()), str((run_root / "logs").resolve())])
        self.assertEqual(
            package["ignored_output_roots"],
            [
                str((ROOT / "hazard/results/tschamut_public_pilot/target_gate_v1").resolve()),
                str((ROOT / "validation/private/tschamut_public_pilot/target_gate_v1").resolve()),
            ],
        )
        self.assertIn(
            f"PYENV_VERSION=system uv run python scripts/submit_balfrin_probe.py --collect --run-root {run_root}",
            package["collection_instructions"],
        )
        self.assertIn(str(run_root / "probe.sbatch"), package["expected_outputs"])

    def test_generate_only_writes_submission_package_without_submitting(self) -> None:
        fake_plan = ({"run_id": "probe_fixed", "commands": []}, "probe_fixed")
        fake_package = {
            "schema_version": "balfrin_submission_package_v1",
            "package_mode": "generate-only",
            "probe_manifest": "validation/pilot_runs/probe.yaml",
            "run_root": "/scratch/rust_rockfall/probes/scale-test/001",
            "repository": {"repo_root": str(ROOT), "branch": "main", "commit": "abc123"},
            "slurm": {
                "partition": "postproc",
                "time": "00:30:00",
                "nodes": 1,
                "ntasks": 1,
                "cpus_per_task": 16,
            },
            "scratch_paths": {
                "scratch_root": "/scratch",
                "uv_cache_dir": "/scratch/.cache/uv",
                "cargo_target_dir": "/scratch/rust_rockfall/target",
            },
            "input_checks": {"status": "ready", "blocking_checks": [], "checks": []},
            "command_plan_path": "/scratch/rust_rockfall/probes/scale-test/001/command_plan.json",
            "sbatch_script_path": "/scratch/rust_rockfall/probes/scale-test/001/probe.sbatch",
            "generated_output_roots": ["/scratch/rust_rockfall/probes/scale-test/001"],
            "ignored_output_roots": [],
            "expected_outputs": [
                "/scratch/rust_rockfall/probes/scale-test/001/command_plan.json",
                "/scratch/rust_rockfall/probes/scale-test/001/probe.sbatch",
                "/scratch/rust_rockfall/probes/scale-test/001/balfrin_submission_package.json",
                "/scratch/rust_rockfall/probes/scale-test/001/balfrin_submission_package.md",
                "/scratch/rust_rockfall/probes/scale-test/001/logs",
            ],
            "collection_instructions": [],
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest = Path(tmpdir) / "manifest.yaml"
            self._write_manifest(manifest)
            run_root = Path(tmpdir) / "run-root"

            with patch.object(submit_driver, "_read_command_plan", return_value=fake_plan), patch.object(
                submit_driver,
                "_build_submission_package_report",
                return_value=fake_package,
            ), patch.object(submit_driver.subprocess, "run") as run_mock:
                buf = io.StringIO()
                with redirect_stdout(buf):
                    submit_driver.main(
                        [
                            str(manifest),
                            "--generate-only",
                            "--run-root",
                            str(run_root),
                            "--partition",
                            "postproc",
                        ]
                    )

                run_mock.assert_not_called()
                self.assertTrue((run_root / "command_plan.json").exists())
                self.assertTrue((run_root / "probe.sbatch").exists())
                self.assertTrue((run_root / "balfrin_submission_package.json").exists())
                self.assertTrue((run_root / "balfrin_submission_package.md").exists())
                self.assertEqual(
                    json.loads((run_root / "balfrin_submission_package.json").read_text(encoding="utf-8")),
                    fake_package,
                )
                self.assertIn("run_root=", buf.getvalue())

    def test_collect_probe_metrics_parses_synthetic_outputs(self) -> None:
        complete_root = ROOT / "tests/fixtures/balfrin_probe_metrics_contract/complete_run_root"
        summary = collect_driver.collect_run_metrics(complete_root)

        self.assertEqual(summary["output_root"], str((complete_root / "output").resolve()))
        self.assertEqual(summary["metrics_contract_status"], "complete")
        self.assertEqual(summary["metrics_contract_missing_metrics"], [])
        self.assertEqual(summary["memory_peak_mb"], 409.22)
        self.assertEqual(summary["validation_output_file_count"], 2005)
        self.assertEqual(summary["validation_output_bytes"], 571377719)
        self.assertEqual(summary["hazard_output_file_count"], 46)
        self.assertEqual(summary["hazard_output_bytes"], 16613900)
        self.assertEqual(summary["conditional_curve_row_count"], 729600)
        self.assertEqual(summary["reduced_output_family_counts"]["map_package_manifest"], 1)
        self.assertEqual(summary["reduced_output_family_counts"]["pilot_gis_package_manifest"], 1)
        self.assertEqual(summary["reduced_output_family_counts"]["trajectory_chunk_manifest"], 2)
        self.assertEqual(summary["reduced_output_family_counts"]["reducer_chunk_manifest"], 2)
        self.assertEqual(summary["trajectory_plan_id"], "validation_tschamut_public_target_gate_v1__trajectory_execution_plan__fixture")
        self.assertEqual(summary["reducer_plan_id"], "validation_tschamut_public_target_gate_v1__trajectory_execution_plan__fixture")
        self.assertEqual(
            summary["trajectory_decision_counts"],
            {"executed": 2},
        )
        self.assertEqual(summary["reducer_decision_counts"], {"executed": 2})
        self.assertEqual(summary["output_write_kind_seconds"]["geotiff"], 0.4)
        self.assertEqual(summary["output_write_kind_bytes"]["manifest_json"], 3400)
        self.assertEqual(
            summary["log_audit"],
            {
                "logs_root": str((complete_root / "logs").resolve()),
                "file_count": 2,
                "matched_line_count": 4,
                "warning_like_line_count": 2,
                "error_like_line_count": 2,
                "affected_log_paths": [
                    str((complete_root / "logs" / "nested" / "worker.log").resolve()),
                    str((complete_root / "logs" / "slurm-123.out").resolve()),
                ],
                "files": [
                    {
                        "path": str((complete_root / "logs" / "nested" / "worker.log").resolve()),
                        "matched_line_count": 2,
                        "warning_like_line_count": 1,
                        "error_like_line_count": 1,
                    },
                    {
                        "path": str((complete_root / "logs" / "slurm-123.out").resolve()),
                        "matched_line_count": 2,
                        "warning_like_line_count": 1,
                        "error_like_line_count": 1,
                    },
                ],
            },
        )

    def test_collect_probe_metrics_reports_blocked_incomplete_root(self) -> None:
        incomplete_root = ROOT / "tests/fixtures/balfrin_probe_metrics_contract/incomplete_run_root"
        summary = collect_driver.collect_run_metrics(incomplete_root)

        self.assertEqual(summary["metrics_contract_status"], "blocked_missing_inputs")
        self.assertIn("memory_peak_mb", summary["metrics_contract_missing_metrics"])
        self.assertIn("validation_output.file_count", summary["metrics_contract_missing_metrics"])
        self.assertIn("hazard_output.file_count", summary["metrics_contract_missing_metrics"])
        self.assertIn("conditional_curve_row_count", summary["metrics_contract_missing_metrics"])
        self.assertIn("reduced_output_family_counts", summary["metrics_contract_missing_metrics"])
        self.assertEqual(summary["reduced_output_family_counts"], {})
        self.assertEqual(summary["trajectory_plan_id"], None)
        self.assertEqual(summary["reducer_plan_id"], None)
        self.assertEqual(summary["trajectory_decision_counts"], {})
        self.assertEqual(summary["reducer_decision_counts"], {})
        self.assertEqual(
            summary["log_audit"],
            {
                "logs_root": str((incomplete_root / "logs").resolve()),
                "file_count": 1,
                "matched_line_count": 1,
                "warning_like_line_count": 1,
                "error_like_line_count": 0,
                "affected_log_paths": [str((incomplete_root / "logs" / "slurm-456.out").resolve())],
                "files": [
                    {
                        "path": str((incomplete_root / "logs" / "slurm-456.out").resolve()),
                        "matched_line_count": 1,
                        "warning_like_line_count": 1,
                        "error_like_line_count": 0,
                    }
                ],
            },
        )

    def test_local_command_plan_mode_prints_plan(self) -> None:
        fake_plan = {"run_status": "target_run_completed", "run_id": "local-plan", "commands": []}
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest = Path(tmpdir) / "manifest.yaml"
            self._write_manifest(manifest)

            with patch.object(
                submit_driver,
                "_read_command_plan",
                return_value=(fake_plan, "local-plan"),
            ):
                out = io.StringIO()
                with redirect_stdout(out):
                    submit_driver.main([str(manifest), "--local-command-plan"])
                content = out.getvalue()

        parsed = json.loads(content)
        self.assertEqual(parsed["run_id"], "local-plan")

    def test_collect_mode_works_without_python_module_path(self) -> None:
        @dataclass
        class _Collector:
            payload: dict

            def collect_run_metrics(self, *_args: object, **_kwargs: object) -> dict:
                return self.payload

        with tempfile.TemporaryDirectory() as tmpdir:
            run_root = Path(tmpdir) / "run"
            run_root.mkdir()
            payload = {"output_root": str(run_root)}
            collector = _Collector(payload)

            with patch.object(
                submit_driver,
                "_load_collect_script",
                return_value=collector,
            ):
                out = io.StringIO()
                with redirect_stdout(out):
                    submit_driver.main(["--collect", "--run-root", str(run_root)])

        self.assertEqual(json.loads(out.getvalue()), payload)


if __name__ == "__main__":
    unittest.main()
