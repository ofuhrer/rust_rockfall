#!/usr/bin/env python3
"""Summarize the future observed runout/deposition benchmark intake contract.

This helper is read-only. It defines the minimum benchmark-intake schema that
would be needed for observed runout/deposition evidence, maps each field to the
physical-credibility requirement it would satisfy, and reports the current
blocked state when no independent benchmark dataset is staged in the repo.
It does not fabricate validation data, fit parameters, or authorize any
calibration, annual-frequency, risk, exposure, vulnerability, or operational
claim.
"""

from __future__ import annotations

import argparse
import json
import sys
from functools import partial
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except ImportError as exc:  # pragma: no cover - environment setup.
    raise SystemExit("PyYAML is required. Run this script with `PYENV_VERSION=system uv run python ...`; CI may use `requirements-tools.txt`") from exc


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from scripts import map_physical_credibility_evidence_requirements as physical_credibility_requirements
from lib.workflow_validation import (
    build_blocked_report as shared_build_blocked_report,
    missing_repo_paths as shared_missing_repo_paths,
    require as shared_require,
    require_false_fields as shared_require_false_fields,
    require_paths_exist as shared_require_paths_exist,
    scan_text_for_misleading_claims as shared_scan_text_for_misleading_claims,
)

SCHEMA_VERSION = "observed_runout_deposition_intake_contract_v1"
EXPECTED_BENCHMARK_ROOT = ROOT / "validation/data/processed/observed_runout_deposition_benchmark"
EXPECTED_BENCHMARK_MANIFEST = EXPECTED_BENCHMARK_ROOT / "manifest.json"
EXPECTED_BENCHMARK_GEOMETRY = EXPECTED_BENCHMARK_ROOT / "observed_runout_deposition.geojson"
EXPECTED_CALIBRATION_ROOT = ROOT / "validation/data/processed/observed_runout_deposition_calibration"
EXPECTED_VALIDATION_INPUT_MANIFEST = ROOT / "validation/data/processed/chant_sura_2020/metadata_contact_split.json"
EXPECTED_VALIDATION_INPUT_CASE = ROOT / "validation/cases/chant_sura_contact.yaml"
EXPECTED_HOLDOUT_MANIFEST = ROOT / "validation/data/processed/chant_sura_2020/holdout_validation_evidence_manifest.json"
EXPECTED_HOLDOUT_CASE = ROOT / "validation/cases/chant_sura_contact_heldout.yaml"
EXPECTED_BENCHMARK_INPUTS = (
    EXPECTED_BENCHMARK_MANIFEST,
    EXPECTED_BENCHMARK_GEOMETRY,
)


class ObservedRunoutDepositionIntakeContractError(ValueError):
    """User-facing observed runout/deposition intake contract error."""


require = partial(shared_require, error_cls=ObservedRunoutDepositionIntakeContractError)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    parser.add_argument("--output-root", type=Path, default=None)
    args = parser.parse_args(argv)

    report = build_report(output_root=args.output_root)
    if args.json_output is not None:
        output_path = args.json_output if args.json_output.is_absolute() else ROOT / args.json_output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    output = json.dumps(report, indent=2, sort_keys=True) if args.format == "json" else render_text_report(report)
    print(output)
    readiness_pack = report.get("readiness_pack", {})
    if readiness_pack.get("readiness_pack_status") == "written":
        return 0
    return 2 if report["observed_runout_deposition_intake_status"] == "blocked_missing_inputs" else 0


def build_report(output_root: Path | None = None) -> dict[str, Any]:
    contract = build_contract()
    field_requirement_map = build_field_requirement_map()
    current_state = build_current_state()
    physical_credibility_gap_update = build_physical_credibility_gap_update()
    dataset_role_classification = build_dataset_role_classification(current_state=current_state)
    benchmark_missing_inputs = current_state["benchmark_intake_missing_inputs"]
    benchmark_intake_manifest = build_benchmark_intake_manifest(
        contract=contract,
        current_state=current_state,
        physical_credibility_gap_update=physical_credibility_gap_update,
        dataset_role_classification=dataset_role_classification,
        pack_root=None,
    )

    if benchmark_missing_inputs:
        report: dict[str, Any] = shared_build_blocked_report(
            schema_version=SCHEMA_VERSION,
            status_key="observed_runout_deposition_intake_status",
            missing_inputs=benchmark_missing_inputs,
            blocked_reason="no independent observed runout/deposition benchmark intake is staged in the repo",
            extra_fields={
                "benchmark_intake_contract": contract,
                "benchmark_intake_manifest": benchmark_intake_manifest,
                "field_requirement_map": field_requirement_map,
                "current_repo_state": current_state,
                "physical_credibility_gap_update": physical_credibility_gap_update,
                "dataset_role_classification": dataset_role_classification,
                "claim_boundaries": claim_boundaries(),
                "current_state_summary": current_state_summary(current_state),
            },
        )
    else:
        report = {
            "schema_version": SCHEMA_VERSION,
            "observed_runout_deposition_intake_status": "ready",
            "benchmark_intake_contract": contract,
            "benchmark_intake_manifest": benchmark_intake_manifest,
            "field_requirement_map": field_requirement_map,
            "current_repo_state": current_state,
            "physical_credibility_gap_update": physical_credibility_gap_update,
            "dataset_role_classification": dataset_role_classification,
            "claim_boundaries": claim_boundaries(),
            "blocked_reason": None,
            "missing_inputs": [],
            "current_state_summary": current_state_summary(current_state),
        }
    validate_claim_boundaries(report["claim_boundaries"])
    shared_scan_text_for_misleading_claims(report, require_fn=require)
    if output_root is not None:
        readiness_pack = build_readiness_pack(output_root=output_root, report=report)
        report["readiness_pack"] = readiness_pack
    return report


