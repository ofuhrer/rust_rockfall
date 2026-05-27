# Source-Frequency Evidence TB-614

Date: 2026-05-26

Status: staged non-production source-frequency design-review evidence and
moved the physical-probability readiness report to the next blocker.

Evidence record:

`validation/private/source_frequency_evidence_tschamut_design_review_v1.yaml`

Validation command:

```bash
PYENV_VERSION=system uv run python scripts/validate_source_frequency_evidence.py \
  validation/private/source_frequency_evidence_tschamut_design_review_v1.yaml \
  --format json
```

Gap-assessment command:

```bash
PYENV_VERSION=system uv run python scripts/assess_validation_calibration_evidence_gaps.py --format json
```

## Record

The staged record is explicitly `accepted_for_design_review` and
`design_review_only`. It is not observed Tschamut source-event evidence and is
not used by runtime products.

Key fields:

| Field | Value |
| --- | --- |
| `source_zone_id` | `tschamut_public_lps_release_bbox` |
| `source_geometry_version` | `tschamut_public_source_zone_metadata_v1` |
| `source_geometry_hash` | `sha256:f38651a8d76407ca3edc46af03246380007773bee59aae9f95abffc6f99cae06` |
| `source_event_rate_per_year` | `0.02` |
| `rate_time_window_years` | `50` |
| `rate_observation_period` | `1970` to `2020` |
| `rate_evidence_type` | `expert_elicitation` |
| `rate_uncertainty` | interval `0.005` to `0.08` events per year |
| `prototype_authorized` | `false` |

The validator reports:

- `record_status`: `accepted_for_design_review`
- `intake_classification`: `accepted`
- `source_event_rate_available`: `true`
- `prototype_authorized`: `false`

## Readiness Impact

The default validation/calibration evidence-gap report now consumes this record.
The source-frequency category is `present` for design-review assessment input,
and the physical-probability readiness check moves past
`source_frequency_evidence`.

Current readiness result:

- `readiness_status`: `partial_evidence_missing_critical_inputs`
- `first_blocking_evidence_class`: `release_probability_model`
- failing evidence classes:
  - `release_probability_model`
  - `block_population_evidence`
  - `calibration_evidence`
  - `independent_holdout_validation`

The next concrete scientific-task list now skips source-frequency staging when
using the default report, because the source-frequency class is already present
for this design-review-only assessment input.

## Boundary

This is not a physical-probability upgrade. The record is a deliberately broad
design-review placeholder with explicit non-production status. Physical and
operational products remain deferred until source-frequency evidence is tied to
release-probability, block-population, calibration, and independent holdout
evidence.
