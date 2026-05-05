use approx::{assert_abs_diff_eq, assert_relative_eq};
use rust_rockfall::{
    dynamics::{
        acceleration_from_gravity, apply_contact_friction, estimate_scarring_depth_m,
        resolve_rotational_sphere_contact, resolve_sphere_contact, ScarringDepthSource,
        ScarringSettings, SoilInteractionModel,
    },
    geometry::SphereBlock,
    integrator::{simulate_fixed_step, IntegratorSettings},
    simulation::{SimulationConfig, TerrainConfig},
    state::{BodyState, ContactState, EnergyDiagnostics},
    stochastic::{sample_release, ContactRoughness, ReleasePerturbation, RoughnessModel},
    terrain::{Plane, Terrain},
    ContactModel, Vec3,
};

#[test]
fn free_flight_energy_is_conserved_without_contact() {
    let block = SphereBlock::new(0.5, 10.0);
    let terrain = Plane::horizontal(-1000.0);
    let initial = BodyState::new(Vec3::new(0.0, 0.0, 100.0), Vec3::new(3.0, -1.0, 4.0));
    let samples = simulate_fixed_step(
        initial,
        block,
        &terrain,
        IntegratorSettings {
            dt_s: 0.01,
            max_time_s: 1.0,
            gravity_mps2: 9.81,
            normal_restitution: 0.0,
            tangential_restitution: 1.0,
            friction_coefficient: 0.0,
            rolling_resistance_coefficient: 0.0,
            stop_speed_mps: 0.0,
            contact_model: ContactModel::TranslationalV0,
            scarring: ScarringSettings::default(),
            roughness: ContactRoughness::default(),
            roughness_seed: None,
        },
    );
    let first = samples.first().unwrap().total_energy_j;
    let last = samples.last().unwrap().total_energy_j;
    assert_relative_eq!(first, last, epsilon = 1.0e-8, max_relative = 1.0e-10);
}

#[test]
fn gravity_acceleration_matches_configuration() {
    assert_eq!(acceleration_from_gravity(9.81), Vec3::new(0.0, 0.0, -9.81));
}

#[test]
fn horizontal_plane_rebound_matches_normal_restitution() {
    let terrain = Plane::horizontal(0.0);
    let mut state = BodyState::new(Vec3::new(0.0, 0.0, 0.4), Vec3::new(1.0, 0.0, -10.0));
    let response = resolve_sphere_contact(&mut state, &terrain, 0.5, 0.3, 1.0, 0.0);

    assert!(response.impacted);
    assert_abs_diff_eq!(state.position_m.z, 0.5, epsilon = 1.0e-12);
    assert_abs_diff_eq!(state.velocity_mps.z, 3.0, epsilon = 1.0e-12);
    assert_abs_diff_eq!(state.velocity_mps.x, 1.0, epsilon = 1.0e-12);
}

#[test]
fn sphere_above_terrain_has_no_contact_response() {
    let terrain = Plane::horizontal(0.0);
    let mut state = BodyState::new(Vec3::new(0.0, 0.0, 2.0), Vec3::new(1.0, 0.0, -1.0));
    let before = state;

    let response = resolve_sphere_contact(&mut state, &terrain, 0.5, 0.3, 1.0, 0.0);

    assert!(!response.impacted);
    assert!(!response.sliding);
    assert_eq!(state, before);
}

#[test]
fn tangential_impact_response_is_limited_by_coulomb_friction() {
    let terrain = Plane::horizontal(0.0);
    let mut state = BodyState::new(Vec3::new(0.0, 0.0, 0.4), Vec3::new(10.0, 0.0, -2.0));

    resolve_sphere_contact(&mut state, &terrain, 0.5, 0.0, 0.0, 0.25);

    assert_abs_diff_eq!(state.velocity_mps.z, 0.0, epsilon = 1.0e-12);
    assert_abs_diff_eq!(state.velocity_mps.x, 9.5, epsilon = 1.0e-12);
}

