//! Tests for DEM terrain error paths: out-of-bounds, nodata, malformed headers,
//! size mismatches, and clamped fallback behaviour.

use rust_rockfall::terrain::{ClampedDemGrid, DemGrid, Terrain, TerrainError};
use rust_rockfall::{
    simulate_one_trajectory, RoughnessModel, SimulationConfig, SphereBlock, TerrainConfig,
    TrajectoryRequest, TrajectoryRun,
};

// ─── DEM header / construction errors ─────────────────────────────────────

#[test]
fn dem_grid_rejects_ncols_below_two() {
    // 1 column, 3 rows → 3 values. This isolates the ncols validation.
    let text = "ncols 1\nnrows 3\nxllcorner 0.0\nyllcorner 0.0\ncellsize 1.0\nNODATA_value -9999\n1\n2\n3\n";
    let err = DemGrid::from_ascii_grid_str(text).unwrap_err();
    assert!(
        matches!(err, TerrainError::InvalidGrid(_)),
        "expected InvalidGrid, got {err:?}"
    );
}

#[test]
fn dem_grid_rejects_nrows_below_two() {
    let text =
        "ncols 3\nnrows 1\nxllcorner 0.0\nyllcorner 0.0\ncellsize 1.0\nNODATA_value -9999\n1 2 3\n";
    let err = DemGrid::from_ascii_grid_str(text).unwrap_err();
    assert!(matches!(err, TerrainError::InvalidGrid(_)));
}

#[test]
fn dem_grid_rejects_nonpositive_cellsize() {
    let text = "ncols 3\nnrows 2\nxllcorner 0.0\nyllcorner 0.0\ncellsize 0.0\nNODATA_value -9999\n1 2 3\n4 5 6\n";
    let err = DemGrid::from_ascii_grid_str(text).unwrap_err();
    assert!(matches!(err, TerrainError::InvalidGrid(_)));
}

#[test]
fn dem_grid_rejects_value_count_mismatch() {
    // 3x2 = 6 values expected, only 5 provided
    let text = "ncols 3\nnrows 2\nxllcorner 0.0\nyllcorner 0.0\ncellsize 1.0\nNODATA_value -9999\n1 2 3\n4 5\n";
    let err = DemGrid::from_ascii_grid_str(text).unwrap_err();
    assert!(matches!(err, TerrainError::ValueCount { .. }));
}

#[test]
fn dem_grid_rejects_non_finite_elevation_in_body() {
    // Rust's str::parse::<f64>() accepts "nan" and produces f64::NAN.
    // DemGrid::from_ascii_grid_str then explicitly checks !value.is_finite()
    // and rejects the grid with InvalidGrid (src/terrain.rs:330-334).
    let text = "ncols 2\nnrows 2\nxllcorner 0.0\nyllcorner 0.0\ncellsize 1.0\nNODATA_value -9999\n1 2\n3 nan\n";
    let err = DemGrid::from_ascii_grid_str(text).unwrap_err();
    assert!(
        matches!(err, TerrainError::InvalidGrid(_)),
        "expected InvalidGrid for non-finite elevation value, got {err:?}"
    );
}

// ─── DEM query errors ──────────────────────────────────────────────────────

fn flat_2x2_dem() -> DemGrid {
    // 2-column, 2-row DEM: cell centers at (0.5, 0.5), (1.5, 0.5), (0.5, 1.5), (1.5, 1.5)
    let text = "ncols 2\nnrows 2\nxllcorner 0.0\nyllcorner 0.0\ncellsize 1.0\nNODATA_value -9999\n10.0 12.0\n11.0 13.0\n";
    DemGrid::from_ascii_grid_str(text).unwrap()
}

#[test]
fn dem_try_height_returns_out_of_bounds_for_query_outside_grid() {
    let dem = flat_2x2_dem();
    let result = dem.try_height(100.0, 0.5);
    assert!(matches!(result, Err(TerrainError::OutOfBounds { .. })));
}

#[test]
fn dem_try_height_returns_out_of_bounds_for_negative_coordinates() {
    let dem = flat_2x2_dem();
    let result = dem.try_height(-1.0, 0.5);
    assert!(matches!(result, Err(TerrainError::OutOfBounds { .. })));
}

