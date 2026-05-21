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
- Regional: out of reach under current single-node/postproc constraints. The
  next step is continued deferral until multi-AOI hazard-throughput evidence
  exists.
- Swiss-wide: out of reach under the current authorization boundary. The next
  step is continued deferral until Balfrin access, authorization, and multi-AOI
  evidence gaps close.

## Bottleneck Ranking

The adjacent-candidate branch moved the first blocker away from source-zone
automation and onto the remaining planning bottlenecks:

1. Scenario cardinality and manifest size.
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
    reflects the adjacent-candidate scenario path.
  - TB-407 measured the smallest multi-zone Balfrin probe on `postproc`, with
    `130` validation files, `53` hazard files, `729600` conditional-curve
    rows, and preservation-ready run-root evidence.
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
  - TB-321 and TB-309 are also failed-closed submit-contract mismatches, not
    measured hazard runs.
- No-go thresholds:
  - `scenario_cardinality` and `manifest_size` remain the first planning
    bottlenecks for larger bounded probes.
  - `reducer_pressure` and replay metadata growth remain the next bottlenecks
    for 100-zone planning.
  - `hazard_throughput` remains out of reach until a larger measured multi-zone
    hazard execution exists.
  - GIS/COG conversion remains blocked until the packaged AOI root has the
    required manifest fields and raster package metadata.
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
| regional | projection-only | 133.779 / 178.4 / 552.77 | 12,862,070 / 39,536,020 / 2,675,271,200 | 60 / 170 / 1,910 | Hazard throughput and multi-AOI support are still absent | blocked_missing_inputs | continued deferral until larger measured evidence exists |
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
- TB-389 adds a measured real-AOI candidate bundle on the restaged management
  terrain, which is useful for downstream scenario pressure work but remains a
  heuristic candidate-generation result rather than validated release-zone
  evidence.
- The largest current real output in this checkout (`target_gate_v1`) packages
  to a 29-file scratch bundle, converts to a 29-file COG-ready scratch bundle,
  and matches layer inventory parity; that is demonstration evidence only and
  does not authorize operational GIS claims.

Extrapolated:

- Runtime, storage, file count, and job-count estimates scale linearly from the
  measured coefficient set.
- Operator effort is inferred from job count and jobs per AOI, not measured
  directly.

## Bottom Line

The current evidence supports a feasible 10-zone planning class, a deferred and
conditional 100-zone planning class, and no-go for regional and Swiss-wide
execution under the current single-node/postproc boundary. The key separator is
now the adjacent-candidate bottleneck ranking: scenario cardinality first,
then reducer pressure, then hazard throughput, GIS packaging, and Balfrin
access. The repository has measured single-job, four-zone postproc, and
smallest multi-zone probe evidence, but not measured larger multi-zone hazard
execution.