def build_readiness_pack(*, output_root: Path, report: dict[str, Any]) -> dict[str, Any]:
    pack_root = resolve_output_root(output_root)
    pack_root.mkdir(parents=True, exist_ok=True)

    acquisition_checklist = build_acquisition_checklist(report=report, pack_root=pack_root)
    dataset_inventory = build_required_dataset_inventory(report=report, pack_root=pack_root)
    geometry_template = build_geometry_template(report=report, pack_root=pack_root)
    provenance_template = build_provenance_template(report=report, pack_root=pack_root)
    objective_placeholders = build_objective_function_placeholders(report=report, pack_root=pack_root)
    blocked_no_evidence_report = build_blocked_no_evidence_report(report=report, pack_root=pack_root)
    template_manifest = build_template_manifest(report=report, pack_root=pack_root)
    benchmark_intake_manifest = build_benchmark_intake_manifest(
        contract=report["benchmark_intake_contract"],
        current_state=report["current_repo_state"],
        physical_credibility_gap_update=report["physical_credibility_gap_update"],
        dataset_role_classification=report["dataset_role_classification"],
        pack_root=pack_root,
    )

    acquisition_checklist_path = pack_root / "acquisition_checklist.md"
    dataset_inventory_path = pack_root / "required_dataset_inventory.yaml"
    geometry_template_path = pack_root / "geometry_template.yaml"
    provenance_template_path = pack_root / "provenance_template.yaml"
    objective_placeholders_path = pack_root / "objective_function_placeholders.yaml"
    blocked_no_evidence_report_path = pack_root / "blocked_no_evidence_report.md"
    template_manifest_path = pack_root / "template_manifest.yaml"
    benchmark_intake_manifest_path = pack_root / "benchmark_intake_manifest.yaml"
    validation_summary_path = pack_root / "validation_summary.json"

    acquisition_checklist_path.write_text(acquisition_checklist, encoding="utf-8")
    dataset_inventory_path.write_text(yaml.safe_dump(dataset_inventory, sort_keys=False), encoding="utf-8")
    geometry_template_path.write_text(yaml.safe_dump(geometry_template, sort_keys=False), encoding="utf-8")
    provenance_template_path.write_text(yaml.safe_dump(provenance_template, sort_keys=False), encoding="utf-8")
    objective_placeholders_path.write_text(yaml.safe_dump(objective_placeholders, sort_keys=False), encoding="utf-8")
    blocked_no_evidence_report_path.write_text(blocked_no_evidence_report, encoding="utf-8")
    template_manifest_path.write_text(yaml.safe_dump(template_manifest, sort_keys=False), encoding="utf-8")
    benchmark_intake_manifest_path.write_text(yaml.safe_dump(benchmark_intake_manifest, sort_keys=False), encoding="utf-8")

    validation_summary = validate_readiness_pack(
        pack_root=pack_root,
        acquisition_checklist_path=acquisition_checklist_path,
        dataset_inventory_path=dataset_inventory_path,
        geometry_template_path=geometry_template_path,
        provenance_template_path=provenance_template_path,
        objective_placeholders_path=objective_placeholders_path,
        blocked_no_evidence_report_path=blocked_no_evidence_report_path,
        template_manifest_path=template_manifest_path,
        benchmark_intake_manifest_path=benchmark_intake_manifest_path,
    )
    validation_summary_path.write_text(json.dumps(validation_summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return {
        "readiness_pack_status": "written",
        "artifact_classification": "template_non_evidence",
        "readiness_pack_root": str(pack_root),
        "generated_files": {
            "acquisition_checklist": str(acquisition_checklist_path),
            "required_dataset_inventory": str(dataset_inventory_path),
            "geometry_template": str(geometry_template_path),
            "provenance_template": str(provenance_template_path),
            "objective_function_placeholders": str(objective_placeholders_path),
            "blocked_no_evidence_report": str(blocked_no_evidence_report_path),
            "template_manifest": str(template_manifest_path),
            "benchmark_intake_manifest": str(benchmark_intake_manifest_path),
            "validation_summary": str(validation_summary_path),
        },
        "validation_summary": validation_summary,
    }


def build_template_manifest(*, report: dict[str, Any], pack_root: Path) -> dict[str, Any]:
    contract = report["benchmark_intake_contract"]
    current_state = report["current_repo_state"]
    return {
        "schema_version": SCHEMA_VERSION,
        "artifact_classification": "template_non_evidence",
        "pack_status": "dry_run_template",
        "pack_root": str(pack_root),
        "source_script": "scripts/summarize_observed_runout_deposition_intake_contract.py",
        "observed_runout_deposition_intake_status": report["observed_runout_deposition_intake_status"],
        "blocked_reason": report["blocked_reason"],
        "benchmark_intake_contract": {
            "geometry": contract["geometry"],
            "event_source_metadata": contract["event_source_metadata"],
            "uncertainty": contract["uncertainty"],
            "objective_function_placeholders": contract["objective_function_placeholders"],
        },
        "required_inputs": [
            {
                "path": str(EXPECTED_BENCHMARK_MANIFEST),
                "exists": EXPECTED_BENCHMARK_MANIFEST.exists(),
            },
            {
                "path": str(EXPECTED_BENCHMARK_GEOMETRY),
                "exists": EXPECTED_BENCHMARK_GEOMETRY.exists(),
            },
        ],
        "validation_boundary": current_state["evidence_boundary"],
        "claim_boundaries": report["claim_boundaries"],
        "notes": [
            "Template/non-evidence artifact only.",
            "No real benchmark data, calibration fit, or operational claim is encoded here.",
        ],
    }


def build_benchmark_intake_manifest(
    *,
    contract: dict[str, Any],
    current_state: dict[str, Any],
    physical_credibility_gap_update: dict[str, Any],
    dataset_role_classification: list[dict[str, Any]],
    pack_root: Path | None,
) -> dict[str, Any]:
    geometry = contract["geometry"]
    event_source_metadata = contract["event_source_metadata"]
    uncertainty = contract["uncertainty"]
    objective_function_placeholders = contract["objective_function_placeholders"]
    return {
        "schema_version": SCHEMA_VERSION,
        "artifact_classification": "template_non_evidence",
        "manifest_status": "dry_run_template" if pack_root is not None else "report_only",
        "pack_root": str(pack_root) if pack_root is not None else None,
        "blocked_reason": (
            "no independent observed runout/deposition benchmark intake is staged in the repo"
            if current_state["benchmark_intake_readiness_status"] != "ready"
            else None
        ),
        "observed_geometry": {
            "required_crs": geometry["required_crs"],
            "required_vertical_datum": geometry["required_vertical_datum"],
            "allowed_geometry_roles": list(geometry["allowed_geometry_roles"]),
            "required_fields": list(geometry["required_fields"]),
            "geometry_roles": [
                {
                    "geometry_role": role,
                    "required": True,
                    "description": geometry_role_description(role),
                }
                for role in geometry["allowed_geometry_roles"]
            ],
        },
        "provenance": {
            "required_fields": list(event_source_metadata["required_fields"]),
            "source_metadata_required": list(event_source_metadata["source_metadata_required"]),
            "current_repo_state": {
                "benchmark_intake_readiness_status": current_state["benchmark_intake_readiness_status"],
                "calibration_readiness_status": current_state["calibration_readiness_status"],
            },
        },
        "uncertainty": {
            "required_fields": list(uncertainty["required_fields"]),
            "measurement_units": dict(uncertainty["measurement_units"]),
        },
        "objective_function_readiness": {
            "required_fields": list(objective_function_placeholders["required_fields"]),
            "objective_status": objective_function_placeholders["objective_status"],
            "fit_record_required": objective_function_placeholders["fit_record_required"],
            "notes": list(objective_function_placeholders["notes"]),
        },
        "calibration_validation_separation": {
            "benchmark_intake_missing_inputs": list(current_state["benchmark_intake_missing_inputs"]),
            "calibration_missing_inputs": list(current_state["calibration_missing_inputs"]),
            "calibration_readiness_status": current_state["calibration_readiness_status"],
            "validation_inputs_status": dataset_role_status(dataset_role_classification, "validation_inputs"),
            "holdout_data_status": dataset_role_status(dataset_role_classification, "holdout_data"),
            "calibration_validation_overlap_allowed": False,
            "no_reuse_for_fit": True,
        },
        "dataset_role_classification": dataset_role_classification,
        "physical_credibility_gap_update": physical_credibility_gap_update,
        "claim_boundaries": claim_boundaries(),
        "notes": [
            "Template/non-evidence manifest for a future observed runout/deposition intake.",
            "No real benchmark data, calibration fit, or operational claim is encoded here.",
        ],
    }


def build_physical_credibility_gap_update() -> dict[str, Any]:
    report = physical_credibility_requirements.build_report()
    return {
        "schema_version": physical_credibility_requirements.SCHEMA_VERSION,
        "physical_credibility_requirements_status": report["physical_credibility_requirements_status"],
        "current_physical_credibility_status": report["current_physical_credibility_status"],
        "calibration_status": report["calibration_status"],
        "validation_status": report["validation_status"],
        "blocked_reason": report["blocked_reason"],
        "missing_inputs": list(report["missing_inputs"]),
        "claim_boundaries": dict(report["claim_boundaries"]),
        "evidence_acquisition_summary": dict(report["evidence_acquisition_summary"]),
    }


def build_dataset_role_classification(current_state: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "dataset_role": "observed_runout_deposition_benchmark",
            "status": "present" if current_state["benchmark_intake_readiness_status"] == "ready" else "missing",
            "required_inputs": [str(EXPECTED_BENCHMARK_MANIFEST), str(EXPECTED_BENCHMARK_GEOMETRY)],
            "claim_boundary": "benchmark intake only; no calibration or operational claim",
        },
        {
            "dataset_role": "release_zone_provenance",
            "status": "present" if current_state["benchmark_intake_readiness_status"] == "ready" else "missing",
            "required_inputs": [str(EXPECTED_BENCHMARK_MANIFEST), str(EXPECTED_BENCHMARK_GEOMETRY)],
            "claim_boundary": "release-zone provenance only; no validation or calibration claim",
        },
        {
            "dataset_role": "block_population_evidence",
            "status": "missing",
            "required_inputs": [str(ROOT / "docs/target_area_physical_evidence_acquisition_pack.md")],
            "claim_boundary": "future physical-probability bridge only",
        },
        {
            "dataset_role": "calibration_inputs",
            "status": "present" if current_state["calibration_readiness_status"] == "ready" else "missing",
            "required_inputs": [str(EXPECTED_CALIBRATION_ROOT)],
            "claim_boundary": "calibration only; separated from benchmark intake and holdout data",
        },
        {
            "dataset_role": "validation_inputs",
            "status": "present" if validation_inputs_available() else "missing",
            "required_inputs": [str(EXPECTED_VALIDATION_INPUT_MANIFEST), str(EXPECTED_VALIDATION_INPUT_CASE)],
            "claim_boundary": "validation-only inputs; separated from calibration inputs",
        },
        {
            "dataset_role": "holdout_data",
            "status": "present" if holdout_data_available() else "missing",
            "required_inputs": [str(EXPECTED_HOLDOUT_MANIFEST), str(EXPECTED_HOLDOUT_CASE)],
            "claim_boundary": "holdout-only data; no reuse for tuning",
        },
    ]


def dataset_role_status(dataset_roles: list[dict[str, Any]], dataset_role: str) -> str:
    for entry in dataset_roles:
        if entry.get("dataset_role") == dataset_role:
            return str(entry.get("status") or "missing")
    return "missing"


def validation_inputs_available() -> bool:
    return EXPECTED_VALIDATION_INPUT_MANIFEST.exists() and EXPECTED_VALIDATION_INPUT_CASE.exists()


def holdout_data_available() -> bool:
    return EXPECTED_HOLDOUT_MANIFEST.exists() and EXPECTED_HOLDOUT_CASE.exists()


def build_required_dataset_inventory(*, report: dict[str, Any], pack_root: Path) -> dict[str, Any]:
    current_state = report["current_repo_state"]
    return {
        "schema_version": SCHEMA_VERSION,
        "artifact_classification": "template_non_evidence",
        "inventory_status": "dry_run_template",
        "pack_root": str(pack_root),
        "dataset_roles": [
            {
                "dataset_role": "independent_observed_runout_deposition_benchmark",
                "status": "missing" if current_state["benchmark_intake_readiness_status"] != "ready" else "present",
                "required_inputs": [
                    str(EXPECTED_BENCHMARK_MANIFEST),
                    str(EXPECTED_BENCHMARK_GEOMETRY),
                ],
                "notes": [
                    "Benchmark intake only.",
                    "Separate from calibration data and fit targets.",
                ],
            },
            {
                "dataset_role": "release_zone_provenance",
                "status": "missing" if current_state["benchmark_intake_readiness_status"] != "ready" else "present",
                "required_inputs": [str(EXPECTED_BENCHMARK_MANIFEST), str(EXPECTED_BENCHMARK_GEOMETRY)],
                "notes": [
                    "Release-zone provenance must be independent from the benchmark intake and current workflow heuristics.",
                ],
            },
            {
                "dataset_role": "block_population_evidence",
                "status": "missing",
                "required_inputs": [str(ROOT / "docs/target_area_physical_evidence_acquisition_pack.md")],
                "notes": [
                    "No block-population or block-size evidence is staged in the repo.",
                ],
            },
            {
                "dataset_role": "calibration_inputs",
                "status": "missing" if current_state["calibration_readiness_status"] != "ready" else "present",
                "required_inputs": [str(EXPECTED_CALIBRATION_ROOT)],
                "notes": [
                    "Kept separate so calibration readiness does not contaminate benchmark intake readiness.",
                ],
            },
            {
                "dataset_role": "validation_inputs",
                "status": "present" if validation_inputs_available() else "missing",
                "required_inputs": [
                    str(EXPECTED_VALIDATION_INPUT_MANIFEST),
                    str(EXPECTED_VALIDATION_INPUT_CASE),
                ],
                "notes": [
                    "Validation inputs remain separate from calibration inputs.",
                ],
            },
            {
                "dataset_role": "holdout_data",
                "status": "present" if holdout_data_available() else "missing",
                "required_inputs": [
                    str(EXPECTED_HOLDOUT_MANIFEST),
                    str(EXPECTED_HOLDOUT_CASE),
                ],
                "notes": [
                    "Holdout data remain separated from calibration and model-selection fixtures.",
                ],
            },
        ],
        "notes": [
            "Template/non-evidence artifact only.",
            "No real benchmark data is staged here.",
        ],
    }


def build_geometry_template(*, report: dict[str, Any], pack_root: Path) -> dict[str, Any]:
    contract = report["benchmark_intake_contract"]
    return {
        "schema_version": SCHEMA_VERSION,
        "artifact_classification": "template_non_evidence",
        "template_status": "dry_run_template",
        "pack_root": str(pack_root),
        "required_crs": contract["geometry"]["required_crs"],
        "required_vertical_datum": contract["geometry"]["required_vertical_datum"],
        "allowed_geometry_roles": contract["geometry"]["allowed_geometry_roles"],
        "required_fields": contract["geometry"]["required_fields"],
        "geometry_roles": [
            {
                "geometry_role": role,
                "required": True,
                "description": geometry_role_description(role),
            }
            for role in contract["geometry"]["allowed_geometry_roles"]
        ],
        "notes": [
            "This inventory is a template for future geometry intake.",
            "It does not contain observed benchmark geometries.",
        ],
    }


def build_provenance_template(*, report: dict[str, Any], pack_root: Path) -> dict[str, Any]:
    contract = report["benchmark_intake_contract"]
    return {
        "schema_version": SCHEMA_VERSION,
        "artifact_classification": "template_non_evidence",
        "template_status": "dry_run_template",
        "pack_root": str(pack_root),
        "required_provenance_fields": contract["event_source_metadata"]["required_fields"],
        "required_source_metadata_fields": contract["event_source_metadata"]["source_metadata_required"],
        "required_uncertainty_fields": contract["uncertainty"]["required_fields"],
        "notes": [
            "Template for future provenance intake only.",
            "It does not contain observed benchmark provenance.",
        ],
    }


def build_objective_function_placeholders(*, report: dict[str, Any], pack_root: Path) -> dict[str, Any]:
    contract = report["benchmark_intake_contract"]
    return {
        "schema_version": SCHEMA_VERSION,
        "artifact_classification": "template_non_evidence",
        "template_status": "dry_run_template",
        "pack_root": str(pack_root),
        "required_fields": contract["objective_function_placeholders"]["required_fields"],
        "objective_status": contract["objective_function_placeholders"]["objective_status"],
        "fit_record_required": contract["objective_function_placeholders"]["fit_record_required"],
        "notes": contract["objective_function_placeholders"]["notes"],
    }


def build_acquisition_checklist(*, report: dict[str, Any], pack_root: Path) -> str:
    contract = report["benchmark_intake_contract"]
    current_state = report["current_repo_state"]
    lines = [
        "# Observed runout/deposition acquisition checklist",
        "",
        "Template / non-evidence artifact.",
        "This checklist identifies the independent benchmark artifacts that must exist before the intake can be treated as real evidence.",
        "",
        "Required acquisition items:",
        f"- Benchmark manifest: {EXPECTED_BENCHMARK_MANIFEST}",
        f"- Benchmark geometry: {EXPECTED_BENCHMARK_GEOMETRY}",
        f"- Required CRS: {contract['geometry']['required_crs']}",
        f"- Required vertical datum: {contract['geometry']['required_vertical_datum']}",
        f"- Allowed geometry roles: {', '.join(contract['geometry']['allowed_geometry_roles'])}",
        f"- Required geometry fields: {', '.join(contract['geometry']['required_fields'])}",
        f"- Required provenance fields: {', '.join(contract['event_source_metadata']['required_fields'])}",
        f"- Required source metadata fields: {', '.join(contract['event_source_metadata']['source_metadata_required'])}",
        f"- Required uncertainty fields: {', '.join(contract['uncertainty']['required_fields'])}",
        f"- Required objective placeholder fields: {', '.join(contract['objective_function_placeholders']['required_fields'])}",
        "",
        "Current boundary:",
        f"- {current_state['evidence_boundary']}",
        "",
        "Acquisition steps:",
        "- Stage an independent observed runout/deposition benchmark manifest.",
        "- Stage the matching observed geometry record(s) with provenance URIs intact.",
        "- Keep the benchmark intake separate from calibration data and fit targets.",
        "- Verify the CRS, vertical datum, geometry roles, and uncertainty metadata before any analysis.",
        "",
        "Artifact root:",
        f"- {pack_root}",
    ]
    return "\n".join(lines) + "\n"


def build_blocked_no_evidence_report(*, report: dict[str, Any], pack_root: Path) -> str:
    current_state = report["current_repo_state"]
    physical_gap = report["physical_credibility_gap_update"]
    lines = [
        "# Blocked no-evidence report",
        "",
        "Status: blocked_missing_inputs",
        "",
        "Reason:",
        f"- {report['blocked_reason']}",
        "",
        "Missing benchmark inputs:",
    ]
    for item in current_state["benchmark_intake_missing_inputs"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "Calibration separation:",
            f"- calibration_readiness_status: {current_state['calibration_readiness_status']}",
            f"- calibration_missing_inputs: {', '.join(current_state['calibration_missing_inputs']) if current_state['calibration_missing_inputs'] else 'none'}",
            "",
            "Dataset-role classification:",
        ]
    )
    for role in report["dataset_role_classification"]:
        lines.append(f"- {role['dataset_role']}: {role['status']}")
    lines.extend(
        [
            "",
            "Physical-credibility gap update:",
            f"- physical_credibility_requirements_status: {physical_gap['physical_credibility_requirements_status']}",
            f"- current_physical_credibility_status: {physical_gap['current_physical_credibility_status']}",
            f"- blocked_reason: {physical_gap['blocked_reason']}",
            "",
            "This report is a blocker summary only and does not encode benchmark evidence.",
            "",
            "Artifact root:",
            f"- {pack_root}",
        ]
    )
    return "\n".join(lines) + "\n"


