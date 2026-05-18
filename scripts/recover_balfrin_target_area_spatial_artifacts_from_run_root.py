#!/usr/bin/env python3
"""Inventory target-area spatial artifacts from the preserved Balfrin run root.

This helper is read-only. It consumes the Balfrin access preflight, inspects
the existing authorized target-area run root or a local fixture, and classifies
spatial artifacts separately from execution-metrics closure. It does not submit
jobs, cancel jobs, write remote files, or upgrade physical or operational
claim boundaries.
"""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Callable

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import check_balfrin_remote_access_preflight as access_preflight  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "balfrin_target_area_spatial_artifact_recovery_v1"
REPORT_BASENAME = "balfrin_target_area_spatial_artifact_recovery_v1"
DEFAULT_ARTIFACT_DIR = ROOT / "validation/private/tschamut_public_pilot/balfrin_target_area_spatial_artifact_recovery_v1"
ACCESS_READY_STATUS = access_preflight.STATUS_READY

STATUS_RECOVERED = "spatial_artifacts_recovered"
STATUS_DEFERRED = "spatial_artifacts_deferred"
STATUS_BLOCKED_ACCESS = "blocked_access"
STATUS_COLLECTION_FAILED = "blocked_collection_failed"

ARTIFACT_RECOVERED = "recovered"
ARTIFACT_NOT_REQUIRED_FOR_METRICS = "not_required_for_execution_metrics_closure"
ARTIFACT_UNAVAILABLE_FROM_ROOT = "unavailable_from_preserved_root"
ARTIFACT_BLOCKED_ACCESS = "blocked_access"

Runner = Callable[..., subprocess.CompletedProcess[str]]


@dataclass(frozen=True)
class SpatialArtifactSpec:
    artifact_id: str
    artifact_kind: str
    description: str
    manifest_kind: str | None = None
    layer_key: str | None = None
    filename: str | None = None


REQUIRED_SPATIAL_ARTIFACTS: tuple[SpatialArtifactSpec, ...] = (
    SpatialArtifactSpec(
        "hazard_run_manifest",
        "hazard_manifest",
        "hazard run manifest declaring target-area layers and package outputs",
    ),
    SpatialArtifactSpec(
        "map_package_manifest",
        "manifest_output",
        "standard map-package manifest declared by the hazard run manifest",
        manifest_kind="map_package_manifest",
    ),
    SpatialArtifactSpec(
        "pilot_gis_package_manifest",
        "manifest_output",
        "pilot GIS package manifest declared by the hazard run manifest",
        manifest_kind="pilot_gis_package_manifest",
    ),
    SpatialArtifactSpec(
        "cellwise_layer:max_kinetic_energy",
        "cellwise_layer",
        "cellwise max_kinetic_energy grid needed for spatial uncertainty interpretation",
        layer_key="max_kinetic_energy",
    ),
    SpatialArtifactSpec(
        "cellwise_layer:max_jump_height",
        "cellwise_layer",
        "cellwise max_jump_height grid needed for spatial uncertainty interpretation",
        layer_key="max_jump_height",
    ),
    SpatialArtifactSpec(
        "cellwise_layer:velocity_exceedance_5mps",
        "cellwise_layer",
        "cellwise velocity_exceedance_5mps grid needed for the default spatial uncertainty layer set",
        layer_key="velocity_exceedance_5mps",
    ),
    SpatialArtifactSpec(
        "spatial_uncertainty_layer_summary",
        "spatial_interpretation_product",
        "compact spatial uncertainty layer summary product",
        filename="spatial_uncertainty_layer_summary.json",
    ),
    SpatialArtifactSpec(
        "spatial_uncertainty_region_products_geojson",
        "spatial_interpretation_product",
        "GeoJSON region products for spatial uncertainty interpretation",
        filename="spatial_uncertainty_region_products.geojson",
    ),
    SpatialArtifactSpec(
        "spatial_confidence_product_manifest",
        "spatial_interpretation_product",
        "spatial confidence product manifest for diagnostic-only GIS products",
        filename="spatial_confidence_product_manifest.json",
    ),
)


