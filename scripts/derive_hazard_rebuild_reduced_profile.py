#!/usr/bin/env python3
"""Derive a reduced validation profile that still supports hazard rebuilding.

This helper is intentionally narrow: it copies a small set of builder-facing
artifacts from a full validation output root into an ignored reduced root,
then emits a reduced manifest that records the reduced-output classification.
The native ``rebuildable_reduced_output`` mode is the canonical path; this
helper remains a compatibility and proof fallback that reproduces the same
builder-facing reduced root from the full validation artifacts. It does not run
validation or build hazard layers itself.
"""

from __future__ import annotations

import argparse
import json
import shutil
from copy import deepcopy
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_ROOT = ROOT / "validation/private/tschamut_public_pilot/target_gate_v1"
DEFAULT_SOURCE_MANIFEST = (
    ROOT / "validation/private/tschamut_public_pilot/target_gate_v1/validation_tschamut_public_target_gate_v1_manifest.json"
)
DEFAULT_OUTPUT_ROOT = ROOT / "validation/private/tschamut_public_pilot/target_gate_v1_rebuildable_reduced"
DEFAULT_OUTPUT_MANIFEST = DEFAULT_OUTPUT_ROOT / "validation_tschamut_public_target_gate_v1_rebuildable_reduced_manifest.json"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def resolve_path(path: str, *, root: Path) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    repo_candidate = ROOT / candidate
    if repo_candidate.exists():
        return repo_candidate
    return root / candidate


def manifest_output_entries(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    outputs = manifest.get("outputs")
    if isinstance(outputs, list):
        return [entry for entry in outputs if isinstance(entry, dict)]
    return []


def output_entry_by_kind(manifest: dict[str, Any], kind: str) -> dict[str, Any] | None:
    for entry in manifest_output_entries(manifest):
        if entry.get("kind") == kind:
            return entry
    return None


def copy_file(source: Path, destination: Path) -> dict[str, Any]:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    return {
        "source_path": str(source.relative_to(ROOT)) if source.is_relative_to(ROOT) else str(source),
        "destination_path": str(destination.relative_to(ROOT)) if destination.is_relative_to(ROOT) else str(destination),
        "bytes": destination.stat().st_size,
    }


def path_or_str(path: Path) -> str:
    return str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)


def select_first_csv(directory: Path) -> Path:
    if not directory.exists() or not directory.is_dir():
        raise SystemExit(f"impact-events directory does not exist: {directory}")
    csv_files = sorted(path for path in directory.glob("*.csv") if path.is_file())
    if not csv_files:
        raise SystemExit(f"no CSV files were found in {directory}")
    return csv_files[0]


