# Grille de stress des coûts

Le moteur applique un **multiplicateur unique** sur la commission et le slippage (bps) définis dans la config (`TRANSACTION_COST_BPS`, `SLIPPAGE_BPS`), comme en recherche Fist.

## Commande

```bash
cd Momentum_Strategy
mstrat cost-stress-grid --mults 1.0,1.5,2.0
```

Les options `--start`, `--end`, `--data`, `--output` fixent la fenêtre et les chemins. Par défaut : `BACKTEST_START` / `BACKTEST_END` et `data/processed/price_matrix.csv`.

Sortie : `results/cost_stress/summary.csv` (et un sous-dossier par multiplicateur avec les CSV/HTML habituels si vous relancez un run complet manuellement). Le script `cost-stress-grid` écrit au minimum `summary.csv` avec les métriques finales par ligne.

## Interprétation institutionnelle

Comparer **CAGR**, **Sharpe**, **nombre de trades** et **turnover moyen** (colonne `avg_turnover` si présente) entre ×1.0 et ×2.0. Un turnover élevé rend la stratégie vulnérable au stress de coûts : documenter si la perf nette reste dans une enveloppe acceptable pour votre mandat.

## Alternative unitaire

```bash
mstrat event-backtest --stress-cost-mult 1.5 --skip-baseline
```
