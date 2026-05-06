# Terrain/Material Diagnostic Matrix

Status: no-tuning diagnostic matrix. This report does not change physics,
defaults, thresholds, release assumptions, validation cases, validation
baselines, terrain classes, benchmark filters, or operational claims.

## Scope

This report applies
`docs/terrain_material_interaction_diagnostic_protocol.md` using existing
diagnostic outputs plus a small set of selected regenerated outputs that only
populate additive `stop_state` fields. It does not run public benchmarks, does
not run held-out Chant Sura for `shape_contact_v0`, and does not use Tschamut
or Mel de la Niva as physics-selection evidence.

Generated local artifacts are ignored and reproducible:

- `validation/results/terrain_material_diagnostic_matrix/stopping_summary.csv`
- `validation/results/terrain_material_diagnostic_matrix/stopping_summary.md`
- `validation/results/terrain_material_diagnostic_matrix/matrix.csv`
- `validation/results/terrain_material_diagnostic_matrix/matrix.md`

## Commands Run

Selected existing diagnostic cases were regenerated only to attach additive
`stop_state` provenance to diagnostics/manifests:

```bash
cargo run -- verify --case verification/analytic/inclined_slide_stop.yaml
cargo run -- verify --case verification/synthetic/slide_to_stop_transition.yaml
cargo run -- verify --case verification/synthetic/repeated_low_energy_impacts.yaml
cargo run -- validate --case validation/cases/chant_sura_contact.yaml
cargo run -- validate --case validation/cases/chant_sura_contact_rotational.yaml
cargo run -- validate --case validation/cases/performance_smoke.yaml
cargo run -- validate --case validation/cases/swissalti3d_release_zone_terrain_classes_pilot.yaml
```

The stopping summary and matrix were generated with:

```bash
python3 scripts/summarize_stopping_behavior.py \
  --diagnostics verification_inclined_slide:verification/results/analytic_inclined_slide_stop.json \
  --diagnostics verification_slide_to_stop:verification/results/regime_slide_to_stop_transition.json \
  --diagnostics verification_repeated_low_energy:verification/results/regime_repeated_low_energy_impacts.json \
  --diagnostics chant_sura_contact:validation/results/chant_sura_contact_metrics.json \
  --diagnostics chant_sura_contact_rotational:validation/results/chant_sura_contact_rotational_metrics.json \
  --manifest synthetic_swiss_performance:validation/results/performance_smoke_manifest.json \
  --manifest synthetic_swiss_terrain_classes:validation/results/swissalti3d_release_zone_terrain_classes_pilot_manifest.json \
  --deposition tschamut_translational:validation/results/tschamut_public_benchmark_all/validation/validation_tschamut_public_benchmark_baseline_deposition.csv \
  --deposition tschamut_rotational:validation/results/tschamut_public_benchmark_all/validation/validation_tschamut_public_benchmark_rotational_deposition.csv \
  --manifest tschamut_translational_manifest:validation/results/tschamut_public_benchmark_all/validation/validation_tschamut_public_benchmark_baseline_manifest.json \
  --manifest tschamut_rotational_manifest:validation/results/tschamut_public_benchmark_all/validation/validation_tschamut_public_benchmark_rotational_manifest.json \
  --trajectory mel_translational_smoke:validation/results/public_benchmarks/mel_de_la_niva_runnable/validation/validation_mel_de_la_niva_baseline_trajectory.csv \
  --trajectory mel_rotational_smoke:validation/results/public_benchmarks/mel_de_la_niva_runnable/validation/validation_mel_de_la_niva_rotational_trajectory.csv \
  --output-csv validation/results/terrain_material_diagnostic_matrix/stopping_summary.csv \
  --output-md validation/results/terrain_material_diagnostic_matrix/stopping_summary.md
```

```bash
python3 scripts/build_terrain_material_diagnostic_matrix.py \
  --input-csv validation/results/terrain_material_diagnostic_matrix/stopping_summary.csv \
  --output-csv validation/results/terrain_material_diagnostic_matrix/matrix.csv \
  --output-md validation/results/terrain_material_diagnostic_matrix/matrix.md
```

## Matrix Bins

Bins are intentionally coarse and were declared before summary interpretation:

- `terrain_slope_abs`: `flat_to_low` below `0.20`, `moderate` below `0.60`,
  `steep` otherwise, or `unknown`;
- `low_energy_contact_count`: `none`, `low` below `100`, `high` at or above
  `100`, or `unknown`;
- `impact_count`: `none`, `low` below `100`, `high` at or above `100`, or
  `unknown`;
- `final_speed_mps`: `stopped_or_near_stopped` at or below `0.05 m/s`,
  `moving` at or below `5 m/s`, `high_speed` above `5 m/s`, or `unknown`;
- `runout_class`: `short` below `75 m`, `mid` up to `150 m`, `long` above
  `150 m`, or `unknown`.

These bins are descriptive only. They are not calibration thresholds.

## Diagnostic Matrix

