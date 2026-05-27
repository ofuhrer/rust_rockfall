# Block-Population Evidence TB-657

Date: 2026-05-27

## Result

The block-population evidence gap is now summarized as a design-review
candidate instead of a generic missing input. The staged Tschamut public block
population record is usable for review of block-size and block-shape evidence,
but it does not authorize runtime physical-probability products.

## Checked Evidence

Validated record:

```text
validation/data/processed/tschamut/block_population_evidence_tschamut_public_candidate_v1.yaml
```

Evidence summary:

- `record_status`: `accepted_for_design_review`
- `source_zone_id`: `tschamut_public_lps_release_bbox`
- `block_population_class_count`: `3`
- `total_count`: `3`
- `prototype_authorized`: `false`
- evidence basis: processed public Tschamut block metadata inventory

Scenario-table summary from
`scripts/generate_tschamut_block_scenario_tables.py`:

- observed-row summary template: `1` row from `10` release samples
- policy block-family template: `9` deterministic conditional rows
- policy sampling-weight total: `30.0`
- normalized sampling-share total: `1.0`
- shape-family labels: `equant`, `platy`, `elongated`

## Boundary

The staged population record and deterministic scenario rows are design-review
inputs. They keep representative block scenarios, conditional sampling weights,
and measured block metadata separate from physical probability, annual
frequency, return-period, operational, and risk semantics.

Calibration evidence remains the first blocking evidence class for the
physical-probability readiness check.
