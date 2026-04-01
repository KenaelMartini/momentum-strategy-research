from __future__ import annotations

from pathlib import Path

import pandas as pd

from momentum_strategy.signals.momentum import compute_momentum_pipeline
from momentum_strategy.strategy_config import load_strategy_params


def test_momentum_pipeline_runs(
    synthetic_prices: pd.DataFrame,
    fixtures_dir: Path,
) -> None:
    params = load_strategy_params(fixtures_dir / "strategy_test.yaml")
    out = compute_momentum_pipeline(synthetic_prices, params)
    sig = out["signal_final"]
    assert not sig.empty
    assert sig.shape[1] == 4
    assert float(sig.abs().max(axis=1).max()) <= 1.0 + 1e-9
