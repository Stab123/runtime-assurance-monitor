# PRÉENREGISTREMENT P4a — Frontière de suffisance de l'enveloppe B

**Version 1.0 — antérieur à toute donnée P4a.**
Baseline : v1.4.1 (commit `2d4ce6a2cecc52778a2f5ebf649e2a128c6a8138`,
DOI `10.5281/zenodo.22681860`), intégralement gelée. Ce document, la
configuration, le design et le code de `ram_p4/` sont figés au commit de gel,
**avant toute exécution confirmatoire**.

## 1. Question et hypothèses

- **H_P4-frontière** : dans D_physique, p_μ(b) présente une transition monotone
  et localisable entre une région S et une région F.
- **H_P4-mécanisme** : si cette transition existe, sa localisation est
  compatible avec l'épuisement de la marge SoC par une erreur d'estimation
  persistante, et non avec un artefact numérique.

Les deux hypothèses sont verdictées **séparément**. Signatures préenregistrées
du mécanisme : (i) erreur d'estimation réalisée ≈ b ; (ii) marge minimale vraie
décroissante en b ; (iii) intervention du moniteur retardée à paramètres
identiques (blocs CRN) ; (iv) insensibilité au DT.

## 2. Estimand primaire

Y = 1 si SoC_vrai(t) < 0.35 à au moins un cycle du run, 0 sinon (seuil brut,
niveau run, cycles non poolés). p_μ(b) = P_μD(Y=1 | b).

## 3. Mesure expérimentale μ_D

μ_D = mesure uniforme sur K = 500 points θ_j = (C_BATT, I_SUN, I_BASE, soc0),
tirés uniformément sur C_BATT ∈ [4.4 ; 14.4] Ah, I_SUN ∈ [0.8 ; 2.5] A,
I_BASE ∈ [0.06 ; 0.75] A, soc0 ∈ [0.40 ; 0.70], conditionnés aux règles
d'admissibilité (§4), générés une fois (seed PLANT, flux unique, ordre de
tirage fixe C_BATT → I_SUN → I_BASE → soc0 avec rejet-continuation) et figés en
clair dans `config_p4a.json` (régénérables par `generer_design.py`).

> « Uniform » est une mesure de couverture expérimentale, pas une hypothèse
> selon laquelle les satellites réels sont uniformément distribués.

p_μ(b) n'est ni une probabilité réelle de défaillance d'un CubeSat, ni une
fréquence de flotte, ni une probabilité de mission : c'est la probabilité de
violation **dans le modèle P4a sous la mesure expérimentale μ_D**. Cette
limitation sera reproduite dans toute publication P4.

## 4. Admissibilité (avant génération, indépendante de tout résultat)

- R1 : I_SUN ≥ 1.5·I_BASE (bilan de charge de base, modèle simplifié hors
  payload ; impliquée par R2).
