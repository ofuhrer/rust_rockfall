//! Verification and validation helpers, case loading, and metric computation.

mod metric_math;
mod metrics;
mod probabilistic;
mod runner;
pub mod types;
mod validation_io;

use metric_math::{
    centroid2, cloud_overlap_fraction, distance2, distance3, mean, nonempty_mean, percentile,
    stddev_axis_y, symmetric_mean_nearest_distance,
};

use crate::{
    dynamics::{ContactModel, ContactParameterProvider, ScarringDepthSource, SoilInteractionModel},
    geodata::{GeodataError, ReleaseZoneMetadata, TerrainClassMap, TerrainSourceMetadata},
    geometry::SphereBlock,
    io,
    manifest::{
        OutputManifest, PerformanceManifest, ReleaseZoneManifest, RunManifest, SeedPolicyManifest,
        ShapeMetadataManifest, StopStateSummaryManifest, TerrainClassCoverageManifest,
        TerrainClassManifest, TerrainExtentManifest, TerrainManifest,
        TerrainMaterialExposureClassSummaryManifest, TerrainMaterialExposureSummaryManifest,
        TrajectoryMetadataManifest, ValidationOutputMode, RUN_MANIFEST_SCHEMA_VERSION,
        STOP_STATE_SUMMARY_SCHEMA_VERSION, TERRAIN_MATERIAL_EXPOSURE_SUMMARY_SCHEMA_VERSION,
    },
    probabilistic::{
        MapPackageManifest, NormalizationScope, ProbabilisticMetadataError, ProbabilityMode,
        ScenarioRow, ScenarioTable, SourceZoneMetadata, MAP_PACKAGE_MANIFEST_SCHEMA_VERSION,
    },
    shape::{BlockShapeMetadata, ShapeContactV0Scaffold, PASSIVE_SHAPE_WARNING},
    simulation::{
        simulate_ensemble_parallel_with_contact_parameters,
        simulate_ensemble_with_contact_parameters,
        simulate_one_trajectory_with_terrain_and_contact_parameters, SimulationConfig,
        SimulationError, SimulationResult, StopReason, StopStateProvenance, TerrainConfig,
        TrajectoryRequest, TrajectoryRun, DEFAULT_STOP_SPEED_MPS,
    },
    state::{BodyState, ContactState, ImpactEvent, TrajectorySample},
    stochastic::{ReleasePerturbation, RoughnessModel},
    terrain::{DemGrid, TerrainError},
    Vec3,
};
use arrow_array::{ArrayRef, BooleanArray, Float64Array, RecordBatch, StringArray, UInt64Array};
use arrow_schema::{DataType, Field, Schema};
use parquet::{arrow::ArrowWriter, basic::Compression, file::properties::WriterProperties};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::{
    collections::{BTreeMap, BTreeSet},
    fs::{self, File},
    io::Read,
    path::{Path, PathBuf},
    process::Command,
    sync::Arc,
    time::{Instant, SystemTime, UNIX_EPOCH},
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
const SIGNIFICANT_IMPACT_TERRAIN_CLASS_SEQUENCE_EDGE_LIMIT: usize = 16;
pub const TRAJECTORY_METADATA_SCHEMA_VERSION: &str = "trajectory_metadata_table_v1";
pub const IMPACT_EVENTS_TABLE_SCHEMA_VERSION: &str = "impact_events_table_v1";
const OUTPUT_FILE_WARNING_THRESHOLD: usize = 1_000;
const OUTPUT_FILE_HIGH_WARNING_THRESHOLD: usize = 10_000;

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
    pub release_zone: Option<ReleaseZoneConfig>,
    #[serde(default)]
    pub terrain_classes: Option<TerrainClassConfig>,
    #[serde(default)]
    pub block_shape: Option<BlockShapeConfig>,
    #[serde(default, alias = "probabilistic")]
    pub probabilistic_metadata: Option<ProbabilisticMetadataConfig>,
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
    #[serde(default)]
    pub metadata_path: Option<PathBuf>,
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

#[derive(Debug, Clone, Default, Serialize, Deserialize, PartialEq)]
pub struct ReleaseZoneConfig {
    pub metadata_path: PathBuf,
    #[serde(default)]
    pub generated_release_points_csv: Option<PathBuf>,
}

#[derive(Debug, Clone, Default, Serialize, Deserialize, PartialEq)]
pub struct TerrainClassConfig {
    pub metadata_path: PathBuf,
}

#[derive(Debug, Clone, Default, Serialize, Deserialize, PartialEq)]
pub struct BlockShapeConfig {
    pub metadata_path: PathBuf,
}

#[derive(Debug, Clone, Default, Serialize, Deserialize, PartialEq)]
pub struct ProbabilisticMetadataConfig {
    #[serde(default)]
    pub source_zone_metadata_path: Option<PathBuf>,
    #[serde(default)]
    pub scenario_table_path: Option<PathBuf>,
    #[serde(default)]
    pub map_product_id: Option<String>,
    #[serde(default)]
    pub probability_mode: Option<ProbabilityMode>,
    #[serde(default)]
    pub normalization_scope: Option<NormalizationScope>,
    #[serde(default)]
    pub scenario_id: Option<String>,
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
    #[serde(default)]
    pub ensemble_workers: Option<usize>,
}

impl Default for CaseRandom {
    fn default() -> Self {
        Self {
            seed: None,
            ensemble_size: default_ensemble_size(),
            ensemble_workers: None,
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
    pub manifest_json: Option<PathBuf>,
    #[serde(default)]
    pub validation_output_mode: Option<ValidationOutputMode>,
    #[serde(default)]
    pub trajectory_csv: Option<PathBuf>,
    #[serde(default)]
    pub trajectory_metadata_csv: Option<PathBuf>,
    #[serde(default)]
    pub ensemble_deposition_csv: Option<PathBuf>,
    #[serde(default)]
    pub ensemble_trajectories_dir: Option<PathBuf>,
    #[serde(default)]
    pub ensemble_impact_events_dir: Option<PathBuf>,
    #[serde(default)]
    pub ensemble_impact_events_parquet: Option<PathBuf>,
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
pub struct EnsembleStopStateRow {
    pub release_id: String,
    pub trajectory_id: String,
    pub seed: Option<u64>,
    pub stop_reason: Option<String>,
    pub final_contact_state: Option<String>,
    pub final_speed_mps: Option<f64>,
    pub final_kinetic_j: Option<f64>,
    pub termination_low_velocity: Option<bool>,
    pub termination_max_steps: Option<bool>,
    pub termination_t_max: Option<bool>,
    pub termination_domain_exit: Option<bool>,
    pub termination_terrain_error: Option<bool>,
    pub last_significant_impact_time_s: Option<f64>,
    pub last_significant_impact_x_m: Option<f64>,
    pub last_significant_impact_y_m: Option<f64>,
    pub last_significant_impact_z_m: Option<f64>,
    pub distance_last_significant_impact_to_final_m: Option<f64>,
    #[serde(default)]
    pub significant_impact_count: Option<usize>,
    pub low_energy_contact_count: Option<usize>,
    pub terrain_normal_x: Option<f64>,
    pub terrain_normal_y: Option<f64>,
    pub terrain_normal_z: Option<f64>,
    pub terrain_slope_abs: Option<f64>,
    #[serde(default)]
    pub terrain_material_context_available: bool,
    pub final_terrain_class_id: Option<i32>,
    pub final_terrain_class_name: Option<String>,
    pub final_terrain_class_source: Option<String>,
    pub last_significant_impact_terrain_class_id: Option<i32>,
    pub last_significant_impact_terrain_class_name: Option<String>,
    pub last_significant_impact_terrain_class_source: Option<String>,
    #[serde(default)]
    pub significant_impact_terrain_class_counts: String,
    #[serde(default)]
    pub significant_impact_terrain_class_sequence_head: String,
    #[serde(default)]
    pub significant_impact_terrain_class_sequence_tail: String,
    #[serde(default)]
    pub significant_impact_terrain_class_sequence_truncated: bool,
    #[serde(default)]
    pub significant_impact_terrain_class_unavailable_count: usize,
    #[serde(default)]
    pub terrain_material_instrumentation_gaps: String,
    pub runout_m: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct TerrainMaterialExposureRow {
    pub release_id: String,
    pub trajectory_id: String,
    pub seed: Option<u64>,
    pub terrain_class_id: Option<i32>,
    pub terrain_class_name: Option<String>,
    pub terrain_class_source: String,
    pub terrain_material_context_status: String,
    pub sample_count: usize,
    pub segment_count: usize,
    pub duration_s: f64,
    pub path_length_m: f64,
    pub airborne_sample_count: usize,
    pub impact_sample_count: usize,
    pub sliding_sample_count: usize,
    pub rolling_sample_count: usize,
    pub stopped_sample_count: usize,
    pub contact_sample_count: usize,
    pub contact_duration_s: f64,
    pub contact_path_length_m: f64,
    pub instrumentation_gaps: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ImpactTerrainMaterialRow {
    pub trajectory_id: String,
    pub seed: Option<u64>,
    pub impact_index: usize,
    pub time_s: f64,
    pub x_m: f64,
    pub y_m: f64,
    pub z_m: f64,
    pub significant_impact: bool,
    pub incoming_normal_speed_mps: f64,
    pub terrain_class_id: Option<i32>,
    pub terrain_class_name: Option<String>,
    pub terrain_class_source: String,
    pub terrain_material_context_status: String,
    pub active_parameter_override_count: usize,
    pub active_parameter_override_fields: String,
    pub active_parameter_override_values: String,
    pub instrumentation_gaps: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct TrajectoryMetadataRow {
    pub trajectory_id: String,
    pub release_id: String,
    pub source_zone_id: String,
    pub release_x_m: f64,
    pub release_y_m: f64,
    pub release_z_m: f64,
    pub release_probability: Option<f64>,
    pub block_radius_m: f64,
    pub block_mass_kg: f64,
    pub block_density_kgpm3: Option<f64>,
    pub shape_class: String,
    #[serde(default)]
    pub shape_id: Option<String>,
    #[serde(default)]
    pub shape_type: Option<String>,
    #[serde(default)]
    pub equivalent_radius_m: Option<f64>,
    #[serde(default)]
    pub principal_length_m: Option<f64>,
    #[serde(default)]
    pub principal_width_m: Option<f64>,
    #[serde(default)]
    pub principal_height_m: Option<f64>,
    #[serde(default)]
    pub ixx_kg_m2: Option<f64>,
    #[serde(default)]
    pub iyy_kg_m2: Option<f64>,
    #[serde(default)]
    pub izz_kg_m2: Option<f64>,
    #[serde(default)]
    pub initial_orientation_w: Option<f64>,
    #[serde(default)]
    pub initial_orientation_x: Option<f64>,
    #[serde(default)]
    pub initial_orientation_y: Option<f64>,
    #[serde(default)]
    pub initial_orientation_z: Option<f64>,
    pub scenario_id: String,
    pub sampling_weight: f64,
    pub probability_model: String,
    #[serde(default)]
    pub map_product_id: Option<String>,
    #[serde(default)]
    pub release_cell_id: Option<String>,
    #[serde(default)]
    pub block_scenario_id: Option<String>,
    #[serde(default)]
    pub block_size_class: Option<String>,
    #[serde(default)]
    pub block_shape_class: Option<String>,
    #[serde(default)]
    pub terrain_material_assumption_id: Option<String>,
    #[serde(default)]
    pub model_configuration_id: Option<String>,
    #[serde(default)]
    pub probability_mode: Option<String>,
    #[serde(default)]
    pub normalization_scope: Option<String>,
    #[serde(default)]
    pub annual_frequency_per_year: Option<f64>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct GeneratedReleasePointRecord {
    pub release_id: String,
    pub x_m: f64,
    pub y_m: f64,
    pub z_m: f64,
    pub vx_mps: f64,
    pub vy_mps: f64,
    pub vz_mps: f64,
    pub source_zone_id: String,
    pub seed: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct CaseReport {
    pub case_id: String,
    pub status: CaseStatus,
    #[serde(default)]
    pub execution_status: ExecutionStatus,
    #[serde(default)]
    pub scientific_status: ScientificStatus,
    pub timestamp_unix_s: u64,
    pub model_version: String,
    pub git_hash: Option<String>,
    pub metrics: BTreeMap<String, f64>,
    pub tolerances: BTreeMap<String, f64>,
    pub failures: Vec<String>,
    pub warnings: Vec<String>,
    pub parameters: SimulationConfig,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub stop_state: Option<StopStateProvenance>,
}

#[derive(Debug, Clone, Default)]
struct RuntimeTiming {
    total_wall_seconds: f64,
    terrain_load_seconds: f64,
    release_generation_seconds: f64,
    simulation_seconds: f64,
    output_write_seconds: f64,
    trajectory_count: usize,
    impact_event_count: usize,
}

impl RuntimeTiming {
    fn record_run(&mut self, run: &TrajectoryRun) {
        self.trajectory_count += 1;
        self.impact_event_count += run.impact_events.len();
    }

    fn record_result(&mut self, result: &SimulationResult) {
        self.trajectory_count += 1;
        self.impact_event_count += result.impact_events.len();
    }

    fn record_runs(&mut self, runs: &[TrajectoryRun]) {
        for run in runs {
            self.record_run(run);
        }
    }

    fn to_manifest(&self, outputs: &[OutputManifest]) -> PerformanceManifest {
        PerformanceManifest {
            total_wall_seconds: self.total_wall_seconds.max(0.0),
            terrain_load_seconds: self.terrain_load_seconds.max(0.0),
            release_generation_seconds: self.release_generation_seconds.max(0.0),
            simulation_seconds: self.simulation_seconds.max(0.0),
            output_write_seconds: self.output_write_seconds.max(0.0),
            hazard_layer_seconds: None,
            trajectory_count: self.trajectory_count,
            impact_event_count: self.impact_event_count,
            output_file_count: outputs.iter().map(|output| output.file_count).sum(),
            output_bytes: outputs.iter().map(|output| output.total_bytes).sum(),
        }
    }
}

struct RunManifestContext<'a> {
    case: &'a BenchmarkCase,
    report: &'a CaseReport,
    outputs: Vec<OutputManifest>,
    terrain_source: Option<&'a TerrainSourceMetadata>,
    release_zone: Option<&'a ReleaseZoneManifest>,
    terrain_classes: Option<&'a TerrainClassManifest>,
    shape_metadata: Option<&'a BlockShapeMetadata>,
    trajectory_metadata: Option<TrajectoryMetadataManifest>,
    ensemble_execution: Option<crate::simulation::LocalParallelEnsembleExecution>,
    performance: PerformanceManifest,
    stop_state_summary: Option<StopStateSummaryManifest>,
    terrain_material_exposure_summary: Option<TerrainMaterialExposureSummaryManifest>,
}

#[derive(Debug, Clone)]
struct ProbabilisticMetadataContext {
    map_product_id: String,
    source_zone_metadata_path: PathBuf,
    scenario_table_path: PathBuf,
    source_zone_id: String,
    scenario: ScenarioRow,
    probability_mode: ProbabilityMode,
    normalization_scope: NormalizationScope,
}

#[derive(Debug, Default)]
struct TrajectoryMetadataCollector {
    rows: BTreeMap<String, TrajectoryMetadataRow>,
    probabilistic_metadata: Option<ProbabilisticMetadataContext>,
}

impl TrajectoryMetadataCollector {
    fn with_probabilistic_metadata(
        probabilistic_metadata: Option<ProbabilisticMetadataContext>,
    ) -> Self {
        Self {
            rows: BTreeMap::new(),
            probabilistic_metadata,
        }
    }

    fn insert_run(
        &mut self,
        case: &BenchmarkCase,
        run: &TrajectoryRun,
        release_id: impl Into<String>,
        source_zone_id: impl Into<String>,
        block: &SphereBlock,
        shape_metadata: Option<&BlockShapeMetadata>,
    ) -> Result<(), ValidationError> {
        if let Some(first) = run.samples.first() {
            self.insert_row(trajectory_metadata_row(TrajectoryMetadataRowInput {
                case,
                trajectory_id: &run.summary.trajectory_id,
                release_id: release_id.into(),
                source_zone_id: source_zone_id.into(),
                release_position_m: [first.x_m, first.y_m, first.z_m],
                block,
                shape_metadata,
                probabilistic_metadata: self.probabilistic_metadata.as_ref(),
            })?);
        }
        Ok(())
    }

    fn insert_single_result(
        &mut self,
        case: &BenchmarkCase,
        result: &SimulationResult,
        block: &SphereBlock,
        shape_metadata: Option<&BlockShapeMetadata>,
    ) -> Result<(), ValidationError> {
        if let Some(first) = result.samples.first() {
            self.insert_row(trajectory_metadata_row(TrajectoryMetadataRowInput {
                case,
                trajectory_id: default_single_trajectory_id(),
                release_id: default_single_trajectory_id().to_string(),
                source_zone_id: default_manual_source_zone_id().to_string(),
                release_position_m: [first.x_m, first.y_m, first.z_m],
                block,
                shape_metadata,
                probabilistic_metadata: self.probabilistic_metadata.as_ref(),
            })?);
        }
        Ok(())
    }

    fn insert_row(&mut self, row: TrajectoryMetadataRow) {
        self.rows.entry(row.trajectory_id.clone()).or_insert(row);
    }

    fn rows(&self) -> Vec<TrajectoryMetadataRow> {
        self.rows.values().cloned().collect()
    }
}

struct TrajectoryMetadataRowInput<'a> {
    case: &'a BenchmarkCase,
    trajectory_id: &'a str,
    release_id: String,
    source_zone_id: String,
    release_position_m: [f64; 3],
    block: &'a SphereBlock,
    shape_metadata: Option<&'a BlockShapeMetadata>,
    probabilistic_metadata: Option<&'a ProbabilisticMetadataContext>,
}

// Keep trajectory metadata assembly fallible so malformed shape-sidecar data
// or case/shape mismatches surface as `ValidationError` instead of panicking.
fn trajectory_metadata_row(
    input: TrajectoryMetadataRowInput<'_>,
) -> Result<TrajectoryMetadataRow, ValidationError> {
    let TrajectoryMetadataRowInput {
        case,
        trajectory_id,
        release_id,
        source_zone_id,
        release_position_m,
        block,
        shape_metadata,
        probabilistic_metadata,
    } = input;
    let (
        shape_class,
        shape_id,
        shape_type,
        equivalent_radius_m,
        principal_lengths,
        moments,
        orientation,
        density,
    ) = if let Some(shape) = shape_metadata {
        let moments = shape.computed_principal_moments_kg_m2()?;
        (
            shape.shape_class_or_default(),
            Some(shape.shape_id.clone()),
            Some(shape.shape_type.as_str().to_string()),
            shape_equivalent_radius_m(shape),
            shape_principal_lengths_m(shape),
            Some(moments),
            Some(shape.orientation.initial_quaternion_wxyz),
            shape.mass_properties.density_kgpm3,
        )
    } else {
        (
            "sphere".to_string(),
            None,
            None,
            None,
            None,
            None,
            None,
            sphere_density_kgpm3(block),
        )
    };
    let scenario = probabilistic_metadata.map(|metadata| &metadata.scenario);
    Ok(TrajectoryMetadataRow {
        trajectory_id: trajectory_id.to_string(),
        release_id: release_id.clone(),
        source_zone_id: probabilistic_metadata
            .map(|metadata| metadata.source_zone_id.clone())
            .unwrap_or(source_zone_id),
        release_x_m: release_position_m[0],
        release_y_m: release_position_m[1],
        release_z_m: release_position_m[2],
        release_probability: scenario.and_then(|row| row.release_probability),
        block_radius_m: block.radius_m,
        block_mass_kg: block.mass_kg,
        block_density_kgpm3: density,
        shape_class,
        shape_id,
        shape_type,
        equivalent_radius_m,
        principal_length_m: principal_lengths.map(|values| values[0]),
        principal_width_m: principal_lengths.map(|values| values[1]),
        principal_height_m: principal_lengths.map(|values| values[2]),
        ixx_kg_m2: moments.map(|values| values[0]),
        iyy_kg_m2: moments.map(|values| values[1]),
        izz_kg_m2: moments.map(|values| values[2]),
        initial_orientation_w: orientation.map(|values| values[0]),
        initial_orientation_x: orientation.map(|values| values[1]),
        initial_orientation_y: orientation.map(|values| values[2]),
        initial_orientation_z: orientation.map(|values| values[3]),
        scenario_id: scenario
            .map(|row| row.scenario_id.clone())
            .unwrap_or_else(|| case.case_id.clone()),
        sampling_weight: scenario.map(|row| row.sampling_weight).unwrap_or(1.0),
        probability_model: probabilistic_metadata
            .map(|metadata| legacy_probability_model(metadata.probability_mode).to_string())
            .unwrap_or_else(|| default_probability_model().to_string()),
        map_product_id: probabilistic_metadata.map(|metadata| metadata.map_product_id.clone()),
        release_cell_id: probabilistic_metadata.map(|_| release_id),
        block_scenario_id: scenario.and_then(|row| row.block_scenario_id.clone()),
        block_size_class: scenario.and_then(|row| row.block_size_class.clone()),
        block_shape_class: scenario.and_then(|row| row.block_shape_class.clone()),
        terrain_material_assumption_id: scenario
            .map(|row| row.terrain_material_assumption_id.clone()),
        model_configuration_id: scenario.map(|row| row.model_configuration_id.clone()),
        probability_mode: probabilistic_metadata
            .map(|metadata| probability_mode_text(metadata.probability_mode).to_string()),
        normalization_scope: probabilistic_metadata
            .map(|metadata| normalization_scope_text(metadata.normalization_scope).to_string()),
        annual_frequency_per_year: None,
    })
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum CaseStatus {
    Passed,
    Failed,
    Skipped,
}

#[derive(Debug, Clone, Copy, Default, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum ExecutionStatus {
    #[default]
    Completed,
    Failed,
    Skipped,
}

#[derive(Debug, Clone, Copy, Default, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum ScientificStatus {
    MeetsAcceptanceThresholds,
    FailsAcceptanceThresholds,
    ReportedWithoutAcceptanceThresholds,
    #[default]
    NotEvaluated,
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
    #[error("Arrow error: {0}")]
    Arrow(#[from] arrow_schema::ArrowError),
    #[error("Parquet error: {0}")]
    Parquet(#[from] parquet::errors::ParquetError),
    #[error("simulation error: {0}")]
    Simulation(#[from] SimulationError),
    #[error("terrain error: {0}")]
    Terrain(#[from] TerrainError),
    #[error("geodata metadata error: {0}")]
    Geodata(#[from] GeodataError),
    #[error("shape metadata error: {0}")]
    Shape(#[from] crate::shape::ShapeMetadataError),
    #[error("probabilistic metadata error: {0}")]
    Probabilistic(#[from] ProbabilisticMetadataError),
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
    runner::run_case_file(path)
}

pub fn run_case(case: &BenchmarkCase) -> Result<CaseReport, ValidationError> {
    runner::run_case(case)
}

pub fn write_report(path: impl AsRef<Path>, report: &CaseReport) -> Result<(), ValidationError> {
    runner::write_report(path, report)
}

fn has_acceptance_thresholds(expected: &ExpectedConfig) -> bool {
    !expected.tolerances.is_empty()
        || !expected.minimums.is_empty()
        || !expected.maximums.is_empty()
        || !expected.values.is_empty()
}

fn lacks_acceptance_thresholds(expected: &ExpectedConfig) -> bool {
    !has_acceptance_thresholds(expected)
}

fn terrain_resolution_m(terrain: &CaseTerrain) -> Option<f64> {
    terrain
        .parameters
        .get("cell_size_m")
        .copied()
        .or_else(|| terrain.parameters.get("cellsize").copied())
}

fn load_terrain_source_metadata(
    case: &BenchmarkCase,
) -> Result<Option<TerrainSourceMetadata>, ValidationError> {
    let Some(metadata_path) = &case.terrain.metadata_path else {
        return Ok(None);
    };
    let metadata = TerrainSourceMetadata::from_yaml_file(metadata_path)?;
    if let Some(dem_path) = &case.terrain.path {
        if matches!(
            case.terrain.terrain_type.as_str(),
            "esri_ascii_grid" | "ascii_dem" | "esri_ascii_grid_clamped" | "ascii_dem_clamped"
        ) {
            let dem = DemGrid::from_ascii_grid(dem_path)?;
            metadata.validate_against_dem(&dem)?;
        }
    }
    Ok(Some(metadata))
}

fn load_release_zone_metadata(
    case: &BenchmarkCase,
    terrain_source: Option<&TerrainSourceMetadata>,
) -> Result<Option<ReleaseZoneMetadata>, ValidationError> {
    let Some(release_zone) = &case.release_zone else {
        return Ok(None);
    };
    let metadata = ReleaseZoneMetadata::from_yaml_file(&release_zone.metadata_path)?;
    if let Some(terrain_source) = terrain_source {
        metadata.validate_against_terrain_source(terrain_source)?;
    }
    Ok(Some(metadata))
}

fn load_terrain_class_map(
    case: &BenchmarkCase,
    terrain_source: Option<&TerrainSourceMetadata>,
) -> Result<Option<TerrainClassMap>, ValidationError> {
    let Some(terrain_classes) = &case.terrain_classes else {
        return Ok(None);
    };
    let class_map = TerrainClassMap::from_metadata_file(&terrain_classes.metadata_path)?;
    if let Some(terrain_source) = terrain_source {
        class_map.validate_against_terrain_source(terrain_source)?;
    }
    Ok(Some(class_map))
}

fn annotate_result_terrain_material_context(
    result: &mut SimulationResult,
    class_map: Option<&TerrainClassMap>,
) {
    let SimulationResult {
        samples,
        impact_events,
        stop_state,
        ..
    } = result;
    let final_xy = samples.last().map(|sample| (sample.x_m, sample.y_m));
    if let Some(stop_state) = stop_state.as_mut() {
        annotate_stop_state_terrain_material_context(
            stop_state,
            final_xy,
            impact_events,
            class_map,
        );
    }
}

fn annotate_run_terrain_material_context(
    run: &mut TrajectoryRun,
    class_map: Option<&TerrainClassMap>,
) {
    let TrajectoryRun {
        samples,
        impact_events,
        stop_state,
        ..
    } = run;
    let final_xy = samples.last().map(|sample| (sample.x_m, sample.y_m));
    if let Some(stop_state) = stop_state.as_mut() {
        annotate_stop_state_terrain_material_context(
            stop_state,
            final_xy,
            impact_events,
            class_map,
        );
    }
}

fn annotate_stop_state_terrain_material_context(
    stop_state: &mut StopStateProvenance,
    final_xy: Option<(f64, f64)>,
    impact_events: &[ImpactEvent],
    class_map: Option<&TerrainClassMap>,
) {
    let Some(class_map) = class_map else {
        return;
    };

    stop_state.terrain_material_context_available = false;
    stop_state.final_terrain_class_id = None;
    stop_state.final_terrain_class_name = None;
    stop_state.final_terrain_class_source = None;
    stop_state.last_significant_impact_terrain_class_id = None;
    stop_state.last_significant_impact_terrain_class_name = None;
    stop_state.last_significant_impact_terrain_class_source = None;
    stop_state.significant_impact_terrain_class_counts.clear();
    stop_state
        .significant_impact_terrain_class_sequence_head
        .clear();
    stop_state
        .significant_impact_terrain_class_sequence_tail
        .clear();
    stop_state.significant_impact_terrain_class_sequence_truncated = false;
    stop_state.significant_impact_terrain_class_unavailable_count = 0;
    stop_state.terrain_material_instrumentation_gaps.clear();

    if let Some((x_m, y_m)) = final_xy {
        if let Some((class_id, class_name, source)) = terrain_class_lookup(class_map, x_m, y_m) {
            stop_state.terrain_material_context_available = true;
            stop_state.final_terrain_class_id = Some(class_id);
            stop_state.final_terrain_class_name = Some(class_name);
            stop_state.final_terrain_class_source = Some(source);
        } else {
            stop_state.terrain_material_instrumentation_gaps.push(
                "final position has no terrain/material class (outside class grid or nodata)"
                    .to_string(),
            );
        }
    } else {
        stop_state
            .terrain_material_instrumentation_gaps
            .push("final position is unavailable for terrain/material class lookup".to_string());
    }

    match (
        stop_state.last_significant_impact_x_m,
        stop_state.last_significant_impact_y_m,
    ) {
        (Some(x_m), Some(y_m)) => {
            if let Some((class_id, class_name, source)) = terrain_class_lookup(class_map, x_m, y_m) {
                stop_state.terrain_material_context_available = true;
                stop_state.last_significant_impact_terrain_class_id = Some(class_id);
                stop_state.last_significant_impact_terrain_class_name = Some(class_name);
                stop_state.last_significant_impact_terrain_class_source = Some(source);
            } else {
                stop_state.terrain_material_instrumentation_gaps.push(
                    "last significant impact has no terrain/material class (outside class grid or nodata)"
                        .to_string(),
                );
            }
        }
        _ => stop_state.terrain_material_instrumentation_gaps.push(
            "last significant impact terrain/material class is unavailable because no significant impact reached the explicit threshold"
                .to_string(),
        ),
    }

    let mut significant_impact_sequence = Vec::new();
    for event in impact_events
        .iter()
        .filter(|event| event.incoming_normal_speed_mps >= SIGNIFICANT_IMPACT_MIN_NORMAL_SPEED_MPS)
    {
        if let Some((class_id, class_name, _source)) =
            terrain_class_lookup(class_map, event.x_m, event.y_m)
        {
            stop_state.terrain_material_context_available = true;
            let label = format!("{class_id}:{class_name}");
            *stop_state
                .significant_impact_terrain_class_counts
                .entry(label.clone())
                .or_insert(0) += 1;
            significant_impact_sequence.push(label);
        } else {
            stop_state.significant_impact_terrain_class_unavailable_count += 1;
        }
    }
    if !significant_impact_sequence.is_empty() {
        let sequence_limit = SIGNIFICANT_IMPACT_TERRAIN_CLASS_SEQUENCE_EDGE_LIMIT * 2;
        if significant_impact_sequence.len() <= sequence_limit {
            stop_state.significant_impact_terrain_class_sequence_head = significant_impact_sequence;
        } else {
            stop_state.significant_impact_terrain_class_sequence_head = significant_impact_sequence
                [..SIGNIFICANT_IMPACT_TERRAIN_CLASS_SEQUENCE_EDGE_LIMIT]
                .to_vec();
            stop_state.significant_impact_terrain_class_sequence_tail = significant_impact_sequence
                [significant_impact_sequence.len()
                    - SIGNIFICANT_IMPACT_TERRAIN_CLASS_SEQUENCE_EDGE_LIMIT..]
                .to_vec();
            stop_state.significant_impact_terrain_class_sequence_truncated = true;
        }
    }
    if stop_state.significant_impact_terrain_class_unavailable_count > 0 {
        let gap = format!(
            "{} significant impacts have no terrain/material class (outside class grid or nodata)",
            stop_state.significant_impact_terrain_class_unavailable_count
        );
        stop_state.terrain_material_instrumentation_gaps.push(gap);
    }
}

fn terrain_class_lookup(
    class_map: &TerrainClassMap,
    x_m: f64,
    y_m: f64,
) -> Option<(i32, String, String)> {
    let class_id = class_map.class_id_at(x_m, y_m)?;
    let class = class_map.classes_by_id.get(&class_id)?;
    Some((
        class_id,
        class.name.clone(),
        class_map.metadata.layer_id.clone(),
    ))
}

fn load_block_shape_metadata(
    case: &BenchmarkCase,
) -> Result<Option<BlockShapeMetadata>, ValidationError> {
    let Some(block_shape) = &case.block_shape else {
        if case.parameters.contact_model == ContactModel::ShapeContactV0 {
            return Err(ValidationError::Case(
                "shape_contact_v0 requires block_shape.metadata_path with compatible shape_metadata_v1".to_string(),
            ));
        }
        return Ok(None);
    };
    let metadata = BlockShapeMetadata::from_yaml_file(&block_shape.metadata_path)?;
    let block = case_block(case)?;
    metadata.validate_against_block(&block)?;
    if case.parameters.contact_model == ContactModel::ShapeContactV0 {
        ShapeContactV0Scaffold::from_metadata(&metadata)?;
    }
    Ok(Some(metadata))
}

fn load_probabilistic_metadata_context(
    case: &BenchmarkCase,
    release_zone: Option<&ReleaseZoneMetadata>,
) -> Result<Option<ProbabilisticMetadataContext>, ValidationError> {
    probabilistic::load_probabilistic_metadata_context(case, release_zone)
}

fn terrain_manifest(
    terrain: &CaseTerrain,
    source: Option<&TerrainSourceMetadata>,
) -> TerrainManifest {
    let metadata_path = terrain
        .metadata_path
        .as_ref()
        .map(|path| path.to_string_lossy().to_string());
    let path = terrain
        .path
        .as_ref()
        .map(|path| path.to_string_lossy().to_string());

    if let Some(source) = source {
        return TerrainManifest {
            terrain_type: terrain.terrain_type.clone(),
            path,
            metadata_path,
            crs: Some(source.coordinate_reference_system.horizontal_name.clone()),
            epsg: Some(source.coordinate_reference_system.epsg),
            vertical_datum: Some(source.coordinate_reference_system.vertical_datum.clone()),
            resolution_m: Some(source.raster.resolution_m),
            extent: Some(TerrainExtentManifest {
                xmin: source.extent_lv95_m.xmin,
                ymin: source.extent_lv95_m.ymin,
                xmax: source.extent_lv95_m.xmax,
                ymax: source.extent_lv95_m.ymax,
            }),
            nodata: source.raster.nodata,
            source_dataset: Some(source.source_dataset.clone()),
            source_product: Some(source.source_product.clone()),
            source_url: source.source_url.clone(),
            source_filename: Some(source.source_filename.clone()),
            license: Some(source.license.clone()),
            download_status: Some(source.download_status.clone()),
            preprocessing_status: Some(source.preprocessing.status.clone()),
            raw_sha256: source.preprocessing.raw_sha256.clone(),
            processed_sha256: source.preprocessing.processed_sha256.clone(),
            provenance_notes: source.provenance.notes.clone(),
        };
    }

    TerrainManifest {
        terrain_type: terrain.terrain_type.clone(),
        path,
        metadata_path,
        crs: None,
        epsg: None,
        vertical_datum: None,
        resolution_m: terrain_resolution_m(terrain),
        extent: None,
        nodata: None,
        source_dataset: None,
        source_product: None,
        source_url: None,
        source_filename: None,
        license: None,
        download_status: None,
        preprocessing_status: None,
        raw_sha256: None,
        processed_sha256: None,
        provenance_notes: Vec::new(),
    }
}

// Keep the manifest conversion fallible so runtime validation can report
// missing or inconsistent shape sidecar data as structured diagnostics.
fn shape_metadata_manifest(
    case: &BenchmarkCase,
    metadata: &BlockShapeMetadata,
) -> Result<ShapeMetadataManifest, ValidationError> {
    let moments = metadata.computed_principal_moments_kg_m2()?;
    Ok(ShapeMetadataManifest {
        schema_version: crate::shape::SHAPE_METADATA_SCHEMA_VERSION.to_string(),
        metadata_path: case
            .block_shape
            .as_ref()
            .map(|config| config.metadata_path.to_string_lossy().to_string()),
        shape_id: metadata.shape_id.clone(),
        shape_type: metadata.shape_type.as_str().to_string(),
        shape_class: metadata.shape_class_or_default(),
        active_contact_shape: "sphere".to_string(),
        active_contact_radius_m: case.block.radius.ok_or_else(|| {
            ValidationError::Case(
                "shape metadata manifest requires block.radius to be set".to_string(),
            )
        })?,
        mass_kg: metadata.mass_properties.mass_kg,
        density_kgpm3: metadata.mass_properties.density_kgpm3,
        equivalent_radius_m: shape_equivalent_radius_m(metadata),
        principal_lengths_m: shape_principal_lengths_m(metadata),
        principal_moments_kg_m2: moments,
        orientation_initialization_mode: metadata.orientation.initialization_mode.clone(),
        initial_quaternion_wxyz: metadata.orientation.initial_quaternion_wxyz,
        source_dataset: metadata.provenance.source_dataset.clone(),
        source_record_id: metadata.provenance.source_record_id.clone(),
        source_url_or_doi: metadata.provenance.source_url_or_doi.clone(),
        license: metadata.provenance.license.clone(),
        provenance_notes: metadata.provenance.notes.clone(),
        warnings: vec![PASSIVE_SHAPE_WARNING.to_string()],
    })
}

fn shape_equivalent_radius_m(metadata: &BlockShapeMetadata) -> Option<f64> {
    match metadata.shape_type {
        crate::shape::BlockShapeType::Sphere => metadata.dimensions_m.radius_m,
        _ => metadata.dimensions_m.equivalent_radius_m,
    }
}

fn shape_principal_lengths_m(metadata: &BlockShapeMetadata) -> Option<[f64; 3]> {
    metadata
        .dimensions_m
        .principal_lengths_m
        .or(metadata.dimensions_m.side_lengths_m)
        .or_else(|| {
            metadata
                .dimensions_m
                .semi_axes_m
                .map(|axes| [2.0 * axes[0], 2.0 * axes[1], 2.0 * axes[2]])
        })
}

fn release_zone_manifest(
    config: Option<&ReleaseZoneConfig>,
    source: &ReleaseZoneMetadata,
    generated_release_points: usize,
) -> ReleaseZoneManifest {
    let extent = source.extent();
    ReleaseZoneManifest {
        zone_id: source.zone_id.clone(),
        metadata_path: config.map(|config| config.metadata_path.to_string_lossy().to_string()),
        crs: source.coordinate_reference_system.horizontal_name.clone(),
        epsg: source.coordinate_reference_system.epsg,
        vertical_datum: source.coordinate_reference_system.vertical_datum.clone(),
        sampling_mode: source.sampling.mode.clone(),
        seed: source.sampling.seed,
        requested_release_points: source.sampling.count,
        generated_release_points,
        extent: TerrainExtentManifest {
            xmin: extent.xmin,
            ymin: extent.ymin,
            xmax: extent.xmax,
            ymax: extent.ymax,
        },
        area_m2: source.area_m2(),
        source_dataset: source.source_dataset.clone(),
        source_url: source.source_url.clone(),
        license: source.license.clone(),
        provenance_notes: source.provenance.notes.clone(),
    }
}

fn terrain_class_manifest(
    config: Option<&TerrainClassConfig>,
    class_map: &TerrainClassMap,
) -> Result<TerrainClassManifest, ValidationError> {
    let metadata = &class_map.metadata;
    let metadata_path = config.map(|config| config.metadata_path.to_string_lossy().to_string());
    let metadata_sha256 = config
        .map(|config| sha256_file(&config.metadata_path))
        .transpose()?;
    let class_grid_sha256 = config
        .map(|config| resolved_terrain_class_grid_path(&config.metadata_path, metadata))
        .map(|path| sha256_file(&path))
        .transpose()?;
    Ok(TerrainClassManifest {
        schema_version: "terrain_class_manifest_v1".to_string(),
        metadata_schema_version: Some(metadata.schema_version),
        layer_id: metadata.layer_id.clone(),
        metadata_path,
        metadata_sha256,
        class_grid_path: metadata.class_grid_path.to_string_lossy().to_string(),
        class_grid_sha256,
        crs: metadata.coordinate_reference_system.horizontal_name.clone(),
        epsg: metadata.coordinate_reference_system.epsg,
        vertical_datum: metadata.coordinate_reference_system.vertical_datum.clone(),
        resolution_m: metadata.raster.resolution_m,
        extent: TerrainExtentManifest {
            xmin: metadata.extent_lv95_m.xmin,
            ymin: metadata.extent_lv95_m.ymin,
            xmax: metadata.extent_lv95_m.xmax,
            ymax: metadata.extent_lv95_m.ymax,
        },
        nodata: metadata.raster.nodata,
        source_dataset: metadata.source_dataset.clone(),
        source_url: metadata.source_url.clone(),
        license: metadata.license.clone(),
        class_coverage: class_map
            .coverage()
            .into_iter()
            .map(|coverage| {
                let active_parameter_override_fields = class_map
                    .classes_by_id
                    .get(&coverage.class_id)
                    .map(|class| class.parameter_overrides.active_field_names())
                    .unwrap_or_default();
                TerrainClassCoverageManifest {
                    class_id: coverage.class_id,
                    name: coverage.name,
                    cell_count: coverage.cell_count,
                    coverage_fraction: coverage.coverage_fraction,
                    active_parameter_override_count: active_parameter_override_fields.len(),
                    active_parameter_override_fields,
                }
            })
            .collect(),
        provenance_notes: metadata.provenance.notes.clone(),
    })
}

fn resolved_terrain_class_grid_path(
    metadata_path: &Path,
    metadata: &crate::geodata::TerrainClassMetadata,
) -> PathBuf {
    if metadata.class_grid_path.is_absolute() {
        metadata.class_grid_path.clone()
    } else {
        metadata_path
            .parent()
            .unwrap_or_else(|| Path::new(""))
            .join(&metadata.class_grid_path)
    }
}

fn file_output_manifest(
    path: impl AsRef<Path>,
    kind: &str,
    format: &str,
    row_count: Option<usize>,
    skipped_empty_files: Option<usize>,
) -> Result<OutputManifest, ValidationError> {
    Ok(OutputManifest {
        kind: kind.to_string(),
        format: format.to_string(),
        path: path.as_ref().to_string_lossy().to_string(),
        file_count: 1,
        total_bytes: fs::metadata(path.as_ref())?.len(),
        sha256: Some(sha256_file(path.as_ref())?),
        schema_version: None,
        row_count,
        skipped_empty_files,
        compression: None,
        row_group_count: None,
    })
}

fn validation_output_mode_is_summary_only(case: &BenchmarkCase) -> bool {
    case.outputs.validation_output_mode == Some(ValidationOutputMode::SummaryOnly)
}

fn validation_output_mode_is_rebuildable_reduced_output(case: &BenchmarkCase) -> bool {
    case.outputs.validation_output_mode == Some(ValidationOutputMode::RebuildableReducedOutput)
}

fn validation_output_mode_writes_builder_facing_outputs(case: &BenchmarkCase) -> bool {
    validation_output_mode_is_rebuildable_reduced_output(case)
        || !validation_output_mode_is_summary_only(case)
}

fn validation_output_mode_writes_debug_outputs(case: &BenchmarkCase) -> bool {
    !validation_output_mode_is_summary_only(case)
        && !validation_output_mode_is_rebuildable_reduced_output(case)
}

fn sha256_file(path: &Path) -> Result<String, ValidationError> {
    let mut file = File::open(path)?;
    let mut digest = Sha256::new();
    let mut buffer = [0_u8; 64 * 1024];
    loop {
        let read = file.read(&mut buffer)?;
        if read == 0 {
            break;
        }
        digest.update(&buffer[..read]);
    }
    Ok(format!("{:x}", digest.finalize()))
}

fn warn_large_debug_outputs(
    case: &BenchmarkCase,
    expected_files: usize,
    warnings: &mut Vec<String>,
) {
    if !validation_output_mode_writes_debug_outputs(case) {
        return;
    }
    if expected_files < OUTPUT_FILE_WARNING_THRESHOLD {
        return;
    }
    let mut configured_outputs = Vec::new();
    if case.outputs.ensemble_trajectories_dir.is_some() {
        configured_outputs.push("ensemble_trajectories_dir");
    }
    if case.outputs.ensemble_impact_events_dir.is_some() {
        configured_outputs.push("ensemble_impact_events_dir");
    }
    if configured_outputs.is_empty() {
        return;
    }
    let severity = if expected_files >= OUTPUT_FILE_HIGH_WARNING_THRESHOLD {
        "high"
    } else {
        "medium"
    };
    warnings.push(format!(
        "{severity}-scale debug output warning: configured {} may create up to {expected_files} per-trajectory CSV files; use these outputs for inspection, not production-scale hazard generation",
        configured_outputs.join(" and ")
    ));
}

fn case_block(case: &BenchmarkCase) -> Result<SphereBlock, ValidationError> {
    let mass_kg = case
        .block
        .mass
        .ok_or_else(|| ValidationError::Case("block.mass is required".to_string()))?;
    let radius_m = case
        .block
        .radius
        .ok_or_else(|| ValidationError::Case("block.radius is required".to_string()))?;
    Ok(SphereBlock::new(radius_m, mass_kg))
}

fn shape_metadata_for_block<'a>(
    shape_metadata: Option<&'a BlockShapeMetadata>,
    block: &SphereBlock,
) -> Option<&'a BlockShapeMetadata> {
    shape_metadata.filter(|metadata| metadata.validate_against_block(block).is_ok())
}

fn build_simulation_config(case: &BenchmarkCase) -> Result<SimulationConfig, ValidationError> {
    let block = case_block(case)?;
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
        block,
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
    case: &'a BenchmarkCase,
    samples: &'a [TrajectorySample],
    impact_events: &'a [ImpactEvent],
    first: &'a TrajectorySample,
    last: &'a TrajectorySample,
    terrain: &'a dyn crate::terrain::Terrain,
    block: &'a SphereBlock,
    observations: &'a [DepositionPoint],
    expected: &'a ExpectedConfig,
    warnings: &'a mut Vec<String>,
}

fn compute_metrics(context: MetricContext<'_>) -> Result<BTreeMap<String, f64>, ValidationError> {
    let case = context.case;
    let samples = context.samples;
    let impact_events = context.impact_events;
    let first = context.first;
    let last = context.last;
    let terrain = context.terrain;
    let block = context.block;
    let observations = context.observations;
    let expected = context.expected;
    let warnings = context.warnings;
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
    let max_bounce_height = max_bounce_height(samples, terrain, block.radius_m)?;
    let rebound_height = rebound_height_after_first_impact(samples, terrain, block.radius_m)?;
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

    if observations.is_empty() {
        if case
            .observations
            .as_ref()
            .and_then(|config| config.deposition_points_csv.as_ref())
            .is_some()
        {
            warnings.push(
                "observed deposition metrics were omitted because deposition_points_csv contained no rows"
                    .to_string(),
            );
        }
    } else if let Some(observed) = observations.first() {
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

    Ok(metrics)
}

struct EnsembleMetricContext<'a> {
    case: &'a BenchmarkCase,
    contact_parameters: Option<&'a dyn ContactParameterProvider>,
    terrain_class_map: Option<&'a TerrainClassMap>,
    metrics: &'a mut BTreeMap<String, f64>,
    warnings: &'a mut Vec<String>,
    output_entries: &'a mut Vec<OutputManifest>,
    timing: &'a mut RuntimeTiming,
    trajectory_metadata: &'a mut TrajectoryMetadataCollector,
    shape_metadata: Option<&'a BlockShapeMetadata>,
    stop_state_summary: &'a mut Option<StopStateSummaryManifest>,
    terrain_material_exposure_summary: &'a mut Option<TerrainMaterialExposureSummaryManifest>,
    ensemble_execution: &'a mut Option<crate::simulation::LocalParallelEnsembleExecution>,
}

fn compute_ensemble_metrics(context: EnsembleMetricContext<'_>) -> Result<(), ValidationError> {
    let EnsembleMetricContext {
        case,
        contact_parameters,
        terrain_class_map,
        metrics,
        warnings,
        output_entries,
        timing,
        trajectory_metadata,
        shape_metadata,
        stop_state_summary: _stop_state_summary,
        terrain_material_exposure_summary: _terrain_material_exposure_summary,
        ensemble_execution,
    } = context;
    let ensemble_size = case.random.ensemble_size.max(1);
    if case.random.seed.is_some() {
        let config_a = build_simulation_config(case)?;
        let config_b = build_simulation_config(case)?;
        let terrain = config_a.terrain.build()?;
        let simulation_started = Instant::now();
        let a = config_a
            .run_with_terrain_and_contact_parameters(terrain.as_ref(), contact_parameters)?;
        let b = config_b
            .run_with_terrain_and_contact_parameters(terrain.as_ref(), contact_parameters)?;
        timing.simulation_seconds += simulation_started.elapsed().as_secs_f64();
        timing.record_result(&a);
        timing.record_result(&b);
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
    let simulation_started = Instant::now();
    let ensemble = if let Some(worker_count) = case.random.ensemble_workers {
        let result = simulate_ensemble_parallel_with_contact_parameters(
            &ensemble_config,
            case.case_id.clone(),
            global_seed,
            &trajectory_ids,
            worker_count,
            contact_parameters,
        )?;
        *ensemble_execution = Some(result.execution);
        result.ensemble
    } else {
        simulate_ensemble_with_contact_parameters(
            &ensemble_config,
            case.case_id.clone(),
            global_seed,
            &trajectory_ids,
            contact_parameters,
        )?
    };
    timing.simulation_seconds += simulation_started.elapsed().as_secs_f64();
    timing.record_runs(&ensemble.trajectories);
    for run in &ensemble.trajectories {
        trajectory_metadata.insert_run(
            case,
            run,
            run.summary.trajectory_id.clone(),
            default_manual_source_zone_id(),
            &ensemble_config.block,
            shape_metadata,
        )?;
    }
    if case.observations.is_none() {
        warn_large_debug_outputs(case, ensemble_size, warnings);
        if validation_output_mode_writes_debug_outputs(case) {
            if let Some(dir) = &case.outputs.ensemble_trajectories_dir {
                let output_started = Instant::now();
                output_entries.push(write_ensemble_trajectory_dir(dir, &ensemble.trajectories)?);
                timing.output_write_seconds += output_started.elapsed().as_secs_f64();
            }
            if let Some(dir) = &case.outputs.ensemble_impact_events_dir {
                let output_started = Instant::now();
                output_entries.push(write_ensemble_impact_events_dir(
                    dir,
                    &ensemble.trajectories,
                )?);
                if let Some(class_map) = terrain_class_map {
                    let terrain_material_dir = impact_terrain_material_sidecar_dir(dir);
                    output_entries.push(write_ensemble_impact_terrain_material_dir(
                        &terrain_material_dir,
                        &ensemble.trajectories,
                        class_map,
                    )?);
                }
                timing.output_write_seconds += output_started.elapsed().as_secs_f64();
            }
            if let Some(path) = &case.outputs.ensemble_impact_events_parquet {
                let output_started = Instant::now();
                output_entries.push(write_ensemble_impact_events_parquet(
                    path,
                    &ensemble.trajectories,
                )?);
                if case.outputs.ensemble_impact_events_dir.is_none() {
                    if let Some(class_map) = terrain_class_map {
                        let terrain_material_dir =
                            impact_terrain_material_sidecar_dir_for_parquet_path(path);
                        output_entries.push(write_ensemble_impact_terrain_material_dir(
                            &terrain_material_dir,
                            &ensemble.trajectories,
                            class_map,
                        )?);
                    }
                }
                timing.output_write_seconds += output_started.elapsed().as_secs_f64();
            }
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
        let simulation_started = Instant::now();
        let alternate = simulate_ensemble_with_contact_parameters(
            &ensemble_config,
            case.case_id.clone(),
            seed.wrapping_add(1),
            &trajectory_ids,
            contact_parameters,
        )?;
        timing.simulation_seconds += simulation_started.elapsed().as_secs_f64();
        timing.record_runs(&alternate.trajectories);
        metrics.insert(
            "different_seed_ensemble_runout_delta_m".to_string(),
            max_runout_delta(&ensemble, &alternate),
        );
    }
    Ok(())
}

struct ValidationEnsembleContext<'a> {
    case: &'a BenchmarkCase,
    base_config: &'a SimulationConfig,
    contact_parameters: Option<&'a dyn ContactParameterProvider>,
    terrain_class_map: Option<&'a TerrainClassMap>,
    observations: &'a ObservationData,
    metrics: &'a mut BTreeMap<String, f64>,
    warnings: &'a mut Vec<String>,
    output_entries: &'a mut Vec<OutputManifest>,
    timing: &'a mut RuntimeTiming,
    trajectory_metadata: &'a mut TrajectoryMetadataCollector,
    shape_metadata: Option<&'a BlockShapeMetadata>,
    stop_state_summary: &'a mut Option<StopStateSummaryManifest>,
    terrain_material_exposure_summary: &'a mut Option<TerrainMaterialExposureSummaryManifest>,
}

fn compute_validation_ensemble_metrics(
    context: ValidationEnsembleContext<'_>,
) -> Result<(), ValidationError> {
    let ValidationEnsembleContext {
        case,
        base_config,
        contact_parameters,
        terrain_class_map,
        observations,
        metrics,
        warnings,
        output_entries,
        timing,
        trajectory_metadata,
        shape_metadata,
        stop_state_summary,
        terrain_material_exposure_summary,
    } = context;
    if observations.release_points.is_empty() {
        if case
            .observations
            .as_ref()
            .and_then(|config| config.release_points_csv.as_ref())
            .is_some()
        {
            warnings.push(
                "validation ensemble metrics were omitted because release_points_csv contained no rows"
                    .to_string(),
            );
        }
        return Ok(());
    }

    let ensemble_size = case.random.ensemble_size.max(1);
    let expected_debug_files = observations.release_points.len() * ensemble_size;
    warn_large_debug_outputs(case, expected_debug_files, warnings);
    let global_seed = case.random.seed.unwrap_or(0);
    let terrain = base_config.terrain.build()?;
    let mut runs = Vec::with_capacity(observations.release_points.len() * ensemble_size);
    let mut deposition_rows = Vec::with_capacity(observations.release_points.len() * ensemble_size);
    let mut stop_state_rows = Vec::with_capacity(observations.release_points.len() * ensemble_size);
    let mut exposure_rows = Vec::new();

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
            let simulation_started = Instant::now();
            let mut run = simulate_one_trajectory_with_terrain_and_contact_parameters(
                &release_config,
                request,
                terrain.as_ref(),
                contact_parameters,
            )?;
            annotate_run_terrain_material_context(&mut run, terrain_class_map);
            timing.simulation_seconds += simulation_started.elapsed().as_secs_f64();
            timing.record_run(&run);
            deposition_rows.push(ensemble_deposition_row(&release.trajectory_id, &run));
            stop_state_rows.push(ensemble_stop_state_row(&release.trajectory_id, &run));
            if let Some(class_map) = terrain_class_map {
                exposure_rows.extend(terrain_material_exposure_rows(
                    &release.trajectory_id,
                    &run,
                    class_map,
                ));
            }
            trajectory_metadata.insert_run(
                case,
                &run,
                release.trajectory_id.clone(),
                default_observed_source_zone_id(),
                &release_config.block,
                shape_metadata_for_block(shape_metadata, &release_config.block),
            )?;
            runs.push(run);
        }
    }

    if let Some(path) = &case.outputs.ensemble_deposition_csv {
        let output_started = Instant::now();
        write_ensemble_deposition_csv(path, &deposition_rows)?;
        let stop_state_path = stop_state_sidecar_path(path);
        let stop_state_output = write_ensemble_stop_state_csv(&stop_state_path, &stop_state_rows)?;
        *stop_state_summary = Some(stop_state_summary_manifest(
            Some(&stop_state_path),
            &stop_state_rows,
            warnings,
        ));
        timing.output_write_seconds += output_started.elapsed().as_secs_f64();
        output_entries.push(file_output_manifest(
            path,
            "ensemble_deposition",
            "csv",
            Some(deposition_rows.len()),
            None,
        )?);
        output_entries.push(stop_state_output);
        if terrain_class_map.is_some() {
            let exposure_path = terrain_material_exposure_sidecar_path(path);
            let exposure_output = write_terrain_material_exposure_csv(
                &exposure_path,
                &exposure_rows,
                "ensemble_terrain_material_exposure",
            )?;
            *terrain_material_exposure_summary = Some(terrain_material_exposure_summary_manifest(
                Some(&exposure_path),
                &exposure_rows,
            ));
            output_entries.push(exposure_output);
        }
    }
    if validation_output_mode_writes_debug_outputs(case) {
        if let Some(dir) = &case.outputs.ensemble_trajectories_dir {
            let output_started = Instant::now();
            output_entries.push(write_ensemble_trajectory_dir(dir, &runs)?);
            timing.output_write_seconds += output_started.elapsed().as_secs_f64();
        }
        if let Some(dir) = &case.outputs.ensemble_impact_events_dir {
            let output_started = Instant::now();
            output_entries.push(write_ensemble_impact_events_dir(dir, &runs)?);
            if let Some(class_map) = terrain_class_map {
                let terrain_material_dir = impact_terrain_material_sidecar_dir(dir);
                output_entries.push(write_ensemble_impact_terrain_material_dir(
                    &terrain_material_dir,
                    &runs,
                    class_map,
                )?);
            }
            timing.output_write_seconds += output_started.elapsed().as_secs_f64();
        }
        if let Some(path) = &case.outputs.ensemble_impact_events_parquet {
            let output_started = Instant::now();
            output_entries.push(write_ensemble_impact_events_parquet(path, &runs)?);
            if case.outputs.ensemble_impact_events_dir.is_none() {
                if let Some(class_map) = terrain_class_map {
                    let terrain_material_dir =
                        impact_terrain_material_sidecar_dir_for_parquet_path(path);
                    output_entries.push(write_ensemble_impact_terrain_material_dir(
                        &terrain_material_dir,
                        &runs,
                        class_map,
                    )?);
                }
            }
            timing.output_write_seconds += output_started.elapsed().as_secs_f64();
        }
    }

    compute_deposition_cloud_metrics(
        &runs,
        observations,
        case.observations
            .as_ref()
            .and_then(|config| config.deposition_points_csv.as_ref())
            .is_some(),
        metrics,
        warnings,
    );
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

struct ReleaseZoneMetricContext<'a> {
    case: &'a BenchmarkCase,
    base_config: &'a SimulationConfig,
    contact_parameters: Option<&'a dyn ContactParameterProvider>,
    terrain_class_map: Option<&'a TerrainClassMap>,
    release_zone: &'a ReleaseZoneMetadata,
    observations: &'a ObservationData,
    metrics: &'a mut BTreeMap<String, f64>,
    warnings: &'a mut Vec<String>,
    output_entries: &'a mut Vec<OutputManifest>,
    timing: &'a mut RuntimeTiming,
    trajectory_metadata: &'a mut TrajectoryMetadataCollector,
    shape_metadata: Option<&'a BlockShapeMetadata>,
    stop_state_summary: &'a mut Option<StopStateSummaryManifest>,
    terrain_material_exposure_summary: &'a mut Option<TerrainMaterialExposureSummaryManifest>,
}

fn compute_release_zone_metrics(
    context: ReleaseZoneMetricContext<'_>,
) -> Result<Option<ReleaseZoneManifest>, ValidationError> {
    let ReleaseZoneMetricContext {
        case,
        base_config,
        contact_parameters,
        terrain_class_map,
        release_zone,
        observations,
        metrics,
        warnings,
        output_entries,
        timing,
        trajectory_metadata,
        shape_metadata,
        stop_state_summary,
        terrain_material_exposure_summary,
    } = context;
    let Some(release_zone_config) = &case.release_zone else {
        return Ok(None);
    };
    let release_started = Instant::now();
    let release_points = release_zone.sample_points()?;
    timing.release_generation_seconds += release_started.elapsed().as_secs_f64();
    warn_large_debug_outputs(case, release_points.len(), warnings);
    let terrain_started = Instant::now();
    let terrain = base_config.terrain.build()?;
    timing.terrain_load_seconds += terrain_started.elapsed().as_secs_f64();
    let mut runs = Vec::with_capacity(release_points.len());
    let mut deposition_rows = Vec::with_capacity(release_points.len());
    let mut stop_state_rows = Vec::with_capacity(release_points.len());
    let mut exposure_rows = Vec::new();
    let mut generated_records = Vec::with_capacity(release_points.len());

    for point in &release_points {
        let z_m = terrain.try_height(point.x_m, point.y_m)?
            + base_config.block.radius_m
            + point.z_offset_m;
        generated_records.push(GeneratedReleasePointRecord {
            release_id: point.release_id.clone(),
            x_m: point.x_m,
            y_m: point.y_m,
            z_m,
            vx_mps: point.vx_mps,
            vy_mps: point.vy_mps,
            vz_mps: point.vz_mps,
            source_zone_id: release_zone.zone_id.clone(),
            seed: release_zone.sampling.seed,
        });

        let mut release_config = base_config.clone();
        release_config.initial_position_m = [point.x_m, point.y_m, z_m];
        release_config.initial_velocity_mps = [point.vx_mps, point.vy_mps, point.vz_mps];
        release_config.random_seed = None;
        let request = TrajectoryRequest::from_global_seed(
            release_zone.sampling.seed,
            case.case_id.clone(),
            point.release_id.clone(),
        );
        let simulation_started = Instant::now();
        let mut run = simulate_one_trajectory_with_terrain_and_contact_parameters(
            &release_config,
            request,
            terrain.as_ref(),
            contact_parameters,
        )?;
        annotate_run_terrain_material_context(&mut run, terrain_class_map);
        timing.simulation_seconds += simulation_started.elapsed().as_secs_f64();
        timing.record_run(&run);
        deposition_rows.push(ensemble_deposition_row(&point.release_id, &run));
        stop_state_rows.push(ensemble_stop_state_row(&point.release_id, &run));
        if let Some(class_map) = terrain_class_map {
            exposure_rows.extend(terrain_material_exposure_rows(
                &point.release_id,
                &run,
                class_map,
            ));
        }
        trajectory_metadata.insert_run(
            case,
            &run,
            point.release_id.clone(),
            release_zone.zone_id.clone(),
            &release_config.block,
            shape_metadata,
        )?;
        runs.push(run);
    }

    if let Some(path) = &release_zone_config.generated_release_points_csv {
        let output_started = Instant::now();
        write_generated_release_points_csv(path, &generated_records)?;
        timing.output_write_seconds += output_started.elapsed().as_secs_f64();
        output_entries.push(file_output_manifest(
            path,
            "generated_release_points",
            "csv",
            Some(generated_records.len()),
            None,
        )?);
    }
    if let Some(path) = &case.outputs.ensemble_deposition_csv {
        let output_started = Instant::now();
        write_ensemble_deposition_csv(path, &deposition_rows)?;
        let stop_state_path = stop_state_sidecar_path(path);
        let stop_state_output = write_ensemble_stop_state_csv(&stop_state_path, &stop_state_rows)?;
        *stop_state_summary = Some(stop_state_summary_manifest(
            Some(&stop_state_path),
            &stop_state_rows,
            warnings,
        ));
        timing.output_write_seconds += output_started.elapsed().as_secs_f64();
        output_entries.push(file_output_manifest(
            path,
            "release_zone_deposition",
            "csv",
            Some(deposition_rows.len()),
            None,
        )?);
        output_entries.push(stop_state_output);
        if terrain_class_map.is_some() {
            let exposure_path = terrain_material_exposure_sidecar_path(path);
            let exposure_output = write_terrain_material_exposure_csv(
                &exposure_path,
                &exposure_rows,
                "release_zone_terrain_material_exposure",
            )?;
            *terrain_material_exposure_summary = Some(terrain_material_exposure_summary_manifest(
                Some(&exposure_path),
                &exposure_rows,
            ));
            output_entries.push(exposure_output);
        }
    }
    if validation_output_mode_writes_debug_outputs(case) {
        if let Some(dir) = &case.outputs.ensemble_trajectories_dir {
            let output_started = Instant::now();
            output_entries.push(write_ensemble_trajectory_dir(dir, &runs)?);
            timing.output_write_seconds += output_started.elapsed().as_secs_f64();
        }
        if let Some(dir) = &case.outputs.ensemble_impact_events_dir {
            let output_started = Instant::now();
            output_entries.push(write_ensemble_impact_events_dir(dir, &runs)?);
            if let Some(class_map) = terrain_class_map {
                let terrain_material_dir = impact_terrain_material_sidecar_dir(dir);
                output_entries.push(write_ensemble_impact_terrain_material_dir(
                    &terrain_material_dir,
                    &runs,
                    class_map,
                )?);
            }
            timing.output_write_seconds += output_started.elapsed().as_secs_f64();
        }
        if let Some(path) = &case.outputs.ensemble_impact_events_parquet {
            let output_started = Instant::now();
            output_entries.push(write_ensemble_impact_events_parquet(path, &runs)?);
            if case.outputs.ensemble_impact_events_dir.is_none() {
                if let Some(class_map) = terrain_class_map {
                    let terrain_material_dir =
                        impact_terrain_material_sidecar_dir_for_parquet_path(path);
                    output_entries.push(write_ensemble_impact_terrain_material_dir(
                        &terrain_material_dir,
                        &runs,
                        class_map,
                    )?);
                }
            }
            timing.output_write_seconds += output_started.elapsed().as_secs_f64();
        }
    }

    let mut runouts = runs
        .iter()
        .map(|run| run.summary.runout_m)
        .collect::<Vec<_>>();
    runouts.sort_by(f64::total_cmp);
    metrics.insert(
        "release_zone_point_count".to_string(),
        release_points.len() as f64,
    );
    metrics.insert(
        "release_zone_extent_area_m2".to_string(),
        release_zone.area_m2(),
    );
    metrics.insert("release_zone_mean_runout_m".to_string(), mean(&runouts));
    metrics.insert(
        "release_zone_max_runout_m".to_string(),
        runouts.last().copied().unwrap_or(0.0),
    );
    compute_deposition_cloud_metrics(
        &runs,
        observations,
        case.observations
            .as_ref()
            .and_then(|config| config.deposition_points_csv.as_ref())
            .is_some(),
        metrics,
        warnings,
    );
    Ok(Some(release_zone_manifest(
        Some(release_zone_config),
        release_zone,
        release_points.len(),
    )))
}

fn compute_observed_trajectory_metrics(
    case: &BenchmarkCase,
    base_config: &SimulationConfig,
    contact_parameters: Option<&dyn ContactParameterProvider>,
    observations: &ObservationData,
    metrics: &mut BTreeMap<String, f64>,
    warnings: &mut Vec<String>,
) -> Result<(), ValidationError> {
    if observations.trajectory_samples.is_empty() {
        if case
            .observations
            .as_ref()
            .and_then(|config| config.trajectory_csv.as_ref())
            .is_some()
        {
            warnings.push(
                "observed trajectory metrics were omitted because trajectory_csv contained no rows"
                    .to_string(),
            );
        }
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
        let run = simulate_one_trajectory_with_terrain_and_contact_parameters(
            &config,
            request,
            terrain.as_ref(),
            contact_parameters,
        )?;
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
            )?);
        }
        observed_jump_envelope = observed_jump_envelope.max(observed_max_jump);

        let simulated_max_jump =
            max_bounce_height(&run.samples, terrain.as_ref(), config.block.radius_m)?;
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
    contact_parameters: Option<&dyn ContactParameterProvider>,
    observations: &ObservationData,
    metrics: &mut BTreeMap<String, f64>,
    warnings: &mut Vec<String>,
) -> Result<(), ValidationError> {
    if observations.contact_events.is_empty() {
        if case
            .observations
            .as_ref()
            .and_then(|config| config.contact_events_csv.as_ref())
            .is_some()
        {
            warnings.push(
                "observed contact metrics were omitted because contact_events_csv contained no rows"
                    .to_string(),
            );
        }
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
        let run = simulate_one_trajectory_with_terrain_and_contact_parameters(
            &config,
            request,
            terrain.as_ref(),
            contact_parameters,
        )?;
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

fn ensemble_stop_state_row(release_id: &str, run: &TrajectoryRun) -> EnsembleStopStateRow {
    let stop_state = run.stop_state.as_ref();
    EnsembleStopStateRow {
        release_id: release_id.to_string(),
        trajectory_id: run.summary.trajectory_id.clone(),
        seed: run.summary.seed,
        stop_reason: stop_state.map(|state| stop_reason_text(&state.stop_reason).to_string()),
        final_contact_state: stop_state
            .map(|state| contact_state_csv(state.final_contact_state).to_string()),
        final_speed_mps: stop_state.map(|state| state.final_speed_mps),
        final_kinetic_j: stop_state.map(|state| state.final_kinetic_j),
        termination_low_velocity: stop_state.map(|state| state.termination_flags.low_velocity),
        termination_max_steps: stop_state.map(|state| state.termination_flags.max_steps),
        termination_t_max: stop_state.map(|state| state.termination_flags.t_max),
        termination_domain_exit: stop_state.map(|state| state.termination_flags.domain_exit),
        termination_terrain_error: stop_state.map(|state| state.termination_flags.terrain_error),
        last_significant_impact_time_s: stop_state
            .and_then(|state| state.last_significant_impact_time_s),
        last_significant_impact_x_m: stop_state.and_then(|state| state.last_significant_impact_x_m),
        last_significant_impact_y_m: stop_state.and_then(|state| state.last_significant_impact_y_m),
        last_significant_impact_z_m: stop_state.and_then(|state| state.last_significant_impact_z_m),
        distance_last_significant_impact_to_final_m: stop_state
            .and_then(|state| state.distance_last_significant_impact_to_final_m),
        significant_impact_count: stop_state.map(|state| state.significant_impact_count),
        low_energy_contact_count: stop_state.map(|state| state.low_energy_contact_count),
        terrain_normal_x: stop_state.and_then(|state| state.terrain_normal_x),
        terrain_normal_y: stop_state.and_then(|state| state.terrain_normal_y),
        terrain_normal_z: stop_state.and_then(|state| state.terrain_normal_z),
        terrain_slope_abs: stop_state.and_then(|state| state.terrain_slope_abs),
        terrain_material_context_available: stop_state
            .map(|state| state.terrain_material_context_available)
            .unwrap_or(false),
        final_terrain_class_id: stop_state.and_then(|state| state.final_terrain_class_id),
        final_terrain_class_name: stop_state
            .and_then(|state| state.final_terrain_class_name.clone()),
        final_terrain_class_source: stop_state
            .and_then(|state| state.final_terrain_class_source.clone()),
        last_significant_impact_terrain_class_id: stop_state
            .and_then(|state| state.last_significant_impact_terrain_class_id),
        last_significant_impact_terrain_class_name: stop_state
            .and_then(|state| state.last_significant_impact_terrain_class_name.clone()),
        last_significant_impact_terrain_class_source: stop_state
            .and_then(|state| state.last_significant_impact_terrain_class_source.clone()),
        significant_impact_terrain_class_counts: serde_json::to_string(
            &stop_state
                .map(|state| state.significant_impact_terrain_class_counts.clone())
                .unwrap_or_default(),
        )
        .expect("significant impact terrain/material class counts serialize to JSON"),
        significant_impact_terrain_class_sequence_head: serde_json::to_string(
            &stop_state
                .map(|state| state.significant_impact_terrain_class_sequence_head.clone())
                .unwrap_or_default(),
        )
        .expect("significant impact terrain/material class head sequence serializes to JSON"),
        significant_impact_terrain_class_sequence_tail: serde_json::to_string(
            &stop_state
                .map(|state| state.significant_impact_terrain_class_sequence_tail.clone())
                .unwrap_or_default(),
        )
        .expect("significant impact terrain/material class tail sequence serializes to JSON"),
        significant_impact_terrain_class_sequence_truncated: stop_state
            .map(|state| state.significant_impact_terrain_class_sequence_truncated)
            .unwrap_or(false),
        significant_impact_terrain_class_unavailable_count: stop_state
            .map(|state| state.significant_impact_terrain_class_unavailable_count)
            .unwrap_or(0),
        terrain_material_instrumentation_gaps: serde_json::to_string(
            &stop_state
                .map(|state| state.terrain_material_instrumentation_gaps.clone())
                .unwrap_or_else(|| {
                    vec![
                        "explicit stop_state is unavailable for terrain/material lookup"
                            .to_string(),
                    ]
                }),
        )
        .expect("terrain/material instrumentation gaps serialize to JSON"),
        runout_m: run.summary.runout_m,
    }
}

fn stop_state_sidecar_path(path: &Path) -> PathBuf {
    let stem = path
        .file_stem()
        .and_then(|value| value.to_str())
        .unwrap_or("ensemble");
    let filename = format!("{stem}_stop_state.csv");
    path.with_file_name(filename)
}

fn terrain_material_exposure_sidecar_path(path: &Path) -> PathBuf {
    let stem = path
        .file_stem()
        .and_then(|value| value.to_str())
        .unwrap_or("ensemble");
    let filename = format!("{stem}_terrain_material_exposure.csv");
    path.with_file_name(filename)
}

fn impact_terrain_material_sidecar_dir(dir: &Path) -> PathBuf {
    let name = dir
        .file_name()
        .and_then(|value| value.to_str())
        .unwrap_or("ensemble_impacts");
    dir.with_file_name(format!("{name}_terrain_material"))
}

fn impact_terrain_material_sidecar_dir_for_parquet_path(path: &Path) -> PathBuf {
    let stem = path
        .file_stem()
        .and_then(|value| value.to_str())
        .unwrap_or("ensemble_impacts");
    path.with_file_name(format!("{stem}_terrain_material"))
}

fn write_ensemble_stop_state_csv(
    path: impl AsRef<Path>,
    rows: &[EnsembleStopStateRow],
) -> Result<OutputManifest, ValidationError> {
    let path = path.as_ref();
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent)?;
    }
    let mut writer = csv::Writer::from_path(path)?;
    for row in rows {
        writer.serialize(row)?;
    }
    writer.flush()?;
    let metadata = fs::metadata(path)?;
    Ok(OutputManifest {
        kind: "ensemble_stop_state".to_string(),
        format: "csv".to_string(),
        path: path.to_string_lossy().to_string(),
        file_count: 1,
        total_bytes: metadata.len(),
        sha256: Some(sha256_file(path)?),
        schema_version: Some("stop_state_table_v3".to_string()),
        row_count: Some(rows.len()),
        skipped_empty_files: None,
        compression: None,
        row_group_count: None,
    })
}

fn stop_state_summary_manifest(
    path: Option<&Path>,
    rows: &[EnsembleStopStateRow],
    warnings: &mut Vec<String>,
) -> StopStateSummaryManifest {
    let mut stop_reason_counts = BTreeMap::new();
    let mut final_contact_state_counts = BTreeMap::new();
    let mut final_speeds = Vec::new();
    let mut final_kinetic = Vec::new();
    let mut low_energy_contact_count_total = 0_usize;
    let mut significant_impact_count_total = 0_usize;
    let mut terrain_slope_available_count = 0_usize;
    let mut explicit_stop_state_count = 0_usize;
    let mut terrain_material_context_available_count = 0_usize;
    let mut final_terrain_class_counts = BTreeMap::new();
    let mut last_significant_impact_terrain_class_counts = BTreeMap::new();
    let mut significant_impact_terrain_class_counts = BTreeMap::new();
    let mut significant_impact_terrain_class_unavailable_count = 0_usize;
    let mut significant_impact_terrain_class_counts_valid = true;
    let mut significant_impact_terrain_class_counts_error = None;
    for row in rows {
        if let Some(reason) = &row.stop_reason {
            explicit_stop_state_count += 1;
            *stop_reason_counts.entry(reason.clone()).or_insert(0) += 1;
        }
        if let Some(state) = &row.final_contact_state {
            *final_contact_state_counts.entry(state.clone()).or_insert(0) += 1;
        }
        if let Some(speed) = row.final_speed_mps {
            final_speeds.push(speed);
        }
        if let Some(kinetic) = row.final_kinetic_j {
            final_kinetic.push(kinetic);
        }
        if let Some(count) = row.low_energy_contact_count {
            low_energy_contact_count_total += count;
        }
        if let Some(count) = row.significant_impact_count {
            significant_impact_count_total += count;
        }
        if row.terrain_slope_abs.is_some() {
            terrain_slope_available_count += 1;
        }
        if row.terrain_material_context_available {
            terrain_material_context_available_count += 1;
        }
        if let Some(label) =
            terrain_class_label(row.final_terrain_class_id, &row.final_terrain_class_name)
        {
            *final_terrain_class_counts.entry(label).or_insert(0) += 1;
        }
        if let Some(label) = terrain_class_label(
            row.last_significant_impact_terrain_class_id,
            &row.last_significant_impact_terrain_class_name,
        ) {
            *last_significant_impact_terrain_class_counts
                .entry(label)
                .or_insert(0) += 1;
        }
        match parse_json_count_map(&row.significant_impact_terrain_class_counts) {
            Ok(parsed) => {
                for (label, count) in parsed {
                    *significant_impact_terrain_class_counts
                        .entry(label)
                        .or_insert(0) += count;
                }
            }
            Err(error) => {
                let warning = format!(
                    "stop-state significant_impact_terrain_class_counts could not be parsed as JSON: {error}"
                );
                warnings.push(warning);
                significant_impact_terrain_class_counts_valid = false;
                significant_impact_terrain_class_counts_error =
                    Some("one or more significant_impact_terrain_class_counts values were malformed JSON and were excluded from the aggregate".to_string());
            }
        }
        significant_impact_terrain_class_unavailable_count +=
            row.significant_impact_terrain_class_unavailable_count;
    }
    StopStateSummaryManifest {
        schema_version: STOP_STATE_SUMMARY_SCHEMA_VERSION.to_string(),
        path: path.map(|path| path.to_string_lossy().to_string()),
        trajectory_count: rows.len(),
        explicit_stop_state_count,
        stop_reason_counts,
        final_contact_state_counts,
        low_energy_contact_count_total,
        significant_impact_count_total,
        terrain_slope_available_count,
        final_speed_mean_mps: nonempty_mean(&final_speeds),
        final_speed_max_mps: final_speeds.iter().copied().reduce(f64::max),
        final_kinetic_mean_j: nonempty_mean(&final_kinetic),
        final_kinetic_max_j: final_kinetic.iter().copied().reduce(f64::max),
        terrain_material_context_available_count,
        final_terrain_class_counts,
        last_significant_impact_terrain_class_counts,
        significant_impact_terrain_class_counts,
        significant_impact_terrain_class_counts_valid,
        significant_impact_terrain_class_counts_error,
        significant_impact_terrain_class_unavailable_count,
        limitations: vec![
            "aggregate is diagnostic only and does not change validation metrics".to_string(),
            "domain_exit and terrain_error flags remain false until the integrator exposes those termination modes".to_string(),
            "terrain/material class counts are provenance groupings from configured terrain_classes metadata, not calibrated material evidence".to_string(),
            "significant-impact terrain/material sequences are bounded head/tail diagnostic samples; full per-event class output is not yet emitted".to_string(),
        ],
    }
}

fn parse_json_count_map(text: &str) -> Result<BTreeMap<String, usize>, serde_json::Error> {
    serde_json::from_str(text)
}

fn terrain_class_label(class_id: Option<i32>, class_name: &Option<String>) -> Option<String> {
    class_id.map(|class_id| match class_name {
        Some(class_name) => format!("{class_id}:{class_name}"),
        None => class_id.to_string(),
    })
}

#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord)]
struct TerrainMaterialExposureKey {
    class_id: Option<i32>,
    class_name: Option<String>,
    source: String,
    status: String,
}

#[derive(Debug, Clone)]
struct TerrainMaterialExposureAccumulator {
    release_id: String,
    trajectory_id: String,
    seed: Option<u64>,
    key: TerrainMaterialExposureKey,
    sample_count: usize,
    segment_count: usize,
    duration_s: f64,
    path_length_m: f64,
    airborne_sample_count: usize,
    impact_sample_count: usize,
    sliding_sample_count: usize,
    rolling_sample_count: usize,
    stopped_sample_count: usize,
    contact_sample_count: usize,
    contact_duration_s: f64,
    contact_path_length_m: f64,
    instrumentation_gaps: BTreeSet<String>,
}

impl TerrainMaterialExposureAccumulator {
    fn new(release_id: &str, run: &TrajectoryRun, key: TerrainMaterialExposureKey) -> Self {
        Self {
            release_id: release_id.to_string(),
            trajectory_id: run.summary.trajectory_id.clone(),
            seed: run.summary.seed,
            key,
            sample_count: 0,
            segment_count: 0,
            duration_s: 0.0,
            path_length_m: 0.0,
            airborne_sample_count: 0,
            impact_sample_count: 0,
            sliding_sample_count: 0,
            rolling_sample_count: 0,
            stopped_sample_count: 0,
            contact_sample_count: 0,
            contact_duration_s: 0.0,
            contact_path_length_m: 0.0,
            instrumentation_gaps: BTreeSet::new(),
        }
    }

    fn record(
        &mut self,
        sample: &TrajectorySample,
        duration_s: f64,
        path_length_m: f64,
        starts_segment: bool,
    ) {
        self.sample_count += 1;
        if starts_segment {
            self.segment_count += 1;
        }
        self.duration_s += duration_s.max(0.0);
        self.path_length_m += path_length_m.max(0.0);
        match sample.contact_state {
            ContactState::Airborne => self.airborne_sample_count += 1,
            ContactState::Impact => self.impact_sample_count += 1,
            ContactState::Sliding => self.sliding_sample_count += 1,
            ContactState::Rolling => self.rolling_sample_count += 1,
            ContactState::Stopped => self.stopped_sample_count += 1,
        }
        if sample.contact_state != ContactState::Airborne {
            self.contact_sample_count += 1;
            self.contact_duration_s += duration_s.max(0.0);
            self.contact_path_length_m += path_length_m.max(0.0);
        }
    }

    fn into_row(self) -> TerrainMaterialExposureRow {
        TerrainMaterialExposureRow {
            release_id: self.release_id,
            trajectory_id: self.trajectory_id,
            seed: self.seed,
            terrain_class_id: self.key.class_id,
            terrain_class_name: self.key.class_name,
            terrain_class_source: self.key.source,
            terrain_material_context_status: self.key.status,
            sample_count: self.sample_count,
            segment_count: self.segment_count,
            duration_s: self.duration_s,
            path_length_m: self.path_length_m,
            airborne_sample_count: self.airborne_sample_count,
            impact_sample_count: self.impact_sample_count,
            sliding_sample_count: self.sliding_sample_count,
            rolling_sample_count: self.rolling_sample_count,
            stopped_sample_count: self.stopped_sample_count,
            contact_sample_count: self.contact_sample_count,
            contact_duration_s: self.contact_duration_s,
            contact_path_length_m: self.contact_path_length_m,
            instrumentation_gaps: serde_json::to_string(
                &self.instrumentation_gaps.into_iter().collect::<Vec<_>>(),
            )
            .expect("terrain/material exposure gaps serialize to JSON"),
        }
    }
}

fn terrain_material_exposure_rows(
    release_id: &str,
    run: &TrajectoryRun,
    class_map: &TerrainClassMap,
) -> Vec<TerrainMaterialExposureRow> {
    let mut accumulators: BTreeMap<TerrainMaterialExposureKey, TerrainMaterialExposureAccumulator> =
        BTreeMap::new();
    let mut previous_key: Option<TerrainMaterialExposureKey> = None;
    let mut previous_sample: Option<&TrajectorySample> = None;
    for sample in &run.samples {
        let key = if let Some((class_id, class_name, source)) =
            terrain_class_lookup(class_map, sample.x_m, sample.y_m)
        {
            TerrainMaterialExposureKey {
                class_id: Some(class_id),
                class_name: Some(class_name),
                source,
                status: "classified".to_string(),
            }
        } else {
            TerrainMaterialExposureKey {
                class_id: None,
                class_name: None,
                source: class_map.metadata.layer_id.clone(),
                status: "unavailable".to_string(),
            }
        };
        let duration_s = previous_sample
            .map(|previous| sample.time_s - previous.time_s)
            .filter(|value| value.is_finite() && *value > 0.0)
            .unwrap_or(0.0);
        let path_length_m = previous_sample
            .map(|previous| horizontal_sample_distance_m(previous, sample))
            .filter(|value| value.is_finite())
            .unwrap_or(0.0);
        let starts_segment = previous_key.as_ref() != Some(&key);
        let accumulator = accumulators
            .entry(key.clone())
            .or_insert_with(|| TerrainMaterialExposureAccumulator::new(release_id, run, key));
        accumulator.record(sample, duration_s, path_length_m, starts_segment);
        if accumulator.key.status == "unavailable" {
            accumulator.instrumentation_gaps.insert(
                "sample position has no terrain/material class (outside class grid or nodata)"
                    .to_string(),
            );
        }
        previous_key = Some(accumulator.key.clone());
        previous_sample = Some(sample);
    }
    accumulators
        .into_values()
        .map(TerrainMaterialExposureAccumulator::into_row)
        .collect()
}

fn horizontal_sample_distance_m(a: &TrajectorySample, b: &TrajectorySample) -> f64 {
    (b.x_m - a.x_m).hypot(b.y_m - a.y_m)
}

fn write_terrain_material_exposure_csv(
    path: impl AsRef<Path>,
    rows: &[TerrainMaterialExposureRow],
    kind: &str,
) -> Result<OutputManifest, ValidationError> {
    let path = path.as_ref();
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent)?;
    }
    let mut writer = csv::Writer::from_path(path)?;
    for row in rows {
        writer.serialize(row)?;
    }
    writer.flush()?;
    let metadata = fs::metadata(path)?;
    Ok(OutputManifest {
        kind: kind.to_string(),
        format: "csv".to_string(),
        path: path.to_string_lossy().to_string(),
        file_count: 1,
        total_bytes: metadata.len(),
        sha256: Some(sha256_file(path)?),
        schema_version: Some("terrain_material_exposure_table_v1".to_string()),
        row_count: Some(rows.len()),
        skipped_empty_files: None,
        compression: None,
        row_group_count: None,
    })
}

fn terrain_material_exposure_summary_manifest(
    path: Option<&Path>,
    rows: &[TerrainMaterialExposureRow],
) -> TerrainMaterialExposureSummaryManifest {
    let mut trajectory_ids = BTreeSet::new();
    let mut classified_sample_count = 0_usize;
    let mut unavailable_sample_count = 0_usize;
    let mut by_class: BTreeMap<String, TerrainMaterialExposureClassSummaryManifest> =
        BTreeMap::new();
    let mut class_trajectories: BTreeMap<String, BTreeSet<String>> = BTreeMap::new();
    for row in rows {
        trajectory_ids.insert(row.trajectory_id.clone());
        if row.terrain_material_context_status == "classified" {
            classified_sample_count += row.sample_count;
        } else {
            unavailable_sample_count += row.sample_count;
        }
        let label = terrain_class_label(row.terrain_class_id, &row.terrain_class_name)
            .unwrap_or_else(|| row.terrain_material_context_status.clone());
        let entry = by_class.entry(label.clone()).or_insert_with(|| {
            TerrainMaterialExposureClassSummaryManifest {
                terrain_class_label: label.clone(),
                trajectory_count: 0,
                sample_count: 0,
                duration_s: 0.0,
                path_length_m: 0.0,
                contact_sample_count: 0,
                contact_duration_s: 0.0,
                contact_path_length_m: 0.0,
            }
        });
        entry.sample_count += row.sample_count;
        entry.duration_s += row.duration_s;
        entry.path_length_m += row.path_length_m;
        entry.contact_sample_count += row.contact_sample_count;
        entry.contact_duration_s += row.contact_duration_s;
        entry.contact_path_length_m += row.contact_path_length_m;
        class_trajectories
            .entry(label)
            .or_default()
            .insert(row.trajectory_id.clone());
    }
    for (label, trajectories) in class_trajectories {
        if let Some(entry) = by_class.get_mut(&label) {
            entry.trajectory_count = trajectories.len();
        }
    }
    TerrainMaterialExposureSummaryManifest {
        schema_version: TERRAIN_MATERIAL_EXPOSURE_SUMMARY_SCHEMA_VERSION.to_string(),
        path: path.map(|path| path.to_string_lossy().to_string()),
        row_count: rows.len(),
        trajectory_count: trajectory_ids.len(),
        classified_sample_count,
        unavailable_sample_count,
        class_summaries: by_class.into_values().collect(),
        limitations: vec![
            "exposure rows are diagnostic only and are derived from saved trajectory samples".to_string(),
            "duration and path length are assigned to the terrain/material class at the segment end sample".to_string(),
            "terrain/material classes are configured assumptions and may include active parameter overrides; they are not observed material truth".to_string(),
        ],
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

fn write_trajectory_metadata_csv(
    path: impl AsRef<Path>,
    rows: &[TrajectoryMetadataRow],
) -> Result<(), ValidationError> {
    if let Some(parent) = path.as_ref().parent() {
        fs::create_dir_all(parent)?;
    }
    let mut writer = csv::Writer::from_path(path)?;
    for row in rows {
        writer.serialize(row)?;
    }
    writer.flush()?;
    Ok(())
}

fn write_trajectory_csv_with_id(
    path: impl AsRef<Path>,
    trajectory_id: &str,
    samples: &[TrajectorySample],
) -> Result<(), ValidationError> {
    if let Some(parent) = path.as_ref().parent() {
        fs::create_dir_all(parent)?;
    }
    let mut writer = csv::Writer::from_path(path)?;
    writer.write_record([
        "trajectory_id",
        "time_s",
        "x_m",
        "y_m",
        "z_m",
        "vx_mps",
        "vy_mps",
        "vz_mps",
        "speed_mps",
        "kinetic_j",
        "rotational_j",
        "potential_j",
        "total_energy_j",
        "contact_state",
        "omega_x_radps",
        "omega_y_radps",
        "omega_z_radps",
        "contact_tangent_speed_mps",
        "rolling_residual_mps",
        "scarring_depth_m",
        "scarring_drag_force_n",
        "scarring_energy_loss_j",
    ])?;
    for sample in samples {
        writer.write_record([
            trajectory_id.to_string(),
            sample.time_s.to_string(),
            sample.x_m.to_string(),
            sample.y_m.to_string(),
            sample.z_m.to_string(),
            sample.vx_mps.to_string(),
            sample.vy_mps.to_string(),
            sample.vz_mps.to_string(),
            sample.speed_mps.to_string(),
            sample.kinetic_j.to_string(),
            sample.rotational_j.to_string(),
            sample.potential_j.to_string(),
            sample.total_energy_j.to_string(),
            contact_state_csv(sample.contact_state).to_string(),
            sample.omega_x_radps.to_string(),
            sample.omega_y_radps.to_string(),
            sample.omega_z_radps.to_string(),
            sample.contact_tangent_speed_mps.to_string(),
            sample.rolling_residual_mps.to_string(),
            sample.scarring_depth_m.to_string(),
            sample.scarring_drag_force_n.to_string(),
            sample.scarring_energy_loss_j.to_string(),
        ])?;
    }
    writer.flush()?;
    Ok(())
}

fn write_impact_events_csv_with_id(
    path: impl AsRef<Path>,
    trajectory_id: &str,
    events: &[ImpactEvent],
) -> Result<(), ValidationError> {
    if let Some(parent) = path.as_ref().parent() {
        fs::create_dir_all(parent)?;
    }
    let mut writer = csv::Writer::from_path(path)?;
    writer.write_record([
        "trajectory_id",
        "impact_index",
        "time_s",
        "x_m",
        "y_m",
        "z_m",
        "terrain_normal_x",
        "terrain_normal_y",
        "terrain_normal_z",
        "effective_normal_x",
        "effective_normal_y",
        "effective_normal_z",
        "incoming_vx_mps",
        "incoming_vy_mps",
        "incoming_vz_mps",
        "post_contact_vx_mps",
        "post_contact_vy_mps",
        "post_contact_vz_mps",
        "post_scarring_vx_mps",
        "post_scarring_vy_mps",
        "post_scarring_vz_mps",
        "post_step_vx_mps",
        "post_step_vy_mps",
        "post_step_vz_mps",
        "impact_angle_deg",
        "incoming_normal_speed_mps",
        "incoming_tangent_speed_mps",
        "post_contact_normal_speed_mps",
        "post_contact_tangent_speed_mps",
        "post_scarring_normal_speed_mps",
        "post_scarring_tangent_speed_mps",
        "post_step_normal_speed_mps",
        "post_step_tangent_speed_mps",
        "pre_contact_translational_j",
        "pre_contact_rotational_j",
        "post_contact_translational_j",
        "post_contact_rotational_j",
        "post_scarring_translational_j",
        "post_scarring_rotational_j",
        "post_step_translational_j",
        "post_step_rotational_j",
        "scarring_depth_m",
        "scarring_area_m2",
        "scarring_drag_force_n",
        "scarring_uncapped_energy_loss_j",
        "scarring_capped_energy_loss_j",
        "scarring_depth_source",
        "cumulative_scarring_energy_loss_j",
    ])?;
    for event in events {
        writer.write_record([
            trajectory_id.to_string(),
            event.impact_index.to_string(),
            event.time_s.to_string(),
            event.x_m.to_string(),
            event.y_m.to_string(),
            event.z_m.to_string(),
            event.terrain_normal_x.to_string(),
            event.terrain_normal_y.to_string(),
            event.terrain_normal_z.to_string(),
            event.effective_normal_x.to_string(),
            event.effective_normal_y.to_string(),
            event.effective_normal_z.to_string(),
            event.incoming_vx_mps.to_string(),
            event.incoming_vy_mps.to_string(),
            event.incoming_vz_mps.to_string(),
            event.post_contact_vx_mps.to_string(),
            event.post_contact_vy_mps.to_string(),
            event.post_contact_vz_mps.to_string(),
            event.post_scarring_vx_mps.to_string(),
            event.post_scarring_vy_mps.to_string(),
            event.post_scarring_vz_mps.to_string(),
            event.post_step_vx_mps.to_string(),
            event.post_step_vy_mps.to_string(),
            event.post_step_vz_mps.to_string(),
            event.impact_angle_deg.to_string(),
            event.incoming_normal_speed_mps.to_string(),
            event.incoming_tangent_speed_mps.to_string(),
            event.post_contact_normal_speed_mps.to_string(),
            event.post_contact_tangent_speed_mps.to_string(),
            event.post_scarring_normal_speed_mps.to_string(),
            event.post_scarring_tangent_speed_mps.to_string(),
            event.post_step_normal_speed_mps.to_string(),
            event.post_step_tangent_speed_mps.to_string(),
            event.pre_contact_translational_j.to_string(),
            event.pre_contact_rotational_j.to_string(),
            event.post_contact_translational_j.to_string(),
            event.post_contact_rotational_j.to_string(),
            event.post_scarring_translational_j.to_string(),
            event.post_scarring_rotational_j.to_string(),
            event.post_step_translational_j.to_string(),
            event.post_step_rotational_j.to_string(),
            event.scarring_depth_m.to_string(),
            event.scarring_area_m2.to_string(),
            event.scarring_drag_force_n.to_string(),
            event.scarring_uncapped_energy_loss_j.to_string(),
            event.scarring_capped_energy_loss_j.to_string(),
            scarring_depth_source_csv(event.scarring_depth_source).to_string(),
            event.cumulative_scarring_energy_loss_j.to_string(),
        ])?;
    }
    writer.flush()?;
    Ok(())
}

fn write_generated_release_points_csv(
    path: impl AsRef<Path>,
    points: &[GeneratedReleasePointRecord],
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
) -> Result<OutputManifest, ValidationError> {
    fs::create_dir_all(dir.as_ref())?;
    remove_stale_csv_outputs(dir.as_ref())?;
    let mut total_bytes = 0_u64;
    let mut row_count = 0_usize;
    for run in runs {
        let filename = format!("{}.csv", safe_filename(&run.summary.trajectory_id));
        let path = dir.as_ref().join(filename);
        write_trajectory_csv_with_id(&path, &run.summary.trajectory_id, &run.samples)?;
        total_bytes += fs::metadata(&path)?.len();
        row_count += run.samples.len();
    }
    let collection_sha256 = sha256_directory_csv_collection(dir.as_ref())?;
    Ok(OutputManifest {
        kind: "ensemble_trajectories".to_string(),
        format: "csv_directory".to_string(),
        path: dir.as_ref().to_string_lossy().to_string(),
        file_count: runs.len(),
        total_bytes,
        sha256: Some(collection_sha256),
        schema_version: None,
        row_count: Some(row_count),
        skipped_empty_files: Some(0),
        compression: None,
        row_group_count: None,
    })
}

fn write_ensemble_impact_events_dir(
    dir: impl AsRef<Path>,
    runs: &[TrajectoryRun],
) -> Result<OutputManifest, ValidationError> {
    fs::create_dir_all(dir.as_ref())?;
    remove_stale_csv_outputs(dir.as_ref())?;
    let mut file_count = 0_usize;
    let mut total_bytes = 0_u64;
    let mut row_count = 0_usize;
    let mut skipped_empty_files = 0_usize;
    for run in runs {
        if run.impact_events.is_empty() {
            skipped_empty_files += 1;
            continue;
        }
        let filename = format!("{}.csv", safe_filename(&run.summary.trajectory_id));
        let path = dir.as_ref().join(filename);
        write_impact_events_csv_with_id(&path, &run.summary.trajectory_id, &run.impact_events)?;
        file_count += 1;
        total_bytes += fs::metadata(&path)?.len();
        row_count += run.impact_events.len();
    }
    let collection_sha256 = if file_count > 0 {
        Some(sha256_directory_csv_collection(dir.as_ref())?)
    } else {
        None
    };
    Ok(OutputManifest {
        kind: "ensemble_impact_events".to_string(),
        format: "csv_directory".to_string(),
        path: dir.as_ref().to_string_lossy().to_string(),
        file_count,
        total_bytes,
        sha256: collection_sha256,
        schema_version: None,
        row_count: Some(row_count),
        skipped_empty_files: Some(skipped_empty_files),
        compression: None,
        row_group_count: None,
    })
}

fn write_ensemble_impact_terrain_material_dir(
    dir: impl AsRef<Path>,
    runs: &[TrajectoryRun],
    class_map: &TerrainClassMap,
) -> Result<OutputManifest, ValidationError> {
    fs::create_dir_all(dir.as_ref())?;
    remove_stale_csv_outputs(dir.as_ref())?;
    let mut file_count = 0_usize;
    let mut total_bytes = 0_u64;
    let mut row_count = 0_usize;
    let mut skipped_empty_files = 0_usize;
    for run in runs {
        if run.impact_events.is_empty() {
            skipped_empty_files += 1;
            continue;
        }
        let rows = impact_terrain_material_rows(run, class_map);
        let filename = format!("{}.csv", safe_filename(&run.summary.trajectory_id));
        let path = dir.as_ref().join(filename);
        write_impact_terrain_material_csv(&path, &rows)?;
        file_count += 1;
        total_bytes += fs::metadata(&path)?.len();
        row_count += rows.len();
    }
    let collection_sha256 = if file_count > 0 {
        Some(sha256_directory_csv_collection(dir.as_ref())?)
    } else {
        None
    };
    Ok(OutputManifest {
        kind: "ensemble_impact_terrain_material".to_string(),
        format: "csv_directory".to_string(),
        path: dir.as_ref().to_string_lossy().to_string(),
        file_count,
        total_bytes,
        sha256: collection_sha256,
        schema_version: Some("impact_terrain_material_table_v1".to_string()),
        row_count: Some(row_count),
        skipped_empty_files: Some(skipped_empty_files),
        compression: None,
        row_group_count: None,
    })
}

fn impact_terrain_material_rows(
    run: &TrajectoryRun,
    class_map: &TerrainClassMap,
) -> Vec<ImpactTerrainMaterialRow> {
    run.impact_events
        .iter()
        .map(|event| {
            let (
                terrain_class_id,
                terrain_class_name,
                terrain_class_source,
                terrain_material_context_status,
                active_parameter_override_fields,
                active_parameter_override_values,
                instrumentation_gaps,
            ) = if let Some((class_id, class_name, source)) =
                terrain_class_lookup(class_map, event.x_m, event.y_m)
            {
                let (active_fields, active_values) = class_map
                    .classes_by_id
                    .get(&class_id)
                    .map(|class| {
                        (
                            class.parameter_overrides.active_field_names(),
                            class.parameter_overrides.active_values(),
                        )
                    })
                    .unwrap_or_default();
                (
                    Some(class_id),
                    Some(class_name),
                    source,
                    "classified".to_string(),
                    active_fields,
                    active_values,
                    Vec::new(),
                )
            } else {
                (
                    None,
                    None,
                    class_map.metadata.layer_id.clone(),
                    "unavailable".to_string(),
                    Vec::new(),
                    Default::default(),
                    vec![
                        "impact position has no terrain/material class (outside class grid or nodata)"
                            .to_string(),
                    ],
                )
            };
            ImpactTerrainMaterialRow {
                trajectory_id: run.summary.trajectory_id.clone(),
                seed: run.summary.seed,
                impact_index: event.impact_index,
                time_s: event.time_s,
                x_m: event.x_m,
                y_m: event.y_m,
                z_m: event.z_m,
                significant_impact: event.incoming_normal_speed_mps
                    >= SIGNIFICANT_IMPACT_MIN_NORMAL_SPEED_MPS,
                incoming_normal_speed_mps: event.incoming_normal_speed_mps,
                terrain_class_id,
                terrain_class_name,
                terrain_class_source,
                terrain_material_context_status,
                active_parameter_override_count: active_parameter_override_fields.len(),
                active_parameter_override_fields: serde_json::to_string(
                    &active_parameter_override_fields,
                )
                .expect("impact terrain/material active override fields serialize to JSON"),
                active_parameter_override_values: serde_json::to_string(
                    &active_parameter_override_values,
                )
                .expect("impact terrain/material active override values serialize to JSON"),
                instrumentation_gaps: serde_json::to_string(&instrumentation_gaps)
                    .expect("impact terrain/material gaps serialize to JSON"),
            }
        })
        .collect()
}

fn write_impact_terrain_material_csv(
    path: impl AsRef<Path>,
    rows: &[ImpactTerrainMaterialRow],
) -> Result<(), ValidationError> {
    if let Some(parent) = path.as_ref().parent() {
        fs::create_dir_all(parent)?;
    }
    let mut writer = csv::Writer::from_path(path)?;
    for row in rows {
        writer.serialize(row)?;
    }
    writer.flush()?;
    Ok(())
}

fn remove_stale_csv_outputs(dir: &Path) -> Result<(), ValidationError> {
    for entry in fs::read_dir(dir)? {
        let path = entry?.path();
        if path.extension().and_then(|extension| extension.to_str()) == Some("csv") {
            fs::remove_file(path)?;
        }
    }
    Ok(())
}

fn sha256_directory_csv_collection(dir: &Path) -> Result<String, ValidationError> {
    let mut paths = fs::read_dir(dir)?
        .map(|entry| entry.map(|entry| entry.path()))
        .collect::<Result<Vec<_>, _>>()?;
    paths.retain(|path| path.extension().and_then(|extension| extension.to_str()) == Some("csv"));
    paths.sort();

    let mut digest = Sha256::new();
    for path in paths {
        let file_name = path
            .file_name()
            .and_then(|name| name.to_str())
            .unwrap_or_default();
        let size = fs::metadata(&path)?.len();
        let file_hash = sha256_file(&path)?;
        digest.update(file_name.as_bytes());
        digest.update(b"\0");
        digest.update(size.to_string().as_bytes());
        digest.update(b"\0");
        digest.update(file_hash.as_bytes());
        digest.update(b"\n");
    }
    Ok(format!("{:x}", digest.finalize()))
}

fn write_ensemble_impact_events_parquet(
    path: impl AsRef<Path>,
    runs: &[TrajectoryRun],
) -> Result<OutputManifest, ValidationError> {
    let path = path.as_ref();
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent)?;
    }

    let row_count: usize = runs.iter().map(|run| run.impact_events.len()).sum();

    let mut trajectory_id = Vec::with_capacity(row_count);
    let mut impact_index = Vec::with_capacity(row_count);
    let mut seed = Vec::with_capacity(row_count);
    let mut significant_impact = Vec::with_capacity(row_count);
    let mut scarring_depth_source = Vec::with_capacity(row_count);

    let mut time_s = Vec::with_capacity(row_count);
    let mut x_m = Vec::with_capacity(row_count);
    let mut y_m = Vec::with_capacity(row_count);
    let mut z_m = Vec::with_capacity(row_count);
    let mut terrain_normal_x = Vec::with_capacity(row_count);
    let mut terrain_normal_y = Vec::with_capacity(row_count);
    let mut terrain_normal_z = Vec::with_capacity(row_count);
    let mut effective_normal_x = Vec::with_capacity(row_count);
    let mut effective_normal_y = Vec::with_capacity(row_count);
    let mut effective_normal_z = Vec::with_capacity(row_count);
    let mut incoming_vx_mps = Vec::with_capacity(row_count);
    let mut incoming_vy_mps = Vec::with_capacity(row_count);
    let mut incoming_vz_mps = Vec::with_capacity(row_count);
    let mut post_contact_vx_mps = Vec::with_capacity(row_count);
    let mut post_contact_vy_mps = Vec::with_capacity(row_count);
    let mut post_contact_vz_mps = Vec::with_capacity(row_count);
    let mut post_scarring_vx_mps = Vec::with_capacity(row_count);
    let mut post_scarring_vy_mps = Vec::with_capacity(row_count);
    let mut post_scarring_vz_mps = Vec::with_capacity(row_count);
    let mut post_step_vx_mps = Vec::with_capacity(row_count);
    let mut post_step_vy_mps = Vec::with_capacity(row_count);
    let mut post_step_vz_mps = Vec::with_capacity(row_count);
    let mut impact_angle_deg = Vec::with_capacity(row_count);
    let mut incoming_normal_speed_mps = Vec::with_capacity(row_count);
    let mut incoming_tangent_speed_mps = Vec::with_capacity(row_count);
    let mut post_contact_normal_speed_mps = Vec::with_capacity(row_count);
    let mut post_contact_tangent_speed_mps = Vec::with_capacity(row_count);
    let mut post_scarring_normal_speed_mps = Vec::with_capacity(row_count);
    let mut post_scarring_tangent_speed_mps = Vec::with_capacity(row_count);
    let mut post_step_normal_speed_mps = Vec::with_capacity(row_count);
    let mut post_step_tangent_speed_mps = Vec::with_capacity(row_count);
    let mut pre_contact_translational_j = Vec::with_capacity(row_count);
    let mut pre_contact_rotational_j = Vec::with_capacity(row_count);
    let mut post_contact_translational_j = Vec::with_capacity(row_count);
    let mut post_contact_rotational_j = Vec::with_capacity(row_count);
    let mut post_scarring_translational_j = Vec::with_capacity(row_count);
    let mut post_scarring_rotational_j = Vec::with_capacity(row_count);
    let mut post_step_translational_j = Vec::with_capacity(row_count);
    let mut post_step_rotational_j = Vec::with_capacity(row_count);
    let mut scarring_depth_m = Vec::with_capacity(row_count);
    let mut scarring_area_m2 = Vec::with_capacity(row_count);
    let mut scarring_drag_force_n = Vec::with_capacity(row_count);
    let mut scarring_uncapped_energy_loss_j = Vec::with_capacity(row_count);
    let mut scarring_capped_energy_loss_j = Vec::with_capacity(row_count);
    let mut cumulative_scarring_energy_loss_j = Vec::with_capacity(row_count);

    for run in runs {
        for event in &run.impact_events {
            trajectory_id.push(run.summary.trajectory_id.clone());
            impact_index.push(event.impact_index as u64);
            seed.push(run.summary.seed);
            significant_impact
                .push(event.incoming_normal_speed_mps >= SIGNIFICANT_IMPACT_MIN_NORMAL_SPEED_MPS);
            scarring_depth_source
                .push(scarring_depth_source_csv(event.scarring_depth_source).to_string());

            time_s.push(event.time_s);
            x_m.push(event.x_m);
            y_m.push(event.y_m);
            z_m.push(event.z_m);
            terrain_normal_x.push(event.terrain_normal_x);
            terrain_normal_y.push(event.terrain_normal_y);
            terrain_normal_z.push(event.terrain_normal_z);
            effective_normal_x.push(event.effective_normal_x);
            effective_normal_y.push(event.effective_normal_y);
            effective_normal_z.push(event.effective_normal_z);
            incoming_vx_mps.push(event.incoming_vx_mps);
            incoming_vy_mps.push(event.incoming_vy_mps);
            incoming_vz_mps.push(event.incoming_vz_mps);
            post_contact_vx_mps.push(event.post_contact_vx_mps);
            post_contact_vy_mps.push(event.post_contact_vy_mps);
            post_contact_vz_mps.push(event.post_contact_vz_mps);
            post_scarring_vx_mps.push(event.post_scarring_vx_mps);
            post_scarring_vy_mps.push(event.post_scarring_vy_mps);
            post_scarring_vz_mps.push(event.post_scarring_vz_mps);
            post_step_vx_mps.push(event.post_step_vx_mps);
            post_step_vy_mps.push(event.post_step_vy_mps);
            post_step_vz_mps.push(event.post_step_vz_mps);
            impact_angle_deg.push(event.impact_angle_deg);
            incoming_normal_speed_mps.push(event.incoming_normal_speed_mps);
            incoming_tangent_speed_mps.push(event.incoming_tangent_speed_mps);
            post_contact_normal_speed_mps.push(event.post_contact_normal_speed_mps);
            post_contact_tangent_speed_mps.push(event.post_contact_tangent_speed_mps);
            post_scarring_normal_speed_mps.push(event.post_scarring_normal_speed_mps);
            post_scarring_tangent_speed_mps.push(event.post_scarring_tangent_speed_mps);
            post_step_normal_speed_mps.push(event.post_step_normal_speed_mps);
            post_step_tangent_speed_mps.push(event.post_step_tangent_speed_mps);
            pre_contact_translational_j.push(event.pre_contact_translational_j);
            pre_contact_rotational_j.push(event.pre_contact_rotational_j);
            post_contact_translational_j.push(event.post_contact_translational_j);
            post_contact_rotational_j.push(event.post_contact_rotational_j);
            post_scarring_translational_j.push(event.post_scarring_translational_j);
            post_scarring_rotational_j.push(event.post_scarring_rotational_j);
            post_step_translational_j.push(event.post_step_translational_j);
            post_step_rotational_j.push(event.post_step_rotational_j);
            scarring_depth_m.push(event.scarring_depth_m);
            scarring_area_m2.push(event.scarring_area_m2);
            scarring_drag_force_n.push(event.scarring_drag_force_n);
            scarring_uncapped_energy_loss_j.push(event.scarring_uncapped_energy_loss_j);
            scarring_capped_energy_loss_j.push(event.scarring_capped_energy_loss_j);
            cumulative_scarring_energy_loss_j.push(event.cumulative_scarring_energy_loss_j);
        }
    }

    debug_assert_eq!(trajectory_id.len(), row_count);
    let mut fields = vec![
        Field::new("trajectory_id", DataType::Utf8, false),
        Field::new("impact_index", DataType::UInt64, false),
        Field::new("seed", DataType::UInt64, true),
        Field::new("significant_impact", DataType::Boolean, false),
        Field::new("scarring_depth_source", DataType::Utf8, false),
    ];
    let mut columns: Vec<ArrayRef> = vec![
        Arc::new(StringArray::from(trajectory_id)),
        Arc::new(UInt64Array::from(impact_index)),
        Arc::new(UInt64Array::from(seed)),
        Arc::new(BooleanArray::from(significant_impact)),
        Arc::new(StringArray::from(scarring_depth_source)),
    ];

    macro_rules! add_f64_column {
        ($name:literal, $values:ident) => {{
            fields.push(Field::new($name, DataType::Float64, false));
            columns.push(Arc::new(Float64Array::from($values)) as ArrayRef);
        }};
    }

    add_f64_column!("time_s", time_s);
    add_f64_column!("x_m", x_m);
    add_f64_column!("y_m", y_m);
    add_f64_column!("z_m", z_m);
    add_f64_column!("terrain_normal_x", terrain_normal_x);
    add_f64_column!("terrain_normal_y", terrain_normal_y);
    add_f64_column!("terrain_normal_z", terrain_normal_z);
    add_f64_column!("effective_normal_x", effective_normal_x);
    add_f64_column!("effective_normal_y", effective_normal_y);
    add_f64_column!("effective_normal_z", effective_normal_z);
    add_f64_column!("incoming_vx_mps", incoming_vx_mps);
    add_f64_column!("incoming_vy_mps", incoming_vy_mps);
    add_f64_column!("incoming_vz_mps", incoming_vz_mps);
    add_f64_column!("post_contact_vx_mps", post_contact_vx_mps);
    add_f64_column!("post_contact_vy_mps", post_contact_vy_mps);
    add_f64_column!("post_contact_vz_mps", post_contact_vz_mps);
    add_f64_column!("post_scarring_vx_mps", post_scarring_vx_mps);
    add_f64_column!("post_scarring_vy_mps", post_scarring_vy_mps);
    add_f64_column!("post_scarring_vz_mps", post_scarring_vz_mps);
    add_f64_column!("post_step_vx_mps", post_step_vx_mps);
    add_f64_column!("post_step_vy_mps", post_step_vy_mps);
    add_f64_column!("post_step_vz_mps", post_step_vz_mps);
    add_f64_column!("impact_angle_deg", impact_angle_deg);
    add_f64_column!("incoming_normal_speed_mps", incoming_normal_speed_mps);
    add_f64_column!("incoming_tangent_speed_mps", incoming_tangent_speed_mps);
    add_f64_column!(
        "post_contact_normal_speed_mps",
        post_contact_normal_speed_mps
    );
    add_f64_column!(
        "post_contact_tangent_speed_mps",
        post_contact_tangent_speed_mps
    );
    add_f64_column!(
        "post_scarring_normal_speed_mps",
        post_scarring_normal_speed_mps
    );
    add_f64_column!(
        "post_scarring_tangent_speed_mps",
        post_scarring_tangent_speed_mps
    );
    add_f64_column!("post_step_normal_speed_mps", post_step_normal_speed_mps);
    add_f64_column!("post_step_tangent_speed_mps", post_step_tangent_speed_mps);
    add_f64_column!("pre_contact_translational_j", pre_contact_translational_j);
    add_f64_column!("pre_contact_rotational_j", pre_contact_rotational_j);
    add_f64_column!("post_contact_translational_j", post_contact_translational_j);
    add_f64_column!("post_contact_rotational_j", post_contact_rotational_j);
    add_f64_column!(
        "post_scarring_translational_j",
        post_scarring_translational_j
    );
    add_f64_column!("post_scarring_rotational_j", post_scarring_rotational_j);
    add_f64_column!("post_step_translational_j", post_step_translational_j);
    add_f64_column!("post_step_rotational_j", post_step_rotational_j);
    add_f64_column!("scarring_depth_m", scarring_depth_m);
    add_f64_column!("scarring_area_m2", scarring_area_m2);
    add_f64_column!("scarring_drag_force_n", scarring_drag_force_n);
    add_f64_column!(
        "scarring_uncapped_energy_loss_j",
        scarring_uncapped_energy_loss_j
    );
    add_f64_column!(
        "scarring_capped_energy_loss_j",
        scarring_capped_energy_loss_j
    );
    add_f64_column!(
        "cumulative_scarring_energy_loss_j",
        cumulative_scarring_energy_loss_j
    );

    let schema = Arc::new(Schema::new(fields));
    let batch = RecordBatch::try_new(schema.clone(), columns)?;
    let properties = WriterProperties::builder()
        .set_compression(Compression::UNCOMPRESSED)
        .build();
    let file = File::create(path)?;
    let mut writer = ArrowWriter::try_new(file, schema, Some(properties))?;
    writer.write(&batch)?;
    let metadata = writer.close()?;

    Ok(OutputManifest {
        kind: "ensemble_impact_events".to_string(),
        format: "parquet".to_string(),
        path: path.to_string_lossy().to_string(),
        file_count: 1,
        total_bytes: fs::metadata(path)?.len(),
        sha256: Some(sha256_file(path)?),
        schema_version: Some(IMPACT_EVENTS_TABLE_SCHEMA_VERSION.to_string()),
        row_count: Some(row_count),
        skipped_empty_files: None,
        compression: Some("uncompressed".to_string()),
        row_group_count: Some(metadata.row_groups.len()),
    })
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

fn default_single_trajectory_id() -> &'static str {
    "trajectory_000000"
}

fn default_manual_source_zone_id() -> &'static str {
    "manual_release"
}

fn default_observed_source_zone_id() -> &'static str {
    "observed_release_points"
}

fn default_probability_model() -> &'static str {
    "unweighted"
}

fn legacy_probability_model(mode: ProbabilityMode) -> &'static str {
    match mode {
        ProbabilityMode::UnweightedDiagnostic => "unweighted",
        ProbabilityMode::SamplingWeightedConditional => "sampling_weighted",
        ProbabilityMode::PhysicalProbability => "physical_probability",
        ProbabilityMode::AnnualFrequency => "annual_frequency",
    }
}

fn probability_mode_text(mode: ProbabilityMode) -> &'static str {
    match mode {
        ProbabilityMode::UnweightedDiagnostic => "unweighted_diagnostic",
        ProbabilityMode::SamplingWeightedConditional => "sampling_weighted_conditional",
        ProbabilityMode::PhysicalProbability => "physical_probability",
        ProbabilityMode::AnnualFrequency => "annual_frequency",
    }
}

fn normalization_scope_text(scope: NormalizationScope) -> &'static str {
    match scope {
        NormalizationScope::ConditionedOnFilter => "conditioned_on_filter",
        NormalizationScope::ConditionedOnScenario => "conditioned_on_scenario",
        NormalizationScope::AbsoluteProbabilityMass => "absolute_probability_mass",
        NormalizationScope::AnnualFrequencySum => "annual_frequency_sum",
    }
}

