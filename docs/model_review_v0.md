# v0 Scientific Model Review

## Summary

The v0 simulator is an internally useful research scaffold: free flight is analytically exact for constant gravity, terrain interaction is explicit and testable, energy diagnostics are exposed, stochastic release perturbations are deterministic, and verification cases cover the intended v0 behavior.

Scientifically, v0 should still be treated as a simplified spherical-block trajectory model, closer to the point/sphere end of the public model spectrum than to full rigid-body rockfall dynamics. It is suitable for analytic verification, software architecture development, and controlled synthetic tests. It is not yet suitable for field-scale validation beyond qualitative smoke tests, because key mechanisms controlling runout, rebound, lateral dispersion, and stopping are not represented.

The recommended next high-impact improvement is:

> Implement a physically consistent spherical contact-mode model with translational-rotational coupling, explicit rolling/sliding diagnostics, and simple rolling resistance.

This is a better next step than roughness or polyhedral shape because it fixes a core mechanics gap in the current sphere model while remaining compatible with the existing architecture and verification suite.

## Current Model Formulation

### Block Representation

The block is a sphere with radius and mass. The state contains position, linear velocity, and angular velocity. The moment of inertia is used in rotational energy diagnostics, but angular velocity is not advanced by contact impulses or rolling kinematics.

Assumption:

- shape does not influence contact orientation, rebound, lateral spreading, or rotational stability;
- rotational energy is reported if angular velocity is supplied, but rotation is not a coupled state variable in v0 dynamics.

Internal consistency:

- the diagnostic formula for spherical rotational energy is physically correct;
- the lack of angular-velocity evolution is clearly a v0 limitation, but it means reported rotation is not dynamically meaningful for most runs.

### Terrain Interaction

Terrain is represented by analytic height functions and small ESRI ASCII DEM fixtures. Contact is evaluated through terrain height/normal queries and a signed sphere-terrain distance. For analytic terrain, normals are deterministic and testable.

Assumption:

- the terrain surface is locally smooth enough that a single normal at the sphere center's horizontal location is sufficient;
- only one terrain contact exists at a time;
- sub-cell roughness, surface blocks, soil deformation, vegetation, and barriers are absent.

Internal consistency:

- the `Terrain` abstraction is appropriate for future DEM and roughness extensions;
- single-contact projection is stable enough for v0 tests;
- fixed-step contact can introduce impact-time error and low-energy contact chatter.

### Free Flight

Free flight uses exact constant-acceleration kinematics:

```text
x(t + dt) = x(t) + v(t) dt + 0.5 g dt^2
v(t + dt) = v(t) + g dt
```

Internal consistency:

- mechanical energy is conserved in dissipation-free flight to floating-point tolerance;
- projectile-motion and free-fall verification cases are appropriately tight.

### Impact and Restitution

When penetration is detected, the sphere is projected out along the terrain normal. Velocity is decomposed into normal and tangential parts. If the normal velocity is incoming, the normal velocity is reversed and scaled by normal restitution. Tangential velocity is reduced by tangential restitution, capped by a Coulomb-like impulse magnitude.

Assumption:

- restitution coefficients are constant and not velocity-, material-, shape-, or roughness-dependent;
- the contact impulse acts only on translational velocity;
- the tangential impulse does not generate angular velocity;
- impact is resolved after a fixed time step, not at the exact time of first contact;
- there is no nonsmooth complementarity solve.

Internal consistency:

- the model dissipates energy for restitution values below one and positive friction;
- the normal/tangential decomposition is clear and testable;
- repeated-bounce tests already document broad impact-count bounds caused by fixed-step contact behavior;
- tangential impact behavior is physically incomplete because a sphere's tangential impulse should generally exchange translational and rotational momentum.

### Contact Friction and Stopping

During contact, normal velocity is constrained away and tangential acceleration is gravity projected onto the terrain tangent. Coulomb friction reduces tangential speed. The block stops when tangential speed is below the configured threshold and gravity tangent cannot overcome friction.

Assumption:

- sliding friction is represented by one Coulomb coefficient;
- static-friction threshold and kinetic-friction dissipation share the same coefficient;
- rolling is not a separate motion mode;
- rolling resistance is absent;
- transition labels are inferred from `ContactState`, not from a formal mode solver.

