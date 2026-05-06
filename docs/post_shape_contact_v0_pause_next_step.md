# Post-`shape_contact_v0` Pause Next-Step Decision

Status: scientific sequencing decision. This document does not change physics,
defaults, validation cases, thresholds, baselines, public benchmark status, or
operational claims.

## Decision

Pause `shape_contact_v0` runtime progression and make the next no-tuning work
package a stopping-behavior diagnostic protocol.

The immediate goal is to explain how the current models lose motion and stop
before adding new terrain/material parameters or broader contact machinery.
This is a diagnostics package, not a calibration package.

## Why `shape_contact_v0` Is Paused

`shape_contact_v0` passed internal plumbing gates: public execution remains
blocked, runtime diagnostic rows serialize to the frozen contract, diagnostic
sidecars/manifests are available, and the internal Chant Sura model-selection
run did not create positive contact energy.

It is paused because the first internal Chant Sura model-selection result is
`failed_uncertain`:

- rebound-velocity error fails the frozen non-regression gate;
- the selected first significant simulated contact for
  `RF16W200r1_impact_00` occurs at `0.005 s`, while the observed
  segment-boundary proxy is at `0.250 s`;
- both compared contact proxies have simulated rebound speeds above the
  observed proxy speeds;
- the active EOTA221 shape assignment is proxy-only because the repository has
  no auditable trajectory-to-EOTA shape mapping for `RF16W200r1`;
- projection correction, persistent contact, orientation evolution, and
  multi-contact remain absent.

Held-out Chant Sura therefore remains blocked. Tschamut and Mel de la Niva
remain diagnostic/non-regression evidence only, not physics-selection evidence.

## Candidate Directions

| Direction | Value | Risk | Decision |
| --- | --- | --- | --- |
| Shape provenance only | Could remove the EOTA221 proxy blocker if public records map trajectories to shapes and orientations. | May require unavailable source material; does not address the rebound failure by itself. | Keep as a parallel research task, not the main implementation package. |
| Rebound/contact-proxy audit only | Directly addresses the failed Chant Sura gate and proxy alignment uncertainty. | A first audit already found no safe no-tuning fix; deeper work may remain dataset-forensic rather than model-informative. | Continue only if new raw provenance is found; otherwise do not spend the next package here. |
| Terrain/material interaction protocol | Addresses a known gap and separates material assumptions from global restitution/friction. | Easy to become hidden calibration if introduced before stopping modes are characterized. | Defer until stopping diagnostics identify where material assumptions matter. |
| Stopping-behavior diagnostics | Explains under-run, over-run, early stopping, deposition concentration, and transition-to-rest behavior without changing model numerics. | Diagnostic-only; may not immediately improve metrics. | Recommended next package. |
| Broader contact-model redesign | Could address shape, persistent contact, projection, and multi-contact coherently. | Too large and not justified after a failed/uncertain first shape slice. | Reject for now. |

## Recommended Work Package

Create a no-tuning stopping-behavior diagnostic package for existing models and
existing benchmark outputs.

The package should characterize, without changing simulation behavior:

- final state and stopping reason;
- last significant impact time and location;
- last contact regime / impact count where available;
- sliding, rolling, ballistic, and stopped fractions through time when available;
- kinetic-energy decay to stop;
- distance from last significant impact to final stop;
- terrain slope/normal near final stop where terrain is available;
- whether a run stops by low velocity, repeated small impacts, domain exit,
  max-step termination, or other existing status;
- grouped behavior by dataset, contact model, runout class, block/mass class,
  and transform where those groupings already exist.

Initial evidence should come from checked-in or reproducibly generated existing
workflows only:

- analytic/synthetic verification cases for expected stop mechanics;
- Chant Sura model-selection/contact fixtures for contact-rich short segments;
- public Tschamut as diagnostic failure-mode evidence only;
- Mel de la Niva as runnable smoke/generalization evidence only where local
  public archives are available;
- hazard-layer deposition/reach summaries as downstream diagnostics, not
  calibration targets.

## Non-Tuning Constraints

The package must not:

- change physics, defaults, contact models, terrain handling, thresholds,
  release assumptions, validation cases, or baselines;
- run held-out Chant Sura for `shape_contact_v0`;
- use Tschamut or Mel de la Niva as physics-selection evidence;
- add terrain/material parameters;
- tune restitution, friction, roughness, scarring, stopping velocity, or
  terrain classes;
- filter runs after seeing outcomes;
- claim operational validity.

Allowed changes:

- additive scripts, reports, manifest fields, and tests that summarize existing
  outputs;
- small synthetic fixtures if needed to verify the diagnostic calculations;
- documentation that separates diagnostics, validation, calibration, and hazard
  mapping.

## Success Criteria

The package succeeds if it produces a reproducible report that:

- identifies which current failures are dominated by early stopping, late
  stopping, repeated low-energy contact, or ballistic/rebound mismatch;
- distinguishes stopping/deposition behavior from trajectory-shape and rebound
  metrics;
- shows whether existing Tschamut under-run and rotational over-run are tied to
  final-stop mechanics or earlier trajectory divergence;
- explains whether terrain/material work is likely to be more informative than
  further shape-contact work;
- preserves all existing numerical baselines and public validation semantics.

## Failure Criteria

Stop or redesign the package if:

- the diagnostics require changing simulation outputs or thresholds;
- existing outputs do not contain enough state to infer stopping behavior and a
  broader instrumentation plan is needed first;
- the work starts selecting or excluding runs based on outcomes;
- the report cannot keep Tschamut and Mel framed as diagnostic rather than
  physics-selection evidence.

## `shape_contact_v0` Status

Keep `shape_contact_v0` as a paused experimental branch in the repository:

- internal scaffolding and diagnostic contracts remain useful;
- public validation and benchmarks remain blocked;
- held-out Chant Sura remains blocked;
- no additional runtime wiring should proceed until either shape provenance and
  rebound alignment are resolved without tuning, or a new reviewed contract is
  written.

## Next Prompt

```text
NEXT TASK — STOPPING-BEHAVIOR DIAGNOSTIC PACKAGE

Do NOT change physics.
Do NOT tune parameters.
Do NOT change defaults, validation cases, thresholds, release assumptions, or baselines.
Do NOT run held-out Chant Sura for shape_contact_v0.
Do NOT use Tschamut or Mel de la Niva as physics-selection evidence.
Do NOT enable public benchmarks.

Goal:
Create a no-tuning stopping-behavior diagnostic package that explains how current
models lose motion and stop across existing verification, Chant Sura, Tschamut
diagnostic, Mel smoke, and hazard-layer workflows where data are already
available.

Tasks:
1. Inspect existing trajectory, impact, manifest, and hazard outputs for fields
   that can support stopping diagnostics.
2. Define a stopping diagnostic schema:
   - final status;
   - stop reason;
   - final speed;
   - final kinetic energy;
   - last significant impact time/location;
   - distance from last significant impact to final stop;
   - impact count;
   - low-energy contact count where available;
   - terrain slope/normal near stop where terrain is available;
   - runout/deposition grouping keys.
3. Implement additive summarization only, using ignored/temp outputs when needed.
4. Produce docs/stopping_behavior_diagnostic_report.md.
5. Conclude whether the next scientific package should be:
   - terrain/material interaction protocol;
   - rebound/contact-proxy provenance work;
   - stopping instrumentation;
   - or continued pause.

Run focused tests and documentation/consistency checks only. No public benchmark
reruns unless explicitly needed for existing diagnostic summaries.
```
