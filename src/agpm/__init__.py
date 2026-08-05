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
from .research import (
    expanding_group_zscore,
    grouped_zscore,
    performance_summary,
    strategy_pnl,
    threshold_position,
    walk_forward_splits,
)

__all__ = [
    "CORN",
    "FuturesContract",
    "add_calendar_spread",
    "annualized_log_spread_slope",
    "annualized_spread_slope",
    "contract_pnl",
    "curve_snapshot",
    "expanding_group_zscore",
    "grouped_zscore",
    "long_roll_return",
    "performance_summary",
    "strategy_pnl",
    "threshold_position",
    "walk_forward_splits",
]
