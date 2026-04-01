# Leviers d’optimisation — Train 1

Ce document décrit les **interrupteurs** ajoutés pour la campagne institutionnelle (signal, risque, régime, coûts, univers, multi-signaux). Les défauts sont dans [`src/momentum_strategy/_config_body.txt`](../../src/momentum_strategy/_config_body.txt) ; surcharge via [`configs/risk_event_driven.yaml`](../../configs/risk_event_driven.yaml) ou **`config_overrides`** dans les presets YAML ([`configs/train1_levers_presets.yaml`](../../configs/train1_levers_presets.yaml)).

## Signal

| Clé | Rôle |
|-----|------|
| `ED_SIGNAL_RISK_ADJUST_ENABLED` | Divise le signal CS par la vol EWMA annualisée (comparaison type Sharpe implicite). |
| `ED_SIGNAL_VOL_FLOOR_ANNUAL` | Plancher vol (annualisé) pour le diviseur. |
| `ED_SIGNAL_HALF_LIFE_REBALANCES` | Décroissance `exp(-n_rebal/τ)` sur le signal ; 0 = off. |
| `ED_SIGNAL_DECAY_RESET_WHEN_FLAT` | Remet le compteur à 0 si portefeuille cible plat. |
| `ED_SIGNAL_BLEND_CONTRARIAN_WEIGHT` | Mélange avec un signal contrarien (rank percentile). |
| `ED_SIGNAL_EXIT_MAX_RANK_FRACTION` | Sort les lignes détenues si le rang CS se dégrade (0 = off). |
| `ED_MULTI_SIGNAL_VALUE_WEIGHT` | Mélange momentum avec un proxy **value** (inverse rendement long terme, z-score CS). |
| `ED_MULTI_SIGNAL_CARRY_WEIGHT` | Réservé (carry explicite non disponible sur matrice close-only). |

## Sizing / risque

| Clé | Rôle |
|-----|------|
| `ED_RISK_PARITY_LINE_WEIGHTS_ENABLED` | Après sélection L/S, rescale les poids bruts en ~1/σ par ligne puis rétablit le gross. |
| `ED_TURNOVER_CAP_PER_REBALANCE_FRACTION` | Plafond Σ|Δw| par rebalance (fraction capital). |
| `ED_PER_LINE_REBAL_BUFFER` | Augmente le seuil de rebalance (réduit le bruit). |

Vol cible portfolio : déjà gérée par `TARGET_VOLATILITY` et `risk_scaling` ; la vol réalisée 21j est dans les `PortfolioStats` (`realized_vol`).

## Régime

| Clé | Rôle |
|-----|------|
| `REGIME_ADX_BLEND_WEIGHT` | Poids de l’**ADX** synthétique (marché EW) dans le score composite. |
| `REGIME_HURST_BLEND_WEIGHT` | Poids d’un **proxy Hurst** (autocorr lag-1 des rendements marché). |

## Coûts / exécution simulée

| Clé | Rôle |
|-----|------|
| `BROKER_IMPACT_SLIPPAGE_MULT` | Multiplicateur ≥ 1 sur le slippage du broker simulé. |

## Univers

| Clé | Rôle |
|-----|------|
| `ED_UNIVERSE_MIN_LAST_PRICE` | Exclut les titres dont le dernier prix est sous le seuil (proxy liquidité). |

## Résiduel sectoriel / macro / ML

Neutralisation sectorielle, séries macro (VIX/courbe), ML sur les poids : **hors périmètre** de ce lot — à brancher avec jeux de données dédiés et protocole anti-fuite (walk-forward Train 1).

## Commande

```bash
mstrat research-pipeline train1-levers
```

## Presets par phase (roadmap 2010-2018)

- Phase 2 signal: `configs/train1_signal_grid_presets.yaml`
- Phase 3 risque: `configs/train1_risk_grid_presets.yaml`
- Phase 4 univers/book: `configs/train1_universe_grid_presets.yaml`

Exécution type:

```bash
mstrat research-pipeline train1-levers --presets configs/train1_signal_grid_presets.yaml
```

Pour la validation finale OOS (2019-2024), geler d'abord la config:

```bash
mstrat research-pipeline train1-archive
mstrat research-pipeline validation
```
