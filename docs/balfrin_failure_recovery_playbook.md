# Balfrin Failure-Recovery Playbook

This playbook covers the current Balfrin single-release-zone demo path in this
repository. The helper names still carry the historical `tschamut` prefix, but
the recovery steps below are the active Balfrin operator entry points.

The goal is deterministic recovery, not ad-hoc debugging. Do not rerun with a
different run root, different run id, or different command plan unless the
recorded failure class requires it.

## Shared setup

```bash
RUN_MANIFEST="${RUN_MANIFEST:-validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml}"
RUN_ID="${RUN_ID:-tschamut_public_balfrin_single_release_zone_v1}"
RUN_ROOT="${RUN_ROOT:-${SCRATCH:-/scratch}/rust_rockfall/probes/balfrin-demo/${RUN_ID}}"
```

Use the same `RUN_ROOT` and `RUN_ID` for submit, collect, and interpretation
recovery. That keeps the artifacts deterministic and prevents accidental state
splits.

## Taxonomy

The canonical machine-readable taxonomy helper is
`scripts/summarize_balfrin_failure_taxonomy.py`. The table below is the same
operator vocabulary in prose form.

| Category | Machine-readable failure class | Primary signal | Recovery action |
| --- | --- | --- | --- |
| Infrastructure | `readiness_blocked` | `scripts/check_balfrin_tschamut_readiness.py` returns `status: blocked_for_balfrin_readiness` and a non-empty `blocking_checks` list | Repair the reported blocker, then rerun readiness and regenerate the package with the same run identifiers. |
| Orchestration | `scheduler_submission_failed` | `scripts/submit_balfrin_probe.py --submit` exits non-zero or never prints `submitted_job_id=` | Regenerate the same submission package, inspect it, and submit again with the same run identifiers. |
| Artifact | `partial_output_incomplete` | `scripts/collect_balfrin_probe_metrics.py` reports `metrics_contract_status: blocked_missing_inputs` with missing output-family fields | Archive the partial run root, keep the successful outputs, and rerun the same submit command after the job is cleared. |
| Metrics | `metrics_blocked` | `metrics_contract_missing_metrics` is non-empty or `log_audit.error_like_line_count` is non-zero | Rerun the metrics collector on the same run root, then inspect the missing fields before deciding whether the job must be replayed. |
| GIS/export | `gis_export_blocked` | `scripts/audit_gis_cog_package_readiness.py` returns `gis_cog_readiness_status` of `blocked_missing_inputs`, `metadata_only`, or `gis_package_ready_cog_blocked` | Repair the missing package fields or exported raster paths, then rerun the GIS/COG audit on the same artifact roots. |
| Scientific state | `interpretation_blocked` | `scripts/summarize_balfrin_post_run_interpretation_gate.py` returns `interpretation_status: blocked_missing_inputs` or `inconclusive_conditional_diagnostic` | Rebuild the evidence bundle, rerun the interpretation gate on the same evidence JSON, and keep the claim boundaries false. |

## Recovery Procedures

### 1) Readiness

Trigger:

- `status: blocked_for_balfrin_readiness`
- one or more entries in `blocking_checks`

Commands:

```bash
PYENV_VERSION=system uv run python scripts/check_balfrin_tschamut_readiness.py \
  "$RUN_MANIFEST" --format json >/tmp/balfrin_readiness.json
PYENV_VERSION=system uv run python - <<'PY'
import json
from pathlib import Path

payload = json.loads(Path("/tmp/balfrin_readiness.json").read_text(encoding="utf-8"))
assert payload["status"] in {"ready_for_balfrin_target_gate", "blocked_for_balfrin_readiness"}
assert "blocking_checks" in payload
assert "checks" in payload
print(payload["status"])
print(",".join(payload.get("blocking_checks", [])))
PY
```

Recovery rule:

- If the blocker is missing input data or a missing tool, fix that path or tool
  first, then rerun readiness with the same `RUN_MANIFEST`.
- If the only warning is missing QGIS, do not stop the demo. The helper reports
  that as a warning, not a hard blocker.

### 2) Scheduler

Trigger:

- `scripts/submit_balfrin_probe.py --submit` returns a non-zero exit status
- no `submitted_job_id=` line is printed

Commands:

