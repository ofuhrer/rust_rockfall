#!/usr/bin/env python3
"""Summarize Balfrin restartability recovery from a partial-state fixture.

This helper is read-only. It classifies a restartability recovery snapshot as
measured, fixture-proven, or blocked_missing_inputs and keeps the recovery
limits explicit so the report does not overstate what the evidence proves.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "balfrin_restartability_recovery_v1"
LARGEST_RUN_RECOVERY_SCHEMA_VERSION = "balfrin_largest_hazard_run_recovery_v1"
DEFAULT_EVIDENCE_JSON = ROOT / "tests/fixtures/balfrin_restartability_recovery/fixture_v1.json"
LARGEST_RUN_MANDATORY_ARTIFACTS = (
    "tb682_profile.json",
    "tb682_profile.md",
    "tb682_time.txt",
    "tb682_pressure.sbatch",
    "tb682_du_bytes.txt",
    "tb682_files.txt",
    "profile/input/multi_zone_hazard_profile_fixture_manifest.json",
    "profile/output/explicit/hazard/multi_zone_hazard_profile_manifest.json",
    "profile/output/explicit/hazard/multi_zone_hazard_profile_execution_plan_v1.json",
    "profile/output/explicit/hazard/multi_zone_hazard_profile_reducer_execution_index_v1.json",
    "profile/output/explicit/hazard/multi_zone_hazard_profile_reducer_merge_state_v1.json",
)


class BalfrinRestartabilityRecoveryError(ValueError):
    """User-facing recovery-summary error."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("json", "text"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    parser.add_argument("--text-output", type=Path, default=None)
    parser.add_argument(
        "--evidence-json",
        type=Path,
        default=None,
        help="optional override JSON file for tests or alternate recovery snapshots",
    )
    parser.add_argument("--source-run-root", type=Path, default=None)
    parser.add_argument("--recovered-run-root", type=Path, default=None)
    parser.add_argument("--job-id", default=None)
    parser.add_argument("--release-zones", type=int, default=None)
    parser.add_argument(
        "--run-id",
        default=None,
        help="optional run id override for source/recovered run-root summaries",
    )
    args = parser.parse_args(argv)

    try:
        if args.source_run_root is not None or args.recovered_run_root is not None:
            report = build_largest_hazard_run_recovery_report(
                source_run_root=args.source_run_root,
                recovered_run_root=args.recovered_run_root,
                job_id=args.job_id,
                release_zones=args.release_zones,
                run_id=args.run_id,
            )
        else:
            report = build_report(load_evidence_override(args.evidence_json))
    except BalfrinRestartabilityRecoveryError as exc:
        print(f"balfrin restartability recovery error: {exc}", file=sys.stderr)
        return 2

    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.text_output is not None:
        args.text_output.parent.mkdir(parents=True, exist_ok=True)
        args.text_output.write_text(render_report(report), encoding="utf-8")

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_report(report))
    return 0 if report["recovery_status"] != "blocked_missing_inputs" else 2


