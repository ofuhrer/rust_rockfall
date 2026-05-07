//! Lightweight Swiss geodata metadata for pilot DEM and source-area ingestion.

use crate::{
    dynamics::{ContactParameterProvider, ContactParameters, ScarringSettings},
    terrain::DemGrid,
};
use serde::{Deserialize, Serialize};
use std::{
    collections::{BTreeMap, BTreeSet},
    fs,
    path::{Path, PathBuf},
};
use thiserror::Error;

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct TerrainSourceMetadata {
    pub schema_version: u32,
    pub tile_id: String,
    pub source_dataset: String,
    pub source_product: String,
    #[serde(default)]
    pub source_url: Option<String>,
    pub source_filename: String,
    #[serde(default)]
    pub source_file_present: bool,
    pub download_status: String,
    pub license: String,
    pub coordinate_reference_system: CoordinateReferenceSystemMetadata,
    pub raster: RasterMetadata,
    pub extent_lv95_m: ExtentMetadata,
    pub preprocessing: PreprocessingMetadata,
    pub provenance: ProvenanceMetadata,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ReleaseZoneMetadata {
    pub schema_version: u32,
    pub zone_id: String,
    #[serde(default)]
    pub title: Option<String>,
    pub source_dataset: String,
    #[serde(default)]
    pub source_url: Option<String>,
    pub license: String,
    pub coordinate_reference_system: CoordinateReferenceSystemMetadata,
    pub geometry: ReleaseZoneGeometry,
    pub sampling: ReleaseZoneSamplingMetadata,
    pub provenance: ProvenanceMetadata,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct TerrainClassMetadata {
    pub schema_version: u32,
    pub layer_id: String,
    pub source_dataset: String,
    #[serde(default)]
    pub source_url: Option<String>,
    pub license: String,
    pub coordinate_reference_system: CoordinateReferenceSystemMetadata,
    pub raster: RasterMetadata,
    pub extent_lv95_m: ExtentMetadata,
    pub class_grid_path: PathBuf,
    pub classes: Vec<TerrainClassDefinition>,
    pub provenance: ProvenanceMetadata,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct TerrainClassDefinition {
    pub id: i32,
    pub name: String,
    #[serde(default)]
    pub parameter_overrides: TerrainClassParameterOverrides,
}

#[derive(Debug, Clone, Default, Serialize, Deserialize, PartialEq)]
pub struct TerrainClassParameterOverrides {
    #[serde(default)]
    pub restitution_n: Option<f64>,
    #[serde(default)]
    pub restitution_t: Option<f64>,
    #[serde(default)]
    pub friction_mu: Option<f64>,
    #[serde(default)]
    pub rolling_resistance: Option<f64>,
    #[serde(default)]
    pub soil_strength_pa: Option<f64>,
    #[serde(default)]
    pub scarring_drag_coefficient: Option<f64>,
    #[serde(default)]
    pub scarring_layer_density_kgpm3: Option<f64>,
    #[serde(default)]
    pub scarring_max_depth_m: Option<f64>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct TerrainClassGrid {
    pub ncols: usize,
    pub nrows: usize,
    pub xllcorner_m: f64,
    pub yllcorner_m: f64,
    pub cellsize_m: f64,
    pub nodata_value: i32,
    pub values: Vec<i32>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct TerrainClassMap {
    pub metadata: TerrainClassMetadata,
    pub grid: TerrainClassGrid,
    pub classes_by_id: BTreeMap<i32, TerrainClassDefinition>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct TerrainClassCoverage {
    pub class_id: i32,
    pub name: String,
    pub cell_count: usize,
    pub coverage_fraction: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ReleaseZoneGeometry {
    #[serde(rename = "type")]
    pub geometry_type: String,
    pub coordinates: Vec<[f64; 2]>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ReleaseZoneSamplingMetadata {
    pub mode: String,
    pub count: usize,
    pub seed: u64,
    #[serde(default)]
    pub initial_velocity_mps: [f64; 3],
    #[serde(default)]
    pub z_offset_m: f64,
    #[serde(default = "default_release_point_id_prefix")]
    pub point_id_prefix: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct GeneratedReleasePoint {
    pub release_id: String,
    pub x_m: f64,
    pub y_m: f64,
    pub vx_mps: f64,
    pub vy_mps: f64,
    pub vz_mps: f64,
    pub z_offset_m: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct CoordinateReferenceSystemMetadata {
    pub epsg: u32,
    pub horizontal_name: String,
    pub vertical_datum: String,
    pub coordinate_unit: String,
    pub height_unit: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct RasterMetadata {
    pub format: String,
    pub resolution_m: f64,
    pub width_px: usize,
    pub height_px: usize,
    pub nodata: Option<f64>,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq)]
pub struct ExtentMetadata {
    pub xmin: f64,
    pub ymin: f64,
    pub xmax: f64,
    pub ymax: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct PreprocessingMetadata {
    pub status: String,
    #[serde(default)]
    pub crop_extent_lv95_m: Option<ExtentMetadata>,
    pub resampling_method: String,
    #[serde(default)]
    pub raw_sha256: Option<String>,
    #[serde(default)]
    pub processed_sha256: Option<String>,
    #[serde(default)]
    pub tool: Option<String>,
    #[serde(default)]
    pub processed_utc: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ProvenanceMetadata {
    pub intended_use: String,
    #[serde(default)]
    pub notes: Vec<String>,
}

#[derive(Debug, Error)]
pub enum GeodataError {
    #[error("failed to read terrain metadata: {0}")]
    Read(#[from] std::io::Error),
    #[error("failed to parse terrain metadata YAML: {0}")]
    Yaml(#[from] serde_yaml::Error),
    #[error("terrain metadata field {field} is invalid: {reason}")]
    Invalid { field: &'static str, reason: String },
}

impl TerrainSourceMetadata {
    pub fn from_yaml_file(path: impl AsRef<Path>) -> Result<Self, GeodataError> {
        let text = fs::read_to_string(path)?;
        Self::from_yaml_str(&text)
    }

    pub fn from_yaml_str(text: &str) -> Result<Self, GeodataError> {
        let metadata: Self = serde_yaml::from_str(text)?;
        metadata.validate()?;
        Ok(metadata)
    }

    pub fn validate(&self) -> Result<(), GeodataError> {
        ensure(self.schema_version == 1, "schema_version", "expected 1")?;
        ensure(!self.tile_id.trim().is_empty(), "tile_id", "must be set")?;
        ensure(
            self.source_dataset == "swisstopo_swissalti3d",
            "source_dataset",
            "minimal pilot currently supports only swisstopo_swissalti3d",
        )?;
        ensure(
            !self.source_product.trim().is_empty(),
            "source_product",
            "must be set",
        )?;
        ensure(
            !self.source_filename.trim().is_empty(),
            "source_filename",
            "must be set",
        )?;
        ensure(!self.license.trim().is_empty(), "license", "must be set")?;
        ensure(
            self.coordinate_reference_system.epsg == 2056,
            "coordinate_reference_system.epsg",
            "Swiss pilot terrain must use EPSG:2056 / LV95",
        )?;
        ensure(
            self.coordinate_reference_system.vertical_datum == "LN02",
            "coordinate_reference_system.vertical_datum",
            "Swiss pilot terrain must use LN02 heights",
        )?;
        ensure(
            self.coordinate_reference_system.coordinate_unit == "m",
            "coordinate_reference_system.coordinate_unit",
            "must be metres",
        )?;
        ensure(
            self.coordinate_reference_system.height_unit == "m",
            "coordinate_reference_system.height_unit",
            "must be metres",
        )?;
        ensure(
            self.raster.resolution_m.is_finite() && self.raster.resolution_m > 0.0,
            "raster.resolution_m",
            "must be finite and positive",
        )?;
        ensure(
            self.raster.width_px >= 2,
            "raster.width_px",
            "must be at least 2",
        )?;
        ensure(
            self.raster.height_px >= 2,
            "raster.height_px",
            "must be at least 2",
        )?;
        ensure(
            self.extent_lv95_m.xmax > self.extent_lv95_m.xmin,
            "extent_lv95_m.xmax",
            "must be greater than xmin",
        )?;
        ensure(
            self.extent_lv95_m.ymax > self.extent_lv95_m.ymin,
            "extent_lv95_m.ymax",
            "must be greater than ymin",
        )?;
        let expected_width_m = self.raster.width_px as f64 * self.raster.resolution_m;
        let expected_height_m = self.raster.height_px as f64 * self.raster.resolution_m;
        ensure_close(
            self.extent_lv95_m.xmax - self.extent_lv95_m.xmin,
            expected_width_m,
            "extent_lv95_m",
            "x extent must match raster width and resolution",
        )?;
        ensure_close(
            self.extent_lv95_m.ymax - self.extent_lv95_m.ymin,
            expected_height_m,
            "extent_lv95_m",
            "y extent must match raster height and resolution",
        )?;
        ensure(
            !self.preprocessing.status.trim().is_empty(),
            "preprocessing.status",
            "must be set",
        )?;
        ensure(
            !self.preprocessing.resampling_method.trim().is_empty(),
            "preprocessing.resampling_method",
            "must be set",
        )?;
        ensure(
            !self.provenance.intended_use.trim().is_empty(),
            "provenance.intended_use",
            "must be set",
        )?;
        Ok(())
    }

    pub fn validate_against_dem(&self, dem: &DemGrid) -> Result<(), GeodataError> {
        ensure(
            self.raster.width_px == dem.ncols,
            "raster.width_px",
            format!(
                "metadata has {}, DEM has {}",
                self.raster.width_px, dem.ncols
            ),
        )?;
        ensure(
            self.raster.height_px == dem.nrows,
            "raster.height_px",
            format!(
                "metadata has {}, DEM has {}",
                self.raster.height_px, dem.nrows
            ),
        )?;
        ensure_close(
            self.raster.resolution_m,
            dem.cellsize_m,
            "raster.resolution_m",
            "metadata resolution must match DEM cellsize",
        )?;
        if let Some(nodata) = self.raster.nodata {
            ensure_close(
                nodata,
                dem.nodata_value,
                "raster.nodata",
                "metadata nodata must match DEM NODATA_value",
            )?;
        }
        ensure_close(
            self.extent_lv95_m.xmin,
            dem.xllcorner_m,
            "extent_lv95_m.xmin",
            "metadata xmin must match DEM xllcorner",
        )?;
        ensure_close(
            self.extent_lv95_m.ymin,
            dem.yllcorner_m,
            "extent_lv95_m.ymin",
            "metadata ymin must match DEM yllcorner",
        )?;
        ensure_close(
            self.extent_lv95_m.xmax,
            dem.xllcorner_m + dem.ncols as f64 * dem.cellsize_m,
            "extent_lv95_m.xmax",
            "metadata xmax must match DEM footprint",
        )?;
        ensure_close(
            self.extent_lv95_m.ymax,
            dem.yllcorner_m + dem.nrows as f64 * dem.cellsize_m,
            "extent_lv95_m.ymax",
            "metadata ymax must match DEM footprint",
        )?;
        Ok(())
    }
}

impl ReleaseZoneMetadata {
    pub fn from_yaml_file(path: impl AsRef<Path>) -> Result<Self, GeodataError> {
        let text = fs::read_to_string(path)?;
        Self::from_yaml_str(&text)
    }

    pub fn from_yaml_str(text: &str) -> Result<Self, GeodataError> {
        let metadata: Self = serde_yaml::from_str(text)?;
        metadata.validate()?;
        Ok(metadata)
    }

    pub fn validate(&self) -> Result<(), GeodataError> {
        ensure(self.schema_version == 1, "schema_version", "expected 1")?;
        ensure(!self.zone_id.trim().is_empty(), "zone_id", "must be set")?;
        ensure(
            !self.source_dataset.trim().is_empty(),
            "source_dataset",
            "must be set",
        )?;
        ensure(!self.license.trim().is_empty(), "license", "must be set")?;
        validate_swiss_crs(&self.coordinate_reference_system)?;
        ensure(
            self.geometry.geometry_type == "polygon",
            "geometry.type",
            "minimal release-zone pilot supports only polygon geometry",
        )?;
        ensure(
            self.geometry.coordinates.len() >= 3,
            "geometry.coordinates",
            "polygon must have at least three vertices",
        )?;
        for point in &self.geometry.coordinates {
            ensure(
                point[0].is_finite() && point[1].is_finite(),
                "geometry.coordinates",
                "all coordinates must be finite",
            )?;
        }
        ensure(
            polygon_area_m2(&self.geometry.coordinates).abs() > 1.0e-9,
            "geometry.coordinates",
            "polygon area must be positive",
        )?;
        ensure(
            self.sampling.mode == "deterministic_grid",
            "sampling.mode",
            "minimal release-zone pilot supports only deterministic_grid",
        )?;
        ensure(
            self.sampling.count > 0,
            "sampling.count",
            "must be greater than zero",
        )?;
        ensure(
            self.sampling.z_offset_m.is_finite() && self.sampling.z_offset_m >= 0.0,
            "sampling.z_offset_m",
            "must be finite and nonnegative",
        )?;
        ensure(
            !self.sampling.point_id_prefix.trim().is_empty(),
            "sampling.point_id_prefix",
            "must be set",
        )?;
        ensure(
            !self.provenance.intended_use.trim().is_empty(),
            "provenance.intended_use",
            "must be set",
        )?;
        Ok(())
    }

    pub fn validate_against_terrain_source(
        &self,
        terrain: &TerrainSourceMetadata,
    ) -> Result<(), GeodataError> {
        ensure(
            self.coordinate_reference_system.epsg == terrain.coordinate_reference_system.epsg,
            "coordinate_reference_system.epsg",
            "release-zone CRS must match terrain-source CRS",
        )?;
        ensure(
            self.coordinate_reference_system.vertical_datum
                == terrain.coordinate_reference_system.vertical_datum,
            "coordinate_reference_system.vertical_datum",
            "release-zone vertical datum must match terrain-source vertical datum",
        )?;
        let extent = self.extent();
        ensure(
            extent.xmin >= terrain.extent_lv95_m.xmin
                && extent.xmax <= terrain.extent_lv95_m.xmax
                && extent.ymin >= terrain.extent_lv95_m.ymin
                && extent.ymax <= terrain.extent_lv95_m.ymax,
            "geometry.coordinates",
            "release-zone polygon extent must lie inside the pilot DEM footprint",
        )?;
        Ok(())
    }

    pub fn extent(&self) -> ExtentMetadata {
        let mut xmin = f64::INFINITY;
        let mut ymin = f64::INFINITY;
        let mut xmax = f64::NEG_INFINITY;
        let mut ymax = f64::NEG_INFINITY;
        for point in &self.geometry.coordinates {
            xmin = xmin.min(point[0]);
            ymin = ymin.min(point[1]);
            xmax = xmax.max(point[0]);
            ymax = ymax.max(point[1]);
        }
        ExtentMetadata {
            xmin,
            ymin,
            xmax,
            ymax,
        }
    }

    pub fn area_m2(&self) -> f64 {
        polygon_area_m2(&self.geometry.coordinates).abs()
    }

    pub fn sample_points(&self) -> Result<Vec<GeneratedReleasePoint>, GeodataError> {
        self.validate()?;
        let extent = self.extent();
        let mut divisions = (self.sampling.count as f64).sqrt().ceil().max(1.0) as usize;
        let mut candidates = Vec::new();
        while candidates.len() < self.sampling.count && divisions <= 512 {
            candidates.clear();
            let dx = (extent.xmax - extent.xmin) / divisions as f64;
            let dy = (extent.ymax - extent.ymin) / divisions as f64;
            for iy in 0..divisions {
                for ix in 0..divisions {
                    let x = extent.xmin + (ix as f64 + 0.5) * dx;
                    let y = extent.ymin + (iy as f64 + 0.5) * dy;
                    if point_in_polygon([x, y], &self.geometry.coordinates) {
                        candidates.push([x, y]);
                    }
                }
            }
            divisions *= 2;
        }
        ensure(
            candidates.len() >= self.sampling.count,
            "sampling.count",
            "could not generate enough deterministic grid points inside polygon",
        )?;

        let offset = if candidates.is_empty() {
            0
        } else {
            (self.sampling.seed as usize) % candidates.len()
        };
        let mut points = Vec::with_capacity(self.sampling.count);
        for index in 0..self.sampling.count {
            let candidate = candidates[(offset + index) % candidates.len()];
            points.push(GeneratedReleasePoint {
                release_id: format!("{}_{index:04}", self.sampling.point_id_prefix),
                x_m: candidate[0],
                y_m: candidate[1],
                vx_mps: self.sampling.initial_velocity_mps[0],
                vy_mps: self.sampling.initial_velocity_mps[1],
                vz_mps: self.sampling.initial_velocity_mps[2],
                z_offset_m: self.sampling.z_offset_m,
            });
        }
        Ok(points)
    }
}

impl TerrainClassMetadata {
    pub fn from_yaml_file(path: impl AsRef<Path>) -> Result<Self, GeodataError> {
        let text = fs::read_to_string(path)?;
        Self::from_yaml_str(&text)
    }

    pub fn from_yaml_str(text: &str) -> Result<Self, GeodataError> {
        let metadata: Self = serde_yaml::from_str(text)?;
        metadata.validate()?;
        Ok(metadata)
    }

    pub fn validate(&self) -> Result<(), GeodataError> {
        ensure(self.schema_version == 1, "schema_version", "expected 1")?;
        ensure(!self.layer_id.trim().is_empty(), "layer_id", "must be set")?;
        ensure(
            !self.source_dataset.trim().is_empty(),
            "source_dataset",
            "must be set",
        )?;
        ensure(!self.license.trim().is_empty(), "license", "must be set")?;
        validate_swiss_crs(&self.coordinate_reference_system)?;
        ensure(
            self.raster.resolution_m.is_finite() && self.raster.resolution_m > 0.0,
            "raster.resolution_m",
            "must be finite and positive",
        )?;
        ensure(
            self.raster.width_px >= 1,
            "raster.width_px",
            "must be at least 1",
        )?;
        ensure(
            self.raster.height_px >= 1,
            "raster.height_px",
            "must be at least 1",
        )?;
        ensure(
            self.extent_lv95_m.xmax > self.extent_lv95_m.xmin,
            "extent_lv95_m.xmax",
            "must be greater than xmin",
        )?;
        ensure(
            self.extent_lv95_m.ymax > self.extent_lv95_m.ymin,
            "extent_lv95_m.ymax",
            "must be greater than ymin",
        )?;
        ensure_close(
            self.extent_lv95_m.xmax - self.extent_lv95_m.xmin,
            self.raster.width_px as f64 * self.raster.resolution_m,
            "extent_lv95_m",
            "x extent must match raster width and resolution",
        )?;
        ensure_close(
            self.extent_lv95_m.ymax - self.extent_lv95_m.ymin,
            self.raster.height_px as f64 * self.raster.resolution_m,
            "extent_lv95_m",
            "y extent must match raster height and resolution",
        )?;
        ensure(
            !self.class_grid_path.as_os_str().is_empty(),
            "class_grid_path",
            "must be set",
        )?;
        ensure(!self.classes.is_empty(), "classes", "must not be empty")?;
        let mut ids = BTreeSet::new();
        for class in &self.classes {
            ensure(
                ids.insert(class.id),
                "classes.id",
                "class ids must be unique",
            )?;
            ensure(!class.name.trim().is_empty(), "classes.name", "must be set")?;
            class.parameter_overrides.validate()?;
        }
        ensure(
            !self.provenance.intended_use.trim().is_empty(),
            "provenance.intended_use",
            "must be set",
        )?;
        Ok(())
    }

    pub fn validate_against_terrain_source(
        &self,
        terrain: &TerrainSourceMetadata,
    ) -> Result<(), GeodataError> {
        ensure(
            self.coordinate_reference_system.epsg == terrain.coordinate_reference_system.epsg,
            "coordinate_reference_system.epsg",
            "terrain-class CRS must match terrain-source CRS",
        )?;
        ensure(
            self.coordinate_reference_system.vertical_datum
                == terrain.coordinate_reference_system.vertical_datum,
            "coordinate_reference_system.vertical_datum",
            "terrain-class vertical datum must match terrain-source vertical datum",
        )?;
        ensure_close(
            self.raster.resolution_m,
            terrain.raster.resolution_m,
            "raster.resolution_m",
            "terrain-class resolution must match terrain-source resolution",
        )?;
        ensure(
            self.raster.width_px == terrain.raster.width_px,
            "raster.width_px",
            "terrain-class width must match terrain-source width",
        )?;
        ensure(
            self.raster.height_px == terrain.raster.height_px,
            "raster.height_px",
            "terrain-class height must match terrain-source height",
        )?;
        ensure_close(
            self.extent_lv95_m.xmin,
            terrain.extent_lv95_m.xmin,
            "extent_lv95_m.xmin",
            "terrain-class extent must match terrain-source extent",
        )?;
        ensure_close(
            self.extent_lv95_m.ymin,
            terrain.extent_lv95_m.ymin,
            "extent_lv95_m.ymin",
            "terrain-class extent must match terrain-source extent",
        )?;
        ensure_close(
            self.extent_lv95_m.xmax,
            terrain.extent_lv95_m.xmax,
            "extent_lv95_m.xmax",
            "terrain-class extent must match terrain-source extent",
        )?;
        ensure_close(
            self.extent_lv95_m.ymax,
            terrain.extent_lv95_m.ymax,
            "extent_lv95_m.ymax",
            "terrain-class extent must match terrain-source extent",
        )?;
        Ok(())
    }
}

impl TerrainClassParameterOverrides {
    pub fn validate(&self) -> Result<(), GeodataError> {
        validate_optional_unit_interval(self.restitution_n, "classes.restitution_n")?;
        validate_optional_unit_interval(self.restitution_t, "classes.restitution_t")?;
        validate_optional_nonnegative(self.friction_mu, "classes.friction_mu")?;
        validate_optional_nonnegative(self.rolling_resistance, "classes.rolling_resistance")?;
        validate_optional_nonnegative(self.soil_strength_pa, "classes.soil_strength_pa")?;
        validate_optional_nonnegative(
            self.scarring_drag_coefficient,
            "classes.scarring_drag_coefficient",
        )?;
        validate_optional_nonnegative(
            self.scarring_layer_density_kgpm3,
            "classes.scarring_layer_density_kgpm3",
        )?;
        validate_optional_nonnegative(self.scarring_max_depth_m, "classes.scarring_max_depth_m")?;
        Ok(())
    }

    pub fn active_field_names(&self) -> Vec<String> {
        let mut names = Vec::new();
        if self.restitution_n.is_some() {
            names.push("restitution_n".to_string());
        }
        if self.restitution_t.is_some() {
            names.push("restitution_t".to_string());
        }
        if self.friction_mu.is_some() {
            names.push("friction_mu".to_string());
        }
        if self.rolling_resistance.is_some() {
            names.push("rolling_resistance".to_string());
        }
        if self.soil_strength_pa.is_some() {
            names.push("soil_strength_pa".to_string());
        }
        if self.scarring_drag_coefficient.is_some() {
            names.push("scarring_drag_coefficient".to_string());
        }
        if self.scarring_layer_density_kgpm3.is_some() {
            names.push("scarring_layer_density_kgpm3".to_string());
        }
        if self.scarring_max_depth_m.is_some() {
            names.push("scarring_max_depth_m".to_string());
        }
        names
    }

    fn apply(&self, base: ContactParameters) -> ContactParameters {
        let mut scarring = ScarringSettings {
            soil_interaction_model: base.scarring.soil_interaction_model,
            soil_strength_pa: self
                .soil_strength_pa
                .unwrap_or(base.scarring.soil_strength_pa),
            scarring_drag_coefficient: self
                .scarring_drag_coefficient
                .unwrap_or(base.scarring.scarring_drag_coefficient),
            scarring_layer_density_kgpm3: self
                .scarring_layer_density_kgpm3
                .unwrap_or(base.scarring.scarring_layer_density_kgpm3),
            scarring_max_depth_m: self
                .scarring_max_depth_m
                .or(base.scarring.scarring_max_depth_m),
        };
        if scarring.validate().is_err() {
            scarring = base.scarring;
        }
        ContactParameters {
            normal_restitution: self.restitution_n.unwrap_or(base.normal_restitution),
            tangential_restitution: self.restitution_t.unwrap_or(base.tangential_restitution),
            friction_coefficient: self.friction_mu.unwrap_or(base.friction_coefficient),
            rolling_resistance_coefficient: self
                .rolling_resistance
                .unwrap_or(base.rolling_resistance_coefficient),
            scarring,
        }
    }
}

impl TerrainClassGrid {
    pub fn from_ascii_grid(path: impl AsRef<Path>) -> Result<Self, GeodataError> {
        let text = fs::read_to_string(path)?;
        Self::from_ascii_grid_str(&text)
    }

    pub fn from_ascii_grid_str(text: &str) -> Result<Self, GeodataError> {
        let dem = DemGrid::from_ascii_grid_str(text).map_err(|err| GeodataError::Invalid {
            field: "class_grid_path",
            reason: err.to_string(),
        })?;
        let nodata_value = checked_i32(dem.nodata_value, "NODATA_value")?;
        let values = dem
            .values_m
            .iter()
            .map(|value| checked_i32(*value, "class grid value"))
            .collect::<Result<Vec<_>, _>>()?;
        Ok(Self {
            ncols: dem.ncols,
            nrows: dem.nrows,
            xllcorner_m: dem.xllcorner_m,
            yllcorner_m: dem.yllcorner_m,
            cellsize_m: dem.cellsize_m,
            nodata_value,
            values,
        })
    }

    pub fn class_id_at(&self, x_m: f64, y_m: f64) -> Option<i32> {
        if x_m < self.xllcorner_m
            || y_m < self.yllcorner_m
            || x_m >= self.xllcorner_m + self.ncols as f64 * self.cellsize_m
            || y_m >= self.yllcorner_m + self.nrows as f64 * self.cellsize_m
        {
            return None;
        }
        let col = ((x_m - self.xllcorner_m) / self.cellsize_m)
            .floor()
            .clamp(0.0, (self.ncols - 1) as f64) as usize;
        let row_from_bottom = ((y_m - self.yllcorner_m) / self.cellsize_m)
            .floor()
            .clamp(0.0, (self.nrows - 1) as f64) as usize;
        let row_from_top = self.nrows - 1 - row_from_bottom;
        let value = self.values[row_from_top * self.ncols + col];
        (value != self.nodata_value).then_some(value)
    }
}

impl TerrainClassMap {
    pub fn from_metadata_file(path: impl AsRef<Path>) -> Result<Self, GeodataError> {
        let path = path.as_ref();
        let metadata = TerrainClassMetadata::from_yaml_file(path)?;
        let grid_path = if metadata.class_grid_path.is_absolute() {
            metadata.class_grid_path.clone()
        } else {
            path.parent()
                .unwrap_or_else(|| Path::new(""))
                .join(&metadata.class_grid_path)
        };
        let grid = TerrainClassGrid::from_ascii_grid(grid_path)?;
        Self::from_metadata_and_grid(metadata, grid)
    }

    pub fn from_metadata_and_grid(
        metadata: TerrainClassMetadata,
        grid: TerrainClassGrid,
    ) -> Result<Self, GeodataError> {
        metadata.validate()?;
        validate_class_grid_against_metadata(&grid, &metadata)?;
        let classes_by_id = metadata
            .classes
            .iter()
            .map(|class| (class.id, class.clone()))
            .collect::<BTreeMap<_, _>>();
        for class_id in grid.values.iter().copied() {
            if class_id == grid.nodata_value {
                continue;
            }
            ensure(
                classes_by_id.contains_key(&class_id),
                "class_grid",
                format!("unknown class id {class_id}"),
            )?;
        }
        Ok(Self {
            metadata,
            grid,
            classes_by_id,
        })
    }

    pub fn validate_against_terrain_source(
        &self,
        terrain: &TerrainSourceMetadata,
    ) -> Result<(), GeodataError> {
        self.metadata.validate_against_terrain_source(terrain)
    }

    pub fn class_id_at(&self, x_m: f64, y_m: f64) -> Option<i32> {
        self.grid.class_id_at(x_m, y_m)
    }

    pub fn coverage(&self) -> Vec<TerrainClassCoverage> {
        let valid_cell_count = self
            .grid
            .values
            .iter()
            .filter(|value| **value != self.grid.nodata_value)
            .count()
            .max(1);
        let mut counts: BTreeMap<i32, usize> = BTreeMap::new();
        for value in &self.grid.values {
            if *value != self.grid.nodata_value {
                *counts.entry(*value).or_default() += 1;
            }
        }
        counts
            .into_iter()
            .filter_map(|(class_id, cell_count)| {
                let class = self.classes_by_id.get(&class_id)?;
                Some(TerrainClassCoverage {
                    class_id,
                    name: class.name.clone(),
                    cell_count,
                    coverage_fraction: cell_count as f64 / valid_cell_count as f64,
                })
            })
            .collect()
    }
}

impl ContactParameterProvider for TerrainClassMap {
    fn parameters_at(&self, x_m: f64, y_m: f64, base: ContactParameters) -> ContactParameters {
        self.class_id_at(x_m, y_m)
            .and_then(|class_id| self.classes_by_id.get(&class_id))
            .map(|class| class.parameter_overrides.apply(base))
            .unwrap_or(base)
    }
}

fn validate_swiss_crs(crs: &CoordinateReferenceSystemMetadata) -> Result<(), GeodataError> {
    ensure(
        crs.epsg == 2056,
        "coordinate_reference_system.epsg",
        "Swiss pilot metadata must use EPSG:2056 / LV95",
    )?;
    ensure(
        crs.vertical_datum == "LN02",
        "coordinate_reference_system.vertical_datum",
        "Swiss pilot metadata must use LN02 heights",
    )?;
    ensure(
        crs.coordinate_unit == "m",
        "coordinate_reference_system.coordinate_unit",
        "must be metres",
    )?;
    ensure(
        crs.height_unit == "m",
        "coordinate_reference_system.height_unit",
        "must be metres",
    )?;
    Ok(())
}

fn ensure(
    condition: bool,
    field: &'static str,
    reason: impl Into<String>,
) -> Result<(), GeodataError> {
    if condition {
        Ok(())
    } else {
        Err(GeodataError::Invalid {
            field,
            reason: reason.into(),
        })
    }
}

fn default_release_point_id_prefix() -> String {
    "release".to_string()
}

fn polygon_area_m2(points: &[[f64; 2]]) -> f64 {
    if points.len() < 3 {
        return 0.0;
    }
    let mut area2 = 0.0;
    for index in 0..points.len() {
        let next = (index + 1) % points.len();
        area2 += points[index][0] * points[next][1] - points[next][0] * points[index][1];
    }
    0.5 * area2
}

fn point_in_polygon(point: [f64; 2], polygon: &[[f64; 2]]) -> bool {
    let mut inside = false;
    let mut previous = polygon.len() - 1;
    for current in 0..polygon.len() {
        let xi = polygon[current][0];
        let yi = polygon[current][1];
        let xj = polygon[previous][0];
        let yj = polygon[previous][1];
        let crosses = ((yi > point[1]) != (yj > point[1]))
            && (point[0] < (xj - xi) * (point[1] - yi) / (yj - yi) + xi);
        if crosses {
            inside = !inside;
        }
        previous = current;
    }
    inside
}

fn ensure_close(
    actual: f64,
    expected: f64,
    field: &'static str,
    reason: impl Into<String>,
) -> Result<(), GeodataError> {
    let tolerance = 1.0e-6 * expected.abs().max(1.0);
    ensure(
        actual.is_finite() && (actual - expected).abs() <= tolerance,
        field,
        format!("{}: actual {actual}, expected {expected}", reason.into()),
    )
}

fn validate_optional_unit_interval(
    value: Option<f64>,
    field: &'static str,
) -> Result<(), GeodataError> {
    if let Some(value) = value {
        ensure(
            value.is_finite() && (0.0..=1.0).contains(&value),
            field,
            "must be finite and in [0, 1]",
        )?;
    }
    Ok(())
}

fn validate_optional_nonnegative(
    value: Option<f64>,
    field: &'static str,
) -> Result<(), GeodataError> {
    if let Some(value) = value {
        ensure(
            value.is_finite() && value >= 0.0,
            field,
            "must be finite and nonnegative",
        )?;
    }
    Ok(())
}

fn checked_i32(value: f64, field: &'static str) -> Result<i32, GeodataError> {
    ensure(
        value.is_finite() && (value.round() - value).abs() <= 1.0e-9,
        field,
        "class grid values must be integer coded",
    )?;
    ensure(
        value >= i32::MIN as f64 && value <= i32::MAX as f64,
        field,
        "class grid value is outside i32 range",
    )?;
    Ok(value.round() as i32)
}

fn validate_class_grid_against_metadata(
    grid: &TerrainClassGrid,
    metadata: &TerrainClassMetadata,
) -> Result<(), GeodataError> {
    ensure(
        grid.ncols == metadata.raster.width_px,
        "raster.width_px",
        "terrain-class grid width must match metadata",
    )?;
    ensure(
        grid.nrows == metadata.raster.height_px,
        "raster.height_px",
        "terrain-class grid height must match metadata",
    )?;
    ensure_close(
        grid.cellsize_m,
        metadata.raster.resolution_m,
        "raster.resolution_m",
        "terrain-class grid cellsize must match metadata",
    )?;
    if let Some(nodata) = metadata.raster.nodata {
        ensure(
            checked_i32(nodata, "raster.nodata")? == grid.nodata_value,
            "raster.nodata",
            "terrain-class grid nodata must match metadata",
        )?;
    }
    ensure_close(
        grid.xllcorner_m,
        metadata.extent_lv95_m.xmin,
        "extent_lv95_m.xmin",
        "terrain-class grid xllcorner must match metadata",
    )?;
    ensure_close(
        grid.yllcorner_m,
        metadata.extent_lv95_m.ymin,
        "extent_lv95_m.ymin",
        "terrain-class grid yllcorner must match metadata",
    )?;
    Ok(())
}
