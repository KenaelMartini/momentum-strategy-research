"""Contrats institutionnels : champs d'audit dans PortfolioStats ; batch sensibilité --write-artifacts."""

from __future__ import annotations

from dataclasses import fields
from pathlib import Path

from momentum_strategy.paths import project_root
from momentum_strategy.research.sensitivity_batch import _resolve_under_project

import pytest

# Garder aligné avec docs/research/REBAL_BOOK_RISK_GUIDE.md section 7
_INSTITUTIONAL_AUDIT_FIELDS = frozenset(
    {
        "trading_suspended",
        "dd_max_stop",
        "suspended_days",
        "signal_generation_reason",
        "defensive_flat_phase",
        "defensive_flat_reason",
        "gross_after_old_regime_filter",
        "gross_after_market_overlay",
        "risk_regime_name",
        "market_regime_effective",
        "rebalancing_day",
        "n_orders",
        "final_turnover",
    }
)


def test_resolve_presets_path_anchors_to_project_root() -> None:
    root = project_root()
    resolved = _resolve_under_project(
        Path("configs/strategy_defaults.yaml"),
        root=root,
        what="test",
    )
    assert resolved.is_file()
    assert resolved.name == "strategy_defaults.yaml"


def test_portfolio_stats_includes_institutional_audit_fields() -> None:
    from momentum_strategy.event_driven.events import PortfolioStats

    names = {f.name for f in fields(PortfolioStats)}
    missing = _INSTITUTIONAL_AUDIT_FIELDS - names
    assert not missing, f"PortfolioStats manque des champs documentés: {missing}"


def test_sensitivity_run_one_write_artifacts_calls_save_results(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    import momentum_strategy.research.sensitivity_batch as sb

    instances: list[object] = []

    class FakeEngine:
        def __init__(self, **kwargs: object) -> None:
            instances.append(self)
            self.final_metrics = {
                "cagr": 0.0,
                "sharpe": 0.0,
                "max_dd": 0.0,
                "calmar": 0.0,
                "final_value": 100_000.0,
                "n_trades": 0,
                "avg_turnover": 0.0,
            }

        def run(self) -> None:
            return None

        def save_results(self) -> dict:
            self._save_called = True
            return {}

    monkeypatch.setattr(sb, "EventDrivenEngine", FakeEngine)
    data = tmp_path / "pm.csv"
    data.write_text("date,A\n2020-01-02,100\n2020-01-03,100\n", encoding="utf-8")
    out = tmp_path / "scenario_a"

    sb._run_one("scen_fast", out, data, "2020-01-02", "2020-01-03", {}, write_artifacts=False)
    eng_fast = instances[-1]
    assert not getattr(eng_fast, "_save_called", False)

    sb._run_one("scen_slow", tmp_path / "scenario_b", data, "2020-01-02", "2020-01-03", {}, write_artifacts=True)
    eng_slow = instances[-1]
    assert getattr(eng_slow, "_save_called", False) is True
