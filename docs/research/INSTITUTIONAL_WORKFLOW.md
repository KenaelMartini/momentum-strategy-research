# Workflow recherche institutionnelle — vue d’ensemble

Ce document regroupe le **cadre perf / risque / process** pour le backtest event-driven. Ne pas utiliser le **full sample** pour choisir les paramètres pendant une campagne active.

## KPI gates institutionnels (obligatoires)

- **Fenêtres officielles**:
  - **Train 1 (calibrage)**: `2010-01-01 -> 2018-12-31`
  - **OOS unique (validation finale)**: `2019-01-01 -> 2024-12-31`
- **Règle de freeze**: après `mstrat research-pipeline train1-archive`, aucune modification de config/presets avant le run OOS final.
- **Artefacts décisionnels minimum**: `summary.csv`, `run_metadata_levers.json`, snapshot presets/config, comparaison baseline vs variante (delta Sharpe / MaxDD / turnover).
- **Objectif risque prioritaire**: maximiser la robustesse Sharpe/MaxDD sous stress coûts (1.0 / 1.5 / 2.0), pas le CAGR seul.

## Gouvernance du code et des specs

- **Source de vérité d’exécution** : le dépôt **Momentum_Strategy** (`python -m momentum_strategy`, configs sous `configs/`). Le dossier **Fist** à côté est considéré comme **legacy / référence historique** : ne pas tuner en parallèle deux copies de `event_driven_risk` ou de la logique risque sans tracer explicitement l’écart (risque de résultats non reproductibles et de décisions contradictoires).
- **Gel des specs** : toute campagne qui fige des paramètres pour validation / OOS doit suivre [SPEC_GEL.md](SPEC_GEL.md) et archiver un run de référence ([REFERENCE_RUN.md](REFERENCE_RUN.md), `mstrat archive-run` après baseline). Le résumé des sensibilités seul ne suffit pas sans snapshot YAML + artefacts datés.

## Ordre d’exécution

1. **Critères** — Remplir / valider [CRITERES_SELECTION.md](CRITERES_SELECTION.md).
2. **Train 1 — baseline + stress + archive**  
   ```bash
   mstrat research-pipeline train1-full
   ```  
   Ou pas à pas : `train1-baseline` → `train1-cost-stress` → `train1-archive`.  
   Sorties : `results/institutional/train1_baseline/`, `results/institutional/train1_cost_stress/summary.csv`, `results/archive/train1_baseline_*`.
2b. **Leviers d’optimisation (Train 1, presets YAML)** — grille auditables (`config_overrides`, voir [SENSITIVITY.md](SENSITIVITY.md), [TRAIN1_LEVERS.md](TRAIN1_LEVERS.md)) :  
   `mstrat research-pipeline train1-levers` → `results/institutional/train1_levers/`.
3. **Sensibilité (optionnel)** — Un levier à la fois sur Train 1 :  
   `mstrat sensitivity-batch --presets configs/sensitivity_presets_train1.yaml --start 2010-01-01 --end 2018-12-31 --output results/institutional/sensitivity_train1`  
   Pour **chaque scénario**, conserver `stats_*.csv` / `rebal_diagnostics_*.csv` dans le dossier du scénario : ajouter `--write-artifacts` (voir [SENSITIVITY.md](SENSITIVITY.md)) — plus lent (dashboard 3D, exports régimes).
4. **Attribution book (optionnel)** — Après un `event-backtest` (ou un batch avec `--write-artifacts`) disposant de `rebal_diagnostics_*` avec `target_weights_json` :  
   `mstrat book-forward-attribution --rebal <chemin/rebal_diagnostics_*.csv> --horizon 21`
5. **Gel** — [SPEC_GEL.md](SPEC_GEL.md) + commit git.
6. **Validation finale OOS unique** — `mstrat research-pipeline validation` → `results/institutional/validation/` (2019-2024).
7. **OOS strict (alias fenêtre unique)** — `mstrat research-pipeline oos-strict` → `results/institutional/oos_strict/` (2019-2024).
8. **Note** — [NOTE_RECHERCHE_EVENT_DRIVEN.md](NOTE_RECHERCHE_EVENT_DRIVEN.md).
9. **Gate paper** — [PAPER_TRADING_GATE.md](PAPER_TRADING_GATE.md).

## Commandes utiles

```bash
mstrat research-pipeline print-commands
mstrat fetch --force
mstrat build-matrix --strict
mstrat data-quality-report
```

Fenêtres : [OOS_WINDOWS.md](OOS_WINDOWS.md), [research_windows.yaml](../../configs/research_windows.yaml).

Rebalance / book / risque : [REBAL_BOOK_RISK_GUIDE.md](REBAL_BOOK_RISK_GUIDE.md), [RISK_LAYERS_TRAIN1.md](RISK_LAYERS_TRAIN1.md).

Sensibilité / artefacts : [SENSITIVITY.md](SENSITIVITY.md).

## Check-list campagne (exécution manuelle)

Enchaîner les étapes **1 → 9** ci-dessus sans sauter validation ni OOS si l’objectif est une conclusion institutionnelle. Avant toute décision sur la **perf nette**, consulter [COST_STRESS.md](COST_STRESS.md). Les étapes 3–4 sont optionnelles mais recommandées pour l’audit des plateaux de courbe et du book.

## Rappel

- **Train 1** = seule zone de **tuning** (2010-01-01 → 2018-12-31).
- **Validation finale OOS** = 2019-01-01 → 2024-12-31, spec figée.
- **Aucun retuning** motivé par les résultats OOS 2019-2024.
