#!/usr/bin/env python3
"""Stage the smallest synthetic Chant Sura / Fluelapass preflight inputs.

This helper copies tiny intentional fixtures into the ignored Chant Sura paths
used by the second-site public-geodata preflight. It stages only the core
terrain, AOI tile catalog, source-zone, scenario, and policy records plus the
ignored roots that the preflight checks for existence. It does not download
public geodata and it does not create any of the public context products that
remain intentionally deferred.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import sys
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except ImportError as exc:  # pragma: no cover - environment setup.
    raise SystemExit("PyYAML is required; install with `python3 -m pip install PyYAML`") from exc


ROOT = Path(__file__).resolve().parents[1]
PREFLIGHT_SCRIPT = ROOT / "scripts" / "check_second_site_public_geodata_preflight.py"
DEFAULT_SITE_CONFIG = ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_candidate.yaml"
DEFAULT_FIXTURE_ROOT = ROOT / "tests/fixtures/second_site_public_geodata_preflight/chant_sura_fluelapass_minimal_staging"


def _load_preflight_module():
    spec = importlib.util.spec_from_file_location("chant_sura_preflight_helper", PREFLIGHT_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load preflight helper from {PREFLIGHT_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


PREFLIGHT = _load_preflight_module()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT, help="repository root to stage into")
    parser.add_argument("--site-config", type=Path, default=DEFAULT_SITE_CONFIG, help="second-site config YAML")
    parser.add_argument("--fixture-root", type=Path, default=DEFAULT_FIXTURE_ROOT, help="tiny synthetic fixture source tree")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    args = parser.parse_args(argv)

    report = stage_minimal_inputs(
        repo_root=resolve_path(args.repo_root),
        site_config=resolve_path(args.site_config),
        fixture_root=resolve_path(args.fixture_root),
    )

    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    output = json.dumps(report, indent=2, sort_keys=True) if args.format == "json" else render_text_report(report)
    print(output)
    return 0


def stage_minimal_inputs(*, repo_root: Path, site_config: Path, fixture_root: Path) -> dict[str, Any]:
    if not site_config.exists():
        raise SystemExit(f"missing site config: {site_config}")
    if not fixture_root.exists():
        raise SystemExit(f"missing fixture root: {fixture_root}")

    original_root = PREFLIGHT.ROOT
    candidate_site_id = ""
    config: dict[str, Any] = {}
    paths: dict[str, Path] = {}
    created_dirs: list[Path] = []
    staged_files: list[Path] = []
    try:
        PREFLIGHT.ROOT = repo_root
        config = PREFLIGHT.load_site_config(site_config)
        candidate_site_id = PREFLIGHT.text_value(config.get("candidate_site_id"))
        if not candidate_site_id:
            raise SystemExit(f"candidate_site_id is missing from {site_config}")

        paths = PREFLIGHT.build_paths(candidate_site_id, config)
        created_dirs = ensure_directories(paths)
        staged_files = stage_fixture_files(paths, fixture_root)
    finally:
        PREFLIGHT.ROOT = original_root

    report = {
        "schema_version": "chant_sura_fluelapass_minimal_preflight_inputs_v1",
        "repo_root": str(repo_root),
        "site_config": str(site_config),
        "site_id": candidate_site_id,
        "site_name": PREFLIGHT.text_value(config.get("candidate_site_name")) or "unspecified",
        "fixture_root": str(fixture_root),
        "created_dirs": [str(path.relative_to(repo_root)) for path in created_dirs],
        "staged_files": [str(path.relative_to(repo_root)) for path in staged_files],
        "deferred_context_categories": [
            "swissimage_context",
            "swisstlm3d_context",
            "swisstlm3d_metadata",
            "swisssurface3d_context",
            "swisssurface3d_raster_context",
            "swissbuildings3d_context",
        ],
        "deferred_context_roots": [
            str(paths["swissimage_context"].relative_to(repo_root)),
            str(paths["swisstlm3d_context"].relative_to(repo_root)),
            str(paths["swisssurface3d_context"].relative_to(repo_root)),
            str(paths["swisssurface3d_raster_context"].relative_to(repo_root)),
            str(paths["swissbuildings3d_context"].relative_to(repo_root)),
        ],
        "terrain_crop_path": str(paths["terrain_crop"].relative_to(repo_root)),
        "aoi_tile_catalog_path": str(paths["aoi_tile_catalog"].relative_to(repo_root)),
        "terrain_metadata_path": str(paths["terrain_metadata"].relative_to(repo_root)),
        "source_zone_metadata_path": str(paths["source_zone_metadata"].relative_to(repo_root)),
        "scenario_table_path": str(paths["scenario_table"].relative_to(repo_root)),
        "source_scenario_policy_path": str(paths["source_scenario_policy"].relative_to(repo_root)),
    }
    return report


def ensure_directories(paths: dict[str, Path]) -> list[Path]:
    dirs = [
        paths["processed_input_root"],
        paths["processed_context_root"],
        paths["validation_case_root"],
        paths["hazard_results_root"],
        paths["source_scenario_policy"].parent,
    ]
    for path in dirs:
        path.mkdir(parents=True, exist_ok=True)
    return dirs


def stage_fixture_files(paths: dict[str, Path], fixture_root: Path) -> list[Path]:
    staged: list[Path] = []
    copies = {
        fixture_root / "terrain.asc": paths["terrain_crop"],
        fixture_root / "aoi_tile_catalog.yaml": paths["aoi_tile_catalog"],
        fixture_root / "terrain_metadata.yaml": paths["terrain_metadata"],
        fixture_root / "source_zone_metadata.yaml": paths["source_zone_metadata"],
        fixture_root / "scenario_table.csv": paths["scenario_table"],
        fixture_root / "source_scenario_policy.yaml": paths["source_scenario_policy"],
    }
    for source, target in copies.items():
        if not source.exists():
            raise SystemExit(f"missing synthetic fixture: {source}")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        staged.append(target)
    return staged


def resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def render_text_report(report: dict[str, Any]) -> str:
    lines = [
        f"schema_version: {report['schema_version']}",
        f"repo_root: {report['repo_root']}",
        f"site_id: {report['site_id']}",
        f"site_name: {report['site_name']}",
        f"fixture_root: {report['fixture_root']}",
        "",
        "created_dirs:",
    ]
    lines.extend(f"- {item}" for item in report["created_dirs"])
    lines.append("")
    lines.append("aoi_tile_catalog_path:")
    lines.append(f"- {report['aoi_tile_catalog_path']}")
    lines.append("")
    lines.append("staged_files:")
    lines.extend(f"- {item}" for item in report["staged_files"])
    lines.append("")
    lines.append("deferred_context_categories:")
    lines.extend(f"- {item}" for item in report["deferred_context_categories"])
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
