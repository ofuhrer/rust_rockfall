# Validation Maturity Framework

Status: claim and evidence framework for reports, roadmaps, and pilot outputs.
This document does not change simulator behavior, validation results, hazard
semantics, or probability modes.

## Purpose

Validation maturity labels describe what kind of evidence supports a claim.
They are conservative report labels, not pass/fail statuses and not automatic
promotion gates. A result may satisfy several lower levels while still being
inadequate for a higher-level hazard-map claim.

Current repository outputs are mostly V0-V2 evidence, with early workflow
evidence for conditional hazard-layer generation. They are not operational
hazard maps, not risk maps, and not annual intensity-frequency products.

## Levels

| Level | Evidence type | Allowed claim | Current examples | Disallowed claim |
| --- | --- | --- | --- | --- |
| V0 analytic verification | Closed-form or procedural checks of implemented equations and file contracts. | "The implementation matches this analytic or schema fixture." | Free-fall, inclined-plane, deterministic seed/order, parser, manifest, and hazard-layer value-parity checks. | Field accuracy, physical occurrence probability, annual frequency, operational validation. |
| V1 synthetic fixture realism | Controlled synthetic terrain or scenario fixtures that exercise plausible workflow branches. | "The workflow behaves consistently on a controlled synthetic case." | Synthetic DEM, terrain-class, probabilistic metadata, GeoTIFF, QGIS-package, and DEM-sensitivity fixtures. | Real-site predictive skill, calibrated probability, return-period maps. |
| V2 impact-level field validation | Public field observations constrain trajectory, impact, energy, or deposition behavior at a limited scale. | "This component or metric is compared with public field observations under stated limits." | Chant Sura trajectory/contact subsets, Chant Sura scarring tables, Tschamut deposition/runout diagnostics, Mel de la Niva smoke benchmarks when prepared. | Complete hazard-map validation, annualized hazard frequency, operational readiness. |
| V3 site-scale hazard-pattern evidence | A predeclared real-site pilot compares conditional spatial hazard indicators with independent site-scale evidence and reports failure modes. | "This site-scale conditional hazard pattern is consistent or inconsistent with the selected evidence under stated assumptions." | Future public real-site conditional pilot after terrain/source/scenario choices are frozen before simulation. | Cross-site generalization, official hazard zoning, return-period products without source-frequency evidence. |
| V4 cross-site generalization | Multiple independent sites or held-out event families support the same workflow and parameter policy. | "The workflow generalizes across the tested evidence set within declared limits." | Future multi-site benchmark suite with held-out evidence and no hidden tuning. | National operational production or regulatory acceptance by itself. |
| V5 operational reproducibility | Independent operational review, documented data governance, reproducible production runs, monitoring, and acceptance criteria exist. | "Operationally reproducible for the reviewed use case." | None in the current repository. | Any current claim of validated operational hazard assessment or risk-map readiness. |

## Product Claim Rules

Use product semantics and maturity labels together:

- Current `unweighted_diagnostic` products are diagnostic count or event-density
  summaries. They can support V0-V1 workflow claims and limited V2 evidence
  when tied to a validation case.
- Current `sampling_weighted_conditional` products are conditional on the
  documented sampling design and filters. Sampling weights are not physical
  source probabilities and are not annual frequencies.
- Current threshold-exceedance products should be called conditional
  intensity-exceedance products when the denominator is a supplied trajectory
  set or sampling-weighted scenario set.
- Reserve intensity-frequency wording for future products with explicit
  physical probability or annual source-frequency semantics.
- Return-period labels require annual source-frequency contracts and are
  unsupported for current products.
- Risk-map language requires exposure, vulnerability, consequence, and
  occupancy contracts and is outside current scope.

## Current Evidence Summary

- V0: strong for analytic mechanics, deterministic execution contracts, schema
  fixtures, and hazard-layer value parity.
- V1: active for synthetic DEM, terrain-class, hazard-layer, map-package, and
  probabilistic metadata fixtures.
- V2: partial and limited for selected public field comparisons. These
  comparisons are useful for identifying model deficiencies and workflow
  failures; they are not complete field validation.
- V3: not yet reached. The real-case pilot roadmap targets conditional
  site-scale evidence first, without annual frequency.
- V4: not yet reached.
- V5: not reached and not claimed.

## Report Requirements

Pilot and validation reports should state:

- maturity level and evidence basis;
- whether products are unweighted diagnostic, sampling-weighted conditional,
  future physical-probability, or future annual-frequency products;
- denominator and conditioning assumptions;
- calibration and validation separation;
- unsupported claims, especially annual frequency, return period, risk, and
  operational hazard-map readiness.