def validate_readiness_pack(
    *,
    pack_root: Path,
    acquisition_checklist_path: Path,
    dataset_inventory_path: Path,
    geometry_template_path: Path,
    provenance_template_path: Path,
    objective_placeholders_path: Path,
    blocked_no_evidence_report_path: Path,
    template_manifest_path: Path,
    benchmark_intake_manifest_path: Path,
) -> dict[str, Any]:
    required_paths = {
        "acquisition_checklist": acquisition_checklist_path,
        "required_dataset_inventory": dataset_inventory_path,
        "geometry_template": geometry_template_path,
        "provenance_template": provenance_template_path,
        "objective_function_placeholders": objective_placeholders_path,
        "blocked_no_evidence_report": blocked_no_evidence_report_path,
        "template_manifest": template_manifest_path,
        "benchmark_intake_manifest": benchmark_intake_manifest_path,
    }
    validated_paths = shared_require_paths_exist(
        required_paths,
        ObservedRunoutDepositionIntakeContractError,
        root=None,
        label_prefix="readiness_pack",
    )
    missing: list[str] = []
    unexpected = [
        str(path.relative_to(pack_root))
        for path in pack_root.iterdir()
        if path.is_file() and path.name not in {p.name for p in required_paths.values()}
    ]
    return {
        "validation_status": "ready" if not unexpected else "blocked_missing_inputs",
        "artifact_classification": "template_non_evidence",
        "pack_root": str(pack_root),
        "required_files_present": True,
        "missing_files": [],
        "unexpected_files": unexpected,
        "validation_boundary": "template_non_evidence_only",
        "checked_files": {name: str(path) for name, path in validated_paths.items()},
    }


