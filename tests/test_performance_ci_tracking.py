#!/usr/bin/env python3
"""Tests for CI performance tracking helpers."""

from __future__ import annotations

import csv
import tempfile
import unittest
from types import SimpleNamespace
from pathlib import Path

import scripts.performance_ci_tracking as perf_ci


class PerformanceCiTrackingTests(unittest.TestCase):
    def test_aggregate_summary_extracts_component_totals(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            summary_path = Path(tmp) / "summary.csv"
            self._write_summary(summary_path)
            aggregate = perf_ci.aggregate_summary_csv(summary_path)

        self.assertEqual(aggregate.run_count, 3)
        self.assertEqual(aggregate.validation_rows, 1)
        self.assertEqual(aggregate.hazard_rows, 2)
        self.assertAlmostEqual(aggregate.values["total_wall_seconds"], 21.0)
        self.assertAlmostEqual(aggregate.values["terrain_load_seconds"], 1.2)
        self.assertAlmostEqual(aggregate.values["release_generation_seconds"], 0.8)
        self.assertAlmostEqual(aggregate.values["simulation_seconds"], 6.0)
        self.assertAlmostEqual(aggregate.values["validation_output_write_seconds"], 2.0)
        self.assertAlmostEqual(aggregate.values["hazard_total_seconds"], 11.0)
        self.assertAlmostEqual(aggregate.values["hazard_accumulation_seconds"], 6.5)
        self.assertAlmostEqual(aggregate.values["hazard_output_write_seconds"], 1.0)
        self.assertAlmostEqual(aggregate.values["bounds_discovery_seconds"], 0.9)

    def test_build_deltas_handles_missing_baseline(self) -> None:
        deltas = perf_ci.build_deltas(
            {"total_wall_seconds": 10.0, "simulation_seconds": 5.0},
            {"total_wall_seconds": 8.0},
        )
        self.assertAlmostEqual(float(deltas["total_wall_seconds"]["delta"] or 0.0), 2.0)
        self.assertAlmostEqual(float(deltas["total_wall_seconds"]["percent"] or 0.0), 25.0)
        self.assertIsNone(deltas["simulation_seconds"]["baseline"])
        self.assertIsNone(deltas["simulation_seconds"]["delta"])
        self.assertIsNone(deltas["simulation_seconds"]["percent"])

    def test_compare_pr_treats_non_dict_baseline_as_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            summary_path = Path(tmp) / "summary.csv"
            self._write_summary(summary_path)
            output_json = Path(tmp) / "pr_compare.json"
            output_md = Path(tmp) / "pr_compare.md"
            args = SimpleNamespace(
                summary_csv=summary_path,
                baseline_url="https://example.invalid/perf/latest.json",
                sha="abc123",
                output_json=output_json,
                output_markdown=output_md,
            )
            # read_json_url returns None for unreachable URL; compare_pr must not raise
            ret = perf_ci.compare_pr(args)
            self.assertEqual(ret, 0)
            import json as _json
            result = _json.loads(output_json.read_text())
            self.assertFalse(result["baseline_available"])

    def test_render_pr_markdown_includes_component_rows(self) -> None:
        report = {
            "sha": "abc123",
            "run_count": 3,
            "validation_rows": 1,
            "hazard_rows": 2,
            "trajectory_count": 12,
            "impact_count": 4,
            "output_bytes": 1024,
            "baseline_available": True,
            "metrics": {key: 1.0 for key in perf_ci.METRICS},
            "deltas": {
                key: {"baseline": 1.0, "delta": 0.0, "percent": 0.0}
                for key in perf_ci.METRICS
            },
        }

        markdown = perf_ci.render_pr_markdown(report)
        self.assertIn("## Performance benchmark", markdown)
        self.assertIn("Simulation kernel", markdown)
        self.assertIn("Hazard accumulation", markdown)
        self.assertIn("Positive deltas mean slower runtime", markdown)

    def test_build_history_svg_contains_series_and_commits(self) -> None:
        history = [
            {
                "sha": "1111111",
                "commit_date": "2026-01-01T00:00:00Z",
                "metrics": {
                    "total_wall_seconds": 10.0,
                    "terrain_load_seconds": 1.0,
                    "release_generation_seconds": 1.0,
                    "simulation_seconds": 4.0,
                    "validation_output_write_seconds": 2.0,
                    "hazard_total_seconds": 1.0,
                    "hazard_accumulation_seconds": 1.5,
                    "hazard_output_write_seconds": 0.8,
                    "bounds_discovery_seconds": 0.2,
                },
            },
            {
                "sha": "2222222",
                "commit_date": "2026-01-02T00:00:00Z",
                "metrics": {
                    "total_wall_seconds": 9.0,
                    "terrain_load_seconds": 0.9,
                    "release_generation_seconds": 1.1,
                    "simulation_seconds": 3.5,
                    "validation_output_write_seconds": 2.2,
                    "hazard_total_seconds": 0.8,
                    "hazard_accumulation_seconds": 1.0,
                    "hazard_output_write_seconds": 0.7,
                    "bounds_discovery_seconds": 0.15,
                },
            },
        ]
        svg = perf_ci.build_history_svg(history)

        self.assertIn("<svg", svg)
        self.assertIn("rust_rockfall main benchmark trend", svg)
        self.assertIn("2222222", svg)
        self.assertIn("Simulation", svg)
        self.assertIn("polyline", svg)
        self.assertIn("<circle", svg)
        self.assertIn("1111111", svg)
        self.assertIn("2222222", svg)

    def test_read_json_url_returns_none_on_unreachable_url(self) -> None:
        result = perf_ci.read_json_url("https://example.invalid/perf/history.json")
        self.assertIsNone(result)

    def test_read_json_url_rejects_non_https_url(self) -> None:
        with self.assertRaisesRegex(
            ValueError, "performance tracking URLs must be HTTPS URLs"
        ):
            perf_ci.read_json_url("http://example.com/perf/history.json")

    def test_record_main_rejects_non_positive_max_points(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            summary_path = Path(tmp) / "summary.csv"
            self._write_summary(summary_path)
            args = SimpleNamespace(
                summary_csv=summary_path,
                history_url="https://example.invalid/perf/history.json",
                commit_sha="abc",
                commit_date="2026-05-09T00:00:00Z",
                history_out=Path(tmp) / "history.json",
                latest_out=Path(tmp) / "latest.json",
                chart_out=Path(tmp) / "chart.svg",
                index_out=Path(tmp) / "index.html",
                max_points=0,
            )
            with self.assertRaisesRegex(ValueError, "max-points must be positive"):
                perf_ci.record_main(args)

    def test_record_main_writes_performance_page_and_site_root_index(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            summary_path = Path(tmp) / "summary.csv"
            self._write_summary(summary_path)
            site_root = Path(tmp) / "site"
            args = SimpleNamespace(
                summary_csv=summary_path,
                history_url="https://example.invalid/perf/history.json",
                commit_sha="abc1234",
                commit_date="2026-05-25T00:00:00Z",
                history_out=site_root / "performance" / "history.json",
                latest_out=site_root / "performance" / "latest.json",
                chart_out=site_root / "performance" / "main_performance.svg",
                index_out=site_root / "performance" / "index.html",
                site_index_out=site_root / "index.html",
                max_points=180,
            )

            ret = perf_ci.record_main(args)

            self.assertEqual(ret, 0)
            self.assertTrue((site_root / "performance" / "latest.json").exists())
            self.assertTrue((site_root / "performance" / "index.html").exists())
            root_index = (site_root / "index.html").read_text(encoding="utf-8")
            self.assertIn("rust_rockfall CI performance", root_index)
            self.assertIn("url=performance/", root_index)
            self.assertIn("Open the performance dashboard", root_index)

    def test_balfrin_efficiency_report_keeps_ci_context_separate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            summary_path = Path(tmp) / "summary.csv"
            self._write_summary(summary_path)
            report = perf_ci.build_balfrin_efficiency_report(summary_csv=summary_path)

        self.assertEqual(report["schema_version"], "balfrin_efficiency_comparison_v1")
        self.assertEqual(report["current_task_id"], "TB-566")
        self.assertEqual(report["current_job_id"], "4367244")
        self.assertEqual(report["current_run"]["scheduler_elapsed_seconds"], 24.0)
        self.assertEqual(report["current_run"]["conditional_curve_rows"], 729600)
        self.assertIsNone(report["current_run"]["trajectory_count"])
        self.assertEqual(
            report["current_run"]["trajectory_count_status"],
            "not_recorded_in_preserved_balfrin_metrics",
        )
        deltas = {row["baseline_task_id"]: row for row in report["deltas_vs_current"]}
        self.assertEqual(deltas["TB-448"]["scheduler_elapsed_seconds_delta"], 0.0)
        self.assertEqual(deltas["TB-557"]["scheduler_elapsed_seconds_delta"], -65.0)
        self.assertEqual(deltas["TB-448"]["hazard_output_file_count_delta"], 4)
        self.assertEqual(report["projection_delta"]["scheduler_elapsed_seconds_delta"], -439.84)
        self.assertEqual(report["ci_standard_profile"]["status"], "measured_ci_standard_profile")
        self.assertEqual(report["ci_standard_profile"]["trajectory_count"], 12)
        self.assertEqual(report["ci_balfrin_separation"]["status"], "separate_contexts")
        self.assertFalse(report["claim_boundaries"]["benchmark_as_validation_claim_allowed"])

    def test_balfrin_efficiency_cli_writes_json_and_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            summary_path = Path(tmp) / "summary.csv"
            self._write_summary(summary_path)
            output_json = Path(tmp) / "balfrin_efficiency.json"
            output_markdown = Path(tmp) / "balfrin_efficiency.md"
            args = SimpleNamespace(
                summary_csv=summary_path,
                output_json=output_json,
                output_markdown=output_markdown,
            )

            ret = perf_ci.balfrin_efficiency(args)

            self.assertEqual(ret, 0)
            self.assertTrue(output_json.exists())
            self.assertTrue(output_markdown.exists())
            markdown = output_markdown.read_text(encoding="utf-8")
            self.assertIn("Balfrin Efficiency Comparison", markdown)
            self.assertIn("CI benchmark data is shown separately", markdown)
            self.assertIn("PYENV_VERSION=system uv run python scripts/performance_ci_tracking.py balfrin-efficiency", markdown)

    def _write_summary(self, path: Path) -> None:
        fieldnames = [
            "stage",
            "total_wall_seconds",
            "terrain_load_seconds",
            "release_generation_seconds",
            "simulation_seconds",
            "output_write_seconds",
            "accumulation_seconds",
            "core_output_write_seconds",
            "bounds_discovery_seconds",
            "trajectory_count",
            "impact_event_count",
            "output_bytes",
        ]
        rows = [
            {
                "stage": "validation",
                "total_wall_seconds": 10.0,
                "terrain_load_seconds": 1.2,
                "release_generation_seconds": 0.8,
                "simulation_seconds": 6.0,
                "output_write_seconds": 2.0,
                "accumulation_seconds": "",
                "core_output_write_seconds": "",
                "bounds_discovery_seconds": "",
                "trajectory_count": 4,
                "impact_event_count": 2,
                "output_bytes": 500,
            },
            {
                "stage": "hazard_explicit_no_plots",
                "total_wall_seconds": 7.0,
                "terrain_load_seconds": "",
                "release_generation_seconds": "",
                "simulation_seconds": "",
                "output_write_seconds": 0.6,
                "accumulation_seconds": 4.0,
                "core_output_write_seconds": 0.6,
                "bounds_discovery_seconds": 0.0,
                "trajectory_count": 4,
                "impact_event_count": 1,
                "output_bytes": 250,
            },
            {
                "stage": "hazard_auto_no_plots",
                "total_wall_seconds": 4.0,
                "terrain_load_seconds": "",
                "release_generation_seconds": "",
                "simulation_seconds": "",
                "output_write_seconds": 0.4,
                "accumulation_seconds": 2.5,
                "core_output_write_seconds": 0.4,
                "bounds_discovery_seconds": 0.9,
                "trajectory_count": 4,
                "impact_event_count": 1,
                "output_bytes": 274,
            },
        ]
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)


if __name__ == "__main__":
    unittest.main()
