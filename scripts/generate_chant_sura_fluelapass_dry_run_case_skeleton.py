#!/usr/bin/env python3
"""Generate a dry-run Chant Sura / Flüelapass case skeleton.

This helper is intentionally narrow:

- it only writes the skeleton case YAML into ``/tmp`` or an ignored
  validation/private output root;
- it validates that the second-site preflight remains at the
  ``deferred_public_context_inputs`` boundary;
- it records the terrain, source-zone, scenario, and policy references that
  would anchor a later real second-site case;
- it keeps the public-context inputs as explicit deferred placeholders and
  does not authorize any ensemble execution.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except ImportError as exc:  # pragma: no cover - environment setup.
    raise SystemExit("PyYAML is required. Run this script with `PYENV_VERSION=system uv run python ...`; CI may use `requirements-tools.txt`") from exc


ROOT = Path(__file__).resolve().parents[1]
PREFLIGHT_SCRIPT = ROOT / "scripts" / "check_second_site_public_geodata_preflight.py"
DEFAULT_SITE_CONFIG = ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml"
DEFAULT_OUTPUT_ROOT = Path("/tmp/tb062_chant_sura_fluelapass_case_skeleton")
SCHEMA_VERSION = "chant_sura_fluelapass_dry_run_case_skeleton_v1"
CASE_FILENAME = "chant_sura_fluelapass_dry_run_case_skeleton.yaml"
ALLOWED_IGNORED_ROOT = ROOT / "validation/private/chant_sura_fluelapass_portability_example_v1"
TMP_ROOTS = (Path("/tmp"), Path("/private/tmp"))
DEFERRED_PUBLIC_CONTEXT_CATEGORIES = [
    "swissimage_context",
    "swisstlm3d_context",
    "swisstlm3d_metadata",
    "swisssurface3d_context",
    "swisssurface3d_raster_context",
    "swissbuildings3d_context",
]


def _load_preflight_module():
    spec = importlib.util.spec_from_file_location("chant_sura_preflight_for_dry_run_case_skeleton", PREFLIGHT_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load preflight helper from {PREFLIGHT_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PREFLIGHT = _load_preflight_module()


class CaseSkeletonError(ValueError):
    """User-facing dry-run case skeleton error."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site-config", type=Path, default=DEFAULT_SITE_CONFIG)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    args = parser.parse_args(argv)

    try:
        report = build_report(args.site_config, args.output_root)
    except CaseSkeletonError as exc:
        report = {
            "schema_version": SCHEMA_VERSION,
            "case_skeleton_status": "blocked_missing_inputs",
            "reference_validation_status": "blocked_missing_inputs",
            "ensemble_execution_status": "blocked_template_only",
            "blocked_reason": str(exc),
            "generated_case_path": "",
            "generated_case_paths": [],
            "write_status": "blocked",
            "scale_up_authorized": False,
            "operational_claims_allowed": False,
        }

    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    output = json.dumps(report, indent=2, sort_keys=True) if args.format == "json" else render_text_report(report)
    print(output)
    return 0 if report["case_skeleton_status"] == "ready" else 2


def build_report(site_config: Path, output_root: Path) -> dict[str, Any]:
    if not site_config.exists():
        raise CaseSkeletonError(f"missing site config: {site_config}")

    config = PREFLIGHT.load_site_config(site_config)
    candidate_site_id = text_value(config.get("candidate_site_id"))
    if not candidate_site_id:
        raise CaseSkeletonError(f"candidate_site_id is missing from {site_config}")

    preflight_report = PREFLIGHT.build_report(site_config)
    if preflight_report["portability_preflight_status"] != "deferred_public_context_inputs":
        raise CaseSkeletonError(
            "Chant Sura dry-run skeleton only applies while the preflight remains "
            f"deferred_public_context_inputs; got {preflight_report['portability_preflight_status']}"
        )
    if preflight_report["core_input_status"] != "ready":
        raise CaseSkeletonError(
            "required terrain, source-zone, scenario, policy, or ignored-root inputs are not ready"
        )

    output_root = resolve_output_root(output_root)
    if not is_allowed_output_root(output_root):
        raise CaseSkeletonError(
            f"output-root must stay under /tmp or {ALLOWED_IGNORED_ROOT}: {output_root}"
        )

    paths = PREFLIGHT.build_paths(candidate_site_id, config)
    case_path = output_root / CASE_FILENAME
    case = build_case_skeleton(
        preflight_report=preflight_report,
        paths=paths,
        output_root=output_root,
        case_path=case_path,
    )

    case_path.parent.mkdir(parents=True, exist_ok=True)
    case_path.write_text(yaml.safe_dump(case, sort_keys=False), encoding="utf-8")

    return {
        "schema_version": SCHEMA_VERSION,
        "case_skeleton_status": "ready",
        "reference_validation_status": "ready",
        "ensemble_execution_status": "blocked_template_only",
        "blocked_reason": "deferred_public_context_inputs",
        "candidate_site_id": candidate_site_id,
        "candidate_site_name": preflight_report["candidate_site_name"],
        "preflight_status": preflight_report["portability_preflight_status"],
        "generated_case_path": str(case_path),
        "generated_case_paths": [str(case_path)],
        "output_root": str(output_root),
        "output_path_strategy": "tmp_or_ignored_only",
        "write_status": "written",
        "site_extent": preflight_report["site_extent_or_placeholder"],
        "source_zone_scenario_contract": preflight_report["source_zone_scenario_contract"],
        "terrain_source_zone_scenario_policy_refs": {
            "terrain_crop": display_path(paths["terrain_crop"]),
            "terrain_metadata": display_path(paths["terrain_metadata"]),
            "source_zone_metadata": display_path(paths["source_zone_metadata"]),
            "scenario_table": display_path(paths["scenario_table"]),
            "source_scenario_policy": display_path(paths["source_scenario_policy"]),
        },
        "deferred_public_context_categories": list(preflight_report["deferred_public_context_categories"]),
        "deferred_public_context_paths_or_patterns": list(preflight_report["deferred_public_context_paths_or_patterns"]),
        "deferred_public_context_placeholders": case["deferred_public_context_placeholders"],
        "claim_boundaries": preflight_report["claim_boundaries"],
        "scale_up_authorized": False,
        "operational_claims_allowed": False,
    }


