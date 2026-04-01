from __future__ import annotations

from pathlib import Path

from momentum_strategy.strategy_config import load_strategy_params


def test_load_strategy_fixture(fixtures_dir: Path) -> None:
    p = load_strategy_params(fixtures_dir / "strategy_test.yaml")
    assert p.momentum_windows == (5, 10, 15, 20)
    assert abs(sum(p.momentum_weights.values()) - 1.0) < 1e-9
