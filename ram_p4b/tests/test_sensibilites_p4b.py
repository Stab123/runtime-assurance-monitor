"""Tests des sensibilités préenregistrées (§13) — dégradation seule.
Labels et comptages SYNTHÉTIQUES."""

from __future__ import annotations

import unittest

from commun import RAM_P4B  # noqa: F401

import analyse_p4b as an
import sensibilites_p4b as sens

R = an.NIVEAUX_RHO


def labels(d):
    return {rho: d.get(k, "M") for k, rho in enumerate(R)}


class TestDegradationSeule(unittest.TestCase):
    def test_variante_confirmante(self):
        vp = an.verdict_p4b(labels({0: "S", 1: "S", 4: "I"}))   # V4
        vv = an.verdict_p4b(labels({0: "S", 1: "S", 4: "I"}))
        r = sens.combiner_sensibilite(vp, {"ocv_plus": vv}, "OCV")
        self.assertEqual(r["code"], "V4")                       # inchangé
        self.assertEqual(r["b_star"], vp["b_star"])             # jamais déplacé

    def test_transition_declassee(self):
        """V4 + variante sans frontière → FRONTIER NOT LOCALIZED
        (OCV SENSITIVE), b_star effacé (jamais réécrit)."""
        vp = an.verdict_p4b(labels({0: "S", 1: "S", 4: "I"}))   # V4
        vv = an.verdict_p4b(labels({0: "S", 1: "S", 4: "S"}))   # V5
        r = sens.combiner_sensibilite(vp, {"ocv_moins": vv}, "OCV")
        self.assertEqual(r["code"], "V4-SENS")
        self.assertEqual(r["verdict"], "FRONTIER NOT LOCALIZED (OCV SENSITIVE)")
        self.assertIsNone(r["b_star"])

    def test_transition_deplacee_declassee(self):
        """Frontière déplacée sous la variante → déclassement aussi."""
        vp = an.verdict_p4b(labels({0: "S", 1: "S", 4: "I"}))
        vv = an.verdict_p4b(labels({0: "S", 1: "S", 2: "S", 4: "I"}))
        r = sens.combiner_sensibilite(vp, {"ocv_plus": vv}, "OCV")
        self.assertEqual(r["code"], "V4-SENS")
        self.assertIsNone(r["b_star"])

    def test_jamais_de_promotion_vers_transition(self):
        """Un verdict autre ne devient JAMAIS TRANSITION DETECTED sous
        variante : annotation seule, code et verdict de base inchangés."""
        vp = an.verdict_p4b(labels({}))                          # V7
        vv = an.verdict_p4b(labels({0: "S", 4: "I"}))            # V4 sous variante
        r = sens.combiner_sensibilite(vp, {"flags": vv}, "FLAG")
        self.assertEqual(r["code"], "V7")                        # PAS de promotion
        self.assertIn("FLAG-SENSITIVE", r["verdict"])
        self.assertIsNone(r["b_star"])

    def test_annotation_verdict_non_transition(self):
        vp = an.verdict_p4b(labels({0: "I"}))                    # V2
        vv = an.verdict_p4b(labels({0: "M"}))                    # V7 sous variante
        r = sens.combiner_sensibilite(vp, {"ocv_plus": vv}, "OCV")
        self.assertEqual(r["code"], "V2")
        self.assertIn("OCV-SENSITIVE", r["verdict"])

    def test_robuste_si_deux_variantes_confirment(self):
        vp = an.verdict_p4b(labels({0: "S", 1: "S", 4: "I"}))
        vv = an.verdict_p4b(labels({0: "S", 1: "S", 4: "I"}))
        r = sens.combiner_sensibilites_ocv(vp, labels({0: "S", 1: "S", 4: "I"}),
                                           labels({0: "S", 1: "S", 4: "I"}))
        self.assertEqual(r["code"], "V4")
        self.assertIn("robuste à l'incertitude OCV locale", r["verdict"])
        self.assertEqual(vv["code"], "V4")

    def test_variante_invalide_n_invalide_pas_le_principal(self):
        """Run invalide dans une campagne de sensibilité : annotation
        « analyse invalide », verdict principal intact (§12 V0)."""
        vp = an.verdict_p4b(labels({0: "S", 1: "S", 4: "I"}))
        r = sens.combiner_sensibilites_ocv(vp,
                                           labels({0: "S", 1: "S", 4: "I"}),
                                           labels({0: "S", 1: "S", 4: "I"}),
                                           n_invalid_moins=1)
        self.assertEqual(r["code"], "V4")
        self.assertIn("invalide", r["sensibilites"]["ocv_moins"])

    def test_variante_ocv_plus_invalide(self):
        """Variante OCV+ invalide (n_invalid_plus >= 1) : annotation
        « analyse invalide » sur ocv_plus, verdict principal intact,
        ocv_moins traitée normalement, jamais de mention « robuste »."""
        vp = an.verdict_p4b(labels({0: "S", 1: "S", 4: "I"}))
        r = sens.combiner_sensibilites_ocv(vp,
                                           labels({0: "S", 1: "S", 4: "I"}),
                                           labels({0: "S", 1: "S", 4: "I"}),
                                           n_invalid_plus=1)
        self.assertEqual(r["code"], "V4")
        self.assertEqual(r["b_star"], vp["b_star"])
        self.assertIn("invalide", r["sensibilites"]["ocv_plus"])
        self.assertEqual(r["sensibilites"]["ocv_moins"],
                         "confirme le verdict principal")
        self.assertNotIn("robuste", r["verdict"])

    def test_deux_variantes_invalides(self):
        """Deux variantes OCV invalides : deux annotations, verdict
        principal strictement inchangé (code, verdict, b_star)."""
        vp = an.verdict_p4b(labels({0: "S", 1: "S", 4: "I"}))
        r = sens.combiner_sensibilites_ocv(vp,
                                           labels({0: "S", 1: "S", 4: "I"}),
                                           labels({0: "S", 1: "S", 4: "I"}),
                                           n_invalid_plus=1,
                                           n_invalid_moins=1)
        self.assertEqual(r["code"], "V4")
        self.assertEqual(r["verdict"], vp["verdict"])
        self.assertEqual(r["b_star"], vp["b_star"])
        self.assertIn("invalide", r["sensibilites"]["ocv_plus"])
        self.assertIn("invalide", r["sensibilites"]["ocv_moins"])

    def test_labels_ocv_plus_none(self):
        """labels_ocv_plus=None : variante analysée comme absente
        (jamais envoyée à _verdict_variante), ocv_moins traitée."""
        vp = an.verdict_p4b(labels({0: "S", 1: "S", 4: "I"}))
        r = sens.combiner_sensibilites_ocv(vp, None,
                                           labels({0: "S", 1: "S", 4: "I"}))
        self.assertEqual(r["code"], "V4")
        self.assertNotIn("ocv_plus", r["sensibilites"])
        self.assertEqual(r["sensibilites"]["ocv_moins"],
                         "confirme le verdict principal")

    def test_labels_ocv_moins_none(self):
        """labels_ocv_moins=None : comportement strictement symétrique
        de labels_ocv_plus=None."""
        vp = an.verdict_p4b(labels({0: "S", 1: "S", 4: "I"}))
        r = sens.combiner_sensibilites_ocv(vp,
                                           labels({0: "S", 1: "S", 4: "I"}),
                                           None)
        self.assertEqual(r["code"], "V4")
        self.assertNotIn("ocv_moins", r["sensibilites"])
        self.assertEqual(r["sensibilites"]["ocv_plus"],
                         "confirme le verdict principal")

    def test_aucune_variante_disponible(self):
        """Aucune variante (None, None) : sortie = verdict principal
        inchangé, aucune annotation, aucune mention « robuste »."""
        vp = an.verdict_p4b(labels({0: "S", 1: "S", 4: "I"}))
        r = sens.combiner_sensibilites_ocv(vp, None, None)
        self.assertEqual(r["code"], "V4")
        self.assertEqual(r["verdict"], vp["verdict"])
        self.assertEqual(r["b_star"], vp["b_star"])
        self.assertEqual(r["sensibilites"], {})

    def test_v4_intact_si_sensibilite_invalide_annotation_seule(self):
        """Verdict principal V4 : une sensibilité techniquement invalide
        ne déclasse PAS la frontière (pas de V4-SENS), n'efface PAS
        b_star — annotation « analyse invalide » seulement."""
        vp = an.verdict_p4b(labels({0: "S", 1: "S", 4: "I"}))
        r = sens.combiner_sensibilites_ocv(vp,
                                           labels({0: "S", 1: "S", 4: "I"}),
                                           None,
                                           n_invalid_plus=1)
        self.assertEqual(r["code"], "V4")
        self.assertNotEqual(r["code"], "V4-SENS")
        self.assertEqual(r["verdict"], vp["verdict"])
        self.assertEqual(r["b_star"], vp["b_star"])
        self.assertIn("invalide", r["sensibilites"]["ocv_plus"])
        self.assertNotIn("ocv_moins", r["sensibilites"])


