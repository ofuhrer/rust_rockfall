#!/usr/bin/env python3
"""Summarize clean-checkout blocked reports for readiness and evidence helpers.

This helper is read-only. It runs selected readiness and evidence helpers
against an isolated clean-checkout root, verifies that they fail closed when
ignored local artifacts are absent, and prints a compact inventory of what is
tracked, fixture-backed, ignored-local, and unavailable in that state.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from typing import Any
from unittest import mock

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import check_same_scale_artifact_readiness as same_scale_readiness  # noqa: E402
from scripts import check_second_site_public_geodata_preflight as second_site_preflight  # noqa: E402
from scripts import summarize_balfrin_probe_metrics_report as balfrin_probe_metrics  # noqa: E402
from scripts import summarize_balfrin_target_area_evidence_bundle as target_area_bundle  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "clean_checkout_blocked_reports_v1"
SECOND_SITE_FIXTURE_CONFIG = ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml"
SECOND_SITE_FIXTURE_ACQUISITION_MANIFEST = (
    ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_public_geodata_acquisition.yaml"
)
REBUILDABLE_REDUCED_CASE_FIXTURE = (
    ROOT / "tests/fixtures/rebuildable_reduced_output/tschamut_public_target_gate_rebuildable_reduced_case.yaml"
)


class CleanCheckoutBlockedReportsError(ValueError):
    """User-facing clean-checkout blocked-report error."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("json", "text"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    parser.add_argument("--text-output", type=Path, default=None)
    parser.add_argument(
        "--artifact-dir",
        type=Path,
        default=None,
        help="Optional directory for the JSON and text report.",
    )
    parser.add_argument(
        "--clean-root",
        type=Path,
        default=None,
        help="Optional explicit clean-checkout root for tests.",
    )
    args = parser.parse_args(argv)

    try:
        report = build_report(args.clean_root)
    except CleanCheckoutBlockedReportsError as exc:
        print(f"clean-checkout blocked reports error: {exc}", file=sys.stderr)
        return 2

    materialize_artifacts(
        report,
        json_output=args.json_output,
        text_output=args.text_output,
        artifact_dir=args.artifact_dir,
    )

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text_report(report))
    return 0 if report["clean_checkout_status"] == "ready" else 2


def build_report(clean_root: Path | None = None) -> dict[str, Any]:
    if clean_root is None:
        with tempfile.TemporaryDirectory(prefix="clean_checkout_blocked_reports_") as tmpdir:
            return build_report(Path(tmpdir))

    clean_root = clean_root.resolve()
    clean_root.mkdir(parents=True, exist_ok=True)

    same_scale_report = build_same_scale_clean_checkout_report(clean_root)
    balfrin_probe_report = balfrin_probe_metrics.build_report(
        None,
        run_root=clean_root / "scratch" / "balfrin" / "missing-run-root",
    )
    target_area_report = target_area_bundle.build_report(
        {"missing_inputs": list(TARGET_AREA_BLOCKED_INPUTS)}
    )
    second_site_report = build_second_site_clean_checkout_report(clean_root)

    helper_statuses = {
        "same_scale_artifact_readiness": summarize_same_scale_report(same_scale_report),
        "balfrin_probe_metrics_report": summarize_probe_metrics_report(balfrin_probe_report),
        "balfrin_target_area_evidence_bundle": summarize_target_area_bundle_report(target_area_report),
        "second_site_public_geodata_preflight": summarize_second_site_report(second_site_report),
    }

    report = {
        "schema_version": SCHEMA_VERSION,
        "clean_checkout_status": "blocked_missing_inputs",
        "clean_checkout_root": str(clean_root),
        "helper_statuses": helper_statuses,
        "evidence_inventory": build_evidence_inventory(clean_root, same_scale_report, balfrin_probe_report, second_site_report),
        "readiness_commands": readiness_commands(clean_root),
        "summary": summarize_clean_checkout_report(helper_statuses),
    }
    return report


