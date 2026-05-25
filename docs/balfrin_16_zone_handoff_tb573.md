# TB-573 Balfrin 16-Zone Diagnostic Handoff

Date: 2026-05-26

## Summary

TB-573 regenerated the 16-zone package from the clean Balfrin checkout at
`b7957e44eeed03930e9914c96d1b8ba4055eadac` under the diagnostic profile.
The package remains fail-closed, but the diagnostic output-budget profile is
accepted and the stale TB-571 manifest-size blocker is gone. The remaining
concrete blocker is the measured reducer/scenario envelope:
`requested simultaneous_release_zone_batch_size=16 exceeds measured max 8`.

No `sbatch` was attempted and no Balfrin job was submitted.

## Balfrin Package

- Package root:
  `/scratch/mch/olifu/rust_rockfall/tb573_16_zone_handoff`
- Pressure root:
  `/scratch/mch/olifu/rust_rockfall/tb573_16_zone_pressure`
- Remote checkout hygiene: `pass`
- Remote head:
  `b7957e44eeed03930e9914c96d1b8ba4055eadac`
- Access preflight status: `ready_for_read_only_collection`
- Package constraint status: `blocked`
- No-submit handoff status: `blocked`
- Authorization preflight status: `blocked_reducer_budget`
- Handoff status: `failed_closed`
- Ready for live postproc submission: `false`
- Output profile status: `ready`
- Submit contract status: `ready`
- Budget acceptance status: `accepted`
- Budget threshold profile:
  `diagnostic_16_zone_single_node_postproc_measurement`
- Budget acceptance failures: `[]`
- Handoff budget recheck status: `budget_passes_no_reduction_needed`
- Manifest pruning status: `budget_passes_no_reduction_needed`

## Preserved Hashes

- Package JSON:
  `207048a337baed4432857e342f59dfe6f5e175327cca2d2c0916ed7c3b31692f`
- Authorization record:
  `aba78a6aaed7aefd9124cde93058ae61cde764a48d81f431be4f191d8e9d8fe0`
- Command plan:
  `d62a8c028726b724a255b369ef597d0203f474b5a481fcaa9f1c13483c477524`
- SBATCH handoff script:
  `7e0cc2f8e189bdc83f1d1ff66fcb92da4f6b5f66b1a16d41fcb3e4897e07265e`
- Projection `probe_manifest_sha256`:
  `9ce28c01877b89de8b89b1753987dc655c152b690e016e3489c43773de5ec3f3`
- Projection `command_plan_sha256`:
  `719027d9fe1c8747c5a0f79cfe9d31c1f464a54a70d3f9ce4dc3ac7bc69cfcf0`
- Projection `output_manifest_sha256`:
  `2c7cacb3765572812d636dba8099b9512cc662706ceee5b6181a84e3157af679`

## Later Submit Command

This command is recorded only as the later explicit submit gate. It was not
run for TB-573.

```bash
PYENV_VERSION=system uv run python scripts/submit_balfrin_probe.py validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml --run-root /scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_multi_release_zone_v1 --run-id tschamut_public_balfrin_multi_release_zone_v1 --partition postproc --time 00:30:00 --nodes 1 --ntasks 1 --cpus-per-task 16 --authorized-submit --reviewed-handoff-package /scratch/mch/olifu/rust_rockfall/tb573_16_zone_handoff/balfrin_multi_release_zone_demo_package_v1.json --authorization-record /scratch/mch/olifu/rust_rockfall/tb573_16_zone_handoff/balfrin_multi_zone_live_authorization_record_v1.yaml
```

Submit contract run root:
`/scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_multi_release_zone_v1`

Submit contract partition: `postproc`

## Exact Blocker

Package first blocker:

```text
blocked: requested simultaneous_release_zone_batch_size=16 exceeds measured max 8; requested reducer_chunk_count=2 reaches measured max 2; requested reducer_worker_count=2 reaches measured max 2; scenario pressure blocked: first bottleneck release_zone_count
```

Authorization preflight first blocker:

```text
gate=output_budget status=blocked_reducer_budget; blocked: requested simultaneous_release_zone_batch_size=16 exceeds measured max 8; requested reducer_chunk_count=2 reaches measured max 2; requested reducer_worker_count=2 reaches measured max 2; scenario pressure blocked: first bottleneck release_zone_count; requested simultaneous_release_zone_batch_size=16 exceeds measured max 8
```

Recovery command retained in the package:

```bash
PYENV_VERSION=system uv run python scripts/generate_balfrin_multi_release_zone_demo_handoff.py --artifact-dir /scratch/mch/olifu/rust_rockfall/tb573_16_zone_handoff --requested-release-zone-batch-size 2 --requested-reducer-chunk-count 2 --requested-reducer-worker-count 2 --format json
```

## Commands Run

```bash
PYENV_VERSION=system uv run python scripts/check_balfrin_remote_access_preflight.py --format json > /tmp/tb573_balfrin_preflight_final.json
```

```bash
PYENV_VERSION=system uv run python scripts/generate_balfrin_multi_release_zone_demo_handoff.py --artifact-dir "$SCRATCH/rust_rockfall/tb573_16_zone_handoff" --candidate-output-root "$SCRATCH/rust_rockfall/tb573_16_zone_handoff/candidate_outputs" --target-area-output-root "$SCRATCH/rust_rockfall/tb573_16_zone_handoff/target_area_handoff" --pressure-probe-root "$SCRATCH/rust_rockfall/tb573_16_zone_pressure" --requested-release-zone-batch-size 16 --requested-reducer-chunk-count 2 --requested-reducer-worker-count 2 --format json --json-output "$SCRATCH/rust_rockfall/tb573_16_zone_handoff/package.json" --text-output "$SCRATCH/rust_rockfall/tb573_16_zone_handoff/package.txt"
```

```bash
PYENV_VERSION=system uv run python scripts/preflight_balfrin_smallest_multi_zone_probe_authorization.py --reviewed-handoff-package "$SCRATCH/rust_rockfall/tb573_16_zone_handoff/balfrin_multi_release_zone_demo_package_v1.json" --authorization-record "$SCRATCH/rust_rockfall/tb573_16_zone_handoff/balfrin_multi_zone_live_authorization_record_v1.yaml" --balfrin-access-preflight-json "$SCRATCH/rust_rockfall/tb573_16_zone_handoff/balfrin_preflight_final.json" --format json --json-output "$SCRATCH/rust_rockfall/tb573_16_zone_handoff/authorization_preflight_final.json" --text-output "$SCRATCH/rust_rockfall/tb573_16_zone_handoff/authorization_preflight_final.txt"
```

```bash
PYENV_VERSION=system uv run python scripts/preflight_balfrin_smallest_multi_zone_probe_authorization.py --reviewed-handoff-package "$SCRATCH/rust_rockfall/tb573_16_zone_handoff/balfrin_multi_release_zone_demo_package_v1.json" --authorization-record "$SCRATCH/rust_rockfall/tb573_16_zone_handoff/balfrin_multi_zone_live_authorization_record_v1.yaml" --validation-mode budget-thresholds --format json --json-output "$SCRATCH/rust_rockfall/tb573_16_zone_handoff/budget_threshold_validation.json"
```

## Boundary Note

This is pre-submit evidence only. It does not authorize or claim a Balfrin
measurement, scale-up, distributed execution, operational hazard assessment,
annual frequency, physical probability, risk, exposure, or vulnerability.
