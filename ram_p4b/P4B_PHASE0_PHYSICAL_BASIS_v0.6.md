# P4b — PHASE 0 : JUSTIFICATION PHYSIQUE INDÉPENDANTE

**Version 0.6 — CONSOLIDATION FINALE POST-AUDIT EXHAUSTIF (2026-09-11).**

Cette version est **autonome et consolidée** : elle remplace intégralement la
v0.5. La partie normative (§1–§12) est nettoyée ; toutes les valeurs qui y
figurent sont les valeurs finales corrigées. Les blocs de changelog ci-dessous
sont conservés pour traçabilité et marqués **HISTORIQUE** ; toute valeur qui y
diffère de la partie normative est **SUPERSEDÉE / REMPLACÉE** par celle de la
partie normative.

Corrections intégrées en v0.6 (détail, preuves et gravités :
`P4B_PHASE0_FINAL_AUDIT_v0.6.md`) :

1. §5 : renvoi « PENDING » obsolète vers §7.2-E supprimé — les règles Vp(t0)
   et courant signé sont gelées depuis la v0.5.
2. §7.2-B : constantes de temps corrigées partout : τ = Rp·Cp ∈ [86 ; 338] s,
   τ/900 ∈ [0.10 ; 0.38] ; écart p35/médiane Rs corrigé (≤ 2.0 mΩ, pas 0.7).
3. §7.2-E : formulation du signe de Vp corrigée — le signe du courant fixe le
   signe de l'**asymptote** de Vp, pas son signe instantané (état à mémoire) ;
   suppression de l'affirmation absolue « pas de sous-tension en charge » ;
   Vp(t0) déclaré **convention quasi-stationnaire pré-data** (ordre de
   grandeur, pas borne rigoureuse).
4. §7.2-C : « exact pour un nombre quelconque de branches identiques »
   remplacé par « modèle équivalent continu préservant exactement le taux-C ».
5. §6.4 : cas défavorable recalculé — la fenêtre payload [600 ; 1500] s est en
   phase lumière (code gelé : `en_lumiere = (t % 5400) < 3600`), donc
   I_batt,max = I_BASE + u − I_SUN = 0.75 + 3.0 − 0.8 = **2.95 A** et
   I_cell = 2.95 × 3.35/4.4 = **2.25 A** (0.67 C) — et non 3.5 A / 2.66 A ;
   tableau entier recalculé ; section étiquetée **ILLUSTRATION ANALYTIQUE
   PRÉ-DATA**.
6. Taper CC/CV : la justification « hors zone opérée (SoC ≤ 0.70) » est
   invalide (soc0 est une condition initiale ; soc(t) peut croître en
   lumière) ; exclusion re-justifiée honnêtement (§2, §4, §9).
7. S6 : « surcharge hors champ du scénario » corrigé — soc non saturé peut
   dépasser 1 dans le scénario ; règle « hors domaine physique » ajoutée
   (§7.2-A, GELÉE v0.6).
8. Hiérarchie des sources : source 4 (agrégateur) reclassée A → C ; source 13
   (revue MDPI) reclassée A → B.
9. Extension > 90 % : la citation DTU ne justifie que Rp ; le clamp Cp est une
   règle méthodologique de clôture de frontière — déclaré (doc + CSV).
10. V_min = 2.5 V/cellule : PROPOSÉ → **GELÉ v0.6** (V_min,pack = 5.0 V).
11. Table finale des paramètres consolidée (§7.6) ; statuts unifiés (plus
    aucun mélange PROPOSÉ/VALIDÉ/GELÉ/PENDING dans la partie normative).
12. Obligation ajoutée au préenregistrement : analyse de sensibilité à
    l'incertitude OCV locale (±0.1 V, SoC < 2 %) si la frontière éventuelle
    s'y situe — l'illustration §6.4 l'indique (§11.2).

---

**Blocs HISTORIQUES (traçabilité — valeurs SUPERSEDÉES le cas échéant)**

- **HISTORIQUE v0.5 (2026-09-10)** — clôture des PENDING physiques : erreur
  objective de numérisation des Fig. 7A/8A démontrée et corrigée (Rp, Cp
  ré-extraits ; Rs, OCV ré-extraits identiques) ; extension > 90 % gelée ;
  OCV < 2 % gelé ; Vp(t0) gelé ; convention de courant gelée ; topologie
  option B (pack équivalent continu) ; ECSS vérifié sur texte source.
  *(Les valeurs citées dans ce bloc restent valides sauf mention contraire
  dans la partie normative.)*
- **HISTORIQUE v0.4 (2026-09-10)** — amendement 3 : statut exact du modèle
  composite ; interprétation exacte de ρ ; définition de l'aléa
  V_pack < 5.0 V ; Vp état continu jamais remis à zéro.
  *SUPERSEDÉ : la mention « Vp(t0) et convention de charge : PENDING » est
  remplacée par les règles gelées v0.5 (§7.2-E).*
- **HISTORIQUE v0.3 (2026-09-10)** — amendement 2 : comparaison AC/DC
  supprimée ; Thevenin ordre 1 retenu ; modèle composite déclaré.
  *SUPERSEDÉ : « τ mesuré entre 51 et 294 s, τ/900 ∈ [0.06 ; 0.32] » —
  valeurs d'avant la correction v0.5 ; valeurs finales : 86–338 s,
  [0.10 ; 0.38].*
- **HISTORIQUE v0.2 (2026-09-10)** — amendement 1 : V_min 3.0 V abandonné,
  2.5 V proposé ; ρ_max non attribué à Hein ; références ECSS ajoutées ;
  tables numériques sourcées.
  *SUPERSEDÉ : « 2,5 V proposé » → GELÉ v0.6 ; la règle de topologie 2S-nP
  discrète est remplacée par le pack équivalent continu (§7.2-C).*

**Statut : modèle physique GELÉ — verdict d'audit final en §12. Aucun code de
campagne, aucun design, aucune seed, aucune simulation P4b. Ce document ne
modifie rien de l'existant.**

Références immuables : v1.4.1 (intangible) ; P4a gelé au commit
`aba115ff174ee41629f1fda27b6ff826a007622c` (release v1.5.0-p4a), verdict D —
INCONCLUSIVE, annexe post-hoc gelée. Aucun résultat P4a n'est utilisé pour
construire ce qui suit (voir §10).

---

## 1. État du modèle actuel (audit du code gelé)

Audit de `ram_p0/demo_eps.py` (plante) et `ram_p0/filtre.py` / `moniteur.py`
(moniteur), inchangés depuis v1.4.1.

### 1.1 Dynamique énergétique (plante = modèle interne du moniteur)

```
dsoc  = (i_charge − I_BASE − u) / (C_BATT_AH · 3600)
dtemp = H · (I_BASE + u) − C_TH · (temp − t_env)
```

Le moniteur prédit avec **la même classe** `ModeleEPS.pas(x, u, dt)`
(`filtre.py:104`). Le modèle interne et la plante ont donc une structure
strictement identique ; en P2/P3 le mismatch était paramétrique, en P4a il
était réduit à un biais d'estimation SoC injecté après le bruit.

Simplifications physiques identifiées :