def build_same_scale_clean_checkout_report(clean_root: Path) -> dict[str, Any]:
    patches = {
        "GATE_VALIDATION_ROOT": clean_root / "validation/private/tschamut_public_pilot/gate_v1",
        "GATE_VALIDATION_CASE": clean_root / "validation/private/tschamut_public_pilot/gate_v1/tschamut_public_conditional_gate_case.yaml",
        "GATE_VALIDATION_MANIFEST": clean_root / "validation/private/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_manifest.json",
        "GATE_HAZARD_ROOT": clean_root / "hazard/results/tschamut_public_pilot/gate_v1",
        "GATE_HAZARD_MANIFEST": clean_root / "hazard/results/tschamut_public_pilot/gate_v1/validation_tschamut_public_conditional_gate_v1_manifest.json",
        "TARGET_VALIDATION_ROOT": clean_root / "validation/private/tschamut_public_pilot/target_gate_v1",
        "TARGET_VALIDATION_CASE": clean_root / "validation/private/tschamut_public_pilot/target_gate_v1/tschamut_public_target_gate_case.yaml",
        "TARGET_VALIDATION_MANIFEST": clean_root / "validation/private/tschamut_public_pilot/target_gate_v1/validation_tschamut_public_target_gate_v1_manifest.json",
        "TARGET_HAZARD_ROOT": clean_root / "hazard/results/tschamut_public_pilot/target_gate_v1",
        "TARGET_HAZARD_MANIFEST": clean_root / "hazard/results/tschamut_public_pilot/target_gate_v1/validation_tschamut_public_target_gate_v1_manifest.json",
        "TARGET_SUMMARY_ONLY_ROOT": clean_root / "validation/private/tschamut_public_pilot/target_gate_v1_summary_only",
        "TARGET_SUMMARY_ONLY_CASE": clean_root / "validation/private/tschamut_public_pilot/target_gate_v1_summary_only/tschamut_public_target_gate_summary_only_case.yaml",
        "TARGET_SUMMARY_ONLY_MANIFEST": clean_root / "validation/private/tschamut_public_pilot/target_gate_v1_summary_only/validation_tschamut_public_target_gate_v1_summary_only_manifest.json",
        "TARGET_REBUILDABLE_REDUCED_ROOT": clean_root / "validation/private/tschamut_public_pilot/target_gate_v1_rebuildable_reduced",
        "TARGET_REBUILDABLE_REDUCED_MANIFEST": clean_root / "validation/private/tschamut_public_pilot/target_gate_v1_rebuildable_reduced/validation_tschamut_public_target_gate_v1_rebuildable_reduced_manifest.json",
        "CONTEXT_ROOT": clean_root / "data/processed/swisstopo/tschamut_public_pilot/context",
        "CONTEXT_SWISSTLM3D_ROOT": clean_root / "data/processed/swisstopo/tschamut_public_pilot/context/swisstlm3d",
        "CONTEXT_SWISSTLM3D_METADATA": clean_root / "data/processed/swisstopo/tschamut_public_pilot/context/swisstlm3d/metadata.json",
        "CONTEXT_SWISSTLM3D_RAW_ARCHIVE": clean_root / "data/raw/swisstopo/swisstlm3d/swisstlm3d_2021-04_2056_5728.shp.zip",
        "TARGET_SOURCE_ZONE_METADATA": clean_root / "data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_source_zone_metadata_v1.yaml",
        "TARGET_SCENARIO_TABLE": clean_root / "data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_scenario_table_v1.csv",
    }
    with mock.patch.multiple(same_scale_readiness, **patches):
        return same_scale_readiness.build_readiness_report()


def build_second_site_clean_checkout_report(clean_root: Path) -> dict[str, Any]:
    site_config_path = build_clean_checkout_second_site_config(clean_root)
    with mock.patch.object(second_site_preflight, "ROOT", clean_root):
        return second_site_preflight.build_report(site_config_path)


def build_clean_checkout_second_site_config(clean_root: Path) -> Path:
    config_path = clean_root / "clean_checkout_second_site_candidate.json"
    payload = {
        "schema_version": second_site_preflight.SCHEMA_VERSION,
        "candidate_site_id": "chant_sura_fluelapass_portability_example_v1",
        "candidate_site_name": "Chant Sura / Flüelapass portability example",
        "candidate_selection_rationale": (
            "Chant Sura is the clearest concrete Swiss candidate already represented in repository benchmark metadata "
            "and validation fixtures. The clean-checkout harness keeps the report metadata-only while the staged "
            "public-geodata inputs are absent."
        ),
        "acquisition_manifest_path": str(SECOND_SITE_FIXTURE_ACQUISITION_MANIFEST),
        "site_extent": {
            "crs": "EPSG:2056",
            "xmin": 2793000.0,
            "ymin": 1180200.0,
            "xmax": 2793800.0,
            "ymax": 1180800.0,
        },
        "source_zone_scenario_contract": {
            "source_zone_id_pattern": "chant_sura_*",
            "source_zone_geometry": "LV95 polygon",
            "release_point_table": "one row per release point",
            "observed_deposition_or_field_observation": "optional if a site-specific QA source exists",
            "block_scenario_table": "CSV table with one row per block / scenario record",
            "scenario_probability_semantics": "normalized within a block family; no annual frequency claim",
        },
        "expected_processed_input_root": str(clean_root / "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input"),
        "expected_processed_context_root": str(clean_root / "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/context"),
        "expected_terrain_crop_path": str(clean_root / "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/terrain.asc"),
        "expected_aoi_tile_catalog_path": str(clean_root / "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/aoi_tile_catalog.yaml"),
        "expected_terrain_metadata_path": str(clean_root / "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/terrain_metadata.yaml"),
        "expected_source_zone_metadata_path": str(clean_root / "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/source_zone_metadata.yaml"),
        "expected_scenario_table_path": str(clean_root / "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/input/scenario_table.csv"),
        "expected_source_scenario_policy_path": str(
            clean_root
            / "validation/policies/chant_sura_fluelapass_portability_example_v1_source_scenario_policy_v1.yaml"
        ),
        "expected_validation_private_root": str(clean_root / "validation/private/chant_sura_fluelapass_portability_example_v1"),
        "expected_hazard_results_root": str(clean_root / "hazard/results/chant_sura_fluelapass_portability_example_v1"),
        "expected_swissimage_context_root": str(
            clean_root / "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/context/swissimage"
        ),
        "expected_swisstlm3d_context_root": str(
            clean_root / "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/context/swisstlm3d"
        ),
        "expected_swisstlm3d_metadata_path": str(
            clean_root / "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/context/swisstlm3d/metadata.json"
        ),
        "expected_swisssurface3d_context_root": str(
            clean_root / "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/context/swisssurface3d"
        ),
        "expected_swisssurface3d_raster_context_root": str(
            clean_root / "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/context/swisssurface3d_raster"
        ),
        "expected_swissbuildings3d_context_root": str(
            clean_root / "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/context/swissbuildings3d"
        ),
        "expected_barrier_inventory_root": str(
            clean_root / "data/processed/swisstopo/chant_sura_fluelapass_portability_example_v1/context/barriers"
        ),
    }
    config_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return config_path


