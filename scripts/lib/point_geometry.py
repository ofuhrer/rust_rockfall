"""Shared LV95 point parsing and simple geometry helpers."""

from __future__ import annotations

import json
import math
from typing import Any


def xy_from_row(
    row: dict[str, Any],
    *,
    x_key: str = "x_m",
    y_key: str = "y_m",
    fallback_key: str = "release_cell_center_lv95_m",
) -> tuple[float, float] | None:
    try:
        x = float(row.get(x_key) or "")
        y = float(row.get(y_key) or "")
    except (TypeError, ValueError):
        center = row.get(fallback_key)
        if not center:
            return None
        try:
            values = json.loads(center) if isinstance(center, str) else center
            x = float(values[0])
            y = float(values[1])
        except (TypeError, ValueError, json.JSONDecodeError, IndexError):
            return None
    if not math.isfinite(x) or not math.isfinite(y):
        return None
    return x, y


def centroid_xy(rows: list[dict[str, Any]], *, x_key: str = "x_m", y_key: str = "y_m") -> dict[str, float]:
    points = [xy for row in rows if (xy := xy_from_row(row, x_key=x_key, y_key=y_key)) is not None]
    if not points:
        return {"x_m": 0.0, "y_m": 0.0}
    return {
        "x_m": round(sum(x for x, _ in points) / len(points), 6),
        "y_m": round(sum(y for _, y in points) / len(points), 6),
    }


def distance_xy(left: dict[str, float], right: dict[str, float]) -> float:
    return math.hypot(
        float(left.get("x_m", 0.0)) - float(right.get("x_m", 0.0)),
        float(left.get("y_m", 0.0)) - float(right.get("y_m", 0.0)),
    )


def point_in_bounds(x: float, y: float, bounds: dict[str, Any]) -> bool:
    return (
        float(bounds.get("xmin", 0.0)) <= x <= float(bounds.get("xmax", 0.0))
        and float(bounds.get("ymin", 0.0)) <= y <= float(bounds.get("ymax", 0.0))
    )
