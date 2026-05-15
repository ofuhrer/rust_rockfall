# Chant Sura Contact Generalization

Status: active v0.6.0 held-out validation experiment. This document evaluates whether the `sphere_rotational_v1` improvement observed on the Chant Sura contact model-selection subset generalizes to independent Chant Sura trajectories. It does not change simulation physics, validation semantics, calibration, or model defaults.

## Purpose

The original and extended Chant Sura contact fixtures showed that `sphere_rotational_v1` improves trajectory-shape and kinetic-energy metrics relative to `translational_v0`, but those same fixtures were already used to decide that rotational contact should be recommended for trajectory/contact experiments.

This held-out experiment asks a narrower robustness question:

> Does the rotational improvement persist on disjoint Chant Sura trajectories that were not used for the contact-model recommendation?

## Deterministic Split

The split is trajectory-level, deterministic, and stored in:

- `validation/data/processed/chant_sura_2020/metadata_contact_split.json`
- `data/processed/chant_sura_2020/metadata_contact_split.json`

Model-selection trajectories:

- `RF16W200r1`
- `RF16W200r3`
- `RF18W200r1`
- `RF18W800r6`
- `RF20e200r1`

Held-out evaluation trajectories:

- `RF16W200r2`
- `RF18W200r4`
- `RF20e200r2`
- `RF20e200r5`
- `RF16W800r2`
- `RF18W800r1`

There is no trajectory ID overlap between the two subsets. Both subsets are constrained to early local-time-reset segments with at least 90% of samples inside the same checked-in RF16 DEM crop. The split is not random; it is an intentionally reproducible small-fixture split that keeps W200 and W800 mass classes in the held-out subset where available.

## Held-Out Fixture

Checked-in held-out files:

- `validation/data/processed/chant_sura_2020/terrain_rf16_contact_heldout.asc`
- `validation/data/processed/chant_sura_2020/release_points_contact_heldout.csv`
- `validation/data/processed/chant_sura_2020/observed_trajectories_contact_heldout.csv`
- `validation/data/processed/chant_sura_2020/observed_contact_events_heldout.csv`
- `validation/data/processed/chant_sura_2020/metadata_contact_heldout.json`

Validation cases:

- `validation/cases/chant_sura_contact_heldout.yaml`
- `validation/cases/chant_sura_contact_heldout_rotational.yaml`

The held-out fixture contains 15 reconstructed flight segments, 765 trajectory samples, and 9 segment-boundary contact/rebound proxies. Segment boundaries are still proxy events inferred from local time resets, not direct instrumented impact measurements.

### Holdout Evidence Manifest

The split is also recorded in a durable manifest for downstream evidence-gap work:

- `validation/data/processed/chant_sura_2020/holdout_validation_evidence_manifest.json`
- `scripts/summarize_chant_sura_holdout_evidence.py`

This manifest keeps diagnostic/model-selection evidence separate from independent holdout-validation evidence and does not add calibration, physical-probability, or operational claims.

## Results

Model-selection extended subset:

| Case | Contact model | Shape mean error (m) | Energy relative error | Jump envelope error (m) | Impact timing mean error (s) | Rebound velocity mean error (m/s) |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Extended baseline | `translational_v0` | 0.563 | 0.498 | 0.713 | 0.683 | 4.281 |
| Extended rotational | `sphere_rotational_v1` | 0.529 | 0.427 | 0.742 | 0.683 | 4.355 |

Held-out subset:

| Case | Contact model | Shape mean error (m) | Energy relative error | Jump envelope error (m) | Impact timing mean error (s) | Rebound velocity mean error (m/s) |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Held-out baseline | `translational_v0` | 0.505 | 0.440 | 0.713 | 0.474 | 4.099 |
| Held-out rotational | `sphere_rotational_v1` | 0.475 | 0.391 | 0.744 | 0.477 | 4.150 |

Relative held-out changes from `translational_v0` to `sphere_rotational_v1`:

- shape mean error improves by about 6%;
- kinetic-energy relative error improves by about 11%;
- jump-height envelope error worsens by about 4%;
- rebound-velocity mean error worsens by about 1%;
- impact-timing mean error is effectively unchanged, with a small numerical worsening of about 0.003 s.

## Interpretation

The held-out result supports the core conclusion from the model-selection subset: `sphere_rotational_v1` improves the trajectory-level metrics most directly tied to path shape and kinetic-energy evolution. The improvement is smaller than in the original two-event fixture, but similar to the extended model-selection fixture.

The result does not support claiming that rotational contact improves all contact observables. Rebound velocity and jump-height envelope remain slightly worse with `sphere_rotational_v1`, and impact timing is essentially unchanged. Those metrics likely depend on terrain alignment, restitution/friction parameterization, missing non-spherical shape, and the fact that segment-boundary proxies are not direct impact-event measurements.

The practical conclusion is:

- `sphere_rotational_v1` generalizes enough to remain the recommended opt-in contact model for Chant Sura trajectory/contact experiments;
- `translational_v0` should remain the default because the held-out data do not show across-the-board improvement and the dataset is still small;
- future model decisions should use this split to avoid selecting and evaluating on the same trajectory IDs.

## Limitations

- The held-out subset is still constrained to one small RF16 DEM crop.
- The split is deterministic and transparent, but not statistically powered.
- Segment-boundary contacts are proxy events inferred from time resets.
- No parameters were tuned on either subset for this experiment.
- The current sphere model cannot use Chant Sura EOTA shape observations.
- The results are not operational validation and should not be used for hazard assessment.

## Answer

`sphere_rotational_v1` does improve trajectory realism across independent Chant Sura data in the limited sense that held-out shape and kinetic-energy errors are lower than `translational_v0`. The improvement is not universal across all metrics, so the recommendation should be strengthened for trajectory/contact experiments but defaults should not change yet.
