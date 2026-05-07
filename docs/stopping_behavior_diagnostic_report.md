# Stopping-Behavior Diagnostic Report

Status: no-tuning diagnostic package. This report does not change physics,
defaults, thresholds, release assumptions, validation cases, baselines, public
benchmark status, or operational claims.

## Scope

This package inspects existing local outputs only. It does not run public
benchmarks, does not run held-out Chant Sura for `shape_contact_v0`, and does
not use Tschamut or Mel de la Niva as physics-selection evidence.

The diagnostic summarizer is:

```bash
python3 scripts/summarize_stopping_behavior.py
```

The local diagnostic summary was generated under ignored results:

- `validation/results/stopping_behavior_diagnostics/summary.csv`
- `validation/results/stopping_behavior_diagnostics/summary.md`

Those generated files are reproducible local diagnostics and are not intended
for git.

## Diagnostic Schema

The additive stopping-diagnostic schema records:

| Field | Meaning | Current source |
| --- | --- | --- |
| `source_label` | Human-readable input label. | script input |
| `source_kind` | `trajectory_csv`, `deposition_csv`, `ensemble_stop_state_csv`, `run_manifest_v1`, or `run_manifest_stop_state_summary_v1`. | script input |
| `dataset_role` | Diagnostic role such as verification, Chant Sura, Tschamut diagnostic, or Mel smoke. | inferred from path/label |
| `contact_model` | Contact-model label inferred from path/label. | inferred from path/label |
| `trajectory_count` | Number of trajectories or deposition rows summarized. | output rows / manifest |
| `final_status_counts` | Final `contact_state` counts when trajectory rows are available. | trajectory CSV |
| `explicit_stop_state_available` | Whether explicit simulator stop-state records were available. | run manifest / stop-state sidecar |
| `stop_reason`, `final_contact_state` | Explicit stop reason and final contact state when instrumented. | run manifest |
| `termination_low_velocity`, `termination_max_steps`, `termination_t_max`, `termination_domain_exit`, `termination_terrain_error` | Explicit termination flags when instrumented. | run manifest |
| `stop_reason_counts` | Explicit stop reason when present, otherwise conservative inferred stop/status reason. | manifest / trajectory/deposition CSV |
| `final_speed_mean_mps`, `final_speed_p95_mps`, `final_speed_max_mps` | Final speed summary. | trajectory/deposition/stop-state CSV |
| `final_kinetic_mean_j`, `final_kinetic_max_j` | Final translational kinetic-energy summary. | trajectory/stop-state CSV |
| `impact_count_total`, `impact_count_mean` | Count of rows with `contact_state == impact`, or aggregate manifest impact count. | trajectory CSV / manifest |
| `significant_impact_count_total` | Proxy count of impact rows with `speed_mps >= 0.05`. | trajectory CSV |
| `low_energy_contact_count_total` | Contact rows with `speed_mps <= 0.05`, or explicit low-energy contact count. | trajectory CSV / stop-state sidecar |
| `distance_last_significant_impact_to_final_mean_m`, `..._max_m` | Horizontal distance from last significant-impact proxy or explicit significant-impact record to final point. | trajectory CSV / stop-state sidecar |
| `runout_mean_m`, `runout_max_m` | Runout summary when deposition rows are available. | deposition CSV |
| `terrain_normal_x`, `terrain_normal_y`, `terrain_normal_z`, `terrain_slope_abs` | Terrain normal/slope at the final position when instrumented. | run manifest |
| `terrain_slope_near_stop_available` | Whether terrain slope/normal near stop was directly available. | manifest / script output |
| `instrumentation_gaps` | Explicit limits for each source. | script output |

Important: `stop_reason_counts` and `significant_impact_count_total` are proxy
diagnostics when generated from legacy trajectory/deposition CSVs. New
run-manifest `stop_state` records and ensemble stop-state sidecars provide
explicit stop reason, final contact state, termination flags, final
speed/kinetic energy, low-energy contact count, last significant-impact
provenance when present, and final terrain normal/slope. The summarizer prefers
those explicit fields and falls back to proxy inference for older outputs.

## Additive Instrumentation

The simulator now emits optional `stop_state` provenance on single-run
simulation results, validation diagnostics, and run manifests. This is an
additive reporting field only: it does not change contact physics, stopping
thresholds, defaults, validation cases, or baselines.

The explicit stop-state record includes:

- `stop_reason` and `final_contact_state`;
- `final_speed_mps` and `final_kinetic_j`;
- termination flags for `low_velocity`, `max_steps`, `t_max`,
  `domain_exit`, and `terrain_error`;
- last significant impact time/location and horizontal distance to the final
  position when an impact exceeds the explicit incoming-normal-speed threshold;
- `low_energy_contact_count`;
- terrain normal and terrain slope at the final position when terrain is
  available.

Current domain-exit and terrain-error flags remain false because the fixed-step
integrator does not yet expose those termination modes as separate outcomes.

For validation cases that already write ensemble/deposition CSV outputs, the
runner now writes an additive `*_stop_state.csv` sidecar and records a
`stop_state_summary_v1` object in the run manifest. The sidecar is diagnostic
only and does not change deposition values, metrics, baselines, or acceptance
criteria. Legacy manifests without `stop_state_summary` remain readable.

## Evidence Inspected

The local diagnostic run inspected these existing outputs:

| Source | Role | Output type |
| --- | --- | --- |
| `verification/results/analytic_inclined_slide_stop.csv` | synthetic/verification | trajectory CSV |
| `verification/results/regime_repeated_low_energy_impacts.csv` | synthetic/verification | trajectory CSV |
| `verification/results/regime_slide_to_stop_transition.csv` | synthetic/verification | trajectory CSV |
| `validation/results/chant_sura_contact_trajectory.csv` | Chant Sura model-selection diagnostic | trajectory CSV |
| `validation/results/chant_sura_contact_rotational_trajectory.csv` | Chant Sura model-selection diagnostic | trajectory CSV |
| `validation/results/public_benchmarks/mel_de_la_niva_runnable/validation/validation_mel_de_la_niva_baseline_trajectory.csv` | Mel smoke only | trajectory CSV |
| `validation/results/public_benchmarks/mel_de_la_niva_runnable/validation/validation_mel_de_la_niva_rotational_trajectory.csv` | Mel smoke only | trajectory CSV |
| `validation/results/tschamut_public_benchmark_all/validation/validation_tschamut_public_benchmark_baseline_deposition.csv` | Tschamut diagnostic only | deposition CSV |
| `validation/results/tschamut_public_benchmark_all/validation/validation_tschamut_public_benchmark_rotational_deposition.csv` | Tschamut diagnostic only | deposition CSV |
| `validation/results/tschamut_public_benchmark_all/validation/validation_tschamut_public_benchmark_baseline_manifest.json` | Tschamut diagnostic only | run manifest |
| `validation/results/tschamut_public_benchmark_all/validation/validation_tschamut_public_benchmark_rotational_manifest.json` | Tschamut diagnostic only | run manifest |

## Summary Results

| Source | Contact model | Trajectories | Final status / reason | Final speed mean (m/s) | Runout mean (m) | Impact count |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| verification inclined slide | translational | 1 | explicit stopped | 0.000 | n/a | 0 |
| verification repeated low-energy impacts | translational | 1 | final speed below threshold proxy | 0.003 | n/a | 664 |
| verification slide-to-stop | translational | 1 | explicit stopped | 0.000 | n/a | 0 |
| Chant Sura contact | translational | 1 | output ended airborne | 5.121 | n/a | 10 |
| Chant Sura contact | spherical rotational | 1 | output ended airborne | 5.867 | n/a | 9 |
| Mel de la Niva smoke | translational | 1 | output ended airborne | 5.408 | n/a | 1306 |
| Mel de la Niva smoke | spherical rotational | 1 | output ended while in contact state | 149.785 | n/a | 1496 |
| Tschamut all-runs | translational | 480 deposition rows | 451 final speeds above threshold, 29 below threshold proxy | 0.312 | 63.398 | manifest aggregate: 248235 |
| Tschamut all-runs | spherical rotational | 480 deposition rows | 480 final speeds above threshold | 6.725 | 202.953 | manifest aggregate: 71729 |

## Key Findings

1. Verification cases prove that the current outputs can distinguish explicit
   stopped states, low-speed terminal states, and repeated low-energy impact
   behavior in synthetic settings.

2. Chant Sura model-selection trajectory outputs end airborne with nonzero
   speed for both current public models. They are contact/rebound diagnostic
   segments, not stopping/deposition tests. This supports keeping Chant Sura as
   trajectory/contact evidence, not as a stopping-behavior benchmark.

3. Public Tschamut all-runs diagnostic deposition outputs show a large contrast
   between current models:

   - translational final-speed mean is `0.312 m/s`, with `29 / 480` deposition
     rows below the `0.05 m/s` proxy threshold and mean runout `63.398 m`;
   - spherical rotational final-speed mean is `6.725 m/s`, with `480 / 480`
     deposition rows above the proxy threshold and mean runout `202.953 m`.

   This supports the existing interpretation that translational behavior tends
   toward early stopping/under-run, while spherical rotation can carry high
   terminal speeds and broad over-run. Tschamut remains diagnostic only because
   registration sensitivity still blocks physics-selection use.

4. Tschamut manifests record aggregate impact-event counts:

   - translational: `248235`;
   - spherical rotational: `71729`.

   The aggregate count is useful for workload and contact-density diagnostics,
   but it cannot by itself explain per-trajectory stopping because manifest
   fields do not contain final state, last significant impact, or stop reason.

5. The local Mel de la Niva runnable smoke outputs show high-energy behavior
   and nonzero terminal speeds, especially for the rotational smoke trajectory.
   This is useful as a non-explosion/generalization smoke signal only; it is not
   calibrated field validation or physics-selection evidence.

## Instrumentation Gaps

Existing outputs are sufficient for a first additive diagnostic summary, but
not for a complete stopping-behavior interpretation.

Missing or weak fields in legacy/generated summary inputs:

- explicit simulator stop reason in older outputs without manifest `stop_state`;
- per-row incoming normal speed in trajectory CSVs;
- last significant impact information in deposition rows;
- distance from last significant impact to final deposition point for legacy
  ensemble deposition outputs that predate the `*_stop_state.csv` sidecar;
- normalized per-trajectory impact summaries beyond the explicit stop-state
  fields;
- explicit domain-exit and terrain-error termination modes from the integrator.

These are instrumentation gaps, not reasons to tune parameters.

## Recommendation

Next scientific package: terrain/material interaction protocol using the new
stopping instrumentation.

Do not proceed directly to terrain/material calibration yet. The current
diagnostic summary shows that stopping/runout differences are central. The new
explicit provenance makes low-speed stopping, output truncation, repeated small
contacts, and terrain slope near stop easier to separate, while domain-exit and
terrain-error termination modes still need future integrator exposure.

The next implementation should use the additive stop-state provenance to design
a terrain/material interaction protocol. That protocol must remain no-tuning
until a reviewed calibration split and acceptance criteria exist, and it should
not use Tschamut or Mel de la Niva as physics-selection evidence.

## Decision

`shape_contact_v0` remains paused. Held-out Chant Sura remains blocked. Public
Tschamut and Mel de la Niva remain diagnostic/non-regression evidence only.

Immediate next direction: no-tuning terrain/material interaction protocol, not
new physics or calibration.
