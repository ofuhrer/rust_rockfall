#!/usr/bin/env python3
"""Check same-scale Tschamut artifact readiness before running diagnostics.

The preflight is read-only. It summarizes whether the ignored local same-scale
gate, target, context, and output-profile artifacts are present, and it emits
exact missing paths plus the known regeneration commands for the selected
pilot. It does not generate artifacts, change physics, or turn readiness into
an acceptance gate.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import shlex
import sys
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "tschamut_same_scale_artifact_readiness_v1"


def _load_module(module_name: str, filename: str):
    path = ROOT / "scripts" / filename
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


AUDIT = _load_module("audit_local_artifacts_for_readiness", "audit_local_artifacts.py")


GATE_VALIDATION_ROOT = ROOT / "validation/private/tschamut_public_pilot/gate_v1"
GATE_VALIDATION_CASE = GATE_VALIDATION_ROOT / "tschamut_public_conditional_gate_case.yaml"
GATE_VALIDATION_MANIFEST = GATE_VALIDATION_ROOT / "validation_tschamut_public_conditional_gate_v1_manifest.json"
GATE_HAZARD_ROOT = ROOT / "hazard/results/tschamut_public_pilot/gate_v1"
GATE_HAZARD_MANIFEST = GATE_HAZARD_ROOT / "validation_tschamut_public_conditional_gate_v1_manifest.json"

TARGET_VALIDATION_ROOT = ROOT / "validation/private/tschamut_public_pilot/target_gate_v1"
TARGET_VALIDATION_CASE = TARGET_VALIDATION_ROOT / "tschamut_public_target_gate_case.yaml"
TARGET_VALIDATION_MANIFEST = TARGET_VALIDATION_ROOT / "validation_tschamut_public_target_gate_v1_manifest.json"
TARGET_HAZARD_ROOT = ROOT / "hazard/results/tschamut_public_pilot/target_gate_v1"
TARGET_HAZARD_MANIFEST = TARGET_HAZARD_ROOT / "validation_tschamut_public_target_gate_v1_manifest.json"

TARGET_SUMMARY_ONLY_ROOT = ROOT / "validation/private/tschamut_public_pilot/target_gate_v1_summary_only"
TARGET_SUMMARY_ONLY_CASE = TARGET_SUMMARY_ONLY_ROOT / "tschamut_public_target_gate_summary_only_case.yaml"
TARGET_SUMMARY_ONLY_MANIFEST = TARGET_SUMMARY_ONLY_ROOT / "validation_tschamut_public_target_gate_v1_summary_only_manifest.json"

CONTEXT_ROOT = ROOT / "data/processed/swisstopo/tschamut_public_pilot/context"
CONTEXT_SWISSTLM3D_ROOT = CONTEXT_ROOT / "swisstlm3d"
CONTEXT_SWISSTLM3D_METADATA = CONTEXT_SWISSTLM3D_ROOT / "metadata.json"
CONTEXT_SWISSTLM3D_RAW_ARCHIVE = ROOT / "data/raw/swisstopo/swisstlm3d/swisstlm3d_2021-04_2056_5728.shp.zip"

TARGET_SOURCE_ZONE_METADATA = ROOT / "data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_source_zone_metadata_v1.yaml"
TARGET_SCENARIO_TABLE = ROOT / "data/processed/swisstopo/tschamut_public_pilot/input/tschamut_public_scenario_table_v1.csv"

CONVERGENCE_SCRIPT = ROOT / "scripts/compare_hazard_map_convergence.py"
CONTEXT_SCRIPT = ROOT / "scripts/inspect_tschamut_public_context_layers.py"
OVERLAP_SCRIPT = ROOT / "scripts/measure_hazard_context_overlap.py"
OUTPUT_PROFILE_SCRIPT = ROOT / "scripts/summarize_bounded_validation_output_profile.py"
UNCERTAINTY_ENVELOPE_SCRIPT = ROOT / "scripts/summarize_same_scale_uncertainty_envelope.py"
DOWNLOAD_CONTEXT_SCRIPT = ROOT / "scripts/download_tschamut_swisstlm3d_context.py"

TSCHAMUT_GRID_XMIN = 2696376.0
TSCHAMUT_GRID_YMIN = 1167384.0
TSCHAMUT_GRID_NCOLS = 300
TSCHAMUT_GRID_NROWS = 304
TSCHAMUT_GRID_CELL_SIZE = 2.0

TARGET_MAP_PRODUCT_ID = "tschamut_public_scalable_conditional_target_gate_v1"
GATE_MAP_PRODUCT_ID = "tschamut_public_conditional_gate_v1"

TARGET_HAZARD_THRESHOLDS = {
    "kinetic_energy_exceedance_j": [1000.0, 10000.0],
    "jump_height_exceedance_m": [0.5, 1.0, 2.0],
    "velocity_exceedance_mps": [5.0, 10.0],
}
GATE_HAZARD_THRESHOLDS = {
    "kinetic_energy_exceedance_j": [1000.0, 10000.0],
    "jump_height_exceedance_m": [1.0, 2.0],
}


@dataclass(frozen=True)
class ArtifactCheck:
    path: Path
    ready: bool
    summary: dict[str, Any]
    missing_paths: list[str]
    notes: list[str]


class SameScaleArtifactReadinessError(ValueError):
    """User-facing readiness error."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    parser.add_argument("--markdown-output", type=Path, default=None)
    args = parser.parse_args(argv)

    try:
        report = build_readiness_report()
    except SameScaleArtifactReadinessError as exc:
        print(f"same-scale artifact readiness error: {exc}", file=sys.stderr)
        return 2

    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.markdown_output is not None:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(render_text_report(report), encoding="utf-8")

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text_report(report))
    return 0 if report["readiness_status"] == "ready" else 2


