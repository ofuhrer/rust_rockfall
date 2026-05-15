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

Same-scale private case regeneration is now deterministic from the committed
frozen pilot records and processed public inputs:

- regeneration command:
  `PYENV_VERSION=system uv run python scripts/generate_tschamut_same_scale_cases.py --format json`
- source records:
  `validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml`,
  `validation/pilot_runs/tschamut_public_scalable_conditional_target_gate_v1.yaml`,
  `validation/policies/tschamut_public_source_scenario_policy_v1.yaml`,
  `data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_source_zone_metadata_v1.yaml`,
  `data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_scenario_table_v1.csv`,
  `data/processed/swisstopo/tschamut_public_pilot/input/release_points_lv95.csv`,
  `data/processed/swisstopo/tschamut_public_pilot/input/observed_deposition_lv95.csv`,
  `data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_swissalti3d_metadata.yaml`,
  `data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_swissalti3d_crop.asc`
- deterministic selection rule: lexicographically smallest shared
  release/deposition `trajectory_id` from the processed public rows; the
  current pilot resolves to `v004`
- preserved claim boundary: the regenerated cases stay research-diagnostic and
  do not change physics, defaults, thresholds, or source-zone semantics

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

The staged swissTLM3D archive has since been queried at corridor level
against the selected Tschamut extent. The measured counts are consistent with
the context review remaining `limiting`, not acceptable: roads and transport
features intersect the corridor, flowing-water features intersect the
corridor, barrier/protection features intersect the corridor, and the sampled
constructed-feature subset does not yet provide corridor intersections. This
is interpretation evidence only; it does not authorize scale-up or turn the
conditional gate into an operational product.

## Hazard-Context Overlap

The same-scale target hazard envelope was measured against the staged context
archive with the overlap diagnostic. A broader `top 3` probe was measured for
`reach_probability` and `max_kinetic_energy`; a three-layer probe that added
`max_jump_height` was runtime-limited and is not counted here:

```bash
PYENV_VERSION=system uv run python scripts/measure_hazard_context_overlap.py \
  --top-cell-count 3 \
  --buffer-radii-m 20 \
  --hazard-layer reach_probability \
  --hazard-layer max_kinetic_energy \
  --format json
```

Measured result:

- `hazard_context_overlap_status`: `measured`
- `context_archive_status`: `measured_corridor_relevance`
- `selected_hazard_layers`: `reach_probability`, `max_kinetic_energy`
- `selected_cell_total`: `6`
- `roads_or_transport_overlap`: `unresolved`
- `barriers_or_protection_overlap`: `unresolved`
- `water_or_channel_overlap`: `unresolved`
- `roads_or_transport_overlap.within_20m_cell_count_total`: `0`
- `barriers_or_protection_overlap.within_20m_cell_count_total`: `0`
- `water_or_channel_overlap.within_20m_cell_count_total`: `0`
- `final_classification`: `unresolved`

Interpretation boundary:

- the limiting corridor features remain measured as corridor-relevant at the
  archive level;
- the top three positive cells in the measured same-scale target hazard
  envelope did not show proximity within 20 m for roads, barriers, or water in
  the measured two-layer diagnostic envelope;
- this remains measured context-overlap evidence only;
- it does not validate hazard-map skill, obstacle physics, or scale-up
  readiness;
- `scale_up_authorized` stays `false`;
- `operational_claims_allowed` stays `false`.

## Disagreement Drivers

The target-vs-gate comparison is `ok` and shares `22` cell-wise layers, but
the disagreement is dominated by sampled-output differences rather than by
grid or corridor metadata.

Measured alignment:

- grid geometry matches exactly (`300 x 304`, `2.0 m`, EPSG `2056`);
- scenario table and source-zone metadata paths match;
- probability mode and normalization scope match;
- all shared cell-wise layer keys match;
- threshold disagreement count is `0`;
- nodata mismatch count is `90` overall;
- case IDs differ by design.

Case metadata differences visible in the restored inputs:

