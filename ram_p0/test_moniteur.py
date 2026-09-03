"""Tests du moniteur P0 — chaque test est rattaché à une exigence RAM-SPEC-0001.

Exécution : python3 -m pytest test_moniteur.py -q
"""

from __future__ import annotations

import math

import pytest

from contraintes import Contrainte, Sens
from demo_eps import (DT, ETAT_INITIAL, SIGMAS_NOMINALES, ModeleEPS,
                      contraintes_eps, faire_moniteur, politique_repli_eps)
from filtre import trajectoire_sure
from moniteur import (Cause, ChienDeGarde, JeuInvalide, MiseAJourRefusee,
                      Mode, Moniteur, Verdict, compiler_jeu)
from trace import (TAILLE_A, TAILLE_B, TAILLE_C, Enregistrement, TamponAnneau,
                   VERSION_SCHEMA, depaqueter_c)

SIG = SIGMAS_NOMINALES
CANDIDAT_SUR = 1.0
CANDIDAT_AGRESSIF = 2.8


def test_formats_16_48_160():
    e = Enregistrement(t_s=12.34, seq=7, version_jeu=3, verdict=1, cause=1,
                       mode=0, indice_contrainte=0, marge=0.25, confiance=0.9,
                       etat=[0.5, 21.0], incertitudes=list(SIG),
                       marges=[0.3, 0.8], action_candidate=[2.8],
                       action_transmise=[1.4])
    assert len(e.paquet_a()) == TAILLE_A == 16
    assert len(e.paquet_b()) == TAILLE_B == 48
    assert len(e.paquet_c()) == TAILLE_C == 160


def test_paquet_c_autodescriptif_et_integre():
    """RA-TRC-005 : version de schéma incluse ; RA-TRC-002 : décodage autonome."""
    e = Enregistrement(t_s=100.0, seq=42, version_jeu=5, verdict=2, cause=2,
                       mode=1, indice_contrainte=0, marge=-0.1, confiance=0.4,
                       etat=[0.36, 22.0], incertitudes=list(SIG),
                       marges=[-0.05, 0.7], action_candidate=[2.8],
                       action_transmise=[0.0])
    d = depaqueter_c(e.paquet_c())
    assert d["version_schema"] == VERSION_SCHEMA
    assert d["version_jeu"] == 5 and d["seq"] == 42
    assert d["verdict"] == 2 and d["cause"] == 2 and d["mode"] == 1
    assert d["indice_contrainte"] == 0
    assert d["etat"][0] == pytest.approx(0.36, abs=1e-6)
    assert d["action_candidate"][0] == pytest.approx(2.8)
    blob = bytearray(e.paquet_c())
    blob[20] ^= 0xFF
    with pytest.raises(ValueError):
        depaqueter_c(bytes(blob))  # corruption détectée par CRC


def test_ra_fun_001_un_verdict_par_cycle():
    m, _ = faire_moniteur(capacite_tampon=512)
    etat = list(ETAT_INITIAL)
    for k in range(200):
        r = m.cycle(k * DT, etat, SIG, True, CANDIDAT_SUR)
        assert r.verdict in set(Verdict)
    assert m._tampon.occupation == 200  # RA-TRC-001


def test_autorise_zero_intervention():
    """W&Z : une candidate sûre n'est jamais modifiée."""
    m, _ = faire_moniteur()
    r = m.cycle(0.0, [0.60, 20.0], SIG, True, CANDIDAT_SUR)
    assert r.verdict is Verdict.AUTORISE
    assert r.action_transmise == CANDIDAT_SUR


def test_modifie_est_l_intervention_minimale():
    """État proche de la limite : la candidate est ramenée au plus près de la
    borne admissible — pas au repli (coût ||v0 - u_candidat|| de W&Z)."""
    m, modele = faire_moniteur()
    modele.en_lumiere = False
    etat = [0.407, 20.0]
    r = m.cycle(0.0, etat, SIG, True, CANDIDAT_AGRESSIF)
    assert r.verdict is Verdict.MODIFIE
    assert r.action_transmise < CANDIDAT_AGRESSIF
    jeu = m._jeu
    ok, _, _ = trajectoire_sure(etat, SIG, r.action_transmise, modele,
                                jeu.contraintes, jeu.horizon_pas,
                                jeu.pas_armement_max, politique_repli_eps, DT)
    assert ok
    ok_plus, _, _ = trajectoire_sure(etat, SIG, r.action_transmise + 0.05, modele,
                                     jeu.contraintes, jeu.horizon_pas,
                                     jeu.pas_armement_max, politique_repli_eps, DT)
    assert not ok_plus


