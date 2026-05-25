# TB-557 Balfrin Bounded Reduced-Output Probe Outcome

Date: 2026-05-25

## Summary

TB-557 submitted one bounded `postproc` Balfrin probe from the reviewed
reduced-output handoff generated after TB-556. The job completed successfully,
and the preserved run root contains collected runtime, memory, validation
output, hazard output, reducer, manifest, and SLURM accounting evidence.

This is measured bounded-run evidence for the research diagnostic path. It is
not an operational hazard assessment, not a Swiss-wide scale-up claim, and not
distributed-execution evidence.

## Pre-Submit Gates

- Local and Balfrin checkout commit: `6a49586`
- Balfrin checkout: `/users/olifu/work/rust_rockfall`
- Access preflight: `ready_for_read_only_collection`
- Reviewed handoff package:
  `/tmp/rust_rockfall/tb557_reduced_output_handoff/balfrin_multi_release_zone_demo_package_v1.json`
- Authorization record:
  `/tmp/rust_rockfall/tb557_reduced_output_handoff/balfrin_multi_zone_live_authorization_record_v1.yaml`
- Authorization preflight: `ready_for_authorization_review`
- Submit contract: `ready`
- Output budget gate: `ready`
- Package status: `mixed_provenance`
- Package constraint status: `warning`
- No-submit handoff contract before launch: `ready_for_review`

The historical reviewed run roots already contained previous evidence, so the
live job used a fresh TB-557 run root under the same Balfrin scratch prefix
instead of overwriting preserved outputs.

## Submitted Job

- Job id: `4366534`
- Partition: `postproc`
- State: `COMPLETED`
- Exit code: `0:0`
- Elapsed: `00:01:29`
- Batch MaxRSS: `390804K`
- Nodes: `1`
- Tasks: `1`
- CPUs per task: `16`
- Time limit: `00:30:00`
- Run root:
  `/scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tb557_bounded_reduced_output_probe_v1`

The `postproc` queue had idle capacity before submission, so the six-hour
full-partition rediscussion boundary was not reached.

## Collected Metrics

From `balfrin_probe_metrics_collected_tb557.json` and
`slurm_accounting_4366534.psv` under the run root:

- `metrics_contract_status`: `complete`
- Missing mandatory metrics: none
- `git_commit`: `6a49586`
- Total wall seconds recorded by collector: `6.536354579031467`
- `memory_peak_mb`: `381.64453125`
- Validation output: `130` files, `34565316` bytes
- Hazard output: `57` files, `31436405` bytes
- Conditional curve rows: `729600`
- Reduced output families include:
  - `hazard_layer`: `36`
  - `deposition_points`: `1`
  - `hazard_metadata`: `1`
  - `trajectory_chunk_manifest`: `2`
  - `trajectory_execution_index`: `1`
  - `trajectory_execution_plan`: `1`
  - `trajectory_merge_state`: `1`
  - `reducer_chunk_manifest`: `2`
  - `reducer_execution_index`: `1`
  - `reducer_execution_plan`: `1`
  - `reducer_merge_state`: `1`
  - `map_package_manifest`: `1`
  - `pilot_gis_package_manifest`: `1`

## Preservation Gate

`scripts/summarize_balfrin_probe_preservation_gate.py` reported:

- `gate_status`: `ready_for_demonstration_evidence`
- `required_run_root_entries_status`: `complete`
- `output_family_summaries.status`: `sufficient`
- Blocked reasons: none

## Evidence Promotion

`scripts/summarize_balfrin_evidence_bundle.py` now promotes this run as the
current measured multi-zone Balfrin evidence:

- `multi_zone_balfrin_evidence.status`: `measured`
- `multi_zone_balfrin_evidence.evidence_type`: `measured`
- `multi_zone_balfrin_evidence.slurm_job_id`: `4366534`
- `latest_bounded_probe_interpretation_gate_report.interpretation_status`:
  `inconclusive_conditional_diagnostic`

The interpretation gate accepts the artifact as a conditional diagnostic while
keeping convergence and physical-credibility claims inconclusive.

## Boundaries

- Exactly one TB-557 live job was submitted.
- Only the `postproc` partition was used.
- No non-`postproc` partition was used.
- No distributed execution or scale-up claim is made.
- No operational hazard assessment is made.
- No annual-frequency, physical-probability, risk, exposure, or vulnerability
  claim is made.
- Generated Balfrin outputs remain under scratch or ignored output roots and
  are not committed.
