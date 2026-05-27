# TB-642 Balfrin Larger Hazard-Throughput Pre-Submit Check

Date: 2026-05-27

TB-642 checked whether the current Balfrin helpers can submit a bounded
`postproc` hazard-throughput run larger than the TB-619 four-zone support point.
The answer is no: the current executable hazard-throughput package path still
tops out at four zones.

## Checks

- Balfrin access preflight: ready for read-only collection and pre-submit checks.
- `postproc` queue snapshot: 10 idle nodes, 12 running jobs, 0 pending jobs, 1
  current-user job.
- Next live-run decision gate: `defer`.
- Decision summary: reducer-pressure optimization is ranked first because live
  scale remains unauthorized in the current decision surface.
- Eight-zone handoff probe:
  `scripts/generate_balfrin_multi_release_zone_demo_handoff.py --requested-release-zone-batch-size 8`.

## Blocker

The eight-zone handoff is not a supported larger hazard-throughput submit path:

- the active eight-zone output-budget check reports
  `blocked_threshold_exceeded`;
- manifest bytes are `22,570`, above the four-zone review profile limit of
  `22,000`;
- output files are `35`, above the four-zone review profile limit of `28`;
- replay-critical `trajectory_csv`, `deposition_csv`, and `impact_events_csv`
  family counts are `8`, above the four-zone review profile limit of `4`;
- the generated `four_zone_hazard_execution_package` remains fixed at
  `release_zone_count=4` and `status=ready_for_submit`.

This is a concrete pre-submit blocker for TB-642. Submitting another run through
the existing hazard-throughput path would rerun the four-zone shape rather than
measure hazard throughput beyond TB-619.

## Next Useful Work

Before a larger hazard-throughput run can be submitted, one of these changes is
needed:

- add a real >4-zone hazard-throughput package profile with accepted replay
  family limits and a generated command plan that actually targets that size; or
- reduce/merge replay-critical per-zone outputs for >4-zone hazard-throughput
  runs while preserving enough artifacts to replay and compare the result.

The existing 24/32/100-zone diagnostic runner remains useful reducer-pressure
evidence, but it is not hazard-throughput evidence.
