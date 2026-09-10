# P4b — PRÉENREGISTREMENT EXPÉRIMENTAL ET STATISTIQUE — v0.1

**Date : 2026-09-11. Statut : PROPOSÉ POUR GEL — en attente de validation
explicite. Aucune simulation P4b, aucun pilote, aucun Monte-Carlo, aucun run
exploratoire n'a été exécuté pour construire ce document. Tous les calculs
rapportés sont analytiques (propriétés binomiales exactes, dynamique SoC de
la plante historique gelée) ou des vérifications du code/scénario
historique.**

Base physique : `P4B_PHASE0_PHYSICAL_BASIS_v0.6.md` — statut **READY FOR
PREREGISTRATION — FINAL PHYSICAL FREEZE APPROVED**. Le modèle physique v0.6
est **intangible** ; aucune décision du présent protocole ne le modifie ni
n'en dépend au sens des résultats (aucun résultat P4b n'existe).

Références immuables : v1.4.1 (commit
`2d4ce6a2cecc52778a2f5ebf649e2a128c6a8138`, DOI 10.5281/zenodo.22681860) ;
P4a gelé au commit `aba115ff174ee41629f1fda27b6ff826a007622c` (release
v1.5.0-p4a), verdict D — INCONCLUSIVE. **Aucun chiffre des 21 blocs
défaillants P4a n'a été consulté ni utilisé pour aucune décision ci-dessous.**

---

## 1. Question scientifique et hypothèses

Question : dans le domaine de mismatch structurel gelé (réalité = tension
terminale sous charge ; enveloppe B = proxy SoC ≥ 0.35), la suffisance de B
présente-t-elle une transition localisable en ρ ∈ [1.0 ; 2.0] ?

Hypothèses (v0.6 §8, inchangées) traduites en critères testables :

- **H_P4b-frontière** est **soutenue** si et seulement si le verdict final
  (après contrôles) est **TRANSITION DETECTED** au sens du §12 (V4). Elle est
  **non soutenue** si le verdict est SUFFICIENT OVER TESTED DOMAIN ou
  INSUFFICIENT AT BASELINE. Elle est **non tranchée** sinon.
- **H_P4b-mécanisme** est **soutenue** si et seulement si TRANSITION
  DETECTED est confirmée par les contrôles numériques préenregistrés
  (§14 : contrôle de pas de temps, re-run déterministe). Toute sensibilité
  au pas de temps ou anomalie logicielle la **réfute** au sens du protocole
  (verdict dégradé, §14).

La possibilité que les deux hypothèses soient **non soutenues** est un
résultat valide et préenregistré.

---

## 2. Plante, scénario, nuisances — héritage gelé

Plante historique (`ram_p0/demo_eps.py`, inchangée) étendue par le modèle
physique v0.6 (Thevenin ordre 1, équations §5 de la v0.6) — **le code
d'extension n'est pas écrit dans ce document** ; il le sera après gel du
protocole, sans aucune liberté d'interprétation résiduelle.

Scénario P2.3 gelé (config `config_p4a.json`, inchangé) :

- durée T = 13 500 s (2.5 orbites), pas dt = 5.0 s, soit 2 700 pas ;
- orbite 5 400 s : lumière [0 ; 3 600), éclipse [3 600 ; 5 400) ;
  `en_lumiere = (t % 5400) < 3600` ; t0 = 0 = début de phase lumière ;
- fenêtre payload : `(t % 5400) ∈ [600 ; 1500)` **et** lumière → u = 3.0 A,
  sinon u = 0 (répétée chaque orbite) ;
- moniteur B actif et inchangé : seuil SoC 0.35, marge 0.02, τ_arm = 120 s,
  politique de repli inchangée (u_exec peut être 0 en repli) ;
- bruit de mesure gelé : `bruit_std = [1e-7 ; 0.1]` (canaux SoC, température) ;
- **biais d'estimation SoC : b = 0 en P4b** (l'interaction biais × structure
  est explicitement remise à une campagne ultérieure — v0.6 §11.2-8) ;
- aléa physique : `V_pack(t) < V_min,pack = 5.0 V` (v0.6, GELÉ).

Tables physiques gelées (SHA256) :

- `data/ocv_soc_ncr18650b_hnei.csv` :
  `7aa959fc99effefbc995237291217cec1657145051b3fa70cd7678fe0b7154c2`
- `data/rint_soc_nmc_dtu.csv` :
  `330efcd3165f5676f06b9128f723566193cc66fa6844fdddbc1f782015697b93`

---

## 3. Facteur expérimental : grille exacte de ρ (PENDING 1)

**Grille gelée : 9 niveaux, uniforme, pas 0.125 :**

```
ρ ∈ {1.000 ; 1.125 ; 1.250 ; 1.375 ; 1.500 ; 1.625 ; 1.750 ; 1.875 ; 2.000}
```

Justification pré-data :

- **Uniforme** : aucune connaissance préalable sur la localisation d'une
  transition éventuelle ; densifier la grille dans une région soupçonnée
  serait un choix orienté résultat. L'uniformité est la seule grille sans
  prior de localisation.
- **9 niveaux** : structure héritée de la campagne P4a (9 niveaux de biais),
  approuvée à l'audit P4a ; équilibre résolution/coût.
- **Pas 0.125** : résolution de localisation ≤ 12.5 % du domaine ; l'intervalle
  de frontière rapporté aura une largeur minimale de 0.125 (§10).
- **Bornes incluses** : ρ = 1.000 = référence cellule neuve (indispensable
  pour le verdict INSUFFICIENT AT BASELINE) ; ρ = 2.000 = borne haute
  justifiée v0.6 §7.1 (indispensable pour borner une frontière > 2).
