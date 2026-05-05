//! Verification and validation helpers, case loading, and metric computation.

use crate::{
    geometry::SphereBlock,
    io,
    simulation::{SimulationConfig, SimulationError, TerrainConfig},
    state::{BodyState, ContactState, TrajectorySample},
    stochastic::ReleasePerturbation,
    terrain::TerrainError,
    Vec3,
};
use serde::{Deserialize, Serialize};
use std::{
    collections::BTreeMap,
    fs,
    path::{Path, PathBuf},
    process::Command,
    time::{SystemTime, UNIX_EPOCH},
};
use thiserror::Error;

pub fn free_flight_state(initial: BodyState, gravity_mps2: f64, time_s: f64) -> BodyState {
    let g = Vec3::new(0.0, 0.0, -gravity_mps2);
    BodyState {
        position_m: initial.position_m + initial.velocity_mps * time_s + 0.5 * g * time_s * time_s,
        velocity_mps: initial.velocity_mps + g * time_s,
        angular_velocity_radps: initial.angular_velocity_radps,
    }
}

pub fn translational_energy_j(state: &BodyState, block: &SphereBlock) -> f64 {
    0.5 * block.mass_kg * state.velocity_mps.norm_squared()
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct BenchmarkCase {
    pub case_id: String,
    #[serde(default)]
    pub title: String,
    #[serde(default)]
    pub level: Option<u8>,
    #[serde(default)]
    pub description: String,
    pub terrain: CaseTerrain,
    pub block: CaseBlock,
    #[serde(default)]
    pub release: CaseRelease,
    #[serde(default)]
    pub parameters: CaseParameters,
    #[serde(default)]
    pub simulation: CaseSimulation,
    #[serde(default)]
    pub random: CaseRandom,
    #[serde(default)]
    pub observations: Option<ObservationConfig>,
    #[serde(default)]
    pub expected: ExpectedConfig,
    #[serde(default)]
    pub metrics: Vec<String>,
    #[serde(default, alias = "output")]
    pub outputs: OutputConfig,
    #[serde(default)]
    pub references: ReferenceConfig,
}

#[derive(Debug, Clone, Default, Serialize, Deserialize, PartialEq)]
pub struct CaseTerrain {
    #[serde(rename = "type", alias = "kind")]
    pub terrain_type: String,
    #[serde(default)]
    pub parameters: BTreeMap<String, f64>,
    #[serde(default)]
    pub path: Option<PathBuf>,
}

#[derive(Debug, Clone, Default, Serialize, Deserialize, PartialEq)]
pub struct CaseBlock {
    #[serde(default, alias = "mass_kg")]
    pub mass: Option<f64>,
    #[serde(default, alias = "radius_m")]
    pub radius: Option<f64>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct CaseRelease {
    #[serde(default)]
    pub position: [f64; 3],
    #[serde(default)]
    pub velocity: [f64; 3],
    #[serde(default)]
    pub angular_velocity: [f64; 3],
    #[serde(default)]
    pub perturbation: CasePerturbation,
}

impl Default for CaseRelease {
    fn default() -> Self {
        Self {
            position: [0.0, 0.0, 0.0],
            velocity: [0.0, 0.0, 0.0],
            angular_velocity: [0.0, 0.0, 0.0],
            perturbation: CasePerturbation::default(),
        }
    }
}

#[derive(Debug, Clone, Copy, Default, Serialize, Deserialize, PartialEq)]
pub struct CasePerturbation {
    #[serde(default)]
    pub position_uniform_m: f64,
    #[serde(default)]
    pub velocity_uniform_mps: f64,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq)]
pub struct CaseParameters {
    #[serde(default = "default_gravity", alias = "gravity_mps2")]
    pub gravity: f64,
    #[serde(default = "default_normal_restitution")]
    pub normal_restitution: f64,
    #[serde(default = "default_tangential_restitution")]
    pub tangential_restitution: f64,
    #[serde(default = "default_friction", alias = "mu")]
    pub friction_coefficient: f64,
}

impl Default for CaseParameters {
    fn default() -> Self {
        Self {
            gravity: default_gravity(),
            normal_restitution: default_normal_restitution(),
            tangential_restitution: default_tangential_restitution(),
            friction_coefficient: default_friction(),
        }
    }
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq)]
pub struct CaseSimulation {
    #[serde(default = "default_dt", alias = "dt_s")]
    pub dt: f64,
    #[serde(default, alias = "max_time_s")]
    pub t_max: Option<f64>,
    #[serde(default)]
    pub max_steps: Option<usize>,
    #[serde(default = "default_stop_speed", alias = "stop_speed_mps")]
    pub stop_velocity: f64,
}

