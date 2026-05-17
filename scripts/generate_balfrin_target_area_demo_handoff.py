#!/usr/bin/env python3
"""Generate the frozen Tschamut target-area Balfrin handoff bundle.

This helper stays at the handoff boundary. It reads the committed target-area
contract and the frozen target-gate records, then emits a deterministic case
skeleton bundle that records the scenario-generation handoff and GIS scope
summary without authorizing any hazard build, job submission, or scale-up.
"""

from __future__ import annotations

import argparse
import csv
import json
import shlex
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except ImportError as exc:  # pragma: no cover - environment setup.
    raise SystemExit("PyYAML is required; install with `python3 -m pip install PyYAML`") from exc


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "balfrin_target_area_demo_handoff_v1"
CASE_SKELETON_SCHEMA_VERSION = "balfrin_target_area_demo_case_skeleton_v1"
COMMAND_MANIFEST_SCHEMA_VERSION = "balfrin_target_area_demo_command_manifest_v1"
EXPECTED_OUTPUT_ROOTS_SCHEMA_VERSION = "balfrin_target_area_demo_expected_output_roots_v1"
SCENARIO_GENERATION_HANDOFF_SCHEMA_VERSION = "balfrin_target_area_demo_scenario_generation_handoff_v1"
GIS_SCOPE_SUMMARY_SCHEMA_VERSION = "balfrin_target_area_demo_gis_scope_summary_v1"
DEFAULT_CONTRACT = ROOT / "validation/pilot_runs/tschamut_public_balfrin_target_area_demo_v1.yaml"
DEFAULT_OUTPUT_ROOT = ROOT / "validation/private/tschamut_public_pilot/balfrin_target_area_demo_v1"
CASE_FILENAME = "tschamut_public_balfrin_target_area_demo_case_skeleton.yaml"
COMMAND_MANIFEST_FILENAME = "tschamut_public_balfrin_target_area_demo_command_manifest.json"
EXPECTED_OUTPUT_ROOTS_FILENAME = "tschamut_public_balfrin_target_area_demo_expected_output_roots.yaml"
SCENARIO_GENERATION_HANDOFF_FILENAME = "tschamut_public_balfrin_target_area_demo_scenario_generation_handoff.json"
GIS_SCOPE_SUMMARY_FILENAME = "tschamut_public_balfrin_target_area_demo_gis_scope_summary.yaml"
BUNDLE_REPORT_FILENAME = "tschamut_public_balfrin_target_area_demo_bundle_report.json"
IGNORED_TARGET_ROOTS = [
    "validation/private/tschamut_public_pilot/target_gate_v1",
    "validation/private/tschamut_public_pilot/target_gate_v1_rebuildable_reduced",
    "validation/private/tschamut_public_pilot/target_gate_v1_summary_only",
    "hazard/results/tschamut_public_pilot/target_gate_v1",
]
BUNDLE_STATUS = "template_only"


