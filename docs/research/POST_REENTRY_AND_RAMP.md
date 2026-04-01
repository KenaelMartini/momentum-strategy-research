# Réentrée circuit breaker, flat défensif et rampe de déploiement

Ce document regroupe les paramètres `config` qui pilotent le temps passé hors marché et l’adoucissement du déploiement après une longue phase cash. Les valeurs par défaut vivent dans [`src/momentum_strategy/_config_body.txt`](../../src/momentum_strategy/_config_body.txt) ; des overrides optionnels passent par [`configs/risk_event_driven.yaml`](../../configs/risk_event_driven.yaml) (fusion dans `runtime_config`).

**Règle institutionnelle** : activer et calibrer **une** famille de leviers à la fois sur la fenêtre train pour isoler l’effet (voir en-tête de `risk_event_driven.yaml`).

## Suspension (max DD) et réentrée

| Paramètre | Rôle |
|-----------|------|
| `MAX_PORTFOLIO_DRAWDOWN` | Seuil de déclenchement du circuit breaker (liquidation → cash). |
| `SUSPENSION_COOLDOWN_CALENDAR_DAYS` | Jours calendaires minimum avant réentrée possible. |
| `SUSPENSION_REENTRY_DD_FROM_EXIT` | Condition sur le rendement depuis la valeur de sortie en cash (voie « lente »). |
| `SUSPENSION_REENTRY_FAST_CALENDAR_DAYS` / `SUSPENSION_REENTRY_FAST_DD_FROM_EXIT` | Voie rapide si configurée. |
| `SUSPENSION_REENTRY_REQUIRE_REGIME_CONFIRMATION` | Si `True`, exige des jours consécutifs dans `SUSPENSION_REENTRY_ALLOWED_RISK_REGIMES`. |
| `SUSPENSION_REENTRY_ALLOWED_RISK_REGIMES` | Régimes risk autorisés pour la confirmation. |
| `SUSPENSION_REENTRY_MIN_CONSECUTIVE_RISK_DAYS` | Nombre de jours consécutifs requis. |

Implémentation : [`event_driven_risk.py`](../../src/momentum_strategy/event_driven_risk.py) (bloc `trading_suspended`). À la réentrée, `mark_deployment_ramp_start` est appelé **dans** le risk manager (même jour que la levée de suspension).

## Garde-fous post-réentrée (optionnels)

| Paramètre | Rôle |
|-----------|------|
| `SUSPENSION_POST_REENTRY_RECUT_*` | Fenêtre de perte vs ancre après réinvestissement. |
| `SUSPENSION_POST_REENTRY_GUARD_*` | Garde-fou sur drawdown depuis pic local après réentrée. |
| `REBALANCE_WINDOW_LOSS_CUT_*` | Perte max vs PV post-rebalance sur N séances. |

## Flat défensif (hors circuit breaker)

| Paramètre | Rôle |
|-----------|------|
| `DEFENSIVE_FLAT_ENABLED` | Active la machine à états flat. |
| `DEFENSIVE_FLAT_ENTRY_*` | Conditions d’entrée (régime effectif + DD + jours consécutifs). |
| `DEFENSIVE_FLAT_MIN_CALENDAR_DAYS` | Durée minimale en flat avant écoute de la réentrée. |
| `DEFENSIVE_FLAT_REENTRY_*` | Conditions de réentrée (régime effectif et/ou risk). |

Implémentation : [`risk/defensive_flat.py`](../../src/momentum_strategy/risk/defensive_flat.py). À la **sortie** du flat, le moteur programme une ancre de rampe au **premier jour de bourse suivant** (`mark_deployment_ramp_start` au début de la boucle), pour que le `risk_snapshot` du jour tienne compte de la rampe.

## Rampe de déploiement (`risk_scaling`)

Réduit temporairement le `risk_scaling` appliqué aux poids (même signal momentum).

| Paramètre | Rôle |
|-----------|------|
| `SUSPENSION_REENTRY_RAMP_ENABLED` | Active la rampe. |
| `DEPLOYMENT_RAMP_SCHEDULE` | `"calendar"` : index par jours calendaires depuis l’ancre ; `"rebalance"` : index par nombre de rebalances investis complétés depuis l’ancre. |
| `SUSPENSION_REENTRY_RAMP_SCALES` | Tuple de multiplicateurs (mode calendrier). |
| `SUSPENSION_REENTRY_RAMP_REBALANCE_SCALES` | Tuple (mode rebalance). |
| `POST_DEPLOYMENT_RISK_EXTRA_MULT` | Multiplicateur additionnel sur la fenêtre (si ≠ 1). |
| `POST_DEPLOYMENT_RISK_ADJUST_CALENDAR_DAYS` | Nombre de jours calendaires depuis l’ancre pendant lesquels s’appliquent `EXTRA_MULT` et le cap ; `0` = désactivé. La rampe et cet ajustement se **désancrent** quand la rampe est terminée **et** (si `ADJUST_CALENDAR_DAYS` > 0) la fenêtre d’ajustement est écoulée. |
| `POST_DEPLOYMENT_RISK_SCALE_CAP` | Si > 0, plafond sur `risk_scaling` pendant la même fenêtre que `ADJUST_CALENDAR_DAYS`. |

Ordre dans le risk manager : vol scaling → underwater prolongé → **rampe** → **ajustement post-déploiement** → snapshot.

Diagnostics rebal : `deployment_ramp_schedule`, `deployment_ramp_index`, `risk_scaling_pre_deployment_ramp`.

## Fichiers liés

- [`event_driven/engine.py`](../../src/momentum_strategy/event_driven/engine.py) — `note_rebalance_completed_for_deployment_ramp`, pending flat exit.
- [`event_driven_risk.py`](../../src/momentum_strategy/event_driven_risk.py) — logique principale.
