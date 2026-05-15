# Same-Scale Sampling Uncertainty Envelope

- Status: `sampling_uncertainty_measured`
- Artifacts included: gate, target, bounded probe v1, bounded probe v2
- Pairwise comparisons: `6`
- Case ids: `validation_tschamut_public_conditional_gate_v1, validation_tschamut_public_target_gate_v1, validation_tschamut_public_sampling_sensitivity_v1_full, validation_tschamut_public_sampling_sensitivity_v2_full`
- Seeds or splits: `34014, 34014, 34014, 34015`
- Ensemble sizes: `6, 100, 12, 12`
- Validation output modes: `full, full, full, full`
- Output file counts: `127, 2716, 247, 247`
- Output byte counts: `34560918, 764598283, 68221148, 68384888`
- Hazard file counts: `56, 56, 49, 56`
- Hazard byte counts: `77758043, 79160991, 21058710, 77883219`

## Dominant Layers
- `max_kinetic_energy`: l1 `92903.17436309032` to `190718.90391041967`, linf `1797.8665432400003` to `4484.5620665999995`, rmse `532.9774279976325` to `983.451160251898`, jaccard `1.0`
- `max_jump_height`: l1 `17.312950101751824` to `30.019475562139338`, linf `0.518719414238` to `1.42875571255`, rmse `0.13600226028761866` to `0.21594778911463908`, jaccard `0.7598039215686274` to `0.8579234972677595`
- `velocity_exceedance_5mps`: l1 `4.07156479883833` to `7.510928961744405`, linf `0.11543002452000001` to `0.21461748633899996`, rmse `0.001289806138060068` to `0.0022902866740530147`, jaccard `0.8028673835125448` to `0.9482758620689655`
- `weighted_velocity_exceedance_5mps`: l1 `3.744242424251889` to `6.863636363644098`, linf `0.10272727272700005` to `0.18939393939400007`, rmse `0.001188329775839792` to `0.0020913227021608824`, jaccard `0.8028673835125448` to `0.9482758620689655`
- `velocity_exceedance_10mps`: l1 `3.1839910089909624` to `5.620628415301155`, linf `0.10726773226800002` to `0.176652892562`, rmse `0.001105428916389202` to `0.0018334883288493604`, jaccard `0.7389162561576355` to `0.9053254437869822`

## Interpretation
- A second same-size seed confirms measured sampling sensitivity rather than accepted convergence.
- `max_kinetic_energy` remains the dominant disagreement layer across all six pairwise comparisons, but the 12-trajectory probe envelope is lower than the gate-target baseline.
- `max_jump_height` remains sensitive to support and nodata differences, with narrower but still nonzero spread across the two probes.
- Velocity exceedance layers vary across seeds but remain lower-order than kinetic-energy disagreement.
- The probe envelope is reusable for future same-scale diagnostics, but it is still conservative and non-operational.
- GIS/package readiness was audited separately in TB-033: the same-scale outputs
  are manifest-complete and GeoTIFF-present, but COG readiness remains blocked
  by the current strip layout and lack of overviews.

## Spatial Uncertainty Interpretation

Spatial same-scale uncertainty is now localized and measurable on the shared
grid, not just as scalar pairwise disagreement:

- `max_kinetic_energy`: concentrated but still nodata/support affected. The
  selected high-uncertainty cells cluster in a compact LV95 box near
  `x 2696638..2696668`, `y 1167684..1167714`. The layer remains the dominant
  disagreement field, but the concentration is not purely magnitude-only
  because nodata/support disagreement is still material.
- `max_jump_height`: dominated by support/nodata differences. The high-
  uncertainty cells cluster in a similarly compact box near
  `x 2696648..2696660`, `y 1167690..1167704`, with a lower magnitude spread
  than kinetic energy but stronger missing-cell sensitivity.
- `velocity_exceedance_5mps`: localized shared-support magnitude variation with
  a very small high-uncertainty fraction relative to the 91,200-cell grid.

The spatial diagnostic therefore answers "where does uncertainty concentrate?"
with a conservative answer: the dominant disagreement is concentrated in a
small same-scale corridor, while `max_jump_height` remains the layer most
affected by nodata/support differences. This does not change the existing
`inconclusive` convergence interpretation.

## Remaining Uncertainty
- seed sensitivity remains structurally limiting on the shared grid
- `max_kinetic_energy` still dominates the envelope
- `max_jump_height` still carries support/nodata variation
- velocity exceedance layers still vary across seeds, but stay below the kinetic-energy spread
- the gate-target interpretation remains conservative and non-operational
