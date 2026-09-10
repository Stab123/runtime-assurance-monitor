"""Graines P4b — source unique : le vérificateur de design GELÉ.

La règle de dérivation est gelée (préenregistrement §8) et implémentée dans
`verifier_design_p4b.py` (fichier gelé au commit de freeze
45e509ee987469598acbf56967fb9e5cdc88a427, tag p4b-preregistration-freeze).
Ce module ne fait que ré-exporter cette implémentation pour les campagnes :
aucune copie, aucune redéfinition — une seule source de vérité.

Labels autorisés (gelés) :
  - PLANT : design nuisance, i = 0 unique. JAMAIS régénéré en campagne —
    les points sont lus depuis config_p4b_design.json gelé.
  - NOISE : bruit de mesure, i = bloc_id ∈ [0 ; 5499], partagé entre les
    9 niveaux de ρ d'un même bloc (CRN) et réutilisé tel quel pour le
    contrôle de pas de temps (convention P4a-dtctrl : seul dt change).
"""

from __future__ import annotations

from verifier_design_p4b import LABELS, seed_graine  # noqa: F401  (gelé)

N_BLOCS = 5500


def graine_bruit_bloc(bloc_id: int) -> int:
    """Graine NOISE du bloc — CRN : identique aux 9 niveaux de ρ du bloc."""
    if not 0 <= bloc_id < N_BLOCS:
        raise ValueError(f"bloc_id hors [0 ; {N_BLOCS - 1}] : {bloc_id}")
    return seed_graine("NOISE", bloc_id)
