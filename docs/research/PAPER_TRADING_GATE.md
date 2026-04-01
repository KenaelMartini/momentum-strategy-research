# Gate paper trading (check-list)

Ne passer en paper trading **que si** tous les points pertinents sont cochés pour votre organisation.

## Recherche

- [ ] Spec **gelée** et documentée ([SPEC_GEL.md](SPEC_GEL.md)).
- [ ] Runs **Train 1**, **validation 2020–2022**, **OOS strict 2023–2024** effectués avec cette spec (`mstrat research-pipeline` ou équivalent).
- [ ] Note de recherche remplie ([NOTE_RECHERCHE_EVENT_DRIVEN.md](NOTE_RECHERCHE_EVENT_DRIVEN.md)) : métriques, régimes, stress coûts, limites données/univers.
- [ ] Critères de sélection Train 1 **passés** ou écarts **explicitement acceptés** ([CRITERES_SELECTION.md](CRITERES_SELECTION.md)).

## Risque et coûts

- [ ] Grille stress coûts (×1.5, ×2) **lue** ; exposition au turnover comprise.
- [ ] Max drawdown et comportement par **régime** (hausse / risk-off) jugés acceptables pour le mandat.

## Opérations

- [ ] Plan de **réconciliation** : fréquence, comparaison positions/P&amp;L moteur vs courtier, responsable.
- [ ] Environnement paper (compte, taille notionnelle, contrats) défini.

## Décision

| Décision | Date | Signé / référence |
|----------|------|-------------------|
| Paper trading GO / NO-GO | | |
| Conditions particulières | | |

Si **NO-GO** : documenter la raison (perf, risque, données, priorité business) dans la note de recherche.
