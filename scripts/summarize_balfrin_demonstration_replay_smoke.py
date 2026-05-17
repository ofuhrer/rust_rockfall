#!/usr/bin/env python3
"""Smoke-test Balfrin demonstration replay from a measured run root.

The helper is read-only. It checks that a run root is present, rebuilds the
Balfrin probe metrics, canonical evidence bundle, and post-run interpretation
gate from available artifacts, and fails closed when the run root or required
evidence inputs are absent.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import audit_gis_cog_package_readiness as gis_cog
from scripts import collect_balfrin_probe_metrics as probe_metrics
from scripts import summarize_balfrin_evidence_bundle as bundle
from scripts import summarize_balfrin_post_run_interpretation_gate as post_run_gate
from scripts import summarize_balfrin_single_job_execution as single_job


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "balfrin_demonstration_replay_smoke_v1"
DEFAULT_ARTIFACT_DIR = ROOT / "validation/private/tschamut_public_pilot/balfrin_demonstration_replay_smoke_v1"


class BalfrinDemonstrationReplaySmokeError(ValueError):
    """User-facing smoke-test error."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--artifact-dir", type=Path, default=DEFAULT_ARTIFACT_DIR)
    parser.add_argument("--format", choices=("json", "text"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    parser.add_argument("--text-output", type=Path, default=None)
    args = parser.parse_args(argv)

    try:
        report = build_report(run_root=args.run_root, artifact_dir=args.artifact_dir)
    except BalfrinDemonstrationReplaySmokeError as exc:
        print(f"balfrin demonstration replay smoke error: {exc}", file=sys.stderr)
        return 2

    materialize_artifacts(report, json_output=args.json_output, text_output=args.text_output)

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text_report(report))
    return 0 if report["smoke_status"] != "blocked_missing_inputs" else 2


def build_report(*, run_root: Path, artifact_dir: Path = DEFAULT_ARTIFACT_DIR) -> dict[str, Any]:
    run_root = run_root.expanduser()
    artifact_dir = artifact_dir.expanduser()
    if not run_root.exists():
        missing_inputs = [str(run_root)]
        return blocked_report(
            missing_inputs,
            reason=f"run root is missing: {run_root}",
            run_root=run_root,
            artifact_dir=artifact_dir,
        )

    probe_summary = probe_metrics.collect_run_metrics(run_root)
    single_job_summary = single_job.build_summary()
    gis_report = gis_cog.build_gis_cog_readiness_report()
    post_run_evidence = bundle.build_post_run_evidence(
        single_job_summary=single_job_summary,
        gis_report=gis_report,
        probe_metrics=probe_summary,
    )
    post_run_report = post_run_gate.build_report(post_run_evidence)
    bundle_report = bundle.build_report(
        {
            "single_job_execution_summary": single_job_summary,
            "probe_metrics": probe_summary,
            "post_run_interpretation_gate_report": post_run_report,
            "gis_cog_readiness_report": gis_report,
            "source_paths": build_source_paths(
                run_root=run_root,
                artifact_dir=artifact_dir,
                probe_summary=probe_summary,
                single_job_summary=single_job_summary,
                gis_report=gis_report,
            ),
            "canonical_bundle_path": artifact_dir,
        }
    )

    probe_metrics_status = str(probe_summary.get("metrics_contract_status") or "blocked_missing_inputs")
    smoke_status = "replayable"
    smoke_blockers = list(bundle_report.get("missing_inputs") or [])
    if bundle_report.get("bundle_status") == "blocked_missing_inputs" or post_run_report.get(
        "interpretation_status"
    ) == "blocked_missing_inputs":
        smoke_status = "blocked_missing_inputs"
    if probe_metrics_status == "blocked_missing_inputs":
        smoke_status = "blocked_missing_inputs"
        for missing in probe_summary.get("metrics_contract_missing_metrics", []):
            if missing not in smoke_blockers:
                smoke_blockers.append(str(missing))
    if not smoke_blockers and smoke_status == "blocked_missing_inputs":
        smoke_blockers = ["replay_artifacts"]

    return {
        "schema_version": SCHEMA_VERSION,
        "smoke_status": smoke_status,
        "run_root": str(run_root),
        "artifact_dir": str(artifact_dir),
        "run_root_status": "present",
        "probe_metrics_status": probe_metrics_status,
        "bundle_status": bundle_report.get("bundle_status", "blocked_missing_inputs"),
        "post_run_interpretation_status": post_run_report.get("interpretation_status", "blocked_missing_inputs"),
        "bundle_report": bundle_report,
        "post_run_interpretation_gate_report": post_run_report,
        "source_paths": build_source_paths(
            run_root=run_root,
            artifact_dir=artifact_dir,
            probe_summary=probe_summary,
            single_job_summary=single_job_summary,
            gis_report=gis_report,
        ),
        "missing_inputs": smoke_blockers,
        "claim_boundaries": post_run_report.get("claim_boundaries", post_run_gate.claim_boundaries()),
    }


def blocked_report(
    missing_inputs: list[str],
    *,
    reason: str,
    run_root: Path,
    artifact_dir: Path,
) -> dict[str, Any]:
    bundle_report = bundle.build_report(
        {
            "missing_inputs": list(missing_inputs),
            "canonical_bundle_path": artifact_dir,
        }
    )
    post_run_report = post_run_gate.build_report({"missing_inputs": ["post_run_evidence_bundle"]})
    return {
        "schema_version": SCHEMA_VERSION,
        "smoke_status": "blocked_missing_inputs",
        "run_root": str(run_root),
        "artifact_dir": str(artifact_dir),
        "run_root_status": "missing",
        "probe_metrics_status": "blocked_missing_inputs",
        "bundle_status": bundle_report.get("bundle_status", "blocked_missing_inputs"),
        "post_run_interpretation_status": post_run_report.get("interpretation_status", "blocked_missing_inputs"),
        "bundle_report": bundle_report,
        "post_run_interpretation_gate_report": post_run_report,
        "source_paths": {
            "run_root": str(run_root),
            "artifact_dir": str(artifact_dir),
        },
        "missing_inputs": list(missing_inputs),
        "blocked_reason": reason,
        "claim_boundaries": post_run_report.get("claim_boundaries", post_run_gate.claim_boundaries()),
    }


def build_source_paths(
    *,
    run_root: Path,
    artifact_dir: Path,
    probe_summary: dict[str, Any],
    single_job_summary: dict[str, Any],
    gis_report: dict[str, Any],
) -> dict[str, Any]:
    return {
        "run_root": str(run_root),
        "artifact_dir": str(artifact_dir),
        "probe_metrics": str(run_root / "balfrin_probe_summary.json"),
        "single_job_record_paths": single_job_summary.get("record_paths", {}),
        "gis_artifact_roots": gis_report.get("artifact_roots", []),
        "post_run_contract_path": str(post_run_gate.DEFAULT_CONTRACT),
    }


def render_text_report(report: dict[str, Any]) -> str:
    lines = [
        "Balfrin Demonstration Replay Smoke",
        f"schema_version: {report['schema_version']}",
        f"smoke_status: {report['smoke_status']}",
        f"run_root_status: {report['run_root_status']}",
        f"run_root: {report['run_root']}",
        f"artifact_dir: {report['artifact_dir']}",
        f"probe_metrics_status: {report['probe_metrics_status']}",
        f"bundle_status: {report['bundle_status']}",
        f"post_run_interpretation_status: {report['post_run_interpretation_status']}",
        "claim_boundaries:",
        f"  operational_claims_allowed: {report['claim_boundaries'].get('operational_claims_allowed', False)}",
        f"  physical_probability_claims_allowed: {report['claim_boundaries'].get('physical_probability_claims_allowed', False)}",
        f"  annual_frequency_claims_allowed: {report['claim_boundaries'].get('annual_frequency_claims_allowed', False)}",
        f"  risk_exposure_vulnerability_claims_allowed: {report['claim_boundaries'].get('risk_exposure_vulnerability_claims_allowed', False)}",
        f"  scale_up_authorized: {report['claim_boundaries'].get('scale_up_authorized', False)}",
        f"  distributed_execution_authorized: {report['claim_boundaries'].get('distributed_execution_authorized', False)}",
    ]
    if report.get("missing_inputs"):
        lines.append("missing_inputs:")
        lines.extend(f"  - {item}" for item in report["missing_inputs"])
    lines.extend(
        [
            "",
            "bundle_report:",
            f"  bundle_summary_status: {report['bundle_report'].get('bundle_summary', {}).get('status', 'unknown')}",
            f"  bundle_summary: {report['bundle_report'].get('bundle_summary', {}).get('summary', 'unknown')}",
            "",
            "post_run_interpretation_gate_report:",
            f"  artifact_acceptance_status: {report['post_run_interpretation_gate_report'].get('artifact_acceptance_status', 'unknown')}",
            f"  usable_as_conditional_diagnostic_artifact: {report['post_run_interpretation_gate_report'].get('usable_as_conditional_diagnostic_artifact', False)}",
        ]
    )
    return "\n".join(lines)


def materialize_artifacts(
    report: dict[str, Any],
    *,
    json_output: Path | None = None,
    text_output: Path | None = None,
) -> None:
    artifact_dir = Path(report["artifact_dir"])
    artifact_dir.mkdir(parents=True, exist_ok=True)

    bundle.materialize_artifacts(report["bundle_report"], artifact_dir=artifact_dir)

    post_run_json = artifact_dir / f"{post_run_gate.SCHEMA_VERSION}.json"
    post_run_text = artifact_dir / f"{post_run_gate.SCHEMA_VERSION}.txt"
    post_run_json.write_text(
        json.dumps(report["post_run_interpretation_gate_report"], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    post_run_text.write_text(post_run_gate.render_text_report(report["post_run_interpretation_gate_report"]), encoding="utf-8")

    smoke_json = json_output or (artifact_dir / f"{SCHEMA_VERSION}.json")
    smoke_text = text_output or (artifact_dir / f"{SCHEMA_VERSION}.txt")
    smoke_json.parent.mkdir(parents=True, exist_ok=True)
    smoke_text.parent.mkdir(parents=True, exist_ok=True)
    smoke_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    smoke_text.write_text(render_text_report(report), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
