//! Independent, literature-based research core for simple 3D rockfall simulation.
//!
//! This crate does not contain RAMMS::ROCKFALL code and does not attempt to
//! reproduce proprietary implementations. The current model is a deliberately
//! small spherical-block simulator intended for analytic validation and future
//! extension.

pub mod dynamics;
pub mod geometry;
pub mod integrator;
pub mod io;
pub mod simulation;
pub mod state;
pub mod stochastic;
pub mod terrain;
pub mod validation;

pub use dynamics::ContactModel;
pub use geometry::SphereBlock;
pub use simulation::{
    simulate_ensemble, simulate_one_trajectory, simulate_one_trajectory_with_terrain,
    EnsembleResult, SimulationConfig, SimulationResult, TerrainConfig, TrajectoryRequest,
    TrajectoryRun, TrajectorySummary,
};
pub use state::{BodyState, ContactState, TrajectorySample};

/// Three-dimensional vector type used throughout the crate.
pub type Vec3 = nalgebra::Vector3<f64>;

/// Scalar tolerance used for geometric safety checks.
pub const EPS: f64 = 1.0e-10;
