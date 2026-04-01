from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from momentum_strategy.data.ibkr import IBKRDataFetcher, load_ibkr_settings
from momentum_strategy.data.matrix import build_price_matrix_pipeline, frames_to_close_matrix, write_price_matrix
from momentum_strategy.universe import load_universe


def _setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s | %(levelname)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S")


def cmd_fetch(args: argparse.Namespace) -> int:
    if args.stocks_only and args.futures_only:
        raise SystemExit("Choisir --stocks-only OU --futures-only, pas les deux.")
    universe = load_universe(Path(args.universe) if args.universe else None)
    fetcher = IBKRDataFetcher(root=Path(args.root) if args.root else None)
    if not fetcher.connect():
        return 1
    use_cache = not args.no_cache
    try:
        all_data: dict = {}
        if args.futures_only:
            all_data = fetcher.fetch_futures_data(
                list(universe.futures), use_cache=use_cache, force=args.force
            )
        elif args.stocks_only:
            all_data = fetcher.fetch_stocks_data(
                list(universe.stocks), use_cache=use_cache, force=args.force
            )
        else:
            all_data.update(
                fetcher.fetch_stocks_data(list(universe.stocks), use_cache=use_cache, force=args.force)
            )
            all_data.update(
                fetcher.fetch_futures_data(list(universe.futures), use_cache=use_cache, force=args.force)
            )
        if not all_data:
            logging.error("Aucune donnée téléchargée.")
            return 1
        pm = frames_to_close_matrix(all_data)
        settings = load_ibkr_settings(fetcher.root)
        sources = []
        for s in pm.columns:
            prefix = "stock" if s in universe.stocks else "future"
            sources.append(str((settings.raw_dir / f"{prefix}_{s}.csv").resolve()))
        write_price_matrix(
            pm,
            settings.processed_dir,
            manifest_extra={"universe_version": universe.version, "sources": sources},
        )
        return 0
    finally:
        fetcher.disconnect()


def cmd_build_matrix(args: argparse.Namespace) -> int:
    if args.stocks_only and args.futures_only:
        raise SystemExit("Choisir --stocks-only OU --futures-only, pas les deux.")
    universe = load_universe(Path(args.universe) if args.universe else None)
    build_price_matrix_pipeline(
        universe,
        stocks_only=args.stocks_only,
        futures_only=args.futures_only,
        root=Path(args.root) if args.root else None,
        strict_universe=args.strict,
    )
    return 0


def cmd_event_backtest(args: argparse.Namespace) -> int:
    from momentum_strategy.event_driven.__main__ import main as ed_main

    chunks: list[str] = []
    if args.start:
        chunks += ["--start", str(args.start)]
    if args.end:
        chunks += ["--end", str(args.end)]
    if args.train1:
        chunks.append("--train1")
    if args.oos1:
        chunks.append("--oos1")
    if args.live:
        chunks.append("--live")
    if args.data:
        chunks += ["--data", str(args.data)]
    if args.output:
        chunks += ["--output", str(args.output)]
    if args.baseline_json:
        chunks += ["--baseline-json", str(args.baseline_json)]
    if args.skip_baseline:
        chunks.append("--skip-baseline")
    if args.stress_cost_mult is not None:
        chunks += ["--stress-cost-mult", str(args.stress_cost_mult)]
    if args.rebalance_threshold is not None:
        chunks += ["--rebalance-threshold", str(args.rebalance_threshold)]
    if args.n_long is not None:
        chunks += ["--n-long", str(args.n_long)]
    if args.n_short is not None:
        chunks += ["--n-short", str(args.n_short)]
    if args.max_position_size is not None:
        chunks += ["--max-position-size", str(args.max_position_size)]
    if args.ed_max_leverage is not None:
        chunks += ["--ed-max-leverage", str(args.ed_max_leverage)]
    if args.ed_signal_entry_eps is not None:
        chunks += ["--ed-signal-entry-eps", str(args.ed_signal_entry_eps)]
    if args.ed_short_notional_scale is not None:
        chunks += ["--ed-short-notional-scale", str(args.ed_short_notional_scale)]
    if args.skip_strategy_benchmark_report:
        chunks.append("--skip-strategy-benchmark-report")
    if getattr(args, "debug_risk_config", False):
        chunks.append("--debug-risk-config")
    return ed_main(chunks)


def cmd_archive_run(args: argparse.Namespace) -> int:
    from momentum_strategy.research.archive_run import archive_reference_run
    from momentum_strategy.paths import project_root
    from datetime import datetime, timezone

    root = project_root()
    dest = Path(args.dest) if args.dest else None
    if dest is None:
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        dest = root / "results" / "archive" / f"run_{ts}"
    archive_reference_run(
        dest,
        copy_latest_event_driven=args.copy_latest_results,
        event_driven_dir=Path(args.event_driven_dir) if args.event_driven_dir else None,
    )
    print(f"Archive écrite : {dest.resolve()}")
    return 0


