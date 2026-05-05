# Calibration

Calibration experiments are separate from verification and validation. They may use public observations to estimate model parameters, but they must not modify validation cases or claim predictive skill.

Current experiment:

- `experiments/tschamut_v0_3/`: controlled historical Tschamut v0.3.0 grid-search calibration. It remains reproducible as a v0.3.0 artifact and does not use v0.4.0 `scarring_contact_v1`.
- `experiments/scarring_single_impact_v0_4/`: controlled single-impact `scarring_contact_v1` parameter-recovery experiment using a semi-empirical proxy dataset. It is not field validation and must not be used as a trajectory-level parameter set.
- `experiments/scarring_single_impact_chant_sura_esurf_2019_v0_4/`: exploratory single-impact `scarring_contact_v1` calibration using public Chant Sura scar dimensions and jump-energy table data from Caviezel et al. 2019. It is real-data calibration, not validation, and the impact components are inferred.

Generated intermediate reports and temporary cases belong under `calibration/results/` and are ignored by git. Small, reproducible experiment definitions, dataset splits, and final summaries are committed under `calibration/experiments/` and `calibration/data/`.
