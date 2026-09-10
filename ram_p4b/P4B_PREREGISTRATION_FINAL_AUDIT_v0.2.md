# P4b — AUDIT GLOBAL FINAL AVANT GEL — v0.2

**Date : 2026-09-11. Objets : `config_p4b_design.json`,
`P4B_PREREGISTRATION_v0.1.md`, `P4B_PREREGISTRATION_AUDIT_v0.1.md`,
`P4B_PHASE0_PHYSICAL_BASIS_v0.6.md`, `data/ocv_soc_ncr18650b_hnei.csv`,
`data/rint_soc_nmc_dtu.csv`, scripts historiques `ram_p4/graines_p4.py`,
`ram_p4/generer_design.py`, `ram_p4/campagne_p4a.py`, `config_p4a.json`.**

**Portée : correction de traçabilité de la génération du design + revue
statistique critique (multiplicité, puissance campagne) + passe globale de
cohérence STATIC ONLY. Aucune simulation P4b, aucun pilote, aucun
Monte-Carlo, aucun résultat scientifique. La régénération du design
rapportée ici est un contrôle déterministe de reproductibilité (tirages
PRNG seuls), pas une exécution de la plante P4b.**

---

## 1. Procédure réelle de génération du design — reconstitution

**Question** : les points proviennent-ils d'un flux unique
`random.Random(seed_graine("PLANT", 0))` avec rejection sampling continu
(hypothèse A), ou d'une réinitialisation par bloc
`seed_graine("PLANT", bloc_id)` (hypothèse B) ?

**Méthode** : régénération déterministe sous les deux hypothèses, dans un
environnement propre, à partir de la règle publiée
(`seed(label,i) = int(SHA256("P4b-structural-v1|<commit>|<DOI>|<label>|<i>")[0:8],
big-endian) mod 2^31`, identique à `ram_p4/graines_p4.py` avec la nouvelle
version de campagne), puis comparaison bit à bit (représentation float64
IEEE 754) avec le fichier gelable.

**Résultat** :

| Hypothèse | Points identiques bit-à-bit | Rejets reproduits |
|---|---|---|
| **A — flux unique, rejection sampling continu** | **3 500 / 3 500** | **602 / 602** |
| B — graine PLANT réinitialisée par bloc_id | 1 / 3 500 (seul bloc 0 coïncide, mécaniquement) | — |

**La procédure réelle est A, sans ambiguïté** : une seule graine
`seed_graine("PLANT", 0)`, un seul objet `random.Random`, tirages
successifs C_BATT_AH → I_SUN → I_BASE → soc0, chaque rejet consomme quatre
tirages et le flux continue, bloc_id attribué aux seuls points acceptés
dans l'ordre d'acceptation, arrêt au point accepté cible. Aucune graine
PLANT dépendant de bloc_id n'existe. Le bruit des runs relève d'un label
distinct : `seed_graine("NOISE", bloc_id)` — la séparation PLANT (flux
global de design) / NOISE (graine par bloc) est désormais écrite
explicitement au §8 du préenregistrement.

## 2. Test bit-à-bit — résultat exigé

- **3 500 / 3 500 points identiques bit-à-bit** (bloc_id et quatre floats,
  comparaison sur la représentation binaire) ✅
- **602 / 602 rejets identiques** ✅
- ordre des tirages vérifié (C_BATT_AH, I_SUN, I_BASE, soc0) ✅
- **Aucune donnée du design modifiée** : l'extension à 5 500 points
  (conséquence de C-01, ci-dessous) a **prolongé le même flux sans le
  réinitialiser** ; les 3 500 premiers points acceptés et les 602 premiers
  rejets sont strictement identiques (propriété de préfixe, re-vérifiée
  bit-à-bit après réécriture du fichier : 0 différence sur 3 500 ; puis
  5 500 / 5 500 sur la version étendue, **934 rejets** au 5 500e point
  accepté, 6 434 candidats).
- ancien SHA256 (3 500 points) conservé dans l'historique :
  `4439351a58d82dd1851568bd14e13854871e75ab75711e02563c2514f0208250` ;
- **nouveau SHA256 (5 500 points, métadonnées explicitées)** :
  `20dcb71d9d8bde837f398157882811bc391e94f713e01ec7baedcb42ff815a63`.

## 3. Champ « compteur »

