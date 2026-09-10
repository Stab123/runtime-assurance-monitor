# P4b — PHASE 0 : RAPPORT D'AUDIT FINAL EXHAUSTIF (v0.6)

**Date : 2026-09-11. Objet audité : `P4B_PHASE0_PHYSICAL_BASIS.md` v0.5
(822 lignes), relu intégralement ligne par ligne en posture de relecteur
externe. Livrable de correction : `P4B_PHASE0_PHYSICAL_BASIS_v0.6.md`
(version consolidée autonome). Aucune simulation, aucun chiffre P4a utilisé.**

## Méthode d'audit (couverture)

- **A. Cohérence globale** : statuts (PROPOSÉ/VALIDÉ/GELÉ/PENDING), renvois
  croisés, changelog vs partie normative.
- **B. Correctifs connus** : PENDING résiduels, valeurs τ obsolètes, wording
  CSV, statut V_min, titre §7.2.
- **C. Audit mathématique Thevenin** : signe du courant vs signe instantané
  de Vp, forme signée unique.
- **D. Audit de l'affirmation « pas de sous-tension en charge »**.
- **E. Audit Vp(t0)** : rigueur de la borne d'initialisation.
- **F. Pack équivalent** : exactitude du partage de courant.
- **G. SoC ∉ [0 ; 1]** : règle pré-data.
- **H. §6.4** : statut d'illustration, obligation de sensibilité OCV.
- **I. Extension > 90 %** : portée exacte de la citation DTU.
- **J. Wording ρ** : jamais « facteur réel de vieillissement », plage
  visuelle étiquetée.
- **K. Audit numérique complet des CSV** : recalcul de τ_ref min/max,
  τ_ρ,max(ρ=2), rtot, écarts médiane/p35, et comparaison systématique avec
  chaque valeur du Markdown (aucune valeur tapée de mémoire).
- **L. Recalcul §6.4** depuis les tables corrigées.
- **M. Hiérarchie des sources**.
- **N. ECSS** : vérification verbatim, absence de seuil numérique.
- **O. Exclusions** : validité des justifications.
- **P. Absolus de causalité** (« ne peut pas », « garantit », « exact »,
  « toujours », « jamais ») : scoping.
- **Q. Table anti-post-hoc** : mise à jour aux valeurs v0.5/v0.6.
- **R. Table finale des paramètres** : §7.6 de la v0.6.
- **T. Passe grep finale** : chaînes obsolètes (résultat en fin de rapport).

## Table des constats

Gravité : CRITICAL (contradiction normative directe ou valeur obsolète dans
une section normative) ; MAJOR (erreur factuelle ou affirmation non étayée à
corriger avant gel) ; MINOR (imprécision sans impact matériel) ; EDITORIAL.

