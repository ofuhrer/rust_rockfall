# Task Backlog

Status: authoritative executable task backlog.

This file is intentionally compact. It should contain only the active TB queue,
the task template, and deferred non-goals. Detailed maturity framing lives in
`docs/current_maturity_snapshot.md`; completed TB history lives in
`docs/agent_work_log.md`.

Worker rule: when a task is completed and committed, remove it from this file.
Append completed TB work to the bottom of `docs/agent_work_log.md` using that
file's template. Record durable decisions in `docs/decision_log.md`.

Progress rule: each task should produce executable or measured progress, not
only labels, validators, or roadmap/status churn.

Orchestrator rule: execute active tasks sequentially by numeric order. Launch
one worker, verify clean `main` and task removal after it finishes, then continue
to the next task. Stop on any failure or dirty worktree; do not pre-generate
later prompts. Full sequential-loop guidance lives in
`docs/orchestration_strategy.md`.

## Active Tasks

_Active TB tasks remain below._

### TB-142: Close Balfrin Metrics Completeness Gaps

Goal: Convert remaining Balfrin ancillary metrics gaps into measured fields or
explicitly non-required blocked classifications.

Capability gap reduced: incomplete runtime/output evidence for management and
future scaling decisions.

Why this outranks alternatives: measured execution exists, but missing or
ambiguous peak-memory and split output metrics weaken the scaling argument.

Inspect first:

- `scripts/collect_balfrin_probe_metrics.py`
- `scripts/summarize_balfrin_evidence_bundle.py`
- `docs/balfrin_single_job_execution_sufficiency.md`
- `docs/current_maturity_snapshot.md`

Deliverables:

- Updated metrics report with mandatory, ancillary, measured, unavailable, and
  blocked fields clearly separated.
- Live Balfrin evidence where available, or a precise explanation of which
  scheduler/artifact fields cannot be recovered.
- Focused tests covering measured and unavailable ancillary metrics.

Definition of done:

- The canonical Balfrin evidence bundle no longer leaves the reader guessing
  whether a metric is missing accidentally, unavailable by design, or measured.

Boundaries: No new ensemble, no scale-up authorization, no operational claim,
and no substitution of fixture evidence for live measurements.

### TB-143: Unblock Bounded Next-Ensemble Metadata Contract

Goal: Fix the optional probabilistic metadata blocker that currently prevents a
small bounded next-ensemble probe from being evaluated cleanly.

Capability gap reduced: uncertainty/runtime frontier planning blocked by a
metadata-contract mismatch.

Why this outranks alternatives: the next scientific execution decision is
blocked by metadata plumbing rather than by a principled no-go result.

Inspect first:

- `scripts/summarize_bounded_next_ensemble_feasibility_probe.py`
- `scripts/summarize_balfrin_ensemble_frontier.py`
- `tests/fixtures/rebuildable_reduced_output/tschamut_public_target_gate_rebuildable_reduced_case.yaml`
- `tests/test_bounded_next_ensemble_feasibility_probe.py`

Deliverables:

- A robust feasibility helper that handles reduced-output fixtures without
  crashing or over-authorizing execution.
- A measured, deferred, or blocked status that explains exactly which metadata
  is required for the smallest useful probe.
- Regression tests for full, reduced, and missing metadata cases.

Definition of done:

- The bounded next-ensemble feasibility helper exits deterministically and
  produces a decision-quality report in clean checkout and live-artifact
  contexts.

Boundaries: No new ensemble run, no tuning, no scale-up authorization, and no
operational claim.

### TB-144: Execute Or Block Minimal Bounded Balfrin Ensemble Probe

Goal: Run the smallest bounded Balfrin follow-up probe, or produce a precise
blocked report if the metadata, artifacts, or authorization are still
insufficient.

Capability gap reduced: lack of measured uncertainty/runtime tradeoff evidence
beyond the current single-release-zone demonstration.

Why this outranks alternatives: after TB-143, the next major question is
whether a small additional measured probe materially changes uncertainty
interpretation enough to justify further execution.

Inspect first:

- `scripts/summarize_bounded_next_ensemble_feasibility_probe.py`
- `scripts/submit_balfrin_probe.py`
- `scripts/collect_balfrin_probe_metrics.py`
- `scripts/summarize_balfrin_ensemble_frontier.py`
- `docs/balfrin_single_job_execution_sufficiency.md`

