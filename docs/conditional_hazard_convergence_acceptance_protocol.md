# Conditional Hazard-Map Convergence Acceptance Protocol

Status: current DT-05 protocol for conditional hazard-map products. The current
DT-04 Balfrin evidence is assessed as `inconclusive`.

This protocol defines how conditional hazard-map evidence is classified without
annual/physical frequency, return periods, exposure, vulnerability, risk, or
operational-validity semantics. It applies only to conditional hazard products
and treats GIS/QGIS visual QA as secondary interoperability evidence, not the
primary pilot outcome.

## Scope

This protocol applies to conditional hazard-map products only:

- `unweighted_diagnostic`
- `sampling_weighted_conditional`
- `conditional_intensity_exceedance`

The protocol does not authorize:

- no annual/physical frequency;
- no return periods;
- no risk, exposure, or vulnerability products;
- no operational hazard-map claims;
- no parameter tuning to force convergence;
- no scale-up based on GIS/QGIS QA alone.

## Required Evidence Categories

A record used under this protocol must include all of the following evidence
categories:

- target run provenance;
- input freeze;
- trajectory count and release-cell count;
- deterministic seed, order, and chunk metadata;
- reducer parity or repeatability;
- output profile;
- output budget;
- checksum and provenance;
- log audit;
- convergence indicators;
- known interpretation blockers.

## Classification Rules

### `pass`

Use `pass` only when all required evidence categories are present and all
convergence gates are satisfied:

- target run provenance matches the assessed DT-04 evidence;
- the input freeze is unchanged;
- the release-cell and trajectory counts match the predeclared target gate;
- seed, order, and chunk metadata are deterministic and reproducible;
- reducer parity or repeatability is confirmed;
- the output profile matches the predeclared conditional profile;
- the output budget is recorded and does not introduce new scale-up blockers;
- checksums and provenance records are present and consistent;
- the log audit is clean;
- convergence indicators are accepted;
- known interpretation blockers are absent or explicitly resolved;
- no prohibited claim language appears.

### `inconclusive`

Use `inconclusive` when the workflow completed and the evidence is usable, but
one or more non-fatal blockers remain. Typical reasons:

- convergence has not been formally accepted yet;
- GIS/QGIS QA is blocked or remains secondary only;
- forest or obstacle context is still limiting;
- debug-output volume remains a blocker for larger follow-up runs;
- the evidence supports interpretation, but not scale-up authorization.

### `no_go`

Use `no_go` when the record cannot support a defensible conditional assessment.
Typical reasons:

- required evidence categories are missing or contradictory;
- the input freeze changed without a documented new assessment;
- deterministic order, seed, or chunk metadata are absent or inconsistent;
- reducer parity or repeatability failed;
- the output profile does not match the predeclared conditional profile;
- prohibited annual/physical, return-period, risk, exposure, vulnerability,
  or operational-validity language appears;
- a record attempts to authorize scale-up while required convergence gates are
  unresolved.

## Current DT-04 Assessment

The current DT-04 Balfrin evidence is assessed as `inconclusive` under this
protocol.

Reasons:

- target-scale convergence has not been accepted;
- manual GIS/QGIS visual QA is secondary and not run in this checkout;
- forest/obstacle context remains limiting;
- validation debug-output volume remains a retained blocker.

This assessment does not authorize scale-up, annual semantics, physical
probability semantics, return periods, risk products, or operational use.

For quantitative convergence review, compare two or more hazard-manifest or
summary paths with `scripts/compare_hazard_map_convergence.py`. The diagnostic
reports layer-summary deltas, conditional-curve row-count differences, and
output checksum parity, and it returns `blocked_missing_inputs` when the local
ignored outputs are absent so downstream acceptance summaries can distinguish
missing evidence from a zero-difference comparison.
