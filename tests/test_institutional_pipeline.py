from __future__ import annotations

from momentum_strategy.research.institutional_pipeline import (
    OOS_STRICT_END,
    OOS_STRICT_START,
    VALIDATION_END,
    VALIDATION_START,
    print_commands,
)


def test_institutional_windows_align_with_research_docs() -> None:
    assert VALIDATION_START == "2019-01-01"
    assert VALIDATION_END == "2024-12-31"
    assert OOS_STRICT_START == "2019-01-01"
    assert OOS_STRICT_END == "2024-12-31"


def test_print_commands_exits_zero() -> None:
    assert print_commands() == 0