def load_evidence_override(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    if not path.exists():
        raise BalfrinRestartabilityRecoveryError(f"evidence override file is missing: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise BalfrinRestartabilityRecoveryError("evidence override must be a JSON object")
    return data


def build_report(evidence_override: dict[str, Any] | None = None) -> dict[str, Any]:
    if evidence_override is None:
        return build_report(load_json(DEFAULT_EVIDENCE_JSON))
    if evidence_override.get("missing_inputs"):
        missing_inputs = [str(item) for item in evidence_override.get("missing_inputs", [])]
        return blocked_report(missing_inputs, reason="required recovery evidence inputs are missing")
    if isinstance(evidence_override.get("recovery_report"), dict):
        return dict(evidence_override["recovery_report"])

    required_keys = ("partial_state", "resume_commands", "recovery_outcome", "artifact_hygiene")
    missing_inputs = [key for key in required_keys if key not in evidence_override]
    if missing_inputs:
        return blocked_report(missing_inputs, reason="required recovery evidence sections are missing")

    evidence_type = str(evidence_override.get("evidence_type") or "").strip().lower()
    if evidence_type == "measured":
        recovery_status = "measured"
    elif evidence_type == "fixture":
        recovery_status = "fixture_proven"
    else:
        recovery_status = "blocked_missing_inputs"

    partial_state = as_mapping(evidence_override.get("partial_state"))
    recovery_outcome = as_mapping(evidence_override.get("recovery_outcome"))
    artifact_hygiene = as_mapping(evidence_override.get("artifact_hygiene"))
    resume_commands = list_of_strings(evidence_override.get("resume_commands"))
    if not resume_commands:
        return blocked_report(["resume_commands"], reason="recovery evidence is missing resume commands")

    reused_chunks = list_of_strings(recovery_outcome.get("reused_chunks"))
    executed_chunks = list_of_strings(recovery_outcome.get("executed_chunks"))
    numerical_artifacts = as_mapping(recovery_outcome.get("numerical_artifact_stability"))
    if recovery_status == "blocked_missing_inputs":
        return blocked_report(["evidence_type"], reason="recovery evidence type is not classified")

    source_json_path = evidence_override.get("source_path")
    if isinstance(source_json_path, str) and source_json_path.strip():
        source_json_value = source_json_path.strip()
    else:
        source_json_value = str(DEFAULT_EVIDENCE_JSON)

    report = {
        "schema_version": SCHEMA_VERSION,
        "pilot_id": str(evidence_override.get("pilot_id") or "tschamut_public_pilot"),
        "run_id": str(evidence_override.get("run_id") or "tschamut_public_balfrin_restartability_recovery_v1"),
        "recovery_status": recovery_status,
        "evidence_status": evidence_type or "unknown",
        "partial_state": partial_state,
        "resume_commands": resume_commands,
        "recovery_timing": as_mapping(evidence_override.get("recovery_timing")),
        "reused_chunks": reused_chunks,
        "executed_chunks": executed_chunks,
        "reused_chunk_counts": as_mapping(recovery_outcome.get("reused_chunk_counts")),
        "executed_chunk_counts": as_mapping(recovery_outcome.get("executed_chunk_counts")),
        "artifact_continuity": as_mapping(evidence_override.get("artifact_continuity")),
        "numerical_artifact_stability": {
            "classification": str(numerical_artifacts.get("classification") or "unknown"),
            "changed_artifact_count": safe_int(numerical_artifacts.get("changed_artifact_count")),
            "changed_paths": list_of_strings(numerical_artifacts.get("changed_paths")),
            "baseline_file_count": safe_int(numerical_artifacts.get("baseline_file_count")),
            "recovered_file_count": safe_int(numerical_artifacts.get("recovered_file_count")),
            "stable_artifact_count": safe_int(numerical_artifacts.get("stable_artifact_count")),
        },
        "artifact_hygiene": {
            "classification": str(artifact_hygiene.get("classification") or "unknown"),
            "generated_roots": list_of_strings(artifact_hygiene.get("generated_roots")),
            "placeholder_roots_avoided": list_of_strings(artifact_hygiene.get("placeholder_roots_avoided")),
        },
        "explicit_limits": list_of_strings(evidence_override.get("explicit_limits")),
        "source_paths": {
            "evidence_json": source_json_value,
            "fixture": str(DEFAULT_EVIDENCE_JSON),
        },
    }
    report["rerun_fraction_summary"] = build_rerun_fraction_summary(
        reused_chunk_counts=report["reused_chunk_counts"],
        executed_chunk_counts=report["executed_chunk_counts"],
    )
    report["recovery_elapsed_summary"] = build_recovery_elapsed_summary(report["recovery_timing"])
    report["preserved_artifact_summary"] = build_preserved_artifact_summary(report)
    if not report["explicit_limits"]:
        if recovery_status == "measured":
            report["explicit_limits"] = [
                "live interrupted/resumed recovery evidence only; no fixture-backed proof is claimed here.",
                "no distributed execution authorization is implied.",
                "no physics, sampling, or output-profile changes are introduced by this report.",
            ]
        else:
            report["explicit_limits"] = [
                "fixture-backed recovery evidence only; no live interruption is claimed here.",
                "no distributed execution authorization is implied.",
                "no physics, sampling, or output-profile changes are introduced by this report.",
            ]
    return report


def build_largest_hazard_run_recovery_report(
    *,
    source_run_root: Path | None,
    recovered_run_root: Path | None,
    job_id: str | None,
    release_zones: int | None,
    run_id: str | None = None,
) -> dict[str, Any]:
    missing_inputs: list[str] = []
    if source_run_root is None:
        missing_inputs.append("source_run_root")
    if recovered_run_root is None:
        missing_inputs.append("recovered_run_root")
    if not job_id:
        missing_inputs.append("job_id")
    if release_zones is None:
        missing_inputs.append("release_zones")
    if missing_inputs:
        return blocked_largest_run_report(missing_inputs, reason="required run-root recovery arguments are missing")

    assert source_run_root is not None
    assert recovered_run_root is not None
    assert job_id is not None
    assert release_zones is not None
    source_run_root = source_run_root.resolve()
    recovered_run_root = recovered_run_root.resolve()
    if not source_run_root.is_dir():
        return blocked_largest_run_report([str(source_run_root)], reason="source run root is missing")
    if not recovered_run_root.is_dir():
        return blocked_largest_run_report([str(recovered_run_root)], reason="recovered run root is missing")

    mandatory_artifacts = [
        *LARGEST_RUN_MANDATORY_ARTIFACTS,
        f"slurm-{job_id}.out",
        f"slurm-{job_id}.err",
    ]
    missing_mandatory = [rel for rel in mandatory_artifacts if not (recovered_run_root / rel).exists()]
    source_manifest = build_payload_manifest(source_run_root)
    recovered_manifest = build_payload_manifest(recovered_run_root)
    manifest_comparison = compare_payload_manifests(source_manifest, recovered_manifest)
    profile_report = load_largest_run_profile(recovered_run_root / "tb682_profile.json")
    metrics_ready = not profile_report.get("missing_profile_fields")
    mandatory_ready = not missing_mandatory
    manifest_ready = manifest_comparison["checksum_match"]
    replay_critical_sufficient = bool(mandatory_ready and manifest_ready and metrics_ready)

    return {
        "schema_version": LARGEST_RUN_RECOVERY_SCHEMA_VERSION,
        "pilot_id": "tschamut_public_pilot",
        "run_id": run_id or "tb684_tb682_384_zone_hazard_run_recovery",
        "recovery_status": "measured" if replay_critical_sufficient else "blocked_missing_inputs",
        "evidence_status": "measured_copied_run_root",
        "job_id": str(job_id),
        "release_zones": release_zones,
        "source_run_root": str(source_run_root),
        "recovered_run_root": str(recovered_run_root),
        "copy_recovery": {
            "status": "measured" if recovered_run_root.is_dir() else "blocked_missing_inputs",
            "source_file_count": len(source_manifest),
            "recovered_payload_file_count": len(recovered_manifest),
            "source_payload_bytes": sum(item["size_bytes"] for item in source_manifest.values()),
            "recovered_payload_bytes": sum(item["size_bytes"] for item in recovered_manifest.values()),
        },
        "mandatory_artifacts": {
            "status": "complete" if mandatory_ready else "missing",
            "checked": mandatory_artifacts,
            "missing": missing_mandatory,
        },
        "manifest_comparison": manifest_comparison,
        "regenerated_metrics": profile_report,
        "replay_critical_artifacts": {
            "sufficient_for_copy_inspection_and_metric_regeneration": replay_critical_sufficient,
            "classification": "sufficient" if replay_critical_sufficient else "blocked_missing_inputs",
            "first_blocker": first_largest_run_blocker(missing_mandatory, manifest_comparison, profile_report),
        },
        "support_limit": {
            "classification": "output_budget_blocked",
            "statement": (
                "The recovered 384-zone run root is complete enough for checksum replay, inspection, "
                "and metric regeneration, but it remains blocked as a replay-ready scale support point "
                "under the current output-byte and manifest-byte budgets."
            ),
        },
        "artifact_hygiene": {
            "classification": "pass_clean",
            "generated_roots": [str(recovered_run_root)],
            "placeholder_roots_avoided": [
                "data/processed/swisstopo/placeholder_second_site_v1",
                "validation/private/placeholder_second_site_v1",
                "hazard/results/placeholder_second_site_v1",
            ],
        },
        "explicit_limits": [
            "Copied-root recovery and replay inspection only; no scheduler job was submitted for this task.",
            "No simulation rerun, scale-up authorization, distributed execution, non-postproc execution, physical-probability, annual-frequency, operational, risk, exposure, or vulnerability claim is introduced.",
            "The 384-zone run remains output-budget-blocked as a replay-ready scale support point even though its preserved artifacts are sufficient for recovery inspection.",
        ],
    }


def build_rerun_fraction_summary(
    *,
    reused_chunk_counts: dict[str, Any],
    executed_chunk_counts: dict[str, Any],
) -> dict[str, Any]:
    families = sorted(set(reused_chunk_counts) | set(executed_chunk_counts))
    by_family: dict[str, dict[str, Any]] = {}
    total_reused = 0
    total_executed = 0
    for family in families:
        reused = safe_int(reused_chunk_counts.get(family)) or 0
        executed = safe_int(executed_chunk_counts.get(family)) or 0
        total = reused + executed
        total_reused += reused
        total_executed += executed
        by_family[family] = {
            "reused_chunks": reused,
            "executed_chunks": executed,
            "total_chunks": total,
            "rerun_fraction": round(executed / total, 6) if total else None,
            "reuse_fraction": round(reused / total, 6) if total else None,
        }
    total_chunks = total_reused + total_executed
    return {
        "status": "measured" if total_chunks else "blocked_missing_chunk_counts",
        "reused_chunks": total_reused,
        "executed_chunks": total_executed,
        "total_chunks": total_chunks,
        "rerun_fraction": round(total_executed / total_chunks, 6) if total_chunks else None,
        "reuse_fraction": round(total_reused / total_chunks, 6) if total_chunks else None,
        "by_family": by_family,
    }


def build_recovery_elapsed_summary(recovery_timing: dict[str, Any]) -> dict[str, Any]:
    elapsed_fields = {
        key: parse_slurm_elapsed(value)
        for key, value in recovery_timing.items()
        if key.endswith("_elapsed")
    }
    measured = {key: value for key, value in elapsed_fields.items() if value is not None}
    return {
        "status": "measured" if measured else "blocked_missing_elapsed_fields",
        "elapsed_seconds_by_field": measured,
        "total_elapsed_seconds": sum(measured.values()) if measured else None,
    }


def parse_slurm_elapsed(value: Any) -> int | None:
    text = str(value or "").strip()
    if not text:
        return None
    day_count = 0
    if "-" in text:
        day_text, text = text.split("-", 1)
        try:
            day_count = int(day_text)
        except ValueError:
            return None
    parts = text.split(":")
    try:
        if len(parts) == 3:
            hours, minutes, seconds = (int(part) for part in parts)
        elif len(parts) == 2:
            hours = 0
            minutes, seconds = (int(part) for part in parts)
        else:
            return None
    except ValueError:
        return None
    return day_count * 86400 + hours * 3600 + minutes * 60 + seconds


def build_preserved_artifact_summary(report: dict[str, Any]) -> dict[str, Any]:
    numerical_artifacts = as_mapping(report.get("numerical_artifact_stability"))
    artifact_continuity = as_mapping(report.get("artifact_continuity"))
    artifact_hygiene = as_mapping(report.get("artifact_hygiene"))
    stable_artifact_count = safe_int(numerical_artifacts.get("stable_artifact_count"))
    baseline_file_count = safe_int(numerical_artifacts.get("baseline_file_count"))
    recovered_file_count = safe_int(numerical_artifacts.get("recovered_file_count"))
    if stable_artifact_count is None and baseline_file_count is not None and safe_int(numerical_artifacts.get("changed_artifact_count")) == 0:
        stable_artifact_count = baseline_file_count
    return {
        "status": "measured" if artifact_continuity or stable_artifact_count is not None else "partial",
        "stable_artifact_count": stable_artifact_count,
        "baseline_file_count": baseline_file_count,
        "recovered_file_count": recovered_file_count,
        "changed_artifact_count": safe_int(numerical_artifacts.get("changed_artifact_count")),
        "continuity_fields": sorted(artifact_continuity),
        "generated_roots": list_of_strings(artifact_hygiene.get("generated_roots")),
    }


def build_payload_manifest(root: Path) -> dict[str, dict[str, Any]]:
    manifest: dict[str, dict[str, Any]] = {}
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root).as_posix()
        if Path(relative).name.startswith("tb684_"):
            continue
        manifest[relative] = {
            "size_bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
    return manifest


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def compare_payload_manifests(
    source_manifest: dict[str, dict[str, Any]],
    recovered_manifest: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    source_paths = set(source_manifest)
    recovered_paths = set(recovered_manifest)
    missing = sorted(source_paths - recovered_paths)
    extra = sorted(recovered_paths - source_paths)
    mismatched = sorted(
        path
        for path in source_paths & recovered_paths
        if source_manifest[path]["sha256"] != recovered_manifest[path]["sha256"]
        or source_manifest[path]["size_bytes"] != recovered_manifest[path]["size_bytes"]
    )
    return {
        "status": "match" if not missing and not extra and not mismatched else "mismatch",
        "checksum_match": not missing and not extra and not mismatched,
        "missing_paths": missing,
        "extra_paths": extra,
        "mismatched_paths": mismatched,
    }


def load_largest_run_profile(profile_path: Path) -> dict[str, Any]:
    if not profile_path.exists():
        return {
            "status": "blocked_missing_inputs",
            "profile_path": str(profile_path),
            "missing_profile_fields": ["tb682_profile.json"],
        }
    profile = load_json(profile_path)
    fixture = as_mapping(profile.get("fixture"))
    profile_scale = as_mapping(profile.get("profile_scale"))
    larger_profile = as_mapping(profile.get("larger_than_four_zone_package_profile"))
    local_pre_submit = as_mapping(larger_profile.get("local_pre_submit_proof"))
    missing_fields = [
        name
        for name, value in {
            "fixture.release_zone_count": fixture.get("release_zone_count"),
            "fixture.trajectory_file_count": fixture.get("trajectory_file_count"),
            "fixture.impact_file_count": fixture.get("impact_file_count"),
            "profile_scale.output_file_count": profile_scale.get("output_file_count"),
            "profile_scale.output_bytes": profile_scale.get("output_bytes"),
            "profile_scale.hazard_layer_seconds": profile_scale.get("hazard_layer_seconds"),
            "profile_scale.total_wall_seconds": profile_scale.get("total_wall_seconds"),
            "larger_than_four_zone_package_profile.local_pre_submit_proof.replay_critical_coverage": local_pre_submit.get(
                "replay_critical_coverage"
            ),
        }.items()
        if value is None
    ]
    replay_critical_coverage = as_mapping(local_pre_submit.get("replay_critical_coverage"))
    return {
        "status": "measured_reconstructed_from_preserved_files" if not missing_fields else "blocked_missing_inputs",
        "profile_path": str(profile_path),
        "profile_id": str(profile.get("profile_id") or ""),
        "release_zone_count": safe_int(fixture.get("release_zone_count")),
        "trajectory_file_count": safe_int(fixture.get("trajectory_file_count")),
        "impact_file_count": safe_int(fixture.get("impact_file_count")),
        "output_file_count": safe_int(profile_scale.get("output_file_count")),
        "output_bytes": safe_int(profile_scale.get("output_bytes")),
        "hazard_layer_seconds": safe_float(profile_scale.get("hazard_layer_seconds")),
        "total_wall_seconds": safe_float(profile_scale.get("total_wall_seconds")),
        "manifest_size_bytes": safe_int(local_pre_submit.get("manifest_size_bytes")),
        "replay_critical_coverage_complete": replay_critical_coverage.get("complete"),
        "output_budget_first_blocker": local_pre_submit.get("first_blocker"),
        "output_budget_blockers": list_of_strings(local_pre_submit.get("blockers")),
        "missing_profile_fields": missing_fields,
    }


def first_largest_run_blocker(
    missing_mandatory: list[str],
    manifest_comparison: dict[str, Any],
    profile_report: dict[str, Any],
) -> str | None:
    if missing_mandatory:
        return f"missing mandatory artifact: {missing_mandatory[0]}"
    if not manifest_comparison.get("checksum_match"):
        for field in ("missing_paths", "mismatched_paths", "extra_paths"):
            paths = list_of_strings(manifest_comparison.get(field))
            if paths:
                return f"manifest {field}: {paths[0]}"
        return "manifest mismatch"
    missing_profile_fields = list_of_strings(profile_report.get("missing_profile_fields"))
    if missing_profile_fields:
        return f"missing profile field: {missing_profile_fields[0]}"
    return None


def blocked_largest_run_report(missing_inputs: list[str], *, reason: str) -> dict[str, Any]:
    return {
        "schema_version": LARGEST_RUN_RECOVERY_SCHEMA_VERSION,
        "pilot_id": "tschamut_public_pilot",
        "run_id": "tb684_tb682_384_zone_hazard_run_recovery",
        "recovery_status": "blocked_missing_inputs",
        "evidence_status": "blocked_missing_inputs",
        "job_id": None,
        "release_zones": None,
        "source_run_root": None,
        "recovered_run_root": None,
        "copy_recovery": {},
        "mandatory_artifacts": {"status": "blocked_missing_inputs", "checked": [], "missing": []},
        "manifest_comparison": {"status": "blocked_missing_inputs", "checksum_match": False},
        "regenerated_metrics": {"status": "blocked_missing_inputs", "missing_profile_fields": []},
        "replay_critical_artifacts": {
            "sufficient_for_copy_inspection_and_metric_regeneration": False,
            "classification": "blocked_missing_inputs",
            "first_blocker": missing_inputs[0] if missing_inputs else reason,
        },
        "support_limit": {"classification": "blocked_missing_inputs", "statement": reason},
        "artifact_hygiene": {
            "classification": "blocked_missing_inputs",
            "generated_roots": [],
            "placeholder_roots_avoided": [],
        },
        "explicit_limits": [reason, *missing_inputs],
    }


def blocked_report(missing_inputs: list[str], *, reason: str) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "pilot_id": "tschamut_public_pilot",
        "run_id": "tschamut_public_balfrin_restartability_recovery_v1",
        "recovery_status": "blocked_missing_inputs",
        "evidence_status": "blocked_missing_inputs",
        "partial_state": {},
        "resume_commands": [],
        "recovery_timing": {},
        "reused_chunks": [],
        "executed_chunks": [],
        "reused_chunk_counts": {},
        "executed_chunk_counts": {},
        "artifact_continuity": {},
        "numerical_artifact_stability": {
            "classification": "blocked_missing_inputs",
            "changed_artifact_count": None,
            "changed_paths": [],
        },
        "artifact_hygiene": {
            "classification": "blocked_missing_inputs",
            "generated_roots": [],
            "placeholder_roots_avoided": [],
        },
        "explicit_limits": [reason, *missing_inputs],
        "source_paths": {
            "evidence_json": None,
            "fixture": str(DEFAULT_EVIDENCE_JSON),
        },
    }


def render_report(report: dict[str, Any]) -> str:
    if report.get("schema_version") == LARGEST_RUN_RECOVERY_SCHEMA_VERSION:
        return render_largest_hazard_run_recovery_report(report)
    return render_text_report(report)


def render_largest_hazard_run_recovery_report(report: dict[str, Any]) -> str:
    copy_recovery = as_mapping(report.get("copy_recovery"))
    mandatory = as_mapping(report.get("mandatory_artifacts"))
    manifest = as_mapping(report.get("manifest_comparison"))
    metrics = as_mapping(report.get("regenerated_metrics"))
    replay = as_mapping(report.get("replay_critical_artifacts"))
    support_limit = as_mapping(report.get("support_limit"))
    artifact_hygiene = as_mapping(report.get("artifact_hygiene"))
    lines = [
        "# Balfrin Largest Hazard Run Recovery Report",
        "",
        f"- Schema: `{report['schema_version']}`",
        f"- Recovery status: `{report['recovery_status']}`",
        f"- Evidence status: `{report['evidence_status']}`",
        f"- Job id: `{report.get('job_id')}`",
        f"- Release zones: `{report.get('release_zones')}`",
        f"- Source run root: `{report.get('source_run_root')}`",
        f"- Recovered run root: `{report.get('recovered_run_root')}`",
        "",
        "## Copy And Manifest",
        "",
        f"- Source payload files: `{copy_recovery.get('source_file_count')}`",
        f"- Recovered payload files: `{copy_recovery.get('recovered_payload_file_count')}`",
        f"- Source payload bytes: `{copy_recovery.get('source_payload_bytes')}`",
        f"- Recovered payload bytes: `{copy_recovery.get('recovered_payload_bytes')}`",
        f"- Payload checksum match: `{manifest.get('checksum_match')}`",
        f"- Missing payload paths: `{manifest.get('missing_paths')}`",
        f"- Extra payload paths: `{manifest.get('extra_paths')}`",
        f"- Mismatched payload paths: `{manifest.get('mismatched_paths')}`",
        "",
        "## Mandatory Artifacts",
        "",
        f"- Status: `{mandatory.get('status')}`",
        f"- Missing: `{mandatory.get('missing')}`",
        "",
        "## Regenerated Metrics",
        "",
        f"- Status: `{metrics.get('status')}`",
        f"- Profile id: `{metrics.get('profile_id')}`",
        f"- Release zones: `{metrics.get('release_zone_count')}`",
        f"- Trajectory files: `{metrics.get('trajectory_file_count')}`",
        f"- Impact-event files: `{metrics.get('impact_file_count')}`",
        f"- Output files: `{metrics.get('output_file_count')}`",
        f"- Output bytes: `{metrics.get('output_bytes')}`",
        f"- Manifest bytes: `{metrics.get('manifest_size_bytes')}`",
        f"- Hazard-layer seconds: `{metrics.get('hazard_layer_seconds')}`",
        f"- Total profile wall seconds: `{metrics.get('total_wall_seconds')}`",
        f"- Replay-critical coverage complete: `{metrics.get('replay_critical_coverage_complete')}`",
        "",
        "## Replay-Critical Sufficiency",
        "",
        f"- Classification: `{replay.get('classification')}`",
        f"- Sufficient for copy inspection and metric regeneration: `{replay.get('sufficient_for_copy_inspection_and_metric_regeneration')}`",
        f"- First blocker: `{replay.get('first_blocker')}`",
        f"- Support-limit classification: `{support_limit.get('classification')}`",
        f"- Support-limit statement: {support_limit.get('statement')}",
        "",
        "## Artifact Hygiene",
        "",
        f"- Classification: `{artifact_hygiene.get('classification')}`",
        f"- Generated roots: `{artifact_hygiene.get('generated_roots')}`",
        f"- Placeholder roots avoided: `{artifact_hygiene.get('placeholder_roots_avoided')}`",
        "",
        "## Explicit Limits",
        "",
    ]
    for limit in report.get("explicit_limits") or []:
        lines.append(f"- {limit}")
    return "\n".join(lines)


def render_text_report(report: dict[str, Any]) -> str:
    lines = [
        "# Balfrin Restartability Recovery Report",
        "",
        f"- Schema: `{report['schema_version']}`",
        f"- Recovery status: `{report['recovery_status']}`",
        f"- Evidence status: `{report['evidence_status']}`",
        f"- Pilot id: `{report['pilot_id']}`",
        f"- Run id: `{report['run_id']}`",
        "",
        "## Partial State",
        "",
        f"- Partial state: `{json.dumps(report['partial_state'], sort_keys=True)}`",
        "",
        "## Resume Commands",
        "",
    ]
    for command in report["resume_commands"]:
        lines.append(f"```bash\n{command}\n```")
    recovery_timing = report.get("recovery_timing") or {}
    if recovery_timing:
        lines.extend(
            [
                "",
                "## Recovery Timing",
                "",
            ]
        )
        for key, value in recovery_timing.items():
            lines.append(f"- {key}: `{value}`")
    artifact_continuity = report.get("artifact_continuity") or {}
    if artifact_continuity:
        lines.extend(
            [
                "",
                "## Artifact Continuity",
                "",
            ]
        )
        for key, value in artifact_continuity.items():
            if isinstance(value, dict):
                lines.append(f"- {key}: `{json.dumps(value, sort_keys=True)}`")
            else:
                lines.append(f"- {key}: `{value}`")
    lines.extend(
        [
            "",
            "## Chunk Recovery",
            "",
            f"- Reused chunks: `{report['reused_chunks']}`",
            f"- Executed chunks: `{report['executed_chunks']}`",
            f"- Reused chunk counts: `{report['reused_chunk_counts']}`",
            f"- Executed chunk counts: `{report['executed_chunk_counts']}`",
            f"- Rerun fraction summary: `{json.dumps(report.get('rerun_fraction_summary') or {}, sort_keys=True)}`",
            f"- Recovery elapsed summary: `{json.dumps(report.get('recovery_elapsed_summary') or {}, sort_keys=True)}`",
            f"- Preserved artifact summary: `{json.dumps(report.get('preserved_artifact_summary') or {}, sort_keys=True)}`",
            "",
            "## Numerical Stability",
            "",
            f"- Classification: `{report['numerical_artifact_stability']['classification']}`",
            f"- Changed artifact count: `{report['numerical_artifact_stability']['changed_artifact_count']}`",
            f"- Changed paths: `{report['numerical_artifact_stability']['changed_paths']}`",
            "",
            "## Artifact Hygiene",
            "",
            f"- Classification: `{report['artifact_hygiene']['classification']}`",
            f"- Generated roots: `{report['artifact_hygiene']['generated_roots']}`",
            f"- Placeholder roots avoided: `{report['artifact_hygiene']['placeholder_roots_avoided']}`",
            "",
            "## Explicit Limits",
            "",
        ]
    )
    for limit in report["explicit_limits"]:
        lines.append(f"- {limit}")
    lines.extend(
        [
            "",
            "## Source Paths",
            "",
            f"- Evidence fixture: `{report['source_paths']['fixture']}`",
        ]
    )
    if report["source_paths"].get("evidence_json"):
        lines.append(f"- Evidence json: `{report['source_paths']['evidence_json']}`")
    return "\n".join(lines)


def safe_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def safe_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def list_of_strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def as_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    return {}


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise BalfrinRestartabilityRecoveryError(f"required recovery evidence fixture is missing: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise BalfrinRestartabilityRecoveryError(f"recovery evidence fixture must be a JSON object: {path}")
    return data


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
