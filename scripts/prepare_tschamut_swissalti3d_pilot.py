#!/usr/bin/env python3
"""Prepare local Tschamut/swissALTI3D pilot case files.

This script writes ignored validation case YAML files from private, manually
supplied Swiss terrain inputs. It validates only the lightweight metadata
contract used by the repository; it does not download data, run simulations, or
change physics.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except ImportError as exc:  # pragma: no cover - exercised by environment setup.
    raise SystemExit("PyYAML is required; install with `python3 -m pip install PyYAML`") from exc


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASE_DIR = ROOT / "validation" / "private" / "tschamut_swissalti3d" / "cases"
DEFAULT_RESULTS_DIR = ROOT / "validation" / "results" / "tschamut_swissalti3d_private"
OBSERVED_DEPOSITION = ROOT / "validation" / "data" / "processed" / "tschamut" / "observed_deposition.csv"
SUPPORTED_EPSG = 2056
SUPPORTED_VERTICAL_DATUM = "LN02"


class PilotError(ValueError):
    """User-facing pilot preparation error."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Prepare ignored Tschamut/swissALTI3D baseline and rotational pilot cases."
    )
    parser.add_argument("--dem-path", required=True, type=Path, help="private ESRI ASCII DEM crop")
    parser.add_argument(
        "--terrain-metadata",
        required=True,
        type=Path,
        help="terrain-source metadata YAML sidecar for the private DEM crop",
    )
    parser.add_argument(
        "--release-zone-metadata",
        required=True,
        type=Path,
        help="release-zone/source-area metadata YAML sidecar",
    )
    parser.add_argument(
        "--terrain-classes-metadata",
        type=Path,
        help="optional aligned terrain/material-class metadata YAML sidecar",
    )
    parser.add_argument("--case-dir", type=Path, default=DEFAULT_CASE_DIR)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--seed", type=int, default=34014)
    parser.add_argument("--ensemble-size", type=int, default=1)
    parser.add_argument("--force", action="store_true", help="overwrite existing generated cases")
    args = parser.parse_args(argv)

    try:
        generated = prepare_pilot_cases(
            dem_path=args.dem_path,
            terrain_metadata_path=args.terrain_metadata,
            release_zone_metadata_path=args.release_zone_metadata,
            terrain_classes_metadata_path=args.terrain_classes_metadata,
            case_dir=args.case_dir,
            results_dir=args.results_dir,
            seed=args.seed,
            ensemble_size=args.ensemble_size,
            force=args.force,
        )
    except PilotError as exc:
        print(f"pilot preparation error: {exc}", file=sys.stderr)
        return 2

    for path in generated:
        print(path)
    return 0


def prepare_pilot_cases(
    *,
    dem_path: Path,
    terrain_metadata_path: Path,
    release_zone_metadata_path: Path,
    terrain_classes_metadata_path: Path | None,
    case_dir: Path,
    results_dir: Path,
    seed: int,
    ensemble_size: int,
    force: bool = False,
) -> list[Path]:
    dem_path = require_existing_file(dem_path, "private swissALTI3D-style DEM crop")
    terrain_metadata_path = require_existing_file(terrain_metadata_path, "terrain metadata sidecar")
    release_zone_metadata_path = require_existing_file(
        release_zone_metadata_path, "release-zone metadata sidecar"
    )
    if terrain_classes_metadata_path is not None:
        terrain_classes_metadata_path = require_existing_file(
            terrain_classes_metadata_path, "terrain-class metadata sidecar"
        )

    if ensemble_size <= 0:
        raise PilotError("--ensemble-size must be positive")
    if seed < 0:
        raise PilotError("--seed must be nonnegative")

    terrain_metadata = read_yaml(terrain_metadata_path, "terrain metadata sidecar")
    dem_header = read_esri_ascii_header(dem_path)
    validate_terrain_metadata(terrain_metadata, dem_header)
    validate_optional_dem_checksum(terrain_metadata, dem_path)

    release_zone_metadata = read_yaml(release_zone_metadata_path, "release-zone metadata sidecar")
    validate_release_zone_metadata(release_zone_metadata, terrain_metadata)

    terrain_class_metadata: dict[str, Any] | None = None
    if terrain_classes_metadata_path is not None:
        terrain_class_metadata = read_yaml(terrain_classes_metadata_path, "terrain-class metadata sidecar")
        validate_terrain_class_metadata(terrain_class_metadata, terrain_metadata, terrain_classes_metadata_path)

    case_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    generated = []
    for contact_model, suffix in (
        ("translational_v0", "baseline"),
        ("sphere_rotational_v1", "rotational"),
    ):
        case = build_case(
            suffix=suffix,
            contact_model=contact_model,
            dem_path=dem_path,
            terrain_metadata_path=terrain_metadata_path,
            release_zone_metadata_path=release_zone_metadata_path,
            terrain_classes_metadata_path=terrain_classes_metadata_path,
            results_dir=results_dir,
            seed=seed,
            ensemble_size=ensemble_size,
        )
        output_path = case_dir / f"tschamut_swissalti3d_{suffix}.yaml"
        if output_path.exists() and not force:
            raise PilotError(f"{output_path} exists; pass --force to overwrite generated pilot cases")
        output_path.write_text(yaml.safe_dump(case, sort_keys=False), encoding="utf-8")
        generated.append(output_path)
    return generated


