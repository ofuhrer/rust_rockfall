# Balfrin Single-Release-Zone Execution Report

Status: blocked execution report, not measured Balfrin evidence.

This report records the first TB-102 attempt for the frozen Balfrin
single-release-zone pilot contract. The repository has the contract, dry-run
case planner, probe driver, metrics collector, and runbook scaffolding, but the
actual execution path is blocked before any Balfrin job can run.

## Attempted commands

```bash
PYENV_VERSION=system uv run python scripts/check_balfrin_tschamut_readiness.py \
  validation/pilot_runs/tschamut_public_balfrin_single_release_zone_pilot_contract_v1.yaml \
  --format json
```

```bash
PYENV_VERSION=system uv run python scripts/summarize_balfrin_single_release_zone_pilot_contract.py \
  --format json
```

```bash
PYENV_VERSION=system uv run python scripts/plan_balfrin_single_release_zone_case_dry_run.py \
  --format json
```

## Exact failure class

- Failure class: manifest schema mismatch
- Blocking message: the readiness checker requires
  `public_real_site_conditional_pilot_run_v1`, but the selected Balfrin contract
  uses `balfrin_single_release_zone_pilot_contract_v1`
- Effect: the readiness check returns `blocked_for_balfrin_readiness` before any
  submission, validation, or metrics collection can start

## Execution outcome

- Readiness status: `blocked_for_balfrin_readiness`
- Readiness checker return code: `2`
- QGIS warning: present, but non-blocking
- Run root: not created
- Balfrin job execution: not started
- Metrics bundle: not produced

## Metrics status

The following metrics were requested by TB-102 but could not be collected
because the run never executed:

- wall time
- memory peak
- output file counts
- output bytes
- reduced-output family counts
- conditional-curve counts
- restartability metadata

## Boundary note

This blocked report does not claim operational readiness, scale-up, annual
frequency, physical probability, risk, exposure, vulnerability, or distributed
execution. It only records the exact pre-execution failure class for the current
checkout.

## Next action

TB-115 later teaches the readiness path to recognize the Balfrin contract
schema through a contract-aware branch. This report preserves the original
TB-102 failure class for historical context.

## TB-116 attempt

Status: blocked execution report, not measured Balfrin evidence.

This addendum records the TB-116 attempt to execute and collect the canonical
Balfrin single-release-zone demo from the frozen public conditional pilot
freeze. Readiness, contract rendering, and dry-run planning were all
successful, but live scheduler submission is unavailable in this environment.

### Attempted commands

```bash
PYENV_VERSION=system uv run python scripts/check_balfrin_tschamut_readiness.py \
  validation/pilot_runs/tschamut_public_balfrin_single_release_zone_pilot_contract_v1.yaml \
  --format json
```

```bash
PYENV_VERSION=system uv run python scripts/summarize_balfrin_single_release_zone_pilot_contract.py \
  --format json
```

```bash
PYENV_VERSION=system uv run python scripts/plan_balfrin_single_release_zone_case_dry_run.py \
  --format json
```

```bash
PYENV_VERSION=system uv run python scripts/submit_balfrin_probe.py \
  validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml \
  --generate-only \
  --run-root /private/tmp/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_single_release_zone_v1 \
  --run-id tschamut_public_balfrin_single_release_zone_v1 \
  --partition postproc \
  --time 00:30:00 \
  --nodes 1 \
  --ntasks 1 \
  --cpus-per-task 16
```

```bash
PYENV_VERSION=system uv run python scripts/submit_balfrin_probe.py \
  validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml \
  --submit \
  --run-root /private/tmp/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_single_release_zone_v1 \
  --run-id tschamut_public_balfrin_single_release_zone_v1 \
  --partition postproc \
  --time 00:30:00 \
  --nodes 1 \
  --ntasks 1 \
  --cpus-per-task 16
```

### Exact failure class

- Failure class: `scheduler_submission_failed`
- Blocking message: `submit_balfrin_probe.py --submit` raises `FileNotFoundError`
  because `sbatch` is not installed or exposed on this node
- Effect: the run root is generated, but no scheduler job can be submitted, so
  there is no live measured Balfrin execution to collect

### Execution outcome

