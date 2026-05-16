#!/usr/bin/env python3
"""Summarize Balfrin restartability recovery from a partial-state fixture.

This helper is read-only. It classifies a restartability recovery snapshot as
measured, fixture-proven, or blocked_missing_inputs and keeps the recovery
limits explicit so the report does not overstate what the evidence proves.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "balfrin_restartability_recovery_v1"
DEFAULT_EVIDENCE_JSON = ROOT / "tests/fixtures/balfrin_restartability_recovery/fixture_v1.json"


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
    args = parser.parse_args(argv)

    try:
        report = build_report(load_evidence_override(args.evidence_json))
    except BalfrinRestartabilityRecoveryError as exc:
        print(f"balfrin restartability recovery error: {exc}", file=sys.stderr)
        return 2

    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.text_output is not None:
        args.text_output.parent.mkdir(parents=True, exist_ok=True)
        args.text_output.write_text(render_text_report(report), encoding="utf-8")

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text_report(report))
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
        "reused_chunks": reused_chunks,
        "executed_chunks": executed_chunks,
        "reused_chunk_counts": as_mapping(recovery_outcome.get("reused_chunk_counts")),
        "executed_chunk_counts": as_mapping(recovery_outcome.get("executed_chunk_counts")),
        "numerical_artifact_stability": {
            "classification": str(numerical_artifacts.get("classification") or "unknown"),
            "changed_artifact_count": safe_int(numerical_artifacts.get("changed_artifact_count")),
            "changed_paths": list_of_strings(numerical_artifacts.get("changed_paths")),
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
    if not report["explicit_limits"]:
        report["explicit_limits"] = [
            "fixture-backed recovery evidence only; no live interruption is claimed here.",
            "no distributed execution authorization is implied.",
            "no physics, sampling, or output-profile changes are introduced by this report.",
        ]
    return report


def blocked_report(missing_inputs: list[str], *, reason: str) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "pilot_id": "tschamut_public_pilot",
        "run_id": "tschamut_public_balfrin_restartability_recovery_v1",
        "recovery_status": "blocked_missing_inputs",
        "evidence_status": "blocked_missing_inputs",
        "partial_state": {},
        "resume_commands": [],
        "reused_chunks": [],
        "executed_chunks": [],
        "reused_chunk_counts": {},
        "executed_chunk_counts": {},
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
    lines.extend(
        [
            "",
            "## Chunk Recovery",
            "",
            f"- Reused chunks: `{report['reused_chunks']}`",
            f"- Executed chunks: `{report['executed_chunks']}`",
            f"- Reused chunk counts: `{report['reused_chunk_counts']}`",
            f"- Executed chunk counts: `{report['executed_chunk_counts']}`",
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
