# Hazard Output Profile Contract (Conditional Hazard Runs)

Status: current output-control contract for `scripts/build_hazard_layers.py`.
This document defines profile behavior only. It does not add or change execution
logic.

Goal:

- keep outputs deterministic and traceable,
- make scalable runs explicit without changing defaults,
- separate debug depth from scalable/reproducible operation.

## Current control surface review

- `--conditional-curve-export` (`full` | `summary-only`, default: `full`)
  - governs whether the per-cell conditional curve table
    `<prefix>_conditional_intensity_exceedance_curves.csv` is written.
- `--grid-csv-export` (`full` | `none`, default: `full`)
  - controls hazard-grid CSV output (`<layer>.csv`) volume.
- `--export-geotiff` (flag)
  - enables GeoTIFF raster export (`<layer>.tif`) for available raster layers.
- `--pilot-gis-package` (flag + `--pilot-gis-package-manifest-json`)
  - emits a diagnostic package manifest linking GeoTIFF/CSV/ASCII/metadata artifacts
    for QGIS review workflows.
  - requires GeoTIFF export.
- trajectory/event directories:
  - `--trajectory`, `--ensemble-trajectories-dir`,
    `--deposition`, `--impact-events`, `--ensemble-impact-events-dir`,
    `--impact-events-parquet`
  - define input corpus and thus output completeness, not output format alone.
- chunk manifests:
  - reducer chunks (`chunks/*_manifest.json`, `chunks/*_state.json`)
  - trajectory-generation chunks (`trajectory_chunks/*_manifest.json`,
    `trajectory_chunks/*_state.json`)
  - execution-index and merge-state sidecars
  - are enabled by `--trajectory-workers` and `--reducer-workers` values > `1`,
    but chunk-level provenance is also present in execution contracts when runs are
    deterministic-local restart-safe.

## Profile definitions

### 1) `full_debug`

Use case:
- local debugging, manual inspection, regression fixtures, and when full traceability
  is required.

Included outputs:
- hazard raster outputs:
  - CSV-grid layer files,
  - ESRI ASCII layer files,
  - GeoTIFF (if enabled),
  - conditional curve CSV table,
  - deposition points GeoJSON,
  - metadata JSON,
  - index HTML and PNGs unless `--no-plots` is set.
- all generated trajectory/impact inputs supplied are processed and reflected in
  hazards.
- full reducer and trajectory chunk sidecars when chunk workers are enabled.

Excluded outputs:
- none by profile definition.

Compatibility risks:
- high output bytes and file counts (especially per-cell curve table + grid CSV),
  can overwhelm file-system metadata and slow local chunk orchestration.

Recommended balfrin setting:
- `--conditional-curve-export full`
- `--grid-csv-export full`
- `--no-plots` (unless explicit diagnostics are needed)
- this remains the default behavior in existing commands and should be used
  intentionally for small runs.

### 2) `scalable_conditional` (recommended starting point for balfrin pilots)

Use case:
- conditional Swiss-scale pilot production and performance-sensitive runs
  where output-size is a first-order constraint.

Included outputs:
- ESRI ASCII raster layers (always produced in current workflow),
- GeoTIFF raster layers when `--export-geotiff` is enabled,
- deposition points GeoJSON,
- metadata JSON,
- no curve table writes by profile intent (`summary-only` mode),
- reducer/trajectory chunk manifests when workers are enabled,
- standard core manifest and provenance fields.

Excluded outputs:
- per-layer hazard CSV-grid (`<layer>.csv`) files via `--grid-csv-export none`,
- conditional curve CSV table via `--conditional-curve-export summary-only`.

Expected scaling behavior:
- lower output bytes and reduced write wall time versus `full_debug`,
- manifest and sidecar count remains, but numeric reducer work is unchanged for the same
  inputs.

Compatibility risks:
- downstream consumers expecting CSV grid or full per-cell curve tables lose direct
  access unless they rerun in a debug profile.
- existing analysis scripts that read only CSV-grid or full curve CSV must be
  updated or fed from archived full-debug outputs.

Recommended balfrin setting:
- `--conditional-curve-export summary-only`
- `--grid-csv-export none`
- `--export-geotiff` (keep raster parity where required)
- `--no-plots`
- explicit workers from validated pilot pattern.

