from __future__ import annotations

"""Fail-closed output-profile validation for generated command plans."""

from typing import Any, Mapping, Sequence
import shlex

from scripts.lib import output_profile_policy as OUTPUT_PROFILE_POLICY


SCHEMA_VERSION = "command_plan_output_profile_validation_v1"
STATUS_READY = "ready"
STATUS_BLOCKED = "blocked_unscalable_output_profile"
STATUS_FIXTURE_SAFE = "fixture_safe_tiny_smoke"
MAX_SCALABLE_WORKERS = 2

_FLAGS_WITH_VALUES = {
    "--conditional-curve-export",
    "--grid-csv-export",
    "--trajectory-workers",
    "--reducer-workers",
    "--trajectory",
    "--ensemble-trajectories-dir",
    "--deposition",
    "--impact-events",
    "--ensemble-impact-events-dir",
    "--impact-events-parquet",
    "--diagnostics",
}


def validate_command_plan_output_profile(
    commands: Sequence[Mapping[str, Any]],
    *,
    label: str,
    allow_tiny_fixture_outputs: bool = False,
) -> dict[str, Any]:
    """Validate output controls for command-plan records.

    Scalable plans fail closed. Tiny smoke fixtures can opt into the same
    diagnostics without failing historical full-debug fixture outputs.
    """

    command_reports = [
        _validate_command(command, allow_tiny_fixture_outputs=allow_tiny_fixture_outputs)
        for command in commands
    ]
    enforced_reports = [report for report in command_reports if report["enforced"]]
    blocked_reports = [] if allow_tiny_fixture_outputs else [
        report for report in enforced_reports if report["status"] != STATUS_READY
    ]
    if allow_tiny_fixture_outputs:
        status = STATUS_FIXTURE_SAFE
        summary = "tiny smoke fixture outputs are explicitly allowed while diagnostics remain visible"
    elif blocked_reports:
        status = STATUS_BLOCKED
        summary = "one or more scalable command-plan entries request non-scalable output or lack rebuildability controls"
    else:
        status = STATUS_READY
        summary = "all scalable command-plan entries satisfy reduced-output defaults"

    return {
        "schema_version": SCHEMA_VERSION,
        "label": label,
        "status": status,
        "summary": summary,
        "allow_tiny_fixture_outputs": allow_tiny_fixture_outputs,
        "validated_command_count": len(command_reports),
        "enforced_command_count": len(enforced_reports),
        "blocked_command_count": len(blocked_reports),
        "blocked_command_ids": [report["command_id"] for report in blocked_reports],
        "diagnostics": command_reports,
    }


def _validate_command(
    command: Mapping[str, Any],
    *,
    allow_tiny_fixture_outputs: bool,
) -> dict[str, Any]:
    command_id = str(command.get("id") or command.get("command_id") or "")
    command_text = str(command.get("command") or "")
    tokens = shlex.split(command_text) if command_text else []
    hazard = _is_hazard_command(tokens)
    enforced = hazard and _is_scalable_surface(command)
    controls = _collect_controls(tokens) if hazard else {}
    diagnostics: list[str] = []

    policy = dict(command.get("output_profile_policy") or {})
    if hazard:
        policy = OUTPUT_PROFILE_POLICY.classify_output_profile_policy(
            conditional_curve_export=controls.get("conditional_curve_export"),
            grid_csv_export=controls.get("grid_csv_export"),
            no_plots=controls.get("no_plots", False),
            explicit_debug_override=allow_tiny_fixture_outputs,
            label=command_id,
        )

    if enforced:
        if controls.get("conditional_curve_export") in {None, "full"}:
            diagnostics.append("full conditional-curve output is not allowed for scalable command plans")
        elif controls.get("conditional_curve_export") != "summary-only":
            diagnostics.append(f"unexpected conditional-curve output mode: {controls.get('conditional_curve_export')}")

        if controls.get("grid_csv_export") in {None, "full"}:
            diagnostics.append("full grid CSV output is not allowed for scalable command plans")
        elif controls.get("grid_csv_export") != "none":
            diagnostics.append(f"unexpected grid CSV output mode: {controls.get('grid_csv_export')}")

        if not controls.get("no_plots", False):
            diagnostics.append("missing reduced-output flag: --no-plots")

        for key, flag in (("trajectory_workers", "--trajectory-workers"), ("reducer_workers", "--reducer-workers")):
            workers = _int_value(controls.get(key), default=1)
            if workers > MAX_SCALABLE_WORKERS:
                diagnostics.append(f"excessive worker/chunk sidecars: {flag} {workers} exceeds {MAX_SCALABLE_WORKERS}")

        missing_rebuildability = [
            flag
            for flag, key in (
                ("--diagnostics", "diagnostics"),
                ("--deposition", "deposition"),
            )
            if not controls.get(key)
        ]
        if not (controls.get("trajectory") or controls.get("ensemble_trajectories_dir")):
            missing_rebuildability.append("--trajectory or --ensemble-trajectories-dir")
        if not (controls.get("impact_events") or controls.get("ensemble_impact_events_dir") or controls.get("impact_events_parquet")):
            missing_rebuildability.append("--impact-events, --ensemble-impact-events-dir, or --impact-events-parquet")
        if missing_rebuildability:
            diagnostics.append("missing rebuildability artifacts: " + ", ".join(missing_rebuildability))

    status = STATUS_READY if not diagnostics or allow_tiny_fixture_outputs else STATUS_BLOCKED
    if allow_tiny_fixture_outputs and diagnostics:
        status = STATUS_FIXTURE_SAFE

    return {
        "command_id": command_id,
        "status": status,
        "enforced": enforced,
        "is_hazard_command": hazard,
        "diagnostics": diagnostics,
        "controls": controls,
        "output_profile_policy": policy,
    }


def _is_hazard_command(tokens: Sequence[str]) -> bool:
    return any(token == "build_hazard_layers.py" or token.endswith("/build_hazard_layers.py") for token in tokens)


def _is_scalable_surface(command: Mapping[str, Any]) -> bool:
    if command.get("read_only"):
        return False
    if not command.get("may_produce_ignored_outputs") and not command.get("ignored_output_paths"):
        return False
    return True


def _collect_controls(tokens: Sequence[str]) -> dict[str, Any]:
    controls: dict[str, Any] = {
        "conditional_curve_export": None,
        "grid_csv_export": None,
        "no_plots": False,
        "trajectory_workers": 1,
        "reducer_workers": 1,
    }
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token == "--no-plots":
            controls["no_plots"] = True
            index += 1
            continue
        if token in _FLAGS_WITH_VALUES:
            value = tokens[index + 1] if index + 1 < len(tokens) else None
            key = token.removeprefix("--").replace("-", "_")
            controls[key] = value
            index += 2
            continue
        index += 1
    return controls


def _int_value(value: Any, *, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default
