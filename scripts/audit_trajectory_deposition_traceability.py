#!/usr/bin/env python3
"""Audit traceability from deposition hazard layers to validation outputs.

The audit is read-only. It connects a hazard `deposition_density` layer to the
validation deposition and trajectory outputs that produced it, and reports
missing or inconsistent local evidence without making a validation, calibration,
or operational claim.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_VALIDATION_MANIFEST = (
    ROOT
    / "validation/private/tschamut_public_pilot/target_gate_v1/validation_tschamut_public_target_gate_v1_manifest.json"
)
DEFAULT_HAZARD_MANIFEST = (
    ROOT
    / "hazard/results/tschamut_public_pilot/target_gate_v1/validation_tschamut_public_target_gate_v1_manifest.json"
)
SCHEMA_VERSION = "trajectory_deposition_traceability_audit_v1"


class TraceabilityAuditError(ValueError):
    """User-facing traceability audit error."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validation-manifest", type=Path, default=DEFAULT_VALIDATION_MANIFEST)
    parser.add_argument("--hazard-manifest", type=Path, default=DEFAULT_HAZARD_MANIFEST)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    args = parser.parse_args(argv)

    try:
        report = build_report(args.validation_manifest, args.hazard_manifest)
    except TraceabilityAuditError as exc:
        print(f"trajectory deposition traceability audit error: {exc}")
        return 2

    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text_report(report))
    return 0 if report["audit_status"] == "traceable" else 2


def build_report(
    validation_manifest_path: Path = DEFAULT_VALIDATION_MANIFEST,
    hazard_manifest_path: Path = DEFAULT_HAZARD_MANIFEST,
) -> dict[str, Any]:
    validation_manifest_path = validation_manifest_path.resolve()
    hazard_manifest_path = hazard_manifest_path.resolve()
    validation_manifest = load_manifest(validation_manifest_path)
    hazard_manifest = load_manifest(hazard_manifest_path)

    validation_outputs = {entry.get("kind"): entry for entry in validation_manifest.get("outputs") or []}
    hazard_outputs = hazard_manifest.get("outputs") or []
    deposition_layer = find_hazard_layer(hazard_outputs, "deposition_density")
    weighted_deposition_layer = find_hazard_layer(hazard_outputs, "weighted_deposition_density", required=False)

    ensemble_deposition = validation_outputs.get("ensemble_deposition")
    trajectory = validation_outputs.get("trajectory")
    ensemble_trajectories = validation_outputs.get("ensemble_trajectories")
    hazard_inputs = hazard_manifest.get("inputs") or {}

    checks = [
        output_check("validation_ensemble_deposition", ensemble_deposition),
        output_check("validation_single_trajectory", trajectory),
        output_check("validation_ensemble_trajectories", ensemble_trajectories),
        output_check("hazard_deposition_density_layer", deposition_layer),
    ]
    if weighted_deposition_layer is not None:
        checks.append(output_check("hazard_weighted_deposition_density_layer", weighted_deposition_layer))

    deposition_rows = row_count(ensemble_deposition)
    single_trajectory_rows = row_count(trajectory)
    ensemble_trajectory_rows = row_count(ensemble_trajectories)
    hazard_deposition_points = hazard_inputs.get("deposition_point_count")
    hazard_trajectory_samples = hazard_inputs.get("trajectory_sample_count")
    expected_trajectory_samples = (
        single_trajectory_rows + ensemble_trajectory_rows
        if single_trajectory_rows is not None and ensemble_trajectory_rows is not None
        else None
    )

    consistency_checks = [
        {
            "check_id": "deposition_rows_match_hazard_input",
            "status": "pass" if deposition_rows == hazard_deposition_points and deposition_rows is not None else "fail",
            "validation_row_count": deposition_rows,
            "hazard_input_count": hazard_deposition_points,
        },
        {
            "check_id": "trajectory_rows_match_hazard_input",
            "status": (
                "pass"
                if expected_trajectory_samples == hazard_trajectory_samples and expected_trajectory_samples is not None
                else "fail"
            ),
            "single_trajectory_rows": single_trajectory_rows,
            "ensemble_trajectory_rows": ensemble_trajectory_rows,
            "expected_trajectory_sample_count": expected_trajectory_samples,
            "hazard_input_count": hazard_trajectory_samples,
        },
    ]

    failures = [
        check["check_id"]
        for check in [*checks, *consistency_checks]
        if check["status"] != "pass"
    ]
    audit_status = "traceable" if not failures else "blocked_missing_traceability"

    return {
        "schema_version": SCHEMA_VERSION,
        "validation_manifest_path": str(validation_manifest_path),
        "hazard_manifest_path": str(hazard_manifest_path),
        "case_id": hazard_manifest.get("case_id") or validation_manifest.get("case_id"),
        "audit_status": audit_status,
        "output_checks": checks,
        "consistency_checks": consistency_checks,
        "traceability_summary": {
            "deposition_layer_path": deposition_layer.get("path") if deposition_layer else None,
            "weighted_deposition_layer_path": weighted_deposition_layer.get("path") if weighted_deposition_layer else None,
            "validation_deposition_path": ensemble_deposition.get("path") if isinstance(ensemble_deposition, dict) else None,
            "validation_trajectory_path": trajectory.get("path") if isinstance(trajectory, dict) else None,
            "validation_ensemble_trajectories_path": (
                ensemble_trajectories.get("path") if isinstance(ensemble_trajectories, dict) else None
            ),
        },
        "claim_boundaries": {
            "field_validation_claim_added": False,
            "calibration_claim_added": False,
            "operational_map_claim_added": False,
            "physical_probability_claim_added": False,
            "balfrin_required": False,
        },
        "missing_or_failed_checks": failures,
        "next_local_follow_up": next_follow_up(audit_status, failures),
    }


