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