from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from momentum_strategy.paths import project_root


def build_data_quality_report(*, matrix_path: Path, output_path: Path) -> Path:
    df = pd.read_csv(matrix_path, index_col=0, parse_dates=True).sort_index()
    if df.empty:
        raise ValueError("price_matrix vide")
    coverage_by_symbol = df.notna().sum().sort_values(ascending=False)
    missing_ratio = (1.0 - (coverage_by_symbol / float(len(df)))).sort_values(ascending=True)

    first_valid = {}
    last_valid = {}
    for col in df.columns:
        s = df[col].dropna()
        if s.empty:
            first_valid[col] = None
            last_valid[col] = None
        else:
            first_valid[col] = str(pd.Timestamp(s.index.min()).date())
            last_valid[col] = str(pd.Timestamp(s.index.max()).date())

    report = {
        "matrix_path": str(matrix_path.resolve()),
        "rows": int(df.shape[0]),
        "n_assets": int(df.shape[1]),
        "start": str(pd.Timestamp(df.index.min()).date()),
        "end": str(pd.Timestamp(df.index.max()).date()),
        "assets_full_coverage": int((missing_ratio <= 0.0).sum()),
        "assets_missing_lt_5pct": int((missing_ratio <= 0.05).sum()),
        "assets_missing_gt_20pct": int((missing_ratio > 0.20).sum()),
        "top_10_best_coverage": [
            {"symbol": str(k), "missing_ratio": float(v)}
            for k, v in missing_ratio.head(10).items()
        ],
        "top_10_worst_coverage": [
            {"symbol": str(k), "missing_ratio": float(v)}
            for k, v in missing_ratio.tail(10).items()
        ],
        "first_valid_date_by_symbol": first_valid,
        "last_valid_date_by_symbol": last_valid,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return output_path


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Rapport qualité data pour price_matrix.csv")
    p.add_argument("--data", type=Path, default=None, help="CSV price_matrix (défaut data/processed/price_matrix.csv)")
    p.add_argument("--output", type=Path, default=None, help="JSON de sortie")
    args = p.parse_args(argv)
    root = project_root()
    data = (Path(args.data) if args.data else (root / "data" / "processed" / "price_matrix.csv")).resolve()
    out = (
        Path(args.output)
        if args.output
        else (root / "results" / "institutional" / "data_quality_report.json")
    )
    path = build_data_quality_report(matrix_path=data, output_path=out)
    print(f"Rapport data quality: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
