use crate::{Vec3, EPS};
use serde::{Deserialize, Serialize};
use std::{fs, path::Path};
use thiserror::Error;

pub trait Terrain: Send + Sync {
    fn height(&self, x_m: f64, y_m: f64) -> f64;

    fn normal(&self, x_m: f64, y_m: f64) -> Vec3;

    fn signed_distance_sphere(&self, center_m: Vec3, radius_m: f64) -> f64 {
        let ground = self.height(center_m.x, center_m.y);
        let n = self.normal(center_m.x, center_m.y);
        let point_on_surface = Vec3::new(center_m.x, center_m.y, ground);
        (center_m - point_on_surface).dot(&n) - radius_m
    }
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq)]
pub struct Plane {
    pub z0_m: f64,
    pub slope_x: f64,
    pub slope_y: f64,
}

impl Plane {
    pub fn horizontal(z0_m: f64) -> Self {
        Self {
            z0_m,
            slope_x: 0.0,
            slope_y: 0.0,
        }
    }
}

impl Terrain for Plane {
    fn height(&self, x_m: f64, y_m: f64) -> f64 {
        self.z0_m + self.slope_x * x_m + self.slope_y * y_m
    }

    fn normal(&self, _x_m: f64, _y_m: f64) -> Vec3 {
        Vec3::new(-self.slope_x, -self.slope_y, 1.0).normalize()
    }
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq)]
pub struct Paraboloid {
    pub z0_m: f64,
    pub ax: f64,
    pub ay: f64,
}

impl Terrain for Paraboloid {
    fn height(&self, x_m: f64, y_m: f64) -> f64 {
        self.z0_m + self.ax * x_m * x_m + self.ay * y_m * y_m
    }

    fn normal(&self, x_m: f64, y_m: f64) -> Vec3 {
        Vec3::new(-2.0 * self.ax * x_m, -2.0 * self.ay * y_m, 1.0).normalize()
    }
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq)]
pub struct StepTerrain {
    pub step_x_m: f64,
    pub high_z_m: f64,
    pub low_z_m: f64,
}

impl Terrain for StepTerrain {
    fn height(&self, x_m: f64, _y_m: f64) -> f64 {
        if x_m < self.step_x_m {
            self.high_z_m
        } else {
            self.low_z_m
        }
    }

    fn normal(&self, _x_m: f64, _y_m: f64) -> Vec3 {
        Vec3::new(0.0, 0.0, 1.0)
    }
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq)]
pub struct VShapedValley {
    pub z0_m: f64,
    pub slope_x: f64,
    pub side_slope_abs_y: f64,
}

impl Terrain for VShapedValley {
    fn height(&self, x_m: f64, y_m: f64) -> f64 {
        self.z0_m + self.slope_x * x_m + self.side_slope_abs_y * y_m.abs()
    }

    fn normal(&self, _x_m: f64, y_m: f64) -> Vec3 {
        let dy = if y_m > 0.0 {
            self.side_slope_abs_y
        } else if y_m < 0.0 {
            -self.side_slope_abs_y
        } else {
            0.0
        };
        Vec3::new(-self.slope_x, -dy, 1.0).normalize()
    }
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq)]
pub struct TerracedSlope {
    pub z0_m: f64,
    pub slope_x: f64,
    pub terrace_width_m: f64,
    pub terrace_height_m: f64,
}

impl Terrain for TerracedSlope {
    fn height(&self, x_m: f64, _y_m: f64) -> f64 {
        let terrace_index = (x_m / self.terrace_width_m.max(EPS)).floor();
        self.z0_m + self.slope_x * x_m + terrace_index * self.terrace_height_m
    }

    fn normal(&self, _x_m: f64, _y_m: f64) -> Vec3 {
        Vec3::new(-self.slope_x, 0.0, 1.0).normalize()
    }
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq)]
pub struct SinusoidalRoughSlope {
    pub z0_m: f64,
    pub slope_x: f64,
    pub amplitude_m: f64,
    pub wavelength_m: f64,
}

