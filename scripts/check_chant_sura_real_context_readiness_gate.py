#!/usr/bin/env python3
"""Report Chant Sura real-context readiness without downloading public data.

The gate compares three things:

- the deterministic public-context acquisition plan from the Chant Sura
  acquisition manifest;
- the local staged core inputs and supporting ignored roots;
- the public-context products that remain intentionally deferred.

The script does not download swisstopo products, run a second-site ensemble, or
turn synthetic core fixtures into public-context evidence.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

try:
    import yaml  # type: ignore
except ImportError as exc:  # pragma: no cover - environment setup.
    raise SystemExit("PyYAML is required; install with `python3 -m pip install PyYAML`") from exc


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "chant_sura_real_context_readiness_gate_v1"
DEFAULT_SITE_CONFIG = ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml"
DEFERRED_PUBLIC_CONTEXT_CATEGORIES = {
    "swissimage_context",
    "swisstlm3d_context",
    "swisstlm3d_metadata",
    "swisssurface3d_context",
    "swisssurface3d_raster_context",
    "swissbuildings3d_context",
}
CORE_INPUT_CATEGORIES = {
    "terrain_crop",
    "terrain_crs_vertical_datum",
    "source_zone_metadata",
    "scenario_table",
    "source_scenario_policy",
}
SUPPORTING_ROOT_CATEGORIES = {
    "processed_input_root",
    "processed_context_root",
    "validation_case_root",
    "hazard_results_root",
}


def _load_preflight_module():
    path = ROOT / "scripts" / "check_second_site_public_geodata_preflight.py"
    spec = importlib.util.spec_from_file_location("chant_sura_real_context_preflight", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load preflight helper from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


PREFLIGHT = _load_preflight_module()


@contextmanager
def _patched_repo_root(repo_root: Path) -> Iterator[None]:
    original_root = PREFLIGHT.ROOT
    PREFLIGHT.ROOT = repo_root
    try:
        yield
    finally:
        PREFLIGHT.ROOT = original_root


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site-config", type=Path, default=DEFAULT_SITE_CONFIG)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    args = parser.parse_args(argv)

    report = build_report(args.site_config, repo_root=args.repo_root)

    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    output = json.dumps(report, indent=2, sort_keys=True) if args.format == "json" else render_text_report(report)
    print(output)
    return 0 if report["real_context_readiness_gate_status"] == "ready_for_real_context_acquisition" else 2


def build_report(site_config: Path | None, *, repo_root: Path | None = None) -> dict[str, Any]:
    repo_root = repo_root or ROOT
    config_path = site_config or DEFAULT_SITE_CONFIG

    with _patched_repo_root(repo_root):
        config = PREFLIGHT.load_site_config(config_path) if config_path.exists() else {}
        candidate_site_id = PREFLIGHT.text_value(config.get("candidate_site_id")) or "unspecified_second_site"
        site_extent = config.get("site_extent") if isinstance(config.get("site_extent"), dict) else {}

        preflight_report = PREFLIGHT.build_report(config_path)
        paths = PREFLIGHT.build_paths(candidate_site_id, config)
        requirements = PREFLIGHT.build_requirements(candidate_site_id, site_extent, paths)
        acquisition_plan = list(preflight_report.get("public_context_acquisition_plan") or [])
        acquisition_manifest = PREFLIGHT.load_site_config(
            Path(preflight_report["acquisition_manifest_path"])
        ) if preflight_report.get("acquisition_manifest_status") == "ready" else {}

        local_core_inputs = build_local_core_inputs(requirements)
        supporting_roots = build_supporting_roots(requirements)
        deferred_public_context_products = [entry for entry in acquisition_plan if entry["category"] in DEFERRED_PUBLIC_CONTEXT_CATEGORIES]
        next_acquisition_decisions = build_next_acquisition_decisions(deferred_public_context_products)

        gate_status = determine_gate_status(
            core_input_status=preflight_report["core_input_status"],
            deferred_public_context_status=preflight_report["deferred_public_context_status"],
            deferred_public_context_products=deferred_public_context_products,
        )

        report = {
            "schema_version": SCHEMA_VERSION,
            "real_context_readiness_gate_status": gate_status,
            "readiness_status": gate_status,
            "candidate_site_id": preflight_report["candidate_site_id"],
            "candidate_site_name": preflight_report["candidate_site_name"],
            "candidate_selection_rationale": preflight_report["candidate_selection_rationale"],
            "site_extent": preflight_report["site_extent_or_placeholder"],
            "acquisition_manifest_status": preflight_report["acquisition_manifest_status"],
            "acquisition_manifest_path": preflight_report["acquisition_manifest_path"],
            "core_input_status": preflight_report["core_input_status"],
            "deferred_public_context_status": preflight_report["deferred_public_context_status"],
            "deterministic_acquisition_plan": acquisition_plan,
            "local_core_inputs": local_core_inputs,
            "supporting_local_roots": supporting_roots,
            "deferred_public_context_products": deferred_public_context_products,
            "next_acquisition_decisions": next_acquisition_decisions,
            "public_context_acquisition_summary": preflight_report["public_context_acquisition_summary"],
            "public_context_boundary_status": preflight_report["public_context_boundary_status"],
            "source_zone_scenario_contract": preflight_report["source_zone_scenario_contract"],
            "synthetic_core_inputs_are_public_context_evidence": False,
            "synthetic_fixture_boundaries": preflight_report["synthetic_fixture_boundaries"],
            "claim_boundaries": preflight_report["claim_boundaries"],
            "operational_claims_allowed": False,
            "scale_up_authorized": False,
            "acquisition_manifest_product_summaries": preflight_report["acquisition_manifest_product_summaries"],
            "local_staged_summary": summarize_local_staging(local_core_inputs, supporting_roots),
            "gate_boundary_summary": build_gate_boundary_summary(
                preflight_report["core_input_status"],
                preflight_report["deferred_public_context_status"],
                deferred_public_context_products,
            ),
            "acquisition_manifest": acquisition_manifest,
        }
        return report


def build_local_core_inputs(requirements: list[dict[str, Any]]) -> list[dict[str, Any]]:
    core_inputs: list[dict[str, Any]] = []
    for requirement in requirements:
        if requirement["category"] not in CORE_INPUT_CATEGORIES:
            continue
        core_inputs.append(
            {
                "category": requirement["category"],
                "kind": requirement["kind"],
                "product": requirement["product"],
                "required": requirement["required"],
                "expected_path": requirement["path_or_pattern"],
                "status": requirement["status"],
                "reusable_from_tschamut": requirement["reusable_from_tschamut"],
                "filesystem_state": describe_path_state(Path(requirement["path_or_pattern"])),
                "synthetic_core_input": True,
                "public_context_evidence": False,
            }
        )
    return core_inputs


def build_supporting_roots(requirements: list[dict[str, Any]]) -> list[dict[str, Any]]:
    roots: list[dict[str, Any]] = []
    for requirement in requirements:
        if requirement["category"] not in SUPPORTING_ROOT_CATEGORIES:
            continue
        path = Path(requirement["path_or_pattern"])
        roots.append(
            {
                "category": requirement["category"],
                "product": requirement["product"],
                "required": requirement["required"],
                "expected_path": requirement["path_or_pattern"],
                "status": requirement["status"],
                "filesystem_state": describe_path_state(path),
            }
        )
    return roots


def build_next_acquisition_decisions(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    decisions: list[dict[str, Any]] = []
    for row in rows:
        decisions.append(
            {
                "category": row["category"],
                "product": row["product"],
                "decision_type": "deferred_public_context_staging",
                "next_acquisition_decision": "acquire_and_stage_public_context_product",
                "expected_staged_path": row["expected_staged_path"],
                "expected_staging_root": row["expected_staging_root"],
                "current_status": row["current_status"],
                "reason": "public context remains intentionally deferred until real products are staged",
                "notes": row["notes"],
            }
        )
    return decisions


def summarize_local_staging(core_inputs: list[dict[str, Any]], supporting_roots: list[dict[str, Any]]) -> dict[str, Any]:
    ready_core_inputs = [entry["category"] for entry in core_inputs if entry["status"] == "ready"]
    ready_supporting_roots = [entry["category"] for entry in supporting_roots if entry["status"] == "ready"]
    deferred_public_context_products = [
        entry["category"]
        for entry in core_inputs
        if entry["category"] in DEFERRED_PUBLIC_CONTEXT_CATEGORIES and entry["status"] == "deferred_public_context"
    ]
    return {
        "ready_core_input_count": len(ready_core_inputs),
        "ready_core_input_categories": ready_core_inputs,
        "ready_supporting_root_count": len(ready_supporting_roots),
        "ready_supporting_root_categories": ready_supporting_roots,
        "deferred_public_context_core_products": deferred_public_context_products,
        "synthetic_core_inputs_are_public_context_evidence": False,
    }


def build_gate_boundary_summary(
    core_input_status: str,
    deferred_public_context_status: str,
    deferred_public_context_products: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "core_inputs_ready": core_input_status == "ready",
        "deferred_public_context_inputs": deferred_public_context_status == "deferred_public_context_inputs",
        "deferred_public_context_product_count": len(deferred_public_context_products),
        "synthetic_core_inputs_are_public_context_evidence": False,
    }


def determine_gate_status(
    *,
    core_input_status: str,
    deferred_public_context_status: str,
    deferred_public_context_products: list[dict[str, Any]],
) -> str:
    if core_input_status != "ready":
        return "blocked_missing_inputs"
    if deferred_public_context_status != "deferred_public_context_inputs":
        return "blocked_missing_inputs"
    if not deferred_public_context_products:
        return "blocked_missing_deferred_public_context"
    return "ready_for_real_context_acquisition"


def describe_path_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "exists": False,
            "kind": "missing",
            "is_empty_directory": False,
            "is_file": False,
            "is_dir": False,
        }
    if path.is_file():
        return {
            "exists": True,
            "kind": "file",
            "is_empty_directory": False,
            "is_file": True,
            "is_dir": False,
        }
    is_empty_directory = not any(path.iterdir())
    return {
        "exists": True,
        "kind": "empty_directory" if is_empty_directory else "nonempty_directory",
        "is_empty_directory": is_empty_directory,
        "is_file": False,
        "is_dir": True,
    }


def render_text_report(report: dict[str, Any]) -> str:
    lines = [
        f"schema_version: {report['schema_version']}",
        f"real_context_readiness_gate_status: {report['real_context_readiness_gate_status']}",
        f"core_input_status: {report['core_input_status']}",
        f"deferred_public_context_status: {report['deferred_public_context_status']}",
        f"candidate_site_id: {report['candidate_site_id']}",
        f"candidate_site_name: {report['candidate_site_name']}",
        f"candidate_selection_rationale: {report['candidate_selection_rationale']}",
        f"acquisition_manifest_status: {report['acquisition_manifest_status']}",
        f"acquisition_manifest_path: {report['acquisition_manifest_path']}",
        "",
        "site_extent:",
    ]
    site_extent = report["site_extent"]
    if isinstance(site_extent, dict):
        for key in ("crs", "xmin", "ymin", "xmax", "ymax"):
            if key in site_extent:
                lines.append(f"  {key}: {site_extent[key]}")
    else:
        lines.append(f"  {site_extent}")

    lines.append("")
    lines.append("local_core_inputs:")
    lines.extend(render_path_status_rows(report.get("local_core_inputs") or []))

    lines.append("")
    lines.append("supporting_local_roots:")
    lines.extend(render_path_status_rows(report.get("supporting_local_roots") or []))

    lines.append("")
    lines.append("deterministic_acquisition_plan:")
    lines.extend(render_plan_rows(report.get("deterministic_acquisition_plan") or []))

    lines.append("")
    lines.append("next_acquisition_decisions:")
    lines.extend(render_decision_rows(report.get("next_acquisition_decisions") or []))

    lines.append("")
    lines.append("deferred_public_context_products:")
    lines.extend(render_plan_rows(report.get("deferred_public_context_products") or []))

    lines.append("")
    lines.append("local_staged_summary:")
    for key, value in (report.get("local_staged_summary") or {}).items():
        lines.append(f"- {key}: {value}")

    lines.append("")
    lines.append("gate_boundary_summary:")
    for key, value in (report.get("gate_boundary_summary") or {}).items():
        lines.append(f"- {key}: {value}")

    lines.append("")
    lines.append("synthetic_core_inputs_are_public_context_evidence: false")
    return "\n".join(lines)


def render_path_status_rows(rows: list[dict[str, Any]]) -> list[str]:
    rendered: list[str] = []
    for row in rows:
        rendered.append(
            f"- {row['category']}: status={row['status']}, expected_path={row['expected_path']}, "
            f"filesystem_state={row['filesystem_state']['kind']}"
        )
    if not rendered:
        rendered.append("- []")
    return rendered


def render_plan_rows(rows: list[dict[str, Any]]) -> list[str]:
    rendered: list[str] = []
    for row in rows:
        rendered.append(
            f"- {row['category']}: product={row['product']}, current_status={row['current_status']}, "
            f"expected_staged_path={row['expected_staged_path']}"
        )
    if not rendered:
        rendered.append("- []")
    return rendered


def render_decision_rows(rows: list[dict[str, Any]]) -> list[str]:
    rendered: list[str] = []
    for row in rows:
        rendered.append(
            f"- {row['category']}: decision_type={row['decision_type']}, "
            f"next_acquisition_decision={row['next_acquisition_decision']}, "
            f"expected_staged_path={row['expected_staged_path']}"
        )
    if not rendered:
        rendered.append("- []")
    return rendered


if __name__ == "__main__":
    raise SystemExit(main())
