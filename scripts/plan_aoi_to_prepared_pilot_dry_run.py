#!/usr/bin/env python3
"""Compose the Chant Sura AOI-to-prepared-pilot dry-run workflow.

This is a read-only orchestrator. It chains the AOI acquisition planner, the
terrain release-zone candidate helper, the pragmatic release-plan helper, and
the portable command-plan helper into one deterministic workflow report. It
does not download data, stage public products, or run any ensemble work.
"""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

try:
    import yaml  # type: ignore
except ImportError as exc:  # pragma: no cover - environment setup.
    raise SystemExit("PyYAML is required. Run this script with `PYENV_VERSION=system uv run python ...`; CI may use `requirements-tools.txt`") from exc

from scripts.lib import output_profile_policy as OUTPUT_PROFILE_POLICY

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "aoi_to_prepared_pilot_dry_run_v1"
CASE_SKELETON_SCHEMA_VERSION = "aoi_to_prepared_pilot_case_skeleton_v1"
COMMAND_MANIFEST_SCHEMA_VERSION = "aoi_to_prepared_pilot_command_manifest_v1"
EXPECTED_OUTPUT_ROOTS_SCHEMA_VERSION = "aoi_to_prepared_pilot_expected_output_roots_v1"
BLOCKED_EXECUTION_SCHEMA_VERSION = "aoi_to_prepared_pilot_blocked_execution_v1"
GIS_SCOPE_SUMMARY_SCHEMA_VERSION = "aoi_to_prepared_pilot_gis_scope_summary_v1"
CACHE_VERIFICATION_SCHEMA_VERSION = "aoi_to_prepared_pilot_cache_verification_v1"
COMPILER_SCHEMA_VERSION = "aoi_to_prepared_pilot_compiler_v1"
RUN_MANIFEST_SCHEMA_VERSION = "aoi_to_prepared_pilot_run_manifest_v1"
EXPECTED_IO_INVENTORY_SCHEMA_VERSION = "aoi_to_prepared_pilot_expected_io_inventory_v1"
EXECUTION_HINTS_SCHEMA_VERSION = "aoi_to_prepared_pilot_execution_hints_v1"
FIRST_BLOCKER_SCHEMA_VERSION = "aoi_to_prepared_pilot_first_blocker_v1"
DEFAULT_SITE_CONFIG = ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml"
DEFAULT_COMMAND_PLAN_SITE = "chant_sura_fluelapass"
DEFAULT_ACQUISITION_MANIFEST = ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_public_geodata_acquisition.yaml"
SYNTHETIC_ROOT = Path("/tmp/tb125_aoi_to_prepared_pilot")


def _load_module(module_name: str, filename: str):
    path = ROOT / "scripts" / filename
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load helper module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


AOI_ACQUISITION = _load_module("aoi_to_prepared_pilot_aoi_acquisition", "plan_swisstopo_aoi_acquisition.py")
CANDIDATE_GENERATION = _load_module("aoi_to_prepared_pilot_candidate_generation", "plan_terrain_release_zone_candidates.py")
SCENARIO_PLAN = _load_module("aoi_to_prepared_pilot_scenario_plan", "plan_pragmatic_release_plan.py")
GENERIC_RELEASE_PLAN = _load_module("aoi_to_prepared_pilot_generic_release_plan", "plan_release_plan_dry_run.py")
COMMAND_PLAN = _load_module("aoi_to_prepared_pilot_command_plan", "generate_pilot_command_plan.py")


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def dump_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def dump_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def normalize_candidate_site_id(value: str) -> str:
    token = value.strip().replace("-", "_").replace(" ", "_")
    filtered = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in token)
    while "__" in filtered:
        filtered = filtered.replace("__", "_")
    return filtered.strip("_") or "unspecified_second_site"


def titleize_token(value: str) -> str:
    token = value.replace("_", " ").replace("-", " ").strip()
    return " ".join(part.capitalize() for part in token.split()) or "Placeholder Second Site"


def load_polygon_summary(path: Path) -> dict[str, Any]:
    payload = load_yaml(path)
    geometry = extract_geometry(payload)
    vertices = polygon_vertices(geometry)
    if len(vertices) < 3:
        raise ValueError(f"release polygon must contain at least three vertices: {path}")
    return {
        "source_path": str(path),
        "geometry_type": geometry.get("type", "Polygon"),
        "vertex_count": len(vertices),
        "extent_lv95_m": polygon_extent(vertices),
        "vertices": vertices,
    }


def extract_geometry(payload: dict[str, Any]) -> dict[str, Any]:
    if isinstance(payload.get("geometry"), dict):
        return payload["geometry"]
    if payload.get("type") == "FeatureCollection":
        features = payload.get("features")
        if isinstance(features, list):
            for feature in features:
                if isinstance(feature, dict) and isinstance(feature.get("geometry"), dict):
                    return feature["geometry"]
    if payload.get("type") in {"Polygon", "MultiPolygon"}:
        return payload
    return {}


def polygon_vertices(geometry: dict[str, Any]) -> list[tuple[float, float]]:
    raw_vertices = geometry.get("coordinates") or geometry.get("vertices")
    if not isinstance(raw_vertices, list):
        return []
    if raw_vertices and isinstance(raw_vertices[0], list) and raw_vertices and raw_vertices[0] and isinstance(raw_vertices[0][0], list):
        raw_vertices = raw_vertices[0]
    vertices: list[tuple[float, float]] = []
    for entry in raw_vertices:
        if not isinstance(entry, (list, tuple)) or len(entry) < 2:
            continue
        vertices.append((float(entry[0]), float(entry[1])))
    if vertices and vertices[0] == vertices[-1]:
        vertices.pop()
    return vertices


def polygon_extent(vertices: list[tuple[float, float]]) -> dict[str, float]:
    xs = [vertex[0] for vertex in vertices]
    ys = [vertex[1] for vertex in vertices]
    return {
        "crs": "EPSG:2056",
        "xmin": min(xs),
        "ymin": min(ys),
        "xmax": max(xs),
        "ymax": max(ys),
    }


def rewrite_strings(payload: Any, source: str, target: str) -> Any:
    if isinstance(payload, str):
        return payload.replace(source, target)
    if isinstance(payload, list):
        return [rewrite_strings(item, source, target) for item in payload]
    if isinstance(payload, dict):
        return {key: rewrite_strings(value, source, target) for key, value in payload.items()}
    return payload


def synthetic_config_root(candidate_site_id: str) -> Path:
    return SYNTHETIC_ROOT / candidate_site_id


def build_synthetic_acquisition_manifest(
    *,
    repo_root: Path,
    candidate_site_id: str,
    candidate_site_name: str,
    site_extent: dict[str, Any] | str,
) -> dict[str, Any]:
    manifest = copy.deepcopy(load_yaml(DEFAULT_ACQUISITION_MANIFEST))
    original_site_id = "chant_sura_fluelapass_portability_example_v1"
    manifest = rewrite_strings(manifest, original_site_id, candidate_site_id)
    manifest["candidate_site_id"] = candidate_site_id
    manifest["candidate_site_name"] = candidate_site_name
    manifest["selection_rationale"] = manifest.get("selection_rationale", "")
    manifest["site_extent"] = site_extent if isinstance(site_extent, dict) else {}
    for key in (
        "expected_processed_input_root",
        "expected_processed_context_root",
        "expected_validation_private_root",
        "expected_hazard_results_root",
    ):
        value = manifest.get(key)
        if isinstance(value, str) and value:
            manifest[key] = str((repo_root / value).resolve())
    ignored_roots = manifest.get("expected_ignored_output_roots")
    if isinstance(ignored_roots, list):
        manifest["expected_ignored_output_roots"] = [
            str((repo_root / value).resolve()) if isinstance(value, str) and value else value
            for value in ignored_roots
        ]
    for product in manifest.get("expected_products", []) or []:
        if isinstance(product, dict):
            staged_path = product.get("expected_staged_path")
            if isinstance(staged_path, str) and staged_path:
                product["expected_staged_path"] = str((repo_root / staged_path).resolve())
    return manifest


def prepare_working_config(
    site_config: Path | None,
    repo_root: Path,
    release_polygon_path: Path | None,
) -> tuple[Path, dict[str, Any], dict[str, Any] | None, bool, bool]:
    has_site_config = site_config is not None and site_config.exists()
    base_config = load_yaml(site_config) if has_site_config else {}
    release_polygon = load_polygon_summary(release_polygon_path) if release_polygon_path is not None and release_polygon_path.exists() else None
    site_extent = base_config.get("site_extent") if isinstance(base_config.get("site_extent"), dict) else {}
    candidate_site_id = normalize_candidate_site_id(
        str(base_config.get("candidate_site_id") or (release_polygon_path.stem if release_polygon_path is not None else "unspecified_second_site"))
    )
    candidate_site_name = str(
        base_config.get("candidate_site_name")
        or (titleize_token(release_polygon_path.stem) if release_polygon_path is not None else "Placeholder Second Site")
    )
    acquisition_manifest_path = Path(str(base_config.get("acquisition_manifest_path") or DEFAULT_ACQUISITION_MANIFEST))
    use_synthetic_config = not has_site_config or release_polygon is not None

    if release_polygon is not None:
        site_extent = release_polygon["extent_lv95_m"]

    if use_synthetic_config:
        synthetic_root = synthetic_config_root(candidate_site_id)
        config_path = synthetic_root / "site_config.yaml"
        acquisition_manifest_path = synthetic_root / "acquisition_manifest.yaml"
        processed_input_root = (repo_root / "data/processed/swisstopo" / candidate_site_id / "input").resolve()
        processed_context_root = (repo_root / "data/processed/swisstopo" / candidate_site_id / "context").resolve()
        validation_root = (repo_root / "validation/private" / candidate_site_id).resolve()
        hazard_root = (repo_root / "hazard/results" / candidate_site_id).resolve()
        synthetic_config = {
            **base_config,
            "candidate_site_id": candidate_site_id,
            "candidate_site_name": candidate_site_name,
            "site_extent": site_extent if isinstance(site_extent, dict) else {},
            "acquisition_manifest_path": str(acquisition_manifest_path),
            "expected_processed_input_root": str(processed_input_root),
            "expected_processed_context_root": str(processed_context_root),
            "expected_validation_private_root": str(validation_root),
            "expected_hazard_results_root": str(hazard_root),
            "expected_terrain_crop_path": str((processed_input_root / "terrain.asc").resolve()),
            "expected_terrain_metadata_path": str((processed_input_root / "terrain_metadata.yaml").resolve()),
            "expected_source_zone_metadata_path": str((processed_input_root / "source_zone_metadata.yaml").resolve()),
            "expected_scenario_table_path": str((processed_input_root / "scenario_table.csv").resolve()),
            "expected_source_scenario_policy_path": str(
                (repo_root / "validation/policies" / f"{candidate_site_id}_source_scenario_policy_v1.yaml").resolve()
            ),
            "expected_swissimage_context_root": str((processed_context_root / "swissimage").resolve()),
            "expected_swisstlm3d_context_root": str((processed_context_root / "swisstlm3d").resolve()),
            "expected_swisstlm3d_metadata_path": str((processed_context_root / "swisstlm3d" / "metadata.json").resolve()),
            "expected_swisssurface3d_context_root": str((processed_context_root / "swisssurface3d").resolve()),
            "expected_swisssurface3d_raster_context_root": str((processed_context_root / "swisssurface3d_raster").resolve()),
            "expected_swissbuildings3d_context_root": str((processed_context_root / "swissbuildings3d").resolve()),
            "expected_barrier_inventory_root": str((processed_context_root / "barriers").resolve()),
            "expected_validation_observations_root": str((processed_input_root / "validation/observations").resolve()),
        }
        if release_polygon is not None:
            synthetic_config["release_polygon_path"] = str(release_polygon_path)
            synthetic_config["release_polygon_summary"] = release_polygon
        if not synthetic_config.get("source_zone_scenario_contract"):
            synthetic_config["source_zone_scenario_contract"] = {
                "source_zone_id_pattern": f"{candidate_site_id}_*",
                "source_zone_geometry": "LV95 polygon",
                "release_point_table": "one row per release point",
                "block_scenario_table": "CSV table with one row per block / scenario record",
                "scenario_probability_semantics": "normalized within a block family; no annual frequency claim",
            }
        dump_yaml(config_path, synthetic_config)
        dump_yaml(
            acquisition_manifest_path,
            build_synthetic_acquisition_manifest(
                repo_root=repo_root,
                candidate_site_id=candidate_site_id,
                candidate_site_name=candidate_site_name,
                site_extent=site_extent if isinstance(site_extent, dict) else {},
            ),
        )
        return config_path, synthetic_config, release_polygon, True, has_site_config

    return site_config if site_config is not None else DEFAULT_SITE_CONFIG, base_config, release_polygon, False, has_site_config