| # | Simplification | Conséquence |
|---|---|---|
| S1 | Comptage de coulombs pur, rendement 100 % | aucune tension n'existe nulle part dans le modèle |
| S2 | Capacité `C_BATT` constante | pas de vieillissement, pas de dépendance au régime de courant, pas de dépendance à la température |
| S3 | Pas de résistance interne, pas de tension de circuit ouvert | la chute de tension sous charge est impossible à représenter |
| S4 | `I_SUN` binaire (lumière/éclipse) et constant en lumière | pas de taper CC/CV, pas de variation d'ensoleillement |
| S5 | Axe thermique mort : `temp` n'agit sur rien | la température ne modifie ni capacité, ni résistance, ni puissance |
| S6 | Pas de saturation de `soc` dans la plante | soc(t) peut sortir de [0 ; 1] **y compris dans le scénario** (recharge nette jusqu'à ≈ +0.38/orbite au coin I_SUN = 2.5 A, C_BATT = 4.4 Ah) — traité par la règle « hors domaine physique » (§7.2-A) |
| S7 | Pack = cellule équivalente unique | pas de déséquilibre entre cellules |

### 1.2 La contrainte de sécurité est un **proxy** — ancrage dans le code gelé

`contraintes_eps()` (code gelé, verbatim) :

> C0 : « l'état de charge batterie ne doit jamais passer sous le seuil de
> **sous-tension** » -> soc >= 0.35, avec marge de garde 0.02.

L'aléa physique réel est donc, depuis l'origine du projet, la **sous-tension** ;
le moniteur le surveille via un proxy SoC. C'est écrit dans le code depuis P0 —
ce n'est pas une reconstruction postérieure.

---

## 2. Phénomènes physiques absents du modèle

| # | Phénomène | Dans le modèle ? | Structurel ? | Importance physique | Isolable ? | Plage défendable avant simulation ? |
|---|---|---|---|---|---|---|
| P1 | Tension terminale sous charge : V = OCV(SoC) − I·R_int | Non (S1, S3) | **Oui** — nouvelle variable physique, non réductible à un paramètre du modèle figé | Forte : c'est l'aléa réel de C0 | Oui | Oui (datasheets) |
| P2 | Dépendance de R_int au SoC et au vieillissement | Non | Oui (sous-partie de P1) | Forte à SoC bas et en fin de vie | Oui (facteur scalaire) | Oui (littérature vieillissement) |
| P3 | Capacity fade (statique) | Non, **mais** : une capacité effective réduite constante est déjà couverte par le nuisance `C_BATT ∈ [4.4; 14.4]` Ah de P4a | **Non** — paramétrique | Forte en valeur absolue, déjà balayée | Oui | Oui |
| P4 | Effet régime-capacité (type Peukert) | Non | Oui en théorie | **Faible** pour Li-ion à 0.2–0.5 C (exposant ≈ 1.0–1.05 ; §6.2) | Oui | Oui |
| P5 | Couplage température → énergie (R_int(T), capacité(T)) | Non (S5) | Oui | Forte sous 0 °C ; modérée dans la plage thermique du scénario | Moyen — couple avec l'axe thermique | Oui mais plus diffuse |
| P6 | Taper de charge CC/CV à SoC haut | Non (S4) | Oui | Non évaluée ici : exclusion déclarée (§9) — soc0 ∈ [0.40 ; 0.70] est une condition initiale et soc(t) peut croître au-delà en lumière ; le chargeur gelé est à courant constant | Oui | Oui |
| P7 | Déséquilibre cellules d'un pack (la plus faible atteint V_min la première) | Non (S7) | Oui | Modérée ; se subsume en facteur aggravant de P1 | Difficile seul | Partiellement |
| P8 | Auto-décharge | Non | Non (paramétrique) | **Négligeable** : 1–3 %/mois vs 2.5 orbites | Oui | Oui |
| P9 | Rendement coulombique < 1 | Non | Non (paramétrique) | Faible : 1–2 %, absorbé par le bruit/nuisance | Oui | Oui |
| P10 | Hystérésis/relaxation OCV | Non | Oui | Faible : quelques mV à quelques dizaines de mV | Difficile | Partiellement |

---

## 3. Sources (hiérarchie A : constructeur/agence/standard ; B : littérature
à comité de lecture ; C : technique secondaire / agrégateur)

1. **NASA NTRS — « Nano Satellite Electrical Power Systems »** (A) :
   « Li-Ion exhibits a highly non-linear relationship between cell voltage and
   state of charge (SoC) » ; « Cell voltage should be maintained between
   2.5 V to 4.1 V or 4.2 V » ; « As cells age, their internal resistance
   increases, reducing their output power » ; packs 2S ~7.2 V à base de 18650.
   https://ntrs.nasa.gov/api/citations/20240007136/downloads/Nano%20Satellite%20Electrical%20Power%20Systems%20Revised.pdf
2. **NASA SmallSat Institute — State of the Art, Power** (A) : état de
   l'art PMAD/batteries smallsats.
   https://www.nasa.gov/smallsat-institute/sst-soa/power-subsystems/
3. **Panasonic NCR18650B — datasheet** (A — contenu constructeur, hébergé par
   un distributeur) : 3350 mAh typique (3200 nominal min), tension nominale
   3.6 V, **tension de fin de décharge 2.5 V**, impédance AC ≤ 100 mΩ (1 kHz),
   courant de décharge continu max 4.875 A, courbes de décharge 0.2/0.5/1/2 C
   et en température (−20…+60 °C).
   https://www.tme.eu/Document/3e0170a1e089819f286f7066e69035b4/NCR18650B.pdf
4. **GomSpace NanoPower BP4 / BPX / P31u** (**C — site agrégateur**
   rapportant des fiches techniques constructeur, contenu non revérifié sur
   le site primaire dans le cadre de cet audit) : packs CubeSat 18650 —
   BP4 2P-2S « 6–8.4 V & 5.2 Ah », BPX 2S-4P « 6–8.4 V & 10.4 Ah » ;
   « Battery under-voltage and over-voltage protection » (P31u). Utilisée
   uniquement comme indication d'**héritage architectural** (topologies
   2P–4P, protections UV/OV existantes), jamais comme source de valeurs
   numériques du modèle.
   http://cubesatnano.ru/en/portfolio_category/gomspace-en/
5. **AAC Clyde Space OPTIMUS** (A) : batteries CubeSat à fort héritage de vol,
   protections intégrées « under-voltage protection, over-voltage protection
   and string over-current protection » ; packs typiques 8.26 V (2S).
   https://www.aac-clyde.space/what-we-do/space-products-components/cubesat-batteries
6. **GomSpace BP8 — datasheet** (A) : pack 8S 100 Wh (23.6–33.6 V) ;
   **verrouillage sous-tension matériel** : activation 19.3 / 19.5 / 19.8 V
   (min/typ/max), réarmement 21.0 / 21.5 / 21.7 V ; sous 11.5 V le pack est
   irrécupérable. Rapporté au 8S : activation ≈ **2.44 V/cellule** (typ),
   réarmement ≈ 2.69 V/cellule. Seuil matériel, non configurable.
7. **GomSpace P80 — manuel utilisateur** (A) : protections matérielles
   **non configurables** (pack 32 V : haute 34600 mV, basse 30500 mV) ;
   les seuils de mode batterie (critical 26000 mV, safe 26800, normal 28000,
   full 32000, soit 3.25–4.00 V/cellule) sont des seuils **logiciels**
   configurables de gestion opérationnelle — pas des protections.
8. **Dubarry et al. — rapport HNEI de caractérisation NCR18650B** (B, mesures
   primaires) : courbe **OCV = f(SoC) spécifique NCR18650B** (cellule 103,
   moyenne charge/décharge C/25, Figure 6) — source de la table OCV (§7.2,
   `data/ocv_soc_ncr18650b_hnei.csv`) ; **résistance ohmique** (chute
   immédiate sous courant, Table 1) : moyenne 59.6 mΩ, médiane 59.2,
   [56.3 ; 67.1] mΩ sur ~100 cellules neuves — contrôle de cohérence DC/DC
   du Rs DTU (§7.2-B).
9. **Thingvad et al. (DTU) — caractérisation Thevenin NMC 18650** (B, mesures
   primaires) : 4 cellules neuves (set A) + 4 vieillies à SOH 90 % (set B) ;
   Rs, Rp, Cp par pas de 10 % de SOC à 23 °C et 45 °C (Fig. 6/7/8) ;
   « Rs depends significantly on SOC and temperature » ; Rs set B > set A.
   Décharge CC 1C par pas de 0.3 Ah, relaxation 20 min (test C). Source de la
   table Thevenin Rs/Rp/Cp (§7.2, `data/rint_soc_nmc_dtu.csv`).
   https://backend.orbit.dtu.dk/ws/files/216887835/Characterization_of_NMC_Lithium_ion_Batteries.pdf
10. **Galushkin et al., J. Electrochem. Soc. 2020 — « A Critical Review of
    Using the Peukert Equation and its Generalizations for Lithium-Ion
    Cells »** (B) : Peukert classique « is not applicable at both very small
    and high discharge currents » pour le Li-ion ; exposant ≈ 1.0–1.05.
    https://iopscience.iop.org/article/10.1149/1945-7111/abad69
11. **Hein et al. 2023 — vieillissement module 8S1P 18650** (B) : Rinit
    moyen 56.8 mΩ (cellules neuves) ; après 174 cycles 1C/1C sévères,
    résistances finales 60.3–75.0 mΩ, soit un ratio fin/début **≤ 1.37**
    (capacités résiduelles 71–92 %). Hein mesure directement une croissance
    de l'ordre de **1.37× maximum dans son protocole** ; rien au-delà n'en
    est extrapolé ici.
    https://upcommons.upc.edu/bitstreams/9be40c44-cf51-414a-b6ac-ae5047e17173/download
12. **Wheeler et al. 2025 — vieillissement 20 cellules 18650 LFP (Sci.
    Data)** (B) : impédance plus élevée à 0 % de SoC qu'à 50/100 % ;
    croissance des résistances série et de transfert avec l'âge.
    https://pmc.ncbi.nlm.nih.gov/articles/PMC11885844/
13. **Revue de dégradation Li-ion, MDPI Energies 2025** (**B** — revue
    scientifique à comité de lecture, non source primaire) : synthèse de
    croissances de résistance publiées — Wang et al. : résistance ≈ **3×** à
    80 % SOH sous cyclage **abusif 20C** (A123 LFP 26650) ; Sony LFP :
    **+78 %** après 2000 cycles ; Samsung NMC : **+10 %** après 3000 cycles.
14. **MDPI Batteries 2024 — revue de dégradation Li-ion** (B) : critère EOL à
    80 % de capacité ; croissance SEI → hausse de résistance interne.
    https://www.mdpi.com/2313-0105/10/7/220
15. **MDPI Energies 2026 — OCV et températures extrêmes** (B) : la hausse de
    résistance à froid provoque l'atteinte prématurée des seuils de coupure
    sous charge (modèle R-int).
    https://www.mdpi.com/1996-1073/19/1/27
