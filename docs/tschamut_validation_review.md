# Tschamut Validation Review

This review covers the active `validation_tschamut_basic` case for `v0.3.0`. The case uses public-derived data from Volkwein and Gerber's EnviDat dataset, "Repetitive trajectory testing in Tschamut 2014", DOI <https://doi.org/10.16904/envidat.34>. It is a limited validation workflow check, not an operational hazard validation and not a calibrated reproduction of the field experiment.

## Preprocessing Assessment

The preprocessing is transparent and reproducible. `scripts/preprocess_datasets.py --dataset tschamut2014` reads only the public `OverviewAllTests.txt` and `all_LPS_splined.txt` resources, preserves raw ZIP files under `data/raw/tschamut2014/`, and writes derived CSV/ASC/JSON files under `data/processed/tschamut2014/` and `validation/data/processed/tschamut/`.

The validation subset currently uses the first 10 LPS trajectories that can be joined to overview block metadata. Release points are the first LPS spline sample for each selected run; deposition points are the last LPS spline sample. Block mass and approximate spherical radius are derived from the overview table. Elevations are shifted by `-1600 m` to match the local coordinate convention described in the overview table, and block-center elevations are projected onto the proxy terrain plus the derived sphere radius. These choices are defensible for a first v0 validation fixture because they are deterministic, small enough for CI, and explicitly documented in the generated metadata. They are also simplifications: first/last LPS samples may not exactly equal physical release/rest positions, and spherical radii collapse measured block dimensions into one scalar.

## Proxy Terrain

The terrain approximation is clearly labelled. `validation/data/processed/tschamut/metadata.json` states that `terrain.asc` is a least-squares plane sampled as an ESRI ASCII grid from public LPS terrain elevations, with:

- `z_m = slope_x * x_m + slope_y * y_m + intercept_m`
- `slope_x = -0.2531275637807767`
- `slope_y = 0.4065679284814367`
- `intercept_m = -15.009701417307735`

This is scientifically acceptable only as a v0 proxy terrain. It is not an official field DEM, does not preserve local concavities, ridges, roughness, or channelization, and should not be used for calibrated field comparison. The report and metadata correctly warn against interpreting it as a calibrated terrain reconstruction.

## Metrics

The metrics are appropriate for an uncalibrated spherical v0.3.0 model because they compare distributions and deposition clouds rather than exact trajectories:

- observed and simulated mean runout,
- mean runout error,
- deposition centroid error,
- symmetric mean nearest-neighbor deposition-cloud error,
- lateral spread error,
- coarse deposition-cloud overlap fraction.

The case intentionally has no pass/fail acceptance threshold. A `Passed` status means that the public-data workflow ran deterministically and reported metrics. It does not mean that the model is accurate for Tschamut.

Current active result:

- observed mean runout: about `102.84 m`
- simulated mean runout: about `41.92 m`
- runout distance error: about `60.92 m`
- deposition centroid error: about `60.10 m`
- deposition-cloud mean nearest error: about `24.62 m`
- lateral spread error: about `10.18 m`
- deposition-cloud overlap fraction within the current coarse radius: about `0.90`

## Interpretation Of The Under-Runout

The roughly `60.9 m` under-runout is physically plausible for the current model and should be treated as useful evidence of missing physics and missing calibration, not as a bug by itself.

Most likely causes:

- The default `translational_v0` contact model has no rolling energy reservoir, no rolling acceleration mode, and no rolling resistance law. Long runout on grassy slopes often depends on rolling and repeated low-loss contacts.
- The chosen restitution and friction values are generic and uncalibrated. `normal_restitution = 0.25`, `tangential_restitution = 0.85`, and `friction_coefficient = 0.45` can dissipate too much energy for some Tschamut trajectories.
- The proxy plane removes important terrain structure. Real local slope breaks, micro-topography, channels, and terrain-guided paths can sustain or redirect motion in ways a fitted plane cannot.
- The blocks are represented as spheres. The public experiments used irregular blocks with different shapes, sizes, and rotational behavior. Shape affects rebound, rolling/sliding transitions, lateral spread, and stopping.
- The opt-in stochastic contact roughness is synthetic and not calibrated to Tschamut. It creates deterministic ensemble spread but is not a terrain-class or material model.
- Release conditions inferred from the first LPS spline sample may not capture the exact experimental release impulse or early trajectory segment.

## Recommended Next Step

The next high-impact step should be a separate, explicit calibration experiment for the current model, not a hidden change to validation. The calibration should use `validation_tschamut_basic` or a larger Tschamut subset to estimate only a small set of exposed parameters, for example:

- `normal_restitution`,
- `tangential_restitution`,
- `friction_coefficient`,
- optionally the three `stochastic_contact_v1` roughness scales.

The calibration objective should be distribution-level, such as a weighted combination of mean runout error, deposition centroid error, lateral spread error, and mean nearest-neighbor deposition error. Parameter bounds, objective weights, selected training runs, and held-out validation runs must be recorded. A follow-up validation case should then run on held-out Tschamut trajectories or a different public dataset.

In parallel, the next physics improvement to evaluate is making `sphere_rotational_v1` usable for this validation case with documented rolling resistance and rolling diagnostics. That should remain opt-in until analytic rolling tests, Tschamut calibration experiments, and report outputs demonstrate that it improves distribution-level behavior without breaking existing v0 cases.
