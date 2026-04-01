# Couches risque — activation prudente (Train 1)

Ordre global signal → ordres et lecture des colonnes `stats_*.csv` : [REBAL_BOOK_RISK_GUIDE.md](REBAL_BOOK_RISK_GUIDE.md) (sections 6–8). Réentrée suspension, flat défensif et rampe de `risk_scaling` : [POST_REENTRY_AND_RAMP.md](POST_REENTRY_AND_RAMP.md).

Les flags vivent surtout dans [`_config_body.txt`](../../src/momentum_strategy/_config_body.txt) ; [`configs/risk_event_driven.yaml`](../../configs/risk_event_driven.yaml) peut **surcharger** n’importe quelle clé homonyme (merge générique dans [`runtime_config.py`](../../src/momentum_strategy/runtime_config.py)).

## Règle

**Une couche par vague** de tests sur Train 1 (2015–2019) : sinon impossible d’attribuer un effet à un mécanisme.

## Exemples de clés (non exhaustif)

| Clé | Effet typique |
|-----|----------------|
| `ENABLE_MARKET_OVERLAY` | Overlay d’exposition selon régime marché |
| `DEFENSIVE_FLAT_ENABLED` | Sortie cash « defensive flat » sous conditions DD / régime |

Pour activer via YAML, créer ou éditer `risk_event_driven.yaml` :

```yaml
# Exemple — NE PAS tout activer à la fois
ENABLE_MARKET_OVERLAY: true
```

Puis run :

```bash
mstrat event-backtest --train1 --skip-baseline --output results/institutional/train1_risk_overlay
```

## Analyse

- **Logs** : suspensions, régimes, messages `Defensive flat`, `Market regime`.
- **CSV** : `rebal_diagnostics_*.csv` (`signal_reason`, colonnes régime).
- **Agrégats** : `regime_performance_effective_*.csv` — comparer TREND / RISK_ON / RISK_OFF / TRANSITION avant/après.

## Après Train 1

Si une couche améliore DD ou Sharpe ×1.5 **sans** dégrader le mandat, documenter dans la note puis **geler** la spec avant validation 2020–2022.
