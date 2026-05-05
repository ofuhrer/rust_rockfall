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

pub fn derive_trajectory_seed(global_seed: u64, case_id: &str, trajectory_id: &str) -> u64 {
    let mut hash = FNV_OFFSET_BASIS ^ global_seed;
    hash = fnv1a_update(hash, case_id.as_bytes());
    hash = fnv1a_update(hash, &[0xff]);
    fnv1a_update(hash, trajectory_id.as_bytes())
}

pub fn stable_hash64(bytes: &[u8]) -> u64 {
    fnv1a_update(FNV_OFFSET_BASIS, bytes)
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

const FNV_OFFSET_BASIS: u64 = 0xcbf2_9ce4_8422_2325;
const FNV_PRIME: u64 = 0x0000_0100_0000_01b3;

fn fnv1a_update(mut hash: u64, bytes: &[u8]) -> u64 {
    for byte in bytes {
        hash ^= u64::from(*byte);
        hash = hash.wrapping_mul(FNV_PRIME);
    }
    hash
}
