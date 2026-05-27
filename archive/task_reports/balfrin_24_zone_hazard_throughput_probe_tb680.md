# TB-680 Balfrin 24-Zone Hazard-Throughput Probe

Date: 2026-05-27

TB-680 ran the next bounded hazard-throughput scale-up on Balfrin `postproc`,
moving the measured hazard-throughput support point from 12 to 24 release
zones.

## Run

- Run root:
  `/scratch/mch/olifu/rust_rockfall/probes/tb680_24_zone_hazard_throughput_preserved_20260527_145422`
- SLURM job id: `4379134`
- Job name: `rr-haz24-tb680b`
- Partition: `postproc`
- Terminal state: `COMPLETED`
- Exit code: `0:0`
- SLURM elapsed: `00:00:01`
- `/usr/bin/time` elapsed: `0:00.70`
- `/usr/bin/time` peak RSS: `41,920` kB (`40.9375` MB)

An earlier same-shape job, `4379125`, completed successfully but used the run
root itself as the profiler materialization directory. The profiler recreated
that directory and removed its own SLURM script/log artifacts, so job `4379134`
is the preserved support point.

## Hazard-Throughput Profile

- Profile status: `profiled_scratch_root`
- Release zones: `24`
- Profile id: `multi_zone_24_zone_custom`
- Trajectory files: `24`
- Impact-event files: `24`
- Hazard-layer seconds: `0.085933`
- Total profile wall seconds: `0.272757`
- Output files: `29`
- Output bytes: `1,169,964`
- Run-root files: `117`
- Run-root bytes: `2,488,907`
- Conditional-curve rows represented in summary-only mode: `36,864`

## Replay Budget

- Output file budget: pass (`29` <= `40`)
- Output byte budget: pass (`1,169,964` <= `1,500,000`)
- Manifest byte budget: fail (`63,992` > `60,000`)
- Conditional-curve table suppressed: pass
- Overall replay budget: fail on manifest bytes

## Boundary

This is measured single-node `postproc` hazard-throughput evidence beyond the
12-zone TB-669 anchor. It is not physical-probability evidence,
annual-frequency evidence, operational evidence, risk/exposure/vulnerability
evidence, distributed execution evidence, Swiss-wide execution, or
non-`postproc` evidence.
