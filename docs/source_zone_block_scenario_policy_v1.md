# Source-Zone And Block-Scenario Policy V1

Status: Phase 2 policy contract for the future public real-site conditional
pilot. This document does not implement source-zone generation, block-size
sampling, physical probability, annual frequency, new physics, or simulator
behavior changes.

## Purpose

The conditional real-site pilot needs source-zone and block-scenario assumptions
that are frozen before simulation. The policy layer records those assumptions
separately from runtime case files so pilot reports can distinguish:

- interpreted source-zone geometry from validation evidence;
- deterministic release sampling from physical release probability;
- block-scenario labels from active physics;
- sampling weights from physical occurrence probability.

The checked-in template is
`validation/templates/public_real_site_source_scenario_policy_v1.yaml`. It is a
share-safe template and should be copied to an ignored pilot directory before a
real domain is selected.

The selected Tschamut public pilot policy is
`validation/policies/tschamut_public_source_scenario_policy_v1.yaml`. It
predeclares the Level 1 public-release bounding source zone, deterministic
release-cell grid, and representative block scenarios for
`tschamut_public_pilot`. It is share-safe and conditional-only: the release
cells and block scenarios carry sampling weights, not physical release
probabilities, annual frequencies, or return-period semantics.

## Required Policy Fields

The policy must record:

- `pilot_id`, `policy_status`, and `operational_status`;
- source-zone evidence level from
  `docs/probabilistic_scenario_model_design.md`;
- allowed geometry type, currently polygon only;
- source-zone geometry for prepared policies;
- derivation inputs and criteria, such as terrain, slope, geology, inventory,
  or expert-review notes;
- deterministic release sampling mode, seed policy, and stable release-cell id
  requirements, including explicit release-cell ids for prepared policies;
- block scenarios with stable `block_scenario_id`, size class, shape class,
  representative radius or mass, and sampling weight;
- explicit unsupported claims: annual frequency, return period, physical
  probability, risk map, and operational hazard map.

Level 1 policy may use manual real-site interpretation backed by CRS/provenance
metadata and terrain/context review. Level 2 policy requires documented
predeclared geomorphic, geology, inventory, or expert-review criteria. Neither
level defines physical release probability or annual source frequency.

## Validation

Run:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run python \
  scripts/validate_source_scenario_policy.py \
  validation/templates/public_real_site_source_scenario_policy_v1.yaml
```

The validator checks that the template or local policy preserves the current
conditional semantics. Prepared local policies must list at least one block
scenario, use finite nonnegative sampling weights with a positive total, keep
`block_shape_class: sphere` until active shape physics is explicitly added, and
leave physical and annual probability fields absent.

Validate the selected Tschamut policy with:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run python \
  scripts/validate_source_scenario_policy.py \
  validation/policies/tschamut_public_source_scenario_policy_v1.yaml
```

## Boundary

This policy can support conditional intensity-exceedance pilot products. It
does not support annual intensity-frequency, return-period labels, operational
hazard-map claims, or risk-map claims.
