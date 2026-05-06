//! Independent, literature-based research core for simple 3D rockfall simulation.
//!
//! This crate does not contain RAMMS::ROCKFALL code and does not attempt to
//! reproduce proprietary implementations. The current model is a deliberately
//! small spherical-block simulator intended for analytic validation and future
//! extension. New physics features are opt-in and versioned.

pub mod dynamics;
pub mod geodata;
pub mod geometry;
pub mod integrator;
pub mod io;
pub mod manifest;
pub mod probabilistic;
pub mod shape;
pub mod simulation;
pub mod state;
pub mod stochastic;
pub mod terrain;
pub mod validation;

pub use dynamics::{
    ContactModel, ContactParameterProvider, ContactParameters, ScarringDepthSource,
    ScarringDiagnostics, ScarringSettings, SoilInteractionModel,
};
pub use geometry::SphereBlock;
pub use shape::{
    select_box_support_point, shape_contact_v0_energy_diagnostic, BlockShapeMetadata,
    BlockShapeType, MassPropertyModel, ShapeContactV0EnergyDiagnostic, ShapeContactV0Scaffold,
    ShapeContactV0SupportDiagnostic, ShapeDimensions, ShapeMassProperties, ShapeOrientation,
    ShapeProvenance, SHAPE_CONTACT_V0_ACTIVE_SHAPE, SHAPE_CONTACT_V0_MODEL,
    SHAPE_METADATA_SCHEMA_VERSION,
};
pub use simulation::{
    simulate_ensemble, simulate_ensemble_with_contact_parameters, simulate_one_trajectory,
    simulate_one_trajectory_with_terrain,
    simulate_one_trajectory_with_terrain_and_contact_parameters, EnsembleResult, SimulationConfig,
    SimulationResult, TerrainConfig, TrajectoryRequest, TrajectoryRun, TrajectorySummary,
};
pub use state::{
    BodyState, ContactState, ImpactEvent, ImpactStageEnergy, TrajectoryDiagnostics,
    TrajectorySample,
};
pub use stochastic::{ContactRoughness, RoughnessModel};

/// Three-dimensional vector type used throughout the crate.
pub type Vec3 = nalgebra::Vector3<f64>;

/// Scalar tolerance used for geometric safety checks.
pub const EPS: f64 = 1.0e-10;
