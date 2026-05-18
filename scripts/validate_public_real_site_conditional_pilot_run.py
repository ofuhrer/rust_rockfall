#!/usr/bin/env python3
"""Validate the Phase 6 public real-site conditional pilot run-freeze contract."""

from __future__ import annotations

import argparse
import json
import math
import re
import shlex
import sys
from functools import partial
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from lib.workflow_validation import (
    normalize_text,
    require as shared_require,
    require_int as shared_require_int,
    require_list as shared_require_list,
    require_mapping as shared_require_mapping,
    require_number as shared_require_number,
    require_paths_exist as shared_require_paths_exist,
    require_checksum_fields as shared_require_checksum_fields,
    require_text as shared_require_text,
    render_status_message,
    SHA256_HEX_RE as SHARED_SHA256_HEX_RE,
    read_yaml as shared_read_yaml,
    resolve_repo_path,
    scan_text_for_misleading_claims as shared_scan_text_for_misleading_claims,
)


ROOT = Path(__file__).resolve().parents[1]
HEX_SHA256_RE = SHARED_SHA256_HEX_RE
SUPPORTED_RUN_STATUSES = {
    "template_not_run",
    "predeclared_ready",
    "gate_run_completed",
    "target_run_completed",
    "no_go",
    "inconclusive",
}
SUPPORTED_GATE_STATUSES = {"not_run", "pass", "no-go", "inconclusive"}
SUPPORTED_EVIDENCE_STATUSES = {"not_run", "gate_run_completed", "target_run_completed", "no-go", "inconclusive"}
COMPLETED_RUN_STATUSES = {"gate_run_completed", "target_run_completed"}
REQUIRED_EVIDENCE_PATHS = (
    "validation_manifest_path",
    "hazard_manifest_path",
    "conditional_curve_table_path",
    "map_package_manifest_path",
    "pilot_gis_package_manifest_path",
    "reducer_chunk_manifest_dir",
)
REQUIRED_ARTIFACT_CHECKSUMS = (
    "validation_manifest_sha256",
    "hazard_manifest_sha256",
    "conditional_curve_table_sha256",
    "map_package_manifest_sha256",
    "pilot_gis_package_manifest_sha256",
)
OPTIONAL_ARTIFACT_CHECKSUMS = (
    "dem_sensitivity_summary_sha256",
    "scaling_summary_sha256",
)
SELECTED_REPORT_ARTIFACT_CHECKSUMS = (
    ("validation_manifest_sha256", "Validation manifest"),
    ("hazard_manifest_sha256", "Hazard manifest"),
    ("conditional_curve_table_sha256", "Conditional curve table"),
    ("map_package_manifest_sha256", "Map-package manifest"),
    ("pilot_gis_package_manifest_sha256", "Pilot GIS package manifest"),
    ("dem_sensitivity_summary_sha256", "DEM sensitivity summary"),
    ("scaling_summary_sha256", "Scaling summary"),
)
SELECTED_GATE_RUN_ID = "tschamut_public_conditional_gate_v1"
SELECTED_PILOT_ID = "tschamut_public_pilot"
SELECTED_REPORT_PATH = "docs/tschamut_public_conditional_pilot_gate_report.md"
SELECTED_REQUIRED_PATH_ROOTS = {
    "validation_manifest_path": "validation/",
    "hazard_manifest_path": "hazard/results/",
    "conditional_curve_table_path": "hazard/results/",
    "map_package_manifest_path": "hazard/results/",
    "pilot_gis_package_manifest_path": "hazard/results/",
    "reducer_chunk_manifest_dir": "hazard/results/",
    "dem_sensitivity_summary_path": "validation/",
    "scaling_summary_path": "hazard/results/",
}
SUPPORTED_CONDITIONAL_CURVE_EXPORT_MODES = {"full", "summary-only"}
SUPPORTED_GRID_CSV_EXPORT_MODES = {"full", "none"}
REQUIRED_UNSUPPORTED_CLAIMS = {
    "annual_frequency",
    "return_period",
    "physical_probability",
    "risk_map",
    "operational_hazard_map",
    "validated_hazard_map",
}
REQUIRED_BUDGET_METRICS = {
    "runtime_seconds",
    "memory_peak_mb",
    "output_file_count",
    "output_total_bytes",
    "trajectory_count",
    "release_cell_count",
}
NO_GO_RUN_STATUSES = {"no_go", "inconclusive"}


class PilotRunError(ValueError):
    """User-facing pilot run validation error."""


require = partial(shared_require, error_cls=PilotRunError)
require_int = partial(shared_require_int, error_cls=PilotRunError)
require_list = partial(shared_require_list, error_cls=PilotRunError)
require_mapping = partial(shared_require_mapping, error_cls=PilotRunError)
require_number = partial(shared_require_number, error_cls=PilotRunError)
require_text = partial(shared_require_text, error_cls=PilotRunError)
read_yaml = partial(shared_read_yaml, error_cls=PilotRunError)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_manifest", type=Path)
    parser.add_argument(
        "--print-command-plan",
        action="store_true",
        help="print the validated dry-run command plan for a non-template pilot freeze file",
    )
    parser.add_argument(
        "--format",
        choices=["shell", "json"],
        default="shell",
        help="command-plan output format when --print-command-plan is used",
    )
    args = parser.parse_args(argv)
    try:
        manifest = read_yaml(
            args.run_manifest,
            read_message="failed to read",
            object_message="run manifest must contain a YAML mapping",
        )
        validate_pilot_run(manifest, args.run_manifest)
        if args.print_command_plan:
            plan = build_command_plan(manifest)
            print_command_plan(plan, args.format)
        else:
            print(
                render_status_message(
                    "public real-site conditional pilot run contract",
                    args.run_manifest,
                    manifest,
                    "run_status",
                    extra_fields=(("operational_status", "operational_status"),),
                )
            )
    except PilotRunError as exc:
        print(f"pilot run validation error: {exc}", file=sys.stderr)
        return 2
    return 0


