#!/usr/bin/env python3
"""Validate the Phase 6 public real-site conditional pilot run-freeze contract."""

from __future__ import annotations

import argparse
import json
import math
import re
import shlex
import sys
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except ImportError as exc:  # pragma: no cover - environment setup.
    raise SystemExit("PyYAML is required; install with `python3 -m pip install PyYAML`") from exc


ROOT = Path(__file__).resolve().parents[1]
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
HEX_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
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


class PilotRunError(ValueError):
    """User-facing pilot run validation error."""


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
        manifest = read_yaml(args.run_manifest)
        validate_pilot_run(manifest, args.run_manifest)
        if args.print_command_plan:
            plan = build_command_plan(manifest)
            print_command_plan(plan, args.format)
        else:
            print(f"public real-site conditional pilot run contract is valid: {args.run_manifest}")
    except PilotRunError as exc:
        print(f"pilot run validation error: {exc}", file=sys.stderr)
        return 2
    return 0


def read_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - path context matters for users.
        raise PilotRunError(f"failed to read {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise PilotRunError(f"run manifest must contain a YAML mapping: {path}")
    return data


def validate_pilot_run(manifest: dict[str, Any], manifest_path: Path | None = None) -> None:
    require(
        manifest.get("schema_version") == "public_real_site_conditional_pilot_run_v1",
        "schema_version must be public_real_site_conditional_pilot_run_v1",
    )
    pilot_id = require_text(manifest.get("pilot_id"), "pilot_id")
    require_text(manifest.get("run_id"), "run_id")
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
    validate_run_evidence(require_mapping(manifest.get("run_evidence"), "run_evidence"), run_status)
    validate_report_plan(require_mapping(manifest.get("report_plan"), "report_plan"), run_status)
    validate_claim_boundary(require_mapping(manifest.get("claim_boundary"), "claim_boundary"))

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

    input_freeze = require_mapping(manifest["input_freeze"], "input_freeze")
    sampling = require_mapping(manifest["sampling_plan"], "sampling_plan")
    hazard_plan = require_mapping(manifest["hazard_output_plan"], "hazard_output_plan")
    output_roots = require_mapping(hazard_plan["output_roots"], "hazard_output_plan.output_roots")
    grid = require_mapping(hazard_plan["explicit_grid"], "hazard_output_plan.explicit_grid")
    benchmark_case_path = require_text(input_freeze["benchmark_case_path"], "input_freeze.benchmark_case_path")
    benchmark_case = read_yaml(repo_path(benchmark_case_path))
    outputs = require_mapping(benchmark_case.get("outputs"), "benchmark_case.outputs")
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
            command.extend([flag, str(outputs[output_key])])
    for threshold in hazard_plan["kinetic_energy_exceedance_j"]:
        command.extend(["--kinetic-energy-exceedance-j", str(threshold)])
    for threshold in hazard_plan["jump_height_exceedance_m"]:
        command.extend(["--jump-height-exceedance-m", str(threshold)])
    for threshold in hazard_plan["velocity_exceedance_mps"]:
        command.extend(["--velocity-exceedance-mps", str(threshold)])
    return command


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
    for key in ("geodata_manifest_path", "source_scenario_policy_path"):
        path = repo_path(require_text(input_freeze.get(key), f"input_freeze.{key}"))
        require(path.exists(), f"input_freeze.{key} does not exist: {path}")
    freeze_status = require_text(input_freeze.get("freeze_status"), "input_freeze.freeze_status")
    if run_status == "template_not_run":
        require(freeze_status == "not_frozen", "template run freeze_status must be not_frozen")
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
    for key in (
        "benchmark_case_path",
        "terrain_metadata_path",
        "source_zone_metadata_path",
        "scenario_table_path",
    ):
        path = repo_path(str(input_freeze[key]))
        require(path.exists(), f"input_freeze.{key} does not exist: {path}")


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


def validate_completed_run_evidence(evidence: dict[str, Any]) -> None:
    validation_manifest_path = require_text(
        evidence.get("validation_manifest_path"),
        "run_evidence.validation_manifest_path",
    )
    require(
        validation_manifest_path.startswith("validation/"),
        "run_evidence.validation_manifest_path must stay under validation/",
    )
    for key in (
        "hazard_manifest_path",
        "conditional_curve_table_path",
        "map_package_manifest_path",
        "pilot_gis_package_manifest_path",
        "reducer_chunk_manifest_dir",
    ):
        value = require_text(evidence.get(key), f"run_evidence.{key}")
        require(value.startswith("hazard/results/"), f"run_evidence.{key} must stay under hazard/results/")

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
    for key in REQUIRED_ARTIFACT_CHECKSUMS:
        checksum = require_text(checksums.get(key), f"run_evidence.artifact_checksums.{key}")
        require(
            HEX_SHA256_RE.fullmatch(checksum) is not None,
            f"run_evidence.artifact_checksums.{key} must be a lowercase SHA-256 hex digest",
        )


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


def repo_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def require_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise PilotRunError(f"{label} must be a mapping")
    return value


def require_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise PilotRunError(f"{label} must be a list")
    return value


def require_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PilotRunError(f"{label} must be a non-empty string")
    return value


def require_number(value: Any, label: str) -> float:
    if not isinstance(value, (int, float)):
        raise PilotRunError(f"{label} must be numeric")
    return float(value)


def require_int(value: Any, label: str, *, minimum: int) -> int:
    if not isinstance(value, int):
        raise PilotRunError(f"{label} must be an integer")
    require(value >= minimum, f"{label} must be at least {minimum}")
    return value


def require(condition: bool, message: str) -> None:
    if not condition:
        raise PilotRunError(message)


if __name__ == "__main__":
    raise SystemExit(main())
