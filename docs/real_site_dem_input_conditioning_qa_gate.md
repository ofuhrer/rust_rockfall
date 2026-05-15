# Real-Site DEM/Input Conditioning QA Gate

Status: DT-07 QA gate for selected public Swiss pilot domains. This fail-closed QA gate defines the minimum evidence needed to accept real-site DEM and input conditioning for interpretation or larger execution. It treats raw public inputs and intermediate conditioning artifacts as explicit provenance inputs. It does not change
physics, change DEM runtime behavior, change defaults, tune parameters, or
authorize annual, physical, risk, exposure, or operational claims.

Maintenance note: this is the completed DT-07 evidence contract. It is not a
current target list. Routine target sequencing and current gap assessment live
only in `docs/task_backlog.md`; update this file only when the
DEM/input QA gate itself changes.

## Scope

This gate applies to:

- the selected Tschamut public pilot;
- future Swiss public-data pilots that depend on public DEM, source-zone, or
  terrain-conditioning artifacts.

The gate is fail-closed. If the evidence is incomplete, stale, ambiguous, or
silently replaced, the pilot must remain `blocked` or `diagnostic`.
It is also a no-tuning/no-operational/no-annual boundary.

## Required Evidence

The following evidence categories must be present before a real-site DEM/input
artifact can be treated as accepted for pilot interpretation:

- raw input evidence;
- atomic ingest and checksum evidence;
- intermediate artifact producer-command evidence;
- CRS and vertical datum evidence;
- registration and transform evidence;
- nodata policy evidence;
- slope, sink, spike, and artifact sanity evidence;
- strict versus clamped DEM interpretation evidence;
- domain-exit and terrain-error interpretation evidence.

## Raw Input Evidence

Raw public inputs must be traceable to a concrete public source record and a
frozen local path policy.

Required fields:

- public source URL or equivalent public source record;
- source-tile id or stable public dataset id;
- raw file path under the ignored local raw cache;
- raw checksum;
- product version/date where available;
- freshness or re-verification status;
- explicit note if the raw artifact is documented but not locally rechecked in
  the current checkout.

For the selected Tschamut pilot, the raw source must be anchored to the
selected public geodata manifest and the public swissALTI3D tile inventory.

## Atomic Ingest And Checksum Evidence

The ingest step must be atomic in the sense that each artifact can be traced to
one producer command and one checksum record.

Required fields:

- producer command or preparation command;
- input path;
- output path;
- raw checksum when available;
- processed checksum when available;
- preprocessing status;
- explicit note if a checksum mismatch or missing artifact makes the pilot
  `blocked`.

The gate does not require new downloader behavior. It requires that the
existing preparation provenance be documented and checkable.

## Intermediate Artifact Evidence

Intermediate artifacts must preserve the provenance needed to reproduce the
conditioning step.

Required fields:

- processed DEM path;
- processed DEM metadata path;
- format;
- extent;
- dimensions;
- resolution;
- nodata policy;
- producer command;
- processed checksum when available.

The Tschamut selected manifest already records the expected paths and checksum
values for the public preparation workflow. This QA gate treats that manifest
as the provenance anchor; it does not rewrite the preparation command or change
the producer behavior.

## CRS / Registration Evidence

The gate requires explicit CRS/registration evidence:

- EPSG `2056`;
- vertical datum `LN02`;
- coordinate and height units in metres;
- extent or footprint consistency;
- explicit registration/transform note for the public input preparation path.

Registration evidence must explain whether the selected crop is aligned,
reprojected, cropped, or otherwise transformed. The gate must record whether
the transform was checked against the expected footprint and whether the
selected artifact is only documented or has been locally reverified.

## Nodata Policy

The gate requires an explicit nodata policy:

- nodata value;
- nodata propagation or preservation rule;
- whether nodata is treated as a hard no-go for a queried cell or as a
  documented boundary condition;
- whether boundary cells are accepted only under the clamped terrain contract.

Nodata policy must be explicit enough that a hazard map cannot quietly absorb
missing terrain values as if they were valid elevations.

## Terrain Sanity Checks

The gate requires explicit sanity checks for:

- slope artifacts;
- sinks;
- spikes;
- crop-edge discontinuities;
- unexpected interpolation artifacts;
- local terrain roughness anomalies that arise from preprocessing rather than
  model physics.

The record should say whether these checks were run, documented from previous
evidence, or still pending. A record may be `diagnostic` if the checks are
documented but not yet fully re-run locally.

## Strict Versus Clamped DEM Interpretation

The gate must state how DEM boundary behavior is interpreted:

- strict DEM behavior is a fail-closed contract when the queried terrain
  leaves the valid domain;
- clamped DEM behavior is a documented boundary convention, not a physical
  continuation of the terrain;
- interpolation across nodata is not a hidden default;
- domain exits and boundary hits must be recorded explicitly in the pilot
  interpretation.

This gate does not change runtime behavior. It makes the chosen behavior and
its limitations explicit before interpretation.
The strict versus clamped DEM interpretation remains a documented contract,
not a runtime change.

## Domain-Exit / Terrain-Error Interpretation

Terrain errors and domain exits must be classified explicitly:

- `passed`: all required evidence is complete and current;
- `blocked`: evidence is missing, stale, or inconsistent;
- `diagnostic`: evidence is documented but not yet sufficient for acceptance;
- `no_go`: evidence contains an unrecoverable provenance, registration, or
  claim-boundary problem.

The selected Tschamut pilot should remain `blocked` or `diagnostic` until the
required evidence is complete and locally verified.
The domain-exit / terrain-error interpretation must stay explicit before
acceptance.

## No-Tuning And Claim Boundary

This gate does not authorize:

- tuning terrain or contact parameters to compensate for input issues;
- changing DEM interpolation/runtime behavior;
- annual frequency, physical probability, return periods, risk, exposure, or
  vulnerability claims;
- operational hazard-map claims;
- treating clamped edge behavior as physical terrain continuation.

## Minimum Acceptance Rule

A real-site DEM/input artifact is acceptable for pilot interpretation only
when the record can show all of the following:

- the raw input is traced to a frozen public source record;
- the ingest step is atomic and checksum-backed;
- the processed artifact is linked to a producer command and checksum;
- CRS and registration are explicit and consistent;
- nodata handling is explicit;
- sanity checks are documented;
- boundary and terrain-error semantics are explicit;
- claim boundaries remain conservative.
