use approx::{assert_abs_diff_eq, assert_relative_eq};
use rust_rockfall::{
    dynamics::{acceleration_from_gravity, apply_contact_friction, resolve_sphere_contact},
    geometry::SphereBlock,
    integrator::{simulate_fixed_step, IntegratorSettings},
    simulation::{SimulationConfig, TerrainConfig},
    state::{BodyState, ContactState, EnergyDiagnostics},
    stochastic::{sample_release, ReleasePerturbation},
    terrain::{Plane, Terrain},
    Vec3,
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
            stop_speed_mps: 0.0,
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
            stop_speed_mps: 0.05,
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
fn energy_diagnostics_include_rotation_for_spheres() {
    let block = SphereBlock::new(2.0, 5.0);
    let mut state = BodyState::new(Vec3::new(0.0, 0.0, 1.0), Vec3::zeros());
    state.angular_velocity_radps = Vec3::new(0.0, 3.0, 0.0);
    let energy = EnergyDiagnostics::from_state(&state, &block, 9.81);
    assert_abs_diff_eq!(energy.rotational_j, 36.0, epsilon = 1.0e-12);
}
