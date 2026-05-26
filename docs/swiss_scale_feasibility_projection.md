# Swiss-Scale Feasibility Projection From Measured Evidence

Status: projection-only synthesis. This report does not authorize a new run,
claim operational readiness, or convert projection into physical, annual,
risk, exposure, or vulnerability semantics.

## Recommendation

- Current practical ceiling: 32 release zones have been measured on Balfrin as
  a single-node `postproc` diagnostic reducer-pressure workload. This is the
  current diagnostic ceiling, not a hazard-throughput, operational, or
  physical-probability ceiling. The older 10-zone single-AOI boundary remains
  the current hazard-planning boundary.
- First bottleneck: scientific evidence remains first for physical or
  operational claims. For further scale diagnostics, the next practical
  blocker is queue policy and whether another bounded `postproc` diagnostic
  step, such as 32 zones, still fits comfortably.
- Next measurable step: run the next bounded diagnostic size only while keeping
  the run root on `$SCRATCH`, then promote runtime, memory, output-byte,
  file-count, and manifest-byte evidence back into the projection surfaces.
- 10-zone: feasible as a hazard-planning class on the current single-node and
  `postproc` boundary, with reducer pressure still the next implementation
  bottleneck.
- 16-zone: measured as Balfrin diagnostic reducer-pressure evidence.
- 24-zone: measured and repeated as Balfrin diagnostic reducer-pressure
  evidence; this is the diagnostic repeatability anchor.
- 32-zone: measured as Balfrin diagnostic reducer-pressure evidence; this is
  the current diagnostic performance ceiling.
- 100-zone: deferred projection. Reducer pressure and replay metadata still
  dominate before any live hazard-throughput interpretation.
- Regional split probe branch: TB-447 executed one bounded regional split
  `postproc` job and TB-448 preserved the run-root metrics. TB-432 remains
  historical failed-closed/no-submit evidence, but it is no longer the latest
  regional split state. The next step is reducer-pressure optimization, then
  scenario batching, before any further live recommendation.
- Regional workflows: still deferred as scale capability; the measured split
  probe is a comparison anchor, not a promotion to broader regional capability.
- Swiss-wide: still deferred as a phase change because there is no measured
  Swiss-wide execution and the physical/scientific evidence basis is not ready.

The next live-run decision gate also reports
`non_postproc_readiness_assessment_v1`. It compares CPU count, memory, runtime,
I/O volume, walltime, partition policy, and execution-model evidence. Current
evidence does not show a measured CPU, memory, runtime, I/O, or walltime reason
to leave `postproc`; the deferred blockers are partition policy and unsupported
execution model. The assessment does not request access or authorize a phase
change.

`scripts/estimate_swiss_wide_execution_envelope.py` now also emits
`swiss_wide_phase_change_readiness_v1`. That matrix keeps the Swiss-wide
blocker decomposed into four independent classes:

- `compute_feasible`: measured national tiling/chunk runtime, memory, I/O,
  restart cost, and any required distributed execution authorization.
- `data_ready`: complete national swissALTI3D plus context-product inventory,
  cache, versions, checksums, and share-safe tiling manifest.
- `validation_ready`: source-frequency evidence, release-probability model,
  independent holdout validation, and calibration/validation separation.
- `operational_ready`: national GIS/COG review, monitoring, reproducibility,
  versioning, and support criteria.

The same report quantifies the planning input footprint with national DEM cell
count, DEM/context byte estimates, tile count, release-zone and trajectory
counts, projected output bytes, and projected file counts. The current status
remains `deferred`; the matrix is a phase-change checklist, not authorization.

## Bottleneck Ranking

The adjacent-candidate branch moved the first blocker away from source-zone
automation and onto the remaining planning bottlenecks:

1. Missing scientific evidence for physical probability and operational use.
1. Queue policy for the next bounded `postproc` diagnostic step.
1. Reducer pressure and replay/metadata growth for larger single-AOI batches.
1. Output-byte and file-count growth when moving beyond diagnostic postproc.
1. Hazard throughput, because the 32-zone evidence is diagnostic rather than a
   larger measured hazard execution.
1. Distributed and non-`postproc` execution, which remain explicit phase
   changes.

## Evidence Basis

The current projection separates evidence by class instead of folding fail-closed
branches into measured capability:

