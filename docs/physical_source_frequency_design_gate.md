# Physical Source-Frequency Design Gate

Status: design gate only. This document does not implement annual frequency,
physical probability, return-period labels, operational hazard maps, or risk
modelling. The current decision is `deferred`: an annual or physical prototype
is not authorized until the evidence and schema blockers below are closed.

## Scope

Current products remain `unweighted_diagnostic`,
`sampling_weighted_conditional`, and conditional intensity-exceedance outputs.
Sampling weights may define a conditional numerical sampling design, but they
must not be reinterpreted as source occurrence rates, block occurrence rates,
or physical scenario probabilities.

This gate defines the minimum contract required before a later prototype can
represent physical probability or annual intensity-frequency products. It is a
claim-control and schema-design artifact, not validation evidence.

## Required Units

A future physical or annual product must keep these quantities separate:

| Quantity | Required unit or denominator | Required interpretation |
| --- | --- | --- |
| Source event rate | events per source zone per year, with a stated time window | occurrence frequency for a defined source-zone event class |
| Block-scenario distribution | conditional probability given a source event | block size, shape, and representative mass distribution for that event class |
| Release-cell allocation | conditional probability given source event and block scenario | spatial allocation within a non-overlapping or adjusted source-zone model |
| Cell exceedance output | exceedances per cell per year | propagated annual contribution after source, block, release, and trajectory uncertainty are combined |

The conceptual future reducer for a cell and threshold is:

```text
lambda(cell, threshold) =
  sum over source zones s [
    source_rate(s) *
    sum over block scenarios b [
      p(b | s) *
      sum over release cells r [
        p(r | s, b) *
        p(exceedance at cell, threshold | s, b, r, model)
      ]
    ]
  ]
```

This equation is not implemented. It is a units check for the future design.

## Required Evidence

Before authorization, each source-frequency record must include:

- stable `source_zone_id` and geometry version or geometry hash;
- source event-class definition;
- rate unit, time window, observation or derivation period, and provenance;
- uncertainty interval or distribution, not only a point estimate;
- method label such as inventory count, expert elicitation, calibrated model,
  or external authority record;
- explicit statement separating calibration inputs from validation evidence.

Each block-scenario distribution must include:

- stable `block_scenario_id` values;
- conditional probability denominator;
- evidence basis for size and shape classes;
- uncertainty representation or documented reason for deferral;
- proof that sampling weights are either separate numerical weights or are
  replaced by physical probabilities with a documented derivation.

## Overlap Rules

Annual source-frequency products require a source-zone overlap policy before a
prototype is allowed:

- source zones must form a mutually exclusive partition, or overlapping zones
  must have an explicit overlap-adjustment rule;
- shared release cells must not be counted twice unless the event classes are
  explicitly distinct;
- geometry versions, crop extents, CRS EPSG:2056, and vertical datum must be
  recorded with the source-frequency records;
- reducers must report whether overlap adjustment was applied.

## Uncertainty Model

The future schema must separate:

- aleatory trajectory variation from seeded model runs;
- conditional block-scenario and release-cell distributions;
- epistemic uncertainty in source occurrence rates;
- model-form and terrain/material uncertainty;
- calibration uncertainty from validation or holdout evidence.

A single deterministic annual rate without uncertainty is insufficient for
authorizing the prototype.

## Validation And Calibration Separation

swisstopo terrain, imagery, building, and context layers are input geodata, not
validation evidence by themselves. Frequency calibration must not be tuned to
make one conditional map resemble a target pattern. Any future calibration data,
validation data, and holdout comparisons must be listed separately in dataset
metadata and reports.

## Schema Plan

A later prototype schema must reject incomplete records and include at least:

- `frequency_model_id`;
- `frequency_mode`;
- `source_zone_id`;
- `source_geometry_version`;
- `source_event_class`;
- `source_event_rate_per_year`;
- `rate_time_window_years`;
- `rate_evidence_type`;
- `rate_provenance`;
- `rate_uncertainty`;
- `block_scenario_id`;
- `block_scenario_probability`;
- `release_cell_id`;
- `release_cell_probability`;
- `source_zone_overlap_policy`;
- `calibration_dataset_ids`;
- `validation_dataset_ids`;
- `operational_status`.

## Gate Decision

Decision: deferred.

Prototype authorization: false.

Blocking conditions:

- no accepted source-frequency evidence contract exists;
- no overlap-adjustment rule exists for source-zone frequency aggregation;
- no executable schema rejects incomplete source-rate, uncertainty, and
  calibration/validation metadata;
- no validation plan exists for annual or physical products;
- current sampling weights are conditional design weights only.

The executable gate record is
`validation/pilot_runs/physical_source_frequency_design_gate_v1.yaml`, checked
by `scripts/validate_physical_source_frequency_design_gate.py`.

## Blocker Resolution Status

One blocker is partially closed: `docs/source_frequency_evidence_contract.md`
defines an inactive source-frequency evidence contract, with template
`validation/templates/source_frequency_evidence_v1.yaml` and validator
`scripts/validate_source_frequency_evidence.py`. The template records
`no_accepted_frequency_evidence`, so this does not authorize annual or
physical products.

Remaining blockers before prototype authorization:

- accepted source-frequency evidence for a source-event class;
- complete block-scenario and release-cell physical probability evidence;
- overlap-adjusted reducers and uncertainty propagation;
- validation/calibration review for frequency products.
