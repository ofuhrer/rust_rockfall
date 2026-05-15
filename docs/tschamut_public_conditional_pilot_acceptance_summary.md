# Measured Conditional Pilot Acceptance Summary

Status: inconclusive

## Result

- Pilot: `tschamut_public_pilot`
- Final classification: `inconclusive`
- Scale-up authorized: `false`
- Convergence status: `inconclusive`
- Output-budget status: `blocked_before_scale_up`
- Blocker status: `present`

## Measured Evidence

### Target Gate
- gate_status: `inconclusive`
- release_cell_count: `10`
- target_trajectories_per_release_zone: `100`
- validation_output_file_count: `2004`
- validation_output_bytes: `571131205`
- hazard_output_file_count: `54`
- hazard_output_bytes: `75423367`

### Balfrin
- reproducibility_classification: `inconclusive`
- simulated_trajectory_count: `1000`
- validation_output_file_count: `2005`
- validation_output_bytes: `571377719`
- hazard_output_file_count: `46`
- hazard_output_bytes: `16613900`

### Convergence
- current_classification: `inconclusive`
- scale_up_authorized: `False`
- blocking_reasons: `['target_vs_small_gate_convergence_not_accepted', 'manual_gis_visual_qa_secondary_only', 'forest_obstacle_context_limiting', 'validation_debug_output_budget_retained']`
- convergence_indicators: `{'status': 'inconclusive', 'target_vs_small_gate_convergence_accepted': False, 'manual_gis_visual_qa_status': 'not_run', 'forest_obstacle_context_status': 'limiting', 'validation_debug_output_volume_status': 'blocker_retained'}`

### Output Budget
- current_classification: `blocked_before_scale_up`
- qa_status: `diagnostic_incomplete`
- validation_output_file_count: `2004`
- validation_output_bytes: `571131205`
- hazard_output_file_count: `54`
- hazard_output_bytes: `75423367`
- validation_debug_output_budget_status: `blocker_retained`

## Uncertainty Reduced

- target_run_provenance is fixed across the selected gate and the Balfrin reproduction
- frozen inputs and deterministic seed-order-chunk metadata are recorded in the convergence protocol
- 1-worker and 2-worker reducer outputs matched for deposition points and hazard layers
- summary-only conditional curves and grid-CSV suppression are recorded for the target gate
- checksum provenance is recorded for the validation, hazard, map-package, and pilot-GIS artifacts
- validation-side and hazard-side output volumes are measured for the selected gate

## Remaining Unresolved

- conditional hazard-map convergence has not been accepted
- manual GIS/QGIS visual QA remains secondary and was not run here
- forest and obstacle context remains limiting
- validation debug-output volume remains a blocker for larger scale-up

## Evidence Records Read

- `validation/pilot_runs/tschamut_public_scalable_conditional_target_gate_v1.yaml`
- `validation/pilot_runs/tschamut_public_balfrin_target_gate_reproduction_v1.yaml`
- `validation/pilot_runs/tschamut_public_conditional_convergence_protocol_v1.yaml`
- `validation/pilot_runs/tschamut_public_output_budget_reducer_gate_v1.yaml`

## Reference Documents

- `docs/conditional_hazard_convergence_acceptance_protocol.md`
- `docs/output_budget_reducer_scaling_gate.md`
- `docs/tschamut_public_scalable_conditional_target_gate.md`

## Classification Rationale

The workflow completed and the evidence is usable, but conditional convergence remains inconclusive, the output budget remains blocked_before_scale_up, and the validation debug-output volume remains a blocker with status blocker_retained.
