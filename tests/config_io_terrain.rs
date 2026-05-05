use approx::assert_abs_diff_eq;
use rust_rockfall::{
    geometry::SphereBlock,
    io,
    simulation::{SimulationConfig, SimulationError, TerrainConfig},
    state::ContactState,
    stochastic::{ReleasePerturbation, RoughnessModel},
    terrain::{
        ChannelizedGully, ClampedDemGrid, DemGrid, GaussianBump, Paraboloid, Plane,
        SinusoidalRoughSlope, StepTerrain, TerracedSlope, Terrain, TerrainError, VShapedValley,
    },
    validation::{load_case, run_case_file, CaseStatus},
    ContactModel, SoilInteractionModel, Vec3,
};
use std::{
    fs,
    path::PathBuf,
    time::{SystemTime, UNIX_EPOCH},
};

#[test]
fn plane_height_normal_and_sphere_distance_are_consistent() {
    let terrain = Plane {
        z0_m: 2.0,
        slope_x: 0.5,
        slope_y: -0.25,
    };

    assert_abs_diff_eq!(terrain.height(4.0, 2.0), 3.5, epsilon = 1.0e-12);
    assert_abs_diff_eq!(terrain.normal(4.0, 2.0).norm(), 1.0, epsilon = 1.0e-12);
    assert_abs_diff_eq!(
        terrain.signed_distance_sphere(Vec3::new(0.0, 0.0, 3.0), 0.5),
        (Vec3::new(0.0, 0.0, 1.0).dot(&terrain.normal(0.0, 0.0))) - 0.5,
        epsilon = 1.0e-12
    );
}

#[test]
fn paraboloid_height_and_normal_use_quadratic_gradient() {
    let terrain = Paraboloid {
        z0_m: 1.0,
        ax: 0.25,
        ay: 0.5,
    };

    assert_abs_diff_eq!(terrain.height(2.0, 3.0), 6.5, epsilon = 1.0e-12);
    let expected = Vec3::new(-1.0, -3.0, 1.0).normalize();
    assert_abs_diff_eq!(terrain.normal(2.0, 3.0).x, expected.x, epsilon = 1.0e-12);
    assert_abs_diff_eq!(terrain.normal(2.0, 3.0).y, expected.y, epsilon = 1.0e-12);
    assert_abs_diff_eq!(terrain.normal(2.0, 3.0).z, expected.z, epsilon = 1.0e-12);
}

#[test]
fn step_terrain_switches_height_at_step_location() {
    let terrain = StepTerrain {
        step_x_m: 10.0,
        high_z_m: 5.0,
        low_z_m: 1.0,
    };

    assert_abs_diff_eq!(terrain.height(9.99, 0.0), 5.0, epsilon = 1.0e-12);
    assert_abs_diff_eq!(terrain.height(10.0, 0.0), 1.0, epsilon = 1.0e-12);
    assert_eq!(terrain.normal(10.0, 0.0), Vec3::new(0.0, 0.0, 1.0));
}

#[test]
fn procedural_terrain_variants_have_expected_heights_and_unit_normals() {
    let valley = VShapedValley {
        z0_m: 0.0,
        slope_x: -0.2,
        side_slope_abs_y: 0.5,
    };
    assert_abs_diff_eq!(valley.height(1.0, -2.0), 0.8, epsilon = 1.0e-12);
    assert_abs_diff_eq!(valley.normal(1.0, -2.0).norm(), 1.0, epsilon = 1.0e-12);

    let terrace = TerracedSlope {
        z0_m: 0.0,
        slope_x: -0.1,
        terrace_width_m: 2.0,
        terrace_height_m: -0.5,
    };
    assert_abs_diff_eq!(terrace.height(4.5, 0.0), -1.45, epsilon = 1.0e-12);

    let rough = SinusoidalRoughSlope {
        z0_m: 0.0,
        slope_x: -0.1,
        amplitude_m: 1.0,
        wavelength_m: 4.0,
    };
    assert_abs_diff_eq!(rough.height(1.0, 0.0), 0.9, epsilon = 1.0e-12);

    let bump = GaussianBump {
        z0_m: 0.0,
        slope_x: 0.0,
        center_x_m: 0.0,
        center_y_m: 0.0,
        height_m: 2.0,
        sigma_m: 1.0,
    };
    assert_abs_diff_eq!(bump.height(0.0, 0.0), 2.0, epsilon = 1.0e-12);

    let gully = ChannelizedGully {
        z0_m: 0.0,
        slope_x: -0.1,
        depth_m: 2.0,
        width_m: 1.0,
    };
    assert_abs_diff_eq!(gully.height(0.0, 0.0), -2.0, epsilon = 1.0e-12);
    assert_abs_diff_eq!(gully.normal(2.0, 0.5).norm(), 1.0, epsilon = 1.0e-12);
}