- Measured evidence:
  - `scripts/estimate_large_scale_execution.py` anchors the 10-zone and
    100-zone hazard-planning rows to the measured conditional-output profile
    and the current Balfrin gate coefficients.
  - `scripts/estimate_swiss_wide_execution_envelope.py` now exposes 16-zone,
    24-zone, and 32-zone diagnostic classes separately from hazard support,
    using the latest Balfrin diagnostic run records when those records are
    present.
  - `scripts/summarize_balfrin_scale_readiness_matrix.py` records the measured
    single-job boundary, TB-307 target-area metrics-completion rerun, TB-312
    four-zone postproc/reducer package, TB-368 preserved two-zone evidence,
    TB-407 smallest multi-zone probe, and the current claim boundaries.
- `scripts/summarize_balfrin_management_demo_package.py` keeps runtime,
  restartability, GIS scope, uncertainty, and claim boundaries in the measured
  section while separating projection-only and failed-closed sections and now
  reflects the adjacent-candidate scenario path, AOI/QGIS review readiness,
  the measured regional split comparison path, and the current projection-first
  next step.
  - TB-407 measured the smallest multi-zone Balfrin probe on `postproc`, with
    `130` validation files, `53` hazard files, `729600` conditional-curve
    rows, and preservation-ready run-root evidence.
- TB-579 measured the 24-zone diagnostic reducer-pressure run on Balfrin:
  job `4368588`, run root
  `/scratch/mch/olifu/rust_rockfall/diagnostics/diagnostic_24_zone_simplified_next`,
  reducer wall time `4.03` s, maximum RSS `33.711` MB, `76` output files,
  `32,904` output bytes, and `20,170` manifest bytes.
- TB-581 repeated the same 24-zone diagnostic shape twice:
  jobs `4368592` and `4368593`, both completed, both recorded reducer wall time
  `4.03` s, both produced `76` output files and `32,922` output bytes, with
  maximum RSS between `34.242` and `39.879` MB.
- TB-599 measured the 32-zone diagnostic reducer-pressure run on Balfrin:
  job `4372124`, run root
  `/scratch/mch/olifu/rust_rockfall/diagnostics/diagnostic_32_zone_tb599_20260526`,
  reducer wall time `5.39` s, maximum RSS `34.168` MB, `100` output files,
  `42,221` output bytes, and `24,514` manifest bytes.
- TB-565 and TB-566 measured the current regional split probe: one bounded
  Balfrin `postproc` job completed as job `4367244`, the preserved run root
  recorded `130` validation files, `57` hazard files, `729600`
  conditional-curve rows, `ready_for_demonstration_evidence` preservation
  status, and run-root metrics that supersede TB-432 as the latest regional
  split state.
  - TB-450 threads that measured regional split evidence through the
    scenario-cardinality, output-tier, and reducer-pressure projection
    surfaces. The measured run root stays within the projected larger-AOI
    runtime, file-count, byte, and manifest bands, so reducer/replay metadata
    remains the next ranked bottleneck instead of another comparison pass.
  - TB-453 measures the current regional GIS/COG pressure on the committed
    regional-output root: `hazard/results/tschamut_public_pilot/target_gate_v1`
    is `gis_package_ready_cog_blocked` with `56` files, `79,160,991` bytes,
    and `22` rasters, while the converted proof root
    `hazard/results/tschamut_public_pilot/gate_v1_cog_export` is
    `cog_package_ready_with_scope_delta` with `52` files, `55,873,028`
    bytes, and `20` rasters. The exact next unblock action is to run
    `scripts/convert_same_scale_package_to_cog.py` on the standard root into a
    scratch COG output root if a refreshed converted proof is needed.
  - TB-389 measured a nonempty restaged management-AOI candidate bundle with
    `scripts/stage_management_aoi_restaged_terrain.py` followed by
    `scripts/plan_terrain_release_zone_candidates.py`; that evidence is
    candidate-generation only and does not upgrade Swiss-wide scale or
    operational claim boundaries.
- Extrapolated assumptions:
- Runtime, storage, file count, and job-count estimates for hazard workflows
    still scale from the measured hazard/output coefficient set.
  - Diagnostic runtime, memory, output-byte, file-count, and manifest-byte
    coefficients are tracked separately from the 24-zone diagnostic run and
    repeatability pair.
  - Operator effort follows the job-count shape; this is a planning inference,
    not a measured time study.
  - Memory remains within the measured single-job band because there is no
    larger measured memory series.
