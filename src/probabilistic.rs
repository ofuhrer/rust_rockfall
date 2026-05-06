//! Metadata contracts for probabilistic hazard-map semantics.
//!
//! This module validates Phase 1 source-zone, scenario-table, and map-package
//! metadata only. It does not alter simulation physics, hazard accumulation, or
//! existing diagnostic output semantics.

use serde::{Deserialize, Serialize};
use std::{
    fs,
    path::{Path, PathBuf},
};
use thiserror::Error;

pub const SOURCE_ZONE_METADATA_SCHEMA_VERSION: &str = "source_zone_metadata_v1";
pub const SCENARIO_TABLE_SCHEMA_VERSION: &str = "scenario_table_v1";
pub const MAP_PACKAGE_MANIFEST_SCHEMA_VERSION: &str = "map_package_manifest_v1";

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum ProbabilityMode {
    UnweightedDiagnostic,
    SamplingWeightedConditional,
    PhysicalProbability,
    AnnualFrequency,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum NormalizationScope {
    ConditionedOnFilter,
    ConditionedOnScenario,
    AbsoluteProbabilityMass,
    AnnualFrequencySum,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct SourceZoneMetadata {
    pub schema_version: String,
    pub source_zone_id: String,
    pub crs_epsg: u32,
    pub vertical_datum: String,
    pub geometry: SourceZoneGeometry,
    pub release_sampling_policy: ReleaseSamplingPolicy,
    pub provenance: SourceZoneProvenance,
    #[serde(default)]
    pub annual_release_frequency_per_year: Option<f64>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct SourceZoneGeometry {
    #[serde(rename = "type")]
    pub geometry_type: String,
    pub vertices: Vec<[f64; 2]>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ReleaseSamplingPolicy {
    pub mode: String,
    #[serde(default)]
    pub seed: Option<u64>,
    #[serde(default)]
    pub release_count: Option<usize>,
    #[serde(default)]
    pub release_cell_id_prefix: Option<String>,
}

#[derive(Debug, Clone, Default, Serialize, Deserialize, PartialEq)]
pub struct SourceZoneProvenance {
    #[serde(default)]
    pub source: Option<String>,
    #[serde(default)]
    pub license: Option<String>,
    #[serde(default)]
    pub notes: Vec<String>,
}

#[derive(Debug, Clone, PartialEq)]
pub struct ScenarioTable {
    pub schema_version: String,
    pub rows: Vec<ScenarioRow>,
}

#[derive(Debug, Clone, Deserialize, Serialize, PartialEq)]
pub struct ScenarioRow {
    pub scenario_id: String,
    pub source_zone_id: String,
    pub release_sampling_policy: String,
    pub model_configuration_id: String,
    pub terrain_material_assumption_id: String,
    pub sampling_weight: f64,
    #[serde(default)]
    pub block_scenario_id: Option<String>,
    #[serde(default)]
    pub block_size_class: Option<String>,
    #[serde(default)]
    pub block_shape_class: Option<String>,
    #[serde(default)]
    pub block_radius_m: Option<f64>,
    #[serde(default)]
    pub block_mass_kg: Option<f64>,
    #[serde(default)]
    pub block_density_kgpm3: Option<f64>,
    #[serde(default)]
    pub release_probability: Option<f64>,
    #[serde(default)]
    pub scenario_probability: Option<f64>,
    #[serde(default)]
    pub annual_frequency_per_year: Option<f64>,
    #[serde(default)]
    pub time_horizon_years: Option<f64>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct MapPackageManifest {
    pub schema_version: String,
    pub map_product_id: String,
    #[serde(default)]
    pub map_product_version: Option<String>,
    pub probability_mode: ProbabilityMode,
    #[serde(default)]
    pub normalization_scope: Option<NormalizationScope>,
    pub source_zone_id: String,
    pub source_zone_metadata_path: PathBuf,
    #[serde(default)]
    pub scenario_table_path: Option<PathBuf>,
    #[serde(default)]
    pub hazard_manifest_paths: Vec<PathBuf>,
    #[serde(default)]
    pub raster_outputs: Vec<MapRasterOutput>,
    #[serde(default)]
    pub layer_semantics: Vec<MapLayerSemantics>,
    #[serde(default)]
    pub validation_context: Vec<String>,
    #[serde(default)]
    pub limitations: Vec<String>,
    #[serde(default)]
    pub operational_status: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct MapLayerSemantics {
    pub layer_name: String,
    #[serde(default)]
    pub units: Option<String>,
    #[serde(default)]
    pub conditioned_on: Vec<String>,
    #[serde(default)]
    pub is_annualized: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct MapRasterOutput {
    pub layer_name: String,
    pub format: String,
    pub path: PathBuf,
    #[serde(default)]
    pub sha256: Option<String>,
    #[serde(default)]
    pub total_bytes: Option<u64>,
    #[serde(default)]
    pub cloud_optimized: bool,
    #[serde(default)]
    pub is_annualized: bool,
}

#[derive(Debug, Error)]
pub enum ProbabilisticMetadataError {
    #[error("failed to read probabilistic metadata: {0}")]
    Read(#[from] std::io::Error),
    #[error("failed to parse probabilistic metadata YAML: {0}")]
    Yaml(#[from] serde_yaml::Error),
    #[error("failed to parse probabilistic metadata JSON: {0}")]
    Json(#[from] serde_json::Error),
    #[error("failed to parse probabilistic scenario CSV: {0}")]
    Csv(#[from] csv::Error),
    #[error("probabilistic metadata field {field} is invalid: {reason}")]
    Invalid { field: &'static str, reason: String },
}

impl SourceZoneMetadata {
    pub fn from_yaml_file(path: impl AsRef<Path>) -> Result<Self, ProbabilisticMetadataError> {
        let text = fs::read_to_string(path)?;
        Self::from_yaml_str(&text)
    }

    pub fn from_yaml_str(text: &str) -> Result<Self, ProbabilisticMetadataError> {
        let metadata: Self = serde_yaml::from_str(text)?;
        metadata.validate()?;
        Ok(metadata)
    }

    pub fn validate(&self) -> Result<(), ProbabilisticMetadataError> {
        ensure(
            self.schema_version == SOURCE_ZONE_METADATA_SCHEMA_VERSION,
            "schema_version",
            format!("expected {SOURCE_ZONE_METADATA_SCHEMA_VERSION}"),
        )?;
        validate_stable_id(&self.source_zone_id, "source_zone_id")?;
        ensure(
            self.crs_epsg > 0,
            "crs_epsg",
            "must be a positive EPSG code",
        )?;
        ensure(
            !self.vertical_datum.trim().is_empty(),
            "vertical_datum",
            "must be set",
        )?;
        ensure(
            self.geometry.geometry_type == "polygon",
            "geometry.type",
            "Phase 1 supports polygon source zones",
        )?;
        ensure(
            self.geometry.vertices.len() >= 3,
            "geometry.vertices",
            "polygon must have at least three vertices",
        )?;
        for vertex in &self.geometry.vertices {
            ensure(
                vertex[0].is_finite() && vertex[1].is_finite(),
                "geometry.vertices",
                "all vertices must be finite",
            )?;
        }
        ensure(
            polygon_area_m2(&self.geometry.vertices).abs() > 1.0e-9,
            "geometry.vertices",
            "polygon area must be positive",
        )?;
        ensure(
            !self.release_sampling_policy.mode.trim().is_empty(),
            "release_sampling_policy.mode",
            "must be set",
        )?;
        if let Some(count) = self.release_sampling_policy.release_count {
            ensure(
                count > 0,
                "release_sampling_policy.release_count",
                "must be greater than zero when present",
            )?;
        }
        if let Some(prefix) = &self.release_sampling_policy.release_cell_id_prefix {
            validate_stable_id(prefix, "release_sampling_policy.release_cell_id_prefix")?;
        }
        validate_optional_nonnegative(
            self.annual_release_frequency_per_year,
            "annual_release_frequency_per_year",
        )?;
        Ok(())
    }
}

impl ScenarioTable {
    pub fn from_csv_file(path: impl AsRef<Path>) -> Result<Self, ProbabilisticMetadataError> {
        let mut reader = csv::Reader::from_path(path)?;
        let mut rows = Vec::new();
        for row in reader.deserialize() {
            rows.push(row?);
        }
        let table = Self {
            schema_version: SCENARIO_TABLE_SCHEMA_VERSION.to_string(),
            rows,
        };
        table.validate_base()?;
        Ok(table)
    }

    pub fn validate_base(&self) -> Result<(), ProbabilisticMetadataError> {
        ensure(
            self.schema_version == SCENARIO_TABLE_SCHEMA_VERSION,
            "schema_version",
            format!("expected {SCENARIO_TABLE_SCHEMA_VERSION}"),
        )?;
        ensure(
            !self.rows.is_empty(),
            "rows",
            "scenario table must not be empty",
        )?;
        for (index, row) in self.rows.iter().enumerate() {
            row.validate_base(index)?;
        }
        Ok(())
    }

    pub fn source_zone_ids(&self) -> impl Iterator<Item = &str> {
        self.rows.iter().map(|row| row.source_zone_id.as_str())
    }

    pub fn total_sampling_weight(&self) -> f64 {
        self.rows.iter().map(|row| row.sampling_weight).sum()
    }

    fn validate_for_mode(
        &self,
        mode: ProbabilityMode,
        normalization_scope: Option<NormalizationScope>,
    ) -> Result<(), ProbabilisticMetadataError> {
        self.validate_base()?;
        match mode {
            ProbabilityMode::UnweightedDiagnostic => {
                for (index, row) in self.rows.iter().enumerate() {
                    ensure(
                        !row.has_physical_probability(),
                        "scenario_table",
                        format!(
                            "row {index} has physical probability fields but mode is unweighted_diagnostic"
                        ),
                    )?;
                    ensure(
                        !row.has_annual_frequency_fields(),
                        "scenario_table",
                        format!(
                            "row {index} has annual-frequency fields but mode is unweighted_diagnostic"
                        ),
                    )?;
                }
            }
            ProbabilityMode::SamplingWeightedConditional => {
                ensure(
                    matches!(
                        normalization_scope,
                        Some(
                            NormalizationScope::ConditionedOnFilter
                                | NormalizationScope::ConditionedOnScenario
                        )
                    ),
                    "normalization_scope",
                    "sampling_weighted_conditional requires conditioned_on_filter or conditioned_on_scenario",
                )?;
                ensure(
                    self.total_sampling_weight().is_finite() && self.total_sampling_weight() > 0.0,
                    "sampling_weight",
                    "sampling_weighted_conditional requires positive total filtered weight",
                )?;
                for (index, row) in self.rows.iter().enumerate() {
                    ensure(
                        !row.has_physical_probability(),
                        "scenario_table",
                        format!(
                            "row {index} has release_probability/scenario_probability; sampling_weight is the only active Phase 1 weight"
                        ),
                    )?;
                    ensure(
                        !row.has_annual_frequency_fields(),
                        "scenario_table",
                        format!(
                            "row {index} has annual-frequency fields; Level 3 annual_frequency support is required"
                        ),
                    )?;
                }
            }
            ProbabilityMode::PhysicalProbability => {
                ensure(
                    matches!(
                        normalization_scope,
                        Some(
                            NormalizationScope::ConditionedOnFilter
                                | NormalizationScope::ConditionedOnScenario
                                | NormalizationScope::AbsoluteProbabilityMass
                        )
                    ),
                    "normalization_scope",
                    "physical_probability requires an explicit non-annual normalization scope",
                )?;
                for (index, row) in self.rows.iter().enumerate() {
                    ensure(
                        row.has_physical_probability(),
                        "scenario_table",
                        format!(
                            "row {index} requires release_probability or scenario_probability for physical_probability"
                        ),
                    )?;
                    ensure(
                        !(row.release_probability.is_some() && row.scenario_probability.is_some()),
                        "scenario_table",
                        format!(
                            "row {index} has both release_probability and scenario_probability; choose one active physical probability column"
                        ),
                    )?;
                    ensure(
                        !row.has_annual_frequency_fields(),
                        "scenario_table",
                        format!(
                            "row {index} has annual-frequency fields but mode is physical_probability"
                        ),
                    )?;
                }
            }
            ProbabilityMode::AnnualFrequency => {
                return Err(ProbabilisticMetadataError::Invalid {
                    field: "probability_mode",
                    reason: "annual_frequency is schema-visible but unsupported in Phase 1; Level 3 temporal/source-frequency semantics are required".to_string(),
                });
            }
        }
        Ok(())
    }
}

impl ScenarioRow {
    fn validate_base(&self, index: usize) -> Result<(), ProbabilisticMetadataError> {
        validate_stable_id(&self.scenario_id, "scenario_id")?;
        validate_stable_id(&self.source_zone_id, "source_zone_id")?;
        ensure(
            !self.release_sampling_policy.trim().is_empty(),
            "release_sampling_policy",
            format!("row {index} must set release_sampling_policy"),
        )?;
        validate_stable_id(&self.model_configuration_id, "model_configuration_id")?;
        validate_stable_id(
            &self.terrain_material_assumption_id,
            "terrain_material_assumption_id",
        )?;
        ensure(
            self.sampling_weight.is_finite() && self.sampling_weight >= 0.0,
            "sampling_weight",
            format!("row {index} must use nonnegative finite sampling_weight"),
        )?;
        validate_optional_stable_id(&self.block_scenario_id, "block_scenario_id")?;
        validate_optional_stable_id(&self.block_size_class, "block_size_class")?;
        validate_optional_stable_id(&self.block_shape_class, "block_shape_class")?;
        validate_optional_positive(self.block_radius_m, "block_radius_m")?;
        validate_optional_positive(self.block_mass_kg, "block_mass_kg")?;
        validate_optional_positive(self.block_density_kgpm3, "block_density_kgpm3")?;
        validate_optional_unit_interval(self.release_probability, "release_probability")?;
        validate_optional_unit_interval(self.scenario_probability, "scenario_probability")?;
        validate_optional_nonnegative(self.annual_frequency_per_year, "annual_frequency_per_year")?;
        validate_optional_positive(self.time_horizon_years, "time_horizon_years")?;
        Ok(())
    }

    fn has_physical_probability(&self) -> bool {
        self.release_probability.is_some() || self.scenario_probability.is_some()
    }

    fn has_annual_frequency_fields(&self) -> bool {
        self.annual_frequency_per_year.is_some() || self.time_horizon_years.is_some()
    }
}

impl MapPackageManifest {
    pub fn from_file(path: impl AsRef<Path>) -> Result<Self, ProbabilisticMetadataError> {
        let path = path.as_ref();
        let text = fs::read_to_string(path)?;
        match path.extension().and_then(|extension| extension.to_str()) {
            Some("json") => Self::from_json_str(&text),
            _ => Self::from_yaml_str(&text),
        }
    }

    pub fn from_json_str(text: &str) -> Result<Self, ProbabilisticMetadataError> {
        let manifest: Self = serde_json::from_str(text)?;
        manifest.validate_base()?;
        Ok(manifest)
    }

    pub fn from_yaml_str(text: &str) -> Result<Self, ProbabilisticMetadataError> {
        let manifest: Self = serde_yaml::from_str(text)?;
        manifest.validate_base()?;
        Ok(manifest)
    }

    pub fn validate_base(&self) -> Result<(), ProbabilisticMetadataError> {
        ensure(
            self.schema_version == MAP_PACKAGE_MANIFEST_SCHEMA_VERSION,
            "schema_version",
            format!("expected {MAP_PACKAGE_MANIFEST_SCHEMA_VERSION}"),
        )?;
        validate_stable_id(&self.map_product_id, "map_product_id")?;
        validate_stable_id(&self.source_zone_id, "source_zone_id")?;
        ensure(
            !self.source_zone_metadata_path.as_os_str().is_empty(),
            "source_zone_metadata_path",
            "Level 1+ map packages require source_zone_metadata_path",
        )?;
        if let Some(scope) = self.normalization_scope {
            ensure(
                self.probability_mode != ProbabilityMode::UnweightedDiagnostic
                    || !matches!(
                        scope,
                        NormalizationScope::AbsoluteProbabilityMass
                            | NormalizationScope::AnnualFrequencySum
                    ),
                "normalization_scope",
                "unweighted_diagnostic must not use physical or annual normalization scopes",
            )?;
        }
        for layer in &self.layer_semantics {
            layer.validate(self.probability_mode)?;
        }
        for output in &self.raster_outputs {
            output.validate(self.probability_mode)?;
        }
        Ok(())
    }

    pub fn validate_with_metadata(
        &self,
        source_zone: &SourceZoneMetadata,
        scenario_table: Option<&ScenarioTable>,
    ) -> Result<(), ProbabilisticMetadataError> {
        self.validate_base()?;
        ensure(
            self.source_zone_id == source_zone.source_zone_id,
            "source_zone_id",
            format!(
                "map package source_zone_id '{}' does not match source metadata '{}'",
                self.source_zone_id, source_zone.source_zone_id
            ),
        )?;
        if let Some(table) = scenario_table {
            table.validate_for_mode(self.probability_mode, self.normalization_scope)?;
            for id in table.source_zone_ids() {
                ensure(
                    id == source_zone.source_zone_id,
                    "scenario_table.source_zone_id",
                    format!(
                        "scenario table source_zone_id '{id}' does not match source metadata '{}'",
                        source_zone.source_zone_id
                    ),
                )?;
            }
        }
        match self.probability_mode {
            ProbabilityMode::UnweightedDiagnostic => {
                ensure(
                    self.scenario_table_path.is_none() || scenario_table.is_some(),
                    "scenario_table_path",
                    "scenario_table_path was provided but no scenario table was supplied for validation",
                )?;
            }
            ProbabilityMode::SamplingWeightedConditional
            | ProbabilityMode::PhysicalProbability
            | ProbabilityMode::AnnualFrequency => {
                ensure(
                    self.scenario_table_path.is_some(),
                    "scenario_table_path",
                    "Level 2+ probability modes require scenario_table_path",
                )?;
                ensure(
                    scenario_table.is_some(),
                    "scenario_table",
                    "Level 2+ probability modes require a parsed scenario table",
                )?;
            }
        }
        if self.probability_mode == ProbabilityMode::AnnualFrequency {
            return Err(ProbabilisticMetadataError::Invalid {
                field: "probability_mode",
                reason: "annual_frequency is schema-visible but unsupported in Phase 1; Level 3 temporal/source-frequency semantics are required".to_string(),
            });
        }
        Ok(())
    }
}

impl MapLayerSemantics {
    fn validate(&self, mode: ProbabilityMode) -> Result<(), ProbabilisticMetadataError> {
        ensure(
            !self.layer_name.trim().is_empty(),
            "layer_semantics.layer_name",
            "must be set",
        )?;
        let layer_name = self.layer_name.to_ascii_lowercase();
        let units = self
            .units
            .as_deref()
            .unwrap_or_default()
            .to_ascii_lowercase();
        if mode == ProbabilityMode::UnweightedDiagnostic {
            ensure(
                !self.is_annualized
                    && !layer_name.contains("annual")
                    && !layer_name.contains("physical_probability")
                    && units != "1/year",
                "layer_semantics",
                "unweighted_diagnostic must not be labelled annualized or physical probability",
            )?;
        }
        if self.is_annualized || layer_name.contains("annual") || units == "1/year" {
            ensure(
                mode == ProbabilityMode::AnnualFrequency,
                "layer_semantics",
                "annualized layer labels require probability_mode annual_frequency",
            )?;
        }
        Ok(())
    }
}

impl MapRasterOutput {
    fn validate(&self, mode: ProbabilityMode) -> Result<(), ProbabilisticMetadataError> {
        ensure(
            !self.layer_name.trim().is_empty(),
            "raster_outputs.layer_name",
            "must be set",
        )?;
        ensure(
            !self.format.trim().is_empty(),
            "raster_outputs.format",
            "must be set",
        )?;
        ensure(
            !self.path.as_os_str().is_empty(),
            "raster_outputs.path",
            "must be set",
        )?;
        if self.is_annualized {
            ensure(
                mode == ProbabilityMode::AnnualFrequency,
                "raster_outputs.is_annualized",
                "annualized raster outputs require probability_mode annual_frequency",
            )?;
        }
        Ok(())
    }
}

fn validate_stable_id(value: &str, field: &'static str) -> Result<(), ProbabilisticMetadataError> {
    ensure(!value.trim().is_empty(), field, "must be set")?;
    ensure(
        value
            .chars()
            .all(|ch| ch.is_ascii_alphanumeric() || matches!(ch, '_' | '-' | '.' | ':' | '/')),
        field,
        "must be a stable id using ASCII letters, numbers, '_', '-', '.', ':', or '/'",
    )
}

fn validate_optional_stable_id(
    value: &Option<String>,
    field: &'static str,
) -> Result<(), ProbabilisticMetadataError> {
    if let Some(value) = value {
        validate_stable_id(value, field)?;
    }
    Ok(())
}

fn validate_optional_positive(
    value: Option<f64>,
    field: &'static str,
) -> Result<(), ProbabilisticMetadataError> {
    if let Some(value) = value {
        ensure(
            value.is_finite() && value > 0.0,
            field,
            "must be positive and finite",
        )?;
    }
    Ok(())
}

fn validate_optional_nonnegative(
    value: Option<f64>,
    field: &'static str,
) -> Result<(), ProbabilisticMetadataError> {
    if let Some(value) = value {
        ensure(
            value.is_finite() && value >= 0.0,
            field,
            "must be nonnegative and finite",
        )?;
    }
    Ok(())
}

fn validate_optional_unit_interval(
    value: Option<f64>,
    field: &'static str,
) -> Result<(), ProbabilisticMetadataError> {
    if let Some(value) = value {
        ensure(
            value.is_finite() && (0.0..=1.0).contains(&value),
            field,
            "must be finite and in [0, 1]",
        )?;
    }
    Ok(())
}

fn polygon_area_m2(points: &[[f64; 2]]) -> f64 {
    if points.len() < 3 {
        return 0.0;
    }
    let mut area2 = 0.0;
    for index in 0..points.len() {
        let next = (index + 1) % points.len();
        area2 += points[index][0] * points[next][1] - points[next][0] * points[index][1];
    }
    0.5 * area2
}

fn ensure(
    condition: bool,
    field: &'static str,
    reason: impl Into<String>,
) -> Result<(), ProbabilisticMetadataError> {
    if condition {
        Ok(())
    } else {
        Err(ProbabilisticMetadataError::Invalid {
            field,
            reason: reason.into(),
        })
    }
}