#[test]
fn dem_parser_reports_header_value_count_and_bounds_errors() {
    assert!(matches!(
        DemGrid::from_ascii_grid_str("ncols nope\n"),
        Err(TerrainError::Header("ncols"))
    ));

    assert!(matches!(
        DemGrid::from_ascii_grid_str(
            "ncols 2\nnrows 2\nxllcorner 0\nyllcorner 0\ncellsize 1\nNODATA_value -9999\n1 2 3\n"
        ),
        Err(TerrainError::ValueCount {
            expected: 4,
            actual: 3
        })
    ));

    let dem = DemGrid::from_ascii_grid_str(
        "ncols 2\nnrows 2\nxllcorner 0\nyllcorner 0\ncellsize 1\nNODATA_value -9999\n2 4\n0 2\n",
    )
    .unwrap();
    assert!(matches!(
        dem.try_height(-0.1, 0.0),
        Err(TerrainError::OutOfBounds { .. })
    ));
}

#[test]
fn clamped_dem_keeps_boundary_queries_finite_without_changing_strict_dem() {
    let dem = DemGrid::from_ascii_grid_str(
        "ncols 3\nnrows 3\nxllcorner 0\nyllcorner 0\ncellsize 1\nNODATA_value -9999\n4 5 6\n2 3 4\n0 1 2\n",
    )
    .unwrap();
    assert!(matches!(
        dem.try_height(-0.5, 0.5),
        Err(TerrainError::OutOfBounds { .. })
    ));

    let clamped = ClampedDemGrid::from_grid(dem);
    assert_abs_diff_eq!(clamped.height(-0.5, 0.5), 1.0, epsilon = 1.0e-12);
    assert_abs_diff_eq!(clamped.height(2.5, 1.5), 5.0, epsilon = 1.0e-12);
    assert_abs_diff_eq!(clamped.normal(-0.5, 0.5).norm(), 1.0, epsilon = 1.0e-12);
}

#[test]
fn clamped_dem_normal_matches_planar_dem_interior_and_edge() {
    let dem = DemGrid::from_ascii_grid_str(
        "ncols 3\nnrows 3\nxllcorner 0\nyllcorner 0\ncellsize 1\nNODATA_value -9999\n4 5 6\n2 3 4\n0 1 2\n",
    )
    .unwrap();
    let clamped = ClampedDemGrid::from_grid(dem);
    let expected = Vec3::new(-1.0, -2.0, 1.0).normalize();
    let interior = clamped.normal(1.0, 1.0);
    let edge = clamped.normal(-0.5, 1.0);

    assert_abs_diff_eq!(interior.x, expected.x, epsilon = 1.0e-12);
    assert_abs_diff_eq!(interior.y, expected.y, epsilon = 1.0e-12);
    assert_abs_diff_eq!(interior.z, expected.z, epsilon = 1.0e-12);
    assert_abs_diff_eq!(edge.x, expected.x, epsilon = 1.0e-12);
    assert_abs_diff_eq!(edge.y, expected.y, epsilon = 1.0e-12);
    assert_abs_diff_eq!(edge.z, expected.z, epsilon = 1.0e-12);
}

