"""Tests du modèle physique P4b — invariants physiques sur CAS JOUETS
(v0.6 §5, §7.2 ; préenregistrement §4). Aucun bloc du design réel."""

from __future__ import annotations

import math
import unittest

from commun import GRAINE_TOY, PARAMS_TOY  # noqa: F401

from modele_p4b import (C_CELL_AH, N_S, PlanteP4b, TablesPhysiques,
                        V_MIN_PACK, est_fini, hors_domaine)


class TestModele(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.t = TablesPhysiques.charger()

    def plante(self, rho=1.0, **kw):
        p = dict(PARAMS_TOY, **kw)
        return PlanteP4b(p, rho, self.t)

    # --- Vp(t0) : règle gelée §7.2-E -----------------------------------------

    def test_vp_init_regle_gelee(self):
        """Vp(t0) = rho · Rp(SoC0) · I_BASE · C_cell / C_BATT."""
        for rho in (1.0, 1.375, 2.0):
            pl = self.plante(rho)
            attendu = rho * self.t.rp(PARAMS_TOY["soc0"]) \
                * PARAMS_TOY["I_BASE"] * C_CELL_AH / PARAMS_TOY["C_BATT_AH"]
            self.assertEqual(pl.vp, attendu)

    def test_vp_init_positif_eclipse_prerun(self):
        """L'éclipse pré-run décharge (u=0) : Vp(t0) > 0 (chute resistive)."""
        self.assertGreater(self.plante().vp, 0.0)

    # --- convention de courant signée (§5) ------------------------------------

    def test_i_batt_signe(self):
        pl = self.plante()
        pl.en_lumiere = False            # éclipse : décharge
        self.assertAlmostEqual(pl.i_batt(0.0), 0.5)
        self.assertAlmostEqual(pl.i_batt(3.0), 3.5)
        pl.en_lumiere = True             # lumière : charge nette possible
        self.assertAlmostEqual(pl.i_batt(0.0), 0.5 - 1.2)   # < 0 = charge
        self.assertAlmostEqual(pl.i_batt(3.0), 3.5 - 1.2)

    def test_i_cell_partage_courant(self):
        pl = self.plante()
        pl.en_lumiere = False
        self.assertAlmostEqual(pl.i_cell(3.0),
                               3.5 * C_CELL_AH / PARAMS_TOY["C_BATT_AH"])

    # --- V_pack : formule gelée ------------------------------------------------

    def test_v_pack_formule(self):
        pl = self.plante(rho=1.75)
        pl.en_lumiere = False
        soc, vp, u = 0.55, 0.012, 3.0
        ic = (PARAMS_TOY["I_BASE"] + u - 0.0) * C_CELL_AH / PARAMS_TOY["C_BATT_AH"]
        attendu = N_S * (self.t.ocv(soc) - ic * 1.75 * self.t.rs(soc) - vp)
        self.assertEqual(pl.v_pack(soc, vp, u), attendu)

    def test_u_exec_utilise_dans_v_pack(self):
        """Le courant EFFECTIVEMENT appliqué (u_exec après moniteur) est
        utilisé — y compris en repli (u_exec = 0)."""
        pl = self.plante()
        pl.en_lumiere = False
        soc, vp = 0.55, 0.01
        self.assertNotEqual(pl.v_pack(soc, vp, 3.0), pl.v_pack(soc, vp, 0.0))
        # En repli (u_exec = 0) la chute ohmique est celle du bus seul :
        v_repli = pl.v_pack(soc, vp, 0.0)
        attendu = N_S * (self.t.ocv(soc)
                         - PARAMS_TOY["I_BASE"] * C_CELL_AH
                         / PARAMS_TOY["C_BATT_AH"] * self.t.rs(soc) - vp)
        self.assertEqual(v_repli, attendu)

    # --- rôle de rho (§7.2-B) ---------------------------------------------------

    def test_rho_scale_rs_rp_pas_cp(self):
        """rho multiplie Rs et Rp ; Cp n'est PAS scalé."""
        soc, vp, u = 0.55, 0.02, 3.0
        p1 = self.plante(rho=1.0)
        p2 = self.plante(rho=2.0)
        for p in (p1, p2):
            p.en_lumiere = False
        ic = p1.i_cell(u)
        d1 = p1.dvp(soc, vp, ic)
        d2 = p2.dvp(soc, vp, ic)
        rp, cp = self.t.rp(soc), self.t.cp(soc)
        self.assertEqual(d1, -vp / (1.0 * rp * cp) + ic / cp)
        self.assertEqual(d2, -vp / (2.0 * rp * cp) + ic / cp)  # Cp non scalé
        # Rs : chute ohmique doublée à rho = 2
        v1 = p1.v_pack(soc, vp, u)
        v2 = p2.v_pack(soc, vp, u)
        self.assertAlmostEqual(v1 - v2, ic * (2.0 - 1.0) * self.t.rs(soc) * N_S)

    def test_rho_ne_change_pas_soc(self):
        """Invariant structurel §7 : la trajectoire SoC ne dépend pas de rho."""
        p1, p2 = self.plante(1.0), self.plante(1.9)
        x1 = [PARAMS_TOY["soc0"], PARAMS_TOY["temp0"]]
        x2 = list(x1)
        for k in range(50):
            t = k * 5.0
            for p in (p1, p2):
                p.en_lumiere = (t % 5400.0) < 3600.0
            u = 3.0 if 600.0 <= (t % 5400.0) < 1500.0 else 0.0
            x1 = p1.pas(x1, u, 5.0)
            x2 = p2.pas(x2, u, 5.0)
            self.assertEqual(x1[0], x2[0])      # bit à bit
        self.assertNotEqual(p1.vp, p2.vp)       # Vp, lui, dépend de rho

    # --- mémoire de Vp (§7.2-E) -------------------------------------------------

    def test_vp_jamais_reinitialise_entree_payload(self):
        """Pas de discontinuité de Vp à l'entrée de la fenêtre payload
        (t = 600 s) : Vp évolue continûment, jamais remis à zéro."""
        pl = self.plante()
        x = [PARAMS_TOY["soc0"], PARAMS_TOY["temp0"]]
        vp_avant = None
        for k in range(130):                    # t jusqu'à 645 s > 600 s
            t = k * 5.0
            pl.en_lumiere = (t % 5400.0) < 3600.0
            u = 3.0 if 600.0 <= (t % 5400.0) < 1500.0 else 0.0
            if vp_avant is not None:
                # continuité : |ΔVp| borné par la dérivée max possible
                self.assertLess(abs(pl.vp - vp_avant), 0.02)
                self.assertNotEqual(pl.vp, 0.0)
            vp_avant = pl.vp
            x = pl.pas(x, u, 5.0)

    def test_vp_relaxation_en_charge(self):
        """En charge nette (I_cell < 0), Vp décroît vers son asymptote
        négative — signe de la convention gelée."""
        pl = self.plante()
        pl.en_lumiere = True
        pl.vp = 0.05
        x = [0.6, 20.0]
        vp0 = pl.vp
        for _ in range(40):
            x = pl.pas(x, 0.0, 5.0)             # charge, pas de payload
        self.assertLess(pl.vp, vp0)

    # --- hors domaine (§7.2-A) : état JAMAIS saturé -----------------------------

    def test_etat_soc_jamais_sature(self):
        """La plante laisse SoC sortir de [0 ; 1] (S6) — seules les tables
        sont clampées."""
        pl = self.plante(soc0=0.98, I_SUN=2.5, I_BASE=0.06, C_BATT_AH=4.4)
        pl.en_lumiere = True
        x = [0.98, 20.0]
        for _ in range(200):                    # charge forte prolongée
            x = pl.pas(x, 0.0, 5.0)
        self.assertGreater(x[0], 1.0)           # dépassement réel, non clampé
        # … et les tables restent évaluables (clamp interne de l'entrée)
        v = pl.v_pack(x[0], pl.vp, 0.0)
        self.assertTrue(math.isfinite(v))

    def test_hors_domaine_flag(self):
        self.assertTrue(hors_domaine(-1e-12))
        self.assertTrue(hors_domaine(1.0 + 1e-12))
        self.assertFalse(hors_domaine(0.0))
        self.assertFalse(hors_domaine(1.0))
        self.assertFalse(hors_domaine(0.5))

    # --- finitude (§4) -----------------------------------------------------------

    def test_est_fini(self):
        self.assertTrue(est_fini(1.0, -2.0, 0.0))
        self.assertFalse(est_fini(float("nan"), 1.0))
        self.assertFalse(est_fini(float("inf")))
        self.assertFalse(est_fini(float("-inf")))

    def test_constantes_gelees(self):
        self.assertEqual(N_S, 2)
        self.assertEqual(C_CELL_AH, 3.35)
        self.assertEqual(V_MIN_PACK, 5.0)       # 2 × 2.5 V (§7.2-D)


if __name__ == "__main__":
    unittest.main()
