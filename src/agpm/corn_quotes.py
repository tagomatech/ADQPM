"""Quote-unit normalization for CME Corn Bloomberg data."""

from __future__ import annotations

import pandas as pd


def normalize_corn_history(
    frame: pd.DataFrame,
    *,
    source_unit: str = "cents/bushel",
    target_unit: str = "USD/bushel",
) -> pd.DataFrame:
    """Preserve Bloomberg quote values and add normalized USD/bushel values.

    CME grain futures are commonly displayed by Bloomberg in cents per
    bushel. The futures P&L engine uses dollars per bushel, so this conversion
    must be explicit and auditable.
    """

    if "value" not in frame:
        raise KeyError("Expected a Bloomberg history column named 'value'")
    if source_unit != "cents/bushel" or target_unit != "USD/bushel":
        raise ValueError("Only cents/bushel to USD/bushel is currently supported")

    result = frame.copy()
    result["raw_value"] = result["value"]
    result["value"] = result["value"] / 100.0
    result["source_unit"] = source_unit
    result["unit"] = target_unit
    return result