def build_case(
    *,
    suffix: str,
    contact_model: str,
    dem_path: Path,
    terrain_metadata_path: Path,
    release_zone_metadata_path: Path,
    terrain_classes_metadata_path: Path | None,
    results_dir: Path,
    seed: int,
    ensemble_size: int,
) -> dict[str, Any]:
    case_id = f"validation_tschamut_swissalti3d_{suffix}"
    outputs = {
        "diagnostics_json": str(results_dir / f"{case_id}_metrics.json"),
        "manifest_json": str(results_dir / f"{case_id}_manifest.json"),
        "ensemble_deposition_csv": str(results_dir / f"{case_id}_deposition.csv"),
        "ensemble_trajectories_dir": str(results_dir / f"{case_id}_trajectories"),
        "ensemble_impact_events_dir": str(results_dir / f"{case_id}_impacts"),
    }
    case: dict[str, Any] = {
        "case_id": case_id,
        "title": f"Tschamut swissALTI3D real-site pilot ({suffix})",
        "level": 5,
        "description": (
            "Local/private Tschamut rerun template using a manually supplied swissALTI3D-style DEM "
            "crop, release-zone metadata, optional terrain classes, and existing physics."
        ),
        "terrain": {
            "type": "ascii_dem_clamped",
            "path": str(dem_path),
            "metadata_path": str(terrain_metadata_path),
        },
        "block": {"mass": 69.0, "radius": 0.176667},
        "release": {
            "position": [0.0, 0.0, 0.0],
            "velocity": [0.0, 0.0, 0.0],
        },
        "release_zone": {
            "metadata_path": str(release_zone_metadata_path),
            "generated_release_points_csv": str(results_dir / f"{case_id}_release_points.csv"),
        },
        "parameters": {
            "gravity": 9.81,
            "normal_restitution": 0.25,
            "tangential_restitution": 0.85,
            "friction_coefficient": 0.45,
            "contact_model": contact_model,
            "roughness_model": "stochastic_contact_v1",
            "roughness_std_normal": 0.08,
            "roughness_std_tangent": 0.06,
            "roughness_std_angle": 0.08,
        },
        "simulation": {"dt": 0.02, "t_max": 18.0, "max_steps": 900, "stop_velocity": 0.1},
        "random": {"seed": seed, "ensemble_size": ensemble_size},
        "hazard_layers": {
            "statistics": {
                "kinetic_energy_exceedance_j": [1000.0, 10000.0],
                "jump_height_exceedance_m": [0.5, 2.0],
                "velocity_exceedance_mps": [5.0, 10.0],
            }
        },
        "validation_scope": {
            "type": "real-site-diagnostic-template",
            "note": (
                "Research workflow template only. Uses private terrain/source-area inputs and existing "
                "parameters; it is not Tschamut calibration or operational hazard validation."
            ),
        },
        "observations": {"deposition_points_csv": str(OBSERVED_DEPOSITION)},
        "expected": {
            "metrics": [
                "release_zone_point_count",
                "release_zone_extent_area_m2",
                "release_zone_mean_runout_m",
                "release_zone_max_runout_m",
                "observed_mean_runout_m",
                "simulated_mean_runout_m",
                "runout_distance_error_m",
                "deposition_centroid_error_m",
                "deposition_cloud_mean_nearest_error_m",
                "lateral_spread_error_m",
                "deposition_cloud_overlap_fraction",
            ],
            "tolerances": {},
        },
        "outputs": outputs,
        "references": {
            "dataset": "tschamut2014",
            "notes": [
                "Private real-site DEM crop and release-zone metadata are generated locally and ignored by git.",
                "Parameters mirror the current Tschamut proxy baseline except for explicit contact-model comparison.",
                "No parameters are tuned to Tschamut observations by this template.",
            ],
        },
        "report": {
            "verifies": [
                "Exercises the real-site Tschamut terrain/source-area workflow and manifest provenance.",
                "Compares baseline and sphere_rotational_v1 behavior on identical private inputs.",
            ],
            "does_not_verify": [
                "Operational hazard skill, proprietary-tool equivalence, calibrated terrain classes, vegetation, forest, fragmentation, or non-spherical block effects.",
            ],
        },
    }
    if terrain_classes_metadata_path is not None:
        case["terrain_classes"] = {"metadata_path": str(terrain_classes_metadata_path)}
    return case


