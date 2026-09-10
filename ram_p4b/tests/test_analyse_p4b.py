"""Tests de l'analyse statistique P4b — labels S/I/M SYNTHÉTIQUES, cas
A–J du §12, frontière §10, monotonie §11. Aucune donnée de campagne."""

from __future__ import annotations

import itertools
import unittest

from commun import RAM_P4B  # noqa: F401

import analyse_p4b as an

R = an.NIVEAUX_RHO


def labels(d):
    """{index_niveau: label} -> {rho: label}, M par défaut."""
    return {rho: d.get(k, "M") for k, rho in enumerate(R)}


class TestWilson(unittest.TestCase):
    def test_valeurs_documentees(self):
        """Valeurs du §6 : Wilson99.44(34/5500) ≈ [0.0039 ; 0.0099] ;
        (35/5500) ≈ [0.0040 ; 0.0101] ; (320/5500) ≈ [0.0500 ; 0.0676] ;
        (319/5500) ≈ [0.0499 ; 0.0674] ; (0/5500) = [0 ; 0.0014]."""
        lo, hi = an.wilson_ic(34, 5500)
        self.assertAlmostEqual(lo, 0.0039, places=4)
        self.assertAlmostEqual(hi, 0.0099, places=4)
        self.assertLessEqual(hi, 0.01)
        lo, hi = an.wilson_ic(35, 5500)
        self.assertAlmostEqual(lo, 0.0040, places=4)
        self.assertAlmostEqual(hi, 0.0101, places=4)
        self.assertGreater(hi, 0.01)
        lo, hi = an.wilson_ic(320, 5500)
        self.assertAlmostEqual(lo, 0.0500, places=4)
        self.assertGreaterEqual(lo, 0.05)
        lo, hi = an.wilson_ic(319, 5500)
        self.assertAlmostEqual(lo, 0.0499, places=4)
        self.assertLess(lo, 0.05)
        lo, hi = an.wilson_ic(0, 5500)
        self.assertAlmostEqual(lo, 0.0, places=15)   # 0 mathématique ;
        # résidu float ~1e-19 sans impact décisionnel (seule la borne sup
        # compte pour SUFFICIENT à x = 0 ; la borne inf sert à x ≥ 320)
        self.assertAlmostEqual(hi, 0.0014, places=4)

    def test_bornes_dans_0_1(self):
        for x in (0, 1, 34, 35, 319, 320, 2750, 5499, 5500):
            lo, hi = an.wilson_ic(x, 5500)
            self.assertTrue(-1e-15 <= lo <= hi <= 1.0 + 1e-15)

    def test_z_gele(self):
        self.assertEqual(an.Z_WILSON, 2.7729212946086634)


class TestClassification(unittest.TestCase):
    def test_seuils_entiers(self):
        self.assertEqual(an.classifier_niveau(0), "S")
        self.assertEqual(an.classifier_niveau(34), "S")
        self.assertEqual(an.classifier_niveau(35), "M")
        self.assertEqual(an.classifier_niveau(319), "M")
        self.assertEqual(an.classifier_niveau(320), "I")
        self.assertEqual(an.classifier_niveau(5500), "I")

    def test_equivalence_bornes_seuils_exhaustive(self):
        """Les deux méthodes (bornes §5 / seuils entiers §6) coïncident
        pour TOUT x ∈ [0 ; 5500] — exigence du mandat."""
        self.assertTrue(an.verifier_equivalence_seuils())

    def test_seuils_entiers_refusent_autre_n(self):
        with self.assertRaises(ValueError):
            an.classifier_niveau_seuils(10, 500)


class TestMonotonie(unittest.TestCase):
    def test_inversion_dure(self):
        self.assertFalse(an.inversion_dure(labels({0: "S", 8: "I"})))
        self.assertTrue(an.inversion_dure(labels({0: "I", 8: "S"})))
        self.assertTrue(an.inversion_dure(labels({3: "I", 7: "S"})))
        # I après S n'est pas une inversion dure
        self.assertFalse(an.inversion_dure(labels({2: "S", 5: "I"})))
        # M ne participe pas
        self.assertFalse(an.inversion_dure(labels({0: "I", 4: "M"})))

    def test_frontiere_intervalle(self):
        f = an.frontiere(labels({3: "S", 4: "I"}))
        self.assertTrue(f["existe"])
        self.assertEqual((f["borne_inf"], f["borne_sup"]), (R[3], R[4]))
        self.assertAlmostEqual(f["largeur"], 0.125)
        self.assertFalse(f["low_resolution"])

    def test_low_resolution_strict(self):
        """LOW RESOLUTION ssi largeur > 0.250 STRICT (§10) : 0.250 exact
        (un seul M) n'est PAS annoté ; 0.375 (deux M) l'est."""
        f1 = an.frontiere(labels({3: "S", 5: "I"}))   # largeur 0.250
        self.assertAlmostEqual(f1["largeur"], 0.250)
        self.assertFalse(f1["low_resolution"])
        f2 = an.frontiere(labels({3: "S", 6: "I"}))   # largeur 0.375
        self.assertAlmostEqual(f2["largeur"], 0.375)
        self.assertTrue(f2["low_resolution"])


