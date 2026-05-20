# TB-371 Balfrin Four-Zone Hazard Run Outcome

Date: 2026-05-20

## Summary

TB-371 repaired the four-zone handoff evidence contract so the live-submit
decision consumes the TB-368 preserved two-zone run root instead of stale
TB-362 failed-closed text.

After the repair, the regenerated four-zone package reported:

- `four_zone_status`: `ready_for_submit`
- `four_zone_decision`: `ready_for_submit`
- `four_zone_ready_for_submit`: `true`
- `measured_two_zone_evidence.source_task`: `TB-368`
- `measured_two_zone_evidence.preservation_gate_status`:
  `ready_for_demonstration_evidence`
- `four_zone_output_budget`: `accepted`
- `four_zone_budget_profile`: `next_larger_four_zone_review_only_probe`
- `release_zone_count`: `4`
- `scenario_count`: `4`

The Balfrin authorization preflight against the regenerated package reported
`preflight_status=ready_for_authorization_review`,
`submit_contract_status=ready`, `output_profile_status=ready`,
`reducer_budget_status=ready`, and `output_budget_acceptance_status=accepted`.

## Submitted Job

Exactly one live job was submitted:

- Job id: `4344163`
- Partition: `postproc`
- State: `COMPLETED`
- Exit code: `0:0`
- Elapsed: `00:05:10`
- Allocated CPUs: `16`
- Batch MaxRSS: `674528K`
- Work directory: `/users/olifu/work/rust_rockfall`
- Run root:
  `/scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_four_zone_hazard_v1`

The job stayed within the 30 minute wall-clock bound. The `postproc` capacity
check before submission showed idle CPUs, so the six-hour full-partition
rediscussion boundary was not reached.

## Collected Metrics

The post-run collector reported:

- `report_status`: `measured_run_root`
- `metrics_contract_status`: `complete`
- `memory_peak_mb`: `742.5703125`
- `validation_output_file_count`: `130`
- `validation_output_bytes`: `34565316`
- `hazard_output_file_count`: `53`
- `hazard_output_bytes`: `55832438`
- `output_file_count`: `46`
- `output_bytes`: `15583780`
- `conditional_curve_row_count`: `729600`
- Reduced output family counts include `trajectory_chunk_manifest=2`,
  `trajectory_execution_plan=1`, `trajectory_execution_index=1`,
  `trajectory_merge_state=1`, `reducer_chunk_manifest=2`,
  `reducer_execution_plan=1`, `reducer_execution_index=1`,
  `reducer_merge_state=1`, `map_package_manifest=1`, and
  `pilot_gis_package_manifest=1`.

## Preservation Gate

`scripts/summarize_balfrin_probe_preservation_gate.py` reported:

- `gate_status`: `ready_for_demonstration_evidence`
- `metrics_contract_status`: `complete`
- `required_run_root_entries_status`: `complete`
- Missing run-root entries: none
- Missing output families: none

## Boundaries

- Exactly one TB-371 live job was submitted.
- Only the `postproc` partition was used.
- No non-`postproc` partition was used.
- No distributed execution or scale-up claim is made.
- No operational hazard assessment is made.
- No annual-frequency, physical-probability, risk, exposure, or vulnerability
  claim is made.
- Generated Balfrin outputs remain under scratch or ignored output roots and
  are not committed.
