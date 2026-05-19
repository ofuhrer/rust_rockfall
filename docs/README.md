# Documentation Index

Current project version: `v0.6.1`.

Use this index as the authority map for current work. Top-level docs should be
current, actionable, or canonical evidence summaries. Historical reports and
superseded planning notes live under `archive/` and should not be used as
starting context for implementation unless a task explicitly asks for them.

## Status Taxonomy

- `governing`: source of truth for scope, claims, or workflow rules.
- `current_workflow`: actively used runbook, contract, or helper documentation.
- `evidence_summary`: canonical measured or fixture-backed evidence summary.
- `archived_evidence`: historical measured evidence preserved for traceability.
- `superseded`: replaced by a named current document.
- `inactive_contract`: future-schema or gate placeholder, not active workflow.

## Governing

- `../README.md`: project overview, quickstart, scope, and current caveats.
- `../AGENTS.md`: automated-agent rules, hard boundaries, and worker fast path.
- `task_backlog.md`: authoritative executable TB queue.
- `current_maturity_snapshot.md`: current maturity, capability gaps, and
  backlog-quality framing.
- `decision_log.md`: durable design and sequencing decisions.
- `agent_work_log.md`: concise chronological TB execution history.
- `onboarding.md`: local setup, hooks, checks, and clean handoff rules.
- `orchestration_strategy.md`: sequential worker execution strategy.
- `agent_reference.md`: detailed policy for broad model, output, versioning,
  HPC, and review changes.
- `project_overview.md`: detailed background reference kept out of the root
  README.

## Model, Validation, And Claims

- `model_design.md`: current equations, assumptions, terrain conventions,
  contact models, API boundaries, and reproducibility model.
- `architecture_boundaries.md`: module responsibility map, large-file refactor
  targets, panic/error boundaries, and scaling boundary.
- `validation_plan.md`: validation strategy, dataset policy, metrics, and
  calibration separation.
- `validation_maturity_framework.md`: evidence levels and allowed claim types.
- `validation_data_schema.md`: validation-case and validation-data schema.
- `verification_plan.md`: verification scope and current checked-in
  verification workflow.
- `dataset_strategy.md`: calibration, validation, pilot, and operational-input
  dataset separation.
- `datasets.md`: public dataset registry, download, preprocessing, and
  calibration-data notes.
- `literature_review.md`: public literature and grey-literature reference
  context.
- `hazard_map_semantics.md`: allowed/disallowed hazard-map language,
  denominator rules, and hazard-versus-risk boundary.
- `hazard_layers.md`: hazard-layer builder behavior, raster outputs, and
  current layer semantics.
- `hazard_output_profile_contract.md`: `full_debug`,
  `scalable_conditional`, and `provenance_audit` output profiles.
- `stochastic_sampling_rng_stream_audit.md`: stochastic stream audit and
  deterministic sampling evidence.

## Current Swiss Workflow

- `swisstopo_data_strategy.md`: Swiss public geodata roles, metadata
  requirements, AOI automation gaps, and second-site boundaries.
- `public_real_site_geodata_preparation.md`: public real-site geodata manifest
  and run-freeze workflow.
- `public_real_site_conditional_pilot_report_template.md`: template for
  conditional pilot reporting without operational claim upgrades.
- `source_zone_block_scenario_policy_v1.md`: conditional source-zone and
  block-scenario policy contract.
- `swiss_terrain_ingestion_pilot.md`: minimal terrain-source, release-zone,
  and terrain-class metadata contracts.
- `terrain_model.md`: retained terrain-model record required by model
  consistency checks.
- `pilot_gis_package.md`: diagnostic QGIS/GeoTIFF package contract.
- `dem_terrain_sensitivity_benchmark.md`: dry-runnable DEM/terrain sensitivity
  fixture and real-site scaffold.
- `chant_sura_fluelapass_real_context_acquisition_decision.md`: deferred
  second-site public-context staging decision and operator checklist.

## Current Balfrin And Tschamut Evidence

