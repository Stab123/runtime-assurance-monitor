# Moniteur d'assurance runtime embarqué — prototype et campagne de falsification

Prototype exécutable d'un moniteur d'assurance pour couche de décision autonome embarquée, avec artefact de trace de décision auditable, et campagne Monte Carlo qui **infirme** l'hypothèse différenciante du projet.

**Résultat principal : négatif.** Le durcissement sur incertitude d'estimation (exigence RA-FUN-003) n'apporte rien dans le scénario testé. L'enveloppe de sécurité seule atteint zéro violation sur 300 tirages ; toute variante de durcissement coûte en disponibilité sans rien prévenir de plus.

---

## Contexte

Le *runtime assurance* encapsule une couche de décision non vérifiable statiquement — planificateur, politique apprise, contrôleur adaptatif — derrière un moniteur vérifié qui autorise, modifie ou bloque chaque action. Le motif est établi : architecture Simplex (Seto et al. 1998), ASTM F3269, et côté contrôle le *predictive safety filter* de Wabersich & Zeilinger. Côté vérification runtime embarquée, R2U2 a volé sur CubeSat (CySat-I), sur l'ISS (Robonaut2) et sur une mission JAXA.

Ce dépôt n'invente aucun de ces éléments. Il explore deux points que la littérature ne traite pas :

1. **un artefact de trace de décision auditable** — reconstituer après mission ce que le moniteur savait, ce qu'il a refusé et quelle contrainte a fait basculer le verdict, sans accès à l'état interne de la couche de décision ;
2. **l'incertitude d'estimation comme déclencheur de premier ordre** du repli, indépendamment de la valeur nominale.

Le point 2 est celui que la campagne infirme.

---

## Résultats — campagne P2.3

Quatre bras, mêmes tirages (*common random numbers*), 300 runs par point, 2700 cycles de 5 s par run.

| Bras | Configuration | Violations | Runs avec violation | Taux de repli | Livraison mission |
|---|---|---|---|---|---|
| **A** | sans moniteur | 2,53 % | 68 / 300 | 0 % | 100 % |
| **B** | enveloppe seule | **0 %** | **0 / 300** | **6,58 %** | **90,80 %** |
| **D** | + évaluation pessimiste 3σ | 0 % | 0 / 300 | 9,42 % | 85,82 % |
| **C** | + seuil d'incertitude (σ = 0,03) | 0 % | 0 / 300 | 18,11 % | 81,52 % |

Le taux de violation est mesuré sur l'état **réel de la plante**, contre les seuils **bruts** — jamais sur l'état estimé, jamais contre le seuil de commutation.

Balayage du seuil d'incertitude (bras C) :

| σ seuil | 0,005 | 0,008 | 0,010 | 0,015 | 0,020 | 0,030 | 0,050 | 0,080 |
|---|---|---|---|---|---|---|---|---|
| Repli | 94,4 % | 55,1 % | 37,1 % | 24,1 % | 22,2 % | 18,1 % | 9,59 % | 9,42 % |
| Livraison | 5,0 % | 37,7 % | 51,8 % | 68,0 % | 73,6 % | 81,5 % | 85,8 % | 85,8 % |
| Violations | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

À σ = 0,08, C est identique à D run par run : le seuil ne se déclenche plus. Le coût est monotone, le bénéfice nul.

**Conclusion.** Le critère de succès pré-enregistré exigeait un point de grille avec un taux de violation strictement inférieur au bras de contrôle B. B vaut zéro ; rien ne peut faire mieux. Sur les deux métriques de coût, chaque point est pire que B. RA-FUN-003 est infirmée.

**Résultat secondaire.** Le bras D montre que l'évaluation pessimiste à 3σ est elle aussi du poids mort dans ce scénario : +2,8 points de repli et −5,0 points de livraison pour zéro violation évitée. La meilleure configuration du tableau est l'enveloppe seule.

Là où le durcissement pourrait payer, la validation à la compilation refuse le jeu de contraintes. Là où le jeu est acceptable, l'enveloppe suffit et le durcissement ne peut que coûter.

---

## P3 — la condition de §7 et le mur de compilation

§7 conditionnait l'utilité du durcissement à un régime où l'autorité du repli est marginale devant le temps-avant-violation (r = τ_armement / τ_violation → 1 ; P2 est à r ≈ 0,3). P3 pousse ce seul levier — le délai d'armement — tout le reste figé (graines, bornes de plante, marges, seuils, grille σ, cycles, et la validation à la compilation sur le modèle nominal 10 Ah).