def geometry_role_description(role: str) -> str:
    descriptions = {
        "source_polygon": "observed source geometry tied to provenance and release-zone screening",
        "runout_axis_line": "measured or digitized axis used for runout comparison",
        "deposition_footprint_polygon": "observed deposition footprint used for overlap comparison",
        "reference_observation_points": "site reference points used for future QA or alignment",
    }
    return descriptions.get(role, "required geometry role for benchmark intake")


def resolve_output_root(output_root: Path) -> Path:
    return output_root if output_root.is_absolute() else ROOT / output_root


def build_contract() -> dict[str, Any]:
    return {
        "geometry": {
            "required_crs": "EPSG:2056",
            "required_vertical_datum": "LN02",
            "allowed_geometry_roles": [
                "source_polygon",
                "runout_axis_line",
                "deposition_footprint_polygon",
                "reference_observation_points",
            ],
            "allowed_encodings": ["GeoJSON", "WKT"],
            "required_fields": [
                "geometry_id",
                "geometry_role",
                "geometry_encoding",
                "geometry_crs",
                "geometry_value",
            ],
        },
        "event_source_metadata": {
            "required_fields": [
                "event_id",
                "event_date",
                "site_id",
                "source_id",
                "source_name",
                "observer",
                "observation_method",
                "provenance_uri",
            ],
            "source_metadata_required": [
                "source_origin_description",
                "source_reference_frame",
                "source_geometry_reference",
            ],
        },
        "uncertainty": {
            "required_fields": [
                "geometry_tolerance_m",
                "position_tolerance_m",
                "timing_tolerance_days",
                "coverage_completeness",
                "qa_status",
                "uncertainty_notes",
            ],
            "measurement_units": {
                "geometry_tolerance_m": "m",
                "position_tolerance_m": "m",
                "timing_tolerance_days": "days",
            },
        },
        "objective_function_placeholders": {
            "required_fields": [
                "runout_endpoint_error_m",
                "runout_axis_distance_residual_m",
                "deposition_footprint_iou",
                "source_to_deposition_distance_residual_m",
                "objective_status",
            ],
            "objective_status": "placeholder_only",
            "fit_record_required": False,
            "notes": [
                "placeholders define future scoring interfaces only",
                "no objective fitting is claimed until real benchmark evidence is staged",
            ],
        },
    }


