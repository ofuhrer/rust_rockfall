# Tschamut Public Pilot Ensemble-Size Feasibility

Status: selected-domain Target 5 decision record for the public Tschamut
conditional pilot. This is a share-safe no-go gate for ensemble increase, not a
new simulation result and not an operational hazard-map assessment.

Validated record:
`validation/pilot_runs/tschamut_public_ensemble_feasibility_v1.yaml`

Validator:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/validate_pilot_ensemble_feasibility.py \
  validation/pilot_runs/tschamut_public_ensemble_feasibility_v1.yaml
```

## Decision

Decision: `no_go` for increasing the selected Tschamut ensemble from the
completed small gate toward the proposed larger count.

The small gate remains useful execution evidence: it has frozen inputs,
deterministic sampling, local ignored validation and hazard artifacts, GIS
package manifests, scaling evidence, and conditional intensity-exceedance
outputs. It does not establish target-scale convergence.

## Evidence Reviewed

- Small gate run-freeze:
  `validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml`
- Scaling review:
  `docs/tschamut_public_pilot_scaling_review.md`
- Manual GIS/QGIS visual QA record:
  `validation/pilot_runs/tschamut_public_gis_visual_qa_v1.yaml`
- Forest/obstacle scope record:
  `validation/pilot_runs/tschamut_public_obstacle_scope_v1.yaml`

## Blockers

- Target-scale convergence is not established by the 60-trajectory gate.
- Manual GIS/QGIS visual QA remains `inconclusive`.
- Forest/obstacle omission remains `limiting` for interpretation.
- Any larger local run must use `--conditional-curve-export summary-only` and
  record runtime, memory, file count, byte count, and reducer-parity evidence.

## Scope Boundary

No physics, defaults, source weights, annual frequency, physical probability,
risk, exposure, vulnerability, or operational semantics are changed. No raw
swisstopo data, processed context layers, validation outputs, or hazard
products are committed.