- `random.ensemble_size`: gate `6`, target `100`;
- `hazard_layers.statistics.jump_height_exceedance_m`: gate uses `0.5 m` and
  `2.0 m`, target uses `0.5 m`, `1.0 m`, and `2.0 m`;
- map product ids differ by design;
- output checksum comparison reports `8` matches, `36` mismatches, and `18`
  missing shared outputs.

Strongest disagreement layers:

- `max_kinetic_energy`: `linf_abs_diff 3028.22579673`, `l1_abs_diff
  190718.90391041967`, `rmse 983.451160251898`, `nonzero_jaccard 1.0`,
  `nodata_mismatch_count 45`;
- `max_jump_height`: `linf_abs_diff 1.42875571255`, `l1_abs_diff
  30.019475562139338`, `rmse 0.21594778911463908`, `nonzero_jaccard
  0.7598039215686274`, `nodata_mismatch_count 45`;
- `velocity_exceedance_5mps`: `linf_abs_diff 0.155778647582`, `l1_abs_diff
  5.312621804416979`, `nonzero_jaccard 0.8279569892473119`;
- `weighted_velocity_exceedance_5mps`: `linf_abs_diff 0.13545454545400004`,
  `l1_abs_diff 4.92878787878956`, `nonzero_jaccard 0.8279569892473119`;
- `velocity_exceedance_10mps`: `linf_abs_diff 0.12553020749800003`,
  `l1_abs_diff 4.4495832036858225`, `nonzero_jaccard 0.7389162561576355`.

Interpretation:

- the dominant driver is numeric divergence in the shared same-scale sampled
  outputs, not CRS or grid misalignment;
- `max_kinetic_energy` is dominated by magnitude difference with identical
  nonzero support;
- `max_jump_height` combines magnitude difference with support and nodata
  differences;
- the exceedance layers show smaller but still measurable footprint shifts;
- same-source and same-scenario metadata reduce the likelihood that the
  disagreement is coming from geometry or source-zone mismatch alone.

## Bounded Sampling Sensitivity Probe

The same-scale sampling-sensitivity probe was run in a bounded local turn to
test whether the target-vs-gate disagreement shrinks under controlled sample
size while preserving physics, thresholds, release assumptions, source and
scenario inputs, and non-operational semantics.

The summary-only probe case was useful as a blocker check, but it could not be
counted as the measured sensitivity probe because the hazard-layer builder
needs trajectory CSV output:

- case id: `validation_tschamut_public_sampling_sensitivity_v1`;
- validation output mode: `summary_only`;
- validation root:
  `validation/private/tschamut_public_pilot/sampling_sensitivity_v1`;
- audit footprint: `6` files, `171790` bytes.

The measured bounded probe therefore used the full-output case:

- case id: `validation_tschamut_public_sampling_sensitivity_v1_full`;
- probe ensemble size: `12`;
- probe seed: `34014`;
- validation output mode: `full`;
- validation root audit:
  `247` files, `68221148` bytes;
- hazard root audit:
  `49` files, `21058710` bytes;
- combined audit total:
  `89279858` bytes.

Measured probe commands:

```bash
PYENV_VERSION=system CARGO_TARGET_DIR=/tmp/rust-rockfall-target cargo run -- validate --case validation/private/tschamut_public_pilot/sampling_sensitivity_v1_full/tschamut_public_sampling_sensitivity_v1_full_case.yaml
PYENV_VERSION=system uv run python scripts/build_hazard_layers.py --case validation/private/tschamut_public_pilot/sampling_sensitivity_v1_full/tschamut_public_sampling_sensitivity_v1_full_case.yaml --output-dir hazard/results/tschamut_public_pilot/sampling_sensitivity_v1_full
PYENV_VERSION=system uv run python scripts/compare_hazard_map_convergence.py hazard/results/tschamut_public_pilot/sampling_sensitivity_v1_full/validation_tschamut_public_sampling_sensitivity_v1_full_manifest.json hazard/results/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_manifest.json hazard/results/tschamut_public_pilot/target_gate_v1/validation_tschamut_public_target_gate_v1_manifest.json --format json
```

