# Balfrin Regional Split Run-Root Metrics TB-566

Date: 2026-05-25

This note records the metrics, preservation, and output-budget collection for
the TB-565 regional split run. It is evidence preservation only; it does not
authorize a rerun, distributed execution, Swiss-wide execution, annual
frequency, physical probability, risk, exposure, vulnerability, regulatory, or
operational claims.

## Evidence Location

- Job id: `4367244`
- Run root: `/scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_multi_release_zone_v1`
- Evidence directory: `/scratch/mch/olifu/rust_rockfall/evidence/tb566_regional_split_run_4367244`
- Local summary transcript: `/tmp/tb566_collection_summary.txt`
- Metrics JSON: `balfrin_probe_metrics_collected_tb566.json`
- Preservation gate JSON/TXT: `balfrin_probe_preservation_gate_tb566.json`, `balfrin_probe_preservation_gate_tb566.txt`
- Output-budget audit JSON/TXT: `balfrin_run_root_output_budget_tb566.json`, `balfrin_run_root_output_budget_tb566.txt`

## Metrics

- Metrics contract status: `complete`
- Missing mandatory metrics: `[]`
- Report status: `measured_run_root`
- Validation output: `130` files / `34,565,330` bytes
- Hazard output: `57` files / `57,670,915` bytes
- Conditional curve rows: `729600`
- Collector wall time: `5.261369686049875` seconds
- Collector memory peak: `172.921875` MB

The metrics collector reports three unavailable ancillary fields for a future
run contract: `validation_output_mode`, `output_write_kind_seconds`, and
`output_write_kind_bytes`. These are not mandatory metrics and do not block the
current metrics contract.

## Preservation Gate

- Preservation gate status: `ready_for_demonstration_evidence`
- Metrics contract status: `complete`
- Required run-root entries status: `complete`
- Missing run-root entries: `[]`
- Output-family status: `sufficient`
- Missing required output families: `[]`
- Spatial/GIS artifact status: `declared`
- Blocked reasons: `[]`

The preservation gate classifies the run root as rebuildable reduced output
with the required manifest and chunk families present. It also records the
output-budget audit below as a separate blocker for compact replay-budget
promotion.

## Output-Budget Audit

- Audit status: `blocked_missing_replay_artifacts`
- Budget profile: `smallest_live_two_zone_probe`
- Missing replay-critical artifacts: `trajectory_csv`, `deposition_csv`, `impact_events_csv`
- Missing required hashes: `probe_manifest_sha256`

Budget blockers:

- `manifest_size_bytes=205049` exceeds `smallest_live_two_zone_probe.max_manifest_size_bytes=18000`.
- `output_file_count=57` exceeds `smallest_live_two_zone_probe.max_total_output_files=20`.
- `sidecar_file_count=17` exceeds `smallest_live_two_zone_probe.max_sidecar_files=11`.
- `reducer_manifest_bytes=43639` exceeds `smallest_live_two_zone_probe.max_reducer_manifest_bytes=400`.
- The projection is missing replay-critical output families: `trajectory_csv`, `deposition_csv`, `impact_events_csv`.
- The projection is missing replay-critical package hash `probe_manifest_sha256`.

This means the measured run root is preserved and usable as demonstration
evidence, but it is not yet a compact replay-budget template for the next
larger handoff.

## Evidence Hashes

| Evidence file | SHA-256 |
| --- | --- |
| `balfrin_probe_metrics_collected_tb566.json` | `943ed3c36cad0c80dbc0ec618d9e2644b9e22952b7a3ad069d26e664b24abb14` |
| `balfrin_probe_preservation_gate_tb566.json` | `ef2571365e4492905b9d675ff906ca4296336f2db4863fe5ec013c2d4e062229` |
| `balfrin_probe_preservation_gate_tb566.txt` | `3653896414567402a95fb250a2609726ff40b92e8c037b8cddbfb613f01a9dce` |
| `balfrin_run_root_output_budget_tb566.json` | `c2d816884a5ec4a4231f44a68df26d46ff4ec8d8eade999179d6aeefcf1eb2ba` |
| `balfrin_run_root_output_budget_tb566.txt` | `bddd632592d10f1ef474a4e86da5827e773480303a341aa50e39423f25e7bf07` |
| `collect_stdout.json` | `4537fa0011e2ced194922523cbdcec17abf73b8dd1f3364f220cf99f8b55fca2` |
| `output_budget_stdout.json` | `c2d816884a5ec4a4231f44a68df26d46ff4ec8d8eade999179d6aeefcf1eb2ba` |
| `preservation_stdout.json` | `ef2571365e4492905b9d675ff906ca4296336f2db4863fe5ec013c2d4e062229` |