#[test]
fn terrain_config_builds_each_supported_variant() {
    assert_abs_diff_eq!(
        TerrainConfig::Plane {
            z0_m: 1.0,
            slope_x: 0.0,
            slope_y: 0.0
        }
        .build()
        .unwrap()
        .height(0.0, 0.0),
        1.0,
        epsilon = 1.0e-12
    );

    assert_abs_diff_eq!(
        TerrainConfig::Paraboloid {
            z0_m: 0.0,
            ax: 1.0,
            ay: 0.0
        }
        .build()
        .unwrap()
        .height(2.0, 0.0),
        4.0,
        epsilon = 1.0e-12
    );

    assert_abs_diff_eq!(
        TerrainConfig::Step {
            step_x_m: 1.0,
            high_z_m: 3.0,
            low_z_m: -1.0
        }
        .build()
        .unwrap()
        .height(2.0, 0.0),
        -1.0,
        epsilon = 1.0e-12
    );

    assert_abs_diff_eq!(
        TerrainConfig::VShapedValley {
            z0_m: 0.0,
            slope_x: 0.0,
            side_slope_abs_y: 0.5
        }
        .build()
        .unwrap()
        .height(0.0, 2.0),
        1.0,
        epsilon = 1.0e-12
    );

    assert_abs_diff_eq!(
        TerrainConfig::TerracedSlope {
            z0_m: 0.0,
            slope_x: 0.0,
            terrace_width_m: 2.0,
            terrace_height_m: -1.0
        }
        .build()
        .unwrap()
        .height(5.0, 0.0),
        -2.0,
        epsilon = 1.0e-12
    );

    assert_abs_diff_eq!(
        TerrainConfig::GaussianBump {
            z0_m: 0.0,
            slope_x: 0.0,
            center_x_m: 0.0,
            center_y_m: 0.0,
            height_m: 1.0,
            sigma_m: 1.0
        }
        .build()
        .unwrap()
        .height(0.0, 0.0),
        1.0,
        epsilon = 1.0e-12
    );
}

#[test]
fn esri_ascii_grid_config_reads_from_file() {
    let path = temp_path("terrain_config.asc");
    fs::write(
        &path,
        "ncols 2\nnrows 2\nxllcorner 0\nyllcorner 0\ncellsize 1\nNODATA_value -9999\n2 4\n0 2\n",
    )
    .unwrap();

    let terrain = TerrainConfig::EsriAsciiGrid {
        path: path.to_string_lossy().to_string(),
    }
    .build()
    .unwrap();

    assert_abs_diff_eq!(terrain.height(0.5, 0.5), 2.0, epsilon = 1.0e-12);
    fs::remove_file(path).unwrap();
}

#[test]
fn clamped_esri_ascii_grid_config_reads_from_file() {
    let path = temp_path("terrain_config_clamped.asc");
    fs::write(
        &path,
        "ncols 2\nnrows 2\nxllcorner 0\nyllcorner 0\ncellsize 1\nNODATA_value -9999\n2 4\n0 2\n",
    )
    .unwrap();

    let terrain = TerrainConfig::EsriAsciiGridClamped {
        path: path.to_string_lossy().to_string(),
    }
    .build()
    .unwrap();

    assert_abs_diff_eq!(terrain.height(-1.0, 0.5), 1.0, epsilon = 1.0e-12);
    assert_abs_diff_eq!(terrain.height(0.5, 0.5), 2.0, epsilon = 1.0e-12);
    fs::remove_file(path).unwrap();
}

#[test]
fn simulation_config_json_defaults_and_seeded_initial_state_are_deterministic() {
    let json = r#"{
        "block": { "radius_m": 0.5, "mass_kg": 10.0 },
        "initial_position_m": [0.0, 0.0, 2.0],
        "initial_velocity_mps": [1.0, 0.0, 0.0],
        "terrain": { "kind": "plane", "z0_m": 0.0, "slope_x": 0.0, "slope_y": 0.0 },
        "dt_s": 0.01,
        "max_time_s": 1.0,
        "random_seed": 7,
        "release_perturbation": { "position_uniform_m": 0.1, "velocity_uniform_mps": 0.2 }
    }"#;

    let config: SimulationConfig = serde_json::from_str(json).unwrap();
    assert_abs_diff_eq!(config.gravity_mps2, 9.81, epsilon = 1.0e-12);
    assert_abs_diff_eq!(config.normal_restitution, 0.25, epsilon = 1.0e-12);
    assert_eq!(config.contact_model, ContactModel::TranslationalV0);
    assert_eq!(config.soil_interaction_model, SoilInteractionModel::None);
    assert_eq!(config.roughness_model, RoughnessModel::None);
    assert_eq!(config.initial_state(), config.initial_state());
}

