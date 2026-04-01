from __future__ import annotations

from pathlib import Path

from momentum_strategy.data.matrix import build_price_matrix_pipeline, load_price_matrix
from momentum_strategy.universe import Universe


def test_build_matrix_from_raw(
    tmp_path: Path,
    synthetic_raw_and_universe: tuple[Path, Universe],
) -> None:
    raw, u = synthetic_raw_and_universe
    proc = tmp_path / "processed"
    pm = build_price_matrix_pipeline(
        u,
        stocks_only=True,
        raw_dir=raw,
        processed_dir=proc,
    )
    assert pm.shape[1] == 4
    assert not pm.isna().all().any()
    loaded = load_price_matrix(proc / "price_matrix.csv")
    assert loaded.shape == pm.shape
