# Balfrin Post-Run Interpretation Gate

This document defines the read-only post-run gate used for the Balfrin
single-release-zone pilot track.

The gate is implemented by
`scripts/summarize_balfrin_post_run_interpretation_gate.py`. It accepts a
conditional diagnostic evidence bundle, classifies the post-run state as
`measured`, `inconclusive`, or `blocked_missing_inputs`, and prints JSON or
text without rerunning the model.

## What the gate checks

- Required readiness
- Convergence and stability
- Output pressure
- GIS and COG readiness
- Physical-credibility boundary

The gate can accept the pilot as a conditional diagnostic artifact when the
required evidence is present and the post-run state is `measured`. That
acceptance is strictly diagnostic. It does not authorize operational use,
physical-probability claims, annual-frequency claims, or risk/exposure/
vulnerability claims.

## Boundary

The gate keeps the physical-credibility check explicit, but it does not turn
that check into a probability claim. The accepted artifact remains a
conditional diagnostic artifact only.

## Typical usage

```bash
PYENV_VERSION=system uv run python scripts/summarize_balfrin_post_run_interpretation_gate.py \
  --format json \
  --evidence-json /tmp/balfrin_post_run_evidence.json
```

The evidence bundle should contain the ready/inconclusive/blocked statuses for
the required checks. When required inputs are missing, the helper returns a
blocked post-run gate instead of guessing.

For a management-facing review bundle that feeds this gate, use
`scripts/summarize_balfrin_evidence_bundle.py` with
`--artifact-dir validation/private/tschamut_public_pilot/balfrin_evidence_bundle_v1`.