Measured comparison result:

- comparison status: `ok`;
- comparison pairs run: `2`;
- shared cell-wise layer count: `44` total across the two pairs;
- strongest disagreement layers: `max_kinetic_energy`,
  `max_jump_height`, `velocity_exceedance_5mps`,
  `weighted_velocity_exceedance_5mps`, and `velocity_exceedance_10mps`;
- `max_kinetic_energy` and `max_jump_height` both shrank relative to the
  gate-vs-target comparison in TB-024, but they remain dominant;
- support and nodata differences persist, especially in `max_jump_height`,
  even though the total mismatch burden is lower than the gate-vs-target case.

Interpretation boundary:

- the probe shows measured sampling sensitivity, not accepted convergence;
- the shrinkage is real but incomplete, so the same-scale pilot remains
  conservative and non-operational;
- `scale_up_authorized` stays `false`;
- `operational_claims_allowed` stays `false`.

TB-031 extends this into a reusable multi-seed envelope by adding a second
bounded 12-trajectory seed. The measured envelope is lower than the gate-vs-
target baseline, but `max_kinetic_energy` remains dominant and
`max_jump_height` still carries support and nodata sensitivity. See
`docs/tschamut_public_same_scale_uncertainty_envelope.md` for the summarized
multi-seed ranges.

TB-033 separately audited the same-scale GIS/package outputs. The map-package
and pilot-GIS manifests are complete and the GeoTIFFs are present, but the
current rasters are not cloud-optimized, are strip-organized, and have no
overviews, so packaging remains COG-blocked even though the scientific
interpretation remains unchanged.

## Same-Scale Convergence Check

The restored same-scale target-side artifacts are now present and the
cell-wise convergence diagnostic can run directly on the emitted hazard
manifests:

- `target_artifact_restore_status`: `restored_or_regenerated`
- `processed_input_bundle_available`: `true`
- `target_private_case_available`: `true`
- `target_validation_manifest_available`: `true`
- `target_hazard_manifest_available`: `true`
- `target_cellwise_layers_available`: `true`
- `target_referenced_grids_available`: `true`
- `gate_manifest_available`: `true`
- readiness-audit total: `2063` files, `650545138` bytes

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/compare_hazard_map_convergence.py \
  hazard/results/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_manifest.json \
  hazard/results/tschamut_public_pilot/target_gate_v1/validation_tschamut_public_target_gate_v1_manifest.json \
  --format json
