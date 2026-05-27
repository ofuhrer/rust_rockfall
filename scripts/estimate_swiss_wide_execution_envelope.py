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
import tempfile
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "swiss_wide_execution_envelope_v1"
SWISS_WIDE_PHASE_CHANGE_SCHEMA_VERSION = "swiss_wide_phase_change_readiness_v1"
MEASURED_BALFRIN_DEMO_RUN_ROOT = (
    "/scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/"
    "tschamut_public_balfrin_single_release_zone_v3"
)
MEASURED_TARGET_AREA_RUN_ROOT = Path(
    "/scratch/mch/olifu/rust_rockfall/probes/"
    "tschamut_public_balfrin_target_area_demo_v1/authorized_tb168_20260517"
)
GENERATED_SCENARIO_TABLE_REPEAT_COUNT = 3
GENERATED_SCENARIO_TABLE_TEMPLATE_IDS = (
    "candidate_release_point_summary_v1",
    "policy_block_family_v1",
)
GENERATED_SCENARIO_TABLE_OUTPUT_ROOT = Path("/tmp/rust_rockfall_tb185_generated_scenario_table")
SWISS_WIDE_PLANNING_ASSUMPTIONS = {
    "country_area_km2": 41_285,
    "dem_cell_size_m": 2.0,
    "dem_bytes_per_cell": 4,
    "context_product_count": 5,
    "context_bytes_per_dem_byte": 3,
    "target_cells_per_tile": 50_000_000,
    "default_aoi_count": 26,
    "release_zones_per_aoi": 10,
    "trajectories_per_release_zone": 6,
}
DEFAULT_NATIONAL_TILING_INVENTORY = ROOT / "archive/task_reports/swiss_national_tiling_inventory_tb607.json"
DEFAULT_NATIONAL_TILE_CHUNK_MAPPING = ROOT / "archive/task_reports/swiss_national_tile_chunk_mapping_tb608.json"