def build_readiness_report() -> dict[str, Any]:
    gate_validation = check_validation_root(
        root=GATE_VALIDATION_ROOT,
        manifest_path=GATE_VALIDATION_MANIFEST,
        case_path=GATE_VALIDATION_CASE,
    )
    gate_hazard = check_hazard_manifest(
        root=GATE_HAZARD_ROOT,
        manifest_path=GATE_HAZARD_MANIFEST,
    )
    target_validation = check_validation_root(
        root=TARGET_VALIDATION_ROOT,
        manifest_path=TARGET_VALIDATION_MANIFEST,
        case_path=TARGET_VALIDATION_CASE,
    )
    target_hazard = check_hazard_manifest(
        root=TARGET_HAZARD_ROOT,
        manifest_path=TARGET_HAZARD_MANIFEST,
    )
    target_summary_only = check_summary_only_validation_root(
        root=TARGET_SUMMARY_ONLY_ROOT,
        manifest_path=TARGET_SUMMARY_ONLY_MANIFEST,
        case_path=TARGET_SUMMARY_ONLY_CASE,
    )
    context = check_context_root(root=CONTEXT_ROOT)
    swisstlm3d = check_swisstlm3d_context(path=CONTEXT_SWISSTLM3D_METADATA)

    checked_paths = collect_checked_paths(
        gate_validation,
        gate_hazard,
        target_validation,
        target_hazard,
        target_summary_only,
        context,
        swisstlm3d,
    )
    missing_paths = sorted(
        {
            *gate_validation.missing_paths,
            *gate_hazard.missing_paths,
            *target_validation.missing_paths,
            *target_hazard.missing_paths,
            *target_summary_only.missing_paths,
            *context.missing_paths,
            *swisstlm3d.missing_paths,
        }
    )

    convergence_ready = bool(gate_hazard.ready and target_hazard.ready and CONVERGENCE_SCRIPT.exists())
    output_profile_ready = bool(target_validation.ready and target_summary_only.ready and OUTPUT_PROFILE_SCRIPT.exists())
    hazard_context_overlap_ready = bool(target_hazard.ready and context.ready and swisstlm3d.ready and OVERLAP_SCRIPT.exists())

    readiness_status = "ready" if not missing_paths else "blocked_missing_inputs"
    blocked_reason = build_blocked_reason(
        missing_paths=missing_paths,
        readiness_status=readiness_status,
    )

    report = {
        "readiness_status": readiness_status,
        "gate_validation_ready": gate_validation.ready,
        "gate_hazard_ready": gate_hazard.ready,
        "target_validation_ready": target_validation.ready,
        "target_hazard_ready": target_hazard.ready,
        "target_summary_only_ready": target_summary_only.ready,
        "context_ready": context.ready,
        "swisstlm3d_ready": swisstlm3d.ready,
        "convergence_ready": convergence_ready,
        "output_profile_ready": output_profile_ready,
        "hazard_context_overlap_ready": hazard_context_overlap_ready,
        "missing_paths": missing_paths,
        "regeneration_commands": build_regeneration_commands(
            gate_validation=gate_validation,
            gate_hazard=gate_hazard,
            target_validation=target_validation,
            target_hazard=target_hazard,
            target_summary_only=target_summary_only,
            context=context,
            swisstlm3d=swisstlm3d,
            convergence_ready=convergence_ready,
            output_profile_ready=output_profile_ready,
            hazard_context_overlap_ready=hazard_context_overlap_ready,
        ),
        "checked_paths": checked_paths,
        "artifact_counts": {
            "gate_validation": gate_validation.summary,
            "gate_hazard": gate_hazard.summary,
            "target_validation": target_validation.summary,
            "target_hazard": target_hazard.summary,
            "target_summary_only": target_summary_only.summary,
            "context": context.summary,
            "swisstlm3d": swisstlm3d.summary,
            "target_convergence_inputs": {
                "gate_manifest": gate_hazard.summary,
                "target_manifest": target_hazard.summary,
            },
            "same_scale_uncertainty_envelope_inputs": {
                "gate_validation": gate_validation.summary,
                "target_validation": target_validation.summary,
                "target_hazard": target_hazard.summary,
                "target_summary_only": target_summary_only.summary,
                "context": context.summary,
                "swisstlm3d": swisstlm3d.summary,
            },
        },
        "scale_up_authorized": False,
        "operational_claims_allowed": False,
        "blocked_reason": blocked_reason,
    }
    return report


