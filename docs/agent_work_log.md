# Agent Work Log

Append-only control log for development subagents. Entries should preserve
scientific boundaries: no hidden physics changes, no private geodata, no
operational validation claims, and no risk-map language unless exposure and
vulnerability are explicitly in scope.

## Entry Template

- Milestone id:
- Roadmap item:
- Hypothesis/objective:
- Files intended to change:
- Implementation summary:
- Checks run:
- Reviewer notes:
- Decision:
- Next proposed milestone:

## Roadmap Items 1-5 Micro-Milestone Plan

Planning only; these milestones do not implement roadmap item content yet.

| Proposed milestone | Roadmap item | Micro-milestone objective | Intended scope |
| --- | --- | --- | --- |
| M002 | 1. Impact and Contact Credibility | Define the next audit task for impact/contact diagnostics and evidence gaps. | Planning/docs only unless explicitly approved later. |
| M003 | 2. Terrain and GIS Foundation | Define the next terrain/GIS provenance or CRS-readiness task. | Planning/docs only unless explicitly approved later. |
| M004 | 3. Release-Zone and Scenario Definition | Define the next source-zone and block-scenario semantics task. | Planning/docs only unless explicitly approved later. |
| M005 | 4. Ensemble Orchestration | Define the next deterministic chunking, manifest, or reducer task. | Planning/docs only unless explicitly approved later. |
| M006 | 5. Hazard-Layer Generation | Define the next hazard-layer semantics, metadata, or export-readiness task. | Planning/docs only unless explicitly approved later. |

## Entries

### M001

- Milestone id: M001
- Roadmap item: Control log setup for roadmap items 1-5.
- Hypothesis/objective: A concise append-only log will let future subagents
  coordinate scoped micro-milestones without changing physics, geodata, or
  validation claims.
- Files intended to change: `docs/agent_work_log.md`
- Implementation summary: Created this control log, entry template, and
  roadmap items 1-5 micro-milestone plan.
- Checks run:
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m py_compile scripts/run_dem_terrain_sensitivity.py` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest tests/test_dem_terrain_sensitivity.py` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/run_dem_terrain_sensitivity.py --pilot-manifest data/processed/swisstopo/tschamut_public_pilot_manifest.yaml --source-scenario-policy validation/policies/tschamut_public_source_scenario_policy_v1.yaml --allow-missing-source-dem --output-dir /tmp/rust_rockfall_tschamut_dem_sensitivity_priority3_check` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/validate_public_real_site_geodata_manifest.py data/processed/swisstopo/tschamut_public_pilot_manifest.yaml` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/validate_source_scenario_policy.py validation/policies/tschamut_public_source_scenario_policy_v1.yaml` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/check_repo_consistency.py` passed.
  `scripts/git-hooks/pre-commit` passed.
  `cargo fmt --check` passed.
  `cargo clippy --all-targets --all-features -- -D warnings` passed.
  `cargo test` passed.
  `cargo run -- verify --all` passed.
  `cargo run -- validate --all` passed.
  `scripts/git-hooks/pre-commit` passed.
  `scripts/git-hooks/pre-commit` passed.
  `git diff --check` passed.
- Reviewer notes: Pending reviewer input.
- Decision: ACCEPT; Priority 3 done at the selected-domain gate level, with
  terrain-variant metrics blocked only by the intentionally ignored processed
  DEM being absent from a clean checkout.
- Next proposed milestone: M002.

## Correction: Roadmap Items 1-5 Target Mapping

This correction supersedes the initial "Roadmap Items 1-5 Micro-Milestone
Plan" above. The initial plan incorrectly mapped items 1-5 to sections from
`docs/roadmap_hazard_mapping.md`. Future work should use the corrected target
sequence below, drawn from the roadmap recommendation targets:

1. Controlled real-site Tschamut/swissALTI3D pilot with embedded gates.
2. Hazard-map semantics and interpretation guide.
3. Pilot GIS/QGIS package and raster semantics.
4. Source-zone and block-scenario semantics v1.
5. DEM and terrain-representation sensitivity benchmark.

## Corrected M002-M015 Micro-Milestone Sequence

Planning only; these milestones do not implement roadmap item content yet.

| Proposed milestone | Target | Micro-milestone objective | Intended scope |
| --- | --- | --- | --- |
| M002 | 1. Controlled real-site Tschamut/swissALTI3D pilot with embedded gates | Define pilot scope, non-tuning constraints, required inputs, and go/no-go gates. | Planning/docs only unless explicitly approved later. |
| M003 | 1. Controlled real-site Tschamut/swissALTI3D pilot with embedded gates | Define execution-report structure for performance, terrain observations, manifests, and visual QA. | Planning/docs only unless explicitly approved later. |
| M004 | 1. Controlled real-site Tschamut/swissALTI3D pilot with embedded gates | Define pilot review gate criteria and failure-mode reporting expectations. | Planning/docs only unless explicitly approved later. |
| M005 | 2. Hazard-map semantics and interpretation guide | Define guide outline for conditional, sampling-weighted, physical-probability, and annual-frequency semantics. | Planning/docs only unless explicitly approved later. |
| M006 | 2. Hazard-map semantics and interpretation guide | Define required labels, limitations, and non-operational interpretation language for hazard layers. | Planning/docs only unless explicitly approved later. |
| M007 | 2. Hazard-map semantics and interpretation guide | Define review checklist for preventing risk-map language and unsupported probability claims. | Planning/docs only unless explicitly approved later. |
| M008 | 3. Pilot GIS/QGIS package and raster semantics | Define GIS package contents, CRS/vertical-datum metadata, grid alignment, nodata, and provenance expectations. | Planning/docs only unless explicitly approved later. |
| M009 | 3. Pilot GIS/QGIS package and raster semantics | Define raster-layer semantics for reach, deposition, energy, jump height, and uncertainty review layers. | Planning/docs only unless explicitly approved later. |
| M010 | 3. Pilot GIS/QGIS package and raster semantics | Define QGIS visual QA checklist and package acceptance gate. | Planning/docs only unless explicitly approved later. |
| M011 | 4. Source-zone and block-scenario semantics v1 | Define source-zone representation, release-cell policy, provenance, and exclusion rules. | Planning/docs only unless explicitly approved later. |
| M012 | 4. Source-zone and block-scenario semantics v1 | Define block scenario metadata for size, shape class, release conditions, weights, and seed policy. | Planning/docs only unless explicitly approved later. |
| M013 | 4. Source-zone and block-scenario semantics v1 | Define consistency checks for scenario weighting, calibration/validation separation, and deterministic seeding. | Planning/docs only unless explicitly approved later. |
| M014 | 5. DEM and terrain-representation sensitivity benchmark | Define benchmark design for DEM resolution, interpolation, smoothing, cliff/nodata handling, and terrain classes. | Planning/docs only unless explicitly approved later. |
| M015 | 5. DEM and terrain-representation sensitivity benchmark | Define sensitivity-report outputs, comparison metrics, and decision gate for pilot terrain readiness. | Planning/docs only unless explicitly approved later. |

## M001 Revision Note

- Milestone id: M001 revision.
- Roadmap item: Control log setup for corrected roadmap recommendation targets
  1-5.
- Hypothesis/objective: Append-only correction can supersede the incorrect
  initial micro-plan without deleting prior log content.
- Files intended to change: `docs/agent_work_log.md`
- Implementation summary: Appended corrected target mapping, corrected
  M002-M015 sequence, and this revision note.
- Checks run:
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest tests/test_public_real_site_conditional_pilot_run.py tests/test_dem_terrain_sensitivity.py` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/validate_public_real_site_conditional_pilot_run.py validation/templates/public_real_site_conditional_pilot_run_v1.yaml` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/validate_public_real_site_conditional_pilot_run.py validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml --print-command-plan` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/run_dem_terrain_sensitivity.py --pilot-manifest data/processed/swisstopo/tschamut_public_pilot_manifest.yaml --source-scenario-policy validation/policies/tschamut_public_source_scenario_policy_v1.yaml --allow-missing-source-dem --output-dir validation/private/tschamut_public_pilot/dem_sensitivity_gate_v1` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest discover -s tests -p 'test_*.py'` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/check_repo_consistency.py` passed.
  `scripts/git-hooks/pre-commit` passed.
  `cargo fmt --check` passed.
  `cargo clippy --all-targets --all-features -- -D warnings` passed.
  `cargo test` passed.
  `cargo run -- verify --all` passed.
  `cargo run -- validate --all` passed.
- Reviewer notes: Initial M001 micro-plan used the wrong roadmap mapping:
  Impact/Contact, Terrain/GIS, Release-Zone, Ensemble Orchestration, and
  Hazard-Layer Generation instead of the requested recommendation targets.
- Decision: REVISE for the initial mapping; corrected decision ACCEPT if this
  correction is complete.
- Next proposed milestone: M002.

### M001 Revision Check Addendum

- Milestone id: M001 revision check.
- Roadmap item: Control log setup for corrected roadmap recommendation targets
  1-5.
- Hypothesis/objective: Record targeted markdown-only verification for the
  append-only correction.
- Files intended to change: `docs/agent_work_log.md`
- Implementation summary: Recorded completion of the requested targeted check.
- Checks run: `git diff --check -- docs/agent_work_log.md`
- Reviewer notes: Correction remains append-only and supersedes the initial
  incorrect plan without deleting it.
- Decision: ACCEPT.
- Next proposed milestone: M002.

### M002

- Milestone id: M002.
- Roadmap item: 1. Controlled real-site Tschamut/swissALTI3D pilot with
  embedded gates.
- Hypothesis/objective: Define the pilot scope, no-tuning constraints,
  required inputs, and go/no-go/evidence gates before any pilot execution or
  report-template work.
- Files intended to change:
  `docs/tschamut_swissalti3d_controlled_pilot_plan.md`,
  `docs/agent_work_log.md`
- Implementation summary: Added a concise pilot scope and evidence-gate
  inventory to the controlled pilot plan, emphasizing provenance completeness,
  source-zone independence, frozen no-tuning settings, manifest completeness,
  spatial QA, comparison evidence, private-data boundaries, and scoped
  non-operational interpretation.
- Checks run:
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/validate_public_real_site_geodata_manifest.py data/processed/swisstopo/tschamut_public_pilot_manifest.yaml` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/validate_source_scenario_policy.py validation/policies/tschamut_public_source_scenario_policy_v1.yaml` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/run_dem_terrain_sensitivity.py --pilot-manifest data/processed/swisstopo/tschamut_public_pilot_manifest.yaml --source-scenario-policy validation/policies/tschamut_public_source_scenario_policy_v1.yaml --output-dir validation/private/tschamut_public_pilot/dem_sensitivity_gate_v1` passed.
  `cargo run -- validate --case validation/private/tschamut_public_pilot/gate_v1/tschamut_public_conditional_gate_case.yaml` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/build_hazard_layers.py --case validation/private/tschamut_public_pilot/gate_v1/tschamut_public_conditional_gate_case.yaml --output-dir hazard/results/tschamut_public_pilot/gate_v1 --grid-xmin 2696376.0 --grid-ymin 1167384.0 --grid-ncols 300 --grid-nrows 304 --grid-cell-size 2.0 --map-product-id tschamut_public_conditional_gate_v1 --probability-mode sampling_weighted_conditional --normalization-scope conditioned_on_filter --source-zone-metadata-path data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_source_zone_metadata_v1.yaml --scenario-table-path data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_scenario_table_v1.csv --map-package-manifest-json hazard/results/tschamut_public_pilot/gate_v1/tschamut_public_conditional_gate_v1_map_package_manifest.json --export-geotiff --pilot-gis-package --pilot-gis-package-manifest-json hazard/results/tschamut_public_pilot/gate_v1/tschamut_public_conditional_gate_v1_pilot_gis_package_manifest.json --pilot-gis-qa-status not-run --pilot-gis-qa-note "Manual GIS/QGIS inspection has not been run for this generated package." --reducer-workers 2 --no-plots --diagnostics validation/private/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_metrics.json --trajectory validation/private/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_trajectory.csv --ensemble-trajectories-dir validation/private/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_trajectories --deposition validation/private/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_deposition.csv --ensemble-impact-events-dir validation/private/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_impacts --kinetic-energy-exceedance-j 1000.0 --kinetic-energy-exceedance-j 10000.0 --jump-height-exceedance-m 1.0 --jump-height-exceedance-m 2.0` passed.
  `/usr/bin/time` sidecar reruns passed for the validation and hazard commands, with `UV_CACHE_DIR=/tmp/uv-cache` required for the hazard command.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/validate_pilot_gis_package.py hazard/results/tschamut_public_pilot/gate_v1/tschamut_public_conditional_gate_v1_pilot_gis_package_manifest.json --require-real-site --require-existing-files --format json` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/summarize_pilot_scaling.py --validation-manifest validation/private/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_manifest.json --hazard-manifest hazard/results/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_manifest.json --gis-package-manifest hazard/results/tschamut_public_pilot/gate_v1/tschamut_public_conditional_gate_v1_pilot_gis_package_manifest.json --validation-time-file validation/private/tschamut_public_pilot/gate_v1/validation_gate_time.txt --hazard-time-file hazard/results/tschamut_public_pilot/gate_v1/hazard_gate_time.txt --output-json hazard/results/tschamut_public_pilot/gate_v1/tschamut_public_conditional_gate_v1_scaling_summary.json --output-md docs/tschamut_public_pilot_scaling_review.md` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest tests/test_public_real_site_conditional_pilot_run.py tests/test_pilot_gis_package_validator.py tests/test_pilot_scaling_summary.py tests/test_dem_terrain_sensitivity.py` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest discover -s tests -p 'test_*.py'` passed.
  `cargo fmt --check` passed.
  `cargo clippy --all-targets --all-features -- -D warnings` passed.
  `cargo test` passed.
  `cargo run -- verify --all` passed.
  `cargo run -- validate --all` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/check_repo_consistency.py` passed.
  `scripts/git-hooks/pre-commit` passed.
- Reviewer notes: No physics changes, no private geodata, no report scripts or
  templates, no operational validation claims, and no risk-map language.
- Decision: ACCEPT; Priority 4 done as an executable selected-domain no-go
  gate, with actual pilot simulation and hazard artifacts blocked only by the
  intentionally ignored processed DEM being absent from the local checkout.
- Next proposed milestone: M003.

### M002 Check Addendum

- Milestone id: M002 check.
- Roadmap item: 1. Controlled real-site Tschamut/swissALTI3D pilot with
  embedded gates.
- Hypothesis/objective: Record targeted markdown-only verification for the
  M002 docs-only scope change.
- Files intended to change:
  `docs/tschamut_swissalti3d_controlled_pilot_plan.md`,
  `docs/agent_work_log.md`
- Implementation summary: Recorded completion of the requested targeted check.
- Checks run:
  `git diff --check -- docs/tschamut_swissalti3d_controlled_pilot_plan.md docs/agent_work_log.md`
- Reviewer notes: Check covers whitespace/errors in the intended changed files.
- Decision: ACCEPT.
- Next proposed milestone: M003.

### M002 Revision Note

- Milestone id: M002 revision.
- Roadmap item: 1. Controlled real-site Tschamut/swissALTI3D pilot with
  embedded gates.
- Hypothesis/objective: Revise the M002 gate inventory and wording so the
  controlled pilot records bottleneck evidence, avoids broad validation or
  operational maturity language, and harmonizes GIS/geodata handling notes.
- Files intended to change:
  `docs/tschamut_swissalti3d_controlled_pilot_plan.md`,
  `docs/tschamut_swissalti3d_pilot.md`,
  `docs/agent_work_log.md`
- Implementation summary: Added a performance/bottleneck interpretability gate
  requiring phase timings and row/file/byte counts for simulation, output
  writing, and hazard accumulation context; softened proxy-terrain and
  rotational-contact interpretation language; replaced production-style wording
  with batch diagnostic wording; added private-path/provenance redaction and
  processed-checksum notes; and noted that real pilot acceptance should use
  explicit DEM-derived hazard-grid arguments.
- Checks run:
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest tests/test_public_real_site_conditional_pilot_run.py` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest tests/test_public_real_site_conditional_pilot_run.py tests/test_pilot_gis_package_validator.py tests/test_pilot_scaling_summary.py tests/test_dem_terrain_sensitivity.py` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest discover -s tests -p 'test_*.py'` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/check_repo_consistency.py` passed.
  `scripts/git-hooks/pre-commit` passed.
  `git diff --check` passed.
  `cargo fmt --check` passed.
  `cargo clippy --all-targets --all-features -- -D warnings` passed.
  `cargo test` passed.
  `cargo run -- verify --all` passed.
  `cargo run -- validate --all` passed.
  `scripts/git-hooks/pre-push` passed.
- Reviewer notes: First M002 pass needed revision for performance
  interpretability evidence, scientific wording around validation and contact
  recommendations, and GIS/geodata handling for private paths, checksums, and
  explicit DEM-derived hazard grids.
- Decision: REVISE for the first M002 pass; corrected decision ACCEPT if this
  correction is complete.
- Next proposed milestone: M003.

### M002 Revision Check Addendum

- Milestone id: M002 revision check.
- Roadmap item: 1. Controlled real-site Tschamut/swissALTI3D pilot with
  embedded gates.
- Hypothesis/objective: Record targeted verification for the M002 revision.
- Files intended to change: `docs/agent_work_log.md`
- Implementation summary: Recorded that the requested M002 revision check
  passed and reviewer findings were addressed.
- Checks run:
  `git diff --check -- docs/tschamut_swissalti3d_controlled_pilot_plan.md docs/tschamut_swissalti3d_pilot.md docs/agent_work_log.md`
  passed.
- Reviewer notes: Performance, scientific wording, and GIS/geodata findings
  were addressed.
- Decision: ACCEPT.
- Next proposed milestone: M003.

### M003

- Milestone id: M003.
- Roadmap item: 1. Controlled real-site Tschamut/swissALTI3D pilot with
  embedded gates.
- Hypothesis/objective: Define the execution-report structure for performance,
  terrain observations, manifests, and visual QA without adding report scripts
  or template files.
- Files intended to change:
  `docs/tschamut_swissalti3d_controlled_pilot_plan.md`,
  `docs/agent_work_log.md`
- Implementation summary: Expanded the controlled pilot deliverable guidance
  into a required diagnostic report structure covering input/provenance
  inventory, command log, gate table, validation and hazard manifest summaries,
  metric table, visual QA notes, performance/bottleneck observations,
  terrain-representation observations, interpretation category, next-step
  decision, and limitations. Added share-safe reporting constraints for raw
  data, private paths, restricted tile identifiers, and share-sensitive
  provenance.
- Checks run:
  `which qgis` returned no executable.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest tests/test_pilot_gis_visual_qa.py` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest tests/test_pilot_gis_visual_qa.py tests/test_pilot_gis_package_validator.py` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/validate_pilot_gis_visual_qa.py validation/pilot_runs/tschamut_public_gis_visual_qa_v1.yaml --format json` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/validate_pilot_gis_visual_qa.py validation/pilot_runs/tschamut_public_gis_visual_qa_v1.yaml --require-existing-package --format json` passed locally against ignored generated outputs.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/validate_pilot_gis_package.py hazard/results/tschamut_public_pilot/gate_v1/tschamut_public_conditional_gate_v1_pilot_gis_package_manifest.json --require-real-site --require-existing-files --format json` passed locally against ignored generated outputs.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest discover -s tests -p 'test_*.py'` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/check_repo_consistency.py` passed.
  `git diff --check` passed.
  `cargo fmt --check` passed.
  `cargo clippy --all-targets --all-features -- -D warnings` passed.
  `cargo test` passed.
  `cargo run -- verify --all` passed.
  `cargo run -- validate --all` passed.
- Reviewer notes: Docs-only scope; no report scripts, templates, physics
  changes, private geodata, operational validation claims, or risk-map language.
- Decision: Pending.
- Next proposed milestone: M004.

### M003 Check Addendum

- Milestone id: M003 check.
- Roadmap item: 1. Controlled real-site Tschamut/swissALTI3D pilot with
  embedded gates.
- Hypothesis/objective: Record targeted markdown-only verification for the
  M003 docs-only scope change.
- Files intended to change:
  `docs/tschamut_swissalti3d_controlled_pilot_plan.md`,
  `docs/agent_work_log.md`
- Implementation summary: Recorded completion of the requested targeted check.
- Checks run:
  `git diff --check -- docs/tschamut_swissalti3d_controlled_pilot_plan.md docs/agent_work_log.md`
- Reviewer notes: Check covers whitespace/errors in the intended changed files.
- Decision: ACCEPT.
- Next proposed milestone: M004.

### M003 Revision Note

- Milestone id: M003 revision.
- Roadmap item: 1. Controlled real-site Tschamut/swissALTI3D pilot with
  embedded gates.
- Hypothesis/objective: Revise the diagnostic report structure to make hazard
  GIS metadata carry-through and visual QA artifact traceability explicit.
