# Gel de la spec (institutionnel)

## Quand geler

Après sélection d’une variante sur **Train 1 uniquement**, selon [CRITERES_SELECTION.md](CRITERES_SELECTION.md), **avant** tout run de validation 2020–2022.

## Check-list

- [ ] Dernier run Train 1 baseline archivé (`mstrat research-pipeline train1-archive` ou `mstrat archive-run --event-driven-dir results/institutional/train1_baseline --copy-latest-results`).
- [ ] `configs/strategy_defaults.yaml`, `configs/risk_event_driven.yaml`, `configs/universe.yaml` correspondent exactement à la variante choisie.
- [ ] Aucun paramètre CLI « orphelin » (ex. `--rebalance-threshold`) non reflété dans la doc ou un fichier de spec — si utilisé en prod, le consigner dans ce document ou dans `_config_body.txt` / YAML.

## Versionnement

1. **Git** : commit avec message explicite, ex. `research: freeze spec candidate train1 2015-2019 v1`.
2. **Tag optionnel** : `git tag spec-train1-v1` après validation du commit.
3. **Copie** : conserver un dossier `results/archive/run_*` contenant `configs_snapshot/` et `run_metadata.yaml`.

## Après le gel

- **Interdit** : modifier la spec pour améliorer les chiffres de **validation** ou **OOS strict**.
- **Autorisé** : si l’OOS échoue, enregistrer la conclusion dans la note et **repartir** d’une nouvelle hypothèse sur **Train 1 seulement** (nouvelle campagne, idéalement nouvelle fenêtre OOS non encore « consommée » si vous redécoupez le temps).
