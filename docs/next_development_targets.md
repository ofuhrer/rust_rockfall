# Next Development Targets

Status: prioritized development directions after the selected Tschamut public
pilot manifest, source/scenario policy, reconciled DEM-sensitivity and
conditional gate evidence, automated GIS package review record, and local
scaling review. These are planning recommendations only and do not change
simulator behavior.

The repository now has substantial scaffolding and selected-domain contracts
for the Swiss hazard-map workflow. The selected Tschamut run-freeze, DEM
sensitivity gate, conditional pilot report, GIS package review, scaling review,
and visual-QA review record have been reconciled against regenerated local
ignored artifacts. The current critical gap is no longer evidence consistency
or an unclassified visual-QA gate; the next development task should scope
forest and obstacle omission before adding features or increasing ensemble
size.

## Target 1: Reconcile And Regenerate Selected Pilot Gate Evidence

Objective: Bring the selected Tschamut run-freeze, DEM-sensitivity evidence,
conditional pilot report, GIS package review, and scaling review into one
authoritative, locally reproducible state.

Rationale: The project could not honestly claim a completed conditional pilot
while the checked-in run-freeze said `no-go` and the GIS/scaling reviews
referenced ignored artifacts that are absent in a clean checkout. This was
resolved before ensemble scaling or source-frequency design.

Expected value for Swiss hazard-map goal: Very high.

Scientific risk: Medium. Reconciliation must not tune parameters or reinterpret
missing data as model behavior.

Engineering risk: Medium. Local ignored outputs, checksums, reports, and
manifest paths must agree.

Likely affected areas:
`validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml`,
`docs/tschamut_public_conditional_pilot_gate_report.md`,
`docs/tschamut_public_pilot_gis_package_review.md`,
`docs/tschamut_public_pilot_scaling_review.md`,
`scripts/validate_public_real_site_conditional_pilot_run.py`,
`scripts/run_dem_terrain_sensitivity.py`, `scripts/validate_pilot_gis_package.py`,
ignored `data/processed/`, `validation/private/`, and `hazard/results/` paths.

Evidence needed: regenerated or verified processed DEM and metadata, DEM
sensitivity report, conditional curve table, hazard/map/GIS/scaling manifests,
artifact checksums, runtime and output-budget metrics, and a
pass/no-go/inconclusive classification that is consistent across reports.

Minimal acceptable deliverable: complete. The selected run-freeze
`validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml` now
records `gate_run_completed` with an `inconclusive` report classification. It
references regenerated ignored DEM-sensitivity, validation, hazard, GIS
package, reducer, scaling, runtime, memory, file-count, byte-count, and
checksum evidence, while the reports consistently state that generated
artifacts remain ignored and non-operational.

What not to do: Do not tune physics, change defaults, commit raw geodata,
commit large generated outputs, or claim operational/annual/physical/risk
validity.

Estimated order: 1.

## Target 2: Run Manual QGIS Visual QA For The Selected Package

Objective: Complete the human GIS review step for the selected pilot package
after the package artifacts are regenerated or verified.

Rationale: Automated manifest/file QA can verify inventory and checksums, but
it cannot confirm visual alignment, nodata styling, source-zone overlay
interpretation, or map-label clarity in QGIS.

Expected value for Swiss hazard-map goal: High.

Scientific risk: Low to medium. Visual QA can reveal spatial metadata errors
that would mislead interpretation.

Engineering risk: Low to medium.

Likely affected areas: `docs/tschamut_public_pilot_gis_package_review.md`,
`docs/pilot_gis_package.md`,
`validation/pilot_runs/tschamut_public_gis_visual_qa_v1.yaml`, local ignored
package outputs.

Evidence needed: QGIS review notes for CRS alignment, DEM/hillshade or terrain
context alignment, nodata styling, source-zone overlay, layer labels, and
conditional-product language.

Minimal acceptable deliverable: complete at the share-safe checklist level. The
selected visual-QA record
`validation/pilot_runs/tschamut_public_gis_visual_qa_v1.yaml` classifies manual
GIS/QGIS visual QA as `inconclusive` because QGIS was unavailable in the
non-GUI agent environment, while automated package QA passed and all required
CRS, datum, alignment, nodata, source-zone, label, and claim-boundary checks are
classified. The validator
`scripts/validate_pilot_gis_visual_qa.py --require-existing-package` checks the
record against the ignored local package when artifacts exist.

What not to do: Do not create a production QGZ, GeoPackage, COG, risk map, or
operational map product in this step.

Estimated order: 2.

## Target 3: Scope Forest And Obstacle Omission For Tschamut

Objective: Determine whether forest, buildings, roads, barriers, nets, or
other obstacles are first-order boundary conditions for the selected Tschamut
pilot corridor.

Rationale: A no-forest/no-obstacle conditional pilot may be acceptable,
limiting, or invalidating depending on the corridor. This should be explicit
before terrain/material, contact, or calibration conclusions are drawn.

Expected value for Swiss hazard-map goal: High.

Scientific risk: Medium if omission is silently absorbed into model parameters.

Engineering risk: Low for scoping.

Likely affected areas: `docs/swisstopo_data_strategy.md`,
`docs/tschamut_public_conditional_pilot_gate_report.md`,
`docs/tschamut_public_obstacle_context_scope.md`,
`validation/pilot_runs/tschamut_public_obstacle_scope_v1.yaml`, future pilot
report notes.

Evidence needed: share-safe inventory of available public context layers and a
classification of obstacle omission as acceptable, limiting, or invalidating
for the selected gate.

