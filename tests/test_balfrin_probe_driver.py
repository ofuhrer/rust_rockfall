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

    def test_collect_probe_metrics_parses_synthetic_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            run_root = Path(tmpdir) / "run"
            output_root = run_root / "hazard_output"
            command_plan_path = run_root / "command_plan.json"
            (output_root / "trajectory_chunks").mkdir(parents=True, exist_ok=True)
            (output_root / "chunks").mkdir(parents=True, exist_ok=True)

            _make_json_file(
                command_plan_path,
                {
                    "commands": [
                        {
                            "name": "build_conditional_hazard_layers",
                            "command": [
                                "python3",
                                "build_hazard_layers.py",
                                "--output-dir",
                                "hazard_output",
                            ],
                            "cwd": str(run_root),
                        }
                    ]
                },
            )

            _make_json_file(
                output_root / "validation_probe_manifest.json",
                {
                    "performance": {
                        "total_wall_seconds": 12.34,
                        "output_bytes": 4321,
                        "output_file_count": 7,
                        "output_write_seconds": 3.21,
                    },
                    "conditional_execution": {
                        "output_budget": {"output_bytes": 4321, "output_file_count": 7},
                        "trajectory_generation": {"plan_id": "trajectory_plan_a"},
                        "reducer": {"trajectory_execution_plan_id": "reducer_plan_a"},
                    },
                    "git_hash": "abc123",
                },
            )
            _make_json_file(
                output_root / "validation_probe_scaling_summary.json",
                {
                    "performance": {
                        "output_write_kind_seconds": {"geotiff": 0.4, "esri_ascii_grid": 0.1},
                        "output_write_kind_bytes": {"geotiff": 1000, "esri_ascii_grid": 2000},
                    }
                },
            )

            _make_json_file(
                output_root / "trajectory_chunks" / "chunk_0000_manifest.json",
                {"orchestration_decision": "reused_completed_state"},
            )
            _make_json_file(
                output_root / "trajectory_chunks" / "chunk_0001_manifest.json",
                {"orchestration_decision": "executed"},
            )
            _make_json_file(
                output_root / "chunks" / "chunk_0000_manifest.json",
                {"orchestration_decision": "executed"},
            )

            _make_json_file(
                output_root / "probe_execution_plan_v1.json",
                {"plan_id": "reducer_plan_file_a"},
            )
            _make_json_file(
                output_root / "probe_trajectory_execution_plan_v1.json",
                {"plan_id": "trajectory_plan_file_a"},
            )

            summary = collect_driver.collect_run_metrics(run_root)

        self.assertEqual(summary["output_root"], str(output_root.resolve()))
        self.assertEqual(summary["output_bytes"], 4321)
        self.assertEqual(summary["output_file_count"], 7)
        self.assertEqual(summary["output_write_seconds"], 3.21)
        self.assertEqual(summary["total_wall_seconds"], 12.34)
        self.assertEqual(summary["trajectory_plan_id"], "trajectory_plan_file_a")
        self.assertEqual(summary["reducer_plan_id"], "reducer_plan_file_a")
        self.assertEqual(
            summary["trajectory_decision_counts"],
            {"reused_completed_state": 1, "executed": 1},
        )
        self.assertEqual(summary["reducer_decision_counts"], {"executed": 1})
        self.assertEqual(summary["output_write_kind_seconds"]["geotiff"], 0.4)

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
