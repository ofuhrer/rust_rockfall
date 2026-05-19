#!/usr/bin/env python3
"""Audit preserved Balfrin run-root output-budget compliance.

This helper is read-only. It inspects files already present under a Balfrin run
root and classifies them against the explicit output/reducer budget contract
without submitting work, mutating remote state, or upgrading scientific claims.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import generate_balfrin_multi_release_zone_demo_handoff as handoff  # noqa: E402


SCHEMA_VERSION = "balfrin_run_root_output_budget_audit_v1"
DEFAULT_BUDGET_PROFILE_ID = handoff.SMALLEST_LIVE_BUDGET_PROFILE_ID
REPORT_BASENAME = "balfrin_run_root_output_budget_audit_v1"

CLAIM_BOUNDARIES = {
    "operational_claims_allowed": False,
    "physical_probability_claims_allowed": False,
    "annual_frequency_claims_allowed": False,
    "risk_exposure_vulnerability_claims_allowed": False,
    "scale_up_authorized": False,
    "distributed_execution_authorized": False,
    "live_submission_authorized": False,
}

REPLAY_HASH_INPUTS = {
    "probe_manifest_sha256": "probe_manifest",
    "command_plan_sha256": "command_plan",
    "output_manifest_sha256": "output_manifest",
}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-root", type=Path, required=True, help="Preserved Balfrin run root to audit.")
    parser.add_argument(
        "--budget-profile-id",
        default=DEFAULT_BUDGET_PROFILE_ID,
        help="Budget profile id from output_budget_acceptance_thresholds.",
    )
    parser.add_argument("--json-output", type=Path, default=None)
    parser.add_argument("--text-output", type=Path, default=None)
    parser.add_argument("--format", choices=("json", "text"), default="text")
    return parser.parse_args(argv)


def _load_json(path: Path | None) -> dict[str, Any] | None:
    if path is None or not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _safe_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _file_entry(path: Path) -> dict[str, Any]:
    if not path.exists() or not path.is_file():
        return {
            "path": str(path),
            "exists": False,
            "bytes": None,
            "sha256": None,
        }
    return {
        "path": str(path),
        "exists": True,
        "bytes": path.stat().st_size,
        "sha256": _sha256_file(path),
    }


def _command_output_dir(command_plan: dict[str, Any], *, run_root: Path) -> Path:
    commands = command_plan.get("commands")
    if not isinstance(commands, list):
        return run_root / "output"
    for entry in commands:
        if not isinstance(entry, dict) or entry.get("name") != "build_conditional_hazard_layers":
            continue
        command = entry.get("command")
        if not isinstance(command, list):
            continue
        cwd = Path(str(entry.get("cwd") or run_root)).expanduser()
        if not cwd.is_absolute():
            cwd = run_root / cwd
        tokens = [str(token) for token in command]
        for index, token in enumerate(tokens):
            if token == "--output-dir" and index + 1 < len(tokens):
                output_dir = Path(tokens[index + 1]).expanduser()
                return output_dir if output_dir.is_absolute() else (cwd / output_dir).resolve()
    return run_root / "output"


def _find_output_manifest(output_root: Path) -> Path | None:
    if not output_root.exists():
        return None
    candidates = sorted(output_root.glob("*_manifest.json"))
    preferred = [path for path in candidates if path.name.startswith("validation_")]
    return preferred[0] if preferred else (candidates[0] if candidates else None)


def _resolve_manifest_path(output_manifest: Path, value: Any) -> Path | None:
    if not isinstance(value, str) or not value:
        return None
    path = Path(value).expanduser()
    if path.is_absolute():
        return path
    direct = (output_manifest.parent / path).resolve()
    if direct.exists():
        return direct
    parts = path.parts
    if parts and parts[0] == output_manifest.parent.name:
        trimmed = (output_manifest.parent / Path(*parts[1:])).resolve()
        if trimmed.exists():
            return trimmed
    return direct


def _declared_outputs(output_manifest: Path | None, manifest: dict[str, Any] | None) -> list[dict[str, Any]]:
    outputs = manifest.get("outputs") if isinstance(manifest, dict) else None
    if not isinstance(outputs, list) or output_manifest is None:
        return []
    declared: list[dict[str, Any]] = []
    for entry in outputs:
        if not isinstance(entry, dict):
            continue
        family = entry.get("kind")
        path = _resolve_manifest_path(output_manifest, entry.get("path"))
        if not isinstance(family, str) or path is None:
            continue
        file_info = _file_entry(path)
        declared.append(
            {
                "family": family,
                "path": str(path),
                "exists": file_info["exists"],
                "bytes": file_info["bytes"],
                "sha256": file_info["sha256"],
            }
        )
    return declared


def _family_summary(declared_outputs: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    summaries: dict[str, dict[str, Any]] = {}
    for entry in declared_outputs:
        family = str(entry["family"])
        summary = summaries.setdefault(family, {"file_count": 0, "bytes": 0, "missing_paths": [], "paths": []})
        summary["paths"].append(entry["path"])
        if entry.get("exists"):
            summary["file_count"] += 1
            summary["bytes"] += int(entry.get("bytes") or 0)
        else:
            summary["missing_paths"].append(entry["path"])
    return summaries


def _tree_stats(root: Path) -> dict[str, Any]:
    if not root.exists():
        return {"path": str(root), "exists": False, "file_count": 0, "bytes": 0}
    file_count = 0
    byte_count = 0
    for path in sorted(candidate for candidate in root.rglob("*") if candidate.is_file()):
        file_count += 1
        byte_count += path.stat().st_size
    return {"path": str(root), "exists": True, "file_count": file_count, "bytes": byte_count}


def _manifest_stats(output_root: Path, output_manifest: Path | None) -> dict[str, Any]:
    manifest_paths = sorted(path for path in output_root.rglob("*manifest*.json") if path.is_file()) if output_root.exists() else []
    return {
        "output_manifest": _file_entry(output_manifest) if output_manifest is not None else None,
        "manifest_file_count": len(manifest_paths),
        "manifest_bytes": sum(path.stat().st_size for path in manifest_paths),
        "manifest_paths": [str(path) for path in manifest_paths],
    }


def _sidecar_stats(
    output_root: Path,
    output_manifest: Path | None,
    declared_outputs: list[dict[str, Any]],
) -> dict[str, Any]:
    if not output_root.exists():
        return {"sidecar_file_count": 0, "sidecar_bytes": 0, "sidecar_paths": []}
    package_manifest_paths = {
        str(Path(entry["path"]).resolve())
        for entry in declared_outputs
        if entry.get("family") in {"map_package_manifest", "pilot_gis_package_manifest"}
    }
    sidecars = [
        path
        for path in sorted(output_root.rglob("*.json"))
        if path.is_file() and (output_manifest is None or path.resolve() != output_manifest.resolve())
        and str(path.resolve()) not in package_manifest_paths
    ]
    return {
        "sidecar_file_count": len(sidecars),
        "sidecar_bytes": sum(path.stat().st_size for path in sidecars),
        "sidecar_paths": [str(path) for path in sidecars],
    }


def _reducer_chunk_stats(output_root: Path) -> dict[str, Any]:
    reducer_root = output_root / "chunks"
    chunk_paths = sorted(reducer_root.glob("*manifest*.json")) if reducer_root.exists() else []
    return {
        "reducer_chunk_count": len(chunk_paths),
        "reducer_manifest_file_count": len(chunk_paths),
        "reducer_manifest_bytes": sum(path.stat().st_size for path in chunk_paths),
        "reducer_manifest_paths": [str(path) for path in chunk_paths],
    }


def _probe_manifest_path(command_plan: dict[str, Any], *, run_root: Path) -> Path | None:
    value = command_plan.get("input")
    if not isinstance(value, str) or not value:
        return None
    path = Path(value).expanduser()
    if path.is_absolute():
        return path
    direct = (run_root / path).resolve()
    if direct.exists():
        return direct
    return (Path.cwd() / path).resolve()


def _hashes(
    *,
    command_plan_path: Path,
    probe_manifest_path: Path | None,
    output_manifest: Path | None,
) -> dict[str, dict[str, Any]]:
    return {
        "command_plan_sha256": _file_entry(command_plan_path),
        "probe_manifest_sha256": _file_entry(probe_manifest_path) if probe_manifest_path is not None else None,
        "output_manifest_sha256": _file_entry(output_manifest) if output_manifest is not None else None,
    }


def _missing_required_hashes(hash_entries: dict[str, dict[str, Any] | None], profile: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    for key in profile.get("required_package_hashes") or []:
        entry = hash_entries.get(str(key))
        if not isinstance(entry, dict) or not entry.get("exists") or not isinstance(entry.get("sha256"), str):
            missing.append(str(key))
    return missing


def _projection(
    *,
    manifest_stats: dict[str, Any],
    sidecar_stats: dict[str, Any],
    reducer_stats: dict[str, Any],
    output_root_stats: dict[str, Any],
    family_summaries: dict[str, dict[str, Any]],
    hash_entries: dict[str, dict[str, Any] | None],
    profile: dict[str, Any],
) -> dict[str, Any]:
    family_counts = {family: int(summary["file_count"]) for family, summary in family_summaries.items()}
    family_bytes = {family: int(summary["bytes"]) for family, summary in family_summaries.items()}
    retained = [
        family
        for family in profile.get("required_replay_critical_families") or []
        if family_counts.get(str(family), 0) > 0
    ]
    projection_hashes = {
        key: entry.get("sha256")
        for key, entry in hash_entries.items()
        if isinstance(entry, dict) and isinstance(entry.get("sha256"), str)
    }
    return {
        "manifest_size_bytes": int(manifest_stats["manifest_bytes"]),
        "output_file_count": int(output_root_stats["file_count"]),
        "output_byte_count": int(output_root_stats["bytes"]),
        "sidecar_file_count": int(sidecar_stats["sidecar_file_count"]),
        "sidecar_byte_count": int(sidecar_stats["sidecar_bytes"]),
        "reducer_manifest_file_count": int(reducer_stats["reducer_manifest_file_count"]),
        "reducer_manifest_bytes": int(reducer_stats["reducer_manifest_bytes"]),
        "reducer_chunk_count": int(reducer_stats["reducer_chunk_count"]),
        "output_family_file_counts": family_counts,
        "output_family_bytes": family_bytes,
        "replay_critical_retained_output_families": retained,
        "projection_file_hashes": projection_hashes,
        "release_zone_count": int(profile.get("release_zone_count") or 2),
        "scenario_count": int(profile.get("scenario_count") or 2),
    }


def _budget_report(projection: dict[str, Any], *, profile_id: str) -> dict[str, Any]:
    thresholds = handoff.build_output_budget_acceptance_thresholds()
    profile = dict(thresholds.get("profiles", {}).get(profile_id) or {})
    if not profile:
        return {
            "schema_version": thresholds.get("schema_version"),
            "status": "blocked_unknown_budget_profile",
            "threshold_profile_id": profile_id,
            "threshold_profile": {},
            "failures": [{"metric": "budget_profile_id", "reason": f"unknown budget profile: {profile_id}"}],
            "exceeded_thresholds": ["budget_profile_id"],
            "compressible_excesses": [],
            "replay_critical_excesses": [],
            "summary": f"unknown budget profile: {profile_id}",
        }
    return handoff.validate_output_budget_acceptance(projection=projection, thresholds=thresholds)


def _audit_status(
    *,
    run_root: Path,
    command_plan_path: Path,
    output_root: Path,
    output_manifest: Path | None,
    declared_outputs: list[dict[str, Any]],
    missing_required_hashes: list[str],
    budget_report: dict[str, Any],
) -> tuple[str, list[str]]:
    blockers: list[str] = []
    if not run_root.exists():
        return "blocked_missing_run_root", [f"run root does not exist: {run_root}"]
    if not command_plan_path.exists():
        blockers.append("missing command_plan.json")
    if not output_root.exists():
        blockers.append("missing output root")
    if output_manifest is None:
        blockers.append("missing output manifest")
    missing_declared = [entry["path"] for entry in declared_outputs if not entry.get("exists")]
    if missing_declared:
        blockers.append("missing declared output paths: " + ", ".join(missing_declared))
    if missing_required_hashes:
        blockers.append("missing required replay hashes: " + ", ".join(missing_required_hashes))
    if budget_report.get("status") != "accepted":
        blockers.append(str(budget_report.get("summary") or "output budget was not accepted"))
    if not blockers:
        return "compliant", []
    if missing_required_hashes or any("missing declared" in blocker for blocker in blockers):
        return "blocked_missing_replay_artifacts", blockers
    if budget_report.get("status") != "accepted":
        return "blocked_budget_exceeded", blockers
    return "blocked_incomplete", blockers


def build_report(run_root: Path, *, budget_profile_id: str = DEFAULT_BUDGET_PROFILE_ID) -> dict[str, Any]:
    run_root = run_root.resolve()
    command_plan_path = run_root / "command_plan.json"
    command_plan = _load_json(command_plan_path) or {}
    output_root = _command_output_dir(command_plan, run_root=run_root)
    output_manifest = _find_output_manifest(output_root)
    manifest = _load_json(output_manifest) if output_manifest is not None else None
    declared = _declared_outputs(output_manifest, manifest)
    family_summaries = _family_summary(declared)
    manifest_summary = _manifest_stats(output_root, output_manifest)
    sidecar_summary = _sidecar_stats(output_root, output_manifest, declared)
    reducer_summary = _reducer_chunk_stats(output_root)
    output_root_summary = _tree_stats(output_root)
    thresholds = handoff.build_output_budget_acceptance_thresholds()
    profile = dict(thresholds.get("profiles", {}).get(budget_profile_id) or {})
    probe_manifest = _probe_manifest_path(command_plan, run_root=run_root)
    hash_entries = _hashes(
        command_plan_path=command_plan_path,
        probe_manifest_path=probe_manifest,
        output_manifest=output_manifest,
    )
    missing_hashes = _missing_required_hashes(hash_entries, profile)
    projection = _projection(
        manifest_stats=manifest_summary,
        sidecar_stats=sidecar_summary,
        reducer_stats=reducer_summary,
        output_root_stats=output_root_summary,
        family_summaries=family_summaries,
        hash_entries=hash_entries,
        profile=profile or {"release_zone_count": 2, "scenario_count": 2},
    )
    budget = _budget_report(projection, profile_id=budget_profile_id)
    status, blockers = _audit_status(
        run_root=run_root,
        command_plan_path=command_plan_path,
        output_root=output_root,
        output_manifest=output_manifest,
        declared_outputs=declared,
        missing_required_hashes=missing_hashes,
        budget_report=budget,
    )
    report = {
        "schema_version": SCHEMA_VERSION,
        "audit_status": status,
        "budget_status": status,
        "read_only": True,
        "run_root": str(run_root),
        "output_root": str(output_root),
        "budget_profile_id": budget_profile_id,
        "budget_profile": profile,
        "per_family": family_summaries,
        "declared_outputs": declared,
        "output_root_totals": output_root_summary,
        "manifest_pressure": manifest_summary,
        "sidecar_pressure": sidecar_summary,
        "reducer_pressure": reducer_summary,
        "hashes": hash_entries,
        "missing_required_hashes": missing_hashes,
        "missing_replay_critical_artifacts": [
            family
            for family in profile.get("required_replay_critical_families", [])
            if projection["output_family_file_counts"].get(str(family), 0) == 0
        ],
        "projection": projection,
        "budget_acceptance": budget,
        "blocked_reasons": blockers,
        "claim_boundaries": CLAIM_BOUNDARIES,
    }
    report["summary"] = summarize_report(report)
    return report


def summarize_report(report: dict[str, Any]) -> str:
    projection = report.get("projection", {}) if isinstance(report, dict) else {}
    return (
        "Balfrin run-root output budget audit "
        f"{report.get('audit_status', 'unknown')}: "
        f"{projection.get('output_file_count', 0)} output files, "
        f"{projection.get('manifest_size_bytes', 0)} manifest bytes, "
        f"{projection.get('sidecar_file_count', 0)} sidecars, "
        f"{projection.get('reducer_chunk_count', 0)} reducer chunks, "
        f"{len(report.get('missing_replay_critical_artifacts', []))} missing replay-critical families, "
        f"{len(report.get('missing_required_hashes', []))} missing required hashes."
    )


def render_text_report(report: dict[str, Any]) -> str:
    lines = [
        "Balfrin Run-Root Output Budget Audit",
        f"schema_version: {report.get('schema_version')}",
        f"audit_status: {report.get('audit_status')}",
        f"budget_profile_id: {report.get('budget_profile_id')}",
        f"run_root: {report.get('run_root')}",
        f"output_root: {report.get('output_root')}",
        f"summary: {report.get('summary')}",
        "projection:",
    ]
    projection = report.get("projection", {})
    for key in (
        "output_file_count",
        "output_byte_count",
        "manifest_size_bytes",
        "sidecar_file_count",
        "sidecar_byte_count",
        "reducer_manifest_file_count",
        "reducer_manifest_bytes",
        "reducer_chunk_count",
    ):
        lines.append(f"  {key}: {projection.get(key)}")
    lines.append("per_family:")
    for family, summary in sorted((report.get("per_family") or {}).items()):
        lines.append(f"  {family}: files={summary.get('file_count')} bytes={summary.get('bytes')}")
    if report.get("blocked_reasons"):
        lines.append("blocked_reasons:")
        for reason in report.get("blocked_reasons", []):
            lines.append(f"  - {reason}")
    lines.append("missing_replay_critical_artifacts:")
    for family in report.get("missing_replay_critical_artifacts", []):
        lines.append(f"  - {family}")
    lines.append("missing_required_hashes:")
    for key in report.get("missing_required_hashes", []):
        lines.append(f"  - {key}")
    return "\n".join(lines)


def materialize_artifacts(
    report: dict[str, Any],
    *,
    json_output: Path | None = None,
    text_output: Path | None = None,
) -> None:
    if json_output is not None:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if text_output is not None:
        text_output.parent.mkdir(parents=True, exist_ok=True)
        text_output.write_text(render_text_report(report) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        report = build_report(args.run_root, budget_profile_id=args.budget_profile_id)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"balfrin run-root output budget audit error: {exc}", file=sys.stderr)
        return 2
    materialize_artifacts(report, json_output=args.json_output, text_output=args.text_output)
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text_report(report))
    return 0 if report["audit_status"] == "compliant" else 2


if __name__ == "__main__":
    raise SystemExit(main())
