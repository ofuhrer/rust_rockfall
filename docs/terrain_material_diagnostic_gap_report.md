# Terrain/Material Diagnostic Gap Report

Status: no-tuning instrumentation gap report. This document records what the
current terrain/material diagnostic subsystem can audit and what remains
unavailable. It does not introduce calibration targets, tuned material
coefficients, validation baseline changes, public benchmark enablement, or
operational claims.

## Current Coverage

The current stack can audit configured terrain/material context for:

- final simulated position class in `stop_state`;
- last significant-impact class in `stop_state`;
- per-trajectory significant-impact class counts and bounded head/tail class
  sequences;
- ensemble `*_stop_state.csv` sidecars with `stop_state_table_v3` fields;
- manifest-level `stop_state_summary_v3` counts for final, last-impact, and
  significant-impact class groupings;
- terrain-class manifest schema/hash provenance for the metadata and class
  raster used by a run;
- trajectory-wide `*_terrain_material_exposure.csv` sidecars and
  `terrain_material_exposure_summary_v1` manifests for generated outputs with
  configured terrain classes;
- read-only summaries grouped by final class and by significant-impact class.

These outputs are descriptive provenance. They support questions such as
"which configured class labels coincide with stopping states or significant
impact sequences?" They do not support material-parameter calibration by
themselves.

## Remaining Gaps

The following gaps remain before terrain/material interaction studies can be
used as calibration or model-selection inputs:

- Active parameter provenance is not emitted per contact or impact. Terrain
  class labels can drive configured contact/scarring overrides, so reports must
  state "configured terrain/material assumption" rather than observed material
  truth until active parameter values are recorded with contact evidence.
- Full per-impact terrain/material tables are not yet emitted. Stop-state
  records carry aggregate counts and bounded sequences only.
- Exposure sidecars summarize saved sample exposure, not continuous path
  integrals. Duration and path length are assigned to the class at the segment
  end sample.
- Contact-episode summaries are not yet emitted. Exposure rows have contact
  sample/duration/path counts, but not contiguous episode start/end causes.
- Terrain-class manifests now carry hashes and schema fields, but per-class
  evidence metadata remains limited to the source fixture metadata.
- `domain_exit` and `terrain_error` termination flags are still placeholders
  until the integrator exposes those termination modes.
- Legacy trajectory and deposition outputs without explicit stop-state sidecars
  remain proxy-only for stop reason, significant impact, and terrain/material
  context.

## Hidden-Tuning Controls

Future work should stop before calibration if any of these controls cannot be
met:

- thresholds for "stopped", "low energy", or "significant impact" must be fixed
  before reviewing outcomes;
- class groupings must come only from configured `terrain_classes` metadata, not
  from path names, runout classes, or desired outcomes;
- Tschamut and Mel de la Niva may be used for diagnostic coverage and
  non-regression checks only, not as physics-selection evidence;
- held-out Chant Sura for `shape_contact_v0` must remain blocked while
  `shape_contact_v0` is paused after the failed/uncertain internal decision.

## Recommended Next Package

The next no-tuning package should add active per-contact parameter provenance
and optional full per-impact terrain/material sidecars. That package should
remain diagnostic-only and should not add fitted coefficients, new calibrated
classes, changed contact laws, or validation-threshold changes.
