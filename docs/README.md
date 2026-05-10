# Documentation Index

Current project version: `v0.6.1`.

`rust_rockfall` targets automated, reproducible rockfall hazard mapping for
Switzerland's Alpine terrain from public geodata, primarily swisstopo. The first
concrete milestone is a valley-scale pilot that connects pragmatic
source-zone/block-scenario generation, large deterministic trajectory
ensembles, uncertainty-aware conditional intensity-exceedance products,
GIS-ready outputs, and performance that can grow from efficient single-socket
runs toward CSCS/SLURM workflows. Risk modelling, exposure/vulnerability
analysis, and operational warning systems are out of scope.

Use this index by authority level. Governing documents and current roadmaps are
the starting point for new work. Evidence reports describe what was observed at
the time they were written. Historical decision fragments have been consolidated
into `decision_log.md`; they do not override the current roadmaps.

## Governing Documents

- `../README.md`: project overview, quickstart, scope, and current caveats.
- `../AGENTS.md`: operating rules for automated agents, hard boundaries, and
  long-term development direction.
- `onboarding.md`: local prerequisites, hooks, optional data setup, and
  handoff checks.
- `model_design.md`: current equations, assumptions, contact models, terrain
  conventions, and API boundaries.
- `validation_data_schema.md`: YAML case and validation-data schema.
- `architecture_boundaries.md`: module responsibility map, panic/error
  boundaries, and refactor targets for large files.
- `validation_plan.md`: validation strategy and calibration policy.
- `validation_maturity_framework.md`: evidence levels and claim hierarchy.
- `dataset_strategy.md`: separation of calibration, validation, pilot, and
  operational input datasets.
- `swisstopo_data_strategy.md`: Swiss geodata roles, CRS/datum expectations,
  provenance requirements, and raw-data boundaries.

## Current Roadmaps

- `next_development_targets.md`: current prioritized development targets.
- `roadmap_recommendation_matrix.md`: scoring matrix behind target ordering.
- `roadmap_hazard_mapping.md`: long-term hazard-map roadmap and hazard/risk
  boundary.
- `real_case_intensity_frequency_implementation_roadmap.md`: staged path from
  conditional intensity-exceedance products to later physical/annual
  intensity-frequency semantics.
- `scalability_and_data_formats_review.md`: large-ensemble, output-format, and
  scaling roadmap.
- `implementation_plan.md`: broad phased implementation plan.
- `decision_log.md`: consolidated record of major design and sequencing
  decisions after pruning stale standalone decision fragments.

## Swiss Pilot And Geodata Contracts

- `public_real_site_geodata_preparation.md`: share-safe public real-site
  geodata manifest and conditional pilot run-freeze workflow.
- `public_real_site_conditional_pilot_report_template.md`: pilot report
  scaffold for pass/no-go/inconclusive classification.
- `source_zone_block_scenario_policy_v1.md`: source-zone evidence levels,
  deterministic release sampling, and representative block-scenario policy.
- `dem_terrain_sensitivity_benchmark.md`: dry-runnable DEM/terrain sensitivity
  fixture and real-site scaffold.
- `pilot_gis_package.md`: diagnostic QGIS/GeoTIFF package contract and visual
  QA gate.
- `swiss_terrain_ingestion_pilot.md`: minimal terrain-source, release-zone, and
  terrain-class metadata contracts.
- `tschamut_swissalti3d_pilot.md`: local/private Tschamut real-site pilot
  workflow.
- `tschamut_swissalti3d_controlled_pilot_plan.md`: historical controlled
  Tschamut/swissALTI3D pilot plan; use current roadmaps for priority decisions.
- `balfrin_tschamut_pilot_runbook.md`: reusable balfrin Tschamut pilot
  operating procedure for readiness, validation/hazard execution, reducer
  provenance inspection, scaling summary regeneration, and artifact hygiene.

## Hazard And Probabilistic Semantics

- `hazard_layers.md`: hazard-layer builder, raster outputs, GeoTIFF options,
  and layer semantics.
- `hazard_map_semantics.md`: allowed/disallowed hazard-map language,
  conditional versus physical/annual probability, denominators, and
  normalization rules.
- `probabilistic_scenario_model_design.md`: scenario-level probability modes,
  source-zone placeholders, and normalization conventions.
- `physical_source_frequency_design_gate.md`: design-gate decision for future
  physical/source-frequency semantics; the current decision keeps the
  annual/physical prototype deferred.
- `source_frequency_evidence_contract.md`: inactive source-rate evidence
  schema, validator, and template for closing one design-gate blocker without
  enabling annual or physical products.
- `block_release_probability_evidence_contract.md`: inactive block-scenario
  and release-cell probability evidence schema, validator, and template for
  closing one design-gate blocker without enabling annual or physical products.
- `physical_frequency_reducer_preconditions.md`: inactive overlap-adjusted
  reducer and uncertainty-propagation precondition schema, validator, and
  template for closing one design-gate blocker without enabling annual or
  physical products.
- `annual_physical_validation_calibration_review_gate.md`: inactive
  validation/calibration review-gate schema, validator, and template for
  closing one design-gate blocker without enabling annual or physical products.
- `annual_physical_prototype_preflight.md`: inactive Target 10 preflight
  schema, validator, and template that keeps the annual/physical prototype
  blocked while the design gate remains deferred.