- `balfrin_probe_slurm_driver.md`: SLURM-first Balfrin probe driver.
- `balfrin_remote_checkout_hygiene_tb304.md`: TB-304 before/after remote
  checkout cleanup record for stale generated Balfrin files.
- `balfrin_skills.md`: practical Balfrin cluster-discovery notes.
- `balfrin_minimal_demo_vs_closure.md`: minimal demo versus scientific closure
  boundary pointer retained because active Balfrin contracts cite it.
- `balfrin_post_run_interpretation_gate.md`: post-run interpretation gate and
  closure boundary.
- `balfrin_failure_recovery_playbook.md`: failure/recovery playbook for the
  current Balfrin pilot path.
- `balfrin_restartability_recovery_report.md`: restartability/recovery
  evidence summary consumed by the Balfrin evidence bundle.
- `balfrin_single_job_execution_sufficiency.md`: canonical Balfrin runtime,
  output, restartability, reducer, metrics, and scale-boundary summary.
- `balfrin_tschamut_pilot_runbook.md`: reusable Balfrin Tschamut pilot
  operating procedure.
- `balfrin_tschamut_readiness.md`: read-only readiness checker documentation.
- `target_area_physical_evidence_acquisition_pack.md`: target-area
  physical-evidence acquisition pack; not an annual/physical authorization.
- `tschamut_public_conditional_pilot_gate_report.md`: selected public
  conditional pilot gate report.
- `tschamut_public_same_scale_uncertainty_envelope.md`: same-scale uncertainty
  envelope and closure-limiting layers.
- `tschamut_public_bounded_validation_output_profile.md`: validation-output
  pressure and reduced-output evidence.
- `tschamut_public_scalable_conditional_target_gate.md`: selected Tschamut
  scalable conditional target-gate record.
- `tschamut_public_scalable_conditional_execution.md`: scalable conditional
  execution design and diagnostics contract.
- `tschamut_public_ensemble_feasibility.md`: bounded ensemble feasibility
  record for the selected public pilot.
- `tschamut_public_obstacle_context_scope.md`: obstacle/context scope record
  used by closure and consistency helpers.
- `tschamut_public_pilot_gis_package_review.md`: local GIS package review
  record retained because tracked pilot records cite it.
- `tschamut_public_pilot_scaling_review.md`: local scaling and output-volume
  evidence retained because validators and pilot records cite it.
- `tschamut_swissalti3d_pilot.md`: current swissALTI3D public-pilot context.
- `conditional_hazard_convergence_acceptance_protocol.md`: current conditional
  hazard convergence protocol.
- `output_budget_reducer_scaling_gate.md`: output-budget and reducer scaling
  gate.
- `real_site_dem_input_conditioning_qa_gate.md`: DEM/input conditioning QA gate.

## Benchmarks And Diagnostics

- `benchmark_catalog.md`: implemented verification and validation inventory.
- `public_benchmark_framework.md`: unified public benchmark ingestion and
  no-tuning workflow.
- `public_benchmark_results_baseline.md`: no-tuning public benchmark inventory.
- `tschamut_public_benchmark_reproduction.md`: public Tschamut reproduction
  workflow and registration-reviewed context.
- `public_tschamut_all_runs_grouped_validation.md`: grouped public Tschamut
  validation report.
- `public_tschamut_failure_mode_analysis.md`: grouped public Tschamut
  failure-mode analysis.
- `chant_sura_contact_validation.md`: Chant Sura contact validation.
- `chant_sura_contact_generalization.md`: held-out Chant Sura split.
- `stopping_behavior_diagnostic_report.md`: no-tuning stopping diagnostics.
- `terrain_material_interaction_protocol.md`: implemented terrain/material
  diagnostic instrumentation.
- `terrain_material_interaction_diagnostic_protocol.md`: no-tuning
  terrain/material diagnostic protocol.
- `terrain_material_diagnostic_gap_report.md`: terrain/material calibration
  and model-selection gaps.
- `terrain_material_diagnostic_matrix.md`: first terrain/material matrix.
- `impact_diagnostics.md`: optional per-impact event logging fields.

