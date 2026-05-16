# Agent Work Log

Append-only current work log for TB tasks.

This file is intentionally short and chronological. The full pre-refactor
history, non-TB planning notes, M-series milestones, backlog refills, and
review triage entries live in `docs/agent_work_log_archive.md`.

## Worker Instructions

- Always append new entries at the bottom of this file. Do not insert work
  logs near related older entries.
- Use one `### TB-XXX: Short Title` heading per completed task.
- Keep the TB entries in ascending order. If the current task is `TB-058`,
  its entry belongs after `TB-057`.
- Do not add backlog-refill notes, review triage, planning notes, or
  non-task narrative here. Put durable planning in `docs/task_backlog.md` or
  `docs/decision_log.md`; archive older non-TB history only in
  `docs/agent_work_log_archive.md`.
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
  are preserved in `docs/agent_work_log_archive.md`.
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
  are preserved in `docs/agent_work_log_archive.md`.
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
  are preserved in `docs/agent_work_log_archive.md`.
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
  are preserved in `docs/agent_work_log_archive.md`.
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
  are preserved in `docs/agent_work_log_archive.md`.
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
  are preserved in `docs/agent_work_log_archive.md`.
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
  are preserved in `docs/agent_work_log_archive.md`.
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
  are preserved in `docs/agent_work_log_archive.md`.
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
  are preserved in `docs/agent_work_log_archive.md`.
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
  are preserved in `docs/agent_work_log_archive.md`.
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
  are preserved in `docs/agent_work_log_archive.md`.
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
  are preserved in `docs/agent_work_log_archive.md`.
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
  are preserved in `docs/agent_work_log_archive.md`.
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
  are preserved in `docs/agent_work_log_archive.md`.
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
  are preserved in `docs/agent_work_log_archive.md`.
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
  are preserved in `docs/agent_work_log_archive.md`.
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
  are preserved in `docs/agent_work_log_archive.md`.
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
  are preserved in `docs/agent_work_log_archive.md`.
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
  are preserved in `docs/agent_work_log_archive.md`.
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
  are preserved in `docs/agent_work_log_archive.md`.
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
  are preserved in `docs/agent_work_log_archive.md`.
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
  are preserved in `docs/agent_work_log_archive.md`.
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
  are preserved in `docs/agent_work_log_archive.md`.
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
  are preserved in `docs/agent_work_log_archive.md`.
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
  are preserved in `docs/agent_work_log_archive.md`.
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
  are preserved in `docs/agent_work_log_archive.md`.
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
  are preserved in `docs/agent_work_log_archive.md`.
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
  are preserved in `docs/agent_work_log_archive.md`.
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
  are preserved in `docs/agent_work_log_archive.md`.
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
  are preserved in `docs/agent_work_log_archive.md`.
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
  are preserved in `docs/agent_work_log_archive.md`.
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
  are preserved in `docs/agent_work_log_archive.md`.
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
  are preserved in `docs/agent_work_log_archive.md`.
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
  are preserved in `docs/agent_work_log_archive.md`.
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
  are preserved in `docs/agent_work_log_archive.md`.
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
  are preserved in `docs/agent_work_log_archive.md`.
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
  are preserved in `docs/agent_work_log_archive.md`.
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
  are preserved in `docs/agent_work_log_archive.md`.
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
  are preserved in `docs/agent_work_log_archive.md`.
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
  are preserved in `docs/agent_work_log_archive.md`.
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
  are preserved in `docs/agent_work_log_archive.md`.
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
  are preserved in `docs/agent_work_log_archive.md`.
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
  are preserved in `docs/agent_work_log_archive.md`.
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
  are preserved in `docs/agent_work_log_archive.md`.
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
  are preserved in `docs/agent_work_log_archive.md`.
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
  are preserved in `docs/agent_work_log_archive.md`.
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
  are preserved in `docs/agent_work_log_archive.md`.
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
  are preserved in `docs/agent_work_log_archive.md`.
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
  are preserved in `docs/agent_work_log_archive.md`.
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
  are preserved in `docs/agent_work_log_archive.md`.
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
  are preserved in `docs/agent_work_log_archive.md`.
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
  are preserved in `docs/agent_work_log_archive.md`.
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
  are preserved in `docs/agent_work_log_archive.md`.
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
  are preserved in `docs/agent_work_log_archive.md`.
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
  are preserved in `docs/agent_work_log_archive.md`.
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
  are preserved in `docs/agent_work_log_archive.md`.
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
  are preserved in `docs/agent_work_log_archive.md`.
- Checks run: see archive for original command lists.
- Result/status: completed or superseded by later TB work.
- Boundaries: historical scientific/operational boundaries preserved as
  recorded in the archive.
- Next task: see `docs/task_backlog.md` for the active queue.

### TB-058: Stabilize Command-Plan And COG Readiness Drift

- Date: 2026-05-16
- Commit: `35c5431`
- Objective: tighten worker-facing command-plan, GIS/COG, and diagnostic-interpretation wording so clean checkouts and converted-package readiness are explicit.
- Files changed: scripts/generate_pilot_command_plan.py, scripts/audit_gis_cog_package_readiness.py, scripts/summarize_tschamut_conditional_diagnostic_interpretation.py, tests/test_pilot_command_plan.py, tests/test_gis_cog_package_readiness.py, tests/test_tschamut_conditional_diagnostic_interpretation.py, docs/pilot_gis_package.md, docs/model_benchmark_execution_report.md, docs/tschamut_public_conditional_pilot_gate_report.md, docs/tschamut_public_same_scale_uncertainty_envelope.md, docs/task_backlog.md
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
- Next task: `TB-099`

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
