#!/usr/bin/env python3
"""Plan the large Balfrin single-release-zone case without executing it.

This helper stays at the dry-run boundary. It reads the frozen public Tschamut
source-zone metadata, the committed scenario table, the conditional policy, and
the reduced-output fixture contract, then emits a deterministic report that
names the large single-zone case inputs, the validation output mode, and the
output roots that must remain ignored. It does not create a validation case,
run a simulation, or authorize scale-up.
"""

from __future__ import annotations

import argparse
import csv
import json
import shlex
import sys
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except ImportError as exc:  # pragma: no cover - environment setup.
    raise SystemExit("PyYAML is required. Run this script with `PYENV_VERSION=system uv run python ...`; CI may use `requirements-tools.txt`") from exc


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "balfrin_single_release_zone_case_plan_dry_run_v1"
DEFAULT_CONTRACT = ROOT / "validation/pilot_runs/tschamut_public_balfrin_single_release_zone_pilot_contract_v1.yaml"
DEFAULT_POLICY = ROOT / "validation/policies/tschamut_public_source_scenario_policy_v1.yaml"
DEFAULT_SOURCE_ZONE_METADATA = ROOT / "data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_source_zone_metadata_v1.yaml"
DEFAULT_SCENARIO_TABLE = ROOT / "data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_scenario_table_v1.csv"
DEFAULT_REDUCED_OUTPUT_CASE = ROOT / "tests/fixtures/rebuildable_reduced_output/tschamut_public_target_gate_rebuildable_reduced_case.yaml"

PLANNED_CASE_OUTPUT_ROOT = ROOT / "validation/private/tschamut_public_pilot/balfrin_single_release_zone_v1"
PLANNED_HAZARD_OUTPUT_ROOT = ROOT / "hazard/results/tschamut_public_pilot/balfrin_single_release_zone_v1"

REPO_GENERATED_OUTPUT_ROOTS_TO_AVOID = [
    "data/processed/swisstopo/placeholder_second_site_v1",
    "validation/private/placeholder_second_site_v1",
    "hazard/results/placeholder_second_site_v1",
    "validation/policies/*placeholder*",
    "verification/results/",
    "validation/results/",
    "hazard/results/",
    "target/",
]


