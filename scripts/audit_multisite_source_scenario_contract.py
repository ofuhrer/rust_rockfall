#!/usr/bin/env python3
"""Audit portable versus site-specific source-zone / scenario contract fields.

This helper compares the frozen Tschamut source-zone and block-scenario
records against a candidate second-site manifest. It is metadata-only and
read-only: it does not download geodata, regenerate cases, run ensembles, or
build hazard layers.
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except ImportError as exc:  # pragma: no cover - environment setup.
    raise SystemExit("PyYAML is required; install with `python3 -m pip install PyYAML`") from exc


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "multisite_source_scenario_contract_audit_v1"
DEFAULT_CANDIDATE_SITE_CONFIG = (
    ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml"
)


def _load_module(module_name: str, filename: str):
    path = ROOT / "scripts" / filename
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


READINESS = _load_module("same_scale_artifact_readiness_for_contract_audit", "check_same_scale_artifact_readiness.py")
PORTABILITY = _load_module("second_site_public_geodata_preflight_for_contract_audit", "check_second_site_public_geodata_preflight.py")

TSCHAMUT_POLICY = ROOT / "validation/policies/tschamut_public_source_scenario_policy_v1.yaml"
TSCHAMUT_GATE_FREEZE = ROOT / "validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml"
TSCHAMUT_TARGET_FREEZE = ROOT / "validation/pilot_runs/tschamut_public_scalable_conditional_target_gate_v1.yaml"
TSCHAMUT_SOURCE_ZONE_METADATA = ROOT / "data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_source_zone_metadata_v1.yaml"
TSCHAMUT_SCENARIO_TABLE = ROOT / "data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_scenario_table_v1.csv"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-site-config", type=Path, default=DEFAULT_CANDIDATE_SITE_CONFIG)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    args = parser.parse_args(argv)

    report = build_report(args.candidate_site_config)

    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    output = json.dumps(report, indent=2, sort_keys=True) if args.format == "json" else render_text_report(report)
    print(output)
    return 0 if report["source_scenario_contract_audit_status"] == "ready" else 2


def build_report(candidate_site_config: Path) -> dict[str, Any]:
    readiness = READINESS.build_readiness_report()
    candidate_config = load_yaml(candidate_site_config) if candidate_site_config.exists() else {}
    candidate = PORTABILITY.build_report(candidate_site_config, site_id=None)

    tschamut_policy = load_yaml(TSCHAMUT_POLICY)
    tschamut_gate = load_yaml(TSCHAMUT_GATE_FREEZE)
    tschamut_target = load_yaml(TSCHAMUT_TARGET_FREEZE)
    tschamut_source_zone = load_yaml(TSCHAMUT_SOURCE_ZONE_METADATA, default={})
    tschamut_scenario_rows = load_csv(TSCHAMUT_SCENARIO_TABLE, default=[])

    candidate_contract = candidate.get("source_zone_scenario_contract", {})

    tschamut_available_fields = build_tschamut_available_fields(
        tschamut_policy=tschamut_policy,
        tschamut_gate=tschamut_gate,
        tschamut_target=tschamut_target,
        tschamut_source_zone=tschamut_source_zone,
        tschamut_scenario_rows=tschamut_scenario_rows,
    )
    candidate_available_fields = build_candidate_available_fields(candidate_config, candidate, candidate_contract)

    field_records = build_field_records(
        tschamut_available_fields,
        candidate,
        candidate_config,
        candidate_available_fields,
        candidate_contract,
    )
    semantic_portability_matrix = build_semantic_portability_matrix(
        tschamut_available_fields=tschamut_available_fields,
        candidate_available_fields=candidate_available_fields,
        field_records=field_records,
        candidate_contract=candidate_contract,
        candidate_report=candidate,
    )

    classifications = {
        "portable_required": [rec["field"] for rec in field_records if rec["classification"] == "portable_required"],
        "site_specific_required": [rec["field"] for rec in field_records if rec["classification"] == "site_specific_required"],
        "tschamut_specific_heuristics": [rec["field"] for rec in field_records if rec["classification"] == "tschamut_specific_heuristic"],
        "missing_for_second_site": [rec["field"] for rec in field_records if rec["classification"] == "missing_for_second_site"],
        "optional_or_deferred": [rec["field"] for rec in field_records if rec["classification"] == "optional_or_deferred"],
        "out_of_scope_for_current_phase": [rec["field"] for rec in field_records if rec["classification"] == "out_of_scope_for_current_phase"],
    }

    candidate_missing = candidate.get("missing_input_categories", [])
    candidate_missing_paths = candidate.get("missing_input_paths_or_patterns", [])
    required_path_patterns_or_manifest_keys = {
        category: path for category, path in zip(candidate_missing, candidate_missing_paths, strict=False)
    }

    missing_second_site_fields = [rec["field"] for rec in field_records if rec["classification"] == "missing_for_second_site"]
    if not missing_second_site_fields:
        missing_second_site_fields = list(candidate_missing)

    blocked_reason = candidate.get("blocked_reason", "none")
    source_scenario_contract_audit_status = "ready" if not candidate_missing and candidate.get("portability_preflight_status") == "ready" else "measured"

    report = {
        "source_scenario_contract_audit_status": source_scenario_contract_audit_status,
        "tschamut_readiness_status": readiness["readiness_status"],
        "second_site_portability_status": candidate["portability_preflight_status"],
        "candidate_site_id": candidate["candidate_site_id"],
        "candidate_site_name": candidate["candidate_site_name"],
        "candidate_selection_rationale": candidate["candidate_selection_rationale"],
        "fields_audited": [rec["field"] for rec in field_records],
        "field_classifications": classifications,
        "field_records": field_records,
        "semantic_portability_matrix": semantic_portability_matrix,
        "synthetic_contract_fixture_status": {
            "chant_sura_candidate_manifest": "synthetic_contract_fixture",
            "chant_sura_source_scenario_policy": "synthetic_contract_fixture",
            "physical_validation_evidence": "not_claimed",
        },
        "tschamut_frozen_record_status": {
            "source_zone_metadata": "ready" if tschamut_source_zone else "missing",
            "scenario_table": "ready" if tschamut_scenario_rows else "missing",
        },
        "tschamut_available_fields": tschamut_available_fields,
        "second_site_available_fields": candidate_available_fields,
        "missing_second_site_fields": missing_second_site_fields,
        "required_path_patterns_or_manifest_keys": required_path_patterns_or_manifest_keys,
        "portable_contract_fields": classifications["portable_required"],
        "site_specific_contract_fields": unique_ordered(
            classifications["site_specific_required"] + classifications["missing_for_second_site"]
        ),
        "tschamut_specific_heuristics": [
            {
                "field": rec["field"],
                "value": rec["tschamut_value"],
                "why": rec["notes"],
            }
            for rec in field_records
            if rec["classification"] == "tschamut_specific_heuristic"
        ],
        "optional_or_deferred_fields": classifications["optional_or_deferred"],
        "out_of_scope_fields": classifications["out_of_scope_for_current_phase"],
        "probability_semantics_boundary": {
            "sampling_weight_semantics": "conditional_sampling_only",
            "scenario_probability_semantics": "normalized within a block family; no annual frequency claim",
            "unsupported_claims": [
                "annual_frequency",
                "physical_probability",
                "risk",
                "exposure",
                "vulnerability",
                "operational_claims",
            ],
        },
        "validation_or_field_evidence_boundary": {
            "observed_deposition_or_field_observation": "optional_if_site_specific_QA_source_exists",
            "not_validation_evidence_by_itself": True,
            "notes": [
                "contract fields define staging requirements only",
                "no field-validation evidence is invented or inferred",
                "candidate portability remains blocked until required inputs are staged",
            ],
        },
        "next_required_artifacts": next_required_artifacts(candidate_missing, required_path_patterns_or_manifest_keys),
        "blocked_reason": blocked_reason,
        "scale_up_authorized": False,
        "operational_claims_allowed": False,
    }
    return report


def load_yaml(path: Path, default: dict[str, Any] | None = None) -> dict[str, Any]:
    if not path.exists():
        return default or {}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def load_csv(path: Path, default: list[dict[str, str]] | None = None) -> list[dict[str, str]]:
    if not path.exists():
        return default or []
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def text_value(value: Any) -> str:
    return str(value).strip() if value not in (None, "") else ""


def build_tschamut_available_fields(
    *,
    tschamut_policy: dict[str, Any],
    tschamut_gate: dict[str, Any],
    tschamut_target: dict[str, Any],
    tschamut_source_zone: dict[str, Any],
    tschamut_scenario_rows: list[dict[str, str]],
) -> dict[str, Any]:
    policy_source_zone = tschamut_policy.get("source_zone_policy", {}) if isinstance(tschamut_policy.get("source_zone_policy"), dict) else {}
    policy_release_sampling = policy_source_zone.get("release_sampling", {}) if isinstance(policy_source_zone.get("release_sampling"), dict) else {}
    policy_block_policy = tschamut_policy.get("block_scenario_policy", {}) if isinstance(tschamut_policy.get("block_scenario_policy"), dict) else {}
    policy_scenarios = policy_block_policy.get("scenarios", []) if isinstance(policy_block_policy.get("scenarios"), list) else []
    source_zone_record = tschamut_source_zone if isinstance(tschamut_source_zone, dict) else {}
    release_sampling_policy = source_zone_record.get("release_sampling_policy", {}) if isinstance(source_zone_record.get("release_sampling_policy"), dict) else {}
    return {
        "site_id_and_naming": {
            "pilot_id": text_value(tschamut_gate.get("pilot_id")),
            "run_id": text_value(tschamut_gate.get("run_id")),
            "map_product_id": text_value(tschamut_gate.get("run_id")) or "tschamut_public_conditional_gate_v1",
        },
        "site_extent_and_crs": {
            "crs_epsg": text_value(tschamut_gate.get("hazard_output_plan", {}).get("explicit_grid", {}).get("crs_epsg"))
            or "EPSG:2056",
            "vertical_datum": text_value(tschamut_policy.get("source_zone_policy", {}).get("coordinate_reference_system", {}).get("vertical_datum"))
            or "LN02",
            "grid": {
                "xmin": tschamut_gate.get("hazard_output_plan", {}).get("explicit_grid", {}).get("xmin"),
                "ymin": tschamut_gate.get("hazard_output_plan", {}).get("explicit_grid", {}).get("ymin"),
                "ncols": tschamut_gate.get("hazard_output_plan", {}).get("explicit_grid", {}).get("ncols"),
                "nrows": tschamut_gate.get("hazard_output_plan", {}).get("explicit_grid", {}).get("nrows"),
                "cell_size_m": tschamut_gate.get("hazard_output_plan", {}).get("explicit_grid", {}).get("cell_size_m"),
            },
        },
        "terrain_crop_path": text_value(tschamut_gate.get("input_freeze", {}).get("terrain_metadata_path")),
        "terrain_metadata_path": text_value(tschamut_gate.get("input_freeze", {}).get("terrain_metadata_path")),
        "source_zone_metadata_path": text_value(tschamut_gate.get("input_freeze", {}).get("source_zone_metadata_path")),
        "scenario_table_path": text_value(tschamut_gate.get("input_freeze", {}).get("scenario_table_path")),
        "source_zone_id": text_value(source_zone_record.get("source_zone_id")) or text_value(policy_source_zone.get("source_zone_id")) or "tschamut_public_lps_release_bbox",
        "source_zone_geometry": text_value(policy_source_zone.get("geometry", {}).get("type")),
        "release_sampling_mode": text_value(release_sampling_policy.get("mode")) or text_value(policy_release_sampling.get("mode")) or "deterministic_grid",
        "release_sampling_seed": release_sampling_policy.get("seed") if release_sampling_policy.get("seed") is not None else policy_release_sampling.get("seed") if policy_release_sampling.get("seed") is not None else 34014,
        "release_cell_id_prefix": text_value(release_sampling_policy.get("release_cell_id_prefix")) or text_value(policy_release_sampling.get("release_cell_id_prefix")) or "tschamut_public_release_cell",
        "release_count": release_sampling_policy.get("release_count") if release_sampling_policy.get("release_count") is not None else policy_release_sampling.get("requested_release_cell_count") if policy_release_sampling.get("requested_release_cell_count") is not None else 10,
        "release_point_table_shape": "one row per release point",
        "release_point_rows": [dict(row) for row in release_sampling_policy.get("release_cells", [])] if release_sampling_policy.get("release_cells") else "actual release-point rows derived from public Tschamut inputs",
        "block_scenario_table_shape": "CSV table with one row per block / scenario record",
        "block_scenario_rows": [dict(row) for row in tschamut_scenario_rows] if tschamut_scenario_rows else [dict(scenario) for scenario in policy_scenarios],
        "block_mass_radius_values": [
            {
                "block_scenario_id": scenario.get("block_scenario_id"),
                "block_mass_kg": scenario.get("block_mass_kg"),
                "block_radius_m": scenario.get("block_radius_m"),
                "sampling_weight": scenario.get("sampling_weight"),
            }
            for scenario in policy_scenarios
        ],
        "sampling_weight_semantics": text_value(policy_release_sampling.get("sampling_weight_semantics")),
        "scenario_probability_semantics": text_value(policy_block_policy.get("sampling_weight_semantics")),
        "random_seed": tschamut_gate.get("sampling_plan", {}).get("random_seed"),
        "ensemble_size": {
            "gate": tschamut_gate.get("sampling_plan", {}).get("gate_run_trajectories_per_release_zone"),
            "target": tschamut_gate.get("sampling_plan", {}).get("target_trajectories_per_release_zone"),
        },
        "output_root_naming": {
            "validation_results": text_value(tschamut_gate.get("hazard_output_plan", {}).get("output_roots", {}).get("validation_results")),
            "hazard_results": text_value(tschamut_gate.get("hazard_output_plan", {}).get("output_roots", {}).get("hazard_results")),
        },
        "context_layer_expectations": [
            "SWISSIMAGE",
            "swissTLM3D",
            "swissSURFACE3D",
            "swissSURFACE3D Raster",
            "swissBUILDINGS3D",
        ],
        "validation_or_field_evidence_boundary": {
            "manual_qgis_visual_qa": text_value(tschamut_gate.get("workflow_gates", {}).get("visual_qa_recorded")),
            "field_validation": "not required by this contract audit",
        },
        "probability_semantics_boundary": {
            "conditional_sampling_only": True,
            "annual_frequency_supported": False,
            "physical_probability_supported": False,
        },
        "source_scenario_policy_path": text_value(tschamut_gate.get("input_freeze", {}).get("source_scenario_policy_path"))
        or text_value(TSCHAMUT_POLICY),
    }


def build_candidate_available_fields(
    candidate_config: dict[str, Any],
    candidate_report: dict[str, Any],
    contract: dict[str, Any],
) -> dict[str, Any]:
    site_extent = candidate_config.get("site_extent", {}) if isinstance(candidate_config.get("site_extent"), dict) else {}
    return {
        "candidate_site_id": candidate_config.get("candidate_site_id") or candidate_report.get("candidate_site_id"),
        "candidate_site_name": candidate_config.get("candidate_site_name") or candidate_report.get("candidate_site_name"),
        "candidate_selection_rationale": candidate_config.get("candidate_selection_rationale") or candidate_report.get("candidate_selection_rationale"),
        "site_extent": site_extent,
        "source_zone_scenario_contract": contract,
        "expected_processed_input_root": candidate_config.get("expected_processed_input_root"),
        "expected_processed_context_root": candidate_config.get("expected_processed_context_root"),
        "expected_terrain_crop_path": candidate_config.get("expected_terrain_crop_path"),
        "expected_terrain_metadata_path": candidate_config.get("expected_terrain_metadata_path"),
        "expected_source_zone_metadata_path": candidate_config.get("expected_source_zone_metadata_path"),
        "expected_scenario_table_path": candidate_config.get("expected_scenario_table_path"),
        "expected_source_scenario_policy_path": candidate_config.get("expected_source_scenario_policy_path"),
        "expected_validation_private_root": candidate_config.get("expected_validation_private_root"),
        "expected_hazard_results_root": candidate_config.get("expected_hazard_results_root"),
        "expected_swissimage_context_root": candidate_config.get("expected_swissimage_context_root"),
        "expected_swisstlm3d_context_root": candidate_config.get("expected_swisstlm3d_context_root"),
        "expected_swisstlm3d_metadata_path": candidate_config.get("expected_swisstlm3d_metadata_path"),
        "expected_swisssurface3d_context_root": candidate_config.get("expected_swisssurface3d_context_root"),
        "expected_swisssurface3d_raster_context_root": candidate_config.get("expected_swisssurface3d_raster_context_root"),
        "expected_swissbuildings3d_context_root": candidate_config.get("expected_swissbuildings3d_context_root"),
        "expected_barrier_inventory_root": candidate_config.get("expected_barrier_inventory_root"),
    }


def build_field_records(
    tschamut: dict[str, Any],
    candidate_report: dict[str, Any],
    candidate_config: dict[str, Any],
    candidate: dict[str, Any],
    candidate_contract: dict[str, Any],
) -> list[dict[str, Any]]:
    candidate_extent = candidate_config.get("site_extent", {}) if isinstance(candidate_config.get("site_extent"), dict) else {}
    missing_categories = set(candidate_report.get("missing_input_categories", []))

    def missing_for_site(category: str) -> bool:
        return category in missing_categories

    field_records: list[dict[str, Any]] = []

    def add(field: str, classification: str, tschamut_value: Any, candidate_value: Any, notes: str) -> None:
        field_records.append(
            {
                "field": field,
                "classification": classification,
                "tschamut_value": tschamut_value,
                "candidate_value": candidate_value,
                "tschamut_available": tschamut_value not in (None, "", [], {}),
                "candidate_available": candidate_value not in (None, "", [], {}),
                "notes": notes,
            }
        )

    add(
        "site_id_and_naming",
        "site_specific_required",
        {"pilot_id": tschamut["site_id_and_naming"]["pilot_id"], "run_id": tschamut["site_id_and_naming"]["run_id"]},
        {"candidate_site_id": candidate.get("candidate_site_id"), "candidate_site_name": candidate.get("candidate_site_name")},
        "Each site needs its own identity and naming contract.",
    )
    add(
        "site_extent_and_crs",
        "site_specific_required",
        tschamut["site_extent_and_crs"],
        candidate_extent,
        "LV95 extent and CRS are site-specific but mandatory.",
    )
    add(
        "terrain_crop_path",
        "missing_for_second_site" if missing_for_site("terrain_crop") else "site_specific_required",
        tschamut["terrain_crop_path"],
        candidate.get("expected_terrain_crop_path"),
        "A candidate needs its own terrain crop path and staged terrain raster.",
    )
    add(
        "terrain_metadata_path",
        "missing_for_second_site" if missing_for_site("terrain_crs_vertical_datum") else "site_specific_required",
        tschamut["terrain_metadata_path"],
        candidate.get("expected_terrain_metadata_path"),
        "Terrain metadata must be staged for each site.",
    )
    add(
        "source_zone_metadata_path",
        "missing_for_second_site" if missing_for_site("source_zone_metadata") else "site_specific_required",
        tschamut["source_zone_metadata_path"],
        candidate.get("expected_source_zone_metadata_path"),
        "Source-zone metadata is site-specific and mandatory.",
    )
    add(
        "scenario_table_path",
        "missing_for_second_site" if missing_for_site("scenario_table") else "site_specific_required",
        tschamut["scenario_table_path"],
        candidate.get("expected_scenario_table_path"),
        "Block/scenario rows are site-specific and mandatory.",
    )
    add(
        "source_zone_id",
        "tschamut_specific_heuristic",
        tschamut["source_zone_id"],
        candidate_contract.get("source_zone_id") or "missing",
        "Tschamut uses a frozen source-zone id derived from public release rows; a new site needs its own source-zone id contract.",
    )
    add(
        "release_sampling_mode",
        "tschamut_specific_heuristic",
        tschamut["release_sampling_mode"],
        candidate_contract.get("release_sampling_mode") or "missing",
        "Tschamut uses a deterministic grid release-sampling heuristic; a second site needs its own declared mode.",
    )
    add(
        "release_sampling_seed",
        "tschamut_specific_heuristic",
        tschamut["release_sampling_seed"],
        candidate_contract.get("release_sampling_seed") or "missing",
        "The Tschamut release-sampling seed is frozen for the selected pilot and is not a portable site contract.",
    )
    add(
        "release_cell_id_prefix",
        "tschamut_specific_heuristic",
        tschamut["release_cell_id_prefix"],
        candidate_contract.get("release_cell_id_prefix") or "missing",
        "The release-cell prefix is a Tschamut naming heuristic, not a cross-site invariant.",
    )
    add(
        "release_count",
        "tschamut_specific_heuristic",
        tschamut["release_count"],
        candidate_contract.get("release_count") or "missing",
        "The selected release count is part of the frozen Tschamut heuristic and must be staged per site.",
    )
    add(
        "source_zone_id_pattern",
        "portable_required",
        "tschamut_public_* (inferred portable pattern contract)",
        candidate_contract.get("source_zone_id_pattern"),
        "A portable contract can express the source-zone id as a site-specific prefix pattern.",
    )
    add(
        "source_zone_geometry",
        "portable_required",
        tschamut["source_zone_geometry"],
        candidate_contract.get("source_zone_geometry"),
        "The contract requires a polygonal LV95 source-zone geometry across sites.",
    )
    add(
        "release_point_table_shape",
        "portable_required",
        tschamut["release_point_table_shape"],
        candidate_contract.get("release_point_table"),
        "The release-point table shape is portable, but the rows are site-specific.",
    )
    add(
        "release_point_rows",
        "missing_for_second_site" if missing_for_site("source_zone_metadata") else "site_specific_required",
        tschamut["release_point_rows"],
        "not staged",
        "Actual release-point rows must be staged for a second site.",
    )
    add(
        "observed_deposition_or_field_observation",
        "optional_or_deferred",
        "present in Tschamut benchmark records",
        candidate_contract.get("observed_deposition_or_field_observation"),
        "Field-observation evidence is optional and should not be invented for the candidate.",
    )
    add(
        "block_scenario_table_shape",
        "portable_required",
        tschamut["block_scenario_table_shape"],
        candidate_contract.get("block_scenario_table"),
        "The scenario table shape is portable; the rows are site-specific.",
    )
    add(
        "block_scenario_rows",
        "missing_for_second_site" if missing_for_site("scenario_table") else "site_specific_required",
        tschamut["block_scenario_rows"],
        "not staged",
        "Actual block/scenario rows must be staged for a second site.",
    )
    add(
        "block_mass_radius_values",
        "tschamut_specific_heuristic",
        tschamut["block_mass_radius_values"],
        "not staged",
        "Tschamut masses/radii are selected public rows; a second site needs its own block-population values.",
    )
    add(
        "sampling_weight_semantics",
        "portable_required",
        tschamut["sampling_weight_semantics"],
        "normalized within a block family; no annual frequency claim",
        "Conditional sampling-weight semantics are portable across sites; annual-frequency semantics are out of scope.",
    )
    add(
        "scenario_probability_semantics",
        "portable_required",
        tschamut["scenario_probability_semantics"],
        candidate_contract.get("scenario_probability_semantics"),
        "Probability semantics are conditional-only in this phase.",
    )
    add(
        "source_scenario_policy_path",
        "site_specific_required",
        tschamut["source_scenario_policy_path"],
        candidate.get("expected_source_scenario_policy_path"),
        "The candidate policy file is a synthetic contract fixture, not physical evidence.",
    )
    add(
        "random_seed",
        "site_specific_required",
        tschamut["random_seed"],
        "not staged",
        "A new site must choose and freeze its own seed; the Tschamut seed is not portable by itself.",
    )
    add(
        "ensemble_size",
        "site_specific_required",
        tschamut["ensemble_size"],
        "not staged",
        "Ensemble size is site- and question-specific; this audit does not change it.",
    )
    add(
        "output_root_naming",
        "site_specific_required",
        tschamut["output_root_naming"],
        {
            "validation_private_root": candidate.get("expected_validation_private_root"),
            "hazard_results_root": candidate.get("expected_hazard_results_root"),
        },
        "Each site needs its own ignored output-root naming convention.",
    )
    add(
        "context_layer_expectations",
        "site_specific_required",
        tschamut["context_layer_expectations"],
        [
            candidate.get("expected_swissimage_context_root"),
            candidate.get("expected_swisstlm3d_context_root"),
            candidate.get("expected_swisssurface3d_context_root"),
            candidate.get("expected_swisssurface3d_raster_context_root"),
            candidate.get("expected_swissbuildings3d_context_root"),
        ],
        "The context inventory is reusable as a category list, but each site must stage its own layers.",
    )
    add(
        "swissimage_context",
        "site_specific_required",
        tschamut["context_layer_expectations"][0],
        candidate.get("expected_swissimage_context_root"),
        "SWISSIMAGE is a site-specific context product that remains deferred until staged.",
    )
    add(
        "swisstlm3d_context",
        "site_specific_required",
        tschamut["context_layer_expectations"][1],
        candidate.get("expected_swisstlm3d_context_root"),
        "swissTLM3D context is site-specific and currently deferred.",
    )
    add(
        "swisstlm3d_metadata_path",
        "site_specific_required",
        "metadata path available in the portable contract only after staging",
        candidate.get("expected_swisstlm3d_metadata_path"),
        "swissTLM3D metadata is part of the staged context contract and stays deferred until present.",
    )
    add(
        "swisssurface3d_context",
        "site_specific_required",
        tschamut["context_layer_expectations"][2],
        candidate.get("expected_swisssurface3d_context_root"),
        "swissSURFACE3D context is site-specific and currently deferred.",
    )
    add(
        "swisssurface3d_raster_context",
        "site_specific_required",
        tschamut["context_layer_expectations"][3],
        candidate.get("expected_swisssurface3d_raster_context_root"),
        "swissSURFACE3D Raster context is site-specific and currently deferred.",
    )
    add(
        "swissbuildings3d_context",
        "site_specific_required",
        tschamut["context_layer_expectations"][4],
        candidate.get("expected_swissbuildings3d_context_root"),
        "swissBUILDINGS3D context is site-specific and currently deferred.",
    )
    add(
        "validation_or_field_evidence_boundary",
        "out_of_scope_for_current_phase",
        tschamut["validation_or_field_evidence_boundary"],
        candidate_contract.get("validation_or_field_evidence"),
        "Validation or field-evidence boundaries remain outside the contract audit.",
    )
    add(
        "annual_frequency_probability_boundary",
        "out_of_scope_for_current_phase",
        tschamut["probability_semantics_boundary"],
        candidate_contract.get("scenario_probability_semantics"),
        "Annual frequency, physical probability, risk, exposure, and vulnerability remain out of scope.",
    )
    return field_records


def build_semantic_portability_matrix(
    *,
    tschamut_available_fields: dict[str, Any],
    candidate_available_fields: dict[str, Any],
    field_records: list[dict[str, Any]],
    candidate_contract: dict[str, Any],
    candidate_report: dict[str, Any],
) -> dict[str, Any]:
    row_labels = {
        "site_id_and_naming": "site identity and naming",
        "site_extent_and_crs": "site extent and CRS",
        "terrain_crop_path": "terrain crop path",
        "terrain_metadata_path": "terrain metadata path",
        "source_zone_metadata_path": "source-zone metadata path",
        "scenario_table_path": "scenario table path",
        "source_zone_id": "source-zone id",
        "release_sampling_mode": "release sampling mode",
        "release_sampling_seed": "release sampling seed",
        "release_cell_id_prefix": "release-cell id prefix",
        "release_count": "release count",
        "source_zone_id_pattern": "source-zone id pattern",
        "source_zone_geometry": "source-zone geometry",
        "release_point_table_shape": "release-point table shape",
        "release_point_rows": "release-point rows",
        "observed_deposition_or_field_observation": "observed deposition or field observation",
        "block_scenario_table_shape": "block/scenario table shape",
        "block_scenario_rows": "block/scenario rows",
        "block_mass_radius_values": "block mass / radius values",
        "sampling_weight_semantics": "sampling weight semantics",
        "scenario_probability_semantics": "scenario probability semantics",
        "random_seed": "random seed",
        "ensemble_size": "ensemble size",
        "output_root_naming": "output-root naming",
        "context_layer_expectations": "context layer expectations",
        "validation_or_field_evidence_boundary": "validation / field-evidence boundary",
        "annual_frequency_probability_boundary": "annual frequency / probability boundary",
    }

    row_summaries = []
    for rec in field_records:
        field = rec["field"]
        row_summaries.append(
            {
                "field": field,
                "label": row_labels.get(field, field.replace("_", " ")),
                "classification": rec["classification"],
                "tschamut": {
                    "status": "available" if rec["tschamut_available"] else "not_available",
                    "value": rec["tschamut_value"],
                },
                "chant_sura": {
                    "status": candidate_status_for_field(field, rec, candidate_contract, candidate_report),
                    "value": rec["candidate_value"],
                },
                "notes": rec["notes"],
            }
        )

    return {
        "tschamut": {
            "site_name": "Tschamut",
            "role": "reference_contract_and_measured_pilot",
            "fixture_status": "frozen_reference_records",
            "available_fields": tschamut_available_fields,
        },
        "chant_sura": {
            "site_name": "Chant Sura / Flüelapass",
            "role": "candidate_contract_fixture",
            "fixture_status": "synthetic_contract_fixture",
            "deferred_public_context_status": candidate_report.get("deferred_public_context_status")
            if candidate_report.get("deferred_public_context_status") in {"deferred_public_context_inputs", "blocked_missing_inputs"}
            else "deferred_public_context_inputs",
            "available_fields": candidate_available_fields,
        },
        "rows": row_summaries,
    }


def candidate_status_for_field(
    field: str,
    record: dict[str, Any],
    candidate_contract: dict[str, Any],
    candidate_report: dict[str, Any],
) -> str:
    if field in {"observed_deposition_or_field_observation", "validation_or_field_evidence_boundary"}:
        return "synthetic_contract_fixture"
    if field == "source_scenario_policy_path":
        return "synthetic_contract_fixture"
    if field in {"site_id_and_naming", "site_extent_and_crs"}:
        return "staged_contract_fixture"
    if field in {
        "swissimage_context",
        "swisstlm3d_context",
        "swisstlm3d_metadata_path",
        "swisssurface3d_context",
        "swisssurface3d_raster_context",
        "swissbuildings3d_context",
    }:
        return "deferred_public_context"
    if field in {
        "terrain_crop_path",
        "terrain_metadata_path",
        "source_zone_metadata_path",
        "scenario_table_path",
        "output_root_naming",
        "context_layer_expectations",
    }:
        return "staged_core_fixture" if record["candidate_available"] else "missing"
    if field in {"source_zone_id_pattern", "source_zone_geometry", "release_point_table_shape", "block_scenario_table_shape", "sampling_weight_semantics", "scenario_probability_semantics"}:
        return "synthetic_contract_fixture"
    if field in {"source_zone_id", "release_sampling_mode", "release_sampling_seed", "release_cell_id_prefix", "release_count", "block_mass_radius_values"}:
        return "tschamut_heuristic_only"
    if field in {"release_point_rows", "block_scenario_rows", "random_seed", "ensemble_size"}:
        return "site_specific_required"
    if field in {"annual_frequency_probability_boundary"}:
        return "out_of_scope"
    return "synthetic_contract_fixture" if record["candidate_available"] else "missing"


def next_required_artifacts(
    missing_categories: list[str],
    required_path_patterns_or_manifest_keys: dict[str, str],
) -> list[dict[str, str]]:
    return [
        {
            "category": category,
            "path_or_pattern": required_path_patterns_or_manifest_keys.get(category, "unknown"),
        }
        for category in missing_categories
    ]


def unique_ordered(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            ordered.append(value)
    return ordered


def render_text_report(report: dict[str, Any]) -> str:
    lines = [
        f"source_scenario_contract_audit_status: {report['source_scenario_contract_audit_status']}",
        f"tschamut_readiness_status: {report['tschamut_readiness_status']}",
        f"second_site_portability_status: {report['second_site_portability_status']}",
        f"candidate_site_id: {report['candidate_site_id']}",
        f"candidate_site_name: {report['candidate_site_name']}",
        "synthetic_contract_fixture_status: "
        + ", ".join(
            [
                report["synthetic_contract_fixture_status"]["chant_sura_candidate_manifest"],
                report["synthetic_contract_fixture_status"]["chant_sura_source_scenario_policy"],
            ]
        ),
        f"blocked_reason: {report['blocked_reason']}",
        "portable_contract_fields: " + ", ".join(report["portable_contract_fields"]),
        "site_specific_contract_fields: " + ", ".join(report["site_specific_contract_fields"]),
        "semantic_portability_matrix:",
    ]
    for site_name in ("tschamut", "chant_sura"):
        site_matrix = report["semantic_portability_matrix"][site_name]
        lines.append(f"  - {site_name}: {site_matrix['fixture_status']} ({site_matrix['role']})")
    lines.append("tschamut_specific_heuristics:")
    for item in report["tschamut_specific_heuristics"]:
        lines.append(f"  - {item['field']}: {item['value']}")
    lines.append("missing_second_site_fields: " + ", ".join(report["missing_second_site_fields"]))
    lines.append("next_required_artifacts:")
    for item in report["next_required_artifacts"]:
        lines.append(f"  - {item['category']}: {item['path_or_pattern']}")
    lines.append("scale_up_authorized: false")
    lines.append("operational_claims_allowed: false")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
