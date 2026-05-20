#!/usr/bin/env python3
"""Summarize a large-AOI GIS/COG stress test from existing package outputs.

The helper is read-only with respect to the committed standard package root.
It audits the standard-root GIS package, optionally converts that package into
an ignored scratch root, and reports runtime, storage, parity, and bottleneck
signals without claiming operational GIS readiness.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import audit_gis_cog_package_readiness as gis_cog
from scripts import package_aoi_hazard_map as aoi_packager
from scripts.convert_same_scale_package_to_cog import convert_same_scale_package_to_cog


SCHEMA_VERSION = "large_aoi_gis_cog_stress_test_v1"
DEFAULT_ARTIFACT_ROOT = ROOT / "hazard/results/tschamut_public_pilot/target_gate_v1"
DEFAULT_STRESS_ROOT = Path("/tmp/rust-rockfall-large-aoi-gis-cog-stress-test")
DEFAULT_PACKAGED_PACKAGE_ROOT = DEFAULT_STRESS_ROOT / "package"
DEFAULT_CONVERTED_PACKAGE_ROOT = DEFAULT_STRESS_ROOT / "converted"


class LargeAoiGisCogStressTestError(ValueError):
    """User-facing stress-test error."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-root", type=Path, default=DEFAULT_ARTIFACT_ROOT)
    parser.add_argument("--packaged-package-root", type=Path, default=DEFAULT_PACKAGED_PACKAGE_ROOT)
    parser.add_argument("--converted-package-root", type=Path, default=DEFAULT_CONVERTED_PACKAGE_ROOT)
    parser.add_argument("--format", choices=("json", "text"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    parser.add_argument("--text-output", type=Path, default=None)
    args = parser.parse_args(argv)

    try:
        report = build_report(
            artifact_root=args.artifact_root,
            packaged_package_root=args.packaged_package_root,
            converted_package_root=args.converted_package_root,
            raster_metadata_provider=gis_cog.inspect_raster_metadata,
        )
    except LargeAoiGisCogStressTestError as exc:
        print(f"large-AOI GIS/COG stress-test error: {exc}", file=sys.stderr)
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
    return 0 if report["stress_test_status"] != "blocked_missing_inputs" else 2


def build_report(
    *,
    artifact_root: Path,
    packaged_package_root: Path,
    converted_package_root: Path,
    raster_metadata_provider: Callable[[Path], dict[str, Any] | None] | None = None,
    package_runner: Callable[[Path, Path], dict[str, Any]] | None = None,
    conversion_runner: Callable[[Path, Path], dict[str, Any]] | None = None,
    clock: Callable[[], float] | None = None,
) -> dict[str, Any]:
    artifact_root = Path(artifact_root)
    packaged_package_root = Path(packaged_package_root)
    converted_package_root = Path(converted_package_root)
    provider = raster_metadata_provider or gis_cog.inspect_raster_metadata
    package_runner = package_runner or (
        lambda input_root, output_root: aoi_packager.package_aoi_hazard_map(input_root, output_root, overwrite=True)
    )
    conversion_runner = conversion_runner or (
        lambda input_root, output_root: convert_same_scale_package_to_cog(input_root, output_root, overwrite=True)
    )
    clock = clock or time.perf_counter

    package_generation_started = clock()
    package_report = package_runner(artifact_root, packaged_package_root)
    package_generation_seconds = max(0.0, clock() - package_generation_started)
    package_html_path = resolve_optional_path((package_report.get("review_surface_paths") or {}).get("html"))
    package_manifest_path = resolve_optional_path((package_report.get("review_surface_paths") or {}).get("manifest"))

    if str(package_report.get("status") or "").startswith("blocked_"):
        return build_blocked_report(
            artifact_root=artifact_root,
            packaged_package_root=packaged_package_root,
            converted_package_root=converted_package_root,
            package_report=package_report,
            package_generation_seconds=package_generation_seconds,
            package_html_path=package_html_path,
            package_manifest_path=package_manifest_path,
            standard_report={"gis_cog_readiness_status": "blocked_missing_inputs", "standard_package_status": {}},
            standard_artifact={},
        )

    standard_report = gis_cog.build_gis_cog_readiness_report(
        artifact_roots=[packaged_package_root],
        raster_metadata_provider=provider,
    )
    standard_artifact = standard_report["artifacts"][0] if standard_report.get("artifacts") else {}

    if standard_report["gis_cog_readiness_status"] == "blocked_missing_inputs":
        return build_blocked_report(
            artifact_root=artifact_root,
            packaged_package_root=packaged_package_root,
            converted_package_root=converted_package_root,
            package_report=package_report,
            package_generation_seconds=package_generation_seconds,
            package_html_path=package_html_path,
            package_manifest_path=package_manifest_path,
            standard_report=standard_report,
            standard_artifact=standard_artifact,
        )

    conversion_started = clock()
    conversion_report = conversion_runner(packaged_package_root, converted_package_root)
    conversion_seconds = max(0.0, clock() - conversion_started)

    combined_report = gis_cog.build_gis_cog_readiness_report(
        artifact_roots=[packaged_package_root],
        converted_package_roots=[converted_package_root],
        raster_metadata_provider=provider,
    )
    converted_package = combined_report["converted_packages"][0] if combined_report.get("converted_packages") else {}

    standard_storage = summarize_manifest_storage(standard_artifact)
    converted_storage = summarize_manifest_storage(converted_package)
    standard_runtime = summarize_package_runtime(standard_artifact)
    converted_runtime = summarize_package_runtime(converted_package)
    first_bottleneck = identify_first_bottleneck(
        standard_report=standard_report,
        standard_artifact=standard_artifact,
        combined_report=combined_report,
        converted_package=converted_package,
        conversion_report=conversion_report,
        package_report=package_report,
    )

    report = {
        "schema_version": SCHEMA_VERSION,
        "stress_test_status": "ready",
        "artifact_root": str(artifact_root),
        "packaged_package_root": str(packaged_package_root),
        "converted_package_root": str(converted_package_root),
        "package_generation_status": package_report.get("status"),
        "package_generation_seconds": package_generation_seconds,
        "package_file_count": package_report.get("package_file_count"),
        "package_byte_count": package_report.get("package_byte_count"),
        "qa_review_html_size_bytes": path_size(package_html_path),
        "qa_review_manifest_size_bytes": path_size(package_manifest_path),
        "standard_package_readiness_status": standard_report["gis_cog_readiness_status"],
        "converted_package_readiness_status": combined_report["converted_package_readiness_status"],
        "standard_package_status": standard_report.get("standard_package_status", {}),
        "converted_package_status": combined_report.get("converted_package_status", {}),
        "package_runtime_seconds": standard_runtime.get("total_wall_seconds"),
        "package_core_output_write_seconds": standard_runtime.get("core_output_write_seconds"),
        "package_manifest_write_seconds": standard_runtime.get("manifest_write_seconds"),
        "cog_conversion_seconds": conversion_seconds,
        "raster_count": standard_artifact.get("raster_layer_count"),
        "vector_count": package_vector_count(package_report),
        "converted_raster_count": converted_package.get("raster_layer_count"),
        "manifest_size_bytes": standard_storage["total_bytes"],
        "converted_manifest_size_bytes": converted_storage["total_bytes"],
        "manifest_file_count": standard_storage["file_count"],
        "converted_manifest_file_count": converted_storage["file_count"],
        "package_size_classification": classify_package_size(
            package_report=package_report,
            standard_report=standard_report,
            combined_report=combined_report,
            conversion_report=conversion_report,
        ),
        "layer_parity": summarize_layer_parity(converted_package),
        "missing_layer_summary": summarize_missing_layers(converted_package),
        "standard_package": summarize_package_snapshot(
            standard_artifact,
            standard_report["gis_cog_readiness_status"],
            standard_storage,
            standard_runtime,
        ),
        "converted_package": summarize_package_snapshot(
            converted_package,
            combined_report["converted_package_readiness_status"],
            converted_storage,
            converted_runtime,
        ),
        "conversion": {
            "status": conversion_report.get("status", "unknown"),
            "output_root": str(converted_package_root),
            "package_file_count": conversion_report.get("package_file_count", 0),
            "package_byte_count": conversion_report.get("package_byte_count", 0),
            "copied_files": conversion_report.get("copied_files", 0),
            "all_declared_geotiffs_cog_ready": conversion_report.get("all_declared_geotiffs_cog_ready", False),
            "elapsed_seconds": conversion_seconds,
            "error": conversion_report.get("error"),
        },
        "first_gis_packaging_bottleneck": first_bottleneck,
        "claim_boundaries": claim_boundaries(),
        "source_paths": {
            "audit_helper": "scripts/audit_gis_cog_package_readiness.py",
            "conversion_helper": "scripts/convert_same_scale_package_to_cog.py",
        },
    }
    return report


def build_blocked_report(
    *,
    artifact_root: Path,
    packaged_package_root: Path,
    converted_package_root: Path,
    package_report: dict[str, Any],
    package_generation_seconds: float,
    package_html_path: Path | None,
    package_manifest_path: Path | None,
    standard_report: dict[str, Any] | None = None,
    standard_artifact: dict[str, Any] | None = None,
) -> dict[str, Any]:
    standard_report = standard_report or {"gis_cog_readiness_status": "blocked_missing_inputs", "standard_package_status": {}}
    standard_artifact = standard_artifact or {}
    missing_inputs = summarize_missing_inputs(artifact_root, standard_artifact)
    return {
        "schema_version": SCHEMA_VERSION,
        "stress_test_status": "blocked_missing_inputs",
        "artifact_root": str(artifact_root),
        "packaged_package_root": str(packaged_package_root),
        "converted_package_root": str(converted_package_root),
        "package_generation_status": package_report.get("status"),
        "package_generation_seconds": package_generation_seconds,
        "package_file_count": package_report.get("package_file_count"),
        "package_byte_count": package_report.get("package_byte_count"),
        "qa_review_html_size_bytes": path_size(package_html_path),
        "qa_review_manifest_size_bytes": path_size(package_manifest_path),
        "standard_package_readiness_status": standard_report["gis_cog_readiness_status"],
        "converted_package_readiness_status": "not_run",
        "standard_package_status": standard_report.get("standard_package_status", {}),
        "converted_package_status": {},
        "package_runtime_seconds": None,
        "package_core_output_write_seconds": None,
        "package_manifest_write_seconds": None,
        "cog_conversion_seconds": None,
        "raster_count": standard_artifact.get("raster_layer_count"),
        "converted_raster_count": None,
        "manifest_size_bytes": summarize_manifest_storage(standard_artifact)["total_bytes"],
        "converted_manifest_size_bytes": None,
        "manifest_file_count": summarize_manifest_storage(standard_artifact)["file_count"],
        "converted_manifest_file_count": None,
        "vector_count": package_vector_count(package_report),
        "package_size_classification": classify_package_size(
            package_report=package_report,
            standard_report=standard_report,
            combined_report={"converted_package_readiness_status": "not_run"},
            conversion_report={"status": "not_run"},
        ),
        "layer_parity": {
            "status": "blocked_missing_inputs",
            "standard_layer_count": standard_artifact.get("raster_layer_count"),
            "converted_layer_count": None,
            "missing_layer_count": None,
            "missing_layer_names": [],
            "extra_layer_count": None,
            "extra_layer_names": [],
        },
        "missing_layer_summary": {
            "status": "blocked_missing_inputs",
            "missing_layer_names": [],
            "extra_layer_names": [],
        },
        "standard_package": summarize_package_snapshot(
            standard_artifact,
            standard_report["gis_cog_readiness_status"],
            summarize_manifest_storage(standard_artifact),
            summarize_package_runtime(standard_artifact),
        ),
        "converted_package": {
            "artifact_id": None,
            "readiness_status": "not_run",
            "cog_package_status": "not_run",
            "raster_count": None,
            "manifest_storage": {"file_count": 0, "total_bytes": 0, "paths": []},
            "package_runtime": {"status": "not_run"},
            "blockers": [],
        },
        "conversion": {
            "status": "not_run",
            "output_root": str(converted_package_root),
            "package_file_count": 0,
            "package_byte_count": 0,
            "copied_files": 0,
            "all_declared_geotiffs_cog_ready": False,
            "elapsed_seconds": None,
            "error": None,
        },
        "first_gis_packaging_bottleneck": {
            "name": "blocked_missing_inputs",
            "reason": "package generation inputs are incomplete, so scratch conversion was not attempted",
            "measured_driver": "missing_inputs",
            "missing_inputs": missing_inputs,
            "impact_scope": "demonstration_readability",
            "affects_demonstration_readability": True,
        },
        "claim_boundaries": claim_boundaries(),
        "source_paths": {
            "audit_helper": "scripts/audit_gis_cog_package_readiness.py",
            "conversion_helper": "scripts/convert_same_scale_package_to_cog.py",
        },
    }


def summarize_package_snapshot(
    artifact: dict[str, Any],
    readiness_status: str,
    manifest_storage: dict[str, Any],
    runtime: dict[str, Any],
) -> dict[str, Any]:
    if not artifact:
        return {
            "artifact_id": None,
            "readiness_status": readiness_status,
            "cog_package_status": "not_run",
            "raster_count": None,
            "manifest_storage": manifest_storage,
            "package_runtime": runtime,
            "blockers": [],
        }
    return {
        "artifact_id": artifact.get("artifact_id"),
        "readiness_status": readiness_status,
        "cog_package_status": artifact.get("cog_package_status"),
        "raster_count": artifact.get("raster_layer_count"),
        "manifest_storage": manifest_storage,
        "package_runtime": runtime,
        "blockers": list(artifact.get("blockers") or []),
        "manifest_completeness": artifact.get("manifest_completeness"),
    }


def summarize_manifest_storage(artifact: dict[str, Any]) -> dict[str, Any]:
    if not artifact:
        return {"file_count": 0, "total_bytes": 0, "paths": []}
    candidates = [
        artifact.get("hazard_manifest_path"),
        artifact.get("map_package_manifest_path"),
        artifact.get("pilot_gis_package_manifest_path"),
    ]
    files = []
    for candidate in candidates:
        if not candidate:
            continue
        path = Path(candidate)
        if path.exists():
            files.append(path)
    return {
        "file_count": len(files),
        "total_bytes": sum(path.stat().st_size for path in files),
        "paths": [str(path) for path in files],
    }


def summarize_package_runtime(artifact: dict[str, Any]) -> dict[str, Any]:
    hazard_manifest_path = artifact.get("hazard_manifest_path") if artifact else None
    if not hazard_manifest_path:
        return {"status": "not_available"}
    path = Path(hazard_manifest_path)
    if not path.exists():
        return {"status": "missing_inputs", "path": str(path)}
    data = json.loads(path.read_text(encoding="utf-8"))
    performance = data.get("performance") or {}
    return {
        "status": "recorded" if performance.get("total_wall_seconds") is not None else "partial",
        "path": str(path),
        "total_wall_seconds": performance.get("total_wall_seconds"),
        "core_output_write_seconds": performance.get("core_output_write_seconds"),
        "manifest_write_seconds": performance.get("manifest_write_seconds"),
        "output_file_count": performance.get("output_file_count"),
        "output_bytes": performance.get("output_bytes"),
    }


def summarize_layer_parity(converted_package: dict[str, Any]) -> dict[str, Any]:
    if not converted_package:
        return {
            "status": "blocked_missing_inputs",
            "standard_layer_count": None,
            "converted_layer_count": None,
            "missing_layer_count": None,
            "missing_layer_names": [],
            "extra_layer_count": None,
            "extra_layer_names": [],
        }
    return {
        "status": converted_package.get("layer_inventory_status") or "blocked_missing_inputs",
        "standard_layer_count": converted_package.get("standard_layer_count"),
        "converted_layer_count": converted_package.get("converted_layer_count"),
        "missing_layer_count": converted_package.get("missing_layer_count"),
        "missing_layer_names": list(converted_package.get("missing_layer_names") or []),
        "extra_layer_count": converted_package.get("extra_layer_count"),
        "extra_layer_names": list(converted_package.get("extra_layer_names") or []),
    }


def summarize_missing_layers(converted_package: dict[str, Any]) -> dict[str, Any]:
    if not converted_package:
        return {"status": "blocked_missing_inputs", "missing_layer_names": [], "extra_layer_names": []}
    return {
        "status": converted_package.get("layer_inventory_status") or "blocked_missing_inputs",
        "missing_layer_names": list(converted_package.get("missing_layer_names") or []),
        "extra_layer_names": list(converted_package.get("extra_layer_names") or []),
    }


def summarize_missing_inputs(artifact_root: Path, artifact: dict[str, Any]) -> list[str]:
    if not artifact_root.exists():
        return [str(artifact_root)]
    missing_inputs: list[str] = []
    if not artifact.get("hazard_manifest_path"):
        missing_inputs.append("missing hazard manifest")
    if not artifact.get("map_package_manifest_path"):
        missing_inputs.append("missing map package manifest")
    if not artifact.get("pilot_gis_package_manifest_path"):
        missing_inputs.append("missing pilot GIS package manifest")
    return missing_inputs


def identify_first_bottleneck(
    *,
    package_report: dict[str, Any],
    standard_report: dict[str, Any],
    standard_artifact: dict[str, Any],
    combined_report: dict[str, Any],
    converted_package: dict[str, Any],
    conversion_report: dict[str, Any],
) -> dict[str, Any]:
    package_status = str(package_report.get("status") or "")
    standard_status = standard_report.get("gis_cog_readiness_status")
    converted_status = combined_report.get("converted_package_readiness_status")
    blockers = list(standard_artifact.get("blockers") or [])
    if package_status.startswith("blocked_"):
        return {
            "name": package_status,
            "reason": "package generation did not complete, so the scratch conversion was not attempted",
            "measured_driver": "package_generation",
            "package_generation_status": package_status,
            "impact_scope": "demonstration_readability",
            "affects_demonstration_readability": True,
        }
    if standard_status == "blocked_missing_inputs":
        return {
            "name": "blocked_missing_inputs",
            "reason": "standard package inputs are incomplete, so scratch conversion was not attempted",
            "measured_driver": "missing_inputs",
            "impact_scope": "demonstration_readability",
            "affects_demonstration_readability": True,
        }
    if blockers:
        converted_note = (
            "scratch conversion is ready"
            if converted_status in {"cog_package_ready", "cog_package_ready_with_scope_delta"}
            else "scratch conversion is not ready"
        )
        return {
            "name": blockers[0],
            "reason": f"standard package remains {standard_status}; {converted_note} with status {converted_status}",
            "measured_driver": "standard_package_blockers",
            "standard_root_status": standard_status,
            "converted_root_status": converted_status,
            "impact_scope": "production_packaging",
            "affects_demonstration_readability": False,
        }
    if conversion_report.get("status") not in {"cog_package_ready", "cog_package_poc_ready"}:
        return {
            "name": str(conversion_report.get("status") or "conversion_failed"),
            "reason": conversion_report.get("error") or "scratch conversion did not complete successfully",
            "measured_driver": "conversion_runner",
            "standard_root_status": standard_status,
            "converted_root_status": converted_status,
            "impact_scope": "production_packaging",
            "affects_demonstration_readability": False,
        }
    if converted_package.get("layer_inventory_status") not in {"parity_match", "no_standard_reference"}:
        return {
            "name": "scope_delta",
            "reason": "scratch conversion is ready, but its layer inventory differs from the standard root",
            "measured_driver": "layer_inventory",
            "standard_root_status": standard_status,
            "converted_root_status": converted_status,
            "impact_scope": "production_packaging",
            "affects_demonstration_readability": False,
        }
    return {
        "name": "no_blocker",
        "reason": "the largest current real output is ready for GIS review and COG conversion; no first blocker was observed",
        "measured_driver": "ready",
        "standard_root_status": standard_status,
        "converted_root_status": converted_status,
        "impact_scope": "none",
        "affects_demonstration_readability": False,
    }


def classify_package_size(
    *,
    package_report: dict[str, Any],
    standard_report: dict[str, Any],
    combined_report: dict[str, Any],
    conversion_report: dict[str, Any],
) -> dict[str, Any]:
    package_status = str(package_report.get("status") or "blocked_missing_inputs")
    standard_status = str(standard_report.get("gis_cog_readiness_status") or "blocked_missing_inputs")
    converted_status = str(combined_report.get("converted_package_readiness_status") or "not_run")
    conversion_status = str(conversion_report.get("status") or "not_run")

    if package_status.startswith("blocked_") or standard_status == "blocked_missing_inputs":
        reason = (
            "package generation inputs are incomplete, so the large-AOI package is not stress-ready"
            if package_status.startswith("blocked_")
            else "the packaged AOI root is missing required manifest fields, so COG projection is not stress-ready"
        )
        return {
            "status": "no_go",
            "reason": reason,
            "package_generation_status": package_status,
            "standard_package_status": standard_status,
            "converted_package_status": converted_status,
        }
    if (
        package_status != "map_package_ready"
        or standard_status != "gis_package_ready"
        or converted_status != "cog_package_ready"
        or conversion_status.startswith("blocked_")
    ):
        return {
            "status": "cog_blocked",
            "reason": "the package is usable for review, but at least one raster remains COG-blocked or the converted root is not fully ready",
            "package_generation_status": package_status,
            "standard_package_status": standard_status,
            "converted_package_status": converted_status,
        }
    return {
        "status": "ready",
        "reason": "the packaged AOI root and converted scratch root are both ready",
        "package_generation_status": package_status,
        "standard_package_status": standard_status,
        "converted_package_status": converted_status,
    }


def claim_boundaries() -> dict[str, Any]:
    return {
        "operational_claims_allowed": False,
        "scale_up_authorized": False,
        "distributed_execution_authorized": False,
        "annual_frequency_claims_allowed": False,
        "physical_probability_claims_allowed": False,
        "risk_exposure_vulnerability_claims_allowed": False,
    }


def render_text_report(report: dict[str, Any]) -> str:
    lines = [
        f"stress_test_status: {report['stress_test_status']}",
        f"package_generation_status: {report.get('package_generation_status')}",
        f"package_size_classification: {report.get('package_size_classification')}",
        f"standard_package_readiness_status: {report.get('standard_package_readiness_status')}",
        f"converted_package_readiness_status: {report.get('converted_package_readiness_status')}",
        f"first_gis_packaging_bottleneck_scope: {report.get('first_gis_packaging_bottleneck', {}).get('impact_scope')}",
        f"first_gis_packaging_bottleneck_affects_demo: {report.get('first_gis_packaging_bottleneck', {}).get('affects_demonstration_readability')}",
        f"package_file_count: {report.get('package_file_count')}",
        f"qa_review_html_size_bytes: {report.get('qa_review_html_size_bytes')}",
        f"package_runtime_seconds: {report.get('package_runtime_seconds')}",
        f"cog_conversion_seconds: {report.get('cog_conversion_seconds')}",
        f"raster_count: {report.get('raster_count')}",
        f"vector_count: {report.get('vector_count')}",
        f"converted_raster_count: {report.get('converted_raster_count')}",
        f"manifest_size_bytes: {report.get('manifest_size_bytes')}",
        f"converted_manifest_size_bytes: {report.get('converted_manifest_size_bytes')}",
        f"layer_parity: {report.get('layer_parity')}",
        f"missing_layer_summary: {report.get('missing_layer_summary')}",
        f"first_gis_packaging_bottleneck: {report.get('first_gis_packaging_bottleneck')}",
    ]
    missing_inputs = report.get("first_gis_packaging_bottleneck", {}).get("missing_inputs") or []
    if missing_inputs:
        lines.append(f"missing_inputs: {', '.join(missing_inputs)}")
    return "\n".join(lines) + "\n"


def package_vector_count(package_report: dict[str, Any]) -> int | None:
    vector_overlays = package_report.get("vector_overlays")
    if isinstance(vector_overlays, list):
        return len(vector_overlays)
    return None


def path_size(path: Path | None) -> int | None:
    if path is None or not path.exists():
        return None
    return path.stat().st_size


def resolve_optional_path(path_text: Any) -> Path | None:
    if not isinstance(path_text, str) or not path_text:
        return None
    return Path(path_text)


if __name__ == "__main__":  # pragma: no cover - CLI entry point.
    raise SystemExit(main())
