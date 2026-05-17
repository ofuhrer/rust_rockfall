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
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except ImportError as exc:  # pragma: no cover - environment setup.
    raise SystemExit("PyYAML is required; install with `python3 -m pip install PyYAML`") from exc


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "observed_runout_deposition_intake_contract_v1"
EXPECTED_BENCHMARK_ROOT = ROOT / "validation/data/processed/observed_runout_deposition_benchmark"
EXPECTED_BENCHMARK_MANIFEST = EXPECTED_BENCHMARK_ROOT / "manifest.json"
EXPECTED_BENCHMARK_GEOMETRY = EXPECTED_BENCHMARK_ROOT / "observed_runout_deposition.geojson"
EXPECTED_CALIBRATION_ROOT = ROOT / "validation/data/processed/observed_runout_deposition_calibration"
EXPECTED_BENCHMARK_INPUTS = (
    EXPECTED_BENCHMARK_MANIFEST,
    EXPECTED_BENCHMARK_GEOMETRY,
)


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
    benchmark_missing_inputs = current_state["benchmark_intake_missing_inputs"]

    report: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "observed_runout_deposition_intake_status": (
            "blocked_missing_inputs" if benchmark_missing_inputs else "ready"
        ),
        "benchmark_intake_contract": contract,
        "field_requirement_map": field_requirement_map,
        "current_repo_state": current_state,
        "claim_boundaries": claim_boundaries(),
        "blocked_reason": (
            "no independent observed runout/deposition benchmark intake is staged in the repo"
            if benchmark_missing_inputs
            else None
        ),
        "missing_inputs": benchmark_missing_inputs,
        "current_state_summary": current_state_summary(current_state),
    }
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

    acquisition_checklist_path = pack_root / "acquisition_checklist.md"
    dataset_inventory_path = pack_root / "required_dataset_inventory.yaml"
    geometry_template_path = pack_root / "geometry_template.yaml"
    provenance_template_path = pack_root / "provenance_template.yaml"
    objective_placeholders_path = pack_root / "objective_function_placeholders.yaml"
    blocked_no_evidence_report_path = pack_root / "blocked_no_evidence_report.md"
    template_manifest_path = pack_root / "template_manifest.yaml"
    validation_summary_path = pack_root / "validation_summary.json"

    acquisition_checklist_path.write_text(acquisition_checklist, encoding="utf-8")
    dataset_inventory_path.write_text(yaml.safe_dump(dataset_inventory, sort_keys=False), encoding="utf-8")
    geometry_template_path.write_text(yaml.safe_dump(geometry_template, sort_keys=False), encoding="utf-8")
    provenance_template_path.write_text(yaml.safe_dump(provenance_template, sort_keys=False), encoding="utf-8")
    objective_placeholders_path.write_text(yaml.safe_dump(objective_placeholders, sort_keys=False), encoding="utf-8")
    blocked_no_evidence_report_path.write_text(blocked_no_evidence_report, encoding="utf-8")
    template_manifest_path.write_text(yaml.safe_dump(template_manifest, sort_keys=False), encoding="utf-8")

    validation_summary = validate_readiness_pack(
        pack_root=pack_root,
        acquisition_checklist_path=acquisition_checklist_path,
        dataset_inventory_path=dataset_inventory_path,
        geometry_template_path=geometry_template_path,
        provenance_template_path=provenance_template_path,
        objective_placeholders_path=objective_placeholders_path,
        blocked_no_evidence_report_path=blocked_no_evidence_report_path,
        template_manifest_path=template_manifest_path,
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
                "dataset_role": "calibration_dataset",
                "status": "missing" if current_state["calibration_readiness_status"] != "ready" else "present",
                "required_inputs": [str(EXPECTED_CALIBRATION_ROOT)],
                "notes": [
                    "Kept separate so calibration readiness does not contaminate benchmark intake readiness.",
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
) -> dict[str, Any]:
    required_paths = {
        "acquisition_checklist": acquisition_checklist_path,
        "required_dataset_inventory": dataset_inventory_path,
        "geometry_template": geometry_template_path,
        "provenance_template": provenance_template_path,
        "objective_function_placeholders": objective_placeholders_path,
        "blocked_no_evidence_report": blocked_no_evidence_report_path,
        "template_manifest": template_manifest_path,
    }
    missing = [name for name, path in required_paths.items() if not path.exists()]
    unexpected = [
        str(path.relative_to(pack_root))
        for path in pack_root.iterdir()
        if path.is_file() and path.name not in {p.name for p in required_paths.values()}
    ]
    return {
        "validation_status": "ready" if not missing and not unexpected else "blocked_missing_inputs",
        "artifact_classification": "template_non_evidence",
        "pack_root": str(pack_root),
        "required_files_present": not missing,
        "missing_files": missing,
        "unexpected_files": unexpected,
        "validation_boundary": "template_non_evidence_only",
        "checked_files": {name: str(path) for name, path in required_paths.items()},
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
    benchmark_missing_inputs = [str(path) for path in EXPECTED_BENCHMARK_INPUTS if not path.exists()]
    calibration_missing_inputs = [str(EXPECTED_CALIBRATION_ROOT)] if not EXPECTED_CALIBRATION_ROOT.exists() else []
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


def render_text_report(report: dict[str, Any]) -> str:
    contract = report["benchmark_intake_contract"]
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
        "field_requirement_map:",
    ]
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
