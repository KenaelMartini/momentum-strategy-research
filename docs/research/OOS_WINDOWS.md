# Fenêtres recherche, validation et OOS strict

Les bornes détaillées et des exemples de commandes sont dans [`configs/research_windows.yaml`](../../configs/research_windows.yaml).

## Principes

1. **Research train** : seule période où l’on explore ou ajuste les paramètres (dans la limite de votre gouvernance).
2. **Validation** : premier hors-échantillon pour vérifier le processus ; éviter l’optimisation répétée sur cette fenêtre.
3. **OOS strict** : spec figée, résultats servant de test final avant paper trading ou décision.

## Raccourcis déjà câblés

- `--train1` : `RESEARCH_TRAIN_1_START` → `RESEARCH_TRAIN_1_END` (voir `_config_body.txt` / shim `config`).
- `--oos1` : `RESEARCH_OOS_AFTER_TRAIN_1_START` → `RESEARCH_OOS_AFTER_TRAIN_1_END` (jusqu’à `BACKTEST_END`).

## Exemples explicites (recommandés dans research_windows.yaml)

```bash
# Validation 2020–2022
mstrat event-backtest --start 2020-01-01 --end 2022-12-31 --skip-baseline

# OOS strict 2023–2024
mstrat event-backtest --start 2023-01-01 --end 2024-12-31 --skip-baseline
```

Après gel de la spec pour l’OOS strict, toute modification de paramètres impose de **redéfinir** une nouvelle fenêtre OOS non contaminée.
