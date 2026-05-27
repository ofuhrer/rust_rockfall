# TB-618 Balfrin Four-Zone Hazard-Throughput Package

Date: 2026-05-27

TB-618 prepared the next larger bounded hazard-throughput package on Balfrin
and stopped at the no-submit boundary.

## Package

- Package root:
  `/scratch/mch/olifu/rust_rockfall/submission_packages/tb618_four_zone_hazard_throughput_package`
- Pressure probe root:
  `/scratch/mch/olifu/rust_rockfall/submission_packages/tb618_four_zone_pressure_probe`
- Reviewed handoff package:
  `/scratch/mch/olifu/rust_rockfall/submission_packages/tb618_four_zone_hazard_throughput_package/balfrin_multi_release_zone_demo_package_v1.json`
- Authorization record:
  `/scratch/mch/olifu/rust_rockfall/submission_packages/tb618_four_zone_hazard_throughput_package/balfrin_multi_zone_live_authorization_record_v1.yaml`
- Command plan:
  `/scratch/mch/olifu/rust_rockfall/submission_packages/tb618_four_zone_hazard_throughput_package/balfrin_multi_release_zone_command_plan_v1.json`
- Authorization preflight:
  `/scratch/mch/olifu/rust_rockfall/submission_packages/tb618_four_zone_hazard_throughput_package/authorization_preflight.json`

## Review Result

- Requested release-zone batch size: `4`
- Package status: `mixed_provenance`
- Package constraint status: `warning`
- Output-budget status: `accepted`
- Output-budget profile: `next_larger_four_zone_review_only_probe`
- Output file count: `23`
- Output byte count: `19,247`
- Manifest size: `18,271` bytes
- Package footprint: `199K`
- Authorization preflight: `ready_for_authorization_review`
- Ready for live `postproc` submission: `true`

The package is larger than the TB-603 two-zone hazard-throughput support point
but still single-node, bounded, and intentionally small relative to the live
scratch headroom measured by TB-617.

## Output Controls

The embedded output-profile policy classifies all command-plan profiles as
`scalable_default`:

- conditional-curve export: `summary-only`;
- grid CSV export: `none`;
- plots: disabled;
- compact/rebuildable handoff artifacts retained.

The standalone `check_hazard_output_profile.py --command-plan` helper is not
the right checker for this package-level command plan because the handoff plan
contains package orchestration commands rather than a direct `build_hazard_layers`
command. The package's embedded output-profile policy and output-budget
projection are the authoritative checks for this no-submit package.

## Recommended TB-619 Submission

The generated authorization record preserves historical default submit command
text. That historical root already exists on Balfrin:

`/scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_four_zone_hazard_v1`

Use a fresh run root for TB-619 to avoid contaminating old evidence:

```bash
PYENV_VERSION=system uv run python scripts/submit_balfrin_probe.py \
  validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml \
  --run-root /scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_four_zone_hazard_tb619_20260527 \
  --run-id tschamut_public_balfrin_four_zone_hazard_tb619_20260527 \
  --partition postproc \
  --time 00:30:00 \
  --nodes 1 \
  --ntasks 1 \
  --cpus-per-task 16 \
  --authorized-submit \
  --reviewed-handoff-package /scratch/mch/olifu/rust_rockfall/submission_packages/tb618_four_zone_hazard_throughput_package/balfrin_multi_release_zone_demo_package_v1.json \
  --authorization-record /scratch/mch/olifu/rust_rockfall/submission_packages/tb618_four_zone_hazard_throughput_package/balfrin_multi_zone_live_authorization_record_v1.yaml
```

This remains a bounded `postproc` hazard-throughput package. It does not add
Swiss-wide, distributed, non-`postproc`, operational, physical-probability,
risk, exposure, or vulnerability evidence until a later task submits and
collects the run.
