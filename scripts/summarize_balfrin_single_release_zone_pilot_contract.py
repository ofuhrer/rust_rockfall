#!/usr/bin/env python3
"""Summarize the frozen Balfrin minimal demonstration contract.

This helper stays read-only. It reads the committed pilot-contract YAML,
checks that the required supporting records exist, and reports the minimal demo
scope, commands, artifacts, evidence, visual products, success criteria, and
explicit no-go boundaries without authorizing scale-up or physical-probability
claims.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "balfrin_single_release_zone_pilot_contract_v1"
DEFAULT_CONTRACT = ROOT / "validation/pilot_runs/tschamut_public_balfrin_single_release_zone_pilot_contract_v1.yaml"
READY_STATUS = "ready_for_balfrin_single_release_zone_pilot"
MINIMAL_DEMO_READY_STATUS = "ready"
BLOCKED_STATUS = "blocked_missing_inputs"
BLOCKED_SCOPE_CREEP_STATUS = "blocked_scope_creep"
ALLOWED_COMMAND_MODES = {"read_only", "dry_run"}
BOUNDARY_FLAGS = (
    "operational_claims_allowed",
    "annual_frequency_claims_allowed",
    "physical_probability_claims_allowed",
    "risk_exposure_vulnerability_claims_allowed",
    "scale_up_authorized",
    "distributed_execution_authorized",
)
REQUIRED_NON_GOALS = {
    "annual_frequency",
    "physical_probability",
    "return_period",
    "risk",
    "exposure",
    "vulnerability",
    "operational_hazard_map",
    "distributed_execution",
    "scale_up",
    "scientific_closure",
}


class BalfrinSingleReleaseZonePilotContractError(ValueError):
    """User-facing contract-summary error."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--format", choices=("json", "text"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    args = parser.parse_args(argv)

    try:
        report = build_report(args.contract)
    except BalfrinSingleReleaseZonePilotContractError as exc:
        print(f"balfrin minimal demonstration contract summary error: {exc}", file=sys.stderr)
        return 2

    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text_report(report))
    return 0 if report["minimal_demo_status"] == MINIMAL_DEMO_READY_STATUS else 2


