# Balfrin readiness checker for the Tschamut conditional pilot

This document describes a dedicated read-only readiness check used before attempting the Tschamut public conditional pilot on balfrin.

## Scope

The checker validates only execution prerequisites:

- repository location and git context (branch + commit),
- required toolchain presence (`rustc`, `cargo`, `python3`, `uv`),
- selected Tschamut geodata/metadata/input paths,
- command-plan inputs generated from the selected conditional pilot run contract,
- writable validation and hazard output locations,
- optional QGIS availability (explicitly allowed to be missing).

The checker does **not** run simulation commands and does **not** alter data.
In plain terms: it does not run simulation commands.

This check does not assess annual-frequency semantics, physical-frequency claims, risk-map claim status, or return-period outputs. Those products remain out of scope for this readiness gate.

## Selected readiness record

The selected DT-02 readiness result is recorded in
`validation/pilot_runs/tschamut_public_balfrin_readiness_v1.yaml`.
It reports the `/users/olifu/work/rust_rockfall` checkout on balfrin as
`ready_for_balfrin_target_gate` for the current Tschamut conditional pilot
readiness gate, with zero blocking checks and QGIS reported as an optional
warning.

Validate the recorded result with:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run python \
  scripts/validate_balfrin_tschamut_readiness_record.py \
  validation/pilot_runs/tschamut_public_balfrin_readiness_v1.yaml
```

The record is share-safe: it records path/status/toolchain/provenance summaries,
not raw geodata, generated hazard products, or the full checker JSON output.
It does not authorize scale-up, complete manual GIS/QGIS QA, or run the
selected hazard-map workflow.

## Usage

```bash
python3 scripts/check_balfrin_tschamut_readiness.py
```

Optional overrides:

- positional argument: path to run-manifest YAML (default `validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml`)
- `--repo-root` for synthetic checks or non-standard checkouts
- `--format text|json|both` (default `both`)

Example:

```bash
python3 scripts/check_balfrin_tschamut_readiness.py \
  --repo-root /workspace/rust_rockfall \
  --format both
```

## Interpreting output

Output is always a machine JSON blob plus a compact human-readable summary.

Non-zero exit status means the checker found at least one **required blocker**. QGIS absence is reported as warning only.

## What is checked

- `input_freeze.geodata_manifest_path` exists
- inferred processed DEM (`path`) and terrain metadata (`metadata_path`) exist in that geodata manifest
- `terrain_metadata_path`, `source_zone_metadata_path`, `scenario_table_path`, `source_scenario_policy_path` exist
- all command-plan file inputs for:
  - `validate_geodata_manifest`
  - `validate_source_scenario_policy`
  - `run_validation_gate`
  - `build_conditional_hazard_layers`
  exist
- command-plan output roots and key output locations are writable
- `validation/private/...` and `hazard/results/...` parents are writable

## Notes

- Existing validator logic is reused to parse and expand the pilot run command plan; no full run is executed.
- QGIS is optional and may be absent.
- The output remains ready to consume in CI or wrappers as a JSON artifact.
