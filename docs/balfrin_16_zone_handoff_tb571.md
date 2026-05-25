# TB-571 Optimized 16-Zone No-Submit Handoff

Date: 2026-05-25

## Scope

TB-571 rebuilt the 16-zone reduced-output handoff after the reducer-manifest pressure reduction in TB-570. This was a pre-submit review only. No `sbatch` command was run and no Balfrin job was submitted.

## Commands

Balfrin read-only preflight after synchronizing the remote checkout:

```bash
PYENV_VERSION=system uv run python scripts/check_balfrin_remote_access_preflight.py --format json > /tmp/tb571_balfrin_preflight_after_sync.json
```

Optimized 16-zone package generation:

```bash
PYENV_VERSION=system uv run python scripts/generate_balfrin_multi_release_zone_demo_handoff.py \
  --artifact-dir /tmp/rust_rockfall/tb571_16_zone_handoff \
  --pressure-probe-root /tmp/rust_rockfall/tb571_16_zone_pressure \
  --requested-release-zone-batch-size 16 \
  --requested-reducer-chunk-count 2 \
  --requested-reducer-worker-count 2 \
  --format json \
  --json-output /tmp/rust_rockfall/tb571_16_zone_handoff/package.json \
  --text-output /tmp/rust_rockfall/tb571_16_zone_handoff/package.txt
```

Authorization and submit-contract preflight:

```bash
PYENV_VERSION=system uv run python scripts/preflight_balfrin_smallest_multi_zone_probe_authorization.py \
  --reviewed-handoff-package /tmp/rust_rockfall/tb571_16_zone_handoff/balfrin_multi_release_zone_demo_package_v1.json \
  --authorization-record /tmp/rust_rockfall/tb571_16_zone_handoff/balfrin_multi_zone_live_authorization_record_v1.yaml \
  --balfrin-access-preflight-json /tmp/tb571_balfrin_preflight_after_sync.json \
  --format json \
  --json-output /tmp/rust_rockfall/tb571_16_zone_handoff/authorization_preflight_after_sync.json \
  --text-output /tmp/rust_rockfall/tb571_16_zone_handoff/authorization_preflight_after_sync.txt
```

## Result

- Remote checkout: clean `main` at `92a6550f9f986a46f4f231bd1e0e56d63463b77c`.
- Package status: `mixed_provenance`.
- Package constraint status: `blocked`.
- Authorization status: `authorized`.
- Submit-contract status: `ready`.
- Submission gate status: `blocked_reducer_budget`.
- Reviewed package SHA-256: `65efa1812312032d22830c9ffbd9031efafef1411b4540c6001a412cd21d520c`.
- Authorization record SHA-256: `d251de4e2f46455c32404f05b01bc86f47a2d4fe932ddfe20786aa3046537dce`.

## Remaining Blocker

The optimized compact projection removed reducer chunk manifest pressure:

- `reducer_manifest_file_count`: `0`
- `reducer_manifest_bytes`: `0`
- `sidecar_file_count`: `2`

The package still fails closed. The first handoff output-budget blocker is now `manifest_size_bytes`; the scenario-pressure gate still first blocks on `release_zone_count` because `16` exceeds the measured simultaneous release-zone batch maximum of `8`.

Recovery command recorded by the package:

```bash
PYENV_VERSION=system uv run python scripts/generate_balfrin_multi_release_zone_demo_handoff.py --artifact-dir /private/tmp/rust_rockfall/tb571_16_zone_handoff --requested-release-zone-batch-size 2 --requested-reducer-chunk-count 2 --requested-reducer-worker-count 2 --format json
```

## Boundary

This evidence does not authorize a live 16-zone run. It preserves a fail-closed pre-submit result and the exact later submit command shape only. It makes no distributed-execution, operational, annual-frequency, risk, or physical-probability claim.
