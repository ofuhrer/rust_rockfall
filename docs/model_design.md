# Model Design

## Scope

The v0 simulator is an independent, literature-based spherical-block model. It is intended for analytic validation and research iteration, not for operational hazard assessment.

Supported now:

- spherical block with explicit mass and radius
- analytic terrain and small ESRI ASCII grids
- gravity-driven free flight
- normal/tangential restitution at impact
- Coulomb friction during contact
- deterministic stochastic release perturbations
- energy-budget trajectory diagnostics

Deliberately left out:

- RAMMS equivalence claims
- proprietary implementation details
- convex polyhedral contact
- nonsmooth complementarity solver
- compactable-soil scarring
- forest, barriers, fragmentation, GIS production workflows, GPU/HPC, visualization

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

Tangential velocity is reduced by a friction-capped restitution impulse. This is an independently chosen v0 approximation, not a hard-contact complementarity solver.

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

Important data types:

- `SimulationConfig`
- `TerrainConfig`
- `SphereBlock`
- `BodyState`
- `TrajectorySample`

The CLI accepts the same JSON configuration:

```bash
rockfall --config examples/inclined_plane.json --output trajectory.csv
```

## Extension Path

The next scientifically meaningful extensions are:

- DEM fixture tests and terrain boundary policies
- sphere rolling diagnostics and rolling resistance
- quaternion orientation state
- ellipsoid and convex-polyhedron geometry APIs
- nonsmooth contact solver or integration with a public solver reference
- calibrated scarring model based on public experimental data

