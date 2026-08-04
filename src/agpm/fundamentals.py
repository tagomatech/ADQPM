"""Agricultural balance, basis, and information-set analytics."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Hashable

import numpy as np
import pandas as pd


def _numeric_array(name: str, value: object) -> np.ndarray:
    array = np.asarray(value, dtype=float)
    if np.any(~np.isfinite(array)):
        raise ValueError(f"{name} must contain only finite values")
    return array


def _restore_type(result: np.ndarray, values: Sequence[object]):
    series_values = [value for value in values if isinstance(value, pd.Series)]
    if series_values:
        index = series_values[0].index
        if any(not value.index.equals(index) for value in series_values[1:]):
            raise ValueError("Series inputs must share the same index")
        return pd.Series(result, index=index)
    if np.ndim(result) == 0:
        return float(result)
    return result


def _nonnegative(name: str, value: object) -> np.ndarray:
    array = _numeric_array(name, value)
    if np.any(array < 0):
        raise ValueError(f"{name} must be non-negative")
    return array


def ending_stocks(
    beginning_stocks: float | np.ndarray | pd.Series,
    production: float | np.ndarray | pd.Series,
    imports: float | np.ndarray | pd.Series,
    domestic_use: float | np.ndarray | pd.Series,
    exports: float | np.ndarray | pd.Series,
    other_disappearance: float | np.ndarray | pd.Series = 0.0,
):
    """Calculate ending stocks from a physical balance identity.

    All arguments must use the same physical unit and accounting period.
    The identity is ``ending = beginning + production + imports - use -
    exports - other_disappearance``. It is an accounting diagnostic, not a
    forecast model.
    """

    values = [
        beginning_stocks,
        production,
        imports,
        domestic_use,
        exports,
        other_disappearance,
    ]
    arrays = [
        _nonnegative("beginning_stocks", beginning_stocks),
        _nonnegative("production", production),
        _nonnegative("imports", imports),
        _nonnegative("domestic_use", domestic_use),
        _nonnegative("exports", exports),
        _nonnegative("other_disappearance", other_disappearance),
    ]
    beginning, produced, imported, domestic, exported, other = np.broadcast_arrays(
        *arrays
    )
    result = beginning + produced + imported - domestic - exported - other
    if np.any(result < 0):
        raise ValueError("balance identity produces negative ending stocks")
    return _restore_type(result, values)


def stocks_to_use(
    ending_stocks: float | np.ndarray | pd.Series,
    total_use: float | np.ndarray | pd.Series,
):
    """Return ending stocks divided by total use.

    ``total_use`` must be strictly positive. The ratio is a scale-free
    scarcity proxy, not a structural estimate of convenience yield.
    """

    values = [ending_stocks, total_use]
    stocks = _nonnegative("ending_stocks", ending_stocks)
    use = _numeric_array("total_use", total_use)
    if np.any(use <= 0):
        raise ValueError("total_use must be strictly positive")
    stocks, use = np.broadcast_arrays(stocks, use)
    return _restore_type(stocks / use, values)


def cash_basis(
    cash_price: float | np.ndarray | pd.Series,
    futures_price: float | np.ndarray | pd.Series,
):
    """Return local cash basis as cash price minus futures price."""

    values = [cash_price, futures_price]
    cash = _numeric_array("cash_price", cash_price)
    futures = _numeric_array("futures_price", futures_price)
    cash, futures = np.broadcast_arrays(cash, futures)
    return _restore_type(cash - futures, values)


def release_surprise(
    reported: float | np.ndarray | pd.Series,
    market_expectation: float | np.ndarray | pd.Series,
):
    """Return a released value minus the market expectation."""

    values = [reported, market_expectation]
    actual = _numeric_array("reported", reported)
    expected = _numeric_array("market_expectation", market_expectation)
    actual, expected = np.broadcast_arrays(actual, expected)
    return _restore_type(actual - expected, values)


def latest_vintage_at(
    frame: pd.DataFrame,
    decision_time: pd.Timestamp | str,
    *,
    release_time: Hashable = "release_time",
    keys: Sequence[Hashable] = (),
) -> pd.DataFrame:
    """Return observations available at a point-in-time decision timestamp.

    If ``keys`` are supplied, the last released row for each key is retained.
    This is useful for revised official estimates: a later vintage replaces an
    earlier vintage only after its release timestamp. Release timestamps must
    use comparable timezone conventions with ``decision_time``.
    """

    if release_time not in frame:
        raise KeyError(f"Missing release-time column: {release_time}")
    missing_keys = [key for key in keys if key not in frame]
    if missing_keys:
        raise KeyError(f"Missing vintage keys: {missing_keys}")

    cutoff = pd.Timestamp(decision_time)
    released = pd.to_datetime(frame[release_time], errors="raise")
    available = frame.loc[released <= cutoff].copy()
    if available.empty:
        return available.reset_index(drop=True)

    available["_release_order"] = released.loc[available.index]
    available = available.sort_values("_release_order")
    if keys:
        available = available.groupby(
            list(keys), sort=False, dropna=False, as_index=False
        ).tail(1)
    return available.drop(columns="_release_order").reset_index(drop=True)