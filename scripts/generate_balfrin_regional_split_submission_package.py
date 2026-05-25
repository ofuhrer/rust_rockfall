#!/usr/bin/env python3
"""Build a no-submit Balfrin regional split submission package.

The package composes the existing multi-release-zone handoff, the regional
split/merge contract materialized by the reducer-pressure probe, and the
smallest multi-zone authorization preflight into one inspectable record. It
does not run ``sbatch`` or submit a Balfrin job.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import generate_balfrin_multi_release_zone_demo_handoff as handoff  # noqa: E402
from scripts import preflight_balfrin_smallest_multi_zone_probe_authorization as preflight  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "balfrin_regional_split_submission_package_v1"
DEFAULT_ARTIFACT_DIR = Path("/tmp/rust_rockfall/balfrin_regional_split_submission_package_v1")
DEFAULT_PACKAGE_JSON = DEFAULT_ARTIFACT_DIR / f"{SCHEMA_VERSION}.json"
DEFAULT_PACKAGE_TXT = DEFAULT_ARTIFACT_DIR / f"{SCHEMA_VERSION}.txt"
REGIONAL_SPLIT_PLAN_RELATIVE = Path("input/regional_split_execution_plan.json")
REGIONAL_MERGE_MANIFEST_RELATIVE = Path("output/merged/regional_split_merge_manifest.json")
SCENARIO_BATCH_SMOKE_SCHEMA_VERSION = "balfrin_scenario_batch_smoke_package_v1"
DEFAULT_SCENARIO_BATCH_SMOKE_ARTIFACT_DIR = Path("/tmp/rust_rockfall/balfrin_scenario_batch_smoke_package_v1")
DEFAULT_SCENARIO_BATCH_SMOKE_JSON = DEFAULT_SCENARIO_BATCH_SMOKE_ARTIFACT_DIR / f"{SCENARIO_BATCH_SMOKE_SCHEMA_VERSION}.json"
DEFAULT_SCENARIO_BATCH_SMOKE_TXT = DEFAULT_SCENARIO_BATCH_SMOKE_ARTIFACT_DIR / f"{SCENARIO_BATCH_SMOKE_SCHEMA_VERSION}.txt"


class BalfrinRegionalSplitSubmissionPackageError(ValueError):
    """User-facing regional split submission-package error."""


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-dir", type=Path, default=DEFAULT_ARTIFACT_DIR)
    parser.add_argument("--handoff-artifact-dir", type=Path, default=None)
    parser.add_argument("--pressure-probe-root", type=Path, default=None)
    parser.add_argument(
        "--balfrin-access-preflight-json",
        type=Path,
        default=None,
        help="Optional JSON from check_balfrin_remote_access_preflight.py. If omitted, access fails closed as not checked.",
    )
    parser.add_argument("--format", choices=("json", "text"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    parser.add_argument("--text-output", type=Path, default=None)
    return parser.parse_args(argv)


def build_report(
    *,
    artifact_dir: Path = DEFAULT_ARTIFACT_DIR,
    handoff_artifact_dir: Path | None = None,
    pressure_probe_root: Path | None = None,
    balfrin_access_preflight: dict[str, Any] | None = None,
    balfrin_access_preflight_source: str = "not_supplied",
    handoff_report_override: dict[str, Any] | None = None,
) -> dict[str, Any]:
    artifact_dir = resolve_output_root(artifact_dir)
    if not is_allowed_output_root(artifact_dir):
        raise BalfrinRegionalSplitSubmissionPackageError(
            "artifact-dir must stay under /tmp, validation/private, or the reviewed Balfrin scratch root "
            f"{handoff.BALFRIN_REVIEWED_SCRATCH_OUTPUT_ROOT}: {artifact_dir}"
        )

    handoff_artifact_dir = resolve_output_root(handoff_artifact_dir or artifact_dir / "handoff")
    pressure_probe_root = resolve_output_root(pressure_probe_root or artifact_dir / "regional_split_probe")
    if not is_allowed_output_root(handoff_artifact_dir) or not is_allowed_output_root(pressure_probe_root):
        raise BalfrinRegionalSplitSubmissionPackageError(
            "handoff-artifact-dir and pressure-probe-root must stay under /tmp, validation/private, "
            f"or the reviewed Balfrin scratch root {handoff.BALFRIN_REVIEWED_SCRATCH_OUTPUT_ROOT}"
        )

    handoff_report = handoff_report_override or handoff.build_report(
        artifact_dir=handoff_artifact_dir,
        pressure_probe_root=pressure_probe_root,
    )
    handoff_report = ensure_compact_handoff_manifest_report(handoff_report)
    reviewed_package = Path(handoff_report["package_json_path"])
    authorization_record = handoff_artifact_dir / handoff.DEFAULT_AUTHORIZATION_RECORD_PATH.name
    access_report = dict(balfrin_access_preflight or preflight._missing_access_report())
    access_source = balfrin_access_preflight_source if balfrin_access_preflight is not None else "not_supplied_failed_closed"
    preflight_report = preflight.build_report(
        reviewed_handoff_package=reviewed_package,
        authorization_record=authorization_record,
        balfrin_access_preflight=access_report,
        balfrin_access_preflight_source=access_source,
    )

    regional_contract = build_regional_contract(pressure_probe_root)
    scratch_package_freshness = build_scratch_package_freshness(
        artifact_dir=artifact_dir,
        access_report=access_report,
        access_source=access_source,
    )
    remote_head_alignment = build_remote_head_alignment(
        access_report=access_report,
        access_source=access_source,
    )
    compact_manifest_freshness = build_compact_manifest_freshness(handoff_report)
    package_contract = build_package_contract_status(
        handoff_report=handoff_report,
        preflight_report=preflight_report,
        regional_contract=regional_contract,
        scratch_package_freshness=scratch_package_freshness,
        remote_head_alignment=remote_head_alignment,
        compact_manifest_freshness=compact_manifest_freshness,
    )
    output_budget = build_output_budget_summary(handoff_report, preflight_report)
    preservation_plan = build_preservation_plan(handoff_report, preflight_report, artifact_dir)
    exact_command = str(
        dict(preflight_report.get("submit_contract_requirement") or {}).get("command")
        or handoff_report.get("authorization_submit_command")
        or ""
    )
    writable_remote_roots = build_writable_remote_roots(preflight_report)
    submission_package_status = classify_submission_package_status(
        package_contract=package_contract,
        preflight_report=preflight_report,
        output_budget=output_budget,
        writable_remote_roots=writable_remote_roots,
        scratch_package_freshness=scratch_package_freshness,
        remote_head_alignment=remote_head_alignment,
        compact_manifest_freshness=compact_manifest_freshness,
    )
    blocking_gate = first_blocker(
        package_contract=package_contract,
        preflight_report=preflight_report,
        output_budget=output_budget,
        writable_remote_roots=writable_remote_roots,
        scratch_package_freshness=scratch_package_freshness,
        remote_head_alignment=remote_head_alignment,
        compact_manifest_freshness=compact_manifest_freshness,
    )
    generation_inputs = {
        "balfrin_remote_head": access_report.get("remote_head"),
        "balfrin_access_preflight_path": access_source,
        "balfrin_access_status": access_report.get("status"),
        "local_package_source_head": remote_head_alignment.get("local_head"),
        "artifact_dir": str(artifact_dir),
    }

    return {
        "schema_version": SCHEMA_VERSION,
        "task_id": "TB-459",
        "submission_package_status": submission_package_status,
        "ready_for_bounded_postproc_submission": submission_package_status == "ready_for_bounded_postproc_submission",
        "first_blocker": blocking_gate,
        "artifact_dir": str(artifact_dir),
        "package_json_path": str(artifact_dir / DEFAULT_PACKAGE_JSON.name),
        "package_text_path": str(artifact_dir / DEFAULT_PACKAGE_TXT.name),
        "reviewed_handoff_package_path": str(reviewed_package),
        "authorization_record_path": str(authorization_record),
        "generation_inputs": generation_inputs,
        "balfrin_access_preflight_path": access_source,
        "balfrin_remote_head": access_report.get("remote_head"),
        "remote_head_alignment": remote_head_alignment,
        "scratch_package_freshness": scratch_package_freshness,
        "compact_manifest_freshness": compact_manifest_freshness,
        "handoff_package_status": handoff_report.get("package_status"),
        "handoff_package_constraint_status": handoff_report.get("package_constraint_status"),
        "regional_split_merge_contract": regional_contract,
        "package_contract_status": package_contract,
        "authorization_preflight_status": preflight_report.get("preflight_status"),
        "authorization_preflight": {
            "schema_version": preflight_report.get("schema_version"),
            "preflight_status": preflight_report.get("preflight_status"),
            "handoff_status": preflight_report.get("handoff_status"),
            "ready_for_live_postproc_submission": preflight_report.get("ready_for_live_postproc_submission"),
            "ready_for_authorized_submission": preflight_report.get("ready_for_authorized_submission"),
            "authorization_granted_by_preflight": preflight_report.get("authorization_granted_by_preflight"),
            "live_submission_authorized": preflight_report.get("live_submission_authorized"),
            "blocked_reason": preflight_report.get("blocked_reason"),
            "first_blocker": preflight_report.get("first_blocker"),
            "balfrin_access_status": preflight_report.get("balfrin_access_status"),
            "balfrin_access_preflight_requirement": preflight_report.get("balfrin_access_preflight_requirement"),
            "gate_results": preflight_report.get("gate_results"),
        },
        "exact_bounded_postproc_command": exact_command,
        "command_contract": {
            "partition": dict(preflight_report.get("submit_contract_requirement") or {}).get("partition", "postproc"),
            "run_id": dict(preflight_report.get("submit_contract_requirement") or {}).get("run_id"),
            "probe_manifest_path": dict(preflight_report.get("submit_contract_requirement") or {}).get(
                "probe_manifest_path"
            ),
            "contains_authorized_submit_flag": "--authorized-submit" in exact_command,
            "contains_generate_only_flag": "--generate-only" in exact_command,
            "no_non_postproc_partition": "--partition postproc" in exact_command,
        },
        "writable_remote_roots": writable_remote_roots,
        "output_budget": output_budget,
        "preservation_plan": preservation_plan,
        "no_submit_semantics": {
            "status": "not_submitted",
            "sbatch_attempted": False,
            "submit_command_executed": False,
            "balfrin_job_submitted": False,
            "package_generation_only": True,
            "boundary_note": "Package generation records the exact later submit command but never executes sbatch.",
        },
        "generated_output_roots": [
            str(artifact_dir),
            str(handoff_artifact_dir),
            str(pressure_probe_root),
        ],
        "claim_boundaries": {
            "operational_claims_allowed": False,
            "annual_frequency_claims_allowed": False,
            "physical_probability_claims_allowed": False,
            "risk_exposure_vulnerability_claims_allowed": False,
            "scale_up_authorized": False,
            "distributed_execution_authorized": False,
            "live_submission_performed": False,
            "partition_scope": "postproc_only",
        },
    }


def build_regional_contract(pressure_probe_root: Path) -> dict[str, Any]:
    plan_path = pressure_probe_root / REGIONAL_SPLIT_PLAN_RELATIVE
    merge_path = pressure_probe_root / REGIONAL_MERGE_MANIFEST_RELATIVE
    plan_status = structured_json_status(plan_path, "regional split plan")
    merge_status = structured_json_status(merge_path, "regional merge manifest")
    plan = dict(plan_status.get("value") or {})
    merge = dict(merge_status.get("value") or {})
    blocked_reasons: list[str] = []
    if plan_status["status"] != "ready":
        blocked_reasons.append(plan_status["blocked_reason"])
    if merge_status["status"] != "ready":
        blocked_reasons.append(merge_status["blocked_reason"])
    if plan.get("schema_version") != "regional_split_execution_plan_v1":
        blocked_reasons.append("regional split plan schema is not regional_split_execution_plan_v1")
    if plan.get("status") != "ready":
        blocked_reasons.append(f"regional split plan status is {plan.get('status')}")
    if merge.get("schema_version") != "regional_split_merge_manifest_v1":
        blocked_reasons.append("regional merge manifest schema is not regional_split_merge_manifest_v1")
    merge_order = str(merge.get("merge_order") or "")
    merge_order_is_deterministic = merge.get("merge_order_deterministic") is True or merge_order.startswith(
        "sorted_"
    )
    if merge.get("merge_order_independent") is not True or not merge_order_is_deterministic:
        blocked_reasons.append("regional merge manifest does not prove deterministic order-independent merge")
    return {
        "status": "ready" if not blocked_reasons else "blocked_package_contract",
        "blocked_reasons": dedupe(blocked_reasons),
        "regional_split_plan_path": str(plan_path),
        "regional_merge_manifest_path": str(merge_path),
        "regional_split_plan_sha256": file_sha256(plan_path) if plan_path.exists() else None,
        "regional_merge_manifest_sha256": file_sha256(merge_path) if merge_path.exists() else None,
        "plan_schema_version": plan.get("schema_version"),
        "plan_status": plan.get("status"),
        "split_count": plan.get("split_count"),
        "execution_key_count": plan.get("execution_key_count"),
        "duplicate_execution_keys": list(plan.get("duplicate_execution_keys") or []),
        "merge_key_policy": plan.get("merge_key_policy"),
        "chunk_order": list(plan.get("chunk_order") or []),
        "merge_schema_version": merge.get("schema_version"),
        "merge_order": merge.get("merge_order"),
        "merge_order_independent": merge.get("merge_order_independent"),
        "merge_order_deterministic": merge_order_is_deterministic,
        "sample_support_summary": merge.get("sample_support_summary", {}),
    }


def build_package_contract_status(
    *,
    handoff_report: dict[str, Any],
    preflight_report: dict[str, Any],
    regional_contract: dict[str, Any],
    scratch_package_freshness: dict[str, Any],
    remote_head_alignment: dict[str, Any],
    compact_manifest_freshness: dict[str, Any],
) -> dict[str, Any]:
    blocked_reasons: list[str] = []
    if regional_contract["status"] != "ready":
        blocked_reasons.extend(regional_contract["blocked_reasons"])
    if scratch_package_freshness["status"] == "blocked_stale_scratch_package":
        blocked_reasons.append(scratch_package_freshness["blocked_reason"])
    if str(remote_head_alignment["status"]).startswith("blocked_"):
        blocked_reasons.append(remote_head_alignment["blocked_reason"])
    if compact_manifest_freshness["status"] != "ready_compact_manifest_current":
        blocked_reasons.append(compact_manifest_freshness["blocked_reason"])
    if handoff_report.get("package_status") == "blocked_missing_inputs":
        blocked_reasons.append("handoff package is blocked_missing_inputs")
    if handoff_report.get("submission_classification") != "blocked_pending_new_human_authorization":
        blocked_reasons.append("handoff package does not preserve pending-authorization classification")
    command_contract = dict(preflight_report.get("submit_contract_requirement") or {})
    if command_contract.get("status") != "ready":
        blocked_reasons.append(command_contract.get("blocked_reason") or "submit contract is not ready")
    command = str(command_contract.get("command") or handoff_report.get("authorization_submit_command") or "")
    if "--partition postproc" not in command:
        blocked_reasons.append("exact submit command is not scoped to the postproc partition")
    return {
        "status": "ready" if not blocked_reasons else "blocked_package_contract",
        "blocked_reasons": dedupe(blocked_reasons),
        "reviewed_handoff_package_status": preflight_report.get("reviewed_handoff_package_status"),
        "submit_contract_status": preflight_report.get("submit_contract_status"),
        "regional_contract_status": regional_contract.get("status"),
        "scratch_package_freshness_status": scratch_package_freshness.get("status"),
        "remote_head_alignment_status": remote_head_alignment.get("status"),
        "compact_manifest_freshness_status": compact_manifest_freshness.get("status"),
    }


def ensure_compact_handoff_manifest_report(handoff_report: dict[str, Any]) -> dict[str, Any]:
    manifest_pruning = dict(handoff_report.get("manifest_pruning") or {})
    active_projection = dict(manifest_pruning.get("active_handoff_output_budget_projection") or {})
    if manifest_pruning.get("mode") == "compact" and active_projection.get("projection_mode") == "compact":
        return handoff_report

    command_plan = dict(handoff_report.get("command_plan") or {})
    pressure_artifact_dir = Path(str(handoff_report.get("pressure_artifact_dir") or ""))
    if not command_plan or not str(pressure_artifact_dir):
        return handoff_report

    compact_projection = handoff.build_handoff_output_budget_projection(
        command_plan=command_plan,
        pressure_artifact_dir=pressure_artifact_dir,
        manifest_mode="compact",
    )
    baseline = dict(handoff_report.get("handoff_output_budget_projection") or {})
    delta = handoff.projection_budget_delta(baseline, compact_projection)
    compact_status = str(compact_projection.get("budget_recheck", {}).get("status") or "")
    replay_critical_contract = handoff.build_replay_critical_contract(
        command_plan=command_plan,
        projection=compact_projection,
    )
    new_manifest_pruning = {
        "status": compact_status or "blocked_replay_contract_ambiguity",
        "summary": (
            "regional split package refreshed the reviewed handoff with compact manifest mode: "
            f"{baseline.get('manifest_size_bytes')} -> {compact_projection.get('manifest_size_bytes')} manifest bytes, "
            f"{baseline.get('sidecar_file_count')} -> {compact_projection.get('sidecar_file_count')} sidecar files."
        ),
        "mode": "compact",
        "active_handoff_output_budget_projection": compact_projection,
        "before": handoff.summarize_projection_budget(baseline),
        "after": handoff.summarize_projection_budget(compact_projection),
        "delta": delta,
        "replay_critical_output_families": list(handoff.REPLAY_CRITICAL_OUTPUT_FAMILIES),
        "pruned_output_families": list(handoff.PRUNED_OUTPUT_FAMILIES),
        "retained_output_families": list(compact_projection.get("output_family_mix") or []),
        "replay_critical_contract": replay_critical_contract,
        "exact_blocking_fields": list(compact_projection.get("output_family_mix") or []),
        "projection_hashes": dict(compact_projection.get("projection_file_hashes") or {}),
        "blocked_reason": compact_projection.get("budget_recheck", {}).get("reason")
        if compact_status != "budget_passes_no_reduction_needed"
        else None,
    }
    updated = dict(handoff_report)
    updated["manifest_pruning"] = new_manifest_pruning
    updated["handoff_output_budget_projection"] = compact_projection
    updated["output_budget_acceptance_validation"] = compact_projection.get("budget_acceptance_validation", {})
    handoff.write_package_files(updated)
    return updated


def build_remote_head_alignment(
    *,
    access_report: dict[str, Any],
    access_source: str,
) -> dict[str, Any]:
    remote_head = access_report.get("remote_head")
    source_kind = "fixture" if access_source == "fixture" else "preflight_json"
    if access_source.startswith("not_supplied"):
        source_kind = "not_supplied"
    if access_report.get("status") != access_preflight_ready_status():
        return {
            "schema_version": "balfrin_remote_head_alignment_v1",
            "status": "not_checked_access_not_ready",
            "aligned": None,
            "remote_head": remote_head,
            "local_head": None,
            "access_preflight_path": access_source,
            "blocked_reason": "",
            "summary": "Remote-head alignment is checked only after the Balfrin access preflight is ready.",
        }
    if source_kind != "preflight_json":
        return {
            "schema_version": "balfrin_remote_head_alignment_v1",
            "status": "not_checked_fixture_or_missing_preflight",
            "aligned": None,
            "remote_head": remote_head,
            "local_head": None,
            "access_preflight_path": access_source,
            "blocked_reason": "",
            "summary": "Remote-head alignment is enforced for file-backed Balfrin access preflight inputs.",
        }
    local_head = local_git_head()
    if not remote_head or not local_head:
        return {
            "schema_version": "balfrin_remote_head_alignment_v1",
            "status": "blocked_remote_head_unknown",
            "aligned": False,
            "remote_head": remote_head,
            "local_head": local_head,
            "access_preflight_path": access_source,
            "blocked_reason": "remote or local git HEAD is unavailable for package/preflight alignment",
            "summary": "The package cannot prove source alignment with the Balfrin checkout.",
        }
    if remote_head != local_head:
        return {
            "schema_version": "balfrin_remote_head_alignment_v1",
            "status": "blocked_remote_head_mismatch",
            "aligned": False,
            "remote_head": remote_head,
            "local_head": local_head,
            "access_preflight_path": access_source,
            "blocked_reason": (
                "Balfrin remote HEAD from the access preflight does not match the local package source HEAD"
            ),
            "summary": "Refresh the Balfrin checkout to the package source revision before considering a retry.",
        }
    return {
        "schema_version": "balfrin_remote_head_alignment_v1",
        "status": "ready_remote_head_aligned",
        "aligned": True,
        "remote_head": remote_head,
        "local_head": local_head,
        "access_preflight_path": access_source,
        "blocked_reason": "",
        "summary": "Balfrin remote HEAD matches the local package source HEAD.",
    }


def build_compact_manifest_freshness(handoff_report: dict[str, Any]) -> dict[str, Any]:
    manifest_pruning = dict(handoff_report.get("manifest_pruning") or {})
    active_projection = dict(manifest_pruning.get("active_handoff_output_budget_projection") or {})
    mode = manifest_pruning.get("mode") or active_projection.get("projection_mode")
    status = str(manifest_pruning.get("status") or "")
    projection_status = str(active_projection.get("status") or "")
    projection_path = active_projection.get("projection_manifest_path")
    ready = mode == "compact" and status in {
        "budget_passes_no_reduction_needed",
        "blocked_budget_reduction_needed",
    }
    return {
        "schema_version": "balfrin_compact_manifest_freshness_v1",
        "status": "ready_compact_manifest_current" if ready else "blocked_compact_manifest_not_current",
        "fresh": ready,
        "manifest_pruning_status": status,
        "manifest_mode": mode,
        "active_projection_status": projection_status,
        "active_projection_manifest_path": projection_path,
        "manifest_size_bytes": active_projection.get("manifest_size_bytes"),
        "output_file_count": active_projection.get("output_file_count"),
        "sidecar_file_count": active_projection.get("sidecar_file_count"),
        "reducer_manifest_file_count": active_projection.get("reducer_manifest_file_count"),
        "projection_hashes": dict(manifest_pruning.get("projection_hashes") or {}),
        "blocked_reason": ""
        if ready
        else "regional split package did not use the current compact handoff manifest projection",
        "summary": manifest_pruning.get("summary"),
    }


def build_scratch_package_freshness(
    *,
    artifact_dir: Path,
    access_report: dict[str, Any],
    access_source: str,
) -> dict[str, Any]:
    package_json = artifact_dir / DEFAULT_PACKAGE_JSON.name
    package_text = artifact_dir / DEFAULT_PACKAGE_TXT.name
    existing_paths = [path for path in (package_json, package_text) if path.exists()]
    expected = {
        "balfrin_remote_head": access_report.get("remote_head"),
        "balfrin_access_preflight_path": access_source,
    }
    base = {
        "schema_version": "balfrin_scratch_package_freshness_v1",
        "artifact_dir": str(artifact_dir),
        "package_json_path": str(package_json),
        "package_text_path": str(package_text),
        "existing_paths": [str(path) for path in existing_paths],
        "expected": expected,
    }
    if not existing_paths:
        return {
            **base,
            "status": "ready_clean_scratch",
            "fresh": True,
            "blocked_reason": "",
            "remediation": "No existing regional split package artifacts were present in the scratch package directory.",
        }

    try:
        existing_package = load_json(package_json)
    except (OSError, json.JSONDecodeError) as exc:
        return _blocked_stale_scratch_package(
            base,
            reason=f"existing scratch package is unreadable or missing JSON: {exc}",
        )

    existing_inputs = dict(existing_package.get("generation_inputs") or {})
    mismatches: list[str] = []
    for key, value in expected.items():
        if existing_inputs.get(key) != value:
            mismatches.append(f"{key}: existing={existing_inputs.get(key)!r} current={value!r}")
    if existing_package.get("schema_version") != SCHEMA_VERSION:
        mismatches.append(
            f"schema_version: existing={existing_package.get('schema_version')!r} current={SCHEMA_VERSION!r}"
        )
    if mismatches:
        return _blocked_stale_scratch_package(
            {
                **base,
                "existing_generation_inputs": existing_inputs,
                "mismatches": mismatches,
            },
            reason="existing regional split scratch package does not match the current access preflight or remote HEAD",
        )

    return {
        **base,
        "status": "ready_existing_current_package",
        "fresh": True,
        "blocked_reason": "",
        "existing_generation_inputs": existing_inputs,
        "remediation": "Existing scratch package matches the current access preflight path and remote HEAD.",
    }


def _blocked_stale_scratch_package(base: dict[str, Any], *, reason: str) -> dict[str, Any]:
    artifact_dir = Path(str(base["artifact_dir"]))
    preserve_path = artifact_dir.parent / f"{artifact_dir.name}_preserve_before_retry.tgz"
    return {
        **base,
        "status": "blocked_stale_scratch_package",
        "fresh": False,
        "blocked_reason": reason,
        "preserve_command": f"tar -C {artifact_dir.parent} -czf {preserve_path} {artifact_dir.name}",
        "clean_command": f"rm -rf {artifact_dir}",
        "use_unique_artifact_dir_guidance": (
            "Retry with a new --artifact-dir under /tmp for local ephemeral work, "
            "or under /scratch/mch/olifu/rust_rockfall on Balfrin."
        ),
        "remediation": (
            "Preserve the existing scratch package or choose a unique --artifact-dir, then remove the stale "
            "local scratch directory before regenerating the regional split package."
        ),
    }


def build_writable_remote_roots(preflight_report: dict[str, Any]) -> dict[str, Any]:
    submit_contract = dict(preflight_report.get("submit_contract_requirement") or {})
    run_root = submit_contract.get("run_root")
    writability = submit_contract.get("run_root_writability_status")
    status = "ready" if submit_contract.get("status") == "ready" and writability else "blocked_remote_root"
    return {
        "status": status,
        "run_root": run_root,
        "writability_status": writability,
        "partition": "postproc",
        "remote_root_prefix": str(preflight.REVIEWED_BALFRIN_RUN_ROOT_PREFIX),
        "blocked_reason": "" if status == "ready" else submit_contract.get("blocked_reason", "run root is not ready"),
        "creation_policy": "reviewed scratch-root contract only; package generation does not create remote roots",
    }


def build_output_budget_summary(handoff_report: dict[str, Any], preflight_report: dict[str, Any]) -> dict[str, Any]:
    reducer = dict(preflight_report.get("reducer_budget_requirement") or {})
    projection = dict(handoff_report.get("handoff_output_budget_projection") or {})
    validation = dict(preflight_report.get("output_budget_acceptance_validation") or {})
    manifest_pruning = dict(handoff_report.get("manifest_pruning") or {})
    blocked_reasons: list[str] = []
    if reducer.get("status") != "ready":
        blocked_reasons.extend(str(reason) for reason in reducer.get("blocked_reasons") or [])
    if validation.get("status") != "accepted":
        blocked_reasons.append(validation.get("summary") or "output-budget acceptance is not accepted")
    if manifest_pruning.get("status") == "blocked_budget_reduction_needed":
        blocked_reasons.append(manifest_pruning.get("blocked_reason") or "manifest pruning still needs reduction")
    return {
        "status": "ready" if not blocked_reasons else "blocked_output_budget",
        "blocked_reasons": dedupe(blocked_reasons),
        "threshold_profile_id": reducer.get("output_budget_acceptance_threshold_profile_id"),
        "acceptance_status": validation.get("status"),
        "acceptance_validation": validation,
        "budget_thresholds": preflight_report.get("output_budget_acceptance_thresholds", {}),
        "projection_mode": projection.get("projection_mode"),
        "manifest_size_bytes": projection.get("manifest_size_bytes"),
        "output_file_count": projection.get("output_file_count"),
        "sidecar_file_count": projection.get("sidecar_file_count"),
        "reducer_manifest_file_count": projection.get("reducer_manifest_file_count"),
        "replay_critical_retained_output_families": list(
            projection.get("replay_critical_retained_output_families") or []
        ),
        "manifest_pruning_status": manifest_pruning.get("status"),
        "manifest_pruning": manifest_pruning,
    }


def build_preservation_plan(
    handoff_report: dict[str, Any],
    preflight_report: dict[str, Any],
    artifact_dir: Path,
) -> dict[str, Any]:
    run_shape = dict(preflight_report.get("smallest_multi_zone_run_shape") or {})
    checklist = list(run_shape.get("preservation_checklist") or [])
    hazard_package = dict(run_shape.get("hazard_package") or {})
    instructions = dict(hazard_package.get("preservation_instructions") or {})
    do_not_commit = list(instructions.get("do_not_commit_paths") or [])
    for path in (
        artifact_dir,
        handoff_report.get("package_json_path"),
        handoff_report.get("command_plan_path"),
        handoff_report.get("sbatch_script_path"),
    ):
        if path is not None and str(path) not in do_not_commit:
            do_not_commit.append(str(path))
    return {
        "status": "ready" if checklist else "blocked_missing_preservation_plan",
        "checklist": checklist,
        "do_not_commit_paths": do_not_commit,
        "ignored_output_roots": list(handoff_report.get("ignored_output_roots") or []),
        "notes": list(instructions.get("notes") or []),
    }


def classify_submission_package_status(
    *,
    package_contract: dict[str, Any],
    preflight_report: dict[str, Any],
    output_budget: dict[str, Any],
    writable_remote_roots: dict[str, Any],
    scratch_package_freshness: dict[str, Any],
    remote_head_alignment: dict[str, Any],
    compact_manifest_freshness: dict[str, Any],
) -> str:
    if scratch_package_freshness["status"] == "blocked_stale_scratch_package":
        return "failed_closed_stale_scratch_package"
    if str(remote_head_alignment["status"]).startswith("blocked_"):
        return "failed_closed_remote_head_mismatch"
    if compact_manifest_freshness["status"] != "ready_compact_manifest_current":
        return "failed_closed_compact_manifest_stale"
    if package_contract["status"] != "ready":
        return "failed_closed_package_contract"
    if output_budget["status"] != "ready":
        return "failed_closed_output_budget"
    if writable_remote_roots["status"] != "ready":
        return "failed_closed_remote_roots"
    if preflight_report.get("preflight_status") != preflight.STATUS_READY:
        return "failed_closed_preflight"
    return "ready_for_bounded_postproc_submission"


def first_blocker(
    *,
    package_contract: dict[str, Any],
    preflight_report: dict[str, Any],
    output_budget: dict[str, Any],
    writable_remote_roots: dict[str, Any],
    scratch_package_freshness: dict[str, Any],
    remote_head_alignment: dict[str, Any],
    compact_manifest_freshness: dict[str, Any],
) -> dict[str, Any] | None:
    if scratch_package_freshness["status"] == "blocked_stale_scratch_package":
        return {
            "gate": "scratch_package_freshness",
            "status": scratch_package_freshness["status"],
            "reason": scratch_package_freshness.get("blocked_reason", ""),
        }
    if str(remote_head_alignment["status"]).startswith("blocked_"):
        return {
            "gate": "remote_head_alignment",
            "status": remote_head_alignment["status"],
            "reason": remote_head_alignment.get("blocked_reason", ""),
        }
    if compact_manifest_freshness["status"] != "ready_compact_manifest_current":
        return {
            "gate": "compact_manifest_freshness",
            "status": compact_manifest_freshness["status"],
            "reason": compact_manifest_freshness.get("blocked_reason", ""),
        }
    if package_contract["status"] != "ready":
        return {"gate": "package_contract", "status": package_contract["status"], "reason": "; ".join(package_contract["blocked_reasons"])}
    if output_budget["status"] != "ready":
        return {"gate": "output_budget", "status": output_budget["status"], "reason": "; ".join(output_budget["blocked_reasons"])}
    if writable_remote_roots["status"] != "ready":
        return {
            "gate": "writable_remote_roots",
            "status": writable_remote_roots["status"],
            "reason": writable_remote_roots.get("blocked_reason", ""),
        }
    if preflight_report.get("preflight_status") != preflight.STATUS_READY:
        return {
            "gate": "authorization_preflight",
            "status": preflight_report.get("preflight_status"),
            "reason": preflight_report.get("blocked_reason", ""),
        }
    return None


def build_batched_scenario_smoke_package(
    *,
    scenario_batching_contract: dict[str, Any],
    artifact_dir: Path = DEFAULT_SCENARIO_BATCH_SMOKE_ARTIFACT_DIR,
) -> dict[str, Any]:
    artifact_dir = resolve_output_root(artifact_dir)
    if not is_allowed_output_root(artifact_dir):
        raise BalfrinRegionalSplitSubmissionPackageError(
            "artifact-dir must stay under /tmp, validation/private, or the reviewed Balfrin scratch root "
            f"{handoff.BALFRIN_REVIEWED_SCRATCH_OUTPUT_ROOT}: {artifact_dir}"
        )

    contract = dict(scenario_batching_contract or {})
    contract_status = str(contract.get("batching_status") or "blocked_missing_inputs")
    batch_count = int(contract.get("batch_count") or 0)
    ready = contract_status == "ready" and batch_count > 0
    package_status = "ready_for_batched_scenario_smoke" if ready else "failed_closed_scenario_batch_contract"
    first_blocker = None if ready else {
        "gate": "scenario_batching_contract",
        "status": contract_status,
        "reason": str(contract.get("blocked_reason") or "scenario batching contract is not ready"),
    }
    package_json_path = artifact_dir / DEFAULT_SCENARIO_BATCH_SMOKE_JSON.name
    package_text_path = artifact_dir / DEFAULT_SCENARIO_BATCH_SMOKE_TXT.name
    return {
        "schema_version": SCENARIO_BATCH_SMOKE_SCHEMA_VERSION,
        "package_status": package_status,
        "ready_for_batched_scenario_smoke": ready,
        "first_blocker": first_blocker,
        "artifact_dir": str(artifact_dir),
        "package_json_path": str(package_json_path),
        "package_text_path": str(package_text_path),
        "scenario_batching_contract": contract,
        "scenario_batching_summary": dict(contract.get("batching_summary") or {}),
        "scenario_batch_count": batch_count,
        "scenario_row_count": int(contract.get("scenario_row_count") or 0),
        "release_zone_count": int(contract.get("release_zone_count") or 0),
        "no_submit_semantics": {
            "status": "not_submitted",
            "sbatch_attempted": False,
            "submit_command_executed": False,
            "package_generation_only": True,
            "smoke_only": True,
            "boundary_note": "Smoke packaging records the batched scenario contract and never executes sbatch.",
        },
        "claim_boundaries": {
            "operational_claims_allowed": False,
            "annual_frequency_claims_allowed": False,
            "physical_probability_claims_allowed": False,
            "risk_exposure_vulnerability_claims_allowed": False,
            "scale_up_authorized": False,
            "distributed_execution_authorized": False,
            "live_submission_performed": False,
        },
        "output_paths": {
            "package_json": str(package_json_path),
            "package_text": str(package_text_path),
        },
    }


def materialize_batched_scenario_smoke_artifacts(
    report: dict[str, Any],
    *,
    json_output: Path | None = None,
    text_output: Path | None = None,
) -> None:
    artifact_dir = Path(report["artifact_dir"])
    artifact_dir.mkdir(parents=True, exist_ok=True)
    report_json = Path(report["package_json_path"])
    report_text = Path(report["package_text_path"])
    report_json.write_text(json.dumps(report, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    report_text.write_text(render_batched_scenario_smoke_text_report(report) + "\n", encoding="utf-8")
    if json_output is not None and Path(json_output) != report_json:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(report, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    if text_output is not None and Path(text_output) != report_text:
        text_output.parent.mkdir(parents=True, exist_ok=True)
        text_output.write_text(render_batched_scenario_smoke_text_report(report) + "\n", encoding="utf-8")


def render_batched_scenario_smoke_text_report(report: dict[str, Any]) -> str:
    first = report.get("first_blocker") or {}
    contract = dict(report.get("scenario_batching_contract") or {})
    budget_profile = dict(contract.get("budget_profile") or {})
    lines = [
        "Balfrin Scenario Batch Smoke Package",
        "",
        f"- Package status: `{report.get('package_status')}`",
        f"- Ready for batched scenario smoke: `{report.get('ready_for_batched_scenario_smoke')}`",
        f"- First blocker: `{first.get('gate')}` `{first.get('status')}` {first.get('reason', '')}",
        f"- Batching status: `{contract.get('batching_status')}`",
        f"- Batch count: `{report.get('scenario_batch_count')}`",
        f"- Release zone batch max: `{budget_profile.get('simultaneous_release_zone_batch_max')}`",
        "",
        "## No Submit",
        "- sbatch_attempted: `False`",
        "- submit_command_executed: `False`",
        "- package_generation_only: `True`",
    ]
    return "\n".join(lines)


def materialize_artifacts(
    report: dict[str, Any],
    *,
    json_output: Path | None = None,
    text_output: Path | None = None,
) -> None:
    artifact_dir = Path(report["artifact_dir"])
    artifact_dir.mkdir(parents=True, exist_ok=True)
    report_json = Path(report["package_json_path"])
    report_text = Path(report["package_text_path"])
    report_json.write_text(json.dumps(report, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    report_text.write_text(render_text_report(report) + "\n", encoding="utf-8")
    if json_output is not None and Path(json_output) != report_json:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(report, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    if text_output is not None and Path(text_output) != report_text:
        text_output.parent.mkdir(parents=True, exist_ok=True)
        text_output.write_text(render_text_report(report) + "\n", encoding="utf-8")


def render_text_report(report: dict[str, Any]) -> str:
    first = report.get("first_blocker") or {}
    regional = dict(report.get("regional_split_merge_contract") or {})
    roots = dict(report.get("writable_remote_roots") or {})
    budget = dict(report.get("output_budget") or {})
    freshness = dict(report.get("scratch_package_freshness") or {})
    alignment = dict(report.get("remote_head_alignment") or {})
    compact = dict(report.get("compact_manifest_freshness") or {})
    lines = [
        "Balfrin Regional Split Submission Package",
        "",
        f"- Submission package status: `{report.get('submission_package_status')}`",
        f"- Ready for bounded postproc submission: `{report.get('ready_for_bounded_postproc_submission')}`",
        f"- Authorization preflight status: `{report.get('authorization_preflight_status')}`",
        f"- First blocker: `{first.get('gate')}` `{first.get('status')}` {first.get('reason', '')}",
        f"- Balfrin remote HEAD: `{report.get('balfrin_remote_head')}`",
        f"- Access preflight path: `{report.get('balfrin_access_preflight_path')}`",
        f"- Remote-head alignment: `{alignment.get('status')}` local=`{alignment.get('local_head')}`",
        f"- Scratch package freshness: `{freshness.get('status')}`",
        f"- Compact manifest freshness: `{compact.get('status')}` mode=`{compact.get('manifest_mode')}`",
        f"- Exact bounded postproc command: `{report.get('exact_bounded_postproc_command')}`",
        "",
        "## Regional Split/Merge",
        f"- Contract status: `{regional.get('status')}`",
        f"- Split count: `{regional.get('split_count')}`",
        f"- Execution key count: `{regional.get('execution_key_count')}`",
        f"- Merge order: `{regional.get('merge_order')}`",
        f"- Merge deterministic: `{regional.get('merge_order_deterministic')}`",
        f"- Split plan: `{regional.get('regional_split_plan_path')}`",
        f"- Merge manifest: `{regional.get('regional_merge_manifest_path')}`",
        "",
        "## Remote Roots",
        f"- Status: `{roots.get('status')}`",
        f"- Run root: `{roots.get('run_root')}`",
        f"- Writability status: `{roots.get('writability_status')}`",
        "",
        "## Output Budget",
        f"- Status: `{budget.get('status')}`",
        f"- Threshold profile: `{budget.get('threshold_profile_id')}`",
        f"- Acceptance status: `{budget.get('acceptance_status')}`",
        f"- Manifest bytes: `{budget.get('manifest_size_bytes')}`",
        f"- Output files: `{budget.get('output_file_count')}`",
        f"- Compact manifest bytes: `{compact.get('manifest_size_bytes')}`",
        f"- Compact sidecar files: `{compact.get('sidecar_file_count')}`",
        "",
        "## Preservation",
    ]
    for item in dict(report.get("preservation_plan") or {}).get("checklist") or []:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## No Submit",
            "- sbatch_attempted: `False`",
            "- balfrin_job_submitted: `False`",
        ]
    )
    return "\n".join(lines)


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def structured_json_status(path: Path, label: str) -> dict[str, Any]:
    if not path.exists():
        return {"status": "missing", "value": {}, "blocked_reason": f"missing {label}: {path}"}
    try:
        return {"status": "ready", "value": load_json(path), "blocked_reason": ""}
    except (OSError, json.JSONDecodeError) as exc:
        return {"status": "blocked_unreadable", "value": {}, "blocked_reason": f"unreadable {label}: {exc}"}


def file_sha256(path: Path) -> str:
    return handoff.file_sha256(path)


def resolve_output_root(path: Path) -> Path:
    if path.is_absolute():
        return path.resolve()
    return (ROOT / path).resolve()


def is_allowed_output_root(path: Path) -> bool:
    return handoff.is_allowed_output_root(path)


def dedupe(items: list[str]) -> list[str]:
    deduped: list[str] = []
    for item in items:
        text = str(item or "").strip()
        if text and text not in deduped:
            deduped.append(text)
    return deduped


def local_git_head() -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def access_preflight_ready_status() -> str:
    return getattr(preflight.access_preflight, "STATUS_READY", "ready_for_read_only_collection")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        access_report = load_json(args.balfrin_access_preflight_json) if args.balfrin_access_preflight_json else None
        report = build_report(
            artifact_dir=args.artifact_dir,
            handoff_artifact_dir=args.handoff_artifact_dir,
            pressure_probe_root=args.pressure_probe_root,
            balfrin_access_preflight=access_report,
            balfrin_access_preflight_source=str(args.balfrin_access_preflight_json)
            if args.balfrin_access_preflight_json
            else "not_supplied",
        )
    except (BalfrinRegionalSplitSubmissionPackageError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"balfrin regional split submission package error: {exc}", file=sys.stderr)
        return 2

    materialize_artifacts(report, json_output=args.json_output, text_output=args.text_output)
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
    else:
        print(render_text_report(report))
    return 0 if report["ready_for_bounded_postproc_submission"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
