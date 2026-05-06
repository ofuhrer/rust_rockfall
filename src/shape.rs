//! Passive block-shape metadata and mass-property diagnostics.
//!
//! Shape metadata is currently descriptive only. Contact and dynamics continue
//! to use the active spherical block unless a future opt-in contact model
//! explicitly says otherwise.

use crate::{geometry::SphereBlock, state::BodyState, Vec3};
use serde::{Deserialize, Serialize};
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

    pub fn apply_support_impulse(
        &self,
        pre_state: BodyState,
        terrain_normal_world: Vec3,
        settings: ShapeContactV0ImpulseSettings,
    ) -> Result<ShapeContactV0ImpulseResult, ShapeMetadataError> {
        let prepared = self.impulse_input(pre_state, terrain_normal_world, settings)?;
        shape_contact_v0_apply_support_impulse(&prepared.support, prepared.input)
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
/// Shape-contact paths must prefer
/// [`ShapeContactV0Scaffold::apply_support_impulse`] so support geometry, mass,
/// and inertia all come from the same validated scaffold. This helper remains
/// internal to avoid public callers mixing those quantities by hand.
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
#[derive(Debug, Clone, Copy)]
struct ShapeContactV0DryRunInput {
    pre_state: BodyState,
    terrain_contact_point_m: Vec3,
    terrain_normal_world: Vec3,
    settings: ShapeContactV0ImpulseSettings,
}

#[cfg(test)]
#[derive(Debug, Clone)]
struct ShapeContactV0DryRunResult {
    terrain_contact_point_m: [f64; 3],
    support_signed_gap_m: f64,
    contact_regime: ShapeContactV0DryRunContactRegime,
    impulse_result: ShapeContactV0ImpulseResult,
}

#[cfg(test)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum ShapeContactV0DryRunContactRegime {
    SeparatedMovingAway,
    SeparatedMovingToward,
    Touching,
    Penetrating,
}

#[cfg(test)]
const SHAPE_CONTACT_V0_DRY_RUN_GAP_TOLERANCE_M: f64 = 1.0e-9;

#[cfg(test)]
fn shape_contact_v0_contact_dry_run(
    scaffold: &ShapeContactV0Scaffold,
    input: ShapeContactV0DryRunInput,
) -> Result<ShapeContactV0DryRunResult, ShapeMetadataError> {
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
    let contact_regime = if support_signed_gap_m > SHAPE_CONTACT_V0_DRY_RUN_GAP_TOLERANCE_M {
        if pre_normal_velocity < 0.0 {
            ShapeContactV0DryRunContactRegime::SeparatedMovingToward
        } else {
            ShapeContactV0DryRunContactRegime::SeparatedMovingAway
        }
    } else if support_signed_gap_m < -SHAPE_CONTACT_V0_DRY_RUN_GAP_TOLERANCE_M {
        ShapeContactV0DryRunContactRegime::Penetrating
    } else {
        ShapeContactV0DryRunContactRegime::Touching
    };
    let impulse_result = match contact_regime {
        ShapeContactV0DryRunContactRegime::SeparatedMovingAway
        | ShapeContactV0DryRunContactRegime::SeparatedMovingToward => {
            shape_contact_v0_no_impulse_result(&prepared.support, prepared.input)?
        }
        ShapeContactV0DryRunContactRegime::Touching
        | ShapeContactV0DryRunContactRegime::Penetrating => {
            shape_contact_v0_apply_support_impulse(&prepared.support, prepared.input)?
        }
    };
    Ok(ShapeContactV0DryRunResult {
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
fn shape_contact_v0_no_impulse_result(
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
}
