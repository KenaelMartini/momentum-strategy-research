"""Calendrier de rebalancement aligné sur REBALANCING_FREQUENCY (config / strategy_defaults)."""

from __future__ import annotations

import pandas as pd


def should_rebalance(
    date: pd.Timestamp,
    last_rebal: pd.Timestamp | None,
    frequency: str,
) -> bool:
    """
    True si la date courante ouvre une nouvelle période de rebalancement
    par rapport à ``last_rebal`` (None = jamais rebalancé).
    """
    if last_rebal is None:
        return True
    d = pd.Timestamp(date).normalize()
    prev = pd.Timestamp(last_rebal).normalize()
    f = (frequency or "monthly").strip().lower()

    if f in ("daily", "d"):
        return d > prev

    if f in ("weekly", "w", "week"):
        yw = (d.isocalendar().year, d.isocalendar().week)
        lw = (prev.isocalendar().year, prev.isocalendar().week)
        return yw > lw

    if f in ("monthly", "m", "month"):
        return (d.year * 12 + d.month) > (prev.year * 12 + prev.month)

    if f in ("quarterly", "q", "quarter"):
        dq = (d.year, (d.month - 1) // 3)
        pq = (prev.year, (prev.month - 1) // 3)
        return dq > pq

    # défaut : mensuel (comportement historique)
    return (d.year * 12 + d.month) > (prev.year * 12 + prev.month)
