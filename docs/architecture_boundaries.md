# Architecture Boundaries

Status: contributor orientation and refactor map. This document does not change
runtime behavior, validation semantics, physics, defaults, or public APIs.

The repository currently mixes a small deterministic trajectory kernel with a
large validation, benchmark, and hazard-map harness. This is intentional history
rather than the desired end state. New work should preserve the separation
below and avoid adding more cross-cutting responsibilities to already large
files.

## Module Responsibility Table

| Area | Current owner | Responsibility | Boundary rule |
| --- | --- | --- | --- |
| Core state and geometry | `src/state.rs`, `src/geometry.rs`, `src/dynamics.rs` | Body state, sphere geometry, contact equations, energy diagnostics. | No file I/O, no YAML, no validation-case knowledge. |
| Terrain queries | `src/terrain.rs` | Analytic terrain, strict/clamped ESRI ASCII DEMs, terrain errors. | New DEM-facing runtime code must use `try_height` / `try_normal` and propagate `TerrainError`. Infallible `height` / `normal` are legacy convenience methods for analytic terrain and tightly controlled tests. |
| Fixed-step integration | `src/integrator.rs` | Deterministic single-trajectory stepping and impact-event creation. | Prefer `try_simulate_fixed_step*` entry points. `simulate_fixed_step*` wrappers are compatibility helpers and may panic if the fallible path reports an error. |
| Simulation orchestration | `src/simulation.rs` | Config validation, one-case execution, ensemble seed derivation, stop-state provenance. | Normal public execution should return structured `SimulationError`s. The `catch_unwind` boundary is a last-resort containment layer, not a substitute for structured errors. |
| Validation and benchmark harness | `src/validation.rs` | YAML cases, observed-data comparisons, output writing, manifests, status reporting, and assorted sidecars. | This file is intentionally a refactor target. New features should prefer narrow helper modules or scripts instead of growing it further. |
| Probabilistic metadata | `src/probabilistic.rs` | Source-zone, scenario-table, and map-package metadata parsers/validators. | Keep probability semantics separate from trajectory physics. |
| Shape-contact experiment | `src/shape.rs` | Passive shape metadata and internal `shape_contact_v0` scaffolds. | Public runtime and benchmarks remain blocked for `shape_contact_v0`; experimental helpers should stay internal or test-only unless a versioned phase explicitly promotes them. |
| Hazard layers | `scripts/build_hazard_layers.py`, `hazard/` | Post-process trajectory/impact/deposition outputs into rasters and manifests. | Treat hazard layers as post-processing products with explicit semantics and provenance, not core physics. |

## Current Large-File Refactor Targets

`src/validation.rs` is a high-priority split target now that near-term pilot
evidence is stable. The first narrow split is complete: pure validation
metric-math helpers live in `src/validation/metric_math.rs`. Suggested
remaining extraction order:

1. case loading and strict schema audit helpers;
2. observed trajectory/contact/deposition metric evaluation beyond pure math;
3. output exporters and sidecar writers;
4. geodata and terrain/material provenance adapters;
5. manifest and checksum assembly;
6. CLI/report status formatting.

`src/shape.rs` should remain paused for public runtime work, but its internal
scaffolds should eventually split by concern:

1. passive metadata parsing and validation;
2. analytic box inertia/support helpers;
3. internal contact-preparation and diagnostic mapping;
4. test-only smoke and serialization fixtures.

Do not perform these splits as cosmetic churn. Use a split only when a focused
change already touches that concern and can preserve behavior with tests.

## Panic And Error Boundary

Production-facing DEM and pilot workflows should be fallible:

- use `Terrain::try_height` and `Terrain::try_normal`;
- use `try_simulate_fixed_step_with_events*`;
- propagate `TerrainError`, `IntegrationError`, or `SimulationError`;
- classify failed inputs separately from physical stopping.

Panicking wrappers remain only for backward compatibility with older direct
Rust callers and analytic tests. New code should not call them for real DEMs,
validation cases, or pilot workflows.

The current guardrail is enforced by focused strict-DEM tests plus
`scripts/check_repo_consistency.py`, which rejects new infallible
terrain/contact calls in `src/integrator.rs`.

## Scaling Boundary

The single-trajectory kernel should remain deterministic, stateless, and free
of file I/O. Ensemble execution, chunking, reducer manifests, sidecar writing,
and future SLURM orchestration belong outside the kernel. Parallel execution is
a roadmap item only after deterministic local chunk/reducer semantics and
output budgets are stable.
