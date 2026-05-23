#!/usr/bin/env python3
"""Rank local conditional hazard-layer families by scientific fragility.

The helper is read-only. It reuses the existing validation/calibration evidence
gap report and does not tune parameters, rerun ensembles, or upgrade any
physical, annual-frequency, operational, risk, or scale-up claim.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import assess_validation_calibration_evidence_gaps as evidence_gaps


SCHEMA_VERSION = "local_hazard_layer_fragility_ranking_v1"

FRAGILITY_ORDER = {
    "highest": 1,
    "high": 2,
    "moderate": 3,
    "low": 4,
    "not_inferred": 5,
}

LAYER_TIEBREAKERS = {
    "max_kinetic_energy": 0,
    "max_jump_height": 1,
    "conditional_intensity_exceedance_layers": 2,
    "reach_probability": 3,
    "deposition_density": 4,
}

FOLLOW_UP_BY_LAYER = {
    "max_kinetic_energy": "Measure gate-vs-target extreme-layer sensitivity before treating energy hotspots as stable diagnostics.",
    "max_jump_height": "Measure support/nodata and summary deltas before treating clearance hotspots as stable diagnostics.",
    "conditional_intensity_exceedance_layers": "Audit denominator provenance and threshold sensitivity before using exceedance layers for interpretation.",
    "reach_probability": "Keep denominator provenance explicit before comparing reach footprints.",
    "deposition_density": "Keep trajectory-to-deposition traceability explicit before comparing deposition footprints.",
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    args = parser.parse_args(argv)

    report = build_report()
    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text_report(report))
    return 0


def build_report() -> dict[str, Any]:
    gap_report = evidence_gaps.build_report()
    ranked_layers = rank_layers(gap_report["product_layer_claim_boundaries"])

    return {
        "schema_version": SCHEMA_VERSION,
        "ranking_status": "ready",
        "source_report_schema_version": gap_report["schema_version"],
        "highest_priority_layers": [
            entry["layer_key"]
            for entry in ranked_layers
            if entry["scientific_fragility_level"] in {"highest", "high"}
            and entry["layer_key"] in {"max_kinetic_energy", "max_jump_height"}
        ],
        "ranked_layers": ranked_layers,
        "claim_boundaries": {
            "annual_frequency_claims_allowed": gap_report["annual_frequency_claims_allowed"],
            "operational_claims_allowed": gap_report["operational_claims_allowed"],
            "physical_probability_claims_allowed": False,
            "risk_exposure_vulnerability_claims_allowed": gap_report["risk_exposure_vulnerability_claims_allowed"],
            "scale_up_authorized": gap_report["scale_up_authorized"],
            "balfrin_required": False,
            "tuning_performed": False,
        },
        "next_local_follow_up": "Run scripts/summarize_extreme_layer_sensitivity_smoke.py --format json after it is implemented.",
    }


def rank_layers(layer_boundaries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = [classify_layer(entry) for entry in layer_boundaries]
    rows.sort(
        key=lambda row: (
            FRAGILITY_ORDER.get(row["scientific_fragility_level"], FRAGILITY_ORDER["not_inferred"]),
            LAYER_TIEBREAKERS.get(row["layer_key"], 99),
            row["layer_key"],
        )
    )
    for rank, row in enumerate(rows, start=1):
        row["rank"] = rank
    return rows


def classify_layer(entry: dict[str, Any]) -> dict[str, Any]:
    fragility = entry.get("scientific_fragility", {})
    diagnostic = entry.get("diagnostic_usefulness", {})
    reproducibility = entry.get("reproducibility", {})
    physical = entry.get("physical_credibility", {})
    operational = entry.get("operational_inadmissibility", {})
    layer_key = str(entry["layer_key"])

    return {
        "rank": 0,
        "layer_key": layer_key,
        "layer_label": entry.get("layer_label", layer_key),
        "layer_family": entry.get("layer_family", ""),
        "scientific_fragility_level": fragility.get("level", "not_inferred"),
        "diagnostic_usefulness_status": diagnostic.get("status", "not_inferred"),
        "reproducibility_status": reproducibility.get("status", "not_inferred"),
        "physical_credibility_status": physical.get("status", "not_inferred"),
        "operational_status": operational.get("status", "not_inferred"),
        "reason": fragility.get("summary", ""),
        "current_repo_basis": list(entry.get("current_repo_basis", [])),
        "evidence_classes_needed": [
            item.get("class_name", "") for item in entry.get("evidence_classes_needed", [])
        ],
        "recommended_local_follow_up": FOLLOW_UP_BY_LAYER.get(
            layer_key,
            "Keep the layer inside the existing diagnostic boundary until a focused local audit exists.",
        ),
    }


def render_text_report(report: dict[str, Any]) -> str:
    lines = [
        f"schema_version: {report['schema_version']}",
        f"ranking_status: {report['ranking_status']}",
        "claim_boundaries:",
    ]
    for key, value in report["claim_boundaries"].items():
        lines.append(f"  {key}: {value}")
    lines.append("highest_priority_layers:")
    for layer_key in report["highest_priority_layers"]:
        lines.append(f"  - {layer_key}")
    lines.append("ranked_layers:")
    for row in report["ranked_layers"]:
        lines.append(
            f"  {row['rank']}. {row['layer_key']}: fragility={row['scientific_fragility_level']} "
            f"reproducibility={row['reproducibility_status']} diagnostic={row['diagnostic_usefulness_status']} "
            f"physical={row['physical_credibility_status']} operational={row['operational_status']}"
        )
        lines.append(f"     reason: {row['reason']}")
        lines.append(f"     recommended_local_follow_up: {row['recommended_local_follow_up']}")
    lines.append(f"next_local_follow_up: {report['next_local_follow_up']}")
    return "\n".join(lines)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
