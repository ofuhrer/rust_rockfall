# Script Inventory

Status: current_workflow navigation and cleanup guardrail.

This inventory classifies every top-level `scripts/*.py` file exactly once. It
does not change CLI behavior and it is not a new execution framework. It exists
so cleanup can distinguish active workflow surfaces from historical or
operator-facing helpers before anything is moved or deleted.

Deletion remains deferred. A script may be deleted only when no current doc,
backlog item, command plan, test, validation record, or reproduction command
names it, and when a replacement path or archive note is documented.

## High-Risk Workflow Surfaces

Do not move these in cleanup passes without a focused compatibility task:

- `scripts/build_hazard_layers.py`
- `scripts/generate_pilot_command_plan.py`
- `scripts/submit_balfrin_probe.py`
- `scripts/plan_aoi_to_prepared_pilot_dry_run.py`
- `scripts/check_repo_consistency.py`
- `scripts/print_agent_task_context.py`

## Core Workflow CLIs

- `scripts/audit_gis_cog_package_readiness.py`
- `scripts/audit_multisite_source_scenario_contract.py`
- `scripts/build_hazard_layers.py`
- `scripts/check_balfrin_remote_access_preflight.py`
- `scripts/check_balfrin_tschamut_readiness.py`
- `scripts/check_chant_sura_real_context_readiness_gate.py`
- `scripts/check_hazard_output_profile.py`
- `scripts/check_hazard_rebuild_output_profile.py`
- `scripts/check_same_scale_artifact_readiness.py`
- `scripts/check_second_site_public_geodata_preflight.py`
- `scripts/collect_balfrin_probe_metrics.py`
- `scripts/compare_hazard_map_convergence.py`
- `scripts/convert_same_scale_package_to_cog.py`
- `scripts/derive_hazard_rebuild_reduced_profile.py`
- `scripts/download_tschamut_swisstlm3d_context.py`
- `scripts/generate_balfrin_multi_release_zone_demo_handoff.py`
- `scripts/generate_balfrin_target_area_demo_handoff.py`
- `scripts/generate_balfrin_target_area_scenario_tables.py`
- `scripts/generate_candidate_source_zone_scenarios.py`
- `scripts/generate_chant_sura_fluelapass_dry_run_case_skeleton.py`
- `scripts/generate_pilot_command_plan.py`
- `scripts/generate_tschamut_block_scenario_tables.py`
- `scripts/generate_tschamut_same_scale_cases.py`
- `scripts/inspect_tschamut_public_context_layers.py`
- `scripts/measure_hazard_context_overlap.py`
- `scripts/plan_aoi_terrain_preprocessing.py`
- `scripts/plan_aoi_to_prepared_pilot_dry_run.py`
- `scripts/plan_balfrin_single_release_zone_case_dry_run.py`
- `scripts/plan_pragmatic_release_plan.py`
- `scripts/plan_release_plan_dry_run.py`
- `scripts/plan_release_zone_heuristic_dry_run.py`
- `scripts/plan_swisstopo_aoi_acquisition.py`
- `scripts/plan_terrain_release_zone_candidates.py`
- `scripts/preflight_balfrin_smallest_multi_zone_probe_authorization.py`
- `scripts/submit_balfrin_probe.py`
- `scripts/verify_public_geodata_cache.py`

## Repository Checks And Context Helpers

- `scripts/audit_case_schema.py`
- `scripts/audit_local_artifacts.py`
- `scripts/check_repo_consistency.py`
- `scripts/inventory_workflow_shell_coupling.py`
- `scripts/performance_ci_tracking.py`
- `scripts/print_agent_task_context.py`

## Hazard Output Support Modules

These are imported by workflow CLIs and should be refactored only with tests for
the calling CLIs.

- `scripts/hazard_output_manifests.py`
- `scripts/hazard_output_reports.py`
- `scripts/hazard_output_writers.py`

## Shared Workflow Helpers

- `scripts/lib/workflow_validation.py` centralizes narrow validation and
  workflow-shell helpers, including dynamic script loading used by compatibility
  CLIs.

## Dataset, Benchmark, And Calibration Preparation

These are operator-facing or research-preparation helpers. The dataset download
and preparation scripts without direct unit-test references are legacy
operator-facing until they get smoke tests or a documented replacement.

- `scripts/calibrate_scarring_impact.py`
- `scripts/download_datasets.py`
- `scripts/prepare_chant_sura_eota221_benchmark.py`
- `scripts/prepare_chant_sura_fluelapass_minimal_preflight_inputs.py`
- `scripts/prepare_chant_sura_public_benchmark.py`
- `scripts/prepare_mel_de_la_niva_benchmark.py`
- `scripts/prepare_tschamut_public_benchmark.py`
- `scripts/prepare_tschamut_swissalti3d_pilot.py`
- `scripts/preprocess_datasets.py`
- `scripts/preprocess_scarring_real_data.py`
- `scripts/run_tschamut_calibration.py`

## Performance, Estimation, And Diagnostic Runners

- `scripts/assess_validation_calibration_evidence_gaps.py`
- `scripts/build_terrain_material_diagnostic_matrix.py`
- `scripts/collect_tschamut_registration_sensitivity.py`
- `scripts/estimate_large_scale_execution.py`
- `scripts/estimate_swiss_wide_execution_envelope.py`
- `scripts/map_physical_credibility_evidence_requirements.py`
- `scripts/prototype_cog_conversion.py`
- `scripts/run_dem_terrain_sensitivity.py`
- `scripts/run_performance_benchmark.py`
- `scripts/run_aoi_hazard_workflow.py`