impl Default for CaseSimulation {
    fn default() -> Self {
        Self {
            dt: default_dt(),
            t_max: Some(1.0),
            max_steps: None,
            stop_velocity: default_stop_speed(),
        }
    }
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq)]
pub struct CaseRandom {
    #[serde(default)]
    pub seed: Option<u64>,
    #[serde(default = "default_ensemble_size")]
    pub ensemble_size: usize,
}

impl Default for CaseRandom {
    fn default() -> Self {
        Self {
            seed: None,
            ensemble_size: default_ensemble_size(),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ObservationConfig {
    #[serde(default)]
    pub deposition_points_csv: Option<PathBuf>,
    #[serde(default)]
    pub trajectory_csv: Option<PathBuf>,
}

#[derive(Debug, Clone, Default, Serialize, Deserialize, PartialEq)]
pub struct ExpectedConfig {
    #[serde(default)]
    pub metrics: Vec<String>,
    #[serde(default)]
    pub values: BTreeMap<String, f64>,
    #[serde(default)]
    pub minimums: BTreeMap<String, f64>,
    #[serde(default)]
    pub maximums: BTreeMap<String, f64>,
    #[serde(default)]
    pub final_position_m: Option<[f64; 3]>,
    #[serde(default)]
    pub final_velocity_mps: Option<[f64; 3]>,
    #[serde(default)]
    pub contact_state: Option<ContactState>,
    #[serde(default)]
    pub rebound_height_m: Option<f64>,
    #[serde(default)]
    pub stopping_distance_m: Option<f64>,
    #[serde(default)]
    pub impact_time_s: Option<f64>,
    #[serde(default)]
    pub min_runout_m: Option<f64>,
    #[serde(default)]
    pub max_runout_m: Option<f64>,
    #[serde(default)]
    pub min_impact_count: Option<usize>,
    #[serde(default)]
    pub max_impact_count: Option<usize>,
    #[serde(default)]
    pub tolerances: BTreeMap<String, f64>,
}

#[derive(Debug, Clone, Default, Serialize, Deserialize, PartialEq)]
pub struct OutputConfig {
    #[serde(default, alias = "metrics_json")]
    pub diagnostics_json: Option<PathBuf>,
    #[serde(default)]
    pub trajectory_csv: Option<PathBuf>,
}

#[derive(Debug, Clone, Default, Serialize, Deserialize, PartialEq)]
pub struct ReferenceConfig {
    #[serde(default)]
    pub literature: Vec<String>,
    #[serde(default)]
    pub dataset: Option<String>,
    #[serde(default)]
    pub notes: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct DepositionPoint {
    pub trajectory_id: String,
    pub experiment_id: String,
    pub x_m: f64,
    pub y_m: f64,
    pub z_m: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct CaseReport {
    pub case_id: String,
    pub status: CaseStatus,
    pub timestamp_unix_s: u64,
    pub model_version: String,
    pub git_hash: Option<String>,
    pub metrics: BTreeMap<String, f64>,
    pub tolerances: BTreeMap<String, f64>,
    pub failures: Vec<String>,
    pub warnings: Vec<String>,
    pub parameters: SimulationConfig,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum CaseStatus {
    Passed,
    Failed,
    Skipped,
}

#[derive(Debug, Error)]
pub enum ValidationError {
    #[error("I/O error: {0}")]
    Io(#[from] std::io::Error),
    #[error("YAML error: {0}")]
    Yaml(#[from] serde_yaml::Error),
    #[error("CSV error: {0}")]
    Csv(#[from] csv::Error),
    #[error("JSON error: {0}")]
    Json(#[from] serde_json::Error),
    #[error("simulation error: {0}")]
    Simulation(#[from] SimulationError),
    #[error("terrain error: {0}")]
    Terrain(#[from] TerrainError),
    #[error("I/O helper error: {0}")]
    Output(#[from] io::IoError),
    #[error("case {0} has no trajectory samples")]
    EmptyTrajectory(String),
    #[error("case configuration error: {0}")]
    Case(String),
}

pub fn load_case(path: impl AsRef<Path>) -> Result<BenchmarkCase, ValidationError> {
    let text = fs::read_to_string(path)?;
    Ok(serde_yaml::from_str(&text)?)
}

pub fn run_case_file(path: impl AsRef<Path>) -> Result<CaseReport, ValidationError> {
    let case = load_case(path)?;
    run_case(&case)
}

pub fn run_case(case: &BenchmarkCase) -> Result<CaseReport, ValidationError> {
    let mut warnings = Vec::new();
    let observations = match load_observations(case, &mut warnings)? {
        ObservationLoad::Loaded(points) => points,
        ObservationLoad::MissingRequired(path) => {
            let report = skipped_report(
                case,
                format!(
                    "observation file is not available: {}; run scripts/download_datasets.py and scripts/preprocess_datasets.py for public data cases",
                    path.display()
                ),
            )?;
            if let Some(path) = &case.outputs.diagnostics_json {
                write_report(path, &report)?;
            }
            return Ok(report);
        }
    };

    let config = build_simulation_config(case)?;
    let result = config.run()?;
    if let Some(path) = &case.outputs.trajectory_csv {
        io::write_trajectory_csv(path, &result.samples)?;
    }

    let samples = &result.samples;
    let first = samples
        .first()
        .ok_or_else(|| ValidationError::EmptyTrajectory(case.case_id.clone()))?;
    let last = samples
        .last()
        .ok_or_else(|| ValidationError::EmptyTrajectory(case.case_id.clone()))?;

    let terrain = config.terrain.build()?;
    let mut metrics = compute_metrics(
        samples,
        first,
        last,
        terrain.as_ref(),
        &config.block,
        &observations,
        &case.expected,
    );
    compute_ensemble_metrics(case, &mut metrics, &mut warnings)?;

    let requested_metrics = requested_metrics(case);
    if !requested_metrics.is_empty() {
        metrics.retain(|name, _| requested_metrics.iter().any(|requested| requested == name));
    }

    let failures = evaluate_failures(last, &metrics, &case.expected);
    let status = if failures.is_empty() {
        CaseStatus::Passed
    } else {
        CaseStatus::Failed
    };

    let report = CaseReport {
        case_id: case.case_id.clone(),
        status,
        timestamp_unix_s: now_unix_s(),
        model_version: env!("CARGO_PKG_VERSION").to_string(),
        git_hash: git_hash(),
        metrics,
        tolerances: case.expected.tolerances.clone(),
        failures,
        warnings,
        parameters: config,
    };

    if let Some(path) = &case.outputs.diagnostics_json {
        write_report(path, &report)?;
    }

    Ok(report)
}

pub fn write_report(path: impl AsRef<Path>, report: &CaseReport) -> Result<(), ValidationError> {
    if let Some(parent) = path.as_ref().parent() {
        fs::create_dir_all(parent)?;
    }
    fs::write(path, serde_json::to_string_pretty(report)?)?;
    Ok(())
}

fn build_simulation_config(case: &BenchmarkCase) -> Result<SimulationConfig, ValidationError> {
    let mass_kg = case
        .block
        .mass
        .ok_or_else(|| ValidationError::Case("block.mass is required".to_string()))?;
    let radius_m = case
        .block
        .radius
        .ok_or_else(|| ValidationError::Case("block.radius is required".to_string()))?;
    let terrain = build_terrain_config(&case.terrain)?;
    let max_time_s = match (case.simulation.t_max, case.simulation.max_steps) {
        (Some(t_max), Some(max_steps)) => t_max.min(max_steps as f64 * case.simulation.dt),
        (Some(t_max), None) => t_max,
        (None, Some(max_steps)) => max_steps as f64 * case.simulation.dt,
        (None, None) => {
            return Err(ValidationError::Case(
                "simulation.t_max or max_steps is required".to_string(),
            ))
        }
    };

    Ok(SimulationConfig {
        block: SphereBlock::new(radius_m, mass_kg),
        initial_position_m: case.release.position,
        initial_velocity_mps: case.release.velocity,
        initial_angular_velocity_radps: case.release.angular_velocity,
        terrain,
        dt_s: case.simulation.dt,
        max_time_s,
        gravity_mps2: case.parameters.gravity,
        normal_restitution: case.parameters.normal_restitution,
        tangential_restitution: case.parameters.tangential_restitution,
        friction_coefficient: case.parameters.friction_coefficient,
        stop_speed_mps: case.simulation.stop_velocity,
        random_seed: case.random.seed,
        release_perturbation: ReleasePerturbation {
            position_uniform_m: case.release.perturbation.position_uniform_m,
            velocity_uniform_mps: case.release.perturbation.velocity_uniform_mps,
        },
    })
}

fn build_terrain_config(terrain: &CaseTerrain) -> Result<TerrainConfig, ValidationError> {
    let p = &terrain.parameters;
    match terrain.terrain_type.as_str() {
        "plane" | "inclined_plane" => Ok(TerrainConfig::Plane {
            z0_m: param(p, "z0_m", 0.0),
            slope_x: param(p, "slope_x", 0.0),
            slope_y: param(p, "slope_y", 0.0),
        }),
        "paraboloid" => Ok(TerrainConfig::Paraboloid {
            z0_m: param(p, "z0_m", 0.0),
            ax: param(p, "ax", 0.0),
            ay: param(p, "ay", 0.0),
        }),
        "step" | "step_terrain" => Ok(TerrainConfig::Step {
            step_x_m: required_param(p, "step_x_m")?,
            high_z_m: required_param(p, "high_z_m")?,
            low_z_m: required_param(p, "low_z_m")?,
        }),
        "v_shaped_valley" => Ok(TerrainConfig::VShapedValley {
            z0_m: param(p, "z0_m", 0.0),
            slope_x: param(p, "slope_x", 0.0),
            side_slope_abs_y: required_param(p, "side_slope_abs_y")?,
        }),
        "terraced_slope" => Ok(TerrainConfig::TerracedSlope {
            z0_m: param(p, "z0_m", 0.0),
            slope_x: param(p, "slope_x", 0.0),
            terrace_width_m: required_param(p, "terrace_width_m")?,
            terrace_height_m: required_param(p, "terrace_height_m")?,
        }),
        "sinusoidal_rough_slope" => Ok(TerrainConfig::SinusoidalRoughSlope {
            z0_m: param(p, "z0_m", 0.0),
            slope_x: param(p, "slope_x", 0.0),
            amplitude_m: required_param(p, "amplitude_m")?,
            wavelength_m: required_param(p, "wavelength_m")?,
        }),
        "gaussian_bump" => Ok(TerrainConfig::GaussianBump {
            z0_m: param(p, "z0_m", 0.0),
            slope_x: param(p, "slope_x", 0.0),
            center_x_m: param(p, "center_x_m", 0.0),
            center_y_m: param(p, "center_y_m", 0.0),
            height_m: required_param(p, "height_m")?,
            sigma_m: required_param(p, "sigma_m")?,
        }),
        "channelized_gully" => Ok(TerrainConfig::ChannelizedGully {
            z0_m: param(p, "z0_m", 0.0),
            slope_x: param(p, "slope_x", 0.0),
            depth_m: required_param(p, "depth_m")?,
            width_m: required_param(p, "width_m")?,
        }),
        "esri_ascii_grid" | "ascii_dem" => Ok(TerrainConfig::EsriAsciiGrid {
            path: terrain
                .path
                .as_ref()
                .ok_or_else(|| {
                    ValidationError::Case(
                        "terrain.path is required for ESRI ASCII grid".to_string(),
                    )
                })?
                .to_string_lossy()
                .to_string(),
        }),
        other => Err(ValidationError::Case(format!(
            "unsupported terrain type '{other}'"
        ))),
    }
}

fn compute_metrics(
    samples: &[TrajectorySample],
    first: &TrajectorySample,
    last: &TrajectorySample,
    terrain: &dyn crate::terrain::Terrain,
    block: &SphereBlock,
    observations: &[DepositionPoint],
    expected: &ExpectedConfig,
) -> BTreeMap<String, f64> {
    let mut metrics = BTreeMap::new();
    let dx = last.x_m - first.x_m;
    let dy = last.y_m - first.y_m;
    let runout = (dx * dx + dy * dy).sqrt();
    let impact_count = impact_count(samples);
    let max_speed = samples
        .iter()
        .map(|sample| sample.speed_mps)
        .fold(0.0_f64, f64::max);
    let max_kinetic = samples
        .iter()
        .map(|sample| sample.kinetic_j)
        .fold(0.0_f64, f64::max);
    let max_bounce_height = max_bounce_height(samples, terrain, block.radius_m);
    let rebound_height = rebound_height_after_first_impact(samples, terrain, block.radius_m);
    let energy_conservation_error = samples
        .iter()
        .map(|sample| (sample.total_energy_j - first.total_energy_j).abs())
        .fold(0.0_f64, f64::max);

    metrics.insert("runout_m".to_string(), runout);
    metrics.insert("final_speed_mps".to_string(), last.speed_mps);
    metrics.insert("impact_count".to_string(), impact_count as f64);
    metrics.insert("max_speed_mps".to_string(), max_speed);
    metrics.insert("max_kinetic_energy_j".to_string(), max_kinetic);
    metrics.insert("max_bounce_height_m".to_string(), max_bounce_height);
    metrics.insert("rebound_height_m".to_string(), rebound_height);
    metrics.insert("total_energy_initial_j".to_string(), first.total_energy_j);
    metrics.insert("total_energy_final_j".to_string(), last.total_energy_j);
    metrics.insert(
        "energy_error_j".to_string(),
        (last.total_energy_j - first.total_energy_j).abs(),
    );
    metrics.insert(
        "energy_conservation_error_j".to_string(),
        energy_conservation_error,
    );
    metrics.insert(
        "energy_monotonicity_violation_j".to_string(),
        energy_monotonicity_violation(samples),
    );

    if let Some(expected_position) = expected.final_position_m {
        let error = distance3([last.x_m, last.y_m, last.z_m], expected_position);
        metrics.insert("position_error_m".to_string(), error);
    }

    if let Some(expected_velocity) = expected.final_velocity_mps {
        let error = distance3([last.vx_mps, last.vy_mps, last.vz_mps], expected_velocity);
        metrics.insert("velocity_error_mps".to_string(), error);
    }

    if let Some(expected_rebound_height) = expected.rebound_height_m {
        metrics.insert(
            "rebound_height_error_m".to_string(),
            (rebound_height - expected_rebound_height).abs(),
        );
    }

    if let Some(expected_stopping_distance) = expected.stopping_distance_m {
        metrics.insert(
            "stopping_distance_error_m".to_string(),
            (runout - expected_stopping_distance).abs(),
        );
    }

    if let Some(expected_impact_time) = expected.impact_time_s {
        if let Some(actual_impact_time) = first_impact_time(samples) {
            metrics.insert(
                "impact_time_error_s".to_string(),
                (actual_impact_time - expected_impact_time).abs(),
            );
        }
    }

    for (name, expected_value) in &expected.values {
        if let Some(value) = metrics.get(name).copied() {
            metrics.insert(format!("{name}_error"), (value - expected_value).abs());
        }
    }

    if let Some(observed) = observations.first() {
        let odx = last.x_m - observed.x_m;
        let ody = last.y_m - observed.y_m;
        let odz = last.z_m - observed.z_m;
        let observed_runout =
            ((observed.x_m - first.x_m).powi(2) + (observed.y_m - first.y_m).powi(2)).sqrt();
        metrics.insert(
            "deposition_point_error_m".to_string(),
            (odx * odx + ody * ody + odz * odz).sqrt(),
        );
        metrics.insert(
            "runout_distance_error_m".to_string(),
            (runout - observed_runout).abs(),
        );
        metrics.insert("lateral_deviation_m".to_string(), ody.abs());
    }

    metrics
}

fn compute_ensemble_metrics(
    case: &BenchmarkCase,
    metrics: &mut BTreeMap<String, f64>,
    warnings: &mut Vec<String>,
) -> Result<(), ValidationError> {
    let ensemble_size = case.random.ensemble_size.max(1);
    if case.random.seed.is_some() {
        let config_a = build_simulation_config(case)?;
        let config_b = build_simulation_config(case)?;
        let a = config_a.run()?;
        let b = config_b.run()?;
        metrics.insert(
            "seed_repeat_max_position_delta_m".to_string(),
            max_position_delta(&a.samples, &b.samples),
        );
    }

    if ensemble_size <= 1 {
        return Ok(());
    }

    if case.release.perturbation.position_uniform_m == 0.0
        && case.release.perturbation.velocity_uniform_mps == 0.0
    {
        warnings.push(
            "ensemble_size > 1 but release perturbation is zero; runout spread may be zero"
                .to_string(),
        );
    }

    let base_seed = case.random.seed.unwrap_or(0);
    let mut runouts = Vec::with_capacity(ensemble_size);
    let mut max_kinetic = Vec::with_capacity(ensemble_size);
    for offset in 0..ensemble_size {
        let mut case_i = case.clone();
        case_i.random.seed = Some(base_seed + offset as u64);
        case_i.random.ensemble_size = 1;
        let config = build_simulation_config(&case_i)?;
        let result = config.run()?;
        if let (Some(first), Some(last)) = (result.samples.first(), result.samples.last()) {
            runouts.push(((last.x_m - first.x_m).powi(2) + (last.y_m - first.y_m).powi(2)).sqrt());
            max_kinetic.push(
                result
                    .samples
                    .iter()
                    .map(|sample| sample.kinetic_j)
                    .fold(0.0_f64, f64::max),
            );
        }
    }

    runouts.sort_by(f64::total_cmp);
    max_kinetic.sort_by(f64::total_cmp);
    metrics.insert("ensemble_mean_runout_m".to_string(), mean(&runouts));
    metrics.insert(
        "ensemble_median_runout_m".to_string(),
        percentile(&runouts, 0.50),
    );
    metrics.insert(
        "ensemble_p05_runout_m".to_string(),
        percentile(&runouts, 0.05),
    );
    metrics.insert(
        "ensemble_p95_runout_m".to_string(),
        percentile(&runouts, 0.95),
    );
    metrics.insert(
        "ensemble_runout_spread_m".to_string(),
        percentile(&runouts, 0.95) - percentile(&runouts, 0.05),
    );
    metrics.insert(
        "ensemble_p95_max_kinetic_energy_j".to_string(),
        percentile(&max_kinetic, 0.95),
    );
    Ok(())
}

fn evaluate_failures(
    last: &TrajectorySample,
    metrics: &BTreeMap<String, f64>,
    expected: &ExpectedConfig,
) -> Vec<String> {
    let mut failures = Vec::new();
    for (metric, tolerance) in &expected.tolerances {
        if let Some(value) = metrics.get(metric) {
            if value > tolerance {
                failures.push(format!("{metric}={value} exceeds tolerance {tolerance}"));
            }
        }
    }

    for (metric, target) in &expected.values {
        if let Some(value) = metrics.get(metric) {
            let tolerance = expected.tolerances.get(metric).copied().unwrap_or(0.0);
            if (value - target).abs() > tolerance {
                failures.push(format!(
                    "{metric}={value} differs from target {target} by more than tolerance {tolerance}"
                ));
            }
        }
    }

    for (metric, minimum) in &expected.minimums {
        if metrics.get(metric).copied().unwrap_or_default() < *minimum {
            failures.push(format!("{metric} below minimum {minimum}"));
        }
    }

    for (metric, maximum) in &expected.maximums {
        if metrics.get(metric).copied().unwrap_or(f64::INFINITY) > *maximum {
            failures.push(format!("{metric} above maximum {maximum}"));
        }
    }

    if let Some(contact_state) = expected.contact_state {
        if last.contact_state != contact_state {
            failures.push(format!(
                "final contact_state={:?}, expected {:?}",
                last.contact_state, contact_state
            ));
        }
    }
    if let Some(min_runout) = expected.min_runout_m {
        if metrics.get("runout_m").copied().unwrap_or_default() < min_runout {
            failures.push(format!("runout_m below minimum {min_runout}"));
        }
    }
    if let Some(max_runout) = expected.max_runout_m {
        if metrics.get("runout_m").copied().unwrap_or_default() > max_runout {
            failures.push(format!("runout_m above maximum {max_runout}"));
        }
    }
    if let Some(min_impacts) = expected.min_impact_count {
        if metrics.get("impact_count").copied().unwrap_or_default() < min_impacts as f64 {
            failures.push(format!("impact_count below minimum {min_impacts}"));
        }
    }
    if let Some(max_impacts) = expected.max_impact_count {
        if metrics.get("impact_count").copied().unwrap_or_default() > max_impacts as f64 {
            failures.push(format!("impact_count above maximum {max_impacts}"));
        }
    }

    failures
}

enum ObservationLoad {
    Loaded(Vec<DepositionPoint>),
    MissingRequired(PathBuf),
}

fn load_observations(
    case: &BenchmarkCase,
    warnings: &mut Vec<String>,
) -> Result<ObservationLoad, ValidationError> {
    let Some(observations) = &case.observations else {
        return Ok(ObservationLoad::Loaded(Vec::new()));
    };
    let Some(path) = &observations.deposition_points_csv else {
        return Ok(ObservationLoad::Loaded(Vec::new()));
    };
    if !path.exists() {
        return Ok(ObservationLoad::MissingRequired(path.clone()));
    }

    let mut reader = csv::Reader::from_path(path)?;
    let mut points = Vec::new();
    for record in reader.deserialize() {
        points.push(record?);
    }
    if points.len() > 1 {
        warnings.push(format!(
            "case {} has {} observed deposition points; current metrics use the first point",
            case.case_id,
            points.len()
        ));
    }
    Ok(ObservationLoad::Loaded(points))
}

fn skipped_report(case: &BenchmarkCase, warning: String) -> Result<CaseReport, ValidationError> {
    Ok(CaseReport {
        case_id: case.case_id.clone(),
        status: CaseStatus::Skipped,
        timestamp_unix_s: now_unix_s(),
        model_version: env!("CARGO_PKG_VERSION").to_string(),
        git_hash: git_hash(),
        metrics: BTreeMap::new(),
        tolerances: case.expected.tolerances.clone(),
        failures: Vec::new(),
        warnings: vec![warning],
        parameters: build_simulation_config(case)?,
    })
}

fn requested_metrics(case: &BenchmarkCase) -> Vec<String> {
    if !case.expected.metrics.is_empty() {
        case.expected.metrics.clone()
    } else {
        case.metrics.clone()
    }
}

fn impact_count(samples: &[TrajectorySample]) -> usize {
    samples
        .windows(2)
        .filter(|pair| {
            pair[1].contact_state == ContactState::Impact
                && pair[0].contact_state == ContactState::Airborne
        })
        .count()
}

fn first_impact_time(samples: &[TrajectorySample]) -> Option<f64> {
    samples
        .iter()
        .find(|sample| sample.contact_state == ContactState::Impact)
        .map(|sample| sample.time_s)
}

fn clearance(
    sample: &TrajectorySample,
    terrain: &dyn crate::terrain::Terrain,
    radius_m: f64,
) -> f64 {
    (sample.z_m - terrain.height(sample.x_m, sample.y_m) - radius_m).max(0.0)
}

fn max_bounce_height(
    samples: &[TrajectorySample],
    terrain: &dyn crate::terrain::Terrain,
    radius_m: f64,
) -> f64 {
    samples
        .iter()
        .map(|sample| clearance(sample, terrain, radius_m))
        .fold(0.0_f64, f64::max)
}

fn rebound_height_after_first_impact(
    samples: &[TrajectorySample],
    terrain: &dyn crate::terrain::Terrain,
    radius_m: f64,
) -> f64 {
    let first_impact = samples
        .iter()
        .position(|sample| sample.contact_state == ContactState::Impact);
    if let Some(index) = first_impact {
        samples[index..]
            .iter()
            .map(|sample| clearance(sample, terrain, radius_m))
            .fold(0.0_f64, f64::max)
    } else {
        0.0
    }
}

fn energy_monotonicity_violation(samples: &[TrajectorySample]) -> f64 {
    samples
        .windows(2)
        .map(|pair| (pair[1].total_energy_j - pair[0].total_energy_j).max(0.0))
        .fold(0.0_f64, f64::max)
}

fn max_position_delta(a: &[TrajectorySample], b: &[TrajectorySample]) -> f64 {
    a.iter()
        .zip(b.iter())
        .map(|(left, right)| {
            distance3(
                [left.x_m, left.y_m, left.z_m],
                [right.x_m, right.y_m, right.z_m],
            )
        })
        .fold(0.0_f64, f64::max)
}

fn mean(values: &[f64]) -> f64 {
    if values.is_empty() {
        0.0
    } else {
        values.iter().sum::<f64>() / values.len() as f64
    }
}

fn percentile(values: &[f64], p: f64) -> f64 {
    if values.is_empty() {
        return 0.0;
    }
    let rank = p.clamp(0.0, 1.0) * (values.len().saturating_sub(1)) as f64;
    let lower = rank.floor() as usize;
    let upper = rank.ceil() as usize;
    if lower == upper {
        values[lower]
    } else {
        let weight = rank - lower as f64;
        values[lower] * (1.0 - weight) + values[upper] * weight
    }
}

fn distance3(a: [f64; 3], b: [f64; 3]) -> f64 {
    ((a[0] - b[0]).powi(2) + (a[1] - b[1]).powi(2) + (a[2] - b[2]).powi(2)).sqrt()
}

fn param(params: &BTreeMap<String, f64>, name: &str, default: f64) -> f64 {
    params.get(name).copied().unwrap_or(default)
}

fn required_param(params: &BTreeMap<String, f64>, name: &str) -> Result<f64, ValidationError> {
    params
        .get(name)
        .copied()
        .ok_or_else(|| ValidationError::Case(format!("terrain.parameters.{name} is required")))
}

fn default_gravity() -> f64 {
    9.81
}

fn default_normal_restitution() -> f64 {
    0.25
}

fn default_tangential_restitution() -> f64 {
    0.85
}

fn default_friction() -> f64 {
    0.45
}

fn default_dt() -> f64 {
    0.01
}

fn default_stop_speed() -> f64 {
    0.05
}

fn default_ensemble_size() -> usize {
    1
}

fn now_unix_s() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|duration| duration.as_secs())
        .unwrap_or_default()
}

fn git_hash() -> Option<String> {
    let output = Command::new("git")
        .args(["rev-parse", "--short", "HEAD"])
        .output()
        .ok()?;
    if !output.status.success() {
        return None;
    }
    let hash = String::from_utf8(output.stdout).ok()?.trim().to_string();
    if hash.is_empty() {
        None
    } else {
        Some(hash)
    }
}
