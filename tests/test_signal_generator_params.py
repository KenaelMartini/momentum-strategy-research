from __future__ import annotations

import logging


def test_momentum_signal_generator_v2_n_long_short() -> None:
    logging.disable(logging.CRITICAL)
    try:
        from momentum_strategy.event_driven_risk import EventDrivenRiskManager, MomentumSignalGeneratorV2

        class DummyHandler:
            pass

        rm = EventDrivenRiskManager(100_000.0)
        gen = MomentumSignalGeneratorV2(
            DummyHandler(),
            rm,
            n_long_positions=3,
            n_short_positions=2,
        )
        assert gen._n_long == 3
        assert gen._n_short == 2

        gen0 = MomentumSignalGeneratorV2(
            DummyHandler(),
            rm,
            n_long_positions=3,
            n_short_positions=0,
        )
        assert gen0._n_short == 0
    finally:
        logging.disable(logging.NOTSET)
