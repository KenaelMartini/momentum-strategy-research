"""
Analyse post-backtest : contribution forward long/short et overlap « winners » vs book.

Lit rebal_diagnostics_*.csv (colonne target_weights_json) et price_matrix.csv.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from momentum_strategy.paths import project_root


def _normalize_index(idx: pd.DatetimeIndex) -> pd.DatetimeIndex:
    return pd.DatetimeIndex([pd.Timestamp(x).normalize() for x in idx])


def _price_row_index(prices: pd.DataFrame, dt: pd.Timestamp) -> int | None:
    ts = pd.Timestamp(dt).normalize()
    norm = _normalize_index(prices.index)
    hits = np.where(norm == ts)[0]
    if len(hits):
        return int(hits[0])
    ge = np.where(norm >= ts)[0]
    if len(ge) == 0:
        return None
    return int(ge[0])


def load_prices(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, index_col=0, parse_dates=True)
    df.index = pd.to_datetime(df.index, utc=True).tz_localize(None)
    return df.sort_index()


def cross_section_fwd_returns(
    prices: pd.DataFrame,
    i_start: int,
    horizon: int,
) -> pd.Series:
    """Rendements simples sur horizon pas de calendrier (lignes de la matrice)."""
    i_end = i_start + horizon
    if i_end >= len(prices):
        return pd.Series(dtype=float)
    p0 = prices.iloc[i_start]
    p1 = prices.iloc[i_end]
    return (p1 / p0) - 1.0


def run_attribution(
    rebal_path: Path,
    prices_path: Path,
    *,
    horizon: int = 21,
) -> tuple[pd.DataFrame, dict[str, float]]:
    rebal = pd.read_csv(rebal_path, parse_dates=["date"])
    prices = load_prices(prices_path)

    rows_out: list[dict] = []
    sum_leg_long = 0.0
    sum_leg_short = 0.0
    n_short_overlap = 0
    n_short_total = 0
    n_long_bottom = 0
    n_long_total = 0
    n_used = 0

    for _, row in rebal.iterrows():
        raw = row.get("target_weights_json")
        if raw is None or (isinstance(raw, float) and np.isnan(raw)) or str(raw).strip() in ("", "{}"):
            continue
        try:
            weights: dict[str, float] = json.loads(str(raw))
        except json.JSONDecodeError:
            continue
        if not weights:
            continue

        dt = row["date"]
        i0 = _price_row_index(prices, pd.Timestamp(dt))
        if i0 is None:
            continue
        r_all = cross_section_fwd_returns(prices, i0, horizon)
        min_cs = min(5, max(3, len(prices.columns)))
        if r_all.empty or r_all.notna().sum() < min_cs:
            continue

        valid = r_all.dropna()
        q90 = float(valid.quantile(0.9))
        q10 = float(valid.quantile(0.1))

        leg_long = 0.0
        leg_short = 0.0
        n_so = 0
        n_st = 0
        n_lb = 0
        n_lt = 0

        for sym, w in weights.items():
            if sym not in r_all.index:
                continue
            ri = r_all.get(sym)
            if ri is None or (isinstance(ri, float) and np.isnan(ri)):
                continue
            ri = float(ri)
            if w > 0.01:
                leg_long += w * ri
                n_lt += 1
                if ri <= q10:
                    n_lb += 1
            elif w < -0.01:
                leg_short += w * ri
                n_st += 1
                if ri >= q90:
                    n_so += 1

        rows_out.append(
            {
                "date": dt,
                "leg_long_fwd": leg_long,
                "leg_short_fwd": leg_short,
                "combined_fwd": leg_long + leg_short,
                "n_long_leg": n_lt,
                "n_short_leg": n_st,
                "short_in_top_decile": n_so,
                "long_in_bottom_decile": n_lb,
            }
        )

        sum_leg_long += leg_long
        sum_leg_short += leg_short
        n_short_overlap += n_so
        n_short_total += n_st
        n_long_bottom += n_lb
        n_long_total += n_lt
        n_used += 1

    detail = pd.DataFrame(rows_out)
    summary = {
        "n_rebalances_used": float(n_used),
        "mean_leg_long_fwd": float(sum_leg_long / n_used) if n_used else float("nan"),
        "mean_leg_short_fwd": float(sum_leg_short / n_used) if n_used else float("nan"),
        "short_lines_in_top_decile_share": float(n_short_overlap / n_short_total) if n_short_total else float("nan"),
        "long_lines_in_bottom_decile_share": float(n_long_bottom / n_long_total) if n_long_total else float("nan"),
        "horizon_rows": float(horizon),
    }
    return detail, summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Attribution forward (long/short, overlap winners) depuis rebal_diagnostics + prix.",
    )
    parser.add_argument(
        "--rebal",
        type=Path,
        required=True,
        help="CSV rebal_diagnostics (colonne target_weights_json)",
    )
    parser.add_argument(
        "--prices",
        type=Path,
        default=None,
        help="price_matrix.csv (defaut: data/processed/price_matrix.csv)",
    )
    parser.add_argument(
        "--horizon",
        type=int,
        default=21,
        help="Horizon en nombre de lignes de la matrice de prix (defaut: 21)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="CSV détail par date (defaut: même dossier que --rebal, book_forward_attribution.csv)",
    )
    args = parser.parse_args(argv)

    root = project_root()
    prices_path = Path(args.prices) if args.prices else root / "data" / "processed" / "price_matrix.csv"
    if not args.rebal.exists():
        print(f"Fichier introuvable: {args.rebal}", file=sys.stderr)
        return 1
    if not prices_path.exists():
        print(f"Fichier introuvable: {prices_path}", file=sys.stderr)
        return 1

    detail, summary = run_attribution(args.rebal, prices_path, horizon=int(args.horizon))

    out = args.output
    if out is None:
        out = args.rebal.parent / "book_forward_attribution.csv"
    detail.to_csv(out, index=False)

    print("Résumé (moyennes par rebalance utilisée, horizon en lignes de prix):")
    for k, v in summary.items():
        if k.startswith("n_"):
            print(f"  {k}: {int(v)}")
        else:
            print(f"  {k}: {v:.6g}" if isinstance(v, float) else f"  {k}: {v}")
    print(f"\nDétail écrit : {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