class TestVerdicts(unittest.TestCase):
    def test_v0_invalide_technique(self):
        v = an.verdict_p4b(labels({i: "S" for i in range(9)}),
                           n_invalid_technique=1)
        self.assertEqual(v["code"], "V0")

    def test_v0_prioritaire_sur_tout(self):
        v = an.verdict_p4b(labels({0: "I"}), n_invalid_technique=3,
                           fraction_flag=0.9)
        self.assertEqual(v["code"], "V0")

    def test_v0b_garde_fou_strict(self):
        """Fraction > 25 % STRICT (§9) : 25.000 % exact ne déclenche PAS."""
        lab = labels({i: "S" for i in range(9)})
        v = an.verdict_p4b(lab, fraction_flag=0.25)
        self.assertEqual(v["code"], "V1")
        v = an.verdict_p4b(lab, fraction_flag=0.2500000001)
        self.assertEqual(v["code"], "V0b")

    def test_v1_tout_suffisant(self):
        v = an.verdict_p4b(labels({i: "S" for i in range(9)}))
        self.assertEqual(v["code"], "V1")

    def test_v2_baseline_insuffisant(self):
        v = an.verdict_p4b(labels({0: "I"}))
        self.assertEqual(v["code"], "V2")

    def test_v2_prioritaire_sur_inversion(self):
        """Cas J du §12 : V2 ∧ inversion dure → V2, inversion documentée."""
        v = an.verdict_p4b(labels({0: "I", 5: "S"}))
        self.assertEqual(v["code"], "V2")
        self.assertTrue(v["inversion_dure"])

    def test_v3_inversion(self):
        v = an.verdict_p4b(labels({2: "I", 6: "S"}))
        self.assertEqual(v["code"], "V3")
        self.assertIsNone(v["b_star"])

    def test_v4_transition(self):
        v = an.verdict_p4b(labels({0: "S", 1: "S", 2: "S", 3: "S", 4: "I"}))
        self.assertEqual(v["code"], "V4")
        self.assertEqual(v["b_star"], (R[3], R[4]))
        self.assertFalse(v["low_resolution"])

    def test_v4_low_resolution(self):
        v = an.verdict_p4b(labels({0: "S", 3: "I"}))  # largeur 0.375
        self.assertEqual(v["code"], "V4")
        self.assertTrue(v["low_resolution"])
        self.assertIn("LOW RESOLUTION", v["verdict"])

    def test_v5_borne_superieure(self):
        v = an.verdict_p4b(labels({0: "S", 4: "S"}))
        self.assertEqual(v["code"], "V5")
        self.assertEqual(v["b_star"], (R[4], None))

    def test_v6_borne_inferieure(self):
        v = an.verdict_p4b(labels({5: "I"}))
        self.assertEqual(v["code"], "V6")
        self.assertEqual(v["b_star"], (None, R[5]))

    def test_v7_inconclusif(self):
        v = an.verdict_p4b(labels({}))
        self.assertEqual(v["code"], "V7")

    def test_cas_A_a_J(self):
        """Couverture des cas du mandat (§12)."""
        cas = {
            "A": (labels({i: "S" for i in range(9)}), "V1"),   # 0 viol. partout
            "B": (labels({0: "I"}), "V2"),                     # viol. dès ρ=1
            "C": (labels({0: "S", 1: "S", 4: "I"}), "V4"),     # transition
            "D1": (labels({3: "I"}), "V6"),                    # sans classif. nette
            "D2": (labels({}), "V7"),
            "E": (labels({0: "S", 3: "I"}), "V4"),             # M entre S et I
            "F": (labels({2: "I", 6: "S"}), "V3"),             # non monotone
            "G": (labels({0: "S", 8: "S"}), "V5"),             # frontière > 2
        }
        for nom, (lab, code) in cas.items():
            with self.subTest(cas=nom):
                self.assertEqual(an.verdict_p4b(lab)["code"], code)
        # H : trop de hors-domaine → V0b
        self.assertEqual(an.verdict_p4b(cas["A"][0], fraction_flag=0.30)["code"],
                         "V0b")
        # I : anomalie technique → V0
        self.assertEqual(an.verdict_p4b(cas["A"][0], n_invalid_technique=1)["code"],
                         "V0")
        # J : V2 ∧ inversion → V2 prioritaire
        self.assertEqual(an.verdict_p4b(labels({0: "I", 5: "S"}))["code"], "V2")

    def test_exhaustivite_partition(self):
        """Les cas V1–V7 partitionnent l'espace des labels : les 3^9
        combinaisons de labels donnent chacune EXACTEMENT un verdict,
        et les niveaux M n'introduisent aucun trou."""
        codes = set()
        for combo in itertools.product("SIM", repeat=9):
            lab = {rho: combo[i] for i, rho in enumerate(R)}
            v = an.verdict_p4b(lab)
            self.assertIn(v["code"],
                          {"V1", "V2", "V3", "V4", "V5", "V6", "V7"})
            codes.add(v["code"])
        self.assertEqual(codes, {"V1", "V2", "V3", "V4", "V5", "V6", "V7"})

    def test_labels_incomplets_refuses(self):
        with self.assertRaises(ValueError):
            an.verdict_p4b({R[0]: "S"})
        with self.assertRaises(ValueError):
            an.verdict_p4b(labels({0: "X"}))


class TestFractionFlag(unittest.TestCase):
    def test_fraction_sur_runs_valides(self):
        runs = [{"invalid_technique": False, "outside_domain": True},
                {"invalid_technique": False, "outside_domain": False},
                {"invalid_technique": False, "outside_domain": False},
                {"invalid_technique": True, "outside_domain": True}]
        self.assertAlmostEqual(an.fraction_flaggee(runs), 1 / 3)


if __name__ == "__main__":
    unittest.main()
