"""Tests des tables physiques gelées et des règles de clamp (v0.6 §7.2) —
synthétique : évaluations ponctuelles de tables, aucune trajectoire."""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from commun import RAM_P4B  # noqa: F401

from modele_p4b import (SHA256_OCV, SHA256_RINT, SOC_MAX_RP_CP,
                        TableGeleeModifiee, TablesPhysiques,
                        _interpolation_lineaire)


class TestTables(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.t = TablesPhysiques.charger()

    def test_sha256_verifies_au_chargement(self):
        self.assertEqual(SHA256_OCV,
            "7aa959fc99effefbc995237291217cec1657145051b3fa70cd7678fe0b7154c2")
        self.assertEqual(SHA256_RINT,
            "330efcd3165f5676f06b9128f723566193cc66fa6844fdddbc1f782015697b93")

    def test_table_modifiee_refusee(self):
        """Une table modifiée d'un octet doit faire échouer le chargement."""
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            shutil.copy(RAM_P4B / "data" / "ocv_soc_ncr18650b_hnei.csv", d)
            shutil.copy(RAM_P4B / "data" / "rint_soc_nmc_dtu.csv", d)
            f = d / "ocv_soc_ncr18650b_hnei.csv"
            brut = f.read_bytes()
            f.write_bytes(brut[:-1] + b"X")     # corruption mineure
            with self.assertRaises(TableGeleeModifiee):
                TablesPhysiques.charger(d)

    def test_noeuds_ocv_exacts(self):
        t = self.t
        self.assertEqual(t.ocv(0.0), 2.834)     # extrait gelé v0.6 §7.2-A
        self.assertEqual(t.ocv(0.10), 3.349)
        self.assertEqual(t.ocv(0.50), 3.676)
        self.assertEqual(t.ocv(1.00), 4.179)

    def test_monotonie_ocv(self):
        xs = self.t._soc_ocv
        ys = self.t._ocv_v
        self.assertEqual(len(xs), 51)           # 51 points (v0.6 §7.2-A)
        self.assertTrue(all(y1 < y2 for y1, y2 in zip(ys, ys[1:])))

    def test_noeuds_rint_p35(self):
        t = self.t
        self.assertAlmostEqual(t.rs(0.0), 42.9e-3)      # p35 (v0.6 §7.2-B)
        self.assertAlmostEqual(t.rs(0.5), 38.9e-3)
        self.assertAlmostEqual(t.rs(1.0), 55.7e-3)      # Rs mesuré à 100 %
        self.assertAlmostEqual(t.rp(0.0), 66.6e-3)
        self.assertAlmostEqual(t.rp(0.5), 26.7e-3)
        self.assertAlmostEqual(t.rp(0.9), 20.0e-3)
        self.assertAlmostEqual(t.cp(0.0), 4.0e3)
        self.assertAlmostEqual(t.cp(0.7), 14.1e3)
        self.assertAlmostEqual(t.cp(0.9), 4.3e3)

    def test_interpolation_lineaire_milieu(self):
        t = self.t
        # OCV au milieu du segment [50 % ; 52 %] : moyenne des deux noeuds
        y50, y52 = 3.676, None
        ys = t._ocv_v
        xs = t._soc_ocv
        i50 = xs.index(0.5)
        y52 = ys[i50 + 1]
        self.assertAlmostEqual(
            t.ocv(0.51), y50 + (y52 - y50) * (0.51 - 0.5) / 0.02, places=15)

    def test_clamp_entree_tables_pas_etat(self):
        """Clamp de la VALEUR D'ENTRÉE ; l'état SoC n'est jamais saturé."""
        t = self.t
        self.assertEqual(t.ocv(1.3), t.ocv(1.0))
        self.assertEqual(t.ocv(-0.2), t.ocv(0.0))
        self.assertEqual(t.rs(1.3), t.rs(1.0))
        self.assertEqual(t.rs(-0.2), t.rs(0.0))

    def test_clamp_rp_cp_090(self):
        """Extension > 90 % GELÉE : Rp(SoC>0.90) = Rp(0.90), idem Cp —
        y compris À L'INTÉRIEUR de [0 ; 1]."""
        t = self.t
        for s in (0.9000001, 0.95, 1.0, 1.4):
            self.assertEqual(t.rp(s), t.rp(SOC_MAX_RP_CP))
            self.assertEqual(t.cp(s), t.cp(SOC_MAX_RP_CP))
        # Rs n'est PAS clampé à 90 % (mesuré à 100 %)
        self.assertNotEqual(t.rs(1.0), t.rs(0.9))
        # En dessous de 90 % : interpolation normale (pas de clamp)
        self.assertNotEqual(t.rp(0.85), t.rp(0.9))

    def test_point_100_rint_inaccessible(self):
        """Rp/Cp à SoC = 100 % (NaN dans la table gelée) ne sont jamais
        atteignables : le clamp à 0.90 plafonne l'entrée."""
        t = self.t
        self.assertEqual(t.rp(1.0), t.rp(0.9))
        self.assertEqual(t.cp(1.0), t.cp(0.9))

    def test_variante_ocv_memoire_seule(self):
        """§13 : ±0.1 V aux points SoC {0.00 ; 0.02} UNIQUEMENT, copie en
        mémoire, table d'origine intacte, interpolation inchangée."""
        t = self.t
        avant = list(t._ocv_v)
        vp = t.variante_ocv(+0.1)
        vm = t.variante_ocv(-0.1)
        self.assertEqual(t._ocv_v, avant)                 # originale intacte
        self.assertAlmostEqual(vp.ocv(0.0), 2.834 + 0.1)
        self.assertAlmostEqual(vp.ocv(0.02), 3.162 + 0.1)
        self.assertAlmostEqual(vm.ocv(0.0), 2.834 - 0.1)
        self.assertAlmostEqual(vm.ocv(0.02), 3.162 - 0.1)
        # Autres points intouchés ; interpolation linéaire inchangée
        self.assertEqual(vp.ocv(0.04), t.ocv(0.04))
        self.assertAlmostEqual(vp.ocv(0.01),
                               (2.834 + 0.1 + 3.162 + 0.1) / 2)
        # La variante partage les mêmes Thevenin
        self.assertEqual(vp.rs(0.5), t.rs(0.5))
        # Le fichier gelé sur disque n'a pas changé
        self.assertEqual(SHA256_OCV, __import__("hashlib").sha256(
            (RAM_P4B / "data" / "ocv_soc_ncr18650b_hnei.csv")
            .read_bytes()).hexdigest())

    def test_interpolation_n_extrapole_jamais(self):
        ys = [1.0, 2.0]
        xs = [0.0, 1.0]
        self.assertEqual(_interpolation_lineaire(xs, ys, -5.0), 1.0)
        self.assertEqual(_interpolation_lineaire(xs, ys, 5.0), 2.0)


if __name__ == "__main__":
    unittest.main()
