# TB-667 Greater-Than-Four-Zone Hazard-Throughput Profile

Date: 2026-05-27

TB-667 promoted the local multi-zone hazard-throughput profiler into an
explicit pre-submit surface for a hazard run shape larger than the four-zone
TB-619 package.

## Result

- Profile status: `profiled_scratch_root`
- Larger-package status: `ready_for_pre_submit`
- Release zones: `12`
- Trajectory files: `12`
- Impact-event files: `12`
- Hazard manifest:
  `/private/tmp/tb667_hazard_throughput_profile_after/output/explicit/hazard/multi_zone_hazard_profile_manifest.json`
- Dominant phase: `accumulation_seconds`
- Dominant layer family: `max_kinetic_energy`

## Replayable Budget

- Maximum output files: `40`
- Observed output files: `29`
- Maximum output bytes: `1,500,000`
- Observed output bytes: `1,145,440`
- Maximum manifest bytes: `60,000`
- Observed manifest bytes: `45,106`
- Summary-only curve export: required and active
- Conditional curve CSV table: suppressed for output budget
- Budget status: `within_budget`

## Reproduction

Materialize and profile a fresh 12-zone fixture:

```bash
PYENV_VERSION=system uv run python scripts/summarize_multi_zone_hazard_throughput_profile.py --materialize-root /tmp/rust_rockfall/multi_zone_hazard_throughput_profile_v2 --profile multi_zone --format json
```

Replay an already materialized profile root:

```bash
PYENV_VERSION=system uv run python scripts/summarize_multi_zone_hazard_throughput_profile.py --profile-root /tmp/rust_rockfall/multi_zone_hazard_throughput_profile_v2 --format json
```

## Boundary

This is local pre-submit hazard-throughput evidence. It proves that the local
package/profile targets more than four release zones and stays inside an
explicit replayable output budget. It is not yet a live Balfrin hazard-throughput
measurement, physical-probability evidence, annual-frequency evidence, or a
Swiss-wide run.
