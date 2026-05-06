# `shape_contact_v0` Chant Sura Provenance And Rebound Audit

Status: internal diagnostic audit only. This is not public validation, not a
benchmark result, not calibration evidence, and not an operational claim.

## Scope

This audit reviews the internal `shape_contact_v0` Chant Sura model-selection
result recorded in
`docs/shape_contact_v0_chant_sura_internal_model_selection.md`.

No physics, defaults, thresholds, terrain, release assumptions, filtering, or
shape assignment were changed. Held-out Chant Sura, Tschamut, Mel de la Niva,
public validation, and public benchmarks were not run.

## Provenance Audit

The internal model-selection fixture uses:

- source validation case: `validation/cases/chant_sura_contact.yaml`;
- source trajectory: `RF16W200r1`, split into three local-time-reset segments;
- active proxy shape row:
  `validation/data/processed/chant_sura_2020/rock_shapes.csv` /
  `EOTA/1m3_EOTA_221_plate.pts`;
- scaling policy:
  `preserve_eota221_aspect_ratio_scale_to_active_block_volume_using_case_density`;
- density assumption: `2670 kg/m3`;
- active mass: `210 kg`;
- active proxy dimensions: approximately
  `0.605674 x 0.605674 x 0.302837 m`;
- orientation initialization: identity.

The repository still does not contain an auditable mapping from
`RF16W200r1` to a specific EOTA shape file or measured initial orientation. The
checked-in processed data identify the W200 trajectory and the available EOTA111
/ EOTA221 shape summaries, but they do not prove that this trajectory used the
EOTA221 plate geometry. This remains a scientific blocker: the current active
shape assignment is proxy-only and cannot support a clean shape-contact
physics-selection claim.

## Rebound Diagnostic Summary

The internal runner compares the same two segment-boundary contact proxies as
the public Chant Sura contact fixture. It uses the same first-significant-impact
semantics as the public validator: the first simulated impact with incoming
normal speed at least `0.05 m/s`, falling back to the first impact only if none
meets that threshold.

The aggregate model-selection metrics remain:

| Metric | `shape_contact_v0` internal run | Frozen gate result |
| --- | ---: | --- |
| `trajectory_shape_mean_error_m` | 0.019654 | pass |
| `trajectory_energy_mean_relative_error` | 0.033823 | pass |
| `trajectory_jump_height_envelope_error_m` | 0.001283 | pass |
| `impact_timing_mean_error_s` | 0.142500 | pass |
| `rebound_velocity_mean_error_mps` | 7.187644 | fail |

The selected contact rows explain why the rebound gate fails:

| Observed proxy | Observed impact time (s) | Selected simulated impact time (s) | Timing error (s) | Observed rebound speed (m/s) | Simulated rebound speed (m/s) | Rebound velocity error (m/s) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `RF16W200r1_impact_00` | 0.250 | 0.005 | 0.245 | 3.012 | 6.099 | 5.977 |
| `RF16W200r1_impact_01` | 1.100 | 1.060 | 0.040 | 4.270 | 8.151 | 8.398 |

Detailed contact diagnostics:

| Observed proxy | Incoming normal speed (m/s) | Normal velocity pre/post (m/s) | Tangential speed pre/post (m/s) | Normal impulse (N s) | Tangential impulse (N s) | Coulomb cap ratio | Support corner signs | Support gap (m) | Contact energy delta (J) | Rot/translation energy ratio pre/post |
| --- | ---: | --- | --- | ---: | ---: | ---: | --- | ---: | ---: | --- |
| `RF16W200r1_impact_00` | 0.465 | -0.465 / 0.303 | 6.190 / 5.268 | 44.704 | 20.117 | 1.000 | `[-1, 1, -1]` | -0.152551 | -118.776 | 0.000 / 0.005 |
| `RF16W200r1_impact_01` | 5.003 | -5.003 / 1.130 | 7.978 / 6.015 | 563.071 | 49.025 | 0.193 | `[1, 1, -1]` | -0.034286 | -1377.119 | 0.000 / 0.137 |

Both selected rows are dissipative (`contact_energy_delta_j <= 0`) and use the
frozen existing restitution/friction parameters. The failure is therefore not
explained by positive contact-energy creation. The first observed proxy is
instead matched to a very early simulated contact at `0.005 s`, and both
selected simulated contacts leave the contact with substantially larger
rebound-speed error than the existing frozen models.

## Interpretation

The audit does not identify a safe no-tuning fix inside the current
`shape_contact_v0` contract. The failure is consistent with the known
pre-runtime limitations:

- single support point only;
- identity orientation only;
- no projection correction;
- no persistent-contact handling;
- no orientation evolution;
- no multi-contact;
- unresolved trajectory-to-EOTA shape mapping.

The early first selected contact is especially important. It suggests that the
active box support geometry can create a contact sequence that is not aligned
with the segment-boundary rebound proxy, even though the aggregate trajectory
shape and jump-height metrics are strong. Changing thresholds, choosing another
orientation, switching shape class, or filtering early contacts after seeing the
result would be tuning leakage and is out of scope.

## Decision

Current decision: pause `shape_contact_v0` runtime progression.

Held-out Chant Sura remains blocked. The model-selection result is still
`failed_uncertain`, with two independent blockers:

- rebound velocity fails the frozen non-regression gate;
- the trajectory-to-EOTA shape mapping is not auditable.

The only shape-contact work still justified without changing the contract is
diagnostic/provenance work:

- locate public evidence that maps `RF16W200r1` to a specific EOTA shape and
  initial orientation, or formally conclude that the mapping is unavailable;
- compare the early simulated contact sequence against raw segment/proxy
  construction to determine whether the rebound failure is a metric-alignment
  issue or a genuine scaffold behavior failure.

If those cannot be resolved without tuning or contract changes, the next
scientific slice should pivot to terrain/material interaction or
stopping-behavior diagnostics rather than adding more shape-contact machinery.