#[test]
fn dem_try_height_returns_nodata_when_cell_is_nodata_sentinel() {
    let text = "ncols 2\nnrows 2\nxllcorner 0.0\nyllcorner 0.0\ncellsize 1.0\nNODATA_value -9999\n10.0 -9999.0\n11.0 13.0\n";
    let dem = DemGrid::from_ascii_grid_str(text).unwrap();
    // Query at (1.5, 0.5) - the cell containing the nodata sentinel.
    let result = dem.try_height(1.5, 0.5);
    assert!(
        matches!(result, Err(TerrainError::NoData { .. })),
        "expected NoData, got {result:?}"
    );
}

#[test]
fn dem_try_height_succeeds_for_interior_query() {
    let dem = flat_2x2_dem();
    let h = dem.try_height(1.0, 1.0).unwrap();
    // Bilinear interpolation at the exact center of the 2x2 grid
    assert!(h.is_finite());
}

#[test]
fn dem_infallible_height_panics_outside_grid() {
    use std::panic::catch_unwind;
    let dem = flat_2x2_dem();
    let result = catch_unwind(|| dem.height(100.0, 0.5));
    assert!(result.is_err(), "expected panic for out-of-bounds query");
}

// ─── DemGrid cell-center coordinate helpers ────────────────────────────────

#[test]
fn dem_grid_center_helpers_match_expected_values() {
    let dem = flat_2x2_dem();
    assert_eq!(dem.xmin_center_m(), 0.5);
    assert_eq!(dem.ymin_center_m(), 0.5);
    assert_eq!(dem.xmax_center_m(), 1.5);
    assert_eq!(dem.ymax_center_m(), 1.5);
}

// ─── ClampedDemGrid fallback behaviour ────────────────────────────────────

fn flat_3x3_clamped() -> ClampedDemGrid {
    let text = "ncols 3\nnrows 3\nxllcorner 0.0\nyllcorner 0.0\ncellsize 1.0\nNODATA_value -9999\n10.0 10.0 10.0\n10.0 10.0 10.0\n10.0 10.0 10.0\n";
    let dem = DemGrid::from_ascii_grid_str(text).unwrap();
    ClampedDemGrid::from_grid(dem)
}

#[test]
fn clamped_dem_does_not_error_for_query_outside_grid() {
    let dem = flat_3x3_clamped();
    // query well outside the grid
    let result = dem.try_height(100.0, 50.0);
    assert!(
        result.is_ok(),
        "clamped DEM should not error outside bounds"
    );
    assert_eq!(result.unwrap(), 10.0);
}

#[test]
fn clamped_dem_normal_outside_grid_is_unit_length() {
    let dem = flat_3x3_clamped();
    let n = dem.try_normal(100.0, 100.0).unwrap();
    let norm = (n.x * n.x + n.y * n.y + n.z * n.z).sqrt();
    assert!(
        (norm - 1.0).abs() < 1.0e-10,
        "normal must be unit length, got norm={norm}"
    );
}

struct RealTerrainEnergyBudget {
    max_speed_mps: f64,
    max_kinetic_j: f64,
    max_total_energy_abs_j: f64,
    max_jump_height_m: f64,
}

fn assert_real_terrain_energy_budget(
    run: &TrajectoryRun,
    terrain: &dyn Terrain,
    radius_m: f64,
    budget: RealTerrainEnergyBudget,
) {
    assert!(
        run.samples.len() > 10,
        "trajectory should contain time history"
    );
    assert_eq!(run.summary.sample_count, run.samples.len());
    assert!(run.summary.final_speed_mps.is_finite());
    assert!(run.summary.max_speed_mps.is_finite());
    assert!(
        run.summary.max_speed_mps <= budget.max_speed_mps,
        "unexpected speed spike: {}",
        run.summary.max_speed_mps
    );
    assert!(run.summary.max_kinetic_energy_j.is_finite());
    assert!(run.summary.max_kinetic_energy_j >= 0.0);
    assert!(
        run.summary.max_kinetic_energy_j <= budget.max_kinetic_j,
        "unexpected kinetic-energy spike: {}",
        run.summary.max_kinetic_energy_j
    );

    let mut max_jump_height_m = f64::NEG_INFINITY;
    for sample in &run.samples {
        assert!(sample.time_s.is_finite(), "non-finite sample time");
        assert!(sample.x_m.is_finite(), "non-finite sample x");
        assert!(sample.y_m.is_finite(), "non-finite sample y");
        assert!(sample.z_m.is_finite(), "non-finite sample z");
        assert!(sample.vx_mps.is_finite(), "non-finite sample vx");
        assert!(sample.vy_mps.is_finite(), "non-finite sample vy");
        assert!(sample.vz_mps.is_finite(), "non-finite sample vz");
        assert!(sample.speed_mps.is_finite(), "non-finite sample speed");
        assert!(
            sample.speed_mps <= budget.max_speed_mps,
            "sample speed exceeded budget: {}",
            sample.speed_mps
        );
        assert!(sample.kinetic_j.is_finite(), "non-finite kinetic energy");
        assert!(sample.kinetic_j >= 0.0, "negative kinetic energy");
        assert!(
            sample.kinetic_j <= budget.max_kinetic_j,
            "sample kinetic energy exceeded budget: {}",
            sample.kinetic_j
        );
        assert!(
            sample.rotational_j.is_finite(),
            "non-finite rotational energy"
        );
        assert!(sample.rotational_j >= 0.0, "negative rotational energy");
        assert!(
            sample.potential_j.is_finite(),
            "non-finite potential energy"
        );
        assert!(sample.total_energy_j.is_finite(), "non-finite total energy");
        assert!(
            sample.total_energy_j.abs() <= budget.max_total_energy_abs_j,
            "sample total energy exceeded budget: {}",
            sample.total_energy_j
        );
        let ground = terrain.try_height(sample.x_m, sample.y_m).unwrap();
        let jump_height_m = sample.z_m - ground - radius_m;
        assert!(
            jump_height_m >= -1.0e-6,
            "sample penetrated below terrain envelope: {jump_height_m}"
        );
        max_jump_height_m = max_jump_height_m.max(jump_height_m);
    }
    assert!(max_jump_height_m.is_finite());
    assert!(
        max_jump_height_m <= budget.max_jump_height_m,
        "unexpected jump-height spike: {max_jump_height_m}"
    );
}

