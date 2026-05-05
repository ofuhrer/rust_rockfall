# Validation Plan

Validation asks whether the current model is useful when compared with observations or published benchmarks. It does not target RAMMS::ROCKFALL equivalence and does not use proprietary datasets.

## v0 Status

Real-world validation is partial and qualitative. The current simulator is a spherical-block model with simple restitution, Coulomb friction, opt-in rotational sphere contact, opt-in stochastic contact roughness, analytic terrain, small DEM support, and deterministic release perturbations. It cannot yet represent block-shape effects, advanced contact/scarring, calibrated spatial roughness distributions, forest interaction, fragmentation, or calibrated field-scale parameter sets.

## Dataset Policy

- Use public datasets only.
- Preserve raw files under `data/raw/<dataset_id>/` or `validation/data/raw/<dataset_id>/`.
- Store reproducible derived files under `data/processed/<dataset_id>/` or `validation/data/processed/<dataset_id>/`.
- Cite dataset title, authors, DOI, source URL, and license.
- Do not commit large raw data.
- Keep large real-data validation optional; small license-compatible derived fixtures may be checked in for CI smoke tests.

The public dataset registry is in `data/datasets.yaml`; dataset notes are in `docs/datasets.md`.

## Commands

```bash
cargo run -- validate --case validation/cases/synthetic_plane_basic.yaml
cargo run -- validate --case validation/cases/tschamut_basic.yaml
cargo run -- validate --all
```

Missing optional public observations cause a skipped report with instructions rather than a CI failure. The checked-in Tschamut subset is intentionally small enough for local and CI validation smoke tests.

## Metrics

Implemented validation metrics include deposition-point distance error, runout distance error, lateral deviation, deposition centroid error, deposition-cloud mean nearest-neighbor distance, deposition-cloud overlap fraction, final speed, impact count, max speed, max bounce height, energy diagnostics, rolling residual/contact diagnostics, and ensemble runout summaries where seeded perturbations are used.
Roughness-specific verification metrics include zero-roughness baseline comparison and different-seed ensemble runout deltas.

Planned metrics include trajectory-envelope overlap, bounce-height time-series error, velocity and angular-velocity time-series error, runout exceedance probability, and deposition-density skill scores.

## Real-World Validation Interpretation

The Tschamut 2014 case is a limited distribution-level comparison against public-derived release and deposition points. It validates only that the v0.3.0 workflow can ingest public observations, run deterministic ensembles, and report interpretable mismatch metrics. It does not validate individual paths or operational hazard skill.

Terrain representation is part of the validation assumption set. `validation_tschamut_proxy_plane` keeps the earlier fitted-plane terrain approximation as an explicit structural-error comparison, while `validation_tschamut_basic` uses the `idw_residual_dem_from_lps` clamped DEM proxy derived from public LPS ground points. Neither terrain is an official field DEM.

For real-world cases:

- distributions matter more than individual paths for the current model;
- mismatch is expected and should identify missing physics, such as block shape, calibrated roughness, vegetation, and richer terrain representation;
- roughness parameters in validation cases are generic model settings, not tuned Tschamut calibration;
- a passing status means the workflow completed and reported metrics, not that the model is field-accurate.

## Reproducibility Criteria

Validation and benchmark workflows must preserve deterministic reproducibility:

- identical trajectory inputs and seed produce identical samples and summaries;
- different trajectory seeds produce distinct perturbed releases when perturbation ranges are nonzero;
- opt-in contact roughness is driven by trajectory-specific seeds and is reproducible for the same trajectory identity;
- ensemble trajectory seeds are derived from global seed, case ID, and trajectory ID;
- per-trajectory results are independent of execution order;
- optional real-world validation cases must skip cleanly when data are absent rather than changing deterministic test behavior.

These criteria support future large ensemble execution without making current validation depend on MPI, GPUs, or distributed schedulers.

## Calibration Policy

- Verification tests must not be calibrated.
- Validation tests may reveal model deficiencies.
- Calibration experiments must be explicitly separated from validation cases.
- Calibration experiments live under `calibration/`; generated intermediate outputs live under ignored `calibration/results/`.
- All tuned parameters must record dataset, objective function, parameter bounds, resulting values, and holdout validation dataset.
- Do not tune secretly to match one dataset.
- Roughness parameters must not be tuned inside validation cases; any future calibration must live in an explicit calibration experiment with recorded objective, bounds, dataset, and holdout policy.
- The Tschamut v0.3.0 calibration experiment is documented in `docs/tschamut_calibration.md`; its selected parameters are research diagnostics and must not become defaults without a separate versioned model decision.

Validation results must describe the model version, parameters, preprocessing, and limitations.
