//! Verification and validation helpers, case loading, and metric computation.

use crate::{
    dynamics::{ContactModel, SoilInteractionModel},
    geometry::SphereBlock,
    io,
    simulation::{
        simulate_ensemble, simulate_one_trajectory_with_terrain, SimulationConfig, SimulationError,
        TerrainConfig, TrajectoryRequest, TrajectoryRun,
    },
    state::{BodyState, ContactState, ImpactEvent, TrajectorySample},
    stochastic::{ReleasePerturbation, RoughnessModel},
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

pub const SIGNIFICANT_IMPACT_MIN_NORMAL_SPEED_MPS: f64 = 0.05;

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
    pub validation_scope: Option<ValidationScope>,
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
    #[serde(default)]
    pub rolling_resistance_coefficient: f64,
    #[serde(default)]
    pub contact_model: ContactModel,
    #[serde(default)]
    pub soil_interaction_model: SoilInteractionModel,
    #[serde(default)]
    pub soil_strength_pa: f64,
    #[serde(default)]
    pub scarring_drag_coefficient: f64,
    #[serde(default)]
    pub scarring_layer_density_kgpm3: f64,
    #[serde(default)]
    pub scarring_max_depth_m: Option<f64>,
    #[serde(default)]
    pub roughness_model: RoughnessModel,
    #[serde(default)]
    pub roughness_std_normal: f64,
    #[serde(default)]
    pub roughness_std_tangent: f64,
    #[serde(default)]
    pub roughness_std_angle: f64,
}

