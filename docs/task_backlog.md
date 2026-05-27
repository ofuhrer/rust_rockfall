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

### TB-637: Run A Calibration-Selected Hazard Smoke

Goal: Check whether the locally selected calibration candidate materially changes the Tschamut hazard layers in a controlled scratch run.

Capability gap reduced: Connects calibration evidence to map-output behavior instead of leaving it isolated in a fitting report.

Why this outranks alternatives: Calibration only matters if its selected parameters have understandable effects on hazard outputs.

Inspect first:

- `calibration/experiments/tschamut_v0_3/selected_parameters.yaml`
- `scripts/build_hazard_layers.py`
- `validation/private/tschamut_public_pilot/target_gate_v1/tschamut_public_target_gate_case.yaml`
- `scripts/compare_hazard_map_convergence.py`

Deliverables:

- A scratch hazard build or concrete blocker comparing baseline and calibration-selected output layers.

Definition of done:

- The comparison reports changed/unchanged layer metrics, uses scratch outputs only, and does not mutate validation cases or default model parameters.

### TB-638: Make Calibration Readiness Report Actionable

Goal: Convert the remaining calibration blocker from a generic `partial` state into specific missing/weak evidence fields.

Capability gap reduced: Clear path from local calibration smoke toward physical-probability readiness.

Why this outranks alternatives: The readiness check now says only calibration is failing, but the next calibration fix needs a precise target.

Inspect first:

- `scripts/assess_validation_calibration_evidence_gaps.py`
- `scripts/check_calibration_separation_preflight.py`
- `calibration/experiments/tschamut_v0_3/objective_contract.json`
- `tests/test_validation_calibration_evidence_gaps.py`

Deliverables:

- A readiness report that identifies concrete calibration sub-blockers such as residual quality, fitted-parameter provenance, acceptance threshold, or holdout scoring completeness.

Definition of done:

- Focused tests pass and the report still keeps physical-probability claims false until all required calibration sub-blockers are satisfied.

### TB-639: Stage Second-Site Public Context Inputs If Available

Goal: Move Chant Sura / Flüelapass from prepared-core readiness to an actual second-site smoke by resolving public-context inputs where local source data are available.

Capability gap reduced: Multi-site transfer and portability beyond Tschamut.

Why this outranks alternatives: The second-site workflow now has terrain/source/scenario readiness, but execution stops on public-context roots.

Inspect first:

- `scripts/inventory_second_site_local_blockers.py`
- `scripts/plan_swisstopo_aoi_acquisition.py`
- `scripts/run_aoi_hazard_workflow.py`
- `tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml`

Deliverables:

- Either staged public-context roots for the second-site fixture from available local/public inputs, or a concrete acquisition blocker with exact missing products and commands.

Definition of done:

- `run_aoi_hazard_workflow.py prepare` remains ready, `run-prepared-pilot-local` advances past the prior missing public-context-root blocker or reports the next concrete blocker.

### TB-640: Run The First Real Second-Site Prepared Pilot

Goal: Execute the smallest useful Chant Sura / Flüelapass prepared pilot once public-context inputs are available.

Capability gap reduced: Demonstrates portability beyond Tschamut on a second site.

Why this outranks alternatives: A successful second-site run is stronger evidence than more Tschamut-only refinement.

Inspect first:

- `scripts/run_aoi_hazard_workflow.py`
- `tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml`
- `docs/aoi_user_manual.md`
- `docs/public_real_site_geodata_preparation.md`

Deliverables:

- A measured second-site prepared-pilot output root or a concrete execution blocker after input staging.

Definition of done:

- The run completes with hazard/review outputs or stops with a single first blocker; fixture-backed local smoke is not counted as second-site evidence.

### TB-641: Compare Second-Site Outputs Against Tschamut Output Shape

Goal: Verify whether the second-site run produces comparable layer families, file counts, byte counts, and package readiness.

Capability gap reduced: Multi-site feasibility and output-interface stability.

Why this outranks alternatives: Portability is not useful if the second-site outputs cannot be reviewed with the same map/package tools.

Inspect first:

- `scripts/package_aoi_hazard_map.py`
- `scripts/summarize_large_aoi_gis_cog_stress_test.py`
- `docs/hazard_layers.md`
- `docs/aoi_user_manual.md`

Deliverables:

- A compact comparison between Tschamut and second-site output/package shape, including missing layer families or review blockers.

Definition of done:

- The comparison uses real output roots when available, reports concrete parity or blockers, and does not add a new long-lived report unless needed by a current workflow.

### TB-642: Run A Larger Bounded Hazard-Throughput Probe On Balfrin

Goal: Measure hazard-throughput beyond the current bounded four-zone support point while staying inside the existing `postproc` standing clearance.

Capability gap reduced: Performance and feasibility evidence for larger Balfrin hazard runs.

Why this outranks alternatives: Diagnostic reducer pressure is measured through 100 zones, but hazard-throughput is still bounded at four zones.

Inspect first:

- `scripts/summarize_balfrin_next_live_run_decision_gate.py`
- `scripts/generate_balfrin_multi_release_zone_demo_handoff.py`
- `scripts/summarize_balfrin_scale_readiness_matrix.py`
- `docs/balfrin_four_zone_hazard_run_tb619.md`
- `docs/balfrin_skills.md`

Deliverables:

- A submitted and monitored Balfrin `postproc` hazard-throughput run larger than TB-619, or a concrete pre-submit blocker.

Definition of done:

- Run roots live under `$SCRATCH`, runtime/memory/output/conditional-curve metrics are collected if the job completes, and claims remain bounded hazard-throughput evidence only.

### TB-643: Measure Reducer Metadata Pressure On Larger Hazard Outputs

Goal: Identify whether reducer metadata, manifest size, or replay sidecars become the next practical bottleneck after a larger hazard-throughput run.

Capability gap reduced: Scalability and output-profile control.

Why this outranks alternatives: The scale matrix ranks reducer and replay metadata pressure as the next scaling blocker after measured regional split comparison.

Inspect first:

- `scripts/summarize_multi_zone_reducer_pressure.py`
- `scripts/summarize_bounded_validation_output_profile.py`
- `docs/hazard_output_profile_contract.md`
- `docs/swiss_scale_feasibility_projection.md`

Deliverables:

- A measured reducer/output-profile summary for the largest available hazard-throughput output root.

Definition of done:

- The summary reports file counts, byte counts, manifest bytes, sidecar families, first pressure driver, and a concrete recommended reducer/output-profile change if one is warranted.

### TB-644: Simplify The Balfrin User Command Path

Goal: Reduce the number of user-facing Balfrin commands by routing routine diagnostic and bounded hazard runs through the smallest current command surface.

Capability gap reduced: Operational usability and repository simplicity.

Why this outranks alternatives: The repo still has many Balfrin helpers, and users need a clear path that does not require knowing historical task scripts.

Inspect first:

- `README.md`
- `docs/balfrin_tschamut_pilot_runbook.md`
- `docs/balfrin_skills.md`
- `scripts/generate_pilot_command_plan.py`
- `scripts/run_balfrin_diagnostic.py`

Deliverables:

- A shorter documented Balfrin command path that points routine work at current runners and demotes obsolete helper entry points to developer/forensic context.

Definition of done:

- Public docs expose fewer top-level Balfrin commands, existing tests still pass, and no executable capability is removed.

### TB-645: Add A Swiss National Data Inventory Smoke

Goal: Check whether the existing national tiling and data-inventory surfaces can produce a current, small, share-safe planning summary.

Capability gap reduced: Swiss-wide data readiness.

Why this outranks alternatives: Swiss-wide execution is deferred partly because national public-geodata inventory and tiling readiness are not current run evidence.

Inspect first:

- `scripts/estimate_swiss_wide_execution_envelope.py`
- `docs/swiss_national_tiling_inventory_tb607.md`
- `docs/swiss_national_tile_chunk_mapping_tb608.md`
- `docs/swisstopo_data_strategy.md`

Deliverables:

- A refreshed local national data/tiling inventory summary or exact missing-input blocker.

Definition of done:

- The result reports tile count, estimated bytes, chunk count, missing products, and whether the current inventory is sufficient for planning only.

### TB-646: Exercise A Small Chunked AOI Processing Prototype

Goal: Test whether the current AOI workflow can process multiple chunks and merge reviewable outputs without introducing distributed execution claims.

Capability gap reduced: Path toward regional/Swiss-scale chunking.

Why this outranks alternatives: Distributed execution is deferred, but a local chunk-and-merge prototype can expose merge and packaging issues before scheduler work.

Inspect first:

- `scripts/generate_pilot_command_plan.py`
- `scripts/build_hazard_layers.py`
- `scripts/package_aoi_hazard_map.py`
- `docs/swiss_scale_feasibility_projection.md`

Deliverables:

- A local scratch chunked AOI smoke or a concrete blocker for chunked hazard-layer merge/package behavior.

Definition of done:

- The prototype writes scratch outputs only, reports per-chunk and merged file/byte counts, and explicitly remains local non-distributed evidence.

### TB-647: Add Operational QA Checklist To Existing Map Package Output

Goal: Make GIS package review more actionable by surfacing visual QA items and provenance fields inside the existing package output.

Capability gap reduced: Operational-readiness preparation without claiming operational use.

Why this outranks alternatives: Packaging is now technically ready, so the next review gap is whether a human can systematically inspect the result.

Inspect first:

- `scripts/package_aoi_hazard_map.py`
- `scripts/generate_aoi_map_qa_review.py`
- `docs/pilot_gis_package.md`
- `docs/hazard_map_semantics.md`

Deliverables:

- A concise QA section in the generated AOI package/review output covering layer presence, CRS, nodata, style availability, and evidence/claim boundaries.

Definition of done:

- Existing package tests pass, generated package output includes the QA checklist, and accepted-for-operational-use remains false by default.

### TB-648: Remove Or Merge Remaining Superseded Docs From The Docs Index

Goal: Continue reducing repository documentation weight after the Balfrin diagnostic-doc consolidation.

Capability gap reduced: Repository navigability and lower maintenance drag.

Why this outranks alternatives: Simplification remains valuable only if it removes stale surfaces while preserving current measured facts.

Inspect first:

- `docs/README.md`
- `docs/project_overview.md`
- `docs/current_maturity_snapshot.md`
- `scripts/check_repo_consistency.py`

Deliverables:

- A safe prune or merge of additional superseded top-level docs, with active references updated to current summary surfaces.

Definition of done:

- `docs/README.md` is shorter or clearer, no active references point at deleted docs, and repository consistency checks pass.

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
