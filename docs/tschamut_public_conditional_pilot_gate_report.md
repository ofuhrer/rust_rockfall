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
| Validation manifest | `b41c5469fe0e3ef29216d05ecf7872509210c0d0a59f63b6230ea6dedce635f3` |
| Hazard manifest | `5d62a9dd4bb8e4436c95125d6009796c7a67dd8bbcbdbff65f790dfe12c32893` |
| Conditional curve table | `c6456f6af984e531c550e72df09240302cdbf5ac34d91741d975ed2da6be81a9` |
| Map-package manifest | `15beba852cbb1d4430f7d4e23714cfd6a321e33e635f4521eb86cdd42ec5bd52` |
| Pilot GIS package manifest | `52061a9a60bd4a5b082c5a68818d4add11b7098e6197f44e5aed2ae789d689c6` |
| DEM sensitivity summary | `85c1ba97f012167ab29f2772b5893aa84fc21cc483bd7d5c7f3f12a155701fa6` |
| Scaling summary | `87ebec392e5142ff5aae698e1f4e7b335dd9a7b56bab8f74e41efced302a7388` |

Runtime and output-volume evidence:

- validation manifest wall time: `4.508` s (from scaling summary);
- hazard manifest wall time: `10.580` s (from scaling summary);
- external `/usr/bin/time` elapsed seconds: validation `6.14`, hazard `11.70`;
- external max RSS samples: validation `37093376`, hazard `429277184` (`max_rss_kb`);
- run-freeze peak memory record: `409.22` MiB (derived from external hazard max RSS sample);
- ignored output tree total: 191 files, 267,527,120 bytes;
- generated validation outputs: 128 files, 34,578,541 bytes;
- generated hazard outputs: 63 files, 232,948,579 bytes;
- validation rows written/read by manifest summary: 81,845;
- hazard input rows read: 81,710.

The classification remains `inconclusive`, not `pass`, because this is a small
gate run only: target-scale convergence is not established, manual QGIS visual
QA is classified `inconclusive`, forest/obstacle omission is classified
`limiting`, and local scaling evidence identifies conditional-curve and raster
output volume as the next bottleneck before increasing ensemble size.

The forest and obstacle omission scope record is:
`validation/pilot_runs/tschamut_public_obstacle_scope_v1.yaml`. It records
SWISSIMAGE, swissTLM3D, swissSURFACE3D/swissSURFACE3D Raster, and
swissBUILDINGS3D context as documented but not locally reviewed for this gate.
The classification is `limiting`; it does not add obstacle physics and does
not justify tuning restitution, roughness, terrain classes, stopping
thresholds, or scenario weights to absorb omitted vegetation or constructed
features.

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

## TB-012 Local Artifact Refresh

Current checkout status: `locally_refreshed_same_scale_gate`

- artifact_refresh_status: `locally_refreshed_same_scale_gate`
- validation_output_mode: `summary_only` for the separate reduced-output probe; the full debug run remains available for family accounting
- defaults_changed: `false`
- selected_pilot_artifacts_available: `true` for the locally staged small gate
- cellwise_layers_available: `true`
- convergence_comparison_status: `ok_self_check_only`
- validation_output_accounting_status: `available`
- full validation output: `125` files, `34545900` bytes from the local full-debug gate manifest
- summary-only validation output: `4` files, `81425` bytes from the local reduced-output gate manifest
- validation reduction: `121` fewer files and `34464475` fewer bytes
- hazard output audit: `56` files, `77758043` bytes under `hazard/results/tschamut_public_pilot/gate_v1`
- local audit total across validation and hazard roots: `183` files, `112318957` bytes
- scale_up_authorized: `false`
- operational_claims_allowed: `false`

The selected-gate inputs were regenerated from public Tschamut/swissALTI3D
sources and staged under ignored paths. The local private case and output
artifacts are intentionally not committed. This refresh proves that the current
contracts can produce validation manifests, hazard manifests, map-package
manifests, pilot-GIS manifests, cell-wise hazard-grid references, and
summary-only validation output evidence on the same-scale gate. It does not
replace the older Balfrin target-scale evidence, does not increase ensemble
size, and does not accept the pilot scientifically.

Commands executed:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/prepare_tschamut_public_benchmark.py \
  --output-root data/processed/swisstopo/tschamut_public_pilot \
  --padding-m 250 --force
