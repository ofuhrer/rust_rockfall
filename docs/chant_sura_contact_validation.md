# Chant Sura DEM-Backed Contact Validation

Status: active v0.6.0 validation experiment. This document describes a small DEM-backed trajectory/contact fixture and model-comparison cases. It does not change simulation physics and does not claim operational validity.

## Purpose

The original Chant Sura validation case, `validation/cases/chant_sura_trajectory_subset.yaml`, is intentionally clean but mostly ballistic: it compares short first-flight reconstructed trajectory segments against constant-gravity simulation on a flat clearance proxy. That case is useful for kinematics, but it cannot constrain contact, roughness, scarring, or future shape models.

The new contact experiment adds a small real-terrain fixture:

- `validation/cases/chant_sura_contact.yaml`
- `validation/cases/chant_sura_contact_rotational.yaml`
- `validation/cases/chant_sura_contact_roughness.yaml`
- `validation/cases/chant_sura_contact_scarring.yaml`
- `validation/cases/chant_sura_contact_extended.yaml`
- `validation/cases/chant_sura_contact_extended_rotational.yaml`
- `validation/cases/chant_sura_contact_extended_roughness.yaml`
- `validation/cases/chant_sura_contact_extended_scarring.yaml`
- `validation/cases/chant_sura_contact_heldout.yaml`
- `validation/cases/chant_sura_contact_heldout_rotational.yaml`

These cases keep the first-flight subset unchanged. The original contact fixture uses a separate RF16W200r1 segmented fixture; the extended fixture uses five source trajectories whose early segments remain inside the RF16 DEM crop; the held-out fixture uses six disjoint source trajectories to test whether the `sphere_rotational_v1` recommendation generalizes. The core contact diagnostics are impact timing, rebound velocity, and post-impact energy change.

## Data And Terrain

Source dataset: Caviezel et al. (2020), Induced Rockfall Dataset #2 (Chant Sura Experimental Campaign), EnviDat DOI `10.16904/envidat.174`.

Raw public inputs:

- `Output/txt/RF16W200r1.txt`: reconstructed trajectory with local time resets between flight/jump segments.
- `Input/UAS/2018_06_20_RF16/20180619_Chant_Sura_DEM_0.05m.tif`: RF16 UAS DEM.

Checked-in derived fixture:

- `validation/data/processed/chant_sura_2020/terrain_rf16_contact.asc`
- `validation/data/processed/chant_sura_2020/release_points_contact.csv`
- `validation/data/processed/chant_sura_2020/observed_trajectories_contact.csv`
- `validation/data/processed/chant_sura_2020/observed_contact_events.csv`
- `validation/data/processed/chant_sura_2020/metadata_contact.json`
- `validation/data/processed/chant_sura_2020/terrain_rf16_contact_extended.asc`
- `validation/data/processed/chant_sura_2020/release_points_contact_extended.csv`
- `validation/data/processed/chant_sura_2020/observed_trajectories_contact_extended.csv`
- `validation/data/processed/chant_sura_2020/observed_contact_events_extended.csv`
- `validation/data/processed/chant_sura_2020/metadata_contact_extended.json`
- `validation/data/processed/chant_sura_2020/terrain_rf16_contact_heldout.asc`
- `validation/data/processed/chant_sura_2020/release_points_contact_heldout.csv`
- `validation/data/processed/chant_sura_2020/observed_trajectories_contact_heldout.csv`
- `validation/data/processed/chant_sura_2020/observed_contact_events_heldout.csv`
- `validation/data/processed/chant_sura_2020/metadata_contact_heldout.json`
- `validation/data/processed/chant_sura_2020/metadata_contact_split.json`

The terrain crop is a small ESRI ASCII grid derived with `gdal_translate` from the public RF16 UAS DEM. The source GeoTIFF reports EPSG:2056 / CH1903+ LV95. Heights are in metres and are treated as source DEM elevations without vertical transformation. The fixture uses the trajectory coordinates directly because both the DEM and reconstructed trajectory use LV95-scale coordinates.

## Coordinate And Height Alignment

The simulator treats `position_m` as the sphere centre of mass. The reconstructed Chant Sura output z values lie close to the DEM surface near the release and segment boundaries. To make the observations compatible with the current sphere-contact convention:

- `raw_z_m` preserves the public reconstructed z value.
- `z_m` is `raw_z_m + equivalent_sphere_radius_m`.
- `z_offset_applied_m` records the applied offset.

This is a modelling alignment for the current sphere approximation, not a coordinate-reference transformation. It should be revisited when non-spherical shapes or measured centre-of-mass trajectories are supported.

## Segmentation

