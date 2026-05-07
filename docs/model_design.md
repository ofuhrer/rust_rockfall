# Model Design

## Scope

The `v0.6.1` simulator is an independent, literature-based spherical-block model used as the current trajectory kernel for the larger goal of automated Swiss Alpine rockfall hazard mapping. It is intended for deterministic simulation, diagnostics, and hazard-layer development, not for risk modelling or operational warning.

Supported now:

- spherical block with explicit mass and radius
- opt-in passive block-shape metadata with validated dimensions, orientation,
  and principal-moment diagnostics
- analytic terrain, strict small ESRI ASCII grids, and opt-in clamped ESRI ASCII terrain patches
- gravity-driven free flight
- normal/tangential restitution at impact
- Coulomb friction during contact
- opt-in rotational sphere contact with rolling diagnostics
- deterministic stochastic release perturbations
- opt-in stochastic impact roughness
- opt-in compactable-soil scarring energy-loss diagnostics
- energy-budget trajectory diagnostics

## Terrain Representation

Terrain access is abstracted through the `Terrain` trait. Analytic terrain remains unchanged. ESRI ASCII grids follow the standard GIS convention: `xllcorner` and `yllcorner` define the outer lower-left cell corner, raster values are sampled at cell centers, and metadata extents describe the full outer footprint. Strict ESRI ASCII grids use bilinear interpolation over the cell-center domain and intentionally fail on out-of-bounds access through `try_height`. The `Terrain` trait itself is currently infallible, so strict DEM use through `height`, `normal`, or the integrator will panic on out-of-bounds or nodata queries; use the clamped DEM variant only when deterministic boundary extrapolation is an explicit validation assumption.

ESRI ASCII `NODATA_value` cells are not interpolated as elevations. Any bilinear query touching a nodata or non-finite corner returns a terrain error through `try_height`; clamped terrain still fails if the clamped stencil touches nodata. This keeps small DEM fixtures auditable and prevents silent smoothing over raster holes, but it is not a full GIS nodata-repair workflow.

The opt-in `ascii_dem_clamped` / `esri_ascii_grid_clamped` model wraps the same ESRI ASCII grid but clamps height and normal queries to the nearest valid cell centers before interpolation. It is intended for limited real-data terrain patches where a trajectory may leave the small validation raster. This boundary policy is deterministic and lightweight, but it is an extrapolation assumption, not a production GIS workflow.

Validation and benchmark cases can attach a terrain-source metadata sidecar with
`terrain.metadata_path`. The first Swiss pilot uses a tiny synthetic
swissALTI3D-style ESRI ASCII crop with LV95/EPSG:2056 and LN02 metadata. The
metadata parser validates CRS, vertical datum, extent, resolution, nodata,
source/provenance, and consistency with the DEM header, then records those fields
in `run_manifest_v1`. This is a provenance contract around existing terrain
loading, not new terrain physics and not a full GIS ingestion layer.

Swiss pilot cases can also attach `release_zone.metadata_path` with a small
LV95/LN02 polygon source-area fixture. The current runtime supports only
`sampling.mode: deterministic_grid`, validates CRS compatibility with the terrain
metadata when available, generates reproducible release points, and records the
release-zone summary in `run_manifest_v1`. This is an orchestration layer around
independent single-trajectory runs; it does not change the trajectory kernel,
contact laws, or default manual release-point behavior.

Swiss pilot cases can attach `terrain_classes.metadata_path` with an aligned
categorical raster. At each contact evaluation the integrator asks the optional
class provider for local overrides to existing parameters such as normal and
tangential restitution, friction, rolling resistance, and scarring coefficients.
If no class provider is configured, the query is outside the class grid, the cell
is nodata, or a class omits a parameter, the global case value is used. This is a
provenance-tracked spatial parameter lookup, not a new physics model or a
calibration result.

Validation cases can also attach `block_shape.metadata_path` with a
`shape_metadata_v1` sidecar. This sidecar can describe a sphere, ellipsoid, box,
principal dimensions, or custom principal moments, including deterministic
initial orientation metadata and provenance. The parser validates finite
positive dimensions, mass, inertia, and unit quaternions, then records passive
shape diagnostics in `run_manifest_v1` and `trajectory_metadata_table_v1`.
Current contact physics still uses `block.radius` and the existing spherical
inertia; passive shape metadata does not alter trajectory, deposition, energy,
or hazard-layer results.