```

Both manifests expose `22` cell-wise layers. The comparison completed with
`status: ok`, but the result is still interpreted conservatively as
`inconclusive` rather than accepted convergence.

Measured overall diagnostics:

- `cellwise_layer_count`: `22`
- `cellwise_linf_abs_diff_max`: `3028.22579673`
- `cellwise_rmse_max`: `983.451160251898`
- `cellwise_nodata_mismatch_count`: `90`
- `cellwise_nonzero_jaccard_min`: `0.1`
- `output_checksum_match_count`: `8`
- `output_checksum_mismatch_count`: `36`
- `output_checksum_missing_count`: `18`

Largest disagreement layers:

- `max_kinetic_energy`: Linf `3028.22579673`, RMSE `983.451160251898`, nonzero Jaccard `1.0`
- `max_jump_height`: Linf `1.42875571255`, RMSE `0.21594778911463908`, nonzero Jaccard `0.7598039215686274`
- `velocity_exceedance_5mps`: Linf `0.155778647582`, RMSE `0.0016156994693019395`, nonzero Jaccard `0.8279569892473119`
- `weighted_velocity_exceedance_5mps`: Linf `0.13545454545400004`, RMSE `0.001482538767662409`, nonzero Jaccard `0.8279569892473119`
- `velocity_exceedance_10mps`: Linf `0.12553020749800003`, RMSE `0.0014119067351479587`, nonzero Jaccard `0.7389162561576355`

Interpretation boundaries remain unchanged:

- the comparison is measured evidence, not operational validation;
- the gate remains `scale_up_authorized: false`;
- annual / physical-frequency / risk claims remain out of scope;
- manual GIS/QGIS QA remains secondary;
- the bounded validation-output profile remains relevant because debug volume is still a limiting workflow pressure;
- the corridor-level context remains `limiting`;
- distributed execution remains deferred on the Balfrin sufficiency record.

Supporting same-scale evidence remains reusable:

- bounded validation output profile: `summary_only` with `4` files / `81425` bytes versus `125` files / `34545900` bytes baseline;
- target-side summary-only validation output profile: `summary_only` with `4` files / `1271721` bytes versus `2005` files / `571368823` bytes baseline;
- swissTLM3D corridor relevance: roads, barriers, and water are measured as `limiting`;
- Balfrin single-job execution sufficiency: next-step single-job execution is sufficient, distributed execution remains deferred.
- Spatial same-scale uncertainty tooling now localizes the dominant disagreement corridor:
  `max_kinetic_energy` is concentrated in a compact LV95 footprint but still carries
  material support/nodata disagreement, `max_jump_height` remains support/nodata
  sensitive, and `velocity_exceedance_5mps` is localized with much smaller range.

## Conditional Pilot Closure Assessment

Measured evidence is now summarized by
`scripts/summarize_tschamut_conditional_pilot_closure.py`. The current derived
closure status remains `inconclusive`, which is consistent with the measured
mix of signals:

- same-scale readiness is `ready`;
- convergence remains `inconclusive` across the measured multi-seed envelope;
- `max_kinetic_energy` remains the dominant disagreement layer;
- `max_jump_height` retains support and nodata sensitivity;
- the validation-output profile still carries a measured no-go blocker for
  hazard-rebuild compatibility;
- GIS packages are manifest-complete but COG-blocked;
- the corridor-context interpretation remains `limiting`;
- reducer/runtime scaling still supports the single-job path;
- second-site portability remains metadata/template-level rather than ready.

The helper keeps `scale_up_authorized: false` and
`operational_claims_allowed: false` and separates the evidence needed for
`accepted_diagnostic`, `no_go`, and `deferred` closure decisions from the
current non-operational pilot state.

Hazard-rebuild compatibility is now summarized separately by
`scripts/check_hazard_rebuild_output_profile.py`: the current target
`summary_only` profile is `summary_only_not_rebuildable`, both bounded probe
profiles are `hazard_rebuild_ready`, and the minimum reduced contract retains
trajectory, deposition, impact-event, and diagnostics families while leaving
trajectory metadata and stop-state as optional overhead.

The COG blocker is also now shown to be technically fixable on a scratch
sample: `scripts/prototype_cog_conversion.py` converts one same-scale GeoTIFF
to `/tmp`, and the GIS/COG audit can distinguish that converted sample as
`cog_conversion_sample_ready` while the committed same-scale package roots
remain `gis_package_ready_cog_blocked` until regenerated.

## Validation And Calibration Evidence Gaps

`scripts/assess_validation_calibration_evidence_gaps.py` now summarizes the
boundary between workflow credibility and physical credibility. Its current
derived status is `physical_credibility_status: not_established`, with
`calibration_status: missing` and `validation_status: partial`. The helper
keeps `scale_up_authorized: false` and `operational_claims_allowed: false`.

Current category mapping:

- observed deposition / runout evidence: `partial`
- release-zone evidence: `partial`
- block-size / block-population evidence: `missing`
- terrain and context evidence: `partial`
- calibration evidence: `missing`
- holdout / validation evidence: `partial`
- multi-site transfer evidence: `partial`

This is evidence-gap analysis only. It does not relabel the current same-scale
diagnostics as physically validated and it does not authorize annual-frequency,
risk, exposure, vulnerability, or operational claims.

## Artifact Readiness Preflight

Before rerunning convergence, output-profile, context, or uncertainty
diagnostics, use the readiness helper to see which same-scale artifacts are
present and which exact paths still need regeneration:

```bash
PYENV_VERSION=system uv run python scripts/check_same_scale_artifact_readiness.py --format json
```

The helper is read-only. It checks gate validation, gate hazard, target
validation, target hazard, target `summary_only` validation, staged public
context, swissTLM3D metadata, hazard/context overlap inputs, and
same-scale uncertainty-envelope inputs. It reports exact missing paths plus
the known regeneration commands, but it does not authorize scale-up or alter
the convergence interpretation.

## Executable Checks

The run-freeze validator accepts the completed local gate record and can print
the command plan for reproducing the frozen validation and hazard steps:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run python \
  scripts/validate_public_real_site_conditional_pilot_run.py \
  validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml \
  --print-command-plan
```

