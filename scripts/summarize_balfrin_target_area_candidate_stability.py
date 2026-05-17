#!/usr/bin/env python3
"""Summarize the deterministic release-zone candidate stability audit for Tschamut.

This helper stays at the dry-run boundary. It reads the frozen target-area
Balfrin demonstration contract, reuses the committed terrain-candidate helper
for the Tschamut pilot inputs, and reports the stable versus heuristic-sensitive
candidate regions explicitly. When an output root is requested, it can also
emit the GIS-readable candidate mask/polygon bundle supported by the existing
helper. It does not validate a release zone, tune thresholds, or authorize an
operational claim.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from time import perf_counter
from pathlib import Path
from typing import Any, Callable

try:
    import yaml  # type: ignore
except ImportError as exc:  # pragma: no cover - environment setup.
    raise SystemExit("PyYAML is required; install with `python3 -m pip install PyYAML`") from exc


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "balfrin_target_area_candidate_stability_v1"
DEFAULT_CONTRACT = ROOT / "validation/pilot_runs/tschamut_public_balfrin_target_area_demo_v1.yaml"


def _load_candidate_module():
    path = ROOT / "scripts" / "plan_terrain_release_zone_candidates.py"
    spec = importlib.util.spec_from_file_location("balfrin_target_area_candidate_stability_candidates", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load candidate helper from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


CANDIDATE_PLANNER = _load_candidate_module()


class TargetAreaCandidateStabilityError(ValueError):
    """User-facing target-area candidate stability error."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--output-root", type=Path, default=None)
    parser.add_argument("--output-mode", choices=("mask", "polygon", "both"), default="both")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    args = parser.parse_args(argv)

    try:
        report = build_report(
            contract_path=args.contract,
            output_root=args.output_root,
            output_mode=args.output_mode,
        )
    except TargetAreaCandidateStabilityError as exc:
        print(f"balfrin target-area candidate stability error: {exc}", file=sys.stderr)
        return 2

    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    output = json.dumps(report, indent=2, sort_keys=True) if args.format == "json" else render_text_report(report)
    print(output)
    return 0 if report["candidate_metrics_status"] == "ready" else 2


