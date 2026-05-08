# Annual/Physical Prototype Preflight

Status: inactive preflight contract for the annual/physical prototype. This
document does not add annual frequency products, physical probability products,
return-period labels, operational hazard maps, or risk modelling.

## Scope

This preflight records the current Target 10 decision boundary. The annual or
physical intensity-frequency prototype must remain blocked until the selected
physical/source-frequency design gate is explicitly authorized and all blocker
contracts are accepted or implemented. Current products remain
`unweighted_diagnostic`, `sampling_weighted_conditional`, and conditional
intensity-exceedance outputs.

The checked-in template is
`validation/templates/annual_physical_prototype_preflight_v1.yaml`, and the
executable validator is
`scripts/validate_annual_physical_prototype_preflight.py`.

## Required Preflight State

The selected record must state:

- `record_status: blocked_by_design_gate`;
- `prototype_authorized: false`;
- `runtime_support_added: false`;
- the referenced design gate path;
- the observed design-gate decision and authorization status;
- the remaining blocker categories;
- claim-boundary fields that reject annual, physical, return-period, risk, and
  operational claims.

The validator reads the referenced design-gate record and verifies that the
preflight stays synchronized with the gate decision. It intentionally rejects
prototype authorization while the design gate remains deferred.

The referenced design gate now also verifies four synthetic design-review fixtures
for the source-frequency, block/release probability, reducer
precondition, and validation/calibration review schemas. These fixtures are
schema coverage only and are not accepted real evidence or implemented reducer
support, so they do not change the blocked preflight state.

## Current Decision

Target 10 remains blocked. The first safe implementation step is therefore a
preflight guard, not runtime support. A future annual or physical prototype
requires accepted source-frequency evidence, accepted block/release probability
evidence, implemented overlap-adjusted reducers, implemented uncertainty
propagation, and an accepted validation/calibration review.