`"compteur": 0` = **index i de l'unique graine de design**
`seed_graine("PLANT", 0)`. Vérifié fonctionnellement : i = 0 est la valeur
qui reproduit le fichier bit-à-bit. Ce champ n'a aucun rôle dans la
génération des nuisances individuelles (il n'existe pas de compteur par
bloc). Il est conservé et sa signification est désormais documentée dans
le JSON (`compteur_signification`) et au §7/§8 du préenregistrement. Aucune
donnée expérimentale n'a été touchée pour harmoniser ce champ.

## 4. Revue statistique critique — multiplicité (point 9 du mandat)

**L'affirmation « conjonction de deux classifications → erreur ≤ 5 % »
n'était PAS rigoureusement vraie.** La règle V4 sélectionne max(S) et
min(I) parmi 9 niveaux selon les données ; la borne 2 × 2.5 % ne vaut que
pour deux niveaux **pré-spécifiés**. Contre-exemple calculé (binomiale
exacte, N = 3 500, IC95) : si 8 niveaux ont une vraie p = 0.0101 (juste
au-dessus de εS) et le niveau haut p = 0.10, alors P(≥ 1 faux SUFFICIENT)
= 1 − (1 − 0.0177)⁸ ≈ **13.3 % > 5 %** — et V4 se déclenche alors sur une
frontière fallacieuse. **STOP appliqué ; correction pré-data proposée et
intégrée avant toute simulation** (constat C-01) :

- IC de Wilson par niveau relevé de 95 % à **99.4444 %**
  (z = 2.7729212946086634, erreur unilatérale ≤ 1/360 ≈ 0.278 % par niveau
  et par côté) ;
- famille d'erreurs = 9 fausses classifications S + 9 fausses
  classifications I = **18 événements** ; borne d'union de Bonferroni :
  P(≥ 1 erreur) ≤ 18/360 = **5 %**, **sous dépendance arbitraire** (la
  borne d'union ne suppose pas l'indépendance — le CRN ne dégrade rien) ;
- l'erreur de toute conclusion de frontière V4 (« b* ∈ (max(S) ; min(I)] »)
  est incluse dans cette famille → **≤ 5 %, non conditionnelle**, quelle que
  soit la sélection effectuée parmi les 9 niveaux ; même borne pour les
  erreurs de V1/V5 (côté S) et V2/V6 (côté I) ;
- conséquence dimensionnante : SUFFICIENT ⟺ x ≤ 34, INSUFFICIENT ⟺
  x ≥ 320 à N = 5 500 ; R1 = P(X ≤ 34 | Bin(5500, 0.005)) = 0.906 ≥ 0.90 ;
  R2 = 1.000 ; N minimal exact = 5 311 (balayage entier), N = 5 500 =
  plus petit multiple de 500 ; campagne = 9 × 5 500 = **49 500 runs
  principaux** ; le design nuisance est étendu à 5 500 points par
  continuation du flux gelé (§2) — **aucun paramètre physique modifié**,
  aucun point existant modifié ;
- tous les nombres dérivés du document ont été recalculés et mis à jour
  (§5, §6, §15, §16, cas 0/N : Wilson99.44 [0 ; 0.0014], CP 0.00107 ;
  précision 0.0187 / 0.0082 ; table OC complète).

## 5. Revue critique — puissance campagne (point 10 du mandat)

L'affirmation « approximation par indépendance conservative car le CRN
induit une corrélation positive » n'était pas démontrable en général :

- pour les verdicts de type **conjonction** (V1 = 9 niveaux S), une
  corrélation positive augmente P(∩) : l'indépendance est bien une borne
  basse (conservative) ;
- pour les verdicts à **événements d'existence** (V4 : « ≥ 1 S » et
  « ≥ 1 I »), la corrélation positive joue dans le sens inverse sur les
  sous-événements d'existence : la direction n'est **pas uniformément
  déterminée**.

Correction rédactionnelle appliquée (C-03) : les valeurs de puissance
campagne sont désormais présentées comme **indicatives sous indépendance**,
avec l'analyse de direction ci-dessus ; il est explicité que les garanties
confirmatoires (erreur par niveau ≤ 0.278 %, famille et frontière ≤ 5 %)
sont établies par borne d'union et valent **sous dépendance arbitraire**.
Aucune propriété non démontrée ne subsiste. N et les données inchangés par
ce point.

## 6. Table des constats

