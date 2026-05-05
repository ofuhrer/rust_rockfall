//! Verification and validation helpers, case loading, and metric computation.

use crate::{
    dynamics::{ContactModel, ContactParameterProvider, ScarringDepthSource, SoilInteractionModel},
    geodata::{GeodataError, ReleaseZoneMetadata, TerrainClassMap, TerrainSourceMetadata},
    geometry::SphereBlock,
    io,
    manifest::{
        OutputManifest, PerformanceManifest, ReleaseZoneManifest, RunManifest, SeedPolicyManifest,
        TerrainClassCoverageManifest, TerrainClassManifest, TerrainExtentManifest, TerrainManifest,
        TrajectoryMetadataManifest, RUN_MANIFEST_SCHEMA_VERSION,
    },
    simulation::{
        simulate_ensemble_with_contact_parameters,
        simulate_one_trajectory_with_terrain_and_contact_parameters, SimulationConfig,
        SimulationError, SimulationResult, TerrainConfig, TrajectoryRequest, TrajectoryRun,
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
use std::{
    collections::BTreeMap,
    fs::{self, File},
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
    pub manifest_json: Option<PathBuf>,
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
    pub scenario_id: String,
    pub sampling_weight: f64,
    pub probability_model: String,
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
    pub timestamp_unix_s: u64,
    pub model_version: String,
    pub git_hash: Option<String>,
    pub metrics: BTreeMap<String, f64>,
    pub tolerances: BTreeMap<String, f64>,
    pub failures: Vec<String>,
    pub warnings: Vec<String>,
    pub parameters: SimulationConfig,
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
    trajectory_metadata: Option<TrajectoryMetadataManifest>,
    performance: PerformanceManifest,
}

#[derive(Debug, Default)]
struct TrajectoryMetadataCollector {
    rows: BTreeMap<String, TrajectoryMetadataRow>,
}

impl TrajectoryMetadataCollector {
    fn insert_run(
        &mut self,
        case: &BenchmarkCase,
        run: &TrajectoryRun,
        release_id: impl Into<String>,
        source_zone_id: impl Into<String>,
        block: &SphereBlock,
    ) {
        if let Some(first) = run.samples.first() {
            self.insert_row(TrajectoryMetadataRow {
                trajectory_id: run.summary.trajectory_id.clone(),
                release_id: release_id.into(),
                source_zone_id: source_zone_id.into(),
                release_x_m: first.x_m,
                release_y_m: first.y_m,
                release_z_m: first.z_m,
                release_probability: None,
                block_radius_m: block.radius_m,
                block_mass_kg: block.mass_kg,
                block_density_kgpm3: sphere_density_kgpm3(block),
                shape_class: "sphere".to_string(),
                scenario_id: case.case_id.clone(),
                sampling_weight: 1.0,
                probability_model: default_probability_model().to_string(),
            });
        }
    }

    fn insert_single_result(
        &mut self,
        case: &BenchmarkCase,
        result: &SimulationResult,
        block: &SphereBlock,
    ) {
        if let Some(first) = result.samples.first() {
            self.insert_row(TrajectoryMetadataRow {
                trajectory_id: default_single_trajectory_id().to_string(),
                release_id: default_single_trajectory_id().to_string(),
                source_zone_id: default_manual_source_zone_id().to_string(),
                release_x_m: first.x_m,
                release_y_m: first.y_m,
                release_z_m: first.z_m,
                release_probability: None,
                block_radius_m: block.radius_m,
                block_mass_kg: block.mass_kg,
                block_density_kgpm3: sphere_density_kgpm3(block),
                shape_class: "sphere".to_string(),
                scenario_id: case.case_id.clone(),
                sampling_weight: 1.0,
                probability_model: default_probability_model().to_string(),
            });
        }
    }

    fn insert_row(&mut self, row: TrajectoryMetadataRow) {
        self.rows.entry(row.trajectory_id.clone()).or_insert(row);
    }

    fn rows(&self) -> Vec<TrajectoryMetadataRow> {
        self.rows.values().cloned().collect()
    }
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
    let total_started = Instant::now();
    let mut timing = RuntimeTiming::default();
    let mut warnings = Vec::new();
    let mut output_entries = Vec::new();
    let mut trajectory_metadata = TrajectoryMetadataCollector::default();
    let load_started = Instant::now();
    let terrain_source = load_terrain_source_metadata(case)?;
    let release_zone_source = load_release_zone_metadata(case, terrain_source.as_ref())?;
    let terrain_class_map = load_terrain_class_map(case, terrain_source.as_ref())?;
    timing.terrain_load_seconds += load_started.elapsed().as_secs_f64();
    let mut release_zone_manifest = release_zone_source
        .as_ref()
        .map(|source| release_zone_manifest(case.release_zone.as_ref(), source, 0));
    let terrain_class_manifest = terrain_class_map
        .as_ref()
        .map(|class_map| terrain_class_manifest(case.terrain_classes.as_ref(), class_map));
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
                let output_started = Instant::now();
                write_report(path, &report)?;
                timing.output_write_seconds += output_started.elapsed().as_secs_f64();
                output_entries.push(file_output_manifest(
                    path,
                    "diagnostics",
                    "json",
                    Some(report.metrics.len()),
                    None,
                )?);
            }
            if let Some(path) = &case.outputs.manifest_json {
                timing.total_wall_seconds = total_started.elapsed().as_secs_f64();
                let performance = timing.to_manifest(&output_entries);
                write_run_manifest(
                    path,
                    RunManifestContext {
                        case,
                        report: &report,
                        outputs: output_entries,
                        terrain_source: terrain_source.as_ref(),
                        release_zone: release_zone_manifest.as_ref(),
                        terrain_classes: terrain_class_manifest.as_ref(),
                        trajectory_metadata: None,
                        performance,
                    },
                )?;
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
    let terrain_started = Instant::now();
    let terrain = config.terrain.build()?;
    timing.terrain_load_seconds += terrain_started.elapsed().as_secs_f64();
    let class_provider = terrain_class_map
        .as_ref()
        .map(|class_map| class_map as &dyn ContactParameterProvider);
    let simulation_started = Instant::now();
    let result =
        config.run_with_terrain_and_contact_parameters(terrain.as_ref(), class_provider)?;
    timing.simulation_seconds += simulation_started.elapsed().as_secs_f64();
    timing.trajectory_count += 1;
    timing.impact_event_count += result.impact_events.len();
    trajectory_metadata.insert_single_result(case, &result, &config.block);
    if let Some(path) = &case.outputs.trajectory_csv {
        let output_started = Instant::now();
        write_trajectory_csv_with_id(path, default_single_trajectory_id(), &result.samples)?;
        timing.output_write_seconds += output_started.elapsed().as_secs_f64();
        output_entries.push(file_output_manifest(
            path,
            "trajectory",
            "csv",
            Some(result.samples.len()),
            None,
        )?);
    }
    if let Some(path) = &case.outputs.impact_events_csv {
        let output_started = Instant::now();
        write_impact_events_csv_with_id(
            path,
            default_single_trajectory_id(),
            &result.impact_events,
        )?;
        timing.output_write_seconds += output_started.elapsed().as_secs_f64();
        output_entries.push(file_output_manifest(
            path,
            "impact_events",
            "csv",
            Some(result.impact_events.len()),
            None,
        )?);
    }
    if let Some(path) = &case.outputs.impact_events_json {
        let output_started = Instant::now();
        io::write_impact_events_json(path, &result.impact_events)?;
        timing.output_write_seconds += output_started.elapsed().as_secs_f64();
        output_entries.push(file_output_manifest(
            path,
            "impact_events",
            "json",
            Some(result.impact_events.len()),
            None,
        )?);
    }

    let samples = &result.samples;
    let first = samples
        .first()
        .ok_or_else(|| ValidationError::EmptyTrajectory(case.case_id.clone()))?;
    let last = samples
        .last()
        .ok_or_else(|| ValidationError::EmptyTrajectory(case.case_id.clone()))?;

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
    compute_ensemble_metrics(
        case,
        class_provider,
        &mut metrics,
        &mut warnings,
        &mut output_entries,
        &mut timing,
        &mut trajectory_metadata,
    )?;
    compute_validation_ensemble_metrics(ValidationEnsembleContext {
        case,
        base_config: &config,
        contact_parameters: class_provider,
        observations: &observations,
        metrics: &mut metrics,
        warnings: &mut warnings,
        output_entries: &mut output_entries,
        timing: &mut timing,
        trajectory_metadata: &mut trajectory_metadata,
    })?;
    if let Some(source) = release_zone_source.as_ref() {
        release_zone_manifest = compute_release_zone_metrics(ReleaseZoneMetricContext {
            case,
            base_config: &config,
            contact_parameters: class_provider,
            release_zone: source,
            observations: &observations,
            metrics: &mut metrics,
            warnings: &mut warnings,
            output_entries: &mut output_entries,
            timing: &mut timing,
            trajectory_metadata: &mut trajectory_metadata,
        })?;
    }
    compute_observed_trajectory_metrics(
        case,
        &config,
        class_provider,
        &observations,
        &mut metrics,
    )?;
    compute_observed_contact_metrics(case, &config, class_provider, &observations, &mut metrics)?;
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

    let trajectory_metadata_manifest = if let Some(path) = &case.outputs.trajectory_metadata_csv {
        let rows = trajectory_metadata.rows();
        let output_started = Instant::now();
        write_trajectory_metadata_csv(path, &rows)?;
        timing.output_write_seconds += output_started.elapsed().as_secs_f64();
        output_entries.push(file_output_manifest(
            path,
            "trajectory_metadata",
            "csv",
            Some(rows.len()),
            None,
        )?);
        Some(TrajectoryMetadataManifest {
            schema_version: TRAJECTORY_METADATA_SCHEMA_VERSION.to_string(),
            path: path.to_string_lossy().to_string(),
            row_count: rows.len(),
            probability_model: default_probability_model().to_string(),
            probability_semantics: "sampling_weight_only".to_string(),
            normalization_convention: "unweighted_current_outputs".to_string(),
            total_sampling_weight: rows.iter().map(|row| row.sampling_weight).sum(),
        })
    } else {
        None
    };

    if let Some(path) = &case.outputs.diagnostics_json {
        let output_started = Instant::now();
        write_report(path, &report)?;
        timing.output_write_seconds += output_started.elapsed().as_secs_f64();
        output_entries.push(file_output_manifest(
            path,
            "diagnostics",
            "json",
            Some(report.metrics.len()),
            None,
        )?);
    }

    if let Some(path) = &case.outputs.manifest_json {
        timing.total_wall_seconds = total_started.elapsed().as_secs_f64();
        let performance = timing.to_manifest(&output_entries);
        write_run_manifest(
            path,
            RunManifestContext {
                case,
                report: &report,
                outputs: output_entries,
                terrain_source: terrain_source.as_ref(),
                release_zone: release_zone_manifest.as_ref(),
                terrain_classes: terrain_class_manifest.as_ref(),
                trajectory_metadata: trajectory_metadata_manifest,
                performance,
            },
        )?;
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

fn write_run_manifest(
    path: impl AsRef<Path>,
    context: RunManifestContext<'_>,
) -> Result<(), ValidationError> {
    let manifest = build_run_manifest(context);
    if let Some(parent) = path.as_ref().parent() {
        fs::create_dir_all(parent)?;
    }
    fs::write(path, serde_json::to_string_pretty(&manifest)?)?;
    Ok(())
}

fn build_run_manifest(context: RunManifestContext<'_>) -> RunManifest {
    let RunManifestContext {
        case,
        report,
        outputs,
        terrain_source,
        release_zone,
        terrain_classes,
        trajectory_metadata,
        performance,
    } = context;
    RunManifest {
        schema_version: RUN_MANIFEST_SCHEMA_VERSION.to_string(),
        created_unix_s: report.timestamp_unix_s,
        case_id: case.case_id.clone(),
        model_version: report.model_version.clone(),
        git_hash: report.git_hash.clone(),
        config_fingerprint: report.parameters.config_fingerprint().ok(),
        completion_status: case_status_text(report.status).to_string(),
        seed_policy: SeedPolicyManifest {
            global_seed: case.random.seed,
            ensemble_size: case.random.ensemble_size.max(1),
            derivation:
                "single trajectories use random.seed directly; ensembles derive trajectory seeds from global seed, case ID, and trajectory ID"
                    .to_string(),
        },
        terrain: terrain_manifest(&case.terrain, terrain_source),
        release_zone: release_zone.cloned(),
        terrain_classes: terrain_classes.cloned(),
        trajectory_metadata,
        outputs,
        performance: Some(performance),
        warnings: report.warnings.clone(),
    }
}

fn case_status_text(status: CaseStatus) -> &'static str {
    match status {
        CaseStatus::Passed => "passed",
        CaseStatus::Failed => "failed",
        CaseStatus::Skipped => "skipped",
    }
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
) -> TerrainClassManifest {
    let metadata = &class_map.metadata;
    TerrainClassManifest {
        layer_id: metadata.layer_id.clone(),
        metadata_path: config.map(|config| config.metadata_path.to_string_lossy().to_string()),
        class_grid_path: metadata.class_grid_path.to_string_lossy().to_string(),
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
            .map(|coverage| TerrainClassCoverageManifest {
                class_id: coverage.class_id,
                name: coverage.name,
                cell_count: coverage.cell_count,
                coverage_fraction: coverage.coverage_fraction,
            })
            .collect(),
        provenance_notes: metadata.provenance.notes.clone(),
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
        schema_version: None,
        row_count,
        skipped_empty_files,
        compression: None,
        row_group_count: None,
    })
}

fn warn_large_debug_outputs(
    case: &BenchmarkCase,
    expected_files: usize,
    warnings: &mut Vec<String>,
) {
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
    contact_parameters: Option<&dyn ContactParameterProvider>,
    metrics: &mut BTreeMap<String, f64>,
    warnings: &mut Vec<String>,
    output_entries: &mut Vec<OutputManifest>,
    timing: &mut RuntimeTiming,
    trajectory_metadata: &mut TrajectoryMetadataCollector,
) -> Result<(), ValidationError> {
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
    let ensemble = simulate_ensemble_with_contact_parameters(
        &ensemble_config,
        case.case_id.clone(),
        global_seed,
        &trajectory_ids,
        contact_parameters,
    )?;
    timing.simulation_seconds += simulation_started.elapsed().as_secs_f64();
    timing.record_runs(&ensemble.trajectories);
    for run in &ensemble.trajectories {
        trajectory_metadata.insert_run(
            case,
            run,
            run.summary.trajectory_id.clone(),
            default_manual_source_zone_id(),
            &ensemble_config.block,
        );
    }
    if case.observations.is_none() {
        warn_large_debug_outputs(case, ensemble_size, warnings);
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
            timing.output_write_seconds += output_started.elapsed().as_secs_f64();
        }
        if let Some(path) = &case.outputs.ensemble_impact_events_parquet {
            let output_started = Instant::now();
            output_entries.push(write_ensemble_impact_events_parquet(
                path,
                &ensemble.trajectories,
            )?);
            timing.output_write_seconds += output_started.elapsed().as_secs_f64();
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
    observations: &'a ObservationData,
    metrics: &'a mut BTreeMap<String, f64>,
    warnings: &'a mut Vec<String>,
    output_entries: &'a mut Vec<OutputManifest>,
    timing: &'a mut RuntimeTiming,
    trajectory_metadata: &'a mut TrajectoryMetadataCollector,
}

fn compute_validation_ensemble_metrics(
    context: ValidationEnsembleContext<'_>,
) -> Result<(), ValidationError> {
    let ValidationEnsembleContext {
        case,
        base_config,
        contact_parameters,
        observations,
        metrics,
        warnings,
        output_entries,
        timing,
        trajectory_metadata,
    } = context;
    if observations.release_points.is_empty() || observations.deposition_points.is_empty() {
        return Ok(());
    }

    let ensemble_size = case.random.ensemble_size.max(1);
    let expected_debug_files = observations.release_points.len() * ensemble_size;
    warn_large_debug_outputs(case, expected_debug_files, warnings);
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
            let simulation_started = Instant::now();
            let run = simulate_one_trajectory_with_terrain_and_contact_parameters(
                &release_config,
                request,
                terrain.as_ref(),
                contact_parameters,
            )?;
            timing.simulation_seconds += simulation_started.elapsed().as_secs_f64();
            timing.record_run(&run);
            deposition_rows.push(ensemble_deposition_row(&release.trajectory_id, &run));
            trajectory_metadata.insert_run(
                case,
                &run,
                release.trajectory_id.clone(),
                default_observed_source_zone_id(),
                &release_config.block,
            );
            runs.push(run);
        }
    }

    if let Some(path) = &case.outputs.ensemble_deposition_csv {
        let output_started = Instant::now();
        write_ensemble_deposition_csv(path, &deposition_rows)?;
        timing.output_write_seconds += output_started.elapsed().as_secs_f64();
        output_entries.push(file_output_manifest(
            path,
            "ensemble_deposition",
            "csv",
            Some(deposition_rows.len()),
            None,
        )?);
    }
    if let Some(dir) = &case.outputs.ensemble_trajectories_dir {
        let output_started = Instant::now();
        output_entries.push(write_ensemble_trajectory_dir(dir, &runs)?);
        timing.output_write_seconds += output_started.elapsed().as_secs_f64();
    }
    if let Some(dir) = &case.outputs.ensemble_impact_events_dir {
        let output_started = Instant::now();
        output_entries.push(write_ensemble_impact_events_dir(dir, &runs)?);
        timing.output_write_seconds += output_started.elapsed().as_secs_f64();
    }
    if let Some(path) = &case.outputs.ensemble_impact_events_parquet {
        let output_started = Instant::now();
        output_entries.push(write_ensemble_impact_events_parquet(path, &runs)?);
        timing.output_write_seconds += output_started.elapsed().as_secs_f64();
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

struct ReleaseZoneMetricContext<'a> {
    case: &'a BenchmarkCase,
    base_config: &'a SimulationConfig,
    contact_parameters: Option<&'a dyn ContactParameterProvider>,
    release_zone: &'a ReleaseZoneMetadata,
    observations: &'a ObservationData,
    metrics: &'a mut BTreeMap<String, f64>,
    warnings: &'a mut Vec<String>,
    output_entries: &'a mut Vec<OutputManifest>,
    timing: &'a mut RuntimeTiming,
    trajectory_metadata: &'a mut TrajectoryMetadataCollector,
}

fn compute_release_zone_metrics(
    context: ReleaseZoneMetricContext<'_>,
) -> Result<Option<ReleaseZoneManifest>, ValidationError> {
    let ReleaseZoneMetricContext {
        case,
        base_config,
        contact_parameters,
        release_zone,
        observations,
        metrics,
        warnings,
        output_entries,
        timing,
        trajectory_metadata,
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
    let mut generated_records = Vec::with_capacity(release_points.len());

    for point in &release_points {
        let z_m =
            terrain.height(point.x_m, point.y_m) + base_config.block.radius_m + point.z_offset_m;
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
        let run = simulate_one_trajectory_with_terrain_and_contact_parameters(
            &release_config,
            request,
            terrain.as_ref(),
            contact_parameters,
        )?;
        timing.simulation_seconds += simulation_started.elapsed().as_secs_f64();
        timing.record_run(&run);
        deposition_rows.push(ensemble_deposition_row(&point.release_id, &run));
        trajectory_metadata.insert_run(
            case,
            &run,
            point.release_id.clone(),
            release_zone.zone_id.clone(),
            &release_config.block,
        );
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
        timing.output_write_seconds += output_started.elapsed().as_secs_f64();
        output_entries.push(file_output_manifest(
            path,
            "release_zone_deposition",
            "csv",
            Some(deposition_rows.len()),
            None,
        )?);
    }
    if let Some(dir) = &case.outputs.ensemble_trajectories_dir {
        let output_started = Instant::now();
        output_entries.push(write_ensemble_trajectory_dir(dir, &runs)?);
        timing.output_write_seconds += output_started.elapsed().as_secs_f64();
    }
    if let Some(dir) = &case.outputs.ensemble_impact_events_dir {
        let output_started = Instant::now();
        output_entries.push(write_ensemble_impact_events_dir(dir, &runs)?);
        timing.output_write_seconds += output_started.elapsed().as_secs_f64();
    }
    if let Some(path) = &case.outputs.ensemble_impact_events_parquet {
        let output_started = Instant::now();
        output_entries.push(write_ensemble_impact_events_parquet(path, &runs)?);
        timing.output_write_seconds += output_started.elapsed().as_secs_f64();
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
    compute_deposition_cloud_metrics(&runs, observations, metrics, warnings);
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
    contact_parameters: Option<&dyn ContactParameterProvider>,
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
    let mut total_bytes = 0_u64;
    let mut row_count = 0_usize;
    for run in runs {
        let filename = format!("{}.csv", safe_filename(&run.summary.trajectory_id));
        let path = dir.as_ref().join(filename);
        write_trajectory_csv_with_id(&path, &run.summary.trajectory_id, &run.samples)?;
        total_bytes += fs::metadata(&path)?.len();
        row_count += run.samples.len();
    }
    Ok(OutputManifest {
        kind: "ensemble_trajectories".to_string(),
        format: "csv_directory".to_string(),
        path: dir.as_ref().to_string_lossy().to_string(),
        file_count: runs.len(),
        total_bytes,
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
    Ok(OutputManifest {
        kind: "ensemble_impact_events".to_string(),
        format: "csv_directory".to_string(),
        path: dir.as_ref().to_string_lossy().to_string(),
        file_count,
        total_bytes,
        schema_version: None,
        row_count: Some(row_count),
        skipped_empty_files: Some(skipped_empty_files),
        compression: None,
        row_group_count: None,
    })
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

#[cfg(test)]
mod tests {
    use super::*;

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
}