Internal consistency:

- horizontal and inclined stopping tests verify the intended behavior;
- the stopping criterion is deterministic and practical;
- without rolling resistance and rotational coupling, the model cannot distinguish sliding, rolling, and spin-dominated motion in a physically meaningful way.

## Alignment With Public Literature

The v0 model aligns with public point/sphere rockfall formulations in using gravity-driven flight, DEM/terrain normals, normal and tangential restitution, Coulomb-style friction, stopping thresholds, deterministic stochastic sampling, and energy/runout outputs. This is consistent with the simplified end of models documented for STONE/r.stone, Rockyfor3D, RocFall3, and RocPro3D.

The v0 model is intentionally below the fidelity of the full rigid-body literature:

- Leine et al. 2014 motivates nonsmooth contact dynamics, contact frames, Coulomb friction, shape-dependent contact, and slippage/scarring concepts.
- Leine et al. 2021 motivates careful rotational integration for non-spherical bodies.
- Lu et al. 2019 motivates compactable-soil/scarring impact models for specific experimental contexts.
- Crosta and Agliardi 2004 and Rockyfor3D emphasize roughness and topographic resolution as drivers of 3D dispersion.
- Caviezel et al. 2021 shows that block shape strongly affects lateral spreading and runout.

The current v0 is therefore scientifically plausible as a minimal demonstrator, but it should not yet be used to interpret shape-sensitive field experiments or terrain-roughness-sensitive runout distributions.

## Limitations and Gaps

| Limitation | Impact on Realism | Impact on Validation | Type |
| --- | --- | --- | --- |
| No translational-rotational coupling | High for rebound, rolling, energy partition, and stopping | High where angular velocity, rolling, or block shape observations exist | Structural |
| No explicit rolling mode or rolling resistance | High for post-impact runout on slopes and talus | High for deposition/runout comparisons | Structural but implementable for spheres |
| Fixed-step impact detection | Medium to high for impact timing, bounce height, and repeated low-energy impacts | Medium for analytic rebound and bounce-count comparisons | Numerical/structural |
| Single smooth contact normal | High on rough DEMs, ridges, gullies, and blocky terrain | High for lateral dispersion and terrain-driven spreading | Structural |
| Constant restitution coefficients | Medium; many models parameterize by soil/roughness/velocity | Medium to high for field calibration | Parameter/model-form |
| No surface roughness model | High for lateral dispersion and runout envelopes | High for Rockyfor3D-style and field dataset comparisons | Structural |
| Spherical shape only | Very high for shape-sensitive experiments | Very high for Chant Sura and similar datasets | Structural |
| No scarring/soil deformation | Medium to high for compactable soils and high-energy impacts | High for scarring-specific experiments | Structural/model-form |
| No forest/barrier/fragmentation interaction | Site dependent; high where present | High for forest or infrastructure datasets | Structural |

The most immediate mechanics gap is not that v0 lacks advanced field processes. It is that the current sphere model itself does not yet conserve or dissipate translational and rotational motion through contact in a physically coherent way.

## Candidate Next Improvements

### 1. Spherical Contact-Mode Upgrade With Rotation and Rolling Resistance

Concept:

- resolve contact using a sphere impulse model that updates both linear and angular velocity;
- distinguish impact, sliding, rolling, and stopped states;
- enforce or diagnose the rolling constraint `v_t = omega x r` at contact;
- add a simple rolling-resistance parameter for post-impact rolling motion;
- optionally add event-localized first contact to reduce fixed-step rebound error.

Difference from v0:

- tangential impulses would generate spin instead of only scaling tangential velocity;
- rotational energy would become dynamic, not diagnostic-only;
- rolling/sliding transitions would become explicit;
- runout and stopping would depend on rolling resistance as well as sliding friction.

Complexity:

- moderate for a sphere-only implementation;
- higher if exact event localization is included in the same phase, but still much lower than polyhedral contact or a nonsmooth multi-contact solver.

Impact:

- high improvement in internal mechanics;
- high improvement for runout and stopping plausibility;
- directly supports new analytic verification cases;
- preserves the current architecture and does not require external datasets.

Required tests:

