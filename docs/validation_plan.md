# Validation Plan

Validation asks whether the current model is useful when compared with observations or published benchmarks. It does not target RAMMS::ROCKFALL equivalence and does not use proprietary datasets.

Claim levels for validation and pilot reports are defined in
`docs/validation_maturity_framework.md`. Current validation evidence should be
reported conservatively: analytic and synthetic checks are V0-V1 evidence,
public field comparisons are limited V2 evidence, and no current result reaches
operational V5 maturity.

## v0.6.1 Status

Real-world validation is partial and qualitative. The current simulator is a spherical-block model with simple restitution, Coulomb friction, opt-in rotational sphere contact, opt-in stochastic contact roughness, opt-in minimal scarring_contact_v1 impact energy-loss diagnostics, analytic terrain, small DEM support, and deterministic release perturbations. It cannot yet represent block-shape effects, advanced contact, calibrated scarring with drag torque or slip-dependent friction, calibrated spatial roughness distributions, forest interaction, fragmentation, or calibrated field-scale parameter sets.

## Dataset Policy

- Use public datasets only.
- Preserve raw files under `data/raw/<dataset_id>/` or `validation/data/raw/<dataset_id>/`.
- Store reproducible derived files under `data/processed/<dataset_id>/` or `validation/data/processed/<dataset_id>/`.
- Cite dataset title, authors, DOI, source URL, and license.
- Do not commit large raw data.
- Keep large real-data validation optional; small license-compatible derived fixtures may be checked in for CI smoke tests.

The public dataset registry is in `data/datasets.yaml`; dataset notes are in `docs/datasets.md`. The multi-dataset role split is documented in `docs/dataset_strategy.md`. The unified public benchmark preparation and grouped-validation contract is documented in `docs/public_benchmark_framework.md`. swisstopo entries are operational input geodata for future Swiss hazard-map workflows, not experimental validation datasets.
Future source-frequency evidence records are governed by
`docs/source_frequency_evidence_contract.md`. Those records must separate
calibration dataset ids from validation dataset ids and must not list swisstopo
terrain as validation evidence by itself.
Future block-scenario and release-cell probability evidence records are
governed by `docs/block_release_probability_evidence_contract.md`. Those
records must not reuse conditional sampling weights as physical probability
evidence, and must keep calibration dataset ids separate from validation
dataset ids.

## Commands

```bash
cargo run -- validate --case validation/cases/synthetic_plane_basic.yaml
cargo run -- validate --case validation/cases/chant_sura_trajectory_subset.yaml
cargo run -- validate --case validation/cases/tschamut_basic.yaml
cargo run -- validate --all
cargo run -- validate --all --json-lines
```

Missing optional public observations cause a skipped report with instructions rather than a CI failure. The checked-in Tschamut subset is intentionally small enough for local and CI validation smoke tests.
The legacy tab-separated output is kept for compatibility. For scientific or
review use, prefer `--json-lines` so each case exposes `completion_status`,
`execution_status`, `scientific_status`, warnings, failures, and metrics.
`Passed` in the legacy output means the case contract completed; it is not by
itself a claim of field validation, operational maturity, or V5 evidence.

## Metrics

Implemented validation metrics include deposition-point distance error, runout distance error, lateral deviation, deposition centroid error, deposition-cloud mean nearest-neighbor distance, deposition-cloud overlap fraction, trajectory-shape error, trajectory kinetic-energy relative error, trajectory proxy jump-height error, final speed, impact count, max speed, max bounce height, energy diagnostics, rolling residual/contact diagnostics, scarring depth/drag/energy-loss diagnostics, and ensemble runout summaries where seeded perturbations are used.
Roughness-specific verification metrics include zero-roughness baseline comparison and different-seed ensemble runout deltas.
Scarring-specific verification metrics include zero-scarring baseline comparison, maximum scarring depth, maximum scarring drag force, and total scarring energy loss.

Planned metrics include trajectory-envelope overlap, bounce-height time-series error, velocity and angular-velocity time-series error, runout exceedance probability, and deposition-density skill scores.

## Real-World Validation Interpretation

Chant Sura is the primary trajectory/physics reference dataset. The checked-in first-flight case uses three short reconstructed segments from the public EnviDat `Output.7z` archive. It compares trajectory shape, translational kinetic-energy evolution, and proxy jump-height consistency on a flat clearance plane.

