# Documentation Index

Current project version: `v0.4.0`.

The repository uses semantic versioning:

- `MAJOR`: breaking physics or output changes, including changing a default model.
- `MINOR`: new opt-in physics or model capabilities that preserve existing defaults.
- `PATCH`: bug fixes, documentation, and test improvements.

Core documents:

- `model_design.md`: current equations, assumptions, model options, and API boundaries.
- `roadmap_hazard_mapping.md`: long-term roadmap toward probabilistic Alpine hazard-map layers and the boundary between hazard and risk modelling.
- `dataset_strategy.md`: multi-dataset roles for physics calibration, trajectory validation, deposition validation, and hazard mapping.
- `hazard_layers.md`: first post-processing workflow for diagnostic reach, deposition, energy, jump-height, and impact-density layers.
- `hazard_workflow_scale_review.md`: stress-test observations, bottlenecks, DEM/GIS gaps, and Swiss-scale requirements for hazard-layer generation.
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