def check_validation_root(*, root: Path, manifest_path: Path, case_path: Path) -> ArtifactCheck:
    summary = summarize_path(root)
    missing_paths: list[str] = []
    notes: list[str] = []
    ready = root.exists() and summary.file_count > 0
    if not manifest_path.exists():
        missing_paths.append(str(manifest_path))
    if not case_path.exists():
        missing_paths.append(str(case_path))
    if not ready:
        notes.append("validation root has no local outputs yet")
    return ArtifactCheck(
        path=root,
        ready=bool(ready and not missing_paths),
        summary=summary_dict(summary),
        missing_paths=missing_paths,
        notes=notes,
    )


def check_summary_only_validation_root(*, root: Path, manifest_path: Path, case_path: Path) -> ArtifactCheck:
    check = check_validation_root(root=root, manifest_path=manifest_path, case_path=case_path)
    missing_paths = list(check.missing_paths)
    notes = list(check.notes)
    manifest_data = load_json(manifest_path) if manifest_path.exists() else {}
    if manifest_path.exists() and manifest_data.get("validation_output_mode") != "summary_only":
        notes.append("validation_output_mode is not summary_only")
        missing_paths.append(str(manifest_path))
    ready = check.ready and manifest_path.exists() and manifest_data.get("validation_output_mode") == "summary_only"
    return ArtifactCheck(
        path=root,
        ready=bool(ready and not missing_paths),
        summary=dict(check.summary),
        missing_paths=sorted(set(missing_paths)),
        notes=notes,
    )


def check_hazard_manifest(*, root: Path, manifest_path: Path) -> ArtifactCheck:
    summary = summarize_path(root)
    missing_paths: list[str] = []
    notes: list[str] = []
    ready = root.exists() and summary.file_count > 0
    if not manifest_path.exists():
        missing_paths.append(str(manifest_path))
        return ArtifactCheck(
            path=root,
            ready=False,
            summary=summary_dict(summary),
            missing_paths=missing_paths,
            notes=["hazard manifest is absent"],
        )

    manifest = load_json(manifest_path)
    if manifest.get("schema_version") != "run_manifest_v1":
        notes.append("hazard manifest has unexpected schema_version")
    cellwise_layers = manifest.get("cellwise_layers") or []
    if not isinstance(cellwise_layers, list) or not cellwise_layers:
        notes.append("hazard manifest does not expose cellwise_layers")
        ready = False
    for layer in cellwise_layers if isinstance(cellwise_layers, list) else []:
        grid_path = layer.get("grid_path") if isinstance(layer, dict) else None
        if not grid_path:
            continue
        grid = resolve_path(grid_path)
        if not grid.exists():
            missing_paths.append(str(grid))
            ready = False

    return ArtifactCheck(
        path=root,
        ready=bool(ready and not missing_paths),
        summary=summary_dict(summary),
        missing_paths=sorted(set(missing_paths)),
        notes=notes,
    )


