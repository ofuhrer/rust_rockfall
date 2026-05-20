# Balfrin Scale Demonstration Management Package

Status: current management synthesis for the Balfrin scale demonstration.

This package answers a narrow question: based on tracked measured evidence and
projection-only scale estimates, is the current architecture plausibly moving
toward a larger Balfrin demonstration?

## Current Answer

- 10-zone work remains feasible as a planning class under the current
  single-node/postproc boundary, but it is still projection-supported rather
  than measured hazard execution.
- 100-zone work is conditionally feasible as a deferred planning case until
  reducer, manifest, scheduler, and authorization pressure are reduced.
- Regional and Swiss-wide workflows are out of reach under current
  single-node/postproc constraints.
- The recent two-zone and four-zone submit branches are failed-closed guardrail
  evidence, not measured hazard execution evidence.
- TB-312's four-zone postproc/reducer package is measured, but it is
  postproc-only and does not upgrade hazard execution capability.
- GIS/COG packaging remains blocked for large AOI stress packages because the
  packaged AOI root lacks required pilot GIS package manifest fields.

## Evidence Classes

- Measured: single-job Balfrin evidence, restartability metadata, target-area
  canonical bundle evidence, uncertainty interpretation, GIS scope, claim
  boundaries, and the TB-312 four-zone postproc/reducer package.
- Projection-only: Swiss-scale feasibility estimates for 10-zone, 100-zone,
  regional, and Swiss-wide workflows.
- Failed-closed: reviewed live-submit branches that stopped before `sbatch`
  because package, checksum, or manifest contracts did not match.
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
measured hazard execution.
