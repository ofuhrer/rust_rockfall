# Benchmark Catalog

This catalog lists the current `v0.4.0` verification and validation cases. These cases verify the independent simulator’s implemented equations and diagnostics; they do not claim agreement with RAMMS::ROCKFALL or operational hazard validity.

## Level 0: Analytic Unit Tests

- `analytic_free_fall`: checks constant-gravity position, velocity, and energy conservation.
- `analytic_projectile_motion`: checks linear horizontal motion, parabolic vertical motion, and final velocity.
- `analytic_vertical_rebound`: checks first rebound height against `e_n^2*h0`.
- `analytic_repeated_bounce`: checks repeated impact counting and first rebound-height decay.
- `analytic_oblique_rebound_flat_plane`: checks normal restitution and Coulomb-capped tangential response.
- `analytic_inclined_slide_stop`: checks frictional stopping for an initially upslope sliding block.
- `analytic_no_motion_threshold`: checks that `tan(theta) < mu` does not initiate sliding from rest.
- `analytic_energy_conservation_no_dissipation`: checks total-energy drift with no contact and no dissipation.
- `analytic_rolling_incline_solid_sphere`: checks opt-in solid-sphere rolling acceleration.
- `analytic_rolling_resistance_stop`: checks rolling-resistance stopping on horizontal terrain.
- `analytic_rolling_energy_monotonic`: checks monotonic total-energy loss under rolling resistance.
- `analytic_insufficient_static_friction_slides`: checks that insufficient static friction reports sliding rather than rolling.

## Level 1: Synthetic Terrain Tests

- `synthetic_flat_plane_rebound`: horizontal plane impact and bounded bounce.
- `synthetic_inclined_plane_bounce_runout`: downslope runout on a constant plane.
- `synthetic_paraboloid_basin_capture`: bounded dissipative motion in a convex basin.
- `synthetic_step_terrain_single_drop`: drop across one terrain discontinuity.
- `synthetic_step_terrain_multi_bounce`: repeated contacts after a step drop.
- `synthetic_ascii_dem_fixture`: small ESRI ASCII grid loading and trajectory smoke test.
- `synthetic_clamped_dem_terrain_variation`: opt-in clamped ESRI ASCII DEM trajectory over a small varied patch, including an initial boundary-clamped query.
- `synthetic_contact_roughness_energy_stability`: bounded stochastic contact roughness remains dissipative within fixed-step numerical tolerance.
- `synthetic_scarring_zero_baseline`: `scarring_contact_v1` with inert parameters exactly matches `soil_interaction_model: none`.
- `synthetic_scarring_energy_dissipation`: fixed-depth scarring diagnostics produce positive bounded energy loss without positive total-energy jumps; optional impact-event CSV/JSON output makes the contact step auditable.
- `synthetic_scarring_depth_velocity_scaling`: inferred scarring depth activates for finite normal impact speed without drag energy loss.
- `synthetic_scarring_depth_soil_strength_scaling`: weak-soil scarring parameters produce a substantial inferred depth diagnostic.

Impact count metrics are explicit: `impact_event_count` is the raw event ledger, `significant_impact_count` filters event rows to incoming normal speed at or above `0.05 m/s`, and legacy `impact_count` remains the trajectory-state transition count.

## Level 2: Motion-Regime Tests

- `regime_bounce_to_slide_transition`: impact followed by contact-dominated motion inferred from diagnostics.
- `regime_slide_to_stop_transition`: sliding state dissipates to stopped state.
- `regime_repeated_low_energy_impacts`: low-energy repeated impacts with bounded energy diagnostics.

The default `translational_v0` contact model exposes `airborne`, `impact`, `sliding`, and `stopped` contact states. The opt-in `sphere_rotational_v1` contact model also exposes `rolling` and rolling-residual diagnostics.

## Level 3: Stochastic Tests

- `stochastic_seeded_release_reproducibility`: same seed reproduces the same trajectory.
- `stochastic_different_seed_spread`: different seeds with nonzero perturbation produce nonzero runout spread.
- `stochastic_ensemble_runout_statistics`: reports mean, median, p05, p95, and kinetic-energy envelope.
- `stochastic_contact_roughness_zero_consistency`: `stochastic_contact_v1` with zero standard deviations exactly matches `roughness_model: none`.
- `stochastic_contact_roughness_reproducibility`: roughened impacts are reproducible for a fixed seed.
- `stochastic_contact_roughness_ensemble_spread`: roughened impacts produce deterministic ensemble spread without release perturbations.

## Level 5: Validation Scaffolds

- `validation_synthetic_plane_basic`: checked-in synthetic observation fixture for validation metric computation.
- `validation_tschamut_proxy_plane`: limited public-data terrain comparison case using the earlier fitted-plane terrain proxy for the Tschamut 2014 subset.
- `validation_tschamut_basic`: limited active public-data validation case using a small processed subset of SLF/WSL EnviDat Tschamut 2014 LPS release/deposition observations and the `idw_residual_dem_from_lps` clamped DEM proxy. It reports distribution-level runout and deposition-cloud mismatch only.

Real-world validation remains partial and qualitative for v0.4.0 because the simulator lacks block shape, advanced contact, calibrated scarring with drag torque/slip-dependent friction, roughness calibration, forest interaction, fragmentation, and production field DEM workflows.
