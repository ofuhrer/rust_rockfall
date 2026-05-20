# TB-366 Balfrin Two-Zone Hazard Run Outcome

Date: 2026-05-20

## Summary

TB-366 submitted the repaired smallest multi-zone Balfrin package on the
`postproc` partition after the immediate access, scheduler, and smallest
multi-zone authorization preflights passed. The live SLURM job completed, but
the result is not promoted to measured two-zone hazard capability because the
post-run preservation gate failed.

This is a live execution record and post-run blocker report, not an operational
hazard assessment and not scale-up evidence.

## Pre-Submit Gates

- Local `main`: `a00cda3f9e3f5967724f865062d77ebe04dbb079`
- Balfrin checkout: `/users/olifu/work/rust_rockfall`
- Remote checkout before repair: `8b94c12d6d1fa89a4928e15b243805b19600d31b`
- Remote checkout after fast-forward: `a00cda3f9e3f5967724f865062d77ebe04dbb079`
- Remote checkout hygiene after fast-forward: clean, `0` dirty paths
- Access preflight after fast-forward: `ready_for_read_only_collection`
- `ready_for_pre_submit`: `true`
- Smallest multi-zone authorization preflight:
  - `preflight_status`: `ready_for_authorization_review`
  - `authorization_status`: `authorized`
  - `reviewed_handoff_package_status`: `reviewed`
  - `authorization_record_status`: `reviewed`
  - `reducer_budget_status`: `ready`
  - `output_profile_status`: `ready`
  - `submit_contract_status`: `ready`
  - `output_budget_acceptance_status`: `accepted`

The `postproc` partition had idle capacity at submit time. The submitted job
requested one node, 16 CPUs, and a 30 minute limit, so it did not trigger the
six-hour full-partition rediscussion boundary.

## Submitted Job

- Job id: `4343898`
- Partition: `postproc`
- State: `COMPLETED`
- Exit code: `0:0`
- Elapsed: `00:00:36`
- MaxRSS: `450312K` for the batch step
- Allocated CPUs: `16`
- Work directory: `/users/olifu/work/rust_rockfall`
- Run root:
  `/scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_multi_release_zone_v1`
- Stdout:
  `/scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_multi_release_zone_v1/logs/slurm-4343898.out`
- Stderr:
  `/scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_multi_release_zone_v1/logs/slurm-4343898.err`

## Run-Root Inventory

The preserved run root contains these top-level files:

- `balfrin_probe_context.txt`
- `balfrin_probe_full_time.txt`
- `balfrin_hazard_stage_time.txt`
- `balfrin_probe_summary.json`
- `balfrin_submission_package.json`
- `balfrin_submission_package.md`
- `command_plan.json`
- `probe.sbatch`
- `logs/slurm-4343898.out`
- `logs/slurm-4343898.err`

The generated command plan used
`validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml` and
executed the gate validation plus `hazard/results/tschamut_public_pilot/gate_v1`
hazard build. The hazard command did not include the repaired
`--conditional-curve-export summary-only` and `--grid-csv-export none` controls
that the smallest two-zone evidence path requires.

## Collected Metrics

From `balfrin_probe_summary.json`:

- `report_status`: `incomplete_run_root`
- `metrics_contract_status`: `blocked_missing_inputs`
- Missing mandatory metric: `memory_peak_mb`
- Total wall seconds recorded by collector: `11.61107430300035`
- Validation output: `130` files, `34565505` bytes
- Hazard output: `99` files, `273194247` bytes
- Hazard output root:
  `/users/olifu/work/rust_rockfall/hazard/results/tschamut_public_pilot/gate_v1`
- Hazard manifest:
  `/users/olifu/work/rust_rockfall/hazard/results/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_manifest.json`

The SLURM sidecar timings were also written:

- Full command-sequence wall time: `33.31698803200561`
- Hazard-stage wall time: `12.505620973999612`

## Preservation Gate

`scripts/summarize_balfrin_probe_preservation_gate.py` reported:

- `preservation_gate_status`: `blocked_missing_inputs`
- `gate_status`: `blocked_missing_inputs`
- `required_run_root_entries_status`: `blocked_missing_inputs`
- `output_family_status`: `blocked_missing_measured_output`
- `run_root_output_budget_audit.audit_status`: `blocked_missing_replay_artifacts`

Blocked reasons:

- `metrics_contract:blocked_missing_inputs`
- Missing run-root entries:
  `balfrin_probe_metrics.json`, `output`,
  `output/validation_balfrin_probe_manifest.json`,
  `output/validation_balfrin_probe_scaling_summary.json`,
  `output/trajectory_chunks`, and `output/chunks`
- `output_tier:blocked_missing_measured_output`
- Output budget audit exceeded the smallest live two-zone thresholds, including
  `manifest_size_bytes=544515 > 11000`, `output_file_count=99 > 20`,
  `sidecar_file_count=32 > 11`, `reducer_manifest_file_count=4 > 2`,
  `reducer_manifest_bytes=69172 > 400`, and `reducer_chunk_count=4 > 2`
- The audit also reported missing replay-critical families and missing
  `probe_manifest_sha256`

## Outcome

TB-366 produced a completed `postproc` job, but it did not produce a measured
two-zone Balfrin hazard run that is preserved and ready for collection. The
persistent blocker is that the submit path still executed the legacy gate
manifest/output contract even though the pre-submit package preflight judged the
smallest two-zone shape as ready. The next task must treat this as blocked
post-run evidence unless it repairs the submit contract and reruns the live
path under the same boundaries.

## Boundaries

- No non-`postproc` partition was used.
- No distributed execution or scale-up claim is made.
- No operational hazard assessment is made.
- No annual-frequency, physical-probability, risk, exposure, or vulnerability
  claim is made.
- Generated Balfrin outputs remain under scratch or ignored output roots and
  are not committed.