## Evidence Summarizers

- `scripts/rehearse_balfrin_post_run_evidence_collector.py`
- `scripts/summarize_balfrin_authorization_gated_multi_zone_measurement_path.py`
- `scripts/summarize_balfrin_bounded_probe_interpretation.py`
- `scripts/summarize_balfrin_demonstration_replay_smoke.py`
- `scripts/summarize_balfrin_demonstration_closure_package.py`
- `scripts/summarize_balfrin_ensemble_frontier.py`
- `scripts/summarize_balfrin_evidence_bundle.py`
- `scripts/summarize_balfrin_failure_taxonomy.py`
- `scripts/summarize_balfrin_management_demo_package.py`
- `scripts/summarize_balfrin_next_live_run_decision_gate.py`
- `scripts/summarize_balfrin_output_tier_audit.py`
- `scripts/summarize_balfrin_physical_credibility_evidence_gaps.py`
- `scripts/summarize_balfrin_post_run_interpretation_gate.py`
- `scripts/summarize_balfrin_probe_metrics_report.py`
- `scripts/summarize_balfrin_probe_preservation_gate.py`
- `scripts/summarize_balfrin_restartability_recovery.py`
- `scripts/summarize_balfrin_scientific_delta_report.py`
- `scripts/summarize_balfrin_single_job_execution.py`
- `scripts/summarize_balfrin_single_release_zone_pilot_contract.py`
- `scripts/recover_balfrin_target_area_metrics_from_run_root.py`
- `scripts/recover_balfrin_target_area_spatial_artifacts_from_run_root.py`
- `scripts/summarize_balfrin_target_area_metrics_completion_rerun_package.py`
- `scripts/summarize_balfrin_target_area_candidate_stability.py`
- `scripts/summarize_balfrin_target_area_evidence_bundle.py`
- `scripts/summarize_balfrin_target_area_gis_cog_scope.py`
- `scripts/summarize_balfrin_target_area_interpretation.py`
- `scripts/summarize_bounded_next_ensemble_feasibility_probe.py`
- `scripts/summarize_bounded_reducer_runtime_scaling.py`
- `scripts/summarize_bounded_validation_output_profile.py`
- `scripts/summarize_chant_sura_contact_diagnostics.py`
- `scripts/summarize_chant_sura_fluelapass_dry_run_report.py`
- `scripts/summarize_chant_sura_holdout_evidence.py`
- `scripts/summarize_clean_checkout_blocked_reports.py`
- `scripts/summarize_conditional_pilot_acceptance.py`
- `scripts/summarize_large_aoi_gis_cog_stress_test.py`
- `scripts/summarize_multi_zone_hazard_throughput_profile.py`
- `scripts/summarize_multi_zone_reducer_pressure.py`
- `scripts/summarize_observed_runout_deposition_intake_contract.py`
- `scripts/summarize_pilot_scaling.py`
- `scripts/summarize_same_scale_sampling_uncertainty.py`
- `scripts/summarize_same_scale_stability_frontier.py`
- `scripts/summarize_same_scale_uncertainty_envelope.py`
- `scripts/summarize_spatial_same_scale_uncertainty.py`
- `scripts/summarize_stopping_behavior.py`
- `scripts/summarize_tschamut_closure_gap_deltas.py`
- `scripts/summarize_tschamut_conditional_diagnostic_interpretation.py`
- `scripts/summarize_tschamut_conditional_pilot_closure.py`
- `scripts/summarize_tschamut_hotspot_provenance.py`

## Validators

- `scripts/validate_annual_physical_prototype_preflight.py`
- `scripts/validate_annual_physical_validation_calibration_review_gate.py`
- `scripts/validate_balfrin_slurm_probe_repeatability.py`
- `scripts/validate_balfrin_target_gate_reproduction.py`
- `scripts/validate_balfrin_tschamut_readiness_record.py`
- `scripts/validate_block_release_probability_evidence.py`
- `scripts/validate_conditional_convergence_protocol.py`
- `scripts/validate_dem_input_conditioning_qa.py`
- `scripts/validate_output_budget_reducer_gate.py`
- `scripts/validate_multi_zone_reducer_pressure_gate.py`
- `scripts/validate_physical_frequency_reducer_preconditions.py`
- `scripts/validate_physical_source_frequency_design_gate.py`
- `scripts/validate_pilot_ensemble_feasibility.py`
- `scripts/validate_pilot_gis_package.py`
- `scripts/validate_pilot_gis_visual_qa.py`
- `scripts/validate_pilot_obstacle_scope.py`
- `scripts/validate_public_benchmark_manifest.py`
- `scripts/validate_public_real_site_conditional_pilot_run.py`
- `scripts/validate_public_real_site_geodata_manifest.py`
- `scripts/validate_scalable_conditional_execution.py`
- `scripts/validate_scalable_conditional_target_gate.py`
- `scripts/validate_source_frequency_evidence.py`
- `scripts/validate_source_scenario_policy.py`
- `scripts/validate_stochastic_sampling_audit.py`

## Consolidation Direction

- Continue extracting genuinely repeated YAML/JSON/path/checksum logic into
  `scripts/lib/workflow_validation.py` only when a focused validator family is
  being touched anyway.
- Do not create another validator family solely to police cleanup.
- Treat `scripts/build_hazard_layers.py` and `scripts/check_repo_consistency.py`
  as separate bounded refactor targets, not incidental cleanup work.
