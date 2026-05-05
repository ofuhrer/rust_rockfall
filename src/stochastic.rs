use crate::{state::BodyState, Vec3};
use rand::{Rng, SeedableRng};
use rand_chacha::ChaCha8Rng;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq)]
pub struct ReleasePerturbation {
    pub position_uniform_m: f64,
    pub velocity_uniform_mps: f64,
}

impl Default for ReleasePerturbation {
    fn default() -> Self {
        Self {
            position_uniform_m: 0.0,
            velocity_uniform_mps: 0.0,
        }
    }
}

pub fn seeded_rng(seed: u64) -> ChaCha8Rng {
    ChaCha8Rng::seed_from_u64(seed)
}

pub fn sample_release(
    initial: BodyState,
    perturbation: ReleasePerturbation,
    seed: u64,
) -> BodyState {
    let mut rng = seeded_rng(seed);
    let mut sample_component = |half_width: f64| {
        if half_width <= 0.0 {
            0.0
        } else {
            rng.gen_range(-half_width..=half_width)
        }
    };

    BodyState {
        position_m: initial.position_m
            + Vec3::new(
                sample_component(perturbation.position_uniform_m),
                sample_component(perturbation.position_uniform_m),
                sample_component(perturbation.position_uniform_m),
            ),
        velocity_mps: initial.velocity_mps
            + Vec3::new(
                sample_component(perturbation.velocity_uniform_mps),
                sample_component(perturbation.velocity_uniform_mps),
                sample_component(perturbation.velocity_uniform_mps),
            ),
        angular_velocity_radps: initial.angular_velocity_radps,
    }
}
