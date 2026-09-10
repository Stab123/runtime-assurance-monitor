# P4B — AUDIT D'IMPLÉMENTATION v0.1

**Date UTC** : 2026-09-11
**Périmètre** : implémentation du protocole P4b GELÉ (commit
`45e509ee987469598acbf56967fb9e5cdc88a427`, tag `p4b-preregistration-freeze`,
parent `aba115ff174ee41629f1fda27b6ff826a007622c`).
**Documents de référence gelés** : `P4B_PREREGISTRATION_v0.1.md` (§2–§16),
`P4B_PHASE0_PHYSICAL_BASIS_v0.6.md` (§5, §7.2).

**Garantie périmétrique** : cet audit porte sur le CODE et les TESTS
UNIQUEMENT. Aucun run scientifique n'a été exécuté : pas de campagne
principale, pas de pilote, pas de sous-échantillon exploratoire, pas de
Monte-Carlo, pas un seul bloc du design gelé dans la plante, pas une seule
graine dérivée P4b utilisée pour une trajectoire. Tous les tests utilisent
des cas synthétiques / jouets explicitement hors design (valeurs nominales
P0 rondes, durées 100–5 100 s, graines arbitraires hors dérivation).

---

## 1. Table d'audit — exigence → code → test

Statuts : **CONFORME** / NON CONFORME / AMBIGU.

