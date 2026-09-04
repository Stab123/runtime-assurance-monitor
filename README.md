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
  campagne_p2.py       campagne Monte Carlo, quatre bras
  executer_p2_3.py     exécution parallèle par run
  config_p2_1.json     configuration figée P2.1     resultats_p2_1.json
  config_p2_2.json     configuration figée P2.2     resultats_p2_2.json
  config_p2_3.json     configuration figée P2.3     resultats_p2_3.json
```

Les trois campagnes sont conservées. P2.1 comportait un défaut de plan d'expérience — le bras C y faisait varier deux choses à la fois — corrigé en P2.2 par l'ajout du bras D et l'extension de la grille. P2.3 porte N de 32 à 300 sans autre changement. Les points communs se reproduisent à l'identique, vérifié comme non-régression.

---

## Reproduction

```bash
python3 -m pytest ram_p0/test_moniteur.py -q
python3 ram_p0/demo_eps.py
python3 ram_p2/executer_p2_3.py
```

Python 3.10+, bibliothèque standard uniquement.

Les graines sont dans les fichiers de configuration, les empreintes SHA-256 des modules dans les fichiers de résultats. Toute modification de configuration crée une nouvelle version du fichier, jamais une édition.

---

## Choix méthodologiques

**σ n'est pas circulaire.** Il est calculé à partir des résidus de mesure — innovations contre le modèle nominal, celui-là même qu'utilise le moniteur — et jamais à partir des paramètres de la plante. Un σ dérivé du modèle de prédiction n'aurait rien mesuré.

**L'écart plante/modèle est réel et défavorable au moniteur.** La plante tire ses paramètres uniformément par run ; le moniteur garde le modèle nominal, qui suppose une capacité batterie plus haute que toute valeur tirée. Malgré cela, l'enveloppe seule ne rate rien.

**Le bras de contrôle est décisif.** Sans B, l'apport de RA-FUN-003 ne serait pas attribuable. Sans D, son coût resterait confondu avec celui du pessimisme d'évaluation.

**Provenance du code.** Quatre défauts d'interaction ont été trouvés par revue adversariale alors que la suite de tests était entièrement verte. Ils ont tous été corrigés **avant** la première campagne : les empreintes des modules du moniteur sont identiques dans les fichiers de résultats P2.1, P2.2 et P2.3 ; seul le pilote de campagne diffère. Aucun résultat rapporté n'a été produit par le code défectueux.

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
