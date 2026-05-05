# Verification Plan

Verification asks whether the code correctly solves the current v0 model. It does not establish real-world validity.

## Levels

- Level 0: analytic mechanics and numerical correctness.
- Level 1: terrain/contact behavior on idealized analytic terrain and tiny DEM fixtures.
- Level 2: motion-regime behavior inferred from contact states and diagnostics.
- Level 3: stochastic reproducibility and deterministic ensemble summaries.

## Local Workflow

```bash
cargo test
cargo run -- verify --case verification/analytic/free_fall.yaml
cargo run -- verify --all
```

The default verification suite uses only checked-in analytic and synthetic fixtures. It does not require large external datasets.

## Tolerances

Free-flight tests use tight tolerances because the integrator uses exact constant-acceleration stepping. Contact tests use physically meaningful but broader tolerances because impact time is resolved on fixed time steps and contact response is deliberately simple.

## What Is Verified

- gravity-driven free flight
- projectile kinematics
- impact response with normal restitution
- tangential restitution as limited by the current Coulomb impulse approximation
- Coulomb contact friction and stopping
- opt-in rotational sphere contact, rolling diagnostics, and rolling resistance
- opt-in compactable-soil scarring depth, drag-force, and energy-loss diagnostics
- terrain height/normal use in contact projection
- deterministic seeded release perturbations
- order-independent ensemble seed derivation
- energy diagnostics and monotonicity checks

## What Is Not Verified

- full 3D polyhedral rigid-body contact
- nonsmooth complementarity solvers
- calibrated spatial terrain roughness/scarring
- scarring drag torque, slip-dependent friction, terrain categories, or calibration against soil observations
- forest/deadwood interaction
- fragmentation
- operational hazard prediction

Verification cases must not be calibrated.

## Roughness Verification

`v0.3.0` adds opt-in `stochastic_contact_v1` impact roughness. Verification covers:

- zero-roughness consistency with `roughness_model: none`;
- fixed-seed reproducibility for roughened impacts;
- different-seed ensemble spread without release perturbations;
- bounded energy behavior for dissipative roughened contact.

These tests verify deterministic contact stochasticity only. They do not calibrate roughness against field terrain classes or validate hazard prediction.

## Scarring Verification

`v0.4.0` adds opt-in `scarring_contact_v1` soil interaction diagnostics. Verification covers:

- zero-effect consistency with `soil_interaction_model: none`;
- positive scarring depth and drag diagnostics in synthetic impact cases;
- nonnegative, bounded scarring energy loss;
- expected depth scaling with impact speed and soil strength through unit tests.

These tests verify the minimal compactable-soil bookkeeping and energy removal only. They do not calibrate soil strength, do not represent terrain categories, and do not validate operational field behavior.