Deliverables:

- Measured probe evidence and metrics, or a fail-closed blocked report with the
  exact missing prerequisites.
- Updated ensemble-frontier input artifacts or documentation showing the
  comparison basis.
- Focused tests for the new measured/blocked status path.

Definition of done:

- The repo records whether a minimal bounded Balfrin probe was measured or why
  it remains blocked, without changing closure status by assertion.

Boundaries: No large production ensemble, no parameter tuning, no scale-up
authorization, and no operational claim.

### TB-145: Interpret Bounded Probe Against Same-Scale Uncertainty

Goal: Compare any new bounded Balfrin probe evidence against the existing
same-scale uncertainty, stability, and closure-gap evidence.

Capability gap reduced: scientific meaning of additional execution evidence.

Why this outranks alternatives: new runtime evidence is only useful if it
changes, confirms, or sharply bounds the current uncertainty interpretation.

Inspect first:

- `scripts/summarize_spatial_same_scale_uncertainty.py`
- `scripts/summarize_tschamut_closure_gap_deltas.py`
- `scripts/summarize_balfrin_ensemble_frontier.py`
- `scripts/summarize_balfrin_post_run_interpretation_gate.py`
- `docs/tschamut_public_same_scale_uncertainty_envelope.md`

Deliverables:

- A deterministic comparison report for unchanged, improved, worsened, or
  blocked uncertainty interpretation.
- Updated text/JSON fields that keep closure inconclusive unless the evidence
  genuinely changes a closure criterion.
- Focused tests for measured, no-change, and missing-probe cases.

Definition of done:

- A reviewer can see whether the bounded probe materially reduced scientific
  uncertainty, merely confirmed current blockers, or remained unavailable.

Boundaries: No closure upgrade by assertion, no physics tuning, no operational
claim, and no physical-probability claim.

### TB-146: Freeze Management Demonstration Evidence Package

Goal: Produce a compact, replayable Balfrin demonstration package intended for
management-facing feasibility review.

Capability gap reduced: fragmented demonstration evidence across many helpers
and documents.

Why this outranks alternatives: the project now has enough measured evidence
that presentation coherence, reproducibility, and claim boundaries matter more
than another status-only report.

Inspect first:

- `scripts/summarize_balfrin_evidence_bundle.py`
- `scripts/summarize_balfrin_demonstration_replay_smoke.py`
- `scripts/summarize_balfrin_post_run_interpretation_gate.py`
- `docs/balfrin_single_job_execution_sufficiency.md`
- `docs/current_maturity_snapshot.md`

Deliverables:

- One compact JSON/text demonstration package manifest with runtime, replay,
  restartability, GIS scope, uncertainty, and claim-boundary sections.
- A deterministic command sequence to regenerate the package into `/tmp` or an
  ignored artifact root.
- Tests that keep measured, fixture-backed, and blocked sections distinct.

Definition of done:

- A non-developer reviewer can inspect one generated package and understand
  what the Balfrin demo proves and what it does not prove.

Boundaries: No operational claim, no annual-frequency claim, no physical
validation claim, and no generated large-artifact commit.

### TB-147: Harden AOI Tile Discovery Against Real Swisstopo Catalog Shapes

Goal: Make AOI-to-product discovery robust to realistic swisstopo catalog
records, product variants, and blocked/no-catalog states.

Capability gap reduced: Swiss-wide workflow automation still depends on
catalog assumptions that have only been fixture-tested narrowly.

Why this outranks alternatives: every future AOI workflow starts with product
and tile discovery; brittle discovery blocks portability before simulation can
begin.

Inspect first:

- `scripts/plan_swisstopo_aoi_acquisition.py`
- `scripts/check_second_site_public_geodata_preflight.py`
- `data/datasets.yaml`
- `docs/swisstopo_data_strategy.md`
- `tests/test_swisstopo_aoi_acquisition_planner.py`

Deliverables:

- Expanded deterministic catalog parsing for product ids, tile ids, CRS,
  resolution, date/version, and expected staging roots.
- Fixture-backed tests for multiple product shapes and clean blocked states.
- No-download command output suitable for AOI-to-prepared-pilot composition.

Definition of done:

- AOI tile discovery produces stable product/tile manifests for realistic
  catalog fixtures and fails closed when catalog metadata is absent.

Boundaries: No downloads, no license-sensitive raw data commits, no ensemble,
and no operational claim.

### TB-148: Define Public Geodata Cache And Provenance Contract

Goal: Define the deterministic cache layout, checksum/provenance fields, and
stage/verify commands needed before real AOI products can be used safely.

Capability gap reduced: missing bridge between no-download AOI planning and
trusted local public-geodata staging.

Why this outranks alternatives: without a cache/provenance contract, future
downloads or manually staged products cannot be audited or reproduced.

Inspect first:

- `docs/swisstopo_data_strategy.md`
- `docs/public_real_site_geodata_preparation.md`
- `scripts/plan_swisstopo_aoi_acquisition.py`
- `scripts/check_second_site_public_geodata_preflight.py`

Deliverables:

- A machine-readable cache/provenance schema or helper output for staged public
  products.
- Verification fields for source URL/id, product version, checksum, CRS,
  resolution, tile id, crop extent, and license/provenance note.
- Tests for verified, missing, checksum-mismatch, and metadata-mismatch states.

Definition of done:

- A future data worker can stage public geodata into an ignored cache and run a
  deterministic verification command before any pilot preparation uses it.

Boundaries: No actual bulk downloads, no raw swisstopo commits, no hazard run,
and no operational claim.

### TB-149: Prototype AOI Terrain Preprocessing From Staged Tiles

Goal: Convert verified staged terrain tiles into a deterministic AOI terrain
crop and metadata package for downstream release-zone and case planning.

Capability gap reduced: missing generic preprocessing step between public tile
staging and pilot-ready terrain inputs.

Why this outranks alternatives: release-zone candidates, source metadata, and
hazard grids cannot become AOI-generic while terrain crops remain handcrafted.

Inspect first:

- `scripts/plan_swisstopo_aoi_acquisition.py`
- `scripts/plan_terrain_release_zone_candidates.py`
- `scripts/check_second_site_public_geodata_preflight.py`
- `docs/public_real_site_geodata_preparation.md`

Deliverables:

- A dry-run or fixture-backed terrain preprocessing helper that records crop
  extent, resolution, CRS, nodata, source tiles, and output roots.
- Tests for fixture terrain, missing tile, and metadata mismatch behavior.
- Integration fields consumed by release-zone candidate generation.

Definition of done:

- A fixture-backed AOI terrain package can be generated or planned
  deterministically without Tschamut-specific paths.

Boundaries: No national-scale processing, no unauthorized downloads, no
physics changes, and no operational claim.

### TB-150: Stress-Test Release-Zone Candidate Heuristic Stability

Goal: Quantify how deterministic terrain-driven release-zone candidates change
under bounded threshold and preprocessing perturbations.

Capability gap reduced: release-zone automation is currently deterministic but
not yet stability-characterized.

Why this outranks alternatives: heuristic release zones dominate downstream
uncertainty, so their robustness must be measured before trusting AOI-scale
automation.

Inspect first:

- `scripts/plan_terrain_release_zone_candidates.py`
- `tests/test_plan_terrain_release_zone_candidates.py`
- `docs/current_maturity_snapshot.md`
- `docs/swisstopo_data_strategy.md`

Deliverables:

- A deterministic sensitivity report for candidate count, area, overlap, and
  stable/unstable candidate regions across bounded heuristic settings.
- Fixture tests for stable and unstable heuristic outcomes.
- Clear non-validation boundary language.

Definition of done:

- The repo can distinguish robust terrain candidates from heuristic-sensitive
  candidates without claiming either is a validated release zone.

Boundaries: No threshold tuning to match outcomes, no field-validation claim,
no operational release-zone claim, and no ensemble run.

### TB-151: Generalize Scenario Generation To Candidate Source Zones

Goal: Generate deterministic block-scenario tables for generic candidate source
zones rather than only the frozen Tschamut policy/table pair.

Capability gap reduced: handcrafted scenario semantics still limit AOI and
second-site workflow portability.

Why this outranks alternatives: AOI preparation needs release-zone and scenario
generation to compose without Tschamut-only identifiers.

Inspect first:

