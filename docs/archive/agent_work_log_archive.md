# Agent Work Log Archive

This archive contains the pre-refactor agent work log exactly as it existed
before the active log was normalized into an append-only TB sequence. It keeps
old planning notes, M-series milestone history, backlog refill notes, review
triage, and other non-TB material out of the active worker log.

Future workers should not append here. Append new work only to
`docs/agent_work_log.md` using the template in that file.

---

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

### TB-057 Physical Credibility Evidence Requirements

- Milestone id: TB-057.
- Roadmap item: Map physical credibility data requirements to concrete
  evidence sources.
- Hypothesis/objective: The current `not_established` physical-credibility
  boundary can be translated into a durable requirements matrix that names
  future acquisition classes without turning diagnostic or holdout fixtures
  into calibration evidence.
- Files intended to change: `scripts/map_physical_credibility_evidence_requirements.py`,
  `tests/test_physical_credibility_evidence_requirements.py`,
  `docs/tschamut_public_conditional_pilot_gate_report.md`,
  `docs/public_real_site_geodata_preparation.md`,
  `docs/swisstopo_data_strategy.md`,
  `docs/task_backlog.md`,
  `docs/agent_work_log.md`
- Implementation summary: Added a read-only physical-credibility evidence
  requirements helper that maps Tschamut diagnostic evidence, Chant Sura
  held-out validation evidence, and the swisstopo context stack into concrete
  future acquisition classes. The report keeps the current boundaries
  conservative: `physical_credibility_requirements_status=mapped_current_gaps`,
  `current_physical_credibility_status=not_established`,
  `calibration_status=missing`, `validation_status=partial`, and
  `intensity_frequency_status=deferred_unsupported`.
- Checks run: pending
- Reviewer notes: The helper is descriptive only. It does not calibrate,
  fit parameters, download geodata, run simulations, or authorize annual,
  physical-probability, risk, exposure, vulnerability, scale-up, or
  operational claims.
- Decision: completed.
- Next proposed milestone: backlog refill needed.

### TB-053 Closure Gap Deltas

- Milestone id: TB-053.
- Roadmap item: Quantify closure-gap deltas from spatial uncertainty masks.
- Hypothesis/objective: The measured spatial decomposition can be translated
  into a concise delta report that shows why the pilot remains
  `inconclusive_conditional_diagnostic` and why the current evidence is closer
  to deferred than to no-go.
- Files intended to change: `scripts/summarize_tschamut_closure_gap_deltas.py`,
  `tests/test_tschamut_closure_gap_deltas.py`,
  `docs/tschamut_public_conditional_pilot_gate_report.md`,
  `docs/tschamut_public_same_scale_uncertainty_envelope.md`,
  `docs/task_backlog.md`,
  `docs/agent_work_log.md`
- Implementation summary: Added a read-only closure-gap delta helper that
  composes the canonical diagnostic interpretation with the measured
  spatial decomposition. The report now lists closure-limiting and
  deferrable layers, compares kinetic energy and jump height against the
  deferrable velocity layer, and keeps the current evidence conservative:
  `closure_gap_status=measured_gaps_remain`, `closure_status=inconclusive`,
  and `interpretation_status=inconclusive_conditional_diagnostic`.
- Checks run:
  `PYENV_VERSION=system uv run python -m py_compile scripts/summarize_tschamut_closure_gap_deltas.py scripts/summarize_tschamut_conditional_pilot_closure.py scripts/summarize_tschamut_conditional_diagnostic_interpretation.py scripts/summarize_spatial_same_scale_uncertainty.py tests/test_tschamut_closure_gap_deltas.py tests/test_tschamut_conditional_pilot_closure.py tests/test_tschamut_conditional_diagnostic_interpretation.py tests/test_spatial_same_scale_uncertainty.py`
  passed.
  `PYENV_VERSION=system uv run python -m unittest tests.test_tschamut_closure_gap_deltas tests.test_tschamut_conditional_pilot_closure tests.test_tschamut_conditional_diagnostic_interpretation tests.test_spatial_same_scale_uncertainty`
  passed.
  `PYENV_VERSION=system uv run python scripts/summarize_tschamut_closure_gap_deltas.py --format json`
  passed.
  `PYENV_VERSION=system uv run python scripts/summarize_tschamut_closure_gap_deltas.py --format text`
  passed.
  `PYENV_VERSION=system uv run python scripts/summarize_tschamut_conditional_pilot_closure.py --format json`
  passed.
  `PYENV_VERSION=system uv run python scripts/summarize_tschamut_conditional_diagnostic_interpretation.py --format json`
  passed.
  `PYENV_VERSION=system uv run python scripts/summarize_spatial_same_scale_uncertainty.py --format json`
  passed.
- Reviewer notes: The helper is descriptive only. It introduces no new
  acceptance criteria, no ensemble, no physics changes, and no operational
  or scale-up claims.
- Decision: completed.
- Next proposed milestone: TB-054.

### TB-052 Support And Nodata Uncertainty Decomposition

- Milestone id: TB-052.
- Roadmap item: Decompose support/nodata uncertainty for the closure-limiting
  same-scale layers.
- Hypothesis/objective: The closure-limiting spatial uncertainty can be split
  into a measurable support/nodata component and a shared-support magnitude
  component without changing the underlying closure status.
- Files intended to change: `scripts/summarize_spatial_same_scale_uncertainty.py`,
  `scripts/summarize_tschamut_conditional_pilot_closure.py`,
  `tests/test_spatial_same_scale_uncertainty.py`,
  `tests/test_tschamut_conditional_pilot_closure.py`,
  `docs/tschamut_public_same_scale_uncertainty_envelope.md`,
  `docs/tschamut_public_conditional_pilot_gate_report.md`,
  `docs/task_backlog.md`,
  `docs/agent_work_log.md`
- Implementation summary: Added a read-only decomposition for
  `max_kinetic_energy`, `max_jump_height`, and `velocity_exceedance_5mps`
  that reports support-only, nodata-only, and shared-support magnitude counts,
  high-uncertainty fractions, and compact decomposition classes. Threaded the
  new decomposition through the closure helper and canonical diagnostic
  interpretation helper. Real same-scale evidence now shows
  `max_kinetic_energy` as overall nodata/support-dominated but
  high-uncertainty shared-support magnitude dominated, `max_jump_height` as
  mixed, and `velocity_exceedance_5mps` as deferrable with shared-support
  magnitude at the selected high-uncertainty cells.
- Checks run:
  `PYENV_VERSION=system uv run python -m py_compile scripts/summarize_spatial_same_scale_uncertainty.py scripts/summarize_tschamut_conditional_pilot_closure.py tests/test_spatial_same_scale_uncertainty.py tests/test_tschamut_conditional_pilot_closure.py`
  passed.
  `PYENV_VERSION=system uv run python -m unittest tests.test_spatial_same_scale_uncertainty tests.test_tschamut_conditional_pilot_closure`
  passed.
  `PYENV_VERSION=system uv run python scripts/summarize_spatial_same_scale_uncertainty.py --format json`
  passed.
  `PYENV_VERSION=system uv run python scripts/summarize_spatial_same_scale_uncertainty.py --format text`
  passed.
  `PYENV_VERSION=system uv run python scripts/summarize_tschamut_conditional_pilot_closure.py --format json`
  passed.
  `PYENV_VERSION=system uv run python scripts/summarize_tschamut_conditional_diagnostic_interpretation.py --format json`
  passed.
- Reviewer notes: This keeps the pilot conservative and non-operational. The
  closure status remains `inconclusive`.
- Decision: completed.
- Next proposed milestone: TB-053.

### TB-047 Portable Source-Scenario Semantics Audit

- Milestone id: TB-047.
- Roadmap item: Harden portable source-zone and scenario semantics for the
  concrete Chant Sura / Flüelapass candidate.
- Hypothesis/objective: The Tschamut source-zone / scenario contract can be
  separated into reusable semantics, Tschamut-specific heuristics, and
  synthetic Chant Sura contract fixtures without running a second-site
  ensemble.
- Files intended to change: `scripts/audit_multisite_source_scenario_contract.py`,
  `tests/test_multisite_source_scenario_contract.py`, `docs/task_backlog.md`,
  `docs/public_real_site_geodata_preparation.md`, `docs/swisstopo_data_strategy.md`,
  `docs/agent_work_log.md`, `validation/policies/chant_sura_fluelapass_portability_example_v1_source_scenario_policy_v1.yaml`
- Implementation summary: Added a machine-readable semantic portability
  matrix, explicit contract-fixture labels for the Chant Sura policy, and
  doc/backlog updates that keep the candidate at deferred public-context
  readiness.
- Checks run: pending
- Reviewer notes: No second-site ensemble or hazard build was run.
- Decision: completed
- Next proposed milestone: TB-048

### Backlog Reprioritization After External Assessment

- Milestone id: backlog reprioritization after external assessment.
- Roadmap item: Reorder the active backlog around Swiss-wide portability and
  scientifically interpretable uncertainty.
- Hypothesis/objective: The external assessment is directionally correct, but
  its numbering is stale because the placeholder and concrete second-site
  manifest work has already advanced. The next highest-value task should be a
  multi-site source-zone/scenario contract audit, followed by multi-seed
  same-scale uncertainty characterization.
- Files intended to change: `docs/task_backlog.md`, `docs/decision_log.md`,
  `docs/agent_work_log.md`
- Implementation summary: Added TB-030 as the multi-site source-zone and
  scenario contract audit, rewrote the sampling task as TB-031 multi-seed
  same-scale uncertainty envelope, and renumbered the command-plan, GIS/COG,
  and reducer/runtime tasks to TB-032 through TB-034. Updated the durable
  decision log to record why source/scenario portability now precedes more
  Tschamut-specific sampling work.
- Checks run:
  `git diff --check`
  passed.
  `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  passed.
  `scripts/git-hooks/pre-commit`
  passed.
- Reviewer notes: This is a backlog prioritization update only. It does not
  change simulator physics, thresholds, release assumptions, sampling weights,
  validation cases, or claim boundaries.
- Decision: ACCEPT.
- Next proposed milestone: TB-030.

### Backlog Refill After Portability Preflight

- Milestone id: backlog refill after TB-027.
- Roadmap item: Reassess repository progress against the Swiss-wide public
  geodata hazard-map workflow goal and refill the executable backlog.
- Hypothesis/objective: The active queue should reflect the latest measured
  state: Tschamut artifacts are ready, convergence is measured but
  inconclusive, sampling sensitivity and output pressure are measured, context
  remains limiting/unresolved, case regeneration is deterministic, and
  second-site portability has a metadata-only preflight.
- Files intended to change: `docs/task_backlog.md`, `docs/decision_log.md`,
  `docs/agent_work_log.md`
- Implementation summary: Refilled the active backlog with TB-028 through
  TB-033. The new sequence prioritizes a concrete second-site manifest,
  same-size alternate-seed sampling evidence, a reusable sampling-uncertainty
  summary, command-plan consolidation, GIS/COG package readiness, and bounded
  reducer/runtime scaling measurement. Updated the capability-gap analysis to
  remove stale missing-artifact blockers and to keep scale-up and operational
  claims unauthorized.
- Checks run:
  `git diff --check`
  passed.
  `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  passed.
  `scripts/git-hooks/pre-commit`
  passed.
- Reviewer notes: This pass changes planning state only. It does not alter
  simulator physics, thresholds, sampling weights, release assumptions,
  baselines, validation cases, or claim boundaries.
- Decision: ACCEPT.
- Next proposed milestone: TB-028.

### Worker Efficiency Consolidation

- Milestone id: worker efficiency consolidation after TB-022.
- Roadmap item: Improve future worker prompt efficiency without adding a new
  governance layer.
- Hypothesis/objective: Future Tschamut same-scale workers should avoid
  repeatedly rediscovering artifact readiness, command plans, stale blocked
  states, pyenv issues, and known pre-push behavior.
- Files intended to change: `AGENTS.md`, `docs/task_backlog.md`,
  `docs/agent_work_log.md`
- Implementation summary: Added a `Tschamut Worker Fast Path` to `AGENTS.md`
  that makes the same-scale artifact readiness preflight the first command for
  relevant tasks, identifies canonical evidence scripts, warns that
  `agent_work_log.md` is non-chronological, and records bounded overlap,
  `PYENV_VERSION=system`, and known parquet pre-push guidance. Added matching
  backlog-protocol wording so future task prompts can point workers at the
  preflight instead of asking them to manually rediscover paths.
- Checks run:
  `git diff --check`
  passed.
  `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  passed.
  `scripts/git-hooks/pre-commit`
  passed.

### TB-025

- Milestone id: TB-025.
- Roadmap item: Run A Bounded Same-Scale Sampling Sensitivity Probe.
- Hypothesis/objective: A small bounded same-scale probe can show whether
  the target-vs-gate disagreement shrinks under controlled sampling without
  changing physics, thresholds, release assumptions, or sampling weights.
- Files intended to change: `docs/task_backlog.md`,
  `docs/tschamut_public_conditional_pilot_gate_report.md`,
  `docs/tschamut_public_same_scale_uncertainty_envelope.md`,
  `docs/agent_work_log.md`
- Implementation summary: Ran the readiness preflight, then attempted a
  summary-only bounded probe. The summary-only probe was blocked for hazard
  rebuilding because trajectory CSV output was not available, so the measured
  sensitivity probe used the bounded full-output case with 12 trajectories and
  the same seed (`34014`). The probe built hazard layers successfully and was
  compared against both gate and target same-scale artifacts. The dominant
  disagreement layers remained `max_kinetic_energy` and `max_jump_height`,
  but their differences shrank relative to the earlier gate-vs-target
  comparison, which supports measured sampling sensitivity rather than an
  accepted convergence claim.
- Evidence streams consumed: the readiness preflight, the summary-only probe
  case and manifest, the bounded full-output probe case and manifest, the
  probe hazard artifacts, the gate and target manifests, and the JSON
  comparison output from `scripts/compare_hazard_map_convergence.py`.
- Classification: `sampling_sensitivity_measured`; `scale_up_authorized`
  remains false and `operational_claims_allowed` remains false.
- Uncertainty reduced: same-scale disagreement now has a measured bounded
  sampling-sensitivity component, and the dominant layers shrink under the
  12-trajectory probe.
- Remaining uncertainty: the probe did not collapse the disagreement, so
  convergence remains conservative and non-operational.
- Checks run:
  `PYENV_VERSION=system uv run python scripts/check_same_scale_artifact_readiness.py --format json`
  passed.
  `PYENV_VERSION=system CARGO_TARGET_DIR=/tmp/rust-rockfall-target timeout 600 cargo run -- validate --case validation/private/tschamut_public_pilot/sampling_sensitivity_v1/tschamut_public_sampling_sensitivity_v1_case.yaml`
  passed, but hazard rebuilding was blocked because trajectory CSV output was
  unavailable.
  `PYENV_VERSION=system CARGO_TARGET_DIR=/tmp/rust-rockfall-target timeout 600 cargo run -- validate --case validation/private/tschamut_public_pilot/sampling_sensitivity_v1_full/tschamut_public_sampling_sensitivity_v1_full_case.yaml`
  passed.
  `PYENV_VERSION=system timeout 600 uv run python scripts/build_hazard_layers.py --case validation/private/tschamut_public_pilot/sampling_sensitivity_v1_full/tschamut_public_sampling_sensitivity_v1_full_case.yaml --output-dir hazard/results/tschamut_public_pilot/sampling_sensitivity_v1_full`
  passed.
  `PYENV_VERSION=system uv run python scripts/audit_local_artifacts.py validation/private/tschamut_public_pilot/sampling_sensitivity_v1_full hazard/results/tschamut_public_pilot/sampling_sensitivity_v1_full`
  passed.
  `PYENV_VERSION=system uv run python scripts/compare_hazard_map_convergence.py hazard/results/tschamut_public_pilot/sampling_sensitivity_v1_full/validation_tschamut_public_sampling_sensitivity_v1_full_manifest.json hazard/results/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_manifest.json hazard/results/tschamut_public_pilot/target_gate_v1/validation_tschamut_public_target_gate_v1_manifest.json --format json`
  passed.
  `git diff --check`
  passed.
  `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  passed.
  `scripts/git-hooks/pre-commit`
  passed.
- Reviewer notes: This is a bounded sensitivity measurement only; it does not
  authorize scale-up or operational interpretation.
- Decision: ACCEPT_WITH_LIMITATIONS.
- Next proposed milestone: TB-026.

### TB-024

- Milestone id: TB-024.
- Roadmap item: Diagnose Target-Vs-Gate Spatial Disagreement Drivers.
- Implementation summary: Reused the existing convergence diagnostic to
  separate the same-scale disagreement drivers without rerunning larger
  ensembles. The target and gate manifolds share the same grid geometry,
  scenario table, source-zone metadata, and cellwise layer keys, but the
  comparison remains `ok` and conservative because the shared sampled outputs
  still diverge numerically. The dominant disagreement is `max_kinetic_energy`
  with identical nonzero support but very large magnitude difference; the next
  strongest driver is `max_jump_height`, which combines magnitude, support,
  and nodata differences; the velocity exceedance layers show smaller but
  measurable footprint shifts.
- Evidence streams consumed: the readiness preflight, the restored gate and
  target manifests, the gate and target case YAMLs, the scenario table, the
  source-zone metadata, and the JSON output from
  `scripts/compare_hazard_map_convergence.py`.
- Classification: `inconclusive` convergence with `scale_up_authorized`
  remaining false and `operational_claims_allowed` remaining false.
- Uncertainty reduced: the disagreement is not coming from grid geometry or
  scenario/source mismatch alone; it is concentrated in shared-output numeric
  divergence plus a smaller nodata/support effect in the maximum layers.
- Remaining uncertainty: the repo still needs a bounded next measurement to
  test whether the differences shrink under a controlled sampling-sensitivity
  probe.
- Checks run:
  `PYENV_VERSION=system uv run python scripts/check_same_scale_artifact_readiness.py --format json`
  passed.
  `PYENV_VERSION=system uv run python scripts/compare_hazard_map_convergence.py hazard/results/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_manifest.json hazard/results/tschamut_public_pilot/target_gate_v1/validation_tschamut_public_target_gate_v1_manifest.json --format json`
  passed.
  `git diff --check`
  passed.
  `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  passed.
  `scripts/git-hooks/pre-commit`
  passed.
- Reviewer notes: This is execution guidance only; it does not change
  simulator physics, thresholds, baselines, release assumptions, or claim
  boundaries.
- Decision: ACCEPT.
- Next proposed milestone: TB-023.

### Backlog Refill After Same-Scale Pilot Progress

- Milestone id: backlog refill after TB-021.
- Roadmap item: Reassess project progress and refill executable backlog after
  restored same-scale artifacts, measured convergence, target-side output
  reduction, and hazard-context overlap evidence.
- Hypothesis/objective: The active backlog should stop treating missing
  target-side artifacts as the dominant blocker and instead prioritize measured
  uncertainty reduction, context-overlap broadening, reproducible case
  regeneration, and Swiss public-geodata portability.
- Files intended to change: `docs/task_backlog.md`, `docs/decision_log.md`,
  `docs/agent_work_log.md`
- Implementation summary: Updated the backlog capability-gap analysis to
  reflect that target-side artifacts are restored, target-vs-gate convergence
  is measured but inconclusive, target-side `summary_only` output reduction is
  measured, and hazard-context overlap is measured only for a narrow top-cell
  envelope. Preserved in-flight TB-022 and added focused follow-up tasks for a
  broader overlap envelope, disagreement-driver diagnosis, bounded sampling
  sensitivity, reproducible case regeneration, and second-site public-geodata
  portability. Updated the durable decision log so the target-vs-gate state is
  no longer recorded as missing-manifest blocked.
- Checks run:
  `git diff --check`
  passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run --with PyYAML python scripts/check_repo_consistency.py`
  passed.
  `scripts/git-hooks/pre-commit`
  passed.
- Reviewer notes: This is a backlog-refill pass only; it does not change
  simulator physics, thresholds, baselines, release assumptions, or
  operational claim boundaries.
- Decision: ACCEPT.
- Next proposed milestone: TB-022, already in flight; otherwise TB-023.

### TB-018 Target Same-Scale Artifact Restore

- Milestone id: TB-018 target same-scale artifact restore.
- Roadmap item: Regenerate Target-Side Same-Scale Tschamut Inputs And Hazard Artifacts.
- Hypothesis/objective: The missing target-side same-scale case, validation
  manifest, hazard manifest, and referenced grids can be regenerated from the
  frozen public inputs without changing physics, thresholds, release
  assumptions, sampling weights, or ensemble size.
- Files intended to change: `validation/private/tschamut_public_pilot/target_gate_v1/tschamut_public_target_gate_case.yaml`, `docs/tschamut_public_conditional_pilot_gate_report.md`, `docs/agent_work_log.md`
- Implementation summary: Reconstructed the ignored target private case from
  the frozen target-gate record and staged public inputs, then reran target
  validation and hazard post-processing under ignored paths. The first cargo
  run failed in the existing target directory with an unrelated parquet rlib
  artifact error, so the run was repeated with a fresh
  `CARGO_TARGET_DIR=/tmp/rust-rockfall-target`. The refreshed target hazard
  manifest now exposes the same 22 cell-wise layers as the gate manifest, and
  the readiness comparison between the gate and target hazard manifests
  completed successfully as a readiness probe. The target side remains
  conditional and non-operational.
- Checks run:
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/audit_local_artifacts.py validation/private/tschamut_public_pilot/target_gate_v1 hazard/results/tschamut_public_pilot/target_gate_v1`
  reported `validation/private/tschamut_public_pilot/target_gate_v1` with
  `2007` files / `571384147` bytes and
  `hazard/results/tschamut_public_pilot/target_gate_v1` with `56` files /
  `79160991` bytes.
  `CARGO_TARGET_DIR=/tmp/rust-rockfall-target cargo run -- validate --case validation/private/tschamut_public_pilot/target_gate_v1/tschamut_public_target_gate_case.yaml`
  passed after the fresh build directory was used.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/build_hazard_layers.py --case validation/private/tschamut_public_pilot/target_gate_v1/tschamut_public_target_gate_case.yaml --output-dir hazard/results/tschamut_public_pilot/target_gate_v1 --grid-xmin 2696376.0 --grid-ymin 1167384.0 --grid-ncols 300 --grid-nrows 304 --grid-cell-size 2.0 --map-product-id tschamut_public_scalable_conditional_target_gate_v1 --probability-mode sampling_weighted_conditional --normalization-scope conditioned_on_filter --source-zone-metadata-path data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_source_zone_metadata_v1.yaml --scenario-table-path data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_scenario_table_v1.csv --map-package-manifest-json hazard/results/tschamut_public_pilot/target_gate_v1/tschamut_public_scalable_conditional_target_gate_v1_map_package_manifest.json --export-geotiff --pilot-gis-package --pilot-gis-package-manifest-json hazard/results/tschamut_public_pilot/target_gate_v1/tschamut_public_scalable_conditional_target_gate_v1_pilot_gis_package_manifest.json --pilot-gis-qa-status not-run --pilot-gis-qa-note \"Manual GIS/QGIS inspection has not been run for this generated package.\" --reducer-workers 2 --no-plots --conditional-curve-export summary-only --grid-csv-export none --diagnostics validation/private/tschamut_public_pilot/target_gate_v1/validation_tschamut_public_target_gate_v1_metrics.json --trajectory validation/private/tschamut_public_pilot/target_gate_v1/validation_tschamut_public_target_gate_v1_trajectory.csv --ensemble-trajectories-dir validation/private/tschamut_public_pilot/target_gate_v1/validation_tschamut_public_target_gate_v1_trajectories --deposition validation/private/tschamut_public_pilot/target_gate_v1/validation_tschamut_public_target_gate_v1_deposition.csv --ensemble-impact-events-dir validation/private/tschamut_public_pilot/target_gate_v1/validation_tschamut_public_target_gate_v1_impacts --kinetic-energy-exceedance-j 1000.0 --kinetic-energy-exceedance-j 10000.0 --jump-height-exceedance-m 0.5 --jump-height-exceedance-m 1.0 --jump-height-exceedance-m 2.0 --velocity-exceedance-mps 5.0 --velocity-exceedance-mps 10.0`
  passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/compare_hazard_map_convergence.py hazard/results/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_manifest.json hazard/results/tschamut_public_pilot/target_gate_v1/validation_tschamut_public_target_gate_v1_manifest.json --format json`
  returned `ok` readiness metrics with `22` shared cell-wise layers and
  `cellwise_shared_layer_count: 22`.
- Reviewer notes: The target artifact chain is now locally present under
  ignored paths. The comparison probe is a readiness check only; it does not
  replace TB-019’s interpretation step.
- Decision: COMPLETED_WITH_LIMITATIONS.
- Next proposed milestone: TB-019.

### TB-017 Target Manifest Restore Block

- Milestone id: TB-017 target manifest restore block.
- Roadmap item: Restore The Same-Scale Target Hazard Manifest For Comparison.
- Hypothesis/objective: The current checkout either contains the target-side
  same-scale hazard manifest and referenced grid files or can record an exact
  missing-input regeneration path without redoing corridor context work.
- Files intended to change: `docs/tschamut_public_conditional_pilot_gate_report.md`, `docs/agent_work_log.md`
- Implementation summary: Audited the local checkout and confirmed that the
  target-side ignored roots are absent here: the private target case,
  validation manifest, hazard manifest, map-package manifest, pilot-GIS
  manifest, conditional curve CSV, and chunk directory are all missing, and
  the processed public inputs needed to regenerate them are also absent.
  Recorded the exact missing paths and the same command plan already used by
  the selected gate so TB-014 can be retried without ambiguity once inputs
  are restored.
- Checks run:
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/audit_local_artifacts.py validation/private/tschamut_public_pilot/target_gate_v1 hazard/results/tschamut_public_pilot/target_gate_v1`
  returned `false` for both target-side roots with `0` files and `0` bytes.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/compare_hazard_map_convergence.py hazard/results/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_manifest.json hazard/results/tschamut_public_pilot/target_gate_v1/validation_tschamut_public_target_gate_v1_manifest.json --format json`
  is the blocked comparison command and remains unavailable until the target
  manifest is restored locally.
- Reviewer notes: No context extraction or corridor review was repeated; TB-015 already measured swissTLM3D corridor relevance. This entry only records the missing target-side comparison artifacts and the regeneration path.
- Decision: BLOCKED_MISSING_INPUTS.
- Next proposed milestone: TB-014.

### TB-012/TB-013 Local Unblock

- Milestone id: TB-012/TB-013 local unblock.
- Roadmap item: Refresh Same-Scale Selected Tschamut Pilot Artifacts; Stage
  Tschamut Context Crops And Measure Real Spatial Relevance.
- Hypothesis/objective: Locally regenerate the ignored public Tschamut input
  bundle, same-scale gate outputs, summary-only validation-output probe, and
  public context evidence so the next review task has measured inputs instead
  of only blocked checklists.
- Files intended to change:
  `scripts/compare_hazard_map_convergence.py`,
  `scripts/inspect_tschamut_public_context_layers.py`,
  `tests/test_tschamut_public_context_layers.py`,
  `docs/task_backlog.md`,
  `docs/tschamut_public_conditional_pilot_gate_report.md`,
  `docs/tschamut_public_obstacle_context_scope.md`,
  `docs/agent_work_log.md`
- Implementation summary: Regenerated the public Tschamut/swissALTI3D
  processed bundle under ignored paths, staged the local private gate case,
  ran the same-scale validation and hazard builder, and added a separate
  ignored `summary_only` validation-output probe. The local full-debug gate
  produced `125` validation files / `34545900` bytes; the summary-only probe
  produced `4` files / `81425` bytes. The hazard manifest now exposes `22`
  cell-wise layers, and the convergence CLI self-check over the emitted hazard
  manifest reports zero cell-wise differences. Public context assets were
  staged under ignored paths for swissSURFACE3D Raster, SWISSIMAGE, and
  swissBUILDINGS3D; swisTLM3D remains metadata-only and unresolved because the
  matching archive is about `3136564656` bytes. The context inspector now
  reports `reviewed_local_context` with `classification: limiting` and
  surfaces the staged surface-minus-bare-earth indicators.
- Checks run:
  `cargo run -- validate --case validation/private/tschamut_public_pilot/gate_v1/tschamut_public_conditional_gate_case.yaml`
  passed.
  `cargo run -- validate --case validation/private/tschamut_public_pilot/gate_v1_summary_only/tschamut_public_conditional_gate_summary_only_case.yaml`
  passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/compare_hazard_map_convergence.py hazard/results/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_manifest.json hazard/results/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_manifest.json --format json`
  passed with `22` shared cell-wise layers and zero differences.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/summarize_bounded_validation_output_profile.py --validation-output-baseline-manifest validation/private/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_manifest.json --validation-output-reduced-manifest validation/private/tschamut_public_pilot/gate_v1_summary_only/validation_tschamut_public_conditional_gate_v1_summary_only_manifest.json --format json`
  passed and measured the local reduction.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/inspect_tschamut_public_context_layers.py --format json`
  returned the expected non-acceptable `limiting` classification with local
  context evidence.
- Reviewer notes: Generated validation, hazard, raw geodata, and processed
  context files remain ignored and uncommitted. The cell-wise convergence
  result is a same-manifest plumbing self-check, not target-vs-gate
  convergence acceptance. The local gate is a same-scale public-input refresh,
  not a replacement for the older Balfrin target-scale run.
- Decision: COMPLETED_WITH_LIMITATIONS.
- Next proposed milestone: TB-014.

### TB-013

- Milestone id: TB-013
- Roadmap item: Stage Tschamut Context Crops And Measure Real Spatial Relevance.
- Hypothesis/objective: The public-context inspector can either measure real
  staged Tschamut context crops or emit an exact blocked acquisition path
  without implying obstacle absence.
- Files intended to change:
  `scripts/inspect_tschamut_public_context_layers.py`,
  `tests/test_tschamut_public_context_layers.py`,
  `docs/tschamut_public_obstacle_context_scope.md`,
  `docs/agent_work_log.md`
- Implementation summary: Extended the inspector report with selected corridor
  metadata, spatial-relevance status, blocked reason, and conservative
  indicators for the expected public context categories. The real checkout
  still has no processed Tschamut context cache under
  `data/processed/swisstopo/tschamut_public_pilot/context/`, so the default
  inspection remains `blocked_pending_local_evidence` and prints an explicit
  acquisition checklist instead of treating missing crops as obstacle absence.
  The deterministic fixture crop remains available only as a fixture-backed
  review path.
- Checks run:
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m py_compile scripts/inspect_tschamut_public_context_layers.py tests/test_tschamut_public_context_layers.py`
  passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest tests.test_tschamut_public_context_layers tests.test_pilot_obstacle_scope`
  passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/inspect_tschamut_public_context_layers.py --format json`
  returned `blocked_pending_local_evidence` with the explicit acquisition
  checklist for the missing real crops.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/inspect_tschamut_public_context_layers.py --context-root tests/fixtures/tschamut_context_layers/available --format json`
  returned `fixture_reviewed_context` for the deterministic fixture crop only.
- Reviewer notes: No real public context crops are staged in this checkout, so
  the context review stays blocked pending local evidence. The report and docs
  now distinguish the blocked acquisition path from the fixture-only
  demonstration path.
- Decision: BLOCKED_PENDING_LOCAL_EVIDENCE.
- Next proposed milestone: TB-014.

### TB-013 swissTLM3D Follow-Up

- Milestone id: TB-013 swisstlm3d follow-up.
- Roadmap item: Stage Tschamut Context Crops And Measure Real Spatial Relevance.
- Hypothesis/objective: The downloaded swissTLM3D archive can be staged as a
  local ignored asset and reflected in the gate/context docs without turning
  archive presence into corridor-level acceptability.
- Files intended to change:
  `docs/tschamut_public_obstacle_context_scope.md`,
  `docs/tschamut_public_conditional_pilot_gate_report.md`,
  `docs/agent_work_log.md`
- Implementation summary: Confirmed that the swissTLM3D archive is now present
  under the ignored raw and processed context paths and updated the context and
  gate docs so they describe it as staged locally but still unresolved until a
  targeted corridor clip or query is performed. The context classification
  remains `limiting`, not `acceptable`.
- Checks run:
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/inspect_tschamut_public_context_layers.py --format json`
  passed and reported `reviewed_local_context` with `classification:
  limiting`.
- Reviewer notes: Archive download is not the same thing as corridor-level
  context acceptance. The residual blocker is feature extraction or clipping for
  roads, channels, and barrier/protection context.
- Decision: COMPLETED_WITH_LIMITATIONS.
- Next proposed milestone: TB-014.

### M074

- Milestone id: M074.
- Roadmap item: post TB-013 capability-gap reassessment and backlog
  reprioritization.
- Hypothesis/objective: The backlog can be re-centered on measured
  target-vs-gate convergence and uncertainty synthesis now that same-scale
  artifacts, output-budget evidence, and staged public context evidence exist.
- Files intended to change:
  `docs/task_backlog.md`,
  `docs/decision_log.md`,
  `docs/agent_work_log.md`
- Implementation summary: Rewrote the active backlog to treat real public
  context as a limiting interpretation input rather than a missing-cache
  blocker, moved target-vs-gate spatial convergence to the top active task,
  and added a reusable same-scale uncertainty-envelope follow-up. The live
  inspector confirmed the staged real context root is present and classified
  `limiting`, while the ignored same-scale gate artifacts and bounded-output
  evidence remain available for comparison.
- Checks run:
  `sed -n '1,220p' docs/task_backlog.md`
  inspected the active queue before editing.
  `sed -n '120,220p' docs/decision_log.md`
  inspected the existing active-decision block before adding the reprioritization note.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python - <<'PY' ... inspect_context_layers(...) ... PY`
  confirmed the real Tschamut context root is present and classified
  `limiting`.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/audit_local_artifacts.py validation/private/tschamut_public_pilot/gate_v1 hazard/results/tschamut_public_pilot/gate_v1`
  confirmed the same-scale ignored gate artifacts are present locally.
- Reviewer notes: The dominant remaining work is now measurement and reusable
  uncertainty synthesis, not context-cache acquisition.
- Decision: ACCEPT.
- Next proposed milestone: TB-014.

### M075

- Milestone id: M075.
- Roadmap item: post TB-013 backlog reprioritization refinement.
- Hypothesis/objective: The active queue should put target-vs-gate spatial
  convergence first, corridor-level context relevance second, and
  uncertainty-envelope synthesis third now that the real public context cache
  is staged locally.
- Files changed:
  `docs/task_backlog.md`,
  `docs/decision_log.md`,
  `docs/agent_work_log.md`
- Implementation summary: Recast TB-015 from a generic uncertainty-envelope
  follow-up into a concrete corridor-level swissTLM3D relevance measurement
  task; moved the uncertainty-envelope synthesis into TB-016; and updated the
  durable decision so the priority order matches the backlog.
- Checks run:
  `git diff --check`
  passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run --with PyYAML python scripts/check_repo_consistency.py`
  passed.
  `scripts/git-hooks/pre-commit`
  passed.
- Reviewer notes: The cache is staged, so the remaining uncertainty is
  corridor-level interpretation, not acquisition.
- Decision: ACCEPT.
- Next proposed milestone: TB-014.

### M076

- Milestone id: M076.
- Roadmap item: post TB-014 same-scale convergence measurement.
- Hypothesis/objective: The refreshed same-scale target-vs-gate comparison
  should either produce measured per-layer cell-wise disagreement or return a
  precise blocked-missing-input record.
- Files intended to change:
  `docs/task_backlog.md`,
  `docs/decision_log.md`,
  `docs/tschamut_public_conditional_pilot_gate_report.md`,
  `docs/agent_work_log.md`
- Implementation summary: Verified that the gate-side hazard manifest exists
  and exposes `cellwise_layers`, but the target-side same-scale manifest path
  is absent in this checkout. The convergence CLI returned
  `blocked_missing_inputs` when run against the gate and target paths, so the
  report now records the exact missing target manifest path and the backlog
  adds a restoration follow-up for the target-side artifacts.
- Checks run:
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/compare_hazard_map_convergence.py hazard/results/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_manifest.json hazard/results/tschamut_public_pilot/target_gate_v1/validation_tschamut_public_target_gate_v1_manifest.json --format json`
  returned `blocked_missing_inputs`.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python - <<'PY' ...`
  inspected the gate manifest and confirmed `cellwise_layers` are available
  there while the target manifest is absent.
- Reviewer notes: The diagnostic correctly refuses to use the gate-side
  self-check as target-vs-gate spatial evidence.
- Decision: BLOCKED_MISSING_INPUTS.
- Next proposed milestone: TB-017.

### TB-008

- Milestone id: TB-008
- Roadmap item: Measure Whether Single-Job Balfrin Execution Is Still Enough.
- Hypothesis/objective: Existing Balfrin, repeatability, target-gate, output-
  budget, and convergence evidence can determine whether distributed execution
  design is needed or should remain deferred without changing runtime
  behavior.
- Files intended to change:
  `scripts/summarize_balfrin_single_job_execution.py`,
  `tests/test_balfrin_single_job_execution.py`,
  `docs/balfrin_single_job_execution_sufficiency.md`,
  `docs/task_backlog.md`,
  `docs/decision_log.md`,
  `docs/agent_work_log.md`
- Implementation summary: Added a record-driven sufficiency summary that
  classifies distributed execution as `defer`, `design_needed`, or
  `blocked_pending_evidence` using the existing repeatability, reproduction,
  output-budget, convergence, feasibility, and current-gate records. The new
  report pins wall time, memory, output size, restartability, and reducer-state
  evidence, keeps distributed execution unauthorized, and records the decision
  as deferred for the next same-scale conditional step. Removed TB-008 from
  the active backlog.
- Checks run:
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m py_compile scripts/summarize_balfrin_single_job_execution.py tests/test_balfrin_single_job_execution.py scripts/check_repo_consistency.py` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest tests.test_balfrin_single_job_execution` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/summarize_balfrin_single_job_execution.py --output-json /tmp/balfrin_single_job_execution_sufficiency.json --output-md docs/balfrin_single_job_execution_sufficiency.md` passed.
  `git diff --check` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run --with PyYAML python scripts/check_repo_consistency.py` passed.
  `scripts/git-hooks/pre-commit` passed.
- Reviewer notes: Keeps the single-job path sufficient for the next same-scale
  conditional pilot step while leaving distributed execution deferred.
- Decision: ACCEPT.
- Next proposed milestone: post-TB-008 backlog reassessment.

### M072

- Milestone id: M072.
- Roadmap item: post TB-001 through TB-008 backlog reassessment.
- Hypothesis/objective: Recenter the backlog on applying the new diagnostics to
  selected-pilot artifacts and reducing measured blockers, rather than adding
  more evidence-status layers after TB-008 deferred distributed execution.
- Files intended to change:
  `AGENTS.md`,
  `docs/task_backlog.md`,
  `docs/decision_log.md`,
  `docs/agent_work_log.md`.
- Implementation summary: Replaced the stale active TB-007 entry with a new
  sequence: wire cell-wise convergence to normal hazard outputs, implement a
  reduced validation debug-output mode, stage and measure public context crops,
  then run an integrated same-scale conditional pilot review. Kept distributed
  Balfrin orchestration deferred because TB-008 found the single-job path
  sufficient for the next same-scale step.
- Checks run:
  `git diff --check` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run --with PyYAML python scripts/check_repo_consistency.py` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run --with PyYAML python -m unittest tests.test_repo_consistency_claim_hygiene` passed.
  `scripts/git-hooks/pre-commit` passed.

### TB-002

- Milestone id: TB-002
- Roadmap item: Build Reusable Hazard-Map Convergence Diagnostics.
- Hypothesis/objective: A reusable manifest-level comparison diagnostic can
  report numeric convergence indicators for conditional hazard-map products
  without changing physics, defaults, thresholds, or baselines.
- Files intended to change:
  `scripts/compare_hazard_map_convergence.py`,
  `tests/test_hazard_map_convergence.py`,
  `tests/fixtures/hazard/convergence/reference_manifest.json`,
  `tests/fixtures/hazard/convergence/perturbed_manifest.json`,
  `docs/conditional_hazard_convergence_acceptance_protocol.md`,
  `docs/task_backlog.md`,
  `docs/agent_work_log.md`
- Implementation summary: Added an importable and CLI-runnable hazard-map
  convergence diagnostic that compares two or more hazard-manifest or summary
  inputs, reports layer-summary deltas, conditional-curve row-count
  differences, output checksum parity, and explicit blocked states for
  missing inputs. Added deterministic tiny manifest fixtures and focused tests
  for identical inputs, changed metrics, missing inputs, and schema stability.
  Removed TB-002 from the active backlog.
- Checks run:
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest tests.test_hazard_map_convergence`
  passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m py_compile scripts/compare_hazard_map_convergence.py tests/test_hazard_map_convergence.py`
  passed.
- Reviewer notes: The diagnostic stays conditional-hazard only and does not
  introduce annual, physical, risk, or operational semantics.
- Decision: ACCEPT.
- Next proposed milestone: TB-003.

### TB-001

- Milestone id: TB-001
- Roadmap item: Produce Measured Conditional Pilot Acceptance Summary.
- Hypothesis/objective: A reproducible summary generator can derive the
  selected Tschamut conditional pilot classification from existing Balfrin,
  convergence, target-gate, and output-budget evidence without changing
  physics, defaults, thresholds, or baselines.
- Files intended to change:
  `scripts/summarize_conditional_pilot_acceptance.py`,
  `tests/test_conditional_pilot_acceptance_summary.py`,
  `docs/archive/tschamut_public_conditional_pilot_acceptance_summary.md`,
  `docs/task_backlog.md`,
  `docs/agent_work_log.md`
- Implementation summary: Added a summary generator that imports the existing
  DT-04/DT-05/DT-08 validators, reads the selected evidence records, derives a
  conservative final classification, and renders a committed markdown report
  that records the reduced uncertainty and remaining blockers. Removed TB-001
  from the backlog.
- Checks run:
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest tests/test_conditional_pilot_acceptance_summary.py` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest tests/test_balfrin_target_gate_reproduction.py tests/test_output_budget_reducer_gate.py tests/test_public_real_site_conditional_pilot_run.py` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/summarize_conditional_pilot_acceptance.py --markdown-output docs/archive/tschamut_public_conditional_pilot_acceptance_summary.md` passed.
  `git diff --check` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run --with PyYAML python scripts/check_repo_consistency.py` passed.
  `scripts/git-hooks/pre-commit` passed.
- Reviewer notes: The summary remains conservative: the selected pilot is still inconclusive and scale-up remains unauthorized.
- Decision: ACCEPT.
- Next proposed milestone: TB-002.

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
  `docs/archive/tschamut_swissalti3d_controlled_pilot_plan.md`,
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
  `docs/archive/tschamut_swissalti3d_controlled_pilot_plan.md`,
  `docs/agent_work_log.md`
- Implementation summary: Recorded completion of the requested targeted check.
- Checks run:
  `git diff --check -- docs/archive/tschamut_swissalti3d_controlled_pilot_plan.md docs/agent_work_log.md`
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
  `docs/archive/tschamut_swissalti3d_controlled_pilot_plan.md`,
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
  `git diff --check -- docs/archive/tschamut_swissalti3d_controlled_pilot_plan.md docs/tschamut_swissalti3d_pilot.md docs/agent_work_log.md`
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
  `docs/archive/tschamut_swissalti3d_controlled_pilot_plan.md`,
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
  `docs/archive/tschamut_swissalti3d_controlled_pilot_plan.md`,
  `docs/agent_work_log.md`
- Implementation summary: Recorded completion of the requested targeted check.
- Checks run:
  `git diff --check -- docs/archive/tschamut_swissalti3d_controlled_pilot_plan.md docs/agent_work_log.md`
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
  `docs/archive/tschamut_swissalti3d_controlled_pilot_plan.md`,
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
  `docs/archive/tschamut_swissalti3d_controlled_pilot_plan.md`,
  `docs/agent_work_log.md`
- Implementation summary: Recorded completion of the requested targeted check.
- Checks run:
  `git diff --check -- docs/archive/tschamut_swissalti3d_controlled_pilot_plan.md docs/agent_work_log.md`
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
  `docs/archive/tschamut_swissalti3d_controlled_pilot_plan.md`,
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
  `docs/archive/tschamut_swissalti3d_controlled_pilot_plan.md`,
  `docs/agent_work_log.md`
- Implementation summary: Recorded completion of the requested targeted check.
- Checks run:
  `git diff --check -- docs/archive/tschamut_swissalti3d_controlled_pilot_plan.md docs/agent_work_log.md`
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
  `docs/archive/tschamut_swissalti3d_controlled_pilot_plan.md`,
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
  `docs/archive/tschamut_swissalti3d_controlled_pilot_plan.md`,
  `docs/agent_work_log.md`
- Implementation summary: Recorded completion of the requested targeted check.
- Checks run:
  `git diff --check -- docs/archive/tschamut_swissalti3d_controlled_pilot_plan.md docs/agent_work_log.md`
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
  `docs/README.md`,
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

### M054

- Milestone id: M054.
- Roadmap item: Roadmap reassessment after validation refactor, CI alignment,
  target-scale interpretation blockers, and balfrin pilot path.
- Hypothesis/objective: Update the active roadmaps so they reflect the latest
  repository state: expanded validation submodules, improved CI Python tooling,
  multi-trajectory Parquet writer support, completed blocked/limiting Target
  13/14 records, Target 15 as the next actionable development step, and the
  balfrin readiness/reproduction sequence for the Tschamut hazard-map pilot.
- Initial gap assessment: The roadmap matrix still ranked manual GIS/QGIS and
  forest/obstacle review above Target 15, even though those items are now
  explicitly blocked/limiting until local artifacts or tools are available.
  The roadmaps also understated the validation split, did not mention the CI
  and Parquet-output changes, and did not yet separate the main hazard-map
  outcome from secondary GIS/QGIS interoperability review.
- Files changed:
  `docs/next_development_targets.md`,
  `docs/real_case_intensity_frequency_implementation_roadmap.md`,
  `docs/roadmap_recommendation_matrix.md`,
  `docs/agent_work_log.md`.
- Implementation summary: Reprioritized Target 15, target-run provenance and
  debug output budget, as the highest-value implementable next step. Roadmaps
  now treat manual GIS/QGIS as secondary interoperability QA rather than the
  main pilot outcome, keep forest/obstacle review as a scientific
  interpretation blocker, and add balfrin artifact/environment readiness plus
  same-scale balfrin target-gate reproduction as the next pilot-specific steps.
  They also record the expanded validation split, CI requirements alignment,
  and Parquet writer as completed building blocks.
- Checks run:
  `git diff --check`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/check_repo_consistency.py`.
- Reviewer notes: Documentation-only roadmap update; no physics, defaults,
  sampling weights, generated outputs, raw geodata, annual frequency support,
  physical probability support, calibration, risk/exposure semantics,
  SLURM/MPI/GPU code, or operational claims are changed.
- Decision: ACCEPT; documentation consistency checks pass.
- Next proposed milestone: Implement Target 15 with an additive provenance and
  output-budget guardrail for selected target-scale evidence, then add the
  balfrin readiness record for `/users/olifu/work/rust_rockfall`.

### M055

- Milestone id: M055.
- Roadmap item: Roadmap reassessment after balfrin readiness/probe progress.
- Hypothesis/objective: Update the prioritized target list so it reflects the
  current state: hazard output profiles, balfrin readiness checker, SLURM-first
  probe driver, probe metrics/log-audit collection, tracked 20-release-cell and
  420x450 probes, and clean 420x450 SLURM baseline evidence.
- Initial gap assessment: The roadmaps still treated balfrin readiness and
  reproduction mostly as future concepts. They did not distinguish completed
  balfrin probe scaffolding from remaining selected-gate work, and they did not
  prioritize closing the current probe repeat/log-audit loop before selected
  target-gate reproduction.
- Files changed:
  `docs/next_development_targets.md`,
  `docs/real_case_intensity_frequency_implementation_roadmap.md`,
  `docs/roadmap_recommendation_matrix.md`,
  `docs/agent_work_log.md`.
- Implementation summary: Reprioritized the near-term list around the Swiss
  public-data hazard-map goal. The next tasks are now: close target-run
  provenance/output-profile policy, record balfrin readiness for
  `/users/olifu/work/rust_rockfall`, close the current SLURM probe
  repeat/log-audit loop, reproduce the selected Tschamut conditional hazard-map
  gate on balfrin at the same scale, and define a conditional hazard-map
  convergence acceptance protocol. GIS/QGIS remains secondary interoperability
  QA, and annual/physical semantics remain deferred.
- Checks run:
  `git diff --check`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/check_repo_consistency.py`
  failed because the transient uv environment lacked PyYAML;
  `UV_CACHE_DIR=/tmp/uv-cache uv run --with PyYAML python scripts/check_repo_consistency.py`
  passed.
- Reviewer notes: Documentation-only roadmap update; no physics, defaults,
  sampling weights, raw geodata, generated outputs, annual frequency support,
  physical probability support, calibration, risk/exposure semantics, or
  operational claims are changed.
- Decision: ACCEPT if documentation consistency checks pass.
- Next proposed milestone: Implement the target-run provenance/output-profile
  policy closure, then record balfrin readiness.

### M056

- Milestone id: M056.
- Roadmap item: Roadmap/target documentation authority consolidation.
- Hypothesis/objective: Remove competing "Target 1" meanings so agents use one
  current implementation target source.
- Initial gap assessment: `docs/next_development_targets.md` still exposed
  completed historical items as `Target N` headings while
  `docs/roadmap_recommendation_matrix.md` used independent rank numbers for
  active work. This caused agents to ask which "Target 1" was intended.
- Files changed:
  `docs/next_development_targets.md`,
  `docs/real_case_intensity_frequency_implementation_roadmap.md`,
  `docs/roadmap_recommendation_matrix.md`,
  `docs/README.md`,
  `README.md`,
  `AGENTS.md`,
  `docs/decision_log.md`,
  `scripts/check_repo_consistency.py`,
  `tests/test_repo_consistency_claim_hygiene.py`,
  `docs/agent_work_log.md`.
- Implementation summary: Made `docs/next_development_targets.md` the single
  authoritative current target list with `DT-xx` identifiers, moved historical
  gates into a concise completed/blocked summary, demoted the matrix and
  long-term roadmap to supporting context, and added a consistency guard
  against reintroducing active-looking `## Target N` headings.
- Checks run:
  `rg -n "^## Target [0-9]+|authoritative current development targets|not authoritative for current target selection" docs`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest tests.test_repo_consistency_claim_hygiene`;
  `git diff --check`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run --with PyYAML python scripts/check_repo_consistency.py`.

### M058

- Milestone id: M058.
- Roadmap item: Python tool-environment reliability.
- Hypothesis/objective: Stop repeated PyYAML import failures when agents run
  repository scripts with plain `uv run python ...`.
- Initial gap assessment: `requirements-tools.txt` listed PyYAML and other
  tool packages, but the repository had no `pyproject.toml`, so `uv run python`
  did not know which dependencies to sync unless the caller remembered
  `--with PyYAML` or created `.venv` manually.
- Files changed:
  `pyproject.toml`,
  `uv.lock`,
  `docs/onboarding.md`,
  `AGENTS.md`,
  `scripts/check_repo_consistency.py`,
  `tests/test_repo_consistency_claim_hygiene.py`,
  `docs/agent_work_log.md`.
- Implementation summary: Added a repository Python tool project with
  dependencies matching `requirements-tools.txt`, disabled package installation
  for the Rust repository, committed the uv lockfile, updated onboarding/agent
  guidance, and added a consistency check that keeps `pyproject.toml` and
  `requirements-tools.txt` aligned.
- Checks run:
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -c "import yaml, numpy, PIL, pyproj, pyarrow, scipy; print('tool deps ok')"`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/validate_scalable_conditional_target_gate.py validation/pilot_runs/tschamut_public_scalable_conditional_target_gate_v1.yaml --format json`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/validate_pilot_ensemble_feasibility.py validation/pilot_runs/tschamut_public_ensemble_feasibility_v1.yaml --format json`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest tests.test_scalable_conditional_target_gate tests.test_pilot_ensemble_feasibility`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest tests.test_repo_consistency_claim_hygiene tests.test_scalable_conditional_target_gate tests.test_pilot_ensemble_feasibility`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/check_repo_consistency.py`.

### M059

- Milestone id: M059.
- Roadmap item: DT-02. Balfrin artifact and environment readiness record.
- Hypothesis/objective: Record a share-safe ready/blocked result for
  `/users/olifu/work/rust_rockfall` before any selected Tschamut conditional
  hazard-map reproduction on balfrin.
- Initial gap assessment: The read-only readiness checker and runbook existed,
  but the repository did not yet contain a selected readiness record with
  toolchain, ignored-input, processed-artifact, writable-output, and claim-boundary
  status.
- Files changed:
  `validation/pilot_runs/tschamut_public_balfrin_readiness_v1.yaml`,
  `scripts/validate_balfrin_tschamut_readiness_record.py`,
  `tests/test_balfrin_tschamut_readiness_record.py`,
  `docs/balfrin_tschamut_readiness.md`,
  `docs/next_development_targets.md`,
  `docs/real_case_intensity_frequency_implementation_roadmap.md`,
  `docs/roadmap_recommendation_matrix.md`,
  `docs/README.md`,
  `scripts/check_repo_consistency.py`,
  `docs/agent_work_log.md`.
- Implementation summary: Ran the balfrin readiness checker on
  `/users/olifu/work/rust_rockfall` and recorded
  `ready_for_balfrin_target_gate` with zero blocking checks. Added a validator
  and tests so the readiness record keeps the raw/geodata/generated-output and
  annual/physical/risk claim boundaries explicit.
- Checks run:
  `ssh -o BatchMode=yes -o ConnectTimeout=10 balfrin 'cd /users/olifu/work/rust_rockfall && UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/check_balfrin_tschamut_readiness.py validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml --format json'`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/validate_balfrin_tschamut_readiness_record.py validation/pilot_runs/tschamut_public_balfrin_readiness_v1.yaml --format json`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest tests.test_balfrin_tschamut_readiness_record tests.test_balfrin_tschamut_readiness`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/check_repo_consistency.py`.

### M062

- Milestone id: M062.
- Roadmap item: Roadmap reprioritization after external hostile review.
- Hypothesis/objective: Merge the review findings into the current Tschamut
  pilot target sequence without changing code, physics, defaults, validation
  cases, generated artifacts, or public claims.
- Files changed:
  `docs/next_development_targets.md`,
  `docs/roadmap_recommendation_matrix.md`,
  `docs/real_case_intensity_frequency_implementation_roadmap.md`,
  `docs/decision_log.md`,
  `docs/agent_work_log.md`.
- Implementation summary: Reconciled the completed DT-05 convergence protocol
  with the external review findings. DT-05 remains complete and classifies the
  DT-04 Balfrin evidence as `inconclusive`; DT-06 stochastic sampling/RNG audit,
  DT-07 DEM/input conditioning QA, and DT-08 output-budget/reducer scaling gate
  now carry the remaining review pressure. Distributed Balfrin execution stays
  behind measured need.
- Checks run:
  `rg -n "DT-05|DT-06|DT-07|External review|convergence|stochastic|DEM/input|not authoritative" docs/next_development_targets.md docs/roadmap_recommendation_matrix.md docs/real_case_intensity_frequency_implementation_roadmap.md docs/decision_log.md`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/check_repo_consistency.py`;
  `git diff --check`.

### M061

- Milestone id: M061.
- Roadmap item: DT-04. Balfrin selected Tschamut target-gate reproduction.
- Hypothesis/objective: Reproduce the selected 1,000-trajectory conditional
  hazard-map target gate in the intended balfrin environment without changing
  physics, defaults, release assumptions, thresholds, sampling weights, or
  output semantics.
- Initial gap assessment: DT-02 and DT-03 showed balfrin readiness and
  single-job SLURM repeatability, but the selected target gate itself still
  lacked share-safe balfrin execution evidence.
- Files changed:
  `validation/pilot_runs/tschamut_public_balfrin_target_gate_reproduction_v1.yaml`,
  `scripts/validate_balfrin_target_gate_reproduction.py`,
  `tests/test_balfrin_target_gate_reproduction.py`,
  `docs/tschamut_public_scalable_conditional_target_gate.md`,
  `docs/next_development_targets.md`,
  `docs/real_case_intensity_frequency_implementation_roadmap.md`,
  `docs/roadmap_recommendation_matrix.md`,
  `scripts/check_repo_consistency.py`,
  `docs/agent_work_log.md`.
- Implementation summary: Ran balfrin SLURM job `4318941` from commit
  `61ab9c6542ba1d2274139940777ff0238f1983cf`. The selected target gate
  completed with 10 observed release cells, 100 trajectories per release cell,
  summary-only conditional curves, grid CSV suppression, GeoTIFF export,
  deterministic two-worker chunk/reducer metadata, checksums, performance
  evidence, and a clean log audit. The reproduction is classified
  `inconclusive`, not `passed`, because convergence acceptance,
  forest/obstacle context, and secondary manual GIS/QGIS QA remain unresolved.
- Checks run:
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/validate_balfrin_target_gate_reproduction.py validation/pilot_runs/tschamut_public_balfrin_target_gate_reproduction_v1.yaml --format json`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest tests.test_balfrin_target_gate_reproduction`.

### M060

- Milestone id: M060.
- Roadmap item: DT-03. Balfrin SLURM probe repeatability and log-audit loop.
- Hypothesis/objective: Decide whether the existing single-job SLURM probe
  driver is stable enough for same-scale selected-gate reproduction on balfrin.
- Initial gap assessment: Fresh 420x450 baseline evidence existed, but the
  repeat/reuse check, numeric-artifact stability check, reviewed log-audit
  result, and selected-gate driver decision were not recorded as a machine-checked
  gate.
- Files changed:
  `validation/pilot_runs/tschamut_public_slurm_probe_repeatability_v1.yaml`,
  `scripts/validate_balfrin_slurm_probe_repeatability.py`,
  `tests/test_balfrin_slurm_probe_repeatability.py`,
  `docs/tschamut_public_pilot_scaling_review.md`,
  `docs/balfrin_probe_slurm_driver.md`,
  `docs/next_development_targets.md`,
  `docs/real_case_intensity_frequency_implementation_roadmap.md`,
  `docs/roadmap_recommendation_matrix.md`,
  `docs/README.md`,
  `scripts/check_repo_consistency.py`,
  `docs/agent_work_log.md`.
- Implementation summary: Ran two 420x450 repeat jobs on balfrin. Both reused
  completed trajectory and reducer chunks, retained stable plan IDs, completed
  with clean log audits, and the second repeat preserved all `33/33` compared
  numeric hazard artifacts byte-for-byte. The driver is classified as
  `ready_for_same_scale_selected_gate_reproduction` with no scale-up,
  distributed-execution, annual/physical, or operational claims.
- Checks run:
  `ssh ... UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/submit_balfrin_probe.py ... --submit ...`;
  `sacct -j 4318872 --format=JobID,State,ExitCode,Elapsed -P`;
  `sacct -j 4318896 --format=JobID,State,ExitCode,Elapsed -P`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/validate_balfrin_slurm_probe_repeatability.py validation/pilot_runs/tschamut_public_slurm_probe_repeatability_v1.yaml --format json`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest tests.test_balfrin_slurm_probe_repeatability tests.test_balfrin_probe_driver`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/check_repo_consistency.py`.

### M061

- Milestone id: M061.
- Roadmap item: DT-05. Conditional hazard-map convergence acceptance
  protocol.
- Hypothesis/objective: Turn the completed DT-04 Balfrin reproduction into a
  machine-checkable conditional convergence assessment without tuning,
  annual/physical semantics, or operational claims.
- Files intended to change:
  `docs/conditional_hazard_convergence_acceptance_protocol.md`,
  `validation/pilot_runs/tschamut_public_conditional_convergence_protocol_v1.yaml`,
  `scripts/validate_conditional_convergence_protocol.py`,
  `tests/test_conditional_convergence_protocol.py`,
  `docs/README.md`,
  `docs/tschamut_public_scalable_conditional_target_gate.md`,
  `docs/next_development_targets.md`,
  `docs/real_case_intensity_frequency_implementation_roadmap.md`,
  `docs/roadmap_recommendation_matrix.md`,
  `scripts/check_repo_consistency.py`,
  `docs/agent_work_log.md`.
- Implementation summary: Added a conservative conditional hazard-map
  convergence protocol, a machine-readable DT-05 assessment record, a focused
  validator, and direct unit tests. The protocol keeps GIS/QGIS QA secondary,
  classifies the current DT-04 Balfrin evidence as `inconclusive`, and keeps
  scale-up authorization false.
- Checks run:
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/validate_conditional_convergence_protocol.py validation/pilot_runs/tschamut_public_conditional_convergence_protocol_v1.yaml --format json` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest tests.test_conditional_convergence_protocol` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest tests.test_balfrin_target_gate_reproduction tests.test_scalable_conditional_target_gate` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/check_repo_consistency.py` passed.
  `git diff --check` passed.
  `scripts/git-hooks/pre-commit` passed.
- Reviewer notes: Current DT-04 evidence remains inconclusive under the
  protocol; no annual/physical/risk/operational claim language was added.
- Decision: ACCEPT.
- Next proposed milestone: DT-06.

### M057

- Milestone id: M057.
- Roadmap item: DT-01. Target-run provenance and selected output-profile
  policy closure.
- Hypothesis/objective: Close the current target-run provenance ambiguity
  without rerunning benchmarks or changing model behavior.
- Initial gap assessment: The selected target-scale gate recorded 1,000
  observed-release trajectories, but its `ensemble_execution` provenance
  represented only an auxiliary single-release path. The selected output
  profile was also not explicitly linked to the output-profile contract.
- Files changed:
  `validation/pilot_runs/tschamut_public_scalable_conditional_target_gate_v1.yaml`,
  `scripts/validate_scalable_conditional_target_gate.py`,
  `tests/test_scalable_conditional_target_gate.py`,
  `validation/pilot_runs/tschamut_public_ensemble_feasibility_v1.yaml`,
  `scripts/validate_pilot_ensemble_feasibility.py`,
  `tests/test_pilot_ensemble_feasibility.py`,
  `docs/tschamut_public_scalable_conditional_target_gate.md`,
  `docs/tschamut_public_ensemble_feasibility.md`,
  `docs/next_development_targets.md`,
  `docs/real_case_intensity_frequency_implementation_roadmap.md`,
  `docs/roadmap_recommendation_matrix.md`,
  `scripts/check_repo_consistency.py`,
  `docs/agent_work_log.md`.
- Implementation summary: Added machine-checked
  `target_run_provenance_policy` and `output_profile_policy` sections to the
  selected target-gate record. They separate observed-release target outputs
  from auxiliary ensemble provenance, classify the current gate as legacy/custom
  summary-only, select `scalable_conditional` for follow-up runs unless
  `provenance_audit` is needed, and retain the validation debug-output budget
  blocker. The ensemble-size no-go record now treats provenance as classified
  and keeps convergence, GIS, obstacle/context, and debug-output budget as the
  remaining blockers.
- Checks run:
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/validate_scalable_conditional_target_gate.py validation/pilot_runs/tschamut_public_scalable_conditional_target_gate_v1.yaml --format json` failed because the transient uv environment lacked PyYAML;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/validate_pilot_ensemble_feasibility.py validation/pilot_runs/tschamut_public_ensemble_feasibility_v1.yaml --format json` failed because the transient uv environment lacked PyYAML;
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest tests.test_scalable_conditional_target_gate tests.test_pilot_ensemble_feasibility` failed because the transient uv environment lacked PyYAML;
  `UV_CACHE_DIR=/tmp/uv-cache uv run --with PyYAML python scripts/validate_scalable_conditional_target_gate.py validation/pilot_runs/tschamut_public_scalable_conditional_target_gate_v1.yaml --format json`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run --with PyYAML python scripts/validate_pilot_ensemble_feasibility.py validation/pilot_runs/tschamut_public_ensemble_feasibility_v1.yaml --format json`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run --with PyYAML python -m unittest tests.test_scalable_conditional_target_gate tests.test_pilot_ensemble_feasibility tests.test_repo_consistency_claim_hygiene`;
  `rg -n "^## Target [0-9]+|authoritative current development targets|not authoritative for current target selection" docs`;
  `git diff --check`;
  `UV_CACHE_DIR=/tmp/uv-cache uv run --with PyYAML python scripts/check_repo_consistency.py`.

### M062

- Milestone id: M062.
- Roadmap item: DT-06. Stochastic sampling and RNG stream audit.
- Hypothesis/objective: Record current stochastic semantics, known stream and
  distribution limits, and the no-behavior-change boundary in a machine-
  readable audit package without changing physics or RNG behavior.
- Files intended to change:
  `docs/stochastic_sampling_rng_stream_audit.md`,
  `validation/pilot_runs/tschamut_public_stochastic_sampling_audit_v1.yaml`,
  `scripts/validate_stochastic_sampling_audit.py`,
  `tests/test_stochastic_sampling_audit.py`,
  `docs/next_development_targets.md`,
  `docs/real_case_intensity_frequency_implementation_roadmap.md`,
  `docs/roadmap_recommendation_matrix.md`,
  `docs/README.md`,
  `docs/decision_log.md`,
  `scripts/check_repo_consistency.py`,
  `docs/agent_work_log.md`.
- Implementation summary: Added a DT-06 stochastic audit document, a
  machine-readable audit record, a focused validator, targeted regression
  tests, and repository-consistency hooks. Updated the authoritative targets
  and roadmap docs so DT-06 is complete and DT-07 is now the next active
  target.
- Checks run:
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/validate_stochastic_sampling_audit.py validation/pilot_runs/tschamut_public_stochastic_sampling_audit_v1.yaml --format json` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest tests.test_stochastic_sampling_audit` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest tests.test_conditional_convergence_protocol tests.test_scalable_conditional_target_gate` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/check_repo_consistency.py` passed.
  `git diff --check` passed.
- Reviewer notes: No physics changes, no RNG changes, no stochastic-default
  changes, and no annual/physical/risk/operational claim language were added.
- Decision: ACCEPT.
- Next proposed milestone: DT-07.

### M063

- Milestone id: M063.
- Roadmap item: DT-07. Real-site DEM/input conditioning QA gate.
- Hypothesis/objective: Record the fail-closed real-site DEM/input
  conditioning QA gate, machine-readable evidence record, validator, and tests
  without changing DEM behavior, physics, or tuning.
- Files intended to change:
  `docs/real_site_dem_input_conditioning_qa_gate.md`,
  `validation/pilot_runs/tschamut_public_dem_input_conditioning_qa_v1.yaml`,
  `scripts/validate_dem_input_conditioning_qa.py`,
  `tests/test_dem_input_conditioning_qa.py`,
  `docs/next_development_targets.md`,
  `docs/real_case_intensity_frequency_implementation_roadmap.md`,
  `docs/roadmap_recommendation_matrix.md`,
  `docs/README.md`,
  `docs/decision_log.md`,
  `scripts/check_repo_consistency.py`,
  `docs/agent_work_log.md`.
- Implementation summary: Added the DT-07 real-site DEM/input conditioning QA
  gate doc, record, validator, and tests; updated the authoritative targets
  and supporting roadmap docs so DT-07 is complete and DT-08 is now the next
  active target.
- Checks run:
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/validate_dem_input_conditioning_qa.py validation/pilot_runs/tschamut_public_dem_input_conditioning_qa_v1.yaml --format json` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest tests.test_dem_input_conditioning_qa` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest tests.test_conditional_convergence_protocol tests.test_stochastic_sampling_audit` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/check_repo_consistency.py` passed.
  `git diff --check` passed.
  `scripts/git-hooks/pre-commit` passed.
- Reviewer notes: No physics changes, no DEM behavior changes, no tuning, and
  no annual/physical/risk/operational claim language were added.
- Decision: ACCEPT.
- Next proposed milestone: DT-08.

### M064

- Milestone id: M064.
- Roadmap item: DT-08. Output budget and reducer scaling gate.
- Hypothesis/objective: Record the fail-closed output budget and reducer
  scaling gate, machine-readable evidence record, validator, and tests without
  changing physics, reducer behavior, or output defaults.
- Files intended to change:
  `docs/output_budget_reducer_scaling_gate.md`,
  `validation/pilot_runs/tschamut_public_output_budget_reducer_gate_v1.yaml`,
  `scripts/validate_output_budget_reducer_gate.py`,
  `tests/test_output_budget_reducer_gate.py`,
  `docs/next_development_targets.md`,
  `docs/real_case_intensity_frequency_implementation_roadmap.md`,
  `docs/roadmap_recommendation_matrix.md`,
  `docs/README.md`,
  `docs/decision_log.md`,
  `scripts/check_repo_consistency.py`,
  `docs/agent_work_log.md`.
- Implementation summary: Added the DT-08 output budget and reducer scaling
  gate doc, record, validator, and tests; updated the authoritative targets
  and supporting roadmap docs so DT-08 is complete, DT-09 is conditional, and
  DT-10 is now the next active target.
- Checks run:
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/validate_output_budget_reducer_gate.py validation/pilot_runs/tschamut_public_output_budget_reducer_gate_v1.yaml --format json` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest tests.test_output_budget_reducer_gate` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest tests.test_conditional_convergence_protocol tests.test_stochastic_sampling_audit tests.test_dem_input_conditioning_qa` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/check_repo_consistency.py` passed.
  `git diff --check` passed.
  `scripts/git-hooks/pre-commit` passed.
- Reviewer notes: No physics changes, no reducer-behavior changes, no output
  default changes, and no annual/physical/risk/operational claim language were
  added.
- Decision: ACCEPT.
- Next proposed milestone: DT-10.

### M065

- Milestone id: M065.
- Roadmap item: documentation consolidation after DT-08.
- Hypothesis/objective: Reduce roadmap drift and agent context cost by making
  `docs/next_development_targets.md` carry the current pilot gap assessment
  and by treating the matrix, long-term roadmap, and completed gate docs as
  supporting context rather than routine DT update targets.
- Files intended to change:
  `docs/next_development_targets.md`,
  `docs/real_case_intensity_frequency_implementation_roadmap.md`,
  `docs/roadmap_recommendation_matrix.md`,
  `docs/real_site_dem_input_conditioning_qa_gate.md`,
  `docs/output_budget_reducer_scaling_gate.md`,
  `docs/README.md`,
  `scripts/check_repo_consistency.py`,
  `docs/agent_work_log.md`.
- Implementation summary: Added maintenance rules that routine DT work should
  update only the authoritative target file and target-specific evidence doc;
  recorded the current post-DT-08 gap assessment with DT-10 as the next active
  target; fixed the roadmap consistency check so it expects DT-08 complete and
  DT-10 active.
- Checks run:
  `rg -n "Maintenance rule|Current Pilot Gap Assessment|DT-08|DT-09|DT-10|not authoritative|routine DT" docs/next_development_targets.md docs/roadmap_recommendation_matrix.md docs/real_case_intensity_frequency_implementation_roadmap.md docs/real_site_dem_input_conditioning_qa_gate.md docs/output_budget_reducer_scaling_gate.md docs/README.md scripts/check_repo_consistency.py` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run --with PyYAML python scripts/check_repo_consistency.py` passed.
  `git diff --check` passed.

### M066

- Milestone id: M066.
- Roadmap item: DT-10. Target-scale forest and obstacle context review.
- Hypothesis/objective: Record the selected Tschamut forest/obstacle context
  gate as blocked pending local evidence because no reviewed public context
  layers are present in this checkout, without changing physics or adding
  obstacle behavior.
- Files intended to change:
  `docs/tschamut_public_obstacle_context_scope.md`,
  `validation/pilot_runs/tschamut_public_obstacle_scope_v1.yaml`,
  `scripts/validate_pilot_obstacle_scope.py`,
  `tests/test_pilot_obstacle_scope.py`,
  `docs/next_development_targets.md`,
  `docs/real_case_intensity_frequency_implementation_roadmap.md`,
  `docs/roadmap_recommendation_matrix.md`,
  `scripts/check_repo_consistency.py`,
  `docs/agent_work_log.md`.
- Implementation summary: Updated the obstacle-context gate record,
  validator, tests, and supporting docs to classify the selected Tschamut
  context review as `blocked_pending_local_evidence`; local public context
  layers remain absent, so the pilot stays non-operational and diagnostic.
- Checks run:
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/validate_pilot_obstacle_scope.py validation/pilot_runs/tschamut_public_obstacle_scope_v1.yaml --format json` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest tests.test_pilot_obstacle_scope` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/check_repo_consistency.py` passed.
  `git diff --check` passed.
- Reviewer notes: No obstacle physics, tuning, or operational hazard-map
  claims were added.
- Decision: ACCEPT.
- Next proposed milestone: DT-11 or the next active roadmap blocker if the
  local context review remains unavailable.

### M067

- Milestone id: M067.
- Roadmap item: planning-document consolidation.
- Hypothesis/objective: Replace the maintained target-list pattern with three
  clear planning records: `task_backlog.md` for executable worker tasks,
  `decision_log.md` for durable decisions, and `agent_work_log.md` for
  completed execution history.
- Files intended to change:
  `docs/task_backlog.md`,
  `docs/next_development_targets.md`,
  `docs/decision_log.md`,
  `docs/README.md`,
  `docs/onboarding.md`,
  `docs/real_case_intensity_frequency_implementation_roadmap.md`,
  `docs/roadmap_recommendation_matrix.md`,
  `docs/real_site_dem_input_conditioning_qa_gate.md`,
  `docs/output_budget_reducer_scaling_gate.md`,
  `docs/archive/tschamut_swissalti3d_controlled_pilot_plan.md`,
  `README.md`,
  `AGENTS.md`,
  `scripts/check_repo_consistency.py`,
  `docs/agent_work_log.md`.
- Implementation summary: Added the authoritative executable backlog with
  worker-sized `TB-xxx` tasks, converted `next_development_targets.md` into a
  legacy pointer, updated onboarding/agent/index docs, and adjusted the
  consistency check to enforce the backlog/decision/work-log split.
- Checks run:
  `UV_CACHE_DIR=/tmp/uv-cache uv run --with PyYAML python -m unittest tests.test_repo_consistency_claim_hygiene` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run --with PyYAML python scripts/check_repo_consistency.py` passed.
  `git diff --check` passed.

### M068

- Milestone id: M068.
- Roadmap item: progress-over-process development rule.
- Hypothesis/objective: Rebalance repository process so future agents prefer
  executable implementation, measured validation, scientific analysis,
  reproducibility improvements, performance work, and tested bug fixes over
  procedural gate work.
- Files intended to change:
  `AGENTS.md`,
  `README.md`,
  `docs/task_backlog.md`,
  `docs/next_development_targets.md`,
  `docs/real_case_intensity_frequency_implementation_roadmap.md`,
  `docs/README.md`,
  `docs/decision_log.md`,
  `docs/agent_work_log.md`.
- Implementation summary: Added an explicit progress-over-process rule,
  clarified that gates and validators are support mechanisms rather than
  deliverables, and required backlog tasks to name the concrete implementation
  or validation outcome they enable.
- Checks run:
  `git diff --check` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run --with PyYAML python scripts/check_repo_consistency.py` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run --with PyYAML python -m unittest tests.test_repo_consistency_claim_hygiene` passed.
  `rg -n "Progress over process|progress over process|Progress Over Process|support mechanisms|not substitutes|concrete implementation or validation outcome|next gate" AGENTS.md README.md docs/task_backlog.md docs/next_development_targets.md docs/real_case_intensity_frequency_implementation_roadmap.md docs/README.md docs/decision_log.md docs/agent_work_log.md` passed.
  `scripts/git-hooks/pre-commit` passed.

### M069

- Milestone id: M069.
- Roadmap item: backlog alignment with project capability gaps.
- Hypothesis/objective: Keep the executable backlog connected to the actual
  project goal: a reproducible Swiss public-data conditional hazard-map pilot,
  not procedural gate maintenance.
- Files intended to change:
  `docs/task_backlog.md`,
  `AGENTS.md`,
  `docs/decision_log.md`,
  `docs/agent_work_log.md`.
- Implementation summary: Reconstructed the objective and capability gaps in
  the backlog, replaced procedural-first tasks with capability-gap tasks, and
  added guidance that backlog evolution must remain tied to simulator,
  validation, reproducibility, scaling, uncertainty, usability, or
  interpretation gaps.
- Checks run:
  `git diff --check` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run --with PyYAML python scripts/check_repo_consistency.py` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run --with PyYAML python -m unittest tests.test_repo_consistency_claim_hygiene` passed.
  `scripts/git-hooks/pre-commit` passed.

### M070

- Milestone id: M070.
- Roadmap item: executable capability backlog refocus.
- Hypothesis/objective: Keep the active backlog centered on new measurements,
  executable diagnostics, reproducibility, and scaling evidence for the
  conditional Tschamut hazard-map pilot rather than further procedural status
  maintenance.
- Files intended to change:
  `AGENTS.md`,
  `docs/task_backlog.md`,
  `scripts/check_repo_consistency.py`,
  `docs/agent_work_log.md`.
- Implementation summary: Added a backlog quality assessment, promoted a
  reusable hazard-map convergence diagnostic task, deprioritized secondary
  manual GIS/QGIS QA until the main evidence chain is less blocked, and kept
  consistency expectations aligned with the executable backlog.
- Checks run:
  `git diff --check` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run --with PyYAML python scripts/check_repo_consistency.py` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run --with PyYAML python -m unittest tests.test_repo_consistency_claim_hygiene` passed.
  `scripts/git-hooks/pre-commit` passed.

### TB-003

- Milestone id: TB-003
- Roadmap item: Implement A Bounded Validation Output Profile For Pilot Runs.
- Hypothesis/objective: A record-driven summary generator can measure the
  selected pilot's bounded output profile, current validation-output pressure,
  and retained output-budget blockers without changing physics, defaults,
  thresholds, release assumptions, validation cases, or baselines.
- Files intended to change:
  `scripts/summarize_bounded_validation_output_profile.py`,
  `tests/test_bounded_validation_output_profile.py`,
  `docs/tschamut_public_bounded_validation_output_profile.md`,
  `docs/task_backlog.md`,
  `scripts/check_repo_consistency.py`,
  `docs/agent_work_log.md`
- Implementation summary: Added a record-driven bounded-output summary
  generator that reads the current pilot pressure record, the Balfrin
  bounded-profile record, the output-budget reducer gate, the convergence
  protocol, and the ensemble-feasibility record. The report now records the
  bounded profile controls, measured file and byte counts, inode/file-family
  pressure, explicit missing-output blockers, uncertainty reduced, and
  unresolved blockers. Removed TB-003 from the active backlog and aligned the
  repo-consistency check with the updated backlog.
- Checks run:
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m py_compile scripts/summarize_bounded_validation_output_profile.py tests/test_bounded_validation_output_profile.py` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest tests.test_bounded_validation_output_profile` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/summarize_bounded_validation_output_profile.py` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/summarize_bounded_validation_output_profile.py --markdown-output docs/tschamut_public_bounded_validation_output_profile.md --json-output /tmp/tschamut_bounded_validation_output_profile.json` passed.
- Reviewer notes: The bounded profile is measured, but the pilot remains inconclusive because convergence is not accepted, validation debug output is still retained, and local ignored outputs are absent in this checkout.
- Decision: ACCEPT.
- Next proposed milestone: TB-004.

### TB-004

- Milestone id: TB-004
- Roadmap item: Acquire Or Verify Public Context-Layer Evidence For Tschamut.
- Hypothesis/objective: A reusable local context-layer inspection command can
  determine whether public forest, building, transport, barrier, and related
  obstacle/context layers are locally available for the selected Tschamut
  conditional hazard-map interpretation, or else emit an explicit acquisition
  path without inferring absence from missing data.
- Files intended to change:
  `scripts/inspect_tschamut_public_context_layers.py`,
  `tests/test_tschamut_public_context_layers.py`,
  `tests/fixtures/tschamut_context_layers/available/`,
  `docs/tschamut_public_obstacle_context_scope.md`,
  `docs/task_backlog.md`,
  `scripts/check_repo_consistency.py`,
  `docs/agent_work_log.md`
- Implementation summary: Added a reusable context-layer inspection command
  that reads the Tschamut obstacle-scope record and the swisstopo dataset
  registry, reports a blocked state when the expected processed context cache
  is absent, and otherwise summarizes local file presence, sizes, checksums,
  CRS/provenance metadata, and conservative layer classifications from tiny
  metadata-only fixtures. Documented the command in the obstacle-scope guide,
  removed TB-004 from the active backlog, and aligned the repo-consistency
  checks with the new executable evidence path.
- Checks run:
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest tests.test_tschamut_public_context_layers tests.test_pilot_obstacle_scope`
  passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/inspect_tschamut_public_context_layers.py --format json`
  returned a blocked pending-local-evidence report with an acquisition
  checklist for the missing context layers.
  `git diff --check` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run --with PyYAML python scripts/check_repo_consistency.py`
  passed.
- Reviewer notes: The inspection stays conditional and non-operational; the
  current checkout still lacks the processed Tschamut context cache, so the
  pilot remains blocked on local evidence rather than on a semantic
  interpretation of absent obstacles.
- Decision: ACCEPT.
- Next proposed milestone: TB-005.

### M071

- Milestone id: M071.
- Roadmap item: post TB-001 through TB-004 backlog reassessment.
- Hypothesis/objective: Incorporate the review finding that the repository's
  strongest next gains are spatial convergence diagnostics and validation
  output reduction, not more status classification or premature distributed
  execution design.
- Files intended to change:
  `AGENTS.md`,
  `docs/task_backlog.md`,
  `docs/decision_log.md`,
  `docs/agent_work_log.md`.
- Implementation summary: Reordered the active backlog around cell-wise
  hazard-map convergence diagnostics, validation-debug output reduction,
  context-cache inspection, and only then Balfrin single-job sufficiency.
  Added guidance to prefer cell-wise/data-level diagnostics when the scientific
  question is spatial stability.
- Checks run:
  `git diff --check` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run --with PyYAML python scripts/check_repo_consistency.py` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run --with PyYAML python -m unittest tests.test_repo_consistency_claim_hygiene` passed.
  `scripts/git-hooks/pre-commit` passed.

### TB-005

- Milestone id: TB-005
- Roadmap item: Add Cell-Wise Hazard-Map Convergence Diagnostics.
- Hypothesis/objective: The reusable convergence diagnostic can compare tiny
  raster-like hazard fixtures cell by cell, while preserving the manifest-level
  comparison path and explicit blocked-missing-input behavior.
- Files intended to change:
  `scripts/compare_hazard_map_convergence.py`,
  `tests/test_hazard_map_convergence.py`,
  `tests/fixtures/hazard/convergence/cellwise/reference_manifest.json`,
  `tests/fixtures/hazard/convergence/cellwise/shifted_manifest.json`,
  `tests/fixtures/hazard/convergence/cellwise/shape_mismatch_manifest.json`,
  `tests/fixtures/hazard/convergence/cellwise/reference/*.asc`,
  `tests/fixtures/hazard/convergence/cellwise/shifted/*.asc`,
  `tests/fixtures/hazard/convergence/cellwise/shape_mismatch/*.asc`,
  `docs/conditional_hazard_convergence_acceptance_protocol.md`,
  `docs/task_backlog.md`,
  `docs/agent_work_log.md`
- Implementation summary: Extended the hazard-map convergence diagnostic so
  it can parse tiny ESRI ASCII grid fixtures, compare cell-wise values per
  layer, and report stable JSON metrics for `linf_abs_diff`, `l1_abs_diff`,
  `rmse`, nonzero overlap/Jaccard, threshold-exceedance disagreement, and
  nodata mismatch counts. The diagnostic still preserves manifest-level
  comparisons and returns explicit `blocked_missing_inputs` or
  `blocked_invalid_inputs` statuses for missing or shape-mismatched cellwise
  artifacts. Removed TB-005 from the active backlog and noted the new
  cell-wise capability in the convergence protocol.
- Checks run:
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m py_compile scripts/compare_hazard_map_convergence.py tests/test_hazard_map_convergence.py` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest tests.test_hazard_map_convergence` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/compare_hazard_map_convergence.py tests/fixtures/hazard/convergence/cellwise/reference_manifest.json tests/fixtures/hazard/convergence/cellwise/shifted_manifest.json --format json` passed.
- Reviewer notes: The new diagnostic is cell-wise only when cellwise fixtures or emitted grids are present; manifest-only comparisons still behave as before.
- Decision: ACCEPT.
- Next proposed milestone: TB-006.

### TB-006

- Milestone id: TB-006
- Roadmap item: Reduce Or Justify Validation Debug Output For Pilot Runs.
- Hypothesis/objective: The bounded-output summary can be made semantically
  exact for `no_go` feasibility decisions and can expose an executable
  validation-output family audit path that distinguishes manifest, trajectory,
  impact, and sidecar classes without changing public defaults or baselines.
- Files intended to change:
  `scripts/summarize_bounded_validation_output_profile.py`,
  `tests/test_bounded_validation_output_profile.py`,
  `docs/tschamut_public_bounded_validation_output_profile.md`,
  `docs/task_backlog.md`,
  `docs/agent_work_log.md`
- Implementation summary: Fixed the bounded-output summary so `no_go`
  feasibility decisions remain `no_go` in the final classification instead of
  collapsing to only `inconclusive`. Added an executable validation-output
  manifest audit path that can classify output families by file count and
  bytes when a local manifest exists, while still reporting
  `blocked_missing_outputs` in a clean checkout. Regenerated the committed
  bounded-output report and removed TB-006 from the active backlog.
- Checks run:
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m py_compile scripts/summarize_bounded_validation_output_profile.py tests/test_bounded_validation_output_profile.py`
  passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest tests.test_bounded_validation_output_profile`
  passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/summarize_bounded_validation_output_profile.py --format json`
  passed and reported `final_classification=no_go` with `validation_output_audit.status=blocked_missing_outputs`.
- Reviewer notes: The implementation stays conditional and diagnostic only;
  it does not reduce public defaults or authorize scale-up.
- Decision: ACCEPT.
- Next proposed milestone: TB-007.

### TB-007

- Milestone id: TB-007
- Roadmap item: Acquire And Inspect Tschamut Public Context Cache.
- Hypothesis/objective: The shared context-layer inspector can separate local evidence from blocked acquisition state and make the public Tschamut context review machine-readable without implying obstacle absence.
- Files changed:
  `scripts/inspect_tschamut_public_context_layers.py`,
  `tests/test_tschamut_public_context_layers.py`,
  `docs/tschamut_public_obstacle_context_scope.md`,
  `docs/agent_work_log.md`
- Implementation summary: Extended the inspector report so it explicitly exposes `classification`, `context_review_status`, `layers_expected`, `layers_available`, `layers_missing`, `source_products`, `local_cache_paths`, `checksums`, `crs_or_spatial_reference`, `interpretation_impact`, and `operational_claims_allowed`. The checkout still has no processed Tschamut context cache, so the default inspection remains `blocked_pending_local_evidence` with a concrete acquisition checklist and staging commands instead of an obstacle-absence inference.
- Checks run:
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m py_compile scripts/inspect_tschamut_public_context_layers.py tests/test_tschamut_public_context_layers.py`
  passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest tests.test_tschamut_public_context_layers tests.test_pilot_obstacle_scope`
  passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/inspect_tschamut_public_context_layers.py --format json`
  returned `blocked_pending_local_evidence` and emitted the explicit acquisition checklist.
  `git diff --check` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run --with PyYAML python scripts/check_repo_consistency.py`
  passed.
  `scripts/git-hooks/pre-commit` passed.
- Reviewer notes: No local public context cache was found in `data/processed/swisstopo/tschamut_public_pilot/context/`, so the review stays blocked and operational claims remain disallowed.
- Decision: BLOCKED_PENDING_LOCAL_EVIDENCE.
- Next proposed milestone: TB-008.

### TB-009

- Milestone id: TB-009
- Roadmap item: Wire Cell-Wise Convergence Diagnostics To Pilot Hazard Outputs.
- Hypothesis/objective: Normal hazard-layer manifests can expose cell-wise grid paths for conditional convergence checks without changing hazard semantics or collapsing mixed-unit layers.
- Files changed:
  `scripts/build_hazard_layers.py`,
  `scripts/compare_hazard_map_convergence.py`,
  `tests/test_hazard_layers.py`,
  `tests/test_hazard_map_convergence.py`,
  `docs/conditional_hazard_convergence_acceptance_protocol.md`,
  `docs/task_backlog.md`,
  `docs/agent_work_log.md`
- Implementation summary: Added a manifest-side `cellwise_layers` projection for ASCII hazard-layer outputs, taught the convergence diagnostic to infer cell-wise layers only when the underlying grid files exist, and kept summary-only manifests on the legacy manifest/checksum path. Updated tiny cell-wise fixtures so the comparison tool can measure per-layer `linf_abs_diff`, `l1_abs_diff`, `rmse`, `nonzero_jaccard`, threshold disagreement, and nodata mismatch without relying on ignored pilot outputs.
- Checks run:
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m py_compile scripts/compare_hazard_map_convergence.py tests/test_hazard_map_convergence.py scripts/build_hazard_layers.py tests/test_hazard_layers.py`
  passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest tests.test_hazard_map_convergence tests.test_hazard_layers`
  passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/compare_hazard_map_convergence.py tests/fixtures/hazard/convergence/cellwise/reference_manifest.json tests/fixtures/hazard/convergence/cellwise/reference_manifest.json --format json`
  returned `ok` with zero cell-wise differences on the tiny emitted fixtures.
  `git diff --check` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run --with PyYAML python scripts/check_repo_consistency.py`
  passed.
  `scripts/git-hooks/pre-commit` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/compare_hazard_map_convergence.py hazard/results/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_manifest.json hazard/results/tschamut_public_pilot/target_gate_v1/validation_tschamut_public_target_gate_v1_manifest.json --format json`
  returned `blocked_missing_inputs` for the expected absent selected-pilot manifests.
- Reviewer notes: The selected Tschamut hazard outputs were not present in checkout, so the applied pilot comparison remains a missing-artifact state; the new inference path preserves the explicit missing-input behavior instead of silently passing.
- Decision: ACCEPT.
- Next proposed milestone: TB-010.

### TB-011

- Milestone id: TB-011
- Roadmap item: Stage Tschamut Context Crops And Measure Spatial Relevance.
- Hypothesis/objective: The context inspector can report the selected Tschamut corridor extent, explicit spatial-relevance status, and conservative per-category relevance indicators while keeping the real checkout blocked when no processed context crops exist.
- Files changed:
  `scripts/inspect_tschamut_public_context_layers.py`,
  `tests/test_tschamut_public_context_layers.py`,
  `docs/tschamut_public_obstacle_context_scope.md`,
  `docs/agent_work_log.md`
- Implementation summary: Extended the inspector to expose `selected_extent_or_corridor`, `spatial_relevance_status`, and `spatial_relevance_indicators` while preserving the blocked checkout path. The default checkout still reports `blocked_pending_local_evidence` with exact staging commands for the missing SWISSIMAGE, swissTLM3D, swissSURFACE3D Raster, and swissBUILDINGS3D context crops, but the deterministic fixture under `tests/fixtures/tschamut_context_layers/available/` now exercises the reviewed spatial-relevance path.
- Checks run:
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m py_compile scripts/inspect_tschamut_public_context_layers.py tests/test_tschamut_public_context_layers.py`
  passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest tests.test_tschamut_public_context_layers tests.test_pilot_obstacle_scope`
  passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/inspect_tschamut_public_context_layers.py --format json`
  returned `blocked_pending_local_evidence` and emitted the explicit acquisition checklist for the missing real checkout context.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/inspect_tschamut_public_context_layers.py --context-root tests/fixtures/tschamut_context_layers/available --format json`
  returned `fixture_reviewed_context` with `status: limiting` on the deterministic metadata-only fixture crop.
- Reviewer notes: No real processed public context crops are staged in `data/processed/swisstopo/tschamut_public_pilot/context/`; the task therefore remains a blocked acquisition path for actual public geodata, not an approval of obstacle omission.
- Decision: BLOCKED_PENDING_LOCAL_EVIDENCE.
- Next proposed milestone: TB-012.

### TB-010

- Milestone id: TB-010
- Roadmap item: Implement A Reduced Validation Debug Output Mode.
- Files changed:
  `src/manifest.rs`,
  `src/validation.rs`,
  `src/validation/runner.rs`,
  `src/validation/types.rs`,
  `scripts/summarize_bounded_validation_output_profile.py`,
  `tests/test_bounded_validation_output_profile.py`,
  `tests/config_io_terrain.rs`,
  `tests/fixtures/bounded_validation_output_profile/baseline_manifest.json`,
  `tests/fixtures/bounded_validation_output_profile/reduced_manifest.json`,
  `docs/validation_data_schema.md`,
  `docs/benchmark_case_schema.yaml`,
  `scripts/check_repo_consistency.py`,
  `docs/tschamut_public_bounded_validation_output_profile.md`,
  `docs/task_backlog.md`,
  `docs/agent_work_log.md`
- Implementation summary: Added an opt-in `outputs.validation_output_mode: summary_only` that suppresses the validation-side trajectory/impact debug artifacts while leaving diagnostics, manifest provenance, and summary outputs intact. The run manifest now records the mode additively. The bounded-output summary script now compares committed baseline/reduced fixtures and reports before/after file and byte totals, retained and omitted output classes, and retained provenance. The regenerated report keeps the real selected-pilot local audit blocked because the ignored manifests are still absent.
- Checks run:
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m py_compile scripts/summarize_bounded_validation_output_profile.py tests/test_bounded_validation_output_profile.py`
  passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest tests.test_bounded_validation_output_profile`
  passed.
  `cargo test validation_output_mode_summary_only_suppresses_debug_outputs_and_records_manifest_mode --test config_io_terrain`
  passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/summarize_bounded_validation_output_profile.py --validation-output-baseline-manifest tests/fixtures/bounded_validation_output_profile/baseline_manifest.json --validation-output-reduced-manifest tests/fixtures/bounded_validation_output_profile/reduced_manifest.json --markdown-output docs/tschamut_public_bounded_validation_output_profile.md --json-output /tmp/tschamut_bounded_validation_output_profile.json`
  passed.
- Reviewer notes: Baseline/reduced accounting is now executable on tiny fixtures; the real Tschamut selected-pilot outputs remain blocked_missing_outputs in this checkout.
- Decision: COMPLETED.
- Next proposed milestone: TB-011.

### M073

- Milestone id: M073.
- Roadmap item: post TB-009 through TB-011 backlog reassessment.
- Hypothesis/objective: Convert the worker results into a next-step backlog
  that prioritizes refreshing same-scale selected Tschamut artifacts under the
  current diagnostic contracts before another acceptance synthesis.
- Files intended to change:
  `docs/task_backlog.md`,
  `docs/decision_log.md`,
  `docs/agent_work_log.md`.
- Implementation summary: Updated the capability gaps to reflect that
  cell-wise hazard output wiring, `summary_only` validation mode, and fixture
  context spatial relevance now exist. Replaced the immediate integrated review
  path with an artifact-refresh task that should either regenerate ignored
  selected-pilot outputs and run the diagnostics or produce exact Balfrin/local
  commands and missing-path evidence.
- Checks run:
  `git diff --check` passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run --with PyYAML python scripts/check_repo_consistency.py` passed.

### TB-012

- Milestone id: TB-012
- Roadmap item: Refresh Same-Scale Selected Tschamut Pilot Artifacts.
- Hypothesis/objective: The selected Tschamut gate artifacts can either be refreshed under the current output contracts or staged as an explicit blocked-input checklist without changing physics, defaults, or baselines.
- Files intended to change:
  `docs/tschamut_public_conditional_pilot_gate_report.md`,
  `docs/agent_work_log.md`
- Implementation summary: Audited the current checkout and confirmed that the ignored selected-gate roots are absent here. Recorded an executable staging checklist and the exact missing paths in the selected-gate report rather than fabricating refreshed outputs. The blocked-state record keeps validation/output accounting, cell-wise convergence, and reduced-output provenance conditional until the missing private gate case and processed public inputs are restored.
- Checks run:
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/audit_local_artifacts.py validation/private/tschamut_public_pilot/gate_v1 hazard/results/tschamut_public_pilot/gate_v1`
  passed and reported both roots absent with zero files/bytes.
  `UV_CACHE_DIR=/tmp/uv-cache uv run --with PyYAML python scripts/validate_scalable_conditional_target_gate.py validation/pilot_runs/tschamut_public_scalable_conditional_target_gate_v1.yaml --format json`
  passed and confirmed the target-gate record is still `inconclusive`.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/check_balfrin_tschamut_readiness.py validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml --format json`
  failed as expected with `blocked_for_balfrin_readiness` because the processed inputs and ignored output roots are missing in this checkout.
- Reviewer notes: The refresh path is documented precisely enough for a future worker to execute on a machine that has the missing inputs or can regenerate them.
- Decision: ACCEPT.
- Next proposed milestone: TB-013.

### TB-015

- Milestone id: TB-015.
- Roadmap item: Measure Corridor-Level Context Relevance From The Staged SwissTLM3D Archive.
- Implementation summary: Extended the Tschamut context inspector with a corridor-query path that uses `ogrinfo` against the staged swissTLM3D zip archive member paths and records per-layer corridor counts, category summaries, queried layer names, and archive status fields. The measured corridor evidence is limiting, not acceptable: roads/transport, flowing water, and barrier/protection features intersect the selected corridor, while the constructed-feature subset remains unresolved.
- Checks run:
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m py_compile scripts/inspect_tschamut_public_context_layers.py tests/test_tschamut_public_context_layers.py`
  passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest tests.test_tschamut_public_context_layers tests.test_pilot_obstacle_scope`
  passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/inspect_tschamut_public_context_layers.py --format json`
  passed in the sense of producing the JSON report; the process exits nonzero for non-acceptable classifications by design.
  `git diff --check`
  passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run --with PyYAML python scripts/check_repo_consistency.py`
  passed.
  `scripts/git-hooks/pre-commit`
  passed.
- Reviewer notes: The archive is now measured at corridor level and should no longer be treated as a missing-cache problem.
- Decision: COMPLETED.
- Next proposed milestone: TB-017.

### TB-016

- Milestone id: TB-016.
- Roadmap item: Build A Reusable Same-Scale Uncertainty Envelope Report.
- Implementation summary: Added `scripts/summarize_same_scale_uncertainty_envelope.py` plus focused tests and a committed markdown report at `docs/tschamut_public_same_scale_uncertainty_envelope.md`. The envelope composes the acceptance summary, the bounded-output profile, the Balfrin single-job sufficiency record, the reviewed local context evidence, and the target-side convergence readiness state. It now surfaces the measured validation-output reduction (`125` files / `34545900` bytes baseline to `4` files / `81425` bytes summary_only), the corridor-level swissTLM3D relevance evidence from TB-015, the single-job defer decision, and the explicit blocked target-artifact state from TB-017 (`blocked_missing_target_artifacts` / `blocked_missing_inputs`).
- Checks run:
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m py_compile scripts/summarize_same_scale_uncertainty_envelope.py tests/test_same_scale_uncertainty_envelope.py`
  passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest tests.test_same_scale_uncertainty_envelope`
  passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/summarize_same_scale_uncertainty_envelope.py --format json`
  passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/summarize_same_scale_uncertainty_envelope.py --markdown-output docs/tschamut_public_same_scale_uncertainty_envelope.md`
  passed.
- Reviewer notes: The envelope is intentionally non-operational; scale-up remains unauthorized and the target-vs-gate convergence remains pending due to missing target-side artifacts.
- Decision: COMPLETED.
- Next proposed milestone: TB-019.

### TB-019

- Milestone id: TB-019.
- Roadmap item: Run Target-Vs-Gate Cell-Wise Spatial Convergence On Restored Artifacts.
- Implementation summary: Verified that both restored same-scale hazard manifests were present and compared them with `scripts/compare_hazard_map_convergence.py --format json`. The comparison completed with `status: ok` and exposed 22 shared cell-wise layers. The largest disagreement layers were `max_kinetic_energy`, `max_jump_height`, `velocity_exceedance_5mps`, `weighted_velocity_exceedance_5mps`, and `velocity_exceedance_10mps`. The result is recorded conservatively as `inconclusive`; scale-up remains unauthorized and operational claims remain false.
- Readiness audit: the restored target-side artifact chain is available locally under ignored paths with `2007` validation files / `571384147` bytes, `56` hazard files / `79160991` bytes, and `2063` total files / `650545138` bytes.
- Supporting evidence consumed: `docs/tschamut_public_conditional_pilot_gate_report.md`, `docs/conditional_hazard_convergence_acceptance_protocol.md`, `docs/tschamut_public_same_scale_uncertainty_envelope.md`, `docs/tschamut_public_bounded_validation_output_profile.md`, `docs/tschamut_public_obstacle_context_scope.md`, `docs/balfrin_single_job_execution_sufficiency.md`, and the restored gate/target hazard manifests.
- Checks run:
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/compare_hazard_map_convergence.py hazard/results/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_manifest.json hazard/results/tschamut_public_pilot/target_gate_v1/validation_tschamut_public_target_gate_v1_manifest.json --format json`
  passed.
  `git diff --check`
  passed.
  `UV_CACHE_DIR=/tmp/uv-cache uv run --with PyYAML python scripts/check_repo_consistency.py`
  passed.
  `scripts/git-hooks/pre-commit`
  passed.
- Reviewer notes: The target-side restoration blocker is cleared for this comparison, but the measured convergence remains conservative rather than accepted. The next scientific work is to interpret the measured differences, not to relabel them as convergence.
- Decision: COMPLETED.
- Next proposed milestone: TB-020.

### TB-020

- Milestone id: TB-020.
- Roadmap item: Measure Target-Side Summary-Only Validation Output Profile.
- Implementation summary: Staged a target-side `summary_only` validation case under `validation/private/tschamut_public_pilot/target_gate_v1_summary_only/`, ran the validation with `CARGO_TARGET_DIR=/tmp/rust-rockfall-target`, and measured the reduced validation output profile against the full target manifest. The full target manifest records `2005` files / `571368823` bytes across seven output families; the target summary-only manifest records `4` files / `1271721` bytes. The local ignored-root inventory reports `2716` files / `764598257` bytes for the full target subtree and `6` files / `1286207` bytes for the summary-only subtree. Required provenance is retained, defaults remain unchanged, scale-up remains unauthorized, and TB-019 convergence interpretation stays `inconclusive`.
- Checks run:
  `PYENV_VERSION=system CARGO_TARGET_DIR=/tmp/rust-rockfall-target cargo run -- validate --case validation/private/tschamut_public_pilot/target_gate_v1_summary_only/tschamut_public_target_gate_summary_only_case.yaml`
  passed.
  `PYENV_VERSION=system python3 scripts/audit_local_artifacts.py validation/private/tschamut_public_pilot/target_gate_v1 validation/private/tschamut_public_pilot/target_gate_v1_summary_only`
  passed.
  `PYENV_VERSION=system python3 scripts/summarize_bounded_validation_output_profile.py --validation-output-baseline-manifest validation/private/tschamut_public_pilot/target_gate_v1/validation_tschamut_public_target_gate_v1_manifest.json --validation-output-reduced-manifest validation/private/tschamut_public_pilot/target_gate_v1_summary_only/validation_tschamut_public_target_gate_v1_summary_only_manifest.json --format json`
  passed.
- Reviewer notes: The target-side summary-only profile is now measured, but it remains diagnostic only and does not alter convergence, scale-up authorization, or operational claim boundaries.
- Decision: COMPLETED.
- Next proposed milestone: TB-021.

### TB-021

- Milestone id: TB-021.
- Roadmap item: Measure Hazard-Context Overlap For Limiting Corridor Features.
- Implementation summary: Added `scripts/measure_hazard_context_overlap.py` and focused tests, then measured the selected Tschamut target hazard envelope against the staged swissTLM3D corridor archive. The top positive cell from each of the analyzed hazard layers (`reach_probability`, `max_kinetic_energy`, `max_jump_height`) was queried against roads/transport, barriers/protection, and water/channels with a 20 m proximity radius. The measured result is conservative and unresolved: all three context categories returned zero overlap/proximity cells within 20 m for the selected top-cell envelope. This is interpretation evidence only; it does not imply obstacle absence or obstacle physics.
- Evidence streams consumed: `docs/tschamut_public_obstacle_context_scope.md`, `docs/tschamut_public_conditional_pilot_gate_report.md`, `docs/tschamut_public_same_scale_uncertainty_envelope.md`, `scripts/inspect_tschamut_public_context_layers.py`, `hazard/results/tschamut_public_pilot/target_gate_v1/validation_tschamut_public_target_gate_v1_manifest.json`, and `data/processed/swisstopo/tschamut_public_pilot/context/swisstlm3d/metadata.json`.
- Classification: `unresolved` at the hazard-context overlap envelope; `operational_claims_allowed` remains false and `scale_up_authorized` remains false.
- Uncertainty reduced: the repo now has a reusable, executable overlap diagnostic that measures corridor-context proximity against selected hazard cells instead of only reporting corridor-level context relevance.
- Remaining uncertainty: the top-cell envelope still does not show a measured roads/barriers/water proximity hit within 20 m, so the context interpretation remains conditional and not obstacle physics.
- Checks run:
  `PYENV_VERSION=system uv run python -m py_compile scripts/measure_hazard_context_overlap.py tests/test_hazard_context_overlap.py`
  passed.
  `PYENV_VERSION=system uv run python -m unittest tests.test_hazard_context_overlap`
  passed.
  `PYENV_VERSION=system uv run python scripts/measure_hazard_context_overlap.py --top-cell-count 1 --buffer-radii-m 20 --hazard-layer reach_probability --hazard-layer max_kinetic_energy --hazard-layer max_jump_height --format json`
  passed and produced the measured overlap JSON.
  `git diff --check`
  passed.
  `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  passed.
  `scripts/git-hooks/pre-commit`
  passed.
- Reviewer notes: The corridor context remains limiting, but the top-cell overlap envelope did not produce a proximity hit for the measured categories. That is useful boundary evidence, not acceptance.
- Decision: COMPLETED.
- Next proposed milestone: TB-022.

### TB-022

- Milestone id: TB-022.
- Roadmap item: Add Same-Scale Artifact Readiness Preflight.
- Implementation summary: Added `scripts/check_same_scale_artifact_readiness.py` and focused tests. The new read-only preflight checks gate validation, gate hazard, target validation, target hazard, target `summary_only` validation, staged public context, swissTLM3D metadata, hazard/context overlap inputs, and same-scale uncertainty-envelope inputs. It reports exact missing paths plus known regeneration commands before expensive same-scale diagnostics.
- Evidence streams consumed: `scripts/audit_local_artifacts.py`, `docs/tschamut_public_conditional_pilot_gate_report.md`, `docs/tschamut_public_same_scale_uncertainty_envelope.md`, `docs/tschamut_public_bounded_validation_output_profile.md`, `docs/tschamut_public_obstacle_context_scope.md`, `scripts/validate_public_real_site_conditional_pilot_run.py`, `scripts/build_hazard_layers.py`, `scripts/compare_hazard_map_convergence.py`, `scripts/inspect_tschamut_public_context_layers.py`, `scripts/measure_hazard_context_overlap.py`, and the local same-scale gate/target/context manifests.
- Classification: `ready` for the local checkout; `scale_up_authorized` remains false and `operational_claims_allowed` remains false.
- Uncertainty reduced: future workers can check exact artifact readiness and regeneration paths before running convergence, output-profile, context, or overlap diagnostics.
- Remaining uncertainty: the same-scale target-vs-gate interpretation remains inconclusive; the preflight only removes repeated discovery overhead.
- Checks run:
  `PYENV_VERSION=system uv run python -m py_compile scripts/check_same_scale_artifact_readiness.py tests/test_same_scale_artifact_readiness.py`
  passed.
  `PYENV_VERSION=system uv run python scripts/check_same_scale_artifact_readiness.py --format json`
  passed.
  `PYENV_VERSION=system uv run python -m unittest tests.test_same_scale_artifact_readiness`
  passed.

### TB-023

- Milestone id: TB-023.
- Roadmap item: Broaden Hazard-Context Overlap Envelope Beyond Top Cells.
- Implementation summary: Broadened the reusable hazard-context overlap
  diagnostic from the earlier top-cell-only probe to a bounded higher-
  relevance envelope. A `top 3` probe over `reach_probability` and
  `max_kinetic_energy` completed successfully against the staged swissTLM3D
  archive; both measured categories remained at zero within 20 m for roads,
  barriers, and water. A three-layer probe that added `max_jump_height` was
  runtime-limited and not counted in the final measured envelope.
- Evidence streams consumed: `scripts/check_same_scale_artifact_readiness.py`,
  `scripts/measure_hazard_context_overlap.py`,
  `docs/tschamut_public_obstacle_context_scope.md`,
  `docs/tschamut_public_conditional_pilot_gate_report.md`,
  `docs/tschamut_public_same_scale_uncertainty_envelope.md`, and the staged
  target hazard/context artifacts.
- Classification: `unresolved` for the bounded overlap envelope; `scale_up_authorized`
  remains false and `operational_claims_allowed` remains false.
- Uncertainty reduced: the corridor interpretation now has measured proximity
  evidence for a broader high-relevance hazard envelope instead of only a
  single top cell per layer.
- Remaining uncertainty: the broader envelope still did not produce roads,
  barriers, or water proximity hits within 20 m, and the three-layer probe
  could not be sustained within a practical runtime bound.
- Checks run:
  `PYENV_VERSION=system uv run python scripts/check_same_scale_artifact_readiness.py --format json`
  passed.
  `PYENV_VERSION=system timeout 180 uv run python scripts/measure_hazard_context_overlap.py --top-cell-count 3 --buffer-radii-m 20 --hazard-layer reach_probability --format json`
  passed.
  `PYENV_VERSION=system timeout 180 uv run python scripts/measure_hazard_context_overlap.py --top-cell-count 3 --buffer-radii-m 20 --hazard-layer reach_probability --hazard-layer max_kinetic_energy --format json`
  passed.
  `PYENV_VERSION=system timeout 180 uv run python scripts/measure_hazard_context_overlap.py --top-cell-count 3 --buffer-radii-m 20 --hazard-layer reach_probability --hazard-layer max_kinetic_energy --hazard-layer max_jump_height --format json`
  was runtime-limited and killed after bounded waiting.
  `git diff --check`
  passed.
  `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  passed.
  `scripts/git-hooks/pre-commit`
  passed.
- Roadmap item: TB-026 hardened source-zone and block-scenario case regeneration.
- Files changed: `scripts/generate_tschamut_same_scale_cases.py`,
  `tests/test_tschamut_same_scale_case_generation.py`,
  `docs/task_backlog.md`,
  `docs/tschamut_public_conditional_pilot_gate_report.md`,
  `docs/tschamut_public_same_scale_uncertainty_envelope.md`.
- Evidence streams consumed: `validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml`,
  `validation/pilot_runs/tschamut_public_scalable_conditional_target_gate_v1.yaml`,
  `validation/policies/tschamut_public_source_scenario_policy_v1.yaml`,
  `data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_source_zone_metadata_v1.yaml`,
  `data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_scenario_table_v1.csv`,
  `data/processed/swisstopo/tschamut_public_pilot/input/release_points_lv95.csv`,
  `data/processed/swisstopo/tschamut_public_pilot/input/observed_deposition_lv95.csv`.
- Classification: `ready`.
- Uncertainty reduced: gate and target private case regeneration is now deterministic from committed records and processed public inputs.
- Remaining uncertainty: none for the case-regeneration path itself; future work can use the helper to recreate ignored private cases without manual editing.
- Checks run: `PYENV_VERSION=system uv run python -m py_compile scripts/generate_tschamut_same_scale_cases.py tests/test_tschamut_same_scale_case_generation.py`,
  `PYENV_VERSION=system uv run python -m unittest tests.test_tschamut_same_scale_case_generation`,
  `PYENV_VERSION=system uv run python scripts/generate_tschamut_same_scale_cases.py --format json --dry-run`,
  `PYENV_VERSION=system uv run python scripts/generate_tschamut_same_scale_cases.py --format json`.

- Roadmap item: TB-027 added a second-site public-geodata portability preflight.
- Files changed: `scripts/check_second_site_public_geodata_preflight.py`,
  `tests/test_second_site_public_geodata_preflight.py`,
  `tests/fixtures/second_site_public_geodata_preflight/site_template.yaml`,
  `docs/task_backlog.md`,
  `docs/public_real_site_geodata_preparation.md`,
  `docs/swisstopo_data_strategy.md`,
  `docs/tschamut_public_conditional_pilot_gate_report.md`,
  `docs/tschamut_public_same_scale_uncertainty_envelope.md`.
- Evidence streams consumed: the Tschamut same-scale readiness preflight,
  public real-site geodata preparation contract, swisstopo data strategy,
  Tschamut case regeneration helper, pilot run-freeze validator, and the
  current Tschamut input metadata as a reusable template.
- Classification: `blocked_missing_inputs` by default; `ready` when a
  second-site config plus required synthetic fixture paths are present.
- Uncertainty reduced: the repo now has a reusable metadata-only portability
  preflight that distinguishes reusable Tschamut workflow components from
  second-site public-geodata prerequisites and missing command-plan inputs.
- Remaining uncertainty: the actual second-site public geodata, site extent,
  and source-zone/scenario records still need to be staged before any real
  second-site pilot can be attempted.
- Checks run: `PYENV_VERSION=system uv run python -m py_compile scripts/check_second_site_public_geodata_preflight.py tests/test_second_site_public_geodata_preflight.py`,
  `PYENV_VERSION=system uv run python -m unittest tests.test_second_site_public_geodata_preflight`,
  `PYENV_VERSION=system uv run python scripts/check_second_site_public_geodata_preflight.py --format json`.

- Roadmap item: TB-028 staged a placeholder second-site public-geodata
  manifest/config.
- Files changed: `scripts/check_second_site_public_geodata_preflight.py`,
  `tests/test_second_site_public_geodata_preflight.py`,
  `tests/fixtures/second_site_public_geodata_preflight/candidate_placeholder_site.yaml`,
  `docs/task_backlog.md`,
  `docs/public_real_site_geodata_preparation.md`,
  `docs/swisstopo_data_strategy.md`.
- Evidence streams consumed: the generic second-site portability preflight,
  the Tschamut same-scale readiness preflight, the public real-site
  geodata-preparation contract, the swisstopo data-strategy contract, and the
  Tschamut processed-input contract as a reusable example.
- Classification: `blocked_missing_inputs` for the staged placeholder
  candidate.
- Uncertainty reduced: the portability helper now has a concrete placeholder
  candidate manifest that surfaces site-specific missing inputs and staging
  paths instead of only a generic template state.
- Remaining uncertainty: no real second-site public geodata or site-specific
  source-zone/scenario records have been staged yet.
- Checks run: `PYENV_VERSION=system uv run python -m py_compile scripts/check_second_site_public_geodata_preflight.py tests/test_second_site_public_geodata_preflight.py`,
  `PYENV_VERSION=system uv run python -m unittest tests.test_second_site_public_geodata_preflight`,
  `PYENV_VERSION=system uv run python scripts/check_second_site_public_geodata_preflight.py --site-config tests/fixtures/second_site_public_geodata_preflight/candidate_placeholder_site.yaml --format json`.

- Roadmap item: TB-029 added a concrete Chant Sura / Flüelapass second-site
  manifest example at
  `tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml`.
- Files changed: `scripts/check_second_site_public_geodata_preflight.py`,
  `tests/test_second_site_public_geodata_preflight.py`,
  `tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml`,
  `docs/task_backlog.md`,
  `docs/public_real_site_geodata_preparation.md`,
  `docs/swisstopo_data_strategy.md`.
- Evidence streams consumed: the Tschamut same-scale readiness preflight, the
  generic second-site portability preflight, Chant Sura dataset metadata in
  `data/datasets.yaml`, and the public-real-site geodata / swisstopo strategy
  docs.
- Classification: `blocked_missing_inputs` for the Chant Sura portability
  example; `staged_candidate_manifest` as the manifest status.
- Uncertainty reduced: the portability helper now distinguishes a concrete
  Swiss candidate example from a generic placeholder and reports terrain,
  source-zone, and scenario manifest statuses explicitly.
- Remaining uncertainty: the site still has no staged terrain, source-zone,
  scenario, or public-context inputs, so it remains a metadata-only example.
- Checks run: `PYENV_VERSION=system uv run python -m py_compile scripts/check_second_site_public_geodata_preflight.py tests/test_second_site_public_geodata_preflight.py`,
  `PYENV_VERSION=system uv run python -m unittest tests.test_second_site_public_geodata_preflight`,
  `PYENV_VERSION=system uv run python scripts/check_second_site_public_geodata_preflight.py --site-config tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml --format json`.

- Roadmap item: TB-030 added a multisite source-zone / scenario contract
  audit at `scripts/audit_multisite_source_scenario_contract.py`.
- Files changed: `scripts/audit_multisite_source_scenario_contract.py`,
  `tests/test_multisite_source_scenario_contract.py`,
  `docs/public_real_site_geodata_preparation.md`,
  `docs/swisstopo_data_strategy.md`,
  `docs/tschamut_public_conditional_pilot_gate_report.md`,
  `docs/tschamut_public_same_scale_uncertainty_envelope.md`,
  `docs/task_backlog.md`.
- Evidence streams consumed: the Tschamut same-scale readiness preflight,
  the frozen Tschamut source-zone policy, the frozen gate/target run records,
  the Tschamut source-zone metadata and scenario table, and the Chant Sura /
  Flüelapass candidate portability manifest plus its blocked preflight.
- Classification: `measured` for the audit, with the Chant Sura candidate
  still `blocked_missing_inputs`.
- Uncertainty reduced: the repo now separates portable source/scenario
  contract shape from Tschamut-specific heuristics, and it records which
  second-site inputs remain missing before a non-Tschamut pilot can be staged.
- Remaining uncertainty: the Chant Sura / Flüelapass candidate still lacks
  staged terrain, source-zone, scenario, and context artifacts.
- Checks run: `PYENV_VERSION=system uv run python -m py_compile scripts/audit_multisite_source_scenario_contract.py tests/test_multisite_source_scenario_contract.py`,
  `PYENV_VERSION=system uv run python -m unittest tests.test_multisite_source_scenario_contract`,
  `PYENV_VERSION=system uv run python scripts/audit_multisite_source_scenario_contract.py --format json`.

- TB-031 multi-seed same-scale uncertainty envelope. Files changed:
  `scripts/summarize_same_scale_sampling_uncertainty.py`,
  `tests/test_same_scale_sampling_uncertainty.py`,
  `validation/private/tschamut_public_pilot/sampling_sensitivity_v2_full/tschamut_public_sampling_sensitivity_v2_full_case.yaml`,
  `docs/tschamut_public_same_scale_uncertainty_envelope.md`,
  `docs/tschamut_public_conditional_pilot_gate_report.md`,
  `docs/task_backlog.md`.
- Evidence streams consumed: the Tschamut readiness preflight, the gate and
  target same-scale manifests, the bounded sampling-sensitivity probe v1, and
  the new bounded same-size probe v2 with seed `34015` and ensemble size `12`.
- Classification: `sampling_uncertainty_measured`.
- Uncertainty reduced: the envelope now spans two bounded 12-trajectory seeds
  and shows that `max_kinetic_energy` remains dominant while `max_jump_height`
  retains support/nodata sensitivity and the velocity-exceedance layers remain
  lower-order.
- Remaining uncertainty: seed sensitivity still limits the shared-grid
  interpretation, `max_kinetic_energy` still dominates, and the pilot remains
  conservative and non-operational.
- Checks run: `PYENV_VERSION=system uv run python scripts/check_same_scale_artifact_readiness.py --format json`,
  `PYENV_VERSION=system uv run python scripts/summarize_same_scale_sampling_uncertainty.py --json-output /tmp/tschamut_sampling_uncertainty.json --markdown-output docs/tschamut_public_same_scale_uncertainty_envelope.md`,
  `PYENV_VERSION=system uv run python -m py_compile scripts/summarize_same_scale_sampling_uncertainty.py tests/test_same_scale_sampling_uncertainty.py`,
  `PYENV_VERSION=system uv run python -m unittest tests.test_same_scale_sampling_uncertainty`.
- TB-032 completed by adding `scripts/generate_pilot_command_plan.py` with
  canonical Tschamut and Chant Sura / Flüelapass command plans. Updated the
  fast-path docs to point at the helper, added
  `tests/test_pilot_command_plan.py`, removed TB-032 from the backlog, and
  verified the helper in JSON and text modes. Checks run:
  `PYENV_VERSION=system uv run python -m py_compile scripts/generate_pilot_command_plan.py tests/test_pilot_command_plan.py`,
  `PYENV_VERSION=system uv run python -m unittest tests.test_pilot_command_plan`,
  `PYENV_VERSION=system uv run python scripts/generate_pilot_command_plan.py --site tschamut_same_scale --format json`,
  `PYENV_VERSION=system uv run python scripts/generate_pilot_command_plan.py --site chant_sura_fluelapass --site-config tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml --format json`.

- TB-033 GIS/COG package readiness audit. Files changed:
  `scripts/audit_gis_cog_package_readiness.py`,
  `tests/test_gis_cog_package_readiness.py`,
  `docs/public_real_site_geodata_preparation.md`,
  `docs/swisstopo_data_strategy.md`,
  `docs/tschamut_public_conditional_pilot_gate_report.md`,
  `docs/tschamut_public_same_scale_uncertainty_envelope.md`,
  `docs/task_backlog.md`.
- Evidence streams consumed: the same-scale readiness preflight, the four
  existing same-scale hazard roots, the four map-package manifests, the four
  pilot-GIS manifests, and bounded `gdalinfo` metadata from representative
  GeoTIFFs.
- Classification: `gis_package_ready_cog_blocked`.
- Uncertainty reduced: the current same-scale outputs are manifest-complete
  with GeoTIFFs present and consistent LV95/LN02 grid metadata, so package
  readiness is no longer a missing-manifest question.
- Remaining uncertainty: the GeoTIFFs are strip-organized, not cloud-optimized,
  and have no overviews, so COG readiness remains blocked. Manual QGIS QA is
  still not run.
- Checks run:
  `PYENV_VERSION=system uv run python scripts/check_same_scale_artifact_readiness.py --format json`,
  `gdalinfo --version`,
  `PYENV_VERSION=system uv run python -m py_compile scripts/audit_gis_cog_package_readiness.py tests/test_gis_cog_package_readiness.py`,
  `PYENV_VERSION=system uv run python -m unittest tests.test_gis_cog_package_readiness`,
  `PYENV_VERSION=system uv run python scripts/audit_gis_cog_package_readiness.py --format json`.

- TB-034 bounded reducer/runtime scaling measurement. Files changed:
  `scripts/summarize_bounded_reducer_runtime_scaling.py`,
  `tests/test_bounded_reducer_runtime_scaling.py`,
  `docs/balfrin_single_job_execution_sufficiency.md`,
  `docs/task_backlog.md`.
- Evidence streams consumed: the same-scale readiness preflight, the canonical
  Tschamut command-plan helper, and the four existing same-scale artifacts
  `gate_v1`, `target_gate_v1`, `sampling_sensitivity_v1_full`, and
  `sampling_sensitivity_v2_full`.
- Classification: `measured_existing_artifacts` with bottleneck
  `validation_output_size`.
- Measured runtime/output evidence: target validation `272.573375917 s` and
  `571368823 bytes`; gate validation `3.999294125 s` and `34545900 bytes`;
  target hazard `41.61543712497223 s` and `22061720 bytes`; gate hazard
  `7.108489040983841 s` and `21025596 bytes`.
- Reducer evidence: target and gate hazard manifests both record `2` workers
  with `22` cellwise layers; the bounded sampling probes remain at the same
  output scale without a distributed-reducer signal.
- Conclusion: local single-job execution remains sufficient for the next
  same-scale step and distributed execution remains unauthorized.
- Checks run:
  `PYENV_VERSION=system uv run python scripts/check_same_scale_artifact_readiness.py --format json`,
  `PYENV_VERSION=system uv run python scripts/generate_pilot_command_plan.py --site tschamut_same_scale --format json`,
  `PYENV_VERSION=system uv run python -m py_compile scripts/summarize_bounded_reducer_runtime_scaling.py tests/test_bounded_reducer_runtime_scaling.py`,
  `PYENV_VERSION=system uv run python -m unittest tests.test_bounded_reducer_runtime_scaling`,
  `PYENV_VERSION=system uv run python scripts/summarize_bounded_reducer_runtime_scaling.py --format json`,
  `PYENV_VERSION=system uv run python scripts/summarize_bounded_reducer_runtime_scaling.py --format text`.

- TB-037 spatial same-scale uncertainty interpretation. Files changed:
  `scripts/summarize_spatial_same_scale_uncertainty.py`,
  `tests/test_spatial_same_scale_uncertainty.py`,
  `docs/tschamut_public_same_scale_uncertainty_envelope.md`,
  `docs/tschamut_public_conditional_pilot_gate_report.md`,
  `docs/task_backlog.md`.
- Evidence streams consumed: the same-scale readiness preflight, the sampling
  uncertainty envelope, and the four same-scale hazard manifests for gate,
  target, and the two bounded probes.
- Classification: `measured_existing_artifacts`.
- Spatial interpretation: `max_kinetic_energy` is still the dominant
  disagreement field, but the highest-uncertainty cells cluster in a compact
  LV95 corridor; `max_jump_height` is dominated by support/nodata differences;
  `velocity_exceedance_5mps` is localized with much smaller range.
- Checks run:
  `PYENV_VERSION=system uv run python -m py_compile scripts/summarize_spatial_same_scale_uncertainty.py tests/test_spatial_same_scale_uncertainty.py`,
  `PYENV_VERSION=system uv run python -m unittest tests.test_spatial_same_scale_uncertainty`,
  `PYENV_VERSION=system uv run python scripts/summarize_spatial_same_scale_uncertainty.py --format json`,
  `PYENV_VERSION=system uv run python scripts/summarize_spatial_same_scale_uncertainty.py --format text`.

- TB-039 Chant Sura public-geodata acquisition manifest. Files changed:
  `tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_public_geodata_acquisition.yaml`,
  `tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml`,
  `scripts/check_second_site_public_geodata_preflight.py`,
  `scripts/generate_pilot_command_plan.py`,
  `tests/test_second_site_public_geodata_preflight.py`,
  `tests/test_pilot_command_plan.py`,
  `docs/public_real_site_geodata_preparation.md`,
  `docs/swisstopo_data_strategy.md`,
  `docs/task_backlog.md`.
- Evidence streams consumed: the second-site portability preflight, the multisite
  source/scenario contract audit, and the portable command plan for Chant Sura /
  Flüelapass.
- Classification: `blocked_missing_inputs` with `acquisition_manifest_status=ready`.
- Manifest status: the committed acquisition manifest now names the expected
  swissALTI3D terrain crop, SWISSIMAGE, swissTLM3D, swissSURFACE3D,
  swissSURFACE3D Raster, swissBUILDINGS3D, source-zone, scenario, optional
  barrier inventory, and ignored output roots. The second-site preflight still
  reports missing terrain/context/source/scenario staging paths, so the site
  remains metadata-only.
- Checks run:
  `PYENV_VERSION=system uv run python -m py_compile scripts/check_second_site_public_geodata_preflight.py tests/test_second_site_public_geodata_preflight.py scripts/generate_pilot_command_plan.py tests/test_pilot_command_plan.py`,
  `PYENV_VERSION=system uv run python -m unittest tests.test_second_site_public_geodata_preflight tests.test_pilot_command_plan`,
  `PYENV_VERSION=system uv run python scripts/check_second_site_public_geodata_preflight.py --site-config tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml --format json`,
  `PYENV_VERSION=system uv run python scripts/audit_multisite_source_scenario_contract.py --format json`,
  `PYENV_VERSION=system uv run python scripts/generate_pilot_command_plan.py --site chant_sura_fluelapass --site-config tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml --format json`.

- Backlog refill after TB-031 through TB-034.
- Files changed: `docs/task_backlog.md`.
- Evidence streams consumed: the multi-seed same-scale uncertainty envelope,
  portable command-plan helper, GIS/COG package audit, bounded
  reducer/runtime scaling summary, same-scale readiness preflight, and
  second-site portability docs.
- Current maturity assessment: same-scale Tschamut execution is reproducible
  and measured; convergence remains inconclusive; target validation output is
  the dominant measured output pressure; GIS packages are manifest-complete but
  COG-blocked; local single-job execution remains sufficient for the next
  same-scale step; Chant Sura / Flüelapass remains metadata-only and
  blocked-missing-inputs.
- Backlog direction: prioritize conditional pilot closure criteria,
  rebuildable reduced validation output, bounded COG conversion, concrete
  Chant Sura public-geodata acquisition staging, and validation/calibration
  evidence-gap analysis.
- Boundaries preserved: no physics changes, no parameter tuning, no scale-up
  authorization, no distributed execution authorization, and no operational,
  annual-frequency, risk, exposure, or vulnerability claims.

### TB-035 Conditional Pilot Closure Criteria

- Milestone id: TB-035.
- Roadmap item: Conditional pilot closure criteria from measured evidence.
- Hypothesis/objective: A reusable closure helper can synthesize the measured
  same-scale convergence, output-profile, GIS/COG, context, runtime, and
  second-site portability evidence into explicit accepted/no-go/deferred
  criteria while preserving the current inconclusive closure status.
- Files intended to change:
  `scripts/summarize_tschamut_conditional_pilot_closure.py`,
  `tests/test_tschamut_conditional_pilot_closure.py`,
  `docs/tschamut_public_conditional_pilot_gate_report.md`,
  `docs/task_backlog.md`,
  `docs/agent_work_log.md`
- Implementation summary: Added a read-only closure helper that composes the
  existing readiness, uncertainty, output-profile, GIS/COG, reducer/runtime,
  context, portability, and multisite-contract evidence into a compact closure
  matrix with explicit accepted_diagnostic, no_go, and deferred requirement
  sets. The helper derives the current closure status as inconclusive and
  keeps scale-up and operational claims false.
- Checks run:
  `PYENV_VERSION=system uv run python -m py_compile scripts/summarize_tschamut_conditional_pilot_closure.py tests/test_tschamut_conditional_pilot_closure.py`,
  `PYENV_VERSION=system uv run python -m unittest tests.test_tschamut_conditional_pilot_closure`,
  `PYENV_VERSION=system uv run python scripts/summarize_tschamut_conditional_pilot_closure.py --format json >/tmp/tb035_closure.json`,
  `PYENV_VERSION=system uv run python scripts/summarize_tschamut_conditional_pilot_closure.py --format text`,
  `git diff --check`,
  `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`,
  `scripts/git-hooks/pre-commit`.
- Reviewer notes: The closure helper is diagnostic only; it does not change
  simulator physics, thresholds, release assumptions, or validation cases.
- Decision: ACCEPT.
- Next proposed milestone: TB-036.

- Backlog adjustment after external review of TB-035 follow-up priorities.
- Files changed: `docs/task_backlog.md`.
- Input assessed: existing same-scale uncertainty tooling is strong on scalar
  pairwise metrics, layer summaries, and envelope ranges, but does not yet
  answer the spatial question of where uncertainty concentrates across seeds
  and layers.
- Decision: ACCEPT with priority adjustment. Added spatial same-scale
  uncertainty interpretation tooling as TB-037, after the
  hazard-rebuild-compatible reduced-output blocker and before COG conversion,
  second-site acquisition staging, and validation/calibration evidence-gap
  work.
- Boundaries preserved: no physics changes, no parameter tuning, no scale-up
  authorization, no operational claims, and no large committed raster outputs.

### TB-038 Bounded COG Conversion Proof Of Concept

- Milestone id: TB-038.
- Roadmap item: Bounded COG conversion proof of concept.
- Hypothesis/objective: A single same-scale GeoTIFF can be converted to a
  COG-ready scratch output with GDAL, and the GIS/COG audit can distinguish
  that converted sample from the still-blocked committed package roots.
- Files changed:
  `scripts/prototype_cog_conversion.py`,
  `scripts/audit_gis_cog_package_readiness.py`,
  `tests/test_cog_conversion_prototype.py`,
  `tests/test_gis_cog_package_readiness.py`,
  `docs/public_real_site_geodata_preparation.md`,
  `docs/swisstopo_data_strategy.md`,
  `docs/tschamut_public_conditional_pilot_gate_report.md`,
  `docs/task_backlog.md`,
  `docs/agent_work_log.md`
- Implementation summary: Added a bounded COG conversion prototype that uses
  `gdal_translate -of COG -co BLOCKSIZE=256 -co COMPRESS=ZSTD` on a single
  same-scale raster and verifies the scratch output with `gdalinfo`. The
  prototype produced a tiled COG with overviews under `/tmp`, while the
  existing same-scale packages remain `gis_package_ready_cog_blocked`. The GIS
  audit now distinguishes the committed package state from a converted sample
  state via `converted_sample_status`.
- Checks run:
  `PYENV_VERSION=system uv run python -m py_compile scripts/prototype_cog_conversion.py tests/test_cog_conversion_prototype.py scripts/audit_gis_cog_package_readiness.py tests/test_gis_cog_package_readiness.py`,
  `PYENV_VERSION=system uv run python -m unittest tests.test_cog_conversion_prototype tests.test_gis_cog_package_readiness`,
  `PYENV_VERSION=system uv run python scripts/prototype_cog_conversion.py --help`,
  `PYENV_VERSION=system uv run python scripts/audit_gis_cog_package_readiness.py --format json`,
  `PYENV_VERSION=system uv run python scripts/audit_gis_cog_package_readiness.py --format json --converted-sample /tmp/tschamut_cog_poc.tif`,
  `git diff --check`,
  `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`,
  `scripts/git-hooks/pre-commit`.
- Reviewer notes: The scratch COG sample lives only in `/tmp` and does not
  modify committed hazard outputs.
- Decision: ACCEPT.
- Next proposed milestone: TB-039.

### TB-036 Hazard-Rebuild-Compatible Reduced Output Profile

- Milestone id: TB-036.
- Roadmap item: Hazard-rebuild-compatible reduced output profile.
- Hypothesis/objective: The hazard builder only needs a small builder-facing
  subset of validation outputs, and the repo can now distinguish the current
  `summary_only_not_rebuildable` profile from a hazard-rebuild-ready reduced
  contract without changing simulation semantics.
- Files changed:
  `scripts/check_hazard_rebuild_output_profile.py`,
  `tests/test_hazard_rebuild_output_profile.py`,
  `docs/tschamut_public_bounded_validation_output_profile.md`,
  `docs/tschamut_public_conditional_pilot_gate_report.md`,
  `docs/task_backlog.md`,
  `docs/agent_work_log.md`
- Implementation summary: Added a read-only hazard-rebuild audit that reads
  the current summary-only and full bounded-probe manifests, compares their
  output families against the inputs consumed by `scripts/build_hazard_layers.py`,
  and reports a minimal builder-facing contract. The current target summary-only
  profile is `summary_only_not_rebuildable`; both bounded probes are
  `hazard_rebuild_ready`. The specified reduced contract retains trajectory,
  deposition, impact-event, and diagnostics families, while treating trajectory
  metadata and stop-state as optional overhead.
- Checks run:
  `PYENV_VERSION=system uv run python -m py_compile scripts/check_hazard_rebuild_output_profile.py tests/test_hazard_rebuild_output_profile.py`,
  `PYENV_VERSION=system uv run python -m unittest tests.test_hazard_rebuild_output_profile`,
  `PYENV_VERSION=system uv run python scripts/check_hazard_rebuild_output_profile.py --format json`,
  `PYENV_VERSION=system uv run python scripts/check_hazard_rebuild_output_profile.py --format text`,
  `git diff --check`,
  `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`,
  `scripts/git-hooks/pre-commit`.
- Reviewer notes: This helper is a compatibility audit only. It does not
  regenerate hazard outputs or change the reduced-output profile in place.
- Decision: ACCEPT.
- Next proposed milestone: TB-037.

- TB-040 validation and calibration evidence-gap assessment. Files changed:
  `scripts/assess_validation_calibration_evidence_gaps.py`,
  `tests/test_validation_calibration_evidence_gaps.py`,
  `docs/tschamut_public_conditional_pilot_gate_report.md`,
  `docs/public_real_site_geodata_preparation.md`,
  `docs/swisstopo_data_strategy.md`,
  `docs/task_backlog.md`,
  `docs/agent_work_log.md`.
- Evidence streams consumed: the Tschamut gate and target run freezes, the
  same-scale uncertainty envelope, the second-site portability preflight, the
  Chant Sura contact and held-out fixtures, the Schiers dataset metadata
  entry, the Balfrin single-job sufficiency record, and the swisstopo / public
  real-site portability docs.
- Derived status: `physical_credibility_status=not_established`,
  `calibration_status=missing`, `validation_status=partial`.
- Interpretation: current same-scale evidence is strong for workflow
  reproducibility and diagnostic interpretation but is still not physically
  credible; calibration and block-population evidence are missing, and the
  holdout boundary remains only partially satisfied.
- Checks run:
  `PYENV_VERSION=system uv run python -m py_compile scripts/assess_validation_calibration_evidence_gaps.py tests/test_validation_calibration_evidence_gaps.py`,
  `PYENV_VERSION=system uv run python -m unittest tests.test_validation_calibration_evidence_gaps`,
  `PYENV_VERSION=system uv run python scripts/assess_validation_calibration_evidence_gaps.py --format json`,
  `PYENV_VERSION=system uv run python scripts/assess_validation_calibration_evidence_gaps.py --format text`.

- Sub-agent efficiency bootstrap helper.
- Hypothesis/objective: recurring worker friction around repo root, pyenv,
  canonical helper discovery, stray placeholder artifacts, and known pre-push
  failures can be reduced with one read-only task-context helper plus concise
  agent guidance.
- Files changed:
  `scripts/print_agent_task_context.py`,
  `tests/test_agent_task_context.py`,
  `AGENTS.md`,
  `docs/task_backlog.md`,
  `docs/agent_work_log.md`.
- Implementation summary: Added `scripts/print_agent_task_context.py`, a
  read-only bootstrap that reports the active backlog task, inspect-first
  files, canonical helper scripts, known local environment issues,
  generated roots to avoid, and the parquet rlib pre-push fallback. Updated
  agent/backlog guidance to make this helper the first TB-task command.
- Boundaries preserved: no simulator behavior, evidence classification,
  validation case, physics, geodata, or hazard-output changes.

- High-level reviewer finding triage after TB-040 and the task-context
  bootstrap.
- Files changed: `docs/task_backlog.md`.
- Decision summary:
  - ACCEPT into backlog: implement the rebuildable reduced-output profile,
    wire spatial uncertainty into closure logic, regenerate one ignored
    COG-ready same-scale package, and stage minimal Chant Sura inputs.
  - KEEP already active: TB-041 Chant Sura holdout evidence manifest.
  - DEFER: distributed execution, large ensembles, manual QGIS QA, operational
    semantics, risk/exposure/vulnerability, and broad helper consolidation.
  - DISMISS: no reviewer finding was dismissed as irrelevant; deferrals are
    due to current priority and readiness, not irrelevance.
- Boundaries preserved: no physics changes, no tuning, no scale-up
  authorization, no operational claims, and no generated geodata committed.

- Backlog refill after TB-040 maturity reassessment.
- Files changed: `docs/task_backlog.md`.
- Evidence streams consumed: same-scale readiness, closure criteria, multi-seed
  and spatial uncertainty summaries, bounded output profile, reducer/runtime
  scaling, GIS/COG audit and COG proof, Chant Sura acquisition manifest, and
  validation/calibration evidence-gap assessment.
- Decision summary: the current active queue TB-041 through TB-045 remains the
  right sequence. The backlog context was updated so completed areas are no
  longer described as missing: spatial uncertainty is measured, COG conversion
  is proven on a scratch sample, closure criteria exist, Chant Sura has an
  acquisition manifest, and physical credibility remains not established.
- Rationale: prioritize holdout evidence, rebuildable reduced output, spatial
  closure interpretation, ignored COG-ready package regeneration, and minimal
  Chant Sura input staging. Defer distributed execution, operational semantics,
  annual-frequency modelling, risk/exposure/vulnerability, large ensembles, and
  helper consolidation.

- TB-041 Chant Sura holdout evidence manifest.
- Files changed:
  `scripts/summarize_chant_sura_holdout_evidence.py`,
  `tests/test_chant_sura_holdout_evidence.py`,
  `validation/data/processed/chant_sura_2020/holdout_validation_evidence_manifest.json`,
  `docs/chant_sura_contact_validation.md`,
  `docs/chant_sura_contact_generalization.md`,
  `docs/task_backlog.md`,
  `docs/agent_work_log.md`.
- Implementation summary: staged a durable read-only Chant Sura holdout
  manifest that separates diagnostic/model-selection evidence from
  independent holdout-validation evidence, keeps calibration and physical
  probability out of scope, and makes the no-overlap boundary machine-readable
  for downstream evidence-gap checks.
- Checks run:
  `PYENV_VERSION=system uv run python -m py_compile scripts/summarize_chant_sura_holdout_evidence.py tests/test_chant_sura_holdout_evidence.py`,
  `PYENV_VERSION=system uv run python -m unittest tests.test_chant_sura_holdout_evidence`,
  `PYENV_VERSION=system uv run python scripts/summarize_chant_sura_holdout_evidence.py --format json`,
  `PYENV_VERSION=system uv run python scripts/summarize_chant_sura_holdout_evidence.py --format text`.

- TB-043 spatial uncertainty integration into conditional closure logic.
- Files changed:
  `scripts/summarize_tschamut_conditional_pilot_closure.py`,
  `tests/test_tschamut_conditional_pilot_closure.py`,
  `docs/tschamut_public_conditional_pilot_gate_report.md`,
  `docs/tschamut_public_same_scale_uncertainty_envelope.md`,
  `docs/task_backlog.md`,
  `docs/agent_work_log.md`.
- Implementation summary: the closure helper now consumes the spatial
  same-scale uncertainty summary directly and records per-layer closure roles
  so `max_kinetic_energy` and `max_jump_height` remain closure-limiting while
  `velocity_exceedance_5mps` is deferrable under the current evidence.
- Boundaries preserved: no physics changes, no tuning, no new ensembles, no
  annual-frequency / risk / exposure / vulnerability / operational claims.

- TB-042 hazard-rebuild-compatible reduced output profile.
- Files changed:
  `scripts/derive_hazard_rebuild_reduced_profile.py`,
  `scripts/check_hazard_rebuild_output_profile.py`,
  `tests/test_hazard_rebuild_output_profile.py`,
  `tests/test_hazard_rebuild_reduced_profile.py`,
  `docs/tschamut_public_bounded_validation_output_profile.md`,
  `docs/tschamut_public_conditional_pilot_gate_report.md`,
  `docs/task_backlog.md`.
- Evidence streams consumed: current summary-only/full hazard-rebuild contract,
  the current full target validation manifest, the reduced-root derivation
  helper, and the hazard-layer builder proof on the derived reduced root.
- Result: `rebuildable_reduced_output` is now a concrete reduced profile on the
  ignored local root
  `validation/private/tschamut_public_pilot/target_gate_v1_rebuildable_reduced`;
  the checker classifies it as rebuildable, the current target summary-only
  profile remains `summary_only_not_rebuildable`, and the bounded probe
  profiles remain `hazard_rebuild_ready`.
- Checks run:
  `PYENV_VERSION=system uv run python -m py_compile scripts/derive_hazard_rebuild_reduced_profile.py scripts/check_hazard_rebuild_output_profile.py tests/test_hazard_rebuild_output_profile.py tests/test_hazard_rebuild_reduced_profile.py`,
  `PYENV_VERSION=system uv run python -m unittest tests.test_hazard_rebuild_output_profile tests.test_hazard_rebuild_reduced_profile`,
  `PYENV_VERSION=system uv run python scripts/derive_hazard_rebuild_reduced_profile.py --format json`,
  `PYENV_VERSION=system uv run python scripts/check_hazard_rebuild_output_profile.py --format json`,
  `PYENV_VERSION=system uv run python scripts/check_hazard_rebuild_output_profile.py --format text`,
  `/usr/bin/time -p env PYENV_VERSION=system uv run python scripts/build_hazard_layers.py --case validation/private/tschamut_public_pilot/target_gate_v1/tschamut_public_target_gate_case.yaml --trajectory validation/private/tschamut_public_pilot/target_gate_v1_rebuildable_reduced/validation_tschamut_public_target_gate_v1_trajectory.csv --deposition validation/private/tschamut_public_pilot/target_gate_v1_rebuildable_reduced/validation_tschamut_public_target_gate_v1_deposition.csv --impact-events validation/private/tschamut_public_pilot/target_gate_v1_rebuildable_reduced/validation_tschamut_public_target_gate_v1_rebuildable_reduced_impact_events.csv --diagnostics validation/private/tschamut_public_pilot/target_gate_v1_rebuildable_reduced/validation_tschamut_public_target_gate_v1_metrics.json --output-dir /tmp/tb042_reduced_hazard --grid-xmin 2696376.0 --grid-ymin 1167384.0 --grid-ncols 300 --grid-nrows 304 --grid-cell-size 2.0 --map-product-id tschamut_public_scalable_conditional_target_gate_v1_rebuildable_reduced --map-package-manifest-json /tmp/tb042_reduced_hazard/tschamut_public_scalable_conditional_target_gate_v1_rebuildable_reduced_map_package_manifest.json --export-geotiff --pilot-gis-package --pilot-gis-package-manifest-json /tmp/tb042_reduced_hazard/tschamut_public_scalable_conditional_target_gate_v1_rebuildable_reduced_pilot_gis_package_manifest.json --pilot-gis-qa-status not-run --pilot-gis-qa-note 'Reduced rebuildable profile proof; manual GIS/QGIS QA not run.' --trajectory-workers 2 --reducer-workers 2 --no-plots --conditional-curve-export summary-only --grid-csv-export none`,
  `git diff --check`,
  `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`,
  `scripts/git-hooks/pre-commit`.
- Result summary: reduced-root validation outputs are 5 files / 1,192,379 bytes
  plus a manifest for 6 files / 1,202,927 bytes total in the ignored reduced
  root; hazard builder proof wrote 63 files / 78,431,962 bytes to
  `/tmp/tb042_reduced_hazard`.

- TB-044 ignored same-scale GIS package as COG-ready.
- Files changed:
  `scripts/convert_same_scale_package_to_cog.py`,
  `scripts/audit_gis_cog_package_readiness.py`,
  `tests/test_same_scale_cog_package_conversion.py`,
  `docs/public_real_site_geodata_preparation.md`,
  `docs/swisstopo_data_strategy.md`,
  `docs/tschamut_public_conditional_pilot_gate_report.md`,
  `docs/task_backlog.md`,
  `docs/agent_work_log.md`.
- Evidence streams consumed: the current same-scale package manifests, the
  scratch COG proof helper, and the GIS/COG audit helper.
- Result: the ignored `hazard/results/tschamut_public_pilot/gate_v1_cog_poc`
  package audits as `cog_package_ready` with `cloud_optimized: true`
  metadata, while the standard `gate_v1`, `target_gate_v1`,
  `sampling_sensitivity_v1_full`, and `sampling_sensitivity_v2_full` package
  roots still audit as `gis_package_ready_cog_blocked`.
- Checks run:
  `PYENV_VERSION=system uv run python -m py_compile scripts/convert_same_scale_package_to_cog.py scripts/audit_gis_cog_package_readiness.py tests/test_same_scale_cog_package_conversion.py tests/test_gis_cog_package_readiness.py`,
  `PYENV_VERSION=system uv run python -m unittest tests.test_same_scale_cog_package_conversion tests.test_gis_cog_package_readiness`,
  `PYENV_VERSION=system uv run python scripts/convert_same_scale_package_to_cog.py --help`,
  `PYENV_VERSION=system uv run python scripts/audit_gis_cog_package_readiness.py --format json`,
  `PYENV_VERSION=system uv run python scripts/convert_same_scale_package_to_cog.py --input-root hazard/results/tschamut_public_pilot/gate_v1 --output-root hazard/results/tschamut_public_pilot/gate_v1_cog_poc --overwrite --format json`,
  `PYENV_VERSION=system uv run python scripts/audit_gis_cog_package_readiness.py --format json --converted-package-root hazard/results/tschamut_public_pilot/gate_v1_cog_poc`,
  `PYENV_VERSION=system uv run python scripts/audit_gis_cog_package_readiness.py --format text --converted-package-root hazard/results/tschamut_public_pilot/gate_v1_cog_poc`,
  `git diff --check`,
  `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`,
  `scripts/git-hooks/pre-commit`.

### TB-045 Minimal Chant Sura Core-Input Staging

- Milestone id: TB-045.
- Roadmap item: Stage Minimal Chant Sura Inputs For Preflight Progress.
- Hypothesis/objective: a tiny synthetic fixture set can move the Chant Sura /
  Fluelapass preflight past the core terrain/source/scenario/root blockers
  without downloading raw public geodata or pretending the public context is
  available.
- Files intended to change: `scripts/prepare_chant_sura_fluelapass_minimal_preflight_inputs.py`,
  `tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_minimal_staging/`,
  `tests/test_second_site_public_geodata_preflight.py`,
  `docs/public_real_site_geodata_preparation.md`,
  `docs/swisstopo_data_strategy.md`,
  `docs/task_backlog.md`,
  `docs/decision_log.md`.
- Implementation summary: added a tiny synthetic Chant Sura staging helper,
  committed the matching fixture set, and updated the portability docs to say
  that the helper only stages the minimal core inputs and ignored roots while
  keeping SWISSIMAGE, swissTLM3D, swissSURFACE3D, swissSURFACE3D Raster, and
  swissBUILDINGS3D explicitly deferred.
- Checks run:
  `PYENV_VERSION=system uv run python scripts/prepare_chant_sura_fluelapass_minimal_preflight_inputs.py --format json`
  passed.
  `PYENV_VERSION=system uv run python scripts/check_second_site_public_geodata_preflight.py --site-config tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml --format json`
  passed with the expected deferred public-context blockers only.
  `PYENV_VERSION=system uv run python -m py_compile scripts/check_second_site_public_geodata_preflight.py tests/test_second_site_public_geodata_preflight.py scripts/generate_pilot_command_plan.py tests/test_pilot_command_plan.py scripts/prepare_chant_sura_fluelapass_minimal_preflight_inputs.py`
  passed.
  `PYENV_VERSION=system uv run python -m unittest tests.test_second_site_public_geodata_preflight`
  passed.
  `PYENV_VERSION=system uv run python -m unittest tests.test_second_site_public_geodata_preflight tests.test_pilot_command_plan`
  failed because `scripts/generate_pilot_command_plan.py` still requires missing
  same-scale Tschamut readiness inputs in this worktree.
  `git diff --check`
  passed.
  `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  passed.
  `scripts/git-hooks/pre-commit`
  passed.
- Reviewer notes: the preflight remains intentionally blocked on deferred
  public context; the helper is only meant to separate that blocker from the
  staged core inputs.
- Decision: ACCEPT_WITH_LIMITATIONS.
- Next proposed milestone: a concrete public-context staging decision for
  Chant Sura / Fluelapass, if and when that path is authorized.

### TB-046 Chant Sura Public-Context Staging Boundary

- Roadmap item: Decide Chant Sura Public-Context Staging Boundary.
- Hypothesis/objective: the Chant Sura / Flüelapass candidate should report
  core terrain/source/scenario/root readiness separately from intentionally
  deferred public-context products, without mistaking deferred context for
  missing core inputs.
- Implementation summary: updated the second-site preflight and portable
  command-plan helper so an empty processed-context root yields
  `deferred_public_context_inputs`, while the acquisition manifest continues to
  spell out the expected SWISSIMAGE, swissTLM3D, swissSURFACE3D,
  swissSURFACE3D Raster, and swissBUILDINGS3D products. The minimal staging
  helper still only stages the synthetic core inputs and ignored roots.
- Checks run:
  `PYENV_VERSION=system uv run python scripts/prepare_chant_sura_fluelapass_minimal_preflight_inputs.py --format json`
  passed.
  `PYENV_VERSION=system uv run python scripts/check_second_site_public_geodata_preflight.py --site-config tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml --format json`
  returned `deferred_public_context_inputs`.
  `PYENV_VERSION=system uv run python scripts/generate_pilot_command_plan.py --site chant_sura_fluelapass --site-config tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml --format json`
  returned a portable plan that marks the second-site steps as template-only.
  `PYENV_VERSION=system uv run python -m py_compile scripts/prepare_chant_sura_fluelapass_minimal_preflight_inputs.py scripts/check_second_site_public_geodata_preflight.py scripts/generate_pilot_command_plan.py tests/test_second_site_public_geodata_preflight.py tests/test_pilot_command_plan.py`
  passed.
  `PYENV_VERSION=system uv run python -m unittest tests.test_second_site_public_geodata_preflight tests.test_pilot_command_plan`
  passed.
  `git diff --check`
  passed.
  `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  passed.
  `scripts/git-hooks/pre-commit`
  passed.
- Decision: ACCEPT_WITH_LIMITATIONS.
- Next proposed milestone: harden the portable source-zone/scenario contract
  for the next concrete second site once a new acquisition decision authorizes
  real public-context downloads.

### Post-TB-046 Engineering Drift Cleanup

- Roadmap item: stabilize task context, generated-artifact hygiene, and command
  plan metadata before starting TB-047.
- Implementation summary: removed hard-coded completed task ids from
  `tests/test_agent_task_context.py`, added the package-level COG conversion
  helper to `scripts/print_agent_task_context.py`, and added unique
  `site::group` command group keys to `scripts/generate_pilot_command_plan.py`
  while preserving existing group ids.
- Boundaries preserved: no scientific classifications, preflight semantics,
  validation artifacts, hazard outputs, or operational/scale-up claims changed.

### TB-048 Spatial Same-Scale Uncertainty Masks

- Roadmap item: emit reusable compact mask summaries for the closure-limiting
  same-scale layers without changing the underlying uncertainty interpretation.
- Implementation summary: extended
  `scripts/summarize_spatial_same_scale_uncertainty.py` with compact
  per-layer mask evidence plus optional ignored JSON summaries, threaded the
  new fields into
  `scripts/summarize_tschamut_conditional_pilot_closure.py`, and kept the
  closure status conservative.
- Checks run:
  `PYENV_VERSION=system uv run python -m py_compile scripts/summarize_spatial_same_scale_uncertainty.py scripts/summarize_tschamut_conditional_pilot_closure.py tests/test_spatial_same_scale_uncertainty.py tests/test_tschamut_conditional_pilot_closure.py`
  passed.
  `PYENV_VERSION=system uv run python -m unittest tests.test_spatial_same_scale_uncertainty tests.test_tschamut_conditional_pilot_closure`
  passed.
  `PYENV_VERSION=system uv run python scripts/check_same_scale_artifact_readiness.py --format json`
  reported same-scale readiness ready except for the known missing raw SWISSTLM3D zip in this worktree.
  `PYENV_VERSION=system uv run python scripts/summarize_spatial_same_scale_uncertainty.py --format json`
  and `--format text` both completed.
  `PYENV_VERSION=system uv run python scripts/summarize_spatial_same_scale_uncertainty.py --format json --mask-output-dir /tmp/tb048_spatial_masks`
  wrote compact ignored mask summary files.
  `PYENV_VERSION=system uv run python scripts/summarize_tschamut_conditional_pilot_closure.py --format json --evidence-json /tmp/tb048_closure_override.json`
  completed with closure status `inconclusive`.
- Boundaries preserved: no new ensembles, physics changes, threshold tuning,
  or operational claims were introduced.

### Post-TB-048 Backlog Handoff Cleanup

- Roadmap item: remove stale completed-task metadata after the TB-047/TB-048
  merge sequence.
- Implementation summary: removed completed TB-047 from `docs/task_backlog.md`
  and updated the active priority order so the task-context helper reports
  TB-049, TB-050, and TB-051 as the active queue.
- Hygiene summary: removed local generated placeholder roots under
  `data/processed/swisstopo/placeholder_second_site_v1`,
  `validation/private/placeholder_second_site_v1`, and
  `hazard/results/placeholder_second_site_v1` before committing.

### TB-049 Canonical Reduced-Output Command Plan

- Milestone id: TB-049.
- Roadmap item: canonicalize the rebuildable reduced-output workflow in the
  portable command plan.
- Hypothesis/objective: the existing `rebuildable_reduced_output` proof can be
  made reproducible through a standard same-scale command-plan group without
  changing physics, thresholds, or validation semantics.
- Files intended to change: `scripts/generate_pilot_command_plan.py`,
  `tests/test_pilot_command_plan.py`,
  `docs/tschamut_public_bounded_validation_output_profile.md`,
  `docs/tschamut_public_conditional_pilot_gate_report.md`,
  `docs/task_backlog.md`,
  `docs/agent_work_log.md`
- Implementation summary: added a `tschamut_same_scale::rebuildable_reduced_output`
  command group with a derivation command and a scratch-only hazard-rebuild
  proof command, and threaded the measured rebuildability status into the
  command-plan JSON. Updated the bounded-output docs to point at the canonical
  command-plan path and removed TB-049 from the active backlog.
- Checks run:
  `PYENV_VERSION=system uv run python -m py_compile scripts/derive_hazard_rebuild_reduced_profile.py scripts/check_hazard_rebuild_output_profile.py scripts/generate_pilot_command_plan.py tests/test_hazard_rebuild_output_profile.py tests/test_hazard_rebuild_reduced_profile.py tests/test_pilot_command_plan.py`
  passed.
  `PYENV_VERSION=system uv run python -m unittest tests.test_hazard_rebuild_output_profile tests.test_hazard_rebuild_reduced_profile tests.test_pilot_command_plan`
  passed.
  `PYENV_VERSION=system uv run python scripts/derive_hazard_rebuild_reduced_profile.py --format json`
  reported `rebuildable_reduced_output`.
  `PYENV_VERSION=system uv run python scripts/check_hazard_rebuild_output_profile.py --format json`
  reported `target_summary_only=summary_only_not_rebuildable` and
  `target_rebuildable_reduced=rebuildable_reduced_output`.
  `PYENV_VERSION=system uv run python scripts/generate_pilot_command_plan.py --site tschamut_same_scale --format json`
  reported the new `rebuildable_reduced_output` command group and canonical
  scratch proof command.
- Reviewer notes: the reduced profile remains a scaling mitigation only; the
  current `summary_only` profile is still not rebuildable.
- Decision: completed.
- Next proposed milestone: TB-050.

### TB-050 Canonical Same-Scale COG Package Conversion

- Milestone id: TB-050.
- Roadmap item: promote the ignored same-scale COG package proof into the
  portable command plan as a first-class workflow step.
- Files intended to change: `scripts/generate_pilot_command_plan.py`,
  `tests/test_pilot_command_plan.py`,
  `docs/public_real_site_geodata_preparation.md`,
  `docs/swisstopo_data_strategy.md`,
  `docs/tschamut_public_conditional_pilot_gate_report.md`,
  `docs/task_backlog.md`,
  `docs/agent_work_log.md`
- Implementation summary: added a dedicated `gis_cog_package_conversion`
  command group with standard GIS audit, ignored-package conversion, and
  converted-package audit commands. Updated the portable plan and docs so the
  package-level COG path is canonical while the committed same-scale roots
  remain truthfully `gis_package_ready_cog_blocked`.
- Checks run: `PYENV_VERSION=system uv run python -m py_compile scripts/convert_same_scale_package_to_cog.py scripts/audit_gis_cog_package_readiness.py scripts/generate_pilot_command_plan.py tests/test_same_scale_cog_package_conversion.py tests/test_gis_cog_package_readiness.py tests/test_pilot_command_plan.py`, `PYENV_VERSION=system uv run python -m unittest tests.test_same_scale_cog_package_conversion tests.test_gis_cog_package_readiness tests.test_pilot_command_plan`, `PYENV_VERSION=system uv run python scripts/convert_same_scale_package_to_cog.py --input-root hazard/results/tschamut_public_pilot/gate_v1 --output-root hazard/results/tschamut_public_pilot/gate_v1_cog_poc --overwrite --format json`, `PYENV_VERSION=system uv run python scripts/audit_gis_cog_package_readiness.py --format json --converted-package-root hazard/results/tschamut_public_pilot/gate_v1_cog_poc`, `PYENV_VERSION=system uv run python scripts/generate_pilot_command_plan.py --site tschamut_same_scale --format json`, `git diff --check`, `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`, and `scripts/git-hooks/pre-commit`.
- Results: the converted ignored package root audits as `cog_package_ready`
  with `cloud_optimized: true`; the standard roots remain
  `gis_package_ready_cog_blocked`; the portable command plan now includes the
  package-level conversion and converted-package audit commands.

### TB-051 Canonical Conditional Diagnostic Interpretation

- Milestone id: TB-051.
- Roadmap item: assemble one canonical measured interpretation artifact for
  the Tschamut same-scale pilot.
- Hypothesis/objective: the closure, spatial uncertainty, rebuildability,
  GIS/COG, runtime, portability, and physical-credibility evidence can be
  composed into a single read-only diagnostic interpretation without changing
  acceptance status or operational boundaries.
- Files intended to change: `scripts/summarize_tschamut_conditional_diagnostic_interpretation.py`,
  `tests/test_tschamut_conditional_diagnostic_interpretation.py`,
  `docs/tschamut_public_conditional_pilot_gate_report.md`,
  `docs/tschamut_public_same_scale_uncertainty_envelope.md`,
  `docs/tschamut_public_bounded_validation_output_profile.md`,
  `docs/public_real_site_geodata_preparation.md`,
  `docs/swisstopo_data_strategy.md`,
  `docs/task_backlog.md`,
  `docs/agent_work_log.md`
- Implementation summary: built a compact synthesis helper that reports the
  current `inconclusive_conditional_diagnostic` interpretation together with
  the measured closure, spatial uncertainty, reduced-output, GIS/COG, runtime,
  portability, and physical-credibility boundaries. The helper keeps
  scale-up, operational, annual-frequency, and risk/exposure/vulnerability
  claims blocked while making the canonical reduced-output and COG proof paths
  command-plan-addressable.
- Checks run:
  `PYENV_VERSION=system uv run python -m py_compile scripts/summarize_tschamut_conditional_diagnostic_interpretation.py tests/test_tschamut_conditional_diagnostic_interpretation.py`
  passed.
  `PYENV_VERSION=system uv run python -m unittest tests.test_tschamut_conditional_diagnostic_interpretation`
  passed.
  `PYENV_VERSION=system uv run python scripts/summarize_tschamut_conditional_diagnostic_interpretation.py --format json`
  passed with output redirected to `/tmp/tb051_diag.json`.
  `PYENV_VERSION=system uv run python scripts/summarize_tschamut_conditional_diagnostic_interpretation.py --format text`
  passed.
- Reviewer notes: the first compose is relatively slow because it reads the
  existing helper evidence, but it remains read-only and reproducible.
- Decision: completed.
- Next proposed milestone: backlog refill needed.

### Post-TB-051 Backlog Refill

- Roadmap item: refill the executable backlog with six concrete follow-up
  tasks after the canonical diagnostic interpretation.
- Implementation summary: updated `docs/task_backlog.md` with six prioritized
  tasks, TB-052 through TB-057, covering support/nodata uncertainty
  decomposition, closure-gap deltas, standard rebuildable reduced output,
  Chant Sura public-context acquisition boundaries, COG-ready export, and
  physical-credibility data requirements.
- Boundaries preserved: no scientific classification, operational claim,
  scale-up authorization, distributed-execution decision, calibration workflow,
  or new simulation was introduced.

### TB-054

- Date: 2026-05-16
- Scope: added a native `rebuildable_reduced_output` validation mode for the
  Tschamut target case, plus a command-plan-visible direct reduced validation
  path.
- Files touched:
  `src/manifest.rs`,
  `src/validation.rs`,
  `src/validation/runner.rs`,
  `tests/config_io_terrain.rs`,
  `scripts/generate_pilot_command_plan.py`,
  `tests/test_pilot_command_plan.py`,
  `tests/fixtures/rebuildable_reduced_output/tschamut_public_target_gate_rebuildable_reduced_case.yaml`,
  `docs/tschamut_public_bounded_validation_output_profile.md`,
  `docs/tschamut_public_conditional_pilot_gate_report.md`,
  `docs/task_backlog.md`,
  `docs/agent_work_log.md`
- Checks run:
  `cargo fmt --check`,
  `cargo test`,
  `PYENV_VERSION=system uv run python -m py_compile scripts/check_hazard_rebuild_output_profile.py scripts/derive_hazard_rebuild_reduced_profile.py scripts/generate_pilot_command_plan.py tests/test_hazard_rebuild_output_profile.py tests/test_hazard_rebuild_reduced_profile.py tests/test_pilot_command_plan.py`
  `PYENV_VERSION=system uv run python -m unittest tests.test_hazard_rebuild_output_profile tests.test_hazard_rebuild_reduced_profile tests.test_pilot_command_plan`
  `PYENV_VERSION=system uv run python scripts/check_hazard_rebuild_output_profile.py --format json`
  `PYENV_VERSION=system uv run python scripts/generate_pilot_command_plan.py --site tschamut_same_scale --format json`
  `PYENV_VERSION=system CARGO_TARGET_DIR=/tmp/rust-rockfall-target cargo run -- validate --case tests/fixtures/rebuildable_reduced_output/tschamut_public_target_gate_rebuildable_reduced_case.yaml`
- Result: direct reduced validation now writes the builder-facing trajectory,
  deposition, impact-event, trajectory-metadata, and diagnostics families
  directly; `summary_only` remains non-rebuildable.

### TB-055

- Date: 2026-05-16
- Scope: made the Chant Sura / Flüelapass public-context acquisition boundary
  explicit and machine-readable, while keeping the synthetic core fixtures
  separated from real public-context readiness.
- Files touched:
  `scripts/check_second_site_public_geodata_preflight.py`,
  `scripts/generate_pilot_command_plan.py`,
  `tests/test_second_site_public_geodata_preflight.py`,
  `tests/test_pilot_command_plan.py`,
  `docs/public_real_site_geodata_preparation.md`,
  `docs/swisstopo_data_strategy.md`,
  `docs/task_backlog.md`,
  `docs/agent_work_log.md`
- Checks run:
  `PYENV_VERSION=system uv run python -m py_compile scripts/check_second_site_public_geodata_preflight.py scripts/generate_pilot_command_plan.py tests/test_second_site_public_geodata_preflight.py tests/test_pilot_command_plan.py`
  `PYENV_VERSION=system uv run python -m unittest tests.test_second_site_public_geodata_preflight tests.test_pilot_command_plan`
  `PYENV_VERSION=system uv run python scripts/prepare_chant_sura_fluelapass_minimal_preflight_inputs.py --format json`
  `PYENV_VERSION=system uv run python scripts/check_second_site_public_geodata_preflight.py --site-config tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml --format json`
  `PYENV_VERSION=system uv run python scripts/generate_pilot_command_plan.py --site chant_sura_fluelapass --site-config tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml --format json`
- Result: `public_context_boundary_status=deferred_public_context_inputs`;
  the report now lists product-level local paths, metadata requirements,
  synthetic-fixture boundaries, and blocked second-site command templates.

- TB-056: Added a first-class COG-ready export path to
  `scripts/build_hazard_layers.py` via `--export-cog` and
  `--cog-package-output-root`, then exposed the canonical same-scale export
  command in `scripts/generate_pilot_command_plan.py` as
  `tschamut_package_cog_export`. The bounded proof ran the gate validation
  builder to `/tmp/tb056_cog_export_staging` and the ignored converted package
  at `hazard/results/tschamut_public_pilot/gate_v1_cog_export`, which audits
  as `cog_package_ready` with `cloud_optimized: true` metadata while the
  standard roots remain `gis_package_ready_cog_blocked`.
- Files touched:
  `scripts/build_hazard_layers.py`,
  `scripts/generate_pilot_command_plan.py`,
  `tests/test_hazard_layers.py`,
  `tests/test_pilot_command_plan.py`,
  `docs/public_real_site_geodata_preparation.md`,
  `docs/swisstopo_data_strategy.md`,
  `docs/tschamut_public_conditional_pilot_gate_report.md`,
  `docs/task_backlog.md`,
  `docs/agent_work_log.md`
- Checks run:
  `PYENV_VERSION=system uv run python -m py_compile scripts/build_hazard_layers.py scripts/generate_pilot_command_plan.py tests/test_hazard_layers.py tests/test_pilot_command_plan.py`,
  `PYENV_VERSION=system uv run python -m unittest tests.test_hazard_layers.HazardLayerTests.test_cog_export_runs_a_post_export_package_step tests.test_pilot_command_plan.PilotCommandPlanTest.test_tschamut_plan_json_has_stable_groups`,
  `PYENV_VERSION=system uv run python scripts/audit_gis_cog_package_readiness.py --format json`,
  `PYENV_VERSION=system uv run python scripts/generate_pilot_command_plan.py --site tschamut_same_scale --format json`,
  `PYENV_VERSION=system uv run python scripts/build_hazard_layers.py --case validation/private/tschamut_public_pilot/gate_v1/tschamut_public_conditional_gate_case.yaml --output-dir /tmp/tb056_cog_export_staging --grid-xmin 2696376.0 --grid-ymin 1167384.0 --grid-ncols 300 --grid-nrows 304 --grid-cell-size 2.0 --map-product-id tschamut_public_conditional_gate_v1 --probability-mode sampling_weighted_conditional --normalization-scope conditioned_on_filter --source-zone-metadata-path data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_source_zone_metadata_v1.yaml --scenario-table-path data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_scenario_table_v1.csv --map-package-manifest-json /tmp/tb056_cog_export_staging/tschamut_public_conditional_gate_v1_map_package_manifest.json --export-geotiff --pilot-gis-package --pilot-gis-package-manifest-json /tmp/tb056_cog_export_staging/tschamut_public_conditional_gate_v1_pilot_gis_package_manifest.json --pilot-gis-qa-status not-run --pilot-gis-qa-note 'Manual GIS/QGIS inspection has not been run for this generated package.' --reducer-workers 2 --no-plots --conditional-curve-export summary-only --grid-csv-export none --diagnostics validation/private/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_metrics.json --trajectory validation/private/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_trajectory.csv --ensemble-trajectories-dir validation/private/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_trajectories --deposition validation/private/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_deposition.csv --ensemble-impact-events-dir validation/private/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_impacts --kinetic-energy-exceedance-j 1000.0 --kinetic-energy-exceedance-j 10000.0 --jump-height-exceedance-m 1.0 --jump-height-exceedance-m 2.0 --export-cog --cog-package-output-root hazard/results/tschamut_public_pilot/gate_v1_cog_export`,
  `PYENV_VERSION=system uv run python scripts/audit_gis_cog_package_readiness.py --format json --converted-package-root hazard/results/tschamut_public_pilot/gate_v1_cog_export`
- Result: the ignored `hazard/results/tschamut_public_pilot/gate_v1_cog_export`
  package audits as `cog_package_ready` with tiled, overviewed, compressed
  GeoTIFFs and `cloud_optimized: true` metadata; the standard same-scale roots
  remain truthfully `gis_package_ready_cog_blocked`.

### Post-TB-057 Backlog Refill

- Date: 2026-05-16
- Scope: refilled the active backlog after TB-057 using the post-TB-056 and
  post-TB-057 review findings plus current measured helper status.
- Measured state used:
  `readiness_status=ready`,
  `closure_status=inconclusive`,
  `spatial_uncertainty_status=measured_existing_artifacts`,
  `spatial_interpretation=nodata_support_dominated`,
  `closure_gap_status=measured_gaps_remain`,
  `hazard_rebuild_output_profile_status=measured`,
  `gis_cog_readiness_status=gis_package_ready_cog_blocked`,
  converted package status `cog_package_ready`,
  second-site `readiness_status=deferred_public_context_inputs`, and
  `physical_credibility_requirements_status=mapped_current_gaps`.
- Result: added TB-058 through TB-066 in priority order, with immediate focus
  on command-plan/COG drift, spatial uncertainty interpretation, bounded
  next-ensemble feasibility, second-site dry-run portability, AOI acquisition
  planning, COG export parity, physical-credibility evidence priorities, and
  canonical diagnostic interpretation alignment.

## Archived Active Work Log Snapshot - 2026-05-18 Cleanup Pass

# Agent Work Log

Append-only current work log for TB tasks.

This file is intentionally short and chronological. The full pre-refactor
history, non-TB planning notes, M-series milestones, backlog refills, and
review triage entries live in `docs/archive/agent_work_log_archive.md`.

## Worker Instructions

- Always append new entries at the bottom of this file. Do not insert work
  logs near related older entries.
- Use one `### TB-XXX: Short Title` heading per completed task.
- Keep the TB entries in ascending order. If the current task is `TB-058`,
  its entry belongs after `TB-057`.
- Do not add backlog-refill notes, review triage, planning notes, or
  non-task narrative here. Put durable planning in `docs/task_backlog.md` or
  `docs/decision_log.md`; archive older non-TB history only in
  `docs/archive/agent_work_log_archive.md`.
- Prefer concise entries. Link to generated helpers, docs, and commits rather
  than pasting long command transcripts.
- Do not leave `Commit: pending` in a committed entry. Use a two-commit
  sequence when recording a completed task: first commit the implementation
  with the backlog removal and no new work-log entry, then append the work-log
  entry with that implementation commit hash and make a small follow-up
  `Record TB-XXX work log` commit. Do not amend repeatedly to chase a
  self-referential hash.

## Entry Template

```markdown
### TB-XXX: Short Title

- Date: YYYY-MM-DD
- Commit: `<implementation-commit-hash>`; never leave `pending` in a pushed commit.
- Objective: one sentence describing the task.
- Files changed: concise comma-separated list or grouped paths.
- Implementation summary: 2-4 bullets focused on what changed.
- Checks run: focused tests plus repo hygiene checks.
- Result/status: completed, blocked, or follow-up needed.
- Boundaries: note no physics/tuning/operational/scale-up changes when relevant.
- Next task: `TB-YYY` or backlog refill needed.
```

## Completed TB Entries

### TB-001: Roadmap item: post TB-001 through TB-008 backlog reassessment.

- Date: see archive if not listed in the original entry.
- Commit: see git history / archive.
- Objective: Replaced the stale active TB-007 entry with a new
- Files changed: see archive for the full historical record.
- Implementation summary: normalized from the pre-refactor log; full details
  are preserved in `docs/archive/agent_work_log_archive.md`.
- Checks run: see archive for original command lists.
- Result/status: completed or superseded by later TB work.
- Boundaries: historical scientific/operational boundaries preserved as
  recorded in the archive.
- Next task: see `docs/task_backlog.md` for the active queue.

### TB-002: Historical Entry

- Date: see archive if not listed in the original entry.
- Commit: see git history / archive.
- Objective: Added an importable and CLI-runnable hazard-map
- Files changed: see archive for the full historical record.
- Implementation summary: normalized from the pre-refactor log; full details
  are preserved in `docs/archive/agent_work_log_archive.md`.
- Checks run: see archive for original command lists.
- Result/status: completed or superseded by later TB work.
- Boundaries: historical scientific/operational boundaries preserved as
  recorded in the archive.
- Next task: see `docs/task_backlog.md` for the active queue.

### TB-003: Next proposed milestone: TB-003.

- Date: see archive if not listed in the original entry.
- Commit: see git history / archive.
- Objective: Added a summary generator that imports the existing
- Files changed: see archive for the full historical record.
- Implementation summary: normalized from the pre-refactor log; full details
  are preserved in `docs/archive/agent_work_log_archive.md`.
- Checks run: see archive for original command lists.
- Result/status: completed or superseded by later TB work.
- Boundaries: historical scientific/operational boundaries preserved as
  recorded in the archive.
- Next task: see `docs/task_backlog.md` for the active queue.

### TB-004: Next proposed milestone: TB-004.

- Date: see archive if not listed in the original entry.
- Commit: see git history / archive.
- Objective: Acquire Or Verify Public Context-Layer Evidence For Tschamut.
- Files changed: see archive for the full historical record.
- Implementation summary: normalized from the pre-refactor log; full details
  are preserved in `docs/archive/agent_work_log_archive.md`.
- Checks run: see archive for original command lists.
- Result/status: completed or superseded by later TB work.
- Boundaries: historical scientific/operational boundaries preserved as
  recorded in the archive.
- Next task: see `docs/task_backlog.md` for the active queue.

### TB-005: Next proposed milestone: TB-005.

- Date: see archive if not listed in the original entry.
- Commit: see git history / archive.
- Objective: Reordered the active backlog around cell-wise
- Files changed: see archive for the full historical record.
- Implementation summary: normalized from the pre-refactor log; full details
  are preserved in `docs/archive/agent_work_log_archive.md`.
- Checks run: see archive for original command lists.
- Result/status: completed or superseded by later TB work.
- Boundaries: historical scientific/operational boundaries preserved as
  recorded in the archive.
- Next task: see `docs/task_backlog.md` for the active queue.

### TB-006: Next proposed milestone: TB-006.

- Date: see archive if not listed in the original entry.
- Commit: see git history / archive.
- Objective: Fixed the bounded-output summary so `no_go`
- Files changed: see archive for the full historical record.
- Implementation summary: normalized from the pre-refactor log; full details
  are preserved in `docs/archive/agent_work_log_archive.md`.
- Checks run: see archive for original command lists.
- Result/status: completed or superseded by later TB work.
- Boundaries: historical scientific/operational boundaries preserved as
  recorded in the archive.
- Next task: see `docs/task_backlog.md` for the active queue.

### TB-007: Implementation summary: Replaced the stale active TB-007 entry with a new

- Date: see archive if not listed in the original entry.
- Commit: see git history / archive.
- Objective: Replaced the stale active TB-007 entry with a new
- Files changed: see archive for the full historical record.
- Implementation summary: normalized from the pre-refactor log; full details
  are preserved in `docs/archive/agent_work_log_archive.md`.
- Checks run: see archive for original command lists.
- Result/status: completed or superseded by later TB work.
- Boundaries: historical scientific/operational boundaries preserved as
  recorded in the archive.
- Next task: see `docs/task_backlog.md` for the active queue.

### TB-008: Historical Entry

- Date: see archive if not listed in the original entry.
- Commit: see git history / archive.
- Objective: Added a record-driven sufficiency summary that
- Files changed: see archive for the full historical record.
- Implementation summary: normalized from the pre-refactor log; full details
  are preserved in `docs/archive/agent_work_log_archive.md`.
- Checks run: see archive for original command lists.
- Result/status: completed or superseded by later TB work.
- Boundaries: historical scientific/operational boundaries preserved as
  recorded in the archive.
- Next task: see `docs/task_backlog.md` for the active queue.

### TB-009: Historical Entry

- Date: see archive if not listed in the original entry.
- Commit: see git history / archive.
- Objective: Added a manifest-side `cellwise_layers` projection for ASCII hazard-layer outputs, taught the convergence diagnostic to infer cell-wise layers only when the underlying grid files exist, and kept summary-only manifests...
- Files changed: see archive for the full historical record.
- Implementation summary: normalized from the pre-refactor log; full details
  are preserved in `docs/archive/agent_work_log_archive.md`.
- Checks run: see archive for original command lists.
- Result/status: completed or superseded by later TB work.
- Boundaries: historical scientific/operational boundaries preserved as
  recorded in the archive.
- Next task: see `docs/task_backlog.md` for the active queue.

### TB-010: Next proposed milestone: TB-010.

- Date: see archive if not listed in the original entry.
- Commit: see git history / archive.
- Objective: Extended the inspector to expose `selected_extent_or_corridor`, `spatial_relevance_status`, and `spatial_relevance_indicators` while preserving the blocked checkout path. The default checkout still reports `blocked_pe...
- Files changed: see archive for the full historical record.
- Implementation summary: normalized from the pre-refactor log; full details
  are preserved in `docs/archive/agent_work_log_archive.md`.
- Checks run: see archive for original command lists.
- Result/status: completed or superseded by later TB work.
- Boundaries: historical scientific/operational boundaries preserved as
  recorded in the archive.
- Next task: see `docs/task_backlog.md` for the active queue.

### TB-011: Historical Entry

- Date: see archive if not listed in the original entry.
- Commit: see git history / archive.
- Objective: Extended the inspector to expose `selected_extent_or_corridor`, `spatial_relevance_status`, and `spatial_relevance_indicators` while preserving the blocked checkout path. The default checkout still reports `blocked_pe...
- Files changed: see archive for the full historical record.
- Implementation summary: normalized from the pre-refactor log; full details
  are preserved in `docs/archive/agent_work_log_archive.md`.
- Checks run: see archive for original command lists.
- Result/status: completed or superseded by later TB work.
- Boundaries: historical scientific/operational boundaries preserved as
  recorded in the archive.
- Next task: see `docs/task_backlog.md` for the active queue.

### TB-012: /TB-013 Local Unblock

- Date: see archive if not listed in the original entry.
- Commit: see git history / archive.
- Objective: Regenerated the public Tschamut/swissALTI3D
- Files changed: see archive for the full historical record.
- Implementation summary: normalized from the pre-refactor log; full details
  are preserved in `docs/archive/agent_work_log_archive.md`.
- Checks run: see archive for original command lists.
- Result/status: completed or superseded by later TB work.
- Boundaries: historical scientific/operational boundaries preserved as
  recorded in the archive.
- Next task: see `docs/task_backlog.md` for the active queue.

### TB-013: TB-012/TB-013 Local Unblock

- Date: see archive if not listed in the original entry.
- Commit: see git history / archive.
- Objective: Regenerated the public Tschamut/swissALTI3D
- Files changed: see archive for the full historical record.
- Implementation summary: normalized from the pre-refactor log; full details
  are preserved in `docs/archive/agent_work_log_archive.md`.
- Checks run: see archive for original command lists.
- Result/status: completed or superseded by later TB work.
- Boundaries: historical scientific/operational boundaries preserved as
  recorded in the archive.
- Next task: see `docs/task_backlog.md` for the active queue.


### TB-014: the selected gate so TB-014 can be retried without ambiguity once inputs

- Date: see archive if not listed in the original entry.
- Commit: see git history / archive.
- Objective: Refresh Same-Scale Selected Tschamut Pilot Artifacts; Stage
- Files changed: see archive for the full historical record.
- Implementation summary: normalized from the pre-refactor log; full details
  are preserved in `docs/archive/agent_work_log_archive.md`.
- Checks run: see archive for original command lists.
- Result/status: completed or superseded by later TB work.
- Boundaries: historical scientific/operational boundaries preserved as
  recorded in the archive.
- Next task: see `docs/task_backlog.md` for the active queue.

### TB-015: Reviewer notes: No context extraction or corridor review was repeated; TB-015 already measured swissTLM3D corridor re...

- Date: see archive if not listed in the original entry.
- Commit: see git history / archive.
- Objective: Refresh Same-Scale Selected Tschamut Pilot Artifacts; Stage
- Files changed: see archive for the full historical record.
- Implementation summary: normalized from the pre-refactor log; full details
  are preserved in `docs/archive/agent_work_log_archive.md`.
- Checks run: see archive for original command lists.
- Result/status: completed or superseded by later TB work.
- Boundaries: historical scientific/operational boundaries preserved as
  recorded in the archive.
- Next task: see `docs/task_backlog.md` for the active queue.

### TB-016: task; moved the uncertainty-envelope synthesis into TB-016; and updated the

- Date: see archive if not listed in the original entry.
- Commit: see git history / archive.
- Objective: post TB-014 same-scale convergence measurement.
- Files changed: see archive for the full historical record.
- Implementation summary: normalized from the pre-refactor log; full details
  are preserved in `docs/archive/agent_work_log_archive.md`.
- Checks run: see archive for original command lists.
- Result/status: completed or superseded by later TB work.
- Boundaries: historical scientific/operational boundaries preserved as
  recorded in the archive.
- Next task: see `docs/task_backlog.md` for the active queue.

### TB-017: Target Manifest Restore Block

- Date: see archive if not listed in the original entry.
- Commit: see git history / archive.
- Objective: Audited the local checkout and confirmed that the
- Files changed: see archive for the full historical record.
- Implementation summary: normalized from the pre-refactor log; full details
  are preserved in `docs/archive/agent_work_log_archive.md`.
- Checks run: see archive for original command lists.
- Result/status: completed or superseded by later TB work.
- Boundaries: historical scientific/operational boundaries preserved as
  recorded in the archive.
- Next task: see `docs/task_backlog.md` for the active queue.

### TB-018: Target Same-Scale Artifact Restore

- Date: see archive if not listed in the original entry.
- Commit: see git history / archive.
- Objective: Reconstructed the ignored target private case from
- Files changed: see archive for the full historical record.
- Implementation summary: normalized from the pre-refactor log; full details
  are preserved in `docs/archive/agent_work_log_archive.md`.
- Checks run: see archive for original command lists.
- Result/status: completed or superseded by later TB work.
- Boundaries: historical scientific/operational boundaries preserved as
  recorded in the archive.
- Next task: see `docs/task_backlog.md` for the active queue.

### TB-019: replace TB-019’s interpretation step.

- Date: see archive if not listed in the original entry.
- Commit: see git history / archive.
- Objective: Audited the local checkout and confirmed that the
- Files changed: see archive for the full historical record.
- Implementation summary: normalized from the pre-refactor log; full details
  are preserved in `docs/archive/agent_work_log_archive.md`.
- Checks run: see archive for original command lists.
- Result/status: completed or superseded by later TB work.
- Boundaries: historical scientific/operational boundaries preserved as
  recorded in the archive.
- Next task: see `docs/task_backlog.md` for the active queue.

### TB-020: Next proposed milestone: TB-020.

- Date: see archive if not listed in the original entry.
- Commit: see git history / archive.
- Objective: Staged a target-side `summary_only` validation case under `validation/private/tschamut_public_pilot/target_gate_v1_summary_only/`, ran the validation with `CARGO_TARGET_DIR=/tmp/rust-rockfall-target`, and measured the...
- Files changed: see archive for the full historical record.
- Implementation summary: normalized from the pre-refactor log; full details
  are preserved in `docs/archive/agent_work_log_archive.md`.
- Checks run: see archive for original command lists.
- Result/status: completed or superseded by later TB work.
- Boundaries: historical scientific/operational boundaries preserved as
  recorded in the archive.
- Next task: see `docs/task_backlog.md` for the active queue.

### TB-021: Milestone id: backlog refill after TB-021.

- Date: see archive if not listed in the original entry.
- Commit: see git history / archive.
- Objective: Updated the backlog capability-gap analysis to
- Files changed: see archive for the full historical record.
- Implementation summary: normalized from the pre-refactor log; full details
  are preserved in `docs/archive/agent_work_log_archive.md`.
- Checks run: see archive for original command lists.
- Result/status: completed or superseded by later TB work.
- Boundaries: historical scientific/operational boundaries preserved as
  recorded in the archive.
- Next task: see `docs/task_backlog.md` for the active queue.

### TB-022: Milestone id: worker efficiency consolidation after TB-022.

- Date: see archive if not listed in the original entry.
- Commit: see git history / archive.
- Objective: Added a `Tschamut Worker Fast Path` to `AGENTS.md`
- Files changed: see archive for the full historical record.
- Implementation summary: normalized from the pre-refactor log; full details
  are preserved in `docs/archive/agent_work_log_archive.md`.
- Checks run: see archive for original command lists.
- Result/status: completed or superseded by later TB work.
- Boundaries: historical scientific/operational boundaries preserved as
  recorded in the archive.
- Next task: see `docs/task_backlog.md` for the active queue.

### TB-023: Next proposed milestone: TB-023.

- Date: see archive if not listed in the original entry.
- Commit: see git history / archive.
- Objective: Updated the backlog capability-gap analysis to
- Files changed: see archive for the full historical record.
- Implementation summary: normalized from the pre-refactor log; full details
  are preserved in `docs/archive/agent_work_log_archive.md`.
- Checks run: see archive for original command lists.
- Result/status: completed or superseded by later TB work.
- Boundaries: historical scientific/operational boundaries preserved as
  recorded in the archive.
- Next task: see `docs/task_backlog.md` for the active queue.

### TB-024: Historical Entry

- Date: see archive if not listed in the original entry.
- Commit: see git history / archive.
- Objective: Reused the existing convergence diagnostic to
- Files changed: see archive for the full historical record.
- Implementation summary: normalized from the pre-refactor log; full details
  are preserved in `docs/archive/agent_work_log_archive.md`.
- Checks run: see archive for original command lists.
- Result/status: completed or superseded by later TB work.
- Boundaries: historical scientific/operational boundaries preserved as
  recorded in the archive.
- Next task: see `docs/task_backlog.md` for the active queue.

### TB-025: Historical Entry

- Date: see archive if not listed in the original entry.
- Commit: see git history / archive.
- Objective: Ran the readiness preflight, then attempted a
- Files changed: see archive for the full historical record.
- Implementation summary: normalized from the pre-refactor log; full details
  are preserved in `docs/archive/agent_work_log_archive.md`.
- Checks run: see archive for original command lists.
- Result/status: completed or superseded by later TB work.
- Boundaries: historical scientific/operational boundaries preserved as
  recorded in the archive.
- Next task: see `docs/task_backlog.md` for the active queue.

### TB-026: Next proposed milestone: TB-026.

- Date: see archive if not listed in the original entry.
- Commit: see git history / archive.
- Objective: Reused the existing convergence diagnostic to
- Files changed: see archive for the full historical record.
- Implementation summary: normalized from the pre-refactor log; full details
  are preserved in `docs/archive/agent_work_log_archive.md`.
- Checks run: see archive for original command lists.
- Result/status: completed or superseded by later TB work.
- Boundaries: historical scientific/operational boundaries preserved as
  recorded in the archive.
- Next task: see `docs/task_backlog.md` for the active queue.

### TB-027: Milestone id: backlog refill after TB-027.

- Date: see archive if not listed in the original entry.
- Commit: see git history / archive.
- Objective: Refilled the active backlog with TB-028 through
- Files changed: see archive for the full historical record.
- Implementation summary: normalized from the pre-refactor log; full details
  are preserved in `docs/archive/agent_work_log_archive.md`.
- Checks run: see archive for original command lists.
- Result/status: completed or superseded by later TB work.
- Boundaries: historical scientific/operational boundaries preserved as
  recorded in the archive.
- Next task: see `docs/task_backlog.md` for the active queue.

### TB-028: Implementation summary: Refilled the active backlog with TB-028 through

- Date: see archive if not listed in the original entry.
- Commit: see git history / archive.
- Objective: Refilled the active backlog with TB-028 through
- Files changed: see archive for the full historical record.
- Implementation summary: normalized from the pre-refactor log; full details
  are preserved in `docs/archive/agent_work_log_archive.md`.
- Checks run: see archive for original command lists.
- Result/status: completed or superseded by later TB work.
- Boundaries: historical scientific/operational boundaries preserved as
  recorded in the archive.
- Next task: see `docs/task_backlog.md` for the active queue.

### TB-029: Roadmap item: TB-029 added a concrete Chant Sura / Flüelapass second-site

- Date: see archive if not listed in the original entry.
- Commit: see git history / archive.
- Objective: TB-029 added a concrete Chant Sura / Flüelapass second-site
- Files changed: see archive for the full historical record.
- Implementation summary: normalized from the pre-refactor log; full details
  are preserved in `docs/archive/agent_work_log_archive.md`.
- Checks run: see archive for original command lists.
- Result/status: completed or superseded by later TB work.
- Boundaries: historical scientific/operational boundaries preserved as
  recorded in the archive.
- Next task: see `docs/task_backlog.md` for the active queue.

### TB-030: Implementation summary: Added TB-030 as the multi-site source-zone and

- Date: see archive if not listed in the original entry.
- Commit: see git history / archive.
- Objective: Added TB-030 as the multi-site source-zone and
- Files changed: see archive for the full historical record.
- Implementation summary: normalized from the pre-refactor log; full details
  are preserved in `docs/archive/agent_work_log_archive.md`.
- Checks run: see archive for original command lists.
- Result/status: completed or superseded by later TB work.
- Boundaries: historical scientific/operational boundaries preserved as
  recorded in the archive.
- Next task: see `docs/task_backlog.md` for the active queue.

### TB-031: scenario contract audit, rewrote the sampling task as TB-031 multi-seed

- Date: see archive if not listed in the original entry.
- Commit: see git history / archive.
- Objective: Historical TB entry normalized during log cleanup; see archive for full original context.
- Files changed: see archive for the full historical record.
- Implementation summary: normalized from the pre-refactor log; full details
  are preserved in `docs/archive/agent_work_log_archive.md`.
- Checks run: see archive for original command lists.
- Result/status: completed or superseded by later TB work.
- Boundaries: historical scientific/operational boundaries preserved as
  recorded in the archive.
- Next task: see `docs/task_backlog.md` for the active queue.

### TB-032: and reducer/runtime tasks to TB-032 through TB-034. Updated the durable

- Date: see archive if not listed in the original entry.
- Commit: see git history / archive.
- Objective: Historical TB entry normalized during log cleanup; see archive for full original context.
- Files changed: see archive for the full historical record.
- Implementation summary: normalized from the pre-refactor log; full details
  are preserved in `docs/archive/agent_work_log_archive.md`.
- Checks run: see archive for original command lists.
- Result/status: completed or superseded by later TB work.
- Boundaries: historical scientific/operational boundaries preserved as
  recorded in the archive.
- Next task: see `docs/task_backlog.md` for the active queue.

### TB-033: . The new sequence prioritizes a concrete second-site manifest,

- Date: see archive if not listed in the original entry.
- Commit: see git history / archive.
- Objective: Historical TB entry normalized during log cleanup; see archive for full original context.
- Files changed: see archive for the full historical record.
- Implementation summary: normalized from the pre-refactor log; full details
  are preserved in `docs/archive/agent_work_log_archive.md`.
- Checks run: see archive for original command lists.
- Result/status: completed or superseded by later TB work.
- Boundaries: historical scientific/operational boundaries preserved as
  recorded in the archive.
- Next task: see `docs/task_backlog.md` for the active queue.

### TB-034: and reducer/runtime tasks to TB-032 through TB-034. Updated the durable

- Date: see archive if not listed in the original entry.
- Commit: see git history / archive.
- Objective: Historical TB entry normalized during log cleanup; see archive for full original context.
- Files changed: see archive for the full historical record.
- Implementation summary: normalized from the pre-refactor log; full details
  are preserved in `docs/archive/agent_work_log_archive.md`.
- Checks run: see archive for original command lists.
- Result/status: completed or superseded by later TB work.
- Boundaries: historical scientific/operational boundaries preserved as
  recorded in the archive.
- Next task: see `docs/task_backlog.md` for the active queue.

### TB-035: Conditional Pilot Closure Criteria

- Date: see archive if not listed in the original entry.
- Commit: see git history / archive.
- Objective: Added a read-only closure helper that composes the
- Files changed: see archive for the full historical record.
- Implementation summary: normalized from the pre-refactor log; full details
  are preserved in `docs/archive/agent_work_log_archive.md`.
- Checks run: see archive for original command lists.
- Result/status: completed or superseded by later TB work.
- Boundaries: historical scientific/operational boundaries preserved as
  recorded in the archive.
- Next task: see `docs/task_backlog.md` for the active queue.

### TB-036: Next proposed milestone: TB-036.

- Date: see archive if not listed in the original entry.
- Commit: see git history / archive.
- Objective: Historical TB entry normalized during log cleanup; see archive for full original context.
- Files changed: see archive for the full historical record.
- Implementation summary: normalized from the pre-refactor log; full details
  are preserved in `docs/archive/agent_work_log_archive.md`.
- Checks run: see archive for original command lists.
- Result/status: completed or superseded by later TB work.
- Boundaries: historical scientific/operational boundaries preserved as
  recorded in the archive.
- Next task: see `docs/task_backlog.md` for the active queue.

### TB-037: spatial same-scale uncertainty interpretation. Files changed:

- Date: see archive if not listed in the original entry.
- Commit: see git history / archive.
- Objective: Historical TB entry normalized during log cleanup; see archive for full original context.
- Files changed: see archive for the full historical record.
- Implementation summary: normalized from the pre-refactor log; full details
  are preserved in `docs/archive/agent_work_log_archive.md`.
- Checks run: see archive for original command lists.
- Result/status: completed or superseded by later TB work.
- Boundaries: historical scientific/operational boundaries preserved as
  recorded in the archive.
- Next task: see `docs/task_backlog.md` for the active queue.

### TB-038: Bounded COG Conversion Proof Of Concept

- Date: see archive if not listed in the original entry.
- Commit: see git history / archive.
- Objective: Added a bounded COG conversion prototype that uses
- Files changed: see archive for the full historical record.
- Implementation summary: normalized from the pre-refactor log; full details
  are preserved in `docs/archive/agent_work_log_archive.md`.
- Checks run: see archive for original command lists.
- Result/status: completed or superseded by later TB work.
- Boundaries: historical scientific/operational boundaries preserved as
  recorded in the archive.
- Next task: see `docs/task_backlog.md` for the active queue.

### TB-039: Chant Sura public-geodata acquisition manifest. Files changed:

- Date: see archive if not listed in the original entry.
- Commit: see git history / archive.
- Objective: Historical TB entry normalized during log cleanup; see archive for full original context.
- Files changed: see archive for the full historical record.
- Implementation summary: normalized from the pre-refactor log; full details
  are preserved in `docs/archive/agent_work_log_archive.md`.
- Checks run: see archive for original command lists.
- Result/status: completed or superseded by later TB work.
- Boundaries: historical scientific/operational boundaries preserved as
  recorded in the archive.
- Next task: see `docs/task_backlog.md` for the active queue.

### TB-040: validation and calibration evidence-gap assessment. Files changed:

- Date: see archive if not listed in the original entry.
- Commit: see git history / archive.
- Objective: Historical TB entry normalized during log cleanup; see archive for full original context.
- Files changed: see archive for the full historical record.
- Implementation summary: normalized from the pre-refactor log; full details
  are preserved in `docs/archive/agent_work_log_archive.md`.
- Checks run: see archive for original command lists.
- Result/status: completed or superseded by later TB work.
- Boundaries: historical scientific/operational boundaries preserved as
  recorded in the archive.
- Next task: see `docs/task_backlog.md` for the active queue.

### TB-041: KEEP already active: TB-041 Chant Sura holdout evidence manifest.

- Date: see archive if not listed in the original entry.
- Commit: see git history / archive.
- Objective: Historical TB entry normalized during log cleanup; see archive for full original context.
- Files changed: see archive for the full historical record.
- Implementation summary: normalized from the pre-refactor log; full details
  are preserved in `docs/archive/agent_work_log_archive.md`.
- Checks run: see archive for original command lists.
- Result/status: completed or superseded by later TB work.
- Boundaries: historical scientific/operational boundaries preserved as
  recorded in the archive.
- Next task: see `docs/task_backlog.md` for the active queue.

### TB-042: hazard-rebuild-compatible reduced output profile.

- Date: see archive if not listed in the original entry.
- Commit: see git history / archive.
- Objective: `rebuildable_reduced_output` is now a concrete reduced profile on the
- Files changed: see archive for the full historical record.
- Implementation summary: normalized from the pre-refactor log; full details
  are preserved in `docs/archive/agent_work_log_archive.md`.
- Checks run: see archive for original command lists.
- Result/status: completed or superseded by later TB work.
- Boundaries: historical scientific/operational boundaries preserved as
  recorded in the archive.
- Next task: see `docs/task_backlog.md` for the active queue.

### TB-043: spatial uncertainty integration into conditional closure logic.

- Date: see archive if not listed in the original entry.
- Commit: see git history / archive.
- Objective: the closure helper now consumes the spatial
- Files changed: see archive for the full historical record.
- Implementation summary: normalized from the pre-refactor log; full details
  are preserved in `docs/archive/agent_work_log_archive.md`.
- Checks run: see archive for original command lists.
- Result/status: completed or superseded by later TB work.
- Boundaries: historical scientific/operational boundaries preserved as
  recorded in the archive.
- Next task: see `docs/task_backlog.md` for the active queue.

### TB-044: ignored same-scale GIS package as COG-ready.

- Date: see archive if not listed in the original entry.
- Commit: see git history / archive.
- Objective: the ignored `hazard/results/tschamut_public_pilot/gate_v1_cog_poc`
- Files changed: see archive for the full historical record.
- Implementation summary: normalized from the pre-refactor log; full details
  are preserved in `docs/archive/agent_work_log_archive.md`.
- Checks run: see archive for original command lists.
- Result/status: completed or superseded by later TB work.
- Boundaries: historical scientific/operational boundaries preserved as
  recorded in the archive.
- Next task: see `docs/task_backlog.md` for the active queue.

### TB-045: Decision summary: the current active queue TB-041 through TB-045 remains the

- Date: see archive if not listed in the original entry.
- Commit: see git history / archive.
- Objective: Historical TB entry normalized during log cleanup; see archive for full original context.
- Files changed: see archive for the full historical record.
- Implementation summary: normalized from the pre-refactor log; full details
  are preserved in `docs/archive/agent_work_log_archive.md`.
- Checks run: see archive for original command lists.
- Result/status: completed or superseded by later TB work.
- Boundaries: historical scientific/operational boundaries preserved as
  recorded in the archive.
- Next task: see `docs/task_backlog.md` for the active queue.

### TB-046: Chant Sura Public-Context Staging Boundary

- Date: see archive if not listed in the original entry.
- Commit: see git history / archive.
- Objective: updated the second-site preflight and portable
- Files changed: see archive for the full historical record.
- Implementation summary: normalized from the pre-refactor log; full details
  are preserved in `docs/archive/agent_work_log_archive.md`.
- Checks run: see archive for original command lists.
- Result/status: completed or superseded by later TB work.
- Boundaries: historical scientific/operational boundaries preserved as
  recorded in the archive.
- Next task: see `docs/task_backlog.md` for the active queue.

### TB-047: Portable Source-Scenario Semantics Audit

- Date: see archive if not listed in the original entry.
- Commit: see git history / archive.
- Objective: Added a machine-readable semantic portability
- Files changed: see archive for the full historical record.
- Implementation summary: normalized from the pre-refactor log; full details
  are preserved in `docs/archive/agent_work_log_archive.md`.
- Checks run: see archive for original command lists.
- Result/status: completed or superseded by later TB work.
- Boundaries: historical scientific/operational boundaries preserved as
  recorded in the archive.
- Next task: see `docs/task_backlog.md` for the active queue.

### TB-048: Next proposed milestone: TB-048

- Date: see archive if not listed in the original entry.
- Commit: see git history / archive.
- Objective: Added TB-030 as the multi-site source-zone and
- Files changed: see archive for the full historical record.
- Implementation summary: normalized from the pre-refactor log; full details
  are preserved in `docs/archive/agent_work_log_archive.md`.
- Checks run: see archive for original command lists.
- Result/status: completed or superseded by later TB work.
- Boundaries: historical scientific/operational boundaries preserved as
  recorded in the archive.
- Next task: see `docs/task_backlog.md` for the active queue.

### TB-049: , TB-050, and TB-051 as the active queue.

- Date: see archive if not listed in the original entry.
- Commit: see git history / archive.
- Objective: canonicalize the rebuildable reduced-output workflow in the
- Files changed: see archive for the full historical record.
- Implementation summary: normalized from the pre-refactor log; full details
  are preserved in `docs/archive/agent_work_log_archive.md`.
- Checks run: see archive for original command lists.
- Result/status: completed or superseded by later TB work.
- Boundaries: historical scientific/operational boundaries preserved as
  recorded in the archive.
- Next task: see `docs/task_backlog.md` for the active queue.

### TB-050: TB-049, TB-050, and TB-051 as the active queue.

- Date: see archive if not listed in the original entry.
- Commit: see git history / archive.
- Objective: canonicalize the rebuildable reduced-output workflow in the
- Files changed: see archive for the full historical record.
- Implementation summary: normalized from the pre-refactor log; full details
  are preserved in `docs/archive/agent_work_log_archive.md`.
- Checks run: see archive for original command lists.
- Result/status: completed or superseded by later TB work.
- Boundaries: historical scientific/operational boundaries preserved as
  recorded in the archive.
- Next task: see `docs/task_backlog.md` for the active queue.

### TB-051: TB-049, TB-050, and TB-051 as the active queue.

- Date: see archive if not listed in the original entry.
- Commit: see git history / archive.
- Objective: canonicalize the rebuildable reduced-output workflow in the
- Files changed: see archive for the full historical record.
- Implementation summary: normalized from the pre-refactor log; full details
  are preserved in `docs/archive/agent_work_log_archive.md`.
- Checks run: see archive for original command lists.
- Result/status: completed or superseded by later TB work.
- Boundaries: historical scientific/operational boundaries preserved as
  recorded in the archive.
- Next task: see `docs/task_backlog.md` for the active queue.

### TB-052: Support And Nodata Uncertainty Decomposition

- Date: see archive if not listed in the original entry.
- Commit: see git history / archive.
- Objective: Added a read-only decomposition for
- Files changed: see archive for the full historical record.
- Implementation summary: normalized from the pre-refactor log; full details
  are preserved in `docs/archive/agent_work_log_archive.md`.
- Checks run: see archive for original command lists.
- Result/status: completed or superseded by later TB work.
- Boundaries: historical scientific/operational boundaries preserved as
  recorded in the archive.
- Next task: see `docs/task_backlog.md` for the active queue.

### TB-053: Closure Gap Deltas

- Date: see archive if not listed in the original entry.
- Commit: see git history / archive.
- Objective: Added a read-only closure-gap delta helper that
- Files changed: see archive for the full historical record.
- Implementation summary: normalized from the pre-refactor log; full details
  are preserved in `docs/archive/agent_work_log_archive.md`.
- Checks run: see archive for original command lists.
- Result/status: completed or superseded by later TB work.
- Boundaries: historical scientific/operational boundaries preserved as
  recorded in the archive.
- Next task: see `docs/task_backlog.md` for the active queue.

### TB-054: Next proposed milestone: TB-054.

- Date: see archive if not listed in the original entry.
- Commit: see git history / archive.
- Objective: Decompose support/nodata uncertainty for the closure-limiting
- Files changed: see archive for the full historical record.
- Implementation summary: normalized from the pre-refactor log; full details
  are preserved in `docs/archive/agent_work_log_archive.md`.
- Checks run: see archive for original command lists.
- Result/status: completed or superseded by later TB work.
- Boundaries: historical scientific/operational boundaries preserved as
  recorded in the archive.
- Next task: see `docs/task_backlog.md` for the active queue.

### TB-055: Historical Entry

- Date: see archive if not listed in the original entry.
- Commit: see git history / archive.
- Objective: Historical TB entry normalized during log cleanup; see archive for full original context.
- Files changed: see archive for the full historical record.
- Implementation summary: normalized from the pre-refactor log; full details
  are preserved in `docs/archive/agent_work_log_archive.md`.
- Checks run: see archive for original command lists.
- Result/status: completed or superseded by later TB work.
- Boundaries: historical scientific/operational boundaries preserved as
  recorded in the archive.
- Next task: see `docs/task_backlog.md` for the active queue.

### TB-056: Added a first-class COG-ready export path to

- Date: see archive if not listed in the original entry.
- Commit: see git history / archive.
- Objective: Historical TB entry normalized during log cleanup; see archive for full original context.
- Files changed: see archive for the full historical record.
- Implementation summary: normalized from the pre-refactor log; full details
  are preserved in `docs/archive/agent_work_log_archive.md`.
- Checks run: see archive for original command lists.
- Result/status: completed or superseded by later TB work.
- Boundaries: historical scientific/operational boundaries preserved as
  recorded in the archive.
- Next task: see `docs/task_backlog.md` for the active queue.

### TB-057: Physical Credibility Evidence Requirements

- Date: see archive if not listed in the original entry.
- Commit: see git history / archive.
- Objective: Added a read-only physical-credibility evidence
- Files changed: see archive for the full historical record.
- Implementation summary: normalized from the pre-refactor log; full details
  are preserved in `docs/archive/agent_work_log_archive.md`.
- Checks run: see archive for original command lists.
- Result/status: completed or superseded by later TB work.
- Boundaries: historical scientific/operational boundaries preserved as
  recorded in the archive.
- Next task: see `docs/task_backlog.md` for the active queue.

### TB-058: Stabilize Command-Plan And COG Readiness Drift

- Date: 2026-05-16
- Commit: `35c5431`
- Objective: tighten worker-facing command-plan, GIS/COG, and diagnostic-interpretation wording so clean checkouts and converted-package readiness are explicit.
- Files changed: scripts/generate_pilot_command_plan.py, scripts/audit_gis_cog_package_readiness.py, scripts/summarize_tschamut_conditional_diagnostic_interpretation.py, tests/test_pilot_command_plan.py, tests/test_gis_cog_package_readiness.py, tests/test_tschamut_conditional_diagnostic_interpretation.py, docs/pilot_gis_package.md, docs/archive/model_benchmark_execution_report.md, docs/tschamut_public_conditional_pilot_gate_report.md, docs/tschamut_public_same_scale_uncertainty_envelope.md, docs/task_backlog.md
- Implementation summary: command-plan tests gained an explicit blocked-readiness path; GIS/COG audit now reports converted-package readiness separately from standard roots; diagnostic interpretation now names legacy summary-only, native reduced-output, standard-root COG-blocked, and converted-package-ready states explicitly; stale export guidance was rewritten in the user-facing docs.
- Checks run: py_compile, unit tests, helper JSON emits, command-plan/audit/diagnostic helper runs, rg stale-guidance search, git diff --check, repo consistency, pre-commit.
- Result/status: completed.
- Boundaries: no new simulation, ensemble, COG manual QA, or operational/scale-up claim was introduced.
- Next task: `TB-059`

### TB-059: Emit Persistent Spatial Disagreement Stability Zones

- Date: 2026-05-16
- Commit: `256b5d7`
- Objective: add a compact, deterministic stability-zone summary so workers can distinguish persistent closure-limiting regions from localized deferrable disagreement.
- Files changed: scripts/summarize_spatial_same_scale_uncertainty.py, scripts/summarize_tschamut_closure_gap_deltas.py, scripts/summarize_tschamut_conditional_pilot_closure.py, scripts/summarize_tschamut_conditional_diagnostic_interpretation.py, tests/test_spatial_same_scale_uncertainty.py, tests/test_tschamut_conditional_pilot_closure.py, tests/test_tschamut_closure_gap_deltas.py, tests/test_tschamut_conditional_diagnostic_interpretation.py, docs/tschamut_public_same_scale_uncertainty_envelope.md, docs/tschamut_public_conditional_pilot_gate_report.md, docs/task_backlog.md
- Implementation summary: extended the same-scale spatial uncertainty helper with per-layer stability-zone summaries and deterministic zone counts/fractions/bounding boxes; threaded the zone summary through the closure and closure-gap helpers; kept closure status conservative and unchanged; updated the gate and uncertainty-envelope docs to explain that the new zones clarify the blocker without changing the outcome.
- Checks run: py_compile on the touched scripts/tests; unit tests for spatial uncertainty, closure, closure-gap deltas, diagnostic interpretation, and agent task context; measured JSON/text report emits from the spatial, closure, closure-gap, and diagnostic helpers.
- Result/status: completed.
- Boundaries: no tuning, no physics change, no new ensemble, no accepted/no-go status change, and no operational/scale-up/annual-frequency/risk/exposure/vulnerability/physical-probability claim was introduced.
- Next task: backlog refill needed; see `docs/task_backlog.md`.

### TB-060: Trace Uncertainty Hotspots To Source And Scenario Evidence

- Date: 2026-05-16
- Commit: `9b17a81`
- Objective: add a read-only hotspot provenance helper that maps the selected high-uncertainty cells to source-zone metadata, the committed scenario row, run-level trajectory/deposition evidence, and artifact roots without adding simulation or tuning.
- Files changed: scripts/summarize_tschamut_hotspot_provenance.py, tests/test_tschamut_hotspot_provenance.py, docs/tschamut_public_conditional_pilot_gate_report.md, docs/task_backlog.md
- Implementation summary: added a compact provenance report with per-layer hotspot provenance classes, explicit can/cannot-attributable evidence classes, LV95 source-zone geometry checks, run-level trajectory/deposition summaries, artifact-root enumeration, and prioritized unknowns for a later bounded ensemble; documented the attribution limits in the gate report.
- Checks run: see git history and archived worker output for the focused checks used before commit
- Result/status: completed.
- Boundaries: no new simulation, source-zone tuning, operational interpretation, annual-frequency claim, physical-probability claim, or risk/exposure/vulnerability claim was introduced.
- Next task: `TB-061`

### TB-061: Define A Bounded Next-Ensemble Feasibility Probe

- Date: 2026-05-16
- Commit: `aa3afa7`
- Objective: add a read-only feasibility report and deferred command-plan template for the smallest bounded same-scale probe that could still clarify the remaining closure question without authorizing scale-up.
- Files changed: scripts/summarize_bounded_next_ensemble_feasibility_probe.py, scripts/generate_pilot_command_plan.py, tests/test_bounded_next_ensemble_feasibility_probe.py, tests/test_pilot_command_plan.py, docs/tschamut_public_conditional_pilot_gate_report.md, docs/task_backlog.md, docs/agent_work_log.md
- Implementation summary: added a JSON/text helper that composes closure-gap, rebuildable-reduced-output, runtime-scaling, and single-job-sufficiency evidence into a bounded next-probe report; added a deferred native `rebuildable_reduced_output` command-plan template; updated the gate report to publish the proposed probe scope, boundedness proof, and explicit no-go conditions.
- Checks run: `PYENV_VERSION=system uv run python -m py_compile scripts/summarize_bounded_next_ensemble_feasibility_probe.py scripts/generate_pilot_command_plan.py tests/test_bounded_next_ensemble_feasibility_probe.py tests/test_pilot_command_plan.py`; `PYENV_VERSION=system uv run python -m unittest tests.test_bounded_next_ensemble_feasibility_probe tests.test_pilot_command_plan`; `PYENV_VERSION=system uv run python scripts/summarize_bounded_next_ensemble_feasibility_probe.py --format json`
- Result/status: completed.
- Boundaries: no ensemble was run, no parameters were tuned, and no scale-up or distributed execution was authorized.
- Next task: `TB-062`

### TB-062: Generate Chant Sura Dry-Run Case Skeleton

- Date: 2026-05-16
- Commit: `d5f220b`
- Objective: add a dry-run Chant Sura / Fluelapass case skeleton helper and command-plan entry that record the real terrain, source-zone, scenario, and policy references while keeping public context deferred.
- Files changed: scripts/generate_chant_sura_fluelapass_dry_run_case_skeleton.py, scripts/generate_pilot_command_plan.py, tests/test_chant_sura_fluelapass_dry_run_case_skeleton.py, tests/test_pilot_command_plan.py, docs/task_backlog.md, docs/agent_work_log.md
- Implementation summary: added a `/tmp`-bounded skeleton generator that writes a YAML case with explicit deferred public-context placeholders and an ensemble-execution block; surfaced the helper as a separate ready command-plan group; added tests that stage minimal core inputs, validate the references, and keep the second-site run path blocked.
- Checks run: see git history and archived worker output for the focused checks used before commit
- Result/status: completed.
- Boundaries: no second-site ensemble, hazard build, downloads, portability claim, or physical-evidence claim was introduced.
- Next task: `TB-063`

### TB-063: Add AOI-To-Swisstopo Acquisition Dry-Run Planner

- Date: 2026-05-16
- Commit: `1a92388`
- Objective: add a deterministic AOI-to-swisstopo dry-run planner that enumerates required public geodata products, expected staging paths, and unresolved acquisition decisions before any real second-site staging.
- Files changed: scripts/plan_swisstopo_aoi_acquisition.py, scripts/generate_pilot_command_plan.py, tests/test_swisstopo_aoi_acquisition_planner.py, tests/test_pilot_command_plan.py, docs/public_real_site_geodata_preparation.md, docs/swisstopo_data_strategy.md, docs/task_backlog.md, docs/agent_work_log.md
- Implementation summary: added a read-only planner that reuses the second-site manifest contract, reports product and metadata staging paths separately, keeps the current deferred public-context boundary explicit, and surfaces the planner as the first step in the portable command plan and workflow docs.
- Checks run: focused unittest suite for the new planner plus second-site command-plan and preflight/skeleton coverage; `PYENV_VERSION=system uv run python -m py_compile scripts/plan_swisstopo_aoi_acquisition.py scripts/generate_pilot_command_plan.py tests/test_swisstopo_aoi_acquisition_planner.py tests/test_pilot_command_plan.py`
- Result/status: completed.
- Boundaries: no downloads, no generated public-context artifacts, no claim that products are locally staged unless files exist, and no operational/scale-up/annual-frequency/risk/exposure/vulnerability/physical-probability claim was introduced.
- Next task: `TB-064`

### TB-064: Verify COG Export Layer Parity And Audit Semantics

- Date: 2026-05-16
- Commit: `bd2686f`
- Objective: make the GIS/COG audit report both package readiness and explicit layer-inventory parity/scope status for the standard gate root versus the converted `gate_v1_cog_export` proof.
- Files changed: scripts/audit_gis_cog_package_readiness.py, tests/test_gis_cog_package_readiness.py, docs/pilot_gis_package.md, docs/public_real_site_geodata_preparation.md, docs/current_maturity_snapshot.md, docs/tschamut_public_conditional_pilot_gate_report.md, docs/task_backlog.md, docs/agent_work_log.md
- Implementation summary: added layer-inventory comparison logic to the GIS/COG audit helper, including standard-versus-converted layer counts, omitted-layer names, omitted-layer semantics, and a text-report summary; added a regression test that compares the 22-layer standard gate root to the 20-layer converted proof and asserts the omitted 0.5 m jump-height pair; updated the package and pilot docs to state that the current COG proof intentionally omits the 0.5 m jump-height layers because that export command only requests the 1 m and 2 m thresholds.
- Checks run: `PYENV_VERSION=system uv run python -m unittest tests.test_gis_cog_package_readiness tests.test_same_scale_cog_package_conversion`; `PYENV_VERSION=system uv run python scripts/audit_gis_cog_package_readiness.py --format json --artifact-root hazard/results/tschamut_public_pilot/gate_v1 --converted-package-root hazard/results/tschamut_public_pilot/gate_v1_cog_export`; `git diff --check`; `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`; `scripts/git-hooks/pre-commit`; `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
- Result/status: completed.
- Boundaries: no generated rasters were committed, no manual QGIS acceptance was claimed, and no operational, scale-up, annual-frequency, risk, exposure, vulnerability, or physical-probability claim was introduced.
- Next task: `TB-065`

### TB-065: Score Physical-Credibility Evidence Acquisition Priorities

- Date: 2026-05-16
- Commit: `8e16a86`
- Objective: rank the concrete evidence acquisitions that most reduce the physical-credibility gap while keeping the current claim boundaries unchanged.
- Files changed: docs/agent_work_log.md, docs/swisstopo_data_strategy.md, docs/task_backlog.md, docs/tschamut_public_conditional_pilot_gate_report.md, scripts/map_physical_credibility_evidence_requirements.py, tests/test_physical_credibility_evidence_requirements.py
- Implementation summary: added a ranked evidence-acquisition matrix to the physical-credibility helper with per-class priority, expected claim unlocked, required data, current repo gap, and separated current-repo versus future-acquisition evidence; surfaced a first-actionable versus deferred acquisition summary in JSON/text; updated the gate report and swisstopo strategy to state that observed runout/deposition is the first actionable acquisition and source-frequency evidence remains deferred.
- Checks run: `PYENV_VERSION=system uv run python scripts/map_physical_credibility_evidence_requirements.py --format json`; `PYENV_VERSION=system uv run python -m unittest tests.test_physical_credibility_evidence_requirements`; `git diff --check`; `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`; `scripts/git-hooks/pre-commit`; `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
- Result/status: completed.
- Boundaries: no calibration fitting, no annual-frequency model, no operational, risk, exposure, or vulnerability claim was introduced, and claim boundaries remain unchanged.
- Next task: `TB-066`

### TB-066: Reconcile Canonical Diagnostic Interpretation With Current Product Paths

- Date: 2026-05-16
- Commit: `9ccc805`
- Objective: reconcile the canonical diagnostic interpretation with the current reduced-output and COG-export product paths so workflow mitigations are separated from scientific blockers without changing the diagnostic status.
- Files changed: docs/tschamut_public_conditional_pilot_gate_report.md, docs/task_backlog.md, scripts/summarize_tschamut_conditional_diagnostic_interpretation.py, tests/test_tschamut_conditional_diagnostic_interpretation.py
- Implementation summary: split the interpretation output into explicit scientific blockers, workflow blockers, product-path statuses, and workflow mitigations; kept `inconclusive_conditional_diagnostic` unchanged; surfaced the native reduced-output path and the COG export path as separate mitigations while preserving the `summary_only_not_rebuildable` and `standard_gis_roots_cog_blocked` blocker names; updated the gate report to reference the new interpretation structure.
- Checks run: `PYENV_VERSION=system uv run python -m unittest tests.test_tschamut_conditional_diagnostic_interpretation`; `PYENV_VERSION=system uv run python -m py_compile scripts/summarize_tschamut_conditional_diagnostic_interpretation.py tests/test_tschamut_conditional_diagnostic_interpretation.py`
- Result/status: completed.
- Boundaries: no acceptance claim, no no-go reclassification, no new simulation, and no operational semantics were introduced.
- Next task: backlog refill needed; see `docs/task_backlog.md`.

### TB-067: Export Spatial Stability And Confidence Layers

- Date: 2026-05-16
- Commit: `e161df8`
- Objective: expose the measured same-scale stability-zone classifications as deterministic GIS-ready diagnostic summaries without changing the closure decision.
- Files changed: docs/hazard_layers.md, docs/task_backlog.md, docs/tschamut_public_same_scale_uncertainty_envelope.md, scripts/summarize_spatial_same_scale_uncertainty.py, scripts/summarize_tschamut_conditional_pilot_closure.py, tests/test_spatial_same_scale_uncertainty.py, tests/test_tschamut_conditional_pilot_closure.py
- Implementation summary: added a pure spatial uncertainty-layer summary that classifies persistent agreement, persistent disagreement, support/nodata-sensitive, closure-limiting, and deferrable disagreement regions; added optional ignored JSON/CSV/GeoJSON exports for the summary; threaded the uncertainty-layer summary through the closure helper as evidence only; and documented why this step stays in summary/vector form instead of a new raster hazard product.
- Checks run: `PYENV_VERSION=system uv run python -m py_compile scripts/summarize_spatial_same_scale_uncertainty.py scripts/summarize_tschamut_conditional_pilot_closure.py tests/test_spatial_same_scale_uncertainty.py tests/test_tschamut_conditional_pilot_closure.py`; `PYENV_VERSION=system uv run python -m unittest tests.test_spatial_same_scale_uncertainty tests.test_tschamut_conditional_pilot_closure`; `PYENV_VERSION=system uv run python scripts/summarize_spatial_same_scale_uncertainty.py --format json >/tmp/tb067_spatial_summary.json`; `PYENV_VERSION=system uv run python scripts/summarize_tschamut_conditional_pilot_closure.py --format json >/tmp/tb067_closure_summary.json`
- Result/status: completed.
- Boundaries: no tuning, no new ensemble, no hazard reclassification, no operational claim, and no physical-probability claim were introduced.
- Next task: `TB-068`

### TB-068: Canonicalize Rebuild-Compatible Reduced Output Workflow

- Date: 2026-05-16
- Commit: `acb5fd6`
- Objective: make the native `rebuildable_reduced_output` path the canonical rebuild-compatible reduced workflow while keeping the derivation script as a compatibility fallback.
- Files changed: docs/current_maturity_snapshot.md, docs/task_backlog.md, docs/tschamut_public_bounded_validation_output_profile.md, scripts/check_hazard_rebuild_output_profile.py, scripts/check_same_scale_artifact_readiness.py, scripts/derive_hazard_rebuild_reduced_profile.py, scripts/generate_pilot_command_plan.py, scripts/summarize_bounded_reducer_runtime_scaling.py, tests/test_bounded_reducer_runtime_scaling.py, tests/test_hazard_rebuild_output_profile.py, tests/test_pilot_command_plan.py, tests/test_same_scale_artifact_readiness.py
- Implementation summary: updated the rebuild-profile checker to treat the native reduced mode as canonical and keep legacy derivation labeled as fallback-only; exposed the native reduced root and readiness state in the same-scale preflight; extended the command plan to surface the native reduced path first and the derivation command as a fallback; and added the canonical reduced-mode comparison to the runtime/output summary.
- Checks run: `PYENV_VERSION=system uv run python -m unittest tests.test_hazard_rebuild_output_profile tests.test_same_scale_artifact_readiness tests.test_pilot_command_plan tests.test_bounded_reducer_runtime_scaling`; `PYENV_VERSION=system uv run python scripts/check_hazard_rebuild_output_profile.py --format json`; `PYENV_VERSION=system uv run python scripts/check_same_scale_artifact_readiness.py --format json`; `PYENV_VERSION=system uv run python scripts/generate_pilot_command_plan.py --site tschamut_same_scale --format json`; `PYENV_VERSION=system uv run python scripts/summarize_bounded_reducer_runtime_scaling.py --format json`; `git diff --check`; `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`; `scripts/git-hooks/pre-commit`; `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
- Result/status: completed.
- Boundaries: no tuning, no ensemble increase, no distributed execution, and no operational claims were introduced.
- Next task: `TB-069`

### TB-069: Generate Canonical Conditional Diagnostic Interpretation Artifact

- Date: 2026-05-16
- Commit: `27d2fe3`
- Objective: materialize the canonical conditional diagnostic interpretation into a deterministic JSON/text bundle path while keeping it non-operational and preserving claim boundaries.
- Files changed: scripts/summarize_tschamut_conditional_diagnostic_interpretation.py, tests/test_tschamut_conditional_diagnostic_interpretation.py, docs/tschamut_public_conditional_pilot_gate_report.md, docs/tschamut_public_same_scale_uncertainty_envelope.md, docs/tschamut_public_bounded_validation_output_profile.md, docs/balfrin_single_job_execution_sufficiency.md, docs/task_backlog.md, docs/agent_work_log.md
- Implementation summary: added `--artifact-dir` plus optional text output support to the canonical diagnostic helper; wrote paired JSON/text artifacts with a compact synthesis brief that surfaces uncertainty, convergence, closure, output, GIS, context, and physical-credibility fields; added regression tests for bundle writing and blocked/missing-input handling; and updated the gate, uncertainty, bounded-output, and Balfrin docs to point at the canonical synthesis bundle path.
- Checks run: `PYENV_VERSION=system uv run python -m py_compile scripts/summarize_tschamut_conditional_diagnostic_interpretation.py tests/test_tschamut_conditional_diagnostic_interpretation.py`; `PYENV_VERSION=system uv run python -m unittest tests.test_tschamut_conditional_diagnostic_interpretation`; `PYENV_VERSION=system uv run python - <<'PY'` smoke check for `summary.main([...])` with a temporary missing-input override and `--artifact-dir /tmp/tb069_diag_bundle_check/validation/private/tschamut_public_pilot/diagnostic_interpretation_v1`; `git diff --check`; `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`; `scripts/git-hooks/pre-commit`; `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
- Result/status: completed.
- Boundaries: no operational semantics, no new simulation, no reclassification, and no physical validation or scale-up claim were introduced.
- Next task: `TB-070`

### TB-070: Quantify Spatial Uncertainty Hotspot Persistence Across Seeds

- Date: 2026-05-16
- Commit: `7526ce1`
- Objective: quantify how the existing spatial same-scale hotspot cells persist across the gate, target, sampling probe v1, and sampling probe v2 artifacts without adding new runs.
- Files changed: docs/agent_work_log.md, docs/decision_log.md, docs/task_backlog.md, docs/tschamut_public_same_scale_uncertainty_envelope.md, scripts/summarize_spatial_same_scale_uncertainty.py, tests/test_spatial_same_scale_uncertainty.py
- Implementation summary: added a deterministic hotspot-persistence summary to the spatial helper by counting how often the selected hotspot cells reappear across the six pairwise artifact comparisons, exposed pairwise-support histograms and stability classes per layer, updated the spatial envelope doc to state which layers are stable versus transient, and added regression coverage on the small committed fixture set.
- Checks run: `PYENV_VERSION=system uv run python -m unittest tests.test_spatial_same_scale_uncertainty tests.test_tschamut_hotspot_provenance tests.test_same_scale_sampling_uncertainty -v`; `PYENV_VERSION=system uv run python scripts/summarize_spatial_same_scale_uncertainty.py --format json >/tmp/tb070_spatial_summary.json`; `git diff --check`; `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`; `scripts/git-hooks/pre-commit`; `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
- Result/status: completed.
- Boundaries: no new ensemble runs, no tuning, no operational claim, and no scale-up or probability semantics were introduced.
- Next task: `TB-071`

### TB-071: Define Physical-Credibility Claim Boundaries Per Product Layer

- Date: 2026-05-16
- Commit: `8a5c47d`
- Objective: distinguish layer-specific diagnostic usefulness, reproducibility, physical credibility, and operational inadmissibility for the current hazard and intensity products.
- Files changed: docs/hazard_layers.md, docs/tschamut_public_conditional_pilot_gate_report.md, docs/validation_maturity_framework.md, docs/task_backlog.md, docs/agent_work_log.md, scripts/assess_validation_calibration_evidence_gaps.py, scripts/map_physical_credibility_evidence_requirements.py, tests/test_validation_calibration_evidence_gaps.py, tests/test_physical_credibility_evidence_requirements.py
- Implementation summary: added deterministic product-layer credibility boundaries to the physical-credibility assessment helper and threaded them through the evidence-requirements helper; separated diagnostic usefulness, reproducibility, physical credibility, and operational inadmissibility in the JSON and text reports; and documented why `max_kinetic_energy` and `max_jump_height` are the most scientifically fragile current layers while the reach, deposition, and conditional exceedance families remain conditional diagnostics only.
- Checks run: `PYENV_VERSION=system uv run python -m unittest tests.test_validation_calibration_evidence_gaps tests.test_physical_credibility_evidence_requirements`; `PYENV_VERSION=system uv run python scripts/assess_validation_calibration_evidence_gaps.py --format json >/tmp/tb071_assess.json`; `PYENV_VERSION=system uv run python scripts/map_physical_credibility_evidence_requirements.py --format json >/tmp/tb071_map.json`
- Result/status: completed.
- Boundaries: no calibration, tuning, operational, scale-up, annual-frequency, risk, exposure, vulnerability, or physical-probability claim was introduced, and no product was reclassified as physically validated.
- Next task: `TB-072`

### TB-072: Stage First Real Chant Sura Public-Context Acquisition Plan

- Date: 2026-05-16
- Commit: `1150121`
- Objective: add a deterministic Chant Sura public-context acquisition plan and dry-run summary that names the exact staging roots and metadata contracts for the deferred SWISSIMAGE, swissTLM3D, swissSURFACE3D, swissSURFACE3D Raster, and swissBUILDINGS3D products without downloading public geodata.
- Files changed: docs/public_real_site_geodata_preparation.md, docs/swisstopo_data_strategy.md, scripts/check_second_site_public_geodata_preflight.py, scripts/plan_swisstopo_aoi_acquisition.py, tests/test_second_site_public_geodata_preflight.py, tests/test_swisstopo_aoi_acquisition_planner.py, docs/task_backlog.md, docs/agent_work_log.md
- Implementation summary: enriched the shared second-site preflight helper with a deterministic public-context acquisition plan and summary that expose the expected staging roots, metadata contracts, and dry-run-only status for the Chant Sura candidate; surfaced the same plan through the AOI acquisition planner; updated the docs to distinguish the synthetic core-staging helper from real public-context readiness; and added regression coverage for the new acquisition-plan fields and summaries.
- Checks run: `PYENV_VERSION=system uv run python -m unittest tests.test_second_site_public_geodata_preflight tests.test_swisstopo_aoi_acquisition_planner`; `PYENV_VERSION=system uv run python scripts/check_second_site_public_geodata_preflight.py --site-config tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml --format json`; `PYENV_VERSION=system uv run python scripts/plan_swisstopo_aoi_acquisition.py --site-config tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml --format json`; `git diff --check`; `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`; `scripts/git-hooks/pre-commit`; `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
- Result/status: completed.
- Boundaries: no second-site ensemble, hazard build, downloads, operational claim, scale-up claim, or physical-probability claim was introduced.
- Next task: `TB-073`

### TB-073: Stabilize Clean-Checkout Python Test Gates

- Date: 2026-05-16
- Commit: `f2cfc05`
- Objective: keep the Python regression suite green on a clean checkout without depending on ignored local Tschamut or Chant Sura artifact roots.
- Files changed: docs/agent_work_log.md, docs/task_backlog.md, tests/test_hazard_context_overlap.py, tests/test_pilot_command_plan.py, tests/test_tschamut_public_context_layers.py
- Implementation summary: added brief test comments that separate clean-checkout fixture and mock coverage from the optional GDAL-backed local integration check, and documented that the Chant Sura / Flüelapass command-plan assertions are metadata-only and do not require staged public-context artifacts.
- Checks run: `PYENV_VERSION=system uv run python -m unittest tests.test_hazard_context_overlap tests.test_tschamut_public_context_layers tests.test_pilot_command_plan`; `PYENV_VERSION=system uv run python -m unittest discover -s tests -p 'test_*.py'`
- Result/status: completed.
- Boundaries: no scientific classifications, hazard-layer semantics, physics, operational boundaries, scale-up authorization, or artifact-generation policy were changed.
- Next task: `TB-074`

### TB-074: Stabilize Clean-Checkout Rust Reduced-Output Test

- Date: 2026-05-16
- Commit: `f745a0d`
- Objective: keep the Rust reduced-output regression test green on a clean checkout without depending on ignored Tschamut same-scale artifacts.
- Files changed: tests/config_io_terrain.rs, tests/fixtures/rebuildable_reduced_output/tschamut_public_target_gate_rebuildable_reduced_case.yaml, tests/fixtures/rebuildable_reduced_output/validation_output_mode_rebuildable_reduced_release_points.csv, tests/fixtures/rebuildable_reduced_output/validation_output_mode_rebuildable_reduced_deposition_points.csv
- Implementation summary: replaced the reduced-output fixture with a tiny self-contained plane case, added committed observation CSVs, and updated the integration test to inject temporary output paths while asserting trajectory, deposition, impact-event CSV, diagnostics, trajectory metadata, and stop-state outputs. The test now proves the native `rebuildable_reduced_output` builder-facing contract without private or ignored artifacts.
- Checks run: `PYENV_VERSION=system uv run python scripts/print_agent_task_context.py --task TB-074 --format json`; `rg -n "^### TB-074:" docs/task_backlog.md`; `PYENV_VERSION=system CARGO_TARGET_DIR=/tmp/rust-rockfall-target cargo test validation_output_mode_rebuildable_reduced_output_writes_builder_facing_outputs -- --nocapture`; `PYENV_VERSION=system CARGO_TARGET_DIR=/tmp/rust-rockfall-target cargo test`; `git diff --check`; `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`; `scripts/git-hooks/pre-commit`; `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
- Result/status: completed.
- Boundaries: no simulator physics, reduced-output scientific meaning, summary-only rebuildability, operational, scale-up, annual-frequency, risk, exposure, vulnerability, or physical-probability claim was changed.
- Next task: `TB-075`

### TB-075: Emit Full-Scope COG Export Parity Proof

- Date: 2026-05-16
- Commit: `1a86ef8`
- Objective: make the same-scale COG export path and audit report distinguish full parity from a bounded scope delta while keeping the standard-root blocked state visible.
- Files changed: docs/agent_work_log.md, docs/pilot_gis_package.md, docs/task_backlog.md, scripts/audit_gis_cog_package_readiness.py, scripts/generate_pilot_command_plan.py, tests/test_gis_cog_package_readiness.py, tests/test_hazard_layers.py, tests/test_pilot_command_plan.py
- Implementation summary: updated the same-scale COG export command plan to request the full gate threshold scope by adding the 0.5 m jump-height threshold; extended the GIS/COG audit to report standard-root layer counts, converted-root layer counts, explicit scope-delta metadata, and the new `cog_package_ready_with_scope_delta` status alongside the standard `gis_package_ready_cog_blocked` state; and refreshed the pilot GIS package docs and focused regression tests to cover parity, blocked-standard, and scope-delta cases.
- Checks run: `PYENV_VERSION=system uv run python -m unittest tests.test_gis_cog_package_readiness.GisCogPackageReadinessTest tests.test_pilot_command_plan.PilotCommandPlanTest tests.test_hazard_layers.HazardLayerTests.test_cog_export_runs_a_post_export_package_step`
- Result/status: completed.
- Boundaries: no generated rasters were committed, no manual QGIS acceptance was required, and no operational GIS claim was introduced.
- Next task: `TB-076`

### TB-076: Define Conditional Gridpoint Curve Product Contract

- Date: 2026-05-16
- Commit: `b8dcd5e`
- Objective: define a machine-readable contract for conditional gridpoint exceedance curves that current hazard maps can emit and audit without annual-frequency claims.
- Files changed: scripts/build_hazard_layers.py, tests/test_hazard_layers.py, docs/hazard_layers.md, docs/hazard_map_semantics.md, docs/tschamut_public_conditional_pilot_gate_report.md, docs/task_backlog.md, docs/agent_work_log.md
- Implementation summary: added a `conditional_gridpoint_curve_contract_v1` summary to the hazard-layer metadata and run manifest so each conditional curve report now records the per-gridpoint table schema, threshold units, normalization scopes, denominator semantics, and explicitly unsupported annual or physical-frequency fields; added a focused regression that validates the contract shape from an existing generated summary-only run; and updated the hazard-layer, semantics, and Tschamut gate docs to separate conditional exceedance curves from physical intensity-frequency language.
- Checks run: `PYENV_VERSION=system uv run python -m unittest tests.test_hazard_layers.HazardLayerTests.test_conditional_curve_summary_only_suppresses_large_curve_table tests.test_hazard_layers.HazardLayerTests.test_map_package_metadata_labels_weighted_outputs_without_changing_layers tests.test_hazard_layers.HazardLayerTests.test_phase1_smoke_example_runs_validation_and_labelled_hazard_package`
- Result/status: completed.
- Boundaries: no annual-frequency modelling, return periods, source occurrence rates, risk, exposure, vulnerability, operational use, or physical-probability claim was introduced.
- Next task: `TB-077`

### TB-077: Prototype AOI-To-Release-Zone Heuristic Dry Run

- Date: 2026-05-16
- Commit: `3bf6bd9`
- Objective: add a deterministic, fixture-backed release-zone heuristic dry run that accepts an AOI/site config, reports the candidate release-zone screening requirements and inputs, and keeps the Chant Sura example honestly in `deferred_public_context_inputs` until real context is staged.
- Files changed: scripts/plan_release_zone_heuristic_dry_run.py, tests/test_release_zone_heuristic_dry_run.py, docs/public_real_site_geodata_preparation.md, docs/swisstopo_data_strategy.md, docs/task_backlog.md, docs/agent_work_log.md
- Implementation summary: added a new dry-run helper that reuses the second-site preflight report to separate heuristic requirements, concrete terrain/source/scenario inputs, and blocked or missing products; surfaced a deterministic text/JSON report for the Chant Sura fixture without claiming a real release-zone interpretation; documented the missing public-context prerequisites and the heuristic boundary in the Swiss geodata guidance; and added regression coverage for the blocked/deferred report shape and deterministic rendering.
- Checks run: see git history and archived worker output for the focused checks used before commit
- Result/status: completed.
- Boundaries: no public data was downloaded, no second-site ensemble was run, no release-zone physics were tuned, and no synthetic fixture was treated as field evidence.
- Next task: `TB-078`

### TB-078: Generate Pragmatic Release-Plan Dry Run

- Date: 2026-05-16
- Commit: `42f8d0b`
- Objective: define how a portable source-zone candidate becomes deterministic release and block-scenario rows before any new ensemble is run.
- Files changed: docs/public_real_site_geodata_preparation.md, docs/swisstopo_data_strategy.md, docs/task_backlog.md, docs/agent_work_log.md, scripts/generate_pilot_command_plan.py, scripts/plan_release_plan_dry_run.py, tests/test_pilot_command_plan.py, tests/test_release_plan_dry_run.py
- Implementation summary: added a fixture-backed release-plan dry run that reads the staged Chant Sura / Flüelapass candidate source-zone metadata and the frozen Tschamut source-scenario policy, emits deterministic release counts plus release and block-scenario rows, and keeps reusable semantics, site-specific inputs, and Tschamut-only heuristics machine-readable; wired the portable command plan to include both the dry-run helper and a blocked template-only second-site execution command; and updated the Swiss geodata guidance plus focused regression coverage to keep the dry-run boundary explicit.
- Checks run: `PYENV_VERSION=system uv run python -m unittest tests.test_release_plan_dry_run tests.test_pilot_command_plan tests.test_release_zone_heuristic_dry_run`; `PYENV_VERSION=system uv run python scripts/plan_release_plan_dry_run.py --site-config tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml --format json >/tmp/tb078_release_plan.json`; `PYENV_VERSION=system uv run python scripts/generate_pilot_command_plan.py --site chant_sura_fluelapass --site-config tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml --format json >/tmp/tb078_command_plan.json`; `git diff --check`; `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`; `scripts/git-hooks/pre-commit`; `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
- Result/status: completed.
- Boundaries: no production release plan was created, no parameters were tuned, no ensembles were run, no scale-up or operational claim was authorized, and the second-site execution command remains template-only until public context is present.
- Next task: `TB-079`

### TB-079: Add Chant Sura Real-Context Readiness Gate Artifact

- Date: 2026-05-16
- Commit: `22f1f8b`
- Objective: add a Chant Sura real-context readiness gate artifact that compares the deterministic public-context acquisition plan, locally staged core inputs, and deferred public-context products without downloading new data.
- Files changed: scripts/check_chant_sura_real_context_readiness_gate.py, tests/test_chant_sura_real_context_readiness_gate.py, docs/public_real_site_geodata_preparation.md, docs/swisstopo_data_strategy.md, docs/task_backlog.md, docs/agent_work_log.md
- Implementation summary: added a new read-only Chant Sura gate script that reuses the second-site preflight and acquisition manifest to report ready core inputs, supporting local roots, deferred public-context products, and concrete next acquisition decisions for SWISSIMAGE, swissTLM3D, swissSURFACE3D, swissSURFACE3D Raster, and swissBUILDINGS3D; made the report explicitly state that synthetic core fixtures are not public-context evidence; added focused regression tests for JSON/text output and the ready-core/deferred-context boundary; and updated the Swiss geodata guidance to reference the new gate while removing TB-079 from the active backlog.
- Checks run: `PYENV_VERSION=system uv run python -m unittest tests.test_chant_sura_real_context_readiness_gate tests.test_second_site_public_geodata_preflight tests.test_swisstopo_aoi_acquisition_planner`; `git diff --check`; `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`; `scripts/git-hooks/pre-commit`; `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`; `git status --short --branch`
- Result/status: completed.
- Boundaries: no swisstopo downloads were performed, no second-site hazard map was run, and no synthetic core fixture was treated as public-context evidence or validation/calibration readiness.
- Next task: `TB-080`

### TB-080: Define Observed Runout And Deposition Validation Intake Contract

- Date: 2026-05-16
- Commit: `587e802`
- Objective: define a minimal observed runout/deposition benchmark-intake contract so the physical-credibility evidence map can name future geometry, event/source metadata, uncertainty, and objective-function placeholders without pretending a calibration dataset is already available.
- Files changed: docs/public_real_site_geodata_preparation.md, docs/tschamut_public_conditional_pilot_gate_report.md, docs/task_backlog.md, docs/agent_work_log.md, scripts/summarize_observed_runout_deposition_intake_contract.py, tests/test_observed_runout_deposition_intake_contract.py
- Implementation summary: added a new read-only intake-contract helper that defines the minimum benchmark schema for observed runout/deposition evidence, maps each contract field to the physical-credibility requirement class it would satisfy, and reports a blocked current state because no independent observed benchmark or calibration dataset is staged in the repository; extended the Tschamut gate and public-geodata guidance to point at the new contract boundary; and added focused regression coverage for the contract shape, requirement mapping, blocked state, and text rendering.
- Checks run: `PYENV_VERSION=system uv run python -m unittest tests.test_observed_runout_deposition_intake_contract tests.test_physical_credibility_evidence_requirements`; `PYENV_VERSION=system uv run python scripts/summarize_observed_runout_deposition_intake_contract.py --format json >/tmp/tb080_observed_runout_contract.json` (blocked helper returns exit code `2` by design); `PYENV_VERSION=system uv run python` to verify the blocked JSON report fields from `/tmp/tb080_observed_runout_contract.json`
- Result/status: completed.
- Boundaries: no validation data was fabricated, no fit parameters were introduced, no closure status changed, and no annual-frequency, risk, exposure, vulnerability, or operational claim was added.
- Next task: backlog refill needed

### TB-081: Harden Bounded Next-Ensemble Feasibility Probe

- Date: 2026-05-16
- Commit: `69603e1`
- Objective: harden the bounded next-ensemble feasibility probe so it reports a deferred planning state against the current reduced-output fixture instead of crashing on missing optional metadata from stale full-case assumptions.
- Files changed: scripts/summarize_bounded_next_ensemble_feasibility_probe.py, tests/test_bounded_next_ensemble_feasibility_probe.py, docs/task_backlog.md, docs/agent_work_log.md
- Implementation summary: added explicit optional-metadata handling to the bounded next-ensemble feasibility helper so missing probabilistic metadata and hazard-probability provenance yield a stable deferred planning status with null optional fields instead of `KeyError`; updated the focused regression test to assert the reduced fixture’s missing optional metadata path and the resulting deferred output shape; and removed TB-081 from the active backlog.
- Checks run: `PYENV_VERSION=system uv run python -m py_compile scripts/summarize_bounded_next_ensemble_feasibility_probe.py tests/test_bounded_next_ensemble_feasibility_probe.py`; `PYENV_VERSION=system uv run python -m unittest tests.test_bounded_next_ensemble_feasibility_probe`; `PYENV_VERSION=system uv run python scripts/summarize_bounded_next_ensemble_feasibility_probe.py --format json`; `git diff --check`; `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`; `scripts/git-hooks/pre-commit`; `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`; `git status --short --branch`
- Result/status: completed.
- Boundaries: no new ensemble was run, no scale-up was authorized, no physics or tuning was changed, and no closure interpretation was reinterpreted.
- Next task: `TB-082`

### TB-082: Split Benchmark Intake Readiness From Calibration Readiness

- Date: 2026-05-16
- Commit: `867bf65`
- Objective: split the observed runout/deposition intake contract so benchmark intake readiness depends only on the benchmark manifest and geometry requirements, while calibration dataset readiness is reported separately.
- Files changed: docs/public_real_site_geodata_preparation.md, docs/task_backlog.md, docs/tschamut_public_conditional_pilot_gate_report.md, docs/agent_work_log.md, scripts/summarize_observed_runout_deposition_intake_contract.py, tests/test_observed_runout_deposition_intake_contract.py
- Implementation summary: updated the observed runout/deposition intake helper so benchmark readiness is computed from the benchmark manifest and geometry inputs only, calibration readiness is emitted as a separate status channel, and the text/JSON report now names both readiness paths explicitly; extended the focused regression coverage with benchmark-present/calibration-absent and all-missing cases; and updated the Swiss geodata guidance plus the Tschamut gate report to describe the split contract.
- Checks run: `PYENV_VERSION=system uv run python -m unittest tests.test_observed_runout_deposition_intake_contract`; `PYENV_VERSION=system uv run python scripts/summarize_observed_runout_deposition_intake_contract.py --format json`; `git diff --check`; `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`; `scripts/git-hooks/pre-commit`; `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`; `git status --short --branch`
- Result/status: completed.
- Boundaries: no benchmark data was fabricated, no calibration parameters were fit, no physical-probability claim was added, and no operational boundary was changed.
- Next task: `TB-083`

### TB-083: Add Observed Runout Intake Readiness Pack Generator

- Date: 2026-05-16
- Commit: `3484683`
- Objective: make the observed runout/deposition contract actionable by generating a dry-run readiness pack for future real benchmark data.
- Files changed: scripts/summarize_observed_runout_deposition_intake_contract.py, tests/test_observed_runout_deposition_intake_contract.py, docs/public_real_site_geodata_preparation.md, docs/swisstopo_data_strategy.md, docs/current_maturity_snapshot.md, docs/task_backlog.md, docs/agent_work_log.md
- Implementation summary: added a caller-provided `--output-root` path to the observed runout/deposition intake helper so it can emit a template manifest, required geometry inventory, provenance checklist, and validation summary into a temporary readiness-pack directory; marked the generated pack explicitly as `template_non_evidence`; kept the existing contract/readiness split intact so the report still remains blocked for missing benchmark inputs; added regression coverage for the written pack structure and CLI success path; and updated the Swiss geodata guidance, maturity snapshot, and backlog so the pack generator is recorded as implemented rather than future work.
- Checks run: `PYENV_VERSION=system uv run python -m unittest tests.test_observed_runout_deposition_intake_contract -q`; `PYENV_VERSION=system uv run python scripts/summarize_observed_runout_deposition_intake_contract.py --output-root /tmp/tb083_readiness_pack --format text`; `git diff --check`; `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`; `scripts/git-hooks/pre-commit`; `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`; `git status --short --branch`
- Result/status: completed.
- Boundaries: no real benchmark data was created or claimed, no calibration or parameter fitting was introduced, no operational or physical-probability boundary moved, and the generated pack remains a template/non-evidence artifact only.
- Next task: `TB-084`

### TB-084: Resolve COG Export Layer-Scope Delta

- Date: 2026-05-16
- Commit: `e77dcce`
- Objective: make the same-scale COG export proof explicit about whether it is full parity with the standard 22-layer GIS package or intentionally bounded with a machine-readable omitted-layer list.
- Files changed: docs/task_backlog.md, scripts/audit_gis_cog_package_readiness.py, scripts/generate_pilot_command_plan.py, tests/test_gis_cog_package_readiness.py, tests/test_pilot_command_plan.py, docs/agent_work_log.md
- Implementation summary: added a structured `cog_scope` object to the GIS/COG readiness audit output so converted packages now report an explicit `full_scope`, `bounded_scope`, `expanded_scope`, or `inventory_mismatch` status alongside the omitted/extra layer names; exposed the same intended scope in the portable command plan metadata for the same-scale COG export command with the 22-layer reference inventory and 0.5 m jump-height layer requirements; and extended the focused regressions to pin the bounded-scope audit shape and the export command's explicit scope intent.
- Checks run: `PYENV_VERSION=system uv run python -m unittest tests.test_gis_cog_package_readiness tests.test_pilot_command_plan`; `PYENV_VERSION=system uv run python scripts/generate_pilot_command_plan.py --site tschamut_same_scale --format json >/tmp/tb084_command_plan.json`; `PYENV_VERSION=system uv run python scripts/audit_gis_cog_package_readiness.py --artifact-root hazard/results/tschamut_public_pilot/gate_v1 --converted-package-root hazard/results/tschamut_public_pilot/gate_v1_cog_export --format json >/tmp/tb084_audit.json`; `git diff --check`
- Result/status: completed.
- Boundaries: no generated rasters were committed, no manual QGIS acceptance was performed, and no operational GIS, scale-up, annual-frequency, risk, exposure, vulnerability, or physical-probability claim was introduced.
- Next task: `TB-085`

### TB-085: Attribute Closure-Limiting Hotspots To Source And Scenario Evidence

- Date: 2026-05-16
- Commit: `c3ea7bf`
- Objective: attribute the measured closure-limiting hotspots to committed source-zone, release, scenario, and support/nodata evidence without changing closure status or running new simulations.
- Files changed: docs/task_backlog.md, docs/tschamut_public_same_scale_uncertainty_envelope.md, scripts/summarize_tschamut_conditional_pilot_closure.py, scripts/summarize_tschamut_hotspot_provenance.py, tests/test_tschamut_conditional_pilot_closure.py, tests/test_tschamut_hotspot_provenance.py, docs/agent_work_log.md
- Implementation summary: extended the hotspot provenance helper with explicit per-layer attribution counts and fractions for shared-support magnitude, support/nodata sensitivity, source-zone overlap/outside relation, scenario identifier coverage, and unknown cell-level lineage; surfaced the same hotspot provenance report inside the conditional closure summary so the closure output now references the attribution evidence without altering any closure decision; tightened the focused regressions to pin the new schema on both synthetic and committed artifacts; and updated the same-scale envelope narrative plus the active backlog to reflect completion.
- Checks run: `PYENV_VERSION=system uv run python -m unittest tests.test_tschamut_hotspot_provenance tests.test_tschamut_conditional_pilot_closure tests.test_tschamut_closure_gap_deltas -v`; `PYENV_VERSION=system uv run python scripts/summarize_tschamut_hotspot_provenance.py --format json >/tmp/tb085_hotspot_provenance.json`; `PYENV_VERSION=system uv run python scripts/summarize_tschamut_hotspot_provenance.py --format text >/tmp/tb085_hotspot_provenance.txt`; `PYENV_VERSION=system uv run python scripts/summarize_tschamut_conditional_pilot_closure.py --format json >/tmp/tb085_closure.json`; `PYENV_VERSION=system uv run python scripts/summarize_tschamut_conditional_pilot_closure.py --format text >/tmp/tb085_closure.txt`; `git diff --check`; `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`; `scripts/git-hooks/pre-commit`; `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`; `git status --short`
- Result/status: completed.
- Boundaries: no new simulation was run, no physics or tuning was changed, no validation or operational claim was introduced, and attribution remained interpretive evidence only.
- Next task: `TB-086`

### TB-086: Summarize Same-Scale Ensemble Stability Frontier

- Date: 2026-05-16
- Commit: `7d81670`
- Objective: Combine the committed same-scale uncertainty, runtime/output footprint, bounded-feasibility, and closure-gap evidence into a bounded stability frontier for deciding whether another small probe would be informative.
- Files changed: scripts/summarize_same_scale_stability_frontier.py, tests/test_same_scale_stability_frontier.py, docs/balfrin_single_job_execution_sufficiency.md, docs/task_backlog.md, docs/agent_work_log.md
- Implementation summary: added a deterministic frontier helper that composes the existing uncertainty, runtime/output, bounded-next-probe feasibility, and closure-gap summaries; classified the current frontier as `additional_probe_informative` when the measured uncertainty spread remains non-zero while the probe footprint stays bounded and local; added regression coverage for the measured and blocked helper-contract paths plus CLI smoke checks; and added a short docs pointer from the Balfrin sufficiency note to the new frontier helper.
- Checks run: `PYENV_VERSION=system uv run python -m py_compile scripts/summarize_same_scale_stability_frontier.py tests/test_same_scale_stability_frontier.py`; `PYENV_VERSION=system uv run python -m unittest tests.test_same_scale_stability_frontier tests.test_same_scale_sampling_uncertainty tests.test_bounded_reducer_runtime_scaling tests.test_bounded_next_ensemble_feasibility_probe tests.test_tschamut_closure_gap_deltas`; `PYENV_VERSION=system uv run python scripts/summarize_same_scale_stability_frontier.py --format text`; `PYENV_VERSION=system uv run python scripts/summarize_same_scale_stability_frontier.py --format json`
- Result/status: completed.
- Boundaries: no new ensemble was run, no production scale-up was authorized, and no scientific closure criteria or physical-probability boundaries were changed.
- Next task: `TB-087`

### TB-087: Extract Persistent Conditional Hazard Confidence Regions

- Date: 2026-05-16
- Commit: `17bf806`
- Objective: derive deterministic conditional-hazard interpretive regions from the committed same-scale uncertainty evidence without authorizing new simulation output.
- Files changed: docs/task_backlog.md, docs/tschamut_public_conditional_pilot_gate_report.md, docs/tschamut_public_same_scale_uncertainty_envelope.md, scripts/summarize_spatial_same_scale_uncertainty.py, scripts/summarize_tschamut_conditional_diagnostic_interpretation.py, tests/test_spatial_same_scale_uncertainty.py, tests/test_tschamut_conditional_diagnostic_interpretation.py
- Implementation summary: added a conditional-hazard region summary on top of the existing spatial uncertainty report so the committed artifacts now name `persistent_agreement`, `stable_low_disagreement`, `shared_support_magnitude_sensitive`, and `support_nodata_sensitive` regions as interpretive aids; threaded that summary through the conditional diagnostic helper and text/JSON output so the measured regions are visible without changing closure status; extended the focused regression coverage to pin the new summary shape and report text; and updated the Tschamut narrative docs plus the active backlog to match the new region language.
- Checks run: `PYENV_VERSION=system uv run python -m unittest tests.test_spatial_same_scale_uncertainty tests.test_tschamut_conditional_diagnostic_interpretation`; `PYENV_VERSION=system uv run python -m py_compile scripts/summarize_spatial_same_scale_uncertainty.py scripts/summarize_tschamut_conditional_diagnostic_interpretation.py tests/test_spatial_same_scale_uncertainty.py tests/test_tschamut_conditional_diagnostic_interpretation.py`; `PYENV_VERSION=system uv run python scripts/summarize_spatial_same_scale_uncertainty.py --format json`; `PYENV_VERSION=system uv run python scripts/summarize_tschamut_conditional_diagnostic_interpretation.py --format json`
- Result/status: completed.
- Boundaries: no operational hazard zone, regulatory class, risk/exposure product, or new simulation output was created; the regions remain interpretive aids only.
- Next task: `TB-088`

### TB-088: Define Minimal Swiss Public-Geodata Workflow Contract

- Date: 2026-05-16
- Commit: `012f507`
- Objective: define a reusable public-geodata contract for any Swiss AOI so later preprocessing, release planning, and hazard generation can target one contract instead of inheriting Chant Sura or Tschamut assumptions.
- Files changed: docs/public_real_site_geodata_preparation.md, docs/swisstopo_data_strategy.md, docs/task_backlog.md, scripts/check_chant_sura_real_context_readiness_gate.py, scripts/check_second_site_public_geodata_preflight.py, scripts/plan_swisstopo_aoi_acquisition.py, tests/fixtures/second_site_public_geodata_preflight/minimal_synthetic_aoi.yaml, tests/test_chant_sura_real_context_readiness_gate.py, tests/test_second_site_public_geodata_preflight.py, tests/test_swisstopo_aoi_acquisition_planner.py, docs/agent_work_log.md
- Implementation summary: added a reusable `public_geodata_workflow_contract` summary to the second-site preflight, AOI acquisition planner, and Chant Sura real-context gate so the reports now name required AOI metadata, CRS/grid assumptions, swisstopo product classes, cache paths, provenance requirements, and deferred optional context; added a tiny synthetic AOI fixture and focused regressions covering both the Chant Sura example and the synthetic fixture to keep contract readiness separate from synthetic-fixture readiness; and updated the public real-site preparation and swisstopo strategy docs plus the active backlog to describe the new contract boundary explicitly.
- Checks run: `PYENV_VERSION=system uv run python -m unittest tests.test_second_site_public_geodata_preflight tests.test_swisstopo_aoi_acquisition_planner tests.test_chant_sura_real_context_readiness_gate -v`; `PYENV_VERSION=system uv run python -m py_compile scripts/check_second_site_public_geodata_preflight.py scripts/plan_swisstopo_aoi_acquisition.py scripts/check_chant_sura_real_context_readiness_gate.py tests/test_second_site_public_geodata_preflight.py tests/test_swisstopo_aoi_acquisition_planner.py tests/test_chant_sura_real_context_readiness_gate.py`; `git diff --check`; `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`; `scripts/git-hooks/pre-commit`; `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`; `git status --short`
- Result/status: completed.
- Boundaries: no public data was downloaded, no fake public-context evidence was staged, and no second-site hazard build or operational claim was introduced.
- Next task: `TB-089`

### TB-089: Add AOI-To-Prepared-Pilot Dry-Run Orchestrator

- Date: 2026-05-16
- Commit: `dfada3a`
- Objective: compose the existing AOI acquisition, public-context gate, release-zone dry run, release-plan dry run, and portable command-plan helpers into one deterministic Chant Sura workflow report.
- Files changed: scripts/plan_aoi_to_prepared_pilot_dry_run.py, tests/test_aoi_to_prepared_pilot_dry_run.py, docs/task_backlog.md, docs/agent_work_log.md
- Implementation summary: added a read-only orchestrator that loads the existing helper reports, orders the workflow steps, carries forward blockers and expected inputs, and aggregates generated versus ignored output roots; added regression coverage for both the staged-temp Chant Sura path and a stubbed composition path so the orchestrator stays pure and deterministic; and removed TB-089 from the active backlog once the workflow report was in place.
- Checks run: `PYENV_VERSION=system uv run python -m py_compile scripts/plan_aoi_to_prepared_pilot_dry_run.py tests/test_aoi_to_prepared_pilot_dry_run.py`; `PYENV_VERSION=system uv run python -m unittest tests.test_aoi_to_prepared_pilot_dry_run tests.test_swisstopo_aoi_acquisition_planner tests.test_release_zone_heuristic_dry_run tests.test_release_plan_dry_run tests.test_pilot_command_plan`; `PYENV_VERSION=system uv run python scripts/plan_aoi_to_prepared_pilot_dry_run.py --format json > /tmp/tb089_aoi_to_prepared_pilot_dry_run.json`; `git diff --check`; `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`; `scripts/git-hooks/pre-commit`; `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`; `git status --short`
- Result/status: completed.
- Boundaries: no data downloads, no ensemble runs, and no operational or probability claims were introduced; the real repo-root invocation still reports the candidate as blocked/deferred where core or public-context inputs are absent.
- Next task: `TB-090`

### TB-090: Generate Second-Site Conditional Case Skeleton

- Date: 2026-05-16
- Commit: `d45de1f`
- Objective: finalized the blocked Chant Sura / Fluelapass dry-run skeleton bookkeeping so the task is removed from the active backlog without authorizing execution.
- Files changed: `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Confirmed the existing dry-run skeleton helper emits a non-executable case draft into `/tmp` or the ignored validation/private path.
  - Verified the command plan exposes the skeleton step alongside the portability preflight and source/scenario audit.
  - Removed TB-090 from the active backlog after the skeleton contract was validated in dry-run mode.
- Checks run:
  - `PYENV_VERSION=system uv run --with pytest python -m pytest tests/test_chant_sura_fluelapass_dry_run_case_skeleton.py tests/test_pilot_command_plan.py tests/test_second_site_public_geodata_preflight.py tests/test_multisite_source_scenario_contract.py`
  - `PYENV_VERSION=system uv run python scripts/generate_chant_sura_fluelapass_dry_run_case_skeleton.py --site-config tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml --output-root /tmp/tb090_chant_sura_fluelapass_case_skeleton --format json`
  - `PYENV_VERSION=system uv run python scripts/generate_pilot_command_plan.py --site chant_sura_fluelapass --site-config tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml --format json`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
- Result/status: completed.
- Boundaries: no Chant Sura validation or hazard generation was run, and no public-context readiness or operational claim was added.
- Next task: backlog refill needed.

### TB-091: Define Balfrin Single-Release-Zone Pilot Contract

- Date: 2026-05-16
- Commit: `d71be8c`
- Objective: Freeze a measurable one-release-zone Balfrin pilot contract with native reduced output, conditional GIS products, and explicit non-operational boundaries.
- Files changed: `scripts/summarize_balfrin_single_release_zone_pilot_contract.py`, `validation/pilot_runs/tschamut_public_balfrin_single_release_zone_pilot_contract_v1.yaml`, `tests/test_balfrin_single_release_zone_pilot_contract.py`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary: added a read-only Balfrin contract helper that reports the frozen release-zone scope, trajectory target, validation output mode, expected artifact families, hazard-layer products, Balfrin resource assumptions, and no-go boundaries; added a committed machine-readable contract record for the next single-release-zone pilot; and covered both the ready contract and a missing-input contract with focused regressions and CLI smoke checks.
- Checks run: `PYENV_VERSION=system uv run python -m py_compile scripts/summarize_balfrin_single_release_zone_pilot_contract.py tests/test_balfrin_single_release_zone_pilot_contract.py`; `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_single_release_zone_pilot_contract -v`; `PYENV_VERSION=system uv run python scripts/summarize_balfrin_single_release_zone_pilot_contract.py --format json`; `PYENV_VERSION=system uv run python scripts/summarize_balfrin_single_release_zone_pilot_contract.py --format text`
- Result/status: completed.
- Boundaries: no new ensemble was run, no Swiss-wide rollout was authorized, and no annual, risk, exposure, vulnerability, operational, or physical-frequency claim was introduced.
- Next task: `TB-092`

### TB-092: Generate Large Single-Zone Tschamut Case Plan

- Date: 2026-05-16
- Commit: `ab39b62`
- Objective: add a deterministic dry-run case plan for the Balfrin single-release-zone pilot that records the frozen public source-zone/scenario inputs, validation output mode, and ignored output roots without authorizing execution.
- Files changed: `scripts/plan_balfrin_single_release_zone_case_dry_run.py`, `scripts/generate_pilot_command_plan.py`, `tests/test_balfrin_single_release_zone_case_plan_dry_run.py`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added a read-only Balfrin case-plan helper that loads the frozen source-zone metadata, scenario table, contract, policy, and rebuildable-reduced fixture and emits a deterministic dry-run report.
  - Recorded the exact ignored output roots, the rebuildable_reduced_output validation mode, the planned case output roots, and a blocked execution template so the report cannot be confused with an executed validation case.
  - Added portable command-plan integration and focused regression coverage for deterministic output, text rendering, and the new command-plan entry.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_single_release_zone_case_plan_dry_run tests.test_release_plan_dry_run tests.test_pilot_command_plan`
- Result/status: completed.
- Boundaries: no validation run, no physics tuning, no block-parameter tuning, no distributed execution, and no generated private cases were introduced.
- Next task: `TB-093`

### TB-093: Emit Balfrin Submission Package For The Pilot

- Date: 2026-05-16
- Commit: `fd36f53`
- Objective: extend the Balfrin probe driver so generate-only runs emit a reproducible submission package with the SBATCH script, command plan, package report, and collection instructions for the single-release-zone pilot.
- Files changed: scripts/submit_balfrin_probe.py, tests/test_balfrin_probe_driver.py, docs/balfrin_probe_slurm_driver.md, docs/task_backlog.md, docs/agent_work_log.md
- Implementation summary:
  - Extended `--generate-only` to write a package JSON and markdown companion alongside the existing command plan and SBATCH script.
  - Recorded the requested SLURM settings, repository branch/commit, readiness input checks, generated package roots, ignored Balfrin output roots, expected outputs, and collection commands in the package report.
  - Added focused tests for the package-report helper, generate-only no-submit behavior, and the generated script/package content, then smoke-tested the generate-only path against the selected Balfrin run-freeze manifest.
- Checks run:
  - `PYENV_VERSION=system uv run python -m py_compile scripts/submit_balfrin_probe.py tests/test_balfrin_probe_driver.py scripts/check_balfrin_tschamut_readiness.py scripts/collect_balfrin_probe_metrics.py scripts/validate_balfrin_tschamut_readiness_record.py`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_probe_driver -v`
  - `PYENV_VERSION=system uv run python scripts/submit_balfrin_probe.py validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml --generate-only --run-root /tmp/tb093_balfrin_package --partition postproc --time 00:30:00 --nodes 1 --ntasks 1 --cpus-per-task 16`
- Result/status: completed.
- Boundaries: no SLURM submission was made, no distributed/MPI execution was added, and the package report keeps the pilot framed as a research-diagnostic conditional workflow.
- Next task: `TB-094`

### TB-094: Capture Balfrin Pilot Metrics Contract

- Date: 2026-05-16
- Commit: `51cd741`
- Objective: define and test the Balfrin pilot metrics contract so completed runs can report the required runtime, memory, volume, family-count, conditional-curve, and restartability evidence or be reported as blocked.
- Files changed: `scripts/collect_balfrin_probe_metrics.py`, `scripts/summarize_balfrin_single_job_execution.py`, `docs/balfrin_single_job_execution_sufficiency.md`, `tests/test_balfrin_probe_driver.py`, `tests/test_balfrin_single_job_execution.py`, `tests/fixtures/balfrin_probe_metrics_contract/`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added a `metrics_contract` block to the Balfrin probe collector so complete run roots expose wall time, memory, validation output volume, hazard output volume, reduced-output family counts, conditional curve counts, and restartability metadata, while incomplete roots return a blocked status with missing metric names.
  - Added fixture-backed regression coverage for a complete synthetic run root and an incomplete run root, including log-audit coverage and contract-status assertions.
  - Updated the Balfrin single-job sufficiency summary and Markdown note to state which metrics are mandatory before claiming pilot feasibility.
- Checks run:
  - `PYENV_VERSION=system uv run python -m py_compile scripts/collect_balfrin_probe_metrics.py scripts/summarize_balfrin_single_job_execution.py tests/test_balfrin_probe_driver.py tests/test_balfrin_single_job_execution.py`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_probe_driver tests.test_balfrin_single_job_execution`
- Result/status: completed.
- Boundaries: no Balfrin job was run, no performance was inferred from missing artifacts, and no distributed-execution authorization was introduced.
- Next task: `TB-095`

### TB-095: Define Conditional Gridpoint Curve Pilot Product

- Date: 2026-05-16
- Commit: `ad7cc56`
- Objective: make the single-release-zone pilot's gridpoint conditional intensity-exceedance curve product explicit, auditable, and tied to GIS output layers.
- Files changed: scripts/build_hazard_layers.py, tests/test_hazard_layers.py, docs/hazard_layers.md, docs/tschamut_public_conditional_pilot_gate_report.md, docs/task_backlog.md, docs/agent_work_log.md
- Implementation summary:
  - Added an audit snapshot to the hazard-layer documentation that spells out the per-gridpoint curve schema, threshold units, denominator semantics, and the hazard-manifest GIS layer tie-out.
  - Expanded the Tschamut conditional pilot gate report with a focused product audit that points to the recorded curve contract, current threshold layers, and the existing non-annual/non-physical boundary.
  - Tightened the hazard-layer regression so the recorded curve contract is asserted alongside the manifest `cellwise_layers` mapping and the annual/physical flags remain false or unsupported.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_hazard_layers.HazardLayerTests.test_exceedance_layers_are_additive_and_manifested tests.test_hazard_layers.HazardLayerTests.test_conditional_curve_summary_only_suppresses_large_curve_table tests.test_hazard_layers.HazardLayerTests.test_map_package_metadata_rejects_annual_frequency_and_source_mismatch`
- Result/status: completed.
- Boundaries: no annual frequency, return-period, risk, exposure, vulnerability, physical-probability, or operational semantics were added.
- Next task: `TB-096`

### TB-096: Plan Terrain-Driven Release-Zone Candidate Generation

- Date: 2026-05-16
- Commit: `bb0bfff`
- Objective: produce a deterministic dry-run release-zone candidate contract from public terrain and context inputs while keeping candidate generation separate from validated release-zone evidence.
- Files changed: `scripts/plan_release_zone_heuristic_dry_run.py`, `tests/test_release_zone_heuristic_dry_run.py`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary: added a first-class release-zone candidate-generation contract covering terrain derivatives, slope/roughness/corridor screening inputs, context exclusions, output geometry schema, provenance requirements, and explicit evidence-boundary labels; kept the dry-run status tied to deferred public context rather than generating release zones; added focused regressions for the blocked Chant Sura public-context path and the tiny synthetic AOI fixture.
- Checks run: `PYENV_VERSION=system uv run python -m py_compile scripts/plan_release_zone_heuristic_dry_run.py tests/test_release_zone_heuristic_dry_run.py`; `PYENV_VERSION=system uv run python -m unittest tests.test_release_zone_heuristic_dry_run -v`
- Result/status: completed.
- Boundaries: no production release zones were generated, no thresholds were tuned against Tschamut outcomes, and no heuristic candidates were treated as physical evidence.
- Next task: `TB-097`

### TB-097: Plan Pragmatic Block-Scenario Generation

- Date: 2026-05-16
- Commit: `bebe942`
- Objective: define a deterministic block-scenario generation dry run that maps release-zone candidates to a small, pragmatic scenario table while keeping Tschamut-only heuristics separate from portable semantics.
- Files changed: `scripts/plan_release_plan_dry_run.py`, `tests/test_release_plan_dry_run.py`, `docs/public_real_site_geodata_preparation.md`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added a scenario-generation contract block to the release-plan dry run with portable semantics, explicit block-size bins, conditional sampling weights, release-cell linkage, required metadata, and unsupported physical-frequency fields.
  - Split the Tschamut-specific heuristics into a separate labeled section, wired deterministic release rows to policy release-cell ids, and added a blocked path for missing terrain or source-zone evidence.
  - Extended the focused regression coverage for the contract shape, the portable-versus-heuristic distinction, the blocked branch, and the text output rendering.
- Checks run:
  - `PYENV_VERSION=system uv run python -m py_compile scripts/plan_release_plan_dry_run.py tests/test_release_plan_dry_run.py`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_release_plan_dry_run tests.test_multisite_source_scenario_contract`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
- Result/status: completed.
- Boundaries: no annual source frequencies were estimated, no block distributions were calibrated, and no physics parameters or operational claims were changed.
- Next task: `TB-098`

### TB-098: Estimate Swiss-Wide Runtime And Storage Envelope

- Date: 2026-05-16
- Commit: `2247fc8`
- Objective: convert measured Tschamut/Balfrin runtime and output evidence into a conservative read-only runtime, storage, file-count, and job-count envelope for larger AOI/release-zone planning.
- Files changed: `scripts/estimate_swiss_wide_execution_envelope.py`, `tests/test_swiss_wide_execution_envelope.py`, `docs/balfrin_single_job_execution_sufficiency.md`, `docs/current_maturity_snapshot.md`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added `scripts/estimate_swiss_wide_execution_envelope.py`, anchored to the bounded reducer/runtime summary, Balfrin single-job sufficiency record, and bounded next-ensemble feasibility evidence.
  - Emitted low/nominal/high bands for runtime seconds, storage bytes, file counts, and job counts, with no-go labels when AOI, release-zone, trajectory, or job counts exceed measured support.
  - Added focused projection tests for small, valley-scale, Swiss-wide, and measured-loader cases, and documented the helper as a planning aid that does not authorize scale-up.
- Checks run:
  - `PYENV_VERSION=system uv run python -m py_compile scripts/estimate_swiss_wide_execution_envelope.py tests/test_swiss_wide_execution_envelope.py`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_swiss_wide_execution_envelope tests.test_bounded_reducer_runtime_scaling`
  - `PYENV_VERSION=system uv run python scripts/estimate_swiss_wide_execution_envelope.py --aoi-count 26 --release-zone-count 10 --trajectory-count 6 --format json`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
- Result/status: completed.
- Boundaries: no Swiss-wide execution was authorized, no jobs were submitted, and extrapolated multi-AOI requests remain labeled as no-go planning cases rather than operational or scale-up evidence.
- Next task: `TB-100`

### TB-099: Add Balfrin Post-Run Interpretation Gate

- Date: 2026-05-16
- Commit: `9587e8e`
- Objective: define the Balfrin single-release-zone post-run interpretation gate that decides whether a conditional diagnostic artifact is usable without expanding operational or physical-probability claims.
- Files changed: `scripts/summarize_balfrin_post_run_interpretation_gate.py`, `tests/test_balfrin_post_run_interpretation_gate.py`, `docs/balfrin_post_run_interpretation_gate.md`, `docs/balfrin_single_job_execution_sufficiency.md`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added a read-only Balfrin post-run gate helper that accepts a post-run evidence bundle and classifies the pilot as `measured_conditional_diagnostic`, `inconclusive_conditional_diagnostic`, or `blocked_missing_inputs`.
  - Kept the gate explicit about the required readiness, convergence/stability, output, GIS/COG, and physical-credibility checks, while separating conditional-diagnostic acceptance from the continued `False` operational and physical-probability boundaries.
  - Added focused regression coverage for measured, blocked, and inconclusive states plus JSON/text CLI smoke checks, and documented the acceptance boundary in a dedicated Balfrin gate note.
- Checks run:
  - `PYENV_VERSION=system uv run python -m py_compile scripts/summarize_balfrin_post_run_interpretation_gate.py tests/test_balfrin_post_run_interpretation_gate.py`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_post_run_interpretation_gate -v`
  - `PYENV_VERSION=system uv run python scripts/summarize_balfrin_post_run_interpretation_gate.py --format json --evidence-json /tmp/balfrin-post-run-XXXX.json`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
- Result/status: completed.
- Boundaries: no operational or physical-probability claims were authorized, no Balfrin run was executed here, and the gate remains a read-only conditional-diagnostic acceptance layer.
- Next task: `TB-100`

### TB-100: Refill Maturity Snapshot For The Balfrin Pilot Track

- Date: 2026-05-16
- Commit: `9cf3ba3`
- Objective: refresh the compact maturity snapshot and worker-context guidance so the Balfrin single-release-zone pilot track is the current execution focus.
- Files changed: `docs/current_maturity_snapshot.md`, `docs/task_backlog.md`, `scripts/print_agent_task_context.py`, `docs/agent_work_log.md`
- Implementation summary:
  - Reworded the maturity snapshot to separate completed dry-run automation from the remaining measured Balfrin execution gap.
  - Removed TB-100 from the active backlog once the snapshot reflected the Balfrin pilot track as the current execution focus.
  - Added a compact `current_execution_focus` line to the task-context helper so the empty active queue still points workers at the Balfrin pilot track.
- Checks run:
  - `PYENV_VERSION=system uv run python -m py_compile scripts/print_agent_task_context.py`
  - `PYENV_VERSION=system uv run python scripts/print_agent_task_context.py --format json`
  - `PYENV_VERSION=system uv run python -c 'import json; p=json.load(open("/tmp/tb100_task_context.json")); print(p["agent_task_context_status"]); print(p.get("backlog_refill_needed")); print(p.get("current_execution_focus")); print(len(p.get("active_tasks", [])))'`
  - `git diff --check`
- Result/status: completed.
- Boundaries: no simulations, scientific claims, or backlog protocol changes were introduced.
- Next task: backlog refill needed

### TB-101: Define Balfrin Minimal Demonstration Contract

- Date: 2026-05-16
- Commit: `8043643`
- Objective: define the smallest convincing Balfrin demonstration artifact with explicit inputs, commands, artifacts, evidence, visual products, success criteria, and non-goals.
- Files changed: `scripts/summarize_balfrin_single_release_zone_pilot_contract.py`, `validation/pilot_runs/tschamut_public_balfrin_single_release_zone_pilot_contract_v1.yaml`, `tests/test_balfrin_single_release_zone_pilot_contract.py`, `docs/balfrin_minimal_demo_vs_closure.md`, `docs/balfrin_tschamut_pilot_runbook.md`, `docs/task_backlog.md`
- Implementation summary:
  - Expanded the committed Balfrin contract into a minimal-demo contract section that is machine-readable and rendered as JSON/text, with explicit required inputs, commands, artifacts, evidence, visual products, success criteria, and non-goals.
  - Added scope-guard validation so the helper reports `ready`, `blocked_missing_inputs`, or `blocked_scope_creep` without authorizing scale-up, distributed execution, or physical-probability claims.
  - Added focused regression coverage for the ready, blocked-input, and scope-creep cases plus a short docs pointer that distinguishes minimal demo success from scientific closure.
- Checks run:
  - `PYENV_VERSION=system uv run python -m py_compile scripts/summarize_balfrin_single_release_zone_pilot_contract.py tests/test_balfrin_single_release_zone_pilot_contract.py`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_single_release_zone_pilot_contract tests.test_balfrin_single_release_zone_case_plan_dry_run -v`
  - `PYENV_VERSION=system uv run python scripts/summarize_balfrin_single_release_zone_pilot_contract.py --format json >/tmp/tb101_balfrin_contract.json`
  - `PYENV_VERSION=system uv run python scripts/summarize_balfrin_single_release_zone_pilot_contract.py --format text >/tmp/tb101_balfrin_contract.txt`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
- Result/status: completed.
- Boundaries: no Balfrin jobs were run, the contract stays non-operational, and no annual-frequency, risk, exposure, vulnerability, distributed-execution, scale-up, or physical-probability claims were authorized.
- Next task: `TB-102`

### TB-102: Execute And Collect The Balfrin Single-Release-Zone Pilot

- Date: 2026-05-16
- Commit: `9944204`
- Objective: attempt the first measured Balfrin single-release-zone pilot execution and, where execution was blocked, record the exact failure class with the minimal audited evidence needed for follow-up.
- Files changed: `docs/archive/balfrin_single_release_zone_execution_report.md`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added a compact blocked execution report that records the exact pre-execution failure class: the readiness checker rejects the selected Balfrin contract because its `schema_version` does not match the public real-site gate schema.
  - Removed TB-102 from the active backlog once the blocked-report path was committed, keeping the backlog consistent with the current executable state.
  - Preserved the non-operational boundary and made clear that no run root, measured metrics bundle, or generated hazard/validation outputs were produced.
- Checks run:
  - `PYENV_VERSION=system uv run python scripts/check_balfrin_tschamut_readiness.py validation/pilot_runs/tschamut_public_balfrin_single_release_zone_pilot_contract_v1.yaml --format both`
  - `PYENV_VERSION=system uv run python scripts/summarize_balfrin_single_release_zone_pilot_contract.py --format json`
  - `PYENV_VERSION=system uv run python scripts/plan_balfrin_single_release_zone_case_dry_run.py --format json`
  - `git commit -m "Record blocked Balfrin single-release-zone execution report"`
- Result/status: blocked.
- Boundaries: no Balfrin execution artifacts were generated or committed, and no operational, annual-frequency, risk, exposure, vulnerability, distributed-execution, or physical-probability claims were introduced.
- Next task: `TB-103`

### TB-103: Harden Balfrin Demonstration Runbook

- Date: 2026-05-16
- Commit: `c38bb1a`
- Objective: make the Balfrin demo execution procedure operationally reproducible with exact start, stop, resume, collect, verify, cleanup, and failure-handoff steps.
- Files changed: `docs/balfrin_tschamut_pilot_runbook.md`, `scripts/submit_balfrin_probe.py`, `tests/test_balfrin_probe_driver.py`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added a command-driven Balfrin runbook sequence with explicit preflight, generate-only, submit, stop, resume, collect, post-run gate, cleanup, and failure-handoff commands.
  - Extended the generated Balfrin submission package output with an operator sequence and exact do-not-commit roots/artifacts so the helper output now mirrors the runbook guidance.
  - Added regression coverage for the new helper output and removed TB-103 from the active backlog.
- Checks run:
  - `PYENV_VERSION=system uv run python -m py_compile scripts/submit_balfrin_probe.py scripts/collect_balfrin_probe_metrics.py scripts/summarize_balfrin_post_run_interpretation_gate.py tests/test_balfrin_probe_driver.py tests/test_balfrin_post_run_interpretation_gate.py`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_probe_driver tests.test_balfrin_post_run_interpretation_gate -v`
  - `PYENV_VERSION=system uv run python scripts/submit_balfrin_probe.py validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml --generate-only --run-root /tmp/tb103_balfrin_probe --run-id tb103_smoke --partition postproc --time 00:30:00 --nodes 1 --ntasks 1 --cpus-per-task 16`
- Result/status: completed.
- Boundaries: no Balfrin jobs were submitted, no claim boundaries were broadened, and no generated probe artifacts were committed.
- Next task: `TB-104`

### TB-104: Add Structured Worker Output Compression

- Date: 2026-05-16
- Commit: `e8fe035`
- Objective: Reduce autonomous worker/orchestrator output pressure by standardizing concise progress summaries, bounded command output, and final structured reports.
- Files changed: `AGENTS.md`, `docs/task_backlog.md`, `scripts/check_repo_consistency.py`, `scripts/print_agent_task_context.py`, `tests/test_agent_task_context.py`
- Implementation summary:
  - Added an explicit worker-output guidance block to the task-context helper with a compact progress style, `/tmp` redirection policy, bounded log/diff guidance, and a fixed final-report schema.
  - Surfaced the same compact-output contract in `AGENTS.md` and the backlog protocol so future worker prompts carry the same output-pressure guidance.
  - Added focused regression coverage for the JSON payload, rendered text output, and repository-consistency guard so the guidance cannot drift silently.
- Checks run:
  - `PYENV_VERSION=system uv run python -m py_compile scripts/print_agent_task_context.py scripts/check_repo_consistency.py tests/test_agent_task_context.py`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_agent_task_context -v`
  - `PYENV_VERSION=system uv run python scripts/print_agent_task_context.py --task TB-104 --format json >/tmp/tb104_task_context.json`
  - `PYENV_VERSION=system uv run python -c 'import json; p=json.load(open("/tmp/tb104_task_context.json")); print(p["worker_output_guidance"]["schema_version"]); print("|".join(p["worker_output_guidance"]["final_report_schema"])); print(p["worker_output_guidance"]["command_output_policy"][0])'`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
- Result/status: completed.
- Boundaries: no scientific helpers, output semantics, or branch/worktree workflows were changed; failure diagnostics remain visible through the preserved final error block guidance.
- Next task: `TB-105`

### TB-105: Build Canonical Balfrin Evidence Bundle

- Date: 2026-05-16
- Commit: `a316ece7a2da1994ca699dc431dfeb6c04e685fe`
- Objective: assemble the Balfrin readiness, metrics, outputs, GIS / COG status, restartability, and interpretation evidence into one canonical read-only bundle and report.
- Files changed: `scripts/summarize_balfrin_evidence_bundle.py`, `tests/test_balfrin_evidence_bundle.py`, `docs/balfrin_single_job_execution_sufficiency.md`, `docs/balfrin_post_run_interpretation_gate.md`, `docs/task_backlog.md`
- Implementation summary:
  - Added a read-only Balfrin evidence-bundle helper that can return a direct fixture bundle, assemble the current repo evidence into a canonical JSON / text pair, or return `blocked_missing_inputs` when required sections are absent.
  - Kept the claim-boundary contract explicit in the bundle output and text rendering so operational, probability, annual-frequency, risk/exposure/vulnerability, scale-up, and distributed-execution claims remain false.
  - Added focused regression coverage for complete, incomplete, blocked, and boundary-preserving bundle cases, plus artifact writing for the canonical bundle directory.
  - Documented the management-facing canonical bundle path in the Balfrin sufficiency and post-run gate docs and removed TB-105 from the active backlog.
- Checks run:
  - `PYENV_VERSION=system uv run python -m py_compile scripts/summarize_balfrin_evidence_bundle.py tests/test_balfrin_evidence_bundle.py`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_evidence_bundle -v`
  - `PYENV_VERSION=system uv run python scripts/summarize_balfrin_evidence_bundle.py --format json >/tmp/tb105_bundle_smoke.json`
  - `jq -r '.bundle_status, .post_run_interpretation_gate_report.interpretation_status, .gis_cog_readiness_report.gis_cog_readiness_status' /tmp/tb105_bundle_smoke.json`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
- Result/status: completed.
- Boundaries: the bundle remains read-only and preserves non-operational, non-probabilistic, non-scale-up, and distributed-execution boundaries; the live repo evidence currently resolves to an `incomplete` bundle rather than a stronger claim.
- Next task: `TB-106`

### TB-106: Demonstrate Balfrin Restartability Recovery

- Date: 2026-05-16
- Commit: `0095d4777ab2ffda5b4c11383b85018f429fbe89`
- Objective: Provide a fixture-backed Balfrin restartability recovery report that classifies a controlled partial-state resume without corrupting outputs or altering numerical artifacts.
- Files changed: `scripts/summarize_balfrin_restartability_recovery.py`, `tests/test_balfrin_restartability_recovery.py`, `tests/fixtures/balfrin_restartability_recovery/fixture_v1.json`, `docs/balfrin_restartability_recovery_report.md`, `docs/task_backlog.md`
- Implementation summary:
  - Added a read-only restartability recovery summarizer that classifies evidence as `measured`, `fixture_proven`, or `blocked_missing_inputs` and keeps explicit limits in the output.
  - Added a controlled partial-state fixture covering resume commands, reused and executed chunks, numerical stability, and artifact hygiene, plus a matching markdown report for repository review.
  - Added focused classification tests for fixture-backed, measured-override, blocked, and CLI artifact-writing paths.
  - Removed TB-106 from the active backlog once the implementation was committed.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest discover -s tests -p 'test_balfrin_*.py'`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
- Result/status: completed.
- Boundaries: fixture-backed recovery evidence only; no live interruption, distributed execution, physics, sampling, or output-profile claims were introduced.
- Next task: `TB-107`

### TB-107: Write Balfrin Demonstration Failure-Recovery Playbook

- Date: 2026-05-16
- Commit: `f2a9a64`
- Objective: Provide deterministic operator-facing recovery procedures for Balfrin demo failures across readiness, scheduler, partial-output, metrics, GIS/export, and interpretation states.
- Files changed: `docs/balfrin_tschamut_pilot_runbook.md`, `docs/balfrin_failure_recovery_playbook.md`, `tests/test_balfrin_failure_recovery_playbook.py`, `docs/task_backlog.md`
- Implementation summary:
  - Added a standalone Balfrin failure-recovery playbook with a small taxonomy table and command-specific recovery steps for readiness, scheduler, partial-output, metrics, GIS/export, and scientific-state failures.
  - Added a short runbook pointer so operators can reach the playbook from the existing Balfrin operational guidance without changing the execution boundary.
  - Added smoke tests that exercise the readiness, metrics, GIS/COG, and interpretation helper outputs the playbook depends on.
  - Removed TB-107 from the active backlog once the playbook was in place.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_failure_recovery_playbook -v`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
- Result/status: completed.
- Boundaries: no jobs were run or broadened, the playbook stays within the current Balfrin single-release-zone demo scope, and the helper contracts remain read-only.
- Next task: `TB-108`

### TB-108: Audit Post-Balfrin Output Tier Sufficiency

- Date: 2026-05-16
- Commit: `c7d573a`
- Objective: Determine whether the measured `rebuildable_reduced_output` tier is sufficient for the Balfrin demo and future bounded runs.
- Files changed: `scripts/summarize_balfrin_output_tier_audit.py`, `tests/test_balfrin_output_tier_audit.py`, `docs/current_maturity_snapshot.md`, `docs/task_backlog.md`
- Implementation summary:
  - Added a read-only Balfrin output-tier audit helper that classifies the measured tier as `sufficient`, `insufficient`, or `blocked_missing_measured_output` without introducing any new output mode.
  - The audit now reports required family counts, measured family counts, validation and hazard file/byte counts, conditional-curve availability, and omitted-output implications from the collected probe evidence.
  - Added focused tests for the complete measured case, a missing-family insufficient case, a missing-measured-output blocked case, and CLI artifact materialization.
  - Removed TB-108 from the active backlog and updated the maturity snapshot to reflect the new audit helper.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_output_tier_audit tests.test_balfrin_probe_driver.BalfrinProbeDriverTests.test_collect_probe_metrics_parses_synthetic_outputs tests.test_balfrin_probe_driver.BalfrinProbeDriverTests.test_collect_probe_metrics_reports_blocked_incomplete_root`
  - `PYENV_VERSION=system uv run python scripts/summarize_balfrin_output_tier_audit.py --run-root tests/fixtures/balfrin_probe_metrics_contract/complete_run_root --format text`
  - `PYENV_VERSION=system uv run python scripts/summarize_balfrin_output_tier_audit.py --run-root tests/fixtures/balfrin_probe_metrics_contract/complete_run_root --format json`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
- Result/status: completed.
- Boundaries: no new output modes were introduced, `summary_only` was not called rebuildable, and the audit keeps operational, scale-up, and physical-probability boundaries false.
- Next task: `TB-109`

### TB-109: Check Balfrin GIS/COG Demonstration Parity

- Date: 2026-05-16
- Commit: `c9f93d7`
- Objective: Emit a Balfrin GIS/COG parity report that makes package usability, COG readiness, curve linkage, manifest consistency, and any scope delta explicit.
- Files changed: `scripts/summarize_balfrin_evidence_bundle.py`, `tests/test_balfrin_evidence_bundle.py`, `docs/task_backlog.md`
- Implementation summary:
  - Added a dedicated Balfrin GIS/COG parity report to the evidence-bundle summarizer so the bundle now surfaces layer counts, COG metadata, curve linkage, manifest consistency, and scope-delta status in one machine-readable object.
  - Wired the parity report into the bundle text rendering and blocked-input path so the emitted report stays explicit when evidence is missing.
  - Added focused regression coverage for ready, blocked-missing-inputs, and bounded-scope package states using fixture-style evidence dictionaries rather than live GIS artifacts.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_evidence_bundle tests.test_gis_cog_package_readiness tests.test_same_scale_cog_package_conversion`
  - `PYENV_VERSION=system uv run python - <<'PY' ... bundle.build_bundle_report(...) ... PY` smoke emission to `/tmp/tb-109_parity_report.json`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
- Result/status: completed.
- Boundaries: the parity report stays read-only, does not commit generated rasters, does not require manual QGIS QA, and keeps operational, scale-up, and physical-probability claims false.
- Next task: `TB-110`

### TB-110: Audit Demo Claim Boundaries

- Date: 2026-05-16
- Commit: `419362f`
- Objective: Add a machine-check that the Balfrin demo helpers and demo-facing docs keep operational, annual-frequency, risk, exposure, vulnerability, physical-probability, scale-up, and distributed-execution claims explicitly out of scope.
- Files changed: `scripts/check_repo_consistency.py`, `tests/test_repo_consistency_claim_hygiene.py`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Extended the existing repository claim-hygiene audit so it now scans the Balfrin post-run gate helper, the Tschamut conditional diagnostic helper, the Balfrin post-run interpretation doc, the Balfrin minimal-demo boundary note, and the Tschamut public conditional pilot gate report.
  - Added explicit rejection of true claim-boundary flags so a future drift to `true` in demo-facing artifacts fails the audit instead of silently widening the boundary.
  - Added focused regression coverage for the current clean repository state and for synthetic demo text that tries to assert operational, annual-frequency, risk, and hazard-map claims.
  - Removed TB-110 from the active backlog after wiring the audit into the consistency checks.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_repo_consistency_claim_hygiene`
  - `PYENV_VERSION=system uv run python scripts/check_repo_consistency.py`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `git diff --check`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
- Result/status: completed.
- Boundaries: the audit only rejects overclaiming and false boundary flags; it does not change any scientific boundary, authorize operational use, or introduce new claim classes.
- Next task: `TB-111`

### TB-111: Compare Balfrin Results Against Same-Scale Uncertainty

- Date: 2026-05-16
- Commit: `3efed2a`
- Objective: Compare the measured Balfrin evidence against same-scale uncertainty, stability frontier, closure-gap deltas, and hotspot provenance without changing scientific boundaries.
- Files changed: `scripts/summarize_balfrin_scientific_delta_report.py`, `tests/test_balfrin_scientific_delta_report.py`, `docs/balfrin_minimal_demo_vs_closure.md`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added a read-only Balfrin scientific delta helper that composes the post-run gate with same-scale uncertainty, stability frontier, closure-gap, and hotspot provenance evidence.
  - The report now classifies measured, inconclusive, and blocked evidence states, and its JSON/text output keeps operational, probabilistic, annual-frequency, risk, exposure, vulnerability, scale-up, and distributed-execution boundaries false.
  - Added focused tests for measured, inconclusive, and missing-input override states plus a CLI JSON/text smoke path.
  - Removed TB-111 from the active backlog and added a doc reference to the new helper.
- Checks run:
  - `PYENV_VERSION=system uv run python -m py_compile scripts/summarize_balfrin_scientific_delta_report.py tests/test_balfrin_scientific_delta_report.py`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_scientific_delta_report tests.test_balfrin_post_run_interpretation_gate tests.test_same_scale_stability_frontier tests.test_tschamut_closure_gap_deltas tests.test_spatial_same_scale_uncertainty tests.test_tschamut_hotspot_provenance`
  - `git diff --check`
- Result/status: completed.
- Boundaries: the delta report compares evidence only; it does not reclassify Tschamut closure, tune physics, or claim physical validation.
- Next task: `TB-112`

### TB-112: Define Balfrin Operational Failure Taxonomy

- Date: 2026-05-16
- Commit: `a16f971`
- Objective: Formalize Balfrin run failure classes and recovery semantics for readiness, scheduler, runtime, partial-output, metrics, GIS/export, and scientific-state failures.
- Files changed: `scripts/summarize_balfrin_failure_taxonomy.py`, `scripts/summarize_balfrin_evidence_bundle.py`, `scripts/check_repo_consistency.py`, `docs/balfrin_tschamut_pilot_runbook.md`, `docs/balfrin_single_job_execution_sufficiency.md`, `docs/balfrin_failure_recovery_playbook.md`, `docs/task_backlog.md`, `tests/test_balfrin_failure_taxonomy.py`, `tests/test_balfrin_evidence_bundle.py`
- Implementation summary:
  - Added a read-only machine-readable Balfrin failure taxonomy helper with canonical classes, commands, recovery actions, and escalation boundaries for the operational and scientific failure states covered by the task.
  - Wired the taxonomy into the canonical Balfrin evidence bundle so the post-run bundle now carries a structured failure-taxonomy report alongside the existing readiness, metrics, GIS, and interpretation evidence.
  - Added focused regression coverage for catalog output plus representative readiness, scheduler, runtime, partial-output, metrics, GIS/export, and scientific-state classifications, and verified the bundle keeps scope-limited states distinct from real blockers.
  - Updated the Balfrin runbook and recovery playbook to point operators at the helper, and removed TB-112 from the active backlog.
- Checks run:
  - `PYENV_VERSION=system uv run python -m py_compile scripts/summarize_balfrin_failure_taxonomy.py scripts/summarize_balfrin_evidence_bundle.py scripts/check_repo_consistency.py tests/test_balfrin_failure_taxonomy.py tests/test_balfrin_evidence_bundle.py`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_failure_taxonomy tests.test_balfrin_evidence_bundle -v`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
- Result/status: completed.
- Boundaries: the taxonomy labels operational recovery cases and explicit scope limits only; it does not alter scientific interpretation criteria or authorize operational hazard claims.
- Next task: `TB-113`

### TB-113: Update Balfrin Runtime And Scaling Frontier

- Date: 2026-05-16
- Commit: `6252600`
- Objective: refine the Swiss-wide planning envelope with measured Balfrin runtime, storage, file-count, memory, and job-count evidence while preserving conservative no-go labeling and a blocked fallback when measurements are absent.
- Files changed: `scripts/estimate_swiss_wide_execution_envelope.py`, `tests/test_swiss_wide_execution_envelope.py`, `docs/task_backlog.md`, `docs/decision_log.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Extended the Swiss-wide envelope helper to carry a measured memory band alongside runtime, storage, file-count, and job-count projections.
  - Added an explicit blocked-report path for missing Balfrin evidence so the helper stays machine-readable instead of hard-failing when measurements are unavailable.
  - Corrected the Balfrin source command metadata and added regression coverage for measured support, extrapolated no-go labels, and blocked missing-evidence behavior.
  - Removed TB-113 from the active backlog and recorded the frontier-basis decision in the decision log.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_swiss_wide_execution_envelope -v`
  - `PYENV_VERSION=system uv run python scripts/estimate_swiss_wide_execution_envelope.py --format json`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
- Result/status: completed.
- Boundaries: the frontier stays read-only and conservative; it does not authorize Swiss-wide execution, distributed execution, or any operational hazard claim.
- Next task: `TB-114`

### TB-114: Prepare Second-Site Real-Context Acquisition Decision

- Date: 2026-05-16
- Commit: `355e698`
- Objective: decide whether the Chant Sura / Flüelapass public-context bundle should be staged next or explicitly deferred, and make the boundary explicit in a share-safe decision pack.
- Files changed: `docs/chant_sura_fluelapass_real_context_acquisition_decision.md`, `docs/public_real_site_geodata_preparation.md`, `docs/swisstopo_data_strategy.md`, `docs/decision_log.md`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary: added a dedicated decision pack that records the current defer recommendation, the required public-context products, the cache/output roots, the current blocked/deferred helper statuses, and exact commands to reproduce the boundary without downloading public context; linked that pack from the public real-site preparation and swisstopo strategy docs so the decision is easy to find; recorded the durable defer decision in the decision log; and removed TB-114 from the active backlog.
- Checks run: `PYENV_VERSION=system uv run python -m unittest tests.test_second_site_public_geodata_preflight tests.test_swisstopo_aoi_acquisition_planner tests.test_chant_sura_real_context_readiness_gate tests.test_aoi_to_prepared_pilot_dry_run`; `PYENV_VERSION=system uv run python scripts/plan_swisstopo_aoi_acquisition.py --site-config tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml --format json > /tmp/tb114_plan_swisstopo_aoi_acquisition.json`; `PYENV_VERSION=system uv run python scripts/check_second_site_public_geodata_preflight.py --site-config tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml --format json > /tmp/tb114_second_site_preflight.json`; `PYENV_VERSION=system uv run python scripts/check_chant_sura_real_context_readiness_gate.py --site-config tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml --format json > /tmp/tb114_real_context_gate.json`; `PYENV_VERSION=system uv run python scripts/plan_aoi_to_prepared_pilot_dry_run.py --site-config tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml --format json > /tmp/tb114_aoi_to_prepared_pilot.json`; `git diff --check`; `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`; `scripts/git-hooks/pre-commit`; `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`; `git status --short`
- Result/status: completed.
- Boundaries: no real swisstopo downloads were performed, no second-site ensemble was run, and synthetic fixtures were not treated as public-context evidence.
- Next task: backlog refill needed

### TB-115: Freeze Canonical Balfrin Demonstration Contract

- Date: 2026-05-17
- Commit: `cb7e1d2`
- Objective: freeze the canonical Balfrin minimal demonstration contract, teach the readiness helper to accept that contract schema, and keep the frozen demo path distinct from scientific closure.
- Files changed: `scripts/check_balfrin_tschamut_readiness.py`, `tests/test_balfrin_tschamut_readiness.py`, `docs/current_maturity_snapshot.md`, `docs/archive/balfrin_single_release_zone_execution_report.md`, `docs/task_backlog.md`
- Implementation summary:
  - Added a contract-aware Balfrin readiness branch that accepts the frozen `balfrin_single_release_zone_pilot_contract_v1` schema without weakening the existing non-operational boundary checks.
  - Kept the original conditional-pilot readiness path intact so existing same-scale readiness behavior remains available for that schema.
  - Added focused regression coverage proving the Balfrin contract schema now passes readiness, the frozen command sequence remains read-only, and minimal-demo success remains distinct from scientific closure.
  - Updated the maturity snapshot and the historical execution report to reflect that TB-115 resolved the schema mismatch blocker while preserving the original TB-102 failure record.
  - Removed TB-115 from the active backlog.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_tschamut_readiness tests.test_balfrin_single_release_zone_pilot_contract tests.test_balfrin_single_release_zone_case_plan_dry_run -v`
  - `PYENV_VERSION=system uv run python scripts/check_balfrin_tschamut_readiness.py validation/pilot_runs/tschamut_public_balfrin_single_release_zone_pilot_contract_v1.yaml --format json`
  - `PYENV_VERSION=system uv run python scripts/summarize_balfrin_single_release_zone_pilot_contract.py --format json`
  - `PYENV_VERSION=system uv run python scripts/plan_balfrin_single_release_zone_case_dry_run.py --format json`
  - `git diff --check`
- Result/status: completed.
- Boundaries: the contract remains a read-only demonstration artifact; no Balfrin job was run, readiness checks were not weakened, and no operational, distributed, scale-up, or physical-probability claims were introduced.
- Next task: `TB-116`

### TB-116 blocked report: Execute And Collect Balfrin Single-Release-Zone Demo

- Date: 2026-05-17
- Commit: `98f5c4c`
- Objective: run the canonical Balfrin single-release-zone demo end-to-end or classify the exact blocked execution state with measurable evidence.
- Files changed: `docs/archive/balfrin_single_release_zone_execution_report.md`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Verified the frozen Balfrin contract, the read-only dry-run plan, and the generated submission package path are all valid.
  - Attempted live submission against the public conditional pilot freeze and recorded the exact orchestration failure class: `scheduler_submission_failed` because `sbatch` is not installed or exposed on this node.
  - Collected the probe metrics summary from the generated scratch root and captured the missing live-run fields so the report stays machine-readable without pretending the run executed.
  - Added a blocked-execution addendum to the historical Balfrin execution report and left a minimal follow-up task to harden scheduler-block classification.
- Checks run:
  - `PYENV_VERSION=system uv run python scripts/check_balfrin_tschamut_readiness.py validation/pilot_runs/tschamut_public_balfrin_single_release_zone_pilot_contract_v1.yaml --format json`
  - `PYENV_VERSION=system uv run python scripts/summarize_balfrin_single_release_zone_pilot_contract.py --format json`
  - `PYENV_VERSION=system uv run python scripts/plan_balfrin_single_release_zone_case_dry_run.py --format json`
  - `PYENV_VERSION=system uv run python scripts/submit_balfrin_probe.py validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml --generate-only --run-root /private/tmp/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_single_release_zone_v1 --run-id tschamut_public_balfrin_single_release_zone_v1 --partition postproc --time 00:30:00 --nodes 1 --ntasks 1 --cpus-per-task 16`
  - `PYENV_VERSION=system uv run python scripts/submit_balfrin_probe.py validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml --submit --run-root /private/tmp/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_single_release_zone_v1 --run-id tschamut_public_balfrin_single_release_zone_v1 --partition postproc --time 00:30:00 --nodes 1 --ntasks 1 --cpus-per-task 16`
  - `PYENV_VERSION=system uv run python scripts/submit_balfrin_probe.py --collect --run-root /private/tmp/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_single_release_zone_v1`
  - `PYENV_VERSION=system uv run python scripts/collect_balfrin_probe_metrics.py --run-root /private/tmp/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_single_release_zone_v1 --output-json /tmp/balfrin_probe_metrics.json`
- Result/status: implemented_blocked_report.
- Boundaries: no measured Balfrin run root was produced, no scheduler job started, and no operational, annual-frequency, physical-probability, risk, exposure, vulnerability, or distributed-execution claim was introduced.
- Next task: `TB-128`

### TB-116: Harden Balfrin Scheduler-Block Classification

- Date: 2026-05-17
- Commit: `8a4b589c474990f06ceb33cf28f681646f8e3d19`
- Objective: Make the Balfrin submit helper return a structured
  `scheduler_submission_failed` report when `sbatch` is missing so the demo
  path fails cleanly instead of surfacing an unclassified traceback.
- Files changed: `scripts/submit_balfrin_probe.py`, `scripts/summarize_balfrin_failure_taxonomy.py`, `tests/test_balfrin_probe_driver.py`, `tests/test_balfrin_failure_taxonomy.py`, `docs/balfrin_failure_recovery_playbook.md`, `docs/task_backlog.md`
- Implementation summary:
  - Added a guarded submit branch that writes `balfrin_submission_report.json`
    and prints the same JSON when `sbatch` is unavailable or unreachable.
  - Classified the new scheduler failure status in the Balfrin failure
    taxonomy so downstream summaries treat it as an observed operational block.
  - Added focused regression coverage for the missing-`sbatch` path and for
    taxonomy classification of `scheduler_submission_failed`.
  - Updated the recovery playbook to point operators at the structured report
    file and removed TB-116 from the active backlog.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_probe_driver tests.test_balfrin_failure_taxonomy`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
- Result/status: implemented_blocked_report
- Boundaries: this records an operational scheduler classification only; it
  does not claim a measured Balfrin run, operational hazard readiness,
  distributed execution, annual frequency, physical probability, risk,
  exposure, or vulnerability.
- Next task: `TB-117`

### TB-117 blocked report: Execute And Collect Balfrin Single-Release-Zone Demo

- Date: 2026-05-17
- Commit: `c0bfe612d5593eb22497994f5aa9670fc073e78e`
- Objective: run the canonical Balfrin single-release-zone demo end-to-end or
  classify the exact blocked execution state with measurable evidence.
- Files changed: `docs/archive/balfrin_single_release_zone_execution_report.md`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Verified the frozen Balfrin contract and the read-only dry-run planner, then
    attempted the canonical submit path against the scheduler-enabled manifest
    flow.
  - Recorded the exact operational failure class when `sbatch` was not exposed
    on this node: `scheduler_submission_failed`.
  - Collected the metrics summary from the generated scratch root so the report
    stays machine-readable without pretending a live run executed.
  - Added a blocked-execution addendum to the historical Balfrin execution
    report and left a minimal scheduler-access unblock task in the backlog.
- Checks run:
  - `PYENV_VERSION=system uv run python scripts/check_balfrin_tschamut_readiness.py validation/pilot_runs/tschamut_public_balfrin_single_release_zone_pilot_contract_v1.yaml --format json`
  - `PYENV_VERSION=system uv run python scripts/submit_balfrin_probe.py validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml --generate-only --run-root /private/tmp/balfrin_tb117_probe_gate --run-id tschamut_public_balfrin_single_release_zone_v1 --partition postproc --time 00:30:00 --nodes 1 --ntasks 1 --cpus-per-task 16`
  - `PYENV_VERSION=system uv run python scripts/submit_balfrin_probe.py validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml --submit --run-root /private/tmp/balfrin_tb117_probe_gate --run-id tschamut_public_balfrin_single_release_zone_v1 --partition postproc --time 00:30:00 --nodes 1 --ntasks 1 --cpus-per-task 16`
  - `PYENV_VERSION=system uv run python scripts/collect_balfrin_probe_metrics.py --run-root /private/tmp/balfrin_tb117_probe_gate --output-json /tmp/balfrin_tb117_probe_gate_metrics.json`
- Result/status: implemented_blocked_report
- Boundaries: no measured Balfrin run root was produced, no scheduler job
  started, and no operational, annual-frequency, physical-probability, risk,
  exposure, vulnerability, or distributed-execution claim was introduced.
- Next task: `TB-129`

### TB-117 scheduler access report: Restore Balfrin Scheduler Access For Demo Submission

- Date: 2026-05-17
- Commit: `1ecc28c1215b60371fa6ec3f8272ce377d104cec`
- Objective: document whether the canonical Balfrin demo path can reach `sbatch`
  and preserve a retryable submission note that keeps the same run root and run
  id.
- Files changed: `docs/balfrin_failure_recovery_playbook.md`, `docs/balfrin_tschamut_pilot_runbook.md`, `scripts/submit_balfrin_probe.py`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Verified by SSH that `balfrin` reaches a login node exposing `/usr/bin/sbatch`.
  - Recorded the Balfrin SSH entry point as the retry path in the failure
    recovery playbook and the operational runbook, keeping `RUN_ROOT` and
    `RUN_ID` unchanged across retries.
  - Updated the submit helper's recovery text so the machine-readable failure
    report points operators at the Balfrin SSH context instead of only saying to
    retry later.
  - Removed TB-117 from the active backlog after documenting the scheduler
    access path.
- Checks run:
  - `ssh -o BatchMode=yes -o ConnectTimeout=8 balfrin 'hostname; command -v sbatch || true; pwd'`
  - `PYENV_VERSION=system uv run python scripts/submit_balfrin_probe.py validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml --generate-only --run-root /tmp/balfrin-tb117-check --run-id tschamut_public_balfrin_single_release_zone_v1 --partition postproc --time 00:30:00 --nodes 1 --ntasks 1 --cpus-per-task 16`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
- Result/status: implemented_blocked_report
- Boundaries: this documents scheduler access and a retry path only; it does not
  claim a measured Balfrin demo run, operational hazard readiness, annual
  frequency, physical probability, risk, exposure, vulnerability, or
  distributed execution.
- Next task: `TB-118`

### TB-118 blocked report: Execute And Collect Balfrin Single-Release-Zone Demo

- Date: 2026-05-17
- Commit: `2b189c4e03282c04a76fc43f4aef8d88a64083c8`
- Objective: run the canonical Balfrin single-release-zone demo end-to-end or
  classify the exact blocked execution state with measurable evidence.
- Files changed: `docs/archive/balfrin_single_release_zone_execution_report.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Verified Balfrin readiness on the remote checkout, generated the frozen
    submission package, and submitted the single-node SLURM job to `postproc`.
  - Watched the live run reach `Compiling rust_rockfall v0.6.1` on `nid001226`
    before the earlier worker self-canceled it in an orchestration error after
    `00:08:09` of runtime; that was not a real Balfrin stall.
  - Collected the partial metrics summary from the same run root, which records
    partial output evidence but still reports
    `metrics_contract_status: blocked_missing_inputs`.
  - Captured the post-run interpretation gate in blocked mode so the closure
    boundary stays explicit and no operational claim is implied.
- Checks run:
  - `ssh balfrin 'cd /users/olifu/work/rust_rockfall && PYENV_VERSION=system uv run python scripts/check_balfrin_tschamut_readiness.py validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml --format json'`
  - `ssh balfrin 'cd /users/olifu/work/rust_rockfall && PYENV_VERSION=system uv run python scripts/submit_balfrin_probe.py validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml --generate-only --run-root /scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_single_release_zone_v1 --run-id tschamut_public_balfrin_single_release_zone_v1 --partition postproc --time 00:30:00 --nodes 1 --ntasks 1 --cpus-per-task 16'`
  - `ssh balfrin 'cd /users/olifu/work/rust_rockfall && PYENV_VERSION=system uv run python scripts/submit_balfrin_probe.py validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml --submit --run-root /scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_single_release_zone_v1 --run-id tschamut_public_balfrin_single_release_zone_v1 --partition postproc --time 00:30:00 --nodes 1 --ntasks 1 --cpus-per-task 16'`
  - `ssh balfrin 'squeue -j 4325958 -o "%.18i %.9T %.50R" || true'`
  - `ssh balfrin 'sacct -j 4325958 --format=JobID,State,Elapsed,TotalCPU,MaxRSS,ExitCode -P || true'`
  - `ssh balfrin 'cd /users/olifu/work/rust_rockfall && PYENV_VERSION=system uv run python scripts/collect_balfrin_probe_metrics.py --run-root /scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_single_release_zone_v1 --output-json /tmp/balfrin_tb118_collect_metrics.json'`
  - `ssh balfrin 'cd /users/olifu/work/rust_rockfall && PYENV_VERSION=system uv run python scripts/summarize_balfrin_post_run_interpretation_gate.py --format json'`
- Result/status: implemented_blocked_report
- Boundaries: the live Balfrin attempt produced partial output evidence only;
  it did not produce a measured run root, full metrics bundle, operational
  hazard readiness, annual frequency, physical probability, risk, exposure,
  vulnerability, or distributed-execution claim.
- Next task: `TB-118`

### TB-118 measured run: Execute And Collect Balfrin Single-Release-Zone Demo

- Date: 2026-05-17
- Commit: `489c209ca1dc4bb1f621783668c9fe87ccd651dc`
- Objective: run the canonical Balfrin single-release-zone demo end-to-end and
  collect measured evidence from the live Balfrin scratch root.
- Files changed: `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Submitted the frozen Balfrin single-release-zone probe to Balfrin using
    the canonical conditional pilot gate manifest and a fresh scratch root:
    `/scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_single_release_zone_v3`.
  - Confirmed the SLURM job completed successfully on `nid001226` with exit
    code `0`, and the run produced hazard-layer GeoTIFFs, ASCII grids, map
    package manifests, and GIS package manifests under the measured output
    roots.
  - Collected the run metrics summary from the live scratch root; the summary
    records `total_wall_seconds`, conditional-curve rows, reduced-output family
    counts, output bytes, and restartability evidence, while the collector still
    leaves some ancillary fields such as memory peak and split validation/hazard
    file counts unset.
  - Rendered a post-run interpretation summary from measured artifacts so the
    closure boundary remains explicit: the diagnostic artifact is usable, while
    operational, annual-frequency, physical-probability, risk, exposure, and
    vulnerability claims remain out of scope.
- Checks run:
  - `ssh -o BatchMode=yes -o ConnectTimeout=10 balfrin 'cd /users/olifu/work/rust_rockfall && PYENV_VERSION=system uv run python scripts/check_balfrin_tschamut_readiness.py validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml --format json'`
  - `ssh -o BatchMode=yes -o ConnectTimeout=10 balfrin 'cd /users/olifu/work/rust_rockfall && PYENV_VERSION=system uv run python scripts/submit_balfrin_probe.py validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml --submit --run-root /scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_single_release_zone_v3 --run-id tschamut_public_balfrin_single_release_zone_v3 --partition postproc --time 01:00:00 --nodes 1 --ntasks 1 --cpus-per-task 16'`
  - `ssh -o BatchMode=yes -o ConnectTimeout=10 balfrin 'squeue -h -j 4326021 -o "%.18i %.9T %.50R"'`
  - `ssh -o BatchMode=yes -o ConnectTimeout=10 balfrin 'sacct -j 4326021 --format=JobID,JobName%20,State,ExitCode,Elapsed,AllocCPUS,MaxRSS,NodeList -P -n'`
  - `ssh -o BatchMode=yes -o ConnectTimeout=10 balfrin 'cd /users/olifu/work/rust_rockfall && PYENV_VERSION=system uv run python scripts/submit_balfrin_probe.py --collect --run-root /scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_single_release_zone_v3'`
  - `ssh -o BatchMode=yes -o ConnectTimeout=10 balfrin 'cd /users/olifu/work/rust_rockfall && PYENV_VERSION=system uv run python scripts/collect_balfrin_probe_metrics.py --run-root /scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_single_release_zone_v3 --output-json /tmp/balfrin_tb118_collect_metrics.json'`
  - `ssh -o BatchMode=yes -o ConnectTimeout=10 balfrin 'sed -n "1,260p" /scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_single_release_zone_v3/balfrin_probe_summary.json'`
  - `PYENV_VERSION=system uv run python scripts/summarize_balfrin_post_run_interpretation_gate.py --format json --evidence-json /tmp/balfrin_tb118_post_run_evidence.json`
- Result/status: implemented_measured
- Boundaries: this records a live Balfrin diagnostic run only; it does not
  claim operational readiness, annual frequency, physical probability, risk,
  exposure, vulnerability, scale-up, or distributed execution.
- Next task: `TB-119`

### TB-119 measured bundle: Build Canonical Balfrin Demonstration Evidence Bundle

- Date: 2026-05-17
- Commit: `pending`
- Objective: convert the measured Balfrin evidence set into one canonical
  bundle with explicit measured, fixture-backed, and blocked section
  provenance.
- Files changed: `scripts/summarize_balfrin_evidence_bundle.py`,
  `tests/test_balfrin_evidence_bundle.py`,
  `docs/balfrin_post_run_interpretation_gate.md`,
  `docs/balfrin_single_job_execution_sufficiency.md`,
  `docs/task_backlog.md`,
  `docs/agent_work_log.md`
- Implementation summary:
  - Reworked the Balfrin evidence-bundle helper so the canonical report now
    exposes `bundle_provenance_status`, section provenance profiles, and
    measured / fixture-backed / blocked section counts.
  - Kept the live Balfrin path measured while preserving the existing
    conditional-diagnostic boundaries from the post-run gate and failure
    taxonomy helpers.
  - Added focused tests that exercise the measured live report, an explicit
    fixture-backed override, and the blocked path so the bundle stays honest
    about evidence provenance.
  - Updated the Balfrin gate and sufficiency docs to point at the canonical
    bundle helper and call out the new provenance split.
- Checks run:
  - `PYENV_VERSION=system uv run python scripts/summarize_balfrin_evidence_bundle.py --artifact-dir /tmp/balfrin_bundle_check --format json`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_evidence_bundle`
- Result/status: implemented_measured
- Boundaries: this records the measured Balfrin evidence bundle only; it does
  not widen operational, annual-frequency, physical-probability, risk,
  exposure, vulnerability, scale-up, or distributed-execution claims.
- Next task: `TB-120`

### TB-120 blocked provenance: Classify Balfrin restartability and output-tier evidence by source

- Date: 2026-05-17
- Commit: `pending`
- Objective: make the Balfrin output-tier audit and restartability notes
  explicitly distinguish measured run-root evidence from fixture-backed
  contract evidence, then remove the TB-120 backlog entry without claiming a
  live interruption/recovery proof that was not performed.
- Files changed: `scripts/summarize_balfrin_output_tier_audit.py`,
  `tests/test_balfrin_output_tier_audit.py`,
  `docs/balfrin_restartability_recovery_report.md`,
  `docs/current_maturity_snapshot.md`,
  `docs/task_backlog.md`,
  `docs/agent_work_log.md`
- Implementation summary:
  - Reworked the Balfrin output-tier audit helper so it now classifies
    evidence provenance as `measured`, `fixture_backed`, or
    `blocked_missing_inputs`, using the collected source paths rather than
    assuming every complete metrics payload is a live measurement.
  - Kept the rebuildability classification and required-family checks intact so
    the fixture-backed contract remains sufficient while no longer being
    mislabeled as live output evidence.
  - Updated the focused regression tests to pin both the fixture-backed and
    measured provenance paths, plus the blocked path, so downstream callers
    can distinguish live run-root evidence from fixture evidence.
  - Clarified the restartability recovery note and maturity snapshot so they
    state plainly that the current recovery artifact is fixture-backed and
    that a live interruption/resume proof still does not exist in this
    checkout.
  - Removed TB-120 from the active backlog after the provenance boundary was
    made explicit.
- Checks run:
  - `PYENV_VERSION=system uv run python scripts/summarize_balfrin_output_tier_audit.py --run-root tests/fixtures/balfrin_probe_metrics_contract/complete_run_root --format json`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_output_tier_audit`
- Result/status: implemented_blocked_report
- Boundaries: no live interruption or recovery job was created, no artificial
  interruption evidence was fabricated, and no operational, annual-frequency,
  physical-probability, risk, exposure, vulnerability, scale-up, or
  distributed-execution claim was introduced.

### TB-121: Generate Canonical Balfrin Conditional Diagnostic Interpretation

- Date: 2026-05-17
- Commit: `6682682`
- Objective: Produce one coherent measured Balfrin interpretation that combines uncertainty, convergence, scaling, GIS readiness, portability, closure semantics, and physical-credibility boundaries.
- Files changed: `scripts/summarize_balfrin_scientific_delta_report.py`, `tests/test_balfrin_scientific_delta_report.py`, `docs/task_backlog.md`
- Implementation summary:
  - Added a canonical interpretation layer to the Balfrin scientific delta helper with an explicit support/weakens/unchanged delta classification.
  - Exposed machine-readable blocker fields for closure-limiting layers, GIS/product scope, runtime/output sufficiency, portability, and physical-credibility limits.
  - Added artifact-dir materialization for the canonical JSON/text interpretation bundle and covered it with focused tests.
- Checks run: `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_scientific_delta_report`; `git diff --check`; `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`; `scripts/git-hooks/pre-commit`; `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
- Result/status: completed
- Boundaries: no physics tuning, acceptance-threshold changes, operational claims, or physical validation claims were introduced.
- Next task: `TB-122`

### TB-122: Resolve Balfrin GIS/COG Demonstration Scope Delta

- Date: 2026-05-17
- Commit: `86fa8cc`
- Objective: make the Balfrin demonstration GIS package unambiguous by exposing a top-level machine-readable COG scope classification in the measured evidence bundle while keeping the full-scope, scope-delta, and blocked-missing-package states explicit.
- Files changed: `scripts/summarize_balfrin_evidence_bundle.py`, `tests/test_balfrin_evidence_bundle.py`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added a top-level `gis_cog_scope_report` to the Balfrin evidence bundle so downstream consumers can read `full_scope`, `bounded_scope`, or `blocked_missing_inputs` directly instead of inferring package scope from nested parity metadata.
  - Kept the nested GIS/COG parity report intact and carried its missing-layer semantics through the new scope report so bounded-scope evidence still names the omitted layers explicitly.
  - Extended the focused Balfrin evidence-bundle tests to cover the full-scope measured report, the intentional scope-delta case, and the blocked-missing-inputs case.
  - Removed TB-122 from the active backlog after the evidence bundle made the demonstration scope classification explicit.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_evidence_bundle tests.test_gis_cog_package_readiness tests.test_same_scale_cog_package_conversion`
- Result/status: completed
- Boundaries: this records package-scope classification only; it does not commit generated rasters, require manual QGIS QA, or convert GIS readiness into operational approval.
- Next task: `TB-123`

### TB-123: Generate Balfrin Terrain-Driven Release-Zone Candidate Metrics

- Date: 2026-05-17
- Commit: `0306acc`
- Objective: Produce deterministic terrain-driven release-zone candidate metrics for the Balfrin/Tschamut AOI without using them as field-validated release zones.
- Files changed: `scripts/plan_terrain_release_zone_candidates.py`, `scripts/generate_pilot_command_plan.py`, `tests/test_plan_terrain_release_zone_candidates.py`, `tests/test_pilot_command_plan.py`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added a read-only terrain candidate-metrics helper that screens the committed Tschamut public pilot DEM with a fixed Horn 3x3 slope kernel and a fixed slope band, excludes the frozen source-zone footprint from candidate screening, and reports deterministic candidate counts, areas, excluded areas, and provenance.
  - Kept the report boundary explicit: the helper emits heuristic workflow inputs only and does not validate release zones, tune thresholds to outcomes, or claim physical release probability.
  - Added focused regressions for deterministic output on the committed inputs and blocked behavior when the public inputs are absent, and exposed the helper through the Balfrin single-release-zone command plan.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_plan_terrain_release_zone_candidates tests.test_pilot_command_plan`
  - `PYENV_VERSION=system uv run python scripts/plan_terrain_release_zone_candidates.py --format json > /tmp/tb123_candidate_metrics.json`
  - `PYENV_VERSION=system uv run python -m py_compile scripts/plan_terrain_release_zone_candidates.py scripts/generate_pilot_command_plan.py tests/test_plan_terrain_release_zone_candidates.py tests/test_pilot_command_plan.py`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \\( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \\) -print`
- Result/status: completed
- Boundaries: no release-zone replacement, threshold tuning, or physical release-probability claims were introduced.
- Next task: `TB-124`

### TB-124: Generate Deterministic Balfrin Block-Scenario Sensitivity Plan

- Date: 2026-05-17
- Commit: `cf1cffe`
- Objective: produce a deterministic Balfrin block-scenario sensitivity plan that keeps pragmatic block-size coverage separate from physical frequency claims.
- Files changed: `scripts/plan_pragmatic_release_plan.py`, `tests/test_plan_pragmatic_release_plan.py`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added a read-only Balfrin block-scenario sensitivity planner that reads the frozen Tschamut source-policy record and committed scenario table, then emits deterministic block-size bins, weighting semantics, reference-table provenance, and explicit non-frequency labels.
  - Kept the report boundary explicit: sampling weights are identified as conditional coverage weights, the frozen scenario table is treated as a reference record, and the same-scale uncertainty note is linked as a non-operational reference only.
  - Added focused regressions for deterministic generation from the committed inputs, blocked behavior when frozen inputs are missing, and stable text rendering.
  - Removed TB-124 from the active backlog after the plan helper and tests were added.
- Checks run:
  - `PYENV_VERSION=system uv run python -m py_compile scripts/plan_pragmatic_release_plan.py tests/test_plan_pragmatic_release_plan.py`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_plan_pragmatic_release_plan -v`
- Result/status: completed
- Boundaries: no block-size distributions were fit, no annual frequencies or physical probabilities were inferred, and the already measured Balfrin demo was not changed.
- Next task: `TB-125`

### TB-125: Prototype AOI-To-Demonstration Preparation Path

- Date: 2026-05-17
- Commit: `82a1fbc`
- Objective: Prepare a deterministic AOI-to-demonstration scaffold that emits terrain manifests, context manifests, release/scenario placeholders, command-plan hooks, and ignored output roots without running an ensemble.
- Files changed: `scripts/plan_aoi_to_prepared_pilot_dry_run.py`, `scripts/generate_pilot_command_plan.py`, `tests/test_aoi_to_prepared_pilot_dry_run.py`, `tests/test_pilot_command_plan.py`, `docs/public_real_site_geodata_preparation.md`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Extended the AOI dry-run planner into a preparation scaffold with explicit preparation-input metadata, terrain and context manifest sections, release/scenario placeholders, command-plan hooks, and ignored output roots.
  - Added release-polygon parsing and deterministic synthetic config/manifest handling so the same report shape remains available for AOI extents, release-polygon overrides, and blocked missing-input cases.
  - Exposed the new preparation helper in the portable command plan and updated the focused tests to cover deterministic output and blocked/missing-input behavior.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_aoi_to_prepared_pilot_dry_run tests.test_pilot_command_plan -v`
  - `PYENV_VERSION=system uv run python -m py_compile scripts/plan_aoi_to_prepared_pilot_dry_run.py scripts/generate_pilot_command_plan.py tests/test_aoi_to_prepared_pilot_dry_run.py tests/test_pilot_command_plan.py`
  - `PYENV_VERSION=system uv run python scripts/plan_aoi_to_prepared_pilot_dry_run.py --format json`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \\( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \\) -print`
- Result/status: completed
- Boundaries: no ensembles were run, no public context was downloaded, and no release-zone validity or operational claim was inferred from the dry-run scaffold.
- Next task: `TB-126`

### TB-126: Define Second-Site Real-Context Trigger From Balfrin Evidence

- Date: 2026-05-17
- Commit: `8fc3afb`
- Objective: convert the Chant Sura / Fluelapass defer decision into a measurable Balfrin-driven trigger for second-site public-context staging.
- Files changed: `scripts/check_chant_sura_real_context_readiness_gate.py`, `tests/test_chant_sura_real_context_readiness_gate.py`, `docs/chant_sura_fluelapass_real_context_acquisition_decision.md`, `docs/public_real_site_geodata_preparation.md`, `docs/swisstopo_data_strategy.md`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added a Balfrin trigger matrix to the Chant Sura real-context readiness gate so SWISSIMAGE, swissTLM3D, swissSURFACE3D, swissSURFACE3D Raster, and swissBUILDINGS3D all share the same measured proceed/defer/blocked logic.
  - Wired the gate to an optional Balfrin evidence snapshot and surfaced the trigger summary in both JSON and text output, keeping the current defer boundary explicit while allowing a measured post-run bundle to flip the staging decision.
  - Updated the Chant Sura decision pack and the broader public-real-site docs to name the measured trigger conditions, and added focused regressions for proceed, defer, and blocked trigger states.
  - Removed TB-126 from the active backlog after the trigger matrix was encoded.
- Checks run:
  - `PYENV_VERSION=system uv run python -m py_compile scripts/check_chant_sura_real_context_readiness_gate.py tests/test_chant_sura_real_context_readiness_gate.py`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_chant_sura_real_context_readiness_gate -v`
  - `PYENV_VERSION=system uv run python scripts/check_chant_sura_real_context_readiness_gate.py --balfrin-evidence-json validation/private/tschamut_public_pilot/balfrin_evidence_bundle_v1/balfrin_evidence_bundle_v1.json --format json`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_swisstopo_aoi_acquisition_planner tests.test_aoi_to_prepared_pilot_dry_run -v`
  - `git diff --check`
- Result/status: completed
- Boundaries: no real public context was downloaded, no second-site ensemble was run, and the existing defer decision remains in force until measured Balfrin evidence satisfies the proceed trigger.
- Next task: `TB-127`

### TB-127: Measure Practical Balfrin Ensemble Frontier

- Date: 2026-05-17
- Commit: `56d1730`
- Objective: summarize the practical Balfrin next-ensemble frontier from the measured Balfrin evidence chain without authorizing scale-up.
- Files changed: `scripts/summarize_balfrin_ensemble_frontier.py`, `tests/test_balfrin_ensemble_frontier.py`, `docs/task_backlog.md`
- Implementation summary:
  - Added a read-only Balfrin frontier helper that composes the scientific delta, single-job sufficiency, bounded next-ensemble feasibility, and same-scale stability evidence into one bounded report.
  - Classified the current frontier as `defer_small_bounded_ensemble` when the measured evidence still shows useful uncertainty spread, the single-job path remains sufficient, and the bounded reduced-output probe stays inside the measured envelope.
  - Preserved a blocked helper-contract path for missing measured Balfrin evidence and covered both the measured and blocked cases with focused regression tests.
  - Removed TB-127 from the active backlog after the helper and tests were in place.
- Checks run:
  - `PYENV_VERSION=system uv run python -m py_compile scripts/summarize_balfrin_ensemble_frontier.py tests/test_balfrin_ensemble_frontier.py`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_ensemble_frontier`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_ensemble_frontier tests.test_balfrin_scientific_delta_report tests.test_balfrin_single_job_execution tests.test_bounded_next_ensemble_feasibility_probe tests.test_same_scale_stability_frontier`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
- Result/status: completed
- Boundaries: no production ensemble was run, no physics or scale-up was changed, and the recommendation stays read-only and non-operational.
- Next task: `TB-128`

### TB-128: Update Swiss-Wide Envelope From Measured Balfrin Demo

- Date: 2026-05-17
- Commit: `dd65ca5`
- Objective: recompute the Swiss-wide planning envelope from measured Balfrin demo evidence while keeping scale-up authorization false.
- Files changed: `scripts/estimate_swiss_wide_execution_envelope.py`, `tests/test_swiss_wide_execution_envelope.py`, `docs/current_maturity_snapshot.md`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added explicit planning labels for `no_go`, `defer`, and `allowed_next_probe`, and carried the measured Balfrin demo run root into the report provenance.
  - Kept the Swiss-wide envelope read-only with `scale_up_authorized=false`, while still projecting runtime, storage, file-count, memory, and job-count bands from measured Balfrin and same-scale evidence.
  - Strengthened regression coverage for the measured no-go projection, the blocked-missing-inputs path, and the Balfrin provenance fields.
  - Updated the maturity snapshot and removed TB-128 from the active backlog after the envelope helper change landed.
- Checks run:
  - `PYENV_VERSION=system uv run python -m py_compile scripts/estimate_swiss_wide_execution_envelope.py tests/test_swiss_wide_execution_envelope.py`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_swiss_wide_execution_envelope -v`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_bounded_reducer_runtime_scaling tests.test_balfrin_single_job_execution -v`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
- Result/status: completed
- Boundaries: the envelope remains a planning aid only; no Swiss-wide execution, distributed execution, production ensemble, or operational hazard claim was authorized.
- Next task: `TB-129`

### TB-129: Map Balfrin Demo Evidence To Physical-Credibility Gaps

- Date: 2026-05-17
- Commit: `0221112`
- Objective: map the measured Balfrin demo outputs to the existing physical-credibility, validation, and calibration evidence requirements without conflating the demo with calibration, validation, annual-frequency, or operational evidence.
- Files changed: `scripts/summarize_balfrin_physical_credibility_evidence_gaps.py`, `tests/test_balfrin_physical_credibility_evidence_gaps.py`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added a Balfrin-specific physical-credibility evidence-gap helper that composes the measured Balfrin bundle, the validation/calibration gap report, the observed runout/deposition intake contract, and the physical-credibility requirement matrix into one read-only report.
  - Classified the Balfrin demo as measured but still `no_physical_evidence`, with diagnostic/reproducibility-only evidence separated from the physical-credibility requirements that remain missing.
  - Added focused regressions for the measured, blocked, and no-physical-evidence states, including a synthetic override path that keeps the demo measured while the physical-credibility boundary stays negative.
  - Removed TB-129 from the active backlog after the helper and tests were in place.
- Checks run:
  - `PYENV_VERSION=system uv run python -m py_compile scripts/summarize_balfrin_physical_credibility_evidence_gaps.py tests/test_balfrin_physical_credibility_evidence_gaps.py`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_physical_credibility_evidence_gaps -v`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_physical_credibility_evidence_gaps tests.test_balfrin_evidence_bundle tests.test_validation_calibration_evidence_gaps -v`
  - `PYENV_VERSION=system uv run python scripts/summarize_balfrin_physical_credibility_evidence_gaps.py --format json`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
- Result/status: completed
- Boundaries: the report stays diagnostic only; no calibration, fitting, return-period, annual-frequency, risk, exposure, vulnerability, distributed-execution, physical-probability, or operational claim was introduced.
- Next task: backlog refill needed; see `docs/task_backlog.md`.

### TB-130: Execute Live Balfrin Restartability And Resume Proof

- Date: 2026-05-17
- Commit: `5102976`
- Objective: replace the fixture-backed Balfrin restartability note with a live interrupted-and-resumed recovery proof from the Balfrin single-node probe path.
- Files changed: `docs/balfrin_failure_recovery_playbook.md`, `docs/balfrin_restartability_recovery_report.md`, `docs/task_backlog.md`, `scripts/summarize_balfrin_evidence_bundle.py`, `scripts/summarize_balfrin_restartability_recovery.py`, `tests/test_balfrin_restartability_recovery.py`
- Implementation summary:
  - Rewrote the restartability report around the live interrupted `v1` run and resumed `v3` run, including the 530-second resume gap, the job ids, and the artifact-continuity checks.
  - Extended the recovery summarizer so measured overrides can carry live timing and continuity fields, and so the rendered report distinguishes live proof from fixture-backed proof.
  - Updated the recovery playbook note and the evidence-bundle source list so the canonical reporting points at the live restartability proof, then removed TB-130 from the active backlog.
  - Added focused tests for measured recovery timing, artifact continuity, and the unchanged fixture-backed CLI path.
- Checks run:
  - `PYENV_VERSION=system uv run python -m py_compile scripts/summarize_balfrin_restartability_recovery.py scripts/summarize_balfrin_evidence_bundle.py tests/test_balfrin_restartability_recovery.py`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_restartability_recovery tests.test_balfrin_evidence_bundle`
  - `PYENV_VERSION=system uv run python scripts/summarize_balfrin_restartability_recovery.py --evidence-json /tmp/balfrin_restartability_recovery_live_override.json --format text`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
- Result/status: completed
- Boundaries: live single-node Balfrin recovery only; no distributed execution, scale-up authorization, physics, annual-frequency, risk, exposure, vulnerability, or operational claim was introduced.
- Next task: `TB-131`

### TB-131: Complete Balfrin Metrics Contract Coverage
- Date: 2026-05-17
- Commit: `87c4016`
- Objective: complete the measured Balfrin metrics contract by surfacing mandatory runtime/output evidence and naming the remaining ancillary-unavailable fields explicitly.
- Files changed: `scripts/collect_balfrin_probe_metrics.py`, `scripts/summarize_balfrin_evidence_bundle.py`, `tests/test_balfrin_probe_driver.py`, `tests/test_balfrin_evidence_bundle.py`, `docs/task_backlog.md`
- Implementation summary:
  - Extended the Balfrin probe collector with an explicit ancillary-metrics block that classifies validation-output-mode and output-write-kind fields as available or unavailable without changing the mandatory metrics contract.
  - Threaded the ancillary block through the canonical evidence bundle so the read-only summary now states the unavailable ancillary fields explicitly while still preserving the measured peak-memory and validation/hazard file-count and byte evidence.
  - Added focused regressions for the measured collector path, the blocked incomplete-root path, the synthetic complete-with-unavailable-ancillary path, and the bundle report propagation.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_probe_driver tests.test_balfrin_evidence_bundle`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
- Result/status: completed
- Boundaries: no new ensemble, no scale-up authorization, no replacement of measured evidence with synthetic evidence, and no operational or probabilistic claim expansion.
- Next task: `TB-132`

### TB-133: Emit Terrain Release-Zone Candidate Polygons And Masks
- Date: 2026-05-17
- Commit: local
- Objective: convert deterministic terrain candidate metrics into reproducible GIS-readable candidate polygon and mask products for the Tschamut dry-run workflow without replacing the validated source zone.
- Files changed: `scripts/plan_terrain_release_zone_candidates.py`, `tests/test_plan_terrain_release_zone_candidates.py`, `docs/current_maturity_snapshot.md`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added an optional `--output-root` / `--output-mode` emission path that writes deterministic candidate polygon and mask bundles plus a manifest, while preserving the existing read-only metrics report when no output root is supplied.
  - Fixed the candidate slope summary to report slope degrees from the computed slope mask instead of terrain elevations, and added frozen-footprint comparison metadata so the emitted bundle explicitly shows the candidate set excludes the validated Tschamut source-zone footprint.
  - Built stable connected-component candidate IDs, GeoJSON feature output, ESRI ASCII mask output, and provenance metadata for the terrain crop, terrain metadata, and frozen source-zone sidecar.
  - Added focused regressions for deterministic emitted outputs, blocked missing-input behavior, and the new product/manifest fields, then removed TB-133 from the active backlog.
- Checks run:
  - `PYENV_VERSION=system uv run python -m py_compile scripts/plan_terrain_release_zone_candidates.py tests/test_plan_terrain_release_zone_candidates.py`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_plan_terrain_release_zone_candidates -v`
  - `PYENV_VERSION=system uv run python scripts/plan_terrain_release_zone_candidates.py --format json --output-root /tmp/tb133_candidate_products`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
- Result/status: completed
- Boundaries: the helper emits dry-run candidate products only; no validated release-zone approval, threshold tuning to outcomes, annual-frequency claim, physical-probability claim, risk, exposure, vulnerability, or operational claim was introduced.
- Next task: `TB-134`

### TB-134: Generate Deterministic Block-Scenario Tables From Policy

- Date: 2026-05-17
- Commit: `e405957`
- Objective: Turn the pragmatic block-scenario sensitivity plan into a deterministic scenario-table generator from release metadata and policy inputs.
- Files changed: `scripts/generate_tschamut_block_scenario_tables.py`, `tests/test_tschamut_block_scenario_table_generation.py`, `docs/task_backlog.md`
- Implementation summary:
  - Added a deterministic Tschamut scenario-table generator that reproduces the committed single-row summary table from policy plus release-point metadata.
  - Added a policy-family template and provenance-aware manifest that preserve stable row IDs, conditional weighting semantics, and non-frequency boundaries without annual-frequency fields.
  - Added focused regression tests for byte-for-byte regeneration, deterministic alternate-template output, and fail-closed missing-input handling.
- Checks run:
  - `PYENV_VERSION=system uv run python -m py_compile scripts/generate_tschamut_block_scenario_tables.py`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_tschamut_block_scenario_table_generation tests.test_plan_pragmatic_release_plan`
  - `PYENV_VERSION=system uv run python scripts/generate_tschamut_block_scenario_tables.py --format json --template observed_rows_summary_v1`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
- Result/status: completed
- Boundaries: no physics changes, no annual frequency, no fitted block-size population model, and no operational interpretation.
- Next task: `TB-135`

### TB-135: Execute Bounded Next Ensemble Probe
- Date: 2026-05-17
- Commit: local
- Objective: produce a fail-closed record for the smallest bounded next same-scale probe that could test uncertainty/runtime tradeoffs without scale-up or operational claims.
- Files changed: `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Ran the bounded-next feasibility helper against the committed same-scale evidence and confirmed the proposed probe remains the frozen rebuildable-reduced target-gate command, with a 17-file / 3,953,602-byte output footprint.
  - Recorded the helper's conservative blocker: optional probabilistic metadata is absent from the current reduced-output fixture, so the probe stays `deferred_pending_optional_probabilistic_metadata` rather than being authorized as a new execution.
  - Compared that blocked probe posture against the existing same-scale envelope in `docs/tschamut_public_same_scale_uncertainty_envelope.md`, where the measured 12-trajectory probes remain materially larger at 247 files and roughly 68 MB, while the same-scale frontier code only supports another bounded probe if the frontier stays informative and the boundedness proof remains true.
  - Noted the Balfrin frontier policy path: it defers a small bounded ensemble only when the same-scale frontier is informative; otherwise it falls back to `no_go_additional_ensemble`, so the conservative next step remains to wait for the missing metadata rather than scale up.
- Checks run:
  - `PYENV_VERSION=system uv run python scripts/summarize_bounded_next_ensemble_feasibility_probe.py --format json`
  - `PYENV_VERSION=system uv run python scripts/summarize_balfrin_ensemble_frontier.py --format json` (did not complete within the bounded wait window)
- Result/status: implemented_blocked_report
- Boundaries: no large production ensemble, no tuning, no scale-up authorization, and no operational claim was introduced; the task records a blocked next-step plan rather than asserting closure change.
- Next task: `TB-136`

### TB-136: Generate Persistent Hazard Confidence Products

- Date: 2026-05-17
- Commit: `a7a85ad`
- Objective: Convert measured same-scale stability and persistence evidence into deterministic GIS-readable diagnostic confidence products with explicit claim boundaries.
- Files changed: `scripts/summarize_spatial_same_scale_uncertainty.py`, `tests/test_spatial_same_scale_uncertainty.py`, `docs/tschamut_public_same_scale_uncertainty_envelope.md`, `docs/task_backlog.md`
- Implementation summary:
  - Added a confidence-product manifest plus deterministic GeoJSON outputs for `persistent_hazard`, `unstable_region`, `support_nodata_sensitive`, and `shared_support_magnitude` derived from the measured same-scale region summaries.
  - Kept the new products boundary-safe by marking them diagnostic-only and reusing the existing stable/unstable region evidence rather than introducing any new model run or probability claim.
  - Extended the spatial regression test to verify the new manifest, product file ordering, deterministic repeat writes, and blocked-input behavior.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_spatial_same_scale_uncertainty`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_same_scale_stability_frontier`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_tschamut_conditional_diagnostic_interpretation`
  - `PYENV_VERSION=system uv run python -m py_compile scripts/summarize_spatial_same_scale_uncertainty.py tests/test_spatial_same_scale_uncertainty.py`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
- Result/status: completed
- Boundaries: diagnostic uncertainty products only; no operational hazard, annual-frequency, physical-probability, or scale-up claim was introduced.
- Next task: `TB-137`

### TB-137: Prepare Chant Sura Real-Context Acquisition Readiness Pack
- Date: 2026-05-17
- Commit: local
- Objective: convert the Chant Sura trigger matrix into a fail-closed readiness pack that separates proceed, defer, missing-input, and locally-stageable states for public-context products.
- Files changed: `docs/chant_sura_fluelapass_real_context_acquisition_decision.md`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Recast the Chant Sura decision document into a readiness pack with an explicit product-by-product matrix, current state labels, staging command families, expected roots, and current preflight impact.
  - Updated the current repo-root status to `blocked_missing_inputs` so the pack now matches the live helpers rather than the earlier staged-core-input scenario.
  - Kept the package fail-closed: the Balfrin trigger remains `defer`, the AOI tile catalog is still missing, and no synthetic fixture was promoted to public-context evidence.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_swisstopo_aoi_acquisition_planner tests.test_second_site_public_geodata_preflight tests.test_chant_sura_real_context_readiness_gate -v`
- Result/status: implemented_blocked_report
- Boundaries: no second-site ensemble, no hazard build, no unauthorized downloads, and no synthetic evidence promotion were introduced.
- Next task: `TB-138`

### TB-138: Prepare Observed Runout And Deposition Benchmark Acquisition Pack

- Date: 2026-05-17
- Commit: `d0a3b06`
- Objective: turn the observed runout/deposition intake contract into a concrete benchmark acquisition pack with explicit non-evidence artifacts and a blocked report.
- Files changed: `scripts/summarize_observed_runout_deposition_intake_contract.py`, `tests/test_observed_runout_deposition_intake_contract.py`, `docs/task_backlog.md`
- Implementation summary:
  - Added a dry-run acquisition pack that now writes an acquisition checklist, required dataset inventory, geometry template, provenance template, objective-function placeholder template, blocked no-evidence report, template manifest, and validation summary.
  - Kept benchmark intake and calibration paths separate by representing the benchmark dataset role independently from the calibration dataset role and by preserving the calibration blocker in the no-evidence report.
  - Extended the regression test to verify the new artifacts, the blocked report wording, and the benchmark-vs-calibration readiness split.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_observed_runout_deposition_intake_contract -v`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_validation_calibration_evidence_gaps tests.test_balfrin_physical_credibility_evidence_gaps -v`
  - `PYENV_VERSION=system uv run python scripts/summarize_observed_runout_deposition_intake_contract.py --output-root /tmp/tb138_observed_runout_pack --format json`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
- Result/status: implemented_blocked_report
- Boundaries: no calibration, fitting, parameter tuning, annual frequency, risk, exposure, vulnerability, operational claim, or real benchmark evidence was introduced.
- Next task: `TB-139`

### TB-139: Build Balfrin Demonstration Replay Smoke Test
- Date: 2026-05-17
- Commit: local
- Objective: add a deterministic Balfrin replay smoke helper that fails closed when the measured run root is absent and regenerates the bundle and post-run interpretation outputs when the run root is available.
- Files changed: `scripts/summarize_balfrin_demonstration_replay_smoke.py`, `tests/test_balfrin_demonstration_replay_smoke.py`, `docs/balfrin_single_job_execution_sufficiency.md`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added a run-root driven smoke helper that collects probe metrics, rebuilds the canonical Balfrin evidence bundle, rebuilds the post-run interpretation gate, and writes a dedicated smoke report alongside the regenerated artifacts.
  - Made the helper fail closed with `blocked_missing_inputs` when the run root is absent, while still materializing blocked bundle and gate reports for the operator handoff path.
  - Added focused tests for present-run-root replay and missing-run-root blocked behavior, and documented the deterministic smoke command in the Balfrin sufficiency note.
- Checks run:
  - `PYENV_VERSION=system uv run python -m py_compile scripts/summarize_balfrin_demonstration_replay_smoke.py tests/test_balfrin_demonstration_replay_smoke.py`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_demonstration_replay_smoke tests.test_balfrin_evidence_bundle tests.test_balfrin_post_run_interpretation_gate -v`
  - `PYENV_VERSION=system uv run python scripts/summarize_balfrin_demonstration_replay_smoke.py --run-root tests/fixtures/balfrin_probe_metrics_contract/complete_run_root --artifact-dir /tmp/balfrin_demonstration_replay_smoke_v1 --format json`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
  - `git status --short`
- Result/status: implemented_measured
- Boundaries: no new Slurm execution, no generated artifact commits, and no claim-boundary changes.
- Next task: `TB-140`

### TB-140
- Date: 2026-05-17
- Commit: local
- Objective: compose the AOI acquisition, terrain candidate, frozen scenario, and portable command-plan dry-run helpers into one deterministic site-level preparation report.
- Files changed: `scripts/plan_aoi_to_prepared_pilot_dry_run.py`, `tests/test_aoi_to_prepared_pilot_dry_run.py`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Reworked the AOI dry-run orchestrator to compose the AOI acquisition planner, the terrain release-zone candidate helper, the frozen scenario-table helper, and the portable command-plan helper into one report.
  - Added explicit report sections for candidate source zones, scenario-generation inputs, ignored output roots, and command-plan hooks, while keeping blocked missing-input behavior deterministic.
  - Updated the focused regression test to cover the staged-fixture composition path and the blocked temp-repo path.
- Checks run:
  - `PYENV_VERSION=system uv run python -m py_compile scripts/plan_aoi_to_prepared_pilot_dry_run.py tests/test_aoi_to_prepared_pilot_dry_run.py`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_aoi_to_prepared_pilot_dry_run tests.test_swisstopo_aoi_acquisition_planner tests.test_plan_terrain_release_zone_candidates tests.test_plan_pragmatic_release_plan tests.test_pilot_command_plan`
- Result/status: implemented_measured
- Boundaries: no downloads, no ensembles, no second-site hazard build, no physical-probability semantics, and no operational claim.
- Next task: backlog refill needed

### TB-141: Replay Measured Balfrin Demo From Live Run Root
- Date: 2026-05-17
- Commit: local
- Objective: distinguish fixture-backed Balfrin replay smoke coverage from a live run-root replay path, then verify the live-root path fails closed when the measured Balfrin run root is absent in this environment.
- Files changed: `scripts/summarize_balfrin_demonstration_replay_smoke.py`, `tests/test_balfrin_demonstration_replay_smoke.py`, `docs/balfrin_single_job_execution_sufficiency.md`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added explicit `run_root_provenance` classification to the Balfrin replay smoke helper so fixture-backed replay, non-fixture live-root replay, and missing roots are distinguishable in both JSON and text output.
  - Added regression coverage for fixture-backed replay, non-fixture present-root classification, and missing-root fail-closed behavior.
  - Documented the new provenance field in the Balfrin sufficiency note and removed the completed task from the active backlog.
- Checks run:
  - `PYENV_VERSION=system uv run python -m py_compile scripts/summarize_balfrin_demonstration_replay_smoke.py tests/test_balfrin_demonstration_replay_smoke.py`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_demonstration_replay_smoke -v`
  - `PYENV_VERSION=system uv run python scripts/summarize_balfrin_demonstration_replay_smoke.py --run-root /scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_single_release_zone_v3 --artifact-dir /tmp/balfrin_live_smoke_blocked_v1 --format json`
- Result/status: implemented_blocked_report
- Boundaries: no new Slurm execution, no generated artifact commits, no operational claim, and no physical-probability claim.
- Next task: `TB-142`

### TB-142: Close Balfrin Metrics Completeness Gaps
- Date: 2026-05-17
- Commit: local
- Objective: separate the Balfrin metrics report into explicit mandatory, ancillary, measured, unavailable, and blocked fields so the canonical evidence bundle no longer blurs live measurements with unrecoverable scheduler/artifact data.
- Files changed: `scripts/collect_balfrin_probe_metrics.py`, `scripts/summarize_balfrin_evidence_bundle.py`, `docs/balfrin_single_job_execution_sufficiency.md`, `docs/current_maturity_snapshot.md`, `tests/test_balfrin_probe_driver.py`, `tests/test_balfrin_evidence_bundle.py`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added explicit metric-status sections to the Balfrin probe collector so mandatory fields, ancillary split-output fields, measured values, unavailable values, and blocked values are all reported separately with recovery notes.
  - Surfaced the new metric-status sections in the canonical Balfrin evidence bundle text and JSON output, including the split-output family counts that explain the ancillary status.
  - Updated the Balfrin sufficiency note and maturity snapshot to describe which fields the live run-root collector can recover and which fields the canonical bundle cannot retain.
  - Extended the Balfrin probe-driver and evidence-bundle regression tests to cover measured mandatory fields, measured split-output artifacts, unavailable ancillary fields, and blocked missing-input cases.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_probe_driver tests.test_balfrin_evidence_bundle -v`
  - `PYENV_VERSION=system uv run python scripts/summarize_balfrin_evidence_bundle.py --format json`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
  - `git status --short`
- Result/status: implemented_measured
- Boundaries: no new ensemble, no scale-up authorization, no operational claim, no substitution of fixture evidence for live measurements, and no claim that the canonical bundle retains scheduler artifacts it does not store.
- Next task: `TB-143`

### TB-143
- Date: 2026-05-17
- Commit: local
- Objective: make the bounded next-ensemble feasibility helper report the optional probabilistic metadata contract explicitly so reduced-output fixtures are handled deterministically without over-authorizing execution.
- Files changed: `scripts/summarize_bounded_next_ensemble_feasibility_probe.py`, `tests/test_bounded_next_ensemble_feasibility_probe.py`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added an explicit optional-metadata contract summary to the bounded next-ensemble feasibility helper, including required sections, required fields, present fields, missing fields, and the exact smallest-useful-probe metadata bundle.
  - Split the section status reporting so a reduced fixture can block on the missing probabilistic metadata contract while a full optional-metadata fixture stays deferred until explicit authorization.
  - Extended the text and JSON reports to surface the exact missing paths, the command-plan status, and the override paths used by the report builder.
  - Added regression coverage for the native reduced fixture, a full optional-metadata fixture, and a partially missing-metadata fixture.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_bounded_next_ensemble_feasibility_probe -v`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_ensemble_frontier -v`
  - `PYENV_VERSION=system uv run python scripts/summarize_bounded_next_ensemble_feasibility_probe.py --format json`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
  - `git status --short`
- Result/status: implemented_measured
- Boundaries: no new ensemble run, no tuning, no scale-up authorization, no operational claim, and no physical-probability claim.
- Next task: `TB-144`

### TB-144
- Date: 2026-05-17
- Commit: local
- Objective: record the smallest bounded Balfrin follow-up probe as a fail-closed blocked report when the optional probabilistic metadata contract is still incomplete.
- Files changed: `tests/test_balfrin_ensemble_frontier.py`, `docs/balfrin_single_job_execution_sufficiency.md`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added a focused frontier regression that proves the practical Balfrin ensemble helper blocks when the feasibility helper reports `blocked_missing_optional_probabilistic_metadata`.
  - Documented the exact missing optional probabilistic metadata fields in the Balfrin sufficiency note so the blocked comparison basis is visible in the repo.
  - Removed the completed TB-144 entry from the active backlog after recording the fail-closed outcome instead of forcing execution.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_ensemble_frontier -v`
  - `PYENV_VERSION=system uv run python scripts/summarize_bounded_next_ensemble_feasibility_probe.py --format json`
- Result/status: implemented_blocked_report
- Boundaries: no ensemble execution, no parameter tuning, no scale-up authorization, and no operational claim.
- Next task: `TB-145`

### TB-145
- Date: 2026-05-17
- Commit: local
- Objective: compare the bounded Balfrin probe against the existing same-scale uncertainty, stability, and closure-gap evidence without upgrading closure by assertion.
- Files changed: `scripts/summarize_balfrin_bounded_probe_interpretation.py`, `scripts/summarize_balfrin_scientific_delta_report.py`, `tests/test_balfrin_bounded_probe_interpretation.py`, `tests/test_balfrin_scientific_delta_report.py`, `docs/tschamut_public_same_scale_uncertainty_envelope.md`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added a dedicated bounded-probe comparison helper that classifies unchanged, improved, worsened, and blocked interpretation states while keeping the closure status explicit and conservative.
  - Wired the new bounded-probe comparison into the Balfrin scientific delta report as a reusable sidecar field so the canonical summary now exposes the probe comparison without turning a blocked probe into a broader scientific failure.
  - Updated the same-scale uncertainty envelope note to point at the new comparator and preserve the current inconclusive closure boundary.
  - Added focused regression coverage for the measured, no-change, and missing-probe states plus an integration assertion that the scientific delta report surfaces the bounded-probe comparison fields.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_bounded_probe_interpretation tests.test_balfrin_scientific_delta_report -v`
  - `PYENV_VERSION=system uv run python -m py_compile scripts/summarize_balfrin_bounded_probe_interpretation.py scripts/summarize_balfrin_scientific_delta_report.py tests/test_balfrin_bounded_probe_interpretation.py tests/test_balfrin_scientific_delta_report.py`
- Result/status: implemented_measured
- Boundaries: no closure upgrade by assertion, no physics tuning, no operational claim, no physical-probability claim, and no scale-up authorization.
- Next task: `TB-146`

### TB-146
- Date: 2026-05-17
- Commit: local
- Objective: freeze the Balfrin management demonstration evidence into one compact replayable package manifest with explicit runtime, replay, restartability, GIS scope, uncertainty, and claim-boundary sections.
- Files changed: `scripts/summarize_balfrin_management_demo_package.py`, `tests/test_balfrin_management_demo_package.py`, `docs/balfrin_single_job_execution_sufficiency.md`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added a compact management-demo package helper that composes the measured evidence bundle with the replay smoke helper and renders a single JSON/text manifest instead of a spread of ad hoc review outputs.
  - Kept the runtime, replay, restartability, GIS scope, uncertainty, and claim-boundary sections separate, and recorded a deterministic regeneration command sequence alongside section provenance counts.
  - Added focused regression coverage for a mixed measured/fixture-backed package, an all-fixture-backed override, and an explicit blocked-missing-inputs override so provenance does not collapse across section types.
  - Documented the new package entrypoint in the Balfrin sufficiency note so a reviewer can regenerate the compact review artifact into `/tmp` or an ignored artifact root.
- Checks run:
  - `PYENV_VERSION=system uv run python -m py_compile scripts/summarize_balfrin_management_demo_package.py tests/test_balfrin_management_demo_package.py`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_management_demo_package -v`
- Result/status: implemented_measured
- Boundaries: no operational claim, no annual-frequency claim, no physical-probability claim, no validation claim, no scale-up authorization, and no generated large-artifact commit.
- Next task: `TB-147`

### TB-147
- Date: 2026-05-17
- Commit: local
- Objective: harden the AOI tile-discovery dry run so realistic swisstopo catalog shapes, product variants, and blocked/no-catalog states produce stable no-download manifests instead of brittle fixture-only matches.
- Files changed: `scripts/check_second_site_public_geodata_preflight.py`, `scripts/plan_swisstopo_aoi_acquisition.py`, `docs/swisstopo_data_strategy.md`, `docs/task_backlog.md`, `tests/test_swisstopo_aoi_acquisition_planner.py`, `tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_minimal_staging/aoi_tile_catalog.yaml`, `tests/fixtures/second_site_public_geodata_preflight/catalog_shapes/blocked_missing_metadata.yaml`, `tests/fixtures/second_site_public_geodata_preflight/catalog_shapes/nested_product_variants.yaml`
- Implementation summary:
  - Added a deterministic catalog flattener that preserves product ids, tile ids, CRS, resolution, product version/date, and expected staging roots while supporting both flat `tiles:` catalogs and nested `products:`/variant catalogs.
  - Extended the AOI discovery report with product/tile manifests, catalog blockers, and no-download summary rows so the planner can compose stable dry-run output without authorizing downloads.
  - Added fixture-backed regression coverage for the current flat catalog, a nested multi-variant catalog, and an explicit blocked catalog so missing metadata fails closed instead of being silently treated as a match.
  - Updated the swisstopo data strategy note to document the stronger catalog provenance contract used by the dry-run planner.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_swisstopo_aoi_acquisition_planner`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_second_site_public_geodata_preflight`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
  - `git status --short`
- Result/status: implemented_measured
- Boundaries: no downloads, no license-sensitive raw data commits, no ensemble, no operational claim, and no scale-up or probability claim.
- Next task: `TB-148`

### TB-148
- Date: 2026-05-17
- Commit: local
- Objective: define a deterministic public-geodata cache contract with explicit provenance fields, stage/verify command templates, and fail-closed verification states for staged AOI products.
- Files changed: `scripts/check_second_site_public_geodata_preflight.py`, `scripts/verify_public_geodata_cache.py`, `tests/test_public_geodata_cache_verifier.py`, `tests/test_second_site_public_geodata_preflight.py`, `docs/swisstopo_data_strategy.md`, `docs/public_real_site_geodata_preparation.md`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added a machine-readable `public_geodata_cache_contract` to the preflight workflow contract so the ignored raw cache root, processed roots, cache-manifest path, stage command, verify command, and required provenance fields are surfaced together.
  - Implemented `scripts/verify_public_geodata_cache.py` with shared preflight logic so staged public products fail closed as `missing`, `checksum_mismatch`, or `metadata_mismatch` instead of being treated as trusted by default.
  - Added focused regression coverage for verified, missing, checksum-mismatch, and metadata-mismatch cache states using temporary staged files and metadata sidecars.
  - Updated the swisstopo strategy and public real-site preparation notes to point at the cache contract and verifier command, then removed TB-148 from the active backlog.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_public_geodata_cache_verifier tests.test_second_site_public_geodata_preflight tests.test_swisstopo_aoi_acquisition_planner -v`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
  - `git status --short`
- Result/status: implemented_fixture_backed
- Boundaries: no bulk download, no raw swisstopo commit, no hazard run, no operational claim, and no scale-up or physical-probability claim.
- Next task: `TB-149`

### TB-149
- Date: 2026-05-17
- Commit: local
- Objective: prototype a deterministic AOI terrain preprocessing helper from staged tiles and feed its contract into release-zone candidate planning.
- Files changed: `scripts/plan_aoi_terrain_preprocessing.py`, `scripts/plan_terrain_release_zone_candidates.py`, `tests/test_aoi_terrain_preprocessing.py`, `tests/test_plan_terrain_release_zone_candidates.py`, `docs/public_real_site_geodata_preparation.md`, `docs/task_backlog.md`
- Implementation summary:
  - Added a fixture-backed AOI terrain preprocessing helper that reads a staged ESRI ASCII crop, terrain metadata sidecar, and AOI tile catalog, then records crop extent, resolution, CRS, nodata, source tiles, output roots, and a manifest path in a deterministic report.
  - Wired the release-zone candidate planner to consume the terrain-preprocessing report when a staged AOI tile catalog is present, including explicit crop extent, resolution, CRS, nodata, and source-tile screening fields.
  - Added regression coverage for the ready fixture case, a missing-tile failure, a metadata-mismatch failure, and the planner integration path that inherits the new terrain-package fields.
  - Removed TB-149 from the active backlog and documented the new helper in the public real-site geodata preparation guide.
- Checks run:
  - `PYENV_VERSION=system uv run python -m py_compile scripts/plan_aoi_terrain_preprocessing.py scripts/plan_terrain_release_zone_candidates.py tests/test_aoi_terrain_preprocessing.py tests/test_plan_terrain_release_zone_candidates.py scripts/prepare_chant_sura_fluelapass_minimal_preflight_inputs.py`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_aoi_terrain_preprocessing tests.test_plan_terrain_release_zone_candidates tests.test_swisstopo_aoi_acquisition_planner`
  - `PYENV_VERSION=system uv run python scripts/plan_aoi_terrain_preprocessing.py --repo-root /tmp --terrain-crop tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_minimal_staging/terrain.asc --terrain-metadata tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_minimal_staging/terrain_metadata.yaml --aoi-tile-catalog tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_minimal_staging/aoi_tile_catalog.yaml --format json`
  - `PYENV_VERSION=system uv run python scripts/plan_terrain_release_zone_candidates.py --terrain-crop tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_minimal_staging/terrain.asc --terrain-metadata tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_minimal_staging/terrain_metadata.yaml --source-zone-metadata tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_minimal_staging/source_zone_metadata.yaml --format json`
- Result/status: implemented_fixture_backed
- Boundaries: no national-scale processing, no unauthorized downloads, no physics changes, and no operational claim.
- Next task: `TB-150`

### TB-150: Stress-Test Release-Zone Candidate Heuristic Stability

- Date: 2026-05-17
- Commit: `ca6ad60`
- Objective: quantify how deterministic terrain-driven release-zone candidates change under bounded threshold and preprocessing perturbations.
- Files changed: `scripts/plan_terrain_release_zone_candidates.py`, `tests/test_plan_terrain_release_zone_candidates.py`, `docs/current_maturity_snapshot.md`, `docs/swisstopo_data_strategy.md`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added a deterministic candidate-sensitivity report that compares baseline, tighter, wider, and footprint-buffered heuristic variants and records candidate count, area, overlap, and stable/unstable region summaries.
  - Extended the candidate planner so a bounded footprint buffer can represent preprocessing perturbation without changing the release-zone claim boundary.
  - Added fixture-backed regression coverage for ready, blocked, stable, and heuristic-sensitive report shapes and updated the text renderer to print the new section.
  - Updated the maturity snapshot and swisstopo strategy notes so the repo explicitly says the stability report is characterization only, not validation.
- Checks run:
  - `PYENV_VERSION=system uv run python -m py_compile scripts/plan_terrain_release_zone_candidates.py tests/test_plan_terrain_release_zone_candidates.py`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_plan_terrain_release_zone_candidates -v`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
  - `git status --short`
- Result/status: implemented_fixture_backed
- Boundaries: no threshold tuning to match outcomes, no field-validation claim, no operational release-zone claim, no ensemble run, and no scale-up authorization.
- Next task: `TB-151`

### TB-151
- Date: 2026-05-17
- Commit: local
- Objective: generalize deterministic block-scenario generation so candidate source-zone metadata and a policy template can produce provenance-aware tables without Tschamut-only identifiers.
- Files changed: `scripts/generate_tschamut_block_scenario_tables.py`, `tests/test_tschamut_block_scenario_table_generation.py`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added a generic candidate-source-zone report path and CLI aliases while keeping the Tschamut defaults as a compatibility wrapper.
  - Introduced provenance-aware manifests with resolved source-zone ids, scenario-family ids, and explicit conditional-only weighting flags for both the legacy summary table and the policy-family table.
  - Added regression coverage for the frozen Tschamut summary, the existing policy-family expansion, and a synthetic non-Tschamut candidate that does not depend on the committed Tschamut reference table.
  - Removed TB-151 from the active backlog after the implementation landed.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_tschamut_block_scenario_table_generation -v`
  - `PYENV_VERSION=system uv run python -m py_compile scripts/generate_tschamut_block_scenario_tables.py tests/test_tschamut_block_scenario_table_generation.py`
- Result/status: implemented_fixture_backed
- Boundaries: no block-population fitting, no annual-frequency semantics, no physics changes, and no operational claim.
- Next task: `TB-152`

### TB-152: Emit Runnable Case Skeletons From AOI Dry Run

- Date: 2026-05-17
- Commit: `fd94635`
- Objective: extend the AOI dry-run so it can emit a non-executed case skeleton bundle and command references under ignored roots.
- Files changed: `scripts/plan_aoi_to_prepared_pilot_dry_run.py`, `tests/test_aoi_to_prepared_pilot_dry_run.py`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added an optional ignored-root output mode that writes a candidate case skeleton YAML, a command manifest JSON, an expected-output-roots YAML, and a blocked-execution JSON bundle.
  - Classified the AOI command references as runnable or template-only in the dry-run report and surfaced those lists in the human-readable output.
  - Added regression coverage for deterministic bundle generation in the optional output mode and for blocked missing-input states that still preserve the handoff artifacts.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_aoi_to_prepared_pilot_dry_run`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
  - `git status --short`
- Result/status: implemented_fixture_backed
- Boundaries: no ensemble execution, no second-site hazard build, no large-artifact commit, no physical-probability semantics, and no operational claim.
- Next task: backlog refill needed

### TB-153
- Date: 2026-05-17
- Commit: local
- Objective: add the optional probabilistic metadata required by the reduced-output bounded next-ensemble probe fixture and keep the helper fail-closed for missing-metadata cases.
- Files changed: `tests/fixtures/rebuildable_reduced_output/tschamut_public_target_gate_rebuildable_reduced_case.yaml`, `tests/test_bounded_next_ensemble_feasibility_probe.py`, `docs/balfrin_single_job_execution_sufficiency.md`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Completed the reduced-output fixture with the optional `probabilistic_metadata` and `hazard_probability` blocks expected by the bounded next-ensemble feasibility helper, using the reduced Tschamut output metadata path and the conditional sampling-weighted filter contract already used elsewhere in the repository.
  - Updated the feasibility-helper tests to assert that the complete fixture is classified as `deferred_pending_authorization` while stripped and partial fixtures remain blocked on missing optional metadata.
  - Documented that the fixture change only unblocks planning and does not authorize execution, and removed TB-153 from the active backlog.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_bounded_next_ensemble_feasibility_probe -v`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
  - `git status --short`
- Result/status: implemented_fixture_backed
- Boundaries: no ensemble execution, no annual frequency, no physical-probability claim, no tuning, and no scale-up authorization.
- Next task: `TB-154`

### TB-154
- Date: 2026-05-17
- Commit: local
- Objective: thread the complete bounded-probe feasibility result into the Balfrin ensemble frontier and Swiss-wide execution-envelope helpers.
- Files changed: `scripts/summarize_bounded_next_ensemble_feasibility_probe.py`, `scripts/summarize_same_scale_stability_frontier.py`, `scripts/summarize_balfrin_ensemble_frontier.py`, `scripts/estimate_swiss_wide_execution_envelope.py`, `tests/test_balfrin_ensemble_frontier.py`, `tests/test_same_scale_stability_frontier.py`, `tests/test_swiss_wide_execution_envelope.py`, `docs/task_backlog.md`, `docs/current_maturity_snapshot.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added an explicit `bounded_probe_recommendation_status` to the bounded-next feasibility helper so downstream consumers can read the recomputed complete-metadata recommendation directly instead of inferring it from the old optional-metadata block.
  - Updated the same-scale stability frontier and Balfrin ensemble frontier to treat the complete feasibility result as a deferred-but-evaluated probe path, while still blocking only on genuine missing-input evidence.
  - Threaded the recommendation status into the Swiss-wide envelope measurement basis and render output, then updated the focused tests to assert the complete-metadata contract and the recomputed deferred status.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_bounded_next_ensemble_feasibility_probe`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_same_scale_stability_frontier`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_ensemble_frontier tests.test_same_scale_stability_frontier`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_swiss_wide_execution_envelope`
  - `PYENV_VERSION=system uv run python scripts/summarize_bounded_next_ensemble_feasibility_probe.py --format json`
  - `PYENV_VERSION=system uv run python scripts/estimate_swiss_wide_execution_envelope.py --format json`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
  - `git status --short`
- Result/status: implemented_measured
- Boundaries: no new Balfrin run, no large ensemble, no distributed execution, no operational claim, no scale-up authorization, and no annual-frequency or physical-probability claim.
- Next task: `TB-155`

### TB-155: Define Measured Minimal Balfrin Probe Execution Package

- Date: 2026-05-17
- Commit: `78e01e3`
- Objective: turn the recomputed bounded Balfrin probe recommendation into a deterministic dry-run submission package that can be inspected later without launching a job.
- Files changed: `scripts/submit_balfrin_probe.py`, `tests/test_balfrin_probe_driver.py`, `docs/balfrin_probe_slurm_driver.md`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Extended the Balfrin submission package to carry the recomputed frontier recommendation, reduced-output controls, explicit `blocked_unlaunched` status, expected run root, command-script path, metrics collection command, and stop/resume notes.
  - Kept the package generation dry-run only by preserving `generate-only` behavior and making the new package fields purely descriptive; no SLURM job submission path was exercised.
  - Updated the focused driver tests to assert the package content, the unlaunched boundary, and the deterministic markdown handoff.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_probe_driver -v`
  - `PYENV_VERSION=system uv run python -m py_compile scripts/submit_balfrin_probe.py tests/test_balfrin_probe_driver.py`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
  - `git status --short`
- Result/status: implemented_measured
- Boundaries: no job submission, no ensemble execution, no distributed execution, no scale-up authorization, and no operational or physical-probability claims.
- Next task: `TB-156`

### TB-156: Add Balfrin Metrics Completeness Remediation Plan
- Date: 2026-05-17
- Commit: local
- Objective: turn the remaining unavailable or ancillary Balfrin probe metrics into an explicit next-run collection contract.
- Files changed: `scripts/collect_balfrin_probe_metrics.py`, `scripts/summarize_balfrin_evidence_bundle.py`, `docs/balfrin_single_job_execution_sufficiency.md`, `tests/test_balfrin_evidence_bundle.py`, `tests/test_balfrin_probe_driver.py`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added a machine-readable `metrics_remediation` contract to the probe collector so missing mandatory fields, unavailable ancillary fields, and the ordered next-run-required checklist stay explicit in the JSON output.
  - Mirrored the same remediation contract into the canonical Balfrin evidence bundle and rendered it in the text summary so the review artifact exposes the same next-run collection checklist.
  - Updated the Balfrin sufficiency note and focused tests to describe and assert the deterministic preservation contract for the next measured run.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_probe_driver.BalfrinProbeDriverTests.test_collect_probe_metrics_parses_synthetic_outputs tests.test_balfrin_probe_driver.BalfrinProbeDriverTests.test_collect_probe_metrics_reports_blocked_incomplete_root tests.test_balfrin_probe_driver.BalfrinProbeDriverTests.test_metrics_contract_marks_ancillary_fields_unavailable_without_blocking_complete_run`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_evidence_bundle.BalfrinEvidenceBundleTests.test_current_report_is_measured_and_tracks_section_provenance`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
  - `git status --short`
- Result/status: implemented_measured
- Boundaries: no new Balfrin run, no synthetic measured metrics, no scale-up claim, and no operational claim.
- Next task: `TB-157`

### TB-157: Connect AOI Case Skeleton To Generic Scenario Generation
- Date: 2026-05-17
- Commit: local
- Objective: make the AOI case-skeleton dry run expose the generic candidate-source-zone scenario-generation command, manifest path, expected scenario table, and blocked status without Tschamut-only scenario assumptions.
- Files changed: `scripts/plan_aoi_to_prepared_pilot_dry_run.py`, `scripts/plan_release_plan_dry_run.py`, `docs/public_real_site_geodata_preparation.md`, `tests/test_aoi_to_prepared_pilot_dry_run.py`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Threaded the generic release-plan dry run through the AOI composer so the handoff bundle now carries a portable candidate-source-zone provenance block, the scenario-generation command, the expected scenario table path, and the scenario-table manifest path.
  - Kept the legacy Tschamut-oriented planning fields intact while making the AOI case-skeleton bundle and text report surface the generic handoff fields directly.
  - Added deterministic synthetic-candidate coverage that rewrites staged source-zone inputs and proves the generic provenance remains candidate-specific, plus a doc note that the weights remain conditional-only sampling weights rather than annual-frequency claims.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_aoi_to_prepared_pilot_dry_run tests.test_release_plan_dry_run`
- Result/status: implemented_fixture_backed
- Boundaries: no ensemble execution, no second-site hazard build, no block-population fitting, no annual frequency, and no operational claim.
- Next task: `TB-158`

### TB-158: Produce Chant Sura Real-Context Staging Checklist
- Date: 2026-05-17
- Commit: local
- Objective: convert the Chant Sura real-context acquisition decision into a concrete product-by-product staging checklist with cache-verifier inputs and explicit dry-run claim boundaries.
- Files changed: `scripts/check_chant_sura_real_context_readiness_gate.py`, `docs/chant_sura_fluelapass_real_context_acquisition_decision.md`, `tests/test_chant_sura_real_context_readiness_gate.py`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added a `real_context_staging_checklist` helper to the Chant Sura readiness gate so each deferred public-context product now carries its expected staging root, the shared cache-manifest verification fields, the deterministic verifier command, and a per-row readiness impact.
  - Threaded the checklist into the gate report and text output with an explicit dry-run boundary note so the helper remains a staging contract and not a download, validation, operational, or physical-credibility claim.
  - Added focused regressions for missing, partially staged, and verifier-ready cache-manifest states by staging temporary manifests and files in the test harness.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_chant_sura_real_context_readiness_gate`
- Result/status: implemented_measured
- Boundaries: no downloads, no synthetic evidence upgrade, no second-site ensemble, no operational claim, and no physical validation claim.
- Next task: `TB-159`

### TB-159: Map Physical-Credibility Gaps Onto AOI Automation Outputs
- Date: 2026-05-17
- Commit: local
- Objective: map AOI dry-run outputs to the physical-credibility evidence matrix so workflow artifacts stay separated from physical validation evidence.
- Files changed: `scripts/map_physical_credibility_evidence_requirements.py`, `tests/test_physical_credibility_evidence_requirements.py`, `tests/test_balfrin_physical_credibility_evidence_gaps.py`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added explicit workflow/provenance summaries for AOI cache verification, terrain preprocessing, release-zone candidates, scenario tables, and case skeletons so the physical-credibility helper labels them as non-physical evidence.
  - Threaded those AOI workflow rows into the Balfrin physical-credibility gap summary and updated the evidence-source matrix entries so downstream reports keep the boundary explicit.
  - Added focused regressions that assert the AOI automation outputs remain workflow artifacts and do not satisfy observed-runout, calibration, block-population, or source-frequency requirements.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_physical_credibility_evidence_requirements tests.test_balfrin_physical_credibility_evidence_gaps tests.test_aoi_to_prepared_pilot_dry_run`
- Result/status: implemented_fixture_backed
- Boundaries: no calibration, no tuning, no physical-probability claim, no annual-frequency claim, and no operational claim.
- Next task: `TB-160`

### TB-160: Add Demonstration GIS Scope Review For AOI Handoff
- Date: 2026-05-17
- Commit: local
- Objective: extend AOI case-skeleton handoff bundles with a machine-readable GIS scope summary that separates planned raster/vector products, downstream template-only COG expectations, unavailable inputs, and non-operational boundaries.
- Files changed: `scripts/plan_aoi_to_prepared_pilot_dry_run.py`, `tests/test_aoi_to_prepared_pilot_dry_run.py`, `docs/public_real_site_geodata_preparation.md`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added a `gis_scope_summary` block to the AOI dry-run report and case-skeleton output so the handoff now records planned raster/vector products, a template-only COG export expectation, blocked/missing inputs, and explicit non-operational GIS boundaries without implying any hazard layers were generated.
  - Kept the summary deterministic for both staged and missing-input skeletons by threading the same structure through the report, written skeleton YAML, and text rendering, then pinning it with focused unittest coverage.
  - Added a short documentation note that states the AOI GIS scope summary is a planning artifact and must not be read as generated hazard-map output.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_aoi_to_prepared_pilot_dry_run -v`
  - `PYENV_VERSION=system uv run python scripts/plan_aoi_to_prepared_pilot_dry_run.py --format json`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
- Result/status: implemented_fixture_backed
- Boundaries: no hazard build, no generated raster commit, no operational GIS claim, no risk/exposure/vulnerability semantics, and no scale-up claim.
- Next task: backlog refill needed

### TB-161: Freeze Target-Area Balfrin Demonstration Inputs
- Date: 2026-05-17
- Commit: local
- Objective: freeze the exact Tschamut target area, release-zone record, scenario-family basis, output mode, and single-job Balfrin execution boundary for the next full-scale demonstration pass.
- Files changed: `validation/pilot_runs/tschamut_public_balfrin_target_area_demo_v1.yaml`, `tests/test_balfrin_target_area_demo_contract.py`, `docs/balfrin_probe_slurm_driver.md`, `docs/current_maturity_snapshot.md`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added a machine-readable target-area demonstration contract with the selected Tschamut domain, frozen target-gate reproduction record, scenario-family basis, output mode, run-id policy, expected ignored roots, and command-plan hook.
  - Added a focused regression that loads the frozen contract and checks the target area, run-id policy, output mode, ignored roots, and claim-boundary booleans remain stable.
  - Threaded a short driver note and maturity-snapshot note so later Balfrin tasks can find the frozen target-area contract without guessing its location or boundary.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_target_area_demo_contract`
  - `PYENV_VERSION=system uv run python scripts/submit_balfrin_probe.py validation/pilot_runs/tschamut_public_scalable_conditional_target_gate_v1.yaml --local-command-plan`
- Result/status: implemented_fixture_backed
- Boundaries: no job submission, no new ensemble, no operational claim, no physical-probability claim, and no scale-up authorization.
- Next task: `TB-162`

### TB-162: Verify Target-Area Public-Geodata Readiness

- Date: 2026-05-17
- Commit: `ed53bbc`; corrected by follow-up commit
- Objective: verify whether the frozen Tschamut target-area Balfrin demonstration contract has the tracked public-geodata, source-zone, scenario, and policy inputs needed for the next handoff tasks.
- Files changed: `docs/balfrin_probe_slurm_driver.md`, `docs/current_maturity_snapshot.md`, `docs/chant_sura_fluelapass_real_context_acquisition_decision.md`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Verified that the frozen target-area contract is the Tschamut selected domain in `validation/pilot_runs/tschamut_public_balfrin_target_area_demo_v1.yaml`, not the Chant Sura / Flüelapass second-site candidate.
  - Confirmed the tracked Tschamut public real-site manifest validates and that the frozen source-zone metadata, release/deposition CSVs, scenario table, source-scenario policy, and conditional pilot gate record are present in the checkout.
  - Kept the separate Chant Sura / Flüelapass readiness snapshot as a second-site blocked/deferred public-context record, not as the frozen Balfrin target-area readiness result.
  - Removed TB-162 from `docs/task_backlog.md` after recording the readiness distinction.
- Checks run:
  - `PYENV_VERSION=system uv run python scripts/validate_public_real_site_geodata_manifest.py data/processed/swisstopo/tschamut_public_pilot_manifest.yaml`
  - tracked-path presence check for the frozen target-area source-zone, release/deposition, scenario, policy, and gate records
  - `PYENV_VERSION=system uv run python scripts/submit_balfrin_probe.py validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml --local-command-plan`
  - `PYENV_VERSION=system uv run python scripts/check_second_site_public_geodata_preflight.py --site-config tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml --format json`
  - `PYENV_VERSION=system uv run python scripts/plan_swisstopo_aoi_acquisition.py --site-config tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml --format json`
  - `PYENV_VERSION=system uv run python scripts/verify_public_geodata_cache.py --cache-manifest data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1_cache_manifest.yaml --format json`
  - `PYENV_VERSION=system uv run python -m pytest tests/test_public_geodata_cache_verifier.py tests/test_second_site_public_geodata_preflight.py tests/test_chant_sura_real_context_readiness_gate.py tests/test_multisite_source_scenario_contract.py -q`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
- Result/status: implemented_measured
- Boundaries: no downloads, no synthetic evidence upgrade, no ensemble execution, and no operational or physical-probability claim.
- Next task: `TB-163`

### TB-163: Materialize Target-Area AOI Case Handoff
- Date: 2026-05-17
- Commit: local
- Objective: materialize the frozen Tschamut target-area AOI handoff bundle with a case skeleton, command manifest, expected-output roots, scenario-generation handoff, and GIS scope summary while keeping the bundle template-only.
- Files changed: `scripts/generate_balfrin_target_area_demo_handoff.py`, `scripts/generate_pilot_command_plan.py`, `tests/test_balfrin_target_area_demo_handoff.py`, `tests/test_pilot_command_plan.py`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added a new target-area-only handoff generator that reads the frozen Tschamut Balfrin contract and writes an ignored bundle with a case skeleton, command manifest, expected-output-roots sidecar, scenario-generation handoff, GIS scope summary, and bundle report.
  - Kept the bundle template-only and non-operational while preserving the frozen target-area boundary, the conditional-only scenario semantics, and the ignored target-gate output roots.
  - Hooked the new generator into the portable pilot command plan and added focused regressions that verify the bundle shape, status, expected roots, and command-plan entry remain deterministic.
- Checks run:
  - `PYENV_VERSION=system uv run python scripts/generate_balfrin_target_area_demo_handoff.py --format json`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_target_area_demo_handoff tests.test_balfrin_target_area_demo_contract tests.test_pilot_command_plan`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
  - `git status --short`
- Result/status: implemented_fixture_backed
- Boundaries: no hazard build, no generated raster commit, no second-site ensemble, no operational GIS claim, and no scale-up authorization.
- Next task: `TB-164`

### TB-164: Validate Target-Area Release-Zone Candidate Stability
- Date: 2026-05-17
- Commit: local
- Objective: validate the frozen Tschamut target-area release-zone candidate audit with an explicit stable-versus-heuristic-sensitive summary and optional GIS-readable candidate outputs.
- Files changed: `scripts/summarize_balfrin_target_area_candidate_stability.py`, `tests/test_balfrin_target_area_candidate_stability.py`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added a target-area-specific summary wrapper around the committed terrain candidate helper so the frozen Tschamut Balfrin contract can be checked against the deterministic candidate stability audit without claiming a validated release zone.
  - Surfaced the stable and heuristic-sensitive region classes explicitly, tied the report back to the frozen target-area contract, and kept the GIS-readable candidate mask/polygon bundle available through the existing helper when a temporary output root is supplied.
  - Added focused regressions that verify deterministic report rendering, the frozen target-area identifiers, and the emitted GIS-readable candidate outputs in a temp directory.
- Checks run:
  - `PYENV_VERSION=system uv run python -m py_compile scripts/summarize_balfrin_target_area_candidate_stability.py tests/test_balfrin_target_area_candidate_stability.py`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_target_area_candidate_stability -v`
  - `PYENV_VERSION=system uv run python scripts/summarize_balfrin_target_area_candidate_stability.py --output-root /tmp/tb164_target_area_o8VdUQ/candidate_products --format json --json-output /tmp/tb164_target_area_o8VdUQ/report.json`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
  - `git status --short --branch`
- Result/status: implemented_measured
- Boundaries: no validated release-zone claim, no tuning, no annual-frequency or physical-probability semantics, no scale-up authorization, and no operational hazard-map claim.
- Next task: `TB-165`

### TB-165: Generate Target-Area Deterministic Scenario Tables
- Date: 2026-05-17
- Commit: local
- Objective: generate deterministic target-area scenario tables and a provenance manifest from the frozen Tschamut Balfrin target-area contract, committed source-zone metadata, release-point metadata, and conditional source-scenario policy without introducing annual-frequency semantics.
- Files changed: `scripts/generate_balfrin_target_area_scenario_tables.py`, `scripts/generate_balfrin_target_area_demo_handoff.py`, `tests/test_balfrin_target_area_scenario_tables.py`, `tests/test_balfrin_target_area_demo_handoff.py`, `docs/public_real_site_geodata_preparation.md`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added a target-area scenario-table wrapper that replays the frozen Tschamut contract into the committed deterministic scenario table, writes a matching manifest, and keeps the conditional-only boundary explicit.
  - Exposed the scenario-table materialization command and output paths through the frozen target-area handoff so the Balfrin bundle now points at the same deterministic provenance trail.
  - Added focused regression coverage for the default frozen inputs, a synthetic contract-backed target-area replay, the blocked-missing-input path, and the handoff integration hook.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_target_area_scenario_tables tests.test_balfrin_target_area_demo_handoff`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_tschamut_block_scenario_table_generation`
- Result/status: implemented_fixture_backed
- Boundaries: no block-population fitting, no annual-frequency semantics, no physics changes, and no operational claim.
- Next task: `TB-166`

### TB-166: Build Target-Area Balfrin Submission Package
- Date: 2026-05-17
- Commit: local
- Objective: build the unlaunched Balfrin submission package for the frozen Tschamut target-area demonstration contract without submitting a job.
- Files changed: `scripts/submit_balfrin_probe.py`, `docs/balfrin_probe_slurm_driver.md`, `tests/test_balfrin_probe_driver.py`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Changed the generated Balfrin submission package status from `blocked_unlaunched` to `deferred_pending_authorization` so the handoff now matches the task's explicit package-status requirement.
  - Regenerated the ignored target-area submission package under `validation/private/tschamut_public_pilot/balfrin_submission_package_v1` with the frozen Tschamut probe manifest, SBATCH script, command manifest, stop/resume notes, and metrics collection command ready for inspection.
  - Removed TB-166 from the active backlog after verifying the package generation path and preserving the no-submission boundary.
- Checks run:
  - `PYENV_VERSION=system uv run python scripts/submit_balfrin_probe.py validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml --generate-only --run-root validation/private/tschamut_public_pilot/balfrin_submission_package_v1 --run-id tschamut_public_balfrin_target_area_demo_v1 --partition postproc --time 00:30:00 --nodes 1 --ntasks 1 --cpus-per-task 16`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_probe_driver`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
- Result/status: implemented_measured
- Boundaries: no Balfrin job submission, no scale-up authorization, no distributed execution, and no generated artifact commit.
- Next task: `TB-167`

### TB-167: Execute Authorized Target-Area Balfrin Probe

- Date: 2026-05-17
- Commit: `5f169f4`
- Objective: determine whether the frozen target-area Balfrin probe could be launched, or else record the exact unresolved gate without submitting a job.
- Files changed: `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Verified that the frozen target-area contract at `validation/pilot_runs/tschamut_public_balfrin_target_area_demo_v1.yaml` is only a read-only handoff and explicitly states that no job submission is authorized by the record.
  - Preserved the unlaunched Balfrin submission-package state from TB-166 at `validation/private/tschamut_public_pilot/balfrin_submission_package_v1` and did not submit a job or materialize any measured run root.
  - Removed TB-167 from the active backlog and recorded this blocked execution report instead of fabricating execution evidence.
- Checks run:
  - `PYENV_VERSION=system uv run python scripts/print_agent_task_context.py --task TB-167 --format json`
  - `rg -n "^### TB-167:" docs/task_backlog.md`
  - `sed -n '/^### TB-167:/,/^### TB-168:/p' docs/task_backlog.md`
  - `sed -n '1,260p' validation/pilot_runs/tschamut_public_balfrin_target_area_demo_v1.yaml`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_target_area_demo_contract tests.test_balfrin_probe_driver`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
  - `git status --short`
- Result/status: blocked
- Boundaries: no Balfrin submission, no measured run, no scale-up authorization, no distributed execution, and no operational or physical-probability claim.
- Next task: `TB-168`

### TB-168: Execute Authorized Target-Area Balfrin Probe

- Date: 2026-05-17
- Commit: local
- Objective: submit the single authorized bounded Balfrin probe for the frozen Tschamut target-area contract, or record the precise scheduler/runtime gate if the remote environment could not support that one submission.
- Files changed: `validation/pilot_runs/tschamut_public_balfrin_target_area_demo_v1.yaml`, `docs/balfrin_probe_slurm_driver.md`, `tests/test_balfrin_target_area_demo_contract.py`, `docs/agent_work_log.md`
- Implementation summary:
  - Fixed the Balfrin handoff path assumption: the live checkout is `/users/olifu/work/rust_rockfall`, while `/scratch/mch/olifu/rust_rockfall/...` is for generated run roots and caches.
  - Fast-forwarded the Balfrin checkout to `0f55940`, generated the authorized submission package, and consumed the single TB-168 submission authorization exactly once.
  - Submitted SLURM job `4329024` on `postproc`; it completed with `COMPLETED`, exit `0:0`, and SLURM elapsed time `00:00:43`.
  - Collected the probe metrics under `/scratch/mch/olifu/rust_rockfall/probes/tschamut_public_balfrin_target_area_demo_v1/authorized_tb168_20260517`.
  - Measured outputs: `output_file_count=58`, `output_bytes=192350243`, collector wall time `12.611904342891648` seconds, conditional curve rows `729600`, trajectory decisions `executed: 4`, reducer decisions `executed: 2` and `reused_completed_state: 2`.
  - Metrics completeness remains a downstream TB-169 gap: peak memory and split validation/hazard output counts/bytes are still missing from the current metrics contract.
- Checks run:
  - `PYENV_VERSION=system uv run python scripts/print_agent_task_context.py --task TB-168 --format json`
  - `rg -n "^### TB-168:" docs/task_backlog.md`
  - `sed -n '27,80p' docs/task_backlog.md`
  - `sed -n '1,220p' validation/pilot_runs/tschamut_public_balfrin_target_area_demo_v1.yaml`
  - `sed -n '1,260p' scripts/submit_balfrin_probe.py`
  - `sed -n '1,260p' scripts/collect_balfrin_probe_metrics.py`
  - `sed -n '1,260p' docs/balfrin_probe_slurm_driver.md`
  - `sed -n '1,260p' scripts/summarize_balfrin_evidence_bundle.py`
  - `PYENV_VERSION=system uv run python scripts/check_balfrin_tschamut_readiness.py validation/pilot_runs/tschamut_public_balfrin_target_area_demo_v1.yaml --format json`
  - `ssh balfrin 'set -euo pipefail; cd /scratch/mch/olifu/rust_rockfall/main; git pull --ff-only origin main; git status --short --branch; test -f validation/pilot_runs/tschamut_public_balfrin_target_area_demo_v1.yaml; test -f validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml; test -f scripts/submit_balfrin_probe.py; test -d /scratch/mch/olifu/rust_rockfall/probes/tschamut_public_balfrin_target_area_demo_v1/authorized_tb168_20260517 && echo run_root_exists=1 || echo run_root_exists=0'`
  - `ssh balfrin 'set -euo pipefail; pwd; ls /scratch || true; find /scratch -maxdepth 3 -type d -name .git 2>/dev/null | sed -n "1,20p"; find /scratch -maxdepth 4 -type d -path "*/rust_rockfall/*" 2>/dev/null | sed -n "1,40p"'`
  - `ssh balfrin 'set -euo pipefail; for d in /scratch/mch/jkeiser /scratch/mch/jkeiser/rust_rockfall /scratch/mch/jkeiser/rust_rockfall/main /scratch/mch/jkeiser/rust_rockfall/probes /scratch/mch/jkeiser/rust_rockfall/probes/tschamut_public_balfrin_target_area_demo_v1 /scratch/mch/jkeiser/rust_rockfall/probes/tschamut_public_balfrin_target_area_demo_v1/authorized_tb168_20260517; do if [ -e "$d" ]; then printf "exists %s\n" "$d"; else printf "missing %s\n" "$d"; fi; done'`
  - `ssh balfrin 'set -euo pipefail; cd /users/olifu/work/rust_rockfall; git pull --ff-only origin main; git status --short --branch; git rev-parse HEAD; test -f validation/pilot_runs/tschamut_public_balfrin_target_area_demo_v1.yaml && echo contract=present'`
  - `ssh balfrin 'set -euo pipefail; cd /users/olifu/work/rust_rockfall; PYENV_VERSION=system uv run python scripts/check_balfrin_tschamut_readiness.py validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml --format json'`
  - `ssh balfrin 'set -euo pipefail; cd /users/olifu/work/rust_rockfall; PYENV_VERSION=system uv run python scripts/submit_balfrin_probe.py validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml --run-root /scratch/mch/olifu/rust_rockfall/probes/tschamut_public_balfrin_target_area_demo_v1/authorized_tb168_20260517 --run-id tschamut_public_balfrin_target_area_demo_v1 --partition postproc --time 00:30:00 --nodes 1 --ntasks 1 --cpus-per-task 16 --generate-only'`
  - `ssh balfrin 'set -euo pipefail; cd /users/olifu/work/rust_rockfall; PYENV_VERSION=system uv run python scripts/submit_balfrin_probe.py validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml --run-root /scratch/mch/olifu/rust_rockfall/probes/tschamut_public_balfrin_target_area_demo_v1/authorized_tb168_20260517 --run-id tschamut_public_balfrin_target_area_demo_v1 --partition postproc --time 00:30:00 --nodes 1 --ntasks 1 --cpus-per-task 16 --submit'`
  - `ssh balfrin 'sacct -j 4329024 --format=JobID,JobName%30,State,ExitCode,Elapsed,MaxRSS,ReqMem,NCPUS -P'`
  - `ssh balfrin 'set -euo pipefail; cd /users/olifu/work/rust_rockfall; PYENV_VERSION=system uv run python scripts/submit_balfrin_probe.py --collect --run-root /scratch/mch/olifu/rust_rockfall/probes/tschamut_public_balfrin_target_area_demo_v1/authorized_tb168_20260517; PYENV_VERSION=system uv run python scripts/collect_balfrin_probe_metrics.py --run-root /scratch/mch/olifu/rust_rockfall/probes/tschamut_public_balfrin_target_area_demo_v1/authorized_tb168_20260517 --output-json /scratch/mch/olifu/rust_rockfall/probes/tschamut_public_balfrin_target_area_demo_v1/authorized_tb168_20260517/balfrin_probe_metrics.json'`
- Result/status: implemented_measured
- Boundaries: exactly one Balfrin submission was issued under the TB-168 authorization; no second submission attempt, no scale-up authorization, and no operational or physical-probability claim.
- Next task: `TB-169`

### TB-169: Collect Target-Area Balfrin Metrics Completeness

- Date: 2026-05-17
- Commit: `0c1c75c`
- Objective: collect and classify the measured Balfrin run-root metrics into a deterministic JSON/text completeness report without fabricating missing memory or split-output evidence.
- Files changed: `scripts/summarize_balfrin_probe_metrics_report.py`, `tests/test_balfrin_probe_metrics_report.py`, `docs/balfrin_single_job_execution_sufficiency.md`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added a dedicated Balfrin metrics report helper that wraps the measured probe summary, renders JSON/text artifacts, and emits an explicit blocked missing-run-root report when the run root is absent.
  - Classified the measured target-area run with mandatory measured metrics, mandatory blocked metrics, ancillary unavailable metrics, and deterministic next-run-required metrics from the preserved collector output.
  - Materialized `balfrin_probe_metrics_report_v1.json` and `balfrin_probe_metrics_report_v1.txt` in `validation/private/tschamut_public_pilot/balfrin_probe_metrics_v1` from the preserved measured summary for review.
  - Added focused tests for the live-run-like classification, the blocked missing-run-root case, and the artifact-writing CLI path; also repaired the stale TB-129 work-log commit reference so repository consistency checks pass.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_probe_metrics_report`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_probe_driver.BalfrinProbeDriverTests.test_collect_probe_metrics_parses_synthetic_outputs tests.test_balfrin_probe_driver.BalfrinProbeDriverTests.test_collect_probe_metrics_reports_blocked_incomplete_root tests.test_balfrin_evidence_bundle.BalfrinEvidenceBundleTests.test_current_report_is_measured_and_tracks_section_provenance`
  - `PYENV_VERSION=system uv run python scripts/summarize_balfrin_probe_metrics_report.py --evidence-json /tmp/balfrin_tb169_live_metrics.json --artifact-dir validation/private/tschamut_public_pilot/balfrin_probe_metrics_v1`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
- Result/status: implemented_measured
- Boundaries: no fabricated measured metrics, no new run, no scale-up authorization, and no operational, physical-probability, or annual-frequency claim.
- Next task: `TB-170`

### TB-170: Build Target-Area Evidence Bundle

- Date: 2026-05-17
- Commit: `7132231`
- Objective: compose the target-area Balfrin evidence into one deterministic JSON/text bundle with explicit section provenance.
- Files changed: `scripts/summarize_balfrin_target_area_evidence_bundle.py`, `tests/test_balfrin_target_area_evidence_bundle.py`, `docs/current_maturity_snapshot.md`, `docs/task_backlog.md`
- Implementation summary:
  - Added a target-area evidence bundle helper that combines the frozen handoff report, the preserved probe-metrics report, and the measured canonical bundle.
  - Classified the target-area sections as unavailable, blocked, and measured so the review artifact does not collapse provenance boundaries.
  - Added focused tests for the live mixed-provenance report, fixture-backed overrides, blocked missing-inputs behavior, and artifact writing.
  - Updated the maturity snapshot and removed TB-170 from the active backlog.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_target_area_evidence_bundle tests.test_balfrin_evidence_bundle.BalfrinEvidenceBundleTests.test_current_report_is_measured_and_tracks_section_provenance`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
- Result/status: implemented_measured
- Boundaries: no operational claim, no physical-credibility upgrade, no generated-output commit, and no annual-frequency semantics.
- Next task: `TB-171`

### TB-171: Produce Target-Area GIS And COG Scope Audit

- Date: 2026-05-17
- Commit: `local`
- Objective: audit the committed target-area GIS package against a scratch COG conversion, report layer parity and missing layers, and keep the target-area demonstration boundaries explicit.
- Files changed: `scripts/summarize_balfrin_target_area_gis_cog_scope.py`, `tests/test_balfrin_target_area_gis_cog_scope.py`, `docs/public_real_site_geodata_preparation.md`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added a dedicated target-area GIS/COG scope helper that composes the committed target package audit, an optional scratch COG conversion, and the frozen handoff scope summary.
  - Classified the current measured target package as COG-blocked on the committed root, while the scratch conversion reports full-scope parity with zero omitted or extra layers.
  - Kept the demo-usability and non-operational boundaries explicit so the report stays diagnostic rather than operational.
  - Added focused tests for the full-scope scratch conversion path and the blocked missing-conversion path.
  - Updated the geodata-preparation documentation to point at the new target-area scope audit helper.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_target_area_gis_cog_scope tests.test_gis_cog_package_readiness`
  - `PYENV_VERSION=system uv run python scripts/summarize_balfrin_target_area_gis_cog_scope.py --artifact-root hazard/results/tschamut_public_pilot/target_gate_v1 --converted-package-root /tmp/tb171_target_gate_v1_cog_export --format json`
  - `PYENV_VERSION=system uv run python scripts/summarize_balfrin_target_area_gis_cog_scope.py --artifact-root hazard/results/tschamut_public_pilot/target_gate_v1 --converted-package-root /tmp/tb171_target_gate_v1_cog_export --format text`
- Result/status: implemented_measured
- Boundaries: no operational GIS claim, no QGIS sign-off claim, no generated raster commit, no risk/exposure/vulnerability semantics, and the committed target root remains distinct from the scratch COG proof.
- Next task: `TB-172`

## TB-172 Target-Area Spatial Uncertainty And Stability

- Date: 2026-05-17
- Commit: `local`
- Objective: produce a target-area spatial uncertainty and stability summary, or report why it is unavailable, with persistent/unstable/support-nodata/magnitude-sensitive region language kept conservative.
- Files changed: `docs/archive/balfrin_target_area_spatial_uncertainty_stability_report.md`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added a standalone blocked-artifacts report for the frozen target-area Balfrin demo that states the current uncertainty/stability/hotspot summaries are unavailable.
  - Recorded the exact blockers: the preserved probe run root is missing locally, the probe metrics helper returns `blocked_missing_run_root`, the target-area handoff is `template_only`, and the GIS/COG scope remains `blocked_missing_products`.
  - Kept the report boundary language aligned with the existing Tschamut summaries and added evidence-bundle integration notes so the target-area bundle can cite the report without treating canonical measured evidence as target-area uncertainty evidence.
  - Removed TB-172 from the active backlog.
- Checks run:
  - `PYENV_VERSION=system uv run python scripts/summarize_balfrin_probe_metrics_report.py --run-root /scratch/mch/olifu/rust_rockfall/probes/tschamut_public_balfrin_target_area_demo_v1/authorized_tb168_20260517 --format json`
  - `PYENV_VERSION=system uv run python scripts/summarize_balfrin_target_area_evidence_bundle.py --format json`
  - `PYENV_VERSION=system uv run python scripts/summarize_balfrin_target_area_gis_cog_scope.py --format json`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_target_area_evidence_bundle tests.test_balfrin_target_area_gis_cog_scope`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
- Result/status: implemented_blocked_report
- Boundaries: no closure upgrade by assertion, no operational hazard-map claim, no physical probability claim, no annual-frequency semantics, and no target-area uncertainty was inferred from a missing run root.
- Next task: `TB-173`

### TB-173: Interpret Target-Area Closure And Scientific Meaning

- Date: 2026-05-17
- Commit: `82f61e7`
- Objective: Generate a deterministic target-area conditional diagnostic interpretation with explicit execution, uncertainty, GIS, output, and physical-credibility boundaries.
- Files changed: `scripts/summarize_balfrin_target_area_interpretation.py`, `tests/test_balfrin_target_area_interpretation.py`, `docs/task_backlog.md`
- Implementation summary:
  - Added a new target-area interpretation helper that composes the target-area evidence bundle, GIS/COG scope, same-scale closure baseline, same-scale diagnostic baseline, and physical-credibility evidence into one sectioned report.
  - Kept the report conservative: the target-area run remains mixed provenance, the diagnostic is not accepted, and the baseline comparison explicitly states that the current Tschamut/Balfrin boundary is unchanged.
  - Added focused tests for override-driven report synthesis, text/JSON artifact generation, and explicit blocked-input behavior; also materialized the small ignored JSON/text report bundle under `validation/private/tschamut_public_pilot/balfrin_target_area_interpretation_v1/`.
- Checks run: `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_target_area_interpretation -q`, `git diff --check`, `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`, `scripts/git-hooks/pre-commit`
- Result/status: completed
- Boundaries: no operational claim, no physical-credibility upgrade, no annual-frequency semantics, and no scale-up authorization.
- Next task: `TB-174`

### TB-174: Demonstrate Target-Area Restartability Or Preserve Blocked Status

- Date: 2026-05-17
- Commit: local
- Objective: record the live target-area Balfrin interruption/resume proof already captured in the restartability recovery report, keep the evidence-bundle integration intact, and remove TB-174 from the active backlog without inventing a new run.
- Files changed: `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Confirmed the target-area restartability report already carries measured live interruption/resume provenance, including resume timing, reused reducer state, executed trajectory work, and artifact-continuity notes.
  - Verified the evidence-bundle helper and its focused tests still recognize restartability fields without treating fixture-backed evidence as a live proof.
  - Removed TB-174 from the active backlog and recorded the measured restartability status in this work log instead of rerunning or resubmitting Balfrin.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_evidence_bundle -q`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_restartability_recovery -q`
- Result/status: implemented_measured
- Boundaries: no new Balfrin job was submitted, no cancellation was performed, no distributed execution or scale-up claim was introduced, and no fixture-backed recovery was presented as live evidence.
- Next task: `TB-175`

### TB-175: Update Target-Area Runtime And Swiss-Wide Scaling Envelope

- Date: 2026-05-17
- Commit: `da2ce84`
- Objective: recompute the Swiss-wide execution envelope from the measured target-area evidence and record the resulting no-go planning labels without authorizing scale-up.
- Files changed: `docs/balfrin_single_job_execution_sufficiency.md`, `docs/task_backlog.md`
- Implementation summary:
  - Added a compact Swiss-wide envelope note to the Balfrin sufficiency doc using the current 26-AOI projection from `scripts/estimate_swiss_wide_execution_envelope.py`.
  - Recorded the no-go extrapolation labels and the measured runtime, storage, file-count, and memory bands in the target-area evidence narrative.
  - Removed TB-175 from the active backlog after recomputing the envelope from current evidence.
- Checks run: `PYENV_VERSION=system uv run python -m unittest tests.test_swiss_wide_execution_envelope -q`, `PYENV_VERSION=system uv run python scripts/estimate_swiss_wide_execution_envelope.py --format json --aoi-count 26 --release-zone-count 10 --trajectory-count 6`, `PYENV_VERSION=system uv run python scripts/summarize_balfrin_single_job_execution.py`, `git diff --check`, `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`, `scripts/git-hooks/pre-commit`, `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
- Result/status: completed
- Boundaries: no distributed execution, no Swiss-wide run, no scale-up authorization, and no operational claim.
- Next task: `TB-176`

### TB-176: Produce Target-Area Management Demonstration Package

- Date: 2026-05-17
- Commit: `local`
- Objective: assemble a compact management-facing package that explains the target-area Balfrin demonstration, evidence, limits, scaling implication, and next decision without inventing new evidence or authorizing a larger execution mode.
- Files changed: `scripts/summarize_balfrin_management_demo_package.py`, `tests/test_balfrin_management_demo_package.py`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Extended the Balfrin management package helper so the generated JSON/text package now includes explicit scaling and next-decision sections alongside runtime, replay, restartability, GIS scope, uncertainty, and claim-boundary evidence.
  - Tightened the scientific-meaning summary to keep the diagnostic boundary explicit and to state that the package is not an operational or physical-credibility result.
  - Added focused tests for the new scaling implication and recommended next authorized step, while keeping fixture-backed override coverage and blocked-input coverage in place.
  - Removed TB-176 from the active backlog after producing the management-facing package.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_management_demo_package -v`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
  - `git status --short`
- Result/status: implemented_measured
- Boundaries: no marketing overclaim, no operational claim, no annual-frequency claim, no physical credibility upgrade, no distributed-execution authorization, and no new Balfrin job submission.
- Next task: `TB-177`

### TB-177: Prepare Second-Site Real-Context Acquisition Execution Plan

- Date: 2026-05-17
- Commit: local
- Objective: turn the Chant Sura real-context staging checklist into a concrete operator execution plan with exact roots, metadata fields, verifier commands, stop conditions, and a no-download fallback report.
- Files changed: `docs/chant_sura_fluelapass_real_context_acquisition_decision.md`, `docs/swisstopo_data_strategy.md`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Expanded the Chant Sura decision pack into an operator-facing execution plan that distinguishes the stage, defer, and optional rows and names the exact verification path for each row.
  - Corrected the public-geodata cache manifest path to the contract root under `data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/public_geodata_cache_manifest.yaml` and documented the cache-verifier fields shared by the deferred public-context rows.
  - Added a no-download fallback report that keeps the response metadata-only when credentials or local files are missing, and aligned the swisstopo strategy note with the execution-plan location.
  - Removed TB-177 from the active backlog so the queue no longer advertises the completed task.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_chant_sura_real_context_readiness_gate -q`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
- Result/status: implemented_measured
- Boundaries: no downloads, no second-site ensemble, no synthetic evidence upgrade, no operational claim, and no change to the public-context defer boundary.
- Next task: `TB-178`

### TB-178: Define Physical Evidence Acquisition Pack For Target Area

- Date: 2026-05-17
- Commit: local
- Objective: package the target-area physical-credibility gaps into a concrete acquisition checklist with dataset roles, required geometry/provenance fields, and blocked-status separation for benchmark intake, calibration, and source-frequency evidence.
- Files changed: `docs/target_area_physical_evidence_acquisition_pack.md`, `docs/current_maturity_snapshot.md`, `docs/tschamut_public_conditional_pilot_gate_report.md`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added a target-area physical evidence acquisition pack that spells out the observed runout/deposition, release-zone, block-population, source-frequency, and calibration-separation acquisition steps without treating any of them as already validated evidence.
  - Added a dataset-role table with the required geometry/provenance fields and claim-boundary mapping so the acquisition request stays tied to concrete record shapes instead of broad status labels.
  - Added an explicit blocked-status summary that separates benchmark intake, calibration, source-frequency, and block-population evidence, and linked the pack from the maturity snapshot and gate report.
  - Removed TB-178 from the active backlog after defining the pack.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_observed_runout_deposition_intake_contract tests.test_validation_calibration_evidence_gaps -v`
  - `PYENV_VERSION=system uv run python scripts/summarize_observed_runout_deposition_intake_contract.py --format json >/tmp/tb178_observed_runout_contract.json`
  - `PYENV_VERSION=system uv run python scripts/map_physical_credibility_evidence_requirements.py --format json >/tmp/tb178_physical_requirements.json`
  - `PYENV_VERSION=system uv run python scripts/assess_validation_calibration_evidence_gaps.py --format json >/tmp/tb178_gap_report.json`
- Result/status: implemented_fixture_backed
- Boundaries: no calibration was performed, no validation evidence was fabricated, no annual-frequency or physical-probability claim was added, and no operational or risk/exposure/vulnerability claim was introduced.
- Next task: `TB-179`

### TB-179: Refill Or Close Post-Demonstration Backlog

- Date: 2026-05-17
- Commit: local
- Objective: reassess the post-demonstration state and decide whether the active queue should be refilled or left empty until new evidence justifies another worker-sized task.
- Files changed: `docs/current_maturity_snapshot.md`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Confirmed the post-demonstration backlog should stay empty for now rather than being padded with speculative follow-on work.
  - Updated the maturity snapshot to state that the active backlog is empty after TB-178 and that `backlog_refill_needed=true` is the current worker-context state.
  - Replaced the TB-179 placeholder in the active backlog with a concise refill-needed note so the queue no longer advertises a fake executable task.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_agent_task_context tests.test_repo_consistency_claim_hygiene -q`
  - `PYENV_VERSION=system uv run python scripts/print_agent_task_context.py --format json`
  - `rg -n "^### TB-[0-9]{3}:" docs/task_backlog.md`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
  - `git status --short`
- Result/status: implemented_blocked_report
- Boundaries: no scientific or execution task was launched, no Balfrin job was submitted, and no claim-boundary or roadmap expansion was introduced without measured evidence.
- Next task: backlog refill needed; see `docs/task_backlog.md`.

### TB-181: Automated Release-Zone Candidate Sweep On Real Terrain

- Date: 2026-05-17
- Commit: local
- Objective: run deterministic release-zone candidate generation on the staged Tschamut real-terrain crop with scratch-root outputs, measured runtime/output accounting, and an explicit multi-zone stress-test readiness signal.
- Files changed: `scripts/plan_terrain_release_zone_candidates.py`, `scripts/summarize_balfrin_target_area_candidate_stability.py`, `tests/test_balfrin_target_area_candidate_stability.py`, `docs/current_maturity_snapshot.md`, `docs/swisstopo_data_strategy.md`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added deterministic component-area distribution statistics to the terrain candidate product bundle so emitted scratch-root polygons carry an explicit area distribution for the candidate components.
  - Wrapped the frozen target-area candidate stability helper with a measured real-terrain sweep summary that records candidate count/area, slope and terrain thresholds, stable-versus-sensitive classes, runtime, output counts, and an explicit multi-zone scenario-generation readiness classification.
  - Added focused regressions for deterministic output shape, blocked-missing-input behavior from a temporary repo root, and the new sweep measurements.
  - Updated the maturity snapshot and swisstopo data strategy to mention the measured real-terrain sweep and its runtime/output evidence, then removed TB-181 from the active backlog.
- Checks run:
  - `PYENV_VERSION=system uv run python -m py_compile scripts/plan_terrain_release_zone_candidates.py scripts/summarize_balfrin_target_area_candidate_stability.py tests/test_balfrin_target_area_candidate_stability.py`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_target_area_candidate_stability -v`
- Result/status: implemented_measured
- Boundaries: no release-zone validation claim, no threshold tuning, no field-evidence claim, no operational release-zone claim, no Balfrin job submission, and no generated GIS or raster outputs committed.
- Next task: `TB-182`

### TB-182: Large Deterministic Scenario Table Generation Stress Test

- Date: 2026-05-17
- Commit: `6547e90`
- Objective: generate a deterministic stress-test scenario table from candidate release-point rows, measure cardinality/runtime/storage pressure, and report TB-183 planning-input readiness.
- Files changed: `scripts/generate_candidate_source_zone_scenarios.py`, `tests/test_candidate_source_zone_scenario_stress.py`, `docs/task_backlog.md`
- Implementation summary:
  - Added a scratch-root-only candidate source-zone stress helper that expands release-point candidates across the frozen Tschamut block-family policy and writes a manifest-rich scenario table plus bounded report.
  - Recorded scenario cardinality summaries by candidate, source-zone family, block family, and scenario-family template, along with runtime and storage measurements and an explicit first-bottleneck report.
  - Added focused regressions for deterministic manifest/row summaries and fail-closed missing-input handling, then removed TB-182 from the active backlog.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_candidate_source_zone_scenario_stress -v`
  - `PYENV_VERSION=system uv run python -m py_compile scripts/generate_candidate_source_zone_scenarios.py tests/test_candidate_source_zone_scenario_stress.py`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
- Result/status: implemented_measured
- Boundaries: no annual-frequency semantics, no physical probability semantics, no parameter tuning, no ensemble execution, and no generated large tables committed to git.
- Next task: `TB-183`

### TB-183: Multi-Release-Zone Balfrin Dry-Run Demonstration

- Date: 2026-05-17
- Commit: local
- Objective: build a bounded multi-release-zone Balfrin dry-run package that combines automatic release candidates, deterministic scenario planning, reduced-output pressure summaries, restartability checkpoints, and uncertainty-aware post-processing commands without authorizing live Balfrin execution.
- Files changed: `scripts/generate_balfrin_multi_release_zone_demo_handoff.py`, `tests/test_balfrin_multi_release_zone_demo_handoff.py`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added a scratch-root-only multi-release-zone handoff generator that composes the candidate sweep summary, a contract-derived deterministic-scenarios snapshot, bounded output and reducer pressure summaries, single-job restartability evidence, and staged uncertainty-aware post-processing commands into one reviewable package.
  - Kept the target-area handoff explicit in the command plan while preventing the package from materializing the target-area bundle, and normalized the volatile candidate sweep runtime so repeated dry-run generation is deterministic.
  - Added focused regressions for the JSON CLI smoke path, the package filesystem outputs, the staged command-plan shape, and the non-materialized target-area bundle boundary.
  - Removed TB-183 from the active backlog once the dry-run package and focused tests were in place.
- Checks run:
  - `PYENV_VERSION=system uv run python -m py_compile scripts/generate_balfrin_multi_release_zone_demo_handoff.py tests/test_balfrin_multi_release_zone_demo_handoff.py`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_multi_release_zone_demo_handoff -v`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
  - `git status --short`
- Result/status: implemented_fixture_backed
- Boundaries: no live Balfrin job submission, no scale-up authorization, no distributed execution, no operational claim, no generated artifacts committed, and no target-area bundle materialized by the package helper.
- Next task: `TB-184`

### TB-184: AOI-To-Prepared-Pilot End-To-End Automation

- Date: 2026-05-17
- Commit: local
- Objective: compose the AOI acquisition, cache verification, terrain preprocessing, release-candidate, scenario-generation, and portable command-plan helpers into one deterministic prepared-pilot report.
- Files changed: `scripts/plan_aoi_to_prepared_pilot_dry_run.py`, `tests/test_aoi_to_prepared_pilot_dry_run.py`, `docs/public_real_site_geodata_preparation.md`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added an explicit cache-verification report and workflow step to the AOI-to-prepared-pilot orchestrator so the report now composes product discovery, cache verification, terrain preprocessing, candidate generation, scenario planning, and command-plan output in one deterministic pass.
  - Threaded deterministic ignored-root layout records and blocked-missing-input inventories through the prepared-pilot summary and case-skeleton bundle so clean-checkout failures name the missing manifest, product, and metadata paths.
  - Extended the focused AOI-prepared-pilot tests with a verified synthetic cache-manifest path and a blocked missing-cache path, then updated the preparation documentation to match the new orchestration shape.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_public_geodata_cache_verifier tests.test_aoi_to_prepared_pilot_dry_run -v`
  - `PYENV_VERSION=system uv run python -m py_compile scripts/plan_aoi_to_prepared_pilot_dry_run.py tests/test_aoi_to_prepared_pilot_dry_run.py`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
- Result/status: implemented_measured
- Boundaries: no public-data download, no simulation run, no second-site ensemble, no operational claim, and no synthetic fixture was represented as public evidence.
- Next task: `TB-185`

### TB-185: Switzerland-Scale Runtime And Storage Projection

- Date: 2026-05-17
- Commit: local
- Objective: extend the Swiss-wide execution envelope helper into a deterministic multi-case planning report that covers 10-zone, 100-zone, regional, and Switzerland-scale envelopes with explicit no-go / defer / next-probe labels, rebuildability ratios, and bottleneck labels.
- Files changed: `scripts/estimate_swiss_wide_execution_envelope.py`, `tests/test_swiss_wide_execution_envelope.py`, `docs/balfrin_single_job_execution_sufficiency.md`, `docs/current_maturity_snapshot.md`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Extended the Swiss-wide envelope helper to load canonical single-job, target-area, and generated scenario-table evidence sources, then synthesize a four-case planning table for 10-zone, 100-zone, regional, and Swiss-wide envelopes.
  - Added explicit rebuildability-cost ratios and bottleneck labels for validation output, hazard output, reducer merge, manifest count, memory, and scheduler practicality, while keeping the helper deterministic and read-only with respect to the repository.
  - Added a focused synthetic regression for the canonical planning cases plus the existing measured-path regressions, updated the Balfrin sufficiency note and maturity snapshot, and removed TB-185 from the active backlog.
- Checks run:
  - `PYENV_VERSION=system uv run python -m py_compile scripts/estimate_swiss_wide_execution_envelope.py tests/test_swiss_wide_execution_envelope.py`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_swiss_wide_execution_envelope -v`
  - `PYENV_VERSION=system uv run python scripts/estimate_swiss_wide_execution_envelope.py --format json >/tmp/tb185_envelope.json`
- Result/status: implemented_measured
- Boundaries: projection-only; no scale-up authorization, no distributed execution, no Swiss-wide run, no annual-frequency or operational claim, and target-area evidence is reported as blocked rather than invented when the measured run root is unavailable.
- Next task: `TB-186`

### TB-186: Large-AOI GIS Packaging Stress Test

- Date: 2026-05-17
- Commit: local
- Objective: add a bounded large-AOI GIS/COG stress-test helper that reports standard-root package runtime, scratch conversion timing, raster count, manifest size, layer parity, and missing-layer summaries while keeping the standard-root COG-blocked state visible.
- Files changed: `scripts/summarize_large_aoi_gis_cog_stress_test.py`, `tests/test_large_aoi_gis_cog_stress_test.py`, `docs/pilot_gis_package.md`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added a standalone large-AOI stress-test helper that audits the standard package root, measures an ignored scratch conversion, and separates the standard-root COG-blocked status from the converted scratch package readiness.
  - Reported package runtime, COG conversion timing, raster count, manifest size, layer parity, missing-layer summaries, and a first GIS packaging bottleneck label without claiming operational readiness or writing generated rasters into the repository.
  - Added focused regressions for the standard-root COG-blocked plus scope-delta-ready path and the blocked-missing-input short-circuit, then updated the pilot GIS package documentation and removed TB-186 from the active backlog.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_large_aoi_gis_cog_stress_test`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_large_aoi_gis_cog_stress_test tests.test_gis_cog_package_readiness tests.test_same_scale_cog_package_conversion tests.test_balfrin_target_area_gis_cog_scope`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
- Result/status: implemented_fixture_backed
- Boundaries: no operational GIS product claim, no manual QGIS acceptance claim, no generated raster commit, and scratch COG readiness does not upgrade the standard root.
- Next task: `TB-187`

### TB-187: Multi-Zone Reducer And Merge Scaling Probe

- Date: 2026-05-17
- Commit: local
- Objective: build a deterministic scratch-root multi-zone reducer probe that measures chunk scaling, merge-order determinism, manifest size, file pressure, reducer wall time, and output-family bytes without relying on ignored live artifacts or a live Balfrin job.
- Files changed: `scripts/summarize_multi_zone_reducer_pressure.py`, `tests/test_multi_zone_reducer_pressure.py`, `docs/multi_zone_reducer_pressure_probe.md`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added a scratch-root probe helper that materializes a 12-zone multi-zone input set, writes manifest-shaped reducer and trajectory outputs, and summarizes chunk count, merge order, reducer wall time, manifest size, file count, and bytes by output family.
  - Classified the probe as `multi_zone_dry_run_blocked` because manifest pressure, output-family pressure, and reducer-runtime pressure are all visible in the scratch-root measurements, and surfaced the corresponding reducer-constraint recommendations for TB-183.
  - Added focused regressions for deterministic repeated materialization and requested release-zone-count propagation, then wrote a small markdown report that preserves the measured blocker/constraint set and removed TB-187 from the active backlog.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_multi_zone_reducer_pressure tests.test_bounded_reducer_runtime_scaling -v`
  - `PYENV_VERSION=system uv run python -m py_compile scripts/summarize_multi_zone_reducer_pressure.py tests/test_multi_zone_reducer_pressure.py`
  - `PYENV_VERSION=system uv run python scripts/summarize_multi_zone_reducer_pressure.py --materialize-root /tmp/rust_rockfall/tb187_multi_zone_probe --format json > /tmp/tb187_multi_zone_report.json`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
  - `git status --short`
- Result/status: implemented_measured
- Boundaries: no live Balfrin job, no distributed reducer, no MPI/GPU, no physics change, no operational hazard claim, and no generated heavy outputs committed.
- Next task: `TB-188`

### TB-188: Real Chant Sura Workflow Dry Run

- Date: 2026-05-17
- Commit: local
- Objective: build a deterministic Chant Sura / Flüelapass dry-run report that composes the real-context readiness gate, AOI preparation, release-candidate generation, scenario generation, command planning, and a permission-gated tiny bounded ensemble handoff without downloading public data or claiming operational readiness.
- Files changed: `scripts/summarize_chant_sura_fluelapass_dry_run_report.py`, `tests/test_chant_sura_fluelapass_workflow_dry_run_report.py`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added a read-only Chant Sura dry-run reporter that threads together the real-context readiness gate, the Chant Sura dry-run case-skeleton helper, the terrain release-candidate generator, the pragmatic scenario-plan helper, and the portable command-plan helper.
  - Classified the default checkout as `blocked_missing_inputs`, the staged fixture path as `ready_for_next_step`, and the tiny bounded ensemble handoff as permission-gated so the report stays fail-closed unless explicit permission is recorded.
  - Added focused regressions for the blocked path, the ready fixture path, and the permission-gated tiny handoff, then removed TB-188 from the active backlog.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_chant_sura_fluelapass_workflow_dry_run_report -v`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_chant_sura_real_context_readiness_gate tests.test_plan_terrain_release_zone_candidates tests.test_plan_pragmatic_release_plan tests.test_pilot_command_plan tests.test_chant_sura_fluelapass_workflow_dry_run_report -v`
  - `PYENV_VERSION=system uv run python -m py_compile scripts/summarize_chant_sura_fluelapass_dry_run_report.py tests/test_chant_sura_fluelapass_workflow_dry_run_report.py`
  - `PYENV_VERSION=system uv run python scripts/summarize_chant_sura_fluelapass_dry_run_report.py --format json`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
  - `git status --short`
- Result/status: implemented_fixture_backed
- Boundaries: no downloads, no second-site ensemble execution, no synthetic public-context evidence, no operational claim, no physical validation claim, and the tiny ensemble handoff remains permission-gated.
- Next task: `TB-189`

### TB-189: Release-Zone Candidate Stability And Sensitivity

- Date: 2026-05-17
- Commit: local
- Objective: measure deterministic stability of automatically generated release-zone candidates across slope-threshold, smoothing, terrain-resolution, and AOI-boundary perturbations, and surface stable, unstable, and heuristic-sensitive classifications with persistence metrics.
- Files changed: `scripts/plan_terrain_release_zone_candidates.py`, `scripts/summarize_balfrin_target_area_candidate_stability.py`, `docs/current_maturity_snapshot.md`, `docs/swisstopo_data_strategy.md`, `docs/task_backlog.md`, `tests/test_plan_terrain_release_zone_candidates.py`, `tests/test_balfrin_target_area_candidate_stability.py`, `docs/agent_work_log.md`
- Implementation summary:
  - Expanded the terrain-candidate sensitivity helper to sweep six deterministic variants: baseline, bounded slope thresholds, 3x3 smoothing, 2x2 coarsened/reexpanded resolution, and a one-cell AOI-boundary trim proxy.
  - Added an explicit sensitivity matrix, persistence metrics, and stable/unstable/heuristic-sensitive region classifications, then exposed them through the Balfrin target-area stability report and a scratch report JSON under the provided output root.
  - Kept the candidate product bundle GIS-readable, filtered the scratch stability report out of output-count measurements so repeated runs stay deterministic, and updated the maturity/data-strategy prose plus focused regressions to cover the new perturbation summaries and fail-closed missing-input behavior.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_plan_terrain_release_zone_candidates tests.test_balfrin_target_area_candidate_stability -v`
  - `PYENV_VERSION=system uv run python -m py_compile scripts/plan_terrain_release_zone_candidates.py scripts/summarize_balfrin_target_area_candidate_stability.py tests/test_plan_terrain_release_zone_candidates.py tests/test_balfrin_target_area_candidate_stability.py`
  - `PYENV_VERSION=system uv run python scripts/summarize_balfrin_target_area_candidate_stability.py --output-root /tmp/tb189_candidate_products --format json >/tmp/tb189_candidate_stability_report.json`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
  - `git status --short`
- Result/status: implemented_measured
- Boundaries: no release-zone validation, no threshold tuning for acceptance, no operational source-zone claim, no generated GIS outputs committed, and the sensitivity report remains a heuristic stability characterization only.
- Next task: `TB-190`

### TB-190: Full Balfrin Demonstration Evidence Package

- Date: 2026-05-17
- Commit: local
- Objective: build one deterministic Balfrin management package that separates measured, fixture-backed, blocked, and unavailable evidence, and answers whether the current architecture is plausibly extensible toward Swiss-wide workflows without turning that answer into an authorization.
- Files changed: `scripts/summarize_balfrin_management_demo_package.py`, `tests/test_balfrin_management_demo_package.py`, `docs/balfrin_single_job_execution_sufficiency.md`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Expanded the management package to include explicit AOI automation, release/scenario automation, blocked target-area probe metrics, the measured canonical target-area bundle, the measured physical-credibility gap report, and a dedicated Swiss-wide extension answer section.
  - Kept runtime, replay, restartability, GIS scope, uncertainty, scaling, and claim-boundary sections separate while preserving section-level provenance counts for measured, fixture-backed, unavailable, and blocked evidence.
  - Updated the focused regressions to pin the expanded section set, the management-facing no-go answer, and the deterministic regeneration command list, and removed TB-190 from the active backlog.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_management_demo_package tests.test_balfrin_target_area_evidence_bundle tests.test_balfrin_physical_credibility_evidence_gaps`
  - `PYENV_VERSION=system uv run python -m py_compile scripts/summarize_balfrin_management_demo_package.py tests/test_balfrin_management_demo_package.py`
  - `PYENV_VERSION=system uv run python scripts/summarize_balfrin_management_demo_package.py --run-root tests/fixtures/balfrin_probe_metrics_contract/complete_run_root --artifact-dir /tmp/balfrin_management_demo_package_v1 --format json`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
  - `git status --short --branch`
- Result/status: implemented_measured
- Boundaries: no marketing overclaim, no operational acceptance, no physical-credibility upgrade, no scale-up authorization, no annual-frequency semantics, and no generated heavy artifacts committed.
- Next task: `TB-191`

### TB-191: Balfrin Metrics And Run-Root Preservation Gate

- Date: 2026-05-17
- Commit: local
- Objective: define and test the Balfrin evidence-preservation gate that must pass before a future authorized live run can be treated as demonstration evidence.
- Files changed: `scripts/summarize_balfrin_probe_preservation_gate.py`, `tests/test_balfrin_probe_preservation_gate.py`, `docs/balfrin_single_job_execution_sufficiency.md`, `docs/balfrin_probe_slurm_driver.md`, `docs/archive/balfrin_target_area_spatial_uncertainty_stability_report.md`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added a dedicated read-only preservation-gate helper that combines the collected probe metrics with run-root file checks, required SLURM accounting fields, output-family summaries, and declared GIS artifact paths.
  - Classified complete, partial, and missing-run-root cases fail closed, with explicit missing-metric and missing-preserved-path reporting so a future live run is only treated as evidence when the contract is satisfied.
  - Updated the operator guidance in the Balfrin sufficiency note, SLURM driver, and target-area stability note so the preservation gate is called out as the evidence-preservation check rather than relying on the metrics report alone.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_balfrin_probe_preservation_gate tests.test_balfrin_probe_metrics_report`
  - `PYENV_VERSION=system uv run python -m py_compile scripts/summarize_balfrin_probe_preservation_gate.py tests/test_balfrin_probe_preservation_gate.py`
  - `PYENV_VERSION=system uv run python scripts/summarize_balfrin_probe_preservation_gate.py --run-root tests/fixtures/balfrin_probe_metrics_contract/complete_run_root --format json`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
  - `git status --short`
- Result/status: implemented_measured
- Boundaries: no live Balfrin submission, no scale-up authorization, no distributed execution, no operational claim, and no fabricated metrics.
- Next task: `TB-192`

### TB-192: Backlog And Command-Plan Reference Integrity Checker

- Date: 2026-05-17
- Commit: local
- Objective: add a fail-fast repository-consistency check that rejects stale active-backlog `Inspect first` paths and stale command-plan or handoff script references before the next worker starts.
- Files changed: `scripts/check_repo_consistency.py`, `docs/task_backlog.md`, `tests/test_repo_consistency_claim_hygiene.py`, `docs/agent_work_log.md`
- Implementation summary:
  - Added an active-backlog path audit that reads each active task's `Inspect first` list, allows only explicitly marked external or generated-scratch references to bypass repo resolution, and fails when a listed repository path no longer exists.
  - Added a command-plan and handoff reference audit that walks the emitted helper reports, validates real script references against tracked repository files, and skips template-only command entries so the current backlog remains clean.
  - Added focused regressions for the valid backlog case, a missing `Inspect first` path, and a stale script reference, then updated the backlog protocol note so future tasks keep their inspect-first paths resolvable.
- Checks run:
  - `PYENV_VERSION=system uv run python -m py_compile scripts/check_repo_consistency.py tests/test_repo_consistency_claim_hygiene.py`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_repo_consistency_claim_hygiene -v`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `git diff --check`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
  - `git status --short`
- Result/status: implemented_measured
- Boundaries: no task execution, no command-plan regeneration, no generated artifact commit, no broad documentation rewrite, and no scale-up or operational-claim change.
- Next task: `TB-193`

### TB-193: Clean-Checkout Reproducibility Blocked-Report Mode

- Date: 2026-05-17
- Commit: local
- Objective: add a deterministic clean-checkout mode that proves the same-scale readiness, Balfrin probe-metrics, Balfrin target-area bundle, and second-site public-geodata helpers fail closed when ignored local artifacts and mounted run roots are absent.
- Files changed: `scripts/summarize_clean_checkout_blocked_reports.py`, `tests/test_clean_checkout_blocked_reports.py`, `docs/balfrin_tschamut_pilot_runbook.md`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added a read-only clean-checkout summary helper that runs the selected readiness and evidence helpers against an isolated temporary root, reuses the existing blocked-report contracts, and emits a compact inventory of tracked, fixture-backed, ignored-local, and unavailable evidence.
  - Kept the same-scale helper on a temporary root with ignored output directories absent, forced the Balfrin probe-metrics helper to use a missing run root, and fed the second-site public-geodata preflight a clean-checkout config whose expected staged inputs all point at the isolated root.
  - Added focused regression coverage for the blocked helper statuses, the inventory categories, and the helper CLI artifact-writing path; documented the command sequence to run before treating local readiness as measured evidence.
- Checks run:
  - `PYENV_VERSION=system uv run python -m py_compile scripts/summarize_clean_checkout_blocked_reports.py tests/test_clean_checkout_blocked_reports.py`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_clean_checkout_blocked_reports -v`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
  - `git status --short`
- Result/status: implemented_blocked_report
- Boundaries: no public-data download, no Balfrin access requirement, no deletion of local ignored artifacts, no new evidence claim, and no generated heavy outputs committed.
- Next task: `TB-194`

### TB-194: Shared Python Workflow Utility Extraction

- Date: 2026-05-17
- Commit: local
- Objective: extract duplicated Python workflow helpers into one shared module so validator and workflow-script safety rules stop drifting apart.
- Files changed: `scripts/lib/__init__.py`, `scripts/lib/workflow_validation.py`, `scripts/validate_source_frequency_evidence.py`, `scripts/validate_block_release_probability_evidence.py`, `scripts/validate_scalable_conditional_target_gate.py`, `scripts/validate_scalable_conditional_execution.py`, `scripts/validate_physical_frequency_reducer_preconditions.py`, `scripts/validate_annual_physical_validation_calibration_review_gate.py`, `scripts/validate_public_real_site_conditional_pilot_run.py`, `tests/test_workflow_validation_helpers.py`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added a small shared `scripts/lib/workflow_validation.py` module with YAML/JSON loading, path resolution, text normalization, SHA-256 validation, `require_*` helpers, claim-boundary field checks, misleading-text scanning, and reusable status-message rendering.
  - Migrated six validator scripts plus the pilot-run validator to the shared helpers, keeping their CLI output and schema-specific validation logic intact while binding each script to its own exception type.
  - Added focused helper tests for loader, checksum, normalization, claim-boundary scan, and status rendering behavior; the existing validator regression tests continue to cover the accepted and rejected fixtures.
  - Kept schema-specific claim-boundary rules, target-gate policies, pilot-run command-plan assembly, and report checksum parsing intentionally script-local.
- Checks run:
  - `PYENV_VERSION=system uv run python -m py_compile scripts/lib/workflow_validation.py scripts/validate_source_frequency_evidence.py scripts/validate_block_release_probability_evidence.py scripts/validate_scalable_conditional_target_gate.py scripts/validate_scalable_conditional_execution.py scripts/validate_physical_frequency_reducer_preconditions.py scripts/validate_annual_physical_validation_calibration_review_gate.py scripts/validate_public_real_site_conditional_pilot_run.py tests/test_workflow_validation_helpers.py`
  - `PYENV_VERSION=system uv run python -m unittest -v tests.test_workflow_validation_helpers tests.test_source_frequency_evidence tests.test_block_release_probability_evidence tests.test_scalable_conditional_target_gate tests.test_scalable_conditional_execution tests.test_physical_frequency_reducer_preconditions tests.test_annual_physical_validation_calibration_review_gate tests.test_public_real_site_conditional_pilot_run`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
  - `git status --short`
- Result/status: implemented_measured
- Boundaries: bounded extraction only; no schema redesign, no claim-boundary behavior change, no mass migration of unrelated scripts, and no generated artifact commit.
- Next task: `TB-195`

### TB-195: Hazard-Layer Writer And Manifest Module Split

- Date: 2026-05-17
- Commit: local
- Objective: split the lowest-risk hazard-layer writer, manifest-entry, and report-rendering helpers out of `scripts/build_hazard_layers.py` without changing CLI behavior or generated schemas.
- Files changed: `scripts/build_hazard_layers.py`, `scripts/hazard_output_writers.py`, `scripts/hazard_output_manifests.py`, `scripts/hazard_output_reports.py`, `tests/test_hazard_output_helpers.py`, `docs/hazard_output_profile_contract.md`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added focused helper modules for shared file/checksum accounting, compact manifest-entry helpers, and HTML report rendering.
  - Updated the hazard builder to delegate those responsibilities while leaving reducer math, raster writers, probability normalization, output-profile defaults, and GIS/COG semantics unchanged.
  - Added direct helper tests for writer metadata/checksums, manifest metadata precedence and fallback hashing, and report rendering output accounting.
  - Documented the next safe split target as the remaining raster writer family, explicitly bounded to behavior-preserving extraction only.
- Checks run:
  - `PYENV_VERSION=system uv run python -m py_compile scripts/build_hazard_layers.py scripts/hazard_output_writers.py scripts/hazard_output_manifests.py scripts/hazard_output_reports.py tests/test_hazard_output_helpers.py`
  - `PYENV_VERSION=system uv run python -m unittest -v tests.test_hazard_output_helpers`
  - `PYENV_VERSION=system uv run python -m unittest -v tests.test_hazard_layers.HazardLayerTests.test_fixture_layers_are_reproducible_and_interpretable tests.test_hazard_layers.HazardLayerTests.test_default_grid_csv_export_is_enabled tests.test_hazard_layers.HazardLayerTests.test_hazard_manifest_includes_terrain_metadata_sidecar_provenance tests.test_hazard_layers.HazardLayerTests.test_pilot_gis_package_manifest_records_review_artifacts_and_boundaries`
  - `PYENV_VERSION=system uv run python -m unittest -v tests.test_hazard_layers tests.test_hazard_output_helpers`
- Result/status: implemented_measured
- Boundaries: no reducer redesign, no probability-semantics change, no output-profile default change, no large fixture regeneration, and no GIS/COG claim upgrade.
- Next task: `TB-196`

### TB-196: Explicit Missing-Data Validity Semantics In Validation Metrics

- Date: 2026-05-18
- Commit: local
- Objective: replace silent empty-input and malformed-summary fallbacks in validation metrics with explicit warnings and validity flags so missing evidence is not mistaken for a real zero-valued result.
- Files changed: `src/manifest.rs`, `src/validation.rs`, `src/validation/metric_math.rs`, `src/validation/metrics.rs`, `src/validation/runner.rs`, `tests/config_io_terrain.rs`, `docs/validation_data_schema.md`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added a warning path for missing observed deposition inputs so empty deposition sidecars no longer produce silent metric omissions.
  - Added a validity flag and error note to the stop-state summary manifest, and changed stop-state count-map aggregation to report malformed JSON instead of collapsing it into an empty aggregate.
  - Added focused regression tests for legitimate zero-valued metric handling, empty deposition-observation warnings, malformed stop-state count-map parsing, and existing observed-data validation flows.
  - Documented how consumers should interpret omitted metrics and invalid summary fields.
- Checks run:
  - `PYENV_VERSION=system CARGO_TARGET_DIR=/tmp/rust-rockfall-target cargo test cloud_metrics_handle_empty_and_symmetric_nearest_cases`
  - `PYENV_VERSION=system CARGO_TARGET_DIR=/tmp/rust-rockfall-target cargo test stop_state_summary_marks_malformed_count_maps_invalid`
  - `PYENV_VERSION=system CARGO_TARGET_DIR=/tmp/rust-rockfall-target cargo test --test config_io_terrain validation_warns_when_deposition_observations_are_missing -- --exact`
  - `PYENV_VERSION=system CARGO_TARGET_DIR=/tmp/rust-rockfall-target cargo test --test config_io_terrain validation_compares_observed_trajectory_shape_and_energy -- --exact`
  - `PYENV_VERSION=system CARGO_TARGET_DIR=/tmp/rust-rockfall-target cargo test --test config_io_terrain swissalti3d_terrain_class_pilot_writes_class_manifest -- --exact`
  - `PYENV_VERSION=system CARGO_TARGET_DIR=/tmp/rust-rockfall-target cargo test validation_reports_raw_and_significant_impact_counts_separately`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
  - `git status --short`
- Result/status: implemented_measured
- Boundaries: no metric retuning, no benchmark reinterpretation, no default physics change, and no broad validation-file refactor beyond the affected paths.
- Next task: `TB-197`

### TB-197: Python Execution Policy Normalization

- Date: 2026-05-18
- Commit: local
- Objective: normalize local Python and PyYAML guidance around the repository `uv` workflow while keeping CI support for `requirements-tools.txt`.
- Files changed: `README.md`, `docs/onboarding.md`, `scripts/check_repo_consistency.py`, PyYAML-dependent scripts under `scripts/`, `tests/test_repo_consistency_claim_hygiene.py`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Updated PyYAML dependency failures to point users at `PYENV_VERSION=system uv run python ...` and identify the CI `requirements-tools.txt` exception instead of recommending global pip installs.
  - Clarified the local-vs-CI Python policy in README and onboarding docs without changing dependency versions or CI installation behavior.
  - Added a repository-consistency check and focused regression test that reject restored global `python`/`python3 -m pip install PyYAML` guidance in Python scripts.
  - Confirmed `pyproject.toml` and `requirements-tools.txt` remain the synchronized dependency sources checked by repo consistency.
- Checks run:
  - `PYENV_VERSION=system uv run python -m py_compile $(git diff --name-only | rg '\.py$')`
  - `PYENV_VERSION=system uv run python -m unittest -v tests.test_repo_consistency_claim_hygiene.HazardClaimHygieneTests.test_python_tool_dependency_metadata_is_consistent tests.test_repo_consistency_claim_hygiene.HazardClaimHygieneTests.test_python_execution_policy_guidance_is_clean`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
- Result/status: implemented_measured
- Boundaries: no dependency upgrade, no removal of CI support for `requirements-tools.txt`, no environment installation, and no behavior change beyond dependency guidance and consistency enforcement.
- Next task: `TB-198`

### TB-198: Calibration Script Failure Diagnostics

- Date: 2026-05-18
- Commit: `0940321`
- Objective: harden calibration scripts so expected missing or empty inputs fail with stage-scoped diagnostics instead of index errors or opaque subprocess failures.
- Files changed: `calibration/README.md`, `scripts/run_tschamut_calibration.py`, `scripts/calibrate_scarring_impact.py`, `scripts/preprocess_scarring_real_data.py`, `tests/test_calibration_failure_diagnostics.py`
- Implementation summary:
  - Added explicit checks for empty calibration splits, empty parameter grids, missing split/deposition rows, missing significant impact events, and failed `cargo run` subprocesses.
  - Added temporary-fixture unit tests covering Tschamut calibration, scarring calibration, and scarring real-data preprocessing failure paths.
  - Updated the calibration README to keep these scripts classified as research diagnostics, not accepted calibration or physical-credibility evidence.
  - Worker completed code and push but missed backlog/work-log cleanup; this follow-up entry regularizes the task bookkeeping.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_calibration_failure_diagnostics`
  - `PYENV_VERSION=system uv run python -m unittest tests.test_validation_calibration_evidence_gaps`
  - `PYENV_VERSION=system uv run python -m py_compile scripts/run_tschamut_calibration.py scripts/calibrate_scarring_impact.py scripts/preprocess_scarring_real_data.py tests/test_calibration_failure_diagnostics.py`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
  - `git status --short`
- Result/status: implemented_measured
- Boundaries: no calibration run, no parameter selection change, no accepted calibration evidence, no model default change, and no annual/physical probability claim.
- Next task: `TB-199`

### TB-199: Runtime-Facing Panic Path Reduction

- Date: 2026-05-18
- Commit: `8a7b2fa`
- Objective: convert the highest-risk runtime-adjacent DEM and validation panic paths into structured errors while leaving compatibility/test wrappers bounded.
- Files changed: `src/terrain.rs`, `src/validation.rs`, `src/validation/runner.rs`
- Implementation summary:
  - Propagated DEM query failures through `ValidationError::Terrain` in observed-trajectory validation metrics instead of relying on panic-prone height access.
  - Changed shape-manifest assembly to return `ValidationError::Case` for missing block radius instead of panicking during run-manifest construction.
  - Added focused Rust tests for structured validation errors on malformed/out-of-bounds DEM queries and shape sidecar radius requirements.
  - Worker completed code and push but missed backlog/work-log cleanup; this follow-up entry regularizes the task bookkeeping.
- Checks run:
  - `cargo test --lib observed_trajectory_metrics_propagate_dem_query_errors`
  - `cargo test --lib shape_metadata_manifest_returns_case_error_when_block_radius_missing`
  - `cargo test --test terrain_edge_cases dem_try_height_returns_out_of_bounds_for_query_outside_grid`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
  - `git status --short`
- Result/status: implemented_measured
- Boundaries: no physics change, no public runtime promotion of `shape_contact_v0`, no sweeping refactor of all `expect` calls, and no change to analytic-test convenience behavior.
- Next task: `TB-200`

### TB-200: GitHub Python Test Clean-Checkout Stabilization

- Date: 2026-05-18
- Commit: `89181ac`
- Objective: Make the Python planning and evidence helpers return explicit blocked or fixture-backed metadata when ignored same-scale, Balfrin, or second-site artifacts are absent in clean-checkout runs.
- Files changed: `scripts/check_hazard_rebuild_output_profile.py`, `scripts/plan_balfrin_single_release_zone_case_dry_run.py`, `tests/test_balfrin_single_release_zone_case_plan_dry_run.py`, `tests/test_chant_sura_fluelapass_dry_run_case_skeleton.py`, `tests/test_hazard_rebuild_output_profile.py`, `tests/test_pilot_command_plan.py`
- Implementation summary:
  - Surfaced `blocked_missing_inputs` at the hazard-rebuild output-profile top level when any default profile manifest/root is missing, so the command plan no longer implies measured scope on a clean checkout.
  - Added a structured blocked report path to the Balfrin dry-run planner and covered it with a JSON CLI test that exercises missing committed inputs.
  - Staged a minimal AOI tile catalog in the Chant Sura test fixture, added a `/tmp` repo-root ready-path test, and added a blocked-missing-input CLI test for the same helper.
  - Extended the output-profile and command-plan tests so missing manifests stay explicit and bounded instead of silently inheriting measured metadata.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest -v tests.test_pilot_command_plan tests.test_swiss_wide_execution_envelope tests.test_balfrin_single_release_zone_case_plan_dry_run tests.test_chant_sura_fluelapass_dry_run_case_skeleton tests.test_hazard_rebuild_output_profile`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
- Result/status: implemented_measured
- Boundaries: no public-data download, no generated ignored-artifact commit, no fabricated measured evidence, no Balfrin access requirement, and no scale-up or operational claim.
- Next task: `TB-201`

### TB-201: Ignored-Artifact Dependency Audit For Python Tests

- Date: 2026-05-18
- Commit: `caf3902`
- Objective: add a repository-consistency audit that catches Python tests which hard-read ignored artifact roots without using committed fixtures, temporary fixtures, or explicit blocked-state expectations.
- Files changed: `scripts/check_repo_consistency.py`, `tests/test_repo_consistency_claim_hygiene.py`, `tests/test_balfrin_target_area_scenario_tables.py`, `tests/test_swiss_wide_execution_envelope.py`, `tests/test_tschamut_block_scenario_table_generation.py`, `tests/fixtures/tschamut_public_input/release_points_lv95.csv`, `tests/fixtures/tschamut_public_input/tschamut_public_scenario_table_v1.csv`, `tests/fixtures/tschamut_public_input/tschamut_public_source_zone_metadata_v1.yaml`, `docs/task_backlog.md`, `docs/agent_work_log.md`
- Implementation summary:
  - Added ignored-artifact dependency classification to repository consistency, including violations for new hard reads from `hazard/results`, `validation/private`, `data/processed/swisstopo`, and `/scratch` paths.
  - Added regression coverage for current classifications, hard-read rejection, and accepted temporary/tracked-fixture reads.
  - Moved scenario-table tests away from ignored Tschamut input roots by adding tracked fixture inputs under `tests/fixtures/tschamut_public_input`.
  - Reworked the Swiss-wide execution envelope smoke test to use mocked measured evidence rather than live local ignored artifacts.
  - Worker completed code and push but missed backlog/work-log cleanup; this follow-up entry regularizes the task bookkeeping.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest tests.test_repo_consistency_claim_hygiene tests.test_balfrin_target_area_scenario_tables tests.test_tschamut_block_scenario_table_generation tests.test_swiss_wide_execution_envelope`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
  - `git status --short`
- Result/status: implemented_measured
- Boundaries: no broad test rewrite, no deletion of local artifacts, no generated fixtures outside `tests/fixtures`, no scientific evidence reclassification, and no scale-up or operational claim.
- Next task: `TB-202`

### TB-202: CI Git History And Output-Root Portability Guard

- Date: 2026-05-18
- Commit: `4806402`
- Objective: Harden the Python CI path so work-log ancestry checks stay deterministic in full-history clones and Chant Sura dry-run output-root validation stays repo-aware when repositories live under `/tmp`.
- Files changed: `.github/workflows/ci.yml`, `docs/task_backlog.md`, `docs/agent_work_log.md`, `scripts/check_repo_consistency.py`, `scripts/generate_chant_sura_fluelapass_dry_run_case_skeleton.py`, `tests/test_repo_consistency_claim_hygiene.py`, `tests/test_chant_sura_fluelapass_dry_run_case_skeleton.py`
- Implementation summary:
  - Set the Python workflow checkout to `fetch-depth: 0` so repository-consistency ancestry checks have full history in CI.
  - Added shallow-clone detection to the work-log hygiene path and a regression test that simulates shallow history.
  - Tightened the Chant Sura dry-run output-root guard to reject repo-local paths even when the repository root itself is under `/tmp`, while still allowing `/tmp` scratch roots and the ignored validation root.
  - Added focused tests for allowed scratch roots, allowed ignored roots, and forbidden repository-local paths.
- Checks run:
  - `PYENV_VERSION=system uv run python -m unittest -v tests.test_repo_consistency_claim_hygiene tests.test_chant_sura_fluelapass_dry_run_case_skeleton`
  - `git diff --check`
  - `PYENV_VERSION=system uv run --with PyYAML python scripts/check_repo_consistency.py`
  - `scripts/git-hooks/pre-commit`
  - `find data/processed/swisstopo validation/private hazard/results validation/policies \( -path '*placeholder_second_site_v1*' -o -name '*placeholder*' \) -print`
- Result/status: completed
- Boundaries: no work-log history changes, no weakening of full-history hygiene, no generated artifact commit, and no expansion of allowed output roots beyond documented scratch/ignored locations.
- Next task: backlog refill needed
