# Politique données

## Source canonique

- **Primaire** : téléchargement via **Interactive Brokers** (`ib_insync`), avec TWS ou IB Gateway actif selon `configs/ibkr.yaml`.
- Les fichiers **bruts** sont stockés sous `data/raw/` avec la convention :
  - `stock_<TICKER>.csv`
  - `future_<ROOT>.csv`

## Cache et idempotence

- Par défaut, un symbole n’est **pas** re-téléchargé si le fichier cache couvre déjà la fenêtre demandée jusqu’à la date de fin configurée (dernière barre disponible).
- L’option **`--force`** force le re-téléchargement pour les symboles concernés.
- Un délai entre requêtes respecte les **pacing limits** IBKR.

## Traitement

- Chaque série brute est **validée** (colonnes, monotonie des dates, OHLC cohérent, prix positifs) avant inclusion dans la matrice agrégée.
- La matrice **`data/processed/price_matrix.csv`** contient une ligne par date de séance et une colonne par ticker (prix de **clôture**), avec la colonne d’index sauvegardée sous le nom `date` pour clarté et interopérabilité avec des moteurs lisant `index_col=0`.

## Alignement multi-actifs

- Les séries sont alignées sur une **grille commune** ; les valeurs manquantes pour un actif sur une date où d’autres négocient sont gérées par **forward-fill** limité (voir module `matrix`) — comportement à documenter pour toute étude académique stricte (risque de biais si mal utilisé).

## Manifeste de build

- Chaque construction de `price_matrix.csv` produit **`data/processed/price_matrix_manifest.yaml`** listant :
  - horodatage UTC du build ;
  - chemins des fichiers sources ;
  - tickers inclus ;
  - paramètres d’alignement (ex. `calendar_mode`).

## Conservation

- `data/raw/` et `data/processed/` sont en **`.gitignore`** : les jeux de données ne versionnent pas dans Git ; seules les configs et le code sont source de vérité pour régénérer les données.

## Corporate actions et type de série

- Les barres téléchargées via IBKR suivent les **paramètres de contrat et d’historique** définis côté TWS / API (splits, dividendes : selon le type de barre « adjusted » ou non côté fournisseur).
- **Hypothèse de recherche actuelle** : prix de **clôture** agrégés dans `price_matrix.csv` ; toute étude académique ou diligence externe doit **qualifier explicitement** si les séries sont totalement ajustées, partiellement, ou brutes, et l’impact sur un signal **momentum long/short** (sauts artificiels, biais de look-ahead si ajustement futur).
- En cas de doute, régénérer la matrice après vérification des specs IBKR pour chaque symbole et consigner la conclusion dans le manifeste ou la note de recherche du run.

## Univers, survivorship et point-in-time

- L’univers est défini dans `configs/universe.yaml` (liste de tickers **actuelle** pour la construction de la matrice).
- **Limite** : sauf pipeline dédié, l’univers n’est en général **pas** reconstitué point-in-time (entrées/sorties historiques, IPO, radiations). Le backtest peut donc souffrir d’un **biais de survivorship** si l’univers d’aujourd’hui est appliqué rétroactivement sur toute la fenêtre.
- Toute présentation des résultats à des tiers doit mentionner cette hypothèse ou s’appuyer sur un univers reconstruit avec dates d’apparition/disparition des titres.

## Lien avec l’archivage des runs

Pour chaque backtest « officiel », archiver le **manifeste** (`price_matrix_manifest.yaml`) avec les configs via `mstrat archive-run` — voir [research/REFERENCE_RUN.md](research/REFERENCE_RUN.md).
