# Contraintes institutionnelles

## Intégrité de la recherche

1. **Pas de look-ahead** : toute décision à la date \(T\) (signal, poids, risque) n’utilise que l’information disponible à \(T\) (prix, volumes, états déjà calculés à \(T\) ou avant). Les moteurs **jour par jour** doivent respecter cette contrainte par construction.
2. **Séparation train / validation / OOS** : les paramètres de stratégie ne sont ajustés que sur les périodes désignées pour la recherche ; l’OOS sert à confirmer une **version figée** de la spec (fichiers de config versionnés).
3. **Traçabilité des runs** : chaque run de pipeline données ou de backtest doit pouvoir être relié à une **version de config** (fichiers sous `configs/`) et, pour la matrice de prix, au **manifeste** généré dans `data/processed/`.

## Modélisation des coûts

- **Commission** et **slippage** en basis points, définis dans `configs/strategy_defaults.yaml`.
- Toute amélioration de performance nette doit être robuste à une **hausse prudente** des coûts (stress), documentée dans les objectifs.

## Contraintes de risque (socle)

- Taille max par ligne, levier max, volatilité cible : paramètres dans la config stratégie ; le **moteur minimal** de backtest peut n’en appliquer qu’un sous-ensemble au début, puis alignement progressif avec le moteur event-driven complet (projet `Fist` ou migration future).
- Les mécanismes avancés (circuit breaker drawdown, overlay de régime, etc.) restent **hors scope** du package initial et seront branchés lors de l’intégration backtest institutionnelle.

## Données et conformité

- La source canonique des prix est l’**API Interactive Brokers** (TWS / Gateway) pour ce dépôt, sauf remplacement explicite par un autre fournisseur documenté dans `docs/politique_donnees.md`.
- Le **scraping web** de prix n’est pas la voie par défaut (qualité, ToS, audit). Toute source alternative doit être approuvée et documentée.

## Corporate actions

- Les séries IBKR utilisées pour le backtest doivent être qualifiées (**ajustées ou brutes**) ; l’hypothèse retenue est indiquée dans la politique données. Les splits non ajustés peuvent produire des sauts de prix aberrants.