def build_prep_summary(
    *,
    config_path: Path,
    config: dict[str, Any],
    release_polygon: dict[str, Any] | None,
    synthetic_config: bool,
    has_site_config: bool,
    acquisition_report: dict[str, Any],
    cache_verification_report: dict[str, Any],
    release_plan_report: dict[str, Any],
    generic_release_plan_report: dict[str, Any],
    candidate_generation_report: dict[str, Any],
    command_plan_report: dict[str, Any],
) -> dict[str, Any]:
    terrain_manifests = [
        row
        for row in acquisition_report.get("required_public_geodata_products", [])
        if row.get("category") in {"terrain_crop", "terrain_metadata"}
    ]
    terrain_metadata_record = next(
        (
            {
                "category": row.get("category"),
                "product": row.get("product"),
                "required": row.get("required"),
                "expected_staged_path": acquisition_report.get("expected_staging_paths", {}).get("terrain_metadata", row.get("path_or_pattern")),
                "current_status": "ready"
                if Path(
                    acquisition_report.get("expected_staging_paths", {}).get("terrain_metadata", row.get("path_or_pattern")) or ""
                ).exists()
                else row.get("status"),
                "staged": Path(
                    acquisition_report.get("expected_staging_paths", {}).get("terrain_metadata", row.get("path_or_pattern")) or ""
                ).exists(),
            }
            for row in acquisition_report.get("required_metadata_records", [])
            if row.get("category") == "terrain_metadata"
        ),
        None,
    )
    if terrain_metadata_record is not None:
        terrain_manifests.append(terrain_metadata_record)
    context_manifests = list(acquisition_report.get("public_context_acquisition_plan", []))
    workflow_contract = acquisition_report.get("public_geodata_workflow_contract", {})
    cache_layout = workflow_contract.get("public_geodata_cache_contract", {}).get("cache_layout", {}) if isinstance(workflow_contract, dict) else {}
    gis_scope_summary = build_gis_scope_summary(
        acquisition_report=acquisition_report,
        cache_verification_report=cache_verification_report,
        terrain_manifests=terrain_manifests,
        context_manifests=context_manifests,
        command_plan_report=command_plan_report,
        workflow_status=release_plan_report.get("scenario_plan_status", "unknown"),
    )
    release_plan_paths = release_plan_report.get("source_inputs", {})
    generic_release_plan_contract = generic_release_plan_report.get("scenario_generation_contract", {})
    release_scenario_placeholders = {
        "source_scenario_policy_path": release_plan_paths.get("source_scenario_policy_path", ""),
        "scenario_table_path": release_plan_paths.get("scenario_table_path", ""),
        "scenario_table_manifest_path": generic_release_plan_contract.get("generic_scenario_generation", {}).get("scenario_table_manifest_path", ""),
        "scenario_generation_command": generic_release_plan_contract.get("generic_scenario_generation", {}).get("command", ""),
        "same_scale_reference_path": release_plan_paths.get("same_scale_reference_path", ""),
        "release_polygon": release_polygon,
        "scenario_plan_status": release_plan_report.get("scenario_plan_status", "unknown"),
    }
    candidate_source_zones = {
        "candidate_metrics_status": candidate_generation_report.get("candidate_metrics_status", "unknown"),
        "candidate_release_zone_set_status": candidate_generation_report.get("candidate_release_zone_set_status", "unknown"),
        "candidate_release_zone_interpretation": candidate_generation_report.get("candidate_release_zone_interpretation", "unknown"),
        "candidate_summary": candidate_generation_report.get("candidate_summary", {}),
        "screening_criteria": candidate_generation_report.get("screening_criteria", {}),
        "terrain_inputs": candidate_generation_report.get("terrain_inputs", {}),
        "source_zone_inputs": candidate_generation_report.get("source_zone_inputs", {}),
        "blocked_missing_inputs": candidate_generation_report.get("blocked_missing_inputs", []),
        "blocked_reason": candidate_generation_report.get("blocked_reason", ""),
        "claim_boundaries": candidate_generation_report.get("claim_boundaries", {}),
        "candidate_release_zone_products": candidate_generation_report.get("candidate_release_zone_products", {}),
    }
    scenario_generation_inputs = {
        "scenario_plan_status": release_plan_report.get("scenario_plan_status", "unknown"),
        "source_policy_provenance": release_plan_report.get("source_policy_provenance", {}),
        "generic_scenario_generation": generic_release_plan_contract.get("generic_scenario_generation", {}),
        "generic_candidate_source_zone_provenance": generic_release_plan_contract.get("generic_candidate_source_zone_provenance", {}),
        "block_size_bins": release_plan_report.get("block_size_bins", []),
        "weighting_semantics": release_plan_report.get("weighting_semantics", {}),
        "reference_scenario_table": release_plan_report.get("reference_scenario_table", {}),
        "scenario_plan_summary": release_plan_report.get("scenario_plan_summary", {}),
        "explicit_non_frequency_labels": release_plan_report.get("explicit_non_frequency_labels", []),
        "same_scale_reference": release_plan_report.get("same_scale_reference", {}),
        "claim_boundary": release_plan_report.get("claim_boundary", {}),
        "pragmatic_coverage_boundary": release_plan_report.get("pragmatic_coverage_boundary", {}),
        "source_inputs": release_plan_report.get("source_inputs", {}),
        "scenario_table_manifest_path": generic_release_plan_contract.get("generic_scenario_generation", {}).get("scenario_table_manifest_path", ""),
        "blocked_execution_status": generic_release_plan_contract.get("generic_scenario_generation", {}).get(
            "blocked_execution_status", release_plan_report.get("scenario_plan_status", "unknown")
        ),
        "conditional_only_weighting": generic_release_plan_contract.get("generic_scenario_generation", {}).get("conditional_only_weighting", True),
    }
    command_plan_hooks = [
        {
            "command_id": command["id"],
            "description": command["description"],
            "command": command["command"],
            "blocked_reason": command.get("blocked_reason", ""),
            "execution_class": command_execution_class(command),
            "expected_inputs": command.get("expected_inputs", []),
            "expected_outputs": command.get("expected_outputs", []),
            "read_only": command.get("read_only", False),
        }
            for command in command_plan_report.get("commands", [])
        if command["id"]
        in {
            "second_site_aoi_acquisition_dry_run_planner",
            "second_site_portability_preflight",
            "second_site_case_skeleton_dry_run",
            "second_site_release_plan_dry_run",
            "second_site_release_plan_execution_template",
            "second_site_benchmark_preparation_template",
        }
    ]
    blocked_template_outputs = command_plan_report.get("ignored_output_paths", [])
    blocked_template_output_roots = [str(Path(path).parent) for path in blocked_template_outputs if path]
    ignored_output_roots = dedupe(
        [
            *acquisition_report.get("acquisition_manifest_expected_ignored_roots", []),
            *blocked_template_output_roots,
            *command_plan_report.get("ignored_output_paths", []),
        ]
    )
    input_mode = "missing_inputs"
    if release_polygon is not None and has_site_config:
        input_mode = "aoi_extent_with_release_polygon"
    elif release_polygon is not None:
        input_mode = "release_polygon"
    elif has_site_config:
        input_mode = "aoi_extent"

    site_extent = acquisition_report.get("site_extent", {})
    if not isinstance(site_extent, dict):
        site_extent = {}

    return {
        "input_mode": input_mode,
        "site_config_path": str(config_path),
        "candidate_site_id": acquisition_report.get("candidate_site_id", ""),
        "candidate_site_name": acquisition_report.get("candidate_site_name", ""),
        "candidate_selection_rationale": acquisition_report.get("candidate_selection_rationale", ""),
        "site_extent": site_extent,
        "release_polygon": release_polygon,
        "synthetic_config": synthetic_config,
        "cache_verification": cache_verification_report,
        "ignored_root_layout": cache_layout,
        "aoi_tile_discovery": acquisition_report.get("aoi_tile_discovery", {}),
        "candidate_source_zones": candidate_source_zones,
        "scenario_generation_inputs": scenario_generation_inputs,
        "terrain_manifests": terrain_manifests,
        "context_manifests": context_manifests,
        "gis_scope_summary": gis_scope_summary,
        "release_scenario_placeholders": release_scenario_placeholders,
        "command_plan_hooks": command_plan_hooks,
        "ignored_output_roots": ignored_output_roots,
        "output_root_planning": {
            "prepared_validation_root": f"validation/private/{acquisition_report.get('candidate_site_id', '')}",
            "prepared_hazard_root": f"hazard/results/{acquisition_report.get('candidate_site_id', '')}",
            "ignored_output_roots": ignored_output_roots,
            "command_plan_ignored_output_roots": command_plan_report.get("ignored_output_paths", []),
            "blocked_command_ids": command_plan_report.get("blocked_template_commands", []),
            "blocked_execution_status": blocked_execution_status(command_plan_report),
        },
    }


