#!/usr/bin/env python3
"""Build a terrain/material diagnostic matrix from stopping summaries.

This is a reporting helper only. It does not run simulations, tune parameters,
change baselines, or select physics. Inputs should come from
scripts/summarize_stopping_behavior.py.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


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


def parse_mapping_keys(value: object) -> list[str]:
    if value is None:
        return []
    text = str(value).strip()
    if not text:
        return []
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return [text]
    if isinstance(parsed, dict):
        return [str(key) for key in sorted(parsed)]
    if isinstance(parsed, list):
        return [str(item) for item in parsed]
    return [str(parsed)]


def boolish(value: object) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def slope_bin(value: object) -> str:
    slope = safe_float(value)
    if slope is None:
        return "unknown"
    if slope < 0.20:
        return "flat_to_low"
    if slope < 0.60:
        return "moderate"
    return "steep"


def count_bin(value: object) -> str:
    count = safe_float(value)
    if count is None:
        return "unknown"
    if count <= 0:
        return "none"
    if count < 100:
        return "low"
    return "high"


def final_speed_bin(value: object) -> str:
    speed = safe_float(value)
    if speed is None:
        return "unknown"
    if speed <= 0.05:
        return "stopped_or_near_stopped"
    if speed <= 5.0:
        return "moving"
    return "high_speed"


def runout_class(value: object) -> str:
    runout = safe_float(value)
    if runout is None:
        return "unknown"
    if runout < 75.0:
        return "short"
    if runout <= 150.0:
        return "mid"
    return "long"


def evidence_mode(row: dict[str, str]) -> str:
    return "explicit_stop_state" if boolish(row.get("explicit_stop_state_available")) else "proxy_fallback"


def label_from_row(row: dict[str, str], direct_field: str, counts_field: str) -> str:
    direct = str(row.get(direct_field) or "").strip()
    if direct:
        return direct
    keys = parse_mapping_keys(row.get(counts_field))
    return "+".join(keys) if keys else "unknown"


def weighted_mean(values: Iterable[tuple[float, int]]) -> float | None:
    total_weight = 0
    total = 0.0
    for value, weight in values:
        total += value * weight
        total_weight += weight
    if total_weight == 0:
        return None
    return total / total_weight


@dataclass
class Aggregate:
    rows: int = 0
    trajectory_count: int = 0
    final_speed: list[tuple[float, int]] = field(default_factory=list)
    final_kinetic: list[tuple[float, int]] = field(default_factory=list)
    low_energy_contact_count_total: int = 0
    impact_count_total: int = 0
    distance_last_impact: list[tuple[float, int]] = field(default_factory=list)
    source_labels: set[str] = field(default_factory=set)
    instrumentation_gaps: set[str] = field(default_factory=set)


GROUP_FIELDS = [
    "dataset_role",
    "contact_model",
    "evidence_mode",
    "stop_reason",
    "final_contact_state",
    "terrain_slope_abs_bin",
    "low_energy_contact_count_bin",
    "impact_count_bin",
    "final_speed_bin",
    "runout_class",
]


FIELDNAMES = GROUP_FIELDS + [
    "matrix_row_count",
    "trajectory_count",
    "final_speed_mean_mps",
    "final_kinetic_mean_j",
    "low_energy_contact_count_total",
    "impact_count_total",
    "distance_last_significant_impact_to_final_mean_m",
    "source_labels",
    "instrumentation_gaps",
]


def matrix_key(row: dict[str, str]) -> dict[str, str]:
    return {
        "dataset_role": row.get("dataset_role") or "unknown",
        "contact_model": row.get("contact_model") or "unknown",
        "evidence_mode": evidence_mode(row),
        "stop_reason": label_from_row(row, "stop_reason", "stop_reason_counts"),
        "final_contact_state": label_from_row(row, "final_contact_state", "final_status_counts"),
        "terrain_slope_abs_bin": slope_bin(row.get("terrain_slope_abs")),
        "low_energy_contact_count_bin": count_bin(row.get("low_energy_contact_count_total")),
        "impact_count_bin": count_bin(row.get("impact_count_total")),
        "final_speed_bin": final_speed_bin(row.get("final_speed_mean_mps")),
        "runout_class": runout_class(row.get("runout_mean_m")),
    }


def build_matrix(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    aggregates: dict[tuple[str, ...], Aggregate] = defaultdict(Aggregate)
    keys_by_tuple: dict[tuple[str, ...], dict[str, str]] = {}
    for row in rows:
        key = matrix_key(row)
        key_tuple = tuple(key[field] for field in GROUP_FIELDS)
        keys_by_tuple[key_tuple] = key
        aggregate = aggregates[key_tuple]
        aggregate.rows += 1
        weight = safe_int(row.get("trajectory_count")) or safe_int(row.get("row_count")) or 1
        aggregate.trajectory_count += weight
        if (value := safe_float(row.get("final_speed_mean_mps"))) is not None:
            aggregate.final_speed.append((value, weight))
        if (value := safe_float(row.get("final_kinetic_mean_j"))) is not None:
            aggregate.final_kinetic.append((value, weight))
        if (value := safe_int(row.get("low_energy_contact_count_total"))) is not None:
            aggregate.low_energy_contact_count_total += value
        if (value := safe_int(row.get("impact_count_total"))) is not None:
            aggregate.impact_count_total += value
        if (
            value := safe_float(row.get("distance_last_significant_impact_to_final_mean_m"))
        ) is not None:
            aggregate.distance_last_impact.append((value, weight))
        if label := row.get("source_label"):
            aggregate.source_labels.add(label)
        for gap in parse_mapping_keys(row.get("instrumentation_gaps")):
            aggregate.instrumentation_gaps.add(gap)

    matrix = []
    for key_tuple in sorted(aggregates):
        aggregate = aggregates[key_tuple]
        key = keys_by_tuple[key_tuple]
        matrix.append(
            {
                **key,
                "matrix_row_count": aggregate.rows,
                "trajectory_count": aggregate.trajectory_count,
                "final_speed_mean_mps": weighted_mean(aggregate.final_speed),
                "final_kinetic_mean_j": weighted_mean(aggregate.final_kinetic),
                "low_energy_contact_count_total": aggregate.low_energy_contact_count_total,
                "impact_count_total": aggregate.impact_count_total,
                "distance_last_significant_impact_to_final_mean_m": weighted_mean(
                    aggregate.distance_last_impact
                ),
                "source_labels": sorted(aggregate.source_labels),
                "instrumentation_gaps": sorted(aggregate.instrumentation_gaps),
            }
        )
    return matrix


def format_cell(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.6g}"
    if isinstance(value, (dict, list)):
        return json.dumps(value, sort_keys=True)
    return str(value)


def read_summary_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


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
        "# Terrain/Material Diagnostic Matrix",
        "",
        "Generated from stopping-behavior summaries. This matrix is diagnostic only.",
        "",
        "| Role | Contact model | Evidence | Stop reason | Final state | Slope bin | Low-energy contacts | Impacts | Speed bin | Runout class | Traj. | Final speed mean m/s | Sources |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | ---: | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            "| {dataset_role} | {contact_model} | {evidence_mode} | {stop_reason} | {final_contact_state} | {terrain_slope_abs_bin} | {low_energy_contact_count_bin} | {impact_count_bin} | {final_speed_bin} | {runout_class} | {trajectory_count} | {final_speed_mean_mps} | `{source_labels}` |".format(
                **{field: format_cell(row.get(field)) for field in FIELDNAMES}
            )
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build a no-tuning terrain/material diagnostic matrix from stopping summaries."
    )
    parser.add_argument("--input-csv", action="append", type=Path, required=True)
    parser.add_argument("--output-csv", type=Path)
    parser.add_argument("--output-md", type=Path)
    args = parser.parse_args()

    rows: list[dict[str, str]] = []
    for path in args.input_csv:
        rows.extend(read_summary_csv(path))
    matrix = build_matrix(rows)
    if args.output_csv:
        write_csv(matrix, args.output_csv)
    if args.output_md:
        write_markdown(matrix, args.output_md)
    if not args.output_csv and not args.output_md:
        print(json.dumps(matrix, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
