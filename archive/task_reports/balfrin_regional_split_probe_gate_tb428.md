# TB-428 Regional Split Balfrin Probe Gate

Date: 2026-05-21

## Summary

TB-428 did not submit a Balfrin job. The regional split/merge contract is
ready, but the reviewed submission package failed closed at the output-budget
gate before `sbatch`.

This is the correct outcome for the current package: the next live regional
split probe must not be submitted until the package fits the reviewed budget or
the budget is explicitly revised by a later task.

## Gate Result

- Package schema: `balfrin_regional_split_submission_package_v1`
- Submission package status: `failed_closed_output_budget`
- Ready for bounded `postproc` submission: `false`
- Authorization preflight status: `blocked_reducer_budget`
- Regional split/merge contract status: `ready`
- Regional split count: `12`
- `sbatch` attempted: `false`
- Balfrin job submitted: `false`

First blocker:

```text
output budget blocked: manifest_size_bytes=14550 exceeds next_larger_four_zone_review_only_probe.max_manifest_size_bytes=14000
```

## Non-Executed Command

The package records this as the later bounded command, but TB-428 did not run
it because the package was not ready:

```bash
PYENV_VERSION=system uv run python scripts/submit_balfrin_probe.py validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml --run-root /scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_multi_release_zone_v1 --run-id tschamut_public_balfrin_multi_release_zone_v1 --partition postproc --time 00:30:00 --nodes 1 --ntasks 1 --cpus-per-task 16 --authorized-submit --reviewed-handoff-package /private/tmp/rust_rockfall/tb428_gate_package/handoff/balfrin_multi_release_zone_demo_package_v1.json --authorization-record /private/tmp/rust_rockfall/tb428_gate_package/handoff/balfrin_multi_zone_live_authorization_record_v1.yaml
```

## Next Unblock Action

The immediate unblock action is to reduce or compact the regional split
manifest/package by at least 550 bytes, or to revise the reviewed budget with a
measured justification in a separate task. Until then, the regional split
Balfrin probe remains a no-submit branch.

## Later Integration Status

TB-431 later compacted the reviewed package enough for the package gate to pass
in fixture-backed preflight. TB-432 then reran the live gate and still failed
closed before `sbatch`, this time because the Balfrin remote checkout hygiene
gate found three stale generated `command_plan.json` files. That TB-432 result
remains failed-closed/no-submit evidence, not measured regional capability.

After TB-432, the transient remote hygiene blocker was cleared outside the
failed-closed run: the ignored generated files were preserved/removed from the
remote checkout, and a fresh access preflight reported
`ready_for_read_only_collection`, `ready_for_pre_submit=true`, remote hygiene
`pass`, and `dirty_path_count=0`. The current next action is therefore evidence
collection: regenerate the ready package with a fresh passing access preflight
and retry one bounded regional split `postproc` probe.

## Boundaries

- No Balfrin job was submitted.
- No non-`postproc` partition was used.
- No distributed execution or scale-up claim is made.
- No operational hazard assessment is made.
- No annual-frequency, physical-probability, risk, exposure, or vulnerability
  claim is made.
