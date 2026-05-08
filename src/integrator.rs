use crate::{
    dynamics::{
        apply_scarring_energy_loss, ballistic_step, contact_point_tangent_velocity,
        rolling_residual, try_apply_contact_friction_after_ballistic_step,
        try_apply_rotational_contact_motion, try_resolve_rotational_sphere_contact_with_normal,
        try_resolve_sphere_contact_with_normal, ContactModel, ContactParameterProvider,
        ContactParameters, RotationalContactSettings, ScarringSettings,
    },
    geometry::SphereBlock,
    state::{
        BodyState, ContactState, ImpactEvent, ImpactStageEnergy, TrajectoryDiagnostics,
        TrajectorySample,
    },
    stochastic::{sample_contact_roughness, seeded_rng, ContactRoughness},
    terrain::{Terrain, TerrainError},
};
use thiserror::Error;

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

#[derive(Debug, Clone, PartialEq)]
pub struct IntegrationResult {
    pub samples: Vec<TrajectorySample>,
    pub impact_events: Vec<ImpactEvent>,
}

#[derive(Debug, Error)]
pub enum IntegrationError {
    #[error("terrain query failed during integration: {0}")]
    Terrain(#[from] TerrainError),
    #[error("unsupported contact model for fixed-step integration: {0}")]
    UnsupportedContactModel(&'static str),
}

pub fn simulate_fixed_step(
    initial: BodyState,
    block: SphereBlock,
    terrain: &dyn Terrain,
    settings: IntegratorSettings,
) -> Vec<TrajectorySample> {
    simulate_fixed_step_with_events(initial, block, terrain, settings).samples
}

/// Compatibility wrapper around the structured-error fixed-step integrator.
///
/// New runtime and DEM-facing code should call
/// [`try_simulate_fixed_step_with_events`] or
/// [`try_simulate_fixed_step_with_events_and_contact_parameters`] so terrain
/// and unsupported-contact failures remain explicit. This wrapper is retained
/// for older analytic tests and simple callers and will panic if the fallible
/// path returns an error.
pub fn simulate_fixed_step_with_events(
    initial: BodyState,
    block: SphereBlock,
    terrain: &dyn Terrain,
    settings: IntegratorSettings,
) -> IntegrationResult {
    simulate_fixed_step_with_events_and_contact_parameters(initial, block, terrain, settings, None)
}

pub fn try_simulate_fixed_step_with_events(
    initial: BodyState,
    block: SphereBlock,
    terrain: &dyn Terrain,
    settings: IntegratorSettings,
) -> Result<IntegrationResult, IntegrationError> {
    try_simulate_fixed_step_with_events_and_contact_parameters(
        initial, block, terrain, settings, None,
    )
}

/// Compatibility wrapper around the structured-error fixed-step integrator
/// with optional terrain/material contact-parameter overrides.
///
/// New runtime and DEM-facing code should call the `try_` variant below. This
/// infallible wrapper is retained for older analytic tests and simple callers
/// and will panic if terrain, nodata, or unsupported-contact errors are
/// returned by the fallible path.
pub fn simulate_fixed_step_with_events_and_contact_parameters(
    initial: BodyState,
    block: SphereBlock,
    terrain: &dyn Terrain,
    settings: IntegratorSettings,
    contact_parameters: Option<&dyn ContactParameterProvider>,
) -> IntegrationResult {
    try_simulate_fixed_step_with_events_and_contact_parameters(
        initial,
        block,
        terrain,
        settings,
        contact_parameters,
    )
    .expect("fixed-step terrain query failed")
}

pub fn try_simulate_fixed_step_with_events_and_contact_parameters(
    initial: BodyState,
    block: SphereBlock,
    terrain: &dyn Terrain,
    settings: IntegratorSettings,
    contact_parameters: Option<&dyn ContactParameterProvider>,
) -> Result<IntegrationResult, IntegrationError> {
    if settings.contact_model == ContactModel::ShapeContactV0 {
        return Err(IntegrationError::UnsupportedContactModel(
            "shape_contact_v0 is an internal verification scaffold and is not wired into fixed-step integration",
        ));
    }
    let mut state = initial;
    let mut time_s = 0.0;
    let mut samples = Vec::new();
    let mut impact_events = Vec::new();
    let mut cumulative_scarring_energy_loss_j = 0.0;
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

        let base_parameters = ContactParameters {
            normal_restitution: settings.normal_restitution,
            tangential_restitution: settings.tangential_restitution,
            friction_coefficient: settings.friction_coefficient,
            rolling_resistance_coefficient: settings.rolling_resistance_coefficient,
            scarring: settings.scarring,
        };
        let local_parameters = contact_parameters
            .map(|provider| {
                provider.parameters_at(state.position_m.x, state.position_m.y, base_parameters)
            })
            .unwrap_or(base_parameters);

        let base_normal = terrain.try_normal(state.position_m.x, state.position_m.y)?;
        let pre_contact_state = state;
        let incoming_velocity = state.velocity_mps;
        let signed_distance_before_response =
            terrain.try_signed_distance_sphere(state.position_m, block.radius_m)?;
        let incoming =
            signed_distance_before_response <= 0.0 && state.velocity_mps.dot(&base_normal) < 0.0;
        let effective_contact = if incoming {
            sample_contact_roughness(
                base_normal,
                local_parameters.normal_restitution,
                local_parameters.tangential_restitution,
                local_parameters.friction_coefficient,
                settings.roughness,
                roughness_rng.as_mut(),
            )
        } else {
            sample_contact_roughness(
                base_normal,
                local_parameters.normal_restitution,
                local_parameters.tangential_restitution,
                local_parameters.friction_coefficient,
                ContactRoughness::default(),
                None,
            )
        };

        let response = match settings.contact_model {
            ContactModel::TranslationalV0 => try_resolve_sphere_contact_with_normal(
                &mut state,
                terrain,
                block.radius_m,
                effective_contact.normal,
                effective_contact.normal_restitution,
                effective_contact.tangential_restitution,
                effective_contact.friction_coefficient,
            )?,
            ContactModel::SphereRotationalV1 => try_resolve_rotational_sphere_contact_with_normal(
                &mut state,
                terrain,
                block,
                effective_contact.normal,
                effective_contact.normal_restitution,
                effective_contact.tangential_restitution,
                effective_contact.friction_coefficient,
            )?,
            ContactModel::ShapeContactV0 => {
                return Err(IntegrationError::UnsupportedContactModel(
                    "shape_contact_v0 is not wired into fixed-step integration",
                ))
            }
        };
        let post_contact_state = state;
        let scarring = if incoming {
            apply_scarring_energy_loss(
                &mut state,
                block,
                incoming_velocity,
                base_normal,
                local_parameters.scarring,
            )
        } else {
            Default::default()
        };
        cumulative_scarring_energy_loss_j += scarring.scarring_energy_loss_j;
        let post_scarring_state = state;

        let mut contact_state = if response.impacted {
            ContactState::Impact
        } else if response.rolling {
            ContactState::Rolling
        } else if response.sliding {
            ContactState::Sliding
        } else {
            ContactState::Airborne
        };

        let signed_distance =
            terrain.try_signed_distance_sphere(state.position_m, block.radius_m)?;
        let normal = terrain.try_normal(state.position_m.x, state.position_m.y)?;
        if signed_distance.abs() < 1.0e-7 && state.velocity_mps.dot(&normal) <= 1.0e-7 {
            contact_state = match settings.contact_model {
                ContactModel::TranslationalV0 => {
                    let stopped = try_apply_contact_friction_after_ballistic_step(
                        &mut state,
                        terrain,
                        settings.dt_s,
                        settings.gravity_mps2,
                        local_parameters.friction_coefficient,
                        settings.stop_speed_mps,
                    )?;
                    if stopped {
                        ContactState::Stopped
                    } else {
                        ContactState::Sliding
                    }
                }
                ContactModel::SphereRotationalV1 => {
                    let contact_response = try_apply_rotational_contact_motion(
                        &mut state,
                        terrain,
                        block,
                        RotationalContactSettings {
                            dt_s: settings.dt_s,
                            gravity_mps2: settings.gravity_mps2,
                            friction_coefficient: local_parameters.friction_coefficient,
                            rolling_resistance_coefficient: local_parameters
                                .rolling_resistance_coefficient,
                            stop_speed_mps: settings.stop_speed_mps,
                        },
                    )?;
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
                ContactModel::ShapeContactV0 => {
                    return Err(IntegrationError::UnsupportedContactModel(
                        "shape_contact_v0 is not wired into fixed-step integration",
                    ))
                }
            };
        }

        let contact_tangent_speed_mps = if signed_distance.abs() < 1.0e-7 {
            contact_point_tangent_velocity(
                &state,
                terrain.try_normal(state.position_m.x, state.position_m.y)?,
                block.radius_m,
            )
            .norm()
        } else {
            response.contact_tangent_speed_mps
        };
        let rolling_residual_mps = if signed_distance.abs() < 1.0e-7 {
            rolling_residual(
                &state,
                terrain.try_normal(state.position_m.x, state.position_m.y)?,
                block.radius_m,
            )
        } else {
            response.rolling_residual_mps
        };

        if response.impacted {
            impact_events.push(build_impact_event(ImpactEventInput {
                impact_index: impact_events.len() + 1,
                time_s,
                block,
                terrain_normal: base_normal,
                effective_normal: effective_contact.normal,
                pre_contact_state,
                post_contact_state,
                post_scarring_state,
                post_step_state: state,
                scarring,
                cumulative_scarring_energy_loss_j,
            }));
        }

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

    Ok(IntegrationResult {
        samples,
        impact_events,
    })
}

#[allow(dead_code)]
#[derive(Debug, Clone, Copy, PartialEq)]
pub(crate) struct ShapeContactV0IntegratorSmokePrediction {
    pub(crate) pre_step_state: BodyState,
    pub(crate) predicted_state: BodyState,
    pub(crate) terrain_contact_point_m: crate::Vec3,
    pub(crate) terrain_normal_world: crate::Vec3,
}

#[allow(dead_code)]
pub(crate) fn shape_contact_v0_integrator_smoke_prediction(
    pre_step_state: BodyState,
    terrain: &dyn Terrain,
    dt_s: f64,
    gravity_mps2: f64,
) -> Result<ShapeContactV0IntegratorSmokePrediction, &'static str> {
    if !(dt_s.is_finite() && dt_s > 0.0) {
        return Err("dt_s must be positive and finite");
    }
    if !(gravity_mps2.is_finite() && gravity_mps2 > 0.0) {
        return Err("gravity_mps2 must be positive and finite");
    }
    let mut predicted_state = pre_step_state;
    ballistic_step(&mut predicted_state, dt_s, gravity_mps2);
    let terrain_height_m = terrain
        .try_height(predicted_state.position_m.x, predicted_state.position_m.y)
        .map_err(|_| "terrain height query failed")?;
    if !terrain_height_m.is_finite() {
        return Err("terrain height must be finite");
    }
    let terrain_normal_world = terrain
        .try_normal(predicted_state.position_m.x, predicted_state.position_m.y)
        .map_err(|_| "terrain normal query failed")?;
    if !terrain_normal_world.x.is_finite()
        || !terrain_normal_world.y.is_finite()
        || !terrain_normal_world.z.is_finite()
        || terrain_normal_world.norm() == 0.0
    {
        return Err("terrain normal must be finite and nonzero");
    }
    Ok(ShapeContactV0IntegratorSmokePrediction {
        pre_step_state,
        predicted_state,
        terrain_contact_point_m: crate::Vec3::new(
            predicted_state.position_m.x,
            predicted_state.position_m.y,
            terrain_height_m,
        ),
        terrain_normal_world,
    })
}

#[derive(Debug, Clone, Copy)]
struct ImpactEventInput {
    impact_index: usize,
    time_s: f64,
    block: SphereBlock,
    terrain_normal: crate::Vec3,
    effective_normal: crate::Vec3,
    pre_contact_state: BodyState,
    post_contact_state: BodyState,
    post_scarring_state: BodyState,
    post_step_state: BodyState,
    scarring: crate::dynamics::ScarringDiagnostics,
    cumulative_scarring_energy_loss_j: f64,
}

fn build_impact_event(input: ImpactEventInput) -> ImpactEvent {
    let normal = unit_or(input.terrain_normal, crate::Vec3::new(0.0, 0.0, 1.0));
    let effective_normal = unit_or(input.effective_normal, normal);
    let pre_energy = ImpactStageEnergy::from_state(&input.pre_contact_state, &input.block);
    let post_contact_energy =
        ImpactStageEnergy::from_state(&input.post_contact_state, &input.block);
    let post_scarring_energy =
        ImpactStageEnergy::from_state(&input.post_scarring_state, &input.block);
    let post_step_energy = ImpactStageEnergy::from_state(&input.post_step_state, &input.block);
    let incoming = input.pre_contact_state.velocity_mps;
    let post_contact = input.post_contact_state.velocity_mps;
    let post_scarring = input.post_scarring_state.velocity_mps;
    let post_step = input.post_step_state.velocity_mps;
    let (incoming_normal, incoming_tangent) = velocity_components(incoming, normal);
    let (post_contact_normal, post_contact_tangent) = velocity_components(post_contact, normal);
    let (post_scarring_normal, post_scarring_tangent) = velocity_components(post_scarring, normal);
    let (post_step_normal, post_step_tangent) = velocity_components(post_step, normal);

    ImpactEvent {
        impact_index: input.impact_index,
        time_s: input.time_s,
        x_m: input.post_step_state.position_m.x,
        y_m: input.post_step_state.position_m.y,
        z_m: input.post_step_state.position_m.z,
        terrain_normal_x: normal.x,
        terrain_normal_y: normal.y,
        terrain_normal_z: normal.z,
        effective_normal_x: effective_normal.x,
        effective_normal_y: effective_normal.y,
        effective_normal_z: effective_normal.z,
        incoming_vx_mps: incoming.x,
        incoming_vy_mps: incoming.y,
        incoming_vz_mps: incoming.z,
        post_contact_vx_mps: post_contact.x,
        post_contact_vy_mps: post_contact.y,
        post_contact_vz_mps: post_contact.z,
        post_scarring_vx_mps: post_scarring.x,
        post_scarring_vy_mps: post_scarring.y,
        post_scarring_vz_mps: post_scarring.z,
        post_step_vx_mps: post_step.x,
        post_step_vy_mps: post_step.y,
        post_step_vz_mps: post_step.z,
        impact_angle_deg: impact_angle_deg(incoming, normal),
        incoming_normal_speed_mps: incoming_normal,
        incoming_tangent_speed_mps: incoming_tangent,
        post_contact_normal_speed_mps: post_contact_normal,
        post_contact_tangent_speed_mps: post_contact_tangent,
        post_scarring_normal_speed_mps: post_scarring_normal,
        post_scarring_tangent_speed_mps: post_scarring_tangent,
        post_step_normal_speed_mps: post_step_normal,
        post_step_tangent_speed_mps: post_step_tangent,
        pre_contact_translational_j: pre_energy.translational_j,
        pre_contact_rotational_j: pre_energy.rotational_j,
        post_contact_translational_j: post_contact_energy.translational_j,
        post_contact_rotational_j: post_contact_energy.rotational_j,
        post_scarring_translational_j: post_scarring_energy.translational_j,
        post_scarring_rotational_j: post_scarring_energy.rotational_j,
        post_step_translational_j: post_step_energy.translational_j,
        post_step_rotational_j: post_step_energy.rotational_j,
        scarring_depth_m: input.scarring.scarring_depth_m,
        scarring_area_m2: input.scarring.scarring_area_m2,
        scarring_drag_force_n: input.scarring.scarring_drag_force_n,
        scarring_uncapped_energy_loss_j: input.scarring.scarring_uncapped_energy_loss_j,
        scarring_capped_energy_loss_j: input.scarring.scarring_energy_loss_j,
        scarring_depth_source: input.scarring.scarring_depth_source,
        cumulative_scarring_energy_loss_j: input.cumulative_scarring_energy_loss_j,
    }
}

fn velocity_components(velocity: crate::Vec3, normal: crate::Vec3) -> (f64, f64) {
    let normal_component = velocity.dot(&normal);
    let tangent = velocity - normal_component * normal;
    (normal_component.abs(), tangent.norm())
}

fn impact_angle_deg(incoming_velocity: crate::Vec3, normal: crate::Vec3) -> f64 {
    let speed = incoming_velocity.norm();
    if speed <= 0.0 {
        return 0.0;
    }
    let cos_angle = (-incoming_velocity / speed).dot(&normal).clamp(-1.0, 1.0);
    cos_angle.acos().to_degrees()
}

fn unit_or(vector: crate::Vec3, fallback: crate::Vec3) -> crate::Vec3 {
    vector
        .try_normalize(crate::EPS)
        .or_else(|| fallback.try_normalize(crate::EPS))
        .unwrap_or_else(|| crate::Vec3::new(0.0, 0.0, 1.0))
}
