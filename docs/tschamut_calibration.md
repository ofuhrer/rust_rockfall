# Tschamut Calibration Experiment

This document describes `calibration/experiments/tschamut_v0_3`, a first controlled calibration experiment for the public Tschamut 2014 dataset. It is explicitly separate from validation. It does not modify `validation/cases/tschamut_basic.yaml`, does not claim predictive skill, and does not produce operational hazard parameters. It is not operational calibration.

## Dataset Split

Input data are the public-derived Tschamut 2014 release and deposition CSVs under `data/processed/tschamut2014/`, derived from Volkwein and Gerber's EnviDat dataset, DOI <https://doi.org/10.16904/envidat.34>.

The split is persisted in `calibration/data/tschamut/split.yaml`. It is deterministic:

1. Group trajectories by `block_id`.
2. Within each block, sort by `SHA-256(seed, block_id, trajectory_id)` with seed `70314`.
3. Select the first 6 runs per block for calibration.
4. Select the next 6 runs per block for held-out validation.
5. Leave all remaining runs unused for this first experiment.

This gives 18 calibration runs and 18 held-out runs, with no overlap. The split is stratified by block ID so that the calibration and holdout partitions both include the three block IDs represented in the processed public-derived data. The choice is simple and reproducible; it is not optimized to make the model look good.

## Parameter Space

The experiment evaluates a small explicit grid defined in `calibration/experiments/tschamut_v0_3/config.yaml`:

- `normal_restitution`: `0.25`, `0.40`
- `tangential_restitution`: `0.85`, `0.95`
- `friction_coefficient`: `0.20`, `0.35`
- roughness profile:
  - `low`: normal `0.04`, tangent `0.04`, angle `0.04 rad`
  - `moderate`: normal `0.08`, tangent `0.06`, angle `0.08 rad`

The grid is intentionally small enough to inspect by hand. It calibrates only exposed v0.3.0 parameters and keeps `contact_model: translational_v0` with opt-in `roughness_model: stochastic_contact_v1`. It does not introduce new physics.

## Objective Function

The scalar objective is a weighted normalized mismatch:

```text
J =
  0.45 * runout_distance_error_m / observed_mean_runout_m
+ 0.25 * deposition_centroid_error_m / observed_mean_runout_m
+ 0.20 * deposition_cloud_mean_nearest_error_m / observed_mean_runout_m
+ 0.10 * lateral_spread_error_m / observed_mean_runout_m
```

Lower is better. The objective deliberately combines runout and deposition-cloud metrics so calibration is not driven by a single number. The metric remains a research diagnostic; it is not a likelihood function and does not quantify operational skill.

## Procedure

Run:

```bash
python3 scripts/run_tschamut_calibration.py
```

The script:

1. Recreates the deterministic split and partition CSVs.
2. Generates temporary calibration cases under `calibration/results/tschamut_v0_3/`.
3. Calls `cargo run -q -- validate --case <generated-case>` for each parameter candidate and partition.
4. Writes committed summaries under `calibration/experiments/tschamut_v0_3/`.

Intermediate files under `calibration/results/` are ignored by git. Committed outputs include:

- `candidate_results.csv`
- `selected_parameters.yaml`
- `summary.json`
- `report.html`

## Result

The selected candidate is `candidate_011`:

- `normal_restitution = 0.40`
- `tangential_restitution = 0.85`
- `friction_coefficient = 0.35`
- `roughness_model = stochastic_contact_v1`
- `roughness_std_normal = 0.08`
- `roughness_std_tangent = 0.06`
- `roughness_std_angle = 0.08 rad`

Calibration subset:

- objective: `0.4598`
- observed mean runout: `92.25 m`
- simulated mean runout: `142.75 m`
- runout error: `50.50 m`
- deposition centroid error: `51.38 m`
- deposition-cloud mean nearest error: `33.26 m`
- lateral spread error: `1.90 m`

Held-out subset:

- objective: `0.3660`
- observed mean runout: `97.63 m`
- simulated mean runout: `140.47 m`
- runout error: `42.84 m`
- deposition centroid error: `43.53 m`
- deposition-cloud mean nearest error: `26.52 m`
- lateral spread error: `2.70 m`

The held-out objective is lower than the calibration objective for this split. That does not prove predictive skill; it mostly shows that this small grid has not visibly overfit the calibration subset. The selected parameters still over-run both partitions substantially when the generated calibration cases use the unbounded analytic proxy plane.

## Terrain Update Note

After the terrain-focused update, validation includes both `validation_tschamut_proxy_plane` and `validation_tschamut_basic`. The calibration grid above has not been rerun or retuned; this preserves the calibration/validation separation and avoids silently changing selected parameters. The updated validation comparison should be read as a fixed-parameter terrain sensitivity experiment, not as a new calibration result.

## Interpretation

This experiment is useful because it exposes parameter sensitivity and model limitations. The active validation case with the bounded IDW residual DEM proxy terrain under-runs the first 10 validation runs. The calibration experiment uses the fitted terrain as an analytic plane to avoid DEM-bound failures during energetic candidate trajectories, and the best grid candidate over-runs the calibration and holdout partitions.

That difference points to terrain representation and contact-mode limitations, not just parameter choice:

- the proxy terrain is too simple and should not be interpreted as a calibrated DEM;
- the translational model lacks rolling energy and explicit rolling resistance;
- spherical blocks cannot represent irregular block shape and shape-dependent rolling/rebound;
- roughness is stochastic contact perturbation, not a spatial terrain roughness model;
- release states inferred from first LPS samples are approximate.

## Next Step

The next calibration experiment should be paired with a model-development decision:

1. Run the same split with opt-in `sphere_rotational_v1` and rolling resistance candidates once the rolling model is ready for field-style cases.
2. Replace the fitted plane proxy with a richer public terrain representation or a bounded procedural terrain that does not introduce artificial DEM-edge failures.
3. Keep a holdout partition and record objective weights, bounds, and selected parameters exactly as done here.

No calibrated parameter from this experiment should become a project default.