- **Aucune adaptation de grille après observation** : interdite (toute
  extension éventuelle serait une campagne séparée, préenregistrée à part).

---

## 4. Endpoint statistique formel (PENDING 2)

Pour le run j au niveau ρ, sur la grille de simulation discrète
t_k = k·dt, k = 0, …, 2699 (dt = 5.0 s) :

```
V_min,j = min over k of V_pack(t_k)      (float64, état au temps t_k,
                                          toutes phases : lumière, éclipse,
                                          payload — aucune exclusion)
Y_j     = 1{ V_min,j < 5.0 }             (inégalité stricte ; l'égalité
                                          V_min,j = 5.0 exactement n'est
                                          PAS une violation)
```

**Précision d'évaluation (déterminisme d'implémentation)** : pour chaque pas
k, V_pack(t_k) est calculé sur l'état (SoC(t_k), Vp(t_k)) et le courant
effectivement appliqué à ce pas, I_cell(t_k) = (I_BASE + u_exec(t_k) −
i_charge(t_k))·C_cell/C_BATT — y compris en repli du moniteur (u_exec = 0) —
avec Vp(t0) initialisé selon la règle gelée v0.6 §7.2-E. Aucune grandeur
n'est évaluée entre les pas.

- **Comparaison en float64**, sans arrondi ni tolérance avant comparaison.
- **Valeurs non finies** : si un V_pack(t_k), SoC(t_k) ou Vp(t_k) est NaN
  ou ±Inf à un pas quelconque, le run est **INVALID_TECHNIQUE** : il n'entre
  ni dans le numérateur ni dans le dénominateur, il est compté et journalisé,
  et la campagne bascule en verdict INVALID / TECHNICAL FAILURE (§12, V0) —
  tolérance zéro.
- **Run interrompu** : un run est complet si et seulement s'il atteint
  k = 2699 sans exception ; tout run incomplet = INVALID_TECHNIQUE (même
  traitement).
- **Drapeau hors domaine physique** (SoC(t) ∉ [0 ; 1]) : le run **reste**
  dans l'analyse (règle d'inclusion, §9) et porte le drapeau.
- **Distinction violation / erreur** : Y n'est calculé que sur des runs
  valides ; une erreur de simulation n'est jamais comptée comme violation
  ni comme non-violation.
- **Estimateur par niveau** : p̂_j = x_j / 5500, où x_j = Σ Y_j sur les runs
  valides du niveau j (la tolérance zéro technique garantit 5 500 runs
  valides par niveau, sinon la campagne est invalide).
- **Descripteur secondaire préenregistré** (descriptif, hors verdict) :
  violation silencieuse = Y_j = 1 ∧ min_k SoC(t_k) ≥ 0.35 — le cœur
  conceptuel du mismatch (B satisfaite, aléa physique franchi). Rapporté
  par niveau, sans rôle dans la règle de décision.

---

## 5. Seuils εS et εF (PENDING 3)

**Gelés : εS = 0.01 ; εF = 0.05.**

- **Justification indépendante de tout résultat P4b** : ce sont les seuils
  de classification statistique préenregistrés de P4a (`config_p4a.json`,
  gelés avant toute exécution P4a, qualifiés à l'époque de « seuils de
  classification statistique — pas des exigences de sûreté spatiale »).
  Les reprendre à l'identique est la seule option sans arbitraire nouveau :
  toute autre paire devrait être justifiée par des considérations
  étrangères au projet.
- **Sémantique** : « B opérationnellement suffisant au niveau ρ » ⟺ la
  probabilité de violation p(ρ) ≤ 1 % ; « B insuffisant » ⟺ p(ρ) ≥ 5 %.
- **Zone intermédiaire explicite** : p ∈ (0.01 ; 0.05) = zone d'indétermination
  déclarée — le protocole ne force aucune conclusion dans cette zone.
- Ces seuils n'ont été choisis ni pour obtenir ni pour éviter une
  frontière : ils préexistent à la question P4b.

**Méthode d'intervalle de confiance préenregistrée** : **IC de Wilson
bilatéral 99.4444 %** (z = 2.7729212946086634), calculé par la formule
standard centrée :

```
centre = (p̂ + z²/2N) / (1 + z²/N)
demi   = z·sqrt(p̂(1−p̂)/N + z²/4N²) / (1 + z²/N)
IC     = [centre − demi ; centre + demi]
```

**Classification d'un niveau (déterministe)** :

- **SUFFICIENT** ⟺ borne supérieure de l'IC99.44 ≤ εS = 0.01 ;
- **INSUFFICIENT** ⟺ borne inférieure de l'IC99.44 ≥ εF = 0.05 ;
- **INTERMEDIATE** sinon (y compris si l'IC chevauche un seuil ou est
  entièrement dans la zone intermédiaire).

Contrôle d'erreur : chaque classification repose sur une seule borne de
l'IC bilatéral 99.4444 %, i.e. une borne unilatérale 99.7222 % →
probabilité de classification erronée ≤ **1/360 ≈ 0.278 %** par niveau et
par côté. La conclusion de frontière (V4) sélectionne max(S) et min(I)
parmi 9 niveaux : cette sélection est contrôlée par une **borne d'union de
Bonferroni sur les 18 événements d'erreur possibles** (9 niveaux × 2 côtés)
: P(au moins un niveau faussement classé S) ≤ 9/360 et P(au moins un niveau
faussement classé I) ≤ 9/360, d'où **erreur de frontière ≤ 18/360 = 5 %**,
sous dépendance arbitraire entre niveaux (la borne d'union n'exige aucune
indépendance — le CRN est sans effet sur cette garantie). Justification
complète : §15.

---

## 6. N, puissance, précision (PENDING 4)

