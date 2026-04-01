from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from momentum_strategy.paths import configs_dir


@dataclass(frozen=True)
class StrategyParams:
    momentum_windows: tuple[int, ...]
    momentum_weights: dict[int, float]
    skip_days: int
    rebalancing_frequency: str
    long_quantile: float
    short_quantile: float
    signal_cs_weight: float
    signal_ts_weight: float
    ewma_lambda: float
    target_volatility: float
    min_assets_for_cs: int
    initial_capital: float
    max_position_size: float
    max_leverage: float
    transaction_cost_bps: float
    slippage_bps: float
    risk_free_rate: float
    backtest_start: str
    backtest_end: str


def _coerce_weights(raw: dict[Any, Any]) -> dict[int, float]:
    out: dict[int, float] = {}
    for k, v in raw.items():
        out[int(k)] = float(v)
    return out


def load_strategy_params(path: Path | None = None) -> StrategyParams:
    p = path or (configs_dir() / "strategy_defaults.yaml")
    raw: dict[str, Any] = yaml.safe_load(p.read_text(encoding="utf-8"))
    windows = tuple(int(x) for x in raw["momentum_windows"])
    wset = set(windows)
    weights = _coerce_weights(raw["momentum_weights"])
    for k in weights:
        if k not in wset:
            raise ValueError(f"Fenêtre {k} dans momentum_weights absente de momentum_windows")
    if set(weights.keys()) != wset:
        raise ValueError("momentum_weights et momentum_windows doivent avoir exactement les mêmes fenêtres")
    sw = sum(weights.values())
    if abs(sw - 1.0) > 1e-6:
        raise ValueError(f"momentum_weights doit sommer à 1.0, obtenu {sw}")
    lq, sq = float(raw["long_quantile"]), float(raw["short_quantile"])
    if not (0 < sq < lq < 1):
        raise ValueError("Quantiles incohérents: attendu 0 < short < long < 1")
    cs_w, ts_w = float(raw["signal_cs_weight"]), float(raw["signal_ts_weight"])
    if abs(cs_w + ts_w - 1.0) > 1e-6:
        raise ValueError("signal_cs_weight + signal_ts_weight doit sommer à 1.0")
    return StrategyParams(
        momentum_windows=windows,
        momentum_weights=weights,
        skip_days=int(raw["skip_days"]),
        rebalancing_frequency=str(raw["rebalancing_frequency"]),
        long_quantile=lq,
        short_quantile=sq,
        signal_cs_weight=cs_w,
        signal_ts_weight=ts_w,
        ewma_lambda=float(raw["ewma_lambda"]),
        target_volatility=float(raw["target_volatility"]),
        min_assets_for_cs=int(raw["min_assets_for_cs"]),
        initial_capital=float(raw["initial_capital"]),
        max_position_size=float(raw["max_position_size"]),
        max_leverage=float(raw["max_leverage"]),
        transaction_cost_bps=float(raw["transaction_cost_bps"]),
        slippage_bps=float(raw["slippage_bps"]),
        risk_free_rate=float(raw["risk_free_rate"]),
        backtest_start=str(raw["backtest_start"]),
        backtest_end=str(raw["backtest_end"]),
    )
