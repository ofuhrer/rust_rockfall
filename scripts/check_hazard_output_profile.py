#!/usr/bin/env python3
"""Classify hazard-layer command output profiles from command-plans or argv tokens."""

from __future__ import annotations

import argparse
import json
import shlex
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


KNOWN_CONTROL_FLAGS_WITH_VALUES = {
    "--conditional-curve-export": "conditional_curve_export",
    "--grid-csv-export": "grid_csv_export",
    "--trajectory-workers": "trajectory_workers",
    "--reducer-workers": "reducer_workers",
}
KNOWN_BOOLEAN_FLAGS = {
    "--no-plots": "no_plots",
    "--export-geotiff": "export_geotiff",
    "--pilot-gis-package": "pilot_gis_package",
}
KNOWN_STRING_FLAGS = {
    "--map-package-manifest-json": "map_package_manifest_json",
    "--pilot-gis-package-manifest-json": "pilot_gis_package_manifest_json",
}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Classify build_hazard_layers output profile intent from command inputs."
    )
    parser.add_argument(
        "--command-plan",
        type=Path,
        help="Path to a command-plan JSON file (e.g. from validate_public_real_site_conditional_pilot_run.py)",
    )
    parser.add_argument(
        "--command-index",
        type=int,
        default=None,
        help="Command index within command-plan (optional when command-plan has one hazard command)",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json", "both"),
        default="both",
        help="Output format",
    )
    parser.add_argument(
        "command",
        nargs="*",
        help=(
            "Direct command tokens (use -- to pass tokens that begin with -)."
            " Useful when a command-plan is not available."
        ),
    )
    return parser.parse_args(argv)


