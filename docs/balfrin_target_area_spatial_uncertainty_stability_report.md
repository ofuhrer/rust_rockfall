# Balfrin Target-Area Spatial Uncertainty And Stability Report

- Status: `blocked_missing_inputs`
- Target-area probe run root: `/scratch/mch/olifu/rust_rockfall/probes/tschamut_public_balfrin_target_area_demo_v1/authorized_tb168_20260517`
- Probe metrics report: `blocked_missing_run_root`
- Target-area evidence bundle: `mixed_provenance`
- GIS/COG scope: `blocked_missing_products`

## What Is Available

The frozen target-area contract and a measured remote Balfrin target-area run
exist, but the local tracked checkout still does not contain target-area hazard
layers or spatial-uncertainty artifacts. This report therefore remains a local
blocked-artifacts note, not a claim that the remote probe did not run.

- `scripts/summarize_balfrin_target_area_evidence_bundle.py` reports
  `bundle_status=mixed_provenance`.
- The target-area handoff section records the frozen contract and remote run
  root, but the local artifact sections remain unavailable.
- The probe-metrics section is `blocked_missing_inputs` when the preserved
  Balfrin run root is not mounted in this checkout.
- The canonical Balfrin evidence bundle remains measured, but it is not a
  target-area spatial-uncertainty artifact and must not be treated as one.
- `scripts/summarize_balfrin_target_area_gis_cog_scope.py` reports the target
  demo as `blocked_missing_products` with no hazard layers generated.

## Uncertainty, Stability, Persistence, Hotspots

No measured target-area spatial uncertainty summary is available from the
preserved artifacts in this repository.

- Persistent regions: unavailable.
- Unstable regions: unavailable.
- Support/nodata-sensitive regions: unavailable.
- Magnitude-sensitive regions: unavailable.
- Hotspot persistence: unavailable.

Reason:

- the preserved target-area run root is missing locally;
- the probe metrics helper therefore returns
  `blocked_missing_run_root`;
- the target-area demo contract itself is template-only and does not contain a
  measured hazard build;
- the GIS/COG audit confirms that no hazard layers or converted COG package
  are available for this target-area handoff.

## Conservative Boundary Language

This report keeps the same conservative boundary language used by the
Tschamut same-scale summaries:

- no closure upgrade by assertion;
- no operational hazard-map claim;
- no physical probability claim;
- no annual-frequency claim;
- no scale-up authorization;
- no distributed-execution authorization.

The missing target-area uncertainty inputs are a blocked-artifacts condition,
not a scientific finding about convergence, closure, or stability.

## Evidence-Bundle Integration Notes

This report is the target-area companion note for the existing evidence bundle.
It should be cited alongside the bundle, not merged into it as measured
evidence.

- The evidence bundle currently combines a `template_only` handoff, a blocked
  probe-metrics report, and a measured canonical bundle.
- The bundle can point to this report as the explicit spatial-uncertainty and
  stability gap note.
- The bundle must not use the measured canonical bundle as surrogate target-
  area uncertainty evidence.
- If a future run root and target-area uncertainty artifacts are staged, the
  blocked status should be re-evaluated from those artifacts rather than from
  the current template-only handoff.

## Commands Checked

```text
PYENV_VERSION=system uv run python scripts/summarize_balfrin_probe_metrics_report.py --run-root /scratch/mch/olifu/rust_rockfall/probes/tschamut_public_balfrin_target_area_demo_v1/authorized_tb168_20260517 --format json
PYENV_VERSION=system uv run python scripts/summarize_balfrin_target_area_evidence_bundle.py --format json
PYENV_VERSION=system uv run python scripts/summarize_balfrin_target_area_gis_cog_scope.py --format json
```
