use crate::{geometry::SphereBlock, state::BodyState, terrain::Terrain, Vec3};
use serde::{Deserialize, Serialize};
use std::f64::consts::PI;

const ROLLING_RESIDUAL_TOLERANCE_MPS: f64 = 1.0e-6;

#[derive(Debug, Clone, Copy, PartialEq)]
pub struct ContactResponse {
    pub impacted: bool,
    pub sliding: bool,
    pub rolling: bool,
    pub contact_tangent_speed_mps: f64,
    pub rolling_residual_mps: f64,
}

#[derive(Debug, Default, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum ContactModel {
    #[default]
    TranslationalV0,
    SphereRotationalV1,
}

#[derive(Debug, Default, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum SoilInteractionModel {
    #[default]
    None,
    ScarringContactV1,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq)]
pub struct ScarringSettings {
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
}

impl Default for ScarringSettings {
    fn default() -> Self {
        Self {
            soil_interaction_model: SoilInteractionModel::None,
            soil_strength_pa: 0.0,
            scarring_drag_coefficient: 0.0,
            scarring_layer_density_kgpm3: 0.0,
            scarring_max_depth_m: None,
        }
    }
}

impl ScarringSettings {
    pub fn validate(&self) -> Result<(), &'static str> {
        if !self.soil_strength_pa.is_finite() || self.soil_strength_pa < 0.0 {
            return Err("soil_strength_pa");
        }
        if !self.scarring_drag_coefficient.is_finite() || self.scarring_drag_coefficient < 0.0 {
            return Err("scarring_drag_coefficient");
        }
        if !self.scarring_layer_density_kgpm3.is_finite() || self.scarring_layer_density_kgpm3 < 0.0
        {
            return Err("scarring_layer_density_kgpm3");
        }
        if self
            .scarring_max_depth_m
            .is_some_and(|depth| !depth.is_finite() || depth < 0.0)
        {
            return Err("scarring_max_depth_m");
        }
        Ok(())
    }
}

#[derive(Debug, Default, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum ScarringDepthSource {
    #[default]
    None,
    Computed,
    ComputedCapped,
    Explicit,
    ExplicitCapped,
}

#[derive(Debug, Default, Clone, Copy, Serialize, Deserialize, PartialEq)]
pub struct ScarringDiagnostics {
    pub scarring_depth_m: f64,
    pub scarring_area_m2: f64,
    pub scarring_drag_force_n: f64,
    pub scarring_uncapped_energy_loss_j: f64,
    pub scarring_energy_loss_j: f64,
    pub scarring_depth_source: ScarringDepthSource,
}

#[derive(Debug, Default, Clone, Copy, PartialEq)]
pub struct ScarringDepthEstimate {
    pub depth_m: f64,
    pub source: ScarringDepthSource,
}

#[derive(Debug, Clone, Copy, PartialEq)]
pub struct RotationalContactSettings {
    pub dt_s: f64,
    pub gravity_mps2: f64,
    pub friction_coefficient: f64,
    pub rolling_resistance_coefficient: f64,
    pub stop_speed_mps: f64,
}

#[derive(Debug, Clone, Copy, PartialEq)]
pub struct ContactParameters {
    pub normal_restitution: f64,
    pub tangential_restitution: f64,
    pub friction_coefficient: f64,
    pub rolling_resistance_coefficient: f64,
    pub scarring: ScarringSettings,
}

pub trait ContactParameterProvider: Send + Sync {
    fn parameters_at(&self, x_m: f64, y_m: f64, base: ContactParameters) -> ContactParameters;
}

pub fn gravity_vector(gravity_mps2: f64) -> Vec3 {
    Vec3::new(0.0, 0.0, -gravity_mps2)
}

pub fn ballistic_step(state: &mut BodyState, dt_s: f64, gravity_mps2: f64) {
    let g = gravity_vector(gravity_mps2);
    state.position_m += state.velocity_mps * dt_s + 0.5 * g * dt_s * dt_s;
    state.velocity_mps += g * dt_s;
}

pub fn acceleration_from_gravity(gravity_mps2: f64) -> Vec3 {
    gravity_vector(gravity_mps2)
}

pub fn resolve_sphere_contact(
    state: &mut BodyState,
    terrain: &dyn Terrain,
    radius_m: f64,
    normal_restitution: f64,
    tangential_restitution: f64,
    friction_coefficient: f64,
) -> ContactResponse {
    let normal = terrain.normal(state.position_m.x, state.position_m.y);
    resolve_sphere_contact_with_normal(
        state,
        terrain,
        radius_m,
        normal,
        normal_restitution,
        tangential_restitution,
        friction_coefficient,
    )
}

