"""Grille de stress commission + slippage (multiplicateur unique sur les deux)."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

import momentum_strategy.runtime_config  # noqa: F401 — shim `config`

from config import BACKTEST_END, BACKTEST_START

from momentum_strategy.event_driven.engine import EventDrivenEngine
from momentum_strategy.paths import project_root


def run_cost_stress_grid(
    multipliers: list[float],
    *,
    data_path: Path | None = None,
    start: str | None = None,
    end: str | None = None,
    output_parent: Path | None = None,
    skip_strategy_benchmark_report: bool = True,
) -> pd.DataFrame:
    root = project_root()
    data = Path(data_path) if data_path else root / "data" / "processed" / "price_matrix.csv"
    out = Path(output_parent) if output_parent else root / "results" / "cost_stress"
    out.mkdir(parents=True, exist_ok=True)
    start_d = start or BACKTEST_START
    end_d = end or BACKTEST_END

    rows: list[dict] = []
    for m in multipliers:
        sub = out / f"mult_{str(m).replace('.', '_')}"
        sub.mkdir(parents=True, exist_ok=True)
        engine = EventDrivenEngine(
            data_path=str(data),
            start_date=start_d,
            end_date=end_d,
            output_dir=str(sub),
            skip_baseline_comparison=True,
            transaction_cost_stress_multiplier=float(m),
            skip_strategy_benchmark_report=skip_strategy_benchmark_report,
        )
        engine.run()
        fm = dict(engine.final_metrics)
        fm["stress_cost_mult"] = float(m)
        rows.append(fm)

    df = pd.DataFrame(rows)
    csv_path = out / "summary.csv"
    df.to_csv(csv_path, index=False)
    return df


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Grille stress coûts (× sur commission et slippage).")
    parser.add_argument(
        "--mults",
        default="1.0,1.5,2.0",
        help="Liste séparée par virgules (défaut: 1.0,1.5,2.0)",
    )
    parser.add_argument("--start", default=None)
    parser.add_argument("--end", default=None)
    parser.add_argument("--data", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument(
        "--with-benchmark-html",
        action="store_true",
        help="Générer aussi strategy_vs_benchmark pour chaque run (plus lent).",
    )
    args = parser.parse_args(argv)
    mults = [float(x.strip()) for x in args.mults.split(",") if x.strip()]
    df = run_cost_stress_grid(
        mults,
        data_path=args.data,
        start=args.start,
        end=args.end,
        output_parent=args.output,
        skip_strategy_benchmark_report=not args.with_benchmark_html,
    )
    print(df.to_string(index=False))
    out = Path(args.output) if args.output else project_root() / "results" / "cost_stress"
    print(f"\nRésumé CSV : {out / 'summary.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
