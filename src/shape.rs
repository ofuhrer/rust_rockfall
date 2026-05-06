//! Passive block-shape metadata and mass-property diagnostics.
//!
//! Shape metadata is currently descriptive only. Contact and dynamics continue
//! to use the active spherical block unless a future opt-in contact model
//! explicitly says otherwise.

use crate::{geometry::SphereBlock, state::BodyState, Vec3};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::{fs, path::Path};
use thiserror::Error;

pub const SHAPE_METADATA_SCHEMA_VERSION: &str = "shape_metadata_v1";
pub const PASSIVE_SHAPE_WARNING: &str =
    "Shape metadata is passive; active contact and dynamics remain spherical.";
pub const SHAPE_CONTACT_V0_MODEL: &str = "shape_contact_v0";
pub const SHAPE_CONTACT_V0_ACTIVE_SHAPE: &str = "principal_dimensions_box_v0";

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

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ShapeContactV0Scaffold {
    pub active_contact_model: String,
    pub active_shape_type: String,
    pub shape_id: String,
    pub mass_kg: f64,
    pub principal_dimensions_m: [f64; 3],
    pub principal_moments_kg_m2: [f64; 3],
    pub orientation_wxyz: [f64; 4],
}

impl ShapeContactV0Scaffold {
    pub fn from_metadata(metadata: &BlockShapeMetadata) -> Result<Self, ShapeMetadataError> {
        metadata.validate()?;
        if metadata.shape_type != BlockShapeType::PrincipalDimensions {
            return Err(ShapeMetadataError::Invalid(format!(
                "{SHAPE_CONTACT_V0_MODEL} requires shape_type principal_dimensions for {SHAPE_CONTACT_V0_ACTIVE_SHAPE}"
            )));
        }
        if metadata.mass_properties.mass_property_model
            != Some(MassPropertyModel::BoxPrincipalDimensions)
        {
            return Err(ShapeMetadataError::Invalid(format!(
                "{SHAPE_CONTACT_V0_MODEL} requires mass_properties.mass_property_model box_principal_dimensions"
            )));
        }
        if metadata.orientation.initialization_mode != "identity" {
            return Err(ShapeMetadataError::Invalid(format!(
                "{SHAPE_CONTACT_V0_MODEL} scaffold currently supports identity orientation only"
            )));
        }
        let principal_dimensions_m =
            metadata.dimensions_m.principal_lengths_m.ok_or_else(|| {
                ShapeMetadataError::Invalid(
                    "principal_dimensions_box_v0 requires dimensions_m.principal_lengths_m"
                        .to_string(),
                )
            })?;
        validate_positive_triplet(principal_dimensions_m, "dimensions_m.principal_lengths_m")?;
        let principal_moments_kg_m2 =
            box_principal_moments_kg_m2(metadata.mass_properties.mass_kg, principal_dimensions_m);
        Ok(Self {
            active_contact_model: SHAPE_CONTACT_V0_MODEL.to_string(),
            active_shape_type: SHAPE_CONTACT_V0_ACTIVE_SHAPE.to_string(),
            shape_id: metadata.shape_id.clone(),
            mass_kg: metadata.mass_properties.mass_kg,
            principal_dimensions_m,
            principal_moments_kg_m2,
            orientation_wxyz: metadata.orientation.initial_quaternion_wxyz,
        })
    }

    pub fn support_point(
        &self,
        center_m: Vec3,
        terrain_normal_world: Vec3,
    ) -> Result<ShapeContactV0SupportDiagnostic, ShapeMetadataError> {
        select_box_support_point(
            center_m,
            terrain_normal_world,
            self.principal_dimensions_m,
            self.orientation_wxyz,
        )
    }

    pub(crate) fn impulse_input(
        &self,
        pre_state: BodyState,
        terrain_normal_world: Vec3,
        settings: ShapeContactV0ImpulseSettings,
    ) -> Result<ShapeContactV0PreparedImpulse, ShapeMetadataError> {
        let support = self.support_point(pre_state.position_m, terrain_normal_world)?;
        let input = ShapeContactV0ImpulseInput {
            pre_state,
            terrain_normal_world,
            mass_kg: self.mass_kg,
            principal_moments_kg_m2: self.principal_moments_kg_m2,
            normal_restitution: settings.normal_restitution,
            tangential_restitution: settings.tangential_restitution,
            friction_coefficient: settings.friction_coefficient,
            gravity_mps2: settings.gravity_mps2,
        };
        Ok(ShapeContactV0PreparedImpulse { support, input })
    }

    #[allow(dead_code)]
    pub(crate) fn apply_support_impulse(
        &self,
        pre_state: BodyState,
        terrain_normal_world: Vec3,
        settings: ShapeContactV0ImpulseSettings,
    ) -> Result<ShapeContactV0ImpulseResult, ShapeMetadataError> {
        let prepared = self.impulse_input(pre_state, terrain_normal_world, settings)?;
        shape_contact_v0_apply_support_impulse(&prepared.support, prepared.input)
    }