class BalfrinTargetAreaSpatialArtifactRecoveryError(ValueError):
    """User-facing spatial artifact recovery error."""


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--run-root",
        default=str(access_preflight.DEFAULT_RUN_ROOT),
        help="Existing authorized Balfrin target-area run root.",
    )
    parser.add_argument(
        "--remote-repo-root",
        default=access_preflight.DEFAULT_REMOTE_REPO_ROOT,
        help="Balfrin git checkout used for read-only remote collection.",
    )
    parser.add_argument("--ssh-target", default=access_preflight.DEFAULT_SSH_TARGET, help="SSH host alias for Balfrin.")
    parser.add_argument("--connect-timeout", type=int, default=10, help="SSH ConnectTimeout in seconds.")
    parser.add_argument("--balfrin-access-json", type=Path, default=None, help="Optional Balfrin access preflight JSON.")
    parser.add_argument("--inventory-json", type=Path, default=None, help="Optional pre-collected spatial inventory JSON.")
    parser.add_argument("--local-run-root", type=Path, default=None, help="Local fixture or mounted run root. Skips SSH.")
    parser.add_argument("--artifact-dir", type=Path, default=None, help="Optional directory for JSON and text report.")
    parser.add_argument("--json-output", type=Path, default=None)
    parser.add_argument("--text-output", type=Path, default=None)
    parser.add_argument("--format", choices=("json", "text"), default="text")
    return parser.parse_args(argv)


def _load_json(path: Path | None) -> dict[str, Any] | None:
    if path is None or not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else None


def _safe_mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _safe_list(value: Any) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def _trim(value: str | None, limit: int = 1200) -> str:
    if value is None:
        return ""
    text = value.strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def _ssh_base_args(ssh_target: str, connect_timeout: int) -> list[str]:
    return ["ssh", "-o", "BatchMode=yes", "-o", f"ConnectTimeout={connect_timeout}", ssh_target]


def _run_remote_text(
    *,
    ssh_target: str,
    connect_timeout: int,
    remote_command: str,
    runner: Runner,
) -> subprocess.CompletedProcess[str]:
    return runner(
        [*_ssh_base_args(ssh_target, connect_timeout), remote_command],
        check=False,
        capture_output=True,
        text=True,
    )


def _remote_cat_json(
    *,
    ssh_target: str,
    connect_timeout: int,
    path: str,
    runner: Runner,
) -> dict[str, Any] | None:
    quoted = shlex.quote(str(PurePosixPath(path)))
    result = _run_remote_text(
        ssh_target=ssh_target,
        connect_timeout=connect_timeout,
        remote_command=f"test -r {quoted} && cat {quoted}",
        runner=runner,
    )
    if result.returncode != 0:
        return None
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def _posix_resolve(path_value: str, *, cwd: str, run_root: str) -> str:
    path = PurePosixPath(path_value)
    if path.is_absolute():
        return str(path)
    base = PurePosixPath(cwd)
    if not base.is_absolute():
        base = PurePosixPath(run_root) / base
    return str(base / path)


def _command_output_dir(command_plan: dict[str, Any], *, run_root: str) -> str:
    commands = command_plan.get("commands")
    if not isinstance(commands, list):
        return f"{run_root}/output"
    for entry in commands:
        if not isinstance(entry, dict) or entry.get("name") != "build_conditional_hazard_layers":
            continue
        command = entry.get("command")
        if not isinstance(command, list):
            continue
        cwd = str(entry.get("cwd") or run_root)
        tokens = [str(token) for token in command]
        for idx, token in enumerate(tokens):
            if token == "--output-dir" and idx + 1 < len(tokens):
                return _posix_resolve(tokens[idx + 1], cwd=cwd, run_root=run_root)
    return f"{run_root}/output"


def _local_command_output_dir(command_plan: dict[str, Any], *, run_root: Path) -> Path:
    output_dir = _command_output_dir(command_plan, run_root=str(run_root))
    return Path(output_dir)


def _first_manifest_in_local_output(output_root: Path) -> Path | None:
    if not output_root.exists():
        return None
    matches = sorted(path for path in output_root.glob("*_manifest.json") if path.is_file())
    for path in matches:
        payload = _load_json(path) or {}
        if isinstance(payload.get("cellwise_layers"), list) or isinstance(payload.get("outputs"), list):
            return path
    return matches[0] if matches else None


def _remote_manifest_candidates(
    *,
    ssh_target: str,
    connect_timeout: int,
    output_root: str,
    runner: Runner,
) -> list[str]:
    result = _run_remote_text(
        ssh_target=ssh_target,
        connect_timeout=connect_timeout,
        remote_command=(
            f"find {shlex.quote(str(PurePosixPath(output_root)))} -maxdepth 1 "
            "-type f -name '*_manifest.json' -print 2>/dev/null | sort"
        ),
        runner=runner,
    )
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _remote_first_hazard_manifest(
    *,
    ssh_target: str,
    connect_timeout: int,
    output_root: str,
    runner: Runner,
) -> tuple[str | None, dict[str, Any]]:
    fallback_path: str | None = None
    fallback_payload: dict[str, Any] = {}
    for path in _remote_manifest_candidates(
        ssh_target=ssh_target,
        connect_timeout=connect_timeout,
        output_root=output_root,
        runner=runner,
    ):
        payload = _remote_cat_json(
            ssh_target=ssh_target,
            connect_timeout=connect_timeout,
            path=path,
            runner=runner,
        ) or {}
        if fallback_path is None:
            fallback_path = path
            fallback_payload = payload
        if isinstance(payload.get("cellwise_layers"), list) or isinstance(payload.get("outputs"), list):
            return path, payload
    return fallback_path, fallback_payload


