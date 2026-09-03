
"""Types de base du jeu de contraintes (RAM-SPEC-0001, blocs B2/B3).

Une contrainte est dérivée d'une exigence en langage naturel, à la manière des
22 spécifications EPS de CySat-I (Aurandt, Jones, Rozier, NFM 2022).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


class Sens(Enum):
    MIN = auto()   # la grandeur doit rester >= seuil
    MAX = auto()   # la grandeur doit rester <= seuil


IDX_AUCUNE = 255   # pas de contrainte déterminante (verdict nominal)


@dataclass(frozen=True)
class Contrainte:
    nom: str
    indice: int
    sens: Sens
    seuil: float
    echelle: float
    seuil_incertitude: float
    delai_armement_s: float
    marge_securite: float = 0.0

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
    """Jeu compilé et validé (RA-FUN-005), versionné (RA-IND-004).

    Ne se construit que via moniteur.compiler_jeu().
    """

    version: int
    contraintes: tuple[Contrainte, ...]
    horizon_pas: int
    pas_armement_max: int