The canonical portable command plan is also available through
`PYENV_VERSION=system uv run python scripts/generate_pilot_command_plan.py --site tschamut_same_scale --format text`.
That helper consolidates the readiness preflight, case generation, validation,
hazard-layer building, convergence comparison, output-profile checks, context
inspection, hazard/context overlap, and uncertainty-summary commands for the
selected Tschamut workflow. Generated outputs stay in ignored
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

Current applied comparison attempt:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/compare_hazard_map_convergence.py \
  hazard/results/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_manifest.json \
  hazard/results/tschamut_public_pilot/target_gate_v1/validation_tschamut_public_target_gate_v1_manifest.json \
  --format json
```

- `convergence_comparison_status`: `blocked_missing_inputs`
- `target_manifest_available`: `false`
- `gate_manifest_available`: `true`
- `cellwise_layers_available`: `true` for the gate manifest only
- missing target path:
  `hazard/results/tschamut_public_pilot/target_gate_v1/validation_tschamut_public_target_gate_v1_manifest.json`
- matching private target manifest path missing in this checkout:
  `validation/private/tschamut_public_pilot/target_gate_v1/validation_tschamut_public_target_gate_v1_manifest.json`
- `validation_output_mode_context`: `summary_only` for the separate reduced-output probe; the full debug run remains available for family accounting
- `context_classification`: `limiting`
- `scale_up_authorized`: `false`
- `operational_claims_allowed`: `false`

The comparison remains blocked until the target-side same-scale manifest and
its referenced raster files are restored or regenerated. This keeps the result
conditional and non-operational rather than inferring spatial stability from a
single manifest-side self-check.

## TB-018 Target Artifact Restore Status

Current checkout status: `restored_or_regenerated`

- target_artifact_restore_status: `restored_or_regenerated`
- processed_input_bundle_available: `true`
- target_private_case_available: `true`
- target_validation_manifest_available: `true`
- target_hazard_manifest_available: `true`
- target_cellwise_layers_available: `true`
- target_referenced_grids_available: `true`
- gate_manifest_available: `true`
- tb019_ready: `true`
- scale_up_authorized: `false`
- operational_claims_allowed: `false`
- artifact_file_count: `2063`
- artifact_byte_count: `650545138`
- comparison_probe_status: `ok`
- comparison_shared_layer_count: `22`
- comparison_cellwise_linf_abs_diff_max: `3028.22579673`
- comparison_cellwise_l1_abs_diff_sum: `190790.42488112117`

Commands run:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/audit_local_artifacts.py \
  validation/private/tschamut_public_pilot/target_gate_v1 \
  hazard/results/tschamut_public_pilot/target_gate_v1

CARGO_TARGET_DIR=/tmp/rust-rockfall-target cargo run -- validate --case \
  validation/private/tschamut_public_pilot/target_gate_v1/tschamut_public_target_gate_case.yaml

UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/build_hazard_layers.py \
  --case validation/private/tschamut_public_pilot/target_gate_v1/tschamut_public_target_gate_case.yaml \
  --output-dir hazard/results/tschamut_public_pilot/target_gate_v1 \
  --grid-xmin 2696376.0 \
  --grid-ymin 1167384.0 \
  --grid-ncols 300 \
  --grid-nrows 304 \
  --grid-cell-size 2.0 \
  --map-product-id tschamut_public_scalable_conditional_target_gate_v1 \
  --probability-mode sampling_weighted_conditional \
  --normalization-scope conditioned_on_filter \
  --source-zone-metadata-path data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_source_zone_metadata_v1.yaml \
  --scenario-table-path data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_scenario_table_v1.csv \
  --map-package-manifest-json hazard/results/tschamut_public_pilot/target_gate_v1/tschamut_public_scalable_conditional_target_gate_v1_map_package_manifest.json \
  --export-geotiff \
  --pilot-gis-package \
  --pilot-gis-package-manifest-json hazard/results/tschamut_public_pilot/target_gate_v1/tschamut_public_scalable_conditional_target_gate_v1_pilot_gis_package_manifest.json \
  --pilot-gis-qa-status not-run \
  --pilot-gis-qa-note "Manual GIS/QGIS inspection has not been run for this generated package." \
  --reducer-workers 2 \
  --no-plots \
  --conditional-curve-export summary-only \
  --grid-csv-export none \
  --diagnostics validation/private/tschamut_public_pilot/target_gate_v1/validation_tschamut_public_target_gate_v1_metrics.json \
  --trajectory validation/private/tschamut_public_pilot/target_gate_v1/validation_tschamut_public_target_gate_v1_trajectory.csv \
  --ensemble-trajectories-dir validation/private/tschamut_public_pilot/target_gate_v1/validation_tschamut_public_target_gate_v1_trajectories \
  --deposition validation/private/tschamut_public_pilot/target_gate_v1/validation_tschamut_public_target_gate_v1_deposition.csv \
  --ensemble-impact-events-dir validation/private/tschamut_public_pilot/target_gate_v1/validation_tschamut_public_target_gate_v1_impacts \
  --kinetic-energy-exceedance-j 1000.0 \
  --kinetic-energy-exceedance-j 10000.0 \
  --jump-height-exceedance-m 0.5 \
  --jump-height-exceedance-m 1.0 \
  --jump-height-exceedance-m 2.0 \
  --velocity-exceedance-mps 5.0 \
  --velocity-exceedance-mps 10.0

UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/compare_hazard_map_convergence.py \
  hazard/results/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_manifest.json \
  hazard/results/tschamut_public_pilot/target_gate_v1/validation_tschamut_public_target_gate_v1_manifest.json \
  --format json
```