def _local_path_candidates(path_value: str, *, manifest_dir: Path, output_root: Path, run_root: Path) -> list[Path]:
    raw = Path(path_value)
    if raw.is_absolute():
        return [raw]
    candidates = [manifest_dir / raw, output_root / raw, run_root / raw]
    return list(dict.fromkeys(candidates))


def _remote_path_candidates(path_value: str, *, manifest_dir: str, output_root: str, run_root: str) -> list[str]:
    raw = PurePosixPath(path_value)
    if raw.is_absolute():
        return [str(raw)]
    candidates = [
        str(PurePosixPath(manifest_dir) / raw),
        str(PurePosixPath(output_root) / raw),
        str(PurePosixPath(run_root) / raw),
    ]
    return list(dict.fromkeys(candidates))


def _local_observe_existing(candidates: list[Path]) -> dict[str, Any]:
    for candidate in candidates:
        if candidate.exists():
            file_count = 1 if candidate.is_file() else sum(1 for path in candidate.rglob("*") if path.is_file())
            total_bytes = candidate.stat().st_size if candidate.is_file() else sum(path.stat().st_size for path in candidate.rglob("*") if path.is_file())
            return {
                "exists": True,
                "path": str(candidate),
                "candidate_paths": [str(path) for path in candidates],
                "file_count": file_count,
                "bytes": total_bytes,
            }
    return {
        "exists": False,
        "path": None,
        "candidate_paths": [str(path) for path in candidates],
        "file_count": None,
        "bytes": None,
    }


def _remote_observe_existing(
    *,
    ssh_target: str,
    connect_timeout: int,
    candidates: list[str],
    runner: Runner,
) -> dict[str, Any]:
    for candidate in candidates:
        quoted = shlex.quote(str(PurePosixPath(candidate)))
        result = _run_remote_text(
            ssh_target=ssh_target,
            connect_timeout=connect_timeout,
            remote_command=(
                f"if test -f {quoted}; then printf 'file %s %s\\n' {quoted} \"$(wc -c < {quoted})\"; "
                f"elif test -d {quoted}; then find {quoted} -type f -printf '%s\\n' 2>/dev/null | "
                "awk '{count += 1; bytes += $1} END {printf \"dir %d %d\\n\", count, bytes}'; "
                "else exit 1; fi"
            ),
            runner=runner,
        )
        if result.returncode != 0:
            continue
        parts = result.stdout.strip().split()
        if len(parts) == 3 and parts[0] in {"file", "dir"}:
            return {
                "exists": True,
                "path": candidate,
                "candidate_paths": candidates,
                "file_count": int(parts[1]) if parts[0] == "dir" else 1,
                "bytes": int(parts[2]),
            }
    return {"exists": False, "path": None, "candidate_paths": candidates, "file_count": None, "bytes": None}


def _local_find_named(run_root: Path, filename: str) -> dict[str, Any]:
    matches = sorted(path for path in run_root.rglob(filename) if path.is_file())
    return _local_observe_existing([matches[0]]) if matches else _local_observe_existing([run_root / filename])


def _remote_find_named(
    *,
    ssh_target: str,
    connect_timeout: int,
    run_root: str,
    filename: str,
    runner: Runner,
) -> dict[str, Any]:
    result = _run_remote_text(
        ssh_target=ssh_target,
        connect_timeout=connect_timeout,
        remote_command=(
            f"find {shlex.quote(str(PurePosixPath(run_root)))} -type f "
            f"-name {shlex.quote(filename)} -print 2>/dev/null | sort | head -n 1"
        ),
        runner=runner,
    )
    if result.returncode != 0 or not result.stdout.strip():
        return {
            "exists": False,
            "path": None,
            "candidate_paths": [str(PurePosixPath(run_root) / filename)],
            "file_count": None,
            "bytes": None,
        }
    return _remote_observe_existing(
        ssh_target=ssh_target,
        connect_timeout=connect_timeout,
        candidates=[result.stdout.strip()],
        runner=runner,
    )


def _manifest_output_path(manifest: dict[str, Any], manifest_kind: str) -> str | None:
    for entry in _safe_list(manifest.get("outputs")):
        if not isinstance(entry, dict):
            continue
        if entry.get("kind") == manifest_kind and isinstance(entry.get("path"), str):
            return str(entry["path"])
    return None


def _cellwise_grid_path(manifest: dict[str, Any], layer_key: str) -> str | None:
    for entry in _safe_list(manifest.get("cellwise_layers")):
        if not isinstance(entry, dict):
            continue
        key = entry.get("key") or entry.get("layer_name")
        if key == layer_key and isinstance(entry.get("grid_path"), str):
            return str(entry["grid_path"])
    return None