def build_field_requirement_map() -> list[dict[str, Any]]:
    return [
        field_requirement(
            "geometry.geometry_crs",
            "terrain_and_context_evidence",
            "site-specific spatial reference needed to interpret the observation in LV95",
        ),
        field_requirement(
            "geometry.geometry_role=source_polygon",
            "release_zone_evidence",
            "ties the observed record to source-zone provenance and release geometry",
        ),
        field_requirement(
            "geometry.geometry_id",
            "observed_runout_deposition",
            "provides a stable identifier for the geometry record",
        ),
        field_requirement(
            "geometry.geometry_role=runout_axis_line",
            "observed_runout_deposition",
            "captures the measured runout path for the benchmark intake",
        ),
        field_requirement(
            "geometry.geometry_role=deposition_footprint_polygon",
            "observed_runout_deposition",
            "captures the observed deposition extent for benchmark comparison",
        ),
        field_requirement(
            "geometry.geometry_encoding",
            "observed_runout_deposition",
            "records the geometry serialization needed to preserve the observation",
        ),
        field_requirement(
            "geometry.geometry_value",
            "observed_runout_deposition",
            "holds the actual geometry payload for the benchmark record",
        ),
        field_requirement(
            "event_source_metadata.event_id",
            "observed_runout_deposition",
            "creates a stable key for a future benchmark intake record",
        ),
        field_requirement(
            "event_source_metadata.event_date",
            "observed_runout_deposition",
            "anchors the observed event in time",
        ),
        field_requirement(
            "event_source_metadata.site_id",
            "observed_runout_deposition",
            "anchors the benchmark to a specific site record",
        ),
        field_requirement(
            "event_source_metadata.source_id",
            "release_zone_evidence",
            "connects the observation to source provenance",
        ),
        field_requirement(
            "event_source_metadata.source_name",
            "observed_runout_deposition",
            "names the source record attached to the observed event",
        ),
        field_requirement(
            "event_source_metadata.observer",
            "observed_runout_deposition",
            "records who captured or validated the observation",
        ),
        field_requirement(
            "event_source_metadata.observation_method",
            "observed_runout_deposition",
            "records the observation method used for the benchmark intake",
        ),
        field_requirement(
            "event_source_metadata.provenance_uri",
            "observed_runout_deposition",
            "supports traceability and audit of the intake record",
        ),
        field_requirement(
            "event_source_metadata.source_origin_description",
            "release_zone_evidence",
            "documents the origin of the source record and its release provenance",
        ),
        field_requirement(
            "event_source_metadata.source_reference_frame",
            "terrain_and_context_evidence",
            "keeps the source record anchored to the same spatial frame as the benchmark",
        ),
        field_requirement(
            "event_source_metadata.source_geometry_reference",
            "release_zone_evidence",
            "links the observation back to the source geometry used in the intake",
        ),
        field_requirement(
            "uncertainty.geometry_tolerance_m",
            "observed_runout_deposition",
            "records spatial measurement tolerance around the observed geometry",
        ),
        field_requirement(
            "uncertainty.position_tolerance_m",
            "observed_runout_deposition",
            "records point-position uncertainty for the intake geometry",
        ),
        field_requirement(
            "uncertainty.timing_tolerance_days",
            "observed_runout_deposition",
            "records event-time uncertainty for the observed record",
        ),
        field_requirement(
            "uncertainty.coverage_completeness",
            "observed_runout_deposition",
            "states whether the benchmark intake is complete or partial",
        ),
        field_requirement(
            "uncertainty.qa_status",
            "observed_runout_deposition",
            "records quality-assurance status for the intake record",
        ),
        field_requirement(
            "uncertainty.uncertainty_notes",
            "observed_runout_deposition",
            "captures the free-text uncertainty notes needed for review",
        ),
        field_requirement(
            "objective_function_placeholders.runout_endpoint_error_m",
            "calibration_data_and_objective_functions",
            "placeholder scoring term for a future calibration or fit record",
        ),
        field_requirement(
            "objective_function_placeholders.runout_axis_distance_residual_m",
            "calibration_data_and_objective_functions",
            "placeholder residual for future objective-function design",
        ),
        field_requirement(
            "objective_function_placeholders.deposition_footprint_iou",
            "calibration_data_and_objective_functions",
            "placeholder overlap score for future objective-function design",
        ),
        field_requirement(
            "objective_function_placeholders.source_to_deposition_distance_residual_m",
            "calibration_data_and_objective_functions",
            "placeholder residual connecting source provenance to deposition comparison",
        ),
        field_requirement(
            "objective_function_placeholders.objective_status",
            "calibration_data_and_objective_functions",
            "labels the objective terms as placeholders rather than fit results",
        ),
    ]


