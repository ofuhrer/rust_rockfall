use rust_rockfall::stochastic::{derive_trajectory_seed, ReleasePerturbation, RoughnessModel};
use rust_rockfall::{
    simulate_ensemble, simulate_one_trajectory, ContactModel, SimulationConfig,
    SoilInteractionModel, SphereBlock, TerrainConfig, TrajectoryRequest,
};
use std::collections::BTreeMap;

#[test]
fn same_trajectory_seed_reproduces_identical_samples() {
    let config = ensemble_ready_config();
    let request = TrajectoryRequest::new("case", "trajectory_a", Some(12345));

    let first = simulate_one_trajectory(&config, request.clone()).unwrap();
    let second = simulate_one_trajectory(&config, request).unwrap();

    assert_eq!(first.samples, second.samples);
    assert_eq!(first.summary, second.summary);
}

#[test]
fn different_trajectory_seed_changes_perturbed_result() {
    let config = ensemble_ready_config();
    let first = simulate_one_trajectory(
        &config,
        TrajectoryRequest::new("case", "trajectory_a", Some(1)),
    )
    .unwrap();
    let second = simulate_one_trajectory(
        &config,
        TrajectoryRequest::new("case", "trajectory_b", Some(2)),
    )
    .unwrap();

    assert_ne!(first.samples, second.samples);
    assert_ne!(
        first.summary.final_position_m,
        second.summary.final_position_m
    );
}

#[test]
fn derived_seed_depends_on_case_and_trajectory_id() {
    let seed = 42;
    assert_eq!(
        derive_trajectory_seed(seed, "case_a", "trajectory_001"),
        derive_trajectory_seed(seed, "case_a", "trajectory_001")
    );
    assert_ne!(
        derive_trajectory_seed(seed, "case_a", "trajectory_001"),
        derive_trajectory_seed(seed, "case_a", "trajectory_002")
    );
    assert_ne!(
        derive_trajectory_seed(seed, "case_a", "trajectory_001"),
        derive_trajectory_seed(seed, "case_b", "trajectory_001")
    );
}

#[test]
fn ensemble_results_are_independent_of_requested_order() {
    let config = ensemble_ready_config();
    let forward = vec![
        "trajectory_a".to_string(),
        "trajectory_b".to_string(),
        "trajectory_c".to_string(),
    ];
    let reverse = forward.iter().rev().cloned().collect::<Vec<_>>();

    let forward_runs = simulate_ensemble(&config, "order_case", 99, &forward).unwrap();
    let reverse_runs = simulate_ensemble(&config, "order_case", 99, &reverse).unwrap();

    let forward_by_id = forward_runs
        .trajectories
        .into_iter()
        .map(|run| (run.request.trajectory_id.clone(), run))
        .collect::<BTreeMap<_, _>>();
    let reverse_by_id = reverse_runs
        .trajectories
        .into_iter()
        .map(|run| (run.request.trajectory_id.clone(), run))
        .collect::<BTreeMap<_, _>>();

    assert_eq!(
        forward_by_id.keys().collect::<Vec<_>>(),
        reverse_by_id.keys().collect::<Vec<_>>()
    );
    for (trajectory_id, forward_run) in forward_by_id {
        let reverse_run = reverse_by_id.get(&trajectory_id).unwrap();
        assert_eq!(forward_run.request.seed, reverse_run.request.seed);
        assert_eq!(forward_run.samples, reverse_run.samples);
        assert_eq!(forward_run.summary, reverse_run.summary);
    }
}

#[test]
fn configuration_and_run_fingerprints_are_stable() {
    let config = ensemble_ready_config();
    let request = TrajectoryRequest::from_global_seed(123, "fingerprint_case", "trajectory_000001");

    assert_eq!(
        config.config_fingerprint().unwrap(),
        config.config_fingerprint().unwrap()
    );
    assert_eq!(
        config.run_fingerprint(&request).unwrap(),
        config.run_fingerprint(&request).unwrap()
    );

    let different_request =
        TrajectoryRequest::from_global_seed(123, "fingerprint_case", "trajectory_000002");
    assert_ne!(
        config.run_fingerprint(&request).unwrap(),
        config.run_fingerprint(&different_request).unwrap()
    );
}

fn ensemble_ready_config() -> SimulationConfig {
    SimulationConfig {
        block: SphereBlock::new(0.5, 20.0),
        initial_position_m: [0.0, 0.0, 3.0],
        initial_velocity_mps: [1.0, 0.0, -0.5],
        initial_angular_velocity_radps: [0.0, 0.0, 0.0],
        terrain: TerrainConfig::Plane {
            z0_m: 0.0,
            slope_x: -0.2,
            slope_y: 0.0,
        },
        dt_s: 0.01,
        max_time_s: 4.0,
        gravity_mps2: 9.81,
        normal_restitution: 0.2,
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
        stop_speed_mps: 0.05,
        random_seed: None,
        release_perturbation: ReleasePerturbation {
            position_uniform_m: 0.2,
            velocity_uniform_mps: 0.1,
        },
    }
}
