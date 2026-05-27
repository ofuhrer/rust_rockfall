# TB-672 Larger Run-Root Recovery

Date: 2026-05-27

TB-672 copied and reconstructed the latest larger hazard-throughput run root
without rerunning the simulation.

## Run Roots

- Source run root:
  `/scratch/mch/olifu/rust_rockfall/probes/tb669_12_zone_hazard_throughput_20260527_123917`
- Recovered run root:
  `/scratch/mch/olifu/rust_rockfall/restartability/tb672_tb669_recovery_20260527_132017`
- Recovery summary:
  `/scratch/mch/olifu/rust_rockfall/restartability/tb672_tb669_recovery_20260527_132017/tb672_recovery_summary.json`

## Copy Footprint

- Source size: `2,431,977` bytes
- Recovered size: `2,446,580` bytes
- Mandatory artifact count: `8`
- Missing mandatory artifacts: none
- Mandatory artifact checksum match: `true`

Mandatory artifacts checked:

- `multi_zone_hazard_throughput_profile.json`
- `multi_zone_hazard_throughput_profile.md`
- `tb669_collected_summary.json`
- `time_verbose.txt`
- `slurm_accounting.psv`
- `tb669_hazard.sbatch`
- `profile/input/multi_zone_hazard_profile_fixture_manifest.json`
- `profile/output/explicit/hazard/multi_zone_hazard_profile_manifest.json`

## Reconstructed Metrics

- Status: `measured_reconstructed_from_preserved_files`
- Metrics regenerated without rerun: `true`
- Reconstructed summary matches source: `true`
- Release zones: `12`
- Trajectory files: `12`
- Impact-event files: `12`
- Output files: `29`
- Output bytes: `1,148,530`
- Hazard-layer seconds: `0.078136`
- Total profile wall seconds: `0.288979`

## Boundary

This is copied-root restartability/recovery evidence for one preserved
single-node `postproc` hazard-throughput run root. It does not prove live job
interruption/resume, distributed execution, non-`postproc` execution,
Swiss-wide execution, physical-probability semantics, or operational readiness.