#[test]
fn inclined_plane_rebound_respects_plane_normal() {
    let terrain = Plane {
        z0_m: 0.0,
        slope_x: -0.5,
        slope_y: 0.0,
    };
    let normal = terrain.normal(0.0, 0.0);
    let mut state = BodyState::new(Vec3::new(0.0, 0.0, 0.1), -6.0 * normal);
    resolve_sphere_contact(&mut state, &terrain, 0.5, 0.5, 1.0, 0.0);

    assert_abs_diff_eq!(state.velocity_mps.dot(&normal), 3.0, epsilon = 1.0e-12);
}

#[test]
fn coulomb_friction_stops_sliding_on_horizontal_plane() {
    let block = SphereBlock::new(0.5, 10.0);
    let terrain = Plane::horizontal(0.0);
    let initial = BodyState::new(Vec3::new(0.0, 0.0, 0.5), Vec3::new(1.0, 0.0, 0.0));
    let samples = simulate_fixed_step(
        initial,
        block,
        &terrain,
        IntegratorSettings {
            dt_s: 0.01,
            max_time_s: 5.0,
            gravity_mps2: 9.81,
            normal_restitution: 0.0,
            tangential_restitution: 1.0,
            friction_coefficient: 0.5,
            rolling_resistance_coefficient: 0.0,
            stop_speed_mps: 0.05,
            contact_model: ContactModel::TranslationalV0,
            scarring: ScarringSettings::default(),
            roughness: ContactRoughness::default(),
            roughness_seed: None,
        },
    );

    let last = samples.last().unwrap();
    assert_eq!(last.contact_state, ContactState::Stopped);
    assert!(last.speed_mps <= 0.05);
}

#[test]
fn low_friction_incline_does_not_stop_when_gravity_overcomes_friction() {
    let terrain = Plane {
        z0_m: 0.0,
        slope_x: -0.5,
        slope_y: 0.0,
    };
    let mut state = BodyState::new(Vec3::new(0.0, 0.0, 0.5), Vec3::zeros());

    let stopped = apply_contact_friction(&mut state, &terrain, 0.1, 9.81, 0.05, 0.1);

    assert!(!stopped);
    assert!(state.velocity_mps.norm() > 0.0);
}

#[test]
fn fixed_seed_reproduces_release_sample() {
    let initial = BodyState::new(Vec3::new(1.0, 2.0, 3.0), Vec3::new(4.0, 5.0, 6.0));
    let perturbation = ReleasePerturbation {
        position_uniform_m: 0.2,
        velocity_uniform_mps: 0.1,
    };

    let a = sample_release(initial, perturbation, 123);
    let b = sample_release(initial, perturbation, 123);
    assert_eq!(a, b);
}

#[test]
fn simple_inclined_plane_runout_is_finite_and_downslope() {
    let config = SimulationConfig {
        block: SphereBlock::new(0.5, 100.0),
        initial_position_m: [0.0, 0.0, 3.0],
        initial_velocity_mps: [1.0, 0.0, 0.0],
        initial_angular_velocity_radps: [0.0, 0.0, 0.0],
        terrain: TerrainConfig::Plane {
            z0_m: 0.0,
            slope_x: -0.2,
            slope_y: 0.0,
        },
        dt_s: 0.01,
        max_time_s: 10.0,
        gravity_mps2: 9.81,
        normal_restitution: 0.1,
        tangential_restitution: 0.8,
        friction_coefficient: 0.6,
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
    };

    let result = config.run().unwrap();
    let last = result.samples.last().unwrap();
    assert!(last.x_m > 0.0);
    assert!(result.samples.len() < 1002);
}

#[test]
fn zero_stochastic_contact_roughness_matches_baseline_exactly() {
    let baseline = roughness_test_config(RoughnessModel::None, 0.0, 0.0, 0.0, Some(99));
    let rough_zero =
        roughness_test_config(RoughnessModel::StochasticContactV1, 0.0, 0.0, 0.0, Some(99));

    assert_eq!(
        baseline.run().unwrap().samples,
        rough_zero.run().unwrap().samples
    );
}

#[test]
fn stochastic_contact_roughness_is_seed_reproducible() {
    let first = roughness_test_config(
        RoughnessModel::StochasticContactV1,
        0.05,
        0.05,
        0.05,
        Some(17),
    )
    .run()
    .unwrap();
    let repeat = roughness_test_config(
        RoughnessModel::StochasticContactV1,
        0.05,
        0.05,
        0.05,
        Some(17),
    )
    .run()
    .unwrap();
    let different = roughness_test_config(
        RoughnessModel::StochasticContactV1,
        0.05,
        0.05,
        0.05,
        Some(18),
    )
    .run()
    .unwrap();

    assert_eq!(first.samples, repeat.samples);
    assert_ne!(first.samples, different.samples);
}

