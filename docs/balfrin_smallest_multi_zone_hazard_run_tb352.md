# TB-352 Smallest Multi-Zone Balfrin Hazard Run

Date: 2026-05-20

## Outcome

TB-352 failed closed before scheduler submission. No `sbatch` command was run, no
job id was allocated, and no multi-zone Balfrin hazard execution evidence was
measured.

## Gates Run

- Balfrin access preflight: `ready_for_read_only_collection`; SSH, remote clone
  hygiene, preserved run-root visibility, and scheduler query passed.
- Remote checkout: `/users/olifu/work/rust_rockfall` fast-forwarded on `main`
  from `20cc865756f1f5afb5c5e19b2a042e94553afd3a` to
  `327690d867fd475e674c76ad8f5f1e9fadc69e01` before the package was
  regenerated.
- Regenerated package root:
  `/tmp/rust_rockfall/balfrin_multi_release_zone_demo_v1`.
- Reviewed handoff package:
  `/tmp/rust_rockfall/balfrin_multi_release_zone_demo_v1/balfrin_multi_release_zone_demo_package_v1.json`.
- Authorization record:
  `/tmp/rust_rockfall/balfrin_multi_release_zone_demo_v1/balfrin_multi_zone_live_authorization_record_v1.yaml`.
- Smallest multi-zone authorization preflight:
  `blocked_reducer_budget`.

## Blocker

The Balfrin-local regenerated package did not pass the task-specific
authorization preflight:

`single-job sufficiency or reducer scaling is not yet ready for the four-zone review package`

The preflight still reported:

- authorization status: `authorized`
- reviewed package status: `reviewed`
- authorization record status: `reviewed`
- access status: `ready_for_read_only_collection`
- submit contract status: `ready`
- output-budget acceptance status: `accepted`
- reviewed package SHA-256:
  `debf49023cd9966a7838cd86612fbda05773b6384e1f669ae552475fb39411a8`
- authorization record SHA-256:
  `7e98fad7405c2e7438a061e6c5ebd6f58f8c65fab8845ebbf6cb0fb17d2fad06`

Because the reducer/output-profile gate blocked, the reviewed submit command was
not executed.

## Planned Run Shape

- Run root:
  `/scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_multi_release_zone_v1`
- Release zones: `2`
- Scenarios: `2`
- Trajectory target: `1000`
- Trajectory workers: `2`
- Reducer workers: `2`
- Reducer chunks: `2`
- Partition: `postproc`
- Time budget: `00:30:00`

## Evidence Boundary

This is a pre-submit fail-closed report only. It is not measured Balfrin
multi-zone hazard evidence, does not reduce the multi-zone execution gap, and
does not support scale-up, distributed-execution, operational, annual-frequency,
physical-probability, risk, exposure, or vulnerability claims.
