use crate::{
    dynamics::{ContactModel, ContactParameterProvider, ScarringSettings, SoilInteractionModel},
    geometry::SphereBlock,
    integrator::{
        simulate_fixed_step_with_events, simulate_fixed_step_with_events_and_contact_parameters,
        IntegratorSettings,
    },
    state::{BodyState, ContactState, ImpactEvent, TrajectorySample},
    stochastic::{
        derive_trajectory_seed, sample_release, stable_hash64, ContactRoughness,
        ReleasePerturbation, RoughnessModel,
    },
    terrain::{
        ChannelizedGully, ClampedDemGrid, DemGrid, GaussianBump, Paraboloid, Plane,
        SinusoidalRoughSlope, StepTerrain, TerracedSlope, Terrain, TerrainError, VShapedValley,
    },
    Vec3,
};
use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;
use thiserror::Error;

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct SimulationConfig {
    pub block: SphereBlock,
    pub initial_position_m: [f64; 3],
    pub initial_velocity_mps: [f64; 3],
    #[serde(default)]
    pub initial_angular_velocity_radps: [f64; 3],
    pub terrain: TerrainConfig,
    pub dt_s: f64,
    pub max_time_s: f64,
    #[serde(default = "default_gravity")]
    pub gravity_mps2: f64,
    #[serde(default = "default_normal_restitution")]
    pub normal_restitution: f64,
    #[serde(default = "default_tangential_restitution")]
    pub tangential_restitution: f64,
    #[serde(default = "default_friction")]
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
    #[serde(default = "default_stop_speed")]
    pub stop_speed_mps: f64,
    #[serde(default)]
    pub random_seed: Option<u64>,
    #[serde(default)]
    pub release_perturbation: ReleasePerturbation,
}

