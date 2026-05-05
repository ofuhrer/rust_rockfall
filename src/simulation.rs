use crate::{
    geometry::SphereBlock,
    integrator::{simulate_fixed_step, IntegratorSettings},
    state::{BodyState, TrajectorySample},
    stochastic::{sample_release, ReleasePerturbation},
    terrain::{
        ChannelizedGully, DemGrid, GaussianBump, Paraboloid, Plane, SinusoidalRoughSlope,
        StepTerrain, TerracedSlope, Terrain, TerrainError, VShapedValley,
    },
    Vec3,
};
use serde::{Deserialize, Serialize};
use thiserror::Error;

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct SimulationConfig {
    pub block: SphereBlock,
    pub initial_position_m: [f64; 3],
    pub initial_velocity_mps: [f64; 3],
    #[serde(default)]
    pub initial_angular_velocity_radps: [f64; 3],
    pub terrain: TerrainConfig,
    pub dt_s: f64,
    pub max_time_s: f64,
    #[serde(default = "default_gravity")]
    pub gravity_mps2: f64,
    #[serde(default = "default_normal_restitution")]
    pub normal_restitution: f64,
    #[serde(default = "default_tangential_restitution")]
    pub tangential_restitution: f64,
    #[serde(default = "default_friction")]
    pub friction_coefficient: f64,
    #[serde(default = "default_stop_speed")]
    pub stop_speed_mps: f64,
    #[serde(default)]
    pub random_seed: Option<u64>,
    #[serde(default)]
    pub release_perturbation: ReleasePerturbation,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(tag = "kind", rename_all = "snake_case")]