fn sphere_density_kgpm3(block: &SphereBlock) -> Option<f64> {
    let volume_m3 = (4.0 / 3.0) * std::f64::consts::PI * block.radius_m.powi(3);
    (volume_m3 > 0.0).then_some(block.mass_kg / volume_m3)
}

fn contact_state_csv(state: ContactState) -> &'static str {
    match state {
        ContactState::Airborne => "airborne",
        ContactState::Sliding => "sliding",
        ContactState::Impact => "impact",
        ContactState::Rolling => "rolling",
        ContactState::Stopped => "stopped",
    }
}

fn stop_reason_text(reason: &StopReason) -> &'static str {
    match reason {
        StopReason::ExplicitStoppedState => "explicit_stopped_state",
        StopReason::FinalSpeedBelowStopThreshold => "final_speed_below_stop_threshold",
        StopReason::TMaxReachedAirborne => "t_max_reached_airborne",
        StopReason::TMaxReachedInContactState => "t_max_reached_in_contact_state",
        StopReason::TMaxReachedOther => "t_max_reached_other",
        StopReason::Unknown => "unknown",
    }
}

fn scarring_depth_source_csv(source: ScarringDepthSource) -> &'static str {
    match source {
        ScarringDepthSource::None => "none",
        ScarringDepthSource::Computed => "computed",
        ScarringDepthSource::ComputedCapped => "computed_capped",
        ScarringDepthSource::Explicit => "explicit",
        ScarringDepthSource::ExplicitCapped => "explicit_capped",
    }
}

