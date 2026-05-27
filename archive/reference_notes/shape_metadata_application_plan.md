# Shape Metadata Application Plan

Status: implemented for public Tschamut per-block passive sidecars; planning for Chant Sura attachment. This plan uses the passive `shape_metadata_v1` scaffold for provenance, grouping, and diagnostics. It does not introduce shape-dependent contact, tune parameters, change defaults, or alter validation semantics.

## Purpose

The passive shape scaffold can now carry block shape, orientation, and mass-property diagnostics through manifests and trajectory metadata while the active contact model remains spherical. The practical next use is to attach public block-shape information to existing validation workflows so later shape-contact work has a traceable data contract.

The immediate scientific value is not improved trajectory prediction. The value is:

- preserving public block mass and dimension provenance next to each run;
- confirming passive metadata is numerically inert;
- grouping existing validation metrics by block ID, mass, equivalent radius, and shape class;
- preparing a clean bridge to future non-spherical contact models.

## Available Shape Information

| Dataset | Public source | Available shape fields | Current local derived records | Missing or uncertain fields |
| --- | --- | --- | --- | --- |
| Public Tschamut 2014 | EnviDat `tschamut2014`, DOI `10.16904/envidat.34` | Block ID, block name, mass, three measured dimensions from `OverviewAllTests.txt`; slope and block scans are public source material | `data/processed/tschamut2014/block_metadata.csv` with blocks 1, 2, and 4, masses, equivalent radii, and `size_x/y/z_m` | Measured orientation at release/impact, center of mass, direct inertia tensor, and a single-shape assignment for mixed-block generated cases |
| Chant Sura 2020 | EnviDat DOI `10.16904/envidat.174` | Block identifier inferred from trajectory IDs, mass/equivalent radius for W200/W800 fixtures; optional EOTA shape files when the archive is available | `validation/data/processed/chant_sura_2020/block_metadata.csv`; optional `rock_shapes.csv` with EOTA point-cloud bounding boxes if `EOTA.7z` has been processed | Guaranteed mapping from each validation trajectory to a specific EOTA shape file, measured initial orientation, direct inertia tensor, and measured per-trajectory mass/density |

The Tschamut overview table is currently the stronger candidate for immediate passive shape sidecars because it contains public per-block dimensions and masses. Chant Sura is useful for equivalent-sphere provenance now, while EOTA-derived non-spherical sidecars should remain catalogued until the trajectory-to-shape mapping is documented.

## Sidecar Strategy

Use small public-data-derived YAML sidecars, one block per `shape_metadata_v1` file. Do not commit raw scans, raw point clouds, large archives, or generated validation outputs.

Recommended committed sidecar locations:

- `data/processed/tschamut2014/shape_metadata/block_1_st_leonard.yaml`
- `data/processed/tschamut2014/shape_metadata/block_2_most_heavy.yaml`
- `data/processed/tschamut2014/shape_metadata/block_4_plate.yaml`
- `validation/data/processed/chant_sura_2020/shape_metadata/W200_equivalent_sphere.yaml`
- `validation/data/processed/chant_sura_2020/shape_metadata/W800_equivalent_sphere.yaml`

For Tschamut, encode measured dimensions as `principal_dimensions` with the explicit box/principal-dimension mass-property model. Include `equivalent_radius_m`, `mass_kg`, a passive identity orientation placeholder, and provenance pointing back to the EnviDat overview table. The shape class should be conservative, for example `principal_dimensions_from_overview`, with optional descriptive labels such as `compact`, `heavy`, or `plate` kept separate from any physics choice.

For Chant Sura W200/W800, use `sphere` sidecars with `shape_class: equivalent_sphere_from_mass` unless the validation case can be tied to a specific EOTA shape record. EOTA bounding-box sidecars may be added as a catalog later, but should not be attached to trajectory validation cases until the block-to-EOTA mapping is auditable.

## Application Plan

1. Generate and validate public sidecars from existing processed metadata.
   - Start from `data/processed/tschamut2014/block_metadata.csv` and `validation/data/processed/chant_sura_2020/block_metadata.csv`.
   - Use only small derived YAML sidecars with public provenance and license notes.
   - Add parser tests that load every committed sidecar and verify mass, radius, dimensions, quaternion normalization, and passive warnings.