The RF16W200r1 text file concatenates multiple local-time segments. Local `time` resets are treated as segment boundaries. The fixture uses the first three segments:

- `RF16W200r1_seg00`
- `RF16W200r1_seg01`
- `RF16W200r1_seg02`

The two boundaries are recorded as observed contact/rebound proxies:

- `RF16W200r1_impact_00`: segment 00 to segment 01
- `RF16W200r1_impact_01`: segment 01 to segment 02

These are not exact instrumented impact events. They are reconstructed segment transitions suitable for model-comparison diagnostics.

The extended fixture adds segments selected from:

- `RF16W200r1`
- `RF16W200r3`
- `RF18W200r1`
- `RF18W800r6`
- `RF20e200r1`

It includes 16 reconstructed flight segments, 816 trajectory samples, and 11 segment-boundary contact/rebound proxies. Segment detection still uses local time resets, but segments are retained only when at least 90% of samples fall within the small RF16 DEM crop. This gives more impact-angle, velocity, and mass variation while keeping the fixture small enough for regular validation runs.

The held-out fixture uses disjoint source trajectories:

- `RF16W200r2`
- `RF18W200r4`
- `RF20e200r2`
- `RF20e200r5`
- `RF16W800r2`
- `RF18W800r1`

It includes 15 reconstructed flight segments, 765 trajectory samples, and 9 segment-boundary contact/rebound proxies. The split is persisted in `metadata_contact_split.json`; no held-out trajectory ID overlaps the model-selection subset.

### Holdout Evidence Manifest

The held-out boundary is also captured in a read-only machine-readable manifest:

- `validation/data/processed/chant_sura_2020/holdout_validation_evidence_manifest.json`
- `scripts/summarize_chant_sura_holdout_evidence.py`

That manifest separates diagnostic/model-selection evidence from independent holdout-validation evidence. It remains explicit that the evidence is contact / trajectory validation only, not calibration, not physical probability, and not operational use.

## Metrics

The case reports existing trajectory metrics:

- `trajectory_shape_mean_error_m`
- `trajectory_shape_p95_error_m`
- `trajectory_shape_max_error_m`
- `trajectory_final_position_mean_error_m`
- `trajectory_energy_mean_relative_error`
- `trajectory_max_jump_height_mean_error_m`

It also adds contact-aware metrics:

- `trajectory_jump_height_envelope_error_m`
- `observed_contact_event_count`
- `contact_event_compared_count`
- `impact_timing_mean_error_s`
- `impact_timing_p95_error_s`
- `rebound_velocity_mean_error_mps`
- `rebound_velocity_p95_error_mps`
- `post_impact_energy_change_mean_error_j`

For each observed contact proxy, the validator simulates the source segment from the matching release row, finds the first significant simulated impact event, and compares timing, outgoing velocity, and translational kinetic-energy change against the next observed segment.

## Initial Model-Comparison Results

The following values were produced by `cargo run -- validate --case ...` during fixture integration. They are diagnostic comparisons, not calibrated acceptance claims.

| Case | Contact / soil option | Shape mean error (m) | Energy relative error | Jump envelope error (m) | Impact timing mean error (s) | Rebound velocity mean error (m/s) |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `validation_chant_sura_contact` | `translational_v0` | 0.418 | 0.394 | 0.731 | 0.628 | 4.899 |
| `validation_chant_sura_contact_rotational` | `sphere_rotational_v1` | 0.378 | 0.289 | 0.750 | 0.628 | 4.902 |
| `validation_chant_sura_contact_roughness` | `stochastic_contact_v1` | 0.437 | 0.429 | 0.748 | 0.660 | 4.917 |
| `validation_chant_sura_contact_scarring` | `scarring_contact_v1` | 0.431 | 0.426 | 0.707 | 0.628 | 4.892 |

The rotational sphere model improves the mean trajectory-shape and energy metrics in this small subset, while roughness and scarring do not improve the same metrics. Scarring slightly lowers the jump-height envelope error, consistent with its dissipative role, but this should not be overinterpreted because the fixture has only two contact proxies and no shape-aware dynamics.

Extended fixture results:

| Case | Contact / soil option | Shape mean error (m) | Energy relative error | Jump envelope error (m) | Impact timing mean error (s) | Rebound velocity mean error (m/s) |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `validation_chant_sura_contact_extended` | `translational_v0` | 0.563 | 0.498 | 0.713 | 0.683 | 4.281 |
| `validation_chant_sura_contact_extended_rotational` | `sphere_rotational_v1` | 0.529 | 0.427 | 0.742 | 0.683 | 4.355 |
| `validation_chant_sura_contact_extended_roughness` | `stochastic_contact_v1` | 0.564 | 0.502 | 0.700 | 0.690 | 4.241 |
| `validation_chant_sura_contact_extended_scarring` | `scarring_contact_v1` | 0.576 | 0.514 | 0.746 | 0.683 | 4.263 |

