"""Types de base du jeu de contraintes (RAM-SPEC-0001, blocs B2/B3).

Une contrainte est dérivée d'une exigence en langage naturel, à la manière des
22 spécifications EPS de CySat-I (Aurandt, Jones, Rozier, NFM 2022). Chaque
contrainte porte :
  - la grandeur surveillée (indice dans le vecteur d'état estimé, IF-1) ;
  - son seuil et son sens ;
  - son seuil d'incertitude propre (RA-FUN-003 : l'incertitude est une entrée
    de premier ordre, par contrainte et non globale) ;
  - le délai d'armement de l'action de repli associée (RA-FUN-004 : l'horizon
    d'évaluation doit être au moins égal à ce délai).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


class Sens(Enum):
    MIN = auto()  # la grandeur doit rester >= seuil
    MAX = auto()  # la grandeur doit rester <= seuil


IDX_AUCUNE = 255  # pas de contrainte déterminante (verdict nominal)


@dataclass(frozen=True)
class Contrainte:
    nom: str                    # identifiant lisible, ex. « C0_SOC_MIN »
    indice: int                 # indice de la grandeur dans l'état estimé
    sens: Sens
    seuil: float
    echelle: float              # normalisation de la marge (unité physique)
    seuil_incertitude: float    # sigma max admissible (RA-FUN-003)
    delai_armement_s: float     # délai d'armement du repli associé (RA-FUN-004)
    marge_securite: float = 0.0  # garde ajoutée côté sûr du seuil

    def evaluer(self, valeur: float) -> bool:
        """Vrai si la valeur (déjà pessimiste) respecte la contrainte."""
        if self.sens is Sens.MIN:
            return valeur >= self.seuil + self.marge_securite
        return valeur <= self.seuil - self.marge_securite

    def marge_normalisee(self, valeur: float) -> float:
        """Distance signée à la limite, > 0 côté sûr, normalisée par echelle."""
        if self.sens is Sens.MIN:
            return (valeur - (self.seuil + self.marge_securite)) / self.echelle
        return ((self.seuil - self.marge_securite) - valeur) / self.echelle


@dataclass(frozen=True)
class JeuContraintes:
    """Jeu de contraintes compilé et validé (RA-FUN-005), versionné (RA-IND-004).

    Ne se construit que via moniteur.compiler_jeu() : la validation
    d'atteignabilité du repli y est effectuée avant toute mise en service.
    """

    version: int
    contraintes: tuple[Contrainte, ...]
    horizon_pas: int          # horizon d'évaluation, >= délai d'armement max
    pas_armement_max: int     # délai d'armement max converti en pas de cycle
