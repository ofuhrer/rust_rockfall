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

Downloaded files go to `data/raw/<dataset_id>/` and retain original filenames. A JSONL manifest records URL, date, size, and SHA-256 checksum.

## Preprocessing

Create the synthetic fixture:

```bash
python3 scripts/preprocess_datasets.py --dataset synthetic_plane_basic
```

Inventory downloaded ZIP archives:

```bash
python3 scripts/preprocess_datasets.py --dataset tschamut2014
```

Dataset-specific conversions should write validation-ready CSV/GeoJSON under `data/processed/<dataset_id>/` and must document CRS, units, and inferred fields.

## Real-World Validation Status

`validation/cases/tschamut_basic.yaml` is a scaffold. It skips gracefully until `data/processed/tschamut2014/deposition_points.csv` exists.

The current simulator is not yet physically rich enough for calibrated comparison against shape-sensitive field experiments. The first real-data use should be qualitative runout/deposition checks on simple Tschamut cases, with calibration choices recorded separately.

## Rules

- Use only public datasets.
- Preserve raw downloads.
- Do not overwrite raw data.
- Do not commit large raw archives.
- Do not tune parameters secretly to match one dataset.
- Keep calibration, verification, and validation separate.