For Tschamut, preprocessing now writes an `idw_residual_dem_from_lps` terrain proxy from public LPS ground points:

```text
z = slope_x x + slope_y y + intercept + IDW_residual(x, y)
```

This preserves more public-data terrain variation than a fitted plane while remaining reproducible and small enough for repository validation fixtures. It is not an official field DEM and is not calibrated terrain reconstruction. Details are in `docs/terrain_model.md`.

Deliberately left out:

- RAMMS equivalence claims
- proprietary implementation details
- convex polyhedral contact
- nonsmooth complementarity solver
- calibrated scarring with drag torque, terrain categories, or slip-dependent friction
- calibrated terrain roughness fields
- forest, barriers, fragmentation, national release-zone generation, production SLURM orchestration, MPI/GPU execution, or operational warning workflows

## Equations and Assumptions

Free flight uses constant gravitational acceleration:

```text
x(t + dt) = x(t) + v(t) dt + 0.5 g dt^2
v(t + dt) = v(t) + g dt
```

Contact is handled by projecting a penetrating sphere out along the terrain normal and decomposing velocity into normal and tangential components:

```text
v = v_n + v_t
v_n+ = -e_n v_n-
```

The default `translational_v0` contact model reduces tangential velocity with a friction-capped restitution impulse. This is an independently chosen v0 approximation, not a hard-contact complementarity solver.

The opt-in `sphere_rotational_v1` contact model uses the sphere contact point:

```text
r = -R n
v_c = v + omega x r
```

Normal impulse updates linear velocity with normal restitution. Tangential impulse is capped by Coulomb friction and updates both linear and angular velocity. During rolling, the model enforces the solid-sphere no-slip relation through diagnostics:

```text
v_t + omega x r = 0
```

For a solid sphere rolling on an inclined plane with sufficient static friction and no rolling resistance, the tangential acceleration is:

```text
a = (5/7) g_t
```

`rolling_resistance_coefficient` is a dimensionless early-stage resistance parameter used only by `sphere_rotational_v1`. It is transparent and testable, but not calibrated as a terrain or soil law.

The experimental `shape_contact_v0` label is recognized only as a
verification-first scaffold. It requires compatible passive shape metadata and
currently exposes analytic `principal_dimensions_box_v0` inertia/support
helpers plus a crate-internal contact-preparation layer, but that path is not
wired into fixed-step simulation or public benchmarks. The raw low-level impulse
kernel is crate-internal test support; it is not a public integration API.
Runtime-facing shape-contact work must route through the preparation layer so
terrain/contact context, support selection, mass, inertia, contact-regime
classification, and diagnostics cannot come from different sources. A test-only
single-contact state-transition wrapper exercises that path before any
fixed-step integrator wiring. The internal contact-adjacent dry run accepts an
explicit terrain contact point and normal, computes support gap and
contact-point velocity diagnostics, and applies a scaffold-owned impulse update
only for touching or penetrating contact without advancing a trajectory.
An additional internal synthetic harness queries a simple analytic terrain for
height and normal, constructs the explicit contact point, and then calls the
same contact-preparation layer. It is a pre-runtime verification aid only, not a
public simulation path. A still narrower mini fixed-step harness advances at
most one ballistic prediction against analytic terrain through an
integrator-owned fixed-step prediction helper before delegating to that same
preparation layer. The current internal integrator-smoke path can collect an
in-memory `shape_contact_runtime_diagnostic_v1` row and manifest-shaped
sidecar record for this single synthetic step, including file-backed shape
metadata path and SHA-256 provenance in tests. Internal tests can write the
diagnostic rows to a temporary JSON Lines sidecar with a manifest checksum, but
this is still not public validation output. The scaffold does not perform
persistent contact, projection, orientation evolution, validation, benchmark
execution, or public output writing.
The frozen pre-runtime diagnostic contract for future wiring is
`shape_contact_runtime_diagnostic_v1`: runtime rows must expose contact regime,
support gap, terrain normal, support point/corner, contact-point speeds,
impulses, Coulomb cap ratio, pre/post translational and rotational energy,
contact/projection/total energy deltas, quaternion state, and active
shape/model metadata before any public `shape_contact_v0` validation run is
allowed. Run manifests must also record active shape metadata, analytic box
inertia, support-selection policy, contact-gap tolerance,
`multi_contact: false`, `new_tuned_parameters: false`, experimental status,
warnings, and limitations.
Separated dry-run states are reported without impulse, including states moving
toward future contact. The contact-gap tolerance is fixed at `1.0e-9 m` as a
deterministic pre-runtime scaffold convention, not as a calibrated contact
parameter. Support-corner
selection uses a deterministic scaffold policy: exact zero components in the
body-frame support direction choose the positive corner sign. This tie-break is
not a physically validated face-contact model. The diagnostic implementation is
still incomplete for public runtime use.
Existing
`translational_v0` and `sphere_rotational_v1` dynamics and defaults remain
unchanged.

