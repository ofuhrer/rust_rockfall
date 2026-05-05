# Changelog

## v0.3.0

- Added opt-in `stochastic_contact_v1` impact roughness.
- Added roughness parameters for contact-normal angular perturbation, dissipative restitution perturbation, and friction increase.
- Added roughness verification cases for zero-roughness consistency, seeded reproducibility, ensemble spread, and energy stability.
- Added semantic-versioning rules and consistency checks.
- Updated visualization/reporting to expose model version and roughness-enabled cases.

## v0.2.0

- Added opt-in `sphere_rotational_v1` sphere contact with translational-rotational impulse coupling.
- Added rolling diagnostics, rolling contact state, and simple rolling resistance.
- Added HPC-readiness constraints, deterministic ensemble seed derivation, validation/report tooling, and report readability improvements.

## v0.1.0

- Initial independent spherical-block simulator with analytic terrain, free flight, translational impact response, Coulomb contact friction, seeded release perturbations, CSV output, and verification scaffolding.