- `scripts/generate_tschamut_block_scenario_tables.py`
- `scripts/plan_pragmatic_release_plan.py`
- `validation/policies/tschamut_public_source_scenario_policy_v1.yaml`
- `tests/test_tschamut_block_scenario_table_generation.py`

Deliverables:

- A site-agnostic scenario-generation path or wrapper that accepts candidate
  source-zone metadata and a policy template.
- Provenance-aware scenario manifests with stable ids and explicit
  conditional-only weighting semantics.
- Tests for Tschamut compatibility and a synthetic non-Tschamut candidate.

Definition of done:

- Scenario tables can be generated deterministically for a generic candidate
  source zone while preserving non-frequency and non-operational boundaries.

Boundaries: No block-population fitting, no annual frequency, no physics
changes, and no operational claim.

### TB-152: Emit Runnable Case Skeletons From AOI Dry Run

Goal: Extend the site-level AOI-to-command-plan dry run so it can emit
non-executed validation case skeletons and command references under ignored
roots.

Capability gap reduced: gap between dry-run composition and a reproducible
operator handoff for a new AOI.

Why this outranks alternatives: after discovery, terrain, release, and scenario
planning compose, the next automation milestone is a reproducible case skeleton
that still stops before execution.

Inspect first:

- `scripts/plan_aoi_to_prepared_pilot_dry_run.py`
- `scripts/generate_pilot_command_plan.py`
- `scripts/generate_tschamut_same_scale_cases.py`
- `tests/test_aoi_to_prepared_pilot_dry_run.py`

Deliverables:

- Optional ignored output mode that writes a candidate case skeleton, command
  manifest, expected output roots, and blocked execution status.
- Tests for deterministic skeleton generation and blocked missing-input states.
- Documentation of which commands are runnable and which remain template-only.

Definition of done:

- A worker can run one dry-run command for a fixture AOI and inspect the exact
  case skeleton and command sequence that would be used before any ensemble
  execution.

Boundaries: No ensemble execution, no second-site hazard build, no generated
large-artifact commit, no physical-probability semantics, and no operational
claim.

## Backlog Protocol

Task headings must always be exactly:

```markdown
### TB-XXX: Short Description
```

Do not put priority, status, owner, or tags in the heading. Use this schema for
every active task:

```markdown
### TB-XXX: Short Description

Goal: One sentence describing why the task matters now.

Capability gap reduced: The concrete capability gap this task reduces.

Why this outranks alternatives: One sentence explaining why this is high
leverage now.

Inspect first:

- `path/or/script.py`

Deliverables:

- Concrete executable, analysis, test, or measured output.

Definition of done:

- Focused checks pass, the capability outcome is explicit, and the task is
  removed from this backlog only when the definition of done is genuinely met.

Boundaries: No tuning, operational claims, scale-up authorization, or other
phase changes unless the task explicitly allows them.
```

Workers should start with compact task context and a targeted backlog lookup:

```bash
PYENV_VERSION=system uv run python scripts/print_agent_task_context.py --task TB-xxx --format json
rg -n "^### TB-xxx:" docs/task_backlog.md
```

Read only the selected task and its `Inspect first` files unless the task
explicitly requires broader context. Use `--detail full` on the task-context
helper only for orchestrator/review work.

Keep worker prompts compact: include the selected task body and essential
pitfalls only. Redirect large JSON, diffs, and logs to `/tmp`, summarize the
result, preserve the final relevant error block when a command fails, and
finish with the compact structured report schema:
`TASK`, `STATUS`, `SUMMARY`, `FILES_CHANGED`, `CHECKS_RUN`, `COMMIT`,
`PUSH_STATUS`, `REMAINING_NEXT_TASK`, `BOUNDARY_NOTE`.

For `STATUS`, distinguish `implemented_measured`,
`implemented_fixture_backed`, `implemented_blocked_report`,
`blocked_unresolved`, and `partial_needs_followup` when relevant. A blocked
report or fixture-backed proof is not the same as measured execution; leave or
add the smallest unblock task before dependent synthesis work.

Before commit, run the task-specific checks, `git diff --check`, repository
consistency, `scripts/git-hooks/pre-commit`, and the placeholder-artifact scan.

Do not keep completed tasks here. Use `agent_work_log.md` for chronological TB
execution history and `decision_log.md` for durable decisions.