def validate_pilot_run(manifest: dict[str, Any], manifest_path: Path | None = None) -> None:
    require(
        manifest.get("schema_version") == "public_real_site_conditional_pilot_run_v1",
        "schema_version must be public_real_site_conditional_pilot_run_v1",
    )
    pilot_id = require_text(manifest.get("pilot_id"), "pilot_id")
    run_id = require_text(manifest.get("run_id"), "run_id")
    run_status = require_text(manifest.get("run_status"), "run_status")
    require(run_status in SUPPORTED_RUN_STATUSES, f"run_status must be one of {sorted(SUPPORTED_RUN_STATUSES)}")
    require(
        manifest.get("operational_status") == "research_diagnostic",
        "operational_status must remain research_diagnostic",
    )

    input_freeze = require_mapping(manifest.get("input_freeze"), "input_freeze")
    validate_input_freeze(input_freeze, run_status)
    validate_physics_freeze(require_mapping(manifest.get("physics_freeze"), "physics_freeze"), run_status)
    validate_sampling_plan(require_mapping(manifest.get("sampling_plan"), "sampling_plan"), run_status)
    validate_hazard_output_plan(
        require_mapping(manifest.get("hazard_output_plan"), "hazard_output_plan"),
        pilot_id,
        run_status,
    )
    validate_workflow_gates(require_mapping(manifest.get("workflow_gates"), "workflow_gates"), run_status)
    validate_output_budget(require_mapping(manifest.get("output_budget"), "output_budget"), run_status)
    run_evidence = require_mapping(manifest.get("run_evidence"), "run_evidence")
    validate_run_evidence(run_evidence, run_status)
    report_plan = require_mapping(manifest.get("report_plan"), "report_plan")
    validate_report_plan(report_plan, run_status)
    validate_claim_boundary(require_mapping(manifest.get("claim_boundary"), "claim_boundary"))
    validate_selected_gate_contract(
        run_id=run_id,
        pilot_id=pilot_id,
        run_status=run_status,
        input_freeze=require_mapping(manifest.get("input_freeze"), "input_freeze"),
        run_evidence=run_evidence,
        report_plan=report_plan,
    )
    if run_status == "no_go":
        validate_no_go_blocker(require_mapping(manifest.get("no_go_blocker"), "no_go_blocker"))

    shared_scan_text_for_misleading_claims(
        manifest,
        require_fn=require,
    )

    if manifest_path is not None and run_status == "template_not_run":
        require(
            "template" in manifest_path.name or manifest_path.parent.name == "templates",
            "template_not_run pilot run manifests should use a template filename or live under validation/templates/",
        )


def build_command_plan(manifest: dict[str, Any]) -> dict[str, Any]:
    validate_pilot_run(manifest)
    run_status = str(manifest["run_status"])
    if run_status == "template_not_run":
        raise PilotRunError("template_not_run manifests do not have enough frozen inputs for a command plan")
    if run_status == "no_go":
        return build_no_go_command_plan(manifest)

    input_freeze = require_mapping(manifest["input_freeze"], "input_freeze")
    sampling = require_mapping(manifest["sampling_plan"], "sampling_plan")
    hazard_plan = require_mapping(manifest["hazard_output_plan"], "hazard_output_plan")
    output_roots = require_mapping(hazard_plan["output_roots"], "hazard_output_plan.output_roots")
    grid = require_mapping(hazard_plan["explicit_grid"], "hazard_output_plan.explicit_grid")
    benchmark_case_path = require_text(input_freeze["benchmark_case_path"], "input_freeze.benchmark_case_path")
    benchmark_case_file = resolve_repo_path(ROOT, benchmark_case_path)
    benchmark_case = (
        read_yaml(
            benchmark_case_file,
            read_message="failed to read",
            object_message="run manifest must contain a YAML mapping",
        )
        if benchmark_case_file.exists()
        else {}
    )
    outputs = (
        require_mapping(benchmark_case.get("outputs"), "benchmark_case.outputs")
        if benchmark_case
        else {}
    )
    hazard_output_dir = require_text(output_roots["hazard_results"], "hazard_output_plan.output_roots.hazard_results")
    run_id = require_text(manifest.get("run_id"), "run_id")

    commands = [
        command_entry(
            "validate_geodata_manifest",
            "Validate the predeclared public geodata manifest before any run.",
            [
                "uv",
                "run",
                "python",
                "scripts/validate_public_real_site_geodata_manifest.py",
                str(input_freeze["geodata_manifest_path"]),
            ],
            env={"UV_CACHE_DIR": "/tmp/uv-cache"},
        ),
        command_entry(
            "validate_source_scenario_policy",
            "Validate the predeclared source-zone and block-scenario policy before any run.",
            [
                "uv",
                "run",
                "python",
                "scripts/validate_source_scenario_policy.py",
                str(input_freeze["source_scenario_policy_path"]),
            ],
            env={"UV_CACHE_DIR": "/tmp/uv-cache"},
        ),
        command_entry(
            "run_validation_gate",
            "Run the frozen validation or benchmark case that generates trajectory/deposition inputs.",
            ["cargo", "run", "--", "validate", "--case", benchmark_case_path],
        ),
        command_entry(
            "build_conditional_hazard_layers",
            "Build sampling-weighted conditional hazard layers, curve table, GeoTIFFs, GIS package manifest, and reducer manifests.",
            build_hazard_command(
                benchmark_case_path,
                outputs,
                input_freeze,
                hazard_plan,
                sampling,
                grid,
                hazard_output_dir,
                run_id,
            ),
            env={"UV_CACHE_DIR": "/tmp/uv-cache"},
        ),
    ]
    return {
        "schema_version": "public_real_site_conditional_pilot_command_plan_v1",
        "run_id": run_id,
        "run_status": run_status,
        "operational_status": "research_diagnostic",
        "generated_outputs_committed": False,
        "commands": commands,
        "claim_boundary": manifest["claim_boundary"],
    }


