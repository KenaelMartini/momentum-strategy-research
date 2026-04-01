from __future__ import annotations

import json

import pandas as pd

from momentum_strategy.research.data_quality import build_data_quality_report


def test_build_data_quality_report(tmp_path) -> None:
    idx = pd.date_range("2020-01-01", periods=4, freq="D")
    df = pd.DataFrame({"A": [1.0, 2.0, 3.0, 4.0], "B": [1.0, None, None, 2.0]}, index=idx)
    matrix = tmp_path / "price_matrix.csv"
    df.to_csv(matrix, index_label="date")
    out = tmp_path / "data_quality.json"
    build_data_quality_report(matrix_path=matrix, output_path=out)
    raw = json.loads(out.read_text(encoding="utf-8"))
    assert raw["rows"] == 4
    assert raw["n_assets"] == 2
    assert raw["start"] == "2020-01-01"
    assert raw["end"] == "2020-01-04"
