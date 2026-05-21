# Swiss-Scale Feasibility Projection From Measured Evidence

Status: projection-only synthesis. This report does not authorize a new run,
claim operational readiness, or convert projection into physical, annual,
risk, exposure, or vulnerability semantics.

## Recommendation

- 10-zone: feasible as a projection-supported planning class on the current
  single-node/postproc boundary. The next feasibility step is a measured
  10-zone probe only after the current `source_zone_footprint_overlap`
  upstream blocker is cleared.
- 100-zone: conditionally feasible and deferred. The next step is further
  reducer, manifest, and scheduler pressure reduction, not a live run.
- Regional: out of reach under current single-node/postproc constraints. The
  next step is to keep it as a no-go planning branch until multi-AOI evidence
  exists.
- Swiss-wide: out of reach under the current authorization boundary. The next
  step is no-go until multi-AOI evidence and authorization gaps close.

## Evidence Basis

The current projection separates evidence by class instead of folding fail-closed
branches into measured capability:

- Measured evidence:
  - `scripts/estimate_swiss_wide_execution_envelope.py` anchors the projection
    to measured support of 1 AOI, 10 release zones, 6 trajectories, and 60
    units per job.
  - `scripts/summarize_balfrin_scale_readiness_matrix.py` records the measured
    single-job boundary, TB-307 target-area metrics-completion rerun, TB-312
    four-zone postproc/reducer package, TB-368 preserved two-zone evidence, and
    the current claim boundaries.
  - `scripts/summarize_balfrin_management_demo_package.py` keeps runtime,
    restartability, GIS scope, uncertainty, and claim boundaries in the measured
    section while separating projection-only and failed-closed sections.
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
    candidate-screening branch and still failed closed at
    `source_zone_footprint_overlap`: the committed 4x4 crop has four valid
    interior cells, all four remain covered by the frozen source-zone footprint,
    and slope screening is not reached.
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
  - `job_count > 1` crosses the current single-job evidence boundary.
  - `release_zone_count > 10` or `trajectory_count > 6` exceeds the measured
    support envelope used by the Swiss-wide helper.
  - GIS/COG conversion remains blocked until the packaged AOI root has the
    required manifest fields and raster package metadata.
  - `scale_up_authorized=false` and `distributed_execution_authorized=false`
    remain hard boundaries.
- Unknowns:
  - The committed tiny management-AOI crop remains blocked by
    `source_zone_footprint_overlap`, but TB-389 showed that the restaged
    management-AOI terrain can produce a nonempty deterministic candidate
    bundle. Candidate generation still remains separate from scenario
    generation and prepared-pilot packaging.
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
| 10-zone | projected from measured single-job support | 13.378 / 17.84 / 55.277 | 1,286,207 / 3,953,602 / 267,527,120 | 6 / 17 / 191 | Single-job supported; manifest size remains the first bottleneck; no measured hazard execution yet | blocked_missing_inputs | next probe candidate after the current upstream blocker clears |
| 100-zone | projection-only | 133.779 / 178.4 / 552.77 | 12,862,070 / 39,536,020 / 2,675,271,200 | 60 / 170 / 1,910 | reducer_merge_multi_job_pressure; scheduler_practicality_requires_authorization; manifest size still first bottleneck | blocked_missing_inputs | deferred planning case; not the next live step |
| regional | projection-only | 133.779 / 178.4 / 552.77 | 12,862,070 / 39,536,020 / 2,675,271,200 | 60 / 170 / 1,910 | multi-job pressure without measured distributed support; manifest size still first bottleneck | blocked_missing_inputs | no-go planning branch until multi-AOI evidence exists |
| Swiss-wide | projection-only | 347.825 / 463.84 / 1,437.203 | 33,441,382 / 102,793,652 / 6,955,705,120 | 156 / 442 / 4,966 | 26 jobs, scheduler_practicality_requires_authorization, manifest size still first bottleneck | blocked_missing_inputs | no-go until multi-AOI evidence and authorization gaps close |

## Measured Versus Extrapolated

Measured:

- Single-job support is bounded at 1 AOI, 10 release zones, and 6 trajectories
  per release zone.
- The readiness matrix records TB-312 four-zone postproc/reducer evidence, but
  that evidence is still postproc-only and does not upgrade hazard execution
  capability.
- The readiness matrix records TB-368 preserved two-zone evidence and TB-386 as
  the current management-AOI failed-closed branch blocked by
  `source_zone_footprint_overlap`; neither upgrades hazard execution
  capability.
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
still measured hazard execution: the repository has measured single-job,
four-zone postproc, and smallest multi-zone probe evidence, but not measured
larger multi-zone hazard execution, and the current management-AOI branch
remains blocked by `source_zone_footprint_overlap` upstream of any new
candidate-screening step.
