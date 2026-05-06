#!/usr/bin/env python3
"""Summarize Chant Sura contact diagnostics from existing validation metrics.

This reporting helper does not run simulations. It reads generated
`validation/results/*metrics.json` files and checked-in processed contact-event
CSV files, then writes a compact diagnostic report that keeps proxy limitations
visible for future contact/shape-model decisions.
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_ROOT = ROOT / "validation" / "results" / "chant_sura_contact_diagnostics"


@dataclass(frozen=True)
class CaseSpec:
    subset: str
    contact_model: str
    metrics_path: Path


CASE_SPECS = [
    CaseSpec("original", "translational_v0", ROOT / "validation/results/chant_sura_contact_metrics.json"),
    CaseSpec("original", "sphere_rotational_v1", ROOT / "validation/results/chant_sura_contact_rotational_metrics.json"),
    CaseSpec("original", "stochastic_contact_v1", ROOT / "validation/results/chant_sura_contact_roughness_metrics.json"),
    CaseSpec("original", "scarring_contact_v1", ROOT / "validation/results/chant_sura_contact_scarring_metrics.json"),
    CaseSpec("extended", "translational_v0", ROOT / "validation/results/chant_sura_contact_extended_metrics.json"),
    CaseSpec(
        "extended",
        "sphere_rotational_v1",
        ROOT / "validation/results/chant_sura_contact_extended_rotational_metrics.json",
    ),
    CaseSpec("extended", "stochastic_contact_v1", ROOT / "validation/results/chant_sura_contact_extended_roughness_metrics.json"),
    CaseSpec("extended", "scarring_contact_v1", ROOT / "validation/results/chant_sura_contact_extended_scarring_metrics.json"),
    CaseSpec("heldout", "translational_v0", ROOT / "validation/results/chant_sura_contact_heldout_metrics.json"),
    CaseSpec(
        "heldout",
        "sphere_rotational_v1",
        ROOT / "validation/results/chant_sura_contact_heldout_rotational_metrics.json",
    ),
]

CONTACT_EVENT_FILES = {
    "original": ROOT / "validation/data/processed/chant_sura_2020/observed_contact_events.csv",
    "extended": ROOT / "validation/data/processed/chant_sura_2020/observed_contact_events_extended.csv",
    "heldout": ROOT / "validation/data/processed/chant_sura_2020/observed_contact_events_heldout.csv",
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    args = parser.parse_args(argv)

    output_root = args.output_root if args.output_root.is_absolute() else ROOT / args.output_root
    output_root.mkdir(parents=True, exist_ok=True)
    report = build_report()
    (output_root / "chant_sura_contact_diagnostics.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n"
    )
    (output_root / "chant_sura_contact_diagnostics.md").write_text(render_markdown(report))
    print(f"wrote Chant Sura contact diagnostics to {output_root}")
    return 0


def build_report(
    case_specs: list[CaseSpec] | None = None,
    contact_event_files: dict[str, Path] | None = None,
) -> dict[str, Any]:
    case_specs = CASE_SPECS if case_specs is None else case_specs
    contact_event_files = CONTACT_EVENT_FILES if contact_event_files is None else contact_event_files
    case_rows = [case_summary(spec) for spec in case_specs]
    event_summaries = {
        subset: contact_event_summary(path) for subset, path in contact_event_files.items()
    }
    return {
        "schema_version": "chant_sura_contact_diagnostic_summary_v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "source": "generated validation metrics and checked-in processed Chant Sura contact proxy CSV files",
        "proxy_confidence": {
            "contact_event_source": "segment_boundary_local_time_reset",
            "direct_impact_sensor_events": False,
            "interpretation": (
                "Rebound velocity, impact timing, and post-impact energy changes are "
                "segment-boundary proxy diagnostics. They support model comparison but "
                "are not instrumented impact truth."
            ),
        },
        "case_summaries": case_rows,
        "relative_changes": relative_changes(case_rows),
        "contact_event_inputs": event_summaries,
        "interpretation": [
            "sphere_rotational_v1 consistently improves trajectory-shape and kinetic-energy metrics on extended and held-out subsets.",
            "rebound velocity and jump-height envelope do not show a corresponding robust improvement.",
            "impact timing remains proxy-limited and nearly unchanged across current contact options.",
            "the result supports opt-in shape/contact research, not a default change or parameter tuning.",
        ],
    }


def case_summary(spec: CaseSpec) -> dict[str, Any]:
    data = json.loads(spec.metrics_path.read_text())
    metrics = data.get("metrics") or {}
    return {
        "subset": spec.subset,
        "contact_model": spec.contact_model,
        "metrics_path": relative(spec.metrics_path),
        "trajectory_shape_mean_error_m": metrics.get("trajectory_shape_mean_error_m"),
        "trajectory_energy_mean_relative_error": metrics.get("trajectory_energy_mean_relative_error"),
        "trajectory_jump_height_envelope_error_m": metrics.get("trajectory_jump_height_envelope_error_m"),
        "impact_timing_mean_error_s": metrics.get("impact_timing_mean_error_s"),
        "rebound_velocity_mean_error_mps": metrics.get("rebound_velocity_mean_error_mps"),
        "contact_event_compared_count": metrics.get("contact_event_compared_count"),
        "observed_contact_event_count": metrics.get("observed_contact_event_count"),
        "post_impact_energy_change_mean_error_j": metrics.get("post_impact_energy_change_mean_error_j"),
    }


def contact_event_summary(path: Path) -> dict[str, Any]:
    with path.open() as file:
        rows = list(csv.DictReader(file))
    incoming = [float(row["incoming_speed_mps"]) for row in rows if row.get("incoming_speed_mps")]
    rebound = [float(row["outgoing_speed_mps"]) for row in rows if row.get("outgoing_speed_mps")]
    energy = []
    for row in rows:
        if row.get("post_impact_energy_change_j"):
            energy.append(float(row["post_impact_energy_change_j"]))
        elif row.get("pre_impact_kinetic_j") and row.get("post_impact_kinetic_j"):
            energy.append(float(row["post_impact_kinetic_j"]) - float(row["pre_impact_kinetic_j"]))
    return {
        "path": relative(path),
        "proxy_event_count": len(rows),
        "mean_observed_incoming_speed_mps": mean(incoming),
        "mean_observed_rebound_speed_mps": mean(rebound),
        "mean_observed_post_impact_energy_change_j": mean(energy),
        "proxy_limitation": "segment boundary, not direct impact sensor",
    }


def relative_changes(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    changes: list[dict[str, Any]] = []
    by_subset_model = {(row["subset"], row["contact_model"]): row for row in rows}
    for subset in ("original", "extended", "heldout"):
        baseline = by_subset_model.get((subset, "translational_v0"))
        rotational = by_subset_model.get((subset, "sphere_rotational_v1"))
        if baseline is None or rotational is None:
            continue
        changes.append(
            {
                "subset": subset,
                "comparison": "sphere_rotational_v1_vs_translational_v0",
                "shape_error_relative_change": relative_change(
                    baseline.get("trajectory_shape_mean_error_m"),
                    rotational.get("trajectory_shape_mean_error_m"),
                ),
                "energy_error_relative_change": relative_change(
                    baseline.get("trajectory_energy_mean_relative_error"),
                    rotational.get("trajectory_energy_mean_relative_error"),
                ),
                "jump_envelope_error_relative_change": relative_change(
                    baseline.get("trajectory_jump_height_envelope_error_m"),
                    rotational.get("trajectory_jump_height_envelope_error_m"),
                ),
                "rebound_velocity_error_relative_change": relative_change(
                    baseline.get("rebound_velocity_mean_error_mps"),
                    rotational.get("rebound_velocity_mean_error_mps"),
                ),
            }
        )
    return changes


def relative_change(base: Any, candidate: Any) -> float | None:
    if not isinstance(base, (int, float)) or not isinstance(candidate, (int, float)) or base == 0:
        return None
    return float((candidate - base) / base)


def mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Chant Sura Contact Diagnostic Summary",
        "",
        "This report reads existing validation metrics and processed contact-proxy CSV files. It does not run simulations or tune parameters.",
        "",
        "## Case Metrics",
        "",
        "| Subset | Contact model | Shape mean error (m) | Energy relative error | Jump envelope error (m) | Timing error (s) | Rebound velocity error (m/s) | Events |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in report["case_summaries"]:
        lines.append(
            "| "
            f"{row['subset']} | `{row['contact_model']}` | "
            f"{fmt(row['trajectory_shape_mean_error_m'])} | "
            f"{fmt(row['trajectory_energy_mean_relative_error'])} | "
            f"{fmt(row['trajectory_jump_height_envelope_error_m'])} | "
            f"{fmt(row['impact_timing_mean_error_s'])} | "
            f"{fmt(row['rebound_velocity_mean_error_mps'])} | "
            f"{fmt(row['contact_event_compared_count'])} |"
        )
    lines.extend(["", "## Relative Rotational Changes", ""])
    lines.append("| Subset | Shape error | Energy error | Jump envelope error | Rebound velocity error |")
    lines.append("| --- | ---: | ---: | ---: | ---: |")
    for row in report["relative_changes"]:
        lines.append(
            "| "
            f"{row['subset']} | "
            f"{fmt_pct(row['shape_error_relative_change'])} | "
            f"{fmt_pct(row['energy_error_relative_change'])} | "
            f"{fmt_pct(row['jump_envelope_error_relative_change'])} | "
            f"{fmt_pct(row['rebound_velocity_error_relative_change'])} |"
        )
    lines.extend(["", "## Contact Proxy Inputs", ""])
    lines.append("| Subset | Proxy events | Mean incoming speed (m/s) | Mean rebound speed (m/s) | Mean post-impact energy change (J) |")
    lines.append("| --- | ---: | ---: | ---: | ---: |")
    for subset, row in report["contact_event_inputs"].items():
        lines.append(
            f"| {subset} | {row['proxy_event_count']} | {fmt(row['mean_observed_incoming_speed_mps'])} | "
            f"{fmt(row['mean_observed_rebound_speed_mps'])} | {fmt(row['mean_observed_post_impact_energy_change_j'])} |"
        )
    lines.extend(["", "## Interpretation", ""])
    lines.extend(f"- {item}" for item in report["interpretation"])
    lines.extend(["", "## Proxy Limitation", "", report["proxy_confidence"]["interpretation"], ""])
    return "\n".join(lines)


def fmt(value: Any) -> str:
    return "" if value is None else f"{float(value):.3f}"


def fmt_pct(value: Any) -> str:
    return "" if value is None else f"{100.0 * float(value):.1f}%"


if __name__ == "__main__":
    raise SystemExit(main())
