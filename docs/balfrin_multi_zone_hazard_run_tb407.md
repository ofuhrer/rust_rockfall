# TB-407 Balfrin Smallest Multi-Zone Probe Outcome

Date: 2026-05-21

## Summary

TB-407 consumed the TB-406 repaired smallest multi-zone handoff, refreshed the
Balfrin access gate, submitted one bounded job on the `postproc` partition, and
preserved the measured run-root evidence.

This is measured Balfrin `postproc` evidence for the bounded research
diagnostic path. It is not an operational hazard assessment, not a scale-up
claim, and not distributed-execution evidence.

## Pre-Submit Gates

- Local checkout before live work: `f326e7c350c3e00ce930fbdb019eb9274c6e6175`
- Balfrin checkout: `/users/olifu/work/rust_rockfall`
- Remote checkout after fast-forward: `f326e7c350c3e00ce930fbdb019eb9274c6e6175`
- Remote checkout hygiene after fast-forward: clean
- Access preflight after fast-forward: `ready_for_read_only_collection`
- `ready_for_pre_submit`: `true`
- TB-406 repaired handoff preflight, regenerated on Balfrin under
  `validation/private/tb407_repaired_handoff_remote`:
  - `preflight_status`: `ready_for_authorization_review`
  - `handoff_status`: `ready_for_live_postproc_submission`
  - `authorization_record_allows_one_bounded_probe`: `true`
  - `ready_for_authorized_submission`: `true`
  - `first_blocker`: `null`
  - `submit_contract_status`: `ready`
  - `output_budget_acceptance_status`: `accepted`
  - `threshold_profile_id`: `smallest_live_two_zone_probe`

Two earlier command attempts stopped before scheduler submission because
node-local `/tmp` did not preserve the access JSON or handoff package across
Balfrin SSH sessions. The successful submit used the allowed ignored
`validation/private` handoff package and a shared scratch access-preflight
record.

## Submitted Job

- Job id: `4347579`
- Partition: `postproc`
- State: `COMPLETED`
- Exit code: `0:0`
- Elapsed: `00:00:29`
- Allocated CPUs: `16`
- Slurm batch MaxRSS: `5492K`
- Work directory: `/users/olifu/work/rust_rockfall`
- Run root:
  `/scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_multi_release_zone_v1`

## Collected Metrics

From `tb407_collect_metrics_4347579.json` under the ignored support root:

- Metrics contract status: `complete`
- Missing mandatory metrics: none
- Collector wall time: `5.2313875560003` seconds
- Collector peak memory: `172.921875` MB
- Validation output: `130` files, `34565330` bytes
- Hazard output: `53` files, `55831799` bytes
- Conditional curve rows: `729600`
- Trajectory decision counts: `{"reused_completed_state": 2}`
- Reducer decision counts: `{"reused_completed_state": 2}`

Measured preservation checksums:

- `command_plan`: `2921b3eccba4d087efa7fca3581fcdd763c01467b3302a6532591a93fa4bd07c`
- `probe_metrics`: `969082d9d6668a964e1d88651220d2a6b9ba133a71e197b0a2a7df3f9d0872f9`
- `hazard_manifest`: `270259e8ca47820c6c4aadebfa2a44e9492d8943d830904ab1d5382425499c84`
- `scaling_summary`: `402f093432e8ab3f89ea97043d7736c2a54e70cdc2f8a835cdc771b0354b6cc7`

## Preservation Gate

`scripts/summarize_balfrin_probe_preservation_gate.py` reported:

- `preservation_gate_status`: `ready_for_demonstration_evidence`
- `required_run_root_entries_status`: `complete`
- Missing run-root entries: none
- `output_family_summaries.status`: `sufficient`
- Missing required output families: none
- Blocked reasons: none

## Boundaries

- Exactly one TB-407 scheduler submission reached `sbatch`.
- Only the `postproc` partition was used.
- No non-`postproc` partition was used.
- No distributed execution or scale-up claim is made.
- No operational hazard assessment is made.
- No annual-frequency, physical-probability, risk, exposure, or vulnerability
  claim is made.
- Generated Balfrin outputs remain under scratch or ignored output roots and
  are not committed.
