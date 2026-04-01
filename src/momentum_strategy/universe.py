from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from momentum_strategy.paths import configs_dir

_TICKER_RE = re.compile(r"^[A-Z0-9.\-]{1,20}$")


@dataclass(frozen=True)
class Universe:
    version: str
    eligibility: str
    stocks: tuple[str, ...]
    futures: tuple[str, ...]

    def all_symbols_for_fetch(self, stocks_only: bool, futures_only: bool) -> list[str]:
        if stocks_only and futures_only:
            raise ValueError("Choisir stocks_only OU futures_only, pas les deux.")
        if stocks_only:
            return list(self.stocks)
        if futures_only:
            return list(self.futures)
        return list(self.stocks) + list(self.futures)


def _validate_symbol(sym: str, *, ctx: str) -> str:
    s = sym.strip().upper()
    if not s or not _TICKER_RE.match(s):
        raise ValueError(f"Symbole invalide ({ctx}): {sym!r}")
    return s


def load_universe(path: Path | None = None) -> Universe:
    p = path or (configs_dir() / "universe.yaml")
    raw: dict[str, Any] = yaml.safe_load(p.read_text(encoding="utf-8"))
    version = str(raw.get("version", "0"))
    eligibility = str(raw.get("eligibility", "")).strip()
    stocks_raw = raw.get("stocks") or []
    fut_raw = raw.get("futures") or []
    if not isinstance(stocks_raw, list) or not isinstance(fut_raw, list):
        raise ValueError("universe.yaml: 'stocks' et 'futures' doivent être des listes.")

    stocks = [_validate_symbol(x, ctx="stock") for x in stocks_raw]
    futures = [_validate_symbol(x, ctx="future") for x in fut_raw]

    if len(set(stocks)) != len(stocks):
        raise ValueError("Doublons dans universe.stocks")
    if len(set(futures)) != len(futures):
        raise ValueError("Doublons dans universe.futures")

    return Universe(
        version=version,
        eligibility=eligibility,
        stocks=tuple(stocks),
        futures=tuple(futures),
    )
