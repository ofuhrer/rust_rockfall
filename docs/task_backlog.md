# Task Backlog

Status: authoritative executable task backlog.

This file is intentionally compact. It should contain only the active TB queue,
the task template, and deferred non-goals. Detailed maturity framing lives in
`docs/current_maturity_snapshot.md`; completed TB history lives in
`docs/agent_work_log.md`.

Worker rule: when a task is done, remove it from this file and add a short
entry to `docs/agent_work_log.md`. Record only durable technical decisions in
`docs/decision_log.md`.

Progress rule: prefer runs, measurements, code, data, and simplification over
new process artifacts.

Reports, checks, validators, YAML records, checklists, and evidence packages are
useful only when they directly enable a run, measurement, acquisition,
reproducibility step, or simplification.

Orchestrator rule: work the active tasks in numeric order and keep `main`
usable. Full sequential-loop guidance lives in `docs/orchestration_strategy.md`.

Live Balfrin rule: the user has granted standing clearance for GPT-5.5 workers
to submit and actively monitor jobs on Balfrin's `postproc` partition. Multiple
concurrent `postproc` jobs are allowed, including filling the partition. If a
run plan would keep `postproc` fully busy for more than 6 hours, stop and
rediscuss. Keep run roots on `$SCRATCH` and preserve enough metadata to replay
and compare the result.

## Active Tasks

### TB-655: Run The Second-Site Prepared-Pilot Path If Inputs Are Ready

Goal: Exercise the Chant Sura / Fluelapass prepared-pilot path with real staged inputs when available, or fail on a precise missing-input boundary.

Capability gap reduced: Second-site AOI execution and package parity.

Why this outranks alternatives: Once public geodata staging improves, the next proof is whether the same AOI path runs on a second site.

Inspect first:

- `scripts/run_aoi_hazard_workflow.py`
- `scripts/inventory_second_site_local_blockers.py`
- `scripts/audit_multisite_source_scenario_contract.py`
- `tests/fixtures/hazard/chant_sura_second_site_smoke_case.yaml`

Deliverables:

- A second-site prepared-pilot scratch run/package, or a precise blocker that names the first missing real input family.

Definition of done:

- The result is clearly labelled as real-input, fixture-backed, or blocked, and no Tschamut-only evidence is counted as second-site validation.

### TB-656: Strengthen Release-Probability Evidence

Goal: Convert the current release-probability gap into a concrete empirical or design-review evidence summary from existing source-zone and candidate records.

Capability gap reduced: Physical-probability scientific credibility.

Why this outranks alternatives: Release-probability evidence is one of the remaining blockers for physical-probability readiness.

Inspect first:

- `scripts/summarize_balfrin_physical_credibility_evidence_gaps.py`
- `scripts/validate_block_release_probability_evidence.py`
- `docs/block_release_probability_evidence_contract.md`
- `docs/source_zone_block_scenario_policy_v1.md`

Deliverables:

- A checked evidence summary or blocker that states what release-probability information is present, absent, and needed next.

Definition of done:

- The physical-credibility gap report moves forward with real evidence or a smaller blocker, without enabling physical-probability map labels.

### TB-657: Strengthen Block-Population Evidence

Goal: Summarize current block-size, block-shape, and scenario-weight evidence from scenario tables and staged records.

Capability gap reduced: Physical-probability and intensity credibility for block scenarios.

Why this outranks alternatives: Block-population evidence is a separate scientific blocker and can be improved from existing scenario/candidate data before new field work.

Inspect first:

- `scripts/generate_tschamut_block_scenario_tables.py`
- `scripts/validate_block_release_probability_evidence.py`
- `docs/probabilistic_scenario_model_design.md`
- `tests/test_tschamut_block_scenario_table_generation.py`

Deliverables:

- A compact block-population evidence summary or blocker tied to current scenario tables and validation tests.

Definition of done:

- The summary identifies usable empirical inputs, design assumptions, and the next data gap without changing simulation defaults.

### TB-658: Refresh Calibration And Holdout Separation Evidence

Goal: Re-run the calibration/holdout separation checks against the latest staged evidence and identify the first unresolved scientific blocker.

Capability gap reduced: Validation credibility and calibration discipline.

Why this outranks alternatives: Stronger scale evidence is not persuasive without clear calibration and holdout separation.

Inspect first:

- `scripts/assess_validation_calibration_evidence_gaps.py`
- `scripts/check_calibration_separation_preflight.py`
- `scripts/audit_chant_sura_holdout_split.py`
- `docs/holdout_runout_deposition_evidence_tb615.md`

Deliverables:

- A refreshed local evidence-gap result that ranks the next scientific action and states whether holdout/calibration separation still passes.

Definition of done:

- The first unresolved blocker is explicit and the result does not promote validation acceptance beyond the evidence.

### TB-659: Collapse One Specialist AOI Command Into The Front Door

Goal: Reduce user-facing complexity by routing one commonly needed specialist AOI helper through `run_aoi_hazard_workflow.py`.

Capability gap reduced: Clean user-facing AOI interface.

Why this outranks alternatives: The repository already has many helper scripts; simplifying the command surface directly improves usability.

Inspect first:

- `scripts/run_aoi_hazard_workflow.py`
- `scripts/preview_aoi_scenario_cost_estimate.py`
- `scripts/package_aoi_hazard_map.py`
- `tests/test_run_aoi_hazard_workflow.py`

