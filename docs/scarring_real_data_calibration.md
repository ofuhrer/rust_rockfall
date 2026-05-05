# Scarring Real-Data Single-Impact Calibration

This document describes the first real-data augmentation of the `scarring_contact_v1` single-impact calibration workflow. It is exploratory impact-level calibration, not validation, not trajectory calibration, and not operational parameter selection.

## Data Source

The subset is derived from public Chant Sura / Flueelapass rockfall experiment material:

- Dataset: Caviezel et al. (2020), *Induced Rockfall Dataset #2 (Chant Sura Experimental Campaign)*, EnviDat DOI `10.16904/envidat.174`.
- Publication tables: Caviezel et al. (2019), *Reconstruction of four-dimensional rockfall trajectories using remote sensing and rock-based accelerometers and gyroscopes*, Earth Surface Dynamics, DOI `10.5194/esurf-7-199-2019`.
- Source table files:
  - `https://esurf.copernicus.org/articles/7/199/2019/esurf-7-199-2019-t01.xlsx`
  - `https://esurf.copernicus.org/articles/7/199/2019/esurf-7-199-2019-t02.xlsx`

The committed derived calibration file is:

```text
calibration/data/scarring_single_impact/chant_sura_esurf_2019_impacts.csv
```

The preprocessing script is:

```bash
python3 scripts/preprocess_scarring_real_data.py
```

Raw downloaded table files are stored under `data/raw/chant_sura_2020/` and remain ignored by git.

## Usable Subset

The first subset contains six impact transitions from the published RF16/RF18 EOTA221 runs:

```text
21->22, 22->23, 23->24, 41->42, 42->43, 43->44
```

Each transition is linked to a mapped scar from the publication table. The calibration CSV includes:

- reconstructed incoming total speed;
- effective normal and tangential speed components;
- mapped ADM scar depth;
- pre-impact translational energy;
- post-rebound translational energy from the beginning of the next jump;
- total translational energy change across the contact transition.

## Preprocessing Assumptions

The source tables do not directly provide terrain-normal impact components or isolated scarring work. The following assumptions are therefore explicit:

- EOTA221 mass is treated as `780 kg`.
- The simulator uses an equivalent-volume sphere radius computed from `780 kg` and concrete density `2400 kg/m3`.
- Effective normal impact speed is inferred from published jump height as `sqrt(2 g JH)`.
- Effective tangential speed is the remaining component of the published resultant impact speed.
- ADM scar depth is used as the depth target because it is derived from UAS altitude-difference mapping.
- Observed post-rebound energy is the beginning translational energy of the next published jump.
- Observed total translational energy loss is not pure scarring. It includes restitution, terrain interaction, block shape, reconstruction uncertainty, and possible terrain-elevation effects.

For that reason, `observed_scarring_energy_loss_j` is intentionally left blank in the real-data CSV. The calibration objective uses scar depth and post-rebound translational energy instead.

## Calibration Experiment

Run:

```bash
python3 scripts/calibrate_scarring_impact.py \
  --config calibration/experiments/scarring_single_impact_chant_sura_esurf_2019_v0_4/config.yaml
```

Committed summary artifacts are:

- `calibration/experiments/scarring_single_impact_chant_sura_esurf_2019_v0_4/candidate_results.csv`
- `calibration/experiments/scarring_single_impact_chant_sura_esurf_2019_v0_4/selected_parameters.yaml`
- `calibration/experiments/scarring_single_impact_chant_sura_esurf_2019_v0_4/summary.json`
- `calibration/experiments/scarring_single_impact_chant_sura_esurf_2019_v0_4/report.html`

The objective is:

```text
objective =
  0.6 * mean_relative_depth_error
+ 0.4 * mean_relative_post_rebound_energy_error
```

## Results

The best candidate in the current grid is:

```text
soil_strength_pa = 500000
scarring_drag_coefficient = 1.0
scarring_layer_density_kgpm3 = 1200
objective = 1.4183
mean_relative_depth_error = 2.1328
mean_relative_post_rebound_energy_error = 0.3466
```

This is not a good physical fit. The energy target is matched moderately for some impacts, but the scar depths are systematically overpredicted:

| impact | depth observed (m) | depth simulated (m) | post-rebound energy observed (J) | post-rebound energy simulated (J) |
| --- | ---: | ---: | ---: | ---: |
| `chant_sura_2_1` | `0.10` | `0.427` | `53800` | `60385` |
| `chant_sura_2_2` | `0.12` | `0.274` | `120800` | `49352` |
| `chant_sura_2_3` | `0.08` | `0.131` | `97200` | `146934` |
| `chant_sura_4_1` | `0.05` | `0.312` | `135100` | `154136` |
| `chant_sura_4_2` | `0.08` | `0.175` | `95300` | `140744` |
| `chant_sura_4_3` | `0.16` | `0.350` | `89300` | `68206` |

## Identifiability

The real-data subset does not separate `scarring_drag_coefficient` from `scarring_layer_density_kgpm3`. In the current model, drag work depends on the product `Cd * rho`, so these two parameters remain structurally confounded unless one is fixed from independent measurements.

Soil strength is identifiable only through the model's depth relation, but the current relation overpredicts the mapped Chant Sura scar depths for the equivalent-sphere assumption. This points to structural model mismatch rather than a simple parameter-search issue.

## Comparison To Proxy Calibration

The proxy calibration recovers its known parameter set exactly because the targets were generated from the same model equations. The Chant Sura real-data experiment does not recover a clean fit. That is the scientifically useful result:

- the workflow can ingest public impact/scar observations;
- impact-level diagnostics are sufficient to compute objective values;
- the minimal model cannot jointly explain mapped scar depths and rebound energies with the current assumptions;
- calibration should not proceed to trajectory-level fitting until the impact-normal inference, shape proxy, and scarring depth law are improved or independently constrained.

## Limitations

- The impact normal is inferred, not directly measured.
- The EOTA block is non-spherical, but the simulator uses an equivalent sphere.
- Published energy transitions include more than scarring.
- Some transitions show apparent translational energy gain in the published table, which can arise from terrain geometry, reconstruction choices, or exchange with rotation; the current single-impact flat-plane setup cannot represent this fully.
- The selected parameters must not be used in Tschamut validation or as model defaults.

## Next Step

The next calibration step should fix or independently constrain either `scarring_layer_density_kgpm3` or `scarring_drag_coefficient`, then revisit the scar-depth law using direct terrain-normal impact estimates from reconstructed trajectories or DEM normals. Without that, the single-impact calibration is informative but underdetermined.