def _inventory_from_local_run_root(run_root: Path) -> dict[str, Any]:
    run_root = run_root.resolve()
    if not run_root.exists():
        raise BalfrinTargetAreaSpatialArtifactRecoveryError(f"run root does not exist: {run_root}")
    command_plan_path = run_root / "command_plan.json"
    command_plan = _load_json(command_plan_path) or {}
    output_root = _local_command_output_dir(command_plan, run_root=run_root)
    manifest_path = _first_manifest_in_local_output(output_root)
    manifest = _load_json(manifest_path) if manifest_path is not None else None
    manifest = manifest or {}
    return _build_local_inventory_snapshot(
        run_root=run_root,
        output_root=output_root,
        command_plan_path=command_plan_path,
        hazard_manifest_path=manifest_path,
        hazard_manifest=manifest,
    )


def _build_local_inventory_snapshot(
    *,
    run_root: Path,
    output_root: Path,
    command_plan_path: Path,
    hazard_manifest_path: Path | None,
    hazard_manifest: dict[str, Any],
) -> dict[str, Any]:
    manifest_dir = hazard_manifest_path.parent if hazard_manifest_path is not None else output_root
    observations: dict[str, dict[str, Any]] = {}
    for spec in REQUIRED_SPATIAL_ARTIFACTS:
        if spec.artifact_kind == "hazard_manifest":
            observations[spec.artifact_id] = _local_observe_existing([hazard_manifest_path] if hazard_manifest_path else [output_root / "missing_manifest.json"])
        elif spec.manifest_kind:
            path_value = _manifest_output_path(hazard_manifest, spec.manifest_kind)
            observations[spec.artifact_id] = (
                _local_observe_existing(_local_path_candidates(path_value, manifest_dir=manifest_dir, output_root=output_root, run_root=run_root))
                if path_value
                else _local_observe_existing([output_root / f"missing_{spec.manifest_kind}"])
            )
        elif spec.layer_key:
            path_value = _cellwise_grid_path(hazard_manifest, spec.layer_key)
            observations[spec.artifact_id] = (
                _local_observe_existing(_local_path_candidates(path_value, manifest_dir=manifest_dir, output_root=output_root, run_root=run_root))
                if path_value
                else _local_observe_existing([output_root / f"missing_layer_{spec.layer_key}"])
            )
        elif spec.filename:
            observations[spec.artifact_id] = _local_find_named(run_root, spec.filename)
    return {
        "schema_version": "balfrin_target_area_spatial_artifact_inventory_snapshot_v1",
        "collection_mode": "local_run_root",
        "run_root": str(run_root),
        "output_root": str(output_root),
        "command_plan_path": str(command_plan_path),
        "hazard_manifest_path": str(hazard_manifest_path) if hazard_manifest_path is not None else None,
        "hazard_manifest_available": bool(hazard_manifest),
        "artifact_observations": observations,
    }


