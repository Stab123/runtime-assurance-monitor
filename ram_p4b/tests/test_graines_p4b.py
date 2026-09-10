"""Tests des graines P4b (préenregistrement §8) — synthétique."""

from __future__ import annotations

import unittest

from commun import RAM_P4B, RACINE  # noqa: F401  (chemins d'import)

import graines_p4b
from verifier_design_p4b import seed_graine as seed_gele  # module gelé


class TestGraines(unittest.TestCase):
    def test_source_unique_module_gele(self):
        """graines_p4b ré-exporte la fonction du vérificateur GELÉ — aucune
        redéfinition."""
        self.assertIs(graines_p4b.seed_graine, seed_gele)

    def test_labels_autorises(self):
        self.assertEqual(graines_p4b.LABELS, ("PLANT", "NOISE"))

    def test_refus_label_inconnu(self):
        with self.assertRaises(ValueError):
            seed_gele("PILOT", 0)     # labels P4a interdits en P4b
        with self.assertRaises(ValueError):
            seed_gele("RESEED", 0)

    def test_graine_noise_par_bloc(self):
        g0 = graines_p4b.graine_bruit_bloc(0)
        g0b = graines_p4b.graine_bruit_bloc(0)
        g1 = graines_p4b.graine_bruit_bloc(1)
        self.assertEqual(g0, g0b)                    # déterministe
        self.assertNotEqual(g0, g1)                  # distincte par bloc
        self.assertTrue(0 <= g0 < 2**31)             # mod 2^31 (§8)

    def test_bornes_bloc_id(self):
        with self.assertRaises(ValueError):
            graines_p4b.graine_bruit_bloc(-1)
        with self.assertRaises(ValueError):
            graines_p4b.graine_bruit_bloc(5500)

    def test_valeur_de_reference_publique(self):
        """Valeur de référence calculée à la main sur la règle gelée
        (SHA256, big-endian, mod 2^31) — ancre publique §8."""
        import hashlib
        s = ("P4b-structural-v1|2d4ce6a2cecc52778a2f5ebf649e2a128c6a8138|"
             "10.5281/zenodo.22681860|NOISE|0")
        attendu = int.from_bytes(
            hashlib.sha256(s.encode("utf-8")).digest()[:8], "big") % 2**31
        self.assertEqual(graines_p4b.graine_bruit_bloc(0), attendu)


if __name__ == "__main__":
    unittest.main()
