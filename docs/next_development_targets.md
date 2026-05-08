# Next Development Targets

Status: prioritized development directions after the real-case
intensity-exceedance roadmap refresh. These are planning recommendations only
and do not change simulator behavior.

The repository now has substantial scaffolding for Swiss hazard-map workflow
semantics: claim hygiene, validation maturity labels, source-zone and
block-scenario templates, conditional intensity-exceedance outputs, lightweight
GeoTIFF export, diagnostic pilot GIS manifests, and deterministic hazard-layer
reducer chunks. The main gap is no longer another contract document. The main
gap is a populated, reproducible public real-site pilot that exercises those
contracts without tuning or operational claims.

## Target 1: Prepare One Public Real-Site swisstopo Pilot Package

Objective: Select one small Swiss pilot domain and prepare a reproducible local
swisstopo geodata package with terrain metadata, CRS/datum provenance,
checksums, and share-safe manifest records.

Rationale: Every downstream item depends on a concrete domain, DEM, extent,
nodata policy, and provenance. Without this, source-zone policy, conditional
curves, QGIS review, and performance measurements remain template-level.

Expected value for Swiss hazard-map goal: Very high.

Scientific risk: Medium. Terrain representation and domain choice can dominate
pilot interpretation.

Engineering risk: Medium. CRS/datum, crop extent, nodata, source-tile
identity, local ignored data paths, and raw-data hygiene must be correct.

Likely affected areas: `docs/public_real_site_geodata_preparation.md`,
`docs/swisstopo_data_strategy.md`,
`data/processed/swisstopo/public_real_site_pilot_manifest_template.yaml`,
`scripts/validate_public_real_site_geodata_manifest.py`, ignored
`data/raw/swisstopo/` and `data/processed/swisstopo/` paths.

Evidence needed: validated `public_real_site_geodata_preparation_v1` manifest,
processed DEM metadata, source-tile checksums, CRS/vertical-datum record, extent
record, nodata record, and a clear statement that swisstopo terrain is input
geodata, not validation evidence.

Minimal acceptable deliverable: complete. The selected-domain manifest
`data/processed/swisstopo/tschamut_public_pilot_manifest.yaml` records the
Tschamut public pilot domain, swissALTI3D tile `2696-1167`, crop metadata,
checksums, ignored paths, and preparation command. No raw geodata or large
generated outputs are committed.

What not to do: Do not tune parameters, commit raw swisstopo products, or claim
operational validation.

Estimated order: 1.

## Target 2: Apply A Domain-Specific Source-Zone And Block-Scenario Policy

Objective: Freeze one predeclared source-zone, release-cell, and block-scenario
policy for the selected pilot domain.

Rationale: Conditional intensity-exceedance curves are not interpretable unless
the denominator, source-zone evidence, release-cell sampling, block scenarios,
and sampling weights are documented before results are inspected.

Expected value for Swiss hazard-map goal: Very high.

Scientific risk: Medium to high. Source-zone and block assumptions can appear
more precise than the evidence supports.

Engineering risk: Low to medium.

Likely affected areas: `docs/source_zone_block_scenario_policy_v1.md`,
`validation/templates/public_real_site_source_scenario_policy_v1.yaml`,
`scripts/validate_source_scenario_policy.py`,
`docs/probabilistic_scenario_model_design.md`, pilot-specific ignored
metadata paths.

Evidence needed: validated source-zone/block-scenario policy, deterministic
release-cell ids, block-scenario ids, conditional sampling weights, evidence
level, derivation notes, and explicit rejection of physical or annual
probability claims.

Minimal acceptable deliverable: complete. The selected-domain policy
`validation/policies/tschamut_public_source_scenario_policy_v1.yaml` passes the
validator and can be referenced by the pilot run-freeze file. It records the
Tschamut source-zone interpretation, deterministic release-cell ids, block
scenario ids, and conditional sampling weights without physical or annual
probability claims.

What not to do: Do not implement a national source-zone algorithm, add annual
source frequencies, or move source zones after seeing pilot outputs.

Estimated order: 2.

## Target 3: Run DEM/Terrain Sensitivity On The Selected Domain

Objective: Use the existing DEM sensitivity framework on the selected pilot
domain before interpreting trajectory, contact, material, or source-zone
failures.

Rationale: DEM representation can dominate runout and map patterns. This must
be measured before calibration, physics selection, or operational-style
interpretation.

Expected value for Swiss hazard-map goal: Very high.

Scientific risk: Medium. Terrain variants must be predeclared and interpreted
as sensitivity evidence, not validation evidence.

Engineering risk: Medium.

Likely affected areas: `docs/dem_terrain_sensitivity_benchmark.md`,
`scripts/run_dem_terrain_sensitivity.py`, terrain metadata sidecars, ignored
pilot result directories.

Evidence needed: fixed source/scenario inputs, fixed physics, comparable
terrain variants, map-difference metrics, terrain metadata, and a clear warning
not to tune contact parameters to compensate for DEM effects.

