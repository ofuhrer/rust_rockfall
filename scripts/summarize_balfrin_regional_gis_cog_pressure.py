#!/usr/bin/env python3
"""Summarize regional GIS/COG package pressure from committed outputs.

This helper is read-only. It measures file counts, byte counts, and raster
counts for the committed regional-output root and an available converted-package
proof root, then threads those counts through the GIS/COG readiness audit so the
report can distinguish standard-root blockage from converted-package readiness
without implying operational GIS readiness.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Callable

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import audit_gis_cog_package_readiness as gis_cog


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "balfrin_regional_gis_cog_pressure_v1"
DEFAULT_ARTIFACT_ROOT = ROOT / "hazard/results/tschamut_public_pilot/target_gate_v1"
DEFAULT_CONVERTED_PACKAGE_ROOT = ROOT / "hazard/results/tschamut_public_pilot/gate_v1_cog_export"


class BalfrinRegionalGisCogPressureError(ValueError):
    """User-facing pressure-summary error."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-root", type=Path, default=DEFAULT_ARTIFACT_ROOT)
    parser.add_argument("--converted-package-root", type=Path, default=DEFAULT_CONVERTED_PACKAGE_ROOT)
    parser.add_argument("--format", choices=("json", "text"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    parser.add_argument("--text-output", type=Path, default=None)
    args = parser.parse_args(argv)

    try:
        report = build_report(
            artifact_root=args.artifact_root,
            converted_package_root=args.converted_package_root,
            raster_metadata_provider=gis_cog.inspect_raster_metadata,
        )
    except BalfrinRegionalGisCogPressureError as exc:
        print(f"balfrin regional GIS/COG pressure error: {exc}", file=sys.stderr)
        return 2

    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.text_output is not None:
        args.text_output.parent.mkdir(parents=True, exist_ok=True)
        args.text_output.write_text(render_text_report(report), encoding="utf-8")

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text_report(report))
    return 0 if report["pressure_state"] != "blocked_missing_inputs" else 2


def build_report(
    *,
    artifact_root: Path,
    converted_package_root: Path,
    raster_metadata_provider: Callable[[Path], dict[str, Any] | None] | None = None,
) -> dict[str, Any]:
    artifact_root = Path(artifact_root)
    converted_package_root = Path(converted_package_root)
    provider = raster_metadata_provider or gis_cog.inspect_raster_metadata

    standard_counts = summarize_package_root(artifact_root)
    converted_counts = summarize_package_root(converted_package_root)
    gis_report = gis_cog.build_gis_cog_readiness_report(
        artifact_roots=[artifact_root],
        converted_package_roots=[converted_package_root],
        raster_metadata_provider=provider,
    )
    standard_artifact = gis_report["artifacts"][0] if gis_report.get("artifacts") else {}
    converted_package = gis_report["converted_packages"][0] if gis_report.get("converted_packages") else {}
    standard_status = str(gis_report.get("standard_package_readiness_status") or "blocked_missing_inputs")
    converted_status = str(gis_report.get("converted_package_readiness_status") or "not_provided")
    pressure_state = classify_pressure_state(standard_status, converted_status, standard_counts, converted_counts)

    return {
        "schema_version": SCHEMA_VERSION,
        "pressure_state": pressure_state,
        "evidence_class": "measured",
        "artifact_root": str(artifact_root),
        "converted_package_root": str(converted_package_root),
        "standard_root": {
            "path": str(artifact_root),
            "file_count": standard_counts["file_count"],
            "byte_count": standard_counts["byte_count"],
            "raster_count": standard_counts["raster_count"],
            "readiness_status": standard_status,
            "cog_package_status": standard_artifact.get("cog_package_status"),
            "blockers": list(standard_artifact.get("blockers") or []),
            "blocker_count": len(standard_artifact.get("blockers") or []),
            "next_unblock_action": next_unblock_action(artifact_root, standard_status),
        },
        "converted_package": {
            "path": str(converted_package_root),
            "file_count": converted_counts["file_count"],
            "byte_count": converted_counts["byte_count"],
            "raster_count": converted_counts["raster_count"],
            "readiness_status": converted_status,
            "cog_package_status": converted_package.get("cog_package_status"),
            "layer_inventory_status": converted_package.get("layer_inventory_status"),
            "cog_scope_status": converted_package.get("cog_scope", {}).get("status"),
            "blockers": list(converted_package.get("blockers") or []),
        },
        "standard_package_readiness_status": standard_status,
        "converted_package_readiness_status": converted_status,
        "standard_package_status": gis_report.get("standard_package_status", {}),
        "converted_package_status": gis_report.get("converted_package_status", {}),
        "converted_package_layer_inventory_status": gis_report.get("converted_package_layer_inventory_status"),
        "converted_package_scope_boundaries": gis_report.get("converted_package_scope_boundaries", {}),
        "converted_package_scope_deltas": gis_report.get("converted_package_scope_deltas", {}),
        "standard_package_layer_counts": gis_report.get("standard_package_layer_counts", {}),
        "pressure_summary": summarize_pressure_state(pressure_state, standard_status, converted_status),
        "claim_boundaries": {
            "operational_claims_allowed": False,
            "scale_up_authorized": False,
            "distributed_execution_authorized": False,
            "annual_frequency_claims_allowed": False,
            "physical_probability_claims_allowed": False,
            "risk_exposure_vulnerability_claims_allowed": False,
        },
        "source_paths": {
            "audit_helper": "scripts/audit_gis_cog_package_readiness.py",
            "conversion_helper": "scripts/convert_same_scale_package_to_cog.py",
        },
    }


def summarize_package_root(root: Path) -> dict[str, int]:
    files = [path for path in root.rglob("*") if path.is_file()]
    raster_count = sum(1 for path in files if path.suffix.lower() == ".tif")
    return {
        "file_count": len(files),
        "byte_count": sum(path.stat().st_size for path in files),
        "raster_count": raster_count,
    }


def classify_pressure_state(
    standard_status: str,
    converted_status: str,
    standard_counts: dict[str, int],
    converted_counts: dict[str, int],
) -> str:
    if standard_status == "blocked_missing_inputs" or converted_status == "not_provided":
        return "blocked_missing_inputs"
    if standard_status == "gis_package_ready_cog_blocked" and converted_status.startswith("cog_package_ready"):
        return "measured_blocked"
    if standard_status == "gis_package_ready" and converted_status.startswith("cog_package_ready"):
        return "measured_ready"
    if standard_counts["file_count"] == 0 or converted_counts["file_count"] == 0:
        return "blocked_missing_inputs"
    return "measured_blocked"


def summarize_pressure_state(pressure_state: str, standard_status: str, converted_status: str) -> str:
    if pressure_state == "blocked_missing_inputs":
        return "Regional GIS/COG pressure cannot be summarized because one or more package roots are missing."
    if pressure_state == "measured_ready":
        return (
            "Measured regional GIS/COG pressure is fully ready: the standard root is COG-ready and the converted proof root is ready."
        )
    return (
        f"Measured regional GIS/COG pressure is blocked at the standard root ({standard_status}) while the converted package remains {converted_status}."
    )


def next_unblock_action(artifact_root: Path, standard_status: str) -> str:
    if standard_status == "blocked_missing_inputs":
        return f"restore the missing package manifests under {artifact_root}"
    return (
        "PYENV_VERSION=system uv run python scripts/convert_same_scale_package_to_cog.py "
        f"--input-root {artifact_root} --output-root /tmp/rust-rockfall-tb453-target_gate_v1_cog_export --overwrite"
    )


def render_text_report(report: dict[str, Any]) -> str:
    lines = [
        f"pressure_state: {report['pressure_state']}",
        f"evidence_class: {report['evidence_class']}",
        f"standard_root_readiness_status: {report['standard_root']['readiness_status']}",
        f"standard_root_file_count: {report['standard_root']['file_count']}",
        f"standard_root_byte_count: {report['standard_root']['byte_count']}",
        f"standard_root_raster_count: {report['standard_root']['raster_count']}",
        f"standard_root_blockers: {', '.join(report['standard_root']['blockers']) or 'none'}",
        f"converted_package_readiness_status: {report['converted_package_readiness_status']}",
        f"converted_package_file_count: {report['converted_package']['file_count']}",
        f"converted_package_byte_count: {report['converted_package']['byte_count']}",
        f"converted_package_raster_count: {report['converted_package']['raster_count']}",
        f"converted_package_status: {report['converted_package']['cog_package_status']}",
        f"converted_package_scope_status: {report['converted_package']['cog_scope_status']}",
        f"pressure_summary: {report['pressure_summary']}",
        f"next_unblock_action: {report['standard_root']['next_unblock_action']}",
    ]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":  # pragma: no cover - CLI entry point.
    raise SystemExit(main())
