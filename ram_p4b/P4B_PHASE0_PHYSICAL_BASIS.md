# P4b — PHASE 0 : JUSTIFICATION PHYSIQUE INDÉPENDANTE

**Version 0.5 — CLÔTURE DES PENDING PHYSIQUES (2026-09-10).**
Audit intégral des tables + gel des règles physiques restantes, sans aucune
simulation, grille, seed ni seuil statistique :

1. **Erreur objective de numérisation démontrée et corrigée** : les
   calibrations y des Fig. 7A (Rp) et 8A (Cp) de la v0.3 étaient erronées
   (v0.3 : y(80 mΩ)=273.3 px, 148 px/80 mΩ ; vérifié : y(0)=443 px axe
   solide, y(80)=263 px, grille 45 px/20 mΩ ; Fig. 8A : vérifié y(0)=1245,
   y(20)=1095, sous-grille 15 px/2 kF). **Rp et Cp ré-extraits** et
   corrigés dans `data/rint_soc_nmc_dtu.csv` ; Rs et OCV ré-extraits
   identiques (écart ≤ 1 px). Correction documentée en §7.2-B — trouvée
   par l'audit pré-data, avant toute simulation.
2. **Extension >90 % gelée** : clamp Rp(SoC>90)=Rp(90), Cp(SoC>90)=Cp(90) —
   soutenu par la source (DTU : « Rp is stable for SOC above 25 % »), aucun
   trend inventé.
3. **OCV < 2 % gelé** : table inchangée, interpolation linéaire uniforme,
   scan fin 0–4 % vérifié (segment raide monotone, sans discontinuité) ;
   incertitude locale ±0.1 V déclarée ; clamp aux bornes de la table hors
   [0 ; 100 %].
4. **Vp(t0) gelé** : état quasi-stationnaire de la phase orbitale précédant
   t0 (éclipse, bus seul) — équation exacte en §7.2-E.
5. **Convention de courant gelée** : I_batt = I_BASE + u − i_charge (signé,
   > 0 = décharge), cohérent avec le code gelé ; Thevenin propagé au courant
   signé ; limitation déclarée (§7.2-E).
6. **Topologie corrigée (option B)** : nP discret abandonné — risque de
   second mismatch capacité/topologie identifié par l'audit ; remplacé par
   le modèle de pack équivalent continu nP_eq = C_BATT/C_cell (§7.2-C).
7. **ECSS vérifié sur texte source** : ECSS-E-ST-20C Rev.2 supporte
   verbatim l'affirmation architecturale (exigence « ultimate over
   charging/discharging protection … hardware … independent from any on
   board software », §5.7.3) ; ECSS-E-HB-20-02A confirmé handbook
   méthodologique. Aucune valeur numérique attribuée. Conservées.

**Version 0.4 — AMENDEMENT PRÉ-DATA 3 (2026-09-10).**
Quatre précisions d'audit intégrées, sans modifier les données OCV/Thevenin
ni choisir grille, seeds ou seuils statistiques :

1. **Statut exact du modèle composite** (§5, §7.2-B) : modèle
   électrochimique équivalent composite — OCV–SoC issue du NCR18650B,
   paramètres dynamiques Thevenin issus de cellules NMC 18650. Toute
   frontière éventuelle de P4b sera une propriété du **modèle composite
   expérimental défini et gelé pour cette campagne** — ni une frontière
   générale des cellules NMC 18650, ni une qualification du Panasonic
   NCR18650B.
2. **Interprétation exacte de ρ** (§7.1) : facteur expérimental de scaling
   résistif / proxy de dégradation résistive — pas une loi universelle
   SOH↔résistance.
3. **Définition exacte de l'aléa de sous-tension** (§5) : V_pack < 5.0 V ;
   les protections COTS documentées démontrent la pertinence
   architecturale de l'aléa, sans être un modèle exact du déclenchement
   d'un pack 2S P4b.
4. **État dynamique Vp et condition initiale** (§7.2-E) : Vp est un état
   continu, initialisé une seule fois par run selon une règle pré-data à
   geler (PENDING), jamais remis à zéro en entrée de fenêtre payload ;
   la convention Vp = 0 du §6.4 est un calcul illustratif relaxé,
   pas une règle d'initialisation ; convention de charge (I_batt < 0)
   PENDING.

**Version 0.3 — AMENDEMENT PRÉ-DATA 2 (2026-09-10).**
Corrections suite à l'audit final de la v0.2 :