- Failed-closed branches:
  - TB-386 rebuilt the current management-AOI Balfrin decision from the
    candidate-screening branch and now fails closed on the adjacent-candidate
    review bundle and generated scenario-table path rather than the old
    source-zone-overlap repair.
  - TB-362 failed closed before `sbatch` on the explicit two-zone hazard path:
    `authorization_status=authorized`, `reducer_budget_status=ready`,
    `submit_contract_status=ready`, and `output_budget_acceptance_status=accepted`,
    but `output_profile_status=blocked_output_profile` kept the pre-submit
    gate at `blocked_reducer_budget`. No job id, runtime, memory, validation
    output, hazard output, GIS package, or measured run root exists for that
    branch.
  - TB-352 failed closed before scheduler submission, so it remains guardrail
    evidence rather than measured multi-zone hazard execution.
  - TB-332/TB-333 failed closed on an authorization checksum mismatch.
  - TB-432 failed closed before `sbatch` on the regional split branch because
    the Balfrin remote checkout hygiene gate found three stale generated
    `command_plan.json` files. The orchestrator later removed those ignored
    generated files from the remote checkout, and a fresh access preflight
    reported `ready_for_read_only_collection`, `ready_for_pre_submit=true`,
    remote hygiene `pass`, and `dirty_path_count=0`; this clears the transient
    hygiene blocker but does not convert TB-432 into measured evidence.
  - TB-321 and TB-309 are also failed-closed submit-contract mismatches, not
    measured hazard runs.
- No-go thresholds:
  - `scenario_cardinality` and `manifest_size` remain the first planning
    bottlenecks for larger bounded probes.
  - `reducer_pressure` and replay metadata growth remain the next bottlenecks
    for 100-zone planning.
- `hazard_throughput` remains out of reach until a larger measured multi-zone
  hazard execution exists.
- GIS/COG conversion remains blocked at the standard-root layer until the
  packaged AOI root has the required manifest fields and raster package
  metadata, even though the converted proof root is already ready.
  - `job_count > 1` still crosses the current single-job evidence boundary.
  - `scale_up_authorized=false` and `distributed_execution_authorized=false`
    remain hard boundaries.
- Unknowns:
  - The adjacent-candidate review bundle now replaces the old
    source-zone-overlap repair as the active management-AOI path, but candidate
    generation still remains separate from scenario generation and prepared-pilot
    packaging.
  - There is no measured multi-AOI Balfrin hazard execution in this repository
    checkout.
  - The target-area validation and hazard-output ratios remain unavailable in
    this checkout, so the projection cannot be compared against those preserved
    outputs here.
  - The manifest estimate is threshold-based rather than a larger measured byte
    series.

## Projection Table

The bands below are read from the helper’s measured coefficients and should be
treated as projection bounds, not new measurements.

| Case | Evidence class | Runtime s (low / nominal / high) | Storage bytes (low / nominal / high) | File count (low / nominal / high) | Bottleneck summary | GIS/COG status | Recommendation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 10-zone | measured hazard-planning boundary | 13.378 / 17.84 / 55.277 | 1,286,207 / 3,953,602 / 267,527,120 | 6 / 17 / 191 | Reducer pressure and replay metadata remain the next hazard-planning bottleneck | bounded | keep as the current hazard-planning anchor |
| 16-zone | measured diagnostic postproc | diagnostic reducer run | diagnostic output footprint | diagnostic file footprint | Scientific evidence prevents promotion beyond diagnostic performance | measured diagnostic | use only as diagnostic performance evidence |
| 24-zone | measured repeatable diagnostic postproc | 4.03 reducer wall seconds | 32,904-32,922 output bytes | 76 output files | Queue policy and scientific evidence block broader claims | measured repeatability pair | use as repeatability evidence below the current ceiling |
| 32-zone | measured diagnostic postproc | 5.39 reducer wall seconds | 42,221 output bytes | 100 output files | Queue policy and scientific evidence block broader claims | measured diagnostic | next diagnostic size only if queue use remains reasonable |
| 100-zone | projection-only deferred | 133.779 / 178.4 / 552.77 | 12,862,070 / 39,536,020 / 2,675,271,200 | 60 / 170 / 1,910 | Reducer pressure, manifest growth, and replay metadata dominate before live hazard throughput | deferred | optimize/re-measure reducer pressure before a live step |
| regional split probe | measured on Balfrin | 24.0 / 24.0 / 24.0 | 34,565,330 / 34,565,330 / 34,565,330 | 130 / 130 / 130 | Measured regional split run-root evidence is available, but it remains bounded comparison evidence | ready_for_demonstration_evidence | keep as comparison evidence |
| regional workflows | deferred | projection-only | projection-only | projection-only | Multi-AOI support and queue policy are not yet measured as scale capability | deferred | no promotion without a phase change |
| Swiss-wide | deferred phase change | projection-only | projection-only | projection-only | Missing scientific evidence and no measured Swiss-wide execution dominate | deferred | continue deferral until science and execution evidence are ready |

