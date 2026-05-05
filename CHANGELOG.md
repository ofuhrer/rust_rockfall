# Changelog

## Unreleased

- Added a lightweight hazard-layer post-processing workflow for reach probability, deposition density, maximum kinetic energy, maximum jump height, significant impact density, CSV/ASCII grid exports, deposition GeoJSON, PNG plots, and local HTML reports.
- Added hazard-layer documentation and smoke-test fixtures while keeping the simulation physics unchanged.

## v0.4.0

- Added opt-in `scarring_contact_v1` soil interaction model for minimal compactable-soil impact energy-loss diagnostics.
- Added scarring configuration fields, trajectory diagnostics, verification metrics, and synthetic scarring verification cases.
- Kept default behavior unchanged with `soil_interaction_model: none`.
- Updated schema, documentation, report generation, and consistency checks for versioned scarring fields.

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
