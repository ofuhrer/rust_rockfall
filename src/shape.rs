//! Passive block-shape metadata and mass-property diagnostics.
//!
//! Shape metadata is currently descriptive only. Contact and dynamics continue
//! to use the active spherical block unless a future opt-in contact model
//! explicitly says otherwise.

use crate::geometry::SphereBlock;
use serde::{Deserialize, Serialize};
use std::{fs, path::Path};
use thiserror::Error;

pub const SHAPE_METADATA_SCHEMA_VERSION: &str = "shape_metadata_v1";
pub const PASSIVE_SHAPE_WARNING: &str =
    "Shape metadata is passive; active contact and dynamics remain spherical.";

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct BlockShapeMetadata {
    pub schema_version: String,
    pub shape_id: String,
    #[serde(rename = "shape_type")]
    pub shape_type: BlockShapeType,
    #[serde(default)]
    pub shape_class: Option<String>,
    pub dimensions_m: ShapeDimensions,
    pub mass_properties: ShapeMassProperties,
    #[serde(default)]
    pub orientation: ShapeOrientation,
    #[serde(default)]
    pub provenance: ShapeProvenance,
}

impl BlockShapeMetadata {
    pub fn from_yaml_file(path: impl AsRef<Path>) -> Result<Self, ShapeMetadataError> {
        let text = fs::read_to_string(path)?;
        let metadata: Self = serde_yaml::from_str(&text)?;
        metadata.validate()?;
        Ok(metadata)
    }

    pub fn validate(&self) -> Result<(), ShapeMetadataError> {
        if self.schema_version != SHAPE_METADATA_SCHEMA_VERSION {
            return Err(ShapeMetadataError::Invalid(format!(
                "unsupported shape metadata schema_version {}; expected {SHAPE_METADATA_SCHEMA_VERSION}",
                self.schema_version
            )));
        }
        if self.shape_id.trim().is_empty() {
            return Err(ShapeMetadataError::Invalid(
                "shape_id must not be empty".to_string(),
            ));
        }
        self.mass_properties.validate()?;
        self.dimensions_m.validate_for(self.shape_type)?;
        self.orientation.validate()?;
        self.computed_principal_moments_kg_m2()?;
        Ok(())
    }

    pub fn validate_against_block(&self, block: &SphereBlock) -> Result<(), ShapeMetadataError> {
        self.validate()?;
        ensure_close(
            self.mass_properties.mass_kg,
            block.mass_kg,
            "mass_properties.mass_kg",
            "block.mass",
        )?;
        if let Some(radius_m) = self
            .dimensions_m
            .active_equivalent_radius_m(self.shape_type)
        {
            ensure_close(
                radius_m,
                block.radius_m,
                "shape equivalent radius",
                "block.radius",
            )?;
        }
        Ok(())
    }