- Files intended to change:
  `docs/tschamut_swissalti3d_controlled_pilot_plan.md`,
  `docs/agent_work_log.md`
- Implementation summary: Updated the hazard manifest summary requirements to
  confirm EPSG:2056/LN02, geotransform or affine grid, nodata,
  extent/resolution, and terrain/source provenance carry through to hazard
  outputs or GeoTIFF metadata where applicable. Updated visual QA notes to
  require reviewed PNG, HTML, GIS, or QGIS artifact references where present,
  or an explicit no-artifact QA statement.
- Checks run:
  Full local verification and pre-push checks passed in commit `1e80234`
  (`Reconcile Tschamut pilot gate evidence`), including `cargo fmt --check`,
  `cargo clippy --all-targets --all-features -- -D warnings`, `cargo test`,
  `cargo run -- verify --all`, `cargo run -- validate --all`, full Python
  unittest discovery through `UV_CACHE_DIR=/tmp/uv-cache uv run python`,
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/check_repo_consistency.py`,
  `scripts/git-hooks/pre-commit`, and `scripts/git-hooks/pre-push`.
- Reviewer notes: M003 needed stronger GIS metadata carry-through and visual QA
  artifact traceability requirements.
- Decision: ACCEPT if corrected.
- Next proposed milestone: M004.

### M003 Revision Check Addendum

- Milestone id: M003 revision check.
- Roadmap item: 1. Controlled real-site Tschamut/swissALTI3D pilot with
  embedded gates.
- Hypothesis/objective: Record targeted markdown-only verification for the
  M003 revision.
- Files intended to change:
  `docs/tschamut_swissalti3d_controlled_pilot_plan.md`,
  `docs/agent_work_log.md`
- Implementation summary: Recorded completion of the requested targeted check.
- Checks run:
  `git diff --check -- docs/tschamut_swissalti3d_controlled_pilot_plan.md docs/agent_work_log.md`
- Reviewer notes: GIS metadata carry-through and visual QA artifact findings
  were addressed.
- Decision: ACCEPT.
- Next proposed milestone: M004.

### M004

- Milestone id: M004.
- Roadmap item: 1. Controlled real-site Tschamut/swissALTI3D pilot with
  embedded gates.
- Hypothesis/objective: Define post-run pilot review gate criteria and
  failure-mode reporting expectations without adding scripts or templates.
- Files intended to change:
  `docs/tschamut_swissalti3d_controlled_pilot_plan.md`,
  `docs/agent_work_log.md`
- Implementation summary: Added post-run gate review criteria for G1-G9,
  including allowed statuses (`pass`, `no-go`, `inconclusive`, `not-run`),
  required reason text for no-go/inconclusive outcomes, rerun limits, and
  failure-mode categories for provenance, CRS/grid alignment, source-zone
  freeze, manifest/output completeness, visual QA, performance evidence,
  terrain-representation confounders, comparison evidence, and interpretation
  boundaries. Clarified that no-go outcomes lead to data, provenance, or
  process fixes, rerun, or deferral, not parameter tuning.
- Checks run:
  Full local verification and pre-push checks passed in commit `ae7bbe5`
  (`Record Tschamut GIS visual QA gate`), including focused visual-QA tests and
  validators, `cargo fmt --check`,
  `cargo clippy --all-targets --all-features -- -D warnings`, `cargo test`,
  `cargo run -- verify --all`, `cargo run -- validate --all`, full Python
  unittest discovery through `UV_CACHE_DIR=/tmp/uv-cache uv run python`,
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/check_repo_consistency.py`,
  `scripts/git-hooks/pre-commit`, and `scripts/git-hooks/pre-push`.
- Reviewer notes: Docs-only scope; no report scripts, templates, physics
  changes, private geodata, operational validation claims, risk-map language,
  or tuning response to failures.
- Decision: Pending.
- Next proposed milestone: M005.

### M004 Check Addendum

- Milestone id: M004 check.
- Roadmap item: 1. Controlled real-site Tschamut/swissALTI3D pilot with
  embedded gates.
- Hypothesis/objective: Record targeted markdown-only verification for the
  M004 docs-only scope change.
- Files intended to change:
  `docs/tschamut_swissalti3d_controlled_pilot_plan.md`,
  `docs/agent_work_log.md`
- Implementation summary: Recorded completion of the requested targeted check.
- Checks run:
  `git diff --check -- docs/tschamut_swissalti3d_controlled_pilot_plan.md docs/agent_work_log.md`
- Reviewer notes: Check covers whitespace/errors in the intended changed files.
- Decision: ACCEPT.
- Next proposed milestone: M005.

### M004 Revision Note

- Milestone id: M004 revision.
- Roadmap item: 1. Controlled real-site Tschamut/swissALTI3D pilot with
  embedded gates.
- Hypothesis/objective: Tighten post-run gate criteria for optional `not-run`
  use, visual QA evidence, CRS/grid alignment, checksum evidence, expected-vs-
  actual output counts, performance run context, and report failure labels.
- Files intended to change:
  `docs/tschamut_swissalti3d_controlled_pilot_plan.md`,
  `docs/agent_work_log.md`
- Implementation summary: Reserved `not-run` for explicitly optional branches,
  clarified that missing required validation outputs, hazard manifests,
  comparison metrics, or visual QA are `no-go`, strengthened G6 visual QA
  evidence requirements, expanded CRS/grid alignment failure modes to include
  raster origin and orientation, required private DEM checksums or recorded
  reasons, required actual-vs-expected release/ensemble/output counts and
  hazard input rows, required performance run context, and required
  failure-mode labels for every `no-go` and `inconclusive` report gate.
- Checks run:
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/validate_public_real_site_geodata_manifest.py data/processed/swisstopo/tschamut_public_pilot_manifest.yaml` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/validate_pilot_obstacle_scope.py validation/pilot_runs/tschamut_public_obstacle_scope_v1.yaml --format json` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest tests/test_pilot_obstacle_scope.py` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest tests/test_pilot_obstacle_scope.py tests/test_public_real_site_geodata_manifest.py` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest discover -s tests -p 'test_*.py'` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/check_repo_consistency.py` passed.
  `git diff --check` passed.
  `cargo fmt --check` passed.
  `cargo clippy --all-targets --all-features -- -D warnings` passed.
  `cargo test` passed.
  `cargo run -- verify --all` passed.
  `cargo run -- validate --all` passed.
- Reviewer notes: M004 needed stronger distinction between optional not-run
  branches and missing required evidence, plus sharper GIS alignment,
  checksum, output-count, performance-context, and gate-label requirements.
- Decision: ACCEPT if corrected.
- Next proposed milestone: M005.

### M004 Revision Check Addendum

- Milestone id: M004 revision check.
- Roadmap item: 1. Controlled real-site Tschamut/swissALTI3D pilot with
  embedded gates.
- Hypothesis/objective: Record targeted markdown-only verification for the
  M004 revision.
- Files intended to change:
  `docs/tschamut_swissalti3d_controlled_pilot_plan.md`,
  `docs/agent_work_log.md`
- Implementation summary: Recorded completion of the requested targeted check.
- Checks run:
  `git diff --check -- docs/tschamut_swissalti3d_controlled_pilot_plan.md docs/agent_work_log.md`
- Reviewer notes: Optional branch handling, visual QA, CRS/grid alignment,
  checksum, count, performance context, and gate-label findings were addressed.
- Decision: ACCEPT.
- Next proposed milestone: M005.

### M005

- Milestone id: M005.
- Roadmap item: 2. Hazard-map semantics and interpretation guide.
- Hypothesis/objective: Define the initial guide outline for conditional,
  sampling-weighted, physical-probability, and annual-frequency semantics
  without adding examples, tests, physics, risk modelling, or annual-frequency
  implementation.
- Files intended to change:
  `docs/hazard_map_semantics.md`,
  `docs/hazard_layers.md`,
  `docs/agent_work_log.md`
- Implementation summary: Created a skeleton hazard-map semantics guide with a
  status/scope statement, current supported `unweighted_diagnostic` and
  `sampling_weighted_conditional` product classes, unsupported
  `physical_probability` and `annual_frequency` classes, denominator and
  conditioning outline, source-zone and block-scenario conditioning outline,
  hazard-versus-risk boundary, and placeholders for later allowed-language,
  manifest-check, and GIS-package alignment milestones. Added a short
  discoverability cross-reference from the hazard-layer workflow doc.
- Checks run: Pending.
- Reviewer notes: Docs-only scope; no report scripts, templates, tests,
  physics changes, annual-frequency claims, operational validation claims, or
  risk modelling.
- Decision: Pending.
- Next proposed milestone: M006.

### M005 Check Addendum

- Milestone id: M005 check.
- Roadmap item: 2. Hazard-map semantics and interpretation guide.
- Hypothesis/objective: Record targeted markdown-only verification for the
  M005 docs-only scope change.
- Files intended to change:
  `docs/hazard_map_semantics.md`,
  `docs/hazard_layers.md`,
  `docs/agent_work_log.md`
- Implementation summary: Recorded completion of the requested targeted check.
- Checks run:
  `git diff --check -- docs/hazard_map_semantics.md docs/hazard_layers.md docs/agent_work_log.md`
- Reviewer notes: Check covers whitespace/errors in the intended changed files.
- Decision: ACCEPT.
- Next proposed milestone: M006.

### M005 Revision Note

- Milestone id: M005 revision.
- Roadmap item: 2. Hazard-map semantics and interpretation guide.
- Hypothesis/objective: Add the design-only `conditional_probability` product
  class and clarify Target 2 sequencing without weakening the minimal
  deliverable.
- Files intended to change:
  `docs/hazard_map_semantics.md`,
  `docs/next_development_targets.md`,
  `docs/agent_work_log.md`
- Implementation summary: Added `conditional_probability` as an unsupported
  design-only product class aligned with
  `docs/probabilistic_scenario_model_design.md`, and added a Target 2
  sequencing note that M005 creates the guide outline while examples and
  manifest-schema enforcement remain later micro-milestones.
- Checks run: Pending.
- Reviewer notes: M005 needed explicit conditional-probability design-only
  semantics and clearer incremental sequencing for the autonomous loop.
- Decision: ACCEPT if corrected.
- Next proposed milestone: M006.

### M005 Revision Check Addendum

- Milestone id: M005 revision check.
- Roadmap item: 2. Hazard-map semantics and interpretation guide.
- Hypothesis/objective: Record targeted markdown-only verification for the
  M005 revision.
- Files intended to change:
  `docs/hazard_map_semantics.md`,
  `docs/next_development_targets.md`,
  `docs/agent_work_log.md`
- Implementation summary: Recorded completion of the requested targeted check.
- Checks run:
  `git diff --check -- docs/hazard_map_semantics.md docs/next_development_targets.md docs/agent_work_log.md`
- Reviewer notes: Conditional-probability and sequencing findings were
  addressed.
- Decision: ACCEPT.
- Next proposed milestone: M006.

### M006

- Milestone id: M006.
- Roadmap item: 2. Hazard-map semantics and interpretation guide.
- Hypothesis/objective: Add concise allowed and disallowed hazard-map language
  examples for current product classes without adding tests or check scripts.
- Files intended to change:
  `docs/hazard_map_semantics.md`,
  `docs/agent_work_log.md`
- Implementation summary: Added a language examples section covering
  `unweighted_diagnostic`, `sampling_weighted_conditional`,
  design-only `conditional_probability`, unsupported `physical_probability`,
  unsupported `annual_frequency`, significant-impact density/event-location
  distributions, hazard-versus-risk boundaries, operational validation
  boundaries, and return-period language. Clarified that disallowed phrases may
  become allowed only in future phases with required source-frequency,
  exposure/vulnerability, validation, and manifest contracts.
- Checks run: Pending.
- Reviewer notes: Docs-only scope; no tests, check scripts, physics changes,
  annual-frequency implementation, operational validation claims, or risk
  modelling.
- Decision: Pending.
- Next proposed milestone: M007.

### M006 Check Addendum

- Milestone id: M006 check.
- Roadmap item: 2. Hazard-map semantics and interpretation guide.
- Hypothesis/objective: Record targeted markdown-only verification for the
  M006 docs-only scope change.
- Files intended to change:
  `docs/hazard_map_semantics.md`,
  `docs/agent_work_log.md`
- Implementation summary: Recorded completion of the requested targeted check.
- Checks run:
  `git diff --check -- docs/hazard_map_semantics.md docs/agent_work_log.md`
- Reviewer notes: Check covers whitespace/errors in the intended changed files.
- Decision: ACCEPT.
- Next proposed milestone: M007.

### M006 Revision Note

- Milestone id: M006 revision.
- Roadmap item: 2. Hazard-map semantics and interpretation guide.
- Hypothesis/objective: Tighten language semantics for map-package product
  labels, builder config terminology, future claim contracts, and
  conditional/sampling-weighted probability wording.
- Files intended to change:
  `docs/hazard_map_semantics.md`,
  `docs/next_development_targets.md`,
  `docs/agent_work_log.md`
- Implementation summary: Updated guide status to include M006 examples,
  distinguished external `probability_mode` labels from current builder config
  terms, split future-allowance requirements by risk, annual/return-period,
  operational, and physical-probability claim type, tightened
  `sampling_weighted_conditional` disallowed wording so sampling weights never
  become physical probability by implication, tightened design-only
  `conditional_probability` wording, and clarified Target 2 sequencing for
  M005, M006, and M007.
- Checks run: Pending.
- Reviewer notes: M006 needed clearer separation between output labels and
  builder config, narrower future-claim contracts, and stricter probability
  wording.
- Decision: ACCEPT if corrected.
- Next proposed milestone: M007.

### M006 Revision Check Addendum

- Milestone id: M006 revision check.
- Roadmap item: 2. Hazard-map semantics and interpretation guide.
- Hypothesis/objective: Record targeted markdown-only verification for the
  M006 revision.
- Files intended to change:
  `docs/hazard_map_semantics.md`,
  `docs/next_development_targets.md`,
  `docs/agent_work_log.md`
- Implementation summary: Recorded completion of the requested targeted check.
- Checks run:
  `git diff --check -- docs/hazard_map_semantics.md docs/next_development_targets.md docs/agent_work_log.md`
- Reviewer notes: Product-label, config-term, future-contract, and probability
  wording findings were addressed.
- Decision: ACCEPT.
- Next proposed milestone: M007.

### M007

- Milestone id: M007.
- Roadmap item: 2. Hazard-map semantics and interpretation guide.
- Hypothesis/objective: Document semantics consistency-check expectations and
  existing fixture references without adding broad new code.
- Files intended to change:
  `docs/hazard_map_semantics.md`,
  `docs/agent_work_log.md`
- Implementation summary: Added a `Consistency Checks And Fixtures` section to
  the semantics guide, referencing existing probabilistic phase 1 tests and
  fixtures, and listing current/future map-package checks for
  `probability_mode`, normalization scope, annualized flags, numerator and
  denominator, source-zone/scenario conditioning, physical/annual rejection,
  significant-impact event-density wording, and risk exclusion.
- Checks run: Pending.
- Reviewer notes: Docs-only scope; no tests, check scripts, physics changes,
  annual-frequency implementation, operational validation claims, or risk
  modelling.
- Decision: Pending.
- Next proposed milestone: M008.

### M007 Check Addendum

- Milestone id: M007 check.
- Roadmap item: 2. Hazard-map semantics and interpretation guide.
- Hypothesis/objective: Record targeted markdown-only verification for the
  M007 docs-only scope change.
- Files intended to change:
  `docs/hazard_map_semantics.md`,
  `docs/agent_work_log.md`
- Implementation summary: Recorded completion of the requested targeted check.
- Checks run:
  `git diff --check -- docs/hazard_map_semantics.md docs/agent_work_log.md`
- Reviewer notes: Check covers whitespace/errors in the intended changed files.
- Decision: ACCEPT.
- Next proposed milestone: M008.

### M007 Revision Note

- Milestone id: M007 revision.
- Roadmap item: 2. Hazard-map semantics and interpretation guide.
- Hypothesis/objective: Clarify which semantics checks are already covered by
  fixtures and which remain future manifest/check-script expectations.
- Files intended to change:
  `docs/hazard_map_semantics.md`,
  `docs/agent_work_log.md`
- Implementation summary: Split the consistency section into existing coverage
  and expected future expansion, softened physical-probability wording to avoid
  overstating current validator coverage, marked numerator/denominator explicit
  fields as future expectations unless already represented by current layer
  semantics, and clarified that risk/operational exclusion is a required review
  expectation with incomplete current executable enforcement.
- Checks run: Pending.
- Reviewer notes: M007 needed clearer separation between current fixture
  coverage and future enforcement, softer physical-probability rejection
  language, and explicit remaining enforcement gaps.
- Decision: ACCEPT if corrected.
- Next proposed milestone: M008.

### M007 Revision Check Addendum

- Milestone id: M007 revision check.
- Roadmap item: 2. Hazard-map semantics and interpretation guide.
- Hypothesis/objective: Record targeted markdown-only verification for the
  M007 revision.
- Files intended to change:
  `docs/hazard_map_semantics.md`,
  `docs/agent_work_log.md`
- Implementation summary: Recorded completion of the requested targeted check.
- Checks run:
  `git diff --check -- docs/hazard_map_semantics.md docs/agent_work_log.md`
- Reviewer notes: Current-vs-future coverage wording was corrected. Remaining
  executable-enforcement gaps are a future milestone candidate.
- Decision: ACCEPT.
- Next proposed milestone: M008.

### M008

- Milestone id: M008.
- Roadmap item: 3. Pilot GIS/QGIS package and raster semantics.
- Hypothesis/objective: Define local pilot GIS/QGIS package contents and
  geospatial metadata expectations without adding production packaging code.
- Files intended to change:
  `docs/pilot_gis_package.md`,
  `docs/hazard_layers.md`,
  `docs/agent_work_log.md`
- Implementation summary: Created a pilot GIS package outline covering local
  review scope, required GeoTIFF/CSV/ASCII parity outputs, manifests,
  source-zone metadata or vector sidecars, terrain metadata, visual QA notes,
  EPSG:2056/LN02 expectations, affine/geotransform, cell size, extent, nodata,
  row order/north-up interpretation, checksums/provenance, explicit
  DEM-derived grid requirements for real pilots, vertical-datum sidecar
  limitations, and deferred QGZ/GeoPackage/styles/COG/tiling work. Added a
  short discoverability cross-reference from `docs/hazard_layers.md`.
- Checks run: Pending.
- Reviewer notes: Docs-only scope; no scripts, tests, production GIS packaging,
  COG claims, operational map claims, private geodata, or risk modelling.
- Decision: Pending.
- Next proposed milestone: M009.

### M008 Check Addendum

- Milestone id: M008 check.
- Roadmap item: 3. Pilot GIS/QGIS package and raster semantics.
- Hypothesis/objective: Record targeted markdown-only verification for the
  M008 docs-only scope change.
- Files intended to change:
  `docs/pilot_gis_package.md`,
  `docs/hazard_layers.md`,
  `docs/agent_work_log.md`
- Implementation summary: Recorded completion of the requested targeted check.
- Checks run:
  `git diff --check -- docs/pilot_gis_package.md docs/hazard_layers.md docs/agent_work_log.md`
- Reviewer notes: Check covers whitespace/errors in the intended changed files.
- Decision: ACCEPT.
- Next proposed milestone: M009.

### M008 Revision Note

- Milestone id: M008 revision.
- Roadmap item: 3. Pilot GIS/QGIS package and raster semantics.
- Hypothesis/objective: Tighten pilot GIS wording to avoid production-package
  implication and make real-site CRS/grid requirements mandatory.
- Files intended to change:
  `docs/pilot_gis_package.md`,
  `docs/agent_work_log.md`
- Implementation summary: Renamed required contents to required diagnostic
  review contents, changed Swiss real-site CRS/geodata wording from `should
  record` to `must record`, and changed real pilot explicit-grid wording from
  `should use` to `must use` explicit DEM-derived grid arguments.
- Checks run: Pending.
- Reviewer notes: M008 needed clearer diagnostic-review framing and mandatory
  real-site CRS/geodata and explicit-grid language.
- Decision: ACCEPT if corrected.
- Next proposed milestone: M009.

### M008 Revision Check Addendum

- Milestone id: M008 revision check.
- Roadmap item: 3. Pilot GIS/QGIS package and raster semantics.
- Hypothesis/objective: Record targeted markdown-only verification for the
  M008 revision.
- Files intended to change:
  `docs/pilot_gis_package.md`,
  `docs/agent_work_log.md`
- Implementation summary: Recorded completion of the requested targeted check.
- Checks run:
  `git diff --check -- docs/pilot_gis_package.md docs/agent_work_log.md`
- Reviewer notes: Diagnostic-review wording and mandatory CRS/grid findings
  were addressed.
- Decision: ACCEPT.
- Next proposed milestone: M009.

### M009