#[test]
fn stochastic_contact_roughness_does_not_create_energy_spikes() {
    let result = roughness_test_config(
        RoughnessModel::StochasticContactV1,
        0.08,
        0.08,
        0.04,
        Some(1234),
    )
    .run()
    .unwrap();
    let max_energy_increase = result
        .samples
        .windows(2)
        .map(|pair| (pair[1].total_energy_j - pair[0].total_energy_j).max(0.0))
        .fold(0.0_f64, f64::max);

    assert_abs_diff_eq!(max_energy_increase, 0.0, epsilon = 1.0e-6);
}

#[test]
fn zero_effect_scarring_matches_no_soil_interaction_exactly() {
    let baseline = scarring_test_config(SoilInteractionModel::None, 0.0, 0.0, 0.0, None);
    let scarring_zero =
        scarring_test_config(SoilInteractionModel::ScarringContactV1, 0.0, 0.0, 0.0, None);

    assert_eq!(
        baseline.run().unwrap().samples,
        scarring_zero.run().unwrap().samples
    );
}

#[test]
fn scarring_depth_increases_with_normal_impact_speed() {
    let slow = estimate_scarring_depth_m(50.0, 0.5, 2.0, 100_000.0, None);
    let fast = estimate_scarring_depth_m(50.0, 0.5, 6.0, 100_000.0, None);

    assert!(fast > slow);
}

#[test]
fn scarring_depth_increases_as_soil_strength_decreases() {
    let strong = estimate_scarring_depth_m(50.0, 0.5, 4.0, 200_000.0, None);
    let weak = estimate_scarring_depth_m(50.0, 0.5, 4.0, 50_000.0, None);

    assert!(weak > strong);
}

#[test]
fn scarring_energy_loss_is_nonnegative_and_dissipative() {
    let config = scarring_test_config(
        SoilInteractionModel::ScarringContactV1,
        100_000.0,
        1.0,
        1600.0,
        Some(0.05),
    );
    let result = config.run().unwrap();
    let total_scarring_loss: f64 = result
        .samples
        .iter()
        .map(|sample| sample.scarring_energy_loss_j)
        .sum();
    let max_energy_increase = result
        .samples
        .windows(2)
        .map(|pair| (pair[1].total_energy_j - pair[0].total_energy_j).max(0.0))
        .fold(0.0_f64, f64::max);

    assert!(total_scarring_loss > 0.0);
    assert_abs_diff_eq!(max_energy_increase, 0.0, epsilon = 1.0e-6);
}

#[test]
fn scarring_diagnostics_are_deterministic() {
    let config = scarring_test_config(
        SoilInteractionModel::ScarringContactV1,
        100_000.0,
        1.0,
        1600.0,
        Some(0.04),
    );

    assert_eq!(config.run().unwrap().samples, config.run().unwrap().samples);
}

#[test]
fn vertical_impact_event_reconstructs_contact_without_scarring() {
    let mut config = scarring_test_config(SoilInteractionModel::None, 0.0, 0.0, 0.0, None);
    config.initial_velocity_mps = [0.0, 0.0, -1.0];
    config.terrain = TerrainConfig::Plane {
        z0_m: 0.0,
        slope_x: 0.0,
        slope_y: 0.0,
    };
    config.max_time_s = 0.7;
    config.dt_s = 0.005;
    config.normal_restitution = 0.5;
    let result = config.run().unwrap();

    assert_eq!(result.impact_events.len(), 1);
    let event = &result.impact_events[0];
    assert_eq!(event.impact_index, 1);
    assert!(event.incoming_vz_mps < 0.0);
    assert_abs_diff_eq!(event.impact_angle_deg, 0.0, epsilon = 1.0e-12);
    assert_abs_diff_eq!(event.incoming_tangent_speed_mps, 0.0, epsilon = 1.0e-12);
    assert_abs_diff_eq!(
        event.post_contact_normal_speed_mps,
        config.normal_restitution * event.incoming_normal_speed_mps,
        epsilon = 1.0e-12
    );
    assert_abs_diff_eq!(event.scarring_capped_energy_loss_j, 0.0, epsilon = 1.0e-12);
    assert_eq!(event.scarring_depth_source, ScarringDepthSource::None);
}