| Role | Contact model | Evidence | Stop reason | Final state | Slope bin | Low-energy contacts | Impacts | Speed bin | Runout class | Traj./rows | Final speed mean (m/s) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | ---: | ---: |
| Chant Sura contact | `sphere_rotational_v1` | explicit `stop_state` | `t_max_reached_airborne` | `airborne` | steep | none | low | high_speed | unknown | 1 | 5.867 |
| Chant Sura contact | `translational_v0` | explicit `stop_state` | `t_max_reached_airborne` | `airborne` | steep | none | low | high_speed | unknown | 3 | 5.121 |
| Synthetic Swiss hazard/smoke | `translational_v0` | explicit `stop_state` | `t_max_reached_in_contact_state` | `impact` | moderate | none | high | moving | unknown | 14 | 1.708 |
| Mel de la Niva smoke | `sphere_rotational_v1` | proxy fallback | `output_ended_while_in_contact_state` | `impact` | unknown | none | high | high_speed | unknown | 1 | 149.785 |
| Mel de la Niva smoke | `translational_v0` | proxy fallback | `output_ended_airborne` | `airborne` | unknown | none | high | high_speed | unknown | 1 | 5.408 |
| Tschamut diagnostic | `sphere_rotational_v1` | proxy fallback | final speed above threshold | unknown | unknown | unknown | unknown | high_speed | long | 480 | 6.725 |
| Tschamut diagnostic manifest | `sphere_rotational_v1` | proxy fallback | unknown | unknown | unknown | unknown | high | unknown | unknown | 495 | n/a |
| Tschamut diagnostic | `translational_v0` | proxy fallback | final speed above/below threshold mix | unknown | unknown | unknown | unknown | moving | short | 480 | 0.312 |
| Tschamut diagnostic manifest | `translational_v0` | proxy fallback | unknown | unknown | unknown | unknown | high | unknown | unknown | 495 | n/a |
| Verification | `translational_v0` | explicit `stop_state` | `explicit_stopped_state` | `stopped` | flat_to_low | low | unknown | stopped_or_near_stopped | unknown | 1 | 0.000 |
| Verification | `translational_v0` | explicit `stop_state` | `explicit_stopped_state` | `stopped` | moderate | low | unknown | stopped_or_near_stopped | unknown | 1 | 0.000 |
| Verification | `translational_v0` | explicit `stop_state` | `final_speed_below_stop_threshold` | `impact` | flat_to_low | high | low | stopped_or_near_stopped | unknown | 1 | 0.003 |

## Findings

1. Explicit `stop_state` works for single-run diagnostics and manifests. The
   verification rows distinguish explicit stopped states, low-speed terminal
   repeated-impact behavior, and `t_max`/contact-state termination.

2. Chant Sura contact rows now have explicit `stop_state`, but they end
   airborne with high terminal speed. This reinforces the existing
   interpretation that Chant Sura is a trajectory/contact benchmark, not a
   deposition or stopping benchmark.

3. The synthetic Swiss terrain-class smoke rows provide explicit
   terrain-normal/slope context and show `t_max_reached_in_contact_state` on
   moderate final slope. This proves the reporting path can carry terrain
   context, but the fixture is synthetic and not calibration evidence.

4. The most important deposition/runout evidence remains proxy based. Tschamut
   and Mel rows in this matrix come from deposition or trajectory outputs that
   do not yet carry per-trajectory explicit `stop_state`. The Tschamut
   translational/rotational contrast remains visible, but terrain/material
   interpretation would still depend on proxy final speeds and aggregate impact
   counts.

5. The matrix does not yet separate terrain/material effects from contact-rich
   stopping in Tschamut. The public Tschamut diagnostic rows lack per-trajectory
   final contact state, terrain slope near stop, last significant impact, and
   low-energy contact counts.

## Interpretation

This first matrix is useful, but it is not sufficient to justify a
terrain/material implementation slice.

It shows that the additive stop-state instrumentation is ready for small
single-run diagnostics. It also shows that the dataset most relevant to
deposition/runout failure modes, public Tschamut, still lacks explicit
per-trajectory stopping provenance in the generated deposition/ensemble outputs
used here.

Therefore, proceeding directly to material-parameter implementation would be
premature. The next work should close the instrumentation gap for ensembles and
deposition-focused diagnostics before any terrain/material model design.

## Decision

Recommended next package: **additive per-trajectory stop-state aggregation for
ensemble/deposition outputs**.

Do not implement new terrain/material physics yet. Do not calibrate terrain
classes. Do not use Tschamut or Mel as physics-selection evidence.

The next package should:

- record per-trajectory stop-state summaries for generated ensemble/deposition
  outputs;
- aggregate explicit stop-state counts into `run_manifest_v1` where ensembles
  are generated;
- include final slope/normal, final contact state, stop reason, final speed,
  final kinetic energy, low-energy contact count, and last significant impact
  distance per trajectory where feasible;
- update the stopping and terrain/material matrix summarizers to prefer those
  per-trajectory fields;
- rerun only selected diagnostic workflows under ignored result paths.

After that, repeat this matrix. If Tschamut/Mel remain proxy-only for the
fields needed to distinguish stopping from terrain/material behavior, the
project should continue instrumentation or rebound/proxy provenance work rather
than implement material parameters.
