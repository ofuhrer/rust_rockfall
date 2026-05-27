# TB-669 Balfrin 12-Zone Hazard-Throughput Probe

Date: 2026-05-27

TB-669 ran the first greater-than-four-zone hazard-throughput probe on Balfrin
`postproc`.

## Run

- Run root:
  `/scratch/mch/olifu/rust_rockfall/probes/tb669_12_zone_hazard_throughput_20260527_123917`
- SLURM job id: `4378015`
- Job name: `rr-haz12-tb669`
- Partition: `postproc`
- Terminal state: `COMPLETED`
- Exit code: `0:0`
- SLURM elapsed: `00:00:03`
- `/usr/bin/time` elapsed: `02.15`
- `/usr/bin/time` peak RSS: `47.016` MB

## Hazard-Throughput Profile

- Profile status: `profiled_scratch_root`
- Release zones: `12`
- Trajectory files: `12`
- Impact-event files: `12`
- Hazard-layer seconds: `0.078136`
- Total profile wall seconds: `0.288979`
- Output files: `29`
- Output bytes: `1,148,530`
- Run-root files: `93`
- Run-root bytes: `2,373,626`

## File Families

- `geotiff`: `11` files / `813,890` bytes
- `esri_ascii_grid`: `11` files / `280,720` bytes
- `json`: `6` files / `50,420` bytes
- `geojson`: `1` file / `3,500` bytes

## Manifest Families

- `reducer_execution_plan`: `15,561` bytes
- `reducer_chunk_manifest`: `15,329` bytes
- `hazard_metadata`: `13,035` bytes
- `reducer_execution_index`: `4,046` bytes

## Replay-Critical Families

- `trajectory_csv`: `12` of `12`
- `impact_events_csv`: `12` of `12`
- `deposition_csv`: `1` of `1`
- `diagnostics_json`: `1` of `1`

## Boundary

This is measured single-node `postproc` hazard-throughput evidence beyond the
four-zone TB-619 anchor. It is not diagnostic reducer-pressure evidence,
physical-probability evidence, annual-frequency evidence, operational evidence,
risk/exposure/vulnerability evidence, distributed execution evidence,
Swiss-wide execution, or non-`postproc` evidence.