**N = 5 500 runs par niveau de ρ** (9 niveaux × 5 500 = 49 500 runs
principaux).

Justification mathématique (calculs binomiaux exacts, audit §16) :

- Avec N = 5 500 et Wilson 99.4444 % : SUFFICIENT ⟺ x ≤ **34** ;
  INSUFFICIENT ⟺ x ≥ **320** (vérification : Wilson99.44(34/5500) =
  [0.0039 ; 0.0099] ≤ 0.01 ; Wilson99.44(35/5500) = [0.0040 ; 0.0101] >
  0.01 ; Wilson99.44(320/5500) = [0.0500 ; 0.0676] ≥ 0.05 ;
  Wilson99.44(319/5500) = [0.0499 ; 0.0674] < 0.05).
- **Exigence R1** : si la vraie p = 0.005 (= εS/2), P(SUFFICIENT) =
  P(X ≤ 34 | Bin(5500, 0.005)) = **0.906 ≥ 0.90**.
- **Exigence R2** : si la vraie p = 0.10 (= 2·εF), P(INSUFFICIENT) =
  P(X ≥ 320 | Bin(5500, 0.10)) = **1.000 ≥ 0.90**.
- N = 5 500 est le plus petit multiple de 500 satisfaisant R1 (minimum
  exact calculé par balayage entier : 5 311 ; N = 5 500 arrondi au
  demi-millier). Le dimensionnement ne porte que sur les propriétés
  statistiques ; **aucun paramètre physique n'a été ajusté pour la
  puissance** (interdit).
- **Historique de dimensionnement (pré-gel)** : une première version de ce
  préenregistrement utilisait l'IC Wilson 95 % et N = 3 500 ; l'audit final
  de cohérence (`P4B_PREREGISTRATION_FINAL_AUDIT_v0.2.md`, constat C-01) a
  démontré que la borne d'erreur de frontière « ≤ 5 % » n'était alors pas
  rigoureuse sous sélection de max(S)/min(I) parmi 9 niveaux. La correction
  pré-data — niveau d'IC 99.4444 % (Bonferroni, 18 événements) et N porté
  à 5 500 — est appliquée ici **avant toute simulation**, sans toucher à
  aucun paramètre physique ni à aucun point de design existant.
- **N ne pourra pas être augmenté après observation** ; toute étude
  supplémentaire serait une campagne séparée, préenregistrée à part.

**Cas 0/N (zéro violation observée)** : zéro violation ne signifie jamais
p = 0. Si x = 0 sur 5 500 : IC Wilson 99.4444 % = [0 ; **0.0014**] ; borne
de Clopper-Pearson unilatérale 99.7222 % = **0.00107**. Le niveau est
classé SUFFICIENT (borne sup ≤ 0.01) et le rapport indique « p ≤ 0.14 %
(IC99.44) », jamais « p = 0 ».

**Précision absolue** : largeur maximale de l'IC99.44 sur la grille : à
p̂ = 0.5, demi-largeur ≈ 0.0187 ; à p̂ = 0.05, demi-largeur ≈ 0.0082.

---

## 7. Mesure de couverture et nuisances (PENDING 5)

**Mesure de couverture** : μ_D = mesure empirique uniforme sur les 5 500
points de design — mesure de couverture expérimentale, **pas** une
distribution de flotte (formulation P4a conservée).

