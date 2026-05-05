# Implementation Plan

## Phase 0: Repository Setup and Design Notes

- Objective: create Rust crate, CLI, docs, and explicit independent-implementation disclaimers.
- Methods: modular library plus `rockfall` binary; JSON config and CSV output.
- Files/modules: `Cargo.toml`, `src/`, `docs/`, `examples/`, `tests/`.
- Tests: crate compiles; smoke tests execute.
- Output: documented experimental project skeleton.
- Limitations: not validated for operational hazard assessment.

## Phase 1: Analytic Terrain Spherical Model

- Objective: simulate a spherical block on plane, paraboloid, and step terrain.
- Methods: exact constant-gravity free-flight update; analytic terrain normals.
- Modules: `terrain`, `geometry`, `state`, `integrator`, `simulation`.
- Tests: gravity acceleration, free-flight energy conservation, simple runout sanity.
- Output: trajectory samples with position, velocity, state, and energy.
- Limitations: no shape-dependent contact or torque.

## Phase 2: Impact, Rebound, and Friction

- Objective: add simple impact and Coulomb friction.
- Methods: velocity decomposition into normal/tangential components; normal restitution; friction-capped tangential response.
- Modules: `dynamics`, `integrator`.
- Tests: horizontal rebound, inclined rebound, stopping under friction.
- Output: deterministic impact and sliding states.
- Limitations: no multi-contact nonsmooth solver.

## Phase 3: DEM Terrain Support

- Objective: support small ESRI ASCII grids.
- Methods: parse raster header, bilinear interpolation, finite-difference normals.
- Modules: `terrain`.
- Tests: flat DEM, bilinear fixture, out-of-bounds errors.
- Output: same simulator can run on DEM fixtures.
- Limitations: no CRS handling, large-raster optimization, GeoTIFF, or GIS workflow.

## Phase 4: Sliding and Rolling Refinement

- Objective: distinguish airborne, impact, sliding, and stopped modes more cleanly.
- Methods: terrain-tangent gravity and Coulomb stop criterion.
- Modules: `dynamics`, `state`.
- Tests: stopping on horizontal terrain and acceleration on inclined terrain.
- Output: clearer diagnostics for contact mode transitions.
- Limitations: rolling resistance remains simplified.

## Phase 5: Rotational Dynamics Scaffold

- Objective: prepare for non-spherical rigid-body motion.
- Methods: expose angular velocity and spherical inertia diagnostics; document quaternion path for later.
- Modules: `geometry`, `state`, `validation`.
- Tests: angular energy diagnostic.
- Output: public API can evolve toward ellipsoids/polyhedra.
- Limitations: orientation does not affect v0 contact.

## Phase 6: Stochastic Ensembles

- Objective: deterministic release perturbations and later ensembles.
- Methods: `ChaCha8Rng` seeded sampling.
- Modules: `stochastic`, `simulation`.
- Tests: fixed seed reproduces identical samples.
- Output: reproducible single-run perturbations.
- Limitations: aggregate ensemble summaries are future work.

## Phase 7: Validation Cases

- Objective: validate against analytic cases first and public benchmark behavior later.
- Methods: unit/integration tests, documented external benchmark candidates.
- Modules: `validation`, `tests`.
- Tests: deterministic analytic tests.
- Output: transparent validation plan.
- Limitations: no RAMMS bitwise comparison.

## Phase 8: Performance Profiling

- Objective: profile after correctness is established.
- Methods: benchmark hot loops and allocation patterns.
- Tests: `cargo test`, `cargo fmt --check`, `cargo clippy -- -D warnings`.
- Output: prioritized optimization list.
- Limitations: HPC/GPU are future phases.

## Future Phases

- Python bindings
- GeoTIFF and production DEM workflows
- stochastic ensemble summaries and rasterized reach maps
- visualization
- compactable-soil scarring
- convex polyhedral rigid-body contact
- public benchmark dataset integration
- HPC and GPU acceleration

