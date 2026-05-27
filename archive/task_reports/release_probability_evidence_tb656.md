# Release-Probability Evidence TB-656

Date: 2026-05-27

## Result

The current release-probability evidence gap is no longer a generic missing
input. A Tschamut public block/release probability candidate is staged and
validates for design review only.

The candidate does not authorize physical-probability map labels, annual
frequency, return periods, operational hazard maps, or risk products. It only
makes the release-probability evidence class inspectable for later review.

## Checked Evidence

Validated record:

```text
validation/data/processed/tschamut/block_release_probability_evidence_tschamut_public_candidate_v1.yaml
```

Validation summary:

- `record_status`: `accepted_for_design_review`
- `source_zone_id`: `tschamut_public_lps_release_bbox`
- `block_scenario_count`: `3`
- `release_cell_count`: `10`
- `prototype_authorized`: `false`

Physical-probability readiness summary from
`scripts/assess_validation_calibration_evidence_gaps.py`:

- `readiness_status`: `partial_evidence_missing_critical_inputs`
- passing evidence classes: `6 / 7`
- first blocking evidence class: `calibration_evidence`
- failing evidence classes: `calibration_evidence`

## Remaining Boundary

The release-probability evidence class is present as a design-review candidate,
not as runtime physical-probability support. Calibration evidence remains the
first blocking input for physical-probability readiness, and final review still
has to decide whether any candidate evidence can be used beyond diagnostics.