Minimal acceptable deliverable: complete. The selected-domain command
`scripts/run_dem_terrain_sensitivity.py --pilot-manifest data/processed/swisstopo/tschamut_public_pilot_manifest.yaml --source-scenario-policy validation/policies/tschamut_public_source_scenario_policy_v1.yaml --allow-missing-source-dem`
validates the Tschamut geodata manifest and source/scenario policy, records the
fixed source zone, ten release cells, three block scenarios, conditional-only
sampling semantics, EPSG:2056/LN02 terrain metadata, and writes a share-safe
`blocked_missing_processed_dem` no-go report when the ignored processed DEM is
absent. Once the public preparation command creates the ignored DEM locally,
the same command without `--allow-missing-source-dem` runs the predeclared
baseline, 3x3 smoothing, and 2x2 coarsening terrain-variant diagnostics.

What not to do: Do not tune restitution, friction, terrain classes, source
zones, or thresholds after seeing sensitivity outcomes.

Estimated order: 3.

## Target 4: Execute The Small Frozen Conditional Pilot Gate Run

Objective: Run the first end-to-end public real-site conditional pilot gate
using frozen terrain, source-zone policy, block scenarios, thresholds, seed,
grid, and output budget.

Rationale: The repository has the run-freeze template and command-plan
validator, but no real public pilot evidence yet. A small gate run proves
whether the full workflow works before scaling.

Expected value for Swiss hazard-map goal: Very high.

Scientific risk: Medium. The gate run is workflow evidence, not operational
validation.

Engineering risk: Medium to high. Output volume, explicit grid alignment,
manifest completeness, and runtime may expose gaps.

Likely affected areas:
`validation/templates/public_real_site_conditional_pilot_run_v1.yaml`,
`scripts/validate_public_real_site_conditional_pilot_run.py`, ignored
`validation/private/`, `validation/results/`, and `hazard/results/` paths.

Evidence needed: validated run-freeze file, generated command plan, conditional
curve table, hazard manifests, GIS package manifest, reducer chunk manifest,
checksums, runtime/memory/file-count records, convergence notes, and a
pass/no-go/inconclusive pilot report.

Minimal acceptable deliverable: complete as a no-go gate. The selected
Tschamut run-freeze
`validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml`
validates and freezes the available geodata manifest, source/scenario policy,
physics defaults, seed, thresholds, explicit grid, output roots, and output
budget, then classifies the small gate as `no-go` because the ignored processed
public DEM and metadata are absent from a clean checkout. The companion report
`docs/tschamut_public_conditional_pilot_gate_report.md` records that no
conditional curves, GIS artifacts, checksums, runtime/memory metrics, or output
volume evidence exist yet. This is an input-data/reproducibility blocker, not a
model result.

What not to do: Do not run held-out or larger ensembles before the gate is
interpretable; do not tune parameters after seeing outputs.

Estimated order: 4.

## Target 5: Produce And Review The Real-Pilot GIS/QGIS Package

Objective: Package selected pilot rasters and sidecars so a GIS reviewer can
inspect CRS alignment, nodata, value parity, source-zone overlays, and
semantics.

Rationale: Current GeoTIFF and pilot GIS manifest tests prove the file contract
at fixture scale. The real pilot still needs practical GIS acceptance.

Expected value for Swiss hazard-map goal: High.

Scientific risk: Low to medium. Mislabelled GIS products can cause
overinterpretation even when raster values are correct.

Engineering risk: Medium.

Likely affected areas: `docs/pilot_gis_package.md`,
`scripts/build_hazard_layers.py`, `tests/test_hazard_layers.py`, ignored
`hazard/results/` package paths.

Evidence needed: GeoTIFF value parity, CSV/ASCII parity, CRS/transform/nodata
checks, source-zone/context sidecar references, visual-QA status, and explicit
non-COG/non-annual/non-risk labels.

Minimal acceptable deliverable: A real-pilot diagnostic package manifest plus
review notes. A QGIS project, GeoPackage, production COG, and operational map
styling remain deferred.

What not to do: Do not call debug GeoTIFFs COG; do not style maps with annual,
return-period, risk, or operational language.

Estimated order: 5.

## Target 6: Measure Local Scaling And Output-Volume Bottlenecks

Objective: Measure single-node runtime, memory, row counts, file counts, and
reducer behavior on the pilot workflow before adding CSCS/SLURM orchestration.

Rationale: Performance is central to the Swiss hazard-map goal, but the next
engineering work should be driven by real pilot bottlenecks. Current reducer
chunking covers hazard post-processing, not the full trajectory-generation
scale problem.

Expected value for Swiss hazard-map goal: High.

Scientific risk: Low if numerical outputs are unchanged.

Engineering risk: Medium.

