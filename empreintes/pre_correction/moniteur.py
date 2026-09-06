"""Moniteur d'assurance runtime — P0.

Implémente la sémantique de RAM-SPEC-0001 v0.1 :
  - exactement un verdict par cycle, dans {AUTORISE, MODIFIE, REPLI,
    INDETERMINE} (RA-FUN-001) ; INDETERMINE est traité comme REPLI par
    l'exécution mais resté distinct pour la trace (RA-FUN-002) ;
  - REPLI si l'incertitude d'une grandeur d'une contrainte active dépasse le
    seuil de cette contrainte (RA-FUN-003 / H4) ;
  - horizon d'évaluation >= délai d'armement du repli (RA-FUN-004) ;
  - repli atteignable validé à la compilation du jeu (RA-FUN-005) ;
  - repli verrouillé, retour au nominal sur critère explicite et horodaté
    (RA-FUN-006) ;
  - absence d'action candidate à l'échéance -> REPLI (RA-IND-003) ;
  - version du jeu de contraintes dans chaque enregistrement (RA-IND-004),
    mise à jour uniquement sur autorisation explicite (IF-6) ;
  - la trace ne bloque jamais le verdict (RA-RES-004) et les pertes sont
    comptées (RA-RES-005) ;
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
    VIOLATION_ENVELOPPE = 1   # repli ou modification dus à l'enveloppe
    INCERTITUDE = 2           # dépassement de seuil d'incertitude (RA-FUN-003)
    TIMEOUT_ACTION = 3        # absence d'action candidate (RA-IND-003)
    ENTREES_INVALIDES = 4     # estimateur invalide / données périmées
    REPLI_VERROUILLE = 5      # mode repli maintenu (RA-FUN-006)


class Mode(IntEnum):
    NOMINAL = 0
    REPLI = 1


class JeuInvalide(Exception):
    """Levée à la compilation si le repli n'est pas atteignable (RA-FUN-005)."""


