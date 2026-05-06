# `shape_contact_v0` Chant Sura Internal Model-Selection Run

Status: internal-only model-selection smoke result. This is not public
validation, not benchmark evidence, not calibration, and not an operational
claim.

## Scope

The run uses the checked-in `validation/cases/chant_sura_contact.yaml` RF16W200r1
model-selection subset and the frozen `shape_contact_v0` diagnostic contract.
It stays outside `validate --all`; the internal fixture is
`validation/internal/shape_contact_v0_chant_sura_model_selection.yaml`.

No friction, restitution, terrain, release, threshold, or filtering parameter
was changed. Tschamut and Mel de la Niva were not run.

## Command

```bash
cargo test shape_contact_v0
```

The model-selection check is the Rust-only test
`shape_contact_v0_internal_chant_sura_model_selection_reports_frozen_gate_result`.
It writes no committed outputs. Shape metadata is generated as a temporary
file-backed `shape_metadata_v1` sidecar during the test so the internal manifest
has a real path and SHA-256 while the run is active.

The internal metric calculation mirrors the existing public Chant Sura
validator semantics for the compared quantities: simulated jump-height envelope
uses each trajectory's last observed sample time as the horizon, and contact
proxy comparison uses the first significant impact according to the existing
`0.05 m/s` incoming-normal-speed threshold before falling back to the first
impact.

## Shape Provenance

The active sidecar is derived from the checked-in
`validation/data/processed/chant_sura_2020/rock_shapes.csv` EOTA221 row:

- `shape_file`: `EOTA/1m3_EOTA_221_plate.pts`
- dimensions: preserve EOTA221 aspect ratio
- scaling: scale from 1.0 m3 reference geometry to the active W200 volume using
  the existing `2670 kg/m3` density assumption
- mass: `210 kg`, matching the RF16W200r1 model-selection case
- orientation: identity

Important limitation: the current repository does not yet contain an auditable
trajectory-to-EOTA shape mapping for this fixture. The EOTA221 assignment is
therefore proxy-only and cannot by itself support a clean physics-selection
claim.

## Metrics

| Metric | `shape_contact_v0` internal run | Frozen `translational_v0` reference | Frozen `sphere_rotational_v1` reference | Gate result |
| --- | ---: | ---: | ---: | --- |
| `trajectory_shape_mean_error_m` | 0.019654 | 0.418 | 0.378 | pass |
| `trajectory_energy_mean_relative_error` | 0.033823 | 0.394 | 0.289 | pass |
| `trajectory_jump_height_envelope_error_m` | 0.001283 | 0.731 | 0.750 | pass |
| `impact_timing_mean_error_s` | 0.142500 | 0.628 | 0.628 | pass |
| `rebound_velocity_mean_error_mps` | 7.187644 | 4.899 | 4.902 | fail |

Diagnostics/provenance:

- observed trajectories compared: 3
- observed contact proxies compared: 2 of 2
- diagnostic rows: 690
- impulsive rows: 78
- non-impulsive penetrating rows: 322
- maximum positive contact-energy delta: `0.0 J`
- diagnostic sidecar SHA-256:
  `c379cac33b2afec2f3e692168a35e68ede5595a08b093f9501fbce33d1ae2c0c`
- temporary shape metadata SHA-256:
  `48e7d14044abde85c169fe9d9fab4e9962549f2e9cd9d87218df1a3bcd8b2596`

## Frozen-Gate Decision

Result: `failed_uncertain`.

Reasons:

- `rebound_velocity_mean_error_mps` exceeds the frozen 10% degradation limit
  relative to the better current model.
- trajectory-to-EOTA shape mapping remains unresolved, so the shape assignment
  is proxy-only.

The strong trajectory-shape, energy, jump-height, and timing numbers are useful
debug signals, but they must not be overinterpreted because the runtime scaffold
still lacks projection correction, persistent contact, orientation evolution,
multi-contact, and a validated trajectory-to-shape join.

## Follow-Up Rebound Audit

The follow-up diagnostic audit is recorded in
`docs/shape_contact_v0_rebound_diagnostic_audit.md`. It keeps the same
no-tuning result and identifies two blockers:

- the selected first significant simulated contact for `RF16W200r1_impact_00`
  occurs at `0.005 s`, while the observed segment-boundary proxy is at
  `0.250 s`;
- both compared contact proxies have simulated rebound speeds substantially
  above the observed proxy speeds, while contact energy remains dissipative.

The audit does not identify a safe parameter-free fix inside the current
contract. It therefore keeps the decision at `failed_uncertain`.

## Recommendation

Do not run held-out Chant Sura yet. Pause `shape_contact_v0` runtime
progression until rebound behavior and trajectory-to-EOTA shape provenance can
be resolved without tuned parameters or changes to the frozen evaluation
contract. If they cannot be resolved, pivot to terrain/material interaction or
stopping-behavior diagnostics rather than adding more shape-contact machinery.