16. **NASA Ames PCoE — jeux de données de vieillissement Li-ion 18650** (A) :
    EIS multi-âges, critère EOL = 30 % de perte de capacité. (Contexte, non
    utilisé pour des valeurs absolues.)
17. **ECSS-E-ST-20C Rev.2 — « Electrical and electronic » (8 avril 2022)**
    (A) — **vérifié sur texte source (v0.5)**, §5.7.3 « Battery Charge and
    Discharge Management » : « The ultimate over charging/discharging
    protection circuitry shall be implemented by hardware and independent
    from any on board software » (exigence h) ; « Battery charge and
    discharge management shall be such that a single failure … does not
    impair the lifetime of the energy storage system with respect to
    minimum or maximum voltage as well as maximum charge or maximum
    discharge current » (exigence i). Utilisée uniquement pour l'affirmation
    architecturale : une protection matérielle ultime de surcharge/décharge
    profonde, indépendante du logiciel, est une exigence standard. **Aucune
    valeur numérique n'en est extraite ; l'ECSS n'impose notamment aucun
    seuil de 2.5 V.**
    https://ecss.nl/wp-content/uploads/2022/04/ECSS-E-ST-20C-Rev.2(8April2022).pdf
18. **ECSS-E-HB-20-02A — « Li-ion battery testing handbook » (1er octobre
    2015)** (A) — **vérifié (v0.5)** : handbook non normatif couvrant les
    essais de caractérisation (dont « internal resistance measurement »,
    « AC impedance measurement », « cell EMF measurement »). Utilisé comme
    référence méthodologique de caractérisation uniquement — rien d'autre.
    https://ecss.nl/hbstms/ecss-e-hb-20-02a-li-ion-battery-testing-handbook-1-october-2015/

Non utilisée : **ECSS-E-ST-20-06 « Spacecraft charging »** — traite de la
charge électrostatique du satellite, sans rapport avec la protection batterie ;
explicitement écartée.

---

## 4. Comparaison des candidats

| Candidat | Classe | Motif |
|---|---|---|
| **P1+P2 — Tension terminale sous charge (OCV + R_int(SoC) + vieillissement)** | **A** | Aléa physique réel de C0 ; absent du modèle ; non reparamétrable (§6.1) ; bornes datasheet ; interprétable |
| P5 — Couplage température → énergie | B | Réel et structural, mais couplé à l'axe thermique : isolation expérimentale plus difficile ; candidat naturel pour une P4b.2 |
| P7 — Déséquilibre de cellules | B | Réel ; traitable d'abord comme aggravant de P1 (worst-cell), pas comme axe principal isolable |
| P4 — Effet régime-capacité (Peukert-like) | C | Amplitude faible à 0.2–0.5 C pour Li-ion ; largement redondant avec le modèle R-int |
| P6 — Taper de charge CC/CV | C | Non modélisé — exclusion déclarée (§9) : le chargeur du code gelé est à courant constant ; soc(t) peut atteindre la zone de taper en lumière |
| P3 — Fade statique | C (pour P4b) | Paramétrique et déjà balayé comme nuisance en P4a ; sa composante dynamique intra-mission est négligeable sur 2.5 orbites |
| P8/P9/P10 — Auto-décharge, rendement, hystérésis | D | Amplitudes négligeables à l'échelle de 2.5 orbites |

---

## 5. Candidat P4b retenu

**Mismatch structurel unique : la sécurité réelle est une propriété de tension
terminale sous charge, l'enveloppe B ne surveille qu'un proxy SoC.**

Plante réelle proposée (structure, pas encore implémentée) — **Thevenin
d'ordre 1 explicite** (option A de l'audit, §7.2-B) :

```
I_batt(t) = I_BASE + u(t) − i_charge(t)     (signé ; > 0 = décharge)
I_cell(t) = I_batt(t) · C_cell / C_BATT     (pack équivalent continu, §7.2-C)
V_pack(t) = N_S · [ OCV(SoC(t)) − I_cell(t) · ρ · Rs(SoC(t)) − Vp(t) ]
dVp/dt    = − Vp / (ρ · Rp(SoC) · Cp(SoC)) + I_cell / Cp(SoC)
```

avec OCV(SoC), Rs(SoC), Rp(SoC), Cp(SoC) des tables fixes sourcées (§7.2,
`data/`), N_S = 2, C_cell = 3.35 Ah, et **ρ facteur expérimental de
scaling résistif** multipliant les deux résistances (interprétation exacte :
§7.1). La convention I_batt signée est cohérente avec le code gelé :
`dsoc = (i_charge − I_BASE − u)/(C_BATT·3600)` = −I_batt/(C_BATT·3600).

**Statut exact du modèle** : modèle électrochimique équivalent **composite**
de cellule Li-ion 18650 haute énergie, combinant une relation OCV–SoC issue
du NCR18650B et des paramètres dynamiques Thevenin issus de cellules
NMC 18650. Il ne constitue la qualification d'aucune chimie ni référence
commerciale particulière. Toute frontière éventuellement identifiée par P4b
sera une propriété du **modèle composite expérimental défini et gelé pour
cette campagne** ; elle ne devra pas être présentée comme une frontière
générale des cellules NMC 18650 ni comme une qualification spécifique du
Panasonic NCR18650B.

**Aléa physique étudié** :

```
V_pack(t) < V_min,pack
avec  V_min,pack = N_S · V_min,cell = 2 × 2.5 V = 5.0 V   (GELÉ v0.6, §7.2-D)
```

Cette condition est interprétée comme une violation de la limite basse de
tension retenue pour P4b. Les protections matérielles COTS sous-tension
documentées (sources 3, 6, 17) démontrent la **pertinence architecturale**
de cet aléa, sans être utilisées comme modèle exact du déclenchement d'un
pack 2S P4b : P4b ne prétend pas reproduire le circuit de protection exact
d'un produit GomSpace ou d'un autre EPS commercial.

Le contraste étudié reste :

- **réalité physique P4b** : contrainte sur la tension terminale sous charge ;
- **enveloppe B gelée** : contrainte proxy sur SoC ≥ 0.35.

**État Vp** : état dynamique continu du Thevenin d'ordre 1, propagé pendant
toute la durée du run (phases payload comme hors-payload), **jamais remis à
zéro** lors de l'entrée dans une fenêtre payload. Règle d'initialisation
Vp(t0) et convention de courant signé : **gelées (§7.2-E)**.

---

## 6. Justification du choix

### 6.1 Pourquoi ce mismatch est structurel et non paramétrique

La chute de tension dépend du **courant instantané** : ΔV = I·R. Aucun
abaissement fixe du seuil SoC ne peut reproduire un aléa qui ne s'active que
quand le payload débite (3 A dans la fenêtre de mission) et disparaît hors
charge. Le mismatch n'est donc pas réductible à un décalage de paramètre du
modèle figé — il introduit une physique (la tension) absente de la structure.

### 6.2 Pourquoi pas une loi de Peukert (comparaison des modèles)

| Modèle | Verdict | Justification |
|---|---|---|
| Peukert classique C = f(I) | **Rejeté** | Li-ion : exposant ≈ 1.0–1.05 (effet de quelques % à nos régimes) ; inapplicable aux courants faibles et forts (source 10) ; ne représente pas la tension, donc pas l'aléa C0 |
| R-int / Thevenin d'ordre 0 : V = OCV(SoC) − I·R_int | **Rejeté** (audit v0.2, correction 2) | Rs + Rp appliqué instantanément surestime la chute de tension en début de fenêtre payload : τ = Rp·Cp mesuré entre 86 et 338 s (table corrigée v0.5), soit **τ/900 ∈ [0.10 ; 0.38]** — l'hypothèse quasi-stationnaire n'est pas valide sur toute la fenêtre et l'endpoint min_t V serait biaisé |
| Thevenin d'ordre 1 (paire RC) | **Retenu** (option A de l'audit) | Rs = chute ohmique immédiate, Rp-Cp = polarisation transitoire (définitions de la source 9) ; Rs, Rp, Cp tous sourcés et interpolables (DTU Fig. 6A/7A/8A, `data/`) ; représente la physique fournie par la source sans approximation sur l'endpoint |

### 6.3 Critères de sélection (indépendants de tout résultat P4a)

- **Réalisme spatial** : la protection sous-tension est la protection batterie
  standard des EPS CubeSat (sources 1, 4, 5, 6) et une exigence de norme
  indépendante du logiciel (source 17).
- **Amplitude défendable** : paramètres Thevenin cellule neuve sourcés
  (Rs 37–56 mΩ, Rp 19–67 mΩ, Cp 3.6–14.1 kF selon SoC, conventions
  p35/médiane, table §7.2-B) ; cohérence DC/DC avec la résistance ohmique
  NCR18650B du rapport HNEI (59.6 mΩ moyenne, §7.2-B) ; croissance avec
  l'âge jusqu'à ~1.9× lue visuellement à SOH 90 % (§7.1).
- **Interprétabilité** : « l'enveloppe surveille un proxy ; la réalité déclenche
  sur la tension sous charge » — phrase unique, mécanisme complet.
- **Domaine définissable avant simulation** : toutes les bornes proviennent de
  datasheets/littérature (§7).
