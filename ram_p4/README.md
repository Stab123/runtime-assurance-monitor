# ram_p4 — P4 « Where the envelope stops sufficing »

Périmètre **nouveau**, strictement séparé de l'historique. La baseline v1.4.1
(P2, P2.3, P3, P3.1, leurs configurations, seeds, données, statistiques,
résultats, scripts et conclusions) reste **intégralement gelée** : ce
répertoire ajoute des fichiers, il n'en modifie aucun.

## Question

Dans un domaine physique D défini indépendamment des résultats du projet
(sources externes, Phase 2), existe-t-il une frontière reproductible séparant
les conditions où l'enveloppe B conserve zéro violation observée au niveau run
de celles où des violations apparaissent — et si oui, est-elle expliquée par
l'épuisement de la marge SoC sous l'effet d'une erreur d'estimation
persistante ?

## Contenu

| Fichier | Rôle |
|---|---|
| `PRE_REGISTRATION_P4A.md` | protocole confirmatoire complet, figé avant données |
| `analysis_plan_p4a.md` | justifications et dimensionnement (Wilson, puissances) |
| `config_p4a.json` | configuration + 500 points de design en clair |
| `schema_resultats_p4a.json` | schéma des données brutes par run |
| `graines_p4.py` | dérivation déterministe des seeds (SHA-256, labels) |
| `generer_design.py` | régénération bit à bit des points de design |
| `campagne_p4a.py` | code de campagne (bras B seul, injection de biais) |
| `analyse_p4a.py` | script d'analyse unique (verdicts automatiques) |

## Statut

**PRÉ-ENREGISTRÉ — aucun résultat confirmatoire n'existe.** L'exécution de
`campagne_p4a.py` en mode `principal`/`reseed`/`dtctrl` est subordonnée à une
autorisation explicite postérieure au commit de gel. Le mode `pilote` (seeds
PILOT, quarantaine) ne sert qu'aux vérifications de plomberie.

## Système de référence

Classe 6U–12U LEO, bus ~7.4–8.4 V, batterie Li-ion 18650 2S2P–2S4P, mesure de
courant par shunt + moniteur de classe INA219, estimation SoC par coulomb
counting + recalage (Phase 2). Toute conclusion P4 est limitée à cette classe
et à la mesure expérimentale μ_D — jamais à une flotte réelle de satellites.