#[test]
fn oblique_scarring_impact_event_records_contact_and_soil_loss() {
    let mut config = scarring_test_config(
        SoilInteractionModel::ScarringContactV1,
        100_000.0,
        1.2,
        1600.0,
        Some(0.05),
    );
    config.max_time_s = 0.9;
    config.dt_s = 0.005;
    let result = config.run().unwrap();

    assert_eq!(result.impact_events.len(), 1);
    let event = &result.impact_events[0];
    assert!(event.incoming_tangent_speed_mps > 0.0);
    assert!(event.scarring_depth_m > 0.0);
    assert!(event.scarring_area_m2 > 0.0);
    assert!(event.scarring_drag_force_n > 0.0);
    assert!(event.scarring_uncapped_energy_loss_j >= event.scarring_capped_energy_loss_j);
    assert!(event.scarring_capped_energy_loss_j > 0.0);
    assert_eq!(event.scarring_depth_source, ScarringDepthSource::Explicit);
    assert!(event.post_scarring_translational_j <= event.post_contact_translational_j);
}

#[test]
fn impact_event_energy_accounting_matches_scarring_diagnostics() {
    let mut config = scarring_test_config(
        SoilInteractionModel::ScarringContactV1,
        100_000.0,
        1.0,
        1600.0,
        Some(0.04),
    );
    config.max_time_s = 1.2;
    config.dt_s = 0.005;
    let result = config.run().unwrap();

    let cumulative: f64 = result
        .impact_events
        .iter()
        .map(|event| event.scarring_capped_energy_loss_j)
        .sum();
    for event in &result.impact_events {
        assert_abs_diff_eq!(
            event.post_contact_translational_j - event.post_scarring_translational_j,
            event.scarring_capped_energy_loss_j,
            epsilon = 1.0e-9
        );
        assert!(event.post_scarring_translational_j <= event.post_contact_translational_j);
    }
    assert_abs_diff_eq!(
        result
            .impact_events
            .last()
            .unwrap()
            .cumulative_scarring_energy_loss_j,
        cumulative,
        epsilon = 1.0e-12
    );
}

#[test]
fn vertical_rotational_impact_leaves_spin_unchanged() {
    let block = SphereBlock::new(0.5, 10.0);
    let terrain = Plane::horizontal(0.0);
    let mut state = BodyState::new(Vec3::new(0.0, 0.0, 0.4), Vec3::new(0.0, 0.0, -4.0));

    let response = resolve_rotational_sphere_contact(&mut state, &terrain, block, 0.5, 1.0, 1.0);

    assert!(response.impacted);
    assert_abs_diff_eq!(state.velocity_mps.z, 2.0, epsilon = 1.0e-12);
    assert_abs_diff_eq!(state.angular_velocity_radps.norm(), 0.0, epsilon = 1.0e-12);
}

fn roughness_test_config(
    roughness_model: RoughnessModel,
    roughness_std_normal: f64,
    roughness_std_tangent: f64,
    roughness_std_angle: f64,
    random_seed: Option<u64>,
) -> SimulationConfig {
    SimulationConfig {
        block: SphereBlock::new(0.5, 50.0),
        initial_position_m: [0.0, 0.0, 4.0],
        initial_velocity_mps: [3.0, 0.2, -0.5],
        initial_angular_velocity_radps: [0.0, 0.0, 0.0],
        terrain: TerrainConfig::Plane {
            z0_m: 0.0,
            slope_x: -0.15,
            slope_y: 0.0,
        },
        dt_s: 0.01,
        max_time_s: 5.0,
        gravity_mps2: 9.81,
        normal_restitution: 0.2,
        tangential_restitution: 0.8,
        friction_coefficient: 0.4,
        rolling_resistance_coefficient: 0.0,
        contact_model: ContactModel::TranslationalV0,
        soil_interaction_model: SoilInteractionModel::None,
        soil_strength_pa: 0.0,
        scarring_drag_coefficient: 0.0,
        scarring_layer_density_kgpm3: 0.0,
        scarring_max_depth_m: None,
        roughness_model,
        roughness_std_normal,
        roughness_std_tangent,
        roughness_std_angle,
        stop_speed_mps: 0.05,
        random_seed,
        release_perturbation: ReleasePerturbation::default(),
    }
}