### 3) `provenance_audit`

Use case:
- failure review, replay validation, cross-run diffing, and manifest contract
  audits.

Included outputs:
- all outputs from `scalable_conditional`,
- all chunk/chunk-state manifests and execution-index artifacts,
- `--pilot-gis-package` manifest (when `--export-geotiff` is enabled),
- optional `--pilot-gis-qa-status`/`--pilot-gis-qa-note` metadata.

Excluded outputs:
- by this profile definition, no mandatory suppression of raster data.
- can still optionally suppress curve/CSV-grid independently via:
  - `--conditional-curve-export summary-only`
  - `--grid-csv-export none`

Expected scaling behavior:
- higher non-hazard metadata volume than `scalable_conditional`,
- useful for deterministic repeat-run investigations and restart correctness.

Compatibility risks:
- larger sidecar fan-out and more JSON scanning in post-processing scripts.
- does not by itself reduce computational cost in simulation/reducer phases.

Recommended balfrin setting:
- use as needed for audits, then keep runbook-safe profiles for recurring runs.
- minimum audit command family:
  - chunk workers > 1,
  - `--conditional-curve-export summary-only`,
  - `--grid-csv-export none` (if not doing full forensics),
  - no visual plots.

## Command-Plan Policy States

The Balfrin handoff helpers now classify command-plan output intent with the
shared `scripts/lib/output_profile_policy.py` policy states:

- `scalable_default`
  - summary-only conditional curves,
  - `--grid-csv-export none`,
  - `--no-plots`.
- `explicit_heavy_debug`
  - heavier output controls are present,
  - the caller has supplied an explicit override for that heavier profile.
- `blocked_unscalable_default`
  - heavier output controls are present without an explicit override,
  - this is the fail-closed state for default multi-zone and Balfrin plans.

Generated AOI and Balfrin command plans also run the shared
`scripts/lib/command_plan_output_profile_validator.py` gate. For scalable
hazard-layer command entries the gate fails closed when it detects full grid
CSV output, full conditional-curve output, missing reduced-output flags,
worker/chunk sidecar counts above the bounded command-plan default, or missing
rebuildability inputs such as diagnostics, trajectory/deposition, and impact
event artifacts. Tiny smoke fixtures can opt into fixture-safe output
diagnostics explicitly; that exception is not used for scalable AOI or Balfrin
plans.

Balfrin handoff contract:

- The current target-gate profile in `validation/pilot_runs/tschamut_public_output_budget_reducer_gate_v1.yaml`
  remains `blocked_unscalable_default` until the recorded grid CSV mode is
  explicitly suppressed.
- The follow-up multi-zone recommendation uses `scalable_default` with
  `--conditional-curve-export summary-only`, `--grid-csv-export none`, and
  `--no-plots`.
- The helpers surface these states in both machine-readable command-plan JSON
  and the text reports written alongside the scratch-root package.

Multi-zone output-budget acceptance is now separate from output-profile
classification. The handoff package records
`output_budget_acceptance_thresholds` and
`output_budget_acceptance_validation` so a `scalable_default` smallest-run shape
still must pass explicit manifest, file-count, sidecar, reducer-chunk,
replay-family, and package-hash limits before the authorization preflight can
treat the reducer budget as ready. The preflight also exposes
`--validation-mode budget-thresholds` to run that budget validator without
turning missing authorization or Balfrin access state into the reported budget
failure.

## Profile classification clarified (Tschamut gate)

The same underlying Tschamut gate workload can be represented under multiple profiles:

- Committed command plan in `validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml`
  currently classifies as `full_debug` because it uses:
  - `--conditional-curve-export full`
  - `--grid-csv-export full`
  - `--no-plots`
- A balfrin-audited command that adds scalability controls **and** audit metadata
  (for example `--pilot-gis-package` and manifest-sidecar inputs) classifies as
  `provenance_audit`.
- A minimal scalable command with:
  - `--conditional-curve-export summary-only`
  - `--grid-csv-export none`
  - `--no-plots`
  and without additional provenance/package controls classifies as `scalable_conditional`.

