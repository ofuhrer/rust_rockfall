# Public Tschamut Model-Improvement Decision

Status: no-tuning scientific decision record after the registered public
Tschamut benchmark. This document does not implement new physics, tune
parameters, change defaults, or change validation semantics.

## Purpose

The public Tschamut benchmark now uses `scan_surface_fit_v1` registration
between public LPS trajectory coordinates and the public CH1903 slope scan, then
runs against a public swissALTI3D 2 m terrain crop. The 10-run and 25-run
subsets give the same broad result:

- `translational_v0` under-runs by about 30 m;
- `sphere_rotational_v1` over-runs strongly;
- registration is no longer the dominant explanation for the mismatch;
- no restitution, friction, roughness, scarring, terrain-class, or release
  parameters have been tuned.

This decision asks what the next no-tuning scientific implementation should be:
a shape-aware scaffold, a terrain/material calibration design, more predefined
model comparisons, more data expansion, better metrics, or GIS-focused work.

## Evidence Reviewed

Primary inputs:

- `docs/tschamut_public_benchmark_reproduction.md`
- `docs/contact_model_decision.md`
- `docs/chant_sura_contact_validation.md`
- `docs/chant_sura_contact_generalization.md`
- `docs/current_state_gap_analysis_next_directions.md`
- `docs/model_design.md`
- `docs/dataset_strategy.md`

Key evidence:

- Chant Sura model-selection, extended, and held-out contact fixtures support
  `sphere_rotational_v1` as the recommended opt-in model for trajectory/contact
  experiments because it improves trajectory-shape and kinetic-energy metrics.
- The same Chant Sura evidence does not support changing defaults: rebound
  velocity, jump-height envelope, and impact timing do not improve uniformly.
- Public Tschamut deposition/runout does not favor either current spherical
  mode as a robust field-deposition model. The default under-runs and the
  rotational sphere over-runs.
- Scarring and roughness comparisons remain useful diagnostics, but current
  no-tuning variants have not resolved the main trajectory/deposition mismatch.
- Terrain/material effects and shape effects are still confounded in Tschamut:
  real terrain is now registered well enough for controlled comparison, but the
  model still uses equivalent spheres and globally chosen parameters.

## Interpretation

The two datasets constrain different failure modes:

- Chant Sura is the stronger trajectory/contact dataset. It says rotational
  energy exchange matters, but it also exposes missing rebound/contact fidelity.
- Tschamut is the stronger deposition/runout dataset. It says the current
  spherical models do not transfer cleanly to field deposition, even with better
  registration and public terrain.

These are not contradictory. They imply that adding spherical rotation is a
useful but incomplete step. The remaining gap is structural: terrain/material
parameterization and non-spherical block behaviour are both plausible causes of
the Tschamut mismatch. A pure parameter search would risk fitting one dataset
before the model has the state variables needed to represent shape-dependent
rolling, tumbling, lateral spread, and energy partitioning.

## Candidate Directions

| Direction | Scientific value | Overfitting risk | Complexity | Data dependency | State-of-practice relevance | No-tuning testability |
| --- | --- | --- | --- | --- | --- | --- |
| Minimal shape-aware scaffold | Very high: addresses equivalent-sphere limitations exposed by Chant Sura and Tschamut. | Medium if evaluated only on Tschamut; lower if scaffold starts with diagnostics and verification. | High, but can be staged. | Needs shape metadata and carefully selected validation cases. | Directly addresses the largest block-representation gap relative to mature 3D rockfall tools. | Good if implemented as opt-in scaffold with fixed shape inputs and no fitted parameters. |
| Terrain/material calibration protocol | High: targets terrain-class parameter uncertainty and runout bias. | High if started before a held-out calibration design exists. | Medium-high. | Requires training/held-out split, terrain class provenance, and calibration policy. | Directly relevant to field hazard modelling. | Moderate: the protocol can be designed now, but calibration should not run yet. |
| Roughness/scarring predefined no-tuning comparison | Medium: cheap diagnostic of existing mechanisms. | Low if parameters are fixed before execution. | Low. | Uses existing public benchmark and existing configs. | Limited; these are simplified mechanisms, not full field terrain laws. | Excellent, but unlikely to resolve structural mismatch alone. |
| Expand to more public Tschamut runs | Medium: improves stability and block/run coverage. | Low. | Low-medium. | Public processed subset has 80 shared rows; full expansion may need outlier review. | Useful evidence, but does not close a physics gap by itself. | Excellent. |
| Improve validation metrics before physics | Medium-high: better separates runout, lateral spread, energy, impact count, and group effects. | Low. | Medium. | Needs consistent observed trajectory/deposition grouping. | Improves credibility of all model comparisons. | Excellent. |
| GIS/GeoTIFF output | High engineering value, low immediate scientific value. | Low. | Medium. | Needs stable reference grids and GIS review workflow. | Important for hazard-map usability, not the current physics decision. | Good, but orthogonal to model-improvement choice. |