Minimal acceptable deliverable: complete at the share-safe scoping level. The
selected scope record
`validation/pilot_runs/tschamut_public_obstacle_scope_v1.yaml` classifies
forest and obstacle omission as `limiting` because public SWISSIMAGE,
swissTLM3D, swissSURFACE3D/swissSURFACE3D Raster, and swissBUILDINGS3D context
layers are documented but not locally reviewed for the selected corridor. The
validator `scripts/validate_pilot_obstacle_scope.py` checks the six required
context categories, future context actions, and claim boundaries. No obstacle
physics is implemented.

What not to do: Do not tune restitution, terrain classes, or stopping behavior
to mimic omitted forest or barriers.

Estimated order: 3.

## Target 4: Address Conditional-Curve/Raster Output-Volume Bottleneck

Objective: Reduce or gate the selected pilot's conditional-curve and raster
output volume before increasing ensemble size.

Rationale: The local scaling review identifies hazard conditional-curve output
volume as the next bottleneck. Larger ensembles should not proceed until the
output contract is manageable and still reviewable.

Expected value for Swiss hazard-map goal: High.

Scientific risk: Low if numerical semantics and manifests remain unchanged.

Engineering risk: Medium.

Likely affected areas: `scripts/build_hazard_layers.py`,
`scripts/summarize_pilot_scaling.py`, `docs/performance_benchmarking.md`,
`docs/scalability_and_data_formats_review.md`, hazard-layer tests, and pilot
run-freeze output budgets.

Evidence needed: output-mode comparison, manifest-visible output budgets,
checks that selected summaries remain deterministic, and a no-default-change or
explicit opt-in recommendation before ensemble scaling.

Minimal acceptable deliverable: an opt-in output-volume control or documented
gate that prevents larger pilot runs from creating unmanageable conditional
curve/raster artifacts by default.

What not to do: Do not remove existing debug outputs, change current hazard
semantics, add distributed orchestration, or hide denominators/provenance.

Estimated order: 4.

## Target 5: Increase Ensemble Size Toward The Target Count

Objective: Increase trajectory count only after the small pilot gate and local
scaling evidence are reproducible and interpretable.

Rationale: The target of roughly 10,000 trajectories per release zone is useful
only if convergence diagnostics and output handling can show what additional
samples change.

Expected value for Swiss hazard-map goal: High.

Scientific risk: Medium. Larger samples can make uncertain source-zone or
block assumptions look falsely precise.

Engineering risk: Medium to high.

Likely affected areas: pilot run-freeze files, performance docs, validation
runner/output modes, hazard reducers, and convergence summaries.

Evidence needed: convergence diagnostics for conditional curves and supporting
layers, trajectory-count sensitivity, output budget compliance, and
worker-count-independent reduced outputs.

Minimal acceptable deliverable: a target-scale feasibility report for the
selected pilot domain, or a documented no-go with the limiting bottleneck.

What not to do: Do not scale up before source-zone, DEM, small-gate, GIS, and
performance interpretation are stable.

Estimated order: 5.

## Target 6: Design Physical Source-Frequency Semantics

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

Minimal acceptable deliverable: a design gate that either authorizes a narrow
annual/physical prototype or keeps annual frequency deferred.

What not to do: Do not back-fill annual frequencies from sampling weights or
calibrate frequency to match one map pattern.

Estimated order: 6.

## Target 7: Implement An Annual/Physical Intensity-Frequency Prototype

Objective: Implement a clearly experimental annual or physical frequency path
only if Target 6 passes.

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

Minimal acceptable deliverable: a small fixture proving annual or physical
frequency sums with explicit units and complete provenance.

What not to do: Do not promote annual-frequency defaults or imply regulatory
readiness.

Estimated order: 7.

## Completed Selected-Domain Roadmap Items

- Public Tschamut real-site swisstopo pilot package is complete at the
  share-safe manifest level.
- Domain-specific source-zone and block-scenario policy is complete at the
  share-safe policy level.
- DEM/terrain sensitivity is complete as a selected-domain gate with local
  ignored terrain-variant metrics recorded in the reconciled run-freeze.
- Small frozen conditional pilot gate is complete as a regenerated local
  ignored trajectory/hazard run with `inconclusive` report classification, not
  as an operational or target-scale result.
- Real-pilot GIS package is complete at automated manifest/file QA level for
  local ignored outputs, and the selected manual GIS/QGIS visual-QA gate is
  explicitly classified `inconclusive` by a share-safe checklist because QGIS
  was unavailable and no visual overlay evidence was produced.
- Forest and obstacle omission is scoped at the share-safe interpretation
  level and classified `limiting` for the selected Tschamut corridor because
  public context layers are documented but not locally reviewed.
- Local scaling/output-volume summary is complete at the manifest-summary
  level and is reconciled with the authoritative run-freeze. It records
  validation/hazard timings, row/file/byte counts, reducer metadata, memory
  sidecars, and a no-default-change bottleneck decision.

## Deferred But Important Cross-Cutting Work

- Shape/contact runtime work remains paused until provenance and rebound
  blockers are resolved.
- Terrain/material calibration remains deferred until DEM sensitivity, pilot
  evidence, and holdout policy are available.
- Production COG/tiled packages remain deferred until local GeoTIFF/QGIS
  acceptance and reducer contracts are stable.

## Recommended Sequence

1. Reconcile and regenerate selected pilot gate evidence.
2. Run or classify manual QGIS visual QA for the selected package.
3. Scope forest and obstacle omission for Tschamut.
4. Address conditional-curve/raster output-volume bottleneck.
5. Increase ensemble size only if convergence and performance evidence justify
   it.
6. Design physical/source-frequency semantics.
7. Implement an annual/physical prototype only if the design gate passes.