def check_context_root(*, root: Path) -> ArtifactCheck:
    expected = [
        root / "swisssurface3d_raster",
        root / "swissimage",
        root / "swissbuildings3d",
        root / "swisstlm3d",
    ]
    summary = summarize_path(root)
    missing_paths = [str(path) for path in expected if not path.exists()]
    ready = root.exists() and summary.file_count > 0 and not missing_paths
    notes = []
    if not root.exists():
        notes.append(f"context root is absent at {root}")
    return ArtifactCheck(
        path=root,
        ready=ready,
        summary=summary_dict(summary),
        missing_paths=missing_paths,
        notes=notes,
    )


def check_swisstlm3d_context(*, path: Path) -> ArtifactCheck:
    summary = summarize_path(path)
    missing_paths: list[str] = []
    notes: list[str] = []
    if not path.exists():
        missing_paths.append(str(path))
        return ArtifactCheck(path=path, ready=False, summary=summary_dict(summary), missing_paths=missing_paths, notes=["swissTLM3D metadata is absent"])

    metadata = load_json(path)
    raw_asset_path = resolve_optional_path(metadata.get("raw_asset_path"))
    local_asset_path = resolve_optional_path(metadata.get("local_asset_path"))
    for candidate in [raw_asset_path, local_asset_path]:
        if candidate is not None and not candidate.exists():
            missing_paths.append(str(candidate))
    ready = bool(metadata.get("staged_asset_present")) and not missing_paths
    if not metadata.get("staged_asset_present"):
        notes.append("staged swissTLM3D archive is absent")
    return ArtifactCheck(
        path=path.parent,
        ready=ready,
        summary=summary_dict(summary),
        missing_paths=sorted(set(missing_paths)),
        notes=notes,
    )


