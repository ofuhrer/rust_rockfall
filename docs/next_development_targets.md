# Next Development Targets

Status: proposed development directions after the current repository review.
These are planning recommendations only and do not change simulator behavior.

The previous roadmap correctly avoided "more physics first." The current
post-`332e626` state has moved several items beyond scaffolding: current
hazard-map semantics, source/block V1 metadata, lightweight GeoTIFF export,
COG deferment, and several reject/accept paths now have executable coverage.
The next targets should therefore focus on pilot evidence, DEM sensitivity,
package-level QA, and the remaining semantic gaps rather than re-documenting
contracts that already exist.

## Target 1: Execute The Controlled Real-Site Tschamut/swissALTI3D Pilot

Objective: Run the no-tuning private/local Tschamut pilot on a real
provenance-tracked swissALTI3D-style DEM crop with frozen release-zone,
scenario, baseline, and `sphere_rotational_v1` comparison settings.

Rationale: The Swiss workflow stack is well specified but not demonstrated on a
real terrain crop. This pilot is the gateway experiment for workflow,
confounding, and feasibility evidence.

Expected value for Swiss hazard-map goal: Very high. It tests real terrain,
source-zone metadata, manifests, hazard layers, GIS QA, output volume, and
throughput in one controlled workflow.

Scientific risk: Medium. Failure may reflect source zones, DEM representation,
forest, block shape, material parameters, or contact physics. It is pilot
evidence, not decisive validation.

Engineering risk: Medium. Private data hygiene, CRS/datum, nodata, edge
behavior, explicit grids, file count, and hazard-stage timings can fail.

Likely affected areas: `docs/tschamut_swissalti3d_controlled_pilot_plan.md`,
`docs/tschamut_swissalti3d_pilot.md`,
`scripts/prepare_tschamut_swissalti3d_pilot.py`,
`scripts/build_hazard_layers.py`, ignored `validation/private/`,
`validation/results/`, and `hazard/results/`.

Evidence needed: G1-G9 gate table, manifest review, baseline/rotational/proxy
metrics, visual QA, terrain-representation notes, row/file/byte counts,
hazard-stage timings, and a decision on whether under-run improves, persists,
worsens, or remains inconclusive.

Minimal acceptable deliverable: A share-safe diagnostic pilot report. No raw
DEMs or large generated outputs are committed.

What not to do: Do not tune parameters, move source zones after seeing results,
claim operational validation, or promote a default contact-model change.

Estimated order: 1.

## Target 2: Build A Dry-Runnable DEM/Terrain Sensitivity Fixture

Objective: Turn `docs/dem_terrain_sensitivity_benchmark.md` into a small
deterministic benchmark fixture comparing terrain resolution, smoothing,
interpolation, nodata/cliff handling, vegetation/surface representation, and
hazard-layer map differences.

Rationale: Terrain representation can dominate trajectory and hazard-map
structure. This should be measured before calibration or physics selection and
can be advanced without private data.

Expected value for Swiss hazard-map goal: Very high. It protects every future
pilot interpretation from confusing DEM artifacts with contact, material,
shape, or source-zone failures.

Scientific risk: Medium. Synthetic perturbations can be arbitrary; they must be
predeclared and interpreted as sensitivity evidence.

Engineering risk: Medium.

Likely affected areas: `verification/synthetic/`, `validation/cases/`,
`scripts/build_hazard_layers.py`, `docs/dem_terrain_sensitivity_benchmark.md`,
`docs/benchmark_catalog.md`, terrain fixtures.

Evidence needed: deterministic rerun parity, fixed-source/scenario invariants,
map-difference metrics for reach/deposition/energy/jump/exceedance layers, and
manifested terrain metadata for each variant.

Minimal acceptable deliverable: A CI-safe dry-run fixture and report template.

What not to do: Do not tune restitution or terrain classes to compensate for
DEM changes; do not treat swisstopo terrain as validation evidence by itself.

Estimated order: 2.

## Target 3: Produce A Pilot GIS/QGIS Package Fixture

Objective: Convert `docs/pilot_gis_package.md` from a contract with tiny
GeoTIFF parity checks into a complete reviewable package fixture with
CRS-correct GeoTIFF, CSV/ASCII parity, source-zone sidecar, manifest labels,
nodata styling guidance, and visual QA evidence.

Rationale: The repo now proves key GeoTIFF value/metadata behavior and
explicitly rejects unverified COG claims. The missing step is a QGIS-ready
package boundary that a pilot reviewer can inspect without interpreting raw
debug files.

Expected value for Swiss hazard-map goal: High.

Scientific risk: Low to medium. GIS metadata errors can create misleading maps.

Engineering risk: Medium.

Likely affected areas: `scripts/build_hazard_layers.py`,
`tests/test_hazard_layers.py`, `docs/hazard_layers.md`,
`docs/pilot_gis_package.md`, `hazard/results/` fixtures if intentionally tiny.

