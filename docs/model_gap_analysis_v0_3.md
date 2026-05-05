# Model Gap Analysis v0.3.0

This document compares the current independent `v0.3.0` model with the public theory available in the RAMMS::Rockfall manual, Leine et al. 2014, Leine et al. 2021, and Lu et al. 2019. It does not claim RAMMS equivalence and does not define proprietary implementation details.

Implementation status: the first minimal opt-in soil interaction layer from this roadmap is implemented in `v0.4.0` as `scarring_contact_v1`. It covers impact-local scar-depth diagnostics and bounded translational energy loss only; slip-dependent friction, drag torque, terrain classes, and calibration remain future work.

## Theory Baseline

### State And Degrees Of Freedom

RAMMS and the Leine/Lu rigid-body literature model the rock as a 3D rigid body with translational and rotational motion. The public RAMMS manual describes six primary velocity states: three translational and three rotational. Leine et al. 2014 and Lu et al. 2019 formulate generalized coordinates with position plus quaternion orientation and generalized velocity with linear velocity plus angular velocity.

Rotation is not a minor diagnostic in these models. It determines contact-point velocity, moment arms, torque, rebound direction, rolling/skipping behavior, energy partition, and lateral dispersion. Leine et al. 2021 further shows that rotational stability, including major/intermediate/minor principal-axis behavior, can affect runout and lateral spreading for non-spherical rocks.

### Motion Regimes

The literature consistently separates free flight, sliding, rolling, bouncing/skipping, and stopping. RAMMS frames realistic behavior as transitions among sliding, rolling, skipping, and jumping. Lu et al. 2019 further decomposes a soft-soil impact into scarring, sliding on a rebound plane, and rebound out of the scar.

For hazard-relevant trajectories, the transitions matter as much as the individual equations: long runout is often associated with repeated jumping/skipping or stable rolling, while stopping generally requires transition into rolling/sliding with sufficient dissipation.

### Contact Modeling

The current open literature distinguishes three broad contact families:

- restitution models: simple normal/tangential rebound factors, often stochastic;
- penalty models: compliant spring/dashpot-style contact with regularized friction;
- nonsmooth hard-contact models: unilateral constraints, Coulomb friction, impact laws, and possible multiple active contact points.

Leine et al. 2014 argues for nonsmooth hard-contact dynamics because it can represent impenetrability, sticking/sliding transitions, Coulomb friction, and multi-contact impulses without mixing numerical stiffness with physical material parameters. RAMMS uses this family conceptually: contact forces act at rock surface points, include moment arms, and are coupled to rotation and orientation.

### Energy Dissipation

The public sources identify multiple dissipation paths:

- restitution loss during rebound;
- Coulomb friction during sliding/contact;
- slip-dependent friction from material accumulation in a scar;
- velocity-squared scarring drag in compactable soil;
- drag torques due to partial immersion and rotation;
- vegetation/tree interaction and fragmentation in later model layers.

Lu et al. 2019 is especially relevant because it explains why effective restitution coefficients are limited for soft compactable soils: plastic deformation, scar depth, soil strength, impact angle, mass, shape, and rotation all influence energy loss.

### Terrain And Soil

RAMMS and Leine et al. 2014 assume DEM-based terrain as a primary model input. DEM resolution controls slope geometry and contact normals, while soil/material categories control scarring and drag parameters. The RAMMS manual separates terrain geometry from soil categories such as surface soil, talus, bedrock, boulder fields, forest soil, swamp, and snow. It also states that DEM sub-grid roughness remains a limitation if unresolved.

### Rock Representation

RAMMS and Leine et al. 2014 use convex polyhedral rock shapes. Shape controls contact points, contact normals, torque arms, rotational stability, rebound direction, runout, and lateral spread. Leine et al. 2014 explicitly contrasts point/sphere models with complex-shape rigid bodies; spheres are computationally simple but cannot represent shape-dependent stopping and gyroscopic behavior. Leine et al. 2021 adds that numerically correct rotation stability is important for platy and wheel-like motion.

## Current v0.3.0 Mapping