- Readiness status: `ready_for_balfrin_target_gate`
- Contract summary: `ready`
- Dry-run case plan: `ready`
- Submission package: generated successfully
- Scheduler submission: blocked before `submitted_job_id` can be produced
- Run root: generated only as a submission package, not as a live measured run
- Metrics bundle: collection on the generated root returns
  `metrics_contract_status: blocked_missing_inputs`

### Metrics status

The collector can still read existing hazard-result artifacts in the repository,
but the TB-116 run root itself did not execute. The blocked metrics summary is
missing the following fields from the live run contract:

- `memory_peak_mb`
- `validation_output.file_count`
- `validation_output.bytes`
- `hazard_output.file_count`
- `hazard_output.bytes`
- `restartability_metadata.trajectory_plan_id`
- `restartability_metadata.trajectory_decision_counts`

### Boundary note

This blocked report does not claim measured Balfrin execution, operational
readiness, annual frequency, physical probability, risk, exposure,
vulnerability, or distributed execution. It only records the exact
orchestration failure class for the current checkout and environment.

## TB-117 attempt

Status: blocked execution report, not measured Balfrin evidence.

This addendum records the TB-117 attempt to execute and collect the canonical
Balfrin single-release-zone demo. The contract summary and dry-run planner
remained available, but the canonical submit path could not start a scheduler
job on this node, so no measured run root was produced.

### Attempted commands

```bash
PYENV_VERSION=system uv run python scripts/check_balfrin_tschamut_readiness.py \
  validation/pilot_runs/tschamut_public_balfrin_single_release_zone_pilot_contract_v1.yaml \
  --format json
```

```bash
PYENV_VERSION=system uv run python scripts/submit_balfrin_probe.py \
  validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml \
  --run-root /private/tmp/balfrin_tb117_probe_gate \
  --run-id tschamut_public_balfrin_single_release_zone_v1 \
  --partition postproc \
  --time 00:30:00 \
  --nodes 1 \
  --ntasks 1 \
  --cpus-per-task 16 \
  --generate-only
```

```bash
PYENV_VERSION=system uv run python scripts/submit_balfrin_probe.py \
  validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml \
  --run-root /private/tmp/balfrin_tb117_probe_gate \
  --run-id tschamut_public_balfrin_single_release_zone_v1 \
  --partition postproc \
  --time 00:30:00 \
  --nodes 1 \
  --ntasks 1 \
  --cpus-per-task 16 \
  --submit
```

```bash
PYENV_VERSION=system uv run python scripts/collect_balfrin_probe_metrics.py \
  --run-root /private/tmp/balfrin_tb117_probe_gate \
  --output-json /tmp/balfrin_tb117_probe_gate_metrics.json
```

### Exact failure class

- Failure class: `scheduler_submission_failed`
- Blocking message: `sbatch` is not installed or exposed on this node, so
  `submit_balfrin_probe.py --submit` returns a structured scheduler report
- Effect: the run root remains scratch-only and the metrics collector reports
  `blocked_missing_inputs` because no live outputs exist

### Execution outcome

- Readiness status: `ready_for_balfrin_target_gate`
- Submission status: `scheduler_submission_failed`
- Submission report path:
  `/private/tmp/balfrin_tb117_probe_gate/balfrin_submission_report.json`
- Metrics status: `blocked_missing_inputs`
- Run root: not measured
- Balfrin job execution: not started

### Boundary note

This blocked report does not claim operational readiness, scale-up, annual
frequency, physical probability, risk, exposure, vulnerability, or
distributed execution. It records the scheduler-access failure class only and
keeps the demo boundary non-operational.

### Next action

TB-129 should restore or expose scheduler access for the canonical Balfrin
demo submission path before dependent synthesis work resumes.

## TB-118 attempt

Status: blocked execution report, not measured Balfrin evidence.

This addendum records the live TB-118 attempt to execute the canonical
Balfrin single-release-zone demo on the Balfrin cluster. Readiness and frozen
submission-package generation succeeded, and the SLURM job started, but the job
stalled in the Rust compilation phase and was canceled before the run-root
collector could emit a complete metrics contract.

### Attempted commands

```bash
ssh balfrin 'cd /users/olifu/work/rust_rockfall && PYENV_VERSION=system uv run python scripts/check_balfrin_tschamut_readiness.py validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml --format json'
```

