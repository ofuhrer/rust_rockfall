#!/usr/bin/env python3
"""Plan a deterministic release-plan dry run from a small AOI/site config.

This helper stays at the dry-run boundary. It does not create a production
release plan, tune parameters, run ensembles, or authorize a second-site
execution template. Instead, it turns the candidate source-zone metadata and
scenario rows into deterministic release and block-scenario rows while keeping
the Tschamut-only seed and block-class heuristics explicit.
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import shlex
import sys
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except ImportError as exc:  # pragma: no cover - environment setup.
    raise SystemExit("PyYAML is required; install with `python3 -m pip install PyYAML`") from exc


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "release_plan_dry_run_v1"
DEFAULT_SITE_CONFIG = ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml"
TSCHAMUT_POLICY = ROOT / "validation/policies/tschamut_public_source_scenario_policy_v1.yaml"


def _load_preflight_module():
    path = ROOT / "scripts" / "check_second_site_public_geodata_preflight.py"
    spec = importlib.util.spec_from_file_location("release_plan_dry_run_preflight", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load preflight helper from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


PREFLIGHT = _load_preflight_module()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site-config", type=Path, default=DEFAULT_SITE_CONFIG)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    args = parser.parse_args(argv)

    report = build_report(args.site_config, repo_root=args.repo_root)

    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    output = json.dumps(report, indent=2, sort_keys=True) if args.format == "json" else render_text_report(report)
    print(output)
    return 0 if report["release_plan_dry_run_status"] == "ready" else 2


def build_report(site_config: Path, repo_root: Path | None = None) -> dict[str, Any]:
    if not site_config.exists():
        raise SystemExit(f"missing site config: {site_config}")

    original_root = PREFLIGHT.ROOT
    repo_root = repo_root or ROOT
    try:
        PREFLIGHT.ROOT = repo_root
        preflight_report = PREFLIGHT.build_report(site_config)
        paths = PREFLIGHT.build_paths(preflight_report["candidate_site_id"], PREFLIGHT.load_site_config(site_config))
    finally:
        PREFLIGHT.ROOT = original_root

    source_zone_record = load_yaml(paths["source_zone_metadata"])
    scenario_rows = load_csv(paths["scenario_table"])
    tschamut_policy = load_yaml(TSCHAMUT_POLICY)

    report = {
        "schema_version": SCHEMA_VERSION,
        "release_plan_dry_run_status": release_plan_status(preflight_report),
        "candidate_site_id": preflight_report["candidate_site_id"],
        "candidate_site_name": preflight_report["candidate_site_name"],
        "candidate_selection_rationale": preflight_report["candidate_selection_rationale"],
        "site_extent": preflight_report["site_extent_or_placeholder"],
        "release_plan_summary": {
            "release_point_count": len(source_zone_record.get("release_points") or []),
            "release_row_count": len(source_zone_record.get("release_points") or []),
            "block_scenario_row_count": len(scenario_rows),
            "reference_block_scenario_class_count": len((tschamut_policy.get("block_scenario_policy", {}) or {}).get("scenarios") or []),
            "release_sampling_seed_policy": {
                "mode": text_value((tschamut_policy.get("source_zone_policy", {}) or {}).get("release_sampling", {}).get("mode")),
                "seed_policy": text_value((tschamut_policy.get("source_zone_policy", {}) or {}).get("release_sampling", {}).get("seed_policy")),
                "seed": (tschamut_policy.get("source_zone_policy", {}) or {}).get("release_sampling", {}).get("seed"),
                "release_cell_id_prefix": text_value((tschamut_policy.get("source_zone_policy", {}) or {}).get("release_sampling", {}).get("release_cell_id_prefix")),
                "requested_release_cell_count": (tschamut_policy.get("source_zone_policy", {}) or {}).get("release_sampling", {}).get("requested_release_cell_count"),
            },
        },
        "reusable_semantics": build_reusable_semantics(preflight_report),
        "site_specific_inputs": build_site_specific_inputs(preflight_report, source_zone_record, scenario_rows, paths),
        "tschamut_only_heuristics": build_tschamut_only_heuristics(tschamut_policy),
        "deterministic_release_rows": build_release_rows(source_zone_record),
        "deterministic_block_scenario_rows": build_block_scenario_rows(scenario_rows),
        "machine_readable_distinction": {
            "reusable_semantics": [
                "release_point_table_shape",
                "block_scenario_table_shape",
                "sampling_weight_semantics",
                "scenario_probability_semantics",
                "coordinate_reference_system",
                "vertical_datum",
            ],
            "site_specific_inputs": [
                "source_zone_record",
                "scenario_table_rows",
                "expected_paths",
            ],
            "tschamut_only_heuristics": [
                "release_sampling_seed_policy",
                "reference_block_scenario_classes",
                "release_cell_id_prefix",
                "requested_release_cell_count",
            ],
        },
        "claim_boundaries": preflight_report["claim_boundaries"],
        "scale_up_authorized": False,
        "operational_claims_allowed": False,
        "blocked_second_site_execution_template": {
            "status": "template_only",
            "command_id": "second_site_release_plan_execution_template",
            "command": command_string(
                [
                    "PYENV_VERSION=system",
                    "uv",
                    "run",
                    "python",
                    "scripts/generate_second_site_release_plan.py",
                    "--site-config",
                    str(site_config),
                    "--output-root",
                    "validation/private/<site_id>",
                    "--format",
                    "json",
                ]
            ),
            "blocked_reason": preflight_report["blocked_reason"],
            "expected_outputs": [
                "validation/private/<site_id>/release_plan_case.yaml",
                "validation/private/<site_id>/release_plan_manifest.json",
            ],
        },
        "blocked_reason": preflight_report["blocked_reason"],
    }
    return report


def release_plan_status(preflight_report: dict[str, Any]) -> str:
    if preflight_report["core_input_status"] != "ready":
        return "blocked_missing_inputs"
    if preflight_report["public_context_boundary_status"] != "ready":
        return "deferred_public_context_inputs"
    return "ready"


def build_reusable_semantics(preflight_report: dict[str, Any]) -> dict[str, Any]:
    source_zone_contract = preflight_report.get("source_zone_scenario_contract", {})
    return {
        "release_point_table_shape": source_zone_contract.get("release_point_table") or "one row per release point",
        "block_scenario_table_shape": source_zone_contract.get("block_scenario_table") or "CSV table with one row per block / scenario record",
        "sampling_weight_semantics": source_zone_contract.get("scenario_probability_semantics")
        or "normalized within a block family; no annual frequency claim",
        "scenario_probability_semantics": source_zone_contract.get("scenario_probability_semantics")
        or "normalized within a block family; no annual frequency claim",
        "coordinate_reference_system": {
            "crs": text_value(preflight_report.get("site_extent_or_placeholder", {}).get("crs"))
            if isinstance(preflight_report.get("site_extent_or_placeholder"), dict)
            else "EPSG:2056",
            "vertical_datum": "LN02",
        },
        "source_zone_geometry": source_zone_contract.get("source_zone_geometry") or "LV95 polygon",
    }


def build_site_specific_inputs(
    preflight_report: dict[str, Any],
    source_zone_record: dict[str, Any],
    scenario_rows: list[dict[str, str]],
    paths: dict[str, Path],
) -> dict[str, Any]:
    return {
        "source_zone_record": {
            "zone_id": text_value(source_zone_record.get("zone_id")),
            "title": text_value(source_zone_record.get("title")),
            "source_dataset": text_value(source_zone_record.get("source_dataset")),
            "source_url": source_zone_record.get("source_url"),
            "license": text_value(source_zone_record.get("license")),
            "coordinate_reference_system": source_zone_record.get("coordinate_reference_system", {}),
            "geometry": source_zone_record.get("geometry", {}),
            "release_points": source_zone_record.get("release_points") or [],
            "provenance": source_zone_record.get("provenance", {}),
        },
        "scenario_table_rows": scenario_rows,
        "expected_paths": {
            "source_zone_metadata": str(paths["source_zone_metadata"]),
            "scenario_table": str(paths["scenario_table"]),
            "source_scenario_policy": str(paths["source_scenario_policy"]),
        },
        "candidate_source_zone_record_fields": [
            "zone_id",
            "title",
            "source_dataset",
            "source_url",
            "license",
            "coordinate_reference_system",
            "geometry",
            "release_points",
            "provenance",
        ],
        "site_extent": preflight_report["site_extent_or_placeholder"],
    }


def build_tschamut_only_heuristics(tschamut_policy: dict[str, Any]) -> dict[str, Any]:
    source_zone_policy = tschamut_policy.get("source_zone_policy", {}) if isinstance(tschamut_policy.get("source_zone_policy"), dict) else {}
    release_sampling = source_zone_policy.get("release_sampling", {}) if isinstance(source_zone_policy.get("release_sampling"), dict) else {}
    block_scenarios = tschamut_policy.get("block_scenario_policy", {}) if isinstance(tschamut_policy.get("block_scenario_policy"), dict) else {}
    scenarios = block_scenarios.get("scenarios", []) if isinstance(block_scenarios.get("scenarios"), list) else []
    return {
        "release_sampling_seed_policy": {
            "mode": text_value(release_sampling.get("mode")) or "deterministic_grid",
            "seed_policy": text_value(release_sampling.get("seed_policy")) or "fixed_integer_recorded_before_simulation",
            "seed": release_sampling.get("seed"),
            "release_cell_id_policy": text_value(release_sampling.get("release_cell_id_policy")) or "stable_source_zone_prefixed_ids",
            "release_cell_id_prefix": text_value(release_sampling.get("release_cell_id_prefix")) or "tschamut_public_release_cell",
            "requested_release_cell_count": release_sampling.get("requested_release_cell_count"),
            "sampling_weight_semantics": text_value(release_sampling.get("sampling_weight_semantics")) or "conditional_sampling_only",
        },
        "reference_block_scenario_classes": [
            {
                "block_scenario_id": text_value(scenario.get("block_scenario_id")),
                "block_size_class": text_value(scenario.get("block_size_class")),
                "block_shape_class": text_value(scenario.get("block_shape_class")),
                "block_radius_m": scenario.get("block_radius_m"),
                "block_mass_kg": scenario.get("block_mass_kg"),
                "sampling_weight": scenario.get("sampling_weight"),
                "derivation_basis": text_value(scenario.get("derivation_basis")),
            }
            for scenario in scenarios
        ],
        "reference_source_zone_id": text_value(source_zone_policy.get("source_zone_id")),
    }


def build_release_rows(source_zone_record: dict[str, Any]) -> list[dict[str, Any]]:
    release_points = source_zone_record.get("release_points") or []
    rows: list[dict[str, Any]] = []
    source_zone_id = text_value(source_zone_record.get("zone_id"))
    for index, release_point in enumerate(release_points, start=1):
        if not isinstance(release_point, dict):
            continue
        release_point_id = text_value(release_point.get("release_point_id")) or f"{source_zone_id}_release_point_{index:03d}"
        rows.append(
            {
                "release_row_id": f"{source_zone_id}_release_row_{index:03d}",
                "release_point_id": release_point_id,
                "source_zone_id": source_zone_id,
                "release_order": index,
                "x": release_point.get("x"),
                "y": release_point.get("y"),
                "z_offset_m": release_point.get("z_offset_m"),
                "notes": text_value(release_point.get("notes")),
            }
        )
    return rows


def build_block_scenario_rows(scenario_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(scenario_rows, start=1):
        rows.append(
            {
                "block_scenario_row_id": f"block_scenario_row_{index:03d}",
                "scenario_id": row.get("scenario_id"),
                "source_zone_id": row.get("source_zone_id"),
                "block_family": row.get("block_family"),
                "relative_weight": row.get("relative_weight"),
                "probability_semantics": row.get("probability_semantics"),
                "release_point_id": row.get("release_point_id"),
            }
        )
    return rows


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def load_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def text_value(value: Any) -> str:
    return str(value).strip() if value not in (None, "") else ""


def command_string(parts: list[str]) -> str:
    return shlex.join(parts)


def render_text_report(report: dict[str, Any]) -> str:
    lines = [
        f"schema_version: {report['schema_version']}",
        f"release_plan_dry_run_status: {report['release_plan_dry_run_status']}",
        f"candidate_site_id: {report['candidate_site_id']}",
        f"candidate_site_name: {report['candidate_site_name']}",
        f"candidate_selection_rationale: {report['candidate_selection_rationale']}",
        "",
        "release_plan_summary:",
    ]
    for key, value in report["release_plan_summary"].items():
        if isinstance(value, dict):
            lines.append(f"- {key}:")
            for subkey, subvalue in value.items():
                lines.append(f"  - {subkey}: {subvalue}")
        else:
            lines.append(f"- {key}: {value}")

    lines.append("")
    lines.append("reusable_semantics:")
    lines.extend(render_nested_dict(report["reusable_semantics"]))

    lines.append("")
    lines.append("site_specific_inputs:")
    lines.extend(render_nested_dict(report["site_specific_inputs"]))

    lines.append("")
    lines.append("tschamut_only_heuristics:")
    lines.extend(render_nested_dict(report["tschamut_only_heuristics"]))

    lines.append("")
    lines.append("deterministic_release_rows:")
    lines.extend(render_rows(report["deterministic_release_rows"]))

    lines.append("")
    lines.append("deterministic_block_scenario_rows:")
    lines.extend(render_rows(report["deterministic_block_scenario_rows"]))

    lines.append("")
    lines.append("machine_readable_distinction:")
    for key, value in report["machine_readable_distinction"].items():
        lines.append(f"- {key}: {', '.join(value)}")

    lines.append("")
    lines.append(f"blocked_reason: {report['blocked_reason']}")
    lines.append(f"scale_up_authorized: {str(report['scale_up_authorized']).lower()}")
    lines.append(f"operational_claims_allowed: {str(report['operational_claims_allowed']).lower()}")
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


def render_rows(rows: list[dict[str, Any]]) -> list[str]:
    rendered: list[str] = []
    if not rows:
        return ["- none"]
    for row in rows:
        rendered.append("- " + ", ".join(f"{key}={value}" for key, value in row.items()))
    return rendered


if __name__ == "__main__":
    raise SystemExit(main())
