from __future__ import annotations

import importlib.util
import io
import json
import tempfile
import unittest
import sys
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "summarize_multi_zone_reducer_pressure.py"
STORAGE_SCRIPT = ROOT / "scripts" / "measure_scenario_storage_output_tier_pressure.py"


def load_module():
    spec = importlib.util.spec_from_file_location("summarize_multi_zone_reducer_pressure", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


MODULE = load_module()
STORAGE_MODULE_SPEC = importlib.util.spec_from_file_location("measure_scenario_storage_output_tier_pressure", STORAGE_SCRIPT)
assert STORAGE_MODULE_SPEC is not None
STORAGE_MODULE = importlib.util.module_from_spec(STORAGE_MODULE_SPEC)
assert STORAGE_MODULE_SPEC.loader is not None
STORAGE_MODULE_SPEC.loader.exec_module(STORAGE_MODULE)


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
            generated = first_report["generated_scratch_root"]
            self.assertEqual(Path(generated["root"]), probe_root.resolve())
            self.assertEqual(generated["root_file_count"], first_report["root_file_count"])
            self.assertEqual(generated["root_byte_count"], first_report["root_byte_count"])
            self.assertEqual(generated["output_file_count"], first_report["output_file_count"])
            self.assertEqual(generated["output_byte_count"], first_report["output_byte_count"])
            self.assertEqual(
                set(generated["manifest_paths"]),
                {"command_plan", "probe_manifest", "regional_split_plan", "output_manifest", "merge_manifest"},
            )
            for path in generated["manifest_paths"].values():
                self.assertTrue(Path(path).exists())
            for byte_count in generated["manifest_size_by_path"].values():
                self.assertGreater(byte_count, 0)
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
            self.assertNotIn("reducer_chunk_manifest", first_report["output_family_file_counts"])
            storage_measure = STORAGE_MODULE.measure_root(
                probe_root / "output",
                label="multi_zone_probe_output",
                evidence_label="fixture_backed",
            )
            self.assertEqual(first_report["output_family_accounting_alignment"]["status"], "ready")
            for family in ("trajectory", "deposition", "impact_events"):
                self.assertEqual(
                    first_report["storage_pressure_family_file_counts"][family],
                    storage_measure["family_counts"][family],
                )
                self.assertEqual(
                    first_report["storage_pressure_family_bytes"][family],
                    storage_measure["family_bytes"][family],
                )
            self.assertEqual(first_report["reducer_manifest_file_count"], 0)
            self.assertEqual(first_report["reducer_manifest_bytes"], 0)
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
            self.assertEqual(
                first_report["measured_reducer_constraints"]["simultaneous_release_zone_batch_max_source"],
                "scratch_local_constraint",
            )
            self.assertEqual(first_report["measured_reducer_constraints"]["reducer_chunk_count_max"], 2)
            self.assertEqual(first_report["measured_reducer_constraints"]["reducer_worker_count_max"], 2)

    def test_completed_diagnostic_run_record_updates_single_node_postproc_batch_ceiling(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmpdir:
            run_record = Path(tmpdir) / "run_record.json"
            run_record.write_text(
                json.dumps(
                    {
                        "schema_version": "balfrin_diagnostic_run_record_v1",
                        "status": "completed",
                        "terminal_state": "COMPLETED",
                        "run_root": "/scratch/mch/olifu/rust_rockfall/diagnostics/diagnostic_16_zone_simplified_20260525",
                        "job_id": "4367731",
                        "diagnostic_shape": {"release_zone_count": 16},
                        "collection": {
                            "status": "complete",
                            "pressure_report": {
                                "status": "measured_scratch_root",
                                "release_zone_count": 16,
                                "output_file_count": 52,
                                "output_byte_count": 23661,
                                "manifest_size_bytes": 15898,
                                "root_file_count": 57,
                                "reducer_wall_time_seconds": 3.07,
                            },
                        },
                    }
                ),
                encoding="utf-8",
            )

            with mock.patch.object(MODULE, "DEFAULT_BALFRIN_DIAGNOSTIC_RUN_RECORD", run_record):
                constraints = MODULE.recommended_constraints(
                    release_zone_count=12,
                    reducer_chunk_count=2,
                    reducer_worker_count=2,
                )

        self.assertEqual(constraints["simultaneous_release_zone_batch_max"], 16)
        self.assertEqual(constraints["simultaneous_release_zone_batch_max_source"], "diagnostic_single_node_postproc")
        self.assertEqual(constraints["next_diagnostic_release_zone_count"], 24)
        self.assertEqual(
            constraints["diagnostic_single_node_postproc_ceiling"]["provenance_label"],
            "diagnostic_single_node_postproc",
        )
        self.assertEqual(constraints["diagnostic_single_node_postproc_ceiling"]["job_id"], "4367731")

    def test_measured_regional_split_root_report_exposes_compact_manifest_and_replay_budgets(self) -> None:
        report = MODULE.build_measured_regional_split_root_report()

        self.assertEqual(report["schema_version"], "multi_zone_measured_regional_split_reducer_pressure_v1")
        self.assertEqual(report["report_kind"], "measured_regional_split_root")
        self.assertEqual(
            report["measured_run_root"],
            "/scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_multi_release_zone_v1",
        )
        self.assertEqual(report["measurement_status"], "measured_existing_artifacts")
        self.assertEqual(report["compact_manifest_recommendation"]["default_manifest_mode"], "compact")
        self.assertEqual(report["compact_manifest_recommendation"]["release_zone_count"], 12)
        self.assertEqual(report["compact_manifest_recommendation"]["manifest_size_bytes_delta"], -16577)
        self.assertEqual(report["compact_manifest_recommendation"]["output_file_count_delta"], 0)
        self.assertEqual(report["compact_manifest_recommendation"]["reducer_manifest_bytes_delta"], 0)
        self.assertEqual(report["compact_manifest_recommendation"]["reducer_manifest_file_count_delta"], 0)
        self.assertEqual(report["compact_manifest_recommendation"]["sidecar_file_count_delta"], 0)
        self.assertEqual(report["reducer_merge_order"], "sorted_chunk_id")
        self.assertTrue(report["reducer_merge_order_independent"])
        self.assertEqual(report["replay_critical_family_budgets"]["reducer_execution_plan"]["file_count"], 1)
        self.assertEqual(report["replay_critical_family_budgets"]["reducer_execution_plan"]["bytes"], 46234)
        self.assertEqual(report["replay_critical_family_budgets"]["reducer_chunk_manifest"]["file_count"], 2)
        self.assertEqual(report["replay_critical_family_budgets"]["reducer_chunk_manifest"]["bytes"], 43141)
        self.assertEqual(report["replay_critical_family_budgets"]["pilot_gis_package_manifest"]["file_count"], 1)
        self.assertEqual(report["replay_critical_family_budgets"]["pilot_gis_package_manifest"]["bytes"], 21956)
        self.assertEqual(report["next_probe_recommendation"]["task_id"], "TB-457")
        self.assertEqual(report["next_probe_recommendation"]["action_id"], "measure_scenario_storage_output_tier_pressure")
        self.assertIn("compact manifest mode", report["summary"])
        self.assertIn("scenario storage and output-tier pressure", report["summary"])

    def test_cli_measured_regional_split_root_report_uses_fixture_backed_artifacts(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            exit_code = MODULE.main(["--measured-regional-split-root-report", "--format", "json"])
        self.assertEqual(exit_code, 0)
        report = json.loads(buffer.getvalue())
        self.assertEqual(report["report_kind"], "measured_regional_split_root")
        self.assertEqual(report["compact_manifest_recommendation"]["default_manifest_mode"], "compact")
        self.assertEqual(report["next_probe_recommendation"]["task_id"], "TB-457")

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
            self.assertEqual(set(first_merge["merged_output_summary"]), {"file_count", "byte_count", "output_listing_mode"})
            self.assertEqual(first_merge["merged_output_summary"]["output_listing_mode"], "full_path_listing")
            self.assertGreater(first_merge["merged_output_summary"]["file_count"], 0)
            self.assertGreater(first_merge["merged_output_summary"]["byte_count"], 0)
            self.assertNotIn("sample_support_summary", first_merge)
            self.assertNotIn("rebuild_compatible_output_families", first_merge)

    def test_compact_merge_manifest_uses_kind_index_listing_without_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            probe_root = Path(tmpdir) / "probe"
            MODULE.materialize_probe_root(
                probe_root,
                release_zone_count=8,
                reducer_worker_count=2,
                reducer_chunk_count=2,
                manifest_mode="compact",
            )
            merge_manifest = json.loads(
                (probe_root / "output" / "merged" / "regional_split_merge_manifest.json").read_text(encoding="utf-8")
            )

        self.assertEqual(merge_manifest["merged_output_summary"]["output_listing_mode"], "compact_family_index_summary")
        self.assertEqual(
            merge_manifest["merged_output_summary"]["rebuild_listing_source"],
            "validation output manifest compact_v1",
        )
        self.assertTrue(all("path" not in entry for entry in merge_manifest["outputs"]))
        trajectory_entries = [entry for entry in merge_manifest["outputs"] if entry["kind"] == "trajectory_csv"]
        reducer_entries = [entry for entry in merge_manifest["outputs"] if entry["kind"] == "reducer_chunk_manifest"]
        self.assertEqual(len(trajectory_entries), 1)
        self.assertEqual(trajectory_entries[0]["zone_index_start"], 0)
        self.assertEqual(trajectory_entries[0]["zone_index_end"], 7)
        self.assertEqual(trajectory_entries[0]["zone_index_count"], 8)
        self.assertEqual(trajectory_entries[0]["file_count"], 8)
        self.assertEqual(reducer_entries, [])
        self.assertTrue(all(entry["total_bytes"] > 0 for entry in merge_manifest["outputs"]))

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
        self.assertNotIn("reducer_chunk_manifest", first_rung["profiles"]["full_full"]["output_family_file_counts"])
        self.assertEqual(first_rung["combined_delta"]["reducer_manifest_file_count_delta"], 0)
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