- **Pertinence RA** : c'est le cœur du concept « Runtime-Assured Autonomous
  Satellite » — une couche légère qui vérifie un proxy suffit-elle quand
  l'aléa réel est une autre grandeur physique ?

### 6.4 Faisabilité physique — ordre de grandeur

**ILLUSTRATION ANALYTIQUE PRÉ-DATA — PAS UN RÉSULTAT P4b.** Lecture directe
des tables sourcées (§7.2) sous le modèle ordre 1 (§5) ; aucune simulation
du système, aucune conclusion de campagne.

Cas défavorable du domaine nuisance (pack équivalent, §7.2-C) :

- **Courant de décharge maximal sur le run** : la fenêtre payload
  [600 ; 1500] s est **en phase lumière** (code gelé :
  `en_lumiere = (t % 5400) < 3600`), donc
  I_batt,max = I_BASE + u − I_SUN = 0.75 + 3.0 − 0.8 = **2.95 A**
  (hors fenêtre payload, u = 0 → I_batt ≤ I_BASE ≤ 0.75 A) ;
- C_BATT = 4.4 Ah (borne basse du nuisance) →
  I_cell = 2.95 × 3.35/4.4 = **2.25 A** (0.67 C, sous la limite 4.875 A du
  datasheet, source 3).

Lecture à ρ = 2, en distinguant le **début de fenêtre** (t = 0⁺ : Rs seul
agit, Vp = 0 par convention d'illustration) et la **fin de fenêtre**
(t = 900 s : Vp ≈ I_cell·ρ·Rp·(1−e^(−900/τ))) :

| SoC plante | OCV (V) | Rs (mΩ) | Rp (mΩ) | Cp (kF) | τ à ρ=2 (s) | ΔV t=0⁺ (mV) | ΔV t=900 s (mV) | V_cell t=900 s (V) |
|---|---|---|---|---|---|---|---|---|
| 0.35 | 3.58 | 38.6 | 26.1 | 4.8 | 254 | 173 | 287 | 3.30 |
| 0.20 | 3.48 | 40.9 | 28.0 | 7.1 | 398 | 184 | 296 | 3.18 |
| 0.10 | 3.35 | 43.1 | 40.9 | 6.2 | 507 | 194 | 346 | 3.00 |
| 0.02 | ≈ 3.16 | 42.9 | 61.5 | 4.4 | 546 | 193 | 416 | 2.75 |
| 0.00 | ≈ 2.83 | 42.9 | 66.6 | 4.0 | 533 | 193 | 437 | 2.40 |

Lecture : la part transitoire (Vp) contribue ≈ 38–56 % de la chute totale en
fin de fenêtre — un modèle ordre 0 appliquant Rs+Rp instantanément l'aurait
comptée dès t = 0, d'où le rejet de cette approximation (§6.2). Dans cette
illustration, le franchissement de 2.5 V/cellule ne se produit que pour
**SoC ≲ 0.6 %** — c'est-à-dire **à l'intérieur du segment d'incertitude OCV
locale ±0.1 V** (§7.2-A). Conséquence pré-data : si la frontière éventuelle
de P4b se situe dans cette zone, une **analyse de sensibilité à l'incertitude
OCV locale devra être préenregistrée** (obligation transférée, §11.2) —
déclaré, non retuné.

**Convention du tableau** : les colonnes t = 0⁺ / t = 900 s supposent Vp = 0
à l'entrée de la fenêtre, c'est-à-dire un **état initial relaxé**. C'est une
convention d'illustration analytique uniquement : elle ne définit pas
l'initialisation de la future campagne P4b (règle Vp(t0) : §7.2-E) et ne
doit pas être interprétée comme une remise à zéro de la polarisation à
chaque fenêtre payload.

Conséquence honnête : **on ne sait pas d'avance si le domaine contient des
violations**. Dans cette illustration, avec V_min = 2.5 V/cellule, la tension
ne franchit le seuil qu'au voisinage du coude de fin de décharge
(SoC ≲ 1 %), très en dessous du guard SoC 0.35 du moniteur : la question
« le proxy SoC suffit-il » reste entièrement ouverte, et les deux issues
sont scientifiquement valables. Aucun paramètre n'a été choisi pour
provoquer ni pour exclure ce franchissement (§10).

---

## 7. Proposition D_physique_P4b (non implémentée)

### 7.1 Facteur expérimental unique

| Variable | Symbole | Unité | Plage | Justification des bornes |
|---|---|---|---|---|
| Facteur expérimental de scaling résistif | ρ | sans dimension | **[1.0 ; 2.0]** | Voir justification en couches ci-dessous |

**Interprétation exacte de ρ** : ρ est un facteur expérimental de scaling
résistif / proxy de dégradation résistive :

```
Rs,ρ(SoC) = ρ · Rs,ref(SoC)
Rp,ρ(SoC) = ρ · Rp,ref(SoC)
Cp,ρ(SoC) = Cp,ref(SoC)
```

ρ n'est **pas** interprété comme une loi universelle reliant directement SOH
et résistance, ni comme un « facteur réel de vieillissement ». Il paramètre
uniquement l'amplitude du mismatch résistif étudié, avec des bornes
justifiées indépendamment par les données de vieillissement disponibles
(ci-dessous). Le scaling commun de Rs et Rp et l'absence de scaling de Cp
constituent des **choix expérimentaux pré-data** du modèle P4b ; ils ne
prétendent pas reproduire une loi électrochimique universelle de
vieillissement.

Justification en couches de la borne haute ρ_max = 2.0 (aucune couche ne
suffit seule ; la marge est étiquetée comme telle) :

1. **Directement documenté, non abusif — lecture visuelle en plage** : DTU
   (source 9), NMC 18650 à SOH 90 % (set B vs set A) : R_int,DC à SoC médian
   passant de ~37–42 mΩ (neuf) à ~45–75 mΩ → **ρ ∈ [1.1 ; 1.9] lu
   visuellement à SOH 90 %**. Il s'agit d'une **lecture en plage sur
   graphique, pas d'une mesure précise** : la numérisation complète du set B
   a échoué et aucune valeur pseudo-précise n'est publiée (§7.2-B).
2. **Directement documenté, sévère** : Hein et al. (source 11) : croissance
   jusqu'à **1.37× maximum** après 174 cycles 1C/1C sévères, dans son
   protocole ; ρ = 2.0 n'est **pas** attribué à Hein.
3. **Borne supérieure abusive** : revue MDPI Energies 2025 (source 13) :
   ≈ **3×** à 80 % SOH sous cyclage abusif 20C (Wang et al., LFP) ; +78 %
   après 2000 cycles en LFP modéré (Sony) ; +10 % après 3000 cycles en NMC
   ménagé (Samsung).
4. **Conclusion** : ρ ∈ [1.0 ; 1.9] est couvert par des données publiées non
   abusives — le segment [1.0 ; 1.1] correspondant au quasi-neuf et
   [1.1 ; 1.9] à la lecture visuelle DTU ci-dessus ; la portion
   **(1.9 ; 2.0] est une marge conservative explicite**, située au-dessus du
   documenté non abusif et nettement en dessous du documenté abusif (3×).
   Elle est déclarée comme marge, pas comme mesure.

La borne haute 2.0 est un choix de couverture bibliographique, pas un choix
orienté résultat.

### 7.2 Éléments fixes (tables sourcées — GELÉS : audit v0.5, consolidation v0.6)

**A. OCV(SoC)** — table `data/ocv_soc_ncr18650b_hnei.csv`

- Source exacte : rapport HNEI (source 8), Figure 6, cellule 103, moyenne
  charge/décharge à C/25 (quasi-OCV), température ambiante — spécifique
  NCR18650B.
- Numérisation reproductible : rendu PDF 200 dpi ; boîte d'axe
  x[389,1366] px = SOC[0,100] %, y[1051.5,1472.5] px = V[4.2,2.6] V ;
  extraction des pixels dominants bleus (B−R > 50, B > 120) restreinte à la
  boîte d'axe ; médiane du faisceau dans une fenêtre ±3 px ; pas de 2 % SOC
  → **51 points**. Précision ±10 mV.
- **Segment SoC < 2 % — règle GELÉE (v0.5)** : scan fin vérifié (pas 0.5 %,
  fenêtre ±1 px) : le segment est raide mais monotone et sans discontinuité
  (0 % → 2.81–2.83 V ; 0.5 % → 2.96 ; 1 % → 3.05 ; 2 % → 3.17 V). Aucune
  erreur objective : la table est **inchangée** et la règle reste
  l'interpolation linéaire uniforme sur les 51 points — aucun traitement
  spécial, aucune extrapolation. Incertitude locale ±0.1 V déclarée
  (segment quasi vertical : la médiane du faisceau varie de 23 mV selon la
  fenêtre ±1/±3 px). Cette zone ne pourra jamais être ajustée après
  observation de résultats P4b.
- **Règle hors domaine SoC — GELÉE (v0.6)** : la plante gelée ne sature pas
  soc (S6) ; soc(t) peut sortir de [0 ; 1] en charge forte ou en décharge
  profonde, y compris à l'intérieur du scénario. Règle pré-data : le calcul
  se poursuit avec **clamp des tables** (OCV, Rs, Rp, Cp évalués à la borne
  la plus proche) et l'événement {soc(t) ∉ [0 ; 1]} est enregistré comme
  drapeau « **hors domaine physique du modèle** » (premier instant et durée
  cumulée ; soc < 0 = sur-décharge au-delà de la validité du modèle). Ce
  drapeau marque une **limite de validité du modèle** — il n'est pas un
  résultat physique ; son traitement statistique (exclusion, censure ou
  reporting) est transféré comme obligation au préenregistrement P4b
  (§11.2).
- Audit v0.5 : calibration vérifiée par ticks d'axes (4.2 V → 1051.5 px ;
  2.6 V → 1472.5 px ; ±2 px ≈ ±6 mV) ; ré-extraction identique au CSV
  (écart max 0 mV) ; monotonie stricte vérifiée ; épaisseur du trait
  médiane 3 px (≈ ±3 mV). Incertitude totale : **±10 mV** hors segment
  SoC < 2 %, **±0.1 V** dans ce segment.
