use serde::{Deserialize, Serialize};

/// Spherical block used by the v0 computational model.
#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq)]
pub struct SphereBlock {
    pub radius_m: f64,
    pub mass_kg: f64,
}

impl SphereBlock {
    pub fn new(radius_m: f64, mass_kg: f64) -> Self {
        Self { radius_m, mass_kg }
    }

    pub fn moment_of_inertia_kg_m2(&self) -> f64 {
        0.4 * self.mass_kg * self.radius_m * self.radius_m
    }
}

/// Future non-spherical block families. They are documented now so public APIs can
/// refer to the intended progression without pretending v0 implements them.
#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
pub enum ShapePlaceholder {
    Ellipsoid,
    ConvexPolyhedron,
}
