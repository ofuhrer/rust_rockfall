# Terrain/Material Interaction Protocol

Status: no-tuning diagnostic implementation record. This document does not
change physics, defaults, stop thresholds, validation baselines, release
conditions, terrain-class values, public benchmark status, or operational
claims.

## Decision

Add terrain/material context to stopping diagnostics only where the runtime
already has a configured `terrain_classes` raster and a defensible `(x, y)`
lookup point.

The implemented diagnostic stack records terrain/material class at:

- the final simulated position, when that position falls inside a non-nodata
  terrain-class cell;
- the last significant impact, when a significant impact exists and its
  location falls inside a non-nodata terrain-class cell.
- each significant impact as a bounded sequence and aggregate per-class count
  in `stop_state` and ensemble stop-state sidecars.

These fields are provenance and grouping labels. They are not calibrated
material parameters, not model-selection evidence, and not operational terrain
classification.

## Additive Schema

`stop_state` records now include:

| Field | Meaning |
| --- | --- |
| `terrain_material_context_available` | `true` when at least one terrain/material lookup succeeded. |
| `final_terrain_class_id` | Terrain-class raster id at the final position, when available. |
| `final_terrain_class_name` | Class name from configured `terrain_classes` metadata. |
| `final_terrain_class_source` | Terrain-class layer id from configured metadata. |
| `last_significant_impact_terrain_class_id` | Terrain-class raster id at the last significant impact, when available. |
| `last_significant_impact_terrain_class_name` | Class name at the last significant impact. |
| `last_significant_impact_terrain_class_source` | Terrain-class layer id used for the impact lookup. |
| `significant_impact_terrain_class_counts` | Per-class count across significant impacts, formatted as `id:name`. |
| `significant_impact_terrain_class_sequence_head` | First bounded segment of the significant-impact class sequence. |
| `significant_impact_terrain_class_sequence_tail` | Last bounded segment when the sequence is truncated. |
| `significant_impact_terrain_class_sequence_truncated` | Whether the full significant-impact sequence exceeded the stored head/tail bounds. |
| `significant_impact_terrain_class_unavailable_count` | Significant-impact count with no class lookup because the impact was outside the class grid or nodata. |
| `terrain_material_instrumentation_gaps` | Explicit reasons terrain/material context is incomplete. |

`stop_state_summary_v3` manifest objects now include:

| Field | Meaning |
| --- | --- |
| `terrain_material_context_available_count` | Number of stop-state rows with any terrain/material class context. |
| `final_terrain_class_counts` | Per-class count at final positions, formatted as `id:name`. |
| `last_significant_impact_terrain_class_counts` | Per-class count at last significant impacts, formatted as `id:name`. |
| `significant_impact_terrain_class_counts` | Per-class significant-impact count, aggregated across stop-state rows. |
| `significant_impact_terrain_class_unavailable_count` | Aggregate count of significant impacts that could not be classified. |

`terrain_classes` manifest objects now include `schema_version`,
`metadata_schema_version`, `metadata_sha256`, and `class_grid_sha256` so future
reviewers can reproduce the exact class assumptions used by a diagnostic run.

When `terrain_classes` metadata is configured for generated ensemble/deposition
outputs, the runner also writes a local `*_terrain_material_exposure.csv`
sidecar and a `terrain_material_exposure_summary_v1` manifest object. Exposure
rows group saved trajectory samples by configured terrain/material class and
record sample count, segment count, horizontal path length, duration, contact
sample count, contact duration, contact path length, and contact-state sample
counts. Rows with out-of-grid or nodata lookups are labelled `unavailable` and
carry explicit instrumentation gaps.

Legacy manifests and diagnostics remain readable because the new fields are
additive and default to absent, false, empty, or null.

## Runtime Scope

The simulator still computes trajectory physics exactly as before. The class
lookup is applied after the run result exists in validation/reporting code, and
only uses the already loaded `TerrainClassMap`.