The extended fixture preserves the main conclusion: `sphere_rotational_v1` improves trajectory shape and kinetic-energy evolution, but it does not improve rebound velocity or jump-height envelope. Roughness and scarring affect individual contact metrics but do not improve shape or energy in this uncalibrated comparison. The larger event count makes this ranking less dependent on the original two contact proxies, but it is still not a formal statistical significance test.

Held-out fixture results:

| Case | Contact option | Shape mean error (m) | Energy relative error | Jump envelope error (m) | Impact timing mean error (s) | Rebound velocity mean error (m/s) |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `validation_chant_sura_contact_heldout` | `translational_v0` | 0.505 | 0.440 | 0.713 | 0.474 | 4.099 |
| `validation_chant_sura_contact_heldout_rotational` | `sphere_rotational_v1` | 0.475 | 0.391 | 0.744 | 0.477 | 4.150 |

The held-out result supports generalization of the trajectory-level improvement: rotational contact again lowers shape and kinetic-energy error. It still does not improve jump-height envelope, rebound velocity, or impact timing, so it strengthens the opt-in recommendation without justifying a default change.

## Diagnostic Summary Workflow

The contact diagnostics can be consolidated without rerunning simulations:

```bash
python3 scripts/summarize_chant_sura_contact_diagnostics.py \
  --output-root validation/results/chant_sura_contact_diagnostics
```

Generated ignored artifacts:

- `validation/results/chant_sura_contact_diagnostics/chant_sura_contact_diagnostics.json`
- `validation/results/chant_sura_contact_diagnostics/chant_sura_contact_diagnostics.md`

The summary reads existing `validation/results/chant_sura_contact*metrics.json`
files and the checked-in processed contact-proxy CSV files. It does not tune
parameters or recompute trajectories. Its purpose is to keep the diagnostic
structure explicit before any future shape/contact implementation:

- trajectory-shape and kinetic-energy metrics are the strongest current evidence
  for the opt-in `sphere_rotational_v1` trajectory/contact recommendation;
- rebound velocity, jump-height envelope, and impact timing remain proxy-limited
  and do not show a robust rotational improvement;
- segment-boundary contact events are labelled as local-time-reset proxies, not
  direct impact-sensor observations;
- the held-out subset remains the most important guard against selecting and
  evaluating a model on the same Chant Sura trajectories.

## Interpretation

This fixture answers a narrower question than full field validation:

> Given a real DEM patch and reconstructed segment boundaries, which currently implemented model options materially change trajectory/contact metrics?

The current answer is that contact-model choice now affects the reported Chant Sura trajectory metrics. That is a useful change from the first-flight subset, where contact options were mostly invisible.

Across the extended fixture, the clearest trajectory-level improvement comes from `sphere_rotational_v1`; the strongest contact-level improvements are mixed and metric-specific. This supports using rotational contact as the recommended opt-in model for trajectory/contact experiments while retaining `translational_v0` as the stable default.

The remaining errors are scientifically meaningful:

- Rebound velocity errors remain several metres per second, indicating that the simple restitution/friction sphere model cannot reproduce observed segment-to-segment velocity changes.
- Impact timing errors are substantial relative to segment duration, which may reflect DEM/trajectory alignment, the centre-of-mass offset assumption, terrain interpolation, or missing shape/contact physics.
- Scarring parameters transferred from impact-level calibration do not create a trajectory-level improvement in this subset.

## Limitations

- The original RF16W200r1 contact fixture includes only one trajectory and two segment-boundary contact proxies.
- The extended fixture improves coverage to five trajectories and 11 contact proxies, and the held-out fixture adds six disjoint trajectories and 9 contact proxies, but both remain small subsets constrained to one DEM crop.
- Segment boundaries are inferred from local time resets, not from a direct impact sensor event table.
- The fixture uses an equivalent sphere and cannot represent EOTA rock shape.
- The full public Input archive is large and remains ignored raw data.
- The DEM crop is checked in only as a small validation fixture; it is not a production terrain workflow.
- The comparison is deterministic and reproducible, but not calibrated and not operational.

## Next Steps

Recommended next scientific work:

1. Add more Chant Sura segments and trajectories only after the current small fixture remains stable and interpretable.
2. Include observed impact/sensor timing if a public table can be processed consistently.
3. Use this fixture to evaluate the first shape-aware model once a non-spherical representation exists.
4. Revisit the vertical alignment assumption when measured centre-of-mass or shape-specific contact-point data are available.
