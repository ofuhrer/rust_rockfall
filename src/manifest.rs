//! Run manifest records for reproducible batch and hazard workflows.

use crate::simulation::{LocalParallelEnsembleExecution, StopStateProvenance};
use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;

pub const RUN_MANIFEST_SCHEMA_VERSION: &str = "run_manifest_v1";
pub const STOP_STATE_SUMMARY_SCHEMA_VERSION: &str = "stop_state_summary_v3";
pub const TERRAIN_MATERIAL_EXPOSURE_SUMMARY_SCHEMA_VERSION: &str =
    "terrain_material_exposure_summary_v1";

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct RunManifest {
    pub schema_version: String,
    pub created_unix_s: u64,
    pub case_id: String,
    pub model_version: String,
    pub git_hash: Option<String>,
    pub config_fingerprint: Option<String>,
    pub completion_status: String,
    #[serde(default = "default_execution_status")]
    pub execution_status: String,
    #[serde(default = "default_scientific_status")]
    pub scientific_status: String,
    pub seed_policy: SeedPolicyManifest,
    pub terrain: TerrainManifest,
    pub release_zone: Option<ReleaseZoneManifest>,
    pub terrain_classes: Option<TerrainClassManifest>,
    #[serde(default)]
    pub shape_metadata: Option<ShapeMetadataManifest>,
    #[serde(default)]
    pub trajectory_metadata: Option<TrajectoryMetadataManifest>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub ensemble_execution: Option<LocalParallelEnsembleExecution>,
    pub outputs: Vec<OutputManifest>,
    #[serde(default)]
    pub performance: Option<PerformanceManifest>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub stop_state: Option<StopStateProvenance>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub stop_state_summary: Option<StopStateSummaryManifest>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub terrain_material_exposure_summary: Option<TerrainMaterialExposureSummaryManifest>,
    pub warnings: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct SeedPolicyManifest {
    pub global_seed: Option<u64>,
    pub ensemble_size: usize,
    pub derivation: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct TerrainManifest {
    pub terrain_type: String,
    pub path: Option<String>,
    pub metadata_path: Option<String>,
    pub crs: Option<String>,
    pub epsg: Option<u32>,
    pub vertical_datum: Option<String>,
    pub resolution_m: Option<f64>,
    pub extent: Option<TerrainExtentManifest>,
    pub nodata: Option<f64>,
    pub source_dataset: Option<String>,
    pub source_product: Option<String>,
    pub source_url: Option<String>,
    pub source_filename: Option<String>,
    pub license: Option<String>,
    pub download_status: Option<String>,
    pub preprocessing_status: Option<String>,
    pub raw_sha256: Option<String>,
    pub processed_sha256: Option<String>,
    pub provenance_notes: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct TerrainExtentManifest {
    pub xmin: f64,
    pub ymin: f64,
    pub xmax: f64,
    pub ymax: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ReleaseZoneManifest {
    pub zone_id: String,
    pub metadata_path: Option<String>,
    pub crs: String,
    pub epsg: u32,
    pub vertical_datum: String,
    pub sampling_mode: String,
    pub seed: u64,
    pub requested_release_points: usize,
    pub generated_release_points: usize,
    pub extent: TerrainExtentManifest,
    pub area_m2: f64,
    pub source_dataset: String,
    pub source_url: Option<String>,
    pub license: String,
    pub provenance_notes: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct TerrainClassManifest {
    #[serde(default = "default_terrain_class_manifest_schema_version")]
    pub schema_version: String,
    #[serde(default)]
    pub metadata_schema_version: Option<u32>,
    pub layer_id: String,
    pub metadata_path: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub metadata_sha256: Option<String>,
    pub class_grid_path: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub class_grid_sha256: Option<String>,
    pub crs: String,
    pub epsg: u32,
    pub vertical_datum: String,
    pub resolution_m: f64,
    pub extent: TerrainExtentManifest,
    pub nodata: Option<f64>,
    pub source_dataset: String,
    pub source_url: Option<String>,
    pub license: String,
    pub class_coverage: Vec<TerrainClassCoverageManifest>,
    pub provenance_notes: Vec<String>,
}

fn default_terrain_class_manifest_schema_version() -> String {
    "terrain_class_manifest_v1".to_string()
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct TerrainClassCoverageManifest {
    pub class_id: i32,
    pub name: String,
    pub cell_count: usize,
    pub coverage_fraction: f64,
    #[serde(default)]
    pub active_parameter_override_count: usize,
    #[serde(default)]
    pub active_parameter_override_fields: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ShapeMetadataManifest {
    pub schema_version: String,
    pub metadata_path: Option<String>,
    pub shape_id: String,
    pub shape_type: String,
    pub shape_class: String,
    pub active_contact_shape: String,
    pub active_contact_radius_m: f64,
    pub mass_kg: f64,
    pub density_kgpm3: Option<f64>,
    pub equivalent_radius_m: Option<f64>,
    pub principal_lengths_m: Option<[f64; 3]>,
    pub principal_moments_kg_m2: [f64; 3],
    pub orientation_initialization_mode: String,
    pub initial_quaternion_wxyz: [f64; 4],
    pub source_dataset: Option<String>,
    pub source_record_id: Option<String>,
    pub source_url_or_doi: Option<String>,
    pub license: Option<String>,
    pub provenance_notes: Vec<String>,
    pub warnings: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct TrajectoryMetadataManifest {
    pub schema_version: String,
    pub path: String,
    pub row_count: usize,
    #[serde(default = "default_probability_model")]
    pub probability_model: String,
    #[serde(default = "default_probability_semantics")]
    pub probability_semantics: String,
    #[serde(default = "default_normalization_convention")]
    pub normalization_convention: String,
    pub total_sampling_weight: f64,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub map_product_id: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub source_zone_id: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub source_zone_metadata_path: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub scenario_table_path: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub scenario_id: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub probability_mode: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub normalization_scope: Option<String>,
}

fn default_probability_model() -> String {
    "unweighted".to_string()
}

fn default_probability_semantics() -> String {
    "sampling_weight_only".to_string()
}

fn default_normalization_convention() -> String {
    "unweighted_current_outputs".to_string()
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct OutputManifest {
    pub kind: String,
    pub format: String,
    pub path: String,
    pub file_count: usize,
    pub total_bytes: u64,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub sha256: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub schema_version: Option<String>,
    pub row_count: Option<usize>,
    pub skipped_empty_files: Option<usize>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub compression: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub row_group_count: Option<usize>,
}

fn default_execution_status() -> String {
    "unknown".to_string()
}

fn default_scientific_status() -> String {
    "unknown".to_string()
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct PerformanceManifest {
    pub total_wall_seconds: f64,
    pub terrain_load_seconds: f64,
    pub release_generation_seconds: f64,
    pub simulation_seconds: f64,
    pub output_write_seconds: f64,
    pub hazard_layer_seconds: Option<f64>,
    pub trajectory_count: usize,
    pub impact_event_count: usize,
    pub output_file_count: usize,
    pub output_bytes: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct StopStateSummaryManifest {
    pub schema_version: String,
    pub path: Option<String>,
    pub trajectory_count: usize,
    pub explicit_stop_state_count: usize,
    pub stop_reason_counts: BTreeMap<String, usize>,
    pub final_contact_state_counts: BTreeMap<String, usize>,
    pub low_energy_contact_count_total: usize,
    #[serde(default)]
    pub significant_impact_count_total: usize,
    pub terrain_slope_available_count: usize,
    pub final_speed_mean_mps: Option<f64>,
    pub final_speed_max_mps: Option<f64>,
    pub final_kinetic_mean_j: Option<f64>,
    pub final_kinetic_max_j: Option<f64>,
    #[serde(default)]
    pub terrain_material_context_available_count: usize,
    #[serde(default)]
    pub final_terrain_class_counts: BTreeMap<String, usize>,
    #[serde(default)]
    pub last_significant_impact_terrain_class_counts: BTreeMap<String, usize>,
    #[serde(default)]
    pub significant_impact_terrain_class_counts: BTreeMap<String, usize>,
    #[serde(default)]
    pub significant_impact_terrain_class_unavailable_count: usize,
    pub limitations: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct TerrainMaterialExposureSummaryManifest {
    pub schema_version: String,
    pub path: Option<String>,
    pub row_count: usize,
    pub trajectory_count: usize,
    pub classified_sample_count: usize,
    pub unavailable_sample_count: usize,
    pub class_summaries: Vec<TerrainMaterialExposureClassSummaryManifest>,
    pub limitations: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct TerrainMaterialExposureClassSummaryManifest {
    pub terrain_class_label: String,
    pub trajectory_count: usize,
    pub sample_count: usize,
    pub duration_s: f64,
    pub path_length_m: f64,
    pub contact_sample_count: usize,
    pub contact_duration_s: f64,
    pub contact_path_length_m: f64,
}