impl Terrain for SinusoidalRoughSlope {
    fn height(&self, x_m: f64, _y_m: f64) -> f64 {
        let k = std::f64::consts::TAU / self.wavelength_m.max(EPS);
        self.z0_m + self.slope_x * x_m + self.amplitude_m * (k * x_m).sin()
    }

    fn normal(&self, x_m: f64, _y_m: f64) -> Vec3 {
        let k = std::f64::consts::TAU / self.wavelength_m.max(EPS);
        let dzdx = self.slope_x + self.amplitude_m * k * (k * x_m).cos();
        Vec3::new(-dzdx, 0.0, 1.0).normalize()
    }
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq)]
pub struct GaussianBump {
    pub z0_m: f64,
    pub slope_x: f64,
    pub center_x_m: f64,
    pub center_y_m: f64,
    pub height_m: f64,
    pub sigma_m: f64,
}

impl Terrain for GaussianBump {
    fn height(&self, x_m: f64, y_m: f64) -> f64 {
        let sigma2 = self.sigma_m.max(EPS).powi(2);
        let dx = x_m - self.center_x_m;
        let dy = y_m - self.center_y_m;
        let bump = self.height_m * (-(dx * dx + dy * dy) / (2.0 * sigma2)).exp();
        self.z0_m + self.slope_x * x_m + bump
    }

    fn normal(&self, x_m: f64, y_m: f64) -> Vec3 {
        let sigma2 = self.sigma_m.max(EPS).powi(2);
        let dx = x_m - self.center_x_m;
        let dy = y_m - self.center_y_m;
        let bump = self.height_m * (-(dx * dx + dy * dy) / (2.0 * sigma2)).exp();
        let dzdx = self.slope_x - bump * dx / sigma2;
        let dzdy = -bump * dy / sigma2;
        Vec3::new(-dzdx, -dzdy, 1.0).normalize()
    }
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq)]
pub struct ChannelizedGully {
    pub z0_m: f64,
    pub slope_x: f64,
    pub depth_m: f64,
    pub width_m: f64,
}

impl Terrain for ChannelizedGully {
    fn height(&self, x_m: f64, y_m: f64) -> f64 {
        let width2 = self.width_m.max(EPS).powi(2);
        let channel = -self.depth_m * (-(y_m * y_m) / (2.0 * width2)).exp();
        self.z0_m + self.slope_x * x_m + channel
    }

