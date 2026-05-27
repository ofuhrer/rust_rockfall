# TB-305 Balfrin Postproc Microbenchmark Evidence

Date: 2026-05-19

Status: measured on Balfrin `postproc`

This evidence records one bounded synthetic post-processing microbenchmark run.
It measures workflow-shell overhead only: filesystem scan, manifest scan,
reducer merge, and lightweight package assembly. It is not a simulation, hazard
calibration, scale-up proof, distributed-execution result, physical-probability
result, risk result, or operational hazard assessment.

## Run

- Job id: `4339870`
- Run root:
  `/scratch/mch/olifu/rust_rockfall/probes/balfrin_postproc_microbenchmark_v1/tb305_20260519T190459Z`
- Partition: `postproc`
- Job shape: one node, one task, one CPU requested, five-minute wall limit
- Package shape: `file_count=128`, `manifest_size_bytes=65536`,
  `sidecar_count=16`, `reducer_chunk_count=8`, `payload_bytes=128`
- Package readiness gate: `ready`, package bytes `97982` against a local
  microbenchmark gate cap of `10000000`
- Preservation status: `preserved_remote_run_root`; required entries present

## Scheduler Evidence

`sacct -j 4339870 --format=JobID,JobName,Partition,State,ExitCode,Elapsed,TotalCPU,AllocCPUS,MaxRSS,MaxDiskRead,MaxDiskWrite,WorkDir -P`
reported:

- `4339870|tb305-postproc-micro|postproc|COMPLETED|0:0|00:00:01|00:00.233|2||||/users/olifu`
- `4339870.batch|batch||COMPLETED|0:0|00:00:01|00:00.231|2|5456K|0|0.00M|`
- `4339870.extern|extern||COMPLETED|0:0|00:00:01|00:00.001|2|660K|0.00M|0.00M|`

The runner-side `/usr/bin/time -v` record reported user time `0.07` seconds,
system time `0.11` seconds, elapsed wall time `0:01.23`, and maximum resident
set size `33012` kbytes.

## Runner Measurements

The generated harness wrote
`package/output/balfrin_postproc_microbenchmark_measurements.json` with:

- Measurement status: `measured_postproc_shell_overhead`
- Wall seconds: `0.6338623960000405`
- CPU seconds: `0.048968283`
- Peak RSS: `32624` kbytes
- File scan seconds: `0.1271800529975735`
- Manifest scan seconds: `0.2482742709980812`
- Reducer merge seconds: `0.17694826799925067`
- Package seconds: `0.08144542599984561`
- Files touched: `154`
- Bytes touched: `89802`

Logs were preserved at `logs/slurm-4339870.out` and
`logs/slurm-4339870.err`; both files were empty.

## Checksums

The run root contains `checksums.sha256` with:

- `4ff21c6f0f2d51b26e3e07966b7be0b680d94453db07037ecadb7a02f99987f4`
  `package_generation.json`
- `30b1dbac8c97be95a45138d78056a145096294907439a65465b3680d4549ba25`
  `package_readiness_gate.json`
- `4ff21c6f0f2d51b26e3e07966b7be0b680d94453db07037ecadb7a02f99987f4`
  `package/balfrin_postproc_microbenchmark_package.json`
- `07718e6d489decdf919423f2ddae65c4970529c3e6dfaa57ddce069baf9b45c6`
  `package/output/balfrin_postproc_microbenchmark_measurements.json`
- `07718e6d489decdf919423f2ddae65c4970529c3e6dfaa57ddce069baf9b45c6`
  `runner_stdout.json`
- `1c971df38a93e357455915b5041c8f1484d3f7837ac2283ccd1a7dac61d5106e`
  `runner_time_v.txt`

## Boundary

This evidence is synthetic post-processing shell overhead only. It does not
authorize non-`postproc` partitions, MPI, GPU, multi-node work, distributed
execution, physics changes, scale-up claims, operational claims,
annual-frequency claims, physical-probability claims, or
risk/exposure/vulnerability claims.
