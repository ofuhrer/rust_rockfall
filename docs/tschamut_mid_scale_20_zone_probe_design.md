# Tschamut Mid-Scale 20-Release-Cell Probe Input Design

Status: probe inputs are now tracked for reproducible command-plan generation. Runtime outputs and manifests remain ignored.

## 1) Current input structure summary

The currently used conditional gate run is driven by:

- `validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml`
- `validation/private/tschamut_public_pilot/gate_v1/tschamut_public_conditional_gate_case.yaml`
- `data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_source_zone_metadata_v1.yaml`
- `data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_scenario_table_v1.csv`
- `validation/policies/tschamut_public_source_scenario_policy_v1.yaml`
- `validation/private/tschamut_public_pilot/gate_v1` validation outputs (generated)
- `hazard/results/tschamut_public_pilot/gate_v1` hazard outputs (generated)

Derived command-plan defaults from the run manifest include:

- `--trajectory-workers 2`
- `--reducer-workers 2`
- `--conditional-curve-export summary-only`
- `--grid-csv-export none`
- `--export-geotiff`
- `--no-plots`

Current small-gate constants in these files:

- `source_zone_metadata.release_sampling_policy.release_count: 10`
- `validation/policies/...` includes `requested_release_cell_count: 10`
- scenario table has 3 rows, all referencing `source_zone_id: tschamut_public_lps_release_bbox`
- validation case has `random.ensemble_size: 6`
- gate policy is `sampling_weighted_conditional` with `conditioned_on_filter`
- output grid geometry is `304 x 300`

## 2) Smallest safe design for a 20-release-cell probe

For this repository’s current schema, a single source-zone metadata file expresses one polygon and one `release_count` knob. The existing command and validation paths already support a deterministic-grid pilot at fixed grid/physics; therefore the smallest safe probe extension is:

- introduce a probe-specific source-zone/scenario pair with `release_count = 20`, while
- keeping the same per-zone trajectory policy (`6`) and all remaining physical/simulation parameters untouched.

This yields the target probe scale of:

- `20` release cells × `6` trajectories per release cell = `120` observed conditional trajectories.

Because the schema does not currently represent multiple independent source-zone records in one metadata file, this is implemented as “20 release cells” (not 20 independent source zones) and “release-cell count doubling” rather than adding a new ID-set.

### Proposed input-side edits (now tracked)

1. **Probe case file**:
- `validation/probes/tschamut_mid_scale_20_release_cell_v1/tschamut_public_mid_scale_20_release_cell_conditional_gate_case.yaml`
   - copied from `validation/private/tschamut_public_pilot/gate_v1/tschamut_public_conditional_gate_case.yaml`.
   - update:
     - `case_id` and all `outputs` paths (trajectory CSVs, metadata CSV, manifests, trajectories, impacts, etc.).
     - `probabilistic_metadata.source_zone_metadata_path` (probe-local copy).
     - `probabilistic_metadata.scenario_table_path` (probe-local copy).
     - `map_product_id` in both `probabilistic_metadata` and `hazard_map_package`.
     - `hazard_map_package.map_package_manifest_json` to a probe-local name.

2. **Probe source-zone metadata**:
- `validation/probes/tschamut_mid_scale_20_release_cell_v1/tschamut_public_source_zone_metadata_mid_scale_20_release_cell_v1.yaml`
   - started from `tschamut_public_source_zone_metadata_v1.yaml` and set:
     - `release_sampling_policy.release_count: 20`
   - keep geometry, CRS, mode, seed, and dataset/license provenance.

3. **Probe scenario table**:
- `validation/probes/tschamut_mid_scale_20_release_cell_v1/tschamut_public_scenario_table_mid_scale_20_release_cell_v1.csv`
   - preserve scenario rows and sampling parameters.
   - preserve `source_zone_id` unless you also choose a renamed probe source-zone id.

