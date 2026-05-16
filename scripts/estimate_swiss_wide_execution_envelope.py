#!/usr/bin/env python3
"""Estimate a Swiss-wide runtime, storage, memory, and job-count envelope from measured pilot evidence.

This helper is read-only. It combines the measured Tschamut same-scale
runtime/output summaries with the Balfrin single-job sufficiency evidence and
projects conservative runtime, storage, file-count, memory, and job-count
envelopes for configurable AOI/release-zone/trajectory counts.

The helper does not submit jobs, run simulations, or authorize distributed
execution. When the requested counts exceed measured support, the report is
explicitly labeled as a no-go extrapolation. When the measured Balfrin inputs
are missing, the helper returns an explicit blocked report instead of
fabricating projections.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "swiss_wide_execution_envelope_v1"

MEASURED_SOURCE_COMMANDS = {
    "bounded_reducer_runtime_scaling": "PYENV_VERSION=system uv run python scripts/summarize_bounded_reducer_runtime_scaling.py --format json",
    "balfrin_single_job_sufficiency": "PYENV_VERSION=system uv run python scripts/summarize_balfrin_single_job_execution.py",
    "bounded_next_ensemble_feasibility_probe": "PYENV_VERSION=system uv run python scripts/summarize_bounded_next_ensemble_feasibility_probe.py --format json",
}


def _load_module(module_name: str, filename: str):
    path = ROOT / "scripts" / filename
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise SwissWideExecutionEnvelopeError(f"failed to load helper module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


RUNTIME_SCALING = _load_module("swiss_wide_envelope_runtime_scaling", "summarize_bounded_reducer_runtime_scaling.py")
SINGLE_JOB = _load_module("swiss_wide_envelope_single_job", "summarize_balfrin_single_job_execution.py")
FEASIBILITY = _load_module("swiss_wide_envelope_feasibility", "summarize_bounded_next_ensemble_feasibility_probe.py")


class SwissWideExecutionEnvelopeError(ValueError):
    """User-facing Swiss-wide envelope projection error."""


@dataclass(frozen=True)
class ProjectionInputs:
    aoi_count: int
    release_zone_count: int
    trajectory_count: int = 6


@dataclass(frozen=True)
class MeasuredCoefficients:
    measured_aoi_count: int
    measured_release_zone_count: int
    measured_trajectory_count: int
    measured_units_per_job: int
    runtime_seconds_per_unit_low: float
    runtime_seconds_per_unit_nominal: float
    runtime_seconds_per_unit_high: float
    storage_bytes_per_unit_low: float
    storage_bytes_per_unit_nominal: float
    storage_bytes_per_unit_high: float
    file_count_per_unit_low: float
    file_count_per_unit_nominal: float
    file_count_per_unit_high: float
    memory_peak_mb_low: float
    memory_peak_mb_nominal: float
    memory_peak_mb_high: float
    measurement_notes: tuple[str, ...]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aoi-count", type=int, default=1, help="number of Swiss AOIs to project")
    parser.add_argument(
        "--release-zone-count",
        type=int,
        default=10,
        help="release zones per AOI to project",
    )
    parser.add_argument(
        "--trajectory-count",
        type=int,
        default=6,
        help="trajectories per release zone to project",
    )
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    args = parser.parse_args(argv)

    report = build_report_from_available_evidence(
        ProjectionInputs(
            aoi_count=args.aoi_count,
            release_zone_count=args.release_zone_count,
            trajectory_count=args.trajectory_count,
        )
    )

    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text_report(report))
    return 0 if report["projection_status"] == "measured_within_support" else 2


@lru_cache(maxsize=1)
def load_measured_coefficients() -> MeasuredCoefficients:
    runtime_report = RUNTIME_SCALING.build_report(RUNTIME_SCALING.DEFAULT_ARTIFACTS)
    single_job_summary = SINGLE_JOB.build_summary()
    feasibility_report = FEASIBILITY.build_report()
    wall_time_evidence = dict(single_job_summary.get("wall_time_evidence") or {})
    memory_evidence = dict(single_job_summary.get("memory_evidence") or {})
    output_size_evidence = dict(single_job_summary.get("output_size_evidence") or {})

    reduced_artifact = find_artifact(runtime_report["artifacts_measured"], "target_rebuildable_reduced")
    if not reduced_artifact:
        raise SwissWideExecutionEnvelopeError("measured reduced-output artifact target_rebuildable_reduced is missing")

    reduced_evidence = dict(feasibility_report.get("measured_evidence") or {})
    if not reduced_evidence:
        raise SwissWideExecutionEnvelopeError("bounded next-ensemble feasibility evidence is missing")

    measured_units_per_job = 1 * 10 * 6
    current_gap_memory_peak_mb = require_numeric_metric(
        memory_evidence.get("current_gap_memory_peak_mb"),
        "single_job_summary.memory_evidence.current_gap_memory_peak_mb",
    )
    reproduction_validation_memory_peak_mb = require_numeric_metric(
        memory_evidence.get("reproduction_validation_memory_peak_bytes_on_darwin"),
        "single_job_summary.memory_evidence.reproduction_validation_memory_peak_bytes_on_darwin",
    ) / 1_000_000.0
    reproduction_hazard_memory_peak_mb = require_numeric_metric(
        memory_evidence.get("reproduction_hazard_memory_peak_bytes_on_darwin"),
        "single_job_summary.memory_evidence.reproduction_hazard_memory_peak_bytes_on_darwin",
    ) / 1_000_000.0
    measurement_notes = (
        "runtime coefficients are anchored to the measured same-scale reduced-output and Balfrin single-job summaries",
        "storage coefficients are anchored to the measured reduced-output, summary-only, and current-gap output summaries",
        "memory frontier is anchored to the measured Balfrin current-gap peak and reproduction validation / hazard memory sidecars",
        "job-count capacity is anchored to the measured 10-release-zone by 6-trajectory pilot footprint",
    )

    return MeasuredCoefficients(
        measured_aoi_count=1,
        measured_release_zone_count=10,
        measured_trajectory_count=6,
        measured_units_per_job=measured_units_per_job,
        runtime_seconds_per_unit_low=require_numeric_metric(
            reduced_artifact.get("validation_runtime_seconds"),
            "runtime_report.artifacts_measured.target_rebuildable_reduced.validation_runtime_seconds",
        )
        / measured_units_per_job,
        runtime_seconds_per_unit_nominal=require_numeric_metric(
            wall_time_evidence.get("current_gap_runtime_seconds"),
            "single_job_summary.wall_time_evidence.current_gap_runtime_seconds",
        )
        / measured_units_per_job,
        runtime_seconds_per_unit_high=require_numeric_metric(
            wall_time_evidence.get("reproduction_validation_wall_seconds"),
            "single_job_summary.wall_time_evidence.reproduction_validation_wall_seconds",
        )
        / measured_units_per_job,
        storage_bytes_per_unit_low=require_numeric_metric(
            reduced_evidence.get("summary_only_output_bytes"),
            "feasibility_report.measured_evidence.summary_only_output_bytes",
        )
        / measured_units_per_job,
        storage_bytes_per_unit_nominal=require_numeric_metric(
            reduced_evidence.get("rebuildable_reduced_output_bytes"),
            "feasibility_report.measured_evidence.rebuildable_reduced_output_bytes",
        )
        / measured_units_per_job,
        storage_bytes_per_unit_high=require_numeric_metric(
            output_size_evidence.get("current_gap_output_bytes"),
            "single_job_summary.output_size_evidence.current_gap_output_bytes",
        )
        / measured_units_per_job,
        file_count_per_unit_low=require_numeric_metric(
            reduced_evidence.get("summary_only_output_file_count"),
            "feasibility_report.measured_evidence.summary_only_output_file_count",
        )
        / measured_units_per_job,
        file_count_per_unit_nominal=require_numeric_metric(
            reduced_evidence.get("rebuildable_reduced_output_file_count"),
            "feasibility_report.measured_evidence.rebuildable_reduced_output_file_count",
        )
        / measured_units_per_job,
        file_count_per_unit_high=require_numeric_metric(
            output_size_evidence.get("current_gap_output_file_count"),
            "single_job_summary.output_size_evidence.current_gap_output_file_count",
        )
        / measured_units_per_job,
        memory_peak_mb_low=min(
            current_gap_memory_peak_mb,
            reproduction_validation_memory_peak_mb,
            reproduction_hazard_memory_peak_mb,
        ),
        memory_peak_mb_nominal=current_gap_memory_peak_mb,
        memory_peak_mb_high=max(
            current_gap_memory_peak_mb,
            reproduction_validation_memory_peak_mb,
            reproduction_hazard_memory_peak_mb,
        ),
        measurement_notes=measurement_notes,
    )


def build_report(inputs: ProjectionInputs, *, coefficients: MeasuredCoefficients) -> dict[str, Any]:
    validate_inputs(inputs)

    total_units = inputs.aoi_count * inputs.release_zone_count * inputs.trajectory_count
    units_per_aoi = inputs.release_zone_count * inputs.trajectory_count
    jobs_per_aoi = math.ceil(units_per_aoi / coefficients.measured_units_per_job)
    job_count = inputs.aoi_count * jobs_per_aoi

    no_go_labels = build_no_go_labels(inputs, coefficients, jobs_per_aoi, job_count)
    projection_status = "measured_within_support" if not no_go_labels else "no_go_extrapolated_beyond_measured_evidence"

    runtime_seconds = build_scalar_band(total_units, coefficients.runtime_seconds_per_unit_low,
                                        coefficients.runtime_seconds_per_unit_nominal,
                                        coefficients.runtime_seconds_per_unit_high,
                                        precision=3)
    storage_bytes = build_integer_band(total_units, coefficients.storage_bytes_per_unit_low,
                                       coefficients.storage_bytes_per_unit_nominal,
                                       coefficients.storage_bytes_per_unit_high)
    file_counts = build_integer_band(total_units, coefficients.file_count_per_unit_low,
                                     coefficients.file_count_per_unit_nominal,
                                     coefficients.file_count_per_unit_high)
    memory_peak_mb = build_absolute_band(
        coefficients.memory_peak_mb_low,
        coefficients.memory_peak_mb_nominal,
        coefficients.memory_peak_mb_high,
        precision=3,
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "measurement_status": "measured_existing_artifacts",
        "projection_status": projection_status,
        "read_only": True,
        "scale_up_authorized": False,
        "distributed_execution_authorized": False,
        "operational_claims_allowed": False,
        "input": {
            "aoi_count": inputs.aoi_count,
            "release_zone_count": inputs.release_zone_count,
            "trajectory_count": inputs.trajectory_count,
            "total_units": total_units,
        },
        "measured_support": {
            "aoi_count": coefficients.measured_aoi_count,
            "release_zone_count": coefficients.measured_release_zone_count,
            "trajectory_count": coefficients.measured_trajectory_count,
            "units_per_job": coefficients.measured_units_per_job,
            "measured_job_count": coefficients.measured_aoi_count,
        },
        "job_count": job_count,
        "jobs_per_aoi": jobs_per_aoi,
        "runtime_seconds": runtime_seconds,
        "storage_bytes": storage_bytes,
        "file_count": file_counts,
        "memory_peak_mb": memory_peak_mb,
        "uncertainty_band": {
            "runtime_seconds": band_summary(runtime_seconds),
            "storage_bytes": band_summary(storage_bytes),
            "file_count": band_summary(file_counts),
            "memory_peak_mb": band_summary(memory_peak_mb),
        },
        "no_go_labels": no_go_labels,
        "blocked_reason": build_blocked_reason(no_go_labels),
        "measurement_basis": {
            "source_commands": MEASURED_SOURCE_COMMANDS,
            "measurement_notes": list(coefficients.measurement_notes),
        },
        "per_unit_coefficients": {
            "runtime_seconds": {
                "low": coefficients.runtime_seconds_per_unit_low,
                "nominal": coefficients.runtime_seconds_per_unit_nominal,
                "high": coefficients.runtime_seconds_per_unit_high,
            },
            "storage_bytes": {
                "low": coefficients.storage_bytes_per_unit_low,
                "nominal": coefficients.storage_bytes_per_unit_nominal,
                "high": coefficients.storage_bytes_per_unit_high,
            },
            "file_count": {
                "low": coefficients.file_count_per_unit_low,
                "nominal": coefficients.file_count_per_unit_nominal,
                "high": coefficients.file_count_per_unit_high,
            },
            "memory_peak_mb": {
                "low": coefficients.memory_peak_mb_low,
                "nominal": coefficients.memory_peak_mb_nominal,
                "high": coefficients.memory_peak_mb_high,
            },
        },
    }


def build_report_from_available_evidence(inputs: ProjectionInputs) -> dict[str, Any]:
    try:
        coefficients = load_measured_coefficients()
    except SwissWideExecutionEnvelopeError as exc:
        return build_blocked_report(inputs, blocked_reason=str(exc))
    return build_report(inputs, coefficients=coefficients)


def build_blocked_report(inputs: ProjectionInputs, *, blocked_reason: str) -> dict[str, Any]:
    total_units = inputs.aoi_count * inputs.release_zone_count * inputs.trajectory_count
    empty_band = {"low": None, "nominal": None, "high": None}
    return {
        "schema_version": SCHEMA_VERSION,
        "measurement_status": "blocked_missing_inputs",
        "projection_status": "blocked_missing_inputs",
        "read_only": True,
        "scale_up_authorized": False,
        "distributed_execution_authorized": False,
        "operational_claims_allowed": False,
        "input": {
            "aoi_count": inputs.aoi_count,
            "release_zone_count": inputs.release_zone_count,
            "trajectory_count": inputs.trajectory_count,
            "total_units": total_units,
        },
        "measured_support": None,
        "job_count": None,
        "jobs_per_aoi": None,
        "runtime_seconds": empty_band,
        "storage_bytes": empty_band,
        "file_count": empty_band,
        "memory_peak_mb": empty_band,
        "uncertainty_band": {
            "runtime_seconds": band_summary(empty_band),
            "storage_bytes": band_summary(empty_band),
            "file_count": band_summary(empty_band),
            "memory_peak_mb": band_summary(empty_band),
        },
        "no_go_labels": [],
        "blocked_reason": blocked_reason,
        "measurement_basis": {
            "source_commands": MEASURED_SOURCE_COMMANDS,
            "measurement_notes": [
                "measured Balfrin evidence was unavailable, so the frontier cannot be projected",
            ],
        },
        "per_unit_coefficients": {
            "runtime_seconds": {"low": None, "nominal": None, "high": None},
            "storage_bytes": {"low": None, "nominal": None, "high": None},
            "file_count": {"low": None, "nominal": None, "high": None},
            "memory_peak_mb": {"low": None, "nominal": None, "high": None},
        },
    }


def validate_inputs(inputs: ProjectionInputs) -> None:
    if inputs.aoi_count <= 0:
        raise SwissWideExecutionEnvelopeError("aoi_count must be positive")
    if inputs.release_zone_count <= 0:
        raise SwissWideExecutionEnvelopeError("release_zone_count must be positive")
    if inputs.trajectory_count <= 0:
        raise SwissWideExecutionEnvelopeError("trajectory_count must be positive")


def build_no_go_labels(
    inputs: ProjectionInputs,
    coefficients: MeasuredCoefficients,
    jobs_per_aoi: int,
    job_count: int,
) -> list[str]:
    labels: list[str] = []
    if inputs.aoi_count > coefficients.measured_aoi_count:
        labels.append("aoi_count_exceeds_measured_support")
    if inputs.release_zone_count > coefficients.measured_release_zone_count:
        labels.append("release_zone_count_exceeds_measured_support")
    if inputs.trajectory_count > coefficients.measured_trajectory_count:
        labels.append("trajectory_count_exceeds_measured_support")
    if jobs_per_aoi > 1:
        labels.append("per_aoi_job_count_exceeds_measured_single_job_support")
    if job_count > coefficients.measured_aoi_count:
        labels.append("total_job_count_exceeds_measured_single_job_support")
    return labels


def build_blocked_reason(no_go_labels: list[str]) -> str:
    if not no_go_labels:
        return "none"
    return "extrapolation beyond measured evidence: " + ", ".join(no_go_labels)


def build_scalar_band(
    total_units: int,
    low_per_unit: float,
    nominal_per_unit: float,
    high_per_unit: float,
    *,
    precision: int,
) -> dict[str, Any]:
    return {
        "low": round(total_units * low_per_unit, precision),
        "nominal": round(total_units * nominal_per_unit, precision),
        "high": round(total_units * high_per_unit, precision),
    }


def build_absolute_band(
    low: float,
    nominal: float,
    high: float,
    *,
    precision: int,
) -> dict[str, float]:
    return {
        "low": round(low, precision),
        "nominal": round(nominal, precision),
        "high": round(high, precision),
    }


def build_integer_band(
    total_units: int,
    low_per_unit: float,
    nominal_per_unit: float,
    high_per_unit: float,
) -> dict[str, int]:
    return {
        "low": math.ceil(total_units * low_per_unit),
        "nominal": math.ceil(total_units * nominal_per_unit),
        "high": math.ceil(total_units * high_per_unit),
    }


def band_summary(band: dict[str, Any]) -> dict[str, Any]:
    low = band["low"]
    nominal = band["nominal"]
    high = band["high"]
    nominal_minus_low = None
    high_minus_nominal = None
    high_to_low_ratio = None
    if isinstance(low, (int, float)) and isinstance(nominal, (int, float)):
        nominal_minus_low = nominal - low
    if isinstance(nominal, (int, float)) and isinstance(high, (int, float)):
        high_minus_nominal = high - nominal
    if isinstance(low, (int, float)) and low:
        high_to_low_ratio = (high / low) if isinstance(high, (int, float)) else None
    return {
        "low": low,
        "nominal": nominal,
        "high": high,
        "nominal_minus_low": nominal_minus_low,
        "high_minus_nominal": high_minus_nominal,
        "high_to_low_ratio": high_to_low_ratio,
    }


def find_artifact(artifacts: list[dict[str, Any]], artifact_id: str) -> dict[str, Any] | None:
    for artifact in artifacts:
        if artifact.get("artifact_id") == artifact_id:
            return artifact
    return None


def render_text_report(report: dict[str, Any]) -> str:
    runtime = report["runtime_seconds"]
    storage = report["storage_bytes"]
    files = report["file_count"]
    memory = report["memory_peak_mb"]
    lines = [
        "Swiss-wide execution envelope",
        f"measurement_status: {report['measurement_status']}",
        f"projection_status: {report['projection_status']}",
        f"blocked_reason: {report['blocked_reason']}",
        f"aoi_count: {report['input']['aoi_count']}",
        f"release_zone_count: {report['input']['release_zone_count']}",
        f"trajectory_count: {report['input']['trajectory_count']}",
        f"total_units: {report['input']['total_units']}",
        f"jobs_per_aoi: {report['jobs_per_aoi']}",
        f"job_count: {report['job_count']}",
        "runtime_seconds:",
        f"  low: {runtime['low']}",
        f"  nominal: {runtime['nominal']}",
        f"  high: {runtime['high']}",
        "storage_bytes:",
        f"  low: {storage['low']}",
        f"  nominal: {storage['nominal']}",
        f"  high: {storage['high']}",
        "file_count:",
        f"  low: {files['low']}",
        f"  nominal: {files['nominal']}",
        f"  high: {files['high']}",
        "memory_peak_mb:",
        f"  low: {memory['low']}",
        f"  nominal: {memory['nominal']}",
        f"  high: {memory['high']}",
        f"no_go_labels: {', '.join(report['no_go_labels']) if report['no_go_labels'] else 'none'}",
        "measurement_basis:",
    ]
    for label, command in report["measurement_basis"]["source_commands"].items():
        lines.append(f"  {label}: {command}")
    for note in report["measurement_basis"]["measurement_notes"]:
        lines.append(f"  note: {note}")
    return "\n".join(lines)


def require_numeric_metric(value: Any, label: str) -> float:
    if value is None:
        raise SwissWideExecutionEnvelopeError(f"measured Balfrin evidence is missing {label}")
    return float(value)


if __name__ == "__main__":
    raise SystemExit(main())
