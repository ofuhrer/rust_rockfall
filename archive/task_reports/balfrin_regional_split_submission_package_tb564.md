# Balfrin Regional Split Submission Package TB-564

Date: 2026-05-25

This note records the no-submit regional split package regenerated for TB-564.
It is a package-readiness record only; it does not report a new Balfrin run or
upgrade any scientific or operational claim.

## Package

- Artifact root: `/tmp/rust_rockfall/tb564_regional_split_package`
- Package JSON: `/tmp/rust_rockfall/tb564_regional_split_package/balfrin_regional_split_submission_package_v1.json`
- Package text: `/tmp/rust_rockfall/tb564_regional_split_package/balfrin_regional_split_submission_package_v1.txt`
- Access preflight JSON: `/tmp/tb564_balfrin_preflight.json`
- Package JSON SHA-256: `1326e3d8ef7bfeb16bac5c36b7b9a2db8c64a60a08a8c310e9db421ee8c6716a`
- Package text SHA-256: `7a71bbc22e22c3920e448f4be4e23a50c1cc02f74c79abf36cfcf121fa0d406e`
- Access preflight SHA-256: `e309c3f61fabb2369ee240a65d8f5e099e3fe0dd92d19b766b1d305ff2e5e329`

## Gate Results

- `submission_package_status`: `ready_for_bounded_postproc_submission`
- `ready_for_bounded_postproc_submission`: `true`
- `first_blocker`: `None`
- `authorization_preflight_status`: `ready_for_authorization_review`
- `remote_head_alignment.status`: `ready_remote_head_aligned`
- Local package source HEAD: `90312dfeb9fc007726eec8ed22e10e8b38f9d752`
- Balfrin remote HEAD: `90312dfeb9fc007726eec8ed22e10e8b38f9d752`
- `compact_manifest_freshness.status`: `ready_compact_manifest_current`
- Compact manifest mode: `compact`
- Compact manifest size: `8657` bytes
- Output budget status: `ready`
- Output budget acceptance: `accepted`
- Threshold profile: `smallest_live_two_zone_probe`
- Writable remote root status: `ready`
- Writable run root: `/scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_multi_release_zone_v1`
- No-submit status: `not_submitted`
- `sbatch_attempted`: `false`
- `submit_command_executed`: `false`
- `balfrin_job_submitted`: `false`

## Preserved Submit Command

```bash
PYENV_VERSION=system uv run python scripts/submit_balfrin_probe.py validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml --run-root /scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_multi_release_zone_v1 --run-id tschamut_public_balfrin_multi_release_zone_v1 --partition postproc --time 00:30:00 --nodes 1 --ntasks 1 --cpus-per-task 16 --authorized-submit --reviewed-handoff-package /private/tmp/rust_rockfall/tb564_regional_split_package/handoff/balfrin_multi_release_zone_demo_package_v1.json --authorization-record /private/tmp/rust_rockfall/tb564_regional_split_package/handoff/balfrin_multi_zone_live_authorization_record_v1.yaml
```

This command was preserved by the package generator and was not executed during
TB-564.
