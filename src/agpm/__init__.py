"""Reusable analytics for the agriculture derivatives research monograph."""

from .futures import (
    CORN,
    FuturesContract,
    add_calendar_spread,
    annualized_log_spread_slope,
    annualized_spread_slope,
    contract_pnl,
    curve_snapshot,
    long_roll_return,
)

__all__ = [
    "CORN",
    "FuturesContract",
    "add_calendar_spread",
    "annualized_log_spread_slope",
    "annualized_spread_slope",
    "contract_pnl",
    "curve_snapshot",
    "long_roll_return",
]
