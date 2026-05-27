# Swiss-Scale Feasibility Projection From Measured Evidence

Status: projection-only synthesis. This report does not authorize a new run,
claim operational readiness, or convert projection into physical, annual,
risk, exposure, or vulnerability semantics.

## Recommendation

- TB-678 current decision: do not submit a Swiss-wide or distributed run yet.
  The concise readiness surface is
  `archive/task_reports/swiss_scale_demonstration_readiness_tb678.md`.
- Measured support has improved locally and on Balfrin, but the Swiss-wide
  phase-change status remains `deferred`.
- First Swiss-wide phase-change blocker:
  `distributed_execution_authorization`.
- First data blocker: `national_public_geodata_inventory`.
- First scientific blocker: accepted validation/calibration evidence; the
  current selected calibration candidate is explicitly rejected by
  `holdout_runout_abs_error_max_m`.
- Current practical ceiling: 100 release zones have been measured on Balfrin as
  a single-node `postproc` diagnostic reducer-pressure workload. This is the
  current diagnostic ceiling, not a hazard-throughput, operational, or
  physical-probability ceiling. TB-680/TB-681 is now the current repeat
  measured 24-zone hazard-throughput support pair.
- First bottleneck: scientific evidence remains first for physical or
  operational claims. For further scale work, the next practical blocker is no
  longer a larger diagnostic by default; it is hazard-throughput scaling and
  scientific validation evidence.
- Next measurable step: use the measured diagnostic series to size the next
  hazard-throughput or validation step, while keeping regional, Swiss-wide,
  distributed, operational, and physical-probability claims separate.
- 10-zone: feasible as a hazard-planning class on the current single-node and
  `postproc` boundary, with reducer pressure still the next implementation
  bottleneck.
- 16-zone: measured as Balfrin diagnostic reducer-pressure evidence.
- 24-zone: measured and repeated as Balfrin diagnostic reducer-pressure
  evidence; this is the diagnostic repeatability anchor.
- 32-zone: measured as Balfrin diagnostic reducer-pressure evidence.
- 40-zone: measured as Balfrin diagnostic reducer-pressure evidence.
- 100-zone: measured as Balfrin diagnostic reducer-pressure evidence; this is
  the current diagnostic performance ceiling.
- Hazard-throughput probe: TB-680/TB-681 measured and repeated a bounded
  24-zone hazard-throughput profile on Balfrin `postproc` with runtime, memory,
  output footprint, and replay-critical family coverage. TB-669 remains the
  previous comparison anchor. This is the current hazard-throughput support
  pair, not a Swiss-wide, operational, distributed, or physical-probability
  claim.
- Latest bounded diagnostic comparison: TB-652 completed an 8-zone compact
  `postproc` diagnostic on Balfrin as job `4377075`, with preserved run root
  `/scratch/mch/olifu/rust_rockfall/diagnostics/tb652_8_zone_20260527`,
  `0:00.59` elapsed wall time, `34.223` MB peak RSS, `28` output files,
  `14,397` output bytes, `11,458` manifest bytes, and `2.11` reducer wall
  seconds. This strengthens diagnostic reducer-pressure evidence but does not
  replace TB-680/TB-681 as the hazard-throughput support pair.
- Prior hazard-throughput probe: TB-603 measured the bounded hazard workflow on
  Balfrin `postproc` with complete mandatory runtime, memory, output, and
  conditional-curve metrics and remains the baseline for TB-619 comparison.
- 100-zone: measured diagnostic reducer-pressure evidence. Reducer pressure is
  no longer projection-only for this diagnostic shape, but live
  hazard-throughput interpretation remains unmeasured at this size.
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
1. Manifest pressure and hazard-output bytes beyond the measured TB-682
   192-zone safe point.
1. Reducer pressure and replay/metadata growth for larger hazard-output
   batches.
1. Output-byte and file-count growth when moving beyond diagnostic postproc.
1. Scaling beyond the repeat measured TB-680/TB-681 hazard-throughput run,
   because the 100-zone evidence is diagnostic and TB-680/TB-681 remains a
   bounded single-node hazard-throughput support pair.
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
    TB-407 smallest multi-zone probe, TB-680 bounded hazard-throughput run, and
    the current claim boundaries.
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
- TB-601 measured the 40-zone diagnostic reducer-pressure run on Balfrin:
  job `4372257`, run root
  `/scratch/mch/olifu/rust_rockfall/diagnostics/diagnostic_40_zone_tb601_20260526`,
  reducer wall time `6.35` s, maximum RSS `33.902` MB, `124` output files,
  `51,493` output bytes, and `28,818` manifest bytes.
