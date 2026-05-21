# Multi-Zone Reducer Pressure Probe

Status: scratch-root probe, not a live Balfrin run.

This probe materializes a deterministic multi-zone scratch root and summarizes
the reducer/merge pressure, reducer-manifest bytes, bounded debug fanout, and
output-family bytes without relying on ignored live artifacts.

Reproduce with:

```bash
PYENV_VERSION=system uv run python scripts/summarize_multi_zone_reducer_pressure.py \
  --materialize-root /tmp/rust_rockfall/tb187_multi_zone_probe \
  --format json
```

## Regional Split Execution Contract

The materialized probe now writes
`input/regional_split_execution_plan.json` with schema
`regional_split_execution_plan_v1`. This is a local scratch-plan contract for
partitioning a multi-zone AOI into deterministic execution chunks and reducer
merge keys; it is not a distributed execution launcher.

Each split entry carries the required replay fields:

- `group`: the source group used for reducer assignment.
- `zone_id`: the stable source-zone id.
- `scenario_id`: the scenario-table row id assigned to the zone.
- `sampling_weight`: the conditional sampling weight when present.
- `chunk_id`: the reducer execution chunk.
- `expected_output_root`: the expected chunk output root.
- `merge_key`: the explicit reducer merge key, using
  `chunk_id/zone_id/scenario_id`.

The same manifest is referenced from `command_plan.json`, the probe manifest,
and the JSON summary. Fixture tests enforce stable ordering and reject duplicate
execution keys so later split/merge work does not rely on implicit file naming.

## Measured Summary

- Probe root: `/tmp/rust_rockfall/multi_zone_reducer_pressure_tb336_probe`
- Release zones: `12`
- Scenarios: `12`
- Trajectory chunks: `12`
- Reducer workers: `2`
- Reducer chunks: `2`
- Merge order: `sorted_chunk_id`
- Merge-order independent: `true`
- Merge-order deterministic: `true`
- Reducer wall time: `2.59` s
- Manifest size: `18274` bytes
- Root file count: `52`
- Output file count: `48`
- Output bytes: `26105`
- Reducer manifest bytes: `614`
- Reducer manifest files: `2`
- Sidecar files: `9`
- Sidecar bytes: `1702`
- Primary output files: `36`
- Primary output bytes: `7586`
- Output family mix: `trajectory_csv, deposition_csv, impact_events_csv, reducer_chunk_manifest, trajectory_execution_plan, trajectory_execution_index, trajectory_merge_state, reducer_execution_plan, reducer_execution_index, reducer_merge_state, diagnostics_json, map_package_manifest, pilot_gis_package_manifest`

## Output Families

- `trajectory_csv`: `12` files / `4678` bytes
- `impact_events_csv`: `12` files / `1660` bytes
- `deposition_csv`: `12` files / `1248` bytes
- `reducer_chunk_manifest`: `2` files / `614` bytes
- `trajectory_execution_index`: `1` file / `422` bytes
- `reducer_execution_index`: `1` file / `226` bytes
- `reducer_merge_state`: `1` file / `105` bytes
- `pilot_gis_package_manifest`: `1` file / `105` bytes
- `map_package_manifest`: `1` file / `93` bytes
- `trajectory_merge_state`: `1` file / `109` bytes
- `trajectory_execution_plan`: `1` file / `76` bytes
- `reducer_execution_plan`: `1` file / `72` bytes
- `diagnostics_json`: `1` file / `143` bytes

## Bottleneck Labels

- `merge_order`: `sorted_chunk_id_deterministic`
- `manifest_size`: `manifest_pressure`
- `output_pressure`: `output_pressure_bounded`
- `reducer_runtime`: `reducer_runtime_pressure`
- `probe_blocker`: `multi_zone_dry_run_blocked`

## Recommended Reducer Constraints For TB-183