- `probabilistic_trajectory_metadata_design.md`: trajectory metadata fields for
  probabilistic scenario/source-zone propagation.
- `probabilistic_hazard_phase1_closure.md`: implemented Level 1/2
  probabilistic map semantics and Phase 1 limits.
- `probabilistic_hazard_mapping_development_roadmap.md`: broader staged
  probabilistic hazard-map development roadmap.

## Benchmark And Validation Evidence

- `benchmark_catalog.md`: implemented verification and validation inventory.
- `public_benchmark_framework.md`: unified public benchmark ingestion and
  no-tuning workflow.
- `public_benchmark_results_baseline.md`: historical no-tuning public benchmark
  execution inventory.
- `tschamut_public_benchmark_reproduction.md`: public Tschamut reproduction
  workflow and registration-reviewed benchmark context.
- `public_tschamut_all_runs_grouped_validation.md`: grouped all-runs public
  Tschamut validation report.
- `public_tschamut_failure_mode_analysis.md`: grouped Tschamut failure-mode
  analysis.
- `tschamut_public_conditional_pilot_gate_report.md`: selected public
  conditional pilot gate report.
- `tschamut_public_ensemble_feasibility.md`: selected-domain ensemble
  feasibility gate.
- `chant_sura_contact_validation.md`: Chant Sura trajectory/contact validation.
- `chant_sura_contact_generalization.md`: held-out Chant Sura split.
- `tschamut_public_obstacle_context_scope.md`: forest/obstacle omission scope
  record.

## Diagnostics And Experimental Work

- `stopping_behavior_diagnostic_report.md`: no-tuning stopping-behavior
  diagnostic schema and evidence.
- `terrain_material_interaction_protocol.md`: implemented stop-state,
  last-impact, and exposure provenance for terrain/material diagnostics.
- `terrain_material_diagnostic_gap_report.md`: remaining gaps before
  terrain/material calibration or model-selection work.
- `terrain_material_interaction_diagnostic_protocol.md`: no-tuning protocol for
  terrain/material diagnostics.
- `terrain_material_diagnostic_matrix.md`: first terrain/material diagnostic
  matrix using explicit stop-state fields where available.
- `impact_diagnostics.md`: optional per-impact event logging fields.
- `shape_aware_block_scaffold_design.md`: passive shape metadata scaffold
  design.
- `shape_metadata_application_plan.md`: passive shape metadata application plan.
- `active_shape_contact_design.md`: design-only active shape-contact proposal.
- `shape_contact_v0_experimental_contract.md`: frozen experimental contract for
  `shape_contact_v0`.
- `shape_contact_v0_runtime_wiring_plan.md`: design-only runtime wiring plan.
- `shape_contact_v0_internal_validation_progression.md`: internal-only
  validation-style smoke progression.
- `shape_contact_v0_chant_sura_internal_model_selection.md`: internal
  model-selection result.
- `shape_contact_v0_rebound_diagnostic_audit.md`: rebound/provenance audit and
  pause rationale.

## Performance And Output Evidence

- `performance_benchmarking.md`: lightweight benchmark instrumentation and
  profiles.
- `performance_ci_tracking.md`: CI benchmark baseline comparison and main-trend
  visualization workflow.
- `performance_benchmark_profile_reference.md`: current benchmark profile
  reference.
- `performance_benchmark_results_initial.md`: initial timing and output-volume
  results.
- `performance_benchmark_synthetic_scale.md`: opt-in synthetic scale benchmark
  design.
- `performance_benchmark_synthetic_scale_results.md`: measured synthetic scale
  results.
- `parquet_impact_benchmark_results.md`: Parquet impact-event benchmark.
- `hazard_throughput_bottleneck_report.md`: hazard input-throughput
  bottleneck observations.
- `hazard_workflow_scale_review.md`: hazard-layer stress-test and Swiss-scale
  requirements.
- `hazard_output_profile_contract.md`: profile-level output contracts for
  conditional hazard runs (`full_debug`, `scalable_conditional`,
  `provenance_audit`).
- `large_scale_execution_probe.md`: projection-only large-scale conditional
  execution estimator and planning assumptions.

## Background And Older Model Work

These documents remain for implementation traceability, but they are not the
starting point for new roadmap decisions:

- `literature_review.md`
- `verification_plan.md`
- `model_review_v0.md`
- `model_review_v0_3.md`
- `model_gap_analysis_v0_3.md`
- `scarring_contact_v1_review.md`
- `scarring_impact_inspection.md`
- `scarring_single_impact_calibration.md`
- `scarring_real_data_calibration.md`
- `tschamut_scarring_experiment.md`
- `weighted_hazard_layer_review.md`
- `ramms_gap_analysis.md`
- `model_benchmark_execution_report.md`
- `model_overall_assessment_report.md`
- `expert_review_briefing.md`

## Documentation Maintenance

When updating docs:

- Prefer updating a governing document or current roadmap over adding another
  standalone report.
- Put long-lived sequencing decisions in `decision_log.md`.
- Treat benchmark/result snapshots as historical unless regenerated with the
  current code and current command paths.
- Do not duplicate raw data, generated result directories, or large geospatial
  outputs in `docs/`.
- After removing or renaming docs, run `python3 scripts/check_repo_consistency.py`
  and search for stale references.

Version notes are tracked in `../CHANGELOG.md`.
