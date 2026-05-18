from __future__ import annotations

import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MISLEADING_HAZARD_CLAIM_PATTERNS: tuple[tuple[str, str], ...] = (
    ("annual frequency claim", r"\bannual(?:ized)?\s+(?:exceedance\s+)?frequenc(?:y|ies)\b"),
    ("annual probability claim", r"\bannual\s+probabilit(?:y|ies)\b"),
    ("annual unit claim", r"\b1\s*/\s*year\b|\bper\s+year\b"),
    ("return-period claim", r"\breturn[- ]period\b|\b(?:10|30|100)[- ]year\b"),
    ("risk-map claim", r"\brisk[- ]map(?:s)?\b"),
    (
        "operational hazard-map claim",
        r"\boperational(?:ly)?\s+(?:validated\s+)?hazard[- ]map(?:s)?\b",
    ),
    ("official hazard-map claim", r"\bofficial\s+hazard[- ]map(?:s)?\b"),
    ("validated hazard-map claim", r"\bvalidated\s+hazard[- ]map(?:s)?\b"),
)

INTENSITY_FREQUENCY_PATTERN = re.compile(r"\bintensity[- ]frequency\b", re.IGNORECASE)

CLAIM_HYGIENE_ALLOWLIST_TERMS = (
    "future",
    "unsupported",
    "disallowed",
    "not ",
    "no ",
    "do not",
    "does not",
    "must not",
    "without",
    "requires",
    "require ",
    "reserved",
    "later",
    "deferred",
    "schema-visible",
    "inactive",
    "excluded",
    "out of scope",
    "before",
    "only when",
    "once ",
    "explicit",
    "reject",
    "rejection",
    "deferral",
    "target",
    "until",
    "design",
    "fields",
    "physical probability",
    "documentation-only",
)

INTENSITY_FREQUENCY_ALLOWLIST_TERMS = CLAIM_HYGIENE_ALLOWLIST_TERMS + (
    "annual",
    "physical",
    "source-frequency",
    "reserve",
    "prototype",
)

DEMO_CLAIM_BOUNDARY_TRUE_FLAG_PATTERNS = (
    ("operational claim-boundary flag", r"\boperational_claims_allowed\b[^\n]{0,40}\btrue\b"),
    ("physical-probability claim-boundary flag", r"\bphysical_probability_claims_allowed\b[^\n]{0,40}\btrue\b"),
    ("annual frequency claim-boundary flag", r"\bannual_frequency_claims_allowed\b[^\n]{0,40}\btrue\b"),
    (
        "risk/exposure/vulnerability claim-boundary flag",
        r"\brisk_exposure_vulnerability_claims_allowed\b[^\n]{0,40}\btrue\b",
    ),
    ("scale-up authorization flag", r"\bscale_up_authorized\b[^\n]{0,40}\btrue\b"),
    (
        "distributed execution authorization flag",
        r"\bdistributed_execution_authorized\b[^\n]{0,40}\btrue\b",
    ),
)


def check_hazard_claim_hygiene() -> list[str]:
    """Reject unsupported hazard-product claims in user-facing text.

    The check is intentionally narrow: it allows future, unsupported, disallowed,
    and explicit boundary language, while flagging bare labels or true claim
    boundary flags that could make a current product look annualized,
    return-period based, operational, or risk oriented.
    """

    paths = [
        ROOT / "README.md",
        ROOT / "hazard/README.md",
        ROOT / "docs/hazard_layers.md",
        ROOT / "docs/hazard_map_semantics.md",
        ROOT / "docs/stochastic_sampling_rng_stream_audit.md",
        ROOT / "docs/conditional_hazard_convergence_acceptance_protocol.md",
        ROOT / "docs/roadmap_hazard_mapping.md",
        ROOT / "docs/validation_plan.md",
        ROOT / "docs/dataset_strategy.md",
        ROOT / "docs/real_case_intensity_frequency_implementation_roadmap.md",
        ROOT / "docs/probabilistic_scenario_model_design.md",
        ROOT / "docs/physical_source_frequency_design_gate.md",
        ROOT / "docs/source_frequency_evidence_contract.md",
        ROOT / "docs/block_release_probability_evidence_contract.md",
        ROOT / "docs/physical_frequency_reducer_preconditions.md",
        ROOT / "docs/annual_physical_validation_calibration_review_gate.md",
        ROOT / "docs/validation_maturity_framework.md",
        ROOT / "docs/pilot_gis_package.md",
        ROOT / "docs/balfrin_post_run_interpretation_gate.md",
        ROOT / "docs/balfrin_minimal_demo_vs_closure.md",
        ROOT / "docs/tschamut_public_conditional_pilot_gate_report.md",
        ROOT / "scripts/summarize_balfrin_failure_taxonomy.py",
        ROOT / "scripts/summarize_balfrin_post_run_interpretation_gate.py",
        ROOT / "scripts/summarize_tschamut_conditional_diagnostic_interpretation.py",
    ]
    errors: list[str] = []
    for path in paths:
        if not path.exists():
            errors.append(f"claim-hygiene path is missing: {path.relative_to(ROOT)}")
            continue
        errors.extend(
            find_hazard_claim_hygiene_errors(
                path.read_text(),
                path.relative_to(ROOT).as_posix(),
            )
        )
    return errors


def find_hazard_claim_hygiene_errors(text: str, label: str) -> list[str]:
    errors: list[str] = []
    lines = text.splitlines()
    for index, line in enumerate(lines, start=1):
        window = _claim_hygiene_window(lines, index)
        for claim_label, pattern in MISLEADING_HAZARD_CLAIM_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE) and not _has_claim_hygiene_allowance(
                window,
                CLAIM_HYGIENE_ALLOWLIST_TERMS,
            ):
                errors.append(
                    f"{label}:{index}: unsupported bare {claim_label}: {line.strip()}"
                )
        if INTENSITY_FREQUENCY_PATTERN.search(line) and not _has_claim_hygiene_allowance(
            window,
            INTENSITY_FREQUENCY_ALLOWLIST_TERMS,
        ):
            errors.append(
                f"{label}:{index}: intensity-frequency must be reserved for future physical/annual products: {line.strip()}"
            )
        for claim_label, pattern in DEMO_CLAIM_BOUNDARY_TRUE_FLAG_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                errors.append(
                    f"{label}:{index}: unsupported demo claim-boundary flag {claim_label}: {line.strip()}"
                )
    return errors


def _claim_hygiene_window(lines: list[str], one_based_index: int) -> str:
    start = max(0, one_based_index - 6)
    end = min(len(lines), one_based_index + 4)
    return "\n".join(lines[start:end]).lower()


def _has_claim_hygiene_allowance(text: str, terms: tuple[str, ...]) -> bool:
    return any(term in text for term in terms)
