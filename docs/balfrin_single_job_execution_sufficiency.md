# Balfrin Single-Job Execution Sufficiency

- Decision: `defer`
- Single-job sufficient for next step: `True`
- Distributed execution authorized: `False`
- Final classification: `defer`
- Feasibility decision: `defer`
- Validation output blocker status: `blocker_retained`
- File-family pressure: `validation_debug_artifacts`
- Defaults changed: `False`

## Wall Time Evidence

- `repeatability_fresh_baseline_total_wall_seconds`: `14.95406103390269`
- `repeatability_fresh_baseline_command_sequence_wall_seconds`: `23.446129538002424`
- `repeatability_repeat_run_total_wall_seconds`: `[10.46352063305676, 10.459748723078519]`
- `reproduction_validation_wall_seconds`: `55.277021307`
- `reproduction_hazard_wall_seconds`: `55.12473134789616`
- `current_gap_runtime_seconds`: `17.84`

## Memory Evidence

- `current_gap_memory_peak_mb`: `409.22`
- `reproduction_validation_memory_peak_bytes_on_darwin`: `367017984`
- `reproduction_hazard_memory_peak_bytes_on_darwin`: `411058176`
- `output_budget_validation_memory_peak_bytes_on_darwin`: `367017984`
- `output_budget_hazard_memory_peak_bytes_on_darwin`: `411058176`

## Output Size Evidence

- `repeatability_fresh_baseline_output_file_count`: `46`
- `repeatability_fresh_baseline_output_bytes`: `32124738`
- `repeatability_repeat_output_file_counts`: `[46, 46]`
- `repeatability_repeat_output_bytes`: `[32125888, 32125876]`
- `reproduction_validation_output_file_count`: `2005`
- `reproduction_validation_output_bytes`: `571377719`
- `reproduction_hazard_output_file_count`: `46`
- `reproduction_hazard_output_bytes`: `16613900`
- `current_gap_output_file_count`: `191`
- `current_gap_output_bytes`: `267527120`
- `output_budget_validation_output_file_count`: `2004`
- `output_budget_validation_output_bytes`: `571131205`
- `output_budget_hazard_output_file_count`: `54`
- `output_budget_hazard_output_bytes`: `75423367`

## Post-Run Interpretation Gate

The Balfrin post-run interpretation gate is
`scripts/summarize_balfrin_post_run_interpretation_gate.py`. It composes the
contract-ready release-zone scope, the single-job sufficiency signal, the
stability-frontier proxy, GIS / COG readiness, and the physical-credibility
boundary checks into one read-only diagnostic summary.

The gate uses three post-run states:

- `measured` when readiness, stability, output, GIS / COG, and claim-boundary
  checks all support a conditional diagnostic artifact;
- `inconclusive` when the artifact is still diagnostic but one or more checks
  remain unresolved or weaker than the measured state;
- `blocked_missing_inputs` when a required evidence input is absent.

The gate can accept a conditional diagnostic artifact while keeping these
boundaries explicit:

- `operational_claims_allowed`: `False`
- `physical_probability_claims_allowed`: `False`
- `annual_frequency_claims_allowed`: `False`
- `risk_exposure_vulnerability_claims_allowed`: `False`
- `scale_up_authorized`: `False`
- `distributed_execution_authorized`: `False`

## Restartability Evidence

- `driver_ready_for_selected_gate_use`: `True`
- `fresh_baseline_job_id`: `4289703`
- `repeat_job_ids`: `['4318872', '4318896']`
- `repeat_reuse_classification`: `pass_reuse_stable`
- `trajectory_plan_id_stable`: `True`
- `reducer_plan_id_stable`: `True`
- `numerical_artifact_classification`: `pass_hash_stable`
- `changed_artifact_count`: `0`
- `output_file_count_stable`: `True`
- `metadata_byte_identity_required`: `False`

## Reducer State Evidence

- `reducer_mode`: `chunked_local_threads`
- `reducer_workers`: `2`
- `reducer_chunk_count`: `2`
- `reducer_merge_order`: `sorted_chunk_id`
- `reducer_merge_order_independent`: `True`
- `reducer_parity_status`: `pass_for_hazard_reducer_outputs`
- `local_restartability_status`: `recorded`
- `reducer_chunk_manifest_status`: `generated`
- `reducer_execution_index_status`: `generated`
- `reducer_merge_state_status`: `generated`
- `worker_counts_compared`: `[1, 2]`

## Metrics Contract

- `status`: `complete`
- `missing_mandatory_metrics`: `[]`
- `metric_statuses.mandatory`:
  - measured fields:
    - wall time
    - memory peak
    - validation output file count
    - validation output bytes
    - hazard output file count
    - hazard output bytes
    - conditional curve row count
    - restartability metadata
  - blocked fields: none in the current measured bundle
