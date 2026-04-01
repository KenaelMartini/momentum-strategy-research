"""Enchaîne plusieurs backtests event-driven (une dimension à la fois), pour sensibilité auditables.

Entre scénarios, `_reset_event_driven_caps_from_strategy_defaults()` réapplique les caps ED / book
depuis `strategy_defaults.yaml` pour éviter la dérive de `config` quand `EventDrivenEngine` mute le module.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

import momentum_strategy.runtime_config  # noqa: F401

from config import BACKTEST_END, BACKTEST_START

from momentum_strategy.event_driven.engine import EventDrivenEngine
from momentum_strategy.paths import configs_dir, project_root
from momentum_strategy.research.config_overlay import apply_config_overrides, restore_config_overrides


def _extract_phase0_diagnostics(engine: EventDrivenEngine) -> dict[str, Any]:
    import config as c

    out: dict[str, Any] = {
        "cfg_regime_adx_blend_weight": float(getattr(c, "REGIME_ADX_BLEND_WEIGHT", 0.0)),
        "cfg_regime_hurst_blend_weight": float(getattr(c, "REGIME_HURST_BLEND_WEIGHT", 0.0)),
        "cfg_risk_parity_enabled": bool(getattr(c, "ED_RISK_PARITY_LINE_WEIGHTS_ENABLED", False)),
        "cfg_signal_risk_adjust_enabled": bool(getattr(c, "ED_SIGNAL_RISK_ADJUST_ENABLED", False)),
    }
    sig_gen = getattr(engine, "signal_gen", None)
    sig_diag = dict(getattr(sig_gen, "last_diagnostics", {}) or {})
    out["diag_signal_risk_adjust_applied"] = bool(sig_diag.get("signal_risk_adjust_applied", False))
    out["diag_risk_parity_applied"] = bool(sig_diag.get("risk_parity_applied", False))
    out["diag_gross_before_risk_parity"] = sig_diag.get("gross_before_risk_parity")
    out["diag_gross_after_risk_parity"] = sig_diag.get("gross_after_risk_parity")

    portfolio = getattr(engine, "portfolio", None)
    hist = list(getattr(portfolio, "history", []) or [])
    if hist:
        eff_counts: dict[str, int] = {}
        for st in hist:
            k = str(getattr(st, "market_regime_effective", "") or "")
            if not k:
                k = "UNKNOWN"
            eff_counts[k] = int(eff_counts.get(k, 0) + 1)
        out["diag_market_regime_effective_counts"] = json.dumps(eff_counts, ensure_ascii=False, sort_keys=True)
    else:
        out["diag_market_regime_effective_counts"] = "{}"
    return out


def _resolve_under_project(path: Path, *, root: Path, what: str) -> Path:
    """Chemin explicite ou relatif au CWD ; sinon relatif à la racine Momentum_Strategy."""
    p = Path(path).expanduser()
    if p.is_file():
        return p.resolve()
    anchored = (root / p).resolve()
    if anchored.is_file():
        return anchored
    raise FileNotFoundError(
        f"{what} introuvable : {path} (essayé {p.resolve()} et {anchored})"
    )


def _reset_event_driven_caps_from_strategy_defaults() -> None:
    """Réinitialise les clés mutées par EventDrivenEngine entre scénarios du batch."""
    import config as c

    p = configs_dir() / "strategy_defaults.yaml"
    if not p.exists():
        return
    s = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    if "max_position_size" in s:
        c.MAX_POSITION_SIZE = float(s["max_position_size"])
    if "ed_max_leverage" in s:
        c.ED_MAX_LEVERAGE = float(s["ed_max_leverage"])
    if "ed_signal_entry_eps" in s:
        c.ED_SIGNAL_ENTRY_EPS = float(s["ed_signal_entry_eps"])
    if "ed_short_notional_scale" in s:
        c.ED_SHORT_NOTIONAL_SCALE = float(s["ed_short_notional_scale"])
    if "event_driven_n_long" in s:
        c.EVENT_DRIVEN_N_LONG = int(s["event_driven_n_long"])
    if "event_driven_n_short" in s:
        c.EVENT_DRIVEN_N_SHORT = int(s["event_driven_n_short"])


def _run_one(
    name: str,
    out_dir: Path,
    data: Path,
    start: str,
    end: str,
    overrides: dict[str, Any],
    *,
    write_artifacts: bool = False,
) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    _reset_event_driven_caps_from_strategy_defaults()
    cfg_ov = overrides.get("config_overrides")
    prev_overlay = apply_config_overrides(cfg_ov if isinstance(cfg_ov, dict) else None)
    try:
        return _run_one_core(
            name,
            out_dir,
            data,
            start,
            end,
            overrides,
            write_artifacts=write_artifacts,
        )
    finally:
        restore_config_overrides(prev_overlay)


def _run_one_core(
    name: str,
    out_dir: Path,
    data: Path,
    start: str,
    end: str,
    overrides: dict[str, Any],
    *,
    write_artifacts: bool = False,
) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    root_ms = project_root()
    sp_raw = overrides.get("strategy_params")
    strategy_resolved: Path | None = None
    if sp_raw is not None:
        strategy_resolved = _resolve_under_project(
            Path(str(sp_raw)),
            root=root_ms,
            what="Fichier strategy_params YAML",
        )

    engine = EventDrivenEngine(
        data_path=str(data),
        start_date=start,
        end_date=end,
        output_dir=str(out_dir),
        skip_baseline_comparison=True,
        transaction_cost_stress_multiplier=overrides.get("stress_cost_mult"),
        rebalance_threshold=overrides.get("rebalance_threshold"),
        n_long_positions=int(overrides["n_long"]) if overrides.get("n_long") is not None else None,
        n_short_positions=int(overrides["n_short"]) if overrides.get("n_short") is not None else None,
        max_position_size=(
            float(overrides["max_position_size"]) if overrides.get("max_position_size") is not None else None
        ),
        ed_max_leverage=float(overrides["ed_max_leverage"]) if overrides.get("ed_max_leverage") is not None else None,
        ed_signal_entry_eps=(
            float(overrides["ed_signal_entry_eps"]) if overrides.get("ed_signal_entry_eps") is not None else None
        ),
        ed_short_notional_scale=(
            float(overrides["ed_short_notional_scale"])
            if overrides.get("ed_short_notional_scale") is not None
            else None
        ),
        skip_strategy_benchmark_report=True,
        strategy_params_path=strategy_resolved,
    )
    engine.run()
    if write_artifacts:
        engine.save_results()
    phase0_diag = _extract_phase0_diagnostics(engine)
    try:
        meta = {
            "scenario": name,
            "start": start,
            "end": end,
            "overrides": {k: repr(v) for k, v in overrides.items()},
            "phase0_diagnostics": phase0_diag,
        }
        (out_dir / "run_metadata_levers.json").write_text(
            json.dumps(meta, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    except OSError:
        pass
    row = {"scenario": name, **dict(engine.final_metrics)}
    row["rebalance_threshold"] = overrides.get("rebalance_threshold")
    row["n_long"] = overrides.get("n_long")
    row["n_short"] = overrides.get("n_short")
    row["stress_cost_mult"] = overrides.get("stress_cost_mult")
    row["max_position_size"] = overrides.get("max_position_size")
    row["ed_max_leverage"] = overrides.get("ed_max_leverage")
    row["ed_signal_entry_eps"] = overrides.get("ed_signal_entry_eps")
    row["ed_short_notional_scale"] = overrides.get("ed_short_notional_scale")
    row["strategy_params"] = str(strategy_resolved) if strategy_resolved is not None else None
    row["config_overrides"] = str(overrides.get("config_overrides")) if overrides.get("config_overrides") else None
    row.update(phase0_diag)
    return row


def run_from_yaml(
    preset_path: Path,
    *,
    data_path: Path | None = None,
    start: str | None = None,
    end: str | None = None,
    output_parent: Path | None = None,
    only: str | None = None,
    write_artifacts: bool = False,
) -> pd.DataFrame:
    root = project_root()
    preset_file = _resolve_under_project(Path(preset_path), root=root, what="Fichier presets YAML")
    raw = yaml.safe_load(preset_file.read_text(encoding="utf-8"))
    scenarios: list[dict] = raw.get("runs", [])
    if data_path is not None:
        data = _resolve_under_project(Path(data_path), root=root, what="price_matrix / data")
    else:
        data = root / "data" / "processed" / "price_matrix.csv"
    parent = Path(output_parent) if output_parent else root / "results" / "sensitivity"
    parent.mkdir(parents=True, exist_ok=True)
    start_d = start or BACKTEST_START
    end_d = end or BACKTEST_END

    rows: list[dict] = []
    for sc in scenarios:
        name = str(sc.get("name", "unnamed"))
        if only and name != only:
            continue
        overrides = {k: v for k, v in sc.items() if k != "name"}
        out_dir = parent / name.replace(" ", "_")
        rows.append(
            _run_one(
                name,
                out_dir,
                data,
                start_d,
                end_d,
                overrides,
                write_artifacts=write_artifacts,
            )
        )

    df = pd.DataFrame(rows)
    df.to_csv(parent / "summary.csv", index=False)
    return df


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Batch sensibilité depuis YAML (rebal, N long/short, strategy_params pour alpha, etc.).",
    )
    parser.add_argument("--presets", type=Path, required=True, help="YAML liste de runs (voir configs/sensitivity_presets.yaml)")
    parser.add_argument("--start", default=None)
    parser.add_argument("--end", default=None)
    parser.add_argument("--data", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--only", default=None, help="N'exécuter que le scénario de ce nom")
    parser.add_argument(
        "--write-artifacts",
        action="store_true",
        help="Après chaque scénario, appeler save_results() (stats, rebal_diagnostics, dashboard 3D, etc.) — plus lent.",
    )
    args = parser.parse_args(argv)
    df = run_from_yaml(
        args.presets,
        data_path=args.data,
        start=args.start,
        end=args.end,
        output_parent=args.output,
        only=args.only,
        write_artifacts=bool(args.write_artifacts),
    )
    print(df.to_string(index=False))
    out = Path(args.output) if args.output else project_root() / "results" / "sensitivity"
    print(f"\nRésumé CSV : {out / 'summary.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