| ID | EMPLACEMENT (v0.5) | PROBLÈME | GRAVITÉ | CORRECTION | PREUVE | STATUT |
|---|---|---|---|---|---|---|
| A-01 | §5, l.336 | « Règle d'initialisation Vp(t0) et convention de charge : PENDING (§7.2-E) » contredit le gel v0.5 | CRITICAL | Remplacé par « gelées (§7.2-E) » | §7.2-E titré « règles GELÉES (v0.5) » ; §11.1 | CORRIGÉ v0.6 |
| A-02 | §7.2-B, l.507–511 | τ « 51–294 s », τ/900 « [0.06 ; 0.32] », « 95.4–100 % », « 65–190 mV » : valeurs v0.3 obsolètes en section normative, contredisant §6.2 corrigé | CRITICAL | 86–338 s ; [0.10 ; 0.38] ; 93.0–100 % (ρ=1), 73.6–99.5 % (ρ=2) ; ≈ 90–299 mV (ρ=2, I_cell=2.25 A) | Recalcul depuis `data/rint_soc_nmc_dtu.csv` : τ = Rp·Cp ∈ [86.0 ; 338.4] s ; 1−e^(−900/86) = 0.99997, 1−e^(−900/338.4) = 0.930 ; I_cell·ρ·Rp ∈ [89.9 ; 299.2] mV | CORRIGÉ v0.6 |
| A-03 | §7.2-E, l.647–650 | « I_batt > 0 → Vp > 0 » et « I_batt < 0 → Vp < 0 » énoncés comme implications instantanées : faux, Vp est un état à mémoire ; réécriture automatique V = OCV + \|I\|ρRs + \|Vp\| | MAJOR | Forme signée unique V = OCV − I_cell·ρ·Rs − Vp ; distinction signe du courant / signe d'asymptote / Vp instantané | EDO dVp/dt : Vp(t) dépend de l'historique ; après une charge, Vp < 0 persiste en début de décharge | CORRIGÉ v0.6 |
| A-04 | §7.2-E, l.657–659 | « V < V_min ne peut pas se déclencher en charge » : absolu physique non garanti (mémoire de Vp ; cellule très déchargée entrant en charge) | MAJOR | Absolu retiré ; endpoint évalué sur toutes les phases ; remarque de marge numérique déclarée comme propriété du modèle, pas théorème | Contre-exemple de principe : Vp > 0 hérité d'une décharge se relaxe en ≈ τ ≤ 677 s après le début de la charge | CORRIGÉ v0.6 |
| A-05 | §6.4, l.379–391 | Courant du cas défavorable 3.5 A erroné : la fenêtre payload [600 ; 1500] s est en lumière (i_charge = I_SUN ≥ 0.8) → I_batt,max = 0.75 + 3.0 − 0.8 = 2.95 A ; I_cell = 2.25 A (0.67 C), pas 2.66 A (0.80 C) | MAJOR | Tableau §6.4 entier recalculé à I_cell = 2.246 A | `ram_p0/demo_eps.py` : `en_lumiere = (t % 5400) < 3600` ; `config_p4a.json` : `fenetre_payload = [600.0, 1500.0]`, `u_payload = 3.0` | CORRIGÉ v0.6 |
| A-06 | §7.2-B, l.538 | « écart p35/médiane ≤ 0.7 mΩ (Rs) » faux : écart max mesuré 2.0 mΩ (SOC = 100 %) | MAJOR | ≤ 2.0 mΩ (Rs), ≤ 2.2 mΩ (Rp), ≤ 0.6 kF (Cp) ; conclusion inchangée (≤ incertitude de numérisation ±3 mΩ / ±1.0 kF) | Recalcul CSV : max\|Rs_med − Rs_p35\| = 2.0 mΩ | CORRIGÉ v0.6 |
| A-07 | §6.3, l.364 | Plages « Rp 12–68 mΩ, Cp 3.8–15.1 kF » obsolètes (antérieures à la correction v0.5) | MAJOR | Rp 19–67 mΩ, Cp 3.6–14.1 kF (p35/médiane) | CSV corrigé : Rp p35 20.0–66.6 / médiane 19.1–65.8 ; Cp p35 3.9–14.1 / médiane 3.6–13.5 | CORRIGÉ v0.6 |
| A-08 | §10, l.754 | « τ/900 ∈ [0.06 ; 0.32] » obsolète dans la table anti-post-hoc | MAJOR | [0.10 ; 0.38] | Recalcul CSV : 86.0/900 = 0.096 ; 338.4/900 = 0.376 | CORRIGÉ v0.6 |
| A-09 | §2 P6 (l.157), §4 (l.277), §9 (l.735) | Justification du taper CC/CV « hors zone opérée (SoC ≤ 0.70) » invalide : soc0 est une condition initiale ; soc(t) peut dépasser 0.70 (voire 1) en lumière | MAJOR | Exclusion re-justifiée : chargeur à courant constant du code gelé ; effet déclaré non modélisé, sans borne d'effet revendiquée | Plante gelée : dsoc > 0 en lumière ; soc non saturé (S6) ; recharge nette ≤ ≈ +0.38/orbite au coin I_SUN = 2.5, C_BATT = 4.4 | CORRIGÉ v0.6 |
| A-10 | §1.1 S6, l.132 | « surcharge possible (hors champ du scénario) » faux : soc peut dépasser 1 dans le scénario | MAJOR | Corrigé ; renvoi à la règle hors-domaine (§7.2-A) | Calcul : (2.5−0.06)·2700/3600/4.4 − 0.56·900/3600/4.4 − 0.06·1800/3600/4.4 ≈ +0.38/orbite depuis soc0 ≤ 0.70 | CORRIGÉ v0.6 |
| A-11 | §3, sources 4 et 13 | Source 4 (cubesatnano.ru, agrégateur) classée A ; source 13 (revue MDPI Energies 2025) classée A | MAJOR | 4 → C (héritage architectural uniquement, jamais de valeurs numériques) ; 13 → B | Hiérarchie déclarée §3 : A = constructeur/agence/standard ; B = revue à comité de lecture ; C = technique secondaire | CORRIGÉ v0.6 |
| A-12 | §7.2-B l.544–549 ; §11.1 ; CSV rint | La citation DTU « Rp is stable for SOC above 25 % » présentée comme justifiant le clamp Rp **et** Cp : elle ne couvre que Rp | MAJOR | Justifications séparées : Rp = sourcé ; Cp = règle méthodologique de clôture de frontière, non tirée de la source | Texte de la citation (Rp uniquement) | CORRIGÉ v0.6 (doc + CSV) |
| A-13 | §7.2-B, l.515 | « l'évolution de Cp avec l'âge est documentée comme secondaire (set B DTU) » non étayé : le set B n'a pas pu être tabulé | MAJOR | Reformulé : choix expérimental pré-data déclaré ; effet de second ordre borné (τ ∈ [0.10 ; 0.75]×900 s sur ρ ∈ [1 ; 2]) | §7.2-B lui-même : « Set B : non tabulé » | CORRIGÉ v0.6 |
| A-14 | §6.4, l.396–410 | Localisations du franchissement (« SoC ≲ 1–2 % », « 0–3 % ») insuffisamment étiquetées comme illustration analytique | MAJOR | Section étiquetée ILLUSTRATION ANALYTIQUE PRÉ-DATA — PAS UN RÉSULTAT P4b ; valeurs recalculées (SoC ≲ 0.6 %) ; obligation de préenregistrer une analyse de sensibilité OCV (±0.1 V) si la frontière s'y situe — déclenchée | Recalcul : V_cell(900) < 2.5 V pour SoC ≲ 0.006 (I_cell = 2.25 A, ρ = 2, convention Vp(0)=0) | CORRIGÉ v0.6 + TRANSFÉRÉ (§11.2-10) |
| A-15 | §7.2-E, l.636–638 | « erreur d'initialisation ≤ ~2 mV » présentée comme borne : non rigoureuse, SoC donc Rp(SoC) évolue pendant l'éclipse pré-run | MAJOR | Ordre de grandeur sous hypothèse de paramètres localement constants ; Vp(t0) déclaré convention quasi-stationnaire pré-data, non reconstruction de l'historique | ΔSoC ≤ I_BASE·1800/(C_BATT·3600) ≈ 0.085 au pire coin | CORRIGÉ v0.6 |
| A-16 | §7.2-C, l.607–608 | « exact pour un nombre quelconque de branches identiques » : un nombre de branches est entier ; nP_eq ∈ [1.31 ; 4.30] est continu | MINOR | « modèle équivalent continu préservant exactement le taux-C » ; héritage COTS distingué du modèle équivalent | Définition nP_eq = C_BATT/C_cell | CORRIGÉ v0.6 |
| A-17 | §7.2-E, l.636 | « τ ≤ 676 s » et « 1800 s ≥ 2.7τ » : arrondis optimistes | MINOR | ≤ 677 s ; « ≈ 2.7τ » qualifié ; résidu e^(−1800/677) ≈ 7 % | Recalcul : 2×338.4 = 676.8 ; 1800/676.8 = 2.66 | CORRIGÉ v0.6 |
| A-18 | §7.1, l.446 vs 456 | « ρ ∈ [1.1 ; 1.9] documenté » vs « ρ ∈ [1.0 ; 1.9] couvert » : incohérence interne ; « documenté » trop fort pour une lecture visuelle | MINOR | [1.1 ; 1.9] étiqueté lecture visuelle en plage à SOH 90 % ; [1.0 ; 1.9] = couverture incluant le quasi-neuf ; jamais « facteur réel de vieillissement » | §7.2-B : « lecture honnête en plage… pas de pseudo-précision » | CORRIGÉ v0.6 |
| A-19 | §3, source 11, l.222 | « Hein démontre… rien au-delà » : absolu de portée | MINOR | « Hein mesure ≤ 1.37× dans son protocole ; rien au-delà n'en est extrapolé ici » | Protocole Hein limité à 174 cycles 1C/1C | CORRIGÉ v0.6 |
| A-20 | §7.2-E, l.634 | « le satellite n'est jamais relaxé en orbite » : absolu physique | MINOR | « dans le scénario gelé, le bus reste alimenté en permanence » | Scénario P2.3 gelé | CORRIGÉ v0.6 |
| A-21 | §7.2-C, l.611 | Héritage 2P–4P attribué aux « sources 4, 6 » : la source 6 (BP8) est un pack 8S, sans topologie 2P–4P documentée | MINOR | Source 4 uniquement | §3, sources 4 et 6 | CORRIGÉ v0.6 |
| A-22 | §7.2 (structure) | Élément E placé avant l'élément D | EDITORIAL | Ordre A, B, C, D, E rétabli | — | CORRIGÉ v0.6 |
| A-23 | CSV OCV, en-tête | « hors zone opérée » (même invalidité qu'A-09) | EDITORIAL | « zone hors condition initiale (soc0 ≥ 0.40) mais potentiellement atteignable dynamiquement » | — | CORRIGÉ v0.6 |
| A-24 | l.96 ; titre §7.2 ; table §7.2 l.688 ; §11.1 l.780 | Statuts incohérents : « PROPOSÉ — en attente d'audit », « PROPOSÉES — à valider à l'audit », V_min « PROPOSÉ » | MAJOR | Statuts unifiés : V_min GELÉ v0.6 ; plus aucun mélange PROPOSÉ/VALIDÉ/GELÉ/PENDING dans la partie normative ; table finale §7.6 | — | CORRIGÉ v0.6 |
| A-25 | Changelog v0.2–v0.4 | Anciennes valeurs (τ 51–294 s ; V_min « proposé » ; topologie nP discrète ; Vp(t0) « PENDING ») sans marquage | MINOR | Blocs marqués HISTORIQUE avec mentions SUPERSEDÉ / REMPLACÉ explicites | — | CORRIGÉ v0.6 |
| A-26 | §7.2-A (absence) | Aucune règle pré-data pour soc(t) ∉ [0 ; 1] alors que la plante ne sature pas soc (S6) | MAJOR | Règle gelée : clamp des tables + drapeau « hors domaine physique du modèle » ; traitement statistique transféré au préenregistrement | S6 + dynamique gelée | CORRIGÉ v0.6 + TRANSFÉRÉ (§11.2-9) |

## Points vérifiés conformes (sans constat)

- ECSS-E-ST-20C Rev.2 §5.7.3 exigences h et i citées verbatim ; aucune valeur
  numérique extraite ; l'ECSS n'est jamais présentée comme imposant 2.5 V.
- OCV : ré-extraction identique au CSV (écart max 0 mV) ; monotonie stricte ;
  extraits du texte conformes au CSV (0 % → 2.834 ; 10 % → 3.349 ;
  20 % → 3.476 ; 35 % ≈ 3.58 ; 50 % → 3.676 ; 70 % → 3.864 ;
  100 % → 4.179 V).
- `rint_soc_nmc_dtu.csv` : rtot_p35 = rs_p35 + rp_p35 exact sur les 10 lignes
  mesurées ; τ/900 ∈ [0.10 ; 0.38] du §6.2 conforme ; extraits Rs/Rp/Cp du
  §7.2-B conformes.
- Vp(t0) pire coin : 2 × 28.4 mΩ × 0.75 A × 3.35/4.4 = 32.4 mV, conforme à
  « ≈ 32 mV » ; résidu e^(−1800/677) = 7.0 %, conforme à « ≤ 7 % ».
- nP_eq ∈ [1.31 ; 4.30] conforme à C_BATT ∈ [4.4 ; 14.4] / 3.35.
- I_cell §6.4 v0.6 : 2.95 × 3.35/4.4 = 2.246 A = 0.67 C < 4.875 A (datasheet).
- Aucun usage des 21 blocs P4a ; aucune simulation P4b exécutée.

## Passe grep finale (section T) sur la v0.6

Chaînes recherchées dans `P4B_PHASE0_PHYSICAL_BASIS_v0.6.md` : « PENDING »
(uniquement statistiques §7.4/§7.5/§11.2), « 51 et 294 », « 0.06 ; 0.32 »,
« 95.4 », « 65–190 », « 12–68 », « 3.8–15.1 », « 0.7 mΩ », « hors zone
opérée », « 2.66 A », « 0.80 C », « 3.5 A », « ne peut pas se déclencher en
charge », « exact pour un nombre quelconque », « erreur d'initialisation ≤ »,
V_min « PROPOSÉ ». Résultat : **chaîne obsolète présente uniquement dans les
blocs HISTORIQUES explicitement marqués SUPERSEDÉ / REMPLACÉ, ou dans le
changelog v0.6 comme valeur supersédée ; la partie normative est propre.**

## Verdict

**PHYSICAL MODEL STATUS : READY FOR PREREGISTRATION — FINAL PHYSICAL FREEZE APPROVED**

Après audit exhaustif de la v0.6, aucun PENDING physique identifié ne
subsiste. Toute modification ultérieure du modèle physique est interdite,
sauf découverte documentée d'une erreur objective indépendante des
résultats P4b.

Aucune incohérence ou erreur matérielle identifiée après l'audit exhaustif
défini ci-dessus : les 26 constats sont tous corrigés dans la v0.6 ou
transférés explicitement comme obligations de préenregistrement (§11.2-9/10).
Les points PENDING restants sont exclusivement statistiques (Phase 3, non
autorisée).

**STOP.** Ce rapport n'autorise ni préenregistrement, ni grille ρ, ni seuils
statistiques, ni N, ni seeds, ni simulation, ni Monte-Carlo, ni pilote, ni
usage des 21 blocs P4a, ni modification de P2/P3/P4a/v1.4.1, ni commit de gel.
