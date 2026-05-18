#!/usr/bin/env python3
"""Summarize the Balfrin demonstration closure package.

This helper is a fail-closed synthesis layer. It combines the current Balfrin
management package with the metrics-completion rerun package, the
multi-release-zone handoff, the preservation gate, and a new-measured-evidence
gate so reviewers can answer whether the evidence is ready to be extended
toward larger Swiss workflows without rereading the repository.

The package only upgrades when a new preservation-checked measured evidence
record is present. Otherwise it stays blocked and labels the mixed provenance
explicitly.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import generate_balfrin_multi_release_zone_demo_handoff as multi_zone_handoff
from scripts import summarize_balfrin_management_demo_package as management
from scripts import summarize_balfrin_probe_preservation_gate as preservation_gate
from scripts import summarize_balfrin_target_area_metrics_completion_rerun_package as metrics_rerun


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "balfrin_demonstration_closure_package_v1"
REPORT_BASENAME = "balfrin_demonstration_closure_package_v1"
DEFAULT_ARTIFACT_DIR = ROOT / "validation/private/tschamut_public_pilot/balfrin_demonstration_closure_package_v1"
DEFAULT_MANAGEMENT_RUN_ROOT = ROOT / "tests/fixtures/balfrin_probe_metrics_contract/complete_run_root"
DEFAULT_PRESERVATION_RUN_ROOT = DEFAULT_MANAGEMENT_RUN_ROOT
DEFAULT_MANAGEMENT_ARTIFACT_DIR = DEFAULT_ARTIFACT_DIR / "management_demo_package_v1"
DEFAULT_METRICS_RERUN_ARTIFACT_DIR = DEFAULT_ARTIFACT_DIR / "metrics_completion_rerun_package_v1"
DEFAULT_MULTI_ZONE_ARTIFACT_DIR = Path("/tmp/rust_rockfall/balfrin_multi_release_zone_demo_v1")

SECTION_NAMES = (
    "runtime_section",
    "replay_section",
    "preservation_section",
    "restartability_section",
    "reducer_output_scaling_section",
    "aoi_release_scenario_automation_section",
    "gis_readiness_section",
    "second_site_portability_section",
    "scientific_claim_boundaries_section",
    "metrics_completion_rerun_section",
    "new_measured_evidence_section",
)

ALLOWED_EVIDENCE_TYPES = {
    "measured",
    "fixture_backed",
    "dry_run",
    "blocked",
    "unavailable",
    "unauthorized",
    "historical",
}

ALLOWED_MEASURED_EVIDENCE_SOURCES = {
    "metrics_completion_rerun",
    "authorized_multi_zone_probe",
}


class BalfrinDemonstrationClosurePackageError(ValueError):
    """User-facing closure-package error."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-dir", type=Path, default=DEFAULT_ARTIFACT_DIR)
    parser.add_argument("--evidence-json", type=Path, default=None)
    parser.add_argument("--format", choices=("json", "text"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    parser.add_argument("--text-output", type=Path, default=None)
    args = parser.parse_args(argv)

    try:
        report = build_report(
            evidence_override=load_evidence_override(args.evidence_json),
            artifact_dir=args.artifact_dir,
        )
    except BalfrinDemonstrationClosurePackageError as exc:
        print(f"balfrin demonstration closure package error: {exc}", file=sys.stderr)
        return 2

    materialize_artifacts(report, json_output=args.json_output, text_output=args.text_output)

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
    else:
        print(render_text_report(report))
    return 0 if not str(report.get("closure_status") or "").startswith("blocked") else 2


def load_evidence_override(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    if not path.exists():
        raise BalfrinDemonstrationClosurePackageError(f"evidence override file is missing: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise BalfrinDemonstrationClosurePackageError("evidence override must be a JSON object")
    return payload


def build_report(
    evidence_override: dict[str, Any] | None = None,
    *,
    artifact_dir: Path = DEFAULT_ARTIFACT_DIR,
) -> dict[str, Any]:
    if evidence_override is not None and isinstance(evidence_override.get("closure_report"), dict):
        return dict(evidence_override["closure_report"])

    if evidence_override is not None and evidence_override.get("missing_inputs"):
        missing_inputs = [str(item) for item in evidence_override.get("missing_inputs", []) if str(item)]
        return blocked_report(
            missing_inputs,
            reason="required closure-package inputs are missing",
            artifact_dir=artifact_dir,
        )

    report = build_current_report(artifact_dir=artifact_dir)
    if evidence_override is None:
        return report

    apply_overrides(report, evidence_override)
    finalize_report(report)
    return report


def build_current_report(*, artifact_dir: Path = DEFAULT_ARTIFACT_DIR) -> dict[str, Any]:
    management_report = management.build_report(
        run_root=DEFAULT_MANAGEMENT_RUN_ROOT,
        artifact_dir=DEFAULT_MANAGEMENT_ARTIFACT_DIR,
    )
    preservation_report = preservation_gate.build_report(run_root=DEFAULT_PRESERVATION_RUN_ROOT)
    metrics_rerun_report = metrics_rerun.build_report()
    multi_zone_report = multi_zone_handoff.build_report(
        artifact_dir=DEFAULT_MULTI_ZONE_ARTIFACT_DIR,
    )

    report = {
        "schema_version": SCHEMA_VERSION,
        "closure_status": "blocked_no_new_measured_evidence",
        "closure_provenance_status": "blocked_no_new_measured_evidence",
        "maturity_label_update_allowed": False,
        "reviewer_answer": build_reviewer_answer("blocked_no_new_measured_evidence"),
        "package_summary": {
            "status": "blocked_no_new_measured_evidence",
            "summary": (
                "No new preservation-checked measured evidence from a metrics-completion rerun or authorized "
                "multi-zone probe is present, so the closure package remains blocked."
            ),
            "section_counts": {},
        },
        "runtime_section": annotate_section(management_report["runtime_section"], "measured"),
        "replay_section": annotate_section(management_report["replay_section"], "fixture_backed"),
        "preservation_section": annotate_section(
            preservation_report,
            "measured" if preservation_report.get("gate_status") == "ready_for_demonstration_evidence" else "blocked",
            status=str(preservation_report.get("gate_status") or "blocked_missing_inputs"),
        ),
        "restartability_section": annotate_section(management_report["restartability_section"], "measured"),
        "reducer_output_scaling_section": annotate_section(management_report["scaling_section"], "measured"),
        "aoi_release_scenario_automation_section": build_aoi_release_scenario_automation_section(management_report),
        "gis_readiness_section": annotate_section(management_report["gis_scope_section"], "measured"),
        "second_site_portability_section": build_second_site_portability_section(multi_zone_report),
        "scientific_claim_boundaries_section": build_scientific_claim_boundaries_section(management_report),
        "metrics_completion_rerun_section": build_metrics_completion_rerun_section(metrics_rerun_report),
        "new_measured_evidence_section": build_new_measured_evidence_section(),
        "claim_boundaries": dict(management_report.get("claim_boundaries") or {}),
        "source_artifacts": build_source_artifacts(artifact_dir),
        "regeneration_commands": build_regeneration_commands(artifact_dir),
    }
    finalize_report(report)
    return report


def annotate_section(section: dict[str, Any], evidence_type: str, *, status: str | None = None) -> dict[str, Any]:
    payload = copy.deepcopy(section)
    payload["evidence_type"] = evidence_type
    if status is not None:
        payload["status"] = status
    return payload


def build_aoi_release_scenario_automation_section(management_report: dict[str, Any]) -> dict[str, Any]:
    section = {
        "status": str(management_report["target_area_aoi_automation_section"].get("status") or "blocked_missing_inputs"),
        "release_scenario_status": str(
            management_report["target_area_release_scenario_section"].get("status") or "blocked_missing_inputs"
        ),
        "summary": (
            "AOI and release/scenario automation stay dry-run or template-only until a new preservation-checked "
            "measured evidence record exists."
        ),
        "source_paths": [
            *collect_source_paths(management_report["target_area_aoi_automation_section"]),
            *collect_source_paths(management_report["target_area_release_scenario_section"]),
        ],
    }
    return annotate_section(section, "dry_run")


def build_second_site_portability_section(multi_zone_report: dict[str, Any]) -> dict[str, Any]:
    follow_up = dict(multi_zone_report.get("follow_up_recommendation") or {})
    pressure = dict(multi_zone_report.get("pressure_checkpoints") or {})
    section = {
        "status": str(follow_up.get("authorization_classification") or "blocked_pending_authorization"),
        "package_status": str(multi_zone_report.get("package_status") or "blocked_missing_inputs"),
        "summary": (
            "Second-site portability remains unauthorized until the reviewed multi-zone path is backed by new "
            "preservation-checked measured evidence."
        ),
        "authorization_classification": follow_up.get("authorization_classification"),
        "authorization_review_command": follow_up.get("authorization_review_command"),
        "authorization_submit_command": follow_up.get("authorization_submit_command"),
        "pressure_status": pressure.get("output_pressure", {}).get("status"),
        "source_paths": collect_source_paths(multi_zone_report),
    }
    return annotate_section(section, "unauthorized")


def build_scientific_claim_boundaries_section(management_report: dict[str, Any]) -> dict[str, Any]:
    claim_boundaries = dict(management_report.get("claim_boundaries") or {})
    swiss_wide = dict(management_report.get("swiss_wide_extension_section") or {})
    section = {
        "status": "historical_boundary",
        "summary": (
            "Scientific claim boundaries are historical guardrails: the package stays non-operational, non-risk, "
            "non-annual-frequency, and non-scale-up regardless of the closure status."
        ),
        "answer": swiss_wide.get("answer"),
        "claim_boundaries": claim_boundaries,
        "source_paths": [
            "docs/balfrin_single_job_execution_sufficiency.md",
            "docs/current_maturity_snapshot.md",
            "scripts/estimate_swiss_wide_execution_envelope.py",
        ],
    }
    return annotate_section(section, "historical", status="historical_boundary")


def build_metrics_completion_rerun_section(metrics_rerun_report: dict[str, Any]) -> dict[str, Any]:
    section = {
        "status": str(metrics_rerun_report.get("package_status") or "blocked_missing_inputs"),
        "summary": (
            "The metrics-completion rerun package is a dry-run plan until a measured rerun result is supplied."
        ),
        "preservation_checklist_status": metrics_rerun_report.get("preservation_checklist", {}).get("status"),
        "existing_target_area_run_comparison": metrics_rerun_report.get("existing_target_area_run_comparison", {}),
        "source_paths": [
            *collect_source_paths(metrics_rerun_report.get("rerun_command_plan", {})),
            *collect_source_paths(metrics_rerun_report.get("preservation_checklist", {})),
        ],
    }
    return annotate_section(section, "dry_run")


def build_new_measured_evidence_section() -> dict[str, Any]:
    section = {
        "status": "blocked_no_new_measured_evidence",
        "source_type": None,
        "preservation_checked": False,
        "preservation_gate_status": "blocked_no_new_measured_evidence",
        "authorization_status": "blocked_no_new_measured_evidence",
        "summary": (
            "No new preservation-checked measured evidence from a metrics-completion rerun or authorized "
            "multi-zone probe is present."
        ),
        "source_paths": [],
    }
    return annotate_section(section, "blocked")


def collect_source_paths(value: Any) -> list[str]:
    if isinstance(value, dict):
        paths: list[str] = []
        for item in value.values():
            paths.extend(collect_source_paths(item))
        return paths
    if isinstance(value, list):
        return [str(item) for item in value if isinstance(item, str) and item]
    if isinstance(value, str) and value:
        return [value]
    return []


def build_source_artifacts(artifact_dir: Path) -> dict[str, Any]:
    return {
        "closure_artifact_dir": str(artifact_dir),
        "management_artifact_dir": str(artifact_dir / "management_demo_package_v1"),
        "metrics_completion_rerun_artifact_dir": str(artifact_dir / "metrics_completion_rerun_package_v1"),
        "multi_zone_handoff_artifact_dir": str(DEFAULT_MULTI_ZONE_ARTIFACT_DIR),
        "preservation_gate_run_root": str(DEFAULT_PRESERVATION_RUN_ROOT),
        "management_run_root": str(DEFAULT_MANAGEMENT_RUN_ROOT),
    }


def build_regeneration_commands(artifact_dir: Path) -> list[str]:
    return [
        "PYENV_VERSION=system uv run python scripts/summarize_balfrin_probe_preservation_gate.py "
        f"--run-root {DEFAULT_PRESERVATION_RUN_ROOT} --artifact-dir {artifact_dir / 'preservation_gate_v1'}",
        "PYENV_VERSION=system uv run python scripts/summarize_balfrin_target_area_metrics_completion_rerun_package.py "
        f"--artifact-dir {artifact_dir / 'metrics_completion_rerun_package_v1'}",
        "PYENV_VERSION=system uv run python scripts/generate_balfrin_multi_release_zone_demo_handoff.py "
        f"--artifact-dir {DEFAULT_MULTI_ZONE_ARTIFACT_DIR}",
        "PYENV_VERSION=system uv run python scripts/summarize_balfrin_management_demo_package.py "
        f"--run-root {DEFAULT_MANAGEMENT_RUN_ROOT} --artifact-dir {artifact_dir / 'management_demo_package_v1'}",
        "PYENV_VERSION=system uv run python scripts/summarize_balfrin_demonstration_closure_package.py "
        f"--artifact-dir {artifact_dir}",
    ]


def apply_overrides(report: dict[str, Any], evidence_override: dict[str, Any]) -> None:
    section_overrides = evidence_override.get("section_overrides")
    if isinstance(section_overrides, dict):
        for section_name, override in section_overrides.items():
            if section_name not in report or not isinstance(report[section_name], dict) or not isinstance(override, dict):
                continue
            report[section_name].update(copy.deepcopy(override))

    if isinstance(evidence_override.get("new_measured_evidence"), dict):
        report["new_measured_evidence_section"].update(copy.deepcopy(evidence_override["new_measured_evidence"]))
    if isinstance(evidence_override.get("preservation_section"), dict):
        report["preservation_section"].update(copy.deepcopy(evidence_override["preservation_section"]))


def finalize_report(report: dict[str, Any]) -> None:
    profile = build_section_provenance_profile(report)
    report["section_provenance_profile"] = profile
    report["package_summary"]["section_counts"] = section_provenance_counts(profile)
    report["closure_status"] = derive_closure_status(profile)
    report["closure_provenance_status"] = report["closure_status"]
    report["maturity_label_update_allowed"] = report["closure_status"] == "complete_measured_closure"
    report["reviewer_answer"] = build_reviewer_answer(report["closure_status"])
    report["package_summary"]["status"] = report["closure_status"]
    report["package_summary"]["summary"] = summarize_package(report)


def build_section_provenance_profile(report: dict[str, Any]) -> list[dict[str, Any]]:
    profile: list[dict[str, Any]] = []
    for section_name in SECTION_NAMES:
        section = dict(report.get(section_name) or {})
        profile.append(
            {
                "section": section_name,
                "status": str(section.get("status") or "blocked_missing_inputs"),
                "evidence_type": classify_evidence_type(section),
                "source_paths": collect_source_paths(section.get("source_paths")),
            }
        )
    return profile


def classify_evidence_type(section: dict[str, Any]) -> str:
    evidence_type = str(section.get("evidence_type") or "").strip()
    if evidence_type in ALLOWED_EVIDENCE_TYPES:
        return evidence_type
    status = str(section.get("status") or "").strip()
    if status.startswith("blocked") or status in {"missing", "blocked"}:
        return "blocked"
    if "fixture" in status:
        return "fixture_backed"
    if "unauthor" in status or "defer" in status:
        return "unauthorized"
    if "template_only" in status or "dry_run" in status or "rerun" in status:
        return "dry_run"
    if "historical" in status:
        return "historical"
    source_paths = collect_source_paths(section.get("source_paths"))
    if any(path.startswith("docs/") for path in source_paths):
        return "historical"
    if any("tests/fixtures" in path for path in source_paths):
        return "fixture_backed"
    return "measured"


def section_provenance_counts(profile: list[dict[str, Any]]) -> dict[str, int]:
    counts = {label: 0 for label in ALLOWED_EVIDENCE_TYPES}
    for section in profile:
        evidence_type = str(section.get("evidence_type") or "blocked")
        if evidence_type in counts:
            counts[evidence_type] += 1
        else:
            counts["blocked"] += 1
    return counts


def derive_closure_status(profile: list[dict[str, Any]]) -> str:
    new_evidence = next((entry for entry in profile if entry["section"] == "new_measured_evidence_section"), {})
    if new_evidence.get("evidence_type") != "measured":
        return "blocked_no_new_measured_evidence"
    if not any(
        entry["section"] == "new_measured_evidence_section"
        for entry in profile
    ):
        return "blocked_missing_inputs"
    non_measured_sections = [
        entry for entry in profile if entry["section"] != "new_measured_evidence_section" and entry["evidence_type"] != "measured"
    ]
    if non_measured_sections:
        return "mixed_provenance_warning"
    return "complete_measured_closure"


def build_reviewer_answer(closure_status: str) -> str:
    if closure_status == "complete_measured_closure":
        return (
            "Yes. The Balfrin evidence is plausibly extensible toward larger Swiss workflows, and the package is "
            "complete enough to support that read within the non-operational boundary recorded here."
        )
    if closure_status == "mixed_provenance_warning":
        return (
            "Plausibly extensible in architecture, but the package still carries mixed provenance across measured, "
            "fixture-backed, dry-run, unauthorized, blocked, unavailable, and historical evidence, so maturity "
            "labels must not be upgraded."
        )
    if closure_status == "blocked_no_new_measured_evidence":
        return (
            "No. The package fails closed because there is no new preservation-checked measured evidence from a "
            "metrics-completion rerun or authorized multi-zone probe, so I cannot upgrade the claim that it is "
            "plausibly extensible toward larger Swiss workflows."
        )
    return "No. Required closure-package inputs are missing."


def summarize_package(report: dict[str, Any]) -> str:
    closure_status = str(report.get("closure_status") or "blocked_missing_inputs")
    counts = report.get("package_summary", {}).get("section_counts", {})
    measured = counts.get("measured", 0) if isinstance(counts, dict) else 0
    blocked = counts.get("blocked", 0) if isinstance(counts, dict) else 0
    if closure_status == "complete_measured_closure":
        return (
            f"Measured closure is complete across {measured} sections, so the evidence is plausibly extensible "
            "toward larger Swiss workflows within the recorded boundary."
        )
    if closure_status == "mixed_provenance_warning":
        return (
            f"The package carries mixed provenance across {measured} measured sections and {blocked} blocked "
            "sections, so it is useful for review but not for a maturity upgrade."
        )
    if closure_status == "blocked_no_new_measured_evidence":
        return (
            "No new preservation-checked measured evidence has been supplied, so the closure package fails closed "
            "and refuses to upgrade maturity labels."
        )
    return "The closure package is blocked because required inputs are missing."


def blocked_report(missing_inputs: list[str], *, reason: str, artifact_dir: Path) -> dict[str, Any]:
    report = {
        "schema_version": SCHEMA_VERSION,
        "closure_status": "blocked_missing_inputs",
        "closure_provenance_status": "blocked_missing_inputs",
        "maturity_label_update_allowed": False,
        "reviewer_answer": "No. Required closure-package inputs are missing.",
        "package_summary": {
            "status": "blocked_missing_inputs",
            "summary": reason,
            "section_counts": {label: 0 for label in ALLOWED_EVIDENCE_TYPES},
        },
        "runtime_section": {"status": "blocked_missing_inputs", "evidence_type": "blocked"},
        "replay_section": {"status": "blocked_missing_inputs", "evidence_type": "blocked"},
        "preservation_section": {"status": "blocked_missing_inputs", "evidence_type": "blocked"},
        "restartability_section": {"status": "blocked_missing_inputs", "evidence_type": "blocked"},
        "reducer_output_scaling_section": {"status": "blocked_missing_inputs", "evidence_type": "blocked"},
        "aoi_release_scenario_automation_section": {"status": "blocked_missing_inputs", "evidence_type": "blocked"},
        "gis_readiness_section": {"status": "blocked_missing_inputs", "evidence_type": "blocked"},
        "second_site_portability_section": {"status": "blocked_missing_inputs", "evidence_type": "blocked"},
        "scientific_claim_boundaries_section": {"status": "blocked_missing_inputs", "evidence_type": "blocked"},
        "metrics_completion_rerun_section": {"status": "blocked_missing_inputs", "evidence_type": "blocked"},
        "new_measured_evidence_section": {"status": "blocked_missing_inputs", "evidence_type": "blocked"},
        "claim_boundaries": {
            "operational_claims_allowed": False,
            "physical_probability_claims_allowed": False,
            "annual_frequency_claims_allowed": False,
            "risk_exposure_vulnerability_claims_allowed": False,
            "scale_up_authorized": False,
            "distributed_execution_authorized": False,
        },
        "section_provenance_profile": [
            {
                "section": section_name,
                "status": "blocked_missing_inputs",
                "evidence_type": "blocked",
                "source_paths": [],
            }
            for section_name in SECTION_NAMES
        ],
        "missing_inputs": list(missing_inputs),
        "source_artifacts": build_source_artifacts(artifact_dir),
        "regeneration_commands": build_regeneration_commands(artifact_dir),
    }
    return report


def materialize_artifacts(
    report: dict[str, Any],
    *,
    json_output: Path | None = None,
    text_output: Path | None = None,
) -> None:
    artifact_dir = Path(str(report.get("source_artifacts", {}).get("closure_artifact_dir") or DEFAULT_ARTIFACT_DIR))
    if artifact_dir is not None:
        artifact_dir.mkdir(parents=True, exist_ok=True)
        json_output = json_output or artifact_dir / f"{REPORT_BASENAME}.json"
        text_output = text_output or artifact_dir / f"{REPORT_BASENAME}.txt"
    if json_output is not None:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(report, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    if text_output is not None:
        text_output.parent.mkdir(parents=True, exist_ok=True)
        text_output.write_text(render_text_report(report) + "\n", encoding="utf-8")


def render_text_report(report: dict[str, Any]) -> str:
    lines = [
        "Balfrin Demonstration Closure Package",
        f"schema_version: {report.get('schema_version', 'unknown')}",
        f"closure_status: {report.get('closure_status', 'unknown')}",
        f"closure_provenance_status: {report.get('closure_provenance_status', 'unknown')}",
        f"maturity_label_update_allowed: {report.get('maturity_label_update_allowed', False)}",
        f"reviewer_answer: {report.get('reviewer_answer', '')}",
        f"summary: {report.get('package_summary', {}).get('summary', '')}",
        "",
        "section_provenance_profile:",
    ]
    for section in report.get("section_provenance_profile", []):
        lines.append(
            f"  - {section.get('section')}: {section.get('status')} "
            f"[{section.get('evidence_type')}]"
        )
    lines.extend(["", "claim_boundaries:"])
    for key, value in sorted((report.get("claim_boundaries") or {}).items()):
        lines.append(f"  - {key}: {value}")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
