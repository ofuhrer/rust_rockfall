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

The Balfrin SSH entry point currently exposes `sbatch`, so the retry path for
the canonical demo is to hop into `balfrin` first and then reuse the same run
identifiers from that shell.

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
RUN_ROOT="${RUN_ROOT:-${SCRATCH:-/scratch}/rust_rockfall/probes/balfrin-demo/${RUN_ID:-$(date -u +%Y%m%d_%H%M%S_utc)}}"
RUN_ID="${RUN_ID:-$(basename "$RUN_ROOT")}"
```

The exact command sequence below is the operational demo procedure. Keep the
same `RUN_ROOT` and `RUN_ID` for submit, stop, resume, collect, and cleanup so
the run stays reproducible.

### 2.1 Preflight

```bash
PYENV_VERSION=system uv run python scripts/check_balfrin_tschamut_readiness.py \
  "$RUN_MANIFEST" --format both
```

### 2.2 Generate-only

```bash
PYENV_VERSION=system uv run python scripts/submit_balfrin_probe.py \
  "$RUN_MANIFEST" \
  --generate-only \
  --run-root "$RUN_ROOT" \
  --run-id "$RUN_ID" \
  --partition postproc \
  --time 00:30:00 \
  --nodes 1 \
  --ntasks 1 \
  --cpus-per-task 16
```

Use `--generate-only` when you want the frozen command plan, SBATCH script, and
submission package without actually starting SLURM.

### 2.3 Submit

```bash
PYENV_VERSION=system uv run python scripts/submit_balfrin_probe.py \
  "$RUN_MANIFEST" \
  --submit \
  --run-root "$RUN_ROOT" \
  --run-id "$RUN_ID" \
  --partition postproc \
  --time 00:30:00 \
  --nodes 1 \
  --ntasks 1 \
  --cpus-per-task 16
```

Record the `submitted_job_id` from the helper output. It is the value used for
stop and resume handoff.

If `sbatch` is not exposed in the current shell, open the Balfrin SSH entry
point first and rerun the exact same submit command from that context:

```bash
ssh -o BatchMode=yes -o ConnectTimeout=8 balfrin
```

Keep the same `RUN_ROOT` and `RUN_ID` when moving between shells. Do not change
either value during the retry.

### 2.4 Stop

```bash
JOB_ID="<submitted_job_id>"
scancel "${JOB_ID}"
```

Stop only the Balfrin probe job you submitted. Do not cancel unrelated work.

### 2.5 Resume

```bash
PYENV_VERSION=system uv run python scripts/submit_balfrin_probe.py \
  "$RUN_MANIFEST" \
  --submit \
  --run-root "$RUN_ROOT" \
  --run-id "$RUN_ID" \
  --partition postproc \
  --time 00:30:00 \
  --nodes 1 \
  --ntasks 1 \
  --cpus-per-task 16
```

Resume means rerun the same helper with the same `RUN_ROOT` and `RUN_ID` after
the stopped job has been cleared. Do not change the command plan or scratch
layout when resuming. If the local shell cannot reach `sbatch`, resume from
the Balfrin SSH context instead of changing the identifiers.

### 2.6 Collect

```bash
PYENV_VERSION=system uv run python scripts/submit_balfrin_probe.py \
  --collect \
  --run-root "$RUN_ROOT"

PYENV_VERSION=system uv run python scripts/collect_balfrin_probe_metrics.py \
  --run-root "$RUN_ROOT"
```

The submission helper and the collector should agree on the same run root. If
they do not, stop and inspect the generated package before proceeding.

### 2.7 Verify

```bash
PYENV_VERSION=system uv run python scripts/summarize_balfrin_post_run_interpretation_gate.py \
  --format json \
  --evidence-json "${RUN_ROOT}/balfrin_post_run_evidence.json"

PYENV_VERSION=system uv run python scripts/summarize_balfrin_failure_taxonomy.py \
  --format json \
  --evidence-json "${RUN_ROOT}/balfrin_post_run_evidence.json" \
  --json-output "${RUN_ROOT}/balfrin_failure_taxonomy_v1.json"
```

Use the post-run evidence bundle only after the collection step has produced the
measured outputs that the gate expects. Keep the gate read-only.
The taxonomy helper is read-only too; it labels operational recovery cases and
scope-limited scientific states without changing the interpretation criteria.

### 2.8 Cleanup

```bash
rm -rf "${RUN_ROOT}"
```

Cleanup applies only after you have copied the needed evidence to a durable
location. Keep scratch-only probe roots out of the repository.

### 2.9 Failure handoff

If the run fails or needs escalation, capture the run package, summary, logs,
and context as a single scratch archive before handing it off:

```bash
tar -C "${RUN_ROOT}" -czf "/tmp/${RUN_ID}_balfrin_probe_handoff.tgz" \
  logs \
  command_plan.json \
  probe.sbatch \
  balfrin_submission_package.json \
  balfrin_submission_package.md \
  balfrin_probe_summary.json \
  balfrin_failure_taxonomy_v1.json \
  balfrin_probe_context.txt \
  balfrin_probe_full_time.txt \
  balfrin_hazard_stage_time.txt
```

The handoff archive should include the submission package, command plan, logs,
and timing sidecars, not tracked outputs copied from elsewhere.

### 2.10 Do not commit generated artifacts

Do not commit any files or directories under these generated output roots:

- `$RUN_ROOT`
- `$RUN_ROOT/logs`
- `validation/private/tschamut_public_pilot/...`
- `hazard/results/tschamut_public_pilot/...`

Do not commit these generated artifacts if they appear in a run root:

- `command_plan.json`
- `probe.sbatch`
- `balfrin_submission_package.json`
- `balfrin_submission_package.md`
- `balfrin_probe_summary.json`
- `balfrin_failure_taxonomy_v1.json`
- `balfrin_probe_context.txt`
- `balfrin_probe_full_time.txt`
- `balfrin_hazard_stage_time.txt`

For deterministic failure-class recovery paths keyed to the current Balfrin
demo scope, see [`docs/balfrin_failure_recovery_playbook.md`](./balfrin_failure_recovery_playbook.md).

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