## Impact Roughness

The default roughness model is `none`. The opt-in `stochastic_contact_v1` model applies bounded stochastic perturbations at impact only. It is a contact stochasticity model, not a spatial terrain roughness map.

For each impact, a trajectory-specific `ChaCha8Rng` samples:

```text
n' = normalize(n + alpha t1 + beta t2)
e_n' = e_n clamp(1 - |eta_n|, 0, 1)
e_t' = e_t clamp(1 - |eta_t|, 0, 1)
mu' = mu (1 + |eta_t|)
```

where `n` is the terrain normal, `t1` and `t2` are orthogonal tangent directions, `alpha` and `beta` are bounded angular perturbations in radians, and `eta_n`, `eta_t` are bounded coefficient perturbations. The parameters are:

- `roughness_model`: `none` or `stochastic_contact_v1`
- `roughness_std_angle`: angular standard-deviation scale in radians
- `roughness_std_normal`: dimensionless normal-restitution perturbation scale
- `roughness_std_tangent`: dimensionless tangential-restitution/friction perturbation scale

The coefficient perturbations are dissipative by construction: restitution is only reduced and friction is only increased. The perturbed normal can redirect rebound direction and create deterministic ensemble spread, but the model is not calibrated to a field terrain class. With all roughness standard deviations set to zero, `stochastic_contact_v1` is required to match `none` exactly.

When roughness is active in a direct JSON `SimulationConfig`, `random_seed`
controls both release perturbation and impact roughness. If `random_seed` is
omitted, the roughness RNG uses seed `0` so the run remains reproducible rather
than nondeterministic. YAML ensemble cases derive per-trajectory seeds from
`random.seed`, `case_id`, and `trajectory_id`; an omitted ensemble seed also
defaults to `0`.

During sliding, the model constrains normal velocity to zero, applies gravity tangent to the terrain, and reduces speed with Coulomb friction:

```text
|a_friction| = mu |g_normal|
```

The stop criterion terminates motion when tangential speed is below the configured threshold and gravity tangent cannot overcome friction.

## Soil Interaction And Scarring

The default soil interaction model is `none`. The opt-in `scarring_contact_v1` model adds a deliberately small compactable-soil energy-loss layer at incoming impacts only. It is not a replacement for `contact_model`, and it does not attempt to reproduce RAMMS::ROCKFALL or Lu et al. 2019 in full.

For an incoming impact, the model estimates normal impact speed:

```text
v_n^- = max(0, -v^- . n)
```

If `scarring_max_depth_m` is supplied, that nonnegative value is used as the scar depth and capped at one sphere radius. Otherwise the first implementation uses a Lu/RAMMS-style empirical scaling with mass, normal impact speed, and soil strength:

```text
d = 0.16 m^(1/4) ME^(-0.4) |v_n^-|^(0.8)
```

where `ME` is interpreted from `soil_strength_pa` after conversion to kPa. The cap at one radius is a stability assumption for the simple sphere-cap area model, not a calibrated field law.

The projected sphere-cap scar area is:

```text
A = pi (2 R d - d^2)
```

The model estimates a local drag force and bounded work:

```text
F_d = 0.5 C_d rho A |v^-|^2
E_loss = min(F_d d, post_contact_translational_kinetic_energy)
```

The post-contact translational velocity magnitude is reduced to remove `E_loss` without changing direction. Angular velocity is not changed by scarring in this minimal model. The new diagnostics are:

- `scarring_depth_m`
- `scarring_area_m2` in optional impact-event output
- `scarring_drag_force_n`
- `scarring_uncapped_energy_loss_j` in optional impact-event output
- `scarring_energy_loss_j`
- `scarring_depth_source` in optional impact-event output

With `soil_interaction_model: none`, or with zero depth-producing/drag parameters, the scarring layer is required to be inert. Deferred features include calibrated soil classes, drag torque, slip-dependent scarring friction, terrain deformation, and non-spherical contact.

Optional impact-event outputs (`outputs.impact_events_csv` and `outputs.impact_events_json`) log one record per terrain impact. They include incoming, post-contact, post-scarring, and post-step velocity/energy snapshots so a single contact step can be reconstructed without changing the trajectory CSV format.

## Public API

Primary entry point:

```rust
let config: SimulationConfig = serde_json::from_reader(reader)?;
let result = config.run()?;
```

Ensemble/HPC-ready orchestration entry points:

```rust
let request = TrajectoryRequest::from_global_seed(42, "case_id", "trajectory_000001");
let run = simulate_one_trajectory(&config, request)?;

let ids = vec!["trajectory_000001".to_string(), "trajectory_000002".to_string()];
let ensemble = simulate_ensemble(&config, "case_id", 42, &ids)?;
```

Important data types:

- `SimulationConfig`
- `TerrainConfig`
- `SphereBlock`
- `BodyState`
- `TrajectorySample`
- `ContactModel`
- `SoilInteractionModel`
- `TrajectoryRequest`
- `TrajectoryRun`
- `TrajectorySummary`
- `EnsembleResult`

The CLI accepts the same JSON configuration:

```bash
rockfall run --config examples/inclined_plane.json --output trajectory.csv
```

## HPC-Readiness Boundaries

Performance is a core hazard-map requirement, not a cosmetic optimization. The
v0.6.1 codebase should first improve single-socket throughput, local parallel
trajectory execution, deterministic chunking, and reducer aggregation toward
roughly 10,000 trajectories per release zone where scientifically appropriate.
It does not yet implement production SLURM orchestration, MPI, GPU execution,
distributed schedulers, or heavy parallel frameworks. It does keep the core
architecture ready for later scaling:

- The single-trajectory kernel is deterministic for explicit inputs.
- `simulate_fixed_step` performs no file I/O and does not use global state.
- `SimulationConfig::run` returns structured samples; CSV/JSON writing is handled by `io` and validation orchestration.
- `SimulationConfig::run_with_terrain` and ensemble orchestration can reuse a previously constructed terrain object, avoiding repeated DEM file reads inside trajectory loops.
- Terrain access is abstracted behind the `Terrain` trait and constructed from serializable `TerrainConfig`.
- Ensemble execution is represented as independent `TrajectoryRequest` values.
- `TrajectorySummary` separates per-trajectory diagnostics from full trajectory samples so future runners can aggregate summaries while streaming or chunking detailed outputs.
- Future CSCS/SLURM orchestration should build on the same deterministic seeds, chunk manifests, row counts, checksums, and reducer merge rules rather than changing the trajectory kernel.

## Reproducibility Model

Randomness is explicit. Release perturbations and opt-in stochastic contact roughness use seeded `ChaCha8Rng` streams; no global RNG state is used.

For ensemble-style runs, trajectory seeds are derived from:

```text
global_seed + case_id + trajectory_id
```

via a stable in-repository hash function. This makes each trajectory reproducible by identity, independent of whether trajectories are executed sequentially, in reverse order, or later across separate workers. Contact roughness uses the trajectory seed and is therefore reproducible with the same `case_id`, `trajectory_id`, and global seed.

`SimulationConfig::config_fingerprint` and `SimulationConfig::run_fingerprint` provide stable identifiers for configuration and configuration-plus-trajectory-request. These are intended for bookkeeping, cache keys, and future chunked output manifests, not as cryptographic hashes.

## Extension Path

The next scientifically meaningful extensions are:

- DEM fixture tests and terrain boundary policies
- impact event localization for reduced time-step sensitivity
- calibrated spatial roughness and terrain-class parameterization
- quaternion orientation state
- ellipsoid and convex-polyhedron geometry APIs
- nonsmooth contact solver or integration with a public solver reference
- calibrated scarring model based on public experimental data
- output manifests for chunked ensemble runs
- local parallel execution and later SLURM orchestration outside the trajectory kernel