- `metric_statuses.ancillary`:
  - measured split-output fields when the live run-root scaling summary is still available:
    - output write kind seconds
    - output write kind bytes
  - unavailable by design in the canonical bundle snapshot:
    - validation output mode
    - output write kind seconds
    - output write kind bytes
- `metric_statuses.measured`: measured mandatory fields plus any ancillary fields recovered from the live run-root summary
- `metric_statuses.unavailable`: ancillary fields that the canonical bundle cannot recover from the preserved single-job summary alone
- `metric_statuses.blocked`: mandatory fields missing from the measured evidence chain
- `metrics_remediation`: machine-readable next-run collection contract with ordered
  `missing_mandatory_metrics`, `unavailable_ancillary_metrics`,
  `next_run_required_metrics`, and `next_run_collection_checklist` entries
  for every field that remains absent from the preserved evidence chain
- Restartability metadata must include stable trajectory and reducer plan IDs, plus the observed decision counts for completed chunks.
- If any mandatory field is absent, the collector reports the run as blocked rather than treating it as feasibility evidence.

For a deterministic target-area metrics completeness report from the measured
run root, use the report helper:

```bash
PYENV_VERSION=system uv run python scripts/summarize_balfrin_probe_metrics_report.py \
  --evidence-json /scratch/mch/olifu/rust_rockfall/probes/tschamut_public_balfrin_target_area_demo_v1/authorized_tb168_20260517/balfrin_probe_metrics.json \
  --artifact-dir validation/private/tschamut_public_pilot/balfrin_probe_metrics_v1
```

The helper materializes `balfrin_probe_metrics_report_v1.json` and
`balfrin_probe_metrics_report_v1.txt` in that directory. Its classification
keeps mandatory metrics, ancillary metrics, unavailable fields, and
next-run-required metrics explicit, and it reports `blocked_missing_run_root`
when the measured run root is absent.

The canonical conditional diagnostic interpretation helper,
`scripts/summarize_tschamut_conditional_diagnostic_interpretation.py`, is the
preferred synthesis entrypoint when the current single-job evidence needs to
be bundled into JSON and text artifacts. Use `--artifact-dir validation/private/tschamut_public_pilot/diagnostic_interpretation_v1`
to materialize that bundle without changing the execution boundary.
The Balfrin post-run interpretation gate,
`scripts/summarize_balfrin_post_run_interpretation_gate.py`, is the read-only
acceptance layer for a conditional diagnostic artifact. It keeps operational
and physical-probability claims false even when the artifact is accepted.

## Canonical Balfrin Evidence Bundle

For management-facing review, use the canonical Balfrin evidence bundle helper:

```bash
PYENV_VERSION=system uv run python scripts/summarize_balfrin_evidence_bundle.py \
  --artifact-dir validation/private/tschamut_public_pilot/balfrin_evidence_bundle_v1
```

The helper materializes `balfrin_evidence_bundle_v1.json` and
`balfrin_evidence_bundle_v1.txt` in that directory. It assembles the single-job
evidence, probe metrics, GIS / COG readiness, restartability, and post-run
interpretation checks into one read-only review artifact, and it now carries a
machine-readable failure taxonomy report for operational recovery handoff.
Its bundle summary also records measured, fixture-backed, and blocked section
counts so the canonical review path can distinguish live Balfrin evidence from
fixture-only or blocked sections. The probe-metrics section now makes the
mandatory, ancillary, measured, unavailable, and blocked fields explicit so a
reader can see which fields are measured in the live run-root collector and
which fields are unavailable in the canonical summary because the preserved
bundle does not retain the run-root `output_root.scaling_summary` tree.
The probe-metrics section also exposes `metrics_remediation`, a deterministic
next-run checklist that enumerates the remaining missing mandatory metrics and
the high-value ancillary fields that must be preserved in the next measured
run.
When evidence is missing, it reports `blocked_missing_inputs` instead of
fabricating a stronger claim.

For a single deterministic replay smoke check, use the run-root driven helper:

```bash
PYENV_VERSION=system uv run python scripts/summarize_balfrin_demonstration_replay_smoke.py \
  --run-root /scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_single_release_zone_v3 \
  --artifact-dir /tmp/balfrin_demonstration_replay_smoke_v1
```

The smoke helper checks that the run root is present, regenerates the Balfrin
evidence bundle and post-run interpretation outputs into the artifact
directory, and returns `blocked_missing_inputs` when the run root is absent or
the required replay artifacts are unavailable.
Its report now also records `run_root_provenance` so fixture-backed replay
coverage is distinguishable from a non-fixture live run root. A fixture path
under `tests/fixtures/...` is reported as `fixture_backed`; a present
non-fixture run root is reported as `live_run_root`; and an absent path
remains `missing`.

