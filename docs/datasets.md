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

The checked-in Chant Sura subset uses three reconstructed trajectory text files from `Output.7z`: `RF16W200r1`, `RF16W800r1`, and `RF18W200r1`. Only the first monotonic time segment is used because the public output files concatenate jump segments with local time resets. Mass is inferred from the published `Ekin` and speed columns, and equivalent sphere radii are inferred using density `2670 kg/m3`. The `Input.7z` DEM is large and remains optional/raw-only for now, so the current validation case uses an explicit flat clearance-plane proxy and must not be interpreted as DEM-based field validation.

Create the Chant Sura real impact-level scarring calibration subset from public ESurf 2019 table downloads:

```bash
python3 scripts/preprocess_scarring_real_data.py
```

This writes `calibration/data/scarring_single_impact/chant_sura_esurf_2019_impacts.csv` and metadata next to it. The table downloads are cached under `data/raw/chant_sura_2020/` and remain ignored by git. The conversion infers an effective normal/tangential impact split from published jump height and resultant speed; this is documented in `docs/scarring_real_data_calibration.md`.

## Real-World Validation Status

`validation/cases/chant_sura_trajectory_subset.yaml` is the primary trajectory/physics validation fixture. It compares short reconstructed Chant Sura flight segments against simulated trajectory shape, translational kinetic-energy evolution, and proxy jump-height metrics. It does not validate full runout, deposition, or shape effects.

`validation/cases/tschamut_basic.yaml` is active with the small processed Tschamut subset under `validation/data/processed/tschamut/`. It uses the IDW residual DEM with opt-in clamped boundary access. `validation/cases/tschamut_proxy_plane.yaml` keeps the earlier fitted-plane approximation as an explicit comparison case. Both compare ensemble-level runout and deposition-cloud summaries only.

The current simulator is not yet physically rich enough for full calibrated comparison against shape-sensitive field experiments. Chant Sura trajectory results, Lu/ESurf scarring calibration, and Tschamut deposition results should be interpreted as complementary plausibility and deficiency checks, not as operational validation.

## Rules

- Use only public datasets.
- Preserve raw downloads.
- Do not overwrite raw data.
- Do not commit large raw archives.
- Do not tune parameters secretly to match one dataset.
- Keep calibration, verification, and validation separate.