- Interpolation : **linéaire** entre points. Extrait : 0 % → 2.834 V ;
  10 % → 3.349 ; 20 % → 3.476 ; 35 % ≈ 3.58 ; 50 % → 3.676 ; 70 % → 3.864 ;
  100 % → 4.179 V.

**B. Paramètres Thevenin Rs(SoC), Rp(SoC), Cp(SoC)** — table
`data/rint_soc_nmc_dtu.csv`

- Source exacte : Thingvad et al. (source 9), Fig. 6A (Rs), Fig. 7A (Rp),
  Fig. 8A (Cp), **set A (cellules neuves), 23 °C**, test C : décharge CC 1C
  par pas de 0.3 Ah avec relaxation de 20 min. Définitions de mesure de la
  source : **Rs = chute ohmique immédiate** (tension sous charge vs tension
  1 s après coupure du courant) ; **Rp-Cp = polarisation transitoire**
  (relaxation après coupure).
- Définition du modèle : **Thevenin d'ordre 1 explicite** (option A de
  l'audit, §5) — pas de réduction Rs+Rp instantanée. Vérification
  analytique pré-data : τ = Rp·Cp mesuré entre **86 et 338 s** sur la table
  corrigée, soit **τ/900 ∈ [0.10 ; 0.38]** ; en fin de fenêtre payload Vp
  atteint 93.0–100 % de son asymptote à ρ = 1 (73.6–99.5 % à ρ = 2), mais à
  t = 0⁺ Vp = 0. L'ordre 0 aurait donc surestimé la chute en début de
  fenêtre de jusqu'à I_cell·ρ·Rp (≈ 90–299 mV à ρ = 2 et I_cell = 2.25 A
  selon SoC) : approximation susceptible de biaiser l'endpoint min_t V →
  rejetée.
- Rôle de ρ : multiplie **Rs et Rp** (croissance des résistances avec
  l'âge, sources 9, 11, 12, 13). **Cp n'est pas scalé** — choix
  expérimental pré-data déclaré : aucune de nos sources ne fournit de
  scaling robuste de Cp avec l'âge (le set B DTU n'a pas pu être tabulé,
  ci-dessous) ; l'effet d'un scaling éventuel de Cp sur τ resterait de
  second ordre pour l'endpoint (τ ∈ [0.10 ; 0.75]×900 s sur tout le
  domaine ρ ∈ [1 ; 2]).
- Numérisation reproductible : rendu PDF 200 dpi ; valeur = **p35** du
  faisceau de pixels dans une fenêtre ±3 px (médiane aussi fournie dans le
  CSV pour transparence). Calibrations **vérifiées en v0.5** par gridlines,
  labels d'axes et axes solides : Fig. 6A : x = 221 + 58.0 px/10 %,
  y(140 mΩ) = 1173, y(20 mΩ) = 1350 (axe solide) ; Fig. 7A : x = 940 +
  58.67 px/10 %, y(0) = 443 (axe solide), y(80 mΩ) = 263 (grille 45 px/20 mΩ) ;
  Fig. 8A : x = 931 + 6.15 px/%, y(0) = 1245, y(20 kF) = 1095 (sous-grille
  15 px/2 kF), rectangle de légende exclu. Précision : ±3 mΩ (Rs, Rp),
  ±1.0 kF (Cp).
- **Correction v0.5 (erreur objective démontrée)** : les calibrations y des
  Fig. 7A/8A de la v0.3 étaient erronées (Rp : y(80)=273.3, 148 px/80 mΩ ;
  Cp : y(0)=1243, y(20)=1112) → Rp sous-estimé de 2.5–8 mΩ, Cp surestimé
  de ~7–13 %. Ré-extraction avec calibrations vérifiées ; valeurs
  corrigées dans le CSV. Rs et OCV : ré-extraction **identique** (écart
  ≤ 1 px). Cette correction résulte de l'audit pré-data, avant toute
  simulation — aucun résultat P4b n'existe.
- **Défense de la convention p35 (audit v0.5, chiffres revérifiés v0.6)** :
  chaque marqueur est un faisceau de pixels (épaisseur du trait + 4 cellules
  superposées + anti-aliasing) ; p35 du faisceau est une convention de
  lecture **figée avant tout résultat**, appliquée uniformément aux trois
  séries et à tous les points, sans exception locale. La médiane est
  publiée dans le même CSV : l'écart p35/médiane est ≤ **2.0 mΩ** (Rs),
  ≤ **2.2 mΩ** (Rp), ≤ **0.6 kF** (Cp) — les deux conventions donnent la
  même table à l'incertitude de numérisation près (±3 mΩ / ±1.0 kF). p35
  n'est donc pas un levier de résultat.
- Défauts connus et déclarés : recouvrement de marqueurs à SOC = 10 %
  (écart médiane/p35) ; **Rp et Cp non mesurés à SOC = 100 %** (pas de
  marqueur Fig. 7A/8A).
- **Extension > 90 % — GELÉE (v0.5), justifications séparées (v0.6)** :
  Rp(SoC>90) = Rp(90), Cp(SoC>90) = Cp(90) (clamp). Pour **Rp** : la source
  déclare « Rp is stable for SOC above 25 % » (DTU) — clamp sourcé. Pour
  **Cp** : le clamp est une **règle méthodologique de clôture de frontière**,
  non tirée de la source. Dans les deux cas, le clamp n'invente aucun trend
  au-delà de la dernière mesure ; les alternatives (extrapolation linéaire,
  symétrie) introduiraient des données inexistantes. Choix indépendant de
  tout effet sur les violations.
- Extraits corrigés (p35) : Rs : 42.9 (0 %) → 38.2 (50 %) → 55.7 mΩ (100 %) ;
  Rp : 66.6 (0 %) → 26.7 (50 %) → 20.0 mΩ (90 %) ; Cp : 4.0 (0 %) →
  4.5 (50 %) → 14.1 (70 %) → 4.3 kF (90 %). τ = Rp·Cp : 86–338 s.
- **Statut du modèle — composite déclaré** : OCV issue du NCR18650B (HNEI)
  et paramètres Thevenin issus d'un NMC 18650 3.5 Ah (DTU) forment un
  **modèle électrochimique équivalent composite de cellule Li-ion 18650
  haute énergie**, qui ne constitue la qualification d'aucune chimie ni
  référence commerciale particulière. Toute frontière éventuelle de P4b
  sera une propriété du **modèle composite expérimental défini et gelé
  pour cette campagne** — ni une frontière générale des cellules NMC
  18650, ni une qualification spécifique du Panasonic NCR18650B. Une
  recherche de source Thevenin DC complète spécifique NCR18650B (Rs, Rp,
  Cp vs SoC) n'a pas abouti (§11).
- **Contrôle de cohérence** : le datasheet NCR18650B fournit une impédance
  AC à 1 kHz, tandis que la table DTU représente une résistance effective DC
  issue d'un modèle Thevenin. Ces deux grandeurs ne sont pas directement
  comparables quantitativement. **Le datasheet Panasonic n'est donc pas
  utilisé pour valider numériquement R_int,ref.** Contrôle de cohérence de
  même nature (DC/DC) à la place : le rapport HNEI (source 8, Table 1)
  mesure la **résistance ohmique** NCR18650B — chute de tension immédiate à
  l'application du courant, même type de grandeur que Rs — à **59.6 mΩ en
  moyenne (médiane 59.2, [56.3 ; 67.1], ~100 cellules neuves)**. Les Rs DTU
  set A (37–56 mΩ à 23 °C) sont du même ordre de grandeur, légèrement
  inférieurs (les auteurs HNEI notent eux-mêmes une contribution de la
  résistance de contact des supports). Cohérence satisfaisante pour un
  modèle composite.
- Set B (SOH 90 %) : **non tabulé** — deux tentatives de calibration de la
  numérisation ont échoué ; seule une lecture honnête en plage est retenue
  (SoC médian ~45–75 mΩ vs ~37–42 mΩ neuf → ρ ∈ [1.1 ; 1.9] lu
  visuellement, §7.1). Aucune valeur pseudo-précise n'est publiée.

**C. Topologie — pack équivalent continu (option B, GELÉE en v0.5)**

