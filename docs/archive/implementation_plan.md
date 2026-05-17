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

- Status: active.
- Objective: add opt-in sphere rotational contact with rolling/sliding diagnostics while preserving `translational_v0` as the default model.
- Methods: sphere contact point velocity, normal restitution impulse, Coulomb-capped tangential impulse with angular-velocity updates, no-slip rolling acceleration, and simple dimensionless rolling resistance.
- Modules: `dynamics`, `state`, `integrator`, `simulation`, `validation`.
- Tests: rotational impulse unit tests, solid-sphere rolling on an inclined plane, rolling-resistance stopping, energy monotonicity, and insufficient-friction sliding.
- Output: `rolling` contact state plus angular velocity, contact tangent speed, and rolling residual diagnostics.
- Limitations: rolling resistance remains a simple transparent law, not a calibrated terrain/soil model.

## Phase 5: Rotational Dynamics Scaffold

- Objective: prepare for non-spherical rigid-body motion.
- Methods: expose angular velocity and spherical inertia diagnostics; document quaternion path for later.
- Modules: `geometry`, `state`, `validation`.
- Tests: angular energy diagnostic.
- Output: public API can evolve toward ellipsoids/polyhedra.
- Limitations: orientation does not affect v0 contact.

## Phase 6: Stochastic Ensembles

- Status: implemented in `v0.3.0`.
- Objective: deterministic release perturbations, opt-in stochastic contact roughness, and ensemble summaries.
- Methods: `ChaCha8Rng` seeded sampling; trajectory-specific seeds for release and impact roughness.
- Modules: `stochastic`, `simulation`.
- Tests: fixed seed reproduces identical samples; zero roughness matches baseline; nonzero roughness produces deterministic runout spread; dissipative roughness has bounded energy behavior.
- Output: reproducible single-run perturbations and ensemble summary metrics.
- Limitations: roughness is contact stochasticity, not a calibrated spatial terrain roughness law.

## Phase 6b: Minimal Scarring Diagnostics

- Status: implemented in `v0.4.0`; retained in the current model as opt-in physics.
- Objective: add opt-in compactable-soil impact energy-loss diagnostics without changing default behavior.
- Methods: estimate impact-local scar depth, sphere-cap area, drag force, and bounded translational energy loss.
- Modules: `dynamics`, `integrator`, `simulation`, `state`, `validation`.
- Tests: zero-effect baseline, nonnegative energy loss, depth scaling, deterministic diagnostics, and synthetic scarring verification cases.
- Output: `scarring_depth_m`, `scarring_drag_force_n`, and `scarring_energy_loss_j` diagnostics.
- Limitations: no calibrated soil classes, drag torque, slip-dependent friction, terrain deformation, or validation tuning.

## Phase 7: Validation Cases

- Objective: validate against analytic cases first and public benchmark behavior later.
- Methods: unit/integration tests, documented external benchmark candidates.
- Modules: `validation`, `tests`.
- Tests: deterministic analytic tests.
- Output: transparent validation plan.
- Limitations: no RAMMS bitwise comparison.

## Phase 8: Performance And Ensemble Scaling

- Objective: make large trajectory ensembles feasible for Swiss hazard-map workflows.
- Methods: benchmark hot loops and allocation patterns; improve single-socket throughput; add local parallel execution where order-independent deterministic seeds and reducers are already defined.
- Tests: `cargo test`, `cargo fmt --check`, `cargo clippy -- -D warnings`.
- Output: prioritized optimization list, throughput metrics, chunk/reducer contracts, and a path to later CSCS/SLURM orchestration.
- Limitations: production SLURM orchestration, MPI, and GPU execution are future phases.

## Future Phases

- Python bindings
- valley-scale Swiss pilot workflow from public geodata
- pragmatic release-zone and block-scenario generation
- uncertainty and intensity-frequency hazard-map summaries
- GeoTIFF and production DEM workflows
- streaming/tiled hazard-map reducers and GeoTIFF/COG export
- production visualization/reporting workflows
- calibrated compactable-soil scarring refinements
- convex polyhedral rigid-body contact
- public benchmark dataset integration
- local parallel execution and later CSCS/SLURM orchestration
- GPU acceleration only after an explicit phase decision