@contextmanager
def _patched_repo_root(repo_root: Path) -> Iterator[None]:
    patched_targets = [
        (AOI_ACQUISITION, "ROOT"),
        (AOI_ACQUISITION.PREFLIGHT, "ROOT"),
    ]
    originals: list[tuple[Any, str, Any]] = []
    for module, attr in patched_targets:
        originals.append((module, attr, getattr(module, attr)))
        setattr(module, attr, repo_root)
    try:
        yield
    finally:
        for module, attr, original in reversed(originals):
            setattr(module, attr, original)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site-config", type=Path, default=DEFAULT_SITE_CONFIG)
    parser.add_argument("--release-polygon", type=Path, default=None)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=None,
        help="optional ignored output root for the candidate case skeleton bundle",
    )
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    args = parser.parse_args(argv)

    report = build_report(
        args.site_config,
        repo_root=args.repo_root,
        release_polygon_path=args.release_polygon,
        skeleton_output_root=args.output_root,
    )

    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    output = json.dumps(report, indent=2, sort_keys=True) if args.format == "json" else render_text_report(report)
    print(output)
    compiler_status = report.get("prepared_pilot_compiler", {}).get("classification", report["workflow_status"])
    return 0 if compiler_status != "blocked_missing_inputs" else 2


def build_report(
    site_config: Path | None,
    repo_root: Path | None = None,
    release_polygon_path: Path | None = None,
    skeleton_output_root: Path | None = None,
) -> dict[str, Any]:
    repo_root = repo_root or ROOT
    config_path, config, release_polygon, synthetic_config, has_site_config = prepare_working_config(
        site_config, repo_root, release_polygon_path
    )

    with _patched_repo_root(repo_root):
        acquisition_report = AOI_ACQUISITION.build_report(config_path)
        cache_verification_report = build_cache_verification_report(
            acquisition_report=acquisition_report,
            repo_root=repo_root,
        )
        candidate_generation_report = CANDIDATE_GENERATION.build_report(repo_root=repo_root)
        release_plan_report = SCENARIO_PLAN.build_report()
        generic_release_plan_report = GENERIC_RELEASE_PLAN.build_report(config_path, repo_root=repo_root)

    command_plan_report = COMMAND_PLAN.build_report(DEFAULT_COMMAND_PLAN_SITE, config_path)

    steps = build_steps(
        acquisition_report=acquisition_report,
        cache_verification_report=cache_verification_report,
        release_plan_report=release_plan_report,
        candidate_generation_report=candidate_generation_report,
        command_plan_report=command_plan_report,
    )
    generated_output_roots = sorted({root for step in steps for root in step["generated_output_roots"]})
    ignored_output_roots = sorted({root for step in steps for root in step["ignored_output_roots"]})
    blockers = [blocker for step in steps for blocker in step["blockers"]]

    workflow_status = aggregate_workflow_status(step["status"] for step in steps)
    prep_summary = build_prep_summary(
        config_path=config_path,
        config=config,
        release_polygon=release_polygon,
        synthetic_config=synthetic_config,
        has_site_config=has_site_config,
        acquisition_report=acquisition_report,
        cache_verification_report=cache_verification_report,
        release_plan_report=release_plan_report,
        generic_release_plan_report=generic_release_plan_report,
        candidate_generation_report=candidate_generation_report,
        command_plan_report=command_plan_report,
    )
    if isinstance(prep_summary.get("gis_scope_summary"), dict):
        prep_summary["gis_scope_summary"]["status"] = workflow_status
    source_zone_inputs = prep_summary.get("candidate_source_zones", {}).get("source_zone_inputs") or {}
    scenario_source_inputs = prep_summary.get("scenario_generation_inputs", {}).get("source_inputs") or {}
    def resolve_compiler_path(value: Any) -> Path | None:
        if not isinstance(value, str) or not value:
            return None
        path = Path(value)
        return path if path.is_absolute() else repo_root / path

    compiler_required_paths = dedupe(
        [
            *(
                str(resolved)
                for row in prep_summary.get("terrain_manifests", [])
                if row.get("expected_staged_path")
                for resolved in [resolve_compiler_path(row.get("expected_staged_path"))]
                if resolved is not None
            ),
            *(
                str(resolved)
                for key, value in source_zone_inputs.items()
                for resolved in [resolve_compiler_path(value) if key.endswith("_path") else None]
                if resolved is not None
            ),
            *(
                str(resolved)
                for key, value in scenario_source_inputs.items()
                for resolved in [resolve_compiler_path(value) if key != "same_scale_reference_path" else None]
                if resolved is not None
            ),
        ]
    )
    compiler_missing_inputs = [path for path in compiler_required_paths if not Path(path).exists()]
    if compiler_missing_inputs:
        workflow_status = "blocked_missing_inputs"
        if isinstance(prep_summary.get("gis_scope_summary"), dict):
            prep_summary["gis_scope_summary"]["status"] = workflow_status
    skeleton_output = build_case_skeleton_output(
        report_inputs={
            "config_path": config_path,
            "config": config,
            "release_polygon": release_polygon,
            "synthetic_config": synthetic_config,
            "has_site_config": has_site_config,
            "acquisition_report": acquisition_report,
            "release_plan_report": release_plan_report,
            "generic_release_plan_report": generic_release_plan_report,
            "candidate_generation_report": candidate_generation_report,
            "command_plan_report": command_plan_report,
            "prep_summary": prep_summary,
            "workflow_status": workflow_status,
            "workflow_steps": steps,
            "compiler_missing_inputs": compiler_missing_inputs,
        },
        repo_root=repo_root,
        output_root=skeleton_output_root,
    )
    if skeleton_output["write_status"] == "written":
        write_case_skeleton_bundle(skeleton_output)

    report = {
        "schema_version": SCHEMA_VERSION,
        "workflow_status": workflow_status,
        "preparation_status": workflow_status,
        "candidate_site_id": acquisition_report["candidate_site_id"],
        "candidate_site_name": acquisition_report["candidate_site_name"],
        "candidate_selection_rationale": acquisition_report["candidate_selection_rationale"],
        "site_extent": acquisition_report["site_extent"],
        "preparation_input": prep_summary,
        "cache_verification": cache_verification_report,
        "terrain_manifests": prep_summary["terrain_manifests"],
        "context_manifests": prep_summary["context_manifests"],
        "gis_scope_summary": prep_summary["gis_scope_summary"],
        "release_scenario_placeholders": prep_summary["release_scenario_placeholders"],
        "candidate_source_zones": prep_summary["candidate_source_zones"],
        "scenario_generation_inputs": prep_summary["scenario_generation_inputs"],
        "output_root_planning": prep_summary["output_root_planning"],
        "command_plan_hooks": prep_summary["command_plan_hooks"],
        "ignored_output_roots": prep_summary["ignored_output_roots"],
        "step_order": [step["step_id"] for step in steps],
        "workflow_steps": steps,
        "workflow_blockers": blockers,
        "workflow_blocker_count": len(blockers),
        "workflow_generated_output_roots": generated_output_roots,
        "workflow_ignored_output_roots": ignored_output_roots,
        "blocked_missing_inputs": dedupe(
            [
                *(str(item) for item in acquisition_report.get("blocked_missing_inputs", []) if item),
                *(str(item) for item in cache_verification_report.get("blocked_missing_inputs", []) if item),
                *(str(item) for item in prep_summary.get("candidate_source_zones", {}).get("blocked_missing_inputs", []) if item),
                *(str(item) for item in release_plan_report.get("missing_inputs", []) if item),
                *compiler_missing_inputs,
            ]
        ),
        "expected_inputs_by_step": {step["step_id"]: step["expected_inputs"] for step in steps},
        "generated_output_roots_by_step": {
            step["step_id"]: step["generated_output_roots"] for step in steps
        },
        "ignored_output_roots_by_step": {step["step_id"]: step["ignored_output_roots"] for step in steps},
        "acquisition_report": acquisition_report,
        "candidate_generation_report": candidate_generation_report,
        "release_plan_report": release_plan_report,
        "command_plan_report": command_plan_report,
        "claim_boundaries": candidate_generation_report.get("claim_boundaries", {}),
        "scale_up_authorized": False,
        "operational_claims_allowed": False,
        "case_skeleton_output": skeleton_output,
    }
    report["prepared_pilot_compiler"] = build_prepared_pilot_compiler_report(skeleton_output=skeleton_output)
    return report


def build_gis_scope_summary(
    *,
    acquisition_report: dict[str, Any],
    cache_verification_report: dict[str, Any],
    terrain_manifests: list[dict[str, Any]],
    context_manifests: list[dict[str, Any]],
    command_plan_report: dict[str, Any],
    workflow_status: str,
) -> dict[str, Any]:
    planned_products = [
        build_gis_scope_product_entry(row, source="terrain")
        for row in terrain_manifests
    ]
    planned_products.extend(
        build_gis_scope_product_entry(row, source="context")
        for row in context_manifests
    )
    blocked_missing_inputs = dedupe(
        [
            *(str(item) for item in acquisition_report.get("blocked_missing_inputs", []) if item),
            *(str(item) for item in cache_verification_report.get("blocked_missing_inputs", []) if item),
            *(
                product["expected_staged_path"]
                for product in planned_products
                if product.get("current_status") == "missing" and product.get("expected_staged_path")
            ),
        ]
    )
    downstream_template_only_commands = list(command_plan_report.get("blocked_template_commands", []))
    cog_export_expectation = {
        "status": "template_only" if downstream_template_only_commands else "not_requested",
        "generated_now": False,
        "hazard_layers_generated": False,
        "cog_export_generated": False,
        "downstream_template_only_command_ids": downstream_template_only_commands,
        "summary": (
            "AOI handoff stops before hazard-map generation; any COG export remains a downstream template-only expectation."
        ),
    }
    non_operational_gis_boundaries = {
        "operational_claims_allowed": False,
        "hazard_layers_generated": False,
        "cog_export_generated": False,
        "scale_up_authorized": False,
        "distributed_execution_authorized": False,
        "annual_frequency_claims_allowed": False,
        "physical_probability_claims_allowed": False,
        "risk_exposure_vulnerability_claims_allowed": False,
    }
    template_only_products = [
        {
            "category": "downstream_cog_export",
            "product": "hazard-map COG export expectation",
            "product_kind": "raster",
            "scope_state": "template_only",
            "current_status": "not_generated",
            "expected_staged_path": "",
            "source": "command_plan",
            "downstream_template_only_command_ids": downstream_template_only_commands,
        }
    ]
    return {
        "schema_version": GIS_SCOPE_SUMMARY_SCHEMA_VERSION,
        "status": workflow_status,
        "summary": (
            "The AOI case-skeleton lists planned GIS inputs separately from downstream template-only COG expectations and does not imply any hazard layers were generated."
        ),
        "planned_products": planned_products,
        "planned_raster_products": [product for product in planned_products if product.get("product_kind") == "raster"],
        "planned_vector_products": [product for product in planned_products if product.get("product_kind") == "vector"],
        "cache_verification": cache_verification_report,
        "template_only_products": template_only_products,
        "blocked_missing_inputs": blocked_missing_inputs,
        "cog_export_expectation": cog_export_expectation,
        "non_operational_gis_boundaries": non_operational_gis_boundaries,
        "no_hazard_layers_generated": True,
    }


