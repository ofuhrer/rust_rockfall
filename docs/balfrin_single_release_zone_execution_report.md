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