## Calibration And Historical Research Records

These remain top-level only because current consistency checks, calibration
scripts, or validation docs still cite them directly. They are research
diagnostics, not accepted calibration or physical-credibility evidence.

- `tschamut_calibration.md`: v0.3.0 Tschamut calibration experiment record.
- `tschamut_scarring_experiment.md`: Tschamut scarring comparison record.
- `scarring_single_impact_calibration.md`: proxy single-impact scarring
  calibration record.
- `scarring_real_data_calibration.md`: Chant Sura table-derived
  single-impact scarring calibration record.

## Experimental Or Deferred

- `active_shape_contact_design.md`: design-only active shape-contact proposal.
- `shape_aware_block_scaffold_design.md`: passive shape metadata scaffold.
- `shape_metadata_application_plan.md`: passive shape metadata application
  plan.
- `shape_contact_v0_experimental_contract.md`: frozen experimental contract.
- `shape_contact_v0_runtime_wiring_plan.md`: design-only runtime wiring plan.
- `shape_contact_v0_internal_validation_progression.md`: internal-only smoke
  progression.
- `shape_contact_v0_chant_sura_internal_model_selection.md`: internal model
  selection result.
- `shape_contact_v0_rebound_diagnostic_audit.md`: rebound/provenance audit and
  pause rationale.

## Inactive Physical/Annual Contracts

These are retained as `inactive_contract` records. They do not enable annual
frequency, physical probability, return-period, risk, exposure, vulnerability,
or operational products.

- `physical_source_frequency_design_gate.md`
- `source_frequency_evidence_contract.md`
- `block_release_probability_evidence_contract.md`
- `physical_frequency_reducer_preconditions.md`
- `annual_physical_validation_calibration_review_gate.md`
- `annual_physical_prototype_preflight.md`
- `probabilistic_scenario_model_design.md`
- `probabilistic_trajectory_metadata_design.md`
- `probabilistic_hazard_phase1_closure.md`

## Performance And Scaling

- `performance_benchmarking.md`: benchmark instrumentation and profiles.
- `performance_ci_tracking.md`: CI benchmark comparison and trend
  visualization workflow.
- `performance_benchmark_profile_reference.md`: current benchmark profile
  reference.
- `performance_benchmark_synthetic_scale.md`: opt-in synthetic scale
  benchmark design.
- `parquet_impact_benchmark_results.md`: Parquet impact-event benchmark.
- `hazard_throughput_bottleneck_report.md`: hazard input-throughput
  observations.
- `hazard_workflow_scale_review.md`: hazard-layer stress test and Swiss-scale
  requirements.
- `large_scale_execution_probe.md`: projection-only execution estimator.
- `multi_zone_reducer_pressure_probe.md`: scratch-root multi-zone reducer
  pressure probe.

## Archive And Script Inventory

- `archive/README.md`: archived and superseded docs preserved for traceability.
- `script_inventory.md`: script tiers, deletion policy, and high-risk workflow
  CLIs that must not be moved in the first cleanup pass.
- `next_development_targets.md`: legacy pointer kept only for old links; do not
  add current priorities there.
- `roadmap_recommendation_matrix.md`: supporting scoring appendix, not the
  active queue.
- `roadmap_hazard_mapping.md`: long-term roadmap.
- `real_case_intensity_frequency_implementation_roadmap.md`: long-term staged
  roadmap toward future physical/annual semantics, not current task authority.
- `scalability_and_data_formats_review.md`: historical planning review with
  current notes where implemented.

## Maintenance Rules

- Prefer updating a governing or current workflow document over adding a new
  standalone report.
- Put durable decisions in `decision_log.md` and completed TB execution in
  `agent_work_log.md`.
- Move superseded reports to `archive/` instead of leaving them top-level with
  current-looking titles.
- Do not treat archived evidence as current maturity unless a current summary
  cites and interprets it.
- After moving docs or changing command references, run:

```bash
PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py
```

Version notes are tracked in `../CHANGELOG.md`.
