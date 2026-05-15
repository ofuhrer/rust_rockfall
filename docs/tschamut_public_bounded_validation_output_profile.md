# Bounded Validation Output Profile Summary

Final classification: `no_go`
Feasibility decision: `no_go`
Scale-up authorized: `False`
Validation output reduced: `False`
Validation output blocker status: `blocker_retained`
File-family pressure: `validation_debug_artifacts`
Defaults changed: `False`
Local output audit: `blocked_missing_outputs`

## Bounded Profile

- Case id: `tschamut_public_scalable_conditional_target_gate_v1`
- Case path: `validation/private/tschamut_public_pilot/target_gate_v1/tschamut_public_target_gate_case.yaml`
- Run id: `tschamut_public_balfrin_target_gate_reproduction_v1`
- Profile: `scalable_conditional`
- Validation command: `cargo run -- validate --case validation/private/tschamut_public_pilot/target_gate_v1/tschamut_public_target_gate_case.yaml`
- Conditional-curve export: `summary-only`
- Grid CSV export: `none`
- Plots enabled: `False`
- Trajectory workers: `2`
- Reducer workers: `2`
- Hazard output files: `46`
- Hazard output bytes: `16613900`
- Validation output files: `2005`
- Validation output bytes: `571377719`

Included output classes:
- `conditional_curve_summary_only`
- `geotiff_rasters`
- `pilot_gis_package`
- `chunk_manifests_and_restart_state`
- `checksum_sidecars`

Excluded output classes:
- `full_conditional_curve_csv`
- `grid_csv`
- `plot_outputs`

## Measured Pressure

- Current file count: `191`
- Current total bytes: `267527120`
- File ceiling: `200`
- Byte ceiling: `250000000`
- File-count margin: `9`
- Byte margin: `-17527120`
- Inode/file-family pressure: `validation_debug_artifacts`

## Measured Deltas vs Selected Target Budget

- Validation file-count delta: `1`
- Validation byte delta: `246514`
- Hazard file-count delta: `-8`
- Hazard byte delta: `-58809467`

## Convergence And Blockers

- Convergence status: `inconclusive`
- Validation debug output status: `blocker_retained`
- Output-budget status: `blocked_before_scale_up`
- QA status: `diagnostic_incomplete`
- Feasibility decision: `no_go`

## Local Output Audit

- Status: `blocked_missing_outputs`
- Missing path: `validation/private/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_manifest.json`
- Missing path: `hazard/results/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_manifest.json`
- Missing path: `hazard/results/tschamut_public_pilot/gate_v1/tschamut_public_conditional_gate_v1_map_package_manifest.json`
- Missing path: `hazard/results/tschamut_public_pilot/gate_v1/tschamut_public_conditional_gate_v1_pilot_gis_package_manifest.json`

## Validation Output Audit

- Status: `blocked_missing_outputs`
- Manifest path: `None`
- Reduced: `False`
- Validation output families are blocked until the ignored manifest is locally available.

Required for audit:
- `validation_manifest`

## Uncertainty Reduced

- The selected profile controls are explicit: summary-only conditional curves, no grid CSV, no plots, and two local reducer workers.
- Hazard-side output volume is bounded in the measured Balfrin reproduction record.
- Validation-side file and byte pressure is now measured separately from hazard-side output volume.
- The output-budget gate now records the file-family pressure label validation_debug_artifacts.
- Validation output families can be audited from a run manifest when the ignored manifest is locally available.

## Remaining Unresolved

- Conditional hazard-map convergence remains inconclusive.
- Validation debug output remains retained as a blocker for the next scale increase.
- Local ignored manifests are absent in this clean checkout, so local output audit remains blocked_missing_outputs.
- Scale-up is not authorized by the selected output-budget gate.

## Provenance

- `current_pressure_record_path`: `/Users/fuhrer/Desktop/rust_rockfall/main/validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml`
- `bounded_profile_record_path`: `/Users/fuhrer/Desktop/rust_rockfall/main/validation/pilot_runs/tschamut_public_balfrin_target_gate_reproduction_v1.yaml`
- `output_budget_record_path`: `/Users/fuhrer/Desktop/rust_rockfall/main/validation/pilot_runs/tschamut_public_output_budget_reducer_gate_v1.yaml`
- `convergence_record_path`: `/Users/fuhrer/Desktop/rust_rockfall/main/validation/pilot_runs/tschamut_public_conditional_convergence_protocol_v1.yaml`
- `ensemble_feasibility_record_path`: `/Users/fuhrer/Desktop/rust_rockfall/main/validation/pilot_runs/tschamut_public_ensemble_feasibility_v1.yaml`
- `output_budget_file_family_pressure`: `validation_debug_artifacts`
- `convergence_classification`: `inconclusive`
- `ensemble_feasibility_decision`: `no_go`

## Limitations

- The run is a research diagnostic conditional hazard-map reproduction, not operational validation.
- The scientific classification remains inconclusive until conditional convergence acceptance rules are defined and applied.
- Manual GIS/QGIS QA is still not run and is secondary interoperability evidence.
- Forest/obstacle context remains a separate interpretation limitation.
- The scalable output profile suppresses full conditional curve CSV and grid CSV outputs, so byte-level comparison to older local legacy-output target artifacts is not expected.
- Generated validation and hazard outputs remain ignored on balfrin and are not committed.
- This summary does not change physics, defaults, thresholds, release assumptions, validation cases, or baselines.
- The report is diagnostic and does not authorize scale-up.
