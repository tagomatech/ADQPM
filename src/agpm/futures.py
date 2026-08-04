"""Contract-aware futures and calendar-spread analytics.

The functions in this module intentionally keep units explicit. Prices are
quoted in currency per physical unit and P&L is returned in currency.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Hashable

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class FuturesContract:
    """Static contract specifications required for mark-to-market P&L."""

    name: str
    multiplier: float
    tick_size: float
    currency: str = "USD"
    unit: str = "bushel"

    @property
    def tick_value(self) -> float:
        return self.multiplier * self.tick_size


CORN = FuturesContract(
    name="CBOT Corn",
    multiplier=5_000.0,
    tick_size=0.0025,
)


def contract_pnl(
    price_change: float | np.ndarray | pd.Series,
    *,
    contracts: float = 1.0,
    multiplier: float = CORN.multiplier,
    side: int = 1,
) -> float | np.ndarray | pd.Series:
    """Return mark-to-market P&L for a futures position.

    Parameters
    ----------
    price_change:
        Change in quoted price, in currency per physical unit.
    contracts:
        Number of contracts. Use ``side`` for direction.
    multiplier:
        Physical units per contract.
    side:
        ``+1`` for long and ``-1`` for short.
    """

    if side not in (-1, 1):
        raise ValueError("side must be +1 or -1")
    return side * contracts * multiplier * price_change


def add_calendar_spread(
    frame: pd.DataFrame,
    *,
    nearby: Hashable,
    deferred: Hashable,
    multiplier: float = CORN.multiplier,
    spread_name: str = "spread",
) -> pd.DataFrame:
    """Add spread and long-deferred-minus-nearby P&L columns.

    The input must be ordered chronologically. The first observation has no
    previous-day P&L and is assigned NaN.
    """

    missing = [column for column in (nearby, deferred) if column not in frame]
    if missing:
        raise KeyError(f"Missing price columns: {missing}")

    result = frame.copy()
    result[spread_name] = result[deferred] - result[nearby]
    result["spread_pnl"] = contract_pnl(
        result[spread_name].diff(), multiplier=multiplier
    )
    return result


def long_roll_return(
    old_price: float | np.ndarray | pd.Series,
    new_price: float | np.ndarray | pd.Series,
) -> float | np.ndarray | pd.Series:
    """Return the price-ratio return from rolling a long position.

    The position is replaced at the same observation time, so this isolates the
    relative price of the old and new delivery months. Contango produces a
    negative value for a long roll under this convention.
    """

    old = np.asarray(old_price)
    new = np.asarray(new_price)
    if np.any(~np.isfinite(old)) or np.any(~np.isfinite(new)):
        raise ValueError("roll prices must be finite")
    if np.any(old <= 0) or np.any(new <= 0):
        raise ValueError("roll prices must be positive")
    result = old / new - 1.0
    if np.ndim(result) == 0:
        return float(result)
    if isinstance(old_price, pd.Series):
        return pd.Series(result, index=old_price.index, name=old_price.name)
    return result


def annualized_log_spread_slope(
    *,
    deferred_price: float | np.ndarray | pd.Series,
    nearby_price: float | np.ndarray | pd.Series,
    deferred_delivery: pd.Timestamp,
    nearby_delivery: pd.Timestamp,
    day_count: float = 365.0,
) -> float | np.ndarray | pd.Series:
    """Return the annualized logarithmic deferred/nearby curve slope.

    This is a descriptive, continuously compounded price-ratio measure. It is
    not a decomposition of financing, storage cost, and convenience yield.
    """

    deferred_delivery = pd.Timestamp(deferred_delivery)
    nearby_delivery = pd.Timestamp(nearby_delivery)
    days = (deferred_delivery - nearby_delivery).days
    if days <= 0:
        raise ValueError("deferred delivery must be after nearby delivery")
    deferred = np.asarray(deferred_price)
    nearby = np.asarray(nearby_price)
    if np.any(~np.isfinite(deferred)) or np.any(~np.isfinite(nearby)):
        raise ValueError("curve prices must be finite")
    if np.any(deferred <= 0) or np.any(nearby <= 0):
        raise ValueError("curve prices must be positive")
    result = np.log(deferred / nearby) * day_count / days
    if np.ndim(result) == 0:
        return float(result)
    if isinstance(deferred_price, pd.Series):
        return pd.Series(result, index=deferred_price.index, name=deferred_price.name)
    return result


def curve_snapshot(
    frame: pd.DataFrame,
    *,
    price: Hashable,
    delivery: Hashable,
) -> pd.DataFrame:
    """Return adjacent-contract curve diagnostics for one observation."""

    required = [price, delivery]
    missing = [column for column in required if column not in frame]
    if missing:
        raise KeyError(f"Missing curve columns: {missing}")

    result = frame.copy().sort_values(delivery).reset_index(drop=True)
    result["price_change"] = result[price].diff()
    result["days_to_next"] = result[delivery].shift(-1) - result[delivery]
    result["next_spread"] = result[price].shift(-1) - result[price]
    result["annualized_slope"] = (
        result["next_spread"]
        / result["days_to_next"].dt.days
        * 365.0
    )
    return result


def annualized_spread_slope(
    *,
    deferred_price: float,
    nearby_price: float,
    deferred_delivery: pd.Timestamp,
    nearby_delivery: pd.Timestamp,
    day_count: float = 365.0,
) -> float:
    """Annualize a deferred-minus-nearby price difference.

    This is a descriptive curve slope. It is not, by itself, a theoretical
    net cost-of-carry estimate.
    """

    deferred_delivery = pd.Timestamp(deferred_delivery)
    nearby_delivery = pd.Timestamp(nearby_delivery)
    days = (deferred_delivery - nearby_delivery).days
    if days <= 0:
        raise ValueError("deferred delivery must be after nearby delivery")
    return (deferred_price - nearby_price) / days * day_count
