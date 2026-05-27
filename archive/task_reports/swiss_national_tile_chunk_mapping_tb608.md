# Swiss National Tile-To-Chunk Mapping TB-608

Date: 2026-05-26

Status: deterministic prototype mapping from the TB-607 inventory. No national
tile manifest was staged and no execution was authorized.

Machine-readable mapping:
`docs/swiss_national_tile_chunk_mapping_tb608.json`

Source inventory:
`docs/swiss_national_tiling_inventory_tb607.json`

## Chunking Policy

- Input tile set: future sorted national LV95 1 km tile manifest
- Source inventory tile count: `43,500`
- Tile sort key: lexical `tile_id`
- Chunk size: `512` tiles
- Chunk count: `85`
- Merge group size: `8` chunks
- Merge group count: `11`
- Scheduler rule: `chunk_index % scheduler_count == scheduler_index`
- Chunk ID template: `swiss_lv95_1km_terrain_chunk_{chunk_index:04d}`
- Merge group ID template: `swiss_lv95_1km_merge_group_{merge_group_index:04d}`

This is intentionally an index-range mapping rather than a fabricated list of
national tile IDs. Once a real national manifest exists, each chunk receives
the sorted tile IDs in its `[tile_index_start_inclusive,
tile_index_end_exclusive)` range.

## Byte Envelope

National input estimates carried into the mapping:

- swissALTI3D 2 m raw float32 terrain: `43.5 GB`
- optional SWISSIMAGE 25 cm RGB raw context: `2.088 TB`
- optional swissSURFACE3D Raster 0.5 m float32 context: `696 GB`

Per full 512-tile chunk:

- swissALTI3D 2 m raw float32 terrain: `512 MB`
- optional SWISSIMAGE 25 cm RGB raw context: `24.576 GB`
- optional swissSURFACE3D Raster 0.5 m float32 context: `8.192 GB`

Last chunk `swiss_lv95_1km_terrain_chunk_0084` contains `492` tiles.

## Restart Boundaries

Each chunk has stable scratch paths:

- state:
  `$SCRATCH/rust_rockfall/swiss_wide/chunks/{chunk_id}/state.json`
- manifest:
  `$SCRATCH/rust_rockfall/swiss_wide/chunks/{chunk_id}/manifest.json`

Reuse is valid only when chunk id, tile index range, sorted tile ids, product
versions, checksums, and execution signature match. Maximum chunk attempts are
`3`, matching the existing chunk-reducer retry contract.

Each merge group writes:

`$SCRATCH/rust_rockfall/swiss_wide/merge_groups/{merge_group_id}/merge_state.json`

Merge order is `sorted_chunk_id`.

## Local Validation

The mapping validates these invariants:

- chunk tile counts sum to `43,500`
- chunk ids are unique
- merge group ids are unique
- every chunk is assigned to exactly one merge group

## Boundary

This is a prototype planner artifact. It does not prove national data
availability, download or stage public geodata, authorize Swiss-wide execution,
or change operational, annual-probability, risk, exposure, or vulnerability
claims.
