from __future__ import annotations

import importlib.util
import io
import json
import tempfile
import unittest
import sys
from contextlib import redirect_stdout
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "summarize_multi_zone_reducer_pressure.py"


def load_module():
    spec = importlib.util.spec_from_file_location("summarize_multi_zone_reducer_pressure", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


MODULE = load_module()


class MultiZoneReducerPressureProbeTests(unittest.TestCase):
    def test_materialized_probe_is_deterministic_and_reports_pressure(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            probe_root = Path(tmpdir) / "probe"
            first = MODULE.materialize_probe_root(
                probe_root,
                release_zone_count=12,
                reducer_worker_count=2,
                reducer_chunk_count=2,
            )
            first_report = MODULE.build_report(probe_root)

            second = MODULE.materialize_probe_root(
                probe_root,
                release_zone_count=12,
                reducer_worker_count=2,
                reducer_chunk_count=2,
            )
            second_report = MODULE.build_report(probe_root)

            self.assertEqual(first.release_zone_count, 12)
            self.assertEqual(first.reducer_chunk_count, 2)
            self.assertEqual(first.scenario_count, 12)
            self.assertEqual(second.release_zone_count, 12)
            self.assertEqual(first_report, second_report)
            self.assertEqual(first_report["probe_status"], "measured_scratch_root")
            self.assertEqual(first_report["manifest_mode"], "full")
            self.assertEqual(first_report["regional_split_plan_schema_version"], "regional_split_execution_plan_v1")
            self.assertEqual(first_report["regional_split_plan_status"], "ready")
            self.assertEqual(first_report["merge_manifest"]["schema_version"], "regional_split_merge_manifest_v1")
            self.assertEqual(first_report["merge_manifest"]["status"], "merged_fixture_outputs")
            self.assertEqual(
                first_report["merge_manifest"]["merge_order"],
                "sorted_chunk_id_then_output_family_then_path",
            )
            self.assertTrue(first_report["merge_manifest"]["merge_order_independent"])
            self.assertEqual(first_report["release_zone_count"], 12)
            self.assertEqual(first_report["trajectory_chunk_count"], 12)
            self.assertEqual(first_report["reducer_chunk_count"], 2)
            self.assertEqual(first_report["merge_order"], "sorted_chunk_id")
            self.assertTrue(first_report["merge_order_independent"])
            self.assertTrue(first_report["multi_zone_dry_run_blocked"])
            self.assertEqual(first_report["bottleneck_labels"]["merge_order"]["label"], "sorted_chunk_id_deterministic")
            self.assertEqual(first_report["bottleneck_labels"]["probe_blocker"]["label"], "multi_zone_dry_run_blocked")
            self.assertGreater(first_report["manifest_size_bytes"], 0)
            self.assertGreater(first_report["root_file_count"], first_report["release_zone_count"])
            self.assertEqual(first_report["output_family_file_counts"]["trajectory_csv"], 12)
            self.assertNotIn("trajectory_chunk_manifest", first_report["output_family_file_counts"])
            self.assertEqual(first_report["output_family_file_counts"]["reducer_chunk_manifest"], 2)
            self.assertEqual(first_report["reducer_manifest_file_count"], 2)
            self.assertEqual(first_report["sidecar_file_count"], 9)
            self.assertEqual(first_report["merged_output_summary"]["file_count"], first_report["output_file_count"] - 2)
            self.assertGreater(first_report["merged_output_summary"]["byte_count"], 0)
            self.assertLess(first_report["merged_output_summary"]["byte_count"], first_report["output_byte_count"])
            self.assertEqual(
                first_report["merged_output_summary"]["output_family_bytes"],
                first_report["output_family_bytes"],
            )
            self.assertEqual(first_report["sample_support_summary"]["source_zone_count"], 12)
            self.assertEqual(first_report["sample_support_summary"]["trajectory_sample_rows"], 72)
            self.assertEqual(first_report["sample_support_summary"]["deposition_sample_rows"], 12)
            self.assertEqual(first_report["sample_support_summary"]["impact_event_sample_rows"], 24)
            self.assertEqual(
                first_report["sample_support_summary"]["source_zone_counts_by_chunk"],
                {"reducer_chunk_00": 6, "reducer_chunk_01": 6},
            )
            self.assertEqual(first_report["rebuild_compatible_output_family_status"], "ready")
            self.assertEqual(
                first_report["rebuild_compatible_output_families"],
                [
                    "trajectory_csv",
                    "deposition_csv",
                    "impact_events_csv",
                    "trajectory_execution_plan",
                    "trajectory_execution_index",
                    "trajectory_merge_state",
                    "reducer_execution_plan",
                    "reducer_execution_index",
                    "reducer_merge_state",
                    "diagnostics_json",
                    "map_package_manifest",
                    "pilot_gis_package_manifest",
                ],
            )
            self.assertGreater(len(first_report["largest_output_families_by_bytes"]), 0)
            self.assertIn("kind", first_report["largest_output_families_by_bytes"][0])
            self.assertEqual(
                first_report["measured_reducer_constraints"]["constraint_source"]["source_document"],
                "docs/multi_zone_reducer_pressure_probe.md",
            )
            self.assertEqual(
                first_report["measured_reducer_constraints"]["simultaneous_release_zone_batch_max"],
                8,
            )
            self.assertEqual(first_report["measured_reducer_constraints"]["reducer_chunk_count_max"], 2)
            self.assertEqual(first_report["measured_reducer_constraints"]["reducer_worker_count_max"], 2)

    def test_regional_split_plan_has_stable_ordering_and_unique_execution_keys(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            probe_root = Path(tmpdir) / "probe"
            MODULE.materialize_probe_root(
                probe_root,
                release_zone_count=6,
                reducer_worker_count=2,
                reducer_chunk_count=3,
            )
            first_plan = json.loads(
                (probe_root / "input" / "regional_split_execution_plan.json").read_text(encoding="utf-8")
            )

            MODULE.materialize_probe_root(
                probe_root,
                release_zone_count=6,
                reducer_worker_count=2,
                reducer_chunk_count=3,
            )
            second_plan = json.loads(
                (probe_root / "input" / "regional_split_execution_plan.json").read_text(encoding="utf-8")
            )

            self.assertEqual(first_plan, second_plan)
            self.assertEqual(first_plan["schema_version"], "regional_split_execution_plan_v1")
            self.assertEqual(first_plan["status"], "ready")
            self.assertEqual(first_plan["merge_key_policy"], "chunk_id/zone_id/scenario_id")
            self.assertEqual(first_plan["split_count"], 6)
            self.assertEqual(first_plan["duplicate_execution_keys"], [])
            merge_keys = [split["merge_key"] for split in first_plan["splits"]]
            self.assertEqual(len(merge_keys), len(set(merge_keys)))
            for split in first_plan["splits"]:
                self.assertNotIn("execution_key", split)
            self.assertEqual(
                [split["zone_id"] for split in first_plan["splits"]],
                [f"source_zone_{index:02d}" for index in range(6)],
            )
            self.assertEqual(
                [split["chunk_id"] for split in first_plan["splits"]],
                [
                    "reducer_chunk_00",
                    "reducer_chunk_01",
                    "reducer_chunk_02",
                    "reducer_chunk_00",
                    "reducer_chunk_01",
                    "reducer_chunk_02",
                ],
            )
            for split in first_plan["splits"]:
                self.assertIn("group", split)
                self.assertIn("zone_id", split)
                self.assertIn("scenario_id", split)
                self.assertIn("sampling_weight", split)
                self.assertIn("chunk_id", split)
                self.assertIn("expected_output_root", split)
                self.assertIn("merge_key", split)

    def test_merge_manifest_ordering_is_stable_when_output_manifest_order_changes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            probe_root = Path(tmpdir) / "probe"
            MODULE.materialize_probe_root(
                probe_root,
                release_zone_count=6,
                reducer_worker_count=2,
                reducer_chunk_count=3,
            )
            regional_split_plan = json.loads(
                (probe_root / "input" / "regional_split_execution_plan.json").read_text(encoding="utf-8")
            )
            output_manifest = json.loads(
                (probe_root / "output" / "validation_multi_zone_reducer_pressure_manifest.json").read_text(encoding="utf-8")
            )
            merge_manifest_path = probe_root / "output" / "merged" / "regional_split_merge_manifest.json"
            first_merge = MODULE.build_merge_manifest(
                probe_root=probe_root,
                merge_manifest_path=merge_manifest_path,
                regional_split_plan=regional_split_plan,
                output_manifest=output_manifest,
                output_family_mix=MODULE.DEFAULT_OUTPUT_FAMILY_MIX,
            )
            shuffled_output_manifest = dict(output_manifest)
            shuffled_output_manifest["outputs"] = list(reversed(output_manifest["outputs"]))
            second_merge = MODULE.build_merge_manifest(
                probe_root=probe_root,
                merge_manifest_path=merge_manifest_path,
                regional_split_plan=regional_split_plan,
                output_manifest=shuffled_output_manifest,
                output_family_mix=MODULE.DEFAULT_OUTPUT_FAMILY_MIX,
            )

            self.assertEqual(first_merge, second_merge)
            output_order = [(entry["kind"], entry["path"]) for entry in first_merge["outputs"]]
            self.assertEqual(output_order, sorted(output_order))
            self.assertEqual(set(first_merge["merged_output_summary"]), {"file_count", "byte_count"})
            self.assertGreater(first_merge["merged_output_summary"]["file_count"], 0)
            self.assertGreater(first_merge["merged_output_summary"]["byte_count"], 0)
            self.assertNotIn("sample_support_summary", first_merge)
            self.assertNotIn("rebuild_compatible_output_families", first_merge)

    def test_merge_manifest_ordering_is_stable_when_batch_plan_order_changes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            probe_root = Path(tmpdir) / "probe"
            MODULE.materialize_probe_root(
                probe_root,
                release_zone_count=80,
                reducer_worker_count=2,
                reducer_chunk_count=2,
            )
            regional_split_plan = json.loads(
                (probe_root / "input" / "regional_split_execution_plan.json").read_text(encoding="utf-8")
            )
            output_manifest = json.loads(
                (probe_root / "output" / "validation_multi_zone_reducer_pressure_manifest.json").read_text(encoding="utf-8")
            )
            merge_manifest_path = probe_root / "output" / "merged" / "regional_split_merge_manifest.json"

            first_merge = MODULE.build_merge_manifest(
                probe_root=probe_root,
                merge_manifest_path=merge_manifest_path,
                regional_split_plan=regional_split_plan,
                output_manifest=output_manifest,
                output_family_mix=MODULE.DEFAULT_OUTPUT_FAMILY_MIX,
            )
            shuffled_plan = dict(regional_split_plan)
            shuffled_plan["splits"] = list(reversed(regional_split_plan["splits"]))
            shuffled_plan["chunk_order"] = list(reversed(regional_split_plan["chunk_order"]))
            second_merge = MODULE.build_merge_manifest(
                probe_root=probe_root,
                merge_manifest_path=merge_manifest_path,
                regional_split_plan=shuffled_plan,
                output_manifest=output_manifest,
                output_family_mix=MODULE.DEFAULT_OUTPUT_FAMILY_MIX,
            )

            self.assertEqual(first_merge, second_merge)
            self.assertEqual(first_merge["merge_order"], "sorted_chunk_id_then_output_family_then_path")
            self.assertTrue(first_merge["merge_order_independent"])
            self.assertEqual(first_merge["chunk_order"], sorted(first_merge["chunk_order"]))
            self.assertEqual(first_merge["merged_output_summary"], second_merge["merged_output_summary"])
            self.assertEqual(
                [(entry["kind"], entry["path"]) for entry in first_merge["outputs"]],
                sorted((entry["kind"], entry["path"]) for entry in first_merge["outputs"]),
            )

    def test_manifest_pressure_ladder_recommends_compact_mode(self) -> None:
        report = MODULE.build_manifest_pressure_ladder_report(release_zone_counts=(2, 4, 8, 12))

        self.assertEqual(report["schema_version"], "multi_zone_reducer_manifest_pressure_ladder_v1")
        self.assertEqual(report["ladder_status"], "measured_scratch_root")
        self.assertEqual(report["release_zone_counts"], [2, 4, 8, 12])
        self.assertEqual(report["recommended_default_manifest_mode"], "compact")
        self.assertEqual(len(report["rungs"]), 4)
        first_rung = report["rungs"][0]
        self.assertLess(first_rung["manifest_mode_delta"]["manifest_size_bytes_delta"], 0)
        self.assertLess(first_rung["output_family_delta"]["output_family_file_count_delta"]["reducer_chunk_manifest"], 0)
        self.assertEqual(first_rung["profiles"]["full_full"]["manifest_mode"], "full")
        self.assertEqual(first_rung["profiles"]["compact_full"]["manifest_mode"], "compact")
        self.assertEqual(first_rung["profiles"]["compact_reduced"]["manifest_mode"], "compact")
        self.assertIn("--measure-manifest-pressure-ladder", report["measurement_command"])
        self.assertIn("compact", report["summary"])

    def test_cli_materialize_root_uses_requested_release_zone_count(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            probe_root = Path(tmpdir) / "custom-probe"
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = MODULE.main(
                    [
                        "--materialize-root",
                        str(probe_root),
                        "--release-zone-count",
                        "8",
                        "--reducer-workers",
                        "2",
                        "--reducer-chunk-count",
                        "2",
                        "--format",
                        "json",
                    ]
                )
            self.assertEqual(exit_code, 0)
            report = json.loads(buffer.getvalue())
            self.assertEqual(report["release_zone_count"], 8)
            self.assertEqual(report["reducer_chunk_count"], 2)
            self.assertEqual(report["trajectory_chunk_count"], 8)
            self.assertEqual(report["probe_status"], "measured_scratch_root")

            command_plan = json.loads((probe_root / "command_plan.json").read_text(encoding="utf-8"))
            command = command_plan["commands"][0]["command"]
            self.assertIn("--release-zone-count", command)
            self.assertIn("8", command)

    def test_materialized_probe_honors_output_family_mix(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            probe_root = Path(tmpdir) / "probe"
            family_mix = (
                "trajectory_csv",
                "reducer_chunk_manifest",
                "reducer_execution_index",
                "reducer_merge_state",
            )
            MODULE.materialize_probe_root(
                probe_root,
                release_zone_count=6,
                reducer_worker_count=2,
                reducer_chunk_count=2,
                output_family_mix=family_mix,
            )
            report = MODULE.build_report(probe_root)

            self.assertEqual(report["output_family_mix"], list(family_mix))
            self.assertEqual(report["release_zone_count"], 6)
            self.assertEqual(report["reducer_chunk_count"], 2)
            self.assertEqual(report["output_family_file_counts"]["trajectory_csv"], 6)
            self.assertEqual(report["output_family_file_counts"]["reducer_chunk_manifest"], 2)
            self.assertNotIn("deposition_csv", report["output_family_file_counts"])
            self.assertNotIn("impact_events_csv", report["output_family_file_counts"])
            self.assertNotIn("trajectory_chunk_manifest", report["output_family_file_counts"])
            self.assertEqual(report["primary_output_file_count"], 6)
            self.assertEqual(report["sidecar_file_count"], 2)
            self.assertGreater(report["reducer_manifest_bytes"], 0)
            self.assertEqual(report["merge_order"], "sorted_chunk_id")
            self.assertTrue(report["merge_order_deterministic"])


if __name__ == "__main__":
    unittest.main()
