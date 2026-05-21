# AOI Conditional Map Workflow Contract

Status: frozen executable contract for the canonical AOI-to-conditional-map
front door. This document names the user-facing phases exposed through
`scripts/run_aoi_hazard_workflow.py` and keeps the workflow readable without
requiring backlog history or maturity narration.

## Purpose

The repository already has the pieces for AOI preparation, candidate review,
scenario generation, bounded execution, post-processing, GIS packaging, and
interpretation. This contract freezes those pieces into one named workflow so
new workers can follow a single phase model instead of rediscovering helper
commands.

The contract is intentionally diagnostic and non-operational. It does not
authorize simulation, scale-up, annual-frequency semantics, physical
probability semantics, or risk/exposure/vulnerability claims.

## Canonical Phases

1. Prepare inputs.
   - Front door: `scripts/run_aoi_hazard_workflow.py status`
   - Preparation gate: `scripts/run_aoi_hazard_workflow.py prepare`
   - Purpose: bootstrap AOI inputs, verify public geodata, and stop before any
     simulation work is attempted.

2. Review candidate release zones.
   - Front door: `scripts/run_aoi_hazard_workflow.py candidate-review`
   - Purpose: inspect the bounded candidate set and review overlays before the
     scenario table is frozen.

3. Generate scenarios.
   - Front door: `scripts/generate_candidate_source_zone_scenarios.py --mode freeze`
   - Purpose: materialize the deterministic scenario table from the reviewed
     candidate package.

4. Run bounded execution.
   - Front door: `scripts/run_aoi_hazard_workflow.py run-prepared-pilot-local`
   - Companion smoke path: `scripts/run_aoi_hazard_workflow.py run-local-smoke`
   - Purpose: execute the bounded local smoke path or the prepared pilot
     wrapper without expanding the claim boundary.

5. Post-process results.
   - Front door: `scripts/run_aoi_hazard_workflow.py package-map`
   - Companion helper: `scripts/run_aoi_hazard_workflow.py collect`
   - Purpose: reduce validation outputs into map-ready products and package
     manifests.

6. Package GIS outputs.
   - Front door: `scripts/package_aoi_hazard_map.py`
   - Purpose: build the review package, manifest, and optional pilot GIS
     bundle for GIS review.

7. Interpret results.
   - Front door: `scripts/run_aoi_hazard_workflow.py workflow`
   - Purpose: open the QA review surface and read the limitations before
     acting on the outputs.

## Contract Rules

- Keep the phase order stable.
- Use the front door commands above rather than introducing new parallel
  helper names for the same phase.
- Preserve the read-only boundary at the front door.
- Treat the generated map package and QA review as diagnostic outputs, not as
  operational or probabilistic evidence.

## Discoverability

The front door script prints this phase model in `--help`, `status`, and
`workflow` text output. The same contract is recorded in the JSON report as
`workflow_contract` so downstream tooling can reference one canonical phase
model.
