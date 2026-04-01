from __future__ import annotations

from pathlib import Path

import pytest

from momentum_strategy.universe import Universe, load_universe


def test_load_universe_fixture(fixtures_dir: Path) -> None:
    u = load_universe(fixtures_dir / "universe_test.yaml")
    assert isinstance(u, Universe)
    assert u.stocks == ("AAA", "BBB", "CCC", "DDD")
    assert u.futures == ()


def test_universe_fetch_lists(fixtures_dir: Path) -> None:
    u = load_universe(fixtures_dir / "universe_test.yaml")
    assert u.all_symbols_for_fetch(True, False) == ["AAA", "BBB", "CCC", "DDD"]
    assert u.all_symbols_for_fetch(False, True) == []
    with pytest.raises(ValueError):
        u.all_symbols_for_fetch(True, True)
