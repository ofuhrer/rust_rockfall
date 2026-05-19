#!/usr/bin/env python3
"""Report Chant Sura real-context readiness without downloading public data.

The gate compares three things:

- the deterministic public-context acquisition plan from the Chant Sura
  acquisition manifest;
- the local staged core inputs and supporting ignored roots;
- the public-context products that remain intentionally deferred.

The script does not download swisstopo products, run a second-site ensemble, or
turn synthetic core fixtures into public-context evidence.
It also surfaces a staging checklist for the deferred public-context products,
but that checklist is a dry-run contract only and not a download or validation
claim.
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

try:
    import yaml  # type: ignore
except ImportError as exc:  # pragma: no cover - environment setup.
    raise SystemExit("PyYAML is required. Run this script with `PYENV_VERSION=system uv run python ...`; CI may use `requirements-tools.txt`") from exc

from scripts.lib.workflow_validation import resolve_optional_repo_path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "chant_sura_real_context_readiness_gate_v1"
REAL_CONTEXT_PRODUCT_READINESS_SCHEMA_VERSION = "chant_sura_real_context_product_readiness_v1"
REAL_CONTEXT_STAGING_CHECKLIST_SCHEMA_VERSION = "chant_sura_real_context_staging_checklist_v1"
PREPARED_PILOT_REAL_INPUT_READINESS_SCHEMA_VERSION = "chant_sura_prepared_pilot_real_input_readiness_v1"
REAL_INPUT_ACQUISITION_HANDOFF_SCHEMA_VERSION = "chant_sura_real_input_acquisition_handoff_v1"
BALFRIN_TRIGGER_MATRIX_SCHEMA_VERSION = "chant_sura_real_context_trigger_matrix_v1"
DEFAULT_SITE_CONFIG = ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml"
DEFAULT_ACQUISITION_PACKAGE = ROOT / "docs/chant_sura_fluelapass_public_context_acquisition_package.yaml"
DEFAULT_BALFRIN_EVIDENCE = ROOT / "validation/private/tschamut_public_pilot/balfrin_evidence_bundle_v1/balfrin_evidence_bundle_v1.json"
CHECKLIST_BOUNDARY_NOTE = (
    "Checklist only; it does not authorize downloads, create staged files, or claim "
    "validation, physical credibility, operational readiness, or scale-up."
)
DEFERRED_PUBLIC_CONTEXT_CATEGORIES = {
    "swissimage_context",
    "swisstlm3d_context",
    "swisstlm3d_metadata",
    "swisssurface3d_context",
    "swisssurface3d_raster_context",
    "swissbuildings3d_context",
}
CORE_INPUT_CATEGORIES = {
    "aoi_tile_catalog",
    "terrain_crop",
    "terrain_crs_vertical_datum",
    "source_zone_metadata",
    "scenario_table",
    "source_scenario_policy",
}
SUPPORTING_ROOT_CATEGORIES = {
    "processed_input_root",
    "processed_context_root",
    "validation_case_root",
    "hazard_results_root",
}
BALFRIN_TRIGGER_PRODUCTS = [
    {"category": "swissimage_context", "product": "SWISSIMAGE", "staging_priority": 1},
    {"category": "swisstlm3d_context", "product": "swissTLM3D", "staging_priority": 2},
    {"category": "swisssurface3d_context", "product": "swissSURFACE3D", "staging_priority": 3},
    {"category": "swisssurface3d_raster_context", "product": "swissSURFACE3D Raster", "staging_priority": 4},
    {"category": "swissbuildings3d_context", "product": "swissBUILDINGS3D", "staging_priority": 5},
]
BALFRIN_PROCEED_STATUSES = {"measured_conditional_diagnostic"}
BALFRIN_DEFER_STATUSES = {"inconclusive_conditional_diagnostic"}
BALFRIN_BLOCKED_STATUSES = {"blocked_missing_inputs"}
PREPARED_PILOT_REAL_INPUT_ROW_STATUSES = {
    "real_staged",
    "fixture_backed",
    "missing",
    "deferred",
}

PREPARED_PILOT_REAL_INPUT_DEFINITIONS = [
    {
        "category": "terrain_crop",
        "product": "swissALTI3D",
        "required": True,
        "path_key": "terrain_crop",
        "validator_category": "terrain_crop",
        "required_fields": ["file_present", "non_empty"],
    },
    {
        "category": "terrain_metadata",
        "product": "swissALTI3D terrain metadata",
        "required": True,
        "path_key": "terrain_metadata",
        "validator_category": "terrain_crs_vertical_datum",
        "required_fields": [
            "coordinate_reference_system.epsg",
            "coordinate_reference_system.vertical_datum",
            "preprocessing.crop_extent_lv95_m",
            "provenance.intended_use",
        ],
    },
    {
        "category": "aoi_tile_catalog",
        "product": "AOI tile catalog for deterministic swisstopo discovery",
        "required": True,
        "path_key": "aoi_tile_catalog",
        "validator_category": "aoi_tile_catalog",
        "required_fields": [
            "schema_version",
            "catalog_status",
            "source_product",
            "product_id",
            "crs",
            "resolution_m",
            "tiles",
            "tiles[*].tile_id",
            "tiles[*].source_product",
            "tiles[*].source_url",
            "tiles[*].extent_lv95_m",
        ],
    },
    {
        "category": "source_zone_metadata",
        "product": "release / source-zone metadata",
        "required": True,
        "path_key": "source_zone_metadata",
        "validator_category": "source_zone_metadata",
        "required_fields": [
            "zone_id",
            "geometry.type",
            "geometry.coordinates",
            "release_points",
            "coordinate_reference_system.vertical_datum",
            "provenance.intended_use",
        ],
    },
    {
        "category": "scenario_table",
        "product": "block / scenario table",
        "required": True,
        "path_key": "scenario_table",
        "validator_category": "scenario_table",
        "required_fields": [
            "scenario_id",
            "source_zone_id",
            "block_family",
            "relative_weight",
            "probability_semantics",
            "release_point_id",
        ],
    },
    {
        "category": "source_scenario_policy",
        "product": "source-scenario policy record",
        "required": True,
        "path_key": "source_scenario_policy",
        "validator_category": "source_scenario_policy",
        "required_fields": [
            "policy_id",
            "site_id",
            "source_zone_id_pattern",
            "source_zone_geometry",
            "release_point_table",
            "block_scenario_table",
            "scenario_probability_semantics",
        ],
    },
    {
        "category": "swissimage_context",
        "product": "SWISSIMAGE",
        "required": True,
        "path_key": "swissimage_context",
        "deferred": True,
    },
    {
        "category": "swisstlm3d_context",
        "product": "swissTLM3D",
        "required": True,
        "path_key": "swisstlm3d_context",
        "deferred": True,
    },
    {
        "category": "swisstlm3d_metadata",
        "product": "swissTLM3D metadata",
        "required": True,
        "path_key": "swisstlm3d_metadata",
        "deferred": True,
    },
    {
        "category": "swisssurface3d_context",
        "product": "swissSURFACE3D",
        "required": True,
        "path_key": "swisssurface3d_context",
        "deferred": True,
    },
    {
        "category": "swisssurface3d_raster_context",
        "product": "swissSURFACE3D Raster",
        "required": True,
        "path_key": "swisssurface3d_raster_context",
        "deferred": True,
    },
    {
        "category": "swissbuildings3d_context",
        "product": "swissBUILDINGS3D",
        "required": True,
        "path_key": "swissbuildings3d_context",
        "deferred": True,
    },
]

REAL_INPUT_DOWNLOAD_REQUEST_CATEGORIES = {"terrain_crop"}
REAL_INPUT_LOCAL_STAGING_CATEGORIES = {
    "terrain_metadata",
    "aoi_tile_catalog",
    "source_zone_metadata",
    "scenario_table",
    "source_scenario_policy",
}

CORE_PRODUCT_VALIDATION_RULES = {
    "aoi_tile_catalog": {
        "required_fields": [
            "schema_version",
            "catalog_status",
            "source_product",
            "product_id",
            "crs",
            "resolution_m",
            "tiles",
            "tiles[*].tile_id",
            "tiles[*].source_product",
            "tiles[*].source_url",
            "tiles[*].extent_lv95_m",
        ]
    },
    "terrain_crop": {
        "required_fields": [
            "file_present",
            "non_empty",
        ]
    },
    "terrain_crs_vertical_datum": {
        "required_fields": [
            "coordinate_reference_system.epsg",
            "coordinate_reference_system.vertical_datum",
            "preprocessing.crop_extent_lv95_m",
            "preprocessing.status",
            "provenance.intended_use",
        ]
    },
    "source_zone_metadata": {
        "required_fields": [
            "zone_id",
            "geometry.type",
            "geometry.coordinates",
            "release_points",
            "coordinate_reference_system.vertical_datum",
            "provenance.intended_use",
        ]
    },
    "scenario_table": {
        "required_fields": [
            "scenario_id",
            "source_zone_id",
            "block_family",
            "relative_weight",
            "probability_semantics",
            "release_point_id",
        ]
    },
    "source_scenario_policy": {
        "required_fields": [
            "policy_id",
            "site_id",
            "source_zone_id_pattern",
            "source_zone_geometry",
            "release_point_table",
            "block_scenario_table",
            "scenario_probability_semantics",
        ]
    },
}


def _load_preflight_module():
    path = ROOT / "scripts" / "check_second_site_public_geodata_preflight.py"
    spec = importlib.util.spec_from_file_location("chant_sura_real_context_preflight", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load preflight helper from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


PREFLIGHT = _load_preflight_module()


def _load_post_run_gate_module():
    path = ROOT / "scripts" / "summarize_balfrin_post_run_interpretation_gate.py"
    spec = importlib.util.spec_from_file_location("chant_sura_real_context_post_run_gate", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load post-run gate helper from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


post_run_gate = _load_post_run_gate_module()


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
    data = PREFLIGHT.load_site_config(path)
    return data if isinstance(data, dict) else {}


def build_prepared_pilot_real_input_readiness(
    acquisition_package: dict[str, Any],
    *,
    preflight_report: dict[str, Any],
    repo_root: Path,
) -> dict[str, Any]:
    package_rows = {
        PREFLIGHT.text_value(row.get("category")): row
        for row in (acquisition_package.get("required_acquisition_items") or [])
        if isinstance(row, dict) and PREFLIGHT.text_value(row.get("category"))
    }
    expected_paths = preflight_report.get("expected_local_paths") or {}

    required_states: list[dict[str, Any]] = []
    for definition in PREPARED_PILOT_REAL_INPUT_DEFINITIONS:
        category = definition["category"]
        package_row = package_rows.get(category)
        expected_path = (
            PREFLIGHT.text_value((package_row or {}).get("expected_path"))
            or PREFLIGHT.text_value(expected_paths.get(definition["path_key"]))
            or ""
        )
        required_states.append(
            build_prepared_pilot_real_input_row(
                definition=definition,
                package_row=package_row,
                expected_path=expected_path,
                repo_root=repo_root,
            )
        )

    core_states = [row for row in required_states if not row["deferred"]]
    deferred_states = [row for row in required_states if row["deferred"]]

    real_staged_states = [row for row in core_states if row["classification"] == "real_staged"]
    fixture_backed_states = [row for row in core_states if row["classification"] == "fixture_backed"]
    missing_states = [row for row in core_states if row["classification"] == "missing"]
    metadata_mismatch_states = [row for row in core_states if row["classification"] == "metadata_mismatch"]
    missing_row_states = [row for row in missing_states if row["missing_reason"] == "missing_row"]
    missing_file_states = [row for row in missing_states if row["missing_reason"] == "missing_file"]

    first_fixture_backed_input = next((row for row in core_states if row["classification"] == "fixture_backed"), None)
    first_missing_non_synthetic_input = next(
        (row for row in core_states if row["classification"] in {"missing", "metadata_mismatch"}),
        None,
    )

    if core_states and len(real_staged_states) == len(core_states):
        classification = "ready_real"
    elif real_staged_states:
        classification = "partial_real"
    elif metadata_mismatch_states:
        classification = "metadata_mismatch"
    elif fixture_backed_states and not missing_states and not metadata_mismatch_states:
        classification = "fixture_backed"
    else:
        classification = "missing"
    if classification == "partial_real" and first_missing_non_synthetic_input is None:
        first_missing_non_synthetic_input = first_fixture_backed_input

    report = {
        "schema_version": PREPARED_PILOT_REAL_INPUT_READINESS_SCHEMA_VERSION,
        "required_real_input_count": len(core_states),
        "real_staged_real_input_count": len(real_staged_states),
        "fixture_backed_real_input_count": len(fixture_backed_states),
        "metadata_mismatch_real_input_count": len(metadata_mismatch_states),
        "missing_real_input_count": len(missing_states),
        "missing_row_count": len(missing_row_states),
        "missing_file_count": len(missing_file_states),
        "deferred_real_input_count": len(deferred_states),
        "input_classification": classification,
        "first_missing_real_input_category": first_missing_non_synthetic_input["category"] if first_missing_non_synthetic_input else "",
        "first_missing_real_input_classification": first_missing_non_synthetic_input["classification"] if first_missing_non_synthetic_input else "",
        "first_missing_real_input_path": first_missing_non_synthetic_input["expected_path"] if first_missing_non_synthetic_input else "",
        "first_missing_real_input_required_fields": [] if first_missing_non_synthetic_input is None else list(first_missing_non_synthetic_input.get("required_fields") or []),
        "first_missing_real_input_missing_fields": [] if first_missing_non_synthetic_input is None else list(first_missing_non_synthetic_input.get("missing_fields") or []),
        "first_missing_real_input_issue": first_missing_non_synthetic_input or {},
        "first_fixture_backed_real_input_category": first_fixture_backed_input["category"] if first_fixture_backed_input else "",
        "first_fixture_backed_real_input_classification": first_fixture_backed_input["classification"] if first_fixture_backed_input else "",
        "first_fixture_backed_real_input_path": first_fixture_backed_input["expected_path"] if first_fixture_backed_input else "",
        "first_fixture_backed_real_input_missing_fields": [] if first_fixture_backed_input is None else list(first_fixture_backed_input.get("missing_fields") or []),
        "first_missing_non_synthetic_input": first_missing_non_synthetic_input or {},
        "required_real_inputs": core_states,
        "deferred_public_context_inputs": deferred_states,
    }
    return report


def build_real_input_acquisition_handoff(
    acquisition_package: dict[str, Any],
    *,
    prepared_pilot_real_input_readiness: dict[str, Any],
    preflight_report: dict[str, Any],
) -> dict[str, Any]:
    package_rows = {
        PREFLIGHT.text_value(row.get("category")): row
        for row in (acquisition_package.get("required_acquisition_items") or [])
        if isinstance(row, dict) and PREFLIGHT.text_value(row.get("category"))
    }
    first_missing = dict(prepared_pilot_real_input_readiness.get("first_missing_non_synthetic_input") or {})
    input_classification = str(prepared_pilot_real_input_readiness.get("input_classification") or "missing")

    if input_classification == "ready_real":
        return {
            "schema_version": REAL_INPUT_ACQUISITION_HANDOFF_SCHEMA_VERSION,
            "next_action_recommendation": "ready_no_handoff_needed",
            "authorization_or_defer_status": "no_action_needed",
            "first_missing_real_input_category": "",
            "first_missing_real_input_classification": "",
            "expected_source_product": "",
            "expected_local_path": "",
            "metadata_contract": [],
            "missing_metadata_fields": [],
            "authorization_required": False,
            "reason": "All real core inputs are staged with matching metadata; no acquisition handoff is needed.",
            "stop_condition": "No handoff stop condition; a real-input dry run can be requested after downstream gates pass.",
        }

    category = PREFLIGHT.text_value(first_missing.get("category"))
    classification = PREFLIGHT.text_value(first_missing.get("classification")) or input_classification
    package_row = package_rows.get(category) or next(
        (row for row in PREPARED_PILOT_REAL_INPUT_DEFINITIONS if row["category"] == category),
        {},
    )
    expected_local_path = (
        PREFLIGHT.text_value(first_missing.get("expected_path"))
        or PREFLIGHT.text_value(package_row.get("expected_path"))
        or PREFLIGHT.text_value((preflight_report.get("expected_local_paths") or {}).get(category))
    )
    expected_source_product = PREFLIGHT.text_value(package_row.get("product")) or category
    metadata_contract = list(package_row.get("metadata_fields") or package_row.get("required_fields") or [])
    missing_metadata_fields = list(first_missing.get("missing_fields") or [])

    if category in REAL_INPUT_DOWNLOAD_REQUEST_CATEGORIES:
        next_action = "request_download_authorization"
        authorization_status = "download_authorization_needed"
        reason = (
            f"The first missing real core input is {expected_source_product}; "
            "download authorization is required before any real-input dry run can stage it."
        )
        stop_condition = (
            f"Stop until download authorization is granted and {expected_local_path} can be staged as a real input."
        )
        authorization_required = True
    elif category in REAL_INPUT_LOCAL_STAGING_CATEGORIES:
        next_action = "stage_local_existing_input"
        authorization_status = "local_staging_needed"
        reason = (
            f"The first missing real core input is {expected_source_product}; "
            "stage the existing local input or metadata record at the expected path before rerunning."
        )
        stop_condition = f"Stop until {expected_local_path} exists with the listed metadata contract."
        authorization_required = False
    else:
        next_action = "defer_second_site"
        authorization_status = "second_site_deferred"
        reason = (
            "The current state does not identify a concrete local staging or download action for the first "
            "missing real core input, so second-site work stays deferred."
        )
        stop_condition = "Stop; do not treat fixtures as public evidence and do not proceed to a dry run."
        authorization_required = False

    return {
        "schema_version": REAL_INPUT_ACQUISITION_HANDOFF_SCHEMA_VERSION,
        "next_action_recommendation": next_action,
        "authorization_or_defer_status": authorization_status,
        "first_missing_real_input_category": category,
        "first_missing_real_input_classification": classification,
        "expected_source_product": expected_source_product,
        "expected_local_path": expected_local_path,
        "metadata_contract": metadata_contract,
        "missing_metadata_fields": missing_metadata_fields,
        "authorization_required": authorization_required,
        "reason": reason,
        "stop_condition": stop_condition,
    }


def build_prepared_pilot_real_input_row(
    *,
    definition: dict[str, Any],
    package_row: dict[str, Any] | None,
    expected_path: str,
    repo_root: Path,
) -> dict[str, Any]:
    category = definition["category"]
    product = PREFLIGHT.text_value((package_row or {}).get("product")) or definition["product"]
    required_fields = list(definition.get("required_fields") or [])
    deferred = bool(definition.get("deferred"))
    package_classification = PREFLIGHT.text_value((package_row or {}).get("classification")) or PREFLIGHT.text_value((package_row or {}).get("current_status"))

    if deferred:
        return {
            "category": category,
            "product": product,
            "classification": "deferred",
            "expected_path": expected_path,
            "required_fields": required_fields,
            "missing_fields": [],
            "metadata_mismatches": [],
            "row_present": package_row is not None,
            "file_present": False,
            "package_classification": package_classification or "deferred",
            "deferred": True,
            "missing_reason": "",
            "verification_status": "deferred",
            "notes": "public-context products remain intentionally deferred until staged and verified",
        }

    if package_row is None:
        return {
            "category": category,
            "product": product,
            "classification": "missing",
            "expected_path": expected_path,
            "required_fields": required_fields,
            "missing_fields": required_fields,
            "metadata_mismatches": [],
            "row_present": False,
            "file_present": False,
            "package_classification": "",
            "deferred": False,
            "missing_reason": "missing_row",
            "verification_status": "missing",
            "notes": "required real-input row is missing from the acquisition package",
        }

    resolved_path = resolve_optional_repo_path(repo_root, expected_path) or (repo_root / expected_path)
    file_present = resolved_path.exists()
    package_is_fixture_backed = package_classification == "fixture_backed"

    if file_present:
        validation_row = build_real_input_validation_row(
            category=category,
            expected_path=resolved_path,
            required_fields=required_fields,
        )
        if package_is_fixture_backed or real_input_payload_has_fixture_markers(resolved_path):
            return {
                **validation_row,
                "category": category,
                "product": product,
                "classification": "fixture_backed",
                "expected_path": expected_path,
                "required_fields": required_fields,
                "row_present": True,
                "file_present": True,
                "package_classification": package_classification or "fixture_backed",
                "deferred": False,
                "missing_reason": "fixture_backed",
                "verification_status": "fixture_backed",
                "notes": "fixture-backed inputs are intentionally non-evidence and do not count as real staging evidence",
            }
        if validation_row["classification"] == "ready":
            return {
                **validation_row,
                "category": category,
                "product": product,
                "classification": "real_staged",
                "expected_path": expected_path,
                "required_fields": required_fields,
                "row_present": True,
                "file_present": True,
                "package_classification": package_classification or "real_staged",
                "deferred": False,
                "missing_reason": "",
                "verification_status": "real_staged",
                "notes": "real staged input satisfies the local file and metadata contract",
            }
        return {
            **validation_row,
            "category": category,
            "product": product,
            "classification": "metadata_mismatch",
            "expected_path": expected_path,
            "required_fields": required_fields,
            "row_present": True,
            "file_present": True,
            "package_classification": package_classification or "real_staged",
            "deferred": False,
            "missing_reason": "metadata_mismatch",
            "verification_status": "metadata_mismatch",
            "notes": "staged file exists but metadata contract is incomplete or mismatched",
        }

    return {
        "category": category,
        "product": product,
        "classification": "missing",
        "expected_path": expected_path,
        "required_fields": required_fields,
        "missing_fields": required_fields,
        "metadata_mismatches": [],
        "row_present": True,
        "file_present": False,
        "package_classification": package_classification or "missing",
        "deferred": False,
        "missing_reason": "missing_file",
        "verification_status": "missing",
        "notes": "required real-input file is absent from the expected staged path",
    }


def build_real_input_validation_row(*, category: str, expected_path: Path, required_fields: list[str]) -> dict[str, Any]:
    validation_category = "terrain_crs_vertical_datum" if category == "terrain_metadata" else category
    validation_row = build_local_product_readiness_row(
        category=validation_category,
        local_core_input={"product": category},
        expected_path=str(expected_path),
        required_fields=required_fields,
    )
    return validation_row


def real_input_payload_has_fixture_markers(path: Path) -> bool:
    try:
        payload = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return False
    lowered = payload.lower()
    return any(
        marker in lowered
        for marker in (
            "synthetic",
            "fixture",
            "minimal_preflight",
            "placeholder_second_site",
            "placeholder",
        )
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site-config", type=Path, default=DEFAULT_SITE_CONFIG)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--acquisition-package", type=Path, default=DEFAULT_ACQUISITION_PACKAGE)
    parser.add_argument(
        "--balfrin-evidence-json",
        type=Path,
        default=DEFAULT_BALFRIN_EVIDENCE,
        help="optional measured Balfrin evidence bundle or post-run gate JSON",
    )
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    args = parser.parse_args(argv)

    report = build_report(
        args.site_config,
        repo_root=args.repo_root,
        acquisition_package_path=args.acquisition_package,
        balfrin_evidence_json=args.balfrin_evidence_json,
    )

    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    output = json.dumps(report, indent=2, sort_keys=True) if args.format == "json" else render_text_report(report)
    print(output)
    return 0 if report["real_context_readiness_gate_status"] == "ready_for_real_context_acquisition" else 2


def build_report(
    site_config: Path | None,
    *,
    repo_root: Path | None = None,
    acquisition_package_path: Path | None = None,
    balfrin_evidence_json: Path | None = None,
) -> dict[str, Any]:
    repo_root = repo_root or ROOT
    config_path = site_config or DEFAULT_SITE_CONFIG

    with _patched_repo_root(repo_root):
        config = PREFLIGHT.load_site_config(config_path) if config_path.exists() else {}
        candidate_site_id = PREFLIGHT.text_value(config.get("candidate_site_id")) or "unspecified_second_site"
        site_extent = config.get("site_extent") if isinstance(config.get("site_extent"), dict) else {}

        preflight_report = PREFLIGHT.build_report(config_path)
        paths = PREFLIGHT.build_paths(candidate_site_id, config)
        requirements = PREFLIGHT.build_requirements(candidate_site_id, site_extent, paths)
        acquisition_plan = list(preflight_report.get("public_context_acquisition_plan") or [])
        acquisition_package = load_acquisition_package(acquisition_package_path or DEFAULT_ACQUISITION_PACKAGE)
        acquisition_manifest = PREFLIGHT.load_site_config(
            Path(preflight_report["acquisition_manifest_path"])
        ) if preflight_report.get("acquisition_manifest_status") == "ready" else {}
        cache_contract = preflight_report["public_geodata_workflow_contract"]["public_geodata_cache_contract"]
        cache_manifest_path = Path(cache_contract["cache_layout"]["cache_manifest_path"])
        cache_verification_report = (
            PREFLIGHT.verify_public_geodata_cache(cache_manifest_path)
            if cache_manifest_path.exists()
            else None
        )
        balfrin_post_run_report = build_balfrin_post_run_report(load_balfrin_evidence_override(balfrin_evidence_json))
        balfrin_trigger_matrix = build_balfrin_trigger_matrix(balfrin_post_run_report)
        balfrin_trigger_summary = build_balfrin_trigger_summary(balfrin_post_run_report, balfrin_trigger_matrix)

        local_core_inputs = build_local_core_inputs(requirements)
        supporting_roots = build_supporting_roots(requirements)
        deferred_public_context_products = [entry for entry in acquisition_plan if entry["category"] in DEFERRED_PUBLIC_CONTEXT_CATEGORIES]
        real_context_product_readiness = build_real_context_product_readiness(
            acquisition_plan=acquisition_plan,
            cache_contract=cache_contract,
            cache_verification_report=cache_verification_report,
            local_core_inputs=local_core_inputs,
            preflight_report=preflight_report,
        )
        next_acquisition_decisions = build_next_acquisition_decisions(
            deferred_public_context_products,
            balfrin_trigger_summary,
        )
        real_context_staging_checklist = build_real_context_staging_checklist(
            real_context_product_readiness=real_context_product_readiness,
            cache_contract=cache_contract,
        )
        prepared_pilot_real_input_readiness = build_prepared_pilot_real_input_readiness(
            acquisition_package,
            preflight_report=preflight_report,
            repo_root=repo_root,
        )
        real_input_acquisition_handoff = build_real_input_acquisition_handoff(
            acquisition_package,
            prepared_pilot_real_input_readiness=prepared_pilot_real_input_readiness,
            preflight_report=preflight_report,
        )

        gate_status = determine_gate_status(
            core_input_status=preflight_report["core_input_status"],
            deferred_public_context_status=preflight_report["deferred_public_context_status"],
            deferred_public_context_products=deferred_public_context_products,
            real_context_product_readiness=real_context_product_readiness,
            prepared_pilot_real_input_readiness=prepared_pilot_real_input_readiness,
        )

        report = {
            "schema_version": SCHEMA_VERSION,
            "real_context_readiness_gate_status": gate_status,
            "readiness_status": gate_status,
            "prepared_pilot_real_input_readiness": prepared_pilot_real_input_readiness,
            "real_input_acquisition_handoff": real_input_acquisition_handoff,
            "prepared_pilot_input_classification": prepared_pilot_real_input_readiness["input_classification"],
            "first_missing_real_input_category": prepared_pilot_real_input_readiness["first_missing_real_input_category"],
            "first_missing_real_input_classification": prepared_pilot_real_input_readiness["first_missing_real_input_classification"],
            "first_missing_real_input_path": prepared_pilot_real_input_readiness["first_missing_real_input_path"],
            "first_missing_real_input_missing_fields": prepared_pilot_real_input_readiness["first_missing_real_input_missing_fields"],
            "first_fixture_backed_real_input_category": prepared_pilot_real_input_readiness["first_fixture_backed_real_input_category"],
            "first_fixture_backed_real_input_classification": prepared_pilot_real_input_readiness["first_fixture_backed_real_input_classification"],
            "first_fixture_backed_real_input_path": prepared_pilot_real_input_readiness["first_fixture_backed_real_input_path"],
            "first_missing_non_synthetic_input": prepared_pilot_real_input_readiness["first_missing_non_synthetic_input"],
            "candidate_site_id": preflight_report["candidate_site_id"],
            "candidate_site_name": preflight_report["candidate_site_name"],
            "candidate_selection_rationale": preflight_report["candidate_selection_rationale"],
            "site_extent": preflight_report["site_extent_or_placeholder"],
            "acquisition_manifest_status": preflight_report["acquisition_manifest_status"],
            "acquisition_manifest_path": preflight_report["acquisition_manifest_path"],
            "balfrin_evidence_path": str(balfrin_evidence_json or DEFAULT_BALFRIN_EVIDENCE),
            "core_input_status": preflight_report["core_input_status"],
            "deferred_public_context_status": preflight_report["deferred_public_context_status"],
            "deterministic_acquisition_plan": acquisition_plan,
            "local_core_inputs": local_core_inputs,
            "supporting_local_roots": supporting_roots,
            "deferred_public_context_products": deferred_public_context_products,
            "real_context_product_readiness": real_context_product_readiness,
            "next_acquisition_decisions": next_acquisition_decisions,
            "real_context_staging_checklist": real_context_staging_checklist,
            "real_context_staging_checklist_state": real_context_staging_checklist["checklist_state"],
            "balfrin_post_run_report": balfrin_post_run_report,
            "balfrin_trigger_summary": balfrin_trigger_summary,
            "balfrin_trigger_matrix": balfrin_trigger_matrix,
            "public_context_acquisition_summary": preflight_report["public_context_acquisition_summary"],
            "public_context_boundary_status": preflight_report["public_context_boundary_status"],
            "public_geodata_workflow_contract": preflight_report["public_geodata_workflow_contract"],
            "source_zone_scenario_contract": preflight_report["source_zone_scenario_contract"],
            "synthetic_core_inputs_are_public_context_evidence": False,
            "synthetic_fixture_boundaries": preflight_report["synthetic_fixture_boundaries"],
            "claim_boundaries": preflight_report["claim_boundaries"],
            "operational_claims_allowed": False,
            "scale_up_authorized": False,
            "acquisition_manifest_product_summaries": preflight_report["acquisition_manifest_product_summaries"],
            "local_staged_summary": summarize_local_staging(local_core_inputs, supporting_roots),
            "gate_boundary_summary": build_gate_boundary_summary(
                preflight_report["core_input_status"],
                preflight_report["deferred_public_context_status"],
                deferred_public_context_products,
            ),
            "acquisition_manifest": acquisition_manifest,
        }
    return report


def load_balfrin_evidence_override(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    if not path.exists():
        return {"missing_inputs": ["post_run_evidence_bundle"], "blocked_reason": f"missing Balfrin evidence JSON: {path}"}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Balfrin evidence override must be a JSON object")
    return data


def build_balfrin_post_run_report(evidence_override: dict[str, Any] | None) -> dict[str, Any] | None:
    if evidence_override is None:
        return None
    if "interpretation_status" in evidence_override and "artifact_acceptance_status" in evidence_override:
        return dict(evidence_override)
    if isinstance(evidence_override.get("post_run_interpretation_gate_report"), dict):
        return dict(evidence_override["post_run_interpretation_gate_report"])
    return post_run_gate.build_report(evidence_override)


def build_balfrin_trigger_matrix(post_run_report: dict[str, Any] | None) -> list[dict[str, Any]]:
    trigger_state = determine_balfrin_trigger_state(post_run_report)
    rows: list[dict[str, Any]] = []
    for product in BALFRIN_TRIGGER_PRODUCTS:
        rows.append(
            {
                "schema_version": BALFRIN_TRIGGER_MATRIX_SCHEMA_VERSION,
                "category": product["category"],
                "product": product["product"],
                "staging_priority": product["staging_priority"],
                "trigger_state": trigger_state,
                "decision": trigger_state,
                "next_acquisition_decision": next_trigger_decision(trigger_state),
                "proceed_when": {
                    "interpretation_status": "measured_conditional_diagnostic",
                    "artifact_acceptance_status": "accepted_conditional_diagnostic",
                    "usable_as_conditional_diagnostic_artifact": True,
                },
                "defer_when": {
                    "interpretation_status": "inconclusive_conditional_diagnostic",
                    "artifact_acceptance_status": "accepted_conditional_diagnostic",
                    "usable_as_conditional_diagnostic_artifact": True,
                },
                "blocked_when": {
                    "interpretation_status": "blocked_missing_inputs",
                    "artifact_acceptance_status": "blocked_missing_inputs",
                    "usable_as_conditional_diagnostic_artifact": False,
                },
                "balfrin_post_run_status": summarize_balfrin_post_run_status(post_run_report),
                "notes": balfrin_trigger_notes(trigger_state, product["product"]),
            }
        )
    return rows


def build_balfrin_trigger_summary(
    post_run_report: dict[str, Any] | None,
    trigger_matrix: list[dict[str, Any]],
) -> dict[str, Any]:
    trigger_state = determine_balfrin_trigger_state(post_run_report)
    return {
        "schema_version": BALFRIN_TRIGGER_MATRIX_SCHEMA_VERSION,
        "trigger_state": trigger_state,
        "decision": trigger_state,
        "product_count": len(trigger_matrix),
        "proceed_product_count": sum(1 for row in trigger_matrix if row["trigger_state"] == "proceed"),
        "defer_product_count": sum(1 for row in trigger_matrix if row["trigger_state"] == "defer"),
        "blocked_product_count": sum(1 for row in trigger_matrix if row["trigger_state"] == "blocked_missing_inputs"),
        "post_run_status": summarize_balfrin_post_run_status(post_run_report),
    }


def determine_balfrin_trigger_state(post_run_report: dict[str, Any] | None) -> str:
    if post_run_report is None:
        return "blocked_missing_inputs"
    interpretation_status = str(post_run_report.get("interpretation_status") or "").strip()
    artifact_acceptance_status = str(post_run_report.get("artifact_acceptance_status") or "").strip()
    if interpretation_status in BALFRIN_BLOCKED_STATUSES or artifact_acceptance_status in BALFRIN_BLOCKED_STATUSES:
        return "blocked_missing_inputs"
    if interpretation_status in BALFRIN_PROCEED_STATUSES and artifact_acceptance_status == "accepted_conditional_diagnostic":
        return "proceed"
    if interpretation_status in BALFRIN_DEFER_STATUSES:
        return "defer"
    return "defer"


def summarize_balfrin_post_run_status(post_run_report: dict[str, Any] | None) -> dict[str, Any]:
    if post_run_report is None:
        return {
            "interpretation_status": "blocked_missing_inputs",
            "artifact_acceptance_status": "blocked_missing_inputs",
            "usable_as_conditional_diagnostic_artifact": False,
        }
    return {
        "interpretation_status": str(post_run_report.get("interpretation_status") or "blocked_missing_inputs"),
        "artifact_acceptance_status": str(post_run_report.get("artifact_acceptance_status") or "blocked_missing_inputs"),
        "usable_as_conditional_diagnostic_artifact": bool(post_run_report.get("usable_as_conditional_diagnostic_artifact")),
    }


def next_trigger_decision(trigger_state: str) -> str:
    if trigger_state == "proceed":
        return "proceed_real_context_staging"
    if trigger_state == "blocked_missing_inputs":
        return "hold_for_balfrin_evidence"
    return "defer_real_context_staging"


def balfrin_trigger_notes(trigger_state: str, product: str) -> list[str]:
    if trigger_state == "proceed":
        return [
            f"Measured Balfrin evidence is sufficient to proceed with {product} staging.",
            "Synthetic fixtures remain non-evidence and do not authorize staging by themselves.",
        ]
    if trigger_state == "blocked_missing_inputs":
        return [
            f"{product} staging remains blocked until a measured Balfrin post-run bundle is supplied.",
            "Missing inputs keep the decision in a hold state rather than a defer/proceed call.",
        ]
    return [
        f"{product} staging stays deferred because the measured Balfrin evidence is still inconclusive.",
        "The existing defer decision remains in force until the Balfrin post-run gate is measured.",
    ]


def build_real_context_product_readiness(
    *,
    acquisition_plan: list[dict[str, Any]],
    cache_contract: dict[str, Any],
    cache_verification_report: dict[str, Any] | None,
    local_core_inputs: list[dict[str, Any]],
    preflight_report: dict[str, Any],
) -> dict[str, Any]:
    cache_verification_rows = cache_verification_rows_by_category(cache_verification_report)
    product_rows: list[dict[str, Any]] = []

    local_core_lookup = {entry["category"]: entry for entry in local_core_inputs}
    acquisition_lookup = {entry["category"]: entry for entry in acquisition_plan}
    public_context_product_requirements = {
        entry["category"]: entry for entry in preflight_report.get("public_context_product_requirements") or []
    }

    for category in (
        "aoi_tile_catalog",
        "terrain_crop",
        "terrain_crs_vertical_datum",
        "source_zone_metadata",
        "scenario_table",
        "source_scenario_policy",
    ):
        row = build_local_product_readiness_row(
            category=category,
            local_core_input=local_core_lookup.get(category),
            expected_path=expected_path_for_local_category(category, local_core_inputs, preflight_report),
            required_fields=list(CORE_PRODUCT_VALIDATION_RULES.get(category, {}).get("required_fields", [])),
        )
        product_rows.append(row)

    for category in [row["category"] for row in BALFRIN_TRIGGER_PRODUCTS]:
        acquisition_row = acquisition_lookup.get(category, {})
        required_fields = list(cache_contract.get("verification_fields") or [])
        product_rows.append(
            build_public_context_product_readiness_row(
                category=category,
                acquisition_row=acquisition_row,
                public_context_requirement=public_context_product_requirements.get(category, {}),
                cache_verification_row=cache_verification_rows.get(category),
                required_fields=required_fields,
            )
        )

    ready_count = sum(1 for row in product_rows if row["classification"] == "ready")
    missing_count = sum(1 for row in product_rows if row["classification"] == "missing")
    deferred_count = sum(1 for row in product_rows if row["classification"] == "deferred")
    metadata_mismatch_count = sum(1 for row in product_rows if row["classification"] == "metadata_mismatch")

    if product_rows and ready_count == len(product_rows):
        readiness_status = "ready"
    elif metadata_mismatch_count:
        readiness_status = "metadata_mismatch"
    elif missing_count:
        readiness_status = "missing"
    elif deferred_count:
        readiness_status = "deferred"
    else:
        readiness_status = "missing"

    return {
        "schema_version": REAL_CONTEXT_PRODUCT_READINESS_SCHEMA_VERSION,
        "readiness_status": readiness_status,
        "product_count": len(product_rows),
        "ready_product_count": ready_count,
        "missing_product_count": missing_count,
        "deferred_product_count": deferred_count,
        "metadata_mismatch_product_count": metadata_mismatch_count,
        "products": product_rows,
    }


def build_local_product_readiness_row(
    *,
    category: str,
    local_core_input: dict[str, Any] | None,
    expected_path: str,
    required_fields: list[str],
) -> dict[str, Any]:
    path = Path(expected_path) if expected_path else Path("")
    if not expected_path or not path.exists():
        return {
            "category": category,
            "product": (local_core_input or {}).get("product", category),
            "classification": "missing",
            "expected_staged_path": expected_path,
            "required_fields": required_fields,
            "missing_fields": required_fields,
            "metadata_mismatches": [],
            "verification_status": "missing",
            "notes": "required local input is absent",
        }

    if category == "terrain_crop":
        is_ready = path.is_file() and path.stat().st_size > 0
        return {
            "category": category,
            "product": (local_core_input or {}).get("product", category),
            "classification": "ready" if is_ready else "metadata_mismatch",
            "expected_staged_path": expected_path,
            "required_fields": required_fields,
            "missing_fields": [] if is_ready else ["non_empty"],
            "metadata_mismatches": [] if is_ready else ["non_empty"],
            "verification_status": "ready" if is_ready else "metadata_mismatch",
            "notes": "terrain crop must exist as a non-empty file",
        }

    if category == "aoi_tile_catalog":
        return validate_aoi_tile_catalog(path, category, local_core_input, required_fields)

    if category == "scenario_table":
        return validate_scenario_table(path, category, local_core_input, required_fields)

    metadata = PREFLIGHT.load_site_config(path)
    if not isinstance(metadata, dict):
        metadata = {}
    missing_fields = missing_metadata_fields(metadata, required_fields)
    classification = "ready" if not missing_fields else "metadata_mismatch"
    return {
        "category": category,
        "product": (local_core_input or {}).get("product", category),
        "classification": classification,
        "expected_staged_path": expected_path,
        "required_fields": required_fields,
        "missing_fields": missing_fields,
        "metadata_mismatches": missing_fields,
        "verification_status": classification,
        "notes": "metadata file must satisfy the required field contract",
    }


def build_public_context_product_readiness_row(
    *,
    category: str,
    acquisition_row: dict[str, Any],
    public_context_requirement: dict[str, Any],
    cache_verification_row: dict[str, Any] | None,
    required_fields: list[str],
) -> dict[str, Any]:
    expected_path = (
        PREFLIGHT.text_value(acquisition_row.get("expected_staged_path"))
        or PREFLIGHT.text_value(public_context_requirement.get("expected_staged_path"))
        or PREFLIGHT.text_value(public_context_requirement.get("path_or_pattern"))
    )
    expected_staging_root = (
        PREFLIGHT.text_value(acquisition_row.get("expected_staging_root"))
        or PREFLIGHT.text_value(public_context_requirement.get("expected_staging_root"))
        or (str(expected_staging_root_for_text(expected_path)) if expected_path else "")
    )

    if cache_verification_row is None:
        return {
            "category": category,
            "product": PREFLIGHT.text_value(acquisition_row.get("product")) or PREFLIGHT.text_value(public_context_requirement.get("product")) or category,
            "classification": "deferred",
            "expected_staged_path": expected_path,
            "expected_staging_root": expected_staging_root,
            "required_fields": required_fields,
            "verification_status": "deferred",
            "missing_paths": [],
            "metadata_mismatches": [],
            "notes": "public-context products remain intentionally deferred until staged and verified",
        }

    verification_status = PREFLIGHT.text_value(cache_verification_row.get("verification_status"))
    classification = "ready" if verification_status == "verified" else "missing" if verification_status == "missing" else "metadata_mismatch"
    return {
        "category": category,
        "product": PREFLIGHT.text_value(acquisition_row.get("product")) or PREFLIGHT.text_value(public_context_requirement.get("product")) or category,
        "classification": classification,
        "expected_staged_path": expected_path,
        "expected_staging_root": expected_staging_root,
        "required_fields": required_fields,
        "verification_status": verification_status or "missing",
        "missing_paths": list(cache_verification_row.get("missing_paths") or []),
        "metadata_mismatches": list(cache_verification_row.get("metadata_mismatches") or []),
        "checksum_match": bool(cache_verification_row.get("checksum_match")),
        "notes": "public-context rows are verified against the staged cache manifest",
    }


def cache_verification_rows_by_category(cache_verification_report: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    if not isinstance(cache_verification_report, dict):
        return rows
    for row in cache_verification_report.get("products") or []:
        if isinstance(row, dict):
            category = PREFLIGHT.text_value(row.get("product_id"))
            if category:
                rows[category] = row
    return rows


def expected_path_for_local_category(
    category: str,
    local_core_inputs: list[dict[str, Any]],
    preflight_report: dict[str, Any],
) -> str:
    for row in local_core_inputs:
        if isinstance(row, dict) and row.get("category") == category:
            return PREFLIGHT.text_value(row.get("expected_path"))
    if category == "aoi_tile_catalog":
        return PREFLIGHT.text_value((preflight_report.get("expected_local_paths") or {}).get("aoi_tile_catalog"))
    if category == "terrain_crop":
        return PREFLIGHT.text_value((preflight_report.get("expected_local_paths") or {}).get("terrain_crop"))
    if category == "terrain_crs_vertical_datum":
        return PREFLIGHT.text_value((preflight_report.get("expected_local_paths") or {}).get("terrain_metadata"))
    return PREFLIGHT.text_value((preflight_report.get("expected_local_paths") or {}).get(category))


def missing_metadata_fields(payload: dict[str, Any], required_fields: list[str]) -> list[str]:
    missing: list[str] = []
    for field in required_fields:
        if not metadata_field_present(payload, field):
            missing.append(field)
    return missing


def metadata_field_present(payload: Any, field: str) -> bool:
    if field == "tiles":
        return bool(isinstance(payload, dict) and isinstance(payload.get("tiles"), list) and payload["tiles"])
    if field.startswith("tiles[*]."):
        if not isinstance(payload, dict):
            return False
        tiles = payload.get("tiles")
        if not isinstance(tiles, list) or not tiles:
            return False
        subfield = field.split(".", 1)[1]
        return all(metadata_field_present(tile, subfield) for tile in tiles if isinstance(tile, dict))
    parts = field.split(".")
    value: Any = payload
    for part in parts:
        if not isinstance(value, dict) or part not in value:
            return False
        value = value[part]
    return value not in (None, "", [])


def validate_aoi_tile_catalog(
    path: Path,
    category: str,
    local_core_input: dict[str, Any] | None,
    required_fields: list[str],
) -> dict[str, Any]:
    catalog = PREFLIGHT.load_site_config(path)
    if not isinstance(catalog, dict):
        catalog = {}
    missing_fields = missing_metadata_fields(catalog, required_fields)
    tile_records = catalog.get("tiles")
    if not isinstance(tile_records, list) or not tile_records:
        missing_fields.append("tiles")
    else:
        for tile_field in ("tile_id", "source_product", "source_url", "extent_lv95_m"):
            if not all(metadata_field_present(tile, tile_field) for tile in tile_records if isinstance(tile, dict)):
                missing_fields.append(f"tiles[*].{tile_field}")
    missing_fields = list(dict.fromkeys(missing_fields))
    classification = "ready" if not missing_fields else "metadata_mismatch"
    return {
        "category": category,
        "product": (local_core_input or {}).get("product", category),
        "classification": classification,
        "expected_staged_path": str(path),
        "required_fields": required_fields,
        "missing_fields": missing_fields,
        "metadata_mismatches": missing_fields,
        "verification_status": classification,
        "notes": "AOI tile catalog must enumerate tile records and discovery metadata",
    }


def validate_scenario_table(
    path: Path,
    category: str,
    local_core_input: dict[str, Any] | None,
    required_fields: list[str],
) -> dict[str, Any]:
    missing_fields: list[str] = []
    try:
        with path.open("r", encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            fieldnames = reader.fieldnames or []
            missing_fields = [field for field in required_fields if field not in fieldnames]
            if not missing_fields and not any(True for _ in reader):
                missing_fields.append("rows")
    except Exception:
        missing_fields = list(required_fields)
    classification = "ready" if not missing_fields else "metadata_mismatch"
    return {
        "category": category,
        "product": (local_core_input or {}).get("product", category),
        "classification": classification,
        "expected_staged_path": str(path),
        "required_fields": required_fields,
        "missing_fields": missing_fields,
        "metadata_mismatches": missing_fields,
        "verification_status": classification,
        "notes": "scenario table must expose the contract columns and at least one scenario row",
    }


def build_local_core_inputs(requirements: list[dict[str, Any]]) -> list[dict[str, Any]]:
    core_inputs: list[dict[str, Any]] = []
    for requirement in requirements:
        if requirement["category"] not in CORE_INPUT_CATEGORIES:
            continue
        core_inputs.append(
            {
                "category": requirement["category"],
                "kind": requirement["kind"],
                "product": requirement["product"],
                "required": requirement["required"],
                "expected_path": requirement["path_or_pattern"],
                "status": requirement["status"],
                "reusable_from_tschamut": requirement["reusable_from_tschamut"],
                "filesystem_state": describe_path_state(Path(requirement["path_or_pattern"])),
                "synthetic_core_input": True,
                "public_context_evidence": False,
            }
        )
    return core_inputs


def build_supporting_roots(requirements: list[dict[str, Any]]) -> list[dict[str, Any]]:
    roots: list[dict[str, Any]] = []
    for requirement in requirements:
        if requirement["category"] not in SUPPORTING_ROOT_CATEGORIES:
            continue
        path = Path(requirement["path_or_pattern"])
        roots.append(
            {
                "category": requirement["category"],
                "product": requirement["product"],
                "required": requirement["required"],
                "expected_path": requirement["path_or_pattern"],
                "status": requirement["status"],
                "filesystem_state": describe_path_state(path),
            }
        )
    return roots


def build_next_acquisition_decisions(
    rows: list[dict[str, Any]],
    balfrin_trigger_summary: dict[str, Any],
) -> list[dict[str, Any]]:
    decisions: list[dict[str, Any]] = []
    trigger_state = balfrin_trigger_summary["trigger_state"]
    next_decision = next_trigger_decision(trigger_state)
    if trigger_state == "proceed":
        reason = "measured Balfrin evidence authorizes public-context staging"
    elif trigger_state == "blocked_missing_inputs":
        reason = "public-context staging is blocked until measured Balfrin evidence is supplied"
    else:
        reason = "public-context staging remains deferred until measured Balfrin evidence is conclusive"
    for row in rows:
        decisions.append(
            {
                "category": row["category"],
                "product": row["product"],
                "decision_type": "deferred_public_context_staging",
                "next_acquisition_decision": next_decision,
                "expected_staged_path": row["expected_staged_path"],
                "expected_staging_root": row["expected_staging_root"],
                "current_status": row["current_status"],
                "balfrin_trigger_state": trigger_state,
                "balfrin_next_decision": next_decision,
                "reason": reason,
                "notes": row["notes"],
            }
        )
    return decisions


def build_real_context_staging_checklist(
    *,
    real_context_product_readiness: dict[str, Any],
    cache_contract: dict[str, Any],
) -> dict[str, Any]:
    verification_fields = list(cache_contract.get("verification_fields") or [])
    verify_commands = cache_contract.get("verify_commands") or []
    verifier_command = ""
    if verify_commands and isinstance(verify_commands[0], dict):
        verifier_command = str(verify_commands[0].get("command") or "")

    rows: list[dict[str, Any]] = []
    verified_count = 0
    missing_count = 0
    deferred_count = 0
    partially_staged_count = 0
    metadata_mismatch_count = 0

    for product in real_context_product_readiness.get("products") or []:
        if not isinstance(product, dict) or product.get("category") not in DEFERRED_PUBLIC_CONTEXT_CATEGORIES:
            continue
        classification = str(product.get("classification") or "missing")
        expected_staged_path = str(product.get("expected_staged_path") or "")
        expected_staging_root = str(product.get("expected_staging_root") or (PREFLIGHT.expected_staging_root_for_text(expected_staged_path) if expected_staged_path else ""))
        verification_status = str(product.get("verification_status") or classification)
        if classification == "ready":
            readiness_impact = "staged files and metadata are ready for deterministic cache verification"
            verified_count += 1
            checklist_state = "verifier_ready"
        elif classification == "deferred":
            readiness_impact = "public-context staging remains intentionally deferred until staged and verified"
            deferred_count += 1
            checklist_state = "deferred"
        elif classification == "missing":
            readiness_impact = "required staged files or metadata are still absent"
            missing_count += 1
            checklist_state = "missing"
        elif classification == "metadata_mismatch":
            readiness_impact = "staged inputs exist but the metadata contract is mismatched"
            metadata_mismatch_count += 1
            checklist_state = "metadata_mismatch"
        else:
            readiness_impact = "staged inputs exist but the cache verifier still fails closed"
            partially_staged_count += 1
            checklist_state = "partially_staged"

        rows.append(
            {
                "schema_version": REAL_CONTEXT_STAGING_CHECKLIST_SCHEMA_VERSION,
                "category": product["category"],
                "product": product["product"],
                "expected_staging_root": expected_staging_root,
                "expected_staged_path": expected_staged_path,
                "cache_manifest_path": str(cache_contract.get("cache_layout", {}).get("cache_manifest_path") or ""),
                "cache_manifest_fields": verification_fields,
                "verifier_command": verifier_command,
                "checklist_state": checklist_state,
                "cache_verification_status": verification_status,
                "classification": classification,
                "required_fields": list(product.get("required_fields") or []),
                "missing_paths": list(product.get("missing_paths") or []),
                "metadata_mismatches": list(product.get("metadata_mismatches") or []),
                "readiness_impact": readiness_impact,
                "claim_boundary_note": CHECKLIST_BOUNDARY_NOTE,
            }
        )

    if verified_count == len(rows) and rows:
        checklist_state = "verifier_ready"
    elif deferred_count == len(rows) and rows:
        checklist_state = "deferred"
    elif missing_count == len(rows) and rows:
        checklist_state = "missing"
    elif metadata_mismatch_count == len(rows) and rows:
        checklist_state = "metadata_mismatch"
    elif partially_staged_count or (rows and verified_count and (missing_count or deferred_count)):
        checklist_state = "partially_staged"
    else:
        checklist_state = "missing"

    return {
        "schema_version": REAL_CONTEXT_STAGING_CHECKLIST_SCHEMA_VERSION,
        "checklist_state": checklist_state,
        "product_count": len(rows),
        "verified_product_count": verified_count,
        "missing_product_count": missing_count,
        "deferred_product_count": deferred_count,
        "partially_staged_product_count": partially_staged_count,
        "metadata_mismatch_product_count": metadata_mismatch_count,
        "cache_manifest_path": str(cache_contract.get("cache_layout", {}).get("cache_manifest_path") or ""),
        "verifier_command": verifier_command,
        "verification_fields": verification_fields,
        "claim_boundary_note": CHECKLIST_BOUNDARY_NOTE,
        "products": rows,
    }


def summarize_local_staging(core_inputs: list[dict[str, Any]], supporting_roots: list[dict[str, Any]]) -> dict[str, Any]:
    ready_core_inputs = [entry["category"] for entry in core_inputs if entry["status"] == "ready"]
    ready_supporting_roots = [entry["category"] for entry in supporting_roots if entry["status"] == "ready"]
    deferred_public_context_products = [
        entry["category"]
        for entry in core_inputs
        if entry["category"] in DEFERRED_PUBLIC_CONTEXT_CATEGORIES and entry["status"] == "deferred_public_context"
    ]
    return {
        "ready_core_input_count": len(ready_core_inputs),
        "ready_core_input_categories": ready_core_inputs,
        "ready_supporting_root_count": len(ready_supporting_roots),
        "ready_supporting_root_categories": ready_supporting_roots,
        "deferred_public_context_core_products": deferred_public_context_products,
        "synthetic_core_inputs_are_public_context_evidence": False,
    }


def build_gate_boundary_summary(
    core_input_status: str,
    deferred_public_context_status: str,
    deferred_public_context_products: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "core_inputs_ready": core_input_status == "ready",
        "deferred_public_context_inputs": deferred_public_context_status == "deferred_public_context_inputs",
        "deferred_public_context_product_count": len(deferred_public_context_products),
        "synthetic_core_inputs_are_public_context_evidence": False,
    }


def determine_gate_status(
    *,
    core_input_status: str,
    deferred_public_context_status: str,
    deferred_public_context_products: list[dict[str, Any]],
    real_context_product_readiness: dict[str, Any],
    prepared_pilot_real_input_readiness: dict[str, Any],
) -> str:
    if core_input_status != "ready":
        return "blocked_missing_inputs"
    if deferred_public_context_status != "deferred_public_context_inputs":
        return "blocked_missing_inputs"
    if not deferred_public_context_products:
        return "blocked_missing_deferred_public_context"
    input_classification = str(prepared_pilot_real_input_readiness.get("input_classification") or "missing")
    if input_classification == "fixture_backed":
        return "blocked_fixture_backed_inputs"
    if input_classification == "partial_real":
        return "blocked_partial_real_inputs"
    if input_classification == "metadata_mismatch":
        return "blocked_metadata_mismatch_inputs"
    if input_classification != "ready_real":
        return "blocked_missing_inputs"
    if (real_context_product_readiness.get("missing_product_count") or 0) > 0:
        return "blocked_missing_inputs"
    if (real_context_product_readiness.get("metadata_mismatch_product_count") or 0) > 0:
        return "blocked_missing_inputs"
    return "ready_for_real_context_acquisition"


def describe_path_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "exists": False,
            "kind": "missing",
            "is_empty_directory": False,
            "is_file": False,
            "is_dir": False,
        }
    if path.is_file():
        return {
            "exists": True,
            "kind": "file",
            "is_empty_directory": False,
            "is_file": True,
            "is_dir": False,
        }
    is_empty_directory = not any(path.iterdir())
    return {
        "exists": True,
        "kind": "empty_directory" if is_empty_directory else "nonempty_directory",
        "is_empty_directory": is_empty_directory,
        "is_file": False,
        "is_dir": True,
    }


def render_text_report(report: dict[str, Any]) -> str:
    lines = [
        f"schema_version: {report['schema_version']}",
        f"real_context_readiness_gate_status: {report['real_context_readiness_gate_status']}",
        f"real_context_staging_checklist_state: {report['real_context_staging_checklist_state']}",
        f"prepared_pilot_input_classification: {report.get('prepared_pilot_input_classification', '')}",
        f"first_missing_real_input_category: {report.get('first_missing_real_input_category', '')}",
        f"first_missing_real_input_classification: {report.get('first_missing_real_input_classification', '')}",
        f"first_missing_real_input_path: {report.get('first_missing_real_input_path', '')}",
        f"first_missing_real_input_missing_fields: {report.get('first_missing_real_input_missing_fields', '')}",
        f"first_fixture_backed_real_input_category: {report.get('first_fixture_backed_real_input_category', '')}",
        f"first_fixture_backed_real_input_classification: {report.get('first_fixture_backed_real_input_classification', '')}",
        f"first_fixture_backed_real_input_path: {report.get('first_fixture_backed_real_input_path', '')}",
        f"core_input_status: {report['core_input_status']}",
        f"deferred_public_context_status: {report['deferred_public_context_status']}",
        f"candidate_site_id: {report['candidate_site_id']}",
        f"candidate_site_name: {report['candidate_site_name']}",
        f"candidate_selection_rationale: {report['candidate_selection_rationale']}",
        f"acquisition_manifest_status: {report['acquisition_manifest_status']}",
        f"acquisition_manifest_path: {report['acquisition_manifest_path']}",
        f"balfrin_evidence_path: {report['balfrin_evidence_path']}",
        "",
        "public_geodata_workflow_contract:",
    ]
    lines.extend(PREFLIGHT._render_public_geodata_workflow_contract(report["public_geodata_workflow_contract"]))
    lines.extend([
        "",
        "site_extent:",
    ])
    site_extent = report["site_extent"]
    if isinstance(site_extent, dict):
        for key in ("crs", "xmin", "ymin", "xmax", "ymax"):
            if key in site_extent:
                lines.append(f"  {key}: {site_extent[key]}")
    else:
        lines.append(f"  {site_extent}")

    lines.append("")
    lines.append("local_core_inputs:")
    lines.extend(render_path_status_rows(report.get("local_core_inputs") or []))

    lines.append("")
    lines.append("supporting_local_roots:")
    lines.extend(render_path_status_rows(report.get("supporting_local_roots") or []))

    lines.append("")
    lines.append("real_context_product_readiness:")
    readiness = report.get("real_context_product_readiness") or {}
    lines.append(f"- schema_version: {readiness.get('schema_version', '')}")
    lines.append(f"- readiness_status: {readiness.get('readiness_status', '')}")
    lines.append(f"- product_count: {readiness.get('product_count', '')}")
    lines.append(f"- ready_product_count: {readiness.get('ready_product_count', '')}")
    lines.append(f"- missing_product_count: {readiness.get('missing_product_count', '')}")
    lines.append(f"- deferred_product_count: {readiness.get('deferred_product_count', '')}")
    lines.append(f"- metadata_mismatch_product_count: {readiness.get('metadata_mismatch_product_count', '')}")
    lines.append("- products:")
    lines.extend(render_product_readiness_rows(readiness.get("products") or []))

    lines.append("")
    lines.append("deterministic_acquisition_plan:")
    lines.extend(render_plan_rows(report.get("deterministic_acquisition_plan") or []))

    lines.append("")
    lines.append("next_acquisition_decisions:")
    lines.extend(render_decision_rows(report.get("next_acquisition_decisions") or []))

    lines.append("")
    lines.append("real_context_staging_checklist:")
    checklist = report.get("real_context_staging_checklist") or {}
    lines.append(f"- schema_version: {checklist.get('schema_version', '')}")
    lines.append(f"- checklist_state: {checklist.get('checklist_state', '')}")
    lines.append(f"- claim_boundary_note: {checklist.get('claim_boundary_note', '')}")
    lines.append(f"- cache_manifest_path: {checklist.get('cache_manifest_path', '')}")
    lines.append(f"- verifier_command: {checklist.get('verifier_command', '')}")
    lines.append("- verification_fields:")
    lines.extend(f"  - {field}" for field in checklist.get("verification_fields") or [])
    lines.append("- products:")
    lines.extend(render_checklist_rows((report.get("real_context_staging_checklist") or {}).get("products") or []))

    lines.append("")
    lines.append("prepared_pilot_real_input_readiness:")
    prepared_pilot_real_input_readiness = report.get("prepared_pilot_real_input_readiness") or {}
    lines.append(f"- schema_version: {prepared_pilot_real_input_readiness.get('schema_version', '')}")
    lines.append(f"- input_classification: {prepared_pilot_real_input_readiness.get('input_classification', '')}")
    lines.append(
        f"- first_missing_real_input_category: {prepared_pilot_real_input_readiness.get('first_missing_real_input_category', '')}"
    )
    lines.append(
        f"- first_missing_real_input_classification: {prepared_pilot_real_input_readiness.get('first_missing_real_input_classification', '')}"
    )
    lines.append(f"- first_missing_real_input_path: {prepared_pilot_real_input_readiness.get('first_missing_real_input_path', '')}")
    lines.append(
        f"- first_missing_real_input_missing_fields: {prepared_pilot_real_input_readiness.get('first_missing_real_input_missing_fields', [])}"
    )
    lines.append(
        f"- first_fixture_backed_real_input_category: {prepared_pilot_real_input_readiness.get('first_fixture_backed_real_input_category', '')}"
    )
    lines.append(
        f"- first_fixture_backed_real_input_classification: {prepared_pilot_real_input_readiness.get('first_fixture_backed_real_input_classification', '')}"
    )
    lines.append(
        f"- first_fixture_backed_real_input_path: {prepared_pilot_real_input_readiness.get('first_fixture_backed_real_input_path', '')}"
    )
    lines.append(f"- required_real_input_count: {prepared_pilot_real_input_readiness.get('required_real_input_count', '')}")
    lines.append(f"- real_staged_real_input_count: {prepared_pilot_real_input_readiness.get('real_staged_real_input_count', '')}")
    lines.append(f"- fixture_backed_real_input_count: {prepared_pilot_real_input_readiness.get('fixture_backed_real_input_count', '')}")
    lines.append(f"- metadata_mismatch_real_input_count: {prepared_pilot_real_input_readiness.get('metadata_mismatch_real_input_count', '')}")
    lines.append(f"- missing_real_input_count: {prepared_pilot_real_input_readiness.get('missing_real_input_count', '')}")
    lines.append(f"- missing_row_count: {prepared_pilot_real_input_readiness.get('missing_row_count', '')}")
    lines.append(f"- missing_file_count: {prepared_pilot_real_input_readiness.get('missing_file_count', '')}")
    lines.append(
        f"- first_missing_non_synthetic_input: {prepared_pilot_real_input_readiness.get('first_missing_non_synthetic_input', {})}"
    )

    lines.append("")
    lines.append("real_input_acquisition_handoff:")
    handoff = report.get("real_input_acquisition_handoff") or {}
    lines.append(f"- schema_version: {handoff.get('schema_version', '')}")
    lines.append(f"- next_action_recommendation: {handoff.get('next_action_recommendation', '')}")
    lines.append(f"- authorization_or_defer_status: {handoff.get('authorization_or_defer_status', '')}")
    lines.append(f"- first_missing_real_input_category: {handoff.get('first_missing_real_input_category', '')}")
    lines.append(f"- first_missing_real_input_classification: {handoff.get('first_missing_real_input_classification', '')}")
    lines.append(f"- expected_source_product: {handoff.get('expected_source_product', '')}")
    lines.append(f"- expected_local_path: {handoff.get('expected_local_path', '')}")
    lines.append(f"- metadata_contract: {handoff.get('metadata_contract', [])}")
    lines.append(f"- missing_metadata_fields: {handoff.get('missing_metadata_fields', [])}")
    lines.append(f"- authorization_required: {handoff.get('authorization_required', '')}")
    lines.append(f"- reason: {handoff.get('reason', '')}")
    lines.append(f"- stop_condition: {handoff.get('stop_condition', '')}")

    lines.append("")
    lines.append("balfrin_trigger_summary:")
    for key, value in (report.get("balfrin_trigger_summary") or {}).items():
        lines.append(f"- {key}: {value}")

    lines.append("")
    lines.append("balfrin_trigger_matrix:")
    lines.extend(render_balfrin_trigger_rows(report.get("balfrin_trigger_matrix") or []))

    lines.append("")
    lines.append("deferred_public_context_products:")
    lines.extend(render_plan_rows(report.get("deferred_public_context_products") or []))

    lines.append("")
    lines.append("local_staged_summary:")
    for key, value in (report.get("local_staged_summary") or {}).items():
        lines.append(f"- {key}: {value}")

    lines.append("")
    lines.append("gate_boundary_summary:")
    for key, value in (report.get("gate_boundary_summary") or {}).items():
        lines.append(f"- {key}: {value}")

    lines.append("")
    lines.append("synthetic_core_inputs_are_public_context_evidence: false")
    return "\n".join(lines)


def render_path_status_rows(rows: list[dict[str, Any]]) -> list[str]:
    rendered: list[str] = []
    for row in rows:
        rendered.append(
            f"- {row['category']}: status={row['status']}, expected_path={row['expected_path']}, "
            f"filesystem_state={row['filesystem_state']['kind']}"
        )
    if not rendered:
        rendered.append("- []")
    return rendered


def render_product_readiness_rows(rows: list[dict[str, Any]]) -> list[str]:
    rendered: list[str] = []
    for row in rows:
        rendered.append(
            f"- {row.get('category', '')}: classification={row.get('classification', '')}, "
            f"expected_staged_path={row.get('expected_staged_path', '')}, "
            f"required_fields={', '.join(row.get('required_fields') or []) or 'none'}, "
            f"missing_fields={', '.join(row.get('missing_fields') or []) or 'none'}, "
            f"metadata_mismatches={', '.join(row.get('metadata_mismatches') or []) or 'none'}"
        )
    if not rendered:
        rendered.append("- []")
    return rendered


def render_plan_rows(rows: list[dict[str, Any]]) -> list[str]:
    rendered: list[str] = []
    for row in rows:
        rendered.append(
            f"- {row['category']}: product={row['product']}, current_status={row['current_status']}, "
            f"expected_staged_path={row['expected_staged_path']}"
        )
    if not rendered:
        rendered.append("- []")
    return rendered


def render_decision_rows(rows: list[dict[str, Any]]) -> list[str]:
    rendered: list[str] = []
    for row in rows:
        rendered.append(
            f"- {row['category']}: decision_type={row['decision_type']}, "
            f"next_acquisition_decision={row['next_acquisition_decision']}, "
            f"expected_staged_path={row['expected_staged_path']}, "
            f"balfrin_trigger_state={row.get('balfrin_trigger_state', 'unknown')}, "
            f"balfrin_next_decision={row.get('balfrin_next_decision', 'unknown')}"
        )
    if not rendered:
        rendered.append("- []")
    return rendered


def render_checklist_rows(rows: list[dict[str, Any]]) -> list[str]:
    rendered: list[str] = []
    for row in rows:
        rendered.append(
            f"- {row['category']}: checklist_state={row['checklist_state']}, "
            f"expected_staging_root={row['expected_staging_root']}, "
            f"verifier_command={row['verifier_command'] or 'missing'}, "
            f"cache_manifest_fields={', '.join(row['cache_manifest_fields']) if row.get('cache_manifest_fields') else 'none'}, "
            f"readiness_impact={row['readiness_impact']}"
        )
    if not rendered:
        rendered.append("- []")
    return rendered


def render_balfrin_trigger_rows(rows: list[dict[str, Any]]) -> list[str]:
    rendered: list[str] = []
    for row in rows:
        rendered.append(
            f"- {row['category']}: product={row['product']}, trigger_state={row['trigger_state']}, "
            f"next_acquisition_decision={row['next_acquisition_decision']}"
        )
    if not rendered:
        rendered.append("- []")
    return rendered


if __name__ == "__main__":
    raise SystemExit(main())