class MiseAJourRefusee(Exception):
    """Levée sur tentative de mise à jour du jeu sans autorisation (IF-6)."""


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

    - horizon = délai d'armement maximal + marge (RA-FUN-004) ;
    - pour chaque contrainte, on vérifie que depuis l'état frontière (côté
      sûr) la trajectoire ne viole aucun seuil de sécurité brut (la marge de
      garde est le recul qui laisse au repli le temps d'agir, pas la limite
      de sécurité elle-même) ;
    - pendant l'armement, l'action transmise persiste : à la compilation on
      ne connaît pas l'action en cours, donc on vérifie les deux bornes
      admissibles — le repli n'est réputé atteignable que si le pire cas
      tient (RA-FUN-005, version P0 par échantillonnage — P1 : analyse
      d'atteignabilité formelle). Un jeu invalide est rejeté ici, pas en vol.
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
        # Critère explicite de retour au nominal (RA-FUN-006) : cycles_retour
        # cycles consécutifs pleinement sûrs (AUTORISE, sans modification)
        # ET dwell minimal en mode repli.
        self._cycles_retour = cycles_retour
        self._dwell_retour_s = dwell_retour_s
        self._n_pre_gel, self._n_post_gel = n_pre_gel, n_post_gel
        # Niveau de confiance déclaré p_S (cf. filtre.py) : k_sigma = 3,0
        # correspond à ~99,7 % sous hypothèse gaussienne. Déclaré, pas
        # justifié — la calibration sur l'estimateur réel est un sujet de P1.
        self._k_sigma = k_sigma

        self._mode = Mode.NOMINAL
        self._seq = 0
        self._vie = 0                    # signal de vie (RA-SUR-002)
        self._cycles_ok = 0
        self._t_entree_repli: Optional[float] = None
        self.notifications: list[tuple[float, str]] = []  # IF-4 vers FDIR

    # ------------------------------------------------------------------ utilitaires

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
        """Agrégat de confiance : 1 = loin des seuils d'incertitude, 0 = atteint."""
        pire = 0.0
        for c in self._jeu.contraintes:
            if c.seuil_incertitude > 0:
                pire = max(pire, sigmas[c.indice] / c.seuil_incertitude)
        return max(0.0, 1.0 - pire)

    def _incertitude_excessive(self, sigmas: Sequence[float]) -> int:
        """Indice de la première contrainte dont le seuil d'incertitude est
        dépassé (RA-FUN-003), IDX_AUCUNE sinon."""
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

    def mettre_a_jour_jeu(self, nouveau: JeuContraintes, autorisation: bool, t_s: float) -> None:
        """IF-6 : mise à jour du jeu de contraintes, autorisation explicite
        requise ; la nouvelle version apparaît dans la trace dès le cycle
        suivant (RA-IND-004)."""
        if not autorisation:
            raise MiseAJourRefusee("IF-6 : mise à jour du jeu sans autorisation")
        self._jeu = nouveau
        self.notifications.append(
            (t_s, f"jeu de contraintes -> version {nouveau.version}")
        )

    # ------------------------------------------------------------------ cycle

    def cycle(
        self,
        t_s: float,
        etat: Sequence[float],
        sigmas: Sequence[float],
        entrees_valides: bool,
        action_candidate: Optional[float],
    ) -> ResultatCycle:
        """Un cycle de décision : exactement un verdict émis (RA-FUN-001)."""
        self._vie += 1  # signal de vie (RA-SUR-002)
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
            # RA-IND-003 : absence d'action candidate à l'échéance.
            verdict, cause = Verdict.REPLI, Cause.TIMEOUT_ACTION
        else:
            idx_inc = self._incertitude_excessive(sigmas)
            if idx_inc != IDX_AUCUNE:
                # RA-FUN-003 : incertitude excessive -> repli, quelle que soit
                # la valeur nominale estimée.
                verdict, cause, idx_det = Verdict.REPLI, Cause.INCERTITUDE, idx_inc
            else:
                u_eval = min(max(action_candidate, self._u_min), self._u_max)
                dans_les_bornes = u_eval == action_candidate
                ok, idx_f, marge_c = self._evaluer(u_eval, etat, sigmas)
                if ok and dans_les_bornes:
                    verdict, cause, marge = Verdict.AUTORISE, Cause.AUCUNE, marge_c
                    action = action_candidate
                else:
                    adm = intervalle_admissible(
                        etat, sigmas, self._modele, self._jeu.contraintes,
                        self._jeu.horizon_pas, self._jeu.pas_armement_max,
                        self._politique_repli, self._dt, self._u_min,
                        self._u_max, self._k_sigma,
                    )
                    if adm is None:
                        verdict, cause = Verdict.REPLI, Cause.VIOLATION_ENVELOPPE
                        _, idx_det, marge = self._evaluer(self._u_min, etat, sigmas)
                    else:
                        u_hat, idx_det, marge = adm
                        # MODIFIE : intervention minimale ||v0 - u_candidat||
                        # (Wabersich & Zeilinger, spécialisation scalaire).
                        verdict, cause = Verdict.MODIFIE, Cause.VIOLATION_ENVELOPPE
                        action = u_hat

        # Verrouillage du repli (RA-FUN-006) : le retour au nominal exige un
        # critère explicite, compté et horodaté.
        if self._mode is Mode.REPLI:
            retour_possible = (
                verdict is Verdict.AUTORISE and cause is Cause.AUCUNE
            )
            self._cycles_ok = self._cycles_ok + 1 if retour_possible else 0
            dwell_ecoule = (
                self._t_entree_repli is not None
                and (t_s - self._t_entree_repli) >= self._dwell_retour_s
            )
            if self._cycles_ok >= self._cycles_retour and dwell_ecoule:
                self._mode = Mode.NOMINAL
                self._cycles_ok = 0
                self.notifications.append(
                    (t_s, f"retour au nominal (critère rempli, entré en repli à "
                          f"{self._t_entree_repli:.0f} s)")
                )
            else:
                if verdict is Verdict.AUTORISE:
                    verdict, cause = Verdict.REPLI, Cause.REPLI_VERROUILLE
                elif verdict is Verdict.MODIFIE:
                    verdict = Verdict.REPLI  # en repli verrouillé, on n'autorise pas
                action = action_repli
        else:
            if verdict in (Verdict.REPLI, Verdict.INDETERMINE):
                self._mode = Mode.REPLI
                self._t_entree_repli = t_s
                self._cycles_ok = 0

        if verdict is not Verdict.AUTORISE:
            self.notifications.append(
                (t_s, f"verdict {verdict.name} / {cause.name}")
            )
        # Gel de contexte (RA-TRC-006) : réservé aux verdicts de repli. Un
        # MODIFIE est un fonctionnement nominal du filtre, pas un événement —
        # figer dessus viderait la rétention étendue de son sens (cf.
        # RAM-NOTE-0001 §4 : le surcoût n'est négligeable que parce que les
        # événements sont rares).
        if verdict in (Verdict.REPLI, Verdict.INDETERMINE):
            self._tampon.figer(seq, self._n_pre_gel, self._n_post_gel)

        # B5 : la trace n'est jamais sur le chemin critique (RA-RES-004).
        marges = []
        for c in self._jeu.contraintes:
            v = etat[c.indice]
            marges.append(c.marge_normalisee(v))
        enregistrement = Enregistrement(
            t_s=t_s, seq=seq, version_jeu=self._jeu.version,
            verdict=int(verdict), cause=int(cause), mode=int(self._mode),
            indice_contrainte=idx_det, marge=marge, confiance=confiance,
            empreinte_candidate=_empreinte(action_candidate),
            empreinte_transmise=_empreinte(action),
            etat=list(etat), incertitudes=list(sigmas), marges=marges,
            action_candidate=[] if action_candidate is None else [action_candidate],
            action_transmise=[action],
        )
        self._tampon.ecrire(seq, t_s, enregistrement.paquet_c())

        return ResultatCycle(
            t_s=t_s, seq=seq, verdict=verdict, cause=cause, mode=self._mode,
            action_transmise=action, marge=marge,
            indice_contrainte=idx_det, confiance=confiance, vie=self._vie,
        )


class ChienDeGarde:
    """Mécanisme indépendant surveillant le signal de vie (RA-SUR-002). En vol,
    cette fonction appartient au FDIR plateforme, pas au moniteur (RA-SUR-001)."""

    def __init__(self, periode_max_s: float):
        self._periode_max = periode_max_s
        self._vie_vue = -1
        self._t_vue = 0.0

    def verifier(self, t_s: float, vie: int) -> bool:
        """Vrai si le moniteur est vivant ; déclenche le mode sûr sinon."""
        if vie != self._vie_vue:
            self._vie_vue, self._t_vue = vie, t_s
            return True
        return (t_s - self._t_vue) <= self._periode_max
