use crate::{
    dynamics::{
        apply_contact_friction, apply_rotational_contact_motion, apply_scarring_energy_loss,
        ballistic_step, contact_point_tangent_velocity,
        resolve_rotational_sphere_contact_with_normal, resolve_sphere_contact_with_normal,
        rolling_residual, ContactModel, RotationalContactSettings, ScarringSettings,
    },
    geometry::SphereBlock,
    state::{BodyState, ContactState, TrajectoryDiagnostics, TrajectorySample},
    stochastic::{sample_contact_roughness, seeded_rng, ContactRoughness},
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
    pub rolling_resistance_coefficient: f64,
    pub stop_speed_mps: f64,
    pub contact_model: ContactModel,
    pub scarring: ScarringSettings,
    pub roughness: ContactRoughness,
    pub roughness_seed: Option<u64>,
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
    let mut roughness_rng = settings
        .roughness
        .is_active()
        .then(|| seeded_rng(settings.roughness_seed.unwrap_or(0)));
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

        let base_normal = terrain.normal(state.position_m.x, state.position_m.y);
        let incoming_velocity = state.velocity_mps;
        let signed_distance_before_response =
            terrain.signed_distance_sphere(state.position_m, block.radius_m);
        let incoming =
            signed_distance_before_response <= 0.0 && state.velocity_mps.dot(&base_normal) < 0.0;
        let effective_contact = if incoming {
            sample_contact_roughness(
                base_normal,
                settings.normal_restitution,
                settings.tangential_restitution,
                settings.friction_coefficient,
                settings.roughness,
                roughness_rng.as_mut(),
            )
        } else {
            sample_contact_roughness(
                base_normal,
                settings.normal_restitution,
                settings.tangential_restitution,
                settings.friction_coefficient,
                ContactRoughness::default(),
                None,
            )
        };

        let response = match settings.contact_model {
            ContactModel::TranslationalV0 => resolve_sphere_contact_with_normal(
                &mut state,
                terrain,
                block.radius_m,
                effective_contact.normal,
                effective_contact.normal_restitution,
                effective_contact.tangential_restitution,
                effective_contact.friction_coefficient,
            ),
            ContactModel::SphereRotationalV1 => resolve_rotational_sphere_contact_with_normal(
                &mut state,
                terrain,
                block,
                effective_contact.normal,
                effective_contact.normal_restitution,
                effective_contact.tangential_restitution,
                effective_contact.friction_coefficient,
            ),
        };
        let scarring = if incoming {
            apply_scarring_energy_loss(
                &mut state,
                block,
                incoming_velocity,
                base_normal,
                settings.scarring,
            )
        } else {
            Default::default()
        };

        let mut contact_state = if response.impacted {
            ContactState::Impact
        } else if response.rolling {
            ContactState::Rolling
        } else if response.sliding {
            ContactState::Sliding
        } else {
            ContactState::Airborne
        };

        let signed_distance = terrain.signed_distance_sphere(state.position_m, block.radius_m);
        let normal = terrain.normal(state.position_m.x, state.position_m.y);
        if signed_distance.abs() < 1.0e-7 && state.velocity_mps.dot(&normal) <= 1.0e-7 {
            contact_state = match settings.contact_model {
                ContactModel::TranslationalV0 => {
                    let stopped = apply_contact_friction(
                        &mut state,
                        terrain,
                        settings.dt_s,
                        settings.gravity_mps2,
                        settings.friction_coefficient,
                        settings.stop_speed_mps,
                    );
                    if stopped {
                        ContactState::Stopped
                    } else {
                        ContactState::Sliding
                    }
                }
                ContactModel::SphereRotationalV1 => {
                    let contact_response = apply_rotational_contact_motion(
                        &mut state,
                        terrain,
                        block,
                        RotationalContactSettings {
                            dt_s: settings.dt_s,
                            gravity_mps2: settings.gravity_mps2,
                            friction_coefficient: settings.friction_coefficient,
                            rolling_resistance_coefficient: settings.rolling_resistance_coefficient,
                            stop_speed_mps: settings.stop_speed_mps,
                        },
                    );
                    if !contact_response.sliding
                        && !contact_response.rolling
                        && state.velocity_mps.norm() <= settings.stop_speed_mps
                    {
                        ContactState::Stopped
                    } else if contact_response.rolling {
                        ContactState::Rolling
                    } else {
                        ContactState::Sliding
                    }
                }
            };
        }

        let contact_tangent_speed_mps = if signed_distance.abs() < 1.0e-7 {
            contact_point_tangent_velocity(
                &state,
                terrain.normal(state.position_m.x, state.position_m.y),
                block.radius_m,
            )
            .norm()
        } else {
            response.contact_tangent_speed_mps
        };
        let rolling_residual_mps = if signed_distance.abs() < 1.0e-7 {
            rolling_residual(
                &state,
                terrain.normal(state.position_m.x, state.position_m.y),
                block.radius_m,
            )
        } else {
            response.rolling_residual_mps
        };

        samples.push(TrajectorySample::from_state_with_diagnostics(
            time_s,
            &state,
            &block,
            settings.gravity_mps2,
            contact_state,
            TrajectoryDiagnostics {
                contact_tangent_speed_mps,
                rolling_residual_mps,
                scarring,
            },
        ));

        if contact_state == ContactState::Stopped {
            break;
        }
    }

    samples
}
