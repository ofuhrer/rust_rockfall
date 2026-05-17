#!/usr/bin/env python3
"""Generate deterministic target-area scenario tables for the frozen Balfrin demo.

This helper stays at the dry-run boundary. It reads the frozen Tschamut
target-area contract together with the committed source-zone metadata, release
points, and conditional source-scenario policy, then reproduces the committed
deterministic scenario table plus a provenance manifest.

It does not fit a population model, change probability semantics, run any
hazard build, or authorize operational claim language.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except ImportError as exc:  # pragma: no cover - environment setup.
    raise SystemExit("PyYAML is required. Run this script with `PYENV_VERSION=system uv run python ...`; CI may use `requirements-tools.txt`") from exc


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "balfrin_target_area_scenario_tables_v1"
DEFAULT_CONTRACT = ROOT / "validation/pilot_runs/tschamut_public_balfrin_target_area_demo_v1.yaml"
DEFAULT_POLICY = ROOT / "validation/policies/tschamut_public_source_scenario_policy_v1.yaml"
DEFAULT_SOURCE_ZONE_METADATA = ROOT / "data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_source_zone_metadata_v1.yaml"
DEFAULT_RELEASE_POINTS = ROOT / "data/processed/swisstopo/tschamut_public_pilot/input/release_points_lv95.csv"
DEFAULT_REFERENCE_SCENARIO_TABLE = ROOT / "data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_scenario_table_v1.csv"
DEFAULT_OUTPUT_ROOT = ROOT / "validation/private/tschamut_public_pilot/balfrin_target_area_demo_v1"
SCENARIO_TABLE_FILENAME = "tschamut_public_balfrin_target_area_demo_scenario_table.csv"
SCENARIO_MANIFEST_FILENAME = "tschamut_public_balfrin_target_area_demo_scenario_manifest.json"


def _load_generic_generator():
    path = ROOT / "scripts" / "generate_tschamut_block_scenario_tables.py"
    spec = importlib.util.spec_from_file_location("generate_tschamut_block_scenario_tables_for_balfrin_target_area", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load generic scenario-table helper from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


GENERATOR = _load_generic_generator()


class TargetAreaScenarioTableError(ValueError):
    """User-facing target-area generation error."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--source-scenario-policy", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("--source-zone-metadata", type=Path, default=DEFAULT_SOURCE_ZONE_METADATA)
    parser.add_argument("--release-points", type=Path, default=DEFAULT_RELEASE_POINTS)
    parser.add_argument("--reference-scenario-table", type=Path, default=DEFAULT_REFERENCE_SCENARIO_TABLE)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    args = parser.parse_args(argv)

    try:
        report = build_report(
            contract_path=args.contract,
            source_scenario_policy_path=args.source_scenario_policy,
            source_zone_metadata_path=args.source_zone_metadata,
            release_points_path=args.release_points,
            reference_scenario_table_path=args.reference_scenario_table,
            output_root=args.output_root,
        )
    except TargetAreaScenarioTableError as exc:
        print(f"balfrin target-area scenario-table error: {exc}", file=sys.stderr)
        return 2

    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if report["scenario_table_status"] == "ready":
        write_outputs(report)

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text_report(report))
    return 0 if report["scenario_table_status"] == "ready" else 2


