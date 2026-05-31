# TB-684 Largest Hazard Run Recovery

Date: 2026-05-31

TB-684 copied, inspected, and summarized the largest recent preserved
single-node hazard-output run without submitting a scheduler job or rerunning
simulation.

## Run Roots

- Source run root:
  `/scratch/mch/olifu/rust_rockfall/probes/tb682_384_zone_hazard_output_pressure_20260527_153407`
- Recovered run root:
  `/scratch/mch/olifu/rust_rockfall/restartability/tb684_tb682_384_recovery_20260531_202648`
- Source job id: `4379371`
- Release zones: `384`
- Recovery summary:
  `/scratch/mch/olifu/rust_rockfall/restartability/tb684_tb682_384_recovery_20260531_202648/tb684_recovery_report.json`

## Copy And Manifest

- Source payload files: `836`
- Recovered payload files: `836`
- Source payload bytes: `4,109,133`
- Recovered payload bytes: `4,109,133`
- Payload checksum match: `true`
- Missing payload paths: none
- Extra payload paths: none
- Mismatched payload paths: none

Mandatory replay-critical artifacts were complete, including the TB-682 profile
JSON/Markdown, scheduler stdout/stderr for job `4379371`, time/du/file-list
records, the pressure sbatch script, the input fixture manifest, and the
explicit hazard manifest, execution plan, reducer execution index, and reducer
merge state.

## Regenerated Metrics

- Status: `measured_reconstructed_from_preserved_files`
- Profile id: `multi_zone_384_zone_custom`
- Release zones: `384`
- Trajectory files: `384`
- Impact-event files: `384`
- Output files: `29`
- Output bytes: `1,536,400`
- Manifest bytes: `325,518`
- Hazard-layer seconds: `0.3593194429995492`
- Total profile wall seconds: `0.5879617109894753`
- Replay-critical coverage complete: `true`

## Sufficiency

The recovered 384-zone run root is sufficient for checksum replay, inspection,
and metric regeneration from preserved artifacts. It is not a replay-ready scale
support point under the current output budgets: the run remains blocked by
hazard-output bytes (`1,536,400` > `1,500,000`) and manifest bytes (`325,518` >
`60,000`).

## Boundary

This is copied-root recovery and replay-inspection evidence for one preserved
single-node `postproc` hazard-output pressure run. No scheduler job was
submitted for TB-684, and no simulation was rerun. This does not introduce
scale-up authorization, distributed execution, non-`postproc` execution,
physical-probability, annual-frequency, operational, risk, exposure, or
vulnerability claims.
