# Tschamut Public Pilot Forest And Obstacle Context Scope

Status: share-safe target-scale interpretation review for forest, building,
road, channel, barrier, and visual-context omission in the selected Tschamut
public conditional pilot. This document does not add obstacle physics, tune
model parameters, download or commit context geodata, define exposure or
vulnerability, or approve an operational hazard product.

## Classification

- Pilot id: `tschamut_public_pilot`
- Run id: `tschamut_public_scalable_conditional_target_gate_v1`
- Scope record:
  `validation/pilot_runs/tschamut_public_obstacle_scope_v1.yaml`
- Current classification: `limiting`
- Target-scale context review status: `blocked_missing_context_layers`
- Operational status: `research_diagnostic`

Forest and obstacle omission remains a limiting boundary condition for
interpreting the executed target-scale gate. The target run uses bare-earth
swissALTI3D terrain and no reviewed local context crop for canopy, buildings,
roads, channels, protection works, or orthophoto alignment. The current
conditional outputs may still be useful workflow diagnostics, but they must not
be used to argue that vegetation, constructed features, channels, barriers, or
protection structures are irrelevant in the corridor.

The local check for this milestone found no
`data/processed/swisstopo/tschamut_public_pilot/context/` directory and no
raw public context products beyond the existing swissALTI3D tile. Therefore
the context review is not a passed visual/context review; it is a documented
blocker for scientific interpretation of the target-scale package.

## Context Inventory

| Category | Candidate public context | Current status | Interpretation |
| --- | --- | --- | --- |
| Forest/canopy | swissSURFACE3D Raster or swissSURFACE3D point cloud | Documented, not downloaded/reviewed | Bare-earth DEM output cannot rule out canopy or forest-floor effects. |
| Buildings/structures | swissBUILDINGS3D and swissTLM3D constructed features | Documented, not downloaded/reviewed | Current outputs do not represent structure interaction, shielding, or consequence. |
| Roads/transport | swissTLM3D roads, tracks, rail, paths | Documented, not downloaded/reviewed | Corridor interpretation cannot decide whether roads, tracks, or embankments are relevant obstacles. |
| Barriers/protection | swissTLM3D constructed features plus local protection-work inventory where available | Documented, not downloaded/reviewed | Current trajectories are not evidence for protection-structure performance or omission. |
| Water/channels | swissTLM3D hydrography and terrain review | Documented, not downloaded/reviewed | DEM-only outputs cannot classify whether channelized terrain or water features affect runout interpretation. |
| Visual QA | SWISSIMAGE | Documented, not downloaded/reviewed | Orthophoto review remains needed for release/source-zone and corridor sanity checks. |

## Executable Check

The scope record is validated with:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run python \
  scripts/validate_pilot_obstacle_scope.py \
  validation/pilot_runs/tschamut_public_obstacle_scope_v1.yaml \
  --format json
```

Expected result: `classification` is `limiting`, target-scale context review
status is `blocked_missing_context_layers`, all six required context categories
are classified, and future context downloads/review actions are explicit. The
validator rejects missing context categories, claimed obstacle physics,
limiting records without future context actions, acceptable classifications
without reviewed target context, and unqualified annual/return-period/risk or
operational language.

## Interpretation Boundary

Allowed current interpretation:

- the selected target-scale gate omits forest and obstacle effects;
- omission is a documented limitation for spatial interpretation;
- future review should use SWISSIMAGE, swissTLM3D, swissSURFACE3D or
  swissSURFACE3D Raster, and swissBUILDINGS3D where relevant;
- current outputs remain conditional diagnostics over the supplied DEM,
  release cells, block scenarios, and sampling weights.

Unsupported current interpretation:

- forest, canopy, buildings, roads, barriers, protection works, or channels are
  physically represented by the simulator;
- current restitution, roughness, terrain classes, stopping thresholds, or
  scenario weights compensate for omitted obstacles;
- current outputs are physical probability, annual frequency, return-period,
  risk, exposure, vulnerability, or operational hazard-map products.

## Required Before Interpretation

Before interpreting Tschamut target-scale spatial patterns as more than an
inconclusive local diagnostic gate, restore or download public context layers
for the selected extent:

1. SWISSIMAGE for visual corridor and release-zone sanity checks.
2. swissTLM3D for roads, tracks, hydrography, and constructed features.
3. swissSURFACE3D or swissSURFACE3D Raster for canopy/surface-height context.
4. swissBUILDINGS3D where building or structure context is relevant.

The next context review should update the scope record to
`acceptable`, `limiting`, or `invalidating` based on actual context evidence.
It should not tune simulator parameters to absorb omitted forest or obstacle
effects.
