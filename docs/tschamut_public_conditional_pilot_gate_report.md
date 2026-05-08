# Tschamut Public Conditional Pilot Gate Report

Status: reconciled local gate report for the selected public Tschamut
conditional pilot. This report records a completed small local conditional
diagnostic gate using ignored generated artifacts. It does not record
operational hazard approval, physical probability, annual frequency,
return-period products, or risk-map results.

## Classification

- Pilot id: `tschamut_public_pilot`
- Run id: `tschamut_public_conditional_gate_v1`
- Current classification: `inconclusive`
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
- physics defaults: unchanged simulator behavior, `translational_v0`, no
  soil-interaction model, opt-in `stochastic_contact_v1` roughness as recorded
  in the frozen generated local benchmark case;
- random seed: `34014`;
- gate scale: six trajectories per deterministic release cell, ten release
  cells, 60 simulated trajectories total;
- conditional thresholds: kinetic energy `1000` and `10000` J; jump height `1`
  and `2` m;
- explicit grid: EPSG:2056/LN02 crop extent from the selected manifest,
  300 by 304 cells at 2 m.

## Gate Evidence

The processed DEM and terrain metadata remain ignored local products, but they
were present for this reconciliation run:

- `data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_swissalti3d_crop.asc`;
- `data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_swissalti3d_metadata.yaml`.

The selected-domain DEM sensitivity gate completed with terrain-variant
metrics and no tuning:

- summary:
  `validation/private/tschamut_public_pilot/dem_sensitivity_gate_v1/dem_terrain_sensitivity_summary.json`;
- SHA-256:
  `85c1ba97f012167ab29f2772b5893aa84fc21cc483bd7d5c7f3f12a155701fa6`;
- status: `pass` / `completed_terrain_variant_metrics`;
- source DEM SHA-256:
  `36f3156bbc57a01536784807a09db214a46911b4df95c04af8182e420973ea8f`.

The small conditional pilot gate completed locally and produced ignored
validation and hazard artifacts:

- validation manifest:
  `validation/private/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_manifest.json`;
- hazard manifest:
  `hazard/results/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_manifest.json`;
- conditional curve table:
  `hazard/results/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_conditional_intensity_exceedance_curves.csv`;
- map-package manifest:
  `hazard/results/tschamut_public_pilot/gate_v1/tschamut_public_conditional_gate_v1_map_package_manifest.json`;
- pilot GIS package manifest:
  `hazard/results/tschamut_public_pilot/gate_v1/tschamut_public_conditional_gate_v1_pilot_gis_package_manifest.json`;
- reducer chunk manifest directory:
  `hazard/results/tschamut_public_pilot/gate_v1/chunks`.

Artifact checksums recorded in the run-freeze:

| Artifact | SHA-256 |
| --- | --- |
| Validation manifest | `f0981caae1da4d3cf5a93c9d1b0a1ae88ac28a9d067824b813e6455a9ec0bf50` |
| Hazard manifest | `6a5cc5711406d01caf2e62585368c4acedf1fc3eaaf5dd815226e9dcaca4043e` |
| Conditional curve table | `cb2d0c5636c3a177c825258acfa6aef2f215fd5ddd99e9cfea92d34256681541` |
| Map-package manifest | `27a95fb037639ac961d6b8eaa1e2de383fb0ebfa91b116b5547a83f28e9f7621` |
| Pilot GIS package manifest | `ab9bc43b1d4ae8a61724f3f951e1127064d1b841b1d74b391516016efd0b9f92` |

Runtime and output-volume evidence:

- validation manifest wall time: `4.066` s;
- hazard manifest wall time: `15.586` s;
- external `/usr/bin/time` elapsed seconds: validation `4.23`, hazard `16.41`;
- external peak RSS: validation `41572` KiB, hazard `390588` KiB;
- run-freeze peak memory record: `381.43` MiB;
- ignored output tree total: 186 files, 226,925,754 bytes;
- generated validation outputs: 125 files, 34,531,527 bytes;
- generated hazard outputs: 55 files, 192,297,963 bytes;
- validation rows written/read by manifest summary: 81,845;
- hazard input rows read: 81,710.

