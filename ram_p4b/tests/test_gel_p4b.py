"""Tests de non-régression du GEL — aucun fichier gelé modifié, constantes
du code = protocole gelé, refus d'exécution sans GO explicite."""

from __future__ import annotations

import hashlib
import subprocess
import sys
import unittest

from commun import RACINE, RAM_P4B

import analyse_p4b as an
import campagne_p4b as camp

# Empreintes au commit de freeze 45e509ee987469598acbf56967fb9e5cdc88a427
# (tag p4b-preregistration-freeze) — recalculées et ancrées ici.
FICHIERS_GELES = {
    "ram_p4b/P4B_PHASE0_PHYSICAL_BASIS_v0.6.md":
        "13de776091b81beea79bbcfe3140ef63662b2c785a8afe057a4d0ad409078225",
    "ram_p4b/P4B_PHASE0_FINAL_AUDIT_v0.6.md":
        "7cde289b5abcfd384ed12c6f78a840a6851840a1d0aa00f596b6bfb40c11c0c8",
    "ram_p4b/P4B_PREREGISTRATION_v0.1.md":
        "fdaf7371c4a35a6f638d458942945a5d081fc2acbd6da9fe1779dc4c558ba2aa",
    "ram_p4b/P4B_PREREGISTRATION_AUDIT_v0.1.md":
        "37720461a66b30276e931a094473b5b37f02a0e13dd703fa8fdb49004310f5d0",
    "ram_p4b/P4B_PREREGISTRATION_FINAL_AUDIT_v0.2.md":
        "2ffa187ebca0aae551177338bee34b1752d3dbcb32f440bb0beabe2eff797caf",
    "ram_p4b/P4B_PHASE0_PHYSICAL_BASIS.md":
        "4edf7b5c653931b073ed79b5c661a874862a809069ef603ad7f9015f99058f61",
    "ram_p4b/config_p4b_design.json":
        "20dcb71d9d8bde837f398157882811bc391e94f713e01ec7baedcb42ff815a63",
    "ram_p4b/verifier_design_p4b.py":
        "fa932dafb7f591ea888d760c6761d32960cbd38296f36e462c9616c8a128969e",
    "ram_p4b/data/ocv_soc_ncr18650b_hnei.csv":
        "7aa959fc99effefbc995237291217cec1657145051b3fa70cd7678fe0b7154c2",
    "ram_p4b/data/rint_soc_nmc_dtu.csv":
        "330efcd3165f5676f06b9128f723566193cc66fa6844fdddbc1f782015697b93",
}

MODULES_HISTORIQUES_GELES = {
    "ram_p0/moniteur.py":
        "aba3b8d9c79486f37fe15a70d1858ac55be86d9280d6579fd6cc8702ea04c8fb",
    "ram_p0/demo_eps.py":
        "b0abbbf1c71d09e3ecbd33a50b4b34353f94c9ace3e477f09c07b766ee8556db",
    "ram_p0/contraintes.py":
        "11b9007f9827a02c0fc259121467910d8ae4e748f4351fa6dd93a403d3b99a9a",
    "ram_p0/filtre.py":
        "6bb583bed56b22e0dfda4bd85e88dc232a6a7e4e510a73a7631ceda341edef2b",
    "ram_p0/trace.py":
        "bf93a1839e6eef13e46c592512f76acdbebce086e5d7cd3d20f1aa1cff8fba90",
    "ram_p2/campagne_p2.py":
        "6eb48963d9281c1bc1a9f343bbb71593a0807902ff0435a7c6b2d03fcc82b42c",
    "ram_p2/chemins.py":
        "88d7a305afb4f6afc8886b0b909b98b20a8ae37bbfaba54fdbd8c4273317fa01",
    "ram_p4/config_p4a.json":
        "e8e8fd32c3b8be7cf69bbb723154f645ade3b1d006013a77ccdd59b40d46feb5",
}


class TestGel(unittest.TestCase):
    def test_fichiers_gelles_inchanges(self):
        for rel, sha in FICHIERS_GELES.items():
            with self.subTest(fichier=rel):
                self.assertEqual(
                    hashlib.sha256((RACINE / rel).read_bytes()).hexdigest(),
                    sha)

    def test_modules_historiques_inchanges(self):
        for rel, sha in MODULES_HISTORIQUES_GELES.items():
            with self.subTest(fichier=rel):
                self.assertEqual(
                    hashlib.sha256((RACINE / rel).read_bytes()).hexdigest(),
                    sha)

    def test_constantes_du_protocole(self):
        self.assertEqual(an.N_PAR_NIVEAU, 5500)
        self.assertEqual(an.EPS_S, 0.01)
        self.assertEqual(an.EPS_F, 0.05)
        self.assertEqual(an.SEUIL_X_SUFFICIENT, 34)
        self.assertEqual(an.SEUIL_X_INSUFFICIENT, 320)
        self.assertEqual(an.GARDE_FOU_FLAG, 0.25)
        self.assertEqual(an.PAS_GRILLE, 0.125)
        self.assertEqual(an.SEUIL_LOW_RESOLUTION, 0.250)
        self.assertEqual(camp.N_BLOCS, 5500)
        self.assertEqual(camp.V_MIN_PACK, 5.0)
        self.assertEqual(camp.SHA256_DESIGN, FICHIERS_GELES[
            "ram_p4b/config_p4b_design.json"])
        self.assertEqual(camp.FREEZE_COMMIT,
                         "45e509ee987469598acbf56967fb9e5cdc88a427")
        self.assertEqual(camp.FREEZE_TAG, "p4b-preregistration-freeze")
        self.assertEqual(camp.FREEZE_PARENT,
                         "aba115ff174ee41629f1fda27b6ff826a007622c")

    def test_grilles_coherentes_entre_modules(self):
        self.assertEqual(camp.NIVEAUX_RHO, an.NIVEAUX_RHO)

    def test_scenario_charge_depuis_config_gelee(self):
        """Le scénario est lu depuis ram_p4/config_p4a.json gelé — valeurs
        exactes du §2 du préenregistrement."""
        cfg, sha = camp.charger_scenario()
        self.assertEqual(sha, MODULES_HISTORIQUES_GELES["ram_p4/config_p4a.json"])
        self.assertEqual(cfg["duree_s"], 13500.0)
        self.assertEqual(cfg["dt_s"], 5.0)
        self.assertEqual(cfg["dt_controle_s"], 2.5)
        self.assertEqual(cfg["seuil_soc"], 0.35)
        self.assertEqual(cfg["marge_securite_soc"], 0.02)
        self.assertEqual(cfg["delai_armement_s"], 120.0)
        self.assertEqual(cfg["u_payload"], 3.0)
        self.assertEqual(cfg["fenetre_payload"], [600.0, 1500.0])
        self.assertEqual(cfg["bruit_std"], [1e-7, 0.1])
        self.assertEqual(cfg["k_sigma"], 0.0)

    def test_execution_refusee_sans_go(self):
        """Le CLI refuse toute exécution sur le design gelé sans
        --execution-autorisee (garde procédurale anti-accident)."""
        r = subprocess.run(
            [sys.executable, str(RAM_P4B / "campagne_p4b.py"), "principal",
             "--debut", "0", "--fin", "1", "--sortie", "/tmp/jamais.jsonl"],
            capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)
        self.assertIn("REFUS", r.stdout)


if __name__ == "__main__":
    unittest.main()