**Génération des nuisances** (règle P4a reprise à l'identique, nouveau flux)
— procédure exacte, sans ambiguïté :

- **une seule graine de design** : `seed_graine("PLANT", 0)` ;
- **un seul objet PRNG** : `rng = random.Random(seed_graine("PLANT", 0))`
  (Mersenne Twister stdlib Python — séquence stable et garantie
  reproductible) ;
- **tirages successifs** sur ce même flux, ordre fixe par candidat :
  **C_BATT_AH, I_SUN, I_BASE, soc0**, uniformes sur les plages gelées
  v0.6 §7.3 : C_BATT ∈ [4.4 ; 14.4] Ah, I_SUN ∈ [0.8 ; 2.5] A,
  I_BASE ∈ [0.06 ; 0.75] A, soc0 ∈ [0.40 ; 0.70] ;
- **admissibilité R1/R2/R3 inchangées** : R1 `I_SUN ≥ 1.5·I_BASE` (impliquée
  par R2) ; R2 `3600·I_SUN ≥ 5400·I_BASE + 0.5·(3·900)` ; R3 `soc0 ≥ 0.39`
  (automatiquement satisfaite) ;
- **rejection sampling continu sur ce même flux** : chaque candidat rejeté
  consomme ses quatre tirages et le flux continue ; sans remplacement
  manuel ni réordonnancement ;
- **bloc_id attribué uniquement aux points acceptés**, dans l'ordre
  d'acceptation (0, 1, 2, …) ;
- **arrêt exactement au 5 500e point accepté** ; **934 candidats rejetés**
  avant cet arrêt (taux 934/6434 = 14.5 %) — comptés et publiés ;
- **aucune graine PLANT dépendant de bloc_id** n'est utilisée : les
  nuisances individuelles ne sont pas ré-initialisées bloc par bloc ;
- points publiés en clair dans `config_p4b_design.json` (SHA256
  `20dcb71d9d8bde837f398157882811bc391e94f713e01ec7baedcb42ff815a63`),
  régénérables bit à bit par la règle ci-dessus.

**Historique de design (pré-gel)** : la version initiale du fichier
s'arrêtait au 3 500e point accepté (SHA256
`4439351a58d82dd1851568bd14e13854871e75ab75711e02563c2514f0208250`,
602 rejets). Le passage à N = 5 500 (§6, correction multiplicité) a
**prolongé le même flux sans le réinitialiser** : les 3 500 premiers points
et les 602 premiers rejets sont strictement identiques (propriété de
préfixe du flux, vérifiée bit à bit à l'audit — C-02 du rapport v0.2).
Aucun point existant n'a été modifié, remplacé, réordonné ni
ré-échantillonné.

**Common Random Numbers (CRN)** : le bloc j (jeu de nuisances j) est évalué
aux **9 niveaux de ρ avec la même graine de bruit** `seed_graine("NOISE", j)`
— structure approuvée en P4a ; les comparaisons entre niveaux sont
appariées, ce qui élimine toute sélection post-hoc entre niveaux et réduit
la variance des contrastes.

**Ordre des runs (fixe)** : bloc-major — pour j = 0, …, 5499 : pour ρ dans
l'ordre croissant de la grille : run(j, ρ). Puis les analyses de sensibilité
(§13), puis les contrôles (§14).

**Conséquence structurelle** : la trajectoire SoC ne dépend pas de ρ
(ρ n'entre que dans V_pack) ; elle ne dépend du bruit que via les décisions
de repli du moniteur — or, sous CRN, la graine de bruit est commune aux
9 niveaux d'un même bloc → la séquence de bruit, les décisions de repli et
la trajectoire SoC sont **identiques aux 9 niveaux** d'un bloc. L'ensemble
des runs flaggés « hors domaine » est donc identique aux 9 niveaux : aucun
niveau ne peut être indirectement défavorisé par les drapeaux.

---

## 8. Seeds (PENDING 6)

**Règle unique, publique, figée** (mécanisme P4a, nouvelle version de
campagne) :

```
seed(label, i) = int(SHA256(s)[0:8], big-endian) mod 2^31
s = "P4b-structural-v1|2d4ce6a2cecc52778a2f5ebf649e2a128c6a8138|
     10.5281/zenodo.22681860|<label>|<i>"
```

- **Labels autorisés** : distinction explicite entre les deux usages —
  **(A) design nuisance** : `PLANT`, compteur **i = 0 unique**, flux global
  continu (§7) — une seule graine pour les 5 500 points, aucune graine
  PLANT par bloc ; **(B) bruit de mesure** : `NOISE`, i = bloc_id ∈
  [0 ; 5499] — une graine indépendante dérivée par bloc, partagée entre
  les 9 niveaux du bloc (CRN) et réutilisée telle quelle pour le contrôle
  de pas de temps (convention P4a-dtctrl : mêmes graines, seul dt change).
  Aucun autre label ; aucune graine P2/P3/P4a réutilisée.
- **PRNG** : `random.Random` (Mersenne Twister, bibliothèque standard
  Python) — le même que P4a ; versions enregistrées (§14).
- **Séparation des sources** : nuisances (PLANT) et bruit (NOISE) sont des
  flux indépendants par construction (labels distincts) ; l'ordre
  d'exécution étant fixe, aucune graine d'ordre/permutation n'est requise.
- **Publication** : la règle de dérivation et les labels sont publiés ici ;
  les 5 500 points de design dérivés sont publiés en clair
  (`config_p4b_design.json`, SHA256
  `20dcb71d9d8bde837f398157882811bc391e94f713e01ec7baedcb42ff815a63`) ; les
  graines de bruit sont dérivables publiquement par quiconque.
- **Interdiction** : aucune graine ne peut être remplacée, ré-échantillonnée
  ou « réessayée » après observation d'un résultat. Les analyses de
  sensibilité OCV (§13) réutilisent les **mêmes** graines (CRN), jamais de
  nouvelles.

---

## 9. SoC hors [0 ; 1] — traitement statistique (PENDING 9)

Rappel v0.6 (gelé) : plante sans saturation ; tables clampées ; événement
enregistré comme drapeau « hors domaine physique du modèle » (premier
instant, durée cumulée).

**Analyse pré-data de l'exposition** (calcul analytique sur la dynamique SoC
gelée, sans exécution de la plante P4b) : quadrature sur la région
admissible → P(max_t SoC > 1) ≈ **6.6 %** ; P(min_t SoC < 0) = 0 (R2 garantit
un bilan net ≥ 0 par orbite) ; sur les 5 500 points de design publiés :
**330 points (6.0 %) flaggés** (calcul déterministe sans repli du moniteur —
le repli ne peut qu'augmenter SoC : borne basse du compte ; SoC minimum
observé sur le design : 0.19). Le drapeau est donc un événement attendu, non
pathologique, de fréquence **identique aux 9 niveaux** (§7).

**Options comparées** :

| Option | Verdict | Motif |
|---|---|---|
| Exclusion des runs flaggés | **Rejetée** | permettrait de retirer après coup des runs « gênants » ; brise le CRN (dénominateurs différents par niveau si le bruit interagissait) ; biais de sélection |
| Censure (run tronqué au drapeau) | **Rejetée** | le min avant censure ignore la fin du run ; introduit une dépendance au temps de drapeau, non interprétable pour un endpoint en min |
| Invalidation systématique | **Rejetée** | ~6 % de runs perdus par construction, sans nécessité |
| **Inclusion + drapeau + reporting + garde-fou** | **Retenue** | aucun run retiré, jamais ; leverage des flags mesuré par analyse bornée préenregistrée |

**Règle principale (gelée)** : **inclusion** — un run flaggé contribue à Y
comme tout autre run (le clamp des tables est la règle de calcul gelée) ;
les comptes de drapeaux sont rapportés par niveau.

**Analyse de robustesse bornée (préenregistrée, déterministe)** : pour
chaque niveau, on compte x_j^(flag) = violations dont le min V_pack survient
**pendant** une période flaggée (seules violations potentiellement artefacts
du clamp, le clamp sous-estimant OCV à SoC > 1). Sensibilité :
x_j' = x_j − x_j^(flag) → reclassification. Si la classification change →
niveau annoté **FLAG-SENSITIVE** ; la classification principale (inclusion)
est inchangée ; si le verdict de frontière change → dégradation selon la
règle symétrique du §13.

**Seuil d'invalidation préspécifié** : si la fraction de runs flaggés à un
niveau dépasse **25 %**, le niveau est déclaré **UNINTERPRETABLE (MODEL
LIMIT)** ; comme la fréquence est identique aux 9 niveaux (§7), cela
équivaut à : campagne → **INCONCLUSIVE (MODEL LIMIT)** (§12, V0b).
Justification du seuil : au-delà d'un quart des runs hors domaine de
validité, l'estimateur reflète davantage la règle de clamp que le modèle
physique ; en dessous, l'analyse bornée encadre l'effet. L'exposition
attendue (≈ 6 %) laisse une marge d'un facteur ≈ 4 — le seuil n'a pas été
calé sur l'exposition mesurée mais sur la lisibilité du modèle.

---

## 10. Frontière P4b — définition mathématique (section 6 du mandat)

Soient S = {ρ_j : niveau classé SUFFICIENT}, I = {ρ_j : niveau classé
INSUFFICIENT}, M = le reste (INTERMEDIATE), toutes classifications issues
uniquement des IC Wilson 99.4444 % du §5.

- **Existence** : une frontière **existe** au sens du protocole ssi
  S ≠ ∅, I ≠ ∅, et max(S) < min(I) (aucune inversion dure, §11).
- **Localisation** : si elle existe, la frontière est rapportée comme
  l'**intervalle** b* ∈ (max(S) ; min(I)]. Sa largeur est un multiple du pas
  0.125 (les niveaux M éventuels à l'intérieur élargissent l'intervalle :
  l'incertitude est rapportée, jamais résorbée).
- **Résolution maximale** : 0.125 (pas de grille). Aucune localisation
  plus fine n'est revendiquée ; aucune interpolation entre niveaux n'est
  utilisée pour « préciser » b*.
- **Annotation résolution** : si min(I) − max(S) > 0.250 (au moins trois pas
  de grille, i.e. au moins deux niveaux M dans l'intervalle), la frontière
  est rapportée avec l'annotation **LOW RESOLUTION**.
- **Borne seule** : si S ≠ ∅ et I = ∅ avec max(S) < 2.000 : seule la borne
  b* > max(S) est rapportée. Si I ≠ ∅ et S = ∅ : seule la borne
  b* < min(I) est rapportée (et si 1.000 ∈ I : INSUFFICIENT AT BASELINE).
- **b* = null** : si ni S ni I ne sont non vides, ou en cas d'inversion
  dure, ou si le garde-fou hors-domaine (§9) ou technique (§4) se déclenche.
- **Transition entre deux niveaux** : c'est le cas nominal — l'intervalle
  (max(S) ; min(I)] contient alors exactement un pas de grille.
- **Aucune région suffisante ou insuffisante démontrée** : verdict
  INCONCLUSIVE ; aucune frontière descriptive n'est promue en frontière
  statistique.

Une transition descriptive (p̂ croissant, IC se chevauchant) **n'est pas**
une frontière localisée : seuls les critères ci-dessus concluent.

---

## 11. Monotonie (section 5 du mandat)

- **Attente physique** : à nuisances fixées (CRN), V_pack est globalement
  décroissante en ρ (Rs, Rp croissants ; l'effet de τ = ρ·Rp·Cp sur Vp n'est
  pas ponctuellement monotone en t, donc la monotonie stricte de min_t V
  n'est **pas** un théorème). La monotonie de p(ρ) est une **attente
  physique**, pas une hypothèse imposée.
- **Statistique** : la monotonie n'est **ni imposée ni lissée** — elle est
  **testée**. Aucune régression isotone (PAVA) ni aucun lissage monotone
  n'est utilisé pour la classification, la frontière ou le verdict.
- **Détection** : **inversion dure** ⟺ ∃ j < k : ρ_j ∈ I et ρ_k ∈ S
  (un niveau insuffisant en dessous d'un niveau suffisant). Détection
  déterministe sur les labels, pas sur les p̂.
- **Effet sur la frontière** : toute inversion dure → **b* = null**, verdict
  FRONTIER NOT LOCALIZED (NON-MONOTONE) — la structure non monotone est
  rapportée telle quelle.
- **Inversions descriptives** (p̂ non monotone sans conflit de labels) :
  rapportées dans le tableau des résultats, sans effet sur le verdict.

---

## 12. Règle de décision déterministe (PENDING 7)

Évaluation **dans l'ordre** ; premier cas qui matche l'emporte. Les labels
S/I/M par niveau viennent du §5 ; S, I, M définis au §10.

| # | Condition (déterministe) | Verdict |
|---|---|---|
| V0 | ≥ 1 run INVALID_TECHNIQUE (NaN/Inf/interrompu, §4) dans la campagne **principale** | **INVALID / TECHNICAL FAILURE** — campagne arrêtée, cause documentée, reprise uniquement après correction et ré-exécution intégrale avec les mêmes graines (jamais de relance partielle). Un run invalide dans une campagne de sensibilité ou de contrôle invalide **cette analyse-là** (annotation « analyse invalide »), pas le verdict principal |
| V0b | fraction de runs flaggés > 25 % (§9) | **INCONCLUSIVE (MODEL LIMIT)** |
| V1 | les 9 niveaux ∈ S | **SUFFICIENT OVER TESTED DOMAIN** |
| V2 | ρ = 1.000 ∈ I | **INSUFFICIENT AT BASELINE** |
| V3 | ∃ j < k : ρ_j ∈ I ∧ ρ_k ∈ S (inversion dure) | **FRONTIER NOT LOCALIZED (NON-MONOTONE)** |
| V4 | S ≠ ∅ ∧ I ≠ ∅ ∧ max(S) < min(I) | **TRANSITION DETECTED**, b* ∈ (max(S) ; min(I)] ; annotation LOW RESOLUTION si largeur > 0.250 |
| V5 | S ≠ ∅ ∧ I = ∅ ∧ non V1 | **FRONTIER NOT LOCALIZED** — borne b* > max(S) ; interprétation : transition éventuelle au-delà de la région certifiée suffisante, non démontrée (couvre notamment le cas où la frontière serait au-delà de ρ = 2) |
| V6 | S = ∅ ∧ I ≠ ∅ (et non V2, donc ρ = 1.000 ∈ M) | **FRONTIER NOT LOCALIZED** — borne b* < min(I) ; aucune région suffisante certifiée |
| V7 | S = ∅ ∧ I = ∅ | **INCONCLUSIVE** — puissance insuffisante pour trancher dans la zone intermédiaire |

**Exhaustivité** : les cas partitionnent l'espace (S, I vides ou non ; si les
deux non vides, soit max(S) < min(I) → V4, soit ∃ inversion dure → V3 ; V1/V2
sont prioritaires et disjoints des cas suivants). Deux analystes appliquant
cette table aux mêmes labels obtiennent nécessairement le même verdict.

**Couverture des cas du mandat** : A (zéro violation partout) → x_j = 0 ∀j
→ tous S → V1. B (violations dès ρ = 1) → V2 si classé I, sinon V6/V7. C
(transition dans [1 ; 2]) → V4. D (violations sans classification nette) →
V6/V7. E (région intermédiaire persistante) → V4 avec annotation LOW
RESOLUTION si M entre S et I, sinon V7. F (non monotone) → V3. G (frontière
> 2) → V5. H (trop de hors-domaine) → V0b. I (anomalie technique) → V0. J
(incompatible avec les hypothèses, ex. V2 ∧ inversion dure) → V2 est
prioritaire et rapporté avec l'inversion documentée ; le texte
d'interprétation déclare H_P4b-frontière non tranchée.

**Jamais de frontière forcée** : V4 est la seule voie vers TRANSITION
DETECTED et exige des labels certifiés aux deux bornes.

---

## 13. Sensibilité OCV ±0.1 V pour SoC < 2 % (PENDING 10)

Obligation héritée de la v0.6 (§6.4, §11.2-10). Traitement gelé :

- **Déclenchement** : **toujours exécutée** (analyse secondaire
  préenregistrée, non conditionnelle aux résultats — exécuter
  systématiquement supprime toute possibilité de choisir après coup).
- **Variantes exactes** : deux campagnes complètes (9 × 5 500 runs, mêmes
  points de design et mêmes graines — CRN) avec, **uniquement pour l'analyse
  de sensibilité** : OCV_+(s) = OCV(s) + 0.1 V et OCV_−(s) = OCV(s) − 0.1 V
  aux points de table s ∈ {0.00 ; 0.02} (interpolation linéaire inchangée —
  perturbation maximale dans l'incertitude déclarée v0.6). La table gelée
  n'est **pas** modifiée : ce sont des variantes d'analyse, pas du modèle.
- **Statut** : analyse **secondaire** ; le verdict principal est toujours
  calculé sur la table gelée.
- **Effet sur le verdict (dégradation seule)** : les labels S/I/M sont
  recalculés sous OCV_+ et OCV_− ; si les conditions V1–V7 changent sous
  l'une ou l'autre variante :
  - TRANSITION DETECTED → **FRONTIER NOT LOCALIZED (OCV SENSITIVE)** si la
    frontière disparaît, apparaît ou se déplace sous une variante ;
  - autre verdict → annotation **OCV-SENSITIVE** ajoutée, verdict inchangé ;
  - si les deux variantes confirment le verdict principal → annotation
    **robuste à l'incertitude OCV locale**.
- **Règle symétrique pour les drapeaux** (§9) : si la reclassification
  x_j' = x_j − x_j^(flag) change les conditions V1–V7 :
  TRANSITION DETECTED → **FRONTIER NOT LOCALIZED (FLAG SENSITIVE)** ;
  autre verdict → annotation **FLAG-SENSITIVE**.
- Une analyse de sensibilité ne peut **jamais** transformer un verdict
  autre en TRANSITION DETECTED, ni déplacer une frontière : elle ne fait
  que dégrader la certitude.

---

## 14. Reproductibilité et contrôles (PENDING 8)

**Environnement** : Python 3.12 (stdlib `random` Mersenne Twister, séquence
garantie stable), numpy/scipy pour l'analyse uniquement ; versions exactes
enregistrées dans les métadonnées de résultats (mécanisme P4a
`empreintes_code` + hash config, repris).

**Empreintes publiées dans ce préenregistrement** :

- tables physiques : SHA256 au §2 ;
- design : `config_p4b_design.json` SHA256
  `20dcb71d9d8bde837f398157882811bc391e94f713e01ec7baedcb42ff815a63`
  (5 500 points, 934 rejets documentés ; version antérieure à 3 500 points
  : SHA256 `4439351a58d82dd1851568bd14e13854871e75ab75711e02563c2514f0208250`,
  préfixe strict de la version courante — vérifié bit à bit) ;
- code : le gel du protocole sera accompagné d'un commit unique contenant
  l'implémentation P4b ; les SHA256 des fichiers seront alors calculés et
  publiés avant exécution (même discipline que P4a).

**Conservation** : résultats bruts par run (JSONL : bloc_id, ρ, paramètres
plante, graine bruit, Y, V_min, t_min, drapeaux, témoin de bruit), logs
d'exécution, config et code hashés — tout conservé, rien d'effacé.

**Contrôles préenregistrés (au service de H_P4b-mécanisme)** :

1. **Re-run déterministe** : la campagne principale complète est ré-exécutée
   une seconde fois avec les mêmes graines ; exigence : vecteurs Y et V_min
   **bit à bit identiques** sur la même plateforme (tolérance cross-plateforme
   : écart relatif < 1e-12 sur V_min, Y identique). Toute divergence →
   INVALID / TECHNICAL FAILURE (V0).
2. **Contrôle du pas de temps** : campagne de contrôle à dt = 2.5 s
   (`dt_controle_s`, héritage P4a), mêmes points de design et **mêmes
   graines de bruit** (label NOISE, convention P4a-dtctrl : seul dt change),
   sur : ρ = 1.000, ρ = 2.000, **et** — si V4 s'applique — les deux niveaux
   bornant la frontière (max(S), min(I)). Critère : les labels S/I/M sous
   dt = 2.5 s doivent être identiques à ceux du principal pour ces niveaux.
   Toute différence qui change le verdict → **INCONCLUSIVE (NUMERICAL
   SENSITIVITY)** ; différence sans effet sur le verdict → annotation
   rapportée.
3. **Témoin CRN** : hash par bloc (paramètres + graine bruit + bruit pur au
   pas 1 000), mécanisme P4a repris — vérifie l'appariement entre niveaux.
4. **Procédure de divergence** : toute divergence reproduction/original →
   arrêt, documentation ; toute correction de code → amendement écrit au
   protocole **avant** reprise, sans toucher aux graines ni aux points.

**Jamais de nouveau protocole après coup** : les contrôles ci-dessus sont
les seuls ; tout contrôle supplémentaire serait descriptif et marqué comme
tel.

---

## 15. Multiplicité et intervalles (section 7 du mandat)

**Problème de sélection identifié et traité (audit final v0.2, C-01)** : la
règle V4 sélectionne max(S) et min(I) **parmi 9 niveaux**, selon les
données. Une borne « conjonction de deux classifications IC95 → erreur
≤ 5 % » n'est **pas** valable pour une sélection post-hoc : si plusieurs
niveaux ont une vraie p juste au-dessus de εS, la probabilité qu'**au moins
un** soit faussement classé SUFFICIENT croît avec le nombre de niveaux
(calcul : p = 0.0101 partout sauf le niveau haut → P(≥ 1 faux S) ≈ 13 %
avec des IC95). Le niveau d'IC par niveau a donc été relevé **avant toute
simulation** pour contrôler l'erreur de la famille complète :

- **IC ponctuels** : Wilson bilatéral **99.4444 %** par niveau
  (z = 2.7729212946086634), i.e. borne unilatérale 99.7222 % par côté
  (erreur ≤ 1/360 ≈ 0.278 %).
- **Contrôle de la famille** : les événements d'erreur possibles sont les
  9 fausses classifications S (p(ρ) > εS mais classé SUFFICIENT) et les 9
  fausses classifications I (p(ρ) < εF mais classé INSUFFICIENT) — **18
  événements**. Borne d'union de Bonferroni : P(≥ 1 erreur dans la famille)
  ≤ 18/360 = **5 %**, **sous dépendance arbitraire** entre niveaux (la
  borne d'union ne suppose pas l'indépendance ; le CRN ne dégrade donc
  aucune garantie).
- **Conclusion de frontière (V4)** : « b* ∈ (max(S) ; min(I)] » est erronée
  seulement si max(S) est une fausse classification S ou min(I) une fausse
  classification I — deux événements inclus dans la famille ci-dessus →
  **erreur de frontière ≤ 5 %, garantie non conditionnelle**, valable quelle
  que soit la sélection effectuée par V4 parmi les 9 niveaux.
- **Verdicts V1/V5 (suffisance)** : V1 exige 9 classifications S ; une
  erreur de V1 implique ≥ 1 fausse classification S → ⊆ famille, ≤ 5 %.
- **Verdicts V2/V6 (insuffisance)** : une erreur implique ≥ 1 fausse
  classification I → ⊆ famille, ≤ 5 %.
- **Pas de procédure séquentielle** : campagne à taille fixe
  (49 500 runs principaux) ; aucun arrêt anticipé, aucune extension.
- Les p̂_j, IC_j et descripteurs (violations silencieuses, inversions de p̂)
  sont rapportés à titre **descriptif**, sans garantie simultanée
  supplémentaire — déclaré.

---

## 16. Audit de puissance (section 8 du mandat — calculs exacts, binomiale)

Probabilités de classification d'un niveau (N = 5 500 ; S ⟺ x ≤ 34 ;
I ⟺ x ≥ 320 ; M sinon) en fonction de la vraie probabilité p :

| vraie p | P(SUFFICIENT) | P(INTERMEDIATE) | P(INSUFFICIENT) |
|---|---|---|---|
| 0 | 1.000 | 0.000 | 0.000 |
| 0.0025 | 1.000 | 0.000 | 0.000 |
| 0.005 (= εS/2) | **0.906** | 0.094 | 0.000 |
| 0.01 (= εS) | 0.002 | 0.998 | 0.000 |
| 0.02 | 0.000 | 1.000 | 0.000 |
| 0.03 | 0.000 | 1.000 | 0.000 |
| 0.05 (= εF) | 0.000 | 0.996 | 0.004 |
| 0.075 | 0.000 | 0.000 | **1.000** |
| 0.10 (= 2·εF) | 0.000 | 0.000 | **1.000** |
| 0.20 | 0.000 | 0.000 | 1.000 |

Lecture honnête :

- **Faux « suffisant »** (vraie p > εS) : ≤ 0.278 % par niveau par
  construction (borne unilatérale 99.7222 %) ; nul en pratique dès
  p ≥ 0.02.
- **Faux « insuffisant »** (vraie p < εF) : ≤ 0.278 % par niveau par
  construction ; nul en pratique pour p ≤ 0.03.
- **Zone intermédiaire** (0.01 ; 0.05) : quasi-toujours INTERMEDIATE —
  comportement voulu et déclaré : le design refuse de trancher dans la zone
  d'indifférence.
- **Aux seuils exacts** (p = εS ou p = εF), le niveau est
  quasi-certainement INTERMEDIATE : la règle est conservative à la frontière
  de classification — propriété annoncée, pas un défaut découvert.

Puissance au niveau campagne — **calcul indicatif sous indépendance entre
niveaux** (statut exact : les garanties confirmatoires du §5/§15 — erreur
par niveau ≤ 0.278 %, erreur de famille et de frontière ≤ 5 % — sont
établies par borne d'union et valent **sous dépendance arbitraire**, donc
sous CRN ; les valeurs ci-dessous, elles, supposent l'indépendance et sont
des ordres de grandeur) :

| Scénario idéalisé | P(verdict correct) sous indépendance |
|---|---|
| Transition nette entre ρ = 1.500 (p = 0.004) et ρ = 1.625 (p = 0.15) | ≈ 1.000 |
| Transition nette entre ρ = 1.000 (p = 0.004) et ρ = 1.125 (p = 0.15) | ≈ 0.994 |
| p = 0.004 partout (pas de transition) | P(SUFFICIENT OVER TESTED DOMAIN) ≈ 0.945 |
| p = 0.15 dès ρ = 1.000 | P(INSUFFICIENT AT BASELINE) = 1.000 |

**Direction de l'effet CRN (analysée, non supposée)** : le CRN induit une
corrélation positive attendue entre les classifications de niveaux proches.
Pour les verdicts de type **conjonction** (V1 = les 9 niveaux S), une
corrélation positive **augmente** P(∩) par rapport au produit — le calcul
sous indépendance est alors une **borne basse** (conservatif). Pour les
verdicts impliquant des **événements d'existence** (V4 : « ≥ 1 niveau S »
et « ≥ 1 niveau I »), la direction n'est pas uniformément déterminée — les
valeurs 1.000 / 0.994 ci-dessus sont donc **indicatives**, sans qualité de
borne. Aucune propriété non démontrée n'est revendiquée.

Le design est jugé **suffisamment puissant** pour les régions tranchées et
honnêtement non conclusif dans la zone intermédiaire ; N n'est modifié ni
pour approcher ni pour éviter une frontière.

---

## 17. Contrôle anti-post-hoc (section 9 du mandat)

| Vérification | État |
|---|---|
| Grille ρ choisie sans résultat P4b | ✅ — uniforme 9 niveaux, justification sans prior de localisation (§3) ; aucune simulation P4b n'existe |
| N choisi sans résultat P4b | ✅ — dimensionnement binomial exact sur εS/εF (§6, §16) ; relevé de 3 500 à 5 500 **avant toute simulation** par l'audit final v0.2 (correction multiplicité C-01), sans toucher aux paramètres physiques ni aux points existants |
| εS/εF choisis sans résultat P4b | ✅ — reprise des seuils préenregistrés P4a, gelés avant P4a elle-même (§5) |
| Seeds choisies sans résultat P4b | ✅ — règle de dérivation SHA256 publiée ; aucune graine n'a été « essayée » ; les points de design sont des tirages PRNG, pas des simulations de la plante P4b |
| Règle SoC hors domaine choisie sans résultat P4b | ✅ — inclusion + garde-fou 25 % ; exposition estimée par calcul analytique sur la dynamique historique gelée (§9) |
| Sensibilité OCV définie sans résultat P4b | ✅ — exécution systématique, variantes exactes, effet en dégradation seule (§13) |
| Règle de frontière définie sans résultat P4b | ✅ — §10/§12 entièrement déterministes sur labels Wilson |
| Aucun chiffre des 21 blocs P4a utilisé | ✅ — seules la structure méthodologique (Wilson, CRN, seeds, design) et les plages nuisance gelées avant P4a sont reprises |
| Aucun pilote exécuté | ✅ |
| Aucune simulation scientifique P4b exécutée | ✅ — seuls calculs analytiques et vérifications du code/scénario historique |

---

## 18. Verdict

**PREREGISTRATION STATUS: READY FOR FINAL FREEZE**

- aucune ambiguïté statistique ne subsiste : endpoint, classification,
  frontière et verdicts sont des fonctions déterministes des données ;
- aucun PENDING ne subsiste (les 10 points du mandat sont résolus) ;
- tous les calculs sont vérifiés (binomiale exacte ; trois passes
  d'audit — `P4B_PREREGISTRATION_AUDIT_v0.1.md` et
  `P4B_PREREGISTRATION_FINAL_AUDIT_v0.2.md`) ;
- le protocole couvre les résultats positifs, négatifs et inconclusifs
  (V0–V7 exhaustifs) ;
- aucune simulation P4b n'a été exécutée.

Deux analystes indépendants appliquant ce document aux mêmes résultats
arrivent nécessairement au même verdict.

---

**STOP.** Ce préenregistrement n'autorise ni le lancement de la campagne, ni
l'écriture du code P4b, ni aucun pilote, Monte-Carlo ou run exploratoire. Il
doit d'abord être relu et approuvé séparément ; seule une validation
explicite suivie du gel (commit) autorise l'implémentation puis l'exécution.
