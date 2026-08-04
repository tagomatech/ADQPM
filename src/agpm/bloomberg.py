"""Bloomberg Desktop API adapters for contract-level agricultural data.

The adapter uses xbbg on top of Bloomberg's Desktop API. Raw Bloomberg data
should remain local/private unless redistribution is permitted.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import re
from typing import Iterable

import pandas as pd


CORN_MONTH_CODES = {
    "H": 3,   # March
    "K": 5,   # May
    "N": 7,   # July
    "U": 9,   # September
    "Z": 12,  # December
}


@dataclass(frozen=True)
class CornFuture:
    ticker: str
    month_code: str
    year: int

    @property
    def delivery_month(self) -> pd.Period:
        return pd.Period(year=self.year, month=CORN_MONTH_CODES[self.month_code], freq="M")


@dataclass(frozen=True)
class CornOption:
    ticker: str
    month_code: str
    year: int
    right: str
    strike_cents_per_bushel: float

    @property
    def delivery_month(self) -> pd.Period:
        return pd.Period(year=self.year, month=CORN_MONTH_CODES[self.month_code], freq="M")

    @property
    def strike_dollars_per_bushel(self) -> float:
        return self.strike_cents_per_bushel / 100.0


def _resolve_year(year_token: str, reference_year: int | None = None) -> int:
    """Resolve Bloomberg's one- or two-digit year token.

    Bloomberg examples such as ``U6`` are interpreted relative to the current
    century unless a two-digit year is supplied. The explicit reference year
    is useful for historical or synthetic tests.
    """

    if len(year_token) == 2:
        return 2000 + int(year_token)
    if len(year_token) != 1:
        raise ValueError(f"Unsupported year token: {year_token!r}")

    reference_year = reference_year or date.today().year
    decade = (reference_year // 10) * 10
    return decade + int(year_token)


def parse_corn_future_ticker(
    ticker: str,
    *,
    reference_year: int | None = None,
) -> CornFuture:
    """Parse tickers such as ``C U6 Comdty`` or ``C U26 Comdty``."""

    match = re.fullmatch(
        r"C\s+(?P<month>[HKNUZ])(?P<year>\d{1,2})\s+Comdty",
        ticker.strip(),
        flags=re.IGNORECASE,
    )
    if not match:
        raise ValueError(f"Not a supported CME Corn futures ticker: {ticker!r}")

    month_code = match.group("month").upper()
    return CornFuture(
        ticker=ticker.strip(),
        month_code=month_code,
        year=_resolve_year(match.group("year"), reference_year),
    )


def parse_corn_option_ticker(
    ticker: str,
    *,
    reference_year: int | None = None,
) -> CornOption:
    """Parse tickers such as ``C U6P 500 Comdty``."""

    match = re.fullmatch(
        r"C\s+(?P<month>[HKNUZ])(?P<year>\d{1,2})(?P<right>[CP])\s+(?P<strike>\d+(?:\.\d+)?)\s+Comdty",
        ticker.strip(),
        flags=re.IGNORECASE,
    )
    if not match:
        raise ValueError(f"Not a supported CME Corn option ticker: {ticker!r}")

    month_code = match.group("month").upper()
    return CornOption(
        ticker=ticker.strip(),
        month_code=month_code,
        year=_resolve_year(match.group("year"), reference_year),
        right=match.group("right").upper(),
        strike_cents_per_bushel=float(match.group("strike")),
    )


def fetch_history(
    tickers: Iterable[str],
    *,
    field: str = "PX_SETTLE",
    start_date: str | date,
    end_date: str | date,
    timeout: int = 30_000,
) -> pd.DataFrame:
    """Fetch Bloomberg historical data and return tidy contract-level rows.

    Returns columns ``date``, ``ticker``, ``field``, and ``value``. xbbg is
    imported lazily so ticker parsing and unit tests do not require a terminal.
    """

    ticker_list = list(tickers)
    if not ticker_list:
        raise ValueError("At least one Bloomberg ticker is required")

    try:
        from xbbg import blp
    except ImportError as exc:  # pragma: no cover - environment-dependent
        raise ImportError("Install xbbg and Bloomberg's blpapi package") from exc

    raw = blp.bdh(
        ticker_list,
        field,
        start_date=start_date,
        end_date=end_date,
        timeout=timeout,
    )
    if raw.empty:
        return pd.DataFrame(columns=["date", "ticker", "field", "value"])

    if isinstance(raw.columns, pd.MultiIndex):
        tidy = raw.stack(level=0, future_stack=True).reset_index()
        tidy = tidy.rename(columns={"level_1": "ticker"})
        if field not in tidy.columns:
            value_column = tidy.columns[-1]
        else:
            value_column = field
    else:
        value_column = field if field in raw.columns else raw.columns[0]
        tidy = raw[[value_column]].copy()
        tidy["ticker"] = ticker_list[0]
        tidy = tidy.reset_index()

    date_column = tidy.columns[0]
    tidy = tidy.rename(columns={date_column: "date", value_column: "value"})
    tidy["date"] = pd.to_datetime(tidy["date"]).dt.tz_localize(None)
    tidy["field"] = field
    tidy = tidy[["date", "ticker", "field", "value"]]
    return tidy.sort_values(["ticker", "date"]).reset_index(drop=True)
