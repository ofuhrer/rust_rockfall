# Documentation Guide

This folder is intentionally a working reference, not a complete history of
every experiment. Start with the documents below and follow links only when a
task needs more detail.

Current project version: `v0.6.1`.

## Start Here

- `../README.md`: project overview, quickstart, and current demonstration
  snapshot.
- `onboarding.md`: local setup, checks, and handoff rules.
- `aoi_user_manual.md`: compact user-facing AOI workflow.
- `swiss_scale_feasibility_projection.md`: current Balfrin and Swiss-scale
  feasibility evidence.
- `current_maturity_snapshot.md`: detailed capability and gap assessment.
- `task_backlog.md`: active executable task queue.
- `agent_work_log.md`: completed task history.

## Core Model And Workflow

- `model_design.md`: current model equations, assumptions, and API boundaries.
- `architecture_boundaries.md`: module boundaries and scaling constraints.
- `validation_plan.md`: validation strategy and calibration separation.
- `validation_data_schema.md`: validation case and validation data schema.
- `public_benchmark_framework.md`: public benchmark ingestion and no-tuning
  workflow.
- `hazard_map_semantics.md`: allowed hazard-map language and claim boundaries.
- `hazard_layers.md`: hazard-layer builder behavior and output semantics.
- `aoi_conditional_workflow_contract.md`: AOI conditional-map phase model.
- `swisstopo_data_strategy.md`: Swiss public geodata strategy.
- `public_real_site_geodata_preparation.md`: real-site geodata preparation and
  review workflow.

## Current Evidence

- `balfrin_scale_demonstration_management_package.md`: concise Balfrin evidence
  synthesis.
- `balfrin_diagnostic_series_tb613.md`: measured diagnostic reducer-pressure
  series through 100 release zones.
- `balfrin_hazard_throughput_run_tb603.md`: bounded Balfrin hazard-throughput
  support run.
- `source_frequency_evidence_tb614.md`: staged source-frequency design-review
  evidence.
- `holdout_runout_deposition_evidence_tb615.md`: staged held-out runout-axis
  benchmark intake.
- `large_aoi_gis_cog_stress_tb609.md`: current larger-output GIS/COG pressure
  evidence.

## Operational References

- `balfrin_skills.md`: practical Balfrin notes.
- `balfrin_tschamut_pilot_runbook.md`: reusable Balfrin Tschamut pilot
  procedure.
- `balfrin_failure_recovery_playbook.md`: Balfrin failure and recovery notes.
- `hazard_output_profile_contract.md`: output profiles and reduced-output
  behavior.
- `performance_ci_tracking.md`: CI benchmark trend publication.
- `script_inventory.md`: script tiers and cleanup policy.

## Maintenance Rule

Keep this guide short. Prefer improving one of the current documents above over
adding another standalone report. Historical planning notes and superseded
reviews should be deleted unless a current workflow or test still depends on
them.
