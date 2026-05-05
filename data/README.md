# Validation Data

This directory contains metadata and small validation fixtures for public rockfall datasets.

Large public datasets are not committed. Use `scripts/download_datasets.py` to download selected public resources into `data/raw/<dataset_id>/`, then use `scripts/preprocess_datasets.py` to create validation-ready files under `data/processed/<dataset_id>/`.

## Layout

- `datasets.yaml`: registry of public datasets and resources.
- `raw/`: local-only raw downloads, ignored by git except `.gitkeep`.
- `processed/`: small processed fixtures or reproducible derived outputs.

## Rules

- Download only public resources listed in `datasets.yaml`.
- Preserve original filenames in `data/raw/`.
- Never overwrite raw data during preprocessing.
- Document source URL, DOI, license, and preprocessing steps for every dataset.
- Do not commit large raw files.
- Do not tune simulator parameters secretly to match one dataset.

The included `synthetic_plane_basic` fixture is synthetic and exists only for CI-style validation of data loading and metrics. The checked-in `chant_sura_2020` subset is a small public trajectory-validation fixture; the checked-in `tschamut2014` subset is a deposition/runout validation fixture. See `../docs/dataset_strategy.md` for dataset roles.

Metadata-only swisstopo entries describe future operational input geodata for
Swiss hazard-map workflows. They are not experimental validation datasets and
their raw national products must not be committed. See
`../docs/swisstopo_data_strategy.md` and
`processed/swisstopo/sample_swissalti3d_tile_metadata.yaml`.