fn compute_deposition_cloud_metrics(
    runs: &[TrajectoryRun],
    observations: &ObservationData,
    observed_deposition_configured: bool,
    metrics: &mut BTreeMap<String, f64>,
    warnings: &mut Vec<String>,
) {
    metrics::compute_deposition_cloud_metrics(
        runs,
        observations,
        observed_deposition_configured,
        metrics,
        warnings,
    )
}

fn compute_roughness_comparison_metrics(
    case: &BenchmarkCase,
    config: &SimulationConfig,
    samples: &[TrajectorySample],
    metrics: &mut BTreeMap<String, f64>,
) -> Result<(), ValidationError> {
    metrics::compute_roughness_comparison_metrics(case, config, samples, metrics)
}

fn compute_scarring_comparison_metrics(
    case: &BenchmarkCase,
    config: &SimulationConfig,
    samples: &[TrajectorySample],
    metrics: &mut BTreeMap<String, f64>,
) -> Result<(), ValidationError> {
    metrics::compute_scarring_comparison_metrics(case, config, samples, metrics)
}

fn evaluate_failures(
    last: &TrajectorySample,
    metrics: &BTreeMap<String, f64>,
    expected: &ExpectedConfig,
) -> Vec<String> {
    metrics::evaluate_failures(last, metrics, expected)
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
    validation_io::load_observations(case, warnings)
}

