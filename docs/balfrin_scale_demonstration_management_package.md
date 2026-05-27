# Balfrin Scale Demonstration Management Package

Status: current management synthesis for the Balfrin scale demonstration.

This package answers a narrow question: based on tracked measured evidence and
projection-only scale estimates, is the current architecture plausibly moving
toward a larger Balfrin demonstration?

## Current Answer

- TB-678 is the current concise decision surface:
  `archive/task_reports/swiss_scale_demonstration_readiness_tb678.md`.
- Do not submit a Swiss-wide or distributed run yet.
- The latest measured hazard-throughput support is the TB-680/TB-681 repeat
  pair: 24 release zones on Balfrin `postproc`, jobs `4379134` and `4379224`,
  `0.272757`-`0.317613` s profile wall time, about `41` MB peak RSS, `29`
  hazard files, and about `1.17` MB hazard output.
- TB-671 measured three isolated concurrent 16-zone diagnostic run roots with
  no contention detected.
- TB-672 reconstructed the TB-669 metrics from a copied `$SCRATCH` run root
  without rerunning.
- TB-673 executed a national-chunk-shaped manifest/state smoke for three
  representative chunks on Balfrin.
- Scientific readiness remains the main blocker: TB-676 explicitly rejected
  the selected calibration candidate on holdout residual quality, and TB-677
  kept the physical-probability prototype fail-closed.
- The 24-zone TB-680/TB-681 repeat pair is the current hazard-throughput support
  point under the single-node/postproc evidence base; its first new blocker is
  manifest byte pressure above the current replay budget.
- TB-682 measured larger single-node hazard-output pressure at `96`, `192`, and
  `384` release zones. The largest measured size still below the current
  reduced-output byte budget is `192` release zones; `384` release zones exceeds
  the output-byte budget and all three larger runs exceed the manifest-byte
  budget.
- Diagnostic reducer pressure is measured through 100 release zones on Balfrin
  `postproc`; the consolidated series is in
  `balfrin_diagnostic_series_tb613.md`.
- Hazard throughput is measured for the bounded four-zone support point in
  TB-619, with TB-603 retained as the comparison baseline.
- Regional split work is measured at the bounded probe level by the current
  regional split run root, but it does not promote broader regional workflows.
- Swiss-wide workflows remain deferred phase changes.
- Older failed-closed submit branches remain guardrail evidence, not measured
  hazard execution evidence.
- Larger-output GIS/COG packaging is no longer blocked for the current largest
  package-capable hazard root: TB-631 measured 39 packaged files, 22 rasters,
  COG readiness, and layer parity.

## Evidence Classes

- Measured: single-job Balfrin evidence, restartability metadata, target-area
  canonical bundle evidence, uncertainty interpretation, GIS scope, claim
  boundaries, TB-312 four-zone postproc/reducer evidence, TB-407 smallest
  multi-zone evidence, current regional split comparison evidence, the
  diagnostic series through 100 release zones, TB-680/TB-681 bounded
  hazard-throughput support, TB-682 larger hazard-output pressure ladder, and
  TB-631 larger-output GIS/COG packaging.
- Projection-only: Swiss-scale feasibility estimates beyond the current
  24-zone hazard-throughput support pair and measured diagnostic support
  points.
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
the reproduction commands, run roots under `$SCRATCH`, submitted git heads, job
ids, runtime/memory/output/manifest measurements, and repeatability bounds.

## Boundaries

This package does not authorize scale-up, distributed execution, operational
use, annual frequency, physical probability, risk, exposure, or vulnerability
claims. It also does not treat failed-closed, diagnostic, or postproc-only
evidence as measured hazard execution. The next useful performance milestone is
a larger bounded hazard-throughput run if queue policy remains favorable; the
next scientific milestone is closing calibration, holdout, source-frequency,
and physical-probability evidence gaps.
