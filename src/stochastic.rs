use crate::{state::BodyState, Vec3};
use rand::{Rng, SeedableRng};
use rand_chacha::ChaCha8Rng;
use serde::{Deserialize, Serialize};
use std::f64::consts::TAU;

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

#[derive(Debug, Default, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum RoughnessModel {
    #[default]
    None,
    StochasticContactV1,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq)]
pub struct ContactRoughness {
    #[serde(default)]
    pub roughness_model: RoughnessModel,
    #[serde(default)]
    pub roughness_std_normal: f64,
    #[serde(default)]
    pub roughness_std_tangent: f64,
    #[serde(default)]
    pub roughness_std_angle: f64,
}

impl Default for ContactRoughness {
    fn default() -> Self {
        Self {
            roughness_model: RoughnessModel::None,
            roughness_std_normal: 0.0,
            roughness_std_tangent: 0.0,
            roughness_std_angle: 0.0,
        }
    }
}

impl ContactRoughness {
    pub fn is_active(&self) -> bool {
        self.roughness_model == RoughnessModel::StochasticContactV1
            && (self.roughness_std_normal > 0.0
                || self.roughness_std_tangent > 0.0
                || self.roughness_std_angle > 0.0)
    }

    pub fn validate(&self) -> Result<(), &'static str> {
        if self.roughness_std_normal < 0.0 {
            return Err("roughness_std_normal");
        }
        if self.roughness_std_tangent < 0.0 {
            return Err("roughness_std_tangent");
        }
        if self.roughness_std_angle < 0.0 {
            return Err("roughness_std_angle");
        }
        Ok(())
    }
}

#[derive(Debug, Clone, Copy, PartialEq)]
pub struct EffectiveContactParameters {
    pub normal: Vec3,
    pub normal_restitution: f64,
    pub tangential_restitution: f64,
    pub friction_coefficient: f64,
}

pub fn sample_contact_roughness(
    base_normal: Vec3,
    normal_restitution: f64,
    tangential_restitution: f64,
    friction_coefficient: f64,
    roughness: ContactRoughness,
    rng: Option<&mut ChaCha8Rng>,
) -> EffectiveContactParameters {
    if !roughness.is_active() {
        return EffectiveContactParameters {
            normal: unit_or(base_normal, Vec3::new(0.0, 0.0, 1.0)),
            normal_restitution,
            tangential_restitution,
            friction_coefficient,
        };
    }

    let Some(rng) = rng else {
        return EffectiveContactParameters {
            normal: unit_or(base_normal, Vec3::new(0.0, 0.0, 1.0)),
            normal_restitution,
            tangential_restitution,
            friction_coefficient,
        };
    };

    let normal_noise = bounded_standard_normal(rng, roughness.roughness_std_normal);
    let tangent_noise = bounded_standard_normal(rng, roughness.roughness_std_tangent);
    let angle_a = bounded_standard_normal(rng, roughness.roughness_std_angle);
    let angle_b = bounded_standard_normal(rng, roughness.roughness_std_angle);
    let normal = perturb_normal(base_normal, angle_a, angle_b);

    EffectiveContactParameters {
        normal,
        normal_restitution: dissipative_scale(normal_restitution, normal_noise),
        tangential_restitution: dissipative_scale(tangential_restitution, tangent_noise),
        friction_coefficient: friction_coefficient.max(0.0) * (1.0 + tangent_noise.abs()),
    }
}

fn bounded_standard_normal(rng: &mut ChaCha8Rng, std: f64) -> f64 {
    if std <= 0.0 {
        return 0.0;
    }
    let u1 = rng.gen_range(f64::MIN_POSITIVE..1.0);
    let u2 = rng.gen_range(0.0..1.0);
    let z = (-2.0 * u1.ln()).sqrt() * (TAU * u2).cos();
    (z * std).clamp(-2.0 * std, 2.0 * std)
}

fn dissipative_scale(value: f64, noise: f64) -> f64 {
    value.clamp(0.0, 1.0) * (1.0 - noise.abs()).clamp(0.0, 1.0)
}

fn perturb_normal(base_normal: Vec3, angle_a: f64, angle_b: f64) -> Vec3 {
    let n = unit_or(base_normal, Vec3::new(0.0, 0.0, 1.0));
    if angle_a == 0.0 && angle_b == 0.0 {
        return n;
    }
    let reference = if n.z.abs() < 0.9 {
        Vec3::new(0.0, 0.0, 1.0)
    } else {
        Vec3::new(1.0, 0.0, 0.0)
    };
    let t1 = unit_or(n.cross(&reference), Vec3::new(1.0, 0.0, 0.0));
    let t2 = unit_or(n.cross(&t1), Vec3::new(0.0, 1.0, 0.0));
    unit_or(n + angle_a * t1 + angle_b * t2, n)
}

fn unit_or(vector: Vec3, fallback: Vec3) -> Vec3 {
    let norm = vector.norm();
    if norm > 0.0 {
        vector / norm
    } else {
        fallback
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
