#!/usr/bin/env python3
"""Generate a deterministic stress-test scenario table from release candidates.

This helper stays at the dry-run boundary. It consumes candidate release-point
rows from a release-points CSV, expands them across the frozen Tschamut
conditional block-family policy, and writes a manifest-rich scenario table into
scratch roots. It does not run ensembles, fit probabilities, tune parameters,
or introduce annual-frequency or physical-probability semantics.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except ImportError as exc:  # pragma: no cover - environment setup.
    raise SystemExit("PyYAML is required. Run this script with `PYENV_VERSION=system uv run python ...`; CI may use `requirements-tools.txt`") from exc

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from lib.workflow_validation import (
    build_release_candidate_physical_meaning_firewall,
    build_release_zone_provenance_intake,
    validate_release_candidate_physical_meaning_firewall,
)


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "candidate_source_zone_scenario_stress_test_v1"
MANIFEST_SCHEMA_VERSION = "candidate_source_zone_scenario_stress_test_manifest_v1"
FREEZER_SCHEMA_VERSION = "reviewed_candidate_source_zone_freezer_v1"
FREEZER_MANIFEST_SCHEMA_VERSION = "reviewed_candidate_source_zone_freezer_manifest_v1"
DEFAULT_POLICY = ROOT / "validation/policies/tschamut_public_source_scenario_policy_v1.yaml"
DEFAULT_RELEASE_POINTS = ROOT / "data/processed/swisstopo/tschamut_public_pilot/input/release_points_lv95.csv"
DEFAULT_OUTPUT_ROOT = Path("/tmp/rust_rockfall_tb182_candidate_source_zone_scenarios")
DEFAULT_TEMPLATE_IDS = ("candidate_release_point_summary_v1", "policy_block_family_v1")
DEFAULT_CANDIDATE_REPEAT_COUNT = 8
DEFAULT_FREEZER_TRAJECTORY_COUNT = 60
DEFAULT_FREEZER_SEED = 34014
SCENARIO_TABLE_FILENAME = "candidate_source_zone_scenario_table.csv"
SCENARIO_MANIFEST_FILENAME = "candidate_source_zone_scenario_manifest.json"
STRESS_REPORT_FILENAME = "candidate_source_zone_scenario_stress_report.json"
FREEZER_SOURCE_ZONE_METADATA_FILENAME = "source_zone_metadata.yaml"
FREEZER_RELEASE_ROWS_FILENAME = "release_rows.csv"
FREEZER_SCENARIO_TABLE_FILENAME = "scenario_table.csv"
FREEZER_POLICY_FILENAME = "source_scenario_policy.yaml"
FREEZER_MANIFEST_FILENAME = "reviewed_candidate_source_zone_freezer_manifest.json"
FREEZER_RELEASE_ROWS_COLUMNS = [
    "release_row_id",
    "candidate_release_zone_id",
    "source_zone_id",
    "release_order",
    "accepted",
    "rejected",
    "review_decision",
    "release_cell_id",
    "release_cell_center_lv95_m",
    "release_cell_count",
    "release_cell_ids",
    "candidate_sensitivity_label",
    "provenance_label",
    "trajectory_count",
    "seed_policy",
    "conditional_weight",
    "annual_frequency_per_year",
    "time_horizon_years",
]
FREEZER_SCENARIO_TABLE_COLUMNS = [
    "scenario_id",
    "candidate_release_zone_id",
    "release_row_id",
    "source_zone_id",
    "block_family_id",
    "block_scenario_id",
    "block_size_class",
    "block_shape_class",
    "block_radius_m",
    "block_mass_kg",
    "trajectory_count",
    "seed_policy",
    "conditional_weight",
    "sampling_weight",
    "release_probability",
    "scenario_probability",
    "annual_frequency_per_year",
    "time_horizon_years",
]
SCENARIO_TABLE_COLUMNS = [
    "scenario_id",
    "candidate_release_zone_record_id",
    "candidate_repeat_index",
    "release_point_id",
    "source_zone_id",
    "source_zone_family_id",
    "scenario_family_template_id",
    "block_family_id",
    "block_scenario_id",
    "block_size_class",
    "block_shape_class",
    "release_point_mass_kg",
    "release_point_radius_m",
    "block_radius_m",
    "block_mass_kg",
    "sampling_weight",
    "normalized_sampling_share",
    "release_probability",
    "scenario_probability",
    "annual_frequency_per_year",
    "time_horizon_years",
]
SUPPORTED_TEMPLATES = {
    "candidate_release_point_summary_v1": "one row per deterministic candidate release point",
    "policy_block_family_v1": "one row per frozen Tschamut block-family scenario",
}
DEFAULT_FREEZER_BLOCK_SCENARIOS = [
    {
        "block_scenario_id": "reviewed_block_small",
        "block_family_id": "reviewed_block_family_small",
        "block_size_class": "reviewed_small",
        "block_shape_class": "sphere",
        "block_radius_m": 0.16,
        "block_mass_kg": 40.0,
        "sampling_weight": 3.0,
    },
    {
        "block_scenario_id": "reviewed_block_medium",
        "block_family_id": "reviewed_block_family_medium",
        "block_size_class": "reviewed_medium",
        "block_shape_class": "sphere",
        "block_radius_m": 0.176667,
        "block_mass_kg": 69.0,
        "sampling_weight": 5.0,
    },
    {
        "block_scenario_id": "reviewed_block_large",
        "block_family_id": "reviewed_block_family_large",
        "block_size_class": "reviewed_large",
        "block_shape_class": "sphere",
        "block_radius_m": 0.198333,
        "block_mass_kg": 79.0,
        "sampling_weight": 2.0,
    },
]


class CandidateSourceZoneScenarioStressError(ValueError):
    """User-facing candidate scenario stress generation error."""


class CandidateSourceZoneFreezerError(ValueError):
    """User-facing candidate source-zone freezer error."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("stress", "freeze"), default="stress")
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("--release-points", type=Path, default=DEFAULT_RELEASE_POINTS)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--candidate-repeat-count", type=int, default=DEFAULT_CANDIDATE_REPEAT_COUNT)
    parser.add_argument(
        "--template-ids",
        default=",".join(DEFAULT_TEMPLATE_IDS),
        help="Comma-separated scenario-family template ids to include.",
    )
    parser.add_argument("--review-package", type=Path, default=None)
    parser.add_argument(
        "--accepted-candidate-ids",
        default="",
        help="Comma-separated candidate_release_zone_id values to freeze.",
    )
    parser.add_argument("--trajectory-count", type=int, default=DEFAULT_FREEZER_TRAJECTORY_COUNT)
    parser.add_argument("--seed", type=int, default=DEFAULT_FREEZER_SEED)
    parser.add_argument("--source-zone-metadata-output", type=Path, default=None)
    parser.add_argument("--release-rows-output", type=Path, default=None)
    parser.add_argument("--scenario-table-output", type=Path, default=None)
    parser.add_argument("--policy-output", type=Path, default=None)
    parser.add_argument("--manifest-output", type=Path, default=None)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    args = parser.parse_args(argv)

    try:
        if args.mode == "freeze":
            report = build_freezer_report(
                review_package_path=args.review_package,
                accepted_candidate_ids=parse_candidate_ids(args.accepted_candidate_ids),
                output_root=args.output_root,
                trajectory_count=args.trajectory_count,
                seed=args.seed,
                source_zone_metadata_output=args.source_zone_metadata_output,
                release_rows_output=args.release_rows_output,
                scenario_table_output=args.scenario_table_output,
                policy_output=args.policy_output,
                manifest_output=args.manifest_output,
            )
        else:
            report = build_report(
                policy_path=args.policy,
                release_points_path=args.release_points,
                output_root=args.output_root,
                candidate_repeat_count=args.candidate_repeat_count,
                template_ids=parse_template_ids(args.template_ids),
            )
    except (CandidateSourceZoneScenarioStressError, CandidateSourceZoneFreezerError) as exc:
        print(f"candidate source-zone scenario error: {exc}", file=sys.stderr)
        return 2

    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text_report(report) if args.mode == "stress" else render_freezer_text_report(report))
    if args.mode == "stress":
        return 0 if report["stress_test_status"] == "ready" else 2
    return 0 if report["freezer_status"] == "ready" else 2


