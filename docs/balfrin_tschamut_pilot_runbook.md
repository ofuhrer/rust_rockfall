# Balfrin Tschamut Pilot Runbook

This runbook is a reusable operational procedure for a local Tschamut conditional
pilot on balfrin. It assumes the shared local workflow contract is already in
place (`validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml` by
default) and keeps the process read-only where possible.

## 1) Scope and prerequisites

- Scope: readiness verification, frozen command-plan execution, reducer provenance
  inspection, and scaling-summary regeneration.
- Out of scope: physics changes, annual/physical semantics, risk-map evidence,
  claim-boundary transitions, and production deployment tasks.
- Required tooling on the node:
  - `git`, `python3`, `cargo`, and `uv`.
  - Optional GIS review tooling: `qgis` (warn-only if missing).

## Minimal Demo Boundary

Use [`docs/balfrin_minimal_demo_vs_closure.md`](./balfrin_minimal_demo_vs_closure.md) as the short pointer for the demo boundary.
Minimal demo success means the contract helper and dry-run planner are bounded
and explicit; scientific closure still belongs to the post-run gate and
measured evidence.

## 2) Bring the repo and manifest to a known state

```bash
cd /path/to/rust_rockfall
git pull origin main
```

Run this from the balfrin checkout used for runs.

Set a manifest variable for reuse:

```bash
RUN_MANIFEST="${RUN_MANIFEST:-validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml}"
```

## 3) Read-only readiness check

Use the dedicated readiness gate before touching compute:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run python \
  scripts/check_balfrin_tschamut_readiness.py "$RUN_MANIFEST" --format both
```

Expected outcomes:

- Exit status `0`: required blockers are clear.
- Non-zero: missing required paths, missing write permission, or other hard blockers.
- QGIS missing is reported as a warning, not a blocker.

## 4) Validation gate

1. Validate the run contract and print the deterministic command plan:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run python \
  scripts/validate_public_real_site_conditional_pilot_run.py \
  "$RUN_MANIFEST" --print-command-plan --format json
```

2. Execute only the contract actions you explicitly want (normally both the frozen
   validation case and hazard build command from the printed plan):

- `cargo run -- validate --case <benchmark_case_path>`
- `uv run python scripts/build_hazard_layers.py ...`

Use the exact arguments from the printed plan so they stay consistent with the
locked manifest.

3. Persist the generated pilot manifests and evidence in ignored paths under
`validation/private/...` and `hazard/results/...` as configured by the manifest.

## 5) Reducer provenance inspection

After a hazard run, verify reducer provenance artifacts are coherent:

```bash
ls -1 hazard/results/tschamut_public_pilot/gate_v1/chunks/*_manifest.json \
  hazard/results/tschamut_public_pilot/gate_v1/chunks/*_state.json
```

Check manifest fields that indicate execution provenance:

- `status`
- `completion_state`
- `row_count`
- `rows_written`
- `output_bytes`
- `execution_attempt`
- `merge_group_id`

Expected behavior from this runbook:

- Manifest lifecycle provenance is populated and deterministic for completed chunks.
- State files are allowed to be accumulator-only artifacts unless the implementation
  semantics explicitly define lifecycle fields there.
- Keep this comparison stable across reruns for equivalent inputs.

## 6) Regenerate scaling summary

Use the same run artifacts for current output-budget and bottleneck evidence:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/summarize_pilot_scaling.py \
  --validation-manifest validation/private/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_manifest.json \
  --hazard-manifest hazard/results/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_manifest.json \
  --gis-package-manifest hazard/results/tschamut_public_pilot/gate_v1/tschamut_public_conditional_gate_v1_pilot_gis_package_manifest.json \
  --validation-time-file validation/private/tschamut_public_pilot/gate_v1/validation_gate_time.txt \
  --hazard-time-file hazard/results/tschamut_public_pilot/gate_v1/hazard_gate_time.txt \
  --output-json hazard/results/tschamut_public_pilot/gate_v1/tschamut_public_conditional_gate_v1_scaling_summary.json \
  --output-md docs/tschamut_public_pilot_scaling_review.md