class BalfrinSingleReleaseZoneCasePlanError(ValueError):
    """User-facing dry-run planner error."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("--source-zone-metadata", type=Path, default=DEFAULT_SOURCE_ZONE_METADATA)
    parser.add_argument("--scenario-table", type=Path, default=DEFAULT_SCENARIO_TABLE)
    parser.add_argument("--reduced-output-case", type=Path, default=DEFAULT_REDUCED_OUTPUT_CASE)
    args = parser.parse_args(argv)

    try:
        report = build_report(
            contract_path=args.contract,
            policy_path=args.policy,
            source_zone_metadata_path=args.source_zone_metadata,
            scenario_table_path=args.scenario_table,
            reduced_output_case_path=args.reduced_output_case,
        )
    except BalfrinSingleReleaseZoneCasePlanError as exc:
        print(f"balfrin single-release-zone case plan error: {exc}", file=sys.stderr)
        return 2

    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text_report(report))
    return 0 if report["case_plan_status"] == "ready" else 2


def build_report(
    *,
    contract_path: Path = DEFAULT_CONTRACT,
    policy_path: Path = DEFAULT_POLICY,
    source_zone_metadata_path: Path = DEFAULT_SOURCE_ZONE_METADATA,
    scenario_table_path: Path = DEFAULT_SCENARIO_TABLE,
    reduced_output_case_path: Path = DEFAULT_REDUCED_OUTPUT_CASE,
) -> dict[str, Any]:
    required_inputs = [
        contract_path,
        policy_path,
        source_zone_metadata_path,
        scenario_table_path,
        reduced_output_case_path,
    ]
    missing = [display_path(path) for path in required_inputs if not path.exists()]
    if missing:
        raise BalfrinSingleReleaseZoneCasePlanError(
            "required committed inputs are missing: " + ", ".join(missing)
        )

    contract = load_yaml(contract_path)
    policy = load_yaml(policy_path)
    source_zone_metadata = load_yaml(source_zone_metadata_path)
    scenario_rows = load_csv_rows(scenario_table_path)
    reduced_output_case = load_yaml(reduced_output_case_path)

    validation_output = contract.get("validation_output", {})
    release_zone_scope = contract.get("release_zone_scope", {})
    balfrin_resource_assumptions = contract.get("balfrin_resource_assumptions", {})
    no_go_boundaries = contract.get("no_go_boundaries", [])

    source_zone_id = text_value(source_zone_metadata, "source_zone_id")
    policy_source_zone_id = text_value(policy, "source_zone_policy.source_zone_id")
    if source_zone_id != policy_source_zone_id:
        raise BalfrinSingleReleaseZoneCasePlanError(
            f"source zone mismatch between metadata ({source_zone_id!r}) and policy ({policy_source_zone_id!r})"
        )

    release_sampling = policy.get("source_zone_policy", {}).get("release_sampling", {})
    block_scenarios = policy.get("block_scenario_policy", {}).get("scenarios", [])
    deterministic_evidence = {
        "source_zone_id": source_zone_id,
        "release_sampling_seed": release_sampling.get("seed"),
        "release_cell_id_prefix": release_sampling.get("release_cell_id_prefix"),
        "release_cell_count": release_zone_scope.get("release_cell_count")
        or source_zone_metadata.get("release_sampling_policy", {}).get("release_count"),
        "trajectory_count_target": release_zone_scope.get("trajectory_count_target"),
        "trajectories_per_release_cell": release_zone_scope.get("trajectories_per_release_cell"),
        "release_zone_count": release_zone_scope.get("release_zone_count"),
        "scenario_table_row_count": len(scenario_rows),
        "scenario_table_row_ids": [row.get("scenario_id") for row in scenario_rows],
        "policy_block_scenario_count": len(block_scenarios),
        "policy_block_scenario_ids": [
            text_value(block_scenario, "block_scenario_id") for block_scenario in block_scenarios
        ],
        "validation_output_mode": text_value(reduced_output_case, "outputs.validation_output_mode"),
        "selection_rule": (
            "frozen public Tschamut source-zone metadata + committed scenario table + "
            "policy block scenarios + rebuildable-reduced fixture; no simulation execution"
        ),
    }

    report = {
        "schema_version": SCHEMA_VERSION,
        "case_plan_status": "ready",
        "case_execution_status": "blocked_template_only",
        "read_only": True,
        "scale_up_authorized": False,
        "distributed_execution_authorized": False,
        "operational_claims_allowed": False,
        "pilot_id": contract.get("pilot_id", "tschamut_public_pilot"),
        "run_id": contract.get(
            "run_id",
            "tschamut_public_balfrin_single_release_zone_pilot_contract_v1",
        ),
        "case_plan_title": "Balfrin single-release-zone large case plan",
        "source_inputs": {
            "contract_path": display_path(contract_path),
            "source_scenario_policy_path": display_path(policy_path),
            "source_zone_metadata_path": display_path(source_zone_metadata_path),
            "scenario_table_path": display_path(scenario_table_path),
            "reduced_output_case_path": display_path(reduced_output_case_path),
        },
        "source_zone_record": {
            "source_zone_id": source_zone_id,
            "crs_epsg": source_zone_metadata.get("crs_epsg"),
            "vertical_datum": source_zone_metadata.get("vertical_datum"),
            "release_sampling_policy": source_zone_metadata.get("release_sampling_policy", {}),
            "provenance": source_zone_metadata.get("provenance", {}),
        },
        "scenario_table_rows": scenario_rows,
        "policy_block_scenario_policy": policy.get("block_scenario_policy", {}),
        "release_zone_scope": {
            "release_zone_count": release_zone_scope.get("release_zone_count"),
            "release_cell_count": release_zone_scope.get("release_cell_count"),
            "trajectory_count_target": release_zone_scope.get("trajectory_count_target"),
            "trajectories_per_release_cell": release_zone_scope.get("trajectories_per_release_cell"),
            "block_scenario_count": release_zone_scope.get("block_scenario_count"),
            "block_scenario_policy": release_zone_scope.get("block_scenario_policy"),
        },
        "validation_output": {
            "validation_output_mode": text_value(reduced_output_case, "outputs.validation_output_mode"),
            "hazard_output_profile": validation_output.get("hazard_output_profile"),
            "conditional_curve_export": validation_output.get("conditional_curve_export"),
            "grid_csv_export": validation_output.get("grid_csv_export"),
            "export_geotiff": validation_output.get("export_geotiff"),
            "pilot_gis_package": validation_output.get("pilot_gis_package"),
        },
        "expected_artifact_families": contract.get("expected_artifact_families", []),
        "hazard_layer_products": contract.get("hazard_layer_products", []),
        "balfrin_resource_assumptions": {
            "execution_boundary": balfrin_resource_assumptions.get("execution_boundary"),
            "trajectory_workers": balfrin_resource_assumptions.get("trajectory_workers"),
            "reducer_workers": balfrin_resource_assumptions.get("reducer_workers"),
            "explicit_grid_required": balfrin_resource_assumptions.get("explicit_grid_required"),
            "distributed_execution_authorized": balfrin_resource_assumptions.get(
                "distributed_execution_authorized"
            ),
            "generated_outputs_committed": balfrin_resource_assumptions.get("generated_outputs_committed"),
            "single_job_boundary": balfrin_resource_assumptions.get("single_job_boundary"),
        },
        "no_go_boundaries": list(no_go_boundaries),
        "planned_case_output_roots": [
            display_path(PLANNED_CASE_OUTPUT_ROOT),
            display_path(PLANNED_HAZARD_OUTPUT_ROOT),
        ],
        "ignored_output_roots": list(REPO_GENERATED_OUTPUT_ROOTS_TO_AVOID),
        "deterministic_generation_evidence": deterministic_evidence,
        "blocked_case_execution_template": {
            "status": "template_only",
            "command_id": "balfrin_single_release_zone_case_execution_template",
            "command": command_string(
                [
                    "PYENV_VERSION=system",
                    "CARGO_TARGET_DIR=/tmp/rust-rockfall-target",
                    "cargo",
                    "run",
                    "--",
                    "validate",
                    "--case",
                    display_path(
                        PLANNED_CASE_OUTPUT_ROOT
                        / "tschamut_public_balfrin_single_release_zone_case.yaml"
                    ),
                ]
            ),
            "expected_outputs": [
                display_path(
                    PLANNED_CASE_OUTPUT_ROOT / "tschamut_public_balfrin_single_release_zone_case.yaml"
                ),
                display_path(
                    PLANNED_CASE_OUTPUT_ROOT
                    / "validation_tschamut_public_balfrin_single_release_zone_manifest.json"
                ),
            ],
            "blocked_reason": (
                "dry-run only; the large Balfrin single-release-zone case is not executed from this helper"
            ),
        },
        "claim_boundaries": {
            "unsupported_current_claims": list(no_go_boundaries),
            "notes": [
                "conditional sampling weights are not physical probabilities",
                "the frozen public source-zone and scenario records are planning inputs, not validation evidence",
                "no operational, annual-frequency, risk, exposure, or vulnerability claim is authorized here",
            ],
        },
        "blocked_reason": "dry-run only",
    }
    return report


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - file context matters for users.
        raise BalfrinSingleReleaseZoneCasePlanError(f"failed to read YAML {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise BalfrinSingleReleaseZoneCasePlanError(f"expected YAML mapping in {path}")
    return data


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    try:
        with path.open(newline="", encoding="utf-8") as file:
            return list(csv.DictReader(file))
    except Exception as exc:  # noqa: BLE001 - file context matters for users.
        raise BalfrinSingleReleaseZoneCasePlanError(f"failed to read CSV {path}: {exc}") from exc


def text_value(data: dict[str, Any], dotted_path: str) -> Any:
    current: Any = data
    for part in dotted_path.split("."):
        if not isinstance(current, dict) or part not in current:
            raise BalfrinSingleReleaseZoneCasePlanError(f"missing required field {dotted_path}")
        current = current[part]
    return current


def command_string(parts: list[str]) -> str:
    return shlex.join(parts)


def display_path(path: Path) -> str:
    if path.is_absolute():
        try:
            return str(path.relative_to(ROOT))
        except ValueError:
            return str(path)
    return str(path)


def render_text_report(report: dict[str, Any]) -> str:
    lines = [
        "Balfrin Single-Release-Zone Case Plan Dry Run",
        "",
        f"- Case plan status: `{report['case_plan_status']}`",
        f"- Case execution status: `{report['case_execution_status']}`",
        f"- Read only: `{report['read_only']}`",
        f"- Scale-up authorized: `{report['scale_up_authorized']}`",
        f"- Distributed execution authorized: `{report['distributed_execution_authorized']}`",
        f"- Operational claims allowed: `{report['operational_claims_allowed']}`",
        f"- Validation output mode: `{report['validation_output']['validation_output_mode']}`",
        "",
        "## Deterministic Evidence",
        "",
        f"- Source zone id: `{report['deterministic_generation_evidence']['source_zone_id']}`",
        f"- Release sampling seed: `{report['deterministic_generation_evidence']['release_sampling_seed']}`",
        f"- Release cell count: `{report['deterministic_generation_evidence']['release_cell_count']}`",
        f"- Trajectory-count target: `{report['deterministic_generation_evidence']['trajectory_count_target']}`",
        f"- Trajectories per release cell: `{report['deterministic_generation_evidence']['trajectories_per_release_cell']}`",
        f"- Block scenario count: `{report['deterministic_generation_evidence']['policy_block_scenario_count']}`",
        "",
        "## Ignored Roots",
        "",
    ]
    for root in report["ignored_output_roots"]:
        lines.append(f"- `{root}`")
    lines.extend(["", "## Planned Case Roots", ""])
    for root in report["planned_case_output_roots"]:
        lines.append(f"- `{root}`")
    lines.extend(
        [
            "",
            "## Blocked Execution Template",
            "",
            f"- Command id: `{report['blocked_case_execution_template']['command_id']}`",
            f"- Status: `{report['blocked_case_execution_template']['status']}`",
            f"- Command: `{report['blocked_case_execution_template']['command']}`",
            f"- Blocked reason: `{report['blocked_case_execution_template']['blocked_reason']}`",
        ]
    )
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
