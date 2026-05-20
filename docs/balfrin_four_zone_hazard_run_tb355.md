# TB-355 Four-Zone Balfrin Hazard Run

Date: 2026-05-20

## Outcome

TB-355 failed closed before scheduler submission. No `sbatch` command was run,
no job id was allocated, and no four-zone Balfrin hazard execution evidence was
measured.

## Gates Run

- Balfrin access preflight: `ready_for_read_only_collection`; SSH, remote clone
  hygiene, preserved run-root visibility, and scheduler query passed.
- Remote checkout: `/users/olifu/work/rust_rockfall` fast-forwarded on `main`
  from `327690d867fd475e674c76ad8f5f1e9fadc69e01` to
  `011f3737ef03e70566de0c68fa48eccd455c34c7` before package-specific checks.
- Four-zone package root:
  `/tmp/tb355_four_zone_handoff`.
- Reviewed handoff package:
  `/tmp/tb355_four_zone_handoff/package.json`.
- Authorization record:
  `/tmp/rust_rockfall/balfrin_multi_release_zone_demo_v1/balfrin_multi_zone_live_authorization_record_v1.yaml`.
- Smallest multi-zone authorization preflight:
  `blocked_reducer_budget`.

## Blocker

The TB-354 four-zone hazard package did not reach `ready_for_submit`.

`TB-352 failed closed before scheduler submission; no measured two-zone hazard evidence is available.`

The Balfrin-local package reported:

- package status: `mixed_provenance`
- four-zone hazard status: `deferred_missing_measured_two_zone_evidence`
- four-zone decision: `defer`
- four-zone decision classification:
  `deferred_missing_measured_two_zone_evidence`
- `ready_for_submit`: `false`
- measured two-zone evidence: `missing`
- source task: `TB-352`

The package-specific preflight also reported:

- preflight status: `blocked_reducer_budget`
- blocked reason:
  `single-job sufficiency or reducer scaling is not yet ready for the four-zone review package`
- submit contract status: `ready`
- reducer budget status: `ready`
- output profile status: `blocked_output_profile`
- output-budget acceptance status: `accepted`
- reviewed handoff package SHA-256:
  `993caf14fc4535fd6cc1d276f68a1e7039b28390419a56a2aec2f21fbb5f3492`
- authorization record SHA-256:
  `cf4b4ad1e59ba2aa00cc79a27b058bbcf77bdab161143d919a9d308d56087825`

Because the four-zone hazard package was not ready for submission, the reviewed
submit command was not executed.

## Planned Run Shape

- Release zones: `4`
- Scenarios: `4`
- Trajectory target: `2000`
- Expected runtime seconds: `0.863`
- Expected storage bytes: `8302`
- Partition: `postproc`

## Evidence Boundary

This is a pre-submit fail-closed report only. It is not measured Balfrin
four-zone hazard evidence, does not reduce the intermediate hazard-execution
gap, and does not support scale-up, distributed-execution, operational,
annual-frequency, physical-probability, risk, exposure, or vulnerability
claims.
