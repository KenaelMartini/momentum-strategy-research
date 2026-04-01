from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from momentum_strategy.paths import project_root
from momentum_strategy.universe import Universe

from .ibkr import load_ibkr_settings
from .validators import assert_columns_match, validate_ohlcv_frame

logger = logging.getLogger(__name__)


def _expected_symbols(universe: Universe, stocks_only: bool, futures_only: bool) -> list[tuple[str, str]]:
    if stocks_only and futures_only:
        raise ValueError("Choisir stocks_only OU futures_only, pas les deux.")
    if stocks_only:
        return [(s, "stock") for s in universe.stocks]
    if futures_only:
        return [(s, "future") for s in universe.futures]
    return [(s, "stock") for s in universe.stocks] + [(s, "future") for s in universe.futures]


def load_raw_series(
    raw_dir: Path,
    universe: Universe,
    *,
    stocks_only: bool = False,
    futures_only: bool = False,
) -> dict[str, pd.DataFrame]:
    raw_dir = Path(raw_dir)
    out: dict[str, pd.DataFrame] = {}
    missing: list[str] = []
    for sym, kind in _expected_symbols(universe, stocks_only, futures_only):
        prefix = "stock" if kind == "stock" else "future"
        path = raw_dir / f"{prefix}_{sym}.csv"
        if not path.exists():
            missing.append(sym)
            continue
        df = pd.read_csv(path, index_col=0, parse_dates=True)
        df.sort_index(inplace=True)
        validate_ohlcv_frame(df, symbol=sym)
        out[sym] = df
    if missing:
        logger.warning("Fichiers raw manquants (%s): %s", len(missing), ", ".join(missing[:20]) + ("..." if len(missing) > 20 else ""))
    if not out:
        raise FileNotFoundError("Aucune série brute trouvée — lancer `mstrat fetch` ou copier des CSV dans data/raw/")
    return out


def frames_to_close_matrix(data_dict: dict[str, pd.DataFrame]) -> pd.DataFrame:
    cols = {}
    for sym, df in data_dict.items():
        if df is not None and "close" in df.columns:
            cols[sym] = df["close"]
    if not cols:
        raise ValueError("Aucune colonne close")
    price_matrix = pd.DataFrame(cols).sort_index()
    price_matrix = price_matrix.ffill()
    price_matrix = price_matrix.dropna(how="all")
    return price_matrix


def write_price_matrix(
    price_matrix: pd.DataFrame,
    processed_dir: Path,
    *,
    manifest_extra: dict[str, Any] | None = None,
) -> tuple[Path, Path]:
    processed_dir = Path(processed_dir)
    processed_dir.mkdir(parents=True, exist_ok=True)
    csv_path = processed_dir / "price_matrix.csv"
    price_matrix.to_csv(csv_path, index_label="date")
    manifest: dict[str, Any] = {
        "built_at_utc": datetime.now(timezone.utc).isoformat(),
        "rows": int(price_matrix.shape[0]),
        "columns": list(price_matrix.columns),
        "calendar_mode": "union_ffill",
        "price_matrix_csv": str(csv_path.resolve()),
    }
    if manifest_extra:
        manifest.update(manifest_extra)
    man_path = processed_dir / "price_matrix_manifest.yaml"
    man_path.write_text(yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True), encoding="utf-8")
    logger.info("Écrit %s (%s x %s)", csv_path.name, *price_matrix.shape)
    return csv_path, man_path


def load_price_matrix(path: Path | None = None, *, root: Path | None = None) -> pd.DataFrame:
    root = root or project_root()
    settings = load_ibkr_settings(root)
    p = Path(path) if path is not None else (settings.processed_dir / "price_matrix.csv")
    if not p.exists():
        raise FileNotFoundError(f"Matrice de prix introuvable: {p}")
    df = pd.read_csv(p, index_col=0, parse_dates=True)
    df.sort_index(inplace=True)
    return df


def build_price_matrix_pipeline(
    universe: Universe,
    *,
    stocks_only: bool = False,
    futures_only: bool = False,
    root: Path | None = None,
    strict_universe: bool = False,
    raw_dir: Path | None = None,
    processed_dir: Path | None = None,
) -> pd.DataFrame:
    root = root or project_root()
    settings = load_ibkr_settings(root)
    rdir = Path(raw_dir) if raw_dir is not None else settings.raw_dir
    pdir = Path(processed_dir) if processed_dir is not None else settings.processed_dir
    data = load_raw_series(rdir, universe, stocks_only=stocks_only, futures_only=futures_only)
    expected = [s for s, _ in _expected_symbols(universe, stocks_only, futures_only)]
    loaded = set(data.keys())
    if strict_universe and set(expected) != loaded:
        raise ValueError(f"Univers strict: manquants {sorted(set(expected) - loaded)}")
    pm = frames_to_close_matrix(data)
    assert_columns_match(loaded, pm)
    sources = [str((rdir / f"{'stock' if sym in universe.stocks else 'future'}_{sym}.csv").resolve()) for sym in pm.columns]
    write_price_matrix(
        pm,
        pdir,
        manifest_extra={
            "universe_version": universe.version,
            "sources": sources,
        },
    )
    return pm
