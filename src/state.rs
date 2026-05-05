use crate::{geometry::SphereBlock, Vec3};
use serde::{Deserialize, Serialize};

/// Dynamic state of the simulated block center of mass.
#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq)]
pub struct BodyState {
    pub position_m: Vec3,
    pub velocity_mps: Vec3,
    pub angular_velocity_radps: Vec3,
}

impl BodyState {
    pub fn new(position_m: Vec3, velocity_mps: Vec3) -> Self {
        Self {
            position_m,
            velocity_mps,
            angular_velocity_radps: Vec3::zeros(),
        }
    }

    pub fn speed_mps(&self) -> f64 {
        self.velocity_mps.norm()
    }
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum ContactState {
    Airborne,
    Sliding,
    Impact,
    Rolling,
    Stopped,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq)]
pub struct EnergyDiagnostics {
    pub translational_j: f64,
    pub rotational_j: f64,
    pub potential_j: f64,
    pub total_j: f64,
}

impl EnergyDiagnostics {
    pub fn from_state(state: &BodyState, block: &SphereBlock, gravity_mps2: f64) -> Self {
        let translational_j = 0.5 * block.mass_kg * state.velocity_mps.norm_squared();
        let rotational_j =
            0.5 * block.moment_of_inertia_kg_m2() * state.angular_velocity_radps.norm_squared();
        let potential_j = block.mass_kg * gravity_mps2 * state.position_m.z;
        Self {
            translational_j,
            rotational_j,
            potential_j,
            total_j: translational_j + rotational_j + potential_j,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct TrajectorySample {
    pub time_s: f64,
    pub x_m: f64,
    pub y_m: f64,
    pub z_m: f64,
    pub vx_mps: f64,
    pub vy_mps: f64,
    pub vz_mps: f64,
    pub speed_mps: f64,
    pub kinetic_j: f64,
    pub rotational_j: f64,
    pub potential_j: f64,
    pub total_energy_j: f64,
    pub contact_state: ContactState,
    pub omega_x_radps: f64,
    pub omega_y_radps: f64,
    pub omega_z_radps: f64,
    pub contact_tangent_speed_mps: f64,
    pub rolling_residual_mps: f64,
}

impl TrajectorySample {
    pub fn from_state(
        time_s: f64,
        state: &BodyState,
        block: &SphereBlock,
        gravity_mps2: f64,
        contact_state: ContactState,
    ) -> Self {
        Self::from_state_with_contact_diagnostics(
            time_s,
            state,
            block,
            gravity_mps2,
            contact_state,
            0.0,
            0.0,
        )
    }

    pub fn from_state_with_contact_diagnostics(
        time_s: f64,
        state: &BodyState,
        block: &SphereBlock,
        gravity_mps2: f64,
        contact_state: ContactState,
        contact_tangent_speed_mps: f64,
        rolling_residual_mps: f64,
    ) -> Self {
        let energy = EnergyDiagnostics::from_state(state, block, gravity_mps2);
        Self {
            time_s,
            x_m: state.position_m.x,
            y_m: state.position_m.y,
            z_m: state.position_m.z,
            vx_mps: state.velocity_mps.x,
            vy_mps: state.velocity_mps.y,
            vz_mps: state.velocity_mps.z,
            speed_mps: state.speed_mps(),
            kinetic_j: energy.translational_j,
            rotational_j: energy.rotational_j,
            potential_j: energy.potential_j,
            total_energy_j: energy.total_j,
            contact_state,
            omega_x_radps: state.angular_velocity_radps.x,
            omega_y_radps: state.angular_velocity_radps.y,
            omega_z_radps: state.angular_velocity_radps.z,
            contact_tangent_speed_mps,
            rolling_residual_mps,
        }
    }
}
