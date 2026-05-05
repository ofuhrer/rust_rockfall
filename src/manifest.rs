//! Run manifest records for reproducible batch and hazard workflows.

use serde::{Deserialize, Serialize};

pub const RUN_MANIFEST_SCHEMA_VERSION: &str = "run_manifest_v1";

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct RunManifest {
    pub schema_version: String,
    pub created_unix_s: u64,
    pub case_id: String,
    pub model_version: String,
    pub git_hash: Option<String>,
    pub config_fingerprint: Option<String>,
    pub completion_status: String,
    pub seed_policy: SeedPolicyManifest,
    pub terrain: TerrainManifest,
    pub outputs: Vec<OutputManifest>,
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
    pub crs: Option<String>,
    pub vertical_datum: Option<String>,
    pub resolution_m: Option<f64>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct OutputManifest {
    pub kind: String,
    pub format: String,
    pub path: String,
    pub file_count: usize,
    pub total_bytes: u64,
    pub row_count: Option<usize>,
    pub skipped_empty_files: Option<usize>,
}