## Ranking

1. **Minimal shape-aware scaffold.**
   This is the highest-value scientific implementation because it addresses the
   most obvious missing state: shape, orientation, inertia, and contact-point
   dependence. The public Tschamut result shows spherical rotation alone can
   overshoot deposition/runout, while Chant Sura shows rotational coupling still
   improves trajectory/energy diagnostics. A scaffold can be tested without
   tuning if it starts with shape metadata, mass properties, orientation state,
   and verification cases before complex contact laws.

2. **Improve validation metrics before physics.**
   This is the safest companion work. It should define how future shape-aware or
   terrain/material experiments are judged: grouped runout errors, lateral
   spread, deposition overlap, energy/jump exceedance, impact counts, block
   class effects, and per-trajectory failure modes. It reduces the risk of
   overinterpreting one aggregate runout metric.

3. **Terrain/material calibration protocol.**
   This is scientifically important but should be designed before it is used.
   Actual calibration should wait until there is a held-out split and a clear
   decision about which parameters are physically identifiable from Tschamut,
   Chant Sura, and scarring data.

4. **Roughness/scarring predefined no-tuning comparison.**
   This is low-risk and useful as a diagnostic, but existing evidence suggests
   these mechanisms alone are unlikely to resolve the main mismatch. It should
   be run as a table in a future model-comparison report, not treated as the
   primary model-improvement direction.

5. **Expand to more public Tschamut runs.**
   The 25-run expansion already confirms the 10-run conclusion. Expanding to
   all 80 shared runs is useful for robustness and outlier discovery, but it is
   now a support task rather than the critical next scientific implementation.

6. **GIS/GeoTIFF output.**
   This should remain a medium-term engineering step. It improves inspection and
   workflow maturity but does not explain why one spherical model under-runs and
   the other over-runs.

## Decision

Recommended next scientific work package:

> Implement a **minimal opt-in shape-aware scaffold**, paired with stricter
> validation-metric definitions, and evaluate it only through predefined,
> no-tuning model-comparison cases.

The first shape-aware slice should avoid a full contact-solver jump. It should
establish:

- shape metadata ingestion for public EOTA/field-shape records where available;
- mass, centre, principal dimensions, and inertia diagnostics;
- an orientation state representation;
- deterministic integration bookkeeping for orientation without changing the
  default sphere path;
- verification fixtures for mass properties and rigid-body state propagation;
- a clear boundary saying that contact still uses existing sphere behaviour
  until a later, separately reviewed shape-contact model is implemented.

This work package is valuable even before full shape contact because it gives
the repository a tested place to carry block geometry, inertia, and orientation
through validation workflows. It also makes the next contact-model extension
less likely to become an unreviewable physics rewrite.

## Deferred Alternative

Deferred alternative: **terrain/material calibration protocol and parameter
search**.

Reason for deferral:

- Tschamut can show deposition/runout bias, but it cannot by itself identify
  whether the missing mechanism is terrain material, roughness, shape, forest or
  vegetation context, release uncertainty, or contact law structure.
- Starting calibration now would risk fitting global restitution/friction or
  terrain-class parameters to compensate for missing shape dynamics.
- The protocol should still be designed soon, but actual calibration should
  wait for a held-out split, predefined objective functions, and explicit
  parameter-identifiability assumptions.

## Supporting Work To Do Alongside Shape

Do next, but keep separate from the shape scaffold:

- define a no-tuning model-comparison matrix for public Tschamut:
  `translational_v0`, `sphere_rotational_v1`, fixed roughness, fixed scarring,
  and future shape scaffold variants;
- add grouped validation summaries for block ID, mass/radius, runout quantiles,
  deposition overlap, lateral spread, and observed/simulated outliers;
- preserve the current 10-run and 25-run public benchmark outputs as reference
  summaries in the report, while keeping generated artifacts ignored;
- use Chant Sura as the primary trajectory/contact check and Tschamut as the
  deposition/runout check.

## Explicitly Deferred

- Changing the default contact model.
- Tuning restitution, friction, roughness, scarring, terrain-class, or release
  parameters to Tschamut.
- Claiming operational validity or equivalence to any proprietary model.
- Implementing full polyhedral/nonsmooth contact in one step.
- Adding GIS/GeoTIFF export as the next scientific model-improvement task.
- Further performance or data-format optimization for this decision.

## Success Criteria For The Next Work Package

The shape-aware scaffold is successful if it:

- preserves existing default numerical behaviour exactly;
- exposes shape/orientation metadata without forcing a contact-law change;
- has analytic tests for mass properties and deterministic orientation state;
- can be attached to Chant Sura/Tschamut cases as metadata for reporting;
- makes the next shape-contact decision more constrained and auditable.

It is not expected to improve Tschamut runout immediately until shape-dependent
contact is introduced and evaluated in a later no-tuning comparison.