def require_existing_file(path: Path, label: str) -> Path:
    path = path.expanduser()
    if not path.exists():
        raise PilotError(f"missing {label}: {path}")
    if not path.is_file():
        raise PilotError(f"{label} is not a file: {path}")
    return path


def read_yaml(path: Path, label: str) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - user-facing path context matters.
        raise PilotError(f"failed to read {label} {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise PilotError(f"{label} must contain a YAML mapping: {path}")
    return data


def read_esri_ascii_header(path: Path) -> dict[str, float]:
    header: dict[str, float] = {}
    with path.open("r", encoding="utf-8") as handle:
        for _ in range(6):
            line = handle.readline()
            if not line:
                raise PilotError(f"DEM header is incomplete: {path}")
            parts = line.split()
            if len(parts) != 2:
                raise PilotError(f"DEM header line must contain key and value: {line.strip()}")
            header[parts[0].lower()] = float(parts[1])
    required = {"ncols", "nrows", "xllcorner", "yllcorner", "cellsize", "nodata_value"}
    missing = required - set(header)
    if missing:
        raise PilotError(f"DEM header is missing required keys {sorted(missing)}: {path}")
    return header


def validate_terrain_metadata(metadata: dict[str, Any], dem_header: dict[str, float]) -> None:
    require_field(metadata.get("schema_version") == 1, "terrain metadata schema_version must be 1")
    require_field(
        metadata.get("source_dataset") == "swisstopo_swissalti3d",
        "terrain metadata source_dataset must be swisstopo_swissalti3d",
    )
    validate_crs(metadata.get("coordinate_reference_system"), "terrain metadata")
    raster = require_mapping(metadata.get("raster"), "terrain metadata raster")
    extent = require_mapping(metadata.get("extent_lv95_m"), "terrain metadata extent_lv95_m")
    resolution = require_number(raster.get("resolution_m"), "terrain raster.resolution_m")
    width = require_int(raster.get("width_px"), "terrain raster.width_px")
    height = require_int(raster.get("height_px"), "terrain raster.height_px")
    nodata = raster.get("nodata")
    require_field(width == int(dem_header["ncols"]), "terrain metadata width_px does not match DEM ncols")
    require_field(height == int(dem_header["nrows"]), "terrain metadata height_px does not match DEM nrows")
    require_close(resolution, dem_header["cellsize"], "terrain metadata resolution_m does not match DEM cellsize")
    if nodata is not None:
        require_close(float(nodata), dem_header["nodata_value"], "terrain metadata nodata does not match DEM NODATA_value")
    xmin = require_number(extent.get("xmin"), "terrain extent xmin")
    ymin = require_number(extent.get("ymin"), "terrain extent ymin")
    xmax = require_number(extent.get("xmax"), "terrain extent xmax")
    ymax = require_number(extent.get("ymax"), "terrain extent ymax")
    require_close(xmin, dem_header["xllcorner"], "terrain extent xmin does not match DEM xllcorner")
    require_close(ymin, dem_header["yllcorner"], "terrain extent ymin does not match DEM yllcorner")
    require_close(xmax - xmin, width * resolution, "terrain extent width does not match raster dimensions")
    require_close(ymax - ymin, height * resolution, "terrain extent height does not match raster dimensions")
    for field in ("source_product", "source_filename", "license", "download_status"):
        require_field(bool(str(metadata.get(field, "")).strip()), f"terrain metadata {field} must be set")
    preprocessing = require_mapping(metadata.get("preprocessing"), "terrain preprocessing")
    require_field(bool(str(preprocessing.get("status", "")).strip()), "terrain preprocessing.status must be set")
    require_field(bool(str(preprocessing.get("resampling_method", "")).strip()), "terrain preprocessing.resampling_method must be set")


def validate_optional_dem_checksum(metadata: dict[str, Any], dem_path: Path) -> None:
    preprocessing = require_mapping(metadata.get("preprocessing"), "terrain preprocessing")
    processed_sha256 = preprocessing.get("processed_sha256")
    if processed_sha256:
        actual = sha256_file(dem_path)
        require_field(
            str(processed_sha256).lower() == actual,
            f"terrain preprocessing.processed_sha256 does not match DEM crop {dem_path}",
        )


def validate_release_zone_metadata(metadata: dict[str, Any], terrain_metadata: dict[str, Any]) -> None:
    require_field(metadata.get("schema_version") == 1, "release-zone metadata schema_version must be 1")
    validate_crs(metadata.get("coordinate_reference_system"), "release-zone metadata")
    geometry = require_mapping(metadata.get("geometry"), "release-zone geometry")
    require_field(geometry.get("type") == "polygon", "release-zone geometry.type must be polygon")
    coordinates = geometry.get("coordinates")
    if not isinstance(coordinates, list) or len(coordinates) < 3:
        raise PilotError("release-zone polygon must contain at least three vertices")
    extent = require_mapping(terrain_metadata.get("extent_lv95_m"), "terrain extent")
    xmin = float(extent["xmin"])
    xmax = float(extent["xmax"])
    ymin = float(extent["ymin"])
    ymax = float(extent["ymax"])
    for index, point in enumerate(coordinates):
        if not isinstance(point, list) or len(point) != 2:
            raise PilotError(f"release-zone vertex {index} must be [x, y]")
        x, y = float(point[0]), float(point[1])
        if not (xmin <= x <= xmax and ymin <= y <= ymax):
            raise PilotError(f"release-zone vertex {index} lies outside terrain extent")
    sampling = require_mapping(metadata.get("sampling"), "release-zone sampling")
    require_field(sampling.get("mode") == "deterministic_grid", "release-zone sampling.mode must be deterministic_grid")
    require_field(require_int(sampling.get("count"), "release-zone sampling.count") > 0, "release-zone sampling.count must be positive")
    require_field(require_int(sampling.get("seed"), "release-zone sampling.seed") >= 0, "release-zone sampling.seed must be nonnegative")


def validate_terrain_class_metadata(
    metadata: dict[str, Any], terrain_metadata: dict[str, Any], metadata_path: Path
) -> None:
    require_field(metadata.get("schema_version") == 1, "terrain-class metadata schema_version must be 1")
    validate_crs(metadata.get("coordinate_reference_system"), "terrain-class metadata")
    grid_path_value = metadata.get("class_grid_path")
    require_field(bool(str(grid_path_value or "").strip()), "terrain-class class_grid_path must be set")
    grid_path = Path(str(grid_path_value))
    if not grid_path.is_absolute():
        grid_path = metadata_path.parent / grid_path
    class_header = read_esri_ascii_header(grid_path)
    raster = require_mapping(metadata.get("raster"), "terrain-class raster")
    terrain_raster = require_mapping(terrain_metadata.get("raster"), "terrain raster")
    require_field(
        int(raster.get("width_px")) == int(terrain_raster.get("width_px")),
        "terrain-class width_px must match terrain metadata",
    )
    require_field(
        int(raster.get("height_px")) == int(terrain_raster.get("height_px")),
        "terrain-class height_px must match terrain metadata",
    )
    require_close(
        float(raster.get("resolution_m")),
        float(terrain_raster.get("resolution_m")),
        "terrain-class resolution_m must match terrain metadata",
    )
    require_field(int(class_header["ncols"]) == int(raster.get("width_px")), "terrain-class grid ncols mismatch")
    require_field(int(class_header["nrows"]) == int(raster.get("height_px")), "terrain-class grid nrows mismatch")
    terrain_extent = require_mapping(terrain_metadata.get("extent_lv95_m"), "terrain extent")
    class_extent = require_mapping(metadata.get("extent_lv95_m"), "terrain-class extent")
    for key in ("xmin", "ymin", "xmax", "ymax"):
        require_close(float(class_extent[key]), float(terrain_extent[key]), f"terrain-class extent {key} must match terrain")
    classes = metadata.get("classes")
    if not isinstance(classes, list) or not classes:
        raise PilotError("terrain-class metadata must declare at least one class")


def validate_crs(value: Any, label: str) -> None:
    crs = require_mapping(value, f"{label} coordinate_reference_system")
    require_field(int(crs.get("epsg", -1)) == SUPPORTED_EPSG, f"{label} must use EPSG:{SUPPORTED_EPSG}")
    require_field(
        str(crs.get("vertical_datum")) == SUPPORTED_VERTICAL_DATUM,
        f"{label} must use vertical datum {SUPPORTED_VERTICAL_DATUM}",
    )
    require_field(str(crs.get("coordinate_unit")) == "m", f"{label} coordinate_unit must be m")
    require_field(str(crs.get("height_unit")) == "m", f"{label} height_unit must be m")


def require_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise PilotError(f"{label} must be a mapping")
    return value


def require_field(condition: bool, message: str) -> None:
    if not condition:
        raise PilotError(message)


def require_number(value: Any, label: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise PilotError(f"{label} must be numeric") from exc


def require_int(value: Any, label: str) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise PilotError(f"{label} must be an integer") from exc
    return parsed


def require_close(left: float, right: float, message: str, tolerance: float = 1.0e-7) -> None:
    if abs(left - right) > tolerance:
        raise PilotError(f"{message}: {left} != {right}")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
