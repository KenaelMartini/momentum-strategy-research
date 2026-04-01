# Note de recherche — backtest event-driven (institutionnel)

Document interne : une **campagne** = une spec + trois fenêtres (Train 1 / validation / OOS strict). Remplir après les runs `mstrat research-pipeline` ou équivalent.

## 1. Hypothèses

- **Données** : source (IBKR), chemin `price_matrix.csv`, copie du manifeste dans l’archive du run.
- **Intégrité** : moteur jour-par-jour, pas de look-ahead sur les signaux ; pas de tuning sur validation/OOS pour cette campagne.
- **Coûts** : `TRANSACTION_COST_BPS`, `SLIPPAGE_BPS`, grille stress ×1 / ×1.5 / ×2 sur **Train 1** au minimum.
- **Critères de sélection** : référence [CRITERES_SELECTION.md](CRITERES_SELECTION.md) (version / date des seuils utilisés).

## 2. Gel de la spec

- **Commit / tag git** : _______________
- **Dossier archive** : `results/archive/...` (chemin) _______________
- **CLI gel** : uniquement configs YAML + `_config_body` tel qu’archivé (pas de `--rebalance-threshold` non documenté, sauf mention explicite ici) : _______________

## 3. Résultats par fenêtre (obligatoire)

### Train 1 (`RESEARCH_TRAIN_1_START` → `RESEARCH_TRAIN_1_END`, typiquement 2015-01-01 → 2019-12-31)

| Métrique | Valeur |
|----------|--------|
| CAGR | |
| Sharpe | |
| Max DD | |
| Calmar | |
| Valeur finale | |
| Nb trades | |
| Turnover / an | |

- **Stress coûts Train 1** : joindre ou citer `results/institutional/train1_cost_stress/summary.csv` (CAGR / Sharpe ×1, ×1.5, ×2).
- **Régimes (TREND / RISK_ON / TRANSITION / RISK_OFF)** : résumer ou référencer `regime_performance_effective_*.csv` du dossier `results/institutional/train1_baseline/`.

### Validation (2020-01-01 → 2022-12-31)

| Métrique | Valeur |
|----------|--------|
| CAGR | |
| Sharpe | |
| Max DD | |
| Valeur finale | |
| Nb trades | |
| Turnover / an | |

- **Régimes** : idem (artefacts sous `results/institutional/validation/`).

### OOS strict (2023-01-01 → 2024-12-31)

| Métrique | Valeur |
|----------|--------|
| CAGR | |
| Sharpe | |
| Max DD | |
| Valeur finale | |
| Nb trades | |
| Turnover / an | |

- **Régimes** : idem (`results/institutional/oos_strict/`).

## 4. Référence marché (mêmes dates)

- **Vs benchmark EW** : fichiers `strategy_vs_benchmark_*.html` si générés (`--with-benchmark-html` sur validation/OOS si besoin).
- **Conclusion qualitative** (alpha brut, DD relatif au EW) : _______________

## 5. Sensibilité Train 1 (si effectuée)

- Fichier presets : _______________
- Résumé CSV : `results/institutional/sensitivity_train1/summary.csv` (ou chemin) _______________
- Variante retenue / rejetée et pourquoi : _______________

## 6. Limites

- Univers / survivorship / ajustement des prix : [politique données](../politique_donnees.md).
- Comportement risque (suspensions, overlays) : extraits `rebal_diagnostics_*.csv` si pertinent.

## 7. Décision / suite

- [ ] Poursuivre vers paper trading (voir [PAPER_TRADING_GATE.md](PAPER_TRADING_GATE.md))
- [ ] Arrêt / refonte
- [ ] Autre : _______________

**Date**, **auteur**, **hash git** du dépôt : _______________