2. Attach passive shape metadata only where the active case block matches.
   - Do not attach a single Tschamut sidecar to a mixed-block case whose active `block.mass` and `block.radius` represent only one block while selected observations include other block IDs.
   - For public Tschamut, prefer generated single-block or explicitly filtered cases so `block_shape.metadata_path` matches the case-level active block.
   - For Chant Sura, attach W200 or W800 equivalent-sphere sidecars only to cases containing that mass class. Split mixed W200/W800 cases or defer shape attachment.

3. Re-run validation as a no-tuning inertness check.
   - Compare each case with and without `block_shape.metadata_path`.
   - Require identical deposition/runout and trajectory metrics apart from additive manifest and trajectory-metadata fields.
   - Review manifest warnings that active contact remains spherical.

4. Add shape-aware grouping to analysis, not physics.
   - Group existing public Tschamut metrics by `block_id`, `mass_kg`, equivalent radius, and principal dimensions.
   - Group Chant Sura contact metrics by W200/W800 class where subsets are not mixed.
   - Treat these groupings as diagnostics for future model design, not calibration.

5. Preserve separation from future shape contact.
   - Do not use passive inertia in dynamics.
   - Do not introduce shape-dependent restitution, friction, rolling resistance, scarring, or tumbling.
   - Do not claim model improvement from passive metadata.

## Implementation Timing

Recommended now:

- Add Tschamut per-block passive sidecars because public mass and dimension records are already available.
- Add Chant Sura W200/W800 equivalent-sphere sidecars for provenance in single-class cases.
- Add sidecar validation tests and one numerical inertness test per representative dataset family.

Recommended to wait:

- Attaching EOTA non-spherical shape sidecars to Chant Sura trajectory cases, unless a public trajectory-to-shape mapping is identified.
- Applying sidecars to mixed-block public Tschamut benchmark cases before the preparation workflow can generate block-filtered cases or per-trajectory shape metadata.
- Any use of shape mass properties in contact or rotational dynamics.

## Validation And Reporting Rules

Shape metadata application is successful when:

- sidecars validate under `shape_metadata_v1`;
- manifests include passive shape provenance and warnings;
- `trajectory_metadata_table_v1` carries additive shape fields;
- numerical validation outputs are unchanged for matched cases;
- grouped metrics can be reproduced from committed sidecars and existing validation outputs;
- reports state clearly that contact remains spherical.

Any mismatch between a sidecar and the active case-level `block.mass` or `block.radius` should fail early or remain unapplied. Silent fallback to approximate shape records would undermine provenance.

## Risks

- Passive metadata can be misread as active shape physics. Keep warnings visible in manifests and docs.
- Mixed-block Tschamut cases can create false provenance if one sidecar is attached to all trajectories. Use block-filtered cases or defer.
- EOTA shape records are useful but not automatically tied to current Chant Sura validation subsets. Treat them as future shape-contact inputs until mapping is documented.
- Grouped metric differences by shape class may reflect release conditions, terrain path, or observation selection, not shape physics.

## Next Decision

Implementation should happen in a small follow-up as metadata plumbing and validation only. The first implementation target should be Tschamut per-block sidecars plus single-block generated case support or documented run filters. Chant Sura EOTA attachment should wait for better shape-to-trajectory records.

## Implementation Note

The public Tschamut sidecars listed above are now committed under `data/processed/tschamut2014/shape_metadata/` and validated by Rust tests. `scripts/prepare_tschamut_public_benchmark.py` supports `--block-id` and `--block-shape-metadata` for single-block benchmark packages; the script rejects passive shape attachment when selected runs contain mixed block IDs. Existing mixed-block public benchmark defaults remain unchanged.

A local block-1 inertness check generated matched 3-run public Tschamut packages
with and without `block_1_st_leonard.yaml` and ran the baseline validation case.
All reported runout/deposition metrics were bitwise identical in the two
metrics JSON files; the only intended differences were additive manifest and
trajectory-metadata shape fields plus the passive-contact warning.
