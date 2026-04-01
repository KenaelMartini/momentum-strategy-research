# CLI : python -m momentum_strategy.event_driven
from __future__ import annotations

import argparse
import logging
import sys
import warnings
from pathlib import Path

import yaml

import momentum_strategy.runtime_config  # noqa: F401 — shim `config`

from momentum_strategy.paths import configs_dir, project_root

from config import (
    BACKTEST_END,
    BACKTEST_START,
    EVENT_DRIVEN_BASELINE_JSON,
    EVENT_DRIVEN_BASELINE_JSON_TRAIN1,
    EVENT_DRIVEN_INVEST_ONLY_MARKET_REGIME_TREND,
    INITIAL_CAPITAL,
    REBALANCING_FREQUENCY,
    RESEARCH_OOS_AFTER_TRAIN_1_END,
    RESEARCH_OOS_AFTER_TRAIN_1_START,
    RESEARCH_TRAIN_1_END,
    RESEARCH_TRAIN_1_START,
)

from .engine import EventDrivenEngine


def _log_debug_risk_config() -> None:
    """Trace le YAML risque, la fusion `config` et les constantes figées de `event_driven_risk`."""
    import config as cfg

    log = logging.getLogger(__name__)
    root = project_root()
    yml = Path(str(getattr(cfg, "RISK_EVENT_DRIVEN_YAML_PATH", "") or ""))
    merged = tuple(getattr(cfg, "RISK_EVENT_DRIVEN_MERGED_KEYS", ()))
    log.info("[debug-risk-config] project_root=%s", root)
    log.info("[debug-risk-config] configs_dir=%s", configs_dir())
    log.info("[debug-risk-config] RISK_EVENT_DRIVEN_YAML_PATH=%s", getattr(cfg, "RISK_EVENT_DRIVEN_YAML_PATH", "<absent>"))
    log.info("[debug-risk-config] fichier YAML existe=%s", yml.is_file())
    log.info("[debug-risk-config] clés fusionnées dans `config` au premier import: %s", merged)
    if yml.is_file():
        raw_disk = yaml.safe_load(yml.read_text(encoding="utf-8")) or {}
        for k in (
            "SUSPENSION_REENTRY_RAMP_ENABLED",
            "DEPLOYMENT_RAMP_SCHEDULE",
            "SUSPENSION_REENTRY_RAMP_SCALES",
            "SUSPENSION_REENTRY_RAMP_REBALANCE_SCALES",
            "POST_DEPLOYMENT_RISK_ADJUST_CALENDAR_DAYS",
            "POST_DEPLOYMENT_RISK_EXTRA_MULT",
            "POST_DEPLOYMENT_RISK_SCALE_CAP",
        ):
            if k in raw_disk:
                log.info("[debug-risk-config] relu sur disque: %s = %r", k, raw_disk[k])
    import momentum_strategy.event_driven_risk as edr

    log.info(
        "[debug-risk-config] event_driven_risk (valeurs à l'import): "
        "SUSPENSION_REENTRY_RAMP_ENABLED=%r DEPLOYMENT_RAMP_SCHEDULE=%r "
        "REBALANCE_SCALES=%r POST_ADJUST_DAYS=%r EXTRA_MULT=%r SCALE_CAP=%r",
        edr.SUSPENSION_REENTRY_RAMP_ENABLED,
        edr.DEPLOYMENT_RAMP_SCHEDULE,
        edr.SUSPENSION_REENTRY_RAMP_REBALANCE_SCALES,
        edr.POST_DEPLOYMENT_RISK_ADJUST_CALENDAR_DAYS,
        edr.POST_DEPLOYMENT_RISK_EXTRA_MULT,
        edr.POST_DEPLOYMENT_RISK_SCALE_CAP,
    )
    cfg_ramp = getattr(cfg, "SUSPENSION_REENTRY_RAMP_ENABLED", "<absent>")
    if cfg_ramp != edr.SUSPENSION_REENTRY_RAMP_ENABLED:
        log.warning(
            "[debug-risk-config] Écart config vs event_driven_risk pour SUSPENSION_REENTRY_RAMP_ENABLED: "
            "config=%r edr=%r — un reload du module sans redémarrer le process peut expliquer ça.",
            cfg_ramp,
            edr.SUSPENSION_REENTRY_RAMP_ENABLED,
        )
    log.info(
        "[debug-risk-config] Si RAMP_ENABLED est False alors que le YAML dit true: "
        "redémarrer Python (ou vérifier que le bon dépôt / configs_dir est utilisé)."
    )


