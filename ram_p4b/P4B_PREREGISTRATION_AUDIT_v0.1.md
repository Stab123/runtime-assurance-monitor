# P4b — AUDIT DE SECONDE PASSE DU PRÉENREGISTREMENT v0.1 — RAPPORT

**Date : 2026-09-11. Objet : `P4B_PREREGISTRATION_v0.1.md`. Posture :
relecteur externe, indépendante de la rédaction. Méthode : relecture
intégrale du document, re-vérification de chaque équation, probabilité,
intervalle de confiance, seuil, graine, référence croisée, définition,
règle de décision et cas limite, conformément à la section 10 du mandat.
Aucune simulation P4b, aucun pilote, aucun Monte-Carlo n'a été exécuté
pour cet audit (calculs binomiaux exacts et vérifications de cohérence
uniquement).**

Références contrôlées : `P4B_PHASE0_PHYSICAL_BASIS_v0.6.md` (gelée) ;
`config_p4a.json` ; `ram_p4/graines_p4.py` ; `ram_p4/generer_design.py` ;
`ram_p4/campagne_p4a.py` ; `config_p4b_design.json` ; tables physiques
`data/*.csv`.

---

## 1. Anomalies trouvées et corrigées

| ID | EMPLACEMENT | PROBLÈME | GRAVITÉ | CORRECTION | PREUVE | STATUT |
|---|---|---|---|---|---|---|
| B-01 | §5 (contrôle d'erreur) | Renvoi « §11 » pour la multiplicité ; la section multiplicité est §15 | EDITORIAL | Renvoi corrigé en « §15 » | §15 = « Multiplicité et intervalles » | CORRIGÉ |
| B-02 | §4 (drapeau hors domaine) | Renvoi « §12 » pour la règle d'inclusion ; la règle est §9 | EDITORIAL | Renvoi corrigé en « §9 » | §9 = « SoC hors [0;1] — traitement statistique » | CORRIGÉ |
| B-03 | §12, cas V5 | Parenthétique initiale « (et non V1, donc ρ = 2.000 ∈ M) » fausse dans le cas général (si ρ = 2.000 ∈ S avec des niveaux M intermédiaires, V5 s'applique sans que ρ = 2.000 ∈ M) | MAJOR | Condition généralisée : « S ≠ ∅ ∧ I = ∅ ∧ non V1 », sans assertion sur le label de ρ = 2.000 ; l'interprétation couvre tous les sous-cas | §12, ligne V5 ; partition §12 « Exhaustivité » | CORRIGÉ |
| B-04 | §8 / §14 (labels de graines) | Contradiction interne : un label « DTCTRL » dédié au contrôle dt était annoncé, alors que la convention P4a gelée (`dt_controle_s`) réutilise les mêmes graines NOISE (seul dt change) ; un label dédié aurait brisé l'appariement du contrôle | MAJOR | Label DTCTRL supprimé ; le contrôle dt réutilise les graines NOISE du bloc, convention P4a-dtctrl explicitée ; labels autorisés = PLANT, NOISE uniquement | `ram_p4/campagne_p4a.py` (contrôle dt P4a, mêmes graines) ; §8 « Labels autorisés » ; §14 contrôle 2 | CORRIGÉ |
| B-05 | §7 (conséquence structurelle) | Formulation initiale « la trajectoire SoC ne dépend ni de ρ ni du bruit » fausse : les décisions de repli du moniteur dépendent du SoC mesuré, donc du bruit | MAJOR | Reformulation conditionnelle exacte : SoC ne dépend pas de ρ ; sous CRN la graine de bruit est commune aux 9 niveaux d'un bloc → séquence de bruit, replis et trajectoire SoC identiques aux 9 niveaux | §7 « Conséquence structurelle » ; moniteur B (seuil SoC bruité, `ram_p0/demo_eps.py`) | CORRIGÉ |
| B-06 | §9 (analyse bornée) | Renvoi « §13.4 » inexistant | EDITORIAL | Renvoi corrigé en « règle symétrique du §13 » | §13 « Règle symétrique pour les drapeaux » | CORRIGÉ |
| B-07 | §12, cas V0 | Portée ambiguë : l'invalidation technique semblait couvrir aussi les campagnes de sensibilité/contrôle, ce qui aurait invalidé le verdict principal pour une anomalie dans une analyse secondaire | MINOR | Portée précisée : V0 vise la campagne principale ; un run invalide en sensibilité/contrôle invalide cette analyse-là (annotation), pas le verdict principal | §12, ligne V0 | CORRIGÉ |
| B-08 | §6 (« minimum exact 3204 ») | Affirmation de minimalité à vérifier | — (vérification) | Aucune correction : balayage entier exhaustif N ∈ [2500 ; 3500] ; premier N avec R1 ≥ 0.90 = 3204 ; plus petit multiple de 500 = 3500 | Re-calcul binomial exact, audit §3.4 ci-dessous | VÉRIFIÉ CONFORME |
| B-09 | §4 (endpoint) | Précision d'évaluation de V_pack(t_k) non écrite dans la définition de l'endpoint (risque d'interprétation divergente : courant appliqué vs demandé, initialisation Vp) | MINOR | Paragraphe « Précision d'évaluation » déplacé dans §4 : V_pack évalué sur (SoC(t_k), Vp(t_k)) avec I_cell du courant effectivement appliqué (repli inclus), Vp(t0) selon v0.6 §7.2-E, rien entre les pas | §4, bloc après la définition de Y_j | CORRIGÉ |
| B-10 | §10 (annotation résolution) | Incohérence de formulation : « plus de deux pas » vs seuil « > 0.250 » (deux pas = 0.250 exactement) | MINOR | Formulation alignée : « au moins trois pas de grille, i.e. au moins deux niveaux M dans l'intervalle », seuil min(I) − max(S) > 0.250 | §10 « Annotation résolution » ; §12 V4 | CORRIGÉ |
| B-11 | §1 (hypothèses) | Renvois « §10 » (critère TRANSITION DETECTED) et « §12 » (contrôles) erronés : les cibles sont §12 (V4) et §14 | EDITORIAL | Renvois corrigés en « §12 (V4) » et « §14 » | §1, puces H_P4b-frontière / H_P4b-mécanisme | CORRIGÉ |

**Comptes : 0 CRITICAL, 2 MAJOR (B-03, B-04), 3 MINOR (B-07, B-09, B-10),
4 EDITORIAL (B-01, B-02, B-06, B-11), 1 vérification conforme (B-08).
Toutes les anomalies sont corrigées dans la v0.1 livrée ; aucune ne
subsiste.**

---

## 2. Anomalies recherchées et non trouvées (négatifs d'audit)

- Aucune modification, même indirecte, de la base physique v0.6, du
  scénario P2.3, de la plante historique, ni des paramètres B/τ_arm/garde.
- Aucune utilisation des résultats des 21 blocs défaillants P4a (reprises
  limitées à la structure méthodologique et aux plages gelées avant P4a).
- Aucun choix calé sur un résultat : grille uniforme sans prior, seuils
  hérités, N dimensionné sur propriétés binomiales, seuil de drapeau 25 %
  justifié par lisibilité du modèle (marge ≈ 4× sur l'exposition estimée
  analytiquement ≈ 6 %, estimation faite avant le choix du seuil).
- Aucune voie vers TRANSITION DETECTED autre que V4 ; aucune analyse de
  sensibilité ne peut améliorer un verdict (dégradation seule, §13).
- Aucun PENDING résidu : les 10 points du mandat sont traités (§3 à §14).
- Aucun trou dans la règle de décision : partition de l'espace
  (S, I) × (vides/non vides) × (ordonnés/inversés) démontrée au §12
  (« Exhaustivité ») ; les cas A–J du mandat sont tous mappés.

---

## 3. Re-vérifications numériques (calculs exacts refaits)

### 3.1 Seuils de classification (Wilson bilatéral 95 %, z = 1.959963985130054, N = 3500)

| x | IC95 re-calculé | Attendu au §6 | Conforme |
|---|---|---|---|
| 0 | [0.000000 ; 0.001096] | [0 ; 0.0011] | ✅ |
| 23 | [0.004383 ; 0.009842] | [0.0044 ; 0.0098] ≤ 0.01 | ✅ |
| 24 | [0.004612 ; 0.010183] | [0.0046 ; 0.0102] > 0.01 | ✅ |
| 200 | [0.049927 ; 0.065329] | [0.0499 ; 0.0653], borne inf < 0.05 | ✅ |
| 201 | [0.050195 ; 0.065633] | [0.0502 ; 0.0656], borne inf ≥ 0.05 | ✅ |

Seuils entiers confirmés : SUFFICIENT ⟺ x ≤ 23 ; INSUFFICIENT ⟺ x ≥ 201.
Cas 0/N : borne de Clopper-Pearson unilatérale 95 % re-calculée =
0.000856 ≈ 0.00086 ✅ (« zéro violation ne signifie jamais p = 0 »).

### 3.2 Exigences de puissance

- R1 = P(X ≤ 23 | Bin(3500, 0.005)) = **0.9198** ≥ 0.90 ✅ (§6 annonce 0.920)
- R2 = P(X ≥ 201 | Bin(3500, 0.10)) = **1.0000** ≥ 0.90 ✅
- Minimalité : balayage entier N ∈ [2500 ; 3500] → premier N avec
  R1 ≥ 0.90 = **3204** ✅ ; plus petit multiple de 500 = **3500** ✅
- Précision absolue : demi-largeurs re-calculées 0.0166 (p̂ = 0.5) et
  0.0072 (p̂ = 0.05) ✅

### 3.3 Table OC du §16 (P(SUFFICIENT)/P(INTERMEDIATE)/P(INSUFFICIENT))

Re-calculée ligne par ligne aux 10 valeurs de p (0 ; 0.0025 ; 0.005 ;
0.01 ; 0.02 ; 0.03 ; 0.05 ; 0.075 ; 0.10 ; 0.20) : **toutes les cellules
conformes à 0.001 près**, y compris P(M | p = εS) = 0.980 et
P(M | p = εF) = 0.974 (règle conservative aux seuils, comme annoncé).

### 3.4 Puissance campagne du §16 (indépendance, conservative)

Re-calculée avec la condition V4 exacte (≥ 1 niveau S, ≥ 1 niveau I,
sans inversion) : transition 1.500/1.625 → ≈ 1.000 ✅ ; transition
1.000/1.125 → 0.9908 ≈ 0.991 ✅ ; p = 0.004 partout → P(V1) = 0.920 ✅ ;
p = 0.15 dès ρ = 1.000 → P(V2) = 1.000 ✅.

### 3.5 Empreintes et design

- `config_p4b_design.json` : SHA256
  `4439351a58d82dd1851568bd14e13854871e75ab75711e02563c2514f0208250` ✅
  (conforme §7/§8/§14) ; contenu relu : 3 500 points, 602 rejets
  documentés (taux 602/4102 = 14.68 % ✅), règle de dérivation, version
  de campagne, plages et ordre de tirage conformes au §7.
- Tables physiques : SHA256
  `7aa959fc…7154c2` (OCV HNEI) et `330efcd3…697b93` (Rint DTU) ✅
  (conformes §2, identiques aux valeurs gelées v0.6).
- Comptes annexes : 205/3500 = 5.857 % ✅ (§9 annonce 205 points,
  5.9 %) ; 9 × 3500 = 31 500 runs ✅ ; grille 9 niveaux pas 0.125 ✅ ;
  2 700 pas par run (k = 0..2699, dt = 5.0 s) ✅.

### 3.6 Dérivation des graines

Règle §8 re-lue contre `ram_p4/graines_p4.py` : même mécanisme
(SHA256 des 8 premiers octets hex, big-endian, mod 2³¹), nouvelle
version de campagne « P4b-structural-v1 », commit v1.4.1 et DOI dans la
chaîne ✅. Labels limités à PLANT/NOISE ✅ ; séparation nuisance/bruit ✅ ;
aucune graine P2/P3/P4a réutilisée ✅.

---

## 4. Test de déterminisme inter-analystes (critère READY du mandat)

Simulation de table sur cas jouets (labels S/I/M fictifs) : pour chaque
combinaison testée — tout S ; ρ = 1.000 ∈ I ; inversion I puis S ;
S et I ordonnés avec ou sans M ; S seuls ; I seuls (ρ = 1.000 ∈ M) ;
tout M — la table V0–V7 rend un verdict unique et identique quel que soit
l'ordre de lecture. Les trois déclencheurs d'invalidation (technique,
hors-domaine > 25 %, divergence de re-run) sont des conditions
observables sans jugement. La sensibilité OCV et la règle symétrique
drapeaux sont en dégradation seule et déterministes. **Deux analystes
indépendants appliquant le document aux mêmes résultats arrivent
nécessairement au même verdict.**

---

## 5. Verdict d'audit

**AUDIT STATUS: PASSED — 0 anomalie résiduelle.** Les 11 constats de la
seconde passe (2 MAJOR, 3 MINOR, 4 EDITORIAL, 1 vérification, 0 CRITICAL)
sont corrigés dans la v0.1 livrée ; tous les calculs critiques sont
re-vérifiés conformes. Le document `P4B_PREREGISTRATION_v0.1.md` satisfait
les 13 sections du mandat, sans PENDING résiduel.

**STOP.** Cet audit n'autorise ni le lancement de la campagne, ni
l'écriture du code P4b, ni aucun pilote, Monte-Carlo ou run exploratoire.
Le préenregistrement doit d'abord être relu et approuvé séparément ;
seule une validation explicite suivie du gel (commit) autorise
l'implémentation puis l'exécution.
