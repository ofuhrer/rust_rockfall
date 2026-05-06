# Expert Review Baseline Release Note

Status: release/tag preparation note only. Do not treat this document as an
operational product release.

Proposed tag name: `v0.6.0-expert-review-baseline`

This note defines the current repository state as a frozen expert-review
baseline before further physics, calibration, or operational workflow changes.
The tag should be created only after explicit human approval.

## Purpose

The baseline is intended for review by rockfall scientists, hazard
practitioners, geomorphologists, contact-model researchers, GIS specialists,
and potential operational stakeholders. It is a stable reference point for
discussion, not a claim of operational readiness or equivalence with any
state-of-practice proprietary tool.

## Included

- Benchmark execution report:
  `docs/model_benchmark_execution_report.md`
- Overall model assessment:
  `docs/model_overall_assessment_report.md`
- Expert review briefing:
  `docs/expert_review_briefing.md`
- Unified public benchmark framework for Tschamut 2014, Chant Sura, Chant Sura
  EOTA221, and Mel de la Niva.
- Public Tschamut all-usable grouped validation report and failure-mode
  analysis.
- Chant Sura trajectory/contact validation and held-out generalization reports.
- Passive shape metadata scaffold and Tschamut/EOTA shape metadata sidecars.
- Probabilistic hazard-map Phase 1 semantics:
  source-zone metadata, scenario tables, trajectory metadata propagation,
  labelled hazard manifests, map-package manifests, and CI-safe smoke example.
- Phase 2A opt-in GeoTIFF export for existing hazard rasters.
- Manifest/provenance improvements, artifact checksums, execution/scientific
  status split, and benchmark framework documentation.

## Explicitly Not Included

- No active non-spherical shape-contact physics.
- No parameter tuning or calibration.
- No default-physics changes.
- No annualized hazard maps.
- No physical source-frequency model.
- No exposure, vulnerability, or risk modelling.
- No operational hazard-map claim.
- No Cloud-Optimized GeoTIFF implementation; COG requests fail explicitly.
- No committed large raw public archives, licensed swisstopo data, private DEMs,
  validation results, or hazard outputs.
- No claim of equivalence to RAMMS::ROCKFALL or any proprietary model.

## Reproducible Commands

Repository checks for the baseline:

```bash
python3 scripts/check_repo_consistency.py
scripts/git-hooks/pre-commit
cargo test
python3 -m unittest tests/test_hazard_layers.py tests/test_performance_benchmark.py
```

Full local pre-push verification, including verification and validation cases:

```bash
scripts/git-hooks/pre-push
```

Public benchmark preparation commands:

```bash
python3 scripts/prepare_chant_sura_public_benchmark.py \
  --output-root validation/results/public_benchmarks/chant_sura_baseline

python3 scripts/prepare_chant_sura_eota221_benchmark.py \
  --output-root validation/results/public_benchmarks/chant_sura_eota221_baseline

python3 scripts/prepare_mel_de_la_niva_benchmark.py \
  --output-root validation/results/public_benchmarks/mel_de_la_niva_baseline

python3 scripts/prepare_tschamut_public_benchmark.py \
  --output-root validation/results/public_benchmarks/tschamut_all_runs \
  --run-limit 80 \
  --padding-m 250 \
  --force
```

Representative public validation commands:

```bash
cargo run -- validate --case validation/results/public_benchmarks/tschamut_all_runs/cases/tschamut_public_benchmark_baseline.yaml
cargo run -- validate --case validation/results/public_benchmarks/tschamut_all_runs/cases/tschamut_public_benchmark_rotational.yaml
cargo run -- validate --case validation/cases/chant_sura_contact.yaml
cargo run -- validate --case validation/cases/chant_sura_contact_rotational.yaml
cargo run -- validate --case validation/cases/chant_sura_contact_extended.yaml
cargo run -- validate --case validation/cases/chant_sura_contact_extended_rotational.yaml
cargo run -- validate --case validation/cases/chant_sura_contact_heldout.yaml
cargo run -- validate --case validation/cases/chant_sura_contact_heldout_rotational.yaml
```

