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
- Local context review status: `reviewed_local_context`
- Target-scale scope-record status: `blocked_missing_context_layers`
- Operational status: `research_diagnostic`

Forest and obstacle omission is no longer only a missing-cache problem in this
checkout. Public context assets were staged under ignored paths for
swissSURFACE3D Raster, SWISSIMAGE, swissBUILDINGS3D, and swissTLM3D. The
local inspection now reports `reviewed_local_context` and classifies the
context as `limiting` across the reviewed categories: relevant
surface-height, building/structure, road/transport, barrier/protection,
hydrography, and visual context exists, but it remains interpretation
evidence rather than obstacle physics.

The target run still uses bare-earth swissALTI3D terrain and no obstacle
physics. The current conditional outputs may be useful workflow diagnostics,
but they must not be used to argue that vegetation, constructed features,
channels, barriers, or protection structures are irrelevant in the corridor.

## Context Inventory

| Category | Candidate public context | Current status | Interpretation |
| --- | --- | --- | --- |
| Forest/canopy | swissSURFACE3D Raster | Real tile staged locally | Limiting: sampled surface-minus-bare-earth context is present and not represented by bare-earth simulation. |
| Buildings/structures | swissBUILDINGS3D and swissTLM3D constructed features | swissBUILDINGS3D regional asset staged locally | Limiting: structure context is present but not clipped to feature counts or represented by physics. |
| Roads/transport | swissTLM3D roads, tracks, rail, paths | Real archive staged locally | Limiting: transport-context evidence is present and should not be treated as obstacle absence. |
| Barriers/protection | swissTLM3D constructed features plus local protection-work inventory where available | Real archive staged locally | Limiting: barrier/protection context is present but still not obstacle physics. |
| Water/channels | swissTLM3D hydrography and terrain review | Real archive staged locally | Limiting: hydrographic context is present and still separate from physics. |
| Visual QA | SWISSIMAGE | Real tile staged locally | Limiting: visual context is available, but it is not acceptance evidence by itself. |

## Executable Check

The scope record is validated with:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run python \
  scripts/validate_pilot_obstacle_scope.py \
  validation/pilot_runs/tschamut_public_obstacle_scope_v1.yaml \
  --format json
```

Expected result: `classification` is `blocked_pending_local_evidence`,
target-scale context review status is `blocked_missing_context_layers`, all six
required context categories are classified, and future context
downloads/review actions are explicit. The validator rejects missing context
categories, claimed obstacle physics, blocked or limiting records without
future context actions, acceptable classifications without reviewed target
context, and unqualified annual/return-period/risk or operational language.

For a concrete local inspection, run:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run python \
  scripts/inspect_tschamut_public_context_layers.py --format json
```

In the current local checkout this returns `status: limiting`,
`context_review_status: reviewed_local_context`, and
`spatial_relevance_status: reviewed_local_context`. The script exits nonzero
for any non-`acceptable` classification, so the limiting result should be read
as a conservative interpretation boundary, not as a tool failure.

The JSON report also separates `classification`, `context_review_status`,
`spatial_relevance_status`, `blocked_reason`, `selected_extent_or_corridor`,
`layers_expected`, `layers_available`, `layers_missing`, `source_products`,
`local_cache_paths`, `checksums`, `crs_or_spatial_reference`,
`spatial_relevance_indicators`, and `interpretation_impact`, while keeping
`operational_claims_allowed` false.
That makes local context evidence explicit without turning the staged
swisTLM3D archive into an obstacle-absence claim. The staged swissTLM3D
archive under `data/processed/swisstopo/tschamut_public_pilot/context/swisstlm3d/`
is intentionally kept separate from any clipped corridor product. The
metadata-only fixture under
`tests/fixtures/tschamut_context_layers/available/` is intentionally labeled as
a fixture and can be used to exercise the limiting/acceptable classification
path without pretending to be staged public geodata.

Measured local context indicators:

- swissSURFACE3D Raster asset:
  `data/processed/swisstopo/tschamut_public_pilot/context/swisssurface3d_raster/swisssurface3d-raster_2020_2696-1167_0.5_2056_5728.tif`
- swissSURFACE3D Raster SHA-256:
  `98b0828ac7fca19ce2ceb2ef448960f6643d77b682ff3e1bdec66040941184dd`
- SWISSIMAGE asset:
  `data/processed/swisstopo/tschamut_public_pilot/context/swissimage/swissimage-dop10_2019_2696-1167_2_2056.tif`
- SWISSIMAGE SHA-256:
  `77e91332a637fd9e42f72da30a3b3bc406d17f7d5700ee45b44aa1366c2deab9`
- swissBUILDINGS3D asset:
  `data/processed/swisstopo/tschamut_public_pilot/context/swissbuildings3d/swissbuildings3d_3_0_2021_1232-12_2056_5728.gdb.zip`
- swissBUILDINGS3D SHA-256:
  `5ad7f1803ecfe5cea9585aeea80001ec7e9d6a43e40896092b13faf7754a7d4d`
- sampled bare-earth DEM cells: `91200`
- fraction of sampled cells where surface is more than `2 m` above bare earth:
  `0.03584429824561403`
- surface-minus-bare-earth p95: `1.434826944921975 m`
- surface-minus-bare-earth max: `20.673950351562553 m`
- swisTLM3D source archive size from HEAD metadata: `3136564656` bytes;
  archive SHA-256:
  `e8ae3fdab1e0496ad780fcda4b58d04cc645808da94367b8ebaf51dad4bf6f0a`;
  the archive is staged locally and treated as limiting context evidence in the
  current inspection.

## Interpretation Boundary

Allowed current interpretation:

- the selected target-scale gate omits forest and obstacle effects;
- omission is a limiting context limitation for spatial interpretation, not a
  missing-cache problem;
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
inconclusive local diagnostic gate, decide whether the current limiting
context evidence should remain a blocker or be accepted under a documented
interpretation rule.

The next context review should update the scope record to
`blocked_pending_local_evidence`, `acceptable`, `limiting`, or `invalidating`
based on actual context evidence. It should not tune simulator parameters to
absorb omitted forest or obstacle effects.
