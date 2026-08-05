import numpy as np
import pandas as pd
import pytest

from agpm.research import (
    expanding_group_zscore,
    grouped_zscore,
    performance_summary,
    strategy_pnl,
    threshold_position,
    walk_forward_splits,
)


def test_grouped_zscore_is_centered_within_groups():
    values = pd.Series([1.0, 3.0, 10.0, 14.0])
    groups = pd.Series(["harvest", "harvest", "storage", "storage"])
    result = grouped_zscore(values, groups)
    np.testing.assert_allclose(result, [-0.70710678, 0.70710678, -0.70710678, 0.70710678])


def test_expanding_group_zscore_does_not_use_current_observation():
    values = pd.Series([1.0, 2.0, 4.0], index=["a", "b", "c"])
    groups = pd.Series(["same", "same", "same"], index=values.index)
    result = expanding_group_zscore(values, groups, min_history=2)
    assert result.iloc[:2].isna().all()
    assert result.iloc[2] == pytest.approx((4.0 - 1.5) / np.std([1.0, 2.0], ddof=1))


def test_threshold_position_is_bounded_and_symmetric():
    score = pd.Series([-2.0, -0.5, 0.5, 2.0])
    result = threshold_position(score, threshold=0.5, max_position=0.75)
    assert result.tolist() == [-0.75, 0.0, 0.0, 0.75]


def test_strategy_pnl_lags_position_and_charges_turnover_costs():
    index = pd.RangeIndex(3)
    target = pd.Series([1.0, 1.0, 0.0], index=index)
    returns = pd.Series([0.10, 0.05, -0.02], index=index)
    result = strategy_pnl(target, returns, cost_per_unit_turnover=0.01)
    assert result["position"].tolist() == [0.0, 1.0, 1.0]
    assert result["net_pnl"].tolist() == pytest.approx([0.0, 0.04, -0.02])


def test_performance_summary_reports_drawdown_and_sharpe():
    summary = performance_summary(pd.Series([0.01, -0.02, 0.01]), periods_per_year=3)
    assert summary["observations"] == 3
    assert summary["total_return"] == pytest.approx((1.01 * 0.98 * 1.01) - 1.0)
    assert summary["max_drawdown"] < 0


def test_walk_forward_splits_have_no_overlap():
    splits = walk_forward_splits(10, train_size=4, test_size=2)
    assert len(splits) == 3
    for train, test in splits:
        assert train[-1] < test[0]
        assert len(train) == 4
        assert len(test) == 2