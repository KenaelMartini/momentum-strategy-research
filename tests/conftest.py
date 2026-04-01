from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from momentum_strategy.universe import Universe, load_universe

FIXTURES = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES


def _write_synthetic_raw_stocks(raw_dir: Path, symbols: list[str], *, n_days: int = 320) -> None:
    raw_dir.mkdir(parents=True, exist_ok=True)
    idx = pd.bdate_range("2020-01-01", periods=n_days)
    for i, sym in enumerate(symbols):
        rng = np.random.default_rng(42 + i)
        close = 100.0 + np.cumsum(rng.normal(0.05, 1.0, len(idx)))
        open_ = np.r_[close[0], close[:-1]]
        high = np.maximum(open_, close) + 0.2
        low = np.minimum(open_, close) - 0.2
        vol = rng.integers(1_000_000, 2_000_000, len(idx))
        df = pd.DataFrame(
            {"open": open_, "high": high, "low": low, "close": close, "volume": vol},
            index=idx,
        )
        df.to_csv(raw_dir / f"stock_{sym}.csv", index_label="date")


@pytest.fixture
def universe_test(fixtures_dir: Path) -> Universe:
    return load_universe(fixtures_dir / "universe_test.yaml")


@pytest.fixture
def synthetic_raw_and_universe(tmp_path: Path, universe_test: Universe) -> tuple[Path, Universe]:
    raw = tmp_path / "raw"
    _write_synthetic_raw_stocks(raw, list(universe_test.stocks), n_days=400)
    return raw, universe_test


@pytest.fixture
def synthetic_prices(synthetic_raw_and_universe: tuple[Path, Universe]) -> pd.DataFrame:
    raw, u = synthetic_raw_and_universe
    cols = {}
    for sym in u.stocks:
        df = pd.read_csv(raw / f"stock_{sym}.csv", index_col=0, parse_dates=True)
        cols[sym] = df["close"]
    return pd.DataFrame(cols).sort_index().ffill()
