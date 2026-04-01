from __future__ import annotations

from pathlib import Path

from momentum_strategy.backtest.minimal import run_default_minimal_backtest
from momentum_strategy.data.matrix import build_price_matrix_pipeline
from momentum_strategy.universe import Universe


def test_minimal_backtest_end_to_end(
    tmp_path: Path,
    synthetic_raw_and_universe: tuple[Path, Universe],
    fixtures_dir: Path,
) -> None:
    raw, u = synthetic_raw_and_universe
    proc = tmp_path / "processed"
    pm = build_price_matrix_pipeline(u, stocks_only=True, raw_dir=raw, processed_dir=proc)
    csv_path = proc / "price_matrix.csv"
    assert csv_path.exists()

    bt, summary = run_default_minimal_backtest(
        price_matrix_path=csv_path,
        params_path=fixtures_dir / "strategy_test.yaml",
        apply_caps=False,
    )
    assert len(bt) == len(pm)
    assert "equity" in bt.columns
    assert summary["n_days"] == len(bt)
    assert bt["equity"].iloc[-1] > 0
