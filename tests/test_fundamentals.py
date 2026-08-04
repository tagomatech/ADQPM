import numpy as np
import pandas as pd
import pytest

from agpm.fundamentals import (
    cash_basis,
    ending_stocks,
    latest_vintage_at,
    release_surprise,
    stocks_to_use,
)


def test_ending_stocks_balance_identity():
    assert ending_stocks(100, 500, 20, 300, 250) == pytest.approx(70)


def test_ending_stocks_preserves_series_index():
    beginning = pd.Series([100, 120], index=["2025", "2026"])
    result = ending_stocks(beginning, 500, 20, 300, 250)
    pd.testing.assert_series_equal(
        result,
        pd.Series([70.0, 90.0], index=beginning.index),
    )


def test_stocks_to_use_and_basis():
    assert stocks_to_use(70, 550) == pytest.approx(70 / 550)
    np.testing.assert_allclose(cash_basis(np.array([4.20, 4.30]), 4.25), [-0.05, 0.05])


def test_release_surprise_is_reported_minus_expectation():
    assert release_surprise(1.72, 1.84) == pytest.approx(-0.12)


def test_latest_vintage_respects_decision_time_and_revisions():
    frame = pd.DataFrame(
        {
            "release_time": pd.to_datetime(
                ["2026-08-12 17:00", "2026-09-11 17:00", "2026-09-11 17:00"]
            ),
            "marketing_year": [2026, 2026, 2027],
            "ending_stocks": [1.90, 1.75, 2.10],
        }
    )
    result = latest_vintage_at(
        frame,
        "2026-09-01 12:00",
        keys=["marketing_year"],
    )
    assert result["ending_stocks"].tolist() == [1.90]

    revised = latest_vintage_at(
        frame,
        "2026-09-12 12:00",
        keys=["marketing_year"],
    )
    assert revised.sort_values("marketing_year")["ending_stocks"].tolist() == [1.75, 2.10]


def test_invalid_physical_inputs_are_rejected():
    with pytest.raises(ValueError, match="non-negative"):
        ending_stocks(100, -1, 0, 10, 10)
    with pytest.raises(ValueError, match="strictly positive"):
        stocks_to_use(10, 0)