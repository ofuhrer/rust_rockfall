# Tschamut Public Pilot GIS Package Review

Status: share-safe diagnostic review record for the executed target-scale
Tschamut public conditional pilot GIS package. The selected visual-QA record now
classifies the target-scale GIS/QGIS review as `blocked`: QGIS is unavailable in
the current non-GUI agent environment, and the ignored target-scale package
artifacts are absent in this checkout. This review is not a QGIS project,
production COG package, operational hazard map, physical-probability product,
annual-frequency product, return-period product, or risk map.

This is local-only evidence. The generated rasters, manifests, and parity files
listed below are ignored outputs and are not present in a clean checkout. The
selected target-scale gate records regenerated local artifacts and checksums,
but reproduction still requires the documented public Tschamut preparation and
ignored local output paths.

## Scope

- Pilot id: `tschamut_public_pilot`
- Run id: `tschamut_public_scalable_conditional_target_gate_v1`
- Package manifest:
  `hazard/results/tschamut_public_pilot/target_gate_v1/tschamut_public_scalable_conditional_target_gate_v1_pilot_gis_package_manifest.json`
- Hazard manifest:
  `hazard/results/tschamut_public_pilot/target_gate_v1/validation_tschamut_public_target_gate_v1_manifest.json`
- Map package manifest:
  `hazard/results/tschamut_public_pilot/target_gate_v1/tschamut_public_scalable_conditional_target_gate_v1_map_package_manifest.json`
- Terrain metadata:
  `data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_swissalti3d_metadata.yaml`

All listed artifacts are ignored local outputs except for this review record.
No raw swisstopo data, processed DEM crop, GeoTIFF, CSV, ESRI ASCII grid,
conditional curve table, or generated package manifest is committed. The
target-scale package artifacts are intentionally absent from git. The selected
target-scale gate is executed but `inconclusive`; this visual-QA record does not
change that classification.

## Automated Package QA

Target-scale package command, to be rerun only after restoring ignored target
artifacts:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run python \
  scripts/validate_pilot_gis_package.py \
  hazard/results/tschamut_public_pilot/target_gate_v1/tschamut_public_scalable_conditional_target_gate_v1_pilot_gis_package_manifest.json \
  --require-real-site \
  --require-existing-files \
  --format json
```

Result in this checkout: blocked, because the ignored target-scale package
manifest and rasters are absent.

The selected target-gate record reports that a local target-scale package was
generated in a prior local run, with summary-only conditional curves, output
budget evidence, and reducer parity. Those artifacts are intentionally not
committed, so this review cannot re-run automated package/file QA here.

## Visual QA Result

The selected visual-QA record is:
`validation/pilot_runs/tschamut_public_gis_visual_qa_v1.yaml`.

Command:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run python \
  scripts/validate_pilot_gis_visual_qa.py \
  validation/pilot_runs/tschamut_public_gis_visual_qa_v1.yaml \
  --format json
```

Result: pass for the review-record contract, with overall visual-QA
classification `blocked`.

Manual QGIS inspection could not be completed in the non-GUI agent environment:
`which qgis` returned no executable, the ignored target-scale package artifacts
are absent in this checkout, and no QGIS screenshots, layer-list export, or
metadata-dialog evidence was produced. The package therefore has this gate
status:

- Automated manifest/file QA: `blocked`
- Manual GIS/QGIS visual QA: `blocked`
- Overall target-scale visual-QA acceptance: `blocked`

Checklist outcome:

- CRS metadata: `blocked` for target-scale visual review because the ignored
  target package is absent here.
- Vertical datum metadata: `blocked` for target-scale visual review because the
  ignored processed terrain metadata/package artifacts are absent here.
- Raster grid alignment: `blocked` because DEM/hazard/source-zone overlay was
  not opened in QGIS.
- Nodata versus valid-zero styling: `blocked` because QGIS styling was not
  inspected.
- Source-zone overlay: `blocked` because no QGIS overlay screenshot or
  layer-list evidence was produced.
- Conditional layer labels: `pass` at manifest/report level.
- Unsupported-claim boundaries: `pass` at manifest/report level.

The target-scale package remains suitable for a future hands-on QGIS review
after ignored artifacts are restored or regenerated. It is not accepted as a
visually reviewed QGIS package.

## Claim Boundary

Allowed current interpretation:

- local diagnostic GeoTIFF review rasters;
- CSV/ESRI ASCII parity grids for the same generated layers;
- conditional intensity-exceedance and sampling-weighted conditional products;
- research diagnostic source-zone and scenario conditioning.

Unsupported current interpretation:

- annual frequency;
- return period;
- physical probability;
- exposure, vulnerability, consequence, expected loss, or risk;
- operational or validated hazard-map status;
- Cloud-Optimized GeoTIFF or production tiled package status.

## Next GIS Action

The next reviewer should restore or regenerate the ignored target-scale package,
run QGIS locally, load the package with the terrain DEM or hillshade,
source-zone sidecar, release-cell context, and selected rasters; verify spatial
alignment, nodata versus valid zero styling, layer labels, and
conditional-product wording; then update the visual-QA record only if the
manual GIS findings support a `pass` or `no-go` classification.