For a compact management-facing package manifest that keeps runtime, replay,
AOI automation, release/scenario automation, restartability, GIS scope,
uncertainty, Swiss-wide extension blockers, and claim boundaries separate, use
`scripts/summarize_balfrin_management_demo_package.py`:

```bash
PYENV_VERSION=system uv run python scripts/summarize_balfrin_management_demo_package.py \
  --run-root tests/fixtures/balfrin_probe_metrics_contract/complete_run_root \
  --artifact-dir /tmp/balfrin_management_demo_package_v1
```

The helper materializes `balfrin_management_demo_package_v1.json` and
`balfrin_management_demo_package_v1.txt` in the chosen directory. Its manifest
also records a deterministic regeneration command sequence so the package can
be replayed without merging measured evidence with the fixture-backed replay
section. It also keeps the false operational, annual-frequency, physical-
probability, scale-up, and distributed-execution boundaries explicit, and it
includes an explicit management answer about Swiss-wide extensibility with
the current blockers named rather than inferred.

## Scientific Blockers

- `conditional_hazard_convergence_not_accepted` from `conditional_convergence_protocol`: current_classification remains inconclusive in the convergence protocol
- `manual_gis_visual_qa_secondary_only` from `conditional_convergence_protocol`: manual GIS/QGIS QA remains secondary and not run here
- `forest_obstacle_context_limiting` from `conditional_convergence_protocol`: forest/obstacle context remains limiting
- `validation_debug_output_budget_retained` from `conditional_convergence_protocol`: validation-side debug output remains retained
- `target_scale_convergence_inconclusive` from `ensemble_feasibility_record`: recorded as a current blocker to increase the selected-domain run
- `manual_gis_visual_qa_inconclusive` from `ensemble_feasibility_record`: recorded as a current blocker to increase the selected-domain run
- `forest_obstacle_omission_limiting` from `ensemble_feasibility_record`: recorded as a current blocker to increase the selected-domain run
- `validation_debug_output_budget_too_large_for_next_increase` from `ensemble_feasibility_record`: recorded as a current blocker to increase the selected-domain run
- `target_vs_small_gate_convergence_not_accepted` from `conditional_convergence_protocol`: recorded as an active convergence blocker
- `accepted_target_vs_small_gate_convergence_interpretation` from `ensemble_feasibility_record`: missing diagnostic remains part of the no-go record
- `manual_gis_visual_qa_for_target_package` from `ensemble_feasibility_record`: missing diagnostic remains part of the no-go record
- `forest_obstacle_context_review_for_target_outputs` from `ensemble_feasibility_record`: missing diagnostic remains part of the no-go record
- `validation_debug_output_reduction_or_justification` from `ensemble_feasibility_record`: missing diagnostic remains part of the no-go record

## Execution Blockers

- `distributed_execution_not_authorized` from `output_budget_reducer_gate`: distributed reducers and SLURM arrays remain outside the current authorization
- `single_job_driver_remains_sufficient` from `balfrin_probe_repeatability`: repeat and reproduction evidence show the single-job path is stable for the next same-scale step
- `single_job_restartability_recorded` from `output_budget_reducer_gate`: restart and merge state evidence is recorded under the single-job boundary

## Recommended Next Step

Continue using the single-job Balfrin SLURM driver for the next same-scale selected Tschamut conditional hazard-map reproduction; keep distributed execution deferred until a new measurement shows a capacity need.

For planning larger AOI counts without changing that execution boundary, use
`scripts/estimate_swiss_wide_execution_envelope.py`. The helper is read-only:
it projects runtime, storage, file-count, and job-count bands from measured
same-scale and Balfrin coefficients, and it labels extrapolated multi-AOI
requests as no-go planning cases rather than as authorized scale-up.

The current Swiss-wide projection from the measured target-area evidence
(`--aoi-count 26 --release-zone-count 10 --trajectory-count 6`) is a
`no_go_extrapolated_beyond_measured_evidence` case. The helper reports
`no_go_labels` of `aoi_count_exceeds_measured_support` and
`total_job_count_exceeds_measured_single_job_support`, with planning labels of
`no_go_extrapolated_beyond_measured_evidence`,
`defer_scale_up_authorized_false`, and
`allowed_next_probe_measured_existing_artifacts`.

The helper now also emits a canonical four-case planning table so the next
scale labels are explicit before larger runs are attempted:

- `10_zone`: `next_probe`
- `100_zone`: `defer`
- `regional`: `no_go`
- `swiss_wide`: `no_go`

That table reuses the measured single-job evidence, the target-area probe
metrics when the authorized run root is available, and the deterministic
scenario-table stress evidence for manifest and scheduler bottleneck labels.