| ID | EXIGENCE PROTOCOLE | FICHIER / LIGNE CODE | TEST ASSOCIÉ | STATUT | REMARQUE |
|----|--------------------|---------------------|--------------|--------|----------|
| A-01 | Équations gelées v0.6 §5 : I_batt = I_BASE + u_exec − i_charge (signé) ; I_cell = I_batt·C_cell/C_BATT ; V_pack = N_S·[OCV − I_cell·ρ·Rs − Vp] ; dVp/dt = −Vp/(ρ·Rp·Cp) + I_cell/Cp | modele_p4b.py : `i_batt` l.235, `i_cell` l.239, `v_pack` l.245, `dvp` l.256, `pas` l.268 | test_modele_p4b.py : test_i_batt_signe, test_i_cell_partage_courant, test_v_pack_formule, test_rho_scale_rs_rp_pas_cp | CONFORME | vérifié contre le texte gelé ligne à ligne |
| A-02 | Vp(t0) = ρ·Rp(SoC0)·I_BASE·C_cell/C_BATT (convention quasi-stationnaire, v0.6 §7.2-E) — aucun warm-up | modele_p4b.py : `PlanteP4b.__init__` l.218–229 | test_vp_init_regle_gelee, test_vp_init_positif_eclipse_prerun | CONFORME | égalité float exacte testée sur 3 ρ |
| A-03 | ρ multiplie Rs et Rp UNIQUEMENT ; Cp NON scalé (v0.6 §7.2-B) | modele_p4b.py : `v_pack` l.250 (ρ·rs), `dvp` l.256–266 (ρ·rp au dénominateur, cp nu) | test_rho_scale_rs_rp_pas_cp | CONFORME | le test vérifie les deux formes analytiquement |
| A-04 | Vp état continu, JAMAIS remis à zéro à l'entrée payload (v0.6 §7.2-E) | modele_p4b.py : `pas` l.268 (vp mis à jour, jamais réassigné) ; aucune réinitialisation dans campagne_p4b.py | test_vp_jamais_reinitialise_entree_payload (continuité à t = 600 s) | CONFORME | audit statique : aucune occurrence de réinitialisation |
| A-05 | Tables OCV (HNEI, 51 pts) et Thevenin (DTU, p35) — interpolation linéaire, aucune extrapolation | modele_p4b.py : `_interpolation_lineaire` l.75, `TablesPhysiques.charger` l.126 | test_noeuds_ocv_exacts, test_noeuds_rint_p35, test_monotonie_ocv, test_interpolation_lineaire_milieu, test_interpolation_n_extrapole_jamais | CONFORME | valeurs de nœuds = extraits publiés v0.6 §7.2 |
| A-06 | Clamp hors domaine : tables évaluées à la borne la plus proche ; état SoC JAMAIS saturé (v0.6 §7.2-A, S6) | modele_p4b.py : `ocv/rs/rp/cp` l.167–182 (clamp de l'entrée) ; `pas` l.268 (aucune saturation) ; `hors_domaine` l.297 | test_clamp_entree_tables_pas_etat, test_etat_soc_jamais_sature, test_hors_domaine_flag | CONFORME | test : SoC réel > 1 atteint, tables évaluables |
| A-07 | Extension > 90 % : Rp(SoC>0.90) = Rp(0.90), Cp idem ; Rs et OCV mesurés jusqu'à 100 % (v0.6 §7.2-B) | modele_p4b.py : `SOC_MAX_RP_CP` l.57 ; grilles séparées `soc_rs` (0–100 %) / `soc_rp_cp` (0–90 %) | test_clamp_rp_cp_090, test_point_100_rint_inaccessible | CONFORME | **écart trouvé et corrigé pendant l'implémentation** : la v1 du chargeur excluait la ligne 100 % pour Rs aussi (Rs(1.0) retournait 44.3 au lieu de 55.7 mΩ) — détecté par test_noeuds_rint_p35 AVANT toute exécution ; correction = grilles séparées. Décision D3 |
| A-08 | V_min,pack = 5.0 V (N_S = 2 × 2.5 V) ; N_S = 2, C_cell = 3.35 Ah (v0.6 §7.2-D) | modele_p4b.py : l.53–56 | test_constantes_gelees | CONFORME | — |
| A-09 | Endpoint §4 : V_min = min sur k = 0..2699 de V_pack(t_k) ; toutes phases ; comparaison float64 stricte < 5.0 | campagne_p4b.py : boucle `simuler_p4b` l.143+ (min sur tous les pas, premier argmin conservé) ; `V_MIN_PACK` l.83 | test_endpoint_inegalite_stricte, test_endpoint_toutes_phases | CONFORME | k = 0 inclus (t0) ; pas d'exclusion de phase |
| A-10 | Précision d'évaluation §4 : V_pack(t_k) sur l'état (SoC(t_k), Vp(t_k)) avec le courant appliqué au pas (u_exec après moniteur, y compris repli = 0) | campagne_p4b.py : évaluation AVANT `plante.pas`, avec `u_exec` du cycle courant | test_u_exec_utilise_dans_v_pack (plante) ; test_repli_du_moniteur_applique (boucle) | CONFORME | ordre figé : estimateur → moniteur → endpoint → propagation |
| A-11 | INVALID_TECHNIQUE tolérance zéro : NaN/Inf/interruption ; run hors numérateur ET dénominateur ; JAMAIS de substitution de Y | campagne_p4b.py : `_RunInvalideTechnique` l.102, contrôle de finitude à chaque pas, `except Exception` → run interrompu ; Y = None | test_run_interrompu_invalide, test_nan_detecte_invalide, test_substitution_y_interdite (schéma) | CONFORME | Y reste null ; le schéma REJETTE toute substitution |
| A-12 | V0 : campagne principale ARRÊTÉE au premier run invalide ; reprise = ré-exécution intégrale (§12) | campagne_p4b.py : `CampagneInvalideTechnique`, arrêt dans `executer`, méta statut INVALID écrite avant arrêt | test_campagne_arretee_sur_run_invalide (blocs jouets) | CONFORME | décision D8 : lecture littérale de « campagne arrêtée » |
| A-13 | Descripteur secondaire §4 : violation silencieuse = Y ∧ min SoC ≥ 0.35 (hors verdict) | campagne_p4b.py : `soc_min`, `violation_silencieuse`, `SEUIL_SOC_DESCRIPTEUR` l.84 | test_coherence_descripteurs | CONFORME | champ ajouté au JSONL (requis par §4) — décision D7 |
| A-14 | Scénario gelé §2 : T = 13 500 s, dt = 5.0 s, orbite 5 400 s, lumière (t%5400)<3600, payload (t%5400)∈[600 ; 1500) ET lumière, u = 3.0 A | campagne_p4b.py : `charger_scenario` l.121 (lecture de ram_p4/config_p4a.json GELÉ), `en_fenetre_payload` l.136 (reprise exacte de campagne_p4a) | test_scenario_charge_depuis_config_gelee | CONFORME | source unique, aucune constante dupliquée (D5) |
| A-15 | Moniteur B INCHANGÉ : réutilisation des modules gelés, aucune copie | campagne_p4b.py : imports ram_p0/ram_p2 l.65–72 ; `faire_jeu(float("inf"), cfg)` ; `Moniteur(..., k_sigma=0.0)` | test_gel_p4b.py : test_modules_historiques_inchanges (SHA256) | CONFORME | construction identique à simuler_p4 gelé (D4) |
| A-16 | Estimateur gelé, biais b = 0 : classe de base EstimateurEPS (2 tirages gauss par cycle, ordre fixe — CRN) | campagne_p4b.py : `EstimateurEPS(modele_est, dt, cfg["bruit_std"], jeu.horizon_pas)` | test_crn_temoin_identique_entre_niveaux, test_graine_bruit_change_le_run | CONFORME | la sous-classe biaisée P4a n'est pas utilisée (D6) |
| A-17 | Grille ρ gelée : 9 niveaux {1.000 ; … ; 2.000}, pas 0.125 (§3) | campagne_p4b.py l.81 ; analyse_p4b.py l.32 | test_grille_rho_exacte (exactitude binaire), test_grilles_coherentes_entre_modules | CONFORME | valeurs exactes en float64 (multiples de 2⁻³) |
| A-18 | N = 5 500 runs/niveau ; ordre bloc-major, ρ croissant (§6, §7) | campagne_p4b.py : `N_BLOCS` l.82, boucle `executer` (bloc externe, ρ interne) | test_gel_p4b.py : test_constantes_du_protocole | CONFORME | — |
| A-19 | Design : LECTURE SEULE du fichier gelé ; jamais de régénération PLANT en campagne (§7, §8) | campagne_p4b.py : `charger_design` l.106 (SHA256 vérifié, refus si modifié) ; graines_p4b.py | test_aucune_regeneration_design (audit statique du source), test_gel (design inchangé) | CONFORME | DesignGeleModifie levée sinon |
| A-20 | Seeds : règle unique gelée ; NOISE par bloc_id, partagé entre les 9 niveaux (CRN) ; labels PLANT/NOISE seulement (§8) | graines_p4b.py : ré-export du module GELÉ verifier_design_p4b.py ; `graine_bruit_bloc` | test_graines_p4b.py (6 tests : source unique, labels, bornes, valeur de référence publique) | CONFORME | aucune réimplémentation de la règle |
| A-21 | CRN : témoin par bloc (hash paramètres + graine) + bruit pur au pas 1 000 (§7, §14) | campagne_p4b.py : `temoin_bloc` l.271, `CYCLE_TEMOIN` l.85, capture `estimateur.bruit_dernier[0]` | test_crn_temoin_identique_entre_niveaux ; test_controles_p4b.TestTemoinsCRN | CONFORME | mécanisme P4a repris (D9 : indice de cycle, convention P4a) |
| A-22 | Wilson bilatéral 99.4444 %, z = 2.7729212946086634, formule standard centrée (§5) | analyse_p4b.py : `Z_WILSON` l.26, `wilson_ic` l.40 | test_valeurs_documentees (IC publiés §6 reproduits à 1e-4), test_z_gele | CONFORME | remarque R1 : borne inf à x = 0 vaut 0 en mathématiques, résidu float ≈ −1e-19 — SANS impact décisionnel (seule la borne sup classe S à petit x ; la borne inf ne sert qu'à x ≥ 320, loin de toute frontière numérique) |
| A-23 | Classification par bornes ET par seuils entiers (x ≤ 34 / x ≥ 320), équivalence DÉMONTRÉE (§5/§6) | analyse_p4b.py : `classifier_niveau_bornes` l.57, `classifier_niveau_seuils` l.67, `verifier_equivalence_seuils` l.79 | test_equivalence_bornes_seuils_exhaustive (5 501 comptages), test_seuils_entiers | CONFORME | équivalence exhaustive vérifiée machine |
| A-24 | Frontière §10 : existence ssi S ≠ ∅ ∧ I ≠ ∅ ∧ max(S) < min(I) ; b* ∈ (max(S) ; min(I)] ; aucune interpolation ; LOW RESOLUTION ssi largeur > 0.250 STRICT | analyse_p4b.py : `frontiere` l.106 | test_frontiere_intervalle, test_low_resolution_strict (0.250 non annoté, 0.375 annoté) | CONFORME | — |
| A-25 | Monotonie testée, jamais imposée ; inversion dure sur LABELS (§11) | analyse_p4b.py : `inversion_dure` l.93 | test_inversion_dure (4 configurations) | CONFORME | aucune régression isotone nulle part |
| A-26 | Verdicts V0–V7 dans l'ordre, premier match ; cas A–J (§12) | analyse_p4b.py : `verdict_p4b` l.137 | test_v0…test_v7, test_cas_A_a_J, test_v2_prioritaire_sur_inversion, test_exhaustivite_partition (3⁹ = 19 683 combinaisons) | CONFORME | partition démontrée exhaustivement |
| A-27 | V0b : fraction flaggée > 25 % STRICT (§9) | analyse_p4b.py : `GARDE_FOU_FLAG` l.33, comparaison stricte l.152 | test_v0b_garde_fou_strict (25.000 % exact = pas de déclenchement) | CONFORME | fraction sur runs valides (D10) |
| A-28 | Règle d'inclusion §9 : run flaggé RESTE dans l'analyse, porte le drapeau (premier instant, durée cumulée, côté, at_vmin) | campagne_p4b.py : bloc drapeau dans `simuler_p4b` ; schemas_p4b.py : champs outside_* | test_drapeau_hors_domaine, test_sans_drapeau_champs_coherents, test_soc_invariant_en_rho (drapeaux identiques entre niveaux sous CRN) | CONFORME | — |
| A-29 | Sensibilité OCV ±0.1 V aux points SoC {0.00 ; 0.02}, copie EN MÉMOIRE, mêmes design/graines (CRN), dégradation seule (§13) | modele_p4b.py : `variante_ocv` l.185 ; campagne_p4b.py : modes ocv_plus/ocv_moins ; sensibilites_p4b.py : `combiner_sensibilite` | test_variante_ocv_memoire_seule ; TestDegradationSeule (7 tests : déclassement, déplacement, jamais de promotion, annotation, robustesse, analyse invalide) | CONFORME | promotion vers TRANSITION structurellement impossible |
| A-30 | Sensibilité drapeaux : x' = x − x_flag (violations dont le min survient hors domaine), dégradation seule (§13, règle symétrique) | sensibilites_p4b.py : `sensibilite_drapeaux` l.107 ; champ outside_at_vmin | test_x_prime, test_x_flag_borne, test_drapeaux_ne_changent_rien_si_vide | CONFORME | — |
| A-31 | Contrôle re-run déterministe : Y et V_min bit à bit (même plateforme) ; cross-plateforme Y identique + écart relatif < 1e-12 ; divergence → V0 (§14.1) | controles_p4b.py : `comparer_rerun` l.35 (struct.pack "<d") | TestRerun (5 tests, y compris 1 ulp détecté) | CONFORME | fonction prête — non exécutée (pas de campagne) |
| A-32 | Contrôle dt = 2.5 s : mêmes points, MÊMES graines NOISE, niveaux {1.000 ; 2.000} + paire de frontière si V4 ; verdict divergent → INCONCLUSIVE (NUMERICAL SENSITIVITY) (§14.2) | campagne_p4b.py : mode dtctrl (label NOISE inchangé, seul dt change) ; controles_p4b.py : `comparer_dtctrl` l.72 | TestDtctrl (3 cas) ; test_gel (dt_controle_s = 2.5 lu du gelé) | CONFORME | convention P4a-dtctrl reprise |
| A-33 | Schéma JSONL par run : tous les champs du mandat + descripteur §4 + témoins (§14) | schemas_p4b.py : CHAMPS_RUN (29 champs), `valider_run` l.70 | test_schemas_p4b.py (8 tests), test_enregistrement_complet_conforme_schema | CONFORME | validation à l'écriture (fail-fast dans executer) |
| A-34 | Provenance future exécution : freeze commit/tag, SHA256 protocole/design/tables/code, versions Python/numpy/scipy, OS, machine, hostname, timestamp UTC (§14) | campagne_p4b.py : `meta_provenance` l.295+, `empreintes_code` l.278 | test_gel_p4b.py : test_constantes_du_protocole (commit/tag/parent) | CONFORME | méta en sidecar .meta.json |
| A-35 | Aucune exécution scientifique avant le GO externe | campagne_p4b.py : CLI exige `--execution-autorisee`, refus explicite (exit 2) | test_execution_refusee_sans_go | CONFORME | garde procédurale ajoutée (D11) — hors protocole, mesure anti-accident sans effet scientifique |
| A-36 | Fichiers gelés non modifiés (protocole, base physique, audits, design, tables, vérificateur, modules P0/P2/P4a) | — (intégrité vérifiée par hash) | test_gel_p4b.py : test_fichiers_gelles_inchanges (10 fichiers), test_modules_historiques_inchanges (8 fichiers) + diff récursif vs commit de freeze : 0 divergence de contenu | CONFORME | preuves §3 |
| A-37 | Environnement d'exécution des tests : Python 3.12, stdlib pour la plante et la décision | modele_p4b.py, campagne_p4b.py, analyse_p4b.py : aucun import numpy/scipy | grep : 0 occurrence numpy/scipy hors commentaires | CONFORME | §14 : numpy/scipy réservés à l'analyse — l'analyse P4b n'en a pas besoin (Wilson en math pur) |

## 2. Décisions d'implémentation documentées (aucune liberté résiduelle)

Ces points ne sont pas des ambiguïtés du protocole : ils relèvent de la
mécanique d'implémentation et sont fixés ici de façon déterministe. Aucun
n'influence une grandeur scientifique sans être énoncé.

- **D1 — Intégration de Vp** : Euler explicite, coefficients évalués à
  (SoC(t_k), I_cell(t_k)) — le MÊME schéma que l'intégrateur SoC gelé de la
  plante historique (`soc + dt·dsoc`, taux au début du pas). Aucune
  grandeur évaluée entre les pas (§4).
- **D2 — Grille temporelle** : `t_k = k·dt` (exact en float64 pour dt ∈
  {5.0 ; 2.5} : k·5 et k·5/2 sont exacts pour k ≤ 5 399) — le modulo
  orbital est donc exact.
- **D3 — Chargement des tables** : Rs chargé jusqu'à SoC = 100 % (mesuré) ;
  Rp/Cp chargés jusqu'à 90 % — le point 100 % (NaN, non mesuré) est
  inaccessible par le clamp gelé. Correction appliquée PENDANT
  l'implémentation, avant toute exécution, détectée par test (cf. A-07).
- **D4 — Moniteur B** : import direct des modules gelés, construction
  identique à `simuler_p4` gelé (`faire_jeu(float("inf"), cfg)`,
  `k_sigma=0.0`). Aucune ligne du moniteur dupliquée.
- **D5 — Scénario** : lu à l'exécution depuis `ram_p4/config_p4a.json`
  gelé (source unique) ; son SHA256 est ancré dans les tests et publié
  dans la méta de chaque campagne.
- **D6 — Estimateur** : classe de base gelée `EstimateurEPS` (biais b ≡ 0
  exactement en P4b) — la sous-classe biaisée P4a n'est pas utilisée.
- **D7 — Champs JSONL** : `soc_min` et `violation_silencieuse` ajoutés au
  schéma — exigés par le descripteur secondaire §4. Aucun champ du mandat
  retiré.
- **D8 — Arrêt de campagne sur run invalide** : lecture littérale de §12
  V0 (« campagne arrêtée, cause documentée ») : la boucle s'interrompt au
  premier run INVALID_TECHNIQUE, l'enregistrement fautif est écrit, la
  méta porte INVALID ; la reprise est nécessairement intégrale (CLI :
  fenêtre complète par défaut).
- **D9 — Témoin CRN** : capturé au CYCLE d'indice 1 000 (convention P4a),
  y compris en dtctrl.
- **D10 — Fraction flaggée** : calculée sur les runs valides de la
  campagne principale (les runs invalides déclenchent V0 avant V0b).
- **D11 — Garde CLI** : `--execution-autorisee` requis pour tout run sur
  le design gelé. Mesure de protection procédurale ; sans objet
  scientifique.

## 3. Preuves de non-altération du gel

- **Hashes** : 10 fichiers gelés ram_p4b/ + 8 modules historiques
  (ram_p0, ram_p2, ram_p4/config_p4a.json) vérifiés SHA256 — ancrés dans
  `tests/test_gel_p4b.py`, tous CONFORMES.
- **Diff contre le commit de freeze** : re-clone du dépôt à
  `p4b-preregistration-freeze`, diff récursif (hors caches) contre
  l'arbre de travail : **0 divergence de contenu** sur les fichiers
  communs ; toutes les entrées nouvelles sont strictement additives sous
  `ram_p4b/` (code, tests, rapports).
- **Aucune donnée scientifique** : aucun fichier de résultats P4b n'existe
  (aucun JSONL de campagne, aucun p̂, aucun verdict empirique). Seuls
  artefacts produits : code, tests, rapports d'audit.

## 4. Ambiguïtés rencontrées

**Aucune ambiguïté bloquante.** Aucun IMPLEMENTATION_BLOCKER n'a dû être
créé. Deux points de formulation ont été tranchés par lecture littérale du
texte gelé (D8) ou par cohérence avec l'intégrateur gelé (D1) — listés en
§2, sans liberté résiduelle.

Remarque mineure R1 (A-22) : la borne inférieure de Wilson à x = 0 est
mathématiquement 0 ; le calcul float64 donne ≈ −1.1e-19 (annulation). La
formule gelée est implémentée à l'identique (aucun clamp ajouté — un clamp
changerait les bits et s'écarterait du texte gelé) ; l'impact décisionnel
est nul.

## 5. Résultat de l'audit

| Contrôle | Résultat |
|---|---|
| Suite de tests synthétiques | **109/109 OK** (4.9 s) |
| Vérificateur mécanique V-1…V-8 | **tous OK** |
| Exigences auditées | 37/37 CONFORME, 0 NON CONFORME, 0 AMBIGU |
| Données scientifiques produites | **0** |
| Fichiers gelés modifiés | **0** |
| Logique statistique modifiée | **non** (implémentée telle que gelée) |
| Liberté d'interprétation résiduelle | **aucune** (décisions D1–D11 figées et documentées) |

**VERDICT : `IMPLEMENTATION STATUS: READY FOR PRE-EXECUTION AUDIT`**

**STOP.** La campagne principale (49 500 runs), les sensibilités et les
contrôles ne seront exécutés qu'après revue de code externe indépendante
et GO explicite.
