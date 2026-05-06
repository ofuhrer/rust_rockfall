# Documentation Index

Current project version: `v0.6.0`.

The repository uses semantic versioning:

- `MAJOR`: breaking physics or output changes, including changing a default model.
- `MINOR`: new opt-in physics or model capabilities that preserve existing defaults.
- `PATCH`: bug fixes, documentation, and test improvements.

Core documents:

- `model_design.md`: current equations, assumptions, model options, and API boundaries.
- `roadmap_hazard_mapping.md`: long-term roadmap toward probabilistic Alpine hazard-map layers and the boundary between hazard and risk modelling.
- `swisstopo_data_strategy.md`: authoritative Swiss geodata roles, swissALTI3D terrain-ingestion metadata, and first pilot workflow design.
- `swiss_terrain_ingestion_pilot.md`: minimal runtime terrain-source, release-zone, and terrain-class metadata contracts with checked-in swissALTI3D-style pilot fixtures.
- `tschamut_swissalti3d_pilot.md`: local/private Tschamut real-site pilot workflow using a manually supplied swissALTI3D-style DEM crop, source-area metadata, optional terrain classes, and existing hazard layers.
- `tschamut_swissalti3d_controlled_pilot_plan.md`: concrete Work Package 1 execution plan for the controlled Tschamut/swissALTI3D real-site pilot, including private inputs, commands, metrics, QA, and interpretation rules.
- `tschamut_public_benchmark_reproduction.md`: registration-reviewed public-data Tschamut benchmark reproduction workflow using EnviDat observations, a public swissALTI3D terrain crop, explicit-grid hazard layers, and no parameter tuning.
- `public_tschamut_model_improvement_decision.md`: no-tuning decision record choosing the next scientific model-improvement direction after the registered public Tschamut benchmark.
- `shape_aware_block_scaffold_design.md`: design-only plan for an opt-in passive block shape, orientation, and inertia metadata scaffold before any non-spherical contact physics.
- `shape_metadata_application_plan.md`: practical plan for attaching passive public block-shape metadata to Tschamut and Chant Sura validation cases without changing dynamics or tuning parameters.
- `swisstopo_terrain_tile_schema.yaml`: schema-style metadata example for future swisstopo terrain tile ingestion.
- `dataset_strategy.md`: multi-dataset roles for physics calibration, trajectory validation, deposition validation, and hazard mapping.
- `chant_sura_contact_validation.md`: DEM-backed segmented Chant Sura trajectory/contact validation setup, metrics, and model-comparison results.
- `chant_sura_contact_generalization.md`: held-out Chant Sura split and generalization test for `sphere_rotational_v1`.
- `contact_model_decision.md`: decision record recommending `sphere_rotational_v1` for trajectory-validation experiments while preserving `translational_v0` as the default.
- `post_ce3959d_next_step_decision.md`: post-`ce3959d` current-state review, operational-capability gap analysis, and next-step decision for Swiss hazard-mapping readiness.
- `post_swiss_pilot_stack_next_step_decision.md`: decision record after the swissALTI3D-style terrain, release-zone, terrain-class, and hazard-exceedance pilot stack.
- `v0_5_next_steps_review.md`: current-state review after `v0.5.0`, key scientific findings, prioritized roadmap, and recommended next actions.
- `chant_sura_model_improvement_evaluation.md`: comparison of candidate model options against the Chant Sura trajectory subset.
- `hazard_layers.md`: first post-processing workflow for diagnostic reach, deposition, energy, jump-height, and impact-density layers.
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
- `probabilistic_trajectory_metadata_design.md`: design and current implementation status for carrying per-trajectory release, block, scenario, and sampling-weight metadata into opt-in weighted hazard maps and future columnar outputs.
- `probabilistic_hazard_framework_priorities.md`: prioritized roadmap for moving from unweighted diagnostic hazard layers toward explicit probabilistic hazard-map semantics.
- `probabilistic_scenario_model_design.md`: scenario-level semantics for conditional source-zone hazard maps, source-frequency placeholders, block scenarios, probability modes, and normalization conventions.
- `weighted_hazard_layer_review.md`: semantic review of the `v0.6.0` sampling-weighted hazard-layer prototype and recommended next engineering step.
- `current_state_gap_analysis_next_directions.md`: strategic post-benchmark current-state review, gap analysis against the state of practice, and recommended next work packages.
- `verification_plan.md`: analytic and synthetic verification strategy.
- `validation_plan.md`: public-data validation strategy and calibration policy.
- `benchmark_catalog.md`: implemented verification and validation case inventory.
- `validation_data_schema.md`: YAML case and validation-data schema.
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

Version notes are tracked in `../CHANGELOG.md`.
