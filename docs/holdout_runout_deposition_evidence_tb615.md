# TB-615 Holdout Runout/Deposition Evidence

TB-615 stages a small Chant Sura held-out runout-axis benchmark intake at the
existing observed runout/deposition benchmark path:

- `validation/data/processed/observed_runout_deposition_benchmark/manifest.json`
- `validation/data/processed/observed_runout_deposition_benchmark/observed_runout_deposition.geojson`

The record uses six held-out Chant Sura trajectories as runout-axis proxies:
`RF16W200r2`, `RF16W800r2`, `RF18W200r4`, `RF18W800r1`,
`RF20e200r2`, and `RF20e200r5`. It points back to the public EnviDat dataset,
the local held-out trajectory CSV, the existing holdout split manifest, and the
existing calibration-separation checks.

The intake is design-review evidence. It closes the local independent-holdout
class in `scripts/assess_validation_calibration_evidence_gaps.py` when the
staged benchmark, held-out split audit, and calibration-separation preflight
all pass. It does not add a deposition-footprint polygon, calibration result,
physical-probability product, annual-frequency product, operational map, risk,
exposure, vulnerability, Swiss-wide execution, distributed execution, or
non-`postproc` claim.

Current result:

- observed runout/deposition intake status: `ready`
- observed deposition/runout evidence category: `present`
- holdout and validation evidence category: `present`
- remaining physical-probability blockers: `release_probability_model`,
  `block_population_evidence`, and `calibration_evidence`

Focused checks:

```bash
PYENV_VERSION=system uv run python scripts/summarize_observed_runout_deposition_intake_contract.py --format json
PYENV_VERSION=system uv run python scripts/audit_chant_sura_holdout_split.py --format json
PYENV_VERSION=system uv run python scripts/check_calibration_separation_preflight.py --format json
PYENV_VERSION=system uv run python scripts/assess_validation_calibration_evidence_gaps.py --format json
PYENV_VERSION=system uv run python -m unittest tests.test_observed_runout_deposition_intake_contract tests.test_validation_calibration_evidence_gaps -v
```