- **R2 : 3600·I_SUN ≥ 5400·I_BASE + 0.5·(3·900)**, soit
  **I_SUN ≥ 1.5·I_BASE + 0.375 A**. Dérivation : charge nette disponible par
  orbite = 3600·I_SUN (apport pendant les 3600 s de lumière) − 5400·I_BASE
  (charge de base sur l'orbite complète) ; viabilité mission minimale =
  couverture de 50 % du service payload nominal (3 A × 900 s) ; donc
  3600·I_SUN − 5400·I_BASE ≥ 1350 C.
- R3 : soc0 ≥ 0.39 (automatiquement satisfaite par la plage).

Ces règles caractérisent le scénario physique admissible ; elles ne dépendent
ni du résultat de B, ni d'une violation observée, ni du slack historique, ni
du comportement futur du moniteur. Points rejetés avant simulation, jamais
après observation.

## 5. Facteur et niveaux (grille fixe)

b = biais SoC persistant signé. **Convention : b > 0 = l'estimation surestime
le SoC vrai ; b < 0 = sous-estimation.**
Niveaux : {−0.10 ; −0.05 ; −0.02 ; −0.01 ; 0 ; +0.01 ; +0.02 ; +0.05 ; +0.10}.
Ancres : 0 = contrôle nul ; 0.01 = borne estimateur haute qualité (< 1 %,
classe EKF) ; 0.02 / 0.05 = bornes du coulomb counting typique (2–5 %) ;
0.10 = pire cas dégradé documenté. Grille totalement fixe : aucun raffinement
adaptatif. Les deux signes sont obligatoirement représentés.

## 6. Injection exacte

PLANTE → MESURE z = x_vrai + ν (iid, échelle équivalente instrumentale :
σ_SoC = 1e-7 par mesure, borne haute de la quantification INA219 convertie en
SoC/cycle) → **BIAIS : z′ = (z_SoC + b, z_temp)** → ESTIMATEUR (algorithme
figé, non modifié) → MONITEUR (enveloppe seule : k_sigma = 0, seuil
d'incertitude infini). b constant pendant tout le run, actif dès t = 0, unité
SoC, saturation [0 ; 1] sur z′_SoC (comptée par run ; quasi-inerte dans
D_physique). Canal température non affecté. Implémentation : le biais étant
additif, il commute avec le bruit ; passer x_mes = (clamp(x_vrai[0] + b),
x_vrai[1]) à l'estimateur figé produit exactement z′ = z + b. Alternatives
(biais sur l'état de l'estimateur, biais sur la capacité estimée) :
extensions P4a.2, hors P4a.

## 7. Facteurs fixes

τ_arm = 120 s ; garde SoC = 0.02 (configuration de référence historique du
baseline, vérifiée dans `ram_p2/config_p2_3.json` : `delai_armement_s = 120.0`,
`marge_securite_soc = 0.02`). Scénario : orbite 5400 s (3600 s lumière /
1800 s éclipse), payload 3 A sur [600 ; 1500] s, durée 13500 s, DT = 5 s
(campagne principale). Le code P4 lit `dt_s` effectivement (le défaut
historique #8 de `ram_p2` n'est pas hérité).

## 8. Seuils de classification statistique P4a

εS = 0.01 ; εF = 0.05. **Ce sont des seuils de classification de cette étude,
pas des exigences de sûreté spatiale.** Justifications : εS = résolution
certifiable par le budget (0/500 → borne Wilson sup = 0.0076 < 0.01) ; εF =
taux au-delà duquel la défaillance est établie avec puissance ≥ 0.99 à
p = 0.10 (≥ 0.82 à p = 0.08).

- **S** : borne sup Wilson 95 % de p̂ < εS
- **F** : borne inf Wilson 95 % de p̂ > εF
- **T** : intermédiaire

## 9. Dimensionnement

N = 500 runs/niveau × 9 niveaux = **4500** (voir `analysis_plan_p4a.md` :
Wilson, puissances, simulation Bernoulli à hypothèses déclarées). Extensions
préenregistrées : +1800 runs RESEED (blocs 0–199, 9 niveaux, famille RESEED) ;
+400 runs DTCTRL (niveaux +0.02/+0.05, blocs 0–199, DT = 2.5 s).
**N total maximal = 6700.** Aucun ajustement après observation.

## 10. CRN

Mêmes θ_j et même graine de bruit (seed NOISE, j) pour les 9 niveaux d'un bloc.
Témoin par run : SHA-256(paramètres, graine bruit) + bruit pur au cycle 1000
(indépendant de l'état, donc du biais). Vérification automatique de l'égalité
des témoins entre niveaux d'un même bloc.

## 11. Analyse

- **IC** : Wilson 95 % bilatéral, z = 1.959963985130054 ; cas zéro événement :
  U = z²/(N+z²).
- **Tendance** : régression logistique p ~ b sur les niveaux ≥ 0, erreurs
  standards cluster-robust par bloc de nuisance, test unilatéral β > 0,
  α = 0.05. L'ajustement isotonique est descriptif ; la monotonie n'est pas
  « prouvée » par le modèle qui l'impose (diagnostic : comptage d'inversions).
- **Frontière** : l'ajustement isotonique (PAVA, non décroissant) porte sur les
  niveaux {0 ; +0.01 ; +0.02 ; +0.05 ; +0.10}.
  **b\* = plus petite valeur positive b telle que p_iso(b) ≥ εF**, avec cas
  exhaustifs : interpolation linéaire uniquement si
  p_iso(b_i) < εF < p_iso(b_{i+1}) ; égalité ou plateau couvrant εF : bord
  gauche du plateau ; p_iso(+0.01) ≥ εF : b\* rapporté « ≤ 0.01 » (censuré à
  gauche, aucune interpolation entre 0 et +0.01) ; aucun niveau ≥ εF : b\*
  indéfini (voies B/D).
- **IC de b\*** : bootstrap 2000 répliques **par blocs de nuisance** (bloc =
  les exécutions d'un θ_j à tous les niveaux ; jamais de bootstrap niveau par
  niveau), mêmes règles de plateau à chaque réplique ; largeur calculée sur les
  répliques où b\* est défini (proportion rapportée). **Largeur maximale
  acceptée : 0.02** ; dépassement → INCONCLUSIF sur la localisation.

## 12. Conclusions globales (automatiques)

- **A — FRONTIÈRE SUPPORTÉE** : ≥ 1 S, ≥ 1 F, tendance significative, b\*
  localisé, IC(b\*) ≤ 0.02, RESEED concordant, contrôle DT concordant.
- **B — FRONTIÈRE NON TROUVÉE DANS D** : aucune région F, précision suffisante.
  Formulation imposée : « aucune frontière n'a été identifiée dans le domaine
  confirmatoire testé à la résolution statistique préenregistrée ».
  Jamais « B est sûr ».
- **C — H_P4-FRONTIÈRE FALSIFIÉE** : violations sans transition
  reproductible/monotone.
- **D — INCONCLUSIF** : puissance/précision/reproductibilité insuffisante.
- **E — MODÈLE INSUFFISANT** : dépendance au DT, artefact d'implémentation ou
  mécanisme non représenté compromettant l'interprétation physique.

## 13. Seeds

seed(label, i) = int(SHA256("P4a-confirmatory-v1 |
2d4ce6a2cecc52778a2f5ebf649e2a128c6a8138 | 10.5281/zenodo.22681860 | label | i")
[0:8], big-endian) mod 2³¹ — implémentée dans `graines_p4.py`. Labels : PLANT,
NOISE, BOOTSTRAP, RESEED, DTCTRL, PILOT. Aucune seed historique P2/P3.

## 14. Exclusions

Crash logiciel ; corruption de fichier ; invariant numérique (NaN dans une
métrique, paramètre hors bornes physiques [−0.5 ; 1.5]) ; rejet d'admissibilité
pré-simulation. Log d'audit conservé pour tout run exclu. Jamais : run extrême,
résultat surprenant, violation trop précoce, valeur gênante, « outlier » défini
après résultat.

## 15. Données brutes par run

run_id, mode, biais, bloc_id, paramètres plante, graine bruit, témoins,
Y, cycles de violation, temps de première violation, marge min, replis,
livraison, erreur d'estimation (moyenne/max), n_saturation, durée de calcul,
métadonnées de campagne (hashes code/config, commit, timestamp). Jamais
remplacées silencieusement.

## 16. Contrôles

- **Contrôle b = 0** : référence scientifique sans biais injecté. **Aucune
  classe S/T/F n'est attendue a priori** : la compréhension préalable peut être
  fausse et sa classification est un résultat scientifique à part entière. Seul
  l'échec d'un invariant logiciel préenregistré peut invalider ce contrôle.
- **RESEED** (200 blocs × 9 niveaux) : **test de direction/effet adapté à la
  puissance de N = 200 — jamais une réplication des classes S/T/F** (0/200 →
  borne Wilson sup = 0.0188 > εS, une réplication S est impossible). (a)
  Homogénéité par niveau : test z bilatéral de deux proportions (principal
  n = 500 vs RESEED n = 200, variance poolée), Bonferroni α = 0.05/9 ;
  discordance significative = reproductibilité non démontrée pour ce niveau.
  (b) Direction : le signe de la pente logistique RESEED (niveaux ≥ 0) doit
  concorder avec le principal ; la significativité RESEED est rapportée, non
  exigée. Verdict : discordance en (a) sur un niveau déterminant pour la
  conclusion globale (tout niveau F ; tout niveau si la conclusion est B), ou
  violation de (b) → conclusion globale D (cause rapportée). Cette règle
  n'invalide aucune donnée : elle classe la force de la conclusion.
- **DTCTRL** : niveaux +0.02/+0.05 × 200 blocs à DT = 2.5 s ; flip de
  classification → issue E candidate.
- **Pilote exploratoire** (≤ 100 runs, b ∈ {0 ; +0.10}, seeds PILOT) :
  vérifications automatiques de plomberie uniquement (complétion, témoins CRN,
  hashes), résultats en quarantaine, jamais intégrés ni analysés pour la
  décision.

## 17. Endpoints secondaires (diagnostiques, non décisionnels)

Marge minimale vraie par run ; replis/run ; livraison/run ; temps de première
violation ; erreur d'estimation réalisée. Ils ne remplacent jamais Y.

## 18. Exclusions de périmètre

Dérive, bruit corrélé, gel/drop-out : P4a.2 / exploratoire. Thermique, C/D,
k_sigma : hors P4a. Conclusions limitées à la classe 6U–12U LEO du système de
référence (Phase 2). Le slack historique (0.0066–0.02) ne sert qu'à formuler
H_P4-mécanisme et à la comparaison a posteriori — jamais aux niveaux, à la
grille, à εS/εF, à N, ni à la sélection des données.

## 19. Arrêt

Exécution complète des 6700 runs maximum, puis analyse préenregistrée.
**Aucun ajout de runs après observation** : toute extension = nouvelle
préinscription.