def build_no_go_command_plan(manifest: dict[str, Any]) -> dict[str, Any]:
    input_freeze = require_mapping(manifest["input_freeze"], "input_freeze")
    blocker = require_mapping(manifest["no_go_blocker"], "no_go_blocker")
    commands = [
        command_entry(
            "validate_geodata_manifest",
            "Validate the selected public geodata manifest before resolving the gate blocker.",
            [
                "uv",
                "run",
                "python",
                "scripts/validate_public_real_site_geodata_manifest.py",
                str(input_freeze["geodata_manifest_path"]),
            ],
            env={"UV_CACHE_DIR": "/tmp/uv-cache"},
        ),
        command_entry(
            "validate_source_scenario_policy",
            "Validate the selected source-zone and block-scenario policy before resolving the gate blocker.",
            [
                "uv",
                "run",
                "python",
                "scripts/validate_source_scenario_policy.py",
                str(input_freeze["source_scenario_policy_path"]),
            ],
            env={"UV_CACHE_DIR": "/tmp/uv-cache"},
        ),
        command_entry(
            "record_dem_sensitivity_blocker",
            "Record the selected-domain DEM sensitivity no-go gate until public geodata preparation creates the ignored processed DEM.",
            [
                "uv",
                "run",
                "python",
                "scripts/run_dem_terrain_sensitivity.py",
                "--pilot-manifest",
                str(input_freeze["geodata_manifest_path"]),
                "--source-scenario-policy",
                str(input_freeze["source_scenario_policy_path"]),
                "--allow-missing-source-dem",
                "--output-dir",
                str(blocker["evidence_output_dir"]),
            ],
            env={"UV_CACHE_DIR": "/tmp/uv-cache"},
        ),
    ]
    return {
        "schema_version": "public_real_site_conditional_pilot_command_plan_v1",
        "run_id": require_text(manifest.get("run_id"), "run_id"),
        "run_status": "no_go",
        "operational_status": "research_diagnostic",
        "generated_outputs_committed": False,
        "commands": commands,
        "blocker": blocker,
        "claim_boundary": manifest["claim_boundary"],
    }