Likely affected areas: `tests/hpc_readiness.rs`,
`docs/performance_benchmarking.md`, `docs/scalability_and_data_formats_review.md`,
`src/simulation.rs`, `src/stochastic.rs`, `src/manifest.rs`, and future output
reducers.

Evidence needed: serial/parallel parity where applicable, order-independent
reducer results, timing, memory, file count, output bytes, and a decision on
whether trajectory output, impact events, hazard accumulation, or orchestration
is the bottleneck.

Minimal acceptable deliverable: A pilot-scale performance note and no-default
change recommendation for the next optimization slice.

What not to do: Do not add MPI, GPU, SLURM, or distributed storage before local
chunk/reducer contracts and bottlenecks are clear.

Estimated order: 6.

## Target 7: Increase Ensemble Size Toward The Target Count

Objective: Increase trajectory count only after the small pilot gate and local
scaling evidence are reproducible and interpretable.

Rationale: The target of roughly 10,000 trajectories per release zone is
scientifically useful only if convergence diagnostics and output handling can
show what additional samples change.

Expected value for Swiss hazard-map goal: High.

Scientific risk: Medium. Larger samples can make uncertain source-zone or
block assumptions look falsely precise.

Engineering risk: Medium to high.

Likely affected areas: pilot run-freeze files, performance docs, validation
runner/output modes, hazard reducers, and convergence summaries.

Evidence needed: convergence diagnostics for conditional curves and supporting
layers, trajectory-count sensitivity, output budget compliance, and
worker-count-independent reduced outputs.

Minimal acceptable deliverable: A target-scale feasibility report for the
selected pilot domain, or a documented no-go with the limiting bottleneck.

What not to do: Do not scale up before source-zone, DEM, and small-gate
interpretation are stable.

Estimated order: 7.

## Target 8: Design Physical Source-Frequency Semantics

Objective: Decide whether and how the project can represent physical or annual
intensity-frequency products.

Rationale: Annual products require source and block occurrence evidence, units,
overlap rules, uncertainty, and validation boundaries. Sampling weights are not
physical probability.

Expected value for Swiss hazard-map goal: High, but only after the conditional
pilot evidence exists.

Scientific risk: High.

Engineering risk: Medium.

Likely affected areas: `docs/hazard_map_semantics.md`,
`docs/probabilistic_scenario_model_design.md`, `docs/validation_plan.md`,
`docs/dataset_strategy.md`, future probability schemas and tests.

Evidence needed: source-frequency units, block-frequency semantics, uncertainty
model, source-zone overlap rules, validation/calibration separation, fixtures,
and rejection tests for incomplete frequency metadata.

Minimal acceptable deliverable: A design gate that either authorizes a narrow
annual/physical prototype or keeps annual frequency deferred.

What not to do: Do not back-fill annual frequencies from sampling weights or
calibrate frequency to match one map pattern.

Estimated order: 8.

## Target 9: Implement An Annual/Physical Intensity-Frequency Prototype

Objective: Implement a clearly experimental annual or physical frequency path
only if Target 8 passes.

Rationale: This is the long-term national hazard-map quantity, but implementing
it before the evidence model exists would create misleading products.

Expected value for Swiss hazard-map goal: Very high eventually.

Scientific risk: High.

Engineering risk: Medium.

Likely affected areas: `src/probabilistic.rs`, scenario metadata, map-package
schemas, `scripts/build_hazard_layers.py`, `tests/probabilistic_phase1.rs`,
`tests/test_hazard_layers.py`, and hazard-map docs.

Evidence needed: complete frequency metadata, analytic frequency-sum fixture,
unit-labelled per-cell curves, manifest provenance, and explicit
non-operational report labels.

Minimal acceptable deliverable: A small fixture proving annual or physical
frequency sums with explicit units and complete provenance.

What not to do: Do not promote annual-frequency defaults or imply regulatory
readiness.

Estimated order: 9.

## Deferred But Important Cross-Cutting Work

- Forest, buildings, roads, barriers, nets, and other obstacle relevance should
  be scoped for the selected pilot domain before interpreting omissions as
  physics or material failures.
- Shape/contact runtime work remains paused until provenance and rebound
  blockers are resolved.
- Terrain/material calibration remains deferred until DEM sensitivity, pilot
  evidence, and holdout policy are available.
- Production COG/tiled packages remain deferred until local GeoTIFF/QGIS
  acceptance and reducer contracts are stable.

## Recommended Sequence

1. Prepare one public real-site swisstopo pilot package.
2. Apply a domain-specific source-zone and block-scenario policy.
3. Run DEM/terrain sensitivity on that domain.
4. Execute the small frozen conditional pilot gate run.
5. Produce and review the real-pilot GIS/QGIS package.
6. Measure local scaling and output-volume bottlenecks.
7. Increase ensemble size toward the target count if convergence and
   performance evidence justify it.
8. Design physical/source-frequency semantics.
9. Implement an annual/physical prototype only if the design gate passes.
