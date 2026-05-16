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

## Region-To-Map Automation Gap

The desired long-term user workflow is region-driven: a user supplies an AOI,
and the system discovers/downloads the required public geodata, prepares
terrain and context inputs, identifies candidate release zones, generates a
release/scenario plan, runs a sufficient ensemble, and exports map products.
That is not yet the implemented workflow.

The largest missing automation pieces are:

- AOI-to-swisstopo product and tile discovery, including download/cache,
  checksum, product-version, retry, and resume handling;
- generic terrain/context preprocessing for swissALTI3D, SWISSIMAGE,
  swissTLM3D, swissSURFACE3D/swissSURFACE3D Raster, and swissBUILDINGS3D;
- heuristic release-zone identification from slope, terrain quality, optional
  geology/material context, and exclusion/context masks;
- pragmatic release/scenario plan generation with release-cell ids, block-size
  or block-mass assumptions, sampling weights, seed policy, and trajectory
  counts;
- automatic ensemble sufficiency criteria based on spatial convergence and
  uncertainty stability rather than a fixed production-scale run;
- native rebuildable reduced output and COG-ready GIS export as default
  workflow surfaces;
- a site-level orchestrator that chains preparation, validation, hazard
  building, uncertainty checks, GIS export, and reporting.

Those steps would still produce conditional diagnostic maps until a separate
physical-probability layer exists. True grid-cell intensity-frequency curves
require source occurrence rates, block-population or block-size frequency
semantics, uncertainty propagation, and validation/calibration evidence. Those
frequency semantics remain deliberately outside the current automated
conditional diagnostic workflow.

## First Swiss Pilot Workflow

1. Select one small Alpine slope or valley domain with a clearly bounded source
   zone and runout corridor.
2. Before any staging, run the AOI-to-swisstopo dry-run planner against the
   candidate site config to list required public products, expected staging
   paths, and unresolved acquisition decisions, then copy the public real-site
   preparation manifest template to an ignored pilot directory and fill in the
   domain, source-tile inventory, local paths, and preprocessing plan before
   any simulation work.
3. Run the release-zone heuristic dry run against the same site config to
   separate heuristic requirements from concrete inputs and to document which
   terrain and public-context prerequisites are still missing before any real
   release-zone interpretation is claimed.
4. Obtain the required swissALTI3D 2 m tiles manually or through a documented
   swisstopo download process. Use 0.5 m only when the pilot question requires
   it and storage is acceptable.
5. Record source tile ids, product version/date, CRS, vertical datum, checksum,
   and license/terms reference.
6. Crop the tiles to the pilot domain with a small buffer and convert to the
   internal DEM representation; preserve LV95 coordinates and LN02 heights.
7. Compute slope/aspect/hillshade for QA and define release zones from a slope
   threshold plus a documented geology/material mask.
8. Run deterministic ensembles with explicit scenario ids, global seed, release
   cell ids, and trajectory ids.
9. Build hazard layers: reach probability, deposition density, maximum kinetic
   energy, maximum jump height, and significant impact density where impact
   events are available.
10. Export development products as CSV/ASCII for inspection; for real pilot
   exchange, move toward GeoTIFF/COG rasters and GeoPackage/GeoJSON vectors.
11. Visually compare terrain, release zones, and hazard layers against
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

The candidate also now has a committed public-geodata acquisition manifest at
`tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_public_geodata_acquisition.yaml`.
That file keeps the second site metadata-only while spelling out the expected
terrain crop, context layers, source-zone/scenario records, and ignored output
roots that must exist before any second-site run is attempted.

The same manifest now drives a deterministic dry-run acquisition summary in
the second-site preflight and the AOI acquisition planner. That summary names
the expected staging roots and metadata contracts for SWISSIMAGE,
swissTLM3D, swissSURFACE3D, swissSURFACE3D Raster, and swissBUILDINGS3D, but
it does not download anything and it does not convert the deferred public
context into readiness.

The Chant Sura real-context readiness gate,
`scripts/check_chant_sura_real_context_readiness_gate.py`, adds the next
layer: it compares the acquisition plan with the locally staged core files and
the deferred public-context products, and it keeps the synthetic core fixtures
explicitly out of the public-context evidence bucket.

`scripts/map_physical_credibility_evidence_requirements.py` now maps the
project's validation gap into concrete evidence requirements. It keeps the
distinction explicit between:

- swisstopo input geodata such as swissALTI3D, SWISSIMAGE, swissTLM3D,
  swissSURFACE3D, swissSURFACE3D Raster, and swissBUILDINGS3D, which are
  workflow inputs and context layers; and