def build_hazard_command(
    benchmark_case_path: str,
    outputs: dict[str, Any],
    input_freeze: dict[str, Any],
    hazard_plan: dict[str, Any],
    sampling: dict[str, Any],
    grid: dict[str, Any],
    hazard_output_dir: str,
    run_id: str,
) -> list[str]:
    def normalize_token(value: Any) -> str:
        return normalize_text(value)

    benchmark_case_path_obj = Path(benchmark_case_path)
    benchmark_case_path_abs = resolve_repo_path(ROOT, benchmark_case_path)
    benchmark_case_id = input_freeze.get("benchmark_case_id")
    case_id = benchmark_case_id or run_id
    if not benchmark_case_id and benchmark_case_path_abs.exists():
        benchmark_case = read_yaml(
            benchmark_case_path_abs,
            read_message="failed to read",
            object_message="run manifest must contain a YAML mapping",
        )
        case_id = require_text(benchmark_case.get("case_id"), "benchmark_case.case_id")
    command = [
        "uv",
        "run",
        "python",
        "scripts/build_hazard_layers.py",
        "--case",
        benchmark_case_path,
        "--output-dir",
        hazard_output_dir,
        "--grid-xmin",
        str(grid["xmin"]),
        "--grid-ymin",
        str(grid["ymin"]),
        "--grid-ncols",
        str(grid["ncols"]),
        "--grid-nrows",
        str(grid["nrows"]),
        "--grid-cell-size",
        str(grid["cell_size_m"]),
        "--map-product-id",
        str(input_freeze["map_product_id"]),
        "--probability-mode",
        str(hazard_plan["probability_mode"]),
        "--normalization-scope",
        str(hazard_plan["normalization_scope"]),
        "--source-zone-metadata-path",
        str(input_freeze["source_zone_metadata_path"]),
        "--scenario-table-path",
        str(input_freeze["scenario_table_path"]),
        "--map-package-manifest-json",
        str(Path(hazard_output_dir) / f"{run_id}_map_package_manifest.json"),
        "--export-geotiff",
        "--pilot-gis-package",
        "--pilot-gis-package-manifest-json",
        str(Path(hazard_output_dir) / f"{run_id}_pilot_gis_package_manifest.json"),
        "--pilot-gis-qa-status",
        "not-run",
        "--pilot-gis-qa-note",
        "Manual GIS/QGIS inspection has not been run for this generated package.",
        "--reducer-workers",
        str(sampling["worker_count"]),
        "--no-plots",
    ]
    conditional_curve_export = hazard_plan.get("conditional_curve_export")
    if conditional_curve_export is not None:
        command.extend(["--conditional-curve-export", str(conditional_curve_export)])
    grid_csv_export = hazard_plan.get("grid_csv_export")
    if grid_csv_export is not None:
        command.extend(["--grid-csv-export", str(grid_csv_export)])
    trajectory_workers = hazard_plan.get("trajectory_workers")
    if trajectory_workers is not None:
        command.extend(["--trajectory-workers", str(trajectory_workers)])
    output_parent = benchmark_case_path_obj.parent
    default_outputs = {
        "diagnostics_json": f"{case_id}_metrics.json",
        "trajectory_csv": f"{case_id}_trajectory.csv",
        "ensemble_trajectories_dir": f"{case_id}_trajectories",
        "ensemble_deposition_csv": f"{case_id}_deposition.csv",
        "ensemble_impact_events_dir": f"{case_id}_impacts",
    }
    for output_key, output_name in default_outputs.items():
        if not outputs.get(output_key):
            outputs[output_key] = normalize_token(output_parent / output_name)
        else:
            outputs[output_key] = normalize_token(outputs[output_key])
    optional_output_args = {
        "diagnostics_json": "--diagnostics",
        "trajectory_csv": "--trajectory",
        "ensemble_trajectories_dir": "--ensemble-trajectories-dir",
        "ensemble_deposition_csv": "--deposition",
        "ensemble_impact_events_dir": "--ensemble-impact-events-dir",
        "ensemble_impact_events_parquet": "--impact-events-parquet",
    }
    for output_key, flag in optional_output_args.items():
        if outputs.get(output_key):
            command.extend([flag, normalize_token(outputs[output_key])])
    for threshold in hazard_plan["kinetic_energy_exceedance_j"]:
        command.extend(["--kinetic-energy-exceedance-j", str(threshold)])
    for threshold in hazard_plan["jump_height_exceedance_m"]:
        command.extend(["--jump-height-exceedance-m", str(threshold)])
    for threshold in hazard_plan["velocity_exceedance_mps"]:
        command.extend(["--velocity-exceedance-mps", str(threshold)])
    return [normalize_token(part) for part in command]