- Milestone id: M009.
- Roadmap item: 3. Pilot GIS/QGIS package and raster semantics.
- Hypothesis/objective: Define raster-layer semantics for local pilot GIS/QGIS
  review without adding code or tests.
- Files intended to change:
  `docs/pilot_gis_package.md`,
  `docs/agent_work_log.md`
- Implementation summary: Added raster review semantics for reach
  probability/fraction, deposition density, maximum kinetic energy, maximum
  jump height, significant-impact density/event-location distribution,
  threshold exceedance layers, probability standard-error/convergence
  diagnostics, weighted conditional layers, nodata versus valid zero, units,
  source table types, and annualized/risk exclusions, with a cross-reference to
  `docs/hazard_map_semantics.md`.
- Checks run: Pending.
- Reviewer notes: Docs-only scope; no code, tests, operational map claims,
  annual-frequency claims, private geodata, or risk modelling.
- Decision: Pending.
- Next proposed milestone: M010.

### M009 Check Addendum

- Milestone id: M009 check.
- Roadmap item: 3. Pilot GIS/QGIS package and raster semantics.
- Hypothesis/objective: Record targeted markdown-only verification for the
  M009 docs-only scope change.
- Files intended to change:
  `docs/pilot_gis_package.md`,
  `docs/agent_work_log.md`
- Implementation summary: Recorded completion of the requested targeted check.
- Checks run:
  `git diff --check -- docs/pilot_gis_package.md docs/agent_work_log.md`
- Reviewer notes: Check covers whitespace/errors in the intended changed files.
- Decision: ACCEPT.
- Next proposed milestone: M010.

### M009 Revision Note

- Milestone id: M009 revision.
- Roadmap item: 3. Pilot GIS/QGIS package and raster semantics.
- Hypothesis/objective: Tighten raster-layer semantics for denominators,
  source inputs, units, and significant-impact density wording.
- Files intended to change:
  `docs/pilot_gis_package.md`,
  `docs/hazard_layers.md`,
  `docs/agent_work_log.md`
- Implementation summary: Updated reach to use supplied trajectory count with
  at-most-once-per-trajectory cell counting, made deposition density a
  dimensionless fraction of supplied deposition rows or points, removed
  impact-adjacent wording from maximum kinetic energy, added explicit source
  input mappings for trajectory CSVs, ensemble deposition CSV, impact-event
  CSV/Parquet, and `trajectory_metadata_table_v1`, and corrected
  `significant_impact_density` in `docs/hazard_layers.md` to fraction of
  significant impact events per cell.
- Checks run: Pending.
- Reviewer notes: M009 needed stricter denominator and source-table language
  and a correction to significant-impact density wording.
- Decision: ACCEPT if corrected.
- Next proposed milestone: M010.

### M009 Revision Check Addendum

- Milestone id: M009 revision check.
- Roadmap item: 3. Pilot GIS/QGIS package and raster semantics.
- Hypothesis/objective: Record targeted markdown-only verification for the
  M009 revision.
- Files intended to change:
  `docs/pilot_gis_package.md`,
  `docs/hazard_layers.md`,
  `docs/agent_work_log.md`
- Implementation summary: Recorded completion of the requested targeted check.
- Checks run:
  `git diff --check -- docs/pilot_gis_package.md docs/hazard_layers.md docs/agent_work_log.md`
- Reviewer notes: Denominator, source-input, unit, and significant-impact
  density findings were addressed.
- Decision: ACCEPT.
- Next proposed milestone: M010.

### M010

- Milestone id: M010.
- Roadmap item: 3. Pilot GIS/QGIS package and raster semantics.
- Hypothesis/objective: Define QGIS visual QA checklist and local diagnostic
  package acceptance gate without adding code, tests, or production packaging.
- Files intended to change:
  `docs/pilot_gis_package.md`,
  `docs/agent_work_log.md`
- Implementation summary: Added a `QGIS Visual QA And Acceptance Gate` section
  covering DEM/hillshade, release-zone sidecar, share-safe observed deposition
  points, hazard rasters, manifests, CRS/project CRS EPSG:2056, LN02
  sidecars, grid alignment, nodata versus zero styling, layer semantic labels,
  no annual/risk/operational styling, artifact references, QA statuses
  (`pass`, `no-go`, `inconclusive`, `not-run`), and local diagnostic acceptance
  boundaries with no QGZ, COG, production, operational, or risk claim.
- Checks run: Pending.
- Reviewer notes: Docs-only scope; no code, tests, QGZ/COG packaging,
  production map claims, operational validation claims, private geodata, or risk
  modelling.
- Decision: Pending.
- Next proposed milestone: M011.

### M010 Check Addendum

- Milestone id: M010 check.
- Roadmap item: 3. Pilot GIS/QGIS package and raster semantics.
- Hypothesis/objective: Record targeted markdown-only verification for the
  M010 docs-only scope change.
- Files intended to change:
  `docs/pilot_gis_package.md`,
  `docs/agent_work_log.md`
- Implementation summary: Recorded completion of the requested targeted check.
- Checks run:
  `git diff --check -- docs/pilot_gis_package.md docs/agent_work_log.md`
- Reviewer notes: Check covers whitespace/errors in the intended changed files.
- Decision: ACCEPT.
- Next proposed milestone: M011.

### M010 Revision Note

- Milestone id: M010 revision.
- Roadmap item: 3. Pilot GIS/QGIS package and raster semantics.
- Hypothesis/objective: Tighten visual QA acceptance semantics and update the
  pilot GIS package status to reflect M008-M010 content.
- Files intended to change:
  `docs/pilot_gis_package.md`,
  `docs/agent_work_log.md`
- Implementation summary: Updated the status line to cover package contents,
  raster semantics, and visual QA gate; tightened acceptance so core CRS/grid
  metadata, semantic labels, nodata handling, provenance, and required visual QA
  evidence must be `pass`; and limited non-blocking `inconclusive` status to
  optional or non-core artifacts that do not affect the diagnostic question.
- Checks run:
  `git diff --check -- docs/pilot_gis_package.md docs/agent_work_log.md`
- Reviewer notes: GIS reviewer accepted M010; scientific reviewer requested a
  stricter acceptance gate and status update.
- Decision: ACCEPT if the targeted check passes.
- Next proposed milestone: M011.

### M010 Acceptance Addendum

- Milestone id: M010 acceptance.
- Roadmap item: 3. Pilot GIS/QGIS package and raster semantics.
- Hypothesis/objective: Record final acceptance after targeted verification.
- Files intended to change: `docs/agent_work_log.md`
- Implementation summary: Recorded that the targeted check passed and both
  reviewer concerns were addressed.
- Checks run:
  `git diff --check -- docs/pilot_gis_package.md docs/agent_work_log.md`
  passed.
- Reviewer notes: GIS reviewer accepted; scientific revision tightened core
  non-waivable acceptance and updated the status line.
- Decision: ACCEPT.
- Next proposed milestone: M011.

### M011

- Milestone id: M011.
- Roadmap item: 4. Source-zone and block-scenario semantics v1.
- Hypothesis/objective: Define source-zone representation, release-cell policy,
  provenance, and exclusion rules using existing source-zone metadata and
  `trajectory_metadata_table_v1` semantics, without adding block-scenario
  semantics yet.
- Files intended to change:
  `docs/probabilistic_scenario_model_design.md`,
  `docs/validation_data_schema.md`,
  `docs/agent_work_log.md`
- Implementation summary: Added a source-zone semantics v1 subsection covering
  polygon/multipolygon design intent, current small-polygon fixture/parser
  limitation, stable `source_zone_id`, deterministic `release_cell_id`,
  release sampling as numerical design rather than physical probability,
  CRS/vertical-datum/provenance/source/license requirements, and exclusions for
  national derivation, slope/geology/inventory release algorithms, annual
  source frequency, physical source probability, swisstopo-as-validation, and
  operational source-zone approval. Added a schema cross-reference near
  release-zone metadata.
- Checks run:
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest tests/test_source_scenario_policy.py tests/test_public_real_site_geodata_manifest.py` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/validate_source_scenario_policy.py validation/policies/tschamut_public_source_scenario_policy_v1.yaml` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/check_repo_consistency.py` passed.
  `git diff --check` passed.
  `scripts/git-hooks/pre-commit` passed.
- Reviewer notes: Local self-review against Priority 2 found no blocker. The
  policy is ready as a conditional source/scenario input contract, but source
  metadata sidecars, DEM sensitivity, and a frozen gate run remain later
  priorities.
- Decision: ACCEPT; Priority 2 done at the selected-domain policy level.
- Next proposed milestone: M012.

### M011 Revision Note

- Milestone id: M011 revision.
- Roadmap item: 4. Source-zone and block-scenario semantics v1.
- Hypothesis/objective: Correct source-zone v1 schema wording so current
  support is polygon-only and release-zone sidecars are not conflated with
  `source_zone_metadata_v1`.
- Files intended to change:
  `docs/probabilistic_scenario_model_design.md`,
  `docs/validation_data_schema.md`,
  `docs/agent_work_log.md`
- Implementation summary: Revised source-zone geometry wording to state that
  current `source_zone_metadata_v1` and release-zone parser support is
  polygon-only, with multipolygon remaining future design intent and not parsed
  today. Clarified that `release_zone.metadata_path` is a separate
  schema-version-1 deterministic release-generation sidecar, while
  `source_zone_metadata_v1` belongs to the probabilistic metadata contract for
  source-zone/scenario joins; both preserve stable identity and provenance but
  are not the same schema.
- Checks run:
  `git diff --check -- docs/probabilistic_scenario_model_design.md docs/validation_data_schema.md docs/agent_work_log.md`
- Reviewer notes: Scientific reviewer accepted M011; roadmap/schema reviewer
  requested revision for polygon-only support and schema separation.
- Decision: ACCEPT if the targeted check passes.
- Next proposed milestone: M012.

### M011 Acceptance Addendum

- Milestone id: M011 acceptance.
- Roadmap item: 4. Source-zone and block-scenario semantics v1.
- Hypothesis/objective: Record final acceptance after targeted verification.
- Files intended to change: `docs/agent_work_log.md`
- Implementation summary: Recorded that the targeted check passed after
  revision and reviewer concerns were addressed.
- Checks run:
  `git diff --check -- docs/probabilistic_scenario_model_design.md docs/validation_data_schema.md docs/agent_work_log.md`
  passed.
- Reviewer notes: Scientific reviewer accepted; roadmap/schema reviewer
  concerns were addressed.
- Decision: ACCEPT.
- Next proposed milestone: M012.

### M012

- Milestone id: M012.
- Roadmap item: 4. Source-zone and block-scenario semantics v1.
- Hypothesis/objective: Define block-scenario metadata semantics v1 using
  existing `scenario_table_v1` and `trajectory_metadata_table_v1` fields without
  adding tests or code.
- Files intended to change:
  `docs/probabilistic_scenario_model_design.md`,
  `docs/validation_data_schema.md`,
  `docs/agent_work_log.md`
- Implementation summary: Added a block-scenario semantics v1 subsection
  covering stable `block_scenario_id`, block size/shape class labels,
  representative radius/mass/density metadata propagation, the current active
  case spherical-block physics boundary, inactive shape-dependent contact,
  `sampling_weight` as conditional sampling weight rather than physical
  block-population probability, inactive source/release probability and annual
  frequency fields, and exclusions for calibrated block-population
  distributions, fragmentation, shape-dependent contact, mid-trajectory
  block-size changes, and operational block-scenario approval. Added schema
  clarification that propagated block-scenario fields are additive Phase 1
  labels/weights and do not change default physics.
- Checks run: Pending.
- Reviewer notes: Pending.
- Decision: Pending.
- Next proposed milestone: M013.

### M012 Revision Note

- Milestone id: M012 revision.
- Roadmap item: 4. Source-zone and block-scenario semantics v1.
- Hypothesis/objective: Correct block-scenario numeric field semantics so
  scenario-table representative values are not described as current trajectory
  metadata numeric overrides.
- Files intended to change:
  `docs/probabilistic_scenario_model_design.md`,
  `docs/validation_data_schema.md`,
  `docs/agent_work_log.md`
- Implementation summary: Revised block-scenario semantics to state that
  `block_scenario_id`, `block_size_class`, `block_shape_class`, and
  `sampling_weight` are current additive propagated scenario labels/weights,
  while representative scenario numeric fields are schema-visible design and
  consistency fields that must match or be reconciled with active case block
  values before interpretation as simulated values. Clarified that current
  `trajectory_metadata_table_v1` numeric block columns report active simulated
  case block and passive shape values, not scenario-row numeric overrides.
- Checks run:
  `git diff --check -- docs/probabilistic_scenario_model_design.md docs/validation_data_schema.md docs/agent_work_log.md`
- Reviewer notes: Scientific reviewer accepted M012; implementation/schema
  reviewer requested revision for current trajectory metadata numeric block
  value provenance.
- Decision: ACCEPT if the targeted check passes.
- Next proposed milestone: M013.

### M012 Acceptance Addendum

- Milestone id: M012 acceptance.
- Roadmap item: 4. Source-zone and block-scenario semantics v1.
- Hypothesis/objective: Record final acceptance after targeted verification.
- Files intended to change: `docs/agent_work_log.md`
- Implementation summary: Recorded that the targeted check passed after
  revision and reviewer concerns were addressed.
- Checks run:
  `git diff --check -- docs/probabilistic_scenario_model_design.md docs/validation_data_schema.md docs/agent_work_log.md`
  passed.
- Reviewer notes: Scientific reviewer accepted; implementation/schema reviewer
  concern was addressed.
- Decision: ACCEPT.
- Next proposed milestone: M013.

### M013

- Milestone id: M013.
- Roadmap item: 4. Source-zone and block-scenario semantics v1.
- Hypothesis/objective: Define consistency checks for scenario weighting,
  calibration/validation separation, and deterministic seeding without adding
  code.
- Files intended to change:
  `docs/probabilistic_scenario_model_design.md`,
  `docs/validation_data_schema.md`,
  `docs/agent_work_log.md`
- Implementation summary: Added Scenario Consistency Checks V1 covering stable
  joins across source-zone metadata, scenario tables, trajectory metadata, and
  manifests; finite nonnegative sampling weights and positive filtered totals;
  denominator and normalization recording; calibration/validation separation;
  swisstopo inputs as operational geodata rather than validation evidence;
  deterministic seeds, trajectory ids, release-cell ids, and order-independent
  reducers; deferred physical probability and annual frequency evidence/schema
  requirements; and physics-boundary failures for block numeric overrides and
  shape labels. Added a validation schema cross-reference noting which checks
  are currently parser/test enforced and which remain documented review gates.
- Checks run: Pending.
- Reviewer notes: Pending.
- Decision: Pending.
- Next proposed milestone: M014.

### M013 Revision Note

- Milestone id: M013 revision.
- Roadmap item: 4. Source-zone and block-scenario semantics v1.
- Hypothesis/objective: Correct M013 consistency-check wording so current
  parser/test-enforced checks are distinguished from documented review gates and
  future executor/reducer expectations.
- Files intended to change:
  `docs/probabilistic_scenario_model_design.md`,
  `docs/agent_work_log.md`
- Implementation summary: Split Scenario Consistency Checks V1 into
  parser/test-enforced checks and documented review gates/future enforcement
  targets. Clarified that deterministic seeding and reducer-order independence
  are documented design/review expectations for future executors and reducers,
  not current parser/test enforcement.
- Checks run:
  `git diff --check -- docs/probabilistic_scenario_model_design.md docs/validation_data_schema.md docs/agent_work_log.md`
- Reviewer notes: Reviewer requested REVISE because the first M013 wording
  implied deterministic seed review and reducer-order independence were already
  executable enforcement.
- Decision: ACCEPT if the targeted check passes.
- Next proposed milestone: M014.

### M013 Acceptance Addendum

- Milestone id: M013 acceptance.
- Roadmap item: 4. Source-zone and block-scenario semantics v1.
- Hypothesis/objective: Record final acceptance after targeted verification.
- Files intended to change: `docs/agent_work_log.md`
- Implementation summary: Recorded that the targeted check passed after
  revision and reviewer concern was addressed.
- Checks run:
  `git diff --check -- docs/probabilistic_scenario_model_design.md docs/validation_data_schema.md docs/agent_work_log.md`
  passed.
- Reviewer notes: Concern was addressed by splitting parser/test-enforced checks
  from documented review gates.
- Decision: ACCEPT.
- Next proposed milestone: M014.

### M014

- Milestone id: M014.
- Roadmap item: 5. DEM and terrain-representation sensitivity benchmark.
- Hypothesis/objective: Add an initial documentation-only benchmark design for
  DEM and terrain-representation sensitivity without running private data or
  generating outputs.
- Files intended to change:
  `docs/dem_terrain_sensitivity_benchmark.md`,
  `docs/benchmark_catalog.md`,
  `docs/agent_work_log.md`
- Implementation summary: Created a DEM/terrain sensitivity benchmark design
  covering purpose, compared terrain representations, invariants, required
  metadata, runout/deposition and hazard-layer metrics, visual QA, timing and
  output-volume context, acceptance gates, and future M015/M016 report
  sections. Added a Level 5 benchmark-catalog cross-reference that marks the
  design as documentation-only and not part of `validate --all`.
- Checks run: Pending.
- Reviewer notes: Pending.
- Decision: Pending.
- Next proposed milestone: M015.

### M014 Revision Note

- Milestone id: M014 revision.
- Roadmap item: 5. DEM and terrain-representation sensitivity benchmark.
- Hypothesis/objective: Make the DEM/terrain sensitivity design concrete enough
  for future execution while staying documentation-only.
- Files intended to change:
  `docs/dem_terrain_sensitivity_benchmark.md`,
  `docs/agent_work_log.md`
- Implementation summary: Added a concrete comparison matrix for
  synthetic/control, public Tschamut proxy, native private swissALTI3D,
  coarsened resolutions, interpolation/resampling methods, smoothing variants,
  cliff/nodata variants, and terrain-class/raster alignment variants. Added
  LV95/EPSG:2056 and LN02 requirements or recorded transforms for private
  Tschamut/swissALTI3D variants; ESRI ASCII `xllcorner`/`yllcorner`, north/top
  first row, and cell-center conventions; predeclared resampling/coarsening and
  nodata behavior; terrain-class variant limits; diagnostic-only observation
  comparison caveats; a minimum dry-run/real-site recipe; ignored output roots;
  command/report placeholders; paired output modes; and gate statuses.
- Checks run:
  Original targeted check:
  `git diff --check -- docs/dem_terrain_sensitivity_benchmark.md docs/benchmark_catalog.md docs/agent_work_log.md`
  passed.
  Revision targeted check:
  `git diff --check -- docs/dem_terrain_sensitivity_benchmark.md docs/agent_work_log.md`
- Reviewer notes: Both reviewers requested revision for concrete executable
  comparison design, metadata/nodata specifics, terrain-class boundaries,
  diagnostic observation language, and a minimum recipe.
- Decision: ACCEPT if the revision targeted check passes.
- Next proposed milestone: M015.

### M014 Acceptance Addendum

- Milestone id: M014 acceptance.
- Roadmap item: 5. DEM and terrain-representation sensitivity benchmark.
- Hypothesis/objective: Record final acceptance after targeted verification.
- Files intended to change: `docs/agent_work_log.md`
- Implementation summary: Recorded that the revision targeted check passed and
  both reviewers' concerns were addressed.
- Checks run:
  `git diff --check -- docs/dem_terrain_sensitivity_benchmark.md docs/agent_work_log.md`
  passed.
- Reviewer notes: Both reviewers' concerns were addressed.
- Decision: ACCEPT.
- Next proposed milestone: M015.

### M015

- Milestone id: M015.
- Roadmap item: 2. Hazard-map semantics and interpretation guide.
- Hypothesis/objective: Complete the current semantics guide without advancing
  physical-probability, annual-frequency, or other roadmap items.
- Files intended to change:
  `docs/hazard_map_semantics.md`,
  `docs/hazard_layers.md`,
  `docs/probabilistic_hazard_phase1_closure.md`,
  `docs/probabilistic_scenario_model_design.md`,
  `docs/agent_work_log.md`
- Implementation summary: Replaced placeholder denominator/conditioning text
  with current unweighted diagnostic and `sampling_weighted_conditional` rules,
  kept physical-probability and annual-frequency labels explicitly inactive,
  tightened executable-check references to current Rust/Python tests and
  fixtures, and updated cross-links to the semantics guide.
- Checks run:
  `git diff --check -- docs/hazard_map_semantics.md docs/hazard_layers.md docs/probabilistic_hazard_phase1_closure.md docs/probabilistic_scenario_model_design.md docs/agent_work_log.md`
  passed.
- Reviewer notes: Pending.
- Decision: Pending reviewer.
- Next proposed milestone: Pending roadmap selection.

### M016 Check Addendum

- Milestone id: M016 check.
- Roadmap item: 3. Pilot GIS/QGIS package and raster semantics.
- Files intended to change: `docs/agent_work_log.md`
- Checks run:
  Targeted diff whitespace check passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest tests.test_hazard_layers.HazardLayerTests.test_geotiff_export_preserves_values_grid_and_crs_metadata tests.test_hazard_layers.HazardLayerTests.test_cog_export_is_explicitly_deferred`
  passed.
