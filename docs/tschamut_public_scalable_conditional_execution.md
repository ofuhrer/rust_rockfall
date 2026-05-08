# Tschamut Public Scalable Conditional Execution

Status: scalable conditional execution design and diagnostics contract for the
selected Tschamut public pilot. This is not operational validation and does not
add annual frequency, physical probability, return-period, risk, exposure, or
vulnerability semantics.

Validated record:
`validation/pilot_runs/tschamut_public_scalable_conditional_execution_v1.yaml`

Validator:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/validate_scalable_conditional_execution.py \
  validation/pilot_runs/tschamut_public_scalable_conditional_execution_v1.yaml
```

## Execution Design

The scalable conditional path uses the existing hazard-layer post-processor,
`scripts/build_hazard_layers.py`. It consumes already generated trajectory,
deposition, and impact-event outputs and does not call the simulator kernel or
change physics.

For local scaling, use explicit deterministic reducer workers:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/build_hazard_layers.py \
  --case validation/private/tschamut_public_pilot/gate_v1/tschamut_public_conditional_gate_case.yaml \
  --diagnostics validation/private/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_trajectory.csv \
  --trajectory-dir validation/private/tschamut_public_pilot/gate_v1/trajectories \
  --output-dir hazard/results/tschamut_public_pilot/scalable_conditional_v1 \
  --cell-size 2.0 \
  --grid-xmin 2696376.0 \
  --grid-ymin 1167384.0 \
  --grid-ncols 300 \
  --grid-nrows 304 \
  --grid-cell-size 2.0 \
  --probability-mode sampling_weighted_conditional \
  --kinetic-energy-exceedance-j 1000.0 \
  --kinetic-energy-exceedance-j 10000.0 \
  --jump-height-exceedance-m 1.0 \
  --jump-height-exceedance-m 2.0 \
  --conditional-curve-export summary-only \
  --reducer-workers 2 \
  --no-plots
```

Generated outputs remain ignored local artifacts unless intentionally reduced to
tiny fixtures.

## Chunk And Merge Contract

The runner partitions trajectory and impact inputs into deterministic contiguous
chunks. Chunk manifests use `hazard_reducer_chunk_manifest_v1`, with stable
chunk ids derived from the output prefix and sorted chunk index.

Reducer merge rules are reproducible:

- counts and densities add cellwise across chunks;
- maximum-energy and maximum-jump layers merge by cellwise maximum;
- chunk states are merged by the `sorted_chunk_id` rule after sorting by
  `chunk_id`;
- reducer output is expected to be independent of worker count for the same
  input set.

The run manifest now includes `conditional_hazard_execution_diagnostics_v1`,
which records reducer mode, worker count, chunk count, merge order, chunk
manifest count, summary-only curve export state, grid cell count, output budget
fields, and required convergence checks.

## Output-Volume Controls

Target-scale runs must use `--conditional-curve-export summary-only`. This keeps
conditional exceedance curve summaries in metadata while suppressing the large
per-cell curve table. Full curve-table export remains useful for small debug
runs but is not allowed for selected-domain scale-up.

Before increasing ensemble size, each candidate run must record:

- output file count;
- output bytes;
- total wall time;
- hazard input rows per second;
- reducer chunk manifest count;
- explicit grid dimensions and cell size.

## Convergence Diagnostics

The selected 60-trajectory gate is execution evidence, not convergence evidence.
Before increasing the Tschamut ensemble, record:

- trajectory-count sensitivity between the gate and target count;
- conditional-curve stability by threshold;
- supporting raster stability;
- probability-standard-error layers;
- worker-count reducer parity for the proposed count.

## Remaining Blockers

Scale-up remains blocked by:

- target-scale convergence not established;
- manual GIS/QGIS visual QA still inconclusive;
- forest/obstacle omission still limiting interpretation;
- target-scale output budget not measured.

The current supported labels remain `unweighted_diagnostic`,
`sampling_weighted_conditional`, and `conditional_intensity_exceedance`.
