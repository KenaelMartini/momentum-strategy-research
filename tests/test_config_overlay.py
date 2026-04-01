from __future__ import annotations

import momentum_strategy.runtime_config  # noqa: F401

from momentum_strategy.research.config_overlay import apply_config_overrides, restore_config_overrides


def test_apply_restore_config_overrides_roundtrip() -> None:
    import config as c

    prev_ed = getattr(c, "ED_SIGNAL_RISK_ADJUST_ENABLED", None)
    prev = apply_config_overrides({"ED_SIGNAL_RISK_ADJUST_ENABLED": True})
    assert c.ED_SIGNAL_RISK_ADJUST_ENABLED is True
    restore_config_overrides(prev)
    assert c.ED_SIGNAL_RISK_ADJUST_ENABLED == prev_ed


def test_apply_turnover_cap_l1_reduces_delta() -> None:
    from momentum_strategy.event_driven_risk import MomentumSignalGeneratorV2

    gen = object.__new__(MomentumSignalGeneratorV2)
    prev = {"A": 0.5, "B": -0.2}
    new = {"A": 0.1, "B": 0.3}
    out = MomentumSignalGeneratorV2._apply_turnover_cap_l1(gen, new, prev, 0.2)  # type: ignore[arg-type]
    d1 = sum(abs(out.get(k, 0) - prev.get(k, 0)) for k in set(out) | set(prev))
    assert d1 <= 0.2000001
