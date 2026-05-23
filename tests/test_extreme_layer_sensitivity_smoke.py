from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts import summarize_extreme_layer_sensitivity_smoke as smoke


class ExtremeLayerSensitivitySmokeTests(unittest.TestCase):
    def test_default_manifests_measure_extreme_layer_deltas(self) -> None:
        report = smoke.build_report()

        self.assertEqual(report["schema_version"], smoke.SCHEMA_VERSION)
        self.assertEqual(report["smoke_status"], "measured")
        self.assertEqual([row["layer_key"] for row in report["layer_summaries"]], list(smoke.EXTREME_LAYERS))
        self.assertGreater(report["overall_metrics"]["max_linf_abs_diff"], 0.0)
        self.assertGreater(report["overall_metrics"]["total_l1_abs_diff"], 0.0)
        self.assertFalse(report["claim_boundaries"]["balfrin_required"])
        self.assertFalse(report["claim_boundaries"]["new_ensemble_execution"])
        self.assertFalse(report["claim_boundaries"]["physical_probability_claims_allowed"])

    def test_fixture_reports_present_layer_support_and_summary_deltas(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            gate_manifest = write_manifest(
                root / "gate_manifest.json",
                {
                    "max_kinetic_energy": [[0.0, 1.0], [2.0, -9999.0]],
                    "max_jump_height": [[0.0, 0.5], [-9999.0, 1.0]],
                },
            )
            target_manifest = write_manifest(
                root / "target_manifest.json",
                {
                    "max_kinetic_energy": [[0.0, 3.0], [2.0, -9999.0]],
                    "max_jump_height": [[0.0, -9999.0], [0.2, 1.4]],
                },
            )

            report = smoke.build_report(gate_manifest=gate_manifest, target_manifest=target_manifest)

        rows = {row["layer_key"]: row for row in report["layer_summaries"]}
        self.assertEqual(report["smoke_status"], "measured")
        self.assertEqual(rows["max_kinetic_energy"]["summary_delta"]["linf_abs_diff"], 2.0)
        self.assertEqual(rows["max_kinetic_energy"]["support_delta"]["nonzero_jaccard"], 1.0)
        self.assertEqual(rows["max_jump_height"]["support_delta"]["nodata_mismatch_count"], 2)
        self.assertEqual(rows["max_jump_height"]["sensitivity_class"], "support_nodata_sensitive_extreme_layer")

    def test_missing_extreme_layer_blocks_without_comparing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            gate_manifest = write_manifest(
                root / "gate_manifest.json",
                {"max_kinetic_energy": [[0.0, 1.0], [2.0, -9999.0]]},
            )
            target_manifest = write_manifest(
                root / "target_manifest.json",
                {
                    "max_kinetic_energy": [[0.0, 3.0], [2.0, -9999.0]],
                    "max_jump_height": [[0.0, 0.2], [0.5, 1.0]],
                },
            )

            report = smoke.build_report(gate_manifest=gate_manifest, target_manifest=target_manifest)

        self.assertEqual(report["smoke_status"], "blocked_missing_extreme_layers")
        self.assertEqual(report["missing_layers"][0]["layer_key"], "max_jump_height")
        self.assertEqual(report["missing_layers"][0]["presence_status"], "missing_from_gate")
        self.assertEqual(report["overall_metrics"]["measured_layer_count"], 0)

    def test_text_report_names_boundaries_and_next_measurement(self) -> None:
        text = smoke.render_text_report(smoke.build_report())

        self.assertIn("max_kinetic_energy", text)
        self.assertIn("max_jump_height", text)
        self.assertIn("operational_claims_allowed: False", text)
        self.assertIn("physical_probability_claims_allowed: False", text)
        self.assertIn("next_measurement", text)


def write_manifest(path: Path, grids: dict[str, list[list[float]]]) -> Path:
    layers = []
    for layer_key, cells in grids.items():
        grid_path = path.parent / f"{path.stem}_{layer_key}.json"
        grid_path.write_text(json.dumps({"nodata_value": -9999, "cells": cells}), encoding="utf-8")
        layers.append(
            {
                "key": layer_key,
                "layer_name": layer_key,
                "format": "json",
                "grid_path": grid_path.name,
                "kind": "hazard_layer",
                "thresholds": [],
            }
        )
    path.write_text(
        json.dumps({"case_id": path.stem, "layers": [], "outputs": [], "cellwise_layers": layers}),
        encoding="utf-8",
    )
    return path


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
