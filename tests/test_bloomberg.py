import pandas as pd
import pytest

from agpm.bloomberg import (
    parse_corn_future_ticker,
    parse_corn_option_ticker,
)


def test_parse_corn_future_ticker():
    contract = parse_corn_future_ticker("C U6 Comdty", reference_year=2026)
    assert contract.month_code == "U"
    assert contract.year == 2026
    assert contract.delivery_month == pd.Period("2026-09", freq="M")


def test_parse_two_digit_corn_future_ticker():
    contract = parse_corn_future_ticker("C Z26 Comdty")
    assert contract.year == 2026
    assert contract.delivery_month.month == 12


def test_parse_corn_put_option_ticker():
    option = parse_corn_option_ticker("C U6P 500 Comdty", reference_year=2026)
    assert option.right == "P"
    assert option.strike_cents_per_bushel == pytest.approx(500.0)
    assert option.strike_dollars_per_bushel == pytest.approx(5.0)


def test_reject_unsupported_contract_month():
    with pytest.raises(ValueError):
        parse_corn_future_ticker("C F6 Comdty", reference_year=2026)
