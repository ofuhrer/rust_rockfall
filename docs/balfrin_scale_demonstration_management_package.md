# Balfrin Scale Demonstration Management Package

Status: current management synthesis for the Balfrin scale demonstration.

This package answers a narrow question: based on tracked measured evidence and
projection-only scale estimates, is the current architecture plausibly moving
toward a larger Balfrin demonstration?

## Current Answer

- 10-zone work remains feasible as a planning class under the current
  single-node/postproc boundary, but it is still projection-supported rather
  than measured hazard execution. The adjacent-candidate and AOI/QGIS updates
  improved review readiness, but they did not open a measured 10-zone live
  probe.
- 100-zone work is conditionally feasible as a deferred planning case until
  reducer, manifest, scheduler, and authorization pressure are reduced.
- Regional split work is the next executable milestone, but under current
  constraints it is still failed-closed/no-submit evidence rather than
  measured scale capability, so regional workflows remain out of reach until
  that bounded retry is measured.
- Swiss-wide workflows are out of reach under current single-node/postproc
  constraints.
- The recent two-zone and four-zone submit branches are failed-closed guardrail
  evidence, not measured hazard execution evidence, and the rebuilt
  management-AOI branch is still blocked by `source_zone_footprint_overlap`.
- TB-312's four-zone postproc/reducer package is measured, and TB-407 adds the
  smallest multi-zone probe, but both remain postproc-only and do not upgrade
  hazard execution capability.
- TB-340 through TB-444 improved real-AOI acquisition/preprocessing automation,
  release-zone/scenario pressure tooling, QGIS and connector review readiness,
  submit-contract regeneration, fail-closed branch integration,
  reducer-pressure evidence, and the current Swiss-scale projection. Those
  changes reduce workflow ambiguity but still do not provide measured
  multi-zone hazard execution.
- GIS/COG packaging remains blocked for large AOI stress packages because the
  packaged AOI root lacks required pilot GIS package manifest fields.

## Evidence Classes

- Measured: single-job Balfrin evidence, restartability metadata, target-area
  canonical bundle evidence, uncertainty interpretation, GIS scope, claim
  boundaries, and the TB-312 four-zone postproc/reducer package plus the
  TB-407 smallest multi-zone probe.
- Projection-only: Swiss-scale feasibility estimates for 10-zone, 100-zone,
  regional, and Swiss-wide workflows.
- Failed-closed: reviewed live-submit branches that stopped before `sbatch`.
  TB-362 failed closed on the explicit two-zone hazard path, and TB-386 keeps
  the current management-AOI decision blocked at `source_zone_footprint_overlap`
  before live execution, so no job id or measured run root exists for either
  branch.
- Fixture-backed: replay/preservation smoke evidence where no live run root is
  mounted.
- Deferred: management review and any future Balfrin submission decision.
- Unavailable: live AOI automation, release/scenario automation, and target-
  area probe metrics in this checkout.

## Regeneration

```bash
PYENV_VERSION=system uv run python scripts/summarize_balfrin_management_demo_package.py \
  --run-root tests/fixtures/balfrin_probe_metrics_contract/complete_run_root \
  --artifact-dir /tmp/balfrin_management_demo_package_v1 \
  --format text
```

The helper writes JSON and text artifacts to the chosen artifact directory and
keeps all claim boundaries false.

## Boundaries

This package does not authorize scale-up, distributed execution, operational
use, annual frequency, physical probability, risk, exposure, or vulnerability
claims. It also does not treat failed-closed or postproc-only evidence as
measured hazard execution, and it keeps the current `source_zone_footprint_overlap`
candidate-screening blocker separate from measured Balfrin evidence. The next
recommended executable milestone is one bounded regional split postproc retry
with a fresh passing access preflight and regenerated ready package.
