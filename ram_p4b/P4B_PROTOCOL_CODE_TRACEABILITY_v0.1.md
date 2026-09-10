# P4B — TRAÇABILITÉ PROTOCOLE ↔ CODE v0.1

**Date UTC** : 2026-09-11
**Protocole** : `P4B_PREREGISTRATION_v0.1.md` gelé (commit
`45e509ee987469598acbf56967fb9e5cdc88a427`, tag
`p4b-preregistration-freeze`), base physique
`P4B_PHASE0_PHYSICAL_BASIS_v0.6.md`.
**Objet** : correspondance exhaustive sections du protocole → fonctions /
fichiers d'implémentation → tests. Les SHA256 du code sont ceux de la
livraison de Phase 4 (pré-exécution) ; ils seront recalculés et publiés
dans la méta de chaque campagne à l'exécution (`empreintes_code`).

| § PROTOCOLE | EXIGENCE | FONCTION / FICHIER | TESTS | SHA256 FICHIER (pré-exécution) |
|---|---|---|---|---|
| §2 Plante/scénario/nuisances hérités | Scénario P2.3 gelé lu depuis `ram_p4/config_p4a.json` ; moniteur B et estimateur importés des modules gelés ; tables SHA256 | `campagne_p4b.charger_scenario` (l.121), `simuler_p4b` (l.143) ; `modele_p4b.TablesPhysiques.charger` (l.126) | test_gel_p4b (scénario, modules, fichiers) ; test_tables_p4b | campagne_p4b.py `4609162c…` ; modele_p4b.py `1b37222b…` |
| §3 Grille ρ | 9 niveaux {1.000…2.000}, pas 0.125, exact float64 | `campagne_p4b.NIVEAUX_RHO` (l.81), `analyse_p4b.NIVEAUX_RHO` (l.32) | test_grille_rho_exacte, test_grilles_coherentes | idem ; analyse_p4b.py `9ee11350…` |
| §4 Endpoint | V_min min sur k = 0..2699, état à t_k, u_exec après moniteur, toutes phases, `< 5.0` strict float64 ; INVALID_TECHNIQUE tolérance zéro ; descripteur violation silencieuse | `simuler_p4b` (campagne_p4b.py) ; `modele_p4b.v_pack` (l.245), `est_fini` (l.302) ; `schemas_p4b.CHAMPS_RUN` | test_modele (endpoint, u_exec) ; test_campagne_toy (stricte, toutes phases, invalides, descripteurs) ; test_schemas | schemas_p4b.py `e67e4ec6…` |
| §5 Seuils εS/εF + Wilson | εS = 0.01, εF = 0.05 ; Wilson bilatéral 99.4444 %, z = 2.7729212946086634, formule standard centrée ; classification par bornes | `analyse_p4b.wilson_ic` (l.40), `classifier_niveau_bornes` (l.57) | test_valeurs_documentees, test_z_gele, test_bornes_dans_0_1 | analyse_p4b.py `9ee11350…` |
| §6 N, puissance, précision | N = 5 500 ; seuils entiers x ≤ 34 / x ≥ 320 ; équivalence bornes ⟷ seuils | `analyse_p4b.N_PAR_NIVEAU` (l.27), `classifier_niveau_seuils` (l.67), `verifier_equivalence_seuils` (l.79) | test_seuils_entiers, test_equivalence_bornes_seuils_exhaustive | idem |
| §7 Couverture, nuisances, CRN, ordre | Design lu (jamais régénéré) ; bloc-major, ρ croissant ; NOISE partagé entre niveaux ; témoins | `campagne_p4b.charger_design` (l.106), `executer` (l.323+), `temoin_bloc` (l.271) ; `graines_p4b.graine_bruit_bloc` | test_aucune_regeneration_design, test_crn_*, test_soc_invariant_en_rho, TestTemoinsCRN | graines_p4b.py `956a8ac1…` |
| §8 Seeds | Règle unique gelée ; labels PLANT/NOISE ; source = module gelé | `graines_p4b.py` (ré-export de `verifier_design_p4b.seed_graine`) | test_graines_p4b (6 tests) | `956a8ac1…` |
| §9 Hors domaine | Run inclus + drapeau (premier instant, durée, côté, at_vmin) ; garde-fou > 25 % STRICT ; fraction sur runs valides | `simuler_p4b` (bloc drapeau) ; `analyse_p4b.GARDE_FOU_FLAG` (l.33), `fraction_flaggee` (l.219), V0b dans `verdict_p4b` | test_drapeau_hors_domaine, test_v0b_garde_fou_strict, TestFractionFlag | idem |
| §10 Frontière | Existence, b* ∈ (max(S) ; min(I)], pas d'interpolation, LOW RESOLUTION > 0.250 strict, b* = null sinon | `analyse_p4b.frontiere` (l.106) | test_frontiere_intervalle, test_low_resolution_strict | idem |
| §11 Monotonie | Testée, jamais imposée ; inversion dure sur labels | `analyse_p4b.inversion_dure` (l.93) | test_inversion_dure | idem |
| §12 Décision V0–V7 | Ordre strict, premier match ; cas A–J ; arrêt de campagne sur V0 ; partition | `analyse_p4b.verdict_p4b` (l.137) ; `campagne_p4b.CampagneInvalideTechnique` + arrêt dans `executer` | test_v0…v7, test_cas_A_a_J, test_exhaustivite_partition (3⁹), test_campagne_arretee_sur_run_invalide | idem |
| §13 Sensibilités | OCV ±0.1 V à SoC {0.00 ; 0.02} en mémoire ; drapeaux x' = x − x_flag ; dégradation seule ; toujours exécutées | `modele_p4b.variante_ocv` (l.185) ; `sensibilites_p4b.combiner_sensibilite` (l.45), `sensibilite_drapeaux` (l.107), `combiner_sensibilites_ocv` (l.127) ; modes ocv_plus/ocv_moins dans `executer` | test_variante_ocv_memoire_seule ; TestDegradationSeule (7) ; TestSensibiliteDrapeaux (3) | sensibilites_p4b.py `8da44e09…` |
| §14 Reproductibilité et contrôles | Re-run bit à bit / cross-plateforme 1e-12 ; dt = 2.5 s mêmes graines NOISE ; témoin CRN ; schéma JSONL ; provenance (hashes, versions, UTC, hostname) ; procédure de divergence | `controles_p4b.comparer_rerun` (l.35), `comparer_dtctrl` (l.72), `verifier_temoins_crn` (l.103) ; `campagne_p4b` mode dtctrl, `meta_provenance` (l.295+), `empreintes_code` (l.278) ; `schemas_p4b.valider_run` | TestRerun (5), TestDtctrl (3), TestTemoinsCRN (3), test_schemas (8), test_constantes_du_protocole | controles_p4b.py `de1f570e…` |
| §15 Multiplicité | Bonferroni 18 événements, z = 2.7729212946086634 — traduit intégralement dans z et les seuils | `analyse_p4b.Z_WILSON` (l.26) | test_z_gele, test_valeurs_documentees | idem |
| §16 Table OC / puissance | Aucune traduction en code (documentée au protocole ; indicative) | — (aucune) | — | — |
| v0.6 §5 Équations | Thevenin ordre 1 explicite, convention signée | `modele_p4b.PlanteP4b` | test_modele_p4b (13 tests) | `1b37222b…` |
| v0.6 §7.2-A OCV + hors domaine | 51 points, linéaire, clamp entrée, drapeau | `TablesPhysiques.ocv`, `_clamp`, `hors_domaine` | test_tables (12 tests) | idem |
| v0.6 §7.2-B Thevenin + ρ | p35 ; Rs jusqu'à 100 % ; Rp/Cp clamp 90 % ; ρ sur Rs/Rp seuls | `TablesPhysiques.rs/rp/cp`, `PlanteP4b.dvp` | test_noeuds_rint_p35, test_clamp_rp_cp_090, test_rho_scale_rs_rp_pas_cp | idem |
| v0.6 §7.2-D Aléa | V_min,pack = 5.0 V | `modele_p4b.V_MIN_PACK` (l.56), `campagne_p4b.V_MIN_PACK` (l.83) | test_constantes_gelees | idem |
| v0.6 §7.2-E Vp | Vp(t0) quasi-stationnaire ; jamais réinitialisé ; mémoire continue | `PlanteP4b.__init__` (l.218), `pas` (l.268) | test_vp_init_*, test_vp_jamais_reinitialise, test_vp_relaxation | idem |
| Garde procédurale (hors protocole) | Refus d'exécution sans GO externe | CLI `--execution-autorisee` | test_execution_refusee_sans_go | campagne_p4b.py `4609162c…` |

**Fichiers sans correspondance protocole** (outillage) :
`tests/commun.py` (`6663208a…`), `verifier_implementation_p4b.py`
(`1804b992…` — auto-contrôles V-1…V-8), `P4B_TEST_REPORT_v0.1.txt`
(`c27f7f74…`), `P4B_IMPLEMENTATION_AUDIT_v0.1.md` (`e9df6943…`).

**Traçabilité inverse** : chaque fonction publique des modules de campagne
et d'analyse est couverte par au moins une ligne du tableau ci-dessus ;
chaque section normative §2–§16 a une traduction en code OU est
explicitement marquée « aucune » (§16 — table OC documentaire, §17–§18 —
conduite du projet, non codables).

**STOP** — en attente de la revue de code externe de pré-exécution.