def build_report(contract_path: Path | None = DEFAULT_CONTRACT) -> dict[str, Any]:
    if contract_path is None:
        raise BalfrinSingleReleaseZonePilotContractError("contract path is required")

    contract_path = Path(contract_path)
    if not contract_path.exists():
        return _blocked_report(
            contract_path=contract_path,
            missing_required_inputs=[str(contract_path)],
            blocker="contract file is missing",
        )

    contract = _load_yaml(contract_path)
    minimal_demo_contract = _require_mapping(contract, "minimal_demo_contract")
    required_inputs = _require_list_of_str(minimal_demo_contract, "required_inputs")
    commands = _require_command_list(minimal_demo_contract, "commands")
    artifacts = _require_object_list(minimal_demo_contract, "artifacts")
    evidence = _require_object_list(minimal_demo_contract, "evidence")
    visual_products = _require_object_list(minimal_demo_contract, "visual_products")
    success_criteria = _require_object_list(minimal_demo_contract, "success_criteria")
    non_goals = _require_list_of_str(minimal_demo_contract, "non_goals")
    claim_boundaries = _require_mapping(minimal_demo_contract, "claim_boundaries")
    scope_authorizations = _require_optional_list_of_str(minimal_demo_contract, "scope_authorizations")
    release_zone_scope = _require_mapping(contract, "release_zone_scope")
    validation_output = _require_mapping(contract, "validation_output")
    balfrin_resource_assumptions = _require_mapping(contract, "balfrin_resource_assumptions")
    no_go_boundaries = _require_list_of_str(contract, "no_go_boundaries")
    expected_artifact_families = _require_list_of_str(contract, "expected_artifact_families")
    hazard_layer_products = _require_list_of_str(contract, "hazard_layer_products")

    missing_required_inputs = [
        str(_to_repo_path(path))
        for path in required_inputs
        if not _to_repo_path(path).exists()
    ]

    scope_creep_reasons = validate_scope_guardrails(
        commands=commands,
        non_goals=non_goals,
        claim_boundaries=claim_boundaries,
        scope_authorizations=scope_authorizations,
    )

    if missing_required_inputs:
        minimal_demo_status = BLOCKED_STATUS
        contract_status = BLOCKED_STATUS
        feasibility_status = BLOCKED_STATUS
        blocked_reason = "one or more required inputs are missing"
    elif scope_creep_reasons:
        minimal_demo_status = BLOCKED_SCOPE_CREEP_STATUS
        contract_status = BLOCKED_SCOPE_CREEP_STATUS
        feasibility_status = BLOCKED_SCOPE_CREEP_STATUS
        blocked_reason = "scope guardrails were widened: " + "; ".join(scope_creep_reasons)
    else:
        minimal_demo_status = MINIMAL_DEMO_READY_STATUS
        contract_status = READY_STATUS
        feasibility_status = READY_STATUS
        blocked_reason = None

    report = {
        "schema_version": SCHEMA_VERSION,
        "pilot_id": contract.get("pilot_id", "tschamut_public_pilot"),
        "run_id": contract.get("run_id", "tschamut_public_balfrin_single_release_zone_pilot_contract_v1"),
        "contract_status": contract_status,
        "minimal_demo_status": minimal_demo_status,
        "conditional_diagnostic_feasibility_status": feasibility_status,
        "scale_up_authorized": False,
        "physical_frequency_authorized": False,
        "operational_claims_allowed": False,
        "contract_path": str(contract_path),
        "minimal_demo_contract": {
            "required_inputs": required_inputs,
            "commands": commands,
            "artifacts": artifacts,
            "evidence": evidence,
            "visual_products": visual_products,
            "success_criteria": success_criteria,
            "non_goals": non_goals,
            "claim_boundaries": {key: bool(claim_boundaries.get(key, False)) for key in BOUNDARY_FLAGS},
            "scope_authorizations": scope_authorizations,
        },
        "release_zone_scope": {
            "release_zone_count": _require_int(release_zone_scope, "release_zone_count"),
            "release_cell_count": _require_int(release_zone_scope, "release_cell_count"),
            "trajectory_count_target": _require_int(release_zone_scope, "trajectory_count_target"),
            "trajectories_per_release_cell": _require_int(release_zone_scope, "trajectories_per_release_cell"),
            "block_scenario_count": _require_int(release_zone_scope, "block_scenario_count"),
            "block_scenario_policy": _require_str(release_zone_scope, "block_scenario_policy"),
        },
        "validation_output": {
            "validation_output_mode": _require_str(validation_output, "validation_output_mode"),
            "hazard_output_profile": _require_str(validation_output, "hazard_output_profile"),
            "conditional_curve_export": _require_str(validation_output, "conditional_curve_export"),
            "grid_csv_export": _require_str(validation_output, "grid_csv_export"),
            "export_geotiff": _require_bool(validation_output, "export_geotiff"),
            "pilot_gis_package": _require_bool(validation_output, "pilot_gis_package"),
        },
        "expected_artifact_families": expected_artifact_families,
        "hazard_layer_products": hazard_layer_products,
        "balfrin_resource_assumptions": {
            "execution_boundary": _require_str(balfrin_resource_assumptions, "execution_boundary"),
            "trajectory_workers": _require_int(balfrin_resource_assumptions, "trajectory_workers"),
            "reducer_workers": _require_int(balfrin_resource_assumptions, "reducer_workers"),
            "explicit_grid_required": _require_bool(balfrin_resource_assumptions, "explicit_grid_required"),
            "distributed_execution_authorized": _require_bool(
                balfrin_resource_assumptions, "distributed_execution_authorized"
            ),
            "generated_outputs_committed": _require_bool(
                balfrin_resource_assumptions, "generated_outputs_committed"
            ),
            "single_job_boundary": _require_bool(balfrin_resource_assumptions, "single_job_boundary"),
        },
        "no_go_boundaries": no_go_boundaries,
        "required_inputs": required_inputs,
        "missing_required_inputs": missing_required_inputs,
        "feasibility_vs_authorization": {
            "conditional_diagnostic_feasibility": feasibility_status,
            "scale_up_authorized": False,
            "physical_frequency_authorized": False,
            "operational_claims_allowed": False,
        },
        "contract_boundary_summary": [
            "one release zone is frozen for the next Balfrin minimal demo",
            "native reduced output stays bounded and non-operational",
            "minimal demo success is not scientific closure",
            "scale-up, annual-frequency, risk, exposure, vulnerability, distributed-execution, and physical-probability claims remain out of scope",
        ],
        "scope_creep_reasons": scope_creep_reasons,
    }

    report["blocker"] = blocked_reason
    return report