| Aspect | Implemented | Simplified | Missing |
| --- | --- | --- | --- |
| State | position, velocity, angular velocity diagnostics; opt-in sphere rotational contact | no orientation state for non-spherical bodies | quaternion orientation, inertia tensor for arbitrary shapes, principal-axis stability |
| Terrain | analytic terrain, strict DEM, opt-in clamped DEM, Tschamut IDW residual proxy | small ASCII grids, bilinear interpolation, simple boundary clamping | production DEM workflow, terrain classes, spatially varying material properties |
| Contact | restitution plus Coulomb friction; opt-in sphere rotational impulse | single contact point, fixed-step projection, constant coefficients | nonsmooth multi-contact solve, shape-dependent contact pairs, slip/stick complementarity |
| Motion regimes | airborne, impact, sliding, rolling/stopped diagnostics | rolling only for sphere model; Tschamut still uses translational default | physically complete sliding/rolling/jumping transitions for general shapes |
| Dissipation | restitution, Coulomb friction, rolling resistance, stochastic contact roughness | coefficients are global and mostly generic | scarring drag, slip-dependent friction state, terrain/soil-dependent parameters, drag torques |
| Rock shape | sphere | no orientation-dependent geometry | convex polyhedra, scanned shapes, shape classes |
| Stochasticity | deterministic release and contact perturbations | roughness is impact-local, not spatial | calibrated roughness fields or terrain material variability |

The current model is therefore coherent for analytic verification and controlled spherical experiments, but it remains closer to STONE/Rockyfor-style simplified trajectory models than to full RAMMS/Leine nonsmooth rigid-body simulation.

## Tschamut Mismatch Through The Theory Lens

The active Tschamut comparison now shows about `31 m` mean runout underestimation for both the fitted-plane comparison and the IDW residual DEM case. The IDW terrain changes deposition-cloud structure but does not resolve the mean-runout gap. The earlier `60.9 m` mismatch was partly a preprocessing/release-height artifact, not purely missing physics.

The remaining mismatch is best interpreted as a combination of structural model gaps:

- **Terrain realism remains limited.** The IDW residual DEM is not an official field DEM, is coarse at `5 m`, and uses clamped boundaries. It improves transparency but not necessarily contact realism.
- **Global restitution/friction coefficients are doing too much work.** Literature models separate geometry, hard contact, scarring, soil strength, and drag; v0.3.0 compresses most dissipation into restitution/friction/roughness.
- **The validation case does not yet use the rotational contact model.** Current Tschamut validation remains `translational_v0`, so angular momentum and rolling energy are not active there.
- **Spherical shape is a major structural limitation.** Public experiments and the RAMMS manual emphasize shape class for runout and lateral spread. A sphere cannot represent platy wheel-like motion, blocky tumbling, or contact-point switching.
- **Scarring/soil interaction is absent.** If Tschamut impacts involve compactable grass/talus/soil layers, a restitution-only model cannot distinguish low-loss hard rebounds from high-loss scarring contacts in a physically interpretable way.

Scarring drag does not automatically explain the current under-runout, because drag is dissipative and could shorten trajectories if added naively. Its value is different: it would separate terrain-material dissipation from arbitrary restitution/friction tuning and expose when the current mismatch is caused by contact energy partition rather than by terrain geometry alone.

## Ranked Candidate Improvements

### 1. Terrain/Soil Interaction v1: Scarring Layer And Slip-Dependent Friction

Expected impact: high for energy-budget realism, impact interpretation, and calibration discipline.

Complexity: moderate for a sphere-only, opt-in implementation; much lower than polyhedral nonsmooth contact.

Architecture fit: good. It can extend contact parameters and diagnostics without changing terrain geometry or requiring new core dependencies.

Validation potential: good. Lu et al. 2019 and public SLF/WSL datasets provide scarring, impact, velocity, and runout contexts. Even where scar dimensions are unavailable, the model can report interpretable inferred scar depth/drag diagnostics.

Main risk: if used without calibration, added drag can worsen under-runout. It must remain opt-in and separately calibrated.

### 2. Shape Class / Convex Polyhedron Scaffold

Expected impact: very high for runout, lateral spread, rolling/skipping, and experimental realism.

Complexity: high. It requires orientation integration, inertia tensors, contact detection against terrain, multiple contact points, and much broader verification.

Architecture fit: medium. Existing modules can host it, but the state/contact/integrator layers would need substantial expansion.

Validation potential: very high for Chant Sura and shape-sensitive datasets.

Reason not selected now: too large for the next incremental step and likely to destabilize the verified sphere model.

### 3. Use `sphere_rotational_v1` In Tschamut Calibration/Validation

Expected impact: medium to high for runout and rolling behavior.

Complexity: low to moderate because the mechanics already exist.

Architecture fit: excellent.

Validation potential: moderate. It tests whether the current sphere rotational model helps before adding new physics.

Reason not selected as the primary new model improvement: it is an experiment with existing physics, not the largest missing mechanism from the RAMMS/Leine/Lu comparison.

### 4. Improved Impact Event Localization

Expected impact: medium for rebound-height and impact-time accuracy.

Complexity: moderate, especially for DEM terrain.

Architecture fit: good.

