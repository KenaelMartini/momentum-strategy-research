# Momentum_Strategy

Projet structuré pour la recherche quantitative : **univers** (YAML), **ingestion IBKR**, **validation et matrice de prix**, **signal momentum** paramétrable, **backtest minimal** de démonstration.

## Prérequis

- Python 3.10+
- TWS ou IB Gateway (paper **7497** par défaut) pour télécharger les prix

## Installation

```bash
cd Momentum_Strategy
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
```

## Commandes

| Action | Commande |
|--------|----------|
| Télécharger les prix (TWS requis) | `mstrat fetch --stocks-only` |
| Forcer le retéléchargement | `mstrat fetch --stocks-only --force` |
| Sans cache disque | `mstrat fetch --stocks-only --no-cache` |
| Construire `price_matrix.csv` depuis `data/raw/` | `mstrat build-matrix --stocks-only` |
| Matrice stricte (tous les tickers) | `mstrat build-matrix --stocks-only --strict` |
| Backtest **minimal** (vectorisé, démo rapide) | `mstrat minimal-backtest` |
| Matrice / YAML stratégie personnalisés | `mstrat minimal-backtest --data chemin/matrix.csv --strategy chemin/strategy_defaults.yaml` |
| Backtest **event-driven** (sans look-ahead, risque Fist) | `mstrat event-backtest --skip-baseline --skip-strategy-benchmark-report` |
| Période + données explicites | `mstrat event-backtest --start 2020-01-01 --end 2021-12-31 --data data/processed/price_matrix.csv --output results/event_driven` |
| Module équivalent | `python -m momentum_strategy.event_driven --skip-baseline` |
| Archiver configs + manifeste (+ dernier run optionnel) | `mstrat archive-run --copy-latest-results` |
| Grille stress coûts (×1 / ×1.5 / ×2) | `mstrat cost-stress-grid --mults 1.0,1.5,2.0` |
| Batch sensibilité (YAML) | `mstrat sensitivity-batch --presets configs/sensitivity_presets.yaml` |
| **Pipeline institutionnel** (Train 1, stress, archive, val, OOS) | `mstrat research-pipeline print-commands` puis ex. `mstrat research-pipeline train1-full` |
| Seuil rebal. / taille book | `mstrat event-backtest --rebalance-threshold 0.03 --n-long 8 --n-short 5` |
| Cap ligne / levier ED / seuil signal | `mstrat event-backtest --max-position-size 0.08 --ed-max-leverage 0.9 --ed-signal-entry-eps 0.025` |
| Rebal / book (guide Train 1) | [docs/research/REBAL_BOOK_RISK_GUIDE.md](docs/research/REBAL_BOOK_RISK_GUIDE.md) |

**minimal-backtest** : pipeline `signals.momentum` + rebalancement mensuel simplifié (hors moteur jour-par-jour).

**event-backtest** : moteur `event_driven` + `event_driven_risk` (MomentumSignalGeneratorV2) + package `risk` (régime, overlay désactivables via `configs/`). Les paramètres communs viennent de `strategy_defaults.yaml` et du corps Fist embarqué (`runtime_config` + `_config_body.txt`). Surclasser le risque avec `configs/risk_event_driven.yaml`.

Fichiers générés : `data/raw/stock_*.csv`, `data/processed/price_matrix.csv`, `data/processed/price_matrix_manifest.yaml`, résultats sous `results/event_driven/` (non versionnés).

## Documentation

- [Objectifs](docs/objectifs.md)
- [Contraintes institutionnelles](docs/contraintes_institutionnelles.md)
- [Politique données](docs/politique_donnees.md)
- Recherche / OOS / stress : [docs/research/](docs/research/) — entrée [INSTITUTIONAL_WORKFLOW.md](docs/research/INSTITUTIONAL_WORKFLOW.md) (Train 1 → validation → OOS, critères, gel, gate paper)

## Arborescence

- `configs/` — univers, IBKR, paramètres de stratégie
- `src/momentum_strategy/` — package installable
- `data/raw`, `data/processed` — données locales (non versionnées)
- `tests/` — tests unitaires

Le bac à sable expérimental reste dans le dossier voisin `Fist` ; ce dépôt ne doit reprendre que le code stabilisé.
