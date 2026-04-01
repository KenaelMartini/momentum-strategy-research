from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import pandas as pd
import yaml
from ib_insync import IB, ContFuture, Stock, util

from momentum_strategy.paths import project_root

from .validators import clean_ohlcv

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class IbkrSettings:
    host: str
    port: int
    client_id: int
    data_frequency: str
    history_duration: str
    data_type: str
    request_sleep_seconds: float
    cache_max_age_calendar_days: int
    raw_dir: Path
    processed_dir: Path


def load_ibkr_settings(root: Path | None = None) -> IbkrSettings:
    root = root or project_root()
    raw: dict[str, Any] = yaml.safe_load((root / "configs" / "ibkr.yaml").read_text(encoding="utf-8"))
    paths = raw.get("paths") or {}
    raw_rel = paths.get("raw", "data/raw")
    proc_rel = paths.get("processed", "data/processed")
    return IbkrSettings(
        host=str(raw["host"]),
        port=int(raw["port"]),
        client_id=int(raw["client_id"]),
        data_frequency=str(raw["data_frequency"]),
        history_duration=str(raw["history_duration"]),
        data_type=str(raw["data_type"]),
        request_sleep_seconds=float(raw.get("request_sleep_seconds", 0.5)),
        cache_max_age_calendar_days=int(raw.get("cache_max_age_calendar_days", 4)),
        raw_dir=(root / raw_rel).resolve(),
        processed_dir=(root / proc_rel).resolve(),
    )


class IBKRDataFetcher:
    """Téléchargement OHLCV via IBKR ; écriture sous `data/raw/`."""

    def __init__(self, settings: IbkrSettings | None = None, root: Path | None = None):
        self.root = root or project_root()
        self.settings = settings or load_ibkr_settings(self.root)
        self.ib = IB()
        self.settings.raw_dir.mkdir(parents=True, exist_ok=True)
        self.settings.processed_dir.mkdir(parents=True, exist_ok=True)

    def connect(self) -> bool:
        try:
            self.ib.connect(
                host=self.settings.host,
                port=self.settings.port,
                clientId=self.settings.client_id,
            )
            logger.info("Connecté à IBKR | host=%s port=%s", self.settings.host, self.settings.port)
            return True
        except Exception as e:
            logger.error("Échec connexion IBKR: %s", e)
            return False

    def disconnect(self) -> None:
        self.ib.disconnect()
        logger.info("Déconnecté de IBKR")

    @staticmethod
    def _stock_contract(symbol: str) -> Stock:
        # Some tickers require explicit primary exchange for historical bars.
        if symbol == "LIN":
            return Stock(symbol, "SMART", "USD", primaryExchange="NYSE")
        return Stock(symbol, "SMART", "USD")

    @staticmethod
    def _continuous_future_contract(symbol: str) -> ContFuture:
        exchange_map = {
            "CL": "NYMEX",
            "NG": "NYMEX",
            "GC": "COMEX",
            "SI": "COMEX",
            "HG": "COMEX",
            "ZC": "CBOT",
            "ZW": "CBOT",
            "ZS": "CBOT",
        }
        ex = exchange_map.get(symbol, "NYMEX")
        return ContFuture(symbol, ex, currency="USD")

    def _fetch_historical_bars(
        self,
        contract,
        *,
        duration: str | None = None,
        bar_size: str | None = None,
        what_to_show: str | None = None,
    ) -> Optional[pd.DataFrame]:
        duration = duration or self.settings.history_duration
        bar_size = bar_size or self.settings.data_frequency
        what_to_show = what_to_show or self.settings.data_type
        try:
            bars = self.ib.reqHistoricalData(
                contract,
                endDateTime="",
                durationStr=duration,
                barSizeSetting=bar_size,
                whatToShow=what_to_show,
                useRTH=True,
                formatDate=1,
                keepUpToDate=False,
            )
            if not bars:
                logger.warning("Aucune barre pour %s", getattr(contract, "symbol", contract))
                return None
            df = util.df(bars)[["date", "open", "high", "low", "close", "volume"]].copy()
            df["date"] = pd.to_datetime(df["date"])
            df.set_index("date", inplace=True)
            df.sort_index(inplace=True)
            return df
        except Exception as e:
            logger.error("Erreur historique %s: %s", getattr(contract, "symbol", "?"), e)
            return None

    def _cache_path(self, symbol: str, asset_type: str) -> Path:
        prefix = "stock" if asset_type == "stock" else "future"
        return self.settings.raw_dir / f"{prefix}_{symbol}.csv"

    def _cache_is_fresh(self, df: pd.DataFrame) -> bool:
        if df is None or df.empty:
            return False
        last = pd.Timestamp(df.index.max()).normalize()
        today = pd.Timestamp.now().normalize()
        age = (today - last).days
        return age <= self.settings.cache_max_age_calendar_days

    def _load_cache(self, symbol: str, asset_type: str) -> Optional[pd.DataFrame]:
        path = self._cache_path(symbol, asset_type)
        if not path.exists():
            return None
        df = pd.read_csv(path, index_col=0, parse_dates=True)
        df.sort_index(inplace=True)
        return df

    def _save_cache(self, df: pd.DataFrame, symbol: str, asset_type: str) -> None:
        path = self._cache_path(symbol, asset_type)
        df.to_csv(path)
        logger.debug("Sauvegardé %s", path)

    def fetch_stocks_data(
        self,
        symbols: list[str],
        *,
        use_cache: bool = True,
        force: bool = False,
    ) -> dict[str, pd.DataFrame]:
        out: dict[str, pd.DataFrame] = {}
        for i, symbol in enumerate(symbols):
            logger.info("[%s/%s] %s", i + 1, len(symbols), symbol)
            if use_cache and not force:
                cached = self._load_cache(symbol, "stock")
                if cached is not None and self._cache_is_fresh(cached):
                    out[symbol] = cached
                    continue
            contract = self._stock_contract(symbol)
            try:
                self.ib.qualifyContracts(contract)
            except Exception as e:
                logger.error("Contrat invalide %s: %s", symbol, e)
                continue
            df = self._fetch_historical_bars(contract)
            if df is None:
                continue
            df = clean_ohlcv(df, symbol)
            self._save_cache(df, symbol, "stock")
            out[symbol] = df
            time.sleep(self.settings.request_sleep_seconds)
        logger.info("Actions OK: %s/%s", len(out), len(symbols))
        return out

    def fetch_futures_data(
        self,
        symbols: list[str],
        *,
        use_cache: bool = True,
        force: bool = False,
    ) -> dict[str, pd.DataFrame]:
        out: dict[str, pd.DataFrame] = {}
        for i, symbol in enumerate(symbols):
            logger.info("[%s/%s] future %s", i + 1, len(symbols), symbol)
            if use_cache and not force:
                cached = self._load_cache(symbol, "future")
                if cached is not None and self._cache_is_fresh(cached):
                    out[symbol] = cached
                    continue
            contract = self._continuous_future_contract(symbol)
            try:
                self.ib.qualifyContracts(contract)
            except Exception as e:
                logger.error("Contrat future invalide %s: %s", symbol, e)
                continue
            df = self._fetch_historical_bars(contract, what_to_show="TRADES")
            if df is None:
                continue
            df = clean_ohlcv(df, symbol)
            self._save_cache(df, symbol, "future")
            out[symbol] = df
            time.sleep(self.settings.request_sleep_seconds)
        logger.info("Futures OK: %s/%s", len(out), len(symbols))
        return out
