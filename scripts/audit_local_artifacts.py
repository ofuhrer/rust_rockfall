#!/usr/bin/env python3
"""Report local ignored artifact/cache directories without modifying them."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TARGETS = (
    "data/raw",
    "validation/results",
    "hazard/results",
    "verification/results",
    "calibration/results",
    "visualization/output",
)


@dataclass(frozen=True)
class ArtifactSummary:
    path: str
    exists: bool
    file_count: int
    total_bytes: int


def summarize_path(path: Path, root: Path = ROOT) -> ArtifactSummary:
    rel = str(path.relative_to(root)) if path.is_relative_to(root) else str(path)
    if not path.exists():
        return ArtifactSummary(path=rel, exists=False, file_count=0, total_bytes=0)

    file_count = 0
    total_bytes = 0
    for child in path.rglob("*"):
        if child.is_file():
            file_count += 1
            total_bytes += child.stat().st_size
    return ArtifactSummary(
        path=rel,
        exists=True,
        file_count=file_count,
        total_bytes=total_bytes,
    )


def summarize_targets(targets: list[Path], root: Path = ROOT) -> list[ArtifactSummary]:
    return [summarize_path(path if path.is_absolute() else root / path, root=root) for path in targets]


def stale_candidates(summaries: list[ArtifactSummary], stale_min_bytes: int) -> list[ArtifactSummary]:
    return [
        summary
        for summary in summaries
        if summary.exists and summary.total_bytes >= stale_min_bytes and summary.file_count > 0
    ]


def format_text(summaries: list[ArtifactSummary]) -> str:
    lines = ["path\texists\tfiles\tbytes"]
    for summary in summaries:
        lines.append(
            f"{summary.path}\t{str(summary.exists).lower()}\t{summary.file_count}\t{summary.total_bytes}"
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="artifact roots to audit; defaults to common ignored raw/result directories",
    )
    parser.add_argument("--json", action="store_true", help="emit JSON instead of tabular text")
    parser.add_argument(
        "--fail-total-bytes",
        type=int,
        default=None,
        help="exit nonzero if the summed artifact size is at or above this byte threshold",
    )
    parser.add_argument(
        "--stale-min-bytes",
        type=int,
        default=1_000_000_000,
        help="mark existing artifact roots at or above this size as likely stale in JSON output",
    )
    args = parser.parse_args(argv)

    targets = args.paths or [Path(path) for path in DEFAULT_TARGETS]
    summaries = summarize_targets(targets)
    total_bytes = sum(summary.total_bytes for summary in summaries)
    payload = {
        "total_bytes": total_bytes,
        "summaries": [asdict(summary) for summary in summaries],
        "likely_stale": [asdict(summary) for summary in stale_candidates(summaries, args.stale_min_bytes)],
        "note": "Read-only local audit. Clean-clone reproduction must not depend on ignored cached outputs.",
    }

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(format_text(summaries))
        print(f"total_bytes\t{total_bytes}")
        print(payload["note"])

    if args.fail_total_bytes is not None and total_bytes >= args.fail_total_bytes:
        print(
            f"artifact audit threshold exceeded: {total_bytes} >= {args.fail_total_bytes}",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