def build_regeneration_commands(
    *,
    gate_validation: ArtifactCheck,
    gate_hazard: ArtifactCheck,
    target_validation: ArtifactCheck,
    target_hazard: ArtifactCheck,
    target_summary_only: ArtifactCheck,
    context: ArtifactCheck,
    swisstlm3d: ArtifactCheck,
    convergence_ready: bool,
    output_profile_ready: bool,
    hazard_context_overlap_ready: bool,
) -> list[dict[str, Any]]:
    commands = [
        {
            "category": "gate_validation",
            "status": readiness_label(gate_validation.ready),
            "command": cargo_validate_command(GATE_VALIDATION_CASE),
        },
        {
            "category": "gate_hazard",
            "status": readiness_label(gate_hazard.ready),
            "command": hazard_command(
                case_path=GATE_VALIDATION_CASE,
                output_dir=GATE_HAZARD_ROOT,
                map_product_id=GATE_MAP_PRODUCT_ID,
                diagnostics_path=GATE_VALIDATION_ROOT / "validation_tschamut_public_conditional_gate_v1_metrics.json",
                trajectory_path=GATE_VALIDATION_ROOT / "validation_tschamut_public_conditional_gate_v1_trajectory.csv",
                trajectories_dir=GATE_VALIDATION_ROOT / "validation_tschamut_public_conditional_gate_v1_trajectories",
                deposition_path=GATE_VALIDATION_ROOT / "validation_tschamut_public_conditional_gate_v1_deposition.csv",
                impact_events_dir=GATE_VALIDATION_ROOT / "validation_tschamut_public_conditional_gate_v1_impacts",
                map_package_manifest=GATE_HAZARD_ROOT / "tschamut_public_conditional_gate_v1_map_package_manifest.json",
                pilot_gis_manifest=GATE_HAZARD_ROOT / "tschamut_public_conditional_gate_v1_pilot_gis_package_manifest.json",
                thresholds=GATE_HAZARD_THRESHOLDS,
            ),
        },
        {
            "category": "target_validation",
            "status": readiness_label(target_validation.ready),
            "command": cargo_validate_command(TARGET_VALIDATION_CASE),
        },
        {
            "category": "target_hazard",
            "status": readiness_label(target_hazard.ready),
            "command": hazard_command(
                case_path=TARGET_VALIDATION_CASE,
                output_dir=TARGET_HAZARD_ROOT,
                map_product_id=TARGET_MAP_PRODUCT_ID,
                diagnostics_path=TARGET_VALIDATION_ROOT / "validation_tschamut_public_target_gate_v1_metrics.json",
                trajectory_path=TARGET_VALIDATION_ROOT / "validation_tschamut_public_target_gate_v1_trajectory.csv",
                trajectories_dir=TARGET_VALIDATION_ROOT / "validation_tschamut_public_target_gate_v1_trajectories",
                deposition_path=TARGET_VALIDATION_ROOT / "validation_tschamut_public_target_gate_v1_deposition.csv",
                impact_events_dir=TARGET_VALIDATION_ROOT / "validation_tschamut_public_target_gate_v1_impacts",
                map_package_manifest=TARGET_HAZARD_ROOT / "tschamut_public_scalable_conditional_target_gate_v1_map_package_manifest.json",
                pilot_gis_manifest=TARGET_HAZARD_ROOT / "tschamut_public_scalable_conditional_target_gate_v1_pilot_gis_package_manifest.json",
                thresholds=TARGET_HAZARD_THRESHOLDS,
            ),
        },
        {
            "category": "target_summary_only_validation",
            "status": readiness_label(target_summary_only.ready),
            "command": cargo_validate_command(TARGET_SUMMARY_ONLY_CASE),
        },
        {
            "category": "context_inspector",
            "status": readiness_label(context.ready),
            "command": command_list_to_string(
                [
                    "PYENV_VERSION=system",
                    "uv",
                    "run",
                    "python",
                    display_path(CONTEXT_SCRIPT),
                    "--format",
                    "json",
                ]
            ),
        },
        {
            "category": "swisstlm3d_staging",
            "status": readiness_label(swisstlm3d.ready),
            "command": command_list_to_string(
                [
                    "PYENV_VERSION=system",
                    "uv",
                    "run",
                    "python",
                    display_path(DOWNLOAD_CONTEXT_SCRIPT),
                    "--accept-large-download",
                    "--copy",
                    "--format",
                    "json",
                ]
            ),
        },
        {
            "category": "convergence_comparison",
            "status": readiness_label(convergence_ready),
            "command": command_list_to_string(
                [
                    "PYENV_VERSION=system",
                    "uv",
                    "run",
                    "python",
                    display_path(CONVERGENCE_SCRIPT),
                    display_path(GATE_HAZARD_MANIFEST),
                    display_path(TARGET_HAZARD_MANIFEST),
                    "--format",
                    "json",
                ]
            ),
        },
        {
            "category": "output_profile_summary",
            "status": readiness_label(output_profile_ready),
            "command": command_list_to_string(
                [
                    "PYENV_VERSION=system",
                    "uv",
                    "run",
                    "python",
                    display_path(OUTPUT_PROFILE_SCRIPT),
                    "--validation-output-baseline-manifest",
                    display_path(TARGET_VALIDATION_MANIFEST),
                    "--validation-output-reduced-manifest",
                    display_path(TARGET_SUMMARY_ONLY_MANIFEST),
                    "--format",
                    "json",
                ]
            ),
        },
        {
            "category": "hazard_context_overlap",
            "status": readiness_label(hazard_context_overlap_ready),
            "command": command_list_to_string(
                [
                    "PYENV_VERSION=system",
                    "uv",
                    "run",
                    "python",
                    display_path(OVERLAP_SCRIPT),
                    "--top-cell-count",
                    "1",
                    "--buffer-radii-m",
                    "20",
                    "--hazard-layer",
                    "reach_probability",
                    "--hazard-layer",
                    "max_kinetic_energy",
                    "--hazard-layer",
                    "max_jump_height",
                    "--format",
                    "json",
                ]
            ),
        },
        {
            "category": "same_scale_uncertainty_envelope",
            "status": readiness_label(
                gate_validation.ready
                and gate_hazard.ready
                and target_validation.ready
                and target_hazard.ready
                and target_summary_only.ready
                and context.ready
                and swisstlm3d.ready
            ),
            "command": command_list_to_string(
                [
                    "PYENV_VERSION=system",
                    "uv",
                    "run",
                    "python",
                    display_path(UNCERTAINTY_ENVELOPE_SCRIPT),
                    "--format",
                    "json",
                ]
            ),
        },
    ]
    return commands