def build_reduced_manifest(
    source_manifest: dict[str, Any],
    reduced_root: Path,
    selected_files: list[dict[str, Any]],
    output_manifest_path: Path,
) -> dict[str, Any]:
    reduced = deepcopy(source_manifest)
    reduced["case_id"] = "validation_tschamut_public_target_gate_v1_rebuildable_reduced"
    reduced["validation_output_mode"] = "rebuildable_reduced_output"
    reduced["outputs"] = selected_files
    reduced["performance"] = deepcopy(reduced.get("performance") or {})
    reduced["performance"]["output_file_count"] = len(selected_files)
    reduced["performance"]["output_bytes"] = sum(int(entry.get("total_bytes") or 0) for entry in selected_files)
    reduced["performance"]["output_write_seconds"] = None
    reduced["trajectory_metadata"] = deepcopy(reduced.get("trajectory_metadata") or {})
    if isinstance(reduced["trajectory_metadata"], dict):
        reduced["trajectory_metadata"]["path"] = str(
            reduced_root / "validation_tschamut_public_target_gate_v1_rebuildable_reduced_trajectory_metadata.csv"
        )
    reduced["hazard_probability"] = deepcopy(reduced.get("hazard_probability") or {})
    if isinstance(reduced["hazard_probability"], dict):
        reduced["hazard_probability"]["metadata_path"] = str(
            reduced_root / "validation_tschamut_public_target_gate_v1_rebuildable_reduced_trajectory_metadata.csv"
        )
    reduced["hazard_map_package"] = deepcopy(reduced.get("hazard_map_package") or {})
    if isinstance(reduced["hazard_map_package"], dict):
        reduced["hazard_map_package"]["map_package_manifest_json"] = str(
            reduced_root / "tschamut_public_scalable_conditional_target_gate_v1_rebuildable_reduced_map_package_manifest.json"
        )
    reduced["output_profile"] = {
        "status": "rebuildable_reduced_output",
        "profile": "rebuildable_reduced_output",
        "validation_output_mode": "rebuildable_reduced_output",
        "derivation_role": "legacy_compatibility_fallback",
        "reduced_from": str(source_manifest.get("_path") or DEFAULT_SOURCE_MANIFEST),
        "notes": [
            "Derived from the full target probe by copying only builder-facing validation artifacts.",
            "This is a compatibility and proof fallback for the canonical native rebuildable_reduced_output mode.",
            "This is a local proof artifact, not a new physics configuration.",
        ],
    }
    reduced["validation_output_profile"] = {
        "status": "rebuildable_reduced_output",
        "validation_output_mode": "rebuildable_reduced_output",
    }
    write_json(output_manifest_path, reduced)
    return reduced


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=DEFAULT_SOURCE_ROOT)
    parser.add_argument("--source-manifest", type=Path, default=DEFAULT_SOURCE_MANIFEST)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--output-manifest", type=Path, default=DEFAULT_OUTPUT_MANIFEST)
    parser.add_argument(
        "--impact-event-count",
        type=int,
        default=1,
        help="number of impact-event CSV files to copy from the source impact-event directory",
    )
    parser.add_argument("--format", choices=("json", "text"), default="json")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.impact_event_count < 1:
        raise SystemExit("--impact-event-count must be at least 1")
    if not args.source_manifest.exists():
        raise SystemExit(f"source manifest does not exist: {args.source_manifest}")
    if not args.source_root.exists():
        raise SystemExit(f"source root does not exist: {args.source_root}")

    source_manifest = read_json(args.source_manifest)
    source_manifest["_path"] = str(args.source_manifest)

    output_root = args.output_root
    if output_root.exists():
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    selected_entries: list[dict[str, Any]] = []
    copied_files: list[dict[str, Any]] = []

    required_kinds = (
        "trajectory",
        "ensemble_deposition",
        "trajectory_metadata",
        "diagnostics",
    )
    for kind in required_kinds:
        entry = output_entry_by_kind(source_manifest, kind)
        if not entry:
            raise SystemExit(f"source manifest is missing required kind: {kind}")
        source_path = resolve_path(str(entry["path"]), root=args.source_root)
        destination_name = Path(str(entry["path"])).name
        destination_path = output_root / destination_name
        copied = copy_file(source_path, destination_path)
        selected_entries.append(
            {
                "kind": str(entry["kind"]),
                "format": str(entry.get("format") or "csv"),
                "path": path_or_str(destination_path),
                "file_count": 1,
                "total_bytes": copied["bytes"],
                "sha256": entry.get("sha256"),
            }
        )
        copied_files.append(copied)

    impact_dir_entry = output_entry_by_kind(source_manifest, "ensemble_impact_events")
    if not impact_dir_entry:
        raise SystemExit("source manifest is missing ensemble_impact_events")
    impact_dir = resolve_path(str(impact_dir_entry["path"]), root=args.source_root)
    impact_csv_source = select_first_csv(impact_dir)
    impact_csv_destination = output_root / "validation_tschamut_public_target_gate_v1_rebuildable_reduced_impact_events.csv"
    copied = copy_file(impact_csv_source, impact_csv_destination)
    selected_entries.append(
        {
            "kind": "impact_events_csv",
            "format": "csv",
            "path": path_or_str(impact_csv_destination),
            "file_count": 1,
            "total_bytes": copied["bytes"],
            "sha256": None,
        }
    )
    copied_files.append(copied)

    reduced_manifest = build_reduced_manifest(
        source_manifest,
        output_root,
        selected_entries,
        args.output_manifest,
    )

    report = {
        "reduced_profile_status": "created",
        "validation_output_mode": "rebuildable_reduced_output",
        "source_manifest_path": str(args.source_manifest.relative_to(ROOT))
        if args.source_manifest.is_relative_to(ROOT)
        else str(args.source_manifest),
        "source_root": str(args.source_root.relative_to(ROOT)) if args.source_root.is_relative_to(ROOT) else str(args.source_root),
        "reduced_root": str(output_root.relative_to(ROOT)) if output_root.is_relative_to(ROOT) else str(output_root),
        "reduced_manifest_path": str(args.output_manifest.relative_to(ROOT))
        if args.output_manifest.is_relative_to(ROOT)
        else str(args.output_manifest),
        "output_file_count": len(selected_entries),
        "output_bytes": sum(entry["total_bytes"] for entry in selected_entries),
        "selected_output_kinds": [entry["kind"] for entry in selected_entries],
        "omitted_output_kinds": [
            entry.get("kind")
            for entry in manifest_output_entries(source_manifest)
            if entry.get("kind") not in {item["kind"] for item in selected_entries}
        ],
        "selected_files": copied_files,
        "scale_up_authorized": False,
        "operational_claims_allowed": False,
        "hazard_rebuild_compatible": True,
    }
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"reduced_profile_status\t{report['reduced_profile_status']}")
        print(f"validation_output_mode\t{report['validation_output_mode']}")
        print(f"output_file_count\t{report['output_file_count']}")
        print(f"output_bytes\t{report['output_bytes']}")
        print("selected_output_kinds\t" + ",".join(report["selected_output_kinds"]))
        print("omitted_output_kinds\t" + ",".join(report["omitted_output_kinds"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
