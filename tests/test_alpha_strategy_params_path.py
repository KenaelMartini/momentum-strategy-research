"""strategy_params_path : même StrategyParams pour historique requis et pipeline momentum."""

from __future__ import annotations

import logging
from pathlib import Path

import pytest

_MINIMAL_STRATEGY_YAML = """
momentum_windows: [21, 63, 126, 252]
momentum_weights:
  21: 0.10
  63: 0.20
  126: 0.30
  252: 0.40
skip_days: 21
rebalancing_frequency: "monthly"
long_quantile: 0.80
short_quantile: 0.20
signal_cs_weight: 0.7
signal_ts_weight: 0.3
ewma_lambda: 0.94
target_volatility: 0.15
min_assets_for_cs: 5
initial_capital: 100000
max_position_size: 0.10
ed_max_leverage: 1
ed_signal_entry_eps: 0.02
ed_short_notional_scale: 0.5
event_driven_n_long: 6
event_driven_n_short: 0
max_leverage: 1.5
transaction_cost_bps: 10
slippage_bps: 5
risk_free_rate: 0.05
backtest_start: "2015-01-01"
backtest_end: "2024-12-31"
"""


def test_momentum_signal_generator_v2_loads_strategy_params_path(tmp_path: Path) -> None:
    logging.disable(logging.CRITICAL)
    try:
        from momentum_strategy.event_driven_risk import EventDrivenRiskManager, MomentumSignalGeneratorV2

        p = tmp_path / "custom_strategy.yaml"
        p.write_text(_MINIMAL_STRATEGY_YAML.strip(), encoding="utf-8")

        class DummyHandler:
            pass

        rm = EventDrivenRiskManager(100_000.0)
        gen = MomentumSignalGeneratorV2(DummyHandler(), rm, strategy_params_path=p)
        assert gen._strategy_params.signal_cs_weight == pytest.approx(0.7)
        assert gen._strategy_params.signal_ts_weight == pytest.approx(0.3)
        assert gen.skip_days == 21
        assert gen.max_window == 252
        assert gen._ewma_lambda == pytest.approx(0.94)
    finally:
        logging.disable(logging.NOTSET)


def test_fist_compat_run_full_pipeline_uses_strategy_params_without_override() -> None:
    from momentum_strategy.signals.fist_compat import MomentumSignalGenerator
    from momentum_strategy.strategy_config import load_strategy_params

    import pandas as pd

    params = load_strategy_params()
    prices = pd.DataFrame({"A": [100.0, 101.0, 102.0, 103.0, 104.0] * 60})
    gen = MomentumSignalGenerator(prices)
    out = gen.run_full_pipeline(strategy_params=params)
    assert "signal_final" in out
    assert not out["signal_final"].empty