def field_requirement(field_path: str, requirement_category: str, why_it_matters: str) -> dict[str, Any]:
    return {
        "field_path": field_path,
        "physical_credibility_requirement": requirement_category,
        "why_it_matters": why_it_matters,
    }


def build_current_state() -> dict[str, Any]:
    benchmark_missing_inputs = shared_missing_repo_paths(
        {
            "manifest": EXPECTED_BENCHMARK_MANIFEST,
            "geometry": EXPECTED_BENCHMARK_GEOMETRY,
        }
    )
    calibration_missing_inputs = shared_missing_repo_paths({"calibration_root": EXPECTED_CALIBRATION_ROOT})
    adjacent_diagnostic_materials = [
        {
            "path": str(ROOT / "data/processed/tschamut2014/observed_deposition.csv"),
            "classification": "diagnostic_only",
            "status": "present" if (ROOT / "data/processed/tschamut2014/observed_deposition.csv").exists() else "missing",
        },
        {
            "path": str(ROOT / "validation/data/processed/tschamut/observed_deposition.csv"),
            "classification": "diagnostic_only",
            "status": "present" if (ROOT / "validation/data/processed/tschamut/observed_deposition.csv").exists() else "missing",
        },
    ]
    return {
        "benchmark_intake_readiness_status": "blocked_missing_inputs" if benchmark_missing_inputs else "ready",
        "calibration_readiness_status": "blocked_missing_inputs" if calibration_missing_inputs else "ready",
        "benchmark_intake_dataset_status": "absent" if benchmark_missing_inputs else "present",
        "calibration_dataset_status": "absent" if calibration_missing_inputs else "present",
        "required_inputs": [
            {"path": str(EXPECTED_BENCHMARK_MANIFEST), "exists": EXPECTED_BENCHMARK_MANIFEST.exists()},
            {"path": str(EXPECTED_BENCHMARK_GEOMETRY), "exists": EXPECTED_BENCHMARK_GEOMETRY.exists()},
            {"path": str(EXPECTED_CALIBRATION_ROOT), "exists": EXPECTED_CALIBRATION_ROOT.exists()},
        ],
        "adjacent_diagnostic_materials": adjacent_diagnostic_materials,
        "benchmark_intake_missing_inputs": benchmark_missing_inputs,
        "calibration_missing_inputs": calibration_missing_inputs,
        "missing_inputs": benchmark_missing_inputs,
        "evidence_boundary": "diagnostic_only_until_independent_benchmark_is_staged",
    }


