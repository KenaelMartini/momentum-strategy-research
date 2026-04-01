from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from momentum_strategy.data.matrix import load_price_matrix
from momentum_strategy.paths import project_root
from momentum_strategy.signals.momentum import (
    apply_basic_weight_caps,
    compute_momentum_pipeline,
    weights_dollar_neutral_at_date,
)
from momentum_strategy.strategy_config import StrategyParams, load_strategy_params

logger = logging.getLogger(__name__)


def run_minimal_monthly_backtest(
    prices: pd.DataFrame,
    signal_final: pd.DataFrame,
    params: StrategyParams,
    *,
    apply_caps: bool = True,
) -> pd.DataFrame:
    """
    Rebalancement en fin de mois (dernier jour de séance du mois).
    Rendement du jour = positions détenues en début de journée (poids post-rebalance veille).
    Coût = (tc + slippage) × demi-turnover sur les jours de rebalance.
    """
    ret = prices.pct_change()
    rebal = prices.groupby(prices.index.to_period("M")).tail(1).index
    rebal = rebal.intersection(signal_final.index)

    w = pd.Series(0.0, index=prices.columns)
    rows: list[dict] = []
    cost_rate = (params.transaction_cost_bps + params.slippage_bps) / 10000.0

    for i, dt in enumerate(prices.index):
        if i == 0:
            rows.append({"date": dt, "port_ret": 0.0, "turnover": 0.0, "cost": 0.0})
            continue
        r_t = ret.loc[dt]
        p_ret = float((w * r_t.fillna(0)).sum())
        to = 0.0
        cost = 0.0
        if dt in rebal:
            raw = signal_final.loc[dt].reindex(prices.columns)
            w_new = weights_dollar_neutral_at_date(raw)
            if apply_caps:
                w_new = apply_basic_weight_caps(w_new, params)
            to = float((w_new - w).abs().sum() / 2.0)
            cost = to * cost_rate
            p_ret -= cost
            w = w_new
        rows.append({"date": dt, "port_ret": p_ret, "turnover": to, "cost": cost})

    out = pd.DataFrame(rows).set_index("date")
    out["equity"] = params.initial_capital * (1 + out["port_ret"]).cumprod()
    return out


def run_default_minimal_backtest(
    *,
    price_matrix_path: Path | None = None,
    params_path: Path | None = None,
    apply_caps: bool = True,
) -> tuple[pd.DataFrame, dict]:
    root = project_root()
    params = load_strategy_params(params_path)
    prices = load_price_matrix(price_matrix_path)
    pipe = compute_momentum_pipeline(prices, params)
    sig = pipe["signal_final"]
    bt = run_minimal_monthly_backtest(prices, sig, params, apply_caps=apply_caps)
    summary = {
        "n_days": len(bt),
        "total_return": float(bt["equity"].iloc[-1] / params.initial_capital - 1) if len(bt) else 0.0,
        "mean_daily_ret": float(bt["port_ret"].mean()) if len(bt) else 0.0,
    }
    return bt, summary
