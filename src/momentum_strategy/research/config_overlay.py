"""Application / restauration temporaire de clés sur le module `config` (batch sensibilité / leviers Train 1).

Les overrides sont des affectations dynamiques sur `config` ; elles doivent être restaurées après chaque
scénario pour éviter la dérive entre runs dans un même processus Python.
"""

from __future__ import annotations

from typing import Any

_MISSING = object()


def _coerce_config_value(name: str, value: Any) -> Any:
    if isinstance(value, str) and value.strip().lower() in ("true", "false"):
        return value.strip().lower() == "true"
    if isinstance(value, list) and name.upper().endswith("WINDOWS"):
        return [int(x) for x in value]
    if isinstance(value, dict) and name.upper().endswith("WEIGHTS"):
        return {int(k): float(v) for k, v in value.items()}
    return value


def apply_config_overrides(overrides: dict[str, Any] | None) -> dict[str, Any]:
    """Applique ``overrides`` sur ``config`` ; retourne un dict pour ``restore_config_overrides``."""
    if not overrides:
        return {}
    import config as c

    previous: dict[str, Any] = {}
    for raw_k, raw_v in overrides.items():
        k = str(raw_k)
        if k.startswith("_"):
            continue
        v = _coerce_config_value(k, raw_v)
        if hasattr(c, k):
            previous[k] = getattr(c, k)
        else:
            previous[k] = _MISSING
        setattr(c, k, v)
    return previous


def restore_config_overrides(previous: dict[str, Any]) -> None:
    import config as c

    for k, v in previous.items():
        if v is _MISSING:
            if hasattr(c, k):
                delattr(c, k)
        else:
            setattr(c, k, v)