- Reviewer notes: Pending.
- Decision: Pending reviewer.

### M016 Acceptance Addendum

- Milestone id: M016 acceptance.
- Roadmap item: 3. Pilot GIS/QGIS package and raster semantics.
- Files intended to change: `docs/agent_work_log.md`
- Implementation summary: Read-only reviewer accepted roadmap item 3 against
  the Definition of Done; stop after one item as requested.
- Reviewer notes: Accepted by read-only reviewer.
- Decision: ACCEPT; item 3 done for current Definition of Done.
- Next proposed milestone: Stop after one item as requested.

### M016 Final Status Note

- Despite append ordering, final item 3 status is complete.
- Targeted checks passed.
- Read-only reviewer accepted against the Definition of Done.
- Decision: ACCEPT.
- Stop after one item as requested.

### M015 Acceptance Addendum

- Milestone id: M015 acceptance.
- Roadmap item: 2. Hazard-map semantics and interpretation guide.
- Hypothesis/objective: Record read-only reviewer acceptance against the
  current Definition of Done.
- Files intended to change: `docs/agent_work_log.md`
- Implementation summary: Selected roadmap item 2 was accepted by the
  read-only reviewer; stop after one item as requested.
- Checks run:
  `cargo test --test probabilistic_phase1` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest tests.test_hazard_layers`
  passed.
  Targeted `git diff --check` passed.
- Reviewer notes: Read-only reviewer accepted item 2 against the Definition of
  Done.
- Decision: ACCEPT; item 2 done for current Definition of Done.
- Next proposed milestone: Stop after one item as requested.

### M016

- Milestone id: M016.
- Roadmap item: 3. Pilot GIS/QGIS package and raster semantics.
- Hypothesis/objective: Complete the current pilot GIS/QGIS package contract
  without advancing production COG or other roadmap work.
- Files intended to change:
  `docs/pilot_gis_package.md`,
  `docs/hazard_layers.md`,
  `docs/agent_work_log.md`
- Implementation summary: Documented debug/review GeoTIFF, local QGIS pilot
  package, and deferred production COG/package distinctions; made
  CRS/transform/nodata/grid-alignment semantics explicit; cited current
  GeoTIFF parity and COG rejection tests; updated the hazard-layer cross-link.
- Checks run: Pending targeted diff whitespace check.
- Reviewer notes: Pending.
- Decision: Pending reviewer.
- Next proposed milestone: Pending roadmap selection.

### M016 Final Status Note 2

- Final item 3 status after all M016 entries: targeted checks passed, read-only
  reviewer accepted against the Definition of Done, decision ACCEPT, and work
  stopped after one item as requested.

### M017

- Milestone id: M017.
- Roadmap item: 4. Source-zone and block-scenario semantics v1.
- Hypothesis/objective: Complete v1 source-zone/block-scenario semantics
  documentation without advancing physical/annual probability work.
- Files intended to change:
  `docs/probabilistic_scenario_model_design.md`,
  `docs/validation_data_schema.md`,
  `docs/agent_work_log.md`
- Implementation summary: Added source-zone derivation evidence levels,
  allowed/disallowed claims, current executable checks and examples, and a
  schema cross-link to the v1 interpretation contract.
- Checks run: Pending targeted diff whitespace check.
- Reviewer notes: Pending.
- Decision: Pending reviewer.
- Next proposed milestone: Pending roadmap selection.

### M017 Acceptance Addendum

- Milestone id: M017 acceptance.
- Roadmap item: 4. Source-zone and block-scenario semantics v1.
- Hypothesis/objective: Record completion against the current Definition of
  Done without advancing physical or annual probability semantics.
- Files intended to change: `docs/agent_work_log.md`
- Implementation summary: Targeted checks passed and a read-only reviewer
  accepted the source-zone/block-scenario v1 documentation, examples,
  unsupported-probability boundaries, deterministic trajectory-metadata joins,
  and source-zone derivation evidence levels.
- Checks run:
  `git diff --check -- docs/probabilistic_scenario_model_design.md docs/validation_data_schema.md docs/agent_work_log.md` passed.
  `cargo test --test probabilistic_phase1` passed.
  `cargo test --test config_io_terrain probabilistic` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/check_repo_consistency.py` passed.
- Reviewer notes: Read-only reviewer accepted item 4 against all Definition of
  Done bullets with no blocking gaps.
- Decision: ACCEPT; item 4 done for current Definition of Done.
- Next proposed milestone: Stop after one item as requested.

### M018

- Milestone id: M018.
- Roadmap item: 5. DEM and terrain-representation sensitivity benchmark.
- Hypothesis/objective: Complete one high-value incomplete roadmap item by
  turning the DEM sensitivity scaffold into a CI-safe dry-runnable fixture.
- Files changed:
  `scripts/run_dem_terrain_sensitivity.py`,
  `tests/test_dem_terrain_sensitivity.py`,
  `docs/dem_terrain_sensitivity_benchmark.md`,
  `docs/benchmark_catalog.md`,
  `docs/README.md`,
  `docs/repository_scientific_roadmap_review.md`.
- Implementation summary: Added a deterministic DEM sensitivity dry run using
  the tiny checked-in swissALTI3D-style DEM fixture. The script writes baseline,
  3x3-smoothed, and 2x2 coarsened/reexpanded ESRI ASCII variants to a
  user-provided output directory, emits JSON elevation/slope-proxy/nodata
  comparison diagnostics, and writes a Markdown report with inventory,
  invariants, command log, metric table, gates, limitations, and a no-tuning
  warning.
- Checks run:
  `python3 -m unittest tests/test_dem_terrain_sensitivity.py` passed.
  `python3 scripts/run_dem_terrain_sensitivity.py --output-dir "$(mktemp -d)"`
  passed.
  `python3 scripts/check_repo_consistency.py` passed.
- Reviewer notes: Read-only reviewer accepted Item 5 against all Definition of
  Done bullets. Minor workspace concern remains: duplicate untracked
  `docs/* 2.md` files are intentionally left unstaged because they pre-existed
  this item.
- Decision: ACCEPT; item 5 done for current Definition of Done.
- Next proposed milestone: Stop after one item as requested.

### M019

- Milestone id: M019.
- Roadmap item: Priority 1. Prepare one public real-site swisstopo pilot
  package.
- Hypothesis/objective: Complete the highest-priority refreshed-roadmap item
  by selecting one concrete public Swiss pilot domain and making its geodata
  package reproducible from public downloads without committing raw or large
  processed files.
- Files changed:
  `.gitignore`,
  `data/processed/swisstopo/tschamut_public_pilot_manifest.yaml`,
  `data/processed/swisstopo/README.md`,
  `docs/public_real_site_geodata_preparation.md`,
  `docs/swisstopo_data_strategy.md`,
  `docs/real_case_intensity_frequency_implementation_roadmap.md`,
  `docs/next_development_targets.md`,
  `scripts/validate_public_real_site_geodata_manifest.py`,
  `scripts/check_repo_consistency.py`,
  `tests/test_public_real_site_geodata_manifest.py`,
  `docs/agent_work_log.md`.
- Implementation summary: Added a selected-domain public Tschamut pilot
  manifest tied to swissALTI3D tile `2696-1167`, EPSG:2056/LN02, ignored raw
  and processed paths, crop extent, 2 m cell size, nodata, source and processed
  SHA-256 digests, and the deterministic preparation command using
  `scripts/prepare_tschamut_public_benchmark.py`. Tightened the geodata
  manifest validator so selected manifests require concrete domain names,
  source tile provenance, product version/date, processed-output metadata,
  preprocessing commands, and valid checksums.
- Checks run:
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest tests/test_public_real_site_geodata_manifest.py` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest tests/test_public_real_site_geodata_manifest.py tests/test_public_real_site_conditional_pilot_run.py tests/test_source_scenario_policy.py` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/validate_public_real_site_geodata_manifest.py data/processed/swisstopo/tschamut_public_pilot_manifest.yaml` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/check_repo_consistency.py` passed.
  `git diff --check` passed.
  `scripts/git-hooks/pre-commit` passed.
- Reviewer notes: Local self-review against Priority 1 Definition of Done
  found no remaining blocker; local execution still depends on public downloads
  or manually preplaced ignored raw files.
- Decision: ACCEPT; Priority 1 done at the share-safe selected-domain package
  level.
- Next proposed milestone: Stop after Priority 1 as requested.

### M020

- Milestone id: M020.
- Roadmap item: Priority 2. Apply a domain-specific source-zone and
  block-scenario policy.
- Hypothesis/objective: Complete the selected Tschamut public pilot
  source/scenario policy without adding annual frequency, physical probability,
  risk, exposure, vulnerability, or simulator behavior changes.
- Files changed:
  `data/processed/swisstopo/tschamut_public_pilot_manifest.yaml`,
  `validation/policies/tschamut_public_source_scenario_policy_v1.yaml`,
  `scripts/validate_source_scenario_policy.py`,
  `scripts/check_repo_consistency.py`,
  `tests/test_source_scenario_policy.py`,
  `docs/source_zone_block_scenario_policy_v1.md`,
  `docs/public_real_site_geodata_preparation.md`,
  `docs/real_case_intensity_frequency_implementation_roadmap.md`,
  `docs/next_development_targets.md`,
  `docs/agent_work_log.md`.
- Implementation summary: Added a selected Tschamut public source-zone and
  block-scenario policy with a Level 1 public-release bounding source zone,
  deterministic release-cell grid, stable release-cell ids, representative
  block scenarios, and conditional-only sampling weights. Extended the policy
  validator and tests to require prepared policy geometry, explicit release
  cells, finite nonnegative conditional weights, and absent physical/annual
  probability fields.
- Checks run: Pending.
- Reviewer notes: Pending.
- Decision: Pending.
- Next proposed milestone: Stop after Priority 2 as requested.

### M021

- Milestone id: M021.
- Roadmap item: Priority 3. Run DEM/terrain sensitivity on the selected
  domain.
- Hypothesis/objective: Complete the selected Tschamut public pilot
  DEM/terrain sensitivity step without simulator behavior changes, parameter
  tuning, annual frequency, physical probability, risk, exposure,
  vulnerability, or operational claims.
- Files changed:
  `data/processed/swisstopo/tschamut_public_pilot_manifest.yaml`,
  `scripts/run_dem_terrain_sensitivity.py`,
  `tests/test_dem_terrain_sensitivity.py`,
  `docs/dem_terrain_sensitivity_benchmark.md`,
  `docs/real_case_intensity_frequency_implementation_roadmap.md`,
  `docs/next_development_targets.md`,
  `docs/agent_work_log.md`.
- Implementation summary: Extended the DEM sensitivity dry-run script with a
  selected Tschamut pilot gate that validates the public geodata manifest and
  source/scenario policy, fixes the source zone, ten release cells, three block
  scenarios, conditional-only sampling semantics, and EPSG:2056/LN02 terrain
  metadata. In clean checkouts where the ignored processed DEM is absent, the
  command writes a share-safe `blocked_missing_processed_dem` no-go summary and
  report; after local public preparation, the same command runs the existing
  baseline, smoothing, and coarsening terrain-variant diagnostics on the
  selected DEM.
- Checks run:
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m py_compile scripts/run_dem_terrain_sensitivity.py` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest tests/test_dem_terrain_sensitivity.py` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/run_dem_terrain_sensitivity.py --pilot-manifest data/processed/swisstopo/tschamut_public_pilot_manifest.yaml --source-scenario-policy validation/policies/tschamut_public_source_scenario_policy_v1.yaml --allow-missing-source-dem --output-dir /tmp/rust_rockfall_tschamut_dem_sensitivity_priority3_check` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/validate_public_real_site_geodata_manifest.py data/processed/swisstopo/tschamut_public_pilot_manifest.yaml` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/validate_source_scenario_policy.py validation/policies/tschamut_public_source_scenario_policy_v1.yaml` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/check_repo_consistency.py` passed.
  `scripts/git-hooks/pre-commit` passed.
  `cargo fmt --check` passed.
  `cargo clippy --all-targets --all-features -- -D warnings` passed.
  `cargo test` passed.
  `cargo run -- verify --all` passed.
  `cargo run -- validate --all` passed.
  `git diff --check` passed.
- Reviewer notes: No raw swisstopo geodata or generated sensitivity outputs
  are committed; the no-go gate is a reproducibility blocker, not a model
  result.
- Decision: ACCEPT; Priority 3 done at the selected-domain gate level, with
  terrain-variant metrics blocked only by the intentionally ignored processed
  DEM being absent from a clean checkout.
- Next proposed milestone: Stop after Priority 3 as requested.

### M022

- Milestone id: M022.
- Roadmap item: Priority 4. Execute the small frozen conditional pilot gate
  run.
- Hypothesis/objective: Complete the selected Tschamut public pilot gate as an
  executable no-go run-freeze and report, without simulator behavior changes,
  parameter tuning, annual frequency, physical probability, risk, exposure,
  vulnerability, or operational claims.
- Files changed:
  `validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml`,
  `docs/tschamut_public_conditional_pilot_gate_report.md`,
  `scripts/validate_public_real_site_conditional_pilot_run.py`,
  `tests/test_public_real_site_conditional_pilot_run.py`,
  `scripts/check_repo_consistency.py`,
  `docs/real_case_intensity_frequency_implementation_roadmap.md`,
  `docs/next_development_targets.md`,
  `docs/validation_data_schema.md`,
  `docs/README.md`,
  `docs/agent_work_log.md`.
- Implementation summary: Added a selected Tschamut public conditional pilot
  run-freeze that validates and freezes the available geodata manifest,
  source/scenario policy, physics defaults, random seed, conditional
  thresholds, explicit EPSG:2056/LN02 grid, output roots, and output budget.
  The gate is classified `no-go` because the ignored processed public DEM and
  metadata are absent from a clean checkout. The report and validator record
  that no conditional curves, GIS artifacts, checksums, runtime/memory metrics,
  output-volume evidence, or model results exist yet.
- Checks run: Pending.
- Reviewer notes: The no-go command plan validates upstream inputs and records
  the DEM-sensitivity blocker only; it intentionally does not run trajectories
  or hazard-layer post-processing until the local public DEM blocker is
  resolved.
- Decision: Pending.
- Next proposed milestone: Stop after Priority 4 as requested.

### M023

- Milestone id: M023.
- Roadmap item: Priority 5. Produce/review real-pilot GIS/QGIS package.
- Hypothesis/objective: Complete the next highest-priority incomplete item by
  adding a share-safe validator and review record for the locally generated
  Tschamut pilot GIS package, without committing generated rasters or claiming
  manual QGIS acceptance.
- Files changed:
  `scripts/validate_pilot_gis_package.py`,
  `tests/test_pilot_gis_package_validator.py`,
  `docs/tschamut_public_pilot_gis_package_review.md`,
  `docs/pilot_gis_package.md`,
  `docs/real_case_intensity_frequency_implementation_roadmap.md`,
  `docs/next_development_targets.md`,
  `docs/agent_work_log.md`.
- Implementation summary: Added a standalone validator for
  `pilot_gis_package_manifest_v1` inventories. With `--require-real-site` and
  `--require-existing-files`, it checks generated file checksums, GeoTIFF/CSV/
  ESRI ASCII parity inventory, EPSG:2056/LN02/nodata/grid metadata from the
  hazard manifest, source-zone sidecar references through package context or
  map-package metadata, and unsupported annual/return-period/risk/operational
  claim boundaries. Added a Tschamut review note recording that the ignored
  local package has 16 GeoTIFFs, 16 CSV parity grids, and 16 ESRI ASCII parity
  grids, with automated package QA passing and manual QGIS visual QA still
  `not-run`.
- Checks run:
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest tests/test_pilot_gis_package_validator.py` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/validate_pilot_gis_package.py hazard/results/tschamut_public_pilot/gate_v1/tschamut_public_conditional_gate_v1_pilot_gis_package_manifest.json --require-real-site --require-existing-files --format json` passed locally against ignored generated outputs.
- Reviewer notes: No raw swisstopo geodata or generated hazard products are
  committed. The GIS package is accepted only at automated manifest/file QA
  level; manual QGIS inspection remains inconclusive/not-run and production
  COG/QGZ/GeoPackage work remains deferred.
- Decision: ACCEPT if final checks pass; Priority 5 done at the automated
  diagnostic-review level.
- Next proposed milestone: Stop after Priority 5 as requested.

### M024

- Milestone id: M024.
- Roadmap item: Priority 6. Measure local scaling and output-volume
  bottlenecks.
- Hypothesis/objective: Complete one share-safe local scaling step for the
  Tschamut public conditional pilot by summarizing existing ignored gate
  manifests, without changing physics, defaults, source policy, annual
  semantics, physical probability semantics, or operational claims.
- Files changed:
  `scripts/summarize_pilot_scaling.py`,
  `tests/test_pilot_scaling_summary.py`,
  `docs/tschamut_public_pilot_scaling_review.md`,
  `docs/performance_benchmarking.md`,
  `docs/real_case_intensity_frequency_implementation_roadmap.md`,
  `docs/next_development_targets.md`,
  `docs/agent_work_log.md`.
- Implementation summary: Added a manifest-driven Tschamut pilot scaling
  summarizer that reads the validation manifest, hazard manifest, optional
  GIS-package manifest, optional `/usr/bin/time` sidecars, and local ignored
  output tree sizes. It fails clearly when required ignored outputs are absent
  unless `--allow-missing` is supplied. The local review records validation and
  hazard wall times, row counts, file counts, byte counts, deterministic
  chunked reducer metadata, memory-sidecar status, and a no-default-change
  decision identifying conditional-curve and raster output volume as the next
  bottleneck before ensemble-size increase or orchestration.
- Checks run:
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest tests/test_pilot_scaling_summary.py tests/test_pilot_gis_package_validator.py tests/test_public_real_site_conditional_pilot_run.py` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/summarize_pilot_scaling.py --allow-missing --validation-manifest /tmp/missing_validation_manifest.json --hazard-manifest /tmp/missing_hazard_manifest.json --gis-package-manifest /tmp/missing_gis_manifest.json` passed and returned `blocked_missing_outputs`.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/summarize_pilot_scaling.py --validation-manifest validation/private/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_manifest.json --hazard-manifest hazard/results/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_manifest.json --gis-package-manifest hazard/results/tschamut_public_pilot/gate_v1/tschamut_public_conditional_gate_v1_pilot_gis_package_manifest.json --output-json hazard/results/tschamut_public_pilot/gate_v1/tschamut_public_conditional_gate_v1_scaling_summary.json --output-md docs/tschamut_public_pilot_scaling_review.md` passed locally against ignored generated outputs.
  `cargo fmt --check` passed.
  `cargo clippy --all-targets --all-features -- -D warnings` passed.
  `cargo test` passed.
  `cargo run -- verify --all` passed.
  `cargo run -- validate --all` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/check_repo_consistency.py` passed.
  `scripts/git-hooks/pre-commit` passed.
  `scripts/git-hooks/pre-push` passed.
- Reviewer notes: No raw swisstopo data, processed DEM, generated hazard
  rasters, conditional curve tables, or generated scaling JSON are committed.
  Memory peak is not claimed unless optional external time sidecars are
  supplied; the current review records that sidecars were not supplied.
- Decision: ACCEPT if final checks pass; Priority 6 done at the local
  manifest-summary level.
- Next proposed milestone: Stop after Priority 6 as requested.

### M025

- Milestone id: M025.
- Roadmap item: Target 1. Reconcile and regenerate selected pilot gate
  evidence.
- Hypothesis/objective: Resolve the refreshed roadmap evidence-consistency gap
  by making the selected Tschamut run-freeze, DEM-sensitivity report,
  conditional pilot report, GIS package review, and scaling review describe
  the same regenerated local ignored gate state.
- Files changed:
  `validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml`,
  `tests/test_public_real_site_conditional_pilot_run.py`,
  `docs/tschamut_public_conditional_pilot_gate_report.md`,
  `docs/tschamut_public_pilot_gis_package_review.md`,
  `docs/tschamut_public_pilot_scaling_review.md`,
  `docs/real_case_intensity_frequency_implementation_roadmap.md`,
  `docs/next_development_targets.md`,
  `docs/agent_work_log.md`.
- Implementation summary: Regenerated or verified the local ignored processed
  DEM sensitivity gate, frozen validation gate, conditional hazard layers, GIS
  package manifest, reducer chunk manifests, scaling summary, and external
  `/usr/bin/time` sidecars. Updated the committed selected run-freeze from a
  missing-DEM no-go state to `gate_run_completed` with `inconclusive` report
  classification, artifact paths, SHA-256 checksums, runtime, peak memory,
  file-count, byte-count, trajectory-count, release-cell-count, and explicit
  non-operational/conditional claim boundaries. Updated tests so the selected
  Tschamut run-freeze builds the full execution command plan while fixture
  coverage still exercises the no-go blocker plan.
