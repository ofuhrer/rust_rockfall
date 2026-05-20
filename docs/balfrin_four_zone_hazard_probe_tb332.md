# TB-332 Four-Zone Balfrin Hazard Probe Fail-Closed Report

Date: 2026-05-20

TB-332 stopped before `sbatch`. No four-zone hazard job was submitted and no
Balfrin hazard run root was created for this task.

## Gate Result

- Access preflight: `ready_for_read_only_collection`
- Remote checkout hygiene: `pass`
- Remote checkout HEAD: `20cc865756f1f5afb5c5e19b2a042e94553afd3a`
- Four-zone package review readiness: `ready_for_review`
- Output-budget status: `accepted`
- Submit-contract status: `ready`
- Reducer-budget status: `ready`
- Output-profile status: `ready`
- Authorization preflight: `blocked_missing_authorization`
- Authorization status: `blocked_missing_inputs`
- Exact blocker: `authorization record reviewed-handoff checksum does not match`

The freshly generated reviewed handoff package checksum was
`5b36191cf79d0f234ef862391b23be85a364a72dc784889fa231c91e21dc950d`, while the
reviewed authorization record still referenced
`8e0a01fd787f941775c51ef7ade12cf18ab370796f6b518be0fd1dd9b5d6e808`.

## Commands Run

```bash
PYENV_VERSION=system uv run python scripts/check_balfrin_remote_access_preflight.py --format json
PYENV_VERSION=system uv run python scripts/generate_balfrin_multi_release_zone_demo_handoff.py --format json
PYENV_VERSION=system uv run python scripts/preflight_balfrin_smallest_multi_zone_probe_authorization.py \
  --reviewed-handoff-package /private/tmp/rust_rockfall/balfrin_multi_release_zone_demo_v1/balfrin_multi_release_zone_demo_package_v1.json \
  --authorization-record /private/tmp/rust_rockfall/balfrin_multi_release_zone_demo_v1/balfrin_multi_zone_live_authorization_record_v1.yaml \
  --balfrin-access-preflight-json /tmp/tb332_balfrin_access_preflight.json \
  --format json
```

Generated JSON reports were kept under `/tmp` and `/private/tmp`; they are not
committed evidence artifacts.

## Boundary Note

This is a precise blocked pre-submit branch, not measured Balfrin hazard
execution. It does not upgrade the existing four-zone postproc-only evidence
from TB-312, does not authorize scale-up or distributed execution, and does not
make operational, annual-frequency, physical-probability, risk, exposure, or
vulnerability claims.
