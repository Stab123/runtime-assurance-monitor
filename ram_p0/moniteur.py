"""Moniteur d'assurance runtime — P0.

Implémente la sémantique de RAM-SPEC-0001 v0.1 :
  - exactement un verdict par cycle (RA-FUN-001) ; INDETERMINE distinct dans
    la trace mais exécuté comme REPLI (RA-FUN-002) ;
  - REPLI si l'incertitude dépasse le seuil d'une contrainte (RA-FUN-003 / H4) ;
  - horizon >= délai d'armement du repli (RA-FUN-004) ;
  - repli atteignable validé à la compilation (RA-FUN-005) ;
  - repli verrouillé, retour sur critère explicite horodaté (RA-FUN-006) ;
  - absence d'action candidate -> REPLI (RA-IND-003) ;
  - version du jeu dans chaque enregistrement (RA-IND-004), mise à jour sur
    autorisation explicite (IF-6) ;
  - la trace ne bloque jamais le verdict (RA-RES-004), pertes comptées (RA-RES-005) ;
  - signal de vie à chaque cycle (RA-SUR-002) ;
  - notification FDIR sur verdict non nominal (IF-4).

Le filtre de sécurité (MODIFIE) est la spécialisation scalaire du predictive
safety filter de Wabersich & Zeilinger : voir filtre.py.
"""

from __future__ import annotations

import hashlib
import math
import struct
from dataclasses import dataclass, replace
from enum import IntEnum
from typing import Callable, Optional, Sequence

from contraintes import IDX_AUCUNE, Contrainte, JeuContraintes, Sens
from filtre import intervalle_admissible, trajectoire_sure
from trace import Enregistrement, TamponAnneau


class Verdict(IntEnum):
    AUTORISE = 0
    MODIFIE = 1
    REPLI = 2
    INDETERMINE = 3


class Cause(IntEnum):
    AUCUNE = 0
    VIOLATION_ENVELOPPE = 1
    INCERTITUDE = 2
    TIMEOUT_ACTION = 3
    ENTREES_INVALIDES = 4
    REPLI_VERROUILLE = 5


class Mode(IntEnum):
    NOMINAL = 0
    REPLI = 1


class JeuInvalide(Exception):
    """Levée à la compilation si le repli n'est pas atteignable (RA-FUN-005)."""


class MiseAJourRefusee(Exception):
    """Levée sur mise à jour du jeu sans autorisation (IF-6)."""


@dataclass
class ResultatCycle:
    t_s: float
    seq: int
    verdict: Verdict
    cause: Cause
    mode: Mode
    action_transmise: float
    marge: float
    indice_contrainte: int
    confiance: float
    vie: int


def _empreinte(action: Optional[float]) -> bytes:
    if action is None:
        return b"\x00\x00\x00"
    return hashlib.blake2s(struct.pack("<d", action), digest_size=3).digest()


def compiler_jeu(
    version: int,
    contraintes: Sequence[Contrainte],
    modele,
    politique_repli: Callable[[Sequence[float]], float],
    dt: float,
    etat_nominal: Sequence[float],
    bornes_action: tuple[float, float],
    marge_horizon_pas: int = 12,
) -> JeuContraintes:
    """Compile et valide un jeu de contraintes.

    Horizon = délai d'armement max + marge (RA-FUN-004). Pour chaque contrainte,
    on vérifie que depuis l'état frontière la trajectoire ne viole aucun seuil
    de sécurité BRUT — la marge de garde est le recul qui laisse au repli le
    temps d'agir, pas la limite de sécurité. Pendant l'armement l'action
    transmise persiste : on teste les deux bornes admissibles, le repli n'est
    réputé atteignable que si le pire cas tient (RA-FUN-005).
    """
    if not contraintes:
        raise JeuInvalide("jeu de contraintes vide")
    pas_armement = max(math.ceil(c.delai_armement_s / dt) for c in contraintes)
    horizon = pas_armement + marge_horizon_pas
    sigmas_nulles = [0.0] * len(etat_nominal)
    contraintes_brutes = [replace(c, marge_securite=0.0) for c in contraintes]
    u_min, u_max = bornes_action
    for c in contraintes:
        x = list(etat_nominal)
        frontiere = (
            c.seuil + c.marge_securite if c.sens is Sens.MIN
            else c.seuil - c.marge_securite
        )
        x[c.indice] = frontiere
        pas_armement_c = math.ceil(c.delai_armement_s / dt)
        for u_persist in (u_min, u_max):
            ok, _, _ = trajectoire_sure(
                x, sigmas_nulles, u_persist, modele, contraintes_brutes,
                horizon, pas_armement_c, politique_repli, dt,
            )
            if not ok:
                raise JeuInvalide(
                    f"RA-FUN-005 : repli non atteignable depuis la frontière de "
                    f"« {c.nom} » (action persistée {u_persist} A pendant "
                    f"l'armement de {c.delai_armement_s:.0f} s) — jeu refusé "
                    f"à la compilation"
                )
    return JeuContraintes(
        version=version,
        contraintes=tuple(contraintes),
        horizon_pas=horizon,
        pas_armement_max=pas_armement,
    )