    fn normal(&self, _x_m: f64, y_m: f64) -> Vec3 {
        let width2 = self.width_m.max(EPS).powi(2);
        let channel = -self.depth_m * (-(y_m * y_m) / (2.0 * width2)).exp();
        let dzdy = -channel * y_m / width2;
        Vec3::new(-self.slope_x, -dzdy, 1.0).normalize()
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct DemGrid {
    pub ncols: usize,
    pub nrows: usize,
    pub xllcorner_m: f64,
    pub yllcorner_m: f64,
    pub cellsize_m: f64,
    pub nodata_value: f64,
    pub values_m: Vec<f64>,
}

#[derive(Debug, Error)]
pub enum TerrainError {
    #[error("failed to read DEM: {0}")]
    Read(#[from] std::io::Error),
    #[error("missing or invalid DEM header field {0}")]
    Header(&'static str),
    #[error("DEM has {actual} elevation values, expected {expected}")]
    ValueCount { expected: usize, actual: usize },
    #[error("DEM query outside grid: x={x_m}, y={y_m}")]
    OutOfBounds { x_m: f64, y_m: f64 },
    #[error("DEM query touches nodata or non-finite elevation at col={col}, row_from_bottom={row_from_bottom}: x={x_m}, y={y_m}")]
    NoData {
        x_m: f64,
        y_m: f64,
        col: usize,
        row_from_bottom: usize,
    },
}

impl DemGrid {
    pub fn from_ascii_grid(path: impl AsRef<Path>) -> Result<Self, TerrainError> {
        let text = fs::read_to_string(path)?;
        Self::from_ascii_grid_str(&text)
    }

    pub fn from_ascii_grid_str(text: &str) -> Result<Self, TerrainError> {
        let mut lines = text.lines();
        let ncols = parse_header_usize(lines.next(), "ncols")?;
        let nrows = parse_header_usize(lines.next(), "nrows")?;
        let xllcorner_m = parse_header_f64(lines.next(), "xllcorner")?;
        let yllcorner_m = parse_header_f64(lines.next(), "yllcorner")?;
        let cellsize_m = parse_header_f64(lines.next(), "cellsize")?;
        let nodata_value = parse_header_f64(lines.next(), "NODATA_value")?;

        let values_m = lines
            .flat_map(|line| line.split_whitespace())
            .map(|value| {
                value
                    .parse::<f64>()
                    .map_err(|_| TerrainError::Header("elevation value"))
            })
            .collect::<Result<Vec<_>, _>>()?;

        let expected = ncols * nrows;
        if values_m.len() != expected {
            return Err(TerrainError::ValueCount {
                expected,
                actual: values_m.len(),
            });
        }

        Ok(Self {
            ncols,
            nrows,
            xllcorner_m,
            yllcorner_m,
            cellsize_m,
            nodata_value,
            values_m,
        })
    }

    fn value(&self, col: usize, row_from_bottom: usize) -> f64 {
        let row_from_top = self.nrows - 1 - row_from_bottom;
        self.values_m[row_from_top * self.ncols + col]
    }

    fn value_is_nodata(&self, value: f64) -> bool {
        if self.nodata_value.is_nan() {
            value.is_nan()
        } else {
            value == self.nodata_value
        }
    }

    fn checked_value(
        &self,
        col: usize,
        row_from_bottom: usize,
        x_m: f64,
        y_m: f64,
    ) -> Result<f64, TerrainError> {
        let value = self.value(col, row_from_bottom);
        if self.value_is_nodata(value) || !value.is_finite() {
            Err(TerrainError::NoData {
                x_m,
                y_m,
                col,
                row_from_bottom,
            })
        } else {
            Ok(value)
        }
    }

    pub fn xmax_m(&self) -> f64 {
        self.xllcorner_m + (self.ncols - 1) as f64 * self.cellsize_m
    }

    pub fn ymax_m(&self) -> f64 {
        self.yllcorner_m + (self.nrows - 1) as f64 * self.cellsize_m
    }

    pub fn clamp_xy(&self, x_m: f64, y_m: f64) -> (f64, f64) {
        (
            x_m.clamp(self.xllcorner_m, self.xmax_m()),
            y_m.clamp(self.yllcorner_m, self.ymax_m()),
        )
    }

    fn fractional_cell(
        &self,
        x_m: f64,
        y_m: f64,
    ) -> Result<(usize, usize, f64, f64), TerrainError> {
        let fx = (x_m - self.xllcorner_m) / self.cellsize_m;
        let fy = (y_m - self.yllcorner_m) / self.cellsize_m;
        if fx < 0.0 || fy < 0.0 || fx > (self.ncols - 1) as f64 || fy > (self.nrows - 1) as f64 {
            return Err(TerrainError::OutOfBounds { x_m, y_m });
        }
        let col0 = fx.floor().min((self.ncols - 2) as f64) as usize;
        let row0 = fy.floor().min((self.nrows - 2) as f64) as usize;
        Ok((col0, row0, fx - col0 as f64, fy - row0 as f64))
    }

    pub fn try_height(&self, x_m: f64, y_m: f64) -> Result<f64, TerrainError> {
        let (col0, row0, tx, ty) = self.fractional_cell(x_m, y_m)?;
        let z00 = self.checked_value(col0, row0, x_m, y_m)?;
        let z10 = self.checked_value(col0 + 1, row0, x_m, y_m)?;
        let z01 = self.checked_value(col0, row0 + 1, x_m, y_m)?;
        let z11 = self.checked_value(col0 + 1, row0 + 1, x_m, y_m)?;
        Ok((1.0 - tx) * (1.0 - ty) * z00
            + tx * (1.0 - ty) * z10
            + (1.0 - tx) * ty * z01
            + tx * ty * z11)
    }

    pub fn try_normal(&self, x_m: f64, y_m: f64) -> Result<Vec3, TerrainError> {
        self.fractional_cell(x_m, y_m)?;
        let h = 0.5 * self.cellsize_m.max(EPS);
        let x0 = (x_m - h).max(self.xllcorner_m);
        let x1 = (x_m + h).min(self.xmax_m());
        let y0 = (y_m - h).max(self.yllcorner_m);
        let y1 = (y_m + h).min(self.ymax_m());
        let dzdx = if (x1 - x0).abs() > EPS {
            (self.try_height(x1, y_m)? - self.try_height(x0, y_m)?) / (x1 - x0)
        } else {
            0.0
        };
        let dzdy = if (y1 - y0).abs() > EPS {
            (self.try_height(x_m, y1)? - self.try_height(x_m, y0)?) / (y1 - y0)
        } else {
            0.0
        };
        Ok(Vec3::new(-dzdx, -dzdy, 1.0).normalize())
    }

    pub fn height_clamped(&self, x_m: f64, y_m: f64) -> f64 {
        let (x_m, y_m) = self.clamp_xy(x_m, y_m);
        self.try_height(x_m, y_m)
            .expect("clamped DEM query must be inside grid and avoid nodata")
    }

    pub fn normal_clamped(&self, x_m: f64, y_m: f64) -> Vec3 {
        let (x_m, y_m) = self.clamp_xy(x_m, y_m);
        self.try_normal(x_m, y_m)
            .expect("clamped DEM normal query must be inside grid and avoid nodata")
    }
}

impl Terrain for DemGrid {
    fn height(&self, x_m: f64, y_m: f64) -> f64 {
        self.try_height(x_m, y_m)
            .unwrap_or_else(|_| panic!("DEM query outside grid at ({x_m}, {y_m})"))
    }

    fn normal(&self, x_m: f64, y_m: f64) -> Vec3 {
        self.try_normal(x_m, y_m)
            .unwrap_or_else(|err| panic!("DEM normal query failed at ({x_m}, {y_m}): {err}"))
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ClampedDemGrid {
    pub grid: DemGrid,
}

impl ClampedDemGrid {
    pub fn from_ascii_grid(path: impl AsRef<Path>) -> Result<Self, TerrainError> {
        Ok(Self {
            grid: DemGrid::from_ascii_grid(path)?,
        })
    }

    pub fn from_grid(grid: DemGrid) -> Self {
        Self { grid }
    }
}

impl Terrain for ClampedDemGrid {
    fn height(&self, x_m: f64, y_m: f64) -> f64 {
        self.grid.height_clamped(x_m, y_m)
    }

    fn normal(&self, x_m: f64, y_m: f64) -> Vec3 {
        self.grid.normal_clamped(x_m, y_m)
    }
}

fn parse_header_usize(line: Option<&str>, name: &'static str) -> Result<usize, TerrainError> {
    parse_header_value(line, name)?
        .parse()
        .map_err(|_| TerrainError::Header(name))
}

fn parse_header_f64(line: Option<&str>, name: &'static str) -> Result<f64, TerrainError> {
    parse_header_value(line, name)?
        .parse()
        .map_err(|_| TerrainError::Header(name))
}

fn parse_header_value<'a>(
    line: Option<&'a str>,
    name: &'static str,
) -> Result<&'a str, TerrainError> {
    let line = line.ok_or(TerrainError::Header(name))?;
    let mut parts = line.split_whitespace();
    let key = parts.next().ok_or(TerrainError::Header(name))?;
    let value = parts.next().ok_or(TerrainError::Header(name))?;
    if !key.eq_ignore_ascii_case(name) {
        return Err(TerrainError::Header(name));
    }
    Ok(value)
}

#[cfg(test)]
mod tests {
    use super::*;
    use approx::assert_relative_eq;

    #[test]
    fn dem_bilinear_interpolation_uses_bottom_origin() {
        let dem = DemGrid::from_ascii_grid_str(
            "ncols 2\nnrows 2\nxllcorner 0\nyllcorner 0\ncellsize 1\nNODATA_value -9999\n2 4\n0 2\n",
        )
        .unwrap();

        assert_relative_eq!(dem.try_height(0.5, 0.5).unwrap(), 2.0, epsilon = 1.0e-12);
        assert_relative_eq!(dem.try_height(0.0, 0.0).unwrap(), 0.0, epsilon = 1.0e-12);
    }
}
