# Documentation Index

Current project version: `v0.5.0`.

The repository uses semantic versioning:

- `MAJOR`: breaking physics or output changes, including changing a default model.
- `MINOR`: new opt-in physics or model capabilities that preserve existing defaults.
- `PATCH`: bug fixes, documentation, and test improvements.

Core documents:

- `model_design.md`: current equations, assumptions, model options, and API boundaries.
- `roadmap_hazard_mapping.md`: long-term roadmap toward probabilistic Alpine hazard-map layers and the boundary between hazard and risk modelling.
- `swisstopo_data_strategy.md`: authoritative Swiss geodata roles, swissALTI3D terrain-ingestion metadata, and first pilot workflow design.
- `swiss_terrain_ingestion_pilot.md`: minimal runtime terrain-source, release-zone, and terrain-class metadata contracts with checked-in swissALTI3D-style pilot fixtures.
- `swisstopo_terrain_tile_schema.yaml`: schema-style metadata example for future swisstopo terrain tile ingestion.
- `dataset_strategy.md`: multi-dataset roles for physics calibration, trajectory validation, deposition validation, and hazard mapping.
- `chant_sura_contact_validation.md`: DEM-backed segmented Chant Sura trajectory/contact validation setup, metrics, and model-comparison results.
- `chant_sura_contact_generalization.md`: held-out Chant Sura split and generalization test for `sphere_rotational_v1`.
- `contact_model_decision.md`: decision record recommending `sphere_rotational_v1` for trajectory-validation experiments while preserving `translational_v0` as the default.
- `post_ce3959d_next_step_decision.md`: post-`ce3959d` current-state review, RAMMS gap analysis, and next-step decision for Swiss hazard-mapping readiness.
- `v0_5_next_steps_review.md`: current-state review after `v0.5.0`, key scientific findings, prioritized roadmap, and recommended next actions.
- `chant_sura_model_improvement_evaluation.md`: comparison of candidate model options against the Chant Sura trajectory subset.
- `hazard_layers.md`: first post-processing workflow for diagnostic reach, deposition, energy, jump-height, and impact-density layers.
- `hazard_workflow_scale_review.md`: stress-test observations, bottlenecks, DEM/GIS gaps, and Swiss-scale requirements for hazard-layer generation.
- `scalability_and_data_formats_review.md`: end-to-end scalability, bottleneck, data-format, and staged architecture review for future large-ensemble and Swiss-scale hazard-map production.
- `hazard_layer_scientific_analysis.md`: scientific interpretation of current ensemble hazard-layer outputs and Swiss-scale readiness gaps.
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