Evidence needed: package-level raster value parity, CRS/transform/nodata
checks, explicit non-COG labeling, source-zone/context sidecar review, and a
QGIS/raster-library smoke inspection note.

Minimal acceptable deliverable: A tiny generated/fixture package that proves
the local review workflow and preserves current hazard values.

What not to do: Do not add GIS dependencies to the trajectory kernel; do not
call unverified GeoTIFFs COG; do not conflate hazard with risk.

Estimated order: 3.

## Target 4: Close Remaining Hazard-Map Semantics Enforcement Gaps

Objective: Extend the current executable semantics coverage to any remaining
manifest/report paths that can emit map labels, denominators, probability
language, source-zone joins, or unsupported annual/physical/risk claims.

Rationale: `docs/hazard_map_semantics.md` is no longer just guidance; current
`unweighted_diagnostic` and `sampling_weighted_conditional` modes have
denominator rules and focused tests. The remaining risk is incomplete coverage
as outputs multiply.

Expected value for Swiss hazard-map goal: High. It protects future map
products from probability and risk overclaims without inventing annual
frequencies.

Scientific risk: Low to medium. The risk is overformalizing unsupported
probability modes; keep current modes narrow.

Engineering risk: Low to medium.

Likely affected areas: `src/probabilistic.rs`, `tests/probabilistic_phase1.rs`,
`tests/fixtures/probabilistic_phase1/`, `scripts/build_hazard_layers.py`,
`tests/test_hazard_layers.py`, `docs/hazard_layers.md`,
`docs/hazard_map_semantics.md`.

Evidence needed: remaining semantic accept/reject tests, required denominator
and normalization fields where products are emitted, and language checks that
prevent annual/physical/risk labels in current products.

Minimal acceptable deliverable: Expanded fixtures and tests covering the
remaining semantic accept/reject cases without adding annual or physical
probabilities.

What not to do: Do not invent source frequency, physical block probabilities,
exposure, vulnerability, or return periods.

Estimated order: 4.

## Target 5: Tighten Source-Zone And Block-Scenario Semantics V1

Objective: Close remaining source-zone/block-policy gaps after the current V1
metadata checks: stable IDs, polygon-only current support, release-cell
identity, block-scenario labels, sampling weights, source-evidence levels, and
explicit non-support for physical/annual probability.

Rationale: National hazard mapping needs defensible source-zone policy and
block scenario semantics before annualized products.

Expected value for Swiss hazard-map goal: High.

Scientific risk: Medium. Source and block assumptions can look more precise
than evidence supports.

Engineering risk: Low to medium.

Likely affected areas: `src/probabilistic.rs`,
`docs/probabilistic_scenario_model_design.md`,
`docs/validation_data_schema.md`, `tests/probabilistic_phase1.rs`,
`validation/cases/probabilistic_phase1_smoke.yaml`.

Evidence needed: any remaining join consistency tests, scenario-row
propagation review, clear separation of release-zone sidecars from
probabilistic source-zone metadata, and literature/source inventory for future
Level 2/3 source-zone derivation.

Minimal acceptable deliverable: Fixture/test coverage for any remaining V1
semantic gaps plus a short policy note for future source-zone derivation
evidence.

What not to do: Do not implement a national source-zone algorithm without
documented slope/geology/inventory assumptions.

Estimated order: 5.

## Target 6: Add A Validation Maturity Framework

Objective: Define maturity labels for claims: V0 analytic verification, V1
synthetic realism, V2 impact-level field validation, V3 site-scale hazard
pattern evidence, V4 cross-site generalization, and V5 operational
reproducibility.

Rationale: The repo distinguishes validation, calibration, pilot evidence, and
operational non-claims, but lacks a concise hierarchy for reports and future
papers.

Expected value for Swiss hazard-map goal: High. It reduces overclaim risk.

Scientific risk: Low if labels are conservative.

Engineering risk: Low.

Likely affected areas: new `docs/validation_maturity_framework.md`,
`docs/validation_plan.md`, `docs/dataset_strategy.md`, `README.md`,
report templates, `scripts/check_repo_consistency.py`.

Evidence needed: mapping of current cases to maturity levels and examples of
allowed/disallowed claims for each level.

Minimal acceptable deliverable: A concise framework referenced by validation
and pilot-report docs.

What not to do: Do not relabel current evidence upward or imply operational
readiness.

Estimated order: 6.

## Target 7: Expand Chant Sura Contact And Shape-Readiness Evidence

Objective: Improve or audit Chant Sura contact/trajectory fixtures, held-out
metrics, passive shape metadata, and proxy-contact caveats before public
shape-contact runtime work.

Rationale: Shape/contact are major scientific gaps, but active shape runtime is
not ready.

Expected value for Swiss hazard-map goal: High scientific value.

