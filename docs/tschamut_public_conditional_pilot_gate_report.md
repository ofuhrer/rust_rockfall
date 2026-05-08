# Tschamut Public Conditional Pilot Gate Report

Status: no-go gate report for the selected public Tschamut conditional pilot.
This report does not record a completed trajectory run, conditional curve
output, GIS review package, operational hazard approval, physical probability,
annual frequency, return-period product, or risk-map result.

## Classification

- Pilot id: `tschamut_public_pilot`
- Run id: `tschamut_public_conditional_gate_v1`
- Current classification: `no-go`
- Operational status: research diagnostic
- Validation maturity target: V1 preparation fixture
- Run-freeze file:
  `validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml`

## Frozen Inputs

The selected gate freezes the share-safe upstream inputs that are available in
git:

- geodata manifest:
  `data/processed/swisstopo/tschamut_public_pilot_manifest.yaml`;
- source-zone/block-scenario policy:
  `validation/policies/tschamut_public_source_scenario_policy_v1.yaml`;
- source zone: `tschamut_public_lps_release_bbox`;
- release sampling: ten deterministic release cells from the policy;
- block scenarios: three representative conditional block scenarios from the
  policy;
- physics defaults: unchanged `translational_v0`, no soil-interaction model,
  no roughness model;
- random seed: `34014`;
- conditional thresholds: kinetic energy `1000` and `10000` J; jump height `1`
  and `2` m;
- explicit grid: EPSG:2056/LN02 crop extent from the selected manifest,
  300 by 304 cells at 2 m.

## Gate Evidence

The gate is no-go because the selected processed DEM and terrain metadata are
ignored local products and are absent from a clean checkout:

- `data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_swissalti3d_crop.asc`;
- `data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_swissalti3d_metadata.yaml`.

This is a reproducibility/input-data blocker, not a model result. No
trajectories, hazard layers, conditional curves, GIS artifacts, runtime
measurements, memory measurements, output file counts, output byte counts, or
artifact checksums exist for this selected pilot gate yet.

## Executable Checks

The run-freeze validator accepts the no-go state and can print a command plan
for the checked pre-run steps:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run python \
  scripts/validate_public_real_site_conditional_pilot_run.py \
  validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml \
  --print-command-plan
```

The command plan validates the selected geodata manifest and source/scenario
policy, then records the DEM-sensitivity blocker in an ignored output
directory. It intentionally does not run `cargo run -- validate` or
`scripts/build_hazard_layers.py` until the processed DEM blocker is resolved.

## Recovery Path

To move this gate from no-go to an actual small conditional pilot run, first
prepare the ignored public geodata package locally:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run python \
  scripts/prepare_tschamut_public_benchmark.py \
  --output-root data/processed/swisstopo/tschamut_public_pilot \
  --padding-m 250 \
  --force
```

Then rerun the selected-domain DEM sensitivity command without
`--allow-missing-source-dem`, generate the frozen benchmark case and sidecars,
and update the run-freeze evidence only after the small gate run and hazard
post-processing complete.

## Claim Boundary

Allowed current claims:

- the selected public geodata manifest and source/scenario policy are frozen
  for a future conditional diagnostic gate run;
- the current gate is blocked before simulation because required ignored local
  processed DEM inputs are missing;
- future outputs from this gate, once run, must be unweighted diagnostics,
  sampling-weighted conditional products, or conditional intensity-exceedance
  products.

Unsupported current claims:

- annual frequency;
- return-period products;
- physical probability;
- risk-map meaning;
- operational or validated hazard-map status.
