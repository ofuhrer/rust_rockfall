#!/usr/bin/env python3
"""Audit Chant Sura model-selection and held-out trajectory split independence.

The helper is read-only. It verifies that model-selection trajectory IDs and
held-out trajectory IDs are disjoint, then reports split counts, roles, and
limitations. It does not calibrate, tune, validate hazard maps, or authorize
physical, annual-frequency, operational, risk, Balfrin, or scale-up claims.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "chant_sura_holdout_split_audit_v1"
DEFAULT_SPLIT_PATH = ROOT / "validation/data/processed/chant_sura_2020/metadata_contact_split.json"
DEFAULT_EVIDENCE_MANIFEST_PATH = ROOT / "validation/data/processed/chant_sura_2020/holdout_validation_evidence_manifest.json"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--split-metadata", type=Path, default=DEFAULT_SPLIT_PATH)
    parser.add_argument("--evidence-manifest", type=Path, default=DEFAULT_EVIDENCE_MANIFEST_PATH)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    args = parser.parse_args(argv)

    report = build_report(split_metadata_path=args.split_metadata, evidence_manifest_path=args.evidence_manifest)
    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text_report(report))
    return 0 if report["audit_status"] == "passed" else 2


def build_report(
    *,
    split_metadata_path: Path = DEFAULT_SPLIT_PATH,
    evidence_manifest_path: Path = DEFAULT_EVIDENCE_MANIFEST_PATH,
) -> dict[str, Any]:
    split = load_json(split_metadata_path)
    evidence_manifest = load_json(evidence_manifest_path) if evidence_manifest_path.exists() else {}
    model_ids = normalized_ids(split.get("model_selection_subset", {}).get("trajectory_ids"))
    heldout_ids = normalized_ids(split.get("held_out_evaluation_subset", {}).get("trajectory_ids"))
    overlap = sorted(set(model_ids).intersection(heldout_ids))
    recorded_overlap = normalized_ids(split.get("overlap"))
    manifest_overlap = normalized_ids(
        evidence_manifest.get("overlap_check", {}).get("shared_trajectory_ids")
        if isinstance(evidence_manifest.get("overlap_check"), dict)
        else []
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "audit_status": "passed" if not overlap else "blocked_overlap_detected",
        "dataset_id": split.get("dataset_id", "unknown"),
        "split_metadata_path": relative(split_metadata_path),
        "evidence_manifest_path": relative(evidence_manifest_path),
        "split_counts": {
            "model_selection_trajectory_count": len(model_ids),
            "held_out_trajectory_count": len(heldout_ids),
            "shared_trajectory_count": len(overlap),
            "recorded_overlap_count": len(recorded_overlap),
        },
        "split_roles": {
            "model_selection_role": split.get("model_selection_subset", {}).get("role", ""),
            "held_out_role": split.get("held_out_evaluation_subset", {}).get("role", ""),
            "split_method": split.get("split_method", ""),
        },
        "model_selection_trajectory_ids": model_ids,
        "held_out_trajectory_ids": heldout_ids,
        "shared_trajectory_ids": overlap,
        "recorded_overlap_trajectory_ids": recorded_overlap,
        "evidence_manifest_shared_trajectory_ids": manifest_overlap,
        "consistency_checks": {
            "recorded_overlap_matches_computed": sorted(recorded_overlap) == overlap,
            "evidence_manifest_overlap_matches_computed": sorted(manifest_overlap) == overlap,
            "no_duplicate_model_selection_ids": len(model_ids) == len(set(model_ids)),
            "no_duplicate_held_out_ids": len(heldout_ids) == len(set(heldout_ids)),
        },
        "limitations": [
            "the split is internal and deterministic, not an external independent validation dataset",
            "segment boundaries remain contact/rebound proxies rather than direct instrumented impacts",
            "the audit protects contact/trajectory evidence only and does not validate Tschamut hazard maps",
            "no calibration, parameter tuning, physical probability, annual frequency, or operational claim is introduced",
        ],
        "claim_boundaries": {
            "calibration_performed": False,
            "parameter_tuning_performed": False,
            "external_validation_claimed": False,
            "physical_probability_claims_allowed": False,
            "annual_frequency_claims_allowed": False,
            "operational_claims_allowed": False,
            "risk_exposure_vulnerability_claims_allowed": False,
            "scale_up_authorized": False,
            "balfrin_required": False,
        },
    }


def normalized_ids(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item)]


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def render_text_report(report: dict[str, Any]) -> str:
    lines = [
        f"schema_version: {report['schema_version']}",
        f"audit_status: {report['audit_status']}",
        f"dataset_id: {report['dataset_id']}",
        "split_counts:",
    ]
    for key, value in report["split_counts"].items():
        lines.append(f"  {key}: {value}")
    lines.append("consistency_checks:")
    for key, value in report["consistency_checks"].items():
        lines.append(f"  {key}: {value}")
    lines.append(f"shared_trajectory_ids: {', '.join(report['shared_trajectory_ids']) or 'none'}")
    lines.append("claim_boundaries:")
    for key, value in report["claim_boundaries"].items():
        lines.append(f"  {key}: {value}")
    lines.append("limitations:")
    lines.extend(f"  - {item}" for item in report["limitations"])
    return "\n".join(lines)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