## Measured Versus Extrapolated

Measured:

- Single-job support is bounded at 1 AOI, 10 release zones, and 6 trajectories
  per release zone.
- The readiness matrix records TB-312 four-zone postproc/reducer evidence, but
  that evidence is still postproc-only and does not upgrade hazard execution
  capability.
- The readiness matrix records TB-368 preserved two-zone evidence and TB-386 as
  the current management-AOI failed-closed branch on the adjacent-candidate
  review bundle; neither upgrades hazard execution capability.
- TB-407 adds the measured smallest multi-zone probe, which is separate from
  the failed-closed branches and still does not authorize scale-up.
- TB-447 and TB-448 add measured regional split evidence. TB-432 remains
  failed-closed/no-submit history, but the next executable action is now
  reducer-pressure optimization, then scenario batching, then local candidate
  evidence before any further live recommendation.
- TB-389 adds a measured real-AOI candidate bundle on the restaged management
  terrain, which is useful for downstream scenario pressure work but remains a
  heuristic candidate-generation result rather than validated release-zone
  evidence.
- The largest current real output in this checkout (`target_gate_v1`) packages
  to a 29-file scratch bundle, converts to a 29-file COG-ready scratch bundle,
  and matches layer inventory parity; that is demonstration evidence only and
  does not authorize operational GIS claims.
- The current regional GIS/COG pressure measurement adds a committed-root
  split: `target_gate_v1` is measured and COG-blocked at `56` files /
  `79,160,991` bytes / `22` rasters, while `gate_v1_cog_export` is ready at
  `52` files / `55,873,028` bytes / `20` rasters. The pressure is therefore
  measured and blocked at the standard root rather than being operationally
  ready, and the next unblock action is the conversion helper on the standard
  root.
- `scripts/measure_scenario_storage_output_tier_pressure.py` measures the
  current real-AOI candidate scenario table at 3 rows, the fixture scenario
  table at 3 rows, and an expanded candidate-repeat ladder at 1 / 3 / 8
  repeats. That ladder yields 100 / 300 / 800 scenario rows, 52,064 / 162,304
  / 431,904 CSV bytes, and 150,221 / 454,203 / 1,197,781 manifest bytes. The
  helper still measures the minimal tier at 5 files / 27,675 bytes, the
  rebuildable-reduced tier at 17 files / 3,953,602 bytes, the GIS tier at 56
  files / 79,160,991 bytes, and the research-full tier at 2,716 files /
  764,598,283 bytes in this checkout. It recommends `rebuildable_reduced` as
  the smallest Balfrin demonstration replay tier because the minimal tier
  omits builder-facing trajectory outputs, and it recommends batching the next
  Balfrin package at `candidate_repeat_count <= 3` / `30` candidates / `300`
  rows because the 8-repeat step grows sharply past that point.
- `scripts/summarize_multi_zone_reducer_pressure.py` and
  `scripts/validate_multi_zone_reducer_pressure_gate.py` can regenerate
  deterministic local reducer-pressure scratch roots under a caller-supplied
  `/tmp` path and report the generated command-plan, probe-manifest,
  regional-split-plan, output-manifest, and merge-manifest paths plus root and
  output byte/file counts. This is scratch-local reproducibility evidence, not
  Balfrin execution evidence.

Extrapolated:

- Runtime, storage, file count, and job-count estimates scale linearly from the
  measured coefficient set.
- Operator effort is inferred from job count and jobs per AOI, not measured
  directly.

## Bottom Line

The current evidence supports a 10-zone hazard-planning boundary and a
32-zone Balfrin diagnostic reducer-pressure boundary, with 24-zone
repeatability evidence below it. It does not yet
support 100-zone, regional-workflow, Swiss-wide, operational,
physical-probability, distributed, or non-`postproc` claims. The next useful
scale action is another bounded diagnostic step only if queue policy allows it;
the next useful scientific action is to close calibration, holdout,
source-frequency, and physical-probability evidence gaps.