def cmd_cost_stress_grid(args: argparse.Namespace) -> int:
    from momentum_strategy.research.cost_stress import run_cost_stress_grid

    mults = [float(x.strip()) for x in args.mults.split(",") if x.strip()]
    df = run_cost_stress_grid(
        mults,
        data_path=Path(args.data) if args.data else None,
        start=args.start,
        end=args.end,
        output_parent=Path(args.output) if args.output else None,
        skip_strategy_benchmark_report=not args.with_benchmark_html,
    )
    print(df.to_string(index=False))
    return 0


def cmd_research_pipeline(args: argparse.Namespace) -> int:
    from momentum_strategy.research.institutional_pipeline import main as pipe_main

    return pipe_main(args.pipeline_argv)


def cmd_book_forward_attribution(args: argparse.Namespace) -> int:
    from momentum_strategy.research.book_forward_attribution import main as bfa_main

    chunks: list[str] = ["--rebal", str(args.rebal), "--horizon", str(args.horizon)]
    if args.prices:
        chunks += ["--prices", str(args.prices)]
    if args.output:
        chunks += ["--output", str(args.output)]
    return bfa_main(chunks)


def cmd_sensitivity_batch(args: argparse.Namespace) -> int:
    from momentum_strategy.research.sensitivity_batch import run_from_yaml

    df = run_from_yaml(
        Path(args.presets),
        data_path=Path(args.data) if args.data else None,
        start=args.start,
        end=args.end,
        output_parent=Path(args.output) if args.output else None,
        only=args.only,
        write_artifacts=bool(args.write_artifacts),
    )
    print(df.to_string(index=False))
    return 0


def cmd_data_quality_report(args: argparse.Namespace) -> int:
    from momentum_strategy.research.data_quality import main as dq_main

    chunks: list[str] = []
    if args.data:
        chunks += ["--data", str(args.data)]
    if args.output:
        chunks += ["--output", str(args.output)]
    return int(dq_main(chunks))


