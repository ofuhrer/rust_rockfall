#!/usr/bin/env python3
"""Audit whether existing validation outputs can support hazard rebuilding.

This helper is read-only. It compares the legacy summary-only profile against
full-output bounded probes and the canonical native rebuildable reduced
profile, then reports the smallest validation artifact set that
``scripts/build_hazard_layers.py`` can consume for hazard rebuilds.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
from dataclasses import asdict, dataclass
import importlib.util
from pathlib import Path
import sys
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

REBUILD_PROOF_SCHEMA_VERSION = "same_scale_rebuild_proof_v1"
DEFAULT_REBUILD_PROOF_THRESHOLDS = {
    "kinetic_energy_exceedance_j": 100.0,
    "jump_height_exceedance_m": 1.0,
    "velocity_exceedance_mps": 5.0,
}


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


class HazardRebuildOutputProfileError(ValueError):
    """User-facing hazard rebuild output-profile error."""


def _load_hazard_builder():
    module_name = "hazard_rebuild_output_profile_builder"
    if module_name in sys.modules:
        return sys.modules[module_name]
    path = ROOT / "scripts" / "build_hazard_layers.py"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise HazardRebuildOutputProfileError(f"unable to load hazard builder from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


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


def resolve_manifest_output_path(raw_path: str, *, manifest_path: Path, profile_root: Path) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path
    repo_relative = ROOT / path
    if repo_relative.exists():
        return repo_relative
    root_relative = profile_root / path
    if root_relative.exists():
        return root_relative
    return manifest_path.parent / path


def output_records_by_kind(manifest: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    records: dict[str, list[dict[str, Any]]] = {}
    for output in extract_outputs(manifest):
        kind = output.get("kind")
        if isinstance(kind, str):
            records.setdefault(kind, []).append(output)
    return records


def first_output_path(
    records: dict[str, list[dict[str, Any]]],
    kind: str,
    *,
    manifest_path: Path,
    profile_root: Path,
) -> Path | None:
    for record in records.get(kind, []):
        for value in normalize_output_paths(record):
            return resolve_manifest_output_path(value, manifest_path=manifest_path, profile_root=profile_root)
    return None


def build_rebuild_proof_args(
    *,
    manifest_path: Path,
    profile_root: Path,
    output_dir: Path,
    prefix: str,
) -> tuple[list[str], list[str]]:
    manifest = read_json(manifest_path)
    records = output_records_by_kind(manifest)
    trajectory_path = first_output_path(records, "trajectory", manifest_path=manifest_path, profile_root=profile_root)
    if trajectory_path is None:
        trajectory_path = first_output_path(records, "ensemble_trajectories", manifest_path=manifest_path, profile_root=profile_root)
    deposition_path = first_output_path(records, "ensemble_deposition", manifest_path=manifest_path, profile_root=profile_root)
    impact_path = first_output_path(records, "impact_events_csv", manifest_path=manifest_path, profile_root=profile_root)
    if impact_path is None:
        impact_path = first_output_path(records, "ensemble_impact_events", manifest_path=manifest_path, profile_root=profile_root)
    diagnostics_path = first_output_path(records, "diagnostics", manifest_path=manifest_path, profile_root=profile_root)

    required = {
        "trajectory_or_ensemble_trajectories": trajectory_path,
        "ensemble_deposition": deposition_path,
        "impact_events": impact_path,
        "diagnostics": diagnostics_path,
    }
    missing = [name for name, path in required.items() if path is None or not path.exists()]
    if missing:
        return [], missing

    trajectory_flag = "--ensemble-trajectories-dir" if trajectory_path is not None and trajectory_path.is_dir() else "--trajectory"
    impact_flag = "--ensemble-impact-events-dir" if impact_path is not None and impact_path.is_dir() else "--impact-events"
    args = [
        trajectory_flag,
        str(trajectory_path),
        "--deposition",
        str(deposition_path),
        impact_flag,
        str(impact_path),
        "--diagnostics",
        str(diagnostics_path),
        "--output-dir",
        str(output_dir),
        "--prefix",
        prefix,
        "--kinetic-energy-exceedance-j",
        str(DEFAULT_REBUILD_PROOF_THRESHOLDS["kinetic_energy_exceedance_j"]),
        "--jump-height-exceedance-m",
        str(DEFAULT_REBUILD_PROOF_THRESHOLDS["jump_height_exceedance_m"]),
        "--velocity-exceedance-mps",
        str(DEFAULT_REBUILD_PROOF_THRESHOLDS["velocity_exceedance_mps"]),
        "--conditional-curve-export",
        "summary-only",
        "--grid-csv-export",
        "none",
        "--no-plots",
    ]
    return args, []


def build_local_rebuild_proof(
    *,
    manifest_path: Path,
    profile_root: Path,
    output_dir: Path,
    prefix: str = "same_scale_rebuild_proof",
    execute: bool = True,
) -> dict[str, Any]:
    args, missing_inputs = build_rebuild_proof_args(
        manifest_path=manifest_path,
        profile_root=profile_root,
        output_dir=output_dir,
        prefix=prefix,
    )
    if missing_inputs:
        return {
            "schema_version": REBUILD_PROOF_SCHEMA_VERSION,
            "proof_status": "blocked_missing_inputs",
            "missing_inputs": missing_inputs,
            "source_manifest_path": str(manifest_path),
            "output_dir": str(output_dir),
            "thresholds": dict(DEFAULT_REBUILD_PROOF_THRESHOLDS),
            "claim_boundary": "local rebuild proof only; no claim upgrade",
        }
    if not execute:
        return {
            "schema_version": REBUILD_PROOF_SCHEMA_VERSION,
            "proof_status": "planned",
            "builder_args": args,
            "source_manifest_path": str(manifest_path),
            "output_dir": str(output_dir),
            "thresholds": dict(DEFAULT_REBUILD_PROOF_THRESHOLDS),
            "claim_boundary": "local rebuild proof only; no claim upgrade",
        }

    builder = _load_hazard_builder()
    output_dir.mkdir(parents=True, exist_ok=True)
    builder_stdout = io.StringIO()
    with contextlib.redirect_stdout(builder_stdout):
        exit_code = builder.main_with_args(args)
    proof_manifest_path = output_dir / f"{prefix}_manifest.json"
    proof_manifest = read_json(proof_manifest_path) if proof_manifest_path.exists() else {}
    generated_layers = list((proof_manifest.get("hazard_statistics") or {}).get("generated_layer_names") or [])
    expected_layers = [
        builder.exceedance_layer_key(
            "kinetic_energy_exceedance",
            DEFAULT_REBUILD_PROOF_THRESHOLDS["kinetic_energy_exceedance_j"],
            "j",
        ),
        builder.exceedance_layer_key(
            "jump_height_exceedance",
            DEFAULT_REBUILD_PROOF_THRESHOLDS["jump_height_exceedance_m"],
            "m",
        ),
        builder.exceedance_layer_key(
            "velocity_exceedance",
            DEFAULT_REBUILD_PROOF_THRESHOLDS["velocity_exceedance_mps"],
            "mps",
        ),
    ]
    missing_layers = [layer for layer in expected_layers if layer not in generated_layers]
    ready = exit_code == 0 and proof_manifest_path.exists() and not missing_layers
    return {
        "schema_version": REBUILD_PROOF_SCHEMA_VERSION,
        "proof_status": "ready" if ready else "blocked_rebuild_failed",
        "builder_exit_code": exit_code,
        "builder_stdout": builder_stdout.getvalue().strip(),
        "source_manifest_path": str(manifest_path),
        "output_dir": str(output_dir),
        "proof_manifest_path": str(proof_manifest_path),
        "generated_layer_names": generated_layers,
        "expected_closure_layer_names": expected_layers,
        "missing_closure_layer_names": missing_layers,
        "thresholds": dict(DEFAULT_REBUILD_PROOF_THRESHOLDS),
        "claim_boundary": "local rebuild proof only; no claim upgrade",
    }


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


def summarize_rebuild_narrowing(local_rebuild_proof: dict[str, Any] | None) -> dict[str, Any]:
    status = (local_rebuild_proof or {}).get("proof_status", "not_run")
    return {
        "summary_only_blocker_narrowing_status": (
            "legacy_summary_only_still_blocked_but_rebuildable_reduced_path_executable"
            if status == "ready"
            else "not_reduced_without_local_rebuild_proof"
        ),
        "reduced_blocker_key": "summary_only_not_rebuildable" if status == "ready" else None,
        "evidence_status": status,
        "claim_boundary": "narrowing applies only to rebuildability mechanics, not scientific closure or claim level",
    }


def build_default_local_hazard_smoke_recommendation(reduced: ProfileClassification | None) -> dict[str, Any]:
    if reduced is None or reduced.classification == "blocked_missing_inputs":
        return {
            "recommendation_status": "blocked_missing_rebuildable_reduced_profile",
            "recommended_validation_output_mode": "rebuildable_reduced_output",
            "recommended_profile_id": None,
            "next_command": "PYENV_VERSION=system uv run python scripts/check_hazard_rebuild_output_profile.py --format json",
            "rebuild_instruction": "restore or derive the native rebuildable reduced profile before local hazard smoke replay",
            "full_output_recovery": {
                "recovery_status": "full_outputs_available_on_explicit_request",
                "full_output_profile_id": "target_validation",
                "full_output_profile_label": "bounded_probe_full_v1",
                "full_output_profile_root": "validation/private/tschamut_public_pilot/target_gate_v1",
                "full_output_case_path": "validation/private/tschamut_public_pilot/target_gate_v1/tschamut_public_target_gate_case.yaml",
                "full_output_command": (
                    "PYENV_VERSION=system CARGO_TARGET_DIR=/tmp/rust-rockfall-target cargo run -- validate --case "
                    "validation/private/tschamut_public_pilot/target_gate_v1/tschamut_public_target_gate_case.yaml"
                ),
                "full_output_notes": (
                    "Use the full validation case when explicitly requesting the heavier historical output set; "
                    "the reduced profile remains the local default."
                ),
            },
            "claim_boundary": "local smoke recommendation only; no scale-up authorization or claim upgrade",
        }
    return {
        "recommendation_status": "recommended",
        "recommended_validation_output_mode": "rebuildable_reduced_output",
        "recommended_profile_id": reduced.profile_id,
        "recommended_profile_label": reduced.label,
        "recommended_profile_root": reduced.root,
        "rebuild_instruction": (
            "run local hazard smoke and replay checks from the rebuildable reduced manifest; "
            "derive or rerun the profile rather than producing full-debug outputs by default"
        ),
        "next_command": (
            "PYENV_VERSION=system uv run python scripts/check_hazard_rebuild_output_profile.py "
            "--rebuild-proof-manifest "
            f"{reduced.manifest_path} "
            "--rebuild-proof-output-dir /tmp/rust_rockfall/rebuildable_reduced_local_smoke --format json"
        ),
        "full_output_recovery": {
            "recovery_status": "full_outputs_available_on_explicit_request",
            "full_output_profile_id": "target_validation",
            "full_output_profile_label": "bounded_probe_full_v1",
            "full_output_profile_root": "validation/private/tschamut_public_pilot/target_gate_v1",
            "full_output_case_path": "validation/private/tschamut_public_pilot/target_gate_v1/tschamut_public_target_gate_case.yaml",
            "full_output_command": (
                "PYENV_VERSION=system CARGO_TARGET_DIR=/tmp/rust-rockfall-target cargo run -- validate --case "
                "validation/private/tschamut_public_pilot/target_gate_v1/tschamut_public_target_gate_case.yaml"
            ),
            "full_output_notes": (
                "Use the full validation case when explicitly requesting the heavier historical output set; "
                "the reduced profile remains the local default."
            ),
        },
        "default_output_policy": {
            "conditional_curve_export": "summary-only",
            "grid_csv_export": "none",
            "no_plots": True,
            "validation_output_mode": "rebuildable_reduced_output",
        },
        "claim_boundary": "local smoke recommendation only; no scale-up authorization or claim upgrade",
    }


def build_report(profile_specs: list[dict[str, Any]], local_rebuild_proof: dict[str, Any] | None = None) -> dict[str, Any]:
    profiles = [
        classify_profile(spec["manifest"], spec["root"], spec["profile_id"], spec["label"])
        for spec in profile_specs
    ]
    by_id = {profile.profile_id: profile for profile in profiles}
    has_blocked_profiles = any(profile.classification == "blocked_missing_inputs" for profile in profiles)

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
        "hazard_rebuild_output_profile_status": "blocked_missing_inputs" if has_blocked_profiles else "measured",
        "readiness_status": "blocked_missing_inputs" if has_blocked_profiles else "ready",
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
        "same_scale_rebuild_evidence": local_rebuild_proof
        or {
            "schema_version": REBUILD_PROOF_SCHEMA_VERSION,
            "proof_status": "not_run",
            "claim_boundary": "local rebuild proof only; no claim upgrade",
        },
        "summary_only_blocker_narrowing": summarize_rebuild_narrowing(local_rebuild_proof),
        "default_local_hazard_smoke_recommendation": build_default_local_hazard_smoke_recommendation(reduced),
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
    recommendation = report.get("default_local_hazard_smoke_recommendation") or {}
    lines.append(
        "default_local_hazard_smoke_recommendation\t"
        + str(recommendation.get("recommendation_status"))
        + "\t"
        + str(recommendation.get("recommended_validation_output_mode"))
    )
    if recommendation.get("recommended_profile_id") is not None:
        lines.append(
            "default_local_hazard_smoke_recommendation_profile\t"
            + str(recommendation.get("recommended_profile_id"))
            + "\t"
            + str(recommendation.get("recommended_profile_label"))
        )
    full_output_recovery = recommendation.get("full_output_recovery") or {}
    if full_output_recovery:
        lines.append(
            "default_local_hazard_full_output_recovery\t"
            + str(full_output_recovery.get("recovery_status"))
            + "\t"
            + str(full_output_recovery.get("full_output_profile_id"))
        )
        lines.append(
            "default_local_hazard_full_output_recovery_command\t"
            + str(full_output_recovery.get("full_output_command"))
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
    parser.add_argument("--rebuild-proof-manifest", type=Path, default=None)
    parser.add_argument("--rebuild-proof-root", type=Path, default=None)
    parser.add_argument("--rebuild-proof-output-dir", type=Path, default=None)
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

    local_rebuild_proof = None
    if args.rebuild_proof_manifest is not None or args.rebuild_proof_output_dir is not None:
        if args.rebuild_proof_manifest is None or args.rebuild_proof_output_dir is None:
            raise SystemExit("--rebuild-proof-manifest and --rebuild-proof-output-dir must be supplied together")
        local_rebuild_proof = build_local_rebuild_proof(
            manifest_path=args.rebuild_proof_manifest,
            profile_root=args.rebuild_proof_root or args.rebuild_proof_manifest.parent,
            output_dir=args.rebuild_proof_output_dir,
        )

    report = build_report(profile_specs, local_rebuild_proof=local_rebuild_proof)
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(format_text(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
