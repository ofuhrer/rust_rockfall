# Tschamut Validation Review

This historical review covers the active `validation_tschamut_basic` case originally reviewed for `v0.3.0` and still run in `v0.5.0` with `soil_interaction_model: none`. The case uses public-derived data from Volkwein and Gerber's EnviDat dataset, "Repetitive trajectory testing in Tschamut 2014", DOI <https://doi.org/10.16904/envidat.34>. It is a limited validation workflow check, not an operational hazard validation and not a calibrated reproduction of the field experiment.

## Preprocessing Assessment

The preprocessing is transparent and reproducible. `scripts/preprocess_datasets.py --dataset tschamut2014` reads only the public `OverviewAllTests.txt` and `all_LPS_splined.txt` resources, preserves raw ZIP files under `data/raw/tschamut2014/`, and writes derived CSV/ASC/JSON files under `data/processed/tschamut2014/` and `validation/data/processed/tschamut/`.

The validation subset currently uses the first 10 LPS trajectories that can be joined to overview block metadata. Release points are the first LPS spline sample for each selected run; deposition points are the last LPS spline sample. Block mass and approximate spherical radius are derived from the overview table. Elevations are shifted by `-1600 m` to match the local coordinate convention described in the overview table, and block-center elevations are projected onto the generated terrain proxy plus the derived sphere radius. These choices are defensible for a first v0 validation fixture because they are deterministic, small enough for CI, and explicitly documented in the generated metadata. They are also simplifications: first/last LPS samples may not exactly equal physical release/rest positions, and spherical radii collapse measured block dimensions into one scalar.

## Terrain Proxy

The terrain approximation is clearly labelled. `validation/data/processed/tschamut/metadata.json` states that `terrain.asc` is an `idw_residual_dem_from_lps` ESRI ASCII grid proxy. It combines a least-squares trend plane with inverse-distance-weighted residuals from public LPS ground points:

- `z_trend_m = slope_x * x_m + slope_y * y_m + intercept_m`
- `z_m = z_trend_m + IDW_residual_from_public_LPS_ground_points`
- `slope_x = -0.2531275637807767`
- `slope_y = 0.4065679284814367`
- `intercept_m = -15.009701417307735`
- `cellsize_m = 5.0`
- `k_nearest = 24`
- `idw_power = 2.0`

This is scientifically acceptable only as a v0 proxy terrain. It is not an official field DEM, and the opt-in `ascii_dem_clamped` boundary policy extrapolates edge queries by clamping to the raster boundary. The report and metadata correctly warn against interpreting it as a calibrated terrain reconstruction. The earlier fitted-plane approximation is retained as `validation_tschamut_proxy_plane` for terrain-structure comparison.

## Metrics

The metrics are appropriate for an uncalibrated spherical v0 model because they compare distributions and deposition clouds rather than exact trajectories:

- observed and simulated mean runout,
- mean runout error,
- deposition centroid error,
- symmetric mean nearest-neighbor deposition-cloud error,
- lateral spread error,
- coarse deposition-cloud overlap fraction.

The case intentionally has no pass/fail acceptance threshold. A `Passed` status means that the public-data workflow ran deterministically and reported metrics. It does not mean that the model is accurate for Tschamut.

Earlier active fitted-plane result before the terrain preprocessing update:

- observed mean runout: about `102.84 m`
- simulated mean runout: about `41.92 m`
- runout distance error: about `60.92 m`
- deposition centroid error: about `60.10 m`
- deposition-cloud mean nearest error: about `24.62 m`
- lateral spread error: about `10.18 m`
- deposition-cloud overlap fraction within the current coarse radius: about `0.90`

Current terrain-comparison results after the IDW residual DEM update:

| Case | Terrain | Simulated mean runout | Runout error | Centroid error | Mean nearest error | Lateral spread error | Overlap |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `validation_tschamut_proxy_plane` | fitted trend plane with updated LPS-projected release heights | `71.53 m` | `31.31 m` | `30.61 m` | `14.99 m` | `9.07 m` | `0.48` |
| `validation_tschamut_basic` | `idw_residual_dem_from_lps` with clamped DEM boundary | `71.77 m` | `31.07 m` | `30.96 m` | `23.75 m` | `16.77 m` | `0.95` |

The large improvement relative to the previous `60.9 m` under-runout is not solely a local-relief effect. It also reflects the corrected preprocessing choice to place release centers on the public LPS-derived terrain height rather than on the old fitted plane. With those updated release heights, the fitted-plane and IDW residual DEM cases have similar mean runout. The IDW residual DEM improves coarse deposition-cloud overlap but worsens mean nearest-neighbor distance and lateral-spread mismatch. That is useful evidence that the model is sensitive to terrain representation, but also that a small uncalibrated IDW terrain proxy does not by itself solve the validation problem.

## Interpretation Of The Remaining Under-Runout

The remaining roughly `31 m` under-runout is physically plausible for the current model and should be treated as useful evidence of missing physics, missing terrain fidelity, and missing calibration, not as a bug by itself.

Most likely causes:

- The default `translational_v0` contact model has no rolling energy reservoir, no rolling acceleration mode, and no rolling resistance law. Long runout on grassy slopes often depends on rolling and repeated low-loss contacts.
- The chosen restitution and friction values are generic and uncalibrated. `normal_restitution = 0.25`, `tangential_restitution = 0.85`, and `friction_coefficient = 0.45` can dissipate too much energy for some Tschamut trajectories.
- The IDW residual DEM is still a proxy. It preserves some local relief from public LPS points, but it is not a high-quality field DEM, has a coarse `5 m` grid, and uses a clamped boundary outside the validation patch.
- The blocks are represented as spheres. The public experiments used irregular blocks with different shapes, sizes, and rotational behavior. Shape affects rebound, rolling/sliding transitions, lateral spread, and stopping.
- The opt-in stochastic contact roughness is synthetic and not calibrated to Tschamut. It creates deterministic ensemble spread but is not a terrain-class or material model.
- Release conditions inferred from the first LPS spline sample may not capture the exact experimental release impulse or early trajectory segment.

## Recommended Next Step

The next terrain-focused step should be to obtain or derive a more faithful local terrain patch from public Tschamut geodata, ideally using the public slope point cloud or small-rock campaign DEM where licensing and size are acceptable. The current IDW residual DEM is valuable because it makes terrain sensitivity visible, but its comparison against the fitted-plane case shows that simple residual interpolation is not enough.

Calibration should remain separate. Any follow-up calibration should use explicit training/holdout partitions and estimate only a small set of exposed parameters, for example:

- `normal_restitution`,
- `tangential_restitution`,
- `friction_coefficient`,
- optionally the three `stochastic_contact_v1` roughness scales.

The calibration objective should be distribution-level, such as a weighted combination of mean runout error, deposition centroid error, lateral spread error, and mean nearest-neighbor deposition error. Parameter bounds, objective weights, selected training runs, and held-out validation runs must be recorded. A follow-up validation case should then run on held-out Tschamut trajectories or a different public dataset.