Le pilote (bras B seul, N = 30, exécuté **avant** figeage du critère — `ram_p3/resultats_pilote_p3.json`) a trouvé deux choses. D'une part B reste à **zéro violation** sur toute la bande compilable. D'autre part, au-delà de τ_armement = 195 s (r ≈ 0,49), la validation RA-FUN-005 **refuse le jeu à la compilation** : depuis la frontière de garde, l'action la plus défavorable persistée pendant l'armement franchirait le seuil brut. Le régime où le durcissement pourrait payer n'est pas un régime difficile à survivre — il est **non déployable par construction**.

Le mur est indexé sur le domaine d'action (u_max = 3 A, déclaré dans `ram_p0/demo_eps.py`, vérifié des deux côtés à la compilation) : le résultat s'énonce *pour ce jeu de bornes*. Ici u_payload = u_max — le pire cas vérifié à la compilation est exactement la charge réelle commandée en fenêtre payload.

P3.1 documente le mur avec puissance statistique : r ∈ {0,35 ; 0,425 ; 0,475} — le dernier collé au mur —, N = 300, quatre bras, grille σ inchangée. Configuration figée et committée avant exécution (`ram_p3/config_p3_1.json`, critère en deux clauses inclus), exécution par `.github/workflows/p3.yml`.

**Résultat P3.1** (N = 300 par point, CRN 300/300 — `ram_p3/resultats_p3_1.json`) : à chaque point de la bande compilable, B reste à **0/300** runs avec violation (Wilson [0 ; 1,3 %]) — y compris à r = 0,475, le dernier point déployable. Le mur n'est pas un artefact de N = 30. Le critère de puissance figé tranche : P3 est **non concluante pour H4** — il n'existe aucun régime déployable où B rate, donc aucun où le durcissement pourrait payer. Les coûts montent avec r pour tous les bras monitorés (repli de B : 10,2 % → 15,6 % → 18,8 % ; livraison : 89,0 % → 84,9 %) sans que l'ordre B &lt; D &lt; C ne s'inverse jamais. Non-régression : le bras A reproduit P2.3 bit à bit à chaque point (6300/6300 champs identiques).

### Portée du résultat

L'énoncé exact est : **dans un régime où l'enveloppe de sécurité suffit déjà, le durcissement sur incertitude ne se justifie pas.** Ce n'est pas un énoncé général.

Le bras de contrôle est au plafond — zéro violation. Dans une expérience où le contrôle ne rate rien, un mécanisme supplémentaire ne peut que coûter. Un scénario où la marge de garde ne couvrirait plus l'erreur d'estimation donnerait peut-être un autre résultat ; construire un tel scénario *après* avoir vu ces chiffres serait de la fabrication de résultat, et n'a donc pas été fait.

---

## Limites déclarées

**Les seuils de falsification n'ont pas été arbitrés.** Les configurations proposent un plafond de violation, un plafond de repli et un plancher de livraison, marqués comme relevant d'un arbitrage opérateur. Cet arbitrage n'a pas eu lieu. La conclusion sur RA-FUN-003 repose sur la comparaison au bras B et ne dépend d'aucun plafond absolu. À titre indicatif, avec 300 runs le bras B franchit trois des quatre seuils proposés et rate le quatrième de 0,06 point (livraison 89,94 % en borne inférieure contre un plancher à 90 %). La question reste ouverte et demande un opérateur satellite.

**Le prototype n'est pas du code de vol.** Python, allocation dynamique : les exigences de mémoire statiquement bornée et de temps d'exécution pire cas ne sont pas démontrables ici. L'action est scalaire et exploite une hypothèse de monotonie propre au modèle testé ; le cas vectoriel exige la formulation quadratique complète. L'incertitude est supposée constante sur l'horizon de prédiction.

**Un seul cas d'usage.** La généricité du moniteur — couche de décision en boîte noire, jeu de contraintes versionné — est une propriété de conception, pas une propriété démontrée.

---

## Contenu