- TB-603 measured the bounded hazard-throughput run on Balfrin:
  job `4372309`, run root
  `/scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_multi_release_zone_tb603_20260526`,
  hazard workflow wall time `7.043564590974711` s, process peak memory
  `357.796875` MB, `57` hazard output files, `31,439,786` hazard output bytes,
  `130` validation-output files, `34,565,316` validation-output bytes, and
  `729,600` conditional-curve rows represented in summary-only mode.
- TB-619 measured the next bounded four-zone hazard-throughput run on Balfrin:
  job `4372656`, run root
  `/scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_four_zone_hazard_tb619_20260527`,
  hazard workflow wall time `6.930015419959091` s, process peak memory
  `379.14453125` MB, `57` hazard output files, `31,439,445` hazard output
  bytes, `130` validation-output files, `34,565,323` validation-output bytes,
  and `729,600` conditional-curve rows represented in summary-only mode. This
  supersedes TB-603 as the latest hazard-throughput support point while keeping
  TB-603 as the comparison baseline.
- TB-669 measured the next bounded 12-zone hazard-throughput run on Balfrin:
  job `4378015`, run root
  `/scratch/mch/olifu/rust_rockfall/probes/tb669_12_zone_hazard_throughput_20260527_123917`,
  profile wall time `0.288978714030236` s, hazard-layer time
  `0.0781356020597741` s, peak memory `47.016` MB, `29` hazard output files,
  `1,148,530` hazard output bytes, `93` run-root files, `2,373,626`
  run-root bytes, and complete replay-critical coverage for `12` trajectory
  CSVs, `12` impact-event CSVs, one deposition CSV, and one diagnostics JSON.
  This supersedes TB-619 as a hazard-throughput support point while keeping
  TB-619 as the comparison baseline.
- TB-680 measured the next bounded 24-zone hazard-throughput run on Balfrin:
  job `4379134`, run root
  `/scratch/mch/olifu/rust_rockfall/probes/tb680_24_zone_hazard_throughput_preserved_20260527_145422`,
  profile wall time `0.2727567689726129` s, hazard-layer time
  `0.08593320602085441` s, peak memory `40.9375` MB, `29` hazard output
  files, `1,169,964` hazard output bytes, `117` run-root files, `2,488,907`
  run-root bytes, and complete replay-critical coverage for `24` trajectory
  CSVs, `24` impact-event CSVs, one deposition CSV, and one diagnostics JSON.
  This supersedes TB-669 as a hazard-throughput support point while keeping
  TB-669 as the comparison baseline. The first new blocker is manifest byte
  pressure: `63,992` observed bytes versus a `60,000` byte replay budget.
- TB-681 repeated the same bounded 24-zone hazard-throughput shape on Balfrin:
  job `4379224`, run root
  `/scratch/mch/olifu/rust_rockfall/probes/tb681_24_zone_hazard_throughput_repeat_20260527_151222`,
  profile wall time `0.3176133460365236` s, hazard-layer time
  `0.08398795907851309` s, peak memory `40.6758` MB, `29` hazard output
  files, `1,169,610` hazard output bytes, `116` run-root files, `2,534,753`
  run-root bytes, and the same replay-critical family coverage. The repeat
  preserves output shape and memory behavior; profile wall time increased by
  about `16%`, so planning should use the repeat maximum until the next larger
  support point exists. Manifest-byte pressure remains the blocker: `63,653`
  observed bytes versus the `60,000` byte replay budget.
- TB-682 measured larger single-node hazard-output pressure at `96`, `192`, and
  `384` release zones on Balfrin `postproc`. The largest measured size still
  under the current reduced-output byte budget is `192` zones: job `4379388`,
  profile wall time `0.4413482559612021` s, hazard-layer time
  `0.21222814603243023` s, peak memory `48.4766` MB, `29` hazard output files,
  `1,353,399` hazard output bytes, and `198,522` manifest bytes. The first
  measured output-byte blocker is `384` zones: job `4379371`, `1,536,400`
  hazard output bytes versus a `1,500,000` byte budget, with `325,518`
  manifest bytes. Do not attempt more than `192` zones under the current output
  profile without reducing hazard output bytes and manifest size.
- TB-652 measured a smaller 8-zone compact diagnostic run on Balfrin:
  job `4377075`, run root
  `/scratch/mch/olifu/rust_rockfall/diagnostics/tb652_8_zone_20260527`,
  terminal state `COMPLETED`, `/usr/bin/time` elapsed `0:00.59`, maximum RSS
  `34.223` MB, `28` output files, `14,397` output bytes, `11,458` manifest
  bytes, and `2.11` reducer wall seconds. The corrected metrics report recorded
  `14` measured and `0` blocked mandatory diagnostic metrics.
