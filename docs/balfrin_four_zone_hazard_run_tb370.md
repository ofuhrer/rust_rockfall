# TB-370 Balfrin Four-Zone Hazard Run Outcome

Date: 2026-05-20

## Summary

TB-370 did not submit a live four-zone Balfrin job. The task failed closed
before `sbatch` because the current four-zone handoff package generated on the
clean Balfrin checkout did not pass the repository live-submit decision gate.

The precise blocker is the four-zone package contract:

- `four_zone_status`: `deferred_missing_measured_two_zone_evidence`
- `four_zone_decision`: `defer`
- `four_zone_ready_for_submit`: `false`
- `four_zone_reason`: `TB-362 failed closed before scheduler submission with output_profile_status=blocked_output_profile; no measured two-zone hazard evidence is available.`
- `review_readiness_classification`: `blocked_efficiency`
- `review_readiness_reason`: `single-job sufficiency or reducer scaling is not yet ready for the four-zone review package`

The output-budget side of the four-zone package was not the blocker:

- `release_zone_count`: `4`
- `scenario_count`: `4`
- `four_zone_output_budget`: `accepted`
- `four_zone_budget_profile`: `next_larger_four_zone_review_only_probe`

## Gate Evidence

The Balfrin checkout was fast-forwarded before live consideration:

- Remote checkout: `/users/olifu/work/rust_rockfall`
- Remote head after fast-forward: `00e0fd429f4f60ceb1add0f8407ac9c60521e947`
- Remote checkout hygiene: clean
- Fresh access preflight: `ready_for_read_only_collection`
- `ready_for_pre_submit`: `true`

The TB-368 two-zone run root was verified on Balfrin with the preservation
helper:

- Run root:
  `/scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_multi_release_zone_v1`
- `gate_status`: `ready_for_demonstration_evidence`
- `metrics_contract_status`: `complete`
- `required_run_root_entries_status`: `complete`
- Missing metrics: none
- Missing run-root entries: none
- Missing output families: none

The repository four-zone handoff helper still fails closed for live submission
despite the preserved TB-368 run-root evidence. The next unblock action is to
repair the handoff/scale-readiness evidence contract so the current TB-368
measured two-zone preservation evidence is consumed by the four-zone live-submit
decision, then regenerate the four-zone package and rerun the same pre-submit
chain.

## Boundaries

- No `sbatch` command was run for TB-370.
- No four-zone job id, run root, metrics JSON, or preservation-gate output was
  produced.
- No non-`postproc` partition was used.
- No distributed execution or scale-up claim is made.
- No operational hazard assessment is made.
- No annual-frequency, physical-probability, risk, exposure, or vulnerability
  claim is made.