Missing inputs: `[]`
Blocked reason: `none`
Commands required if blocked: `[]`
TB-014/19 readiness: `true` for readiness probing only; not a convergence acceptance pass.

## TB-017 Target Manifest Restore Status

Current checkout status: `blocked_missing_inputs`

- target_artifact_restore_status: `blocked_missing_inputs`
- target_validation_manifest_available: `false`
- target_hazard_manifest_available: `false`
- target_cellwise_layers_available: `false`
- target_referenced_grids_available: `false`
- gate_manifest_available: `true` in this checkout
- tb014_ready: `false`
- validation_output_mode: `unavailable`
- defaults_changed: `false`
- scale_up_authorized: `false`
- operational_claims_allowed: `false`

Missing local paths in this checkout:

- `validation/private/tschamut_public_pilot/target_gate_v1/tschamut_public_target_gate_case.yaml`
- `validation/private/tschamut_public_pilot/target_gate_v1/validation_tschamut_public_target_gate_v1_manifest.json`
- `hazard/results/tschamut_public_pilot/target_gate_v1/validation_tschamut_public_target_gate_v1_manifest.json`
- `hazard/results/tschamut_public_pilot/target_gate_v1/tschamut_public_scalable_conditional_target_gate_v1_map_package_manifest.json`
- `hazard/results/tschamut_public_pilot/target_gate_v1/tschamut_public_scalable_conditional_target_gate_v1_pilot_gis_package_manifest.json`
- `hazard/results/tschamut_public_pilot/target_gate_v1/validation_tschamut_public_target_gate_v1_conditional_intensity_exceedance_curves.csv`
- `hazard/results/tschamut_public_pilot/target_gate_v1/chunks/`

