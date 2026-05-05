# Scarring Single-Impact Calibration

This document describes the first controlled single-impact calibration experiment for `scarring_contact_v1`. It is an impact-level parameter-recovery and sensitivity exercise. It is not trajectory calibration, not validation, and not operational calibration.

For the later real-data augmentation using public Chant Sura / ESurf 2019 table data, see `scarring_real_data_calibration.md`.

## Dataset

No committed repository dataset currently provides public impact-level scar measurements with all of the following fields:

- incoming impact velocity;
- rebound/contact-response velocity;
- scar depth or scar geometry;
- impact-level energy loss.

The first experiment therefore uses a small semi-empirical proxy dataset:

- data file: `calibration/data/scarring_single_impact/reference_impacts.csv`
- experiment config: `calibration/experiments/scarring_single_impact_v0_4/config.yaml`
- source: proxy targets derived from the documented v0.4.0 scarring depth and drag-work equations
- status: repository test/calibration fixture, not observational field data

The proxy dataset contains three flat-plane impacts:

| impact | normal speed (m/s) | tangential speed (m/s) | target scar depth (m) | target scarring loss (J) |
| --- | ---: | ---: | ---: | ---: |
| low | `3.0` | `0.75` | `0.085304` | `1.599672` |
| moderate | `5.5` | `1.5` | `0.138537` | `13.504836` |
| high | `8.0` | `2.5` | `0.186959` | `50.175482` |

The reference targets intentionally correspond to a known parameter set:

```text
soil_strength_pa = 500000
scarring_drag_coefficient = 0.01
scarring_layer_density_kgpm3 = 1600
```

This makes the experiment a transparent parameter-recovery test. It checks whether the impact-event workflow can recover a known impact-level parameter set and expose sensitivity, not whether the parameters are valid for field prediction.

## Calibration Targets

The objective uses two impact-level quantities from `ImpactEvent`:

- `scarring_depth_m`
- `scarring_capped_energy_loss_j`

These were chosen because they are directly tied to the minimal scarring model:

- soil strength controls computed scar depth through the empirical depth relation;
- drag coefficient and layer density control velocity-squared drag work and therefore energy loss;
- both quantities can be reconstructed per impact without relying on trajectory runout.

Rebound velocity is inspected indirectly through `post_contact_translational_j` and `post_scarring_translational_j`, but it is not a target in this first objective.

## Parameter Space

The explicit grid is deliberately small:

| parameter | values |
| --- | --- |
| `soil_strength_pa` | `250000`, `500000`, `1000000` |
| `scarring_drag_coefficient` | `0.005`, `0.01`, `0.02` |
| `scarring_layer_density_kgpm3` | `1200`, `1600`, `2000` |

The experiment evaluates `27` candidates across `3` impacts. All runs are deterministic.

## Objective Function

For each candidate, each impact is simulated as a controlled flat-plane single-impact case. The first significant `ImpactEvent` is extracted and compared with the proxy target.

The scalar objective is:

```text
objective =
  0.55 * mean_relative_depth_error
+ 0.45 * mean_relative_energy_loss_error
```

where each relative error uses a small epsilon guard of `1e-9`. Lower is better.

## Reproduction

Run:

```bash
python3 scripts/calibrate_scarring_impact.py
```

The script writes ignored intermediate single-impact configs, trajectories, and impact-event logs under:

```text
calibration/results/scarring_single_impact_v0_4/
```

Committed summary artifacts are:

- `calibration/experiments/scarring_single_impact_v0_4/candidate_results.csv`
- `calibration/experiments/scarring_single_impact_v0_4/selected_parameters.yaml`
- `calibration/experiments/scarring_single_impact_v0_4/summary.json`
- `calibration/experiments/scarring_single_impact_v0_4/report.html`

## Results

The best candidate is:

```text
soil_strength_pa = 500000
scarring_drag_coefficient = 0.01
scarring_layer_density_kgpm3 = 1600
objective ~= 0
```

This recovers the known proxy parameter set. The best-candidate impact comparison is:

| impact | depth target (m) | depth sim (m) | loss target (J) | loss sim (J) | loss / post-contact energy |
| --- | ---: | ---: | ---: | ---: | ---: |
| low | `0.085304` | `0.085304` | `1.599672` | `1.599672` | `0.03465` |
| moderate | `0.138537` | `0.138537` | `13.504836` | `13.504836` | `0.08355` |
| high | `0.186959` | `0.186959` | `50.175482` | `50.175482` | `0.13602` |

The top neighboring candidates show the expected sensitivity:

- Keeping `soil_strength_pa = 500000` preserves depth exactly.
- Changing layer density from `1600` to `1200` or `2000` changes energy loss by about `25%` while leaving depth unchanged.
- Changing soil strength affects depth and can partly compensate energy through scar area, but it produces systematic depth error.
- `scarring_drag_coefficient` and `scarring_layer_density_kgpm3` are not independently identifiable from energy loss alone because the current force law depends on their product `Cd * rho`.

## Interpretation

This experiment confirms that the impact-event instrumentation is sufficient for a minimal calibration loop:

- controlled single-impact simulations can be generated deterministically;
- the first significant `ImpactEvent` can be extracted reliably;
- scar depth and scarring energy loss can be compared per impact;
- the objective recovers a known proxy parameter set;
- parameter sensitivities match the model equations.

The result is intentionally circular because the proxy targets are generated from the same model family. That is acceptable for this first step because the purpose is workflow validation and interpretability, not field calibration.

## Limitations

- The dataset is synthetic/semi-empirical, not measured scar data.
- No Lu 2019 or Chant Sura scar-depth observations are committed in this repository.
- The result is single-impact only and must not be applied to Tschamut validation.
- The experiment does not calibrate terrain classes, drag torque, slip-dependent friction, roughness, or block shape.
- `Cd` and layer density remain structurally confounded in this minimal force law.

## Next Step

The next scientific step is to replace or augment the proxy dataset with public impact-level measurements, ideally including scar geometry and pre/post-impact velocities. Until that exists, `scarring_contact_v1` should not be calibrated against full trajectories or operational hazard outputs.