def current_state_summary(current_state: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "summary": "No independent observed runout/deposition benchmark intake is staged in the repo.",
            "status": current_state["benchmark_intake_readiness_status"],
        },
        {
            "summary": "No calibration dataset is available for objective fitting.",
            "status": current_state["calibration_readiness_status"],
        },
        {
            "summary": "Existing observed deposition files are diagnostic-only and not accepted as benchmark intake.",
            "status": "diagnostic_only",
        },
    ]


def claim_boundaries() -> dict[str, bool]:
    return {
        "calibration_claims_allowed": False,
        "physical_probability_claims_allowed": False,
        "annual_frequency_claims_allowed": False,
        "risk_exposure_vulnerability_claims_allowed": False,
        "operational_claims_allowed": False,
    }


def validate_claim_boundaries(boundaries: dict[str, Any]) -> None:
    shared_require_false_fields(
        boundaries,
        (
            "calibration_claims_allowed",
            "physical_probability_claims_allowed",
            "annual_frequency_claims_allowed",
            "risk_exposure_vulnerability_claims_allowed",
            "operational_claims_allowed",
        ),
        ObservedRunoutDepositionIntakeContractError,
        label_prefix="claim_boundaries",
    )


def render_text_report(report: dict[str, Any]) -> str:
    contract = report["benchmark_intake_contract"]
    benchmark_manifest = report["benchmark_intake_manifest"]
    current_state = report["current_repo_state"]
    lines = [
        f"schema_version: {report['schema_version']}",
        f"observed_runout_deposition_intake_status: {report['observed_runout_deposition_intake_status']}",
        f"blocked_reason: {report['blocked_reason']}",
        "",
        "benchmark_intake_contract:",
        f"- geometry.required_crs: {contract['geometry']['required_crs']}",
        f"- geometry.required_vertical_datum: {contract['geometry']['required_vertical_datum']}",
        f"- geometry.allowed_geometry_roles: {', '.join(contract['geometry']['allowed_geometry_roles'])}",
        f"- event_source_metadata.required_fields: {', '.join(contract['event_source_metadata']['required_fields'])}",
        f"- uncertainty.required_fields: {', '.join(contract['uncertainty']['required_fields'])}",
        f"- objective_function_placeholders.required_fields: {', '.join(contract['objective_function_placeholders']['required_fields'])}",
        "",
        "benchmark_intake_manifest:",
        f"- manifest_status: {benchmark_manifest['manifest_status']}",
        f"- dataset_roles: {', '.join(role['dataset_role'] for role in benchmark_manifest['dataset_role_classification'])}",
        f"- physical_credibility_status: {benchmark_manifest['physical_credibility_gap_update']['current_physical_credibility_status']}",
        "",
        "physical_credibility_gap_update:",
        f"- physical_credibility_requirements_status: {report['physical_credibility_gap_update']['physical_credibility_requirements_status']}",
        f"- current_physical_credibility_status: {report['physical_credibility_gap_update']['current_physical_credibility_status']}",
        f"- blocked_reason: {report['physical_credibility_gap_update']['blocked_reason']}",
        "",
        "dataset_role_classification:",
    ]
    for item in report["dataset_role_classification"]:
        lines.append(f"- {item['dataset_role']}: {item['status']}")
    lines.extend(
        [
            "",
            "field_requirement_map:",
        ]
    )
    for item in report["field_requirement_map"]:
        lines.append(
            f"- {item['field_path']} -> {item['physical_credibility_requirement']}: {item['why_it_matters']}"
        )
    lines.append("")
    lines.append("current_repo_state:")
    lines.append(f"- benchmark_intake_readiness_status: {current_state['benchmark_intake_readiness_status']}")
    lines.append(f"- calibration_readiness_status: {current_state['calibration_readiness_status']}")
    lines.append(f"- benchmark_intake_dataset_status: {current_state['benchmark_intake_dataset_status']}")
    lines.append(f"- calibration_dataset_status: {current_state['calibration_dataset_status']}")
    lines.append(f"- evidence_boundary: {current_state['evidence_boundary']}")
    lines.append("benchmark_intake_missing_inputs:")
    for item in current_state["benchmark_intake_missing_inputs"]:
        lines.append(f"- {item}")
    lines.append("calibration_missing_inputs:")
    for item in current_state["calibration_missing_inputs"]:
        lines.append(f"- {item}")
    lines.append("current_state_summary:")
    for item in report["current_state_summary"]:
        lines.append(f"- {item['summary']} [{item['status']}]")
    lines.append("missing_inputs:")
    for item in current_state["missing_inputs"]:
        lines.append(f"- {item}")
    if "readiness_pack" in report:
        readiness_pack = report["readiness_pack"]
        lines.append("")
        lines.append("readiness_pack:")
        lines.append(f"- readiness_pack_status: {readiness_pack['readiness_pack_status']}")
        lines.append(f"- artifact_classification: {readiness_pack['artifact_classification']}")
        lines.append(f"- readiness_pack_root: {readiness_pack['readiness_pack_root']}")
        for name, path in readiness_pack["generated_files"].items():
            lines.append(f"- {name}: {path}")
    lines.append("")
    lines.append("claim_boundaries:")
    for key, value in report["claim_boundaries"].items():
        lines.append(f"- {key}: {str(value).lower()}")
    return "\n".join(lines)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