def build_gis_scope_product_entry(row: dict[str, Any], *, source: str) -> dict[str, Any]:
    current_status = str(row.get("current_status") or row.get("status") or "unknown")
    scope_state = "planned"
    if current_status == "missing":
        scope_state = "unavailable"
    elif current_status == "optional":
        scope_state = "planned"
    return {
        "source": source,
        "category": row.get("category", ""),
        "product": row.get("product", ""),
        "product_kind": classify_gis_product_kind(row.get("category", ""), row.get("product", "")),
        "required": bool(row.get("required", False)),
        "current_status": current_status,
        "scope_state": scope_state,
        "expected_staged_path": row.get("expected_staged_path", ""),
    }


def classify_gis_product_kind(category: str, product: str) -> str:
    if category in {"terrain_crop", "swissimage_context", "swisssurface3d_context", "swisssurface3d_raster_context"}:
        return "raster"
    if category in {"swisstlm3d_context", "swissbuildings3d_context", "barrier_inventory"}:
        return "vector"
    if category.endswith("_metadata") or category in {"aoi_tile_catalog", "scenario_table", "source_scenario_policy"}:
        return "metadata"
    if category == "source_zone_metadata":
        return "metadata"
    if category == "release_observation_evidence":
        return "evidence"
    if "raster" in category or "terrain" in category:
        return "raster"
    if "tile" in category or "catalog" in category:
        return "metadata"
    return "unknown"


def build_steps(
    *,
    acquisition_report: dict[str, Any],
    cache_verification_report: dict[str, Any],
    release_plan_report: dict[str, Any],
    candidate_generation_report: dict[str, Any],
    command_plan_report: dict[str, Any],
) -> list[dict[str, Any]]:
    candidate_site_id = acquisition_report["candidate_site_id"]
    ignored_site_roots = [
        f"validation/private/{candidate_site_id}",
        f"hazard/results/{candidate_site_id}",
    ]

    steps: list[dict[str, Any]] = [
        {
            "step_id": "aoi_acquisition",
            "label": "AOI acquisition contract",
            "status": acquisition_report["acquisition_boundary_status"],
            "blocked_reason": (
                "required core inputs remain missing"
                if acquisition_report["acquisition_boundary_status"] == "blocked_missing_inputs"
                else "public-context products remain deferred"
                if acquisition_report["acquisition_boundary_status"] != "ready"
                else ""
            ),
            "expected_inputs": [
                acquisition_report["acquisition_manifest_path"],
                *acquisition_expected_inputs(acquisition_report),
            ],
            "generated_output_roots": acquisition_report["public_context_acquisition_summary"].get("expected_staging_roots", []),
            "ignored_output_roots": acquisition_report.get("acquisition_manifest_expected_ignored_roots", []),
            "blockers": build_step_blockers(
                "aoi_acquisition",
                acquisition_report["acquisition_boundary_status"],
                acquisition_report.get("acquisition_manifest_expected_ignored_roots", []),
                acquisition_report.get("deferred_public_context_categories", []),
            ),
        },
        {
            "step_id": "public_geodata_cache_verification",
            "label": "Public geodata cache verification",
            "status": cache_verification_step_status(cache_verification_report),
            "blocked_reason": cache_verification_blocked_reason(cache_verification_report),
            "expected_inputs": cache_verification_expected_inputs(cache_verification_report),
            "generated_output_roots": [],
            "ignored_output_roots": [],
            "blockers": build_step_blockers(
                "public_geodata_cache_verification",
                cache_verification_step_status(cache_verification_report),
                [],
                cache_verification_report.get("blocked_missing_inputs", []),
            ),
        },
        {
            "step_id": "release_zone_candidate_generation",
            "label": "Release-zone candidate generation",
            "status": candidate_generation_report["candidate_metrics_status"],
            "blocked_reason": candidate_generation_report.get("blocked_reason", ""),
            "expected_inputs": expected_inputs_from_candidate_generation(candidate_generation_report),
            "generated_output_roots": [],
            "ignored_output_roots": [],
            "blockers": build_step_blockers(
                "release_zone_candidate_generation",
                candidate_generation_report["candidate_metrics_status"],
                [],
                candidate_generation_report.get("blocked_missing_inputs", []),
            ),
        },
        {
            "step_id": "release_plan_dry_run",
            "label": "Scenario-table generation",
            "status": release_plan_report["scenario_plan_status"],
            "blocked_reason": release_plan_report.get("blocked_reason", ""),
            "expected_inputs": expected_inputs_from_scenario_generation(release_plan_report),
            "generated_output_roots": [],
            "ignored_output_roots": [],
            "blockers": build_step_blockers(
                "release_plan_dry_run",
                release_plan_report["scenario_plan_status"],
                [],
                release_plan_report.get("missing_inputs", []),
            ),
        },
        {
            "step_id": "prepared_pilot_command_plan",
            "label": "Prepared-pilot command-plan helper",
            "status": command_plan_step_status(command_plan_report),
            "blocked_reason": command_plan_blocked_reason(command_plan_report),
            "expected_inputs": command_plan_expected_inputs(command_plan_report),
            "generated_output_roots": [],
            "ignored_output_roots": command_plan_report["ignored_output_paths"],
            "blockers": build_step_blockers(
                "prepared_pilot_command_plan",
                command_plan_step_status(command_plan_report),
                command_plan_report["ignored_output_paths"],
                command_plan_report.get("blocked_template_commands", []),
            ),
        },
    ]
    return steps


def build_step_blockers(
    step_id: str,
    status: str,
    ignored_output_roots: list[str],
    blocker_payload: list[Any],
) -> list[dict[str, Any]]:
    blockers: list[dict[str, Any]] = []
    if status == "ready":
        return blockers
    blockers.append(
        {
            "step_id": step_id,
            "status": status,
            "ignored_output_roots": ignored_output_roots,
            "details": blocker_payload,
        }
    )
    return blockers


def acquisition_expected_inputs(report: dict[str, Any]) -> list[str]:
    paths: list[str] = []
    for entry in report.get("required_public_geodata_products", []):
        path = entry.get("expected_staged_path")
        if path:
            paths.append(path)
    for entry in report.get("required_metadata_records", []):
        path = entry.get("path_or_pattern")
        if path:
            paths.append(path)
    return dedupe(paths)


def expected_inputs_from_real_context_gate(report: dict[str, Any]) -> list[str]:
    inputs: list[str] = []
    for entry in report.get("local_core_inputs", []):
        expected_path = entry.get("expected_path")
        if expected_path:
            inputs.append(expected_path)
    for entry in report.get("supporting_local_roots", []):
        expected_path = entry.get("expected_path")
        if expected_path:
            inputs.append(expected_path)
    return dedupe(inputs)


def expected_inputs_from_release_zone(report: dict[str, Any]) -> list[str]:
    inputs: list[str] = []
    for entry in report.get("heuristic_inputs", []):
        expected_path = entry.get("path_or_pattern")
        if expected_path:
            inputs.append(expected_path)
    return dedupe(inputs)


def expected_inputs_from_candidate_generation(report: dict[str, Any]) -> list[str]:
    inputs: list[str] = []
    terrain_inputs = report.get("terrain_inputs", {})
    if isinstance(terrain_inputs, dict):
        for value in terrain_inputs.values():
            if isinstance(value, str):
                inputs.append(value)
    source_zone_inputs = report.get("source_zone_inputs", {})
    if isinstance(source_zone_inputs, dict):
        for value in source_zone_inputs.values():
            if isinstance(value, str):
                inputs.append(value)
    return dedupe(inputs)