def hazard_command(
    *,
    case_path: Path,
    output_dir: Path,
    map_product_id: str,
    diagnostics_path: Path,
    trajectory_path: Path,
    trajectories_dir: Path,
    deposition_path: Path,
    impact_events_dir: Path,
    map_package_manifest: Path,
    pilot_gis_manifest: Path,
    thresholds: dict[str, list[float]],
) -> str:
    parts = [
        "PYENV_VERSION=system",
        "uv",
        "run",
        "python",
        display_path(ROOT / "scripts" / "build_hazard_layers.py"),
        "--case",
        display_path(case_path),
        "--output-dir",
        display_path(output_dir),
        "--grid-xmin",
        str(TSCHAMUT_GRID_XMIN),
        "--grid-ymin",
        str(TSCHAMUT_GRID_YMIN),
        "--grid-ncols",
        str(TSCHAMUT_GRID_NCOLS),
        "--grid-nrows",
        str(TSCHAMUT_GRID_NROWS),
        "--grid-cell-size",
        str(TSCHAMUT_GRID_CELL_SIZE),
        "--map-product-id",
        map_product_id,
        "--probability-mode",
        "sampling_weighted_conditional",
        "--normalization-scope",
        "conditioned_on_filter",
        "--source-zone-metadata-path",
        display_path(TARGET_SOURCE_ZONE_METADATA),
        "--scenario-table-path",
        display_path(TARGET_SCENARIO_TABLE),
        "--map-package-manifest-json",
        display_path(map_package_manifest),
        "--export-geotiff",
        "--pilot-gis-package",
        "--pilot-gis-package-manifest-json",
        display_path(pilot_gis_manifest),
        "--pilot-gis-qa-status",
        "not-run",
        "--pilot-gis-qa-note",
        "Manual GIS/QGIS inspection has not been run for this generated package.",
        "--reducer-workers",
        "2",
        "--no-plots",
        "--conditional-curve-export",
        "summary-only",
        "--grid-csv-export",
        "none",
        "--diagnostics",
        display_path(diagnostics_path),
        "--trajectory",
        display_path(trajectory_path),
        "--ensemble-trajectories-dir",
        display_path(trajectories_dir),
        "--deposition",
        display_path(deposition_path),
        "--ensemble-impact-events-dir",
        display_path(impact_events_dir),
    ]
    for threshold in thresholds.get("kinetic_energy_exceedance_j", []):
        parts.extend(["--kinetic-energy-exceedance-j", str(threshold)])
    for threshold in thresholds.get("jump_height_exceedance_m", []):
        parts.extend(["--jump-height-exceedance-m", str(threshold)])
    for threshold in thresholds.get("velocity_exceedance_mps", []):
        parts.extend(["--velocity-exceedance-mps", str(threshold)])
    return command_list_to_string(parts)


def cargo_validate_command(case_path: Path) -> str:
    return command_list_to_string(
        [
            "PYENV_VERSION=system",
            "CARGO_TARGET_DIR=/tmp/rust-rockfall-target",
            "cargo",
            "run",
            "--",
            "validate",
            "--case",
            display_path(case_path),
        ]
    )


