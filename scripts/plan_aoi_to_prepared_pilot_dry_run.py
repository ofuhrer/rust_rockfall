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
    raise SystemExit("PyYAML is required; install with `python3 -m pip install PyYAML`") from exc


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "aoi_to_prepared_pilot_dry_run_v1"
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
COMMAND_PLAN = _load_module("aoi_to_prepared_pilot_command_plan", "generate_pilot_command_plan.py")


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def dump_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


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
    release_plan_report: dict[str, Any],
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
    release_plan_paths = release_plan_report.get("source_inputs", {})
    release_scenario_placeholders = {
        "source_scenario_policy_path": release_plan_paths.get("source_scenario_policy_path", ""),
        "scenario_table_path": release_plan_paths.get("scenario_table_path", ""),
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
        "block_size_bins": release_plan_report.get("block_size_bins", []),
        "weighting_semantics": release_plan_report.get("weighting_semantics", {}),
        "reference_scenario_table": release_plan_report.get("reference_scenario_table", {}),
        "scenario_plan_summary": release_plan_report.get("scenario_plan_summary", {}),
        "explicit_non_frequency_labels": release_plan_report.get("explicit_non_frequency_labels", []),
        "same_scale_reference": release_plan_report.get("same_scale_reference", {}),
        "claim_boundary": release_plan_report.get("claim_boundary", {}),
        "pragmatic_coverage_boundary": release_plan_report.get("pragmatic_coverage_boundary", {}),
        "source_inputs": release_plan_report.get("source_inputs", {}),
    }
    command_plan_hooks = [
        {
            "command_id": command["id"],
            "description": command["description"],
            "command": command["command"],
            "blocked_reason": command.get("blocked_reason", ""),
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
        "aoi_tile_discovery": acquisition_report.get("aoi_tile_discovery", {}),
        "candidate_source_zones": candidate_source_zones,
        "scenario_generation_inputs": scenario_generation_inputs,
        "terrain_manifests": terrain_manifests,
        "context_manifests": context_manifests,
        "release_scenario_placeholders": release_scenario_placeholders,
        "command_plan_hooks": command_plan_hooks,
        "ignored_output_roots": ignored_output_roots,
        "output_root_planning": {
            "prepared_validation_root": f"validation/private/{acquisition_report.get('candidate_site_id', '')}",
            "prepared_hazard_root": f"hazard/results/{acquisition_report.get('candidate_site_id', '')}",
            "ignored_output_roots": ignored_output_roots,
            "command_plan_ignored_output_roots": command_plan_report.get("ignored_output_paths", []),
            "blocked_command_ids": command_plan_report.get("blocked_template_commands", []),
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
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    args = parser.parse_args(argv)

    report = build_report(args.site_config, repo_root=args.repo_root, release_polygon_path=args.release_polygon)

    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    output = json.dumps(report, indent=2, sort_keys=True) if args.format == "json" else render_text_report(report)
    print(output)
    return 0 if report["workflow_status"] == "ready" else 2


def build_report(
    site_config: Path | None,
    repo_root: Path | None = None,
    release_polygon_path: Path | None = None,
) -> dict[str, Any]:
    repo_root = repo_root or ROOT
    config_path, config, release_polygon, synthetic_config, has_site_config = prepare_working_config(
        site_config, repo_root, release_polygon_path
    )

    with _patched_repo_root(repo_root):
        acquisition_report = AOI_ACQUISITION.build_report(config_path)
        candidate_generation_report = CANDIDATE_GENERATION.build_report(repo_root=repo_root)
        release_plan_report = SCENARIO_PLAN.build_report()

    command_plan_report = COMMAND_PLAN.build_report(DEFAULT_COMMAND_PLAN_SITE, config_path)

    steps = build_steps(
        acquisition_report=acquisition_report,
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
        release_plan_report=release_plan_report,
        candidate_generation_report=candidate_generation_report,
        command_plan_report=command_plan_report,
    )

    report = {
        "schema_version": SCHEMA_VERSION,
        "workflow_status": workflow_status,
        "preparation_status": workflow_status,
        "candidate_site_id": acquisition_report["candidate_site_id"],
        "candidate_site_name": acquisition_report["candidate_site_name"],
        "candidate_selection_rationale": acquisition_report["candidate_selection_rationale"],
        "site_extent": acquisition_report["site_extent"],
        "preparation_input": prep_summary,
        "terrain_manifests": prep_summary["terrain_manifests"],
        "context_manifests": prep_summary["context_manifests"],
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
    }
    return report


def build_steps(
    *,
    acquisition_report: dict[str, Any],
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
            "blocked_reason": "",
            "expected_inputs": expected_inputs_from_scenario_generation(release_plan_report),
            "generated_output_roots": [],
            "ignored_output_roots": [],
            "blockers": build_step_blockers(
                "release_plan_dry_run",
                release_plan_report["scenario_plan_status"],
                [],
                [],
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
            "output_root_planning:",
        ]
    )
    for key, value in (prep.get("output_root_planning") or {}).items():
        lines.append(f"- {key}: {value}")
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
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