pub fn resolve_sphere_contact_with_normal(
    state: &mut BodyState,
    terrain: &dyn Terrain,
    radius_m: f64,
    contact_normal: Vec3,
    normal_restitution: f64,
    tangential_restitution: f64,
    friction_coefficient: f64,
) -> ContactResponse {
    let signed_distance = terrain.signed_distance_sphere(state.position_m, radius_m);
    if signed_distance > 0.0 {
        return ContactResponse {
            impacted: false,
            sliding: false,
            rolling: false,
            contact_tangent_speed_mps: 0.0,
            rolling_residual_mps: 0.0,
        };
    }

    let projection_normal = terrain.normal(state.position_m.x, state.position_m.y);
    state.position_m -= signed_distance * projection_normal;
    let normal = unit_or(contact_normal, projection_normal);

    let vn = state.velocity_mps.dot(&normal);
    let normal_velocity = vn * normal;
    let tangential_velocity = state.velocity_mps - normal_velocity;

    if vn < 0.0 {
        let post_normal_velocity = -normal_restitution.clamp(0.0, 1.0) * normal_velocity;
        let requested_tangent_change =
            (1.0 - tangential_restitution.clamp(0.0, 1.0)) * tangential_velocity.norm();
        let friction_cap = friction_coefficient.max(0.0) * (1.0 + normal_restitution) * (-vn);
        let tangent_scale = if tangential_velocity.norm() > 0.0 {
            1.0 - requested_tangent_change.min(friction_cap) / tangential_velocity.norm()
        } else {
            0.0
        };
        state.velocity_mps = post_normal_velocity + tangential_velocity * tangent_scale.max(0.0);
        ContactResponse {
            impacted: true,
            sliding: state.velocity_mps.norm() > 0.0,
            rolling: false,
            contact_tangent_speed_mps: tangential_velocity.norm(),
            rolling_residual_mps: tangential_velocity.norm(),
        }
    } else {
        state.velocity_mps -= normal_velocity;
        ContactResponse {
            impacted: false,
            sliding: tangential_velocity.norm() > 0.0,
            rolling: false,
            contact_tangent_speed_mps: tangential_velocity.norm(),
            rolling_residual_mps: tangential_velocity.norm(),
        }
    }
}

pub fn resolve_rotational_sphere_contact(
    state: &mut BodyState,
    terrain: &dyn Terrain,
    block: SphereBlock,
    normal_restitution: f64,
    tangential_restitution: f64,
    friction_coefficient: f64,
) -> ContactResponse {
    let normal = terrain.normal(state.position_m.x, state.position_m.y);
    resolve_rotational_sphere_contact_with_normal(
        state,
        terrain,
        block,
        normal,
        normal_restitution,
        tangential_restitution,
        friction_coefficient,
    )
}

pub fn resolve_rotational_sphere_contact_with_normal(
    state: &mut BodyState,
    terrain: &dyn Terrain,
    block: SphereBlock,
    contact_normal: Vec3,
    normal_restitution: f64,
    tangential_restitution: f64,
    friction_coefficient: f64,
) -> ContactResponse {
    let signed_distance = terrain.signed_distance_sphere(state.position_m, block.radius_m);
    if signed_distance > 0.0 {
        return ContactResponse {
            impacted: false,
            sliding: false,
            rolling: false,
            contact_tangent_speed_mps: 0.0,
            rolling_residual_mps: 0.0,
        };
    }

    let projection_normal = terrain.normal(state.position_m.x, state.position_m.y);
    state.position_m -= signed_distance * projection_normal;
    let normal = unit_or(contact_normal, projection_normal);
    let contact_offset = -block.radius_m * normal;
    let contact_velocity = contact_point_velocity(state, contact_offset);
    let vn = contact_velocity.dot(&normal);
    let contact_tangent_velocity = contact_velocity - vn * normal;
    let initial_tangent_speed = contact_tangent_velocity.norm();

    if vn < 0.0 {
        let normal_impulse =
            block.mass_kg * (1.0 + normal_restitution.clamp(0.0, 1.0)) * (-vn) * normal;
        apply_impulse(state, block, contact_offset, normal_impulse);

        if initial_tangent_speed > 0.0 {
            let tangent_denominator = tangential_impulse_denominator(block);
            let requested_impulse = -((1.0 - tangential_restitution.clamp(0.0, 1.0))
                / tangent_denominator)
                * contact_tangent_velocity;
            let friction_cap = friction_coefficient.max(0.0) * normal_impulse.norm();
            let tangent_impulse = clamp_vector_norm(requested_impulse, friction_cap);
            apply_impulse(state, block, contact_offset, tangent_impulse);
        }

        let residual = rolling_residual(state, normal, block.radius_m);
        ContactResponse {
            impacted: true,
            sliding: residual > ROLLING_RESIDUAL_TOLERANCE_MPS,
            rolling: residual <= ROLLING_RESIDUAL_TOLERANCE_MPS,
            contact_tangent_speed_mps: initial_tangent_speed,
            rolling_residual_mps: residual,
        }
    } else {
        state.velocity_mps -= state.velocity_mps.dot(&normal) * normal;
        let residual = rolling_residual(state, normal, block.radius_m);
        ContactResponse {
            impacted: false,
            sliding: residual > ROLLING_RESIDUAL_TOLERANCE_MPS,
            rolling: residual <= ROLLING_RESIDUAL_TOLERANCE_MPS && state.velocity_mps.norm() > 0.0,
            contact_tangent_speed_mps: initial_tangent_speed,
            rolling_residual_mps: residual,
        }
    }
}

