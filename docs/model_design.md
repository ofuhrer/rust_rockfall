# Model Design

## Scope

The `v0.3.0` simulator is an independent, literature-based spherical-block model. It is intended for analytic validation and research iteration, not for operational hazard assessment.

Supported now:

- spherical block with explicit mass and radius
- analytic terrain and small ESRI ASCII grids
- gravity-driven free flight
- normal/tangential restitution at impact
- Coulomb friction during contact
- opt-in rotational sphere contact with rolling diagnostics
- deterministic stochastic release perturbations
- opt-in stochastic impact roughness
- energy-budget trajectory diagnostics

Deliberately left out:

- RAMMS equivalence claims
- proprietary implementation details
- convex polyhedral contact
- nonsmooth complementarity solver
- compactable-soil scarring
- calibrated terrain roughness fields
- forest, barriers, fragmentation, GIS production workflows, MPI/GPU/distributed execution

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

During sliding, the model constrains normal velocity to zero, applies gravity tangent to the terrain, and reduces speed with Coulomb friction:

```text
|a_friction| = mu |g_normal|
```

The stop criterion terminates motion when tangential speed is below the configured threshold and gravity tangent cannot overcome friction.

## Public API

Primary entry point:

```rust
let config: SimulationConfig = serde_json::from_reader(reader)?;
let result = config.run()?;
```

HPC-ready orchestration entry points:

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
- `TrajectoryRequest`
- `TrajectoryRun`
- `TrajectorySummary`
- `EnsembleResult`

The CLI accepts the same JSON configuration:

```bash
rockfall run --config examples/inclined_plane.json --output trajectory.csv
```

## HPC-Readiness Boundaries

The v0.3.0 codebase does not implement MPI, GPU execution, distributed schedulers, or heavy parallel frameworks. It does keep the core architecture ready for later scaling:

- The single-trajectory kernel is deterministic for explicit inputs.
- `simulate_fixed_step` performs no file I/O and does not use global state.
- `SimulationConfig::run` returns structured samples; CSV/JSON writing is handled by `io` and validation orchestration.
- `SimulationConfig::run_with_terrain` and ensemble orchestration can reuse a previously constructed terrain object, avoiding repeated DEM file reads inside trajectory loops.
- Terrain access is abstracted behind the `Terrain` trait and constructed from serializable `TerrainConfig`.
- Ensemble execution is represented as a loop over independent `TrajectoryRequest` values.
- `TrajectorySummary` separates per-trajectory diagnostics from full trajectory samples so future runners can aggregate summaries while streaming or chunking detailed outputs.

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
- optional parallel/distributed orchestration outside the trajectory kernel