- Keep `merge_order` at `sorted_chunk_id`.
- Keep `merge_order_independent` set to `true`.
- Hold `reducer_worker_count` at `2` until a larger scratch probe says otherwise.
- Cap `reducer_chunk_count` at `2` for the next probe.
- Stage simultaneous release zones in batches of at most `8`.

## Conclusion

Reducer pressure is still a blocker for a multi-zone Balfrin dry run at this
probe shape. The dominant signals are manifest pressure and reducer-runtime
pressure, while output-family pressure is now explicitly bounded by the reduced
debug fanout, so TB-183 should keep the reducer constraints above in place
before attempting a larger dry run.

## Regression Gate

The fixture-backed regression gate that enforces these budgets is:

```bash
PYENV_VERSION=system uv run python scripts/validate_multi_zone_reducer_pressure_gate.py \
  --materialize-root /tmp/rust_rockfall/tb218_multi_zone_gate_probe \
  --format json
```

Its warning and blocked thresholds are themselves fixture-backed and are
derived from deterministic 9-zone and 11-zone scratch profiles until real
Balfrin roots are measured.

## Handoff-Derived Projection

The scratch probe remains the reducer-pressure measurement source, but the
Balfrin multi-release-zone handoff now also projects the output budget from
the concrete `multi_zone_reducer_pressure_summary` command in its command
plan. That projection runs the fixture-backed gate against the command-plan
shape and records primary outputs, reducer manifests, sidecars, manifest
bytes, per-family budget checks, and first bottleneck labels in the handoff
package. If the projected command-plan shape exceeds the current gate, the
handoff package remains fail-closed even when the smaller requested submit
shape is otherwise within measured reducer maxima.

## TB-245 Current Handoff Projection

The current TB-245 recheck still stays `blocked_budget_reduction_needed`
rather than `budget_passes_no_reduction_needed`. The bounded baseline
projection now records `12` release zones, `48` output files, `26105` output
bytes, `18274` manifest bytes, `9` sidecar files, and `614` reducer-manifest
bytes.

TB-246 adds a compact manifest-pruning path that keeps the replay-safe
primary outputs plus the merge-state files and projection hashes while
pruning the chunk-manifest, execution-plan, execution-index, diagnostics, and
GIS sidecars. That compact projection now records `39` output files,
`23772` output bytes, `17788` manifest bytes, `2` sidecar files, and `0`
reducer-manifest bytes, but it still remains `blocked_budget_reduction_needed`
because the first blocked label is still `manifest_size_bytes`.

The compact projection now makes the replay-critical boundary explicit:
`trajectory_csv`, `deposition_csv`, `impact_events_csv`,
`trajectory_merge_state`, and `reducer_merge_state` remain, along with the
`probe_manifest`, `command_plan`, and `output_manifest` SHA-256 hashes that the
handoff report records for provenance. The budget can therefore be rechecked
without mutating the live handoff semantics, while still reporting the exact
remaining fields that prevent a smaller manifest.

## TB-266 Smallest Multi-Zone Handoff Budget Repair

The reviewed two-release-zone probe shape is still fail-closed, but the repair
path now reports a compact before/after budget envelope instead of only a
generic manifest-pressure label:

- Before: `48` output files, `9` sidecar files, `614` reducer-manifest bytes,
  `18274` manifest bytes.
- After compact pruning: `39` output files, `2` sidecar files, `0`
  reducer-manifest bytes, `17788` manifest bytes.

The retained replay-critical families are
`trajectory_csv`, `deposition_csv`, `impact_events_csv`,
`trajectory_merge_state`, and `reducer_merge_state`. The blocker is still
`manifest_size_bytes`, but the follow-on report now keeps the replay-critical
field inventory and the compact retained families explicit so the next review
can see exactly what cannot be removed to pass the budget.

## Smallest Authorization Preflight Shape

The smallest bounded multi-zone authorization preflight consumes the reviewed
handoff package, a live-run authorization record, and the Balfrin read-only
access report before the submit path can reach `sbatch`:

```bash
PYENV_VERSION=system uv run python scripts/preflight_balfrin_smallest_multi_zone_probe_authorization.py \
  --reviewed-handoff-package /tmp/rust_rockfall/balfrin_multi_release_zone_demo_v1/balfrin_multi_release_zone_demo_package_v1.json \
  --authorization-record /tmp/rust_rockfall/balfrin_multi_release_zone_demo_v1/balfrin_multi_zone_live_authorization_record_v1.yaml \
  --balfrin-access-preflight-json /tmp/balfrin_remote_access_preflight_tb226.json \
  --format json
```

For the reviewed smallest handoff, the reported run shape is `2` release
zones, `2` scenarios, `2` trajectory workers, `2` reducer workers, `2` reducer
chunks, summary-only conditional curves, no grid CSV export, GeoTIFF export,
and pilot GIS packaging. This stays within the measured reducer constraints
above while retaining the non-operational, no-scale-up, and no-distributed-run
boundaries.

TB-247 refreshes the preflight decision branch so the machine-readable answer is
one of `ready_for_authorization_review`, `blocked_missing_authorization`,
`blocked_reducer_budget`, or `blocked_access`. The current compact handoff
budget is still consumed before the authorization-record branch, so the
remaining `blocked_budget_reduction_needed` manifest-size blocker keeps the
smallest package at `blocked_reducer_budget` rather than making it reviewable.
The Balfrin access report status is still recorded separately, and the preflight
continues to state that it does not grant authorization or permit live
submission.

## TB-268 Evidence Integration Status

TB-267 did not produce measured multi-zone Balfrin evidence. The Balfrin access
preflight passed read-only, but the smallest two-release-zone authorization
preflight failed closed before submission with `blocked_reducer_budget`; the
first reducer/output bottleneck was `manifest_size_bytes`, and the required
authorization record was missing. No SLURM job id, metrics JSON, preservation
gate, or post-run collector output was promoted.

The current reducer-pressure, evidence-bundle, closure, next-action, and
Swiss-wide envelope helpers therefore classify the multi-zone state as
`blocked_incomplete`, not measured. The scaling frontier is a no-go until the
manifest-size reducer-budget blocker and the missing authorization record are
resolved. If a future preservation-checked two-zone Balfrin root is supplied,
the helpers can move the frontier to a reviewed next-larger package, but they
still keep `scale_up_authorized=false` and do not authorize a larger run.

## TB-287 Smallest Two-Zone Probe Gate

TB-287 did not submit a live Balfrin job. No separate exact user authorization
for the bounded two-zone submit was present at execution time, so no
`--authorized-submit` command or `sbatch` call was run.

After TB-303, the user granted standing clearance for GPT-5.5 workers to submit
and actively monitor Balfrin `postproc` jobs. That removes the earlier
authorization blocker for the smallest two-zone postproc probe, but it does not
remove technical pre-submit gates. The authorization record remains a
reproducibility/audit artifact for the helper chain, and the access, remote
checkout hygiene, output-budget, reduced-output, preservation, and post-run
evidence gates still determine whether a job may actually be submitted.
Multiple concurrent `postproc` jobs are allowed under this clearance, but
keeping the partition fully busy for more than 6 hours requires rediscussion.

The current read-only preflight also fails before submission with the exact
helper blocker `blocked_dirty_remote_checkout`: the Balfrin checkout reports no
tracked modifications, but it still contains untracked generated run files,
SLURM logs, and scratch helper scripts. The refreshed smallest authorization
preflight over `/tmp/tb287_balfrin_access_preflight.json` reports
`preflight_status=blocked_access`,
`balfrin_access_status=blocked_dirty_remote_checkout`,
`reducer_budget_status=ready`, `output_profile_status=ready`, and the
authorization record was previously `missing`. A later GPT-5.5 worker attempt
created a reviewed/authorized audit record with package SHA-256
`8e0a01fd787f941775c51ef7ade12cf18ab370796f6b518be0fd1dd9b5d6e808` and
authorization-record SHA-256
`a92371d0117f39ba5657480090d8173a9cc50808174afa38101c1c80e4291fe4`, but the
access preflight still returned `blocked_dirty_remote_checkout`. The
authorization-gated path report keeps `submit_command_executed=false` and
promotes no measured result.