def command_entry(
    name: str,
    purpose: str,
    command: list[str],
    *,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    return {
        "name": name,
        "purpose": purpose,
        "cwd": str(ROOT),
        "env": env or {},
        "command": command,
    }


def print_command_plan(plan: dict[str, Any], format_name: str) -> None:
    if format_name == "json":
        print(json.dumps(plan, indent=2, sort_keys=True))
        return
    for entry in plan["commands"]:
        env = " ".join(f"{key}={shlex.quote(value)}" for key, value in entry["env"].items())
        command = " ".join(shlex.quote(part) for part in entry["command"])
        print(f"# {entry['name']}: {entry['purpose']}")
        print(f"{env + ' ' if env else ''}{command}")


def validate_input_freeze(input_freeze: dict[str, Any], run_status: str) -> None:
    shared_require_paths_exist(
        {
            "geodata_manifest_path": require_text(input_freeze.get("geodata_manifest_path"), "input_freeze.geodata_manifest_path"),
            "source_scenario_policy_path": require_text(
                input_freeze.get("source_scenario_policy_path"),
                "input_freeze.source_scenario_policy_path",
            ),
        },
        PilotRunError,
        root=ROOT,
        label_prefix="input_freeze",
    )
    freeze_status = require_text(input_freeze.get("freeze_status"), "input_freeze.freeze_status")
    if run_status == "template_not_run":
        require(freeze_status == "not_frozen", "template run freeze_status must be not_frozen")
        return
    if run_status in NO_GO_RUN_STATUSES:
        require(
            freeze_status in {"blocked_missing_processed_dem", "frozen"},
            "no-go or inconclusive pilot runs must set freeze_status to blocked_missing_processed_dem or frozen",
        )
        for key in ("benchmark_case_path", "terrain_metadata_path", "source_zone_metadata_path", "scenario_table_path"):
            value = input_freeze.get(key)
            require(value is None or isinstance(value, str), f"input_freeze.{key} must be null or a string")
        require_text(input_freeze.get("map_product_id"), "input_freeze.map_product_id")
        return
    require(freeze_status == "frozen", "non-template pilot runs must set freeze_status to frozen")
    for key in (
        "benchmark_case_path",
        "terrain_metadata_path",
        "source_zone_metadata_path",
        "scenario_table_path",
        "map_product_id",
    ):
        require_text(input_freeze.get(key), f"input_freeze.{key}")


def validate_physics_freeze(physics: dict[str, Any], run_status: str) -> None:
    require(physics.get("defaults_changed") is False, "physics_freeze.defaults_changed must be false")
    require(
        physics.get("simulator_behavior_changed") is False,
        "physics_freeze.simulator_behavior_changed must be false",
    )
    require_text(physics.get("contact_model"), "physics_freeze.contact_model")
    require_text(physics.get("soil_interaction_model"), "physics_freeze.soil_interaction_model")
    require_text(physics.get("roughness_model"), "physics_freeze.roughness_model")
    require(
        physics.get("tuning_after_output_review_allowed") is False,
        "tuning_after_output_review_allowed must be false",
    )
    status = require_text(physics.get("parameters_status"), "physics_freeze.parameters_status")
    if run_status != "template_not_run":
        require(status == "frozen", "non-template pilot runs must freeze physics parameters")


def validate_sampling_plan(sampling: dict[str, Any], run_status: str) -> None:
    require(
        sampling.get("release_cell_policy") == "deterministic_grid",
        "sampling_plan.release_cell_policy must be deterministic_grid",
    )
    require(
        sampling.get("scenario_weight_semantics") == "conditional_sampling_only",
        "sampling_plan.scenario_weight_semantics must be conditional_sampling_only",
    )
    require(
        sampling.get("reducer_mode") == "deterministic_local_reducer",
        "sampling_plan.reducer_mode must be deterministic_local_reducer",
    )
    if run_status == "template_not_run":
        return
    require_int(sampling.get("random_seed"), "sampling_plan.random_seed", minimum=0)
    gate_count = require_int(
        sampling.get("gate_run_trajectories_per_release_zone"),
        "sampling_plan.gate_run_trajectories_per_release_zone",
        minimum=1,
    )
    target_count = require_int(
        sampling.get("target_trajectories_per_release_zone"),
        "sampling_plan.target_trajectories_per_release_zone",
        minimum=gate_count,
    )
    _ = target_count
    require_int(sampling.get("worker_count"), "sampling_plan.worker_count", minimum=1)


def validate_hazard_output_plan(plan: dict[str, Any], pilot_id: str, run_status: str) -> None:
    require(
        plan.get("probability_mode") == "sampling_weighted_conditional",
        "hazard_output_plan.probability_mode must be sampling_weighted_conditional",
    )
    require(
        plan.get("normalization_scope") == "conditioned_on_filter",
        "hazard_output_plan.normalization_scope must be conditioned_on_filter",
    )
    require(plan.get("conditional_curve_table_required") is True, "conditional curve table must be required")
    require(plan.get("geotiff_required") is True, "GeoTIFF output must be required")
    require(plan.get("pilot_gis_package_required") is True, "pilot GIS package must be required")
    require(plan.get("explicit_grid_required") is True, "explicit grid must be required")
    require(plan.get("generated_outputs_committed") is False, "generated_outputs_committed must be false")
    conditional_curve_export = plan.get("conditional_curve_export")
    if conditional_curve_export is not None:
        require(
            conditional_curve_export in SUPPORTED_CONDITIONAL_CURVE_EXPORT_MODES,
            "hazard_output_plan.conditional_curve_export must be full or summary-only",
        )
    grid_csv_export = plan.get("grid_csv_export")
    if grid_csv_export is not None:
        require(
            grid_csv_export in SUPPORTED_GRID_CSV_EXPORT_MODES,
            "hazard_output_plan.grid_csv_export must be full or none",
        )
    if run_status != "template_not_run":
        trajectory_workers = plan.get("trajectory_workers")
        if trajectory_workers is not None:
            require_int(trajectory_workers, "hazard_output_plan.trajectory_workers", minimum=1)
    for key in ("kinetic_energy_exceedance_j", "jump_height_exceedance_m", "velocity_exceedance_mps"):
        values = require_list(plan.get(key), f"hazard_output_plan.{key}")
        for value in values:
            number = require_number(value, f"hazard_output_plan.{key}[]")
            require(math.isfinite(number) and number >= 0.0, f"{key} thresholds must be finite and nonnegative")
    explicit_grid = require_mapping(plan.get("explicit_grid"), "hazard_output_plan.explicit_grid")
    if run_status != "template_not_run":
        for key in ("xmin", "ymin", "cell_size_m"):
            require_number(explicit_grid.get(key), f"explicit_grid.{key}")
        for key in ("ncols", "nrows"):
            require_int(explicit_grid.get(key), f"explicit_grid.{key}", minimum=1)
        require(any(plan[key] for key in ("kinetic_energy_exceedance_j", "jump_height_exceedance_m", "velocity_exceedance_mps")), "non-template pilot runs must define at least one intensity threshold")
    output_roots = require_mapping(plan.get("output_roots"), "hazard_output_plan.output_roots")
    for key in ("validation_results", "hazard_results"):
        value = require_text(output_roots.get(key), f"hazard_output_plan.output_roots.{key}")
        require(pilot_id in value, f"{key} output root should include pilot_id {pilot_id}")
    require(
        str(output_roots["hazard_results"]).startswith("hazard/results/"),
        "hazard_results must stay under hazard/results/",
    )


def validate_workflow_gates(gates: dict[str, Any], run_status: str) -> None:
    for key, value in gates.items():
        status = require_text(value, f"workflow_gates.{key}")
        require(status in SUPPORTED_GATE_STATUSES, f"workflow_gates.{key} must be one of {sorted(SUPPORTED_GATE_STATUSES)}")
    if run_status in {"gate_run_completed", "target_run_completed"}:
        required_pass = (
            "geodata_manifest_validated",
            "source_scenario_policy_validated",
            "benchmark_case_frozen",
            "small_gate_run_completed",
            "conditional_curves_generated",
            "gis_package_generated",
            "output_budget_recorded",
        )
        for key in required_pass:
            require(gates.get(key) == "pass", f"completed pilot runs require workflow_gates.{key}: pass")


def validate_output_budget(budget: dict[str, Any], run_status: str) -> None:
    require_int(budget.get("max_committed_generated_files"), "output_budget.max_committed_generated_files", minimum=0)
    require(
        budget.get("max_committed_generated_files") == 0,
        "public pilot generated outputs must not be committed by default",
    )
    metrics = set(require_list(budget.get("required_recorded_metrics"), "output_budget.required_recorded_metrics"))
    missing = REQUIRED_BUDGET_METRICS - metrics
    require(not missing, f"output_budget.required_recorded_metrics omits {sorted(missing)}")
    if run_status != "template_not_run":
        require_int(budget.get("max_private_file_count"), "output_budget.max_private_file_count", minimum=1)
        require_int(budget.get("max_private_total_bytes"), "output_budget.max_private_total_bytes", minimum=1)


def validate_run_evidence(evidence: dict[str, Any], run_status: str) -> None:
    evidence_status = require_text(evidence.get("evidence_status"), "run_evidence.evidence_status")
    require(
        evidence_status in SUPPORTED_EVIDENCE_STATUSES,
        f"run_evidence.evidence_status must be one of {sorted(SUPPORTED_EVIDENCE_STATUSES)}",
    )

    if run_status in COMPLETED_RUN_STATUSES:
        require(
            evidence_status == run_status,
            f"completed run_status {run_status} requires matching run_evidence.evidence_status",
        )
        validate_completed_run_evidence(evidence)
        return

    if run_status in {"template_not_run", "predeclared_ready"}:
        require(evidence_status == "not_run", f"{run_status} manifests must keep run_evidence.evidence_status not_run")
        for key in set(REQUIRED_EVIDENCE_PATHS) | REQUIRED_BUDGET_METRICS:
            require(evidence.get(key) is None, f"{run_status} manifests must keep run_evidence.{key} null")
        checksums = require_mapping(evidence.get("artifact_checksums"), "run_evidence.artifact_checksums")
        for key in REQUIRED_ARTIFACT_CHECKSUMS:
            require(checksums.get(key) is None, f"{run_status} manifests must keep run_evidence.artifact_checksums.{key} null")
        diagnostics = require_mapping(
            evidence.get("convergence_diagnostics"),
            "run_evidence.convergence_diagnostics",
        )
        require(
            diagnostics.get("status") == "not_run",
            f"{run_status} manifests must keep convergence diagnostics not_run",
        )
    elif run_status in NO_GO_RUN_STATUSES:
        require(evidence_status == run_status.replace("_", "-"), f"{run_status} manifests must use matching run_evidence.evidence_status")
        for key in set(REQUIRED_EVIDENCE_PATHS) | REQUIRED_BUDGET_METRICS:
            require(evidence.get(key) is None, f"{run_status} manifests must keep run_evidence.{key} null")
        checksums = require_mapping(evidence.get("artifact_checksums"), "run_evidence.artifact_checksums")
        for key in REQUIRED_ARTIFACT_CHECKSUMS:
            require(checksums.get(key) is None, f"{run_status} manifests must keep run_evidence.artifact_checksums.{key} null")
        diagnostics = require_mapping(
            evidence.get("convergence_diagnostics"),
            "run_evidence.convergence_diagnostics",
        )
        status = require_text(diagnostics.get("status"), "run_evidence.convergence_diagnostics.status")
        require(status in {"no-go", "inconclusive"}, f"{run_status} convergence status must be no-go or inconclusive")
        notes = require_list(diagnostics.get("notes"), "run_evidence.convergence_diagnostics.notes")
        require(notes, f"{run_status} convergence diagnostics notes must not be empty")


def validate_completed_run_evidence(evidence: dict[str, Any]) -> None:
    validation_manifest_path = require_text(
        evidence.get("validation_manifest_path"),
        "run_evidence.validation_manifest_path",
    )
    hazard_manifest_path = require_text(evidence.get("hazard_manifest_path"), "run_evidence.hazard_manifest_path")
    conditional_curve_table_path = require_text(
        evidence.get("conditional_curve_table_path"),
        "run_evidence.conditional_curve_table_path",
    )
    map_package_manifest_path = require_text(
        evidence.get("map_package_manifest_path"),
        "run_evidence.map_package_manifest_path",
    )
    pilot_gis_package_manifest_path = require_text(
        evidence.get("pilot_gis_package_manifest_path"),
        "run_evidence.pilot_gis_package_manifest_path",
    )
    reducer_chunk_manifest_dir = require_text(
        evidence.get("reducer_chunk_manifest_dir"),
        "run_evidence.reducer_chunk_manifest_dir",
    )
    require(
        resolve_repo_path(ROOT, validation_manifest_path).is_relative_to(ROOT / "validation"),
        "run_evidence.validation_manifest_path must stay under validation/",
    )
    for key in (
        "hazard_manifest_path",
        "conditional_curve_table_path",
        "map_package_manifest_path",
        "pilot_gis_package_manifest_path",
        "reducer_chunk_manifest_dir",
    ):
        require(
            resolve_repo_path(
                ROOT,
                {
                    "hazard_manifest_path": hazard_manifest_path,
                    "conditional_curve_table_path": conditional_curve_table_path,
                    "map_package_manifest_path": map_package_manifest_path,
                    "pilot_gis_package_manifest_path": pilot_gis_package_manifest_path,
                    "reducer_chunk_manifest_dir": reducer_chunk_manifest_dir,
                }[key],
            ).is_relative_to(ROOT / "hazard/results"),
            f"run_evidence.{key} must stay under hazard/results/",
        )

    for key in ("runtime_seconds", "memory_peak_mb"):
        value = require_number(evidence.get(key), f"run_evidence.{key}")
        require(math.isfinite(value) and value >= 0.0, f"run_evidence.{key} must be finite and nonnegative")
    for key in ("output_file_count", "output_total_bytes", "trajectory_count", "release_cell_count"):
        require_int(evidence.get(key), f"run_evidence.{key}", minimum=1)

    diagnostics = require_mapping(
        evidence.get("convergence_diagnostics"),
        "run_evidence.convergence_diagnostics",
    )
    status = require_text(diagnostics.get("status"), "run_evidence.convergence_diagnostics.status")
    require(
        status in {"pass", "no-go", "inconclusive"},
        "completed run_evidence.convergence_diagnostics.status must be pass, no-go, or inconclusive",
    )
    notes = require_list(diagnostics.get("notes"), "run_evidence.convergence_diagnostics.notes")
    require(notes, "completed run_evidence.convergence_diagnostics.notes must not be empty")
    for index, note in enumerate(notes):
        require_text(note, f"run_evidence.convergence_diagnostics.notes[{index}]")

    checksums = require_mapping(evidence.get("artifact_checksums"), "run_evidence.artifact_checksums")
    shared_require_checksum_fields(
        checksums,
        REQUIRED_ARTIFACT_CHECKSUMS,
        PilotRunError,
        label_prefix="run_evidence.artifact_checksums",
    )
    shared_require_checksum_fields(
        checksums,
        OPTIONAL_ARTIFACT_CHECKSUMS,
        PilotRunError,
        label_prefix="run_evidence.artifact_checksums",
        allow_none=True,
    )


def validate_selected_gate_contract(
    *,
    run_id: str,
    pilot_id: str,
    run_status: str,
    input_freeze: dict[str, Any],
    run_evidence: dict[str, Any],
    report_plan: dict[str, Any],
) -> None:
    if run_id != SELECTED_GATE_RUN_ID:
        return
    require(
        pilot_id == SELECTED_PILOT_ID,
        f"selected gate run {run_id} requires pilot_id {SELECTED_PILOT_ID}",
    )
    require(
        run_status == "gate_run_completed",
        f"selected gate run {run_id} requires run_status gate_run_completed",
    )
    require(
        report_plan.get("report_path") == SELECTED_REPORT_PATH,
        f"selected gate run {run_id} requires report {SELECTED_REPORT_PATH}",
    )
    require(
        report_plan.get("current_classification") == "inconclusive",
        f"selected gate run {run_id} requires report_plan.current_classification inconclusive",
    )
    require(
        run_evidence.get("evidence_status") == "gate_run_completed",
        f"selected gate run {run_id} requires run_evidence.evidence_status gate_run_completed",
    )
    report_path = require_text(report_plan.get("report_path"), "report_plan.report_path")
    report_file = shared_require_paths_exist(
        {"report_path": report_path},
        PilotRunError,
        root=ROOT,
        label_prefix="report_plan",
    )["report_path"]
    try:
        report_text = report_file.read_text(encoding="utf-8")
    except OSError as exc:
        raise PilotRunError(
            f"selected gate run {run_id} requires report {SELECTED_REPORT_PATH} to be readable: {exc}"
        ) from exc
    require(
        f"Run id: `{run_id}`" in report_text,
        f"selected gate run {run_id} requires the selected report to reference the same run id",
    )
    require(
        input_freeze.get("map_product_id") == run_id,
        f"selected gate run {run_id} requires map_product_id to match run_id",
    )
    checksums = require_mapping(run_evidence.get("artifact_checksums"), "run_evidence.artifact_checksums")
    shared_require_checksum_fields(
        checksums,
        REQUIRED_ARTIFACT_CHECKSUMS + OPTIONAL_ARTIFACT_CHECKSUMS,
        PilotRunError,
        label_prefix="run_evidence.artifact_checksums",
    )
    report_checksums = parse_report_artifact_checksums(report_text)
    for key, label in SELECTED_REPORT_ARTIFACT_CHECKSUMS:
        selected_checksum = require_text(checksums.get(key), f"run_evidence.artifact_checksums.{key}")
        report_checksum = report_checksums.get(normalize_report_artifact_label(label))
        require(
            report_checksum is not None,
            f"selected gate run {run_id} requires report checksum row for {label}",
        )
        require(
            report_checksum == selected_checksum,
            f"selected gate run {run_id} report checksum mismatch for {label}: freeze {selected_checksum}, report {report_checksum}",
        )

    for key, root in SELECTED_REQUIRED_PATH_ROOTS.items():
        require(
            key in run_evidence,
            f"selected gate run {run_id} requires run_evidence.{key}",
        )
        value = require_text(run_evidence.get(key), f"run_evidence.{key}")
        require(
            value.startswith(root),
            f"selected gate run {run_id} requires run_evidence.{key} under {root}",
        )
    require(
        run_evidence.get("convergence_diagnostics", {}).get("notes"),
        f"selected gate run {run_id} requires non-empty convergence diagnostics notes",
    )

    evidence_convergence = require_mapping(
        run_evidence.get("convergence_diagnostics"),
        "run_evidence.convergence_diagnostics",
    )
    notes = require_list(
        evidence_convergence.get("notes"),
        "run_evidence.convergence_diagnostics.notes",
    )
    require(
        all(isinstance(note, str) and note.strip() for note in notes),
        f"selected gate run {run_id} convergence notes must all be non-empty strings",
    )


def normalize_report_artifact_label(label: str) -> str:
    return " ".join(label.strip().lower().split())


def parse_report_artifact_checksums(report_text: str) -> dict[str, str]:
    artifact_checksums: dict[str, str] = {}
    checksum_row = re.compile(r"^\|\s*(?P<artifact>[^|]+)\s*\|\s*`(?P<sha>[0-9a-f]{64})`\s*\|$")
    for line in report_text.splitlines():
        match = checksum_row.match(line.strip())
        if match is None:
            continue
        artifact = normalize_report_artifact_label(match.group("artifact"))
        artifact_checksums[artifact] = match.group("sha")
    return artifact_checksums


def validate_report_plan(report: dict[str, Any], run_status: str) -> None:
    path = require_text(report.get("report_path"), "report_plan.report_path")
    require(path.startswith("docs/"), "report_plan.report_path must stay under docs/")
    allowed = set(require_list(report.get("allowed_classifications"), "report_plan.allowed_classifications"))
    require({"pass", "no-go", "inconclusive"} <= allowed, "report_plan.allowed_classifications must include pass, no-go, and inconclusive")
    classification = require_text(report.get("current_classification"), "report_plan.current_classification")
    if run_status == "template_not_run":
        require(classification == "not_run", "template report classification must be not_run")
    else:
        require(classification in allowed, "non-template report classification must be pass, no-go, or inconclusive")


def validate_claim_boundary(boundary: dict[str, Any]) -> None:
    allowed = set(require_list(boundary.get("current_allowed_products"), "claim_boundary.current_allowed_products"))
    require("conditional_intensity_exceedance" in allowed, "claim_boundary must allow conditional_intensity_exceedance")
    future = set(require_list(boundary.get("future_products"), "claim_boundary.future_products"))
    require("annual_intensity_frequency" in future, "claim_boundary must reserve future annual_intensity_frequency")
    unsupported = set(require_list(boundary.get("unsupported_current_claims"), "claim_boundary.unsupported_current_claims"))
    missing = REQUIRED_UNSUPPORTED_CLAIMS - unsupported
    require(not missing, f"claim_boundary unsupported_current_claims omits {sorted(missing)}")
    notes = "\n".join(str(note).lower() for note in require_list(boundary.get("notes"), "claim_boundary.notes"))
    require("not validation evidence" in notes, "claim_boundary notes must keep input provenance out of validation evidence")
    require("sampling-weighted conditional" in notes, "claim_boundary notes must keep current products conditional")
    shared_scan_text_for_misleading_claims(
        boundary,
        require_fn=require,
        patterns=(
            re.compile(r"\breturn[- ]?period\b", re.IGNORECASE),
            re.compile(r"\brisk[- ]?map\b", re.IGNORECASE),
            re.compile(r"\boperational(?:ly)?\s+(?:approved|validated|ready|hazard)\b", re.IGNORECASE),
            re.compile(r"\bannual(?:ized)?\s+(?:frequency|probability|rate)\b", re.IGNORECASE),
        ),
        skip_keys=(),
        allow_markers=(
            "unsupported",
            "not_",
            "no_",
            "no ",
            "without",
            "defer",
            "future",
            "out of scope",
            "remain",
            "blocked",
            "missing",
        ),
    )


def validate_no_go_blocker(blocker: dict[str, Any]) -> None:
    require_text(blocker.get("blocker_id"), "no_go_blocker.blocker_id")
    require_text(blocker.get("status"), "no_go_blocker.status")
    require_text(blocker.get("classification"), "no_go_blocker.classification")
    require(blocker["classification"] == "no-go", "no_go_blocker.classification must be no-go")
    missing_paths = require_list(blocker.get("missing_paths"), "no_go_blocker.missing_paths")
    require(missing_paths, "no_go_blocker.missing_paths must not be empty")
    for index, value in enumerate(missing_paths):
        require_text(value, f"no_go_blocker.missing_paths[{index}]")
    commands = require_list(blocker.get("recovery_commands"), "no_go_blocker.recovery_commands")
    require(commands, "no_go_blocker.recovery_commands must not be empty")
    for index, value in enumerate(commands):
        require_text(value, f"no_go_blocker.recovery_commands[{index}]")
    require_text(blocker.get("evidence_output_dir"), "no_go_blocker.evidence_output_dir")
    notes = "\n".join(str(note).lower() for note in require_list(blocker.get("notes"), "no_go_blocker.notes"))
    require("not a model result" in notes, "no_go_blocker.notes must say the no-go is not a model result")


if __name__ == "__main__":
    raise SystemExit(main())
