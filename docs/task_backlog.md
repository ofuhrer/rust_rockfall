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