    pub fn computed_principal_moments_kg_m2(&self) -> Result<[f64; 3], ShapeMetadataError> {
        let mass_kg = self.mass_properties.mass_kg;
        match self.shape_type {
            BlockShapeType::Sphere => {
                let radius_m = self.dimensions_m.radius_m.ok_or_else(|| {
                    ShapeMetadataError::Invalid("sphere requires dimensions_m.radius_m".to_string())
                })?;
                Ok(sphere_principal_moments_kg_m2(mass_kg, radius_m))
            }
            BlockShapeType::Ellipsoid => {
                let axes = self.dimensions_m.semi_axes_m.ok_or_else(|| {
                    ShapeMetadataError::Invalid(
                        "ellipsoid requires dimensions_m.semi_axes_m".to_string(),
                    )
                })?;
                Ok(ellipsoid_principal_moments_kg_m2(mass_kg, axes))
            }
            BlockShapeType::Box => {
                let lengths = self.dimensions_m.side_lengths_m.ok_or_else(|| {
                    ShapeMetadataError::Invalid(
                        "box requires dimensions_m.side_lengths_m".to_string(),
                    )
                })?;
                Ok(box_principal_moments_kg_m2(mass_kg, lengths))
            }
            BlockShapeType::PrincipalDimensions => {
                let lengths = self.dimensions_m.principal_lengths_m.ok_or_else(|| {
                    ShapeMetadataError::Invalid(
                        "principal_dimensions requires dimensions_m.principal_lengths_m"
                            .to_string(),
                    )
                })?;
                match self.mass_properties.mass_property_model {
                    Some(MassPropertyModel::BoxPrincipalDimensions) => {
                        Ok(box_principal_moments_kg_m2(mass_kg, lengths))
                    }
                    Some(MassPropertyModel::EllipsoidPrincipalDimensions) => Ok(
                        ellipsoid_principal_moments_kg_m2(
                            mass_kg,
                            [0.5 * lengths[0], 0.5 * lengths[1], 0.5 * lengths[2]],
                        ),
                    ),
                    Some(other) => Err(ShapeMetadataError::Invalid(format!(
                        "principal_dimensions requires box_principal_dimensions or ellipsoid_principal_dimensions mass_property_model, got {other:?}"
                    ))),
                    None => Err(ShapeMetadataError::Invalid(
                        "principal_dimensions requires mass_properties.mass_property_model"
                            .to_string(),
                    )),
                }
            }
            BlockShapeType::CustomPrincipalMoments => {
                let moments = self
                    .mass_properties
                    .principal_moments_kg_m2
                    .ok_or_else(|| {
                        ShapeMetadataError::Invalid(
                            "custom_principal_moments requires mass_properties.principal_moments_kg_m2"
                                .to_string(),
                        )
                    })?;
                validate_positive_triplet(moments, "mass_properties.principal_moments_kg_m2")?;
                Ok(moments)
            }
        }
    }

    pub fn shape_class_or_default(&self) -> String {
        self.shape_class
            .clone()
            .unwrap_or_else(|| self.shape_type.as_str().to_string())
    }
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum BlockShapeType {
    Sphere,
    Ellipsoid,
    Box,
    PrincipalDimensions,
    CustomPrincipalMoments,
}

impl BlockShapeType {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::Sphere => "sphere",
            Self::Ellipsoid => "ellipsoid",
            Self::Box => "box",
            Self::PrincipalDimensions => "principal_dimensions",
            Self::CustomPrincipalMoments => "custom_principal_moments",
        }
    }
}

#[derive(Debug, Clone, Default, Serialize, Deserialize, PartialEq)]
pub struct ShapeDimensions {
    #[serde(default)]
    pub radius_m: Option<f64>,
    #[serde(default)]
    pub semi_axes_m: Option<[f64; 3]>,
    #[serde(default)]
    pub side_lengths_m: Option<[f64; 3]>,
    #[serde(default)]
    pub principal_lengths_m: Option<[f64; 3]>,
    #[serde(default)]
    pub equivalent_radius_m: Option<f64>,
}

impl ShapeDimensions {
    fn validate_for(&self, shape_type: BlockShapeType) -> Result<(), ShapeMetadataError> {
        if let Some(radius_m) = self.radius_m {
            validate_positive(radius_m, "dimensions_m.radius_m")?;
        }
        if let Some(radius_m) = self.equivalent_radius_m {
            validate_positive(radius_m, "dimensions_m.equivalent_radius_m")?;
        }
        if let Some(values) = self.semi_axes_m {
            validate_positive_triplet(values, "dimensions_m.semi_axes_m")?;
        }
        if let Some(values) = self.side_lengths_m {
            validate_positive_triplet(values, "dimensions_m.side_lengths_m")?;
        }
        if let Some(values) = self.principal_lengths_m {
            validate_positive_triplet(values, "dimensions_m.principal_lengths_m")?;
        }
        match shape_type {
            BlockShapeType::Sphere if self.radius_m.is_none() => Err(ShapeMetadataError::Invalid(
                "sphere requires dimensions_m.radius_m".to_string(),
            )),
            BlockShapeType::Ellipsoid if self.semi_axes_m.is_none() => {
                Err(ShapeMetadataError::Invalid(
                    "ellipsoid requires dimensions_m.semi_axes_m".to_string(),
                ))
            }
            BlockShapeType::Box if self.side_lengths_m.is_none() => Err(
                ShapeMetadataError::Invalid("box requires dimensions_m.side_lengths_m".to_string()),
            ),
            BlockShapeType::PrincipalDimensions if self.principal_lengths_m.is_none() => {
                Err(ShapeMetadataError::Invalid(
                    "principal_dimensions requires dimensions_m.principal_lengths_m".to_string(),
                ))
            }
            _ => Ok(()),
        }
    }

