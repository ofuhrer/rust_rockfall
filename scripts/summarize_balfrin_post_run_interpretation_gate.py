#!/usr/bin/env python3
"""Summarize the Balfrin post-run interpretation gate.

This helper is read-only. It accepts a post-run evidence bundle, classifies
the Balfrin single-release-zone pilot as measured, inconclusive, or blocked,
and keeps the conditional-diagnostic boundary explicit. It does not authorize
operational use, physical-probability claims, annual-frequency claims, or
scale-up.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "balfrin_post_run_interpretation_gate_v1"
DEFAULT_PILOT_ID = "tschamut_public_pilot"
DEFAULT_RUN_ID = "tschamut_public_balfrin_single_release_zone_v1"
DEFAULT_CONTRACT = ROOT / "validation/pilot_runs/tschamut_public_balfrin_single_release_zone_pilot_contract_v1.yaml"

READINESS_READY_STATUSES = {"ready_for_balfrin_single_release_zone_pilot", "ready"}
READINESS_INCONCLUSIVE_STATUSES = {"ready_with_scope_limits", "ready_with_notes"}
CONVERGENCE_MEASURED_STATUSES = {"measured", "measured_existing_artifacts", "pass"}
CONVERGENCE_INCONCLUSIVE_STATUSES = {"inconclusive", "defer", "deferred"}
OUTPUT_MEASURED_STATUSES = {"measured", "rebuildable_reduced_output", "bounded_reduced_output"}
OUTPUT_INCONCLUSIVE_STATUSES = {"summary_only_not_rebuildable", "inconclusive", "deferred"}
GIS_MEASURED_STATUSES = {"gis_package_ready", "cog_package_ready"}
GIS_INCONCLUSIVE_STATUSES = {"gis_package_ready_cog_blocked", "metadata_only", "cog_package_ready_with_scope_delta"}


class BalfrinPostRunInterpretationGateError(ValueError):
    """User-facing gate-summary error."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("json", "text"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    parser.add_argument(
        "--evidence-json",
        type=Path,
        default=None,
        help="optional override JSON file for tests or alternate post-run evidence snapshots",
    )
    args = parser.parse_args(argv)

    try:
        report = build_report(load_evidence_override(args.evidence_json))
    except BalfrinPostRunInterpretationGateError as exc:
        print(f"balfrin post-run interpretation gate error: {exc}", file=sys.stderr)
        return 2

    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text_report(report))
    return 0 if report["interpretation_status"] != "blocked_missing_inputs" else 2