def command_list_to_string(parts: list[str]) -> str:
    return shlex.join(parts)


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def collect_checked_paths(*checks: ArtifactCheck) -> list[str]:
    checked: set[str] = set()
    for check in checks:
        checked.add(str(check.path))
        checked.update(check.missing_paths)
    checked.update(
        {
            str(GATE_VALIDATION_CASE),
            str(GATE_VALIDATION_MANIFEST),
            str(GATE_HAZARD_MANIFEST),
            str(TARGET_VALIDATION_CASE),
            str(TARGET_VALIDATION_MANIFEST),
            str(TARGET_HAZARD_MANIFEST),
            str(TARGET_SUMMARY_ONLY_CASE),
            str(TARGET_SUMMARY_ONLY_MANIFEST),
            str(CONTEXT_SWISSTLM3D_METADATA),
            str(CONTEXT_SWISSTLM3D_RAW_ARCHIVE),
            str(CONTEXT_ROOT),
            str(CONTEXT_SWISSTLM3D_ROOT),
            str(CONTEXT_SCRIPT),
            str(CONVERGENCE_SCRIPT),
            str(OVERLAP_SCRIPT),
            str(OUTPUT_PROFILE_SCRIPT),
            str(UNCERTAINTY_ENVELOPE_SCRIPT),
            str(DOWNLOAD_CONTEXT_SCRIPT),
        }
    )
    return sorted(checked)


def build_blocked_reason(*, missing_paths: list[str], readiness_status: str) -> str:
    if readiness_status == "ready":
        return ""
    if not missing_paths:
        return "blocked by missing or incomplete readiness inputs"
    return "missing readiness inputs: " + ", ".join(missing_paths)


def readiness_label(ready: bool) -> str:
    return "ready" if ready else "blocked_missing_inputs"


def summary_dict(summary: Any) -> dict[str, Any]:
    return {
        "path": summary.path,
        "exists": summary.exists,
        "file_count": summary.file_count,
        "total_bytes": summary.total_bytes,
    }


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - path context is essential.
        raise SameScaleArtifactReadinessError(f"failed to read JSON from {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise SameScaleArtifactReadinessError(f"JSON file must contain a mapping: {path}")
    return data


def resolve_path(path_value: str) -> Path:
    path = Path(path_value)
    return path if path.is_absolute() else ROOT / path


def resolve_optional_path(path_value: Any) -> Path | None:
    if not path_value:
        return None
    return resolve_path(str(path_value))


def check_results_to_text(report: dict[str, Any]) -> str:
    lines = [
        f"readiness_status: {report['readiness_status']}",
        f"scale_up_authorized: {str(report['scale_up_authorized']).lower()}",
        f"operational_claims_allowed: {str(report['operational_claims_allowed']).lower()}",
        "",
    ]
    categories = [
        ("gate_validation_ready", "gate validation"),
        ("gate_hazard_ready", "gate hazard"),
        ("target_validation_ready", "target validation"),
        ("target_hazard_ready", "target hazard"),
        ("target_summary_only_ready", "target summary-only validation"),
        ("context_ready", "public context"),
        ("swisstlm3d_ready", "swissTLM3D archive"),
        ("convergence_ready", "convergence diagnostic"),
        ("output_profile_ready", "output-profile diagnostic"),
        ("hazard_context_overlap_ready", "hazard-context overlap diagnostic"),
    ]
    for key, label in categories:
        lines.append(f"{label}: {str(report[key]).lower()}")
    lines.append("")
    if report["missing_paths"]:
        lines.append("missing_paths:")
        for path in report["missing_paths"]:
            lines.append(f"- {path}")
    else:
        lines.append("missing_paths: none")
    lines.append("")
    lines.append("regeneration_commands:")
    for entry in report["regeneration_commands"]:
        lines.append(f"- {entry['category']}: {entry['command']}")
    return "\n".join(lines)


def render_text_report(report: dict[str, Any]) -> str:
    return check_results_to_text(report)


def summarize_path(path: Path):
    if path.exists() and path.is_file():
        try:
            rel = str(path.relative_to(ROOT))
        except ValueError:
            rel = str(path)
        return SimpleNamespace(path=rel, exists=True, file_count=1, total_bytes=path.stat().st_size)
    return AUDIT.summarize_path(path, root=ROOT)


if __name__ == "__main__":
    raise SystemExit(main())