def render_text_report(report: dict[str, Any]) -> str:
    minimal_demo = report.get("minimal_demo_contract") or {}

    if not report.get("release_zone_scope"):
        lines = [
            "Balfrin Minimal Demonstration Contract",
            "",
            f"- Contract status: `{report['contract_status']}`",
            f"- Minimal demo status: `{report['minimal_demo_status']}`",
            f"- Conditional diagnostic feasibility: `{report['conditional_diagnostic_feasibility_status']}`",
            f"- Scale-up authorized: `{report['scale_up_authorized']}`",
            f"- Physical frequency authorized: `{report['physical_frequency_authorized']}`",
            f"- Operational claims allowed: `{report['operational_claims_allowed']}`",
        ]
        if report.get("blocker"):
            lines.extend(["", f"- Blocker: {report['blocker']}"])
        if report.get("scope_creep_reasons"):
            lines.extend(["", "Scope creep reasons:"])
            for reason in report["scope_creep_reasons"]:
                lines.append(f"- {reason}")
        lines.extend(["", "## Missing Inputs", ""])
        if report["missing_required_inputs"]:
            for item in report["missing_required_inputs"]:
                lines.append(f"- `{item}`")
        else:
            lines.append("- none")
        lines.extend(["", "## Contract Boundary Summary", ""])
        for item in report["contract_boundary_summary"]:
            lines.append(f"- {item}")
        lines.extend(
            [
                "",
                "## Minimal Demo vs Scientific Closure",
                "",
                "This contract defines the smallest convincing Balfrin demonstration artifact, not a measured scientific-closure decision.",
                "Scientific closure remains the job of the post-run interpretation gate and later measured evidence.",
            ]
        )
        return "\n".join(lines)

    lines = [
        "Balfrin Minimal Demonstration Contract",
        "",
        f"- Contract status: `{report['contract_status']}`",
        f"- Minimal demo status: `{report['minimal_demo_status']}`",
        f"- Conditional diagnostic feasibility: `{report['conditional_diagnostic_feasibility_status']}`",
        f"- Scale-up authorized: `{report['scale_up_authorized']}`",
        f"- Physical frequency authorized: `{report['physical_frequency_authorized']}`",
        f"- Operational claims allowed: `{report['operational_claims_allowed']}`",
        "",
    ]
    if report.get("blocker"):
        lines.extend(["", f"- Blocker: {report['blocker']}"])
    if report.get("scope_creep_reasons"):
        lines.extend(["", "Scope creep reasons:"])
        for reason in report["scope_creep_reasons"]:
            lines.append(f"- {reason}")
    lines.extend(
        [
            "",
            "## Minimal Demo Scope",
            "",
            "Required inputs:",
        ]
    )
    for item in minimal_demo.get("required_inputs", []):
        lines.append(f"- `{item}`")
    lines.extend(["", "Commands:"])
    for command in minimal_demo.get("commands", []):
        lines.append(f"- `{command['command_id']}` [{command['mode']}]")
        lines.append(f"  - `{command['command']}`")
        lines.append(f"  - {command['purpose']}")
        for output in command.get("expected_outputs", []):
            lines.append(f"  - expected output: `{output}`")
    lines.extend(["", "Artifacts:"])
    for artifact in minimal_demo.get("artifacts", []):
        lines.append(f"- `{artifact['artifact_id']}` [{artifact['kind']}] -> `{artifact['path']}`")
    lines.extend(["", "Evidence:"])
    for item in minimal_demo.get("evidence", []):
        lines.append(f"- `{item['evidence_id']}` [{item['status']}] - {item['note']}")
    lines.extend(["", "Visual Products:"])
    for item in minimal_demo.get("visual_products", []):
        lines.append(f"- `{item['visual_product_id']}` [{item['format']}] - {item['purpose']}")
    lines.extend(["", "Success Criteria:"])
    for item in minimal_demo.get("success_criteria", []):
        lines.append(f"- `{item['criterion_id']}` - {item['statement']}")
    lines.extend(["", "Non-Goals:"])
    for item in minimal_demo.get("non_goals", []):
        lines.append(f"- `{item}`")
    lines.extend(["", "Claim Boundaries:"])
    for key, value in minimal_demo.get("claim_boundaries", {}).items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "Scope Authorizations:"])
    if minimal_demo.get("scope_authorizations"):
        for item in minimal_demo["scope_authorizations"]:
            lines.append(f"- `{item}`")
    else:
        lines.append("- none")

    scope = report["release_zone_scope"]
    validation_output = report["validation_output"]
    resources = report["balfrin_resource_assumptions"]
    lines.extend(
        [
            "",
            "## Release Zone Scope",
            "",
            f"- Release zone count: `{scope['release_zone_count']}`",
            f"- Release cell count: `{scope['release_cell_count']}`",
            f"- Trajectory-count target: `{scope['trajectory_count_target']}`",
            f"- Trajectories per release cell: `{scope['trajectories_per_release_cell']}`",
            f"- Block scenario count: `{scope['block_scenario_count']}`",
            f"- Block scenario policy: `{scope['block_scenario_policy']}`",
            "",
            "## Validation Output",
            "",
            f"- Validation output mode: `{validation_output['validation_output_mode']}`",
            f"- Hazard output profile: `{validation_output['hazard_output_profile']}`",
            f"- Conditional curve export: `{validation_output['conditional_curve_export']}`",
            f"- Grid CSV export: `{validation_output['grid_csv_export']}`",
            f"- Export GeoTIFF: `{validation_output['export_geotiff']}`",
            f"- Pilot GIS package: `{validation_output['pilot_gis_package']}`",
            "",
            "Expected artifact families:",
        ]
    )
    for family in report["expected_artifact_families"]:
        lines.append(f"- `{family}`")
    lines.extend(["", "Hazard-layer products:"])
    for product in report["hazard_layer_products"]:
        lines.append(f"- `{product}`")
    lines.extend(
        [
            "",
            "## Balfrin Resource Assumptions",
            "",
            f"- Execution boundary: `{resources['execution_boundary']}`",
            f"- Trajectory workers: `{resources['trajectory_workers']}`",
            f"- Reducer workers: `{resources['reducer_workers']}`",
            f"- Explicit grid required: `{resources['explicit_grid_required']}`",
            f"- Distributed execution authorized: `{resources['distributed_execution_authorized']}`",
            f"- Generated outputs committed: `{resources['generated_outputs_committed']}`",
            f"- Single-job boundary: `{resources['single_job_boundary']}`",
            "",
            "## No-Go Boundaries",
            "",
        ]
    )
    for boundary in report["no_go_boundaries"]:
        lines.append(f"- `{boundary}`")
    lines.extend(
        [
            "",
            "## Required Inputs",
            "",
        ]
    )
    for item in report["required_inputs"]:
        lines.append(f"- `{item}`")
    lines.extend(["", "## Missing Inputs", ""])
    if report["missing_required_inputs"]:
        for item in report["missing_required_inputs"]:
            lines.append(f"- `{item}`")
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Contract Boundary Summary",
            "",
        ]
    )
    for item in report["contract_boundary_summary"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Minimal Demo vs Scientific Closure",
            "",
            "This contract defines the smallest convincing Balfrin demonstration artifact, not a measured scientific-closure decision.",
            "Scientific closure remains the job of the post-run interpretation gate and later measured evidence.",
        ]
    )
    return "\n".join(lines)


