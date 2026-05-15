from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.check_hazard_rebuild_output_profile import classify_profile
from scripts.derive_hazard_rebuild_reduced_profile import main as derive_reduced_profile


def write_text(path: Path, content: str = "x\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class HazardRebuildReducedProfileDerivationTests(unittest.TestCase):
    def test_derivation_creates_rebuildable_reduced_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            source_root = tmp_root / "source"
            output_root = tmp_root / "reduced"
            source_manifest = source_root / "validation_source_manifest.json"
            output_manifest = output_root / "validation_reduced_manifest.json"

            write_text(source_root / "trajectory.csv", "trajectory\n")
            write_text(source_root / "deposition.csv", "deposition\n")
            write_text(source_root / "trajectory_metadata.csv", "metadata\n")
            write_text(source_root / "metrics.json", '{"status": "ok"}\n')
            impact_dir = source_root / "impacts"
            write_text(impact_dir / "impact_a.csv", "impact-a\n")
            write_text(impact_dir / "impact_b.csv", "impact-b\n")

            source_payload = {
                "case_id": "validation_tschamut_public_target_gate_v1",
                "outputs": [
                    {"kind": "trajectory", "path": "trajectory.csv", "format": "csv"},
                    {"kind": "ensemble_deposition", "path": "deposition.csv", "format": "csv"},
                    {"kind": "ensemble_impact_events", "path": "impacts", "format": "csv_directory"},
                    {"kind": "trajectory_metadata", "path": "trajectory_metadata.csv", "format": "csv"},
                    {"kind": "diagnostics", "path": "metrics.json", "format": "json"},
                ],
            }
            source_manifest.write_text(json.dumps(source_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

            exit_code = derive_reduced_profile(
                [
                    "--source-root",
                    str(source_root),
                    "--source-manifest",
                    str(source_manifest),
                    "--output-root",
                    str(output_root),
                    "--output-manifest",
                    str(output_manifest),
                    "--format",
                    "json",
                ]
            )

            self.assertEqual(exit_code, 0)
            self.assertTrue(output_manifest.exists())

            payload = json.loads(output_manifest.read_text(encoding="utf-8"))
            self.assertEqual(payload["validation_output_mode"], "rebuildable_reduced_output")
            self.assertEqual(payload["performance"]["output_file_count"], 5)
            self.assertGreater(payload["performance"]["output_bytes"], 0)
            self.assertEqual(len(payload["outputs"]), 5)

            profile = classify_profile(output_manifest, output_root, "target_rebuildable_reduced", "derived_reduced")
            self.assertEqual(profile.classification, "rebuildable_reduced_output")
            self.assertEqual(profile.file_count, 6)
            self.assertEqual(profile.output_count, 5)
            self.assertIn("impact_events_csv", profile.output_kinds)
            self.assertIn("trajectory", profile.output_kinds)


if __name__ == "__main__":
    unittest.main()