```bash
PYENV_VERSION=system uv run python scripts/submit_balfrin_probe.py \
  "$RUN_MANIFEST" \
  --run-root "$RUN_ROOT" \
  --run-id "$RUN_ID" \
  --partition postproc \
  --time 00:30:00 \
  --nodes 1 \
  --ntasks 1 \
  --cpus-per-task 16 \
  --generate-only
sed -n '1,220p' "$RUN_ROOT/balfrin_submission_package.json"
PYENV_VERSION=system uv run python scripts/submit_balfrin_probe.py \
  "$RUN_MANIFEST" \
  --run-root "$RUN_ROOT" \
  --run-id "$RUN_ID" \
  --partition postproc \
  --time 00:30:00 \
  --nodes 1 \
  --ntasks 1 \
  --cpus-per-task 16 \
  --submit
```

If `sbatch` is missing or unreachable, the submit helper writes
`$RUN_ROOT/balfrin_submission_report.json` and prints the same structured
report to stdout with `status: scheduler_submission_failed`.

Recovery rule:

- Keep the exact same run root and run id.
- If `sbatch` fails again, capture the handoff archive from the run root before
  any cleanup or rerun.
- If a job id was printed but the job later fails, inspect it with
  `squeue -j "$JOB_ID" -o "%.18i %.9T %.50R"` and `scontrol show job "$JOB_ID"`.

### 3) Partial Output

Trigger:

- `metrics_contract_status: blocked_missing_inputs`
- missing `validation_output.*`, `hazard_output.*`, or restartability metadata

Commands:

```bash
PYENV_VERSION=system uv run python scripts/collect_balfrin_probe_metrics.py \
  --run-root "$RUN_ROOT" \
  --output-json /tmp/balfrin_probe_metrics.json
PYENV_VERSION=system uv run python - <<'PY'
import json
from pathlib import Path

payload = json.loads(Path("/tmp/balfrin_probe_metrics.json").read_text(encoding="utf-8"))
print(payload["metrics_contract_status"])
print(",".join(payload.get("metrics_contract_missing_metrics", [])))
print(payload["output_root"])
PY
tar -C "$RUN_ROOT" -czf "/tmp/${RUN_ID}_balfrin_probe_handoff.tgz" \
  logs \
  command_plan.json \
  probe.sbatch \
  balfrin_submission_package.json \
  balfrin_submission_package.md \
  balfrin_probe_summary.json \
  balfrin_probe_context.txt \
  balfrin_probe_full_time.txt \
  balfrin_hazard_stage_time.txt
```

Recovery rule:

- Do not delete the entire run root unless the collected summary shows the
  partial tree is irrecoverable.
- Preserve the logs and summary first, then replay the same submit command with
  the same run root and run id.

### 4) Metrics

Trigger:

- `metrics_contract_missing_metrics` is non-empty
- `log_audit.error_like_line_count` is non-zero

Commands:

```bash
PYENV_VERSION=system uv run python scripts/collect_balfrin_probe_metrics.py \
  --run-root "$RUN_ROOT" \
  --output-json /tmp/balfrin_probe_metrics.json
PYENV_VERSION=system uv run python - <<'PY'
import json
from pathlib import Path

summary = json.loads(Path("/tmp/balfrin_probe_metrics.json").read_text(encoding="utf-8"))
print(summary.get("metrics_contract_status", "unknown"))
print(summary.get("metrics_contract_missing_metrics", []))
print(summary.get("log_audit", {}).get("error_like_line_count", "unknown"))
PY
```

Recovery rule:

- If the summary is blocked only because files are still missing, rerun the
  submit path for the same run root.
- If the summary is complete but the log audit shows error-like lines, inspect
  the affected log paths before touching outputs.

### 5) GIS / Export

Trigger:

- `gis_cog_readiness_status: blocked_missing_inputs`
- `gis_cog_readiness_status: metadata_only`
- `gis_cog_readiness_status: gis_package_ready_cog_blocked`

Commands:

```bash
PYENV_VERSION=system uv run python scripts/audit_gis_cog_package_readiness.py \
  --format json \
  --artifact-root hazard/results/tschamut_public_pilot/gate_v1 \
  --artifact-root hazard/results/tschamut_public_pilot/target_gate_v1 \
  >/tmp/balfrin_gis_cog.json
PYENV_VERSION=system uv run python - <<'PY'
import json
from pathlib import Path

payload = json.loads(Path("/tmp/balfrin_gis_cog.json").read_text(encoding="utf-8"))
print(payload["gis_cog_readiness_status"])
print(payload.get("converted_package_readiness_status", "not_provided"))
print(payload.get("qgis_manual_qa_status", "not_provided"))
PY
```

