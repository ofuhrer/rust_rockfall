#!/usr/bin/env python3
"""Generate a bounded Balfrin post-processing microbenchmark package.

The generated package is synthetic and measures workflow-shell overhead only:
filesystem scanning, manifest parsing, reducer-chunk merging, and lightweight
hazard-package assembly. It does not run simulations, submit jobs, or make
physical or operational claims.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "balfrin_postproc_microbenchmark_package_v1"
RUNNER_SCHEMA_VERSION = "balfrin_postproc_microbenchmark_measurement_v1"
DEFAULT_PACKAGE_ID = "balfrin_postproc_microbenchmark_v1"
DEFAULT_FILE_COUNT = 32
DEFAULT_MANIFEST_SIZE_BYTES = 8192
DEFAULT_SIDECAR_COUNT = 6
DEFAULT_REDUCER_CHUNK_COUNT = 4
DEFAULT_PAYLOAD_BYTES = 128


class BalfrinPostprocMicrobenchmarkPackageError(ValueError):
    """User-facing package-generation error."""


@dataclass(frozen=True)
class PackageConfig:
    package_id: str
    file_count: int
    manifest_size_bytes: int
    sidecar_count: int
    reducer_chunk_count: int
    payload_bytes: int


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, required=True, help="Directory to materialize the package into.")
    parser.add_argument("--package-id", default=DEFAULT_PACKAGE_ID)
    parser.add_argument("--file-count", type=positive_int, default=DEFAULT_FILE_COUNT)
    parser.add_argument("--manifest-size-bytes", type=positive_int, default=DEFAULT_MANIFEST_SIZE_BYTES)
    parser.add_argument("--sidecar-count", type=non_negative_int, default=DEFAULT_SIDECAR_COUNT)
    parser.add_argument("--reducer-chunk-count", type=positive_int, default=DEFAULT_REDUCER_CHUNK_COUNT)
    parser.add_argument("--payload-bytes", type=positive_int, default=DEFAULT_PAYLOAD_BYTES)
    parser.add_argument("--force", action="store_true", help="Replace an existing output root.")
    parser.add_argument("--format", choices=("json", "text"), default="text")
    return parser.parse_args(argv)


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be greater than zero")
    return parsed


def non_negative_int(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("value must be non-negative")
    return parsed


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    config = PackageConfig(
        package_id=args.package_id,
        file_count=args.file_count,
        manifest_size_bytes=args.manifest_size_bytes,
        sidecar_count=args.sidecar_count,
        reducer_chunk_count=args.reducer_chunk_count,
        payload_bytes=args.payload_bytes,
    )
    try:
        package = materialize_package(args.output_root, config=config, force=args.force)
    except BalfrinPostprocMicrobenchmarkPackageError as exc:
        print(f"balfrin postproc microbenchmark package error: {exc}", file=sys.stderr)
        return 2

    if args.format == "json":
        print(json.dumps(package, indent=2, sort_keys=True))
    else:
        print(render_text(package))
    return 0


def materialize_package(output_root: Path, *, config: PackageConfig, force: bool = False) -> dict[str, Any]:
    validate_config(config)
    output_root = output_root.resolve()
    if output_root.exists():
        if not force:
            raise BalfrinPostprocMicrobenchmarkPackageError(f"output root already exists: {output_root}")
        shutil.rmtree(output_root)

    input_root = output_root / "input"
    file_family_root = input_root / "file_families"
    manifest_root = input_root / "manifests"
    sidecar_root = input_root / "sidecars"
    reducer_root = input_root / "reducer_chunks"
    harness_root = output_root / "harness"
    output_dir = output_root / "output"
    for path in (file_family_root, manifest_root, sidecar_root, reducer_root, harness_root, output_dir):
        path.mkdir(parents=True, exist_ok=True)

    data_files = write_data_files(file_family_root, config)
    sidecars = write_sidecars(sidecar_root, config)
    reducer_chunks = write_reducer_chunks(reducer_root, config)
    synthetic_manifest = write_sized_manifest(manifest_root / "synthetic_manifest.json", config, data_files, sidecars, reducer_chunks)
    runner_path = harness_root / "run_balfrin_postproc_microbenchmark.py"
    runner_path.write_text(RUNNER_SCRIPT, encoding="utf-8")
    runner_path.chmod(0o755)

    package_manifest_path = output_root / "balfrin_postproc_microbenchmark_package.json"
    measurement_plan = build_measurement_plan(output_root, runner_path)
    package_manifest = {
        "schema_version": SCHEMA_VERSION,
        "package_id": config.package_id,
        "package_status": "generated_no_live_execution",
        "live_submission_authorized": False,
        "simulation_execution_included": False,
        "operational_claims_allowed": False,
        "physical_probability_claims_allowed": False,
        "scale_up_authorized": False,
        "distributed_execution_authorized": False,
        "config": {
            "file_count": config.file_count,
            "manifest_size_bytes": config.manifest_size_bytes,
            "sidecar_count": config.sidecar_count,
            "reducer_chunk_count": config.reducer_chunk_count,
            "payload_bytes": config.payload_bytes,
        },
        "paths": {
            "package_root": str(output_root),
            "file_family_root": str(file_family_root),
            "manifest_root": str(manifest_root),
            "sidecar_root": str(sidecar_root),
            "reducer_chunk_root": str(reducer_root),
            "runner": str(runner_path),
            "measurement_output": str(output_dir / "balfrin_postproc_microbenchmark_measurements.json"),
        },
        "synthetic_inputs": {
            "data_files": summarize_paths(data_files),
            "sidecars": summarize_paths(sidecars),
            "reducer_chunks": summarize_paths(reducer_chunks),
            "synthetic_manifest": summarize_path(synthetic_manifest),
        },
        "expected_touched": {
            "minimum_files": config.file_count + config.sidecar_count + config.reducer_chunk_count + 2,
            "data_payload_bytes": config.file_count * config.payload_bytes,
        },
        "measurement_plan": measurement_plan,
        "boundary_note": (
            "Synthetic post-processing microbenchmark package only; no live Balfrin submission, "
            "simulation execution, physical probability, risk, exposure, vulnerability, scale-up, "
            "distributed-execution, or operational hazard claim is authorized."
        ),
    }
    package_manifest_path.write_text(json.dumps(package_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    package_manifest["paths"]["package_manifest"] = str(package_manifest_path)
    package_manifest_path.write_text(json.dumps(package_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_readme(output_root / "README.md", package_manifest)
    return package_manifest


def validate_config(config: PackageConfig) -> None:
    if config.file_count <= 0:
        raise BalfrinPostprocMicrobenchmarkPackageError("file_count must be greater than zero")
    if config.manifest_size_bytes <= 0:
        raise BalfrinPostprocMicrobenchmarkPackageError("manifest_size_bytes must be greater than zero")
    if config.sidecar_count < 0:
        raise BalfrinPostprocMicrobenchmarkPackageError("sidecar_count must be non-negative")
    if config.reducer_chunk_count <= 0:
        raise BalfrinPostprocMicrobenchmarkPackageError("reducer_chunk_count must be greater than zero")
    if config.payload_bytes <= 0:
        raise BalfrinPostprocMicrobenchmarkPackageError("payload_bytes must be greater than zero")


def write_data_files(root: Path, config: PackageConfig) -> list[Path]:
    paths: list[Path] = []
    for index in range(config.file_count):
        family = root / f"family_{index % 4:02d}"
        family.mkdir(parents=True, exist_ok=True)
        path = family / f"synthetic_{index:06d}.dat"
        seed = f"{config.package_id}:{index}\n".encode("utf-8")
        repeated = (seed * ((config.payload_bytes // len(seed)) + 1))[: config.payload_bytes]
        path.write_bytes(repeated)
        paths.append(path)
    return paths


def write_sidecars(root: Path, config: PackageConfig) -> list[Path]:
    paths: list[Path] = []
    for index in range(config.sidecar_count):
        path = root / f"sidecar_{index:04d}.json"
        payload = {
            "schema_version": "synthetic_sidecar_v1",
            "sidecar_index": index,
            "package_id": config.package_id,
            "role": "postproc_metadata_fixture",
        }
        path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")
        paths.append(path)
    return paths


def write_reducer_chunks(root: Path, config: PackageConfig) -> list[Path]:
    paths: list[Path] = []
    for index in range(config.reducer_chunk_count):
        values = [{"cell_id": f"cell_{i:04d}", "value": index + i} for i in range(8)]
        path = root / f"chunk_{index:04d}_manifest.json"
        payload = {
            "schema_version": "synthetic_reducer_chunk_v1",
            "chunk_id": f"chunk_{index:04d}",
            "merge_order": index,
            "values": values,
        }
        path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")
        paths.append(path)
    return paths


def write_sized_manifest(path: Path, config: PackageConfig, data_files: list[Path], sidecars: list[Path], reducer_chunks: list[Path]) -> Path:
    entries = [{"family": data_file.parent.name, "path": data_file.as_posix(), "bytes": data_file.stat().st_size} for data_file in data_files]
    payload: dict[str, Any] = {
        "schema_version": "synthetic_postproc_manifest_v1",
        "package_id": config.package_id,
        "entries": entries,
        "sidecars": [path.as_posix() for path in sidecars],
        "reducer_chunks": [path.as_posix() for path in reducer_chunks],
        "padding": "",
    }
    path.write_text(_json_at_least_size(payload, config.manifest_size_bytes), encoding="utf-8")
    return path


def _json_at_least_size(payload: dict[str, Any], target_bytes: int) -> str:
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if len(text.encode("utf-8")) >= target_bytes:
        return text
    while len(text.encode("utf-8")) < target_bytes:
        payload["padding"] += "x" * (target_bytes - len(text.encode("utf-8")))
        text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    return text


def build_measurement_plan(package_root: Path, runner_path: Path) -> dict[str, Any]:
    output_path = package_root / "output" / "balfrin_postproc_microbenchmark_measurements.json"
    return {
        "status": "ready_for_authorized_postproc_node_measurement",
        "runner_schema_version": RUNNER_SCHEMA_VERSION,
        "command": (
            "PYENV_VERSION=system uv run python "
            f"{runner_path} --package-root {package_root} --output-json {output_path}"
        ),
        "phase_metrics": [
            "file_scan_seconds",
            "manifest_scan_seconds",
            "reducer_merge_seconds",
            "package_seconds",
        ],
        "resource_metrics": [
            "wall_seconds",
            "cpu_seconds",
            "peak_rss_kb",
            "files_touched",
            "bytes_touched",
        ],
        "execution_boundary": "postprocessing shell only; no sbatch or simulation step is included",
    }


def summarize_paths(paths: list[Path]) -> dict[str, Any]:
    return {
        "count": len(paths),
        "total_bytes": sum(path.stat().st_size for path in paths),
        "sha256": sha256_paths(paths),
    }


def summarize_path(path: Path) -> dict[str, Any]:
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256_file(path)}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_paths(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths):
        digest.update(path.as_posix().encode("utf-8"))
        digest.update(sha256_file(path).encode("utf-8"))
    return digest.hexdigest()


def write_readme(path: Path, package_manifest: dict[str, Any]) -> None:
    plan = package_manifest["measurement_plan"]
    text = "\n".join(
        [
            "# Balfrin Postproc Microbenchmark Package",
            "",
            "This package is synthetic and bounded. It measures workflow-shell post-processing overhead only.",
            "",
            "Run command after separate live-run authorization:",
            "",
            "```bash",
            plan["command"],
            "```",
            "",
            package_manifest["boundary_note"],
            "",
        ]
    )
    path.write_text(text, encoding="utf-8")


def render_text(package: dict[str, Any]) -> str:
    config = package["config"]
    return "\n".join(
        [
            f"schema_version: {package['schema_version']}",
            f"package_id: {package['package_id']}",
            f"package_status: {package['package_status']}",
            f"package_root: {package['paths']['package_root']}",
            f"file_count: {config['file_count']}",
            f"manifest_size_bytes: {config['manifest_size_bytes']}",
            f"sidecar_count: {config['sidecar_count']}",
            f"reducer_chunk_count: {config['reducer_chunk_count']}",
            f"measurement_command: {package['measurement_plan']['command']}",
            f"boundary_note: {package['boundary_note']}",
        ]
    )


RUNNER_SCRIPT = '''#!/usr/bin/env python3
"""Run the generated Balfrin post-processing microbenchmark package."""

from __future__ import annotations

import argparse
import json
import os
import resource
import tarfile
import time
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "balfrin_postproc_microbenchmark_measurement_v1"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-root", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    package_root = args.package_root.resolve()
    manifest = json.loads((package_root / "balfrin_postproc_microbenchmark_package.json").read_text(encoding="utf-8"))
    start_wall = time.perf_counter()
    start_cpu = time.process_time()

    scan = measure_phase(lambda: scan_files(Path(manifest["paths"]["file_family_root"])))
    manifest_scan = measure_phase(lambda: read_json_tree(Path(manifest["paths"]["manifest_root"]), Path(manifest["paths"]["sidecar_root"])))
    reducer_merge = measure_phase(lambda: merge_reducer_chunks(Path(manifest["paths"]["reducer_chunk_root"])))
    package = measure_phase(lambda: package_outputs(package_root, args.output_json.parent))

    touched_files = scan["result"]["file_count"] + manifest_scan["result"]["file_count"] + reducer_merge["result"]["file_count"] + package["result"]["file_count"]
    touched_bytes = scan["result"]["total_bytes"] + manifest_scan["result"]["total_bytes"] + reducer_merge["result"]["total_bytes"] + package["result"]["total_bytes"]
    report = {
        "schema_version": SCHEMA_VERSION,
        "package_schema_version": manifest["schema_version"],
        "package_id": manifest["package_id"],
        "measurement_status": "measured_postproc_shell_overhead",
        "live_submission_authorized": False,
        "simulation_execution_included": False,
        "wall_seconds": time.perf_counter() - start_wall,
        "cpu_seconds": time.process_time() - start_cpu,
        "peak_rss_kb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "phase_seconds": {
            "file_scan_seconds": scan["seconds"],
            "manifest_scan_seconds": manifest_scan["seconds"],
            "reducer_merge_seconds": reducer_merge["seconds"],
            "package_seconds": package["seconds"],
        },
        "files_touched": touched_files,
        "bytes_touched": touched_bytes,
        "phase_results": {
            "file_scan": scan["result"],
            "manifest_scan": manifest_scan["result"],
            "reducer_merge": reducer_merge["result"],
            "package": package["result"],
        },
        "boundary_note": manifest["boundary_note"],
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


def measure_phase(callback):
    start = time.perf_counter()
    result = callback()
    return {"seconds": time.perf_counter() - start, "result": result}


def scan_files(root: Path) -> dict[str, Any]:
    file_count = 0
    total_bytes = 0
    family_counts: dict[str, int] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        file_count += 1
        total_bytes += path.stat().st_size
        family_counts[path.parent.name] = family_counts.get(path.parent.name, 0) + 1
    return {"file_count": file_count, "total_bytes": total_bytes, "family_counts": family_counts}


def read_json_tree(*roots: Path) -> dict[str, Any]:
    file_count = 0
    total_bytes = 0
    object_count = 0
    for root in roots:
        for path in sorted(root.rglob("*.json")):
            total_bytes += path.stat().st_size
            data = json.loads(path.read_text(encoding="utf-8"))
            object_count += len(data) if isinstance(data, dict) else 1
            file_count += 1
    return {"file_count": file_count, "total_bytes": total_bytes, "json_object_count": object_count}


def merge_reducer_chunks(root: Path) -> dict[str, Any]:
    merged: dict[str, float] = {}
    file_count = 0
    total_bytes = 0
    for path in sorted(root.glob("chunk_*_manifest.json")):
        total_bytes += path.stat().st_size
        chunk = json.loads(path.read_text(encoding="utf-8"))
        for item in chunk.get("values", []):
            cell_id = item["cell_id"]
            merged[cell_id] = merged.get(cell_id, 0.0) + float(item["value"])
        file_count += 1
    return {"file_count": file_count, "total_bytes": total_bytes, "merged_cell_count": len(merged), "merged_value_sum": sum(merged.values())}


def package_outputs(package_root: Path, output_root: Path) -> dict[str, Any]:
    output_root.mkdir(parents=True, exist_ok=True)
    package_path = output_root / "synthetic_hazard_package.tar.gz"
    input_root = package_root / "input"
    with tarfile.open(package_path, "w:gz") as tar:
        for path in sorted(input_root.rglob("*.json")):
            tar.add(path, arcname=path.relative_to(package_root))
    return {"file_count": 1, "total_bytes": package_path.stat().st_size, "package_path": str(package_path)}


if __name__ == "__main__":
    raise SystemExit(main())
'''


if __name__ == "__main__":
    raise SystemExit(main())