def build_report(
    *,
    policy_path: Path = DEFAULT_POLICY,
    release_points_path: Path = DEFAULT_RELEASE_POINTS,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    candidate_repeat_count: int = DEFAULT_CANDIDATE_REPEAT_COUNT,
    template_ids: list[str] | tuple[str, ...] = DEFAULT_TEMPLATE_IDS,
) -> dict[str, Any]:
    template_ids = parse_template_ids(template_ids)
    required_inputs = [policy_path, release_points_path]
    missing_inputs = [display_path(path) for path in required_inputs if not path.exists()]
    if missing_inputs:
        return blocked_report(
            missing_inputs,
            policy_path=policy_path,
            release_points_path=release_points_path,
            output_root=output_root,
            candidate_repeat_count=candidate_repeat_count,
            template_ids=template_ids,
            blocked_reason="required candidate release-zone inputs are missing",
        )

    if candidate_repeat_count < 1:
        raise CandidateSourceZoneScenarioStressError("candidate-repeat-count must be at least 1")

    build_started = time.perf_counter()
    policy = load_yaml(policy_path)
    release_points = load_csv_rows(release_points_path)
    block_scenarios = load_block_scenarios(policy)
    output_root = resolve_output_root(output_root)

    if not is_allowed_output_root(output_root):
        raise CandidateSourceZoneScenarioStressError(
            f"output-root must stay under /tmp or an ignored repo root: {output_root}"
        )

    candidate_records = build_candidate_release_zone_records(
        release_points=release_points,
        release_points_path=release_points_path,
        candidate_repeat_count=candidate_repeat_count,
        source_zone_id=text_value(get_nested_value(policy, ("source_zone_policy", "source_zone_id"))) or "tschamut_public_source_zone",
    )
    rows = build_rows(
        candidate_records=candidate_records,
        block_scenarios=block_scenarios,
        template_ids=template_ids,
        policy=policy,
    )
    normalize_row_shares(rows)
    release_candidate_firewall = build_release_candidate_firewall(candidate_records=candidate_records, rows=rows)

    manifest = build_manifest(
        policy=policy,
        policy_path=policy_path,
        release_points_path=release_points_path,
        output_root=output_root,
        candidate_records=candidate_records,
        rows=rows,
        block_scenarios=block_scenarios,
        template_ids=template_ids,
        release_candidate_firewall=release_candidate_firewall,
    )
    build_seconds = time.perf_counter() - build_started

    scenario_table_output_path = output_root / SCENARIO_TABLE_FILENAME
    scenario_manifest_output_path = output_root / SCENARIO_MANIFEST_FILENAME
    report_output_path = output_root / STRESS_REPORT_FILENAME
    write_started = time.perf_counter()
    scenario_table_output_path.parent.mkdir(parents=True, exist_ok=True)
    write_csv(scenario_table_output_path, rows)
    scenario_manifest_output_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_seconds = time.perf_counter() - write_started

    csv_bytes = scenario_table_output_path.stat().st_size
    manifest_bytes = scenario_manifest_output_path.stat().st_size
    total_bytes = csv_bytes + manifest_bytes
    first_scaling_bottleneck = build_first_scaling_bottleneck(
        csv_bytes=csv_bytes,
        manifest_bytes=manifest_bytes,
        row_count=len(rows),
        candidate_record_count=len(candidate_records),
        block_family_count=len(block_scenarios),
        template_count=len(template_ids),
    )
    runtime_measurements = {
        "build_seconds": round(build_seconds, 6),
        "write_seconds": round(write_seconds, 6),
        "total_seconds": round(build_seconds + write_seconds, 6),
    }
    storage_measurements = {
        "csv_bytes": csv_bytes,
        "manifest_bytes": manifest_bytes,
        "total_bytes": total_bytes,
    }
    tb_183_planning_input = build_tb_183_planning_input(
        candidate_record_count=len(candidate_records),
        row_count=len(rows),
        block_family_count=len(block_scenarios),
        template_count=len(template_ids),
    )

    report = {
        "schema_version": SCHEMA_VERSION,
        "stress_test_status": "ready",
        "blocked_reason": None,
        "read_only": True,
        "scale_up_authorized": False,
        "operational_claims_allowed": False,
        "template_ids": list(template_ids),
        "candidate_repeat_count": candidate_repeat_count,
        "candidate_release_zone_record_count": len(candidate_records),
        "scenario_row_count": len(rows),
        "generated_scenario_table_rows": rows,
        "scenario_table_manifest": manifest,
        "release_candidate_physical_meaning_firewall": release_candidate_firewall,
        "runtime_measurements": runtime_measurements,
        "storage_measurements": storage_measurements,
        "first_scaling_bottleneck": first_scaling_bottleneck,
        "tb_183_planning_input": tb_183_planning_input,
        "output_paths": {
            "scenario_table_csv": display_path(scenario_table_output_path),
            "scenario_table_manifest_json": display_path(scenario_manifest_output_path),
            "stress_report_json": display_path(report_output_path),
        },
    }
    report_output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def blocked_report(
    missing_inputs: list[str],
    *,
    policy_path: Path,
    release_points_path: Path,
    output_root: Path,
    candidate_repeat_count: int,
    template_ids: list[str],
    blocked_reason: str,
) -> dict[str, Any]:
    output_root = resolve_output_root(output_root)
    scenario_table_output_path = output_root / SCENARIO_TABLE_FILENAME
    scenario_manifest_output_path = output_root / SCENARIO_MANIFEST_FILENAME
    report_output_path = output_root / STRESS_REPORT_FILENAME
    return {
        "schema_version": SCHEMA_VERSION,
        "stress_test_status": "blocked_missing_inputs",
        "blocked_reason": blocked_reason,
        "read_only": True,
        "scale_up_authorized": False,
        "operational_claims_allowed": False,
        "template_ids": list(template_ids),
        "candidate_repeat_count": candidate_repeat_count,
        "candidate_release_zone_record_count": 0,
        "scenario_row_count": 0,
        "release_candidate_physical_meaning_firewall": {
            "firewall_status": "blocked_missing_provenance",
            "release_candidate_provenance_state": "blocked_missing_provenance",
            "release_candidate_provenance_state_counts": {
                "workflow_generated": 0,
                "field_supported": 0,
                "mixed_provenance": 0,
                "blocked_missing_provenance": 0,
            },
            "release_candidate_provenance_profile": [],
            "sampling_weight_semantics": "conditional_sampling_only",
            "sampling_weight_boundary": "not occurrence probability, physical probability, annual frequency, return period, or risk",
            "sampling_weight_not_occurrence_probability": True,
            "sampling_weight_not_physical_probability": True,
            "sampling_weight_not_annual_frequency": True,
            "sampling_weight_not_return_period": True,
            "sampling_weight_not_risk": True,
            "physical_probability_claims_allowed": False,
            "annual_frequency_claims_allowed": False,
            "return_period_claims_allowed": False,
            "risk_claims_allowed": False,
            "scenario_row_provenance_profile": [],
            "scenario_row_count": 0,
        },
        "scenario_table_manifest": {
            "schema_version": MANIFEST_SCHEMA_VERSION,
            "table_status": "blocked_missing_inputs",
            "blocked_reason": blocked_reason,
            "missing_inputs": sorted(set(missing_inputs)),
            "candidate_release_zone_record_count": 0,
            "scenario_row_count": 0,
            "row_ids": [],
            "candidate_cardinality": [],
            "source_zone_family_cardinality": [],
            "block_family_cardinality": [],
            "scenario_family_template_cardinality": [],
            "first_scaling_bottleneck": {
                "name": "unavailable",
                "reason": blocked_reason,
            },
            "source_inputs": {
                "policy_path": display_path(policy_path),
                "release_points_path": display_path(release_points_path),
            },
            "supported_templates": template_summary(template_ids),
            "release_candidate_physical_meaning_firewall": {
                "firewall_status": "blocked_missing_provenance",
                "release_candidate_provenance_state": "blocked_missing_provenance",
                "release_candidate_provenance_state_counts": {
                    "workflow_generated": 0,
                    "field_supported": 0,
                    "mixed_provenance": 0,
                    "blocked_missing_provenance": 0,
                },
                "release_candidate_provenance_profile": [],
                "sampling_weight_semantics": "conditional_sampling_only",
                "sampling_weight_boundary": "not occurrence probability, physical probability, annual frequency, return period, or risk",
                "sampling_weight_not_occurrence_probability": True,
                "sampling_weight_not_physical_probability": True,
                "sampling_weight_not_annual_frequency": True,
                "sampling_weight_not_return_period": True,
                "sampling_weight_not_risk": True,
                "physical_probability_claims_allowed": False,
                "annual_frequency_claims_allowed": False,
                "return_period_claims_allowed": False,
                "risk_claims_allowed": False,
                "scenario_row_provenance_profile": [],
                "scenario_row_count": 0,
            },
        },
        "runtime_measurements": {
            "build_seconds": 0.0,
            "write_seconds": 0.0,
            "total_seconds": 0.0,
        },
        "storage_measurements": {
            "csv_bytes": 0,
            "manifest_bytes": 0,
            "total_bytes": 0,
        },
        "first_scaling_bottleneck": {
            "name": "unavailable",
            "reason": blocked_reason,
        },
        "tb_183_planning_input": {
            "status": "blocked_missing_inputs",
            "reason": blocked_reason,
            "candidate_release_zone_record_count": 0,
            "scenario_row_count": 0,
            "block_family_count": 0,
            "scenario_family_template_count": len(template_ids),
        },
        "output_paths": {
            "scenario_table_csv": display_path(scenario_table_output_path),
            "scenario_table_manifest_json": display_path(scenario_manifest_output_path),
            "stress_report_json": display_path(report_output_path),
        },
    }


