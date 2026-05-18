from __future__ import annotations

"""Shared command-plan output-profile policy helpers.

The helpers classify the command-plan output contract into one of three
states:

- ``scalable_default``: summary-only curves, grid CSV suppression, and
  no-plots are all explicit.
- ``explicit_heavy_debug``: heavier output controls are present, but an
  explicit override has been supplied.
- ``blocked_unscalable_default``: heavier controls are present without an
  explicit override.

The policy intentionally stays about control intent only. It does not change
hazard values or execution semantics.
"""

from typing import Any


POLICY_SCHEMA_VERSION = "command_plan_output_profile_policy_v1"
SCALABLE_DEFAULT = "scalable_default"
EXPLICIT_HEAVY_DEBUG = "explicit_heavy_debug"
BLOCKED_UNSCALABLE_DEFAULT = "blocked_unscalable_default"

REQUIRED_SCALABLE_CONTROLS = (
    "--conditional-curve-export summary-only",
    "--grid-csv-export none",
    "--no-plots",
)


def classify_output_profile_policy(
    *,
    conditional_curve_export: Any,
    grid_csv_export: Any,
    no_plots: Any,
    explicit_debug_override: bool = False,
    label: str | None = None,
) -> dict[str, Any]:
    conditional_curve_export_value = _normalize_text(conditional_curve_export)
    grid_csv_export_value = _normalize_text(grid_csv_export)
    no_plots_value = _coerce_bool(no_plots)

    heavy_controls: list[str] = []
    if conditional_curve_export_value != "summary-only":
        heavy_controls.append(f"--conditional-curve-export {conditional_curve_export_value or 'missing'}")
    if grid_csv_export_value != "none":
        heavy_controls.append(f"--grid-csv-export {grid_csv_export_value or 'missing'}")
    if not no_plots_value:
        heavy_controls.append("--plots-enabled")

    if not heavy_controls:
        classification = SCALABLE_DEFAULT
        summary = "summary-only conditional curves, grid CSV suppression, and no-plots are explicit"
        blocked_reason = None
    elif explicit_debug_override:
        classification = EXPLICIT_HEAVY_DEBUG
        summary = "explicit heavy-debug override allows heavier conditional-curve or grid-CSV output"
        blocked_reason = None
    else:
        classification = BLOCKED_UNSCALABLE_DEFAULT
        summary = "heavy conditional-curve, grid-CSV, or plot outputs are blocked unless explicitly overridden"
        blocked_reason = "; ".join(heavy_controls)

    return {
        "schema_version": POLICY_SCHEMA_VERSION,
        "label": label,
        "classification": classification,
        "summary": summary,
        "required_scalable_controls": list(REQUIRED_SCALABLE_CONTROLS),
        "conditional_curve_export": conditional_curve_export_value,
        "grid_csv_export": grid_csv_export_value,
        "no_plots": no_plots_value,
        "explicit_debug_override": explicit_debug_override,
        "heavy_controls": heavy_controls,
        "blocked_reason": blocked_reason,
    }


def summarize_output_profile_policies(policies: list[dict[str, Any]], *, label: str | None = None) -> dict[str, Any]:
    blocked = [policy for policy in policies if policy.get("classification") == BLOCKED_UNSCALABLE_DEFAULT]
    explicit = [policy for policy in policies if policy.get("classification") == EXPLICIT_HEAVY_DEBUG]
    scalable = [policy for policy in policies if policy.get("classification") == SCALABLE_DEFAULT]

    if blocked:
        classification = BLOCKED_UNSCALABLE_DEFAULT
        summary = "one or more command-plan profiles request heavy output defaults without an explicit override"
    elif explicit:
        classification = EXPLICIT_HEAVY_DEBUG
        summary = "one or more command-plan profiles use an explicit heavy-debug override"
    else:
        classification = SCALABLE_DEFAULT
        summary = "all command-plan profiles stay on the scalable default"

    return {
        "schema_version": POLICY_SCHEMA_VERSION,
        "label": label,
        "classification": classification,
        "summary": summary,
        "policy_count": len(policies),
        "scalable_policy_count": len(scalable),
        "explicit_heavy_debug_policy_count": len(explicit),
        "blocked_unscalable_default_policy_count": len(blocked),
        "policy_states": policies,
        "blocked_policy_labels": [policy.get("label") for policy in blocked if policy.get("label")],
        "explicit_heavy_debug_policy_labels": [policy.get("label") for policy in explicit if policy.get("label")],
        "scalable_policy_labels": [policy.get("label") for policy in scalable if policy.get("label")],
    }


def _normalize_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _coerce_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value != 0
    if isinstance(value, str):
        text = value.strip().lower()
        if text in {"1", "true", "yes", "on"}:
            return True
        if text in {"0", "false", "no", "off", ""}:
            return False
    return bool(value)