## TB-293 Output-Budget Acceptance Thresholds

The multi-zone handoff now carries objective budget thresholds in
`output_budget_acceptance_thresholds` and validates each projection into
`output_budget_acceptance_validation`. The smallest live-review profile is
`smallest_live_two_zone_probe` with maxima of `11000` manifest bytes, `20`
output files, `11` sidecar files, `2` reducer manifest files, `400`
reducer-manifest bytes, and `2` reducer chunks. The next larger review-only
profile is `next_larger_four_zone_review_only_probe` with maxima of `14000`
manifest bytes, `28` output files, `13` sidecar files, `2` reducer manifest
files, `450` reducer-manifest bytes, and `2` reducer chunks.

Both profiles retain per-family file-count thresholds, the replay-critical
families `trajectory_csv`, `deposition_csv`, `impact_events_csv`,
`trajectory_merge_state`, and `reducer_merge_state`, and the replay-critical
package hashes `probe_manifest_sha256`, `command_plan_sha256`, and
`output_manifest_sha256`. The validator reports each exceeded metric with its
measured value, threshold, excess, and whether the excess is `compressible` or
`replay_critical`. The smallest authorization preflight consumes this report and
also provides `--validation-mode budget-thresholds` for budget-only review; that
mode does not convert missing authorization or dirty Balfrin access state into a
budget failure.

## TB-348 Scenario Pressure Gate

TB-348 adds a scenario-pressure planning surface to the handoff so the current
pre-submit path can distinguish the 10-zone, 50-zone, and 100-zone planning
cases before live submission. The gate now fails closed on the first scenario
or manifest overage using the measured reducer envelope, with explicit
threshold profiles for release-zone batch size, manifest pressure, output file
count, and root file count.

## TB-301 Local Scaling Ladder

TB-314 refreshed the local ladder after TB-312 measured four-zone Balfrin
postproc evidence and TB-313 rejected the accumulator micro-optimization. The
helper still stays local and fixture-backed; it records scratch-only
pressure/throughput evidence and does not promote the Balfrin postproc result
into a local hazard-accumulation claim.

Measured rung summary:

| Zones | Status | Manifest bytes | Reducer manifest bytes | Sidecars | Output files | First bottleneck | Accumulation s | Raster write s | Reducer merge s | Total wall s |
| --- | --- | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: |
| 1 | `probe_ready` | `5888` | `197` | `3` | `8` | `raster_write_seconds` | `0.010291` | `0.020531` | `0.000000` | `0.129674` |
| 2 | `probe_ready` | `6292` | `394` | `4` | `13` | `accumulation_seconds` | `0.090298` | `0.022384` | `0.006235` | `0.218312` |
| 4 | `probe_ready` | `6948` | `438` | `6` | `21` | `accumulation_seconds` | `0.090089` | `0.021907` | `0.006222` | `0.211048` |
| 8 | `multi_zone_dry_run_blocked` | `8260` | `526` | `10` | `37` | `accumulation_seconds` | `0.088567` | `0.023540` | `0.006084` | `0.223721` |
| 12 | `multi_zone_dry_run_blocked` | `9586` | `614` | `14` | `53` | `accumulation_seconds` | `0.104789` | `0.022471` | `0.007194` | `0.230328` |

The status change is stable across the refresh: `1`, `2`, and `4` zones remain
`probe_ready`, while `8` and `12` zones remain `multi_zone_dry_run_blocked`.
The first blocked rung is still `8` zones, and the first bottleneck label stays
`accumulation_seconds` for every rung beyond the single-zone raster-write case.
That keeps the current local scaling frontier clear without turning the TB-312
Balfrin postproc measurement into a local hazard-accumulation claim.

