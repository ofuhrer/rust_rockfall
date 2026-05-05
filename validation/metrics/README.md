# Validation Metrics

The Rust implementation of verification and validation metrics lives in `src/validation.rs`.

Current implemented metrics:

- `runout_m`
- `final_speed_mps`
- `impact_count`
- `max_kinetic_energy_j`
- `energy_error_j`
- `position_error_m`
- `deposition_point_error_m`
- `runout_distance_error_m`
- `lateral_deviation_m`
- `deposition_centroid_error_m`
- `deposition_cloud_mean_nearest_error_m`
- `deposition_cloud_overlap_fraction`
- `lateral_spread_error_m`
- `observed_mean_runout_m`
- `simulated_mean_runout_m`
- `validation_release_count`
- `validation_simulated_trajectory_count`

Planned metrics:

- trajectory envelope overlap
- bounce-height error
- velocity and angular-velocity time-series error
- kinetic-energy error at impact points
- runout exceedance probability
- deposition-density skill score beyond the current nearest-neighbor/overlap summary
- ensemble percentile envelopes for spatial deposition fields