1. **Comparaison AC/DC supprimée** : l'impédance AC 1 kHz du datasheet
   NCR18650B n'est plus utilisée pour valider numériquement R_int,ref
   (§7.2-B). Remplacée par un contrôle de cohérence de même nature (DC/DC) :
   résistance ohmique NCR18650B du rapport HNEI (Table 1).
2. **Thevenin ordre 1 explicite retenu** (option A de l'audit) : la réduction
   R_int = Rs + Rp instantanée est abandonnée. τ = Rp·Cp mesuré entre 51 et
   294 s, soit τ/900 ∈ [0.06 ; 0.32] — NON « << 900 s ». Cp est désormais
   sourcé (DTU Fig. 8A) et interpolé ; équations exactes en §5 et §7.2-B.
3. **Modèle composite déclaré** (choix B de l'audit) : P4b n'est PAS un
   modèle spécifique NCR18650B ; c'est un modèle composite représentatif
   d'une cellule NMC 18650 haute énergie (§7.2-B). Toute frontière
   éventuelle sera celle de cette classe expérimentale. *(Formulation
   précisée en v0.4 : la frontière est une propriété du modèle composite
   expérimental gelé, pas d'une classe de cellules générale.)*

**Version 0.2 — AMENDEMENT PRÉ-DATA 1 (2026-09-10).**
Amendements suite à l'audit de la v0.1 (concept et mismatch validés) :

1. V_min : 3,0 V/cellule abandonné comme valeur primaire (aucune source primaire
   précise) ; 2,5 V/cellule (datasheet) proposé, corroboré par une source COTS
   primaire (GomSpace BP8, verrouillage matériel non configurable).
2. ρ_max : la valeur 2,0 n'est plus attribuée à Hein et al. ; justification
   en couches avec marge conservative explicitement étiquetée (§7.1).
3. Références ECSS ajoutées : ECSS-E-ST-20C Rev.2 (8 avril 2022) et
   ECSS-E-HB-20-02A (1er octobre 2015), utilisées uniquement pour les
   affirmations qu'elles supportent. ECSS-E-ST-20-06 n'est PAS utilisée.
4. Modèle physique reproductible : tables numériques sourcées OCV(SoC) et
   paramètres Thevenin fournies (`data/`), méthode de numérisation documentée,
   règle de topologie 2S-nP explicite.
5. Aucun résultat de simulation introduit ; aucun choix ne vise une classe de
   verdict ; aucun lien avec les 21 blocs de l'annexe P4a.

**Statut : PROPOSÉ — en attente d'audit. Aucun code de campagne, aucun design,
aucune seed, aucune simulation P4b. Ce document ne modifie rien de l'existant.**

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
| S6 | Pas de saturation de `soc` dans la plante | surcharge possible dans la plante (hors champ du scénario) |
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
| P6 | Taper de charge CC/CV à SoC haut | Non (S4) | Oui | **Négligeable** : la zone opérée (SoC ≤ 0.70) reste en régime CC | Oui | Oui |
| P7 | Déséquilibre cellules d'un pack (la plus faible atteint V_min la première) | Non (S7) | Oui | Modérée ; se subsume en facteur aggravant de P1 | Difficile seul | Partiellement |
| P8 | Auto-décharge | Non | Non (paramétrique) | **Négligeable** : 1–3 %/mois vs 2.5 orbites | Oui | Oui |
| P9 | Rendement coulombique < 1 | Non | Non (paramétrique) | Faible : 1–2 %, absorbé par le bruit/nuisance | Oui | Oui |
| P10 | Hystérésis/relaxation OCV | Non | Oui | Faible : quelques mV à quelques dizaines de mV | Difficile | Partiellement |

---

## 3. Sources (hiérarchie A : constructeur/agence ; B : littérature revue ;
C : technique secondaire)

1. **NASA NTRS — « Nano Satellite Electrical Power Systems »** (A) :
   « Li-Ion exhibits a highly non-linear relationship between cell voltage and
   state of charge (SoC) » ; « Cell voltage should be maintained between
   2.5 V to 4.1 V or 4.2 V » ; « As cells age, their internal resistance
   increases, reducing their output power » ; packs 2S ~7.2 V à base de 18650.
   https://ntrs.nasa.gov/api/citations/20240007136/downloads/Nano%20Satellite%20Electrical%20Power%20Systems%20Revised.pdf
2. **NASA SmallSat Institute — State of the Art, Power** (A) : état de
   l'art PMAD/batteries smallsats.
   https://www.nasa.gov/smallsat-institute/sst-soa/power-subsystems/
3. **Panasonic NCR18650B — datasheet** (A) : 3350 mAh typique (3200 nominal
   min), tension nominale 3.6 V, **tension de fin de décharge 2.5 V**,
   impédance AC ≤ 100 mΩ (1 kHz), courant de décharge continu max 4.875 A,
   courbes de décharge 0.2/0.5/1/2 C et en température (−20…+60 °C).
   https://www.tme.eu/Document/3e0170a1e089819f286f7066e69035b4/NCR18650B.pdf
4. **GomSpace NanoPower BP4 / BPX / P31u** (A) : packs CubeSat 18650 —
   BP4 2P-2S « 6–8.4 V & 5.2 Ah », BPX 2S-4P « 6–8.4 V & 10.4 Ah » ;
   « Battery under-voltage and over-voltage protection » (P31u).
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
    (capacités résiduelles 71–92 %). Hein démontre directement une croissance
    de l'ordre de **1.37× maximum**, rien au-delà.
    https://upcommons.upc.edu/bitstreams/9be40c44-cf51-414a-b6ac-ae5047e17173/download
12. **Wheeler et al. 2025 — vieillissement 20 cellules 18650 LFP (Sci.
    Data)** (B) : impédance plus élevée à 0 % de SoC qu'à 50/100 % ;
    croissance des résistances série et de transfert avec l'âge.
    https://pmc.ncbi.nlm.nih.gov/articles/PMC11885844/
13. **Revue de dégradation Li-ion, MDPI Energies 2025** (A) : synthèse de
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
    valeur numérique n'en est extraite.**
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
| P6 — Taper de charge CC/CV | C | Hors zone opérée (SoC ≤ 0.70) |
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
avec  V_min,pack = N_S · V_min,cell = 2 × 2.5 V = 5.0 V
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
Vp(t0) et convention de charge : PENDING (§7.2-E).

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
  (Rs 37–56 mΩ, Rp 12–68 mΩ, Cp 3.8–15.1 kF selon SoC, table §7.2-B) ;
  cohérence DC/DC avec la résistance ohmique NCR18650B du rapport HNEI
  (59.6 mΩ moyenne, §7.2-B) ; croissance avec l'âge jusqu'à ~1.9×
  documentée à SOH 90 % (§7.1).
- **Interprétabilité** : « l'enveloppe surveille un proxy ; la réalité déclenche
  sur la tension sous charge » — phrase unique, mécanisme complet.
- **Domaine définissable avant simulation** : toutes les bornes proviennent de
  datasheets/littérature (§7).
- **Pertinence RA** : c'est le cœur du concept « Runtime-Assured Autonomous
  Satellite » — une couche légère qui vérifie un proxy suffit-elle quand
  l'aléa réel est une autre grandeur physique ?

### 6.4 Faisabilité physique — ordre de grandeur (données sourcées §7.2, PAS une simulation)

Cas défavorable du domaine nuisance (pack équivalent, §7.2-C option B) :
C_BATT = 4.4 Ah → I_cell = 3.5 A × 3.35/4.4 = **2.66 A** (0.80 C, sous la
limite 4.875 A du datasheet 3). Lecture directe des tables corrigées v0.5
avec le modèle ordre 1 (§5), à ρ = 2 — en distinguant le **début de
fenêtre** (t = 0⁺ : Rs seul agit, Vp = 0) et la **fin de fenêtre**
(t = 900 s : Vp ≈ I·ρ·Rp·(1−e^(−900/τ))) :

| SoC plante | OCV (V) | Rs (mΩ) | Rp (mΩ) | Cp (kF) | τ à ρ=2 (s) | ΔV t=0⁺ (mV) | ΔV t=900 s (mV) | V_cell t=900 s (V) |
|---|---|---|---|---|---|---|---|---|
| 0.35 | 3.58 | 38.5 | 26.1 | 4.8 | 254 | 205 | 341 | 3.24 |
| 0.20 | 3.48 | 40.9 | 28.0 | 7.1 | 398 | 218 | 352 | 3.12 |
| 0.10 | 3.35 | 43.1 | 40.9 | 6.2 | 507 | 230 | 411 | 2.94 |
| 0.02 | ≈ 3.16 | 42.9 | 61.5 | 4.4 | 546 | 229 | 493 | 2.67 |
| 0.00 | ≈ 2.83 | 42.9 | 66.6 | 4.0 | 533 | 229 | 518 | 2.32 |

Lecture : la part transitoire (Vp) contribue ~30–55 % de la chute totale
en fin de fenêtre — un modèle ordre 0 appliquant Rs+Rp instantanément
l'aurait comptée dès t = 0, d'où le rejet de cette approximation (§6.2).
Le franchissement de 2.5 V/cellule ne se produit qu'au voisinage du coude
de fin de décharge (SoC ≲ 1–2 %), dans la zone où l'incertitude OCV
locale est ±0.1 V (§7.2-A) — déclaré, non retuné.

**Convention du tableau** : les colonnes t = 0⁺ / t = 900 s supposent Vp = 0
à l'entrée de la fenêtre, c'est-à-dire un **état initial relaxé**. C'est un
calcul analytique illustratif uniquement : il ne définit pas l'initialisation
de la future campagne P4b et ne doit pas être interprété comme une remise à
zéro de la polarisation à chaque fenêtre payload (règle Vp : §7.2-E).

Conséquence honnête : **on ne sait pas d'avance si le domaine contient des
violations**. Avec V_min = 2.5 V/cellule (datasheet), la tension ne franchit le
seuil qu'au voisinage du coude de fin de décharge (SoC ≈ 0–3 %), très en
dessous du guard SoC 0.35 du moniteur : la question « le proxy SoC suffit-il »
reste entièrement ouverte, et les deux issues sont scientifiquement valables.
Aucun paramètre n'a été choisi pour provoquer ni pour exclure ce franchissement
(§10).

---

## 7. Proposition D_physique_P4b (non implémentée)

### 7.1 Facteur expérimental unique

| Variable | Symbole | Unité | Plage proposée | Justification des bornes |
|---|---|---|---|---|
| Facteur expérimental de scaling résistif | ρ | sans dimension | **[1.0 ; 2.0]** | Voir justification en couches ci-dessous |

**Interprétation exacte de ρ** (précision d'audit, v0.4) : ρ est un facteur
expérimental de scaling résistif / proxy de dégradation résistive :

```
Rs,ρ(SoC) = ρ · Rs,ref(SoC)
Rp,ρ(SoC) = ρ · Rp,ref(SoC)
Cp,ρ(SoC) = Cp,ref(SoC)
```

ρ n'est **pas** interprété comme une loi universelle reliant directement SOH
et résistance. Il paramètre uniquement l'amplitude du mismatch résistif
étudié, avec des bornes justifiées indépendamment par les données de
vieillissement disponibles (ci-dessous). Le scaling commun de Rs et Rp et
l'absence de scaling de Cp constituent des **choix expérimentaux pré-data**
du modèle P4b ; ils ne prétendent pas reproduire une loi électrochimique
universelle de vieillissement.

Justification en couches de la borne haute ρ_max = 2.0 (aucune couche ne
suffit seule ; la marge est étiquetée comme telle) :

1. **Directement documenté, non abusif** : DTU (source 9), NMC 18650 à
   SOH 90 % (set B vs set A) : lecture honnête en plage, R_int,DC à SoC médian
   passant de ~37–42 mΩ (neuf) à ~45–75 mΩ → **ρ ∈ [1.1 ; 1.9]** documenté à
   SOH 90 %. (Numérisation du set B limitée : valeurs en plage visuelle
   vérifiée, pas de pseudo-précision — §7.2-B.)
2. **Directement documenté, sévère** : Hein et al. (source 11) : croissance
   jusqu'à **1.37× maximum** après 174 cycles 1C/1C sévères. ρ = 2.0 n'est
   **pas** attribué à Hein.
3. **Borne supérieure abusive** : revue MDPI Energies 2025 (source 13) :
   ≈ **3×** à 80 % SOH sous cyclage abusif 20C (Wang et al., LFP) ; +78 %
   après 2000 cycles en LFP modéré (Sony) ; +10 % après 3000 cycles en NMC
   ménagé (Samsung).
4. **Conclusion** : ρ ∈ [1.0 ; 1.9] est couvert par des données publiées non
   abusives ; la portion **(1.9 ; 2.0] est une marge conservative explicite**,
   située au-dessus du documenté non abusif et nettement en dessous du
   documenté abusif (3×). Elle est déclarée comme marge, pas comme mesure.

La borne haute 2.0 est un choix de couverture bibliographique, pas un choix
orienté résultat.

### 7.2 Éléments fixes (tables sourcées, PROPOSÉES — à valider à l'audit)

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
  fenêtre ±1/±3 px). Hors [0 ; 100 %] : clamp aux bornes de la table, avec
  drapeau « hors domaine caractérisé » (soc < 0 = sur-décharge au-delà de
  la validité du modèle). Cette zone ne pourra jamais être ajustée après
  observation de résultats P4b.
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
  analytique pré-data : τ = Rp·Cp mesuré entre **51 et 294 s** sur la table,
  soit **τ/900 ∈ [0.06 ; 0.32]** ; en fin de fenêtre payload Vp atteint
  95.4–100 % de son asymptote, mais à t = 0⁺ Vp = 0. L'ordre 0 aurait donc
  surestimé la chute en début de fenêtre de jusqu'à I_cell·ρ·Rp
  (≈ 65–190 mV à ρ = 2 selon SoC) : approximation susceptible de biaiser
  l'endpoint min_t V → rejetée.
- Rôle de ρ : multiplie **Rs et Rp** (croissance des résistances avec
  l'âge, sources 9, 11, 12, 13). **Cp n'est pas scalé** — choix déclaré
  pré-data : l'évolution de Cp avec l'âge est documentée comme secondaire
  (set B DTU) et son effet sur τ est de second ordre pour l'endpoint.
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
- **Défense de la convention p35 (audit v0.5)** : chaque marqueur est un
  faisceau de pixels (épaisseur du trait + 4 cellules superposées +
  anti-aliasing) ; p35 du faisceau est une convention de lecture **figée
  avant tout résultat**, appliquée uniformément aux trois séries et à tous
  les points, sans exception locale. La médiane est publiée dans le même
  CSV : l'écart p35/médiane est ≤ 0.7 mΩ (Rs), ≤ 2.4 mΩ (Rp), ≤ 0.6 kF
  (Cp) — les deux conventions donnent la même table à l'incertitude de
  numérisation près. p35 n'est donc pas un levier de résultat.
- Défauts connus et déclarés : recouvrement de marqueurs à SOC = 10 %
  (écart médiane/p35) ; **Rp et Cp non mesurés à SOC = 100 %** (pas de
  marqueur Fig. 7A/8A).
- **Extension > 90 % — GELÉE (v0.5)** : Rp(SoC>90) = Rp(90), Cp(SoC>90) =
  Cp(90) (clamp). Justification : la source déclare « Rp is stable for SOC
  above 25 % » (DTU, §results) ; le clamp n'invente aucun trend au-delà de
  la dernière mesure ; les alternatives (extrapolation linéaire, symétrie)
  introduiraient des données inexistantes. Choix indépendant de tout effet
  sur les violations.
- Extraits corrigés (p35) : Rs : 42.9 (0 %) → 38.2 (50 %) → 55.7 mΩ (100 %) ;
  Rp : 66.6 (0 %) → 26.7 (50 %) → 20.0 mΩ (90 %) ; Cp : 4.0 (0 %) →
  4.5 (50 %) → 14.1 (70 %) → 4.3 kF (90 %). τ = Rp·Cp : 86–338 s.
- **Statut du modèle — composite déclaré (choix B de l'audit, correction
  3 ; précisé en v0.4)** : OCV issue du NCR18650B (HNEI) et paramètres
  Thevenin issus d'un NMC 18650 3.5 Ah (DTU) forment un **modèle
  électrochimique équivalent composite de cellule Li-ion 18650 haute
  énergie**, qui ne constitue la qualification d'aucune chimie ni
  référence commerciale particulière. Toute frontière éventuelle de P4b
  sera une propriété du **modèle composite expérimental défini et gelé
  pour cette campagne** — ni une frontière générale des cellules NMC
  18650, ni une qualification spécifique du Panasonic NCR18650B. Une
  recherche de source Thevenin DC complète spécifique NCR18650B (Rs, Rp,
  Cp vs SoC) n'a pas abouti (§11).
- **Contrôle de cohérence (correction 1 de l'audit)** : le datasheet
  NCR18650B fournit une impédance AC à 1 kHz, tandis que la table DTU
  représente une résistance effective DC issue d'un modèle Thevenin. Ces
  deux grandeurs ne sont pas directement comparables quantitativement.
  **Le datasheet Panasonic n'est donc pas utilisé pour valider
  numériquement R_int,ref.** Contrôle de cohérence de même nature (DC/DC)
  à la place : le rapport HNEI (source 8, Table 1) mesure la **résistance
  ohmique** NCR18650B — chute de tension immédiate à l'application du
  courant, même type de grandeur que Rs — à **59.6 mΩ en moyenne
  (médiane 59.2, [56.3 ; 67.1], ~100 cellules neuves)**. Les Rs DTU set A
  (37–56 mΩ à 23 °C) sont du même ordre de grandeur, légèrement inférieurs
  (les auteurs HNEI notent eux-mêmes une contribution de la résistance de
  contact des supports). Cohérence satisfaisante pour un modèle composite.
- Set B (SOH 90 %) : **non tabulé** — deux tentatives de calibration de la
  numérisation ont échoué ; seule une lecture honnête en plage est retenue
  (SoC médian ~45–75 mΩ vs ~37–42 mΩ neuf → ρ ∈ [1.1 ; 1.9], §7.1). Aucune
  valeur pseudo-précise n'est publiée.

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

Déclaration explicite : il s'agit d'un **modèle de pack équivalent** — le
courant par cellule est le courant de pack ramené au rapport des capacités,
exact pour un nombre quelconque de branches identiques ; le taux-C par
cellule égale le taux-C du pack. nP_eq ∈ [1.31 ; 4.30] sur le domaine
nuisance : l'héritage COTS 2P–4P (sources 4, 6) a motivé le choix de la
capacité de référence C_cell, sans constituer une contrainte dure — déclaré.
N_S = 2 fixe (héritage CubeSat 6–8.4 V : sources 4, 5 ; proxy du modèle
figé). V_min,pack = N_S × V_min,cell = 2 × 2.5 = **5.0 V** (§7.2-D).

**E. État dynamique Vp et convention de courant — règles GELÉES (v0.5)**

- Vp est un **état dynamique continu** du modèle Thevenin d'ordre 1 de la
  future plante P4b, évoluant selon
  `dVp/dt = −Vp / [ρ·Rp(SoC)·Cp(SoC)] + I_cell/Cp(SoC)` avec
  I_cell = I_batt·C_cell/C_BATT. Vp n'est **jamais remis à zéro** lors de
  l'entrée dans une fenêtre payload ; il évolue continûment pendant toute
  la durée du run.
- **Vp(t0) — règle gelée** : le scénario gelé démarre à t0 = 0 en début de
  phase lumière ; la phase précédant t0 est donc une éclipse (1800 s) sous
  courant bus seul (u = 0 hors fenêtre [600 ; 1500] s). L'état initial
  physique cohérent est l'**état quasi-stationnaire de cette éclipse
  pré-run** :

  ```
  Vp(t0) = ρ · Rp(SoC0) · I_BASE · C_cell / C_BATT
  ```

  Justification : le satellite n'est jamais relaxé en orbite (bus toujours
  alimenté) — Vp(t0) = 0 rejeté car physiquement incohérent, non retenu
  pour sa simplicité ; l'éclipse pré-run dure 1800 s ≥ 2.7τ même au pire
  coin (τ = ρ·Rp·Cp ≤ 676 s à ρ = 2) → résidu de relaxation ≤ 7 % de
  Vp(t0), lui-même borné à ≈ 32 mV au pire coin nuisance (I_BASE = 0.75 A,
  C_BATT = 4.4 Ah, SoC0 = 0.40) → erreur d'initialisation ≤ ~2 mV,
  négligeable et déclarée. Alternative « point fixe périodique sur
  l'orbite » considérée et rejetée : complexité injustifiée au vu de ce
  résidu. Règle déterministe, reproductible, fonction uniquement des
  nuisances tirés et des tables gelées.
- **Convention de courant — gelée** : I_batt = I_BASE + u − i_charge,
  signé, > 0 = décharge ; identité avec le code gelé
  `dsoc = (i_charge − I_BASE − u)/(C_BATT·3600) = −I_batt/(C_BATT·3600)`.
  Propagation du Thevenin au **courant signé** sur tout le domaine :
  - I_batt > 0 (décharge) : V = OCV − I_cell·ρ·Rs − Vp, Vp > 0 ;
  - I_batt = 0 : relaxation libre dVp/dt = −Vp/(ρ·Rp·Cp) ;
  - I_batt < 0 (charge) : même équation, I_cell < 0 → Vp < 0 et
    V = OCV + |I_cell|·ρ·Rs + |Vp| (surtension de charge, signe correct).
  Justification : le Thevenin est un circuit équivalent **linéaire** —
  l'extension au courant signé est l'extension minimale standard ;
  l'OCV HNEI est la moyenne des branches charge/décharge C/25, documentant
  un comportement quasi symétrique à faible régime pour la cellule de
  référence. **Limitation déclarée** : les paramètres DTU sont mesurés en
  décharge ; une asymétrie charge spécifique n'est pas modélisée. L'aléa
  étudié étant du côté décharge (V < V_min ne peut pas se déclencher en
  charge, qui élève la tension), cette limitation ne peut ni masquer ni
  créer un événement de sous-tension — elle n'affecte que la valeur de Vp
  en entrée de phase de décharge, propagée continûment par le modèle.

**D. V_min par cellule**

- **Proposition : 2.5 V/cellule** — valeur primaire du datasheet NCR18650B
  (tension de fin de décharge, source 3), corroborée par la NASA (2.5–4.1/4.2 V,
  source 1) et par un seuil COTS primaire vérifiable : le verrouillage
  sous-tension **matériel non configurable** du GomSpace BP8 s'active à
  ≈ 2.44 V/cellule (typ) avec réarmement à ≈ 2.69 V/cellule (source 6) — le
  seuil de protection réel est donc au voisinage de 2.5 V/cellule, pas de
  3.0 V.
- **3.0 V/cellule abandonné comme valeur primaire** : aucune source primaire
  précise ne le documente comme seuil de protection. Les seuils « critical
  battery » 3.25 V/cellule du GomSpace P80 (source 7) sont des seuils
  **logiciels configurables** de gestion opérationnelle — pas des protections ;
  ils ne peuvent pas servir de référence V_min.
- V_min,pack = 5.0 V (2S). Ce choix suit la hiérarchie des sources
  (datasheet primaire > pratique supposée) ; il n'a été influencé par aucun
  résultat — aucun n'existe en P4b (§10).

| Élément | Valeur/forme | Source | Statut |
|---|---|---|---|
| Topologie pack | 2S fixe ; **pack équivalent continu** nP_eq = C_BATT/3.35 (option B — pas de nP discret) | 3, 4, 6 | GELÉ v0.5 |
| OCV(SoC) | table 51 points NCR18650B (C/25 moyen), interpolation linéaire ; auditée (ré-extraction identique, monotone, ±10 mV / ±0.1 V sous 2 %) | 8 (`data/`) | GELÉ v0.5 |
| Rs(SoC), Rp(SoC), Cp(SoC) | Thevenin ordre 1 explicite, set A neuf 23 °C ; Rp/Cp **corrigés v0.5** (erreur de calibration démontrée) ; extension clamp 90 % gelée ; ρ multiplie Rs et Rp, Cp non scalé | 9 (`data/`) | GELÉ v0.5 |
| Vp(t0) | ρ·Rp(SoC0)·I_BASE·C_cell/C_BATT (quasi-stationnaire éclipse pré-run) | scénario gelé + 9 | GELÉ v0.5 |
| Convention courant | I_batt = I_BASE + u − i_charge signé ; Thevenin bidirectionnel ; limitation charge déclarée | code gelé + 9 | GELÉ v0.5 |
| Statut du modèle | **composite expérimental gelé** (OCV NCR18650B + dynamique Thevenin NMC 18650 ; frontière = propriété du modèle gelé, pas d'une chimie ni d'une référence commerciale) | 8, 9 | DÉCLARÉ |
| V_min par cellule | **2.5 V** (datasheet, corroboré COTS BP8 ≈ 2.44 V matériel) | 1, 3, 6 | PROPOSÉ |
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
physique réel — pendant que B continue de vérifier SoC ≥ 0.35. La définition
formelle de Y, les seuils εS/εF et tout le protocole statistique relèvent de
la Phase 3 P4b : **PENDING**.

---

## 8. Hypothèses PROPOSÉES

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
- Taper de charge CC/CV (hors zone opérée).
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
| Aucune borne choisie parce qu'elle devrait produire des violations | ✅ — V_min = 2.5 V suit la hiérarchie des sources (datasheet primaire > pratique supposée) ; il **éloigne** le seuil de la zone opérée, sens inverse d'un choix orienté violation ; l'ordre de grandeur §6.4 montre que l'issue reste réellement incertaine |
| ρ_max justifié indépendamment | ✅ — [1.0 ; 1.9] documenté non abusif (DTU) ; 1.37× max attribué à Hein (pas 2.0) ; portion (1.9 ; 2.0] étiquetée marge conservative, bornée par le documenté abusif (3×, Wang) |
| Aucun paramètre ajusté après observation d'un résultat P4b | ✅ — aucune simulation P4b n'existe ; rien n'a pu être observé |
| Aucune simulation scientifique P4b exécutée | ✅ — Phase 0 = audit + bibliographie + numérisation de données publiées ; §6.4 est une lecture directe des tables sourcées, pas une simulation du système |
| Choix du modèle Thevenin (correction 2) orienté résultat ? | ✅ — option A (ordre 1 explicite) choisie sur un argument physique pré-data (τ/900 ∈ [0.06 ; 0.32], biais potentiel de l'endpoint) formulé par l'audit **avant** toute simulation ; l'option retenue **réduit** la chute calculée en début de fenêtre, sens inverse d'un choix orienté violation |
| Hétérogénéité des cellules (correction 3) | ✅ — choix B déclaré : modèle composite expérimental gelé (OCV NCR18650B + dynamique Thevenin NMC 18650), frontière = propriété du modèle gelé uniquement ; la recherche d'une source spécifique NCR18650B a été menée **avant** la décision et n'a pas abouti ; aucun remplacement ne pourra avoir lieu après observation d'un résultat |
| Comparaison AC/DC (correction 1) | ✅ — supprimée partout ; le datasheet Panasonic ne valide pas numériquement R_int,ref ; contrôle DC/DC de même nature (HNEI Table 1) à la place |
| Correction Rp/Cp v0.5 orientée résultat ? | ✅ — erreur de calibration **objective** démontrée par gridlines/labels/axes de la source ; trouvée en audit pré-data alors qu'aucune simulation P4b n'existe ; son effet (Rp corrigé à la hausse) n'a joué aucun rôle dans la décision de corriger |
| Topologie option B orientée résultat ? | ✅ — choisie sur un argument de cohérence interne (éliminer un second mismatch capacité/topologie) et de conservation de la distribution nuisance historique ; aucun résultat P4b n'existe |
| Vp(t0) choisi pour simplifier ? | ✅ — Vp(t0) = 0 rejeté car physiquement incohérent (bus toujours alimenté) ; la règle retenue (quasi-stationnaire de l'éclipse pré-run) est **plus** complexe et physiquement motivée |
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
- V_min = 2.5 V/cellule comme limite basse expérimentale proposée
  (V_min,pack = 5.0 V) ;
- aucun recours aux 21 blocs P4a ; aucun résultat P4b existant.

Gelé en v0.5 (clôture des PENDING physiques) :

- tables OCV / Rs / Rp / Cp auditées contre leurs sources primaires
  (calibrations vérifiées par gridlines/labels/axes ; ré-extraction OCV et
  Rs identique ; **Rp et Cp corrigés** après erreur objective démontrée) ;
- règle d'extension Rp/Cp au-delà de 90 % (clamp, soutenu par la source) ;
- traitement du segment OCV < 2 % (table inchangée, interpolation linéaire
  uniforme, incertitude déclarée) ;
- Vp(t0) = ρ·Rp(SoC0)·I_BASE·C_cell/C_BATT (quasi-stationnaire éclipse
  pré-run) ;
- convention de courant signé I_batt = I_BASE + u − i_charge, Thevenin
  bidirectionnel avec limitation charge déclarée ;
- topologie pack équivalent continu nP_eq = C_BATT/C_cell (option B — le
  mismatch capacité/topologie potentiel est éliminé) ;
- références ECSS vérifiées sur texte source (E-ST-20C Rev.2 §5.7.3
  exigences h et i ; E-HB-20-02A handbook méthodologique).

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

---

**PHYSICAL MODEL STATUS : READY FOR PREREGISTRATION** (modèle physique —
décision finale réservée à l'audit). Tous les PENDING physiques sont clos ;
les points restants sont exclusivement statistiques et relèvent de la Phase
3, non autorisée à ce stade.

**STOP.** Aucune grille ρ, aucun endpoint statistique, aucune seed, aucune
simulation scientifique P4b, aucun préenregistrement et aucun commit de gel
ne sont autorisés par ce seul livrable.
