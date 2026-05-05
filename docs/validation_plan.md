# Validation Plan

Validation asks whether the current model is useful when compared with observations or published benchmarks. It does not target RAMMS::ROCKFALL equivalence and does not use proprietary datasets.

## v0 Status

Real-world validation is partial and qualitative. The current simulator is a spherical-block model with simple restitution, Coulomb friction, analytic terrain, small DEM support, and deterministic release perturbations. It cannot yet represent block-shape effects, advanced contact/scarring, explicit roughness distributions, forest interaction, fragmentation, or calibrated field-scale parameter sets.

## Dataset Policy

- Use public datasets only.
- Preserve raw files under `data/raw/<dataset_id>/` or `validation/data/raw/<dataset_id>/`.
- Store reproducible derived files under `data/processed/<dataset_id>/` or `validation/data/processed/<dataset_id>/`.
- Cite dataset title, authors, DOI, source URL, and license.
- Do not commit large raw data.
- Skip optional real-data validation gracefully when data are not downloaded.

The public dataset registry is in `data/datasets.yaml`; dataset notes are in `docs/datasets.md`.

## Commands

```bash
cargo run -- validate --case validation/cases/synthetic_plane_basic.yaml
cargo run -- validate --case validation/cases/tschamut_basic.yaml
cargo run -- validate --all
```

Missing public observations cause a skipped report with instructions rather than a CI failure.

## Metrics

Implemented validation metrics include deposition-point distance error, runout distance error, lateral deviation, final speed, impact count, max speed, max bounce height, energy diagnostics, and ensemble runout summaries where seeded perturbations are used.

Planned metrics include trajectory-envelope overlap, bounce-height time-series error, velocity and angular-velocity time-series error, runout exceedance probability, and deposition-density skill scores.

## Calibration Policy

- Verification tests must not be calibrated.
- Validation tests may reveal model deficiencies.
- Calibration experiments must be explicitly separated from validation cases.
- All tuned parameters must record dataset, objective function, parameter bounds, resulting values, and holdout validation dataset.
- Do not tune secretly to match one dataset.

Validation results must describe the model version, parameters, preprocessing, and limitations.
