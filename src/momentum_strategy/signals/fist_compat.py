"""Compatibilité avec l'API Fist `MomentumSignalGenerator` pour `event_driven_risk`."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

import pandas as pd

from momentum_strategy.signals.momentum import compute_momentum_pipeline
from momentum_strategy.strategy_config import StrategyParams, load_strategy_params


class MomentumSignalGenerator:
    """Même surface que Fist `strategies.momentum.momentum_signal.MomentumSignalGenerator`."""

    def __init__(self, price_matrix: pd.DataFrame) -> None:
        self.prices = price_matrix

    def run_full_pipeline(
        self,
        *,
        strategy_params: StrategyParams | None = None,
        cs_weight: float | None = None,
        ts_weight: float | None = None,
    ) -> dict[str, Any]:
        """Pipeline complet. Si ``strategy_params`` est fourni, il pilote tout le signal (dont CS/TS).

        ``cs_weight`` / ``ts_weight`` ne s'appliquent que s'ils sont non-None (override ponctuel).
        """
        params = strategy_params if strategy_params is not None else load_strategy_params()
        if cs_weight is not None or ts_weight is not None:
            params = replace(
                params,
                signal_cs_weight=float(cs_weight if cs_weight is not None else params.signal_cs_weight),
                signal_ts_weight=float(ts_weight if ts_weight is not None else params.signal_ts_weight),
            )
        return compute_momentum_pipeline(self.prices, params)
