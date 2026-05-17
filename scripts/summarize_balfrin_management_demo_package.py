#!/usr/bin/env python3
"""Summarize the Balfrin management demonstration package.

This helper composes the measured Balfrin evidence bundle with a replay smoke
check into one compact review package. It keeps runtime, replay,
restartability, GIS scope, uncertainty, and claim-boundary sections separate
so a non-developer reviewer can see what the demo proves and what it does not
prove without collapsing fixture-backed replay evidence into measured evidence.
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
from scripts import summarize_balfrin_demonstration_replay_smoke as replay_smoke
from scripts import summarize_balfrin_evidence_bundle as bundle
from scripts import summarize_balfrin_post_run_interpretation_gate as post_run_gate
from scripts import summarize_balfrin_single_job_execution as single_job


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "balfrin_management_demo_package_v1"
DEFAULT_ARTIFACT_DIR = ROOT / "validation/private/tschamut_public_pilot/balfrin_management_demo_package_v1"
DEFAULT_REPLAY_RUN_ROOT = ROOT / "tests/fixtures/balfrin_probe_metrics_contract/complete_run_root"


class BalfrinManagementDemoPackageError(ValueError):
    """User-facing management package error."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-root", type=Path, default=DEFAULT_REPLAY_RUN_ROOT)
    parser.add_argument("--artifact-dir", type=Path, default=DEFAULT_ARTIFACT_DIR)
    parser.add_argument("--format", choices=("json", "text"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    parser.add_argument("--text-output", type=Path, default=None)
    parser.add_argument(
        "--evidence-json",
        type=Path,
        default=None,
        help="optional override JSON file for tests or alternate package snapshots",
    )
    args = parser.parse_args(argv)

    try:
        report = build_report(
            run_root=args.run_root,
            artifact_dir=args.artifact_dir,
            evidence_override=load_evidence_override(args.evidence_json),
        )
    except BalfrinManagementDemoPackageError as exc:
        print(f"balfrin management demo package error: {exc}", file=sys.stderr)
        return 2

    materialize_artifacts(report, json_output=args.json_output, text_output=args.text_output)

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text_report(report))
    return 0 if report["package_status"] != "blocked_missing_inputs" else 2


def load_evidence_override(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    if not path.exists():
        raise BalfrinManagementDemoPackageError(f"evidence override file is missing: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise BalfrinManagementDemoPackageError("evidence override must be a JSON object")
    return data


def build_report(
    *,
    run_root: Path,
    artifact_dir: Path = DEFAULT_ARTIFACT_DIR,
    evidence_override: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if evidence_override is None:
        return build_current_report(run_root=run_root, artifact_dir=artifact_dir)
    if evidence_override.get("missing_inputs"):
        missing_inputs = [str(item) for item in evidence_override.get("missing_inputs", [])]
        return blocked_report(
            missing_inputs,
            reason="required package inputs are missing",
            run_root=run_root,
            artifact_dir=artifact_dir,
        )
    if isinstance(evidence_override.get("package_report"), dict):
        return dict(evidence_override["package_report"])

    required_keys = (
        "runtime_section",
        "replay_section",
        "restartability_section",
        "gis_scope_section",
        "uncertainty_section",
        "claim_boundary_section",
    )
    if any(key in evidence_override for key in required_keys):
        missing_inputs = [key for key in required_keys if key not in evidence_override]
        if missing_inputs:
            return blocked_report(
                missing_inputs,
                reason="required package sections are missing",
                run_root=run_root,
                artifact_dir=artifact_dir,
            )
        return assemble_package_report(
            runtime_section=dict(evidence_override["runtime_section"]),
            replay_section=dict(evidence_override["replay_section"]),
            restartability_section=dict(evidence_override["restartability_section"]),
            gis_scope_section=dict(evidence_override["gis_scope_section"]),
            uncertainty_section=dict(evidence_override["uncertainty_section"]),
            claim_boundary_section=dict(evidence_override["claim_boundary_section"]),
            scaling_section=dict(evidence_override["scaling_section"]),
            next_decision_section=dict(evidence_override["next_decision_section"]),
            source_artifacts=as_mapping(evidence_override.get("source_artifacts")),
            regeneration_commands=listify(evidence_override.get("regeneration_commands")),
            package_artifact_dir=Path(str(evidence_override.get("package_artifact_dir") or artifact_dir)),
            run_root=Path(str(evidence_override.get("run_root") or run_root)),
        )

    return build_current_report(run_root=run_root, artifact_dir=artifact_dir)


def build_current_report(*, run_root: Path, artifact_dir: Path = DEFAULT_ARTIFACT_DIR) -> dict[str, Any]:
    if not run_root.exists():
        return blocked_report(
            [str(run_root)],
            reason=f"run root is missing: {run_root}",
            run_root=run_root,
            artifact_dir=artifact_dir,
        )

    bundle_report = bundle.build_current_report()
    smoke_report = replay_smoke.build_report(run_root=run_root, artifact_dir=artifact_dir / "replay_smoke_v1")
    post_run_report = dict(bundle_report.get("post_run_interpretation_gate_report") or {})
    if not post_run_report:
        post_run_report = post_run_gate.build_report(
            {
                "single_job_execution_summary": bundle_report.get("single_job_execution_summary", {}),
                "probe_metrics": bundle_report.get("probe_metrics", {}),
                "post_run_interpretation_gate_report": bundle_report.get(
                    "post_run_interpretation_gate_report", {}
                ),
                "gis_cog_readiness_report": bundle_report.get("gis_cog_readiness_report", {}),
            }
        )

    return assemble_package_report(
        runtime_section=build_runtime_section(bundle_report),
        replay_section=build_replay_section(smoke_report),
        restartability_section=build_restartability_section(bundle_report),
        gis_scope_section=build_gis_scope_section(bundle_report),
        uncertainty_section=build_uncertainty_section(bundle_report, smoke_report),
        claim_boundary_section=build_claim_boundary_section(post_run_report),
        scaling_section=build_scaling_section(bundle_report, post_run_report),
        next_decision_section=build_next_decision_section(bundle_report, post_run_report),
        source_artifacts=build_source_artifacts(
            bundle_report=bundle_report,
            smoke_report=smoke_report,
            package_artifact_dir=artifact_dir,
            run_root=run_root,
        ),
        regeneration_commands=build_regeneration_commands(run_root=run_root, package_artifact_dir=artifact_dir),
        package_artifact_dir=artifact_dir,
        run_root=run_root,
    )


def assemble_package_report(
    *,
    runtime_section: dict[str, Any],
    replay_section: dict[str, Any],
    restartability_section: dict[str, Any],
    gis_scope_section: dict[str, Any],
    uncertainty_section: dict[str, Any],
    claim_boundary_section: dict[str, Any],
    scaling_section: dict[str, Any],
    next_decision_section: dict[str, Any],
    source_artifacts: dict[str, Any],
    regeneration_commands: list[str],
    package_artifact_dir: Path,
    run_root: Path,
) -> dict[str, Any]:
    sections = [
        ("runtime_section", runtime_section, build_section_source_paths(runtime_section)),
        ("replay_section", replay_section, build_section_source_paths(replay_section)),
        ("restartability_section", restartability_section, build_section_source_paths(restartability_section)),
        ("gis_scope_section", gis_scope_section, build_section_source_paths(gis_scope_section)),
        ("uncertainty_section", uncertainty_section, build_section_source_paths(uncertainty_section)),
        ("claim_boundary_section", claim_boundary_section, build_section_source_paths(claim_boundary_section)),
        ("scaling_section", scaling_section, build_section_source_paths(scaling_section)),
        ("next_decision_section", next_decision_section, build_section_source_paths(next_decision_section)),
    ]
    section_provenance_profile = []
    for section_name, section_payload, source_paths in sections:
        section_provenance_profile.append(
            {
                "section": section_name,
                "status": section_status(section_payload),
                "evidence_type": classify_evidence_type(section_payload, source_paths),
                "source_paths": source_paths,
            }
        )

    package_status = derive_package_status(section_provenance_profile)
    package_summary = {
        "status": package_status,
        "summary": summarize_package(
            package_status,
            runtime_section,
            replay_section,
            uncertainty_section,
            claim_boundary_section,
            scaling_section,
            next_decision_section,
        ),
        "section_counts": section_provenance_counts(section_provenance_profile),
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "package_status": package_status,
        "package_provenance_status": package_status,
        "package_artifact_dir": str(package_artifact_dir),
        "run_root": str(run_root),
        "package_summary": package_summary,
        "runtime_section": runtime_section,
        "replay_section": replay_section,
        "restartability_section": restartability_section,
        "gis_scope_section": gis_scope_section,
        "uncertainty_section": uncertainty_section,
        "claim_boundary_section": claim_boundary_section,
        "scaling_section": scaling_section,
        "next_decision_section": next_decision_section,
        "claim_boundaries": claim_boundary_section.get("claim_boundaries", post_run_gate.claim_boundaries()),
        "section_provenance_profile": section_provenance_profile,
        "source_artifacts": source_artifacts,
        "regeneration_commands": regeneration_commands,
        "evidence_sources": evidence_sources(source_artifacts),
    }


def blocked_report(
    missing_inputs: list[str],
    *,
    reason: str,
    run_root: Path,
    artifact_dir: Path,
) -> dict[str, Any]:
    claim_boundaries = post_run_gate.claim_boundaries()
    section_names = (
        "runtime_section",
        "replay_section",
        "restartability_section",
        "gis_scope_section",
        "uncertainty_section",
        "claim_boundary_section",
        "scaling_section",
        "next_decision_section",
    )
    section_provenance_profile = [
        {
            "section": section_name,
            "status": "blocked_missing_inputs",
            "evidence_type": "blocked",
            "source_paths": [],
        }
        for section_name in section_names
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "package_status": "blocked_missing_inputs",
        "package_provenance_status": "blocked_missing_inputs",
        "package_artifact_dir": str(artifact_dir),
        "run_root": str(run_root),
        "package_summary": {
            "status": "blocked_missing_inputs",
            "summary": "Balfrin management package is blocked because one or more required sections are missing.",
            "section_counts": section_provenance_counts(section_provenance_profile),
        },
        "runtime_section": {"status": "blocked_missing_inputs"},
        "replay_section": {"status": "blocked_missing_inputs", "missing_inputs": list(missing_inputs)},
        "restartability_section": {"status": "blocked_missing_inputs"},
        "gis_scope_section": {"status": "blocked_missing_inputs"},
        "uncertainty_section": {"status": "blocked_missing_inputs"},
        "claim_boundary_section": {
            "status": "blocked_missing_inputs",
            "claim_boundaries": claim_boundaries,
        },
        "scaling_section": {"status": "blocked_missing_inputs"},
        "next_decision_section": {"status": "blocked_missing_inputs"},
        "claim_boundaries": claim_boundaries,
        "section_provenance_profile": section_provenance_profile,
        "source_artifacts": {
            "package_artifact_dir": str(artifact_dir),
            "run_root": str(run_root),
        },
        "regeneration_commands": build_regeneration_commands(run_root=run_root, package_artifact_dir=artifact_dir),
        "evidence_sources": evidence_sources({"run_root": str(run_root)}),
        "missing_inputs": list(missing_inputs),
        "blocked_reason": reason,
    }


def build_runtime_section(bundle_report: dict[str, Any]) -> dict[str, Any]:
    single_job_summary = dict(bundle_report.get("single_job_execution_summary") or {})
    probe_metrics = dict(bundle_report.get("probe_metrics") or {})
    metrics_contract = dict(single_job_summary.get("metrics_contract") or {})
    mandatory_metrics = dict(metrics_contract.get("mandatory_metrics") or {})
    section = {
        "status": str(bundle_report.get("bundle_status") or metrics_contract.get("status") or "blocked_missing_inputs"),
        "summary": (
            "Measured runtime, memory, and output footprint show the Balfrin demo is replayable without implying an operational hazard-map claim."
        ),
        "decision": single_job_summary.get("decision"),
        "single_job_sufficient_for_next_step": bool(single_job_summary.get("single_job_sufficient_for_next_step")),
        "wall_time_seconds": probe_metrics.get("wall_time_seconds"),
        "memory_peak_mb": probe_metrics.get("memory_peak_mb"),
        "validation_output": probe_metrics.get("validation_output", {}),
        "hazard_output": probe_metrics.get("hazard_output", {}),
        "conditional_curve_row_count": probe_metrics.get("conditional_curve_row_count"),
        "metrics_contract_status": metrics_contract.get("status"),
        "source_paths": build_runtime_source_paths(bundle_report),
    }
    if mandatory_metrics:
        section["restartability_metadata"] = mandatory_metrics.get("restartability_metadata", {})
    return section


def build_replay_section(smoke_report: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": str(smoke_report.get("smoke_status") or "blocked_missing_inputs"),
        "summary": (
            "Replay smoke proves the command path can be rerun from a present run root; fixture-backed replay remains distinct from measured runtime evidence."
        ),
        "run_root": smoke_report.get("run_root"),
        "run_root_provenance": smoke_report.get("run_root_provenance"),
        "run_root_status": smoke_report.get("run_root_status"),
        "bundle_status": smoke_report.get("bundle_status"),
        "post_run_interpretation_status": smoke_report.get("post_run_interpretation_status"),
        "missing_inputs": smoke_report.get("missing_inputs", []),
        "source_paths": build_section_source_paths(smoke_report),
    }


def build_restartability_section(bundle_report: dict[str, Any]) -> dict[str, Any]:
    single_job_summary = dict(bundle_report.get("single_job_execution_summary") or {})
    restartability = dict((single_job_summary.get("restartability_evidence") or {}))
    return {
        "status": str(bundle_report.get("bundle_status") or single_job_summary.get("metrics_contract", {}).get("status") or "blocked_missing_inputs"),
        "summary": (
            "The single-job path records repeatable job IDs and reducer state, while distributed execution stays deferred."
        ),
        "driver_ready_for_selected_gate_use": restartability.get("driver_ready_for_selected_gate_use"),
        "fresh_baseline_job_id": restartability.get("fresh_baseline_job_id"),
        "repeat_job_ids": restartability.get("repeat_job_ids", []),
        "repeat_reuse_classification": restartability.get("repeat_reuse_classification"),
        "trajectory_plan_id_stable": restartability.get("trajectory_plan_id_stable"),
        "reducer_plan_id_stable": restartability.get("reducer_plan_id_stable"),
        "numerical_artifact_classification": restartability.get("numerical_artifact_classification"),
        "changed_artifact_count": restartability.get("changed_artifact_count"),
        "output_file_count_stable": restartability.get("output_file_count_stable"),
        "metadata_byte_identity_required": restartability.get("metadata_byte_identity_required"),
        "local_restartability_status": restartability.get("local_restartability_status"),
        "reducer_state": bundle_report.get("single_job_execution_summary", {})
        .get("metrics_contract", {})
        .get("mandatory_metrics", {})
        .get("restartability_metadata", {}),
        "source_paths": build_runtime_source_paths(bundle_report),
    }


def build_gis_scope_section(bundle_report: dict[str, Any]) -> dict[str, Any]:
    gis_scope_report = dict(bundle_report.get("gis_cog_scope_report") or {})
    gis_report = dict(bundle_report.get("gis_cog_readiness_report") or {})
    return {
        "status": str(gis_scope_report.get("scope_status") or gis_report.get("gis_cog_readiness_status") or "blocked_missing_inputs"),
        "summary": (
            "GIS scope is explicit: the package distinguishes full scope, bounded scope, and blocked inputs without calling the result an operational map."
        ),
        "scope_status": gis_scope_report.get("scope_status"),
        "scope_delta_status": gis_scope_report.get("scope_delta_status"),
        "parity_status": gis_scope_report.get("parity_status"),
        "standard_package_readiness_status": gis_report.get("standard_package_readiness_status"),
        "converted_package_readiness_status": gis_report.get("converted_package_readiness_status"),
        "converted_package_layer_inventory_status": gis_report.get("converted_package_layer_inventory_status"),
        "layer_counts": bundle_report.get("gis_cog_parity_report", {}).get("layer_counts", {}),
        "scope_delta": bundle_report.get("gis_cog_parity_report", {}).get("scope_delta", {}),
        "manifest_consistency": bundle_report.get("gis_cog_parity_report", {}).get("manifest_consistency", {}),
        "source_paths": build_gis_source_paths(bundle_report),
    }


def build_uncertainty_section(bundle_report: dict[str, Any], smoke_report: dict[str, Any]) -> dict[str, Any]:
    post_run_report = dict(bundle_report.get("post_run_interpretation_gate_report") or {})
    failure_report = dict(bundle_report.get("failure_taxonomy_report") or {})
    return {
        "status": str(bundle_report.get("bundle_status") or post_run_report.get("interpretation_status") or "blocked_missing_inputs"),
        "evidence_type": "measured",
        "summary": (
            "Scientific meaning remains conditional and non-operational; the package separates measured evidence from fixture-backed replay and keeps the false claim boundaries intact."
        ),
        "bundle_status": bundle_report.get("bundle_status"),
        "bundle_summary": bundle_report.get("bundle_summary", {}),
        "interpretation_status": post_run_report.get("interpretation_status"),
        "artifact_acceptance_status": post_run_report.get("artifact_acceptance_status"),
        "taxonomy_status": failure_report.get("taxonomy_status"),
        "status_counts": failure_report.get("status_counts", {}),
        "section_counts": bundle_report.get("section_provenance_profile", []),
        "probe_metrics_status": bundle_report.get("probe_metrics", {}).get("status"),
        "smoke_status": smoke_report.get("smoke_status"),
        "smoke_missing_inputs": smoke_report.get("missing_inputs", []),
        "source_paths": build_uncertainty_source_paths(bundle_report, smoke_report),
    }


def build_claim_boundary_section(post_run_report: dict[str, Any]) -> dict[str, Any]:
    claim_boundaries = dict(post_run_report.get("claim_boundaries") or post_run_gate.claim_boundaries())
    return {
        "status": "guarded",
        "summary": (
            "Claim boundaries stay false: the package is a conditional diagnostic review artifact, not an operational, physical-probability, annual-frequency, or risk product."
        ),
        "claim_boundaries": claim_boundaries,
        "source_paths": [str(post_run_gate.DEFAULT_CONTRACT), "docs/balfrin_post_run_interpretation_gate.md"],
    }


def build_scaling_section(bundle_report: dict[str, Any], post_run_report: dict[str, Any]) -> dict[str, Any]:
    single_job_summary = dict(bundle_report.get("single_job_execution_summary") or {})
    claim_boundaries = dict(post_run_report.get("claim_boundaries") or post_run_gate.claim_boundaries())
    single_job_sufficient = bool(single_job_summary.get("single_job_sufficient_for_next_step"))
    scale_up_authorized = bool(claim_boundaries.get("scale_up_authorized", False))
    distributed_execution_authorized = bool(claim_boundaries.get("distributed_execution_authorized", False))
    if single_job_sufficient:
        scaling_implication = (
            "Keep the next step at the single-job boundary; scale-up and distributed execution stay deferred."
        )
    else:
        scaling_implication = (
            "Do not infer a scale-up path from this package; the current evidence does not justify moving beyond the single-job boundary."
        )
    return {
        "status": "measured",
        "summary": "Scaling stays bounded by the measured single-job path; the package does not authorize a larger execution mode.",
        "single_job_sufficient_for_next_step": single_job_sufficient,
        "scale_up_authorized": scale_up_authorized,
        "distributed_execution_authorized": distributed_execution_authorized,
        "scaling_implication": scaling_implication,
        "source_paths": build_runtime_source_paths(bundle_report),
    }


def build_next_decision_section(bundle_report: dict[str, Any], post_run_report: dict[str, Any]) -> dict[str, Any]:
    single_job_summary = dict(bundle_report.get("single_job_execution_summary") or {})
    claim_boundaries = dict(post_run_report.get("claim_boundaries") or post_run_gate.claim_boundaries())
    next_authorized_step = "management review of this package"
    if bool(single_job_summary.get("single_job_sufficient_for_next_step")) and not bool(
        claim_boundaries.get("scale_up_authorized", False)
    ):
        recommendation = (
            "The next authorized step is management review of this package; no new Balfrin submission, scale-up, or distributed execution is authorized here."
        )
    else:
        recommendation = (
            "The package stays advisory only; a separate authorization would be required before any further Balfrin execution."
        )
    return {
        "status": "deferred",
        "summary": "This package is for review and decision-making, not for launching another Balfrin job.",
        "recommended_next_authorized_step": next_authorized_step,
        "recommendation": recommendation,
        "source_paths": [str(post_run_gate.DEFAULT_CONTRACT), "docs/balfrin_single_job_execution_sufficiency.md"],
    }


def build_source_artifacts(
    *,
    bundle_report: dict[str, Any],
    smoke_report: dict[str, Any],
    package_artifact_dir: Path,
    run_root: Path,
) -> dict[str, Any]:
    return {
        "package_artifact_dir": str(package_artifact_dir),
        "bundle_artifact_dir": str(Path(bundle_report.get("canonical_bundle_path") or DEFAULT_ARTIFACT_DIR / "balfrin_evidence_bundle_v1")),
        "smoke_artifact_dir": str(smoke_report.get("artifact_dir") or (package_artifact_dir / "replay_smoke_v1")),
        "replay_run_root": str(run_root),
        "bundle_canonical_path": str(bundle_report.get("canonical_bundle_path") or ""),
        "smoke_run_root_provenance": smoke_report.get("run_root_provenance"),
    }


def build_regeneration_commands(*, run_root: Path, package_artifact_dir: Path) -> list[str]:
    bundle_artifact_dir = package_artifact_dir / "balfrin_evidence_bundle_v1"
    smoke_artifact_dir = package_artifact_dir / "balfrin_demonstration_replay_smoke_v1"
    return [
        " ".join(
            [
                "PYENV_VERSION=system",
                "uv",
                "run",
                "python",
                "scripts/summarize_balfrin_evidence_bundle.py",
                "--artifact-dir",
                str(bundle_artifact_dir),
            ]
        ),
        " ".join(
            [
                "PYENV_VERSION=system",
                "uv",
                "run",
                "python",
                "scripts/summarize_balfrin_demonstration_replay_smoke.py",
                "--run-root",
                str(run_root),
                "--artifact-dir",
                str(smoke_artifact_dir),
                "--format",
                "json",
            ]
        ),
        " ".join(
            [
                "PYENV_VERSION=system",
                "uv",
                "run",
                "python",
                "scripts/summarize_balfrin_management_demo_package.py",
                "--run-root",
                str(run_root),
                "--artifact-dir",
                str(package_artifact_dir),
                "--format",
                "json",
            ]
        ),
    ]


def render_text_report(report: dict[str, Any]) -> str:
    lines = [
        "Balfrin Management Demonstration Package",
        f"schema_version: {report['schema_version']}",
        f"package_status: {report['package_status']}",
        f"package_provenance_status: {report.get('package_provenance_status', report['package_status'])}",
        f"package_artifact_dir: {report['package_artifact_dir']}",
        f"run_root: {report['run_root']}",
        "package_summary:",
        f"  status: {report['package_summary']['status']}",
        f"  summary: {report['package_summary']['summary']}",
        "  section_counts:",
    ]
    for key in ("measured", "fixture_backed", "blocked_missing_inputs"):
        if key in report["package_summary"]["section_counts"]:
            lines.append(f"    {key}: {report['package_summary']['section_counts'][key]}")
    lines.extend(
        [
            "runtime_section:",
            f"  status: {report['runtime_section'].get('status', 'unknown')}",
            f"  wall_time_seconds: {report['runtime_section'].get('wall_time_seconds', 'unknown')}",
            f"  memory_peak_mb: {report['runtime_section'].get('memory_peak_mb', 'unknown')}",
            f"  single_job_sufficient_for_next_step: {report['runtime_section'].get('single_job_sufficient_for_next_step', False)}",
            "replay_section:",
            f"  status: {report['replay_section'].get('status', 'unknown')}",
            f"  run_root_provenance: {report['replay_section'].get('run_root_provenance', 'unknown')}",
            f"  run_root_status: {report['replay_section'].get('run_root_status', 'unknown')}",
            "restartability_section:",
            f"  status: {report['restartability_section'].get('status', 'unknown')}",
            f"  repeat_reuse_classification: {report['restartability_section'].get('repeat_reuse_classification', 'unknown')}",
            f"  trajectory_plan_id_stable: {report['restartability_section'].get('trajectory_plan_id_stable', False)}",
            f"  reducer_plan_id_stable: {report['restartability_section'].get('reducer_plan_id_stable', False)}",
            "gis_scope_section:",
            f"  status: {report['gis_scope_section'].get('status', 'unknown')}",
            f"  scope_status: {report['gis_scope_section'].get('scope_status', 'unknown')}",
            f"  scope_delta_status: {report['gis_scope_section'].get('scope_delta_status', 'unknown')}",
            "uncertainty_section:",
            f"  status: {report['uncertainty_section'].get('status', 'unknown')}",
            f"  interpretation_status: {report['uncertainty_section'].get('interpretation_status', 'unknown')}",
            f"  taxonomy_status: {report['uncertainty_section'].get('taxonomy_status', 'unknown')}",
            "claim_boundary_section:",
            f"  status: {report['claim_boundary_section'].get('status', 'unknown')}",
            f"  operational_claims_allowed: {report['claim_boundaries'].get('operational_claims_allowed', False)}",
            f"  physical_probability_claims_allowed: {report['claim_boundaries'].get('physical_probability_claims_allowed', False)}",
            f"  annual_frequency_claims_allowed: {report['claim_boundaries'].get('annual_frequency_claims_allowed', False)}",
            f"  risk_exposure_vulnerability_claims_allowed: {report['claim_boundaries'].get('risk_exposure_vulnerability_claims_allowed', False)}",
            f"  scale_up_authorized: {report['claim_boundaries'].get('scale_up_authorized', False)}",
            f"  distributed_execution_authorized: {report['claim_boundaries'].get('distributed_execution_authorized', False)}",
            "scaling_section:",
            f"  status: {report['scaling_section'].get('status', 'unknown')}",
            f"  single_job_sufficient_for_next_step: {report['scaling_section'].get('single_job_sufficient_for_next_step', False)}",
            f"  scale_up_authorized: {report['scaling_section'].get('scale_up_authorized', False)}",
            f"  distributed_execution_authorized: {report['scaling_section'].get('distributed_execution_authorized', False)}",
            f"  scaling_implication: {report['scaling_section'].get('scaling_implication', 'unknown')}",
            "next_decision_section:",
            f"  status: {report['next_decision_section'].get('status', 'unknown')}",
            f"  recommended_next_authorized_step: {report['next_decision_section'].get('recommended_next_authorized_step', 'unknown')}",
            f"  recommendation: {report['next_decision_section'].get('recommendation', 'unknown')}",
            "section_provenance_profile:",
        ]
    )
    for section in report["section_provenance_profile"]:
        lines.append(
            f"  - {section.get('section', 'unknown')}: {section.get('evidence_type', 'unknown')} | {section.get('status', 'unknown')}"
        )
    lines.append("regeneration_commands:")
    for command in report.get("regeneration_commands", []):
        lines.append(f"  - {command}")
    if report.get("missing_inputs"):
        lines.append("missing_inputs:")
        lines.extend(f"  - {item}" for item in report["missing_inputs"])
    return "\n".join(lines)


def materialize_artifacts(
    report: dict[str, Any],
    *,
    json_output: Path | None = None,
    text_output: Path | None = None,
) -> None:
    artifact_dir = Path(report["package_artifact_dir"])
    artifact_dir.mkdir(parents=True, exist_ok=True)

    json_output = json_output or artifact_dir / f"{SCHEMA_VERSION}.json"
    text_output = text_output or artifact_dir / f"{SCHEMA_VERSION}.txt"
    json_output.parent.mkdir(parents=True, exist_ok=True)
    text_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    text_output.write_text(render_text_report(report), encoding="utf-8")


def section_status(section_payload: dict[str, Any]) -> str:
    status = str(
        section_payload.get("status")
        or section_payload.get("run_root_status")
        or section_payload.get("scope_status")
        or section_payload.get("interpretation_status")
        or ""
    ).strip()
    return status or "blocked_missing_inputs"


def classify_evidence_type(section_payload: dict[str, Any], source_paths: list[str]) -> str:
    status = section_status(section_payload)
    if status.startswith("blocked") or status == "missing":
        return "blocked"
    if section_payload.get("evidence_type") in {"measured", "fixture_backed"}:
        return str(section_payload["evidence_type"])
    if any(bundle.is_fixture_path(path) for path in source_paths):
        return "fixture_backed"
    return "measured"


def derive_package_status(section_provenance_profile: list[dict[str, Any]]) -> str:
    evidence_types = {str(section.get("evidence_type") or "blocked") for section in section_provenance_profile}
    if "blocked" in evidence_types:
        return "blocked_missing_inputs"
    if "measured" in evidence_types and "fixture_backed" in evidence_types:
        return "mixed_provenance"
    if evidence_types == {"fixture_backed"}:
        return "fixture_backed"
    return "measured"


def summarize_package(
    package_status: str,
    runtime_section: dict[str, Any],
    replay_section: dict[str, Any],
    uncertainty_section: dict[str, Any],
    claim_boundary_section: dict[str, Any],
    scaling_section: dict[str, Any],
    next_decision_section: dict[str, Any],
) -> str:
    if package_status == "blocked_missing_inputs":
        return "Balfrin management package is blocked because one or more required sections are missing."
    replay_status = str(replay_section.get("run_root_provenance") or "unknown")
    scaling_implication = str(scaling_section.get("scaling_implication") or "Scaling stays bounded by the single-job path.")
    next_step = str(next_decision_section.get("recommended_next_authorized_step") or "management review of this package")
    if package_status == "mixed_provenance":
        return (
            f"Runtime, restartability, GIS scope, uncertainty, and claim boundaries are measured; replay is fixture-backed so the package stays reproducible without collapsing provenance. {scaling_implication} The next authorized step is {next_step}."
        )
    if package_status == "fixture_backed":
        return (
            f"All package sections are fixture-backed, so the manifest is replayable but does not represent live measured evidence. {scaling_implication} The next authorized step is {next_step}."
        )
    return (
        f"Runtime, replay, restartability, GIS scope, uncertainty, and claim boundaries are explicit; replay provenance is {replay_status} and operational, annual-frequency, physical-probability, scale-up, and distributed-execution claims remain false. {scaling_implication} The next authorized step is {next_step}."
    )


def section_provenance_counts(profile: list[dict[str, Any]]) -> dict[str, int]:
    counts = {"measured": 0, "fixture_backed": 0, "blocked_missing_inputs": 0}
    for section in profile:
        evidence_type = str(section.get("evidence_type") or "blocked")
        if evidence_type == "measured":
            counts["measured"] += 1
        elif evidence_type == "fixture_backed":
            counts["fixture_backed"] += 1
        else:
            counts["blocked_missing_inputs"] += 1
    return counts


def build_section_source_paths(section_payload: dict[str, Any]) -> list[str]:
    paths = section_payload.get("source_paths")
    if isinstance(paths, list):
        return [str(item) for item in paths if isinstance(item, str) and item]
    if isinstance(paths, dict):
        collected: list[str] = []
        for value in paths.values():
            if isinstance(value, str) and value:
                collected.append(value)
            elif isinstance(value, list):
                collected.extend(str(item) for item in value if isinstance(item, str) and item)
        return collected
    if isinstance(paths, str) and paths:
        return [paths]
    return []


def build_runtime_source_paths(bundle_report: dict[str, Any]) -> list[str]:
    source_paths = dict(bundle_report.get("source_paths") or {})
    record_paths = source_paths.get("single_job_record_paths")
    if isinstance(record_paths, dict):
        return [str(value) for value in record_paths.values() if isinstance(value, str) and value]
    return []


def build_gis_source_paths(bundle_report: dict[str, Any]) -> list[str]:
    source_paths = dict(bundle_report.get("source_paths") or {})
    artifact_roots = source_paths.get("gis_artifact_roots")
    if isinstance(artifact_roots, list):
        return [str(value) for value in artifact_roots if isinstance(value, str) and value]
    return []


def build_uncertainty_source_paths(bundle_report: dict[str, Any], smoke_report: dict[str, Any]) -> list[str]:
    paths = []
    source_paths = dict(bundle_report.get("source_paths") or {})
    contract_path = source_paths.get("post_run_contract_path")
    if isinstance(contract_path, str) and contract_path:
        paths.append(contract_path)
    smoke_root = smoke_report.get("run_root")
    if isinstance(smoke_root, str) and smoke_root:
        paths.append(smoke_root)
    return paths


def evidence_sources(source_artifacts: dict[str, Any]) -> list[str]:
    sources = [
        "scripts/summarize_balfrin_evidence_bundle.py",
        "scripts/summarize_balfrin_demonstration_replay_smoke.py",
        "scripts/summarize_balfrin_post_run_interpretation_gate.py",
        "scripts/summarize_balfrin_single_job_execution.py",
        "scripts/audit_gis_cog_package_readiness.py",
        "docs/balfrin_single_job_execution_sufficiency.md",
    ]
    if source_artifacts:
        sources.append(str(source_artifacts.get("package_artifact_dir") or DEFAULT_ARTIFACT_DIR))
    return sources


def as_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    return {}


def listify(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


if __name__ == "__main__":
    raise SystemExit(main())