#[test]
fn real_tschamut_dem_trajectory_has_finite_bounded_physics() {
    let terrain_path = format!(
        "{}/data/processed/tschamut2014/terrain.asc",
        env!("CARGO_MANIFEST_DIR")
    );
    let terrain = DemGrid::from_ascii_grid(&terrain_path).unwrap();
    let radius_m = 0.30;
    let start_x = -25.0;
    let start_y = 300.0;
    let start_ground_z = terrain.try_height(start_x, start_y).unwrap();
    let config = SimulationConfig {
        block: SphereBlock::new(radius_m, 100.0),
        initial_position_m: [start_x, start_y, start_ground_z + radius_m + 1.0],
        initial_velocity_mps: [8.0, -3.0, 0.0],
        initial_angular_velocity_radps: [0.0, 0.0, 0.0],
        terrain: TerrainConfig::EsriAsciiGrid { path: terrain_path },
        dt_s: 0.02,
        max_time_s: 2.0,
        gravity_mps2: 9.81,
        normal_restitution: 0.25,
        tangential_restitution: 0.85,
        friction_coefficient: 0.45,
        rolling_resistance_coefficient: 0.0,
        contact_model: Default::default(),
        soil_interaction_model: Default::default(),
        soil_strength_pa: 0.0,
        scarring_drag_coefficient: 0.0,
        scarring_layer_density_kgpm3: 0.0,
        scarring_max_depth_m: None,
        roughness_model: Default::default(),
        roughness_std_normal: 0.0,
        roughness_std_tangent: 0.0,
        roughness_std_angle: 0.0,
        stop_speed_mps: 0.05,
        random_seed: None,
        release_perturbation: Default::default(),
    };

    let run = simulate_one_trajectory(
        &config,
        TrajectoryRequest::new("real_tschamut_dem_golden", "trajectory_000000", None),
    )
    .unwrap();

    assert_real_terrain_energy_budget(
        &run,
        &terrain,
        radius_m,
        RealTerrainEnergyBudget {
            max_speed_mps: 40.0,
            max_kinetic_j: 100_000.0,
            max_total_energy_abs_j: 2_000_000.0,
            max_jump_height_m: 20.0,
        },
    );
    assert!(run.summary.runout_m > 5.0, "runout should be non-trivial");
    assert!(
        run.summary.final_position_m[0] > start_x,
        "trajectory should move generally east/down-slope on the fixture"
    );
}

