"""Shared hazard-output file writing helpers."""

from __future__ import annotations

import hashlib
import time
from pathlib import Path
from typing import Any


NODATA = -9999.0


def register_written_output(
    path: Path,
    kind: str,
    output_file_metadata: dict[Path, dict[str, Any]],
    output_write_kind_seconds: dict[str, float],
    output_write_kind_bytes: dict[str, int],
    *,
    elapsed_seconds: float,
    total_bytes: int,
    sha256_hex: str | None,
) -> None:
    output_write_kind_seconds[kind] = output_write_kind_seconds.get(kind, 0.0) + elapsed_seconds
    output_write_kind_bytes[kind] = output_write_kind_bytes.get(kind, 0) + total_bytes
    output_file_metadata[path] = {
        "total_bytes": total_bytes,
        "sha256": sha256_hex,
    }


def safe_sha256_hex(data: bytes) -> str:
    digest = hashlib.sha256()
    digest.update(data)
    return digest.hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_file_text(
    path: Path,
    text: str,
    kind: str,
    output_file_metadata: dict[Path, dict[str, Any]],
    output_write_kind_seconds: dict[str, float],
    output_write_kind_bytes: dict[str, int],
    *,
    elapsed_seconds: float,
) -> None:
    started = time.perf_counter()
    data = text.encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    register_written_output(
        path,
        kind,
        output_file_metadata,
        output_write_kind_seconds,
        output_write_kind_bytes,
        elapsed_seconds=elapsed_seconds + (time.perf_counter() - started),
        total_bytes=len(data),
        sha256_hex=safe_sha256_hex(data),
    )


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
