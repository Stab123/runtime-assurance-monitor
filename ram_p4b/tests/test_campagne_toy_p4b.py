"""Tests de la boucle de campagne P4b sur CAS JOUETS — jamais de bloc du
design réel, jamais la durée/scénario scientifique gelés (13 500 s).
Durées jouets : 100 s (20 pas) et 5 100 s (1 020 pas, pour le témoin CRN
au pas 1 000)."""

from __future__ import annotations

import math
import unittest

from commun import GRAINE_TOY, PARAMS_TOY, cfg_toy

import campagne_p4b as camp
from modele_p4b import TablesPhysiques
from schemas_p4b import valider_run


class TestCampagneToy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.t = TablesPhysiques.charger()
        cls.cfg100 = cfg_toy(100.0)
        cls.cfg5100 = cfg_toy(5100.0)

    def _identite(self, rec, rho=1.0, bloc_id=0, mode="principal"):
        rec.update({
            "run_id": f"{mode}_rho{rho:.3f}_bloc{bloc_id:05d}", "mode": mode,
            "bloc_id": bloc_id, "rho": rho,
            "C_BATT_AH": PARAMS_TOY["C_BATT_AH"], "I_SUN": PARAMS_TOY["I_SUN"],
            "I_BASE": PARAMS_TOY["I_BASE"], "soc0": PARAMS_TOY["soc0"],
            "noise_seed": GRAINE_TOY, "dt_s": 5.0,
            "temoin_bloc": camp.temoin_bloc(PARAMS_TOY, GRAINE_TOY)})
        return rec

    # --- déterminisme / CRN ---------------------------------------------------

    def test_determinisme_bit_a_bit(self):
        r1 = camp.simuler_p4b(1.0, PARAMS_TOY, GRAINE_TOY, self.cfg5100, self.t)
        r2 = camp.simuler_p4b(1.0, PARAMS_TOY, GRAINE_TOY, self.cfg5100, self.t)
        self.assertEqual(r1, r2)                # enregistrements identiques

    def test_crn_temoin_identique_entre_niveaux(self):
        r1 = camp.simuler_p4b(1.0, PARAMS_TOY, GRAINE_TOY, self.cfg5100, self.t)
        r2 = camp.simuler_p4b(2.0, PARAMS_TOY, GRAINE_TOY, self.cfg5100, self.t)
        self.assertIsNotNone(r1["temoin_bruit"])
        self.assertEqual(r1["temoin_bruit"], r2["temoin_bruit"])   # bruit pur

    def test_soc_invariant_en_rho(self):
        """Conséquence structurelle §7 : SoC identique aux 9 niveaux (CRN)."""
        r1 = camp.simuler_p4b(1.0, PARAMS_TOY, GRAINE_TOY, self.cfg5100, self.t)
        r2 = camp.simuler_p4b(1.875, PARAMS_TOY, GRAINE_TOY, self.cfg5100, self.t)
        self.assertEqual(r1["soc_min"], r2["soc_min"])
        self.assertEqual(r1["fallback_fraction"], r2["fallback_fraction"])
        self.assertEqual(r1["outside_domain"], r2["outside_domain"])

    def test_graine_bruit_change_le_run(self):
        r1 = camp.simuler_p4b(1.0, PARAMS_TOY, 1, self.cfg5100, self.t)
        r2 = camp.simuler_p4b(1.0, PARAMS_TOY, 2, self.cfg5100, self.t)
        self.assertNotEqual(r1["temoin_bruit"], r2["temoin_bruit"])

    # --- endpoint (§4) ----------------------------------------------------------

    def test_endpoint_inegalite_stricte(self):
        """Y = 1{V_min < 5.0} : l'égalité exacte n'est PAS une violation."""
        # Contrôle unitaire de la comparaison, sur valeurs artisanales :
        self.assertEqual(1 if 4.9999999999 < 5.0 else 0, 1)
        self.assertEqual(1 if 5.0 < 5.0 else 0, 0)
        # Et le code utilise bien la comparaison stricte (source auditée) :
        import inspect
        src = inspect.getsource(camp.simuler_p4b)
        self.assertIn("v_min < V_MIN_PACK", src)
        self.assertNotIn("v_min <= V_MIN_PACK", src)

    def test_endpoint_toutes_phases(self):
        """V_min est pris sur TOUTES les phases, y compris charge : le
        premier argmin est conservé et t_min ∈ [0 ; T)."""
        r = camp.simuler_p4b(1.0, PARAMS_TOY, GRAINE_TOY, self.cfg5100, self.t)
        self.assertTrue(0.0 <= r["t_min"] < 5100.0)
        self.assertFalse(r["invalid_technique"])
        self.assertIn(r["Y"], (0, 1))

    def test_coherence_descripteurs(self):
        r = camp.simuler_p4b(1.0, PARAMS_TOY, GRAINE_TOY, self.cfg5100, self.t)
        self.assertEqual(r["violation_silencieuse"],
                         bool(r["Y"] == 1 and r["soc_min"] >= 0.35))
        self.assertTrue(math.isfinite(r["V_min"]))
        self.assertLessEqual(r["soc_min"], PARAMS_TOY["soc0"] + 1e-9 + 0.1)

    # --- moniteur B : u_exec réellement appliqué --------------------------------

    def test_repli_du_moniteur_applique(self):
        """Cas jouet avec soc0 proche du seuil : le moniteur B doit
        intervenir (repli → u_exec = 0) et le run rester valide."""
        toy = dict(PARAMS_TOY, soc0=0.355)
        r = camp.simuler_p4b(1.0, toy, GRAINE_TOY, self.cfg100, self.t)
        self.assertFalse(r["invalid_technique"])
        self.assertGreater(r["fallback_fraction"], 0.0)   # repli survenu
        self.assertLessEqual(r["payload_delivery_fraction"], 1.0)

    def test_sans_intervention_livraison_complete(self):
        r = camp.simuler_p4b(1.0, PARAMS_TOY, GRAINE_TOY, self.cfg5100, self.t)
        self.assertEqual(r["fallback_fraction"], 0.0)
        self.assertEqual(r["payload_delivery_fraction"], 1.0)

    # --- INVALID_TECHNIQUE (tolérance zéro, §4) ---------------------------------

    def test_run_interrompu_invalide(self):
        """Exception en cours de run → INVALID_TECHNIQUE, Y = null."""
        toy = dict(PARAMS_TOY, C_BATT_AH=0.0)   # division par zéro assurée
        r = camp.simuler_p4b(1.0, toy, GRAINE_TOY, self.cfg100, self.t)
        self.assertTrue(r["invalid_technique"])
        self.assertIsNone(r["Y"])
        self.assertIsNotNone(r["invalid_reason"])

    def test_nan_detecte_invalide(self):
        """NaN dans l'état → INVALID_TECHNIQUE (via plante dégradée jouet)."""
        import modele_p4b
        original = modele_p4b.PlanteP4b.pas

        def pas_nan(self, x, u, dt):            # jouet : injecte un NaN
            x2 = original(self, x, u, dt)
            return [float("nan"), x2[1]]

        modele_p4b.PlanteP4b.pas = pas_nan
        try:
            r = camp.simuler_p4b(1.0, PARAMS_TOY, GRAINE_TOY,
                                 self.cfg100, self.t)
        finally:
            modele_p4b.PlanteP4b.pas = original
        self.assertTrue(r["invalid_technique"])
        self.assertIsNone(r["Y"])
        self.assertIn("non finie", r["invalid_reason"])

    # --- drapeau hors domaine (§9) ----------------------------------------------

    def test_drapeau_hors_domaine(self):
        """Charge forte jouet : SoC > 1 → drapeau, premier instant, durée ;
        le run RESTE valide (règle d'inclusion)."""
        toy = dict(PARAMS_TOY, soc0=0.98, I_SUN=2.5, I_BASE=0.06,
                   C_BATT_AH=4.4)
        r = camp.simuler_p4b(1.0, toy, GRAINE_TOY, cfg_toy(3000.0), self.t)
        self.assertFalse(r["invalid_technique"])
        self.assertTrue(r["outside_domain"])
        self.assertTrue(r["outside_high"])
        self.assertFalse(r["outside_low"])
        self.assertIsNotNone(r["outside_first_t"])
        self.assertGreater(r["outside_duration"], 0.0)
        self.assertIsNotNone(r["outside_at_vmin"])
        self.assertIsNotNone(r["Y"])            # inclus dans l'analyse

    def test_sans_drapeau_champs_coherents(self):
        r = camp.simuler_p4b(1.0, PARAMS_TOY, GRAINE_TOY, self.cfg100, self.t)
        self.assertFalse(r["outside_domain"])
        self.assertIsNone(r["outside_first_t"])
        self.assertEqual(r["outside_duration"], 0.0)

    # --- schéma JSONL -------------------------------------------------------------

    def test_enregistrement_complet_conforme_schema(self):
        r = camp.simuler_p4b(1.0, PARAMS_TOY, GRAINE_TOY, self.cfg5100, self.t)
        self._identite(r)
        self.assertEqual(valider_run(r), [])

    def test_enregistrement_invalide_conforme_schema(self):
        toy = dict(PARAMS_TOY, C_BATT_AH=0.0)
        r = camp.simuler_p4b(1.0, toy, GRAINE_TOY, self.cfg100, self.t)
        self._identite(r)
        self.assertEqual(valider_run(r), [])

    # --- grille et constantes ------------------------------------------------------

    def test_grille_rho_exacte(self):
        attendue = (1.0, 1.125, 1.25, 1.375, 1.5, 1.625, 1.75, 1.875, 2.0)
        self.assertEqual(camp.NIVEAUX_RHO, attendue)
        for i, rho in enumerate(camp.NIVEAUX_RHO):
            self.assertEqual(rho, 1.0 + i * 0.125)   # exactitude binaire

    def test_aucune_regeneration_design(self):
        """La campagne LIT le design gelé ; la graine PLANT n'est jamais
        utilisée par le module de campagne (aucun import de random pour le
        design — le seul random.Random est le bruit NOISE du run)."""
        import inspect
        src = inspect.getsource(camp)
        self.assertNotIn('seed_graine("PLANT"', src)
        self.assertNotIn("seed_graine('PLANT'", src)
        self.assertIn("charger_design", src)

    def test_campagne_arretee_sur_run_invalide(self):
        """§12 V0 : « campagne arrêtée, cause documentée » — la boucle
        s'interrompt au premier run INVALID_TECHNIQUE et la méta porte le
        statut INVALID. Blocs et paramètres SYNTHÉTIQUES."""
        import json
        import tempfile
        from pathlib import Path
        points_toy = [dict(bloc_id=0, **{k: PARAMS_TOY[k] for k in
                                         ("C_BATT_AH", "I_SUN", "I_BASE",
                                          "soc0")}),
                      dict(bloc_id=1, C_BATT_AH=0.0, I_SUN=1.2, I_BASE=0.5,
                           soc0=0.6)]           # bloc jouet invalide
        with tempfile.TemporaryDirectory() as d:
            sortie = Path(d) / "toy.jsonl"
            with self.assertRaises(camp.CampagneInvalideTechnique):
                camp.executer("principal", 0, 2, sortie,
                              points=points_toy, cfg=self.cfg100,
                              tables=self.t)
            lignes = sortie.read_text().strip().split("\n")
            # 9 niveaux du bloc 0 + arrêt au premier niveau du bloc 1
            self.assertEqual(len(lignes), 10)
            meta = json.loads(sortie.with_suffix(".meta.json").read_text())
            self.assertEqual(meta["statut"], "INVALID / TECHNICAL FAILURE")
            rec_invalide = json.loads(lignes[-1])
            self.assertTrue(rec_invalide["invalid_technique"])
            self.assertIsNone(rec_invalide["Y"])


if __name__ == "__main__":
    unittest.main()