```

Then review:

- staging and output-byte totals,
- bottleneck classification,
- merge order/merge-state coherence.

## 7) Clean balfrin CSV-grid suppression evidence (conditional-only)

The clean `main` benchmark on balfrin was run with identical Tschamut gate_v1
inputs, identical reducer worker count (`--reducer-workers 2`), and
`--conditional-curve-export summary-only` for both modes:

- `--grid-csv-export full`
- `--grid-csv-export none`

Recorded effect (full -> none):

- `output_bytes`: `75,046,369` -> `15,522,667` (saves `59,523,702`, -79.3%)
- `output_write_seconds`: `5.3310` -> `2.7450` (-48.5%)
- wall time: `0:11.57` -> `0:06.54` (-43.5%)
- CSV grid disappearance: `.csv` hazard-grid files present in `full`, absent in `none`

Semantic status for this evidence:

- Conditional diagnostic scope only; no annual/physical semantics.
- No default semantic or numerical changes.
- Defaults remain unchanged (`full` remains default behavior).
- `--grid-csv-export none` is an explicit opt-in scaling mode.
- GeoTIFF (`.tif`) and ESRI ASCII (`.asc`) hazard outputs remain in `none` mode.

Recommended baseline setting for future balfrin-scale conditional pilots (until a
defaults update is explicitly approved):

```bash
--conditional-curve-export summary-only --grid-csv-export none
```

## 9) Repeat-run reproducibility rule (trajectory/reducer smoke)

Use a second identical command against the same frozen command-plan inputs as a
smoke check; this confirms deterministic reuse without requiring byte-identical
manifests.

- Confirm wall time improved (for example: `9.25s` -> `4.61s`) and chunk decisions
  show expected reuse (`reused_completed_state`) after a valid prior run.
- Confirm numerical outputs remain stable by hash/equality checks for:
  - GeoTIFF layers,
  - ESRI ASCII grids,
  - GeoJSON,
  - hazard CSV and conditional diagnostics.
- Treat small manifest/provenance metadata churn as expected for repeat runs:
  manifest/index/chunk/provenance JSON and pilot-GIS/metadata sidecars may change
  while numerical outputs remain stable.
- Required repeat-run acceptance:
  - Orchestration decisions are coherent and stable for the same inputs,
  - numerical artifact hashes are stable,
  - no required numerical output regression.
- Optional diffing workflow: copy first-run manifests before rerun if you need exact
  provenance-byte auditing.

Do not treat non-numerical manifest byte drift as a reproducibility failure on its
own in this local smoke-test context.

## 10) Balfrin clean 2x2 vs 4x4 chunk-count smoke (Tschamut conditional gate)

A clean balfrin comparison on `/users/olifu/work/rust_rockfall` (commit `23fade0`)
used commit-synchronized conditional-only inputs with:

- `--trajectory-workers 2 --reducer-workers 2`
- `--trajectory-workers 4 --reducer-workers 4`
- `--conditional-curve-export summary-only`
- `--grid-csv-export none`
- `--no-plots`

Orchestrated path for each run before execution:

- remove only: `hazard/results/tschamut_public_pilot/gate_v1/chunks`
- remove only: `hazard/results/tschamut_public_pilot/gate_v1/trajectory_chunks`

Observed clean evidence (sidecars captured with `/usr/bin/time`):

- `2x2`: wall time `9.05s`, `total_wall_seconds 8.2485`,
  `output_write_seconds 2.8636`, `output_bytes 15,579,398`, `output_file_count 46`
- `4x4`: wall time `9.77s`, `total_wall_seconds 9.2953`,
  `output_write_seconds 3.1814`, `output_bytes 15,614,702`, `output_file_count 50`

Observed orchestration behavior:

- chunk IDs are deterministic (`...__chunk_0000..`),
- trajectory and reducer lineage references remain coherent,
- both runs were fresh and show `executed` chunk decisions,
- no stale/mixed/orphaned orchestration anomalies were reported by the manifests,
- output format set (`esri_ascii_grid` + `geotiff`) remained stable.

Interpretation for this small gate workload:

- `4x4` was slower and wrote more output files than `2x2`.
- Recommend continuing with `--trajectory-workers 2 --reducer-workers 2` for this
  small Tschamut gate conditional workflow.

This is conditional-only scaling evidence on balfrin; it does not imply operational
readiness, larger-gate extrapolation, or annual/physical-semantic behavior.

## 8) Do not commit generated artifacts

Do not commit ignored generated outputs from pilots, including:

- `validation/private/tschamut_public_pilot/...`
- `hazard/results/tschamut_public_pilot/...`
- timing sidecars (`validation_gate_time.txt`, `hazard_gate_time.txt`)
- generated scaling JSON/Markdown for local runs, unless the file is explicitly meant
  to be a tracked evidence document.

Commit only intentionally curated docs, tests, scripts, and schemas.