class TestSensibiliteDrapeaux(unittest.TestCase):
    def test_x_prime(self):
        """x'_j = x_j − x_j^(flag) — reclassification sur comptages
        synthétiques."""
        x = {rho: 40 for rho in R}             # M partout
        xf = {rho: 0 for rho in R}
        xf[R[0]] = 10                          # 40 − 10 = 30 ≤ 34 → S
        vp = an.verdict_p4b({rho: "M" for rho in R})   # V7 principal
        r = sens.sensibilite_drapeaux(x, xf, vp)
        self.assertEqual(r["code"], "V7")      # jamais de promotion
        self.assertIn("FLAG-SENSITIVE", r["verdict"])

    def test_x_flag_borne(self):
        x = {rho: 10 for rho in R}
        xf = {rho: 11 for rho in R}            # x_flag > x : absurde
        with self.assertRaises(ValueError):
            sens.sensibilite_drapeaux(
                x, xf, an.verdict_p4b({rho: "M" for rho in R}))

    def test_drapeaux_ne_changent_rien_si_vide(self):
        x = {rho: 5 for rho in R}              # S partout
        xf = {rho: 0 for rho in R}
        vp = an.verdict_p4b({rho: "S" for rho in R})
        r = sens.sensibilite_drapeaux(x, xf, vp)
        self.assertEqual(r["code"], "V1")


if __name__ == "__main__":
    unittest.main()
