# TB-432 Regional Split Balfrin Probe Gate

Date: 2026-05-21

## Summary

TB-432 did not submit a Balfrin job. After the TB-431 package compaction, the
regional split package passed the package-contract, output-budget, writable
remote-root, and preservation-plan gates, but failed closed at the Balfrin
authorization/access preflight before `sbatch`.

This is the correct outcome for the current remote state: the next live
regional split probe must not be submitted until the Balfrin checkout hygiene
gate is clean and the package is regenerated from a passing access preflight.

## Gate Result

- Package schema: `balfrin_regional_split_submission_package_v1`
- Submission package status: `failed_closed_preflight`
- Ready for bounded `postproc` submission: `false`
- Authorization preflight status: `blocked_access`
- First blocker gate: `authorization_preflight`
- First blocker reason: `Balfrin access preflight status is blocked_dirty_remote_checkout`
- Package contract status: `ready`
- Output-budget status: `ready`
- Writable remote-root status: `ready`
- Preservation-plan status: `ready`
- Regional split/merge contract status: `ready`
- Regional split count: `12`
- Regional execution key count: `12`
- Merge order: `sorted_chunk_id_then_output_family_then_path`
- Merge order independent: `true`
- Merge order deterministic: `true`
- `sbatch` attempted: `false`
- Balfrin job submitted: `false`

Remote checkout hygiene found three stale generated package files:

```text
validation/private/tb407_repaired_handoff_remote/multi_zone_pressure/four_zone_review_only/handoff_output_budget_projection_compact_root/command_plan.json
validation/private/tb407_repaired_handoff_remote/multi_zone_pressure/four_zone_review_only/handoff_output_budget_projection_full_root/command_plan.json
validation/private/tb407_repaired_handoff_remote/multi_zone_pressure/handoff_output_budget_projection_full_root/command_plan.json
```

## Non-Executed Command

The package records this as the later bounded command, but TB-432 did not run
it because the authorization/access preflight was not ready:

```bash
PYENV_VERSION=system uv run python scripts/submit_balfrin_probe.py validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml --run-root /scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_multi_release_zone_v1 --run-id tschamut_public_balfrin_multi_release_zone_v1 --partition postproc --time 00:30:00 --nodes 1 --ntasks 1 --cpus-per-task 16 --authorized-submit --reviewed-handoff-package /private/tmp/rust_rockfall/tb432_regional_split_failed_closed_package/handoff/balfrin_multi_release_zone_demo_package_v1.json --authorization-record /private/tmp/rust_rockfall/tb432_regional_split_failed_closed_package/handoff/balfrin_multi_zone_live_authorization_record_v1.yaml
```

## Metrics Status

- Runtime: not measured because no scheduler submission occurred.
- Peak memory: not measured because no scheduler submission occurred.
- Validation output file count and bytes: not measured for TB-432 because no
  run root was produced.
- Hazard output file count and bytes: not measured for TB-432 because no run
  root was produced.
- Reducer metrics: package gate remained ready from the fixture-backed
  projection, but no live regional split reducer metrics were measured.
- Preservation gate: package preservation plan ready; post-run preservation
  evidence not applicable because no job was submitted.
- Run-root pointer: planned reviewed scratch root
  `/scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_multi_release_zone_v1`.
- Local failed-closed package record:
  `/tmp/rust_rockfall/tb432_regional_split_failed_closed_package/balfrin_regional_split_submission_package_v1.json`.
- Local access preflight record: `/tmp/tb432_balfrin_access_preflight.json`.

## Next Unblock Action

Preserve or remove the three stale generated `command_plan.json` files in the
Balfrin checkout, rerun:

```bash
PYENV_VERSION=system uv run python scripts/check_balfrin_remote_access_preflight.py --format json
PYENV_VERSION=system uv run python scripts/generate_balfrin_regional_split_submission_package.py --balfrin-access-preflight-json <passing-preflight.json> --format json
```

Only submit the recorded bounded `postproc` command after the regenerated
package reports `ready_for_bounded_postproc_submission=true`.

## Boundaries

- No Balfrin job was submitted.
- No non-`postproc` partition was used.
- No distributed execution or scale-up claim is made.
- No operational hazard assessment is made.
- No annual-frequency, physical-probability, risk, exposure, or vulnerability
  claim is made.