## TB-309 Smallest Two-Zone Probe Result

TB-309 did not produce measured two-zone Balfrin evidence. The live access and
remote-hygiene gate passed after fast-forwarding the Balfrin checkout to
`34ead5c8e39842e66c1051a7e474180296a1bbd6`, and the smallest authorization
preflight reported `ready_for_authorization_review` with reducer budget
`ready`, output profile `ready`, and output-budget acceptance `accepted`.

The attempt failed closed before `sbatch`: the reviewed submit command supplies
`validation/pilot_runs/tschamut_public_balfrin_target_area_demo_v1.yaml` to
`scripts/submit_balfrin_probe.py`, but that helper currently requires a
`public_real_site_conditional_pilot_run_v1` probe manifest. No job id, run root,
metrics JSON, preservation gate, or measured result was produced. The next safe
action is submit-contract repair or package regeneration, not a live scale step.
See `docs/balfrin_two_zone_probe_tb309.md` for the checksums and exact error
block.

## TB-320 Submit-Contract Repair

TB-320 repairs the package generator so the reviewed two-zone command uses the
executable pilot-run manifest:

```bash
PYENV_VERSION=system uv run python scripts/submit_balfrin_probe.py validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml --run-root /scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_multi_release_zone_v1 --run-id tschamut_public_balfrin_multi_release_zone_v1 --partition postproc --time 00:30:00 --nodes 1 --ntasks 1 --cpus-per-task 16 --authorized-submit --reviewed-handoff-package /tmp/rust_rockfall/balfrin_multi_release_zone_demo_v1/balfrin_multi_release_zone_demo_package_v1.json --authorization-record /tmp/rust_rockfall/balfrin_multi_release_zone_demo_v1/balfrin_multi_zone_live_authorization_record_v1.yaml
```

The pre-submit authorization helper now validates that submit command's probe
manifest contract before access or scheduler submission can pass. The remaining
live-run gates are access/checkout hygiene, reviewed package and authorization
record agreement, output-budget readiness, preservation/output-budget evidence
capture, and the actual `postproc` `sbatch` execution. This is still only
two-zone contract readiness, not measured multi-zone Balfrin evidence.

## TB-322 Two-Zone Shape And Scratch-Root Repair

TB-322 repairs the package default so the top-level live handoff validates the
`smallest_live_two_zone_probe` profile with `release_zone_count=2`, while the
four-zone package remains explicitly review-only under
`review_only_four_zone_package`. The generated review and later-submit commands
now target the Balfrin account scratch root:

```bash
PYENV_VERSION=system uv run python scripts/submit_balfrin_probe.py validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml --run-root /scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_multi_release_zone_v1 --run-id tschamut_public_balfrin_multi_release_zone_v1 --partition postproc --time 00:30:00 --nodes 1 --ntasks 1 --cpus-per-task 16 --generate-only
```

Remote generate-only proof from `/users/olifu/work/rust_rockfall` wrote
`command_plan.json` and `probe.sbatch` under
`/scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tb322_generate_only_20260520T000000Z`
without calling `sbatch`. This is pre-submit readiness only, not measured
multi-zone Balfrin hazard evidence.

## TB-333 Four-Zone Hazard Outcome Integration

TB-333 keeps the four-zone postproc evidence and the four-zone hazard branch
separate. TB-312 remains the measured Balfrin `postproc` record, while TB-332
failed closed before `sbatch` because the authorization checksum no longer
matched the reviewed handoff package. That means the four-zone hazard branch
still has accepted output pressure but no measured hazard execution, so it
does not support an eight-zone probe or a hazard-builder optimization claim.

The updated decision surface therefore defers larger hazard work until a
measured hazard branch exists. The local scratch ladder still first blocks at
8 zones on `accumulation_seconds`, but that local breakpoint is separate from
the blocked Balfrin hazard branch and should not be read as live hazard
execution evidence.

