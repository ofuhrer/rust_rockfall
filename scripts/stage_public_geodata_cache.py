#!/usr/bin/env python3
"""Validate and record locally staged public swisstopo inputs against a cache manifest.

This helper is a local staging front door. It does not download public
geodata, infer missing tiles, or authorize any operational workflow. Instead,
it reads the cache-manifest template, validates the locally supplied staged
paths and metadata sidecars, records deterministic checksums and provenance
fields, and rewrites the manifest in place.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except ImportError as exc:  # pragma: no cover - environment setup.
    raise SystemExit("PyYAML is required. Run this script with `PYENV_VERSION=system uv run python ...`; CI may use `requirements-tools.txt`") from exc


ROOT = Path(__file__).resolve().parents[1]
PREFLIGHT_SCRIPT = ROOT / "scripts" / "check_second_site_public_geodata_preflight.py"
STAGED_PRODUCT_CATEGORIES = {
    "terrain_crop",
    "swissimage_context",
    "swisstlm3d_context",
    "swisssurface3d_context",
    "swisssurface3d_raster_context",
    "swissbuildings3d_context",
    "barrier_inventory",
}
STAGING_WIZARD_SCHEMA_VERSION = "swiss_public_geodata_cache_stage_proposal_v1"
WIZARD_READY_STATUSES = {"ready_to_apply", "ready_with_optional_deferred"}
WIZARD_BLOCKING_STATUSES = {
    "ambiguous_match",
    "checksum_mismatch",
    "metadata_mismatch",
    "missing",
    "missing_metadata",
    "unsupported_product",
}


def _load_preflight_module():
    spec = importlib.util.spec_from_file_location("public_geodata_cache_stage_preflight", PREFLIGHT_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load preflight helper from {PREFLIGHT_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


PREFLIGHT = _load_preflight_module()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-manifest", type=Path, required=True)
    parser.add_argument("--local-path", action="append", type=Path, default=[], help="local file or directory to match against the cache manifest")
    parser.add_argument("--scan-root", action="append", type=Path, default=[], help="directory root to scan recursively for staging candidates")
    parser.add_argument("--proposal-output", type=Path, default=None, help="write the dry-run staging proposal before any manifest update")
    parser.add_argument("--apply", action="store_true", help="apply the wizard proposal to the manifest after a successful dry run")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--json-output", type=Path, default=None)
    args = parser.parse_args(argv)

    report = stage_public_geodata_cache(
        args.cache_manifest,
        local_paths=args.local_path,
        scan_roots=args.scan_root,
        proposal_output=args.proposal_output,
        apply=args.apply,
    )

    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    output = json.dumps(report, indent=2, sort_keys=True) if args.format == "json" else render_text_report(report)
    print(output)
    if report.get("wizard_mode"):
        return 0 if report.get("proposal_status") in WIZARD_READY_STATUSES else 2
    return 0 if report["staging_status"] == "verified" else 2


def stage_public_geodata_cache(
    cache_manifest_path: Path,
    *,
    local_paths: list[Path] | None = None,
    scan_roots: list[Path] | None = None,
    proposal_output: Path | None = None,
    apply: bool = False,
) -> dict[str, Any]:
    if not cache_manifest_path.exists():
        raise SystemExit(f"missing cache manifest: {cache_manifest_path}")
    manifest = PREFLIGHT.load_site_config(cache_manifest_path)
    if not isinstance(manifest, dict):
        manifest = {}
    local_paths = list(local_paths or [])
    scan_roots = list(scan_roots or [])
    if local_paths or scan_roots:
        return stage_public_geodata_cache_with_wizard(
            cache_manifest_path,
            manifest,
            local_paths=local_paths,
            scan_roots=scan_roots,
            proposal_output=proposal_output,
            apply=apply,
        )
    products = manifest.get("products") or []
    staged_products: list[dict[str, Any]] = []
    overall_status = "verified"
    for record in products:
        if not isinstance(record, dict):
            continue
        staged_product = stage_public_geodata_cache_product(record, cache_manifest_path.parent)
        staged_products.append(staged_product)
        status = PREFLIGHT.text_value(staged_product.get("staging_status")) or "missing"
        if status == "optional_missing":
            continue
        if status == "unsupported_product":
            overall_status = status
            continue
        if status == "missing" and overall_status == "verified":
            overall_status = status
        elif status == "checksum_mismatch" and overall_status == "verified":
            overall_status = status
        elif status == "metadata_mismatch" and overall_status == "verified":
            overall_status = status

    staged_count = sum(1 for entry in staged_products if entry.get("staging_status") == "verified")
    optional_missing_count = sum(1 for entry in staged_products if entry.get("staging_status") == "optional_missing")
    missing_count = sum(1 for entry in staged_products if entry.get("staging_status") == "missing")
    checksum_mismatch_count = sum(1 for entry in staged_products if entry.get("staging_status") == "checksum_mismatch")
    metadata_mismatch_count = sum(1 for entry in staged_products if entry.get("staging_status") == "metadata_mismatch")
    unsupported_count = sum(1 for entry in staged_products if entry.get("staging_status") == "unsupported_product")

    staged_manifest = {
        **manifest,
        "schema_version": manifest.get("schema_version") or PREFLIGHT.PUBLIC_GEODATA_CACHE_TEMPLATE_SCHEMA_VERSION,
        "staging_status": overall_status,
        "cache_manifest_path": str(cache_manifest_path),
        "staged_product_count": staged_count,
        "optional_missing_product_count": optional_missing_count,
        "missing_product_count": missing_count,
        "checksum_mismatch_product_count": checksum_mismatch_count,
        "metadata_mismatch_product_count": metadata_mismatch_count,
        "unsupported_product_count": unsupported_count,
        "products": staged_products,
    }
    cache_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    cache_manifest_path.write_text(yaml.safe_dump(staged_manifest, sort_keys=False), encoding="utf-8")

    return {
        "schema_version": "swiss_public_geodata_cache_staging_report_v1",
        "staging_status": overall_status,
        "cache_manifest_path": str(cache_manifest_path),
        "product_count": len(staged_products),
        "staged_product_count": staged_count,
        "optional_missing_product_count": optional_missing_count,
        "missing_product_count": missing_count,
        "checksum_mismatch_product_count": checksum_mismatch_count,
        "metadata_mismatch_product_count": metadata_mismatch_count,
        "unsupported_product_count": unsupported_count,
        "products": staged_products,
        "claim_boundaries": PREFLIGHT.claim_boundaries(),
    }


def stage_public_geodata_cache_with_wizard(
    cache_manifest_path: Path,
    manifest: dict[str, Any],
    *,
    local_paths: list[Path],
    scan_roots: list[Path],
    proposal_output: Path | None,
    apply: bool,
) -> dict[str, Any]:
    candidate_roots = [*local_paths, *scan_roots]
    proposal = build_public_geodata_cache_stage_proposal(cache_manifest_path, manifest, candidate_roots)
    if proposal_output is not None:
        write_public_geodata_cache_stage_proposal(proposal_output, proposal)
    if not apply or proposal["proposal_status"] not in WIZARD_READY_STATUSES:
        return proposal

    applied_manifest = {
        **manifest,
        "schema_version": manifest.get("schema_version") or PREFLIGHT.PUBLIC_GEODATA_CACHE_TEMPLATE_SCHEMA_VERSION,
        "staging_status": "verified",
        "cache_manifest_path": str(cache_manifest_path),
        "staged_product_count": proposal["staged_product_count"],
        "optional_missing_product_count": proposal["optional_missing_product_count"],
        "missing_product_count": proposal["missing_product_count"],
        "checksum_mismatch_product_count": proposal["checksum_mismatch_product_count"],
        "metadata_mismatch_product_count": proposal["metadata_mismatch_product_count"],
        "unsupported_product_count": proposal["unsupported_product_count"],
        "products": proposal["applied_products"],
    }
    cache_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    cache_manifest_path.write_text(yaml.safe_dump(applied_manifest, sort_keys=False), encoding="utf-8")

    return {
        "schema_version": STAGING_WIZARD_SCHEMA_VERSION,
        "wizard_mode": True,
        "proposal_status": proposal["proposal_status"],
        "staging_status": "verified",
        "cache_manifest_path": str(cache_manifest_path),
        "product_count": proposal["product_count"],
        "staged_product_count": proposal["staged_product_count"],
        "optional_missing_product_count": proposal["optional_missing_product_count"],
        "missing_product_count": proposal["missing_product_count"],
        "checksum_mismatch_product_count": proposal["checksum_mismatch_product_count"],
        "metadata_mismatch_product_count": proposal["metadata_mismatch_product_count"],
        "unsupported_product_count": proposal["unsupported_product_count"],
        "products": proposal["applied_products"],
        "proposal": proposal,
        "claim_boundaries": PREFLIGHT.claim_boundaries(),
    }


def build_public_geodata_cache_stage_proposal(
    cache_manifest_path: Path,
    manifest: dict[str, Any],
    candidate_roots: list[Path],
) -> dict[str, Any]:
    products = manifest.get("products") or []
    candidates = collect_public_geodata_stage_candidates(candidate_roots)
    proposed_products: list[dict[str, Any]] = []
    applied_products: list[dict[str, Any]] = []
    overall_status = "ready_to_apply"

    for record in products:
        if not isinstance(record, dict):
            continue
        proposal_product = propose_public_geodata_cache_product(record, cache_manifest_path.parent, candidates)
        proposed_products.append(proposal_product)
        applied_products.append(proposal_product["applied_record"])
        status = PREFLIGHT.text_value(proposal_product.get("proposal_status")) or "missing"
        if status == "optional_deferred":
            if overall_status == "ready_to_apply":
                overall_status = "ready_with_optional_deferred"
            continue
        if status in WIZARD_BLOCKING_STATUSES:
            overall_status = f"blocked_{status}"

    staged_count = sum(1 for entry in applied_products if entry.get("staging_status") == "verified")
    optional_missing_count = sum(1 for entry in applied_products if entry.get("staging_status") == "optional_missing")
    missing_count = sum(1 for entry in applied_products if entry.get("staging_status") == "missing")
    checksum_mismatch_count = sum(1 for entry in applied_products if entry.get("staging_status") == "checksum_mismatch")
    metadata_mismatch_count = sum(1 for entry in applied_products if entry.get("staging_status") == "metadata_mismatch")
    unsupported_count = sum(1 for entry in applied_products if entry.get("staging_status") == "unsupported_product")

    proposal = {
        "schema_version": STAGING_WIZARD_SCHEMA_VERSION,
        "wizard_mode": True,
        "proposal_status": overall_status,
        "cache_manifest_path": str(cache_manifest_path),
        "product_count": len(applied_products),
        "staged_product_count": staged_count,
        "optional_missing_product_count": optional_missing_count,
        "missing_product_count": missing_count,
        "checksum_mismatch_product_count": checksum_mismatch_count,
        "metadata_mismatch_product_count": metadata_mismatch_count,
        "unsupported_product_count": unsupported_count,
        "candidate_root_count": len(candidate_roots),
        "candidate_count": len(candidates),
        "candidate_roots": [format_public_geodata_manifest_path(path) for path in candidate_roots],
        "products": proposed_products,
        "applied_products": applied_products,
        "claim_boundaries": PREFLIGHT.claim_boundaries(),
    }
    return proposal


def propose_public_geodata_cache_product(
    record: dict[str, Any],
    manifest_base: Path,
    candidates: list[dict[str, Any]],
) -> dict[str, Any]:
    category = PREFLIGHT.text_value(record.get("category")) or PREFLIGHT.text_value(record.get("product_id")) or PREFLIGHT.text_value(record.get("source_product_id"))
    required = bool(record.get("required", True))
    if not category or category not in STAGED_PRODUCT_CATEGORIES:
        applied_record = {
            **record,
            "required": required,
            "staging_status": "unsupported_product",
            "verification_status": "unsupported_product",
            "observed_checksum_sha256": "",
            "observed_metadata_mismatches": [],
        }
        return {
            "category": category or "unsupported_product",
            "required": required,
            "proposal_status": "unsupported_product",
            "blocking_reasons": ["unsupported product"],
            "matched_candidate_paths": [],
            "matched_candidate_kinds": [],
            "applied_record": applied_record,
        }

    expected_stage = PREFLIGHT.resolve_repo_path(
        record.get("staged_path") or record.get("expected_staged_path"),
        base=manifest_base,
    )
    expected_metadata = PREFLIGHT.resolve_repo_path(
        record.get("metadata_path") or record.get("expected_metadata_path"),
        base=manifest_base,
    )
    matched_candidate = choose_public_geodata_stage_candidate(record, candidates)
    candidate_was_ambiguous = bool(matched_candidate and matched_candidate.get("ambiguous"))
    applied_record = {
        **record,
        "required": required,
        "staged_path": (
            format_public_geodata_manifest_path(matched_candidate["path"])
            if matched_candidate and not candidate_was_ambiguous
            else format_public_geodata_manifest_path(expected_stage)
        ),
        "metadata_path": (
            format_public_geodata_manifest_path(PREFLIGHT.resolve_repo_path(matched_candidate.get("metadata_path"), base=manifest_base))
            if matched_candidate and not candidate_was_ambiguous and matched_candidate.get("metadata_path")
            else format_public_geodata_manifest_path(expected_metadata)
        ),
    }
    if matched_candidate is not None and not candidate_was_ambiguous:
        applied_record["checksum_sha256"] = PREFLIGHT.text_value(record.get("checksum_sha256")) or PREFLIGHT.text_value(record.get("processed_checksum"))
        applied_record["raw_checksum"] = PREFLIGHT.text_value(record.get("raw_checksum"))
        applied_record["processed_checksum"] = PREFLIGHT.text_value(record.get("processed_checksum"))

    staged_product = stage_public_geodata_cache_product(applied_record, manifest_base)
    proposal_status = staged_product["staging_status"]
    blocking_reasons: list[str] = []
    if candidate_was_ambiguous:
        proposal_status = "ambiguous_match"
        blocking_reasons.append("ambiguous match")
    elif matched_candidate is None:
        proposal_status = "optional_deferred" if not required else "missing"
        if required:
            blocking_reasons.append("missing candidate")
    elif proposal_status == "missing" and matched_candidate and not Path(applied_record["metadata_path"]).exists():
        proposal_status = "missing_metadata"
        blocking_reasons.append("missing metadata")
    elif proposal_status == "optional_missing":
        proposal_status = "optional_deferred"
    elif proposal_status in {"checksum_mismatch", "metadata_mismatch", "unsupported_product"}:
        blocking_reasons.append(proposal_status.replace("_", " "))

    return {
        "category": category,
        "required": required,
        "proposal_status": proposal_status,
        "blocking_reasons": blocking_reasons,
        "matched_candidate_paths": [format_public_geodata_manifest_path(matched_candidate["path"])] if matched_candidate and not candidate_was_ambiguous else [],
        "matched_candidate_kinds": [matched_candidate["kind"]] if matched_candidate and not candidate_was_ambiguous else [],
        "expected_staged_path": format_public_geodata_manifest_path(expected_stage),
        "expected_metadata_path": format_public_geodata_manifest_path(expected_metadata),
        "matched_staged_path": staged_product.get("staged_path"),
        "matched_metadata_path": staged_product.get("metadata_path"),
        "applied_record": staged_product,
    }


def choose_public_geodata_stage_candidate(record: dict[str, Any], candidates: list[dict[str, Any]]) -> dict[str, Any] | None:
    expected_kind = "directory" if not Path(PREFLIGHT.text_value(record.get("staged_path")) or PREFLIGHT.text_value(record.get("expected_staged_path")) or "").suffix else "file"
    scored_candidates: list[tuple[tuple[int, int, int, int], dict[str, Any]]] = []
    for candidate in candidates:
        if candidate["kind"] != expected_kind:
            continue
        score = score_public_geodata_stage_candidate(record, candidate)
        if score > (0, 0):
            scored_candidates.append((score, candidate))
    if not scored_candidates:
        return None
    scored_candidates.sort(key=lambda item: item[0], reverse=True)
    if len(scored_candidates) > 1 and scored_candidates[0][0] == scored_candidates[1][0]:
        return {
            "path": "",
            "kind": "ambiguous",
            "metadata_path": "",
            "ambiguous": True,
        }
    return scored_candidates[0][1]


def score_public_geodata_stage_candidate(record: dict[str, Any], candidate: dict[str, Any]) -> tuple[int, int, int, int]:
    record_tokens = public_geodata_stage_tokens(
        *[
            record.get("category"),
            record.get("product_id"),
            record.get("source_product_id"),
            record.get("source_product_name"),
            record.get("tile_id_or_delivery_identifier"),
            record.get("tile_id"),
        ]
    )
    candidate_tokens = set(candidate.get("tokens") or [])
    token_overlap = len(record_tokens & candidate_tokens)
    metadata_matches = 0
    candidate_metadata = candidate.get("metadata") if isinstance(candidate.get("metadata"), dict) else {}
    expected_source_product_id = PREFLIGHT.text_value(record.get("source_product_id"))
    expected_source_product_name = PREFLIGHT.text_value(record.get("source_product_name"))
    expected_tile_id = PREFLIGHT.text_value(record.get("tile_id_or_delivery_identifier")) or PREFLIGHT.text_value(record.get("tile_id"))
    expected_checksum = PREFLIGHT.text_value(record.get("checksum_sha256")) or PREFLIGHT.text_value(record.get("processed_checksum"))
    if expected_source_product_id and PREFLIGHT.text_value(candidate_metadata.get("source_product_id")) == expected_source_product_id:
        metadata_matches += 1
    if expected_source_product_name and PREFLIGHT.text_value(candidate_metadata.get("source_product_name")) == expected_source_product_name:
        metadata_matches += 1
    if expected_tile_id and (
        PREFLIGHT.text_value(candidate_metadata.get("tile_id")) == expected_tile_id
        or PREFLIGHT.text_value(candidate_metadata.get("tile_id_or_delivery_identifier")) == expected_tile_id
    ):
        metadata_matches += 1
    if expected_checksum and PREFLIGHT.text_value(candidate.get("checksum_sha256")) == expected_checksum:
        metadata_matches += 1
    candidate_name = candidate["path"].name.lower()
    metadata_penalty = 10 if candidate["kind"] == "file" and (candidate["path"].suffix.lower() in {".json", ".yaml", ".yml"} or "metadata" in candidate_name) else 0
    data_bonus = 1 if candidate["kind"] == "file" and candidate["path"].suffix.lower() not in {".json", ".yaml", ".yml"} and "metadata" not in candidate_name else 0
    return (metadata_matches, token_overlap + data_bonus - metadata_penalty)


def collect_public_geodata_stage_candidates(local_roots: list[Path]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    seen_paths: set[Path] = set()
    for root in local_roots:
        resolved_root = root.expanduser().resolve()
        if not resolved_root.exists() or resolved_root in seen_paths:
            continue
        seen_paths.add(resolved_root)
        if resolved_root.is_file():
            candidates.append(build_public_geodata_stage_candidate(resolved_root, root=resolved_root))
            continue
        candidates.append(build_public_geodata_stage_candidate(resolved_root, root=resolved_root))
        for path in sorted(resolved_root.rglob("*")):
            if not path.is_file() and not path.is_dir():
                continue
            if path in seen_paths:
                continue
            seen_paths.add(path)
            candidates.append(build_public_geodata_stage_candidate(path, root=resolved_root))
    return candidates


def build_public_geodata_stage_candidate(path: Path, *, root: Path) -> dict[str, Any]:
    metadata = {}
    metadata_path = ""
    if path.is_file():
        metadata, metadata_path = load_public_geodata_stage_file_metadata(path)
    elif path.is_dir():
        metadata, metadata_path = load_public_geodata_stage_directory_metadata(path)
    token_values = [
        path.name,
        path.stem,
        *(metadata.get(key) for key in ("source_product_id", "source_product_name", "tile_id", "tile_id_or_delivery_identifier", "product_id") if isinstance(metadata.get(key), (str, int, float))),
    ]
    tokens = public_geodata_stage_tokens(*token_values)
    if path.is_dir():
        for descendant in sorted(path.rglob("*")):
            if descendant.is_file():
                tokens.update(public_geodata_stage_tokens(descendant.name, descendant.stem))
    return {
        "path": path,
        "root": root,
        "kind": "directory" if path.is_dir() else "file",
        "metadata": metadata,
        "metadata_path": metadata_path,
        "checksum_sha256": PREFLIGHT.sha256_path(path, exclude_paths=None) if path.is_file() else "",
        "tokens": sorted(tokens),
    }


def load_public_geodata_stage_metadata(path: Path) -> tuple[dict[str, Any], str]:
    if path.suffix.lower() not in {".yaml", ".yml", ".json"}:
        return {}, ""
    metadata = PREFLIGHT.load_site_config(path)
    return (metadata if isinstance(metadata, dict) else {}, str(path) if metadata else "")


def load_public_geodata_stage_file_metadata(path: Path) -> tuple[dict[str, Any], str]:
    if path.suffix.lower() in {".yaml", ".yml", ".json"}:
        return load_public_geodata_stage_metadata(path)

    sibling_candidates = [
        path.with_name("metadata.json"),
        path.with_name("metadata.yaml"),
        path.with_name(f"{path.stem}_metadata.json"),
        path.with_name(f"{path.stem}_metadata.yaml"),
        path.with_suffix(".json"),
        path.with_suffix(".yaml"),
    ]
    for candidate in sibling_candidates:
        if not candidate.exists() or not candidate.is_file():
            continue
        metadata = PREFLIGHT.load_site_config(candidate)
        if isinstance(metadata, dict) and metadata:
            return metadata, str(candidate)
    return {}, ""


def load_public_geodata_stage_directory_metadata(path: Path) -> tuple[dict[str, Any], str]:
    for metadata_path in sorted(path.rglob("*")):
        if not metadata_path.is_file():
            continue
        if metadata_path.name not in {"metadata.json", "metadata.yaml"} and not metadata_path.name.endswith("_metadata.yaml") and not metadata_path.name.endswith("_metadata.json"):
            continue
        metadata = PREFLIGHT.load_site_config(metadata_path)
        if isinstance(metadata, dict) and metadata:
            return metadata, str(metadata_path)
    return {}, ""


def public_geodata_stage_tokens(*values: Any) -> set[str]:
    tokens: set[str] = set()
    for value in values:
        text = PREFLIGHT.text_value(value).lower()
        if not text:
            continue
        for token in re.split(r"[^a-z0-9]+", text):
            if token and len(token) >= 3:
                tokens.add(token)
    return tokens


def write_public_geodata_cache_stage_proposal(path: Path, proposal: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix.lower() in {".yaml", ".yml"}:
        path.write_text(yaml.safe_dump(proposal, sort_keys=False), encoding="utf-8")
    else:
        path.write_text(json.dumps(proposal, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def format_public_geodata_manifest_path(path: Path) -> str:
    if not isinstance(path, Path):
        path = Path(path)
    resolved = path.expanduser().resolve()
    try:
        return str(resolved.relative_to(PREFLIGHT.ROOT))
    except ValueError:
        return str(resolved)


def stage_public_geodata_cache_product(record: dict[str, Any], manifest_base: Path) -> dict[str, Any]:
    category = PREFLIGHT.text_value(record.get("category")) or PREFLIGHT.text_value(record.get("product_id")) or PREFLIGHT.text_value(record.get("source_product_id"))
    required = bool(record.get("required", True))
    if not category or category not in STAGED_PRODUCT_CATEGORIES:
        return {
            **record,
            "required": required,
            "staging_status": "unsupported_product",
            "verification_status": "unsupported_product",
            "observed_checksum_sha256": "",
            "observed_metadata_mismatches": [],
        }

    staged_path = PREFLIGHT.resolve_repo_path(
        record.get("staged_path") or record.get("expected_staged_path"),
        base=manifest_base,
    )
    metadata_path = PREFLIGHT.resolve_repo_path(
        record.get("metadata_path") or record.get("expected_metadata_path"),
        base=manifest_base,
    )
    expected_checksum = PREFLIGHT.text_value(record.get("checksum_sha256")) or PREFLIGHT.text_value(record.get("processed_checksum"))
    observed_checksum = (
        PREFLIGHT.sha256_path(staged_path, exclude_paths={metadata_path} if staged_path.is_dir() else None)
        if staged_path.exists()
        else ""
    )
    actual_metadata = PREFLIGHT.load_site_config(metadata_path) if metadata_path.is_file() else {}
    if not isinstance(actual_metadata, dict):
        actual_metadata = {}

    missing_paths = [name for name, path in (("staged_path", staged_path), ("metadata_path", metadata_path)) if not path.exists()]
    if metadata_path.exists() and not metadata_path.is_file():
        missing_paths.append("metadata_path")
    if missing_paths:
        status = "missing" if required else "optional_missing"
        return {
            **record,
            "required": required,
            "staging_status": status,
            "verification_status": status,
            "staged_path": str(staged_path),
            "metadata_path": str(metadata_path),
            "observed_checksum_sha256": observed_checksum,
            "observed_metadata_mismatches": [],
            "missing_paths": missing_paths,
        }

    metadata_mismatches = compare_metadata(record, actual_metadata)
    checksum_match = not expected_checksum or observed_checksum == expected_checksum
    if not checksum_match:
        status = "checksum_mismatch"
    elif metadata_mismatches:
        status = "metadata_mismatch"
    else:
        status = "verified"

    normalized_record = {
        **record,
        "required": required,
        "staging_status": status,
        "verification_status": status,
        "staged_path": str(staged_path),
        "metadata_path": str(metadata_path),
        "checksum_sha256": expected_checksum or observed_checksum,
        "observed_checksum_sha256": observed_checksum,
        "observed_metadata_mismatches": metadata_mismatches,
    }
    if status == "verified":
        normalized_record["raw_checksum"] = observed_checksum
        normalized_record["processed_checksum"] = observed_checksum
        normalized_record["preprocessing_command_and_timestamp"] = (
            PREFLIGHT.text_value(record.get("preprocessing_command_and_timestamp"))
            or f"PYENV_VERSION=system uv run python scripts/stage_public_geodata_cache.py --cache-manifest {cache_manifest_path_for_record(record, manifest_base)}"
        )
    return normalized_record


def compare_metadata(record: dict[str, Any], metadata: dict[str, Any]) -> list[str]:
    mismatches: list[str] = []
    expected_source_product_id = PREFLIGHT.text_value(record.get("source_product_id"))
    expected_source_product_name = PREFLIGHT.text_value(record.get("source_product_name"))
    expected_source_url = PREFLIGHT.text_value(record.get("source_url_or_download_record")) or PREFLIGHT.text_value(record.get("source_url"))
    expected_product_version = PREFLIGHT.text_value(record.get("product_version_or_date")) or PREFLIGHT.text_value(record.get("product_version"))
    expected_tile_id = PREFLIGHT.text_value(record.get("tile_id_or_delivery_identifier")) or PREFLIGHT.text_value(record.get("tile_id"))
    expected_crs = PREFLIGHT.text_value(record.get("crs"))
    expected_resolution = PREFLIGHT.normalize_resolution_m(record.get("resolution_m"))
    expected_crop_extent = record.get("crop_extent_lv95_m") if isinstance(record.get("crop_extent_lv95_m"), dict) else {}
    expected_license = PREFLIGHT.text_value(record.get("license_or_terms_reference")) or PREFLIGHT.text_value(record.get("license_note"))
    expected_raw_checksum = PREFLIGHT.text_value(record.get("raw_checksum"))
    expected_processed_checksum = PREFLIGHT.text_value(record.get("processed_checksum"))
    expected_preprocessing = PREFLIGHT.text_value(record.get("preprocessing_command_and_timestamp"))

    if expected_source_product_id and PREFLIGHT.text_value(metadata.get("source_product_id")) != expected_source_product_id:
        mismatches.append("source_product_id")
    if expected_source_product_name and PREFLIGHT.text_value(metadata.get("source_product_name")) != expected_source_product_name:
        mismatches.append("source_product_name")
    if expected_source_url and PREFLIGHT.text_value(metadata.get("source_url_or_download_record")) != expected_source_url and PREFLIGHT.text_value(metadata.get("source_url")) != expected_source_url:
        mismatches.append("source_url_or_download_record")
    if expected_product_version and PREFLIGHT.text_value(metadata.get("product_version_or_date")) != expected_product_version and PREFLIGHT.text_value(metadata.get("product_version")) != expected_product_version:
        mismatches.append("product_version_or_date")
    if expected_tile_id and PREFLIGHT.text_value(metadata.get("tile_id_or_delivery_identifier")) != expected_tile_id and PREFLIGHT.text_value(metadata.get("tile_id")) != expected_tile_id:
        mismatches.append("tile_id_or_delivery_identifier")
    if expected_crs and PREFLIGHT.text_value(metadata.get("crs")) != expected_crs:
        mismatches.append("crs")
    if expected_resolution is not None and PREFLIGHT.normalize_resolution_m(metadata.get("resolution_m")) != expected_resolution:
        mismatches.append("resolution_m")
    if expected_crop_extent and metadata.get("crop_extent_lv95_m") != expected_crop_extent:
        mismatches.append("crop_extent_lv95_m")
    if expected_license and PREFLIGHT.text_value(metadata.get("license_or_terms_reference")) != expected_license and PREFLIGHT.text_value(metadata.get("license_note")) != expected_license:
        mismatches.append("license_or_terms_reference")
    if expected_raw_checksum and PREFLIGHT.text_value(metadata.get("raw_checksum")) != expected_raw_checksum:
        mismatches.append("raw_checksum")
    if expected_processed_checksum and PREFLIGHT.text_value(metadata.get("processed_checksum")) != expected_processed_checksum:
        mismatches.append("processed_checksum")
    if expected_preprocessing and PREFLIGHT.text_value(metadata.get("preprocessing_command_and_timestamp")) != expected_preprocessing:
        mismatches.append("preprocessing_command_and_timestamp")
    return mismatches


def cache_manifest_path_for_record(record: dict[str, Any], manifest_base: Path) -> str:
    return str(manifest_base / "public_geodata_cache_manifest.yaml")


def render_text_report(report: dict[str, Any]) -> str:
    lines = [
        f"schema_version: {report['schema_version']}",
        f"staging_status: {report['staging_status']}",
        f"cache_manifest_path: {report['cache_manifest_path']}",
        f"product_count: {report['product_count']}",
        f"staged_product_count: {report['staged_product_count']}",
        f"optional_missing_product_count: {report['optional_missing_product_count']}",
        f"missing_product_count: {report['missing_product_count']}",
        f"checksum_mismatch_product_count: {report['checksum_mismatch_product_count']}",
        f"metadata_mismatch_product_count: {report['metadata_mismatch_product_count']}",
        f"unsupported_product_count: {report['unsupported_product_count']}",
        "products:",
    ]
    for product in report["products"]:
        lines.append(
            f"- {product.get('category') or product.get('product_id')}: "
            f"staging_status={product.get('staging_status')}, "
            f"checksum_match={product.get('staging_status') == 'verified'}, "
            f"missing_paths={', '.join(product.get('missing_paths') or []) or 'none'}, "
            f"metadata_mismatches={', '.join(product.get('observed_metadata_mismatches') or []) or 'none'}"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