fn skipped_report(case: &BenchmarkCase, warning: String) -> Result<CaseReport, ValidationError> {
    Ok(CaseReport {
        case_id: case.case_id.clone(),
        status: CaseStatus::Skipped,
        execution_status: ExecutionStatus::Skipped,
        scientific_status: ScientificStatus::NotEvaluated,
        timestamp_unix_s: now_unix_s(),
        model_version: env!("CARGO_PKG_VERSION").to_string(),
        git_hash: git_hash(),
        metrics: BTreeMap::new(),
        tolerances: case.expected.tolerances.clone(),
        failures: Vec::new(),
        warnings: vec![warning],
        parameters: build_simulation_config(case)?,
        stop_state: None,
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
) -> Result<f64, TerrainError> {
    Ok((sample.z_m - terrain.try_height(sample.x_m, sample.y_m)? - radius_m).max(0.0))
}

fn max_bounce_height(
    samples: &[TrajectorySample],
    terrain: &dyn crate::terrain::Terrain,
    radius_m: f64,
) -> Result<f64, TerrainError> {
    samples
        .iter()
        .map(|sample| clearance(sample, terrain, radius_m))
        .try_fold(0.0_f64, |acc, value| value.map(|value| acc.max(value)))
}

fn rebound_height_after_first_impact(
    samples: &[TrajectorySample],
    terrain: &dyn crate::terrain::Terrain,
    radius_m: f64,
) -> Result<f64, TerrainError> {
    let first_impact = samples
        .iter()
        .position(|sample| sample.contact_state == ContactState::Impact);
    if let Some(index) = first_impact {
        samples[index..]
            .iter()
            .map(|sample| clearance(sample, terrain, radius_m))
            .try_fold(0.0_f64, |acc, value| value.map(|value| acc.max(value)))
    } else {
        Ok(0.0)
    }
}

fn energy_monotonicity_violation(samples: &[TrajectorySample]) -> f64 {
    samples
        .windows(2)
        .map(|pair| (pair[1].total_energy_j - pair[0].total_energy_j).max(0.0))
        .fold(0.0_f64, f64::max)
}

fn max_position_delta(a: &[TrajectorySample], b: &[TrajectorySample]) -> f64 {
    if a.len() != b.len() {
        return f64::INFINITY;
    }
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
    sample.rotational_j = lerp(left.rotational_j, right.rotational_j);
    sample.potential_j = lerp(left.potential_j, right.potential_j);
    sample.total_energy_j = lerp(left.total_energy_j, right.total_energy_j);
    sample.contact_state = if weight < 0.5 {
        left.contact_state
    } else {
        right.contact_state
    };
    sample.omega_x_radps = lerp(left.omega_x_radps, right.omega_x_radps);
    sample.omega_y_radps = lerp(left.omega_y_radps, right.omega_y_radps);
    sample.omega_z_radps = lerp(left.omega_z_radps, right.omega_z_radps);
    sample.contact_tangent_speed_mps = lerp(
        left.contact_tangent_speed_mps,
        right.contact_tangent_speed_mps,
    );
    sample.rolling_residual_mps = lerp(left.rolling_residual_mps, right.rolling_residual_mps);
    sample.scarring_depth_m = lerp(left.scarring_depth_m, right.scarring_depth_m);
    sample.scarring_drag_force_n = lerp(left.scarring_drag_force_n, right.scarring_drag_force_n);
    sample.scarring_energy_loss_j = lerp(left.scarring_energy_loss_j, right.scarring_energy_loss_j);
    sample
}

fn observed_clearance(
    sample: &ObservedTrajectorySample,
    terrain: &dyn crate::terrain::Terrain,
    radius_m: f64,
) -> Result<f64, TerrainError> {
    Ok((sample.z_m - terrain.try_height(sample.x_m, sample.y_m)? - radius_m).max(0.0))
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
    DEFAULT_STOP_SPEED_MPS
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

#[cfg(test)]
mod tests {
    use super::*;
    use crate::shape::{
        BlockShapeType, MassPropertyModel, ShapeDimensions, ShapeMassProperties, ShapeOrientation,
        ShapeProvenance,
    };
    use std::{
        fs,
        time::{SystemTime, UNIX_EPOCH},
    };

    fn temp_path(prefix: &str, suffix: &str) -> std::path::PathBuf {
        let nonce = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .expect("system clock before UNIX_EPOCH")
            .as_nanos();
        std::env::temp_dir().join(format!(
            "rust_rockfall_tb199_{prefix}_{pid}_{nonce}.{suffix}",
            pid = std::process::id(),
        ))
    }

    fn write_temp_file(prefix: &str, suffix: &str, contents: &str) -> std::path::PathBuf {
        let path = temp_path(prefix, suffix);
        fs::write(&path, contents).expect("write temp test file");
        path
    }

    fn minimal_case(case_id: &str, terrain: CaseTerrain, block: CaseBlock) -> BenchmarkCase {
        BenchmarkCase {
            case_id: case_id.to_string(),
            title: String::new(),
            level: None,
            description: String::new(),
            terrain,
            block,
            release: CaseRelease::default(),
            release_zone: None,
            terrain_classes: None,
            block_shape: None,
            probabilistic_metadata: None,
            parameters: CaseParameters::default(),
            simulation: CaseSimulation {
                dt: 0.1,
                t_max: Some(0.2),
                max_steps: None,
                stop_velocity: default_stop_speed(),
            },
            random: CaseRandom::default(),
            observations: None,
            validation_scope: None,
            expected: ExpectedConfig::default(),
            metrics: Vec::new(),
            outputs: OutputConfig::default(),
            references: ReferenceConfig::default(),
        }
    }

    #[test]
    fn large_debug_output_warnings_are_nonfatal_and_thresholded() {
        let mut case = BenchmarkCase {
            case_id: "warning_case".to_string(),
            title: String::new(),
            level: None,
            description: String::new(),
            terrain: CaseTerrain {
                terrain_type: "plane".to_string(),
                ..CaseTerrain::default()
            },
            block: CaseBlock {
                mass: Some(1.0),
                radius: Some(0.5),
            },
            release: CaseRelease::default(),
            release_zone: None,
            terrain_classes: None,
            block_shape: None,
            probabilistic_metadata: None,
            parameters: CaseParameters::default(),
            simulation: CaseSimulation::default(),
            random: CaseRandom::default(),
            observations: None,
            validation_scope: None,
            expected: ExpectedConfig::default(),
            metrics: Vec::new(),
            outputs: OutputConfig {
                ensemble_trajectories_dir: Some(PathBuf::from("trajectory_debug")),
                ensemble_impact_events_dir: Some(PathBuf::from("impact_debug")),
                ..OutputConfig::default()
            },
            references: ReferenceConfig::default(),
        };
        let mut warnings = Vec::new();
        warn_large_debug_outputs(&case, OUTPUT_FILE_WARNING_THRESHOLD - 1, &mut warnings);
        assert!(warnings.is_empty());

        warn_large_debug_outputs(&case, OUTPUT_FILE_WARNING_THRESHOLD, &mut warnings);
        assert_eq!(warnings.len(), 1);
        assert!(warnings[0].contains("medium-scale debug output warning"));
        assert!(warnings[0].contains("ensemble_trajectories_dir and ensemble_impact_events_dir"));

        warnings.clear();
        warn_large_debug_outputs(&case, OUTPUT_FILE_HIGH_WARNING_THRESHOLD, &mut warnings);
        assert_eq!(warnings.len(), 1);
        assert!(warnings[0].contains("high-scale debug output warning"));

        case.outputs.ensemble_trajectories_dir = None;
        case.outputs.ensemble_impact_events_dir = None;
        warnings.clear();
        warn_large_debug_outputs(&case, OUTPUT_FILE_HIGH_WARNING_THRESHOLD, &mut warnings);
        assert!(warnings.is_empty());
    }

    #[test]
    fn stop_state_summary_marks_malformed_count_maps_invalid() {
        fn row(label_json: &str) -> EnsembleStopStateRow {
            EnsembleStopStateRow {
                release_id: "release".to_string(),
                trajectory_id: "trajectory".to_string(),
                seed: Some(1),
                stop_reason: Some("explicit_stopped_state".to_string()),
                final_contact_state: Some("stopped".to_string()),
                final_speed_mps: Some(0.0),
                final_kinetic_j: Some(0.0),
                termination_low_velocity: Some(true),
                termination_max_steps: Some(false),
                termination_t_max: Some(false),
                termination_domain_exit: Some(false),
                termination_terrain_error: Some(false),
                last_significant_impact_time_s: None,
                last_significant_impact_x_m: None,
                last_significant_impact_y_m: None,
                last_significant_impact_z_m: None,
                distance_last_significant_impact_to_final_m: None,
                significant_impact_count: Some(0),
                low_energy_contact_count: Some(0),
                terrain_normal_x: None,
                terrain_normal_y: None,
                terrain_normal_z: None,
                terrain_slope_abs: None,
                terrain_material_context_available: false,
                final_terrain_class_id: None,
                final_terrain_class_name: None,
                final_terrain_class_source: None,
                last_significant_impact_terrain_class_id: None,
                last_significant_impact_terrain_class_name: None,
                last_significant_impact_terrain_class_source: None,
                significant_impact_terrain_class_counts: label_json.to_string(),
                significant_impact_terrain_class_sequence_head: String::new(),
                significant_impact_terrain_class_sequence_tail: String::new(),
                significant_impact_terrain_class_sequence_truncated: false,
                significant_impact_terrain_class_unavailable_count: 0,
                terrain_material_instrumentation_gaps: String::new(),
                runout_m: 0.0,
            }
        }

        let rows = vec![row(r#"{"rock":2}"#), row("{not json}")];
        let mut warnings = Vec::new();
        let summary = stop_state_summary_manifest(None, &rows, &mut warnings);

        assert_eq!(summary.trajectory_count, 2);
        assert!(!summary.significant_impact_terrain_class_counts_valid);
        assert!(summary
            .significant_impact_terrain_class_counts_error
            .as_deref()
            .unwrap()
            .contains("malformed JSON"));
        assert_eq!(
            summary.significant_impact_terrain_class_counts.get("rock"),
            Some(&2)
        );
        assert!(warnings
            .iter()
            .any(|warning| warning.contains("could not be parsed as JSON")));
    }

    #[test]
    fn observed_trajectory_metrics_propagate_dem_query_errors() {
        let dem_path = write_temp_file(
            "observed_metrics_dem",
            "asc",
            "ncols 2\nnrows 2\nxllcorner 0.0\nyllcorner 0.0\ncellsize 1.0\nNODATA_value -9999\n10.0 10.0\n10.0 10.0\n",
        );
        let case = minimal_case(
            "observed_metrics_dem_case",
            CaseTerrain {
                terrain_type: "esri_ascii_grid".to_string(),
                path: Some(dem_path.clone()),
                ..CaseTerrain::default()
            },
            CaseBlock {
                mass: Some(1.0),
                radius: Some(0.5),
            },
        );
        let config = build_simulation_config(&case).expect("simulation config");
        let observations = ObservationData {
            trajectory_samples: vec![
                ObservedTrajectorySample {
                    trajectory_id: "trajectory_1".to_string(),
                    experiment_id: "experiment_1".to_string(),
                    time_s: 0.0,
                    x_m: 0.5,
                    y_m: 0.5,
                    z_m: 2.0,
                    vx_mps: Some(0.0),
                    vy_mps: Some(0.0),
                    vz_mps: Some(0.0),
                    speed_mps: Some(0.0),
                    kinetic_j: Some(0.0),
                },
                ObservedTrajectorySample {
                    trajectory_id: "trajectory_1".to_string(),
                    experiment_id: "experiment_1".to_string(),
                    time_s: 0.1,
                    x_m: 100.0,
                    y_m: 0.5,
                    z_m: 2.0,
                    vx_mps: Some(0.0),
                    vy_mps: Some(0.0),
                    vz_mps: Some(0.0),
                    speed_mps: Some(0.0),
                    kinetic_j: Some(0.0),
                },
            ],
            ..ObservationData::default()
        };
        let mut metrics = BTreeMap::new();
        let mut warnings = Vec::new();

        let error = compute_observed_trajectory_metrics(
            &case,
            &config,
            None,
            &observations,
            &mut metrics,
            &mut warnings,
        )
        .expect_err("dem query should be reported as a structured validation error");

        assert!(matches!(
            error,
            ValidationError::Terrain(TerrainError::OutOfBounds { .. })
        ));
        let _ = fs::remove_file(dem_path);
    }

    #[test]
    fn shape_metadata_manifest_returns_case_error_when_block_radius_missing() {
        let case = minimal_case(
            "shape_metadata_case",
            CaseTerrain {
                terrain_type: "plane".to_string(),
                ..CaseTerrain::default()
            },
            CaseBlock {
                mass: Some(1.0),
                radius: None,
            },
        );
        let mut case = case;
        case.block_shape = Some(BlockShapeConfig {
            metadata_path: std::path::PathBuf::from("shape_sidecar.yaml"),
        });
        let metadata = BlockShapeMetadata {
            schema_version: crate::shape::SHAPE_METADATA_SCHEMA_VERSION.to_string(),
            shape_id: "shape-1".to_string(),
            shape_type: BlockShapeType::PrincipalDimensions,
            shape_class: Some("compatibility_shape".to_string()),
            dimensions_m: ShapeDimensions {
                principal_lengths_m: Some([1.0, 2.0, 3.0]),
                ..ShapeDimensions::default()
            },
            mass_properties: ShapeMassProperties {
                mass_kg: 1.0,
                density_kgpm3: None,
                mass_property_model: Some(MassPropertyModel::BoxPrincipalDimensions),
                principal_moments_kg_m2: None,
                center_of_mass_offset_m: None,
            },
            orientation: ShapeOrientation::default(),
            provenance: ShapeProvenance::default(),
        };

        let error = shape_metadata_manifest(&case, &metadata)
            .expect_err("missing block.radius should produce a structured validation error");

        assert!(
            matches!(error, ValidationError::Case(message) if message.contains("block.radius"))
        );
    }
}