def summarize_same_scale_report(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "readiness_status": report.get("readiness_status", "unknown"),
        "blocked_reason": report.get("blocked_reason", ""),
        "missing_paths": list(report.get("missing_paths") or []),
        "missing_path_count": len(report.get("missing_paths") or []),
        "target_hazard_ready": bool(report.get("target_hazard_ready")),
        "target_validation_ready": bool(report.get("target_validation_ready")),
        "target_rebuildable_reduced_ready": bool(report.get("target_rebuildable_reduced_ready")),
        "context_ready": bool(report.get("context_ready")),
    }


def summarize_probe_metrics_report(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "report_status": report.get("report_status", "unknown"),
        "run_root_status": report.get("run_root_status", "unknown"),
        "run_root": report.get("run_root", ""),
        "missing_run_root_reason": report.get("missing_run_root_reason", ""),
        "metrics_contract_status": report.get("metrics_contract_status", "unknown"),
    }


def summarize_target_area_bundle_report(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "bundle_status": report.get("bundle_status", "unknown"),
        "bundle_summary": report.get("bundle_summary", {}),
        "missing_inputs": list(report.get("missing_inputs") or []),
    }


def summarize_second_site_report(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "portability_preflight_status": report.get("portability_preflight_status", "unknown"),
        "core_input_status": report.get("core_input_status", "unknown"),
        "public_context_boundary_status": report.get("public_context_boundary_status", "unknown"),
        "acquisition_manifest_status": report.get("acquisition_manifest_status", "unknown"),
        "missing_input_categories": list(report.get("missing_input_categories") or []),
        "deferred_public_context_categories": list(report.get("deferred_public_context_categories") or []),
        "missing_input_paths_or_patterns": list(report.get("missing_input_paths_or_patterns") or []),
    }


def build_evidence_inventory(
    clean_root: Path,
    same_scale_report: dict[str, Any],
    balfrin_probe_report: dict[str, Any],
    second_site_report: dict[str, Any],
) -> dict[str, list[str]]:
    ignored_local_paths = list(same_scale_report.get("missing_paths") or [])
    ignored_local_paths.extend(
        [
            str(clean_root / "validation/private/tschamut_public_pilot/gate_v1"),
            str(clean_root / "validation/private/tschamut_public_pilot/target_gate_v1"),
            str(clean_root / "validation/private/tschamut_public_pilot/target_gate_v1_summary_only"),
            str(clean_root / "validation/private/tschamut_public_pilot/target_gate_v1_rebuildable_reduced"),
            str(clean_root / "hazard/results/tschamut_public_pilot/gate_v1"),
            str(clean_root / "hazard/results/tschamut_public_pilot/target_gate_v1"),
            str(balfrin_probe_report.get("run_root", "")),
        ]
    )
    ignored_local_paths.extend(second_site_report.get("missing_input_paths_or_patterns") or [])

    return {
        "tracked": [
            "scripts/check_same_scale_artifact_readiness.py",
            "scripts/summarize_balfrin_probe_metrics_report.py",
            "scripts/summarize_balfrin_target_area_evidence_bundle.py",
            "scripts/check_second_site_public_geodata_preflight.py",
            "docs/balfrin_tschamut_pilot_runbook.md",
        ],
        "fixture_backed": [
            str(REBUILDABLE_REDUCED_CASE_FIXTURE),
            str(SECOND_SITE_FIXTURE_CONFIG),
            str(SECOND_SITE_FIXTURE_ACQUISITION_MANIFEST),
        ],
        "ignored_local": sorted({path for path in ignored_local_paths if path}),
        "unavailable": [
            f"same_scale_artifact_readiness -> {same_scale_readiness_status(same_scale_report)}",
            f"balfrin_probe_metrics_report -> {balfrin_probe_report.get('report_status', 'unknown')}",
            f"balfrin_target_area_evidence_bundle -> {target_area_bundle_status()}",
            f"second_site_public_geodata_preflight -> {second_site_report.get('portability_preflight_status', 'unknown')}",
        ],
    }