def build_report(
    *,
    contract_path: Path = DEFAULT_CONTRACT,
    source_scenario_policy_path: Path = DEFAULT_POLICY,
    source_zone_metadata_path: Path = DEFAULT_SOURCE_ZONE_METADATA,
    release_points_path: Path = DEFAULT_RELEASE_POINTS,
    reference_scenario_table_path: Path = DEFAULT_REFERENCE_SCENARIO_TABLE,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
) -> dict[str, Any]:
    required_inputs = [
        contract_path,
        source_scenario_policy_path,
        source_zone_metadata_path,
        release_points_path,
        reference_scenario_table_path,
    ]
    missing_inputs = [display_path(path) for path in required_inputs if not path.exists()]
    if missing_inputs:
        return blocked_report(
            missing_inputs,
            contract_path=contract_path,
            source_scenario_policy_path=source_scenario_policy_path,
            source_zone_metadata_path=source_zone_metadata_path,
            release_points_path=release_points_path,
            reference_scenario_table_path=reference_scenario_table_path,
            output_root=output_root,
            blocked_reason="required frozen target-area inputs are missing",
        )

    contract = load_yaml(contract_path)
    target_area = require_mapping(contract.get("target_area"), "target_area")
    input_freeze = require_mapping(contract.get("input_freeze"), "input_freeze")
    claim_boundary = require_mapping(contract.get("claim_boundary"), "claim_boundary")

    frozen_source_zone_metadata_path = resolve_repo_path(input_freeze.get("source_zone_metadata_path"))
    frozen_release_points_path = resolve_repo_path(input_freeze.get("release_points_csv"))
    frozen_reference_table_path = resolve_repo_path(input_freeze.get("scenario_table_path"))
    frozen_policy_path = resolve_repo_path(input_freeze.get("source_scenario_policy_path"))

    for path, expected in (
        (frozen_policy_path, source_scenario_policy_path),
        (frozen_source_zone_metadata_path, source_zone_metadata_path),
        (frozen_release_points_path, release_points_path),
        (frozen_reference_table_path, reference_scenario_table_path),
    ):
        if path.resolve() != expected.resolve():
            raise TargetAreaScenarioTableError(
                f"contract path mismatch for {display_path(expected)}; frozen contract points at {display_path(path)}"
            )

    scenario_family_basis = text_value(input_freeze.get("scenario_family_basis"), "input_freeze.scenario_family_basis")
    scenario_probability_semantics = text_value(
        input_freeze.get("scenario_probability_semantics"), "input_freeze.scenario_probability_semantics"
    )
    if scenario_family_basis and scenario_family_basis != "conditional_sampling_only":
        raise TargetAreaScenarioTableError(
            f"scenario family basis must remain conditional_sampling_only, got {scenario_family_basis!r}"
        )
    if scenario_probability_semantics and scenario_probability_semantics != "normalized within a block family; no annual frequency claim":
        raise TargetAreaScenarioTableError(
            "scenario probability semantics must remain normalized within a block family; no annual frequency claim"
        )

    generic_report = GENERATOR.build_report(
        policy_path=source_scenario_policy_path,
        source_zone_metadata_path=source_zone_metadata_path,
        release_points_path=release_points_path,
        reference_scenario_table_path=reference_scenario_table_path,
        template_id="observed_rows_summary_v1",
    )
    if generic_report["scenario_table_status"] != "ready":
        return blocked_report(
            [],
            contract_path=contract_path,
            source_scenario_policy_path=source_scenario_policy_path,
            source_zone_metadata_path=source_zone_metadata_path,
            release_points_path=release_points_path,
            reference_scenario_table_path=reference_scenario_table_path,
            output_root=output_root,
            blocked_reason=generic_report.get("blocked_reason") or "generic scenario-table generation is blocked",
            generic_report=generic_report,
        )

    source_zone_metadata = load_yaml(source_zone_metadata_path)
    scenario_rows = generic_report["generated_scenario_table_rows"]
    scenario_manifest = generic_report["scenario_table_manifest"]
    target_area_id = text_value(target_area.get("target_area_id"), "target_area.target_area_id")
    target_area_name = text_value(target_area.get("target_area_name"), "target_area.target_area_name")
    run_id = text_value(contract.get("run_id"), "run_id")

    output_root = resolve_output_root(output_root)
    scenario_table_output_path = output_root / SCENARIO_TABLE_FILENAME
    scenario_manifest_output_path = output_root / SCENARIO_MANIFEST_FILENAME

    report = {
        "schema_version": SCHEMA_VERSION,
        "scenario_table_status": "ready",
        "blocked_reason": None,
        "read_only": True,
        "scale_up_authorized": False,
        "operational_claims_allowed": False,
        "contract_status": text_value(contract.get("contract_status"), "contract_status"),
        "target_area_id": target_area_id,
        "target_area_name": target_area_name,
        "run_id": run_id,
        "target_area": {
            "target_area_id": target_area_id,
            "target_area_name": target_area_name,
            "target_area_label": text_value(target_area.get("target_area_label"), "target_area.target_area_label"),
            "site_extent": target_area.get("site_extent", {}),
        },
        "input_freeze": {
            "source_zone_metadata_path": display_path(frozen_source_zone_metadata_path),
            "release_points_csv": display_path(frozen_release_points_path),
            "scenario_table_path": display_path(frozen_reference_table_path),
            "source_scenario_policy_path": display_path(frozen_policy_path),
            "scenario_family_basis": scenario_family_basis,
            "scenario_probability_semantics": scenario_probability_semantics,
        },
        "source_inputs": {
            "contract_path": display_path(contract_path),
            "source_scenario_policy_path": display_path(source_scenario_policy_path),
            "source_zone_metadata_path": display_path(source_zone_metadata_path),
            "release_points_path": display_path(release_points_path),
            "reference_scenario_table_path": display_path(reference_scenario_table_path),
        },
        "deterministic_generation_evidence": {
            "source_zone_id": text_value(source_zone_metadata.get("source_zone_id"), "source_zone_metadata.source_zone_id"),
            "release_sampling_seed": source_zone_metadata.get("release_sampling_policy", {}).get("seed"),
            "scenario_id": scenario_rows[0]["scenario_id"] if scenario_rows else None,
            "row_count": len(scenario_rows),
            "conditional_weighting_semantics": scenario_manifest.get("conditional_weighting_semantics", {}),
            "source_zone_provenance": scenario_manifest.get("source_zone_provenance", {}),
            "release_metadata_provenance": scenario_manifest.get("release_metadata_provenance", {}),
        },
        "generated_scenario_table_rows": scenario_rows,
        "scenario_table_manifest": {
            **scenario_manifest,
            "target_area": {
                "target_area_id": target_area_id,
                "target_area_name": target_area_name,
                "contract_path": display_path(contract_path),
            },
        },
        "output_paths": {
            "scenario_table_csv": display_path(scenario_table_output_path),
            "scenario_manifest_json": display_path(scenario_manifest_output_path),
        },
        "claim_boundary": claim_boundary,
    }
    return report