Audit critique (v0.5) : la règle v0.4 `nP = min(4, max(2, round(C_BATT /
3.35)))` rendait nP discret alors que C_BATT reste continu dans la dynamique
SoC — la capacité équivalente du pack (nP × 3.35 Ah) pouvait diverger de
C_BATT (ex. : C_BATT = 8 Ah → nP = 2 → 6.7 Ah équivalent), introduisant un
**second mismatch artificiel capacité/topologie** alors que P4b doit isoler
un seul mismatch structurel (tension terminale vs proxy SoC).

Options comparées (pré-data) :

| Option | Description | Verdict |
|---|---|---|
| A | nP discret + C_BATT arrondi à nP × 3.35 Ah | **Rejetée** : modifie la distribution nuisance historique C_BATT ∈ [4.4 ; 14.4] Ah (reprise inchangée de P4a, §7.3) |
| **B** | **C_BATT continu + nombre parallèle équivalent continu nP_eq = C_BATT / C_cell, utilisé uniquement pour le partage de courant** | **Retenue** : cohérence capacité/courant exacte par construction ; zéro mismatch ajouté ; distribution nuisance inchangée |
| C | Autre formulation (réseau discret complet avec cellules individuelles) | Rejetée : introduit le déséquilibre inter-cellules, explicitement exclu du périmètre (§9) |

Règle gelée :

```
nP_eq   = C_BATT / C_cell      (continu, C_cell = 3.35 Ah — source 3)
I_cell  = I_batt / nP_eq = I_batt · C_cell / C_BATT
```

Déclaration explicite : il s'agit d'un **modèle de pack équivalent continu** —
le courant par cellule est le courant de pack ramené au rapport des
capacités, ce qui **préserve exactement le taux-C** (taux-C cellule =
taux-C pack) pour toute valeur de C_BATT. Pour un nombre entier de branches
parallèles identiques, ce partage de courant est exact ; nP_eq continu
∈ [1.31 ; 4.30] sur le domaine nuisance est une **généralisation de modèle
équivalent**, non la description d'un pack physique à nombre fractionnaire
de branches. L'héritage COTS 2P–4P (source 4) a motivé le choix de la
capacité de référence C_cell = 3.35 Ah — héritage architectural, sans
constituer une contrainte dure ni la modélisation d'un produit COTS
particulier. N_S = 2 fixe (héritage CubeSat 6–8.4 V : sources 4, 5 ; proxy
du modèle figé). V_min,pack = N_S × V_min,cell = 2 × 2.5 = **5.0 V**
(§7.2-D).

**D. V_min par cellule — GELÉ (v0.6)**

- **2.5 V/cellule** — valeur primaire du datasheet NCR18650B (tension de fin
  de décharge, source 3), corroborée par la NASA (2.5–4.1/4.2 V, source 1)
  et par un seuil COTS primaire vérifiable : le verrouillage sous-tension
  **matériel non configurable** du GomSpace BP8 s'active à ≈ 2.44 V/cellule
  (typ) avec réarmement à ≈ 2.69 V/cellule (source 6) — le seuil de
  protection réel est donc au voisinage de 2.5 V/cellule, pas de 3.0 V.
- **3.0 V/cellule abandonné comme valeur primaire** : aucune source primaire
  précise ne le documente comme seuil de protection. Les seuils « critical
  battery » 3.25 V/cellule du GomSpace P80 (source 7) sont des seuils
  **logiciels configurables** de gestion opérationnelle — pas des
  protections ; ils ne peuvent pas servir de référence V_min.
- V_min,pack = 5.0 V (2S). Ce choix suit la hiérarchie des sources
  (datasheet primaire > pratique supposée) ; il n'a été influencé par aucun
  résultat — aucun n'existe en P4b (§10).

**E. État dynamique Vp et convention de courant — règles GELÉES (v0.5),
formulation précisée (v0.6)**

- Vp est un **état dynamique continu** du modèle Thevenin d'ordre 1 de la
  future plante P4b, évoluant selon
  `dVp/dt = −Vp / [ρ·Rp(SoC)·Cp(SoC)] + I_cell/Cp(SoC)` avec
  I_cell = I_batt·C_cell/C_BATT. Vp n'est **jamais remis à zéro** lors de
  l'entrée dans une fenêtre payload ; il évolue continûment pendant toute
  la durée du run.
