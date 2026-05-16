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

Measured support/nodata decomposition for the closure-limiting layers:

- `max_kinetic_energy`: the layer-level concentration class remains
  `dominated_by_nodata_support_differences`, but the selected high-uncertainty
  cells are `shared_support_magnitude_dominated` with support/nodata fraction
  `0.0` and shared-support magnitude fraction `1.0`. The broader layer still
  carries `66` nodata/support disagreements across `229` valid-any cells, so
  it remains closure-limiting.
- `max_jump_height`: the layer-level concentration class remains
  `dominated_by_nodata_support_differences`, but the decomposition is
  `mixed_support_and_magnitude` with support/nodata fraction `0.25` and
  shared-support magnitude fraction `0.75`. The layer still carries `66`
  nodata/support disagreements and remains closure-limiting.
- `velocity_exceedance_5mps`: the layer-level concentration class remains
  `spatially_localized_shared_support_magnitude`, and the selected
  high-uncertainty cells are entirely shared-support magnitude variation
  (`support/nodata=0.0`, `shared-support magnitude=1.0`). Across the full
  grid, the decomposition is still measured as mixed, but the layer remains
  deferrable rather than closure-limiting.

The spatial diagnostic therefore answers "where does uncertainty concentrate?"
with a conservative answer: the dominant disagreement is concentrated in a
small same-scale corridor, while `max_jump_height` remains the layer most
affected by nodata/support differences. This does not change the existing
`inconclusive` convergence interpretation.

## Persistent Spatial Disagreement Stability Zones

The same measured masks can also be summarized as stability zones, which keeps
the closure-limiting layers visible without changing the science status:

- `max_kinetic_energy`: `persistent_closure_limiting`; dominant zone category
  `shared_support_magnitude`; high-uncertainty zone category
  `shared_support_magnitude`; zone counts over the evaluated cells are
  `support_nodata_sensitive=66` (`0.2237288136`), `shared_support_magnitude=228`
  (`0.7728813559`), and `persistent_agreement=1`
  (`0.0033898305`); closure-role impact is `no_change`.
- `max_jump_height`: `persistent_closure_limiting`; dominant zone category
  `shared_support_magnitude`; high-uncertainty zone category
  `shared_support_magnitude`; zone counts over the evaluated cells are
  `support_nodata_sensitive=122` (`0.4135593220`),
  `shared_support_magnitude=136` (`0.4610169492`), and
  `persistent_agreement=2` (`0.0067796610`); closure-role impact is
  `no_change`.
- `velocity_exceedance_5mps`: `deferrable_localized`; dominant zone category
  `support_nodata_sensitive`; high-uncertainty zone category
  `shared_support_magnitude`; zone counts over the evaluated cells are
  `support_nodata_sensitive=66` (`0.0007236842`),
  `shared_support_magnitude=213` (`0.0023355263`), and
  `persistent_agreement=0`; closure-role impact is `no_change`.

The new stability-zone summary is therefore a compact interpretation aid, not a
new acceptance criterion. It makes the persistent closure-limiting regions and
the localized deferrable disagreement explicit, but it does not change the
current `inconclusive` closure status.

## Hotspot Persistence Across Gate/Target/Probes

The selected hotspot cells can also be checked for pairwise persistence across
the four committed artifacts, which gives a direct stability view over the
existing gate, target, sampling probe v1, and sampling probe v2 layers. This is
measured from the six pairwise comparisons among those artifacts and does not
introduce a new simulation run.

- `max_kinetic_energy`: `mixed_persistence`; the selected hotspot cells recur
  in `2..4` of the `6` pairwise comparisons, with pairwise-support histogram
  `2=2, 3=3, 4=3`. The hotspot core is present, but some edge cells are still
  transient across seeds/probes.
- `max_jump_height`: `mostly_persistent`; the selected hotspot cells recur in
  `3..5` of the `6` pairwise comparisons, with pairwise-support histogram
  `3=1, 4=3, 5=4`. This is the clearest mostly-stable hotspot pattern in the
  current spatial envelope.
- `velocity_exceedance_5mps`: `stable_across_all_pairs`; all selected hotspot
  cells recur in all `6` pairwise comparisons, with pairwise-support histogram
  `6=8`. This layer is spatially stable at the selected hotspot scale.

Taken together, the hotspot core is spatially stable for the velocity layer and
mostly persistent for jump height, while kinetic energy retains a transient
edge. That is a stability statement about the measured hotspot cells only; it
does not change the existing `inconclusive` convergence interpretation or any
claim boundary.

The same measured stability classes can be exported as GIS-ready diagnostic
summaries with `scripts/summarize_spatial_same_scale_uncertainty.py
--gis-output-dir <ignored-root>`. That helper writes JSON, CSV, and GeoJSON
products for persistent agreement, persistent disagreement, support/nodata
sensitivity, closure-limiting disagreement, and deferrable disagreement.
Those outputs are intentionally summaries rather than new raster layers: they
repackage the measured cell classes for GIS inspection without introducing a
new hazard map or a new interpretation criterion.

For the decision delta between the closure-limiting layers and the deferrable
velocity layer, see
`scripts/summarize_tschamut_closure_gap_deltas.py`. That helper reuses the
same measured spatial evidence to show which fields keep the pilot
inconclusive, which ones are deferrable, and why the current evidence is
closer to deferred than to no-go.

The conditional closure helper now reads this spatial concentration directly,
so the same evidence can be treated as closure-limiting, deferrable, or
unresolved rather than only as a scalar envelope.

The canonical conditional diagnostic interpretation helper,
`scripts/summarize_tschamut_conditional_diagnostic_interpretation.py`,
uses this envelope alongside closure, reduced-output, GIS/COG, runtime,
portability, and physical-credibility summaries. That keeps the measured
uncertainty evidence inside the diagnostic boundary without turning it into an
acceptance claim.
For a materialized synthesis bundle, treat `--artifact-dir validation/private/tschamut_public_pilot/diagnostic_interpretation_v1`
on that helper as the primary entrypoint.

For the measured closure-gap delta between closure-limiting and deferrable
layers, see `scripts/summarize_tschamut_closure_gap_deltas.py`.

For hotspot provenance back to the committed source-zone and scenario
evidence, see `scripts/summarize_tschamut_hotspot_provenance.py`. Its
measured summary keeps the same closure-limiting hotspots in the
source-zone/scenario boundary: the selected cells remain outside the source
polygon, `max_kinetic_energy` is fully shared-support magnitude, and
`max_jump_height` is the layer with the strongest support/nodata sensitivity.
That attribution is interpretive evidence only; it does not change the
existing `inconclusive` closure status.

Compact mask summaries are also available from
`scripts/summarize_spatial_same_scale_uncertainty.py --mask-output-dir <ignored-root>`.
Those summaries preserve the same layer-specific counts, extents, and closure
roles for `max_kinetic_energy`, `max_jump_height`, and
`velocity_exceedance_5mps` without forcing workers to re-derive the same cell
sets from pairwise rasters.

## Remaining Uncertainty
- seed sensitivity remains structurally limiting on the shared grid
- `max_kinetic_energy` still dominates the envelope
- `max_jump_height` still carries support/nodata variation
- velocity exceedance layers still vary across seeds, but stay below the kinetic-energy spread
- the gate-target interpretation remains conservative and non-operational