def build_cache_verification_report(*, acquisition_report: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    workflow_contract = acquisition_report.get("public_geodata_workflow_contract", {})
    cache_contract = workflow_contract.get("public_geodata_cache_contract", {}) if isinstance(workflow_contract, dict) else {}
    cache_layout = cache_contract.get("cache_layout", {}) if isinstance(cache_contract, dict) else {}
    cache_manifest_value = cache_layout.get("cache_manifest_path")
    expected_products = list(acquisition_report.get("required_public_geodata_products", []))
    expected_metadata_records = list(acquisition_report.get("required_metadata_records", []))
    if not cache_manifest_value:
        return {
            "schema_version": CACHE_VERIFICATION_SCHEMA_VERSION,
            "cache_verification_status": "blocked_missing_inputs",
            "cache_manifest_path": "",
            "cache_manifest_status": "missing",
            "verification_status": "missing",
            "verification_report": None,
            "expected_products": expected_products,
            "expected_metadata_records": expected_metadata_records,
            "blocked_missing_inputs": cache_expected_product_descriptions(expected_products, expected_metadata_records),
            "cache_contract": cache_contract,
            "read_only": True,
            "scale_up_authorized": False,
            "operational_claims_allowed": False,
        }
    cache_manifest_path = Path(str(cache_manifest_value))
    if not cache_manifest_path.exists():
        return {
            "schema_version": CACHE_VERIFICATION_SCHEMA_VERSION,
            "cache_verification_status": "blocked_missing_inputs",
            "cache_manifest_path": str(cache_manifest_path),
            "cache_manifest_status": "missing",
            "verification_status": "missing",
            "verification_report": None,
            "expected_products": expected_products,
            "expected_metadata_records": expected_metadata_records,
            "blocked_missing_inputs": cache_missing_inputs(
                cache_manifest_path=cache_manifest_path,
                expected_products=expected_products,
                expected_metadata_records=expected_metadata_records,
            ),
            "cache_contract": cache_contract,
            "read_only": True,
            "scale_up_authorized": False,
            "operational_claims_allowed": False,
        }

    manifest = load_yaml(cache_manifest_path)
    manifest_products = manifest.get("products") if isinstance(manifest, dict) else []
    verification_report = AOI_ACQUISITION.PREFLIGHT.verify_public_geodata_cache(cache_manifest_path)
    blocked_missing_inputs = []
    if verification_report.get("verification_status") != "verified":
        blocked_missing_inputs = cache_missing_inputs(
            cache_manifest_path=cache_manifest_path,
            expected_products=expected_products,
            expected_metadata_records=expected_metadata_records,
            manifest_products=manifest_products if isinstance(manifest_products, list) else [],
            verification_report=verification_report,
        )
    return {
        "schema_version": CACHE_VERIFICATION_SCHEMA_VERSION,
        "cache_verification_status": cache_verification_step_status(
            {"verification_status": verification_report.get("verification_status"), "cache_manifest_status": "ready"}
        ),
        "cache_manifest_path": str(cache_manifest_path),
        "cache_manifest_status": "ready",
        "verification_status": verification_report.get("verification_status", "missing"),
        "verification_report": verification_report,
        "expected_products": expected_products,
        "expected_metadata_records": expected_metadata_records,
        "manifest_products": manifest_products if isinstance(manifest_products, list) else [],
        "blocked_missing_inputs": blocked_missing_inputs,
        "cache_contract": cache_contract,
        "read_only": True,
        "scale_up_authorized": False,
        "operational_claims_allowed": False,
    }


def cache_missing_inputs(
    *,
    cache_manifest_path: Path,
    expected_products: list[dict[str, Any]],
    expected_metadata_records: list[dict[str, Any]],
    manifest_products: list[dict[str, Any]] | None = None,
    verification_report: dict[str, Any] | None = None,
) -> list[str]:
    missing_inputs = [str(cache_manifest_path)]
    if manifest_products is None or not manifest_products:
        missing_inputs.extend(
            cache_expected_product_descriptions(expected_products, expected_metadata_records)
        )
        return dedupe(missing_inputs)

    if isinstance(verification_report, dict) and verification_report.get("verification_status") == "verified":
        return []

    verification_products = verification_report.get("products", []) if isinstance(verification_report, dict) else []
    for index, product in enumerate(manifest_products):
        verification_product = verification_products[index] if index < len(verification_products) and isinstance(verification_products[index], dict) else {}
        verification_status = str(verification_product.get("verification_status") or "")
        if verification_status == "verified":
            continue
        product_label = cache_product_label(product)
        if verification_status == "missing":
            missing_paths = verification_product.get("missing_paths") or []
            if missing_paths:
                missing_inputs.extend(f"{product_label}: {item}" for item in missing_paths if item)
            else:
                missing_inputs.append(f"{product_label}: staged product or metadata missing")
            continue
        metadata_mismatches = verification_product.get("metadata_mismatches") or []
        if metadata_mismatches:
            missing_inputs.extend(f"{product_label}: metadata {item}" for item in metadata_mismatches if item)
    return dedupe(missing_inputs)


def cache_expected_product_descriptions(
    expected_products: list[dict[str, Any]],
    expected_metadata_records: list[dict[str, Any]],
) -> list[str]:
    descriptions: list[str] = []
    for row in expected_products:
        descriptions.append(cache_product_label(row))
        expected_path = row.get("expected_staged_path")
        if expected_path:
            descriptions.append(f"{cache_product_label(row)} -> {expected_path}")
    for row in expected_metadata_records:
        descriptions.append(cache_product_label(row))
        expected_path = row.get("path_or_pattern") or row.get("expected_staged_path")
        if expected_path:
            descriptions.append(f"{cache_product_label(row)} -> {expected_path}")
    return dedupe(descriptions)


def cache_product_label(record: dict[str, Any]) -> str:
    category = str(record.get("category") or record.get("kind") or "cache_product")
    product = str(record.get("product") or record.get("product_name") or category)
    expected_path = str(record.get("expected_staged_path") or record.get("path_or_pattern") or "")
    if expected_path:
        return f"{category} ({product}) @ {expected_path}"
    return f"{category} ({product})"


def cache_verification_step_status(report: dict[str, Any]) -> str:
    status = str(report.get("verification_status") or report.get("cache_verification_status") or "blocked_missing_inputs")
    if status == "verified":
        return "ready"
    if status == "missing" or report.get("cache_manifest_status") == "missing":
        return "blocked_missing_inputs"
    return status


def cache_verification_blocked_reason(report: dict[str, Any]) -> str:
    status = str(report.get("verification_status") or report.get("cache_verification_status") or "")
    if status == "verified":
        return ""
    if report.get("cache_manifest_status") == "missing":
        return f"missing cache manifest: {report.get('cache_manifest_path', '')}"
    if status == "missing":
        return "cache verification is blocked until the staged product and metadata pairs exist"
    if status == "checksum_mismatch":
        return "cache verification checksum mismatch"
    if status == "metadata_mismatch":
        return "cache verification metadata mismatch"
    return "cache verification is blocked"


def cache_verification_expected_inputs(report: dict[str, Any]) -> list[str]:
    inputs = [str(report.get("cache_manifest_path") or "")]
    for row in report.get("expected_products", []):
        if not isinstance(row, dict):
            continue
        expected_path = row.get("expected_staged_path")
        if expected_path:
            inputs.append(str(expected_path))
    for row in report.get("expected_metadata_records", []):
        if not isinstance(row, dict):
            continue
        expected_path = row.get("path_or_pattern") or row.get("expected_staged_path")
        if expected_path:
            inputs.append(str(expected_path))
    return dedupe([item for item in inputs if item])


def expected_inputs_from_scenario_generation(report: dict[str, Any]) -> list[str]:
    inputs: list[str] = []
    source_inputs = report.get("source_inputs", {})
    for path in (source_inputs or {}).values():
        if path:
            inputs.append(path)
    return dedupe(inputs)


def command_plan_step_status(report: dict[str, Any]) -> str:
    if report.get("blocked_template_commands"):
        return "deferred_public_context_inputs"
    return report.get("second_site_portability_status", "ready")


def command_plan_blocked_reason(report: dict[str, Any]) -> str:
    if report.get("blocked_template_commands"):
        return f"blocked_template_commands: {', '.join(report['blocked_template_commands'])}"
    return ""


def command_plan_expected_inputs(report: dict[str, Any]) -> list[str]:
    inputs: list[str] = []
    for command in report.get("commands", []):
        inputs.extend(command.get("expected_inputs", []))
    return dedupe(inputs)


def aggregate_workflow_status(statuses: Any) -> str:
    statuses = list(statuses)
    if any(status == "blocked_missing_inputs" for status in statuses):
        return "blocked_missing_inputs"
    if any(status != "ready" for status in statuses):
        return "deferred_public_context_inputs"
    return "ready"


def dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        ordered.append(item)
    return ordered


def classify_prepared_pilot_compiler(report: dict[str, Any]) -> str:
    if report.get("workflow_status") == "blocked_missing_inputs":
        return "blocked_missing_inputs"
    if report.get("command_plan_report", {}).get("blocked_template_commands"):
        return "ready_for_balfrin_postproc"
    return "ready_for_local_smoke"


def first_compiler_blocker(report: dict[str, Any]) -> dict[str, Any]:
    compiler_missing_inputs = [str(item) for item in report.get("compiler_missing_inputs", []) if str(item).strip()]
    if compiler_missing_inputs:
        return {
            "schema_version": FIRST_BLOCKER_SCHEMA_VERSION,
            "status": "blocked_missing_inputs",
            "step_id": "prepared_pilot_inputs",
            "label": "Prepared-pilot compiler inputs",
            "blocked_reason": "prepared-pilot inputs are missing",
            "missing_inputs": compiler_missing_inputs,
            "command_plan_blocked_commands": [],
            "first_missing_input": compiler_missing_inputs[0],
        }

    for step in report.get("workflow_steps", []):
        if step.get("step_id") != "prepared_pilot_command_plan":
            continue
        blocked_template_commands = list(report.get("command_plan_report", {}).get("blocked_template_commands", []))
        if blocked_template_commands:
            return {
                "schema_version": FIRST_BLOCKER_SCHEMA_VERSION,
                "status": step.get("status", "deferred_public_context_inputs"),
                "step_id": step.get("step_id", ""),
                "label": step.get("label", ""),
                "blocked_reason": step.get("blocked_reason", ""),
                "missing_inputs": blocked_template_commands,
                "command_plan_blocked_commands": blocked_template_commands,
                "first_missing_input": blocked_template_commands[0],
            }

    return {
        "schema_version": FIRST_BLOCKER_SCHEMA_VERSION,
        "status": "ready",
        "step_id": "",
        "label": "",
        "blocked_reason": "",
        "missing_inputs": [],
        "command_plan_blocked_commands": [],
        "first_missing_input": "",
    }


def flatten_command_field(commands: list[dict[str, Any]], field: str) -> list[str]:
    values: list[str] = []
    for command in commands:
        for item in command.get(field, []):
            if item:
                values.append(str(item))
    return dedupe(values)


def build_expected_io_inventory(
    *,
    report_inputs: dict[str, Any],
    skeleton_output: dict[str, Any],
) -> dict[str, Any]:
    steps = report_inputs["workflow_steps"]
    command_plan_report = report_inputs["command_plan_report"]
    prep_summary = report_inputs["prep_summary"]
    return {
        "schema_version": EXPECTED_IO_INVENTORY_SCHEMA_VERSION,
        "expected_input_paths": dedupe(
            [
                *flatten_command_field(steps, "expected_inputs"),
                *command_plan_expected_inputs(command_plan_report),
            ]
        ),
        "expected_output_paths": dedupe(
            [
                *flatten_command_field(steps, "generated_output_roots"),
                *flatten_command_field(steps, "ignored_output_roots"),
                *flatten_command_field(command_plan_report.get("commands", []), "expected_outputs"),
                *skeleton_output.get("expected_output_roots", []),
            ]
        ),
        "expected_inputs_by_step": skeleton_output.get("expected_inputs_by_step", {}),
        "generated_output_roots_by_step": skeleton_output.get("generated_output_roots_by_step", {}),
        "ignored_output_roots_by_step": skeleton_output.get("ignored_output_roots_by_step", {}),
        "expected_step_count": len(steps),
        "command_plan_expected_inputs": command_plan_expected_inputs(command_plan_report),
        "command_plan_expected_outputs": flatten_command_field(command_plan_report.get("commands", []), "expected_outputs"),
        "prepared_validation_root": prep_summary["output_root_planning"]["prepared_validation_root"],
        "prepared_hazard_root": prep_summary["output_root_planning"]["prepared_hazard_root"],
        "command_manifest_path": skeleton_output.get("command_manifest_path", ""),
        "run_manifest_path": skeleton_output.get("run_manifest_path", ""),
        "case_skeleton_path": skeleton_output.get("case_skeleton_path", ""),
    }


def build_output_profile_summary(report_inputs: dict[str, Any]) -> dict[str, Any]:
    command_plan_report = report_inputs["command_plan_report"]
    prep_summary = report_inputs["prep_summary"]
    return {
        "schema_version": OUTPUT_PROFILE_POLICY.POLICY_SCHEMA_VERSION,
        "command_profile_policy": command_plan_report.get("output_profile_policy", {}),
        "command_profile_validation": command_plan_report.get("output_profile_validation", {}),
        "command_plan_status": command_plan_report.get("command_plan_status", ""),
        "blocked_template_commands": list(command_plan_report.get("blocked_template_commands", [])),
        "gis_scope_summary": {
            "schema_version": prep_summary.get("gis_scope_summary", {}).get("schema_version", ""),
            "status": prep_summary.get("gis_scope_summary", {}).get("status", ""),
            "no_hazard_layers_generated": bool(prep_summary.get("gis_scope_summary", {}).get("no_hazard_layers_generated", False)),
            "cog_export_expectation": prep_summary.get("gis_scope_summary", {}).get("cog_export_expectation", {}),
            "non_operational_gis_boundaries": prep_summary.get("gis_scope_summary", {}).get("non_operational_gis_boundaries", {}),
        },
    }


def build_execution_hints(
    *,
    report_inputs: dict[str, Any],
    skeleton_output: dict[str, Any],
    classification: str,
) -> dict[str, Any]:
    prep_summary = report_inputs["prep_summary"]
    output_root = skeleton_output.get("output_root") or prep_summary["output_root_planning"]["prepared_validation_root"]
    balfrin_output_root = prep_summary["output_root_planning"]["prepared_hazard_root"]
    local_status = classification if classification != "ready_for_balfrin_postproc" else "ready_for_local_smoke"
    balfrin_status = classification if classification != "ready_for_local_smoke" else "not_required"
    return {
        "schema_version": EXECUTION_HINTS_SCHEMA_VERSION,
        "local": {
            "status": local_status,
            "execution_surface": "local_smoke",
            "output_root": output_root,
            "command_manifest_path": skeleton_output.get("command_manifest_path", ""),
            "run_manifest_path": skeleton_output.get("run_manifest_path", ""),
            "notes": [
                "keep the compiler package on a writable local path for smoke review",
                "no ensemble execution or Balfrin submission is authorized in this task",
            ],
        },
        "balfrin": {
            "status": balfrin_status,
            "execution_surface": "balfrin_postproc",
            "output_root": balfrin_output_root,
            "command_manifest_path": skeleton_output.get("command_manifest_path", ""),
            "run_manifest_path": skeleton_output.get("run_manifest_path", ""),
            "notes": [
                "handoff package only; live Balfrin submission remains out of scope here",
                "use the same compiler outputs after an access and readiness preflight in a later task",
            ],
        },
    }


def build_run_manifest(
    *,
    report_inputs: dict[str, Any],
    skeleton_output: dict[str, Any],
    classification: str,
    first_blocker: dict[str, Any],
) -> dict[str, Any]:
    expected_io_inventory = build_expected_io_inventory(report_inputs=report_inputs, skeleton_output=skeleton_output)
    output_profile = build_output_profile_summary(report_inputs)
    execution_hints = build_execution_hints(report_inputs=report_inputs, skeleton_output=skeleton_output, classification=classification)
    command_plan_report = report_inputs["command_plan_report"]
    prep_summary = report_inputs["prep_summary"]
    return {
        "schema_version": RUN_MANIFEST_SCHEMA_VERSION,
        "classification": classification,
        "run_manifest_status": classification,
        "candidate_site_id": report_inputs["acquisition_report"]["candidate_site_id"],
        "candidate_site_name": report_inputs["acquisition_report"]["candidate_site_name"],
        "workflow_status": report_inputs["workflow_status"],
        "input_mode": prep_summary["input_mode"],
        "prepared_validation_root": prep_summary["output_root_planning"]["prepared_validation_root"],
        "prepared_hazard_root": prep_summary["output_root_planning"]["prepared_hazard_root"],
        "command_plan": {
            "schema_version": command_plan_report.get("schema_version", ""),
            "command_plan_status": command_plan_report.get("command_plan_status", ""),
            "blocked_template_commands": list(command_plan_report.get("blocked_template_commands", [])),
            "command_group_ids": list(command_plan_report.get("command_group_ids", [])),
            "command_group_keys": list(command_plan_report.get("command_group_keys", [])),
            "command_ids": list(command_plan_report.get("command_ids", [])),
            "commands": command_plan_report.get("commands", []),
            "ignored_output_paths": list(command_plan_report.get("ignored_output_paths", [])),
            "output_profile_policy": command_plan_report.get("output_profile_policy", {}),
            "output_profile_validation": command_plan_report.get("output_profile_validation", {}),
        },
        "expected_io_inventory": expected_io_inventory,
        "output_profile": output_profile,
        "execution_hints": execution_hints,
        "first_blocker": first_blocker,
        "command_manifest_path": skeleton_output.get("command_manifest_path", ""),
        "run_manifest_path": skeleton_output.get("run_manifest_path", ""),
        "case_skeleton_path": skeleton_output.get("case_skeleton_path", ""),
    }


def build_prepared_pilot_compiler_report(
    *,
    skeleton_output: dict[str, Any],
) -> dict[str, Any]:
    run_manifest = skeleton_output.get("run_manifest", {})
    return {
        "schema_version": COMPILER_SCHEMA_VERSION,
        "classification": run_manifest.get("classification", "blocked_missing_inputs"),
        "run_manifest_path": skeleton_output.get("run_manifest_path", ""),
        "first_blocker": run_manifest.get("first_blocker", {}),
        "run_manifest": run_manifest,
        "command_plan": run_manifest["command_plan"],
        "expected_io_inventory": run_manifest["expected_io_inventory"],
        "output_profile": run_manifest["output_profile"],
        "execution_hints": run_manifest["execution_hints"],
    }


def render_text_report(report: dict[str, Any]) -> str:
    lines = [
        f"schema_version: {report['schema_version']}",
        f"workflow_status: {report['workflow_status']}",
        f"candidate_site_id: {report['candidate_site_id']}",
        f"candidate_site_name: {report['candidate_site_name']}",
        f"candidate_selection_rationale: {report['candidate_selection_rationale']}",
        f"site_extent: {report['site_extent']}",
        f"scale_up_authorized: {str(report['scale_up_authorized']).lower()}",
        f"operational_claims_allowed: {str(report['operational_claims_allowed']).lower()}",
        "",
        "preparation_input:",
    ]
    prep = report.get("preparation_input", {})
    for key in (
        "input_mode",
        "site_config_path",
        "candidate_site_id",
        "candidate_site_name",
        "candidate_selection_rationale",
        "site_extent",
    ):
        lines.append(f"- {key}: {prep.get(key, '')}")
    if prep.get("release_polygon"):
        lines.append("- release_polygon:")
        polygon = prep["release_polygon"]
        for key, value in polygon.items():
            lines.append(f"  - {key}: {value}")
    lines.extend(
        [
            "",
            "cache_verification:",
        ]
    )
    cache_verification = report.get("cache_verification", {})
    lines.append(f"- schema_version: {cache_verification.get('schema_version', '')}")
    lines.append(f"- cache_verification_status: {cache_verification.get('cache_verification_status', '')}")
    lines.append(f"- cache_manifest_status: {cache_verification.get('cache_manifest_status', '')}")
    lines.append(f"- cache_manifest_path: {cache_verification.get('cache_manifest_path', '')}")
    lines.append(f"- verification_status: {cache_verification.get('verification_status', '')}")
    if cache_verification.get("blocked_missing_inputs"):
        lines.append("- blocked_missing_inputs:")
        lines.extend(f"  - {item}" for item in cache_verification["blocked_missing_inputs"])
    else:
        lines.append("- blocked_missing_inputs: none")
    lines.append("- expected_products:")
    if cache_verification.get("expected_products"):
        for row in cache_verification["expected_products"]:
            lines.append(f"  - {cache_product_label(row)}")
    else:
        lines.append("  - none")
    lines.append("- expected_metadata_records:")
    if cache_verification.get("expected_metadata_records"):
        for row in cache_verification["expected_metadata_records"]:
            lines.append(f"  - {cache_product_label(row)}")
    else:
        lines.append("  - none")
    lines.extend(
        [
            "",
            "aoi_tile_discovery:",
        ]
    )
    discovery = prep.get("aoi_tile_discovery", {})
    lines.extend(
        [
            f"- schema_version: {discovery.get('schema_version', '')}",
            f"- discovery_status: {discovery.get('discovery_status', '')}",
            f"- catalog_path: {discovery.get('catalog_path', '')}",
            f"- tile_candidate_count: {discovery.get('tile_candidate_count', 0)}",
        ]
    )
    if discovery.get("tile_candidates"):
        lines.append("- tile_candidates:")
        for entry in discovery["tile_candidates"]:
            lines.append(f"  - {entry.get('tile_id', '')}: {entry.get('source_product', '')}")
    else:
        lines.append("- tile_candidates: none")
    if discovery.get("required_products"):
        lines.append("- required_products:")
        for entry in discovery["required_products"]:
            lines.append(
                f"  - {entry.get('category', '')}: {entry.get('coverage_descriptor', '')}, "
                f"staging_root={entry.get('expected_staging_root', '')}"
            )
    else:
        lines.append("- required_products: none")
    if discovery.get("missing_catalog_inputs"):
        lines.append("- missing_catalog_inputs:")
        lines.extend(f"  - {item}" for item in discovery["missing_catalog_inputs"])
    else:
        lines.append("- missing_catalog_inputs: none")
    lines.append("- no_download_boundary:")
    for key, value in (discovery.get("no_download_boundary") or {}).items():
        lines.append(f"  - {key}: {value}")
    lines.extend(
        [
            "",
            "candidate_source_zones:",
        ]
    )
    candidate_source_zones = prep.get("candidate_source_zones", {})
    lines.append(f"- candidate_metrics_status: {candidate_source_zones.get('candidate_metrics_status', '')}")
    lines.append(
        f"- candidate_release_zone_set_status: {candidate_source_zones.get('candidate_release_zone_set_status', '')}"
    )
    lines.append(
        f"- candidate_release_zone_interpretation: {candidate_source_zones.get('candidate_release_zone_interpretation', '')}"
    )
    if candidate_source_zones.get("blocked_reason"):
        lines.append(f"- blocked_reason: {candidate_source_zones.get('blocked_reason', '')}")
    if candidate_source_zones.get("blocked_missing_inputs"):
        lines.append("- blocked_missing_inputs:")
        lines.extend(f"  - {item}" for item in candidate_source_zones["blocked_missing_inputs"])
    lines.append("- candidate_summary:")
    for key, value in (candidate_source_zones.get("candidate_summary") or {}).items():
        lines.append(f"  - {key}: {value}")
    lines.append("- screening_criteria:")
    for key, value in (candidate_source_zones.get("screening_criteria") or {}).items():
        lines.append(f"  - {key}: {value}")
    lines.append("- terrain_inputs:")
    for key, value in (candidate_source_zones.get("terrain_inputs") or {}).items():
        lines.append(f"  - {key}: {value}")
    lines.append("- source_zone_inputs:")
    for key, value in (candidate_source_zones.get("source_zone_inputs") or {}).items():
        lines.append(f"  - {key}: {value}")
    lines.extend(
        [
            "",
            "scenario_generation_inputs:",
        ]
    )
    scenario_generation_inputs = prep.get("scenario_generation_inputs", {})
    lines.append(f"- scenario_plan_status: {scenario_generation_inputs.get('scenario_plan_status', '')}")
    lines.append("- source_policy_provenance:")
    for key, value in (scenario_generation_inputs.get("source_policy_provenance") or {}).items():
        lines.append(f"  - {key}: {value}")
    lines.append("- generic_candidate_source_zone_provenance:")
    for key, value in (scenario_generation_inputs.get("generic_candidate_source_zone_provenance") or {}).items():
        lines.append(f"  - {key}: {value}")
    lines.append("- generic_scenario_generation:")
    for key, value in (scenario_generation_inputs.get("generic_scenario_generation") or {}).items():
        lines.append(f"  - {key}: {value}")
    lines.append("- block_size_bins:")
    for row in scenario_generation_inputs.get("block_size_bins", []):
        lines.append(
            f"  - {row.get('block_scenario_id', '')}: {row.get('block_size_class', '')} / {row.get('sampling_weight', '')}"
        )
    lines.append("- weighting_semantics:")
    for key, value in (scenario_generation_inputs.get("weighting_semantics") or {}).items():
        lines.append(f"  - {key}: {value}")
    lines.append("- reference_scenario_table:")
    for key, value in (scenario_generation_inputs.get("reference_scenario_table") or {}).items():
        lines.append(f"  - {key}: {value}")
    lines.append("- scenario_plan_summary:")
    for key, value in (scenario_generation_inputs.get("scenario_plan_summary") or {}).items():
        lines.append(f"  - {key}: {value}")
    lines.append("- explicit_non_frequency_labels:")
    for value in scenario_generation_inputs.get("explicit_non_frequency_labels", []):
        lines.append(f"  - {value}")
    lines.append("- same_scale_reference:")
    for key, value in (scenario_generation_inputs.get("same_scale_reference") or {}).items():
        lines.append(f"  - {key}: {value}")
    lines.append("- claim_boundary:")
    for key, value in (scenario_generation_inputs.get("claim_boundary") or {}).items():
        lines.append(f"  - {key}: {value}")
    lines.append("- pragmatic_coverage_boundary:")
    for key, value in (scenario_generation_inputs.get("pragmatic_coverage_boundary") or {}).items():
        lines.append(f"  - {key}: {value}")
    lines.append("- source_inputs:")
    for key, value in (scenario_generation_inputs.get("source_inputs") or {}).items():
        lines.append(f"  - {key}: {value}")
    lines.append(f"- scenario_table_manifest_path: {scenario_generation_inputs.get('scenario_table_manifest_path', '')}")
    lines.append(f"- blocked_execution_status: {scenario_generation_inputs.get('blocked_execution_status', '')}")
    lines.append(f"- conditional_only_weighting: {scenario_generation_inputs.get('conditional_only_weighting', '')}")
    lines.extend(
        [
            "",
            "terrain_manifests:",
        ]
    )
    for row in report.get("terrain_manifests", []):
        lines.append(
            f"- {row.get('category', '')}: {row.get('expected_staged_path', '')} [{row.get('current_status', '')}]"
        )
    lines.extend(
        [
            "",
            "context_manifests:",
        ]
    )
    for row in report.get("context_manifests", []):
        lines.append(
            f"- {row.get('category', '')}: {row.get('expected_staged_path', '')} [{row.get('current_status', '')}]"
        )
    lines.extend(
        [
            "",
            "gis_scope_summary:",
        ]
    )
    gis_scope_summary = prep.get("gis_scope_summary", {})
    lines.append(f"- schema_version: {gis_scope_summary.get('schema_version', '')}")
    lines.append(f"- status: {gis_scope_summary.get('status', '')}")
    lines.append(f"- summary: {gis_scope_summary.get('summary', '')}")
    lines.append(f"- no_hazard_layers_generated: {gis_scope_summary.get('no_hazard_layers_generated', False)}")
    lines.append(f"- cog_export_expectation: {gis_scope_summary.get('cog_export_expectation', {})}")
    lines.append("- planned_raster_products:")
    if gis_scope_summary.get("planned_raster_products"):
        for row in gis_scope_summary["planned_raster_products"]:
            lines.append(
                f"  - {row.get('category', '')}: {row.get('product', '')} "
                f"[{row.get('current_status', '')} -> {row.get('scope_state', '')}]"
            )
    else:
        lines.append("  - none")
    lines.append("- planned_vector_products:")
    if gis_scope_summary.get("planned_vector_products"):
        for row in gis_scope_summary["planned_vector_products"]:
            lines.append(
                f"  - {row.get('category', '')}: {row.get('product', '')} "
                f"[{row.get('current_status', '')} -> {row.get('scope_state', '')}]"
            )
    else:
        lines.append("  - none")
    lines.append("- template_only_products:")
    if gis_scope_summary.get("template_only_products"):
        for row in gis_scope_summary["template_only_products"]:
            lines.append(
                f"  - {row.get('category', '')}: {row.get('product', '')} "
                f"[{row.get('scope_state', '')}]"
            )
    else:
        lines.append("  - none")
    if gis_scope_summary.get("blocked_missing_inputs"):
        lines.append("- blocked_missing_inputs:")
        lines.extend(f"  - {item}" for item in gis_scope_summary["blocked_missing_inputs"])
    else:
        lines.append("- blocked_missing_inputs: none")
    lines.append("- non_operational_gis_boundaries:")
    for key, value in (gis_scope_summary.get("non_operational_gis_boundaries") or {}).items():
        lines.append(f"  - {key}: {value}")
    lines.extend(
        [
            "",
            "release_scenario_placeholders:",
        ]
    )
    for key, value in report.get("release_scenario_placeholders", {}).items():
        lines.append(f"- {key}: {value}")
    lines.extend(
        [
            "",
            "command_plan_hooks:",
        ]
    )
    for row in report.get("command_plan_hooks", []):
        lines.append(f"- {row.get('command_id', '')}: {row.get('blocked_reason', '') or 'ready'}")
    lines.extend(
        [
            "",
            "ignored_output_roots:",
        ]
    )
    if report.get("ignored_output_roots"):
        lines.extend(f"- {item}" for item in report["ignored_output_roots"])
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "ignored_root_layout:",
        ]
    )
    if report.get("ignored_root_layout"):
        for key, value in report["ignored_root_layout"].items():
            lines.append(f"- {key}: {value}")
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "output_root_planning:",
        ]
    )
    for key, value in (prep.get("output_root_planning") or {}).items():
        lines.append(f"- {key}: {value}")
    lines.extend(
        [
            "",
            "prepared_pilot_compiler:",
        ]
    )
    compiler = report.get("prepared_pilot_compiler", {})
    lines.append(f"- schema_version: {compiler.get('schema_version', '')}")
    lines.append(f"- classification: {compiler.get('classification', '')}")
    lines.append(f"- run_manifest_path: {compiler.get('run_manifest_path', '')}")
    lines.append(f"- first_blocker: {compiler.get('first_blocker', {})}")
    lines.append("- command_plan:")
    for key, value in (compiler.get("command_plan") or {}).items():
        if key == "commands" and isinstance(value, list):
            lines.append(f"  - {key}: {len(value)} commands")
            continue
        lines.append(f"  - {key}: {value}")
    lines.append("- expected_io_inventory:")
    inventory = compiler.get("expected_io_inventory", {})
    lines.append(f"  - schema_version: {inventory.get('schema_version', '')}")
    lines.append(f"  - expected_step_count: {inventory.get('expected_step_count', 0)}")
    lines.append(f"  - command_manifest_path: {inventory.get('command_manifest_path', '')}")
    lines.append(f"  - run_manifest_path: {inventory.get('run_manifest_path', '')}")
    lines.append(f"  - case_skeleton_path: {inventory.get('case_skeleton_path', '')}")
    lines.append("- output_profile:")
    for key, value in (compiler.get("output_profile") or {}).items():
        if key == "gis_scope_summary" and isinstance(value, dict):
            lines.append("  - gis_scope_summary:")
            for subkey, subvalue in value.items():
                lines.append(f"    - {subkey}: {subvalue}")
            continue
        lines.append(f"  - {key}: {value}")
    lines.append("- execution_hints:")
    for key, value in (compiler.get("execution_hints") or {}).items():
        if isinstance(value, dict):
            lines.append(f"  - {key}:")
            for subkey, subvalue in value.items():
                if isinstance(subvalue, list):
                    lines.append(f"    - {subkey}:")
                    lines.extend(f"      - {item}" for item in subvalue)
                else:
                    lines.append(f"    - {subkey}: {subvalue}")
        else:
            lines.append(f"  - {key}: {value}")
    lines.extend(
        [
            "",
            "workflow_steps:",
        ]
    )
    for step in report["workflow_steps"]:
        lines.append(f"- {step['step_id']}: {step['status']} [{step['label']}]")
        if step["blocked_reason"]:
            lines.append(f"  blocked_reason: {step['blocked_reason']}")
        if step["expected_inputs"]:
            lines.append("  expected_inputs:")
            lines.extend(f"  - {item}" for item in step["expected_inputs"])
        if step["generated_output_roots"]:
            lines.append("  generated_output_roots:")
            lines.extend(f"  - {item}" for item in step["generated_output_roots"])
        if step["ignored_output_roots"]:
            lines.append("  ignored_output_roots:")
            lines.extend(f"  - {item}" for item in step["ignored_output_roots"])
    lines.append("")
    lines.append("workflow_generated_output_roots:")
    if report["workflow_generated_output_roots"]:
        lines.extend(f"- {item}" for item in report["workflow_generated_output_roots"])
    else:
        lines.append("- none")
    lines.append("")
    lines.append("workflow_ignored_output_roots:")
    if report["workflow_ignored_output_roots"]:
        lines.extend(f"- {item}" for item in report["workflow_ignored_output_roots"])
    else:
        lines.append("- none")
    lines.append("")
    lines.append("workflow_blockers:")
    if report["workflow_blockers"]:
        for blocker in report["workflow_blockers"]:
            lines.append(
                f"- {blocker['step_id']}: {blocker['status']} ({', '.join(str(item) for item in blocker['details']) if blocker['details'] else 'none'})"
            )
    else:
        lines.append("- none")
    lines.append("")
    lines.append("blocked_missing_inputs:")
    if report.get("blocked_missing_inputs"):
        lines.extend(f"- {item}" for item in report["blocked_missing_inputs"])
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "case_skeleton_output:",
        ]
    )
    skeleton = report.get("case_skeleton_output", {})
    lines.append(f"- status: {skeleton.get('status', 'not_requested')}")
    lines.append(f"- write_status: {skeleton.get('write_status', 'not_requested')}")
    lines.append(f"- blocked_execution_status: {skeleton.get('blocked_execution_status', 'blocked_missing_inputs')}")
    lines.append(f"- output_root: {skeleton.get('output_root', '')}")
    lines.append(f"- skeleton_path: {skeleton.get('case_skeleton_path', '')}")
    lines.append(f"- command_manifest_path: {skeleton.get('command_manifest_path', '')}")
    lines.append(f"- expected_output_roots_path: {skeleton.get('expected_output_roots_path', '')}")
    lines.append(f"- blocked_execution_path: {skeleton.get('blocked_execution_path', '')}")
    if skeleton.get("runnable_command_ids"):
        lines.append("- runnable_command_ids:")
        lines.extend(f"  - {item}" for item in skeleton["runnable_command_ids"])
    else:
        lines.append("- runnable_command_ids: none")
    if skeleton.get("template_only_command_ids"):
        lines.append("- template_only_command_ids:")
        lines.extend(f"  - {item}" for item in skeleton["template_only_command_ids"])
    else:
        lines.append("- template_only_command_ids: none")
    if skeleton.get("expected_output_roots"):
        lines.append("- expected_output_roots:")
        lines.extend(f"  - {item}" for item in skeleton["expected_output_roots"])
    else:
        lines.append("- expected_output_roots: none")
    scenario_handoff = (skeleton.get("case_skeleton", {}) or {}).get("scenario_generation_handoff", {})
    if scenario_handoff:
        lines.append("- scenario_generation_handoff:")
        for key, value in scenario_handoff.items():
            if isinstance(value, dict):
                lines.append(f"  - {key}:")
                for subkey, subvalue in value.items():
                    lines.append(f"    - {subkey}: {subvalue}")
            else:
                lines.append(f"  - {key}: {value}")
    return "\n".join(lines)


