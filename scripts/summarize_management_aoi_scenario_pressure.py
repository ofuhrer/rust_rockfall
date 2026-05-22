#!/usr/bin/env python3
"""Summarize real-AOI scenario-generation pressure for the management AOI.

This helper stays at the dry-run boundary. It reads the frozen candidate
stability / review manifests and the source-scenario policy, then reports the
scenario-generation pressure that would be imposed by the current candidate
set. When the candidate set is empty, the report is explicitly blocked and
preserves the measured zero-candidate result instead of inventing scenarios.

The helper does not generate hazard outputs, run ensembles, or introduce any
frequency, probability, or operational claim semantics.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
import tempfile
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except ImportError as exc:  # pragma: no cover - environment setup.
    raise SystemExit(
        "PyYAML is required. Run this script with `PYENV_VERSION=system uv run python ...`; "
        "CI may use `requirements-tools.txt`"
    ) from exc


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "management_aoi_scenario_pressure_v1"
DEFERRAL_SCHEMA_VERSION = "release_candidate_zero_result_diagnostic_v1"
PREPARED_PILOT_SMOKE_HANDOFF_SCHEMA_VERSION = "management_aoi_prepared_pilot_smoke_handoff_v1"
PREPARED_PILOT_SMOKE_COMMAND_TARGET = "second_site_aoi_to_prepared_pilot_dry_run"
DEFAULT_CANDIDATE_METRICS_MANIFEST = ROOT / "validation/private/source_zone_review/tschamut_expanded_source_zone_candidate_report.json"
DEFAULT_CANDIDATE_REVIEW_MANIFEST = ROOT / "validation/private/source_zone_review/tschamut_adjacent_prau_mulins_candidate_v1_review_manifest.json"
DEFAULT_POLICY = ROOT / "validation/policies/tschamut_public_source_scenario_policy_v1.yaml"
DEFAULT_OUTPUT_ROOT = Path("/tmp/rust_rockfall/tb404_management_aoi_scenario_pressure")
DEFAULT_SCENARIO_OUTPUT_ROOT = Path("/tmp/rust_rockfall/tb404_management_aoi_scenario_table")
DEFAULT_DEFERRAL_TERRAIN_CROP = ROOT / "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/terrain.asc"
DEFAULT_DEFERRAL_TERRAIN_METADATA = ROOT / "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/terrain_metadata.yaml"
DEFAULT_DEFERRAL_SOURCE_ZONE_METADATA = (
    ROOT / "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/source_zone_metadata.yaml"
)


def _load_module(module_name: str, filename: str):
    path = ROOT / "scripts" / filename
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load helper module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


DIAGNOSTIC = _load_module("management_aoi_scenario_pressure_deferral_diagnostic", "diagnose_release_candidate_zero_result.py")
REVIEW_PLANNER = _load_module("management_aoi_scenario_pressure_review_planner", "plan_terrain_release_zone_candidates.py")
SCENARIO_FREEZER = _load_module("management_aoi_scenario_pressure_freezer", "generate_candidate_source_zone_scenarios.py")
AOI_PREVIEW = _load_module("management_aoi_scenario_pressure_aoi_preview", "preview_aoi_scenario_cost_estimate.py")
OUTPUT_BUDGET = _load_module("management_aoi_scenario_pressure_output_budget", "summarize_bounded_validation_output_profile.py")


CANDIDATE_EXPANSION_COUNTS = (1, 2, 4, 8)
FAIL_CLOSED_SEARCH_LIMIT = 4096


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-metrics-manifest", type=Path, default=DEFAULT_CANDIDATE_METRICS_MANIFEST)
    parser.add_argument("--candidate-review-manifest", type=Path, default=DEFAULT_CANDIDATE_REVIEW_MANIFEST)
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--scenario-output-root", type=Path, default=DEFAULT_SCENARIO_OUTPUT_ROOT)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    args = parser.parse_args(argv)

    try:
        report = build_report(
            candidate_metrics_manifest_path=args.candidate_metrics_manifest,
            candidate_review_manifest_path=args.candidate_review_manifest,
            policy_path=args.policy,
            output_root=args.output_root,
            scenario_output_root=args.scenario_output_root,
        )
    except ManagementAoiScenarioPressureError as exc:
        print(f"management AOI scenario pressure error: {exc}", file=sys.stderr)
        return 2

    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text_report(report))
    return 0 if report["scenario_pressure_status"] == "ready" else 2


def build_report(
    *,
    candidate_metrics_manifest_path: Path = DEFAULT_CANDIDATE_METRICS_MANIFEST,
    candidate_review_manifest_path: Path = DEFAULT_CANDIDATE_REVIEW_MANIFEST,
    policy_path: Path = DEFAULT_POLICY,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    scenario_output_root: Path = DEFAULT_SCENARIO_OUTPUT_ROOT,
) -> dict[str, Any]:
    missing_inputs = [
        display_path(path)
        for path in (candidate_metrics_manifest_path, candidate_review_manifest_path, policy_path)
        if not path.exists()
    ]
    if missing_inputs:
        return blocked_report(
            missing_inputs=missing_inputs,
            candidate_metrics_manifest_path=candidate_metrics_manifest_path,
            candidate_review_manifest_path=candidate_review_manifest_path,
            policy_path=policy_path,
            output_root=output_root,
            scenario_output_root=scenario_output_root,
            blocked_reason="required candidate manifests or policy are missing",
            blocking_label="blocked_missing_inputs",
        )

    candidate_metrics = load_json(candidate_metrics_manifest_path)
    candidate_review = load_json(candidate_review_manifest_path)
    policy = load_yaml(policy_path)

    candidate_summary = candidate_metrics.get("candidate_summary") or {}
    review_summary = candidate_review.get("review_summary") or {}
    candidate_count = int(
        review_summary.get("candidate_count")
        if isinstance(review_summary.get("candidate_count"), int)
        else candidate_summary.get("candidate_cell_count", 0)
        or 0
    )
    candidate_area_m2 = float(candidate_summary.get("candidate_area_m2") or 0.0)
    candidate_family_cardinality = summarize_candidate_family_cardinality(candidate_review)
    policy_block_families = summarize_policy_block_families(policy)

    bundle_root = candidate_metrics_manifest_path.parent
    bundle_measurements = measure_bundle_pressure(bundle_root)
    generated_table_report: dict[str, Any] | None = None
    candidate_expansion_report: dict[str, Any] | None = None

    if candidate_count <= 0:
        deferral_report = load_management_aoi_deferral_report()
        deferral_record = dict(deferral_report.get("deferral_record") or {})
        deferral_blocker = str(deferral_record.get("blocker_type") or "")
        scenario_pressure_status = (
            f"blocked_{deferral_blocker}" if deferral_blocker else "blocked_empty_candidate_set"
        )
        blocked_reason = str(
            deferral_record.get("required_upstream_replacement")
            or deferral_record.get("blocking_summary")
            or deferral_report.get("blocked_reason")
            or "TB-377 preserved a zero-candidate management-AOI result; no scenario rows can be generated without inventing candidates."
        )
        first_blocker = dict(deferral_report.get("first_blocker") or {})
        unblock_guidance = dict(deferral_report.get("unblock_guidance") or {})
        smoke_handoff = build_prepared_pilot_smoke_handoff(
            scenario_table_generation={},
            scenario_output_root=scenario_output_root,
        )
        report = {
            "schema_version": SCHEMA_VERSION,
            "scenario_pressure_status": scenario_pressure_status,
            "blocked_reason": blocked_reason,
            "read_only": True,
            "scale_up_authorized": False,
            "operational_claims_allowed": False,
            "deferral_record": deferral_record,
            "deferral_diagnostic": dict(deferral_report.get("diagnostic_report") or {}),
            "first_blocker": first_blocker,
            "required_upstream_replacement": deferral_record.get("required_upstream_replacement", ""),
            "blocking_summary": deferral_record.get("blocking_summary", ""),
            "source_inputs": {
                "candidate_metrics_manifest_path": display_path(candidate_metrics_manifest_path),
                "candidate_review_manifest_path": display_path(candidate_review_manifest_path),
                "policy_path": display_path(policy_path),
            },
            "candidate_evidence": {
                "candidate_release_zone_set_status": text_value(candidate_metrics.get("candidate_release_zone_set_status")),
                "candidate_cell_count": int(candidate_summary.get("candidate_cell_count") or 0),
                "candidate_area_m2": candidate_area_m2,
                "candidate_family_cardinality": candidate_family_cardinality,
                "review_summary": {
                    "candidate_count": int(review_summary.get("candidate_count") or 0),
                    "review_row_count": int(review_summary.get("review_row_count") or 0),
                    "review_decision_counts": dict(review_summary.get("review_decision_counts") or {}),
                    "candidate_stability_class_counts": dict(review_summary.get("candidate_stability_class_counts") or {}),
                },
                "bundle_measurements": bundle_measurements,
            },
            "scenario_generation_pressure": {
                "scenario_row_count": 0,
                "scenario_family_cardinality": [],
                "policy_block_family_cardinality": [
                    {**family, "row_count": 0}
                    for family in policy_block_families
                ],
                "scenario_table_csv_bytes": 0,
                "scenario_table_manifest_bytes": 0,
                "scenario_table_total_bytes": 0,
                "manifest_pressure": {
                    "scenario_table_manifest_pressure": "blocked_no_scenario_table",
                    "candidate_bundle_manifest_bytes": bundle_measurements["manifest_bytes"],
                    "candidate_bundle_total_bytes": bundle_measurements["total_bytes"],
                },
                "prepared_pilot_smoke_handoff": smoke_handoff,
            },
            "command_plan_implications": [
                {
                    "command_id": "second_site_release_plan_dry_run",
                    "status": "template_only",
                    "implication": "keep it as a read-only template; it does not authorize a real-AOI scenario table",
                },
                {
                    "command_id": "second_site_release_plan_execution_template",
                    "status": scenario_pressure_status,
                    "implication": blocked_reason,
                },
                {
                    "command_id": "second_site_aoi_to_prepared_pilot_dry_run",
                    "status": "deferred",
                    "implication": "the AOI-to-prepared-pilot path remains a dry-run scaffold only",
                },
            ],
            "unblock_guidance": unblock_guidance,
            "claim_boundary": claim_boundary_from_policy(policy),
            "prepared_pilot_smoke_handoff": smoke_handoff,
        }
        write_report(report, output_root)
        return report

    generated_table_report = build_generated_scenario_table_report(
        candidate_review_manifest_path=candidate_review_manifest_path,
        policy_path=policy_path,
        output_root=output_root,
        scenario_output_root=scenario_output_root,
    )
    if generated_table_report.get("scenario_table_status") != "ready":
        return blocked_report(
            missing_inputs=[],
            candidate_metrics_manifest_path=candidate_metrics_manifest_path,
            candidate_review_manifest_path=candidate_review_manifest_path,
            policy_path=policy_path,
            output_root=output_root,
            scenario_output_root=scenario_output_root,
            blocked_reason=str(generated_table_report.get("blocked_reason") or "real-AOI scenario table generation failed"),
            blocking_label=str(generated_table_report.get("scenario_table_status") or "blocked_scenario_table_generation_failed"),
            candidate_evidence_override={
                "candidate_release_zone_set_status": text_value(candidate_metrics.get("candidate_release_zone_set_status")),
                "candidate_cell_count": int(candidate_summary.get("candidate_cell_count") or 0),
                "candidate_area_m2": candidate_area_m2,
                "candidate_family_cardinality": candidate_family_cardinality,
                "review_summary": {
                    "candidate_count": int(review_summary.get("candidate_count") or 0),
                    "review_row_count": int(review_summary.get("review_row_count") or 0),
                    "review_decision_counts": dict(review_summary.get("review_decision_counts") or {}),
                    "candidate_stability_class_counts": dict(review_summary.get("candidate_stability_class_counts") or {}),
                },
                "bundle_measurements": bundle_measurements,
            },
        )

    candidate_expansion_report = build_candidate_expansion_pressure_report(
        candidate_review_manifest_path=candidate_review_manifest_path,
        candidate_review=candidate_review,
        policy=policy,
        trajectory_count=int((generated_table_report.get("scenario_table_generation") or {}).get("trajectory_count") or 60),
        output_root=output_root,
        scenario_output_root=scenario_output_root,
    )

    scenario_table_generation = dict(generated_table_report.get("scenario_table_generation") or {})
    prepared_pilot_smoke_handoff = build_prepared_pilot_smoke_handoff(
        scenario_table_generation=scenario_table_generation,
        scenario_output_root=scenario_output_root,
    )
    scenario_table_generation["prepared_pilot_smoke_handoff"] = prepared_pilot_smoke_handoff
    scenario_table_bundle_measurements = dict(scenario_table_generation.get("bundle_measurements") or {})
    scenario_table_manifest = dict(scenario_table_generation.get("scenario_table_manifest") or {})
    scenario_table_file_count = int(scenario_table_bundle_measurements.get("file_count") or 0)
    scenario_row_count = int(scenario_table_generation.get("scenario_row_count") or 0)
    scenario_rows = list(scenario_table_generation.get("scenario_table_rows") or [])
    block_family_counts: dict[str, int] = {}
    release_zone_counts: dict[str, int] = {}
    for row in scenario_rows:
        if not isinstance(row, dict):
            continue
        block_family_id = text_value(row.get("block_family_id"))
        release_zone_id = text_value(row.get("candidate_release_zone_id"))
        if block_family_id:
            block_family_counts[block_family_id] = block_family_counts.get(block_family_id, 0) + 1
        if release_zone_id:
            release_zone_counts[release_zone_id] = release_zone_counts.get(release_zone_id, 0) + 1
    generated_scenario_family_cardinality = [
        {"scenario_family_id": family_id, "row_count": count}
        for family_id, count in sorted(block_family_counts.items())
    ]
    generated_release_zone_cardinality = [
        {"release_zone_id": release_zone_id, "row_count": count}
        for release_zone_id, count in sorted(release_zone_counts.items())
    ]

    report = {
        "schema_version": SCHEMA_VERSION,
        "scenario_pressure_status": "ready",
        "blocked_reason": "",
        "read_only": True,
        "scale_up_authorized": False,
        "operational_claims_allowed": False,
        "deferral_record": {},
        "deferral_diagnostic": {},
        "first_blocker": {
            "blocker_id": "none",
            "status": "candidates_present",
            "reason": "the current candidate package contains at least one candidate cell",
        },
        "required_upstream_replacement": "",
        "blocking_summary": "",
        "source_inputs": {
            "candidate_metrics_manifest_path": display_path(candidate_metrics_manifest_path),
            "candidate_review_manifest_path": display_path(candidate_review_manifest_path),
            "policy_path": display_path(policy_path),
        },
        "candidate_evidence": {
            "candidate_release_zone_set_status": text_value(candidate_metrics.get("candidate_release_zone_set_status")),
            "candidate_cell_count": candidate_count,
            "candidate_area_m2": candidate_area_m2,
            "candidate_family_cardinality": candidate_family_cardinality,
            "review_summary": {
                "candidate_count": int(review_summary.get("candidate_count") or 0),
                "review_row_count": int(review_summary.get("review_row_count") or 0),
                "review_decision_counts": dict(review_summary.get("review_decision_counts") or {}),
                "candidate_stability_class_counts": dict(review_summary.get("candidate_stability_class_counts") or {}),
            },
            "bundle_measurements": bundle_measurements,
        },
        "scenario_generation_pressure": {
            "scenario_row_count": scenario_row_count,
            "scenario_family_cardinality": generated_scenario_family_cardinality,
            "release_zone_cardinality": generated_release_zone_cardinality,
            "policy_block_family_cardinality": [
                {**family, "row_count": scenario_row_count}
                for family in policy_block_families
            ],
            "scenario_table_csv_bytes": int(scenario_table_generation.get("csv_bytes") or 0),
            "scenario_table_manifest_bytes": int(scenario_table_generation.get("manifest_bytes") or 0),
            "scenario_table_total_bytes": int(scenario_table_generation.get("total_bytes") or 0),
            "scenario_table_file_count": scenario_table_file_count,
            "scenario_table_runtime_seconds": float(scenario_table_generation.get("runtime_seconds") or 0.0),
            "scenario_table_output_root": scenario_table_generation.get("scenario_table_output_root", ""),
            "scenario_table_review_application_root": scenario_table_generation.get("review_application_output_root", ""),
            "manifest_pressure": {
                "scenario_table_manifest_pressure": "ready",
                "candidate_bundle_manifest_bytes": bundle_measurements["manifest_bytes"],
                "candidate_bundle_total_bytes": bundle_measurements["total_bytes"],
            },
            "candidate_expansion_counts": list(CANDIDATE_EXPANSION_COUNTS),
            "candidate_expansion_ladder": candidate_expansion_report.get("candidate_expansion_ladder", []),
            "candidate_expansion_ladder_summary": candidate_expansion_report.get("candidate_expansion_ladder_summary", {}),
            "candidate_expansion_threshold": candidate_expansion_report.get("candidate_expansion_threshold", {}),
            "prepared_pilot_smoke_handoff": prepared_pilot_smoke_handoff,
        },
        "command_plan_implications": [
            {
                "command_id": "second_site_release_plan_dry_run",
                "status": "ready",
                "implication": "the current candidate package can be summarized and frozen into a deterministic scenario table",
            },
            {
                "command_id": "second_site_release_plan_execution_template",
                "status": "ready",
                "implication": (
                    f"prepared-pilot compilation can proceed against the generated {scenario_row_count}-row scenario table; "
                    f"the smallest useful candidate expansion stays within the current reduced-output assumptions at "
                    f"{candidate_expansion_report.get('candidate_expansion_ladder_summary', {}).get('smallest_useful_candidate_count', 0)} candidates"
                ),
            },
            {
                "command_id": "second_site_aoi_to_prepared_pilot_dry_run",
                "status": "ready",
                "implication": "the AOI-to-prepared-pilot path can consume the non-empty candidate package and emitted scenario table",
            },
        ],
        "unblock_guidance": {
            "recommended_next_action": "inspect the generated scenario table and review-applied candidate package before any freeze or prepared-pilot step",
            "scenario_generation_should_remain_blocked": False,
            "balfrin_multi_zone_run_should_remain_blocked": False,
            "max_variant_candidate_cell_count": candidate_count,
        },
        "claim_boundary": claim_boundary_from_policy(policy),
        "scenario_table_generation": scenario_table_generation,
        "prepared_pilot_smoke_handoff": prepared_pilot_smoke_handoff,
    }
    write_report(report, output_root)
    return report


def blocked_report(
    *,
    missing_inputs: list[str],
    candidate_metrics_manifest_path: Path,
    candidate_review_manifest_path: Path,
    policy_path: Path,
    output_root: Path,
    scenario_output_root: Path,
    blocked_reason: str,
    blocking_label: str,
    candidate_evidence_override: dict[str, Any] | None = None,
) -> dict[str, Any]:
    bundle_measurements = measure_bundle_pressure(candidate_metrics_manifest_path.parent)
    smoke_handoff = build_prepared_pilot_smoke_handoff(
        scenario_table_generation={},
        scenario_output_root=scenario_output_root,
    )
    report = {
        "schema_version": SCHEMA_VERSION,
        "scenario_pressure_status": blocking_label,
        "blocked_reason": blocked_reason,
        "read_only": True,
        "scale_up_authorized": False,
        "operational_claims_allowed": False,
        "source_inputs": {
            "candidate_metrics_manifest_path": display_path(candidate_metrics_manifest_path),
            "candidate_review_manifest_path": display_path(candidate_review_manifest_path),
            "policy_path": display_path(policy_path),
        },
        "candidate_evidence": {
            **(candidate_evidence_override or {
                "candidate_release_zone_set_status": "",
                "candidate_cell_count": 0,
                "candidate_area_m2": 0.0,
                "candidate_family_cardinality": [],
                "review_summary": {
                    "candidate_count": 0,
                    "review_row_count": 0,
                    "review_decision_counts": {},
                    "candidate_stability_class_counts": {},
                },
            }),
            "bundle_measurements": bundle_measurements,
        },
        "scenario_generation_pressure": {
            "scenario_row_count": 0,
            "scenario_family_cardinality": [],
            "release_zone_cardinality": [],
            "policy_block_family_cardinality": [],
            "scenario_table_csv_bytes": 0,
            "scenario_table_manifest_bytes": 0,
            "scenario_table_total_bytes": 0,
            "scenario_table_file_count": 0,
            "scenario_table_runtime_seconds": 0.0,
            "scenario_table_output_root": display_path(scenario_output_root),
            "scenario_table_review_application_root": "",
            "manifest_pressure": {
                "scenario_table_manifest_pressure": "blocked_missing_inputs",
                "candidate_bundle_manifest_bytes": bundle_measurements["manifest_bytes"],
                "candidate_bundle_total_bytes": bundle_measurements["total_bytes"],
            },
            "prepared_pilot_smoke_handoff": smoke_handoff,
        },
        "command_plan_implications": [
            {
                "command_id": "second_site_release_plan_dry_run",
                "status": "template_only",
                "implication": "dry-run planning remains read-only",
            },
            {
                "command_id": "second_site_release_plan_execution_template",
                "status": "blocked_missing_inputs",
                "implication": "scenario generation cannot proceed until the missing inputs are restored",
            },
            {
                "command_id": "second_site_aoi_to_prepared_pilot_dry_run",
                "status": "deferred",
                "implication": "the AOI-to-prepared-pilot path remains a dry-run scaffold only",
            },
        ],
        "claim_boundary": {
            "annual_frequency_supported": False,
            "physical_probability_supported": False,
            "return_period_supported": False,
            "operational_hazard_map_supported": False,
            "risk_or_exposure_supported": False,
        },
        "missing_inputs": sorted(set(missing_inputs)),
        "prepared_pilot_smoke_handoff": smoke_handoff,
    }
    write_report(report, output_root)
    return report


def summarize_candidate_family_cardinality(candidate_review: dict[str, Any]) -> list[dict[str, Any]]:
    candidate_ids = list(candidate_review.get("candidate_release_zone_ids") or [])
    if not candidate_ids:
        return []
    row_count = int((candidate_review.get("review_summary") or {}).get("review_row_count") or len(candidate_ids))
    return [
        {
            "candidate_family_id": candidate_id,
            "candidate_count": 1,
            "review_row_count": row_count,
        }
        for candidate_id in candidate_ids
    ]


def summarize_policy_block_families(policy: dict[str, Any]) -> list[dict[str, Any]]:
    scenarios = (
        policy.get("block_scenario_policy", {}).get("scenarios", [])
        if isinstance(policy.get("block_scenario_policy"), dict)
        else []
    )
    families: list[dict[str, Any]] = []
    for index, scenario in enumerate(scenarios, start=1):
        if not isinstance(scenario, dict):
            continue
        families.append(
            {
                "block_family_id": text_value(scenario.get("block_family_id")) or text_value(scenario.get("block_size_class")),
                "block_scenario_id": text_value(scenario.get("block_scenario_id")),
                "sampling_weight": float(scenario.get("sampling_weight") or 0.0),
                "family_index": index,
            }
        )
    return families


def build_generated_scenario_table_report(
    *,
    candidate_review_manifest_path: Path,
    policy_path: Path,
    output_root: Path,
    scenario_output_root: Path,
) -> dict[str, Any]:
    review_package = load_json(candidate_review_manifest_path)
    candidate_ids = list(review_package.get("candidate_release_zone_ids") or [])
    if not candidate_ids:
        return {
            "scenario_table_status": "blocked_no_candidates",
            "blocked_reason": "real-AOI candidate review manifest does not contain any candidate release zones",
            "scenario_table_generation": {},
        }

    scenario_output_root = resolve_scratch_output_root(scenario_output_root)
    review_application_root = output_root / "review_applied"
    review_started = time.perf_counter()
    review_application = REVIEW_PLANNER.build_review_apply_report(
        review_package_path=candidate_review_manifest_path,
        candidate_review_decisions={candidate_id: "accepted" for candidate_id in candidate_ids},
        output_root=review_application_root,
    )
    review_seconds = time.perf_counter() - review_started
    freeze_started = time.perf_counter()
    freezer_report = SCENARIO_FREEZER.build_freezer_report(
        review_package_path=Path(review_application["outputs"]["manifest"]),
        accepted_candidate_ids=candidate_ids,
        output_root=scenario_output_root,
        trajectory_count=60,
        seed=34014,
    )
    freeze_seconds = time.perf_counter() - freeze_started
    total_seconds = review_seconds + freeze_seconds
    scenario_table_output_root = scenario_output_root
    scenario_table_files = [path for path in scenario_table_output_root.rglob("*") if path.is_file()]
    csv_path = Path(freezer_report["output_paths"]["scenario_table"])
    manifest_path = Path(freezer_report["output_paths"]["manifest"])
    scenario_table_manifest_payload = load_json(manifest_path)
    scenario_generation = {
        "scenario_table_status": "ready",
        "blocked_reason": "",
        "scenario_table_generation": {
            "review_application_status": review_application.get("review_application_status", ""),
            "review_application_output_root": display_path(review_application_root),
            "review_application_manifest": review_application["outputs"]["manifest"],
            "scenario_table_output_root": display_path(scenario_table_output_root),
            "trajectory_count": 60,
            "scenario_table_csv": freezer_report["output_paths"]["scenario_table"],
            "scenario_table_manifest": freezer_report["output_paths"]["manifest"],
            "scenario_row_count": int(freezer_report.get("scenario_row_count") or 0),
            "accepted_candidate_count": int(freezer_report.get("accepted_candidate_count") or 0),
            "candidate_release_zone_count": int(freezer_report.get("accepted_candidate_count") or 0),
            "runtime_seconds": round(total_seconds, 6),
            "review_application_seconds": round(review_seconds, 6),
            "freeze_seconds": round(freeze_seconds, 6),
            "csv_bytes": csv_path.stat().st_size if csv_path.exists() else 0,
            "manifest_bytes": manifest_path.stat().st_size if manifest_path.exists() else 0,
            "total_bytes": sum(path.stat().st_size for path in scenario_table_files),
            "file_count": len(scenario_table_files),
            "bundle_measurements": measure_bundle_pressure(scenario_table_output_root),
            "scenario_table_manifest": scenario_table_manifest_payload,
            "source_zone_family_cardinality": list(scenario_table_manifest_payload.get("source_zone_family_cardinality") or []),
            "block_family_cardinality": list(scenario_table_manifest_payload.get("block_family_cardinality") or []),
            "scenario_family_template_cardinality": list(scenario_table_manifest_payload.get("scenario_family_template_cardinality") or []),
            "scenario_table_rows": freezer_report.get("scenario_table_rows") or [],
            "manifest_compaction": freezer_report.get("manifest_compaction") or {},
        },
    }
    return scenario_generation


def build_prepared_pilot_smoke_handoff(
    *,
    scenario_table_generation: dict[str, Any],
    scenario_output_root: Path,
) -> dict[str, Any]:
    manifest = scenario_table_generation.get("scenario_table_manifest")
    if not isinstance(manifest, dict):
        manifest = {}
    output_paths = manifest.get("output_paths")
    if not isinstance(output_paths, dict):
        output_paths = {}

    source_candidate_ids = candidate_ids_from_scenario_table_manifest(manifest)
    scenario_table_output_root = (
        text_value(scenario_table_generation.get("scenario_table_output_root"))
        or display_path(scenario_output_root)
    )
    scenario_table_csv = (
        text_value(scenario_table_generation.get("scenario_table_csv"))
        or text_value(output_paths.get("scenario_table"))
        or str((scenario_output_root / "scenario_table.csv").resolve())
    )
    scenario_table_manifest_path = (
        text_value(scenario_table_generation.get("scenario_table_manifest_path"))
        or text_value(output_paths.get("manifest"))
        or str((scenario_output_root / "scenario_table_manifest.json").resolve())
    )
    scenario_table_id = Path(scenario_table_output_root).name if scenario_table_output_root else ""
    missing_fields: list[str] = []
    if not source_candidate_ids:
        missing_fields.append("source_candidate_id")
    if not scenario_table_csv:
        missing_fields.append("scenario_table_csv")
    if not scenario_table_manifest_path:
        missing_fields.append("scenario_table_manifest_path")
    smoke_status = "ready" if not missing_fields else "blocked_missing_inputs"
    return {
        "schema_version": PREPARED_PILOT_SMOKE_HANDOFF_SCHEMA_VERSION,
        "smoke_status": smoke_status,
        "blocked_reason": (
            "" if smoke_status == "ready" else f"missing prepared-pilot smoke handoff fields: {', '.join(missing_fields)}"
        ),
        "missing_fields": missing_fields,
        "command_plan_target": PREPARED_PILOT_SMOKE_COMMAND_TARGET,
        "source_candidate_id": source_candidate_ids[0] if source_candidate_ids else "",
        "source_candidate_ids": source_candidate_ids,
        "scenario_table_id": scenario_table_id,
        "scenario_table_output_root": scenario_table_output_root,
        "scenario_table_csv": scenario_table_csv,
        "scenario_table_manifest_path": scenario_table_manifest_path,
        "scenario_row_count": int(scenario_table_generation.get("scenario_row_count") or manifest.get("scenario_row_count") or 0),
        "accepted_candidate_count": int(
            scenario_table_generation.get("accepted_candidate_count")
            or manifest.get("accepted_candidate_count")
            or len(source_candidate_ids)
        ),
        "read_only": True,
        "scale_up_authorized": False,
        "operational_claims_allowed": False,
    }


def candidate_ids_from_scenario_table_manifest(manifest: dict[str, Any]) -> list[str]:
    candidate_ids: list[str] = []
    for key in (
        "accepted_candidate_ids",
        "candidate_release_zone_ids",
        "candidate_release_zone_record_ids",
        "source_candidate_ids",
    ):
        values = manifest.get(key)
        if isinstance(values, list):
            candidate_ids.extend(text_value(value) for value in values)
    for key in ("source_zone_family_cardinality", "release_zone_cardinality"):
        rows = manifest.get(key)
        if not isinstance(rows, list):
            continue
        for row in rows:
            if not isinstance(row, dict):
                continue
            candidate_ids.append(
                text_value(row.get("source_zone_id"))
                or text_value(row.get("release_zone_id"))
                or text_value(row.get("candidate_release_zone_id"))
            )
    return dedupe([candidate_id for candidate_id in candidate_ids if candidate_id])


def build_candidate_expansion_pressure_report(
    *,
    candidate_review_manifest_path: Path,
    candidate_review: dict[str, Any],
    policy: dict[str, Any],
    trajectory_count: int,
    output_root: Path,
    scenario_output_root: Path,
) -> dict[str, Any]:
    reviewed_ids = list(candidate_review.get("candidate_release_zone_ids") or [])
    review_rows = [row for row in (candidate_review.get("candidate_review_rows") or []) if isinstance(row, dict)]
    if not review_rows and not reviewed_ids:
        return {
            "candidate_expansion_ladder": [],
            "candidate_expansion_ladder_summary": {
                "smallest_useful_candidate_count": 0,
                "smallest_useful_output_pressure_label": "",
                "first_blocked_candidate_count": 0,
                "first_blocked_output_pressure_label": "",
                "candidate_expansion_counts": list(CANDIDATE_EXPANSION_COUNTS),
            },
            "candidate_expansion_threshold": {
                "status": "blocked_missing_inputs",
                "blocked_reason": "candidate review manifest does not contain any candidate rows",
                "blocking_label": "blocked_missing_inputs",
                "threshold_candidate_count": 0,
            },
        }

    output_profile_policy = AOI_PREVIEW.default_output_profile_policy()
    budget_summary = OUTPUT_BUDGET.build_summary()
    block_family_count = max(1, len(summarize_policy_block_families(policy)))
    ladder: list[dict[str, Any]] = []
    smallest_useful: dict[str, Any] | None = None
    first_blocked: dict[str, Any] | None = None

    with tempfile.TemporaryDirectory(dir="/tmp", prefix="management_aoi_candidate_expansion_") as tmpdir:
        tmp_root = Path(tmpdir)
        for candidate_count in CANDIDATE_EXPANSION_COUNTS:
            synthetic_package = build_synthetic_review_package_for_candidate_count(
                candidate_review=candidate_review,
                candidate_count=candidate_count,
            )
            synthetic_package_path = tmp_root / f"candidate_expansion_{candidate_count:02d}.yaml"
            synthetic_package_path.write_text(yaml.safe_dump(synthetic_package, sort_keys=False), encoding="utf-8")
            selected_ids = list((synthetic_package.get("review_application") or {}).get("accepted_candidate_ids") or [])
            if not selected_ids:
                continue

            freezer_report = SCENARIO_FREEZER.build_freezer_report(
                review_package_path=synthetic_package_path,
                accepted_candidate_ids=selected_ids,
                output_root=tmp_root / f"freeze_{candidate_count:02d}",
                trajectory_count=trajectory_count,
                seed=SCENARIO_FREEZER.DEFAULT_FREEZER_SEED + candidate_count,
            )
            output_paths = {
                name: Path(path)
                for name, path in (freezer_report.get("output_paths") or {}).items()
            }
            csv_path = output_paths.get("scenario_table")
            manifest_path = output_paths.get("manifest")
            if csv_path is None or manifest_path is None:
                continue

            csv_bytes = csv_path.stat().st_size
            manifest_bytes = manifest_path.stat().st_size
            total_bytes = sum(path.stat().st_size for path in output_paths.values())
            row_units = max(1, int(freezer_report.get("accepted_candidate_count") or 0)) * max(1, trajectory_count) * max(1, block_family_count)
            pressure = AOI_PREVIEW.estimate_output_pressure(row_units)
            execution_target = AOI_PREVIEW.recommend_execution_target(
                profile_policy=output_profile_policy,
                projected_files=pressure["projected_files"],
                projected_bytes=pressure["projected_bytes"],
                budget_summary=budget_summary,
            )
            output_pressure_labels = {
                "target": execution_target["target"],
                "target_status": execution_target["target_status"],
                "local": execution_target["local_assessment"]["status"],
                "balfrin": execution_target["balfrin_assessment"]["status"],
                "budget_exceeded": execution_target["target_status"] == AOI_PREVIEW.BLOCKED_TARGET,
            }
            row = {
                "candidate_count": candidate_count,
                "candidate_release_zone_record_count": int(freezer_report.get("accepted_candidate_count") or 0),
                "candidate_release_zone_ids": selected_ids,
                "scenario_row_count": int(freezer_report.get("scenario_row_count") or 0),
                "scenario_table_csv_bytes": csv_bytes,
                "scenario_table_manifest_bytes": manifest_bytes,
                "scenario_table_total_bytes": total_bytes,
                "scenario_table_file_count": len(output_paths),
                "output_pressure_labels": output_pressure_labels,
                "output_pressure_estimate": {
                    "projected_files": pressure["projected_files"],
                    "projected_bytes": pressure["projected_bytes"],
                    "estimated_runtime_seconds": pressure["estimated_runtime_seconds"],
                },
                "execution_target": execution_target,
                "output_budget_assessment": {
                    "local": execution_target["local_assessment"],
                    "balfrin": execution_target["balfrin_assessment"],
                    "budget_exceeded": execution_target["target_status"] == AOI_PREVIEW.BLOCKED_TARGET,
                },
                "scenario_cardinality": {
                    "source_zone_count": int(freezer_report.get("accepted_candidate_count") or 0),
                    "scenario_family_count": block_family_count,
                    "row_count": int(freezer_report.get("scenario_row_count") or 0),
                },
            }
            ladder.append(row)
            if smallest_useful is None and not row["output_budget_assessment"]["budget_exceeded"]:
                smallest_useful = row
            if first_blocked is None and row["output_budget_assessment"]["budget_exceeded"]:
                first_blocked = row

    threshold = build_candidate_expansion_threshold(
        candidate_review=candidate_review,
        policy=policy,
        trajectory_count=trajectory_count,
        output_profile_policy=output_profile_policy,
        budget_summary=budget_summary,
    )
    ladder_summary = {
        "candidate_expansion_counts": list(CANDIDATE_EXPANSION_COUNTS),
        "smallest_useful_candidate_count": int((smallest_useful or {}).get("candidate_count") or 0),
        "smallest_useful_output_pressure_label": text_value((smallest_useful or {}).get("output_pressure_labels", {}).get("target")),
        "first_blocked_candidate_count": int((first_blocked or {}).get("candidate_count") or 0),
        "first_blocked_output_pressure_label": text_value((first_blocked or {}).get("output_pressure_labels", {}).get("target")),
    }
    return {
        "candidate_expansion_ladder": ladder,
        "candidate_expansion_ladder_summary": ladder_summary,
        "candidate_expansion_threshold": threshold,
    }


def build_candidate_expansion_threshold(
    *,
    candidate_review: dict[str, Any],
    policy: dict[str, Any],
    trajectory_count: int,
    output_profile_policy: dict[str, Any],
    budget_summary: dict[str, Any],
) -> dict[str, Any]:
    review_rows = [row for row in (candidate_review.get("candidate_review_rows") or []) if isinstance(row, dict)]
    if not review_rows:
        return {
            "status": "blocked_missing_inputs",
            "blocked_reason": "candidate review manifest does not contain any candidate rows",
            "blocking_label": "blocked_missing_inputs",
            "threshold_candidate_count": 0,
            "last_ready_candidate_count": 0,
            "search_counts": [],
        }

    block_family_count = max(1, len(summarize_policy_block_families(policy)))
    search_counts: list[int] = []
    candidate_count = 1
    last_ready: dict[str, Any] | None = None
    while candidate_count <= FAIL_CLOSED_SEARCH_LIMIT:
        search_counts.append(candidate_count)
        row_units = max(1, candidate_count) * max(1, trajectory_count) * max(1, block_family_count)
        pressure = AOI_PREVIEW.estimate_output_pressure(row_units)
        execution_target = AOI_PREVIEW.recommend_execution_target(
            profile_policy=output_profile_policy,
            projected_files=pressure["projected_files"],
            projected_bytes=pressure["projected_bytes"],
            budget_summary=budget_summary,
        )
        if execution_target["target_status"] == AOI_PREVIEW.BLOCKED_TARGET:
            return {
                "status": "blocked_output_budget_exceeded",
                "blocked_reason": execution_target["blocked_reason"],
                "blocking_label": AOI_PREVIEW.BLOCKED_OUTPUT_BUDGET_EXCEEDED,
                "threshold_candidate_count": candidate_count,
                "last_ready_candidate_count": int((last_ready or {}).get("candidate_count") or 0),
                "last_ready_output_pressure_label": text_value((last_ready or {}).get("execution_target", {}).get("target")),
                "search_counts": search_counts,
            }
        last_ready = {
            "candidate_count": candidate_count,
            "execution_target": execution_target,
        }
        candidate_count *= 2

    return {
        "status": "ready",
        "blocked_reason": "",
        "blocking_label": "",
        "threshold_candidate_count": 0,
        "last_ready_candidate_count": int((last_ready or {}).get("candidate_count") or 0),
        "last_ready_output_pressure_label": text_value((last_ready or {}).get("execution_target", {}).get("target")),
        "search_counts": search_counts,
    }


def build_synthetic_review_package_for_candidate_count(
    *,
    candidate_review: dict[str, Any],
    candidate_count: int,
) -> dict[str, Any]:
    if candidate_count < 1:
        raise ManagementAoiScenarioPressureError("candidate-count must be at least 1")

    review_rows = [row for row in (candidate_review.get("candidate_review_rows") or []) if isinstance(row, dict)]
    if not review_rows:
        raise ManagementAoiScenarioPressureError("candidate review manifest does not contain any candidate rows")

    accepted_rows = [row for row in review_rows if bool(row.get("accepted")) or text_value(row.get("review_decision")) == "accepted"]
    template_rows = accepted_rows or review_rows
    synthetic_ids: list[str] = []
    synthetic_rows: list[dict[str, Any]] = []
    for index in range(candidate_count):
        template_row = dict(template_rows[index % len(template_rows)])
        base_id = text_value(template_row.get("candidate_release_zone_id")) or f"candidate_{index + 1:03d}"
        synthetic_id = base_id if candidate_count == 1 and index == 0 else f"{base_id}__expansion_{index + 1:03d}"
        synthetic_ids.append(synthetic_id)
        template_row["candidate_release_zone_id"] = synthetic_id
        template_row["accepted"] = True
        template_row["rejected"] = False
        template_row["review_decision"] = "accepted"
        template_row["candidate_sensitivity_label"] = text_value(template_row.get("candidate_sensitivity_label")) or "reviewed"
        template_row["provenance_label"] = text_value(template_row.get("provenance_label")) or "workflow_generated"
        template_row["release_cell_count"] = int(template_row.get("release_cell_count") or 1)
        template_row["release_cell_ids"] = text_value(template_row.get("release_cell_ids")) or f"{synthetic_id}__cell_000"
        bbox = template_row.get("component_bbox_lv95_m")
        if isinstance(bbox, dict):
            offset = float(index) * 2.0
            template_row["component_bbox_lv95_m"] = {
                **bbox,
                "xmin": float(bbox.get("xmin", 0.0)) + offset,
                "ymin": float(bbox.get("ymin", 0.0)) + offset,
                "xmax": float(bbox.get("xmax", 0.0)) + offset,
                "ymax": float(bbox.get("ymax", 0.0)) + offset,
            }
        synthetic_rows.append(template_row)

    review_application = dict(candidate_review.get("review_application") or {})
    review_application["validation_status"] = "validated"
    review_application["accepted_candidate_ids"] = synthetic_ids
    review_application["accepted_candidate_count"] = len(synthetic_ids)
    review_application["validated_candidate_count"] = len(synthetic_ids)

    review_summary = dict(candidate_review.get("review_summary") or {})
    review_summary["candidate_count"] = len(synthetic_ids)
    review_summary["review_row_count"] = len(synthetic_rows)
    review_summary["accepted_candidate_count"] = len(synthetic_ids)
    review_summary["rejected_candidate_count"] = 0

    return {
        **candidate_review,
        "review_package_status": "review_applied",
        "review_application": review_application,
        "review_summary": review_summary,
        "candidate_release_zone_ids": synthetic_ids,
        "candidate_review_rows": synthetic_rows,
        "candidate_count": len(synthetic_ids),
    }


def load_management_aoi_deferral_report() -> dict[str, Any]:
    try:
        report = DIAGNOSTIC.build_report(
            repo_root=ROOT,
            terrain_crop_path=DEFAULT_DEFERRAL_TERRAIN_CROP,
            terrain_metadata_path=DEFAULT_DEFERRAL_TERRAIN_METADATA,
            source_zone_metadata_path=DEFAULT_DEFERRAL_SOURCE_ZONE_METADATA,
        )
    except Exception:
        return {}
    if report.get("diagnostic_status") != "zero_candidates_diagnosed":
        return {}
    return report


def measure_bundle_pressure(bundle_root: Path) -> dict[str, Any]:
    if not bundle_root.exists():
        return {
            "bundle_root": display_path(bundle_root),
            "file_count": 0,
            "manifest_bytes": 0,
            "total_bytes": 0,
        }
    files = [path for path in bundle_root.rglob("*") if path.is_file()]
    manifest_bytes = sum(path.stat().st_size for path in files if path.name.endswith("_manifest.json"))
    return {
        "bundle_root": display_path(bundle_root),
        "file_count": len(files),
        "manifest_bytes": manifest_bytes,
        "total_bytes": sum(path.stat().st_size for path in files),
    }


def claim_boundary_from_policy(policy: dict[str, Any]) -> dict[str, Any]:
    claim_boundary = policy.get("claim_boundary", {}) if isinstance(policy.get("claim_boundary"), dict) else {}
    return {
        "annual_frequency_supported": False,
        "physical_probability_supported": False,
        "return_period_supported": False,
        "operational_hazard_map_supported": False,
        "risk_or_exposure_supported": False,
        "current_allowed_products": list(claim_boundary.get("current_allowed_products", [])),
        "unsupported_current_claims": list(claim_boundary.get("unsupported_current_claims", [])),
        "notes": list(claim_boundary.get("notes", [])),
    }


def write_report(report: dict[str, Any], output_root: Path) -> None:
    output_root = Path(output_root)
    output_root.mkdir(parents=True, exist_ok=True)
    report_path = output_root / "management_aoi_scenario_pressure_report.json"
    report["output_paths"] = {
        "scenario_pressure_report_json": display_path(report_path),
    }
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def resolve_scratch_output_root(output_root: Path) -> Path:
    resolved = output_root if output_root.is_absolute() else (ROOT / output_root)
    if not SCENARIO_FREEZER.is_allowed_output_root(resolved):
        raise ManagementAoiScenarioPressureError(
            f"scenario-output-root must stay under /tmp or an ignored repo root: {resolved}"
        )
    return resolved


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def text_value(value: Any) -> str:
    return str(value).strip() if value not in (None, "") else ""


def display_path(path: Path) -> str:
    resolved = path.resolve(strict=False)
    try:
        return str(resolved.relative_to(ROOT))
    except ValueError:
        return str(resolved)


def dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def render_text_report(report: dict[str, Any]) -> str:
    lines = [
        "Management AOI Scenario Pressure",
        "",
        f"- schema_version: `{report['schema_version']}`",
        f"- scenario_pressure_status: `{report['scenario_pressure_status']}`",
        f"- blocked_reason: `{report.get('blocked_reason', '')}`",
        f"- read_only: `{report['read_only']}`",
        f"- scale_up_authorized: `{report['scale_up_authorized']}`",
        f"- operational_claims_allowed: `{report['operational_claims_allowed']}`",
        "",
        "Candidate Evidence",
        f"- candidate_release_zone_set_status: `{report['candidate_evidence']['candidate_release_zone_set_status']}`",
        f"- candidate_cell_count: `{report['candidate_evidence']['candidate_cell_count']}`",
        f"- candidate_area_m2: `{report['candidate_evidence']['candidate_area_m2']}`",
        f"- candidate_bundle_file_count: `{report['candidate_evidence']['bundle_measurements']['file_count']}`",
        f"- candidate_bundle_total_bytes: `{report['candidate_evidence']['bundle_measurements']['total_bytes']}`",
        "",
        "Scenario Pressure",
        f"- scenario_row_count: `{report['scenario_generation_pressure']['scenario_row_count']}`",
        f"- scenario_table_file_count: `{report['scenario_generation_pressure'].get('scenario_table_file_count', 0)}`",
        f"- scenario_table_csv_bytes: `{report['scenario_generation_pressure']['scenario_table_csv_bytes']}`",
        f"- scenario_table_manifest_bytes: `{report['scenario_generation_pressure']['scenario_table_manifest_bytes']}`",
        f"- scenario_table_total_bytes: `{report['scenario_generation_pressure']['scenario_table_total_bytes']}`",
        f"- scenario_table_runtime_seconds: `{report['scenario_generation_pressure'].get('scenario_table_runtime_seconds', 0.0)}`",
        f"- manifest_pressure: `{report['scenario_generation_pressure']['manifest_pressure']['scenario_table_manifest_pressure']}`",
        "",
        "Candidate Expansion Ladder",
        f"- candidate_expansion_counts: `{report['scenario_generation_pressure'].get('candidate_expansion_counts', [])}`",
    ]
    for row in report["scenario_generation_pressure"].get("candidate_expansion_ladder", []):
        lines.append(
            f"- candidate_count: `{row.get('candidate_count', '')}` scenario_row_count: `{row.get('scenario_row_count', '')}` "
            f"csv_bytes: `{row.get('scenario_table_csv_bytes', '')}` manifest_bytes: `{row.get('scenario_table_manifest_bytes', '')}` "
            f"pressure_target: `{row.get('output_pressure_labels', {}).get('target', '')}`"
        )
    ladder_summary = report["scenario_generation_pressure"].get("candidate_expansion_ladder_summary", {})
    if ladder_summary:
        lines.append(
            f"- smallest_useful_candidate_count: `{ladder_summary.get('smallest_useful_candidate_count', 0)}` "
            f"first_blocked_candidate_count: `{ladder_summary.get('first_blocked_candidate_count', 0)}`"
        )
    threshold = report["scenario_generation_pressure"].get("candidate_expansion_threshold", {})
    if threshold:
        lines.append(
            f"- threshold_status: `{threshold.get('status', '')}` "
            f"threshold_candidate_count: `{threshold.get('threshold_candidate_count', 0)}` "
            f"last_ready_candidate_count: `{threshold.get('last_ready_candidate_count', 0)}`"
        )
    lines.extend(["", "Policy Block Families"])
    for family in report["scenario_generation_pressure"].get("policy_block_family_cardinality", []):
        lines.append(
            f"- {family.get('block_family_id', '')}: block_scenario_id=`{family.get('block_scenario_id', '')}` "
            f"sampling_weight=`{family.get('sampling_weight', '')}` row_count=`{family.get('row_count', 0)}`"
        )
    scenario_families = report["scenario_generation_pressure"].get("scenario_family_cardinality", [])
    if scenario_families:
        lines.extend(["", "Generated Scenario Families"])
        for family in scenario_families:
            lines.append(f"- {family.get('scenario_family_id', '')}: row_count=`{family.get('row_count', 0)}`")
    lines.extend(["", "Command Plan Implications"])
    for item in report.get("command_plan_implications", []):
        lines.append(
            f"- {item.get('command_id', '')}: {item.get('status', '')} -> {item.get('implication', '')}"
        )
    return "\n".join(lines)


class ManagementAoiScenarioPressureError(ValueError):
    """User-facing scenario-pressure error."""


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
