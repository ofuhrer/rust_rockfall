#!/usr/bin/env python3
"""Verify a staged public-geodata cache against a deterministic provenance contract."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _load_preflight_module():
    path = ROOT / "scripts" / "check_second_site_public_geodata_preflight.py"
    spec = importlib.util.spec_from_file_location("public_geodata_cache_verifier_preflight", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load preflight helper from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


PREFLIGHT = _load_preflight_module()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-manifest", type=Path, required=True)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    args = parser.parse_args(argv)

    report = PREFLIGHT.verify_public_geodata_cache(args.cache_manifest)

    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    output = json.dumps(report, indent=2, sort_keys=True) if args.format == "json" else render_text_report(report)
    print(output)
    return 0 if report["verification_status"] == "verified" else 2


def render_text_report(report: dict[str, object]) -> str:
    lines = [
        f"schema_version: {report['schema_version']}",
        f"verification_status: {report['verification_status']}",
        f"cache_manifest_path: {report['cache_manifest_path']}",
        f"product_count: {report['product_count']}",
        "verification_fields:",
    ]
    lines.extend(f"- {field}" for field in report["verification_fields"])
    lines.append("products:")
    products = report.get("products") or []
    if products:
        for product in products:
            if not isinstance(product, dict):
                continue
            lines.append(
                f"- {product.get('product_id', '')}: status={product.get('verification_status', '')}, "
                f"checksum_match={product.get('checksum_match', False)}, "
                f"missing_paths={', '.join(product.get('missing_paths') or []) or 'none'}, "
                f"metadata_mismatches={', '.join(product.get('metadata_mismatches') or []) or 'none'}"
            )
    else:
        lines.append("- none")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
