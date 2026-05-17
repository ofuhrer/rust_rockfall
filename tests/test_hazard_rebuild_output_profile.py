from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.check_hazard_rebuild_output_profile import build_report, classify_profile


def write_text(path: Path, content: str = "x\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_manifest(root: Path, manifest_name: str, outputs: list[dict[str, object]]) -> Path:
    manifest = {
        "case_id": manifest_name.removesuffix("_manifest.json"),
        "outputs": outputs,
    }
    manifest_path = root / manifest_name
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest_path


class HazardRebuildOutputProfileTests(unittest.TestCase):
    def test_summary_only_profile_is_not_rebuildable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "summary_only"
            outputs = [
                {"kind": "ensemble_deposition", "path": "summary_deposition.csv"},
                {"kind": "ensemble_stop_state", "path": "summary_stop_state.csv"},
                {"kind": "trajectory_metadata", "path": "summary_trajectory_metadata.csv"},
                {"kind": "diagnostics", "path": "summary_metrics.json"},
            ]
            for item in outputs:
                write_text(root / str(item["path"]), "1\n")
            manifest_path = write_manifest(root, "summary_manifest.json", outputs)

            profile = classify_profile(manifest_path, root, "target_summary_only", "summary_only")

            self.assertEqual(profile.classification, "summary_only_not_rebuildable")
            self.assertIn("trajectory_inputs", profile.missing_output_groups)
            self.assertIn("impact_event_inputs", profile.missing_output_groups)
            self.assertNotIn("deposition_inputs", profile.missing_output_groups)
            self.assertNotIn("diagnostics_inputs", profile.missing_output_groups)

    def test_full_probe_profile_is_rebuild_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "full_probe"
            outputs = [
                {"kind": "trajectory", "path": "trajectory.csv"},
                {"kind": "ensemble_deposition", "path": "deposition.csv"},
                {"kind": "ensemble_stop_state", "path": "stop_state.csv"},
                {"kind": "ensemble_trajectories", "path": "trajectories"},
                {"kind": "ensemble_impact_events", "path": "impacts"},
                {"kind": "trajectory_metadata", "path": "trajectory_metadata.csv"},
                {"kind": "diagnostics", "path": "metrics.json"},
            ]
            for item in outputs:
                target = root / str(item["path"])
                if target.suffix:
                    write_text(target, "1\n")
                else:
                    target.mkdir(parents=True, exist_ok=True)
                    write_text(target / "sample.csv", "1\n")
            manifest_path = write_manifest(root, "full_manifest.json", outputs)

            profile = classify_profile(manifest_path, root, "sampling_sensitivity_v1_full", "full_probe")

            self.assertEqual(profile.classification, "hazard_rebuild_ready")
            self.assertEqual(profile.missing_output_groups, tuple())
            self.assertEqual(profile.output_count, 7)

    def test_reduced_profile_is_rebuildable_reduced_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "reduced"
            outputs = [
                {"kind": "trajectory", "path": "trajectory.csv"},
                {"kind": "ensemble_deposition", "path": "deposition.csv"},
                {"kind": "impact_events_csv", "path": "impact_events.csv"},
                {"kind": "trajectory_metadata", "path": "trajectory_metadata.csv"},
                {"kind": "diagnostics", "path": "metrics.json"},
            ]
            for item in outputs:
                write_text(root / str(item["path"]), "1\n")
            manifest_path = write_manifest(root, "reduced_manifest.json", outputs)
            manifest_payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest_payload["validation_output_mode"] = "rebuildable_reduced_output"
            manifest_path.write_text(json.dumps(manifest_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

            profile = classify_profile(manifest_path, root, "target_rebuildable_reduced", "native_reduced")

            self.assertEqual(profile.classification, "rebuildable_reduced_output")
            self.assertEqual(profile.missing_output_groups, tuple())
            self.assertIn("impact_events_csv", profile.output_kinds)
            self.assertIn("trajectory", profile.output_kinds)
            self.assertEqual(profile.output_count, 5)
            self.assertEqual(profile.file_count, 6)
            self.assertGreater(profile.total_bytes, 0)

    def test_missing_inputs_report_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "missing"
            manifest_path = root / "missing_manifest.json"
            profile = classify_profile(manifest_path, root, "missing", "missing")
            self.assertEqual(profile.classification, "blocked_missing_inputs")

            report = build_report(
                [
                    {
                        "profile_id": "target_summary_only",
                        "label": "current_target_summary_only",
                        "root": root,
                        "manifest": manifest_path,
                    }
                ]
            )
            self.assertEqual(report["hazard_rebuild_output_profile_status"], "blocked_missing_inputs")
            self.assertEqual(report["readiness_status"], "blocked_missing_inputs")
            self.assertEqual(report["profile_classifications"]["target_summary_only"], "blocked_missing_inputs")

    def test_report_contract_shape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            summary_root = root / "summary"
            full_root = root / "full"
            reduced_root = root / "reduced"
            summary_outputs = [
                {"kind": "ensemble_deposition", "path": "summary_deposition.csv"},
                {"kind": "ensemble_stop_state", "path": "summary_stop_state.csv"},
                {"kind": "trajectory_metadata", "path": "summary_trajectory_metadata.csv"},
                {"kind": "diagnostics", "path": "summary_metrics.json"},
            ]
            full_outputs = [
                {"kind": "trajectory", "path": "trajectory.csv"},
                {"kind": "ensemble_deposition", "path": "deposition.csv"},
                {"kind": "ensemble_stop_state", "path": "stop_state.csv"},
                {"kind": "ensemble_trajectories", "path": "trajectories"},
                {"kind": "ensemble_impact_events", "path": "impacts"},
                {"kind": "trajectory_metadata", "path": "trajectory_metadata.csv"},
                {"kind": "diagnostics", "path": "metrics.json"},
            ]
            for item in summary_outputs:
                write_text(summary_root / str(item["path"]), "1\n")
            for item in full_outputs:
                target = full_root / str(item["path"])
                if target.suffix:
                    write_text(target, "1\n")
                else:
                    target.mkdir(parents=True, exist_ok=True)
                    write_text(target / "sample.csv", "1\n")
            reduced_outputs = [
                {"kind": "trajectory", "path": "trajectory.csv"},
                {"kind": "ensemble_deposition", "path": "deposition.csv"},
                {"kind": "impact_events_csv", "path": "impact_events.csv"},
                {"kind": "trajectory_metadata", "path": "trajectory_metadata.csv"},
                {"kind": "diagnostics", "path": "metrics.json"},
            ]
            for item in reduced_outputs:
                write_text(reduced_root / str(item["path"]), "1\n")
            summary_manifest = write_manifest(summary_root, "summary_manifest.json", summary_outputs)
            full_manifest = write_manifest(full_root, "full_manifest.json", full_outputs)
            reduced_manifest = write_manifest(reduced_root, "reduced_manifest.json", reduced_outputs)
            reduced_payload = json.loads(reduced_manifest.read_text(encoding="utf-8"))
            reduced_payload["validation_output_mode"] = "rebuildable_reduced_output"
            reduced_manifest.write_text(json.dumps(reduced_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

            report = build_report(
                [
                    {
                        "profile_id": "target_summary_only",
                        "label": "current_target_summary_only",
                        "root": summary_root,
                        "manifest": summary_manifest,
                    },
                    {
                        "profile_id": "sampling_sensitivity_v1_full",
                        "label": "bounded_probe_full_v1",
                        "root": full_root,
                        "manifest": full_manifest,
                    },
                    {
                        "profile_id": "target_rebuildable_reduced",
                        "label": "native_rebuildable_reduced_output",
                        "root": reduced_root,
                        "manifest": reduced_manifest,
                    },
                ]
            )

            self.assertFalse(report["scale_up_authorized"])
            self.assertFalse(report["operational_claims_allowed"])
            self.assertIn("required_hazard_rebuild_artifacts", report)
            self.assertIn("rebuildable_reduced_profile", report)
            self.assertIn("native_rebuildable_reduced_profile", report)
            self.assertEqual(report["profile_classifications"]["target_summary_only"], "summary_only_not_rebuildable")
            self.assertEqual(report["profile_classifications"]["sampling_sensitivity_v1_full"], "hazard_rebuild_ready")
            self.assertEqual(report["profile_classifications"]["native_rebuildable_reduced_output"], "rebuildable_reduced_output")
            self.assertEqual(report["reduced_profile"]["classification"], "rebuildable_reduced_output")
            self.assertEqual(report["rebuildable_reduced_profile"]["classification"], "rebuildable_reduced_output")


if __name__ == "__main__":
    unittest.main()
