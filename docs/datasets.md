# Public Dataset Integration

The dataset registry is `data/datasets.yaml`. Raw data are downloaded only on demand and are ignored by git.

## Public Dataset Sources

Primary public sources currently registered:

- Tschamut 2014 repetitive trajectory testing: EnviDat DOI [10.16904/envidat.34](https://doi.org/10.16904/envidat.34), ODbL with DbCL.
- Tschamut small-rock induced campaign: EnviDat DOI [10.16904/envidat.37](https://doi.org/10.16904/envidat.37), ODbL with DbCL.
- Chant Sura / Flüelapass campaign: EnviDat DOI [10.16904/envidat.174](https://doi.org/10.16904/envidat.174), WSL Data Policy.
- Schiers deadwood campaign: EnviDat DOI [10.16904/envidat.359](https://doi.org/10.16904/envidat.359), WSL Data Policy.
- Surava rockfall trilogy: EnviDat DOI [10.16904/envidat.248](https://doi.org/10.16904/envidat.248), WSL Data Policy.
- Parde rockfall gallery impact tests: EnviDat DOI [10.16904/envidat.41](https://doi.org/10.16904/envidat.41), ODbL with DbCL.

Operational Swiss geodata sources are also registered as metadata-only
placeholders. They are input-data candidates for future hazard-map workflows,
not experimental validation datasets:

- swissALTI3D: primary bare-earth DEM terrain foundation.
- swissSURFACE3D and swissSURFACE3D Raster: surface, vegetation, building, and
  obstacle context.
- swissTLM3D: topographic vector context for infrastructure, hydrography,
  land-cover, and release/exclusion masks.
- swissBUILDINGS3D: building exposure or obstacle context for later risk or
  site-specific studies.
- GeoCover, Geological Atlas 1:25,000, and GeoMaps 500: geological/material and
  release-zone context at different scales.
- SWISSIMAGE: orthophoto QA and visual review.

See `swisstopo_data_strategy.md` for the distinction between validation
datasets and operational geodata.

## Downloading Data

Install PyYAML if needed:

```bash
python3 -m pip install PyYAML
```

Download a targeted resource:

```bash
python3 scripts/download_datasets.py --dataset tschamut2014 --resource overview_tests
```

For the current Tschamut validation subset, download the public overview and LPS trajectory resources:

```bash
python3 scripts/download_datasets.py \
  --dataset tschamut2014 \
  --resource overview_tests \
  --resource lps_trajectories
```

Downloaded files go to `data/raw/<dataset_id>/` and retain original filenames. A JSONL manifest records URL, date, size, and SHA-256 checksum.

## Preprocessing

Create the synthetic fixture:

```bash
python3 scripts/preprocess_datasets.py --dataset synthetic_plane_basic
```

Preprocess the Tschamut 2014 resources:

```bash
python3 scripts/preprocess_datasets.py --dataset tschamut2014
```

This writes:

- `data/processed/tschamut2014/release_points.csv`
- `data/processed/tschamut2014/observed_deposition.csv`
- `data/processed/tschamut2014/block_metadata.csv`
- `data/processed/tschamut2014/terrain.asc`
- a small checked-in subset under `validation/data/processed/tschamut/`

The Tschamut terrain file is an `idw_residual_dem_from_lps` ESRI ASCII grid proxy. It adds inverse-distance-weighted residuals from public LPS ground elevations to a least-squares trend plane. It is more realistic than the earlier fitted plane because it retains local terrain variation, but it is still not an official field DEM. Coordinates remain in the public LPS local horizontal coordinate system, and elevations are shifted by `-1600 m` to match the overview table convention.

Dataset-specific conversions should write validation-ready CSV/GeoJSON under `data/processed/<dataset_id>/` and must document CRS, units, and inferred fields.

swisstopo products are not downloaded by the generic validation-data workflow.
For Swiss pilot domains, download only the required tiles manually or through a
documented future adapter, preserve raw filenames locally, and create
metadata/provenance records before conversion to internal DEM fixtures.

Create the Chant Sura trajectory-validation subset from the public EnviDat Output archive and optional EOTA shape archive:

```bash
python3 scripts/download_datasets.py \
  --dataset chant_sura_2020 \
  --resource output_archive \
  --resource eota
python3 scripts/preprocess_datasets.py --dataset chant_sura_2020
```

This writes:

- `data/processed/chant_sura_2020/release_points.csv`
- `data/processed/chant_sura_2020/observed_trajectories.csv`
- `data/processed/chant_sura_2020/block_metadata.csv`
- `data/processed/chant_sura_2020/rock_shapes.csv` when `eota.7z` is present
- a small checked-in validation subset under `validation/data/processed/chant_sura_2020/`

The checked-in Chant Sura first-flight subset uses three reconstructed trajectory text files from `Output.7z`: `RF16W200r1`, `RF16W800r1`, and `RF18W200r1`. Only the first monotonic time segment is used because the public output files concatenate jump segments with local time resets. Mass is inferred from the published `Ekin` and speed columns, and equivalent sphere radii are inferred using density `2670 kg/m3`.

The DEM-backed contact subset uses the first three local-time-reset segments from `RF16W200r1` plus a small ASCII-grid crop derived from `Input/UAS/2018_06_20_RF16/20180619_Chant_Sura_DEM_0.05m.tif`. The full `Input.7z` archive is large and remains ignored raw data. Only the tiny derived `terrain_rf16_contact.asc` fixture is committed. Segment boundaries are treated as contact/rebound proxies and must not be interpreted as full-campaign field validation.

Create the Chant Sura real impact-level scarring calibration subset from public ESurf 2019 table downloads:

```bash
python3 scripts/preprocess_scarring_real_data.py
```

This writes `calibration/data/scarring_single_impact/chant_sura_esurf_2019_impacts.csv` and metadata next to it. The table downloads are cached under `data/raw/chant_sura_2020/` and remain ignored by git. The conversion infers an effective normal/tangential impact split from published jump height and resultant speed; this is documented in `docs/scarring_real_data_calibration.md`.

## Real-World Validation Status

`validation/cases/chant_sura_trajectory_subset.yaml` is the primary trajectory/physics validation fixture. It compares short reconstructed Chant Sura flight segments against simulated trajectory shape, translational kinetic-energy evolution, and proxy jump-height metrics. It does not validate full runout, deposition, or shape effects.

`validation/cases/tschamut_basic.yaml` is active with the small processed Tschamut subset under `validation/data/processed/tschamut/`. It uses the IDW residual DEM with opt-in clamped boundary access. `validation/cases/tschamut_proxy_plane.yaml` keeps the earlier fitted-plane approximation as an explicit comparison case. Both compare ensemble-level runout and deposition-cloud summaries only.

The current simulator is not yet physically rich enough for full calibrated comparison against shape-sensitive field experiments. Chant Sura trajectory results, Lu/ESurf scarring calibration, and Tschamut deposition results should be interpreted as complementary plausibility and deficiency checks, not as operational validation.

The Chant Sura contact-validation fixtures now include both the original
two-event RF16W200r1 subset and an extended multi-trajectory subset with 16
segments and 11 segment-boundary contact/rebound proxies inside the small RF16
DEM crop. The extended subset is intended for contact-model comparison only; it
does not change the separation between validation and calibration.

## Rules

- Use only public datasets.
- Preserve raw downloads.
- Do not overwrite raw data.
- Do not commit large raw archives.
- Do not tune parameters secretly to match one dataset.
- Keep calibration, verification, and validation separate.