#[test]
fn real_tschamut_stochastic_contact_replay_is_deterministic_and_bounded() {
    let terrain_path = format!(
        "{}/validation/data/processed/tschamut/terrain.asc",
        env!("CARGO_MANIFEST_DIR")
    );
    let terrain = ClampedDemGrid::from_grid(DemGrid::from_ascii_grid(&terrain_path).unwrap());
    let radius_m = 0.176667;
    let start_x = 33.4;
    let start_y = 236.67;
    let start_ground_z = terrain.try_height(start_x, start_y).unwrap();
    let config = SimulationConfig {
        block: SphereBlock::new(radius_m, 69.0),
        initial_position_m: [start_x, start_y, start_ground_z + radius_m],
        initial_velocity_mps: [0.74314, 1.3547, 0.76954],
        initial_angular_velocity_radps: [0.0, 0.0, 0.0],
        terrain: TerrainConfig::EsriAsciiGridClamped {
            path: terrain_path.clone(),
        },
        dt_s: 0.02,
        max_time_s: 3.0,
        gravity_mps2: 9.81,
        normal_restitution: 0.25,
        tangential_restitution: 0.85,
        friction_coefficient: 0.45,
        rolling_resistance_coefficient: 0.0,
        contact_model: Default::default(),
        soil_interaction_model: Default::default(),
        soil_strength_pa: 0.0,
        scarring_drag_coefficient: 0.0,
        scarring_layer_density_kgpm3: 0.0,
        scarring_max_depth_m: None,
        roughness_model: RoughnessModel::StochasticContactV1,
        roughness_std_normal: 0.08,
        roughness_std_tangent: 0.06,
        roughness_std_angle: 0.08,
        stop_speed_mps: 0.1,
        random_seed: None,
        release_perturbation: Default::default(),
    };
    let request = TrajectoryRequest::new(
        "validation_tschamut_basic_replay",
        "trajectory_000000",
        Some(34014),
    );

    let first = simulate_one_trajectory(&config, request.clone()).unwrap();
    let second = simulate_one_trajectory(&config, request).unwrap();

    assert_eq!(first.summary, second.summary);
    assert_eq!(first.samples, second.samples);
    assert_real_terrain_energy_budget(
        &first,
        &terrain,
        radius_m,
        RealTerrainEnergyBudget {
            max_speed_mps: 30.0,
            max_kinetic_j: 25_000.0,
            max_total_energy_abs_j: 150_000.0,
            max_jump_height_m: 20.0,
        },
    );
    assert!(first.summary.runout_m > 1.0, "runout should be non-trivial");
}

#[test]
fn real_chant_sura_dem_trajectory_has_finite_bounded_physics() {
    let terrain_path = format!(
        "{}/validation/data/processed/chant_sura_2020/terrain_rf16_contact.asc",
        env!("CARGO_MANIFEST_DIR")
    );
    let terrain = DemGrid::from_ascii_grid(&terrain_path).unwrap();
    let radius_m = 0.265790716577;
    let start_x = 2793260.85;
    let start_y = 1180275.93;
    let start_ground_z = terrain.try_height(start_x, start_y).unwrap();
    let config = SimulationConfig {
        block: SphereBlock::new(radius_m, 210.0),
        initial_position_m: [start_x, start_y, start_ground_z + radius_m],
        initial_velocity_mps: [1.17599999905, -4.33600000013, -4.23375],
        initial_angular_velocity_radps: [0.0, 0.0, 0.0],
        terrain: TerrainConfig::EsriAsciiGridClamped { path: terrain_path },
        dt_s: 0.005,
        max_time_s: 1.15,
        gravity_mps2: 9.81,
        normal_restitution: 0.25,
        tangential_restitution: 0.85,
        friction_coefficient: 0.45,
        rolling_resistance_coefficient: 0.0,
        contact_model: Default::default(),
        soil_interaction_model: Default::default(),
        soil_strength_pa: 0.0,
        scarring_drag_coefficient: 0.0,
        scarring_layer_density_kgpm3: 0.0,
        scarring_max_depth_m: None,
        roughness_model: Default::default(),
        roughness_std_normal: 0.0,
        roughness_std_tangent: 0.0,
        roughness_std_angle: 0.0,
        stop_speed_mps: 0.05,
        random_seed: None,
        release_perturbation: Default::default(),
    };

    let run = simulate_one_trajectory(
        &config,
        TrajectoryRequest::new("real_chant_sura_dem_golden", "trajectory_000000", None),
    )
    .unwrap();

    assert_real_terrain_energy_budget(
        &run,
        &terrain,
        radius_m,
        RealTerrainEnergyBudget {
            max_speed_mps: 50.0,
            max_kinetic_j: 100_000.0,
            max_total_energy_abs_j: 6_000_000.0,
            max_jump_height_m: 10.0,
        },
    );
    assert!(run.summary.runout_m > 0.5, "runout should be non-trivial");
    assert!(
        run.summary.final_position_m[1] < start_y,
        "trajectory should move generally downslope on the RF16 fixture"
    );
}
