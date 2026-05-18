#!/usr/bin/env python3
"""Summarize the Chant Sura / Flüelapass dry-run workflow.

This helper composes the read-only Chant Sura readiness gate, AOI staging
contract, release-candidate generator, scenario-plan generator, command-plan
helper, and dry-run case skeleton into one deterministic report.

It does not download public data, run an ensemble, or treat synthetic
fixtures as public-context evidence. The optional tiny bounded ensemble
handoff stays blocked unless the caller explicitly authorizes it.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "chant_sura_fluelapass_dry_run_report_v1"
DEFAULT_SITE_CONFIG = ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml"
DEFAULT_ACQUISITION_PACKAGE = ROOT / "docs/chant_sura_fluelapass_public_context_acquisition_package.yaml"
DEFAULT_PERMISSION_NOTE = "no explicit tiny bounded ensemble permission recorded"
DEFAULT_TINY_ENSEMBLE_ROOT = Path("/tmp/tb188_chant_sura_fluelapass_tiny_ensemble_handoff")


def _load_module(module_name: str, filename: str):
    path = ROOT / "scripts" / filename
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load helper module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


READINESS_GATE = _load_module(
    "chant_sura_dry_run_readiness_gate",
    "check_chant_sura_real_context_readiness_gate.py",
)
PREFLIGHT = _load_module(
    "chant_sura_dry_run_preflight",
    "check_second_site_public_geodata_preflight.py",
)
AOI_CANDIDATES = _load_module(
    "chant_sura_dry_run_candidate_generation",
    "plan_terrain_release_zone_candidates.py",
)
SCENARIO_PLAN = _load_module(
    "chant_sura_dry_run_scenario_plan",
    "plan_pragmatic_release_plan.py",
)
COMMAND_PLAN = _load_module(
    "chant_sura_dry_run_command_plan",
    "generate_pilot_command_plan.py",
)
CASE_SKELETON = _load_module(
    "chant_sura_dry_run_case_skeleton",
    "generate_chant_sura_fluelapass_dry_run_case_skeleton.py",
)


@contextmanager
def _patched_repo_root(repo_root: Path) -> Iterator[None]:
    original_root = PREFLIGHT.ROOT
    PREFLIGHT.ROOT = repo_root
    try:
        yield
    finally:
        PREFLIGHT.ROOT = original_root


def load_acquisition_package(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {}
    package = READINESS_GATE.load_acquisition_package(path)
    return package if isinstance(package, dict) else {}


def acquisition_package_row_map(acquisition_package: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for row in acquisition_package.get("required_acquisition_items") or []:
        if not isinstance(row, dict):
            continue
        category = PREFLIGHT.text_value(row.get("category"))
        if category:
            rows[category] = row
    return rows


def acquisition_package_status(acquisition_package: dict[str, Any]) -> str:
    rows = acquisition_package_row_map(acquisition_package)
    core_definitions = [
        definition
        for definition in READINESS_GATE.PREPARED_PILOT_REAL_INPUT_DEFINITIONS
        if not definition.get("deferred")
    ]
    core_statuses = [
        PREFLIGHT.text_value((rows.get(definition["category"]) or {}).get("classification"))
        or PREFLIGHT.text_value((rows.get(definition["category"]) or {}).get("current_status"))
        or "missing"
        for definition in core_definitions
    ]
    if core_statuses and all(status == "real_staged" for status in core_statuses):
        return "ready_real"
    if core_statuses and all(status == "fixture_backed" for status in core_statuses):
        return "fixture_backed"
    if core_statuses and all(status == "missing" for status in core_statuses):
        return "missing"
    if any(status == "real_staged" for status in core_statuses):
        return "partial_real"
    if any(status == "fixture_backed" for status in core_statuses):
        return "fixture_backed"
    return "missing"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site-config", type=Path, default=DEFAULT_SITE_CONFIG)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--acquisition-package", type=Path, default=DEFAULT_ACQUISITION_PACKAGE)
    parser.add_argument(
        "--allow-tiny-ensemble-handoff",
        action="store_true",
        help="record explicit permission for the optional tiny bounded ensemble handoff",
    )
    parser.add_argument(
        "--tiny-ensemble-note",
        type=str,
        default=DEFAULT_PERMISSION_NOTE,
        help="record why the tiny ensemble handoff is permitted or blocked",
    )
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    args = parser.parse_args(argv)

    report = build_report(
        args.site_config,
        repo_root=args.repo_root,
        acquisition_package_path=args.acquisition_package,
        allow_tiny_ensemble_handoff=args.allow_tiny_ensemble_handoff,
        tiny_ensemble_note=args.tiny_ensemble_note,
    )

    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    output = json.dumps(report, indent=2, sort_keys=True) if args.format == "json" else render_text_report(report)
    print(output)
    return 0 if report["workflow_classification"] == "ready_for_next_step" else 2


def build_report(
    site_config: Path,
    *,
    repo_root: Path | None = None,
    acquisition_package_path: Path | None = None,
    allow_tiny_ensemble_handoff: bool = False,
    tiny_ensemble_note: str = DEFAULT_PERMISSION_NOTE,
) -> dict[str, Any]:
    repo_root = repo_root or ROOT
    if not site_config.exists():
        return blocked_report(
            site_config=site_config,
            repo_root=repo_root,
            blocked_reason=f"missing site config: {site_config}",
            allow_tiny_ensemble_handoff=allow_tiny_ensemble_handoff,
            tiny_ensemble_note=tiny_ensemble_note,
        )

    with _patched_repo_root(repo_root):
        config = PREFLIGHT.load_site_config(site_config)
        candidate_site_id = PREFLIGHT.text_value(config.get("candidate_site_id")) or "unspecified_second_site"
        candidate_site_name = PREFLIGHT.text_value(config.get("candidate_site_name")) or "unspecified"
        preflight_report = PREFLIGHT.build_report(site_config)
        readiness_report = READINESS_GATE.build_report(
            site_config,
            repo_root=repo_root,
            acquisition_package_path=acquisition_package_path or DEFAULT_ACQUISITION_PACKAGE,
        )
        acquisition_package = load_acquisition_package(acquisition_package_path or DEFAULT_ACQUISITION_PACKAGE)
        paths = PREFLIGHT.build_paths(candidate_site_id, config)

    candidate_generation_report = build_candidate_generation_report(
        repo_root=repo_root,
        terrain_crop_path=paths["terrain_crop"],
        terrain_metadata_path=paths["terrain_metadata"],
        source_zone_metadata_path=paths["source_zone_metadata"],
    )
    scenario_generation_report = SCENARIO_PLAN.build_report(
        policy_path=paths["source_scenario_policy"],
        scenario_table_path=paths["scenario_table"],
    )
    command_plan_report = COMMAND_PLAN.build_report("chant_sura_fluelapass", site_config)
    case_skeleton_report = build_case_skeleton_report(
        preflight_report=preflight_report,
        paths=paths,
        repo_root=repo_root,
        readiness_report=readiness_report,
    )
    prep_summary = {
        "site_config_path": str(site_config),
        "synthetic_config": bool(PREFLIGHT.text_value(config.get("fixture_profile"))),
    }
    prepared_pilot_input_classification = acquisition_package_status(acquisition_package)
    real_input_acquisition_handoff = dict(readiness_report.get("real_input_acquisition_handoff") or {})
    first_missing_real_input_category = derive_first_missing_real_input_category(
        prepared_pilot_input_classification=prepared_pilot_input_classification,
        acquisition_package=acquisition_package,
    )
    first_missing_real_input_classification = derive_first_missing_real_input_classification(
        prepared_pilot_input_classification=prepared_pilot_input_classification,
    )
    if (
        prepared_pilot_input_classification == "missing"
        and not real_input_acquisition_handoff.get("first_missing_real_input_category")
    ):
        expected_local_path = str((preflight_report.get("expected_local_paths") or {}).get(first_missing_real_input_category, ""))
        real_input_acquisition_handoff = {
            "schema_version": READINESS_GATE.REAL_INPUT_ACQUISITION_HANDOFF_SCHEMA_VERSION,
            "next_action_recommendation": "request_download_authorization"
            if first_missing_real_input_category == "terrain_crop"
            else "stage_local_existing_input",
            "authorization_or_defer_status": "download_authorization_needed"
            if first_missing_real_input_category == "terrain_crop"
            else "local_staging_needed",
            "first_missing_real_input_category": first_missing_real_input_category,
            "first_missing_real_input_classification": first_missing_real_input_classification,
            "expected_source_product": first_missing_real_input_category,
            "expected_local_path": expected_local_path,
            "metadata_contract": [],
            "missing_metadata_fields": [],
            "authorization_required": first_missing_real_input_category == "terrain_crop",
            "reason": "The acquisition package does not yet contain real staged core inputs.",
            "stop_condition": (
                f"Stop until {first_missing_real_input_category or 'the missing real core input'}"
                f" ({expected_local_path or 'expected local path unavailable'}) is staged and validated."
            ),
        }

    prepared_pilot_provenance = build_prepared_pilot_provenance(preflight_report, prep_summary)
    prepared_pilot_provenance["real_input_classification"] = prepared_pilot_input_classification
    prepared_pilot_provenance["first_missing_real_input_category"] = first_missing_real_input_category
    prepared_pilot_provenance["status"] = {
        "ready_real": "real_staged",
        "partial_real": "partial_real",
        "fixture_backed": "fixture_backed",
        "missing": "missing",
    }.get(prepared_pilot_input_classification, "missing")
    blocked_fixture_backed_inputs = collect_blocked_fixture_backed_inputs(
        readiness_report=readiness_report,
        preflight_report=preflight_report,
        prepared_pilot_provenance=prepared_pilot_provenance,
    )
    blocked_partial_real_inputs = collect_blocked_partial_real_inputs(
        readiness_report=readiness_report,
        prepared_pilot_provenance=prepared_pilot_provenance,
    )
    if prepared_pilot_input_classification == "missing":
        blocked_fixture_backed_inputs = []
        blocked_partial_real_inputs = []
    prep_summary["prepared_pilot_provenance"] = prepared_pilot_provenance
    blocked_missing_inputs = collect_blocked_missing_inputs(
        readiness_report=readiness_report,
        preflight_report=preflight_report,
        candidate_generation_report=candidate_generation_report,
        scenario_generation_report=scenario_generation_report,
        command_plan_report=command_plan_report,
        case_skeleton_report=case_skeleton_report,
        prepared_pilot_input_classification=prepared_pilot_input_classification,
        real_input_acquisition_handoff=real_input_acquisition_handoff,
    )
    workflow_classification = classify_workflow(
        prepared_pilot_input_classification=prepared_pilot_input_classification,
        blocked_missing_inputs=blocked_missing_inputs,
        blocked_fixture_backed_inputs=blocked_fixture_backed_inputs,
        blocked_partial_real_inputs=blocked_partial_real_inputs,
    )
    tiny_handoff_status = build_tiny_bounded_ensemble_handoff_status(
        workflow_classification=workflow_classification,
        allow_tiny_ensemble_handoff=allow_tiny_ensemble_handoff,
    )
    tiny_handoff_report = build_tiny_bounded_ensemble_handoff(
        candidate_site_id=candidate_site_id,
        candidate_site_name=candidate_site_name,
        repo_root=repo_root,
        case_skeleton_report=case_skeleton_report,
        command_plan_report=command_plan_report,
        readiness_report=readiness_report,
        real_input_acquisition_handoff=real_input_acquisition_handoff,
        tiny_handoff_status=tiny_handoff_status,
        tiny_ensemble_note=tiny_ensemble_note,
    )

    workflow_steps = build_workflow_steps(
        readiness_report=readiness_report,
        case_skeleton_report=case_skeleton_report,
        candidate_generation_report=candidate_generation_report,
        scenario_generation_report=scenario_generation_report,
        command_plan_report=command_plan_report,
        tiny_handoff_report=tiny_handoff_report,
    )
    public_context_readiness = dict(readiness_report)
    public_context_readiness["prepared_pilot_input_classification"] = prepared_pilot_input_classification
    public_context_readiness["first_missing_real_input_category"] = first_missing_real_input_category
    public_context_readiness["first_missing_real_input_classification"] = first_missing_real_input_classification
    public_context_readiness["real_input_acquisition_handoff"] = real_input_acquisition_handoff

    report = {
        "schema_version": SCHEMA_VERSION,
        "workflow_classification": workflow_classification,
        "readiness_status": workflow_classification,
        "prepared_pilot_input_classification": prepared_pilot_input_classification,
        "first_missing_real_input_category": first_missing_real_input_category,
        "first_missing_real_input_classification": first_missing_real_input_classification,
        "candidate_site_id": candidate_site_id,
        "candidate_site_name": candidate_site_name,
        "site_extent": readiness_report.get("site_extent", preflight_report.get("site_extent_or_placeholder", {})),
        "public_context_readiness": public_context_readiness,
        "real_input_acquisition_handoff": real_input_acquisition_handoff,
        "aoi_preparation": case_skeleton_report,
        "release_candidate_generation": candidate_generation_report,
        "scenario_generation": scenario_generation_report,
        "command_planning": command_plan_report,
        "tiny_bounded_ensemble_handoff": tiny_handoff_report,
        "workflow_steps": workflow_steps,
        "blocked_missing_inputs": blocked_missing_inputs,
        "blocked_fixture_backed_inputs": blocked_fixture_backed_inputs,
        "blocked_partial_real_inputs": blocked_partial_real_inputs,
        "prepared_pilot_provenance": prepared_pilot_provenance,
        "ready_for_next_step": {
            "status": workflow_classification,
            "next_step": "tiny_bounded_ensemble_handoff" if workflow_classification == "ready_for_next_step" else "none",
            "requires_explicit_permission": True,
            "permission_recorded": allow_tiny_ensemble_handoff,
            "permission_note": tiny_ensemble_note,
        },
        "claim_boundaries": readiness_report.get("claim_boundaries", {}),
        "scale_up_authorized": False,
        "operational_claims_allowed": False,
    }
    return report


def blocked_report(
    *,
    site_config: Path,
    repo_root: Path,
    blocked_reason: str,
    allow_tiny_ensemble_handoff: bool,
    tiny_ensemble_note: str,
) -> dict[str, Any]:
    candidate_site_id = "unspecified_second_site"
    candidate_site_name = "unspecified"
    if site_config.exists():
        try:
            with _patched_repo_root(repo_root):
                config = PREFLIGHT.load_site_config(site_config)
                candidate_site_id = PREFLIGHT.text_value(config.get("candidate_site_id")) or candidate_site_id
                candidate_site_name = PREFLIGHT.text_value(config.get("candidate_site_name")) or candidate_site_name
        except Exception:  # pragma: no cover - defensive fallback for blocked path only.
            pass
    tiny_handoff_report = build_tiny_bounded_ensemble_handoff(
        candidate_site_id=candidate_site_id,
        candidate_site_name=candidate_site_name,
        repo_root=repo_root,
        case_skeleton_report={
            "case_skeleton_status": "blocked_missing_inputs",
            "blocked_reason": blocked_reason,
            "generated_case_path": "",
        },
        command_plan_report={"command_plan_status": "blocked_missing_inputs", "blocked_template_commands": []},
        readiness_report={"real_context_readiness_gate_status": "blocked_missing_inputs"},
        real_input_acquisition_handoff={},
        tiny_handoff_status="blocked_missing_inputs",
        tiny_ensemble_note=tiny_ensemble_note,
    )
    report = {
        "schema_version": SCHEMA_VERSION,
        "workflow_classification": "blocked_missing_inputs",
        "readiness_status": "blocked_missing_inputs",
        "prepared_pilot_input_classification": "missing",
        "first_missing_real_input_category": "",
        "first_missing_real_input_classification": "",
        "candidate_site_id": candidate_site_id,
        "candidate_site_name": candidate_site_name,
        "site_extent": "placeholder_extent_missing",
        "real_input_acquisition_handoff": {},
        "prepared_pilot_provenance": {
            "schema_version": "chant_sura_prepared_pilot_provenance_v1",
            "status": "blocked_missing_inputs",
            "candidate_site_id": candidate_site_id,
            "candidate_site_name": candidate_site_name,
            "synthetic_fixture_readiness_status": "blocked_missing_inputs",
            "synthetic_fixture_profile": "none",
            "real_input_classification": "missing",
            "first_missing_real_input_category": "",
            "site_config_path": str(site_config),
            "synthetic_config": False,
            "source": "missing site config",
        },
        "public_context_readiness": {"real_context_readiness_gate_status": "blocked_missing_inputs"},
        "aoi_preparation": {
            "case_skeleton_status": "blocked_missing_inputs",
            "blocked_reason": blocked_reason,
            "generated_case_path": "",
        },
        "release_candidate_generation": {
            "candidate_metrics_status": "blocked_missing_inputs",
            "candidate_release_zone_set_status": "not_emitted",
            "candidate_release_zone_interpretation": "not_claimed",
            "blocked_missing_inputs": [blocked_reason],
            "blocked_reason": blocked_reason,
        },
        "scenario_generation": {
            "scenario_plan_status": "blocked_missing_inputs",
            "blocked_reason": blocked_reason,
            "missing_inputs": [blocked_reason],
        },
        "command_planning": {
            "command_plan_status": "blocked_missing_inputs",
            "blocked_template_commands": [],
            "blocked_reason": blocked_reason,
            "commands": [],
        },
        "tiny_bounded_ensemble_handoff": tiny_handoff_report,
        "workflow_steps": [
            {
                "step_id": "public_context_readiness",
                "status": "blocked_missing_inputs",
                "blocked_reason": blocked_reason,
            },
            {
                "step_id": "aoi_preparation",
                "status": "blocked_missing_inputs",
                "blocked_reason": blocked_reason,
            },
            {
                "step_id": "release_candidate_generation",
                "status": "blocked_missing_inputs",
                "blocked_reason": blocked_reason,
            },
            {
                "step_id": "scenario_generation",
                "status": "blocked_missing_inputs",
                "blocked_reason": blocked_reason,
            },
            {
                "step_id": "command_planning",
                "status": "blocked_missing_inputs",
                "blocked_reason": blocked_reason,
            },
            {
                "step_id": "tiny_bounded_ensemble_handoff",
                "status": tiny_handoff_report["status"],
                "blocked_reason": tiny_handoff_report["blocked_reason"],
            },
        ],
        "blocked_missing_inputs": [blocked_reason],
        "blocked_fixture_backed_inputs": [],
        "blocked_partial_real_inputs": [],
        "ready_for_next_step": {
            "status": "blocked_missing_inputs",
            "next_step": "none",
            "requires_explicit_permission": bool(allow_tiny_ensemble_handoff),
            "permission_recorded": allow_tiny_ensemble_handoff,
            "permission_note": tiny_ensemble_note,
        },
        "claim_boundaries": {
            "operational_claims_allowed": False,
            "scale_up_authorized": False,
            "annual_frequency_claims_allowed": False,
            "physical_probability_claims_allowed": False,
            "risk_exposure_vulnerability_claims_allowed": False,
        },
        "scale_up_authorized": False,
        "operational_claims_allowed": False,
    }
    return report


def build_candidate_generation_report(
    *,
    repo_root: Path,
    terrain_crop_path: Path,
    terrain_metadata_path: Path,
    source_zone_metadata_path: Path,
) -> dict[str, Any]:
    try:
        return AOI_CANDIDATES.build_report(
            repo_root=repo_root,
            terrain_crop_path=terrain_crop_path,
            terrain_metadata_path=terrain_metadata_path,
            source_zone_metadata_path=source_zone_metadata_path,
        )
    except AOI_CANDIDATES.TerrainReleaseZoneCandidateMetricsError as exc:
        return {
            "schema_version": AOI_CANDIDATES.SCHEMA_VERSION,
            "candidate_metrics_status": "blocked_missing_inputs",
            "candidate_release_zone_set_status": "not_emitted",
            "candidate_release_zone_interpretation": "not_claimed",
            "candidate_site_id": "chant_sura_fluelapass_portability_example_v1",
            "candidate_site_name": "Chant Sura / Flüelapass portability example",
            "blocked_missing_inputs": [
                str(terrain_crop_path),
                str(terrain_metadata_path),
                str(source_zone_metadata_path),
            ],
            "blocked_reason": str(exc),
            "scale_up_authorized": False,
            "operational_claims_allowed": False,
            "claim_boundaries": {
                "heuristic_workflow_input_only": True,
                "validated_release_zone_evidence": False,
                "field_validation_claims_allowed": False,
                "physical_release_probability_claims_allowed": False,
                "scale_up_authorized": False,
                "operational_claims_allowed": False,
                "notes": [
                    "candidate cells are heuristic workflow inputs, not validated release zones",
                    "candidate generation fails closed when the terrain crop is missing or malformed",
                ],
            },
        }


def build_case_skeleton_report(
    *,
    preflight_report: dict[str, Any],
    paths: dict[str, Path],
    repo_root: Path,
    readiness_report: dict[str, Any],
) -> dict[str, Any]:
    if preflight_report.get("core_input_status") != "ready":
        return {
            "schema_version": CASE_SKELETON.SCHEMA_VERSION,
            "case_skeleton_status": "blocked_missing_inputs",
            "reference_validation_status": "blocked_missing_inputs",
            "ensemble_execution_status": "blocked_template_only",
            "blocked_reason": preflight_report.get("blocked_reason", "required terrain, source-zone, scenario, or policy inputs are not ready"),
            "generated_case_path": "",
            "generated_case_paths": [],
            "write_status": "blocked",
            "scale_up_authorized": False,
            "operational_claims_allowed": False,
        }

    output_root = DEFAULT_TINY_ENSEMBLE_ROOT
    case_path = output_root / CASE_SKELETON.CASE_FILENAME
    case = CASE_SKELETON.build_case_skeleton(
        preflight_report=preflight_report,
        paths=paths,
        output_root=output_root,
        case_path=case_path,
    )
    case["generation_boundary"]["preflight_status"] = readiness_report["real_context_readiness_gate_status"]
    return {
        "schema_version": CASE_SKELETON.SCHEMA_VERSION,
        "case_skeleton_status": "ready",
        "reference_validation_status": "ready",
        "ensemble_execution_status": "blocked_template_only",
        "blocked_reason": "deferred_public_context_inputs",
        "candidate_site_id": preflight_report.get("candidate_site_id", ""),
        "candidate_site_name": preflight_report.get("candidate_site_name", ""),
        "preflight_status": readiness_report["real_context_readiness_gate_status"],
        "generated_case_path": str(case_path),
        "generated_case_paths": [str(case_path)],
        "output_root": str(output_root),
        "output_path_strategy": "tmp_or_ignored_only",
        "write_status": "not_written",
        "site_extent": preflight_report.get("site_extent_or_placeholder", {}),
        "source_zone_scenario_contract": preflight_report.get("source_zone_scenario_contract", {}),
        "terrain_source_zone_scenario_policy_refs": {
            "terrain_crop": str(paths["terrain_crop"]),
            "terrain_metadata": str(paths["terrain_metadata"]),
            "source_zone_metadata": str(paths["source_zone_metadata"]),
            "scenario_table": str(paths["scenario_table"]),
            "source_scenario_policy": str(paths["source_scenario_policy"]),
        },
        "deferred_public_context_categories": list(preflight_report.get("deferred_public_context_categories", [])),
        "deferred_public_context_paths_or_patterns": list(preflight_report.get("deferred_public_context_paths_or_patterns", [])),
        "deferred_public_context_placeholders": case["deferred_public_context_placeholders"],
        "claim_boundaries": case["claim_boundaries"],
        "case_skeleton": case,
        "scale_up_authorized": False,
        "operational_claims_allowed": False,
    }


def collect_blocked_missing_inputs(
    *,
    readiness_report: dict[str, Any],
    preflight_report: dict[str, Any],
    candidate_generation_report: dict[str, Any],
    scenario_generation_report: dict[str, Any],
    command_plan_report: dict[str, Any],
    case_skeleton_report: dict[str, Any],
    prepared_pilot_input_classification: str,
    real_input_acquisition_handoff: dict[str, Any],
) -> list[str]:
    blocked: list[str] = []
    if prepared_pilot_input_classification == "missing":
        first_missing = str(
            readiness_report.get("first_missing_real_input_category")
            or real_input_acquisition_handoff.get("first_missing_real_input_category")
            or "terrain_crop"
        )
        blocked.append(f"prepared pilot acquisition package is missing real input category: {first_missing}")
        handoff_reason = str(
            real_input_acquisition_handoff.get("stop_condition")
            or real_input_acquisition_handoff.get("reason")
            or ""
        )
        if handoff_reason:
            blocked.append(f"TB-250 acquisition handoff: {handoff_reason}")
    return dedupe(blocked)


def build_prepared_pilot_provenance(
    preflight_report: dict[str, Any],
    prep_summary: dict[str, Any],
) -> dict[str, Any]:
    contract = preflight_report.get("public_geodata_workflow_contract", {})
    synthetic_fixture_readiness_status = str(contract.get("synthetic_fixture_readiness_status") or "not_applicable")
    synthetic_fixture_profile = str(contract.get("synthetic_fixture_profile") or "none")
    provenance_status = "fixture_backed" if synthetic_fixture_readiness_status == "ready" else "real_staged"
    return {
        "schema_version": "chant_sura_prepared_pilot_provenance_v1",
        "status": provenance_status,
        "candidate_site_id": preflight_report.get("candidate_site_id", ""),
        "candidate_site_name": preflight_report.get("candidate_site_name", ""),
        "synthetic_fixture_readiness_status": synthetic_fixture_readiness_status,
        "synthetic_fixture_profile": synthetic_fixture_profile,
        "site_config_path": prep_summary.get("site_config_path", ""),
        "synthetic_config": bool(prep_summary.get("synthetic_config")),
        "source": "public_geodata_workflow_contract.synthetic_fixture_readiness_status",
    }


def collect_blocked_fixture_backed_inputs(
    *,
    readiness_report: dict[str, Any],
    preflight_report: dict[str, Any],
    prepared_pilot_provenance: dict[str, Any],
) -> list[str]:
    if readiness_report.get("real_context_readiness_gate_status") != "blocked_fixture_backed_inputs":
        return []
    contract = preflight_report.get("public_geodata_workflow_contract", {})
    synthetic_fixture_profile = str(contract.get("synthetic_fixture_profile") or "unknown_fixture_profile")
    candidate_site_id = str(
        prepared_pilot_provenance.get("candidate_site_id")
        or preflight_report.get("candidate_site_id")
        or "unspecified_second_site"
    )
    return [
        f"{candidate_site_id}: synthetic fixture inputs are not public evidence",
        f"{candidate_site_id}: fixture_profile={synthetic_fixture_profile}",
    ]


def collect_blocked_partial_real_inputs(
    *,
    readiness_report: dict[str, Any],
    prepared_pilot_provenance: dict[str, Any],
) -> list[str]:
    if readiness_report.get("real_context_readiness_gate_status") != "blocked_partial_real_inputs":
        return []
    first_missing = str(prepared_pilot_provenance.get("first_missing_real_input_category") or "unknown")
    candidate_site_id = str(prepared_pilot_provenance.get("candidate_site_id") or "unspecified_second_site")
    return [
        f"{candidate_site_id}: prepared-pilot inputs are only partially real",
        f"{candidate_site_id}: first_missing_real_input_category={first_missing}",
    ]


def derive_first_missing_real_input_category(
    *,
    prepared_pilot_input_classification: str,
    acquisition_package: dict[str, Any],
) -> str:
    rows = acquisition_package_row_map(acquisition_package)
    if prepared_pilot_input_classification == "missing":
        for definition in READINESS_GATE.PREPARED_PILOT_REAL_INPUT_DEFINITIONS:
            if definition.get("deferred"):
                continue
            row = rows.get(definition["category"]) or {}
            classification = PREFLIGHT.text_value(row.get("classification")) or PREFLIGHT.text_value(
                row.get("current_status")
            )
            if classification != "real_staged":
                return definition["category"]
        return "terrain_crop"
    if prepared_pilot_input_classification == "fixture_backed":
        return "terrain_crop"
    if prepared_pilot_input_classification == "partial_real":
        for definition in READINESS_GATE.PREPARED_PILOT_REAL_INPUT_DEFINITIONS:
            if definition.get("deferred"):
                return str(definition["category"])
        return "swissimage_context"
    return ""


def derive_first_missing_real_input_classification(*, prepared_pilot_input_classification: str) -> str:
    if prepared_pilot_input_classification == "missing":
        return "missing"
    if prepared_pilot_input_classification == "fixture_backed":
        return "fixture_backed"
    if prepared_pilot_input_classification == "partial_real":
        return "deferred"
    return ""


def classify_workflow(
    *,
    prepared_pilot_input_classification: str,
    blocked_missing_inputs: list[str],
    blocked_fixture_backed_inputs: list[str],
    blocked_partial_real_inputs: list[str],
) -> str:
    if prepared_pilot_input_classification == "missing":
        return "blocked_missing_real_core_inputs"
    if blocked_fixture_backed_inputs:
        return "blocked_fixture_backed_inputs"
    if blocked_partial_real_inputs:
        return "blocked_partial_real_inputs"
    if blocked_missing_inputs:
        return "blocked_missing_inputs"
    return "ready_for_next_step"


def build_tiny_bounded_ensemble_handoff_status(
    *,
    workflow_classification: str,
    allow_tiny_ensemble_handoff: bool,
) -> str:
    if workflow_classification == "blocked_missing_real_core_inputs":
        return "blocked_missing_real_core_inputs"
    if workflow_classification == "blocked_fixture_backed_inputs":
        return "blocked_fixture_backed_inputs"
    if workflow_classification == "blocked_partial_real_inputs":
        return "blocked_partial_real_inputs"
    if workflow_classification != "ready_for_next_step":
        return "blocked_missing_inputs"
    return "ready" if allow_tiny_ensemble_handoff else "blocked_missing_permission"


def build_tiny_bounded_ensemble_handoff(
    *,
    candidate_site_id: str,
    candidate_site_name: str,
    repo_root: Path,
    case_skeleton_report: dict[str, Any],
    command_plan_report: dict[str, Any],
    readiness_report: dict[str, Any],
    real_input_acquisition_handoff: dict[str, Any],
    tiny_handoff_status: str,
    tiny_ensemble_note: str,
) -> dict[str, Any]:
    if tiny_handoff_status == "blocked_missing_real_core_inputs":
        blocked_reason = str(
            real_input_acquisition_handoff.get("stop_condition")
            or real_input_acquisition_handoff.get("reason")
            or "real-input acquisition package is not ready"
        )
    elif tiny_handoff_status == "blocked_fixture_backed_inputs":
        blocked_reason = "synthetic fixture inputs are not public evidence"
    elif tiny_handoff_status == "blocked_partial_real_inputs":
        blocked_reason = "prepared-pilot inputs are only partially real"
    elif tiny_handoff_status == "blocked_missing_permission":
        blocked_reason = "explicit permission not recorded"
    elif tiny_handoff_status == "blocked_missing_inputs":
        blocked_reason = "required real-context inputs are missing"
    else:
        blocked_reason = ""
    return {
        "schema_version": "chant_sura_tiny_bounded_ensemble_handoff_v1",
        "status": tiny_handoff_status,
        "candidate_site_id": candidate_site_id,
        "candidate_site_name": candidate_site_name,
        "repo_root": str(repo_root),
        "case_skeleton_path": case_skeleton_report.get("generated_case_path", ""),
        "command_plan_status": command_plan_report.get("command_plan_status", "blocked_missing_inputs"),
        "readiness_status": readiness_report.get("real_context_readiness_gate_status", "blocked_missing_inputs"),
        "requires_explicit_permission": True,
        "permission_note": tiny_ensemble_note,
        "blocked_reason": blocked_reason,
        "claim_boundaries": {
            "operational_claims_allowed": False,
            "scale_up_authorized": False,
            "physical_probability_claims_allowed": False,
        },
    }


def build_workflow_steps(
    *,
    readiness_report: dict[str, Any],
    case_skeleton_report: dict[str, Any],
    candidate_generation_report: dict[str, Any],
    scenario_generation_report: dict[str, Any],
    command_plan_report: dict[str, Any],
    tiny_handoff_report: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        {
            "step_id": "public_context_readiness",
            "status": readiness_report.get("real_context_readiness_gate_status", "blocked_missing_inputs"),
            "blocked_reason": readiness_report.get("public_context_boundary_status", ""),
            "expected_inputs": readiness_report.get("acquisition_manifest_product_summaries", []),
        },
        {
            "step_id": "aoi_preparation",
            "status": case_skeleton_report.get("case_skeleton_status", "blocked_missing_inputs"),
            "blocked_reason": case_skeleton_report.get("blocked_reason", ""),
            "expected_inputs": list(case_skeleton_report.get("terrain_source_zone_scenario_policy_refs", {}).values()),
        },
        {
            "step_id": "release_candidate_generation",
            "status": candidate_generation_report.get("candidate_metrics_status", "blocked_missing_inputs"),
            "blocked_reason": candidate_generation_report.get("blocked_reason", ""),
            "expected_inputs": list(candidate_generation_report.get("terrain_inputs", {}).values())
            + list(candidate_generation_report.get("source_zone_inputs", {}).values()),
        },
        {
            "step_id": "scenario_generation",
            "status": scenario_generation_report.get("scenario_plan_status", "blocked_missing_inputs"),
            "blocked_reason": scenario_generation_report.get("blocked_reason", ""),
            "expected_inputs": [
                scenario_generation_report.get("source_policy_provenance", {}).get("policy_path", ""),
                scenario_generation_report.get("reference_scenario_table", {}).get("path", ""),
            ],
        },
        {
            "step_id": "command_planning",
            "status": command_plan_report.get("command_plan_status", "blocked_missing_inputs"),
            "blocked_reason": command_plan_report.get("public_context_boundary_status", ""),
            "expected_inputs": list(command_plan_report.get("blocked_second_site_commands", [])),
        },
        {
            "step_id": "tiny_bounded_ensemble_handoff",
            "status": tiny_handoff_report.get("status", "blocked_missing_inputs"),
            "blocked_reason": tiny_handoff_report.get("blocked_reason", ""),
            "expected_inputs": [tiny_handoff_report.get("case_skeleton_path", "")],
        },
    ]


def dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        ordered.append(item)
    return ordered


def render_text_report(report: dict[str, Any]) -> str:
    provenance = report.get("prepared_pilot_provenance", {})
    handoff = report.get("real_input_acquisition_handoff", {})
    lines = [
        f"schema_version: {report['schema_version']}",
        f"workflow_classification: {report['workflow_classification']}",
        f"prepared_pilot_input_classification: {report.get('prepared_pilot_input_classification', '')}",
        f"first_missing_real_input_category: {report.get('first_missing_real_input_category', '')}",
        f"first_missing_real_input_classification: {report.get('first_missing_real_input_classification', '')}",
        f"candidate_site_id: {report['candidate_site_id']}",
        f"candidate_site_name: {report['candidate_site_name']}",
        f"scale_up_authorized: {str(report['scale_up_authorized']).lower()}",
        f"operational_claims_allowed: {str(report['operational_claims_allowed']).lower()}",
        "",
        "prepared_pilot_provenance:",
        f"- status: {provenance.get('status', '')}",
        f"- synthetic_fixture_readiness_status: {provenance.get('synthetic_fixture_readiness_status', '')}",
        f"- synthetic_fixture_profile: {provenance.get('synthetic_fixture_profile', '')}",
        f"- real_input_classification: {provenance.get('real_input_classification', '')}",
        f"- first_missing_real_input_category: {provenance.get('first_missing_real_input_category', '')}",
        f"- synthetic_config: {provenance.get('synthetic_config', False)}",
        "",
        "public_context_readiness:",
        f"- real_context_readiness_gate_status: {report['public_context_readiness'].get('real_context_readiness_gate_status', '')}",
        f"- real_context_product_readiness_status: {report['public_context_readiness'].get('real_context_product_readiness', {}).get('readiness_status', '')}",
        f"- real_context_product_ready_count: {report['public_context_readiness'].get('real_context_product_readiness', {}).get('ready_product_count', '')}",
        f"- real_context_product_deferred_count: {report['public_context_readiness'].get('real_context_product_readiness', {}).get('deferred_product_count', '')}",
        f"- real_context_product_missing_count: {report['public_context_readiness'].get('real_context_product_readiness', {}).get('missing_product_count', '')}",
        f"- real_context_staging_checklist_state: {report['public_context_readiness'].get('real_context_staging_checklist_state', '')}",
        f"- deferred_public_context_status: {report['public_context_readiness'].get('deferred_public_context_status', '')}",
        "",
        "aoi_preparation:",
        f"- case_skeleton_status: {report['aoi_preparation'].get('case_skeleton_status', '')}",
        f"- generated_case_path: {report['aoi_preparation'].get('generated_case_path', '')}",
        f"- blocked_reason: {report['aoi_preparation'].get('blocked_reason', '')}",
        "",
        "release_candidate_generation:",
        f"- candidate_metrics_status: {report['release_candidate_generation'].get('candidate_metrics_status', '')}",
        f"- candidate_release_zone_set_status: {report['release_candidate_generation'].get('candidate_release_zone_set_status', '')}",
        "",
        "scenario_generation:",
        f"- scenario_plan_status: {report['scenario_generation'].get('scenario_plan_status', '')}",
        "",
        "command_planning:",
        f"- command_plan_status: {report['command_planning'].get('command_plan_status', '')}",
        f"- blocked_template_commands: {report['command_planning'].get('blocked_template_commands', [])}",
        "",
        "tiny_bounded_ensemble_handoff:",
        f"- status: {report['tiny_bounded_ensemble_handoff'].get('status', '')}",
        f"- blocked_reason: {report['tiny_bounded_ensemble_handoff'].get('blocked_reason', '')}",
        f"- permission_note: {report['tiny_bounded_ensemble_handoff'].get('permission_note', '')}",
        "",
        "real_input_acquisition_handoff:",
        f"- next_action_recommendation: {handoff.get('next_action_recommendation', '')}",
        f"- authorization_or_defer_status: {handoff.get('authorization_or_defer_status', '')}",
        f"- first_missing_real_input_category: {handoff.get('first_missing_real_input_category', '')}",
        f"- first_missing_real_input_classification: {handoff.get('first_missing_real_input_classification', '')}",
        f"- expected_source_product: {handoff.get('expected_source_product', '')}",
        f"- expected_local_path: {handoff.get('expected_local_path', '')}",
        f"- authorization_required: {handoff.get('authorization_required', False)}",
        f"- reason: {handoff.get('reason', '')}",
        f"- stop_condition: {handoff.get('stop_condition', '')}",
        "",
        "workflow_steps:",
    ]
    for step in report.get("workflow_steps", []):
        lines.append(f"- {step.get('step_id', '')}: {step.get('status', '')}")
        if step.get("blocked_reason"):
            lines.append(f"  blocked_reason: {step['blocked_reason']}")
    if report.get("blocked_fixture_backed_inputs"):
        lines.extend(["", "blocked_fixture_backed_inputs:"])
        lines.extend(f"- {item}" for item in report["blocked_fixture_backed_inputs"])
    if report.get("blocked_partial_real_inputs"):
        lines.extend(["", "blocked_partial_real_inputs:"])
        lines.extend(f"- {item}" for item in report["blocked_partial_real_inputs"])
    if report.get("blocked_missing_inputs") and report["workflow_classification"] == "blocked_missing_real_core_inputs":
        lines.extend(["", "blocked_missing_real_core_inputs:"])
        lines.extend(f"- {item}" for item in report["blocked_missing_inputs"])
    elif report.get("blocked_missing_inputs"):
        lines.extend(["", "blocked_missing_inputs:"])
        lines.extend(f"- {item}" for item in report["blocked_missing_inputs"])
    lines.extend(["", "ready_for_next_step:"])
    ready = report.get("ready_for_next_step", {})
    lines.append(f"- status: {ready.get('status', '')}")
    lines.append(f"- next_step: {ready.get('next_step', '')}")
    lines.append(f"- requires_explicit_permission: {ready.get('requires_explicit_permission', False)}")
    lines.append(f"- permission_recorded: {ready.get('permission_recorded', False)}")
    lines.append(f"- permission_note: {ready.get('permission_note', '')}")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