def _collect_remote_inventory(
    *,
    ssh_target: str,
    connect_timeout: int,
    run_root: str,
    runner: Runner,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    run_root_posix = str(PurePosixPath(run_root))
    try:
        command_plan_path = f"{run_root_posix}/command_plan.json"
        command_plan = _remote_cat_json(
            ssh_target=ssh_target,
            connect_timeout=connect_timeout,
            path=command_plan_path,
            runner=runner,
        ) or {}
        output_root = _command_output_dir(command_plan, run_root=run_root_posix)
        hazard_manifest_path, hazard_manifest = _remote_first_hazard_manifest(
            ssh_target=ssh_target,
            connect_timeout=connect_timeout,
            output_root=output_root,
            runner=runner,
        )
        manifest_dir = str(PurePosixPath(hazard_manifest_path).parent) if hazard_manifest_path else output_root
        observations: dict[str, dict[str, Any]] = {}
        for spec in REQUIRED_SPATIAL_ARTIFACTS:
            if spec.artifact_kind == "hazard_manifest":
                observations[spec.artifact_id] = _remote_observe_existing(
                    ssh_target=ssh_target,
                    connect_timeout=connect_timeout,
                    candidates=[hazard_manifest_path or f"{output_root}/missing_manifest.json"],
                    runner=runner,
                )
            elif spec.manifest_kind:
                path_value = _manifest_output_path(hazard_manifest, spec.manifest_kind)
                observations[spec.artifact_id] = (
                    _remote_observe_existing(
                        ssh_target=ssh_target,
                        connect_timeout=connect_timeout,
                        candidates=_remote_path_candidates(path_value, manifest_dir=manifest_dir, output_root=output_root, run_root=run_root_posix),
                        runner=runner,
                    )
                    if path_value
                    else _remote_observe_existing(
                        ssh_target=ssh_target,
                        connect_timeout=connect_timeout,
                        candidates=[f"{output_root}/missing_{spec.manifest_kind}"],
                        runner=runner,
                    )
                )
            elif spec.layer_key:
                path_value = _cellwise_grid_path(hazard_manifest, spec.layer_key)
                observations[spec.artifact_id] = (
                    _remote_observe_existing(
                        ssh_target=ssh_target,
                        connect_timeout=connect_timeout,
                        candidates=_remote_path_candidates(path_value, manifest_dir=manifest_dir, output_root=output_root, run_root=run_root_posix),
                        runner=runner,
                    )
                    if path_value
                    else _remote_observe_existing(
                        ssh_target=ssh_target,
                        connect_timeout=connect_timeout,
                        candidates=[f"{output_root}/missing_layer_{spec.layer_key}"],
                        runner=runner,
                    )
                )
            elif spec.filename:
                observations[spec.artifact_id] = _remote_find_named(
                    ssh_target=ssh_target,
                    connect_timeout=connect_timeout,
                    run_root=run_root_posix,
                    filename=spec.filename,
                    runner=runner,
                )
        snapshot = {
            "schema_version": "balfrin_target_area_spatial_artifact_inventory_snapshot_v1",
            "collection_mode": "remote_read_only_file_scan",
            "run_root": run_root_posix,
            "output_root": output_root,
            "command_plan_path": command_plan_path,
            "hazard_manifest_path": hazard_manifest_path,
            "hazard_manifest_available": bool(hazard_manifest),
            "artifact_observations": observations,
        }
        diagnostic = {
            "status": "complete",
            "mode": "remote_read_only_file_scan",
            "remote_command": "read command_plan, hazard manifest, declared output paths, cellwise layers, and named spatial products",
            "returncode": 0,
            "stdout": "<json elided>",
            "stderr": "",
        }
        return snapshot, diagnostic
    except (OSError, subprocess.TimeoutExpired) as exc:
        return None, {
            "status": STATUS_COLLECTION_FAILED,
            "mode": "remote_read_only_file_scan",
            "remote_command": "read target-area spatial artifact inventory",
            "returncode": None,
            "stdout": "",
            "stderr": _trim(str(exc)),
        }


def _access_report_from_inputs(
    explicit_access_preflight: dict[str, Any] | None,
    *,
    ssh_target: str,
    remote_repo_root: str,
    run_root: str,
    connect_timeout: int,
    runner: Runner,
    run_preflight: bool,
) -> dict[str, Any]:
    if explicit_access_preflight is not None:
        return dict(explicit_access_preflight)
    if not run_preflight:
        return {
            "schema_version": access_preflight.SCHEMA_VERSION,
            "status": "not_required_for_local_or_inventory_input",
            "ready_for_read_only_collection": True,
            "read_only": True,
            "live_submission_authorized": False,
            "ssh_target": ssh_target,
            "remote_repo_root": str(PurePosixPath(remote_repo_root)),
            "run_root": str(PurePosixPath(run_root)),
            "checked_commands": [],
        }
    return access_preflight.collect_preflight_report(
        ssh_target=ssh_target,
        remote_repo_root=remote_repo_root,
        run_root=run_root,
        connect_timeout=connect_timeout,
        runner=runner,
    )


def _artifact_entry_from_observation(spec: SpatialArtifactSpec, observation: dict[str, Any]) -> dict[str, Any]:
    recovered = bool(observation.get("exists"))
    status = ARTIFACT_RECOVERED if recovered else ARTIFACT_UNAVAILABLE_FROM_ROOT
    return {
        "artifact_id": spec.artifact_id,
        "artifact_kind": spec.artifact_kind,
        "description": spec.description,
        "status": status,
        "path": observation.get("path"),
        "candidate_paths": list(observation.get("candidate_paths") or []),
        "file_count": observation.get("file_count"),
        "bytes": observation.get("bytes"),
        "required_for_target_area_spatial_interpretation": True,
        "execution_metrics_closure_status": ARTIFACT_NOT_REQUIRED_FOR_METRICS,
        "usable_as_physical_validation_evidence": False,
        "reason": ""
        if recovered
        else "not found in the preserved run-root inventory; keep as explicit spatial-artifact deferral",
    }


def _blocked_artifact_entry(spec: SpatialArtifactSpec, access_status: str) -> dict[str, Any]:
    return {
        "artifact_id": spec.artifact_id,
        "artifact_kind": spec.artifact_kind,
        "description": spec.description,
        "status": ARTIFACT_BLOCKED_ACCESS,
        "path": None,
        "candidate_paths": [],
        "file_count": None,
        "bytes": None,
        "required_for_target_area_spatial_interpretation": True,
        "execution_metrics_closure_status": ARTIFACT_NOT_REQUIRED_FOR_METRICS,
        "usable_as_physical_validation_evidence": False,
        "reason": f"Balfrin read-only access preflight status is {access_status}",
    }


def _artifact_summary(entries: list[dict[str, Any]]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    by_artifact: dict[str, dict[str, Any]] = {}
    for entry in entries:
        status = str(entry.get("status") or "unknown")
        counts[status] = counts.get(status, 0) + 1
        by_artifact[str(entry.get("artifact_id"))] = entry
    unrecovered = [entry["artifact_id"] for entry in entries if entry.get("status") != ARTIFACT_RECOVERED]
    return {
        "status": "complete" if not unrecovered else "incomplete",
        "required_artifacts": [spec.artifact_id for spec in REQUIRED_SPATIAL_ARTIFACTS],
        "entries": entries,
        "by_artifact": by_artifact,
        "status_counts": counts,
        "recovered_artifacts": [entry["artifact_id"] for entry in entries if entry.get("status") == ARTIFACT_RECOVERED],
        "unrecovered_artifacts": unrecovered,
    }


def _claim_boundaries() -> dict[str, bool]:
    return {
        "operational_claims_allowed": False,
        "physical_probability_claims_allowed": False,
        "annual_frequency_claims_allowed": False,
        "risk_exposure_vulnerability_claims_allowed": False,
        "scale_up_authorized": False,
        "distributed_execution_authorized": False,
        "live_submission_authorized": False,
        "physical_validation_evidence_established": False,
    }


def _execution_metrics_separation(entries: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "status": "separated_from_spatial_artifacts",
        "execution_metrics_closure_status": "not_evaluated_by_this_spatial_helper",
        "spatial_artifact_classification": ARTIFACT_NOT_REQUIRED_FOR_METRICS,
        "artifact_count": len(entries),
        "entries": [
            {
                "artifact_id": entry["artifact_id"],
                "status": entry["execution_metrics_closure_status"],
                "spatial_availability_status": entry["status"],
            }
            for entry in entries
        ],
        "summary": (
            "Target-area spatial artifacts are inventoried for spatial interpretation only; "
            "missing spatial products do not reopen or close execution-metrics evidence."
        ),
    }


def _spatial_interpretation_evidence(entries: list[dict[str, Any]]) -> dict[str, Any]:
    unrecovered = [entry["artifact_id"] for entry in entries if entry.get("status") != ARTIFACT_RECOVERED]
    blocked = [entry["artifact_id"] for entry in entries if entry.get("status") == ARTIFACT_BLOCKED_ACCESS]
    if blocked:
        status = "blocked_access"
    elif unrecovered:
        status = "deferred_missing_spatial_artifacts"
    else:
        status = "recovered_existing_run_root"
    return {
        "status": status,
        "usable_as_target_area_spatial_interpretation_evidence": status == "recovered_existing_run_root",
        "unrecovered_artifacts": unrecovered,
        "physical_validation_evidence_status": "not_established",
        "usable_as_physical_validation_evidence": False,
        "summary": (
            "Spatial artifacts are available for target-area interpretation."
            if status == "recovered_existing_run_root"
            else "Spatial artifacts remain explicit deferrals and are not physical validation evidence."
        ),
    }


def build_report(
    *,
    access_report: dict[str, Any] | None = None,
    inventory: dict[str, Any] | None = None,
    local_run_root: Path | None = None,
    run_root: str = str(access_preflight.DEFAULT_RUN_ROOT),
    remote_repo_root: str = access_preflight.DEFAULT_REMOTE_REPO_ROOT,
    ssh_target: str = access_preflight.DEFAULT_SSH_TARGET,
    connect_timeout: int = 10,
    runner: Runner = subprocess.run,
) -> dict[str, Any]:
    collection_diagnostic: dict[str, Any] = {"status": "not_run"}
    should_run_preflight = inventory is None and local_run_root is None
    access = _access_report_from_inputs(
        access_report,
        ssh_target=ssh_target,
        remote_repo_root=remote_repo_root,
        run_root=run_root,
        connect_timeout=connect_timeout,
        runner=runner,
        run_preflight=should_run_preflight,
    )
    access_status = str(access.get("status") or "unknown")

    if inventory is None and local_run_root is None and access_status != ACCESS_READY_STATUS:
        entries = [_blocked_artifact_entry(spec, access_status) for spec in REQUIRED_SPATIAL_ARTIFACTS]
        report = _assemble_report(
            report_status=STATUS_BLOCKED_ACCESS,
            access=access,
            collection=collection_diagnostic,
            entries=entries,
            inventory=None,
            run_root=run_root,
            remote_repo_root=remote_repo_root,
            ssh_target=ssh_target,
        )
        return report

    if inventory is None and local_run_root is not None:
        inventory = _inventory_from_local_run_root(local_run_root)
        collection_diagnostic = {"status": "complete", "mode": "local_run_root", "run_root": str(local_run_root)}
    elif inventory is None:
        inventory, collection_diagnostic = _collect_remote_inventory(
            ssh_target=ssh_target,
            connect_timeout=connect_timeout,
            run_root=run_root,
            runner=runner,
        )

    if inventory is None:
        entries = [_blocked_artifact_entry(spec, STATUS_COLLECTION_FAILED) for spec in REQUIRED_SPATIAL_ARTIFACTS]
        return _assemble_report(
            report_status=STATUS_COLLECTION_FAILED,
            access=access,
            collection=collection_diagnostic,
            entries=entries,
            inventory=None,
            run_root=run_root,
            remote_repo_root=remote_repo_root,
            ssh_target=ssh_target,
        )

    observations = _safe_mapping(inventory.get("artifact_observations"))
    entries = [
        _artifact_entry_from_observation(spec, _safe_mapping(observations.get(spec.artifact_id)))
        for spec in REQUIRED_SPATIAL_ARTIFACTS
    ]
    report_status = STATUS_RECOVERED if all(entry["status"] == ARTIFACT_RECOVERED for entry in entries) else STATUS_DEFERRED
    return _assemble_report(
        report_status=report_status,
        access=access,
        collection=collection_diagnostic,
        entries=entries,
        inventory=inventory,
        run_root=str(inventory.get("run_root") or run_root),
        remote_repo_root=remote_repo_root,
        ssh_target=ssh_target,
    )


def _assemble_report(
    *,
    report_status: str,
    access: dict[str, Any],
    collection: dict[str, Any],
    entries: list[dict[str, Any]],
    inventory: dict[str, Any] | None,
    run_root: str,
    remote_repo_root: str,
    ssh_target: str,
) -> dict[str, Any]:
    artifact_summary = _artifact_summary(entries)
    spatial_evidence = _spatial_interpretation_evidence(entries)
    report = {
        "schema_version": SCHEMA_VERSION,
        "report_status": report_status,
        "read_only": True,
        "live_submission_authorized": False,
        "run_root": run_root,
        "remote_repo_root": remote_repo_root,
        "ssh_target": ssh_target,
        "balfrin_access_preflight": access,
        "collection": collection,
        "inventory_source": {
            "schema_version": inventory.get("schema_version") if isinstance(inventory, dict) else None,
            "collection_mode": inventory.get("collection_mode") if isinstance(inventory, dict) else None,
            "output_root": inventory.get("output_root") if isinstance(inventory, dict) else None,
            "command_plan_path": inventory.get("command_plan_path") if isinstance(inventory, dict) else None,
            "hazard_manifest_path": inventory.get("hazard_manifest_path") if isinstance(inventory, dict) else None,
            "hazard_manifest_available": inventory.get("hazard_manifest_available") if isinstance(inventory, dict) else False,
        },
        "spatial_artifact_recovery": artifact_summary,
        "execution_metrics_closure_separation": _execution_metrics_separation(entries),
        "spatial_interpretation_evidence": spatial_evidence,
        "claim_boundaries": _claim_boundaries(),
    }
    report["summary"] = summarize_report(report)
    return report


def summarize_report(report: dict[str, Any]) -> str:
    recovery = report.get("spatial_artifact_recovery", {}) if isinstance(report, dict) else {}
    counts = recovery.get("status_counts", {}) if isinstance(recovery, dict) else {}
    spatial = report.get("spatial_interpretation_evidence", {}) if isinstance(report, dict) else {}
    return (
        "Balfrin target-area spatial artifact recovery "
        f"{report.get('report_status', 'unknown')}: "
        f"{counts.get(ARTIFACT_RECOVERED, 0)} recovered, "
        f"{counts.get(ARTIFACT_UNAVAILABLE_FROM_ROOT, 0)} unavailable from preserved root, "
        f"{counts.get(ARTIFACT_BLOCKED_ACCESS, 0)} blocked by access. "
        f"spatial_interpretation_evidence={spatial.get('status', 'unknown')}; "
        "spatial artifacts are not required for execution-metrics closure."
    )


def render_text_report(report: dict[str, Any]) -> str:
    lines = [
        "Balfrin Target-Area Spatial Artifact Recovery",
        f"schema_version: {report.get('schema_version', 'unknown')}",
        f"report_status: {report.get('report_status', 'unknown')}",
        f"read_only: {report.get('read_only', True)}",
        f"live_submission_authorized: {report.get('live_submission_authorized', False)}",
        f"run_root: {report.get('run_root', 'unknown')}",
        f"ssh_target: {report.get('ssh_target', 'unknown')}",
        f"remote_repo_root: {report.get('remote_repo_root', 'unknown')}",
        f"summary: {report.get('summary', '')}",
    ]
    access = _safe_mapping(report.get("balfrin_access_preflight"))
    lines.extend(
        [
            "balfrin_access_preflight:",
            f"  status: {access.get('status', 'unknown')}",
            f"  ready_for_read_only_collection: {access.get('ready_for_read_only_collection', False)}",
            f"  live_submission_authorized: {access.get('live_submission_authorized', False)}",
        ]
    )
    collection = _safe_mapping(report.get("collection"))
    lines.extend(
        [
            "collection:",
            f"  status: {collection.get('status', 'unknown')}",
            f"  mode: {collection.get('mode', '')}",
            f"  returncode: {collection.get('returncode')}",
        ]
    )
    source = _safe_mapping(report.get("inventory_source"))
    lines.extend(
        [
            "inventory_source:",
            f"  collection_mode: {source.get('collection_mode')}",
            f"  output_root: {source.get('output_root')}",
            f"  hazard_manifest_path: {source.get('hazard_manifest_path')}",
            f"  hazard_manifest_available: {source.get('hazard_manifest_available')}",
        ]
    )
    recovery = _safe_mapping(report.get("spatial_artifact_recovery"))
    lines.append("spatial_artifact_recovery:")
    lines.append(f"  status: {recovery.get('status', 'unknown')}")
    lines.append(f"  status_counts: {recovery.get('status_counts', {})}")
    for entry in recovery.get("entries", []):
        lines.append(
            "  - "
            f"{entry.get('artifact_id')}: {entry.get('status')} path={entry.get('path')} "
            f"execution_metrics_closure_status={entry.get('execution_metrics_closure_status')} "
            f"reason={entry.get('reason', '')}"
        )
    separation = _safe_mapping(report.get("execution_metrics_closure_separation"))
    lines.extend(
        [
            "execution_metrics_closure_separation:",
            f"  status: {separation.get('status', 'unknown')}",
            f"  spatial_artifact_classification: {separation.get('spatial_artifact_classification')}",
            f"  summary: {separation.get('summary', '')}",
        ]
    )
    spatial = _safe_mapping(report.get("spatial_interpretation_evidence"))
    lines.extend(
        [
            "spatial_interpretation_evidence:",
            f"  status: {spatial.get('status', 'unknown')}",
            f"  usable_as_target_area_spatial_interpretation_evidence: {spatial.get('usable_as_target_area_spatial_interpretation_evidence')}",
            f"  physical_validation_evidence_status: {spatial.get('physical_validation_evidence_status')}",
            f"  usable_as_physical_validation_evidence: {spatial.get('usable_as_physical_validation_evidence')}",
            f"  unrecovered_artifacts: {spatial.get('unrecovered_artifacts', [])}",
        ]
    )
    boundaries = _safe_mapping(report.get("claim_boundaries"))
    lines.append("claim_boundaries:")
    for key in (
        "operational_claims_allowed",
        "physical_probability_claims_allowed",
        "annual_frequency_claims_allowed",
        "risk_exposure_vulnerability_claims_allowed",
        "scale_up_authorized",
        "distributed_execution_authorized",
        "live_submission_authorized",
        "physical_validation_evidence_established",
    ):
        lines.append(f"  {key}: {boundaries.get(key)}")
    return "\n".join(lines)


def materialize_artifacts(
    report: dict[str, Any],
    *,
    json_output: Path | None = None,
    text_output: Path | None = None,
    artifact_dir: Path | None = None,
) -> None:
    if artifact_dir is not None:
        artifact_dir.mkdir(parents=True, exist_ok=True)
        json_output = json_output or (artifact_dir / f"{REPORT_BASENAME}.json")
        text_output = text_output or (artifact_dir / f"{REPORT_BASENAME}.txt")
    if json_output is not None:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if text_output is not None:
        text_output.parent.mkdir(parents=True, exist_ok=True)
        text_output.write_text(render_text_report(report) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        access_report = _load_json(args.balfrin_access_json)
        inventory = _load_json(args.inventory_json)
        report = build_report(
            access_report=access_report,
            inventory=inventory,
            local_run_root=args.local_run_root,
            run_root=args.run_root,
            remote_repo_root=args.remote_repo_root,
            ssh_target=args.ssh_target,
            connect_timeout=args.connect_timeout,
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"balfrin target-area spatial artifact recovery error: {exc}", file=sys.stderr)
        return 2

    materialize_artifacts(
        report,
        json_output=args.json_output,
        text_output=args.text_output,
        artifact_dir=args.artifact_dir,
    )
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text_report(report))
    return 2 if report["report_status"] in {STATUS_BLOCKED_ACCESS, STATUS_COLLECTION_FAILED} else 0


if __name__ == "__main__":
    raise SystemExit(main())
