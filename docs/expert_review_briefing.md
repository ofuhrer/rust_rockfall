# Expert Review Briefing

Purpose: support external review of the current rockfall simulation and hazard-map workflow before further physics or operational work.

This is not an operational hazard assessment and not a claim of equivalence with state-of-practice proprietary tools.

## What Exists Now

- Deterministic simulator with analytic, synthetic, and public-data validation workflows.
- Public Tschamut all-runs benchmark using registered public observations and public swissALTI3D terrain.
- Chant Sura trajectory/contact validation fixtures.
- Passive block-shape metadata scaffold and Tschamut/EOTA shape sidecars.
- Diagnostic and labelled conditional hazard layers, including sampling-weighted variants.
- GeoTIFF export for existing hazard rasters; Cloud-Optimized GeoTIFF is deliberately deferred until a verified writer is selected.
- Manifest-backed provenance, checksums, execution/scientific status, and non-operational warnings.

## Key Evidence

- Tschamut default `translational_v0` under-runs by about 35 m mean signed runout error across 80 processed public runs.
- Tschamut `sphere_rotational_v1` over-runs strongly, with about 105 m mean signed runout error.
- Chant Sura rotational contact improves small-fixture trajectory shape and energy metrics, but rebound, jump, and timing errors remain.
- Shape metadata is currently passive and does not affect dynamics.
- Probabilistic Phase 1 supports conditional and sampling-weighted map semantics only, not annualized hazard.

## Questions For Reviewers

### Rockfall and Geomorphology

- Do the Tschamut grouped failure modes look more like shape/contact problems, terrain/material problems, release-condition uncertainty, or mixed causes?
- Are impact-rich under-running trajectories a useful diagnostic for stopping behaviour?
- Which additional field metrics should be included before model changes?

### Contact-Model Researchers

- Are the Chant Sura contact metrics sufficient to design an active shape-contact prototype?
- Which minimal shape/orientation state should be tested first without overfitting?
- What acceptance criteria should prevent a model that fixes Chant Sura but worsens Tschamut?

### Hazard Practitioners

- Are the distinctions between diagnostics, conditional maps, sampling-weighted maps, annualized maps, and risk products clear?
- Are the current reach, energy, jump-height, deposition, and impact-density layers useful for review?
- What metadata is missing from the map-package manifests?

### GIS Specialists

- Are GeoTIFF metadata, CRS, NODATA, transform, and layer naming sufficient for first review?
- Do QGIS-loaded GeoTIFF reach, energy, jump-height, deposition, and exceedance layers preserve the intended map semantics?
- What COG, styling, tiling, or metadata-profile requirements should come next?
- Are generated artifacts and provenance easy enough to audit?

### Operational Stakeholders

- What evidence would be required before a controlled non-operational Swiss pilot could be externally reviewed?
- Which limitations must be most visible to avoid misuse?
- Which products should remain explicitly out of scope until annual frequencies and calibration exist?

## Pending Decisions

1. Whether to implement an active shape-contact prototype next or first strengthen terrain/material calibration design.
2. Whether to expand runnable external benchmarks before changing physics.
3. Whether Phase 2 GIS work should focus on COG packaging, map-product bundles, or regional orchestration.
4. What minimal source-frequency evidence is required before annualized hazard maps can be discussed.

## Review Materials

- `docs/model_benchmark_execution_report.md`
- `docs/model_overall_assessment_report.md`
- `docs/public_tschamut_all_runs_grouped_validation.md`
- `docs/public_tschamut_failure_mode_analysis.md`
- `docs/chant_sura_contact_validation.md`
- `docs/probabilistic_hazard_phase1_closure.md`
- `docs/ramms_gap_analysis.md`
- `docs/active_shape_contact_design.md`