pub fn apply_contact_friction(
    state: &mut BodyState,
    terrain: &dyn Terrain,
    dt_s: f64,
    gravity_mps2: f64,
    friction_coefficient: f64,
    stop_speed_mps: f64,
) -> bool {
    let normal = terrain.normal(state.position_m.x, state.position_m.y);
    let gravity = gravity_vector(gravity_mps2);
    let normal_acc = gravity.dot(&normal) * normal;
    let tangent_acc = gravity - normal_acc;
    let mut tangent_velocity = state.velocity_mps - state.velocity_mps.dot(&normal) * normal;

    let friction_limit = friction_coefficient.max(0.0) * normal_acc.norm();
    if tangent_velocity.norm() <= stop_speed_mps && tangent_acc.norm() <= friction_limit {
        state.velocity_mps = Vec3::zeros();
        return true;
    }

    tangent_velocity += tangent_acc * dt_s;
    let speed = tangent_velocity.norm();
    if speed > 0.0 {
        let friction_delta = friction_limit * dt_s;
        let new_speed = (speed - friction_delta).max(0.0);
        tangent_velocity *= new_speed / speed;
    }

    state.velocity_mps = tangent_velocity;
    if state.velocity_mps.norm() <= stop_speed_mps && tangent_acc.norm() <= friction_limit {
        state.velocity_mps = Vec3::zeros();
        true
    } else {
        false
    }
}

pub fn apply_contact_friction_after_ballistic_step(
    state: &mut BodyState,
    terrain: &dyn Terrain,
    dt_s: f64,
    gravity_mps2: f64,
    friction_coefficient: f64,
    stop_speed_mps: f64,
) -> bool {
    let normal = terrain.normal(state.position_m.x, state.position_m.y);
    let gravity = gravity_vector(gravity_mps2);
    let normal_acc = gravity.dot(&normal) * normal;
    let tangent_acc = gravity - normal_acc;
    state.velocity_mps -= tangent_acc * dt_s;
    apply_contact_friction(
        state,
        terrain,
        dt_s,
        gravity_mps2,
        friction_coefficient,
        stop_speed_mps,
    )
}