MEASURED_SOURCE_COMMANDS = {
    "bounded_reducer_runtime_scaling": "PYENV_VERSION=system uv run python scripts/summarize_bounded_reducer_runtime_scaling.py --format json",
    "balfrin_single_job_sufficiency": "PYENV_VERSION=system uv run python scripts/summarize_balfrin_single_job_execution.py",
    "bounded_next_ensemble_feasibility_probe": "PYENV_VERSION=system uv run python scripts/summarize_bounded_next_ensemble_feasibility_probe.py --format json",
    "multi_zone_manifest_pressure_ladder": (
        "PYENV_VERSION=system uv run python scripts/summarize_multi_zone_reducer_pressure.py "
        "--measure-manifest-pressure-ladder --format json"
    ),
    "balfrin_probe_metrics_report": (
        "PYENV_VERSION=system uv run python scripts/summarize_balfrin_probe_metrics_report.py "
        "--run-root /scratch/mch/olifu/rust_rockfall/probes/"
        "tschamut_public_balfrin_target_area_demo_v1/authorized_tb168_20260517 --format json"
    ),
    "hazard_throughput_probe_metrics_report": (
        "PYENV_VERSION=system uv run python scripts/summarize_balfrin_probe_metrics_report.py "
        "--run-root /scratch/mch/olifu/rust_rockfall/probes/balfrin-demo/"
        "tschamut_public_balfrin_multi_release_zone_tb603_20260526 --format json"
    ),
    "candidate_source_zone_scenarios": (
        "PYENV_VERSION=system uv run python scripts/generate_candidate_source_zone_scenarios.py "
        "--candidate-repeat-count 3 --template-ids candidate_release_point_summary_v1,policy_block_family_v1 "
        "--output-root /tmp/rust_rockfall_tb185_generated_scenario_table --format json"
    ),
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
MANIFEST_PRESSURE = _load_module(
    "swiss_wide_envelope_manifest_pressure",
    "summarize_multi_zone_reducer_pressure.py",
)
TARGET_AREA_PROBE = _load_module("swiss_wide_envelope_target_area_probe", "summarize_balfrin_probe_metrics_report.py")
EVIDENCE_BUNDLE = _load_module("swiss_wide_envelope_evidence_bundle", "summarize_balfrin_evidence_bundle.py")
SCENARIO_GENERATOR = _load_module(
    "swiss_wide_envelope_scenario_generator",
    "generate_candidate_source_zone_scenarios.py",
)


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
    bounded_probe_recommendation_status: str | None
    multi_zone_manifest_pressure_ladder: dict[str, Any] | None = None
    diagnostic_release_zone_count: int | None = None
    diagnostic_runtime_seconds_per_zone: float | None = None
    diagnostic_output_bytes_per_zone: float | None = None
    diagnostic_file_count_per_zone: float | None = None
    diagnostic_manifest_bytes_per_zone: float | None = None
    diagnostic_memory_peak_mb: float | None = None
    diagnostic_repeatability_status: str | None = None
    diagnostic_repeatability_bounds: dict[str, Any] | None = None
    diagnostic_run_root: str | None = None
    diagnostic_job_id: str | None = None


@dataclass(frozen=True)
class PlanningCaseSpec:
    case_id: str
    scale_label: str
    aoi_count: int
    release_zone_count: int
    trajectory_count: int
    decision: str
    decision_reason: str
    evidence_class: str
    blocker_category: str


CANONICAL_PLANNING_CASES = (
    PlanningCaseSpec(
        case_id="10_zone",
        scale_label="10 release zones",
        aoi_count=1,
        release_zone_count=10,
        trajectory_count=6,
        decision="next_probe",
        decision_reason="Matches the measured Balfrin release-zone cardinality and remains the authorized next-probe boundary.",
        evidence_class="measured_hazard_boundary",
        blocker_category="reducer_pressure",
    ),
    PlanningCaseSpec(
        case_id="16_zone",
        scale_label="16 release zones",
        aoi_count=1,
        release_zone_count=16,
        trajectory_count=6,
        decision="measured_diagnostic",
        decision_reason="Measured as a single-node/postproc diagnostic reducer-pressure run; not a hazard-throughput or physical-probability result.",
        evidence_class="measured_diagnostic_postproc",
        blocker_category="scientific_evidence",
    ),
    PlanningCaseSpec(
        case_id="24_zone",
        scale_label="24 release zones",
        aoi_count=1,
        release_zone_count=24,
        trajectory_count=6,
        decision="measured_diagnostic",
        decision_reason="Measured and repeated as a single-node/postproc diagnostic reducer-pressure run; this is the repeatability anchor below the current diagnostic ceiling.",
        evidence_class="measured_repeatable_diagnostic_postproc",
        blocker_category="queue_policy",
    ),
    PlanningCaseSpec(
        case_id="32_zone",
        scale_label="32 release zones",
        aoi_count=1,
        release_zone_count=32,
        trajectory_count=6,
        decision="measured_diagnostic",
        decision_reason="Measured as a single-node/postproc diagnostic reducer-pressure run below the current 100-zone diagnostic ceiling.",
        evidence_class="measured_diagnostic_postproc",
        blocker_category="queue_policy",
    ),
    PlanningCaseSpec(
        case_id="100_zone",
        scale_label="100 release zones",
        aoi_count=1,
        release_zone_count=100,
        trajectory_count=6,
        decision="measured_diagnostic",
        decision_reason="Measured as a single-node/postproc diagnostic reducer-pressure run; this is diagnostic performance evidence, not hazard-throughput or physical-probability evidence.",
        evidence_class="measured_diagnostic_postproc",
        blocker_category="scientific_validation_and_hazard_throughput",
    ),
    PlanningCaseSpec(
        case_id="regional",
        scale_label="regional workflows",
        aoi_count=10,
        release_zone_count=10,
        trajectory_count=6,
        decision="no_go",
        decision_reason="Multi-AOI scheduling and reducer fan-out exceed the current single-job evidence boundary.",
        evidence_class="deferred_multi_aoi_projection",
        blocker_category="queue_policy",
    ),
    PlanningCaseSpec(
        case_id="swiss_wide",
        scale_label="Switzerland-scale planning envelope",
        aoi_count=26,
        release_zone_count=10,
        trajectory_count=6,
        decision="no_go",
        decision_reason="Switzerland-wide AOI multiplicity remains beyond measured support and requires explicit authorization before any larger run.",
        evidence_class="deferred_swiss_wide_projection",
        blocker_category="missing_scientific_evidence",
    ),
)


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
    parser.add_argument(
        "--national-data-inventory-smoke",
        action="store_true",
        help="Summarize the current share-safe national data and tile/chunk inventory without building the execution envelope.",
    )
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    args = parser.parse_args(argv)

    if args.national_data_inventory_smoke:
        report = build_national_data_inventory_smoke()
        exit_status = 0
    else:
        report = build_report_from_available_evidence(
            ProjectionInputs(
                aoi_count=args.aoi_count,
                release_zone_count=args.release_zone_count,
                trajectory_count=args.trajectory_count,
            )
        )
        exit_status = 0 if report["projection_status"] == "measured_within_support" else 2

    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    elif args.national_data_inventory_smoke:
        print(render_national_data_inventory_smoke_text(report))
    else:
        print(render_text_report(report))
    return exit_status


def _load_json_file(path: Path, label: str) -> dict[str, Any]:
    if not path.exists():
        raise SwissWideExecutionEnvelopeError(f"{label} is missing: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SwissWideExecutionEnvelopeError(f"{label} must be a JSON object: {path}")
    return payload


def _int_or_none(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def build_national_data_inventory_smoke(
    *,
    inventory_path: Path = DEFAULT_NATIONAL_TILING_INVENTORY,
    chunk_mapping_path: Path = DEFAULT_NATIONAL_TILE_CHUNK_MAPPING,
) -> dict[str, Any]:
    inventory = _load_json_file(inventory_path, "national tiling inventory")
    mapping = _load_json_file(chunk_mapping_path, "national tile chunk mapping")

    products = [dict(row) for row in inventory.get("products") or [] if isinstance(row, dict)]
    required_products = [
        product
        for product in products
        if str(product.get("role") or "").startswith("mandatory")
        or product.get("product_id") in {"swissalti3d_2m", "swissimage_10cm_or_25cm", "swisstlm3d"}
    ]
    missing_products = [
        str(product.get("product_id"))
        for product in products
        if str(product.get("current_cache_status") or "missing") != "ready"
    ]
    estimated_required_input_bytes = 0
    for product in required_products:
        for key in (
            "estimated_raw_bytes_national_float32",
            "estimated_raw_bytes_national_rgb_25cm",
            "estimated_raw_bytes_national",
        ):
            value = _int_or_none(product.get(key))
            if value is not None:
                estimated_required_input_bytes += value
                break

    grid = dict(inventory.get("tiling_grid") or {})
    chunking = dict(mapping.get("chunking_policy") or {})
    national_expected_input_bytes = dict(mapping.get("national_expected_input_bytes") or {})
    chunks = mapping.get("chunks") if isinstance(mapping.get("chunks"), list) else []
    merge_groups = mapping.get("merge_groups") if isinstance(mapping.get("merge_groups"), list) else []
    chunk_count = _int_or_none(chunking.get("chunk_count")) or len(chunks)
    merge_group_count = _int_or_none(chunking.get("merge_group_count")) or len(merge_groups)
    tile_count = _int_or_none(chunking.get("tile_count")) or _int_or_none(grid.get("national_1km_tile_count_estimate"))
    validation = dict(mapping.get("validation") or {})
    validation_ready = bool(validation) and all(bool(value) for value in validation.values())
    terrain_product = next((product for product in products if product.get("product_id") == "swissalti3d_2m"), {})
    first_chunk = dict(chunks[0]) if chunks else {}
    last_chunk = dict(chunks[-1]) if chunks else {}

    planning_only = bool(tile_count and chunk_count and merge_group_count and validation_ready)
    data_cache_ready = not missing_products
    inventory_sufficient_for_planning_only = planning_only and not data_cache_ready

    return {
        "schema_version": "swiss_national_data_inventory_smoke_v1",
        "status": "planning_inventory_ready_missing_cache" if inventory_sufficient_for_planning_only else "blocked_missing_inventory",
        "inventory_path": str(inventory_path),
        "chunk_mapping_path": str(chunk_mapping_path),
        "inventory_status": inventory.get("inventory_status"),
        "mapping_status": mapping.get("mapping_status"),
        "tile_count": tile_count,
        "chunk_count": chunk_count,
        "merge_group_count": merge_group_count,
        "chunk_size_tiles": _int_or_none(chunking.get("chunk_size_tiles")),
        "last_chunk_tile_count": _int_or_none(last_chunk.get("tile_count")),
        "terrain_product_tile_count": _int_or_none(dict(terrain_product).get("tile_count_estimate")),
        "estimated_required_input_bytes": estimated_required_input_bytes,
        "national_expected_input_bytes": national_expected_input_bytes,
        "missing_products": missing_products,
        "missing_product_count": len(missing_products),
        "mapping_validation": validation,
        "mapping_validation_ready": validation_ready,
        "first_chunk_id": first_chunk.get("chunk_id"),
        "last_chunk_id": last_chunk.get("chunk_id"),
        "inventory_sufficient_for_planning_only": inventory_sufficient_for_planning_only,
        "data_cache_ready": data_cache_ready,
        "execution_ready": False,
        "claim_boundary": (
            "share-safe inventory and chunk planning only; no national data cache, Swiss-wide execution, "
            "distributed execution, operational, annual, physical-probability, risk, exposure, or vulnerability claim"
        ),
    }


def render_national_data_inventory_smoke_text(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"national_data_inventory_smoke: {report.get('status')}",
            f"tile_count: {report.get('tile_count')}",
            f"chunk_count: {report.get('chunk_count')}",
            f"merge_group_count: {report.get('merge_group_count')}",
            f"estimated_required_input_bytes: {report.get('estimated_required_input_bytes')}",
            f"missing_product_count: {report.get('missing_product_count')}",
            f"missing_products: {', '.join(report.get('missing_products') or [])}",
            f"inventory_sufficient_for_planning_only: {report.get('inventory_sufficient_for_planning_only')}",
        ]
    )


@lru_cache(maxsize=1)
def load_measured_coefficients() -> MeasuredCoefficients:
    try:
        runtime_report = RUNTIME_SCALING.build_report(RUNTIME_SCALING.DEFAULT_ARTIFACTS)
        single_job_summary = SINGLE_JOB.build_summary()
        feasibility_report = FEASIBILITY.build_report()
        with tempfile.TemporaryDirectory(dir="/tmp", prefix="swiss_envelope_reducer_ladder_") as tmpdir:
            manifest_pressure_ladder = MANIFEST_PRESSURE.build_manifest_pressure_ladder_report(
                ladder_root=Path(tmpdir) / "ladder"
            )
    except Exception as exc:  # Helper modules use their own user-facing error classes.
        raise SwissWideExecutionEnvelopeError(f"measured input helper failed: {exc}") from exc
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
    diagnostic_evidence = load_latest_diagnostic_evidence()
    hazard_throughput_evidence = load_latest_hazard_throughput_evidence()
    repeatability = load_diagnostic_repeatability_summary()
    diagnostic_release_zone_count = diagnostic_evidence.get("release_zone_count")
    diagnostic_runtime_seconds_per_zone = build_ratio(
        diagnostic_evidence.get("reducer_wall_time_seconds"),
        diagnostic_release_zone_count,
        precision=6,
    )
    diagnostic_output_bytes_per_zone = build_ratio(
        diagnostic_evidence.get("diagnostic_output_bytes"),
        diagnostic_release_zone_count,
        precision=6,
    )
    diagnostic_file_count_per_zone = build_ratio(
        diagnostic_evidence.get("diagnostic_output_file_count"),
        diagnostic_release_zone_count,
        precision=6,
    )
    diagnostic_manifest_bytes_per_zone = build_ratio(
        diagnostic_evidence.get("diagnostic_manifest_size_bytes"),
        diagnostic_release_zone_count,
        precision=6,
    )
    measurement_notes = (
        "runtime coefficients are anchored to the measured same-scale reduced-output and Balfrin single-job summaries",
        "storage coefficients are anchored to the measured reduced-output, summary-only, and current-gap output summaries",
        "memory frontier is anchored to the measured Balfrin current-gap peak and reproduction validation / hazard memory sidecars",
        "job-count capacity is anchored to the measured 10-release-zone by 6-trajectory pilot footprint",
        "multi-zone manifest pressure is anchored to the measured 2/4/8/12-zone full-vs-compact ladder, which recommends compact as the default manifest mode",
        "diagnostic reducer-pressure coefficients are anchored to the latest measured Balfrin diagnostic run record and kept separate from hazard-throughput projections",
        "hazard-throughput support is anchored to the measured TB-680 24-zone Balfrin postproc profile and kept separate from diagnostic reducer-pressure evidence",
    )
    measured_release_zone_count = max(
        10,
        int(hazard_throughput_evidence.get("release_zone_count"))
        if isinstance(hazard_throughput_evidence.get("release_zone_count"), int)
        else 10,
    )

    return MeasuredCoefficients(
        measured_aoi_count=1,
        measured_release_zone_count=measured_release_zone_count,
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
        bounded_probe_recommendation_status=feasibility_report.get("bounded_probe_recommendation_status"),
        multi_zone_manifest_pressure_ladder=manifest_pressure_ladder,
        diagnostic_release_zone_count=diagnostic_release_zone_count
        if isinstance(diagnostic_release_zone_count, int)
        else None,
        diagnostic_runtime_seconds_per_zone=diagnostic_runtime_seconds_per_zone,
        diagnostic_output_bytes_per_zone=diagnostic_output_bytes_per_zone,
        diagnostic_file_count_per_zone=diagnostic_file_count_per_zone,
        diagnostic_manifest_bytes_per_zone=diagnostic_manifest_bytes_per_zone,
        diagnostic_memory_peak_mb=diagnostic_evidence.get("memory_peak_mb")
        if isinstance(diagnostic_evidence.get("memory_peak_mb"), (int, float))
        else None,
        diagnostic_repeatability_status=repeatability.get("status"),
        diagnostic_repeatability_bounds=repeatability.get("bounds"),
        diagnostic_run_root=diagnostic_evidence.get("run_root")
        if isinstance(diagnostic_evidence.get("run_root"), str)
        else None,
        diagnostic_job_id=diagnostic_evidence.get("slurm_job_id")
        if isinstance(diagnostic_evidence.get("slurm_job_id"), str)
        else None,
    )


def load_latest_diagnostic_evidence() -> dict[str, Any]:
    paths = tuple(
        dict.fromkeys(
            (
                EVIDENCE_BUNDLE.DEFAULT_BALFRIN_DIAGNOSTIC_RUN_RECORD,
                *EVIDENCE_BUNDLE.DEFAULT_BALFRIN_DIAGNOSTIC_RUN_RECORDS,
            )
        )
    )
    rows: list[dict[str, Any]] = []
    for path in paths:
        record = EVIDENCE_BUNDLE.load_json_object(path)
        if record is None:
            continue
        evidence = EVIDENCE_BUNDLE.build_multi_zone_balfrin_evidence(record)
        if evidence.get("status") == "measured" and evidence.get("output_mode") == "diagnostic_reducer_pressure":
            rows.append(evidence)
    rows.append(dict(EVIDENCE_BUNDLE.TB665_DIAGNOSTIC_PROBE))
    rows.sort(key=lambda row: int(row.get("release_zone_count") or 0))
    return rows[-1] if rows else {}


def load_latest_hazard_throughput_evidence() -> dict[str, Any]:
    return EVIDENCE_BUNDLE.build_latest_hazard_throughput_evidence()


def load_diagnostic_repeatability_summary() -> dict[str, Any]:
    rows = []
    for path in EVIDENCE_BUNDLE.DEFAULT_BALFRIN_24_ZONE_REPEATABILITY_RUN_RECORDS:
        record = EVIDENCE_BUNDLE.load_json_object(path)
        if record is None:
            continue
        evidence = EVIDENCE_BUNDLE.build_multi_zone_balfrin_evidence(record)
        if evidence.get("status") == "measured" and evidence.get("output_mode") == "diagnostic_reducer_pressure":
            rows.append(
                {
                    "runtime_seconds": evidence.get("reducer_wall_time_seconds"),
                    "memory_peak_mb": evidence.get("memory_peak_mb"),
                    "output_file_count": evidence.get("diagnostic_output_file_count"),
                    "output_bytes": evidence.get("diagnostic_output_bytes"),
                    "manifest_bytes": evidence.get("diagnostic_manifest_size_bytes"),
                    "release_zone_count": evidence.get("release_zone_count"),
                }
            )
    release_zone_counts = {row.get("release_zone_count") for row in rows}
    same_size = len(release_zone_counts) == 1
    return {
        "status": "measured_repeatability_pair" if len(rows) >= 2 and same_size else "waiting_for_repeatability_pair",
        "run_count": len(rows),
        "release_zone_count": next(iter(release_zone_counts)) if same_size and release_zone_counts else None,
        "bounds": {
            "runtime_seconds": build_numeric_bounds(rows, "runtime_seconds"),
            "memory_peak_mb": build_numeric_bounds(rows, "memory_peak_mb"),
            "output_file_count": build_numeric_bounds(rows, "output_file_count"),
            "output_bytes": build_numeric_bounds(rows, "output_bytes"),
            "manifest_bytes": build_numeric_bounds(rows, "manifest_bytes"),
        },
    }


def build_numeric_bounds(rows: list[dict[str, Any]], key: str) -> dict[str, Any]:
    values = [float(row[key]) for row in rows if isinstance(row.get(key), (int, float))]
    if not values:
        return {"min": None, "median": None, "max": None, "spread": None}
    ordered = sorted(values)
    middle = len(ordered) // 2
    median = ordered[middle] if len(ordered) % 2 else (ordered[middle - 1] + ordered[middle]) / 2
    return {
        "min": min(values),
        "median": round(median, 6),
        "max": max(values),
        "spread": round(max(values) - min(values), 6),
    }


@lru_cache(maxsize=1)
def load_canonical_bundle_report() -> dict[str, Any]:
    report = EVIDENCE_BUNDLE.build_report()
    bundle_status = str(report.get("bundle_status") or "blocked_missing_inputs")
    if bundle_status == "blocked_missing_inputs":
        raise SwissWideExecutionEnvelopeError("canonical Balfrin evidence bundle is blocked")
    return report


@lru_cache(maxsize=1)
def load_target_area_probe_report() -> dict[str, Any]:
    if not MEASURED_TARGET_AREA_RUN_ROOT.exists():
        return {
            "schema_version": "balfrin_probe_metrics_report_v1",
            "report_status": "blocked_missing_run_root",
            "run_root_status": "missing_run_root",
            "run_root": str(MEASURED_TARGET_AREA_RUN_ROOT),
            "missing_run_root_reason": f"run root does not exist: {MEASURED_TARGET_AREA_RUN_ROOT}",
            "metrics_contract_status": "blocked_missing_run_root",
            "metrics_contract_missing_metrics": [],
            "metrics_contract_ancillary_unavailable_metrics": [],
            "metric_statuses": {},
            "metrics_remediation": {},
            "summary": "Balfrin target-area probe metrics are blocked because the measured run root is missing.",
            "source_paths": {
                "run_root": str(MEASURED_TARGET_AREA_RUN_ROOT),
                "output_root": None,
                "probe_manifest_path": None,
                "command_plan_path": None,
                "hazard_manifest_path": None,
            },
            "wall_time_seconds": None,
            "memory_peak_mb": None,
            "validation_output": {},
            "hazard_output": {},
        }
    report = TARGET_AREA_PROBE.build_report(run_root=MEASURED_TARGET_AREA_RUN_ROOT)
    report_status = str(report.get("report_status") or "blocked_missing_run_root")
    if report_status == "blocked_missing_run_root":
        return report
    return report


@lru_cache(maxsize=1)
def load_generated_scenario_table_evidence() -> dict[str, Any]:
    report = SCENARIO_GENERATOR.build_report(
        policy_path=ROOT / "validation/policies/tschamut_public_source_scenario_policy_v1.yaml",
        release_points_path=ROOT / "data/processed/swisstopo/tschamut_public_pilot/input/release_points_lv95.csv",
        output_root=GENERATED_SCENARIO_TABLE_OUTPUT_ROOT,
        candidate_repeat_count=GENERATED_SCENARIO_TABLE_REPEAT_COUNT,
        template_ids=GENERATED_SCENARIO_TABLE_TEMPLATE_IDS,
    )
    if str(report.get("stress_test_status") or "blocked_missing_inputs") == "blocked_missing_inputs":
        raise SwissWideExecutionEnvelopeError("generated scenario-table evidence is blocked")
    return report


def build_ratio(numerator: Any, denominator: Any, *, precision: int = 3) -> float | None:
    if not isinstance(numerator, (int, float)):
        return None
    if not isinstance(denominator, (int, float)) or denominator == 0:
        return None
    return round(float(numerator) / float(denominator), precision)


def build_rebuildability_cost(
    *,
    projected_storage_bytes: dict[str, Any],
    projected_file_count: dict[str, Any],
    single_job_summary: dict[str, Any],
    feasibility_report: dict[str, Any],
    target_area_probe_report: dict[str, Any],
) -> dict[str, Any]:
    measured = dict(feasibility_report.get("measured_evidence") or {})
    current_gap_output = dict(single_job_summary.get("output_size_evidence") or {})
    target_validation_output = dict(target_area_probe_report.get("validation_output") or {})
    target_hazard_output = dict(target_area_probe_report.get("hazard_output") or {})
    target_area_available = target_area_probe_report.get("report_status") != "blocked_missing_run_root"
    projected_storage_nominal = projected_storage_bytes.get("nominal")
    projected_files_nominal = projected_file_count.get("nominal")
    return {
        "projected_storage_bytes": projected_storage_nominal,
        "projected_file_count": projected_files_nominal,
        "current_gap_output_bytes": current_gap_output.get("current_gap_output_bytes"),
        "current_gap_output_file_count": current_gap_output.get("current_gap_output_file_count"),
        "rebuildable_reduced_output_bytes": measured.get("rebuildable_reduced_output_bytes"),
        "rebuildable_reduced_output_file_count": measured.get("rebuildable_reduced_output_file_count"),
        "target_validation_output_bytes": target_validation_output.get("bytes"),
        "target_validation_output_file_count": target_validation_output.get("file_count"),
        "target_hazard_output_bytes": target_hazard_output.get("bytes"),
        "target_hazard_output_file_count": target_hazard_output.get("file_count"),
        "target_area_evidence_available": target_area_available,
        "bounded_relative_to_target_validation": (
            target_area_available
            and projected_storage_nominal is not None
            and target_validation_output.get("bytes") is not None
            and projected_storage_nominal <= target_validation_output.get("bytes")
        ),
        "bounded_relative_to_target_hazard": (
            target_area_available
            and projected_storage_nominal is not None
            and target_hazard_output.get("bytes") is not None
            and projected_storage_nominal <= target_hazard_output.get("bytes")
        ),
        "output_byte_ratio_to_target_validation": build_ratio(
            projected_storage_nominal,
            target_validation_output.get("bytes"),
        ),
        "output_file_ratio_to_target_validation": build_ratio(
            projected_files_nominal,
            target_validation_output.get("file_count"),
        ),
        "output_byte_ratio_to_target_hazard": build_ratio(
            projected_storage_nominal,
            target_hazard_output.get("bytes"),
        ),
        "output_file_ratio_to_target_hazard": build_ratio(
            projected_files_nominal,
            target_hazard_output.get("file_count"),
        ),
        "output_byte_ratio_to_current_gap": build_ratio(
            projected_storage_nominal,
            current_gap_output.get("current_gap_output_bytes"),
        ),
        "output_file_ratio_to_current_gap": build_ratio(
            projected_files_nominal,
            current_gap_output.get("current_gap_output_file_count"),
        ),
        "output_byte_ratio_to_rebuildable_reduced": build_ratio(
            projected_storage_nominal,
            measured.get("rebuildable_reduced_output_bytes"),
        ),
        "output_file_ratio_to_rebuildable_reduced": build_ratio(
            projected_files_nominal,
            measured.get("rebuildable_reduced_output_file_count"),
        ),
        "missing_target_area_evidence": not target_area_available,
    }


def build_bottleneck_labels(
    *,
    inputs: ProjectionInputs,
    coefficients: MeasuredCoefficients,
    job_count: int,
    jobs_per_aoi: int,
    projected_storage_bytes: dict[str, Any],
    projected_memory_peak_mb: dict[str, Any],
    single_job_summary: dict[str, Any],
    target_area_probe_report: dict[str, Any],
    generated_scenario_table_report: dict[str, Any],
) -> dict[str, Any]:
    current_gap_output = dict(single_job_summary.get("output_size_evidence") or {})
    target_validation_output = dict(target_area_probe_report.get("validation_output") or {})
    target_hazard_output = dict(target_area_probe_report.get("hazard_output") or {})
    target_area_available = target_area_probe_report.get("report_status") != "blocked_missing_run_root"
    scenario_manifest = dict(generated_scenario_table_report.get("scenario_table_manifest") or {})
    first_scaling_bottleneck = dict(generated_scenario_table_report.get("first_scaling_bottleneck") or {})
    manifest_pressure_label = str(first_scaling_bottleneck.get("name") or "manifest_size")
    validation_label = (
        "validation_output_size_exceeds_target_validation"
        if target_area_available
        and projected_storage_bytes.get("nominal") is not None
        and target_validation_output.get("bytes") is not None
        and projected_storage_bytes["nominal"] > target_validation_output["bytes"]
        else (
            "validation_output_target_area_unavailable"
            if not target_area_available
            else "validation_output_size_within_target_validation"
        )
    )
    hazard_label = (
        "hazard_output_size_exceeds_target_hazard"
        if target_area_available
        and projected_storage_bytes.get("nominal") is not None
        and target_hazard_output.get("bytes") is not None
        and projected_storage_bytes["nominal"] > target_hazard_output["bytes"]
        else (
            "hazard_output_target_area_unavailable"
            if not target_area_available
            else "hazard_output_size_within_target_hazard"
        )
    )
    reducer_merge_label = (
        "reducer_merge_multi_job_pressure"
        if job_count > 1 or jobs_per_aoi > 1
        else "reducer_merge_single_job_supported"
    )
    memory_label = (
        "memory_peak_within_measured_single_job"
        if projected_memory_peak_mb.get("high") is not None
        and coefficients.memory_peak_mb_high is not None
        and projected_memory_peak_mb["high"] <= coefficients.memory_peak_mb_high
        else "memory_peak_exceeds_measured_single_job"
    )
    scheduler_label = (
        "scheduler_practicality_single_job_supported"
        if job_count == 1
        else "scheduler_practicality_requires_authorization"
    )
    manifest_count_label = (
        "manifest_size"
        if manifest_pressure_label == "manifest_size"
        else "manifest_row_fan_out"
    )
    return {
        "validation_output": {
            "label": validation_label,
            "evidence": {
                "projected_storage_bytes": projected_storage_bytes.get("nominal"),
                "current_gap_output_bytes": current_gap_output.get("current_gap_output_bytes"),
                "target_validation_output_bytes": target_validation_output.get("bytes"),
                "target_area_evidence_available": target_area_available,
            },
        },
        "hazard_output": {
            "label": hazard_label,
            "evidence": {
                "projected_storage_bytes": projected_storage_bytes.get("nominal"),
                "target_hazard_output_bytes": target_hazard_output.get("bytes"),
                "target_area_evidence_available": target_area_available,
            },
        },
        "reducer_merge": {
            "label": reducer_merge_label,
            "evidence": {
                "job_count": job_count,
                "jobs_per_aoi": jobs_per_aoi,
                "measured_job_count": coefficients.measured_aoi_count,
            },
        },
        "manifest_count": {
            "label": manifest_count_label,
            "evidence": {
                "candidate_repeat_count": generated_scenario_table_report.get("candidate_repeat_count"),
                "candidate_release_zone_record_count": generated_scenario_table_report.get(
                    "candidate_release_zone_record_count"
                ),
                "scenario_row_count": generated_scenario_table_report.get("scenario_row_count"),
                "first_scaling_bottleneck": first_scaling_bottleneck,
            },
        },
        "memory": {
            "label": memory_label,
            "evidence": {
                "projected_memory_peak_mb": projected_memory_peak_mb.get("nominal"),
                "measured_memory_peak_mb": coefficients.memory_peak_mb_nominal,
                "current_gap_memory_peak_mb": current_gap_output.get("current_gap_memory_peak_mb"),
            },
        },
        "scheduler_practicality": {
            "label": scheduler_label,
            "evidence": {
                "job_count": job_count,
                "aoi_count": inputs.aoi_count,
                "release_zone_count": inputs.release_zone_count,
                "scenario_table_manifest_status": scenario_manifest.get("table_status"),
            },
        },
    }


def build_case_projection(
    *,
    spec: PlanningCaseSpec,
    coefficients: MeasuredCoefficients,
    single_job_summary: dict[str, Any],
    feasibility_report: dict[str, Any],
    target_area_probe_report: dict[str, Any],
    generated_scenario_table_report: dict[str, Any],
) -> dict[str, Any]:
    inputs = ProjectionInputs(
        aoi_count=spec.aoi_count,
        release_zone_count=spec.release_zone_count,
        trajectory_count=spec.trajectory_count,
    )
    validate_inputs(inputs)

    total_units = inputs.aoi_count * inputs.release_zone_count * inputs.trajectory_count
    units_per_aoi = inputs.release_zone_count * inputs.trajectory_count
    jobs_per_aoi = math.ceil(units_per_aoi / coefficients.measured_units_per_job)
    job_count = inputs.aoi_count * jobs_per_aoi
    runtime_seconds = build_scalar_band(
        total_units,
        coefficients.runtime_seconds_per_unit_low,
        coefficients.runtime_seconds_per_unit_nominal,
        coefficients.runtime_seconds_per_unit_high,
        precision=3,
    )
    storage_bytes = build_integer_band(
        total_units,
        coefficients.storage_bytes_per_unit_low,
        coefficients.storage_bytes_per_unit_nominal,
        coefficients.storage_bytes_per_unit_high,
    )
    file_count = build_integer_band(
        total_units,
        coefficients.file_count_per_unit_low,
        coefficients.file_count_per_unit_nominal,
        coefficients.file_count_per_unit_high,
    )
    memory_peak_mb = build_absolute_band(
        coefficients.memory_peak_mb_low,
        coefficients.memory_peak_mb_nominal,
        coefficients.memory_peak_mb_high,
        precision=3,
    )
    planning_labels = {
        "no_go": "no_go_extrapolated_beyond_measured_evidence" if spec.decision == "no_go" else "no_go_not_triggered",
        "defer": "defer_scale_up_authorized_false" if spec.decision == "defer" else "defer_not_triggered",
        "allowed_next_probe": (
            "allowed_next_probe_measured_existing_artifacts"
            if spec.decision == "next_probe"
            else "allowed_next_probe_not_triggered"
        ),
        "measured_diagnostic": (
            "measured_diagnostic_single_node_postproc"
            if spec.decision == "measured_diagnostic"
            and isinstance(coefficients.diagnostic_release_zone_count, int)
            and spec.release_zone_count <= coefficients.diagnostic_release_zone_count
            else "measured_diagnostic_not_triggered"
        ),
    }
    diagnostic_support_available = (
        isinstance(coefficients.diagnostic_release_zone_count, int)
        and spec.release_zone_count <= coefficients.diagnostic_release_zone_count
    )
    diagnostic_projection = None
    if spec.decision == "measured_diagnostic" and diagnostic_support_available:
        diagnostic_projection = {
            "release_zone_count": spec.release_zone_count,
            "diagnostic_ceiling_release_zone_count": coefficients.diagnostic_release_zone_count,
            "runtime_seconds_per_zone": coefficients.diagnostic_runtime_seconds_per_zone,
            "output_bytes_per_zone": coefficients.diagnostic_output_bytes_per_zone,
            "file_count_per_zone": coefficients.diagnostic_file_count_per_zone,
            "manifest_bytes_per_zone": coefficients.diagnostic_manifest_bytes_per_zone,
            "runtime_seconds_nominal": round(
                spec.release_zone_count * coefficients.diagnostic_runtime_seconds_per_zone,
                3,
            )
            if coefficients.diagnostic_runtime_seconds_per_zone is not None
            else None,
            "output_bytes_nominal": math.ceil(
                spec.release_zone_count * coefficients.diagnostic_output_bytes_per_zone
            )
            if coefficients.diagnostic_output_bytes_per_zone is not None
            else None,
            "file_count_nominal": math.ceil(
                spec.release_zone_count * coefficients.diagnostic_file_count_per_zone
            )
            if coefficients.diagnostic_file_count_per_zone is not None
            else None,
            "manifest_bytes_nominal": math.ceil(
                spec.release_zone_count * coefficients.diagnostic_manifest_bytes_per_zone
            )
            if coefficients.diagnostic_manifest_bytes_per_zone is not None
            else None,
            "memory_peak_mb": coefficients.diagnostic_memory_peak_mb,
            "repeatability_status": coefficients.diagnostic_repeatability_status,
            "run_root": coefficients.diagnostic_run_root,
            "job_id": coefficients.diagnostic_job_id,
            "claim_boundary": "diagnostic reducer-pressure evidence only; not hazard throughput, physical probability, operational, distributed, or Swiss-wide evidence",
        }
    return {
        "case_id": spec.case_id,
        "scale_label": spec.scale_label,
        "planning_decision": spec.decision,
        "decision_reason": spec.decision_reason,
        "evidence_class": spec.evidence_class,
        "blocker_category": spec.blocker_category,
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
        "diagnostic_support": {
            "status": "measured" if coefficients.diagnostic_release_zone_count else "missing",
            "release_zone_count": coefficients.diagnostic_release_zone_count,
            "runtime_seconds_per_zone": coefficients.diagnostic_runtime_seconds_per_zone,
            "output_bytes_per_zone": coefficients.diagnostic_output_bytes_per_zone,
            "file_count_per_zone": coefficients.diagnostic_file_count_per_zone,
            "manifest_bytes_per_zone": coefficients.diagnostic_manifest_bytes_per_zone,
            "memory_peak_mb": coefficients.diagnostic_memory_peak_mb,
            "repeatability_status": coefficients.diagnostic_repeatability_status,
            "repeatability_bounds": coefficients.diagnostic_repeatability_bounds,
            "run_root": coefficients.diagnostic_run_root,
            "job_id": coefficients.diagnostic_job_id,
            "claim_boundary": "diagnostic reducer-pressure support only; hazard, physical-probability, operational, distributed, and Swiss-wide claims remain separate",
        },
        "job_count": job_count,
        "jobs_per_aoi": jobs_per_aoi,
        "runtime_seconds": runtime_seconds,
        "storage_bytes": storage_bytes,
        "file_count": file_count,
        "memory_peak_mb": memory_peak_mb,
        "diagnostic_projection": diagnostic_projection,
        "planning_labels": planning_labels,
        "rebuildability_cost": build_rebuildability_cost(
            projected_storage_bytes=storage_bytes,
            projected_file_count=file_count,
            single_job_summary=single_job_summary,
            feasibility_report=feasibility_report,
            target_area_probe_report=target_area_probe_report,
        ),
        "bottleneck_labels": build_bottleneck_labels(
            inputs=inputs,
            coefficients=coefficients,
            job_count=job_count,
            jobs_per_aoi=jobs_per_aoi,
            projected_storage_bytes=storage_bytes,
            projected_memory_peak_mb=memory_peak_mb,
            single_job_summary=single_job_summary,
            target_area_probe_report=target_area_probe_report,
            generated_scenario_table_report=generated_scenario_table_report,
        ),
        "scenario_table_evidence": {
            "candidate_repeat_count": generated_scenario_table_report.get("candidate_repeat_count"),
            "candidate_release_zone_record_count": generated_scenario_table_report.get(
                "candidate_release_zone_record_count"
            ),
            "scenario_row_count": generated_scenario_table_report.get("scenario_row_count"),
            "first_scaling_bottleneck": generated_scenario_table_report.get("first_scaling_bottleneck"),
        },
        "evidence_basis": {
            "single_job": {
                "current_gap_output_bytes": dict(single_job_summary.get("output_size_evidence") or {}).get(
                    "current_gap_output_bytes"
                ),
                "current_gap_output_file_count": dict(single_job_summary.get("output_size_evidence") or {}).get(
                    "current_gap_output_file_count"
                ),
            },
            "target_area": {
                "wall_time_seconds": target_area_probe_report.get("wall_time_seconds"),
                "memory_peak_mb": target_area_probe_report.get("memory_peak_mb"),
                "validation_output": target_area_probe_report.get("validation_output"),
                "hazard_output": target_area_probe_report.get("hazard_output"),
            },
            "generated_scenario_table": {
                "candidate_repeat_count": generated_scenario_table_report.get("candidate_repeat_count"),
                "candidate_release_zone_record_count": generated_scenario_table_report.get(
                    "candidate_release_zone_record_count"
                ),
                "scenario_row_count": generated_scenario_table_report.get("scenario_row_count"),
                "first_scaling_bottleneck": generated_scenario_table_report.get("first_scaling_bottleneck"),
            },
        },
    }


def summarize_planning_cases(case_specs: tuple[PlanningCaseSpec, ...]) -> dict[str, Any]:
    summary = {"next_probe": [], "measured_diagnostic": [], "defer": [], "no_go": []}
    for spec in case_specs:
        summary.setdefault(spec.decision, []).append(spec.case_id)
    return {
        "status": "measured_existing_artifacts",
        "next_probe": summary["next_probe"],
        "measured_diagnostic": summary["measured_diagnostic"],
        "defer": summary["defer"],
        "no_go": summary["no_go"],
        "case_count": len(case_specs),
    }


def build_swiss_wide_national_requirements(
    *,
    projected_storage_bytes: dict[str, Any],
    projected_file_count: dict[str, Any],
    projected_job_count: int,
    projected_jobs_per_aoi: int,
    assumptions: dict[str, Any] | None = None,
) -> dict[str, Any]:
    values = dict(SWISS_WIDE_PLANNING_ASSUMPTIONS)
    if assumptions:
        values.update(assumptions)
    area_m2 = float(values["country_area_km2"]) * 1_000_000.0
    cell_size = float(values["dem_cell_size_m"])
    dem_cell_count = math.ceil(area_m2 / (cell_size * cell_size))
    dem_bytes = dem_cell_count * int(values["dem_bytes_per_cell"])
    context_bytes = dem_bytes * int(values["context_bytes_per_dem_byte"])
    tile_count = math.ceil(dem_cell_count / int(values["target_cells_per_tile"]))
    release_zone_count = int(values["default_aoi_count"]) * int(values["release_zones_per_aoi"])
    trajectory_count = release_zone_count * int(values["trajectories_per_release_zone"])
    return {
        "schema_version": "swiss_wide_national_requirements_v1",
        "assumption_class": "planning_default_not_measured_national_inventory",
        "input_data_requirements": {
            "country_area_km2": int(values["country_area_km2"]),
            "dem_cell_size_m": cell_size,
            "estimated_dem_cell_count": dem_cell_count,
            "estimated_dem_bytes": dem_bytes,
            "estimated_context_bytes": context_bytes,
            "estimated_total_input_bytes": dem_bytes + context_bytes,
            "required_context_products": [
                "swissALTI3D",
                "SWISSIMAGE",
                "swissTLM3D",
                "swissSURFACE3D",
                "swissBUILDINGS3D",
            ],
        },
        "tiling_requirements": {
            "target_cells_per_tile": int(values["target_cells_per_tile"]),
            "estimated_tile_count": tile_count,
            "chunk_key_policy": "stable_national_tile_id_plus_release_zone_batch",
            "merge_order": "sorted_tile_id_then_sorted_chunk_id",
        },
        "execution_requirements": {
            "aoi_count": int(values["default_aoi_count"]),
            "release_zone_count": release_zone_count,
            "trajectory_count": trajectory_count,
            "projected_job_count": projected_job_count,
            "projected_jobs_per_aoi": projected_jobs_per_aoi,
            "requires_distributed_orchestration": projected_job_count > 1 or tile_count > 1,
        },
        "output_footprint_requirements": {
            "projected_storage_bytes": projected_storage_bytes.get("nominal"),
            "projected_storage_bytes_high": projected_storage_bytes.get("high"),
            "projected_file_count": projected_file_count.get("nominal"),
            "projected_file_count_high": projected_file_count.get("high"),
            "requires_cog_package_plan": True,
            "requires_replay_budget": True,
        },
    }


def build_swiss_wide_phase_change_readiness(
    *,
    projection_status: str,
    no_go_labels: list[str],
    distributed_execution_authorized: bool,
    national_requirements: dict[str, Any],
    class_overrides: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    classes = {
        "compute_feasible": {
            "status": "ready"
            if projection_status == "measured_within_support" and distributed_execution_authorized
            else "deferred",
            "first_missing_input": "measured_distributed_or_single_job_swiss_wide_execution"
            if projection_status != "measured_within_support"
            else "distributed_execution_authorization",
            "evidence_needed": [
                "measured national tiling/chunk-count runtime",
                "measured walltime, memory, I/O, and restart cost",
                "distributed execution authorization when job_count or tile_count exceeds one",
            ],
        },
        "data_ready": {
            "status": "deferred",
            "first_missing_input": "national_public_geodata_inventory",
            "evidence_needed": [
                "complete swissALTI3D national tile inventory",
                "ready local cache for required context products",
                "share-safe national tiling manifest with checksums and versions",
            ],
        },
        "validation_ready": {
            "status": "deferred",
            "first_missing_input": "multi_site_holdout_validation_and_physical_probability_evidence",
            "evidence_needed": [
                "source-frequency evidence",
                "release-probability model",
                "independent holdout validation beyond Tschamut",
                "calibration/validation separation",
            ],
        },
        "operational_ready": {
            "status": "deferred",
            "first_missing_input": "operational_gis_review_monitoring_and_support",
            "evidence_needed": [
                "national GIS/COG package QA",
                "monitoring and reproducibility record",
                "versioned release and support criteria",
            ],
        },
    }
    for class_name, override in (class_overrides or {}).items():
        if class_name in classes:
            classes[class_name] = {**classes[class_name], **override}
    blocked_classes = [name for name, row in classes.items() if row.get("status") != "ready"]
    first_blocker = blocked_classes[0] if blocked_classes else None
    return {
        "schema_version": SWISS_WIDE_PHASE_CHANGE_SCHEMA_VERSION,
        "phase_change_status": "ready_for_phase_change_review" if not blocked_classes else "deferred",
        "swiss_wide_execution_authorized": False,
        "class_statuses": classes,
        "blocked_classes": blocked_classes,
        "first_blocker_class": first_blocker,
        "first_missing_input": classes[first_blocker]["first_missing_input"] if first_blocker else None,
        "no_go_labels": list(no_go_labels),
        "national_requirements": national_requirements,
        "claim_boundary": "readiness decomposition only; no Swiss-wide execution, operational, annual, physical-probability, or risk claim",
    }


def build_multi_zone_scaling_frontier(canonical_bundle_report: dict[str, Any]) -> dict[str, Any]:
    evidence = EVIDENCE_BUNDLE.build_multi_zone_balfrin_evidence(
        canonical_bundle_report.get("multi_zone_balfrin_evidence")
    )
    status = str(evidence.get("status") or "blocked_incomplete")
    first_bottleneck = str(evidence.get("first_bottleneck_label") or "manifest_size_bytes")
    release_zone_count = evidence.get("release_zone_count")
    measured_two_zone = status == "measured" and release_zone_count == 2
    failed_closed_two_zone = status == "failed_closed" and release_zone_count == 2
    if measured_two_zone:
        frontier_status = "measured_two_zone_boundary"
        next_branch = "review_next_larger_balfrin_package"
        next_blocker = "explicit_authorization_required"
        summary = (
            "Measured two-zone Balfrin evidence is present, so the scaling frontier can move to a reviewed "
            "next-larger package; this report still does not authorize a larger run."
        )
    elif failed_closed_two_zone:
        frontier_status = "failed_closed"
        next_branch = "resolve_two_zone_failed_closed_blocker"
        next_blocker = str(evidence.get("next_blocker") or "failed_closed:two_zone_pre_submit")
        summary = (
            str(evidence.get("summary") or "")
            or "The current two-zone branch failed closed before sbatch, so it remains guardrail evidence rather than measured multi-zone hazard execution."
        )
    elif status.startswith("blocked"):
        frontier_status = "blocked_incomplete"
        next_branch = "no_go"
        next_blocker = f"blocked_reducer_budget:{first_bottleneck}"
        summary = (
            "No measured multi-zone Balfrin run is present. TB-267 stopped before submission at reducer budget "
            f"first bottleneck {first_bottleneck}, with the authorization record missing."
        )
    else:
        frontier_status = "not_measured"
        next_branch = "no_go"
        next_blocker = str(evidence.get("next_blocker") or "multi_zone_evidence_not_measured")
        summary = "Only scratch or fixture-backed multi-zone evidence is present, so larger Balfrin or Swiss AOI expansion is no-go."
    return {
        "status": frontier_status,
        "evidence_status": status,
        "evidence_type": evidence.get("evidence_type"),
        "root_class": evidence.get("root_class"),
        "release_zone_count": release_zone_count,
        "first_bottleneck_label": first_bottleneck,
        "next_scaling_branch": next_branch,
        "next_blocker": next_blocker,
        "larger_run_authorized": False,
        "scale_up_authorized": False,
        "distributed_execution_authorized": False,
        "summary": summary,
    }


def build_report(inputs: ProjectionInputs, *, coefficients: MeasuredCoefficients) -> dict[str, Any]:
    validate_inputs(inputs)

    single_job_summary = SINGLE_JOB.build_summary()
    feasibility_report = FEASIBILITY.build_report()
    canonical_bundle_report = load_canonical_bundle_report()
    hazard_throughput_evidence = load_latest_hazard_throughput_evidence()
    hazard_throughput_baseline = dict(hazard_throughput_evidence.get("comparison_baseline") or {})
    multi_zone_scaling_frontier = build_multi_zone_scaling_frontier(canonical_bundle_report)
    target_area_probe_report = load_target_area_probe_report()
    generated_scenario_table_report = load_generated_scenario_table_evidence()
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
    national_requirements = build_swiss_wide_national_requirements(
        projected_storage_bytes=storage_bytes,
        projected_file_count=file_counts,
        projected_job_count=job_count,
        projected_jobs_per_aoi=jobs_per_aoi,
    )
    swiss_wide_phase_change_readiness = build_swiss_wide_phase_change_readiness(
        projection_status=projection_status,
        no_go_labels=no_go_labels,
        distributed_execution_authorized=False,
        national_requirements=national_requirements,
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
        "diagnostic_support": {
            "status": "measured" if coefficients.diagnostic_release_zone_count else "missing",
            "release_zone_count": coefficients.diagnostic_release_zone_count,
            "runtime_seconds_per_zone": coefficients.diagnostic_runtime_seconds_per_zone,
            "output_bytes_per_zone": coefficients.diagnostic_output_bytes_per_zone,
            "file_count_per_zone": coefficients.diagnostic_file_count_per_zone,
            "manifest_bytes_per_zone": coefficients.diagnostic_manifest_bytes_per_zone,
            "memory_peak_mb": coefficients.diagnostic_memory_peak_mb,
            "repeatability_status": coefficients.diagnostic_repeatability_status,
            "repeatability_bounds": coefficients.diagnostic_repeatability_bounds,
            "run_root": coefficients.diagnostic_run_root,
            "job_id": coefficients.diagnostic_job_id,
            "claim_boundary": "diagnostic reducer-pressure support only; hazard, physical-probability, operational, distributed, and Swiss-wide claims remain separate",
        },
        "hazard_throughput_support": {
            "status": hazard_throughput_evidence.get("status"),
            "task_id": hazard_throughput_evidence.get("task_id"),
            "job_id": hazard_throughput_evidence.get("slurm_job_id"),
            "run_root": hazard_throughput_evidence.get("run_root"),
            "release_zone_count": hazard_throughput_evidence.get("release_zone_count"),
            "runtime_seconds": hazard_throughput_evidence.get("total_wall_seconds"),
            "hazard_stage_seconds": hazard_throughput_evidence.get("hazard_stage_seconds"),
            "memory_peak_mb": hazard_throughput_evidence.get("memory_peak_mb"),
            "validation_output_file_count": hazard_throughput_evidence.get("validation_output_file_count"),
            "validation_output_bytes": hazard_throughput_evidence.get("validation_output_bytes"),
            "hazard_output_file_count": hazard_throughput_evidence.get("hazard_output_file_count"),
            "hazard_output_bytes": hazard_throughput_evidence.get("hazard_output_bytes"),
            "run_root_file_count": hazard_throughput_evidence.get("run_root_file_count"),
            "run_root_bytes": hazard_throughput_evidence.get("run_root_bytes"),
            "conditional_curve_row_count": hazard_throughput_evidence.get("conditional_curve_row_count"),
            "comparison_baseline_task_id": hazard_throughput_baseline.get("task_id"),
            "comparison_baseline_job_id": hazard_throughput_baseline.get("slurm_job_id"),
            "comparison_baseline_runtime_seconds": hazard_throughput_baseline.get("total_wall_seconds"),
            "claim_boundary": hazard_throughput_evidence.get("claim_boundary"),
        },
        "job_count": job_count,
        "jobs_per_aoi": jobs_per_aoi,
        "runtime_seconds": runtime_seconds,
        "storage_bytes": storage_bytes,
        "file_count": file_counts,
        "memory_peak_mb": memory_peak_mb,
        "swiss_wide_phase_change_readiness": swiss_wide_phase_change_readiness,
        "rebuildability_cost": build_rebuildability_cost(
            projected_storage_bytes=storage_bytes,
            projected_file_count=file_counts,
            single_job_summary=single_job_summary,
            feasibility_report=feasibility_report,
            target_area_probe_report=target_area_probe_report,
        ),
        "bottleneck_labels": build_bottleneck_labels(
            inputs=inputs,
            coefficients=coefficients,
            job_count=job_count,
            jobs_per_aoi=jobs_per_aoi,
            projected_storage_bytes=storage_bytes,
            projected_memory_peak_mb=memory_peak_mb,
            single_job_summary=single_job_summary,
            target_area_probe_report=target_area_probe_report,
            generated_scenario_table_report=generated_scenario_table_report,
        ),
        "uncertainty_band": {
            "runtime_seconds": band_summary(runtime_seconds),
            "storage_bytes": band_summary(storage_bytes),
            "file_count": band_summary(file_counts),
            "memory_peak_mb": band_summary(memory_peak_mb),
        },
        "no_go_labels": no_go_labels,
        "blocked_reason": build_blocked_reason(no_go_labels),
        "measurement_basis": {
            "balfrin_demo_run_root": MEASURED_BALFRIN_DEMO_RUN_ROOT,
            "target_area_run_root": str(MEASURED_TARGET_AREA_RUN_ROOT),
            "generated_scenario_table_output_root": str(GENERATED_SCENARIO_TABLE_OUTPUT_ROOT),
            "source_commands": MEASURED_SOURCE_COMMANDS,
            "measurement_notes": list(coefficients.measurement_notes),
            "bounded_probe_recommendation_status": coefficients.bounded_probe_recommendation_status,
            "multi_zone_manifest_pressure_ladder": coefficients.multi_zone_manifest_pressure_ladder,
            "diagnostic_support": {
                "release_zone_count": coefficients.diagnostic_release_zone_count,
                "runtime_seconds_per_zone": coefficients.diagnostic_runtime_seconds_per_zone,
                "output_bytes_per_zone": coefficients.diagnostic_output_bytes_per_zone,
                "file_count_per_zone": coefficients.diagnostic_file_count_per_zone,
                "manifest_bytes_per_zone": coefficients.diagnostic_manifest_bytes_per_zone,
                "memory_peak_mb": coefficients.diagnostic_memory_peak_mb,
                "repeatability_status": coefficients.diagnostic_repeatability_status,
                "repeatability_bounds": coefficients.diagnostic_repeatability_bounds,
                "run_root": coefficients.diagnostic_run_root,
                "job_id": coefficients.diagnostic_job_id,
            },
            "hazard_throughput_support": {
                "task_id": hazard_throughput_evidence.get("task_id"),
                "job_id": hazard_throughput_evidence.get("slurm_job_id"),
                "run_root": hazard_throughput_evidence.get("run_root"),
                "release_zone_count": hazard_throughput_evidence.get("release_zone_count"),
                "runtime_seconds": hazard_throughput_evidence.get("total_wall_seconds"),
                "hazard_stage_seconds": hazard_throughput_evidence.get("hazard_stage_seconds"),
                "memory_peak_mb": hazard_throughput_evidence.get("memory_peak_mb"),
                "hazard_output_file_count": hazard_throughput_evidence.get("hazard_output_file_count"),
                "hazard_output_bytes": hazard_throughput_evidence.get("hazard_output_bytes"),
                "run_root_file_count": hazard_throughput_evidence.get("run_root_file_count"),
                "run_root_bytes": hazard_throughput_evidence.get("run_root_bytes"),
                "conditional_curve_row_count": hazard_throughput_evidence.get("conditional_curve_row_count"),
                "comparison_baseline_task_id": hazard_throughput_baseline.get("task_id"),
                "comparison_baseline_job_id": hazard_throughput_baseline.get("slurm_job_id"),
                "claim_boundary": hazard_throughput_evidence.get("claim_boundary"),
            },
            "canonical_bundle_status": canonical_bundle_report.get("bundle_status"),
            "canonical_bundle_summary": canonical_bundle_report.get("bundle_summary", {}),
            "multi_zone_scaling_frontier": multi_zone_scaling_frontier,
            "single_job_summary": {
                "decision": single_job_summary.get("decision"),
                "final_classification": single_job_summary.get("final_classification"),
                "single_job_sufficient_for_next_step": single_job_summary.get(
                    "single_job_sufficient_for_next_step"
                ),
                "current_pressure": single_job_summary.get("current_pressure"),
            },
            "target_area_probe_metrics": {
                "report_status": target_area_probe_report.get("report_status"),
                "wall_time_seconds": target_area_probe_report.get("wall_time_seconds"),
                "memory_peak_mb": target_area_probe_report.get("memory_peak_mb"),
                "validation_output": target_area_probe_report.get("validation_output"),
                "hazard_output": target_area_probe_report.get("hazard_output"),
            },
            "generated_scenario_table": {
                "stress_test_status": generated_scenario_table_report.get("stress_test_status"),
                "candidate_repeat_count": generated_scenario_table_report.get("candidate_repeat_count"),
                "candidate_release_zone_record_count": generated_scenario_table_report.get(
                    "candidate_release_zone_record_count"
                ),
                "scenario_row_count": generated_scenario_table_report.get("scenario_row_count"),
                "first_scaling_bottleneck": generated_scenario_table_report.get("first_scaling_bottleneck"),
            },
        },
        "planning_labels": build_planning_labels(
            measurement_status="measured_existing_artifacts",
            no_go_labels=no_go_labels,
            multi_zone_scaling_frontier=multi_zone_scaling_frontier,
        ),
        "planning_cases": [
            build_case_projection(
                spec=spec,
                coefficients=coefficients,
                single_job_summary=single_job_summary,
                feasibility_report=feasibility_report,
                target_area_probe_report=target_area_probe_report,
                generated_scenario_table_report=generated_scenario_table_report,
            )
            for spec in CANONICAL_PLANNING_CASES
        ],
        "planning_case_summary": summarize_planning_cases(CANONICAL_PLANNING_CASES),
        "multi_zone_scaling_frontier": multi_zone_scaling_frontier,
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
    try:
        diagnostic_evidence = load_latest_diagnostic_evidence()
        diagnostic_repeatability = load_diagnostic_repeatability_summary()
    except Exception:
        diagnostic_evidence = {}
        diagnostic_repeatability = {}
    diagnostic_release_zone_count = diagnostic_evidence.get("release_zone_count")
    diagnostic_support = {
        "status": "measured" if isinstance(diagnostic_release_zone_count, int) else "blocked_missing_inputs",
        "release_zone_count": diagnostic_release_zone_count if isinstance(diagnostic_release_zone_count, int) else None,
        "runtime_seconds_per_zone": build_ratio(
            diagnostic_evidence.get("reducer_wall_time_seconds"),
            diagnostic_release_zone_count,
            precision=6,
        ),
        "output_bytes_per_zone": build_ratio(
            diagnostic_evidence.get("diagnostic_output_bytes"),
            diagnostic_release_zone_count,
            precision=6,
        ),
        "file_count_per_zone": build_ratio(
            diagnostic_evidence.get("diagnostic_output_file_count"),
            diagnostic_release_zone_count,
            precision=6,
        ),
        "manifest_bytes_per_zone": build_ratio(
            diagnostic_evidence.get("diagnostic_manifest_size_bytes"),
            diagnostic_release_zone_count,
            precision=6,
        ),
        "memory_peak_mb": diagnostic_evidence.get("memory_peak_mb")
        if isinstance(diagnostic_evidence.get("memory_peak_mb"), (int, float))
        else None,
        "repeatability_status": diagnostic_repeatability.get("status"),
        "repeatability_bounds": diagnostic_repeatability.get("bounds"),
        "run_root": diagnostic_evidence.get("run_root")
        if isinstance(diagnostic_evidence.get("run_root"), str)
        else None,
        "job_id": diagnostic_evidence.get("slurm_job_id")
        if isinstance(diagnostic_evidence.get("slurm_job_id"), str)
        else None,
        "claim_boundary": (
            "diagnostic reducer-pressure support only; hazard projection coefficients are unavailable"
            if isinstance(diagnostic_release_zone_count, int)
            else "diagnostic support unavailable because measured evidence is missing"
        ),
    }
    national_requirements = build_swiss_wide_national_requirements(
        projected_storage_bytes=empty_band,
        projected_file_count=empty_band,
        projected_job_count=0,
        projected_jobs_per_aoi=0,
    )
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
        "diagnostic_support": diagnostic_support,
        "job_count": None,
        "jobs_per_aoi": None,
        "runtime_seconds": empty_band,
        "storage_bytes": empty_band,
        "file_count": empty_band,
        "memory_peak_mb": empty_band,
        "swiss_wide_phase_change_readiness": build_swiss_wide_phase_change_readiness(
            projection_status="blocked_missing_inputs",
            no_go_labels=["blocked_missing_inputs"],
            distributed_execution_authorized=False,
            national_requirements=national_requirements,
        ),
        "rebuildability_cost": {
            "projected_storage_bytes": None,
            "projected_file_count": None,
            "current_gap_output_bytes": None,
            "current_gap_output_file_count": None,
            "rebuildable_reduced_output_bytes": None,
            "rebuildable_reduced_output_file_count": None,
            "target_validation_output_bytes": None,
            "target_validation_output_file_count": None,
            "target_hazard_output_bytes": None,
            "target_hazard_output_file_count": None,
            "bounded_relative_to_target_validation": False,
            "bounded_relative_to_target_hazard": False,
            "output_byte_ratio_to_target_validation": None,
            "output_file_ratio_to_target_validation": None,
            "output_byte_ratio_to_target_hazard": None,
            "output_file_ratio_to_target_hazard": None,
            "output_byte_ratio_to_current_gap": None,
            "output_file_ratio_to_current_gap": None,
            "output_byte_ratio_to_rebuildable_reduced": None,
            "output_file_ratio_to_rebuildable_reduced": None,
        },
        "bottleneck_labels": {
            "validation_output": {"label": "blocked_missing_inputs", "evidence": {}},
            "hazard_output": {"label": "blocked_missing_inputs", "evidence": {}},
            "reducer_merge": {"label": "blocked_missing_inputs", "evidence": {}},
            "manifest_count": {"label": "blocked_missing_inputs", "evidence": {}},
            "memory": {"label": "blocked_missing_inputs", "evidence": {}},
            "scheduler_practicality": {"label": "blocked_missing_inputs", "evidence": {}},
        },
        "uncertainty_band": {
            "runtime_seconds": band_summary(empty_band),
            "storage_bytes": band_summary(empty_band),
            "file_count": band_summary(empty_band),
            "memory_peak_mb": band_summary(empty_band),
        },
        "no_go_labels": [],
        "blocked_reason": blocked_reason,
        "measurement_basis": {
            "balfrin_demo_run_root": MEASURED_BALFRIN_DEMO_RUN_ROOT,
            "target_area_run_root": str(MEASURED_TARGET_AREA_RUN_ROOT),
            "generated_scenario_table_output_root": str(GENERATED_SCENARIO_TABLE_OUTPUT_ROOT),
            "source_commands": MEASURED_SOURCE_COMMANDS,
            "measurement_notes": [
                "measured Balfrin evidence was unavailable, so the frontier cannot be projected",
            ],
            "bounded_probe_recommendation_status": None,
            "multi_zone_manifest_pressure_ladder": None,
            "diagnostic_support": diagnostic_support,
            "canonical_bundle_status": "blocked_missing_inputs",
            "canonical_bundle_summary": {},
            "multi_zone_scaling_frontier": {
                "status": "blocked_missing_inputs",
                "next_scaling_branch": "no_go",
                "next_blocker": "missing_inputs",
                "larger_run_authorized": False,
            },
            "target_area_probe_metrics": {
                "report_status": "blocked_missing_inputs",
                "wall_time_seconds": None,
                "memory_peak_mb": None,
                "validation_output": {},
                "hazard_output": {},
            },
            "generated_scenario_table": {
                "stress_test_status": "blocked_missing_inputs",
                "candidate_repeat_count": None,
                "candidate_release_zone_record_count": None,
                "scenario_row_count": None,
                "first_scaling_bottleneck": {},
            },
            "single_job_summary": None,
        },
        "planning_labels": build_planning_labels(
            measurement_status="blocked_missing_inputs",
            no_go_labels=[],
            multi_zone_scaling_frontier={"status": "blocked_missing_inputs"},
        ),
        "planning_cases": [],
        "planning_case_summary": {
            "status": "blocked_missing_inputs",
            "next_probe": [],
            "measured_diagnostic": [],
            "defer": [],
            "no_go": [],
            "case_count": 0,
        },
        "multi_zone_scaling_frontier": {
            "status": "blocked_missing_inputs",
            "next_scaling_branch": "no_go",
            "next_blocker": blocked_reason,
            "larger_run_authorized": False,
            "scale_up_authorized": False,
            "distributed_execution_authorized": False,
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


def build_planning_labels(
    *,
    measurement_status: str,
    no_go_labels: list[str],
    multi_zone_scaling_frontier: dict[str, Any] | None = None,
) -> dict[str, str]:
    no_go_label = "no_go_extrapolated_beyond_measured_evidence" if no_go_labels else "no_go_not_triggered"
    defer_label = "defer_scale_up_authorized_false"
    frontier_status = str((multi_zone_scaling_frontier or {}).get("status") or "")
    allowed_next_probe_label = (
        "allowed_next_probe_blocked_missing_inputs"
        if measurement_status != "measured_existing_artifacts"
        else "allowed_next_probe_measured_two_zone_review_only"
        if frontier_status == "measured_two_zone_boundary"
        else "allowed_next_probe_blocked_failed_closed"
        if frontier_status == "failed_closed"
        else "allowed_next_probe_blocked_multi_zone_evidence"
        if frontier_status.startswith("blocked")
        else "allowed_next_probe_measured_existing_artifacts"
    )
    return {
        "no_go": no_go_label,
        "defer": defer_label,
        "allowed_next_probe": allowed_next_probe_label,
    }


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
    rebuildability_cost = report.get("rebuildability_cost", {})
    bottleneck_labels = report.get("bottleneck_labels", {})
    multi_zone_frontier = report.get("multi_zone_scaling_frontier", {})
    diagnostic_support = report.get("diagnostic_support", {})
    swiss_wide_readiness = report.get("swiss_wide_phase_change_readiness", {})
    national_requirements = swiss_wide_readiness.get("national_requirements", {})
    input_requirements = national_requirements.get("input_data_requirements", {})
    tiling_requirements = national_requirements.get("tiling_requirements", {})
    execution_requirements = national_requirements.get("execution_requirements", {})
    output_requirements = national_requirements.get("output_footprint_requirements", {})
    lines = [
        "Swiss-wide execution envelope",
        f"measurement_status: {report['measurement_status']}",
        f"projection_status: {report['projection_status']}",
        f"blocked_reason: {report['blocked_reason']}",
        "planning_labels:",
        f"  no_go: {report['planning_labels']['no_go']}",
        f"  defer: {report['planning_labels']['defer']}",
        f"  allowed_next_probe: {report['planning_labels']['allowed_next_probe']}",
        f"  bounded_probe_recommendation_status: {report['measurement_basis'].get('bounded_probe_recommendation_status')}",
        "multi_zone_scaling_frontier:",
        f"  status: {multi_zone_frontier.get('status', 'unknown')}",
        f"  evidence_status: {multi_zone_frontier.get('evidence_status', 'unknown')}",
        f"  next_scaling_branch: {multi_zone_frontier.get('next_scaling_branch', 'unknown')}",
        f"  next_blocker: {multi_zone_frontier.get('next_blocker', 'unknown')}",
        f"  first_bottleneck_label: {multi_zone_frontier.get('first_bottleneck_label', 'unknown')}",
        f"  larger_run_authorized: {multi_zone_frontier.get('larger_run_authorized', False)}",
        "diagnostic_support:",
        f"  status: {diagnostic_support.get('status', 'unknown')}",
        f"  release_zone_count: {diagnostic_support.get('release_zone_count')}",
        f"  repeatability_status: {diagnostic_support.get('repeatability_status')}",
        f"  runtime_seconds_per_zone: {diagnostic_support.get('runtime_seconds_per_zone')}",
        f"  output_bytes_per_zone: {diagnostic_support.get('output_bytes_per_zone')}",
        "swiss_wide_phase_change_readiness:",
        f"  status: {swiss_wide_readiness.get('phase_change_status')}",
        f"  first_blocker_class: {swiss_wide_readiness.get('first_blocker_class')}",
        f"  first_missing_input: {swiss_wide_readiness.get('first_missing_input')}",
        f"  estimated_total_input_bytes: {input_requirements.get('estimated_total_input_bytes')}",
        f"  estimated_tile_count: {tiling_requirements.get('estimated_tile_count')}",
        f"  required_release_zone_count: {execution_requirements.get('release_zone_count')}",
        f"  required_trajectory_count: {execution_requirements.get('trajectory_count')}",
        f"  projected_output_bytes: {output_requirements.get('projected_storage_bytes')}",
        f"  projected_output_file_count: {output_requirements.get('projected_file_count')}",
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
        "rebuildability_cost:",
        f"  projected_storage_bytes: {rebuildability_cost.get('projected_storage_bytes')}",
        f"  projected_file_count: {rebuildability_cost.get('projected_file_count')}",
        f"  bounded_relative_to_target_validation: {rebuildability_cost.get('bounded_relative_to_target_validation')}",
        f"  bounded_relative_to_target_hazard: {rebuildability_cost.get('bounded_relative_to_target_hazard')}",
        f"  output_byte_ratio_to_target_validation: {rebuildability_cost.get('output_byte_ratio_to_target_validation')}",
        f"  output_file_ratio_to_target_validation: {rebuildability_cost.get('output_file_ratio_to_target_validation')}",
        f"  output_byte_ratio_to_target_hazard: {rebuildability_cost.get('output_byte_ratio_to_target_hazard')}",
        f"  output_file_ratio_to_target_hazard: {rebuildability_cost.get('output_file_ratio_to_target_hazard')}",
        "bottleneck_labels:",
        f"  validation_output: {bottleneck_labels.get('validation_output', {}).get('label', 'unknown')}",
        f"  hazard_output: {bottleneck_labels.get('hazard_output', {}).get('label', 'unknown')}",
        f"  reducer_merge: {bottleneck_labels.get('reducer_merge', {}).get('label', 'unknown')}",
        f"  manifest_count: {bottleneck_labels.get('manifest_count', {}).get('label', 'unknown')}",
        f"  memory: {bottleneck_labels.get('memory', {}).get('label', 'unknown')}",
        f"  scheduler_practicality: {bottleneck_labels.get('scheduler_practicality', {}).get('label', 'unknown')}",
        "planning_case_summary:",
        f"  status: {report.get('planning_case_summary', {}).get('status', 'unknown')}",
        f"  next_probe: {report.get('planning_case_summary', {}).get('next_probe', [])}",
        f"  measured_diagnostic: {report.get('planning_case_summary', {}).get('measured_diagnostic', [])}",
        f"  defer: {report.get('planning_case_summary', {}).get('defer', [])}",
        f"  no_go: {report.get('planning_case_summary', {}).get('no_go', [])}",
        "measurement_basis:",
        f"  balfrin_demo_run_root: {report['measurement_basis']['balfrin_demo_run_root']}",
        f"  target_area_run_root: {report['measurement_basis'].get('target_area_run_root')}",
        f"  generated_scenario_table_output_root: {report['measurement_basis'].get('generated_scenario_table_output_root')}",
        f"  canonical_bundle_status: {report['measurement_basis'].get('canonical_bundle_status')}",
    ]
    for class_name, row in (swiss_wide_readiness.get("class_statuses") or {}).items():
        lines.append(f"  readiness_class.{class_name}: {row.get('status')} ({row.get('first_missing_input')})")
    for label, command in report["measurement_basis"]["source_commands"].items():
        lines.append(f"  {label}: {command}")
    for note in report["measurement_basis"]["measurement_notes"]:
        lines.append(f"  note: {note}")
    single_job_summary = report["measurement_basis"].get("single_job_summary")
    if isinstance(single_job_summary, dict):
        lines.append("  single_job_summary:")
        lines.append(f"    decision: {single_job_summary.get('decision')}")
        lines.append(f"    final_classification: {single_job_summary.get('final_classification')}")
        lines.append(
            "    single_job_sufficient_for_next_step: "
            f"{single_job_summary.get('single_job_sufficient_for_next_step')}"
        )
    target_area_probe_metrics = report["measurement_basis"].get("target_area_probe_metrics")
    if isinstance(target_area_probe_metrics, dict):
        lines.append("  target_area_probe_metrics:")
        lines.append(f"    report_status: {target_area_probe_metrics.get('report_status')}")
        lines.append(f"    wall_time_seconds: {target_area_probe_metrics.get('wall_time_seconds')}")
        lines.append(f"    memory_peak_mb: {target_area_probe_metrics.get('memory_peak_mb')}")
    generated_scenario_table = report["measurement_basis"].get("generated_scenario_table")
    if isinstance(generated_scenario_table, dict):
        lines.append("  generated_scenario_table:")
        lines.append(f"    stress_test_status: {generated_scenario_table.get('stress_test_status')}")
        lines.append(f"    candidate_repeat_count: {generated_scenario_table.get('candidate_repeat_count')}")
        lines.append(
            "    candidate_release_zone_record_count: "
            f"{generated_scenario_table.get('candidate_release_zone_record_count')}"
        )
        lines.append(f"    scenario_row_count: {generated_scenario_table.get('scenario_row_count')}")
        first_bottleneck = generated_scenario_table.get("first_scaling_bottleneck") or {}
        lines.append(f"    first_scaling_bottleneck: {first_bottleneck.get('name')}")
    planning_cases = report.get("planning_cases") or []
    if planning_cases:
        lines.append("planning_cases:")
        for case in planning_cases:
            lines.append(f"  - case_id: {case.get('case_id')}")
            lines.append(f"    scale_label: {case.get('scale_label')}")
            lines.append(f"    planning_decision: {case.get('planning_decision')}")
            lines.append(f"    evidence_class: {case.get('evidence_class')}")
            lines.append(f"    blocker_category: {case.get('blocker_category')}")
            lines.append(f"    decision_reason: {case.get('decision_reason')}")
            lines.append(f"    job_count: {case.get('job_count')}")
            lines.append(f"    jobs_per_aoi: {case.get('jobs_per_aoi')}")
            lines.append(f"    runtime_seconds: {case.get('runtime_seconds', {})}")
            lines.append(f"    storage_bytes: {case.get('storage_bytes', {})}")
            lines.append(f"    file_count: {case.get('file_count', {})}")
            lines.append(f"    memory_peak_mb: {case.get('memory_peak_mb', {})}")
            if case.get("diagnostic_projection"):
                lines.append(f"    diagnostic_projection: {case.get('diagnostic_projection')}")
            lines.append(f"    planning_labels: {case.get('planning_labels', {})}")
            lines.append(
                f"    manifest_count_bottleneck: "
                f"{case.get('bottleneck_labels', {}).get('manifest_count', {}).get('label', 'unknown')}"
            )
            lines.append(
                f"    scheduler_practicality_bottleneck: "
                f"{case.get('bottleneck_labels', {}).get('scheduler_practicality', {}).get('label', 'unknown')}"
            )
    return "\n".join(lines)


def require_numeric_metric(value: Any, label: str) -> float:
    if value is None:
        raise SwissWideExecutionEnvelopeError(f"measured Balfrin evidence is missing {label}")
    return float(value)


if __name__ == "__main__":
    raise SystemExit(main())
