#!/usr/bin/env python3
"""Validate the Phase 1 public real-site geodata preparation manifest."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except ImportError as exc:  # pragma: no cover - environment setup.
    raise SystemExit("PyYAML is required; install with `python3 -m pip install PyYAML`") from exc


ROOT = Path(__file__).resolve().parents[1]
SUPPORTED_EPSG = 2056
SUPPORTED_VERTICAL_DATUM = "LN02"
VALID_STATUSES = {"template_not_run", "prepared_private_local", "ready_for_conditional_pilot"}
REQUIRED_UNSUPPORTED_CLAIMS = {
    "annual_frequency",
    "return_period",
    "risk_map",
    "operational_hazard_map",
    "validated_hazard_map",
}


class ManifestError(ValueError):
    """User-facing manifest validation error."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args(argv)

    try:
        manifest = read_yaml(args.manifest)
        validate_manifest(manifest, args.manifest)
    except ManifestError as exc:
        print(f"manifest validation error: {exc}", file=sys.stderr)
        return 2

    print(f"public real-site geodata manifest is valid: {args.manifest}")
    return 0


def read_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - path context matters for users.
        raise ManifestError(f"failed to read {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ManifestError(f"manifest must contain a YAML mapping: {path}")
    return data


def validate_manifest(manifest: dict[str, Any], manifest_path: Path | None = None) -> None:
    require(manifest.get("schema_version") == 1, "schema_version must be 1")
    require(
        manifest.get("manifest_type") == "public_real_site_geodata_preparation_v1",
        "manifest_type must be public_real_site_geodata_preparation_v1",
    )
    pilot_id = require_text(manifest.get("pilot_id"), "pilot_id")
    status = require_text(manifest.get("pilot_status"), "pilot_status")
    require(status in VALID_STATUSES, f"pilot_status must be one of {sorted(VALID_STATUSES)}")
    require(
        manifest.get("operational_status") == "research_diagnostic",
        "operational_status must remain research_diagnostic",
    )

    domain = require_mapping(manifest.get("selected_domain"), "selected_domain")
    validate_crs(domain.get("coordinate_reference_system"), "selected_domain")
    extent = require_mapping(domain.get("extent_lv95_m"), "selected_domain.extent_lv95_m")
    validate_extent(extent, status)

    layout = require_mapping(manifest.get("local_layout"), "local_layout")
    validate_layout(layout, pilot_id)

    datasets = require_sequence(manifest.get("required_datasets"), "required_datasets")
    validate_required_datasets(datasets, status)

    for dataset in require_sequence(
        manifest.get("optional_context_datasets", []),
        "optional_context_datasets",
    ):
        validate_dataset_common(require_mapping(dataset, "optional_context_datasets[]"), status)

    preprocessing = require_mapping(manifest.get("preprocessing_plan"), "preprocessing_plan")
    validate_preprocessing(preprocessing, status)
    validate_claim_boundary(require_mapping(manifest.get("claim_boundary"), "claim_boundary"))

    if manifest_path is not None and status == "template_not_run":
        require(
            manifest_path.name.endswith("template.yaml"),
            "template_not_run manifests should use a template filename",
        )


def validate_crs(value: Any, label: str) -> None:
    crs = require_mapping(value, f"{label}.coordinate_reference_system")
    require(crs.get("epsg") == SUPPORTED_EPSG, f"{label} must use EPSG:2056")
    require(
        crs.get("vertical_datum") == SUPPORTED_VERTICAL_DATUM,
        f"{label} must use vertical datum LN02",
    )
    require(crs.get("coordinate_unit") == "m", f"{label} coordinate_unit must be m")
    require(crs.get("height_unit") == "m", f"{label} height_unit must be m")


def validate_extent(extent: dict[str, Any], status: str) -> None:
    values = [extent.get(key) for key in ("xmin", "ymin", "xmax", "ymax")]
    if status == "template_not_run" and all(value is None for value in values):
        return
    xmin, ymin, xmax, ymax = (require_number(value, f"extent {key}") for value, key in zip(values, ("xmin", "ymin", "xmax", "ymax")))
    require(xmax > xmin, "extent xmax must be greater than xmin")
    require(ymax > ymin, "extent ymax must be greater than ymin")


def validate_layout(layout: dict[str, Any], pilot_id: str) -> None:
    raw_root = require_text(layout.get("raw_root"), "local_layout.raw_root")
    processed_root = require_text(layout.get("processed_root"), "local_layout.processed_root")
    private_root = require_text(
        layout.get("private_validation_root"),
        "local_layout.private_validation_root",
    )
    hazard_root = require_text(layout.get("hazard_results_root"), "local_layout.hazard_results_root")
    require(raw_root.startswith("data/raw/swisstopo/"), "raw_root must stay under data/raw/swisstopo/")
    require(
        processed_root.startswith("data/processed/swisstopo/"),
        "processed_root must stay under data/processed/swisstopo/",
    )
    require(
        private_root.startswith("validation/private/"),
        "private_validation_root must stay under validation/private/",
    )
    require(hazard_root.startswith("hazard/results/"), "hazard_results_root must stay under hazard/results/")
    for path in (raw_root, processed_root, private_root, hazard_root):
        require(pilot_id in path, f"local layout path should include pilot_id {pilot_id}: {path}")
    require(layout.get("raw_files_committed") is False, "raw_files_committed must be false")
    require(
        layout.get("processed_large_files_committed") is False,
        "processed_large_files_committed must be false",
    )


def validate_required_datasets(datasets: list[Any], status: str) -> None:
    mapped = {
        require_mapping(dataset, "required_datasets[]").get("dataset_id"): require_mapping(
            dataset,
            "required_datasets[]",
        )
        for dataset in datasets
    }
    require("swisstopo_swissalti3d" in mapped, "required_datasets must include swisstopo_swissalti3d")
    for dataset in mapped.values():
        validate_dataset_common(dataset, status)
    swissalti = mapped["swisstopo_swissalti3d"]
    require(
        swissalti.get("role") == "mandatory_bare_earth_terrain",
        "swisstopo_swissalti3d role must be mandatory_bare_earth_terrain",
    )
    if status != "template_not_run":
        require(
            bool(swissalti.get("source_tiles")),
            "prepared manifests must list swissALTI3D source_tiles",
        )
        require(
            bool(swissalti.get("processed_outputs")),
            "prepared manifests must list swissALTI3D processed_outputs",
        )


def validate_dataset_common(dataset: dict[str, Any], status: str) -> None:
    dataset_id = require_text(dataset.get("dataset_id"), "dataset.dataset_id")
    require(dataset_id.startswith("swisstopo_"), f"{dataset_id} must be a swisstopo dataset id")
    require_text(dataset.get("role"), f"{dataset_id}.role")
    require(dataset.get("source_file_present") is False, f"{dataset_id}.source_file_present must be false in committed manifests")
    download_status = require_text(dataset.get("download_status"), f"{dataset_id}.download_status")
    if status == "template_not_run":
        require(
            download_status in {"not_downloaded", "metadata_only"},
            f"{dataset_id}.download_status must be not_downloaded or metadata_only for templates",
        )


def validate_preprocessing(preprocessing: dict[str, Any], status: str) -> None:
    require_text(preprocessing.get("status"), "preprocessing_plan.status")
    steps = require_sequence(preprocessing.get("steps"), "preprocessing_plan.steps")
    require(len(steps) >= 5, "preprocessing_plan.steps must document the preparation workflow")
    processed_dem = require_mapping(preprocessing.get("processed_dem"), "preprocessing_plan.processed_dem")
    if status == "template_not_run":
        require(
            all(processed_dem.get(key) is None for key in ("path", "format", "processed_sha256")),
            "template processed_dem path, format, and checksum must remain null",
        )
    else:
        require_text(processed_dem.get("path"), "processed_dem.path")
        require_text(processed_dem.get("format"), "processed_dem.format")
        require_text(processed_dem.get("processed_sha256"), "processed_dem.processed_sha256")
    require_text(
        preprocessing.get("dem_terrain_sensitivity_status"),
        "preprocessing_plan.dem_terrain_sensitivity_status",
    )
    require_text(preprocessing.get("visual_qa_status"), "preprocessing_plan.visual_qa_status")


def validate_claim_boundary(boundary: dict[str, Any]) -> None:
    allowed = set(require_sequence(boundary.get("current_allowed_products"), "claim_boundary.current_allowed_products"))
    require("conditional_intensity_exceedance" in allowed, "claim_boundary must allow current conditional_intensity_exceedance")
    future = set(require_sequence(boundary.get("future_products"), "claim_boundary.future_products"))
    require("annual_intensity_frequency" in future, "claim_boundary must reserve future annual_intensity_frequency")
    unsupported = set(
        require_sequence(
            boundary.get("unsupported_current_claims"),
            "claim_boundary.unsupported_current_claims",
        )
    )
    missing = REQUIRED_UNSUPPORTED_CLAIMS - unsupported
    require(not missing, f"claim_boundary unsupported_current_claims omits {sorted(missing)}")
    notes = "\n".join(str(note).lower() for note in require_sequence(boundary.get("notes"), "claim_boundary.notes"))
    require("not validation evidence" in notes, "claim_boundary notes must say swisstopo is not validation evidence")


def require_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ManifestError(f"{label} must be a mapping")
    return value


def require_sequence(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise ManifestError(f"{label} must be a list")
    return value


def require_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ManifestError(f"{label} must be a non-empty string")
    return value


def require_number(value: Any, label: str) -> float:
    if not isinstance(value, (int, float)):
        raise ManifestError(f"{label} must be numeric")
    return float(value)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ManifestError(message)


if __name__ == "__main__":
    raise SystemExit(main())
