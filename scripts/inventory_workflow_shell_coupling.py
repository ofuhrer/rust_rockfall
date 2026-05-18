#!/usr/bin/env python3
"""Inventory implicit workflow-shell coupling across tracked repository files."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Sequence


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "workflow_shell_coupling_inventory_v1"
TEXT_SUFFIXES = {".py", ".md", ".yaml", ".yml", ".json", ".csv", ".toml", ".txt"}
IGNORED_ROOT_PREFIXES = (
    "hazard/results/",
    "validation/private/",
    "data/processed/swisstopo/",
    "verification/results/",
    "validation/results/",
    "calibration/results/",
)
PATH_METHODS = (
    "read_text(",
    "read_bytes(",
    "write_text(",
    "write_bytes(",
    "exists(",
    "stat(",
    "open(",
    "glob(",
    "rglob(",
    "mkdir(",
    "touch(",
)
SCRIPT_REF_PATTERN = re.compile(
    r"(?<![A-Za-z0-9_./-])(?P<ref>(?:\./)?scripts/[A-Za-z0-9_./-]+\.py)\b"
)
STATUS_FIELD_PATTERN = re.compile(
    r"""(?P<key>[A-Za-z0-9_]+_status|status)\s*[:=]\s*(?P<quote>["']?)(?P<value>[A-Za-z0-9_./-]+)(?P=quote)"""
)
LOADED_SCRIPT_PATTERN = re.compile(
    r"""(?:
        _load(?:_script)?_module\(\s*["'][^"']+["']\s*,\s*["'](?P<loader_file>[^"']+\.py)["']
        |
        load_repo_script_module\(\s*ROOT\s*,\s*["'][^"']+["']\s*,\s*["'](?P<shared_loader_file>[^"']+\.py)["']
        |
        ROOT\s*/\s*["']scripts["']\s*/\s*["'](?P<root_file>[^"']+\.py)["']
    )""",
    re.VERBOSE,
)
COMMAND_PLAN_HINTS = ("command plan", "command_plan", "blocked_template_commands")
REPORT_HINTS = ("build_report(", "render_text_report(", "build_readiness_report(", "build_inventory(")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    args = parser.parse_args(argv)

    inventory = build_inventory()
    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(inventory, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    output = json.dumps(inventory, indent=2, sort_keys=True) if args.format == "json" else render_text_report(inventory)
    print(output)
    return 0


def build_inventory(
    paths: Sequence[Path] | None = None,
    *,
    root: Path = ROOT,
) -> dict[str, Any]:
    selected_paths = sorted((Path(path) for path in (paths or discover_tracked_text_paths(root))), key=str)
    records = [build_file_record(path=path, root=root) for path in selected_paths]
    public_records = [{key: value for key, value in record.items() if key != "text"} for record in records]

    dynamic_import_entries = [record for record in public_records if record["dynamic_imports"]]
    generated_report_entries = [record for record in dynamic_import_entries if record["report_surface"]]
    command_plan_entries = [record for record in public_records if record["command_plan_surface"]]
    ignored_root_entries = [record for record in public_records if record["ignored_root_dependencies"]]

    status_entries = collect_status_entries(records)
    status_inventory = build_status_inventory(status_entries)

    families = [
        {
            "family": "dynamic_import_by_path",
            "severity": "needs_shared_helper",
            "summary": {
                "file_count": len(dynamic_import_entries),
                "dependency_count": sum(len(record["dynamic_imports"]) for record in dynamic_import_entries),
            },
            "entries": dynamic_import_entries,
        },
        {
            "family": "command_plan_script_references",
            "severity": "stale_reference_risk",
            "summary": {
                "file_count": len(command_plan_entries),
                "reference_count": sum(len(record["script_references"]) for record in command_plan_entries),
                "stale_reference_count": sum(len(record["stale_script_references"]) for record in command_plan_entries),
            },
            "entries": command_plan_entries,
        },
        {
            "family": "ignored_root_path_assumptions",
            "severity": "hidden_local_state_risk",
            "summary": {
                "file_count": len(ignored_root_entries),
                "reference_count": sum(len(record["ignored_root_dependencies"]) for record in ignored_root_entries),
                "ignored_root_only_file_count": sum(
                    1 for record in ignored_root_entries if record["ignored_root_only_dependency"]
                ),
            },
            "entries": ignored_root_entries,
        },
        {
            "family": "generated_report_dependencies",
            "severity": "stable_contract",
            "summary": {
                "file_count": len(generated_report_entries),
                "dependency_count": sum(len(record["dynamic_imports"]) for record in generated_report_entries),
            },
            "entries": generated_report_entries,
        },
        {
            "family": "duplicated_status_vocabularies",
            "severity": "needs_shared_helper",
            "summary": {
                "value_count": len(status_inventory),
                "duplicated_value_count": sum(1 for item in status_inventory if item["occurrence_count"] > 1),
            },
            "entries": status_inventory,
        },
    ]

    return {
        "schema_version": SCHEMA_VERSION,
        "root": str(root),
        "file_count": len(selected_paths),
        "files": [str(path.relative_to(root)) if path.is_relative_to(root) else str(path) for path in selected_paths],
        "families": families,
        "prioritized_extraction_shortlist": build_extraction_shortlist(families),
    }


def discover_tracked_text_paths(root: Path) -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--full-name"],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return []
    paths = [
        root / line.strip()
        for line in result.stdout.splitlines()
        if line.strip() and (root / line.strip()).suffix.lower() in TEXT_SUFFIXES
    ]
    return sorted(paths)


def build_file_record(path: Path, *, root: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    rel = _relative_path(root, path)
    script_references = _collect_script_references(text)
    stale_script_references = [ref for ref in script_references if not (root / ref).exists()]
    ignored_root_dependencies = _collect_ignored_root_dependencies(text)
    dynamic_imports = _collect_dynamic_imports(text)
    command_plan_surface = _is_command_plan_surface(rel, text, script_references)
    report_surface = _is_report_surface(text, dynamic_imports)
    ignored_root_only_dependency = bool(ignored_root_dependencies) and not _has_tracked_path_reference(text)
    return {
        "path": rel,
        "text": text,
        "command_plan_surface": command_plan_surface,
        "report_surface": report_surface,
        "script_references": script_references,
        "stale_script_references": stale_script_references,
        "ignored_root_dependencies": ignored_root_dependencies,
        "ignored_root_only_dependency": ignored_root_only_dependency,
        "dynamic_imports": dynamic_imports,
    }


def _relative_path(root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _collect_script_references(text: str) -> list[str]:
    refs: list[str] = []
    for match in SCRIPT_REF_PATTERN.finditer(text):
        ref = match.group("ref").removeprefix("./")
        if ref not in refs:
            refs.append(ref)
    return refs


def _collect_dynamic_imports(text: str) -> list[str]:
    dependencies: list[str] = []
    for match in LOADED_SCRIPT_PATTERN.finditer(text):
        ref = match.group("loader_file") or match.group("shared_loader_file") or match.group("root_file")
        if ref:
            dependency = f"scripts/{ref}" if not ref.startswith("scripts/") else ref
            if dependency not in dependencies:
                dependencies.append(dependency)
    return dependencies


def _collect_ignored_root_dependencies(text: str) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        for prefix in IGNORED_ROOT_PREFIXES:
            if prefix in line:
                method = next((token.strip("(") for token in PATH_METHODS if token in line), "reference")
                entry = {"line": str(line_number), "method": method, "prefix": prefix, "line_text": line.strip()}
                if entry not in entries:
                    entries.append(entry)
    return entries


def _is_command_plan_surface(rel_path: str, text: str, script_references: list[str]) -> bool:
    return rel_path.endswith("generate_pilot_command_plan.py") or (
        any(hint in text.lower() for hint in COMMAND_PLAN_HINTS) and bool(script_references)
    )


def _is_report_surface(text: str, dynamic_imports: list[str]) -> bool:
    return bool(dynamic_imports) and any(hint in text for hint in REPORT_HINTS)


def _has_tracked_path_reference(text: str) -> bool:
    return any(
        token in text
        for token in (
            "tests/fixtures/",
            '"tests" / "fixtures"',
            "docs/",
            "scripts/",
            "validation/policies/",
            "validation/pilot_runs/",
            "data/raw/",
        )
    )


def collect_status_entries(records: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    per_value: dict[tuple[str, str], dict[str, Any]] = {}
    for record in records:
        path = record["path"]
        text = record.get("text", "")
        for match in STATUS_FIELD_PATTERN.finditer(text):
            key = match.group("key")
            value = match.group("value")
            slot = per_value.setdefault(
                (key, value),
                {"key": key, "value": value, "files": set(), "occurrence_count": 0},
            )
            slot["files"].add(path)
            slot["occurrence_count"] += 1

    aggregated: dict[str, dict[str, Any]] = {}
    for entry in per_value.values():
        value = entry["value"]
        slot = aggregated.setdefault(
            value,
            {"value": value, "occurrence_count": 0, "files": set(), "keys": set()},
        )
        slot["occurrence_count"] += entry["occurrence_count"]
        slot["files"].update(entry["files"])
        slot["keys"].add(entry["key"])

    entries = [
        {
            "value": value,
            "occurrence_count": data["occurrence_count"],
            "files": sorted(data["files"]),
            "keys": sorted(data["keys"]),
        }
        for value, data in aggregated.items()
    ]
    entries.sort(key=lambda item: (-item["occurrence_count"], item["value"]))
    return entries


def build_status_inventory(entries: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        entry
        for entry in entries
        if entry["occurrence_count"] > 1 or len(entry["keys"]) > 1 or len(entry["files"]) > 1
    ]


def build_extraction_shortlist(families: Sequence[dict[str, Any]]) -> list[dict[str, str]]:
    shortlist: list[dict[str, str]] = []
    if any(family["family"] == "command_plan_script_references" and family["summary"]["stale_reference_count"] for family in families):
        shortlist.append(
            {
                "priority": "1",
                "scope": "command-plan validation",
                "work": "extract a shared script-reference check for pilot command-plan strings and keep stale refs fail-closed.",
            }
        )
    if any(family["family"] == "ignored_root_path_assumptions" and family["summary"]["ignored_root_only_file_count"] for family in families):
        shortlist.append(
            {
                "priority": "2",
                "scope": "ignored-root assumptions",
                "work": "centralize ignored-root path-family metadata so local-state dependencies are explicit in one helper.",
            }
        )
    if any(family["family"] == "dynamic_import_by_path" and family["summary"]["file_count"] for family in families):
        shortlist.append(
            {
                "priority": "3",
                "scope": "dynamic import-by-path",
                "work": "factor the repeated spec-from-file-location loader pattern into one shared workflow-shell helper.",
            }
        )
    if any(family["family"] == "duplicated_status_vocabularies" and family["summary"]["duplicated_value_count"] for family in families):
        shortlist.append(
            {
                "priority": "4",
                "scope": "status vocabulary",
                "work": "define the duplicated workflow status values in a shared vocabulary map before they drift farther apart.",
            }
        )
    return shortlist


def render_text_report(inventory: dict[str, Any]) -> str:
    lines = [
        f"schema_version: {inventory['schema_version']}",
        f"root: {inventory['root']}",
        f"file_count: {inventory['file_count']}",
        "",
    ]
    for family in inventory["families"]:
        lines.append(f"{family['family']} [{family['severity']}]")
        for key, value in family["summary"].items():
            lines.append(f"  {key}: {value}")
        for entry in family["entries"]:
            if family["family"] == "duplicated_status_vocabularies":
                lines.append(
                    f"  - {entry['value']} (count={entry['occurrence_count']}, keys={', '.join(entry['keys'])})"
                )
                continue
            lines.append(f"  - {entry['path']}")
            if entry.get("script_references"):
                lines.append(f"    script_references: {', '.join(entry['script_references'])}")
            if entry.get("stale_script_references"):
                lines.append(f"    stale_script_references: {', '.join(entry['stale_script_references'])}")
            if entry.get("ignored_root_dependencies"):
                lines.append("    ignored_root_dependencies:")
                for dep in entry["ignored_root_dependencies"]:
                    lines.append(
                        f"      - line {dep['line']} {dep['method']} {dep['prefix']} :: {dep['line_text']}"
                    )
            if entry.get("dynamic_imports"):
                lines.append(f"    dynamic_imports: {', '.join(entry['dynamic_imports'])}")
        lines.append("")
    lines.append("prioritized_extraction_shortlist:")
    for item in inventory["prioritized_extraction_shortlist"]:
        lines.append(f"  {item['priority']}. {item['scope']}: {item['work']}")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
