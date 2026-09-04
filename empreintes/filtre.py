"""Filtre de sécurité prédictif — spécialisation scalaire de Wabersich & Zeilinger.

Référence : K. P. Wabersich & M. N. Zeilinger, « A predictive safety filter for
learning-based control of constrained nonlinear dynamical systems », Automatica
129:109597, 2021 (arXiv:1812.05506) ; version linéaire : CDC 2018.

Formulation originale (cas linéaire) :

    min_v  ||v_0 - u_candidat||^2
    s.c.   z_{k+1} = A z_k + B v_k,  z_0 = x(t),
           z_k dans X,  v_k dans U,  z_N dans X_f

Le filtre ne modifie l'action candidate que du minimum nécessaire ; si le
problème est infaisable, la trajectoire de backup (ici : la politique de repli)
prend la main.

Spécialisation P0 (action scalaire), trois écarts assumés et documentés :

  1. La trajectoire de backup n'est pas optimisée : c'est le déroulé de la
     politique de repli B4, déterministe et vérifiable (RAM-SPEC-0001 §3).
     C'est plus conservateur que W&Z, mais statiquement analysable — le bon
     compromis pour une base de confiance.
  2. L'ensemble admissible de v_0 est alors un intervalle [u_min, u_hat], sous
     hypothèse de monotonie (plus l'action est forte, plus le risque croît —
     vrai pour le modèle EPS : courant payload -> décharge et échauffement).
     La borne est obtenue par dichotomie en NB_ITER_DICHOTOMIE itérations
     fixes : nombre d'itérations borné statiquement, dans l'esprit de
     RA-RES-003 (WCET borné).
  3. L'évaluation est pessimiste : chaque contrainte est vérifiée sur la borne
     défavorable de l'état estimé (x -/+ k_sigma * sigma), traduction de H4.
     P0 suppose sigma constant sur l'horizon — limitation documentée.

Niveau de confiance déclaré : K_SIGMA = 3,0 correspond à p_S ~ 99,7 % sous
hypothèse gaussienne. C'est une borne de confiance *déclarée*, au sens des
variantes stochastiques du filtre de W&Z — la filiation exige que ce niveau
soit explicite, pas qu'il soit justifié. Sa calibration sur l'estimateur
réel (gaussianité, queues de distribution, bornes non probabilistes) est un
travail de P1 ; en attendant, toute marge affichée par le moniteur se lit
« à p_S déclaré ».

P1 : action vectorielle -> remplacer la dichotomie par le QP complet de
Wabersich & Zeilinger (le reste de l'architecture ne change pas).
"""

from __future__ import annotations

import math
from typing import Callable, Optional, Sequence

from contraintes import IDX_AUCUNE, Contrainte, Sens

K_SIGMA = 3.0               # p_S ~ 99,7 % (gaussien) — niveau déclaré, cf. ci-dessus
NB_ITER_DICHOTOMIE = 32     # nombre fixe d'itérations (borne temporelle)

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
    """Déroule la trajectoire « action u0 puis repli » et vérifie l'enveloppe.

    Séquence évaluée (RA-FUN-004) :
      - pas 0                    : action candidate u0 ;
      - pas 1 .. pas_armement    : u0 persiste — le repli est en cours
                                   d'armement, l'action courante continue de
                                   s'appliquer (hypothèse conservatrice) ;
      - pas > pas_armement       : politique de repli B4 effective.

    Renvoie (sur, indice_premiere_contrainte_violee, marge_min_normalisee).
    La marge est calculée sur les valeurs pessimistes et tronquée à [-1, 1].
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

    Renvoie None si même u_min est insoutenable -> le problème de W&Z est
    infaisable, le moniteur doit émettre REPLI.
    Renvoie (u_hat, indice_contrainte_determinante, marge) sinon : u_hat est
    l'action la plus proche possible de toute candidate trop forte, c.-à-d. la
    modification minimale au sens du coût ||v_0 - u_candidat||.
    """
    ok_lo, idx_lo, marge_lo = trajectoire_sure(
        x0, sigmas, u_min, modele, contraintes, horizon, pas_armement, politique_repli, dt, k_sigma
    )
    if not ok_lo:
        return None  # infaisable même au plancher -> repli (backup de W&Z)
    ok_hi, _, marge_hi = trajectoire_sure(
        x0, sigmas, u_max, modele, contraintes, horizon, pas_armement, politique_repli, dt, k_sigma
    )
    if ok_hi:
        return (u_max, IDX_AUCUNE, marge_hi)

    lo, hi = u_min, u_max
    for _ in range(NB_ITER_DICHOTOMIE):
        mid = 0.5 * (lo + hi)
        ok, _, _ = trajectoire_sure(
            x0, sigmas, mid, modele, contraintes, horizon, pas_armement, politique_repli, dt, k_sigma
        )
        if ok:
            lo = mid
        else:
            hi = mid
    # La contrainte déterminante est la première violée juste au-dessus de la
    # borne : c'est elle qui a fait basculer le verdict (trace, RAM-SPEC §6).
    _, idx_det, _ = trajectoire_sure(
        x0, sigmas, hi, modele, contraintes, horizon, pas_armement, politique_repli, dt, k_sigma
    )
    _, _, marge = trajectoire_sure(
        x0, sigmas, lo, modele, contraintes, horizon, pas_armement, politique_repli, dt, k_sigma
    )
    return (lo, idx_det, marge)
