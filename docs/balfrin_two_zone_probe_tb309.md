# TB-309 Smallest Two-Zone Balfrin Probe Result

Date: 2026-05-19

Status: fail-closed before scheduler submission.

TB-309 reran the live Balfrin access, remote-hygiene, authorization-audit,
reducer-budget, output-profile, and output-budget gates for the smallest
two-zone `postproc` probe. The Balfrin checkout was first fast-forwarded from
`722f7c7ebb7ace7927b5502c46ea3cec99b48ce9` to current `main` at
`34ead5c8e39842e66c1051a7e474180296a1bbd6`; the rerun access preflight then
reported `ready_for_read_only_collection`, `ready_for_pre_submit=true`, remote
branch `main`, dirty path count `0`, and no untracked generated files.

The smallest authorization preflight passed with:

- `preflight_status=ready_for_authorization_review`
- `ready_for_authorized_submission=true`
- `reviewed_handoff_package_status=reviewed`
- `authorization_record_status=reviewed`
- `balfrin_access_status=ready_for_read_only_collection`
- `reducer_budget_status=ready`
- `output_profile_status=ready`
- `output_budget_acceptance_status=accepted`
- run shape: `2` release zones, `2` scenarios, `2` trajectory workers, `2`
  reducer workers, and `2` reducer chunks

The reviewed handoff package checksum was
`8e0a01fd787f941775c51ef7ade12cf18ab370796f6b518be0fd1dd9b5d6e808`.
The original authorization record checksum was
`a92371d0117f39ba5657480090d8173a9cc50808174afa38101c1c80e4291fe4`.
For the Balfrin-side validation, a remote-path audit copy changed only
`reviewed_handoff_package_path` from the macOS `/private/tmp/...` path to the
Balfrin `/tmp/...` path; that remote audit copy checksum was
`7bbde4900c4389ceab74e1b4bf909f164444c4dc0697c7985865e20204759cc5`.

Submission did not reach `sbatch`. The exact reviewed submit path currently
passes `validation/pilot_runs/tschamut_public_balfrin_target_area_demo_v1.yaml`
to `scripts/submit_balfrin_probe.py`, but that helper requires a
`public_real_site_conditional_pilot_run_v1` probe manifest. The command failed
before writing a submission report or run root with:

```text
validate_public_real_site_conditional_pilot_run.PilotRunError:
schema_version must be public_real_site_conditional_pilot_run_v1
```

Post-attempt confirmation:

- no `submitted_job_id` was produced
- `squeue -u "$USER"` showed no TB-309 job
- the intended writable Balfrin run root
  `/scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/tschamut_public_balfrin_multi_release_zone_v1`
  was absent after the failed pre-scheduler attempt

Current exact technical blocker: the reviewed smallest two-zone package submit
command is not executable by the current SLURM probe driver because it supplies
the target-area wrapper contract instead of the executable pilot-run probe
manifest. The next task should repair or regenerate the reviewed two-zone
submit package so the package, authorization audit record, and
`submit_balfrin_probe.py` agree on an executable manifest before any new live
submission attempt.

TB-320 repair: regenerate the handoff package with:

```bash
PYENV_VERSION=system uv run python scripts/generate_balfrin_multi_release_zone_demo_handoff.py --format json
```

The repaired review and submit commands now pass
`validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml`, whose
schema is `public_real_site_conditional_pilot_run_v1`, to
`scripts/submit_balfrin_probe.py`. The old target-area wrapper path remains a
fail-closed contract mismatch. Before a GPT-5.5 Balfrin worker submits the
two-zone job, the remaining live-run gates are Balfrin access/checkout hygiene,
reviewed handoff package and authorization-record checksum agreement,
reducer/output-budget readiness, preservation-gate planning, and the explicit
`postproc` scheduler submit step.

Boundary: this is not measured multi-zone Balfrin evidence. It does not
authorize a larger run, non-`postproc` partition, distributed execution,
scale-up claim, annual-frequency or physical-probability claim,
risk/exposure/vulnerability product, or operational use.
