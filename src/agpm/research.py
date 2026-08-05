"""Research utilities for seasonal signals and auditable backtests."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd


def grouped_zscore(
    values: pd.Series,
    groups: pd.Series,
    *,
    min_count: int = 2,
    ddof: int = 1,
) -> pd.Series:
    """Standardize values within groups using the full supplied sample.

    This is descriptive standardization. It is not point-in-time safe when
    applied to a complete backtest sample; use :func:`expanding_group_zscore`
    for a signal that must use only information available before each row.
    """

    values = pd.Series(values, copy=False)
    groups = pd.Series(groups, index=values.index, copy=False)
    if len(values) != len(groups):
        raise ValueError("values and groups must have the same length")
    if min_count < 1:
        raise ValueError("min_count must be at least one")
    if ddof < 0:
        raise ValueError("ddof must be non-negative")

    mean = values.groupby(groups, sort=False, dropna=False).transform("mean")
    std = values.groupby(groups, sort=False, dropna=False).transform(
        lambda group: group.std(ddof=ddof)
    )
    count = values.groupby(groups, sort=False, dropna=False).transform("count")
    result = (values - mean) / std.replace(0.0, np.nan)
    result[count < min_count] = np.nan
    return result.rename(values.name)


def expanding_group_zscore(
    values: pd.Series,
    groups: pd.Series,
    *,
    min_history: int = 20,
    ddof: int = 1,
) -> pd.Series:
    """Calculate a group-conditional z-score using prior observations only.

    At row ``t`` the mean and standard deviation are calculated from earlier
    rows with the same group label. The current observation is never included
    in its own reference distribution. This is deliberately simple and
    auditable; production research may replace the loop with a faster online
    estimator after testing equivalence.
    """

    values = pd.Series(values, copy=False)
    groups = pd.Series(groups, index=values.index, copy=False)
    if len(values) != len(groups):
        raise ValueError("values and groups must have the same length")
    if min_history < 1:
        raise ValueError("min_history must be at least one")
    if ddof < 0:
        raise ValueError("ddof must be non-negative")

    result = pd.Series(np.nan, index=values.index, dtype=float, name=values.name)
    history: dict[object, list[float]] = {}
    for index, value, group in zip(values.index, values, groups, strict=True):
        observations = history.setdefault(group, [])
        if np.isfinite(value) and len(observations) >= min_history:
            scale = float(np.std(observations, ddof=ddof))
            if scale > 0.0:
                result.loc[index] = (float(value) - float(np.mean(observations))) / scale
        if np.isfinite(value):
            observations.append(float(value))
    return result


def threshold_position(
    score: pd.Series,
    *,
    threshold: float = 0.0,
    max_position: float = 1.0,
) -> pd.Series:
    """Map a score to a bounded long/flat/short target position."""

    score = pd.Series(score, copy=False)
    if threshold < 0:
        raise ValueError("threshold must be non-negative")
    if max_position <= 0:
        raise ValueError("max_position must be positive")
    result = pd.Series(0.0, index=score.index, name="target_position")
    result.loc[score > threshold] = max_position
    result.loc[score < -threshold] = -max_position
    return result


def strategy_pnl(
    target_position: pd.Series,
    period_return: pd.Series,
    *,
    position_lag: int = 1,
    cost_per_unit_turnover: float = 0.0,
) -> pd.DataFrame:
    """Calculate lagged signal P&L with linear turnover costs.

    ``period_return`` must be the return of the explicitly defined
    tradable object (an outright contract, spread, or normalized basis
    exposure). The position is lagged before multiplying by the return, and
    costs are charged on absolute changes in target position.
    """

    target_position = pd.Series(target_position, dtype=float, copy=False)
    period_return = pd.Series(period_return, dtype=float, copy=False)
    if not target_position.index.equals(period_return.index):
        raise ValueError("target_position and period_return must share an index")
    if position_lag < 0:
        raise ValueError("position_lag must be non-negative")
    if cost_per_unit_turnover < 0:
        raise ValueError("cost_per_unit_turnover must be non-negative")

    position = target_position.shift(position_lag).fillna(0.0)
    turnover = position.diff().abs().fillna(position.abs())
    gross = position * period_return
    costs = cost_per_unit_turnover * turnover
    result = pd.DataFrame(
        {
            "target_position": target_position,
            "position": position,
            "period_return": period_return,
            "turnover": turnover,
            "gross_pnl": gross,
            "costs": costs,
            "net_pnl": gross - costs,
        }
    )
    return result


def performance_summary(
    returns: pd.Series,
    *,
    periods_per_year: float = 252.0,
) -> pd.Series:
    """Summarize a return stream without hiding missing observations."""

    returns = pd.Series(returns, dtype=float, copy=False).dropna()
    if returns.empty:
        raise ValueError("returns must contain at least one finite observation")
    if np.any(~np.isfinite(returns)):
        raise ValueError("returns must contain only finite observations")
    if periods_per_year <= 0:
        raise ValueError("periods_per_year must be positive")

    equity = (1.0 + returns).cumprod()
    drawdown = equity / equity.cummax() - 1.0
    volatility = returns.std(ddof=1) * np.sqrt(periods_per_year)
    sharpe = np.nan
    if returns.std(ddof=1) > 0:
        sharpe = returns.mean() / returns.std(ddof=1) * np.sqrt(periods_per_year)
    return pd.Series(
        {
            "observations": len(returns),
            "total_return": equity.iloc[-1] - 1.0,
            "annualized_return": equity.iloc[-1] ** (periods_per_year / len(returns)) - 1.0,
            "annualized_volatility": volatility,
            "sharpe_zero_rate": sharpe,
            "hit_rate": (returns > 0).mean(),
            "max_drawdown": drawdown.min(),
        }
    )


def walk_forward_splits(
    n_observations: int,
    *,
    train_size: int,
    test_size: int,
    step: int | None = None,
) -> list[tuple[np.ndarray, np.ndarray]]:
    """Return expanding-origin rolling train/test index arrays.

    The training window is fixed at ``train_size`` observations in this first
    implementation. Each test window is strictly later than its training
    window. Hyperparameters must be selected inside each training window.
    """

    if n_observations <= 0:
        raise ValueError("n_observations must be positive")
    if train_size <= 0 or test_size <= 0:
        raise ValueError("train_size and test_size must be positive")
    step = test_size if step is None else step
    if step <= 0:
        raise ValueError("step must be positive")

    splits: list[tuple[np.ndarray, np.ndarray]] = []
    test_start = train_size
    while test_start + test_size <= n_observations:
        train = np.arange(test_start - train_size, test_start)
        test = np.arange(test_start, test_start + test_size)
        splits.append((train, test))
        test_start += step
    return splits