def command_execution_class(command: dict[str, Any]) -> str:
    return "template_only" if command.get("blocked_reason") else "runnable"


def blocked_execution_status(command_plan_report: dict[str, Any], workflow_status: str | None = None) -> str:
    if workflow_status == "blocked_missing_inputs":
        return "blocked_missing_inputs"
    return "blocked_template_only" if command_plan_report.get("blocked_template_commands") else "ready"


def resolve_output_root(repo_root: Path, output_root: Path | None) -> Path | None:
    if output_root is None:
        return None
    resolved = output_root if output_root.is_absolute() else repo_root / output_root
    if not is_allowed_output_root(resolved, repo_root):
        raise ValueError(f"output root must stay under /tmp or validation/private: {resolved}")
    return resolved


def is_allowed_output_root(output_root: Path, repo_root: Path) -> bool:
    resolved = output_root.resolve()
    allowed_roots = [Path("/tmp").resolve(), (repo_root / "validation/private").resolve()]
    return any(resolved.is_relative_to(root) for root in allowed_roots)


def build_case_skeleton_output(
    *,
    report_inputs: dict[str, Any],
    repo_root: Path,
    output_root: Path | None,
) -> dict[str, Any]:
    prep_summary = report_inputs["prep_summary"]
    resolved_output_root = resolve_output_root(repo_root, output_root)
    blocked_execution = blocked_execution_status(
        report_inputs["command_plan_report"],
        workflow_status=report_inputs["workflow_status"],
    )
    resolved_output_root_entries = [str(resolved_output_root)] if resolved_output_root is not None else []
    expected_output_roots = dedupe(
        [
            *resolved_output_root_entries,
            prep_summary["output_root_planning"]["prepared_validation_root"],
            prep_summary["output_root_planning"]["prepared_hazard_root"],
            *prep_summary["ignored_output_roots"],
            *prep_summary["output_root_planning"]["command_plan_ignored_output_roots"],
        ]
    )
    runnable_command_ids = [
        command["command_id"]
        for command in prep_summary["command_plan_hooks"]
        if command["execution_class"] == "runnable"
    ]
    template_only_command_ids = [
        command["command_id"]
        for command in prep_summary["command_plan_hooks"]
        if command["execution_class"] == "template_only"
    ]
    skeleton_status = "blocked_missing_inputs" if report_inputs["workflow_status"] == "blocked_missing_inputs" else "ready"
    case_skeleton = {
        "schema_version": CASE_SKELETON_SCHEMA_VERSION,
        "case_skeleton_status": skeleton_status,
        "blocked_execution_status": blocked_execution,
        "candidate_site_id": report_inputs["acquisition_report"]["candidate_site_id"],
        "candidate_site_name": report_inputs["acquisition_report"]["candidate_site_name"],
        "input_mode": prep_summary["input_mode"],
        "site_extent": prep_summary["site_extent"],
        "release_polygon": prep_summary["release_polygon"],
        "gis_scope_summary": prep_summary.get("gis_scope_summary", {}),
        "blocked_reason": (
            "workflow blocked_missing_inputs; required inputs are missing"
            if report_inputs["workflow_status"] == "blocked_missing_inputs"
            else "dry-run only; ensemble execution is not authorized"
        ),
        "command_sequence": [
            {
                "step_id": step["step_id"],
                "label": step["label"],
                "status": step["status"],
                "blocked_reason": step["blocked_reason"],
                "expected_inputs": step["expected_inputs"],
                "generated_output_roots": step["generated_output_roots"],
                "ignored_output_roots": step["ignored_output_roots"],
            }
            for step in report_inputs["workflow_steps"]
        ],
        "expected_output_roots": expected_output_roots,
        "runnable_command_ids": runnable_command_ids,
        "template_only_command_ids": template_only_command_ids,
        "output_root": str(resolved_output_root) if resolved_output_root is not None else "",
        "write_status": "not_requested" if resolved_output_root is None else "pending",
        "scenario_generation_handoff": {
            "command_id": report_inputs["generic_release_plan_report"].get("scenario_generation_contract", {})
            .get("generic_scenario_generation", {})
            .get("command_id", ""),
            "command": report_inputs["generic_release_plan_report"].get("scenario_generation_contract", {})
            .get("generic_scenario_generation", {})
            .get("command", ""),
            "expected_scenario_table_path": report_inputs["generic_release_plan_report"].get("scenario_generation_contract", {})
            .get("generic_scenario_generation", {})
            .get("expected_scenario_table_path", ""),
            "scenario_table_manifest_path": report_inputs["generic_release_plan_report"].get("scenario_generation_contract", {})
            .get("generic_scenario_generation", {})
            .get("scenario_table_manifest_path", ""),
            "blocked_execution_status": report_inputs["generic_release_plan_report"].get("scenario_generation_contract", {})
            .get("generic_scenario_generation", {})
            .get("blocked_execution_status", blocked_execution),
            "conditional_only_weighting": report_inputs["generic_release_plan_report"].get("scenario_generation_contract", {})
            .get("generic_scenario_generation", {})
            .get("conditional_only_weighting", True),
            "generic_candidate_source_zone_provenance": report_inputs["generic_release_plan_report"].get("scenario_generation_contract", {})
            .get("generic_candidate_source_zone_provenance", {}),
        },
    }
    command_manifest = {
        "schema_version": COMMAND_MANIFEST_SCHEMA_VERSION,
        "candidate_site_id": report_inputs["acquisition_report"]["candidate_site_id"],
        "candidate_site_name": report_inputs["acquisition_report"]["candidate_site_name"],
        "command_plan_status": report_inputs["command_plan_report"]["command_plan_status"],
        "blocked_execution_status": blocked_execution,
        "blocked_template_commands": report_inputs["command_plan_report"].get("blocked_template_commands", []),
        "command_groups": report_inputs["command_plan_report"].get("command_groups", []),
        "commands": report_inputs["command_plan_report"].get("commands", []),
        "command_ids": report_inputs["command_plan_report"].get("command_ids", []),
        "command_descriptions": report_inputs["command_plan_report"].get("command_descriptions", {}),
        "ignored_output_paths": report_inputs["command_plan_report"].get("ignored_output_paths", []),
        "output_profile_validation": report_inputs["command_plan_report"].get("output_profile_validation", {}),
        "runnable_command_ids": runnable_command_ids,
        "template_only_command_ids": template_only_command_ids,
    }
    blocked_execution_report = {
        "schema_version": BLOCKED_EXECUTION_SCHEMA_VERSION,
        "case_skeleton_status": skeleton_status,
        "blocked_execution_status": blocked_execution,
        "blocked_reason": (
            "workflow blocked_missing_inputs; required inputs are missing"
            if report_inputs["workflow_status"] == "blocked_missing_inputs"
            else "dry-run only; ensemble execution is not authorized"
        ),
        "missing_input_paths": dedupe(
            [
                *(str(item) for item in report_inputs["prep_summary"].get("blocked_missing_inputs", []) if item),
                *(str(item) for item in report_inputs["prep_summary"].get("candidate_source_zones", {}).get("blocked_missing_inputs", []) if item),
            ]
        ),
        "blocked_command_ids": report_inputs["command_plan_report"].get("blocked_template_commands", []),
    }
    skeleton = {
        **case_skeleton,
        "command_manifest": command_manifest,
        "blocked_execution": blocked_execution_report,
    }
    run_manifest_path = str(
        (resolved_output_root / "aoi_to_prepared_pilot_run_manifest.yaml") if resolved_output_root is not None else ""
    )
    skeleton_output = {
        "status": skeleton_status,
        "write_status": "written" if resolved_output_root is not None else "not_requested",
        "blocked_execution_status": blocked_execution,
        "blocked_reason": blocked_execution_report["blocked_reason"],
        "output_root": str(resolved_output_root) if resolved_output_root is not None else "",
        "case_skeleton_path": str(
            (resolved_output_root / "aoi_to_prepared_pilot_case_skeleton.yaml") if resolved_output_root is not None else ""
        ),
        "command_manifest_path": str(
            (resolved_output_root / "aoi_to_prepared_pilot_command_manifest.json") if resolved_output_root is not None else ""
        ),
        "expected_output_roots_path": str(
            (resolved_output_root / "aoi_to_prepared_pilot_expected_output_roots.yaml") if resolved_output_root is not None else ""
        ),
        "blocked_execution_path": str(
            (resolved_output_root / "aoi_to_prepared_pilot_blocked_execution.json") if resolved_output_root is not None else ""
        ),
        "run_manifest_path": run_manifest_path,
        "expected_inputs_by_step": {step["step_id"]: step["expected_inputs"] for step in report_inputs["workflow_steps"]},
        "generated_output_roots_by_step": {
            step["step_id"]: step["generated_output_roots"] for step in report_inputs["workflow_steps"]
        },
        "ignored_output_roots_by_step": {
            step["step_id"]: step["ignored_output_roots"] for step in report_inputs["workflow_steps"]
        },
        "expected_output_roots": expected_output_roots,
        "runnable_command_ids": runnable_command_ids,
        "template_only_command_ids": template_only_command_ids,
        "case_skeleton": skeleton,
    }
    skeleton_output["run_manifest"] = build_run_manifest(
        report_inputs=report_inputs,
        skeleton_output=skeleton_output,
        classification=classify_prepared_pilot_compiler({
            **report_inputs,
            "workflow_status": report_inputs["workflow_status"],
            "command_plan_report": report_inputs["command_plan_report"],
        }),
        first_blocker=first_compiler_blocker({
            **report_inputs,
            "workflow_status": report_inputs["workflow_status"],
            "command_plan_report": report_inputs["command_plan_report"],
        }),
    )
    return skeleton_output


def write_case_skeleton_bundle(skeleton_output: dict[str, Any]) -> None:
    output_root = skeleton_output.get("output_root")
    if not output_root:
        return
    Path(output_root).mkdir(parents=True, exist_ok=True)
    case_skeleton = copy.deepcopy(skeleton_output["case_skeleton"])
    case_skeleton["write_status"] = "written"
    dump_yaml(Path(skeleton_output["case_skeleton_path"]), case_skeleton)
    dump_json(Path(skeleton_output["command_manifest_path"]), skeleton_output["case_skeleton"]["command_manifest"])
    dump_yaml(Path(skeleton_output["run_manifest_path"]), skeleton_output["run_manifest"])
    dump_yaml(
        Path(skeleton_output["expected_output_roots_path"]),
        {
            "schema_version": EXPECTED_OUTPUT_ROOTS_SCHEMA_VERSION,
            "expected_output_roots": skeleton_output["expected_output_roots"],
        },
    )
    dump_json(Path(skeleton_output["blocked_execution_path"]), skeleton_output["case_skeleton"]["blocked_execution"])


if __name__ == "__main__":
    raise SystemExit(main())