def blocked_report(
    missing_inputs: list[str],
    *,
    contract_path: Path,
    source_scenario_policy_path: Path,
    source_zone_metadata_path: Path,
    release_points_path: Path,
    reference_scenario_table_path: Path,
    output_root: Path,
    blocked_reason: str,
    generic_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    output_root = resolve_output_root(output_root)
    scenario_table_output_path = output_root / SCENARIO_TABLE_FILENAME
    scenario_manifest_output_path = output_root / SCENARIO_MANIFEST_FILENAME
    return {
        "schema_version": SCHEMA_VERSION,
        "scenario_table_status": "blocked_missing_inputs" if missing_inputs else "blocked_contract_mismatch",
        "blocked_reason": blocked_reason,
        "read_only": True,
        "scale_up_authorized": False,
        "operational_claims_allowed": False,
        "contract_path": display_path(contract_path),
        "source_inputs": {
            "contract_path": display_path(contract_path),
            "source_scenario_policy_path": display_path(source_scenario_policy_path),
            "source_zone_metadata_path": display_path(source_zone_metadata_path),
            "release_points_path": display_path(release_points_path),
            "reference_scenario_table_path": display_path(reference_scenario_table_path),
        },
        "generated_scenario_table_rows": [],
        "scenario_table_manifest": {
            "schema_version": f"{SCHEMA_VERSION}_manifest_v1",
            "table_status": "blocked_missing_inputs" if missing_inputs else "blocked_contract_mismatch",
            "blocked_reason": blocked_reason,
            "missing_inputs": sorted(set(missing_inputs)),
            "read_only": True,
            "operational_claims_allowed": False,
            "scale_up_authorized": False,
            "scenario_table_csv": display_path(scenario_table_output_path),
            "scenario_manifest_json": display_path(scenario_manifest_output_path),
            "generic_report": generic_report or {},
        },
        "deterministic_generation_evidence": {
            "scenario_id": None,
            "release_sampling_seed": None,
            "conditional_weighting_semantics": {},
            "source_zone_provenance": {},
            "release_metadata_provenance": {},
        },
        "output_paths": {
            "scenario_table_csv": display_path(scenario_table_output_path),
            "scenario_manifest_json": display_path(scenario_manifest_output_path),
        },
    }


def write_outputs(report: dict[str, Any]) -> None:
    output_paths = report.get("output_paths", {})
    csv_path = repo_path(output_paths.get("scenario_table_csv"))
    manifest_path = repo_path(output_paths.get("scenario_manifest_json"))
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    GENERATOR.write_csv(csv_path, report["generated_scenario_table_rows"])
    manifest_path.write_text(
        json.dumps(report["scenario_table_manifest"], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def render_text_report(report: dict[str, Any]) -> str:
    lines = [
        f"schema_version: {report.get('schema_version', '')}",
        f"scenario_table_status: {report.get('scenario_table_status', '')}",
        f"target_area_id: {report.get('target_area_id', '')}",
        f"target_area_name: {report.get('target_area_name', '')}",
        f"run_id: {report.get('run_id', '')}",
        "deterministic_generation_evidence:",
    ]
    evidence = report.get("deterministic_generation_evidence", {}) or {}
    for key in (
        "source_zone_id",
        "release_sampling_seed",
        "scenario_id",
        "row_count",
    ):
        lines.append(f"- {key}: {evidence.get(key, '')}")
    lines.append("scenario_table_manifest:")
    manifest = report.get("scenario_table_manifest", {}) or {}
    for key in (
        "schema_version",
        "scenario_family_id",
        "row_count",
        "row_ids",
        "block_scenario_ids",
        "conditional_weighting_semantics",
    ):
        lines.append(f"- {key}: {manifest.get(key, '')}")
    lines.append("output_paths:")
    for key, value in (report.get("output_paths") or {}).items():
        lines.append(f"- {key}: {value}")
    return "\n".join(lines)


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def require_mapping(value: Any, context: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TargetAreaScenarioTableError(f"{context} must be a YAML mapping")
    return value


def resolve_output_root(output_root: Path) -> Path:
    return output_root if output_root.is_absolute() else (ROOT / output_root)


def resolve_repo_path(value: Any) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise TargetAreaScenarioTableError("missing required repository path value")
    path = Path(value)
    return path if path.is_absolute() else (ROOT / path)


def repo_path(value: Any) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise TargetAreaScenarioTableError("missing output path value")
    path = Path(value)
    return path if path.is_absolute() else (ROOT / path)


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def text_value(value: Any, context: str | None = None) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if context is not None:
        return str(value)
    return str(value)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
