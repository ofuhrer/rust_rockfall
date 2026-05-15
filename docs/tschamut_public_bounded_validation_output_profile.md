# Bounded Validation Output Profile Summary

Final classification: `no_go`
Feasibility decision: `no_go`
Scale-up authorized: `False`
Validation output reduced: `True`
Validation output blocker status: `blocker_retained`
File-family pressure: `validation_debug_artifacts`
Defaults changed: `False`
Local output audit: `available`

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

- Status: `available`

## Validation Output Audit

- Status: `available`
- Manifest path: `validation/private/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_manifest.json`
- Reduced: `False`
- Validation output mode: `None`
- Family count: `7`
- Total file count: `125`
- Total bytes: `34545900`

Validation output families:
- `diagnostics_json`: files=`1` bytes=`3778` kind=`diagnostics` format=`json`
- `ensemble_deposition_csv`: files=`1` bytes=`8140` kind=`ensemble_deposition` format=`csv`
- `ensemble_impact_events_dir`: files=`60` bytes=`19759181` kind=`ensemble_impact_events` format=`csv_directory`
- `ensemble_stop_state_csv`: files=`1` bytes=`39649` kind=`ensemble_stop_state` format=`csv`
- `ensemble_trajectories_dir`: files=`60` bytes=`14461966` kind=`ensemble_trajectories` format=`csv_directory`
- `trajectory_csv`: files=`1` bytes=`244218` kind=`trajectory` format=`csv`
- `trajectory_metadata_csv`: files=`1` bytes=`28968` kind=`trajectory_metadata` format=`csv`

## Validation Output Comparison

- Status: `available`
- Validation output mode: `summary_only`
- Baseline file count: `125`
- Reduced file count: `4`
- Baseline bytes: `34545900`
- Reduced bytes: `81425`
- Reduction file-count delta: `121`
- Reduction byte delta: `34464475`
- Required provenance retained: `True`

Retained output classes:

Omitted or sampled output classes:
- `diagnostics_json`
- `ensemble_deposition_csv`
- `ensemble_impact_events_dir`
- `ensemble_stop_state_csv`
- `ensemble_trajectories_dir`
- `trajectory_csv`
- `trajectory_metadata_csv`

## Target-Side Validation Output Profile

- `target_validation_output_profile_status`: `measured`
- `validation_output_mode`: `summary_only`
- `defaults_changed`: `false`
- `blocked_reason`: `none`
- `validation_output_blocker_status`: `blocker_retained`
- `baseline_manifest_path`: `validation/private/tschamut_public_pilot/target_gate_v1/validation_tschamut_public_target_gate_v1_manifest.json`
- `reduced_manifest_path`: `validation/private/tschamut_public_pilot/target_gate_v1_summary_only/validation_tschamut_public_target_gate_v1_summary_only_manifest.json`
- `baseline_file_count`: `2005`
- `baseline_bytes`: `571368823`
- `reduced_file_count`: `4`
- `reduced_bytes`: `1271721`
- `reduction_file_count_delta`: `2001`
- `reduction_bytes_delta`: `570097102`
- `required_provenance_retained`: `true`
- `target_convergence_interpretation`: `inconclusive`
- `scale_up_authorized`: `false`
- `operational_claims_allowed`: `false`

## Hazard-Rebuild Compatibility

Read-only helper:
`scripts/check_hazard_rebuild_output_profile.py`

Current classification:
- `target_summary_only`: `summary_only_not_rebuildable`
- `sampling_sensitivity_v1_full`: `hazard_rebuild_ready`
- `sampling_sensitivity_v2_full`: `hazard_rebuild_ready`

Current target summary-only profile keeps:
- `diagnostics`
- `ensemble_deposition`
- `ensemble_stop_state`
- `trajectory_metadata`

Current target summary-only profile omits:
- `trajectory`
- `ensemble_trajectories`
- `ensemble_impact_events`

Minimal builder-facing reduced contract:
- `trajectory_csv` or `ensemble_trajectories_dir`
- `ensemble_deposition_csv`
- `ensemble_impact_events_dir` or `impact_events_csv` or `ensemble_impact_events_parquet`
- `diagnostics_json`

Optional overhead that the builder does not consume directly:
- `trajectory_metadata_csv`
- `ensemble_stop_state_csv`

Measured file pressure:
- current target summary-only root: `6` files / `1286207` bytes
- full bounded probe roots: `247` files / `68221148` bytes and `247` files / `68384888` bytes

Interpretation:
- the current summary-only profile is intentionally compact but not hazard-rebuild compatible;
- the full bounded probes remain hazard-rebuild-ready;
- a reduced profile can be specified safely by retaining the builder-facing families above, but the summary-only profile itself still lacks them.

## Rebuildable Reduced Profile

A concrete reduced profile is now derived from the current full target root
into an ignored local reduction root:

- derivation command:
  `PYENV_VERSION=system uv run python scripts/derive_hazard_rebuild_reduced_profile.py --format json`
- reduced root:
  `validation/private/tschamut_public_pilot/target_gate_v1_rebuildable_reduced`
- reduced validation output mode:
  `rebuildable_reduced_output`
- selected retained families:
  `trajectory`, `ensemble_deposition`, `impact_events_csv`, `trajectory_metadata`, `diagnostics`
- omitted families:
  `ensemble_trajectories`, `ensemble_impact_events`, `ensemble_stop_state`

Measured reduced profile size:

