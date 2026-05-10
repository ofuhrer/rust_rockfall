# Tschamut Mid-Scale 20-Release-Cell Probe Input Design

Status: planning design only. This task does not create probe inputs yet.

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

### Proposed input-side edits (to be generated later)

1. **Private probe case file** (private copy first):
- `validation/private/tschamut_public_pilot/mid_scale_20_release_cell_probe/tschamut_public_mid_scale_20_release_cell_conditional_gate_case.yaml`
   - copy from `validation/private/tschamut_public_pilot/gate_v1/tschamut_public_conditional_gate_case.yaml`.
   - update:
     - `case_id` and all `outputs` paths (trajectory CSVs, metadata CSV, manifests, trajectories, impacts, etc.).
     - `probabilistic_metadata.source_zone_metadata_path` (probe-local copy).
     - `probabilistic_metadata.scenario_table_path` (probe-local copy).
     - `map_product_id` in both `probabilistic_metadata` and `hazard_map_package`.
     - `hazard_map_package.map_package_manifest_json` to a probe-local name.

2. **Probe source-zone metadata** (private copy):
- `validation/private/tschamut_public_pilot/mid_scale_20_release_cell_probe/tschamut_public_source_zone_metadata_mid_scale_20_release_cell_v1.yaml`
   - start from `tschamut_public_source_zone_metadata_v1.yaml` and set:
     - `release_sampling_policy.release_count: 20`
   - keep geometry, CRS, mode, seed, and dataset/license provenance.

3. **Probe scenario table** (private copy):
- `validation/private/tschamut_public_pilot/mid_scale_20_release_cell_probe/tschamut_public_scenario_table_mid_scale_20_release_cell_v1.csv`
   - preserve scenario rows and sampling parameters.
   - preserve `source_zone_id` unless you also choose a renamed probe source-zone id.

4. **Private probe pilot manifest** (for balfrin execution later):
- `validation/private/tschamut_public_pilot/mid_scale_20_release_cell_probe/tschamut_public_conditional_mid_scale_20_release_cell_pilot_run.yaml`
   - copy from `validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml` and override:
     - `run_id`
     - `run_status = gate_run_completed` (or `template_not_run` during dry planning)
     - `input_freeze.benchmark_case_path` -> probe case
     - `input_freeze.source_zone_metadata_path` -> probe source-zone metadata
     - `input_freeze.scenario_table_path` -> probe scenario table
     - `input_freeze.map_product_id` -> probe map product
     - `run_evidence` paths -> probe-local ignored artifact names
   - keep `sampling_plan.gate_run_trajectories_per_release_zone: 6`, `sampling_plan.worker_count: 2`, `hazard_output_plan` flags unchanged.

## 3) Why not duplicate everything in tracked `validation/pilot_runs` now?

- `validation/private/**` is already ignored in `.gitignore`; probe-specific inputs and outputs can therefore stay out of git.
- Existing shared files in `validation/pilot_runs`, `validation/policies`, and `data/processed/...` remain stable and continue to support gate reproducibility.
- This keeps the current conditional gate as the source-of-truth baseline while isolating probe-only perturbations.

## 4) File roles: tracked vs ignored

Track only short documentation and optional templates; keep mutable probe inputs/outputs private:

- **Tracked**: this design doc, and optionally a tiny probe template manifest in `validation/templates` (if desired for future repeatability).
- **Ignored/private** (do not commit):
  - probe case file
  - probe source-zone metadata
  - probe scenario table
  - probe pilot manifest with environment-local paths
  - all probe validation/hazard outputs and timing sidecars

## 5) Pre-execution validation checks before balfrin run

Before running the balfrin probe, validate the planned input bundle with lightweight checks:

1. `python3 scripts/validate_public_real_site_conditional_pilot_run.py <probe_manifest.yaml> --print-command-plan --format json`
2. `python3 scripts/validate_source_scenario_policy.py validation/policies/tschamut_public_source_scenario_policy_v1.yaml` (or a probe-policy copy, if used).
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
   - `validation/private/...`
   - `hazard/results/...`
7. Confirm run manifests and map-package fields reference the probe `map_product_id`.

## 6) Recommended balfrin-facing artifacts to generate later

For the first run only, generate these minimal files locally in private output paths:

- private validation case manifest and trajectory/deposition artifacts
- private hazard manifest and reducer chunks
- private map-package and pilot-GIS package manifests
- private timing sidecar and scaling summary

These artifacts are runtime outputs and must remain untracked.

## 7) Source-scenario policy consistency options

The design has two viable paths:

1. Minimal path (default planning path): keep the existing policy (`requested_release_cell_count: 10`) and treat it as a planning-side template.
   - This is valid for command generation and execution because the policy validator does not currently gate the hazard execution contract on this field.
   - It is useful as a fast check path but introduces documentation mismatch: one policy artifact says 10 requested cells while runtime inputs request 20.

2. Stricter path (recommended before balfrin execution): create a probe-local copy of `validation/policies/tschamut_public_source_scenario_policy_v1.yaml` with:
   - `requested_release_cell_count: 20`
   - matching synthetic `release_cells` list for 20 cells if policy is used for explicit provenance checks.
   - set the private probe manifest input-freeze policy reference to this probe-local policy copy.

Recommendation:

- Prefer the stricter path before balfrin execution to avoid ambiguity between planning documentation and execution inputs, and to preserve policy/runtime consistency when sharing probe results.

- Do not modify the tracked policy file for this probe; use a private/local policy copy and keep it uncommitted unless the team later formalizes a tracked shared 20-release-cell policy.
