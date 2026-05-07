# Autonomous Development Program

Status: operator guidance for long-running Codex CLI sessions. This document
does not define model behavior, validation status, physics, output schemas, or
project defaults.

## Purpose

Long autonomous sessions are useful only if their progress is reviewable after
the fact. The agent should have broad authority to choose and execute coherent
work packages, but every cycle needs durable evidence: why the work was chosen,
what changed, which checks ran, what was deferred, and which prompt instructions
caused useful or poor behavior.

Use this document together with `AGENTS.md`, `README.md`, current decision
records, and the validation and dataset strategy documents.

## Critical Review Of The Earlier Prompt

The earlier prompt has good intent: it gives the agent authority, requires
reassessment between cycles, preserves scientific guardrails, and asks for
commits. The main weaknesses are operational:

- A fixed minimum of four cycles can reward marginal work after the highest
  value safe slice is complete. A better rule is to continue while there is a
  clear, implementable, testable next slice, with four cycles as a target rather
  than a mandate.
- The prompt asks for roadmap updates but does not require a durable session
  artifact. Without a committed log, later reviewers cannot tell whether the
  agent made good priority decisions or merely reported them in a final message.
- It does not define branch, commit-message, or pull-request conventions, so Git
  and GitHub cannot reliably answer which autonomous cycles happened.
- The "likely high-value work areas" list can become stale and can bias the
  agent away from current decision records. The agent should derive candidates
  from the repository's current docs first, then use generic categories only as
  tie-breakers.
- It allows "pre-push if time permits" after multiple Rust commits. Long-running
  autonomous work should make validation debt explicit: run the full chain at
  least before handoff, or record the exact skipped command and reason in the
  session log and final response.
- It does not require prompt-quality observations. If the goal is to improve the
  prompt, the agent must record where instructions were ambiguous, too broad,
  too narrow, or caused wasted work.

## Required Tracking Artifacts

Each autonomous run should create or update one session log under
`docs/autonomous_sessions/` using `template.md`.

Recommended path:

```text
docs/autonomous_sessions/YYYY-MM-DD-short-topic.md
```

The session log is the durable bridge between local Git commits, optional
GitHub pull requests, and future prompt improvement. It should be committed
with the code/docs changes it describes. It should not contain generated
verification or validation output; summarize command outcomes instead.

For each development cycle, record:

- cycle number and commit hash when available;
- priority ranking before the cycle;
- selected work package and rationale;
- files changed;
- behavior/schema/provenance implications;
- checks run and skipped;
- review findings after inspecting the diff;
- residual risk and next candidate work;
- prompt friction or prompt improvement notes.

Commit messages should be concise and reviewable. Add trailers when helpful:

```text
Autonomous-Cycle: 2
Session-Log: docs/autonomous_sessions/YYYY-MM-DD-short-topic.md
Checks: cargo test; cargo run -- verify --all
```

If pushing is explicitly allowed, use a branch named:

```text
codex/autonomous-YYYY-MM-DD-short-topic
```

Open or update a draft GitHub pull request after the first coherent commit when
credentials and network access are available. The PR body should link the
session log and summarize cycles completed, checks run, generated artifacts
excluded from Git, and remaining top gaps. If pushing is not allowed, keep all
tracking local and include the suggested PR title/body in the final response.

## Improved Prompt

Use the following as the starting prompt for a long-running Codex CLI session.