- validation/calibration evidence such as independent holdout benchmarks,
  block-population surveys, and source-frequency catalogues, which are not
  satisfied by synthetic fixtures or terrain/context inputs alone.

That separation is deliberate: the public geodata strategy prepares inputs for
hazard-map workflows, but it does not by itself establish physical credibility.
The helper also ranks the evidence acquisitions so observed runout/deposition
is the first actionable acquisition, while source-frequency and temporal-
frequency evidence remain deferred because annual-frequency semantics stay out
of scope.

The second-site preflight now reports this boundary explicitly with
`public_context_boundary_status`, per-product expected paths, metadata
requirements, synthetic-fixture boundaries, and blocked second-site command
templates. Synthetic core fixtures can satisfy terrain, source-zone, scenario,
and policy readiness, but they must not satisfy public-context readiness for
SWISSIMAGE, swissTLM3D, swissSURFACE3D, swissSURFACE3D Raster, or
swissBUILDINGS3D.

The canonical conditional diagnostic interpretation helper
`scripts/summarize_tschamut_conditional_diagnostic_interpretation.py`
uses this portability boundary only as a blocker boundary. It does not turn
the deferred Chant Sura public-context products into validation evidence or a
second-site readiness claim.

The candidate source-zone / scenario policy fixture at
`validation/policies/chant_sura_fluelapass_portability_example_v1_source_scenario_policy_v1.yaml`
is a synthetic contract record, not physical evidence. It helps separate the
portable policy shape from the site-specific public context that remains
deferred.

The tiny staging helper
`scripts/prepare_chant_sura_fluelapass_minimal_preflight_inputs.py` copies the
synthetic core fixture set from
`tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_minimal_staging/`
into the ignored Chant Sura paths. It only stages the minimum terrain,
source-zone, scenario, and source-scenario policy records plus the ignored
input, validation, and hazard roots. It also creates the empty processed-
context root so the second-site preflight can report the public products as
`deferred_public_context_inputs` rather than as missing core inputs. SWISSIMAGE,
swissTLM3D, swissSURFACE3D, swissSURFACE3D Raster, and swissBUILDINGS3D stay
deferred and continue to appear explicitly in the preflight and acquisition
manifest.
That helper is a synthetic staging aid only. It is useful for core readiness
checks, but it is not a real public-context acquisition workflow and must not
be interpreted as one.

The validation/calibration evidence-gap helper
`scripts/assess_validation_calibration_evidence_gaps.py` now makes the current
boundary explicit: workflow reproducibility is strong, diagnostic validation
is partial, but physical credibility is not yet established. Calibration and
block-population evidence remain missing, and annual-frequency, risk,
exposure, vulnerability, and operational claims stay out of scope.

The observed runout/deposition intake contract helper
`scripts/summarize_observed_runout_deposition_intake_contract.py` now also
generates a dry-run readiness pack in a caller-provided temporary directory.
That pack contains a template manifest, required geometry inventory,
provenance checklist, and validation summary, and it is explicitly marked as
a template/non-evidence artifact so future benchmark evidence cannot be
confused with the contract scaffolding.

The source-zone / scenario contract audit helper
`scripts/audit_multisite_source_scenario_contract.py` now distinguishes the
portable contract shape from the Tschamut-specific heuristics that were used
to freeze the current pilot. It is still metadata-only and does not imply that
the Chant Sura candidate is ready for a run.

The release-plan dry-run helper
`scripts/plan_release_plan_dry_run.py` extends that boundary one step further
by turning the staged candidate source-zone record into deterministic release
rows and block-scenario rows. It keeps reusable semantics, site-specific
inputs, and Tschamut-only seed / block-class heuristics separate, and the
portable command plan now carries a template-only second-site execution entry
that remains blocked until public context is present.

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

A bounded proof-of-concept conversion path now exists in
`scripts/prototype_cog_conversion.py`. On a single same-scale GeoTIFF it writes
only to `/tmp`, converts with `gdal_translate -of COG -co BLOCKSIZE=256 -co
COMPRESS=ZSTD`, and verifies a tiled COG layout with overviews via
`gdalinfo`. That scratch proof is now extended to an ignored same-scale
package-level result at `hazard/results/tschamut_public_pilot/gate_v1_cog_export`,
which audits as `cog_package_ready` with `cloud_optimized: true` metadata.
The committed same-scale outputs remain unchanged and should still audit as
`gis_package_ready_cog_blocked` until regenerated with a COG-ready layout.

The canonical portable command plan now names the package-level conversion
step explicitly, pairing `scripts/build_hazard_layers.py --export-cog` with
the standard and converted-package GIS/COG audits. The prototype script stays
documented as a sample-only proof path; the command plan is the canonical
workflow surface for the ignored package conversion.
