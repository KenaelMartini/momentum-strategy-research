# Objectifs du projet Momentum_Strategy

## Mandat

Construire une chaîne reproductible **données → signal momentum → backtest**, avec une documentation et une structure adaptées à un environnement de gestion quantitative (recherche figée, validation hors échantillon).

## Univers et instrument

- **Phase actuelle** : actions US liquides (large / mid caps) listées dans `configs/universe.yaml` ; extension futures possible via la même configuration.
- **Benchmark de référence** : portefeuille **équipondéré** sur le même univers et la même grille de dates que la matrice de prix traitée (comparaisons « apples to apples »).

## Fréquence et style de stratégie

- **Rebalancement** : mensuel (standard académique momentum), sauf évolution documentée dans `configs/strategy_defaults.yaml`.
- **Signal** : combinaison **cross-sectionnel** (relative) et **time-series** (directionnel), paramétrée par des poids CS/TS.

## Métriques prioritaires

- Rendement annualisé et **volatilité annualisée**.
- **Ratio de Sharpe** (taux sans risque explicite dans la config).
- **Drawdown maximum** et profil de drawdown.
- **Turnover** et **coûts** (commission + slippage en basis points).
- Stabilité des résultats sous **stress de coûts** (+20 % par exemple) sur la période de recherche.

## Périmètre temporel (recherche)

- **Train 1** : exploration et calibrage des hypothèses (bornes indicatives : 2015–2019 ; ajustables dans la config stratégie).
- **OOS** : période réservée à la validation d’une variante **déjà choisie** sur le train, sans ré-optimisation ad hoc sur l’OOS.

## Hors périmètre (phase initiale)

- Exécution live, gestion d’ordres réelle, et risque opérationnel complet.
- Optimisation massive multi-paramètres sans journal d’expériences (à introduire plus tard si besoin).