```bash
ssh balfrin 'cd /users/olifu/work/rust_rockfall && PYENV_VERSION=system uv run python scripts/submit_balfrin_probe.py validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml --generate-only --run-root /scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_single_release_zone_v1 --run-id tschamut_public_balfrin_single_release_zone_v1 --partition postproc --time 00:30:00 --nodes 1 --ntasks 1 --cpus-per-task 16'
```

```bash
ssh balfrin 'cd /users/olifu/work/rust_rockfall && PYENV_VERSION=system uv run python scripts/submit_balfrin_probe.py validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml --submit --run-root /scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_single_release_zone_v1 --run-id tschamut_public_balfrin_single_release_zone_v1 --partition postproc --time 00:30:00 --nodes 1 --ntasks 1 --cpus-per-task 16'
```

```bash
ssh balfrin 'squeue -j 4325958 -o "%.18i %.9T %.50R" || true'
```

```bash
ssh balfrin 'sacct -j 4325958 --format=JobID,State,Elapsed,TotalCPU,MaxRSS,ExitCode -P || true'
```

```bash
ssh balfrin 'cd /users/olifu/work/rust_rockfall && PYENV_VERSION=system uv run python scripts/collect_balfrin_probe_metrics.py --run-root /scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_single_release_zone_v1 --output-json /tmp/balfrin_tb118_collect_metrics.json'
```

```bash
ssh balfrin 'cd /users/olifu/work/rust_rockfall && PYENV_VERSION=system uv run python scripts/summarize_balfrin_post_run_interpretation_gate.py --format json'
```

### Exact failure class

- Failure class: `partial_output_incomplete`
- Blocking message: the job reached `Compiling rust_rockfall v0.6.1` on
  `nid001226`, but it did not produce the full run-root metrics contract before
  cancellation
- Effect: the collector reports `metrics_contract_status: blocked_missing_inputs`
  with missing `memory_peak_mb`, `validation_output.file_count`,
  `validation_output.bytes`, `hazard_output.file_count`, and
  `hazard_output.bytes`

### Execution outcome

- Readiness status: `ready_for_balfrin_target_gate`
- Submission status: `submitted_job_id=4325958`
- Job runtime before cancel: `00:08:09`
- Cancel status: `scancel` completed cleanly
- Run root: generated at
  `/scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_single_release_zone_v1`
- Probe package: generated
- SLURM log state: the job was canceled after the compiler phase and did not
  emit the run summary or full/hazard timing sidecars
- Metrics summary: blocked, but partial output exists

### Partial metrics evidence

The collector saw these partial evidence fields before the cancellation:

- `total_wall_seconds`: `9.295269045978785`
- `output_file_count`: `50`
- `output_bytes`: `15614702`
- `conditional_curve_row_count`: `729600`
- `trajectory_plan_id`: `validation_tschamut_public_conditional_gate_v1__trajectory_execution_plan__ec29c17a15d14be158e5b29f`
- `reducer_plan_id`: `validation_tschamut_public_conditional_gate_v1__execution_plan__45a1df662650afcf9d9f8e09`
- `trajectory_decision_counts`: `{"executed": 4}`
- `reducer_decision_counts`: `{"executed": 4}`
- `reduced_output_family_counts`: `{"deposition_points": 1, "hazard_layer": 32, "hazard_metadata": 1, "map_package_manifest": 1, "pilot_gis_package_manifest": 1, "reducer_chunk_manifest": 4, "reducer_execution_index": 1, "reducer_execution_plan": 1, "reducer_merge_state": 1, "trajectory_chunk_manifest": 4, "trajectory_execution_index": 1, "trajectory_execution_plan": 1, "trajectory_merge_state": 1}`

### Closure summary

The post-run interpretation gate remains blocked because no post-run evidence
bundle was provided. It returns `interpretation_status: blocked_missing_inputs`
and keeps the conditional-diagnostic boundary explicit.

### Boundary note

This blocked report does not claim a measured Balfrin demo run, operational
hazard readiness, annual frequency, physical probability, risk, exposure,
vulnerability, or distributed execution. It records the exact partial-output
state for the current Balfrin attempt and leaves the task open for follow-up on
the remote build stall.