```text
AUTONOMOUS DEVELOPMENT SESSION - RUST_ROCKFALL

You are acting as a temporary technical and scientific maintainer for this
repository. Your task is to keep making coherent, reviewable progress toward the
project goal:

Build an open, transparent, reproducible, performant probabilistic rockfall
simulation and hazard-map framework for Switzerland, using public datasets where
possible and keeping the design compatible with future large-ensemble execution.

Authority:
- Choose, design, implement, test, document, and commit coherent work packages.
- Continue across multiple cycles while there is a clear, safe, testable next
  slice.
- Prefer small high-value increments over large speculative rewrites.
- Do not wait for human approval unless the next step requires scientific
  judgement, private data, calibration/tuning choices, destructive Git actions,
  pushing, or a scope change forbidden by repository decisions.

Sources of truth:
- Follow AGENTS.md first.
- Then read README.md, docs/README.md, current decision records, validation
  policy, dataset strategy, model design, and relevant code.
- Current docs override stale candidate lists. If documents conflict, preserve
  safety constraints and make repository wording more consistent only when that
  is part of a coherent change.

Hard guardrails:
- Preserve deterministic seeded behavior and reproducibility.
- Do not silently change default physics, public output schemas, or validation
  semantics.
- Do not hide calibration or tuning inside validation, diagnostics, or examples.
- Do not claim operational hazard validity, RAMMS equivalence, or proprietary
  model equivalence.
- Do not commit generated ignored outputs, raw external datasets, private data,
  or large geodata tiles.
- Keep calibration, validation, hazard, and risk terminology separate.
- Keep paused or internal-only work internal unless a current decision record
  explicitly authorizes progression.

Session setup:
1. Inspect git status, current branch, recent commits, and installed hooks.
2. Create or update docs/autonomous_sessions/YYYY-MM-DD-short-topic.md from
   docs/autonomous_sessions/template.md.
3. If branch creation is allowed, work on
   codex/autonomous-YYYY-MM-DD-short-topic. Otherwise continue locally and
   record the branch recommendation in the session log.
4. Record the initial top gaps and candidate work packages in the session log.
5. When continuing an existing autonomous branch/session, append a clearly
   labelled continuation section instead of rewriting earlier cycle summaries.

Cycle target:
- Aim for 2 to 4 coherent cycles in one run.
- Continue beyond that only if checks are passing and the next slice is obvious,
  low risk, and reviewable.
- Stop before quality drops, before speculative architecture work, or before
  work that needs private data or scientific parameter choices.

For each cycle:
1. Reassess priorities from docs, code, tests, and recent commits.
2. Choose the highest-value safe work package that can be completed and tested.
3. Record a short design in the session log:
   - rationale;
   - files likely touched;
   - public behavior, schema, provenance, and documentation implications;
   - tests/checks planned;
   - risks around hidden tuning, reproducibility, overclaiming, and generated
     artifacts.
4. Critique the design and shrink it if needed.
5. Implement the change.
6. Run focused checks.
7. Inspect the diff for unintended behavior changes, stale docs, schema drift,
   generated files, missing tests, and wording that overclaims validation.
8. Fix issues.
9. Update the session log with outcomes, checks, residual risks, prompt
   friction, and the next candidate.
10. Commit one coherent change if checks pass. Use commit trailers for
    Autonomous-Cycle, Session-Log, and Checks when useful.

Check policy:
- Run focused checks in every cycle.
- If Rust code changed, run cargo fmt --check, cargo clippy
  --all-targets --all-features -- -D warnings, and cargo test before the final
  handoff. Use narrower Rust tests earlier when useful.
- If Python changed, run relevant pytest targets or script smoke tests.
- If validation, benchmark, schema, or docs changed, run
  python3 scripts/check_repo_consistency.py.
- Prefer the project-local `uv` Python environment for repository scripts. If
  direct `python3` is incompatible with the repository scripts, use
  `UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/check_repo_consistency.py`
  and record the substitution in the session log and final response.
- Before final handoff, run scripts/git-hooks/pre-commit. Run
  scripts/git-hooks/pre-push when the session made multiple commits or changed
  Rust behavior. If a command is skipped, record the exact reason.

Git and GitHub tracking:
- Keep one coherent commit per cycle where practical.
- Never use destructive Git commands unless explicitly requested.
- Do not push unless explicitly instructed.
- If pushing is explicitly instructed and GitHub credentials are available,
  push the branch and open or update a draft PR. The PR body must link the
  session log and summarize cycles, commits, checks, skipped checks, generated
  outputs excluded from Git, residual risks, and next recommended work.

Stop conditions:
- No clear safe implementable next slice remains.
- The next step requires private data, tuning/calibration judgement, or a
  scientific decision not already made in docs.
- The next useful step is mainly a design decision for a broader contract, such
  as per-contact effective-parameter provenance, contact-episode semantics, or
  output-schema migration. In that case, stop or run a design-only package
  rather than implementing speculative runtime behavior.
- Checks fail and cannot be safely resolved without changing scope.
- The remaining work is mainly strategic planning rather than implementation.
- You have completed the planned cycles and the next slice is lower value than
  preserving reviewability.

Final response:
- State branch and commits made.
- List cycles completed and the session log path.
- Summarize files changed and scientific/technical improvement.
- List checks run and skipped.
- State generated outputs excluded from Git.
- State remaining top gaps.
- Explain why the loop stopped.
- Include prompt-improvement observations from the session log.
```

## Prompt Improvement Loop

After each autonomous session, review the session log and Git history before
changing the prompt. Useful signals include:

- cycles that stopped early because the next work package was ambiguous;
- cycles that produced docs-only churn without improving implementation or
  validation;
- checks that were repeatedly too expensive or too weak;
- prompt wording that encouraged broad refactors, stale priorities, or
  overconfident scientific claims;
- missing artifact fields that made review harder;
- commit messages or PR bodies that failed to connect changes to the cycle
  rationale.

When a prompt-improvement note recurs across sessions, map it back into durable
documentation rather than leaving it only in a chat transcript. Good homes are:

- `AGENTS.md` for agent operating rules and required handoff behavior;
- `docs/onboarding.md` for local environment and toolchain substitutions;
- `docs/autonomous_development_program.md` for autonomous-session prompt
  wording and stop conditions;
- `docs/autonomous_sessions/template.md` for fields that should appear in every
  future session log.

Update this document only when there is concrete evidence from one or more
session logs.