The classification remains `inconclusive`, not `pass`, because this is a small
gate run only: target-scale convergence is not established, manual QGIS visual
QA is still not run, and local scaling evidence identifies conditional-curve
and raster output volume as the next bottleneck before increasing ensemble
size.

## Executable Checks

The run-freeze validator accepts the completed local gate record and can print
the command plan for reproducing the frozen validation and hazard steps:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run python \
  scripts/validate_public_real_site_conditional_pilot_run.py \
  validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml \
  --print-command-plan
```

The command plan validates the selected geodata manifest and source/scenario
policy, runs the frozen validation case, and builds sampling-weighted
conditional hazard layers, conditional curves, GeoTIFFs, the GIS package
manifest, and reducer chunk manifests. Generated outputs stay in ignored
`validation/private/` and `hazard/results/` paths.

The reconciled commands used for this evidence were:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run python \
  scripts/run_dem_terrain_sensitivity.py \
  --pilot-manifest data/processed/swisstopo/tschamut_public_pilot_manifest.yaml \
  --source-scenario-policy validation/policies/tschamut_public_source_scenario_policy_v1.yaml \
  --output-dir validation/private/tschamut_public_pilot/dem_sensitivity_gate_v1
```

```bash
cargo run -- validate --case \
  validation/private/tschamut_public_pilot/gate_v1/tschamut_public_conditional_gate_case.yaml
```

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/build_hazard_layers.py \
  --case validation/private/tschamut_public_pilot/gate_v1/tschamut_public_conditional_gate_case.yaml \
  --output-dir hazard/results/tschamut_public_pilot/gate_v1 \
  --grid-xmin 2696376.0 \
  --grid-ymin 1167384.0 \
  --grid-ncols 300 \
  --grid-nrows 304 \
  --grid-cell-size 2.0 \
  --map-product-id tschamut_public_conditional_gate_v1 \
  --probability-mode sampling_weighted_conditional \
  --normalization-scope conditioned_on_filter \
  --source-zone-metadata-path data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_source_zone_metadata_v1.yaml \
  --scenario-table-path data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_scenario_table_v1.csv \
  --map-package-manifest-json hazard/results/tschamut_public_pilot/gate_v1/tschamut_public_conditional_gate_v1_map_package_manifest.json \
  --export-geotiff \
  --pilot-gis-package \
  --pilot-gis-package-manifest-json hazard/results/tschamut_public_pilot/gate_v1/tschamut_public_conditional_gate_v1_pilot_gis_package_manifest.json \
  --pilot-gis-qa-status not-run \
  --pilot-gis-qa-note "Manual GIS/QGIS inspection has not been run for this generated package." \
  --reducer-workers 2 \
  --no-plots \
  --diagnostics validation/private/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_metrics.json \
  --trajectory validation/private/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_trajectory.csv \
  --ensemble-trajectories-dir validation/private/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_trajectories \
  --deposition validation/private/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_deposition.csv \
  --ensemble-impact-events-dir validation/private/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_impacts \
  --kinetic-energy-exceedance-j 1000.0 \
  --kinetic-energy-exceedance-j 10000.0 \
  --jump-height-exceedance-m 1.0 \
  --jump-height-exceedance-m 2.0
```

For memory evidence, the validation and hazard commands were also rerun with
`/usr/bin/time` sidecars at:

- `validation/private/tschamut_public_pilot/gate_v1/validation_gate_time.txt`;
- `hazard/results/tschamut_public_pilot/gate_v1/hazard_gate_time.txt`.

## Claim Boundary

Allowed current claims:

- the selected public geodata manifest and source/scenario policy are frozen
  for this conditional diagnostic gate;
- the processed DEM, DEM sensitivity artifacts, validation outputs, hazard
  outputs, GIS package, scaling summary, and time sidecars are local ignored
  artifacts and are not committed;
- current outputs are unweighted diagnostics, sampling-weighted conditional
  products, or conditional intensity-exceedance products;
- swisstopo terrain remains input geodata, not validation evidence by itself.

Unsupported current claims:

- annual frequency;
- return-period products;
- physical probability;
- risk-map meaning;
- operational or validated hazard-map status.
