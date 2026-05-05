use crate::{
    dynamics::{apply_contact_friction, ballistic_step, resolve_sphere_contact},
    geometry::SphereBlock,
    state::{BodyState, ContactState, TrajectorySample},
    terrain::Terrain,
};

#[derive(Debug, Clone, Copy, PartialEq)]
pub struct IntegratorSettings {
    pub dt_s: f64,
    pub max_time_s: f64,
    pub gravity_mps2: f64,
    pub normal_restitution: f64,
    pub tangential_restitution: f64,
    pub friction_coefficient: f64,
    pub stop_speed_mps: f64,
}

pub fn simulate_fixed_step(
    initial: BodyState,
    block: SphereBlock,
    terrain: &dyn Terrain,
    settings: IntegratorSettings,
) -> Vec<TrajectorySample> {
    let mut state = initial;
    let mut time_s = 0.0;
    let mut samples = Vec::new();
    samples.push(TrajectorySample::from_state(
        time_s,
        &state,
        &block,
        settings.gravity_mps2,
        ContactState::Airborne,
    ));

    let max_steps = (settings.max_time_s / settings.dt_s + 1.0e-12).floor() as usize;
    for _ in 0..max_steps {
        ballistic_step(&mut state, settings.dt_s, settings.gravity_mps2);
        time_s += settings.dt_s;

        let response = resolve_sphere_contact(
            &mut state,
            terrain,
            block.radius_m,
            settings.normal_restitution,
            settings.tangential_restitution,
            settings.friction_coefficient,
        );

        let mut contact_state = if response.impacted {
            ContactState::Impact
        } else if response.sliding {
            ContactState::Sliding
        } else {
            ContactState::Airborne
        };

        let signed_distance = terrain.signed_distance_sphere(state.position_m, block.radius_m);
        let normal = terrain.normal(state.position_m.x, state.position_m.y);
        if signed_distance.abs() < 1.0e-7 && state.velocity_mps.dot(&normal) <= 1.0e-7 {
            let stopped = apply_contact_friction(
                &mut state,
                terrain,
                settings.dt_s,
                settings.gravity_mps2,
                settings.friction_coefficient,
                settings.stop_speed_mps,
            );
            contact_state = if stopped {
                ContactState::Stopped
            } else {
                ContactState::Sliding
            };
        }

        samples.push(TrajectorySample::from_state(
            time_s,
            &state,
            &block,
            settings.gravity_mps2,
            contact_state,
        ));

        if contact_state == ContactState::Stopped {
            break;
        }
    }

    samples
}
