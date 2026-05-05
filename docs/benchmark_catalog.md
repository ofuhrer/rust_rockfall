# Benchmark Catalog

This catalog lists the current v0 verification and validation cases. These cases verify the independent simulator’s implemented equations and diagnostics; they do not claim agreement with RAMMS::ROCKFALL or operational hazard validity.

## Level 0: Analytic Unit Tests

- `analytic_free_fall`: checks constant-gravity position, velocity, and energy conservation.
- `analytic_projectile_motion`: checks linear horizontal motion, parabolic vertical motion, and final velocity.
- `analytic_vertical_rebound`: checks first rebound height against `e_n^2*h0`.
- `analytic_repeated_bounce`: checks repeated impact counting and first rebound-height decay.
- `analytic_oblique_rebound_flat_plane`: checks normal restitution and Coulomb-capped tangential response.
- `analytic_inclined_slide_stop`: checks frictional stopping for an initially upslope sliding block.
- `analytic_no_motion_threshold`: checks that `tan(theta) < mu` does not initiate sliding from rest.
- `analytic_energy_conservation_no_dissipation`: checks total-energy drift with no contact and no dissipation.

## Level 1: Synthetic Terrain Tests

- `synthetic_flat_plane_rebound`: horizontal plane impact and bounded bounce.
- `synthetic_inclined_plane_bounce_runout`: downslope runout on a constant plane.
- `synthetic_paraboloid_basin_capture`: bounded dissipative motion in a convex basin.
- `synthetic_step_terrain_single_drop`: drop across one terrain discontinuity.
- `synthetic_step_terrain_multi_bounce`: repeated contacts after a step drop.
- `synthetic_ascii_dem_fixture`: small ESRI ASCII grid loading and trajectory smoke test.

## Level 2: Motion-Regime Tests

- `regime_bounce_to_slide_transition`: impact followed by contact-dominated motion inferred from diagnostics.
- `regime_slide_to_stop_transition`: sliding state dissipates to stopped state.
- `regime_repeated_low_energy_impacts`: low-energy repeated impacts with bounded energy diagnostics.

The current model exposes `airborne`, `impact`, `sliding`, and `stopped` contact states. It does not expose a full rolling regime.

## Level 3: Stochastic Tests

- `stochastic_seeded_release_reproducibility`: same seed reproduces the same trajectory.
- `stochastic_different_seed_spread`: different seeds with nonzero perturbation produce nonzero runout spread.
- `stochastic_ensemble_runout_statistics`: reports mean, median, p05, p95, and kinetic-energy envelope.

## Level 5: Validation Scaffolds

- `validation_synthetic_plane_basic`: checked-in synthetic observation fixture for validation metric computation.
- `validation_tschamut_basic`: optional scaffold for public SLF/WSL EnviDat Tschamut data; skipped until processed observations exist locally.

Real-world validation remains partial and qualitative for v0 because the simulator lacks block shape, advanced contact/scarring, roughness calibration, forest interaction, fragmentation, and calibrated DEM workflows.

