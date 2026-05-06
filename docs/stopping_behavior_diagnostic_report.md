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
| `source_kind` | `trajectory_csv`, `deposition_csv`, or `run_manifest_v1`. | script input |
| `dataset_role` | Diagnostic role such as verification, Chant Sura, Tschamut diagnostic, or Mel smoke. | inferred from path/label |
| `contact_model` | Contact-model label inferred from path/label. | inferred from path/label |
| `trajectory_count` | Number of trajectories or deposition rows summarized. | output rows / manifest |
| `final_status_counts` | Final `contact_state` counts when trajectory rows are available. | trajectory CSV |
| `stop_reason_counts` | Conservative inferred stop/status reason. | trajectory/deposition CSV |
| `final_speed_mean_mps`, `final_speed_p95_mps`, `final_speed_max_mps` | Final speed summary. | trajectory/deposition CSV |
| `final_kinetic_mean_j`, `final_kinetic_max_j` | Final translational kinetic-energy summary. | trajectory CSV |
| `impact_count_total`, `impact_count_mean` | Count of rows with `contact_state == impact`, or aggregate manifest impact count. | trajectory CSV / manifest |
| `significant_impact_count_total` | Proxy count of impact rows with `speed_mps >= 0.05`. | trajectory CSV |
| `low_energy_contact_count_total` | Contact rows with `speed_mps <= 0.05`. | trajectory CSV |
| `distance_last_significant_impact_to_final_mean_m`, `..._max_m` | Horizontal distance from last significant-impact proxy to final point. | trajectory CSV |
| `runout_mean_m`, `runout_max_m` | Runout summary when deposition rows are available. | deposition CSV |
| `terrain_slope_near_stop_available` | Whether terrain slope/normal near stop was directly available. | currently false |
| `instrumentation_gaps` | Explicit limits for each source. | script output |

Important: `stop_reason_counts` and `significant_impact_count_total` are proxy
diagnostics. Current outputs do not contain an explicit simulator stop-reason
field, nor do trajectory CSV rows contain incoming normal speed. The script
therefore does not claim exact physical stop modes.

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

Missing or weak fields:

- explicit simulator stop reason;
- whether the run ended because of low velocity, max steps, domain exit, or
  output truncation;
- per-row incoming normal speed in trajectory CSVs;
- terrain slope and terrain normal at final stop;
- last significant impact information in deposition rows;
- distance from last significant impact to final deposition point for ensemble
  deposition outputs unless full trajectory or impact-event directories are
  scanned;
- normalized per-trajectory impact summaries in manifests.

These are instrumentation gaps, not reasons to tune parameters.

## Recommendation

Next scientific package: stopping instrumentation, then terrain/material
interaction protocol.

Do not proceed directly to terrain/material calibration yet. The current
diagnostic summary shows that stopping/runout differences are central, but the
outputs do not yet record enough per-trajectory stop-state provenance to
separate low-speed physical stopping, output truncation, domain exit, repeated
small impacts, and terrain/material effects.

The next implementation should therefore add additive stop-state provenance to
manifests and/or trajectory summaries without changing dynamics:

- explicit `stop_reason`;
- final contact state;
- final speed and kinetic energy;
- last significant impact time/location;
- distance from last significant impact to final position;
- terrain normal/slope at final position where terrain is available;
- low-energy contact counts;
- domain/max-step/low-velocity termination flags.

Only after those fields exist should a terrain/material interaction protocol be
designed. That protocol must remain no-tuning until a reviewed calibration
split and acceptance criteria exist.

## Decision

`shape_contact_v0` remains paused. Held-out Chant Sura remains blocked. Public
Tschamut and Mel de la Niva remain diagnostic/non-regression evidence only.

Immediate next direction: additive stopping instrumentation, not new physics.
