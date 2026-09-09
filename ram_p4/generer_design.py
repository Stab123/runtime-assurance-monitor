"""Generation deterministe des 500 points de design P4a (pre-enregistrement §3-§4).

Un seul flux : rng = random.Random(seed_graine("PLANT", 0)).
Ordre de tirage par candidat (fixe) : C_BATT, I_SUN, I_BASE, soc0 (uniformes
dans les plages D_physique). Le candidat est accepte si et seulement si les
regles d'admissibilite R1/R2/R3 sont satisfaites ; sinon il est rejete et le
flux continue. On s'arrete a 500 points acceptes. Les points acceptes sont
inscrits en clair dans config_p4a.json ; ce script permet de les regenerer et
de verifier l'identite bit a bit (non-regression du design).

Regles (avant generation, independantes de tout resultat) :
  R1 : I_SUN >= 1.5 * I_BASE                      (impliquee par R2)
  R2 : 3600*I_SUN >= 5400*I_BASE + 0.5*(3*900)
       <=> I_SUN >= 1.5*I_BASE + 0.375            (regle liante)
  R3 : soc0 >= 0.39                               (automatiquement satisfaite)

« Uniform » est une mesure de couverture experimentale, pas une hypothese
selon laquelle les satellites reels sont uniformement distribues.
"""

from __future__ import annotations

import random

from graines_p4 import seed_graine

K_POINTS = 500

PLAGES = {
    "C_BATT_AH": (4.4, 14.4),
    "I_SUN": (0.8, 2.5),
    "I_BASE": (0.06, 0.75),
    "soc0": (0.40, 0.70),
}


def admissible(p: dict) -> bool:
    """R1/R2/R3 — caracterisent le scenario physique, jamais le moniteur."""
    if p["I_SUN"] < 1.5 * p["I_BASE"]:              # R1
        return False
    if 3600.0 * p["I_SUN"] < 5400.0 * p["I_BASE"] + 0.5 * (3.0 * 900.0):  # R2
        return False
    if p["soc0"] < 0.39:                            # R3
        return False
    return True


def generer_points(k: int = K_POINTS) -> list[dict]:
    rng = random.Random(seed_graine("PLANT", 0))
    points = []
    while len(points) < k:
        p = {
            "C_BATT_AH": rng.uniform(*PLAGES["C_BATT_AH"]),
            "I_SUN": rng.uniform(*PLAGES["I_SUN"]),
            "I_BASE": rng.uniform(*PLAGES["I_BASE"]),
            "soc0": rng.uniform(*PLAGES["soc0"]),
        }
        if admissible(p):
            points.append({"bloc_id": len(points), **p})
    return points


if __name__ == "__main__":
    pts = generer_points()
    print(f"{len(pts)} points generes ; premier : {pts[0]}")