    fn active_equivalent_radius_m(&self, shape_type: BlockShapeType) -> Option<f64> {
        match shape_type {
            BlockShapeType::Sphere => self.radius_m,
            _ => self.equivalent_radius_m,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ShapeMassProperties {
    pub mass_kg: f64,
    #[serde(default)]
    pub density_kgpm3: Option<f64>,
    #[serde(default)]
    pub mass_property_model: Option<MassPropertyModel>,
    #[serde(default)]
    pub principal_moments_kg_m2: Option<[f64; 3]>,
    #[serde(default)]
    pub center_of_mass_offset_m: Option<[f64; 3]>,
}

impl ShapeMassProperties {
    fn validate(&self) -> Result<(), ShapeMetadataError> {
        validate_positive(self.mass_kg, "mass_properties.mass_kg")?;
        if let Some(density) = self.density_kgpm3 {
            validate_positive(density, "mass_properties.density_kgpm3")?;
        }
        if let Some(moments) = self.principal_moments_kg_m2 {
            validate_positive_triplet(moments, "mass_properties.principal_moments_kg_m2")?;
        }
        if let Some(offset) = self.center_of_mass_offset_m {
            validate_finite_triplet(offset, "mass_properties.center_of_mass_offset_m")?;
        }
        Ok(())
    }
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum MassPropertyModel {
    SolidSphere,
    SolidEllipsoid,
    Box,
    BoxPrincipalDimensions,
    EllipsoidPrincipalDimensions,
    CustomPrincipalMoments,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ShapeOrientation {
    #[serde(default = "default_orientation_representation")]
    pub representation: String,
    #[serde(default = "default_orientation_initialization_mode")]
    pub initialization_mode: String,
    #[serde(default = "default_identity_quaternion")]
    pub initial_quaternion_wxyz: [f64; 4],
}

impl Default for ShapeOrientation {
    fn default() -> Self {
        Self {
            representation: default_orientation_representation(),
            initialization_mode: default_orientation_initialization_mode(),
            initial_quaternion_wxyz: default_identity_quaternion(),
        }
    }
}

impl ShapeOrientation {
    fn validate(&self) -> Result<(), ShapeMetadataError> {
        if self.representation != "quaternion_wxyz" {
            return Err(ShapeMetadataError::Invalid(format!(
                "unsupported orientation.representation {}; expected quaternion_wxyz",
                self.representation
            )));
        }
        match self.initialization_mode.as_str() {
            "identity" | "fixed_quaternion" => {}
            other => {
                return Err(ShapeMetadataError::Invalid(format!(
                    "unsupported orientation.initialization_mode {other}"
                )));
            }
        }
        let q = self.initial_quaternion_wxyz;
        for (idx, value) in q.iter().enumerate() {
            if !value.is_finite() {
                return Err(ShapeMetadataError::Invalid(format!(
                    "orientation.initial_quaternion_wxyz[{idx}] must be finite"
                )));
            }
        }
        let norm = (q[0] * q[0] + q[1] * q[1] + q[2] * q[2] + q[3] * q[3]).sqrt();
        if (norm - 1.0).abs() > 1.0e-6 {
            return Err(ShapeMetadataError::Invalid(format!(
                "orientation.initial_quaternion_wxyz must be unit length; norm is {norm}"
            )));
        }
        if self.initialization_mode == "identity" && q != default_identity_quaternion() {
            return Err(ShapeMetadataError::Invalid(
                "identity orientation must use [1.0, 0.0, 0.0, 0.0]".to_string(),
            ));
        }
        Ok(())
    }
}

#[derive(Debug, Clone, Default, Serialize, Deserialize, PartialEq, Eq)]
pub struct ShapeProvenance {
    #[serde(default)]
    pub source_dataset: Option<String>,
    #[serde(default)]
    pub source_record_id: Option<String>,
    #[serde(default)]
    pub source_url_or_doi: Option<String>,
    #[serde(default)]
    pub license: Option<String>,
    #[serde(default)]
    pub notes: Vec<String>,
}

#[derive(Debug, Error)]
pub enum ShapeMetadataError {
    #[error("I/O error: {0}")]
    Io(#[from] std::io::Error),
    #[error("YAML error: {0}")]
    Yaml(#[from] serde_yaml::Error),
    #[error("shape metadata error: {0}")]
    Invalid(String),
}

pub fn sphere_principal_moments_kg_m2(mass_kg: f64, radius_m: f64) -> [f64; 3] {
    let moment = 0.4 * mass_kg * radius_m * radius_m;
    [moment, moment, moment]
}

pub fn ellipsoid_principal_moments_kg_m2(mass_kg: f64, semi_axes_m: [f64; 3]) -> [f64; 3] {
    let [a, b, c] = semi_axes_m;
    [
        0.2 * mass_kg * (b * b + c * c),
        0.2 * mass_kg * (a * a + c * c),
        0.2 * mass_kg * (a * a + b * b),
    ]
}

pub fn box_principal_moments_kg_m2(mass_kg: f64, side_lengths_m: [f64; 3]) -> [f64; 3] {
    let [lx, ly, lz] = side_lengths_m;
    [
        mass_kg * (ly * ly + lz * lz) / 12.0,
        mass_kg * (lx * lx + lz * lz) / 12.0,
        mass_kg * (lx * lx + ly * ly) / 12.0,
    ]
}

fn default_orientation_representation() -> String {
    "quaternion_wxyz".to_string()
}

fn default_orientation_initialization_mode() -> String {
    "identity".to_string()
}

fn default_identity_quaternion() -> [f64; 4] {
    [1.0, 0.0, 0.0, 0.0]
}

fn ensure_close(
    actual: f64,
    expected: f64,
    actual_label: &str,
    expected_label: &str,
) -> Result<(), ShapeMetadataError> {
    let tolerance = 1.0e-9_f64.max(1.0e-6 * expected.abs().max(actual.abs()));
    if (actual - expected).abs() > tolerance {
        return Err(ShapeMetadataError::Invalid(format!(
            "{actual_label} ({actual}) must match {expected_label} ({expected}) within {tolerance}"
        )));
    }
    Ok(())
}

fn validate_positive(value: f64, label: &str) -> Result<(), ShapeMetadataError> {
    if !value.is_finite() || value <= 0.0 {
        return Err(ShapeMetadataError::Invalid(format!(
            "{label} must be positive and finite"
        )));
    }
    Ok(())
}

fn validate_positive_triplet(values: [f64; 3], label: &str) -> Result<(), ShapeMetadataError> {
    for (idx, value) in values.iter().enumerate() {
        if !value.is_finite() || *value <= 0.0 {
            return Err(ShapeMetadataError::Invalid(format!(
                "{label}[{idx}] must be positive and finite"
            )));
        }
    }
    Ok(())
}

fn validate_finite_triplet(values: [f64; 3], label: &str) -> Result<(), ShapeMetadataError> {
    for (idx, value) in values.iter().enumerate() {
        if !value.is_finite() {
            return Err(ShapeMetadataError::Invalid(format!(
                "{label}[{idx}] must be finite"
            )));
        }
    }
    Ok(())
}
