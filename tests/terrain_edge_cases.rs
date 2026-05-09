//! Tests for DEM terrain error paths: out-of-bounds, nodata, malformed headers,
//! size mismatches, and clamped fallback behaviour.

use rust_rockfall::terrain::{ClampedDemGrid, DemGrid, Terrain, TerrainError};

// ─── DEM header / construction errors ─────────────────────────────────────

#[test]
fn dem_grid_rejects_ncols_below_two() {
    let text = "ncols 1\nnrows 3\nxllcorner 0.0\nyllcorner 0.0\ncellsize 1.0\nNODATA_value -9999\n1 2 3 4 5 6\n";
    let err = DemGrid::from_ascii_grid_str(text).unwrap_err();
    assert!(
        matches!(err, TerrainError::InvalidGrid(_)),
        "expected InvalidGrid, got {err:?}"
    );
}

#[test]
fn dem_grid_rejects_nrows_below_two() {
    let text =
        "ncols 3\nnrows 1\nxllcorner 0.0\nyllcorner 0.0\ncellsize 1.0\nNODATA_value -9999\n1 2 3\n";
    let err = DemGrid::from_ascii_grid_str(text).unwrap_err();
    assert!(matches!(err, TerrainError::InvalidGrid(_)));
}

#[test]
fn dem_grid_rejects_nonpositive_cellsize() {
    let text = "ncols 3\nnrows 2\nxllcorner 0.0\nyllcorner 0.0\ncellsize 0.0\nNODATA_value -9999\n1 2 3\n4 5 6\n";
    let err = DemGrid::from_ascii_grid_str(text).unwrap_err();
    assert!(matches!(err, TerrainError::InvalidGrid(_)));
}

#[test]
fn dem_grid_rejects_value_count_mismatch() {
    // 3x2 = 6 values expected, only 5 provided
    let text = "ncols 3\nnrows 2\nxllcorner 0.0\nyllcorner 0.0\ncellsize 1.0\nNODATA_value -9999\n1 2 3\n4 5\n";
    let err = DemGrid::from_ascii_grid_str(text).unwrap_err();
    assert!(matches!(err, TerrainError::ValueCount { .. }));
}

#[test]
fn dem_grid_rejects_non_finite_elevation_in_body() {
    // Using a sentinel value distinct from NODATA to carry a NaN should fail
    // because raw NaN in elevation values is rejected during parsing.
    // We simulate this by parsing a grid with "nan" as a data value.
    let text = "ncols 2\nnrows 2\nxllcorner 0.0\nyllcorner 0.0\ncellsize 1.0\nNODATA_value -9999\n1 2\n3 nan\n";
    let err = DemGrid::from_ascii_grid_str(text).unwrap_err();
    // "nan" won't parse as f64 via parse::<f64>() on some platforms; it may
    // succeed and produce a NaN on others. Either the Header parse error or
    // the InvalidGrid non-finite check is acceptable.
    assert!(
        matches!(err, TerrainError::Header(_) | TerrainError::InvalidGrid(_)),
        "unexpected error variant: {err:?}"
    );
}

// ─── DEM query errors ──────────────────────────────────────────────────────

fn flat_2x2_dem() -> DemGrid {
    // 2-column, 2-row DEM: cell centers at (0.5, 0.5), (1.5, 0.5), (0.5, 1.5), (1.5, 1.5)
    let text = "ncols 2\nnrows 2\nxllcorner 0.0\nyllcorner 0.0\ncellsize 1.0\nNODATA_value -9999\n10.0 12.0\n11.0 13.0\n";
    DemGrid::from_ascii_grid_str(text).unwrap()
}

#[test]
fn dem_try_height_returns_out_of_bounds_for_query_outside_grid() {
    let dem = flat_2x2_dem();
    let result = dem.try_height(100.0, 0.5);
    assert!(matches!(result, Err(TerrainError::OutOfBounds { .. })));
}

#[test]
fn dem_try_height_returns_out_of_bounds_for_negative_coordinates() {
    let dem = flat_2x2_dem();
    let result = dem.try_height(-1.0, 0.5);
    assert!(matches!(result, Err(TerrainError::OutOfBounds { .. })));
}

#[test]
fn dem_try_height_returns_nodata_when_cell_is_nodata_sentinel() {
    let text = "ncols 2\nnrows 2\nxllcorner 0.0\nyllcorner 0.0\ncellsize 1.0\nNODATA_value -9999\n10.0 -9999.0\n11.0 13.0\n";
    let dem = DemGrid::from_ascii_grid_str(text).unwrap();
    // Query at (1.5, 0.5) - the cell containing the nodata sentinel.
    let result = dem.try_height(1.5, 0.5);
    assert!(
        matches!(result, Err(TerrainError::NoData { .. })),
        "expected NoData, got {result:?}"
    );
}

#[test]
fn dem_try_height_succeeds_for_interior_query() {
    let dem = flat_2x2_dem();
    let h = dem.try_height(1.0, 1.0).unwrap();
    // Bilinear interpolation at the exact center of the 2x2 grid
    assert!(h.is_finite());
}

#[test]
fn dem_infallible_height_panics_outside_grid() {
    use std::panic::catch_unwind;
    let dem = flat_2x2_dem();
    let result = catch_unwind(|| dem.height(100.0, 0.5));
    assert!(result.is_err(), "expected panic for out-of-bounds query");
}

// ─── DemGrid cell-center coordinate helpers ────────────────────────────────

#[test]
fn dem_grid_center_helpers_match_expected_values() {
    let dem = flat_2x2_dem();
    assert_eq!(dem.xmin_center_m(), 0.5);
    assert_eq!(dem.ymin_center_m(), 0.5);
    assert_eq!(dem.xmax_center_m(), 1.5);
    assert_eq!(dem.ymax_center_m(), 1.5);
}

// ─── ClampedDemGrid fallback behaviour ────────────────────────────────────

fn flat_3x3_clamped() -> ClampedDemGrid {
    let text = "ncols 3\nnrows 3\nxllcorner 0.0\nyllcorner 0.0\ncellsize 1.0\nNODATA_value -9999\n10.0 10.0 10.0\n10.0 10.0 10.0\n10.0 10.0 10.0\n";
    let dem = DemGrid::from_ascii_grid_str(text).unwrap();
    ClampedDemGrid::from_grid(dem)
}

#[test]
fn clamped_dem_does_not_error_for_query_outside_grid() {
    let dem = flat_3x3_clamped();
    // query well outside the grid
    let result = dem.try_height(100.0, 50.0);
    assert!(
        result.is_ok(),
        "clamped DEM should not error outside bounds"
    );
    assert_eq!(result.unwrap(), 10.0);
}

#[test]
fn clamped_dem_normal_outside_grid_is_unit_length() {
    let dem = flat_3x3_clamped();
    let n = dem.try_normal(100.0, 100.0).unwrap();
    let norm = (n.x * n.x + n.y * n.y + n.z * n.z).sqrt();
    assert!(
        (norm - 1.0).abs() < 1.0e-10,
        "normal must be unit length, got norm={norm}"
    );
}