```
ram_p0/
  contraintes.py       types du jeu de contraintes (versionné, seuils d'incertitude par contrainte)
  filtre.py            filtre de sécurité prédictif, spécialisation scalaire de W&Z
  moniteur.py          verdicts, verrouillage du repli, compilation du jeu, signal de vie
  trace.py             enregistreur : formats 16/48/160 octets, tampon anneau figé, CRC, décodeur
  demo_eps.py          scénario EPS façon CySat-I, injection de fautes
  test_moniteur.py     tests, chacun rattaché à une exigence
ram_p2/
  chemins.py           résolution des chemins du dépôt
  campagne_p2.py       campagne Monte Carlo, quatre bras (chemins relatifs)
  executer_p2_3.py     exécution parallèle par run (chemins relatifs)
  config_p2_1.json     configuration figée P2.1     resultats_p2_1.json
  config_p2_2.json     configuration figée P2.2     resultats_p2_2.json
  config_p2_3.json     configuration figée P2.3     resultats_p2_3.json
ram_p3/
  pilote_p3.py         pilote de puissance, bras B seul, avant figeage
  executer_p3_1.py     exécution parallèle P3.1 et fusion des partiels
  config_pilote_p3.json, config_p3_1.json (figée avant exécution)
  resultats_pilote_p3.json, partiel_r*.json, resultats_p3_1.json
empreintes/            octets exacts ayant produit les résultats publiés —
                       pour la vérification, jamais l'exécution
                       (voir empreintes/README.md)
verifier_empreintes.py compare module par module les empreintes SHA-256
                       embarquées dans les résultats aux octets d'empreintes/
.github/workflows/tests.yml
                       à chaque push : pytest ram_p0/test_moniteur.py,
                       puis verifier_empreintes.py
.github/workflows/p3.yml
                       déclenchement manuel : exécute P3.1, un job par point r
```

Les trois campagnes sont conservées. P2.1 comportait un défaut de plan d'expérience — le bras C y faisait varier deux choses à la fois — corrigé en P2.2 par l'ajout du bras D et l'extension de la grille. P2.3 porte N de 32 à 300 sans autre changement. Les points communs se reproduisent à l'identique, vérifié comme non-régression.

---

## Reproduction

```bash
python3 -m pytest ram_p0/test_moniteur.py -q
python3 ram_p0/demo_eps.py
python3 verifier_empreintes.py
python3 ram_p2/executer_p2_3.py ram_p2/config_p2_2.json resultats_rejeu.json 4
```

Python 3.10+, bibliothèque standard uniquement.

**Environnement d'exécution des campagnes publiées.** P2.1, P2.2 et P2.3 ont tourné en septembre 2026 dans le bac à sable Linux d'un agent logiciel (CPython 3.12.12, x86-64). Les chemins absolus `/mnt/agents/output/...` visibles dans les octets d'archive (`empreintes/`) sont ceux de cet environnement ; les copies exécutables de `ram_p0/` et `ram_p2/` résolvent leurs chemins relativement au dépôt (`ram_p2/chemins.py`) et se rejouent telles quelles après un clone. Un rejeu reproduit les résultats run par run ; ses `empreintes_code` sont identiques pour les quatre modules du moniteur et différentes pour les deux pilotes, dont seuls les chemins ont été relativisés — la vérification des empreintes pointe donc sur `empreintes/`.

Les graines sont dans les fichiers de configuration, les empreintes SHA-256 des modules dans les fichiers de résultats. Toute modification de configuration crée une nouvelle version du fichier, jamais une édition.

---

## Choix méthodologiques

**σ n'est pas circulaire.** Il est calculé à partir des résidus de mesure — innovations contre le modèle nominal, celui-là même qu'utilise le moniteur — et jamais à partir des paramètres de la plante. Un σ dérivé du modèle de prédiction n'aurait rien mesuré.

**L'écart plante/modèle est réel et défavorable au moniteur.** La plante tire ses paramètres uniformément par run ; le moniteur garde le modèle nominal, qui suppose une capacité batterie plus haute que toute valeur tirée. Malgré cela, l'enveloppe seule ne rate rien.

**Le bras de contrôle est décisif.** Sans B, l'apport de RA-FUN-003 ne serait pas attribuable. Sans D, son coût resterait confondu avec celui du pessimisme d'évaluation.

**Provenance du code.** Quatre défauts d'interaction ont été trouvés par revue adversariale alors que la suite de tests était entièrement verte. Ils ont tous été corrigés **avant** la première campagne : les empreintes des modules du moniteur sont identiques dans les fichiers de résultats P2.1, P2.2 et P2.3 ; seul le pilote de campagne diffère. Aucun résultat rapporté n'a été produit par le code défectueux. Le pilote P2.1 (trois bras) a été édité en place pour devenir la version quatre bras, et l'environnement d'exécution n'en a conservé aucune copie : son empreinte reste vérifiable dans `resultats_p2_1.json`, et rejouer la configuration P2.1 avec la version quatre bras reproduit les bras A, B et C run par run — motif complet dans `empreintes/README.md`.

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