def cmd_minimal_backtest(args: argparse.Namespace) -> int:
    from momentum_strategy.backtest.minimal import run_default_minimal_backtest

    bt, summary = run_default_minimal_backtest(
        price_matrix_path=Path(args.data) if args.data else None,
        params_path=Path(args.strategy) if args.strategy else None,
        apply_caps=not args.no_caps,
    )
    print(bt.tail())
    print("---")
    print(summary)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="mstrat", description="Momentum_Strategy CLI")
    parser.add_argument("-v", "--verbose", action="store_true")
    sub = parser.add_subparsers(dest="command", required=True)

    p_fetch = sub.add_parser("fetch", help="Télécharger les prix via IBKR et construire price_matrix.csv")
    p_fetch.add_argument("--root", type=str, default=None, help="Racine du projet (défaut: auto)")
    p_fetch.add_argument("--universe", type=str, default=None, help="Chemin universe.yaml")
    p_fetch.add_argument("--stocks-only", action="store_true")
    p_fetch.add_argument("--futures-only", action="store_true")
    p_fetch.add_argument(
        "--no-cache",
        action="store_true",
        help="Ne pas utiliser le cache disque (chaque série est retéléchargée)",
    )
    p_fetch.add_argument("--force", action="store_true", help="Forcer le retéléchargement de chaque série")
    p_fetch.set_defaults(func=cmd_fetch)

    p_build = sub.add_parser("build-matrix", help="Construire price_matrix.csv depuis data/raw/")
    p_build.add_argument("--root", type=str, default=None)
    p_build.add_argument("--universe", type=str, default=None)
    p_build.add_argument("--stocks-only", action="store_true")
    p_build.add_argument("--futures-only", action="store_true")
    p_build.add_argument("--strict", action="store_true", help="Exiger tous les fichiers de l'univers")
    p_build.set_defaults(func=cmd_build_matrix)

    p_ed = sub.add_parser(
        "event-backtest",
        help="Backtest event-driven (sans look-ahead) + risque Fist, résultats dans results/event_driven/",
    )
    p_ed.add_argument("--start", type=str, default=None)
    p_ed.add_argument("--end", type=str, default=None)
    p_ed.add_argument("--train1", action="store_true")
    p_ed.add_argument("--oos1", action="store_true")
    p_ed.add_argument("--live", action="store_true")
    p_ed.add_argument("--data", type=str, default=None, help="Chemin price_matrix.csv")
    p_ed.add_argument("--output", type=str, default=None, help="Dossier résultats (défaut: ./results/event_driven)")
    p_ed.add_argument("--baseline-json", type=str, default=None)
    p_ed.add_argument("--skip-baseline", action="store_true")
    p_ed.add_argument("--stress-cost-mult", type=float, default=None)
    p_ed.add_argument("--rebalance-threshold", type=float, default=None)
    p_ed.add_argument(
        "--n-long",
        type=int,
        default=None,
        help="Candidats longs (défaut: strategy_defaults event_driven_n_long)",
    )
    p_ed.add_argument(
        "--n-short",
        type=int,
        default=None,
        help="Candidats shorts (défaut: strategy_defaults event_driven_n_short, ex. 0)",
    )
    p_ed.add_argument("--max-position-size", type=float, default=None, help="Cap par ligne (fraction)")
    p_ed.add_argument("--ed-max-leverage", type=float, default=None, help="Levier brut max event-driven")
    p_ed.add_argument("--ed-signal-entry-eps", type=float, default=None, help="Seuil |signal| entree L/S")
    p_ed.add_argument(
        "--ed-short-notional-scale",
        type=float,
        default=None,
        help="Multiplicateur notionnel sur les shorts (defaut config 0.5)",
    )
    p_ed.add_argument(
        "--skip-strategy-benchmark-report",
        action="store_true",
        help="Ne pas générer le HTML stratégie vs benchmark EW",
    )
    p_ed.add_argument(
        "--debug-risk-config",
        action="store_true",
        help="Tracer fusion risk_event_driven.yaml et constantes rampe (event_driven_risk)",
    )
    p_ed.set_defaults(func=cmd_event_backtest)

    p_arch = sub.add_parser(
        "archive-run",
        help="Archiver configs + manifeste (+ optionnel derniers CSV event-driven) pour traçabilité",
    )
    p_arch.add_argument("--dest", type=str, default=None, help="Dossier cible (défaut: results/archive/run_<ts>)")
    p_arch.add_argument(
        "--copy-latest-results",
        action="store_true",
        help="Copier le dernier stats_*.csv et fichiers liés depuis results/event_driven",
    )
    p_arch.add_argument("--event-driven-dir", type=str, default=None)
    p_arch.set_defaults(func=cmd_archive_run)

    p_cs = sub.add_parser(
        "cost-stress-grid",
        help="Enchaîner des backtests avec plusieurs multiplicateurs de coûts (résumé CSV)",
    )
    p_cs.add_argument("--mults", type=str, default="1.0,1.5,2.0")
    p_cs.add_argument("--start", type=str, default=None)
    p_cs.add_argument("--end", type=str, default=None)
    p_cs.add_argument("--data", type=str, default=None)
    p_cs.add_argument("--output", type=str, default=None)
    p_cs.add_argument("--with-benchmark-html", action="store_true")
    p_cs.set_defaults(func=cmd_cost_stress_grid)

    p_rp = sub.add_parser(
        "research-pipeline",
        help="Pipeline institutionnel : Train 1 baseline, stress coûts, archive, validation, OOS",
    )
    p_rp.add_argument(
        "pipeline_argv",
        nargs=argparse.REMAINDER,
        help="Sous-commande : print-commands | train1-baseline | train1-cost-stress | train1-archive | train1-levers | train1-full | validation | oos-strict",
    )
    p_rp.set_defaults(func=cmd_research_pipeline)

    p_bfa = sub.add_parser(
        "book-forward-attribution",
        help="Attribution forward long/short et overlap winners (rebal_diagnostics + price_matrix)",
    )
    p_bfa.add_argument("--rebal", type=str, required=True, help="Chemin rebal_diagnostics_*.csv")
    p_bfa.add_argument("--prices", type=str, default=None, help="price_matrix.csv")
    p_bfa.add_argument("--horizon", type=int, default=21, help="Pas de calendrier dans la matrice (defaut 21)")
    p_bfa.add_argument("--output", type=str, default=None, help="CSV détail (defaut à côté du rebal)")
    p_bfa.set_defaults(func=cmd_book_forward_attribution)

    p_sb = sub.add_parser(
        "sensitivity-batch",
        help="Sensibilité depuis configs/sensitivity_presets.yaml (plusieurs scénarios)",
    )
    p_sb.add_argument("--presets", type=str, required=True)
    p_sb.add_argument("--start", type=str, default=None)
    p_sb.add_argument("--end", type=str, default=None)
    p_sb.add_argument("--data", type=str, default=None)
    p_sb.add_argument("--output", type=str, default=None)
    p_sb.add_argument("--only", type=str, default=None)
    p_sb.add_argument(
        "--write-artifacts",
        action="store_true",
        help="Par scénario : stats/rebal CSV, dashboard 3D, etc. (plus lent)",
    )
    p_sb.set_defaults(func=cmd_sensitivity_batch)

    p_dq = sub.add_parser(
        "data-quality-report",
        help="Rapport qualité/coverage de la price_matrix (phase extension données).",
    )
    p_dq.add_argument("--data", type=str, default=None, help="Chemin price_matrix.csv")
    p_dq.add_argument("--output", type=str, default=None, help="Chemin JSON de sortie")
    p_dq.set_defaults(func=cmd_data_quality_report)

    p_bt = sub.add_parser("minimal-backtest", help="Backtest mensuel minimal sur price_matrix.csv")
    p_bt.add_argument("--data", type=str, default=None, help="Chemin price_matrix.csv")
    p_bt.add_argument("--strategy", type=str, default=None, help="Chemin strategy_defaults.yaml")
    p_bt.add_argument("--no-caps", action="store_true", help="Désactiver caps levier / ligne")
    p_bt.set_defaults(func=cmd_minimal_backtest)

    args = parser.parse_args(argv)
    _setup_logging(args.verbose)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
