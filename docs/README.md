# Documentation Index

Current project version: `v0.6.1`.

Project direction: `rust_rockfall` targets automated, reproducible rockfall
hazard mapping for Switzerland's Alpine terrain from public geodata, primarily
swisstopo. The first milestone is a valley-scale pilot with pragmatic
release-zone and block-scenario generation, uncertainty-aware trajectory
ensembles, GIS-ready hazard outputs, and performance suitable for large local
and later CSCS/SLURM runs. Risk modelling, exposure/vulnerability analysis, and
operational warning systems are out of scope.

The repository uses semantic versioning:

- `MAJOR`: breaking physics or output changes, including changing a default model.
- `MINOR`: new opt-in physics or model capabilities that preserve existing defaults.
- `PATCH`: bug fixes, documentation, and test improvements.

Use this index by authority level. Current governing documents and current
roadmaps should guide new work. Evidence reports describe what was observed at
the time they were written. Historical decision records and work logs are
retained for traceability and must not override the current governing docs or
target list.

Current governing documents:

- `model_design.md`: current equations, assumptions, model options, and API boundaries.
- `onboarding.md`: generic local prerequisites, Rust/Python installation, git-hook setup, optional public benchmark data commands, and handoff checks.
- `balfrin_skills.md`: Balfrin cluster guide covering SLURM partitions, hardware, filesystems, and Rust job submission recipes.
- `roadmap_hazard_mapping.md`: long-term roadmap toward probabilistic Alpine hazard-map layers and the boundary between hazard and risk modelling.
- `validation_maturity_framework.md`: conservative V0-V5 evidence and claim levels for verification, synthetic fixtures, field validation, site-scale hazard-pattern evidence, cross-site generalization, and operational reproducibility.
- `validation_plan.md`: public-data validation strategy and calibration policy.
- `dataset_strategy.md`: multi-dataset roles for physics calibration, trajectory validation, deposition validation, and hazard mapping.
- `validation_data_schema.md`: YAML case and validation-data schema.

Current roadmaps and target lists:

- `next_development_targets.md`: current prioritized development targets after the latest repository review.
- `roadmap_recommendation_matrix.md`: current scoring matrix and prioritization rationale for near-term roadmap choices.
- `real_case_intensity_frequency_implementation_roadmap.md`: staged roadmap from current conditional intensity-exceedance pilot products to future physical-probability or annual intensity-frequency products.
- `repository_scientific_roadmap_review.md`: historical snapshot review used to seed earlier target lists; prefer `next_development_targets.md` and `real_case_intensity_frequency_implementation_roadmap.md` for current priorities when they differ.

Current implementation contracts and evidence reports:

