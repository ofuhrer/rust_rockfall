# Tschamut Calibration Experiment

This historical document describes `calibration/experiments/tschamut_v0_3`, a controlled calibration experiment for the public Tschamut 2014 dataset. It is explicitly separate from validation. It does not modify `validation/cases/tschamut_basic.yaml`, does not claim predictive skill, and does not produce operational hazard parameters. It is not operational calibration. The experiment remains a v0.3.0 calibration artifact and does not use the v0.4.0 `scarring_contact_v1` soil interaction model.

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

The experiment evaluates an explicit local grid defined in `calibration/experiments/tschamut_v0_3/config.yaml`:

- `normal_restitution`: `0.20`, `0.25`, `0.35`, `0.40`
- `tangential_restitution`: `0.80`, `0.85`, `0.90`
- `friction_coefficient`: `0.30`, `0.35`, `0.40`, `0.45`
- roughness profile:
  - `low`: normal `0.04`, tangent `0.04`, angle `0.04 rad`
  - `moderate`: normal `0.08`, tangent `0.06`, angle `0.08 rad`
  - `high`: normal `0.12`, tangent `0.08`, angle `0.12 rad`

The grid is intentionally local around the prior edge optimum while broadening friction, restitution, and roughness enough to test whether the earlier result was grid-limited. It calibrates only exposed v0.3.0 parameters and keeps `contact_model: translational_v0` with opt-in `roughness_model: stochastic_contact_v1`. It does not introduce new physics.

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
PYENV_VERSION=system uv run python scripts/run_tschamut_calibration.py
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
- `objective_contract.json`

To inspect the executable objective without running the candidate grid:

```bash
PYENV_VERSION=system uv run python scripts/run_tschamut_calibration.py --describe-objective
```

To refresh summaries and residual diagnostics from existing candidate and ensemble outputs without rerunning the full grid:

```bash
PYENV_VERSION=system uv run python scripts/run_tschamut_calibration.py --refresh-summary-only
```

## Result

The expanded local run completed with 144 candidates and no calibration/holdout ID overlap. The selected candidate is `candidate_103`:

- `normal_restitution = 0.35`
- `tangential_restitution = 0.90`
- `friction_coefficient = 0.40`
- `roughness_model = stochastic_contact_v1`
- `roughness_std_normal = 0.08`
- `roughness_std_tangent = 0.06`
- `roughness_std_angle = 0.08 rad`

Calibration subset:

- objective: `0.0464`
- observed mean runout: `92.25 m`
- simulated mean runout: `90.63 m`
- runout error: `1.62 m`
- deposition centroid error: `3.65 m`
- deposition-cloud mean nearest error: `11.46 m`
- lateral spread error: `3.48 m`

Held-out subset:

- objective: `0.0857`
- observed mean runout: `97.63 m`
- simulated mean runout: `105.51 m`
- runout error: `7.88 m`
- deposition centroid error: `8.99 m`
- deposition-cloud mean nearest error: `8.09 m`
- lateral spread error: `9.50 m`

The held-out objective remains close to the calibration objective for this split. That does not prove predictive skill; it mainly shows that this expanded local grid has not visibly overfit the calibration subset. The selected parameters improve runout and centroid errors substantially compared with the prior 16-candidate smoke, while lateral spread remains weaker on the held-out subset.

The measured sensitivity summary in `summary.json` identifies `friction_coefficient` as the strongest mean objective driver across the explicit grid. The calibration-objective span between the best and worst candidates is `1.4124`, so the run confirms that parameter changes produce measurable runout/deposition metric deltas.

Residual diagnostics in `summary.json` compare the selected candidate's ensemble mean endpoint with each observed deposition row:

- calibration partition: 18 trajectories, 72 ensemble members, mean absolute runout error `24.43 m`, median `23.23 m`, max `70.41 m`; worst runout case `v107`;
- held-out partition: 18 trajectories, 72 ensemble members, mean absolute runout error `18.22 m`, median `12.86 m`, max `55.11 m`; worst runout case `v086`.

These residuals show that the aggregate objective improvement does not remove important per-event errors. They are diagnostics for model development, not an acceptance threshold.

## Hazard-Layer Smoke

TB-637 ran a scratch-only 20-member Tschamut target-gate smoke comparing the target-gate baseline parameters with the selected `candidate_103` parameters. The scratch cases changed only the output root, ensemble size, and candidate parameters; no validation case, default parameter, or committed hazard output was mutated.

Aggregate validation metrics moved in the expected direction for this bounded smoke:

- simulated mean runout increased from `72.16 m` to `82.36 m`;
- runout error decreased from `30.68 m` to `20.48 m`;
- deposition centroid error decreased from `30.14 m` to `19.91 m`;
- deposition-cloud mean nearest error decreased from `24.34 m` to `14.44 m`;
- lateral spread error decreased from `16.85 m` to `14.97 m`;
- deposition-cloud overlap increased from `0.795` to `0.985`.

Hazard-layer comparison found `24` shared layers on the same explicit grid, no layer-shape mismatch, no threshold-set disagreement, and no reference-only or candidate-only layers. Outputs changed materially rather than only through metadata: all `48` comparable output checksums differed. Selected layer deltas included reach-probability `L1=15.345`, weighted reach-probability `L1=2.79`, max kinetic-energy `RMSE=3295.22 J`, max jump-height `RMSE=0.580 m`, and deposition-density nonzero Jaccard `0.0`.

This confirms that the calibration-selected parameters materially affect map outputs in a controlled scratch run. It remains a bounded smoke, not a validation acceptance or operational hazard-map claim.

## Terrain Update Note

After the terrain-focused update, validation includes both `validation_tschamut_proxy_plane` and `validation_tschamut_basic`. The calibration grid above was rerun as a bounded smoke in TB-627 from the explicit objective contract; this preserves the calibration/validation separation because the holdout partition remains excluded from fitting and selected parameters are not promoted into validation cases.

## Interpretation

This experiment is useful because it exposes parameter sensitivity and model limitations. The active validation case with the bounded IDW residual DEM proxy terrain under-runs the first 10 validation runs. The calibration experiment uses the fitted terrain as an analytic plane to avoid DEM-bound failures during energetic candidate trajectories, and the best grid candidate over-runs the calibration and holdout partitions.

That pattern points to terrain representation, contact-mode limitations, and per-event residual structure, not just scalar parameter choice:

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
