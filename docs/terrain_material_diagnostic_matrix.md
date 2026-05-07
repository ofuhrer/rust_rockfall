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

The matrix can be reproduced from existing local diagnostic outputs. The latest
sidecar refresh reran only the selected small Swiss smoke cases needed to
populate additive ensemble stop-state sidecars:

```bash
cargo run -- validate --case validation/cases/performance_smoke.yaml
cargo run -- validate --case validation/cases/swissalti3d_release_zone_terrain_classes_pilot.yaml
```

Earlier verification and Chant Sura diagnostics are consumed as existing local
outputs. Tschamut and Mel de la Niva outputs are not regenerated here and remain
diagnostic/proxy evidence only.

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
  --stop-state synthetic_swiss_performance_stop_state:validation/results/performance_smoke_deposition_stop_state.csv \
  --stop-state synthetic_swiss_terrain_classes_stop_state:validation/results/swissalti3d_terrain_class_deposition_stop_state.csv \
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
| Synthetic Swiss hazard/smoke manifest summary | `translational_v0` | explicit `stop_state_summary_v3` | `t_max_reached_in_contact_state` | `impact` | unknown | none | high | moving | unknown | 8 | 0.878 |
| Synthetic Swiss hazard/smoke sidecar | `translational_v0` | explicit `ensemble_stop_state_csv` | `t_max_reached_in_contact_state` | `impact` | unknown | none | unknown | moving | short | 8 | 0.878 |
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

1. Explicit `stop_state` works for single-run diagnostics, run manifests, and
   generated ensemble/deposition sidecars. The verification rows distinguish
   explicit stopped states, low-speed terminal repeated-impact behavior, and
   `t_max`/contact-state termination.

2. Chant Sura contact rows now have explicit `stop_state`, but they end
   airborne with high terminal speed. This reinforces the existing
   interpretation that Chant Sura is a trajectory/contact benchmark, not a
   deposition or stopping benchmark.

3. The synthetic Swiss smoke rows now provide explicit ensemble-level
   stop-state sidecars. Both the baseline Swiss smoke and terrain-class smoke
   cases end as `t_max_reached_in_contact_state` with final `impact` state,
   mean final speed about `0.878 m/s`, no low-energy contacts, and short runout
   in the sidecar rows. This proves the reporting path can carry per-trajectory
   stop reason, final contact state, final speed/kinetic energy, runout, and
   terrain-normal/slope availability for generated ensembles. The fixtures are
   synthetic and are not calibration evidence.

4. The most important field-scale deposition/runout evidence remains proxy
   based. Tschamut and Mel rows in this matrix come from existing deposition or
   trajectory outputs that do not yet carry per-trajectory explicit
   `stop_state`. The Tschamut translational/rotational contrast remains
   visible, but terrain/material interpretation would still depend on proxy
   final speeds and aggregate impact counts.

5. The matrix does not yet separate terrain/material effects from contact-rich
   stopping in Tschamut. The public Tschamut diagnostic rows lack per-trajectory
   final contact state, terrain slope near stop, last significant impact, and
   low-energy contact counts.

## Interpretation

This refreshed matrix is useful, but it is not sufficient to justify a
terrain/material implementation slice.

It shows that the additive stop-state instrumentation is ready for small
single-run diagnostics and generated ensemble/deposition sidecars. It also
now has a direct path for final-stop and last-significant-impact class grouping
when configured terrain-class metadata exists. It also shows that the dataset
most relevant to deposition/runout failure modes, public Tschamut, still lacks
explicit per-trajectory stopping provenance in the generated deposition outputs
used here.

Therefore, proceeding directly to material-parameter implementation would be
premature. The instrumentation gap for generated ensemble/deposition outputs
has been closed for newly generated smoke/ensemble workflows, but the
field-scale diagnostic evidence remains proxy-limited.

## Decision

Recommended next package: **terrain/material implementation design should
remain deferred; choose between targeted public-diagnostic regeneration for
explicit stop-state sidecars and rebound/contact-proxy provenance work**.

Do not implement new terrain/material physics yet. Do not calibrate terrain
classes. Do not use Tschamut or Mel as physics-selection evidence.

The next package should not add material parameters yet. It should either:

- run a reviewed, diagnostic-only regeneration path that adds explicit
  stop-state sidecars to selected Tschamut/Mel outputs without changing filters,
  transforms, defaults, baselines, or physics-selection status; or
- continue rebound/contact-proxy provenance work if the required field-scale
  regeneration is too expensive or still scientifically ambiguous.

If the field-scale rows remain proxy-only or cannot distinguish
stopping/contact behavior from terrain/material behavior, the project should
continue instrumentation or rebound/proxy provenance work rather than implement
material parameters.