def test_repli_enveloppe_quand_rien_n_est_admissible():
    m, modele = faire_moniteur()
    modele.en_lumiere = False
    r = m.cycle(0.0, [0.395, 20.0], SIG, True, CANDIDAT_AGRESSIF)
    assert r.verdict is Verdict.REPLI
    assert r.cause is Cause.VIOLATION_ENVELOPPE
    assert r.action_transmise == politique_repli_eps(None)


def test_ra_fun_003_incertitude_declenche_repli():
    """Valeur nominale sûre, mais sigma_soc > seuil -> REPLI (H4)."""
    m, _ = faire_moniteur()
    r = m.cycle(0.0, [0.60, 20.0], [0.08, 0.5], True, CANDIDAT_SUR)
    assert r.verdict is Verdict.REPLI
    assert r.cause is Cause.INCERTITUDE
    assert r.indice_contrainte == 0


def test_ra_trc_004_causes_distinguees():
    """REPLI-enveloppe et REPLI-incertitude sont deux causes différentes."""
    m, modele = faire_moniteur()
    modele.en_lumiere = False
    r1 = m.cycle(0.0, [0.395, 20.0], SIG, True, CANDIDAT_AGRESSIF)
    m2, _ = faire_moniteur()
    r2 = m2.cycle(0.0, [0.60, 20.0], [0.08, 0.5], True, CANDIDAT_SUR)
    assert r1.cause is Cause.VIOLATION_ENVELOPPE
    assert r2.cause is Cause.INCERTITUDE


def test_ra_ind_003_absence_d_action_vaut_repli():
    m, _ = faire_moniteur()
    r = m.cycle(0.0, list(ETAT_INITIAL), SIG, True, None)
    assert r.verdict is Verdict.REPLI
    assert r.cause is Cause.TIMEOUT_ACTION


def test_ra_fun_002_indetermine_traite_comme_repli():
    m, _ = faire_moniteur()
    r = m.cycle(0.0, list(ETAT_INITIAL), SIG, False, CANDIDAT_SUR)
    assert r.verdict is Verdict.INDETERMINE
    assert r.action_transmise == politique_repli_eps(None)
    assert m.mode is Mode.REPLI


def test_ra_fun_006_repli_verrouille_puis_retour_explicite():
    m, modele = faire_moniteur(cycles_retour=3, dwell_retour_s=10.0)
    modele.en_lumiere = False
    r0 = m.cycle(0.0, [0.395, 20.0], SIG, True, CANDIDAT_AGRESSIF)
    assert r0.verdict is Verdict.REPLI
    r1 = m.cycle(5.0, [0.60, 20.0], SIG, True, CANDIDAT_SUR)
    assert r1.verdict is Verdict.REPLI and r1.cause is Cause.REPLI_VERROUILLE
    r2 = m.cycle(10.0, [0.60, 20.0], SIG, True, CANDIDAT_SUR)
    assert r2.verdict is Verdict.REPLI
    r3 = m.cycle(15.0, [0.60, 20.0], SIG, True, CANDIDAT_SUR)
    assert r3.verdict is Verdict.AUTORISE
    assert m.mode is Mode.NOMINAL
    assert any("retour au nominal" in msg for _, msg in m.notifications)


def test_ra_fun_005_jeu_invalide_rejete_a_la_compilation():
    """Sans marge de garde, le repli n'est plus atteignable depuis la frontière
    en éclipse (le bus seul décharge) : le jeu doit être refusé."""
    modele = ModeleEPS()
    modele.en_lumiere = False
    c_mauvaise = Contrainte("C0_SANS_MARGE", 0, Sens.MIN, 0.35, 1.0, 0.05,
                            delai_armement_s=120.0, marge_securite=0.0)
    with pytest.raises(JeuInvalide):
        compiler_jeu(9, [c_mauvaise], modele, politique_repli_eps, DT,
                     etat_nominal=[0.6, 20.0], bornes_action=(0.0, 3.0))


def test_ra_fun_005_armement_long_rejete():
    """Même contrainte C0, mais délai d'armement de 300 s : l'action la plus
    défavorable persistée 300 s depuis la frontière franchit le seuil brut.
    Avec un pas_armement nul (ancien comportement), le jeu passait."""
    modele = ModeleEPS()
    modele.en_lumiere = False
    c0_lente = Contrainte("C0_SOC_MIN", 0, Sens.MIN, 0.35, 1.0, 0.05,
                          delai_armement_s=300.0, marge_securite=0.02)
    with pytest.raises(JeuInvalide):
        compiler_jeu(10, [c0_lente], modele, politique_repli_eps, DT,
                     etat_nominal=[0.6, 20.0], bornes_action=(0.0, 3.0))


