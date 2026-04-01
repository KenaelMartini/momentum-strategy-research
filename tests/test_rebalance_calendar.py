from __future__ import annotations

import pandas as pd

from momentum_strategy.event_driven.rebalance_calendar import should_rebalance


def test_should_rebalance_first_day() -> None:
    d = pd.Timestamp("2020-03-15")
    assert should_rebalance(d, None, "monthly") is True


def test_monthly_advances_on_new_month() -> None:
    last = pd.Timestamp("2020-01-10")
    assert should_rebalance(pd.Timestamp("2020-01-20"), last, "monthly") is False
    assert should_rebalance(pd.Timestamp("2020-02-03"), last, "monthly") is True


def test_quarterly() -> None:
    last = pd.Timestamp("2020-01-15")
    assert should_rebalance(pd.Timestamp("2020-03-30"), last, "quarterly") is False
    assert should_rebalance(pd.Timestamp("2020-04-01"), last, "quarterly") is True


def test_weekly_same_week() -> None:
    last = pd.Timestamp("2020-06-01")
    assert should_rebalance(pd.Timestamp("2020-06-03"), last, "weekly") is False


def test_daily() -> None:
    last = pd.Timestamp("2020-06-01")
    assert should_rebalance(pd.Timestamp("2020-06-02"), last, "daily") is True