- TB-611 prepared the no-submit 100-zone diagnostic package at
  `/scratch/mch/olifu/rust_rockfall/diagnostics/diagnostic_100_zone_tb611_20260526`
  and measured the same reducer-pressure shape locally: `100` release zones,
  `4` reducer chunks, `304` output files, `121,016` output bytes, `60,703`
  manifest bytes, and `13.55` reducer wall seconds. TB-612 then converted this
  package into measured Balfrin scheduler evidence.
- TB-612 submitted that package as Balfrin `postproc` job `4372447`, which
  completed with exit code `0:0`, scheduler elapsed `00:00:01`,
  `/usr/bin/time` elapsed `0:01.26`, maximum RSS `34.16 MB`, `304` output
  files, `121,172` output bytes, `61,119` manifest bytes, and `448,376`
  run-root bytes. This promotes 100 zones to measured diagnostic reducer
  pressure only; hazard throughput, Swiss-wide execution, distributed
  execution, and physical-probability claims remain separate.
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
  - TB-609 refreshed that proof through
    `scripts/summarize_large_aoi_gis_cog_stress_test.py` on
    `target_gate_v1`: the standard package is `gis_package_ready` with `39`
    files, `401,265` bytes, `22` rasters, and `3` manifest files; the scratch
    converted package is `cog_package_ready` with `39` files, `403,419` bytes,
    `22` rasters, `333,888` manifest bytes, `25.104302958003245` seconds of
    conversion time, and `parity_match` layer inventory.
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
- `hazard_throughput` is now measured for the bounded TB-619 support point, but
  larger multi-zone, distributed, and Swiss-wide hazard execution remains
  unmeasured.
- GIS/COG conversion is measured for the current largest package-capable output
  root: TB-631 produced a COG-ready scratch package with 22/22 raster parity
  and no packaging blocker.
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
| 32-zone | measured diagnostic postproc | 5.39 reducer wall seconds | 42,221 output bytes | 100 output files | Scientific evidence blocks broader claims | measured diagnostic | use as diagnostic performance evidence |
| 40-zone | measured diagnostic postproc | 6.35 reducer wall seconds | 51,493 output bytes | 124 output files | Scientific evidence blocks broader claims | measured diagnostic | use as diagnostic performance evidence |
| hazard-throughput probe | repeat measured on Balfrin | 0.273-0.318 profile wall seconds | 1,169,610-1,169,964 hazard output bytes | 29 hazard output files | Scientific validation and manifest/reducer/replay pressure block broader claims | summary-only reduced output measured twice with manifest-byte blocker | use TB-680/TB-681 as the repeat bounded hazard-throughput support |
| hazard-output pressure ladder | measured on Balfrin | 0.396 / 0.441 / 0.588 profile wall seconds | 1,261,335 / 1,353,399 / 1,536,400 hazard output bytes | 29 hazard output files | Manifest bytes fail at all larger sizes; output bytes first fail at 384 zones | 96/192/384-zone reduced-output ladder | keep 192 zones as the current measured output-byte-safe size |
| 100-zone | measured diagnostic postproc | 13.55 reducer wall seconds | 121,172 output bytes | 304 output files | Hazard-throughput and scientific evidence block broader claims | measured diagnostic | promote series, then measure hazard throughput or validation evidence |
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
- The largest current package-capable output in this checkout (`target_gate_v1`)
  is no longer blocked at the GIS/COG conversion layer. TB-631 measured a
  `39`-file / `401,265` byte scratch package, converted it to a COG-ready
  `39`-file / `403,419` byte scratch package, kept all `22` raster layers in
  parity, and measured `19.775688750029076` seconds of COG conversion on the
  local machine. This is demonstration packaging evidence only and does not
  authorize operational GIS claims.
- TB-646 exercised a local chunked AOI-style hazard/package smoke in `/tmp`
  using the Tschamut target-gate inputs with `2` trajectory workers and `3`
  reducer workers. The run wrote `63` hazard files / `24,207,052` bytes,
  completed `3` reducer chunks and `2` trajectory chunks, preserved
  `sorted_chunk_id` merge order, and packaged `41` review files /
  `415,570` bytes with `24` rasters and `2` vector overlays. This is local
  chunk/merge/package evidence only, not distributed execution evidence.
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

The current evidence supports a 10-zone hazard-planning boundary, a measured
100-zone Balfrin diagnostic reducer-pressure ceiling, a bounded 24-zone
hazard-throughput support pair from TB-680/TB-681, and a 192-zone measured
hazard-output byte-safe point from TB-682. It does not yet support broader
regional-workflow, Swiss-wide, operational, physical-probability, distributed,
or non-`postproc` claims. The next useful scale action is a larger bounded
hazard-throughput run if queue policy allows it; the next useful scientific
action is to close the remaining calibration-evidence gap.