    #[allow(dead_code)]
    pub(crate) fn prepare_contact(
        &self,
        input: ShapeContactV0ContactInput,
    ) -> Result<ShapeContactV0ContactResult, ShapeMetadataError> {
        shape_contact_v0_prepare_contact(self, input)
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ShapeContactV0SupportDiagnostic {
    pub active_contact_model: String,
    pub active_shape_type: String,
    pub orientation_wxyz: [f64; 4],
    pub orientation_norm_error: f64,
    pub support_point_m: [f64; 3],
    pub support_corner_signs: [i8; 3],
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq)]
pub struct ShapeContactV0EnergyDiagnostic {
    pub pre_translational_kinetic_j: f64,
    pub pre_rotational_kinetic_j: f64,
    pub pre_total_mechanical_energy_j: f64,
    pub post_translational_kinetic_j: f64,
    pub post_rotational_kinetic_j: f64,
    pub post_total_mechanical_energy_j: f64,
    pub contact_energy_delta_j: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ShapeContactV0ImpulseDiagnostic {
    pub active_contact_model: String,
    pub active_shape_type: String,
    pub impacted: bool,
    pub support_point_m: [f64; 3],
    pub support_corner_signs: [i8; 3],
    pub contact_point_velocity_pre_mps: [f64; 3],
    pub contact_point_velocity_post_mps: [f64; 3],
    pub pre_contact_normal_velocity_mps: f64,
    pub post_contact_normal_velocity_mps: f64,
    pub pre_contact_tangential_speed_mps: f64,
    pub post_contact_tangential_speed_mps: f64,
    pub normal_impulse_n_s: f64,
    pub tangential_impulse_n_s: [f64; 3],
    pub tangential_impulse_norm_n_s: f64,
    pub coulomb_friction_cap_n_s: f64,
    pub coulomb_cap_ratio: f64,
    pub energy: ShapeContactV0EnergyDiagnostic,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ShapeContactV0ImpulseResult {
    pub post_state: BodyState,
    pub diagnostic: ShapeContactV0ImpulseDiagnostic,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub(crate) struct ShapeContactV0PreparedImpulse {
    support: ShapeContactV0SupportDiagnostic,
    input: ShapeContactV0ImpulseInput,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq)]
pub struct ShapeContactV0ImpulseSettings {
    pub normal_restitution: f64,
    pub tangential_restitution: f64,
    pub friction_coefficient: f64,
    pub gravity_mps2: f64,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq)]
pub(crate) struct ShapeContactV0ImpulseInput {
    pre_state: BodyState,
    terrain_normal_world: Vec3,
    mass_kg: f64,
    principal_moments_kg_m2: [f64; 3],
    normal_restitution: f64,
    tangential_restitution: f64,
    friction_coefficient: f64,
    gravity_mps2: f64,
}

#[allow(dead_code)]
#[derive(Debug, Clone, Copy, PartialEq)]
pub(crate) struct ShapeContactV0ContactInput {
    pub(crate) pre_state: BodyState,
    pub(crate) terrain_contact_point_m: Vec3,
    pub(crate) terrain_normal_world: Vec3,
    pub(crate) settings: ShapeContactV0ImpulseSettings,
}

#[allow(dead_code)]
#[derive(Debug, Clone, PartialEq)]
pub(crate) struct ShapeContactV0ContactResult {
    pub(crate) terrain_contact_point_m: [f64; 3],
    pub(crate) support_signed_gap_m: f64,
    pub(crate) contact_regime: ShapeContactV0ContactRegime,
    pub(crate) impulse_result: ShapeContactV0ImpulseResult,
}

#[allow(dead_code)]
#[derive(Debug, Clone, Copy, Serialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub(crate) enum ShapeContactV0ContactRegime {
    SeparatedMovingAway,
    SeparatedMovingToward,
    Touching,
    Penetrating,
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

pub fn select_box_support_point(
    center_m: Vec3,
    terrain_normal_world: Vec3,
    principal_dimensions_m: [f64; 3],
    orientation_wxyz: [f64; 4],
) -> Result<ShapeContactV0SupportDiagnostic, ShapeMetadataError> {
    validate_finite_triplet([center_m.x, center_m.y, center_m.z], "center_m")?;
    validate_positive_triplet(principal_dimensions_m, "principal_dimensions_m")?;
    validate_finite_triplet(
        [
            terrain_normal_world.x,
            terrain_normal_world.y,
            terrain_normal_world.z,
        ],
        "terrain_normal_world",
    )?;
    let normal_norm = terrain_normal_world.norm();
    if normal_norm == 0.0 {
        return Err(ShapeMetadataError::Invalid(
            "terrain_normal_world must be nonzero".to_string(),
        ));
    }
    validate_unit_quaternion(orientation_wxyz, "orientation_wxyz")?;
    let normal = terrain_normal_world / normal_norm;
    let direction_body = rotate_vector_by_quaternion_conjugate(-normal, orientation_wxyz);
    // Deterministic scaffold policy: exact zero support-direction components
    // choose the positive corner sign. This is not a validated face-contact
    // model; it only makes pre-runtime support selection reproducible.
    let support_corner_signs = [
        deterministic_sign(direction_body.x),
        deterministic_sign(direction_body.y),
        deterministic_sign(direction_body.z),
    ];
    let support_body = Vec3::new(
        0.5 * principal_dimensions_m[0] * f64::from(support_corner_signs[0]),
        0.5 * principal_dimensions_m[1] * f64::from(support_corner_signs[1]),
        0.5 * principal_dimensions_m[2] * f64::from(support_corner_signs[2]),
    );
    let support_world = rotate_vector_by_quaternion(support_body, orientation_wxyz);
    let support_point = center_m + support_world;
    let orientation_norm = quaternion_norm(orientation_wxyz);
    Ok(ShapeContactV0SupportDiagnostic {
        active_contact_model: SHAPE_CONTACT_V0_MODEL.to_string(),
        active_shape_type: SHAPE_CONTACT_V0_ACTIVE_SHAPE.to_string(),
        orientation_wxyz,
        orientation_norm_error: (orientation_norm - 1.0).abs(),
        support_point_m: [support_point.x, support_point.y, support_point.z],
        support_corner_signs,
    })
}

pub fn shape_contact_v0_energy_diagnostic(
    pre_state: &BodyState,
    post_state: &BodyState,
    mass_kg: f64,
    principal_moments_kg_m2: [f64; 3],
    gravity_mps2: f64,
) -> Result<ShapeContactV0EnergyDiagnostic, ShapeMetadataError> {
    validate_positive(mass_kg, "mass_kg")?;
    validate_positive_triplet(principal_moments_kg_m2, "principal_moments_kg_m2")?;
    validate_positive(gravity_mps2, "gravity_mps2")?;
    let pre_translational_kinetic_j = 0.5 * mass_kg * pre_state.velocity_mps.norm_squared();
    let pre_rotational_kinetic_j = principal_axis_rotational_energy_j(
        pre_state.angular_velocity_radps,
        principal_moments_kg_m2,
    );
    let pre_total_mechanical_energy_j = pre_translational_kinetic_j
        + pre_rotational_kinetic_j
        + mass_kg * gravity_mps2 * pre_state.position_m.z;
    let post_translational_kinetic_j = 0.5 * mass_kg * post_state.velocity_mps.norm_squared();
    let post_rotational_kinetic_j = principal_axis_rotational_energy_j(
        post_state.angular_velocity_radps,
        principal_moments_kg_m2,
    );
    let post_total_mechanical_energy_j = post_translational_kinetic_j
        + post_rotational_kinetic_j
        + mass_kg * gravity_mps2 * post_state.position_m.z;
    Ok(ShapeContactV0EnergyDiagnostic {
        pre_translational_kinetic_j,
        pre_rotational_kinetic_j,
        pre_total_mechanical_energy_j,
        post_translational_kinetic_j,
        post_rotational_kinetic_j,
        post_total_mechanical_energy_j,
        contact_energy_delta_j: post_total_mechanical_energy_j - pre_total_mechanical_energy_j,
    })
}

/// Crate-internal low-level analytic impulse helper.
///
/// Shape-contact runtime-adjacent paths must prefer
/// [`shape_contact_v0_prepare_contact`] so support-gap classification gates
/// impulse application. This helper remains internal to avoid public callers
/// mixing support geometry, mass, and inertia by hand.
pub(crate) fn shape_contact_v0_apply_support_impulse(
    support: &ShapeContactV0SupportDiagnostic,
    input: ShapeContactV0ImpulseInput,
) -> Result<ShapeContactV0ImpulseResult, ShapeMetadataError> {
    let pre_state = input.pre_state;
    let mass_kg = input.mass_kg;
    let principal_moments_kg_m2 = input.principal_moments_kg_m2;
    let terrain_normal_world = input.terrain_normal_world;
    validate_finite_triplet(
        [
            pre_state.position_m.x,
            pre_state.position_m.y,
            pre_state.position_m.z,
        ],
        "pre_state.position_m",
    )?;
    validate_finite_triplet(
        [
            pre_state.velocity_mps.x,
            pre_state.velocity_mps.y,
            pre_state.velocity_mps.z,
        ],
        "pre_state.velocity_mps",
    )?;
    validate_finite_triplet(
        [
            pre_state.angular_velocity_radps.x,
            pre_state.angular_velocity_radps.y,
            pre_state.angular_velocity_radps.z,
        ],
        "pre_state.angular_velocity_radps",
    )?;
    validate_positive(mass_kg, "mass_kg")?;
    validate_positive_triplet(principal_moments_kg_m2, "principal_moments_kg_m2")?;
    validate_positive(input.gravity_mps2, "gravity_mps2")?;
    validate_unit_interval(input.normal_restitution, "normal_restitution")?;
    validate_unit_interval(input.tangential_restitution, "tangential_restitution")?;
    validate_nonnegative(input.friction_coefficient, "friction_coefficient")?;
    validate_unit_quaternion(support.orientation_wxyz, "support.orientation_wxyz")?;
    if support.orientation_wxyz != default_identity_quaternion() {
        return Err(ShapeMetadataError::Invalid(
            "shape_contact_v0 impulse kernel currently supports identity orientation only"
                .to_string(),
        ));
    }
    validate_finite_triplet(support.support_point_m, "support.support_point_m")?;
    validate_finite_triplet(
        [
            terrain_normal_world.x,
            terrain_normal_world.y,
            terrain_normal_world.z,
        ],
        "terrain_normal_world",
    )?;
    let normal_norm = terrain_normal_world.norm();
    if normal_norm == 0.0 {
        return Err(ShapeMetadataError::Invalid(
            "terrain_normal_world must be nonzero".to_string(),
        ));
    }

    let normal = terrain_normal_world / normal_norm;
    let support_point = Vec3::new(
        support.support_point_m[0],
        support.support_point_m[1],
        support.support_point_m[2],
    );
    let contact_offset = support_point - pre_state.position_m;
    let pre_contact_velocity = rigid_body_contact_point_velocity(pre_state, contact_offset);
    let pre_normal_velocity = pre_contact_velocity.dot(&normal);
    let pre_tangent_velocity = pre_contact_velocity - pre_normal_velocity * normal;
    let pre_tangent_speed = pre_tangent_velocity.norm();
    let mut post_state = pre_state;
    let mut normal_impulse_n_s = 0.0;
    let mut tangential_impulse = Vec3::zeros();
    let mut coulomb_friction_cap_n_s = 0.0;

    if pre_normal_velocity < 0.0 {
        let normal_denominator = impulse_effective_mass_denominator(
            mass_kg,
            principal_moments_kg_m2,
            contact_offset,
            normal,
        )?;
        normal_impulse_n_s =
            -((1.0 + input.normal_restitution) * pre_normal_velocity) / normal_denominator;
        apply_principal_axis_impulse(
            &mut post_state,
            mass_kg,
            principal_moments_kg_m2,
            contact_offset,
            normal_impulse_n_s * normal,
        );

        let post_normal_contact_velocity =
            rigid_body_contact_point_velocity(post_state, contact_offset);
        let post_normal_vn = post_normal_contact_velocity.dot(&normal);
        let post_normal_tangent_velocity = post_normal_contact_velocity - post_normal_vn * normal;
        let post_normal_tangent_speed = post_normal_tangent_velocity.norm();
        coulomb_friction_cap_n_s = input.friction_coefficient * normal_impulse_n_s.abs();
        if post_normal_tangent_speed > 0.0 {
            let tangent_direction = post_normal_tangent_velocity / post_normal_tangent_speed;
            let tangent_denominator = impulse_effective_mass_denominator(
                mass_kg,
                principal_moments_kg_m2,
                contact_offset,
                tangent_direction,
            )?;
            let requested_tangent_impulse = -((1.0 - input.tangential_restitution)
                * post_normal_tangent_speed)
                / tangent_denominator
                * tangent_direction;
            tangential_impulse =
                clamp_vector_norm(requested_tangent_impulse, coulomb_friction_cap_n_s);
            apply_principal_axis_impulse(
                &mut post_state,
                mass_kg,
                principal_moments_kg_m2,
                contact_offset,
                tangential_impulse,
            );
        }
    }

    let post_contact_velocity = rigid_body_contact_point_velocity(post_state, contact_offset);
    let post_normal_velocity = post_contact_velocity.dot(&normal);
    let post_tangent_velocity = post_contact_velocity - post_normal_velocity * normal;
    let tangential_impulse_norm_n_s = tangential_impulse.norm();
    let coulomb_cap_ratio = if coulomb_friction_cap_n_s > 0.0 {
        tangential_impulse_norm_n_s / coulomb_friction_cap_n_s
    } else {
        0.0
    };
    let energy = shape_contact_v0_energy_diagnostic(
        &pre_state,
        &post_state,
        mass_kg,
        principal_moments_kg_m2,
        input.gravity_mps2,
    )?;

    Ok(ShapeContactV0ImpulseResult {
        post_state,
        diagnostic: ShapeContactV0ImpulseDiagnostic {
            active_contact_model: SHAPE_CONTACT_V0_MODEL.to_string(),
            active_shape_type: SHAPE_CONTACT_V0_ACTIVE_SHAPE.to_string(),
            impacted: pre_normal_velocity < 0.0,
            support_point_m: support.support_point_m,
            support_corner_signs: support.support_corner_signs,
            contact_point_velocity_pre_mps: [
                pre_contact_velocity.x,
                pre_contact_velocity.y,
                pre_contact_velocity.z,
            ],
            contact_point_velocity_post_mps: [
                post_contact_velocity.x,
                post_contact_velocity.y,
                post_contact_velocity.z,
            ],
            pre_contact_normal_velocity_mps: pre_normal_velocity,
            post_contact_normal_velocity_mps: post_normal_velocity,
            pre_contact_tangential_speed_mps: pre_tangent_speed,
            post_contact_tangential_speed_mps: post_tangent_velocity.norm(),
            normal_impulse_n_s,
            tangential_impulse_n_s: [
                tangential_impulse.x,
                tangential_impulse.y,
                tangential_impulse.z,
            ],
            tangential_impulse_norm_n_s,
            coulomb_friction_cap_n_s,
            coulomb_cap_ratio,
            energy,
        },
    })
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

fn validate_nonnegative(value: f64, label: &str) -> Result<(), ShapeMetadataError> {
    if !value.is_finite() || value < 0.0 {
        return Err(ShapeMetadataError::Invalid(format!(
            "{label} must be nonnegative and finite"
        )));
    }
    Ok(())
}

fn validate_unit_interval(value: f64, label: &str) -> Result<(), ShapeMetadataError> {
    if !value.is_finite() || !(0.0..=1.0).contains(&value) {
        return Err(ShapeMetadataError::Invalid(format!(
            "{label} must be finite and in [0, 1]"
        )));
    }
    Ok(())
}

fn validate_unit_quaternion(values: [f64; 4], label: &str) -> Result<(), ShapeMetadataError> {
    for (idx, value) in values.iter().enumerate() {
        if !value.is_finite() {
            return Err(ShapeMetadataError::Invalid(format!(
                "{label}[{idx}] must be finite"
            )));
        }
    }
    let norm = quaternion_norm(values);
    if (norm - 1.0).abs() > 1.0e-6 {
        return Err(ShapeMetadataError::Invalid(format!(
            "{label} must be unit length; norm is {norm}"
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

fn deterministic_sign(value: f64) -> i8 {
    if value < 0.0 {
        -1
    } else {
        1
    }
}

fn quaternion_norm(values: [f64; 4]) -> f64 {
    (values[0] * values[0] + values[1] * values[1] + values[2] * values[2] + values[3] * values[3])
        .sqrt()
}

fn rotate_vector_by_quaternion(vector: Vec3, q: [f64; 4]) -> Vec3 {
    let q_vec = Vec3::new(q[1], q[2], q[3]);
    let uv = q_vec.cross(&vector);
    let uuv = q_vec.cross(&uv);
    vector + (2.0 * q[0]) * uv + 2.0 * uuv
}

fn rotate_vector_by_quaternion_conjugate(vector: Vec3, q: [f64; 4]) -> Vec3 {
    rotate_vector_by_quaternion(vector, [q[0], -q[1], -q[2], -q[3]])
}

fn principal_axis_rotational_energy_j(omega_radps: Vec3, principal_moments_kg_m2: [f64; 3]) -> f64 {
    0.5 * (principal_moments_kg_m2[0] * omega_radps.x * omega_radps.x
        + principal_moments_kg_m2[1] * omega_radps.y * omega_radps.y
        + principal_moments_kg_m2[2] * omega_radps.z * omega_radps.z)
}

fn rigid_body_contact_point_velocity(state: BodyState, contact_offset_m: Vec3) -> Vec3 {
    state.velocity_mps + state.angular_velocity_radps.cross(&contact_offset_m)
}

fn impulse_effective_mass_denominator(
    mass_kg: f64,
    principal_moments_kg_m2: [f64; 3],
    contact_offset_m: Vec3,
    impulse_direction: Vec3,
) -> Result<f64, ShapeMetadataError> {
    let direction_norm = impulse_direction.norm();
    if direction_norm == 0.0 {
        return Err(ShapeMetadataError::Invalid(
            "impulse_direction must be nonzero".to_string(),
        ));
    }
    let direction = impulse_direction / direction_norm;
    let rotational_axis = contact_offset_m.cross(&direction);
    let angular_velocity_delta_per_impulse = Vec3::new(
        rotational_axis.x / principal_moments_kg_m2[0],
        rotational_axis.y / principal_moments_kg_m2[1],
        rotational_axis.z / principal_moments_kg_m2[2],
    );
    let contact_velocity_delta_per_impulse =
        direction / mass_kg + angular_velocity_delta_per_impulse.cross(&contact_offset_m);
    let denominator = direction.dot(&contact_velocity_delta_per_impulse);
    if !denominator.is_finite() || denominator <= 0.0 {
        return Err(ShapeMetadataError::Invalid(format!(
            "effective impulse mass denominator must be positive and finite; got {denominator}"
        )));
    }
    Ok(denominator)
}

fn apply_principal_axis_impulse(
    state: &mut BodyState,
    mass_kg: f64,
    principal_moments_kg_m2: [f64; 3],
    contact_offset_m: Vec3,
    impulse_n_s: Vec3,
) {
    state.velocity_mps += impulse_n_s / mass_kg;
    let angular_impulse = contact_offset_m.cross(&impulse_n_s);
    state.angular_velocity_radps += Vec3::new(
        angular_impulse.x / principal_moments_kg_m2[0],
        angular_impulse.y / principal_moments_kg_m2[1],
        angular_impulse.z / principal_moments_kg_m2[2],
    );
}

fn clamp_vector_norm(vector: Vec3, max_norm: f64) -> Vec3 {
    let norm = vector.norm();
    if norm > max_norm.max(0.0) && norm > 0.0 {
        vector * (max_norm.max(0.0) / norm)
    } else {
        vector
    }
}

#[allow(dead_code)]
pub(crate) const SHAPE_CONTACT_V0_CONTACT_GAP_TOLERANCE_M: f64 = 1.0e-9;

/// Crate-internal shape-contact preparation layer.
///
/// This is the single pre-runtime path that owns terrain/contact context,
/// support selection, signed support-gap classification, and impulse
/// application. Future integrator-adjacent code should route through this
/// helper instead of calling [`ShapeContactV0Scaffold::apply_support_impulse`]
/// directly.
#[allow(dead_code)]
pub(crate) fn shape_contact_v0_prepare_contact(
    scaffold: &ShapeContactV0Scaffold,
    input: ShapeContactV0ContactInput,
) -> Result<ShapeContactV0ContactResult, ShapeMetadataError> {
    validate_finite_triplet(
        [
            input.terrain_contact_point_m.x,
            input.terrain_contact_point_m.y,
            input.terrain_contact_point_m.z,
        ],
        "terrain_contact_point_m",
    )?;
    validate_finite_triplet(
        [
            input.terrain_normal_world.x,
            input.terrain_normal_world.y,
            input.terrain_normal_world.z,
        ],
        "terrain_normal_world",
    )?;
    let normal_norm = input.terrain_normal_world.norm();
    if normal_norm == 0.0 {
        return Err(ShapeMetadataError::Invalid(
            "terrain_normal_world must be nonzero".to_string(),
        ));
    }
    let normal = input.terrain_normal_world / normal_norm;
    let prepared =
        scaffold.impulse_input(input.pre_state, input.terrain_normal_world, input.settings)?;
    let support_point = Vec3::new(
        prepared.support.support_point_m[0],
        prepared.support.support_point_m[1],
        prepared.support.support_point_m[2],
    );
    let support_signed_gap_m = (support_point - input.terrain_contact_point_m).dot(&normal);
    let pre_contact_velocity = rigid_body_contact_point_velocity(
        input.pre_state,
        support_point - input.pre_state.position_m,
    );
    let pre_normal_velocity = pre_contact_velocity.dot(&normal);
    let contact_regime = if support_signed_gap_m > SHAPE_CONTACT_V0_CONTACT_GAP_TOLERANCE_M {
        if pre_normal_velocity < 0.0 {
            ShapeContactV0ContactRegime::SeparatedMovingToward
        } else {
            ShapeContactV0ContactRegime::SeparatedMovingAway
        }
    } else if support_signed_gap_m < -SHAPE_CONTACT_V0_CONTACT_GAP_TOLERANCE_M {
        ShapeContactV0ContactRegime::Penetrating
    } else {
        ShapeContactV0ContactRegime::Touching
    };
    let impulse_result = match contact_regime {
        ShapeContactV0ContactRegime::SeparatedMovingAway
        | ShapeContactV0ContactRegime::SeparatedMovingToward => {
            shape_contact_v0_no_impulse_result(&prepared.support, prepared.input)?
        }
        ShapeContactV0ContactRegime::Touching | ShapeContactV0ContactRegime::Penetrating => {
            shape_contact_v0_apply_support_impulse(&prepared.support, prepared.input)?
        }
    };
    Ok(ShapeContactV0ContactResult {
        terrain_contact_point_m: [
            input.terrain_contact_point_m.x,
            input.terrain_contact_point_m.y,
            input.terrain_contact_point_m.z,
        ],
        support_signed_gap_m,
        contact_regime,
        impulse_result,
    })
}

#[cfg(test)]
#[derive(Debug, Clone, Copy)]
struct ShapeContactV0TestContactStepInput {
    pre_state: BodyState,
    terrain_normal_world: Vec3,
    settings: ShapeContactV0ImpulseSettings,
}

#[cfg(test)]
fn shape_contact_v0_test_contact_step(
    scaffold: &ShapeContactV0Scaffold,
    input: ShapeContactV0TestContactStepInput,
) -> Result<ShapeContactV0ImpulseResult, ShapeMetadataError> {
    scaffold.apply_support_impulse(input.pre_state, input.terrain_normal_world, input.settings)
}

#[cfg(test)]
type ShapeContactV0DryRunInput = ShapeContactV0ContactInput;

#[cfg(test)]
type ShapeContactV0DryRunResult = ShapeContactV0ContactResult;

#[cfg(test)]
type ShapeContactV0DryRunContactRegime = ShapeContactV0ContactRegime;

#[cfg(test)]
fn shape_contact_v0_contact_dry_run(
    scaffold: &ShapeContactV0Scaffold,
    input: ShapeContactV0DryRunInput,
) -> Result<ShapeContactV0DryRunResult, ShapeMetadataError> {
    scaffold.prepare_contact(input)
}

#[allow(dead_code)]
#[derive(Debug, Clone, Copy)]
struct ShapeContactV0SyntheticTerrainInput {
    pre_state: BodyState,
    terrain_query_x_m: f64,
    terrain_query_y_m: f64,
    settings: ShapeContactV0ImpulseSettings,
}

#[allow(dead_code)]
#[derive(Debug, Clone, Copy)]
struct ShapeContactV0MiniFixedStepInput {
    pre_step_state: BodyState,
    dt_s: f64,
    gravity_mps2: f64,
    settings: ShapeContactV0ImpulseSettings,
}

#[allow(dead_code)]
#[derive(Debug, Clone)]
struct ShapeContactV0MiniFixedStepResult {
    pre_step_state: BodyState,
    predicted_state: BodyState,
    terrain_contact_point_m: [f64; 3],
    terrain_normal_world: [f64; 3],
    contact: ShapeContactV0ContactResult,
}

#[allow(dead_code)]
#[derive(Debug, Clone, Serialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
enum ShapeContactV0RuntimeRegimeLabelV1 {
    NonImpulsiveSeparated,
    NonImpulsiveTouching,
    NonImpulsivePenetrating,
    ImpulsiveTouching,
    ImpulsivePenetrating,
}

#[allow(dead_code)]
#[derive(Debug, Clone, Serialize, PartialEq)]
struct ShapeContactV0RuntimeDiagnosticRowV1 {
    shape_contact_runtime_schema_version: String,
    case_id: String,
    trajectory_id: String,
    step_index: u64,
    time_s: f64,
    shape_contact_row_id: String,
    contact_event_id: Option<String>,
    impact_index: Option<u64>,
    active_contact_model: String,
    active_shape_type: String,
    shape_id: String,
    contact_regime: ShapeContactV0ContactRegime,
    shape_contact_regime_label: ShapeContactV0RuntimeRegimeLabelV1,
    support_signed_gap_m: f64,
    contact_gap_tolerance_m: f64,
    terrain_contact_point_x_m: f64,
    terrain_contact_point_y_m: f64,
    terrain_contact_point_z_m: f64,
    terrain_normal_x: f64,
    terrain_normal_y: f64,
    terrain_normal_z: f64,
    support_point_x_m: f64,
    support_point_y_m: f64,
    support_point_z_m: f64,
    support_corner_sign_x: i8,
    support_corner_sign_y: i8,
    support_corner_sign_z: i8,
    support_corner_changed: Option<bool>,
    contact_point_normal_velocity_pre_mps: f64,
    contact_point_normal_velocity_post_mps: f64,
    contact_point_tangential_speed_pre_mps: f64,
    contact_point_tangential_speed_post_mps: f64,
    normal_impulse_n_s: f64,
    tangential_impulse_x_n_s: f64,
    tangential_impulse_y_n_s: f64,
    tangential_impulse_z_n_s: f64,
    tangential_impulse_norm_n_s: f64,
    coulomb_friction_cap_n_s: f64,
    coulomb_cap_ratio: Option<f64>,
    normal_restitution: f64,
    tangential_restitution: f64,
    friction_coefficient: f64,
    gravity_mps2: f64,
    pre_translational_kinetic_j: f64,
    post_translational_kinetic_j: f64,
    pre_rotational_kinetic_j: f64,
    post_rotational_kinetic_j: f64,
    pre_potential_energy_j: f64,
    post_potential_energy_j: f64,
    pre_total_mechanical_energy_j: f64,
    post_total_mechanical_energy_j: f64,
    contact_energy_delta_j: f64,
    projection_energy_delta_j: Option<f64>,
    total_energy_delta_j: f64,
    rotational_to_translational_energy_ratio_pre: Option<f64>,
    rotational_to_translational_energy_ratio_post: Option<f64>,
    orientation_w: f64,
    orientation_x: f64,
    orientation_y: f64,
    orientation_z: f64,
    orientation_norm_error: f64,
    orientation_initialization_mode: String,
    impulse_applied: bool,
    projection_applied: bool,
}

#[allow(dead_code)]
#[derive(Debug, Clone)]
struct ShapeContactV0RuntimeDiagnosticIdentity<'a> {
    case_id: &'a str,
    trajectory_id: &'a str,
    step_index: u64,
    time_s: f64,
    contact_event_id: Option<&'a str>,
    impact_index: Option<u64>,
}

#[allow(dead_code)]
#[derive(Debug, Clone, Default)]
struct ShapeContactV0RuntimeDiagnosticWriterV1 {
    rows: Vec<ShapeContactV0RuntimeDiagnosticRowV1>,
}

#[allow(dead_code)]
impl ShapeContactV0RuntimeDiagnosticWriterV1 {
    fn new() -> Self {
        Self::default()
    }

    fn write_row(&mut self, row: ShapeContactV0RuntimeDiagnosticRowV1) {
        self.rows.push(row);
    }

    fn rows(&self) -> &[ShapeContactV0RuntimeDiagnosticRowV1] {
        &self.rows
    }

    fn to_json_lines(&self) -> Result<String, serde_json::Error> {
        let mut lines = Vec::with_capacity(self.rows.len());
        for row in &self.rows {
            lines.push(serde_json::to_string(row)?);
        }
        Ok(lines.join("\n"))
    }

    fn to_sidecar_manifest(
        &self,
        diagnostic_sidecar_path: Option<String>,
    ) -> Result<ShapeContactV0DiagnosticSidecarManifestV1, serde_json::Error> {
        let json_lines = self.to_json_lines()?;
        Ok(self.sidecar_manifest_for_json_lines(diagnostic_sidecar_path, &json_lines))
    }

    fn write_json_lines_sidecar(
        &self,
        diagnostic_sidecar_path: &Path,
    ) -> Result<ShapeContactV0DiagnosticSidecarManifestV1, ShapeMetadataError> {
        let json_lines = self.to_json_lines().map_err(|err| {
            ShapeMetadataError::Invalid(format!(
                "shape_contact_runtime_diagnostic_v1 serialization failed: {err}"
            ))
        })?;
        fs::write(diagnostic_sidecar_path, json_lines.as_bytes())?;
        Ok(self.sidecar_manifest_for_json_lines(
            Some(diagnostic_sidecar_path.display().to_string()),
            &json_lines,
        ))
    }

    fn sidecar_manifest_for_json_lines(
        &self,
        diagnostic_sidecar_path: Option<String>,
        json_lines: &str,
    ) -> ShapeContactV0DiagnosticSidecarManifestV1 {
        ShapeContactV0DiagnosticSidecarManifestV1 {
            diagnostic_sidecar_kind: "shape_contact_runtime_diagnostic_jsonl_v1".to_string(),
            diagnostic_sidecar_path,
            schema_version: "shape_contact_runtime_diagnostic_v1".to_string(),
            row_count: self.rows.len(),
            json_lines_hash64: Some(format!(
                "{:016x}",
                crate::stochastic::stable_hash64(json_lines.as_bytes())
            )),
            json_lines_sha256: Some(sha256_hex(json_lines.as_bytes())),
            no_public_output_warning:
                "internal shape_contact_v0 smoke sidecar; not public validation or benchmark output"
                    .to_string(),
        }
    }
}

#[allow(dead_code)]
#[derive(Debug, Clone, Serialize, PartialEq, Eq)]
struct ShapeContactV0DiagnosticSidecarManifestV1 {
    diagnostic_sidecar_kind: String,
    diagnostic_sidecar_path: Option<String>,
    schema_version: String,
    row_count: usize,
    json_lines_hash64: Option<String>,
    json_lines_sha256: Option<String>,
    no_public_output_warning: String,
}

#[allow(dead_code)]
#[derive(Debug, Clone, Copy)]
struct ShapeContactV0RuntimeSmokeInput {
    contact_model: crate::dynamics::ContactModel,
    pre_step_state: BodyState,
    dt_s: f64,
    gravity_mps2: f64,
    settings: ShapeContactV0ImpulseSettings,
    step_index: u64,
    time_s: f64,
}

#[allow(dead_code)]
#[derive(Debug, Clone, Serialize, PartialEq)]
struct ShapeContactV0RuntimeSmokeManifestV1 {
    active_contact_model: String,
    active_shape_type: String,
    shape_metadata_path: Option<String>,
    shape_metadata_sha256: Option<String>,
    shape_id: String,
    mass_kg: f64,
    principal_dimensions_m: [f64; 3],
    orientation_initialization_mode: String,
    orientation_representation: String,
    inertia_model: String,
    principal_moments_kg_m2: [f64; 3],
    support_selection_policy: String,
    support_corner_tie_break: String,
    contact_gap_tolerance_m: f64,
    multi_contact: bool,
    new_tuned_parameters: bool,
    defaults_changed: bool,
    projection_correction_enabled: bool,
    persistent_contact_enabled: bool,
    orientation_evolution_enabled: bool,
    runtime_diagnostic_schema_version: String,
    experimental_status: String,
    warnings: Vec<String>,
    limitations: Vec<String>,
}

#[allow(dead_code)]
#[derive(Debug, Clone)]
struct ShapeContactV0RuntimeSmokeResult {
    pre_step_state: BodyState,
    predicted_state: BodyState,
    terrain_contact_point_m: [f64; 3],
    terrain_normal_world: [f64; 3],
    writer: ShapeContactV0RuntimeDiagnosticWriterV1,
    manifest: ShapeContactV0RuntimeSmokeManifestV1,
}

#[allow(dead_code)]
#[derive(Debug, Clone, Serialize, PartialEq)]
struct ShapeContactV0RuntimeSmokeManifestPackageV1 {
    shape_contact_v0: ShapeContactV0RuntimeSmokeManifestV1,
    diagnostic_sidecar: ShapeContactV0DiagnosticSidecarManifestV1,
}

#[allow(dead_code)]
fn shape_contact_v0_runtime_smoke_manifest_package(
    result: &ShapeContactV0RuntimeSmokeResult,
) -> Result<ShapeContactV0RuntimeSmokeManifestPackageV1, serde_json::Error> {
    Ok(ShapeContactV0RuntimeSmokeManifestPackageV1 {
        shape_contact_v0: result.manifest.clone(),
        diagnostic_sidecar: result.writer.to_sidecar_manifest(None)?,
    })
}

#[allow(dead_code)]
fn shape_contact_v0_runtime_smoke_manifest(
    scaffold: &ShapeContactV0Scaffold,
    shape_metadata_path: Option<String>,
    shape_metadata_sha256: Option<String>,
) -> ShapeContactV0RuntimeSmokeManifestV1 {
    ShapeContactV0RuntimeSmokeManifestV1 {
        active_contact_model: SHAPE_CONTACT_V0_MODEL.to_string(),
        active_shape_type: SHAPE_CONTACT_V0_ACTIVE_SHAPE.to_string(),
        shape_metadata_path,
        shape_metadata_sha256,
        shape_id: scaffold.shape_id.clone(),
        mass_kg: scaffold.mass_kg,
        principal_dimensions_m: scaffold.principal_dimensions_m,
        orientation_initialization_mode: default_orientation_initialization_mode(),
        orientation_representation: default_orientation_representation(),
        inertia_model: "analytic_box_principal_moments".to_string(),
        principal_moments_kg_m2: scaffold.principal_moments_kg_m2,
        support_selection_policy: "single_support_point_from_terrain_normal_positive_zero_tiebreak"
            .to_string(),
        support_corner_tie_break: "zero_components_choose_positive_sign".to_string(),
        contact_gap_tolerance_m: SHAPE_CONTACT_V0_CONTACT_GAP_TOLERANCE_M,
        multi_contact: false,
        new_tuned_parameters: false,
        defaults_changed: false,
        projection_correction_enabled: false,
        persistent_contact_enabled: false,
        orientation_evolution_enabled: false,
        runtime_diagnostic_schema_version: "shape_contact_runtime_diagnostic_v1".to_string(),
        experimental_status: "internal_runtime_smoke_only".to_string(),
        warnings: vec![
            "shape_contact_v0 runtime smoke is opt-in internal verification plumbing"
                .to_string(),
            "shape_contact_v0 is uncalibrated, non-operational, not RAMMS-equivalent, and not benchmark-validated"
                .to_string(),
        ],
        limitations: vec![
            "missing projection correction".to_string(),
            "missing persistent contact".to_string(),
            "missing orientation evolution".to_string(),
            "missing multi-contact".to_string(),
            "missing public benchmark evidence".to_string(),
        ],
    }
}

#[allow(dead_code)]
fn shape_contact_v0_internal_runtime_smoke_step<T: crate::terrain::Terrain>(
    metadata: &BlockShapeMetadata,
    terrain: &T,
    input: ShapeContactV0RuntimeSmokeInput,
) -> Result<ShapeContactV0RuntimeSmokeResult, ShapeMetadataError> {
    shape_contact_v0_internal_runtime_smoke_step_with_provenance(
        metadata, terrain, input, None, None,
    )
}

#[allow(dead_code)]
fn shape_contact_v0_internal_integrator_smoke_step_from_metadata_file<
    T: crate::terrain::Terrain,
>(
    metadata_path: &Path,
    terrain: &T,
    input: ShapeContactV0RuntimeSmokeInput,
) -> Result<ShapeContactV0RuntimeSmokeResult, ShapeMetadataError> {
    let text = fs::read_to_string(metadata_path)?;
    let metadata: BlockShapeMetadata = serde_yaml::from_str(&text)?;
    metadata.validate()?;
    shape_contact_v0_internal_runtime_smoke_step_with_provenance(
        &metadata,
        terrain,
        input,
        Some(metadata_path.display().to_string()),
        Some(sha256_hex(text.as_bytes())),
    )
}

#[allow(dead_code)]
fn shape_contact_v0_internal_runtime_smoke_step_with_provenance<T: crate::terrain::Terrain>(
    metadata: &BlockShapeMetadata,
    terrain: &T,
    input: ShapeContactV0RuntimeSmokeInput,
    shape_metadata_path: Option<String>,
    shape_metadata_sha256: Option<String>,
) -> Result<ShapeContactV0RuntimeSmokeResult, ShapeMetadataError> {
    if input.contact_model != crate::dynamics::ContactModel::ShapeContactV0 {
        return Err(ShapeMetadataError::Invalid(
            "shape_contact_v0 runtime smoke requires contact_model shape_contact_v0".to_string(),
        ));
    }
    let scaffold = ShapeContactV0Scaffold::from_metadata(metadata)?;
    let mini_step = shape_contact_v0_mini_fixed_step(
        &scaffold,
        terrain,
        ShapeContactV0MiniFixedStepInput {
            pre_step_state: input.pre_step_state,
            dt_s: input.dt_s,
            gravity_mps2: input.gravity_mps2,
            settings: input.settings,
        },
    )?;
    let diagnostic_input = ShapeContactV0ContactInput {
        pre_state: mini_step.predicted_state,
        terrain_contact_point_m: Vec3::new(
            mini_step.terrain_contact_point_m[0],
            mini_step.terrain_contact_point_m[1],
            mini_step.terrain_contact_point_m[2],
        ),
        terrain_normal_world: Vec3::new(
            mini_step.terrain_normal_world[0],
            mini_step.terrain_normal_world[1],
            mini_step.terrain_normal_world[2],
        ),
        settings: input.settings,
    };
    let row = shape_contact_v0_runtime_diagnostic_row_v1(
        &scaffold,
        &diagnostic_input,
        &mini_step.contact,
        ShapeContactV0RuntimeDiagnosticIdentity {
            case_id: "shape_contact_v0_internal_runtime_smoke",
            trajectory_id: "runtime_smoke_trajectory_000001",
            step_index: input.step_index,
            time_s: input.time_s,
            contact_event_id: None,
            impact_index: None,
        },
    )?;
    let mut writer = ShapeContactV0RuntimeDiagnosticWriterV1::new();
    writer.write_row(row);

    Ok(ShapeContactV0RuntimeSmokeResult {
        pre_step_state: mini_step.pre_step_state,
        predicted_state: mini_step.predicted_state,
        terrain_contact_point_m: mini_step.terrain_contact_point_m,
        terrain_normal_world: mini_step.terrain_normal_world,
        writer,
        manifest: shape_contact_v0_runtime_smoke_manifest(
            &scaffold,
            shape_metadata_path,
            shape_metadata_sha256,
        ),
    })
}

#[allow(dead_code)]
fn shape_contact_v0_synthetic_terrain_step<T: crate::terrain::Terrain>(
    scaffold: &ShapeContactV0Scaffold,
    terrain: &T,
    input: ShapeContactV0SyntheticTerrainInput,
) -> Result<ShapeContactV0ContactResult, ShapeMetadataError> {
    let terrain_height_m = terrain.height(input.terrain_query_x_m, input.terrain_query_y_m);
    validate_finite_triplet(
        [
            input.terrain_query_x_m,
            input.terrain_query_y_m,
            terrain_height_m,
        ],
        "terrain_query_contact_point",
    )?;
    let terrain_normal_world = terrain.normal(input.terrain_query_x_m, input.terrain_query_y_m);
    scaffold.prepare_contact(ShapeContactV0ContactInput {
        pre_state: input.pre_state,
        terrain_contact_point_m: Vec3::new(
            input.terrain_query_x_m,
            input.terrain_query_y_m,
            terrain_height_m,
        ),
        terrain_normal_world,
        settings: input.settings,
    })
}

#[allow(dead_code)]
fn shape_contact_v0_regime_label_v1(
    contact_regime: ShapeContactV0ContactRegime,
    impulse_applied: bool,
) -> ShapeContactV0RuntimeRegimeLabelV1 {
    match (contact_regime, impulse_applied) {
        (ShapeContactV0ContactRegime::SeparatedMovingAway, _)
        | (ShapeContactV0ContactRegime::SeparatedMovingToward, _) => {
            ShapeContactV0RuntimeRegimeLabelV1::NonImpulsiveSeparated
        }
        (ShapeContactV0ContactRegime::Touching, false) => {
            ShapeContactV0RuntimeRegimeLabelV1::NonImpulsiveTouching
        }
        (ShapeContactV0ContactRegime::Touching, true) => {
            ShapeContactV0RuntimeRegimeLabelV1::ImpulsiveTouching
        }
        (ShapeContactV0ContactRegime::Penetrating, true) => {
            ShapeContactV0RuntimeRegimeLabelV1::ImpulsivePenetrating
        }
        (ShapeContactV0ContactRegime::Penetrating, false) => {
            ShapeContactV0RuntimeRegimeLabelV1::NonImpulsivePenetrating
        }
    }
}

#[allow(dead_code)]
fn shape_contact_v0_runtime_diagnostic_row_v1(
    scaffold: &ShapeContactV0Scaffold,
    input: &ShapeContactV0ContactInput,
    result: &ShapeContactV0ContactResult,
    identity: ShapeContactV0RuntimeDiagnosticIdentity<'_>,
) -> Result<ShapeContactV0RuntimeDiagnosticRowV1, ShapeMetadataError> {
    validate_finite_triplet(
        [
            input.terrain_normal_world.x,
            input.terrain_normal_world.y,
            input.terrain_normal_world.z,
        ],
        "terrain_normal_world",
    )?;
    let normal_norm = input.terrain_normal_world.norm();
    if normal_norm == 0.0 {
        return Err(ShapeMetadataError::Invalid(
            "terrain_normal_world must be nonzero".to_string(),
        ));
    }
    let terrain_normal = input.terrain_normal_world / normal_norm;
    let diagnostic = &result.impulse_result.diagnostic;
    let energy = &diagnostic.energy;
    let pre_potential_energy_j = energy.pre_total_mechanical_energy_j
        - energy.pre_translational_kinetic_j
        - energy.pre_rotational_kinetic_j;
    let post_potential_energy_j = energy.post_total_mechanical_energy_j
        - energy.post_translational_kinetic_j
        - energy.post_rotational_kinetic_j;
    let rotational_to_translational_energy_ratio_pre = positive_ratio_or_none(
        energy.pre_rotational_kinetic_j,
        energy.pre_translational_kinetic_j,
    );
    let rotational_to_translational_energy_ratio_post = positive_ratio_or_none(
        energy.post_rotational_kinetic_j,
        energy.post_translational_kinetic_j,
    );
    let total_energy_delta_j =
        energy.post_total_mechanical_energy_j - energy.pre_total_mechanical_energy_j;
    ensure_close(
        total_energy_delta_j,
        energy.contact_energy_delta_j,
        "total_energy_delta_j",
        "contact_energy_delta_j",
    )?;

    Ok(ShapeContactV0RuntimeDiagnosticRowV1 {
        shape_contact_runtime_schema_version: "shape_contact_runtime_diagnostic_v1".to_string(),
        case_id: identity.case_id.to_string(),
        trajectory_id: identity.trajectory_id.to_string(),
        step_index: identity.step_index,
        time_s: identity.time_s,
        shape_contact_row_id: format!(
            "{}:shape_contact:{}",
            identity.trajectory_id, identity.step_index
        ),
        contact_event_id: identity.contact_event_id.map(str::to_string),
        impact_index: identity.impact_index,
        active_contact_model: diagnostic.active_contact_model.clone(),
        active_shape_type: diagnostic.active_shape_type.clone(),
        shape_id: scaffold.shape_id.clone(),
        contact_regime: result.contact_regime,
        shape_contact_regime_label: shape_contact_v0_regime_label_v1(
            result.contact_regime,
            diagnostic.impacted,
        ),
        support_signed_gap_m: result.support_signed_gap_m,
        contact_gap_tolerance_m: SHAPE_CONTACT_V0_CONTACT_GAP_TOLERANCE_M,
        terrain_contact_point_x_m: result.terrain_contact_point_m[0],
        terrain_contact_point_y_m: result.terrain_contact_point_m[1],
        terrain_contact_point_z_m: result.terrain_contact_point_m[2],
        terrain_normal_x: terrain_normal.x,
        terrain_normal_y: terrain_normal.y,
        terrain_normal_z: terrain_normal.z,
        support_point_x_m: diagnostic.support_point_m[0],
        support_point_y_m: diagnostic.support_point_m[1],
        support_point_z_m: diagnostic.support_point_m[2],
        support_corner_sign_x: diagnostic.support_corner_signs[0],
        support_corner_sign_y: diagnostic.support_corner_signs[1],
        support_corner_sign_z: diagnostic.support_corner_signs[2],
        support_corner_changed: None,
        contact_point_normal_velocity_pre_mps: diagnostic.pre_contact_normal_velocity_mps,
        contact_point_normal_velocity_post_mps: diagnostic.post_contact_normal_velocity_mps,
        contact_point_tangential_speed_pre_mps: diagnostic.pre_contact_tangential_speed_mps,
        contact_point_tangential_speed_post_mps: diagnostic.post_contact_tangential_speed_mps,
        normal_impulse_n_s: diagnostic.normal_impulse_n_s,
        tangential_impulse_x_n_s: diagnostic.tangential_impulse_n_s[0],
        tangential_impulse_y_n_s: diagnostic.tangential_impulse_n_s[1],
        tangential_impulse_z_n_s: diagnostic.tangential_impulse_n_s[2],
        tangential_impulse_norm_n_s: diagnostic.tangential_impulse_norm_n_s,
        coulomb_friction_cap_n_s: diagnostic.coulomb_friction_cap_n_s,
        coulomb_cap_ratio: if diagnostic.coulomb_friction_cap_n_s > 0.0 {
            Some(diagnostic.coulomb_cap_ratio)
        } else {
            None
        },
        normal_restitution: input.settings.normal_restitution,
        tangential_restitution: input.settings.tangential_restitution,
        friction_coefficient: input.settings.friction_coefficient,
        gravity_mps2: input.settings.gravity_mps2,
        pre_translational_kinetic_j: energy.pre_translational_kinetic_j,
        post_translational_kinetic_j: energy.post_translational_kinetic_j,
        pre_rotational_kinetic_j: energy.pre_rotational_kinetic_j,
        post_rotational_kinetic_j: energy.post_rotational_kinetic_j,
        pre_potential_energy_j,
        post_potential_energy_j,
        pre_total_mechanical_energy_j: energy.pre_total_mechanical_energy_j,
        post_total_mechanical_energy_j: energy.post_total_mechanical_energy_j,
        contact_energy_delta_j: energy.contact_energy_delta_j,
        projection_energy_delta_j: None,
        total_energy_delta_j,
        rotational_to_translational_energy_ratio_pre,
        rotational_to_translational_energy_ratio_post,
        orientation_w: scaffold.orientation_wxyz[0],
        orientation_x: scaffold.orientation_wxyz[1],
        orientation_y: scaffold.orientation_wxyz[2],
        orientation_z: scaffold.orientation_wxyz[3],
        orientation_norm_error: (quaternion_norm(scaffold.orientation_wxyz) - 1.0).abs(),
        orientation_initialization_mode: default_orientation_initialization_mode(),
        impulse_applied: diagnostic.impacted,
        projection_applied: false,
    })
}

#[allow(dead_code)]
fn positive_ratio_or_none(numerator: f64, denominator: f64) -> Option<f64> {
    if denominator > 0.0 {
        Some(numerator / denominator)
    } else {
        None
    }
}

#[allow(dead_code)]
fn sha256_hex(bytes: &[u8]) -> String {
    let mut digest = Sha256::new();
    digest.update(bytes);
    format!("{:x}", digest.finalize())
}

#[allow(dead_code)]
fn shape_contact_v0_mini_fixed_step<T: crate::terrain::Terrain>(
    scaffold: &ShapeContactV0Scaffold,
    terrain: &T,
    input: ShapeContactV0MiniFixedStepInput,
) -> Result<ShapeContactV0MiniFixedStepResult, ShapeMetadataError> {
    validate_positive(input.dt_s, "dt_s")?;
    validate_positive(input.gravity_mps2, "gravity_mps2")?;
    ensure_close(
        input.settings.gravity_mps2,
        input.gravity_mps2,
        "settings.gravity_mps2",
        "mini_fixed_step.gravity_mps2",
    )?;
    let prediction = crate::integrator::shape_contact_v0_integrator_smoke_prediction(
        input.pre_step_state,
        terrain,
        input.dt_s,
        input.gravity_mps2,
    )
    .map_err(|message| ShapeMetadataError::Invalid(message.to_string()))?;
    let predicted_state = prediction.predicted_state;
    validate_finite_triplet(
        [
            predicted_state.position_m.x,
            predicted_state.position_m.y,
            predicted_state.position_m.z,
        ],
        "predicted_state.position_m",
    )?;
    validate_finite_triplet(
        [
            predicted_state.velocity_mps.x,
            predicted_state.velocity_mps.y,
            predicted_state.velocity_mps.z,
        ],
        "predicted_state.velocity_mps",
    )?;

    let contact = scaffold.prepare_contact(ShapeContactV0ContactInput {
        pre_state: predicted_state,
        terrain_contact_point_m: prediction.terrain_contact_point_m,
        terrain_normal_world: prediction.terrain_normal_world,
        settings: input.settings,
    })?;

    Ok(ShapeContactV0MiniFixedStepResult {
        pre_step_state: prediction.pre_step_state,
        predicted_state,
        terrain_contact_point_m: [
            prediction.terrain_contact_point_m.x,
            prediction.terrain_contact_point_m.y,
            prediction.terrain_contact_point_m.z,
        ],
        terrain_normal_world: [
            prediction.terrain_normal_world.x,
            prediction.terrain_normal_world.y,
            prediction.terrain_normal_world.z,
        ],
        contact,
    })
}

#[allow(dead_code)]
pub(crate) fn shape_contact_v0_no_impulse_result(
    support: &ShapeContactV0SupportDiagnostic,
    input: ShapeContactV0ImpulseInput,
) -> Result<ShapeContactV0ImpulseResult, ShapeMetadataError> {
    let pre_state = input.pre_state;
    validate_finite_triplet(
        [
            pre_state.position_m.x,
            pre_state.position_m.y,
            pre_state.position_m.z,
        ],
        "pre_state.position_m",
    )?;
    validate_finite_triplet(
        [
            pre_state.velocity_mps.x,
            pre_state.velocity_mps.y,
            pre_state.velocity_mps.z,
        ],
        "pre_state.velocity_mps",
    )?;
    validate_finite_triplet(
        [
            pre_state.angular_velocity_radps.x,
            pre_state.angular_velocity_radps.y,
            pre_state.angular_velocity_radps.z,
        ],
        "pre_state.angular_velocity_radps",
    )?;
    validate_positive(input.mass_kg, "mass_kg")?;
    validate_positive_triplet(input.principal_moments_kg_m2, "principal_moments_kg_m2")?;
    validate_positive(input.gravity_mps2, "gravity_mps2")?;
    validate_unit_interval(input.normal_restitution, "normal_restitution")?;
    validate_unit_interval(input.tangential_restitution, "tangential_restitution")?;
    validate_nonnegative(input.friction_coefficient, "friction_coefficient")?;
    validate_finite_triplet(support.support_point_m, "support.support_point_m")?;
    validate_finite_triplet(
        [
            input.terrain_normal_world.x,
            input.terrain_normal_world.y,
            input.terrain_normal_world.z,
        ],
        "terrain_normal_world",
    )?;
    let normal_norm = input.terrain_normal_world.norm();
    if normal_norm == 0.0 {
        return Err(ShapeMetadataError::Invalid(
            "terrain_normal_world must be nonzero".to_string(),
        ));
    }
    let normal = input.terrain_normal_world / normal_norm;
    let support_point = Vec3::new(
        support.support_point_m[0],
        support.support_point_m[1],
        support.support_point_m[2],
    );
    let contact_offset = support_point - pre_state.position_m;
    let contact_velocity = rigid_body_contact_point_velocity(pre_state, contact_offset);
    let normal_velocity = contact_velocity.dot(&normal);
    let tangent_velocity = contact_velocity - normal_velocity * normal;
    let energy = shape_contact_v0_energy_diagnostic(
        &pre_state,
        &pre_state,
        input.mass_kg,
        input.principal_moments_kg_m2,
        input.gravity_mps2,
    )?;
    Ok(ShapeContactV0ImpulseResult {
        post_state: pre_state,
        diagnostic: ShapeContactV0ImpulseDiagnostic {
            active_contact_model: SHAPE_CONTACT_V0_MODEL.to_string(),
            active_shape_type: SHAPE_CONTACT_V0_ACTIVE_SHAPE.to_string(),
            impacted: false,
            support_point_m: support.support_point_m,
            support_corner_signs: support.support_corner_signs,
            contact_point_velocity_pre_mps: [
                contact_velocity.x,
                contact_velocity.y,
                contact_velocity.z,
            ],
            contact_point_velocity_post_mps: [
                contact_velocity.x,
                contact_velocity.y,
                contact_velocity.z,
            ],
            pre_contact_normal_velocity_mps: normal_velocity,
            post_contact_normal_velocity_mps: normal_velocity,
            pre_contact_tangential_speed_mps: tangent_velocity.norm(),
            post_contact_tangential_speed_mps: tangent_velocity.norm(),
            normal_impulse_n_s: 0.0,
            tangential_impulse_n_s: [0.0, 0.0, 0.0],
            tangential_impulse_norm_n_s: 0.0,
            coulomb_friction_cap_n_s: 0.0,
            coulomb_cap_ratio: 0.0,
            energy,
        },
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::terrain::{Plane, Terrain};
    use std::time::{SystemTime, UNIX_EPOCH};

    fn assert_close(actual: f64, expected: f64, epsilon: f64) {
        assert!(
            (actual - expected).abs() <= epsilon,
            "expected {expected}, got {actual}"
        );
    }

    fn test_scaffold(mass_kg: f64, principal_dimensions_m: [f64; 3]) -> ShapeContactV0Scaffold {
        ShapeContactV0Scaffold {
            active_contact_model: SHAPE_CONTACT_V0_MODEL.to_string(),
            active_shape_type: SHAPE_CONTACT_V0_ACTIVE_SHAPE.to_string(),
            shape_id: "unit_test_box".to_string(),
            mass_kg,
            principal_dimensions_m,
            principal_moments_kg_m2: box_principal_moments_kg_m2(mass_kg, principal_dimensions_m),
            orientation_wxyz: default_identity_quaternion(),
        }
    }

    fn test_shape_metadata(mass_kg: f64, principal_dimensions_m: [f64; 3]) -> BlockShapeMetadata {
        BlockShapeMetadata {
            schema_version: SHAPE_METADATA_SCHEMA_VERSION.to_string(),
            shape_id: "unit_test_box".to_string(),
            shape_type: BlockShapeType::PrincipalDimensions,
            shape_class: Some("box_runtime_smoke_fixture".to_string()),
            dimensions_m: ShapeDimensions {
                principal_lengths_m: Some(principal_dimensions_m),
                equivalent_radius_m: Some(1.0),
                ..ShapeDimensions::default()
            },
            mass_properties: ShapeMassProperties {
                mass_kg,
                density_kgpm3: None,
                mass_property_model: Some(MassPropertyModel::BoxPrincipalDimensions),
                principal_moments_kg_m2: None,
                center_of_mass_offset_m: None,
            },
            orientation: ShapeOrientation::default(),
            provenance: ShapeProvenance::default(),
        }
    }

    fn temp_shape_contact_path(name: &str, extension: &str) -> std::path::PathBuf {
        let nonce = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_nanos();
        std::env::temp_dir().join(format!(
            "rust_rockfall_shape_contact_v0_{nonce}_{name}.{extension}"
        ))
    }

    fn write_test_shape_metadata_file(
        metadata: &BlockShapeMetadata,
        name: &str,
    ) -> std::path::PathBuf {
        let path = temp_shape_contact_path(name, "yaml");
        let yaml = serde_yaml::to_string(metadata).unwrap();
        fs::write(&path, yaml).unwrap();
        path
    }

    fn runtime_smoke_input(
        pre_step_state: BodyState,
        step_index: u64,
    ) -> ShapeContactV0RuntimeSmokeInput {
        ShapeContactV0RuntimeSmokeInput {
            contact_model: crate::dynamics::ContactModel::ShapeContactV0,
            pre_step_state,
            dt_s: 0.1,
            gravity_mps2: 9.81,
            settings: settings(0.5, 0.0, 0.4),
            step_index,
            time_s: step_index as f64 * 0.1,
        }
    }

    fn shape_contact_v0_internal_integrator_smoke_fixture() -> Vec<ShapeContactV0RuntimeSmokeResult>
    {
        let metadata = test_shape_metadata(2.0, [2.0, 2.0, 2.0]);
        let metadata_path = write_test_shape_metadata_file(&metadata, "internal_integrator_smoke");
        let flat = Plane::horizontal(0.0);
        let inclined = Plane {
            z0_m: 0.0,
            slope_x: 0.2,
            slope_y: -0.1,
        };
        let cases = vec![
            shape_contact_v0_internal_integrator_smoke_step_from_metadata_file(
                &metadata_path,
                &flat,
                runtime_smoke_input(
                    BodyState::new(Vec3::new(0.0, 0.0, 1.2), Vec3::new(0.0, 0.0, -1.5095)),
                    1,
                ),
            )
            .unwrap(),
            shape_contact_v0_internal_integrator_smoke_step_from_metadata_file(
                &metadata_path,
                &flat,
                runtime_smoke_input(
                    BodyState::new(Vec3::new(0.0, 0.0, 3.0), Vec3::new(0.0, 0.0, -1.0)),
                    2,
                ),
            )
            .unwrap(),
            shape_contact_v0_internal_integrator_smoke_step_from_metadata_file(
                &metadata_path,
                &flat,
                runtime_smoke_input(
                    BodyState::new(Vec3::new(0.0, 0.0, 0.8), Vec3::new(0.0, 0.0, 1.4905)),
                    3,
                ),
            )
            .unwrap(),
            shape_contact_v0_internal_integrator_smoke_step_from_metadata_file(
                &metadata_path,
                &inclined,
                runtime_smoke_input(
                    BodyState::new(Vec3::new(0.0, 0.0, 2.0), Vec3::new(0.0, 0.0, -1.0)),
                    4,
                ),
            )
            .unwrap(),
        ];
        fs::remove_file(&metadata_path).unwrap();
        cases
    }

    fn settings(
        normal_restitution: f64,
        tangential_restitution: f64,
        friction_coefficient: f64,
    ) -> ShapeContactV0ImpulseSettings {
        ShapeContactV0ImpulseSettings {
            normal_restitution,
            tangential_restitution,
            friction_coefficient,
            gravity_mps2: 9.81,
        }
    }

    fn settings_with_gravity(
        normal_restitution: f64,
        tangential_restitution: f64,
        friction_coefficient: f64,
        gravity_mps2: f64,
    ) -> ShapeContactV0ImpulseSettings {
        ShapeContactV0ImpulseSettings {
            normal_restitution,
            tangential_restitution,
            friction_coefficient,
            gravity_mps2,
        }
    }

    fn runtime_identity(step_index: u64) -> ShapeContactV0RuntimeDiagnosticIdentity<'static> {
        ShapeContactV0RuntimeDiagnosticIdentity {
            case_id: "shape_contract_case",
            trajectory_id: "trajectory_000001",
            step_index,
            time_s: step_index as f64 * 0.01,
            contact_event_id: None,
            impact_index: None,
        }
    }

    fn assert_shape_contact_runtime_diagnostic_fields(value: &serde_json::Value) {
        let object = value.as_object().expect("diagnostic row must be an object");
        let actual: std::collections::BTreeSet<_> = object.keys().map(String::as_str).collect();
        let expected: std::collections::BTreeSet<_> = [
            "shape_contact_runtime_schema_version",
            "case_id",
            "trajectory_id",
            "step_index",
            "time_s",
            "shape_contact_row_id",
            "contact_event_id",
            "impact_index",
            "active_contact_model",
            "active_shape_type",
            "shape_id",
            "contact_regime",
            "shape_contact_regime_label",
            "support_signed_gap_m",
            "contact_gap_tolerance_m",
            "terrain_contact_point_x_m",
            "terrain_contact_point_y_m",
            "terrain_contact_point_z_m",
            "terrain_normal_x",
            "terrain_normal_y",
            "terrain_normal_z",
            "support_point_x_m",
            "support_point_y_m",
            "support_point_z_m",
            "support_corner_sign_x",
            "support_corner_sign_y",
            "support_corner_sign_z",
            "support_corner_changed",
            "contact_point_normal_velocity_pre_mps",
            "contact_point_normal_velocity_post_mps",
            "contact_point_tangential_speed_pre_mps",
            "contact_point_tangential_speed_post_mps",
            "normal_impulse_n_s",
            "tangential_impulse_x_n_s",
            "tangential_impulse_y_n_s",
            "tangential_impulse_z_n_s",
            "tangential_impulse_norm_n_s",
            "coulomb_friction_cap_n_s",
            "coulomb_cap_ratio",
            "normal_restitution",
            "tangential_restitution",
            "friction_coefficient",
            "gravity_mps2",
            "pre_translational_kinetic_j",
            "post_translational_kinetic_j",
            "pre_rotational_kinetic_j",
            "post_rotational_kinetic_j",
            "pre_potential_energy_j",
            "post_potential_energy_j",
            "pre_total_mechanical_energy_j",
            "post_total_mechanical_energy_j",
            "contact_energy_delta_j",
            "projection_energy_delta_j",
            "total_energy_delta_j",
            "rotational_to_translational_energy_ratio_pre",
            "rotational_to_translational_energy_ratio_post",
            "orientation_w",
            "orientation_x",
            "orientation_y",
            "orientation_z",
            "orientation_norm_error",
            "orientation_initialization_mode",
            "impulse_applied",
            "projection_applied",
        ]
        .into_iter()
        .collect();
        assert_eq!(actual, expected);
    }

    fn shape_contact_v0_runtime_diagnostic_fixture_rows(
    ) -> Vec<ShapeContactV0RuntimeDiagnosticRowV1> {
        let scaffold = test_scaffold(2.0, [2.0, 2.0, 2.0]);
        let separated_input = ShapeContactV0ContactInput {
            pre_state: BodyState::new(Vec3::new(0.0, 0.0, 1.5), Vec3::new(0.0, 0.0, -1.0)),
            terrain_contact_point_m: Vec3::new(1.0, 1.0, 0.0),
            terrain_normal_world: Vec3::new(0.0, 0.0, 2.0),
            settings: settings(0.25, 0.75, 0.2),
        };
        let impulsive_input = ShapeContactV0ContactInput {
            pre_state: BodyState::new(Vec3::new(0.0, 0.0, 1.0), Vec3::new(3.0, 0.0, -2.0)),
            terrain_contact_point_m: Vec3::new(1.0, 1.0, 0.0),
            terrain_normal_world: Vec3::new(0.0, 0.0, 1.0),
            settings: settings(0.5, 0.0, 0.4),
        };
        let penetrating_input = ShapeContactV0ContactInput {
            pre_state: BodyState::new(Vec3::new(0.0, 0.0, 0.9), Vec3::new(0.0, 0.0, 1.0)),
            terrain_contact_point_m: Vec3::new(1.0, 1.0, 0.0),
            terrain_normal_world: Vec3::new(0.0, 0.0, 1.0),
            settings: settings(0.5, 0.0, 0.4),
        };
        let separated_result =
            shape_contact_v0_contact_dry_run(&scaffold, separated_input).unwrap();
        let impulsive_result =
            shape_contact_v0_contact_dry_run(&scaffold, impulsive_input).unwrap();
        let penetrating_result =
            shape_contact_v0_contact_dry_run(&scaffold, penetrating_input).unwrap();

        vec![
            shape_contact_v0_runtime_diagnostic_row_v1(
                &scaffold,
                &separated_input,
                &separated_result,
                runtime_identity(7),
            )
            .unwrap(),
            shape_contact_v0_runtime_diagnostic_row_v1(
                &scaffold,
                &impulsive_input,
                &impulsive_result,
                ShapeContactV0RuntimeDiagnosticIdentity {
                    case_id: "shape_contract_case",
                    trajectory_id: "trajectory_000002",
                    step_index: 11,
                    time_s: 0.11,
                    contact_event_id: Some("impact_000003"),
                    impact_index: Some(3),
                },
            )
            .unwrap(),
            shape_contact_v0_runtime_diagnostic_row_v1(
                &scaffold,
                &penetrating_input,
                &penetrating_result,
                ShapeContactV0RuntimeDiagnosticIdentity {
                    case_id: "shape_contract_case",
                    trajectory_id: "trajectory_000003",
                    step_index: 13,
                    time_s: 0.13,
                    contact_event_id: None,
                    impact_index: None,
                },
            )
            .unwrap(),
        ]
    }

    #[test]
    fn shape_contact_v0_test_step_off_center_normal_impact_updates_angular_velocity() {
        let scaffold = test_scaffold(2.0, [2.0, 2.0, 2.0]);
        let result = shape_contact_v0_test_contact_step(
            &scaffold,
            ShapeContactV0TestContactStepInput {
                pre_state: BodyState::new(Vec3::new(0.0, 0.0, 1.0), Vec3::new(0.0, 0.0, -2.0)),
                terrain_normal_world: Vec3::new(0.0, 0.0, 1.0),
                settings: settings(0.0, 1.0, 0.0),
            },
        )
        .unwrap();

        assert!(result.diagnostic.impacted);
        let impulse = result.diagnostic.normal_impulse_n_s;
        assert!(impulse > 0.0);
        assert_close(
            result.post_state.angular_velocity_radps.x,
            impulse / scaffold.principal_moments_kg_m2[0],
            1.0e-12,
        );
        assert_close(
            result.post_state.angular_velocity_radps.y,
            -impulse / scaffold.principal_moments_kg_m2[1],
            1.0e-12,
        );
        assert_close(result.post_state.angular_velocity_radps.z, 0.0, 1.0e-12);
    }

    #[test]
    fn shape_contact_v0_test_step_matches_normal_restitution() {
        let scaffold = test_scaffold(2.0, [2.0, 2.0, 2.0]);
        let result = shape_contact_v0_test_contact_step(
            &scaffold,
            ShapeContactV0TestContactStepInput {
                pre_state: BodyState::new(Vec3::new(0.0, 0.0, 1.0), Vec3::new(0.0, 0.0, -2.0)),
                terrain_normal_world: Vec3::new(0.0, 0.0, 1.0),
                settings: settings(0.5, 1.0, 0.0),
            },
        )
        .unwrap();

        assert!(result.diagnostic.impacted);
        assert_close(
            result.diagnostic.pre_contact_normal_velocity_mps,
            -2.0,
            1.0e-12,
        );
        assert_close(
            result.diagnostic.post_contact_normal_velocity_mps,
            1.0,
            1.0e-12,
        );
        assert_close(result.diagnostic.tangential_impulse_norm_n_s, 0.0, 1.0e-12);
    }

    #[test]
    fn shape_contact_v0_test_step_tangential_impulse_respects_coulomb_cap() {
        let scaffold = test_scaffold(2.0, [2.0, 2.0, 2.0]);
        let result = shape_contact_v0_test_contact_step(
            &scaffold,
            ShapeContactV0TestContactStepInput {
                pre_state: BodyState::new(Vec3::new(0.0, 0.0, 1.0), Vec3::new(6.0, 0.0, -2.0)),
                terrain_normal_world: Vec3::new(0.0, 0.0, 1.0),
                settings: settings(0.2, 0.0, 0.01),
            },
        )
        .unwrap();

        assert!(result.diagnostic.coulomb_friction_cap_n_s > 0.0);
        assert_close(
            result.diagnostic.tangential_impulse_norm_n_s,
            result.diagnostic.coulomb_friction_cap_n_s,
            1.0e-12,
        );
        assert!(result.diagnostic.coulomb_cap_ratio <= 1.0 + 1.0e-12);
    }

    #[test]
    fn shape_contact_v0_test_step_zero_incoming_normal_velocity_has_no_normal_impulse() {
        let scaffold = test_scaffold(2.0, [2.0, 2.0, 2.0]);
        let pre_state = BodyState::new(Vec3::new(0.0, 0.0, 1.0), Vec3::new(1.0, 0.0, 0.0));
        let result = shape_contact_v0_test_contact_step(
            &scaffold,
            ShapeContactV0TestContactStepInput {
                pre_state,
                terrain_normal_world: Vec3::new(0.0, 0.0, 1.0),
                settings: settings(0.5, 0.0, 1.0),
            },
        )
        .unwrap();

        assert!(!result.diagnostic.impacted);
        assert_close(
            result.diagnostic.pre_contact_normal_velocity_mps,
            0.0,
            1.0e-12,
        );
        assert_close(result.diagnostic.normal_impulse_n_s, 0.0, 1.0e-12);
        assert_eq!(result.post_state, pre_state);
    }

    #[test]
    fn shape_contact_v0_test_step_zero_initial_tangent_speed_is_finite() {
        let scaffold = test_scaffold(2.0, [2.0, 2.0, 2.0]);
        let result = shape_contact_v0_test_contact_step(
            &scaffold,
            ShapeContactV0TestContactStepInput {
                pre_state: BodyState::new(Vec3::new(0.0, 0.0, 1.0), Vec3::new(0.0, 0.0, -2.0)),
                terrain_normal_world: Vec3::new(0.0, 0.0, 1.0),
                settings: settings(0.0, 0.0, 0.0),
            },
        )
        .unwrap();

        assert_close(
            result.diagnostic.pre_contact_tangential_speed_mps,
            0.0,
            1.0e-12,
        );
        assert_close(result.diagnostic.tangential_impulse_norm_n_s, 0.0, 1.0e-12);
        assert!(result
            .diagnostic
            .post_contact_tangential_speed_mps
            .is_finite());
        assert_close(result.diagnostic.coulomb_cap_ratio, 0.0, 1.0e-12);
    }

    #[test]
    fn shape_contact_v0_test_step_dissipative_contact_does_not_create_energy() {
        let scaffold = test_scaffold(3.0, [2.0, 3.0, 4.0]);
        let mut pre_state = BodyState::new(Vec3::new(0.0, 0.0, 3.0), Vec3::new(3.0, -1.0, -2.0));
        pre_state.angular_velocity_radps = Vec3::new(0.2, -0.1, 0.3);
        let result = shape_contact_v0_test_contact_step(
            &scaffold,
            ShapeContactV0TestContactStepInput {
                pre_state,
                terrain_normal_world: Vec3::new(0.0, 0.0, 1.0),
                settings: settings(0.4, 0.0, 0.8),
            },
        )
        .unwrap();

        assert!(result.diagnostic.energy.contact_energy_delta_j <= 1.0e-10);
    }

    #[test]
    fn shape_contact_v0_test_step_identity_quaternion_remains_normalized() {
        let scaffold = test_scaffold(2.0, [2.0, 2.0, 2.0]);
        let result = shape_contact_v0_test_contact_step(
            &scaffold,
            ShapeContactV0TestContactStepInput {
                pre_state: BodyState::new(Vec3::new(0.0, 0.0, 1.0), Vec3::new(0.0, 0.0, -2.0)),
                terrain_normal_world: Vec3::new(0.0, 0.0, 1.0),
                settings: settings(0.0, 0.0, 0.0),
            },
        )
        .unwrap();

        assert_eq!(
            result.diagnostic.active_contact_model,
            SHAPE_CONTACT_V0_MODEL
        );
        assert_close(quaternion_norm(scaffold.orientation_wxyz), 1.0, 1.0e-12);
    }

    #[test]
    fn shape_contact_v0_test_step_couples_support_mass_and_inertia() {
        let scaffold = test_scaffold(12.0, [2.0, 4.0, 6.0]);
        let pre_state = BodyState::new(Vec3::new(10.0, 20.0, 30.0), Vec3::new(0.0, 0.0, -1.0));
        let support = scaffold
            .support_point(pre_state.position_m, Vec3::new(0.0, 0.0, 1.0))
            .unwrap();
        let result = shape_contact_v0_test_contact_step(
            &scaffold,
            ShapeContactV0TestContactStepInput {
                pre_state,
                terrain_normal_world: Vec3::new(0.0, 0.0, 1.0),
                settings: settings(0.25, 0.5, 0.1),
            },
        )
        .unwrap();

        assert_eq!(support.support_corner_signs, [1, 1, -1]);
        assert_close(support.support_point_m[0], 11.0, 1.0e-12);
        assert_close(support.support_point_m[1], 22.0, 1.0e-12);
        assert_close(support.support_point_m[2], 27.0, 1.0e-12);
        assert_eq!(result.diagnostic.support_point_m, support.support_point_m);
    }

    #[test]
    fn shape_contact_v0_test_step_rejects_invalid_orientation() {
        let mut scaffold = test_scaffold(2.0, [2.0, 2.0, 2.0]);
        scaffold.orientation_wxyz = [
            std::f64::consts::FRAC_1_SQRT_2,
            0.0,
            std::f64::consts::FRAC_1_SQRT_2,
            0.0,
        ];
        let error = shape_contact_v0_test_contact_step(
            &scaffold,
            ShapeContactV0TestContactStepInput {
                pre_state: BodyState::new(Vec3::new(0.0, 0.0, 1.0), Vec3::new(0.0, 0.0, -2.0)),
                terrain_normal_world: Vec3::new(0.0, 0.0, 1.0),
                settings: settings(0.0, 0.0, 0.0),
            },
        )
        .unwrap_err()
        .to_string();
        assert!(error.contains("identity orientation only"));
    }

    #[test]
    fn shape_contact_v0_dry_run_separated_moving_away_has_no_normal_impulse() {
        let scaffold = test_scaffold(2.0, [2.0, 2.0, 2.0]);
        let pre_state = BodyState::new(Vec3::new(0.0, 0.0, 1.0), Vec3::new(0.0, 0.0, 0.5));
        let result = shape_contact_v0_contact_dry_run(
            &scaffold,
            ShapeContactV0DryRunInput {
                pre_state,
                terrain_contact_point_m: Vec3::new(1.0, 1.0, -0.25),
                terrain_normal_world: Vec3::new(0.0, 0.0, 1.0),
                settings: settings(0.5, 0.0, 1.0),
            },
        )
        .unwrap();

        assert!(!result.impulse_result.diagnostic.impacted);
        assert_eq!(
            result.contact_regime,
            ShapeContactV0DryRunContactRegime::SeparatedMovingAway
        );
        assert_close(result.support_signed_gap_m, 0.25, 1.0e-12);
        assert_close(
            result.impulse_result.diagnostic.normal_impulse_n_s,
            0.0,
            1.0e-12,
        );
        assert_eq!(result.impulse_result.post_state, pre_state);
    }

    #[test]
    fn shape_contact_v0_dry_run_separated_moving_toward_has_no_normal_impulse() {
        let scaffold = test_scaffold(2.0, [2.0, 2.0, 2.0]);
        let pre_state = BodyState::new(Vec3::new(0.0, 0.0, 1.0), Vec3::new(0.0, 0.0, -2.0));
        let result = shape_contact_v0_contact_dry_run(
            &scaffold,
            ShapeContactV0DryRunInput {
                pre_state,
                terrain_contact_point_m: Vec3::new(1.0, 1.0, -0.25),
                terrain_normal_world: Vec3::new(0.0, 0.0, 1.0),
                settings: settings(0.5, 0.0, 1.0),
            },
        )
        .unwrap();

        assert!(!result.impulse_result.diagnostic.impacted);
        assert_eq!(
            result.contact_regime,
            ShapeContactV0DryRunContactRegime::SeparatedMovingToward
        );
        assert_close(result.support_signed_gap_m, 0.25, 1.0e-12);
        assert_close(
            result.impulse_result.diagnostic.normal_impulse_n_s,
            0.0,
            1.0e-12,
        );
        assert_eq!(result.impulse_result.post_state, pre_state);
    }

    #[test]
    fn shape_contact_v0_dry_run_touching_incoming_contact_rebounds_along_normal() {
        let scaffold = test_scaffold(2.0, [2.0, 2.0, 2.0]);
        let result = shape_contact_v0_contact_dry_run(
            &scaffold,
            ShapeContactV0DryRunInput {
                pre_state: BodyState::new(Vec3::new(0.0, 0.0, 1.0), Vec3::new(0.0, 0.0, -2.0)),
                terrain_contact_point_m: Vec3::new(1.0, 1.0, 0.0),
                terrain_normal_world: Vec3::new(0.0, 0.0, 1.0),
                settings: settings(0.5, 1.0, 0.0),
            },
        )
        .unwrap();

        assert!(result.impulse_result.diagnostic.impacted);
        assert_eq!(
            result.contact_regime,
            ShapeContactV0DryRunContactRegime::Touching
        );
        assert_close(
            result
                .impulse_result
                .diagnostic
                .post_contact_normal_velocity_mps,
            1.0,
            1.0e-12,
        );
        assert!(
            result
                .impulse_result
                .diagnostic
                .post_contact_normal_velocity_mps
                > 0.0
        );
    }

    #[test]
    fn shape_contact_v0_dry_run_touching_non_incoming_contact_has_no_impulse() {
        let scaffold = test_scaffold(2.0, [2.0, 2.0, 2.0]);
        let pre_state = BodyState::new(Vec3::new(0.0, 0.0, 1.0), Vec3::new(0.0, 0.0, 0.5));
        let result = shape_contact_v0_contact_dry_run(
            &scaffold,
            ShapeContactV0DryRunInput {
                pre_state,
                terrain_contact_point_m: Vec3::new(1.0, 1.0, 0.0),
                terrain_normal_world: Vec3::new(0.0, 0.0, 1.0),
                settings: settings(0.5, 1.0, 0.0),
            },
        )
        .unwrap();

        assert!(!result.impulse_result.diagnostic.impacted);
        assert_eq!(
            result.contact_regime,
            ShapeContactV0DryRunContactRegime::Touching
        );
        assert_close(
            result.impulse_result.diagnostic.normal_impulse_n_s,
            0.0,
            1.0e-12,
        );
        assert_eq!(result.impulse_result.post_state, pre_state);
    }

    #[test]
    fn shape_contact_v0_dry_run_penetrating_incoming_contact_rebounds_along_normal() {
        let scaffold = test_scaffold(2.0, [2.0, 2.0, 2.0]);
        let result = shape_contact_v0_contact_dry_run(
            &scaffold,
            ShapeContactV0DryRunInput {
                pre_state: BodyState::new(Vec3::new(0.0, 0.0, 1.0), Vec3::new(0.0, 0.0, -2.0)),
                terrain_contact_point_m: Vec3::new(1.0, 1.0, 0.25),
                terrain_normal_world: Vec3::new(0.0, 0.0, 1.0),
                settings: settings(0.5, 1.0, 0.0),
            },
        )
        .unwrap();

        assert!(result.impulse_result.diagnostic.impacted);
        assert_eq!(
            result.contact_regime,
            ShapeContactV0DryRunContactRegime::Penetrating
        );
        assert_close(result.support_signed_gap_m, -0.25, 1.0e-12);
        assert_close(
            result
                .impulse_result
                .diagnostic
                .post_contact_normal_velocity_mps,
            1.0,
            1.0e-12,
        );
    }

    #[test]
    fn shape_contact_v0_dry_run_penetrating_moving_away_has_no_impulse() {
        let scaffold = test_scaffold(2.0, [2.0, 2.0, 2.0]);
        let pre_state = BodyState::new(Vec3::new(0.0, 0.0, 1.0), Vec3::new(0.0, 0.0, 0.5));
        let result = shape_contact_v0_contact_dry_run(
            &scaffold,
            ShapeContactV0DryRunInput {
                pre_state,
                terrain_contact_point_m: Vec3::new(1.0, 1.0, 0.25),
                terrain_normal_world: Vec3::new(0.0, 0.0, 1.0),
                settings: settings(0.5, 1.0, 0.0),
            },
        )
        .unwrap();

        assert!(!result.impulse_result.diagnostic.impacted);
        assert_eq!(
            result.contact_regime,
            ShapeContactV0DryRunContactRegime::Penetrating
        );
        assert_close(result.support_signed_gap_m, -0.25, 1.0e-12);
        assert_close(
            result.impulse_result.diagnostic.normal_impulse_n_s,
            0.0,
            1.0e-12,
        );
        assert_eq!(result.impulse_result.post_state, pre_state);
    }

    #[test]
    fn shape_contact_v0_dry_run_handles_inclined_normal_deterministically() {
        let scaffold = test_scaffold(2.0, [2.0, 2.0, 2.0]);
        let normal = Vec3::new(0.0, 1.0, 1.0);
        let result = shape_contact_v0_contact_dry_run(
            &scaffold,
            ShapeContactV0DryRunInput {
                pre_state: BodyState::new(Vec3::new(0.0, 0.0, 1.0), -2.0 * normal.normalize()),
                terrain_contact_point_m: Vec3::new(1.0, -1.0, 0.0),
                terrain_normal_world: normal,
                settings: settings(0.25, 1.0, 0.0),
            },
        )
        .unwrap();

        assert_eq!(
            result.impulse_result.diagnostic.support_corner_signs,
            [1, -1, -1]
        );
        assert_eq!(
            result.contact_regime,
            ShapeContactV0DryRunContactRegime::Touching
        );
        assert_close(result.support_signed_gap_m, 0.0, 1.0e-12);
        assert!(
            result
                .impulse_result
                .diagnostic
                .post_contact_normal_velocity_mps
                > 0.0
        );
    }

    #[test]
    fn shape_contact_v0_dry_run_flat_tie_break_remains_reproducible() {
        let scaffold = test_scaffold(2.0, [2.0, 2.0, 2.0]);
        let first = shape_contact_v0_contact_dry_run(
            &scaffold,
            ShapeContactV0DryRunInput {
                pre_state: BodyState::new(Vec3::new(0.0, 0.0, 1.0), Vec3::new(0.0, 0.0, -1.0)),
                terrain_contact_point_m: Vec3::new(1.0, 1.0, 0.0),
                terrain_normal_world: Vec3::new(0.0, 0.0, 1.0),
                settings: settings(0.0, 1.0, 0.0),
            },
        )
        .unwrap();
        let second = shape_contact_v0_contact_dry_run(
            &scaffold,
            ShapeContactV0DryRunInput {
                pre_state: BodyState::new(Vec3::new(0.0, 0.0, 1.0), Vec3::new(0.0, 0.0, -1.0)),
                terrain_contact_point_m: Vec3::new(1.0, 1.0, 0.0),
                terrain_normal_world: Vec3::new(0.0, 0.0, 1.0),
                settings: settings(0.0, 1.0, 0.0),
            },
        )
        .unwrap();

        assert_eq!(
            first.impulse_result.diagnostic.support_corner_signs,
            [1, 1, -1]
        );
        assert_eq!(
            first.impulse_result.diagnostic.support_corner_signs,
            second.impulse_result.diagnostic.support_corner_signs
        );
        assert_eq!(first.terrain_contact_point_m, [1.0, 1.0, 0.0]);
    }

    #[test]
    fn shape_contact_v0_dry_run_dissipative_contact_does_not_create_energy() {
        let scaffold = test_scaffold(3.0, [2.0, 3.0, 4.0]);
        let mut pre_state = BodyState::new(Vec3::new(0.0, 0.0, 3.0), Vec3::new(3.0, -1.0, -2.0));
        pre_state.angular_velocity_radps = Vec3::new(0.2, -0.1, 0.3);
        let result = shape_contact_v0_contact_dry_run(
            &scaffold,
            ShapeContactV0DryRunInput {
                pre_state,
                terrain_contact_point_m: Vec3::new(1.0, 1.5, 1.0),
                terrain_normal_world: Vec3::new(0.0, 0.0, 1.0),
                settings: settings(0.4, 0.0, 0.8),
            },
        )
        .unwrap();

        assert!(result.impulse_result.diagnostic.impacted);
        assert!(
            result
                .impulse_result
                .diagnostic
                .energy
                .contact_energy_delta_j
                <= 1.0e-10
        );
    }

    #[test]
    fn shape_contact_v0_runtime_diagnostic_maps_separated_row_contract() {
        let scaffold = test_scaffold(2.0, [2.0, 2.0, 2.0]);
        let input = ShapeContactV0ContactInput {
            pre_state: BodyState::new(Vec3::new(0.0, 0.0, 1.5), Vec3::new(0.0, 0.0, -1.0)),
            terrain_contact_point_m: Vec3::new(1.0, 1.0, 0.0),
            terrain_normal_world: Vec3::new(0.0, 0.0, 2.0),
            settings: settings(0.25, 0.75, 0.2),
        };
        let result = shape_contact_v0_contact_dry_run(&scaffold, input).unwrap();
        let row = shape_contact_v0_runtime_diagnostic_row_v1(
            &scaffold,
            &input,
            &result,
            runtime_identity(7),
        )
        .unwrap();

        assert_eq!(
            row.shape_contact_runtime_schema_version,
            "shape_contact_runtime_diagnostic_v1"
        );
        assert_eq!(row.case_id, "shape_contract_case");
        assert_eq!(row.trajectory_id, "trajectory_000001");
        assert_eq!(row.step_index, 7);
        assert_close(row.time_s, 0.07, 1.0e-12);
        assert_eq!(
            row.shape_contact_row_id,
            "trajectory_000001:shape_contact:7"
        );
        assert_eq!(row.contact_event_id, None);
        assert_eq!(row.impact_index, None);
        assert_eq!(
            row.contact_regime,
            ShapeContactV0ContactRegime::SeparatedMovingToward
        );
        assert_eq!(
            row.shape_contact_regime_label,
            ShapeContactV0RuntimeRegimeLabelV1::NonImpulsiveSeparated
        );
        assert!(!row.impulse_applied);
        assert!(!row.projection_applied);
        assert_eq!(row.projection_energy_delta_j, None);
        assert_eq!(row.coulomb_cap_ratio, None);
        assert_close(row.support_signed_gap_m, 0.5, 1.0e-12);
        assert_close(
            row.contact_gap_tolerance_m,
            SHAPE_CONTACT_V0_CONTACT_GAP_TOLERANCE_M,
            1.0e-18,
        );
        assert_eq!(row.terrain_contact_point_x_m, 1.0);
        assert_eq!(row.terrain_contact_point_y_m, 1.0);
        assert_eq!(row.terrain_contact_point_z_m, 0.0);
        assert_close(row.terrain_normal_x, 0.0, 1.0e-12);
        assert_close(row.terrain_normal_y, 0.0, 1.0e-12);
        assert_close(row.terrain_normal_z, 1.0, 1.0e-12);
        assert_eq!(row.support_corner_changed, None);
        assert_eq!(row.active_contact_model, SHAPE_CONTACT_V0_MODEL);
        assert_eq!(row.active_shape_type, SHAPE_CONTACT_V0_ACTIVE_SHAPE);
        assert_eq!(row.shape_id, scaffold.shape_id);
        assert_close(row.normal_restitution, 0.25, 1.0e-12);
        assert_close(row.tangential_restitution, 0.75, 1.0e-12);
        assert_close(row.friction_coefficient, 0.2, 1.0e-12);
        assert_close(row.gravity_mps2, 9.81, 1.0e-12);
        assert_close(row.normal_impulse_n_s, 0.0, 1.0e-12);
        assert_close(row.tangential_impulse_norm_n_s, 0.0, 1.0e-12);
        assert_close(row.total_energy_delta_j, 0.0, 1.0e-12);
        assert_close(
            row.contact_energy_delta_j,
            row.total_energy_delta_j,
            1.0e-12,
        );
        assert_close(row.orientation_w, 1.0, 1.0e-12);
        assert_close(row.orientation_x, 0.0, 1.0e-12);
        assert_close(row.orientation_y, 0.0, 1.0e-12);
        assert_close(row.orientation_z, 0.0, 1.0e-12);
        assert_close(row.orientation_norm_error, 0.0, 1.0e-12);
        assert_eq!(row.orientation_initialization_mode, "identity");
    }

    #[test]
    fn shape_contact_v0_runtime_diagnostic_maps_touching_impulsive_row_contract() {
        let scaffold = test_scaffold(2.0, [2.0, 2.0, 2.0]);
        let input = ShapeContactV0ContactInput {
            pre_state: BodyState::new(Vec3::new(0.0, 0.0, 1.0), Vec3::new(3.0, 0.0, -2.0)),
            terrain_contact_point_m: Vec3::new(1.0, 1.0, 0.0),
            terrain_normal_world: Vec3::new(0.0, 0.0, 1.0),
            settings: settings(0.5, 0.0, 0.4),
        };
        let result = shape_contact_v0_contact_dry_run(&scaffold, input).unwrap();
        let row = shape_contact_v0_runtime_diagnostic_row_v1(
            &scaffold,
            &input,
            &result,
            ShapeContactV0RuntimeDiagnosticIdentity {
                case_id: "shape_contract_case",
                trajectory_id: "trajectory_000002",
                step_index: 11,
                time_s: 0.11,
                contact_event_id: Some("impact_000003"),
                impact_index: Some(3),
            },
        )
        .unwrap();

        assert_eq!(row.contact_regime, ShapeContactV0ContactRegime::Touching);
        assert_eq!(
            row.shape_contact_regime_label,
            ShapeContactV0RuntimeRegimeLabelV1::ImpulsiveTouching
        );
        assert!(row.impulse_applied);
        assert_eq!(row.contact_event_id.as_deref(), Some("impact_000003"));
        assert_eq!(row.impact_index, Some(3));
        assert_eq!(
            row.shape_contact_row_id,
            "trajectory_000002:shape_contact:11"
        );
        assert_close(row.support_point_x_m, 1.0, 1.0e-12);
        assert_close(row.support_point_y_m, 1.0, 1.0e-12);
        assert_close(row.support_point_z_m, 0.0, 1.0e-12);
        assert_eq!(row.support_corner_sign_x, 1);
        assert_eq!(row.support_corner_sign_y, 1);
        assert_eq!(row.support_corner_sign_z, -1);
        assert!(row.contact_point_normal_velocity_pre_mps < 0.0);
        assert!(row.contact_point_normal_velocity_post_mps > 0.0);
        assert!(row.contact_point_tangential_speed_pre_mps > 0.0);
        assert!(row.normal_impulse_n_s > 0.0);
        assert!(row.tangential_impulse_norm_n_s > 0.0);
        assert!(row.coulomb_friction_cap_n_s > 0.0);
        assert!(row.coulomb_cap_ratio.unwrap() <= 1.0 + 1.0e-12);
        assert_close(
            row.tangential_impulse_norm_n_s,
            (row.tangential_impulse_x_n_s.powi(2)
                + row.tangential_impulse_y_n_s.powi(2)
                + row.tangential_impulse_z_n_s.powi(2))
            .sqrt(),
            1.0e-12,
        );
        assert_close(
            row.total_energy_delta_j,
            row.post_total_mechanical_energy_j - row.pre_total_mechanical_energy_j,
            1.0e-12,
        );
        assert_close(
            row.total_energy_delta_j,
            row.contact_energy_delta_j,
            1.0e-12,
        );
        assert_eq!(row.projection_energy_delta_j, None);
        assert!(!row.projection_applied);
        assert!(row.pre_translational_kinetic_j > 0.0);
        assert!(row.post_translational_kinetic_j > 0.0);
        assert!(row.pre_potential_energy_j > 0.0);
        assert!(row.post_potential_energy_j > 0.0);
    }

    #[test]
    fn shape_contact_v0_runtime_diagnostic_maps_penetrating_non_impulsive_row_contract() {
        let scaffold = test_scaffold(2.0, [2.0, 2.0, 2.0]);
        let input = ShapeContactV0ContactInput {
            pre_state: BodyState::new(Vec3::new(0.0, 0.0, 0.9), Vec3::new(0.0, 0.0, 1.0)),
            terrain_contact_point_m: Vec3::new(1.0, 1.0, 0.0),
            terrain_normal_world: Vec3::new(0.0, 0.0, 1.0),
            settings: settings(0.5, 0.0, 0.4),
        };
        let result = shape_contact_v0_contact_dry_run(&scaffold, input).unwrap();
        let row = shape_contact_v0_runtime_diagnostic_row_v1(
            &scaffold,
            &input,
            &result,
            ShapeContactV0RuntimeDiagnosticIdentity {
                case_id: "shape_contract_case",
                trajectory_id: "trajectory_000003",
                step_index: 13,
                time_s: 0.13,
                contact_event_id: None,
                impact_index: None,
            },
        )
        .unwrap();

        assert_eq!(row.contact_regime, ShapeContactV0ContactRegime::Penetrating);
        assert_eq!(
            row.shape_contact_regime_label,
            ShapeContactV0RuntimeRegimeLabelV1::NonImpulsivePenetrating
        );
        assert!(!row.impulse_applied);
        assert_close(row.support_signed_gap_m, -0.1, 1.0e-12);
        assert!(row.contact_point_normal_velocity_pre_mps > 0.0);
        assert_close(
            row.contact_point_normal_velocity_post_mps,
            row.contact_point_normal_velocity_pre_mps,
            1.0e-12,
        );
        assert_close(row.normal_impulse_n_s, 0.0, 1.0e-12);
        assert_close(row.tangential_impulse_x_n_s, 0.0, 1.0e-12);
        assert_close(row.tangential_impulse_y_n_s, 0.0, 1.0e-12);
        assert_close(row.tangential_impulse_z_n_s, 0.0, 1.0e-12);
        assert_close(row.tangential_impulse_norm_n_s, 0.0, 1.0e-12);
        assert_eq!(row.coulomb_cap_ratio, None);
        assert_eq!(row.projection_energy_delta_j, None);
        assert!(!row.projection_applied);
        assert_close(
            row.total_energy_delta_j,
            row.post_total_mechanical_energy_j - row.pre_total_mechanical_energy_j,
            1.0e-12,
        );
        assert_close(
            row.total_energy_delta_j,
            row.contact_energy_delta_j,
            1.0e-12,
        );
    }

    #[test]
    fn shape_contact_v0_runtime_diagnostic_serializes_frozen_json_contract() {
        let scaffold = test_scaffold(2.0, [2.0, 2.0, 2.0]);
        let separated_input = ShapeContactV0ContactInput {
            pre_state: BodyState::new(Vec3::new(0.0, 0.0, 1.5), Vec3::new(0.0, 0.0, -1.0)),
            terrain_contact_point_m: Vec3::new(1.0, 1.0, 0.0),
            terrain_normal_world: Vec3::new(0.0, 0.0, 2.0),
            settings: settings(0.25, 0.75, 0.2),
        };
        let impulsive_input = ShapeContactV0ContactInput {
            pre_state: BodyState::new(Vec3::new(0.0, 0.0, 1.0), Vec3::new(3.0, 0.0, -2.0)),
            terrain_contact_point_m: Vec3::new(1.0, 1.0, 0.0),
            terrain_normal_world: Vec3::new(0.0, 0.0, 1.0),
            settings: settings(0.5, 0.0, 0.4),
        };
        let penetrating_input = ShapeContactV0ContactInput {
            pre_state: BodyState::new(Vec3::new(0.0, 0.0, 0.9), Vec3::new(0.0, 0.0, 1.0)),
            terrain_contact_point_m: Vec3::new(1.0, 1.0, 0.0),
            terrain_normal_world: Vec3::new(0.0, 0.0, 1.0),
            settings: settings(0.5, 0.0, 0.4),
        };
        let separated_result =
            shape_contact_v0_contact_dry_run(&scaffold, separated_input).unwrap();
        let impulsive_result =
            shape_contact_v0_contact_dry_run(&scaffold, impulsive_input).unwrap();
        let penetrating_result =
            shape_contact_v0_contact_dry_run(&scaffold, penetrating_input).unwrap();

        let rows = vec![
            shape_contact_v0_runtime_diagnostic_row_v1(
                &scaffold,
                &separated_input,
                &separated_result,
                runtime_identity(7),
            )
            .unwrap(),
            shape_contact_v0_runtime_diagnostic_row_v1(
                &scaffold,
                &impulsive_input,
                &impulsive_result,
                ShapeContactV0RuntimeDiagnosticIdentity {
                    case_id: "shape_contract_case",
                    trajectory_id: "trajectory_000002",
                    step_index: 11,
                    time_s: 0.11,
                    contact_event_id: Some("impact_000003"),
                    impact_index: Some(3),
                },
            )
            .unwrap(),
            shape_contact_v0_runtime_diagnostic_row_v1(
                &scaffold,
                &penetrating_input,
                &penetrating_result,
                ShapeContactV0RuntimeDiagnosticIdentity {
                    case_id: "shape_contract_case",
                    trajectory_id: "trajectory_000003",
                    step_index: 13,
                    time_s: 0.13,
                    contact_event_id: None,
                    impact_index: None,
                },
            )
            .unwrap(),
        ];
        let fixture_json = serde_json::to_string_pretty(&rows).unwrap();
        let fixture: serde_json::Value = serde_json::from_str(&fixture_json).unwrap();
        let fixture_rows = fixture.as_array().expect("fixture must be a JSON array");
        assert_eq!(fixture_rows.len(), 3);
        for row in fixture_rows {
            assert_shape_contact_runtime_diagnostic_fields(row);
            assert_eq!(
                row["shape_contact_runtime_schema_version"],
                "shape_contact_runtime_diagnostic_v1"
            );
            assert!(row["shape_contact_regime_label"].is_string());
            assert_eq!(row["projection_energy_delta_j"], serde_json::Value::Null);
            assert_eq!(row["projection_applied"], false);
        }

        assert_eq!(
            fixture_rows[0]["shape_contact_row_id"],
            "trajectory_000001:shape_contact:7"
        );
        assert_eq!(fixture_rows[0]["contact_regime"], "separated_moving_toward");
        assert_eq!(
            fixture_rows[0]["shape_contact_regime_label"],
            "non_impulsive_separated"
        );
        assert_eq!(fixture_rows[0]["contact_event_id"], serde_json::Value::Null);
        assert_eq!(fixture_rows[0]["impact_index"], serde_json::Value::Null);
        assert_eq!(
            fixture_rows[0]["support_corner_changed"],
            serde_json::Value::Null
        );

        assert_eq!(fixture_rows[1]["contact_regime"], "touching");
        assert_eq!(
            fixture_rows[1]["shape_contact_regime_label"],
            "impulsive_touching"
        );
        assert_eq!(fixture_rows[1]["contact_event_id"], "impact_000003");
        assert_eq!(fixture_rows[1]["impact_index"], 3);

        assert_eq!(fixture_rows[2]["contact_regime"], "penetrating");
        assert_eq!(
            fixture_rows[2]["shape_contact_regime_label"],
            "non_impulsive_penetrating"
        );
        assert_eq!(fixture_rows[2]["normal_impulse_n_s"], 0.0);
        assert_eq!(fixture_rows[2]["tangential_impulse_norm_n_s"], 0.0);
        assert_eq!(
            fixture_rows[2]["shape_contact_row_id"],
            "trajectory_000003:shape_contact:13"
        );
    }

    #[test]
    fn shape_contact_v0_runtime_diagnostic_writer_collects_json_lines_in_order() {
        let mut writer = ShapeContactV0RuntimeDiagnosticWriterV1::new();
        for row in shape_contact_v0_runtime_diagnostic_fixture_rows() {
            writer.write_row(row);
        }

        assert_eq!(writer.rows().len(), 3);
        assert_eq!(
            writer.rows()[0].shape_contact_row_id,
            "trajectory_000001:shape_contact:7"
        );
        assert_eq!(
            writer.rows()[1].shape_contact_row_id,
            "trajectory_000002:shape_contact:11"
        );
        assert_eq!(
            writer.rows()[2].shape_contact_row_id,
            "trajectory_000003:shape_contact:13"
        );

        let json_lines = writer.to_json_lines().unwrap();
        let lines: Vec<_> = json_lines.lines().collect();
        assert_eq!(lines.len(), 3);
        let parsed_rows: Vec<serde_json::Value> = lines
            .iter()
            .map(|line| serde_json::from_str(line).unwrap())
            .collect();

        for row in &parsed_rows {
            assert_shape_contact_runtime_diagnostic_fields(row);
            assert_eq!(
                row["shape_contact_runtime_schema_version"],
                "shape_contact_runtime_diagnostic_v1"
            );
            assert!(row["shape_contact_regime_label"].is_string());
            assert_eq!(row["projection_energy_delta_j"], serde_json::Value::Null);
            assert_eq!(row["projection_applied"], false);
        }
        assert_eq!(
            parsed_rows[0]["shape_contact_row_id"],
            "trajectory_000001:shape_contact:7"
        );
        assert_eq!(
            parsed_rows[0]["shape_contact_regime_label"],
            "non_impulsive_separated"
        );
        assert_eq!(parsed_rows[0]["contact_event_id"], serde_json::Value::Null);
        assert_eq!(parsed_rows[0]["impact_index"], serde_json::Value::Null);
        assert_eq!(
            parsed_rows[0]["support_corner_changed"],
            serde_json::Value::Null
        );
        assert_eq!(
            parsed_rows[1]["shape_contact_regime_label"],
            "impulsive_touching"
        );
        assert_eq!(parsed_rows[1]["contact_event_id"], "impact_000003");
        assert_eq!(
            parsed_rows[2]["shape_contact_regime_label"],
            "non_impulsive_penetrating"
        );
        assert_eq!(parsed_rows[2]["normal_impulse_n_s"], 0.0);
        assert_eq!(parsed_rows[2]["tangential_impulse_norm_n_s"], 0.0);
    }

    #[test]
    fn shape_contact_v0_runtime_diagnostic_sidecar_manifest_records_rows_and_hash() {
        let mut writer = ShapeContactV0RuntimeDiagnosticWriterV1::new();
        for row in shape_contact_v0_runtime_diagnostic_fixture_rows() {
            writer.write_row(row);
        }

        let json_lines = writer.to_json_lines().unwrap();
        let sidecar = writer
            .to_sidecar_manifest(Some("shape_contact_runtime_diagnostics.jsonl".to_string()))
            .unwrap();

        assert_eq!(
            sidecar.diagnostic_sidecar_kind,
            "shape_contact_runtime_diagnostic_jsonl_v1"
        );
        assert_eq!(
            sidecar.diagnostic_sidecar_path.as_deref(),
            Some("shape_contact_runtime_diagnostics.jsonl")
        );
        assert_eq!(
            sidecar.schema_version,
            "shape_contact_runtime_diagnostic_v1"
        );
        assert_eq!(sidecar.row_count, 3);
        let expected_hash = format!(
            "{:016x}",
            crate::stochastic::stable_hash64(json_lines.as_bytes())
        );
        assert_eq!(
            sidecar.json_lines_hash64.as_deref(),
            Some(expected_hash.as_str())
        );
        let expected_sha256 = sha256_hex(json_lines.as_bytes());
        assert_eq!(
            sidecar.json_lines_sha256.as_deref(),
            Some(expected_sha256.as_str())
        );
        assert!(sidecar
            .no_public_output_warning
            .contains("not public validation or benchmark output"));

        let manifest_json = serde_json::to_value(&sidecar).unwrap();
        assert_eq!(manifest_json["row_count"], 3);
        assert_eq!(
            manifest_json["diagnostic_sidecar_kind"],
            "shape_contact_runtime_diagnostic_jsonl_v1"
        );
        assert!(manifest_json["json_lines_hash64"].as_str().is_some());
        assert!(manifest_json["json_lines_sha256"].as_str().is_some());
        assert!(manifest_json["no_public_output_warning"]
            .as_str()
            .unwrap()
            .contains("not public validation or benchmark output"));
    }

    #[test]
    fn shape_contact_v0_runtime_diagnostic_sidecar_writes_json_lines_file() {
        let mut writer = ShapeContactV0RuntimeDiagnosticWriterV1::new();
        for row in shape_contact_v0_runtime_diagnostic_fixture_rows() {
            writer.write_row(row);
        }
        let sidecar_path = temp_shape_contact_path("sidecar", "jsonl");

        let sidecar = writer.write_json_lines_sidecar(&sidecar_path).unwrap();
        let json_lines = fs::read_to_string(&sidecar_path).unwrap();
        fs::remove_file(&sidecar_path).unwrap();

        assert_eq!(sidecar.row_count, 3);
        let sidecar_path_string = sidecar_path.display().to_string();
        assert_eq!(
            sidecar.diagnostic_sidecar_path.as_deref(),
            Some(sidecar_path_string.as_str())
        );
        let expected_sha256 = sha256_hex(json_lines.as_bytes());
        assert_eq!(
            sidecar.json_lines_sha256.as_deref(),
            Some(expected_sha256.as_str())
        );
        let rows = json_lines.lines().collect::<Vec<_>>();
        assert_eq!(rows.len(), 3);
        let first: serde_json::Value = serde_json::from_str(rows[0]).unwrap();
        assert_shape_contact_runtime_diagnostic_fields(&first);
        assert_eq!(
            first["shape_contact_row_id"],
            "trajectory_000001:shape_contact:7"
        );
    }

    #[test]
    fn shape_contact_v0_runtime_smoke_flat_touching_incoming_emits_diagnostic_row() {
        let metadata = test_shape_metadata(2.0, [2.0, 2.0, 2.0]);
        let plane = Plane::horizontal(0.0);
        let result = shape_contact_v0_internal_runtime_smoke_step(
            &metadata,
            &plane,
            ShapeContactV0RuntimeSmokeInput {
                contact_model: crate::dynamics::ContactModel::ShapeContactV0,
                pre_step_state: BodyState::new(
                    Vec3::new(0.0, 0.0, 1.2),
                    Vec3::new(0.0, 0.0, -1.5095),
                ),
                dt_s: 0.1,
                gravity_mps2: 9.81,
                settings: settings(0.5, 0.0, 0.4),
                step_index: 1,
                time_s: 0.1,
            },
        )
        .unwrap();

        assert_eq!(result.writer.rows().len(), 1);
        let row = &result.writer.rows()[0];
        assert_eq!(row.contact_regime, ShapeContactV0ContactRegime::Touching);
        assert_eq!(
            row.shape_contact_regime_label,
            ShapeContactV0RuntimeRegimeLabelV1::ImpulsiveTouching
        );
        assert!(row.impulse_applied);
        assert_close(result.predicted_state.position_m.z, 1.0, 1.0e-12);
        assert_close(row.terrain_contact_point_z_m, 0.0, 1.0e-12);
        assert_close(row.terrain_normal_z, 1.0, 1.0e-12);
        assert!(row.normal_impulse_n_s > 0.0);
    }

    #[test]
    fn shape_contact_v0_runtime_smoke_separated_state_writes_non_impulsive_row() {
        let metadata = test_shape_metadata(2.0, [2.0, 2.0, 2.0]);
        let plane = Plane::horizontal(0.0);
        let result = shape_contact_v0_internal_runtime_smoke_step(
            &metadata,
            &plane,
            ShapeContactV0RuntimeSmokeInput {
                contact_model: crate::dynamics::ContactModel::ShapeContactV0,
                pre_step_state: BodyState::new(Vec3::new(0.0, 0.0, 2.0), Vec3::new(0.0, 0.0, -1.0)),
                dt_s: 0.1,
                gravity_mps2: 9.81,
                settings: settings(0.5, 0.0, 0.4),
                step_index: 1,
                time_s: 0.1,
            },
        )
        .unwrap();

        let row = &result.writer.rows()[0];
        assert_eq!(
            row.contact_regime,
            ShapeContactV0ContactRegime::SeparatedMovingToward
        );
        assert_eq!(
            row.shape_contact_regime_label,
            ShapeContactV0RuntimeRegimeLabelV1::NonImpulsiveSeparated
        );
        assert!(!row.impulse_applied);
        assert!(row.support_signed_gap_m > 0.0);
        assert_close(row.normal_impulse_n_s, 0.0, 1.0e-12);
        assert_close(row.tangential_impulse_norm_n_s, 0.0, 1.0e-12);
    }

    #[test]
    fn shape_contact_v0_runtime_smoke_penetrating_moving_away_maps_non_impulsive() {
        let metadata = test_shape_metadata(2.0, [2.0, 2.0, 2.0]);
        let plane = Plane::horizontal(0.0);
        let result = shape_contact_v0_internal_runtime_smoke_step(
            &metadata,
            &plane,
            ShapeContactV0RuntimeSmokeInput {
                contact_model: crate::dynamics::ContactModel::ShapeContactV0,
                pre_step_state: BodyState::new(
                    Vec3::new(0.0, 0.0, 0.8),
                    Vec3::new(0.0, 0.0, 1.4905),
                ),
                dt_s: 0.1,
                gravity_mps2: 9.81,
                settings: settings(0.5, 0.0, 0.4),
                step_index: 1,
                time_s: 0.1,
            },
        )
        .unwrap();

        let row = &result.writer.rows()[0];
        assert_eq!(row.contact_regime, ShapeContactV0ContactRegime::Penetrating);
        assert_eq!(
            row.shape_contact_regime_label,
            ShapeContactV0RuntimeRegimeLabelV1::NonImpulsivePenetrating
        );
        assert!(!row.impulse_applied);
        assert!(row.support_signed_gap_m < 0.0);
        assert!(row.contact_point_normal_velocity_pre_mps > 0.0);
        assert_close(row.normal_impulse_n_s, 0.0, 1.0e-12);
        assert_close(row.tangential_impulse_norm_n_s, 0.0, 1.0e-12);
    }

    #[test]
    fn shape_contact_v0_runtime_smoke_passes_inclined_normal_to_diagnostics() {
        let metadata = test_shape_metadata(2.0, [2.0, 2.0, 2.0]);
        let plane = Plane {
            z0_m: 0.0,
            slope_x: 0.2,
            slope_y: -0.1,
        };
        let result = shape_contact_v0_internal_runtime_smoke_step(
            &metadata,
            &plane,
            ShapeContactV0RuntimeSmokeInput {
                contact_model: crate::dynamics::ContactModel::ShapeContactV0,
                pre_step_state: BodyState::new(Vec3::new(0.0, 0.0, 2.0), Vec3::new(0.0, 0.0, -1.0)),
                dt_s: 0.1,
                gravity_mps2: 9.81,
                settings: settings(0.5, 0.0, 0.4),
                step_index: 1,
                time_s: 0.1,
            },
        )
        .unwrap();

        let expected_normal = plane.normal(
            result.predicted_state.position_m.x,
            result.predicted_state.position_m.y,
        );
        let row = &result.writer.rows()[0];
        assert_close(row.terrain_normal_x, expected_normal.x, 1.0e-12);
        assert_close(row.terrain_normal_y, expected_normal.y, 1.0e-12);
        assert_close(row.terrain_normal_z, expected_normal.z, 1.0e-12);
        assert_close(result.terrain_normal_world[0], expected_normal.x, 1.0e-12);
        assert_close(result.terrain_normal_world[1], expected_normal.y, 1.0e-12);
        assert_close(result.terrain_normal_world[2], expected_normal.z, 1.0e-12);
    }

    #[test]
    fn shape_contact_v0_runtime_smoke_json_fields_match_frozen_contract() {
        let metadata = test_shape_metadata(2.0, [2.0, 2.0, 2.0]);
        let plane = Plane::horizontal(0.0);
        let result = shape_contact_v0_internal_runtime_smoke_step(
            &metadata,
            &plane,
            ShapeContactV0RuntimeSmokeInput {
                contact_model: crate::dynamics::ContactModel::ShapeContactV0,
                pre_step_state: BodyState::new(
                    Vec3::new(0.0, 0.0, 1.2),
                    Vec3::new(0.0, 0.0, -1.5095),
                ),
                dt_s: 0.1,
                gravity_mps2: 9.81,
                settings: settings(0.5, 0.0, 0.4),
                step_index: 1,
                time_s: 0.1,
            },
        )
        .unwrap();

        let json_lines = result.writer.to_json_lines().unwrap();
        let lines: Vec<_> = json_lines.lines().collect();
        assert_eq!(lines.len(), 1);
        let row: serde_json::Value = serde_json::from_str(lines[0]).unwrap();
        assert_shape_contact_runtime_diagnostic_fields(&row);
        assert_eq!(
            row["shape_contact_runtime_schema_version"],
            "shape_contact_runtime_diagnostic_v1"
        );
        assert_eq!(
            row["shape_contact_row_id"],
            "runtime_smoke_trajectory_000001:shape_contact:1"
        );
        assert!(row["shape_contact_regime_label"].is_string());
        assert_eq!(row["projection_energy_delta_j"], serde_json::Value::Null);
        assert_eq!(row["projection_applied"], false);
    }

    #[test]
    fn shape_contact_v0_runtime_smoke_manifest_contains_required_shape_fields() {
        let metadata = test_shape_metadata(2.0, [2.0, 2.0, 2.0]);
        let plane = Plane::horizontal(0.0);
        let result = shape_contact_v0_internal_runtime_smoke_step(
            &metadata,
            &plane,
            ShapeContactV0RuntimeSmokeInput {
                contact_model: crate::dynamics::ContactModel::ShapeContactV0,
                pre_step_state: BodyState::new(
                    Vec3::new(0.0, 0.0, 1.2),
                    Vec3::new(0.0, 0.0, -1.5095),
                ),
                dt_s: 0.1,
                gravity_mps2: 9.81,
                settings: settings(0.5, 0.0, 0.4),
                step_index: 1,
                time_s: 0.1,
            },
        )
        .unwrap();
        let manifest = serde_json::to_value(&result.manifest).unwrap();
        let object = manifest.as_object().unwrap();
        for key in [
            "active_contact_model",
            "active_shape_type",
            "shape_metadata_path",
            "shape_metadata_sha256",
            "shape_id",
            "mass_kg",
            "principal_dimensions_m",
            "orientation_initialization_mode",
            "orientation_representation",
            "inertia_model",
            "principal_moments_kg_m2",
            "support_selection_policy",
            "support_corner_tie_break",
            "contact_gap_tolerance_m",
            "multi_contact",
            "new_tuned_parameters",
            "defaults_changed",
            "projection_correction_enabled",
            "persistent_contact_enabled",
            "orientation_evolution_enabled",
            "runtime_diagnostic_schema_version",
            "experimental_status",
            "warnings",
            "limitations",
        ] {
            assert!(object.contains_key(key), "manifest missing {key}");
        }
        assert_eq!(manifest["active_contact_model"], SHAPE_CONTACT_V0_MODEL);
        assert_eq!(manifest["active_shape_type"], SHAPE_CONTACT_V0_ACTIVE_SHAPE);
        assert_eq!(
            manifest["runtime_diagnostic_schema_version"],
            "shape_contact_runtime_diagnostic_v1"
        );
        assert_eq!(
            manifest["experimental_status"],
            "internal_runtime_smoke_only"
        );
        assert_eq!(manifest["shape_metadata_path"], serde_json::Value::Null);
        assert_eq!(manifest["shape_metadata_sha256"], serde_json::Value::Null);
        assert_eq!(manifest["multi_contact"], false);
        assert_eq!(manifest["new_tuned_parameters"], false);
        assert_eq!(manifest["defaults_changed"], false);
        assert_eq!(manifest["projection_correction_enabled"], false);
        assert_eq!(manifest["persistent_contact_enabled"], false);
        assert_eq!(manifest["orientation_evolution_enabled"], false);
        let warnings = manifest["warnings"].as_array().unwrap();
        let warning_text = warnings
            .iter()
            .map(|value| value.as_str().unwrap())
            .collect::<Vec<_>>()
            .join(" ");
        for required in [
            "opt-in",
            "uncalibrated",
            "non-operational",
            "not RAMMS-equivalent",
            "not benchmark-validated",
        ] {
            assert!(
                warning_text.contains(required),
                "manifest warnings missing {required}: {warning_text}"
            );
        }
        let limitations = manifest["limitations"].as_array().unwrap();
        let limitation_text = limitations
            .iter()
            .map(|value| value.as_str().unwrap())
            .collect::<Vec<_>>()
            .join(" ");
        for required in [
            "missing projection correction",
            "missing persistent contact",
            "missing orientation evolution",
            "missing multi-contact",
            "missing public benchmark evidence",
        ] {
            assert!(
                limitation_text.contains(required),
                "manifest limitations missing {required}: {limitation_text}"
            );
        }
    }

    #[test]
    fn shape_contact_v0_integrator_smoke_file_backed_metadata_records_provenance() {
        let metadata = test_shape_metadata(2.0, [2.0, 2.0, 2.0]);
        let metadata_path = write_test_shape_metadata_file(&metadata, "runtime_smoke");
        let plane = Plane::horizontal(0.0);
        let result = shape_contact_v0_internal_integrator_smoke_step_from_metadata_file(
            &metadata_path,
            &plane,
            ShapeContactV0RuntimeSmokeInput {
                contact_model: crate::dynamics::ContactModel::ShapeContactV0,
                pre_step_state: BodyState::new(
                    Vec3::new(0.0, 0.0, 1.2),
                    Vec3::new(0.0, 0.0, -1.5095),
                ),
                dt_s: 0.1,
                gravity_mps2: 9.81,
                settings: settings(0.5, 0.0, 0.4),
                step_index: 1,
                time_s: 0.1,
            },
        )
        .unwrap();
        let metadata_path_string = metadata_path.display().to_string();
        fs::remove_file(&metadata_path).unwrap();

        assert_eq!(result.writer.rows().len(), 1);
        let row = &result.writer.rows()[0];
        assert!(row.impulse_applied);
        assert_eq!(
            row.shape_contact_regime_label,
            ShapeContactV0RuntimeRegimeLabelV1::ImpulsiveTouching
        );
        assert_eq!(
            result.manifest.shape_metadata_path.as_deref(),
            Some(metadata_path_string.as_str())
        );
        let sha256 = result.manifest.shape_metadata_sha256.as_deref().unwrap();
        assert_eq!(sha256.len(), 64);
        assert!(sha256
            .chars()
            .all(|character| character.is_ascii_hexdigit()));
    }

    #[test]
    fn shape_contact_v0_internal_integrator_smoke_fixture_writes_sidecar() {
        let results = shape_contact_v0_internal_integrator_smoke_fixture();
        assert_eq!(results.len(), 4);

        let mut writer = ShapeContactV0RuntimeDiagnosticWriterV1::new();
        for result in &results {
            assert_eq!(result.writer.rows().len(), 1);
            writer.write_row(result.writer.rows()[0].clone());
            assert!(result.manifest.shape_metadata_path.is_some());
            let sha256 = result.manifest.shape_metadata_sha256.as_deref().unwrap();
            assert_eq!(sha256.len(), 64);
        }

        let sidecar_path = temp_shape_contact_path("internal_integrator_smoke_sidecar", "jsonl");
        let sidecar = writer.write_json_lines_sidecar(&sidecar_path).unwrap();
        let json_lines = fs::read_to_string(&sidecar_path).unwrap();
        fs::remove_file(&sidecar_path).unwrap();
        assert_eq!(sidecar.row_count, 4);
        let expected_sha256 = sha256_hex(json_lines.as_bytes());
        assert_eq!(
            sidecar.json_lines_sha256.as_deref(),
            Some(expected_sha256.as_str())
        );
        assert!(sidecar
            .no_public_output_warning
            .contains("not public validation or benchmark output"));

        let rows = json_lines
            .lines()
            .map(|line| serde_json::from_str::<serde_json::Value>(line).unwrap())
            .collect::<Vec<_>>();
        assert_eq!(rows.len(), 4);
        assert_eq!(rows[0]["shape_contact_regime_label"], "impulsive_touching");
        assert_eq!(
            rows[1]["shape_contact_regime_label"],
            "non_impulsive_separated"
        );
        assert_eq!(
            rows[2]["shape_contact_regime_label"],
            "non_impulsive_penetrating"
        );
        assert!(rows[3]["terrain_normal_x"].as_f64().unwrap().abs() > 0.0);
    }

    #[test]
    fn shape_contact_v0_runtime_smoke_manifest_references_diagnostic_sidecar() {
        let metadata = test_shape_metadata(2.0, [2.0, 2.0, 2.0]);
        let plane = Plane::horizontal(0.0);
        let result = shape_contact_v0_internal_runtime_smoke_step(
            &metadata,
            &plane,
            ShapeContactV0RuntimeSmokeInput {
                contact_model: crate::dynamics::ContactModel::ShapeContactV0,
                pre_step_state: BodyState::new(
                    Vec3::new(0.0, 0.0, 1.2),
                    Vec3::new(0.0, 0.0, -1.5095),
                ),
                dt_s: 0.1,
                gravity_mps2: 9.81,
                settings: settings(0.5, 0.0, 0.4),
                step_index: 1,
                time_s: 0.1,
            },
        )
        .unwrap();

        let package = shape_contact_v0_runtime_smoke_manifest_package(&result).unwrap();
        assert_eq!(
            package.shape_contact_v0.active_contact_model,
            SHAPE_CONTACT_V0_MODEL
        );
        assert_eq!(
            package.diagnostic_sidecar.diagnostic_sidecar_kind,
            "shape_contact_runtime_diagnostic_jsonl_v1"
        );
        assert_eq!(package.diagnostic_sidecar.diagnostic_sidecar_path, None);
        assert_eq!(
            package.diagnostic_sidecar.schema_version,
            "shape_contact_runtime_diagnostic_v1"
        );
        assert_eq!(package.diagnostic_sidecar.row_count, 1);
        assert!(package
            .diagnostic_sidecar
            .json_lines_hash64
            .as_deref()
            .is_some());

        let package_json = serde_json::to_value(&package).unwrap();
        assert_eq!(
            package_json["shape_contact_v0"]["active_contact_model"],
            SHAPE_CONTACT_V0_MODEL
        );
        assert_eq!(
            package_json["diagnostic_sidecar"]["diagnostic_sidecar_kind"],
            "shape_contact_runtime_diagnostic_jsonl_v1"
        );
        assert_eq!(
            package_json["diagnostic_sidecar"]["diagnostic_sidecar_path"],
            serde_json::Value::Null
        );
        assert_eq!(package_json["diagnostic_sidecar"]["row_count"], 1);
    }

    #[test]
    fn shape_contact_v0_runtime_smoke_requires_shape_contact_model() {
        let metadata = test_shape_metadata(2.0, [2.0, 2.0, 2.0]);
        let plane = Plane::horizontal(0.0);
        let error = shape_contact_v0_internal_runtime_smoke_step(
            &metadata,
            &plane,
            ShapeContactV0RuntimeSmokeInput {
                contact_model: crate::dynamics::ContactModel::TranslationalV0,
                pre_step_state: BodyState::new(
                    Vec3::new(0.0, 0.0, 1.2),
                    Vec3::new(0.0, 0.0, -1.5095),
                ),
                dt_s: 0.1,
                gravity_mps2: 9.81,
                settings: settings(0.5, 0.0, 0.4),
                step_index: 1,
                time_s: 0.1,
            },
        )
        .unwrap_err();

        assert!(error
            .to_string()
            .contains("requires contact_model shape_contact_v0"));
    }

    #[test]
    fn shape_contact_v0_runtime_regime_label_v1_values_are_fixed() {
        assert_eq!(
            shape_contact_v0_regime_label_v1(
                ShapeContactV0ContactRegime::SeparatedMovingAway,
                false
            ),
            ShapeContactV0RuntimeRegimeLabelV1::NonImpulsiveSeparated
        );
        assert_eq!(
            shape_contact_v0_regime_label_v1(
                ShapeContactV0ContactRegime::SeparatedMovingToward,
                false
            ),
            ShapeContactV0RuntimeRegimeLabelV1::NonImpulsiveSeparated
        );
        assert_eq!(
            shape_contact_v0_regime_label_v1(ShapeContactV0ContactRegime::Touching, false),
            ShapeContactV0RuntimeRegimeLabelV1::NonImpulsiveTouching
        );
        assert_eq!(
            shape_contact_v0_regime_label_v1(ShapeContactV0ContactRegime::Touching, true),
            ShapeContactV0RuntimeRegimeLabelV1::ImpulsiveTouching
        );
        assert_eq!(
            shape_contact_v0_regime_label_v1(ShapeContactV0ContactRegime::Penetrating, true),
            ShapeContactV0RuntimeRegimeLabelV1::ImpulsivePenetrating
        );
        assert_eq!(
            shape_contact_v0_regime_label_v1(ShapeContactV0ContactRegime::Penetrating, false),
            ShapeContactV0RuntimeRegimeLabelV1::NonImpulsivePenetrating
        );
    }

    #[test]
    fn shape_contact_v0_synthetic_flat_plane_separated_has_no_impulse() {
        let scaffold = test_scaffold(2.0, [2.0, 2.0, 2.0]);
        let plane = Plane::horizontal(0.0);
        let pre_state = BodyState::new(Vec3::new(0.0, 0.0, 1.5), Vec3::new(0.0, 0.0, 0.25));
        let result = shape_contact_v0_synthetic_terrain_step(
            &scaffold,
            &plane,
            ShapeContactV0SyntheticTerrainInput {
                pre_state,
                terrain_query_x_m: 1.0,
                terrain_query_y_m: 1.0,
                settings: settings(0.5, 1.0, 0.0),
            },
        )
        .unwrap();

        assert_eq!(
            result.contact_regime,
            ShapeContactV0ContactRegime::SeparatedMovingAway
        );
        assert!(!result.impulse_result.diagnostic.impacted);
        assert_close(result.support_signed_gap_m, 0.5, 1.0e-12);
        assert_eq!(result.impulse_result.post_state, pre_state);
    }

    #[test]
    fn shape_contact_v0_synthetic_flat_plane_touching_incoming_impacts() {
        let scaffold = test_scaffold(2.0, [2.0, 2.0, 2.0]);
        let plane = Plane::horizontal(0.0);
        let result = shape_contact_v0_synthetic_terrain_step(
            &scaffold,
            &plane,
            ShapeContactV0SyntheticTerrainInput {
                pre_state: BodyState::new(Vec3::new(0.0, 0.0, 1.0), Vec3::new(0.0, 0.0, -2.0)),
                terrain_query_x_m: 1.0,
                terrain_query_y_m: 1.0,
                settings: settings(0.5, 1.0, 0.0),
            },
        )
        .unwrap();

        assert_eq!(result.contact_regime, ShapeContactV0ContactRegime::Touching);
        assert!(result.impulse_result.diagnostic.impacted);
        assert_close(result.support_signed_gap_m, 0.0, 1.0e-12);
        assert!(
            result
                .impulse_result
                .diagnostic
                .post_contact_normal_velocity_mps
                > 0.0
        );
    }

    #[test]
    fn shape_contact_v0_synthetic_flat_plane_penetrating_incoming_impacts() {
        let scaffold = test_scaffold(2.0, [2.0, 2.0, 2.0]);
        let plane = Plane::horizontal(0.25);
        let result = shape_contact_v0_synthetic_terrain_step(
            &scaffold,
            &plane,
            ShapeContactV0SyntheticTerrainInput {
                pre_state: BodyState::new(Vec3::new(0.0, 0.0, 1.0), Vec3::new(0.0, 0.0, -2.0)),
                terrain_query_x_m: 1.0,
                terrain_query_y_m: 1.0,
                settings: settings(0.5, 1.0, 0.0),
            },
        )
        .unwrap();

        assert_eq!(
            result.contact_regime,
            ShapeContactV0ContactRegime::Penetrating
        );
        assert!(result.impulse_result.diagnostic.impacted);
        assert_close(result.support_signed_gap_m, -0.25, 1.0e-12);
    }

    #[test]
    fn shape_contact_v0_synthetic_inclined_plane_uses_terrain_normal() {
        let scaffold = test_scaffold(2.0, [2.0, 2.0, 2.0]);
        let plane = Plane {
            z0_m: 0.0,
            slope_x: 0.0,
            slope_y: 1.0,
        };
        let normal = plane.normal(0.0, -1.0);
        let result = shape_contact_v0_synthetic_terrain_step(
            &scaffold,
            &plane,
            ShapeContactV0SyntheticTerrainInput {
                pre_state: BodyState::new(Vec3::new(0.0, 0.0, 2.0), -2.0 * normal),
                terrain_query_x_m: 1.0,
                terrain_query_y_m: 1.0,
                settings: settings(0.25, 1.0, 0.0),
            },
        )
        .unwrap();

        assert_eq!(result.contact_regime, ShapeContactV0ContactRegime::Touching);
        assert_eq!(
            result.impulse_result.diagnostic.support_corner_signs,
            [1, 1, -1]
        );
        assert_close(result.support_signed_gap_m, 0.0, 1.0e-12);
    }

    #[test]
    fn shape_contact_v0_synthetic_separated_moving_toward_has_no_impulse() {
        let scaffold = test_scaffold(2.0, [2.0, 2.0, 2.0]);
        let plane = Plane::horizontal(0.0);
        let pre_state = BodyState::new(Vec3::new(0.0, 0.0, 1.5), Vec3::new(0.0, 0.0, -2.0));
        let result = shape_contact_v0_synthetic_terrain_step(
            &scaffold,
            &plane,
            ShapeContactV0SyntheticTerrainInput {
                pre_state,
                terrain_query_x_m: 1.0,
                terrain_query_y_m: 1.0,
                settings: settings(0.5, 1.0, 0.0),
            },
        )
        .unwrap();

        assert_eq!(
            result.contact_regime,
            ShapeContactV0ContactRegime::SeparatedMovingToward
        );
        assert!(!result.impulse_result.diagnostic.impacted);
        assert_close(
            result.impulse_result.diagnostic.normal_impulse_n_s,
            0.0,
            1.0e-12,
        );
        assert_eq!(result.impulse_result.post_state, pre_state);
    }

    #[test]
    fn shape_contact_v0_synthetic_dissipative_contact_does_not_create_energy() {
        let scaffold = test_scaffold(3.0, [2.0, 3.0, 4.0]);
        let plane = Plane::horizontal(1.0);
        let mut pre_state = BodyState::new(Vec3::new(0.0, 0.0, 3.0), Vec3::new(3.0, -1.0, -2.0));
        pre_state.angular_velocity_radps = Vec3::new(0.2, -0.1, 0.3);
        let result = shape_contact_v0_synthetic_terrain_step(
            &scaffold,
            &plane,
            ShapeContactV0SyntheticTerrainInput {
                pre_state,
                terrain_query_x_m: 1.0,
                terrain_query_y_m: 1.5,
                settings: settings(0.4, 0.0, 0.8),
            },
        )
        .unwrap();

        assert!(result.impulse_result.diagnostic.impacted);
        assert!(
            result
                .impulse_result
                .diagnostic
                .energy
                .contact_energy_delta_j
                <= 1.0e-10
        );
    }

    #[test]
    fn shape_contact_v0_synthetic_flat_tie_break_remains_reproducible() {
        let scaffold = test_scaffold(2.0, [2.0, 2.0, 2.0]);
        let plane = Plane::horizontal(0.0);
        let input = ShapeContactV0SyntheticTerrainInput {
            pre_state: BodyState::new(Vec3::new(0.0, 0.0, 1.0), Vec3::new(0.0, 0.0, -1.0)),
            terrain_query_x_m: 1.0,
            terrain_query_y_m: 1.0,
            settings: settings(0.0, 1.0, 0.0),
        };
        let first = shape_contact_v0_synthetic_terrain_step(&scaffold, &plane, input).unwrap();
        let second = shape_contact_v0_synthetic_terrain_step(&scaffold, &plane, input).unwrap();

        assert_eq!(
            first.impulse_result.diagnostic.support_corner_signs,
            [1, 1, -1]
        );
        assert_eq!(
            first.impulse_result.diagnostic.support_corner_signs,
            second.impulse_result.diagnostic.support_corner_signs
        );
    }

    #[test]
    fn shape_contact_v0_mini_fixed_step_airborne_step_has_no_impulse() {
        let scaffold = test_scaffold(2.0, [2.0, 2.0, 2.0]);
        let plane = Plane::horizontal(0.0);
        let pre_step_state = BodyState::new(Vec3::new(0.0, 0.0, 3.0), Vec3::new(0.0, 0.0, 0.0));
        let result = shape_contact_v0_mini_fixed_step(
            &scaffold,
            &plane,
            ShapeContactV0MiniFixedStepInput {
                pre_step_state,
                dt_s: 0.1,
                gravity_mps2: 10.0,
                settings: settings_with_gravity(0.5, 1.0, 0.0, 10.0),
            },
        )
        .unwrap();

        assert_eq!(result.pre_step_state, pre_step_state);
        assert_close(result.predicted_state.position_m.z, 2.95, 1.0e-12);
        assert_close(result.predicted_state.velocity_mps.z, -1.0, 1.0e-12);
        assert_eq!(
            result.contact.contact_regime,
            ShapeContactV0ContactRegime::SeparatedMovingToward
        );
        assert!(!result.contact.impulse_result.diagnostic.impacted);
        assert_eq!(
            result.contact.impulse_result.post_state,
            result.predicted_state
        );
        assert_close(result.contact.support_signed_gap_m, 1.95, 1.0e-12);
    }

    #[test]
    fn shape_contact_v0_mini_fixed_step_reaching_touching_contact_impacts() {
        let scaffold = test_scaffold(2.0, [2.0, 2.0, 2.0]);
        let plane = Plane::horizontal(0.0);
        let result = shape_contact_v0_mini_fixed_step(
            &scaffold,
            &plane,
            ShapeContactV0MiniFixedStepInput {
                pre_step_state: BodyState::new(Vec3::new(0.0, 0.0, 1.05), Vec3::new(0.0, 0.0, 0.0)),
                dt_s: 0.1,
                gravity_mps2: 10.0,
                settings: settings_with_gravity(0.5, 1.0, 0.0, 10.0),
            },
        )
        .unwrap();

        assert_close(result.predicted_state.position_m.z, 1.0, 1.0e-12);
        assert_eq!(result.terrain_contact_point_m, [0.0, 0.0, 0.0]);
        assert_eq!(
            result.contact.contact_regime,
            ShapeContactV0ContactRegime::Touching
        );
        assert!(result.contact.impulse_result.diagnostic.impacted);
        assert_close(result.contact.support_signed_gap_m, 0.0, 1.0e-12);
        assert!(
            result
                .contact
                .impulse_result
                .diagnostic
                .post_contact_normal_velocity_mps
                > 0.0
        );
    }

    #[test]
    fn shape_contact_v0_mini_fixed_step_reaching_penetrating_contact_impacts() {
        let scaffold = test_scaffold(2.0, [2.0, 2.0, 2.0]);
        let plane = Plane::horizontal(0.0);
        let result = shape_contact_v0_mini_fixed_step(
            &scaffold,
            &plane,
            ShapeContactV0MiniFixedStepInput {
                pre_step_state: BodyState::new(Vec3::new(0.0, 0.0, 1.0), Vec3::new(0.0, 0.0, 0.0)),
                dt_s: 0.1,
                gravity_mps2: 10.0,
                settings: settings_with_gravity(0.5, 1.0, 0.0, 10.0),
            },
        )
        .unwrap();

        assert_close(result.predicted_state.position_m.z, 0.95, 1.0e-12);
        assert_eq!(
            result.contact.contact_regime,
            ShapeContactV0ContactRegime::Penetrating
        );
        assert!(result.contact.impulse_result.diagnostic.impacted);
        assert_close(result.contact.support_signed_gap_m, -0.05, 1.0e-12);
    }

    #[test]
    fn shape_contact_v0_mini_fixed_step_separated_moving_toward_waits_for_contact() {
        let scaffold = test_scaffold(2.0, [2.0, 2.0, 2.0]);
        let plane = Plane::horizontal(0.0);
        let result = shape_contact_v0_mini_fixed_step(
            &scaffold,
            &plane,
            ShapeContactV0MiniFixedStepInput {
                pre_step_state: BodyState::new(Vec3::new(0.0, 0.0, 1.55), Vec3::new(0.0, 0.0, 0.0)),
                dt_s: 0.1,
                gravity_mps2: 10.0,
                settings: settings_with_gravity(0.5, 1.0, 0.0, 10.0),
            },
        )
        .unwrap();

        assert_eq!(
            result.contact.contact_regime,
            ShapeContactV0ContactRegime::SeparatedMovingToward
        );
        assert_close(result.contact.support_signed_gap_m, 0.5, 1.0e-12);
        assert!(!result.contact.impulse_result.diagnostic.impacted);
        assert_close(
            result.contact.impulse_result.diagnostic.normal_impulse_n_s,
            0.0,
            1.0e-12,
        );
        assert_eq!(
            result.contact.impulse_result.post_state,
            result.predicted_state
        );
    }

    #[test]
    fn shape_contact_v0_mini_fixed_step_captures_terrain_normal() {
        let scaffold = test_scaffold(2.0, [2.0, 2.0, 2.0]);
        let plane = Plane {
            z0_m: 0.0,
            slope_x: 0.0,
            slope_y: 1.0,
        };
        let result = shape_contact_v0_mini_fixed_step(
            &scaffold,
            &plane,
            ShapeContactV0MiniFixedStepInput {
                pre_step_state: BodyState::new(Vec3::new(0.0, 2.0, 5.0), Vec3::new(0.0, 0.0, 0.0)),
                dt_s: 0.1,
                gravity_mps2: 10.0,
                settings: settings_with_gravity(0.5, 1.0, 0.0, 10.0),
            },
        )
        .unwrap();
        let expected_normal = plane.normal(
            result.predicted_state.position_m.x,
            result.predicted_state.position_m.y,
        );

        assert_close(result.terrain_contact_point_m[2], 2.0, 1.0e-12);
        assert_close(result.terrain_normal_world[0], expected_normal.x, 1.0e-12);
        assert_close(result.terrain_normal_world[1], expected_normal.y, 1.0e-12);
        assert_close(result.terrain_normal_world[2], expected_normal.z, 1.0e-12);
        assert_eq!(
            result
                .contact
                .impulse_result
                .diagnostic
                .support_corner_signs,
            [1, 1, -1]
        );
    }

    #[test]
    fn shape_contact_v0_mini_fixed_step_dissipative_contact_does_not_create_energy() {
        let scaffold = test_scaffold(3.0, [2.0, 3.0, 4.0]);
        let plane = Plane::horizontal(1.0);
        let mut pre_step_state =
            BodyState::new(Vec3::new(0.0, 0.0, 3.05), Vec3::new(3.0, -1.0, 0.0));
        pre_step_state.angular_velocity_radps = Vec3::new(0.2, -0.1, 0.3);
        let result = shape_contact_v0_mini_fixed_step(
            &scaffold,
            &plane,
            ShapeContactV0MiniFixedStepInput {
                pre_step_state,
                dt_s: 0.1,
                gravity_mps2: 10.0,
                settings: settings_with_gravity(0.4, 0.0, 0.8, 10.0),
            },
        )
        .unwrap();

        assert_eq!(
            result.contact.contact_regime,
            ShapeContactV0ContactRegime::Touching
        );
        assert!(result.contact.impulse_result.diagnostic.impacted);
        assert!(
            result
                .contact
                .impulse_result
                .diagnostic
                .energy
                .contact_energy_delta_j
                <= 1.0e-10
        );
    }

    #[test]
    fn shape_contact_v0_mini_fixed_step_rejects_gravity_mismatch() {
        let scaffold = test_scaffold(2.0, [2.0, 2.0, 2.0]);
        let plane = Plane::horizontal(0.0);
        let error = shape_contact_v0_mini_fixed_step(
            &scaffold,
            &plane,
            ShapeContactV0MiniFixedStepInput {
                pre_step_state: BodyState::new(Vec3::new(0.0, 0.0, 3.0), Vec3::new(0.0, 0.0, 0.0)),
                dt_s: 0.1,
                gravity_mps2: 10.0,
                settings: settings(0.5, 1.0, 0.0),
            },
        )
        .unwrap_err()
        .to_string();

        assert!(error.contains("settings.gravity_mps2"));
        assert!(error.contains("mini_fixed_step.gravity_mps2"));
    }
}
