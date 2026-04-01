from __future__ import annotations

import logging
from typing import Any

import numpy as np
import pandas as pd

from momentum_strategy.strategy_config import StrategyParams

logger = logging.getLogger(__name__)


def compute_log_returns(prices: pd.DataFrame) -> pd.DataFrame:
    return np.log(prices / prices.shift(1))


def compute_raw_momentum(prices: pd.DataFrame, params: StrategyParams) -> dict[int, pd.DataFrame]:
    out: dict[int, pd.DataFrame] = {}
    for window in params.momentum_windows:
        mom = np.log(prices.shift(params.skip_days) / prices.shift(window))
        out[window] = mom
    return out


def compute_momentum_score(prices: pd.DataFrame, params: StrategyParams) -> pd.DataFrame:
    raw = compute_raw_momentum(prices, params)
    score = pd.DataFrame(0.0, index=prices.index, columns=prices.columns)
    for window, weight in params.momentum_weights.items():
        score = score + weight * raw[window].fillna(0)
    longest = max(params.momentum_windows)
    valid_mask = raw[longest].notna().any(axis=1)
    return score.loc[valid_mask]


def compute_ewma_vol(log_returns: pd.DataFrame, momentum_index: pd.Index, params: StrategyParams) -> pd.DataFrame:
    lam = params.ewma_lambda
    alpha = 1.0 - lam
    ewma_var = (
        log_returns.fillna(0).pow(2).ewm(alpha=alpha, adjust=False, min_periods=20).mean()
    )
    vol = np.sqrt(ewma_var * 252)
    vol = vol.reindex(momentum_index)
    return vol.clip(lower=0.01)


def compute_zscore(momentum_score: pd.DataFrame) -> pd.DataFrame:
    cross_mean = momentum_score.mean(axis=1)
    cross_std = momentum_score.std(axis=1).replace(0, np.nan)
    z = momentum_score.sub(cross_mean, axis=0).div(cross_std, axis=0)
    return z.clip(lower=-3.0, upper=3.0)


def compute_signal_cs(zscore: pd.DataFrame, params: StrategyParams) -> pd.DataFrame:
    sig = pd.DataFrame(0.0, index=zscore.index, columns=zscore.columns)
    for date in zscore.index:
        row = zscore.loc[date].dropna()
        if len(row) < params.min_assets_for_cs:
            continue
        upper = row.quantile(params.long_quantile)
        lower = row.quantile(params.short_quantile)
        for asset, score in row.items():
            if score >= upper:
                sig.loc[date, asset] = 1.0
            elif score <= lower:
                sig.loc[date, asset] = -1.0
    return sig


def compute_signal_ts(momentum_score: pd.DataFrame, ewma_vol: pd.DataFrame, params: StrategyParams) -> pd.DataFrame:
    common = momentum_score.index.intersection(ewma_vol.index)
    mom = momentum_score.reindex(common)
    vol = ewma_vol.reindex(common)
    raw_ts = mom / vol
    signal_vol = raw_ts.std(axis=1).replace(0, np.nan).ffill()
    scale = params.target_volatility / signal_vol
    ts = raw_ts.mul(scale, axis=0)
    return ts.clip(lower=-3.0, upper=3.0)


def compute_signal_final(signal_cs: pd.DataFrame, signal_ts: pd.DataFrame, params: StrategyParams) -> pd.DataFrame:
    common = signal_cs.index.intersection(signal_ts.index)
    cs = signal_cs.reindex(common)
    ts = signal_ts.reindex(common)
    comb = params.signal_cs_weight * cs + params.signal_ts_weight * ts
    row_max = comb.abs().max(axis=1).replace(0, 1.0)
    return comb.div(row_max, axis=0)


def compute_momentum_pipeline(prices: pd.DataFrame, params: StrategyParams) -> dict[str, Any]:
    """Pipeline complète : prix → signal final (vectorisé)."""
    log_ret = compute_log_returns(prices)
    mom_score = compute_momentum_score(prices, params)
    log_aligned = log_ret.reindex(mom_score.index)
    ewma_vol = compute_ewma_vol(log_aligned, mom_score.index, params)
    z = compute_zscore(mom_score)
    sig_cs = compute_signal_cs(z, params)
    sig_ts = compute_signal_ts(mom_score, ewma_vol, params)
    sig_final = compute_signal_final(sig_cs, sig_ts, params)
    return {
        "log_returns": log_ret,
        "momentum_score": mom_score,
        "ewma_vol": ewma_vol,
        "zscore": z,
        "signal_cs": sig_cs,
        "signal_ts": sig_ts,
        "signal_final": sig_final,
    }


def weights_dollar_neutral_at_date(signal_row: pd.Series) -> pd.Series:
    """Normalise une ligne de signal en poids gross ~1 (L/S dollar-neutral si CS pur)."""
    s = signal_row.fillna(0)
    den = s.abs().sum()
    if den < 1e-12:
        return pd.Series(0.0, index=s.index)
    return s / den


def apply_basic_weight_caps(weights: pd.Series, params: StrategyParams) -> pd.Series:
    """Plafonne |w| par actif puis rescale pour respecter gross leverage max."""
    w = weights.copy()
    cap = params.max_position_size
    lev = params.max_leverage
    w = w.clip(lower=-cap, upper=cap)
    s = w.abs().sum()
    if s > lev and s > 1e-12:
        w = w * (lev / s)
    return w