class Moniteur:
    """Blocs B1 à B5 de RAM-SPEC-0001, synchrones avec la boucle de décision."""

    def __init__(
        self,
        jeu: JeuContraintes,
        modele,
        politique_repli: Callable[[Sequence[float]], float],
        dt: float,
        tampon: TamponAnneau,
        u_min: float,
        u_max: float,
        cycles_retour: int = 12,
        dwell_retour_s: float = 120.0,
        n_pre_gel: int = 12,
        n_post_gel: int = 12,
        k_sigma: float = 3.0,
    ):
        self._jeu = jeu
        self._modele = modele
        self._politique_repli = politique_repli
        self._dt = dt
        self._tampon = tampon
        self._u_min, self._u_max = u_min, u_max
        self._cycles_retour = cycles_retour
        self._dwell_retour_s = dwell_retour_s
        self._n_pre_gel, self._n_post_gel = n_pre_gel, n_post_gel
        self._k_sigma = k_sigma

        self._mode = Mode.NOMINAL
        self._seq = 0
        self._vie = 0
        self._cycles_ok = 0
        self._t_entree_repli: Optional[float] = None
        self.notifications: list[tuple[float, str]] = []

    @property
    def mode(self) -> Mode:
        return self._mode

    @property
    def vie(self) -> int:
        return self._vie

    @property
    def version_jeu(self) -> int:
        return self._jeu.version

    def _confiance(self, sigmas: Sequence[float]) -> float:
        """Agrégat : 1 = loin des seuils d'incertitude, 0 = atteint."""
        pire = 0.0
        for c in self._jeu.contraintes:
            if c.seuil_incertitude > 0:
                pire = max(pire, sigmas[c.indice] / c.seuil_incertitude)
        return max(0.0, 1.0 - pire)

    def _incertitude_excessive(self, sigmas: Sequence[float]) -> int:
        """Indice de la première contrainte dont le seuil est dépassé (RA-FUN-003)."""
        for i, c in enumerate(self._jeu.contraintes):
            if sigmas[c.indice] > c.seuil_incertitude:
                return i
        return IDX_AUCUNE

    def _evaluer(self, u: float, etat: Sequence[float], sigmas: Sequence[float]):
        return trajectoire_sure(
            etat, sigmas, u, self._modele, self._jeu.contraintes,
            self._jeu.horizon_pas, self._jeu.pas_armement_max,
            self._politique_repli, self._dt, self._k_sigma,
        )

    def mettre_a_jour_jeu(self, nouveau: JeuContraintes, autorisation: bool,
                          t_s: float) -> None:
        """IF-6 : autorisation explicite requise ; la nouvelle version apparaît
        dans la trace dès le cycle suivant (RA-IND-004)."""
        if not autorisation:
            raise MiseAJourRefusee("IF-6 : mise à jour du jeu sans autorisation")
        self._jeu = nouveau
        self.notifications.append(
            (t_s, f"jeu de contraintes -> version {nouveau.version}")
        )

    def cycle(
        self,
        t_s: float,
        etat: Sequence[float],
        sigmas: Sequence[float],
        entrees_valides: bool,
        action_candidate: Optional[float],
    ) -> ResultatCycle:
        """Un cycle de décision : exactement un verdict émis (RA-FUN-001)."""
        self._vie += 1
        seq = self._seq
        self._seq += 1

        action_repli = self._politique_repli(etat)
        confiance = self._confiance(sigmas)
        verdict = Verdict.AUTORISE
        cause = Cause.AUCUNE
        idx_det = IDX_AUCUNE
        marge = math.nan
        action = action_repli

        if not entrees_valides:
            verdict, cause = Verdict.INDETERMINE, Cause.ENTREES_INVALIDES
        elif action_candidate is None:
            verdict, cause = Verdict.REPLI, Cause.TIMEO
