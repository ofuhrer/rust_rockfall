# Model Review v0.3.0

`v0.3.0` implements the next incremental model step after rotational sphere contact: opt-in stochastic contact roughness.

## Rationale

The v0.2.0 model can produce deterministic trajectories and rotational rolling diagnostics, but ensembles only spread when release conditions are perturbed. Public rockfall literature emphasizes terrain roughness, contact variability, and micro-topography as important controls on rebound direction, lateral dispersion, and runout. A full terrain-class or DEM-scale roughness model would require calibration data and stronger spatial assumptions, so v0.3.0 chooses a narrower first step: bounded stochastic perturbations at impact.

## Chosen Improvement

`stochastic_contact_v1` perturbs:

- impact contact normal direction;
- normal and tangential restitution, only in the dissipative direction;
- friction, only upward.

This creates deterministic ensemble spread while preserving the existing `roughness_model: none` default.

## What This Adds

- A first physically meaningful source of trajectory variability beyond release perturbations.
- Seeded roughness behavior tied to trajectory identity for future parallel ensembles.
- Verification cases for zero-roughness consistency, reproducibility, ensemble spread, and energy stability.

## What This Does Not Add

- Calibrated terrain roughness classes.
- Spatially correlated roughness fields.
- DEM micro-topography synthesis.
- Scarring, fragmentation, vegetation, or polyhedral contact.
- Operational hazard validation.

## Next Scientific Questions

- Which public experimental cases have enough trajectory and terrain metadata to calibrate roughness without overfitting?
- Should roughness eventually be represented as spatial terrain metadata, impact-material classes, or both?
- How should roughness interact with future polyhedral block shape and scarring models?
