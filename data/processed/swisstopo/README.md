# swisstopo Processed Metadata Fixtures

This directory is reserved for small, reproducible metadata fixtures related to
future swisstopo terrain ingestion.

It must not contain national swisstopo raw products or large cropped rasters.
Full swissALTI3D, swissSURFACE3D, SWISSIMAGE, and similar products should stay
under local ignored raw-data paths and be referenced by metadata/provenance
records only.

Current fixture:

- `sample_swissalti3d_tile_metadata.yaml`: schema-style example for one
  swissALTI3D pilot tile. It is metadata only; no source raster is committed.
- `public_real_site_pilot_manifest_template.yaml`: Phase 1 public real-site
  preparation manifest template. Copy it to an ignored local pilot directory
  before filling in real tile ids, checksums, or processed DEM paths.

Runtime pilot fixture:

- `../../../validation/data/processed/swisstopo_pilot/` contains a tiny synthetic
  swissALTI3D-style ESRI ASCII crop, terrain-source metadata, source-area
  metadata, and terrain/material-class metadata used by the Swiss pilot
  validation cases. These files are synthetic test data, not swisstopo raw
  products or calibrated terrain classes.

See `docs/swisstopo_data_strategy.md` for the data strategy,
`docs/swiss_terrain_ingestion_pilot.md` for the runtime pilot contract, and
`docs/public_real_site_geodata_preparation.md` for the share-safe real-site
preparation manifest contract.
