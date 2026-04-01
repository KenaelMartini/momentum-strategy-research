from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from momentum_strategy.research.book_forward_attribution import run_attribution


def test_run_attribution_short_overlap(tmp_path: Path) -> None:
    dates = pd.bdate_range("2020-01-01", periods=40)
    rng = np.random.default_rng(0)
    r = rng.normal(0.001, 0.01, size=(len(dates), 4))
    prices = pd.DataFrame(
        100.0 * np.exp(np.cumsum(r, axis=0)),
        index=dates,
        columns=["W", "X", "Y", "Z"],
    )
    pm = tmp_path / "pm.csv"
    prices.to_csv(pm, index_label="date")

    # Short on W with strong positive forward move (artificially set last rows)
    w_json = '{"W":-0.1,"X":0.1}'
    reb = pd.DataFrame(
        {
            "date": [dates[5]],
            "target_weights_json": [w_json],
        }
    )
    rb = tmp_path / "rebal.csv"
    reb.to_csv(rb, index=False)

    detail, summary = run_attribution(rb, pm, horizon=5)
    assert len(detail) == 1
    assert summary["n_rebalances_used"] == 1.0
    assert "leg_long_fwd" in detail.columns
    assert "leg_short_fwd" in detail.columns