- tangential impulse creates angular velocity with expected sign and magnitude;
- no-slip rolling kinematic relation is satisfied after transition;
- rolling sphere on an inclined plane follows the analytic acceleration for a solid sphere where applicable;
- rolling resistance stops a sphere on horizontal terrain;
- translational plus rotational energy is conserved for ideal elastic/no-friction contact where applicable and dissipates monotonically when resistance is active.

### 2. Surface Roughness Representation

Concept:

- perturb effective contact normals, surface heights, or restitution/friction parameters based on roughness classes or stochastic distributions;
- represent sub-grid topographic variability that is not captured by analytic terrain or coarse DEMs.

Difference from v0:

- the terrain contact response would no longer depend only on the smooth terrain normal;
- lateral dispersion and rebound variability could emerge from terrain/roughness parameters.

Complexity:

- moderate if implemented as stochastic normal perturbations or procedural roughness;
- higher if tied to DEM resolution, block size, and spatial correlation.

Impact:

- high for field-scale runout envelopes and lateral spreading;
- important for Rockyfor3D-like probabilistic modeling and Crosta/Agliardi-style dispersion studies.

Reason not selected first:

- roughness would sit on top of the current incomplete sphere contact mechanics;
- adding stochastic roughness before rotational contact risks hiding basic energy and mode-transition deficiencies behind calibration parameters.

### 3. Improved Impact Event Localization

Concept:

- detect the time of first terrain contact within a time step and resolve impact at that event time;
- continue the remaining sub-step after impact.

Difference from v0:

- impact timing and rebound height would be less dependent on `dt`;
- repeated low-energy bounce chatter should decrease.

Complexity:

- low to moderate for analytic terrain;
- higher for DEM terrain and complex terrain shapes.

Impact:

- medium to high for numerical robustness;
- important for clean verification and later roughness/contact extensions.

Reason not selected as a standalone primary improvement:

- it improves numerical timing but does not address the larger physics gap: absent rotational coupling and rolling modes.
- it should be included as a sub-phase of the contact-mode upgrade where feasible.

### 4. Polyhedral or Non-Spherical Blocks

Concept:

- represent rocks as ellipsoids, convex polyhedra, or sampled shapes with orientation-dependent contact.

Difference from v0:

- contact normals, torque, rotational stability, and lateral spreading would become shape dependent.

Complexity:

- high;
- requires orientation integration, mass properties, contact detection, and likely nonsmooth contact methods.

Impact:

- very high for experiments showing shape effects, especially Chant Sura-style datasets.

Reason not selected first:

- implementing non-spherical shapes before a correct sphere contact/rolling model would build complex shape dynamics on an incomplete contact foundation.

## Recommendation

The next primary model improvement should be a **physically consistent spherical contact-mode model with rotation, rolling/sliding transitions, and rolling resistance**.

This choice gives the best effort-to-benefit ratio:

- It directly fixes the largest internal mechanics gap in v0.
- It makes existing angular-velocity and rotational-energy fields scientifically meaningful.
- It aligns with public model families that include rolling friction/resistance and repeatable restitution/friction behavior.
- It improves runout and stopping behavior without introducing site-specific roughness calibration.
- It enables strong analytic verification tests before field validation complexity is added.
- It prepares the architecture for later roughness and non-spherical contact, rather than competing with those extensions.

Surface roughness is likely the next high-impact field-validation feature after this. Polyhedral shape is scientifically important but should wait until the contact and rotational state machinery is reliable for spheres.

## Implementation Roadmap

### Phase A: Specify the Sphere Contact Mechanics

Objective:

- define the sphere-only contact equations before coding.

Model decisions:

- contact point relative to center: `r = -R n`;
- decompose relative contact velocity into normal and tangent components;
- normal impulse uses normal restitution;
- tangential impulse follows Coulomb bounds and updates both linear and angular velocity;
- rolling condition uses contact-point tangential velocity;
- rolling resistance is represented by a clearly named coefficient with explicit units/interpretation.

Documentation updates:

- extend `docs/model_design.md` with the selected impulse equations;
- update `docs/validation_data_schema.md` with rolling-resistance and mode fields if needed;
- document what remains an assumption rather than a calibrated law.

### Phase B: Add Explicit Motion Diagnostics

Objective:

- distinguish current contact states more clearly without changing all orchestration code.