Deliverables:

- A new or improved front-door subcommand that delegates to an existing helper without duplicating logic, plus focused tests.

Definition of done:

- Users can perform the selected AOI action through `run_aoi_hazard_workflow.py`, and the specialist helper remains internal or compatibility-level.

### TB-660: Simplify The Balfrin Helper Surface

Goal: Demote or remove stale Balfrin helper references so routine users see `run_balfrin_diagnostic.py` first.

Capability gap reduced: Repository simplification and lower operational drag.

Why this outranks alternatives: Old handoff/preflight/submit helper paths still make the Balfrin interface look more procedural than it needs to be.

Inspect first:

- `docs/script_inventory.md`
- `docs/balfrin_tschamut_pilot_runbook.md`
- `docs/balfrin_skills.md`
- `scripts/run_balfrin_diagnostic.py`

Deliverables:

- A smaller Balfrin command surface in docs and script inventory, with stale helper references demoted to forensic or compatibility use.

Definition of done:

- The routine Balfrin path is unambiguous and repository consistency checks pass.

### TB-661: Exercise A National Inventory Chunk Smoke

Goal: Re-run the Swiss national inventory/chunk planning smoke and make the next data-cache blocker concrete.

Capability gap reduced: Swiss-wide feasibility preparation without claiming Swiss-wide execution.

Why this outranks alternatives: Swiss-scale work is deferred, but national inventory and chunk planning can still expose concrete data/cache gaps.

Inspect first:

- `scripts/estimate_swiss_wide_execution_envelope.py`
- `docs/swiss_national_tiling_inventory_tb607.md`
- `docs/swiss_national_tile_chunk_mapping_tb608.md`
- `docs/swiss_scale_feasibility_projection.md`

Deliverables:

- A fresh national inventory/chunk smoke output with tile count, chunk count, estimated input bytes, missing products, and cache readiness.

Definition of done:

- The Swiss-scale projection or inventory note names the current data-cache blocker while leaving Swiss-wide execution deferred.

### TB-662: Measure Output Pressure After QA Checklist Packaging

Goal: Quantify whether the new package QA checklist materially changes package file count, byte count, or manifest pressure.

Capability gap reduced: Output-footprint control for larger AOI and Balfrin packages.

Why this outranks alternatives: Review usability improved, but larger runs still depend on keeping package and manifest growth bounded.

Inspect first:

- `scripts/package_aoi_hazard_map.py`
- `scripts/summarize_balfrin_output_tier_audit.py`
- `scripts/audit_balfrin_run_root_output_budget.py`
- `docs/hazard_output_profile_contract.md`

Deliverables:

- A before/after or current-package pressure measurement that includes checklist manifest bytes and package file counts.

Definition of done:

- The result states whether checklist packaging is negligible, acceptable, or a scaling concern for larger packages.

### TB-663: Run A Local CI Front-Door Cleanup Pass

Goal: Identify one slow, redundant, or confusing local CI path and simplify it without reducing coverage.

Capability gap reduced: Developer speed and drift prevention.

Why this outranks alternatives: Faster local verification helps prevent another local-vs-GitHub Actions drift.

Inspect first:

- `scripts/run_ci_local.py`
- `tests/python_test_tiers.toml`
- `.github/workflows/ci.yml`
- `tests/test_run_ci_local.py`

Deliverables:

- A small local CI runner or test-tier simplification with focused test coverage.

Definition of done:

- The documented local CI command remains aligned with GitHub Actions and the change removes duplication or confusion.

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
leverage now, preferably tied to a measured blocker, an executable workflow
boundary, real evidence acquisition, output/runtime scaling, or simplification
of duplicated orchestration.

Inspect first:

- `path/or/script.py`

Deliverables:

- Concrete executable, analysis, test, or measured output. If the deliverable is
  mainly a report, check, validator, checklist, or package, state the exact run,
  recovery, acquisition, reproducibility, or consolidation action it enables.

Definition of done:

- Focused checks pass, the result is explicit, and the task actually moved
  execution, measurement, acquisition, or simplification forward.

Scope: Keep work focused. If a task changes physics defaults, execution
architecture, partition choice, or public output semantics, record that choice
plainly in the work log.
```

Workers should start with compact task context and a targeted backlog lookup:

```bash
PYENV_VERSION=system uv run python scripts/print_agent_task_context.py --task TB-xxx --format json
rg -n "^### TB-xxx:" docs/task_backlog.md
```

Read the selected task and its `Inspect first` files first. Pull broader
context only when it is needed.

Inspect first entries must resolve to tracked repository files unless explicitly marked `external:` or `generated scratch:`.

Keep worker prompts compact. Redirect large JSON, diffs, and logs to `/tmp` and
summarize the important result; finish with the compact structured report schema:
`TASK`, `STATUS`, `SUMMARY`, `FILES_CHANGED`, `CHECKS_RUN`, `COMMIT`,
`PUSH_STATUS`, `REMAINING_NEXT_TASK`, `BOUNDARY_NOTE`.

Before commit, run the focused checks, `git diff --check`, and the pre-commit
hook. Add broader consistency checks when the change touches shared contracts or
public docs.

Do not keep completed tasks here. Append completed TB work to the bottom of `docs/agent_work_log.md`
and use `decision_log.md` for durable decisions.
