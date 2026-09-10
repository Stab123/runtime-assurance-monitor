"""Utilitaire commun des tests P4b : chemins d'import + cas jouets.

TOUS les cas de cette suite sont SYNTHÉTIQUES : paramètres ronds nominaux
P0 (10 Ah, 1.2 A, 0.5 A, soc0 = 0.6) ou variantes artisanales, durées
courtes (100 s / 5 100 s vs 13 500 s gelé), graines arbitraires hors
dérivation P4b. AUCUN bloc du design gelé n'est chargé ni exécuté, AUCUN
résultat scientifique P4b n'est produit par ces tests.
"""

from __future__ import annotations

import sys
from pathlib import Path

RAM_P4B = Path(__file__).resolve().parents[1]
RACINE = RAM_P4B.parent
for p in (RAM_P4B, RACINE / "ram_p0", RACINE / "ram_p2", RACINE / "ram_p4"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

# Cas jouet de référence — valeurs nominales P0, explicitement hors design.
PARAMS_TOY = {"C_BATT_AH": 10.0, "I_SUN": 1.2, "I_BASE": 0.5, "soc0": 0.6,
              "H": 1.5e-3, "C_TH": 5e-4, "temp0": 20.0}

GRAINE_TOY = 123456789   # arbitraire, HORS dérivation seed_graine P4b


def cfg_toy(duree_s: float = 100.0, dt_s: float = 5.0) -> dict:
    """Config jouet minimale (mêmes champs que charger_scenario)."""
    return {
        "duree_s": duree_s, "dt_s": dt_s, "dt_controle_s": 2.5,
        "delai_armement_s": 120.0, "seuil_soc": 0.35, "seuil_temp": 45.0,
        "marge_securite_soc": 0.02, "marge_securite_temp": 1.0,
        "u_payload": 3.0, "fenetre_payload": [600.0, 1500.0],
        "capacite_tampon": 4096, "seuil_incertitude_soc": 1e30,
        "seuil_incertitude_temp": 2.0, "k_sigma": 0.0,
        "bruit_std": [1e-7, 0.1],
    }
