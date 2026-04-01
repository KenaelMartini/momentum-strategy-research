from __future__ import annotations

import json
from dataclasses import dataclass

import momentum_strategy.runtime_config  # noqa: F401

from momentum_strategy.research.sensitivity_batch import _extract_phase0_diagnostics


@dataclass
class _FakeStat:
    market_regime_effective: str


class _FakePortfolio:
    def __init__(self) -> None:
        self.history = [_FakeStat("TREND"), _FakeStat("TREND"), _FakeStat("TRANSITION")]


class _FakeSignalGen:
    last_diagnostics = {
        "signal_risk_adjust_applied": True,
        "risk_parity_applied": True,
        "gross_before_risk_parity": 0.9,
        "gross_after_risk_parity": 1.1,
    }


class _FakeEngine:
    def __init__(self) -> None:
        self.signal_gen = _FakeSignalGen()
        self.portfolio = _FakePortfolio()


def test_extract_phase0_diagnostics_contains_regime_and_flags() -> None:
    d = _extract_phase0_diagnostics(_FakeEngine())  # type: ignore[arg-type]
    assert d["diag_signal_risk_adjust_applied"] is True
    assert d["diag_risk_parity_applied"] is True
    counts = json.loads(d["diag_market_regime_effective_counts"])
    assert counts["TREND"] == 2
    assert counts["TRANSITION"] == 1
