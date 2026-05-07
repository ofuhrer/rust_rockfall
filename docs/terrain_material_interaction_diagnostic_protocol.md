# Terrain/Material Interaction Diagnostic Protocol

Status: no-tuning diagnostic protocol. This document does not change physics,
defaults, validation cases, thresholds, release assumptions, terrain classes,
baselines, public benchmark status, or operational claims.

## Decision

Use the new additive `stop_state` provenance to diagnose terrain/material
interaction hypotheses before adding or calibrating any terrain/material model.

The next scientific question is not "which parameter value fits best?" It is:

> Are the current under-run, over-run, and deposition failures more consistent
> with stopping/terrain-material interaction, rebound/contact proxy mismatch,
> release/registration uncertainty, or missing active shape-contact physics?

This protocol is intended to reduce that ambiguity without changing the model.

## Evidence Basis

Current evidence motivates this protocol:

- Public Tschamut remains diagnostic-only because registration sensitivity
  blocks physics-selection use. It still exposes a strong qualitative contrast:
  `translational_v0` tends toward early under-run, while
  `sphere_rotational_v1` strongly over-runs.
- Chant Sura is the strongest current trajectory/contact evidence. It supports
  `sphere_rotational_v1` for trajectory shape and kinetic-energy experiments,
  but rebound velocity, jump-height envelope, and impact timing remain weak.
- The internal `shape_contact_v0` model-selection run is paused because rebound
  velocity failed the frozen gate and trajectory-to-EOTA shape provenance is not
  auditable.
- Mel de la Niva is useful only as a high-energy/generalization smoke workflow,
  not as field calibration or physics-selection evidence.
- The new `stop_state` instrumentation records explicit stop reason, final
  contact state, terminal speed/energy, low-energy contact count, last
  significant-impact provenance, and terrain normal/slope at the final position
  where available.

## Scope

Allowed:

- read existing checked-in or ignored diagnostic outputs;
- regenerate selected existing diagnostic outputs only to populate additive
  `stop_state` fields;
- summarize and group existing runs by stop-state and terrain/material context;
- use Tschamut and Mel only as diagnostic/non-regression smoke evidence;
- use Chant Sura for contact/trajectory context, not stopping/deposition
  calibration;
- add reports, scripts, and tests that are descriptive only.

Not allowed:

- changing physics, defaults, thresholds, release assumptions, terrain handling,
  validation cases, validation baselines, or benchmark filters;
- adding new material parameters;
- changing terrain-class overrides;
- fitting friction, restitution, roughness, scarring, stopping velocity, or
  class-specific parameter values;
- using Tschamut or Mel de la Niva as physics-selection evidence;
- running held-out Chant Sura for `shape_contact_v0`;
- claiming operational hazard-map validity.

## Diagnostic Inputs

Preferred inputs, in order:

1. Run manifests and validation diagnostics that include explicit `stop_state`.
2. Trajectory CSVs with `contact_state`, speed, kinetic energy, and position.
3. Impact-event CSV/JSON outputs with incoming normal speed and event location.
4. Deposition CSVs with final point, runout, and final speed.
5. Hazard-layer manifests and rasters as downstream spatial diagnostics only.

Legacy outputs without `stop_state` remain usable, but must be labelled as proxy
evidence. The summarizer should prefer explicit `stop_state` fields and fall
back to proxy inference only when necessary.

## Required Groupings

Every diagnostic table should preserve the following grouping keys where
available:

| Grouping key | Purpose |
| --- | --- |
| `dataset_role` | Separate verification, Chant Sura contact, Tschamut diagnostic, Mel smoke, and hazard workflows. |
| `contact_model` | Compare `translational_v0`, `sphere_rotational_v1`, roughness/scarring variants, and paused internal models without mixing semantics. |
| `stop_reason` | Separate explicit stopped states, low-velocity terminal states, `t_max` endings, and unknown/proxy endings. |
| `final_contact_state` | Distinguish airborne endings from contact-dominated endings. |
| `terrain_slope_abs` bins | Test whether stopping/final speed patterns correlate with local slope near the final point. |
| `low_energy_contact_count` bins | Identify repeated low-energy contact/stopping behavior. |
| `impact_count` / `significant_impact_count` bins | Distinguish contact-rich paths from ballistic/rebound-dominated paths. |
| `runout_class` | Keep short/mid/long observed-runout behavior visible without selecting runs post hoc. |
| `block_size_class` / `block_shape_class` | Use passive metadata as grouping only; do not reinterpret it as active shape physics. |
| `terrain_material_assumption_id` | Preserve Phase 1 probabilistic scenario semantics when available. |

Suggested bins must be declared before summary generation. For the first pass,
use coarse, descriptive bins only:

- `terrain_slope_abs`: `flat_to_low`, `moderate`, `steep`, `unknown`;
- `low_energy_contact_count`: `none`, `low`, `high`, `unknown`;
- `impact_count`: `none`, `low`, `high`, `unknown`;
- `final_speed_mps`: `stopped_or_near_stopped`, `moving`, `high_speed`,
  `unknown`.

No bin may be changed after inspecting outcomes unless the report records that
the change is exploratory and not used for decision gates.

## Required Metrics

Minimum per-group metrics:

- trajectory count or deposition-row count;
- final-speed mean, p95, and maximum;
- final kinetic-energy mean and maximum;
- stop-reason counts;
- final contact-state counts;
- low-energy contact-count total and mean;
- impact-event count total and mean;
- significant-impact count total where incoming normal speed is available;
- distance from last significant impact to final position;
- terrain-slope availability and slope-bin counts;
- runout mean, signed runout error, or deposition/runout class when reference
  observations exist;
- explicit instrumentation gaps.

The report must keep metrics descriptive. It must not rank parameter values or
select a new default model.

## Dataset Interpretation Rules

### Verification And Synthetic Cases

Use these to prove diagnostic semantics:

- low-velocity stop;
- `t_max` / max-step termination;
- repeated low-energy impacts;
- airborne unfinished/output-ended state;
- terrain slope/normal availability.

These cases can define expected diagnostic behavior but cannot validate field
realism.

### Chant Sura

Use Chant Sura to contextualize contact and rebound behavior only. Its current
fixtures are short reconstructed trajectory/contact segments, not deposition
or stopping benchmarks. Do not use Chant Sura stopping summaries to tune
terrain/material behavior.

### Tschamut

Use Tschamut only as diagnostic failure-mode evidence. Any terrain/material
interpretation must repeat the registration limitation and must not claim
physics-selection readiness. A valid Tschamut diagnostic can say that a failure
is contact-rich, early-stopping, high-terminal-speed, or slope-associated; it
cannot by itself select a calibrated material model.

### Mel De La Niva

Use Mel de la Niva only as high-energy/generalization smoke evidence unless a
future reviewed runnable benchmark provides stronger trajectory/deposition
provenance. Do not calibrate against Mel smoke outputs.

### Hazard Layers

Use hazard rasters to inspect downstream spatial consequences of existing
trajectory behavior. Hazard layers are not calibration objectives in this
protocol and are not risk maps.

## Stop Conditions

Pause the protocol and do not proceed to terrain/material implementation if:

- explicit stop-state fields are absent from the representative outputs needed
  for the comparison;
- domain-exit or terrain-error modes are needed but still not instrumented;
- ensemble-level stop-state aggregation is required but the relevant
  diagnostics have not been regenerated with `*_stop_state.csv` sidecars and
  `stop_state_summary_v3` manifests;
- the analysis starts changing thresholds or bins after seeing outcomes;
- Tschamut or Mel is being used as physics-selection evidence;
- the result cannot distinguish terrain/material stopping behavior from
  rebound/contact proxy mismatch.

## Success Criteria

The protocol succeeds if it produces a reproducible diagnostic report that:

- uses explicit `stop_state` fields where available;
- identifies whether current failures are dominated by early stopping,
  high-speed terminal motion, repeated low-energy contact, or rebound mismatch;
- separates trajectory/contact evidence from deposition/runout evidence;
- clearly states which datasets support each conclusion;
- recommends one of:
  - terrain/material implementation design;
  - additional stopping instrumentation;
  - rebound/contact-proxy provenance work;
  - continued pause.

## Failure Criteria

The protocol fails if:

- key conclusions depend on proxy-inferred stopping state when explicit
  instrumentation should have been regenerated first;
- grouping or filtering changes after outcomes are known;
- diagnostics require a physics/default/baseline change;
- the report cannot keep calibration, validation, diagnostics, hazard mapping,
  and operational products separate.

## Implementation Slices

### Slice A: Report-Only Diagnostic Matrix

Create a terrain/material diagnostic report from existing outputs and, where
needed, regenerated existing diagnostic cases that write `stop_state`.

No code beyond summarization/reporting should be required.

### Slice B: Stop-State Aggregation Gaps

If Slice A shows that ensemble manifests are insufficient, use the additive
per-trajectory `*_stop_state.csv` sidecars and `stop_state_summary_v3`
manifest aggregates when regenerating selected diagnostics. This remains
instrumentation only.

### Slice C: Terrain/Material Assumption Inventory

Inventory existing terrain-class and material-assumption metadata, including
which fields are provenance labels versus active parameter overrides.

### Slice D: Implementation Decision

Only after Slices A-C should the project decide whether a no-tuning
terrain/material implementation slice is justified. Any implementation must be
opt-in, versioned, documented, and tested against synthetic cases before public
benchmark use.

## Recommended Next Prompt

```text
NEXT TASK - TERRAIN/MATERIAL DIAGNOSTIC MATRIX

Do NOT change physics.
Do NOT tune parameters.
Do NOT change defaults, thresholds, release assumptions, validation cases, or baselines.
Do NOT use Tschamut or Mel de la Niva as physics-selection evidence.
Do NOT run held-out Chant Sura for shape_contact_v0.
Do NOT enable public benchmarks.

Goal:
Generate a no-tuning terrain/material diagnostic matrix using explicit stop_state
fields where available and proxy fallback only when clearly labelled.

Tasks:
1. Review docs/terrain_material_interaction_diagnostic_protocol.md and
   docs/stopping_behavior_diagnostic_report.md.
2. Regenerate only selected existing diagnostic outputs if needed to populate
   additive stop_state fields.
3. Summarize by dataset_role, contact_model, stop_reason, final_contact_state,
   terrain_slope_abs bin, low_energy_contact_count bin, impact_count bin,
   runout class, and available block/terrain-material labels.
4. Produce docs/terrain_material_diagnostic_matrix.md.
5. Conclude whether the next package should be terrain/material implementation
   design, more stop-state instrumentation, rebound/proxy provenance work, or
   continued pause.
6. Run focused tests and documentation/consistency checks only.
```
