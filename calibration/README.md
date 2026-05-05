# Calibration

Calibration experiments are separate from verification and validation. They may use public observations to estimate model parameters, but they must not modify validation cases or claim predictive skill.

Current experiment:

- `experiments/tschamut_v0_3/`: controlled Tschamut v0.3.0 grid-search calibration.

Generated intermediate reports and temporary cases belong under `calibration/results/` and are ignored by git. Small, reproducible experiment definitions, dataset splits, and final summaries are committed under `calibration/experiments/` and `calibration/data/`.
