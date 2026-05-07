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
| `terrain_material_instrumentation_gaps` | Explicit reasons terrain/material context is incomplete. |

`stop_state_summary_v1` manifest objects now include:

| Field | Meaning |
| --- | --- |
| `terrain_material_context_available_count` | Number of stop-state rows with any terrain/material class context. |
| `final_terrain_class_counts` | Per-class count at final positions, formatted as `id:name`. |
| `last_significant_impact_terrain_class_counts` | Per-class count at last significant impacts, formatted as `id:name`. |

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
  --group-by-terrain-material
```

The grouped rows summarize final speed, final kinetic energy, stop reason,
final contact state, low-energy contacts, last-impact distance, runout, and
terrain/material gaps for each final terrain/material class.

The summarizer never infers a terrain/material class from paths or outcomes.
Rows without class context are grouped as `unknown` and carry instrumentation
gaps.

## Implementation Status

Implemented:

- additive single-run `stop_state` class fields;
- additive ensemble stop-state CSV class fields;
- additive `stop_state_summary_v1` class-count fields;
- grouped stop-state summarization by final terrain/material class;
- synthetic tests for configured class lookup, missing metadata fallback,
  out-of-grid lookup gaps, and summarizer grouping.

Still missing:

- dominant or coverage-weighted class exposure along an entire trajectory;
- contact-count or impact-count distributions by terrain/material class;
- active per-contact parameter-value provenance;
- class-grid checksums and per-class evidence metadata;
- domain-exit and terrain-error termination exposure from the integrator.

## Examples

The checked-in Swiss pilot terrain-class fixture is synthetic. It can prove
schema and lookup behavior, but it cannot support terrain/material calibration:

```bash
cargo run -- validate --case validation/cases/swissalti3d_release_zone_terrain_classes_pilot.yaml
python3 scripts/summarize_stopping_behavior.py \
  --stop-state synthetic_swiss:validation/results/swissalti3d_terrain_class_deposition_stop_state.csv \
  --group-by-terrain-material \
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

Recommended next package: run a reviewed, diagnostic-only regeneration path
for selected field-scale outputs so explicit stop-state sidecars carry final
and last-impact terrain/material context where class metadata is configured.
If field-scale rows remain proxy-only, continue instrumentation or
rebound/contact-proxy provenance work before implementing any material model.
