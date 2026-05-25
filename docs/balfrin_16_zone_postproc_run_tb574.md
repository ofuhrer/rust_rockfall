# TB-574 Balfrin 16-Zone Diagnostic Postproc Submission Decision

Date: 2026-05-26

## Summary

TB-574 did not submit a Balfrin `postproc` job because the reviewed TB-573
16-zone package did not pass the no-submit preflight. This is the expected
outcome for "submit if checks pass": checks did not pass, so no `sbatch` was
attempted.

The useful result is a precise run-root and package reason for not completing:
the diagnostic budget profile is accepted, the output profile and submit
contract are ready, Balfrin access is ready, but the 16-zone batch exceeds the
measured reducer/scenario envelope.

## Package Used

- Reviewed package:
  `/scratch/mch/olifu/rust_rockfall/tb573_16_zone_handoff/balfrin_multi_release_zone_demo_package_v1.json`
- Authorization record:
  `/scratch/mch/olifu/rust_rockfall/tb573_16_zone_handoff/balfrin_multi_zone_live_authorization_record_v1.yaml`
- Intended run root:
  `/scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_multi_release_zone_v1`
- Remote checkout head:
  `b7957e44eeed03930e9914c96d1b8ba4055eadac`
- Package JSON SHA-256:
  `207048a337baed4432857e342f59dfe6f5e175327cca2d2c0916ed7c3b31692f`
- Authorization record SHA-256:
  `aba78a6aaed7aefd9124cde93058ae61cde764a48d81f431be4f191d8e9d8fe0`
- Final access preflight SHA-256:
  `894f7e72b8637413969edf06c8f47a7025437185cd21bfcec272211bab8aa83d`
- Authorization preflight JSON SHA-256:
  `a073f6fc377e11805151fee4130701ef07329bb68d6957d70ea4ba91b7ef831c`

## Decision

- Scheduler submission: not attempted.
- Job id: none.
- Exit code: not applicable.
- Elapsed time: not applicable.
- MaxRSS: not applicable.
- Queue state: not queried for submission because the package preflight failed
  before scheduler interaction.
- Access status: `ready_for_read_only_collection`.
- Output profile status: `ready`.
- Submit contract status: `ready`.
- Budget acceptance status: `accepted`.
- Budget profile:
  `diagnostic_16_zone_single_node_postproc_measurement`.
- Authorization preflight status: `blocked_reducer_budget`.

Exact remaining blocker:

```text
blocked: requested simultaneous_release_zone_batch_size=16 exceeds measured max 8; requested reducer_chunk_count=2 reaches measured max 2; requested reducer_worker_count=2 reaches measured max 2; scenario pressure blocked: first bottleneck release_zone_count
```

## Boundary Note

This is a no-submit decision record, not a measured Balfrin run. It makes clear
why TB-574 did not produce runtime, memory, or scheduler metrics and why TB-575
has no 16-zone run root to collect from.
