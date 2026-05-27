# TB-678 Swiss-Scale Demonstration Readiness

Date: 2026-05-27

## Decision

Do not submit a Swiss-wide or distributed run yet.

The repo now has strong Balfrin evidence for bounded single-node `postproc`
execution, restartability, isolated concurrent run roots, and national-chunk
orchestration. It does not yet have the data, accepted science, distributed
authorization, or operational review needed for a full Swiss-scale
demonstration.

## Measured Support Points

| Capability | Latest measured support |
| --- | --- |
| Hazard throughput | TB-669: 12 release zones, job `4378015`, `0.288979` s profile wall time, `47.016` MB peak RSS, `29` hazard files, `1,148,530` hazard bytes |
| Diagnostic reducer pressure | TB-612: 100-zone diagnostic, job `4372447`, `304` output files, `121,172` bytes, `34.16` MB peak RSS |
| Fresh compact diagnostic | TB-665: 32-zone diagnostic, job `4377419`, `5.39` s reducer wall time, `100` output files, `42,188` bytes |
| Concurrent isolated roots | TB-671: three 16-zone diagnostics, jobs `4378322`, `4378358`, `4378359`, all `COMPLETED`, no contention detected |
| Larger-run recovery | TB-672: copied TB-669 run root and regenerated metrics from preserved files with checksum match |
| National chunk shape | TB-673: 3 representative national chunks, `1516` tiles, manifest/state smoke on Balfrin job `4378565` |
| Minimum second-site cache | TB-674: real staged Chant Sura `swissALTI3D` terrain cache verifies `ready` |
| Second-site prepared pilot | TB-675: prepare reaches `ready_for_planning`, local run blocks first on `context/swissimage` |
| Calibration acceptance | TB-676: selected candidate rejected by `holdout_runout_abs_error_max_m` (`55.111764` m > `30.0` m) |
| Physical-probability prototype | TB-677: fail-closed; design gate remains deferred and prototype authorization is `false` |

## Swiss-Scale Envelope

From `scripts/estimate_swiss_wide_execution_envelope.py`:

- Measured support: `1` AOI, `12` release zones, `6` trajectories per release
  zone, `60` units per job.
- Swiss planning case: `26` AOIs, `260` release zones, `1560`
  trajectories.
- National input estimate: `10,321,250,000` DEM cells, `41,285,000,000`
  DEM bytes, `123,855,000,000` context bytes, `165,140,000,000` total input
  bytes.
- Phase-change status: `deferred`.
- First Swiss-wide phase-change blocker: `distributed_execution_authorization`.
- First data blocker: `national_public_geodata_inventory`.
- First validation blocker: accepted multi-site scientific evidence; the
  current calibration candidate is explicitly rejected.

## Go / No-Go

Ready now:

- Show bounded single-node Balfrin feasibility.
- Show reducer-pressure diagnostics through 100 zones.
- Show one bounded 12-zone hazard-throughput support point.
- Show restartability from preserved run-root artifacts.
- Show isolated concurrent `$SCRATCH` roots for small diagnostics.
- Show national chunk mapping can drive executable manifest/state work.

Not ready:

- Swiss-wide DEM/context payload processing.
- Distributed scheduler orchestration.
- Non-`postproc` execution.
- Accepted calibration/validation for physical probability.
- Real second-site prepared pilot.
- Operational, return-period, risk, exposure, or vulnerability products.

## Recommended Next Balfrin Action

Reject any Swiss-wide `sbatch` for now.

The next executable Balfrin demonstration should be a bounded hazard-throughput
scale-up beyond TB-669, not another diagnostic-only run. Use the TB-669 package
shape and submit only after the package states:

- release-zone count above `12`,
- `$SCRATCH` run root,
- summary-only/reduced output profile,
- preserved replay-critical artifacts,
- no physical-probability or operational labels,
- expected output footprint below the TB-669 recovery budget class.

If a command is needed today, the safe action is review/regeneration, not
submission:

```bash
PYENV_VERSION=system uv run python scripts/summarize_balfrin_management_demo_package.py \
  --format json \
  --json-output /tmp/tb678_management_package.json

PYENV_VERSION=system uv run python scripts/summarize_balfrin_scale_readiness_matrix.py \
  --format json \
  --json-output /tmp/tb678_scale_matrix.json

PYENV_VERSION=system uv run python scripts/estimate_swiss_wide_execution_envelope.py \
  --format json \
  --json-output /tmp/tb678_swiss_envelope.json
```

## Boundary

This readiness package is a decision surface. It does not authorize Swiss-wide
execution, distributed execution, physical probability, annual frequency,
operational use, return-period labels, risk/exposure/vulnerability products, or
non-`postproc` execution.