Scientific risk: Medium. Segment-boundary contacts remain imperfect evidence.

Engineering risk: Medium.

Likely affected areas: `validation/cases/chant_sura_contact*.yaml`,
`data/processed/chant_sura_2020/`, `docs/chant_sura_contact_validation.md`,
`docs/shape_aware_block_scaffold_design.md`, `src/shape.rs`.

Evidence needed: deterministic split records, contact timing/rebound/energy
metrics, shape provenance, and non-regression checks for current defaults.

Minimal acceptable deliverable: A reviewed shape-readiness report and any small
fixture cleanup needed to support a later shape decision gate.

What not to do: Do not treat proxy contacts as exact impacts; do not run public
`shape_contact_v0` validation while it remains gated.

Estimated order: 7.

## Target 8: Scope Forest/Obstacle Relevance For The Pilot Domain

Objective: Determine whether forest, buildings, roads, barriers, nets, or
other obstacles are first-order boundary conditions for the selected Swiss
pilot domain.

Rationale: A no-forest/no-obstacle pilot can be acceptable, limiting, or
invalidating depending on the corridor.

Expected value for Swiss hazard-map goal: High for interpretation.

Scientific risk: Medium if omission is silently absorbed into parameters.

Engineering risk: Low for scoping.

Likely affected areas: `docs/swisstopo_data_strategy.md`,
`docs/roadmap_hazard_mapping.md`, pilot report, future terrain-context docs.

Evidence needed: share-safe inventory of available context layers and a clear
statement of whether omission is acceptable, limiting, or invalidating.

Minimal acceptable deliverable: A pilot-domain scoping memo.

What not to do: Do not implement forest/barrier physics in this package; do not
tune restitution or terrain classes to mimic forest.

Estimated order: 8.

## Target 9: Prototype Deterministic Local Parallel Execution And Streaming Reduction

Objective: Add an opt-in local parallel execution/reducer prototype only after
pilot or benchmark evidence shows throughput/output pressure.

Rationale: The 10,000-trajectories-per-release-zone target needs local
parallelism and order-independent reducers before SLURM. This may matter more
than trajectory Parquet if reduced outputs are sufficient.

Expected value for Swiss hazard-map goal: High engineering value.

Scientific risk: Low if serial/parallel parity is strict.

Engineering risk: Medium to high.

Likely affected areas: `src/simulation.rs`, `src/stochastic.rs`,
`src/validation.rs`, `src/manifest.rs`, `scripts/build_hazard_layers.py`,
`tests/hpc_readiness.rs`, performance scripts.

Evidence needed: deterministic parity independent of worker count and order,
thread-safe reducer contract, memory/file-count benchmarks, and scaling curves.

Minimal acceptable deliverable: An opt-in prototype with parity tests and a
benchmark report.

What not to do: Do not add MPI, GPU, or SLURM first; do not change defaults or
optimize the kernel without evidence.

Estimated order: 9.

## Target 10: Design Terrain/Material Calibration And Production Data-Format Gates

Objective: Define the gate that must be passed before terrain/material
calibration, trajectory sample tables, tiled reducers, or COG production are
implemented.

Rationale: These are important, but premature work could fit structural errors
or optimize the wrong data path.

Expected value for Swiss hazard-map goal: Medium to high as a guardrail.

Scientific risk: High if calibration starts before pilot, DEM sensitivity, and
holdout evidence.

Engineering risk: Medium.

Likely affected areas: `docs/terrain_material_interaction_protocol.md`,
`docs/scalability_and_data_formats_review.md`,
`docs/trajectory_parquet_next_step_decision.md`,
`calibration/`, future reducer/COG docs.

Evidence needed: holdout policy, objective functions, parameter bounds,
calibration-status metadata, and measured decision criteria for CSV vs Parquet
vs streaming reducers vs tiled rasters.

Minimal acceptable deliverable: A short gate document that explicitly defers
implementation until evidence exists.

What not to do: Do not tune terrain classes on Tschamut proxy results; do not
add writer-only trajectory Parquet; do not implement production COG/tiled
reducers before local reducer contracts.

Estimated order: 10.

## Recommended Sequence

1. Execute the controlled real-site Tschamut/swissALTI3D pilot if private data
   are available.
2. Build a dry-runnable DEM/terrain sensitivity fixture.
3. Produce a pilot GIS/QGIS package fixture.
4. Close remaining hazard-map semantics enforcement gaps.
5. Tighten source-zone and block-scenario V1 semantics.
6. Add validation maturity labels.
7. Expand Chant Sura contact and shape-readiness evidence.
8. Scope forest/obstacle relevance for the pilot domain.
9. Prototype deterministic local parallel execution and streaming reduction
   only when measured bottlenecks justify it.
10. Gate terrain/material calibration and production data-format work until
    pilot, sensitivity, and holdout evidence exist.