class TargetAreaHandoffError(ValueError):
    """User-facing handoff generation error."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    args = parser.parse_args(argv)

    try:
        report = build_report(args.contract, args.output_root)
    except TargetAreaHandoffError as exc:
        print(f"balfrin target-area handoff error: {exc}", file=__import__("sys").stderr)
        return 2

    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text_report(report))
    return 0


def build_report(contract_path: Path = DEFAULT_CONTRACT, output_root: Path = DEFAULT_OUTPUT_ROOT) -> dict[str, Any]:
    if not contract_path.exists():
        raise TargetAreaHandoffError(f"missing target-area contract: {contract_path}")

    contract = load_yaml(contract_path)
    target_area = require_mapping(contract.get("target_area"), "target_area")
    input_freeze = require_mapping(contract.get("input_freeze"), "input_freeze")
    output_mode = require_mapping(contract.get("output_mode"), "output_mode")
    boundary = require_mapping(contract.get("balfrin_execution_boundary"), "balfrin_execution_boundary")
    claim_boundary = require_mapping(contract.get("claim_boundary"), "claim_boundary")

    output_root = resolve_output_root(output_root)
    if not is_allowed_output_root(output_root):
        raise TargetAreaHandoffError(
            f"output-root must stay under /tmp or {DEFAULT_OUTPUT_ROOT}: {output_root}"
        )

    reproduction_path = resolve_repo_path(input_freeze.get("target_gate_reproduction_record_path"))
    execution_contract_path = resolve_repo_path(input_freeze.get("target_gate_execution_contract_path"))
    conditional_gate_path = resolve_repo_path(input_freeze.get("conditional_pilot_gate_path"))
    source_zone_metadata_path = resolve_repo_path(input_freeze.get("source_zone_metadata_path"))
    release_points_path = resolve_repo_path(input_freeze.get("release_points_csv"))
    deposition_points_path = resolve_repo_path(input_freeze.get("deposition_points_csv"))
    scenario_table_path = resolve_repo_path(input_freeze.get("scenario_table_path"))
    source_scenario_policy_path = resolve_repo_path(input_freeze.get("source_scenario_policy_path"))
    geodata_manifest_path = resolve_repo_path(target_area.get("geodata_manifest_path"))

    required_inputs = [
        reproduction_path,
        execution_contract_path,
        conditional_gate_path,
        source_zone_metadata_path,
        release_points_path,
        deposition_points_path,
        scenario_table_path,
        source_scenario_policy_path,
        geodata_manifest_path,
    ]
    missing = [display_path(path) for path in required_inputs if not path.exists()]
    if missing:
        raise TargetAreaHandoffError("required frozen target-area inputs are missing: " + ", ".join(missing))

    reproduction_record = load_yaml(reproduction_path)
    execution_contract = load_yaml(execution_contract_path)
    conditional_gate = load_yaml(conditional_gate_path)
    source_zone_metadata = load_yaml(source_zone_metadata_path)
    scenario_rows = load_csv_rows(scenario_table_path)
    source_scenario_policy = load_yaml(source_scenario_policy_path)
    target_gate_case_path = resolve_repo_path(
        require_mapping(reproduction_record.get("case_generation"), "case_generation").get("case_path")
    )
    target_gate_case = load_yaml(target_gate_case_path)

    target_area_id = text_value(target_area.get("target_area_id"), "target_area.target_area_id")
    target_area_name = text_value(target_area.get("target_area_name"), "target_area.target_area_name")
    run_id = text_value(contract.get("run_id"), "run_id")
    target_gate_case_id = text_value(target_gate_case.get("case_id"), "target_gate_case.case_id")

    scenario_generation_handoff = build_scenario_generation_handoff(
        contract_path=contract_path,
        target_area=target_area,
        input_freeze=input_freeze,
        boundary=boundary,
        reproduction_path=reproduction_path,
        target_gate_case_path=target_gate_case_path,
        execution_contract_path=execution_contract_path,
        geodata_manifest_path=geodata_manifest_path,
        source_zone_metadata_path=source_zone_metadata_path,
        scenario_table_path=scenario_table_path,
        source_scenario_policy_path=source_scenario_policy_path,
        source_zone_metadata=source_zone_metadata,
        scenario_rows=scenario_rows,
        source_scenario_policy=source_scenario_policy,
        reproduction_record=reproduction_record,
        execution_contract=execution_contract,
        target_gate_case=target_gate_case,
        output_root=output_root,
    )
    gis_scope_summary = build_gis_scope_summary(
        target_area=target_area,
        input_freeze=input_freeze,
        output_mode=output_mode,
        boundary=boundary,
        claim_boundary=claim_boundary,
        output_root=output_root,
        target_gate_case_path=target_gate_case_path,
        target_gate_case_id=target_gate_case_id,
        execution_contract=execution_contract,
        conditional_gate=conditional_gate,
    )
    command_manifest = build_command_manifest(
        contract_path=contract_path,
        target_gate_case_path=target_gate_case_path,
        output_root=output_root,
        scenario_generation_handoff=scenario_generation_handoff,
        gis_scope_summary=gis_scope_summary,
    )
    expected_output_roots = build_expected_output_roots(output_root)
    case_skeleton = build_case_skeleton(
        contract=contract,
        target_area=target_area,
        input_freeze=input_freeze,
        output_mode=output_mode,
        boundary=boundary,
        claim_boundary=claim_boundary,
        target_gate_case_path=target_gate_case_path,
        target_gate_case_id=target_gate_case_id,
        scenario_generation_handoff=scenario_generation_handoff,
        gis_scope_summary=gis_scope_summary,
        command_manifest=command_manifest,
        expected_output_roots=expected_output_roots,
        output_root=output_root,
    )

    bundle = {
        "schema_version": SCHEMA_VERSION,
        "bundle_status": BUNDLE_STATUS,
        "bundle_runnable_status": "runnable",
        "bundle_execution_boundary": "template_only_handoff_bundle",
        "target_area_id": target_area_id,
        "target_area_name": target_area_name,
        "run_id": run_id,
        "output_root": str(output_root),
        "case_skeleton_output": {
            "schema_version": CASE_SKELETON_SCHEMA_VERSION,
            "status": BUNDLE_STATUS,
            "write_status": "written",
            "case_skeleton_path": str(output_root / CASE_FILENAME),
            "command_manifest_path": str(output_root / COMMAND_MANIFEST_FILENAME),
            "expected_output_roots_path": str(output_root / EXPECTED_OUTPUT_ROOTS_FILENAME),
            "scenario_generation_handoff_path": str(output_root / SCENARIO_GENERATION_HANDOFF_FILENAME),
            "gis_scope_summary_path": str(output_root / GIS_SCOPE_SUMMARY_FILENAME),
            "bundle_report_path": str(output_root / BUNDLE_REPORT_FILENAME),
            "case_skeleton": case_skeleton,
        },
        "command_manifest": command_manifest,
        "expected_output_roots": expected_output_roots,
        "scenario_generation_handoff": scenario_generation_handoff,
        "gis_scope_summary": gis_scope_summary,
        "claim_boundary": claim_boundary,
        "blocked_reason": "template_only frozen target-area handoff",
        "scale_up_authorized": False,
        "distributed_execution_authorized": False,
        "operational_claims_allowed": False,
        "raw_inputs": {
            "contract_path": display_path(contract_path),
            "target_gate_reproduction_record_path": display_path(reproduction_path),
            "target_gate_execution_contract_path": display_path(execution_contract_path),
            "conditional_pilot_gate_path": display_path(conditional_gate_path),
            "target_gate_case_path": display_path(target_gate_case_path),
            "geodata_manifest_path": display_path(geodata_manifest_path),
            "source_zone_metadata_path": display_path(source_zone_metadata_path),
            "release_points_csv": display_path(release_points_path),
            "deposition_points_csv": display_path(deposition_points_path),
            "scenario_table_path": display_path(scenario_table_path),
            "source_scenario_policy_path": display_path(source_scenario_policy_path),
        },
    }

    write_bundle_files(bundle)
    return bundle


def build_case_skeleton(
    *,
    contract: dict[str, Any],
    target_area: dict[str, Any],
    input_freeze: dict[str, Any],
    output_mode: dict[str, Any],
    boundary: dict[str, Any],
    claim_boundary: dict[str, Any],
    target_gate_case_path: Path,
    target_gate_case_id: str,
    scenario_generation_handoff: dict[str, Any],
    gis_scope_summary: dict[str, Any],
    command_manifest: dict[str, Any],
    expected_output_roots: list[str],
    output_root: Path,
) -> dict[str, Any]:
    return {
        "schema_version": CASE_SKELETON_SCHEMA_VERSION,
        "case_id": "tschamut_public_balfrin_target_area_demo_case_skeleton_v1",
        "title": "Tschamut target-area Balfrin handoff case skeleton",
        "mode": "template_only",
        "case_skeleton_status": BUNDLE_STATUS,
        "blocked_execution_status": BUNDLE_STATUS,
        "bundle_execution_boundary": "template_only_handoff_bundle",
        "bundle_status": BUNDLE_STATUS,
        "read_only": True,
        "target_area_id": text_value(target_area.get("target_area_id"), "target_area.target_area_id"),
        "target_area_name": text_value(target_area.get("target_area_name"), "target_area.target_area_name"),
        "target_area_label": text_value(target_area.get("target_area_label"), "target_area.target_area_label"),
        "target_area": target_area,
        "run_id": text_value(contract.get("run_id"), "run_id"),
        "contract_status": text_value(contract.get("contract_status"), "contract_status"),
        "input_freeze": {
            **input_freeze,
            "target_gate_case_path": display_path(target_gate_case_path),
            "target_gate_case_id": target_gate_case_id,
        },
        "output_mode": output_mode,
        "balfrin_execution_boundary": boundary,
        "claim_boundary": claim_boundary,
        "command_sequence": [
            {
                "step_id": command["id"],
                "label": command["label"],
                "status": command["execution_class"],
                "blocked_reason": command.get("blocked_reason", ""),
                "command": command["command"],
                "expected_inputs": command["expected_inputs"],
                "expected_outputs": command["expected_outputs"],
            }
            for command in command_manifest["commands"]
        ],
        "expected_output_roots": expected_output_roots,
        "runnable_command_ids": [
            command["id"] for command in command_manifest["commands"] if command["execution_class"] == "runnable"
        ],
        "template_only_command_ids": [
            command["id"] for command in command_manifest["commands"] if command["execution_class"] == "template_only"
        ],
        "output_root": str(output_root),
        "write_status": "written",
        "scenario_generation_handoff": scenario_generation_handoff,
        "gis_scope_summary": gis_scope_summary,
        "command_manifest": command_manifest,
        "notes": [
            "The bundle is template-only: it records a frozen target-area handoff and does not authorize hazard build or submission.",
            "The target-area contract remains the Tschamut selected domain, not the Chant Sura / Flüelapass second-site candidate.",
        ],
    }


def build_command_manifest(
    *,
    contract_path: Path,
    target_gate_case_path: Path,
    output_root: Path,
    scenario_generation_handoff: dict[str, Any],
    gis_scope_summary: dict[str, Any],
) -> dict[str, Any]:
    materialized_case_path = output_root / CASE_FILENAME
    command_manifest_path = output_root / COMMAND_MANIFEST_FILENAME
    expected_output_roots_path = output_root / EXPECTED_OUTPUT_ROOTS_FILENAME
    scenario_generation_handoff_path = output_root / SCENARIO_GENERATION_HANDOFF_FILENAME
    gis_scope_summary_path = output_root / GIS_SCOPE_SUMMARY_FILENAME
    bundle_report_path = output_root / BUNDLE_REPORT_FILENAME
    commands = [
        {
            "id": "target_area_contract_review",
            "label": "Frozen target-area contract review",
            "description": "Review the committed Tschamut target-area Balfrin contract without changing any artifact.",
            "command": command_string(["cat", display_path(contract_path)]),
            "execution_class": "runnable",
            "blocked_reason": "",
            "read_only": True,
            "may_produce_ignored_outputs": False,
            "expected_inputs": [display_path(contract_path)],
            "expected_outputs": ["YAML frozen target-area contract review"],
        },
        {
            "id": "materialize_target_area_handoff_bundle",
            "label": "Target-area handoff bundle materialization",
            "description": "Materialize the frozen target-area AOI handoff bundle into an ignored validation/private root.",
            "command": command_string(
                [
                    "PYENV_VERSION=system",
                    "uv",
                    "run",
                    "python",
                    display_path(ROOT / "scripts" / "generate_balfrin_target_area_demo_handoff.py"),
                    "--contract",
                    display_path(contract_path),
                    "--output-root",
                    display_path(output_root),
                    "--format",
                    "json",
                ]
            ),
            "execution_class": "template_only",
            "blocked_reason": "template_only_frozen_handoff_bundle",
            "read_only": False,
            "may_produce_ignored_outputs": True,
            "expected_inputs": [
                display_path(contract_path),
                display_path(target_gate_case_path),
            ],
            "expected_outputs": [
                str(materialized_case_path),
                str(command_manifest_path),
                str(expected_output_roots_path),
                str(scenario_generation_handoff_path),
                str(gis_scope_summary_path),
                str(bundle_report_path),
            ],
        },
    ]
    return {
        "schema_version": COMMAND_MANIFEST_SCHEMA_VERSION,
        "bundle_status": BUNDLE_STATUS,
        "target_area_id": "tschamut_public_pilot",
        "run_id": "tschamut_public_balfrin_target_area_demo_v1",
        "read_only": False,
        "scale_up_authorized": False,
        "distributed_execution_authorized": False,
        "operational_claims_allowed": False,
        "command_groups": [
            {
                "id": "target_area_handoff_review",
                "label": "Target-area handoff review",
                "status": "ready",
            },
            {
                "id": "target_area_handoff_materialization",
                "label": "Target-area handoff materialization",
                "status": "template_only",
            },
        ],
        "commands": commands,
        "command_ids": [command["id"] for command in commands],
        "command_descriptions": {command["id"]: command["description"] for command in commands},
        "blocked_template_commands": [command["id"] for command in commands if command["execution_class"] == "template_only"],
        "ignored_output_paths": [str(output_root)],
        "expected_output_paths": [
            str(materialized_case_path),
            str(command_manifest_path),
            str(expected_output_roots_path),
            str(scenario_generation_handoff_path),
            str(gis_scope_summary_path),
            str(bundle_report_path),
        ],
        "scenario_generation_handoff": scenario_generation_handoff,
        "gis_scope_summary": gis_scope_summary,
    }


def build_expected_output_roots(output_root: Path) -> list[str]:
    return [str(output_root), *IGNORED_TARGET_ROOTS]


def build_scenario_generation_handoff(
    *,
    contract_path: Path,
    target_area: dict[str, Any],
    input_freeze: dict[str, Any],
    boundary: dict[str, Any],
    reproduction_path: Path,
    target_gate_case_path: Path,
    execution_contract_path: Path,
    geodata_manifest_path: Path,
    source_zone_metadata_path: Path,
    scenario_table_path: Path,
    source_scenario_policy_path: Path,
    source_zone_metadata: dict[str, Any],
    scenario_rows: list[dict[str, str]],
    source_scenario_policy: dict[str, Any],
    reproduction_record: dict[str, Any],
    execution_contract: dict[str, Any],
    target_gate_case: dict[str, Any],
    output_root: Path,
) -> dict[str, Any]:
    scenario_table_generation_command = command_string(
        [
            "PYENV_VERSION=system",
            "uv",
            "run",
            "python",
            display_path(ROOT / "scripts" / "generate_balfrin_target_area_scenario_tables.py"),
            "--contract",
            display_path(contract_path),
            "--source-scenario-policy",
            display_path(source_scenario_policy_path),
            "--source-zone-metadata",
            display_path(source_zone_metadata_path),
            "--release-points",
            display_path(resolve_repo_path(input_freeze.get("release_points_csv"))),
            "--reference-scenario-table",
            display_path(scenario_table_path),
            "--output-root",
            display_path(output_root),
            "--format",
            "json",
        ]
    )
    return {
        "schema_version": SCENARIO_GENERATION_HANDOFF_SCHEMA_VERSION,
        "status": BUNDLE_STATUS,
        "summary": (
            "The frozen target-area contract keeps the Tschamut selected domain, source-zone metadata, scenario table, "
            "and source-scenario policy together as a template-only handoff."
        ),
        "contract_path": display_path(contract_path),
        "target_area_id": text_value(target_area.get("target_area_id"), "target_area.target_area_id"),
        "target_area_name": text_value(target_area.get("target_area_name"), "target_area.target_area_name"),
        "target_area_label": text_value(target_area.get("target_area_label"), "target_area.target_area_label"),
        "geodata_manifest_path": display_path(geodata_manifest_path),
        "target_gate_reproduction_record_path": display_path(reproduction_path),
        "target_gate_execution_contract_path": display_path(execution_contract_path),
        "target_gate_case_path": display_path(target_gate_case_path),
        "conditional_pilot_gate_path": display_path(resolve_repo_path(input_freeze.get("conditional_pilot_gate_path"))),
        "source_zone_metadata_path": display_path(source_zone_metadata_path),
        "scenario_table_path": display_path(scenario_table_path),
        "source_scenario_policy_path": display_path(source_scenario_policy_path),
        "scenario_family_basis": text_value(input_freeze.get("scenario_family_basis"), "input_freeze.scenario_family_basis"),
        "scenario_probability_semantics": text_value(
            input_freeze.get("scenario_probability_semantics"), "input_freeze.scenario_probability_semantics"
        ),
        "scenario_table_generation": {
            "command_id": "target_area_scenario_table_generation",
            "command": scenario_table_generation_command,
            "output_root": display_path(output_root),
            "scenario_table_csv": display_path(output_root / "tschamut_public_balfrin_target_area_demo_scenario_table.csv"),
            "scenario_manifest_json": display_path(
                output_root / "tschamut_public_balfrin_target_area_demo_scenario_manifest.json"
            ),
            "conditional_only_weighting": True,
            "source_zone_id": text_value(source_zone_metadata.get("source_zone_id"), "source_zone_metadata.source_zone_id"),
            "release_sampling_seed": source_zone_metadata.get("release_sampling_policy", {}).get("seed"),
            "scenario_id": (scenario_rows[0].get("scenario_id") if scenario_rows else None),
        },
        "target_gate_case_id": text_value(target_gate_case.get("case_id"), "target_gate_case.case_id"),
        "source_zone_id": text_value(source_zone_metadata.get("source_zone_id"), "source_zone_metadata.source_zone_id"),
        "source_zone_release_point_count": len(source_zone_metadata.get("release_points") or []),
        "scenario_table_row_count": len(scenario_rows),
        "source_scenario_policy_summary": {
            "source_zone_policy": source_scenario_policy.get("source_zone_policy", {}),
            "block_scenario_policy": source_scenario_policy.get("block_scenario_policy", {}),
            "claim_boundary": source_scenario_policy.get("claim_boundary", {}),
        },
        "reproduction_record": reproduction_record,
        "execution_contract": execution_contract,
        "template_only": True,
        "blocked_reason": "template_only_frozen_target_area_handoff",
        "command_plan_hook": boundary.get("command_plan_hook", {}),
    }


def build_gis_scope_summary(
    *,
    target_area: dict[str, Any],
    input_freeze: dict[str, Any],
    output_mode: dict[str, Any],
    boundary: dict[str, Any],
    claim_boundary: dict[str, Any],
    output_root: Path,
    target_gate_case_path: Path,
    target_gate_case_id: str,
    execution_contract: dict[str, Any],
    conditional_gate: dict[str, Any],
) -> dict[str, Any]:
    planned_products = [
        {
            "source": "frozen_target_area",
            "category": "target_area_boundary",
            "product": "target-area boundary and extent summary",
            "product_kind": "vector",
            "required": True,
            "current_status": "ready",
            "scope_state": "frozen_input",
            "expected_staged_path": text_value(target_area.get("geodata_manifest_path"), "target_area.geodata_manifest_path"),
        },
        {
            "source": "frozen_target_area",
            "category": "validation_case",
            "product": "target validation case YAML",
            "product_kind": "metadata",
            "required": True,
            "current_status": "ready",
            "scope_state": "frozen_input",
            "expected_staged_path": display_path(target_gate_case_path),
        },
        {
            "source": "frozen_target_area",
            "category": "validation_manifest",
            "product": "target validation manifest",
            "product_kind": "metadata",
            "required": True,
            "current_status": "template_only",
            "scope_state": "template_only",
            "expected_staged_path": "validation/private/tschamut_public_pilot/target_gate_v1/validation_tschamut_public_target_gate_v1_manifest.json",
        },
        {
            "source": "frozen_target_area",
            "category": "hazard_layers",
            "product": "target hazard layers and conditional curves",
            "product_kind": "raster",
            "required": True,
            "current_status": "template_only",
            "scope_state": "template_only",
            "expected_staged_path": "hazard/results/tschamut_public_pilot/target_gate_v1",
        },
        {
            "source": "frozen_target_area",
            "category": "pilot_gis_package",
            "product": "target pilot GIS package",
            "product_kind": "vector",
            "required": True,
            "current_status": "template_only",
            "scope_state": "template_only",
            "expected_staged_path": "hazard/results/tschamut_public_pilot/target_gate_v1/tschamut_public_scalable_conditional_target_gate_v1_pilot_gis_package_manifest.json",
        },
    ]
    cog_export_expectation = {
        "status": "template_only",
        "generated_now": False,
        "hazard_layers_generated": False,
        "cog_export_generated": False,
        "downstream_template_only_command_ids": ["materialize_target_area_handoff_bundle"],
        "summary": "The target-area handoff stops before hazard build; any GIS package or COG export remains a downstream template-only expectation.",
    }
    non_operational_gis_boundaries = {
        "operational_claims_allowed": False,
        "hazard_layers_generated": False,
        "cog_export_generated": False,
        "scale_up_authorized": False,
        "distributed_execution_authorized": False,
        "annual_frequency_claims_allowed": False,
        "physical_probability_claims_allowed": False,
        "risk_exposure_vulnerability_claims_allowed": False,
    }
    return {
        "schema_version": GIS_SCOPE_SUMMARY_SCHEMA_VERSION,
        "status": BUNDLE_STATUS,
        "summary": (
            "The frozen target-area case skeleton records planned GIS inputs separately from downstream template-only "
            "outputs and does not imply any hazard layers were generated."
        ),
        "planned_products": planned_products,
        "planned_raster_products": [product for product in planned_products if product.get("product_kind") == "raster"],
        "planned_vector_products": [product for product in planned_products if product.get("product_kind") == "vector"],
        "template_only_products": [
            {
                "category": "target_area_handoff_bundle",
                "product": "ignored target-area handoff bundle",
                "product_kind": "metadata",
                "scope_state": "template_only",
                "current_status": "not_generated",
                "expected_staged_path": display_path(output_root),
                "source": "bundle_generator",
            }
        ],
        "blocked_missing_inputs": [],
        "cog_export_expectation": cog_export_expectation,
        "non_operational_gis_boundaries": non_operational_gis_boundaries,
        "no_hazard_layers_generated": True,
        "output_mode": output_mode,
        "balfrin_execution_boundary": boundary,
        "claim_boundary": claim_boundary,
        "target_gate_case_id": target_gate_case_id,
        "conditional_gate_case_path": display_path(target_gate_case_path),
        "conditional_gate_summary": conditional_gate,
    }


def write_bundle_files(bundle: dict[str, Any]) -> None:
    output_root = Path(bundle["output_root"])
    output_root.mkdir(parents=True, exist_ok=True)
    case_skeleton = dict(bundle["case_skeleton_output"]["case_skeleton"])
    dump_yaml(output_root / CASE_FILENAME, case_skeleton)
    dump_json(output_root / COMMAND_MANIFEST_FILENAME, bundle["command_manifest"])
    dump_yaml(
        output_root / EXPECTED_OUTPUT_ROOTS_FILENAME,
        {
            "schema_version": EXPECTED_OUTPUT_ROOTS_SCHEMA_VERSION,
            "bundle_status": BUNDLE_STATUS,
            "expected_output_roots": bundle["expected_output_roots"],
        },
    )
    dump_json(output_root / SCENARIO_GENERATION_HANDOFF_FILENAME, bundle["scenario_generation_handoff"])
    dump_yaml(output_root / GIS_SCOPE_SUMMARY_FILENAME, bundle["gis_scope_summary"])
    dump_json(
        output_root / BUNDLE_REPORT_FILENAME,
        {
            "schema_version": SCHEMA_VERSION,
            "bundle_status": bundle["bundle_status"],
            "bundle_runnable_status": bundle["bundle_runnable_status"],
            "bundle_execution_boundary": bundle["bundle_execution_boundary"],
            "target_area_id": bundle["target_area_id"],
            "target_area_name": bundle["target_area_name"],
            "run_id": bundle["run_id"],
            "output_root": bundle["output_root"],
            "case_skeleton_path": bundle["case_skeleton_output"]["case_skeleton_path"],
            "command_manifest_path": bundle["case_skeleton_output"]["command_manifest_path"],
            "expected_output_roots_path": bundle["case_skeleton_output"]["expected_output_roots_path"],
            "scenario_generation_handoff_path": bundle["case_skeleton_output"]["scenario_generation_handoff_path"],
            "gis_scope_summary_path": bundle["case_skeleton_output"]["gis_scope_summary_path"],
            "blocked_reason": bundle["blocked_reason"],
            "scale_up_authorized": bundle["scale_up_authorized"],
            "distributed_execution_authorized": bundle["distributed_execution_authorized"],
            "operational_claims_allowed": bundle["operational_claims_allowed"],
        },
    )


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def dump_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def dump_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def require_mapping(value: Any, context: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TargetAreaHandoffError(f"{context} must be a YAML mapping")
    return value


def resolve_output_root(output_root: Path) -> Path:
    return output_root if output_root.is_absolute() else (ROOT / output_root)


def is_allowed_output_root(output_root: Path) -> bool:
    resolved = output_root.resolve()
    allowed_roots = [Path("/tmp").resolve(), DEFAULT_OUTPUT_ROOT.resolve()]
    return any(resolved.is_relative_to(root) for root in allowed_roots)


def resolve_repo_path(value: Any) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise TargetAreaHandoffError("missing required repository path value")
    path = Path(value)
    return path if path.is_absolute() else (ROOT / path)


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def text_value(value: Any, context: str) -> str:
    if value in (None, ""):
        raise TargetAreaHandoffError(f"{context} is missing")
    return str(value).strip()


def command_string(parts: list[str]) -> str:
    return shlex.join(parts)


def render_text_report(report: dict[str, Any]) -> str:
    lines = [
        f"schema_version: {report['schema_version']}",
        f"bundle_status: {report['bundle_status']}",
        f"bundle_runnable_status: {report['bundle_runnable_status']}",
        f"bundle_execution_boundary: {report['bundle_execution_boundary']}",
        f"target_area_id: {report['target_area_id']}",
        f"target_area_name: {report['target_area_name']}",
        f"run_id: {report['run_id']}",
        f"output_root: {report['output_root']}",
        "",
        "case_skeleton_output:",
    ]
    case_output = report["case_skeleton_output"]
    for key in (
        "schema_version",
        "status",
        "write_status",
        "case_skeleton_path",
        "command_manifest_path",
        "expected_output_roots_path",
        "scenario_generation_handoff_path",
        "gis_scope_summary_path",
        "bundle_report_path",
    ):
        lines.append(f"- {key}: {case_output[key]}")
    lines.append("")
    lines.append("scenario_generation_handoff:")
    lines.extend(render_nested_dict(report["scenario_generation_handoff"]))
    lines.append("")
    lines.append("gis_scope_summary:")
    lines.extend(render_nested_dict(report["gis_scope_summary"]))
    return "\n".join(lines)


def render_nested_dict(mapping: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    for key, value in mapping.items():
        if isinstance(value, dict):
            lines.append(f"- {key}:")
            for subkey, subvalue in value.items():
                lines.append(f"  - {subkey}: {subvalue}")
        elif isinstance(value, list):
            lines.append(f"- {key}:")
            if not value:
                lines.append("  - []")
            for item in value:
                if isinstance(item, dict):
                    lines.append("  -")
                    for subkey, subvalue in item.items():
                        lines.append(f"    - {subkey}: {subvalue}")
                else:
                    lines.append(f"  - {item}")
        else:
            lines.append(f"- {key}: {value}")
    return lines


if __name__ == "__main__":
    raise SystemExit(main())