def load_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise TraceabilityAuditError(f"manifest does not exist: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def find_hazard_layer(outputs: list[dict[str, Any]], layer_name: str, *, required: bool = True) -> dict[str, Any] | None:
    for entry in outputs:
        if entry.get("kind") == "hazard_layer" and entry.get("layer_name") == layer_name:
            return entry
    if required:
        return None
    return None


def output_check(check_id: str, entry: Any) -> dict[str, Any]:
    if not isinstance(entry, dict):
        return {"check_id": check_id, "status": "missing", "path": None, "row_count": None}
    path = ROOT / entry.get("path", "")
    status = "pass" if path.exists() and int(entry.get("file_count") or 0) > 0 else "missing"
    return {
        "check_id": check_id,
        "status": status,
        "path": entry.get("path"),
        "row_count": entry.get("row_count"),
        "file_count": entry.get("file_count"),
        "total_bytes": entry.get("total_bytes"),
        "sha256": entry.get("sha256"),
    }


def row_count(entry: Any) -> int | None:
    if not isinstance(entry, dict) or not isinstance(entry.get("row_count"), int):
        return None
    return int(entry["row_count"])


def next_follow_up(audit_status: str, failures: list[str]) -> str:
    if audit_status == "traceable":
        return "Use this traceability audit before interpreting deposition-density diagnostics; next local task is hazard-layer fragility ranking."
    return "Regenerate or repair the missing validation/hazard output families before interpreting deposition-density diagnostics: " + ", ".join(failures)


def render_text_report(report: dict[str, Any]) -> str:
    lines = [
        f"schema_version: {report['schema_version']}",
        f"audit_status: {report['audit_status']}",
        f"case_id: {report['case_id']}",
        "traceability_summary:",
    ]
    for key, value in report["traceability_summary"].items():
        lines.append(f"  {key}: {value}")
    lines.append("consistency_checks:")
    for check in report["consistency_checks"]:
        lines.append(f"  {check['check_id']}: {check['status']}")
    lines.append("claim_boundaries:")
    for key, value in report["claim_boundaries"].items():
        lines.append(f"  {key}: {value}")
    lines.append(f"next_local_follow_up: {report['next_local_follow_up']}")
    return "\n".join(lines)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
