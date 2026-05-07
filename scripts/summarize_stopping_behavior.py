#!/usr/bin/env python3
"""Summarize stopping-behavior diagnostics from existing outputs.

This script is intentionally read-only with respect to simulation behavior. It
does not run models, tune parameters, change baselines, or filter outcomes. It
summarizes trajectory/deposition/manifest artifacts that already exist.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


DEFAULT_STOP_SPEED_MPS = 0.05
DEFAULT_LOW_ENERGY_CONTACT_SPEED_MPS = 0.05
DEFAULT_SIGNIFICANT_IMPACT_SPEED_MPS = 0.05

CONTACT_STATES = {"impact", "sliding", "rolling", "stopped"}


@dataclass(frozen=True)
class InputSpec:
    label: str
    path: Path


def parse_spec(text: str) -> InputSpec:
    if ":" not in text:
        path = Path(text)
        return InputSpec(path.stem, path)
    label, path = text.split(":", 1)
    if not label.strip():
        raise ValueError(f"empty label in input spec {text!r}")
    return InputSpec(label.strip(), Path(path))


def safe_float(value: object) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        number = float(text)
    except ValueError:
        return None
    if not math.isfinite(number):
        return None
    return number


def safe_int(value: object) -> int | None:
    number = safe_float(value)
    if number is None:
        return None
    return int(number)


def read_csv_dicts(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def mean(values: Iterable[float]) -> float | None:
    values = list(values)
    if not values:
        return None
    return sum(values) / len(values)


def p95(values: Iterable[float]) -> float | None:
    values = sorted(values)
    if not values:
        return None
    if len(values) == 1:
        return values[0]
    rank = 0.95 * (len(values) - 1)
    lo = math.floor(rank)
    hi = math.ceil(rank)
    frac = rank - lo
    return values[lo] * (1.0 - frac) + values[hi] * frac


def max_or_none(values: Iterable[float]) -> float | None:
    values = list(values)
    if not values:
        return None
    return max(values)


def horizontal_distance_m(a: dict[str, str], b: dict[str, str]) -> float | None:
    ax = safe_float(a.get("x_m"))
    ay = safe_float(a.get("y_m"))
    bx = safe_float(b.get("x_m"))
    by = safe_float(b.get("y_m"))
    if None in (ax, ay, bx, by):
        return None
    return math.hypot(float(ax) - float(bx), float(ay) - float(by))


def infer_role(label: str, path: Path) -> str:
    text = f"{label} {path}".lower()
    if "verification" in text or "analytic" in text or "regime" in text:
        return "verification_or_synthetic"
    if "chant_sura" in text:
        return "chant_sura_contact_diagnostic"
    if "tschamut" in text:
        return "tschamut_diagnostic_only"
    if "mel_de_la_niva" in text or "mel" in text:
        return "mel_de_la_niva_smoke_only"
    if "hazard" in text or "swissalti3d" in text or "performance" in text:
        return "hazard_or_smoke_workflow"
    return "unknown"


def infer_contact_model(label: str, path: Path) -> str:
    text = f"{label} {path}".lower()
    if "shape_contact_v0" in text:
        return "shape_contact_v0_internal_only"
    if "rotational" in text or "sphere_rotational_v1" in text:
        return "sphere_rotational_v1"
    if "scarring" in text:
        return "translational_v0_plus_scarring"
    if "roughness" in text:
        return "translational_v0_plus_roughness"
    return "translational_v0_or_unspecified"


def infer_stop_reason(
    final_row: dict[str, str],
    *,
    stop_speed_mps: float,
) -> str:
    state = (final_row.get("contact_state") or "").strip()
    final_speed = safe_float(final_row.get("speed_mps"))
    if state == "stopped":
        return "explicit_stopped_state"
    if final_speed is not None and final_speed <= stop_speed_mps:
        return "final_speed_below_stop_threshold_proxy"
    if state in {"impact", "sliding", "rolling"}:
        return "output_ended_while_in_contact_state"
    if state == "airborne":
        return "output_ended_airborne"
    return "unknown_no_explicit_stop_reason"


def summarize_trajectory_csv(
    spec: InputSpec,
    *,
    stop_speed_mps: float = DEFAULT_STOP_SPEED_MPS,
    low_energy_contact_speed_mps: float = DEFAULT_LOW_ENERGY_CONTACT_SPEED_MPS,
    significant_impact_speed_mps: float = DEFAULT_SIGNIFICANT_IMPACT_SPEED_MPS,
) -> dict[str, object]:
    rows = read_csv_dicts(spec.path)
    by_trajectory: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_trajectory[row.get("trajectory_id") or "trajectory_000000"].append(row)

    final_speeds: list[float] = []
    final_kinetic: list[float] = []
    final_states = Counter()
    stop_reasons = Counter()
    impact_counts: list[int] = []
    significant_impact_counts: list[int] = []
    low_energy_contact_counts: list[int] = []
    last_impact_to_final_distances: list[float] = []

    for trajectory_rows in by_trajectory.values():
        trajectory_rows.sort(key=lambda row: safe_float(row.get("time_s")) or 0.0)
        final = trajectory_rows[-1]
        final_state = (final.get("contact_state") or "unknown").strip() or "unknown"
        final_states[final_state] += 1
        stop_reasons[infer_stop_reason(final, stop_speed_mps=stop_speed_mps)] += 1
        if (speed := safe_float(final.get("speed_mps"))) is not None:
            final_speeds.append(speed)
        if (kinetic := safe_float(final.get("kinetic_j"))) is not None:
            final_kinetic.append(kinetic)

        impact_rows = [
            row for row in trajectory_rows if (row.get("contact_state") or "").strip() == "impact"
        ]
        contact_rows = [
            row for row in trajectory_rows if (row.get("contact_state") or "").strip() in CONTACT_STATES
        ]
        significant_impacts = []
        for row in impact_rows:
            speed = safe_float(row.get("speed_mps"))
            if speed is not None and speed >= significant_impact_speed_mps:
                significant_impacts.append(row)
        low_energy_contacts = [
            row
            for row in contact_rows
            if (speed := safe_float(row.get("speed_mps"))) is not None
            and speed <= low_energy_contact_speed_mps
        ]
        impact_counts.append(len(impact_rows))
        significant_impact_counts.append(len(significant_impacts))
        low_energy_contact_counts.append(len(low_energy_contacts))
        if significant_impacts:
            distance = horizontal_distance_m(significant_impacts[-1], final)
            if distance is not None:
                last_impact_to_final_distances.append(distance)

    gaps = [
        "stop_reason is inferred from final contact_state and final speed; no explicit simulator stop_reason field is present",
        "significant impact is proxied by impact rows with speed_mps >= threshold, not incoming normal speed",
        "terrain slope/normal at final stop is not present in trajectory CSV outputs",
    ]
    if not rows or "contact_state" not in rows[0]:
        gaps.append("contact_state is missing")

    return {
        "source_label": spec.label,
        "source_kind": "trajectory_csv",
        "source_path": str(spec.path),
        "dataset_role": infer_role(spec.label, spec.path),
        "contact_model": infer_contact_model(spec.label, spec.path),
        "row_count": len(rows),
        "trajectory_count": len(by_trajectory),
        "final_status_counts": dict(sorted(final_states.items())),
        "stop_reason_counts": dict(sorted(stop_reasons.items())),
        "final_speed_mean_mps": mean(final_speeds),
        "final_speed_p95_mps": p95(final_speeds),
        "final_speed_max_mps": max_or_none(final_speeds),
        "final_kinetic_mean_j": mean(final_kinetic),
        "final_kinetic_max_j": max_or_none(final_kinetic),
        "impact_count_total": sum(impact_counts),
        "impact_count_mean": mean(float(value) for value in impact_counts),
        "significant_impact_count_total": sum(significant_impact_counts),
        "low_energy_contact_count_total": sum(low_energy_contact_counts),
        "distance_last_significant_impact_to_final_mean_m": mean(last_impact_to_final_distances),
        "distance_last_significant_impact_to_final_max_m": max_or_none(
            last_impact_to_final_distances
        ),
        "runout_mean_m": None,
        "runout_max_m": None,
        "terrain_slope_near_stop_available": False,
        "instrumentation_gaps": gaps,
    }


def summarize_deposition_csv(
    spec: InputSpec,
    *,
    stop_speed_mps: float = DEFAULT_STOP_SPEED_MPS,
) -> dict[str, object]:
    rows = read_csv_dicts(spec.path)
    final_speeds = [value for row in rows if (value := safe_float(row.get("final_speed_mps"))) is not None]
    runouts = [value for row in rows if (value := safe_float(row.get("runout_m"))) is not None]
    stop_reasons = Counter()
    for speed in final_speeds:
        if speed <= stop_speed_mps:
            stop_reasons["final_speed_below_stop_threshold_proxy"] += 1
        else:
            stop_reasons["deposition_row_final_speed_above_threshold"] += 1
    gaps = [
        "deposition CSV gives final point/runout/final_speed only; contact_state history is unavailable",
        "impact counts and last significant impact distance require trajectory or impact-event outputs",
        "terrain slope/normal at final stop is not present in deposition CSV outputs",
    ]
    return {
        "source_label": spec.label,
        "source_kind": "deposition_csv",
        "source_path": str(spec.path),
        "dataset_role": infer_role(spec.label, spec.path),
        "contact_model": infer_contact_model(spec.label, spec.path),
        "row_count": len(rows),
        "trajectory_count": len(rows),
        "final_status_counts": {},
        "stop_reason_counts": dict(sorted(stop_reasons.items())),
        "final_speed_mean_mps": mean(final_speeds),
        "final_speed_p95_mps": p95(final_speeds),
        "final_speed_max_mps": max_or_none(final_speeds),
        "final_kinetic_mean_j": None,
        "final_kinetic_max_j": None,
        "impact_count_total": None,
        "impact_count_mean": None,
        "significant_impact_count_total": None,
        "low_energy_contact_count_total": None,
        "distance_last_significant_impact_to_final_mean_m": None,
        "distance_last_significant_impact_to_final_max_m": None,
        "runout_mean_m": mean(runouts),
        "runout_max_m": max_or_none(runouts),
        "terrain_slope_near_stop_available": False,
        "instrumentation_gaps": gaps,
    }


def summarize_stop_state_csv(spec: InputSpec) -> dict[str, object]:
    rows = read_csv_dicts(spec.path)
    final_speeds = [
        value for row in rows if (value := safe_float(row.get("final_speed_mps"))) is not None
    ]
    final_kinetic = [
        value for row in rows if (value := safe_float(row.get("final_kinetic_j"))) is not None
    ]
    runouts = [value for row in rows if (value := safe_float(row.get("runout_m"))) is not None]
    last_impact_distances = [
        value
        for row in rows
        if (value := safe_float(row.get("distance_last_significant_impact_to_final_m")))
        is not None
    ]
    stop_reasons = Counter(
        value
        for row in rows
        if (value := str(row.get("stop_reason") or "").strip())
    )
    final_states = Counter(
        value
        for row in rows
        if (value := str(row.get("final_contact_state") or "").strip())
    )
    terrain_slope_available = any(
        safe_float(row.get("terrain_slope_abs")) is not None for row in rows
    )
    low_energy_contact_count_total = sum(
        value
        for row in rows
        if (value := safe_int(row.get("low_energy_contact_count"))) is not None
    )
    gaps = []
    if not rows:
        gaps.append("stop-state sidecar is empty")
    if not terrain_slope_available:
        gaps.append("terrain slope/normal at final stop is unavailable")
    if not last_impact_distances:
        gaps.append("no significant impact-to-final distance is available")
    return {
        "source_label": spec.label,
        "source_kind": "ensemble_stop_state_csv",
        "source_path": str(spec.path),
        "dataset_role": infer_role(spec.label, spec.path),
        "contact_model": infer_contact_model(spec.label, spec.path),
        "row_count": len(rows),
        "trajectory_count": len(rows),
        "explicit_stop_state_available": bool(rows),
        "final_status_counts": dict(sorted(final_states.items())),
        "stop_reason_counts": dict(sorted(stop_reasons.items())),
        "final_speed_mean_mps": mean(final_speeds),
        "final_speed_p95_mps": p95(final_speeds),
        "final_speed_max_mps": max_or_none(final_speeds),
        "final_kinetic_mean_j": mean(final_kinetic),
        "final_kinetic_max_j": max_or_none(final_kinetic),
        "impact_count_total": None,
        "impact_count_mean": None,
        "significant_impact_count_total": None,
        "low_energy_contact_count_total": low_energy_contact_count_total,
        "distance_last_significant_impact_to_final_mean_m": mean(last_impact_distances),
        "distance_last_significant_impact_to_final_max_m": max_or_none(last_impact_distances),
        "runout_mean_m": mean(runouts),
        "runout_max_m": max_or_none(runouts),
        "terrain_slope_near_stop_available": terrain_slope_available,
        "instrumentation_gaps": gaps,
    }


def summarize_manifest(spec: InputSpec) -> dict[str, object]:
    manifest = json.loads(spec.path.read_text(encoding="utf-8"))
    performance = manifest.get("performance") or {}
    stop_state_summary = manifest.get("stop_state_summary") or {}
    if stop_state_summary:
        return summarize_stop_state_summary_manifest(
            spec,
            stop_state_summary,
            impact_count_total=safe_int(performance.get("impact_event_count")),
        )
    stop_state = manifest.get("stop_state") or {}
    if stop_state:
        row = summarize_explicit_stop_state(
            spec,
            stop_state,
            source_kind="run_manifest_v1",
            trajectory_count=safe_int(performance.get("trajectory_count")),
            impact_count_total=safe_int(performance.get("impact_event_count")),
        )
        if row["trajectory_count"] not in (None, 1):
            row["instrumentation_gaps"].insert(
                0,
                "manifest stop_state describes the primary single-run trajectory; ensemble stop-state aggregation is not yet instrumented",
            )
        return row
    gaps = [
        "manifest performance fields give aggregate counts only, not per-trajectory stopping state",
        "final speed, final kinetic energy, and last significant impact distance require trajectory/deposition outputs",
    ]
    return {
        "source_label": spec.label,
        "source_kind": "run_manifest_v1",
        "source_path": str(spec.path),
        "dataset_role": infer_role(spec.label, spec.path),
        "contact_model": infer_contact_model(spec.label, spec.path),
        "row_count": None,
        "trajectory_count": safe_int(performance.get("trajectory_count")),
        "final_status_counts": {},
        "stop_reason_counts": {},
        "final_speed_mean_mps": None,
        "final_speed_p95_mps": None,
        "final_speed_max_mps": None,
        "final_kinetic_mean_j": None,
        "final_kinetic_max_j": None,
        "impact_count_total": safe_int(performance.get("impact_event_count")),
        "impact_count_mean": None,
        "significant_impact_count_total": None,
        "low_energy_contact_count_total": None,
        "distance_last_significant_impact_to_final_mean_m": None,
        "distance_last_significant_impact_to_final_max_m": None,
        "runout_mean_m": None,
        "runout_max_m": None,
        "terrain_slope_near_stop_available": False,
        "instrumentation_gaps": gaps,
    }


def summarize_stop_state_summary_manifest(
    spec: InputSpec,
    stop_state_summary: dict[str, object],
    *,
    impact_count_total: int | None,
) -> dict[str, object]:
    gaps = list(stop_state_summary.get("limitations") or [])
    if not stop_state_summary.get("terrain_slope_available_count"):
        gaps.append("terrain slope/normal at final stop is unavailable")
    return {
        "source_label": spec.label,
        "source_kind": "run_manifest_stop_state_summary_v1",
        "source_path": str(spec.path),
        "dataset_role": infer_role(spec.label, spec.path),
        "contact_model": infer_contact_model(spec.label, spec.path),
        "row_count": None,
        "trajectory_count": safe_int(stop_state_summary.get("trajectory_count")),
        "explicit_stop_state_available": bool(
            safe_int(stop_state_summary.get("explicit_stop_state_count")) or 0
        ),
        "stop_reason": None,
        "final_contact_state": None,
        "termination_low_velocity": None,
        "termination_max_steps": None,
        "termination_t_max": None,
        "termination_domain_exit": None,
        "termination_terrain_error": None,
        "last_significant_impact_time_s": None,
        "terrain_normal_x": None,
        "terrain_normal_y": None,
        "terrain_normal_z": None,
        "terrain_slope_abs": None,
        "final_status_counts": stop_state_summary.get("final_contact_state_counts") or {},
        "stop_reason_counts": stop_state_summary.get("stop_reason_counts") or {},
        "final_speed_mean_mps": safe_float(stop_state_summary.get("final_speed_mean_mps")),
        "final_speed_p95_mps": None,
        "final_speed_max_mps": safe_float(stop_state_summary.get("final_speed_max_mps")),
        "final_kinetic_mean_j": safe_float(stop_state_summary.get("final_kinetic_mean_j")),
        "final_kinetic_max_j": safe_float(stop_state_summary.get("final_kinetic_max_j")),
        "impact_count_total": impact_count_total,
        "impact_count_mean": None,
        "significant_impact_count_total": None,
        "low_energy_contact_count_total": safe_int(
            stop_state_summary.get("low_energy_contact_count_total")
        ),
        "distance_last_significant_impact_to_final_mean_m": None,
        "distance_last_significant_impact_to_final_max_m": None,
        "runout_mean_m": None,
        "runout_max_m": None,
        "terrain_slope_near_stop_available": bool(
            safe_int(stop_state_summary.get("terrain_slope_available_count")) or 0
        ),
        "instrumentation_gaps": gaps,
    }


def summarize_explicit_stop_state(
    spec: InputSpec,
    stop_state: dict[str, object],
    *,
    source_kind: str,
    trajectory_count: int | None,
    impact_count_total: int | None,
) -> dict[str, object]:
    final_contact_state = stop_state.get("final_contact_state")
    stop_reason = stop_state.get("stop_reason")
    termination = stop_state.get("termination_flags") or {}
    gaps = []
    if stop_state.get("last_significant_impact_time_s") is None:
        gaps.append("no significant impact reached the explicit incoming-normal-speed threshold")
    if not all(
        stop_state.get(field) is not None
        for field in ("terrain_normal_x", "terrain_normal_y", "terrain_normal_z")
    ):
        gaps.append("terrain normal at final position is unavailable")
    return {
        "source_label": spec.label,
        "source_kind": source_kind,
        "source_path": str(spec.path),
        "dataset_role": infer_role(spec.label, spec.path),
        "contact_model": infer_contact_model(spec.label, spec.path),
        "row_count": None,
        "trajectory_count": trajectory_count,
        "explicit_stop_state_available": True,
        "stop_reason": stop_reason,
        "final_contact_state": final_contact_state,
        "termination_low_velocity": bool(termination.get("low_velocity")),
        "termination_max_steps": bool(termination.get("max_steps")),
        "termination_t_max": bool(termination.get("t_max")),
        "termination_domain_exit": bool(termination.get("domain_exit")),
        "termination_terrain_error": bool(termination.get("terrain_error")),
        "last_significant_impact_time_s": stop_state.get("last_significant_impact_time_s"),
        "terrain_normal_x": stop_state.get("terrain_normal_x"),
        "terrain_normal_y": stop_state.get("terrain_normal_y"),
        "terrain_normal_z": stop_state.get("terrain_normal_z"),
        "terrain_slope_abs": stop_state.get("terrain_slope_abs"),
        "final_status_counts": ({final_contact_state: 1} if final_contact_state else {}),
        "stop_reason_counts": ({stop_reason: 1} if stop_reason else {}),
        "final_speed_mean_mps": safe_float(stop_state.get("final_speed_mps")),
        "final_speed_p95_mps": safe_float(stop_state.get("final_speed_mps")),
        "final_speed_max_mps": safe_float(stop_state.get("final_speed_mps")),
        "final_kinetic_mean_j": safe_float(stop_state.get("final_kinetic_j")),
        "final_kinetic_max_j": safe_float(stop_state.get("final_kinetic_j")),
        "impact_count_total": impact_count_total,
        "impact_count_mean": None,
        "significant_impact_count_total": None,
        "low_energy_contact_count_total": safe_int(stop_state.get("low_energy_contact_count")),
        "distance_last_significant_impact_to_final_mean_m": safe_float(
            stop_state.get("distance_last_significant_impact_to_final_m")
        ),
        "distance_last_significant_impact_to_final_max_m": safe_float(
            stop_state.get("distance_last_significant_impact_to_final_m")
        ),
        "runout_mean_m": None,
        "runout_max_m": None,
        "terrain_slope_near_stop_available": stop_state.get("terrain_slope_abs") is not None,
        "instrumentation_gaps": gaps,
    }


def summarize_diagnostics_json(spec: InputSpec) -> dict[str, object]:
    report = json.loads(spec.path.read_text(encoding="utf-8"))
    stop_state = report.get("stop_state") or {}
    if stop_state:
        metrics = report.get("metrics") or {}
        trajectory_count = safe_int(metrics.get("validation_trajectory_count")) or 1
        impact_count_total = safe_int(
            metrics.get("impact_event_count")
            or metrics.get("impact_count")
            or metrics.get("contact_event_compared_count")
        )
        return summarize_explicit_stop_state(
            spec,
            stop_state,
            source_kind="diagnostics_json",
            trajectory_count=trajectory_count,
            impact_count_total=impact_count_total,
        )
    gaps = [
        "diagnostics JSON does not contain explicit stop_state; use trajectory/deposition outputs for proxy fallback",
    ]
    return {
        "source_label": spec.label,
        "source_kind": "diagnostics_json",
        "source_path": str(spec.path),
        "dataset_role": infer_role(spec.label, spec.path),
        "contact_model": infer_contact_model(spec.label, spec.path),
        "row_count": None,
        "trajectory_count": None,
        "final_status_counts": {},
        "stop_reason_counts": {},
        "final_speed_mean_mps": None,
        "final_speed_p95_mps": None,
        "final_speed_max_mps": None,
        "final_kinetic_mean_j": None,
        "final_kinetic_max_j": None,
        "impact_count_total": None,
        "impact_count_mean": None,
        "significant_impact_count_total": None,
        "low_energy_contact_count_total": None,
        "distance_last_significant_impact_to_final_mean_m": None,
        "distance_last_significant_impact_to_final_max_m": None,
        "runout_mean_m": None,
        "runout_max_m": None,
        "terrain_slope_near_stop_available": False,
        "instrumentation_gaps": gaps,
    }


FIELDNAMES = [
    "source_label",
    "source_kind",
    "dataset_role",
    "contact_model",
    "trajectory_count",
    "row_count",
    "explicit_stop_state_available",
    "stop_reason",
    "final_contact_state",
    "termination_low_velocity",
    "termination_max_steps",
    "termination_t_max",
    "termination_domain_exit",
    "termination_terrain_error",
    "last_significant_impact_time_s",
    "terrain_normal_x",
    "terrain_normal_y",
    "terrain_normal_z",
    "terrain_slope_abs",
    "final_status_counts",
    "stop_reason_counts",
    "final_speed_mean_mps",
    "final_speed_p95_mps",
    "final_speed_max_mps",
    "final_kinetic_mean_j",
    "final_kinetic_max_j",
    "impact_count_total",
    "impact_count_mean",
    "significant_impact_count_total",
    "low_energy_contact_count_total",
    "distance_last_significant_impact_to_final_mean_m",
    "distance_last_significant_impact_to_final_max_m",
    "runout_mean_m",
    "runout_max_m",
    "terrain_slope_near_stop_available",
    "instrumentation_gaps",
    "source_path",
]


def format_cell(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.6g}"
    if isinstance(value, (dict, list)):
        return json.dumps(value, sort_keys=True)
    return str(value)


def write_csv(rows: list[dict[str, object]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: format_cell(row.get(field)) for field in FIELDNAMES})


def write_markdown(rows: list[dict[str, object]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Stopping Behavior Diagnostic Summary",
        "",
        "Generated by `scripts/summarize_stopping_behavior.py` from existing outputs.",
        "This is diagnostic evidence only; it does not rerun simulations or change baselines.",
        "",
        "| Source | Kind | Role | Contact model | Traj. | Final speed mean (m/s) | Runout mean (m) | Impact count | Stop reasons |",
        "| --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            "| {source_label} | {source_kind} | {dataset_role} | {contact_model} | {trajectory_count} | {final_speed_mean_mps} | {runout_mean_m} | {impact_count_total} | `{stop_reason_counts}` |".format(
                **{field: format_cell(row.get(field)) for field in FIELDNAMES}
            )
        )
    lines.extend(
        [
            "",
            "## Instrumentation Gaps",
            "",
        ]
    )
    for row in rows:
        gaps = row.get("instrumentation_gaps") or []
        if gaps:
            lines.append(f"- `{row['source_label']}`: " + "; ".join(str(gap) for gap in gaps))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_rows(args: argparse.Namespace) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for spec in args.trajectory:
        rows.append(
            summarize_trajectory_csv(
                parse_spec(spec),
                stop_speed_mps=args.stop_speed_mps,
                low_energy_contact_speed_mps=args.low_energy_contact_speed_mps,
                significant_impact_speed_mps=args.significant_impact_speed_mps,
            )
        )
    for spec in args.deposition:
        rows.append(summarize_deposition_csv(parse_spec(spec), stop_speed_mps=args.stop_speed_mps))
    for spec in args.stop_state:
        rows.append(summarize_stop_state_csv(parse_spec(spec)))
    for spec in args.manifest:
        rows.append(summarize_manifest(parse_spec(spec)))
    for spec in args.diagnostics:
        rows.append(summarize_diagnostics_json(parse_spec(spec)))
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Summarize stopping-behavior diagnostics from existing outputs."
    )
    parser.add_argument("--trajectory", action="append", default=[], help="label:path trajectory CSV")
    parser.add_argument("--deposition", action="append", default=[], help="label:path deposition CSV")
    parser.add_argument(
        "--stop-state",
        action="append",
        default=[],
        help="label:path ensemble stop-state sidecar CSV",
    )
    parser.add_argument("--manifest", action="append", default=[], help="label:path run manifest JSON")
    parser.add_argument("--diagnostics", action="append", default=[], help="label:path diagnostics JSON")
    parser.add_argument("--output-csv", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--stop-speed-mps", type=float, default=DEFAULT_STOP_SPEED_MPS)
    parser.add_argument(
        "--low-energy-contact-speed-mps",
        type=float,
        default=DEFAULT_LOW_ENERGY_CONTACT_SPEED_MPS,
    )
    parser.add_argument(
        "--significant-impact-speed-mps",
        type=float,
        default=DEFAULT_SIGNIFICANT_IMPACT_SPEED_MPS,
    )
    args = parser.parse_args()
    rows = build_rows(args)
    if args.output_csv:
        write_csv(rows, args.output_csv)
    if args.output_md:
        write_markdown(rows, args.output_md)
    if not args.output_csv and not args.output_md:
        print(json.dumps(rows, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
