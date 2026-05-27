# TB-681 Balfrin 24-Zone Hazard-Throughput Repeat

Date: 2026-05-27

TB-681 repeated the TB-680 bounded hazard-throughput shape on Balfrin
`postproc` to separate stable output behavior from one-off scheduler noise.

## Run

- Run root:
  `/scratch/mch/olifu/rust_rockfall/probes/tb681_24_zone_hazard_throughput_repeat_20260527_151222`
- SLURM job id: `4379224`
- Job name: `rr-haz24-tb681`
- Partition: `postproc`
- Terminal state: `COMPLETED`
- Exit code: `0:0`
- SLURM elapsed: `00:00:03`
- `/usr/bin/time` elapsed: `0:02.25`
- `/usr/bin/time` peak RSS: `41,652` kB (`40.6758` MB)

## Hazard-Throughput Profile

- Profile status: `profiled_scratch_root`
- Release zones: `24`
- Profile id: `multi_zone_24_zone_custom`
- Trajectory files: `24`
- Impact-event files: `24`
- Hazard-layer seconds: `0.083988`
- Total profile wall seconds: `0.317613`
- Output files: `29`
- Output bytes: `1,169,610`
- Run-root files: `116`
- Run-root bytes: `2,534,753`
- Conditional-curve rows represented in summary-only mode: `36,864`

## Variability Against TB-680

- Same release-zone count: yes
- Same hazard output file count: yes
- Same conditional-curve row count: yes
- Profile wall delta: `+0.044857` s, about `16%` slower than TB-680
- Hazard-layer delta: `-0.001945` s
- Peak RSS delta: `-0.2617` MB
- Hazard output byte delta: `-354` bytes
- Manifest byte delta: `-339` bytes

Use the slower repeat wall time, `0.317613` s, as the conservative planning
coefficient until a larger hazard-throughput support point exists.

## Replay Budget

- Output file budget: pass (`29` <= `40`)
- Output byte budget: pass (`1,169,610` <= `1,500,000`)
- Manifest byte budget: fail (`63,653` > `60,000`)
- Conditional-curve table suppressed: pass
- Overall replay budget: fail on manifest bytes

## Boundary

This is repeat measured single-node `postproc` hazard-throughput evidence for
the TB-680 24-zone shape. It is not physical-probability evidence,
annual-frequency evidence, operational evidence, risk/exposure/vulnerability
evidence, distributed execution evidence, Swiss-wide execution, or
non-`postproc` evidence.
