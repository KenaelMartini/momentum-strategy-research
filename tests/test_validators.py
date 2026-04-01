from __future__ import annotations

import pandas as pd
import pytest

from momentum_strategy.data.validators import validate_ohlcv_frame


def test_validate_rejects_negative_close() -> None:
    idx = pd.bdate_range("2020-01-01", periods=3)
    df = pd.DataFrame(
        {"open": [1, 1, 1], "high": [1, 1, 1], "low": [1, 1, 1], "close": [1, -1, 1], "volume": [1, 1, 1]},
        index=idx,
    )
    with pytest.raises(ValueError, match="positifs"):
        validate_ohlcv_frame(df, symbol="X")
