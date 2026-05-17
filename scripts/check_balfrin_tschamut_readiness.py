#!/usr/bin/env python3
"""Read-only balfrin readiness checker for the Tschamut public conditional pilot."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except ImportError as exc:  # pragma: no cover - environment setup path.
    raise SystemExit("PyYAML is required. Run this script with `PYENV_VERSION=system uv run python ...`; CI may use `requirements-tools.txt`") from exc

ROOT = Path(__file__).resolve().parents[1]

default_run_manifest = ROOT / "validation/pilot_runs/tschamut_public_conditional_pilot_gate_v1.yaml"

STATUS_READY = "ready_for_balfrin_target_gate"
STATUS_BLOCKED = "blocked_for_balfrin_readiness"
CONDITIONAL_PILOT_SCHEMA_VERSION = "public_real_site_conditional_pilot_run_v1"
BALFRIN_CONTRACT_SCHEMA_VERSION = "balfrin_single_release_zone_pilot_contract_v1"
EXPECTED_BALFRIN_COMMAND_IDS = (
    "summarize_contract_json",
    "summarize_contract_text",
    "dry_run_case_plan",
    "post_run_gate_preview",
)


def _to_repo_path(repo_root: Path, value: str) -> Path:
    path = Path(str(value).strip().replace("\\", "/"))
    if path.is_absolute():
        return path
    return (repo_root / path).resolve()


def _first_strict_mapping(value: Any, context: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{context} must be a YAML mapping")
    return value


def _load_module(path: Path, module_name: str) -> Any:
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _add_check(
    checks: list[dict[str, Any]],
    *,
    name: str,
    status: str,
    required: bool,
    message: str,
    path: str | None = None,
) -> None:
    checks.append(
        {
            "name": name,
            "status": status,
            "required": required,
            "message": message,
            "path": path,
        }
    )


def _read_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - file context matters for users.
        raise ValueError(f"failed to read YAML: {path}: {exc}") from exc
    if data is None:
        raise ValueError(f"manifest is empty: {path}")
    if not isinstance(data, dict):
        raise ValueError(f"manifest must be YAML mapping: {path}")
    return data


def _tool_probe(binary: str) -> dict[str, Any]:
    exe = shutil.which(binary)
    tool = {"binary": binary, "required": binary != "qgis", "available": False, "version": None, "path": exe}
    if exe is None:
        return tool

    args = [exe, "--version"]
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:  # noqa: BLE001
        tool["error"] = str(exc)
        return tool

    if result.returncode == 0:
        output = (result.stdout or result.stderr or "").strip().splitlines()
        tool["available"] = True
        tool["version"] = output[0] if output else ""
    else:
        tool["error"] = f"command failed with code {result.returncode}"
    return tool


def _git_info(repo_root: Path) -> dict[str, Any]:
    if not (repo_root / ".git").exists():
        return {"status": "missing", "branch": None, "commit": None}

    def run_git(*args: str) -> str:
        out = subprocess.run(
            ["git", *args],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        return out

    info: dict[str, Any] = {"status": "ok", "branch": None, "commit": None}
    try:
        branch = run_git("rev-parse", "--abbrev-ref", "HEAD")
        commit = run_git("rev-parse", "HEAD")
    except subprocess.CalledProcessError as exc:
        info["status"] = "error"
        info["error"] = str(exc)
        return info
    except FileNotFoundError as exc:
        info["status"] = "missing_binary"
        info["error"] = str(exc)
        return info
    info["branch"] = branch
    info["commit"] = commit
    if not info["branch"] or not info["commit"]:
        info["status"] = "error"
    return info


def _is_writable_dir(path: Path) -> bool:
    if path.exists():
        check_path = path if path.is_dir() else path.parent
    else:
        check_path = path.parent
    return check_path.exists() and check_path.is_dir() and os.access(check_path, os.W_OK | os.X_OK)


def _collect_processed_inputs_checks(repo_root: Path, checks: list[dict[str, Any]], geodata_manifest_path: Path) -> None:
    try:
        geodata_manifest = _read_yaml(geodata_manifest_path)
    except (OSError, ValueError) as exc:
        _add_check(
            checks,
            name="processed_dem_inputs.manifest_read",
            status="fail",
            required=True,
            message=f"cannot read geodata manifest: {exc}",
            path=str(geodata_manifest_path),
        )
        return

    required_datasets = geodata_manifest.get("required_datasets")
    if not isinstance(required_datasets, list) or not required_datasets:
        _add_check(
            checks,
            name="processed_dem_inputs.missing_dataset_entry",
            status="warn",
            required=False,
            message="geodata manifest has no required_datasets block to infer processed DEM metadata paths",
            path=str(geodata_manifest_path),
        )
        return

    inferred_count = 0
    for idx, dataset in enumerate(required_datasets):
        if not isinstance(dataset, dict):
            continue
        outputs = dataset.get("processed_outputs")
        if not isinstance(outputs, list):
            continue
        for item in outputs:
            if not isinstance(item, dict):
                continue
            dem_path = item.get("path")
            metadata_path = item.get("metadata_path")
            if not isinstance(dem_path, str) or not isinstance(metadata_path, str):
                continue
            inferred_count += 1
            dem = _to_repo_path(repo_root, dem_path)
            meta = _to_repo_path(repo_root, metadata_path)
            if dem.exists():
                _add_check(
                    checks,
                    name=f"processed_dem_inputs[{idx}].dem",
                    status="pass",
                    required=True,
                    message="processed DEM path exists",
                    path=str(dem),
                )
            else:
                _add_check(
                    checks,
                    name=f"processed_dem_inputs[{idx}].dem",
                    status="fail",
                    required=True,
                    message="processed DEM path is missing",
                    path=str(dem),
                )

            if meta.exists():
                _add_check(
                    checks,
                    name=f"processed_dem_inputs[{idx}].metadata",
                    status="pass",
                    required=True,
                    message="terrain metadata path exists",
                    path=str(meta),
                )
            else:
                _add_check(
                    checks,
                    name=f"processed_dem_inputs[{idx}].metadata",
                    status="fail",
                    required=True,
                    message="terrain metadata path is missing",
                    path=str(meta),
                )

    if inferred_count == 0:
        _add_check(
            checks,
            name="processed_dem_inputs.none",
            status="warn",
            required=False,
            message="No processed DEM entries were found in geodata manifest",
            path=str(geodata_manifest_path),
        )


def _collect_command_plan_checks(
    repo_root: Path,
    checks: list[dict[str, Any]],
    plan: dict[str, Any],
) -> None:
    commands = plan.get("commands")
    if not isinstance(commands, list):
        _add_check(
            checks,
            name="command_plan.commands",
            status="fail",
            required=True,
            message="command plan must include a commands array",
            path=None,
        )
        return

    required_file_flags = {
        "run_validation_gate": ["--case"],
        "build_conditional_hazard_layers": ["--case", "--source-zone-metadata-path", "--scenario-table-path"],
    }
    writable_dir_flags = {
        "build_conditional_hazard_layers": [
            "--output-dir",
            "--diagnostics",
            "--trajectory",
            "--ensemble-trajectories-dir",
            "--deposition",
            "--ensemble-impact-events-dir",
            "--map-package-manifest-json",
            "--pilot-gis-package-manifest-json",
        ]
    }
    required_commands = {
        "validate_geodata_manifest",
        "validate_source_scenario_policy",
        "run_validation_gate",
        "build_conditional_hazard_layers",
    }
    found_commands: set[str] = set()

    for entry in commands:
        if not isinstance(entry, dict):
            continue
        name = entry.get("name", "")
        found_commands.add(name)
        command = entry.get("command")
        if not isinstance(command, list):
            _add_check(
                checks,
                name=f"command_plan[{name}].shape",
                status="warn",
                required=False,
                message="command plan entry missing command array",
                path=None,
            )
            continue

        tokens = [str(x) for x in command]
        if name in {"validate_geodata_manifest", "validate_source_scenario_policy"}:
            if not tokens:
                _add_check(
                    checks,
                    name=f"command_plan[{name}].input",
                    status="fail",
                    required=True,
                    message=f"{name} has no command arguments",
                    path=name,
                )
                continue
            input_path = _to_repo_path(repo_root, tokens[-1])
            if input_path.exists():
                _add_check(
                    checks,
                    name=f"command_plan[{name}].input",
                    status="pass",
                    required=True,
                    message=f"{name} input exists",
                    path=str(input_path),
                )
            else:
                _add_check(
                    checks,
                    name=f"command_plan[{name}].input",
                    status="fail",
                    required=True,
                    message=f"{name} input is missing",
                    path=str(input_path),
                )
            continue

        for token in required_file_flags.get(name, []):
            token_index = -1
            for i, value in enumerate(tokens):
                if value == token:
                    token_index = i
                    break
            if token_index < 0:
                _add_check(
                    checks,
                    name=f"command_plan[{name}].{token}.missing",
                    status="warn",
                    required=False,
                    message=f"{name} is missing expected input flag {token}",
                    path=None,
                )
                continue
            if token_index + 1 >= len(tokens):
                _add_check(
                    checks,
                    name=f"command_plan[{name}].{token}.malformed",
                    status="fail",
                    required=True,
                    message=f"command argument for {token} is missing",
                    path=name,
                )
                continue
            path_value = _to_repo_path(repo_root, str(tokens[token_index + 1]))
            if path_value.exists():
                _add_check(
                    checks,
                    name=f"command_plan[{name}].{token}",
                    status="pass",
                    required=True,
                    message=f"command input exists: {token}",
                    path=str(path_value),
                )
            else:
                _add_check(
                    checks,
                    name=f"command_plan[{name}].{token}",
                    status="fail",
                    required=True,
                    message=f"command input is missing: {token}",
                    path=str(path_value),
                )

        for token in writable_dir_flags.get(name, []):
            token_index = -1
            for i, value in enumerate(tokens):
                if value == token:
                    token_index = i
                    break
            if token_index < 0:
                continue
            if token_index + 1 >= len(tokens):
                _add_check(
                    checks,
                    name=f"command_plan[{name}].{token}.malformed",
                    status="fail",
                    required=True,
                    message=f"command argument for {token} is missing",
                    path=name,
                )
                continue
            path_value = _to_repo_path(repo_root, str(tokens[token_index + 1]))
            if _is_writable_dir(path_value):
                _add_check(
                    checks,
                    name=f"command_plan[{name}].{token}",
                    status="pass",
                    required=True,
                    message=f"command output location is writable: {token}",
                    path=str(path_value),
                )
            else:
                _add_check(
                    checks,
                    name=f"command_plan[{name}].{token}",
                    status="fail",
                    required=True,
                    message=f"command output location is not writable: {token}",
                    path=str(path_value),
                )

    missing_commands = sorted(required_commands - found_commands)
    for missing_command in missing_commands:
        _add_check(
            checks,
            name=f"command_plan[{missing_command}].missing",
            status="fail",
            required=True,
            message=f"command plan is missing required command '{missing_command}'",
            path=None,
        )


def _collect_root_checks(repo_root: Path, checks: list[dict[str, Any]], run_manifest: dict[str, Any]) -> None:
    input_freeze = _first_strict_mapping(run_manifest.get("input_freeze"), "input_freeze")
    hazard_output_plan = _first_strict_mapping(
        run_manifest.get("hazard_output_plan"),
        "hazard_output_plan",
    )
    output_roots = _first_strict_mapping(hazard_output_plan.get("output_roots"), "hazard_output_plan.output_roots")

    required_roots = {
        "validation_private_root": (output_roots.get("validation_results"), True),
        "hazard_results_root": (output_roots.get("hazard_results"), True),
        "scratch_like_case_root": (input_freeze.get("benchmark_case_path"), True),
    }

    for key, (value, required) in required_roots.items():
        if not isinstance(value, str):
            if key == "scratch_like_case_root":
                path = repo_root
            else:
                _add_check(
                    checks,
                    name=f"output_roots.{key}.schema",
                    status="warn",
                    required=False,
                    message=f"manifest missing {key}",
                    path=None,
                )
                continue
            continue
        else:
            path = _to_repo_path(repo_root, value)
            if _is_writable_dir(path):
                _add_check(
                    checks,
                    name=f"output_roots.{key}",
                    status="pass",
                    required=required,
                    message="output root parent is writable",
                    path=str(path),
                )
            else:
                _add_check(
                    checks,
                    name=f"output_roots.{key}",
                    status="fail" if required else "warn",
                    required=required,
                    message="output root parent is not writable",
                    path=str(path),
                )


def _collect_claim_scope_checks(checks: list[dict[str, Any]], run_manifest: dict[str, Any]) -> None:
    claim_boundary = run_manifest.get("claim_boundary")
    if not isinstance(claim_boundary, dict):
        _add_check(
            checks,
            name="claim_boundary",
            status="warn",
            required=False,
            message="manifest claim_boundary missing",
            path=None,
        )
        return

    unsupported = claim_boundary.get("unsupported_current_claims")
    if not isinstance(unsupported, list):
        _add_check(
            checks,
            name="claim_boundary.unsupported_current_claims",
            status="warn",
            required=False,
            message="claim boundary must list unsupported_current_claims",
            path=None,
        )
        return

    for required_claim in (
        "annual_frequency",
        "return_period",
        "physical_probability",
        "risk_map",
    ):
        if required_claim in unsupported:
            _add_check(
                checks,
                name=f"claim_boundary.unsupported_current_claims.{required_claim}",
                status="pass",
                required=False,
                message="annual/physical/risk products remain out of scope",
                path=None,
            )


def _collect_balfrin_contract_checks(
    repo_root: Path,
    checks: list[dict[str, Any]],
    contract_report: dict[str, Any],
    dry_run_report: dict[str, Any],
) -> None:
    contract_path = contract_report.get("contract_path")
    minimal_demo_status = contract_report.get("minimal_demo_status")
    contract_status = contract_report.get("contract_status")
    if minimal_demo_status == "ready" and contract_status == "ready_for_balfrin_single_release_zone_pilot":
        _add_check(
            checks,
            name="balfrin_contract.summary",
            status="pass",
            required=True,
            message="frozen Balfrin minimal demonstration contract is ready",
            path=contract_path,
        )
    else:
        _add_check(
            checks,
            name="balfrin_contract.summary",
            status="fail",
            required=True,
            message=(
                "Balfrin contract summary is not ready: "
                f"contract_status={contract_status}, minimal_demo_status={minimal_demo_status}"
            ),
            path=contract_path,
        )

    release_zone_scope = contract_report.get("release_zone_scope", {})
    for key, expected in (
        ("release_zone_count", 1),
        ("release_cell_count", 10),
        ("trajectory_count_target", 1000),
        ("trajectories_per_release_cell", 100),
        ("block_scenario_count", 3),
    ):
        value = release_zone_scope.get(key)
        _add_check(
            checks,
            name=f"balfrin_contract.release_zone_scope.{key}",
            status="pass" if value == expected else "fail",
            required=True,
            message=f"{key} must be {expected}",
            path=contract_path,
        )

    validation_output = contract_report.get("validation_output", {})
    _add_check(
        checks,
        name="balfrin_contract.validation_output",
        status=(
            "pass"
            if validation_output.get("validation_output_mode") == "rebuildable_reduced_output"
            and validation_output.get("conditional_curve_export") == "summary-only"
            and validation_output.get("grid_csv_export") == "none"
            and validation_output.get("pilot_gis_package") is True
            and validation_output.get("export_geotiff") is True
            else "fail"
        ),
        required=True,
        message="Balfrin contract uses the frozen reduced-output and GIS package mode",
        path=contract_path,
    )

    minimal_demo_contract = contract_report.get("minimal_demo_contract", {})
    non_goals = set(minimal_demo_contract.get("non_goals", []))
    _add_check(
        checks,
        name="balfrin_contract.non_goals.scientific_closure",
        status="pass" if "scientific_closure" in non_goals else "fail",
        required=True,
        message="minimal demo keeps scientific closure out of scope",
        path=contract_path,
    )

    claim_boundaries = minimal_demo_contract.get("claim_boundaries", {})
    for field in (
        "operational_claims_allowed",
        "annual_frequency_claims_allowed",
        "physical_probability_claims_allowed",
        "risk_exposure_vulnerability_claims_allowed",
        "scale_up_authorized",
        "distributed_execution_authorized",
    ):
        _add_check(
            checks,
            name=f"balfrin_contract.claim_boundaries.{field}",
            status="pass" if claim_boundaries.get(field) is False else "fail",
            required=True,
            message=f"{field} must remain false",
            path=contract_path,
        )

    command_ids = [command.get("command_id") for command in minimal_demo_contract.get("commands", [])]
    _add_check(
        checks,
        name="balfrin_contract.command_sequence",
        status="pass" if tuple(command_ids) == EXPECTED_BALFRIN_COMMAND_IDS else "fail",
        required=True,
        message="command sequence is frozen and read-only",
        path=contract_path,
    )

    _add_check(
        checks,
        name="balfrin_case_plan.status",
        status=(
            "pass"
            if dry_run_report.get("case_plan_status") == "ready"
            and dry_run_report.get("case_execution_status") == "blocked_template_only"
            else "fail"
        ),
        required=True,
        message="Balfrin dry-run plan remains read-only and blocked from execution",
        path=contract_path,
    )
    _add_check(
        checks,
        name="balfrin_case_plan.boundary",
        status=(
            "pass"
            if dry_run_report.get("read_only") is True and dry_run_report.get("operational_claims_allowed") is False
            else "fail"
        ),
        required=True,
        message="dry-run plan preserves the non-operational boundary",
        path=contract_path,
    )
    _add_check(
        checks,
        name="balfrin_case_plan.validation_output_mode",
        status=(
            "pass"
            if dry_run_report.get("validation_output", {}).get("validation_output_mode")
            == "rebuildable_reduced_output"
            else "fail"
        ),
        required=True,
        message="case plan keeps rebuildable reduced output frozen",
        path=contract_path,
    )
    _add_check(
        checks,
        name="balfrin_case_plan.ignored_roots",
        status=(
            "pass"
            if isinstance(dry_run_report.get("ignored_output_roots"), list)
            and {"validation/results/", "hazard/results/", "target/"}.issubset(
                set(dry_run_report.get("ignored_output_roots", []))
            )
            else "fail"
        ),
        required=True,
        message="dry-run plan keeps generated products in ignored roots",
        path=contract_path,
    )

    planned_roots = dry_run_report.get("planned_case_output_roots", [])
    if isinstance(planned_roots, list) and len(planned_roots) == 2 and all(isinstance(path, str) for path in planned_roots):
        writable = all(_is_writable_dir(_to_repo_path(repo_root, path)) for path in planned_roots)
        _add_check(
            checks,
            name="balfrin_case_plan.output_roots",
            status="pass" if writable else "fail",
            required=True,
            message="planned Balfrin output roots are writable",
            path=planned_roots[0],
        )
    else:
        _add_check(
            checks,
            name="balfrin_case_plan.output_roots",
            status="fail",
            required=True,
            message="Balfrin case plan does not declare the expected output roots",
            path=contract_path,
        )

    selection_rule = dry_run_report.get("deterministic_generation_evidence", {}).get("selection_rule", "")
    _add_check(
        checks,
        name="balfrin_case_plan.selection_rule",
        status="pass" if "no simulation execution" in str(selection_rule) else "fail",
        required=True,
        message="case plan explicitly stays dry-run only",
        path=contract_path,
    )


def collect_readiness_report(
    *,
    repo_root: Path,
    run_manifest_path: Path,
    tool_probe: Any = None,
    git_probe: Any = None,
    validator_module: Any = None,
) -> dict[str, Any]:
    if not repo_root.is_absolute():
        repo_root = (Path.cwd() / repo_root).absolute()
    tool_probe = tool_probe or _tool_probe
    git_probe = git_probe or _git_info
    checks: list[dict[str, Any]] = []

    if repo_root.exists() and repo_root.is_dir():
        _add_check(
            checks,
            name="repo.path",
            status="pass",
            required=True,
            message="repo_path exists",
            path=str(repo_root),
        )
    else:
        _add_check(
            checks,
            name="repo.path",
            status="fail",
            required=True,
            message="repo_path does not exist",
            path=str(repo_root),
        )

    git_info = git_probe(repo_root)
    branch = git_info.get("branch")
    commit = git_info.get("commit")
    if git_info.get("status") == "ok" and branch and commit:
        _add_check(
            checks,
            name="repo.branch",
            status="pass",
            required=True,
            message="git branch resolved",
            path=None,
        )
        _add_check(
            checks,
            name="repo.commit",
            status="pass",
            required=True,
            message="git commit resolved",
            path=None,
        )
    else:
        _add_check(
            checks,
            name="repo.branch",
            status="fail",
            required=True,
            message=(git_info.get("error") or "failed to read git branch/commit"),
            path=None,
        )

    if branch:
        current_branch = branch
    else:
        current_branch = None

    if commit:
        current_commit = commit
    else:
        current_commit = None

    for binary in ("rustc", "cargo", "python3", "uv"):
        info = tool_probe(binary)
        if info.get("available"):
            _add_check(
                checks,
                name=f"tool.{binary}",
                status="pass",
                required=True,
                message=info.get("version") or "tool available",
                path=info.get("path"),
            )
        else:
            _add_check(
                checks,
                name=f"tool.{binary}",
                status="fail",
                required=True,
                message=f"{binary} missing or not executable{f' ({info.get('error')})' if info.get('error') else ''}",
                path=info.get("path"),
            )

    qgis_info = tool_probe("qgis")
    if qgis_info.get("available"):
        _add_check(
            checks,
            name="tool.qgis",
            status="pass",
            required=False,
            message=qgis_info.get("version") or "qgis available",
            path=qgis_info.get("path"),
        )
    else:
        _add_check(
            checks,
            name="tool.qgis",
            status="warn",
            required=False,
            message="QGIS not found; manual GIS visual QA remains out-of-scope for this readiness check",
            path=qgis_info.get("path"),
        )

    run_manifest_path = run_manifest_path if run_manifest_path.is_absolute() else (repo_root / run_manifest_path)
    if not run_manifest_path.exists():
        _add_check(
            checks,
            name="run_manifest",
            status="fail",
            required=True,
            message="run manifest does not exist",
            path=str(run_manifest_path),
        )
        return {
            "script": "balfrin_tschamut_readiness",
            "status": STATUS_BLOCKED,
            "repo_path": str(repo_root),
            "target_run_manifest": str(run_manifest_path),
            "branch": current_branch,
            "commit": current_commit,
            "checks": checks,
        }

    run_manifest = _read_yaml(run_manifest_path)
    schema_version = run_manifest.get("schema_version")
    if schema_version == CONDITIONAL_PILOT_SCHEMA_VERSION:
        _add_check(
            checks,
            name="run_manifest.schema_version",
            status="pass",
            required=True,
            message=f"schema_version is {CONDITIONAL_PILOT_SCHEMA_VERSION}",
            path=str(run_manifest_path),
        )
        if validator_module is None:
            validator_path = ROOT / "scripts" / "validate_public_real_site_conditional_pilot_run.py"
            validator_module = _load_module(validator_path, "validate_public_real_site_conditional_pilot_run")

        try:
            validator_module.validate_pilot_run(run_manifest, run_manifest_path)
            _add_check(
                checks,
                name="pilot_run_manifest",
                status="pass",
                required=True,
                message="run manifest validated by existing pilot contract validator",
                path=str(run_manifest_path),
            )
        except Exception as exc:  # noqa: BLE001 - preserve validator context for diagnostics.
            _add_check(
                checks,
                name="pilot_run_manifest",
                status="fail",
                required=True,
                message=f"pilot manifest validation failed: {exc}",
                path=str(run_manifest_path),
            )
            return {
                "script": "balfrin_tschamut_readiness",
                "status": STATUS_BLOCKED,
                "repo_path": str(repo_root),
                "target_run_manifest": str(run_manifest_path),
                "branch": current_branch,
                "commit": current_commit,
                "checks": checks,
            }

        if run_manifest.get("run_status") == "template_not_run":
            _add_check(
                checks,
                name="run_manifest.status",
                status="fail",
                required=True,
                message="template run manifest is not usable for readiness command prerequisites",
                path=str(run_manifest_path),
            )
            return {
                "script": "balfrin_tschamut_readiness",
                "status": STATUS_BLOCKED,
                "repo_path": str(repo_root),
                "target_run_manifest": str(run_manifest_path),
                "branch": current_branch,
                "commit": current_commit,
                "checks": checks,
            }

        _collect_claim_scope_checks(checks, run_manifest)
        _collect_root_checks(repo_root, checks, run_manifest)

        input_freeze = _first_strict_mapping(run_manifest.get("input_freeze"), "input_freeze")
        geodata_manifest_raw = input_freeze.get("geodata_manifest_path")
        if not isinstance(geodata_manifest_raw, str) or not geodata_manifest_raw:
            _add_check(
                checks,
                name="input_freeze.geodata_manifest_path",
                status="fail",
                required=True,
                message="input_freeze.geodata_manifest_path missing",
                path=None,
            )
        else:
            geodata_manifest_path = _to_repo_path(repo_root, geodata_manifest_raw)
            if geodata_manifest_path.exists():
                _add_check(
                    checks,
                    name="input_freeze.geodata_manifest_path",
                    status="pass",
                    required=True,
                    message="geodata manifest exists",
                    path=str(geodata_manifest_path),
                )
                _collect_processed_inputs_checks(repo_root, checks, geodata_manifest_path)
            else:
                _add_check(
                    checks,
                    name="input_freeze.geodata_manifest_path",
                    status="fail",
                    required=True,
                    message="geodata manifest path missing",
                    path=str(geodata_manifest_path),
                )

        for key in ("terrain_metadata_path", "source_zone_metadata_path", "scenario_table_path", "source_scenario_policy_path"):
            raw = input_freeze.get(key)
            if not isinstance(raw, str):
                _add_check(
                    checks,
                    name=f"input_freeze.{key}",
                    status="warn",
                    required=False,
                    message=f"{key} missing in manifest",
                    path=None,
                )
                continue
            path = _to_repo_path(repo_root, raw)
            if path.exists():
                _add_check(
                    checks,
                    name=f"input_freeze.{key}",
                    status="pass",
                    required=True,
                    message=f"{key} exists",
                    path=str(path),
                )
            else:
                _add_check(
                    checks,
                    name=f"input_freeze.{key}",
                    status="fail",
                    required=True,
                    message=f"{key} missing",
                    path=str(path),
                )

        try:
            command_plan = validator_module.build_command_plan(run_manifest)
            _add_check(
                checks,
                name="command_plan",
                status="pass",
                required=True,
                message="command-plan built without execution",
                path=None,
            )
            _collect_command_plan_checks(repo_root, checks, command_plan)
        except Exception as exc:  # noqa: BLE001 - this check reports parser/runtime details.
            _add_check(
                checks,
                name="command_plan",
                status="fail",
                required=True,
                message=f"command-plan build failed: {exc}",
                path=None,
            )
            command_plan = None
    elif schema_version == BALFRIN_CONTRACT_SCHEMA_VERSION:
        _add_check(
            checks,
            name="run_manifest.schema_version",
            status="pass",
            required=True,
            message=f"schema_version is {BALFRIN_CONTRACT_SCHEMA_VERSION}",
            path=str(run_manifest_path),
        )
        contract_module = _load_module(
            ROOT / "scripts" / "summarize_balfrin_single_release_zone_pilot_contract.py",
            "summarize_balfrin_single_release_zone_pilot_contract",
        )
        plan_module = _load_module(
            ROOT / "scripts" / "plan_balfrin_single_release_zone_case_dry_run.py",
            "plan_balfrin_single_release_zone_case_dry_run",
        )
        contract_report = contract_module.build_report(run_manifest_path)
        dry_run_report = plan_module.build_report(contract_path=run_manifest_path)
        _collect_balfrin_contract_checks(repo_root, checks, contract_report, dry_run_report)
        command_plan = {
            "schema_version": dry_run_report["schema_version"],
            "case_plan_status": dry_run_report["case_plan_status"],
            "case_execution_status": dry_run_report["case_execution_status"],
            "commands": contract_report["minimal_demo_contract"]["commands"],
            "planned_case_output_roots": dry_run_report["planned_case_output_roots"],
            "ignored_output_roots": dry_run_report["ignored_output_roots"],
            "blocked_case_execution_template": dry_run_report["blocked_case_execution_template"],
            "deterministic_generation_evidence": dry_run_report["deterministic_generation_evidence"],
        }
    else:
        _add_check(
            checks,
            name="run_manifest.schema_version",
            status="fail",
            required=True,
            message=(
                "unsupported schema_version; expected "
                f"{CONDITIONAL_PILOT_SCHEMA_VERSION} or {BALFRIN_CONTRACT_SCHEMA_VERSION}"
            ),
            path=str(run_manifest_path),
        )
        return {
            "script": "balfrin_tschamut_readiness",
            "status": STATUS_BLOCKED,
            "repo_path": str(repo_root),
            "target_run_manifest": str(run_manifest_path),
            "branch": current_branch,
            "commit": current_commit,
            "checks": checks,
        }

    blockers = [entry for entry in checks if entry["required"] and entry["status"] == "fail"]
    status = STATUS_READY if not blockers else STATUS_BLOCKED

    return {
        "script": "balfrin_tschamut_readiness",
        "status": status,
        "repo_path": str(repo_root),
        "target_run_manifest": str(run_manifest_path),
        "branch": branch,
        "commit": commit,
        "toolchain": {
            "rustc_available": any(entry["name"] == "tool.rustc" and entry["status"] == "pass" for entry in checks),
            "cargo_available": any(entry["name"] == "tool.cargo" and entry["status"] == "pass" for entry in checks),
            "python3_available": any(entry["name"] == "tool.python3" and entry["status"] == "pass" for entry in checks),
            "uv_available": any(entry["name"] == "tool.uv" and entry["status"] == "pass" for entry in checks),
            "qgis_optional": any(entry["name"] == "tool.qgis" for entry in checks),
        },
        "command_plan": command_plan,
        "checks": checks,
        "blocking_checks": [entry["name"] for entry in blockers],
        "report_scope": {
            "annual_physical_risk_products": "out_of_scope",
            "notes": [
                "This checker validates execution readiness and path/tool preconditions only.",
                "Annual frequency, annual intensity frequency, and operational risk-map outputs are explicitly out of scope.",
            ],
        },
    }


def _format_human_summary(report: dict[str, Any]) -> str:
    lines = ["Balfrin Tschamut readiness check", "--------------------------------"]
    status = report["status"]
    lines.append(f"Status: {status}")
    lines.append(f"Repository: {report['repo_path']}")
    if report.get("branch"):
        lines.append(f"Branch: {report['branch']}")
    if report.get("commit"):
        lines.append(f"Commit: {report['commit']}")

    checks = report["checks"]
    failures = [c for c in checks if c["status"] == "fail"]
    required_failures = [c for c in failures if c["required"]]
    warnings = [c for c in checks if c["status"] == "warn"]

    lines.append("")
    lines.append(f"Blocking checks: {len(required_failures)}")
    for entry in required_failures:
        lines.append(f"- {entry['name']}: {entry['message']}")
        if entry.get("path"):
            lines.append(f"  path: {entry['path']}")

    if warnings:
        lines.append("")
        lines.append(f"Warnings: {len(warnings)}")
        for entry in warnings:
            lines.append(f"- {entry['name']}: {entry['message']}")
            if entry.get("path"):
                lines.append(f"  path: {entry['path']}")

    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check read-only prerequisites for the Tschamut public conditional pilot on balfrin.",
    )
    parser.add_argument(
        "run_manifest",
        nargs="?",
        type=Path,
        default=default_run_manifest,
        help="Pilot run manifest path (default: selected-domain gate manifest)",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=ROOT,
        help="Path to repository root for relative-path resolution",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json", "both"),
        default="both",
        help="Output format",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = args.repo_root
    report = collect_readiness_report(
        repo_root=repo_root,
        run_manifest_path=args.run_manifest,
    )

    if args.format in {"text", "both"}:
        print(_format_human_summary(report))
    if args.format in {"json", "both"}:
        print(json.dumps(report, indent=2, sort_keys=True))

    if report["status"] == STATUS_READY:
        return 0
    if report["status"] == STATUS_BLOCKED:
        return 2
    return 1


if __name__ == "__main__":  # pragma: no cover - CLI entry
    raise SystemExit(main())