pub fn apply_rotational_contact_motion(
    state: &mut BodyState,
    terrain: &dyn Terrain,
    block: SphereBlock,
    settings: RotationalContactSettings,
) -> ContactResponse {
    let normal = terrain.normal(state.position_m.x, state.position_m.y);
    let gravity = gravity_vector(settings.gravity_mps2);
    let normal_acc = gravity.dot(&normal) * normal;
    let tangent_acc = gravity - normal_acc;
    let normal_acc_magnitude = normal_acc.norm();
    let static_friction_limit = settings.friction_coefficient.max(0.0) * normal_acc_magnitude;
    let rolling_resistance =
        settings.rolling_resistance_coefficient.max(0.0) * normal_acc_magnitude;

    state.velocity_mps -= state.velocity_mps.dot(&normal) * normal;
    state.velocity_mps -= tangent_acc * settings.dt_s;
    let contact_offset = -block.radius_m * normal;
    let residual_before = rolling_residual(state, normal, block.radius_m);
    let tangent_velocity = state.velocity_mps - state.velocity_mps.dot(&normal) * normal;
    let rolling_possible = residual_before
        <= settings.stop_speed_mps.max(ROLLING_RESIDUAL_TOLERANCE_MPS)
        && static_friction_limit + 1.0e-12 >= rolling_static_friction_required(tangent_acc);

    if rolling_possible {
        let mut next_tangent_velocity =
            tangent_velocity + (5.0 / 7.0) * tangent_acc * settings.dt_s;
        let speed = next_tangent_velocity.norm();
        if speed > 0.0 && rolling_resistance > 0.0 {
            let new_speed = (speed - rolling_resistance * settings.dt_s).max(0.0);
            next_tangent_velocity *= new_speed / speed;
        }

        if next_tangent_velocity.norm() <= settings.stop_speed_mps
            && tangent_acc.norm() <= rolling_resistance + 1.0e-12
        {
            state.velocity_mps = Vec3::zeros();
            state.angular_velocity_radps = Vec3::zeros();
            return ContactResponse {
                impacted: false,
                sliding: false,
                rolling: false,
                contact_tangent_speed_mps: residual_before,
                rolling_residual_mps: 0.0,
            };
        }

        state.velocity_mps = next_tangent_velocity;
        state.angular_velocity_radps = normal.cross(&state.velocity_mps) / block.radius_m;
        let residual = rolling_residual(state, normal, block.radius_m);
        return ContactResponse {
            impacted: false,
            sliding: false,
            rolling: true,
            contact_tangent_speed_mps: residual_before,
            rolling_residual_mps: residual,
        };
    }

    if tangent_velocity.norm() <= settings.stop_speed_mps
        && tangent_acc.norm() <= static_friction_limit
    {
        state.velocity_mps = Vec3::zeros();
        return ContactResponse {
            impacted: false,
            sliding: false,
            rolling: false,
            contact_tangent_speed_mps: residual_before,
            rolling_residual_mps: 0.0,
        };
    }

    state.velocity_mps += tangent_acc * settings.dt_s;
    let slip_velocity = contact_point_tangent_velocity(state, normal, block.radius_m);
    let slip_speed = slip_velocity.norm();
    if slip_speed > 0.0 && static_friction_limit > 0.0 {
        let impulse_cap = block.mass_kg * static_friction_limit * settings.dt_s;
        let impulse_needed = -slip_velocity / tangential_impulse_denominator(block);
        let impulse = clamp_vector_norm(impulse_needed, impulse_cap);
        apply_impulse(state, block, contact_offset, impulse);
    }

    state.velocity_mps -= state.velocity_mps.dot(&normal) * normal;
    let residual = rolling_residual(state, normal, block.radius_m);
    ContactResponse {
        impacted: false,
        sliding: residual > ROLLING_RESIDUAL_TOLERANCE_MPS || state.velocity_mps.norm() > 0.0,
        rolling: residual <= ROLLING_RESIDUAL_TOLERANCE_MPS && state.velocity_mps.norm() > 0.0,
        contact_tangent_speed_mps: slip_speed,
        rolling_residual_mps: residual,
    }
}

pub fn contact_point_tangent_velocity(state: &BodyState, normal: Vec3, radius_m: f64) -> Vec3 {
    let contact_offset = -radius_m * normal;
    let contact_velocity = contact_point_velocity(state, contact_offset);
    contact_velocity - contact_velocity.dot(&normal) * normal
}

pub fn rolling_residual(state: &BodyState, normal: Vec3, radius_m: f64) -> f64 {
    contact_point_tangent_velocity(state, normal, radius_m).norm()
}

pub fn apply_scarring_energy_loss(
    state: &mut BodyState,
    block: SphereBlock,
    incoming_velocity_mps: Vec3,
    contact_normal: Vec3,
    settings: ScarringSettings,
) -> ScarringDiagnostics {
    if settings.soil_interaction_model != SoilInteractionModel::ScarringContactV1 {
        return ScarringDiagnostics::default();
    }

    let normal = unit_or(contact_normal, Vec3::new(0.0, 0.0, 1.0));
    let normal_impact_speed_mps = (-incoming_velocity_mps.dot(&normal)).max(0.0);
    if normal_impact_speed_mps <= 0.0 {
        return ScarringDiagnostics::default();
    }

    let depth = estimate_scarring_depth(
        block.mass_kg,
        block.radius_m,
        normal_impact_speed_mps,
        settings.soil_strength_pa,
        settings.scarring_max_depth_m,
    );
    let depth_m = depth.depth_m;
    if depth_m <= 0.0 {
        return ScarringDiagnostics::default();
    }

    let scar_area_m2 = sphere_cap_projection_area_m2(block.radius_m, depth_m);
    let impact_speed_mps = incoming_velocity_mps.norm();
    let drag_force_n = 0.5
        * settings.scarring_drag_coefficient.max(0.0)
        * settings.scarring_layer_density_kgpm3.max(0.0)
        * scar_area_m2
        * impact_speed_mps
        * impact_speed_mps;
    let available_kinetic_j = 0.5 * block.mass_kg * state.velocity_mps.norm_squared();
    let uncapped_energy_loss_j = (drag_force_n * depth_m).max(0.0);
    let energy_loss_j = uncapped_energy_loss_j.clamp(0.0, available_kinetic_j);

    if energy_loss_j > 0.0 && available_kinetic_j > 0.0 {
        let retained_fraction = ((available_kinetic_j - energy_loss_j) / available_kinetic_j)
            .max(0.0)
            .sqrt();
        state.velocity_mps *= retained_fraction;
    }

    ScarringDiagnostics {
        scarring_depth_m: depth_m,
        scarring_area_m2: scar_area_m2,
        scarring_drag_force_n: drag_force_n,
        scarring_uncapped_energy_loss_j: uncapped_energy_loss_j,
        scarring_energy_loss_j: energy_loss_j,
        scarring_depth_source: depth.source,
    }
}

