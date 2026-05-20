# TB-367 Balfrin Two-Zone Hazard Rerun Outcome

Date: 2026-05-20

## Summary

TB-367 repaired the submit driver so `probe.sbatch` executes the generated
`command_plan.json` instead of regenerating the legacy gate command plan at
runtime. The generated plan now binds the hazard stage to the preserved run-root
layout under `output/validation_balfrin_probe*` and carries the compact output
controls `--conditional-curve-export summary-only` and `--grid-csv-export none`.

One authorized `postproc` rerun was submitted and completed, but the run is not
promoted to measured two-zone hazard evidence. The preservation gate failed on a
new blocker: the executed command did not create `output/trajectory_chunks`, so
trajectory restartability metadata and trajectory chunk manifests are missing.
This is not the legacy TB-366 gate-manifest/output-root contract.

This is a live execution record and fail-closed blocker report, not an
operational hazard assessment and not scale-up evidence.

## Local Repair And Dry-Run Proof

Focused regression coverage was added for `scripts/submit_balfrin_probe.py`.
The dry-run/generate-only proof verified that generated `command_plan.json` and
`probe.sbatch` preserve:

- `--output-dir <run-root>/output`
- `--prefix validation_balfrin_probe`
- `--conditional-curve-export summary-only`
- `--grid-csv-export none`
- `--map-package-manifest-json <run-root>/output/validation_balfrin_probe_map_package_manifest.json`
- `--pilot-gis-package-manifest-json <run-root>/output/validation_balfrin_probe_pilot_gis_package_manifest.json`
- `probe.sbatch` uses the prebuilt `${RUN_ROOT}/command_plan.json`
- `probe.sbatch` no longer calls `validate_public_real_site_conditional_pilot_run.py`
  to overwrite the plan at runtime

After the live fail-closed outcome identified the missing trajectory chunk
blocker, the local submit contract was further tightened to force
`--trajectory-workers 2` and `--reducer-workers 2` in the preserved plan. That
post-run repair has focused dry-run proof, but it was not resubmitted under
TB-367 because the task allowed exactly one bounded rerun.

## Pre-Submit Gates

- Local repair commit pushed before live run: `f5222535cd254e3cc2c6e544570f020626069515`
- Balfrin checkout: `/users/olifu/work/rust_rockfall`
- Remote checkout after fast-forward: `f5222535cd254e3cc2c6e544570f020626069515`
- Remote checkout hygiene after fast-forward: clean
- Access preflight after fast-forward: `ready_for_read_only_collection`
- Smallest multi-zone authorization preflight:
  - `preflight_status`: `ready_for_authorization_review`
  - `submit_contract_status`: `ready`
  - `output_profile_status`: `ready`
  - `reducer_budget_status`: `ready`
  - `output_budget_acceptance_status`: `accepted`

The `postproc` partition had idle nodes before submit. The submitted job
requested one node, 16 CPUs, and a 30 minute limit, so it did not trigger the
six-hour full-partition rediscussion boundary.

## Submitted Job

- Job id: `4344036`
- Partition: `postproc`
- State: `COMPLETED`
- Exit code: `0:0`
- Elapsed: `00:00:36`
- Batch MaxRSS: `177072K`
- Allocated CPUs: `16`
- Work directory: `/users/olifu/work/rust_rockfall`
- Run root:
  `/scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_multi_release_zone_v1`
- Stdout:
  `/scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_multi_release_zone_v1/logs/slurm-4344036.out`
- Stderr:
  `/scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_multi_release_zone_v1/logs/slurm-4344036.err`

## Collected Metrics

From `balfrin_probe_metrics.json` after collecting SLURM accounting:

- `report_status`: `incomplete_run_root`
- `metrics_contract_status`: `blocked_missing_inputs`
- Missing mandatory metrics:
  `restartability_metadata.trajectory_plan_id`,
  `restartability_metadata.trajectory_decision_counts`
- `memory_peak_mb`: `172.921875`
- Total wall seconds recorded by collector: `8.262323980001383`
- Validation output: `130` files, `34565490` bytes
- Hazard output: `46` files, `55763017` bytes
- Conditional curve row count: `729600`
- Preserved output families included hazard layers, reducer execution plan,
  reducer execution index, reducer merge state, two reducer chunk manifests,
  map-package manifest, and pilot GIS package manifest.

## Preservation Gate

`scripts/summarize_balfrin_probe_preservation_gate.py` reported:

- `preservation_gate_status`: `blocked_missing_inputs`
- `required_run_root_entries_status`: `blocked_missing_inputs`
- Missing run-root entry: `output/trajectory_chunks`
- `output_family_summaries.status`: `blocked_missing_measured_output`
- Missing required output family: `trajectory_chunk_manifest`
- `spatial_gis_artifact_paths.status`: `declared`

Blocked reasons:

- `metrics_contract:blocked_missing_inputs`
- `missing_run_root_entries:output/trajectory_chunks`
- `output_tier:blocked_missing_measured_output`

The output-budget audit also remains blocked on compressible manifest/file-count
pressure and missing replay-critical trajectory-side families, but the primary
definition-of-done blocker for this run is the absent trajectory chunk
preservation path.

## Outcome

TB-367 produced a completed `postproc` job using the repaired run-root hazard
output path and compact curve/grid controls, but it did not produce preserved
measured two-zone hazard evidence. The persistent blocker is now explicit:
the live command must preserve trajectory chunk manifests and trajectory
restartability metadata, not just reducer chunks.

The submit driver has been updated after the live run to force
`--trajectory-workers 2` and `--reducer-workers 2` in the preserved command
plan. A successor task may use that dry-run proof as the starting point for a
new authorization-gated rerun.

## Boundaries

- Exactly one TB-367 live job was submitted.
- Only the `postproc` partition was used.
- No distributed execution or scale-up claim is made.
- No operational hazard assessment is made.
- No annual-frequency, physical-probability, risk, exposure, or vulnerability
  claim is made.
- Generated Balfrin outputs remain under scratch or ignored output roots and
  are not committed.