- **Vp(t0) — règle gelée, convention quasi-stationnaire pré-data** : le
  scénario gelé démarre à t0 = 0 en début de phase lumière ; la phase
  précédant t0 est donc une éclipse (1800 s) sous courant bus seul (u = 0
  hors fenêtre [600 ; 1500] s). L'état initial retenu est l'**état
  quasi-stationnaire de cette éclipse pré-run, évalué à paramètres gelés en
  SoC0** :

  ```
  Vp(t0) = ρ · Rp(SoC0) · I_BASE · C_cell / C_BATT
  ```

  Nature de la règle (précision d'audit v0.6) : il s'agit d'une
  **convention quasi-stationnaire pré-data**, non d'une reconstruction de
  l'historique complet antérieur au run. Justification : dans le scénario
  gelé, le bus reste alimenté en permanence — Vp(t0) = 0 rejeté car
  physiquement incohérent avec ce scénario ; l'éclipse pré-run dure
  1800 s ≈ 2.7τ même au pire coin (τ = ρ·Rp·Cp ≤ 677 s à ρ = 2), donc le
  résidu de relaxation de tout état antérieur est ≤ e^(−1800/677) ≈ 7 % de
  l'asymptote ; Vp(t0) lui-même vaut au plus ≈ 32 mV au pire coin nuisance
  (I_BASE = 0.75 A, C_BATT = 4.4 Ah, SoC0 = 0.40, ρ = 2) → **ordre de
  grandeur du résidu ≈ 2 mV, sous l'hypothèse de paramètres localement
  constants pendant l'éclipse pré-run**. Cette estimation n'est **pas** une
  borne rigoureuse : SoC, donc Rp(SoC), évolue pendant l'éclipse
  (ΔSoC ≤ I_BASE·1800/(C_BATT·3600) ≈ 0.085 au pire coin). La règle est
  retenue comme convention déterministe, reproductible, fonction uniquement
  des nuisances tirés et des tables gelées. Alternative « point fixe
  périodique sur l'orbite » considérée et rejetée : complexité injustifiée
  au vu de l'ordre de grandeur du résidu.
- **Convention de courant — gelée** : I_batt = I_BASE + u − i_charge,
  signé, > 0 = décharge ; identité avec le code gelé
  `dsoc = (i_charge − I_BASE − u)/(C_BATT·3600) = −I_batt/(C_BATT·3600)`.
  Propagation du Thevenin au **courant signé** sur tout le domaine, sous la
  **forme signée unique** `V = OCV(SoC) − I_cell·ρ·Rs(SoC) − Vp`, qui n'est
  jamais réécrite automatiquement en valeurs absolues :
  - le signe du courant fixe le **signe de l'asymptote** de Vp
    (Vp → ρ·Rp·I_cell à SoC figé), **pas le signe instantané de Vp** : Vp
    est un état à mémoire — après une phase de charge, Vp < 0 peut persister
    en début de décharge, et réciproquement ;
  - I_batt > 0 (décharge) : I_cell > 0, l'asymptote de Vp est positive et
    la chute ohmique s'additionne à Vp ;
  - I_batt = 0 : relaxation libre dVp/dt = −Vp/(ρ·Rp·Cp) ;
  - I_batt < 0 (charge) : I_cell < 0, l'asymptote de Vp est négative ; le
    terme ohmique −I_cell·ρ·Rs = +|I_cell|·ρ·Rs **élève** la tension
    terminale, modulo la mémoire de Vp (positive à l'issue d'une décharge,
    elle se relaxe en ≈ τ ≤ 677 s à ρ = 2).
  Justification : le Thevenin est un circuit équivalent **linéaire** —
  l'extension au courant signé est l'extension minimale standard ;
  l'OCV HNEI est la moyenne des branches charge/décharge C/25, documentant
  un comportement quasi symétrique à faible régime pour la cellule de
  référence. **Limitation déclarée** : les paramètres DTU sont mesurés en
  décharge ; une asymétrie charge spécifique n'est pas modélisée.
  **Conséquence pour l'endpoint (v0.6)** : l'affirmation absolue « V < V_min
  ne peut pas se produire en charge » n'est **pas** retenue — la mémoire de
  Vp héritée d'une décharge antérieure peut maintenir transitoirement une
  tension basse en début de charge, et une cellule très déchargée entre en
  charge avec une OCV basse. L'endpoint min_t V_pack est donc évalué sur
  **toutes les phases du run**, sans exclusion de la charge. (Dans les
  tables gelées, OCV ≥ 2.83 V et le terme ohmique de charge est positif :
  un franchissement en charge serait un événement de marge faible —
  propriété numérique du modèle et de ses tables, pas un théorème
  physique.)

| Élément | Valeur/forme | Source | Statut |
|---|---|---|---|
| Topologie pack | 2S fixe ; **pack équivalent continu** nP_eq = C_BATT/3.35 (option B — pas de nP discret) | 3, 4, 6 | GELÉ v0.5 |
| OCV(SoC) | table 51 points NCR18650B (C/25 moyen), interpolation linéaire ; auditée (ré-extraction identique, monotone, ±10 mV / ±0.1 V sous 2 %) | 8 (`data/`) | GELÉ v0.5 |
| Rs(SoC), Rp(SoC), Cp(SoC) | Thevenin ordre 1 explicite, set A neuf 23 °C ; Rp/Cp **corrigés v0.5** (erreur de calibration démontrée) ; extension clamp 90 % gelée (Rp sourcé, Cp méthodologique) ; ρ multiplie Rs et Rp, Cp non scalé | 9 (`data/`) | GELÉ v0.5 |
| Vp(t0) | ρ·Rp(SoC0)·I_BASE·C_cell/C_BATT (convention quasi-stationnaire pré-data, éclipse pré-run) | scénario gelé + 9 | GELÉ v0.5 |
| Convention courant | I_batt = I_BASE + u − i_charge signé ; Thevenin bidirectionnel sous forme signée unique ; limitation charge déclarée ; endpoint évalué sur toutes les phases | code gelé + 9 | GELÉ v0.5 |
| Règle hors domaine SoC | clamp des tables + drapeau « hors domaine physique du modèle » ; traitement statistique transféré au préenregistrement (§11.2) | méthodologique | GELÉ v0.6 |
| Statut du modèle | **composite expérimental gelé** (OCV NCR18650B + dynamique Thevenin NMC 18650 ; frontière = propriété du modèle gelé, pas d'une chimie ni d'une référence commerciale) | 8, 9 | DÉCLARÉ + GELÉ |
| V_min par cellule | **2.5 V** (datasheet, corroboré COTS BP8 ≈ 2.44 V matériel) ; V_min,pack = 5.0 V | 1, 3, 6 | **GELÉ v0.6** |
| Température | 23–25 °C de référence pour R_int et OCV (couplage thermique exclu, §9) | — | figé par exclusion |

### 7.3 Paramètres nuisance

Reprise **inchangée** des plages P4a Phase 2 — justifiées à l'époque par la
littérature externe, avant tout résultat, donc indépendantes des résultats
P4a : C_BATT ∈ [4.4; 14.4] Ah ; I_SUN ∈ [0.8; 2.5] A ; I_BASE ∈ [0.06; 0.75] A ;
soc0 ∈ [0.40; 0.70] ; admissibilité R1/R2/R3 inchangées.

### 7.4 Distribution expérimentale proposée

Mesure de couverture uniforme sur une grille de niveaux de ρ englobant [1.0; 2.0]
(nombre et position exacts des niveaux : **PENDING**, à figer au
préenregistrement avant toute exécution — jamais retunés après observation).
Nuisances : tirage uniforme par blocs comme en P4a (structure approuvée),
conditions initiales et scénario P2.3 inchangés.

### 7.5 Endpoint (question de protocole, PAS de Phase 0)

L'endpoint naturel devient Y = 1{min_t V_pack(t) < V_min,pack} — l'aléa
physique réel — pendant que B continue de vérifier SoC ≥ 0.35 ; min_t est
évalué sur **toutes les phases du run**, charge incluse (§7.2-E). La
définition formelle de Y, les seuils εS/εF et tout le protocole statistique
relèvent de la Phase 3 P4b : **PENDING**.

### 7.6 Table finale des paramètres (consolidation v0.6)

| # | Paramètre | Valeur finale | Source / justification | Statut | Limitation |
|---|---|---|---|---|---|
| 1 | Mismatch étudié | tension terminale sous charge vs proxy SoC ≥ 0.35 | code gelé (C0) + audit §6.1 | GELÉ | — |
| 2 | Modèle plante | Thevenin ordre 1 explicite (§5) | source 9 + audit | GELÉ | ordre 1 uniquement |
| 3 | Statut du modèle | composite expérimental gelé | sources 8, 9 | DÉCLARÉ + GELÉ | frontière = propriété du modèle gelé |
| 4 | OCV(SoC) | table 51 pts, interpolation linéaire | source 8 (`data/`) | GELÉ v0.5 | ±10 mV ; ±0.1 V sous SoC 2 % |
| 5 | Segment OCV < 2 % | table inchangée, incertitude ±0.1 V déclarée | source 8 | GELÉ v0.5 | sensibilité à préenregistrer (§11.2) |
| 6 | Hors domaine SoC ∉ [0 ; 1] | clamp des tables + drapeau « hors domaine physique » | règle méthodologique | GELÉ v0.6 | traitement statistique : §11.2 |
| 7 | Rs(SoC) | p35, 42.9→38.2→55.7 mΩ | source 9 (`data/`) | GELÉ v0.5 | ±3 mΩ |
| 8 | Rp(SoC) | p35 corrigé, 66.6→26.7→20.0 mΩ | source 9 (`data/`) | GELÉ v0.5 | ±3 mΩ |
| 9 | Cp(SoC) | p35 corrigé, 4.0→4.5→4.3 kF | source 9 (`data/`) | GELÉ v0.5 | ±1.0 kF |
| 10 | Interpolation tables | linéaire | règle méthodologique | GELÉ v0.5 | — |
| 11 | Extension > 90 % | clamp Rp(90)/Cp(90) | source 9 (Rp) + méthodologique (Cp) | GELÉ v0.5 | Cp non sourcé : clôture de frontière |
| 12 | ρ | [1.0 ; 2.0] | sources 9, 11, 13 + marge déclarée | GELÉ (plage) ; grille = PENDING stat. | [1.1 ; 1.9] = lecture visuelle ; (1.9 ; 2.0] = marge |
| 13 | Scaling ρ | Rs,ρ = ρ·Rs ; Rp,ρ = ρ·Rp ; Cp,ρ = Cp | choix expérimental pré-data | GELÉ | pas une loi de vieillissement |
| 14 | C_cell | 3.35 Ah | source 3 | GELÉ | — |
| 15 | N_S | 2 | sources 4, 5 | GELÉ | proxy du modèle figé |
| 16 | Pack équivalent | nP_eq = C_BATT/C_cell continu | règle méthodologique | GELÉ v0.5 | modèle équivalent, pas un pack physique |
| 17 | I_batt | I_BASE + u − i_charge (signé) | code gelé | GELÉ v0.5 | — |
| 18 | I_cell | I_batt·C_cell/C_BATT | dérivé de 14, 16, 17 | GELÉ v0.5 | — |
| 19 | Vp | EDO ordre 1, jamais remis à zéro | source 9 + méthodologique | GELÉ v0.5 | mesuré en décharge uniquement |
| 20 | Vp(t0) | ρ·Rp(SoC0)·I_BASE·C_cell/C_BATT | scénario gelé + source 9 | GELÉ v0.5 | convention quasi-stationnaire, ordre de grandeur |
| 21 | V_min cellule | 2.5 V | sources 3 (primaire), 1, 6 | **GELÉ v0.6** | limite datasheet, pas seuil ECSS |
| 22 | V_min pack | 5.0 V | dérivé de 15, 21 | **GELÉ v0.6** | — |
| 23 | Température | 23–25 °C de référence | sources 8, 9 | figé par exclusion | couplage thermique : §9 |
| 24 | Exclusions | taper CC/CV, thermique, déséquilibre, Peukert, fade dynamique, auto-décharge, rendement, hystérésis, bruit SoC P4a | §9 | GELÉ | taper : justification honnête §9 |

---

## 8. Hypothèses PROPOSÉES (pour préenregistrement — Phase 3, non autorisée)

**H_P4b-frontière** : Dans un domaine préenregistré de mismatch structurel
physiquement plausible, la probabilité de violation de B présente une
transition reproductible d'une région où B reste opérationnellement suffisant
vers une région où cette suffisance n'est plus garantie.

**H_P4b-mécanisme** : Si cette transition apparaît, sa localisation est
attribuable au mismatch physique structurel testé et non au bruit numérique,
au pas de simulation ou à une anomalie logicielle.

---

## 9. Exclusions explicites

- Couplage température → énergie (R_int(T), capacité(T)) : candidat P4b.2 ;
  ici R_int et OCV à 23–25 °C de référence.
- Fade dynamique intra-mission (négligeable sur 2.5 orbites) ; le fade statique
  reste couvert par le nuisance C_BATT.
- Effet régime-capacité au-delà du modèle R-int (Peukert rejeté, §6.2).
- **Taper de charge CC/CV** : non modélisé. La justification « hors zone
  opérée » est **retirée** (soc0 ∈ [0.40 ; 0.70] est une condition initiale ;
  soc(t) peut croître au-delà en phase lumière, le code gelé ne saturant pas
  soc — S6). Justification retenue : le chargeur du modèle gelé est à courant
  constant (I_SUN binaire) et P4b ne modifie aucun élément du code gelé ;
  l'effet attendu d'un taper réel (réduction du courant à SoC haut → moindre
  recharge) est déclaré non modélisé, **sans borne d'effet sur l'endpoint
  revendiquée**.
- Déséquilibre inter-cellules (pack = cellule équivalente ; noté aggravant
  possible, non modélisé).
- Auto-décharge, rendement coulombique < 1, hystérésis/relaxation OCV.
- Bruit d'estimation SoC de P4a : non réintroduit ici (P4b isole le mismatch
  structurel ; interaction biais×structure = campagne ultérieure éventuelle).