def _blocked_report(*, contract_path: Path, missing_required_inputs: list[str], blocker: str) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "pilot_id": "tschamut_public_pilot",
        "run_id": "tschamut_public_balfrin_single_release_zone_pilot_contract_v1",
        "contract_status": BLOCKED_STATUS,
        "minimal_demo_status": BLOCKED_STATUS,
        "conditional_diagnostic_feasibility_status": BLOCKED_STATUS,
        "scale_up_authorized": False,
        "physical_frequency_authorized": False,
        "operational_claims_allowed": False,
        "contract_path": str(contract_path),
        "minimal_demo_contract": {
            "required_inputs": [],
            "commands": [],
            "artifacts": [],
            "evidence": [],
            "visual_products": [],
            "success_criteria": [],
            "non_goals": [],
            "claim_boundaries": {key: False for key in BOUNDARY_FLAGS},
            "scope_authorizations": [],
        },
        "release_zone_scope": {},
        "validation_output": {},
        "expected_artifact_families": [],
        "hazard_layer_products": [],
        "balfrin_resource_assumptions": {},
        "no_go_boundaries": [
            "annual_frequency",
            "physical_probability",
            "return_period",
            "risk",
            "exposure",
            "vulnerability",
            "operational_hazard_map",
            "distributed_execution",
            "scale_up",
            "scientific_closure",
        ],
        "required_inputs": [],
        "missing_required_inputs": missing_required_inputs,
        "feasibility_vs_authorization": {
            "conditional_diagnostic_feasibility": BLOCKED_STATUS,
            "scale_up_authorized": False,
            "physical_frequency_authorized": False,
            "operational_claims_allowed": False,
        },
        "contract_boundary_summary": [
            blocker,
            "scale-up, annual-frequency, risk, exposure, vulnerability, distributed-execution, physical-probability, and operational claims remain out of scope",
        ],
        "blocker": blocker,
        "scope_creep_reasons": [],
    }


