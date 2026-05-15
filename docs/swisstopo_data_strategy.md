# swisstopo Data Strategy

## Purpose

This project uses two distinct classes of data:

- **Experimental validation datasets** such as Chant Sura, Tschamut, Schiers,
  Surava, and impact-test tables. These constrain model physics, diagnostics,
  calibration experiments, and validation metrics.
- **Operational input geodata** such as swissALTI3D, swissSURFACE3D,
  swissTLM3D, swissBUILDINGS3D, GeoCover, geological maps, and SWISSIMAGE.
  These are the terrain, context, and QA layers required for future Swiss
  hazard-map workflows.

The distinction matters. A field experiment can show whether a model behaves
plausibly, but it is not the terrain foundation for a national map product.
Conversely, swissALTI3D is authoritative terrain input, but it does not validate
impact physics by itself.

No full swisstopo product is downloaded or committed by default. This document
records the intended roles, metadata requirements, and first pilot workflow.

## Dataset Roles

| Dataset | Purpose | Resolution / Format | CRS / Heights | Tiling / Size | Project Role | Hazard or Risk |
|---|---|---|---|---|---|---|
| swissALTI3D | Bare-earth digital elevation model without vegetation or buildings | 0.5 m or 2 m grid; COG GeoTIFF, ASCII XYZ, ESRI ASCII on request | LV95 / LN02, represented internally as EPSG:2056 + LN02 | About 43,500 one-kilometre tiles; national COG size is tens to hundreds of GB depending on resolution | Mandatory terrain foundation for pilot and later Swiss hazard layers | Hazard |
| swissSURFACE3D | Classified LiDAR point cloud of natural and man-made surface objects | COPC / LAS point cloud; high point density | LV95 / LN02 | One-kilometre tiles; hundreds of MB per tile | Optional future context for forest, obstacle, and DSM derivation | Hazard context; exposure context where used carefully |
| swissSURFACE3D Raster | Digital surface model including visible permanent landscape elements | 0.5 m grid; COG GeoTIFF, ASCII XYZ, ESRI ASCII on request | LV95 / LN02 | One-kilometre tiles; national-scale hundreds of GB | Optional DSM/obstacle context and canopy/building height comparisons against swissALTI3D | Hazard context, not risk alone |
| swissTLM3D | Large-scale 3D topographic landscape vector model | File Geodatabase, Shapefile, GeoPackage, DXF, INTERLIS | LV95 / LN02 | National vector product; thematically organized | Infrastructure, hydrography, roads, land-cover context, release/exclusion masks, QA overlays | Hazard context; risk only with exposure/vulnerability |
| swissBUILDINGS3D | 3D building models | File Geodatabase, DWG, CityGML where available | LV95 / LN02 | National/building-tile product; large | Building obstacle/exposure context for future risk workflows; not needed for core hazard physics | Mostly risk/exposure; optional obstacle context |
| GeoCover | Geological 2D vector model of superficial strata | File Geodatabase ZIP, GeoPackage, INTERLIS | MN95/LV95 | Map-sheet/compilation based | Geological/material context and future release-zone or terrain-class masks | Hazard context |
| Geological Atlas 1:25,000 | Detailed geological maps and explanatory booklets | Printed/PDF/map products and source-derived geodata through swisstopo channels | Product dependent; align to LV95 before use | Sheet based | Site-scale geology and material interpretation | Hazard context |
| GeoMaps 500 | Overview geological, tectonic, hydrogeological, geophysical, and palaeoglaciological maps | Pixel and vector products at 1:500,000 | Product dependent; use only with explicit CRS metadata | National overview | Regional context only; too coarse for local release-zone delineation | Hazard context |
| SWISSIMAGE | Orthophoto mosaic for visual inspection and QA | 10 cm / 25 cm source resolution; downloadable COG tiles, plus lower-resolution options | CH1903+ / LV95 (EPSG:2056) for recent products | About 42,700 one-kilometre tiles; national COG size can reach TB scale at 10 cm | Visual QA, release-zone review, terrain/preprocessing sanity checks | QA/context; not a hazard or risk model |

## Mandatory Pilot Inputs

A first Swiss pilot should stay small and auditable. Required input layers:

- swissALTI3D cropped to a single slope or valley domain;
- a release-zone mask or polygon generated from slope threshold and documented
  geology/material assumptions;
- model configuration, seed policy, and block/source assumptions;
- hazard-layer output metadata containing CRS, resolution, extent, source tile
  identifiers, and preprocessing provenance.

Useful but optional pilot layers:

- SWISSIMAGE for visual QA;
- GeoCover or Geological Atlas information for release-zone/material screening;
- swissTLM3D for roads, waterways, or exclusion/context features;
- swissSURFACE3D Raster for vegetation/building/obstacle sensitivity studies.

Risk-layer inputs such as swissBUILDINGS3D, road traffic, building occupancy, or
vulnerability functions are deliberately outside the first hazard pilot.

## Terrain Tile Metadata

Every swisstopo terrain tile converted into the internal DEM representation
should carry metadata equivalent to:

- source dataset id and product name;
- source URL or download record;
- tile id and source filename;
- CRS (`EPSG:2056` for LV95 workflows);
- vertical datum (`LN02` unless explicitly transformed);
- height unit, nodata value, cell size, and raster dimensions;
- LV95 extent in metres;
- crop extent and resampling method, if any;
- checksums for raw and processed files when available;
- preprocessing tool and timestamp;
- license/terms reference;
- project role and operational status.

The sample metadata fixture lives at
`data/processed/swisstopo/sample_swissalti3d_tile_metadata.yaml`. It is metadata
only and does not imply that the referenced raw swisstopo tile is present.

The first runtime pilot fixture lives at
`validation/data/processed/swisstopo_pilot/`. It contains a tiny synthetic
swissALTI3D-style ESRI ASCII crop and a matching metadata sidecar. The fixture is
not real swisstopo elevation data; it exists to validate CRS, LN02 height,
extent, nodata, provenance, and manifest handling before manually supplied real
terrain crops are introduced.

The Phase 1 public real-site preparation contract lives in
`docs/public_real_site_geodata_preparation.md`. Its checked-in template manifest
is `data/processed/swisstopo/public_real_site_pilot_manifest_template.yaml` and
can be validated with
`scripts/validate_public_real_site_geodata_manifest.py`. The template records
the required public geodata inventory, local ignored directory layout,
preprocessing gates, and claim boundaries without downloading or committing raw
swisstopo products.

The first selected public pilot-domain manifest is
`data/processed/swisstopo/tschamut_public_pilot_manifest.yaml`. It fixes the
Tschamut 2014 public release/deposition corridor, public swissALTI3D tile
`2696-1167`, EPSG:2056/LN02, the expected 2 m crop extent, source and processed
checksums, and the command
`scripts/prepare_tschamut_public_benchmark.py --output-root
data/processed/swisstopo/tschamut_public_pilot --padding-m 250 --force`.
Generated raw and processed files remain ignored; the manifest is provenance
for input geodata, not validation evidence.

The selected Tschamut pilot now also has a share-safe forest/obstacle omission
scope record at `validation/pilot_runs/tschamut_public_obstacle_scope_v1.yaml`,
validated by `scripts/validate_pilot_obstacle_scope.py`. It classifies current
forest and obstacle omission as `limiting` because SWISSIMAGE, swissTLM3D,
swissSURFACE3D/swissSURFACE3D Raster, and swissBUILDINGS3D context layers have
not been locally downloaded or reviewed for the selected corridor. This record
does not add obstacle physics, risk or exposure semantics, or operational
approval; it only prevents DEM-only conditional outputs from being interpreted
as evidence that vegetation, roads, buildings, barriers, or channels are
irrelevant.

## Minimal Ingestion Design

The first ingestion layer should not introduce heavy GIS dependencies into the
Rust core. The recommended boundary is:

1. **External geodata preparation** reads swissALTI3D COG/GeoTIFF or ASCII data,
   crops to a pilot domain, checks metadata, and writes either ESRI ASCII DEM or
   a future internal raster container.
2. **Metadata validation** verifies LV95/EPSG:2056 coordinates, LN02 heights,
   finite extent, positive resolution, nodata policy, and source provenance.
3. **Simulation kernel** consumes the same trait-based terrain abstraction as
   existing DEM fixtures; it does not know about swisstopo download logistics.
4. **Hazard post-processing** exports rasters with CRS/resolution/extent and
   provenance metadata attached.

This keeps the single-trajectory simulator deterministic and free of file I/O
side effects while allowing a later Python/GDAL or Rust/GDAL adapter outside the
kernel.

The current implementation supports this boundary through `terrain.metadata_path`
and optional `release_zone.metadata_path` in validation/benchmark YAML. The
terrain parser validates `EPSG:2056`, `LN02`, metre units, finite LV95 extent,
raster resolution/dimensions, nodata handling, source/provenance fields, and
consistency with small ESRI ASCII DEM headers. The release-zone parser validates
an LV95/LN02 polygon fixture, deterministic grid sampling metadata, and CRS
compatibility with the terrain sidecar. The optional `terrain_classes.metadata_path`
parser validates an aligned categorical raster and declared class ids, then uses
those classes only to select local values for existing contact/scarring
parameters. The generated `run_manifest_v1` records the validated terrain-source,
release-zone, and terrain-class metadata. Details are in
`docs/swiss_terrain_ingestion_pilot.md`.