## TB-356 Measured Run-Root Reducer/Merge Profile

TB-356 reran the Balfrin access preflight and fast-forwarded the Balfrin clone
at `/users/olifu/work/rust_rockfall` from
`011f3737ef03e70566de0c68fa48eccd455c34c7` to
`955be7b089c32f3991642799c418785ff24e9f60` before read-only collection. No
jobs were submitted, no `sbatch` command was run, and no remote run root was
mutated.

Two-zone measured hazard evidence remains deferred. The intended smallest
multi-zone run root
`/scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_multi_release_zone_v1`
is absent on Balfrin. The read-only output-budget audit reports
`blocked_missing_run_root` with `0` output files, `0` manifest bytes,
`0` sidecars, `0` reducer chunks, missing replay-critical families
`trajectory_csv`, `deposition_csv`, `impact_events_csv`,
`trajectory_merge_state`, and `reducer_merge_state`, and missing replay hashes
`probe_manifest_sha256`, `command_plan_sha256`, and
`output_manifest_sha256`. This preserves the TB-352/TB-355 fail-closed boundary
and does not promote either branch as measured two-zone hazard evidence.

The available measured multi-zone reducer evidence is still the TB-312
four-zone Balfrin `postproc` run root:
`/scratch/mch/olifu/rust_rockfall/probes/tb312_four_zone_postproc_probe_v1/tb312_20260519T224500Z`.
The reducer-pressure summary over that run root reports `4` release zones,
`4` scenarios, `4` trajectory chunks, `2` reducer workers, and `2` reducer
chunks. Reducer merge ordering is `sorted_chunk_id`,
`merge_order_independent=true`, and `merge_order_deterministic=true`; the
measured reducer wall time in the pressure manifest is `1.63` seconds.

The run-root output-budget audit with
`next_larger_four_zone_review_only_probe` reports `compliant` and
`output budget accepted`: `25` output files, `15107` output bytes,
`12220` manifest bytes across `10` manifest files, `10` sidecars,
`6590` sidecar bytes, `2` reducer manifest files, `128` reducer-manifest bytes,
and `2` reducer chunks. The measured output-family counts are:

| Family | Files | Bytes |
| --- | ---: | ---: |
| `trajectory_csv` | `4` | `1548` |
| `deposition_csv` | `4` | `416` |
| `impact_events_csv` | `4` | `552` |
| `trajectory_chunk_manifest` | `4` | `268` |
| `reducer_chunk_manifest` | `2` | `128` |
| `trajectory_merge_state` | `1` | `108` |
| `reducer_merge_state` | `1` | `105` |
| `map_package_manifest` | `1` | `86` |
| `pilot_gis_package_manifest` | `1` | `92` |

Replay-critical outputs are retained for the measured four-zone postproc root:
`trajectory_csv`, `deposition_csv`, `impact_events_csv`,
`trajectory_merge_state`, and `reducer_merge_state`. The replay hashes are also
present: `probe_manifest_sha256`
`6eccf5362b7a6752c2ffd4711b386f9e0fbf975f841cafff31f7bf1eb46f68f3`,
`command_plan_sha256`
`5ea6cb093cc6f47e2a7c5284b9f9f4b2df8705d5663f3e0a545a9f71b03346ac`, and
`output_manifest_sha256`
`ba02b8dd51c585d8109eb4c29cfa7c6fc7d460ff247807ee8fe10bd7522e5854`.

No threshold change is made from TB-356. The measured four-zone `postproc`
run-root profile is within the existing four-zone review-only output-budget
thresholds, so its first measured budget bottleneck is `none`. The scratch-local
ladder and reducer-pressure helper remain separate: their pressure labels still
flag manifest/reducer pressure for planning, and the first local blocked rung
remains `8` zones. A measured two-zone hazard run root is still required before
four-zone hazard submission evidence or larger AOI claims can be upgraded.
