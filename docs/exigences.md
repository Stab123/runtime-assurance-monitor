# Requirements traceability — RA-*

Requirements of the runtime assurance monitor, as referenced in the code comments
(specification RAM-SPEC-0001, not public). Each entry gives the statement, the
implementing mechanism, and the associated test(s) in `ram_p0/test_moniteur.py`
(23 tests, run by `pytest ram_p0/` and by the CI workflow `tests.yml`).

## Functional requirements (RA-FUN)

| ID | Statement | Mechanism | Test(s) |
|---|---|---|---|
| RA-FUN-001 | Exactly one verdict per decision cycle, from {AUTORISE, MODIFIE, REPLI, INDETERMINE} | Single emission point in `Moniteur.decider()` | `test_ra_fun_001_un_verdict_par_cycle` |
| RA-FUN-002 | INDETERMINE is executed as REPLI but kept distinct in the trace | `Verdict` enum; execution path treats INDETERMINE as REPLI, trace records the real verdict | `test_ra_fun_002_indetermine_traite_comme_repli` |
| RA-FUN-003 | Estimation uncertainty above its own threshold triggers fallback, independently of the nominal value (hypothesis H4 — falsified) | Per-constraint `seuil_incertitude`; check `_indice_incertitude()` before envelope evaluation; cause `INCERTITUDE` | `test_ra_fun_003_incertitude_declenche_repli` |
| RA-FUN-004 | The evaluation horizon covers the arming delay of the fallback action; the projected sequence applies the action for exactly τ_arming | `horizon = max arming delay + margin` at compile time; persistence loop `k < pas_armement` in `filtre.trajectoire_sure()` (post-correction) | `test_ra_fun_004_horizon_couvre_le_delai_d_armement`, `test_ra_fun_004_persistance_exactement_pas_armement` |
| RA-FUN-005 | A constraint set whose fallback is not reachable is rejected at compile time | Reachability validation when the set is compiled; raises `RepliInatteignable` | `test_ra_fun_005_jeu_invalide_rejete_a_la_compilation`, `test_ra_fun_005_armement_long_rejete` |
| RA-FUN-006 | Once engaged, the fallback is latched; return to nominal requires an explicit criterion | `REPLI_VERROUILLE` state; `cycles_retour` counter | `test_ra_fun_006_repli_verrouille_puis_retour_explicite` |

## Independence requirements (RA-IND)

| ID | Statement | Mechanism | Test(s) |
|---|---|---|---|
| RA-IND-001 | The monitor never accesses the decision layer's internal state — only the proposed action and the estimate | Fingerprint of the decision layer computed from observable outputs only | `test_ra_ind_001_empreinte_sans_acces_interne` |
| RA-IND-003 | Absence of a candidate action at the deadline is itself a fallback trigger | `TIMEOUT_ACTION` cause, verdict REPLI | `test_ra_ind_003_absence_d_action_vaut_repli` |
| RA-IND-004 | Every trace record carries the constraint-set version; set updates are authorized and traced | `version_jeu` field; `mettre_a_jour_jeu()` | `test_ra_ind_004_mise_a_jour_jeu_autorisee_et_tracee` |

## Trace requirements (RA-TRC)

| ID | Statement | Mechanism | Test(s) |
|---|---|---|---|
| RA-TRC-001 | One record per cycle | Ring buffer written once per `decider()` call | `test_ra_fun_001_un_verdict_par_cycle` (buffer occupancy asserted) |
| RA-TRC-002 | Records are self-describing: decodable without access to the decision layer | Packet C format with embedded metadata | `test_paquet_c_autodescriptif_et_integre` |
| RA-TRC-004 | The recorded cause distinguishes envelope-triggered from uncertainty-triggered fallback | `Cause.ENVELOPPE` vs `Cause.INCERTITUDE` | `test_ra_trc_004_causes_distinguees` |
| RA-TRC-005 | Every record carries the schema version | Schema version field in packet C | `test_paquet_c_autodescriptif_et_integre` |
| RA-TRC-006 | On a fallback verdict, a context window [event − n_pre, event + n_post] is frozen for later extraction | `gele` window in the recorder | `test_ra_trc_006_fenetre_figee_extractible` |

## Resource requirements (RA-RES)

| ID | Statement | Mechanism | Test(s) |
|---|---|---|---|
| RA-RES-001 / RA-RES-002 | Memory is bounded (fixed-size records, fixed-capacity buffer) — formal proof deferred to the port to the target language | Fixed-size records (16/48/160 bytes), fixed-capacity ring buffer | `test_formats_16_48_160`, `test_tampon_reboucle_sans_perte` |
| RA-RES-003 | Worst-case execution time is bounded | Bounded evaluation loop (fixed horizon, no dynamic allocation) in `filtre.py` | — (structure only; WCET measured at porting) |
| RA-RES-004 | Trace saturation degrades the trace, never the verdict | Non-blocking write; verdict returned regardless of buffer state | `test_ra_res_004_005_saturation_trace_jamais_verdict` |
| RA-RES-005 | Every lost record is counted | `pertes` counter in the recorder | `test_ra_res_004_005_saturation_trace_jamais_verdict` |

## Supervision requirements (RA-SUR)

| ID | Statement | Mechanism | Test(s) |
|---|---|---|---|
| RA-SUR-001 | Monitoring the monitor's liveness belongs to the platform FDIR, not to the monitor itself | Scope exclusion; `ChienDeGarde` provided as a stand-in for the ground segment | — (exclusion of scope, documented in `moniteur.py`) |
| RA-SUR-002 | A heartbeat signal is emitted at every cycle | `_vie` counter incremented in `decider()`; watchdog checks progression | `test_ra_sur_002_chien_de_garde` |

## Notes

- Numbering gaps (RA-IND-002, RA-TRC-003) exist in the source specification and are
  preserved here for traceability.
- The falsified hypothesis H4 corresponds to RA-FUN-003: the campaign shows the
  mechanism works as specified but brings no benefit in the tested scenario.
