# Terrain Model Update

This document records the first terrain-focused model improvement after the Tschamut validation and calibration experiments. The objective is to reduce structural terrain error without adding new contact physics or production GIS complexity.

## Current Shortcomings

Before this update, real-data validation used a least-squares plane sampled as an ESRI ASCII grid. That was transparent and reproducible, but physically weak:

- local slope breaks, concavities, ridges, and channelization were removed;
- normals were constant, so terrain-guided redirection could not be represented;
- strict DEM access could fail when trajectories left a small raster patch;
- calibration could change restitution, friction, and roughness, but could not recover missing terrain geometry.

The Tschamut review and calibration therefore identified terrain representation as a dominant structural limitation.

## Chosen Increment

The new opt-in terrain path is `ascii_dem_clamped` / `esri_ascii_grid_clamped`. It wraps the existing ESRI ASCII grid reader and keeps the same bilinear interpolation inside the grid. Queries outside the grid are clamped to the nearest grid boundary before evaluating height and normals.

This is deliberately modest. It does not introduce heavy GIS dependencies, resampling libraries, spatial indexes, or multiresolution terrain. It gives validation cases a bounded terrain-patch policy while preserving the strict `ascii_dem` behavior for tests that should fail on out-of-bounds access.

## Tschamut Terrain Proxy

`scripts/preprocess_datasets.py --dataset tschamut2014` now writes `terrain.asc` as an `idw_residual_dem_from_lps` proxy:

```text
z_trend = slope_x * x + slope_y * y + intercept
z = z_trend + IDW_residual(public LPS ground points)
```

The trend plane uses all public LPS ground elevations from the selected EnviDat resource. Residuals are interpolated with inverse-distance weighting (`k_nearest = 24`, `idw_power = 2`) on a `5 m` ESRI ASCII grid with `45 m` padding around the trajectory points.

This is still not an official field DEM. It is a reproducible public-data terrain proxy that preserves more local relief than a plane and is suitable for v0.3.0 structural-error experiments.

## Boundary Policy

`ascii_dem_clamped` clamps `(x, y)` to the raster bounds for height and finite-difference normal queries. This avoids edge panics in limited-patch validation cases and allows trajectories to finish gracefully. The trade-off is that motion beyond the raster edge sees an extrapolated boundary height and one-sided/flat boundary normal. This can affect runout and must be reported when used.

Strict `ascii_dem` remains available and unchanged for verification fixtures where out-of-bounds access should remain an error.

## Validation Use

Two Tschamut validation cases are now kept side by side:

- `validation_tschamut_proxy_plane`: fitted-plane baseline retained for terrain-model comparison;
- `validation_tschamut_basic`: IDW residual DEM with clamped boundary access.

Both cases are uncalibrated distribution-level comparisons. Differences between them should be interpreted as evidence of terrain sensitivity, not as operational validation.
