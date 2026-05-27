# TB-362 Two-Zone Balfrin Hazard Run

Date: 2026-05-20

## Outcome

TB-362 failed closed before `sbatch`. No live two-zone Balfrin hazard job was
submitted, and no measured two-zone hazard run root was created.

The immediate blocker came from the remote Balfrin pre-submit gate after
regenerating the explicit two-zone package on the Balfrin checkout:

- `preflight_status`: `blocked_reducer_budget`
- `ready_for_authorized_submission`: `false`
- `authorization_status`: `authorized`
- `reducer_budget_status`: `ready`
- `output_profile_status`: `blocked_output_profile`
- `submit_contract_status`: `ready`
- `output_budget_acceptance_status`: `accepted`
- `blocked_reason`: `single-job sufficiency or reducer scaling is not yet ready for the four-zone review package`

Because one required gate blocked, the submit command was not executed.

## Gate Evidence

The Balfrin checkout was fast-forward clean at
`8b94c12d6d1fa89a4928e15b243805b19600d31b`. The access preflight reported
`ready_for_read_only_collection`, `ready_for_pre_submit=true`, and checkout
hygiene `pass` with `0` dirty paths.

Remote artifacts preserved under `/tmp` on Balfrin:

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| `/tmp/tb362_two_zone_access_preflight.json` | 6475 | `3423898bdea9fb035ada2604e7a1e9724add671b441d338c68f217db7927c0a7` |
| `/tmp/tb362_two_zone_handoff/balfrin_multi_release_zone_demo_package_v1.json` | 516315 | `455c22b155f2acf84f9d12f57dcea1ce43dfa24b85b7d1372c646c1cb9e46962` |
| `/tmp/tb362_two_zone_handoff/balfrin_multi_zone_live_authorization_record_v1.yaml` | 1425 | `985471d40e3d95504f51f21a0b01f15fc6cb3794d676454e3f0422d713403365` |
| `/tmp/tb362_two_zone_handoff/preflight.json` | 300324 | `af3a22716fadd5294bd5fcefb80a99905fbfd96541fa1adca3d11ce62ee70078` |
| `/tmp/tb362_two_zone_handoff/generate_stdout.json` | 516315 | `455c22b155f2acf84f9d12f57dcea1ce43dfa24b85b7d1372c646c1cb9e46962` |
| `/tmp/tb362_two_zone_handoff/balfrin_multi_release_zone_command_plan_v1.json` | 19656 | `c05e97ed88461b2d0b457d7e780f1bee0da46bd1bc3336030b4f996f7784c544` |
| `/tmp/tb362_two_zone_handoff/balfrin_multi_release_zone_handoff.sbatch` | 2349 | `f2bb824c7b3ad8b54591274b9899bf237d6da490955876e57f3a798a7877e86c` |

The blocked submit contract, not executed, was:

```bash
PYENV_VERSION=system uv run python scripts/submit_balfrin_probe.py validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml --run-root /scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_multi_release_zone_v1 --run-id tschamut_public_balfrin_multi_release_zone_v1 --partition postproc --time 00:30:00 --nodes 1 --ntasks 1 --cpus-per-task 16 --authorized-submit --reviewed-handoff-package /tmp/tb362_two_zone_handoff/balfrin_multi_release_zone_demo_package_v1.json --authorization-record /tmp/tb362_two_zone_handoff/balfrin_multi_zone_live_authorization_record_v1.yaml
```

## Scheduler Guard

The `postproc` queue was queried before the blocked decision. The candidate
job would have requested only `postproc`, `1` node, `1` task,
`16` CPUs per task, and a `00:30:00` wall time. The pre-submit gate blocked
before scheduler submission, so the 6-hour full-partition rediscussion rule was
not reached by this task.

## Boundary

This is a pre-submit fail-closed report only. It is not measured Balfrin
two-zone hazard evidence, not a scale-up authorization, not distributed
execution, not a non-`postproc` run, and not an operational, annual-frequency,
physical-probability, risk, exposure, or vulnerability claim.
