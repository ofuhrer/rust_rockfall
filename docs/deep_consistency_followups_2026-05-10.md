# Deep Consistency Follow-Ups (2026-05-10)

Status: low-risk findings from the 2026-05-10 deep consistency pass were fixed in
`scripts/build_hazard_layers.py`, `tests/test_hazard_layers.py`, and
`README.md`. The items below remain intentionally open because they require
broader behavior or performance-design decisions.

## Open Follow-Up 1: DEM Normal Query Cost In Tight Integrator Loops

- Scope: `src/terrain.rs` (`DemGrid::try_normal`) and `src/integrator.rs`
  fixed-step loop.
- Observation: normal estimation currently triggers multiple DEM height queries
  per integrator step and can be called twice per step in near-contact branches.
- Risk: medium performance risk for large DEM-based ensembles.
- Suggested next step: profile representative DEM runs and evaluate cached local
  gradients or a single-query terrain sampler interface without changing current
  physical semantics.

## Open Follow-Up 2: Clamped DEM Nodata Fallback Is O(N) Over Full Grid

- Scope: `src/terrain.rs` (`nearest_valid_height`).
- Observation: fallback currently scans all cells to find a nearest valid value.
- Risk: medium performance risk when many clamped queries hit nodata regions.
- Suggested next step: benchmark nodata-heavy cases and evaluate a precomputed
  nearest-valid lookup/index strategy with deterministic behavior.

## Open Follow-Up 3: Parallel Ensemble Chunk Iteration Overhead

- Scope: `src/simulation.rs` (worker chunk loop in
  `simulate_ensemble_parallel_with_contact_parameters`).
- Observation: chunk workers iterate via enumerate/take/skip chains rather than
  direct chunk slicing.
- Risk: low-to-medium performance overhead risk for large trajectory counts.
- Suggested next step: micro-benchmark worker-loop iteration alternatives and
  adopt the simplest zero-behavior-change path if measurable.

## Open Follow-Up 4: Hazard Chunk Signature Cost Scales With Full File Hashing

- Scope: `scripts/build_hazard_layers.py` trajectory/reducer execution signatures.
- Observation: execution signatures include content SHA256 for chunk artifacts,
  which can be expensive for large CSV inventories.
- Risk: medium orchestration startup overhead risk in large local chunked runs.
- Suggested next step: measure planning overhead on target-scale runs and decide
  whether to keep full-content hashing or introduce a documented fast-path
  fingerprint policy.