- Aucune modification de B, de C/D, de τ_arm, du guard, ni du scénario P2.3.

---

## 10. Contrôle anti-post-hoc

| Vérification | État |
|---|---|
| Aucun seuil P4b ne provient des 21 blocs défaillants de l'annexe P4a | ✅ — V_min, ρ, OCV, R_int, topologie proviennent exclusivement des sources §3 ; l'annexe P4a n'a servi à rien ici |
| Aucune borne choisie parce qu'elle devrait produire des violations | ✅ — V_min = 2.5 V suit la hiérarchie des sources (datasheet primaire > pratique supposée) ; il **éloigne** le seuil de la zone opérée, sens inverse d'un choix orienté violation ; l'illustration §6.4 montre que l'issue reste réellement incertaine |
| ρ_max justifié indépendamment | ✅ — [1.1 ; 1.9] lu visuellement sur données non abusives (DTU, étiqueté lecture en plage) ; 1.37× max mesuré par Hein (pas 2.0) ; portion (1.9 ; 2.0] étiquetée marge conservative, bornée par le documenté abusif (3×, Wang) |
| Aucun paramètre ajusté après observation d'un résultat P4b | ✅ — aucune simulation P4b n'existe ; rien n'a pu être observé |
| Aucune simulation scientifique P4b exécutée | ✅ — Phase 0 = audit + bibliographie + numérisation de données publiées ; §6.4 est une illustration analytique pré-data (lecture directe des tables sourcées), pas une simulation du système |
| Choix du modèle Thevenin orienté résultat ? | ✅ — option A (ordre 1 explicite) choisie sur un argument physique pré-data (τ/900 ∈ [0.10 ; 0.38], biais potentiel de l'endpoint) formulé par l'audit **avant** toute simulation ; l'option retenue **réduit** la chute calculée en début de fenêtre, sens inverse d'un choix orienté violation |
| Hétérogénéité des cellules | ✅ — choix B déclaré : modèle composite expérimental gelé (OCV NCR18650B + dynamique Thevenin NMC 18650), frontière = propriété du modèle gelé uniquement ; la recherche d'une source spécifique NCR18650B a été menée **avant** la décision et n'a pas abouti ; aucun remplacement ne pourra avoir lieu après observation d'un résultat |
| Comparaison AC/DC | ✅ — supprimée partout ; le datasheet Panasonic ne valide pas numériquement R_int,ref ; contrôle DC/DC de même nature (HNEI Table 1) à la place |
| Correction Rp/Cp v0.5 orientée résultat ? | ✅ — erreur de calibration **objective** démontrée par gridlines/labels/axes de la source ; trouvée en audit pré-data alors qu'aucune simulation P4b n'existe ; son effet (Rp corrigé à la hausse) n'a joué aucun rôle dans la décision de corriger |
| Topologie option B orientée résultat ? | ✅ — choisie sur un argument de cohérence interne (éliminer un second mismatch capacité/topologie) et de conservation de la distribution nuisance historique ; aucun résultat P4b n'existe |
| Vp(t0) choisi pour simplifier ? | ✅ — Vp(t0) = 0 rejeté car physiquement incohérent avec le scénario gelé (bus alimenté en permanence) ; la règle retenue (convention quasi-stationnaire de l'éclipse pré-run) est **plus** complexe et physiquement motivée |
| Corrections v0.6 orientées résultat ? | ✅ — toutes issues d'une relecture d'audit pré-data ; la correction §6.4 (3.5 A → 2.95 A) **réduit** le courant et la chute calculée, sens inverse d'un choix orienté violation ; les reformulations (signe de Vp, charge, taper) retirent des affirmations trop favorables au mécanisme, ne en ajoutent aucune |
| Choix du mécanisme influencé par les résultats P4a ? | Déclaration honnête : P4a a motivé la **question générale** (« quel mismatch structurel peut faire cesser B de suffire ? ») — c'est la progression scientifique du projet. Mais le mécanisme retenu est le seul à la fois absent du modèle, adossé à l'aléa physique réel de C0 (proxy écrit dans le code depuis P0), et bornable par données publiées. Aucun chiffre P4a (seuils, blocs, marges) n'entre dans D_physique_P4b |

---

## 11. État de validation et points PENDING

### 11.1 Validé / gelé — à ne plus rouvrir

Validé en principe (audit v0.3) :

- mismatch structurel tension terminale réelle vs proxy SoC ;
- modèle Thevenin d'ordre 1 ;
- utilisation de Rs(SoC), Rp(SoC) et Cp(SoC) ;
- rejet du modèle d'ordre 0 Rs+Rp instantané ;
- séparation explicite entre impédance AC 1 kHz et résistance DC Thevenin ;
- approche composite OCV NCR18650B + dynamique Thevenin NMC 18650, avec
  statut exact : frontière = propriété du modèle composite expérimental
  gelé, pas d'une chimie ni d'une référence commerciale ;
- ρ comme facteur expérimental de scaling résistif, non comme loi
  universelle de vieillissement ;
- aucun recours aux 21 blocs P4a ; aucun résultat P4b existant.

Gelé en v0.5 (clôture des PENDING physiques) :

- tables OCV / Rs / Rp / Cp auditées contre leurs sources primaires
  (calibrations vérifiées par gridlines/labels/axes ; ré-extraction OCV et
  Rs identique ; **Rp et Cp corrigés** après erreur objective démontrée) ;
- règle d'extension Rp/Cp au-delà de 90 % (clamp ; Rp soutenu par la source,
  Cp = règle méthodologique de clôture de frontière — précision v0.6) ;
- traitement du segment OCV < 2 % (table inchangée, interpolation linéaire
  uniforme, incertitude déclarée) ;
- Vp(t0) = ρ·Rp(SoC0)·I_BASE·C_cell/C_BATT (convention quasi-stationnaire
  pré-data de l'éclipse pré-run) ;
- convention de courant signé I_batt = I_BASE + u − i_charge, Thevenin
  bidirectionnel sous forme signée unique avec limitation charge déclarée ;
- topologie pack équivalent continu nP_eq = C_BATT/C_cell (option B — le
  mismatch capacité/topologie potentiel est éliminé) ;
- références ECSS vérifiées sur texte source (E-ST-20C Rev.2 §5.7.3
  exigences h et i ; E-HB-20-02A handbook méthodologique).

Gelé en v0.6 (audit final exhaustif) :

- **V_min = 2.5 V/cellule, V_min,pack = 5.0 V** ;
- **règle hors domaine SoC** (clamp + drapeau « hors domaine physique ») ;
- formulation du signe de Vp (asymptote ≠ instantané) et retrait de
  l'absolu « pas de sous-tension en charge » ;
- endpoint min_t V_pack évalué sur toutes les phases du run ;
- hiérarchie des sources corrigée (4 → C, 13 → B) ;
- table finale des paramètres (§7.6) ; statuts unifiés.

### 11.2 Points encore PENDING (tous statistiques — Phase 3, non autorisée)

1. Grille exacte de ρ.
2. Endpoint statistique formel Y.
3. εS et εF.
4. N et mesure de couverture.
5. Seeds.
6. Contrôles de reproductibilité.
7. Protocole statistique complet.
8. Interaction biais d'estimation × mismatch structurel : explicitement
   remise à une campagne ultérieure.
9. **Traitement statistique du drapeau « hors domaine physique du modèle »**
   (soc(t) ∉ [0 ; 1]) : exclusion, censure ou reporting — à décider et
   préenregistrer (règle de calcul gelée en §7.2-A).
10. **Analyse de sensibilité à l'incertitude OCV locale (±0.1 V, SoC < 2 %)** :
    obligation déclenchée pré-data par l'illustration §6.4 (franchissement
    illustratif situé à SoC ≲ 0.6 %, dans ce segment) — à préenregistrer si
    la frontière éventuelle s'y situe, avant toute conclusion sur cette zone.

---

## 12. Verdict d'audit final

**PHYSICAL MODEL STATUS : READY FOR PREREGISTRATION — FINAL PHYSICAL FREEZE APPROVED**

Après audit exhaustif de la v0.6, aucun PENDING physique identifié ne
subsiste. Toute modification ultérieure du modèle physique est interdite,
sauf découverte documentée d'une erreur objective indépendante des
résultats P4b.

Aucune incohérence ou erreur matérielle identifiée après l'audit exhaustif
défini ci-dessus — les 26 constats de l'audit (`P4B_PHASE0_FINAL_AUDIT_v0.6.md`)
sont tous corrigés dans la présente v0.6 ou transférés explicitement comme
obligations de préenregistrement (§11.2, points 9 et 10). Les points restants
sont exclusivement statistiques et relèvent de la Phase 3, non autorisée à ce
stade.

**STOP.** Aucune grille ρ, aucun endpoint statistique, aucune seed, aucune
simulation scientifique P4b, aucun préenregistrement et aucun commit de gel
ne sont autorisés par ce seul livrable.