def _configure_logging() -> None:
    warnings.filterwarnings("ignore")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def main(argv: list[str] | None = None) -> int:
    _configure_logging()
    sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Backtest event-driven Phase 3")
    parser.add_argument(
        "--start",
        default=BACKTEST_START,
        help=f"Début (défaut: BACKTEST_START = {BACKTEST_START})",
    )
    parser.add_argument(
        "--end",
        default=BACKTEST_END,
        help=f"Fin (défaut: BACKTEST_END = {BACKTEST_END})",
    )
    parser.add_argument(
        "--train1",
        action="store_true",
        help=(
            "Période train 1 recherche : RESEARCH_TRAIN_1_START → RESEARCH_TRAIN_1_END "
            f"({RESEARCH_TRAIN_1_START} → {RESEARCH_TRAIN_1_END}). "
            "Écrase --start / --end."
        ),
    )
    parser.add_argument(
        "--oos1",
        action="store_true",
        help=(
            "Hors échantillon après train 1 : RESEARCH_OOS_AFTER_TRAIN_1_* "
            f"({RESEARCH_OOS_AFTER_TRAIN_1_START} → {RESEARCH_OOS_AFTER_TRAIN_1_END}). "
            "Écrase --start / --end."
        ),
    )
    parser.add_argument("--live", action="store_true")
    parser.add_argument(
        "--data",
        default=None,
        help="Chemin price_matrix.csv (défaut: <racine Momentum_Strategy>/data/processed/price_matrix.csv)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Dossier résultats (défaut: <racine Momentum_Strategy>/results/event_driven)",
    )
    parser.add_argument(
        "--baseline-json",
        default=None,
        help="Fichier JSON baseline pour save_results (défaut : train1 → "
        f"{EVENT_DRIVEN_BASELINE_JSON_TRAIN1}, sinon {EVENT_DRIVEN_BASELINE_JSON})",
    )
    parser.add_argument(
        "--skip-baseline",
        action="store_true",
        help="Ne pas comparer aux métriques baseline (ex. run OOS de validation)",
    )
    parser.add_argument(
        "--stress-cost-mult",
        type=float,
        default=None,
        help="Multiplicateur commission + slippage (ex. 1.2 = stress +20 %%).",
    )
    parser.add_argument(
        "--rebalance-threshold",
        type=float,
        default=None,
        help=(
            "Surcharge du seuil de rebalance (sinon REBALANCE_THRESHOLD_DEFAULT dans config). "
            "Utile pour sweeps train 1 sans modifier config.py."
        ),
    )
    parser.add_argument(
        "--n-long",
        type=int,
        default=None,
        help="Nombre de candidats longs en tête du signal (défaut: EVENT_DRIVEN_N_LONG dans config).",
    )
    parser.add_argument(
        "--n-short",
        type=int,
        default=None,
        help="Nombre de candidats shorts en queue du signal (défaut: config EVENT_DRIVEN_N_SHORT, ex. 0).",
    )
    parser.add_argument(
        "--max-position-size",
        type=float,
        default=None,
        help="Surcharge MAX_POSITION_SIZE (fraction du capital par ligne, ex. 0.08).",
    )
    parser.add_argument(
        "--ed-max-leverage",
        type=float,
        default=None,
        help="Surcharge ED_MAX_LEVERAGE (gross exposure max apres caps ligne, defaut 1.0).",
    )
    parser.add_argument(
        "--ed-signal-entry-eps",
        type=float,
        default=None,
        help="Surcharge ED_SIGNAL_ENTRY_EPS (seuil |signal| pour entrer long/short, defaut 0.02).",
    )
    parser.add_argument(
        "--ed-short-notional-scale",
        type=float,
        default=None,
        help="Surcharge ED_SHORT_NOTIONAL_SCALE (multiplicateur notionnel shorts, defaut 0.5).",
    )
    parser.add_argument(
        "--skip-strategy-benchmark-report",
        action="store_true",
        help="Ne pas générer strategy_vs_benchmark_*.html (comparaison EW) à la fin du run.",
    )
    parser.add_argument(
        "--debug-risk-config",
        action="store_true",
        help="Tracer risk_event_driven.yaml + clés fusionnées et constantes figées event_driven_risk (rampe).",
    )
    if argv is None:
        argv = sys.argv[1:]
    args = parser.parse_args(argv)

    if args.debug_risk_config:
        _log_debug_risk_config()

    root = project_root()
    if args.data is None:
        args.data = str((root / "data" / "processed" / "price_matrix.csv").resolve())
    if args.output is None:
        args.output = str((root / "results" / "event_driven").resolve())

    if args.train1 and args.oos1:
        parser.error("Utilise --train1 ou --oos1, pas les deux.")
    if args.train1:
        args.start = RESEARCH_TRAIN_1_START
        args.end = RESEARCH_TRAIN_1_END
    elif args.oos1:
        args.start = RESEARCH_OOS_AFTER_TRAIN_1_START
        args.end = RESEARCH_OOS_AFTER_TRAIN_1_END

    print("=" * 60)
    print("  PHASE 3 — BACKTEST EVENT-DRIVEN")
    print("=" * 60)
    print(f"  Période   : {args.start} → {args.end}")
    print(f"  Capital   : ${INITIAL_CAPITAL:,.0f}")
    print(f"  Visu live : {'OUI' if args.live else 'NON'}")
    if args.skip_baseline or (args.oos1 and args.baseline_json is None):
        print(
            "  Baseline  : ignorée"
            + (" (--skip-baseline)" if args.skip_baseline else " (OOS par défaut)")
        )
    elif args.baseline_json:
        print(f"  Baseline  : {args.baseline_json}")
    elif args.train1:
        print(f"  Baseline  : {EVENT_DRIVEN_BASELINE_JSON_TRAIN1}")
    else:
        print(f"  Baseline  : {EVENT_DRIVEN_BASELINE_JSON}")
    if args.stress_cost_mult is not None:
        print(f"  Stress coûts: ×{args.stress_cost_mult:g}")
    if args.rebalance_threshold is not None:
        print(f"  Seuil rebal. : {args.rebalance_threshold:g} (--rebalance-threshold)")
    if args.n_long is not None or args.n_short is not None:
        import config as _cfg_ed

        _dnl = int(getattr(_cfg_ed, "EVENT_DRIVEN_N_LONG", 6))
        _dns = int(getattr(_cfg_ed, "EVENT_DRIVEN_N_SHORT", 0))
        print(
            f"  N long/short : {args.n_long if args.n_long is not None else _dnl} / "
            f"{args.n_short if args.n_short is not None else _dns}"
        )
    print(f"  Rebal freq  : {REBALANCING_FREQUENCY}")
    if EVENT_DRIVEN_INVEST_ONLY_MARKET_REGIME_TREND:
        print("  Filtre test : investi seulement si régime marché effectif = TREND (sinon cash)")
    if args.max_position_size is not None:
        print(f"  Max pos     : {args.max_position_size:g} (--max-position-size)")
    if args.ed_max_leverage is not None:
        print(f"  ED levier   : {args.ed_max_leverage:g} (--ed-max-leverage)")
    if args.ed_signal_entry_eps is not None:
        print(f"  Sig eps     : {args.ed_signal_entry_eps:g} (--ed-signal-entry-eps)")
    if args.ed_short_notional_scale is not None:
        print(f"  Short scale : {args.ed_short_notional_scale:g} (--ed-short-notional-scale)")
    print("=" * 60)

    skip_bl = bool(args.skip_baseline)
    baseline_path: Path | None = None
    if not skip_bl:
        if args.oos1 and args.baseline_json is None:
            skip_bl = True
        elif args.baseline_json is not None:
            baseline_path = Path(args.baseline_json)
        elif args.train1:
            baseline_path = Path(EVENT_DRIVEN_BASELINE_JSON_TRAIN1)
        else:
            baseline_path = Path(EVENT_DRIVEN_BASELINE_JSON)

    engine = EventDrivenEngine(
        data_path=args.data,
        start_date=args.start,
        end_date=args.end,
        initial_capital=INITIAL_CAPITAL,
        live_viz=args.live,
        output_dir=args.output,
        baseline_reference_path=baseline_path,
        skip_baseline_comparison=skip_bl,
        transaction_cost_stress_multiplier=args.stress_cost_mult,
        rebalance_threshold=args.rebalance_threshold,
        n_long_positions=args.n_long,
        n_short_positions=args.n_short,
        max_position_size=args.max_position_size,
        ed_max_leverage=args.ed_max_leverage,
        ed_signal_entry_eps=args.ed_signal_entry_eps,
        ed_short_notional_scale=args.ed_short_notional_scale,
        skip_strategy_benchmark_report=args.skip_strategy_benchmark_report,
    )

    engine.run()

    print("\n  Génération de la visualisation 3D...")
    files = engine.save_results()

    print("\n" + "=" * 60)
    print("  FICHIERS GÉNÉRÉS")
    print("=" * 60)
    for key, path in files.items():
        if path:
            print(f"  {key:12s} : {path}")
    if files.get("dashboard"):
        print("\n  Ouvre dans ton navigateur :")
        print(f"  {files['dashboard']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