#[test]
fn simulation_config_json_accepts_rotational_contact_model() {
    let json = r#"{
        "block": { "radius_m": 0.5, "mass_kg": 10.0 },
        "initial_position_m": [0.0, 0.0, 0.5],
        "initial_velocity_mps": [1.0, 0.0, 0.0],
        "initial_angular_velocity_radps": [0.0, 2.0, 0.0],
        "terrain": { "kind": "plane", "z0_m": 0.0, "slope_x": 0.0, "slope_y": 0.0 },
        "dt_s": 0.01,
        "max_time_s": 0.02,
        "contact_model": "sphere_rotational_v1",
        "rolling_resistance_coefficient": 0.1
    }"#;

    let config: SimulationConfig = serde_json::from_str(json).unwrap();
    assert_eq!(config.contact_model, ContactModel::SphereRotationalV1);
    assert_abs_diff_eq!(
        config.rolling_resistance_coefficient,
        0.1,
        epsilon = 1.0e-12
    );
    assert!(!config.run().unwrap().samples.is_empty());
}

#[test]
fn simulation_config_json_accepts_stochastic_contact_roughness() {
    let json = r#"{
        "block": { "radius_m": 0.5, "mass_kg": 10.0 },
        "initial_position_m": [0.0, 0.0, 2.0],
        "initial_velocity_mps": [1.0, 0.0, -0.5],
        "terrain": { "kind": "plane", "z0_m": 0.0, "slope_x": 0.0, "slope_y": 0.0 },
        "dt_s": 0.01,
        "max_time_s": 1.0,
        "random_seed": 11,
        "roughness_model": "stochastic_contact_v1",
        "roughness_std_normal": 0.05,
        "roughness_std_tangent": 0.04,
        "roughness_std_angle": 0.03
    }"#;

    let config: SimulationConfig = serde_json::from_str(json).unwrap();
    assert_eq!(config.roughness_model, RoughnessModel::StochasticContactV1);
    assert_abs_diff_eq!(config.roughness_std_angle, 0.03, epsilon = 1.0e-12);
    assert_eq!(config.run().unwrap().samples, config.run().unwrap().samples);
}

#[test]
fn simulation_config_json_accepts_scarring_contact_model() {
    let json = r#"{
        "block": { "radius_m": 0.5, "mass_kg": 10.0 },
        "initial_position_m": [0.0, 0.0, 2.0],
        "initial_velocity_mps": [0.0, 0.0, -1.0],
        "terrain": { "kind": "plane", "z0_m": 0.0, "slope_x": 0.0, "slope_y": 0.0 },
        "dt_s": 0.01,
        "max_time_s": 1.0,
        "soil_interaction_model": "scarring_contact_v1",
        "soil_strength_pa": 100000.0,
        "scarring_drag_coefficient": 1.0,
        "scarring_layer_density_kgpm3": 1600.0,
        "scarring_max_depth_m": 0.05
    }"#;

    let config: SimulationConfig = serde_json::from_str(json).unwrap();
    assert_eq!(
        config.soil_interaction_model,
        SoilInteractionModel::ScarringContactV1
    );
    let result = config.run().unwrap();
    assert!(result
        .samples
        .iter()
        .any(|sample| sample.scarring_energy_loss_j > 0.0));
}

#[test]
fn validation_yaml_rejects_unknown_contact_model() {
    let path = temp_path("bad_contact_model.yaml");
    fs::write(
        &path,
        r#"
case_id: bad_contact_model
terrain: { type: plane, parameters: { z0_m: 0.0, slope_x: 0.0, slope_y: 0.0 } }
block: { mass: 1.0, radius: 0.5 }
parameters:
  contact_model: hidden_magic
"#,
    )
    .unwrap();

    assert!(load_case(&path).is_err());
    fs::remove_file(path).unwrap();
}

#[test]
fn validation_yaml_rejects_unknown_roughness_model() {
    let path = temp_path("bad_roughness_model.yaml");
    fs::write(
        &path,
        r#"
case_id: bad_roughness_model
terrain: { type: plane, parameters: { z0_m: 0.0, slope_x: 0.0, slope_y: 0.0 } }
block: { mass: 1.0, radius: 0.5 }
parameters:
  roughness_model: hidden_magic
"#,
    )
    .unwrap();

    assert!(load_case(&path).is_err());
    fs::remove_file(path).unwrap();
}