4. **Tracked probe pilot manifest**:
- `validation/probes/tschamut_mid_scale_20_release_cell_v1/tschamut_public_conditional_mid_scale_20_release_cell_pilot_run.yaml`
   - copy from `validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml` and override:
     - `run_id`
     - `run_status` set for planning/execution intent
     - `input_freeze.benchmark_case_path` -> probe case
     - `input_freeze.source_zone_metadata_path` -> probe source-zone metadata
     - `input_freeze.scenario_table_path` -> probe scenario table
     - `input_freeze.map_product_id` -> probe map product
     - `run_evidence` paths -> probe-local ignored artifact names
   - keep `sampling_plan.gate_run_trajectories_per_release_zone: 6`, `sampling_plan.worker_count: 2`, `hazard_output_plan` flags unchanged.

## 3) Why this tracked location

- `validation/private/**` remains ignored for generated outputs and timing sidecars.
- Tracked inputs in `validation/probes/...` provide deterministic command-plan regeneration after checkout.

## 4) File roles: tracked vs ignored

Tracked probe inputs:

- **Tracked**:
  - this design doc
  - `validation/probes/tschamut_mid_scale_20_release_cell_v1/tschamut_public_conditional_mid_scale_20_release_cell_pilot_run.yaml`
  - `validation/probes/tschamut_mid_scale_20_release_cell_v1/tschamut_public_mid_scale_20_release_cell_conditional_gate_case.yaml`
  - `validation/probes/tschamut_mid_scale_20_release_cell_v1/tschamut_public_source_zone_metadata_mid_scale_20_release_cell_v1.yaml`
  - `validation/probes/tschamut_mid_scale_20_release_cell_v1/tschamut_public_scenario_table_mid_scale_20_release_cell_v1.csv`
  - `validation/probes/tschamut_mid_scale_20_release_cell_v1/tschamut_public_source_scenario_policy_mid_scale_20_release_cell_v1.yaml`
- **Ignored/private outputs** (do not commit):
  - `validation/private/tschamut_public_pilot/mid_scale_20_release_cell_probe/...`
  - `hazard/results/tschamut_public_pilot/mid_scale_20_release_cell_probe/...`
  - timing sidecars, manifests, chunks, trajectory/deposition outputs, map-package manifests

## 5) Pre-execution validation checks before balfrin run

Before running the balfrin probe, validate the planned input bundle with lightweight checks:

1. `python3 scripts/validate_public_real_site_conditional_pilot_run.py <probe_manifest.yaml> --print-command-plan --format json`
2. `python3 scripts/validate_source_scenario_policy.py <probe_policy.yaml>`
3. Confirm `source_zone_metadata` and `scenario_table` consistency:
   - all scenario table rows use the same `source_zone_id` as probe metadata.
   - all `scenario_id` values remain valid for the probe.
4. Confirm generated command plan flags include expected controls:
   - `--conditional-curve-export summary-only`
   - `--grid-csv-export none`
   - `--export-geotiff`
   - `--no-plots`
   - `--trajectory-workers 2`
   - `--reducer-workers 2`
5. Confirm `source_zone_id`/`scenario_id` filters in the case match the probe metadata.
6. Confirm output roots stay intentionally uncommitted:
   - `validation/private/tschamut_public_pilot/mid_scale_20_release_cell_probe`
   - `hazard/results/tschamut_public_pilot/mid_scale_20_release_cell_probe`
7. Confirm run manifests and map-package fields reference the probe `map_product_id`.

## 6) Recommended balfrin-facing artifacts to generate later

For the first run only, generate these minimal files locally in ignored output paths:

- private validation case manifest and trajectory/deposition artifacts
- private hazard manifest and reducer chunks
- private map-package and pilot-GIS package manifests
- private timing sidecar and scaling summary

These artifacts are runtime outputs and must remain untracked.

## 7) Source-scenario policy consistency

Current implementation uses the tracked policy copy in the tracked manifest and keeps requested-cell consistency explicit:

- `validation/probes/tschamut_mid_scale_20_release_cell_v1/tschamut_public_source_scenario_policy_mid_scale_20_release_cell_v1.yaml`
- `requested_release_cell_count: 20`
- source-scenario and source metadata IDs aligned with the tracked probe manifest.
