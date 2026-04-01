# ============================================================
# runtime_config — namespace compatible `config` (Fist) + fusion YAML
# S'enregistre comme sys.modules["config"] pour les modules non migrés.
# ============================================================
from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Any

import yaml

from momentum_strategy.paths import configs_dir, project_root

_BODY_PATH = Path(__file__).with_name("_config_body.txt")


def _exec_fist_defaults(g: dict[str, Any]) -> None:
    if not _BODY_PATH.exists():
        raise FileNotFoundError(f"Manque {_BODY_PATH} (extrait du config Fist)")
    src = _BODY_PATH.read_text(encoding="utf-8")
    exec(compile(src, str(_BODY_PATH), "exec"), g)


def _resolve_paths(g: dict[str, Any]) -> None:
    root = project_root()
    g["DATA_PATH"] = str(root / "data" / "raw").replace("\\", "/") + "/"
    g["PROCESSED_DATA_PATH"] = str(root / "data" / "processed").replace("\\", "/") + "/"


def _merge_strategy_defaults(g: dict[str, Any]) -> None:
    p = configs_dir() / "strategy_defaults.yaml"
    if not p.exists():
        return
    s = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    if "backtest_start" in s:
        g["BACKTEST_START"] = str(s["backtest_start"])
    if "backtest_end" in s:
        g["BACKTEST_END"] = str(s["backtest_end"])
    if "initial_capital" in s:
        g["INITIAL_CAPITAL"] = float(s["initial_capital"])
    if "transaction_cost_bps" in s:
        g["TRANSACTION_COST_BPS"] = float(s["transaction_cost_bps"])
    if "slippage_bps" in s:
        g["SLIPPAGE_BPS"] = float(s["slippage_bps"])
    if "risk_free_rate" in s:
        g["RISK_FREE_RATE"] = float(s["risk_free_rate"])
    if "momentum_weights" in s and s["momentum_weights"]:
        g["MOMENTUM_WEIGHTS"] = {int(k): float(v) for k, v in s["momentum_weights"].items()}
    if "momentum_windows" in s:
        g["MOMENTUM_WINDOWS"] = [int(x) for x in s["momentum_windows"]]
    if "skip_days" in s:
        g["SKIP_DAYS"] = int(s["skip_days"])
    if "long_quantile" in s:
        g["LONG_QUANTILE"] = float(s["long_quantile"])
    if "short_quantile" in s:
        g["SHORT_QUANTILE"] = float(s["short_quantile"])
    if "long_quantile" in s:
        g["LONG_QUANTILE"] = float(s["long_quantile"])
    if "rebalancing_frequency" in s:
        g["REBALANCING_FREQUENCY"] = str(s["rebalancing_frequency"])
    if "target_volatility" in s:
        g["TARGET_VOLATILITY"] = float(s["target_volatility"])
    if "max_position_size" in s:
        g["MAX_POSITION_SIZE"] = float(s["max_position_size"])
    if "max_leverage" in s:
        g["MAX_LEVERAGE"] = float(s["max_leverage"])
    if "ed_max_leverage" in s:
        g["ED_MAX_LEVERAGE"] = float(s["ed_max_leverage"])
    if "ed_signal_entry_eps" in s:
        g["ED_SIGNAL_ENTRY_EPS"] = float(s["ed_signal_entry_eps"])
    if "ed_short_notional_scale" in s:
        g["ED_SHORT_NOTIONAL_SCALE"] = float(s["ed_short_notional_scale"])
    if "event_driven_n_long" in s:
        g["EVENT_DRIVEN_N_LONG"] = int(s["event_driven_n_long"])
    if "event_driven_n_short" in s:
        g["EVENT_DRIVEN_N_SHORT"] = int(s["event_driven_n_short"])


def _merge_risk_event_driven(g: dict[str, Any]) -> None:
    """Fusionne `configs/risk_event_driven.yaml` dans le namespace `config`.

    Expose pour debug : ``RISK_EVENT_DRIVEN_YAML_PATH``, ``RISK_EVENT_DRIVEN_MERGED_KEYS``.
    """
    p = configs_dir() / "risk_event_driven.yaml"
    g["RISK_EVENT_DRIVEN_YAML_PATH"] = str(p.resolve())
    g["RISK_EVENT_DRIVEN_MERGED_KEYS"] = ()
    if not p.exists():
        _maybe_log_risk_yaml_debug(g, present=False, merged_keys=(), reason="fichier absent")
        return
    raw = yaml.safe_load(p.read_text(encoding="utf-8"))
    if not raw:
        _maybe_log_risk_yaml_debug(g, present=True, merged_keys=(), reason="fichier vide ou uniquement commentaires")
        return
    merged: list[str] = []
    for k, v in raw.items():
        if isinstance(k, str) and k.startswith("_"):
            continue
        g[str(k)] = v
        merged.append(str(k))
    g["RISK_EVENT_DRIVEN_MERGED_KEYS"] = tuple(sorted(merged))
    _maybe_log_risk_yaml_debug(g, present=True, merged_keys=g["RISK_EVENT_DRIVEN_MERGED_KEYS"], reason=None)


def _maybe_log_risk_yaml_debug(
    g: dict[str, Any],
    *,
    present: bool,
    merged_keys: tuple[str, ...],
    reason: str | None,
) -> None:
    flag = os.environ.get("MSTRAT_DEBUG_RISK_CONFIG", "").strip().lower()
    if flag not in ("1", "true", "yes"):
        return
    log = logging.getLogger("momentum_strategy.runtime_config")
    path = g.get("RISK_EVENT_DRIVEN_YAML_PATH", "?")
    log.info("[MSTRAT_DEBUG_RISK_CONFIG] yaml_path=%s present=%s", path, present)
    if reason:
        log.info("[MSTRAT_DEBUG_RISK_CONFIG] merge: %s", reason)
    else:
        log.info("[MSTRAT_DEBUG_RISK_CONFIG] clés fusionnées (%d): %s", len(merged_keys), merged_keys)
    for name in (
        "SUSPENSION_REENTRY_RAMP_ENABLED",
        "DEPLOYMENT_RAMP_SCHEDULE",
        "POST_DEPLOYMENT_RISK_ADJUST_CALENDAR_DAYS",
    ):
        if name in g:
            log.info("[MSTRAT_DEBUG_RISK_CONFIG] config.%s = %r", name, g[name])


_g = globals()
_exec_fist_defaults(_g)
_resolve_paths(_g)
_merge_strategy_defaults(_g)
_merge_risk_event_driven(_g)

sys.modules.setdefault("config", sys.modules[__name__])
