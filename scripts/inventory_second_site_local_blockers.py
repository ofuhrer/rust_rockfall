#!/usr/bin/env python3
"""Inventory local blockers for the Chant Sura / Fluelapass second-site path.

The helper is read-only. It groups the existing public-geodata preflight inputs
into local unblock surfaces and names the next local command for each group. It
does not download data, submit Balfrin jobs, run ensembles, or make physical,
annual-frequency, operational, risk, or scale-up claims.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except ImportError as exc:  # pragma: no cover - environment setup.
    raise SystemExit("PyYAML is required. Run this script with `.venv/bin/python ...` or `uv run python ...`") from exc


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import check_second_site_public_geodata_preflight as preflight


SCHEMA_VERSION = "second_site_local_blocker_inventory_v1"
DEFAULT_SITE_CONFIG = ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml"

GROUP_CATEGORIES = {
    "terrain_inputs": ("terrain_crop", "terrain_crs_vertical_datum", "aoi_tile_catalog"),
    "source_zone_inputs": ("source_zone_metadata",),
    "scenario_inputs": ("scenario_table", "source_scenario_policy"),
    "public_context_inputs": (
        "swissimage_context",
        "swisstlm3d_context",
        "swisssurface3d_context",
        "swisssurface3d_raster_context",
        "swissbuildings3d_context",
    ),
    "prepared_pilot_inputs": ("validation_case_root", "hazard_results_root", "processed_input_root", "processed_context_root"),
}
LOCAL_PREPARED_PILOT_GROUPS = {"terrain_inputs", "source_zone_inputs", "scenario_inputs"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site-config", type=Path, default=DEFAULT_SITE_CONFIG)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    args = parser.parse_args(argv)

    report = build_report(args.site_config)
    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text_report(report))
    return 0


def build_report(site_config: Path = DEFAULT_SITE_CONFIG) -> dict[str, Any]:
    preflight_report = preflight.build_report(site_config)
    site_config_data = load_yaml(site_config)
    requirements = {
        str(item.get("category")): item
        for item in preflight_report.get("site_specific_required_inputs", [])
        if isinstance(item, dict) and item.get("category")
    }
    acquisition_summaries = {
        str(item.get("category")): item
        for item in preflight_report.get("acquisition_manifest_product_summaries", [])
        if isinstance(item, dict) and item.get("category")
    }

    blocker_groups = [
        build_group(
            group_id=group_id,
            categories=categories,
            requirements=requirements,
            acquisition_summaries=acquisition_summaries,
            site_config=site_config,
            site_config_data=site_config_data,
        )
        for group_id, categories in GROUP_CATEGORIES.items()
    ]
    prepared_group = next(group for group in blocker_groups if group["group_id"] == "prepared_pilot_inputs")
    prepared_group["status"] = prepared_pilot_status(blocker_groups)
    prepared_group["blockers"] = prepared_pilot_blockers(blocker_groups)
    prepared_group["next_local_command"] = prepared_pilot_next_command(site_config, blocker_groups)

    local_blocking_groups = [
        group for group in blocker_groups if group["group_id"] in LOCAL_PREPARED_PILOT_GROUPS and group["status"] != "ready"
    ]
    external_blocking_groups = [
        group for group in blocker_groups if group["group_id"] == "public_context_inputs" and group["status"] != "ready"
    ]
    blocking_groups = local_blocking_groups + external_blocking_groups
    first_blocking_group = blocking_groups[0]["group_id"] if blocking_groups else ""
    inventory_status = "ready"
    if local_blocking_groups:
        inventory_status = "blocked_local_inputs"
    elif external_blocking_groups:
        inventory_status = "ready_with_deferred_public_context"
    return {
        "schema_version": SCHEMA_VERSION,
        "inventory_status": inventory_status,
        "candidate_site_id": preflight_report.get("candidate_site_id", ""),
        "candidate_site_name": preflight_report.get("candidate_site_name", ""),
        "preflight_status": preflight_report.get("portability_preflight_status", ""),
        "core_input_status": preflight_report.get("core_input_status", ""),
        "deferred_public_context_status": preflight_report.get("deferred_public_context_status", ""),
        "first_blocking_group": first_blocking_group,
        "first_external_data_blocker": external_blocking_groups[0]["group_id"] if external_blocking_groups else "",
        "blocker_groups": blocker_groups,
        "claim_boundaries": {
            "downloads_authorized": False,
            "balfrin_required": False,
            "live_balfrin_submission_authorized": False,
            "annual_frequency_claims_allowed": False,
            "operational_claims_allowed": False,
            "physical_probability_claims_allowed": False,
            "risk_exposure_vulnerability_claims_allowed": False,
            "scale_up_authorized": False,
        },
        "next_local_unblock_command": (
            local_blocking_groups[0]["next_local_command"]
            if local_blocking_groups
            else prepared_pilot_next_command(site_config, blocker_groups)
        ),
        "next_external_acquisition_command": (
            external_blocking_groups[0]["next_local_command"] if external_blocking_groups else ""
        ),
    }


def build_group(
    *,
    group_id: str,
    categories: tuple[str, ...],
    requirements: dict[str, dict[str, Any]],
    acquisition_summaries: dict[str, dict[str, Any]],
    site_config: Path,
    site_config_data: dict[str, Any],
) -> dict[str, Any]:
    items = [input_item(category, requirements, acquisition_summaries) for category in categories]
    blockers = [item for item in items if item["status"] != "ready"]
    if group_id == "terrain_inputs" and not blockers:
        terrain_qa = terrain_domain_qa_status(site_config_data, requirements)
        if terrain_qa["status"] != "ready":
            blockers.append(terrain_qa)
        aoi_tile_qa = aoi_tile_catalog_qa_status(site_config_data, requirements)
        if aoi_tile_qa["status"] != "ready":
            blockers.append(aoi_tile_qa)
    if group_id == "source_zone_inputs" and not blockers:
        source_zone_qa = source_zone_domain_qa_status(site_config_data, requirements)
        if source_zone_qa["status"] != "ready":
            blockers.append(source_zone_qa)
    status = "ready" if not blockers else blockers[0]["status"]
    return {
        "group_id": group_id,
        "status": status,
        "required_categories": list(categories),
        "input_items": items,
        "blockers": blockers,
        "next_local_command": group_next_command(group_id, site_config, blockers),
    }


def input_item(
    category: str,
    requirements: dict[str, dict[str, Any]],
    acquisition_summaries: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    requirement = requirements.get(category, {})
    acquisition = acquisition_summaries.get(category, {})
    expected_path = str(requirement.get("path_or_pattern") or acquisition.get("expected_staged_path") or "")
    status = str(requirement.get("status") or acquisition.get("status") or "blocked_missing_inputs")
    if status == "deferred_public_context":
        status = "blocked_deferred_public_context"
    return {
        "category": category,
        "status": status,
        "expected_path": expected_path,
        "product": requirement.get("product") or acquisition.get("product") or "",
        "notes": requirement.get("notes") or "",
    }


def terrain_domain_qa_status(site_config_data: dict[str, Any], requirements: dict[str, dict[str, Any]]) -> dict[str, Any]:
    terrain_metadata_path = Path(str(requirements.get("terrain_crs_vertical_datum", {}).get("path_or_pattern") or ""))
    if not terrain_metadata_path.exists():
        return {
            "category": "terrain_domain_qa",
            "status": "blocked_missing_inputs",
            "expected_path": str(terrain_metadata_path),
            "blocked_reason": "terrain metadata is missing",
        }
    metadata = load_yaml(terrain_metadata_path)
    site_extent = site_config_data.get("site_extent") if isinstance(site_config_data.get("site_extent"), dict) else {}
    terrain_extent = (
        metadata.get("crop_extent_lv95_m")
        if isinstance(metadata.get("crop_extent_lv95_m"), dict)
        else metadata.get("extent_lv95_m")
        if isinstance(metadata.get("extent_lv95_m"), dict)
        else {}
    )
    if not site_extent or not terrain_extent:
        return {
            "category": "terrain_domain_qa",
            "status": "blocked_terrain_qa",
            "expected_path": str(terrain_metadata_path),
            "blocked_reason": "site or terrain extent metadata is incomplete",
        }
    if contains_extent(terrain_extent, site_extent):
        return {
            "category": "terrain_domain_qa",
            "status": "ready",
            "expected_path": str(terrain_metadata_path),
            "blocked_reason": "",
        }
    return {
        "category": "terrain_domain_qa",
        "status": "blocked_terrain_qa",
        "expected_path": str(terrain_metadata_path),
        "blocked_reason": "configured_site_extent_exceeds_terrain_crop",
        "next_local_action": "restage the terrain crop so it fully contains the configured site extent",
        "site_extent_lv95_m": site_extent,
        "terrain_extent_lv95_m": terrain_extent,
    }


def aoi_tile_catalog_qa_status(site_config_data: dict[str, Any], requirements: dict[str, dict[str, Any]]) -> dict[str, Any]:
    tile_catalog_path = Path(str(requirements.get("aoi_tile_catalog", {}).get("path_or_pattern") or ""))
    if not tile_catalog_path.exists():
        return {
            "category": "aoi_tile_catalog_qa",
            "status": "blocked_missing_inputs",
            "expected_path": str(tile_catalog_path),
            "blocked_reason": "aoi tile catalog is missing",
            "next_local_action": "stage or regenerate the AOI tile catalog before terrain preprocessing",
        }
    site_extent = site_config_data.get("site_extent") if isinstance(site_config_data.get("site_extent"), dict) else {}
    catalog = load_yaml(tile_catalog_path)
    tile_extents = [
        tile.get("extent_lv95_m")
        for tile in catalog.get("tiles", [])
        if isinstance(tile, dict) and isinstance(tile.get("extent_lv95_m"), dict)
    ]
    if not site_extent or not tile_extents:
        return {
            "category": "aoi_tile_catalog_qa",
            "status": "blocked_aoi_tile_qa",
            "expected_path": str(tile_catalog_path),
            "blocked_reason": "site extent or AOI tile extents are incomplete",
            "next_local_action": "regenerate the AOI tile catalog with LV95 tile extents",
        }
    if any(contains_extent(tile_extent, site_extent) for tile_extent in tile_extents):
        return {
            "category": "aoi_tile_catalog_qa",
            "status": "ready",
            "expected_path": str(tile_catalog_path),
            "blocked_reason": "",
        }
    return {
        "category": "aoi_tile_catalog_qa",
        "status": "blocked_aoi_tile_qa",
        "expected_path": str(tile_catalog_path),
        "blocked_reason": "configured_site_extent_exceeds_aoi_tile_catalog",
        "next_local_action": "update the AOI tile catalog or site extent before terrain preprocessing",
        "site_extent_lv95_m": site_extent,
        "tile_extent_count": len(tile_extents),
    }


def source_zone_domain_qa_status(site_config_data: dict[str, Any], requirements: dict[str, dict[str, Any]]) -> dict[str, Any]:
    source_zone_path = Path(str(requirements.get("source_zone_metadata", {}).get("path_or_pattern") or ""))
    if not source_zone_path.exists():
        return {
            "category": "source_zone_domain_qa",
            "status": "blocked_missing_inputs",
            "expected_path": str(source_zone_path),
            "blocked_reason": "source-zone metadata is missing",
            "next_local_action": "stage source-zone metadata before candidate review",
        }
    metadata = load_yaml(source_zone_path)
    site_extent = site_config_data.get("site_extent") if isinstance(site_config_data.get("site_extent"), dict) else {}
    vertices = source_zone_vertices(metadata)
    release_points = source_zone_release_points(metadata)
    if not site_extent or (not vertices and not release_points):
        return {
            "category": "source_zone_domain_qa",
            "status": "blocked_source_zone_domain_qa",
            "expected_path": str(source_zone_path),
            "blocked_reason": "site extent or source-zone coordinates are incomplete",
            "next_local_action": "add LV95 source-zone vertices or release points before candidate review",
        }
    outside_vertices = [point for point in vertices if not point_in_extent(point, site_extent)]
    outside_release_points = [point for point in release_points if not point_in_extent(point, site_extent)]
    if not outside_vertices and not outside_release_points:
        return {
            "category": "source_zone_domain_qa",
            "status": "ready",
            "expected_path": str(source_zone_path),
            "blocked_reason": "",
        }
    return {
        "category": "source_zone_domain_qa",
        "status": "blocked_source_zone_domain_qa",
        "expected_path": str(source_zone_path),
        "blocked_reason": "source_zone_coordinates_outside_configured_site_extent",
        "next_local_action": "correct the source-zone metadata or expand the configured site extent before candidate review",
        "outside_vertex_count": len(outside_vertices),
        "outside_release_point_count": len(outside_release_points),
    }


def source_zone_vertices(metadata: dict[str, Any]) -> list[tuple[float, float]]:
    geometry = metadata.get("geometry") if isinstance(metadata.get("geometry"), dict) else {}
    raw_vertices = geometry.get("vertices") or geometry.get("coordinates") or []
    vertices: list[tuple[float, float]] = []
    for raw in raw_vertices:
        if isinstance(raw, list) and raw and isinstance(raw[0], list):
            for nested in raw:
                point = xy_pair(nested)
                if point is not None:
                    vertices.append(point)
        else:
            point = xy_pair(raw)
            if point is not None:
                vertices.append(point)
    return vertices


def source_zone_release_points(metadata: dict[str, Any]) -> list[tuple[float, float]]:
    points = []
    for raw in metadata.get("release_points", []) or []:
        if isinstance(raw, dict):
            point = xy_pair([raw.get("x"), raw.get("y")])
            if point is not None:
                points.append(point)
    return points


def xy_pair(raw: Any) -> tuple[float, float] | None:
    if not isinstance(raw, (list, tuple)) or len(raw) < 2:
        return None
    try:
        return (float(raw[0]), float(raw[1]))
    except (TypeError, ValueError):
        return None


def point_in_extent(point: tuple[float, float], extent: dict[str, Any]) -> bool:
    try:
        x, y = point
        return (
            float(extent["xmin"]) <= x <= float(extent["xmax"])
            and float(extent["ymin"]) <= y <= float(extent["ymax"])
        )
    except (KeyError, TypeError, ValueError):
        return False


def contains_extent(container: dict[str, Any], inner: dict[str, Any]) -> bool:
    try:
        return (
            float(container["xmin"]) <= float(inner["xmin"])
            and float(container["ymin"]) <= float(inner["ymin"])
            and float(container["xmax"]) >= float(inner["xmax"])
            and float(container["ymax"]) >= float(inner["ymax"])
        )
    except (KeyError, TypeError, ValueError):
        return False


def group_next_command(group_id: str, site_config: Path, blockers: list[dict[str, Any]]) -> str:
    site_config_arg = str(site_config)
    if group_id == "terrain_inputs":
        return (
            "PYENV_VERSION=system uv run python scripts/plan_aoi_terrain_preprocessing.py "
            f"--repo-root . --site-config {site_config_arg} --format json"
        )
    if group_id == "source_zone_inputs":
        return f"PYENV_VERSION=system uv run python scripts/run_aoi_hazard_workflow.py candidate-review --site-config {site_config_arg} --format json"
    if group_id == "scenario_inputs":
        return f"PYENV_VERSION=system uv run python scripts/run_aoi_hazard_workflow.py prepare --site-config {site_config_arg} --repo-root . --format json"
    if group_id == "public_context_inputs":
        return f"PYENV_VERSION=system uv run python scripts/plan_swisstopo_aoi_acquisition.py --site-config {site_config_arg} --format text"
    if blockers:
        return f"PYENV_VERSION=system uv run python scripts/run_aoi_hazard_workflow.py prepare --site-config {site_config_arg} --repo-root . --format json"
    return f"PYENV_VERSION=system uv run python scripts/run_aoi_hazard_workflow.py workflow --site-config {site_config_arg} --format text"


def prepared_pilot_status(blocker_groups: list[dict[str, Any]]) -> str:
    blocking = [
        group
        for group in blocker_groups
        if group["group_id"] in LOCAL_PREPARED_PILOT_GROUPS and group["status"] != "ready"
    ]
    if blocking:
        return "blocked_by_local_inputs"
    public_context = next((group for group in blocker_groups if group["group_id"] == "public_context_inputs"), None)
    if public_context and public_context["status"] != "ready":
        return "ready_with_deferred_public_context"
    return "ready"


def prepared_pilot_blockers(blocker_groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    blockers = []
    for group in blocker_groups:
        if group["group_id"] in LOCAL_PREPARED_PILOT_GROUPS and group["status"] != "ready":
            blockers.append(
                {
                    "category": group["group_id"],
                    "status": group["status"],
                    "blocked_reason": (group.get("blockers") or [{}])[0].get("blocked_reason", group["status"]),
                    "next_local_command": group["next_local_command"],
                }
            )
    return blockers


def prepared_pilot_next_command(site_config: Path, blocker_groups: list[dict[str, Any]]) -> str:
    for group in blocker_groups:
        if group["group_id"] in LOCAL_PREPARED_PILOT_GROUPS and group["status"] != "ready":
            return group["next_local_command"]
    return f"PYENV_VERSION=system uv run python scripts/run_aoi_hazard_workflow.py prepare --site-config {site_config} --repo-root . --format json"


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def render_text_report(report: dict[str, Any]) -> str:
    lines = [
        f"schema_version: {report['schema_version']}",
        f"inventory_status: {report['inventory_status']}",
        f"candidate_site_id: {report['candidate_site_id']}",
        f"preflight_status: {report['preflight_status']}",
        f"first_blocking_group: {report['first_blocking_group']}",
        f"first_external_data_blocker: {report['first_external_data_blocker']}",
        "claim_boundaries:",
    ]
    for key, value in report["claim_boundaries"].items():
        lines.append(f"  {key}: {value}")
    lines.append("blocker_groups:")
    for group in report["blocker_groups"]:
        lines.append(f"  - {group['group_id']}: {group['status']}")
        for blocker in group["blockers"]:
            reason = blocker.get("blocked_reason") or blocker.get("status", "")
            lines.append(f"    blocker: {blocker.get('category', '')} ({reason})")
            if blocker.get("next_local_action"):
                lines.append(f"      next_local_action: {blocker['next_local_action']}")
        lines.append(f"    next_local_command: {group['next_local_command']}")
    lines.append(f"next_local_unblock_command: {report['next_local_unblock_command']}")
    lines.append(f"next_external_acquisition_command: {report['next_external_acquisition_command']}")
    return "\n".join(lines)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