| ID | EMPLACEMENT | PROBLÈME | GRAVITÉ | CORRECTION | PREUVE | STATUT |
|---|---|---|---|---|---|---|
| C-01 | Préenregistrement §5/§6/§15/§16 | Borne « erreur frontière ≤ 5 % » non valable sous sélection de max(S)/min(I) parmi 9 niveaux (P(≥1 faux S) ≈ 13.3 % en configuration adverse avec IC95) | CRITICAL | IC Wilson 99.4444 % (z = 2.7729212946086634) ; Bonferroni 18 événements → erreur famille/frontière ≤ 5 % sous dépendance arbitraire ; N 3 500 → 5 500 (min exact 5 311 ; R1 = 0.906 ; R2 = 1.000) ; design étendu par continuation du flux | Calcul binomial exact du contre-exemple ; re-dimensionnement vérifié (Wilson99.44(34/5500) = [0.0039 ; 0.0099] ≤ 0.01 ; (35/5500) borne sup 0.0101 > 0.01 ; (320/5500) borne inf 0.0500 ≥ 0.05 ; (319/5500) borne inf 0.0499 < 0.05) | CORRIGÉ |
| C-02 | `config_p4b_design.json` + §7/§8 | Description de la procédure de génération potentiellement ambiguë (flux unique vs graine par bloc) | MAJOR | Procédure réelle démontrée = flux unique (A) ; texte §7/§8 et métadonnées JSON explicités (une graine, un PRNG, ordre de tirage, rejet consomme 4 tirages, bloc_id = ordre d'acceptation, arrêt au 5 500e, aucune graine PLANT par bloc) | Test bit-à-bit : A = 3 500/3 500 + 602/602 ; B = 1/3 500 | CORRIGÉ |
| C-03 | §16 (puissance campagne) | « Indépendance conservative » affirmée sans démonstration ; fausse en direction pour les événements d'existence (V4) | MAJOR | Reformulation : valeurs indicatives sous indépendance ; direction de l'effet CRN analysée par type de verdict ; garanties confirmatoires déclarées indépendance-free (borne d'union) | Analyse signe de corrélation (conjonction vs existence), §5 du présent rapport | CORRIGÉ |
| C-04 | `config_p4b_design.json` champ `compteur` | Signification ambiguë de `"compteur": 0` | MINOR | Documenté : index i de l'unique graine `seed_graine("PLANT", 0)` ; aucun compteur par bloc ; champ conservé, métadonnée explicative ajoutée | Reproduction bit-à-bit avec i = 0 | CORRIGÉ |
| C-05 | `config_p4b_design.json` | N = 5 500 (C-01) exige 5 500 points de design | — (conséquence) | Continuation déterministe du même flux (pas de réinitialisation, pas de nouvelle graine, pas de ré-échantillonnage) ; 3 500 premiers points et 602 premiers rejets strictement inchangés ; 934 rejets totaux ; nouveau SHA256 publié, ancien conservé | Préfixe vérifié bit-à-bit 3 500/3 500 ; version étendue re-vérifiée 5 500/5 500 | CORRIGÉ |
| C-06 | §5 bloc classification | Libellés résiduels « IC95 » après changement de niveau | EDITORIAL | « borne supérieure/inférieure de l'IC99.44 » | grep « IC95 » : ne subsiste que dans l'explication historique du §15 (voulu) | CORRIGÉ |
| C-07 | §10, §13 | Références résiduelles « IC Wilson 95 % » (§10) et « 9 × 3 500 runs » (§13, sensibilité OCV) | EDITORIAL | « IC Wilson 99.4444 % » ; « 9 × 5 500 runs » | Relecture intégrale post-correction | CORRIGÉ |

## 7. Passe globale de cohérence (22 contrôles du mandat)

| # | Contrôle | Résultat |
|---|---|---|
| 1 | Conflit Phase 0 / Phase 3 | ✅ aucun — la v0.6 délègue explicitement Y, εS/εF et le protocole statistique à la Phase 3 ; aucune contradiction |
| 2 | Modification physique post-gel v0.6 | ✅ aucune — v0.6 intacte (non éditée) ; tables inchangées |
| 3 | Grille ρ = {1.000 ; 1.125 ; 1.250 ; 1.375 ; 1.500 ; 1.625 ; 1.750 ; 1.875 ; 2.000} | ✅ §3 inchangé |
| 4 | N = 5 500 par niveau (après correction C-01) | ✅ §6 ; cohérent partout |
| 5 | 9 × 5 500 = 49 500 runs principaux | ✅ §6, §15 |
| 6 | Seuils Wilson : SUFFICIENT ⟺ x ≤ 34 ; INSUFFICIENT ⟺ x ≥ 320 | ✅ re-vérifiés par calcul exact (§4 ci-dessus) |
| 7 | εS = 0.01 | ✅ inchangé (héritage P4a) |
| 8 | εF = 0.05 | ✅ inchangé (héritage P4a) |
| 9 | Aucun usage des 21 blocs P4a | ✅ confirmé |
| 10 | Endpoint principal exact | ✅ §4 inchangé (Y_j = 1{min_k V_pack(t_k) < 5.0}, float64, toutes phases, INVALID_TECHNIQUE tolérance zéro) |
| 11 | V0–V7 exhaustifs et déterministes | ✅ partition démontrée §12, cas A–J mappés |
| 12 | Sensibilité OCV en dégradation seule | ✅ §13 inchangé |
| 13 | Sensibilité FLAG en dégradation seule | ✅ §13 règle symétrique inchangée |
| 14 | Règle hors domaine conforme v0.6 | ✅ inclusion + drapeau + garde-fou 25 % ; exposition réévaluée sur le design étendu : 330/5 500 = 6.0 % flaggés (SoC > 1), 0 point SoC < 0 (min 0.19) — cohérent avec la quadrature ≈ 6.6 % |
| 15 | Contrôle dt conforme | ✅ dt = 2.5 s, mêmes graines NOISE (convention P4a-dtctrl), ρ = 1.000 / 2.000 / bornes de frontière |
| 16 | CRN correctement défini | ✅ §7 : même graine NOISE par bloc aux 9 niveaux |
| 17 | Seeds correctement définies | ✅ §8 : distinction explicite PLANT (flux global unique) / NOISE (par bloc) ; règle SHA256 vérifiée contre `graines_p4.py` |
| 18 | Design reproductible bit-à-bit | ✅ 3 500/3 500 (préfixe) et 5 500/5 500 (version courante), 602 + 934 rejets, SHA256 publiés |
| 19 | Hashes des tables conformes | ✅ `7aa959fc…7154c2` (OCV), `330efcd3…697b93` (Rint) — inchangés, conformes v0.6 |
| 20 | Aucun PENDING | ✅ les 10 points restent résolus après corrections |
| 21 | Aucun paramètre choisissable après résultats | ✅ toute modification post-résultat interdite (§6, §8, §14) ; C-01/C-03 appliqués avant toute simulation |
| 22 | Aucune ambiguïté d'implémentation | ✅ procédure de design désormais non interprétable de travers ; endpoint, classification, verdicts déterministes |

## 8. Historique des empreintes du design

| Version | Points | Rejets | SHA256 |
|---|---|---|---|
| initiale | 3 500 | 602 | `4439351a58d82dd1851568bd14e13854871e75ab75711e02563c2514f0208250` |
| **courante (gelable)** | **5 500** | **934** | `20dcb71d9d8bde837f398157882811bc391e94f713e01ec7baedcb42ff815a63` |

La version courante prolonge strictement la version initiale (préfixe
bit-à-bit vérifié). Tables physiques inchangées (hashes §7, contrôle 19).

## 9. Verdict

**FINAL PREREGISTRATION AUDIT: READY FOR FREEZE**

- design reproduit 3 500/3 500 (préfixe) et 5 500/5 500 bit-à-bit, 602
  puis 934 rejets ✅ ;
- aucune donnée du design modifiée (propriété de préfixe démontrée) ✅ ;
- aucune ambiguïté de seed restante (PLANT flux global unique / NOISE par
  bloc, procédure écrite sans interprétation possible) ✅ ;
- aucune erreur statistique matérielle restante : la faille de multiplicité
  (C-01) est corrigée par Bonferroni 18 événements (erreur de frontière
  ≤ 5 % garantie sous dépendance arbitraire) et le wording de puissance
  (C-03) ne revendique plus aucune propriété non démontrée ✅ ;
- aucun PENDING ✅ ;
- aucun résultat P4b généré ✅.

---

**STOP.** Cet audit n'autorise ni l'implémentation de la plante P4b, ni le
lancement de la campagne, ni un pilote, ni un Monte-Carlo, ni la production
de résultats scientifiques, ni la modification de P2/P3/P4a/v1.4.1. Le
gel/commit sera une étape séparée, après validation externe explicite.
