from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from scripts import summarize_same_scale_uncertainty_envelope as envelope


class SameScaleUncertaintyEnvelopeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fake_acceptance = SimpleNamespace(
            build_acceptance_summary=lambda **kwargs: {"pilot_id": "tschamut_public_pilot"}
        )
        self.fake_bounded = SimpleNamespace(build_summary=lambda **kwargs: self._bounded_summary())
        self.fake_single_job = SimpleNamespace(build_summary=lambda **kwargs: self._single_job_summary())
        self.fake_context = SimpleNamespace(inspect_context_layers=lambda **kwargs: self._context_summary())
        self.fake_compare = SimpleNamespace(
            OK_STATUS="ok",
            compare_hazard_map_convergence=lambda *_args, **_kwargs: self.fail(
                "target-vs-gate convergence should remain blocked when target-side artifacts are absent"
            ),
        )

    def _bounded_summary(self) -> dict[str, object]:
        return {
            "final_classification": "no_go",
            "validation_output_blocker_status": "blocker_retained",
            "validation_output_reduced": True,
            "validation_output_comparison": {
                "status": "available",
                "validation_output_mode": "summary_only",
                "baseline_file_count": 125,
                "reduced_file_count": 4,
                "baseline_bytes": 34_545_900,
                "reduced_bytes": 81_425,
                "reduction_file_count_delta": 121,
                "reduction_bytes_delta": 34_464_475,
                "required_provenance_retained": True,
                "retained_output_classes": ["conditional_curve_summary_only"],
                "omitted_or_sampled_output_classes": ["trajectory_csv"],
            },
            "output_size_evidence": {
                "output_budget_validation_output_file_count": 125,
                "output_budget_validation_output_bytes": 34_545_900,
                "output_budget_hazard_output_file_count": 46,
                "output_budget_hazard_output_bytes": 16_613_900,
            },
            "validation_output_audit": {
                "status": "available",
                "manifest_path": "validation/private/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_manifest.json",
                "reduced": False,
                "validation_output_mode": None,
                "family_count": 7,
                "total_file_count": 125,
                "total_bytes": 34_545_900,
            },
            "local_output_audit": {"status": "available"},
        }

    def _single_job_summary(self) -> dict[str, object]:
        return {
            "decision": "defer",
            "final_classification": "defer",
            "single_job_sufficient_for_next_step": True,
            "distributed_execution_authorized": False,
            "current_pressure": {
                "current_file_count": 191,
                "current_byte_count": 267_527_120,
                "file_margin_to_ceiling": 9,
                "byte_margin_to_ceiling": -17_527_120,
            },
        }

    def _context_summary(self) -> dict[str, object]:
        return {
            "classification": "limiting",
            "context_review_status": "reviewed_local_context",
            "spatial_relevance_status": "reviewed_local_context",
            "swisstlm3d_archive_status": "measured_corridor_relevance",
            "roads_or_transport_relevance": {
                "classification": "limiting",
                "feature_count": 38,
            },
            "barriers_or_protection_relevance": {
                "classification": "limiting",
                "feature_count": 6,
            },
            "water_or_channel_relevance": {
                "classification": "limiting",
                "feature_count": 24,
            },
        }

    def test_missing_target_artifacts_keep_envelope_conditionally_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            gate_manifest = tmpdir_path / "gate_manifest.json"
            gate_manifest.write_text("{}", encoding="utf-8")
            target_validation_manifest = tmpdir_path / "missing_target_validation_manifest.json"
            target_hazard_manifest = tmpdir_path / "missing_target_hazard_manifest.json"

            with patch.object(envelope, "ACCEPTANCE", self.fake_acceptance), patch.object(
                envelope, "BOUNDED", self.fake_bounded
            ), patch.object(envelope, "SINGLE_JOB", self.fake_single_job), patch.object(
                envelope, "CONTEXT", self.fake_context
            ), patch.object(
                envelope, "CONVERGENCE", self.fake_compare
            ):
                report = envelope.build_uncertainty_envelope(
                    gate_manifest=gate_manifest,
                    target_validation_manifest=target_validation_manifest,
                    target_hazard_manifest=target_hazard_manifest,
                    context_root=tmpdir_path / "context",
                )

        expected_top_level = {
            "report_schema_version",
            "pilot_id",
            "final_classification",
            "uncertainty_envelope_status",
            "convergence_status",
            "target_artifact_restore_status",
            "gate_manifest_available",
            "target_validation_manifest_available",
            "target_hazard_manifest_available",
            "target_cellwise_layers_available",
            "tb014_ready",
            "convergence_evidence",
            "validation_output_status",
            "validation_output_mode_context",
            "validation_output_evidence",
            "context_status",
            "context_evidence",
            "execution_sufficiency_status",
            "execution_sufficiency_evidence",
            "artifact_readiness_status",
            "missing_or_pending_inputs",
            "limiting_factors",
            "uncertainty_reduced",
            "remaining_uncertainty",
            "scale_up_authorized",
            "operational_claims_allowed",
        }
        self.assertTrue(expected_top_level.issubset(report.keys()))
        self.assertEqual(report["final_classification"], "inconclusive")
        self.assertEqual(report["uncertainty_envelope_status"], "measured_with_pending_target_artifacts")
        self.assertEqual(report["convergence_status"], "blocked_missing_target_artifacts")
        self.assertEqual(report["target_artifact_restore_status"], "blocked_missing_inputs")
        self.assertTrue(report["gate_manifest_available"])
        self.assertFalse(report["target_validation_manifest_available"])
        self.assertFalse(report["target_hazard_manifest_available"])
        self.assertFalse(report["target_cellwise_layers_available"])
        self.assertFalse(report["tb014_ready"])
        self.assertEqual(report["validation_output_status"], "blocker_retained")
        self.assertEqual(report["validation_output_mode_context"], "summary_only")
        self.assertEqual(report["context_status"], "limiting")
        self.assertEqual(report["execution_sufficiency_status"], "defer")
        self.assertFalse(report["scale_up_authorized"])
        self.assertFalse(report["operational_claims_allowed"])

        expected_convergence_keys = {
            "convergence_status",
            "artifact_readiness_status",
            "target_artifact_restore_status",
            "gate_manifest_available",
            "target_validation_manifest_available",
            "target_hazard_manifest_available",
            "target_cellwise_layers_available",
            "tb014_ready",
            "compared_artifacts",
            "per_layer_metrics",
            "strongest_disagreement_layers",
            "overall_metrics",
            "missing_inputs",
            "compare_result",
        }
        self.assertEqual(set(report["convergence_evidence"]), expected_convergence_keys)
        self.assertTrue(any("summary_only" in item for item in report["uncertainty_reduced"]))
        self.assertTrue(
            any("real local context evidence is reviewed" in item for item in report["uncertainty_reduced"])
        )
        self.assertIn("single-job execution sufficiency is recorded", report["uncertainty_reduced"])
        self.assertTrue(
            any("corridor-level swissTLM3D relevance is measured" in item for item in report["uncertainty_reduced"])
        )

        missing_categories = {item["category"] for item in report["missing_or_pending_inputs"]}
        self.assertIn("target_artifact_restore", missing_categories)
        self.assertIn("convergence", missing_categories)
        self.assertIn("execution_sufficiency", missing_categories)

        requested_paths = {
            item.get("requested_path")
            for item in report["missing_or_pending_inputs"]
            if "requested_path" in item
        }
        self.assertIn(str(target_validation_manifest), requested_paths)
        self.assertIn(str(target_hazard_manifest), requested_paths)

    def test_markdown_render_surfaces_pending_target_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            gate_manifest = tmpdir_path / "gate_manifest.json"
            gate_manifest.write_text("{}", encoding="utf-8")
            target_validation_manifest = tmpdir_path / "missing_target_validation_manifest.json"
            target_hazard_manifest = tmpdir_path / "missing_target_hazard_manifest.json"

            with patch.object(envelope, "ACCEPTANCE", self.fake_acceptance), patch.object(
                envelope, "BOUNDED", self.fake_bounded
            ), patch.object(envelope, "SINGLE_JOB", self.fake_single_job), patch.object(
                envelope, "CONTEXT", self.fake_context
            ), patch.object(
                envelope, "CONVERGENCE", self.fake_compare
            ):
                report = envelope.build_uncertainty_envelope(
                    gate_manifest=gate_manifest,
                    target_validation_manifest=target_validation_manifest,
                    target_hazard_manifest=target_hazard_manifest,
                    context_root=tmpdir_path / "context",
                )

        markdown = envelope.render_markdown_report(report)
        self.assertIn("Target artifact restore status: `blocked_missing_inputs`", markdown)
        self.assertIn("Validation output mode context: `summary_only`", markdown)
        self.assertIn("Roads/transport relevance", markdown)


if __name__ == "__main__":
    unittest.main()