- Checks run: Pending.
- Reviewer notes: No raw swisstopo data, processed DEM, generated validation
  outputs, generated hazard rasters, generated conditional curve tables,
  generated GIS package manifests, generated scaling JSON, or time sidecars
  are committed. The gate remains `inconclusive` because target-scale
  convergence and manual QGIS visual QA are not established.
- Decision: ACCEPT if final checks pass; Target 1 done at the reconciled local
  ignored-artifact level.
- Next proposed milestone: Stop after Target 1 as requested.

### M026

- Milestone id: M026.
- Roadmap item: Target 2. Run or classify manual QGIS visual QA for the
  selected package.
- Hypothesis/objective: Complete the next selected visual-QA gate with a
  share-safe, executable review record that does not pretend a QGIS pass was
  achieved in the non-GUI agent environment.
- Initial gap assessment: The selected package had passing automated
  manifest/file QA but still recorded manual QGIS visual QA as `not-run`.
  The local environment has no `qgis` executable, so a visual acceptance pass
  would be unsupported.
- Files changed:
  `scripts/validate_pilot_gis_visual_qa.py`,
  `tests/test_pilot_gis_visual_qa.py`,
  `validation/pilot_runs/tschamut_public_gis_visual_qa_v1.yaml`,
  `docs/tschamut_public_pilot_gis_package_review.md`,
  `docs/pilot_gis_package.md`,
  `docs/real_case_intensity_frequency_implementation_roadmap.md`,
  `docs/next_development_targets.md`,
  `docs/agent_work_log.md`.
- Implementation summary: Added a `pilot_gis_visual_qa_record_v1` validator
  and selected Tschamut review record. The record classifies manual GIS/QGIS
  visual QA as `inconclusive`, with automated CRS/LN02/label/claim-boundary
  checks passing and raster-grid alignment, nodata styling, and source-zone
  overlay remaining inconclusive because QGIS was unavailable and no visual
  screenshots or layer-list artifacts were produced. The validator rejects
  selected `not-run` records, pass records without QGIS evidence, missing core
  checklist items, and unqualified misleading current-product claims.
- Checks run: Pending.
- Reviewer notes: No raw swisstopo data, processed DEM, generated validation
  outputs, generated hazard rasters, screenshots, QGIS projects, GeoPackages,
  COGs, or generated package outputs are committed. This completes the visual
  QA gate only as an explicit `inconclusive` classification, not as visual
  acceptance.
- Decision: ACCEPT if final checks pass; Target 2 done at the share-safe
  checklist-classification level.
- Next proposed milestone: Scope forest and obstacle omission for Tschamut.

### M027

- Milestone id: M027.
- Roadmap item: Target 3. Scope forest and obstacle omission for Tschamut.
- Hypothesis/objective: Complete one share-safe interpretation gate that
  classifies whether omitted forest, roads, structures, channels, barriers, or
  visual-context layers limit the selected Tschamut conditional gate, without
  changing physics, defaults, or probability semantics.
- Initial gap assessment: The selected public geodata manifest still recorded
  forest/obstacle relevance as not scoped. The conditional gate used
  bare-earth swissALTI3D terrain and no reviewed local SWISSIMAGE, swissTLM3D,
  swissSURFACE3D/swissSURFACE3D Raster, or swissBUILDINGS3D context, so the
  omission needed an explicit interpretation classification before scale-up.
- Files changed:
  `scripts/validate_pilot_obstacle_scope.py`,
  `tests/test_pilot_obstacle_scope.py`,
  `validation/pilot_runs/tschamut_public_obstacle_scope_v1.yaml`,
  `docs/tschamut_public_obstacle_context_scope.md`,
  `data/processed/swisstopo/tschamut_public_pilot_manifest.yaml`,
  `docs/swisstopo_data_strategy.md`,
  `docs/tschamut_public_conditional_pilot_gate_report.md`,
  `docs/real_case_intensity_frequency_implementation_roadmap.md`,
  `docs/next_development_targets.md`,
  `docs/hazard_map_semantics.md`,
  `docs/README.md`,
  `docs/agent_work_log.md`.
- Implementation summary: Added a `pilot_obstacle_scope_v1` validator and a
  selected Tschamut scope record. The record classifies forest/obstacle
  omission as `limiting`, inventories six required context categories, records
  public context layers that still need local review, and states that
  restitution, roughness, terrain classes, stopping thresholds, and scenario
  weights must not be tuned to absorb omitted vegetation or constructed
  features. Updated current roadmap/report docs and the selected geodata
  manifest to reflect the scoped limitation.
- Checks run: Pending.
- Reviewer notes: No raw SWISSIMAGE, swissTLM3D, swissSURFACE3D,
  swissBUILDINGS3D, processed context crop, screenshots, obstacle layers,
  generated hazard products, risk/exposure layers, or obstacle physics are
  committed.
- Decision: ACCEPT if final checks pass; Target 3 done at the share-safe
  scoping-classification level.
- Next proposed milestone: Address the conditional-curve/raster output-volume
  bottleneck before increasing ensemble size.

### M028

- Milestone id: M028.
- Roadmap item: Target 4. Address conditional-curve/raster output-volume
  bottleneck.
- Hypothesis/objective: Add a no-default-change output-volume gate for the
  largest selected Tschamut local hazard artifact before any ensemble-size
  increase.
- Initial gap assessment: The selected scaling review identified
  `conditional_intensity_exceedance_curves` as the largest local hazard output
  at 117,305,412 bytes. The hazard builder could write the full per-cell curve
  table, but it lacked an explicit opt-in path for pre-scale runs that need
  threshold rasters and metadata summaries without committing to the large CSV
  table.
- Files changed:
  `scripts/build_hazard_layers.py`,
  `tests/test_hazard_layers.py`,
  `docs/performance_benchmarking.md`,
  `docs/tschamut_public_pilot_scaling_review.md`,
  `docs/scalability_and_data_formats_review.md`,
  `docs/real_case_intensity_frequency_implementation_roadmap.md`,
  `docs/next_development_targets.md`,
  `docs/agent_work_log.md`.
- Implementation summary: Added
  `scripts/build_hazard_layers.py --conditional-curve-export {full,summary-only}`.
  The default remains `full`. The `summary-only` mode preserves conditional
  exceedance rasters, curve metadata summaries, denominators, and non-annual
  semantics while omitting the large per-cell curve CSV table and its manifest
  output entry.
