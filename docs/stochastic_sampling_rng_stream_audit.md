# Stochastic Sampling And RNG Stream Audit

Status: DT-06 audit package for current stochastic semantics. This document
records the current stochastic contracts, known gaps, and future test gates.
It does not change physics, change RNG behavior, or tune stochastic
parameters; the current stochastic implementation is not statistically validated.

## Scope And Boundary

This audit is documentation and validation work only.

This is the no-behavior-change boundary for the audit.

- no physics changes;
- no RNG changes;
- no stochastic default changes;
- no tuning of release, roughness, or weighting parameters;
- no reinterpretation of current conditional layers as annual, physical,
  risk, exposure, or operational products.

The current conditional products remain conditional diagnostic products. This
audit does not convert them into accepted stochastic-validity evidence.

## Current RNG And Seed Derivation

The current trajectory seed path is deterministic and narrow:

- `TrajectoryRequest::from_global_seed()` derives a seed from
  `global_seed + case_id + trajectory_id`;
- `derive_trajectory_seed()` uses a stable FNV-1a style hash over the global
  seed, `case_id`, and `trajectory_id`;
- `sample_release()` initializes a local `ChaCha8Rng` from that derived seed
  and samples axis-aligned perturbations;
- `simulate_ensemble_parallel()` preserves deterministic order and chunk
  metadata, but it does not change seed derivation;
- contact roughness uses an optional local seed from
  `IntegratorSettings.roughness_seed.unwrap_or(0)` when roughness is active.

Current stream-separation limitations:

- the derived trajectory seed does not explicitly namespace worker id;
- the derived trajectory seed does not explicitly namespace retry or chunk
  execution;
- the derived trajectory seed does not explicitly namespace stochastic
  variable family;
- the derived trajectory seed does not explicitly namespace draw index;
- roughness draws have their own optional local seed, but there is no explicit
  per-family or per-draw substream contract.

## Current Stochastic Variable Families

The current code base has the following stochastic families or stochastic-like
contracts:

| Family | Current status | Notes |
| --- | --- | --- |
| trajectory seed | implemented | Deterministic seed derived from global seed, case id, and trajectory id. |
| release perturbation | implemented | Axis-aligned uniform perturbations in position and velocity. |
| roughness/contact | implemented with limits | Stochastic contact roughness perturbs normals, restitution, and friction. |
| scenario sampling weight | implemented for conditional weighting only | Sampling weights are conditioning weights, not physical probability. |
| block mass/shape/restitution draws | not sampled | The current pilot path does not define sampled mass, shape, or restitution distributions. |

## Release Perturbation Semantics

`ReleasePerturbation` currently exposes two nonnegative half-widths:

- `position_uniform_m`;
- `velocity_uniform_mps`.

Current semantics:

- each Cartesian component is sampled independently;
- the same half-width is used on x, y, and z;
- sampling is uniform within `[-half_width, +half_width]`;
- a zero half-width yields no perturbation;
- the perturbation is additive on top of the initial state.

Known limitations:

- there is no configurable non-uniform release distribution;
- there is no support model for release-cell area, release-cell density, or
  per-axis asymmetry;
- there is no explicit worker/chunk/retry/draw-index substream contract for
  release perturbation.

## Roughness And Contact Semantics

`stochastic_contact_v1` is currently the only stochastic contact roughness
model. It is opt-in and only active when the roughness model is enabled and at
least one roughness standard deviation is positive.

Current semantics:

- the roughness RNG is seeded locally and only used when roughness is active;
- normal and tangential restitution are perturbed by bounded Gaussian-style
  draws;
- normal direction is perturbed by two bounded Gaussian-style angle draws;
- friction is scaled by the absolute tangent draw and clamped to remain
  nonnegative;
- bounded Gaussian draws are clipped to `±2σ`;
- dissipative scaling clamps the resulting restitution to `[0, 1]`.

Known limitations:

- the contact roughness distribution is bounded and clipped, not a general
  support contract;
- the roughness semantics do not define explicit tail handling or
  reweighting;
- the roughness semantics do not define independent family substreams for
  worker, chunk, retry, or draw index;
- mass, block shape, and baseline contact restitution are not sampled as
  stochastic families in the current pilot path.

## Scenario And Block Sampling Semantics

The current probabilistic scenario design uses `sampling_weighted_conditional`
layers and `sampling_weight` metadata only for conditional weighting.

Current semantics:

- `sampling_weight` is a conditioning weight over a documented filter set;
- weighted layers are normalized over the active filtered scenario table;
- trajectory-level, deposition, and significant-impact weighted layers are
  documented as conditional outputs;
- the current scenario path does not interpret `sampling_weight` as physical
  probability, annual frequency, or risk.

Known limitations:

- the weighting contract is conditional, not a physical source-frequency
  model;
- scenario and block weights do not define annual or operational semantics;
- a zero-weight filter set remains invalid for current weighted products;
- uncertainty semantics for weighted estimators are still documentation-level
  rather than an accepted stochastic-validity contract.

## Distribution, Truncation, And Support Limitations

Current distribution/support limitations are explicit:

- release perturbation uses a uniform box, not a general distribution family;
- roughness uses clipped Gaussian-style draws with hard bounds at `±2σ`;
- roughness and contact scaling clamp effective restitution and friction
  rather than preserving tail behavior;
- there is no sampled support contract for mass, shape, or per-impact
  restitution families in the selected pilot path;
- there is no explicit tail-support or truncation-policy audit for future
  draw families.

## Weighted Uncertainty Limitations

Weighted uncertainty in the current repository is a scenario-conditioning
tool, not an accepted stochastic validity result.

Current limitations:

- `sampling_weighted_conditional` is a weighted conditional hazard product,
  not a physical probability;
- the weighted estimator remains tied to the documented scenario filter and
  metadata table;
- sampling weights do not encode annual occurrence, source frequency, or risk;
- the current Tschamut evidence does not elevate weighted uncertainty into an
  operational or validated claim.

## Impact On The Tschamut Pilot

The selected Tschamut pilot evidence should be interpreted as follows:

- the DT-04/DT-05 conditional convergence evidence remains `inconclusive`;
- this audit documents current stochastic semantics but does not validate the
  stochastic model as statistically accepted;
- the current Tschamut evidence cannot be treated as accepted stochastic
  validity evidence;
- annual, physical, risk, exposure, and operational claims remain out of
  scope.

## Required Future Implementation And Test Gates

Future implementation and test gates should cover:

- explicit stream-separation contracts for worker, chunk, retry, family, and
  draw-index labels;
- seed collision and independence tests for derived trajectory streams;
- substream collision tests for roughness and any future stochastic family
  that is added;
- release distribution and truncation contracts, including support and tail
  handling;
- weighted estimator contracts for conditional uncertainty products;
- claim-hygiene checks that reject annual, physical, risk, exposure, and
  operational reinterpretations;
- regression tests that fail if RNG derivation, stochastic defaults, or
  physics behavior are silently changed.

## No-Behavior-Change Boundary

This audit is a protocol and documentation target only.

- it does not change physics;
- it does not change RNG behavior;
- it does not change stochastic defaults;
- it does not tune distributions or thresholds;
- it does not authorize larger pilot runs;
- it does not turn current conditional layers into accepted stochastic-validity
  evidence.
