//! Public namespace for validation domain types.
//!
//! This module provides a structured access path (`validation::types::*`) while
//! preserving the original `validation::*` API surface.

pub use super::{
    BenchmarkCase, BlockShapeConfig, CaseBlock, CaseParameters, CasePerturbation, CaseRandom,
    CaseRelease, CaseReport, CaseSimulation, CaseStatus, CaseTerrain, DepositionPoint,
    EnsembleDepositionPoint, EnsembleStopStateRow, ExecutionStatus, ExpectedConfig,
    GeneratedReleasePointRecord, ImpactTerrainMaterialRow, ObservationConfig, ObservedContactEvent,
    ObservedTrajectorySample, OutputConfig, ProbabilisticMetadataConfig, ReferenceConfig,
    ReleasePoint, ReleaseZoneConfig, ScientificStatus, TerrainClassConfig,
    TerrainMaterialExposureRow, TrajectoryMetadataRow, ValidationError, ValidationScope,
};
pub use crate::manifest::ValidationOutputMode;
