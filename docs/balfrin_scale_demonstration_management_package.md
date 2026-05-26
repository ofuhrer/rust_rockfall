# Balfrin Scale Demonstration Management Package

Status: current management synthesis for the Balfrin scale demonstration.

This package answers a narrow question: based on tracked measured evidence and
projection-only scale estimates, is the current architecture plausibly moving
toward a larger Balfrin demonstration?

## Current Answer

- 10-zone work remains the current hazard-planning boundary under the
  single-node/postproc evidence base.
- 24-zone work is now measured and repeated as a Balfrin diagnostic
  reducer-pressure workload: job `4368588` measured the simplified 24-zone
  shape, and jobs `4368592`/`4368593` repeated it at the same size. This is
  performance and output-footprint evidence, not hazard-throughput or
  physical-probability evidence.
- 100-zone work remains a deferred projection until reducer, manifest,
  scheduler, queue-policy, and scientific-evidence pressure are reduced.
- Regional split work is measured at the bounded probe level by the current
  regional split run root, but it does not promote broader regional workflows.
- Swiss-wide workflows remain deferred phase changes.
- The recent two-zone and four-zone submit branches are failed-closed guardrail
  evidence, not measured hazard execution evidence, and the rebuilt
  management-AOI branch is still blocked by `source_zone_footprint_overlap`.
- TB-312's four-zone postproc/reducer package is measured, TB-407 adds the
  smallest multi-zone probe, TB-565/TB-566 add the current measured regional
  split run root, and TB-579/TB-581/TB-582 add the 24-zone diagnostic and
  repeatability evidence, but these remain bounded diagnostic or comparison
  evidence and do not upgrade hazard execution capability.
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
  boundaries, TB-312 four-zone postproc/reducer evidence, TB-407 smallest
  multi-zone evidence, current regional split comparison evidence, and the
  24-zone diagnostic repeatability pair.
- Projection-only: Swiss-scale feasibility estimates beyond the current
  10-zone hazard-planning boundary and 24-zone diagnostic boundary.
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
keeps all claim boundaries false. The `diagnostic_performance_section` records
the exact 24-zone reproduction commands, run roots under `$SCRATCH`, submitted
git heads, job ids, runtime/memory/output/manifest measurements, and
repeatability bounds.

## Boundaries

This package does not authorize scale-up, distributed execution, operational
use, annual frequency, physical probability, risk, exposure, or vulnerability
claims. It also does not treat failed-closed, diagnostic, or postproc-only
evidence as measured hazard execution. The next useful performance milestone is
a larger bounded diagnostic only if queue policy remains favorable; the next
scientific milestone is closing calibration, holdout, source-frequency, and
physical-probability evidence gaps.