fn scarring_test_config(
    soil_interaction_model: SoilInteractionModel,
    soil_strength_pa: f64,
    scarring_drag_coefficient: f64,
    scarring_layer_density_kgpm3: f64,
    scarring_max_depth_m: Option<f64>,
) -> SimulationConfig {
    let mut config = roughness_test_config(RoughnessModel::None, 0.0, 0.0, 0.0, Some(123));
    config.initial_position_m = [0.0, 0.0, 3.0];
    config.initial_velocity_mps = [1.0, 0.0, -1.0];
    config.max_time_s = 2.0;
    config.normal_restitution = 0.35;
    config.tangential_restitution = 0.85;
    config.soil_interaction_model = soil_interaction_model;
    config.soil_strength_pa = soil_strength_pa;
    config.scarring_drag_coefficient = scarring_drag_coefficient;
    config.scarring_layer_density_kgpm3 = scarring_layer_density_kgpm3;
    config.scarring_max_depth_m = scarring_max_depth_m;
    config
}

#[test]
fn frictionless_oblique_rotational_impact_does_not_generate_spin() {
    let block = SphereBlock::new(0.5, 10.0);
    let terrain = Plane::horizontal(0.0);
    let mut state = BodyState::new(Vec3::new(0.0, 0.0, 0.4), Vec3::new(3.0, 0.0, -4.0));

    resolve_rotational_sphere_contact(&mut state, &terrain, block, 0.5, 0.0, 0.0);

    assert_abs_diff_eq!(state.velocity_mps.x, 3.0, epsilon = 1.0e-12);
    assert_abs_diff_eq!(state.angular_velocity_radps.norm(), 0.0, epsilon = 1.0e-12);
}

#[test]
fn oblique_rotational_impact_generates_spin_with_friction() {
    let block = SphereBlock::new(0.5, 10.0);
    let terrain = Plane::horizontal(0.0);
    let mut state = BodyState::new(Vec3::new(0.0, 0.0, 0.4), Vec3::new(3.0, 0.0, -4.0));

    resolve_rotational_sphere_contact(&mut state, &terrain, block, 0.5, 0.0, 10.0);

    assert!(state.velocity_mps.x < 3.0);
    assert!(state.angular_velocity_radps.y > 0.0);
}

#[test]
fn dissipative_rotational_impact_does_not_increase_total_energy() {
    let block = SphereBlock::new(0.5, 10.0);
    let terrain = Plane::horizontal(0.0);
    let mut state = BodyState::new(Vec3::new(0.0, 0.0, 0.49), Vec3::new(3.0, 0.0, -4.0));
    let before = EnergyDiagnostics::from_state(&state, &block, 9.81).total_j;

    resolve_rotational_sphere_contact(&mut state, &terrain, block, 0.5, 0.0, 10.0);

    let after = EnergyDiagnostics::from_state(&state, &block, 9.81).total_j;
    assert!(after <= before);
}

#[test]
fn rotational_tangential_impulse_respects_coulomb_cap() {
    let block = SphereBlock::new(0.5, 10.0);
    let terrain = Plane::horizontal(0.0);
    let mut state = BodyState::new(Vec3::new(0.0, 0.0, 0.4), Vec3::new(10.0, 0.0, -2.0));

    resolve_rotational_sphere_contact(&mut state, &terrain, block, 0.0, 0.0, 0.25);

    assert_abs_diff_eq!(state.velocity_mps.x, 9.5, epsilon = 1.0e-12);
    assert_abs_diff_eq!(state.angular_velocity_radps.y, 2.5, epsilon = 1.0e-12);
}

