"""Tests des contrôles préenregistrés (§14) — enregistrements SYNTHÉTIQUES."""

from __future__ import annotations

import math
import unittest

from commun import RAM_P4B  # noqa: F401

import controles_p4b as ctl
import analyse_p4b as an


def run(rid, y, v):
    return {"run_id": rid, "Y": y, "V_min": v, "bloc_id": 0,
            "temoin_bruit": 1e-7, "temoin_bloc": "abc"}


class TestRerun(unittest.TestCase):
    def test_identique_bit_a_bit(self):
        a = [run("r1", 0, 7.123456789), run("r2", 1, 4.987654321)]
        b = [run("r1", 0, 7.123456789), run("r2", 1, 4.987654321)]
        r = ctl.comparer_rerun(a, b)
        self.assertTrue(r["identique"])

    def test_divergence_un_ulp(self):
        """Même plateforme : un seul ulp d'écart sur V_min = divergence."""
        a = [run("r1", 0, 7.123456789)]
        b = [run("r1", 0, math.nextafter(7.123456789, 8.0))]
        r = ctl.comparer_rerun(a, b, meme_plateforme=True)
        self.assertFalse(r["identique"])
        # Cross-plateforme : le même écart (rel < 1e-12) est toléré
        r = ctl.comparer_rerun(a, b, meme_plateforme=False)
        self.assertTrue(r["identique"])

    def test_y_identique_obligatoire_meme_cross_plateforme(self):
        a = [run("r1", 0, 7.0)]
        b = [run("r1", 1, 7.0)]
        self.assertFalse(ctl.comparer_rerun(a, b, False)["identique"])

    def test_cross_plateforme_tolerance(self):
        a = [run("r1", 0, 7.0)]
        b = [run("r1", 0, 7.0 * (1 + 5e-13))]   # < 1e-12 relatif
        self.assertTrue(ctl.comparer_rerun(a, b, False)["identique"])
        b = [run("r1", 0, 7.0 * (1 + 5e-12))]   # > 1e-12 relatif
        self.assertFalse(ctl.comparer_rerun(a, b, False)["identique"])

    def test_cardinaux_differents(self):
        self.assertFalse(ctl.comparer_rerun([run("r1", 0, 7.0)], [])["identique"])


class TestDtctrl(unittest.TestCase):
    def test_conforme(self):
        lp = {1.0: "S", 2.0: "I"}
        ld = {1.0: "S", 2.0: "I"}
        r = ctl.comparer_dtctrl(lp, ld, (1.0, 2.0), "V4", "V4")
        self.assertEqual(r["statut"], "CONFORME")

    def test_difference_sans_effet(self):
        lp = {1.0: "S", 2.0: "I", 1.5: "M"}
        ld = {1.0: "S", 2.0: "I", 1.5: "S"}   # label change…
        r = ctl.comparer_dtctrl(lp, ld, (1.0, 2.0, 1.5), "V4", "V4")
        # … mais le verdict est inchangé
        self.assertEqual(r["statut"], "DIFFERENCE_SANS_EFFET")

    def test_divergent_change_verdict(self):
        lp = {1.0: "S", 2.0: "I"}
        ld = {1.0: "S", 2.0: "M"}
        r = ctl.comparer_dtctrl(lp, ld, (1.0, 2.0), "V4", "V5")
        self.assertEqual(r["statut"], "DIVERGENT")
        self.assertEqual(r["effet_verdict"],
                         "INCONCLUSIVE (NUMERICAL SENSITIVITY)")


class TestTemoinsCRN(unittest.TestCase):
    def test_bloc_apparie(self):
        rs = [dict(run(f"b0_rho{rho}", 0, 7.0), bloc_id=0) for rho in
              an.NIVEAUX_RHO]
        r = ctl.verifier_temoins_crn(rs)
        self.assertTrue(r["conforme"])
        self.assertEqual(r["blocs_ok"], 1)

    def test_temoin_divergent_detecte(self):
        rs = [dict(run(f"b0_rho{rho}", 0, 7.0), bloc_id=0) for rho in
              an.NIVEAUX_RHO]
        rs[3]["temoin_bruit"] = 9e-7
        r = ctl.verifier_temoins_crn(rs)
        self.assertFalse(r["conforme"])

    def test_temoin_absent_signale(self):
        rs = [dict(run(f"b0_rho{rho}", 0, 7.0), bloc_id=0) for rho in
              an.NIVEAUX_RHO]
        rs[0]["temoin_bruit"] = None
        self.assertFalse(ctl.verifier_temoins_crn(rs)["conforme"])


if __name__ == "__main__":
    unittest.main()