def load_evidence_override(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    if not path.exists():
        raise BalfrinPostRunInterpretationGateError(f"evidence override file is missing: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise BalfrinPostRunInterpretationGateError("evidence override must be a JSON object")
    return data


def build_report(evidence_override: dict[str, Any] | None = None) -> dict[str, Any]:
    if evidence_override is None:
        return blocked_report(["post_run_evidence_bundle"], reason="no post-run evidence bundle was provided")
    if evidence_override.get("missing_inputs"):
        missing_inputs = [str(item) for item in evidence_override.get("missing_inputs", [])]
        return blocked_report(missing_inputs, reason="required post-run evidence inputs are missing")
    if isinstance(evidence_override.get("post_run_interpretation_gate_report"), dict):
        return dict(evidence_override["post_run_interpretation_gate_report"])

    pilot_id = str(evidence_override.get("pilot_id") or DEFAULT_PILOT_ID)
    run_id = str(evidence_override.get("run_id") or DEFAULT_RUN_ID)
    contract_path = Path(str(evidence_override.get("contract_path") or DEFAULT_CONTRACT))
    required_checks = build_required_checks(evidence_override)
    blocked_checks = [check["name"] for check in required_checks if check["status"] == "blocked_missing_inputs" and check["required"]]
    if blocked_checks:
        return blocked_report(
            [f"check:{name}" for name in blocked_checks],
            reason="required post-run evidence inputs are missing",
            pilot_id=pilot_id,
            run_id=run_id,
            contract_path=contract_path,
            required_checks=required_checks,
        )

    interpretation_status = derive_interpretation_status(required_checks)
    acceptance_status = (
        "accepted_conditional_diagnostic"
        if interpretation_status != "blocked_missing_inputs"
        else "blocked_missing_inputs"
    )
    report = {
        "schema_version": SCHEMA_VERSION,
        "pilot_id": pilot_id,
        "run_id": run_id,
        "contract_path": str(contract_path),
        "interpretation_status": interpretation_status,
        "artifact_acceptance_status": acceptance_status,
        "usable_as_conditional_diagnostic_artifact": acceptance_status == "accepted_conditional_diagnostic",
        "required_checks": required_checks,
        "readiness_check": find_check(required_checks, "readiness"),
        "convergence_stability_check": find_check(required_checks, "convergence_stability"),
        "output_check": find_check(required_checks, "output"),
        "gis_cog_check": find_check(required_checks, "gis_cog"),
        "physical_credibility_check": find_check(required_checks, "physical_credibility"),
        "required_readiness": summarize_check(find_check(required_checks, "readiness")),
        "required_convergence_stability": summarize_check(find_check(required_checks, "convergence_stability")),
        "required_output": summarize_check(find_check(required_checks, "output")),
        "required_gis_cog": summarize_check(find_check(required_checks, "gis_cog")),
        "required_physical_credibility": summarize_check(find_check(required_checks, "physical_credibility")),
        "claim_boundaries": claim_boundaries(),
        "evidence_sources": evidence_sources(),
        "blocked_reason": "none",
        "operational_claims_allowed": False,
        "physical_probability_claims_allowed": False,
        "annual_frequency_claims_allowed": False,
        "risk_exposure_vulnerability_claims_allowed": False,
        "scale_up_authorized": False,
    }
    return report


def blocked_report(
    missing_inputs: list[str],
    *,
    reason: str,
    pilot_id: str = DEFAULT_PILOT_ID,
    run_id: str = DEFAULT_RUN_ID,
    contract_path: Path = DEFAULT_CONTRACT,
    required_checks: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    checks = required_checks or build_required_checks({"missing_inputs": missing_inputs})
    return {
        "schema_version": SCHEMA_VERSION,
        "pilot_id": pilot_id,
        "run_id": run_id,
        "contract_path": str(contract_path),
        "interpretation_status": "blocked_missing_inputs",
        "artifact_acceptance_status": "blocked_missing_inputs",
        "usable_as_conditional_diagnostic_artifact": False,
        "required_checks": checks,
        "readiness_check": find_check(checks, "readiness"),
        "convergence_stability_check": find_check(checks, "convergence_stability"),
        "output_check": find_check(checks, "output"),
        "gis_cog_check": find_check(checks, "gis_cog"),
        "physical_credibility_check": find_check(checks, "physical_credibility"),
        "required_readiness": summarize_check(find_check(checks, "readiness")),
        "required_convergence_stability": summarize_check(find_check(checks, "convergence_stability")),
        "required_output": summarize_check(find_check(checks, "output")),
        "required_gis_cog": summarize_check(find_check(checks, "gis_cog")),
        "required_physical_credibility": summarize_check(find_check(checks, "physical_credibility")),
        "claim_boundaries": claim_boundaries(),
        "evidence_sources": evidence_sources(),
        "missing_inputs": missing_inputs,
        "blocked_reason": reason,
        "operational_claims_allowed": False,
        "physical_probability_claims_allowed": False,
        "annual_frequency_claims_allowed": False,
        "risk_exposure_vulnerability_claims_allowed": False,
        "scale_up_authorized": False,
    }


def build_required_checks(evidence: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        build_readiness_check(evidence),
        build_convergence_stability_check(evidence),
        build_output_check(evidence),
        build_gis_cog_check(evidence),
        build_physical_credibility_check(evidence),
    ]


def build_readiness_check(evidence: dict[str, Any]) -> dict[str, Any]:
    section = section_for(evidence, "readiness", "readiness_check", "readiness_status")
    status = str(section.get("status") or "").strip()
    if not status:
        status = "blocked_missing_inputs"
    if status in READINESS_READY_STATUSES:
        normalized = "measured"
    elif status in READINESS_INCONCLUSIVE_STATUSES:
        normalized = "inconclusive"
    elif status.startswith("blocked") or status == "missing":
        normalized = "blocked_missing_inputs"
    else:
        normalized = "inconclusive"
    return {
        "name": "readiness",
        "required": True,
        "status": normalized,
        "evidence_status": status,
        "summary": section.get("summary")
        or "Balfrin single-release-zone pilot readiness must be confirmed before the post-run gate can accept the artifact.",
        "blockers": listify(section.get("blockers")),
    }


def build_convergence_stability_check(evidence: dict[str, Any]) -> dict[str, Any]:
    section = section_for(evidence, "convergence_stability", "convergence_stability_check", "convergence_status")
    status = str(section.get("status") or "").strip()
    if not status:
        status = "blocked_missing_inputs"
    if status in CONVERGENCE_MEASURED_STATUSES:
        normalized = "measured"
    elif status in CONVERGENCE_INCONCLUSIVE_STATUSES:
        normalized = "inconclusive"
    elif status.startswith("blocked") or status == "missing":
        normalized = "blocked_missing_inputs"
    else:
        normalized = "inconclusive"
    return {
        "name": "convergence_stability",
        "required": True,
        "status": normalized,
        "evidence_status": status,
        "summary": section.get("summary")
        or "Convergence and stability must be measured well enough to distinguish a usable diagnostic artifact from an unresolved post-run interpretation.",
        "blockers": listify(section.get("blockers")),
    }


def build_output_check(evidence: dict[str, Any]) -> dict[str, Any]:
    section = section_for(evidence, "output", "output_check", "output_status")
    status = str(section.get("status") or "").strip()
    if not status:
        status = "blocked_missing_inputs"
    if status in OUTPUT_MEASURED_STATUSES:
        normalized = "measured"
    elif status in OUTPUT_INCONCLUSIVE_STATUSES:
        normalized = "inconclusive"
    elif status.startswith("blocked") or status == "missing":
        normalized = "blocked_missing_inputs"
    else:
        normalized = "inconclusive"
    return {
        "name": "output",
        "required": True,
        "status": normalized,
        "evidence_status": status,
        "summary": section.get("summary")
        or "Output pressure must remain bounded enough that the diagnostic artifact stays inspectable and reproducible.",
        "blockers": listify(section.get("blockers")),
    }


def build_gis_cog_check(evidence: dict[str, Any]) -> dict[str, Any]:
    section = section_for(evidence, "gis_cog", "gis_cog_check", "gis_cog_status")
    status = str(section.get("status") or "").strip()
    if not status:
        status = "blocked_missing_inputs"
    if status in GIS_MEASURED_STATUSES:
        normalized = "measured"
    elif status in GIS_INCONCLUSIVE_STATUSES:
        normalized = "inconclusive"
    elif status.startswith("blocked") or status == "missing":
        normalized = "blocked_missing_inputs"
    else:
        normalized = "inconclusive"
    return {
        "name": "gis_cog",
        "required": True,
        "status": normalized,
        "evidence_status": status,
        "summary": section.get("summary")
        or "GIS packaging and COG readiness must be explicit so the conditional diagnostic artifact remains reviewable without implying operational release.",
        "blockers": listify(section.get("blockers")),
    }


def build_physical_credibility_check(evidence: dict[str, Any]) -> dict[str, Any]:
    section = section_for(
        evidence,
        "physical_credibility",
        "physical_credibility_check",
        "physical_credibility_status",
    )
    status = str(section.get("status") or "").strip() or "not_established"
    return {
        "name": "physical_credibility",
        "required": True,
        "status": status,
        "evidence_status": status,
        "summary": section.get("summary")
        or "Physical credibility remains unestablished; the gate records this boundary and does not turn it into a physical-probability claim.",
        "blockers": listify(section.get("blockers")),
    }


def derive_interpretation_status(required_checks: list[dict[str, Any]]) -> str:
    required = [check for check in required_checks if check["required"]]
    if any(check["status"] == "blocked_missing_inputs" for check in required):
        return "blocked_missing_inputs"
    if all(check["status"] == "measured" for check in required if check["name"] != "physical_credibility"):
        return "measured_conditional_diagnostic"
    return "inconclusive_conditional_diagnostic"


def summarize_check(check: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": check["name"],
        "status": check["status"],
        "evidence_status": check["evidence_status"],
        "summary": check["summary"],
        "blockers": check["blockers"],
        "required": check["required"],
    }


def find_check(checks: list[dict[str, Any]], name: str) -> dict[str, Any]:
    for check in checks:
        if check["name"] == name:
            return check
    raise BalfrinPostRunInterpretationGateError(f"missing required check: {name}")


def section_for(evidence: dict[str, Any], *keys: str) -> dict[str, Any]:
    for key in keys:
        value = evidence.get(key)
        if isinstance(value, dict):
            return dict(value)
        if isinstance(value, str):
            return {"status": value}
    return {}


def listify(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def claim_boundaries() -> dict[str, Any]:
    return {
        "operational_claims_allowed": False,
        "physical_probability_claims_allowed": False,
        "annual_frequency_claims_allowed": False,
        "risk_exposure_vulnerability_claims_allowed": False,
        "scale_up_authorized": False,
        "distributed_execution_authorized": False,
        "notes": [
            "conditional diagnostics are not operational hazard maps",
            "conditional diagnostics are not physical probabilities",
            "the gate only decides conditional-diagnostic usability",
        ],
    }


def evidence_sources() -> list[str]:
    return [
        "validation/pilot_runs/tschamut_public_balfrin_single_release_zone_pilot_contract_v1.yaml",
        "docs/balfrin_single_job_execution_sufficiency.md",
        "scripts/summarize_balfrin_single_job_execution.py",
        "scripts/summarize_tschamut_conditional_diagnostic_interpretation.py",
        "docs/tschamut_public_conditional_pilot_gate_report.md",
        "docs/balfrin_post_run_interpretation_gate.md",
    ]


def render_text_report(report: dict[str, Any]) -> str:
    lines = [
        "Balfrin Post-Run Interpretation Gate",
        "",
        f"- Interpretation status: `{report['interpretation_status']}`",
        f"- Artifact acceptance status: `{report['artifact_acceptance_status']}`",
        f"- Usable as conditional diagnostic artifact: `{report['usable_as_conditional_diagnostic_artifact']}`",
        f"- Operational claims allowed: `{report['operational_claims_allowed']}`",
        f"- Physical probability claims allowed: `{report['physical_probability_claims_allowed']}`",
        f"- Annual frequency claims allowed: `{report['annual_frequency_claims_allowed']}`",
        f"- Risk/exposure/vulnerability claims allowed: `{report['risk_exposure_vulnerability_claims_allowed']}`",
        f"- Scale-up authorized: `{report['scale_up_authorized']}`",
        "",
        "## Required Checks",
        "",
    ]
    for check in report["required_checks"]:
        lines.extend(
            [
                f"- {check['name']}: `{check['status']}`",
                f"  - evidence status: `{check['evidence_status']}`",
                f"  - summary: {check['summary']}",
            ]
        )
        if check["blockers"]:
            lines.append(f"  - blockers: {', '.join(check['blockers'])}")
    lines.extend(
        [
            "",
            "## Claim Boundaries",
            "",
        ]
    )
    for key, value in report["claim_boundaries"].items():
        if key == "notes":
            continue
        lines.append(f"- {key}: `{value}`")
    lines.append("")
    lines.append("Notes:")
    for note in report["claim_boundaries"].get("notes", []):
        lines.append(f"- {note}")
    if report.get("missing_inputs"):
        lines.extend(["", "## Missing Inputs", ""])
        for item in report["missing_inputs"]:
            lines.append(f"- `{item}`")
    if report.get("blocked_reason") and report["blocked_reason"] != "none":
        lines.extend(["", f"Blocked reason: {report['blocked_reason']}"])
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
