#!/usr/bin/env python3
"""Audit whether existing validation outputs can support hazard rebuilding.

This helper is read-only. It compares the legacy summary-only profile against
full-output bounded probes and the canonical native rebuildable reduced
profile, then reports the smallest validation artifact set that
``scripts/build_hazard_layers.py`` can consume for hazard rebuilds.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

DEFAULT_PROFILE_SPECS = (
    {
        "profile_id": "target_summary_only",
        "label": "current_target_summary_only",
        "root": ROOT / "validation/private/tschamut_public_pilot/target_gate_v1_summary_only",
        "manifest": ROOT
        / "validation/private/tschamut_public_pilot/target_gate_v1_summary_only/validation_tschamut_public_target_gate_v1_summary_only_manifest.json",
    },
    {
        "profile_id": "sampling_sensitivity_v1_full",
        "label": "bounded_probe_full_v1",
        "root": ROOT / "validation/private/tschamut_public_pilot/sampling_sensitivity_v1_full",
        "manifest": ROOT
        / "validation/private/tschamut_public_pilot/sampling_sensitivity_v1_full/validation_tschamut_public_sampling_sensitivity_v1_full_manifest.json",
    },
    {
        "profile_id": "sampling_sensitivity_v2_full",
        "label": "bounded_probe_full_v2",
        "root": ROOT / "validation/private/tschamut_public_pilot/sampling_sensitivity_v2_full",
        "manifest": ROOT
        / "validation/private/tschamut_public_pilot/sampling_sensitivity_v2_full/validation_tschamut_public_sampling_sensitivity_v2_full_manifest.json",
    },
    {
        "profile_id": "target_rebuildable_reduced",
        "label": "native_rebuildable_reduced_output",
        "root": ROOT / "validation/private/tschamut_public_pilot/target_gate_v1_rebuildable_reduced",
        "manifest": ROOT
        / "validation/private/tschamut_public_pilot/target_gate_v1_rebuildable_reduced/validation_tschamut_public_target_gate_v1_rebuildable_reduced_manifest.json",
    },
)

REQUIRED_BUILDER_GROUPS = (
    {
        "group": "trajectory_inputs",
        "any_of_output_kinds": ("trajectory", "ensemble_trajectories"),
        "required_artifacts": ("trajectory_csv or ensemble_trajectories_dir",),
        "builder_inputs": ("--trajectory", "--ensemble-trajectories-dir"),
        "notes": (
            "Hazard layers that depend on reach, kinetic-energy, and jump-height outputs consume trajectory CSVs."
        ),
    },
    {
        "group": "deposition_inputs",
        "any_of_output_kinds": ("ensemble_deposition",),
        "required_artifacts": ("ensemble_deposition_csv",),
        "builder_inputs": ("--deposition",),
        "notes": ("Deposition layers are built from the deposition CSV."),
    },
    {
        "group": "impact_event_inputs",
        "any_of_output_kinds": ("ensemble_impact_events", "impact_events_csv", "ensemble_impact_events_parquet"),
        "required_artifacts": (
            "ensemble_impact_events_dir or impact_events_csv or ensemble_impact_events_parquet",
        ),
        "builder_inputs": ("--impact-events", "--ensemble-impact-events-dir", "--impact-events-parquet"),
        "notes": ("Impact-density layers require impact-event inputs when those layers are rebuilt."),
    },
    {
        "group": "diagnostics_inputs",
        "any_of_output_kinds": ("diagnostics",),
        "required_artifacts": ("diagnostics_json",),
        "builder_inputs": ("--diagnostics",),
        "notes": ("Diagnostics JSON preserves provenance and map-package context."),
    },
)

OPTIONAL_BUILDER_ARTIFACTS = (
    {
        "kind": "trajectory_metadata",
        "artifact": "trajectory_metadata_csv",
        "notes": "Helpful provenance, but not consumed by scripts/build_hazard_layers.py.",
    },
    {
        "kind": "ensemble_stop_state",
        "artifact": "ensemble_stop_state_csv",
        "notes": "Useful for validation bookkeeping, but not consumed by scripts/build_hazard_layers.py.",
    },
)


@dataclass(frozen=True)
class ArtifactAudit:
    path: str
    exists: bool
    file_count: int
    total_bytes: int


@dataclass(frozen=True)
class ProfileClassification:
    profile_id: str
    label: str
    root: str
    manifest_path: str
    classification: str
    missing_output_groups: tuple[str, ...]
    missing_output_kinds: tuple[str, ...]
    output_kinds: tuple[str, ...]
    output_count: int
    file_count: int
    total_bytes: int


def audit_path(path: Path, root: Path = ROOT) -> ArtifactAudit:
    rel = str(path.relative_to(root)) if path.is_relative_to(root) else str(path)
    if not path.exists():
        return ArtifactAudit(path=rel, exists=False, file_count=0, total_bytes=0)

    file_count = 0
    total_bytes = 0
    for child in path.rglob("*"):
        if child.is_file():
            file_count += 1
            total_bytes += child.stat().st_size
    return ArtifactAudit(path=rel, exists=True, file_count=file_count, total_bytes=total_bytes)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def extract_outputs(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    outputs = manifest.get("outputs")
    if isinstance(outputs, list):
        return [entry for entry in outputs if isinstance(entry, dict)]
    return []


def normalize_output_paths(output: dict[str, Any]) -> list[str]:
    values: list[str] = []
    for key in ("path", "directory", "output_path"):
        value = output.get(key)
        if isinstance(value, str) and value:
            values.append(value)
    for key in ("paths",):
        value = output.get(key)
        if isinstance(value, list):
            values.extend(str(item) for item in value if isinstance(item, str) and item)
        elif isinstance(value, str) and value:
            values.append(value)
    return values


def output_kinds(outputs: list[dict[str, Any]]) -> list[str]:
    kinds = {str(output.get("kind")) for output in outputs if isinstance(output.get("kind"), str)}
    kinds.discard("None")
    return sorted(kinds)


def group_satisfaction(output_kind_set: set[str]) -> tuple[list[str], list[str]]:
    satisfied: list[str] = []
    missing: list[str] = []
    for requirement in REQUIRED_BUILDER_GROUPS:
        if output_kind_set.intersection(requirement["any_of_output_kinds"]):
            satisfied.append(requirement["group"])
        else:
            missing.append(requirement["group"])
    return satisfied, missing


def required_artifacts_for_group(group: str) -> list[str]:
    for requirement in REQUIRED_BUILDER_GROUPS:
        if requirement["group"] == group:
            return list(requirement["required_artifacts"])
    return []


def classify_profile(manifest_path: Path, root: Path, profile_id: str, label: str) -> ProfileClassification:
    if not manifest_path.exists() or not root.exists():
        return ProfileClassification(
            profile_id=profile_id,
            label=label,
            root=str(root.relative_to(ROOT)) if root.is_relative_to(ROOT) else str(root),
            manifest_path=str(manifest_path.relative_to(ROOT)) if manifest_path.is_relative_to(ROOT) else str(manifest_path),
            classification="blocked_missing_inputs",
            missing_output_groups=tuple(),
            missing_output_kinds=tuple(),
            output_kinds=tuple(),
            output_count=0,
            file_count=0,
            total_bytes=0,
        )

    manifest = read_json(manifest_path)
    outputs = extract_outputs(manifest)
    kinds = output_kinds(outputs)
    kind_set = set(kinds)
    satisfied, missing_groups = group_satisfaction(kind_set)
    missing_kinds: list[str] = []
    for group in missing_groups:
        missing_kinds.extend(required_artifacts_for_group(group))

    validation_output_mode = manifest.get("validation_output_mode")
    if not missing_groups and validation_output_mode == "rebuildable_reduced_output":
        classification = "rebuildable_reduced_output"
    elif not missing_groups:
        classification = "hazard_rebuild_ready"
    elif "trajectory_inputs" in missing_groups and "impact_event_inputs" in missing_groups:
        classification = "summary_only_not_rebuildable"
    elif "trajectory_inputs" in missing_groups:
        classification = "summary_only_not_rebuildable"
    else:
        classification = "unknown"

    audit = audit_path(root)
    return ProfileClassification(
        profile_id=profile_id,
        label=label,
        root=audit.path,
        manifest_path=str(manifest_path.relative_to(ROOT)) if manifest_path.is_relative_to(ROOT) else str(manifest_path),
        classification=classification,
        missing_output_groups=tuple(missing_groups),
        missing_output_kinds=tuple(sorted(set(missing_kinds))),
        output_kinds=tuple(kinds),
        output_count=len(outputs),
        file_count=audit.file_count,
        total_bytes=audit.total_bytes,
    )


def build_contract() -> dict[str, Any]:
    return {
        "rebuild_contract_status": "specified",
        "required_builder_groups": [
            {
                "group": requirement["group"],
                "any_of_output_kinds": list(requirement["any_of_output_kinds"]),
                "required_artifacts": list(requirement["required_artifacts"]),
                "builder_inputs": list(requirement["builder_inputs"]),
                "notes": requirement["notes"],
            }
            for requirement in REQUIRED_BUILDER_GROUPS
        ],
        "optional_builder_artifacts": [dict(item) for item in OPTIONAL_BUILDER_ARTIFACTS],
        "minimal_rebuildable_output_kinds": [
            "trajectory",
            "ensemble_deposition",
            "impact_events_csv",
            "diagnostics",
        ],
        "minimal_rebuildable_artifacts": [
            "trajectory_csv or ensemble_trajectories_dir",
            "ensemble_deposition_csv",
            "ensemble_impact_events_dir or impact_events_csv or ensemble_impact_events_parquet",
            "diagnostics_json",
        ],
        "hazard_rebuild_compatibility_note": (
            "The native rebuildable_reduced_output profile is the canonical hazard-rebuild-compatible reduced mode. "
            "A reduced profile is hazard-rebuild compatible only if it keeps the builder-facing "
            "trajectory, deposition, impact-event, and diagnostics families. "
            "trajectory_metadata and ensemble_stop_state are optional overhead. "
            "The legacy derivation script remains a compatibility and proof fallback."
        ),
    }


def build_report(profile_specs: list[dict[str, Any]]) -> dict[str, Any]:
    profiles = [
        classify_profile(spec["manifest"], spec["root"], spec["profile_id"], spec["label"])
        for spec in profile_specs
    ]
    by_id = {profile.profile_id: profile for profile in profiles}

    summary = by_id.get("target_summary_only")
    reduced = by_id.get("target_rebuildable_reduced")
    full_profiles = [profile for profile in profiles if profile.profile_id != "target_summary_only"]
    summary_file_count = summary.file_count if summary else 0
    summary_byte_count = summary.total_bytes if summary else 0
    reduced_file_count = reduced.file_count if reduced else 0
    reduced_byte_count = reduced.total_bytes if reduced else 0

    comparisons = []
    for profile in full_profiles:
        comparison = {
            "baseline_profile_id": summary.profile_id if summary else None,
            "comparison_profile_id": profile.profile_id,
            "baseline_file_count": summary_file_count,
            "comparison_file_count": profile.file_count,
            "baseline_byte_count": summary_byte_count,
            "comparison_byte_count": profile.total_bytes,
            "file_count_delta": profile.file_count - summary_file_count,
            "byte_count_delta": profile.total_bytes - summary_byte_count,
        }
        if profile.profile_id == "target_rebuildable_reduced":
            comparison["comparison_classification"] = profile.classification
        comparisons.append(comparison)

    missing_summary_artifacts = {
        "required_builder_groups": list(next((profile.missing_output_groups for profile in profiles if profile.profile_id == "target_summary_only"), ())),
        "required_builder_artifacts": list(next((profile.missing_output_kinds for profile in profiles if profile.profile_id == "target_summary_only"), ())),
    }

    return {
        "hazard_rebuild_output_profile_status": "measured",
        "readiness_status": "ready",
        "scale_up_authorized": False,
        "operational_claims_allowed": False,
        "required_hazard_rebuild_artifacts": build_contract(),
        "profiles": [asdict(profile) for profile in profiles],
        "profile_classifications": {
            **{profile.profile_id: profile.classification for profile in profiles},
            "native_rebuildable_reduced_output": reduced.classification if reduced else "blocked_missing_inputs",
        },
        "missing_summary_only_artifacts": missing_summary_artifacts,
        "file_byte_pressure": {
            "target_summary_only": {
                "file_count": summary_file_count,
                "byte_count": summary_byte_count,
            },
            "target_rebuildable_reduced": {
                "file_count": reduced_file_count,
                "byte_count": reduced_byte_count,
            },
            "comparisons": comparisons,
        },
        "reduced_profile": {
            "profile_id": reduced.profile_id if reduced else None,
            "label": reduced.label if reduced else None,
            "classification": reduced.classification if reduced else "blocked_missing_inputs",
            "file_count": reduced_file_count,
            "byte_count": reduced_byte_count,
            "output_kinds": list(reduced.output_kinds) if reduced else [],
            "validation_output_mode": "rebuildable_reduced_output" if reduced else None,
        },
        "native_rebuildable_reduced_profile": {
            "profile_id": reduced.profile_id if reduced else None,
            "label": reduced.label if reduced else None,
            "classification": reduced.classification if reduced else "blocked_missing_inputs",
            "file_count": reduced_file_count,
            "byte_count": reduced_byte_count,
            "output_kinds": list(reduced.output_kinds) if reduced else [],
            "validation_output_mode": "rebuildable_reduced_output" if reduced else None,
            "status": "canonical_native_rebuildable_reduced_output",
        },
        "rebuildable_reduced_profile": {
            "status": "specified",
            "classification": "rebuildable_reduced_output",
            "canonical_path": "native_rebuildable_reduced_output",
            "retained_output_kinds": [
                "trajectory",
                "ensemble_deposition",
                "impact_events_csv",
                "diagnostics",
            ],
            "retained_artifacts": [
                "trajectory_csv or ensemble_trajectories_dir",
                "ensemble_deposition_csv",
                "ensemble_impact_events_dir or impact_events_csv or ensemble_impact_events_parquet",
                "diagnostics_json",
            ],
            "optional_artifacts": [
                "trajectory_metadata_csv",
                "ensemble_stop_state_csv",
            ],
        },
        "builder_contract_notes": (
            "The current target summary-only profile is not rebuildable because it drops the trajectory "
            "and impact-event families that build_hazard_layers.py reads directly. "
            "The native rebuildable_reduced_output profile keeps the builder-facing families and is the canonical "
            "rebuild-compatible reduced mode. "
            "The legacy derivation path is retained only as a compatibility and proof fallback, while full bounded "
            "probes remain hazard-rebuild-ready."
        ),
    }


def format_text(report: dict[str, Any]) -> str:
    lines = [
        f"hazard_rebuild_output_profile_status\t{report['hazard_rebuild_output_profile_status']}",
        f"readiness_status\t{report['readiness_status']}",
    ]
    for profile in report.get("profiles", []):
        lines.append(
            "\t".join(
                [
                    "profile",
                    str(profile.get("profile_id")),
                    str(profile.get("classification")),
                    f"files={profile.get('file_count')}",
                    f"bytes={profile.get('total_bytes')}",
                    f"kinds={','.join(profile.get('output_kinds') or [])}",
                ]
            )
        )
        if profile.get("missing_output_groups"):
            lines.append(
                "\t".join(
                    [
                        "missing_groups",
                        str(profile.get("profile_id")),
                        ",".join(profile.get("missing_output_groups") or []),
                    ]
                )
            )
    lines.append(
        "minimal_rebuildable_artifacts\t"
        + ", ".join(report["required_hazard_rebuild_artifacts"]["minimal_rebuildable_artifacts"])
    )
    lines.append(
        "summary_only_missing_artifacts\t"
        + ", ".join(report["missing_summary_only_artifacts"]["required_builder_artifacts"])
    )
    reduced = report.get("native_rebuildable_reduced_profile") or report.get("reduced_profile") or {}
    lines.append(
        "native_rebuildable_reduced_profile\t"
        + str(reduced.get("profile_id"))
        + "\t"
        + str(reduced.get("classification"))
        + f"\tfiles={reduced.get('file_count')}"
        + f"\tbytes={reduced.get('byte_count')}"
    )
    legacy = report.get("rebuildable_reduced_profile") or {}
    lines.append(
        "rebuildable_reduced_profile\t"
        + str(legacy.get("status"))
        + "\t"
        + str(legacy.get("canonical_path"))
    )
    lines.append(f"scale_up_authorized\t{str(report['scale_up_authorized']).lower()}")
    lines.append(f"operational_claims_allowed\t{str(report['operational_claims_allowed']).lower()}")
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("json", "text"), default="json")
    parser.add_argument("--summary-only-manifest", type=Path, default=DEFAULT_PROFILE_SPECS[0]["manifest"])
    parser.add_argument("--summary-only-root", type=Path, default=DEFAULT_PROFILE_SPECS[0]["root"])
    parser.add_argument("--full-manifest", type=Path, action="append", default=[])
    parser.add_argument("--full-root", type=Path, action="append", default=[])
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    profile_specs = [
        {
            "profile_id": "target_summary_only",
            "label": "current_target_summary_only",
            "root": args.summary_only_root,
            "manifest": args.summary_only_manifest,
        }
    ]

    if args.full_manifest and args.full_root and len(args.full_manifest) != len(args.full_root):
        raise SystemExit("--full-manifest and --full-root must be supplied in matching counts")

    if args.full_manifest and args.full_root:
        for index, (manifest, root) in enumerate(zip(args.full_manifest, args.full_root, strict=True), start=1):
            profile_specs.append(
                {
                    "profile_id": f"full_probe_{index}",
                    "label": f"full_probe_{index}",
                    "root": root,
                    "manifest": manifest,
                }
            )
    else:
        profile_specs.extend(
            [
                {
                    "profile_id": "sampling_sensitivity_v1_full",
                    "label": "bounded_probe_full_v1",
                    "root": DEFAULT_PROFILE_SPECS[1]["root"],
                    "manifest": DEFAULT_PROFILE_SPECS[1]["manifest"],
                },
                {
                    "profile_id": "sampling_sensitivity_v2_full",
                    "label": "bounded_probe_full_v2",
                    "root": DEFAULT_PROFILE_SPECS[2]["root"],
                    "manifest": DEFAULT_PROFILE_SPECS[2]["manifest"],
                },
                {
                    "profile_id": "target_rebuildable_reduced",
                    "label": "native_rebuildable_reduced_output",
                    "root": DEFAULT_PROFILE_SPECS[3]["root"],
                    "manifest": DEFAULT_PROFILE_SPECS[3]["manifest"],
                },
            ]
        )

    report = build_report(profile_specs)
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(format_text(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