def test_ra_fun_004_horizon_couvre_le_delai_d_armement():
    modele = ModeleEPS()
    c_lente = Contrainte("C_LENTE", 1, Sens.MAX, 45.0, 50.0, 2.0,
                         delai_armement_s=300.0, marge_securite=1.0)
    jeu = compiler_jeu(2, [c_lente], modele, politique_repli_eps, DT,
                       etat_nominal=[0.6, 20.0], bornes_action=(0.0, 3.0))
    assert jeu.horizon_pas >= 300.0 / DT


def test_ra_ind_004_mise_a_jour_jeu_autorisee_et_tracee():
    m, _ = faire_moniteur()
    modele = ModeleEPS()
    modele.en_lumiere = False
    with pytest.raises(MiseAJourRefusee):
        m.mettre_a_jour_jeu(m._jeu, autorisation=False, t_s=0.0)
    jeu_v2 = compiler_jeu(2, contraintes_eps(), modele, politique_repli_eps, DT,
                          etat_nominal=[0.6, 20.0], bornes_action=(0.0, 3.0))
    m.mettre_a_jour_jeu(jeu_v2, autorisation=True, t_s=5.0)
    m.cycle(10.0, list(ETAT_INITIAL), SIG, True, CANDIDAT_SUR)
    enregistrements = m._tampon.extraire_plage(0.0, 1e9)
    assert enregistrements
    d = depaqueter_c(enregistrements[-1][1])
    assert d["version_jeu"] == 2


def test_tampon_reboucle_sans_perte():
    """Rebouclage : 30 cycles nominaux dans un tampon de 8 — occupation 8, et
    les séquences conservées sont les 8 dernières. Aucun gel en nominal, donc
    aucune perte ne doit être comptée."""
    m, modele = faire_moniteur(capacite_tampon=8)
    etat = list(ETAT_INITIAL)
    for k in range(30):
        m.cycle(k * DT, etat, SIG, True, CANDIDAT_SUR)
    conserves = m._tampon.extraire_plage(0.0, 1e9)
    seqs = [seq for seq, _ in conserves]
    assert m._tampon.occupation == 8
    assert seqs == list(range(22, 30))
    assert m._tampon.pertes == 0


def test_ra_res_004_005_saturation_trace_jamais_verdict():
    """Tampon minuscule + fenêtre figée : la trace se perd (comptée), le
    verdict est toujours émis."""
    m, modele = faire_moniteur(capacite_tampon=4, n_pre_gel=2, n_post_gel=2)
    modele.en_lumiere = False
    verdicts = []
    r = m.cycle(0.0, [0.395, 20.0], SIG, True, CANDIDAT_AGRESSIF)  # fige
    verdicts.append(r.verdict)
    for k in range(1, 12):
        r = m.cycle(k * DT, [0.60, 20.0], SIG, True, CANDIDAT_SUR)
        verdicts.append(r.verdict)
    assert all(v in set(Verdict) for v in verdicts)
    assert m._tampon.pertes > 0


def test_ra_trc_006_fenetre_figee_extractible():
    m, modele = faire_moniteur(capacite_tampon=64, n_pre_gel=2, n_post_gel=2)
    modele.en_lumiere = False
    m.cycle(0.0, [0.395, 20.0], SIG, True, CANDIDAT_AGRESSIF)  # non nominal -> gel
    for k in range(1, 4):
        m.cycle(k * DT, [0.60, 20.0], SIG, True, CANDIDAT_SUR)
    gele = m._tampon.extraire_gele()
    assert gele
    assert all(isinstance(b, bytes) and len(b) == TAILLE_C for _, b in gele)
    assert m._tampon.extraire_gele() == []  # extraction consomme le gel


def test_ra_sur_002_chien_de_garde():
    m, _ = faire_moniteur()
    cdg = ChienDeGarde(periode_max_s=2 * DT)
    r = m.cycle(0.0, list(ETAT_INITIAL), SIG, True, CANDIDAT_SUR)
    assert cdg.verifier(0.0, r.vie)
    assert cdg.verifier(5.0, r.vie)        # en retard mais dans la tolérance
    assert not cdg.verifier(20.0, r.vie)   # signal de vie absent -> mode sûr


def test_ra_ind_001_empreinte_sans_acces_interne():
    """L'empreinte ne révèle rien de la couche de décision."""
    m, _ = faire_moniteur()
    m.cycle(0.0, list(ETAT_INITIAL), SIG, True, None)
    m.cycle(5.0, list(ETAT_INITIAL), SIG, True, CANDIDAT_SUR)
    enr = m._tampon.extraire_plage(0.0, 1e9)
    d_none = depaqueter_c(enr[0][1])
    d_ok = depaqueter_c(enr[1][1])
    assert d_none["empreinte_candidate"] == b"\x00\x00\x00"
    assert len(d_ok["empreinte_candidate"]) == 3
    assert d_ok["empreinte_candidate"] != b"\x00\x00\x00"


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-q"]))