def build_case_skeleton(
    *,
    preflight_report: dict[str, Any],
    paths: dict[str, Path],
    output_root: Path,
    case_path: Path,
) -> dict[str, Any]:
    placeholder_paths = {
        "swissimage_context": display_path(paths["swissimage_context"]),
        "swisstlm3d_context": display_path(paths["swisstlm3d_context"]),
        "swisstlm3d_metadata": display_path(paths["swisstlm3d_metadata"]),
        "swisssurface3d_context": display_path(paths["swisssurface3d_context"]),
        "swisssurface3d_raster_context": display_path(paths["swisssurface3d_raster_context"]),
        "swissbuildings3d_context": display_path(paths["swissbuildings3d_context"]),
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "case_id": SCHEMA_VERSION,
        "title": "Chant Sura / Flüelapass dry-run case skeleton",
        "mode": "dry_run",
        "candidate_site_id": preflight_report["candidate_site_id"],
        "candidate_site_name": preflight_report["candidate_site_name"],
        "site_extent": preflight_report["site_extent_or_placeholder"],
        "source_zone_scenario_contract": preflight_report["source_zone_scenario_contract"],
        "generation_boundary": {
            "preflight_status": preflight_report["portability_preflight_status"],
            "reference_validation_status": "ready",
            "ensemble_execution_status": "blocked_template_only",
            "blocked_reason": "deferred_public_context_inputs",
            "write_policy": "tmp_or_ignored_only",
            "output_root": display_path(output_root),
        },
        "references": {
            "terrain": {
                "terrain_crop": display_path(paths["terrain_crop"]),
                "terrain_metadata": display_path(paths["terrain_metadata"]),
            },
            "source_zone": {
                "source_zone_metadata": display_path(paths["source_zone_metadata"]),
            },
            "scenario": {
                "scenario_table": display_path(paths["scenario_table"]),
            },
            "policy": {
                "source_scenario_policy": display_path(paths["source_scenario_policy"]),
            },
        },
        "deferred_public_context_placeholders": {
            category: {
                "expected_staged_path": placeholder_paths[category],
                "status": "deferred_public_context_inputs",
            }
            for category in DEFERRED_PUBLIC_CONTEXT_CATEGORIES
        },
        "outputs": {
            "case_yaml_path": display_path(case_path),
        },
        "claim_boundaries": preflight_report["claim_boundaries"],
        "notes": [
            "Dry-run skeleton only; no ensemble execution, hazard build, or staging download is authorized.",
            "Public context stays deferred until real staged inputs exist.",
            "Terrain, source-zone, scenario, and policy references are recorded for later handoff.",
        ],
    }


def resolve_output_root(output_root: Path) -> Path:
    return output_root if output_root.is_absolute() else (ROOT / output_root)


def is_allowed_output_root(
    output_root: Path,
    *,
    repo_root: Path = ROOT,
    allowed_ignored_root: Path = ALLOWED_IGNORED_ROOT,
    scratch_roots: tuple[Path, ...] = TMP_ROOTS,
) -> bool:
    resolved = output_root.resolve()
    resolved_repo_root = repo_root.resolve()
    resolved_allowed_ignored_root = allowed_ignored_root.resolve()
    if resolved.is_relative_to(resolved_allowed_ignored_root):
        return True
    if resolved.is_relative_to(resolved_repo_root):
        return False
    return any(resolved.is_relative_to(root.resolve()) for root in scratch_roots)


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def text_value(value: Any) -> str:
    return str(value).strip() if value not in (None, "") else ""


def render_text_report(report: dict[str, Any]) -> str:
    lines = [
        f"schema_version: {report['schema_version']}",
        f"case_skeleton_status: {report.get('case_skeleton_status', 'blocked_missing_inputs')}",
        f"reference_validation_status: {report.get('reference_validation_status', 'blocked_missing_inputs')}",
        f"ensemble_execution_status: {report.get('ensemble_execution_status', 'blocked_template_only')}",
        f"candidate_site_id: {report.get('candidate_site_id', 'unknown')}",
        f"candidate_site_name: {report.get('candidate_site_name', 'unknown')}",
        f"generated_case_path: {report.get('generated_case_path', 'none')}",
        f"output_path_strategy: {report.get('output_path_strategy', 'tmp_or_ignored_only')}",
        f"write_status: {report.get('write_status', 'blocked')}",
    ]
    if report.get("blocked_reason"):
        lines.append(f"blocked_reason: {report['blocked_reason']}")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