def _read_command_plan(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read command-plan: {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"command-plan must be an object: {path}")
    return payload


def _as_command_tokens(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(token) for token in value]
    if isinstance(value, str):
        return shlex.split(value)
    raise ValueError("command entry must be a list or string")


def _looks_like_hazard_command(tokens: list[str]) -> bool:
    if not tokens:
        return False
    return any(part.endswith("scripts/build_hazard_layers.py") or part == "build_hazard_layers.py" for part in tokens)


def _find_hazard_command_from_plan(plan: dict[str, Any], command_index: int | None = None) -> list[str]:
    commands = plan.get("commands")
    if not isinstance(commands, list) or not commands:
        raise ValueError("command-plan does not contain a commands array")

    indexed = []
    for entry in commands:
        if not isinstance(entry, dict):
            continue
        command_value = entry.get("command")
        if command_value is None:
            continue
        try:
            tokens = _as_command_tokens(command_value)
        except ValueError:
            continue
        if _looks_like_hazard_command(tokens):
            indexed.append(tokens)

    if not indexed:
        raise ValueError("command-plan does not contain build_hazard_layers command")

    if command_index is None:
        if len(indexed) == 1:
            return indexed[0]
        # Prefer the last hazard build command in multi-step plan.
        return indexed[-1]

    if command_index < 0:
        command_index = len(indexed) + command_index
    if command_index < 0 or command_index >= len(indexed):
        raise ValueError(f"--command-index {command_index} out of range for hazard command selection")
    return indexed[command_index]


def _extract_build_hazard_tokens(tokens: list[str]) -> list[str]:
    if not _looks_like_hazard_command(tokens):
        raise ValueError("input command does not reference scripts/build_hazard_layers.py")
    for index, token in enumerate(tokens):
        if token.endswith("build_hazard_layers.py") or token == "build_hazard_layers.py":
            return tokens[index + 1 :]
    raise ValueError("cannot locate build_hazard_layers.py token in command")


def _collect_profile_controls(tokens: list[str]) -> tuple[dict[str, Any], list[str]]:
    controls: dict[str, Any] = {
        "conditional_curve_export": "full",
        "grid_csv_export": "full",
        "no_plots": False,
        "export_geotiff": False,
        "pilot_gis_package": False,
        "trajectory_workers": 1,
        "reducer_workers": 1,
        "map_package_manifest_json": None,
        "pilot_gis_package_manifest_json": None,
    }

    unsupported: list[str] = []
    idx = 0
    while idx < len(tokens):
        token = tokens[idx]
        if token in KNOWN_CONTROL_FLAGS_WITH_VALUES:
            key = KNOWN_CONTROL_FLAGS_WITH_VALUES[token]
            if idx + 1 >= len(tokens):
                unsupported.append(f"{token} missing value")
                idx += 1
                continue
            value = tokens[idx + 1]
            if key in {"trajectory_workers", "reducer_workers"}:
                try:
                    controls[key] = int(value)
                except ValueError:
                    unsupported.append(f"{token} expects integer, got {value!r}")
            elif key in {"conditional_curve_export", "grid_csv_export"}:
                controls[key] = value
            else:
                controls[key] = value
            idx += 2
            continue

        if token in KNOWN_BOOLEAN_FLAGS:
            controls[KNOWN_BOOLEAN_FLAGS[token]] = True
            idx += 1
            continue

        if token in KNOWN_STRING_FLAGS:
            if idx + 1 >= len(tokens):
                unsupported.append(f"{token} missing value")
                idx += 1
                continue
            controls[KNOWN_STRING_FLAGS[token]] = tokens[idx + 1]
            idx += 2
            continue

        idx += 1

    return controls, unsupported


def _classify_controls(controls: dict[str, Any]) -> dict[str, Any]:
    matched_controls: list[str] = []
    missing_controls: list[str] = []
    ambiguous_controls: list[str] = []

    requires_scalable_curve = controls["conditional_curve_export"] == "summary-only"
    requires_scalable_csv = controls["grid_csv_export"] == "none"
    requires_no_plots = bool(controls["no_plots"])

    if requires_scalable_curve:
        matched_controls.append("--conditional-curve-export summary-only")
    else:
        if controls["conditional_curve_export"] != "full":
            missing_controls.append("unexpected --conditional-curve-export value")
    if requires_scalable_csv:
        matched_controls.append("--grid-csv-export none")
    else:
        if controls["grid_csv_export"] != "full":
            missing_controls.append("unexpected --grid-csv-export value")
    if requires_no_plots:
        matched_controls.append("--no-plots")

    if controls["conditional_curve_export"] == "summary-only" and controls["grid_csv_export"] == "full":
        ambiguous_controls.append("conditional summary-only with full grid CSV output")
    if controls["conditional_curve_export"] == "full" and controls["grid_csv_export"] == "none":
        ambiguous_controls.append("full curves with grid-csv disabled")

    scalability_ready = requires_scalable_curve and requires_scalable_csv and requires_no_plots

    profile = "custom_or_mixed"
    if scalability_ready:
        has_provenance_markers = (
            bool(controls["pilot_gis_package"])
            or controls["trajectory_workers"] > 1
            or controls["reducer_workers"] > 1
        )
        if has_provenance_markers:
            profile = "provenance_audit"
            if controls["pilot_gis_package"]:
                if not controls["pilot_gis_package_manifest_json"]:
                    missing_controls.append("--pilot-gis-package-manifest-json")
                if not controls["map_package_manifest_json"]:
                    missing_controls.append("--map-package-manifest-json")
            matched_controls.append("trajectory/reducer provenance lineage")
        else:
            profile = "scalable_conditional"
    else:
        if (
            controls["conditional_curve_export"] in {"full", None}
            and controls["grid_csv_export"] in {"full", None}
        ):
            profile = "full_debug"

    if not scalability_ready and controls["conditional_curve_export"] == "summary-only" and controls["grid_csv_export"] == "full":
        missing_controls.append("--grid-csv-export none for scalable_conditional")
        missing_controls.append("--no-plots for scalable_conditional")
    if not scalability_ready and controls["grid_csv_export"] == "none" and controls["conditional_curve_export"] == "full":
        missing_controls.append("--conditional-curve-export summary-only for scalable_conditional")

    required_scalable = [
        "--conditional-curve-export summary-only",
        "--grid-csv-export none",
        "--no-plots",
    ]
    missing_scalable_controls = [
        flag
        for flag in required_scalable
        if flag not in matched_controls
    ]

    recommendations = []
    if profile == "scalable_conditional":
        if controls["trajectory_workers"] != 2:
            recommendations.append("set --trajectory-workers 2 for balanced small-gate chunking")
        if controls["reducer_workers"] != 2:
            recommendations.append("set --reducer-workers 2 for balanced small-gate chunking")
    if profile == "full_debug" and missing_controls:
        recommendations.append("use --conditional-curve-export summary-only and --grid-csv-export none for scalable mode")

    return {
        "profile": profile,
        "matched_controls": sorted(set(matched_controls)),
        "missing_controls": sorted(set(missing_controls)),
        "missing_scalable_controls": missing_scalable_controls,
        "unsupported_or_ambiguous_controls": sorted(set(ambiguous_controls)),
        "recommendations": sorted(set(recommendations)),
        "controls": controls,
    }


def classify_profile(command_plan: Path | None = None, command: list[str] | None = None, *, command_index: int | None = None) -> dict[str, Any]:
    if command_plan is None and not command:
        raise ValueError("provide either --command-plan or explicit command tokens")

    if command_plan is not None:
        plan = _read_command_plan(command_plan)
        tokens = _find_hazard_command_from_plan(plan, command_index=command_index)
    else:
        assert command is not None
        tokens = command

    hazard_tokens = _extract_build_hazard_tokens(tokens)
    controls, parse_warnings = _collect_profile_controls(hazard_tokens)
    result = _classify_controls(controls)
    result["unsupported_or_ambiguous_controls"] = sorted(
        set(result["unsupported_or_ambiguous_controls"] + parse_warnings)
    )
    result["input"] = {
        "source": "command-plan" if command_plan is not None else "argv",
        "command": tokens,
    }
    return result


def _format_report(result: dict[str, Any]) -> str:
    lines = [
        f"Detected profile: {result['profile']}",
        "Matched controls:",
    ]
    if result["matched_controls"]:
        lines.extend(f"  - {flag}" for flag in result["matched_controls"])
    else:
        lines.append("  - (none)")

    lines.append("Missing controls:")
    if result["missing_controls"]:
        lines.extend(f"  - {flag}" for flag in result["missing_controls"])
    else:
        lines.append("  - (none)")

    lines.append("Unsupported/ambiguous controls:")
    if result["unsupported_or_ambiguous_controls"]:
        lines.extend(f"  - {flag}" for flag in result["unsupported_or_ambiguous_controls"])
    else:
        lines.append("  - (none)")

    if result["recommendations"]:
        lines.append("Recommendations:")
        lines.extend(f"  - {value}" for value in result["recommendations"])

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        result = classify_profile(
            command_plan=args.command_plan,
            command=args.command,
            command_index=args.command_index,
        )
    except ValueError as exc:
        print(f"error: {exc}")
        return 2

    if args.format in {"text", "both"}:
        print(_format_report(result))
    if args.format in {"json", "both"}:
        print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point.
    raise SystemExit(main())
