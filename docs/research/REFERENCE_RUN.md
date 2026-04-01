# Archivage d’un run de référence

Objectif : satisfaire la traçabilité décrite dans [contraintes institutionnelles](../contraintes_institutionnelles.md) (configs versionnées + lien au manifeste données).

## Commande

```bash
cd Momentum_Strategy
mstrat archive-run --copy-latest-results
```

Sans `--dest`, un dossier horodaté est créé sous `results/archive/run_<timestamp_utc>/` (non versionné car `results/` est ignoré par Git). Copiez ce dossier vers votre stockage documentaire interne si besoin.

Contenu typique :

- `configs_snapshot/` — copies de `strategy_defaults.yaml`, `risk_event_driven.yaml`, `universe.yaml`, `ibkr.yaml`, `research_windows.yaml` (si présents)
- `price_matrix_manifest.yaml` — copie du manifeste de build de la matrice (si `data/processed/` est à jour)
- `run_metadata.yaml` — date UTC, version Python, commit git (si dépôt git), SHA256 des fichiers copiés, exemples de commandes CLI
- `event_driven_artifacts/` — si `--copy-latest-results` : dernier `stats_*.csv`, `rebal_diagnostics_*.csv`, `regime_performance_effective_*.csv`, `strategy_vs_benchmark_*.html` lorsque disponibles

## Manuel

Pour un run « officiel », notez aussi dans votre outil de suivi :

- Commande exacte (`--start`, `--end`, `--data`, `--output`, `--stress-cost-mult`, etc.)
- Identité du jeu de données (hash du manifeste dans `run_metadata.yaml`)
