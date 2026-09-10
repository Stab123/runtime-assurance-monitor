"""Verification deterministe du design P4b (pre-enregistrement §7-§8, audit final v0.2).

Regle unique, publique et figee :

    seed(label, i) = int(SHA256(s)[0:8], big-endian) mod 2**31
    s = "P4b-structural-v1|<commit v1.4.1>|10.5281/zenodo.22681860|<label>|<i>"

Design nuisance (label PLANT) : UN SEUL flux
    rng = random.Random(seed_graine("PLANT", 0))
tirages successifs C_BATT_AH, I_SUN, I_BASE, soc0 ; admissibilite R1/R2/R3 ;
chaque rejet consomme quatre tirages et le flux continue ; bloc_id attribue
aux seuls points acceptes, dans l'ordre d'acceptation ; arret exactement au
5500e point accepte ; 934 candidats rejetes avant cet arret. AUCUNE graine
PLANT dependant de bloc_id. Le bruit des runs utilise un label distinct :
seed_graine("NOISE", bloc_id).

Ce script regenere le design et verifie l'identite BIT A BIT avec
config_p4b_design.json (non-regression du design). Il n'execute ni ne
reference la plante P4b. Usage :

    python3 verifier_design_p4b.py
"""

from __future__ import annotations

import hashlib
import json
import random
import struct
import sys
from pathlib import Path

COMMIT_V141 = "2d4ce6a2cecc52778a2f5ebf649e2a128c6a8138"
DOI_V141 = "10.5281/zenodo.22681860"
VERSION_CAMPAGNE = "P4b-structural-v1"

LABELS = ("PLANT", "NOISE")

K_POINTS = 5500
REJETS_ATTENDUS = 934
SHA256_ATTENDU = (
    "20dcb71d9d8bde837f398157882811bc391e94f713e01ec7baedcb42ff815a63"
)

PLAGES = {
    "C_BATT_AH": (4.4, 14.4),
    "I_SUN": (0.8, 2.5),
    "I_BASE": (0.06, 0.75),
    "soc0": (0.40, 0.70),
}


def seed_graine(label: str, i: int) -> int:
    """Graine deterministe. `label` dans LABELS, `i` compteur >= 0."""
    if label not in LABELS:
        raise ValueError(f"label inconnu : {label!r} (attendu dans {LABELS})")
    if i < 0:
        raise ValueError("compteur negatif")
    s = f"{VERSION_CAMPAGNE}|{COMMIT_V141}|{DOI_V141}|{label}|{i}"
    h = hashlib.sha256(s.encode("utf-8")).digest()
    return int.from_bytes(h[:8], "big") % (2**31)


def admissible(p: dict) -> bool:
    """R1/R2/R3 — caracterisent le scenario physique, jamais le moniteur."""
    if p["I_SUN"] < 1.5 * p["I_BASE"]:              # R1
        return False
    if 3600.0 * p["I_SUN"] < 5400.0 * p["I_BASE"] + 0.5 * (3.0 * 900.0):  # R2
        return False
    if p["soc0"] < 0.39:                            # R3
        return False
    return True


def generer_points(k: int = K_POINTS) -> tuple[list[dict], int]:
    rng = random.Random(seed_graine("PLANT", 0))
    points, rejets = [], 0
    while len(points) < k:
        p = {
            "C_BATT_AH": rng.uniform(*PLAGES["C_BATT_AH"]),
            "I_SUN": rng.uniform(*PLAGES["I_SUN"]),
            "I_BASE": rng.uniform(*PLAGES["I_BASE"]),
            "soc0": rng.uniform(*PLAGES["soc0"]),
        }
        if admissible(p):
            points.append({"bloc_id": len(points), **p})
        else:
            rejets += 1
    return points, rejets


def main() -> int:
    here = Path(__file__).resolve().parent
    fjson = here / "config_p4b_design.json"
    data = json.loads(fjson.read_text(encoding="utf-8"))
    ref = data["design_points"]

    gen, rejets = generer_points()
    cles = ("C_BATT_AH", "I_SUN", "I_BASE", "soc0")
    diff = 0
    for g, r in zip(gen, ref):
        if g["bloc_id"] != r["bloc_id"] or any(
            struct.pack("<d", g[c]) != struct.pack("<d", r[c]) for c in cles
        ):
            diff += 1

    sha = hashlib.sha256(fjson.read_bytes()).hexdigest()
    print(f"points regeneres      : {len(gen)}")
    print(f"points fichier        : {len(ref)}")
    print(f"differences bit-a-bit : {diff}")
    print(f"rejets regeneres      : {rejets} (attendu {REJETS_ATTENDUS})")
    print(f"SHA256 fichier        : {sha}")
    print(f"SHA256 attendu        : {SHA256_ATTENDU}")

    ok = (
        diff == 0
        and len(gen) == len(ref) == K_POINTS
        and rejets == REJETS_ATTENDUS
        and sha == SHA256_ATTENDU
    )
    print("VERDICT :", "DESIGN REPRODUCTIBLE BIT-A-BIT" if ok else "ECART — STOP")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