def build_candidate_release_zone_records(
    *,
    release_points: list[dict[str, str]],
    release_points_path: Path,
    candidate_repeat_count: int,
    source_zone_id: str,
    release_zone_provenance_intake: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for repeat_index in range(candidate_repeat_count):
        for source_index, row in enumerate(release_points, start=1):
            release_point_id = text_value(row.get("trajectory_id")) or f"release_point_{source_index:03d}"
            block_id = text_value(row.get("block_id"))
            family_id = f"release_block_{block_id}" if block_id else "release_block_unknown"
            candidate_release_zone_record_id = (
                release_point_id if candidate_repeat_count == 1 else f"{release_point_id}__repeat_{repeat_index:03d}"
            )
            intake = build_release_zone_provenance_intake(
                release_zone_provenance_intake,
                workflow_generated=True if release_zone_provenance_intake is None else None,
                field_supported=False if release_zone_provenance_intake is None else None,
                blocked_missing_provenance=False if release_zone_provenance_intake is None else None,
                provenance_note="deterministic release-point CSV expansion",
                provenance_source=display_path(release_points_path),
            )
            records.append(
                {
                    "candidate_release_zone_record_id": candidate_release_zone_record_id,
                    "candidate_repeat_index": repeat_index,
                    "candidate_release_zone_record_index": len(records) + 1,
                    "release_point_id": release_point_id,
                    "source_zone_id": source_zone_id,
                    "source_zone_family_id": family_id,
                    "release_point_block_id": block_id,
                    "release_point_mass_kg": parse_float(row.get("mass_kg")),
                    "release_point_radius_m": parse_float(row.get("radius_m")),
                    "release_point_source_path": display_path(release_points_path),
                    "release_point_source_row_index": source_index,
                    "source_record_kind": "release_point_candidate",
                    "release_zone_provenance_intake": intake,
                    "candidate_release_zone_record_kind": intake["release_candidate_provenance_state"],
                    "workflow_generated": bool(intake["workflow_generated"]),
                    "field_supported": bool(intake["field_supported"]),
                    "blocked_missing_provenance": bool(intake["blocked_missing_provenance"]),
                    "release_candidate_provenance_state": intake["release_candidate_provenance_state"],
                    "provenance_note": intake["provenance_note"],
                }
            )
    return records


def build_rows(
    *,
    candidate_records: list[dict[str, Any]],
    block_scenarios: list[dict[str, Any]],
    template_ids: list[str],
    policy: dict[str, Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    policy_prefix = policy_root_prefix(policy)
    for candidate_record in candidate_records:
        candidate_id = text_value(candidate_record.get("candidate_release_zone_record_id"))
        source_zone_id = text_value(candidate_record.get("source_zone_id"))
        release_point_id = text_value(candidate_record.get("release_point_id"))
        source_zone_family_id = text_value(candidate_record.get("source_zone_family_id"))
        repeat_index = candidate_record.get("candidate_repeat_index")
        provenance_state = candidate_record.get(
            "release_candidate_provenance_state",
            candidate_record.get("candidate_release_zone_record_kind", "workflow_generated"),
        )

        for template_id in template_ids:
            if template_id == "candidate_release_point_summary_v1":
                rows.append(
                    {
                        "scenario_id": f"{candidate_id}__candidate_release_point_summary",
                        "candidate_release_zone_record_id": candidate_id,
                        "candidate_repeat_index": repeat_index,
                        "release_point_id": release_point_id,
                        "source_zone_id": source_zone_id,
                        "source_zone_family_id": source_zone_family_id,
                        "scenario_family_template_id": template_id,
                        "block_family_id": "candidate_release_point_summary",
                        "block_scenario_id": f"{policy_prefix}_candidate_release_point_summary",
                        "block_size_class": "candidate_release_point_summary",
                        "block_shape_class": "",
                        "release_point_mass_kg": candidate_record.get("release_point_mass_kg"),
                        "release_point_radius_m": candidate_record.get("release_point_radius_m"),
                        "block_radius_m": "",
                        "block_mass_kg": "",
                        "sampling_weight": 1.0,
                        "normalized_sampling_share": None,
                        "release_probability": "",
                        "scenario_probability": "",
                        "annual_frequency_per_year": "",
                        "time_horizon_years": "",
                        "release_candidate_provenance_state": provenance_state,
                    }
                )
                continue

            if template_id == "policy_block_family_v1":
                for block_scenario in block_scenarios:
                    block_family_id = text_value(block_scenario.get("block_size_class")) or text_value(
                        block_scenario.get("block_scenario_id")
                    )
                    rows.append(
                        {
                            "scenario_id": f"{candidate_id}__{text_value(block_scenario.get('block_scenario_id'))}",
                            "candidate_release_zone_record_id": candidate_id,
                            "candidate_repeat_index": repeat_index,
                            "release_point_id": release_point_id,
                            "source_zone_id": source_zone_id,
                            "source_zone_family_id": source_zone_family_id,
                            "scenario_family_template_id": template_id,
                            "block_family_id": block_family_id,
                            "block_scenario_id": text_value(block_scenario.get("block_scenario_id")),
                            "block_size_class": text_value(block_scenario.get("block_size_class")),
                            "block_shape_class": text_value(block_scenario.get("block_shape_class")),
                            "release_point_mass_kg": candidate_record.get("release_point_mass_kg"),
                            "release_point_radius_m": candidate_record.get("release_point_radius_m"),
                            "block_radius_m": block_scenario.get("block_radius_m"),
                            "block_mass_kg": block_scenario.get("block_mass_kg"),
                            "sampling_weight": float(block_scenario.get("sampling_weight") or 0.0),
                            "normalized_sampling_share": None,
                            "release_probability": "",
                            "scenario_probability": "",
                            "annual_frequency_per_year": "",
                            "time_horizon_years": "",
                            "release_candidate_provenance_state": provenance_state,
                        }
                    )
                continue

            raise CandidateSourceZoneScenarioStressError(f"unsupported scenario-family template: {template_id}")
    return rows


def normalize_row_shares(rows: list[dict[str, Any]]) -> None:
    total_weight = sum(float(row.get("sampling_weight") or 0.0) for row in rows)
    for row in rows:
        row["normalized_sampling_share"] = round(float(row.get("sampling_weight") or 0.0) / total_weight, 6) if total_weight else None


def build_manifest(
    *,
    policy: dict[str, Any],
    policy_path: Path,
    release_points_path: Path,
    output_root: Path,
    candidate_records: list[dict[str, Any]],
    rows: list[dict[str, Any]],
    block_scenarios: list[dict[str, Any]],
    template_ids: list[str],
    release_candidate_firewall: dict[str, Any] | None = None,
) -> dict[str, Any]:
    candidate_cardinality = summarize_candidate_cardinality(candidate_records, rows, template_ids, block_scenarios)
    source_zone_family_cardinality = summarize_group_cardinality(rows, "source_zone_family_id")
    block_family_cardinality = summarize_group_cardinality(rows, "block_family_id")
    scenario_family_template_cardinality = summarize_group_cardinality(rows, "scenario_family_template_id")
    row_summaries = [
        {
            "row_id": text_value(row.get("scenario_id")),
            "candidate_release_zone_record_id": text_value(row.get("candidate_release_zone_record_id")),
            "source_zone_family_id": text_value(row.get("source_zone_family_id")),
            "scenario_family_template_id": text_value(row.get("scenario_family_template_id")),
            "block_family_id": text_value(row.get("block_family_id")),
            "sampling_weight": row.get("sampling_weight"),
            "normalized_sampling_share": row.get("normalized_sampling_share"),
            "release_candidate_provenance_state": text_value(row.get("release_candidate_provenance_state")),
        }
        for row in rows
    ]
    first_scaling_bottleneck = build_first_scaling_bottleneck(
        csv_bytes=None,
        manifest_bytes=None,
        row_count=len(rows),
        candidate_record_count=len(candidate_records),
        block_family_count=len(block_scenarios),
        template_count=len(template_ids),
    )
    return {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "table_status": "ready",
        "candidate_repeat_count": candidate_repeat_count_from_records(candidate_records),
        "candidate_release_zone_record_count": len(candidate_records),
        "scenario_row_count": len(rows),
        "candidate_release_zone_record_ids": [text_value(candidate.get("candidate_release_zone_record_id")) for candidate in candidate_records],
        "source_zone_family_ids": sorted({text_value(candidate.get("source_zone_family_id")) for candidate in candidate_records}),
        "block_family_ids": sorted({text_value(item.get("block_size_class")) or text_value(item.get("block_scenario_id")) for item in block_scenarios}),
        "scenario_family_template_ids": list(template_ids),
        "row_ids": [text_value(row.get("scenario_id")) for row in rows],
        "candidate_cardinality": candidate_cardinality,
        "source_zone_family_cardinality": source_zone_family_cardinality,
        "block_family_cardinality": block_family_cardinality,
        "scenario_family_template_cardinality": scenario_family_template_cardinality,
        "row_summaries": row_summaries,
        "conditional_weighting_semantics": {
            "sampling_weight_semantics": "conditional_sampling_only",
            "scenario_probability_semantics": "normalized within a block family; not occurrence probability, physical probability, annual frequency, return period, or risk",
            "sampling_weights_are_not_physical_probability": True,
            "sampling_weights_are_not_annual_frequency": True,
            "conditional_only_weighting": True,
        },
        "release_candidate_physical_meaning_firewall": release_candidate_firewall
        or build_release_candidate_firewall(candidate_records=candidate_records, rows=rows),
        "first_scaling_bottleneck": first_scaling_bottleneck,
        "tb_183_planning_input": build_tb_183_planning_input(
            candidate_record_count=len(candidate_records),
            row_count=len(rows),
            block_family_count=len(block_scenarios),
            template_count=len(template_ids),
        ),
        "source_inputs": {
            "policy_path": display_path(policy_path),
            "release_points_path": display_path(release_points_path),
            "output_root": display_path(output_root),
        },
        "supported_templates": template_summary(template_ids),
        "read_only": True,
        "scale_up_authorized": False,
        "operational_claims_allowed": False,
    }


def summarize_candidate_cardinality(
    candidate_records: list[dict[str, Any]],
    rows: list[dict[str, Any]],
    template_ids: list[str],
    block_scenarios: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows_by_candidate: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        candidate_id = text_value(row.get("candidate_release_zone_record_id"))
        rows_by_candidate.setdefault(candidate_id, []).append(row)

    summaries: list[dict[str, Any]] = []
    for candidate in candidate_records:
        candidate_id = text_value(candidate.get("candidate_release_zone_record_id"))
        candidate_rows = rows_by_candidate.get(candidate_id, [])
        summaries.append(
            {
                "candidate_release_zone_record_id": candidate_id,
                "candidate_repeat_index": candidate.get("candidate_repeat_index"),
                "source_zone_family_id": text_value(candidate.get("source_zone_family_id")),
                "release_point_id": text_value(candidate.get("release_point_id")),
                "row_count": len(candidate_rows),
                "template_count": len({text_value(row.get("scenario_family_template_id")) for row in candidate_rows}),
                "block_family_count": len({text_value(row.get("block_family_id")) for row in candidate_rows}),
            }
        )
    return summaries


def summarize_group_cardinality(rows: list[dict[str, Any]], field_name: str) -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    for row in rows:
        key = text_value(row.get(field_name))
        counts[key] = counts.get(key, 0) + 1
    return [
        {"group_id": group_id, "row_count": count}
        for group_id, count in sorted(counts.items(), key=lambda item: item[0])
    ]


def build_first_scaling_bottleneck(
    *,
    csv_bytes: int | None,
    manifest_bytes: int | None,
    row_count: int,
    candidate_record_count: int,
    block_family_count: int,
    template_count: int,
) -> dict[str, Any]:
    if manifest_bytes is not None and csv_bytes is not None and manifest_bytes >= csv_bytes:
        return {
            "name": "manifest_size",
            "reason": "row-level provenance summaries and candidate cardinality trees make the manifest grow faster than the CSV",
            "measured_driver": "manifest_bytes",
            "csv_bytes": csv_bytes,
            "manifest_bytes": manifest_bytes,
        }
    if row_count >= candidate_record_count * block_family_count * template_count:
        return {
            "name": "row_fan_out",
            "reason": "candidate-by-template-by-block fan-out dominates row growth once release candidates are expanded",
            "measured_driver": "row_count",
            "row_count": row_count,
            "candidate_release_zone_record_count": candidate_record_count,
            "block_family_count": block_family_count,
            "template_count": template_count,
        }
    return {
        "name": "candidate_fan_out",
        "reason": "candidate release-zone multiplicity is the first non-constant multiplier in the scenario table",
        "measured_driver": "candidate_release_zone_record_count",
        "candidate_release_zone_record_count": candidate_record_count,
        "block_family_count": block_family_count,
        "template_count": template_count,
    }


def build_tb_183_planning_input(
    *,
    candidate_record_count: int,
    row_count: int,
    block_family_count: int,
    template_count: int,
) -> dict[str, Any]:
    ready = candidate_record_count > 0 and row_count > 0 and block_family_count > 0 and template_count > 0
    return {
        "status": "ready" if ready else "blocked_missing_inputs",
        "reason": "deterministic candidate release rows, block families, and scenario-family templates are present" if ready else "planning input is incomplete",
        "candidate_release_zone_record_count": candidate_record_count,
        "scenario_row_count": row_count,
        "block_family_count": block_family_count,
        "scenario_family_template_count": template_count,
        "ready_for_tb_183": ready,
    }


def normalize_candidate_ids(candidate_ids: list[str] | tuple[str, ...]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for candidate_id in candidate_ids:
        token = text_value(candidate_id)
        if not token or token in seen:
            continue
        seen.add(token)
        normalized.append(token)
    return normalized


def parse_candidate_ids(value: str | list[str] | tuple[str, ...]) -> list[str]:
    if isinstance(value, (list, tuple)):
        return normalize_candidate_ids([text_value(item) for item in value])
    return normalize_candidate_ids([item.strip() for item in value.split(",") if item.strip()])


def normalize_freezer_block_scenarios(block_scenarios: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    ids: set[str] = set()
    total_weight = 0.0
    for index, scenario in enumerate(block_scenarios, start=1):
        if not isinstance(scenario, dict):
            raise CandidateSourceZoneFreezerError(f"block scenario {index} must be a mapping")
        block_scenario_id = text_value(scenario.get("block_scenario_id"))
        if not block_scenario_id:
            raise CandidateSourceZoneFreezerError(f"block scenario {index} must define block_scenario_id")
        if block_scenario_id in ids:
            raise CandidateSourceZoneFreezerError(f"duplicate block_scenario_id: {block_scenario_id}")
        block_size_class = text_value(scenario.get("block_size_class"))
        block_shape_class = text_value(scenario.get("block_shape_class")) or "sphere"
        block_family_id = text_value(scenario.get("block_family_id")) or block_size_class or block_scenario_id
        block_radius_m = scenario.get("block_radius_m")
        block_mass_kg = scenario.get("block_mass_kg")
        sampling_weight = scenario.get("sampling_weight")
        try:
            weight = float(sampling_weight)
        except (TypeError, ValueError) as exc:
            raise CandidateSourceZoneFreezerError(f"block scenario {block_scenario_id} sampling_weight must be numeric") from exc
        if not (weight == weight and weight not in (float("inf"), float("-inf"))):
            raise CandidateSourceZoneFreezerError(f"block scenario {block_scenario_id} sampling_weight must be finite")
        if weight < 0.0:
            raise CandidateSourceZoneFreezerError(f"block scenario {block_scenario_id} sampling_weight must be nonnegative")
        total_weight += weight
        ids.add(block_scenario_id)
        normalized.append(
            {
                "block_scenario_id": block_scenario_id,
                "block_family_id": block_family_id,
                "block_size_class": block_size_class or block_family_id,
                "block_shape_class": block_shape_class,
                "block_radius_m": block_radius_m,
                "block_mass_kg": block_mass_kg,
                "sampling_weight": weight,
            }
        )
    if total_weight <= 0.0:
        raise CandidateSourceZoneFreezerError("conditional block-scenario weights must sum to a positive value")
    return normalized


def build_freezer_source_zone_geometry(
    review_package_path: Path,
    review_package: dict[str, Any],
    accepted_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    accepted_ids = {text_value(row.get("candidate_release_zone_id")) for row in accepted_rows}
    candidate_geojson_path = review_package.get("outputs", {}).get("polygon")
    features: list[dict[str, Any]] = []
    if isinstance(candidate_geojson_path, str) and candidate_geojson_path.strip():
        geojson_path = repo_path(candidate_geojson_path)
        if geojson_path.exists():
            payload = load_yaml_or_json(geojson_path)
            raw_features = payload.get("features", [])
            if isinstance(raw_features, list):
                for feature in raw_features:
                    if isinstance(feature, dict):
                        feature_id = text_value((feature.get("properties") or {}).get("candidate_release_zone_id"))
                        if accepted_ids and feature_id not in accepted_ids:
                            continue
                        features.append(feature)
    if not features:
        for row in accepted_rows:
            bbox = row.get("component_bbox_lv95_m")
            if isinstance(bbox, dict):
                features.append(
                    {
                        "properties": {"candidate_release_zone_id": text_value(row.get("candidate_release_zone_id"))},
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [
                                [
                                    [bbox.get("xmin", 0.0), bbox.get("ymin", 0.0)],
                                    [bbox.get("xmax", 0.0), bbox.get("ymin", 0.0)],
                                    [bbox.get("xmax", 0.0), bbox.get("ymax", 0.0)],
                                    [bbox.get("xmin", 0.0), bbox.get("ymax", 0.0)],
                                    [bbox.get("xmin", 0.0), bbox.get("ymin", 0.0)],
                                ]
                            ],
                        },
                    }
                )
    bounds = collect_feature_bounds(features)
    return {
        "type": "polygon",
        "coordinates": [
            [bounds["xmin"], bounds["ymin"]],
            [bounds["xmax"], bounds["ymin"]],
            [bounds["xmax"], bounds["ymax"]],
            [bounds["xmin"], bounds["ymax"]],
        ],
    }


def collect_feature_bounds(features: list[dict[str, Any]]) -> dict[str, float]:
    xs: list[float] = []
    ys: list[float] = []
    for feature in features:
        geometry = feature.get("geometry")
        if not isinstance(geometry, dict):
            continue
        for x, y in geometry_coordinates(geometry):
            xs.append(x)
            ys.append(y)
    if not xs or not ys:
        raise CandidateSourceZoneFreezerError("review package polygon geometry is required to freeze a source zone")
    return {"xmin": min(xs), "ymin": min(ys), "xmax": max(xs), "ymax": max(ys)}


def geometry_coordinates(geometry: dict[str, Any]) -> list[tuple[float, float]]:
    coordinates: list[tuple[float, float]] = []
    geometry_type = text_value(geometry.get("type")).lower()
    raw_coordinates = geometry.get("coordinates")
    if geometry_type == "polygon" and isinstance(raw_coordinates, list):
        if raw_coordinates and isinstance(raw_coordinates[0], (list, tuple)) and len(raw_coordinates[0]) >= 2 and isinstance(raw_coordinates[0][0], (int, float)):
            for point in raw_coordinates:
                if isinstance(point, (list, tuple)) and len(point) >= 2:
                    coordinates.append((float(point[0]), float(point[1])))
        else:
            rings = raw_coordinates
            for ring in rings:
                if not isinstance(ring, list):
                    continue
                for point in ring:
                    if isinstance(point, (list, tuple)) and len(point) >= 2:
                        coordinates.append((float(point[0]), float(point[1])))
    elif geometry_type == "multipolygon" and isinstance(raw_coordinates, list):
        for polygon in raw_coordinates:
            if not isinstance(polygon, list):
                continue
            for ring in polygon:
                if not isinstance(ring, list):
                    continue
                for point in ring:
                    if isinstance(point, (list, tuple)) and len(point) >= 2:
                        coordinates.append((float(point[0]), float(point[1])))
    return coordinates


def build_freezer_release_cells(
    source_zone_id: str,
    accepted_rows: list[dict[str, Any]],
    geometry: dict[str, Any],
) -> list[dict[str, Any]]:
    bounds = source_zone_bounds(geometry)
    release_cells: list[dict[str, Any]] = []
    for index, row in enumerate(accepted_rows, start=1):
        candidate_id = text_value(row.get("candidate_release_zone_id"))
        row_bounds = row.get("component_bbox_lv95_m")
        if isinstance(row_bounds, dict):
            cx = (float(row_bounds.get("xmin", 0.0)) + float(row_bounds.get("xmax", 0.0))) / 2.0
            cy = (float(row_bounds.get("ymin", 0.0)) + float(row_bounds.get("ymax", 0.0))) / 2.0
        else:
            cx = (bounds["xmin"] + bounds["xmax"]) / 2.0
            cy = (bounds["ymin"] + bounds["ymax"]) / 2.0
        release_cells.append(
            {
                "release_cell_id": f"{source_zone_id}_release_cell_{index:03d}",
                "candidate_release_zone_id": candidate_id,
                "center_lv95_m": [round(cx, 6), round(cy, 6)],
                "sampling_weight": 1.0,
            }
        )
    return release_cells


def source_zone_bounds(geometry: dict[str, Any]) -> dict[str, float]:
    coordinates = geometry_coordinates(geometry)
    if not coordinates:
        raise CandidateSourceZoneFreezerError("source zone geometry is required")
    xs = [x for x, _ in coordinates]
    ys = [y for _, y in coordinates]
    return {"xmin": min(xs), "ymin": min(ys), "xmax": max(xs), "ymax": max(ys)}


def build_freezer_source_zone_metadata(
    *,
    source_zone_id: str,
    candidate_site_id: str,
    candidate_site_name: str,
    review_package_path: Path,
    review_package: dict[str, Any],
    accepted_ids: list[str],
    rejected_ids: list[str],
    release_cells: list[dict[str, Any]],
    trajectory_count: int,
    seed: int,
    geometry: dict[str, Any],
) -> dict[str, Any]:
    bounds = source_zone_bounds(geometry)
    polygon_vertices = [
        [bounds["xmin"], bounds["ymin"]],
        [bounds["xmax"], bounds["ymin"]],
        [bounds["xmax"], bounds["ymax"]],
        [bounds["xmin"], bounds["ymax"]],
    ]
    return {
        "schema_version": "source_zone_metadata_v1",
        "source_zone_id": source_zone_id,
        "candidate_site_id": candidate_site_id,
        "candidate_site_name": candidate_site_name,
        "freeze_mode": FREEZER_SCHEMA_VERSION,
        "source_review_package_path": display_path(review_package_path),
        "accepted_candidate_ids": accepted_ids,
        "rejected_candidate_ids": rejected_ids,
        "accepted_candidate_count": len(accepted_ids),
        "rejected_candidate_count": len(rejected_ids),
        "trajectory_count_target": trajectory_count,
        "seed_policy": "fixed_integer_recorded_before_simulation",
        "seed": seed,
        "geometry": {
            "type": "polygon",
            "vertices": polygon_vertices,
        },
        "release_sampling_policy": {
            "mode": "deterministic_grid",
            "seed_policy": "fixed_integer_recorded_before_simulation",
            "seed": seed,
            "release_cell_id_prefix": f"{source_zone_id}_release_cell",
            "release_count": len(release_cells),
            "trajectory_count_target": trajectory_count,
            "sampling_weight_semantics": "conditional_sampling_only",
        },
        "provenance": {
            "source": text_value(review_package.get("candidate_selection_rationale")) or "reviewed candidate freeze package",
            "notes": [
                "reviewed candidate ids are frozen into deterministic conditional planning rows",
                "annual-frequency, physical probability, and operational claims remain out of scope",
            ],
        },
        "annual_release_frequency_per_year": None,
    }


def build_freezer_release_rows(
    *,
    source_zone_id: str,
    accepted_rows: list[dict[str, Any]],
    release_cells: list[dict[str, Any]],
    trajectory_count: int,
    seed: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(accepted_rows, start=1):
        candidate_id = text_value(row.get("candidate_release_zone_id"))
        release_cell = release_cells[index - 1]
        release_cell_count = row.get("release_cell_count")
        if not isinstance(release_cell_count, int):
            release_cell_ids = text_value(row.get("release_cell_ids"))
            release_cell_count = len(release_cell_ids.split(";")) if release_cell_ids else 0
        rows.append(
            {
                "release_row_id": f"{source_zone_id}__release_row_{index:03d}",
                "candidate_release_zone_id": candidate_id,
                "source_zone_id": source_zone_id,
                "release_order": index,
                "accepted": bool(row.get("accepted")),
                "rejected": bool(row.get("rejected")),
                "review_decision": text_value(row.get("review_decision")),
                "release_cell_id": text_value(release_cell.get("release_cell_id")),
                "release_cell_center_lv95_m": release_cell.get("center_lv95_m"),
                "release_cell_count": int(release_cell_count),
                "release_cell_ids": text_value(row.get("release_cell_ids")),
                "candidate_sensitivity_label": text_value(row.get("candidate_sensitivity_label")),
                "provenance_label": text_value(row.get("provenance_label")),
                "trajectory_count": trajectory_count,
                "seed_policy": "fixed_integer_recorded_before_simulation",
                "conditional_weight": 1.0,
                "annual_frequency_per_year": "",
                "time_horizon_years": "",
                "seed": seed,
            }
        )
    return rows


def build_freezer_scenario_rows(
    *,
    source_zone_id: str,
    release_rows: list[dict[str, Any]],
    block_scenarios: list[dict[str, Any]],
    trajectory_count: int,
    seed: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for release_row in release_rows:
        for block_scenario in block_scenarios:
            scenario_id = f"{release_row['release_row_id']}__{block_scenario['block_scenario_id']}"
            weight = float(block_scenario["sampling_weight"])
            rows.append(
                {
                    "scenario_id": scenario_id,
                    "candidate_release_zone_id": release_row["candidate_release_zone_id"],
                    "release_row_id": release_row["release_row_id"],
                    "source_zone_id": source_zone_id,
                    "block_family_id": text_value(block_scenario.get("block_family_id")) or text_value(block_scenario.get("block_size_class")),
                    "block_scenario_id": text_value(block_scenario.get("block_scenario_id")),
                    "block_size_class": text_value(block_scenario.get("block_size_class")),
                    "block_shape_class": text_value(block_scenario.get("block_shape_class")) or "sphere",
                    "block_radius_m": block_scenario.get("block_radius_m"),
                    "block_mass_kg": block_scenario.get("block_mass_kg"),
                    "trajectory_count": trajectory_count,
                    "seed_policy": "fixed_integer_recorded_before_simulation",
                    "conditional_weight": weight,
                    "sampling_weight": weight,
                    "release_probability": "",
                    "scenario_probability": "",
                    "annual_frequency_per_year": "",
                    "time_horizon_years": "",
                    "seed": seed,
                }
            )
    return rows


def build_freezer_policy(
    *,
    site_id: str,
    candidate_site_name: str,
    source_zone_id: str,
    review_package_path: Path,
    review_package: dict[str, Any],
    accepted_ids: list[str],
    rejected_ids: list[str],
    release_cells: list[dict[str, Any]],
    block_scenarios: list[dict[str, Any]],
    trajectory_count: int,
    seed: int,
    geometry: dict[str, Any],
) -> dict[str, Any]:
    policy = load_yaml(ROOT / "validation/templates/public_real_site_source_scenario_policy_v1.yaml")
    policy["policy_id"] = f"{site_id}_source_scenario_policy_v1"
    policy["pilot_id"] = site_id
    policy["policy_status"] = "ready_for_conditional_pilot"
    policy["operational_status"] = "research_diagnostic"
    policy.setdefault("validation_maturity_target", "V1_preparation_fixture")

    source_zone_policy = policy.setdefault("source_zone_policy", {})
    source_zone_policy["source_zone_id"] = source_zone_id
    source_zone_policy["geometry_status"] = "reviewed_candidate_freeze"
    source_zone_policy["geometry"] = geometry
    source_zone_policy.setdefault("evidence_level", "level1_manual_real_site_interpretation")
    source_zone_policy.setdefault("allowed_geometry_type", "polygon")
    source_zone_policy["derivation_criteria"] = {
        "status": "reviewed_candidate_freeze",
        "slope_threshold_degrees": None,
        "geology_or_material_filter": None,
        "inventory_or_expert_review": "reviewed candidate ids frozen into deterministic conditional planning rows",
        "manual_interpretation_notes": text_value(review_package.get("candidate_selection_rationale"))
        or "reviewed candidate source-zone freeze",
    }
    source_zone_policy["release_sampling"] = {
        "mode": "deterministic_grid",
        "seed_policy": "fixed_integer_recorded_before_simulation",
        "seed": seed,
        "release_cell_id_policy": "stable_source_zone_prefixed_ids",
        "release_cell_id_prefix": f"{source_zone_id}_release_cell",
        "requested_release_cell_count": len(release_cells),
        "sampling_weight_semantics": "conditional_sampling_only",
        "physical_release_probability_supported": False,
        "annual_source_frequency_supported": False,
        "trajectory_count_target": trajectory_count,
        "release_cells": [
            {
                "release_cell_id": text_value(cell.get("release_cell_id")),
                "center_lv95_m": cell.get("center_lv95_m"),
                "sampling_weight": cell.get("sampling_weight"),
            }
            for cell in release_cells
        ],
    }

    block_policy = policy.setdefault("block_scenario_policy", {})
    block_policy["block_population_status"] = "representative_scenarios_not_physical_population"
    block_policy["active_shape_physics_supported"] = False
    block_policy["sampling_weight_semantics"] = "conditional_sampling_only"
    block_policy["trajectory_count_target"] = trajectory_count
    block_policy["scenarios"] = [
        {
            "block_scenario_id": text_value(scenario.get("block_scenario_id")),
            "block_family_id": text_value(scenario.get("block_family_id")) or text_value(scenario.get("block_size_class")),
            "block_size_class": text_value(scenario.get("block_size_class")),
            "block_shape_class": text_value(scenario.get("block_shape_class")) or "sphere",
            "block_radius_m": scenario.get("block_radius_m"),
            "block_mass_kg": scenario.get("block_mass_kg"),
            "sampling_weight": float(scenario.get("sampling_weight") or 0.0),
            "trajectory_count_target": trajectory_count,
            "conditional_weight": float(scenario.get("sampling_weight") or 0.0),
        }
        for scenario in block_scenarios
    ]

    claim_boundary = policy.setdefault("claim_boundary", {})
    claim_boundary["current_allowed_products"] = [
        "unweighted_diagnostic",
        "sampling_weighted_conditional",
        "conditional_intensity_exceedance",
    ]
    claim_boundary["unsupported_current_claims"] = [
        "annual_frequency",
        "return_period",
        "physical_probability",
        "risk_map",
        "operational_hazard_map",
        "validated_hazard_map",
    ]
    claim_boundary["notes"] = [
        "reviewed candidate source-zone choices are input assumptions, not validation evidence by themselves",
        "release-cell and block-scenario sampling weights are conditional sampling weights, not physical probabilities",
        "this policy supports a research diagnostic conditional pilot only, not an operational source-zone approval",
        "source-zone review rows are not validation evidence",
        "sampling weights are not physical probability",
    ]

    policy["freeze_controls"] = {
        "freeze_mode": FREEZER_SCHEMA_VERSION,
        "review_package_path": display_path(review_package_path),
        "accepted_candidate_ids": accepted_ids,
        "rejected_candidate_ids": rejected_ids,
        "trajectory_count": trajectory_count,
        "seed_policy": "fixed_integer_recorded_before_simulation",
        "seed": seed,
        "block_family_ids": [text_value(scenario.get("block_family_id")) or text_value(scenario.get("block_size_class")) for scenario in block_scenarios],
        "conditional_weight_total": sum(float(scenario.get("sampling_weight") or 0.0) for scenario in block_scenarios),
    }
    return policy


def write_freezer_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh, lineterminator="\n")
        writer.writerow(columns)
        for row in rows:
            writer.writerow([csv_value(row.get(column)) for column in columns])


def build_release_candidate_firewall(
    *,
    candidate_records: list[dict[str, Any]],
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    firewall = build_release_candidate_physical_meaning_firewall(candidate_records)
    firewall["scenario_row_provenance_profile"] = [
        {
            "row_id": text_value(row.get("scenario_id")),
            "candidate_release_zone_record_id": text_value(row.get("candidate_release_zone_record_id")),
            "release_candidate_provenance_state": text_value(row.get("release_candidate_provenance_state")),
            "sampling_weight": row.get("sampling_weight"),
            "normalized_sampling_share": row.get("normalized_sampling_share"),
            "sampling_weight_semantics": "conditional_sampling_only",
            "sampling_weight_boundary": "not occurrence probability, physical probability, annual frequency, return period, or risk",
        }
        for row in rows
    ]
    firewall["scenario_row_count"] = len(rows)
    validate_release_candidate_physical_meaning_firewall(firewall, error_cls=CandidateSourceZoneScenarioStressError)
    return firewall


def build_freezer_report(
    *,
    review_package_path: Path | None,
    accepted_candidate_ids: list[str] | None,
    output_root: Path,
    trajectory_count: int,
    seed: int,
    source_zone_metadata_output: Path | None = None,
    release_rows_output: Path | None = None,
    scenario_table_output: Path | None = None,
    policy_output: Path | None = None,
    manifest_output: Path | None = None,
    block_scenarios: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if review_package_path is None:
        raise CandidateSourceZoneFreezerError("review-package is required in freeze mode")

    review_package_path = review_package_path.resolve(strict=False)
    if not review_package_path.exists():
        raise CandidateSourceZoneFreezerError(f"missing review package: {display_path(review_package_path)}")

    output_root = resolve_output_root(output_root)
    if not is_allowed_output_root(output_root):
        raise CandidateSourceZoneFreezerError(f"output-root must stay under /tmp or an ignored repo root: {output_root}")

    review_package = load_yaml_or_json(review_package_path)
    review_rows = review_package.get("candidate_review_rows", [])
    if not isinstance(review_rows, list):
        raise CandidateSourceZoneFreezerError("review package candidate_review_rows must be a list")

    review_rows_by_id: dict[str, dict[str, Any]] = {}
    review_order: list[str] = []
    for row in review_rows:
        if not isinstance(row, dict):
            continue
        candidate_id = text_value(row.get("candidate_release_zone_id"))
        if not candidate_id:
            continue
        if candidate_id in review_rows_by_id:
            raise CandidateSourceZoneFreezerError(f"duplicate candidate_release_zone_id in review package: {candidate_id}")
        review_rows_by_id[candidate_id] = row
        review_order.append(candidate_id)

    explicit_ids = normalize_candidate_ids(accepted_candidate_ids) if accepted_candidate_ids is not None else []
    if explicit_ids:
        missing_ids = [candidate_id for candidate_id in explicit_ids if candidate_id not in review_rows_by_id]
        if missing_ids:
            raise CandidateSourceZoneFreezerError("accepted candidate ids not found in review package: " + ", ".join(missing_ids))
        explicit_id_set = set(explicit_ids)
        accepted_ids = [candidate_id for candidate_id in review_order if candidate_id in explicit_id_set]
        rejected_selection = [
            candidate_id
            for candidate_id in accepted_ids
            if not bool(review_rows_by_id[candidate_id].get("accepted"))
            and text_value(review_rows_by_id[candidate_id].get("review_decision")) != "accepted"
        ]
        if rejected_selection:
            raise CandidateSourceZoneFreezerError(
                "explicit accepted candidate ids must be review-decisions accepted: " + ", ".join(rejected_selection)
            )
    else:
        accepted_ids = [
            candidate_id
            for candidate_id in review_order
            if bool(review_rows_by_id[candidate_id].get("accepted"))
            or text_value(review_rows_by_id[candidate_id].get("review_decision")) == "accepted"
        ]

    if not accepted_ids:
        raise CandidateSourceZoneFreezerError("no accepted candidate ids were selected")

    accepted_rows = [review_rows_by_id[candidate_id] for candidate_id in accepted_ids]
    rejected_ids = [candidate_id for candidate_id in review_order if candidate_id not in accepted_ids]
    source_zone_id = text_value(review_package.get("source_zone_id")) or text_value(review_package.get("candidate_site_id")) or "reviewed_source_zone"
    site_id = text_value(review_package.get("candidate_site_id")) or source_zone_id
    candidate_site_name = text_value(review_package.get("candidate_site_name")) or site_id
    source_zone_geometry = build_freezer_source_zone_geometry(review_package_path, review_package, accepted_rows)
    block_scenarios = normalize_freezer_block_scenarios(block_scenarios or DEFAULT_FREEZER_BLOCK_SCENARIOS)
    conditional_weight_total = sum(float(scenario.get("sampling_weight") or 0.0) for scenario in block_scenarios)
    if conditional_weight_total <= 0.0:
        raise CandidateSourceZoneFreezerError("conditional block-scenario weights must sum to a positive value")

    release_cells = build_freezer_release_cells(source_zone_id, accepted_rows, source_zone_geometry)
    source_zone_metadata = build_freezer_source_zone_metadata(
        source_zone_id=source_zone_id,
        candidate_site_id=site_id,
        candidate_site_name=candidate_site_name,
        review_package_path=review_package_path,
        review_package=review_package,
        accepted_ids=accepted_ids,
        rejected_ids=rejected_ids,
        release_cells=release_cells,
        trajectory_count=trajectory_count,
        seed=seed,
        geometry=source_zone_geometry,
    )
    release_rows = build_freezer_release_rows(
        source_zone_id=source_zone_id,
        accepted_rows=accepted_rows,
        release_cells=release_cells,
        trajectory_count=trajectory_count,
        seed=seed,
    )
    scenario_rows = build_freezer_scenario_rows(
        source_zone_id=source_zone_id,
        release_rows=release_rows,
        block_scenarios=block_scenarios,
        trajectory_count=trajectory_count,
        seed=seed,
    )
    policy = build_freezer_policy(
        site_id=site_id,
        candidate_site_name=candidate_site_name,
        source_zone_id=source_zone_id,
        review_package_path=review_package_path,
        review_package=review_package,
        accepted_ids=accepted_ids,
        rejected_ids=rejected_ids,
        release_cells=release_cells,
        block_scenarios=block_scenarios,
        trajectory_count=trajectory_count,
        seed=seed,
        geometry=source_zone_geometry,
    )

    source_zone_metadata_output = source_zone_metadata_output or (output_root / FREEZER_SOURCE_ZONE_METADATA_FILENAME)
    release_rows_output = release_rows_output or (output_root / FREEZER_RELEASE_ROWS_FILENAME)
    scenario_table_output = scenario_table_output or (output_root / FREEZER_SCENARIO_TABLE_FILENAME)
    policy_output = policy_output or (output_root / FREEZER_POLICY_FILENAME)
    manifest_output = manifest_output or (output_root / FREEZER_MANIFEST_FILENAME)

    for path in (source_zone_metadata_output, release_rows_output, scenario_table_output, policy_output, manifest_output):
        path.parent.mkdir(parents=True, exist_ok=True)

    source_zone_metadata_output.write_text(yaml.safe_dump(source_zone_metadata, sort_keys=False), encoding="utf-8")
    write_freezer_csv(release_rows_output, release_rows, FREEZER_RELEASE_ROWS_COLUMNS)
    write_freezer_csv(scenario_table_output, scenario_rows, FREEZER_SCENARIO_TABLE_COLUMNS)
    policy_output.write_text(yaml.safe_dump(policy, sort_keys=False), encoding="utf-8")

    report = {
        "schema_version": FREEZER_SCHEMA_VERSION,
        "freezer_status": "ready",
        "blocked_reason": None,
        "read_only": True,
        "scale_up_authorized": False,
        "operational_claims_allowed": False,
        "candidate_site_id": site_id,
        "candidate_site_name": candidate_site_name,
        "review_package_path": display_path(review_package_path),
        "source_zone_id": source_zone_id,
        "accepted_candidate_ids": accepted_ids,
        "rejected_candidate_ids": rejected_ids,
        "accepted_candidate_count": len(accepted_ids),
        "rejected_candidate_count": len(rejected_ids),
        "release_row_count": len(release_rows),
        "scenario_row_count": len(scenario_rows),
        "trajectory_count": trajectory_count,
        "seed": seed,
        "seed_policy": "fixed_integer_recorded_before_simulation",
        "block_family_ids": [text_value(scenario.get("block_family_id")) for scenario in block_scenarios],
        "block_scenario_ids": [text_value(scenario.get("block_scenario_id")) for scenario in block_scenarios],
        "conditional_weight_total": conditional_weight_total,
        "conditional_weight_semantics": "conditional_sampling_only",
        "source_zone_metadata": source_zone_metadata,
        "release_rows": release_rows,
        "scenario_table_rows": scenario_rows,
        "policy": policy,
        "claim_boundaries": policy.get("claim_boundary", {}),
        "output_paths": {
            "source_zone_metadata": display_path(source_zone_metadata_output),
            "release_rows": display_path(release_rows_output),
            "scenario_table": display_path(scenario_table_output),
            "policy": display_path(policy_output),
            "manifest": display_path(manifest_output),
        },
    }
    manifest_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def candidate_repeat_count_from_records(candidate_records: list[dict[str, Any]]) -> int:
    repeat_indices = {int(candidate.get("candidate_repeat_index") or 0) for candidate in candidate_records}
    return max(repeat_indices) + 1 if repeat_indices else 0


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def load_yaml_or_json(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        data = json.loads(text)
    else:
        try:
            data = yaml.safe_load(text)
        except Exception:
            data = json.loads(text)
    return data if isinstance(data, dict) else {}


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def load_block_scenarios(policy: dict[str, Any]) -> list[dict[str, Any]]:
    block_policy = policy.get("block_scenario_policy", {}) if isinstance(policy.get("block_scenario_policy"), dict) else {}
    scenarios = block_policy.get("scenarios", []) if isinstance(block_policy.get("scenarios"), list) else []
    block_scenarios: list[dict[str, Any]] = []
    for scenario in scenarios:
        if not isinstance(scenario, dict):
            continue
        block_scenarios.append(
            {
                "block_scenario_id": text_value(scenario.get("block_scenario_id")),
                "block_size_class": text_value(scenario.get("block_size_class")),
                "block_shape_class": text_value(scenario.get("block_shape_class")),
                "block_radius_m": scenario.get("block_radius_m"),
                "block_mass_kg": scenario.get("block_mass_kg"),
                "sampling_weight": scenario.get("sampling_weight"),
            }
        )
    return block_scenarios


def resolve_output_root(output_root: Path) -> Path:
    return output_root if output_root.is_absolute() else (ROOT / output_root)


def is_allowed_output_root(output_root: Path) -> bool:
    resolved = output_root.resolve(strict=False)
    allowed_roots = [
        Path("/tmp"),
        Path("/private/tmp"),
        ROOT / "validation/private",
        ROOT / "data/processed/swisstopo",
        ROOT / "validation/policies",
        ROOT / "hazard/results",
        ROOT / "validation/results",
        ROOT / "verification/results",
        ROOT / "target",
    ]
    return any(resolved == root or resolved.is_relative_to(root) for root in allowed_roots)


def parse_template_ids(value: str | list[str] | tuple[str, ...]) -> list[str]:
    if isinstance(value, (list, tuple)):
        template_ids = [text_value(item) for item in value if text_value(item)]
    else:
        template_ids = [item.strip() for item in value.split(",") if item.strip()]
    if not template_ids:
        raise CandidateSourceZoneScenarioStressError("at least one scenario-family template id is required")
    unknown = [template_id for template_id in template_ids if template_id not in SUPPORTED_TEMPLATES]
    if unknown:
        raise CandidateSourceZoneScenarioStressError("unsupported scenario-family template ids: " + ", ".join(unknown))
    return template_ids


def template_summary(template_ids: list[str]) -> list[dict[str, str]]:
    return [
        {
            "template_id": template_id,
            "description": SUPPORTED_TEMPLATES[template_id],
        }
        for template_id in template_ids
    ]


def policy_root_prefix(policy: dict[str, Any]) -> str:
    policy_id = text_value(policy.get("policy_id"))
    if policy_id.endswith("_source_scenario_policy_v1"):
        return policy_id[: -len("_source_scenario_policy_v1")]
    return policy_id or "scenario"


def display_path(path: Path) -> str:
    resolved = path.resolve(strict=False)
    try:
        return str(resolved.relative_to(ROOT))
    except ValueError:
        return str(resolved)


def text_value(value: Any) -> str:
    return str(value).strip() if value not in (None, "") else ""


def parse_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed == parsed and parsed not in (float("inf"), float("-inf")) else None


def get_nested_value(mapping: dict[str, Any], keys: tuple[str, ...]) -> Any:
    current: Any = mapping
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh, lineterminator="\n")
        writer.writerow(SCENARIO_TABLE_COLUMNS)
        for row in rows:
            writer.writerow([csv_value(row.get(column)) for column in SCENARIO_TABLE_COLUMNS])


def csv_value(value: Any) -> str:
    if value in (None, ""):
        return ""
    if isinstance(value, float):
        if value in (1.0, 2.0, 3.0, 5.0):
            return f"{value:.1f}"
        return f"{value:.6f}"
    return str(value)


def write_outputs(report: dict[str, Any]) -> None:
    output_paths = report.get("output_paths", {}) or {}
    csv_path = repo_path(output_paths.get("scenario_table_csv"))
    manifest_path = repo_path(output_paths.get("scenario_table_manifest_json"))
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    write_csv(csv_path, report["generated_scenario_table_rows"])
    manifest_path.write_text(json.dumps(report["scenario_table_manifest"], indent=2, sort_keys=True) + "\n", encoding="utf-8")


def repo_path(value: Any) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise CandidateSourceZoneScenarioStressError("missing output path value")
    path = Path(value)
    return path if path.is_absolute() else (ROOT / path)


def render_text_report(report: dict[str, Any]) -> str:
    lines = [
        "Candidate Source-Zone Scenario Stress Test",
        "",
        f"- Schema version: `{report['schema_version']}`",
        f"- Stress test status: `{report['stress_test_status']}`",
        f"- Candidate repeat count: `{report['candidate_repeat_count']}`",
        f"- Candidate release-zone record count: `{report['candidate_release_zone_record_count']}`",
        f"- Scenario row count: `{report['scenario_row_count']}`",
        "",
        "Release Candidate Physical-Meaning Firewall",
    ]
    firewall = report.get("release_candidate_physical_meaning_firewall", {})
    lines.append(f"- release_candidate_provenance_state: `{firewall.get('release_candidate_provenance_state', '')}`")
    lines.append(f"- firewall_status: `{firewall.get('firewall_status', '')}`")
    lines.append(f"- sampling_weight_semantics: `{firewall.get('sampling_weight_semantics', '')}`")
    lines.append(f"- sampling_weight_boundary: `{firewall.get('sampling_weight_boundary', '')}`")
    lines.append(f"- physical_probability_claims_allowed: `{firewall.get('physical_probability_claims_allowed', '')}`")
    lines.append(f"- annual_frequency_claims_allowed: `{firewall.get('annual_frequency_claims_allowed', '')}`")
    lines.append(f"- return_period_claims_allowed: `{firewall.get('return_period_claims_allowed', '')}`")
    lines.append(f"- risk_claims_allowed: `{firewall.get('risk_claims_allowed', '')}`")
    lines.append("- release_candidate_provenance_state_counts:")
    for key, value in (firewall.get("release_candidate_provenance_state_counts") or {}).items():
        lines.append(f"  - {key}: {value}")
    lines.append("- release_candidate_provenance_profile:")
    for entry in firewall.get("release_candidate_provenance_profile", []):
        lines.append(f"  - {entry.get('candidate_release_zone_record_id', '')}: {entry.get('provenance_state', '')}")
        lines.append(f"    workflow_generated: {entry.get('workflow_generated', '')}")
        lines.append(f"    field_supported: {entry.get('field_supported', '')}")
        lines.append(f"    blocked_missing_provenance: {entry.get('blocked_missing_provenance', '')}")
    lines.append("- scenario_row_provenance_profile:")
    for entry in firewall.get("scenario_row_provenance_profile", []):
        lines.append(f"  - {entry.get('row_id', '')}: {entry.get('release_candidate_provenance_state', '')}")
        lines.append(f"    sampling_weight: {entry.get('sampling_weight', '')}")
        lines.append(f"    normalized_sampling_share: {entry.get('normalized_sampling_share', '')}")
    lines.extend(
        [
            "",
            "Planning Input",
        ]
    )
    planning = report.get("tb_183_planning_input", {})
    lines.append(f"- status: `{planning.get('status', '')}`")
    lines.append(f"- reason: `{planning.get('reason', '')}`")
    lines.append(f"- ready_for_tb_183: `{planning.get('ready_for_tb_183', '')}`")
    lines.append("")
    lines.append("First Bottleneck")
    bottleneck = report.get("first_scaling_bottleneck", {})
    lines.append(f"- name: `{bottleneck.get('name', '')}`")
    lines.append(f"- reason: `{bottleneck.get('reason', '')}`")
    lines.append("")
    lines.append("Storage")
    storage = report.get("storage_measurements", {})
    lines.append(f"- csv_bytes: `{storage.get('csv_bytes', '')}`")
    lines.append(f"- manifest_bytes: `{storage.get('manifest_bytes', '')}`")
    lines.append(f"- total_bytes: `{storage.get('total_bytes', '')}`")
    lines.append("")
    lines.append("Runtime")
    runtime = report.get("runtime_measurements", {})
    lines.append(f"- build_seconds: `{runtime.get('build_seconds', '')}`")
    lines.append(f"- write_seconds: `{runtime.get('write_seconds', '')}`")
    lines.append(f"- total_seconds: `{runtime.get('total_seconds', '')}`")
    lines.append("")
    lines.append("Output Paths")
    for key, value in (report.get("output_paths") or {}).items():
        lines.append(f"- {key}: `{value}`")
    return "\n".join(lines)


def render_freezer_text_report(report: dict[str, Any]) -> str:
    lines = [
        "Reviewed Candidate Source-Zone Freezer",
        "",
        f"- Schema version: `{report['schema_version']}`",
        f"- Freezer status: `{report['freezer_status']}`",
        f"- Candidate site id: `{report['candidate_site_id']}`",
        f"- Candidate site name: `{report['candidate_site_name']}`",
        f"- Source zone id: `{report['source_zone_id']}`",
        f"- Accepted candidate count: `{report['accepted_candidate_count']}`",
        f"- Rejected candidate count: `{report['rejected_candidate_count']}`",
        f"- Release row count: `{report['release_row_count']}`",
        f"- Scenario row count: `{report['scenario_row_count']}`",
        f"- Trajectory count: `{report['trajectory_count']}`",
        f"- Seed policy: `{report['seed_policy']}`",
        f"- Conditional weight total: `{report['conditional_weight_total']}`",
        "",
        "Claim Boundary",
    ]
    claim = report.get("claim_boundaries", {}) or {}
    lines.append(f"- sampling_weight_semantics: `{claim.get('sampling_weight_semantics', report.get('conditional_weight_semantics', ''))}`")
    unsupported = claim.get("unsupported_current_claims") or []
    if unsupported:
        lines.append(f"- unsupported_current_claims: `{', '.join(str(item) for item in unsupported)}`")
    notes = claim.get("notes") or []
    if notes:
        lines.append("- notes:")
        for note in notes:
            lines.append(f"  - {note}")
    lines.append("")
    lines.append("Output Paths")
    for key, value in (report.get("output_paths") or {}).items():
        lines.append(f"- {key}: `{value}`")
    return "\n".join(lines)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
