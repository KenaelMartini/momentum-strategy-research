# Sensibilité (rebal, N long / short)

## Ligne de commande (un run)

```bash
mstrat event-backtest --rebalance-threshold 0.03 --skip-baseline
mstrat event-backtest --n-long 8 --n-short 5 --skip-baseline
```

## Pipeline Train 1 — leviers (`train1-levers`)

Enchaîne automatiquement les scénarios du fichier [`configs/train1_levers_presets.yaml`](../../configs/train1_levers_presets.yaml) sur **RESEARCH_TRAIN_1_*** vers `results/institutional/train1_levers/` :

```bash
mstrat research-pipeline train1-levers
```

Options : `--presets <chemin.yaml>`, `--data <price_matrix.csv>`, `--only <nom_scénario>`, `--no-write-artifacts` (plus rapide). Chaque dossier de scénario reçoit un `run_metadata_levers.json`. Détail des clés : [TRAIN1_LEVERS.md](TRAIN1_LEVERS.md).

Presets roadmap:
- `configs/train1_signal_grid_presets.yaml` (phase 2 signal)
- `configs/train1_risk_grid_presets.yaml` (phase 3 risque)
- `configs/train1_universe_grid_presets.yaml` (phase 4 univers)

### `config_overrides` dans un preset YAML

Sous chaque scénario, une clé **`config_overrides`** : dictionnaire `{ NOM_CONSTANTE_CONFIG: valeur }` appliqué sur le module `config` **avant** le run puis **restauré** après (voir [`research/config_overlay.py`](../../src/momentum_strategy/research/config_overlay.py)). Les noms doivent correspondre à [`_config_body.txt`](../../src/momentum_strategy/_config_body.txt) (ex. `ED_SIGNAL_RISK_ADJUST_ENABLED`, `REGIME_ADX_BLEND_WEIGHT`).

## Train 1 uniquement

Pour limiter le tuning à l’in-sample institutionnel, utiliser [`configs/sensitivity_presets_train1.yaml`](../../configs/sensitivity_presets_train1.yaml) avec `--start 2010-01-01 --end 2018-12-31` et `--output results/institutional/sensitivity_train1`.

Presets dédiés : [`sensitivity_rebal_train1.yaml`](../../configs/sensitivity_rebal_train1.yaml) (seuil rebal), [`sensitivity_book_train1.yaml`](../../configs/sensitivity_book_train1.yaml) (N L/S, max pos, ED levier, eps signal). Guide : [REBAL_BOOK_RISK_GUIDE.md](REBAL_BOOK_RISK_GUIDE.md).

## Alpha (signal momentum) — `strategy_params`

Pour faire varier **l’alpha** (poids d’horizons, quantiles CS, `signal_cs_weight` / `signal_ts_weight`, etc.) sans remplacer [`configs/strategy_defaults.yaml`](../../configs/strategy_defaults.yaml) entre chaque run :

- Chaque scénario peut déclarer une clé **`strategy_params`** : chemin vers un **YAML complet** au même schéma que `strategy_defaults.yaml` (obligatoire : `load_strategy_params` valide toutes les clés et la cohérence fenêtres / poids).
- Résolution de chemin : comme `--presets` / `--data` (CWD d’abord, sinon racine `Momentum_Strategy`).
- Le résumé `summary.csv` contient une colonne **`strategy_params`** (chemin résolu) pour audit.

Preset exemple Train 1 : [`configs/sensitivity_presets_train1_alpha.yaml`](../../configs/sensitivity_presets_train1_alpha.yaml) ; fichiers YAML sous [`configs/alpha_train1/`](../../configs/alpha_train1/).

```bash
mstrat sensitivity-batch --presets configs/sensitivity_presets_train1_alpha.yaml --start 2010-01-01 --end 2018-12-31 --output results/institutional/sensitivity_train1_alpha
```

Sous **PowerShell** (Windows), le `\` de fin de ligne est une habitude **bash** : il provoque une erreur de parsing. Utiliser la **commande sur une seule ligne** ci-dessus, ou la continuation avec **backtick** `` ` `` :

```powershell
mstrat sensitivity-batch --presets configs/sensitivity_presets_train1_alpha.yaml `
  --start 2010-01-01 --end 2018-12-31 `
  --output results/institutional/sensitivity_train1_alpha
```

`EventDrivenEngine` accepte aussi `strategy_params_path` en Python pour un run isolé.

**Flux institutionnel** : explorer l’alpha sur la fenêtre *train* ([`configs/research_windows.yaml`](../../configs/research_windows.yaml)), **geler** le fichier YAML retenu (copie datée / commit), puis **validation** et **OOS strict** sans retuner les clés d’alpha sur ces fenêtres.

## Batch auditables

Les chemins `--presets` et `--data` peuvent être **relatifs au répertoire courant** ou, s’ils n’existent pas là, **relatifs à la racine du dépôt Momentum_Strategy** (parent de `src/`). Tu peux donc lancer `mstrat` depuis le dossier parent `Stratégie de trading` avec `--presets configs/sensitivity_presets_train1.yaml`.

Fichier [`configs/sensitivity_presets.yaml`](../../configs/sensitivity_presets.yaml) : une liste de scénarios nommés. Exécution :

```bash
mstrat sensitivity-batch --presets configs/sensitivity_presets.yaml
```

Un seul scénario :

```bash
mstrat sensitivity-batch --presets configs/sensitivity_presets.yaml --only baseline
```

Résumé : `results/sensitivity/summary.csv` (non versionné).

### Mode rapide vs mode audit

| Mode | Comportement |
|------|----------------|
| **Défaut** | `engine.run()` uniquement → métriques agrégées dans `summary.csv` par scénario ; **pas** de `stats_*.csv` ni `rebal_diagnostics_*.csv` dans le sous-dossier du scénario. |
| **`--write-artifacts`** | Après chaque scénario, `save_results()` → `stats_*.csv`, `rebal_diagnostics_*.csv` (si rebalances), exports régimes / perf régime, dashboard 3D ; **plus lent**. Le HTML `strategy_vs_benchmark_*.html` reste **désactivé** dans le batch (`skip_strategy_benchmark_report`) ; pour ce rapport, lancer un `mstrat event-backtest` dédié. |

Exemple Train 1 avec artefacts :

```bash
mstrat sensitivity-batch --presets configs/sensitivity_presets_train1.yaml --start 2010-01-01 --end 2018-12-31 --output results/institutional/sensitivity_train1 --write-artifacts
```

(Même remarque **PowerShell** : une seule ligne, ou lignes suivantes précédées d’un backtick `` ` `` en fin de ligne précédente.)

Attribution forward sur un `rebal_diagnostics_*` produit ainsi : [INSTITUTIONAL_WORKFLOW.md](INSTITUTIONAL_WORKFLOW.md) (étape 4), commande `mstrat book-forward-attribution`.

Règle : ne combiner trop de dimensions en une seule grille sans documenter l’explosion des degrés de liberté ; préférer une dimension dominante par note de recherche.
