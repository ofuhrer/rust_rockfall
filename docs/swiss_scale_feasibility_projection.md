# Swiss-Scale Feasibility Projection From Measured Evidence

Status: projection-only synthesis. This report does not authorize a new run,
claim operational readiness, or convert projection into physical, annual,
risk, exposure, or vulnerability semantics.

## Recommendation

- Feasible: 10-zone, single-AOI workflow on the current single-node/postproc
  boundary.
- Conditionally feasible: 100-zone workflow only as a deferred planning case;
  it crosses into multi-job pressure and needs additional manifest/reducer
  policy work before it becomes a practical target.
- Out of reach: regional and Switzerland-wide workflows under current
  single-node/postproc constraints.

## Evidence Basis

Measured evidence used here is limited to existing repository helpers and
preserved outputs:

- `scripts/estimate_swiss_wide_execution_envelope.py` anchors the execution
  frontier to measured support of 1 AOI, 10 release zones, 6 trajectories, and
  60 units per job.
- `scripts/estimate_large_scale_execution.py` provides the 10-zone output
  calibration cross-check: 46 files and 15,613,000 estimated bytes for the
  scalable conditional profile with GeoTIFF export and 2x2 chunking.
- `scripts/summarize_large_aoi_gis_cog_stress_test.py` classifies the GIS/COG
  path as blocked because the packaged AOI root is missing the pilot GIS
  package manifest fields needed for conversion and the standard package
  remains COG-blocked.
- `scripts/summarize_balfrin_evidence_bundle.py` now carries TB-352 as the
  canonical smallest multi-zone fail-closed branch; it is distinct from the
  measured rows and does not add measured hazard-execution support.
- The same-scale and Swiss-wide envelope helpers reuse the current measured
  manifest pressure signal: manifest size is the first bottleneck, with the
  generator evidence showing 120 scenario rows, 30 candidate release-zone
  records, and a 147,566-byte manifest versus a 35,911-byte CSV.

## Projection Table

The runtime, storage, and file counts below are the nominal bands returned by
the Swiss-wide envelope helper. Low and high bands are inherited from the
current measured coefficients and should be read as projection bounds, not new
measurements.

| Case | Runtime s (low / nominal / high) | Storage bytes (low / nominal / high) | File count (low / nominal / high) | Reducer and manifest pressure | GIS/COG status | Operator effort | Recommendation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 10-zone | 13.378 / 17.84 / 55.277 | 1,286,207 / 3,953,602 / 267,527,120 | 6 / 17 / 191 | Single-job supported; manifest_size remains the first bottleneck | blocked_missing_inputs (missing pilot GIS package manifest) | 1 job, 1 job per AOI | feasible |
| 100-zone | 133.779 / 178.4 / 552.77 | 12,862,070 / 39,536,020 / 2,675,271,200 | 60 / 170 / 1,910 | reducer_merge_multi_job_pressure; scheduler_practicality_requires_authorization; manifest_size still first bottleneck | blocked_missing_inputs (missing pilot GIS package manifest) | 10 jobs, 10 jobs per AOI | conditionally feasible, but deferred |
| regional | 133.779 / 178.4 / 552.77 | 12,862,070 / 39,536,020 / 2,675,271,200 | 60 / 170 / 1,910 | multi-job pressure without measured distributed support; manifest_size still first bottleneck | blocked_missing_inputs (missing pilot GIS package manifest) | 10 jobs, 1 job per AOI | out of reach |
| Swiss-wide | 347.825 / 463.84 / 1,437.203 | 33,441,382 / 102,793,652 / 6,955,705,120 | 156 / 442 / 4,966 | 26 jobs, scheduler_practicality_requires_authorization, manifest_size still first bottleneck | blocked_missing_inputs (missing pilot GIS package manifest) | 26 jobs, 1 job per AOI | out of reach |

## Measured Versus Extrapolated

Measured:

- Single-job support is real and bounded at 1 AOI, 10 release zones, and 6
  trajectories per release zone.
- The 10-zone output-family cross-check remains small enough to stay within the
  current single-node boundary, with 46 files and 15.6 MB of estimated output
  under the scalable conditional profile.
- GIS/COG packaging remains blocked by missing pilot GIS manifest fields and
  raster readiness gaps.

Extrapolated:

- Runtime, storage, and file counts scale linearly from the measured coefficient
  set.
- Memory stays in the current single-job band because there is no larger
  measured memory series.
- Operator effort is approximated from job count and jobs per AOI. When job
  count rises above 1, the report treats the case as multi-job pressure rather
  than a single-job execution target. This is an inference from scheduler
  shape, not a measured human-time benchmark.

## No-Go Thresholds

- `job_count > 1` is the current practical threshold where reducer-merge and
  scheduler pressure stop being single-job evidence.
- `release_zone_count > 10` or `trajectory_count > 6` exceed the measured
  support boundary used by the Swiss-wide envelope helper.
- TB-352 failed closed before scheduler submission, so a partial or fail-closed
  multi-zone branch still does not count as measured support for the 100-zone
  or Swiss-wide rows.
- GIS/COG conversion remains a no-go until the packaged AOI root has the
  required manifest fields and the raster package can be represented with the
  expected tiling and overview metadata.
- `scale_up_authorized=false` and `distributed_execution_authorized=false`
  remain hard boundaries in the current helpers.

## Unknowns

- The current environment does not recover the target-area validation and
  hazard outputs, so the ratio to those preserved outputs remains unresolved.
- There is no measured multi-AOI Balfrin run in the repository, so the 100-zone,
  regional, and Swiss-wide rows are projections only. TB-352 is fail-closed,
  not measured.
- The manifest estimate is threshold-based rather than a larger measured byte
  series; the first bottleneck is known, but there is no bigger manifest
  measurement to fit.
- Partial multi-zone evidence would still be insufficient even if it existed in
  the future; the projection only advances on measured hazard execution, not on
  incomplete branches.

## Bottom Line

Current evidence supports a bounded yes for the 10-zone class, a deferred and
conditional projection for the 100-zone class, and no-go for regional and
Switzerland-wide execution under the current single-node/postproc boundary.
The GIS/COG path is separately blocked and does not yet support a Swiss-scale
packaging claim.
