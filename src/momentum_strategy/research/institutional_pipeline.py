"""
Enchaînements recherche institutionnelle : Train 1 baseline, stress coûts, archive,
validation, OOS strict — dossiers résultats séparés sous results/institutional/.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import momentum_strategy.runtime_config  # noqa: F401 — shim `config`

from config import RESEARCH_TRAIN_1_END, RESEARCH_TRAIN_1_START

from momentum_strategy.paths import configs_dir, project_root

# Aligné sur configs/research_windows.yaml
VALIDATION_START = "2019-01-01"
VALIDATION_END = "2024-12-31"
OOS_STRICT_START = "2019-01-01"
OOS_STRICT_END = "2024-12-31"

INST_DIR = "institutional"
TRAIN1_BASELINE_SUB = "train1_baseline"
TRAIN1_COST_STRESS_SUB = "train1_cost_stress"
TRAIN1_LEVERS_SUB = "train1_levers"
VALIDATION_SUB = "validation"
OOS_SUB = "oos_strict"


def _inst_root() -> Path:
    return project_root() / "results" / INST_DIR


def run_train1_baseline(*, data: Path | None = None, skip_benchmark_html: bool = True) -> int:
    from momentum_strategy.event_driven.__main__ import main as ed_main

    out = _inst_root() / TRAIN1_BASELINE_SUB
    out.mkdir(parents=True, exist_ok=True)
    chunks = [
        "--train1",
        "--skip-baseline",
        "--output",
        str(out),
    ]
    if data is not None:
        chunks += ["--data", str(data)]
    if skip_benchmark_html:
        chunks.append("--skip-strategy-benchmark-report")
    return int(ed_main(chunks))


def run_train1_cost_stress(
    *,
    mults: list[float],
    data: Path | None = None,
    skip_benchmark_html: bool = True,
) -> int:
    from momentum_strategy.research.cost_stress import run_cost_stress_grid

    out = _inst_root() / TRAIN1_COST_STRESS_SUB
    df = run_cost_stress_grid(
        mults,
        data_path=data,
        start=RESEARCH_TRAIN_1_START,
        end=RESEARCH_TRAIN_1_END,
        output_parent=out,
        skip_strategy_benchmark_report=skip_benchmark_html,
    )
    print(df.to_string(index=False))
    print(f"\nRésumé : {out / 'summary.csv'}")
    return 0


def run_train1_levers(
    *,
    presets: Path | None = None,
    data: Path | None = None,
    write_artifacts: bool = True,
    only: str | None = None,
) -> int:
    """Campagne presets YAML sur la fenêtre Train 1 uniquement → results/institutional/train1_levers/."""
    from momentum_strategy.research.sensitivity_batch import run_from_yaml

    p = presets if presets is not None else configs_dir() / "train1_levers_presets.yaml"
    out = _inst_root() / TRAIN1_LEVERS_SUB
    out.mkdir(parents=True, exist_ok=True)
    df = run_from_yaml(
        p,
        data_path=data,
        start=RESEARCH_TRAIN_1_START,
        end=RESEARCH_TRAIN_1_END,
        output_parent=out,
        only=only,
        write_artifacts=write_artifacts,
    )
    print(df.to_string(index=False))
    print(f"\nRésumé : {out / 'summary.csv'}")
    return 0


def run_archive_train1_baseline(*, dest: Path | None = None) -> int:
    from datetime import datetime, timezone

    from momentum_strategy.research.archive_run import archive_reference_run

    ed_dir = _inst_root() / TRAIN1_BASELINE_SUB
    root = project_root()
    if dest is None:
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        dest = root / "results" / "archive" / f"train1_baseline_{ts}"
    archive_reference_run(
        dest,
        copy_latest_event_driven=True,
        event_driven_dir=ed_dir,
    )
    print(f"Archive Train 1 baseline : {dest.resolve()}")
    return 0


def run_validation(*, data: Path | None = None, skip_benchmark_html: bool = True) -> int:
    from momentum_strategy.event_driven.__main__ import main as ed_main

    out = _inst_root() / VALIDATION_SUB
    out.mkdir(parents=True, exist_ok=True)
    chunks = [
        "--start",
        VALIDATION_START,
        "--end",
        VALIDATION_END,
        "--skip-baseline",
        "--output",
        str(out),
    ]
    if data is not None:
        chunks += ["--data", str(data)]
    if skip_benchmark_html:
        chunks.append("--skip-strategy-benchmark-report")
    return int(ed_main(chunks))


def run_oos_strict(*, data: Path | None = None, skip_benchmark_html: bool = True) -> int:
    from momentum_strategy.event_driven.__main__ import main as ed_main

    out = _inst_root() / OOS_SUB
    out.mkdir(parents=True, exist_ok=True)
    chunks = [
        "--start",
        OOS_STRICT_START,
        "--end",
        OOS_STRICT_END,
        "--skip-baseline",
        "--output",
        str(out),
    ]
    if data is not None:
        chunks += ["--data", str(data)]
    if skip_benchmark_html:
        chunks.append("--skip-strategy-benchmark-report")
    return int(ed_main(chunks))


def print_commands() -> int:
    root = project_root()
    print("Cadre institutionnel - commandes equivalentes (depuis la racine Momentum_Strategy) :\n")
    print("1) Baseline Train 1 -> results/institutional/train1_baseline/")
    print("   mstrat research-pipeline train1-baseline")
    print()
    print("2) Grille stress couts Train 1 (2010-2018) -> results/institutional/train1_cost_stress/")
    print("   mstrat research-pipeline train1-cost-stress")
    print()
    print("3) Archive configs + dernier run du dossier train1_baseline/")
    print("   mstrat research-pipeline train1-archive")
    print()
    print("3b) Leviers optimisation (presets YAML, Train 1) -> results/institutional/train1_levers/")
    print("   mstrat research-pipeline train1-levers")
    print("   mstrat research-pipeline train1-levers --presets configs/train1_levers_presets.yaml")
    print("   mstrat research-pipeline train1-levers --presets configs/train1_signal_grid_presets.yaml")
    print("   mstrat research-pipeline train1-levers --presets configs/train1_risk_grid_presets.yaml")
    print("   mstrat research-pipeline train1-levers --presets configs/train1_universe_grid_presets.yaml")
    print()
    print("4) Validation finale OOS unique 2019-2024 -> results/institutional/validation/")
    print("   mstrat research-pipeline validation")
    print()
    print("5) OOS strict (alias fenêtre unique 2019-2024) -> results/institutional/oos_strict/")
    print(f"   mstrat research-pipeline oos-strict")
    print()
    print(f"Racine projet : {root}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Pipeline recherche institutionnelle (Train 1, val, OOS).")
    sub = parser.add_subparsers(dest="phase", required=True)

    p_print = sub.add_parser("print-commands", help="Afficher le plan de commandes")
    p_print.set_defaults(func=lambda a: print_commands())

    def _tb(a):
        return Path(a.data) if getattr(a, "data", None) else None

    p1 = sub.add_parser("train1-baseline", help="Backtest event-driven --train1 → institutional/train1_baseline")
    p1.add_argument("--data", type=Path, default=None)
    p1.add_argument("--with-benchmark-html", action="store_true")
    p1.set_defaults(
        func=lambda a: run_train1_baseline(data=_tb(a), skip_benchmark_html=not a.with_benchmark_html)
    )

    p2 = sub.add_parser("train1-cost-stress", help="Grille coûts sur RESEARCH_TRAIN_1_*")
    p2.add_argument("--data", type=Path, default=None)
    p2.add_argument("--mults", type=str, default="1.0,1.5,2.0")
    p2.add_argument("--with-benchmark-html", action="store_true")
    p2.set_defaults(
        func=lambda a: run_train1_cost_stress(
            mults=[float(x.strip()) for x in a.mults.split(",") if x.strip()],
            data=_tb(a),
            skip_benchmark_html=not a.with_benchmark_html,
        )
    )

    p3 = sub.add_parser("train1-archive", help="Archiver configs + dernier run train1_baseline")
    p3.add_argument("--dest", type=Path, default=None)
    p3.set_defaults(func=lambda a: run_archive_train1_baseline(dest=a.dest))

    p_lev = sub.add_parser(
        "train1-levers",
        help="Batch sensibilité leviers (YAML) sur RESEARCH_TRAIN_1_* → institutional/train1_levers",
    )
    p_lev.add_argument(
        "--presets",
        type=Path,
        default=None,
        help="YAML des scénarios (défaut: configs/train1_levers_presets.yaml)",
    )
    p_lev.add_argument("--data", type=Path, default=None)
    p_lev.add_argument(
        "--no-write-artifacts",
        action="store_true",
        help="Ne pas appeler save_results par scénario (plus rapide, moins d'artefacts)",
    )
    p_lev.add_argument("--only", type=str, default=None, help="Un seul scénario par nom")
    p_lev.set_defaults(
        func=lambda a: run_train1_levers(
            presets=a.presets,
            data=a.data,
            write_artifacts=not a.no_write_artifacts,
            only=a.only,
        )
    )

    p4 = sub.add_parser("validation", help=f"Validation {VALIDATION_START} → {VALIDATION_END}")
    p4.add_argument("--data", type=Path, default=None)
    p4.add_argument(
        "--with-benchmark-html",
        action="store_true",
        help="Générer strategy_vs_benchmark (plus lent).",
    )
    p4.set_defaults(
        func=lambda a: run_validation(data=_tb(a), skip_benchmark_html=not a.with_benchmark_html)
    )

    p5 = sub.add_parser("oos-strict", help=f"OOS strict {OOS_STRICT_START} → {OOS_STRICT_END}")
    p5.add_argument("--data", type=Path, default=None)
    p5.add_argument("--with-benchmark-html", action="store_true")
    p5.set_defaults(
        func=lambda a: run_oos_strict(data=_tb(a), skip_benchmark_html=not a.with_benchmark_html)
    )

    p_all = sub.add_parser(
        "train1-full",
        help="Enchaîne train1-baseline + train1-cost-stress + train1-archive (long)",
    )
    p_all.add_argument("--data", type=Path, default=None)
    p_all.add_argument("--mults", type=str, default="1.0,1.5,2.0")
    p_all.set_defaults(func=lambda a: _train1_full(a))

    args = parser.parse_args(argv)
    return int(args.func(args))


def _train1_full(args: argparse.Namespace) -> int:
    data = Path(args.data) if args.data else None
    rc = run_train1_baseline(data=data, skip_benchmark_html=True)
    if rc != 0:
        return rc
    rc = run_train1_cost_stress(
        mults=[float(x.strip()) for x in args.mults.split(",") if x.strip()],
        data=data,
        skip_benchmark_html=True,
    )
    if rc != 0:
        return rc
    return run_archive_train1_baseline(dest=None)


if __name__ == "__main__":
    raise SystemExit(main())