Validation potential: mostly analytic/numerical.

Reason not selected: improves numerical timing but does not add missing physical dissipation or shape mechanisms.

### 5. Full Nonsmooth Hard-Contact Solver

Expected impact: very high.

Complexity: very high.

Architecture fit: long-term only.

Validation potential: high, but only after shape/contact geometry exists.

Reason not selected: premature for the current codebase.

## Selected Next Improvement

The next targeted model improvement should be:

> Add an opt-in `scarring_contact_v1` terrain/soil interaction model for spherical blocks, with a compactable scarring layer, velocity-squared drag, slip-dependent friction, and explicit energy/scar diagnostics.

This is the best next step because it is strongly supported by the RAMMS manual, Leine et al. 2014, and Lu et al. 2019; it is more feasible than polyhedral contact; and it addresses the current problem that restitution/friction parameters are absorbing too many distinct physical effects.

This must not become the default. It should be a research model used only when a case explicitly provides soil/scarring parameters or a calibration experiment selects them.

## Implementation Roadmap

### Minimal Physical Model

Add a new opt-in contact or material model:

```yaml
parameters:
  soil_interaction_model: scarring_contact_v1
  soil_strength_pa: ...
  scarring_drag_coefficient: ...
  scarring_layer_density_kgpm3: ...
  scarring_max_depth_m: null
  slip_friction_min: ...
  slip_friction_max: ...
  slip_friction_growth_per_m: ...
  slip_friction_decay_per_s: ...
```

For a sphere, approximate:

- maximum penetration depth from a public Lu/RAMMS-style relation using mass, normal impact velocity, and soil strength;
- effective scar area from sphere radius and penetration depth;
- scarring drag as a velocity-squared resistance opposite motion during impact/contact;
- slip-dependent friction as `mu(s) = mu_min + 2/pi * (mu_max - mu_min) * atan(kappa s)`;
- slip state growth during contact and exponential decay during separation.

The first version should report diagnostics rather than attempt full RAMMS-style hard-contact behavior.

### Core Changes

- Extend config schemas with `soil_interaction_model: none | scarring_contact_v1`.
- Add explicit soil/scarring parameters with conservative defaults that preserve current behavior.
- Add per-sample diagnostics:
  - `scarring_depth_m`
  - `scarring_drag_force_n`
  - `scarring_energy_loss_j`
  - `slip_distance_m`
  - `effective_friction_coefficient`
- Keep file I/O outside the simulation kernel.
- Keep all randomness explicit and trajectory-seeded if any stochastic soil sampling is later added.

### Verification Tests

Required analytic/synthetic checks:

- zero scarring parameters exactly match the baseline contact model;
- scarring drag always dissipates translational plus rotational energy;
- deeper scarring occurs for larger normal impact speed;
- deeper scarring occurs for lower soil strength;
- slip-dependent friction increases monotonically with contact slip and decays after separation;
- horizontal impact into a scarring layer loses the expected bounded energy for a simple fixture;
- deterministic repeated run with same seed/config gives identical scar diagnostics.

### Validation And Calibration Strategy

- Do not alter `validation_tschamut_basic`.
- Add a separate calibration experiment, for example `calibration/experiments/tschamut_scarring_v1`, only after verification passes.
- Prefer public datasets with measured scar dimensions and velocities for first calibration. Lu et al. 2019 / Chant Sura is scientifically better than Tschamut for scarring because scar dimensions and high-frequency impact measurements are discussed.
- Use Tschamut only as a held-out plausibility check unless reliable scar/material metadata are available.
- Report whether scarring improves energy/runout interpretation, not whether it "matches RAMMS".

### Reporting

The HTML report should show:

- soil/scarring model enabled/disabled;
- key soil parameters;
- total scarring energy loss;
- maximum inferred scar depth;
- warnings when a real-world validation uses uncalibrated soil parameters.

### Documentation

Update:

- `docs/model_design.md` with equations and assumptions;
- `docs/validation_data_schema.md` and `docs/benchmark_case_schema.yaml` with new fields;
- `docs/benchmark_catalog.md` with scarring verification cases;
- `docs/validation_plan.md` with a clear calibration policy for soil parameters;
- `AGENTS.md` to require scarring/contact changes to update schema, tests, docs, and report output together.

## Decision Summary

The biggest long-term gap remains non-spherical rock shape with robust nonsmooth contact. However, that is too large for the next safe increment. The highest-impact feasible step is `scarring_contact_v1`: it introduces a public-literature energy-dissipation mechanism, separates soil/material behavior from arbitrary restitution tuning, creates measurable diagnostics, and prepares the project for scientifically defensible calibration against public experimental datasets.
