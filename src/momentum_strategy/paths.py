from __future__ import annotations

from pathlib import Path


def project_root() -> Path:
    """Racine du dépôt Momentum_Strategy (parent de `src/`)."""
    return Path(__file__).resolve().parents[2]


def configs_dir() -> Path:
    return project_root() / "configs"