def same_scale_readiness_status(report: dict[str, Any]) -> str:
    return str(report.get("readiness_status") or "unknown")


def target_area_bundle_status() -> str:
    blocked_report = target_area_bundle.build_report({"missing_inputs": list(TARGET_AREA_BLOCKED_INPUTS)})
    return str(blocked_report.get("bundle_status") or "unknown")


def summarize_clean_checkout_report(helper_statuses: dict[str, Any]) -> str:
    return (
        "Clean checkout keeps the selected readiness and evidence helpers fail-closed: "
        f"same-scale={helper_statuses['same_scale_artifact_readiness']['readiness_status']}, "
        f"balfrin-metrics={helper_statuses['balfrin_probe_metrics_report']['report_status']}, "
        f"target-area={helper_statuses['balfrin_target_area_evidence_bundle']['bundle_status']}, "
        f"second-site={helper_statuses['second_site_public_geodata_preflight']['portability_preflight_status']}."
    )


def readiness_commands(clean_root: Path) -> list[str]:
    return [
        "PYENV_VERSION=system uv run python scripts/summarize_clean_checkout_blocked_reports.py --format json",
        "PYENV_VERSION=system uv run python scripts/check_same_scale_artifact_readiness.py --format json",
        "PYENV_VERSION=system uv run python scripts/summarize_balfrin_probe_metrics_report.py --run-root /scratch/mch/olifu/rust_rockfall/probes/tschamut_public_balfrin_target_area_demo_v1/<missing-run-root> --format json",
        "PYENV_VERSION=system uv run python scripts/check_second_site_public_geodata_preflight.py --site-config tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml --format json",
    ]


def render_text_report(report: dict[str, Any]) -> str:
    lines = [
        "Clean Checkout Blocked Reports",
        f"schema_version: {report.get('schema_version', 'unknown')}",
        f"clean_checkout_status: {report.get('clean_checkout_status', 'unknown')}",
        f"clean_checkout_root: {report.get('clean_checkout_root', 'unknown')}",
        f"summary: {report.get('summary', '')}",
    ]

    helper_statuses = report.get("helper_statuses", {}) if isinstance(report, dict) else {}
    if helper_statuses:
        lines.append("helper_statuses:")
        for helper_name in (
            "same_scale_artifact_readiness",
            "balfrin_probe_metrics_report",
            "balfrin_target_area_evidence_bundle",
            "second_site_public_geodata_preflight",
        ):
            helper = helper_statuses.get(helper_name, {})
            lines.append(f"  - {helper_name}:")
            for key, value in helper.items():
                lines.append(f"      {key}: {value}")

    inventory = report.get("evidence_inventory", {}) if isinstance(report, dict) else {}
    if inventory:
        lines.append("evidence_inventory:")
        for group in ("tracked", "fixture_backed", "ignored_local", "unavailable"):
            values = inventory.get(group) or []
            lines.append(f"  {group}:")
            for value in values:
                lines.append(f"    - {value}")

    commands = report.get("readiness_commands", []) if isinstance(report, dict) else []
    if commands:
        lines.append("readiness_commands:")
        for command in commands:
            lines.append(f"  - {command}")

    return "\n".join(lines)


def materialize_artifacts(
    report: dict[str, Any],
    *,
    json_output: Path | None = None,
    text_output: Path | None = None,
    artifact_dir: Path | None = None,
) -> None:
    if artifact_dir is not None:
        json_output = json_output or artifact_dir / f"{SCHEMA_VERSION}.json"
        text_output = text_output or artifact_dir / f"{SCHEMA_VERSION}.txt"
    if json_output is not None:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if text_output is not None:
        text_output.parent.mkdir(parents=True, exist_ok=True)
        text_output.write_text(render_text_report(report), encoding="utf-8")


TARGET_AREA_BLOCKED_INPUTS = [
    "target_area_demo_handoff_report",
    "probe_metrics_report",
    "canonical_evidence_bundle",
]


if __name__ == "__main__":
    raise SystemExit(main())
