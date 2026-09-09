"""Derivation deterministe des graines P4a (pre-enregistrement §13).

Regle unique, publique et figee :

    seed(label, i) = int(SHA256(s)[0:8], big-endian) mod 2**31

avec s = "P4a-confirmatory-v1|<commit v1.4.1>|10.5281/zenodo.22681860|<label>|<i>"

Labels : PLANT, NOISE, BOOTSTRAP, RESEED, DTCTRL, PILOT.
Aucune graine historique P2/P3 n'est reutilisee. Les graines de la famille
PILOT sont definitivement exclues du confirmatoire.
"""

from __future__ import annotations

import hashlib

COMMIT_V141 = "2d4ce6a2cecc52778a2f5ebf649e2a128c6a8138"
DOI_V141 = "10.5281/zenodo.22681860"
VERSION_CAMPAGNE = "P4a-confirmatory-v1"

LABELS = ("PLANT", "NOISE", "BOOTSTRAP", "RESEED", "DTCTRL", "PILOT")


def seed_graine(label: str, i: int) -> int:
    """Graine deterministe. `label` dans LABELS, `i` compteur >= 0."""
    if label not in LABELS:
        raise ValueError(f"label inconnu : {label!r} (attendu dans {LABELS})")
    if i < 0:
        raise ValueError("compteur negatif")
    s = f"{VERSION_CAMPAGNE}|{COMMIT_V141}|{DOI_V141}|{label}|{i}"
    h = hashlib.sha256(s.encode("utf-8")).digest()
    return int.from_bytes(h[:8], "big") % (2 ** 31)
