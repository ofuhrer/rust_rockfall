#!/usr/bin/env python3
"""Collect public Tschamut registration-sensitivity classifications.

The collector reads already-generated public Tschamut benchmark result roots for
the three documented coordinate transforms. It does not run simulations, tune
parameters, or modify preparation manifests. Its output is the classification
table required before public Tschamut can be used as physics-selection evidence.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPORT_SCHEMA_VERSION = "tschamut_registration_sensitivity_report_v1"
REQUIRED_TRANSFORMS = ("scan_surface_fit_v1", "bbox_align_v1", "overview_offset_v1")
CONTACT_CASES = {
    "translational_v0": "baseline",
    "sphere_rotational_v1": "rotational",
}
RUNOUT_THRESHOLD_M = 10.0


@dataclass(frozen=True)
class TransformInput:
    method: str
    root: Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        action="append",
        default=[],
        metavar="METHOD=RESULT_ROOT",
        help=(
            "generated Tschamut benchmark root for one transform; repeat for "
            "scan_surface_fit_v1, bbox_align_v1, and overview_offset_v1"
        ),
    )
    parser.add_argument(
        "--run-subset",
        default="all_usable_public_runs",
        help="stable subset label to record in classification rows",
    )
    parser.add_argument("--output-json", type=Path, help="optional report JSON path")
    parser.add_argument("--output-md", type=Path, help="optional Markdown table path")
    args = parser.parse_args(argv)

    inputs = parse_inputs(args.input)
    report = build_report(inputs, run_subset=args.run_subset)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(text)
    if args.output_md:
        args.output_md.parent.mkdir(parents=True, exist_ok=True)
        args.output_md.write_text(render_markdown(report))
    if not args.output_json and not args.output_md:
        print(text, end="")
    return 0 if report["classification_stability_reported"] else 2


def parse_inputs(values: list[str]) -> list[TransformInput]:
    inputs: list[TransformInput] = []
    for value in values:
        if "=" not in value:
            raise SystemExit(f"--input must use METHOD=RESULT_ROOT, got {value!r}")
        method, raw_root = value.split("=", 1)
        method = method.strip()
        if method not in REQUIRED_TRANSFORMS:
            raise SystemExit(f"unsupported transform method in --input: {method}")
        root = Path(raw_root.strip())
        if not root.is_absolute():
            root = ROOT / root
        inputs.append(TransformInput(method=method, root=root))
    return inputs


def build_report(inputs: list[TransformInput], *, run_subset: str) -> dict[str, Any]:
    by_method = {item.method: item for item in inputs}
    rows: list[dict[str, Any]] = []
    missing_evidence: list[str] = []
    input_summaries: list[dict[str, Any]] = []

    for method in REQUIRED_TRANSFORMS:
        item = by_method.get(method)
        if item is None:
            missing_evidence.append(f"missing input root for {method}")
            continue
        summary, errors = inspect_transform_input(item)
        input_summaries.append(summary)
        missing_evidence.extend(errors)
        for contact_model, case_name in CONTACT_CASES.items():
            metrics_path = metrics_file(item.root, case_name)
            if not metrics_path.exists():
                missing_evidence.append(f"missing metrics for {method}/{contact_model}: {relative(metrics_path)}")
                continue
            rows.append(classify_metrics(method, contact_model, run_subset, metrics_path))

    stability = classification_stability(rows)
    complete = not missing_evidence and required_rows_present(rows)
    physics_selection_allowed = complete and stability["stable_across_transforms"]

    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "benchmark_id": "tschamut",
        "dataset_id": "tschamut2014",
        "run_subset": run_subset,
        "required_methods": list(REQUIRED_TRANSFORMS),
        "required_contact_models": list(CONTACT_CASES),
        "classification_stability_reported": complete,
        "classification_stable_across_transforms": stability["stable_across_transforms"],
        "physics_selection_allowed": physics_selection_allowed,
        "classification_sensitivity": rows,
        "stability_by_contact_model": stability["by_contact_model"],
        "inputs": input_summaries,
        "missing_evidence": missing_evidence,
        "limitations": [
            "No simulations are run by this collector; it only reads generated no-tuning benchmark metrics.",
            "The classification table is valid for physics-selection discussion only when all required transforms and contact models are present.",
            "Passive shape metadata remains passive and is not interpreted as shape-dependent dynamics.",
            "The report is not an operational hazard assessment.",
        ],
    }


def inspect_transform_input(item: TransformInput) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    manifest_path = item.root / "preparation_manifest.json"
    manifest: dict[str, Any] = {}
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text())
        except Exception as exc:
            errors.append(f"could not parse {relative(manifest_path)}: {exc}")
    else:
        errors.append(f"missing preparation manifest for {item.method}: {relative(manifest_path)}")

    manifest_method = ((manifest.get("transform") or {}).get("method") if manifest else None)
    if manifest_method and manifest_method != item.method:
        errors.append(
            f"manifest transform mismatch for {relative(manifest_path)}: "
            f"input={item.method}, manifest={manifest_method}"
        )
    selected_ids = manifest.get("selected_ids") or (manifest.get("selection") or {}).get("selected_trajectory_ids")
    return (
        {
            "transform_method": item.method,
            "result_root": relative(item.root),
            "preparation_manifest": relative(manifest_path),
            "manifest_transform_method": manifest_method,
            "selected_run_count": len(selected_ids) if isinstance(selected_ids, list) else None,
        },
        errors,
    )


def classify_metrics(
    method: str,
    contact_model: str,
    run_subset: str,
    path: Path,
) -> dict[str, Any]:
    data = json.loads(path.read_text())
    actual_contact_model = (data.get("parameters") or {}).get("contact_model")
    if actual_contact_model and actual_contact_model != contact_model:
        raise SystemExit(
            f"{relative(path)} contact_model mismatch: expected {contact_model}, got {actual_contact_model}"
        )
    metrics = data.get("metrics") or {}
    observed = require_number(metrics, "observed_mean_runout_m", path)
    simulated = require_number(metrics, "simulated_mean_runout_m", path)
    signed_error = simulated - observed
    runout_class = classify_runout(signed_error)
    overlap = number_or_none(metrics.get("deposition_cloud_overlap_fraction"))
    deposition_class = classify_deposition_overlap(overlap)
    return {
        "transform_method": method,
        "run_subset": run_subset,
        "contact_model": contact_model,
        "classification": f"{runout_class}_{deposition_class}",
        "runout_classification": runout_class,
        "deposition_classification": deposition_class,
        "classification_rule": (
            f"runout uses simulated_mean_runout_m - observed_mean_runout_m with "
            f"+/-{RUNOUT_THRESHOLD_M:g} m threshold; deposition uses observed-cloud overlap classes"
        ),
        "grouped_metrics": {
            "observed_mean_runout_m": observed,
            "simulated_mean_runout_m": simulated,
            "signed_runout_error_m": signed_error,
            "absolute_runout_distance_error_m": number_or_none(metrics.get("runout_distance_error_m")),
            "deposition_centroid_error_m": number_or_none(metrics.get("deposition_centroid_error_m")),
            "deposition_cloud_mean_nearest_error_m": number_or_none(
                metrics.get("deposition_cloud_mean_nearest_error_m")
            ),
            "deposition_cloud_overlap_fraction": overlap,
            "lateral_spread_error_m": number_or_none(metrics.get("lateral_spread_error_m")),
            "validation_release_count": number_or_none(metrics.get("validation_release_count")),
            "validation_simulated_trajectory_count": number_or_none(
                metrics.get("validation_simulated_trajectory_count")
            ),
        },
        "summary_metric_provenance": relative(path),
    }


def classification_stability(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_contact: dict[str, dict[str, Any]] = {}
    stable = True
    for contact_model in CONTACT_CASES:
        contact_rows = [row for row in rows if row.get("contact_model") == contact_model]
        by_method = {row["transform_method"]: row["classification"] for row in contact_rows}
        missing = [method for method in REQUIRED_TRANSFORMS if method not in by_method]
        classifications = sorted(set(by_method.values()))
        contact_stable = not missing and len(classifications) == 1
        if not contact_stable:
            stable = False
        by_contact[contact_model] = {
            "stable": contact_stable,
            "missing_methods": missing,
            "classifications": by_method,
        }
    return {"stable_across_transforms": stable, "by_contact_model": by_contact}


def required_rows_present(rows: list[dict[str, Any]]) -> bool:
    present = {(row.get("transform_method"), row.get("contact_model")) for row in rows}
    required = {
        (method, contact_model) for method in REQUIRED_TRANSFORMS for contact_model in CONTACT_CASES
    }
    return required.issubset(present)


def classify_runout(signed_error_m: float) -> str:
    if signed_error_m < -RUNOUT_THRESHOLD_M:
        return "under_run"
    if signed_error_m > RUNOUT_THRESHOLD_M:
        return "over_run"
    return "near_observed_runout"


def classify_deposition_overlap(overlap: float | None) -> str:
    if overlap is None:
        return "unknown_deposition_overlap"
    if overlap <= 0.0:
        return "no_deposition_overlap"
    if overlap < 0.25:
        return "low_deposition_overlap"
    if overlap < 0.75:
        return "partial_deposition_overlap"
    return "high_deposition_overlap"


def metrics_file(root: Path, case_name: str) -> Path:
    return root / "validation" / f"validation_tschamut_public_benchmark_{case_name}_metrics.json"


def require_number(metrics: dict[str, Any], key: str, path: Path) -> float:
    value = number_or_none(metrics.get(key))
    if value is None:
        raise SystemExit(f"{relative(path)} is missing numeric metrics.{key}")
    return value


def number_or_none(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Tschamut Registration Sensitivity",
        "",
        "| Field | Value |",
        "| --- | --- |",
        f"| Run subset | `{report['run_subset']}` |",
        f"| Classification stability reported | `{str(report['classification_stability_reported']).lower()}` |",
        f"| Stable across transforms | `{str(report['classification_stable_across_transforms']).lower()}` |",
        f"| Physics selection allowed | `{str(report['physics_selection_allowed']).lower()}` |",
        "",
        "| Transform | Contact model | Classification | Signed runout error (m) | Deposition overlap | Metrics provenance |",
        "| --- | --- | --- | ---: | ---: | --- |",
    ]
    for row in report["classification_sensitivity"]:
        metrics = row["grouped_metrics"]
        overlap = metrics.get("deposition_cloud_overlap_fraction")
        overlap_text = "" if overlap is None else f"{overlap:.3f}"
        lines.append(
            "| "
            f"`{row['transform_method']}` | "
            f"`{row['contact_model']}` | "
            f"`{row['classification']}` | "
            f"{metrics['signed_runout_error_m']:.3f} | "
            f"{overlap_text} | "
            f"`{row['summary_metric_provenance']}` |"
        )
    if report["missing_evidence"]:
        lines.extend(["", "## Missing Evidence", ""])
        lines.extend(f"- {item}" for item in report["missing_evidence"])
    lines.extend(
        [
            "",
            "## Limitations",
            "",
            *[f"- {item}" for item in report["limitations"]],
            "",
        ]
    )
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
