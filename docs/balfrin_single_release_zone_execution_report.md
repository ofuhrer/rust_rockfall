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

The readiness path must be taught to recognize the Balfrin contract schema, or a
contract-aware wrapper must be added, before TB-102 can produce measured
evidence.
