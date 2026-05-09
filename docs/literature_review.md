# Literature Review

This project uses public scientific and grey literature to build an independent, transparent rockfall simulator. It does not copy proprietary source code, inspect binaries, or claim equivalence to closed-source reference implementations.

## Local Background Material

- Leine, Schweizer, Christen, Glover, Bartelt, and Gerber, 2014, *Simulation of rockfall trajectories with consideration of rock shape*. This is the most relevant local source for a full 3D rigid-body formulation: convex polyhedral rock shapes, high-resolution DEM terrain, nonsmooth contact dynamics, unilateral constraints, Coulomb friction, contact frames, and a slippage-dependent friction model for scarring-like behavior.
- Leine, Capobianco, Bartelt, Christen, and Caviezel, 2021, *Stability of rigid body motion through an extended intermediate axis theorem*. This motivates careful rotational integration for non-spherical blocks and documents why energy/momentum behavior matters for platy rocks and wheel-like motion.
- Lu et al., 2019, *Modelling rockfall impact with scarring in compactable soils*. This provides a public scarring-impact model with a compactable soil layer, hard rebound plane, velocity-squared drag concept, and validation against Chant Sura experiments.
- `RAMMS_ROCK2_Manual.pdf`, 2026. The manual is useful as grey literature for terminology, modelling assumptions, terrain/soil parameters, outputs, and validation cautions. It is not treated as a complete specification of proprietary internals.

## Additional Public Sources

- STONE / GRASS `r.stone`: an open GIS implementation of a point-like 3D rockfall model using DEMs, normal/tangential restitution, rolling friction, stop velocity, and stochastic parameter perturbations. <https://grass.osgeo.org/grass-stable/manuals/addons/r.stone.html>
- Rockyfor3D: a probabilistic process-based 3D trajectory model combining parabolic flight, rebounds, roughness classes, soil-type restitution, and stochastic choices. <https://www.ecorisq.org/tool-manuals/rockyfor3d-user-manual/125-rockyfor3d-manual/file>
- RocFall3: a commercial 3D program documenting lumped-mass and rigid-body options, repeatable pseudorandom generation, restitution/friction model families, and common outputs. <https://www.rocscience.com/help/rocfall3/overview/technical-specifications>
- RocPro3D: a hybrid lumped-mass model with free fall, impact, translation, transitions, velocity-dependent restitution, and dynamic Coulomb rolling friction. <https://www.rocpro3d.com/overview/>
- Crosta and Agliardi, 2004, *Parametric evaluation of 3D dispersion of rockfall trajectories*. This emphasizes that lateral dispersion depends on slope gradient, micro-topography, roughness, and model resolution. <https://nhess.copernicus.org/articles/4/583/2004/>
- Caviezel et al., 2021, *The relevance of rock shape over mass*. This provides field evidence that shape strongly affects lateral spreading and runout, and identifies the Chant Sura dataset as a calibration resource. <https://www.nature.com/articles/s41467-021-25794-y>
- Siconos: an open nonsmooth dynamics/contact framework relevant as a conceptual reference for future complementarity solvers, not a v0 dependency. <https://nonsmooth.gricad-pages.univ-grenoble-alpes.fr/siconos/index.html/>

## What Is Available

- Publicly documented model families: point-mass, sphere, hybrid lumped-mass, and full rigid-body models.
- Public equations and concepts for free flight, restitution, Coulomb friction, contact frames, DEM interpolation, scarring drag, energy diagnostics, and stochastic ensembles.
- Public validation philosophy: analytic checks where possible, field calibration where available, and no expectation of bitwise agreement across models.

## What Is Missing

- A complete, public, implementation-level description of all relevant vendor implementations.
- Public benchmark input/output files sufficient to verify a new simulator against the full RAMMS model.
- Calibrated parameter sets for general terrain, soil, block shape, and vegetation outside specific experimental contexts.
- A validated open dataset in this repository for DEM-scale rockfall benchmarks.
