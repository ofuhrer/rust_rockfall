# TB-668 Larger Hazard Local Pre-Submit Proof

Date: 2026-05-27

TB-668 exercised the 12-zone hazard-throughput profile locally before any live
Balfrin submission.

## Result

- Local pre-submit status: `ready_for_submit`
- First blocker: none
- Release zones: `12`
- Hazard output profile: `provenance_audit`
- Output-profile classification: `scalable_default`
- Output files: `29`
- Output bytes: `1,144,485`
- Manifest bytes: `44,221`

## File Families

- `geotiff`: `11` files
- `esri_ascii_grid`: `11` files
- `json`: `6` files
- `geojson`: `1` file

## Replay-Critical Coverage

- `trajectory_csv`: `12` of `12`, consumed via `--ensemble-trajectories-dir`
- `impact_events_csv`: `12` of `12`, consumed via `--ensemble-impact-events-dir`
- `deposition_csv`: `1` of `1`, consumed via `--deposition`
- `diagnostics_json`: `1` of `1`, consumed via `--diagnostics`

## Command

```bash
PYENV_VERSION=system uv run python scripts/summarize_multi_zone_hazard_throughput_profile.py --materialize-root /tmp/tb668_hazard_pre_submit --profile multi_zone --format json --json-output /tmp/tb668_hazard_pre_submit.json --markdown-output /tmp/tb668_hazard_pre_submit.md
```

## Boundary

This is a local dry-run/pre-submit proof only. It does not submit to Balfrin and
does not establish live hazard-throughput, physical-probability,
annual-frequency, operational, risk/exposure/vulnerability, distributed,
Swiss-wide, or non-`postproc` evidence.
