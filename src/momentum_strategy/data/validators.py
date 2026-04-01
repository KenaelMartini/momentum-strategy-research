from __future__ import annotations

import logging
from typing import Iterable

import pandas as pd

logger = logging.getLogger(__name__)

REQUIRED_COLS = ("open", "high", "low", "close", "volume")


def validate_ohlcv_frame(df: pd.DataFrame, *, symbol: str) -> None:
    """Lève ValueError si la série brute n'est pas utilisable."""
    if df is None or df.empty:
        raise ValueError(f"{symbol}: DataFrame vide")
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"{symbol}: colonnes manquantes {missing}")
    idx = df.index
    if not idx.is_monotonic_increasing:
        raise ValueError(f"{symbol}: index dates non croissant")
    if idx.duplicated().any():
        raise ValueError(f"{symbol}: dates dupliquées dans l'index")
    for c in ("open", "high", "low", "close"):
        if (df[c] <= 0).any():
            raise ValueError(f"{symbol}: prix {c} non strictement positifs")
    ohlc_ok = (df["high"] >= df[["open", "close"]].max(axis=1)) & (
        df["low"] <= df[["open", "close"]].min(axis=1)
    )
    if not ohlc_ok.all():
        bad = int((~ohlc_ok).sum())
        raise ValueError(f"{symbol}: {bad} lignes OHLC incohérentes")


def log_extreme_returns(df: pd.DataFrame, symbol: str, threshold: float = 0.5) -> None:
    r = df["close"].pct_change()
    n = int((r.abs() > threshold).sum())
    if n > 0:
        logger.warning(
            "%s: %s rendements journaliers |r| > %.0f%% — vérifier ajustements splits/dividendes",
            symbol,
            n,
            threshold * 100,
        )


def clean_ohlcv(df: pd.DataFrame, symbol: str) -> pd.DataFrame:
    """Nettoyage défensif avant sauvegarde raw (aligné sur Fist)."""
    out = df.copy()
    out = out[~out.index.duplicated(keep="last")]
    out = out.ffill().dropna()
    for c in ("close", "open", "high", "low"):
        out = out[out[c] > 0]
    valid = (out["high"] >= out[["open", "close"]].max(axis=1)) & (
        out["low"] <= out[["open", "close"]].min(axis=1)
    )
    out = out[valid]
    log_extreme_returns(out, symbol)
    return out


def assert_columns_match(universe_cols: Iterable[str], price_matrix: pd.DataFrame) -> None:
    missing = set(universe_cols) - set(price_matrix.columns)
    if missing:
        raise ValueError(f"Colonnes manquantes dans la matrice: {sorted(missing)}")