#[test]
fn validation_yaml_rejects_unknown_soil_interaction_model() {
    let path = temp_path("bad_soil_interaction_model.yaml");
    fs::write(
        &path,
        r#"
case_id: bad_soil_interaction_model
terrain: { type: plane, parameters: { z0_m: 0.0, slope_x: 0.0, slope_y: 0.0 } }
block: { mass: 1.0, radius: 0.5 }
parameters:
  soil_interaction_model: hidden_magic
"#,
    )
    .unwrap();

    assert!(load_case(&path).is_err());
    fs::remove_file(path).unwrap();
}

#[test]
fn simulation_validation_rejects_non_positive_inputs() {
    let mut config = minimal_config();
    config.block = SphereBlock::new(0.0, 1.0);
    assert!(matches!(
        config.run(),
        Err(SimulationError::NonPositive("block.radius_m"))
    ));

    let mut config = minimal_config();
    config.block = SphereBlock::new(1.0, 0.0);
    assert!(matches!(
        config.run(),
        Err(SimulationError::NonPositive("block.mass_kg"))
    ));

    let mut config = minimal_config();
    config.dt_s = 0.0;
    assert!(matches!(
        config.run(),
        Err(SimulationError::NonPositive("dt_s"))
    ));

    let mut config = minimal_config();
    config.max_time_s = 0.0;
    assert!(matches!(
        config.run(),
        Err(SimulationError::NonPositive("max_time_s"))
    ));

    let mut config = minimal_config();
    config.gravity_mps2 = 0.0;
    assert!(matches!(
        config.run(),
        Err(SimulationError::NonPositive("gravity_mps2"))
    ));

    let mut config = minimal_config();
    config.rolling_resistance_coefficient = -0.1;
    assert!(matches!(
        config.run(),
        Err(SimulationError::NonPositive(
            "rolling_resistance_coefficient"
        ))
    ));

    let mut config = minimal_config();
    config.roughness_std_angle = -0.1;
    assert!(matches!(
        config.run(),
        Err(SimulationError::NonPositive("roughness_std_angle"))
    ));

    let mut config = minimal_config();
    config.soil_strength_pa = -1.0;
    assert!(matches!(
        config.run(),
        Err(SimulationError::NonPositive("soil_strength_pa"))
    ));

    let mut config = minimal_config();
    config.scarring_max_depth_m = Some(-0.1);
    assert!(matches!(
        config.run(),
        Err(SimulationError::NonPositive("scarring_max_depth_m"))
    ));
}

#[test]
fn read_config_reports_json_errors_and_write_csv_round_trips_samples() {
    let bad_config_path = temp_path("bad_config.json");
    fs::write(&bad_config_path, "{not json").unwrap();
    assert!(io::read_config(&bad_config_path).is_err());
    fs::remove_file(bad_config_path).unwrap();

    let result = minimal_config().run().unwrap();
    let csv_path = temp_path("trajectory.csv");
    io::write_trajectory_csv(&csv_path, &result.samples).unwrap();
    let csv_text = fs::read_to_string(&csv_path).unwrap();

    assert!(csv_text.contains("time_s"));
    assert!(csv_text.contains("contact_state"));
    assert!(
        csv_text.contains(match result.samples.last().unwrap().contact_state {
            ContactState::Airborne => "airborne",
            ContactState::Sliding => "sliding",
            ContactState::Impact => "impact",
            ContactState::Rolling => "rolling",
            ContactState::Stopped => "stopped",
        })
    );
    assert!(csv_text.contains("omega_x_radps"));
    assert!(csv_text.contains("rolling_residual_mps"));
    assert!(csv_text.contains("scarring_depth_m"));
    assert!(csv_text.contains("scarring_energy_loss_j"));
    fs::remove_file(csv_path).unwrap();
}