Interpretation rule:
- `provenance_audit` is not a failure; it is a stronger output contract.
- It is compatible with scalable runtime behavior and is used when deterministic
  replay/audit artifacts are needed in the same run.

## Recommended default mapping (current)

- Keep existing default behavior (compatible with historical expectations):
  - `--conditional-curve-export full`
  - `--grid-csv-export full`
  - `--reducer-workers 1`
  - `--trajectory-workers 1`
  - no `--pilot-gis-package`.
- Use explicit profile intent in runbooks rather than changing this default behavior.

## Recommended practical balfrin command templates

### Balfrin scalable profile

```bash
python3 scripts/build_hazard_layers.py \
  --case <run-case.yaml> \
  --output-dir <run/output/dir> \
  --cell-size 5 \
  --conditional-curve-export summary-only \
  --grid-csv-export none \
  --export-geotiff \
  --trajectory-workers 2 \
  --reducer-workers 2 \
  --no-plots
```

### Provenance audit profile

```bash
python3 scripts/build_hazard_layers.py \
  --case <run-case.yaml> \
  --output-dir <run/output/dir> \
  --cell-size 5 \
  --conditional-curve-export summary-only \
  --grid-csv-export none \
  --export-geotiff \
  --trajectory-workers 2 \
  --reducer-workers 2 \
  --pilot-gis-package \
  --pilot-gis-qa-status not-run \
  --no-plots
```

## Contract defaults for trajectory/event directories

- Full-debug and provenance-audit profiles still allow large trajectory/event sources:
  - full CSV inputs (`--trajectory` / `--ensemble-trajectories-dir`),
  - full deposition tables,
  - full impact-event CSV/Parquet inputs.
- Scalable profile does not change source ingestion policy; it controls only output
  emission and metadata expansion.
- Reproducibility and replay correctness depend on stable pathing, naming, and
  signatures in chunk-sidecar contracts. Current manifests and signatures already
  represent local replay safety for compatible restart semantics.

## Checker usage

Use the read-only profile checker to verify command intent for hazard profiles.

- From an explicit command:

```bash
python3 scripts/check_hazard_output_profile.py \
  -- python3 scripts/build_hazard_layers.py \
  --case validation/private/tschamut_public_pilot/gate_v1/tschamut_public_conditional_gate_case.yaml \
  --output-dir hazard/results/tschamut_public_pilot/gate_v1 \
  --conditional-curve-export summary-only \
  --grid-csv-export none \
  --no-plots \
  --reducer-workers 2
```

- From a command-plan JSON:

```bash
python3 scripts/check_hazard_output_profile.py \
  --command-plan validation/results/command_plans/tschamut_public_conditional_gate.json \
  --format json
```

Output fields:

- `profile`: one of `full_debug`, `scalable_conditional`, `provenance_audit`,
  `custom_or_mixed`.
- `matched_controls`: profile controls detected from the command.
- `missing_controls`: required controls that are absent for the detected profile.
- `missing_scalable_controls`: direct required controls for `scalable_conditional`.
- `unsupported_or_ambiguous_controls`: unsupported values or mixed profile signals.
- `recommendations`: optional profile-improvement suggestions.

## Future implementation note (not implemented yet)

Optional flag to simplify user intent:

```
--output-profile {full_debug,scalable_conditional,provenance_audit}
```

This would map to the control combinations in this contract without changing
defaults and without altering existing legacy behavior. This remains a future CLI
ergonomic improvement, intentionally not implemented yet.

## Implementation Split Note

`scripts/build_hazard_layers.py` now delegates stable file-writing, manifest-entry,
and HTML-report helpers to small focused modules. The next safe split target is
the remaining raster writer family (`write_layers`, ASCII grid, GeoTIFF, and
curve-table emission), but that should stay behavior-preserving and fixture-backed:
do not change reducer math, probability normalization, output-profile defaults,
or GIS/COG claim status as part of that extraction.

## Scope notes

- This contract applies to conditional research hazard outputs.
- It does not include annual frequency, physical probability, return-period,
  risk-map, or operational products.
- `--pilot-gis-package` is a diagnostic package contract and does not imply QA
  completion or operational suitability.