def validate_scope_guardrails(
    *,
    commands: list[dict[str, Any]],
    non_goals: list[str],
    claim_boundaries: dict[str, Any],
    scope_authorizations: list[str],
) -> list[str]:
    reasons: list[str] = []

    missing_non_goals = sorted(REQUIRED_NON_GOALS.difference(non_goals))
    if missing_non_goals:
        reasons.append("missing non-goals: " + ", ".join(missing_non_goals))

    unauthorized_flags = [flag for flag in BOUNDARY_FLAGS if bool(claim_boundaries.get(flag)) is True]
    if unauthorized_flags:
        reasons.append("authorization flags set true: " + ", ".join(sorted(unauthorized_flags)))

    if scope_authorizations:
        reasons.append("scope authorizations are not empty: " + ", ".join(scope_authorizations))

    bad_modes = sorted(
        {
            str(command.get("mode") or "")
            for command in commands
            if str(command.get("mode") or "") not in ALLOWED_COMMAND_MODES
        }
    )
    if bad_modes:
        reasons.append("command modes outside the read_only/dry_run boundary: " + ", ".join(bad_modes))

    return reasons


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - preserve path context.
        raise BalfrinSingleReleaseZonePilotContractError(f"failed to read YAML {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise BalfrinSingleReleaseZonePilotContractError(f"YAML document must be a mapping: {path}")
    if data.get("schema_version") != SCHEMA_VERSION:
        raise BalfrinSingleReleaseZonePilotContractError(
            f"schema_version must be {SCHEMA_VERSION}: {path}"
        )
    return data


def _require_mapping(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key)
    if not isinstance(value, dict):
        raise BalfrinSingleReleaseZonePilotContractError(f"{key} must be a mapping")
    return value


def _require_list_of_str(data: dict[str, Any], key: str) -> list[str]:
    value = data.get(key)
    if not isinstance(value, list) or not value or not all(isinstance(item, str) for item in value):
        raise BalfrinSingleReleaseZonePilotContractError(f"{key} must be a non-empty list of strings")
    return value


def _require_optional_list_of_str(data: dict[str, Any], key: str) -> list[str]:
    value = data.get(key)
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise BalfrinSingleReleaseZonePilotContractError(f"{key} must be a list of strings")
    return value


def _require_command_list(data: dict[str, Any], key: str) -> list[dict[str, Any]]:
    value = data.get(key)
    if not isinstance(value, list) or not value:
        raise BalfrinSingleReleaseZonePilotContractError(f"{key} must be a non-empty list of command mappings")
    commands: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict):
            raise BalfrinSingleReleaseZonePilotContractError(f"{key} entries must be mappings")
        command_id = item.get("command_id")
        command = item.get("command")
        mode = item.get("mode")
        purpose = item.get("purpose")
        expected_outputs = item.get("expected_outputs")
        if not isinstance(command_id, str) or not command_id:
            raise BalfrinSingleReleaseZonePilotContractError(f"{key} entries require non-empty command_id strings")
        if not isinstance(command, str) or not command:
            raise BalfrinSingleReleaseZonePilotContractError(f"{key} entries require non-empty command strings")
        if not isinstance(mode, str) or not mode:
            raise BalfrinSingleReleaseZonePilotContractError(f"{key} entries require non-empty mode strings")
        if not isinstance(purpose, str) or not purpose:
            raise BalfrinSingleReleaseZonePilotContractError(f"{key} entries require non-empty purpose strings")
        if not isinstance(expected_outputs, list) or not expected_outputs or not all(
            isinstance(output, str) and output for output in expected_outputs
        ):
            raise BalfrinSingleReleaseZonePilotContractError(
                f"{key} entries require non-empty expected_outputs lists of strings"
            )
        commands.append(
            {
                "command_id": command_id,
                "command": command,
                "mode": mode,
                "purpose": purpose,
                "expected_outputs": expected_outputs,
            }
        )
    return commands


def _require_object_list(data: dict[str, Any], key: str) -> list[dict[str, Any]]:
    value = data.get(key)
    if not isinstance(value, list) or not value:
        raise BalfrinSingleReleaseZonePilotContractError(f"{key} must be a non-empty list of mappings")
    objects: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict):
            raise BalfrinSingleReleaseZonePilotContractError(f"{key} entries must be mappings")
        objects.append(item)
    return objects


def _require_str(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value:
        raise BalfrinSingleReleaseZonePilotContractError(f"{key} must be a non-empty string")
    return value


def _require_int(data: dict[str, Any], key: str) -> int:
    value = data.get(key)
    if not isinstance(value, int):
        raise BalfrinSingleReleaseZonePilotContractError(f"{key} must be an integer")
    return value


def _require_bool(data: dict[str, Any], key: str) -> bool:
    value = data.get(key)
    if not isinstance(value, bool):
        raise BalfrinSingleReleaseZonePilotContractError(f"{key} must be a boolean")
    return value


def _to_repo_path(value: str) -> Path:
    path = Path(str(value).strip().replace("\\", "/"))
    return path if path.is_absolute() else (ROOT / path).resolve()


if __name__ == "__main__":
    raise SystemExit(main())