Recovery rule:

- `blocked_missing_inputs`: repair the manifest or raster path that the audit
  reports, then rerun the audit.
- `metadata_only`: keep the run diagnostic only; this means the machine lacks
  the raster metadata toolchain and should not be treated as a stronger export
  failure.
- `gis_package_ready_cog_blocked`: accept the state as scope-limited unless the
  task explicitly asks for a COG conversion proof.

### 6) Scientific State / Interpretation

Trigger:

- `interpretation_status: blocked_missing_inputs`
- `interpretation_status: inconclusive_conditional_diagnostic`

Commands:

```bash
PYENV_VERSION=system uv run python scripts/summarize_balfrin_evidence_bundle.py \
  --artifact-dir validation/private/tschamut_public_pilot/balfrin_evidence_bundle_v1
PYENV_VERSION=system uv run python scripts/summarize_balfrin_post_run_interpretation_gate.py \
  --format json \
  --evidence-json "$RUN_ROOT/balfrin_post_run_evidence.json" \
  >/tmp/balfrin_post_run_gate.json
PYENV_VERSION=system uv run python - <<'PY'
import json
from pathlib import Path

payload = json.loads(Path("/tmp/balfrin_post_run_gate.json").read_text(encoding="utf-8"))
print(payload["interpretation_status"])
print(payload["artifact_acceptance_status"])
print(payload["required_readiness"]["status"])
print(payload["required_output"]["status"])
print(payload["required_gis_cog"]["status"])
PY
```

Recovery rule:

- If the gate is blocked, rebuild the evidence bundle first and rerun the gate
  on the same evidence JSON.
- If the gate is inconclusive, keep the artifact accepted only as a conditional
  diagnostic and do not widen the claim boundary.

## Smoke checks

These are the minimal command-output checks the playbook relies on:

1. Readiness output:

```bash
PYENV_VERSION=system uv run python scripts/check_balfrin_tschamut_readiness.py \
  "$RUN_MANIFEST" --format json >/tmp/balfrin_readiness.json
PYENV_VERSION=system uv run python - <<'PY'
import json
from pathlib import Path

payload = json.loads(Path("/tmp/balfrin_readiness.json").read_text(encoding="utf-8"))
assert "status" in payload
assert "blocking_checks" in payload
assert "checks" in payload
PY
```

2. Metrics output:

```bash
PYENV_VERSION=system uv run python scripts/collect_balfrin_probe_metrics.py \
  --run-root "$RUN_ROOT" \
  --output-json /tmp/balfrin_probe_metrics.json
PYENV_VERSION=system uv run python - <<'PY'
import json
from pathlib import Path

payload = json.loads(Path("/tmp/balfrin_probe_metrics.json").read_text(encoding="utf-8"))
assert "metrics_contract_status" in payload
assert "metrics_contract_missing_metrics" in payload
assert "log_audit" in payload
PY
```

3. GIS / export output:

```bash
PYENV_VERSION=system uv run python scripts/audit_gis_cog_package_readiness.py \
  --format json \
  --artifact-root hazard/results/tschamut_public_pilot/gate_v1 \
  >/tmp/balfrin_gis_cog.json
PYENV_VERSION=system uv run python - <<'PY'
import json
from pathlib import Path

payload = json.loads(Path("/tmp/balfrin_gis_cog.json").read_text(encoding="utf-8"))
assert "gis_cog_readiness_status" in payload
assert "converted_package_readiness_status" in payload
assert "qgis_manual_qa_status" in payload
PY
```

4. Interpretation output:

```bash
PYENV_VERSION=system uv run python scripts/summarize_balfrin_post_run_interpretation_gate.py \
  --format json \
  --evidence-json "$RUN_ROOT/balfrin_post_run_evidence.json" \
  >/tmp/balfrin_post_run_gate.json
PYENV_VERSION=system uv run python - <<'PY'
import json
from pathlib import Path

payload = json.loads(Path("/tmp/balfrin_post_run_gate.json").read_text(encoding="utf-8"))
assert "interpretation_status" in payload
assert "artifact_acceptance_status" in payload
assert "required_checks" in payload
PY
```