Representative GeoTIFF smoke workflow:

```bash
cargo run -- validate --case validation/cases/probabilistic_phase1_smoke.yaml

python3 scripts/build_hazard_layers.py \
  --case validation/cases/probabilistic_phase1_smoke.yaml \
  --trajectory validation/results/probabilistic_phase1_smoke_trajectory.csv \
  --ensemble-trajectories-dir validation/results/probabilistic_phase1_smoke_trajectories \
  --output-dir hazard/results/probabilistic_phase1_smoke_geotiff \
  --cell-size 2 \
  --no-plots \
  --export-geotiff
```

## Generated Artifact Policy

Generated artifacts remain out of git unless they are intentional tiny fixtures.
This includes:

- `validation/results/**`
- `hazard/results/**`
- raw public archives under ignored cache directories
- private or licensed swisstopo data
- generated PNG/HTML/GeoTIFF outputs
- local review scratch directories

Expert reviewers should reproduce generated artifacts from commands and compare
them against manifest checksums and provenance fields. Review packages should
share generated products separately from the source repository when needed.

## External Review Questions

1. Do the public Tschamut grouped failure modes indicate a shape/contact gap,
   terrain/material gap, release-condition gap, or mixed cause?
2. Are Chant Sura contact metrics sufficient to design a minimal active
   shape-contact prototype?
3. Are rebound, jump-height, impact-timing, and energy diagnostics adequate for
   evaluating future contact models?
4. Are the probabilistic Phase 1 labels clear enough to distinguish diagnostic,
   conditional, sampling-weighted, physical-probability, and annualized products?
5. Are GeoTIFF outputs and manifests sufficient for first GIS/practitioner
   review?
6. What evidence is missing before a controlled non-operational Swiss pilot can
   be externally reviewed?

## Known Limitations

- The default `translational_v0` model persistently under-runs the public
  Tschamut all-runs benchmark.
- The opt-in `sphere_rotational_v1` model improves some Chant Sura
  trajectory/contact metrics but strongly over-runs Tschamut.
- Passive shape metadata is validated and propagated but does not affect
  dynamics.
- Terrain/material effects and shape/contact effects remain confounded.
- Mel de la Niva remains metadata-only and is not yet a runnable benchmark.
- GeoTIFF export is uncompressed float64 and intentionally not COG.
- Annual frequencies, physical source probabilities, exposure, vulnerability,
  and risk are not implemented.

## Recommended Reviewer Workflow

1. Start with `docs/expert_review_briefing.md` for the short review map.
2. Read `docs/model_benchmark_execution_report.md` for reproducible evidence,
   commands, and metrics.
3. Read `docs/model_overall_assessment_report.md` for maturity, limitations,
   and roadmap implications.
4. Review `docs/public_tschamut_all_runs_grouped_validation.md` and
   `docs/public_tschamut_failure_mode_analysis.md` before discussing physics
   changes.
5. Review `docs/chant_sura_contact_validation.md` and
   `docs/chant_sura_contact_generalization.md` before judging contact-model
   realism.
6. Load representative GeoTIFF hazard outputs in QGIS and compare CRS,
   transform, NODATA, layer names, and manifest semantics.
7. Record feedback as explicit go/no-go criteria for the next physics,
   calibration, GIS, or probabilistic workflow step.

## Next Decisions After Review

- Whether to implement a minimal active shape-contact prototype.
- Whether to design a terrain/material calibration protocol before changing
  contact physics.
- Whether to make Mel de la Niva runnable before further model development.
- Whether GIS Phase 2B should prioritize verified COG export, map-package
  bundles, or regional orchestration.
- What minimum evidence is required before Level 3 annual-frequency semantics
  can be designed.

## Version-Bump Assessment

No version bump is warranted for this release-preparation note by itself. It is
documentation-only and does not add physics, defaults, public APIs, schemas, or
numerical behavior. If the proposed expert-review baseline tag is created, use
the pre-release-style tag `v0.6.0-expert-review-baseline` to identify the frozen
review state without changing `Cargo.toml` or the documented project version.