Core changes:

- add `Rolling` to `ContactState` or add a separate motion-mode diagnostic;
- expose contact-point tangential speed, angular speed, and rolling-residual diagnostics where useful;
- keep trajectory CSV backward-compatible where possible by appending fields rather than renaming existing ones.

Tests:

- serialization round-trip for new state/mode fields;
- CSV output contains new diagnostics;
- old verification cases still pass or have documented expected changes.

### Phase C: Implement Translational-Rotational Contact for Spheres

Objective:

- make tangential contact affect angular velocity.

Core changes:

- update `dynamics::resolve_sphere_contact` or add a new implementation behind a clearly named model option;
- compute angular impulse update for a solid sphere;
- ensure frictional impulses do not create energy in dissipative cases;
- keep all randomness explicit and independent of execution order.

Verification tests:

- vertical impact with no tangential velocity leaves angular velocity unchanged;
- oblique impact with friction generates angular velocity of the expected sign;
- frictionless oblique impact preserves tangential velocity and angular velocity;
- high tangential impulse is capped by Coulomb friction;
- total energy does not increase for `e_n <= 1`, dissipative tangential restitution, and positive friction.

### Phase D: Add Rolling and Rolling Resistance

Objective:

- represent post-impact rolling more plausibly.

Core changes:

- implement rolling-mode update for a sphere in contact with terrain;
- add a rolling-resistance parameter to config and YAML schema;
- define transition conditions between sliding, rolling, and stopped states;
- preserve no-motion threshold behavior.

Verification tests:

- rolling sphere acceleration on an inclined plane matches the solid-sphere analytic result where the no-slip assumption applies:

```text
a = (5/7) g sin(theta)
```

- rolling resistance stops a sphere on horizontal terrain;
- static threshold prevents motion where slope is too small;
- energy loss under rolling resistance is monotonic;
- order-independent stochastic ensemble tests remain unchanged.

### Phase E: Optional Impact Event Localization

Objective:

- reduce time-step sensitivity in rebound cases.

Core changes:

- for analytic plane terrain, solve the first-contact time inside the step;
- later generalize with bracketed root finding for supported terrain types;
- keep DEM behavior conservative until robust interpolation/root policies are defined.

Verification tests:

- rebound height converges less sensitively with `dt`;
- repeated bounce impact count becomes more stable;
- free-flight tests remain unchanged.

### Phase F: Validation and Benchmark Updates

Objective:

- make the new mechanics visible in validation workflows.

Validation changes:

- add synthetic rolling benchmarks under `verification/synthetic/`;
- add rolling-resistance cases to `docs/benchmark_catalog.md`;
- update HTML report generation only if new plot fields are added;
- keep real-world validation optional and explicitly uncalibrated until public datasets are preprocessed.

## New Verification Tests Needed

Minimum test additions for the selected improvement:

- `sphere_oblique_impact_generates_spin`
- `frictionless_oblique_impact_does_not_generate_spin`
- `tangential_impulse_respects_coulomb_bound_with_rotation`
- `rolling_sphere_incline_acceleration_matches_analytic_solution`
- `rolling_resistance_stops_horizontal_motion`
- `rolling_energy_budget_is_monotonic_with_resistance`
- `rolling_mode_is_reported_in_trajectory_output`
- `existing_v0_rebound_cases_remain_within_documented_tolerances`

## Open Scientific Questions

- Should rolling resistance be represented as a force coefficient, moment coefficient, or velocity-dependent law in early versions?
- Should tangential restitution remain separate from Coulomb friction once rotational coupling is introduced, or should a single tangential impulse law replace it?
- How should roughness be parameterized relative to block radius and DEM resolution?
- Which public experimental dataset has sufficient angular velocity, trajectory, and deposition data to calibrate rolling resistance without overfitting?
- When should the simulator switch from sphere-specific contact equations to a general rigid-body contact framework?

## Bottom Line

The v0 model is coherent for what it claims to be: a minimal, deterministic spherical-block simulator with simple restitution and Coulomb contact friction. Its largest scientific weakness is that contact does not yet exchange translational and rotational motion, so rolling and spin are not physical. The next high-impact step is therefore to make sphere contact mechanics physically consistent before adding roughness, shape complexity, or field calibration.