#[test]
fn write_csv_reports_path_errors() {
    let result = minimal_config().run().unwrap();
    let directory_path = temp_path("csv_directory");
    fs::create_dir(&directory_path).unwrap();

    assert!(io::write_trajectory_csv(&directory_path, &result.samples).is_err());
    fs::remove_dir(directory_path).unwrap();
}

#[test]
fn read_config_successfully_loads_example_shape() {
    let path = temp_path("valid_config.json");
    fs::write(
        &path,
        r#"{
            "block": { "radius_m": 0.5, "mass_kg": 10.0 },
            "initial_position_m": [0.0, 0.0, 2.0],
            "initial_velocity_mps": [1.0, 0.0, 0.0],
            "terrain": { "kind": "step", "step_x_m": 1.0, "high_z_m": 0.0, "low_z_m": -1.0 },
            "dt_s": 0.01,
            "max_time_s": 1.0
        }"#,
    )
    .unwrap();

    let config = io::read_config(&path).unwrap();
    assert!(matches!(config.terrain, TerrainConfig::Step { .. }));
    fs::remove_file(path).unwrap();
}

#[test]
fn validation_case_runner_writes_metrics_for_synthetic_fixture() {
    let output = PathBuf::from("validation/results/synthetic_plane_basic_metrics.json");
    let _ = fs::remove_file(&output);

    let report = run_case_file("validation/cases/synthetic_plane_basic.yaml").unwrap();

    assert!(matches!(
        report.status,
        CaseStatus::Passed | CaseStatus::Failed
    ));
    assert!(report.metrics.contains_key("deposition_point_error_m"));
    assert!(output.exists());
    fs::remove_file(output).unwrap();
}

#[test]
fn tschamut_validation_fixture_runs_reproducibly() {
    let output = PathBuf::from("validation/results/tschamut_basic_metrics.json");
    let trajectory = PathBuf::from("validation/results/tschamut_basic_trajectory.csv");
    let ensemble = PathBuf::from("validation/results/tschamut_basic_ensemble_deposition.csv");
    let _ = fs::remove_file(&output);
    let _ = fs::remove_file(&trajectory);
    let _ = fs::remove_file(&ensemble);

    let first = run_case_file("validation/cases/tschamut_basic.yaml").unwrap();
    let second = run_case_file("validation/cases/tschamut_basic.yaml").unwrap();

    assert_eq!(first.status, CaseStatus::Passed);
    assert_eq!(first.metrics, second.metrics);
    assert!(first.metrics.contains_key("deposition_centroid_error_m"));
    assert!(first.metrics.contains_key("runout_distance_error_m"));
    assert!(output.exists());
    assert!(trajectory.exists());
    assert!(ensemble.exists());
    fs::remove_file(output).unwrap();
    fs::remove_file(trajectory).unwrap();
    fs::remove_file(ensemble).unwrap();
}

fn minimal_config() -> SimulationConfig {
    SimulationConfig {
        block: SphereBlock::new(0.5, 10.0),
        initial_position_m: [0.0, 0.0, 2.0],
        initial_velocity_mps: [1.0, 0.0, 0.0],
        initial_angular_velocity_radps: [0.0, 0.0, 0.0],
        terrain: TerrainConfig::Plane {
            z0_m: 0.0,
            slope_x: 0.0,
            slope_y: 0.0,
        },
        dt_s: 0.01,
        max_time_s: 0.05,
        gravity_mps2: 9.81,
        normal_restitution: 0.25,
        tangential_restitution: 0.85,
        friction_coefficient: 0.45,
        rolling_resistance_coefficient: 0.0,
        contact_model: ContactModel::TranslationalV0,
        soil_interaction_model: SoilInteractionModel::None,
        soil_strength_pa: 0.0,
        scarring_drag_coefficient: 0.0,
        scarring_layer_density_kgpm3: 0.0,
        scarring_max_depth_m: None,
        roughness_model: RoughnessModel::None,
        roughness_std_normal: 0.0,
        roughness_std_tangent: 0.0,
        roughness_std_angle: 0.0,
        stop_speed_mps: 0.1,
        random_seed: None,
        release_perturbation: ReleasePerturbation::default(),
    }
}

fn temp_path(name: &str) -> PathBuf {
    let nonce = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .as_nanos();
    std::env::temp_dir().join(format!("rust_rockfall_{nonce}_{name}"))
}