def build_report(
    *,
    contract_path: Path = DEFAULT_CONTRACT,
    repo_root: Path = ROOT,
    output_root: Path | None = None,
    output_mode: str = "both",
    timer: Callable[[], float] | None = None,
) -> dict[str, Any]:
    timer = timer or perf_counter
    if not contract_path.exists():
        raise TargetAreaCandidateStabilityError(f"missing target-area contract: {contract_path}")

    contract = load_yaml(contract_path)
    target_area = require_mapping(contract.get("target_area"), "target_area")
    input_freeze = require_mapping(contract.get("input_freeze"), "input_freeze")
    claim_boundary = require_mapping(contract.get("claim_boundary"), "claim_boundary")

    target_area_id = text_value(target_area.get("target_area_id"), "target_area.target_area_id")
    source_zone_metadata_path = resolve_repo_path(input_freeze.get("source_zone_metadata_path"), base_root=repo_root)
    scenario_table_path = resolve_repo_path(input_freeze.get("scenario_table_path"), base_root=repo_root)
    source_scenario_policy_path = resolve_repo_path(input_freeze.get("source_scenario_policy_path"), base_root=repo_root)
    geodata_manifest_path = resolve_repo_path(target_area.get("geodata_manifest_path"), base_root=repo_root)
    terrain_crop_path = source_zone_metadata_path.parent / "tschamut_public_swissalti3d_crop.asc"
    terrain_metadata_path = source_zone_metadata_path.parent / "tschamut_public_swissalti3d_metadata.yaml"
    sweep_start = timer()

    required_inputs = [
        contract_path,
        geodata_manifest_path,
        source_zone_metadata_path,
        terrain_crop_path,
        terrain_metadata_path,
        scenario_table_path,
        source_scenario_policy_path,
    ]
    missing = [display_path(path) for path in required_inputs if not path.exists()]
    if missing:
        return blocked_report(
            contract_path=contract_path,
            target_area=target_area,
            input_freeze=input_freeze,
            claim_boundary=claim_boundary,
            missing_inputs=missing,
        )

    candidate_report = CANDIDATE_PLANNER.build_report(
        repo_root=repo_root,
        terrain_crop_path=terrain_crop_path,
        terrain_metadata_path=terrain_metadata_path,
        source_zone_metadata_path=source_zone_metadata_path,
        output_root=output_root,
        output_mode=output_mode,
    )
    sweep_runtime_seconds = timer() - sweep_start
    if candidate_report["candidate_site_id"] != target_area_id:
        raise TargetAreaCandidateStabilityError(
            "frozen target-area contract and candidate helper disagree on target-area id"
        )

    candidate_sensitivity_report = candidate_report["candidate_sensitivity_report"]
    stable_region = candidate_sensitivity_report["stable_candidate_region"]
    unstable_region = candidate_sensitivity_report["unstable_candidate_region"]
    sweep_measurements = candidate_sweep_measurements(output_root, candidate_report, sweep_runtime_seconds)
    multi_zone_readiness = multi_zone_stress_test_readiness(candidate_report, sweep_measurements)

    report = {
        "schema_version": SCHEMA_VERSION,
        "candidate_metrics_status": candidate_report["candidate_metrics_status"],
        "candidate_release_zone_set_status": candidate_report["candidate_release_zone_set_status"],
        "candidate_release_zone_interpretation": candidate_report["candidate_release_zone_interpretation"],
        "contract_path": display_path(contract_path),
        "contract_status": text_value(contract.get("contract_status"), "contract_status"),
        "target_area": {
            "target_area_id": target_area_id,
            "target_area_name": text_value(target_area.get("target_area_name"), "target_area.target_area_name"),
            "target_area_label": text_value(target_area.get("target_area_label"), "target_area.target_area_label"),
            "site_extent": target_area.get("site_extent", {}),
            "geodata_manifest_path": display_path(geodata_manifest_path),
        },
        "frozen_input_freeze": {
            "target_gate_reproduction_record_path": text_value(
                input_freeze.get("target_gate_reproduction_record_path"),
                "input_freeze.target_gate_reproduction_record_path",
            ),
            "source_zone_metadata_path": display_path(source_zone_metadata_path),
            "release_points_csv": text_value(input_freeze.get("release_points_csv"), "input_freeze.release_points_csv"),
            "deposition_points_csv": text_value(
                input_freeze.get("deposition_points_csv"), "input_freeze.deposition_points_csv"
            ),
            "scenario_table_path": display_path(scenario_table_path),
            "source_scenario_policy_path": display_path(source_scenario_policy_path),
            "scenario_family_basis": text_value(input_freeze.get("scenario_family_basis"), "input_freeze.scenario_family_basis"),
            "scenario_probability_semantics": text_value(
                input_freeze.get("scenario_probability_semantics"), "input_freeze.scenario_probability_semantics"
            ),
        },
        "candidate_summary": candidate_report["candidate_summary"],
        "candidate_stability_summary": {
            "stability_status": candidate_sensitivity_report["sensitivity_status"],
            "sensitivity_scope": candidate_sensitivity_report["sensitivity_scope"],
            "variant_count": candidate_sensitivity_report["variant_count"],
            "baseline_variant_id": candidate_sensitivity_report["baseline_variant_id"],
            "candidate_count_range": candidate_sensitivity_report["candidate_count_range"],
            "candidate_area_range_m2": candidate_sensitivity_report["candidate_area_range_m2"],
            "stable_candidate_region": stable_region,
            "heuristic_sensitive_candidate_region": unstable_region,
            "pairwise_overlap_summary": candidate_sensitivity_report["pairwise_overlap_summary"],
        },
        "candidate_sweep_summary": {
            "sweep_status": candidate_report["candidate_metrics_status"],
            "sweep_mode": "real_terrain_candidate_sweep",
            "candidate_count": candidate_report["candidate_summary"].get("candidate_cell_count", 0),
            "candidate_area_m2": candidate_report["candidate_summary"].get("candidate_area_m2", 0.0),
            "candidate_count_range": candidate_sensitivity_report["candidate_count_range"],
            "candidate_area_range_m2": candidate_sensitivity_report["candidate_area_range_m2"],
            "candidate_component_area_distribution_m2": candidate_report["candidate_release_zone_products"].get(
                "component_area_distribution_m2",
                {"min": None, "max": None, "mean": None, "median": None, "p95": None},
            ),
            "slope_thresholds_deg": {
                "minimum": candidate_report["screening_criteria"].get("candidate_slope_min_deg"),
                "maximum": candidate_report["screening_criteria"].get("candidate_slope_max_deg"),
            },
            "topography_thresholds": {
                "cell_area_m2": candidate_report["terrain_summary"].get("cell_area_m2"),
                "resolution_m": candidate_report["terrain_summary"].get("resolution_m"),
                "elevation_min_m": candidate_report["terrain_summary"].get("elevation_min_m"),
                "elevation_max_m": candidate_report["terrain_summary"].get("elevation_max_m"),
                "valid_area_fraction": candidate_report["terrain_summary"].get("valid_cell_count", 0)
                / candidate_report["terrain_summary"].get("cell_count", 1),
                "extent_lv95_m": candidate_report["terrain_summary"].get("extent_lv95_m", {}),
            },
            "multi_zone_stress_test_readiness": multi_zone_readiness,
            "sweep_measurements": sweep_measurements,
        },
        "candidate_release_zone_products": candidate_release_zone_products_summary(candidate_report),
        "candidate_footprint_comparison": candidate_report["candidate_footprint_comparison"],
        "claim_boundaries": claim_boundary,
        "candidate_claim_boundaries": candidate_sensitivity_report["claim_boundaries"],
        "blocked_reason": candidate_report["blocked_reason"] or "none",
        "scale_up_authorized": False,
        "operational_claims_allowed": False,
        "gis_readable_candidate_outputs_supported": True,
        "gis_readable_candidate_outputs_emitted": bool(output_root is not None),
    }
    return report