- Runtime band: `347.825` / `463.84` / `1437.203` s
- Storage band: `33441382` / `102793652` / `6955705120` bytes
- File-count band: `156` / `442` / `4966`
- Memory band: `367.018` / `409.22` / `411.058` MB
- Interpretation: the measured target-area evidence supports a bounded local
  next step, but it does not authorize Swiss-wide scale-up.

## Limitations

- This summary reuses recorded Balfrin and reducer evidence; it does not run a new simulation.
- Distributed execution remains unauthorized by the current evidence set.
- The summary stays conditional and non-operational and does not change physics, defaults, thresholds, or baselines.

## Record Paths

- `repeatability_record`: `validation/pilot_runs/tschamut_public_slurm_probe_repeatability_v1.yaml`
- `reproduction_record`: `validation/pilot_runs/tschamut_public_balfrin_target_gate_reproduction_v1.yaml`
- `output_budget_record`: `validation/pilot_runs/tschamut_public_output_budget_reducer_gate_v1.yaml`
- `convergence_record`: `validation/pilot_runs/tschamut_public_conditional_convergence_protocol_v1.yaml`
- `feasibility_record`: `validation/pilot_runs/tschamut_public_ensemble_feasibility_v1.yaml`
- `current_gap_record`: `validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml`

## Bounded Reducer Scaling Evidence

- `bounded_reducer_scaling_status`: `measured_existing_artifacts`
- `bounded_reducer_scaling_command`: `PYENV_VERSION=system uv run python scripts/summarize_bounded_reducer_runtime_scaling.py --format json`
- `timing_source`: `manifest_performance.total_wall_seconds`
- `reducer_workers_compared`: `[2, 2, null, 2]`
- `hazard_layer_counts`: `[22, 22, 22, 22]`
- `validation_roots_file_counts`: `[127, 2716, 247, 247]`
- `validation_roots_bytes`: `[34560918, 764598283, 68221148, 68384888]`
- `hazard_roots_file_counts`: `[56, 56, 49, 56]`
- `hazard_roots_bytes`: `[77758043, 79160991, 21058710, 77883219]`
- `validation_runtime_seconds`: `[3.999294125, 272.573375917, 8.460070916, 7.736682417]`
- `hazard_runtime_seconds`: `[7.108489040983841, 41.61543712497223, 9.922129791986663, 12.383317541971337]`
- `bottleneck_classification`: `validation_output_size`
- `output_scaling_findings`:
  - target validation output remains the dominant volume pressure;
  - target validation runtime is the slowest observed stage in the measured same-scale set;
  - the measured reducer remains chunked local threads with two workers for gate and target;
  - the bounded sampling probes stay near the same order of magnitude without a distributed-reducer signal.

The bounded same-scale measurement supports the existing conclusion: local single-job execution is still sufficient for the next same-scale step, and distributed execution remains unauthorized by the current evidence set.

The combined stability-frontier helper,
`scripts/summarize_same_scale_stability_frontier.py`,
now folds the same-scale uncertainty, bounded runtime/output, bounded
next-probe feasibility, and closure-gap evidence into one conservative
recommendation for whether another small probe would still be informative.

## Minimal Bounded Probe Status

The minimal bounded Balfrin follow-up probe moved from planning handoff to one
explicitly authorized measured run. TB-168 submitted the frozen target-area
contract as SLURM job `4329024`, which completed successfully at:

- `/scratch/mch/olifu/rust_rockfall/probes/tschamut_public_balfrin_target_area_demo_v1/authorized_tb168_20260517`

- Probe status: `measured_authorized_probe_completed`
- Planning state: `--generate-only` remains available for future handoffs, but
  a generated package is not execution approval
- Metrics state: measured wall time, output bytes, file count, and conditional
  curve rows are available; peak memory and split validation/hazard output
  metrics remain incomplete in the preserved target-area evidence
- Safety state: `scale_up_authorized` and `distributed_execution_authorized`
  remain false
- Failure mode: removing either optional metadata block still produces a
  fail-closed missing-metadata report

The practical frontier helper
`scripts/summarize_balfrin_ensemble_frontier.py` and the Swiss-wide envelope
helper use this bounded measured probe as evidence, while keeping additional
probes and scale-up deferred until explicitly authorized.
`scripts/submit_balfrin_probe.py --generate-only` can still emit an unlaunched
submission package without invoking the full frontier scan. That package is an
operator handoff, not execution approval.

TB-156 added a metrics-remediation contract for the Balfrin evidence bundle. It
separates missing mandatory metrics, unavailable ancillary metrics, and
next-run-required collection fields so follow-up work can improve measured
evidence without implying that another ensemble has already run.