pub const DEFAULT_STOP_SPEED_MPS: f64 = 0.10;
pub const STOP_SIGNIFICANT_IMPACT_MIN_NORMAL_SPEED_MPS: f64 = 0.05;
pub const STOP_LOW_ENERGY_CONTACT_SPEED_MPS: f64 = 0.05;

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub enum TerrainConfig {
    Plane {
        z0_m: f64,
        slope_x: f64,
        slope_y: f64,
    },
    Paraboloid {
        z0_m: f64,
        ax: f64,
        ay: f64,
    },
    Step {
        step_x_m: f64,
        high_z_m: f64,
        low_z_m: f64,
    },
    VShapedValley {
        z0_m: f64,
        slope_x: f64,
        side_slope_abs_y: f64,
    },
    TerracedSlope {
        z0_m: f64,
        slope_x: f64,
        terrace_width_m: f64,
        terrace_height_m: f64,
    },
    SinusoidalRoughSlope {
        z0_m: f64,
        slope_x: f64,
        amplitude_m: f64,
        wavelength_m: f64,
    },
    GaussianBump {
        z0_m: f64,
        slope_x: f64,
        center_x_m: f64,
        center_y_m: f64,
        height_m: f64,
        sigma_m: f64,
    },
    ChannelizedGully {
        z0_m: f64,
        slope_x: f64,
        depth_m: f64,
        width_m: f64,
    },
    EsriAsciiGrid {
        path: String,
    },
    EsriAsciiGridClamped {
        path: String,
    },
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct SimulationResult {
    pub samples: Vec<TrajectorySample>,
    #[serde(default)]
    pub impact_events: Vec<ImpactEvent>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub stop_state: Option<StopStateProvenance>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct TrajectoryRequest {
    pub case_id: String,
    pub trajectory_id: String,
    pub seed: Option<u64>,
}

impl TrajectoryRequest {
    pub fn new(
        case_id: impl Into<String>,
        trajectory_id: impl Into<String>,
        seed: Option<u64>,
    ) -> Self {
        Self {
            case_id: case_id.into(),
            trajectory_id: trajectory_id.into(),
            seed,
        }
    }

    pub fn from_global_seed(
        global_seed: u64,
        case_id: impl Into<String>,
        trajectory_id: impl Into<String>,
    ) -> Self {
        let case_id = case_id.into();
        let trajectory_id = trajectory_id.into();
        let seed = derive_trajectory_seed(global_seed, &case_id, &trajectory_id);
        Self {
            case_id,
            trajectory_id,
            seed: Some(seed),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct TrajectoryRun {
    pub request: TrajectoryRequest,
    pub samples: Vec<TrajectorySample>,
    #[serde(default)]
    pub impact_events: Vec<ImpactEvent>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub stop_state: Option<StopStateProvenance>,
    pub summary: TrajectorySummary,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum StopReason {
    ExplicitStoppedState,
    FinalSpeedBelowStopThreshold,
    TMaxReachedAirborne,
    TMaxReachedInContactState,
    TMaxReachedOther,
    Unknown,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct TerminationFlags {
    pub low_velocity: bool,
    pub max_steps: bool,
    pub t_max: bool,
    pub domain_exit: bool,
    pub terrain_error: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct StopStateProvenance {
    pub stop_reason: StopReason,
    pub final_contact_state: ContactState,
    pub final_speed_mps: f64,
    pub final_kinetic_j: f64,
    pub termination_flags: TerminationFlags,
    pub last_significant_impact_time_s: Option<f64>,
    pub last_significant_impact_x_m: Option<f64>,
    pub last_significant_impact_y_m: Option<f64>,
    pub last_significant_impact_z_m: Option<f64>,
    pub distance_last_significant_impact_to_final_m: Option<f64>,
    #[serde(default)]
    pub significant_impact_count: usize,
    pub low_energy_contact_count: usize,
    pub terrain_normal_x: Option<f64>,
    pub terrain_normal_y: Option<f64>,
    pub terrain_normal_z: Option<f64>,
    pub terrain_slope_abs: Option<f64>,
    #[serde(default)]
    pub terrain_material_context_available: bool,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub final_terrain_class_id: Option<i32>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub final_terrain_class_name: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub final_terrain_class_source: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub last_significant_impact_terrain_class_id: Option<i32>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub last_significant_impact_terrain_class_name: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub last_significant_impact_terrain_class_source: Option<String>,
    #[serde(default)]
    pub significant_impact_terrain_class_counts: BTreeMap<String, usize>,
    #[serde(default)]
    pub significant_impact_terrain_class_sequence_head: Vec<String>,
    #[serde(default)]
    pub significant_impact_terrain_class_sequence_tail: Vec<String>,
    #[serde(default)]
    pub significant_impact_terrain_class_sequence_truncated: bool,
    #[serde(default)]
    pub significant_impact_terrain_class_unavailable_count: usize,
    #[serde(default)]
    pub terrain_material_instrumentation_gaps: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct TrajectorySummary {
    pub trajectory_id: String,
    pub seed: Option<u64>,
    pub sample_count: usize,
    pub final_position_m: [f64; 3],
    pub final_speed_mps: f64,
    pub runout_m: f64,
    pub max_speed_mps: f64,
    pub max_kinetic_energy_j: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct EnsembleResult {
    pub case_id: String,
    pub global_seed: u64,
    pub trajectories: Vec<TrajectoryRun>,
}

#[derive(Debug, Error)]
pub enum SimulationError {
    #[error("terrain error: {0}")]
    Terrain(#[from] TerrainError),
    #[error("configuration serialization error: {0}")]
    Serialize(#[from] serde_json::Error),
    #[error("configuration value must be positive: {0}")]
    NonPositive(&'static str),
    #[error("configuration value must be within [{min}, {max}]: {field}")]
    OutOfRange {
        field: &'static str,
        min: f64,
        max: f64,
    },
    #[error("trajectory {0} has no samples")]
    EmptyTrajectory(String),
    #[error("unsupported contact model for simulation: {0}")]
    UnsupportedContactModel(&'static str),
}

impl SimulationConfig {
    pub fn initial_state(&self) -> BodyState {
        let state = BodyState {
            position_m: arr3(self.initial_position_m),
            velocity_mps: arr3(self.initial_velocity_mps),
            angular_velocity_radps: arr3(self.initial_angular_velocity_radps),
        };
        if let Some(seed) = self.random_seed {
            sample_release(state, self.release_perturbation, seed)
        } else {
            state
        }
    }

    pub fn run(&self) -> Result<SimulationResult, SimulationError> {
        self.validate()?;
        let terrain = self.terrain.build()?;
        self.run_with_terrain(terrain.as_ref())
    }

    pub fn run_with_terrain(
        &self,
        terrain: &dyn Terrain,
    ) -> Result<SimulationResult, SimulationError> {
        self.run_with_terrain_and_contact_parameters(terrain, None)
    }

    pub fn run_with_terrain_and_contact_parameters(
        &self,
        terrain: &dyn Terrain,
        contact_parameters: Option<&dyn ContactParameterProvider>,
    ) -> Result<SimulationResult, SimulationError> {
        self.validate()?;
        let settings = IntegratorSettings {
            dt_s: self.dt_s,
            max_time_s: self.max_time_s,
            gravity_mps2: self.gravity_mps2,
            normal_restitution: self.normal_restitution,
            tangential_restitution: self.tangential_restitution,
            friction_coefficient: self.friction_coefficient,
            rolling_resistance_coefficient: self.rolling_resistance_coefficient,
            stop_speed_mps: self.stop_speed_mps,
            contact_model: self.contact_model,
            scarring: ScarringSettings {
                soil_interaction_model: self.soil_interaction_model,
                soil_strength_pa: self.soil_strength_pa,
                scarring_drag_coefficient: self.scarring_drag_coefficient,
                scarring_layer_density_kgpm3: self.scarring_layer_density_kgpm3,
                scarring_max_depth_m: self.scarring_max_depth_m,
            },
            roughness: ContactRoughness {
                roughness_model: self.roughness_model,
                roughness_std_normal: self.roughness_std_normal,
                roughness_std_tangent: self.roughness_std_tangent,
                roughness_std_angle: self.roughness_std_angle,
            },
            roughness_seed: self.random_seed,
        };
        let result = if let Some(contact_parameters) = contact_parameters {
            simulate_fixed_step_with_events_and_contact_parameters(
                self.initial_state(),
                self.block,
                terrain,
                settings,
                Some(contact_parameters),
            )
        } else {
            simulate_fixed_step_with_events(self.initial_state(), self.block, terrain, settings)
        };
        let stop_state =
            build_stop_state_provenance(&result.samples, &result.impact_events, terrain, &settings);
        Ok(SimulationResult {
            samples: result.samples,
            impact_events: result.impact_events,
            stop_state,
        })
    }

    pub fn config_fingerprint(&self) -> Result<String, SimulationError> {
        let serialized = serde_json::to_string(self)?;
        Ok(format!("{:016x}", stable_hash64(serialized.as_bytes())))
    }

    pub fn run_fingerprint(&self, request: &TrajectoryRequest) -> Result<String, SimulationError> {
        let serialized = serde_json::to_string(&(self, request))?;
        Ok(format!("{:016x}", stable_hash64(serialized.as_bytes())))
    }

    fn validate(&self) -> Result<(), SimulationError> {
        if self.contact_model == ContactModel::ShapeContactV0 {
            return Err(SimulationError::UnsupportedContactModel(
                "shape_contact_v0 is a verification scaffold; analytic impulses are not wired into fixed-step simulation yet",
            ));
        }
        require_positive(self.block.radius_m, "block.radius_m")?;
        require_positive(self.block.mass_kg, "block.mass_kg")?;
        require_positive(self.dt_s, "dt_s")?;
        require_positive(self.max_time_s, "max_time_s")?;
        require_positive(self.gravity_mps2, "gravity_mps2")?;
        require_unit_interval(self.normal_restitution, "normal_restitution")?;
        require_unit_interval(self.tangential_restitution, "tangential_restitution")?;
        require_nonnegative(self.friction_coefficient, "friction_coefficient")?;
        require_nonnegative(
            self.rolling_resistance_coefficient,
            "rolling_resistance_coefficient",
        )?;
        require_nonnegative(self.stop_speed_mps, "stop_speed_mps")?;
        self.release_perturbation
            .validate()
            .map_err(SimulationError::NonPositive)?;
        ContactRoughness {
            roughness_model: self.roughness_model,
            roughness_std_normal: self.roughness_std_normal,
            roughness_std_tangent: self.roughness_std_tangent,
            roughness_std_angle: self.roughness_std_angle,
        }
        .validate()
        .map_err(SimulationError::NonPositive)?;
        ScarringSettings {
            soil_interaction_model: self.soil_interaction_model,
            soil_strength_pa: self.soil_strength_pa,
            scarring_drag_coefficient: self.scarring_drag_coefficient,
            scarring_layer_density_kgpm3: self.scarring_layer_density_kgpm3,
            scarring_max_depth_m: self.scarring_max_depth_m,
        }
        .validate()
        .map_err(SimulationError::NonPositive)?;
        Ok(())
    }
}

fn require_positive(value: f64, field: &'static str) -> Result<(), SimulationError> {
    if value.is_finite() && value > 0.0 {
        Ok(())
    } else {
        Err(SimulationError::NonPositive(field))
    }
}

fn require_nonnegative(value: f64, field: &'static str) -> Result<(), SimulationError> {
    if value.is_finite() && value >= 0.0 {
        Ok(())
    } else {
        Err(SimulationError::NonPositive(field))
    }
}

fn require_unit_interval(value: f64, field: &'static str) -> Result<(), SimulationError> {
    require_nonnegative(value, field)?;
    if value <= 1.0 {
        Ok(())
    } else {
        Err(SimulationError::OutOfRange {
            field,
            min: 0.0,
            max: 1.0,
        })
    }
}

pub fn simulate_one_trajectory(
    config: &SimulationConfig,
    request: TrajectoryRequest,
) -> Result<TrajectoryRun, SimulationError> {
    let terrain = config.terrain.build()?;
    simulate_one_trajectory_with_terrain(config, request, terrain.as_ref())
}

pub fn simulate_one_trajectory_with_terrain(
    config: &SimulationConfig,
    request: TrajectoryRequest,
    terrain: &dyn Terrain,
) -> Result<TrajectoryRun, SimulationError> {
    simulate_one_trajectory_with_terrain_and_contact_parameters(config, request, terrain, None)
}

pub fn simulate_one_trajectory_with_terrain_and_contact_parameters(
    config: &SimulationConfig,
    request: TrajectoryRequest,
    terrain: &dyn Terrain,
    contact_parameters: Option<&dyn ContactParameterProvider>,
) -> Result<TrajectoryRun, SimulationError> {
    let mut trajectory_config = config.clone();
    trajectory_config.random_seed = request.seed;
    let result =
        trajectory_config.run_with_terrain_and_contact_parameters(terrain, contact_parameters)?;
    let summary = summarize_trajectory(&request.trajectory_id, request.seed, &result.samples)?;
    Ok(TrajectoryRun {
        request,
        samples: result.samples,
        impact_events: result.impact_events,
        stop_state: result.stop_state,
        summary,
    })
}

pub fn simulate_ensemble(
    config: &SimulationConfig,
    case_id: impl Into<String>,
    global_seed: u64,
    trajectory_ids: &[String],
) -> Result<EnsembleResult, SimulationError> {
    simulate_ensemble_with_contact_parameters(config, case_id, global_seed, trajectory_ids, None)
}

pub fn simulate_ensemble_with_contact_parameters(
    config: &SimulationConfig,
    case_id: impl Into<String>,
    global_seed: u64,
    trajectory_ids: &[String],
    contact_parameters: Option<&dyn ContactParameterProvider>,
) -> Result<EnsembleResult, SimulationError> {
    let case_id = case_id.into();
    let terrain = config.terrain.build()?;
    let mut trajectories = Vec::with_capacity(trajectory_ids.len());
    for trajectory_id in trajectory_ids {
        let request = TrajectoryRequest::from_global_seed(
            global_seed,
            case_id.clone(),
            trajectory_id.clone(),
        );
        trajectories.push(simulate_one_trajectory_with_terrain_and_contact_parameters(
            config,
            request,
            terrain.as_ref(),
            contact_parameters,
        )?);
    }
    Ok(EnsembleResult {
        case_id,
        global_seed,
        trajectories,
    })
}

pub fn summarize_trajectory(
    trajectory_id: impl Into<String>,
    seed: Option<u64>,
    samples: &[TrajectorySample],
) -> Result<TrajectorySummary, SimulationError> {
    let trajectory_id = trajectory_id.into();
    let first = samples
        .first()
        .ok_or_else(|| SimulationError::EmptyTrajectory(trajectory_id.clone()))?;
    let last = samples
        .last()
        .expect("non-empty samples have a last sample");
    let runout_m = ((last.x_m - first.x_m).powi(2) + (last.y_m - first.y_m).powi(2)).sqrt();
    let max_speed_mps = samples
        .iter()
        .map(|sample| sample.speed_mps)
        .fold(0.0_f64, f64::max);
    let max_kinetic_energy_j = samples
        .iter()
        .map(|sample| sample.kinetic_j)
        .fold(0.0_f64, f64::max);

    Ok(TrajectorySummary {
        trajectory_id,
        seed,
        sample_count: samples.len(),
        final_position_m: [last.x_m, last.y_m, last.z_m],
        final_speed_mps: last.speed_mps,
        runout_m,
        max_speed_mps,
        max_kinetic_energy_j,
    })
}

fn build_stop_state_provenance(
    samples: &[TrajectorySample],
    impact_events: &[ImpactEvent],
    terrain: &dyn Terrain,
    settings: &IntegratorSettings,
) -> Option<StopStateProvenance> {
    let last = samples.last()?;
    let step_count = samples.len().saturating_sub(1);
    let configured_max_steps = (settings.max_time_s / settings.dt_s + 1.0e-12).floor() as usize;
    let t_max_reached = last.time_s + 1.0e-12 >= settings.max_time_s;
    let max_steps_reached = step_count >= configured_max_steps;
    let low_velocity = last.speed_mps <= settings.stop_speed_mps;
    let final_contact_state = last.contact_state;
    let stop_reason = if final_contact_state == ContactState::Stopped {
        StopReason::ExplicitStoppedState
    } else if t_max_reached && final_contact_state == ContactState::Airborne {
        StopReason::TMaxReachedAirborne
    } else if low_velocity {
        StopReason::FinalSpeedBelowStopThreshold
    } else if t_max_reached
        && matches!(
            final_contact_state,
            ContactState::Impact | ContactState::Sliding | ContactState::Rolling
        )
    {
        StopReason::TMaxReachedInContactState
    } else if t_max_reached {
        StopReason::TMaxReachedOther
    } else {
        StopReason::Unknown
    };

    let last_significant_impact = impact_events.iter().rev().find(|event| {
        event.incoming_normal_speed_mps >= STOP_SIGNIFICANT_IMPACT_MIN_NORMAL_SPEED_MPS
    });
    let significant_impact_count = impact_events
        .iter()
        .filter(|event| {
            event.incoming_normal_speed_mps >= STOP_SIGNIFICANT_IMPACT_MIN_NORMAL_SPEED_MPS
        })
        .count();
    let distance_last_significant_impact_to_final_m = last_significant_impact
        .map(|event| ((last.x_m - event.x_m).powi(2) + (last.y_m - event.y_m).powi(2)).sqrt());
    let low_energy_contact_count = samples
        .iter()
        .filter(|sample| {
            matches!(
                sample.contact_state,
                ContactState::Impact
                    | ContactState::Sliding
                    | ContactState::Rolling
                    | ContactState::Stopped
            ) && sample.speed_mps <= STOP_LOW_ENERGY_CONTACT_SPEED_MPS
        })
        .count();
    let normal = terrain.normal(last.x_m, last.y_m);
    let terrain_slope_abs = if normal.z.abs() > 1.0e-12 {
        Some((normal.x.hypot(normal.y) / normal.z.abs()).abs())
    } else {
        None
    };

    Some(StopStateProvenance {
        stop_reason,
        final_contact_state,
        final_speed_mps: last.speed_mps,
        final_kinetic_j: last.kinetic_j,
        termination_flags: TerminationFlags {
            low_velocity,
            max_steps: max_steps_reached && final_contact_state != ContactState::Stopped,
            t_max: t_max_reached && final_contact_state != ContactState::Stopped,
            domain_exit: false,
            terrain_error: false,
        },
        last_significant_impact_time_s: last_significant_impact.map(|event| event.time_s),
        last_significant_impact_x_m: last_significant_impact.map(|event| event.x_m),
        last_significant_impact_y_m: last_significant_impact.map(|event| event.y_m),
        last_significant_impact_z_m: last_significant_impact.map(|event| event.z_m),
        distance_last_significant_impact_to_final_m,
        significant_impact_count,
        low_energy_contact_count,
        terrain_normal_x: Some(normal.x),
        terrain_normal_y: Some(normal.y),
        terrain_normal_z: Some(normal.z),
        terrain_slope_abs,
        terrain_material_context_available: false,
        final_terrain_class_id: None,
        final_terrain_class_name: None,
        final_terrain_class_source: None,
        last_significant_impact_terrain_class_id: None,
        last_significant_impact_terrain_class_name: None,
        last_significant_impact_terrain_class_source: None,
        significant_impact_terrain_class_counts: BTreeMap::new(),
        significant_impact_terrain_class_sequence_head: Vec::new(),
        significant_impact_terrain_class_sequence_tail: Vec::new(),
        significant_impact_terrain_class_sequence_truncated: false,
        significant_impact_terrain_class_unavailable_count: 0,
        terrain_material_instrumentation_gaps: vec![
            "terrain_classes metadata is not configured for this run".to_string(),
        ],
    })
}

impl TerrainConfig {
    pub fn build(&self) -> Result<Box<dyn Terrain>, TerrainError> {
        match self {
            TerrainConfig::Plane {
                z0_m,
                slope_x,
                slope_y,
            } => Ok(Box::new(Plane {
                z0_m: *z0_m,
                slope_x: *slope_x,
                slope_y: *slope_y,
            })),
            TerrainConfig::Paraboloid { z0_m, ax, ay } => Ok(Box::new(Paraboloid {
                z0_m: *z0_m,
                ax: *ax,
                ay: *ay,
            })),
            TerrainConfig::Step {
                step_x_m,
                high_z_m,
                low_z_m,
            } => Ok(Box::new(StepTerrain {
                step_x_m: *step_x_m,
                high_z_m: *high_z_m,
                low_z_m: *low_z_m,
            })),
            TerrainConfig::VShapedValley {
                z0_m,
                slope_x,
                side_slope_abs_y,
            } => Ok(Box::new(VShapedValley {
                z0_m: *z0_m,
                slope_x: *slope_x,
                side_slope_abs_y: *side_slope_abs_y,
            })),
            TerrainConfig::TerracedSlope {
                z0_m,
                slope_x,
                terrace_width_m,
                terrace_height_m,
            } => Ok(Box::new(TerracedSlope {
                z0_m: *z0_m,
                slope_x: *slope_x,
                terrace_width_m: *terrace_width_m,
                terrace_height_m: *terrace_height_m,
            })),
            TerrainConfig::SinusoidalRoughSlope {
                z0_m,
                slope_x,
                amplitude_m,
                wavelength_m,
            } => Ok(Box::new(SinusoidalRoughSlope {
                z0_m: *z0_m,
                slope_x: *slope_x,
                amplitude_m: *amplitude_m,
                wavelength_m: *wavelength_m,
            })),
            TerrainConfig::GaussianBump {
                z0_m,
                slope_x,
                center_x_m,
                center_y_m,
                height_m,
                sigma_m,
            } => Ok(Box::new(GaussianBump {
                z0_m: *z0_m,
                slope_x: *slope_x,
                center_x_m: *center_x_m,
                center_y_m: *center_y_m,
                height_m: *height_m,
                sigma_m: *sigma_m,
            })),
            TerrainConfig::ChannelizedGully {
                z0_m,
                slope_x,
                depth_m,
                width_m,
            } => Ok(Box::new(ChannelizedGully {
                z0_m: *z0_m,
                slope_x: *slope_x,
                depth_m: *depth_m,
                width_m: *width_m,
            })),
            TerrainConfig::EsriAsciiGrid { path } => Ok(Box::new(DemGrid::from_ascii_grid(path)?)),
            TerrainConfig::EsriAsciiGridClamped { path } => {
                Ok(Box::new(ClampedDemGrid::from_ascii_grid(path)?))
            }
        }
    }
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

fn default_stop_speed() -> f64 {
    DEFAULT_STOP_SPEED_MPS
}

fn arr3(values: [f64; 3]) -> Vec3 {
    Vec3::new(values[0], values[1], values[2])
}
