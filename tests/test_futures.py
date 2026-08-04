import pandas as pd
import pytest

from agpm.futures import (
    CORN,
    add_calendar_spread,
    annualized_log_spread_slope,
    annualized_spread_slope,
    contract_pnl,
    long_roll_return,
)


def test_corn_tick_value():
    assert CORN.tick_value == pytest.approx(12.50)


def test_long_and_short_pnl():
    assert contract_pnl(0.07) == pytest.approx(350.0)
    assert contract_pnl(-0.07, side=-1) == pytest.approx(350.0)


def test_calendar_spread_sign_convention():
    frame = pd.DataFrame(
        {
            "nearby": [4.50, 4.52],
            "deferred": [4.62, 4.67],
        }
    )
    result = add_calendar_spread(frame, nearby="nearby", deferred="deferred")
    assert result.loc[1, "spread"] == pytest.approx(0.15)
    assert result.loc[1, "spread_pnl"] == pytest.approx(150.0)


def test_long_roll_return_is_negative_in_contango():
    assert long_roll_return(4.50, 4.62) == pytest.approx(4.50 / 4.62 - 1.0)
    assert long_roll_return(4.62, 4.50) > 0

    with pytest.raises(ValueError):
        long_roll_return(0.0, 4.50)


def test_annualized_log_slope_is_a_price_ratio_measure():
    slope = annualized_log_spread_slope(
        deferred_price=4.20,
        nearby_price=4.00,
        deferred_delivery=pd.Timestamp("2026-12-15"),
        nearby_delivery=pd.Timestamp("2026-09-15"),
    )
    assert slope == pytest.approx((365 / 91) * __import__("math").log(4.20 / 4.00))


def test_annualized_slope_requires_forward_delivery():
    slope = annualized_spread_slope(
        deferred_price=4.20,
        nearby_price=4.00,
        deferred_delivery=pd.Timestamp("2026-12-15"),
        nearby_delivery=pd.Timestamp("2026-09-15"),
    )
    assert slope > 0

    with pytest.raises(ValueError):
        annualized_spread_slope(
            deferred_price=4.20,
            nearby_price=4.00,
            deferred_delivery=pd.Timestamp("2026-09-15"),
            nearby_delivery=pd.Timestamp("2026-12-15"),
        )
