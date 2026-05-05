use crate::{state::BodyState, terrain::Terrain, Vec3};

#[derive(Debug, Clone, Copy, PartialEq)]
pub struct ContactResponse {
    pub impacted: bool,
    pub sliding: bool,
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
    let signed_distance = terrain.signed_distance_sphere(state.position_m, radius_m);
    if signed_distance > 0.0 {
        return ContactResponse {
            impacted: false,
            sliding: false,
        };
    }

    let normal = terrain.normal(state.position_m.x, state.position_m.y);
    state.position_m -= signed_distance * normal;

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
        }
    } else {
        state.velocity_mps -= normal_velocity;
        ContactResponse {
            impacted: false,
            sliding: tangential_velocity.norm() > 0.0,
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
