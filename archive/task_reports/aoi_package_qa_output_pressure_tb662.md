# AOI Package QA Output Pressure TB-662

Date: 2026-05-27

Command:

```bash
rm -rf /tmp/tb662_aoi_package
PYENV_VERSION=system uv run python scripts/package_aoi_hazard_map.py \
  --input-root hazard/results/tschamut_public_pilot/target_gate_v1 \
  --output-root /tmp/tb662_aoi_package \
  --overwrite \
  --format json > /tmp/tb662_aoi_package.json
```

## Result

- package status: `map_package_ready`
- package files: `39`
- package bytes: `440,839`
- package manifest bytes: `165,220`
- pilot GIS manifest bytes: `82,313`
- summary bytes: `1,671`
- review surface status: `review_ready_with_warnings`
- QA checklist status: `diagnostic_review_pending`
- QA checklist items: `8`
- QA checklist ready items: `5`
- QA checklist pending items: `2`

The serialized QA checklist is `8,292` bytes. That is about `1.9%` of the
package byte count and about `5.0%` of the primary package manifest. At this
package size, checklist packaging is acceptable and not a material scaling
concern.

## Boundary

This measurement uses the existing target-gate AOI package root and does not
change package contents, hazard values, output policy, physical-probability
semantics, operational acceptance, or Balfrin execution behavior.
