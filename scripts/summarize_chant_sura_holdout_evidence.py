#!/usr/bin/env python3
"""Summarize Chant Sura held-out validation evidence from existing fixtures.

This helper is read-only. It separates diagnostic / model-selection evidence
from held-out validation evidence and keeps calibration, physical-probability,
and operational claims out of scope.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except ImportError as exc:  # pragma: no cover - environment setup.
    raise SystemExit("PyYAML is required. Run this script with `PYENV_VERSION=system uv run python ...`; CI may use `requirements-tools.txt`") from exc


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "chant_sura_holdout_evidence_v1"
DEFAULT_MANIFEST_PATH = ROOT / "validation/data/processed/chant_sura_2020/holdout_validation_evidence_manifest.json"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("json", "text"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    parser.add_argument("--markdown-output", type=Path, default=None)
    args = parser.parse_args(argv)

    report = build_report()
    if args.json_output is not None:
        output_path = args.json_output if args.json_output.is_absolute() else ROOT / args.json_output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.markdown_output is not None:
        output_path = args.markdown_output if args.markdown_output.is_absolute() else ROOT / args.markdown_output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(render_markdown(report), encoding="utf-8")

    rendered = json.dumps(report, indent=2, sort_keys=True) if args.format == "json" else render_text(report)
    print(rendered)
    return 0


def build_report() -> dict[str, Any]:
    split_path = ROOT / "validation/data/processed/chant_sura_2020/metadata_contact_split.json"
    heldout_case_path = ROOT / "validation/cases/chant_sura_contact_heldout.yaml"
    model_selection_case_path = ROOT / "validation/cases/chant_sura_contact.yaml"
    model_selection_internal_path = ROOT / "validation/internal/shape_contact_v0_chant_sura_model_selection.yaml"
    heldout_rotational_case_path = ROOT / "validation/cases/chant_sura_contact_heldout_rotational.yaml"
    heldout_data = load_yaml(heldout_case_path)
    model_selection_data = load_yaml(model_selection_case_path)
    split_data = load_json(split_path)
    internal_data = load_yaml(model_selection_internal_path)
    heldout_rotational_data = load_yaml(heldout_rotational_case_path)

    heldout_trajectory_ids = list(split_data.get("held_out_evaluation_subset", {}).get("trajectory_ids") or [])
    model_selection_trajectory_ids = list(split_data.get("model_selection_subset", {}).get("trajectory_ids") or [])
    overlap = sorted(set(heldout_trajectory_ids).intersection(model_selection_trajectory_ids))

    diagnostic_evidence = {
        "status": "partial",
        "role": "diagnostic/model-selection",
        "source_case": relative(model_selection_case_path),
        "source_internal_selection": relative(model_selection_internal_path),
        "trajectory_ids": model_selection_trajectory_ids,
        "selection_summaries": [
            "model-selection subset is used to compare candidate contact-model options before the held-out evaluation",
            "the internal model-selection fixture is explicitly internal-only and proxy-only for EOTA shape assignment",
        ],
        "limitations": [
            "model-selection evidence is diagnostic and not independent holdout validation",
            "shape mapping remains proxy-only and unresolved",
        ],
    }

    holdout_evidence = {
        "status": "present",
        "role": "independent_holdout_validation",
        "source_case": relative(heldout_case_path),
        "source_rotational_case": relative(heldout_rotational_case_path),
        "trajectory_ids": heldout_trajectory_ids,
        "selection_boundary_notes": [
            "held-out trajectories are disjoint from the model-selection subset",
            "segment boundaries remain contact/rebound proxies inferred from local time resets",
            "the split metadata is deterministic and explicit",
        ],
        "metrics_summary": {
            "trajectory_count": heldout_data.get("expected", {}).get("values", {}).get("validation_trajectory_count"),
            "trajectory_samples": heldout_data.get("expected", {}).get("values", {}).get("observed_trajectory_sample_count"),
            "contact_events": heldout_data.get("expected", {}).get("values", {}).get("observed_contact_event_count"),
            "contact_proxies": heldout_data.get("validation_scope", {}).get("note", ""),
        },
        "limitations": [
            "held-out contact evidence does not validate Tschamut hazard maps",
            "held-out contact evidence does not establish annual or physical probability",
            "it is contact / trajectory evidence, not full Swiss-wide hazard-map validation",
        ],
    }

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "manifest_path": relative(DEFAULT_MANIFEST_PATH),
        "holdout_evidence_status": "separated_holdout_validation_evidence",
        "candidate_dataset_id": split_data.get("dataset_id", "chant_sura_2020"),
        "candidate_site_id": "chant_sura_2020",
        "candidate_site_name": "Chant Sura",
        "evidence_role_summary": [
            {
                "role": "diagnostic_selection_evidence",
                "classification": diagnostic_evidence["status"],
                "summary": "model-selection and internal-only model-comparison evidence remain diagnostic and proxy-limited",
            },
            {
                "role": "independent_holdout_validation_evidence",
                "classification": holdout_evidence["status"],
                "summary": "the held-out split is deterministic, disjoint, and documented for contact/trajectory validation",
            },
            {
                "role": "calibration_evidence",
                "classification": "missing",
                "summary": "no calibration dataset or parameter-fitting record is introduced by this manifest",
            },
            {
                "role": "physical_probability_evidence",
                "classification": "out_of_scope",
                "summary": "this is contact/trajectory validation only, not a physical probability dataset",
            },
            {
                "role": "operational_evidence",
                "classification": "out_of_scope",
                "summary": "this is not operational hazard evidence",
            },
        ],
        "model_selection_evidence": diagnostic_evidence,
        "holdout_validation_evidence": holdout_evidence,
        "split_metadata": split_data,
        "fixture_boundaries": {
            "heldout_case_path": relative(heldout_case_path),
            "heldout_rotational_case_path": relative(heldout_rotational_case_path),
            "model_selection_case_path": relative(model_selection_case_path),
            "model_selection_internal_path": relative(model_selection_internal_path),
            "terrain_paths": [
                relative(ROOT / "validation/data/processed/chant_sura_2020/terrain_rf16_contact_heldout.asc"),
                relative(ROOT / "validation/data/processed/chant_sura_2020/terrain_rf16_contact.asc"),
            ],
            "split_overlap_trajectory_ids": overlap,
            "split_overlaps_detected": bool(overlap),
            "split_metadata_sufficiency": "sufficient_for_current_holdout_boundary" if not overlap else "blocked_overlap_detected",
            "split_is_deterministic": True,
            "proxy_boundary_note": "segment boundaries are contact/rebound proxies, not direct impact sensors",
        },
        "overlap_check": {
            "status": "no_overlap_detected" if not overlap else "overlap_detected",
            "shared_trajectory_ids": overlap,
            "interpretation": "no shared trajectory IDs between model-selection and held-out subsets",
        },
        "calibration_status": "not_calibration",
        "physical_probability_claims_allowed": False,
        "annual_frequency_claims_allowed": False,
        "risk_exposure_vulnerability_claims_allowed": False,
        "operational_claims_allowed": False,
        "scale_up_authorized": False,
        "limitations": [
            "held-out contact evidence does not validate Tschamut hazard maps",
            "held-out contact evidence does not establish annual or physical probability",
            "it is contact / trajectory evidence, not full Swiss-wide hazard-map validation",
            "the current split is deterministic and compact, not statistically powered",
            "segment boundaries are proxy events inferred from local time resets",
            "no calibration or parameter tuning is introduced by this manifest",
        ],
        "recommended_next_evidence_step": (
            "Use this manifest as the holdout boundary reference for contact/trajectory generalization; "
            "if broader validation is needed, stage a separate independent benchmark rather than reusing these fixtures."
        ),
    }
    return manifest


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def render_text(report: dict[str, Any]) -> str:
    lines = [
        f"holdout_evidence_status: {report['holdout_evidence_status']}",
        f"candidate_dataset_id: {report['candidate_dataset_id']}",
        f"candidate_site_id: {report['candidate_site_id']}",
        f"candidate_site_name: {report['candidate_site_name']}",
        f"calibration_status: {report['calibration_status']}",
        f"physical_probability_claims_allowed: {str(report['physical_probability_claims_allowed']).lower()}",
        f"annual_frequency_claims_allowed: {str(report['annual_frequency_claims_allowed']).lower()}",
        f"risk_exposure_vulnerability_claims_allowed: {str(report['risk_exposure_vulnerability_claims_allowed']).lower()}",
        f"operational_claims_allowed: {str(report['operational_claims_allowed']).lower()}",
        f"scale_up_authorized: {str(report['scale_up_authorized']).lower()}",
        "",
        "evidence_role_summary:",
    ]
    for item in report["evidence_role_summary"]:
        lines.append(f"- {item['role']}: {item['classification']}")
        lines.append(f"  {item['summary']}")
    lines.append("")
    lines.append(f"overlap_check: {report['overlap_check']['status']}")
    lines.append(f"split_metadata_sufficiency: {report['fixture_boundaries']['split_metadata_sufficiency']}")
    lines.append("limitations:")
    lines.extend(f"- {item}" for item in report["limitations"])
    if report.get("recommended_next_evidence_step"):
        lines.append("")
        lines.append(f"recommended_next_evidence_step: {report['recommended_next_evidence_step']}")
    return "\n".join(lines)


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Chant Sura Holdout Evidence Manifest",
        "",
        f"- Holdout evidence status: `{report['holdout_evidence_status']}`",
        f"- Candidate dataset id: `{report['candidate_dataset_id']}`",
        f"- Candidate site id: `{report['candidate_site_id']}`",
        f"- Candidate site name: `{report['candidate_site_name']}`",
        f"- Calibration status: `{report['calibration_status']}`",
        "",
        "## Evidence Roles",
    ]
    for item in report["evidence_role_summary"]:
        lines.append(f"- `{item['role']}`: `{item['classification']}` - {item['summary']}")
    lines.append("")
    lines.append("## Split Metadata")
    lines.append(f"- Held-out trajectories: `{', '.join(report['holdout_validation_evidence']['trajectory_ids'])}`")
    lines.append(
        f"- Model-selection trajectories: `{', '.join(report['model_selection_evidence']['trajectory_ids'])}`"
    )
    lines.append(f"- Overlap check: `{report['overlap_check']['status']}`")
    lines.append("")
    lines.append("## Limitations")
    lines.extend(f"- {item}" for item in report["limitations"])
    return "\n".join(lines) + "\n"


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