- Checks run:
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest tests.test_hazard_layers.HazardLayerTests.test_conditional_curve_summary_only_suppresses_large_curve_table tests.test_hazard_layers.HazardLayerTests.test_exceedance_layers_are_additive_and_manifested`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest discover -s tests -p 'test_*.py'`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/check_repo_consistency.py`;
  `cargo fmt --check`;
  `cargo clippy --all-targets --all-features -- -D warnings`;
  `cargo test`;
  `cargo run -- verify --all`;
  `cargo run -- validate --all`;
  `scripts/git-hooks/pre-commit`.
- Reviewer notes: No physics, defaults, source weights, annual frequency,
  physical probability, risk/exposure semantics, generated hazard products, or
  raw/processed swisstopo geodata are changed or committed.
- Decision: ACCEPT if final checks pass; Target 4 done for the largest
  curve-table output bottleneck. Raster-output optimization remains future
  work.
- Next proposed milestone: Increase ensemble size only if convergence,
  performance, and output-volume evidence justify it.

### M029

- Milestone id: M029.
- Roadmap item: Target 5. Increase ensemble size toward the target count.
- Hypothesis/objective: Complete the selected-domain ensemble-size decision
  without launching a larger ignored run or weakening claim boundaries. The
  acceptable completion path is a documented no-go if convergence, output,
  visual-QA, or interpretation preconditions are not met.
- Initial gap assessment: The small Tschamut conditional gate is reproducible,
  and conditional-curve output volume now has a summary-only control, but the
  repository still lacked an executable decision record stating whether an
  ensemble increase is authorized. Target-scale convergence is not established,
  manual GIS/QGIS visual QA is inconclusive, and forest/obstacle omission is
  limiting.
- Files changed:
  `scripts/validate_pilot_ensemble_feasibility.py`,
  `tests/test_pilot_ensemble_feasibility.py`,
  `validation/pilot_runs/tschamut_public_ensemble_feasibility_v1.yaml`,
  `docs/tschamut_public_ensemble_feasibility.md`,
  `scripts/check_repo_consistency.py`,
  `docs/real_case_intensity_frequency_implementation_roadmap.md`,
  `docs/next_development_targets.md`,
  `docs/README.md`,
  `docs/agent_work_log.md`.
- Implementation summary: Added a `pilot_ensemble_feasibility_v1` validator
  and selected Tschamut no-go record. The record blocks ensemble increase until
  target-scale convergence diagnostics, output-budget evidence with
  `--conditional-curve-export summary-only`, manual GIS/QGIS visual QA, and
  forest/obstacle context review are resolved. The validator rejects missing
  blockers, non-increasing trajectory counts, full curve-table export for the
  increase path, missing preconditions, and unqualified misleading claims.
- Checks run:
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest tests.test_pilot_ensemble_feasibility`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/validate_pilot_ensemble_feasibility.py validation/pilot_runs/tschamut_public_ensemble_feasibility_v1.yaml`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/check_repo_consistency.py`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest discover -s tests -p 'test_*.py'`;
  `cargo fmt --check`;
  `cargo clippy --all-targets --all-features -- -D warnings`;
  `cargo test`;
  `cargo run -- verify --all`;
  `cargo run -- validate --all`;
  `scripts/git-hooks/pre-commit`.
- Reviewer notes: No larger ensemble was executed or committed. No physics,
  defaults, source weights, annual frequency, physical probability,
  risk/exposure semantics, generated hazard products, or raw/processed
  swisstopo geodata are changed or committed.
- Decision: ACCEPT if final checks pass; Target 5 done as a selected-domain
  no-go feasibility gate.
- Next proposed milestone: Design physical/source-frequency semantics.

### M030

- Milestone id: M030.
- Roadmap item: Target 6. Complete fallible terrain/integrator API migration.
- Hypothesis/objective: Complete the compatibility-preserving fallible runtime
  guardrail so real DEM nodata or crop-edge failures propagate as structured
  errors without changing physics, defaults, or public validation outputs.
- Initial gap assessment: The fixed-step integrator used fallible top-level DEM
  queries but still delegated contact response and contact-motion work to
  helpers that used infallible terrain queries internally. The consistency
  script also lacked a guardrail against reintroducing those calls in the
  integrator.
- Files changed:
  `src/dynamics.rs`,
  `src/integrator.rs`,
  `tests/config_io_terrain.rs`,
  `scripts/check_repo_consistency.py`,
  `docs/architecture_boundaries.md`,
  `docs/model_design.md`,
  `docs/real_case_intensity_frequency_implementation_roadmap.md`,
  `docs/next_development_targets.md`,
  `docs/agent_work_log.md`.
- Implementation summary: Added fallible contact-response, contact-friction,
  and rotational contact-motion helpers in `src/dynamics.rs`; switched the
  fixed-step integrator to call those helpers and propagate `TerrainError`
  through `IntegrationError`; retained infallible wrappers as compatibility
  helpers with explicit panic messages. Added a strict DEM contact-response
  guardrail test and repository consistency checks that reject new infallible
  terrain/contact calls in `src/integrator.rs`.
- Checks run:
  `cargo fmt --check`;
  `cargo test strict_dem_`;
  `cargo clippy --all-targets --all-features -- -D warnings`;
  `cargo test`;
  `cargo run -- verify --all`;
  `cargo run -- validate --all`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest discover -s tests -p 'test_*.py'`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/check_repo_consistency.py`;
  `git diff --check`;
  `scripts/git-hooks/pre-commit`.
- Reviewer notes: No DEM interpolation numerics, contact physics, defaults,
  validation baselines, generated products, annual frequency, physical
  probability, risk/exposure semantics, or raw/processed swisstopo geodata are
  changed or committed. Strict DEM terrain failures remain workflow/input
  errors, not physical stopping states.
- Decision: ACCEPT if final checks pass; Target 6 done at the guardrail level.
- Next proposed milestone: Split one coherent validation or shape-contact
  concern by module boundary.

### M031

- Milestone id: M031.
- Roadmap item: Target 7. Split validation and experimental shape internals by
  concern.
- Hypothesis/objective: Complete the first behavior-preserving split from the
  large validation module by extracting one pure concern without changing
  schemas, outputs, validation baselines, physics, or public runtime behavior.
- Initial gap assessment: `src/validation.rs` still mixed case orchestration,
  output writing, manifests, observed-data metrics, and pure numeric helper
  functions in one large file. A full case-loader or exporter split would have
  high review risk, but pure metric-math helpers were a narrow, testable
  concern.
- Files changed:
  `src/validation.rs`,
  `src/validation/metric_math.rs`,
  `scripts/check_repo_consistency.py`,
  `docs/architecture_boundaries.md`,
  `docs/real_case_intensity_frequency_implementation_roadmap.md`,
  `docs/next_development_targets.md`,
  `docs/agent_work_log.md`.
- Implementation summary: Added a private `validation::metric_math` submodule
  for pure validation metric helpers (`mean`, `percentile`, distance/centroid,
  nearest-cloud, spread, and overlap functions), imported those helpers from
  `src/validation.rs`, and removed the duplicate definitions from the monolith.
  Added focused unit tests for percentile interpolation/clamping and cloud
  metric edge cases, plus a repository consistency guard that keeps the
  extracted helpers out of `src/validation.rs`.
- Checks run:
  `cargo fmt --check`;
  `cargo test validation::metric_math`;
  `cargo clippy --all-targets --all-features -- -D warnings`;
  `cargo test`;
  `cargo run -- verify --all`;
  `cargo run -- validate --all`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest discover -s tests -p 'test_*.py'`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/check_repo_consistency.py`;
  `git diff --check`;
  `scripts/git-hooks/pre-commit`.
- Reviewer notes: No physics, defaults, validation baselines, schema fields,
  output files, generated products, annual frequency, physical probability,
  risk/exposure semantics, or raw/processed swisstopo geodata are changed or
  committed. Larger validation and shape-contact splits remain future work.
- Decision: ACCEPT if final checks pass; Target 7 done for the first narrow
  concern split.
- Next proposed milestone: Add deterministic local parallel ensemble
  execution.

### M032

- Milestone id: M032.
- Roadmap item: Target 8. Add deterministic local parallel ensemble execution.
- Hypothesis/objective: Add an opt-in local threaded ensemble runner that
  preserves serial-default behavior and deterministic trajectory identity,
  ordering, and provenance without introducing SLURM, MPI, GPU, distributed
  orchestration, or larger selected-domain runs.
- Initial gap assessment: The simulator already represented trajectories as
  independent `TrajectoryRequest` values and had order-independent seed tests,
  but the public ensemble runner was serial only. There was no executable
  local threaded runner or local execution metadata contract proving
  serial-vs-parallel parity.
- Files changed:
  `src/simulation.rs`,
  `src/lib.rs`,
  `tests/hpc_readiness.rs`,
  `scripts/check_repo_consistency.py`,
  `docs/model_design.md`,
  `docs/real_case_intensity_frequency_implementation_roadmap.md`,
  `docs/next_development_targets.md`,
  `docs/agent_work_log.md`.
- Implementation summary: Added `simulate_ensemble_parallel` and
  `simulate_ensemble_parallel_with_contact_parameters` as opt-in local
  threaded ensemble runners. The implementation partitions requested
  trajectory ids into deterministic contiguous chunks, executes chunks on local
  scoped threads against shared immutable terrain/configuration, restores
  requested trajectory order after join, and returns
  `LocalParallelEnsembleExecution` metadata with schema
  `local_parallel_ensemble_v1`, requested/effective worker counts, chunk ids,
  and merge order. Serial `simulate_ensemble` remains unchanged and remains
  the default.
- Checks run:
  `cargo fmt --check`;
  `cargo test --test hpc_readiness`;
  `cargo clippy --all-targets --all-features -- -D warnings`;
  `cargo test`;
  `cargo run -- verify --all`;
  `cargo run -- validate --all`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest discover -s tests -p 'test_*.py'`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/check_repo_consistency.py`;
  `git diff --check`;
  `scripts/git-hooks/pre-commit`.
- Reviewer notes: No physics, stochastic seed derivation, defaults,
  validation-runner defaults, output schemas, generated products, annual
  frequency, physical probability, risk/exposure semantics, SLURM/MPI/GPU
  orchestration, larger ensemble execution, or raw/processed swisstopo geodata
  are changed or committed.
- Decision: ACCEPT if final checks pass; Target 8 done at the opt-in
  library-contract level.
- Next proposed milestone: Design physical/source-frequency semantics.

### M033

- Milestone id: M033.
- Roadmap item: Target 9. Design physical source-frequency semantics.
- Hypothesis/objective: Complete the source-frequency semantics target as a
  conservative design gate, deciding whether annual or physical products are
  authorized without adding runtime support or reinterpreting sampling weights.
- Initial gap assessment: Targets 1-8 were complete, but the repository still
  lacked a dedicated design-gate record defining required source-rate units,
  block and release-cell denominators, overlap policy, uncertainty,
  calibration/validation separation, and rejection tests for incomplete
  frequency metadata.
- Files changed:
  `docs/physical_source_frequency_design_gate.md`,
  `validation/pilot_runs/physical_source_frequency_design_gate_v1.yaml`,
  `scripts/validate_physical_source_frequency_design_gate.py`,
  `tests/test_physical_source_frequency_design_gate.py`,
  `scripts/check_repo_consistency.py`,
  `docs/hazard_map_semantics.md`,
  `docs/probabilistic_scenario_model_design.md`,
  `docs/real_case_intensity_frequency_implementation_roadmap.md`,
  `docs/next_development_targets.md`,
  `docs/README.md`,
  `docs/agent_work_log.md`.
- Implementation summary: Added a documentation and YAML design gate that keeps
  the annual/physical prototype deferred. The gate defines source event-rate
  units, conditional block-scenario and release-cell denominators, conceptual
  frequency propagation, required source-zone overlap rules, uncertainty
  components, calibration/validation separation, and the future schema fields
  needed before any prototype can proceed. Added a focused validator, unit
  tests, and repository consistency checks that reject premature authorization,
  missing units, missing overlap policy, missing uncertainty, and sampling
  weights reused as physical probability.
- Checks run:
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/validate_physical_source_frequency_design_gate.py validation/pilot_runs/physical_source_frequency_design_gate_v1.yaml`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest tests.test_physical_source_frequency_design_gate`;
  `git diff --check`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/check_repo_consistency.py`;
  `cargo fmt --check`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest discover -s tests -p 'test_*.py'`;
  `cargo clippy --all-targets --all-features -- -D warnings`;
  `cargo test`;
  `cargo run -- verify --all`;
  `cargo run -- validate --all`;
  `scripts/git-hooks/pre-commit`.
- Reviewer notes: No physics, defaults, trajectory execution, hazard reducer,
  annual frequency runtime support, physical probability runtime support,
  risk/exposure semantics, generated products, or raw/processed swisstopo
  geodata are changed or committed.
- Decision: ACCEPT if final checks pass; Target 9 done as a deferred design
  gate. Target 10 remains blocked until the gate blockers are resolved.
- Next proposed milestone: Resolve source-frequency evidence, overlap,
  uncertainty, and calibration/validation blockers before requesting an annual
  or physical prototype.

### M034

- Milestone id: M034.
- Roadmap item: Resolve physical/source-frequency design-gate blockers:
  source-frequency evidence contract.
- Hypothesis/objective: Close the first source-frequency schema blocker by
  defining an inactive source-rate evidence record contract and rejection
  checks, while keeping annual/physical prototype authorization false.
- Initial gap assessment: Target 9 defined the required source-frequency
  evidence fields and rejection tests, but the repository still lacked a
  concrete source-frequency evidence template and validator. Target 10 remains
  blocked because the design gate is deferred.
- Files changed:
  `docs/source_frequency_evidence_contract.md`,
  `validation/templates/source_frequency_evidence_v1.yaml`,
  `scripts/validate_source_frequency_evidence.py`,
  `tests/test_source_frequency_evidence.py`,
  `scripts/check_repo_consistency.py`,
  `docs/physical_source_frequency_design_gate.md`,
  `docs/probabilistic_scenario_model_design.md`,
  `docs/dataset_strategy.md`,
  `docs/validation_plan.md`,
  `docs/real_case_intensity_frequency_implementation_roadmap.md`,
  `docs/next_development_targets.md`,
  `docs/README.md`,
  `docs/agent_work_log.md`.
- Implementation summary: Added `source_frequency_evidence_v1` as an inactive
  evidence contract with a selected template recording
  `no_accepted_frequency_evidence`. The validator accepts complete candidate
  records only for design review and rejects missing rates, bad units, missing
  uncertainty, overlap-policy gaps, calibration/validation dataset overlap,
  swisstopo geodata as validation evidence, misleading claims, and any
  prototype authorization. Documentation now records that this closes one
  schema blocker but leaves annual/physical products deferred.
- Checks run:
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/validate_source_frequency_evidence.py validation/templates/source_frequency_evidence_v1.yaml`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest tests.test_source_frequency_evidence`;
  `git diff --check`;
  `python3 scripts/check_repo_consistency.py` failed because system Python does
  not support `from __future__ import annotations`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/check_repo_consistency.py`;
  `cargo fmt --check`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest discover -s tests -p 'test_*.py'`;
  `cargo clippy --all-targets --all-features -- -D warnings`;
  `cargo test`;
  `cargo run -- verify --all`;
  `cargo run -- validate --all`;
  `scripts/git-hooks/pre-commit`.
- Reviewer notes: No physics, defaults, trajectory execution, hazard reducer,
  annual frequency runtime support, physical probability runtime support,
  risk/exposure semantics, generated products, or raw/processed swisstopo
  geodata are changed or committed.
- Decision: ACCEPT if final checks pass; one source-frequency evidence-schema
  blocker is resolved, but Target 10 remains blocked by missing accepted
  evidence, block/release probability evidence, overlap-adjusted reducers,
  uncertainty propagation, and validation/calibration review.
- Next proposed milestone: Define the block-scenario and release-cell physical
  probability evidence contract, still without enabling runtime annual or
  physical products.

### M035

- Milestone id: M035.
- Roadmap item: Resolve physical/source-frequency design-gate blockers:
  block-scenario and release-cell physical probability evidence contract.
- Hypothesis/objective: Close the block/release probability schema blocker by
  defining an inactive evidence record contract and rejection checks, while
  keeping annual/physical prototype authorization false.
- Initial gap assessment: The source-frequency evidence contract existed, but
  the repository still lacked a concrete template and validator for conditional
  block-scenario probabilities, release-cell probabilities by block scenario,
  denominator checks, uncertainty notes, dataset separation, and sampling-weight
  boundary enforcement.
- Files changed:
  `docs/block_release_probability_evidence_contract.md`,
  `validation/templates/block_release_probability_evidence_v1.yaml`,
  `scripts/validate_block_release_probability_evidence.py`,
  `tests/test_block_release_probability_evidence.py`,
  `scripts/check_repo_consistency.py`,
  `docs/physical_source_frequency_design_gate.md`,
  `docs/probabilistic_scenario_model_design.md`,
  `docs/dataset_strategy.md`,
  `docs/validation_plan.md`,
  `docs/real_case_intensity_frequency_implementation_roadmap.md`,
  `docs/next_development_targets.md`,
  `docs/README.md`,
  `README.md`,
  `docs/agent_work_log.md`.
- Implementation summary: Added
  `block_release_probability_evidence_v1` as an inactive evidence contract with
  a selected template recording
  `no_accepted_block_release_probability_evidence`. The validator accepts
  complete candidate records only for design review and rejects invalid
  denominators, missing or non-summing block probabilities, missing or
  non-summing release-cell probabilities by block scenario, unknown block joins,
  sampling weights reused as physical probability, missing candidate
  uncertainty, calibration/validation dataset overlap, swisstopo geodata as
  validation evidence, misleading claims, and any prototype authorization.
- Checks run:
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/validate_block_release_probability_evidence.py validation/templates/block_release_probability_evidence_v1.yaml`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest tests.test_block_release_probability_evidence`;
  `git diff --check`;
  `python3 scripts/check_repo_consistency.py` failed because system Python does
  not support `from __future__ import annotations`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/check_repo_consistency.py`;
  `cargo fmt --check`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest discover -s tests -p 'test_*.py'`;
  `cargo clippy --all-targets --all-features -- -D warnings`;
  `cargo test`;
  `cargo run -- verify --all`;
  `cargo run -- validate --all`;
  `scripts/git-hooks/pre-commit`.
- Reviewer notes: No physics, defaults, trajectory execution, hazard reducer,
  annual frequency runtime support, physical probability runtime support,
  risk/exposure semantics, generated products, or raw/processed swisstopo
  geodata are changed or committed.
- Decision: ACCEPT if final checks pass; one block/release probability
  evidence-schema blocker is resolved, but Target 10 remains blocked by missing
  accepted evidence, overlap-adjusted reducers, uncertainty propagation, and
  validation/calibration review.
- Next proposed milestone: Define overlap-adjusted reducer and uncertainty
  propagation preconditions for future annual/physical products, still without
  enabling runtime annual or physical products.

### M036

- Milestone id: M036.
- Roadmap item: Resolve physical/source-frequency design-gate blockers:
  overlap-adjusted reducer and uncertainty-propagation preconditions.
- Hypothesis/objective: Close the reducer/uncertainty design blocker by
  defining an inactive precondition record contract and rejection checks, while
  keeping annual/physical prototype authorization false.
- Initial gap assessment: Source-frequency and block/release probability
  evidence contracts existed, but the repository still lacked a concrete
  template and validator for overlap policy selection, double-counting guards,
  deterministic reducer merge preconditions, required uncertainty components,
  output summary requirements, and calibration/validation separation.
- Files changed:
  `docs/physical_frequency_reducer_preconditions.md`,
  `validation/templates/physical_frequency_reducer_preconditions_v1.yaml`,
  `scripts/validate_physical_frequency_reducer_preconditions.py`,
  `tests/test_physical_frequency_reducer_preconditions.py`,
  `scripts/check_repo_consistency.py`,
  `docs/physical_source_frequency_design_gate.md`,
  `docs/probabilistic_scenario_model_design.md`,
  `docs/dataset_strategy.md`,
  `docs/validation_plan.md`,
  `docs/real_case_intensity_frequency_implementation_roadmap.md`,
  `docs/next_development_targets.md`,
  `docs/README.md`,
  `README.md`,
  `docs/agent_work_log.md`.
- Implementation summary: Added
  `physical_frequency_reducer_preconditions_v1` as an inactive precondition
  contract with a selected template recording `preconditions_not_satisfied`.
  The validator accepts complete candidate records only for design review and
  rejects missing overlap policies, missing double-counting guards,
  non-deterministic reducer merge preconditions, active annual/physical output
  support, missing uncertainty components, missing uncertainty output
  summaries, calibration/validation dataset overlap, swisstopo geodata as
  validation evidence, misleading claims, and any prototype authorization.
- Checks run:
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/validate_physical_frequency_reducer_preconditions.py validation/templates/physical_frequency_reducer_preconditions_v1.yaml`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest tests.test_physical_frequency_reducer_preconditions`;
  `git diff --check`;
  `python3 scripts/check_repo_consistency.py` failed because system Python does
  not support `from __future__ import annotations`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/check_repo_consistency.py`;
  `cargo fmt --check`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest discover -s tests -p 'test_*.py'`;
  `cargo clippy --all-targets --all-features -- -D warnings`;
  `cargo test`;
  `cargo run -- verify --all`;
  `cargo run -- validate --all`;
  `scripts/git-hooks/pre-commit`.
- Reviewer notes: No physics, defaults, trajectory execution, hazard reducer,
  annual frequency runtime support, physical probability runtime support,
  risk/exposure semantics, generated products, or raw/processed swisstopo
  geodata are changed or committed.
- Decision: ACCEPT if final checks pass; the reducer/uncertainty precondition
  blocker is resolved at the inactive contract level, but Target 10 remains
  blocked by missing accepted evidence, implemented overlap-adjusted reducers,
  implemented uncertainty propagation, and validation/calibration review.
- Next proposed milestone: Define the validation/calibration review gate for
  future annual/physical products, still without enabling runtime annual or
  physical products.

### M037

- Milestone id: M037.
- Roadmap item: Resolve physical/source-frequency design-gate blockers:
  validation/calibration review gate for future annual/physical products.
- Hypothesis/objective: Close the review-gate blocker by defining an inactive
  validation/calibration review record contract and rejection checks, while
  keeping annual/physical prototype authorization false.
- Initial gap assessment: Source-frequency, block/release probability, and
  reducer/uncertainty precondition contracts existed, but the repository still
  lacked a concrete template and validator for frequency-product calibration,
  validation, holdout, maturity limits, dataset-role separation, no-tuning
  rules, and claim boundaries.
- Files changed:
  `docs/annual_physical_validation_calibration_review_gate.md`,
  `validation/templates/annual_physical_validation_calibration_review_gate_v1.yaml`,
  `scripts/validate_annual_physical_validation_calibration_review_gate.py`,
  `tests/test_annual_physical_validation_calibration_review_gate.py`,
  `scripts/check_repo_consistency.py`,
  `docs/physical_source_frequency_design_gate.md`,
  `docs/probabilistic_scenario_model_design.md`,
  `docs/dataset_strategy.md`,
  `docs/validation_plan.md`,
  `docs/real_case_intensity_frequency_implementation_roadmap.md`,
  `docs/next_development_targets.md`,
  `docs/README.md`,
  `README.md`,
  `docs/agent_work_log.md`.
- Implementation summary: Added
  `annual_physical_validation_calibration_review_gate_v1` as an inactive
  review-gate contract with a selected template recording `review_not_passed`.
  The validator accepts complete candidate records only for design review and
  rejects missing source-frequency/block-release/reducer record references,
  missing no-tuning rules, missing maturity targets or caps,
  calibration/validation/holdout dataset overlap, swisstopo geodata as
  validation or holdout evidence, claim-boundary support, misleading claims,
  and any prototype authorization.
- Checks run:
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/validate_annual_physical_validation_calibration_review_gate.py validation/templates/annual_physical_validation_calibration_review_gate_v1.yaml`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest tests.test_annual_physical_validation_calibration_review_gate`;
  `git diff --check`;
  `python3 scripts/check_repo_consistency.py` failed because system Python does
  not support `from __future__ import annotations`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/check_repo_consistency.py`;
  `cargo fmt --check`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest discover -s tests -p 'test_*.py'`;
  `cargo clippy --all-targets --all-features -- -D warnings`;
  `cargo test`;
  `cargo run -- verify --all`;
  `cargo run -- validate --all`;
  `scripts/git-hooks/pre-commit`.
- Reviewer notes: No physics, defaults, trajectory execution, hazard reducer,
  annual frequency runtime support, physical probability runtime support,
  risk/exposure semantics, generated products, or raw/processed swisstopo
  geodata are changed or committed.
- Decision: ACCEPT if final checks pass; the validation/calibration review
  blocker is resolved at the inactive contract level, but Target 10 remains
  blocked by missing accepted evidence, implemented overlap-adjusted reducers,
  implemented uncertainty propagation, and an accepted review record.
- Next proposed milestone: Reassess the physical/source-frequency design gate
  decision with all inactive contracts present; keep the annual/physical
  prototype deferred unless accepted evidence and implemented reducers exist.

### M038

- Milestone id: M038.
- Roadmap item: Reassess the physical/source-frequency design gate with all
  inactive blocker contracts present.
- Hypothesis/objective: Make the selected design-gate record explicitly
  machine-check the four inactive blocker contracts and keep Target 10 blocked
  until accepted evidence, implemented reducers, uncertainty propagation, and
  an accepted review record exist.
- Initial gap assessment: The source-frequency, block/release probability,
  reducer/uncertainty, and validation/calibration contracts existed, but the
  main physical/source-frequency gate did not yet enumerate those records or
  verify their checked-in statuses as the reason the annual/physical prototype
  remains unauthorized.
- Files changed:
  `validation/pilot_runs/physical_source_frequency_design_gate_v1.yaml`,
  `scripts/validate_physical_source_frequency_design_gate.py`,
  `tests/test_physical_source_frequency_design_gate.py`,
  `scripts/check_repo_consistency.py`,
  `docs/physical_source_frequency_design_gate.md`,
  `docs/real_case_intensity_frequency_implementation_roadmap.md`,
  `docs/next_development_targets.md`,
  `docs/agent_work_log.md`.
- Implementation summary: Added a `gate_reassessment` section and
  `blocker_contracts` list to the selected design-gate record. The validator
  now reads each referenced contract template, verifies schema and status
  agreement, requires inactive contracts to remain prototype blockers, and
  reports blocker counts. Focused tests cover missing blocker records,
  mismatched observed statuses, and inactive contracts incorrectly marked
  nonblocking.
- Checks run:
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/validate_physical_source_frequency_design_gate.py validation/pilot_runs/physical_source_frequency_design_gate_v1.yaml`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest tests.test_physical_source_frequency_design_gate`;
  `git diff --check`;
  `python3 scripts/check_repo_consistency.py` failed because system Python does
  not support `from __future__ import annotations`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/check_repo_consistency.py`;
  `cargo fmt --check`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest discover -s tests -p 'test_*.py'`;
  `cargo clippy --all-targets --all-features -- -D warnings`;
  `cargo test`;
  `cargo run -- verify --all`;
  `cargo run -- validate --all`;
  `scripts/git-hooks/pre-commit`.
- Reviewer notes: No physics, defaults, generated outputs, raw/processed
  swisstopo geodata, annual frequency runtime support, physical probability
  runtime support, risk/exposure semantics, or operational claims are changed.
- Decision: ACCEPT if final checks pass; the gate reassessment is complete and
  explicitly deferred, with Target 10 still blocked.
- Next proposed milestone: Resolve exactly one remaining blocker only if
  accepted evidence or implemented reducer work is explicitly requested;
  otherwise keep annual/physical prototype work deferred.

### M039

- Milestone id: M039.
- Roadmap item: Target 10. Annual/physical intensity-frequency prototype
  preflight.
- Hypothesis/objective: Record the first incomplete roadmap item as explicitly
  blocked by the deferred physical/source-frequency design gate, with an
  executable preflight check that prevents accidental annual/physical runtime
  work before accepted evidence and implemented reducers exist.
- Initial gap assessment: Targets 1-9 were complete at their documented levels.
  Target 10 was the first incomplete item, but the selected design gate remains
  `deferred` and all four blocker contracts are inactive. Implementing runtime
  annual or physical products would violate the current roadmap and claim
  boundaries; the missing safe artifact was a Target 10 preflight record tying
  prototype work to the gate decision.
- Files changed:
  `docs/annual_physical_prototype_preflight.md`,
  `validation/templates/annual_physical_prototype_preflight_v1.yaml`,
  `scripts/validate_annual_physical_prototype_preflight.py`,
  `tests/test_annual_physical_prototype_preflight.py`,
  `scripts/check_repo_consistency.py`,
  `docs/physical_source_frequency_design_gate.md`,
  `docs/real_case_intensity_frequency_implementation_roadmap.md`,
  `docs/next_development_targets.md`,
  `docs/README.md`,
  `README.md`,
  `docs/agent_work_log.md`.
- Implementation summary: Added `annual_physical_prototype_preflight_v1` as an
  inactive Target 10 guard with selected status `blocked_by_design_gate`. The
  validator reads the selected physical/source-frequency design gate, verifies
  that the observed gate decision remains `deferred`, rejects prototype
  authorization and runtime support, requires the remaining blocker list, and
  preserves annual/physical/risk/operational claim boundaries.
- Checks run:
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/validate_annual_physical_prototype_preflight.py validation/templates/annual_physical_prototype_preflight_v1.yaml`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest tests.test_annual_physical_prototype_preflight`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/check_repo_consistency.py`;
  `git diff --check`;
  `CARGO_TARGET_DIR=/Users/fuhrer/Desktop/rust_rockfall/target cargo fmt --check`;
  `CARGO_TARGET_DIR=/Users/fuhrer/Desktop/rust_rockfall/target cargo clippy --all-targets --all-features -- -D warnings`;
  `CARGO_TARGET_DIR=/Users/fuhrer/Desktop/rust_rockfall/target cargo test`;
  `CARGO_TARGET_DIR=/Users/fuhrer/Desktop/rust_rockfall/target cargo run -- verify --all`;
  `CARGO_TARGET_DIR=/Users/fuhrer/Desktop/rust_rockfall/target cargo run -- validate --all`;
  `CARGO_TARGET_DIR=/Users/fuhrer/Desktop/rust_rockfall/target UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest discover -s tests -p 'test_*.py'`;
  `CARGO_TARGET_DIR=/Users/fuhrer/Desktop/rust_rockfall/target UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/check_repo_consistency.py`;
  `CARGO_TARGET_DIR=/Users/fuhrer/Desktop/rust_rockfall/target scripts/git-hooks/pre-commit`.
- Reviewer notes: No physics, defaults, generated outputs, raw/processed
  swisstopo geodata, annual frequency runtime support, physical probability
  runtime support, risk/exposure semantics, or operational claims are changed.
- Decision: ACCEPT if final checks pass; Target 10 is now guarded by an
  executable no-go preflight while the prototype remains blocked.
- Next proposed milestone: Resolve exactly one real blocker only if accepted
  evidence or implemented reducer work is explicitly requested; otherwise keep
  annual/physical prototype work deferred.

### M040

- Milestone id: M040.
- Roadmap item: Target 10 blocker: source-frequency evidence design-review
  fixture.
- Hypothesis/objective: Add one executable accepted-record fixture for the
  source-frequency evidence contract without treating it as accepted Tschamut
  evidence or authorizing annual/physical runtime support.
- Initial gap assessment: The source-frequency evidence contract and selected
  `no_accepted_frequency_evidence` template existed, and in-memory tests covered
  candidate records, but the repository did not contain a small checked fixture
  exercising the `accepted_for_design_review` state. Real accepted Swiss
  source-rate evidence is still unavailable and must not be invented.
- Files changed:
  `tests/fixtures/frequency/source_frequency_evidence_design_review_fixture_v1.yaml`,
  `tests/test_source_frequency_evidence.py`,
  `scripts/check_repo_consistency.py`,
  `docs/source_frequency_evidence_contract.md`,
  `docs/real_case_intensity_frequency_implementation_roadmap.md`,
  `docs/next_development_targets.md`,
  `docs/agent_work_log.md`.
- Implementation summary: Added a synthetic
  `accepted_for_design_review` source-frequency evidence fixture with explicit
  LV95/LN02 metadata, source-rate units, uncertainty interval, overlap policy,
  separated calibration/validation fixture ids, and claim boundaries. Tests and
  consistency checks validate the fixture while docs state that it is not
  accepted evidence for Tschamut or any real Swiss source zone.
- Checks run:
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/validate_source_frequency_evidence.py tests/fixtures/frequency/source_frequency_evidence_design_review_fixture_v1.yaml`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest tests.test_source_frequency_evidence`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/check_repo_consistency.py`;
  `git diff --check`;
  `CARGO_TARGET_DIR=/Users/fuhrer/Desktop/rust_rockfall/target cargo fmt --check`;
  `CARGO_TARGET_DIR=/Users/fuhrer/Desktop/rust_rockfall/target cargo clippy --all-targets --all-features -- -D warnings`;
  `CARGO_TARGET_DIR=/Users/fuhrer/Desktop/rust_rockfall/target cargo test`;
  `CARGO_TARGET_DIR=/Users/fuhrer/Desktop/rust_rockfall/target cargo run -- verify --all`;
  `CARGO_TARGET_DIR=/Users/fuhrer/Desktop/rust_rockfall/target cargo run -- validate --all`;
  `CARGO_TARGET_DIR=/Users/fuhrer/Desktop/rust_rockfall/target UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest discover -s tests -p 'test_*.py'`;
  `CARGO_TARGET_DIR=/Users/fuhrer/Desktop/rust_rockfall/target UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/check_repo_consistency.py`;
  `CARGO_TARGET_DIR=/Users/fuhrer/Desktop/rust_rockfall/target scripts/git-hooks/pre-commit`.
- Reviewer notes: No physics, defaults, generated outputs, raw/processed
  swisstopo geodata, annual frequency runtime support, physical probability
  runtime support, risk/exposure semantics, operational claims, or selected
  design-gate authorization are changed.
- Decision: ACCEPT if final checks pass; source-frequency accepted-record
  validation is now covered by a tiny committed fixture while the real evidence
  blocker remains unresolved.
- Next proposed milestone: Resolve exactly one real blocker only if real
  accepted evidence or implemented reducer work is explicitly provided or
  requested.

### M042

- Milestone id: M042.
- Roadmap item: Target 10 blocker: physical frequency reducer precondition
  design-review fixture.
- Hypothesis/objective: Add one executable accepted-record fixture for the
  reducer precondition contract without implementing overlap-adjusted reducers,
  uncertainty propagation, or annual/physical runtime support.
- Initial gap assessment: The reducer precondition contract and selected
  `preconditions_not_satisfied` template existed, and in-memory tests covered
  candidate records, but the repository did not contain a small checked fixture
  exercising the `accepted_for_design_review` state. Implemented
  overlap-adjusted reducers and uncertainty propagation are still unavailable
  and must not be implied by a schema fixture.
- Files changed:
  `tests/fixtures/frequency/physical_frequency_reducer_preconditions_design_review_fixture_v1.yaml`,
  `tests/test_physical_frequency_reducer_preconditions.py`,
  `scripts/check_repo_consistency.py`,
  `docs/physical_frequency_reducer_preconditions.md`,
  `docs/real_case_intensity_frequency_implementation_roadmap.md`,
  `docs/next_development_targets.md`,
  `docs/agent_work_log.md`.
- Implementation summary: Added a synthetic `accepted_for_design_review`
  reducer-precondition fixture with explicit LV95/LN02 source-zone scope,
  documented-overlap-adjustment policy, double-counting guard requirement,
  deterministic and order-independent merge requirements, inactive output-unit
  support, required input record types, uncertainty components and summary
  fields, separated calibration/validation fixture ids, and claim boundaries.
  Tests and consistency checks validate the fixture while docs state that it is
  not an implemented reducer and does not authorize runtime products.
- Checks run:
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/validate_physical_frequency_reducer_preconditions.py tests/fixtures/frequency/physical_frequency_reducer_preconditions_design_review_fixture_v1.yaml`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest tests.test_physical_frequency_reducer_preconditions`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/check_repo_consistency.py`;
  `git diff --check`;
  `CARGO_TARGET_DIR=/Users/fuhrer/Desktop/rust_rockfall/target cargo fmt --check`;
  `CARGO_TARGET_DIR=/Users/fuhrer/Desktop/rust_rockfall/target cargo clippy --all-targets --all-features -- -D warnings`;
  `CARGO_TARGET_DIR=/Users/fuhrer/Desktop/rust_rockfall/target cargo test`;
  `CARGO_TARGET_DIR=/Users/fuhrer/Desktop/rust_rockfall/target cargo run -- verify --all`;
  `CARGO_TARGET_DIR=/Users/fuhrer/Desktop/rust_rockfall/target cargo run -- validate --all`;
  `CARGO_TARGET_DIR=/Users/fuhrer/Desktop/rust_rockfall/target UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest discover -s tests -p 'test_*.py'`;
  `CARGO_TARGET_DIR=/Users/fuhrer/Desktop/rust_rockfall/target UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/check_repo_consistency.py`;
  `CARGO_TARGET_DIR=/Users/fuhrer/Desktop/rust_rockfall/target scripts/git-hooks/pre-commit`.