- `probabilistic_hazard_mapping_development_roadmap.md`: staged development roadmap reframing the project around transparent, reproducible probabilistic hazard-map production for selected Swiss regions.
- `probabilistic_hazard_phase1_implementation_plan.md`: concrete Level 1-2 implementation plan for map semantics, source-zone identity, scenario tables, probability labels, normalization rules, and validation slices.
- `probabilistic_hazard_phase1_closure.md`: closure record for Phase 1 Slices B-E, defining implemented Level 1/2 probabilistic map semantics, smoke-example coverage, compatibility guarantees, and the recommended Phase 2A GIS export step.
- `swisstopo_data_strategy.md`: authoritative Swiss geodata roles, swissALTI3D terrain-ingestion metadata, and first pilot workflow design.
- `swiss_terrain_ingestion_pilot.md`: minimal runtime terrain-source, release-zone, and terrain-class metadata contracts with checked-in swissALTI3D-style pilot fixtures.
- `public_real_site_geodata_preparation.md`: Phase 1 manifest contract for share-safe public real-site swisstopo preparation before source-zone or ensemble work.
- `tschamut_swissalti3d_pilot.md`: local/private Tschamut real-site pilot workflow using a manually supplied swissALTI3D-style DEM crop, source-area metadata, optional terrain classes, and existing hazard layers.
- `tschamut_swissalti3d_controlled_pilot_plan.md`: concrete Work Package 1 execution plan for the controlled Tschamut/swissALTI3D real-site pilot, including private inputs, commands, metrics, QA, and interpretation rules.
- `tschamut_public_benchmark_reproduction.md`: registration-reviewed public-data Tschamut benchmark reproduction workflow using EnviDat observations, a public swissALTI3D terrain crop, explicit-grid hazard layers, and no parameter tuning.
- `dem_terrain_sensitivity_benchmark.md`: dry-runnable DEM/terrain-representation sensitivity fixture and real-site scaffold using fixed terrain variants, map-difference metrics, report gates, and an explicit warning not to tune contact parameters to compensate for DEM effects.
- `public_tschamut_model_improvement_decision.md`: no-tuning decision record choosing the next scientific model-improvement direction after the registered public Tschamut benchmark.
- `public_tschamut_failure_mode_analysis.md`: grouped public Tschamut failure-mode analysis by block, runout class, impact count, trajectory length, hazard-layer structure, and contact model.
- `public_tschamut_all_runs_grouped_validation.md`: Work Package 1 all-usable public Tschamut grouped-validation report covering all 80 processed shared LPS/overview runs, exclusions, QA, hazard structure, and next-step criteria.
- `active_shape_contact_design.md`: design-only Work Package 2 plan for a minimal opt-in active shape-contact model evaluated against WP1 Tschamut and Chant Sura evidence before implementation.
- `shape_contact_v0_experimental_contract.md`: frozen experimental contract for the first `shape_contact_v0` feasibility prototype, including implementation boundaries, diagnostics, no-tuning gates, falsification rules, and explicit deferrals.
- `shape_contact_v0_runtime_wiring_plan.md`: design-only plan for the smallest future fixed-step integrator wiring slice, including call path, diagnostic writer, manifest requirements, runtime guards, tests, and stop conditions.
- `shape_contact_v0_internal_validation_progression.md`: internal-only smoke-case gate for `shape_contact_v0`, recording the tracked `validation/internal` fixture, frozen diagnostics, public-exclusion rules, and Chant Sura decision boundary.
- `shape_contact_v0_chant_sura_internal_model_selection.md`: internal-only Chant Sura model-selection result for `shape_contact_v0`, including frozen-gate metrics, diagnostic/provenance checks, and the current failed/uncertain decision.
- `shape_contact_v0_rebound_diagnostic_audit.md`: internal-only audit of the Chant Sura `shape_contact_v0` rebound failure and unresolved trajectory-to-EOTA shape provenance blocker.
- `post_shape_contact_v0_pause_next_step.md`: decision record pausing `shape_contact_v0` runtime progression and choosing no-tuning stopping-behavior diagnostics as the next scientific work package.
- `stopping_behavior_diagnostic_report.md`: no-tuning diagnostic report and schema for existing stopping, contact-state, final-speed, runout, and instrumentation-gap evidence after pausing `shape_contact_v0`.
- `terrain_material_interaction_protocol.md`: additive implementation record for final-stop, last-significant-impact, significant-impact sequence, and trajectory exposure terrain/material class provenance in `stop_state`, ensemble sidecars, manifests, and summaries.
- `terrain_material_diagnostic_gap_report.md`: no-tuning gap report for the current terrain/material diagnostic subsystem, including remaining provenance gaps before calibration or model-selection work.
- `terrain_material_interaction_diagnostic_protocol.md`: no-tuning protocol for using explicit stop-state provenance to diagnose terrain/material interaction hypotheses before any material-parameter implementation or calibration.
- `terrain_material_diagnostic_matrix.md`: first no-tuning terrain/material diagnostic matrix using explicit `stop_state` where available, labelled proxy fallback for older deposition-focused evidence, and the next step to repeat the matrix with ensemble stop-state sidecars.
- `shape_aware_block_scaffold_design.md`: design-only plan for an opt-in passive block shape, orientation, and inertia metadata scaffold before any non-spherical contact physics.
- `shape_metadata_application_plan.md`: practical plan for attaching passive public block-shape metadata to Tschamut and Chant Sura validation cases without changing dynamics or tuning parameters.
- `public_tschamut_shape_metadata_milestone.md`: concise scientific milestone report after the registered public Tschamut benchmark, passive shape scaffold, Tschamut sidecars, and inertness validation.
- `swisstopo_terrain_tile_schema.yaml`: schema-style metadata example for future swisstopo terrain tile ingestion.
- `public_benchmark_framework.md`: unified public benchmark ingestion, provenance, grouped-validation, and no-tuning workflow for Tschamut, Chant Sura, Chant Sura EOTA221, and Mel de la Niva.
- `public_benchmark_results_baseline.md`: first no-tuning execution inventory for the unified public benchmark framework, including Tschamut all-runs metrics, Chant Sura contact metrics, passive EOTA221 QA, and Mel de la Niva opt-in runnable smoke status.
- `model_benchmark_execution_report.md`: expert-review benchmark execution package summarizing executed datasets, commands, grouped metrics, hazard-layer examples, probabilistic smoke evidence, provenance, and reproducibility limits.
- `model_overall_assessment_report.md`: strategic current-model maturity assessment covering strengths, weaknesses, systematic failure modes, hazard-map readiness, GIS readiness, and operational limitations.
- `expert_review_briefing.md`: concise practitioner-facing briefing with the key evidence, review questions, pending decisions, and materials for external scientific and operational discussion.
- `expert_review_release_note.md`: release/tag preparation note for the proposed `v0.6.0-expert-review-baseline` frozen review state, including included scope, exclusions, commands, artifact policy, reviewer workflow, and version-bump assessment.
- `chant_sura_contact_validation.md`: DEM-backed segmented Chant Sura trajectory/contact validation setup, metrics, and model-comparison results.
- `chant_sura_contact_generalization.md`: held-out Chant Sura split and generalization test for `sphere_rotational_v1`.
- `contact_model_decision.md`: decision record recommending `sphere_rotational_v1` for trajectory-validation experiments while preserving `translational_v0` as the default.
- `chant_sura_model_improvement_evaluation.md`: comparison of candidate model options against the Chant Sura trajectory subset.
- `hazard_layers.md`: first post-processing workflow for diagnostic reach, deposition, energy, jump-height, and impact-density layers.
- `pilot_gis_package.md`: diagnostic GIS/QGIS review-package contract, GeoTIFF/parity expectations, visual-QA gate, and current package manifest boundary.
- `tschamut_public_obstacle_context_scope.md`: selected Tschamut forest/obstacle omission scope record, classifying current omission as limiting without adding obstacle physics or risk semantics.
- `hazard_workflow_scale_review.md`: stress-test observations, bottlenecks, DEM/GIS gaps, and Swiss-scale requirements for hazard-layer generation.
- `scalability_and_data_formats_review.md`: end-to-end scalability, bottleneck, data-format, and staged architecture review for future large-ensemble and Swiss-scale hazard-map production.
- `hazard_layer_scientific_analysis.md`: scientific interpretation of current ensemble hazard-layer outputs and Swiss-scale readiness gaps.
- `performance_benchmarking.md`: lightweight runtime/manifest instrumentation and CI-safe plus private benchmark recipes.
- `performance_benchmark_results_initial.md`: first measured timing and output-volume results from the smoke and synthetic Swiss pilot benchmark runs.
- `performance_benchmark_synthetic_scale.md`: opt-in synthetic scale benchmark for stress-testing simulation, CSV output, impact-event output, hazard accumulation, plotting, and file count before changing data formats.
- `performance_benchmark_synthetic_scale_results.md`: measured synthetic scale benchmark results and engineering recommendation based on the 50/100/200 release matrix.
- `performance_benchmark_profile_reference.md`: canonical smoke, standard, custom, and scale profile validation after the benchmark-profile refactor.
- `parquet_impact_benchmark_results.md`: measured comparison of opt-in Parquet impact-event output against per-trajectory CSV impact-event output at 500/1000 release scale.
- `columnar_output_design_decision.md`: design decision for opt-in batched Parquet/Arrow impact and trajectory outputs based on the 500/1000 synthetic benchmark.
- `trajectory_parquet_next_step_decision.md`: benchmark-backed decision record on whether full trajectory CSV output is now the dominant bottleneck and whether opt-in trajectory Parquet is justified.
- `hazard_accumulation_architecture_decision.md`: benchmark-backed decision record for the next hazard-accumulation scalability step before adding more output formats.
- `hazard_throughput_bottleneck_report.md`: first measured use of hazard input-throughput counters, identifying auto-grid bounds discovery and trajectory accumulation as the next optimization targets.
- `ramms_gap_analysis.md`: public-evidence comparison between the local open simulator and publicly documented RAMMS::ROCKFALL capabilities, with scientific, GIS, validation, and engineering gap priorities.
- `post_ramms_gap_next_work_packages.md`: staged no-tuning roadmap translating the RAMMS gap analysis into grouped public Tschamut validation, shape-contact design, conditional model/calibration work, and GIS export follow-up packages.
- `probabilistic_trajectory_metadata_design.md`: design and current implementation status for carrying per-trajectory release, block, scenario, and sampling-weight metadata into opt-in weighted hazard maps and future columnar outputs.
- `probabilistic_hazard_framework_priorities.md`: prioritized roadmap for moving from unweighted diagnostic hazard layers toward explicit probabilistic hazard-map semantics.
- `probabilistic_scenario_model_design.md`: scenario-level semantics for conditional source-zone hazard maps, source-frequency placeholders, block scenarios, probability modes, and normalization conventions.
- `source_zone_block_scenario_policy_v1.md`: Phase 2 policy contract for predeclared real-site source-zone evidence, deterministic release sampling, and representative block scenarios.
- `public_real_site_geodata_preparation.md`: Phase 1/6 share-safe public real-site geodata manifest and conditional pilot run-freeze workflow.
- `public_real_site_conditional_pilot_report_template.md`: Phase 6 report scaffold for pass/no-go/inconclusive local conditional pilot classification.
- `tschamut_public_conditional_pilot_gate_report.md`: selected Tschamut public conditional pilot gate report for the reconciled local ignored gate evidence and remaining inconclusive interpretation boundaries.
- `weighted_hazard_layer_review.md`: semantic review of the `v0.6.0` sampling-weighted hazard-layer prototype and recommended next engineering step.
- `autonomous_development_program.md`: operator prompt, tracking artifacts, and Git/GitHub conventions for long-running autonomous development sessions.
- `verification_plan.md`: analytic and synthetic verification strategy.
- `benchmark_catalog.md`: implemented verification and validation case inventory.
- `impact_diagnostics.md`: optional per-impact event logging fields and interpretation guide.
- `implementation_plan.md`: phased implementation roadmap.
- `literature_review.md`: public literature and grey-literature sources.
- `model_review_v0_3.md`: rationale for the first opt-in impact roughness model.
- `model_gap_analysis_v0_3.md`: theory-informed rationale for the minimal opt-in scarring model.
- `scarring_contact_v1_review.md`: calibration-readiness review for the minimal scarring model.
- `scarring_impact_inspection.md`: manual reconstruction of representative synthetic scarring impacts.
- `scarring_single_impact_calibration.md`: first controlled single-impact scarring calibration workflow.
- `scarring_real_data_calibration.md`: first real-data single-impact scarring calibration experiment using public Chant Sura / ESurf 2019 tables.
- `tschamut_scarring_experiment.md`: controlled Tschamut baseline versus transferred impact-level `scarring_contact_v1` comparison.

Historical decision records and superseded roadmap context:

- `post_ce3959d_next_step_decision.md`: post-`ce3959d` current-state review, retained as historical context.
- `post_swiss_pilot_stack_next_step_decision.md`: decision record after the swissALTI3D-style terrain, release-zone, terrain-class, and hazard-exceedance pilot stack.
- `v0_5_next_steps_review.md`: current-state review after `v0.5.0`, retained as historical context.
- `current_state_gap_analysis_next_directions.md`: older strategic post-benchmark gap analysis. Use current planning documents such as `next_development_targets.md`, `real_case_intensity_frequency_implementation_roadmap.md`, `roadmap_recommendation_matrix.md`, and this index when priorities conflict.

Version notes are tracked in `../CHANGELOG.md`.
