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


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "observed_runout_deposition_intake_contract_v1"
EXPECTED_BENCHMARK_ROOT = ROOT / "validation/data/processed/observed_runout_deposition_benchmark"
EXPECTED_BENCHMARK_MANIFEST = EXPECTED_BENCHMARK_ROOT / "manifest.json"
EXPECTED_BENCHMARK_GEOMETRY = EXPECTED_BENCHMARK_ROOT / "observed_runout_deposition.geojson"
EXPECTED_CALIBRATION_ROOT = ROOT / "validation/data/processed/observed_runout_deposition_calibration"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    args = parser.parse_args(argv)

    report = build_report()
    if args.json_output is not None:
        output_path = args.json_output if args.json_output.is_absolute() else ROOT / args.json_output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    output = json.dumps(report, indent=2, sort_keys=True) if args.format == "json" else render_text_report(report)
    print(output)
    return 2 if report["observed_runout_deposition_intake_status"] == "blocked_missing_inputs" else 0


def build_report() -> dict[str, Any]:
    contract = build_contract()
    field_requirement_map = build_field_requirement_map()
    current_state = build_current_state()
    missing_inputs = current_state["missing_inputs"]

    return {
        "schema_version": SCHEMA_VERSION,
        "observed_runout_deposition_intake_status": "blocked_missing_inputs" if missing_inputs else "ready",
        "benchmark_intake_contract": contract,
        "field_requirement_map": field_requirement_map,
        "current_repo_state": current_state,
        "claim_boundaries": claim_boundaries(),
        "blocked_reason": (
            "no independent observed runout/deposition benchmark intake is staged in the repo"
            if missing_inputs
            else None
        ),
        "missing_inputs": missing_inputs,
        "current_state_summary": current_state_summary(current_state),
    }


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
    benchmark_inputs = [
        EXPECTED_BENCHMARK_MANIFEST,
        EXPECTED_BENCHMARK_GEOMETRY,
        EXPECTED_CALIBRATION_ROOT,
    ]
    missing_inputs = [str(path) for path in benchmark_inputs if not path.exists()]
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
        "benchmark_intake_dataset_status": "absent" if missing_inputs else "present",
        "calibration_dataset_status": "absent" if not EXPECTED_CALIBRATION_ROOT.exists() else "present",
        "required_inputs": [
            {"path": str(EXPECTED_BENCHMARK_MANIFEST), "exists": EXPECTED_BENCHMARK_MANIFEST.exists()},
            {"path": str(EXPECTED_BENCHMARK_GEOMETRY), "exists": EXPECTED_BENCHMARK_GEOMETRY.exists()},
            {"path": str(EXPECTED_CALIBRATION_ROOT), "exists": EXPECTED_CALIBRATION_ROOT.exists()},
        ],
        "adjacent_diagnostic_materials": adjacent_diagnostic_materials,
        "missing_inputs": missing_inputs,
        "evidence_boundary": "diagnostic_only_until_independent_benchmark_is_staged",
    }


def current_state_summary(current_state: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "summary": "No independent observed runout/deposition benchmark intake is staged in the repo.",
            "status": current_state["benchmark_intake_dataset_status"],
        },
        {
            "summary": "No calibration dataset is available for objective fitting.",
            "status": current_state["calibration_dataset_status"],
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
    lines.append(f"- benchmark_intake_dataset_status: {current_state['benchmark_intake_dataset_status']}")
    lines.append(f"- calibration_dataset_status: {current_state['calibration_dataset_status']}")
    lines.append(f"- evidence_boundary: {current_state['evidence_boundary']}")
    lines.append("current_state_summary:")
    for item in report["current_state_summary"]:
        lines.append(f"- {item['summary']} [{item['status']}]")
    lines.append("missing_inputs:")
    for item in current_state["missing_inputs"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("claim_boundaries:")
    for key, value in report["claim_boundaries"].items():
        lines.append(f"- {key}: {str(value).lower()}")
    return "\n".join(lines)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