pub fn estimate_scarring_depth_m(
    mass_kg: f64,
    radius_m: f64,
    normal_impact_speed_mps: f64,
    soil_strength_pa: f64,
    max_depth_m: Option<f64>,
) -> f64 {
    estimate_scarring_depth(
        mass_kg,
        radius_m,
        normal_impact_speed_mps,
        soil_strength_pa,
        max_depth_m,
    )
    .depth_m
}

pub fn estimate_scarring_depth(
    mass_kg: f64,
    radius_m: f64,
    normal_impact_speed_mps: f64,
    soil_strength_pa: f64,
    max_depth_m: Option<f64>,
) -> ScarringDepthEstimate {
    let cap_m = radius_m.max(0.0);
    if cap_m <= 0.0 {
        return ScarringDepthEstimate::default();
    }
    if let Some(depth_m) = max_depth_m {
        let clamped = depth_m.clamp(0.0, cap_m);
        return ScarringDepthEstimate {
            depth_m: clamped,
            source: if depth_m > cap_m {
                ScarringDepthSource::ExplicitCapped
            } else if clamped > 0.0 {
                ScarringDepthSource::Explicit
            } else {
                ScarringDepthSource::None
            },
        };
    }
    if mass_kg <= 0.0 || normal_impact_speed_mps <= 0.0 || soil_strength_pa <= 0.0 {
        return ScarringDepthEstimate::default();
    }
    let soil_strength_kpa = soil_strength_pa / 1000.0;
    let depth_m = 0.16
        * mass_kg.powf(0.25)
        * soil_strength_kpa.powf(-0.4)
        * normal_impact_speed_mps.powf(0.8);
    let clamped = depth_m.clamp(0.0, cap_m);
    ScarringDepthEstimate {
        depth_m: clamped,
        source: if depth_m > cap_m {
            ScarringDepthSource::ComputedCapped
        } else if clamped > 0.0 {
            ScarringDepthSource::Computed
        } else {
            ScarringDepthSource::None
        },
    }
}

pub fn sphere_cap_projection_area_m2(radius_m: f64, depth_m: f64) -> f64 {
    let radius_m = radius_m.max(0.0);
    let depth_m = depth_m.clamp(0.0, 2.0 * radius_m);
    PI * (2.0 * radius_m * depth_m - depth_m * depth_m).max(0.0)
}

fn contact_point_velocity(state: &BodyState, contact_offset: Vec3) -> Vec3 {
    state.velocity_mps + state.angular_velocity_radps.cross(&contact_offset)
}

fn apply_impulse(state: &mut BodyState, block: SphereBlock, contact_offset: Vec3, impulse: Vec3) {
    state.velocity_mps += impulse / block.mass_kg;
    state.angular_velocity_radps +=
        contact_offset.cross(&impulse) / block.moment_of_inertia_kg_m2();
}

fn tangential_impulse_denominator(block: SphereBlock) -> f64 {
    1.0 / block.mass_kg + block.radius_m * block.radius_m / block.moment_of_inertia_kg_m2()
}

fn rolling_static_friction_required(tangent_acc: Vec3) -> f64 {
    (2.0 / 7.0) * tangent_acc.norm()
}

fn clamp_vector_norm(vector: Vec3, max_norm: f64) -> Vec3 {
    let norm = vector.norm();
    if norm > max_norm.max(0.0) && norm > 0.0 {
        vector * (max_norm.max(0.0) / norm)
    } else {
        vector
    }
}

fn unit_or(vector: Vec3, fallback: Vec3) -> Vec3 {
    let norm = vector.norm();
    if norm > 0.0 {
        vector / norm
    } else {
        fallback
    }
}