For the first real-site Tschamut rerun, `scripts/prepare_tschamut_swissalti3d_pilot.py`
creates ignored local case files from a private swissALTI3D-style DEM crop,
terrain metadata, release-zone metadata, and optional terrain-class metadata.
The script performs the same lightweight CRS, extent, resolution, nodata, and
provenance checks before any validation command is run. Details are in
`docs/tschamut_swissalti3d_pilot.md`.

## First Swiss Pilot Workflow

1. Select one small Alpine slope or valley domain with a clearly bounded source
   zone and runout corridor.
2. Copy the public real-site preparation manifest template to an ignored pilot
   directory and fill in the domain, source-tile inventory, local paths, and
   preprocessing plan before any simulation work.
3. Obtain the required swissALTI3D 2 m tiles manually or through a documented
   swisstopo download process. Use 0.5 m only when the pilot question requires
   it and storage is acceptable.
4. Record source tile ids, product version/date, CRS, vertical datum, checksum,
   and license/terms reference.
5. Crop the tiles to the pilot domain with a small buffer and convert to the
   internal DEM representation; preserve LV95 coordinates and LN02 heights.
6. Compute slope/aspect/hillshade for QA and define release zones from a slope
   threshold plus a documented geology/material mask.
7. Run deterministic ensembles with explicit scenario ids, global seed, release
   cell ids, and trajectory ids.
8. Build hazard layers: reach probability, deposition density, maximum kinetic
   energy, maximum jump height, and significant impact density where impact
   events are available.
9. Export development products as CSV/ASCII for inspection; for real pilot
   exchange, move toward GeoTIFF/COG rasters and GeoPackage/GeoJSON vectors.
10. Visually compare terrain, release zones, and hazard layers against
    SWISSIMAGE and hillshade. Treat the result as a research diagnostic unless
    separately reviewed and validated.

## Second-Site Portability

`scripts/check_second_site_public_geodata_preflight.py` summarizes the public
geodata, metadata records, and ignored output roots needed to port the current
Tschamut workflow to another Swiss site. It is metadata-only and does not
download or stage any second-site data. The command is meant to surface what is
reusable from Tschamut and what still needs site-specific public input before a
new pilot can be attempted.

The staged placeholder candidate manifest for that helper is
`tests/fixtures/second_site_public_geodata_preflight/candidate_placeholder_site.yaml`.
Its current blocked report is expected, because it names site-specific paths
without any real second-site public geodata yet staged under them.

A more concrete candidate example is
`tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml`.
It treats Chant Sura / Flüelapass as the candidate site because the repo
already contains Chant Sura dataset metadata and benchmark fixtures, but the
example remains blocked until terrain, source-zone, scenario, and context
products are staged at the candidate roots.

The source-zone / scenario contract audit helper
`scripts/audit_multisite_source_scenario_contract.py` now distinguishes the
portable contract shape from the Tschamut-specific heuristics that were used
to freeze the current pilot. It is still metadata-only and does not imply that
the Chant Sura candidate is ready for a run.

## Data-Size Implications

swissALTI3D and SWISSIMAGE are tile-based national products with full-coverage
sizes that range from tens of GB to multiple TB depending on resolution and
format. Future workflows must therefore be tiled and resumable:

- never require national input data in CI;
- keep raw swisstopo downloads out of git;
- keep pilot fixtures cropped and license-compatible;
- record provenance for every cropped or resampled tile;
- prefer GeoTIFF/COG or other tiled raster outputs for map products;
- design hazard reducers so partial tiles can be merged deterministically.

## Operational-Use Boundary

This strategy prepares the project to use authoritative Swiss geodata. It does
not make the simulator operationally validated. Hazard layers are simulated
physical indicators only. Risk maps require exposure, vulnerability, temporal
occurrence, and consequence assumptions that are not part of the current core.

The current same-scale Tschamut outputs now have complete map-package and
pilot-GIS manifests and GeoTIFF layer outputs, but the audited rasters are not
yet cloud-optimized: the manifests mark `cloud_optimized: false`, the sampled
GeoTIFFs are strip-organized with no overviews, and the GIS/COG audit therefore
remains package-complete but COG-blocked rather than scientifically accepted.
