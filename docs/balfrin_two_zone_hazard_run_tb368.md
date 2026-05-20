# TB-368 Balfrin Two-Zone Hazard Rerun Outcome

Date: 2026-05-20

## Summary

TB-368 verified the post-TB-367 trajectory/reducer worker repair and submitted
one authorized bounded rerun on Balfrin `postproc`. The rerun completed and the
preserved run root now satisfies the preservation gate that TB-367 failed.

This is measured two-zone run-root preservation evidence for the bounded
research diagnostic path. It is not an operational hazard assessment, not a
scale-up claim, and not distributed-execution evidence.

## Dry-Run Proof

Local generate-only proof used:

```bash
PYENV_VERSION=system uv run python scripts/submit_balfrin_probe.py \
  validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml \
  --run-root /tmp/rust_rockfall/tb368_generate_only \
  --run-id tschamut_public_balfrin_multi_release_zone_v1 \
  --partition postproc --time 00:30:00 --nodes 1 --ntasks 1 \
  --cpus-per-task 16 --generate-only
```

The generated command plan preserved:

- `--trajectory-workers 2`
- `--reducer-workers 2`
- `--output-dir /private/tmp/rust_rockfall/tb368_generate_only/output`
- `run_root_output_contract.trajectory_chunks_dir`:
  `/private/tmp/rust_rockfall/tb368_generate_only/output/trajectory_chunks`
- `run_root_output_contract.reducer_chunks_dir`:
  `/private/tmp/rust_rockfall/tb368_generate_only/output/chunks`
- `probe.sbatch` uses `${RUN_ROOT}/command_plan.json`
- `probe.sbatch` does not regenerate the legacy plan with
  `validate_public_real_site_conditional_pilot_run.py`

## Pre-Submit Gates

- Local checkout before live work: `c2c56d44fe340b1ba0ba29861babd65bb133a63c`
- Balfrin checkout: `/users/olifu/work/rust_rockfall`
- Remote checkout after fast-forward: `c2c56d44fe340b1ba0ba29861babd65bb133a63c`
- Remote checkout hygiene after fast-forward: clean
- Access preflight after fast-forward: `ready_for_read_only_collection`
- `ready_for_pre_submit`: `true`
- Smallest multi-zone authorization preflight:
  - `preflight_status`: `ready_for_authorization_review`
  - `authorization_status`: `authorized`
  - `submit_contract_status`: `ready`
  - `output_profile_status`: `ready`
  - `reducer_budget_status`: `ready`
  - `output_budget_acceptance_status`: `accepted`

The planned job used one node, 16 CPUs, and a 30 minute limit on `postproc`.
`postproc` had idle capacity before submission, so the six-hour full-partition
rediscussion boundary was not reached.

## Submitted Job

- Job id: `4344114`
- Partition: `postproc`
- State: `COMPLETED`
- Exit code: `0:0`
- Elapsed: `00:00:41`
- Batch MaxRSS: `39372K`
- Allocated CPUs: `16`
- Work directory: `/users/olifu/work/rust_rockfall`
- Run root:
  `/scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_multi_release_zone_v1`

## Collected Metrics

From `balfrin_probe_metrics_collected_tb368.json` and the preservation-gate
artifact written under the run root:

- `report_status`: `measured_run_root`
- `metrics_contract_status`: `complete`
- Missing mandatory metrics: none
- `memory_peak_mb`: `172.921875`
- Total wall seconds recorded by collector: `6.570337791999918`
- Hazard output: `53` files, `55829693` bytes
- `output/trajectory_chunks`: present
- Trajectory chunk files under `output/trajectory_chunks`: `4`
- Reduced output family counts include:
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
- Missing run-root entries: none
- `output_family_summaries.status`: `sufficient`
- Missing required output families: none
- Blocked reasons: none

The TB-367 blocker, missing `output/trajectory_chunks` and trajectory
restartability metadata, is resolved for this preserved run root.

## Boundaries

- Exactly one TB-368 live job was submitted.
- Only the `postproc` partition was used.
- No non-`postproc` partition was used.
- No distributed execution or scale-up claim is made.
- No operational hazard assessment is made.
- No annual-frequency, physical-probability, risk, exposure, or vulnerability
  claim is made.
- Generated Balfrin outputs remain under scratch or ignored output roots and
  are not committed.
