# Tschamut Public Pilot Ensemble-Size Feasibility

Status: selected-domain ensemble-size decision record for the public Tschamut
conditional pilot. This is a share-safe no-go gate for ensemble increase after
reviewing the executed but inconclusive target-scale evidence, not an
operational hazard-map assessment.

Validated record:
`validation/pilot_runs/tschamut_public_ensemble_feasibility_v1.yaml`

Validator:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/validate_pilot_ensemble_feasibility.py \
  validation/pilot_runs/tschamut_public_ensemble_feasibility_v1.yaml
```

## Decision

Decision: `no_go` for increasing the selected Tschamut ensemble beyond the
current target-scale diagnostic evidence.

The target-scale workflow now exists as local ignored execution evidence: 1,000
observed-release trajectories, summary-only conditional hazard layers,
runtime/memory/output-budget sidecars, checksums, and 1-vs-2 worker reducer
parity for compared outputs. It does not authorize ensemble increase because
the target evidence is itself `inconclusive`.

## Evidence Reviewed

- Small gate run-freeze:
  `validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml`
- Scaling review:
  `docs/tschamut_public_pilot_scaling_review.md`
- Manual GIS/QGIS visual QA record:
  `validation/pilot_runs/tschamut_public_gis_visual_qa_v1.yaml`
- Forest/obstacle scope record:
  `validation/pilot_runs/tschamut_public_obstacle_scope_v1.yaml`
- Target-scale gate evidence:
  `validation/pilot_runs/tschamut_public_scalable_conditional_target_gate_v1.yaml`

## Blockers

- Target-vs-small-gate convergence has not been accepted.
- Manual GIS/QGIS visual QA is explicitly blocked for the target-scale package
  because QGIS is unavailable and the ignored target package artifacts are
  absent in this checkout.
- Forest/obstacle omission remains `limiting` for interpretation.
- Validation-runner `ensemble_execution` provenance covers the auxiliary
  single-release 100-trajectory path, not all 1,000 observed-release target
  trajectories.
- Validation-side debug output volume remains too large for another increase
  without reduction or explicit justification.

## Scope Boundary

No physics, defaults, source weights, annual frequency, physical probability,
risk, exposure, vulnerability, or operational semantics are changed. No raw
swisstopo data, processed context layers, validation outputs, or hazard
products are committed.