pub enum TerrainConfig {
    Plane {
        z0_m: f64,
        slope_x: f64,
        slope_y: f64,
    },
    Paraboloid {
        z0_m: f64,
        ax: f64,
        ay: f64,
    },
    Step {
        step_x_m: f64,
        high_z_m: f64,
        low_z_m: f64,
    },
    VShapedValley {
        z0_m: f64,
        slope_x: f64,
        side_slope_abs_y: f64,
    },
    TerracedSlope {
        z0_m: f64,
        slope_x: f64,
        terrace_width_m: f64,
        terrace_height_m: f64,
    },
    SinusoidalRoughSlope {
        z0_m: f64,
        slope_x: f64,
        amplitude_m: f64,
        wavelength_m: f64,
    },
    GaussianBump {
        z0_m: f64,
        slope_x: f64,
        center_x_m: f64,
        center_y_m: f64,
        height_m: f64,
        sigma_m: f64,
    },
    ChannelizedGully {
        z0_m: f64,
        slope_x: f64,
        depth_m: f64,
        width_m: f64,
    },
    EsriAsciiGrid {
        path: String,
    },
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct SimulationResult {
    pub samples: Vec<TrajectorySample>,
}

#[derive(Debug, Error)]
pub enum SimulationError {
    #[error("terrain error: {0}")]
    Terrain(#[from] TerrainError),
    #[error("configuration value must be positive: {0}")]
    NonPositive(&'static str),
}

impl SimulationConfig {
    pub fn initial_state(&self) -> BodyState {
        let state = BodyState {
            position_m: arr3(self.initial_position_m),
            velocity_mps: arr3(self.initial_velocity_mps),
            angular_velocity_radps: arr3(self.initial_angular_velocity_radps),
        };
        if let Some(seed) = self.random_seed {
            sample_release(state, self.release_perturbation, seed)
        } else {
            state
        }
    }

    pub fn run(&self) -> Result<SimulationResult, SimulationError> {
        self.validate()?;
        let terrain = self.terrain.build()?;
        let settings = IntegratorSettings {
            dt_s: self.dt_s,
            max_time_s: self.max_time_s,
            gravity_mps2: self.gravity_mps2,
            normal_restitution: self.normal_restitution,
            tangential_restitution: self.tangential_restitution,
            friction_coefficient: self.friction_coefficient,
            stop_speed_mps: self.stop_speed_mps,
        };
        Ok(SimulationResult {
            samples: simulate_fixed_step(
                self.initial_state(),
                self.block,
                terrain.as_ref(),
                settings,
            ),
        })
    }

    fn validate(&self) -> Result<(), SimulationError> {
        if self.block.radius_m <= 0.0 {
            return Err(SimulationError::NonPositive("block.radius_m"));
        }
        if self.block.mass_kg <= 0.0 {
            return Err(SimulationError::NonPositive("block.mass_kg"));
        }
        if self.dt_s <= 0.0 {
            return Err(SimulationError::NonPositive("dt_s"));
        }
        if self.max_time_s <= 0.0 {
            return Err(SimulationError::NonPositive("max_time_s"));
        }
        if self.gravity_mps2 <= 0.0 {
            return Err(SimulationError::NonPositive("gravity_mps2"));
        }
        Ok(())
    }
}

impl TerrainConfig {
    pub fn build(&self) -> Result<Box<dyn Terrain>, TerrainError> {
        match self {
            TerrainConfig::Plane {
                z0_m,
                slope_x,
                slope_y,
            } => Ok(Box::new(Plane {
                z0_m: *z0_m,
                slope_x: *slope_x,
                slope_y: *slope_y,
            })),
            TerrainConfig::Paraboloid { z0_m, ax, ay } => Ok(Box::new(Paraboloid {
                z0_m: *z0_m,
                ax: *ax,
                ay: *ay,
            })),
            TerrainConfig::Step {
                step_x_m,
                high_z_m,
                low_z_m,
            } => Ok(Box::new(StepTerrain {
                step_x_m: *step_x_m,
                high_z_m: *high_z_m,
                low_z_m: *low_z_m,
            })),
            TerrainConfig::VShapedValley {
                z0_m,
                slope_x,
                side_slope_abs_y,
            } => Ok(Box::new(VShapedValley {
                z0_m: *z0_m,
                slope_x: *slope_x,
                side_slope_abs_y: *side_slope_abs_y,
            })),
            TerrainConfig::TerracedSlope {
                z0_m,
                slope_x,
                terrace_width_m,
                terrace_height_m,
            } => Ok(Box::new(TerracedSlope {
                z0_m: *z0_m,
                slope_x: *slope_x,
                terrace_width_m: *terrace_width_m,
                terrace_height_m: *terrace_height_m,
            })),
            TerrainConfig::SinusoidalRoughSlope {
                z0_m,
                slope_x,
                amplitude_m,
                wavelength_m,
            } => Ok(Box::new(SinusoidalRoughSlope {
                z0_m: *z0_m,
                slope_x: *slope_x,
                amplitude_m: *amplitude_m,
                wavelength_m: *wavelength_m,
            })),
            TerrainConfig::GaussianBump {
                z0_m,
                slope_x,
                center_x_m,
                center_y_m,
                height_m,
                sigma_m,
            } => Ok(Box::new(GaussianBump {
                z0_m: *z0_m,
                slope_x: *slope_x,
                center_x_m: *center_x_m,
                center_y_m: *center_y_m,
                height_m: *height_m,
                sigma_m: *sigma_m,
            })),
            TerrainConfig::ChannelizedGully {
                z0_m,
                slope_x,
                depth_m,
                width_m,
            } => Ok(Box::new(ChannelizedGully {
                z0_m: *z0_m,
                slope_x: *slope_x,
                depth_m: *depth_m,
                width_m: *width_m,
            })),
            TerrainConfig::EsriAsciiGrid { path } => Ok(Box::new(DemGrid::from_ascii_grid(path)?)),
        }
    }
}

fn default_gravity() -> f64 {
    9.81
}

fn default_normal_restitution() -> f64 {
    0.25
}

fn default_tangential_restitution() -> f64 {
    0.85
}

fn default_friction() -> f64 {
    0.45
}

fn default_stop_speed() -> f64 {
    0.10
}

fn arr3(values: [f64; 3]) -> Vec3 {
    Vec3::new(values[0], values[1], values[2])
}