cargo run -- validate --case validation/private/tschamut_public_pilot/gate_v1/tschamut_public_conditional_gate_case.yaml
UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/build_hazard_layers.py \
  --case validation/private/tschamut_public_pilot/gate_v1/tschamut_public_conditional_gate_case.yaml \
  --output-dir hazard/results/tschamut_public_pilot/gate_v1 \
  --grid-xmin 2696376.0 --grid-ymin 1167384.0 \
  --grid-ncols 300 --grid-nrows 304 --grid-cell-size 2.0 \
  --map-product-id tschamut_public_conditional_gate_v1 \
  --probability-mode sampling_weighted_conditional \
  --normalization-scope conditioned_on_filter \
  --source-zone-metadata-path data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_source_zone_metadata_v1.yaml \
  --scenario-table-path data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_scenario_table_v1.csv \
  --map-package-manifest-json hazard/results/tschamut_public_pilot/gate_v1/tschamut_public_conditional_gate_v1_map_package_manifest.json \
  --export-geotiff --pilot-gis-package \
  --pilot-gis-package-manifest-json hazard/results/tschamut_public_pilot/gate_v1/tschamut_public_conditional_gate_v1_pilot_gis_package_manifest.json \
  --pilot-gis-qa-status not-run \
  --pilot-gis-qa-note "Manual GIS/QGIS inspection has not been run for this generated package." \
  --reducer-workers 2 --no-plots \
  --conditional-curve-export summary-only --grid-csv-export none \
  --diagnostics validation/private/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_metrics.json \
  --trajectory validation/private/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_trajectory.csv \
  --ensemble-trajectories-dir validation/private/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_trajectories \
  --deposition validation/private/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_deposition.csv \
  --ensemble-impact-events-dir validation/private/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_impacts \
  --kinetic-energy-exceedance-j 1000.0 \
  --kinetic-energy-exceedance-j 10000.0 \
  --jump-height-exceedance-m 1.0 \
  --jump-height-exceedance-m 2.0
cargo run -- validate --case validation/private/tschamut_public_pilot/gate_v1_summary_only/tschamut_public_conditional_gate_summary_only_case.yaml
```

Validation metrics from the full local gate:

- `validation_release_count`: `10.0`
- `validation_simulated_trajectory_count`: `60.0`
- `observed_mean_runout_m`: `102.84352800000002`
- `simulated_mean_runout_m`: `71.88091457322881`
- `runout_distance_error_m`: `30.962613426771213`
- `deposition_centroid_error_m`: `30.43179306979487`
- `deposition_cloud_mean_nearest_error_m`: `24.61802934798019`
- `deposition_cloud_overlap_fraction`: `0.7`
- `lateral_spread_error_m`: `16.709094142790736`

Hazard manifest evidence:

- manifest path:
  `hazard/results/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_manifest.json`
- `cellwise_layers`: `22`
- `output_file_count`: `53` recorded in the hazard performance snapshot
- `output_bytes`: `21025596` recorded in the hazard performance snapshot
- `total_wall_seconds`: `7.108489040983841`
- `conditional_curve_export.mode`: `summary-only`
- `grid_csv_export`: `none`
- `conditional_curve.row_count`: `1276800`

The cell-wise convergence command now works against normal emitted hazard
manifests with repo-relative grid paths:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/compare_hazard_map_convergence.py \
  hazard/results/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_manifest.json \
  hazard/results/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_manifest.json \
  --format json
```

Self-comparison result:

- `status`: `ok`
- `cellwise_layer_count`: `22`
- `cellwise_shared_layer_count`: `22`
- `cellwise_linf_abs_diff_max`: `0.0`
- `cellwise_l1_abs_diff_sum`: `0.0`
- `cellwise_rmse_max`: `0.0`
- `cellwise_nonzero_jaccard_min`: `1.0`
- `cellwise_threshold_disagreement_count`: `0`
- `output_checksum_match_count`: `53`

This is a plumbing sanity check only. Target-vs-gate spatial convergence still
requires the matching `target_gate_v1` hazard manifest and raster artifacts.

## TB-013 Context Stage Update

Current checkout status: `reviewed_local_context`

- context_review_status: `reviewed_local_context`
- spatial_relevance_status: `reviewed_local_context`
- classification: `limiting`
- swissSURFACE3D Raster: staged locally
- SWISSIMAGE: staged locally
- swissBUILDINGS3D: staged locally
- swissTLM3D: staged locally, but not yet clipped or queried for the selected
  corridor
- operational_claims_allowed: `false`

The swissTLM3D archive is now present under the ignored raw and processed
context paths. The report therefore no longer treats it as metadata-only; the
remaining gap is corridor-specific extraction or feature-level inspection for
roads, channels, and barrier/protection context. Archive presence alone does
not make the context acceptable, so the local classification stays `limiting`.

Relevant paths:

- raw archive:
  `data/raw/swisstopo/swisstlm3d/swisstlm3d_2021-04_2056_5728.shp.zip`
- staged context archive:
  `data/processed/swisstopo/tschamut_public_pilot/context/swisstlm3d/swisstlm3d_2021-04_2056_5728.shp.zip`
- metadata sidecar:
  `data/processed/swisstopo/tschamut_public_pilot/context/swisstlm3d/metadata.json`