Missing processed public inputs needed to regenerate the target side:

- `data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_swissalti3d_metadata.yaml`
- `data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_scenario_table_v1.csv`
- `data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_source_zone_metadata_v1.yaml`

Required regeneration path when inputs are restored:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/validate_public_real_site_conditional_pilot_run.py \
  validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml \
  --print-command-plan

cargo run -- validate --case validation/private/tschamut_public_pilot/target_gate_v1/tschamut_public_target_gate_case.yaml

UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/build_hazard_layers.py \
  --case validation/private/tschamut_public_pilot/target_gate_v1/tschamut_public_target_gate_case.yaml \
  --output-dir hazard/results/tschamut_public_pilot/target_gate_v1 \
  --grid-xmin 2696376.0 \
  --grid-ymin 1167384.0 \
  --grid-ncols 300 \
  --grid-nrows 304 \
  --grid-cell-size 2.0 \
  --map-product-id tschamut_public_scalable_conditional_target_gate_v1 \
  --probability-mode sampling_weighted_conditional \
  --normalization-scope conditioned_on_filter \
  --source-zone-metadata-path data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_source_zone_metadata_v1.yaml \
  --scenario-table-path data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_scenario_table_v1.csv \
  --map-package-manifest-json hazard/results/tschamut_public_pilot/target_gate_v1/tschamut_public_scalable_conditional_target_gate_v1_map_package_manifest.json \
  --export-geotiff \
  --pilot-gis-package \
  --pilot-gis-package-manifest-json hazard/results/tschamut_public_pilot/target_gate_v1/tschamut_public_scalable_conditional_target_gate_v1_pilot_gis_package_manifest.json \
  --pilot-gis-qa-status not-run \
  --pilot-gis-qa-note "Manual GIS/QGIS inspection has not been run for this generated package." \
  --reducer-workers 2 \
  --no-plots \
  --conditional-curve-export summary-only \
  --grid-csv-export none \
  --diagnostics validation/private/tschamut_public_pilot/target_gate_v1/validation_tschamut_public_target_gate_v1_metrics.json \
  --trajectory validation/private/tschamut_public_pilot/target_gate_v1/validation_tschamut_public_target_gate_v1_trajectory.csv \
  --ensemble-trajectories-dir validation/private/tschamut_public_pilot/target_gate_v1/validation_tschamut_public_target_gate_v1_trajectories \
  --deposition validation/private/tschamut_public_pilot/target_gate_v1/validation_tschamut_public_target_gate_v1_deposition.csv \
  --ensemble-impact-events-dir validation/private/tschamut_public_pilot/target_gate_v1/validation_tschamut_public_target_gate_v1_impacts \
  --kinetic-energy-exceedance-j 1000.0 \
  --kinetic-energy-exceedance-j 10000.0 \
  --jump-height-exceedance-m 1.0 \
  --jump-height-exceedance-m 2.0
```

TB-014 readiness remains `false` in this checkout because the target-side
manifest and referenced grid files are missing. TB-014 can be retried only
after the ignored target artifacts are restored or regenerated locally.

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

A separate second-site portability preflight now reports the public-geodata
products, metadata records, and ignored output roots that would be required to
port this workflow beyond Tschamut. That helper is metadata-only and does not
change the current Tschamut interpretation.

The source-zone / scenario contract audit
`scripts/audit_multisite_source_scenario_contract.py` further separates the
portable contract shape from Tschamut-specific release and block heuristics,
which helps future second-site staging without reinterpreting the gate result.

Relevant paths:

- raw archive:
  `data/raw/swisstopo/swisstlm3d/swisstlm3d_2021-04_2056_5728.shp.zip`
- staged context archive:
  `data/processed/swisstopo/tschamut_public_pilot/context/swisstlm3d/swisstlm3d_2021-04_2056_5728.shp.zip`
- metadata sidecar:
  `data/processed/swisstopo/tschamut_public_pilot/context/swisstlm3d/metadata.json`