impl Default for CaseParameters {
    fn default() -> Self {
        Self {
            gravity: default_gravity(),
            normal_restitution: default_normal_restitution(),
            tangential_restitution: default_tangential_restitution(),
            friction_coefficient: default_friction(),
            rolling_resistance_coefficient: 0.0,
            contact_model: ContactModel::default(),
            soil_interaction_model: SoilInteractionModel::default(),
            soil_strength_pa: 0.0,
            scarring_drag_coefficient: 0.0,
            scarring_layer_density_kgpm3: 0.0,
            scarring_max_depth_m: None,
            roughness_model: RoughnessModel::default(),
            roughness_std_normal: 0.0,
            roughness_std_tangent: 0.0,
            roughness_std_angle: 0.0,
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
    pub release_points_csv: Option<PathBuf>,
    #[serde(default)]
    pub deposition_points_csv: Option<PathBuf>,
    #[serde(default)]
    pub trajectory_csv: Option<PathBuf>,
    #[serde(default)]
    pub contact_events_csv: Option<PathBuf>,
}

#[derive(Debug, Clone, Default, Serialize, Deserialize, PartialEq, Eq)]
pub struct ValidationScope {
    #[serde(default, rename = "type")]
    pub scope_type: String,
    #[serde(default)]
    pub note: String,
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
    #[serde(default)]
    pub ensemble_deposition_csv: Option<PathBuf>,
    #[serde(default)]
    pub ensemble_trajectories_dir: Option<PathBuf>,
    #[serde(default)]
    pub ensemble_impact_events_dir: Option<PathBuf>,
    #[serde(default)]
    pub impact_events_csv: Option<PathBuf>,
    #[serde(default)]
    pub impact_events_json: Option<PathBuf>,
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
    #[serde(default)]
    pub release_x_m: Option<f64>,
    #[serde(default)]
    pub release_y_m: Option<f64>,
    #[serde(default)]
    pub release_z_m: Option<f64>,
    #[serde(default)]
    pub observed_runout_m: Option<f64>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ReleasePoint {
    pub trajectory_id: String,
    pub experiment_id: String,
    pub x_m: f64,
    pub y_m: f64,
    pub z_m: f64,
    #[serde(default)]
    pub vx_mps: f64,
    #[serde(default)]
    pub vy_mps: f64,
    #[serde(default)]
    pub vz_mps: f64,
    #[serde(default)]
    pub mass_kg: Option<f64>,
    #[serde(default)]
    pub radius_m: Option<f64>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ObservedTrajectorySample {
    pub trajectory_id: String,
    pub experiment_id: String,
    pub time_s: f64,
    pub x_m: f64,
    pub y_m: f64,
    pub z_m: f64,
    #[serde(default)]
    pub vx_mps: Option<f64>,
    #[serde(default)]
    pub vy_mps: Option<f64>,
    #[serde(default)]
    pub vz_mps: Option<f64>,
    #[serde(default)]
    pub speed_mps: Option<f64>,
    #[serde(default)]
    pub kinetic_j: Option<f64>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ObservedContactEvent {
    pub event_id: String,
    pub trajectory_id: String,
    pub experiment_id: String,
    pub source_segment_id: String,
    pub next_segment_id: String,
    pub impact_index: usize,
    pub impact_time_s: f64,
    pub x_m: f64,
    pub y_m: f64,
    pub z_m: f64,
    #[serde(default)]
    pub raw_z_m: Option<f64>,
    pub incoming_vx_mps: f64,
    pub incoming_vy_mps: f64,
    pub incoming_vz_mps: f64,
    pub outgoing_vx_mps: f64,
    pub outgoing_vy_mps: f64,
    pub outgoing_vz_mps: f64,
    #[serde(default)]
    pub incoming_speed_mps: Option<f64>,
    #[serde(default)]
    pub outgoing_speed_mps: Option<f64>,
    #[serde(default)]
    pub pre_impact_kinetic_j: Option<f64>,
    #[serde(default)]
    pub post_impact_kinetic_j: Option<f64>,
    #[serde(default)]
    pub mass_kg: Option<f64>,
    #[serde(default)]
    pub radius_m: Option<f64>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct EnsembleDepositionPoint {
    pub release_id: String,
    pub trajectory_id: String,
    pub seed: Option<u64>,
    pub x_m: f64,
    pub y_m: f64,
    pub z_m: f64,
    pub runout_m: f64,
    pub final_speed_mps: f64,
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
        ObservationLoad::Loaded(data) => data,
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
    if case.validation_scope.is_some()
        && case.expected.tolerances.is_empty()
        && case.expected.minimums.is_empty()
        && case.expected.maximums.is_empty()
        && case.expected.values.is_empty()
    {
        warnings.push(
            "real-world validation case has no pass/fail acceptance thresholds; passed means the workflow completed and reported metrics".to_string(),
        );
    }

    let config = build_simulation_config(case)?;
    let result = config.run()?;
    if let Some(path) = &case.outputs.trajectory_csv {
        io::write_trajectory_csv(path, &result.samples)?;
    }
    if let Some(path) = &case.outputs.impact_events_csv {
        io::write_impact_events_csv(path, &result.impact_events)?;
    }
    if let Some(path) = &case.outputs.impact_events_json {
        io::write_impact_events_json(path, &result.impact_events)?;
    }

    let samples = &result.samples;
    let first = samples
        .first()
        .ok_or_else(|| ValidationError::EmptyTrajectory(case.case_id.clone()))?;
    let last = samples
        .last()
        .ok_or_else(|| ValidationError::EmptyTrajectory(case.case_id.clone()))?;

    let terrain = config.terrain.build()?;
    let mut metrics = compute_metrics(MetricContext {
        samples,
        impact_events: &result.impact_events,
        first,
        last,
        terrain: terrain.as_ref(),
        block: &config.block,
        observations: &observations.deposition_points,
        expected: &case.expected,
    });
    compute_ensemble_metrics(case, &mut metrics, &mut warnings)?;
    compute_validation_ensemble_metrics(case, &config, &observations, &mut metrics, &mut warnings)?;
    compute_observed_trajectory_metrics(case, &config, &observations, &mut metrics)?;
    compute_observed_contact_metrics(case, &config, &observations, &mut metrics)?;
    compute_roughness_comparison_metrics(case, &config, samples, &mut metrics)?;
    compute_scarring_comparison_metrics(case, &config, samples, &mut metrics)?;

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
        rolling_resistance_coefficient: case.parameters.rolling_resistance_coefficient,
        contact_model: case.parameters.contact_model,
        soil_interaction_model: case.parameters.soil_interaction_model,
        soil_strength_pa: case.parameters.soil_strength_pa,
        scarring_drag_coefficient: case.parameters.scarring_drag_coefficient,
        scarring_layer_density_kgpm3: case.parameters.scarring_layer_density_kgpm3,
        scarring_max_depth_m: case.parameters.scarring_max_depth_m,
        roughness_model: case.parameters.roughness_model,
        roughness_std_normal: case.parameters.roughness_std_normal,
        roughness_std_tangent: case.parameters.roughness_std_tangent,
        roughness_std_angle: case.parameters.roughness_std_angle,
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
        "esri_ascii_grid_clamped" | "ascii_dem_clamped" => {
            Ok(TerrainConfig::EsriAsciiGridClamped {
                path: terrain
                    .path
                    .as_ref()
                    .ok_or_else(|| {
                        ValidationError::Case(
                            "terrain.path is required for clamped ESRI ASCII grid".to_string(),
                        )
                    })?
                    .to_string_lossy()
                    .to_string(),
            })
        }
        other => Err(ValidationError::Case(format!(
            "unsupported terrain type '{other}'"
        ))),
    }
}

struct MetricContext<'a> {
    samples: &'a [TrajectorySample],
    impact_events: &'a [ImpactEvent],
    first: &'a TrajectorySample,
    last: &'a TrajectorySample,
    terrain: &'a dyn crate::terrain::Terrain,
    block: &'a SphereBlock,
    observations: &'a [DepositionPoint],
    expected: &'a ExpectedConfig,
}

fn compute_metrics(context: MetricContext<'_>) -> BTreeMap<String, f64> {
    let samples = context.samples;
    let impact_events = context.impact_events;
    let first = context.first;
    let last = context.last;
    let terrain = context.terrain;
    let block = context.block;
    let observations = context.observations;
    let expected = context.expected;
    let mut metrics = BTreeMap::new();
    let dx = last.x_m - first.x_m;
    let dy = last.y_m - first.y_m;
    let runout = (dx * dx + dy * dy).sqrt();
    let impact_count = impact_count(samples);
    let significant_impact_count = significant_impact_count(impact_events);
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
    metrics.insert("impact_event_count".to_string(), impact_events.len() as f64);
    metrics.insert(
        "significant_impact_count".to_string(),
        significant_impact_count as f64,
    );
    metrics.insert(
        "significant_impact_min_normal_speed_mps".to_string(),
        SIGNIFICANT_IMPACT_MIN_NORMAL_SPEED_MPS,
    );
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
    metrics.insert(
        "max_rolling_residual_mps".to_string(),
        samples
            .iter()
            .map(|sample| sample.rolling_residual_mps)
            .fold(0.0_f64, f64::max),
    );
    metrics.insert(
        "final_rolling_residual_mps".to_string(),
        last.rolling_residual_mps,
    );
    metrics.insert(
        "final_contact_tangent_speed_mps".to_string(),
        last.contact_tangent_speed_mps,
    );
    metrics.insert(
        "final_angular_speed_radps".to_string(),
        (last.omega_x_radps.powi(2) + last.omega_y_radps.powi(2) + last.omega_z_radps.powi(2))
            .sqrt(),
    );
    metrics.insert(
        "max_scarring_depth_m".to_string(),
        samples
            .iter()
            .map(|sample| sample.scarring_depth_m)
            .fold(0.0_f64, f64::max),
    );
    metrics.insert(
        "max_scarring_drag_force_n".to_string(),
        samples
            .iter()
            .map(|sample| sample.scarring_drag_force_n)
            .fold(0.0_f64, f64::max),
    );
    metrics.insert(
        "total_scarring_energy_loss_j".to_string(),
        samples
            .iter()
            .map(|sample| sample.scarring_energy_loss_j)
            .sum(),
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

    let roughness_active = case.parameters.roughness_model == RoughnessModel::StochasticContactV1
        && (case.parameters.roughness_std_normal > 0.0
            || case.parameters.roughness_std_tangent > 0.0
            || case.parameters.roughness_std_angle > 0.0);

    if case.release.perturbation.position_uniform_m == 0.0
        && case.release.perturbation.velocity_uniform_mps == 0.0
        && !roughness_active
    {
        warnings.push(
            "ensemble_size > 1 but release and roughness perturbations are zero; runout spread may be zero"
                .to_string(),
        );
    }

    let global_seed = case.random.seed.unwrap_or(0);
    let trajectory_ids = (0..ensemble_size)
        .map(|offset| format!("trajectory_{offset:06}"))
        .collect::<Vec<_>>();
    let mut ensemble_config = build_simulation_config(case)?;
    ensemble_config.random_seed = None;
    let ensemble = simulate_ensemble(
        &ensemble_config,
        case.case_id.clone(),
        global_seed,
        &trajectory_ids,
    )?;
    if case.observations.is_none() {
        if let Some(dir) = &case.outputs.ensemble_trajectories_dir {
            write_ensemble_trajectory_dir(dir, &ensemble.trajectories)?;
        }
        if let Some(dir) = &case.outputs.ensemble_impact_events_dir {
            write_ensemble_impact_events_dir(dir, &ensemble.trajectories)?;
        }
    }
    let mut runouts = ensemble
        .trajectories
        .iter()
        .map(|trajectory| trajectory.summary.runout_m)
        .collect::<Vec<_>>();
    let mut max_kinetic = ensemble
        .trajectories
        .iter()
        .map(|trajectory| trajectory.summary.max_kinetic_energy_j)
        .collect::<Vec<_>>();

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

    if let Some(seed) = case.random.seed {
        let alternate = simulate_ensemble(
            &ensemble_config,
            case.case_id.clone(),
            seed.wrapping_add(1),
            &trajectory_ids,
        )?;
        metrics.insert(
            "different_seed_ensemble_runout_delta_m".to_string(),
            max_runout_delta(&ensemble, &alternate),
        );
    }
    Ok(())
}

fn compute_validation_ensemble_metrics(
    case: &BenchmarkCase,
    base_config: &SimulationConfig,
    observations: &ObservationData,
    metrics: &mut BTreeMap<String, f64>,
    warnings: &mut Vec<String>,
) -> Result<(), ValidationError> {
    if observations.release_points.is_empty() || observations.deposition_points.is_empty() {
        return Ok(());
    }

    let ensemble_size = case.random.ensemble_size.max(1);
    let global_seed = case.random.seed.unwrap_or(0);
    let terrain = base_config.terrain.build()?;
    let mut runs = Vec::with_capacity(observations.release_points.len() * ensemble_size);
    let mut deposition_rows = Vec::with_capacity(observations.release_points.len() * ensemble_size);

    for release in &observations.release_points {
        let mut release_config = base_config.clone();
        release_config.initial_position_m = [release.x_m, release.y_m, release.z_m];
        release_config.initial_velocity_mps = [release.vx_mps, release.vy_mps, release.vz_mps];
        release_config.random_seed = None;
        if let (Some(radius_m), Some(mass_kg)) = (release.radius_m, release.mass_kg) {
            release_config.block = SphereBlock::new(radius_m, mass_kg);
        }

        for member_index in 0..ensemble_size {
            let member_id = format!("{}_member_{member_index:03}", release.trajectory_id);
            let request =
                TrajectoryRequest::from_global_seed(global_seed, case.case_id.clone(), member_id);
            let run =
                simulate_one_trajectory_with_terrain(&release_config, request, terrain.as_ref())?;
            deposition_rows.push(ensemble_deposition_row(&release.trajectory_id, &run));
            runs.push(run);
        }
    }

    if let Some(path) = &case.outputs.ensemble_deposition_csv {
        write_ensemble_deposition_csv(path, &deposition_rows)?;
    }
    if let Some(dir) = &case.outputs.ensemble_trajectories_dir {
        write_ensemble_trajectory_dir(dir, &runs)?;
    }
    if let Some(dir) = &case.outputs.ensemble_impact_events_dir {
        write_ensemble_impact_events_dir(dir, &runs)?;
    }

    compute_deposition_cloud_metrics(&runs, observations, metrics, warnings);
    metrics.insert(
        "validation_release_count".to_string(),
        observations.release_points.len() as f64,
    );
    metrics.insert(
        "validation_simulated_trajectory_count".to_string(),
        runs.len() as f64,
    );
    Ok(())
}

fn compute_observed_trajectory_metrics(
    case: &BenchmarkCase,
    base_config: &SimulationConfig,
    observations: &ObservationData,
    metrics: &mut BTreeMap<String, f64>,
) -> Result<(), ValidationError> {
    if observations.trajectory_samples.is_empty() {
        return Ok(());
    }

    let terrain = base_config.terrain.build()?;
    let releases = observations
        .release_points
        .iter()
        .map(|release| (release.trajectory_id.as_str(), release))
        .collect::<BTreeMap<_, _>>();
    let mut grouped: BTreeMap<String, Vec<&ObservedTrajectorySample>> = BTreeMap::new();
    for sample in &observations.trajectory_samples {
        grouped
            .entry(sample.trajectory_id.clone())
            .or_default()
            .push(sample);
    }

    let mut position_errors = Vec::new();
    let mut final_position_errors = Vec::new();
    let mut relative_energy_errors = Vec::new();
    let mut max_jump_errors = Vec::new();
    let mut observed_jump_envelope = 0.0_f64;
    let mut simulated_jump_envelope = 0.0_f64;
    let mut compared_trajectory_count = 0_usize;

    for (trajectory_id, mut observed_samples) in grouped {
        observed_samples.sort_by(|a, b| a.time_s.total_cmp(&b.time_s));
        let Some(first_observed) = observed_samples.first().copied() else {
            continue;
        };

        let mut config = base_config.clone();
        config.initial_position_m = [first_observed.x_m, first_observed.y_m, first_observed.z_m];
        config.initial_velocity_mps = [
            first_observed
                .vx_mps
                .unwrap_or(base_config.initial_velocity_mps[0]),
            first_observed
                .vy_mps
                .unwrap_or(base_config.initial_velocity_mps[1]),
            first_observed
                .vz_mps
                .unwrap_or(base_config.initial_velocity_mps[2]),
        ];
        if let Some(release) = releases.get(trajectory_id.as_str()) {
            config.initial_position_m = [release.x_m, release.y_m, release.z_m];
            config.initial_velocity_mps = [release.vx_mps, release.vy_mps, release.vz_mps];
            if let (Some(radius_m), Some(mass_kg)) = (release.radius_m, release.mass_kg) {
                config.block = SphereBlock::new(radius_m, mass_kg);
            }
        }
        config.max_time_s = observed_samples
            .last()
            .map(|sample| sample.time_s)
            .unwrap_or(config.max_time_s)
            .max(config.dt_s);
        config.random_seed = None;

        let request =
            TrajectoryRequest::from_global_seed(0, case.case_id.clone(), trajectory_id.clone());
        let run = simulate_one_trajectory_with_terrain(&config, request, terrain.as_ref())?;
        if run.samples.is_empty() {
            continue;
        }
        compared_trajectory_count += 1;

        let mut observed_max_jump = 0.0_f64;
        for observed in &observed_samples {
            let simulated = interpolate_sample(&run.samples, observed.time_s);
            position_errors.push(distance3(
                [simulated.x_m, simulated.y_m, simulated.z_m],
                [observed.x_m, observed.y_m, observed.z_m],
            ));
            if let Some(observed_kinetic) = observed.kinetic_j {
                if observed_kinetic > 0.0 {
                    relative_energy_errors
                        .push((simulated.kinetic_j - observed_kinetic).abs() / observed_kinetic);
                }
            }
            observed_max_jump = observed_max_jump.max(observed_clearance(
                observed,
                terrain.as_ref(),
                config.block.radius_m,
            ));
        }
        observed_jump_envelope = observed_jump_envelope.max(observed_max_jump);

        let simulated_max_jump =
            max_bounce_height(&run.samples, terrain.as_ref(), config.block.radius_m);
        simulated_jump_envelope = simulated_jump_envelope.max(simulated_max_jump);
        max_jump_errors.push((simulated_max_jump - observed_max_jump).abs());

        if let (Some(simulated_last), Some(observed_last)) =
            (run.samples.last(), observed_samples.last())
        {
            final_position_errors.push(distance3(
                [simulated_last.x_m, simulated_last.y_m, simulated_last.z_m],
                [observed_last.x_m, observed_last.y_m, observed_last.z_m],
            ));
        }
    }

    metrics.insert(
        "validation_trajectory_count".to_string(),
        compared_trajectory_count as f64,
    );
    metrics.insert(
        "observed_trajectory_sample_count".to_string(),
        observations.trajectory_samples.len() as f64,
    );
    if !position_errors.is_empty() {
        position_errors.sort_by(f64::total_cmp);
        metrics.insert(
            "trajectory_shape_mean_error_m".to_string(),
            mean(&position_errors),
        );
        metrics.insert(
            "trajectory_shape_p95_error_m".to_string(),
            percentile(&position_errors, 0.95),
        );
        metrics.insert(
            "trajectory_shape_max_error_m".to_string(),
            position_errors.last().copied().unwrap_or_default(),
        );
    }
    if !final_position_errors.is_empty() {
        metrics.insert(
            "trajectory_final_position_mean_error_m".to_string(),
            mean(&final_position_errors),
        );
    }
    if !relative_energy_errors.is_empty() {
        metrics.insert(
            "trajectory_energy_mean_relative_error".to_string(),
            mean(&relative_energy_errors),
        );
    }
    if !max_jump_errors.is_empty() {
        metrics.insert(
            "trajectory_max_jump_height_mean_error_m".to_string(),
            mean(&max_jump_errors),
        );
        metrics.insert(
            "trajectory_jump_height_envelope_error_m".to_string(),
            (simulated_jump_envelope - observed_jump_envelope).abs(),
        );
    }

    Ok(())
}

fn compute_observed_contact_metrics(
    case: &BenchmarkCase,
    base_config: &SimulationConfig,
    observations: &ObservationData,
    metrics: &mut BTreeMap<String, f64>,
) -> Result<(), ValidationError> {
    if observations.contact_events.is_empty() {
        return Ok(());
    }

    let releases = observations
        .release_points
        .iter()
        .map(|release| (release.trajectory_id.as_str(), release))
        .collect::<BTreeMap<_, _>>();
    let terrain = base_config.terrain.build()?;
    let mut impact_timing_errors = Vec::new();
    let mut rebound_velocity_errors = Vec::new();
    let mut post_impact_energy_change_errors = Vec::new();
    let mut compared_count = 0_usize;

    for observed in &observations.contact_events {
        let Some(release) = releases.get(observed.source_segment_id.as_str()) else {
            continue;
        };
        let mut config = base_config.clone();
        config.initial_position_m = [release.x_m, release.y_m, release.z_m];
        config.initial_velocity_mps = [release.vx_mps, release.vy_mps, release.vz_mps];
        if let (Some(radius_m), Some(mass_kg)) = (release.radius_m, release.mass_kg) {
            config.block = SphereBlock::new(radius_m, mass_kg);
        }
        if let (Some(radius_m), Some(mass_kg)) = (observed.radius_m, observed.mass_kg) {
            config.block = SphereBlock::new(radius_m, mass_kg);
        }
        config.max_time_s = (observed.impact_time_s + 4.0 * config.dt_s).max(config.dt_s);
        config.random_seed = None;

        let request = TrajectoryRequest::from_global_seed(
            0,
            case.case_id.clone(),
            observed.source_segment_id.clone(),
        );
        let run = simulate_one_trajectory_with_terrain(&config, request, terrain.as_ref())?;
        let Some(simulated_impact) = first_significant_impact_event(&run.impact_events) else {
            continue;
        };

        compared_count += 1;
        impact_timing_errors.push((simulated_impact.time_s - observed.impact_time_s).abs());
        rebound_velocity_errors.push(distance3(
            [
                simulated_impact.post_scarring_vx_mps,
                simulated_impact.post_scarring_vy_mps,
                simulated_impact.post_scarring_vz_mps,
            ],
            [
                observed.outgoing_vx_mps,
                observed.outgoing_vy_mps,
                observed.outgoing_vz_mps,
            ],
        ));

        if let (Some(pre_observed), Some(post_observed)) = (
            observed.pre_impact_kinetic_j,
            observed.post_impact_kinetic_j,
        ) {
            let observed_delta = post_observed - pre_observed;
            let simulated_delta = simulated_impact.post_scarring_translational_j
                - simulated_impact.pre_contact_translational_j;
            post_impact_energy_change_errors.push((simulated_delta - observed_delta).abs());
        }
    }

    metrics.insert(
        "observed_contact_event_count".to_string(),
        observations.contact_events.len() as f64,
    );
    metrics.insert(
        "contact_event_compared_count".to_string(),
        compared_count as f64,
    );
    if !impact_timing_errors.is_empty() {
        impact_timing_errors.sort_by(f64::total_cmp);
        metrics.insert(
            "impact_timing_mean_error_s".to_string(),
            mean(&impact_timing_errors),
        );
        metrics.insert(
            "impact_timing_p95_error_s".to_string(),
            percentile(&impact_timing_errors, 0.95),
        );
    }
    if !rebound_velocity_errors.is_empty() {
        rebound_velocity_errors.sort_by(f64::total_cmp);
        metrics.insert(
            "rebound_velocity_mean_error_mps".to_string(),
            mean(&rebound_velocity_errors),
        );
        metrics.insert(
            "rebound_velocity_p95_error_mps".to_string(),
            percentile(&rebound_velocity_errors, 0.95),
        );
    }
    if !post_impact_energy_change_errors.is_empty() {
        post_impact_energy_change_errors.sort_by(f64::total_cmp);
        metrics.insert(
            "post_impact_energy_change_mean_error_j".to_string(),
            mean(&post_impact_energy_change_errors),
        );
        metrics.insert(
            "post_impact_energy_change_p95_error_j".to_string(),
            percentile(&post_impact_energy_change_errors, 0.95),
        );
    }

    Ok(())
}

fn first_significant_impact_event(events: &[ImpactEvent]) -> Option<&ImpactEvent> {
    events
        .iter()
        .find(|event| event.incoming_normal_speed_mps >= SIGNIFICANT_IMPACT_MIN_NORMAL_SPEED_MPS)
        .or_else(|| events.first())
}

fn ensemble_deposition_row(release_id: &str, run: &TrajectoryRun) -> EnsembleDepositionPoint {
    let final_position = run.summary.final_position_m;
    EnsembleDepositionPoint {
        release_id: release_id.to_string(),
        trajectory_id: run.summary.trajectory_id.clone(),
        seed: run.summary.seed,
        x_m: final_position[0],
        y_m: final_position[1],
        z_m: final_position[2],
        runout_m: run.summary.runout_m,
        final_speed_mps: run.summary.final_speed_mps,
    }
}

fn write_ensemble_deposition_csv(
    path: impl AsRef<Path>,
    points: &[EnsembleDepositionPoint],
) -> Result<(), ValidationError> {
    if let Some(parent) = path.as_ref().parent() {
        fs::create_dir_all(parent)?;
    }
    let mut writer = csv::Writer::from_path(path)?;
    for point in points {
        writer.serialize(point)?;
    }
    writer.flush()?;
    Ok(())
}

fn write_ensemble_trajectory_dir(
    dir: impl AsRef<Path>,
    runs: &[TrajectoryRun],
) -> Result<(), ValidationError> {
    fs::create_dir_all(dir.as_ref())?;
    for run in runs {
        let filename = format!("{}.csv", safe_filename(&run.summary.trajectory_id));
        let path = dir.as_ref().join(filename);
        io::write_trajectory_csv(&path, &run.samples)?;
    }
    Ok(())
}

fn write_ensemble_impact_events_dir(
    dir: impl AsRef<Path>,
    runs: &[TrajectoryRun],
) -> Result<(), ValidationError> {
    fs::create_dir_all(dir.as_ref())?;
    for run in runs {
        if run.impact_events.is_empty() {
            continue;
        }
        let filename = format!("{}.csv", safe_filename(&run.summary.trajectory_id));
        let path = dir.as_ref().join(filename);
        io::write_impact_events_csv(&path, &run.impact_events)?;
    }
    Ok(())
}

fn safe_filename(text: &str) -> String {
    let mut output = String::with_capacity(text.len());
    for ch in text.chars() {
        if ch.is_ascii_alphanumeric() || matches!(ch, '_' | '-' | '.') {
            output.push(ch);
        } else {
            output.push('_');
        }
    }
    if output.is_empty() {
        "trajectory".to_string()
    } else {
        output
    }
}

fn compute_deposition_cloud_metrics(
    runs: &[TrajectoryRun],
    observations: &ObservationData,
    metrics: &mut BTreeMap<String, f64>,
    warnings: &mut Vec<String>,
) {
    let simulated_points = runs
        .iter()
        .map(|run| {
            (
                run.summary.final_position_m[0],
                run.summary.final_position_m[1],
            )
        })
        .collect::<Vec<_>>();
    let observed_points = observations
        .deposition_points
        .iter()
        .map(|point| (point.x_m, point.y_m))
        .collect::<Vec<_>>();
    if simulated_points.is_empty() || observed_points.is_empty() {
        return;
    }

    let simulated_runouts = runs
        .iter()
        .map(|run| run.summary.runout_m)
        .collect::<Vec<_>>();
    let observed_runouts = observations
        .deposition_points
        .iter()
        .filter_map(observed_runout)
        .collect::<Vec<_>>();

    if observed_runouts.is_empty() {
        warnings.push(
            "observed deposition points do not include release coordinates; runout error is omitted"
                .to_string(),
        );
    } else {
        metrics.insert(
            "observed_mean_runout_m".to_string(),
            mean(&observed_runouts),
        );
        metrics.insert(
            "simulated_mean_runout_m".to_string(),
            mean(&simulated_runouts),
        );
        metrics.insert(
            "runout_distance_error_m".to_string(),
            (mean(&simulated_runouts) - mean(&observed_runouts)).abs(),
        );
    }

    let simulated_centroid = centroid2(&simulated_points);
    let observed_centroid = centroid2(&observed_points);
    metrics.insert(
        "deposition_centroid_error_m".to_string(),
        distance2(simulated_centroid, observed_centroid),
    );
    metrics.insert(
        "deposition_cloud_mean_nearest_error_m".to_string(),
        symmetric_mean_nearest_distance(&simulated_points, &observed_points),
    );
    metrics.insert(
        "lateral_spread_error_m".to_string(),
        (stddev_axis_y(&simulated_points) - stddev_axis_y(&observed_points)).abs(),
    );
    metrics.insert(
        "deposition_cloud_overlap_fraction".to_string(),
        cloud_overlap_fraction(&simulated_points, &observed_points, 15.0),
    );
}

fn compute_roughness_comparison_metrics(
    case: &BenchmarkCase,
    config: &SimulationConfig,
    samples: &[TrajectorySample],
    metrics: &mut BTreeMap<String, f64>,
) -> Result<(), ValidationError> {
    if case.parameters.roughness_model != RoughnessModel::StochasticContactV1 {
        return Ok(());
    }
    if case.parameters.roughness_std_normal != 0.0
        || case.parameters.roughness_std_tangent != 0.0
        || case.parameters.roughness_std_angle != 0.0
    {
        return Ok(());
    }

    let mut baseline = config.clone();
    baseline.roughness_model = RoughnessModel::None;
    baseline.roughness_std_normal = 0.0;
    baseline.roughness_std_tangent = 0.0;
    baseline.roughness_std_angle = 0.0;
    let baseline_result = baseline.run()?;
    metrics.insert(
        "roughness_zero_baseline_max_position_delta_m".to_string(),
        max_position_delta(samples, &baseline_result.samples),
    );
    Ok(())
}

fn compute_scarring_comparison_metrics(
    case: &BenchmarkCase,
    config: &SimulationConfig,
    samples: &[TrajectorySample],
    metrics: &mut BTreeMap<String, f64>,
) -> Result<(), ValidationError> {
    if case.parameters.soil_interaction_model != SoilInteractionModel::ScarringContactV1 {
        return Ok(());
    }
    if case.parameters.soil_strength_pa != 0.0
        || case.parameters.scarring_drag_coefficient != 0.0
        || case.parameters.scarring_layer_density_kgpm3 != 0.0
        || case.parameters.scarring_max_depth_m.unwrap_or(0.0) != 0.0
    {
        return Ok(());
    }

    let mut baseline = config.clone();
    baseline.soil_interaction_model = SoilInteractionModel::None;
    baseline.soil_strength_pa = 0.0;
    baseline.scarring_drag_coefficient = 0.0;
    baseline.scarring_layer_density_kgpm3 = 0.0;
    baseline.scarring_max_depth_m = None;
    let baseline_result = baseline.run()?;
    metrics.insert(
        "scarring_zero_baseline_max_position_delta_m".to_string(),
        max_position_delta(samples, &baseline_result.samples),
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

#[derive(Debug, Clone, Default, PartialEq)]
struct ObservationData {
    deposition_points: Vec<DepositionPoint>,
    release_points: Vec<ReleasePoint>,
    trajectory_samples: Vec<ObservedTrajectorySample>,
    contact_events: Vec<ObservedContactEvent>,
}

enum ObservationLoad {
    Loaded(ObservationData),
    MissingRequired(PathBuf),
}

fn load_observations(
    case: &BenchmarkCase,
    warnings: &mut Vec<String>,
) -> Result<ObservationLoad, ValidationError> {
    let Some(observations) = &case.observations else {
        return Ok(ObservationLoad::Loaded(ObservationData::default()));
    };

    let mut data = ObservationData::default();
    if let Some(path) = &observations.release_points_csv {
        if !path.exists() {
            return Ok(ObservationLoad::MissingRequired(path.clone()));
        }
        data.release_points = read_release_points(path)?;
    }

    if let Some(path) = &observations.deposition_points_csv {
        if !path.exists() {
            return Ok(ObservationLoad::MissingRequired(path.clone()));
        }
        data.deposition_points = read_deposition_points(path)?;
    }
    if let Some(path) = &observations.trajectory_csv {
        if !path.exists() {
            return Ok(ObservationLoad::MissingRequired(path.clone()));
        }
        data.trajectory_samples = read_observed_trajectory_samples(path)?;
    }
    if let Some(path) = &observations.contact_events_csv {
        if !path.exists() {
            return Ok(ObservationLoad::MissingRequired(path.clone()));
        }
        data.contact_events = read_observed_contact_events(path)?;
    }
    if data.deposition_points.len() > 1 && data.release_points.is_empty() {
        warnings.push(format!(
            "case {} has {} observed deposition points; current metrics use the first point",
            case.case_id,
            data.deposition_points.len()
        ));
    }
    Ok(ObservationLoad::Loaded(data))
}

fn read_deposition_points(path: &Path) -> Result<Vec<DepositionPoint>, ValidationError> {
    let mut reader = csv::Reader::from_path(path)?;
    let mut points = Vec::new();
    for record in reader.deserialize() {
        points.push(record?);
    }
    Ok(points)
}

fn read_release_points(path: &Path) -> Result<Vec<ReleasePoint>, ValidationError> {
    let mut reader = csv::Reader::from_path(path)?;
    let mut points = Vec::new();
    for record in reader.deserialize() {
        points.push(record?);
    }
    Ok(points)
}

fn read_observed_trajectory_samples(
    path: &Path,
) -> Result<Vec<ObservedTrajectorySample>, ValidationError> {
    let mut reader = csv::Reader::from_path(path)?;
    let mut samples = Vec::new();
    for record in reader.deserialize() {
        samples.push(record?);
    }
    Ok(samples)
}

fn read_observed_contact_events(path: &Path) -> Result<Vec<ObservedContactEvent>, ValidationError> {
    let mut reader = csv::Reader::from_path(path)?;
    let mut events = Vec::new();
    for record in reader.deserialize() {
        events.push(record?);
    }
    Ok(events)
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

fn significant_impact_count(impact_events: &[ImpactEvent]) -> usize {
    impact_events
        .iter()
        .filter(|event| event.incoming_normal_speed_mps >= SIGNIFICANT_IMPACT_MIN_NORMAL_SPEED_MPS)
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

fn interpolate_sample(samples: &[TrajectorySample], time_s: f64) -> TrajectorySample {
    if time_s <= samples[0].time_s {
        return samples[0].clone();
    }
    for pair in samples.windows(2) {
        let left = &pair[0];
        let right = &pair[1];
        if time_s <= right.time_s {
            let span = (right.time_s - left.time_s).max(f64::EPSILON);
            let weight = ((time_s - left.time_s) / span).clamp(0.0, 1.0);
            return interpolate_trajectory_sample(left, right, weight);
        }
    }
    samples
        .last()
        .cloned()
        .unwrap_or_else(|| samples[0].clone())
}

fn interpolate_trajectory_sample(
    left: &TrajectorySample,
    right: &TrajectorySample,
    weight: f64,
) -> TrajectorySample {
    let lerp = |a: f64, b: f64| a * (1.0 - weight) + b * weight;
    let mut sample = left.clone();
    sample.time_s = lerp(left.time_s, right.time_s);
    sample.x_m = lerp(left.x_m, right.x_m);
    sample.y_m = lerp(left.y_m, right.y_m);
    sample.z_m = lerp(left.z_m, right.z_m);
    sample.vx_mps = lerp(left.vx_mps, right.vx_mps);
    sample.vy_mps = lerp(left.vy_mps, right.vy_mps);
    sample.vz_mps = lerp(left.vz_mps, right.vz_mps);
    sample.speed_mps = lerp(left.speed_mps, right.speed_mps);
    sample.kinetic_j = lerp(left.kinetic_j, right.kinetic_j);
    sample
}

fn observed_clearance(
    sample: &ObservedTrajectorySample,
    terrain: &dyn crate::terrain::Terrain,
    radius_m: f64,
) -> f64 {
    (sample.z_m - terrain.height(sample.x_m, sample.y_m) - radius_m).max(0.0)
}

fn max_runout_delta(
    left: &crate::simulation::EnsembleResult,
    right: &crate::simulation::EnsembleResult,
) -> f64 {
    left.trajectories
        .iter()
        .zip(right.trajectories.iter())
        .map(|(a, b)| (a.summary.runout_m - b.summary.runout_m).abs())
        .fold(0.0_f64, f64::max)
}

fn observed_runout(point: &DepositionPoint) -> Option<f64> {
    point.observed_runout_m.or_else(|| {
        Some(distance2(
            (point.x_m, point.y_m),
            (point.release_x_m?, point.release_y_m?),
        ))
    })
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

fn centroid2(points: &[(f64, f64)]) -> (f64, f64) {
    if points.is_empty() {
        return (0.0, 0.0);
    }
    let x = points.iter().map(|point| point.0).sum::<f64>() / points.len() as f64;
    let y = points.iter().map(|point| point.1).sum::<f64>() / points.len() as f64;
    (x, y)
}

fn distance2(a: (f64, f64), b: (f64, f64)) -> f64 {
    ((a.0 - b.0).powi(2) + (a.1 - b.1).powi(2)).sqrt()
}

fn symmetric_mean_nearest_distance(left: &[(f64, f64)], right: &[(f64, f64)]) -> f64 {
    0.5 * (mean_nearest_distance(left, right) + mean_nearest_distance(right, left))
}

fn mean_nearest_distance(from: &[(f64, f64)], to: &[(f64, f64)]) -> f64 {
    if from.is_empty() || to.is_empty() {
        return 0.0;
    }
    from.iter()
        .map(|point| {
            to.iter()
                .map(|candidate| distance2(*point, *candidate))
                .fold(f64::INFINITY, f64::min)
        })
        .sum::<f64>()
        / from.len() as f64
}

fn stddev_axis_y(points: &[(f64, f64)]) -> f64 {
    if points.len() <= 1 {
        return 0.0;
    }
    let mean_y = points.iter().map(|point| point.1).sum::<f64>() / points.len() as f64;
    let variance = points
        .iter()
        .map(|point| (point.1 - mean_y).powi(2))
        .sum::<f64>()
        / points.len() as f64;
    variance.sqrt()
}

fn cloud_overlap_fraction(
    simulated_points: &[(f64, f64)],
    observed_points: &[(f64, f64)],
    radius_m: f64,
) -> f64 {
    if simulated_points.is_empty() {
        return 0.0;
    }
    let hits = simulated_points
        .iter()
        .filter(|point| {
            observed_points
                .iter()
                .any(|observed| distance2(**point, *observed) <= radius_m)
        })
        .count();
    hits as f64 / simulated_points.len() as f64
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