def candidate_release_zone_products_summary(candidate_report: dict[str, Any]) -> dict[str, Any]:
    products = candidate_report["candidate_release_zone_products"]
    summary = {
        "schema_version": products.get("schema_version", "terrain_release_zone_candidate_products_v1"),
        "output_status": products.get("output_status", "not_emitted"),
        "output_mode": products.get("output_mode", "not_emitted"),
        "candidate_site_id": products.get("candidate_site_id"),
        "candidate_site_name": products.get("candidate_site_name"),
        "source_zone_id": products.get("source_zone_id"),
        "candidate_release_zone_set_status": products.get("candidate_release_zone_set_status", "not_emitted"),
        "component_count": products.get("component_count", 0),
        "candidate_cell_count": products.get("candidate_cell_count", 0),
        "candidate_excludes_frozen_footprint": products.get("candidate_excludes_frozen_footprint", True),
        "component_area_distribution_m2": products.get(
            "component_area_distribution_m2", {"min": None, "max": None, "mean": None, "median": None, "p95": None}
        ),
        "manifest_path": products.get("manifest_path"),
    }
    if "outputs" in products:
        summary["outputs"] = products["outputs"]
    return summary


def candidate_sweep_measurements(
    output_root: Path | None,
    candidate_report: dict[str, Any],
    sweep_runtime_seconds: float,
) -> dict[str, Any]:
    if output_root is None or candidate_report["candidate_release_zone_products"].get("output_status") != "emitted":
        return {
            "runtime_seconds": float(sweep_runtime_seconds),
            "output_root": None,
            "output_file_count": 0,
            "output_total_bytes": 0,
            "output_paths": {},
        }

    output_root = Path(output_root)
    output_files = [path for path in output_root.rglob("*") if path.is_file()]
    return {
        "runtime_seconds": float(sweep_runtime_seconds),
        "output_root": display_path(output_root),
        "output_file_count": len(output_files),
        "output_total_bytes": sum(path.stat().st_size for path in output_files),
        "output_paths": dict(candidate_report["candidate_release_zone_products"].get("outputs") or {}),
    }


def multi_zone_stress_test_readiness(
    candidate_report: dict[str, Any],
    sweep_measurements: dict[str, Any],
) -> dict[str, Any]:
    if candidate_report["candidate_metrics_status"] != "ready":
        return {
            "status": "blocked_missing_inputs",
            "summary": "candidate sweep inputs are missing",
        }
    if candidate_report["candidate_release_zone_products"].get("output_status") != "emitted":
        return {
            "status": "not_ready",
            "summary": "candidate masks or polygons were not emitted to a scratch or ignored root",
        }
    if candidate_report["candidate_release_zone_products"].get("component_count", 0) < 2:
        return {
            "status": "not_ready",
            "summary": "candidate sweep produced fewer than two polygon components",
        }
    if candidate_report["candidate_sensitivity_report"].get("sensitivity_status") != "ready":
        return {
            "status": "not_ready",
            "summary": "candidate stability characterization is not ready",
        }
    if sweep_measurements.get("output_file_count", 0) < 2:
        return {
            "status": "not_ready",
            "summary": "candidate sweep did not materialize enough scratch-root outputs for a multi-zone handoff",
        }
    return {
        "status": "ready",
        "summary": "deterministic real-terrain candidate sweep is ready for multi-zone scenario-generation stress tests",
    }