#[test]
fn rolling_sphere_incline_acceleration_matches_solid_sphere_solution() {
    let slope_x = -0.2;
    let radius = 0.5;
    let terrain = Plane {
        z0_m: 0.0,
        slope_x,
        slope_y: 0.0,
    };
    let normal = terrain.normal(0.0, 0.0);
    let initial = BodyState::new(Vec3::new(0.0, 0.0, radius / normal.z), Vec3::zeros());
    let samples = simulate_fixed_step(
        initial,
        SphereBlock::new(radius, 10.0),
        &terrain,
        IntegratorSettings {
            dt_s: 0.001,
            max_time_s: 0.1,
            gravity_mps2: 9.81,
            normal_restitution: 0.0,
            tangential_restitution: 1.0,
            friction_coefficient: 1.0,
            rolling_resistance_coefficient: 0.0,
            stop_speed_mps: 0.0,
            contact_model: ContactModel::SphereRotationalV1,
            scarring: ScarringSettings::default(),
            roughness: ContactRoughness::default(),
            roughness_seed: None,
        },
    );

    let last = samples.last().unwrap();
    let expected_speed = (5.0 / 7.0) * 9.81 * normal.x * 0.1;
    assert_eq!(last.contact_state, ContactState::Rolling);
    assert_abs_diff_eq!(last.speed_mps, expected_speed, epsilon = 0.02);
    assert_abs_diff_eq!(last.rolling_residual_mps, 0.0, epsilon = 1.0e-9);
}

#[test]
fn rolling_resistance_stops_horizontal_motion() {
    let block = SphereBlock::new(0.5, 10.0);
    let terrain = Plane::horizontal(0.0);
    let mut initial = BodyState::new(Vec3::new(0.0, 0.0, 0.5), Vec3::new(1.0, 0.0, 0.0));
    initial.angular_velocity_radps = Vec3::new(0.0, 2.0, 0.0);
    let samples = simulate_fixed_step(
        initial,
        block,
        &terrain,
        IntegratorSettings {
            dt_s: 0.001,
            max_time_s: 2.0,
            gravity_mps2: 9.81,
            normal_restitution: 0.0,
            tangential_restitution: 1.0,
            friction_coefficient: 1.0,
            rolling_resistance_coefficient: 0.2,
            stop_speed_mps: 0.02,
            contact_model: ContactModel::SphereRotationalV1,
            scarring: ScarringSettings::default(),
            roughness: ContactRoughness::default(),
            roughness_seed: None,
        },
    );

    let first = samples.first().unwrap();
    let last = samples.last().unwrap();
    let runout = last.x_m - first.x_m;
    assert_eq!(last.contact_state, ContactState::Stopped);
    assert_abs_diff_eq!(runout, 1.0 / (2.0 * 0.2 * 9.81), epsilon = 0.03);
}

#[test]
fn insufficient_static_friction_slides_instead_of_rolling() {
    let slope_x = -0.5;
    let radius = 0.5;
    let terrain = Plane {
        z0_m: 0.0,
        slope_x,
        slope_y: 0.0,
    };
    let normal = terrain.normal(0.0, 0.0);
    let initial = BodyState::new(Vec3::new(0.0, 0.0, radius / normal.z), Vec3::zeros());
    let samples = simulate_fixed_step(
        initial,
        SphereBlock::new(radius, 10.0),
        &terrain,
        IntegratorSettings {
            dt_s: 0.01,
            max_time_s: 0.1,
            gravity_mps2: 9.81,
            normal_restitution: 0.0,
            tangential_restitution: 1.0,
            friction_coefficient: 0.01,
            rolling_resistance_coefficient: 0.0,
            stop_speed_mps: 0.0,
            contact_model: ContactModel::SphereRotationalV1,
            scarring: ScarringSettings::default(),
            roughness: ContactRoughness::default(),
            roughness_seed: None,
        },
    );

    let last = samples.last().unwrap();
    assert_eq!(last.contact_state, ContactState::Sliding);
    assert!(last.rolling_residual_mps > 0.0);
}

#[test]
fn energy_diagnostics_include_rotation_for_spheres() {
    let block = SphereBlock::new(2.0, 5.0);
    let mut state = BodyState::new(Vec3::new(0.0, 0.0, 1.0), Vec3::zeros());
    state.angular_velocity_radps = Vec3::new(0.0, 3.0, 0.0);
    let energy = EnergyDiagnostics::from_state(&state, &block, 9.81);
    assert_abs_diff_eq!(energy.rotational_j, 36.0, epsilon = 1.0e-12);
}
