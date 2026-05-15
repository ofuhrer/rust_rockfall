# Tschamut Public Pilot Scaling Review

Status: local manifest-based scaling and output-volume evidence.
This is a research diagnostic performance note, not validation evidence,
not an operational hazard-map claim, and not an annual or physical
probability product.

## Commands

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/summarize_pilot_scaling.py \
  --output-json hazard/results/tschamut_public_pilot/gate_v1/tschamut_public_conditional_gate_v1_scaling_summary.json \
  --output-md docs/tschamut_public_pilot_scaling_review.md
```

## Observed Local Metrics

| Stage | Wall seconds | Output write seconds | Rows read/written | Files | Bytes |
| --- | ---: | ---: | ---: | ---: | ---: |
| validation | 3.750 | 2.535 | 81845 | 125 | 34562779 |
| hazard | 12.172 | 8.687 | 81710 | 58 | 192717542 |

Local ignored output tree totals:

- Files: `188`
- Bytes: `267522045`

External `/usr/bin/time` sidecars:

- Validation: `missing`
- Hazard: `missing`

## Reducer Evidence

- Mode: `chunked_local_threads`
- Worker count: `2`
- Chunk count: `2`
- Merge order: `sorted_chunk_id`
- Merge-order independent: `True`

## Bottleneck Decision

- Status: `no_default_change_recommended`
- Primary bottleneck: `hazard_conditional_curve_output_volume`
- Largest hazard output kind: `conditional_intensity_exceedance_curves`
- Largest hazard output bytes: `117670336`
- Next action: optimize or gate conditional-curve table and raster output modes before increasing ensemble size.

Do not add MPI, GPU, SLURM orchestration, annual frequency, physical
probability, or ensemble-size increases from this evidence alone.

## Claim Boundary

Current products remain conditional intensity-exceedance and
sampling-weighted conditional diagnostics. The scaling summary does not
introduce exposure, vulnerability, consequence, expected loss, return
period, annual frequency, physical probability, or operational map
semantics.

## Balfrin CSV-grid suppression evidence (clean main, conditional-only)

A clean balfrin `main` benchmark was executed on identical Tschamut
gate_v1 inputs with:

- `--conditional-curve-export summary-only`
- `--reducer-workers 2`
- `--grid-csv-export` set to `full` and `none`.

| Mode | Output bytes | Output-write seconds | Wall time | Largest output kind |
| --- | ---: | ---: | ---: | --- |
| `full` | 75,046,369 | 5.3310 | 0:11.57 | `csv_grid` (59,518,059 bytes) |
| `none` | 15,522,667 | 2.7450 | 0:06.54 | `geotiff` (11,678,624 bytes) |

Change from `full` -> `none`:

- `csv_grid` output removed (no `.csv` hazard-grid files in `none`)
- output bytes: `-59,523,702` (-79.3%)
- output-write seconds: `-2.5859` (-48.5%)
- wall time: `-5.03s` (-43.5%)

Remaining bottleneck in `none` mode:

- geotiff + esri_ascii_grid write path, plus non-serialization hazard-stage cost.

Operational scope for this evidence:

- conditional hazard diagnostics only
- no annual/physical semantics
- no default or validator semantic change
- `--grid-csv-export none` is an explicit opt-in scaling mode.

Do not add MPI, GPU, SLURM orchestration, annual frequency, physical probability,
or ensemble-size increases from this evidence alone.

## Local chunk-count scaling smoke (not balfrin evidence)

Location: `/Users/fuhrer/Desktop/rust_rockfall` (laptop/local checkout), not
`/users/olifu/work/rust_rockfall`.

Chunk-count runs (same fixed workload, same outputs policy):

| Trajectory/Reducer Workers | Trajectory Chunks | Reducer Chunks | Wall time (s) | Output write seconds | Output bytes | Output files |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `2/2` | 2 | 2 | `21.20` | `6.0881` | `15,582,152` | `46` |
| `4/4` | 4 | 4 | `27.61` | `9.5276` | `15,617,393` | `50` |
| `8/8` | 8 | 8 | `32.08` | `8.3838` | `15,687,566` | `58` |

Finding:

- Small Tschamut gate_v1 workload: increasing chunk count from 2 to 4/8 added chunk
  management overhead and did not improve runtime.
- Current locally recommended small-gate mode remains:
  `--trajectory-workers 2 --reducer-workers 2 --conditional-curve-export summary-only --grid-csv-export none`.
- Confirmed clean balfrin-scale chunk-count evidence still requires runs from
  `/users/olifu/work/rust_rockfall`.

## Clean balfrin chunk-count scaling smoke (2×2 vs 4×4, commit `23fade0`)

Clean evidence from `/users/olifu/work/rust_rockfall` (clean `main`, same
conditional-only command family as this review) compared:

- `2×2`: `--trajectory-workers 2 --reducer-workers 2`
- `4×4`: `--trajectory-workers 4 --reducer-workers 4`

with `--conditional-curve-export summary-only`, `--grid-csv-export none`, `--no-plots`.

| Trajectory/Reducer Workers | Trajectory Chunks | Reducer Chunks | Wall time (s) | `total_wall_seconds` | `output_write_seconds` | `output_bytes` | `output_file_count` |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `2×2` | 2 | 2 | `9.05` | `8.2485` | `2.8636` | `15,579,398` | `46` |
| `4×4` | 4 | 4 | `9.77` | `9.2953` | `3.1814` | `15,614,702` | `50` |

Orchestration check summary from the two runs:

- chunk IDs were deterministic,
- trajectory/reducer lineage references were coherent,
- all chunks were `executed` in these fresh clean runs,
- no stale/mixed/orphaned decision anomalies were reported.

Interpretation:

- for the current small Tschamut gate_v1 conditional workload, `4×4` was slower than
  `2×2`;
- recommended current small-gate mode remains:
  `--trajectory-workers 2 --reducer-workers 2` (with the same output policy).

Evidence scope:

- conditional-only scaling evidence only,
- no annual/physical semantics,
- no operational hazard-map readiness claim,
- this is not a generic scalability law for larger Swiss-scale runs.

## Repeat-run drift classification (same inputs, same command plan)

- Repeat run completed with stable command plan, `trajectory_workers=2`,
  `reducer_workers=2`, `--conditional-curve-export summary-only`,
  `--grid-csv-export none`.
- Wall time improved on reuse (`~9.25s` -> `~4.61s`) with stable
  `trajectory_execution_plan_id`.
- Numeric outputs remained hash-stable (GeoTIFF, ESRI ASCII, GeoJSON, hazard CSV/
  conditional diagnostics).
- Observed drift was limited to provenance/metadata artifacts such as manifests,
  execution plans/indexes, chunk manifests, and pilot GIS/metadata sidecars.
- Acceptable repeat-run rule:
  manifest byte identity is not required; numerical hazard/product hashes should be
  stable; orchestration decisions should be coherent; snapshot first/repeat
  manifests before rerun when provenance diffing is required.

## 20-release-cell balfrin probe evidence (tracked probe, commit `d16d245`)

Tracked probe executed on clean balfrin checkout (`/users/olifu/work/rust_rockfall`) under:

- `validation/probes/tschamut_mid_scale_20_release_cell_v1/`
- `--trajectory-workers 2`
- `--reducer-workers 2`
- `--conditional-curve-export summary-only`
- `--grid-csv-export none`
- `--export-geotiff`
- `--no-plots`

Run evidence:

| Run | `wall_seconds` | `total_wall_seconds` | `output_bytes` | `output_file_count` | `output_write_seconds` | Chunk outcome |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| First run | `7.743111` | `6.88505400205031` | `15,602,497` | `46` | `2.7461103320820257` | `executed` |
| Repeat run | `4.770220` | `4.339605016983114` | `15,602,620` | `46` | `2.796586749027483` | `reused_completed_state` |
| Second repeat (drift audit) | `4.721994` | `4.296635876991786` | `15,602,596` | `46` | `2.7926949579268694` | `reused_completed_state` |

Drift classification for first-vs-second-repeat:

- Geospatial/diagnostic products stable:
  - GeoTIFF `16/16` unchanged
  - ESRI ASCII `16/16` unchanged
  - GeoJSON `1/1` unchanged
- `json manifests/indexes/plans` changed (`10/16` JSON artifacts), expected from
  provenance and timing metadata updates.
- `plan_id` values remained stable.
- chunk decisions stayed coherent and stable (`reused_completed_state`, no stale/orphan/missing-state anomalies).
- state/provenance reuse remained valid; no decision-order anomalies.

Interpretation:

- Numerical outputs were stable; byte-level output-budget differences were small and confined to provenance/metadata layers.
- This supports a valid conditional-only repeatability rule for this probe scale:
  manifest bytes need not be byte-identical, but numerical hazard products should remain stable.

Limitations:

- conditional-only evidence only
- no annual/physical semantics
- not operational evidence
- not Swiss-scale extrapolation

Recommendation:

- 20-release-cell probe passed.
- replay/reuse behavior is stable.
- next balfrin scaling step should vary one dimension only, preferably trajectory count per release cell or grid size (not chunk count).

## 20-release-cell × 12 trajectories balfrin probe evidence (tracked probe, commit `d16d245`)

Tracked probe definition:

- `validation/probes/tschamut_mid_scale_20_release_cell_12traj_v1/`
- same output profile as 20×6:
  - `--trajectory-workers 2`
  - `--reducer-workers 2`
  - `--conditional-curve-export summary-only`
  - `--grid-csv-export none`
  - `--export-geotiff`
  - `--no-plots`

Profile check:

- `python3 scripts/check_hazard_output_profile.py --command-plan /tmp/..._12traj.json`
  → `Detected profile: provenance_audit`

Validation checks run:

- command plan generation succeeded from tracked probe manifest and policy.
- command plan command controls include all intended flags above.

Observed execution summary:

| Run | `wall_seconds` | `total_wall_seconds` | `output_bytes` | `output_file_count` | `output_write_seconds` | `trajectory_count` | `trajectory chunks` | `reducer chunks` |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| First run | `12.279972` | `11.125986575032584` | `15,691,724` | `46` | `3.267310244962573` | `121` | `executed` | `executed` |
| Repeat run | `13.748173`* | `5.14157305995` | `15,692,692` | `46` | `2.883542826` | `121` | `reused_completed_state` | `reused_completed_state` |

* `wall_seconds` from sidecar is full command-sequence timing and is noisy; prefer
`total_wall_seconds` for model comparability.

Scaling interpretation vs 20×6:

- output_bytes changed only slightly (`+89,227`) while trajectory count doubled (60→121), indicating existing output gating still dominates outputs.
- first-run wall time increased materially with trajectories doubled.
- repeat wall time dropped due reuse (`executed` → `reused_completed_state`), confirming deterministic local resumability.
- this pattern implies the near-term bottleneck is trajectory/reducer processing overhead, not output volume, at this workload slice.

Stability classification:

- probe reused completed trajectory and reducer chunks in repeat.
- plan IDs remained stable.
- no stale, orphan, or missing-state anomalies were observed.
- output numeric payloads remained stable in prior 20×12 probes; provenance/protocol drift remains acceptable under the same rule used for previous balfrin repeat checks.

## 420×450 grid-size balfrin probe evidence (tracked probe)

Tracked grid-size probe definition:

- `validation/probes/tschamut_mid_scale_grid_probe_420x450_v1/`
- base workload:
  - `release-zone-count = 20`
  - `trajectories per release cell = 12`
  - grid `420 x 450` (from `304 x 300`)
  - `trajectory-workers = 2`
  - `reducer-workers = 2`
- output controls:
  - `--conditional-curve-export summary-only`
  - `--grid-csv-export none`
  - `--trajectory-workers 2`
  - `--reducer-workers 2`
  - `--export-geotiff`
  - `--no-plots`

Observed first-run summary:

| Metric | Value |
| --- | ---: |
| command-sequence wall time (`/usr/bin/time` real) | `34.60s` |
| `total_wall_seconds` | `15.839314937009476` |
| `output_bytes` | `32,124,792` |
| `output_file_count` | `46` |
| `output_write_seconds` | `6.502529560937546` |
| `trajectory chunks` | `2` |
| `reducer chunks` | `2` |

Output-kind split for this probe:

| Output kind | Seconds | Bytes |
| --- | ---: | ---: |
| `esri_ascii_grid` | `0.7421` | `7,583,879` |
| `geotiff` | `0.6311` | `24,197,024` |
| `json` | `0.00116` | `20,452` |
| `geojson` | `0.00166` | `53,926` |

Plan/index/merge IDs were coherent; no stale/orphan/missing-state anomalies were observed.

Comparison vs 20×12 baseline (304×300, same profile/workers):

| Metric | 20×12 baseline (`304×300`) | 420×450 run | Ratio / delta |
| --- | ---: | ---: | --- |
| grid cell count | `91,200` | `189,000` | `~2.07×` |
| `total_wall_seconds` | `11.125986575032584` | `15.839314937009476` | `+42.3%` |
| `output_bytes` | `15,691,724` | `32,124,792` | `+105.0%` |
| `output_file_count` | `46` | `46` | `0%` |
| `output_write_seconds` | `3.267310244962573` | `6.502529560937546` | `+99.0%` |

Interpretation:

- raster-domain outputs scale approximately with cell count; raster file counts stayed constant while raster bytes and serialization time rose near proportionally.
- with this controlled grid-size increase, raster output write/serialization became the clearer dominant pressure.

## Fresh SLURM 420×450 clean baseline evidence (submission `4289703`)

Tracking details:

- commit: `61ab9c6` (`Fix SLURM probe heredoc quote stripping`)
- manifest: `validation/probes/tschamut_mid_scale_grid_probe_420x450_v1/tschamut_public_conditional_mid_scale_grid_probe_420x450_12traj_pilot_run.yaml`
- run root: `/scratch/mch/olifu/rust_rockfall/probes/slurm_smoke_420x450/fresh_baseline_ee8c4eb`
- job ID: `4289703`
- partition: `postproc`
- timing sidecars:
  - `balfrin_probe_full_time.txt = 23.446129538002424`
  - `balfrin_hazard_stage_time.txt = 15.635101707070135`

Fresh-run summary:

- `total_wall_seconds = 14.95406103390269`
- `output_bytes = 32,124,738`
- `output_file_count = 46`
- `output_write_seconds = 5.986803226056509`
- `trajectory_decision_counts = {"executed": 2}`
- `reducer_decision_counts = {"executed": 2}`
- `trajectory_plan_id = validation_tschamut_public_conditional_mid_scale_grid_probe_420x450_12traj_probe_v1__trajectory_execution_plan__75b0ef839657fa96a9fed7d6`
- `reducer_plan_id = validation_tschamut_public_conditional_mid_scale_grid_probe_420x450_12traj_probe_v1__execution_plan__b26a5e3da0a3cf72f6e550d3`
- manifest/control audit:
  - command includes all intended controls (`summary-only`, `grid-csv-export none`,
    `trajectory-workers 2`, `reducer-workers 2`, `export-geotiff`, `no-plots`)
  - no repo-path quoting warning, no fatal git warning, no `--account`, no GPU/operational partition

Important history:

- earlier first submit `4289616` completed on reused state,
- clean fresh baseline reference for this grid point is `4289703` after clearing output `chunks/` and `trajectory_chunks/` for the target probe output path.

Comparison vs earlier manual 420×450 first run (`15.839314937009476`, `32,124,792`, `46`, `6.502529560937546`):

- `total_wall_seconds`: `14.95406103390269`
- `output_bytes`: `32,124,738`
- `output_file_count`: `46`
- `output_write_seconds`: `5.986803226056509`
- close alignment; expected small timing variance and minor write timing differences.

Evidence limits for this result:

- conditional-only evidence,
- no annual/physical semantics,
- no operational hazard-map claim,
- driver still single-job local chunked execution (no array/reducer-array stage yet).

Scope note:

- no repeat/reuse validation was executed for this 420×450 probe yet.

Recommended next step:

- run one repeat/reuse check for 420×450 to confirm the same provenance/manifest drift rule applies at this grid scale.
- otherwise continue one-dimension variation and/or raster I/O strategy tests (e.g., COG/GeoTIFF trade-off exploration).

## DT-03 repeat/reuse closure for the 420×450 SLURM probe

DT-03 is now recorded in
`validation/pilot_runs/tschamut_public_slurm_probe_repeatability_v1.yaml`.
The record classifies the tracked 420×450 probe as
`pass_with_scope_limits` and the single-job SLURM driver as
`ready_for_same_scale_selected_gate_reproduction`.

Repeat jobs:

| Job | Run root | SLURM state | Trajectory chunks | Reducer chunks | Total wall seconds | Output bytes | Output files | Log audit |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | --- |
| `4318872` | `/scratch/mch/olifu/rust_rockfall/probes/slurm_smoke_420x450/dt03_repeat_420x450_20260514_235658` | `COMPLETED 0:0` | `reused_completed_state: 2` | `reused_completed_state: 2` | `10.4635` | `32,125,888` | `46` | clean |
| `4318896` | `/scratch/mch/olifu/rust_rockfall/probes/slurm_smoke_420x450/dt03_repeat2_420x450_20260514_235851` | `COMPLETED 0:0` | `reused_completed_state: 2` | `reused_completed_state: 2` | `10.4597` | `32,125,876` | `46` | clean |

Additional hash-stability check:

- compared before and after the second repeat run;
- `33/33 numeric hazard artifacts` unchanged;
- artifact families: GeoTIFF, ESRI ASCII, GeoJSON, CSV;
- total compared numeric artifact bytes: `31,831,717` before and after;
- changed artifact count: `0`.

Interpretation:

- repeat/reuse behavior is stable for the tracked 420×450 single-job probe;
- trajectory and reducer plan IDs remained stable across repeat runs;
- warning-like and error-like log-audit counts were zero for both repeat jobs;
- manifest/provenance byte identity is not required because timing and metadata
  sidecars may update between repeats;
- the driver is acceptable for DT-04 same-scale selected-gate reproduction with
  the same controls.

Scope limits:

- this is conditional-only execution evidence;
- it does not reproduce the selected Tschamut target gate itself;
- it does not authorize ensemble-size increase, SLURM arrays, MPI, GPU execution,
  annual/physical probabilities, or operational hazard-map claims.