def blocked_report(
    *,
    contract_path: Path,
    target_area: dict[str, Any],
    input_freeze: dict[str, Any],
    claim_boundary: dict[str, Any],
    missing_inputs: list[str],
) -> dict[str, Any]:
    sweep_measurements = {
        "runtime_seconds": 0.0,
        "output_root": None,
        "output_file_count": 0,
        "output_total_bytes": 0,
        "output_paths": {},
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "candidate_metrics_status": "blocked_missing_inputs",
        "candidate_release_zone_set_status": "not_emitted",
        "candidate_release_zone_interpretation": "not_claimed",
        "contract_path": display_path(contract_path),
        "contract_status": "blocked_missing_inputs",
        "target_area": {
            "target_area_id": target_area.get("target_area_id"),
            "target_area_name": target_area.get("target_area_name"),
            "target_area_label": target_area.get("target_area_label"),
            "site_extent": target_area.get("site_extent", {}),
            "geodata_manifest_path": target_area.get("geodata_manifest_path"),
        },
        "frozen_input_freeze": {
            "target_gate_reproduction_record_path": input_freeze.get("target_gate_reproduction_record_path"),
            "source_zone_metadata_path": input_freeze.get("source_zone_metadata_path"),
            "release_points_csv": input_freeze.get("release_points_csv"),
            "deposition_points_csv": input_freeze.get("deposition_points_csv"),
            "scenario_table_path": input_freeze.get("scenario_table_path"),
            "source_scenario_policy_path": input_freeze.get("source_scenario_policy_path"),
            "scenario_family_basis": input_freeze.get("scenario_family_basis"),
            "scenario_probability_semantics": input_freeze.get("scenario_probability_semantics"),
        },
        "candidate_summary": {},
        "candidate_stability_summary": {},
        "candidate_sweep_summary": {
            "sweep_status": "blocked_missing_inputs",
            "sweep_mode": "real_terrain_candidate_sweep",
            "candidate_count": 0,
            "candidate_area_m2": 0.0,
            "candidate_count_range": {"min": None, "max": None},
            "candidate_area_range_m2": {"min": None, "max": None},
            "candidate_component_area_distribution_m2": {"min": None, "max": None, "mean": None, "median": None, "p95": None},
            "slope_thresholds_deg": {"minimum": None, "maximum": None},
            "topography_thresholds": {
                "cell_area_m2": None,
                "resolution_m": None,
                "elevation_min_m": None,
                "elevation_max_m": None,
                "valid_area_fraction": None,
                "extent_lv95_m": {},
            },
            "multi_zone_stress_test_readiness": {
                "status": "blocked_missing_inputs",
                "summary": "required inputs are missing",
            },
            "sweep_measurements": sweep_measurements,
        },
        "candidate_release_zone_products": {
            "schema_version": "terrain_release_zone_candidate_products_v1",
            "output_status": "not_emitted",
            "output_mode": "not_emitted",
            "candidate_site_id": target_area.get("target_area_id"),
            "candidate_site_name": target_area.get("target_area_name"),
            "source_zone_id": None,
            "candidate_release_zone_set_status": "not_emitted",
            "component_count": 0,
            "candidate_cell_count": 0,
            "candidate_excludes_frozen_footprint": True,
            "manifest_path": None,
            "outputs": {},
        },
        "candidate_footprint_comparison": {},
        "claim_boundaries": claim_boundary,
        "candidate_claim_boundaries": {},
        "blocked_reason": "missing required inputs: " + ", ".join(missing_inputs),
        "scale_up_authorized": False,
        "operational_claims_allowed": False,
        "gis_readable_candidate_outputs_supported": True,
        "gis_readable_candidate_outputs_emitted": False,
        "blocked_missing_inputs": missing_inputs,
    }


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def require_mapping(value: Any, context: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TargetAreaCandidateStabilityError(f"{context} must be a YAML mapping")
    return value


def resolve_repo_path(value: Any, *, base_root: Path = ROOT) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise TargetAreaCandidateStabilityError("missing required repository path value")
    path = Path(value)
    return path if path.is_absolute() else (base_root / path)


def text_value(value: Any, context: str) -> str:
    if value in (None, ""):
        raise TargetAreaCandidateStabilityError(f"{context} is missing")
    return str(value).strip()


def display_path(path: Path | str) -> str:
    path = Path(path)
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def render_text_report(report: dict[str, Any]) -> str:
    lines = [
        "Balfrin Target-Area Candidate Stability Summary",
        "",
        f"- Contract status: `{report['contract_status']}`",
        f"- Candidate metrics status: `{report['candidate_metrics_status']}`",
        f"- Candidate release-zone interpretation: `{report['candidate_release_zone_interpretation']}`",
        f"- Candidate release-zone output status: `{report['candidate_release_zone_products']['output_status']}`",
        f"- Candidate release-zone output mode: `{report['candidate_release_zone_products']['output_mode']}`",
        f"- Stable region class: `{report['candidate_stability_summary'].get('stable_candidate_region', {}).get('region_class', 'unknown')}`",
        f"- Heuristic-sensitive region class: `{report['candidate_stability_summary'].get('heuristic_sensitive_candidate_region', {}).get('region_class', 'unknown')}`",
        "",
        "## Target Area",
        "",
        f"- Target area id: `{report['target_area']['target_area_id']}`",
        f"- Target area name: `{report['target_area']['target_area_name']}`",
        f"- Target area label: `{report['target_area']['target_area_label']}`",
        f"- Geodata manifest: `{report['target_area']['geodata_manifest_path']}`",
        "",
        "## Frozen Inputs",
        "",
        f"- Source-zone metadata: `{report['frozen_input_freeze']['source_zone_metadata_path']}`",
        f"- Scenario table: `{report['frozen_input_freeze']['scenario_table_path']}`",
        f"- Source-scenario policy: `{report['frozen_input_freeze']['source_scenario_policy_path']}`",
        "",
        "## Stability Summary",
        "",
        f"- Variant count: `{report['candidate_stability_summary'].get('variant_count', 'n/a')}`",
        f"- Baseline variant: `{report['candidate_stability_summary'].get('baseline_variant_id', 'n/a')}`",
        f"- Candidate count range: `{report['candidate_stability_summary'].get('candidate_count_range', {})}`",
        f"- Candidate area range m2: `{report['candidate_stability_summary'].get('candidate_area_range_m2', {})}`",
        "",
        "## Sweep Measurements",
        "",
        f"- Sweep status: `{report['candidate_sweep_summary'].get('sweep_status', 'n/a')}`",
        f"- Sweep runtime seconds: `{report['candidate_sweep_summary'].get('sweep_measurements', {}).get('runtime_seconds', 'n/a')}`",
        f"- Output file count: `{report['candidate_sweep_summary'].get('sweep_measurements', {}).get('output_file_count', 'n/a')}`",
        f"- Output total bytes: `{report['candidate_sweep_summary'].get('sweep_measurements', {}).get('output_total_bytes', 'n/a')}`",
        f"- Multi-zone stress-test readiness: `{report['candidate_sweep_summary'].get('multi_zone_stress_test_readiness', {}).get('status', 'n/a')}`",
        "",
        "## Candidate Outputs",
        "",
        f"- Manifest: `{report['candidate_release_zone_products']['manifest_path']}`",
    ]
    outputs = report["candidate_release_zone_products"].get("outputs") or {}
    for key in ("polygon", "mask", "manifest"):
        if key in outputs:
            lines.append(f"- {key}: `{outputs[key]}`")
    lines.extend(
        [
            "",
            "## Claim Boundaries",
            "",
            f"- Scale-up authorized: `{report['scale_up_authorized']}`",
            f"- Operational claims allowed: `{report['operational_claims_allowed']}`",
            f"- GIS-readable candidate outputs supported: `{report['gis_readable_candidate_outputs_supported']}`",
            f"- GIS-readable candidate outputs emitted: `{report['gis_readable_candidate_outputs_emitted']}`",
        ]
    )
    if report.get("blocked_reason") and report["blocked_reason"] != "none":
        lines.extend(["", f"- Blocked reason: `{report['blocked_reason']}`"])
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