No lookup is inferred from file paths, outcomes, runout, stop reason, terrain
slope, or final speed. When `terrain_classes` metadata is absent, the diagnostic
reports that class context is unavailable. When a lookup point is outside the
class raster or on nodata, the diagnostic reports that gap explicitly.

## Summarization

`scripts/summarize_stopping_behavior.py` now preserves the additive class
fields and can emit extra per-final-class rows with:

```bash
python3 scripts/summarize_stopping_behavior.py \
  --stop-state label:path/to/ensemble_stop_state.csv \
  --terrain-material-exposure label:path/to/ensemble_terrain_material_exposure.csv \
  --group-by-terrain-material \
  --group-by-impact-terrain-material
```

The grouped rows summarize final speed, final kinetic energy, stop reason,
final contact state, low-energy contacts, last-impact distance, significant
impact class counts, unavailable impact-class lookups, runout, and
terrain/material gaps for each final or significant-impact terrain/material
class.

The summarizer never infers a terrain/material class from paths or outcomes.
Rows without class context are grouped as `unknown` and carry instrumentation
gaps.

## Implementation Status

Implemented:

- additive single-run `stop_state` class fields;
- additive ensemble stop-state CSV class fields;
- additive `stop_state_table_v3` and `stop_state_summary_v3` class-count
  fields;
- additive terrain-class manifest hashes and schema fields;
- additive `terrain_material_exposure_table_v1` sidecars and
  `terrain_material_exposure_summary_v1` manifests for generated outputs with
  configured terrain classes;
- grouped stop-state summarization by final and significant-impact
  terrain/material class;
- synthetic tests for configured class lookup, missing metadata fallback,
  out-of-grid lookup gaps, and summarizer grouping.

Still missing:

- active per-contact parameter-value provenance;
- per-class evidence metadata beyond fixture/source provenance;
- domain-exit and terrain-error termination exposure from the integrator.

## Examples

The checked-in Swiss pilot terrain-class fixture is synthetic. It can prove
schema and lookup behavior, but it cannot support terrain/material calibration:

```bash
cargo run -- validate --case validation/cases/swissalti3d_release_zone_terrain_classes_pilot.yaml
python3 scripts/summarize_stopping_behavior.py \
  --stop-state synthetic_swiss:validation/results/swissalti3d_terrain_class_deposition_stop_state.csv \
  --terrain-material-exposure synthetic_swiss_exposure:validation/results/swissalti3d_terrain_class_deposition_terrain_material_exposure.csv \
  --group-by-terrain-material \
  --group-by-impact-terrain-material \
  --output-csv validation/results/terrain_material_diagnostics/synthetic_swiss_stopping_by_material.csv \
  --output-md validation/results/terrain_material_diagnostics/synthetic_swiss_stopping_by_material.md
```

Generated files under `validation/results/` are local diagnostics and should
not be committed unless intentionally converted into tiny fixtures.

## Limitations

Terrain classes in the current runtime can carry active parameter overrides.
Diagnostic reports must therefore describe them as configured terrain/material
assumptions, not observed material truth. Current checked-in class values are
synthetic fixtures and are not calibrated.

Tschamut and Mel de la Niva remain diagnostic/non-regression evidence only.
They must not be used as physics-selection evidence for terrain/material
models. Held-out Chant Sura for `shape_contact_v0` remains blocked, and
`shape_contact_v0` runtime progression remains paused.

## Next-Step Decision

Do not proceed to terrain/material calibration or new material parameters yet.

Recommended next package: add active per-contact parameter provenance and a
reviewed, diagnostic-only regeneration path for selected field-scale outputs
so explicit stop-state sidecars carry final, last-impact, and significant-impact
terrain/material context where class metadata is configured. If field-scale rows
remain proxy-only, continue instrumentation or rebound/contact-proxy provenance
work before implementing any material model.
