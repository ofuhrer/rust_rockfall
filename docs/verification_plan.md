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
- terrain height/normal use in contact projection
- deterministic seeded release perturbations
- energy diagnostics and monotonicity checks

## What Is Not Verified

- full 3D polyhedral rigid-body contact
- nonsmooth complementarity solvers
- rolling resistance as a separate physics model
- terrain roughness/scarring
- forest/deadwood interaction
- fragmentation
- operational hazard prediction

Verification cases must not be calibrated.

