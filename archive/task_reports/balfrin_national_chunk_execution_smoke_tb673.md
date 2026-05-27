# TB-673 Balfrin National Chunk Execution Smoke

Date: 2026-05-27

## Result

A tiny national-chunk-shaped smoke ran successfully on Balfrin `postproc` and
wrote restartable manifest/state outputs for representative first, middle, and
last chunks from the Swiss national chunk mapping.

Run root:

`/scratch/mch/olifu/rust_rockfall/swiss_wide_smokes/tb673_national_chunk_smoke_20260527_152950_pycompat`

Scheduler job:

- Job id: `4378565`
- State: `COMPLETED`
- Exit code: `0:0`
- SLURM elapsed: `00:00:02`
- `/usr/bin/time` elapsed: `0:00.07`
- Peak RSS: `10668` KB

## Measured Smoke

- Status: `measured_chunk_manifest_state_smoke_missing_payload_data`
- National mapping size: `85` chunks across `11` merge groups
- Sampled chunks: `3`
- Sampled chunk ids:
  - `swiss_lv95_1km_terrain_chunk_0000`
  - `swiss_lv95_1km_terrain_chunk_0042`
  - `swiss_lv95_1km_terrain_chunk_0084`
- Sampled tiles: `1516` of `43500`
- Sample fraction of chunks: `0.035294`
- Sample fraction of tiles: `0.034851`
- Required sampled `swissALTI3D` bytes represented by the mapping:
  `1,516,000,000`
- Optional sampled context bytes represented by the mapping:
  `97,024,000,000`
- Smoke wall time inside the Python worker: `0.011102` seconds
- Output files: `13`
- Output bytes: `134,092`

## Output Shape

Each sampled national chunk wrote:

- `chunks/<chunk_id>/manifest.json`
- `chunks/<chunk_id>/state.json`

The manifests preserve the national mapping fields needed by the restart
boundary: chunk id, chunk index, tile index range, tile count, merge group,
expected input byte classes, expected output classes, and an execution
signature.

## Inventory Comparison

The smoke exercised the same chunk identifiers and restart boundaries described
by `docs/swiss_national_tile_chunk_mapping_tb608.json`.

The national mapping projects:

- `43,500` national 1 km tiles
- `85` terrain chunks
- `11` merge groups
- nominal chunk size of `512` tiles, with a final `492`-tile chunk

This smoke covered one chunk from the first merge group, one from the middle
merge group, and the final partial chunk. It therefore confirms that the
national mapping can drive executable Balfrin chunk-manifest/state work, but it
does not yet process the underlying raster payloads.

## Missing Payload Blocker

The concrete blocker for real national payload processing is:

- Required family: `swissALTI3D national 2 m chunk payloads`
- Product key: `swissalti3d_2m_raw_float32`
- Optional context families for richer processing: `SWISSIMAGE`,
  `swissSURFACE3D Raster`

## Boundary

This is a Balfrin chunk-orchestration smoke. It does not claim Swiss-wide DEM
cell processing, hazard simulation, distributed execution, physical probability,
or operational risk output.
