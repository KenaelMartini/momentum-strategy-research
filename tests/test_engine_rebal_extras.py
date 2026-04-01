from __future__ import annotations

import json

import pytest

from momentum_strategy.event_driven.engine import rebalance_book_extras


def test_rebalance_book_extras_counts_and_json() -> None:
    sig = {
        "n_long_candidates": 6,
        "n_short_candidates": 4,
        "n_selected_positions": 8,
        "n_signal_universe": 50,
    }
    w = {"AAA": 0.1, "BBB": -0.05, "CCC": 0.005}
    x = rebalance_book_extras(sig, w)
    assert x["n_target_long"] == 1
    assert x["n_target_short"] == 1
    assert x["gross_long"] == pytest.approx(0.1)
    assert x["gross_short"] == pytest.approx(0.05)
    d = json.loads(x["target_weights_json"])
    assert d["AAA"] == 0.1
    assert d["BBB"] == -0.05
