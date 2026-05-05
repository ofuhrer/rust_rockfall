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