- Reviewer notes: No physics, defaults, generated outputs, raw/processed
  swisstopo geodata, annual frequency runtime support, physical probability
  runtime support, risk/exposure semantics, operational claims, reducer runtime
  support, or selected design-gate authorization are changed.
- Decision: ACCEPT if final checks pass; reducer precondition accepted-record
  validation is now covered by a tiny committed fixture while implementation
  remains unresolved.
- Next proposed milestone: Resolve exactly one real blocker only if implemented
  reducer work or accepted validation/calibration review evidence is explicitly
  provided or requested.

### M043

- Milestone id: M043.
- Roadmap item: Target 10 blocker: annual/physical validation-calibration
  review design-review fixture.
- Hypothesis/objective: Add one executable accepted-record fixture for the
  validation/calibration review gate without accepting real validation evidence
  or authorizing annual/physical runtime support.
- Initial gap assessment: The validation/calibration review gate and selected
  `review_not_passed` template existed, and in-memory tests covered candidate
  records, but the repository did not contain a small checked fixture exercising
  the `accepted_for_design_review` state. Real accepted annual/physical
  validation-calibration review evidence is still unavailable and must not be
  invented.
- Files changed:
  `tests/fixtures/frequency/annual_physical_validation_calibration_review_gate_design_review_fixture_v1.yaml`,
  `tests/test_annual_physical_validation_calibration_review_gate.py`,
  `scripts/check_repo_consistency.py`,
  `docs/annual_physical_validation_calibration_review_gate.md`,
  `docs/real_case_intensity_frequency_implementation_roadmap.md`,
  `docs/next_development_targets.md`,
  `docs/agent_work_log.md`.
- Implementation summary: Added a synthetic `accepted_for_design_review`
  validation/calibration review fixture with explicit references to the
  source-frequency, block/release, and reducer-precondition design-review
  fixtures; separated calibration, validation, and holdout fixture ids;
  no-tuning and external-generalization requirements; maturity target/cap
  fields; swisstopo input-geodata boundaries; and claim boundaries. Tests and
  consistency checks validate the fixture while docs state that it is not
  accepted validation evidence for Tschamut or any real Swiss source zone.
- Checks run:
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/validate_annual_physical_validation_calibration_review_gate.py tests/fixtures/frequency/annual_physical_validation_calibration_review_gate_design_review_fixture_v1.yaml`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest tests.test_annual_physical_validation_calibration_review_gate`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/check_repo_consistency.py`;
  `git diff --check`;
  `CARGO_TARGET_DIR=/Users/fuhrer/Desktop/rust_rockfall/target cargo fmt --check`;
  `CARGO_TARGET_DIR=/Users/fuhrer/Desktop/rust_rockfall/target cargo clippy --all-targets --all-features -- -D warnings`;
  `CARGO_TARGET_DIR=/Users/fuhrer/Desktop/rust_rockfall/target cargo test`;
  `CARGO_TARGET_DIR=/Users/fuhrer/Desktop/rust_rockfall/target cargo run -- verify --all`;
  `CARGO_TARGET_DIR=/Users/fuhrer/Desktop/rust_rockfall/target cargo run -- validate --all`;
  `CARGO_TARGET_DIR=/Users/fuhrer/Desktop/rust_rockfall/target UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest discover -s tests -p 'test_*.py'`;
  `CARGO_TARGET_DIR=/Users/fuhrer/Desktop/rust_rockfall/target UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/check_repo_consistency.py`;
  `CARGO_TARGET_DIR=/Users/fuhrer/Desktop/rust_rockfall/target scripts/git-hooks/pre-commit`.
- Reviewer notes: No physics, defaults, generated outputs, raw/processed
  swisstopo geodata, annual frequency runtime support, physical probability
  runtime support, risk/exposure semantics, operational claims, accepted real
  validation evidence, or selected design-gate authorization are changed.
- Decision: ACCEPT if final checks pass; validation/calibration review
  accepted-record validation is now covered by a tiny committed fixture while
  real review acceptance remains unresolved.
- Next proposed milestone: Resolve exactly one real blocker only if real
  accepted evidence or implemented reducer work is explicitly provided; otherwise
  reassess the Target 10 preflight/design gate against the now-covered synthetic
  fixture states without enabling runtime products.

### M044

- Milestone id: M044.
- Roadmap item: Target 10 blocker: design-gate/preflight reassessment against
  synthetic accepted-record fixture coverage.
- Hypothesis/objective: Reassess the physical/source-frequency design gate
  against the four completed synthetic design-review fixtures while preserving
  the selected inactive templates as blocking gate inputs and keeping the
  annual/physical prototype unauthorized.
- Initial gap assessment: The source-frequency, block/release probability,
  reducer-precondition, and validation/calibration design-review fixtures all
  existed and were individually validated, but the central design gate did not
  yet enumerate or verify those fixture states. The preflight still correctly
  referenced the deferred gate, but documentation did not explicitly state that
  fixture coverage is schema-only and does not close real evidence or reducer
  blockers.
- Files changed:
  `validation/pilot_runs/physical_source_frequency_design_gate_v1.yaml`,
  `scripts/validate_physical_source_frequency_design_gate.py`,
  `tests/test_physical_source_frequency_design_gate.py`,
  `scripts/check_repo_consistency.py`,
  `docs/physical_source_frequency_design_gate.md`,
  `docs/annual_physical_prototype_preflight.md`,
  `docs/real_case_intensity_frequency_implementation_roadmap.md`,
  `docs/next_development_targets.md`,
  `docs/agent_work_log.md`.
- Implementation summary: Added a `design_review_fixture_reassessment` section
  and four `design_review_fixtures` entries to the executable design-gate
  record. The gate validator now reads those fixture files, verifies their
  schema versions, `accepted_for_design_review` statuses, false prototype
  authorization, and `not_authorized` runtime state, while still requiring the
  selected inactive templates to remain prototype blockers. Tests cover fixture
  status drift and accidental runtime authorization.
- Checks run:
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/validate_physical_source_frequency_design_gate.py validation/pilot_runs/physical_source_frequency_design_gate_v1.yaml`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest tests.test_physical_source_frequency_design_gate`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/validate_annual_physical_prototype_preflight.py validation/templates/annual_physical_prototype_preflight_v1.yaml`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest tests.test_annual_physical_prototype_preflight`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/check_repo_consistency.py`;
  `git diff --check`;
  `CARGO_TARGET_DIR=/Users/fuhrer/Desktop/rust_rockfall/target cargo fmt --check`;
  `CARGO_TARGET_DIR=/Users/fuhrer/Desktop/rust_rockfall/target cargo clippy --all-targets --all-features -- -D warnings`;
  `CARGO_TARGET_DIR=/Users/fuhrer/Desktop/rust_rockfall/target cargo test`;
  `CARGO_TARGET_DIR=/Users/fuhrer/Desktop/rust_rockfall/target cargo run -- verify --all`;
  `CARGO_TARGET_DIR=/Users/fuhrer/Desktop/rust_rockfall/target cargo run -- validate --all`;
  `CARGO_TARGET_DIR=/Users/fuhrer/Desktop/rust_rockfall/target UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest discover -s tests -p 'test_*.py'`;
  `CARGO_TARGET_DIR=/Users/fuhrer/Desktop/rust_rockfall/target UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/check_repo_consistency.py`;
  `CARGO_TARGET_DIR=/Users/fuhrer/Desktop/rust_rockfall/target scripts/git-hooks/pre-commit`.
- Reviewer notes: No physics, defaults, generated outputs, raw/processed
  swisstopo geodata, annual frequency runtime support, physical probability
  runtime support, risk/exposure semantics, operational claims, accepted real
  validation evidence, implemented reducers, or selected design-gate
  authorization are changed.
- Decision: ACCEPT if final checks pass; synthetic accepted-record fixture
  coverage is now centrally reassessed by the design gate while Target 10
  remains blocked.
- Next proposed milestone: Resolve exactly one real blocker only if real
  accepted evidence or implemented reducer work is explicitly provided;
  otherwise keep annual/physical prototype implementation deferred.

### M045

- Milestone id: M045.
- Roadmap item: Scalable conditional intensity-exceedance pilot for the selected
  Tschamut public domain.
- Hypothesis/objective: Add a narrow conditional-only scaling slice that makes
  deterministic local chunking, chunk manifests, sorted reducer merge rules,
  summary-only conditional curves, output-budget diagnostics, and convergence
  diagnostics executable without introducing annual, physical-probability,
  return-period, risk, exposure, vulnerability, or operational semantics.
- Initial gap assessment: The hazard-layer runner already supported local
  reducer workers, chunk manifests, deterministic sorted chunk merge, and
  summary-only conditional curve export, but the run manifest did not yet
  expose a compact conditional execution diagnostics section and the selected
  Tschamut pilot lacked a validated decision record tying those controls to the
  no-scale-up blockers.
- Files changed:
  `scripts/build_hazard_layers.py`,
  `tests/test_hazard_layers.py`,
  `validation/pilot_runs/tschamut_public_scalable_conditional_execution_v1.yaml`,
  `scripts/validate_scalable_conditional_execution.py`,
  `tests/test_scalable_conditional_execution.py`,
  `docs/tschamut_public_scalable_conditional_execution.md`,
  `docs/real_case_intensity_frequency_implementation_roadmap.md`,
  `docs/next_development_targets.md`,
  `scripts/check_repo_consistency.py`,
  `docs/agent_work_log.md`.
- Implementation summary: Added `conditional_hazard_execution_diagnostics_v1`
  to hazard run manifests, covering conditional product labels, serial or
  chunked reducer settings, chunk manifest counts, sorted merge order,
  summary-only curve status, grid cell count, output file/byte counts, and
  convergence diagnostics required before scale-up. Added a selected Tschamut
  scalable conditional execution decision record plus validator/tests that keep
  scale-up unauthorized until convergence, GIS visual QA, obstacle context, and
  target output-budget evidence are complete.
- Checks run:
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest tests.test_hazard_layers tests.test_scalable_conditional_execution`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/validate_scalable_conditional_execution.py validation/pilot_runs/tschamut_public_scalable_conditional_execution_v1.yaml`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/check_repo_consistency.py`;
  `git diff --check`;
  `CARGO_TARGET_DIR=/Users/fuhrer/Desktop/rust_rockfall/target cargo fmt --check`;
  `CARGO_TARGET_DIR=/Users/fuhrer/Desktop/rust_rockfall/target cargo clippy --all-targets --all-features -- -D warnings`;
  `CARGO_TARGET_DIR=/Users/fuhrer/Desktop/rust_rockfall/target cargo test`;
  `CARGO_TARGET_DIR=/Users/fuhrer/Desktop/rust_rockfall/target cargo run -- verify --all`;
  `CARGO_TARGET_DIR=/Users/fuhrer/Desktop/rust_rockfall/target cargo run -- validate --all`;
  `CARGO_TARGET_DIR=/Users/fuhrer/Desktop/rust_rockfall/target UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest discover -s tests -p 'test_*.py'`;
  `CARGO_TARGET_DIR=/Users/fuhrer/Desktop/rust_rockfall/target UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/check_repo_consistency.py`;
  `CARGO_TARGET_DIR=/Users/fuhrer/Desktop/rust_rockfall/target scripts/git-hooks/pre-commit`.
- Reviewer notes: No physics, sampling weights, defaults, generated outputs,
  raw/public/private geodata, annual frequency support, physical probability
  support, return-period semantics, risk/exposure/vulnerability semantics, or
  operational claims are changed.
- Decision: ACCEPT if final checks pass; scalable conditional execution is
  design-ready and test-covered, but selected Tschamut ensemble-size increase
  remains unauthorized.
- Next proposed milestone: Run the selected Tschamut scalable conditional
  command locally only after ignored input data are present, then record
  target-scale convergence and output-budget evidence before reconsidering
  ensemble-size increase.

### M046

- Milestone id: M046.
- Roadmap item: Deterministic chunked ensemble execution architecture.
- Hypothesis/objective: Move deterministic local ensemble chunk execution from
  library-only support into the real validation case runner so large
  conditional trajectory ensembles can record reproducible chunk provenance
  before any future CSCS/SLURM orchestration.
- Initial gap assessment: `simulate_ensemble_parallel` already provided
  deterministic local-thread chunks and HPC-readiness tests, but validation
  cases still used the serial ensemble path and `run_manifest_v1` did not
  record trajectory-execution chunk ids, worker counts, or merge order for
  configured ensemble runs.
- Files changed:
  `src/validation.rs`,
  `src/manifest.rs`,
  `tests/config_io_terrain.rs`,
  `scripts/check_repo_consistency.py`,
  `docs/model_design.md`,
  `docs/validation_data_schema.md`,
  `docs/scalability_and_data_formats_review.md`,
  `docs/decision_log.md`,
  `docs/real_case_intensity_frequency_implementation_roadmap.md`,
  `docs/next_development_targets.md`,
  `docs/agent_work_log.md`.
- Implementation summary: Added optional `random.ensemble_workers` to
  validation cases. When configured with `ensemble_size > 1`, the validation
  runner uses `simulate_ensemble_parallel_with_contact_parameters`, preserves
  deterministic requested-trajectory ordering, and serializes
  `local_parallel_ensemble_v1` as `ensemble_execution` in `run_manifest_v1`.
  Cases that omit `ensemble_workers` keep the previous serial path.
- Checks run:
  `CARGO_TARGET_DIR=/Users/fuhrer/Desktop/rust_rockfall/target cargo fmt --check`;
  `CARGO_TARGET_DIR=/Users/fuhrer/Desktop/rust_rockfall/target cargo test --test hpc_readiness`;
  `CARGO_TARGET_DIR=/Users/fuhrer/Desktop/rust_rockfall/target cargo test --test config_io_terrain`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/check_repo_consistency.py`;
  `git diff --check`;
  `CARGO_TARGET_DIR=/Users/fuhrer/Desktop/rust_rockfall/target cargo clippy --all-targets --all-features -- -D warnings`;
  `CARGO_TARGET_DIR=/Users/fuhrer/Desktop/rust_rockfall/target cargo test`;
  `CARGO_TARGET_DIR=/Users/fuhrer/Desktop/rust_rockfall/target cargo run -- verify --all`;
  `CARGO_TARGET_DIR=/Users/fuhrer/Desktop/rust_rockfall/target cargo run -- validate --all`;
  `CARGO_TARGET_DIR=/Users/fuhrer/Desktop/rust_rockfall/target UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest discover -s tests -p 'test_*.py'`;
  `CARGO_TARGET_DIR=/Users/fuhrer/Desktop/rust_rockfall/target UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/check_repo_consistency.py`;
  `CARGO_TARGET_DIR=/Users/fuhrer/Desktop/rust_rockfall/target scripts/git-hooks/pre-commit`.
- Reviewer notes: No physics, defaults, sampling weights, generated large
  outputs, raw/public/private geodata, annual frequency support, physical
  probability support, calibration, benchmark enablement, risk/exposure
  semantics, SLURM/MPI/GPU code, or operational claims are changed.
- Decision: ACCEPT if final checks pass; this closes the first validation-runner
  provenance gap but resumable cross-process chunk manifests and scheduler
  orchestration remain future work.
- Next proposed milestone: Add a design-only or fixture-backed resumable
  trajectory chunk manifest contract with idempotent chunk completion and
  output checksum preconditions, still without adding scheduler execution.

### M041

- Milestone id: M041.
- Roadmap item: Target 10 blocker: block/release probability evidence
  design-review fixture.
- Hypothesis/objective: Add one executable accepted-record fixture for the
  block/release probability evidence contract without treating it as accepted
  Tschamut evidence or authorizing annual/physical runtime support.
- Initial gap assessment: The block/release probability evidence contract and
  selected `no_accepted_block_release_probability_evidence` template existed,
  and in-memory tests covered candidate records, but the repository did not
  contain a small checked fixture exercising the `accepted_for_design_review`
  state. Real accepted Swiss block-scenario and release-cell probability
  evidence is still unavailable and must not be invented.
- Files changed:
  `tests/fixtures/frequency/block_release_probability_evidence_design_review_fixture_v1.yaml`,
  `tests/test_block_release_probability_evidence.py`,
  `scripts/check_repo_consistency.py`,
  `docs/block_release_probability_evidence_contract.md`,
  `docs/real_case_intensity_frequency_implementation_roadmap.md`,
  `docs/next_development_targets.md`,
  `docs/agent_work_log.md`.
- Implementation summary: Added a synthetic `accepted_for_design_review`
  block/release evidence fixture with explicit LV95/LN02 metadata, conditional
  block-scenario probabilities summing to one, release-cell probabilities
  summing to one per block scenario, sampling-weight boundary checks,
  uncertainty notes, separated calibration/validation fixture ids, and claim
  boundaries. Tests and consistency checks validate the fixture while docs state
  that it is not accepted evidence for Tschamut or any real Swiss source zone.
- Checks run:
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/validate_block_release_probability_evidence.py tests/fixtures/frequency/block_release_probability_evidence_design_review_fixture_v1.yaml`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest tests.test_block_release_probability_evidence`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/check_repo_consistency.py`;
  `git diff --check`;
  `CARGO_TARGET_DIR=/Users/fuhrer/Desktop/rust_rockfall/target cargo fmt --check`;
  `CARGO_TARGET_DIR=/Users/fuhrer/Desktop/rust_rockfall/target cargo clippy --all-targets --all-features -- -D warnings`;
  `CARGO_TARGET_DIR=/Users/fuhrer/Desktop/rust_rockfall/target cargo test`;
  `CARGO_TARGET_DIR=/Users/fuhrer/Desktop/rust_rockfall/target cargo run -- verify --all`;
  `CARGO_TARGET_DIR=/Users/fuhrer/Desktop/rust_rockfall/target cargo run -- validate --all`;
  `CARGO_TARGET_DIR=/Users/fuhrer/Desktop/rust_rockfall/target UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest discover -s tests -p 'test_*.py'`;
  `CARGO_TARGET_DIR=/Users/fuhrer/Desktop/rust_rockfall/target UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/check_repo_consistency.py`;
  `CARGO_TARGET_DIR=/Users/fuhrer/Desktop/rust_rockfall/target scripts/git-hooks/pre-commit`.
- Reviewer notes: No physics, defaults, generated outputs, raw/processed
  swisstopo geodata, annual frequency runtime support, physical probability
  runtime support, risk/exposure semantics, operational claims, or selected
  design-gate authorization are changed.
- Decision: ACCEPT if final checks pass; block/release accepted-record
  validation is now covered by a tiny committed fixture while the real evidence
  blocker remains unresolved.
- Next proposed milestone: Resolve exactly one real blocker only if real
  accepted evidence or implemented reducer work is explicitly provided or
  requested.

### M047

- Milestone id: M047.
- Roadmap item: Roadmap reassessment after scalable conditional execution and
  validation-runner ensemble provenance.
- Hypothesis/objective: Update the active roadmaps so they reflect the current
  repository state: the selected scalable conditional execution contract and
  local parallel ensemble provenance exist, but selected target-scale
  convergence and output-budget evidence have not yet been generated.
- Initial gap assessment: `docs/next_development_targets.md` still pointed to
  physical/source-frequency semantics as the next task, and
  `docs/roadmap_recommendation_matrix.md` still ranked completed guardrail work
  such as fallible DEM-facing integration and deterministic local parallel
  ensemble execution above the actual missing evidence step.
- Files changed:
  `docs/next_development_targets.md`,
  `docs/real_case_intensity_frequency_implementation_roadmap.md`,
  `docs/roadmap_recommendation_matrix.md`,
  `docs/agent_work_log.md`.
- Implementation summary: Reprioritized near-term work around executing or
  explicitly blocking the selected Tschamut scalable conditional target-scale
  gate, then reassessing the ensemble-size gate with convergence,
  output-budget, manual GIS/QGIS, and forest/obstacle evidence. Annual and
  physical intensity-frequency work remains deferred behind accepted
  source-frequency evidence and preflight gates.
- Checks run:
  `git diff --check`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/check_repo_consistency.py`.
