# Moniteur d'assurance d'exécution embarqué — prototype et campagne de falsification

> Traduction française du [README.md](../README.md) anglais, qui fait foi.
> Dernière synchronisation : v1.0.1 (7 septembre 2026).

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22552147.svg)](https://doi.org/10.5281/zenodo.22552147)
[![tests](https://github.com/Stab123/runtime-assurance-monitor/actions/workflows/tests.yml/badge.svg)](https://github.com/Stab123/runtime-assurance-monitor/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](../LICENSE)

Prototype exécutable d'un moniteur d'assurance pour une couche de décision embarquée autonome, avec un artefact de trace de décision auditable, et une campagne Monte Carlo qui **falsifie** l'hypothèse différenciante du projet.

**Résultat principal : négatif.** Le durcissement sur l'incertitude d'estimation (exigence RA-FUN-003) n'apporte rien dans le scénario testé. L'enveloppe de sécurité seule atteint zéro violation sur 300 tirages ; chaque variante durcie coûte de la disponibilité sans rien prévenir de plus.

---

## Note de correction — septembre 2026

**Statut : rejeu terminé.** Une revue de code a trouvé deux défauts de code (un décalage temporel d'un pas dans la persistance du repli, et un bogue latent de projection jamais atteint par les campagnes) plus une table de documentation obsolète. Toutes les campagnes (P2.2, P2.3, pilote P3, P3.1) ont été rejouées sur GitHub Actions avec des configurations **strictement inchangées** : les comptages de violations sont inchangés, repli et livraison ont bougé d'au plus 0,04 point, le mur s'est déplacé d'exactement un point de grille du pilote comme le fix le prédisait, et chaque chiffre ci-dessous est la version post-correction. **Toutes les conclusions qualitatives sont inchangées.** Protocole complet, chiffres et conséquences : [CHANGELOG.md](../CHANGELOG.md) (entrée v1.0-p3.1).

---

## Contexte

L'*assurance d'exécution* (*runtime assurance*) enrobe une couche de décision qui ne peut pas être vérifiée statiquement — planificateur, politique apprise, contrôleur adaptatif — derrière un moniteur vérifié qui autorise, modifie ou bloque chaque action. Le motif est établi : architecture Simplex (Seto et al. 1998), ASTM F3269, et côté contrôle le *predictive safety filter* de Wabersich & Zeilinger. Côté vérification à l'exécution embarquée, R2U2 a volé sur un CubeSat (CySat-I), sur l'ISS (Robonaut2) et sur une mission JAXA.

Ce dépôt ne réinvente aucun de ces éléments. Il explore deux points que la littérature ne traite pas :

1. **un artefact de trace de décision auditable** — reconstruire après la mission ce que le moniteur savait, ce qu'il a refusé, et quelle contrainte a fait basculer le verdict, sans accès à l'état interne de la couche de décision ;
2. **l'incertitude d'estimation comme déclencheur de premier ordre** du repli, indépendamment de la valeur nominale.

C'est le point 2 que la campagne falsifie.

---

## Résultats — campagne P2.3

Quatre bras, mêmes tirages (*common random numbers*), 300 runs par point, 2700 cycles de 5 s par run.

| Bras | Configuration | Violations | Runs avec violation | Taux de repli | Livraison mission |
|---|---|---|---|---|---|
| **A** | sans moniteur | 2,53 % | 68 / 300 | 0 % | 100 % |
| **B** | enveloppe seule | **0 %** | **0 / 300** | **6,57 %** | **90,81 %** |
| **D** | + évaluation pessimiste 3σ | 0 % | 0 / 300 | 9,43 % | 85,83 % |
| **C** | + seuil d'incertitude (σ = 0,03) | 0 % | 0 / 300 | 18,11 % | 81,52 % |

Le taux de violation est mesuré sur l'**état réel de la plante**, contre les seuils **bruts** — jamais sur l'état estimé, jamais contre le seuil de commutation.

Balayage du seuil d'incertitude (bras C) :

| Seuil σ | 0,005 | 0,008 | 0,010 | 0,015 | 0,020 | 0,030 | 0,050 | 0,080 |
|---|---|---|---|---|---|---|---|---|
| Repli | 94,89 % | 59,10 % | 40,20 % | 24,98 % | 22,63 % | 18,11 % | 9,60 % | 9,43 % |
| Livraison | 4,54 % | 31,91 % | 48,00 % | 67,34 % | 74,13 % | 81,52 % | 85,82 % | 85,83 % |
| Violations | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

À σ = 0,08, C est identique à D run par run : le seuil ne se déclenche jamais. Le coût est monotone, le bénéfice nul.

**Conclusion.** Le critère de succès pré-enregistré exigeait un point de grille avec un taux de violation strictement inférieur au bras témoin B. B est à zéro ; rien ne peut faire mieux. Sur les deux métriques de coût, chaque point est pire que B. RA-FUN-003 est falsifiée.

**Résultat secondaire.** Le bras D montre que l'évaluation pessimiste 3σ est aussi du poids mort dans ce scénario : +2,9 points de repli et −5,0 points de livraison pour zéro violation évitée. La meilleure configuration du tableau est l'enveloppe seule.

Là où le durcissement pourrait payer, la validation à la compilation refuse le jeu de contraintes. Là où le jeu est acceptable, l'enveloppe suffit et le durcissement ne peut que coûter.

---

## P3 — la condition du §7 et le mur de compilation

Le §7 rendait le durcissement utile seulement dans un régime où l'autorité du repli est marginale relativement au temps avant violation (r = τ_armement / τ_violation → 1 ; avec le τ_violation formel = 205,8 s de la note de correction, P2 à 120 s se situe à r = 0,58). P3 pousse ce levier unique — le délai d'armement — tout le reste étant figé (graines, bornes de plante, marges, seuils, grille σ, cycles, et validation à la compilation sur le modèle nominal 10 Ah).

Le pilote (bras B seul, N = 30, exécuté **avant** le gel du critère — `ram_p3/resultats_pilote_p3.json`) a trouvé deux choses. D'abord, B reste à **zéro violation** sur toute la bande compilable — y compris à 195 s, que le code pré-correction refusait encore (le décalage d'un pas lui faisait appliquer 200 s ; le fix a déplacé le mur d'exactement un point de grille, comme prévu). Ensuite, au-delà de τ_armement = 195 s (r physique ≈ 0,95), la validation RA-FUN-005 **rejette le jeu de contraintes à la compilation** : depuis la frontière de garde, l'action la plus défavorable persistée pendant l'armement franchirait le seuil brut (compilable à 195 s avec une marge résiduelle de +0,0002, refusé dès 196 s ; le point de grille suivant du pilote, 240 s, est refusé). Le régime où le durcissement pourrait payer n'est pas un régime difficile à survivre — il est **non déployable par construction**.

Le mur est indexé sur le domaine d'action (u_max = 3 A, déclaré dans `ram_p0/demo_eps.py`, vérifié sur les deux bornes à la compilation) : le résultat est énoncé *pour ce jeu de bornes*. Ici u_payload = u_max — le pire cas vérifié à la compilation est exactement la charge réellement commandée dans la fenêtre payload.

P3.1 documente le mur avec puissance statistique : τ_armement ∈ {140 ; 170 ; 190} s — r physique ∈ {0,68 ; 0,83 ; 0,92}, le dernier au ras du mur —, N = 300, quatre bras, grille σ inchangée. (Les fichiers de configuration figés conservent les labels r d'origine, définis contre un τ_violation = 400 s rétro-calculé plutôt que dérivé — voir la note de correction ; les résultats sont énoncés ici en secondes.) Configuration figée et commitée avant exécution (`ram_p3/config_p3_1.json`, critère à deux clauses inclus), exécutée par `.github/workflows/p3.yml`.

**Résultat P3.1** (N = 300 par point, CRN 300/300 — `ram_p3/resultats_p3_1.json`) : à chaque point de la bande compilable, B reste à **0/300** runs avec violation (Wilson [0 ; 1,3 %]) — y compris à 190 s (r = 0,92), le dernier point déployable. Le mur n'est pas un artefact du N = 30. Le critère de puissance figé tranche : P3 est **non concluant pour H4** — il n'existe pas de régime déployable où B échoue, donc aucun où le durcissement pourrait payer. Les coûts montent avec r pour tous les bras monitorés (repli B : 10,18 % → 15,60 % → 18,77 % ; livraison : 89,05 % → 86,47 % → 84,91 %) sans que l'ordre B < D < C se renverse jamais. Non-régression : le bras A reproduit P2.3 bit pour bit à chaque point (6300/6300 champs identiques).

### Portée du résultat

L'énoncé exact est : **dans un régime où l'enveloppe de sécurité suffit déjà, le durcissement sur l'incertitude n'est pas justifié.** Ce n'est pas un énoncé général.

Le bras témoin est au plafond — zéro violation. Dans une expérience où le témoin n'échoue à rien, un mécanisme additionnel ne peut que coûter. Un scénario où la marge de garde ne couvre plus l'erreur d'estimation pourrait donner un résultat différent ; construire un tel scénario *après* avoir vu ces chiffres serait de la fabrication de résultats, et n'a donc pas été fait.

---

## Limitations déclarées

**Les seuils de falsification n'ont pas été arbitrés.** Les configurations proposent un plafond de violation, un plafond de repli et un plancher de livraison, marqués comme exigeant un arbitrage opérateur. Cet arbitrage n'a pas eu lieu. La conclusion sur RA-FUN-003 repose sur la comparaison avec le bras B et ne dépend d'aucun plafond absolu. Pour information, avec 300 runs le bras B passe trois des quatre seuils proposés et manque le quatrième de 0,05 point (livraison 89,95 % à la borne basse contre un plancher de 90 %). La question reste ouverte et a besoin d'un opérateur satellite.

**Le prototype n'est pas du code de vol.** Python, allocation dynamique : les exigences de mémoire statiquement bornée et de temps d'exécution pire cas ne peuvent pas être démontrées ici. L'action est scalaire et exploite une hypothèse de monotonie propre au modèle testé ; le cas vectoriel requiert la formulation quadratique complète. L'incertitude est supposée constante sur l'horizon de prédiction.

**Un seul cas d'usage.** La généricité du moniteur — couche de décision boîte noire, jeu de contraintes versionné — est une propriété de conception, pas une propriété démontrée.

---

## Contenu

```
ram_p0/
  contraintes.py       types de jeux de contraintes (versionnés, seuils
                       d'incertitude par contrainte)
  filtre.py            filtre de sécurité prédictif, spécialisation scalaire
                       de W&Z
  moniteur.py          verdicts, verrouillage du repli, compilation des jeux,
                       signal de vie
  trace.py             enregistreur : formats 16/48/160 octets, tampon
                       circulaire figeable, CRC, décodeur
  demo_eps.py          scénario EPS façon CySat-I, injection de fautes
  test_moniteur.py     tests, chacun rattaché à une exigence
ram_p2/
  chemins.py           résolution des chemins du dépôt
  campagne_p2.py       campagne Monte Carlo, quatre bras (chemins relatifs)
  executer_p2_3.py     exécution parallèle par run (chemins relatifs)
  config_p2_1.json     configuration P2.1 figée     resultats_p2_1.json
  config_p2_2.json     configuration P2.2 figée     resultats_p2_2.json
  config_p2_3.json     configuration P2.3 figée     resultats_p2_3.json
ram_p3/
  pilote_p3.py         pilote puissance, bras B seul, avant gel
  executer_p3_1.py     exécution parallèle P3.1 et fusion des partiels
  config_pilote_p3.json, config_p3_1.json (figés avant exécution)
  resultats_pilote_p3.json, partiel_r*.json, resultats_p3_1.json
empreintes/            octets exacts ayant produit les résultats publiés —
                       pour vérification, jamais exécution
                       (voir empreintes/README.md)
verifier_empreintes.py compare module par module les empreintes SHA-256
                       embarquées dans les résultats contre les octets
                       d'empreintes/
.github/workflows/tests.yml
                       à chaque push : pytest ram_p0/test_moniteur.py,
                       puis verifier_empreintes.py
.github/workflows/p3.yml
                       déclenchement manuel : exécute P3.1, un job par
                       point r
.github/workflows/rejeu.yml
                       déclenchement manuel : les rejeux de septembre 2026
                       (P2.2, P2.3, pilote P3), configurations inchangées
figures/
  faire_figures.py     régénère les Figures 2 et 3 du papier depuis les
                       fichiers de résultats publiés
docs/
  exigences.md         traçabilité des exigences (RA-* → mécanisme → test)
  README_fr.md         ce fichier
paper/                 prépublication v2 (FR/EN), remplacée — v3 en
                       préparation
CITATION.cff           métadonnées de citation (DOI conceptuel Zenodo)
CHANGELOG.md           protocole de correction et historique des releases
```

Les trois campagnes sont conservées. P2.1 avait un défaut de plan d'expérience — le bras C variait deux choses à la fois — corrigé dans P2.2 en ajoutant le bras D et en étendant la grille. P2.3 fait passer N de 32 à 300 sans autre changement. Les points partagés se reproduisent à l'identique, vérifié en non-régression.

---

## Reproduction

```bash
python3 -m pytest ram_p0/test_moniteur.py -q
python3 ram_p0/demo_eps.py
python3 verifier_empreintes.py
python3 ram_p2/executer_p2_3.py ram_p2/config_p2_2.json resultats_rejeu.json 4
```

Python 3.10+, bibliothèque standard seule.

**Environnement d'exécution des campagnes publiées.** P2.1, P2.2 et P2.3 ont tourné à l'origine dans le bac à sable Linux d'un agent logiciel (CPython 3.12.12, x86-64). Les chemins absolus `/mnt/agents/output/...` visibles dans les octets archivés d'origine (`empreintes/campagne_p2.py`, `empreintes/executer_p2_3.py`) appartiennent à cet environnement ; les copies exécutables sous `ram_p0/` et `ram_p2/` résolvent leurs chemins relativement au dépôt (`ram_p2/chemins.py`) et se rejouent telles quelles après un clone. Les rejeux de septembre 2026 (P2.2, P2.3, P3) ont tourné sur des runners GitHub Actions avec ces copies à chemins relatifs : ils reproduisent les résultats d'origine run par run (violations identiques, repli/livraison à 0,04 point près — le fix du décalage raccourcit la persistance d'exactement un pas), et leurs `empreintes_code` sont archivées sous `empreintes/campagne_p2_rejeu.py` et `empreintes/executer_p2_3_rejeu.py`. Un rejeu reproduit les résultats run par run ; ses `empreintes_code` sont identiques pour les quatre modules du moniteur et différentes pour les deux pilotes, dont seuls les chemins ont été relativisés — la vérification d'empreintes pointe donc vers `empreintes/`.

Les graines sont dans les fichiers de configuration, les empreintes SHA-256 des modules dans les fichiers de résultats. Toute modification de configuration crée une nouvelle version du fichier, jamais une édition.

---

## Choix méthodologiques

**σ n'est pas circulaire.** Il est calculé depuis les résidus de mesure — innovations contre le modèle nominal, celui-là même que le moniteur utilise — et jamais depuis les paramètres de la plante. Un σ dérivé du modèle de prédiction n'aurait rien mesuré.

**L'écart plante/modèle est réel et défavorable au moniteur.** La plante tire ses paramètres uniformément par run ; le moniteur garde le modèle nominal, qui suppose une capacité batterie supérieure à toute valeur tirée. Malgré cela, l'enveloppe seule ne manque rien.

**Le bras témoin est décisif.** Sans B, la contribution de RA-FUN-003 ne serait pas attribuable. Sans D, son coût resterait confondu avec celui de l'évaluation pessimiste.

**Provenance du code.** Le décompte des défauts utilisé partout dans ce dépôt (README, CHANGELOG, §6 du papier) est : **quatre défauts d'interaction + deux défauts de code + un défaut de documentation** — sept au total. Les quatre défauts d'interaction ont été trouvés par revue adversariale alors que la suite de tests était entièrement verte, et ont tous été corrigés **avant** la première campagne : les empreintes des modules du moniteur sont identiques dans les fichiers de résultats P2.1, P2.2 et P2.3 ; seul le pilote de campagne diffère. Aucun résultat rapporté n'a été produit par ce code défectueux. Les trois défauts restants — deux dans le code, une table de documentation obsolète — ont été trouvés plus tard (note de correction de septembre 2026 en tête) : les résultats publiés avaient été produits par le code affecté, donc toutes les campagnes ont été rejouées à configurations inchangées — chaque conclusion qualitative a tenu. Le pilote P2.1 (trois bras) a été édité sur place pour devenir la version à quatre bras, et l'environnement d'exécution n'en a gardé aucune copie : son empreinte reste vérifiable dans `resultats_p2_1.json`, et rejouer la configuration P2.1 avec la version à quatre bras reproduit les bras A, B et C run par run — justification complète dans `empreintes/README.md`.

**Pré-enregistrement et archivage.** Chaque configuration de campagne a été commitée avant son exécution — l'historique git porte l'ordre config-avant-résultats pour P2.1, P2.2, P2.3 et P3.1. Cet historique est désormais horodaté dans deux archives indépendantes et non réécrivables : Zenodo (DOI conceptuel [10.5281/zenodo.22552147](https://doi.org/10.5281/zenodo.22552147), un DOI de version par release) et [Software Heritage](https://archive.softwareheritage.org/), qui préserve le graphe git complet. Les tags de release sont annotés mais non signés GPG ; l'horodatage et l'intégrité sont couverts par ces deux archives.

---

## Références

- K. P. Wabersich, M. N. Zeilinger, *A predictive safety filter for learning-based control of constrained nonlinear dynamical systems*, Automatica 129:109597, 2021 — arXiv:1812.05506
- A. Aurandt, P. H. Jones, K. Y. Rozier, *Runtime Verification Triggers Real-time, Autonomous Fault Recovery on the CySat-I*, NASA Formal Methods 2022
- D. Seto, B. Krogh, L. Sha, A. Chutinan, *The Simplex architecture for safe on-line control system upgrades*, ACC 1998
- ECSS-E-ST-70-11C Rev.1 (15 octobre 2025), *Space segment operability*
- ECSS-E-ST-70-41C, *Telemetry and telecommand packet utilization*

---

## Licence

MIT.
