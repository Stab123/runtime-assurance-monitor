"""Tests du schéma JSONL (§14) — enregistrements SYNTHÉTIQUES artisanaux."""

from __future__ import annotations

import unittest

from commun import RAM_P4B  # noqa: F401

from schemas_p4b import CHAMPS_RUN, valider_run


def rec_valide():
    return {
        "run_id": "principal_rho1.000_bloc00000", "mode": "principal",
        "bloc_id": 0, "rho": 1.0, "C_BATT_AH": 10.0, "I_SUN": 1.2,
        "I_BASE": 0.5, "soc0": 0.6, "noise_seed": 123, "dt_s": 5.0,
        "cycles": 2700,
        "Y": 0, "V_min": 7.36, "t_min": 1200.0, "soc_at_vmin": 0.55,
        "Vp_at_vmin": 0.012, "I_batt_at_vmin": 3.5, "I_cell_at_vmin": 1.17,
        "soc_min": 0.55, "violation_silencieuse": False,
        "outside_domain": False, "outside_first_t": None,
        "outside_duration": 0.0, "outside_low": False, "outside_high": False,
        "outside_at_vmin": False,
        "invalid_technique": False, "invalid_reason": None,
        "fallback_fraction": 0.0, "payload_delivery_fraction": 1.0,
        "temoin_bruit": 9.4e-8, "temoin_bloc": "ab" * 32,
    }


class TestSchema(unittest.TestCase):
    def test_valide(self):
        self.assertEqual(valider_run(rec_valide()), [])

    def test_champ_manquant(self):
        r = rec_valide()
        del r["V_min"]
        self.assertTrue(any("V_min" in e for e in valider_run(r)))

    def test_champ_imprevu(self):
        r = rec_valide()
        r["champ_libre"] = 1
        self.assertTrue(any("non prévu" in e for e in valider_run(r)))

    def test_type_invalide(self):
        r = rec_valide()
        r["Y"] = "0"
        self.assertTrue(any("Y" in e for e in valider_run(r)))
        r = rec_valide()
        r["Y"] = True            # bool n'est pas int pour le schéma
        self.assertTrue(any("Y" in e for e in valider_run(r)))

    def test_substitution_y_interdite(self):
        """Run invalide avec Y non null = violation de la tolérance zéro."""
        r = rec_valide()
        r["invalid_technique"] = True
        r["invalid_reason"] = "NaN au pas 12"
        self.assertTrue(any("substitution" in e for e in valider_run(r)))
        # la forme correcte passe :
        for c in ("Y", "V_min", "t_min", "soc_at_vmin", "Vp_at_vmin",
                  "I_batt_at_vmin", "I_cell_at_vmin", "soc_min",
                  "violation_silencieuse", "outside_at_vmin",
                  "fallback_fraction", "payload_delivery_fraction"):
            r[c] = None
        self.assertEqual(valider_run(r), [])

    def test_invalide_sans_raison(self):
        r = rec_valide()
        r["invalid_technique"] = True
        self.assertTrue(any("invalid_reason" in e for e in valider_run(r)))

    def test_coherence_drapeau(self):
        r = rec_valide()
        r["outside_domain"] = True          # sans first_t → incohérent
        self.assertTrue(any("outside" in e for e in valider_run(r)))
        r["outside_first_t"] = 100.0
        r["outside_duration"] = 25.0
        r["outside_high"] = True
        self.assertEqual(valider_run(r), [])

    def test_tous_les_champs_du_mandat_presents(self):
        """Champs exigés par le mandat : bloc_id, rho, C_BATT_AH, I_SUN,
        I_BASE, soc0, noise_seed, Y, V_min, t_min, soc_at_vmin,
        Vp_at_vmin, I_batt_at_vmin, I_cell_at_vmin, outside_domain,
        outside_first_t, outside_duration, outside_at_vmin,
        invalid_technique, invalid_reason, fallback_fraction,
        payload_delivery_fraction, témoin/hash déterministe."""
        noms = {n for n, _, _ in CHAMPS_RUN}
        exiges = {"bloc_id", "rho", "C_BATT_AH", "I_SUN", "I_BASE", "soc0",
                  "noise_seed", "Y", "V_min", "t_min", "soc_at_vmin",
                  "Vp_at_vmin", "I_batt_at_vmin", "I_cell_at_vmin",
                  "outside_domain", "outside_first_t", "outside_duration",
                  "outside_at_vmin", "invalid_technique", "invalid_reason",
                  "fallback_fraction", "payload_delivery_fraction",
                  "temoin_bruit", "temoin_bloc"}
        self.assertTrue(exiges <= noms)


if __name__ == "__main__":
    unittest.main()
