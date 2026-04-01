# Critères de sélection (Train 1) — à figer avant les sweeps

Documenter **avant** toute grille de sensibilité les règles de rejet / acceptation d’une variante. Adapter les seuils au mandat ; les valeurs ci-dessous sont un **exemple** de cadre mesurable.

## Règles proposées (exemple)

| ID | Critère | Seuil | Mesure |
|----|---------|-------|--------|
| C1 | Sharpe (coûts nominaux ×1) sur Train 1 | > 0 | `final_metrics.sharpe` |
| C2 | Sharpe sous stress ×1.5 sur Train 1 | > 0 | `mstrat research-pipeline train1-cost-stress` ou colonne `summary.csv` |
| C3 | Sharpe sous stress ×2 sur Train 1 | > −0.05 (ou rejet si < 0) | idem |
| C4 | CAGR sous ×2 sur Train 1 | > 0 | idem |
| C5 | Max drawdown Train 1 (×1) | < −25 % (exemple) | `max_dd` |
| C6 | Turnover annualisé Train 1 | < baseline × 0,85 **ou** justification écrite si plus haut | `avg_turnover` |
| C7 | Trade-off | Ne pas retenir une variante qui **n’améliore** que le CAGR si le DD empire **et** le Sharpe ×1.5 baisse | Revue manuelle |

## Utilisation

1. Copier ce fichier ou enregistrer les seuils retenus dans la note de recherche (section critères).
2. Après chaque sweep Train 1, cocher pass/fail par ligne dans un tableau annexe.
3. La **spec candidate** doit satisfaire tous les critères **actifs** (marquer N/A si un critère est désactivé volontairement).

## Révision

Toute modification des critères **après** avoir vu la validation/OOS doit être documentée comme **changement de protocole** (nouvelle campagne, nouvelles fenêtres si nécessaire).
