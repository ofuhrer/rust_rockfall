# Swiss-Scale Feasibility Projection From Measured Evidence

Status: projection-only synthesis. This report does not authorize a new run,
claim operational readiness, or convert projection into physical, annual,
risk, exposure, or vulnerability semantics.

## Recommendation

- 10-zone: feasible as a projection-supported planning class on the current
  single-node/postproc boundary. The adjacent-candidate path means source-zone
  automation is no longer the first blocker; the next evidence should support a
  larger bounded probe only if scenario cardinality stays manageable.
- 100-zone: conditionally feasible and deferred. The next step is reducer and
  replay-pressure reduction, not a live run, because the current projection is
  still dominated by manifest and metadata growth rather than measured
  multi-zone hazard throughput.
- Regional split probe branch: TB-447 executed one bounded regional split
  `postproc` job and TB-448 preserved the run-root metrics. TB-432 remains
  historical failed-closed/no-submit evidence, but it is no longer the latest
  regional split state. The next step is reducer-pressure optimization, then
  scenario batching, before any further live recommendation.
- Regional workflows: still out of reach as scale capability under current
  single-node/postproc constraints; the measured split probe is an anchor for
  comparison, not a promotion to broader regional capability.
- Swiss-wide: out of reach under the current authorization boundary. The next
  step is continued deferral until Balfrin access, authorization, and multi-AOI
  evidence gaps close.

## Bottleneck Ranking

The adjacent-candidate branch moved the first blocker away from source-zone
automation and onto the remaining planning bottlenecks:

1. Scenario cardinality and manifest size.
1. GIS/research-full output growth after the measured scenario table remains
   compact.
1. Reducer pressure and replay/metadata growth.
1. Hazard throughput, because no larger measured multi-zone hazard execution
   exists yet.
1. GIS packaging and manifest metadata completeness.
1. Balfrin access and authorization boundaries for larger planning cases.

## Evidence Basis

The current projection separates evidence by class instead of folding fail-closed
branches into measured capability:

- Measured evidence:
  - `scripts/estimate_large_scale_execution.py` anchors the 10-zone and
    100-zone planning rows to the measured conditional-output profile and the
    current Balfrin gate coefficients.
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
- TB-447 and TB-448 measured the latest regional split probe: one bounded
  Balfrin `postproc` job completed as job `4350232`, the preserved run root
  recorded `130` validation files, `53` hazard files, `729600`
  conditional-curve rows, `ready_for_demonstration_evidence` preservation
  status, and the run-root metrics that supersede TB-432 as the latest
  regional split state.
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
  - Runtime, storage, file count, and job-count estimates scale from the current
    measured coefficient set.
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
| 10-zone | projected from measured single-job support | 13.378 / 17.84 / 55.277 | 1,286,207 / 3,953,602 / 267,527,120 | 6 / 17 / 191 | Scenario cardinality remains the first bottleneck; source-zone automation is no longer first after the adjacent-candidate path | blocked_missing_inputs | next probe candidate if the scenario table stays compact |
| 100-zone | projection-only | 133.779 / 178.4 / 552.77 | 12,862,070 / 39,536,020 / 2,675,271,200 | 60 / 170 / 1,910 | Reducer pressure, manifest growth, and replay metadata dominate before live hazard throughput | blocked_missing_inputs | optimization task before any live step |
| regional split probe | measured on Balfrin | 24.0 / 24.0 / 24.0 | 34,565,323 / 34,565,323 / 34,565,323 | 130 / 130 / 130 | Measured regional split run-root evidence is now available; reducer pressure now outranks another comparison pass | ready_for_demonstration_evidence | reducer-pressure optimization first, then scenario batching, then local evidence |
| regional workflows | projection-only | 133.779 / 178.4 / 552.77 | 12,862,070 / 39,536,020 / 2,675,271,200 | 60 / 170 / 1,910 | Hazard throughput and multi-AOI support are still absent, so the broader class remains a projection-only planning class | blocked_missing_inputs | no scale-capability promotion until reducer-pressure and scenario-batching follow-up measurements are refreshed |
| Swiss-wide | projection-only | 347.825 / 463.84 / 1,437.203 | 33,441,382 / 102,793,652 / 6,955,705,120 | 156 / 442 / 4,966 | Balfrin access, authorization, and scheduler practicality remain the final boundary | blocked_missing_inputs | continued deferral until access and multi-AOI gaps close |

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

Extrapolated:

- Runtime, storage, file count, and job-count estimates scale linearly from the
  measured coefficient set.
- Operator effort is inferred from job count and jobs per AOI, not measured
  directly.

## Bottom Line

The current evidence supports a feasible 10-zone planning class, a deferred and
conditional 100-zone planning class, and no promoted broader regional or
Swiss-wide scale capability under the current single-node/postproc boundary.
The regional split branch is measured at the bounded probe level, and the
regional GIS/COG package pressure is now measured as blocked at the standard
root while the converted proof root is ready. The next decisive gap is reducer
and replay metadata pressure first, with scenario batching next and local
candidate evidence after that, rather than another regional split retry; the
exact unblock action for the GIS/COG branch is the conversion helper on the
standard root. The repository has measured single-job, four-zone
postproc, smallest multi-zone probe, bounded regional split, and regional
GIS/COG pressure evidence, but not measured larger multi-zone hazard
execution.
