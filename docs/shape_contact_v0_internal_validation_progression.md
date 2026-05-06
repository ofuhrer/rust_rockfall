# `shape_contact_v0` Internal Validation Progression

This note records the first internal validation-style smoke case for
`shape_contact_v0`. It is verification plumbing only, not public validation,
benchmark evidence, calibration evidence, or operational evidence.

## Internal Case

- Case file: `validation/internal/shape_contact_v0_internal_smoke.yaml`
- Public discovery status: excluded from `cargo run -- validate --all` because
  the CLI discovers only `validation/cases/`.
- Public runner status: ordinary validation loading must still reject the case
  with the `shape_contact_v0` verification-scaffold error.
- Shape provenance: file-backed passive shape metadata path and SHA-256 are
  recorded by the internal smoke runner.
- Outputs: internal tests collect rows in memory or temporary JSON Lines
  sidecars only. No generated diagnostic sidecar is committed.

## Frozen Internal Gates

The internal case covers four synthetic regimes: touching incoming, separated
moving toward, penetrating moving away, and inclined terrain normal. The gate is
clean only if:

- every row maps to `shape_contact_runtime_diagnostic_v1`;
- sidecar manifests record schema version, row count, SHA-256, and the
  non-public-output warning;
- projection fields remain `null` / `false`;
- dissipative contacts do not create positive total/contact energy;
- file-backed shape metadata path and checksum are present;
- public validation and simulation remain blocked.

## Decision Boundary

A clean internal smoke result is permission only to review the next boundary. It
does not by itself justify public validation, benchmark execution, or continued
shape-contact development.

The next allowed step after a clean review is one controlled internal Chant Sura
model-selection run for `shape_contact_v0`, outside `validate --all`, compared
only against frozen trajectory/contact gates and without tuning. Tschamut and
Mel de la Niva remain diagnostic non-regression smoke evidence only.