The DEM-backed segmented-contact experiments use a small RF16 UAS DEM crop. The original contact fixture uses the first three RF16W200r1 local-time-reset segments, while the extended fixture uses five source trajectories, 16 segments, and 11 segment-boundary contact/rebound proxies that stay inside the same crop. A held-out fixture adds six disjoint source trajectories, 15 segments, and 9 contact/rebound proxies for generalization testing. These cases add contact-aware metrics for impact timing, rebound velocity, post-impact kinetic-energy change, and jump-height envelope. They constrain contact-model behavior qualitatively, but they remain small subsets and do not validate complete runout, deposition, non-spherical shape effects, or operational hazard skill.

The Tschamut 2014 case is a limited distribution-level comparison against public-derived release and deposition points. It validates only that the current workflow can ingest public observations, run deterministic ensembles, and report interpretable mismatch metrics. It does not validate individual paths or operational hazard skill.

Terrain representation is part of the validation assumption set. `validation_tschamut_proxy_plane` keeps the earlier fitted-plane terrain approximation as an explicit structural-error comparison, while `validation_tschamut_basic` uses the `idw_residual_dem_from_lps` clamped DEM proxy derived from public LPS ground points. Neither terrain is an official field DEM.

The registered public Tschamut benchmark workflow extends this smoke-test role
with public EnviDat observations, public swissALTI3D terrain, documented
registration, explicit-grid hazard layers, and grouped no-tuning analysis. It
is still a benchmark reproduction and failure-mode workflow, not operational
hazard validation.

Any hazard-layer products from validation or benchmark workflows must use the
semantics in `docs/hazard_map_semantics.md`: current outputs are unweighted
diagnostic or sampling-weighted conditional products. Threshold products are
conditional intensity-exceedance diagnostics, not annual intensity-frequency or
return-period products.
The inactive source-frequency evidence template does not change this
interpretation; it only defines fields and rejection checks for future review.
The inactive block/release probability evidence template likewise does not
change current products; it only defines fields and rejection checks for future
review.

Mel de la Niva is registered as an external high-energy/generalization
benchmark. Its public Zenodo data are large and remain ignored locally. The
first runnable package is opt-in and generated under `validation/results/` from
the public trajectory, GIS, and SfM DSM archives. It records checksums, retains
LV03/EPSG:21781 coordinates, crops the public DSM, and builds baseline and
`sphere_rotational_v1` path-endpoint/deposition smoke cases. Because the LAS
trajectory archive used by the first package lacks timestamps, this is
reproducible workflow validation and external failure-mode evidence, not timed
trajectory validation or calibration.

The Tschamut `scarring_contact_v1` comparison in `docs/tschamut_scarring_experiment.md` is an explicit comparative experiment. It applies impact-level Chant Sura scarring parameters to Tschamut without changing the original validation case and without tuning to Tschamut runout. Such experiments are useful for understanding model directionality, but they are not evidence of predictive skill unless calibration and held-out validation are separately designed.

For real-world cases:

- distributions matter more than individual paths for the current model;
- mismatch is expected and should identify missing physics, such as block shape, calibrated roughness, vegetation, and richer terrain representation;
- roughness parameters in validation cases are generic model settings, not tuned Tschamut calibration;
- a passing status means the workflow completed and reported metrics, not that the model is field-accurate.
- each public benchmark must be interpreted according to its declared role:
  Chant Sura for trajectory/contact realism, Chant Sura EOTA221 for passive
  shape-readiness and future shape-contact tests, Tschamut for deposition and
  grouped runout failures, and Mel de la Niva for later external high-energy
  generalization.

## Reproducibility Criteria

Validation and benchmark workflows must preserve deterministic reproducibility:

- identical trajectory inputs and seed produce identical samples and summaries;
- different trajectory seeds produce distinct perturbed releases when perturbation ranges are nonzero;
- opt-in contact roughness is driven by trajectory-specific seeds and is reproducible for the same trajectory identity;
- ensemble trajectory seeds are derived from global seed, case ID, and trajectory ID;
- per-trajectory results are independent of execution order;
- optional real-world validation cases must skip cleanly when data are absent rather than changing deterministic test behavior.
- public benchmark preparation manifests must record selected run IDs,
  excluded runs, CRS/registration assumptions, data provenance, and deterministic
  seed policy before validation outputs are interpreted.

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