- Reviewer notes: Documentation-only roadmap update; no physics, defaults,
  sampling weights, generated outputs, raw geodata, annual frequency support,
  physical probability support, risk/exposure semantics, or operational claims
  are changed.
- Decision: ACCEPT; documentation consistency checks pass.
- Next proposed milestone: Run the selected Tschamut scalable conditional
  target-scale gate locally with ignored prepared inputs and record
  convergence, output-budget, runtime, memory, checksum, and worker-parity
  evidence before changing the ensemble-size gate.

### M048

- Milestone id: M048.
- Roadmap item: Target 11 scalable conditional target-scale gate.
- Hypothesis/objective: Attempt the selected Tschamut target-scale conditional
  gate from the current checkout and record a share-safe evidence state without
  fabricating missing ignored inputs or generated results.
- Initial gap assessment: The scalable conditional contract and command plan
  are valid, but the checkout lacks the ignored private validation case,
  processed DEM metadata, scenario table, prior trajectory directory, and prior
  hazard manifest required to execute or compare the target-scale run.
- Files changed:
  `validation/pilot_runs/tschamut_public_scalable_conditional_target_gate_v1.yaml`,
  `scripts/validate_scalable_conditional_target_gate.py`,
  `tests/test_scalable_conditional_target_gate.py`,
  `docs/tschamut_public_scalable_conditional_target_gate.md`,
  `scripts/check_repo_consistency.py`,
  `docs/next_development_targets.md`,
  `docs/real_case_intensity_frequency_implementation_roadmap.md`,
  `docs/roadmap_recommendation_matrix.md`,
  `docs/agent_work_log.md`.
- Implementation summary: Added a `scalable_conditional_target_gate_v1`
  selected-pilot record with `gate_status: blocked_missing_inputs`. The record
  lists the missing ignored paths, confirms target execution did not start,
  keeps generated outputs uncommitted, requires summary-only conditional curves,
  validation-runner `random.ensemble_workers`, deterministic reducer workers,
  convergence/output-budget evidence, and explicit claim boundaries before any
  ensemble-size gate reassessment. A validator, tests, docs, and consistency
  checks now guard the blocked target-gate state.
- Checks run:
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/validate_scalable_conditional_target_gate.py validation/pilot_runs/tschamut_public_scalable_conditional_target_gate_v1.yaml`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest tests.test_scalable_conditional_target_gate`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/check_repo_consistency.py`;
  `git diff --check`;
  `CARGO_TARGET_DIR=/Users/fuhrer/Desktop/rust_rockfall/target cargo fmt --check`;
  `CARGO_TARGET_DIR=/Users/fuhrer/Desktop/rust_rockfall/target cargo clippy --all-targets --all-features -- -D warnings`;
  `CARGO_TARGET_DIR=/Users/fuhrer/Desktop/rust_rockfall/target cargo test`;
  `CARGO_TARGET_DIR=/Users/fuhrer/Desktop/rust_rockfall/target cargo run -- verify --all`;
  `CARGO_TARGET_DIR=/Users/fuhrer/Desktop/rust_rockfall/target cargo run -- validate --all`;
  `CARGO_TARGET_DIR=/Users/fuhrer/Desktop/rust_rockfall/target UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest discover -s tests -p 'test_*.py'`;
  `CARGO_TARGET_DIR=/Users/fuhrer/Desktop/rust_rockfall/target UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/check_repo_consistency.py`;
  `CARGO_TARGET_DIR=/Users/fuhrer/Desktop/rust_rockfall/target scripts/git-hooks/pre-commit`.
- Reviewer notes: No physics, defaults, sampling weights, generated outputs,
  raw/public/private geodata, annual frequency support, physical probability
  support, calibration, risk/exposure semantics, SLURM/MPI/GPU code, or
  operational claims are changed.
- Decision: ACCEPT if final checks pass; Target 11 is now represented by a
  checked `blocked_missing_inputs` evidence record rather than an unrecorded
  failed local attempt.
- Next proposed milestone: Regenerate or restore the ignored processed DEM,
  private frozen validation case, scenario table, prior gate trajectories, and
  prior hazard manifest, then rerun the target-scale gate and replace the
  blocker with executed or inconclusive evidence.

### M049

- Milestone id: M049.
- Roadmap item: Target 11 scalable conditional target-scale gate evidence.
- Hypothesis/objective: Regenerate the ignored Tschamut inputs, run the selected
  target-scale conditional workflow, and replace the `blocked_missing_inputs`
  record with executed or inconclusive evidence.
- Initial gap assessment: Raw public Tschamut and swissALTI3D inputs were
  present locally. The processed public DEM, conditional source/scenario
  sidecars, private target case, validation outputs, and hazard outputs had to
  be regenerated under ignored paths. Validation-runner `ensemble_execution`
  provenance was expected to require careful interpretation because observed
  multi-release validation outputs and the local parallel ensemble path are not
  identical.
- Files changed:
  `validation/pilot_runs/tschamut_public_scalable_conditional_target_gate_v1.yaml`,
  `scripts/validate_scalable_conditional_target_gate.py`,
  `tests/test_scalable_conditional_target_gate.py`,
  `docs/tschamut_public_scalable_conditional_target_gate.md`,
  `scripts/check_repo_consistency.py`,
  `docs/next_development_targets.md`,
  `docs/real_case_intensity_frequency_implementation_roadmap.md`,
  `docs/roadmap_recommendation_matrix.md`,
  `docs/agent_work_log.md`.
- Local ignored inputs and outputs regenerated:
  `data/processed/swisstopo/tschamut_public_pilot/input/*`,
  `validation/private/tschamut_public_pilot/target_gate_v1/*`,
  `hazard/results/tschamut_public_pilot/target_gate_v1/*`, and
  `hazard/results/tschamut_public_pilot/target_gate_v1_worker1/*`.
- Implementation summary: The selected target-gate record now reports
  `gate_status: inconclusive`. It records restored/regenerated inputs, a
  completed 1,000-trajectory observed-release validation run, summary-only
  conditional hazard layers, suppressed full curve-table output, reducer chunk
  metadata, output file/byte counts, runtime and Darwin memory sidecars,
  checksums, and 1-vs-2 worker reducer parity for compared outputs. The
  validator and tests now enforce executed/inconclusive evidence fields in
  addition to the original blocked-record semantics.
- Checks run:
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/prepare_tschamut_public_benchmark.py --output-root data/processed/swisstopo/tschamut_public_pilot --padding-m 250 --force`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/validate_public_real_site_geodata_manifest.py data/processed/swisstopo/tschamut_public_pilot_manifest.yaml`;
  `cargo run -- validate --case validation/private/tschamut_public_pilot/target_gate_v1/tschamut_public_target_gate_case.yaml`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/build_hazard_layers.py ... --conditional-curve-export summary-only --reducer-workers 2 --no-plots`;
  matching 1-worker hazard reducer parity command in
  `hazard/results/tschamut_public_pilot/target_gate_v1_worker1`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/validate_scalable_conditional_target_gate.py validation/pilot_runs/tschamut_public_scalable_conditional_target_gate_v1.yaml --format json`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest tests.test_scalable_conditional_target_gate`.
- Reviewer notes: The run does not tune parameters, change physics, change
  defaults, add annual/physical/risk semantics, or commit generated/raw/private
  artifacts. The target evidence remains inconclusive because convergence has
  not been accepted, manual GIS/QGIS visual QA remains incomplete, obstacle
  context remains limiting, and `ensemble_execution` provenance covers only the
  auxiliary single-release 100-trajectory ensemble path rather than all 1,000
  observed-release validation outputs.
- Decision: ACCEPT if final repository checks pass; Target 11 now has executed
  but inconclusive evidence and no longer has a missing-input blocker.
- Next proposed milestone: Reassess the selected ensemble-size gate against the
  new target evidence, keeping convergence, manual GIS QA, obstacle context, and
  validation-runner provenance limitations visible.

### M050

- Milestone id: M050.
- Roadmap item: Target 12 selected ensemble-size gate reassessment.
- Hypothesis/objective: Reassess the selected Tschamut ensemble-size gate using
  the newly executed but inconclusive target-scale evidence, and either keep
  scale-up blocked or authorize exactly one further diagnostic step with
  explicit limitations.
- Initial gap assessment: Target-scale execution evidence now exists, but the
  evidence record is `inconclusive`: target-vs-small-gate convergence has not
  been accepted, manual GIS/QGIS visual QA remains incomplete, obstacle/forest
  context remains limiting, validation-runner `ensemble_execution` provenance
  covers only the auxiliary single-release ensemble path, and validation-side
  debug outputs are large.
- Files changed:
  `validation/pilot_runs/tschamut_public_ensemble_feasibility_v1.yaml`,
  `scripts/validate_pilot_ensemble_feasibility.py`,
  `tests/test_pilot_ensemble_feasibility.py`,
  `docs/tschamut_public_ensemble_feasibility.md`,
  `docs/next_development_targets.md`,
  `docs/real_case_intensity_frequency_implementation_roadmap.md`,
  `docs/roadmap_recommendation_matrix.md`,
  `docs/agent_work_log.md`.
- Implementation summary: The ensemble feasibility record remains `decision:
  no_go`, but now explicitly reviews Target 11 evidence: 1,000 target
  trajectories, summary-only curves, runtime/memory/file/byte counts, checksums,
  and 1-vs-2 reducer parity. The validator now requires target-scale evidence
  fields and rejects missing target-scale/provenance blockers. Roadmap docs now
  identify manual GIS QA, obstacle context, validation-runner provenance scope,
  and validation debug output volume as the next blockers rather than missing
  target execution.
- Checks run:
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/validate_pilot_ensemble_feasibility.py validation/pilot_runs/tschamut_public_ensemble_feasibility_v1.yaml --format json`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest tests.test_pilot_ensemble_feasibility`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/check_repo_consistency.py`;
  `git diff --check`;
  `CARGO_TARGET_DIR=/Users/fuhrer/Desktop/rust_rockfall/target cargo fmt --check`;
  `CARGO_TARGET_DIR=/Users/fuhrer/Desktop/rust_rockfall/target cargo clippy --all-targets --all-features -- -D warnings`;
  `CARGO_TARGET_DIR=/Users/fuhrer/Desktop/rust_rockfall/target cargo test`;
  `CARGO_TARGET_DIR=/Users/fuhrer/Desktop/rust_rockfall/target cargo run -- verify --all`;
  `CARGO_TARGET_DIR=/Users/fuhrer/Desktop/rust_rockfall/target cargo run -- validate --all`;
  `CARGO_TARGET_DIR=/Users/fuhrer/Desktop/rust_rockfall/target UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest discover -s tests -p 'test_*.py'`;
  `CARGO_TARGET_DIR=/Users/fuhrer/Desktop/rust_rockfall/target UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/check_repo_consistency.py`;
  `CARGO_TARGET_DIR=/Users/fuhrer/Desktop/rust_rockfall/target scripts/git-hooks/pre-commit`.
- Reviewer notes: No physics, defaults, sampling weights, generated outputs,
  raw/public/private geodata, annual frequency support, physical probability
  support, calibration, risk/exposure semantics, SLURM/MPI/GPU code, or
  operational claims are changed.
- Decision: ACCEPT if final checks pass; selected ensemble-size increase remains
  no-go after target-scale evidence review.
- Next proposed milestone: Complete or explicitly classify manual GIS/QGIS
  visual QA for the executed target-scale package, while keeping the output
  research-diagnostic and non-operational.

### M051

- Milestone id: M051.
- Roadmap item: Planning alignment — expand next-step targets after M049/M050.
- Hypothesis/objective: Capture Targets 13–15 (manual GIS QA, obstacle-context
  interpretation review, validation-runner provenance and debug output budget)
  and refresh the executive summary and recommended sequence now that
  target-scale evidence exists and ensemble increase remains no-go.
- Files changed:
  `docs/next_development_targets.md`,
  `docs/real_case_intensity_frequency_implementation_roadmap.md`,
  `docs/agent_work_log.md`.
- Implementation summary: Intro paragraph and recommended sequence now emphasize
  interpretation/provenance blockers; added explicit Target 13–15 definitions
  tied to existing pilot records and guardrails; CSCS/SLURM deferral wording
  aligned with current evidence posture.
- Checks run:
  `git diff --check`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/check_repo_consistency.py`.
- Reviewer notes: Docs-only; no simulator, validator behavior, or geodata changes.
- Decision: ACCEPT; documentation consistency checks pass.
- Next proposed milestone: Execute Target 13 (manual GIS/QGIS review record) or
  record a concrete GUI/package blocker.

### M052

- Milestone id: M052.
- Roadmap item: Target 13 manual GIS/QGIS review for the executed target-scale
  package.
- Hypothesis/objective: Replace the unclassified target-scale manual GIS/QGIS
  review gap with an explicit share-safe blocker record, without generating or
  committing package artifacts.
- Initial gap assessment: The target-scale conditional gate had executed but
  remained inconclusive, and the roadmap identified manual GIS/QGIS review as
  the highest-priority interpretation blocker. In this checkout QGIS is not
  installed and the ignored target-scale package manifests/rasters are absent,
  so visual inspection cannot honestly be completed.
- Files changed:
  `validation/pilot_runs/tschamut_public_gis_visual_qa_v1.yaml`,
  `scripts/validate_pilot_gis_visual_qa.py`,
  `tests/test_pilot_gis_visual_qa.py`,
  `docs/tschamut_public_pilot_gis_package_review.md`,
  `docs/tschamut_public_scalable_conditional_target_gate.md`,
  `docs/tschamut_public_ensemble_feasibility.md`,
  `validation/pilot_runs/tschamut_public_scalable_conditional_target_gate_v1.yaml`,
  `validation/pilot_runs/tschamut_public_ensemble_feasibility_v1.yaml`,
  `docs/real_case_intensity_frequency_implementation_roadmap.md`,
  `docs/next_development_targets.md`,
  `docs/agent_work_log.md`.
- Implementation summary: Retargeted the selected visual-QA record to the
  target-scale package paths and classified automated package QA, manual QGIS
  visual QA, and overall visual-QA acceptance as `blocked`. The validator now
  accepts `blocked` selected-review statuses only with explicit blockers, and
  tests cover the selected blocked record and a synthetic blocked record.
  Related target-gate and ensemble-feasibility records now state that manual
  GIS/QGIS review is blocked by absent QGIS and absent ignored target package
  artifacts.
- Checks run:
  `which qgis` returned no executable;
  `test -f hazard/results/tschamut_public_pilot/target_gate_v1/tschamut_public_scalable_conditional_target_gate_v1_pilot_gis_package_manifest.json` returned `missing`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/validate_pilot_gis_visual_qa.py validation/pilot_runs/tschamut_public_gis_visual_qa_v1.yaml --format json`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest tests.test_pilot_gis_visual_qa`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/validate_pilot_ensemble_feasibility.py validation/pilot_runs/tschamut_public_ensemble_feasibility_v1.yaml --format json`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/validate_scalable_conditional_target_gate.py validation/pilot_runs/tschamut_public_scalable_conditional_target_gate_v1.yaml --format json`;
  `git diff --check`;
  `python3 scripts/check_repo_consistency.py` failed because system Python does
  not support `from __future__ import annotations`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/check_repo_consistency.py`;
  `cargo fmt --check`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest discover -s tests -p 'test_*.py'`;
  `cargo clippy --all-targets --all-features -- -D warnings`;
  `cargo test`;
  `cargo run -- verify --all`;
  `cargo run -- validate --all`;
  `scripts/git-hooks/pre-commit`.
- Reviewer notes: No physics, defaults, sampling weights, generated outputs,
  raw/public/private geodata, annual frequency support, physical probability
  support, risk/exposure semantics, QGIS project, screenshots, or operational
  claims are added.
- Decision: ACCEPT if final checks pass; Target 13 is complete as an explicit
  blocked review record, not as a passed visual QA.
- Next proposed milestone: Review forest and obstacle context for the selected
  Tschamut target-scale corridor, still without adding obstacle physics or
  tuning parameters.

### M053

- Milestone id: M053.
- Roadmap item: Target 14 forest and obstacle context review for target-scale
  Tschamut interpretation.
- Hypothesis/objective: Retarget the obstacle-context scope from a small gate
  scoping note to the executed target-scale package, and make missing public
  context crops an explicit limiting blocker without adding obstacle physics or
  tuning.
- Initial gap assessment: The checked-in obstacle-scope record documented
  public context requirements and claim boundaries, but it did not explicitly
  bind the review to the executed target-scale gate, the blocked target package
  visual-QA record, or a machine-checked local context-artifact absence.
- Files changed:
  `validation/pilot_runs/tschamut_public_obstacle_scope_v1.yaml`,
  `scripts/validate_pilot_obstacle_scope.py`,
  `tests/test_pilot_obstacle_scope.py`,
  `docs/tschamut_public_obstacle_context_scope.md`,
  `docs/tschamut_public_scalable_conditional_target_gate.md`,
  `docs/tschamut_public_ensemble_feasibility.md`,
  `validation/pilot_runs/tschamut_public_scalable_conditional_target_gate_v1.yaml`,
  `validation/pilot_runs/tschamut_public_ensemble_feasibility_v1.yaml`,
  `docs/real_case_intensity_frequency_implementation_roadmap.md`,
  `docs/next_development_targets.md`,
  `scripts/check_repo_consistency.py`,
  `docs/agent_work_log.md`.
- Implementation summary: The selected obstacle-scope record now targets
  `tschamut_public_scalable_conditional_target_gate_v1`, records
  `blocked_missing_context_layers` for local target-scale context review, keeps
  omission classified as `limiting`, lists required public context layers, and
  preserves no-obstacle-physics, no-risk, no-annual-frequency, and
  no-physical-probability boundaries. The validator and tests now reject
  blocked reviews with reviewed artifacts and acceptable classifications without
  reviewed target context. The repository consistency script checks that the
  target-scale obstacle-scope contract remains present.
- Checks run:
  `test -e data/processed/swisstopo/tschamut_public_pilot/context`;
  `find data/processed/swisstopo/tschamut_public_pilot -maxdepth 3 -type f`;
  `find data/raw -maxdepth 3 -type f`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/validate_pilot_obstacle_scope.py validation/pilot_runs/tschamut_public_obstacle_scope_v1.yaml --format json`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest tests.test_pilot_obstacle_scope`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/validate_pilot_ensemble_feasibility.py validation/pilot_runs/tschamut_public_ensemble_feasibility_v1.yaml --format json`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/validate_scalable_conditional_target_gate.py validation/pilot_runs/tschamut_public_scalable_conditional_target_gate_v1.yaml --format json`;
  `git diff --check`;
  `python3 scripts/check_repo_consistency.py` failed because system Python does
  not support `from __future__ import annotations`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/check_repo_consistency.py`;
  `cargo fmt --check`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest discover -s tests -p 'test_*.py'`;
  `cargo clippy --all-targets --all-features -- -D warnings`;
  `cargo test`;
  `cargo run -- verify --all`;
  `cargo run -- validate --all`;
  `scripts/git-hooks/pre-commit`.
- Reviewer notes: No simulator behavior, physics parameters, defaults, raw
  geodata, generated hazard products, annual frequency semantics, physical
  probability semantics, risk/exposure semantics, or operational claims are
  added.
- Decision: ACCEPT if final checks pass; Target 14 is complete as a limiting
  target-scale review with an explicit missing-context-artifact blocker, not as
  a resolved obstacle analysis.
- Next proposed milestone: Implement Target 15, validation-runner provenance
  and debug output-budget tightening for the selected Tschamut target-scale
  evidence.
