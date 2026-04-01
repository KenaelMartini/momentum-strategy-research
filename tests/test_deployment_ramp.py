"""Rampe de déploiement : ancre, mode calendrier / rebalance, nettoyage d'état."""

from __future__ import annotations

import pandas as pd
import pytest


def test_mark_deployment_ramp_start_noop_when_all_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    import momentum_strategy.event_driven_risk as edr

    monkeypatch.setattr(edr, "SUSPENSION_REENTRY_RAMP_ENABLED", False)
    monkeypatch.setattr(edr, "POST_DEPLOYMENT_RISK_ADJUST_CALENDAR_DAYS", 0)
    rm = edr.EventDrivenRiskManager(100_000.0)
    rm.mark_deployment_ramp_start(pd.Timestamp("2020-06-01"))
    assert not hasattr(rm, "_deployment_ramp_anchor_date")


def test_note_rebalance_increments_counter(monkeypatch: pytest.MonkeyPatch) -> None:
    import momentum_strategy.event_driven_risk as edr

    monkeypatch.setattr(edr, "SUSPENSION_REENTRY_RAMP_ENABLED", True)
    monkeypatch.setattr(edr, "POST_DEPLOYMENT_RISK_ADJUST_CALENDAR_DAYS", 0)
    rm = edr.EventDrivenRiskManager(100_000.0)
    rm.mark_deployment_ramp_start(pd.Timestamp("2020-06-01"))
    rm.note_rebalance_completed_for_deployment_ramp()
    rm.note_rebalance_completed_for_deployment_ramp()
    assert rm._deployment_ramp_rebalances == 2


def test_maybe_clear_calendar_when_days_exceed_scales(monkeypatch: pytest.MonkeyPatch) -> None:
    import momentum_strategy.event_driven_risk as edr

    monkeypatch.setattr(edr, "SUSPENSION_REENTRY_RAMP_ENABLED", True)
    monkeypatch.setattr(edr, "DEPLOYMENT_RAMP_SCHEDULE", "calendar")
    monkeypatch.setattr(edr, "SUSPENSION_REENTRY_RAMP_SCALES", (0.5, 1.0))
    monkeypatch.setattr(edr, "POST_DEPLOYMENT_RISK_ADJUST_CALENDAR_DAYS", 0)
    rm = edr.EventDrivenRiskManager(100_000.0)
    rm.mark_deployment_ramp_start(pd.Timestamp("2020-01-02"))
    rm._maybe_clear_deployment_ramp_anchor(pd.Timestamp("2020-01-02"))
    assert hasattr(rm, "_deployment_ramp_anchor_date")
    rm._maybe_clear_deployment_ramp_anchor(pd.Timestamp("2020-01-04"))
    assert not hasattr(rm, "_deployment_ramp_anchor_date")


def test_maybe_clear_rebalance_when_count_exceeds_scales(monkeypatch: pytest.MonkeyPatch) -> None:
    import momentum_strategy.event_driven_risk as edr

    monkeypatch.setattr(edr, "SUSPENSION_REENTRY_RAMP_ENABLED", True)
    monkeypatch.setattr(edr, "DEPLOYMENT_RAMP_SCHEDULE", "rebalance")
    monkeypatch.setattr(edr, "SUSPENSION_REENTRY_RAMP_REBALANCE_SCALES", (0.5, 1.0))
    monkeypatch.setattr(edr, "POST_DEPLOYMENT_RISK_ADJUST_CALENDAR_DAYS", 0)
    rm = edr.EventDrivenRiskManager(100_000.0)
    rm.mark_deployment_ramp_start(pd.Timestamp("2020-01-02"))
    rm.note_rebalance_completed_for_deployment_ramp()
    rm._maybe_clear_deployment_ramp_anchor(pd.Timestamp("2020-01-02"))
    assert hasattr(rm, "_deployment_ramp_anchor_date")
    rm.note_rebalance_completed_for_deployment_ramp()
    rm._maybe_clear_deployment_ramp_anchor(pd.Timestamp("2020-01-03"))
    assert not hasattr(rm, "_deployment_ramp_anchor_date")


def test_snapshot_suspend_post_reentry_clears_deployment_ramp(monkeypatch: pytest.MonkeyPatch) -> None:
    import momentum_strategy.event_driven_risk as edr

    monkeypatch.setattr(edr, "SUSPENSION_REENTRY_RAMP_ENABLED", True)
    monkeypatch.setattr(edr, "POST_DEPLOYMENT_RISK_ADJUST_CALENDAR_DAYS", 0)
    rm = edr.EventDrivenRiskManager(100_000.0)
    rm.mark_deployment_ramp_start(pd.Timestamp("2020-01-02"))
    rm._snapshot_suspend_post_reentry(
        pd.Timestamp("2020-01-03"),
        100_000.0,
        "TEST",
        "TEST",
        "test",
    )
    assert not hasattr(rm, "_deployment_ramp_anchor_date")
