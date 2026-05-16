from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import yaml

from scripts import summarize_tschamut_hotspot_provenance as summary


class TschamutHotspotProvenanceTests(unittest.TestCase):
    def test_json_shape_and_provenance_classes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_zone_path = root / "source_zone.yaml"
            scenario_table_path = root / "scenario_table.csv"
            trajectory_metadata_path = root / "trajectory_metadata.csv"
            deposition_path = root / "deposition.csv"
            source_zone_path.write_text(
                yaml.safe_dump(
                    {
                        "schema_version": "source_zone_metadata_v1",
                        "source_zone_id": "source_zone_a",
                        "crs_epsg": 2056,
                        "vertical_datum": "LN02",
                        "geometry": {
                            "type": "polygon",
                            "vertices": [[0.0, 0.0], [10.0, 0.0], [10.0, 10.0], [0.0, 10.0]],
                        },
                        "release_sampling_policy": {
                            "mode": "deterministic_grid",
                            "seed": 11,
                            "release_count": 2,
                        },
                    }
                ),
                encoding="utf-8",
            )
            scenario_table_path.write_text(
                "\n".join(
                    [
                        "scenario_id,source_zone_id,release_sampling_policy,model_configuration_id,terrain_material_assumption_id,sampling_weight,block_scenario_id,block_size_class,block_shape_class,block_radius_m,block_mass_kg,block_density_kgpm3,release_probability,scenario_probability,annual_frequency_per_year,time_horizon_years",
                        "scenario_a,source_zone_a,deterministic_grid,model_a,uniform,1.0,block_a,sphere,sphere,0.2,1.0,2000,,,,",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            trajectory_metadata_path.write_text(
                "\n".join(
                    [
                        "trajectory_id,release_id,source_zone_id,scenario_id,sampling_weight,probability_mode,normalization_scope",
                        "t001,r001,source_zone_a,scenario_a,1.0,sampling_weighted,conditioned_on_filter",
                        "t002,r002,source_zone_a,scenario_a,1.0,sampling_weighted,conditioned_on_filter",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            deposition_path.write_text(
                "\n".join(
                    [
                        "trajectory_id,x_m,y_m,z_m",
                        "t001,12.0,5.0,1.0",
                        "t002,13.0,6.0,1.0",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            spatial_report = {
                "schema_version": "spatial_same_scale_uncertainty_v1",
                "selected_layers": [
                    "max_kinetic_energy",
                    "velocity_exceedance_5mps",
                ],
                "artifacts_measured": [
                    {
                        "artifact_id": "artifact_a",
                        "manifest_path": str(root / "hazard" / "artifact_a_manifest.json"),
                    }
                ],
                "layer_summaries": {
                    "max_kinetic_energy": {
                        "uncertainty_concentration_class": "spatially_localized_shared_support_magnitude",
                        "mask_evidence": {"closure_role": "closure_limiting"},
                        "top_high_uncertainty_cells": [
                            {
                                "row": 2,
                                "col": 3,
                                "x_center": 12.0,
                                "y_center": 5.0,
                                "range": 42.0,
                                "support_flags_by_artifact": {"artifact_a": True, "artifact_b": True},
                                "valid_flags_by_artifact": {"artifact_a": True, "artifact_b": True},
                                "values_by_artifact": {"artifact_a": 1.0, "artifact_b": 3.0},
                            }
                        ],
                    },
                    "velocity_exceedance_5mps": {
                        "uncertainty_concentration_class": "diffuse_across_shared_support",
                        "mask_evidence": {"closure_role": "deferrable"},
                        "top_high_uncertainty_cells": [
                            {
                                "row": 4,
                                "col": 1,
                                "x_center": 13.0,
                                "y_center": 6.0,
                                "range": 0.5,
                                "support_flags_by_artifact": {"artifact_a": True, "artifact_b": True},
                                "valid_flags_by_artifact": {"artifact_a": True, "artifact_b": True},
                                "values_by_artifact": {"artifact_a": 0.1, "artifact_b": 0.4},
                            }
                        ],
                    },
                },
            }
            closure_gap_report = {
                "closure_limiting_layers": [
                    {"layer_key": "max_kinetic_energy", "closure_role": "closure_limiting"},
                ],
                "deferrable_layers": [
                    {"layer_key": "velocity_exceedance_5mps", "closure_role": "deferrable"},
                ],
            }

            report = summary.build_report(
                {
                    "same_scale_uncertainty_report": spatial_report,
                    "closure_gap_report": closure_gap_report,
                    "source_zone_metadata_path": str(source_zone_path),
                    "scenario_table_path": str(scenario_table_path),
                    "trajectory_metadata_path": str(trajectory_metadata_path),
                    "deposition_path": str(deposition_path),
                }
            )

            self.assertEqual(report["hotspot_provenance_status"], "measured_existing_artifacts")
            self.assertEqual(report["source_zone_evidence"]["source_zone_id"], "source_zone_a")
            self.assertEqual(report["scenario_evidence"]["row_count"], 1)
            self.assertEqual(report["trajectory_deposition_evidence"]["trajectory_metadata_row_count"], 2)
            self.assertEqual(report["layer_provenance_summaries"]["max_kinetic_energy"]["source_zone_attribution_class"], "outside_source_zone_polygon")
            self.assertEqual(report["layer_provenance_summaries"]["max_kinetic_energy"]["scenario_attribution_class"], "single_scenario_row_only")
            self.assertEqual(
                report["layer_provenance_summaries"]["max_kinetic_energy"]["trajectory_deposition_attribution_class"],
                "run_level_traceable_without_cell_lineage",
            )
            self.assertEqual(
                report["layer_provenance_summaries"]["max_kinetic_energy"]["hotspot_provenance_class"],
                "closure_limiting_outside_source_zone_polygon_single_scenario_row_only_run_level_traceable_without_cell_lineage",
            )
            self.assertTrue(
                report["layer_provenance_summaries"]["max_kinetic_energy"]["hotspot_support_summary"]["all_hotspots_outside_source_zone_polygon"]
            )
            self.assertGreater(
                report["layer_provenance_summaries"]["max_kinetic_energy"]["top_high_uncertainty_cells"][0]["distance_to_source_zone_m"],
                0.0,
            )
            self.assertEqual(report["prioritized_unknowns"][0]["layer_key"], "max_kinetic_energy")
            self.assertEqual(report["prioritized_unknowns"][1]["layer_key"], "velocity_exceedance_5mps")
            self.assertTrue(
                any(root_entry["root_type"] == "input_root" for root_entry in report["artifact_roots"])
            )
            self.assertIn("source_zone_a", summary.render_text_report(report))

    def test_missing_inputs_override_reports_blocked_status(self) -> None:
        report = summary.build_report({"missing_inputs": ["docs/missing.json"]})
        self.assertEqual(report["hotspot_provenance_status"], "blocked_missing_inputs")
        self.assertEqual(report["missing_inputs"], ["docs/missing.json"])
        self.assertFalse(report["scale_up_authorized"])
        self.assertFalse(report["operational_claims_allowed"])
