"""Filtre de sécurité prédictif — spécialisation scalaire de Wabersich & Zeilinger.

Référence : K. P. Wabersich & M. N. Zeilinger, « A predictive safety filter for
learning-based control of constrained nonlinear dynamical systems », Automatica
129:109597, 2021 (arXiv:1812.05506).

Spécialisation P0 (action scalaire), trois écarts assumés :
  1. Backup non optimisé : déroulé de la politique de repli B4, statiquement
     analysable — plus conservateur que W&Z, choix assumé pour la base de confiance.
  2. Action scalaire : l'ensemble admissible de v_0 est un intervalle, borne
     obtenue par dichotomie en NB_ITER_DICHOTOMIE itérations fixes (WCET borné).
  3. Évaluation pessimiste à x -/+ k_sigma * sigma (H4), sigma constant sur
     l'horizon — limitation documentée.

K_SIGMA = 3,0 correspond à p_S ~ 99,7 % sous hypothèse gaussienne : niveau
déclaré, non calibré. Sa calibration est un travail de P1.
"""

from __future__ import annotations

import math
from typing import Callable, Optional, Sequence

from contraintes import IDX_AUCUNE, Contrainte, Sens

K_SIGMA = 3.0
NB_ITER_DICHOTOMIE = 32

Modele = object  # protocole : .pas(x, u, dt) -> list[float]
PolitiqueRepli = Callable[[Sequence[float]], float]


def _valeur_pessimiste(c: Contrainte, x: Sequence[float], sigmas: Sequence[float],
                       k_sigma: float) -> float:
    """Borne défavorable de la grandeur surveillée au niveau p_S déclaré (H4)."""
    v = x[c.indice]
    if c.sens is Sens.MIN:
        return v - k_sigma * sigmas[c.indice]
    return v + k_sigma * sigmas[c.indice]


def trajectoire_sure(
    x0: Sequence[float],
    sigmas: Sequence[float],
    u0: float,
    modele: Modele,
    contraintes: Sequence[Contrainte],
    horizon: int,
    pas_armement: int,
    politique_repli: PolitiqueRepli,
    dt: float,
    k_sigma: float = K_SIGMA,
) -> tuple[bool, int, float]:
    """Déroule « action u0 puis repli » et vérifie l'enveloppe (RA-FUN-004).

    pas 0 : u0 ; pas 1..pas_armement : u0 persiste (armement en cours) ;
    au-delà : politique de repli B4 effective.
    """
    x = list(x0)
    marge_min = math.inf
    for k in range(horizon):
        if k <= pas_armement:
            u = u0
        else:
            u = politique_repli(x)
        x = list(modele.pas(x, u, dt))
        for i, c in enumerate(contraintes):
            v = _valeur_pessimiste(c, x, sigmas, k_sigma)
            m = max(-1.0, min(1.0, c.marge_normalisee(v)))
            if m < marge_min:
                marge_min = m
            if not c.evaluer(v):
                return False, i, marge_min
    return True, IDX_AUCUNE, marge_min if math.isfinite(marge_min) else 1.0


def intervalle_admissible(
    x0: Sequence[float],
    sigmas: Sequence[float],
    modele: Modele,
    contraintes: Sequence[Contrainte],
    horizon: int,
    pas_armement: int,
    politique_repli: PolitiqueRepli,
    dt: float,
    u_min: float,
    u_max: float,
    k_sigma: float = K_SIGMA,
) -> Optional[tuple[float, int, float]]:
    """Borne supérieure de l'intervalle admissible de v_0 (filtre W&Z scalaire).

    None si u_min lui-même est insoutenable -> le moniteur doit émettre REPLI.
    """
    ok_lo, idx_lo, marge_lo = trajectoire_sure(
        x0, sigmas, u_min, modele, contraintes, horizon, pas_armement,
        politique_repli, dt, k_sigma
    )
    if not ok_lo:
        return None
    ok_hi, _, marge_hi = trajectoire_sure(
        x0, sigmas, u_max, modele, contraintes, horizon, pas_armement,
        politique_repli, dt, k_sigma
    )
    if ok_hi:
        return (u_max, IDX_AUCUNE, marge_hi)

    lo, hi = u_min, u_max
    for _ in range(NB_ITER_DICHOTOMIE):
        mid = 0.5 * (lo + hi)
        ok, _, _ = trajectoire_sure(
            x0, sigmas, mid, modele, contraintes, horizon, pas_armement,
            politique_repli, dt, k_sigma
        )
        if ok:
            lo = mid
        else:
            hi = mid
    _, idx_det, _ = trajectoire_sure(
        x0, sigmas, hi, modele, contraintes, horizon, pas_armement,
        politique_repli, dt, k_sigma
    )
    _, _, marge = trajectoire_sure(
        x0, sigmas, lo, modele, contraintes, horizon, pas_armement,
        politique_repli, dt, k_sigma
    )
    return (lo, idx_det, marge)