- reduced validation-root file count: `6`
- reduced validation-root byte count: `1202927`
- reduced validation outputs only: `5` files, `1192379` bytes
- compared with current target summary-only: `6` files, `1286207` bytes
- compared with the full target output: `2005` files, `571368823` bytes
- checker classification: `rebuildable_reduced_output`

The canonical command-plan path now exposes both the derivation command and
the scratch hazard-rebuild proof command through
`scripts/generate_pilot_command_plan.py --site tschamut_same_scale --format json`
under the `tschamut_same_scale::rebuildable_reduced_output` group. That keeps
the reduced-output workflow reproducible without implying that
`summary_only` itself is rebuildable.

Hazard-rebuild proof:

- command:
  `PYENV_VERSION=system uv run python scripts/build_hazard_layers.py --case validation/private/tschamut_public_pilot/target_gate_v1/tschamut_public_target_gate_case.yaml --trajectory validation/private/tschamut_public_pilot/target_gate_v1_rebuildable_reduced/validation_tschamut_public_target_gate_v1_trajectory.csv --deposition validation/private/tschamut_public_pilot/target_gate_v1_rebuildable_reduced/validation_tschamut_public_target_gate_v1_deposition.csv --impact-events validation/private/tschamut_public_pilot/target_gate_v1_rebuildable_reduced/validation_tschamut_public_target_gate_v1_rebuildable_reduced_impact_events.csv --diagnostics validation/private/tschamut_public_pilot/target_gate_v1_rebuildable_reduced/validation_tschamut_public_target_gate_v1_metrics.json --output-dir /tmp/tb042_reduced_hazard --grid-xmin 2696376.0 --grid-ymin 1167384.0 --grid-ncols 300 --grid-nrows 304 --grid-cell-size 2.0 --map-product-id tschamut_public_scalable_conditional_target_gate_v1_rebuildable_reduced --map-package-manifest-json /tmp/tb042_reduced_hazard/tschamut_public_scalable_conditional_target_gate_v1_rebuildable_reduced_map_package_manifest.json --export-geotiff --pilot-gis-package --pilot-gis-package-manifest-json /tmp/tb042_reduced_hazard/tschamut_public_scalable_conditional_target_gate_v1_rebuildable_reduced_pilot_gis_package_manifest.json --pilot-gis-qa-status not-run --pilot-gis-qa-note 'Reduced rebuildable profile proof; manual GIS/QGIS QA not run.' --trajectory-workers 2 --reducer-workers 2 --no-plots --conditional-curve-export summary-only --grid-csv-export none`
- elapsed wall time: `12.24` s
- hazard proof output root: `/tmp/tb042_reduced_hazard`
- proof output root file count: `63`
- proof output root bytes: `78431962`
- map-package manifest present: `True`
- pilot-GIS manifest present: `True`

Ignored-root inventory from `audit_local_artifacts.py`:

- Full target validation root: `2716` files, `764598257` bytes
- Target summary-only root: `6` files, `1286207` bytes

Validation output audit for the full-debug target manifest:

- Status: `available`
- Manifest path: `validation/private/tschamut_public_pilot/target_gate_v1/validation_tschamut_public_target_gate_v1_manifest.json`
- Validation output mode: `None`
- Family count: `7`
- Total file count: `2005`
- Total bytes: `571368823`

Validation output families:

- `diagnostics_json`: files=`1` bytes=`4009`
- `ensemble_deposition_csv`: files=`1` bytes=`135123`
- `ensemble_impact_events_dir`: files=`1000` bytes=`329167071`
- `ensemble_stop_state_csv`: files=`1` bytes=`645663`
- `ensemble_trajectories_dir`: files=`1000` bytes=`240699621`
- `trajectory_csv`: files=`1` bytes=`244218`
- `trajectory_metadata_csv`: files=`1` bytes=`473118`

Reduced summary-only validation families:

- `diagnostics_json`: files=`1` bytes=`3794`
- `ensemble_deposition_csv`: files=`1` bytes=`8138`
- `ensemble_stop_state_csv`: files=`1` bytes=`39667`
- `trajectory_metadata_csv`: files=`1` bytes=`29826`

Retained output classes in the summary-only target profile:

- `diagnostics_json`
- `ensemble_deposition_csv`
- `ensemble_stop_state_csv`
- `trajectory_metadata_csv`

Omitted or sampled output classes in the summary-only target profile:

- `ensemble_impact_events_dir`
- `ensemble_trajectories_dir`
- `trajectory_csv`

Provenance retained:

- `schema_version`: `run_manifest_v1`
- `performance`
- `trajectory_metadata`
- `outputs`
- `validation_output_mode: summary_only`

## Uncertainty Reduced

- The selected profile controls are explicit: summary-only conditional curves, no grid CSV, no plots, and two local reducer workers.
- Hazard-side output volume is bounded in the measured Balfrin reproduction record.
- Validation-side file and byte pressure is now measured separately from hazard-side output volume.
- Target-side summary-only validation output pressure is now measured separately from the same-scale gate path.
- The output-budget gate now records the file-family pressure label validation_debug_artifacts.
- Validation output families can be audited from a run manifest when the ignored manifest is locally available.

## Remaining Unresolved

- Conditional hazard-map convergence remains inconclusive.
- Validation debug output is reduced for the supplied comparison manifests, but target-scale scale-up still requires accepted convergence and output-budget evidence.
- Local ignored manifests are available for this audit, but generated outputs remain uncommitted and must be regenerated or staged on other checkouts.
- Scale-up is not authorized by the selected output-budget gate.
- The target-side summary-only profile remains diagnostic only and does not alter convergence interpretation.

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
